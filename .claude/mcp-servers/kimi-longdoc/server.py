# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "mcp>=2.0.0",
#     "httpx>=0.27",
#     "pymupdf>=1.24",
# ]
# ///
"""kimi-longdoc — 장문 문서를 Kimi-K3(1M 컨텍스트)로 통독시켜 구조화 추출하는 MCP 서버.

설계 원칙
  - 문서 텍스트는 로컬에서 추출한다(업로드 최소화, 크레딧 절약).
  - 모든 페이지에 [p.N] 마커를 심어, 모델이 출처 페이지를 반드시 인용하게 한다.
  - 추출 결과는 '후보값'이다. 치수/면적/법조항은 원문 페이지로 교차검증해야 한다.
  - 큰 결과는 파일로 저장하고 호출자에게는 경로 + 미리보기만 돌려준다.
"""

from __future__ import annotations

import base64
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
DEFAULT_MODEL = os.environ.get("KIMI_MODEL", "moonshotai/kimi-k3")
# 1M 토큰 ≈ 3~4M 문자. 여유를 두고 자른다.
DEFAULT_MAX_CHARS = int(os.environ.get("KIMI_MAX_CHARS", "2800000"))
TIMEOUT = httpx.Timeout(connect=15.0, read=1800.0, write=300.0, pool=15.0)

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".csv", ".json", ".xml", ".htm", ".html", ".py"}

CITATION_RULE = (
    "본문에는 [p.N] 형태의 페이지 마커가 들어 있다. "
    "네가 출력하는 모든 사실·수치·조항에는 근거 페이지를 반드시 함께 적어라. "
    "본문에서 확인되지 않는 값은 절대 추측하지 말고 null 로 두고, "
    "확인 불가 사유를 별도로 남겨라."
)

# Windows 기본 콘솔 인코딩(cp949)에서는 한글이 깨진다. MCP 프레이밍 전에 UTF-8로 고정.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

mcp = MCPServer("kimi-longdoc")


# ---------------------------------------------------------------- 로컬 문서 처리


@dataclass
class Extracted:
    path: Path
    text: str
    pages: int
    text_pages: int          # 실제로 텍스트가 나온 페이지 수
    images: list[str]        # data URL


def _auth_headers() -> dict:
    """로컬/Team·Enterprise 클라우드: NVIDIA_API_KEY 환경변수로 직접 인증.
    Pro/Max 클라우드: 환경변수를 비워두고 claude.ai/code 환경의 API credential로
    등록하면, 요청이 세션 밖으로 나간 뒤 Anthropic 프록시가 헤더를 붙여준다
    (키가 세션 안에는 전혀 들어오지 않음) — 그래서 키가 없어도 에러내지 않고
    헤더 없이 요청을 보낸다."""
    key = os.environ.get("NVIDIA_API_KEY", "").strip()
    return {"Authorization": "Bearer " + key} if key else {}


def _parse_pages(spec: str | None, total: int) -> list[int]:
    """'1-5,8,12-' → 0-based 페이지 인덱스 목록."""
    if not spec:
        return list(range(total))
    out: set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            a, _, b = chunk.partition("-")
            start = int(a) if a.strip() else 1
            end = int(b) if b.strip() else total
        else:
            start = end = int(chunk)
        for n in range(max(1, start), min(total, end) + 1):
            out.add(n - 1)
    return sorted(out)


def _load(path: Path, pages: str | None, vision: bool, dpi: int) -> Extracted:
    suffix = path.suffix.lower()

    if suffix in IMAGE_SUFFIXES:
        data = base64.b64encode(path.read_bytes()).decode()
        ext = suffix.lstrip(".")
        mime = "image/jpeg" if ext in {"jpg", "jpeg"} else "image/" + ext
        return Extracted(path, "", 1, 0, ["data:" + mime + ";base64," + data])

    if suffix in TEXT_SUFFIXES:
        body = path.read_text(encoding="utf-8", errors="replace")
        return Extracted(path, "=== [p.1] ===\n" + body, 1, 1, [])

    if suffix != ".pdf":
        raise ToolError(
            "지원하지 않는 형식입니다: " + path.name + ". "
            "hwp/hwpx/docx/xlsx 는 kordoc MCP 로 먼저 md/txt 변환 후 넘기세요."
        )

    import pymupdf

    parts: list[str] = []
    images: list[str] = []
    text_pages = 0
    with pymupdf.open(path) as doc:
        total = doc.page_count
        targets = _parse_pages(pages, total)
        for idx in targets:
            page = doc.load_page(idx)
            body = page.get_text("text").strip()
            marker = "=== [p." + str(idx + 1) + "] ==="
            if body:
                text_pages += 1
                parts.append(marker + "\n" + body)
            else:
                parts.append(marker + " (텍스트 레이어 없음)")
            # 스캔본이거나 vision 요청이면 해당 페이지를 이미지로도 첨부
            if vision or not body:
                pix = page.get_pixmap(dpi=dpi)
                images.append(
                    "data:image/png;base64,"
                    + base64.b64encode(pix.tobytes("png")).decode()
                )
    return Extracted(path, "\n\n".join(parts), len(targets), text_pages, images)


def _gather(
    paths: list[str], pages: str | None, vision: bool, dpi: int, max_chars: int
) -> tuple[str, list[str], list[dict], list[str]]:
    docs: list[str] = []
    images: list[str] = []
    report: list[dict] = []
    notes: list[str] = []

    for raw in paths:
        p = Path(raw).expanduser()
        if not p.exists():
            raise ToolError("파일이 없습니다: " + str(p))
        ex = _load(p, pages, vision, dpi)
        docs.append("########## FILE: " + p.name + " ##########\n" + ex.text)
        images.extend(ex.images)
        report.append(
            {
                "file": str(p),
                "pages": ex.pages,
                "pages_with_text": ex.text_pages,
                "chars": len(ex.text),
                "images_attached": len(ex.images),
                "scanned": ex.pages > 0 and ex.text_pages == 0,
            }
        )

    blob = "\n\n".join(docs)
    if len(blob) > max_chars:
        notes.append(
            "본문이 {:,}자로 한도({:,}자)를 넘어 잘렸습니다. "
            "pages 인자로 범위를 좁혀 나눠 호출하세요.".format(len(blob), max_chars)
        )
        blob = blob[:max_chars] + "\n\n[...본문 잘림...]"
    if len(images) > 40:
        notes.append("이미지 " + str(len(images)) + "장 중 앞 40장만 전송합니다.")
        images = images[:40]
    return blob, images, report, notes


# ---------------------------------------------------------------- API 호출


def _call(
    system: str,
    user_text: str,
    images: list[str],
    model: str,
    reasoning_effort: str,
    json_schema: dict | None,
    temperature: float,
) -> tuple[str, dict]:
    content: list[dict] = [{"type": "text", "text": user_text}]
    for url in images:
        content.append({"type": "image_url", "image_url": {"url": url}})

    payload: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
        "temperature": temperature,
        "max_tokens": 32768,
    }
    if reasoning_effort and reasoning_effort != "none":
        payload["reasoning_effort"] = reasoning_effort
    if json_schema:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "extraction", "schema": json_schema, "strict": False},
        }

    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.post(
            BASE_URL + "/chat/completions",
            headers={"Accept": "application/json", **_auth_headers()},
            json=payload,
        )
        if r.status_code in (401, 403):
            raise ToolError(
                "NVIDIA API 인증 실패(" + str(r.status_code) + "). "
                "로컬/Team·Enterprise 클라우드: NVIDIA_API_KEY 환경변수를 확인하세요. "
                "Pro/Max 클라우드: claude.ai/code 환경 설정의 API credentials에 "
                "integrate.api.nvidia.com 을 등록했는지 확인하세요. "
                + r.text[:500]
            )
        if r.status_code >= 400:
            raise ToolError(
                "NVIDIA API " + str(r.status_code) + ": " + r.text[:1000]
            )
        data = r.json()

    text = data["choices"][0]["message"].get("content") or ""
    return text, data.get("usage", {})


def _deliver(text: str, out_path: str | None, meta: dict) -> str:
    """큰 결과는 파일로 떨구고 미리보기만 반환."""
    meta_block = json.dumps(meta, ensure_ascii=False, indent=2)
    if out_path:
        p = Path(out_path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        preview = text[:2000]
        tail = "\n\n[...전체 내용은 위 파일 참조...]" if len(text) > 2000 else ""
        return "저장: " + str(p) + "\n\n" + meta_block + "\n\n--- 미리보기 ---\n" + preview + tail
    return meta_block + "\n\n" + text


# ---------------------------------------------------------------- MCP 도구


@mcp.tool()
def probe(paths: list[str], pages: str | None = None) -> str:
    """API 호출 없이 로컬에서만 문서를 점검한다. 크레딧 쓰기 전에 항상 먼저 실행할 것.

    페이지 수, 텍스트 레이어 유무(스캔본 판별), 예상 토큰량을 보고한다.

    Args:
        paths: PDF/이미지/텍스트 파일 경로 목록.
        pages: 페이지 범위 (예: "1-20,45,80-"). 생략 시 전체.
    """
    _, _, report, notes = _gather(paths, pages, False, 100, 10**9)
    total_chars = sum(r["chars"] for r in report)
    scanned = [r["file"] for r in report if r["scanned"]]
    out = {
        "files": report,
        "total_chars": total_chars,
        "estimated_input_tokens": round(total_chars / 2.5),  # 한글 기준 보수적 추정
        "fits_in_1m_context": total_chars / 2.5 < 950_000,
        "scanned_files_need_vision": scanned,
        "notes": notes,
    }
    return json.dumps(out, ensure_ascii=False, indent=2)


@mcp.tool()
def extract_document(
    paths: list[str],
    instruction: str,
    json_schema: dict | None = None,
    pages: str | None = None,
    vision: bool = False,
    out_path: str | None = None,
    reasoning_effort: str = "medium",
    model: str = DEFAULT_MODEL,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """장문 문서를 Kimi-K3 1M 컨텍스트에 통째로 넣어 구조화 데이터로 추출한다.

    공모전 지침서 → 요구조건 테이블, 법령 원문 → 조항별 정리, 결정조서 → 규제값 등에 사용.
    모든 출력값에는 근거 페이지 [p.N]가 붙는다. 값이 확인되지 않으면 null로 남긴다.

    반환된 수치는 '후보값'이다. 면적·치수·법조항은 반드시 원문 페이지로 교차검증할 것.

    Args:
        paths: 문서 경로 목록. hwp/hwpx/docx는 kordoc로 먼저 변환해서 넘길 것.
        instruction: 무엇을 뽑을지에 대한 지시. 구체적일수록 정확하다.
        json_schema: 원하는 출력 JSON Schema. 주면 스키마에 맞춰 강제 출력한다.
        pages: 페이지 범위 (예: "1-40").
        vision: True면 각 페이지를 이미지로도 첨부한다(도면·표·다이어그램 판독용, 느리고 비쌈).
        out_path: 결과 저장 경로. 결과가 길면 반드시 지정할 것.
        reasoning_effort: "none" | "low" | "medium" | "high" | "max".
            지침서·법령 통독처럼 한 번에 정확히 뽑아야 하면 "max".
        model: 모델 id. 정확한 값은 list_models로 확인.
        max_chars: 전송 본문 최대 문자 수.
    """
    blob, images, report, notes = _gather(paths, pages, vision, 150, max_chars)
    system = (
        "너는 한국 건축설계사무소의 문서 분석 담당이다. 주어진 원문만 근거로 답한다. "
        + CITATION_RULE
        + " 출력은 한국어로 한다."
    )
    fmt = (
        "결과는 JSON으로만 출력하라."
        if json_schema
        else "결과는 Markdown 표 또는 JSON 등 요청에 맞는 구조화 형태로 출력하라."
    )
    user = "[지시]\n" + instruction + "\n\n" + fmt + "\n\n[원문]\n" + blob

    text, usage = _call(system, user, images, model, reasoning_effort, json_schema, 0.1)
    return _deliver(text, out_path, {"source_files": report, "usage": usage, "notes": notes})


@mcp.tool()
def ask_documents(
    paths: list[str],
    question: str,
    pages: str | None = None,
    vision: bool = False,
    out_path: str | None = None,
    reasoning_effort: str = "high",
    model: str = DEFAULT_MODEL,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """문서 전체를 근거로 자유형 질문에 답하게 한다. 독립 2차 의견/교차검증용.

    같은 질문을 Claude와 Kimi-K3에 각각 물어 답이 갈리는 지점을 찾는 용도로 쓴다.
    답이 갈리면 그 지점이 원문 재확인이 필요한 곳이다.

    Args:
        paths: 문서 경로 목록.
        question: 질문.
        pages: 페이지 범위.
        vision: 페이지 이미지 첨부 여부.
        out_path: 결과 저장 경로.
        reasoning_effort: "none" | "low" | "medium" | "high" | "max".
            지침서·법령 통독처럼 한 번에 정확히 뽑아야 하면 "max".
        model: 모델 id.
        max_chars: 전송 본문 최대 문자 수.
    """
    blob, images, report, notes = _gather(paths, pages, vision, 150, max_chars)
    system = (
        "너는 한국 건축 실무 문서를 읽는 분석가다. 주어진 원문만 근거로 답한다. "
        + CITATION_RULE
        + " 원문에서 답을 찾을 수 없으면 '원문에 근거 없음'이라고 명시하라. 한국어로 답하라."
    )
    user = "[질문]\n" + question + "\n\n[원문]\n" + blob
    text, usage = _call(system, user, images, model, reasoning_effort, None, 0.2)
    return _deliver(text, out_path, {"source_files": report, "usage": usage, "notes": notes})


@mcp.tool()
def list_models(filter: str = "kimi") -> str:
    """NVIDIA 엔드포인트에서 사용 가능한 모델 id 목록을 조회한다.

    NVIDIA build 페이지의 코드 샘플에 model id가 비어 있으므로, 첫 사용 전 이걸로 확인할 것.

    Args:
        filter: id에 포함될 부분 문자열. 빈 문자열이면 전체.
    """
    with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
        r = client.get(BASE_URL + "/models", headers=_auth_headers())
        if r.status_code >= 400:
            raise ToolError("NVIDIA API " + str(r.status_code) + ": " + r.text[:500])
        ids = sorted(m.get("id", "") for m in r.json().get("data", []))
    hits = [i for i in ids if filter.lower() in i.lower()] if filter else ids
    return json.dumps(
        {"matched": hits, "total_available": len(ids), "configured_default": DEFAULT_MODEL},
        ensure_ascii=False,
        indent=2,
    )


if __name__ == "__main__":
    try:
        mcp.run()
    except Exception as exc:  # noqa: BLE001
        print("kimi-longdoc 기동 실패: " + str(exc), file=sys.stderr)
        raise
