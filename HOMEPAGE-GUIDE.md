# 홈페이지 수정 가이드 (다음 세션 착수 문서)

이 문서는 **"무엇을 어떻게 고치는가"** 를 담은 실무 안내서입니다.
"무엇을 했는가" 기록은 `WORK-LOG.md`, 블로그 글 포맷은 `BLOG-TEMPLATE.md`를 보세요.

---

## 0. 가장 먼저 — 작업 시작 전 체크 (필수)

이 저장소는 **건축가 두 명이 각자 push** 합니다. 내 로컬이 뒤처진 상태에서 작업하면 충돌하거나 남의 작업을 덮어씁니다.

```bash
git fetch origin
git log HEAD..origin/master --oneline    # 원격에 새 커밋이 있는지 확인
git status --short                        # 내 쪽 미커밋 변경 확인
```

- 원격에 새 커밋이 있으면 → `git merge origin/master` (또는 `git pull --ff-only`) 먼저
- **절대 force-push 금지.** push가 거부되면 반드시 원격 커밋 내용을 먼저 읽어보고 머지할 것
- 상대 작업자가 손댄 파일은 건드리지 않고, **추가(additive)** 위주로 수정하는 것이 안전

---

## 1. 사이트 구조 3분 요약

| 항목 | 내용 |
|---|---|
| 형식 | 빌드 없는 정적 사이트 (HTML + CSS + JS 원본 그대로 배포) |
| 배포 | GitHub Pages, **`master` 브랜치 기준**. push하면 1~2분 내 자동 반영 |
| 도메인 | www.ooa-architects.com (`CNAME` 파일로 지정) |
| 페이지 | `index.html`(홈) `project.html`(Works) `about.html` `press.html` `contact.html` |
| 공통 | `css/style.css` (1,120줄) · `js/main.js` (295줄) · `fonts/`(Pretendard 셀프호스팅) |

### ⚠️ 배포 함정 — 작업 브랜치에만 push하면 사이트는 안 바뀝니다

Pages는 **`master`만** 바라봅니다. 작업 브랜치에 push해놓고 "홈페이지에 변화가 없다"고 헷갈린 전례가 여러 번 있습니다.

```bash
git push -u origin <작업브랜치>          # 1) 작업 브랜치 백업
git checkout master && git merge <작업브랜치> --ff-only
git push origin master                   # 2) ← 이게 실제 배포
```

### ⚠️ Pretendard는 400/500/700만 있습니다

`font-weight: 600`을 쓰면 브라우저가 **700으로 올려 렌더**해서 의도보다 훨씬 진하게 나옵니다.
"살짝만 강조"가 필요하면 **500**을 쓰세요.

### ⚠️ 프로젝트 ID는 숫자로 시작합니다

`34-haenam-...` 같은 ID는 **CSS 선택자로 쓸 수 없습니다**(`querySelector('#34-...')`는 예외를 던짐).
`main.js`는 이미 `getElementById`로 처리해 두었으니 그대로 유지하고, 테스트 코드에서는 `[id="34-..."]` 속성 선택자를 쓰세요.

---

## 2. 파일 지도 — 무엇을 고치려면 어디를 보나

| 고치고 싶은 것 | 파일 / 위치 |
|---|---|
| 홈 첫 화면 인트로(OOA 글자 + 점) | `js/main.js` `initIntroSplash()` + `css/style.css` `.intro-*` |
| 홈 상단 배경 슬라이드쇼 | `js/main.js` `initHeroSlideshow()` + `images/main/01~06.jpg` |
| 프로젝트 목록·슬라이드쇼 동작 | `js/main.js` `initSlideshows()` |
| 왼쪽 사이드바 메뉴 | 5개 HTML 전부의 `<details class="nav-tree">` 블록 (동일 내용 복붙) |
| 프로젝트 본문 | `index.html` + `project.html` 의 `<article class="project-entry">` |
| 회사 소개·수상이력 | `about.html` |
| 언론보도 | `press.html` |
| 연락처·지도 | `contact.html` |
| 색상·간격·타이포 | `css/style.css` 최상단 `:root` 커스텀 속성 |

주요 CSS 변수: `--c-text-1`(본문) `--c-line`(구분선) `--c-teal: #04a1b2`(포인트) `--c-chip-bg`

---

## 3. 자주 하는 작업 레시피

### 3-1. 프로젝트 추가 (가장 빈번)

현재 34건. **Op.34 해남 유기농산업복합서비스 지원단지**(`34-haenam-organic-industry-complex`)를 그대로 복사해서 쓰면 가장 빠릅니다.

1. **이미지 배치**: `images/projects/<번호>-<영문슬러그>/01.jpg …` (가로 2000px 권장, JPG)
2. **`project.html`** — 해당 **카테고리 묶음 안**에 `<article>` 블록 추가
3. **`index.html`** — **맨 앞(최신순)** 에 같은 `<article>` 블록 추가
4. **사이드바** — 5개 HTML 전부의 해당 카테고리 `<ul>`에 `<li><a href="project.html#슬러그">이름</a></li>` 추가
5. **`sitemap.xml`** `lastmod` 날짜 갱신

> **두 파일의 정렬 기준이 다릅니다.**
> `index.html` = 최신순(34 → 33 → 32 …) / `project.html` = 사이드바 카테고리 순(주거·상업 → 문화 → 교육 → 복지 → 공공 → 산업)
> 같은 블록이라도 넣는 **위치가 다르니** 복붙 위치를 반드시 확인하세요.

`<article>` 블록 필수 구성:

- `id` / `aria-labelledby` 에 슬러그 (둘이 일치해야 함)
- `Op. N · <span class="tag-label">영문 카테고리</span>`
- `<dl class="project-meta-list">` — 공모 / 위치 / 용도 / 규모 4줄
- `.slideshow` — 사진 N장마다 `.slide` N개 + `.slide-index`는 `01 / N` 형식 + `.slide-dot` 버튼도 **N개**
- `.slide` 의 `tile-a → tile-b → tile-c → tile-d` 클래스는 4개 주기로 반복
- 첫 슬라이드만 `is-active` / `aria-hidden="false"`
- `alt`에 **위치·용도를 함께** 기재 (SEO 규칙) — 예: `유기농산업복합서비스 지원단지 (전남 해남군, 근린생활시설) 이미지 1`

### 3-2. 언론보도(Press) 추가

`press.html`의 `.press-item` 복사. 구조는 `8rem 1fr auto` 그리드:

- 왼쪽 **날짜** — 공모 수상건은 **사무소 Awards 수상일** 기준, 준공·기사는 기사 날짜 기준
- 가운데 **제목** → `project.html#슬러그`(자사 Works)로 연결
- 오른쪽 회색 **출처명** + 그 아래 16:10 **썸네일** → 외부 기사/유튜브로 연결
- 최신순 정렬 유지

### 3-3. 수상이력(Awards) 추가

`about.html`의 연도 블록에 한 줄 추가:

```html
[발주처] 공모명 — <strong class="award-grade">우수상(3등)</strong>
```

`.award-grade`는 `font-weight: 500` (색상 변경 없음). 600은 쓰지 마세요(§1 참고).

### 3-4. 텍스트·레이아웃 미세 조정

- 긴 한글 문단은 `word-break: keep-all` 를 유지해야 단어가 안 쪼개집니다
- 링크 밑줄 제거는 `link-underline` 클래스를 **빼는** 방식
- 지도는 iframe이라 **내부를 CSS로 못 건드립니다.** 핀·라벨은 iframe 바깥에 절대배치한 오버레이(`.contact-map-pin`, `.contact-map-label`)로 올려둔 상태 — iframe의 `filter: grayscale(1)`이 오버레이에 영향 주지 않게 분리해둔 구조이니 합치지 마세요

---

## 4. 검증 방법

### 로컬 미리보기

```bash
python3 -m http.server 4173     # 저장소 루트에서
# http://localhost:4173
```

### Playwright (클라우드 세션 기준 경로 주의)

이 환경에서 Playwright는 기본 PATH에 없습니다:

```bash
export PATH=/opt/node22/bin:/usr/local/bin:/usr/bin:/bin
export NODE_PATH=/opt/node22/lib/node_modules
# 브라우저 실행 파일: /opt/pw-browsers/chromium
```

**이미지 깨짐 검사 시 주의**: 슬라이드가 `loading="lazy"`라 그냥 재면 `naturalWidth === 0`으로 **전부 깨진 것처럼 오탐**합니다. 검사 전에 `img.loading = 'eager'` 로 바꾸고 `await img.decode()` 를 기다리세요.
슬라이드쇼 dot 클릭은 자동 전환과 충돌해 타임아웃 나기 쉬우니, 클릭 대신 **decode 성공 여부로 검증**하는 편이 안정적입니다.

### 배포 확인

라이브 사이트(`www.ooa-architects.com`)는 이 환경에서 **프록시 차단**되어 못 엽니다. 대신:

1. `master`의 파일 내용으로 확인 (GitHub MCP `get_file_contents`)
2. GitHub Actions의 `pages-build-deployment` 실행 성공 확인

---

## 5. 이 환경에서 막히는 것들 (미리 알고 시작하기)

| 막히는 것 | 우회 |
|---|---|
| `blog.naver.com`, `law.go.kr`, `sasaki.com`, `utaa.co.kr`, 라이브 사이트 — 프록시 차단 | 사용자에게 스크린샷·텍스트 요청 |
| `git`/`ls` 등 "command not found" | 모든 Bash 호출 앞에 `export PATH=/usr/local/bin:/usr/bin:/bin` |
| `gh` CLI 없음 | GitHub MCP 도구(`mcp__github__*`) 사용 |
| 네이버 블로그는 코드로 반영 불가 | `BLOG-TEMPLATE.md` 수동 가이드 |

---

## 6. 지금 열려 있는 수정 후보 (바로 착수 가능)

우선순위 순. 어느 것부터 할지는 사용자 확인 후 진행하세요.

### A. 홈 히어로 이미지 용량 — 체감 속도 개선 (권장 1순위)

- 현황: `images/main/01~06.jpg` 6장 **합계 약 4.5MB**, `index.html`에서 **6장 전부 `loading="eager"`**
- 문제: 첫 화면에서 6장을 동시에 받느라 모바일 진입이 느림
- 조치안: ① 2~6번째를 `loading="lazy"`로 ② WebP 변환 또는 품질 재압축 ③ 긴 변 1920px 제한
- 주의: 교체 시 원본은 OneDrive에 있으므로 저장소에는 **웹용 축소본만**

### B. `README.md` 인코딩 깨짐

- 현황: UTF-16LE + BOM으로 저장돼 GitHub에서 `��# o o a - a r c h i t e c t s` 로 보임
- 조치: UTF-8로 다시 작성 (내용 자체가 거의 없으므로 새로 쓰는 편이 빠름)

### C. JSON-LD 좌표(geo) 추가 보류분

- 사무실 정확한 위도/경도를 확인할 방법이 없어 보류 중. 좌표를 확보하면 `index.html` JSON-LD에 추가

### D. 코드 밖 작업 (사용자가 직접 — `WORK-LOG.md` 미완료 7·8번)

- 네이버 블로그 기존 "법규" 글 4건에 `BLOG-TEMPLATE.md` 포맷 적용
- 인포그래픽 카드 이미지 수정(저장소에 원본 없음, 외부 디자인 툴 필요)
- 네이버 스마트플레이스 등록 / 구글 서치 콘솔 색인 요청 / 카카오맵 영업시간 수정

---

## 7. 다음 세션 시작 문장 예시

```
홈페이지 수정 작업 이어서 할게. HOMEPAGE-GUIDE.md 읽고 시작해줘.
작업 전에 git fetch로 원격 새 커밋 확인부터 하고,
<하고 싶은 작업>을 진행해줘.
```

---
*이 문서는 작업 안내서이며, 실제 사이트 코드가 아닙니다.*
