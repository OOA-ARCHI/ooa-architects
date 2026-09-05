# -*- coding: utf-8 -*-
"""호텔 가은 객실 단위평면 생성 (디럭스룸 35.0m² / 패밀리룸 45.5m²)

참고도면 1·2의 표현 규칙(0CONC 벽체, 0WIN 창호, DOOR 문, FUR 가구, m²/PY 면적표기)과
호텔가은 계획도면(0718)의 객실 블록 치수(디럭스 7.0×5.0m, 패밀리 7.0×6.5m)를 적용.
단위: mm (INSUNITS=4)
"""
import ezdxf
from ezdxf import units
from ezdxf.math import Vec2
import math

doc = ezdxf.new("R2010", setup=True)
doc.units = units.MM
doc.header["$INSUNITS"] = 4

# ---- 텍스트 스타일 (한글: Pretendard) ----
doc.styles.add("KOR", font="Pretendard-Regular.ttf")

# ---- 레이어 (참고도면 명칭 준용) ----
LAYERS = [
    ("0CONC", 7),       # 벽체
    ("해치벽체", 8),     # 벽체 해치
    ("0WIN", 4),        # 창호
    ("DOOR", 2),        # 문
    ("FUR", 3),         # 가구
    ("TOIL", 5),        # 위생기구
    ("0TEXT-1", 7),     # 문자
    ("S-DIM", 1),       # 치수
    ("0CEN", 9),        # 중심선/보조선
]
for name, color in LAYERS:
    doc.layers.add(name, color=color)
for _ln in ("0CEN",):
    doc.layers.get(_ln).dxf.linetype = "DASHDOT"

msp = doc.modelspace()

# ---- 치수 스타일 ----
dimstyle = doc.dimstyles.add("D100")
dimstyle.dxf.dimtxt = 250
dimstyle.dxf.dimasz = 180
dimstyle.dxf.dimexe = 120
dimstyle.dxf.dimexo = 150
dimstyle.dxf.dimgap = 80
dimstyle.dxf.dimdec = 0
dimstyle.dxf.dimtad = 1
dimstyle.dxf.dimtxsty = "KOR"
dimstyle.dxf.dimclrd = 1
dimstyle.dxf.dimclre = 1
dimstyle.dxf.dimclrt = 1

# ================= 헬퍼 =================

def rect(layer, x1, y1, x2, y2, dx=0.0):
    msp.add_lwpolyline(
        [(x1+dx, y1), (x2+dx, y1), (x2+dx, y2), (x1+dx, y2)],
        close=True, dxfattribs={"layer": layer})

def line(layer, p1, p2, dx=0.0):
    msp.add_line((p1[0]+dx, p1[1]), (p2[0]+dx, p2[1]), dxfattribs={"layer": layer})

def circle(layer, c, r, dx=0.0):
    msp.add_circle((c[0]+dx, c[1]), r, dxfattribs={"layer": layer})

def arc(layer, c, r, a1, a2, dx=0.0):
    msp.add_arc((c[0]+dx, c[1]), r, a1, a2, dxfattribs={"layer": layer})

def ellipse(layer, c, rx, ry, dx=0.0):
    # major axis = x
    if rx >= ry:
        msp.add_ellipse((c[0]+dx, c[1]), major_axis=(rx, 0), ratio=ry/rx,
                        dxfattribs={"layer": layer})
    else:
        msp.add_ellipse((c[0]+dx, c[1]), major_axis=(0, ry), ratio=rx/ry,
                        dxfattribs={"layer": layer})

def wall(x1, y1, x2, y2, dx=0.0):
    """벽체: 외곽선 + 솔리드 해치"""
    rect("0CONC", x1, y1, x2, y2, dx)
    h = msp.add_hatch(color=8, dxfattribs={"layer": "해치벽체"})
    h.paths.add_polyline_path(
        [(x1+dx, y1), (x2+dx, y1), (x2+dx, y2), (x1+dx, y2)], is_closed=True)
    h.set_pattern_fill("ANSI31", scale=15.0, color=8)

def text(layer, s, pos, h, dx=0.0, align="MIDDLE_CENTER", color=None):
    attribs = {"layer": layer, "style": "KOR", "height": h}
    if color is not None:
        attribs["color"] = color
    t = msp.add_text(s, dxfattribs=attribs)
    t.set_placement((pos[0]+dx, pos[1]), align=ezdxf.enums.TextEntityAlignment[align])

def door(hinge, leaf_angle_deg, swing_deg, width, dx=0.0):
    """문: 문짝(선) + 회전호. leaf_angle=닫힘상태에서 열린 문짝 방향각"""
    hx, hy = hinge[0]+dx, hinge[1]
    a = math.radians(leaf_angle_deg)
    tip = (hx + width*math.cos(a), hy + width*math.sin(a))
    msp.add_line((hx, hy), tip, dxfattribs={"layer": "DOOR"})
    a1, a2 = sorted([leaf_angle_deg, leaf_angle_deg + swing_deg])
    msp.add_arc((hx, hy), width, a1, a2, dxfattribs={"layer": "DOOR"})

def window(x1, x2, y_wall1, y_wall2, dx=0.0):
    """창호: 개구부 내 4중선"""
    t3 = (y_wall2 - y_wall1) / 3.0
    for y in (y_wall1, y_wall1+t3, y_wall2-t3, y_wall2):
        line("0WIN", (x1, y), (x2, y), dx)
    line("0WIN", (x1, y_wall1), (x1, y_wall2), dx)
    line("0WIN", (x2, y_wall1), (x2, y_wall2), dx)

def bed(x1, y1, x2, y2, head, dx=0.0):
    """침대: 외곽 + 베개 + 이불 접힘선. head: 'bottom'|'right'"""
    rect("FUR", x1, y1, x2, y2, dx)
    if head == "bottom":
        w = x2 - x1
        if w >= 1500:  # 더블: 베개 2개
            pw = (w - 3*160) / 2
            rect("FUR", x1+160, y1+120, x1+160+pw, y1+520, dx)
            rect("FUR", x2-160-pw, y1+120, x2-160, y1+520, dx)
        else:          # 싱글: 베개 1개
            rect("FUR", x1+180, y1+120, x2-180, y1+520, dx)
        fy = y1 + (y2-y1)*0.62
        line("FUR", (x1, fy), (x2, fy), dx)
        line("FUR", (x1, fy+140), (x2, fy+140), dx)
        line("FUR", (x1, y2-220), (x1+220, y2), dx)
    elif head == "right":
        h = y2 - y1
        rect("FUR", x2-520, y1+180, x2-120, y2-180, dx)
        fx = x2 - (x2-x1)*0.62
        line("FUR", (fx, y1), (fx, y2), dx)
        line("FUR", (fx-140, y1), (fx-140, y2), dx)
        line("FUR", (x1+220, y1), (x1, y1+220), dx)

def lamp_table(x1, y1, x2, y2, dx=0.0):
    rect("FUR", x1, y1, x2, y2, dx)
    circle("FUR", ((x1+x2)/2, (y1+y2)/2), 110, dx)

def toilet(cx, tank_y1, tank_y2, dx=0.0):
    """양변기: 탱크(사각) + 볼(타원), 아래벽 기준"""
    rect("TOIL", cx-220, tank_y1, cx+220, tank_y2, dx)
    ellipse("TOIL", (cx, tank_y2 + 330), 230, 310, dx)

def basin(x1, y1, x2, y2, dx=0.0):
    """세면카운터 + 세면볼"""
    rect("TOIL", x1, y1, x2, y2, dx)
    cx, cy = (x1+x2)/2, (y1+y2)/2
    ellipse("TOIL", (cx, cy), 270, 190, dx)
    circle("TOIL", (cx, y1+90), 45, dx)

# ================= 단위평면 =================

def unit_deluxe(dx):
    """디럭스룸 7000x5000 (35.0m²) — 복도(하부), 창(상부)"""
    W, D = 7000, 5000
    # ---- 벽체 ----
    wall(0, 0, 2700, 200, dx)         # 하부벽(좌측, 출입문 개구부 앞)
    wall(3600, 0, W, 200, dx)         # 하부벽(우측)
    wall(0, D-200, 1200, D, dx)       # 상부벽(좌측, 창 개구부 앞)
    wall(5800, D-200, W, D, dx)       # 상부벽(우측)
    wall(0, 200, 200, D-200, dx)      # 좌측 세대간벽
    wall(W-200, 200, W, D-200, dx)    # 우측 세대간벽
    # 욕실 칸막이 (100THK)
    wall(2400, 200, 2500, 1300, dx)   # 수직(하)
    wall(2400, 2100, 2500, 2400, dx)  # 수직(상)
    wall(200, 2300, 2400, 2400, dx)   # 수평
    # ---- 개구부 ----
    door((3600, 200), 90, 90, 900, dx)            # 출입문 W900 (내부로 열림)
    door((2400, 1300), 180, -90, 800, dx)         # 욕실문 W800 (욕실측)
    window(1200, 5800, D-200, D, dx)              # 창호 W4600
    # ---- 욕실 (2200x2100) ----
    rect("TOIL", 200, 1400, 1100, 2300, dx)       # 샤워부스
    line("TOIL", (200, 1400), (1100, 2300), dx)
    line("TOIL", (200, 2300), (1100, 1400), dx)
    toilet(700, 250, 470, dx)                     # 양변기
    basin(1500, 200, 2400, 750, dx)               # 세면대
    text("0TEXT-1", "욕실", (1600, 1150), 200, dx)
    # ---- 침실 가구 ----
    rect("FUR", 950, 2400, 2850, 2500, dx)        # 헤드보드
    bed(1000, 2500, 2800, 4500, "bottom", dx)     # 킹베드 1800x2000
    lamp_table(400, 2500, 900, 3000, dx)          # 협탁(좌)
    lamp_table(2900, 2500, 3400, 3000, dx)        # 협탁(우)
    rect("FUR", 6350, 2500, 6800, 3900, dx)       # TV장
    rect("FUR", 6380, 2750, 6450, 3650, dx)       # TV
    rect("FUR", 5750, 4100, 6350, 4700, dx)       # 라운지체어
    rect("FUR", 5820, 4170, 6280, 4630, dx)
    circle("FUR", (5300, 4400), 300, dx)          # 티테이블
    rect("FUR", 4550, 4150, 5000, 4650, dx)       # 보조의자
    rect("FUR", 4000, 200, 5800, 850, dx)         # 옷장
    line("FUR", (4000, 200), (5800, 850), dx)
    line("FUR", (4900, 200), (4900, 850), dx)
    rect("FUR", 5950, 250, 6750, 800, dx)         # 캐리어받침
    line("FUR", (5950, 250), (6750, 800), dx)
    line("FUR", (5950, 800), (6750, 250), dx)
    # ---- 문자 ----
    text("0TEXT-1", "디럭스룸", (4550, 3550), 350, dx)
    text("0TEXT-1", "35.0m² /10.59PY", (4550, 3150), 250, dx)
    # ---- 치수 ----
    for (p1, p2), dist in {((0,0),(2700,0)): -700, ((2700,0),(3600,0)): -700, ((3600,0),(7000,0)): -700}.items():
        d = msp.add_linear_dim(base=(p1[0]+dx, dist), p1=(p1[0]+dx, p1[1]), p2=(p2[0]+dx, p2[1]),
                               dimstyle="D100", dxfattribs={"layer": "S-DIM"})
        d.render()
    d = msp.add_linear_dim(base=(dx, -1300), p1=(dx, 0), p2=(dx+W, 0),
                           dimstyle="D100", dxfattribs={"layer": "S-DIM"})
    d.render()
    for (p1, p2) in [((0,0),(0,2400)), ((0,2400),(0,5000))]:
        d = msp.add_linear_dim(base=(dx-700, 0), p1=(dx+p1[0], p1[1]), p2=(dx+p2[0], p2[1]),
                               angle=90, dimstyle="D100", dxfattribs={"layer": "S-DIM"})
        d.render()
    d = msp.add_linear_dim(base=(dx-1300, 0), p1=(dx, 0), p2=(dx, D),
                           angle=90, dimstyle="D100", dxfattribs={"layer": "S-DIM"})
    d.render()
    # 타이틀
    text("0TEXT-1", "디럭스룸 (DELUXE ROOM)", (3500, -2500), 500, dx)
    text("0TEXT-1", "전용 35.0m² /10.59PY  ·  7.0m × 5.0m  ·  기준 2인", (3500, -3150), 280, dx)
    text("0TEXT-1", "외부 (조망)", (3500, 5450), 280, dx, color=8)

def unit_family(dx):
    """패밀리룸 7000x6500 (45.5m²) — 복도(하부), 창(상부)"""
    W, D = 7000, 6500
    # ---- 벽체 ----
    wall(0, 0, 3000, 200, dx)
    wall(3900, 0, W, 200, dx)
    wall(0, D-200, 1200, D, dx)
    wall(5800, D-200, W, D, dx)
    wall(0, 200, 200, D-200, dx)
    wall(W-200, 200, W, D-200, dx)
    # 욕실 칸막이 (100THK)
    wall(2600, 200, 2700, 1400, dx)
    wall(2600, 2200, 2700, 2500, dx)
    wall(200, 2400, 2600, 2500, dx)
    # ---- 개구부 ----
    door((3900, 200), 90, 90, 900, dx)            # 출입문 W900
    door((2600, 1400), 180, -90, 800, dx)         # 욕실문 W800
    window(1200, 5800, D-200, D, dx)              # 창호 W4600
    # ---- 욕실 (2400x2200, 욕조형) ----
    rect("TOIL", 200, 1650, 1900, 2400, dx)       # 욕조
    rect("TOIL", 290, 1740, 1810, 2310, dx)
    circle("TOIL", (470, 2025), 80, dx)           # 배수구
    toilet(550, 250, 470, dx)                     # 양변기
    basin(1500, 200, 2600, 750, dx)               # 세면대
    text("0TEXT-1", "욕실", (1250, 1150), 200, dx)
    # ---- 침실 가구 ----
    rect("FUR", 1250, 2500, 3150, 2600, dx)       # 헤드보드
    bed(1300, 2600, 3100, 4600, "bottom", dx)     # 더블베드 1800x2000
    lamp_table(3200, 2600, 3700, 3100, dx)        # 협탁
    bed(4800, 2600, 6800, 3700, "right", dx)      # 싱글베드1 2000x1100
    bed(4800, 4000, 6800, 5100, "right", dx)      # 싱글베드2 2000x1100
    rect("FUR", 200, 4800, 650, 6100, dx)         # TV장
    rect("FUR", 560, 4950, 630, 5950, dx)         # TV
    rect("FUR", 200, 2700, 850, 4500, dx)         # 옷장
    line("FUR", (200, 2700), (850, 4500), dx)
    line("FUR", (200, 3600), (850, 3600), dx)
    circle("FUR", (3650, 5600), 400, dx)          # 좌식테이블
    rect("FUR", 2950, 5400, 3350, 5800, dx)       # 방석
    rect("FUR", 3950, 5400, 4350, 5800, dx)
    rect("FUR", 3450, 4900, 3850, 5300, dx)
    # ---- 미니주방 ----
    rect("FUR", 4300, 200, 6200, 800, dx)         # 카운터
    rect("TOIL", 4450, 380, 4950, 680, dx)        # 싱크
    circle("TOIL", (4700, 300), 45, dx)
    circle("FUR", (5450, 500), 160, dx)           # 쿡탑
    circle("FUR", (5850, 500), 160, dx)
    rect("FUR", 6300, 200, 6800, 750, dx)         # 냉장고
    line("FUR", (6300, 200), (6800, 750), dx)
    text("0TEXT-1", "미니주방", (5250, 980), 180, dx)
    # ---- 문자 ----
    text("0TEXT-1", "패밀리룸", (3950, 3800), 350, dx)
    text("0TEXT-1", "45.5m² /13.76PY", (3950, 3420), 250, dx)
    # ---- 치수 ----
    for (p1, p2) in [((0,0),(3000,0)), ((3000,0),(3900,0)), ((3900,0),(7000,0))]:
        d = msp.add_linear_dim(base=(dx, -700), p1=(dx+p1[0], p1[1]), p2=(dx+p2[0], p2[1]),
                               dimstyle="D100", dxfattribs={"layer": "S-DIM"})
        d.render()
    d = msp.add_linear_dim(base=(dx, -1300), p1=(dx, 0), p2=(dx+W, 0),
                           dimstyle="D100", dxfattribs={"layer": "S-DIM"})
    d.render()
    for (p1, p2) in [((0,0),(0,2500)), ((0,2500),(0,6500))]:
        d = msp.add_linear_dim(base=(dx-700, 0), p1=(dx+p1[0], p1[1]), p2=(dx+p2[0], p2[1]),
                               angle=90, dimstyle="D100", dxfattribs={"layer": "S-DIM"})
        d.render()
    d = msp.add_linear_dim(base=(dx-1300, 0), p1=(dx, 0), p2=(dx, D),
                           angle=90, dimstyle="D100", dxfattribs={"layer": "S-DIM"})
    d.render()
    # 타이틀
    text("0TEXT-1", "패밀리룸 (FAMILY ROOM)", (3500, -2500), 500, dx)
    text("0TEXT-1", "전용 45.5m² /13.76PY  ·  7.0m × 6.5m  ·  기준 4인", (3500, -3150), 280, dx)
    text("0TEXT-1", "외부 (조망)", (3500, 6950), 280, dx, color=8)

# ---- 배치 ----
DX_DELUXE = 0
DX_FAMILY = 10500
unit_deluxe(DX_DELUXE)
unit_family(DX_FAMILY)

# ---- 복도 표기 ----
cen = doc.layers.get("0CEN")
line("0CEN", (-1000, -1900), (18500, -1900))
text("0TEXT-1", "복도 (CORRIDOR)", (8750, -1750), 300, color=8)

# ---- 시트 타이틀/주기 ----
text("0TEXT-1", "호텔 가은 — 객실 단위평면 계획", (8750, 8900), 700)
text("0TEXT-1", "디럭스룸 35.0m² · 패밀리룸 45.5m²  (참고도면 1·2 객실유닛 준용, 계획도면 0718 블록치수 적용)", (8750, 8100), 320, color=8)
notes = [
    "1. 벽체: 외벽·세대간벽 200THK, 욕실 칸막이벽 100THK",
    "2. 개구부: 객실 출입문 W900, 욕실문 W800, 외부창 W4600",
    "3. 디럭스룸(3F 북측 4실): 킹베드+라운지 구성, 기준 2인",
    "4. 패밀리룸(2F 전층·3F 남측): 더블+싱글2 구성, 미니주방·욕조 포함, 기준 4인",
    "5. 치수 단위: mm / 면적은 벽체 중심선 기준",
]
for i, n in enumerate(notes):
    t = msp.add_text(n, dxfattribs={"layer": "0TEXT-1", "style": "KOR", "height": 250, "color": 8})
    t.set_placement((-500, -4300 - i*450), align=ezdxf.enums.TextEntityAlignment.LEFT)

import os
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hotel-gaun-guestroom-plans.dxf")
doc.saveas(out)
print("saved:", out)

# ---- PNG 미리보기 ----
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy

fig = plt.figure(figsize=(20, 13), dpi=110)
ax = fig.add_axes([0, 0, 1, 1])
ctx = RenderContext(doc)
backend = MatplotlibBackend(ax)
cfg = Configuration(background_policy=BackgroundPolicy.WHITE)
Frontend(ctx, backend, config=cfg).draw_layout(msp, finalize=True)
png = out.replace(".dxf", ".png")
fig.savefig(png, dpi=110, facecolor="white")
print("saved:", png)
