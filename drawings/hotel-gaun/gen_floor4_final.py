# -*- coding: utf-8 -*-
"""호텔 가은 4층 전체 평면도 — 로프트베드/복층 유닛 반영판 (계단·가구 겹침 재정리)

기존 4층(gen_floors.py floor_34f)의 벽체/복도/코어/문/욕실/주방 좌표는 그대로 유지하고
(리모델링 시 급배수 라이저·복도 연결 정합성 확보), 객실 내부 콘텐츠만
디럭스=로프트베드, 패밀리(45.5 코너 2실)=복층으로 교체.

*** 가정(설계 전제, 이전 제안과 동일) ***
- 4F 층고 4,500mm (2~3F 표준 약 3,200mm 대비 +1,300) — 구조/설비 검토 필요
- 디럭스 로프트: 하부 2,600 + 슬래브 300 + 상부(침대존) 1,600(좌식)
- 패밀리 복층: 하부 2,200 + 슬래브 300 + 상부(자녀실) 2,000(착석 가능)

*** 이번 재정리에서 고친 점 ***
- 사다리/계단을 방 중앙에 띄우지 않고, 벽체에 밀착한 코너에 배치(구조적으로도 타당)
- 계단/사다리 개구부(진입 지점)와 침대·소파·수납 가구가 평면상 겹치지 않도록 전 유닛 좌표 재계산
- 패밀리 45.0(9.0×5.0m, 저심도 비례)은 계단 확보가 어려워 이번 1차 반영에서 제외, 표준형 유지(주기에 명시)

단위: mm
"""
import ezdxf
from ezdxf import units
import math, os

doc = ezdxf.new("R2010", setup=True)
doc.units = units.MM
doc.header["$INSUNITS"] = 4
doc.styles.add("KOR", font="Pretendard-Regular.ttf")

LAYERS = [("0CONC",7),("해치벽체",8),("0WIN",4),("DOOR",2),("FUR",3),("TOIL",5),
          ("0TEXT-1",7),("S-DIM",1),("0CEN",9),("COL",8),("0LOFT",6),("0OTB",9),("STAIR",2)]
for n,c in LAYERS: doc.layers.add(n, color=c)
doc.layers.get("0CEN").dxf.linetype = "DASHDOT"
doc.layers.get("0LOFT").dxf.linetype = "DASHED"
msp = doc.modelspace()

ds = doc.dimstyles.add("D100")
for k,v in dict(dimtxt=300, dimasz=220, dimexe=150, dimexo=200, dimgap=90,
                dimdec=0, dimtad=1, dimclrd=1, dimclre=1, dimclrt=1).items():
    setattr(ds.dxf, k, v)
ds.dxf.dimtxsty = "KOR"

# ---------------- 변환(TF) ----------------
class TF:
    def __init__(self, x0, y0, W, D, mx=False, my=False):
        self.x0, self.y0, self.W, self.D, self.mx, self.my = x0, y0, W, D, mx, my
    def pt(self, u, v):
        u2 = self.W - u if self.mx else u
        v2 = self.D - v if self.my else v
        return (self.x0 + u2, self.y0 + v2)
    def ang(self, a):
        if self.mx and self.my: return (180 + a) % 360
        if self.mx: return (180 - a) % 360
        if self.my: return (-a) % 360
        return a % 360
    def rect(self, layer, x1, y1, x2, y2):
        p1, p2 = self.pt(x1,y1), self.pt(x2,y2)
        xa, xb = sorted((p1[0], p2[0])); ya, yb = sorted((p1[1], p2[1]))
        msp.add_lwpolyline([(xa,ya),(xb,ya),(xb,yb),(xa,yb)], close=True, dxfattribs={"layer": layer})
    def line(self, layer, p1, p2):
        msp.add_line(self.pt(*p1), self.pt(*p2), dxfattribs={"layer": layer})
    def circle(self, layer, c, r):
        msp.add_circle(self.pt(*c), r, dxfattribs={"layer": layer})
    def ellipse(self, layer, c, rx, ry):
        cc = self.pt(*c)
        if rx >= ry: msp.add_ellipse(cc, major_axis=(rx,0), ratio=ry/rx, dxfattribs={"layer": layer})
        else: msp.add_ellipse(cc, major_axis=(0,ry), ratio=rx/ry, dxfattribs={"layer": layer})
    def arc(self, layer, c, r, a1, a2):
        odd = self.mx != self.my
        na1, na2 = (self.ang(a2), self.ang(a1)) if odd else (self.ang(a1), self.ang(a2))
        msp.add_arc(self.pt(*c), r, na1, na2, dxfattribs={"layer": layer})
    def wall(self, x1, y1, x2, y2):
        p1, p2 = self.pt(x1,y1), self.pt(x2,y2)
        xa, xb = sorted((p1[0], p2[0])); ya, yb = sorted((p1[1], p2[1]))
        msp.add_lwpolyline([(xa,ya),(xb,ya),(xb,yb),(xa,yb)], close=True, dxfattribs={"layer": "0CONC"})
        h = msp.add_hatch(color=8, dxfattribs={"layer": "해치벽체"})
        h.paths.add_polyline_path([(xa,ya),(xb,ya),(xb,yb),(xa,yb)], is_closed=True)
        h.set_pattern_fill("ANSI31", scale=18.0, color=8)
    def text(self, s, pos, h, layer="0TEXT-1", color=None):
        at = {"layer": layer, "style": "KOR", "height": h}
        if color is not None: at["color"] = color
        t = msp.add_text(s, dxfattribs=at)
        t.set_placement(self.pt(*pos), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    def door(self, hinge, leaf_angle, sweep, width):
        a = math.radians(leaf_angle)
        tip = (hinge[0] + width*math.cos(a), hinge[1] + width*math.sin(a))
        self.line("DOOR", hinge, tip)
        a1, a2 = sorted([leaf_angle, leaf_angle + sweep])
        self.arc("DOOR", hinge, width, a1, a2)
    def window(self, x1, x2, yw1, yw2):
        t3 = (yw2 - yw1) / 3.0
        for y in (yw1, yw1+t3, yw2-t3, yw2): self.line("0WIN", (x1,y), (x2,y))
        self.line("0WIN", (x1,yw1), (x1,yw2)); self.line("0WIN", (x2,yw1), (x2,yw2))
    def window_v(self, y1, y2, xw1, xw2):
        t3 = (xw2 - xw1) / 3.0
        for x in (xw1, xw1+t3, xw2-t3, xw2): self.line("0WIN", (x,y1), (x,y2))
        self.line("0WIN", (xw1,y1), (xw2,y1)); self.line("0WIN", (xw1,y2), (xw2,y2))

# ---------------- 가구/위생기구 ----------------
def bed_v(tf, x1, y1, x2, y2, head="bottom"):
    tf.rect("FUR", x1, y1, x2, y2)
    w = x2 - x1
    py1, py2 = (y1+120, y1+520) if head=="bottom" else (y2-520, y2-120)
    if w >= 1500:
        pw = (w - 3*160)/2
        tf.rect("FUR", x1+160, py1, x1+160+pw, py2); tf.rect("FUR", x2-160-pw, py1, x2-160, py2)
    else:
        tf.rect("FUR", x1+180, py1, x2-180, py2)
    fy = y1 + (y2-y1)*0.62 if head=="bottom" else y2-(y2-y1)*0.62
    tf.line("FUR", (x1,fy), (x2,fy)); tf.line("FUR", (x1,fy+140 if head=="bottom" else fy-140), (x2,fy+140 if head=="bottom" else fy-140))

def bed_h(tf, x1, y1, x2, y2, head="right"):
    tf.rect("FUR", x1, y1, x2, y2)
    h = y2 - y1
    px1, px2 = (x2-520, x2-120) if head=="right" else (x1+120, x1+520)
    if h >= 1500:
        ph = (h - 3*160)/2
        tf.rect("FUR", px1, y1+160, px2, y1+160+ph); tf.rect("FUR", px1, y2-160-ph, px2, y2-160)
    else:
        tf.rect("FUR", px1, y1+180, px2, y2-180)
    fx = x2 - (x2-x1)*0.62 if head=="right" else x1+(x2-x1)*0.62
    tf.line("FUR", (fx,y1), (fx,y2))

def nightstand(tf, x1, y1, x2, y2):
    tf.rect("FUR", x1, y1, x2, y2); tf.circle("FUR", ((x1+x2)/2,(y1+y2)/2), 110)

def toilet(tf, cx, ty1, ty2):
    tf.rect("TOIL", cx-220, ty1, cx+220, ty2); tf.ellipse("TOIL", (cx, ty2+330), 230, 310)

def basin(tf, x1, y1, x2, y2):
    tf.rect("TOIL", x1, y1, x2, y2)
    cx, cy = (x1+x2)/2, (y1+y2)/2
    tf.ellipse("TOIL", (cx,cy), 270, 190); tf.circle("TOIL", (cx, y1+90), 45)

def shower(tf, x1, y1, x2, y2):
    tf.rect("TOIL", x1, y1, x2, y2)
    tf.line("TOIL", (x1,y1), (x2,y2)); tf.line("TOIL", (x1,y2), (x2,y1))

def bathtub(tf, x1, y1, x2, y2):
    tf.rect("TOIL", x1, y1, x2, y2); tf.rect("TOIL", x1+80, y1+80, x2-80, y2-80)
    tf.circle("TOIL", (x1+250, (y1+y2)/2), 80)

def wardrobe(tf, x1, y1, x2, y2, split="v"):
    tf.rect("FUR", x1, y1, x2, y2); tf.line("FUR", (x1,y1), (x2,y2))
    if split == "v": tf.line("FUR", ((x1+x2)/2,y1), ((x1+x2)/2,y2))
    else: tf.line("FUR", (x1,(y1+y2)/2), (x2,(y1+y2)/2))

def kitchenette(tf, x1, x2, fx1, fx2):
    tf.rect("FUR", x1, 200, x2, 800)
    tf.rect("TOIL", x1+150, 380, x1+650, 680); tf.circle("TOIL", (x1+400, 300), 45)
    tf.circle("FUR", (x2-900, 500), 160); tf.circle("FUR", (x2-500, 500), 160)
    tf.rect("FUR", fx1, 200, fx2, 750)

# ---- 로프트/복층 전용 심볼 (계단·사다리는 반드시 벽체 밀착 배치) ----
def loft_edge(tf, x1, y1, x2, y2):
    tf.rect("0LOFT", x1, y1, x2, y2)

def guardrail(tf, p1, p2):
    tf.line("0LOFT", p1, p2)
    dx, dy = p2[0]-p1[0], p2[1]-p1[1]
    for t in (0.15, 0.35, 0.5, 0.65, 0.85):
        tf.circle("0LOFT", (p1[0]+dx*t, p1[1]+dy*t), 30)

def otb_hatch(tf, x1, y1, x2, y2, label="오픈보이드\n(하부 개방)", label_h=150):
    tf.rect("0OTB", x1, y1, x2, y2)
    n = int((x2-x1+y2-y1)/450)
    for i in range(1, n):
        off = i*450
        xa, ya, xb, yb = x1+off, y1, x1, y1+off
        if xa > x2: ya += (xa-x2); xa = x2
        if yb > y2: xb += (yb-y2); yb = y2
        if xa >= x1 and yb <= y2:
            tf.line("0OTB", (min(xa,x2), ya), (xb, min(yb,y2)))
    if label:
        tf.text(label, ((x1+x2)/2, (y1+y2)/2), label_h, color=9)

def ladder(tf, x1, y1, x2, y2):
    """벽체 밀착형 사다리(평면기호): x1~x2 폭, y1~y2 방향으로 등반"""
    tf.rect("STAIR", x1, y1, x2, y2)
    n = max(3, int((y2-y1)/260))
    for i in range(1, n):
        y = y1 + (y2-y1)*i/n
        tf.line("STAIR", (x1,y), (x2,y))
    tf.text("사다리\nUP", ((x1+x2)/2, (y1+y2)/2), 130, color=9)

def stair_v(tf, x1, y1, x2, y2, nsteps=10):
    """벽체 밀착형 직선계단(수직 방향 상승)"""
    tf.rect("STAIR", x1, y1, x2, y2)
    for i in range(1, nsteps):
        y = y1 + (y2-y1)*i/nsteps
        tf.line("STAIR", (x1,y), (x2,y))
    tf.text("UP", ((x1+x2)/2, y1+300), 180, color=9)

def spiral_stair(tf, cx, cy, r, nsteps=12):
    """저심도 유닛용 나선계단 (지름 약 1300, 벽 코너 밀착 배치)"""
    tf.circle("STAIR", (cx,cy), r); tf.circle("STAIR", (cx,cy), r*0.22)
    for i in range(nsteps):
        a = math.radians(360*i/nsteps)
        tf.line("STAIR", (cx+r*0.22*math.cos(a), cy+r*0.22*math.sin(a)),
                          (cx+r*math.cos(a), cy+r*math.sin(a)))
    tf.text("나선계단\nUP", (cx, cy-r-260), 150, color=9)

def kitchenette2(tf, x1, y1, x2, y2, fridge=True):
    """디럭스용 간이주방(싱크+2구 인덕션, 임의 위치) — 정식 주방과 달리 소형 카운터형"""
    tf.rect("FUR", x1, y1, x2, y2)
    cw = x2 - x1
    tf.rect("TOIL", x1+120, y1+ (y2-y1)*0.2, x1+120+min(500,cw*0.35), y2-(y2-y1)*0.2)
    tf.circle("FUR", (x2-cw*0.22, (y1+y2)/2), min(140,(y2-y1)*0.28))
    tf.circle("FUR", (x2-cw*0.5, (y1+y2)/2), min(140,(y2-y1)*0.28))
    if fridge:
        tf.rect("FUR", x2+150, y1, x2+150+ (y2-y1), y2)  # 소형 냉장고(측면 배치)

# ================= 디럭스 로프트베드 — 최종안 (계단·가구 재배치) =================

def unit_dlx_a_loft(tf):
    """디럭스 로프트 외측형 (7000x5000) — 출입: 우측벽 하단, 욕실 원위치(좌하단) 유지
    간이주방 신설 + 사다리 위치 조정(진입 통과동선 y200~1300 확보)"""
    W, D = tf.W, tf.D
    # 욕실 (원위치 유지, 좌하단)
    tf.wall(2400, 200, 2500, 1300); tf.wall(2400, 2100, 2500, 2400); tf.wall(200, 2300, 2400, 2400)
    shower(tf, 200, 1400, 1100, 2300); toilet(tf, 700, 250, 470); basin(tf, 1500, 200, 2400, 750)
    tf.text("욕실", (1600, 1150), 190); tf.door((2400, 1300), 180, -90, 800)
    # 출입문 (우측벽 하단, 원위치 유지)
    tf.door((W-200, 300), 180, -90, 900)
    # 발코니창 (상단, 원위치 유지)
    tf.window(1200, 5800, D-200, D)
    # ---- 복층 상부존 해치(0OTB) — 침대다락이 얹히는 영역(x4300~6800)과 오픈보이드(x200~4300) 구분 ----
    # (가구보다 먼저 그려 배경 패턴으로 배치)
    otb_hatch(tf, 200, 200, 4300, 4800, label=None)
    guardrail(tf, (4300,200), (4300,4800))
    # ---- 통과동선(진입문→욕실) 확보: y200~1300 전 구간 가구 없음 ----
    # 사다리 (로프트 경계, 통과동선 위쪽으로 이동)
    ladder(tf, 4300, 1400, 4800, 2400)
    # 간이주방 (통과동선 위, 벽체 밀착) — 사다리와 이격 위해 냉장고 생략(싱크+2구 인덕션)
    kitchenette2(tf, 2700, 1400, 4100, 1950, fridge=False)
    tf.text("간이주방", (3400, 2150), 160, color=9)
    # 소파 (정적 공간 — 통과동선·주방·사다리에서 이격된 안쪽 코너)
    tf.rect("FUR", 5000, 1450, 6800, 2350); tf.rect("FUR", 5070, 1520, 6730, 2280)
    # TV장 (우측벽)
    tf.rect("FUR", 6300, 2700, 6800, 4200); tf.rect("FUR", 6330, 2900, 6400, 4000)
    # 라운지체어 + 티테이블 (창측, 정적 공간 — 창호에서 300 이격)
    tf.rect("FUR", 5200, 4000, 5900, 4500); tf.rect("FUR", 5270, 4070, 5830, 4460)
    tf.circle("FUR", (4700, 4250), 250)
    # 옷장 (욕실 옆, 통과동선·창호와 무관한 벽면 — 창호에서 300 이격)
    tf.rect("FUR", 200, 3700, 1300, 4500); tf.line("FUR", (200,3700), (1300,4500))
    tf.text("① 디럭스 로프트", (2700, 3900), 190)
    tf.text("(간이주방 · 2F 침대다락)", (2700, 3550), 150, color=8)

def unit_dlx_b_loft(tf):
    """디럭스 로프트 내측형 (7000x5000) — 출입: 하단벽, 욕실 원위치(중앙) 유지
    간이주방 신설 + 통과동선(진입문→욕실) 확보, 사다리는 창측 코너 유지"""
    W, D = tf.W, tf.D
    # 욕실 (원위치 유지, 중앙)
    tf.wall(3300, 200, 3400, 2400); tf.wall(5600, 200, 5700, 1350); tf.wall(5600, 2150, 5700, 2400)
    tf.wall(3400, 2300, 5700, 2400)
    shower(tf, 3400, 1400, 4300, 2300); toilet(tf, 3850, 250, 470); basin(tf, 4600, 200, 5600, 750)
    tf.text("욕실", (4450, 1150), 190); tf.door((5600, 2150), 180, 90, 800)
    # 출입문 (하단벽, 원위치 유지)
    tf.door((6600, 200), 90, 90, 900)
    # 창 (상단, 원위치 유지)
    tf.window(1200, 5800, D-200, D)
    # ---- 복층 상부존 해치(0OTB) — 침대다락이 얹히는 영역(x200~3300)과 오픈보이드(x3300~6800) 구분 ----
    otb_hatch(tf, 3300, 200, 6800, 4800, label=None)
    guardrail(tf, (3300,200), (3300,4800))
    # ---- 통과동선(진입문→욕실문, x3400~6600·y200~2150) 확보 ----
    # 사다리 (로프트 경계 x2800~3300, 상단벽 코너 — 창측, 침대와 이격)
    ladder(tf, 2800, 3900, 3300, 4700)
    # 간이주방 (욕실 하부, 통과동선 아래쪽 — 침실 진입 후 안쪽)
    kitchenette2(tf, 3600, 2600, 5000, 3150)
    tf.text("간이주방", (4300, 3350), 160, color=9)
    # 옷장 (좌측벽 상단, 통과동선·소파와 이격)
    wardrobe(tf, 200, 200, 1700, 1400, split="v")
    # 소파 (정적 공간, 로프트 아래 — 옷장에서 200 이격)
    tf.rect("FUR", 500, 1600, 2300, 2500); tf.rect("FUR", 570, 1670, 2230, 2430)
    # TV장 (좌측벽, 창측)
    tf.rect("FUR", 300, 3200, 1700, 3700)
    # 라운지 (창측, 정적 공간 — 창호에서 300 이격)
    tf.rect("FUR", 5200, 3700, 6800, 4500); tf.rect("FUR", 5270, 3770, 6730, 4460)
    tf.circle("FUR", (4900, 4050), 260)
    tf.text("② 디럭스 로프트", (1300, 4550), 190)
    tf.text("(간이주방 · 2F 침대다락)", (1300, 4200), 150, color=8)

# ================= 패밀리 복층 — 최종안 (계단·가구 재배치, 45.5 코너형) =================

def unit_fam_corner_duplex(tf, wide=False):
    """패밀리 복층 45.5(7000x6500) — 출입: 우측벽 하단, 욕실·미니주방 원위치 유지
    계단은 입구 옆 우측벽에 밀착(직선 10단). 부모 침대는 안쪽(정적) 코너에 배치,
    진입문→욕실 통과동선(y200~1300)은 가구 없이 확보"""
    W, D = tf.W, tf.D
    # 욕실 (원위치 유지, 좌하단)
    tf.wall(2600, 200, 2700, 1350); tf.wall(2600, 2150, 2700, 2500); tf.wall(200, 2400, 2600, 2500)
    bathtub(tf, 200, 1650, 1700, 2400); toilet(tf, 550, 250, 470); basin(tf, 1500, 200, 2600, 750)
    tf.text("욕실", (1150, 1150), 190); tf.door((2600, 2150), 180, 90, 800)
    # 미니주방 (원위치 유지, 진입 통과동선 상에 벽면 밀착 — 통행에 지장 없음)
    kitchenette(tf, 2800, W-2000, W-1900, W-1300)
    tf.text("미니주방", (3600, 980), 170)
    # 출입문 (우측벽 하단, 원위치 유지)
    tf.door((W-200, 300), 180, -90, 900)
    # ---- 복층 상부존 해치(0OTB) — 실 전체가 복층(2F 자녀실)이므로 계단실을 제외한 전 구간 표시 ----
    otb_hatch(tf, 200, 200, W-1000, D-200, label=None)
    otb_hatch(tf, W-1000, 200, W-200, 1300, label=None)
    # 계단 (입구 옆 우측벽 밀착, 직선 10단 — 문 스윙(y300~1200)과 이격해 y1400 시작)
    stair_v(tf, W-900, 1400, W-200, 3400, nsteps=10)
    tf.rect("FUR", W-900, 3600, W-200, 4200)                                     # 콘솔(계단 하부 수납)
    # ---- 부모 침대 (정적 공간 — 진입·주방·계단에서 가장 먼 안쪽 코너, 욕실 뒷벽) ----
    tf.rect("FUR", 500, 2850, 2500, 2950)                                        # 헤드보드
    bed_h(tf, 300, 2950, 2300, 4950, head="left")
    nightstand(tf, 2450, 2950, 2900, 3400)
    # 옷장 (침대 발치 옆, 소파와 200 이격)
    wardrobe(tf, 2500, 4200, 3100, 4900, split="h")
    # 좌식 소파 + 티테이블 (창측, 계단·주방·옷장과 이격된 정적 공간 — 창호에서 500 이격)
    tf.rect("FUR", 3900, 5100, 6300, 5800); tf.rect("FUR", 3970, 5170, 6230, 5730)
    tf.circle("FUR", (3300, 5450), 300)
    tf.text("부모 침실 + 거실 (층고 2,200)", (2000, 6050), 190, color=9)
    tf.text("2F 자녀실\n계단 개구부", (W-550, 2400), 140, color=8)
    tf.text("③ 패밀리 복층", (4700, 1500), 190)
    tf.text("(간이주방 · 2F 자녀실)", (4700, 1150), 150, color=8)

# ================= 층 골격 (기존 4층 벽체·복도·코어 그대로 재사용) =================

def south_wing_4f(F):
    F.wall(5000, 0, 6200, 200); F.wall(10800, 0, 13500, 200)
    F.wall(19500, 0, 27200, 200); F.wall(31800, 0, 33000, 200)
    F.window(6200, 10800, 0, 200); F.window(13500, 19500, 0, 200); F.window(27200, 31800, 0, 200)
    F.wall(5000, 200, 5200, 6500); F.wall(32800, 200, 33000, 6500)
    F.wall(5200, 6300, 12000, 6500)
    F.wall(12000, 6300, 12400, 6500); F.wall(17000, 6300, 17400, 6500)
    F.window(12400, 17000, 6300, 6500)
    F.wall(26000, 6300, 32800, 6500)
    F.wall(11900, 200, 12100, 5400); F.wall(11900, 6200, 12100, 6300)
    F.wall(25900, 200, 26100, 5400); F.wall(25900, 6200, 26100, 6300)
    F.wall(20900, 200, 21100, 4900)
    F.wall(12100, 4900, 17400, 5100); F.wall(18200, 4900, 21150, 5100); F.wall(21950, 4900, 25900, 5100)
    F.text("복도", (15100, 5750), 280, color=8)
    # 유닛 — 패밀리 3실 전체 복층으로 교체 (45.5 코너형 2실 + 45.0 저심도형 1실), 리넨실은 표준 유지
    unit_fam_corner_duplex(TF(F.x0+5000, F.y0+0, 7000, 6500, my=True))
    unit_fam_corner_duplex(TF(F.x0+26000, F.y0+0, 7000, 6500, mx=True, my=True))
    unit_fam45_duplex(TF(F.x0+12000, F.y0+0, 9000, 5000, my=True))
    unit_linen(TF(F.x0+21000, F.y0+0, 5000, 5000, my=True))
    F.text("리넨실", (23500, 2700), 340); F.text("25.0m² /7.56PY", (23500, 2200), 240)
    # 패밀리 복층 3실은 유닛 내부 소형 태그(③④) + 하단 실 스케줄로 표기 (겹침 방지)

def unit_fam45_duplex(tf):
    """패밀리 복층 45.0 (9000x5000, 저심도형) — 출입: 하단벽, 욕실·미니주방 원위치 유지
    나선계단(지름1200)으로 저심도 문제 해결. 부모 침대는 안쪽 정적 공간에 배치,
    진입문→욕실 통과동선(x5300~6400,y200~2150)은 가구 없이 확보"""
    W, D = tf.W, tf.D
    tf.wall(6300, 200, 6400, 1350); tf.wall(6300, 2150, 6400, 2400); tf.wall(6400, 2300, 8800, 2400)
    shower(tf, 7900, 1400, 8800, 2300); toilet(tf, 8350, 250, 470); basin(tf, 6500, 200, 7400, 700)
    tf.text("욕실", (7150, 1150), 200); tf.door((6400, 2150), 0, -90, 800)
    tf.door((6200, 200), 90, 90, 900)
    # 미니주방 (원위치에서 폭 축소 — 진입문 스윙(x5300~6200)과 300 이격 확보)
    kitchenette(tf, 3400, 5000, 2700, 3300); tf.text("미니주방", (4200, 980), 180)
    tf.window(1500, 7500, D-200, D)
    # ---- 복층 상부존 해치(0OTB) — 실 전체가 복층(2F 자녀실)이므로 나선계단실을 제외한 전 구간 표시 ----
    otb_hatch(tf, 2000, 200, W-200, D-200, label=None)
    otb_hatch(tf, 200, 900, 2000, D-200, label=None)
    # 옷장 (좌하단, 원위치 유지)
    wardrobe(tf, 200, 200, 2000, 850, split="v")
    # 나선계단 (좌측 상단 코너 — 저심도(5m)에서도 계단실 최소화, 통과동선과 무관한 벽 코너)
    spiral_stair(tf, 1050, 4100, 600, nsteps=12)
    # ---- 부모 침대 (정적 공간 — 진입·주방·계단·욕실에서 이격된 실 중앙부) ----
    tf.rect("FUR", 2300, 1050, 4300, 1150)                                       # 헤드보드
    bed_h(tf, 2300, 1200, 4300, 3150, head="left")
    nightstand(tf, 2300, 3300, 2800, 3750)
    # 소파 + 티테이블 (욕실 옆, 정적 공간 — 통과동선 아래쪽)
    tf.rect("FUR", 6300, 2650, 7300, 3600); tf.rect("FUR", 6370, 2720, 7230, 3530)
    tf.circle("FUR", (7700, 3100), 280)
    tf.text("④ 패밀리 복층", (4300, 4400), 190)
    tf.text("(2F 자녀실)", (4300, 4050), 150, color=8)

def unit_linen(tf):
    W, D = tf.W, tf.D
    tf.door((950, 200), 90, 90, 800)
    tf.rect("FUR", 4300, 200, 4800, 4800); tf.line("FUR", (4550,200), (4550,4800))
    tf.rect("FUR", 200, 4300, 4300, 4800); tf.line("FUR", (200,4550), (4300,4550))
    tf.rect("FUR", 200, 2900, 850, 3550); tf.circle("FUR", (525, 3225), 240)
    tf.rect("FUR", 200, 3650, 850, 4300); tf.circle("FUR", (525, 3975), 240)
    tf.text("세탁", (525, 2650), 180)

def connector_core(F):
    F.wall(17400, 6500, 17600, 8000); F.wall(17400, 14500, 17600, 16300)
    F.wall(27800, 6500, 28000, 16300)
    F.wall(21370, 6500, 28000, 6700); F.wall(21570, 12600, 27800, 12800)
    F.wall(21370, 6700, 21570, 8600); F.wall(21370, 9400, 21570, 10900); F.wall(21370, 11700, 21570, 12800)
    F.wall(24000, 6700, 24200, 12600)
    F.rect("FUR", 21570, 8000, 23900, 10000); F.line("FUR", (21570,8000),(23900,10000)); F.line("FUR", (21570,10000),(23900,8000))
    F.rect("FUR", 21570, 10300, 23900, 12300); F.line("FUR", (21570,10300),(23900,12300)); F.line("FUR", (21570,12300),(23900,10300))
    F.text("EV", (22700, 9000), 300); F.text("EV", (22700, 11300), 300)
    F.text("12인승 장애인겸용", (22700, 7350), 200, color=8)
    for i in range(9):
        x = 24600 + i*300
        F.line("FUR", (x, 6900), (x, 9500)); F.line("FUR", (x, 9900), (x, 12500))
    F.line("FUR", (24200, 9700), (27800, 9700))
    F.text("계단", (26500, 9700), 300); F.text("홀", (19400, 10900), 380)
    F.text("마주침 마당", (9000, 11300), 300, color=8)

def lounge(F, x1, x2, west_vend=True):
    if west_vend:
        F.rect("FUR", x1+100, 21900, x1+750, 22550); F.line("FUR", (x1+100,21900),(x1+750,22550))
        F.rect("FUR", x1+100, 21150, x1+750, 21800); F.line("FUR", (x1+100,21150),(x1+750,21800))
    else:
        F.rect("FUR", x2-750, 21900, x2-100, 22550); F.line("FUR", (x2-750,21900),(x2-100,22550))
        F.rect("FUR", x2-750, 21150, x2-100, 21800); F.line("FUR", (x2-750,21150),(x2-100,21800))
    cx = (x1+x2)/2
    F.circle("FUR", (cx, 19600), 400)
    for sx, sy in [(cx-750, 19400), (cx+350, 19400), (cx-200, 18600), (cx-200, 20400)]:
        F.rect("FUR", sx, sy, sx+400, sy+400)
    F.text("휴게공간", (cx, 21000-350), 300); F.text("(자판기)", (cx, 20250), 240, color=8)

def floor_4f(F):
    south_wing_4f(F); connector_core(F)
    F.wall(7000, 22600, 8200, 22800); F.wall(12800, 22600, 14300, 22800)
    F.wall(17200, 22600, 18700, 22800); F.wall(23300, 22600, 24500, 22800)
    F.window(8200, 12800, 22600, 22800); F.window(14300, 17200, 22600, 22800); F.window(18700, 23300, 22600, 22800)
    for xa, xb in [(0, 7000), (24500, 31500)]:
        F.line("0WIN", (xa, 22650), (xb, 22650)); F.line("0WIN", (xa, 22780), (xb, 22780))
        F.text("발코니", ((xa+xb)/2, 22150), 280, color=8)
    F.line("0WIN", (50, 21300), (50, 22780)); F.line("0WIN", (31450, 21300), (31450, 22780))
    F.wall(0, 21100, 1200, 21300); F.wall(5800, 21100, 7000, 21300); F.window(1200, 5800, 21100, 21300)
    F.wall(24500, 21100, 25700, 21300); F.wall(30300, 21100, 31500, 21300); F.window(25700, 30300, 21100, 21300)
    F.wall(0, 16300, 200, 21100); F.wall(31300, 16300, 31500, 21100)
    F.wall(200, 16300, 7000, 16500)
    F.wall(7000, 16300, 7400, 16500); F.wall(17000, 16300, 17400, 16500); F.window(7400, 17000, 16300, 16500)
    F.wall(24500, 16300, 31300, 16500)
    F.wall(6900, 16500, 7100, 16600); F.wall(6900, 17400, 7100, 22600)
    F.wall(24400, 16500, 24600, 16600); F.wall(24400, 17400, 24600, 22600)
    F.wall(7100, 17700, 12700, 17900); F.wall(13600, 17700, 14000, 17900)
    F.wall(17500, 17700, 17900, 17900); F.wall(18800, 17700, 24400, 17900)
    F.wall(13900, 17900, 14100, 22600); F.wall(17400, 17900, 17600, 22600)
    F.text("복도", (12000, 17100), 280, color=8)
    # ---- 유닛: 4실 전체 로프트베드로 교체 ----
    unit_dlx_a_loft(TF(F.x0+0, F.y0+16300, 7000, 5000))
    unit_dlx_a_loft(TF(F.x0+24500, F.y0+16300, 7000, 5000, mx=True))
    unit_dlx_b_loft(TF(F.x0+7000, F.y0+17800, 7000, 5000))
    unit_dlx_b_loft(TF(F.x0+17500, F.y0+17800, 7000, 5000, mx=True))
    lounge(F, 14100, 17400, west_vend=True)
    # 실명/면적은 각 유닛 내부의 소형 태그(①~④) + 하단 실 스케줄로 표기 (겹침 방지)

# ---------------- 치수 ----------------
def dims_common(F, north_chain):
    x0 = F.x0
    for a, b in [(0,5000),(5000,12000),(12000,21000),(21000,26000),(26000,33000)]:
        d = msp.add_linear_dim(base=(x0, F.y0-1200), p1=(x0+a, F.y0), p2=(x0+b, F.y0),
                               dimstyle="D100", dxfattribs={"layer": "S-DIM"}); d.render()
    d = msp.add_linear_dim(base=(x0, F.y0-2300), p1=(x0, F.y0), p2=(x0+33000, F.y0),
                           dimstyle="D100", dxfattribs={"layer": "S-DIM"}); d.render()
    prev = north_chain[0]
    for b in north_chain[1:]:
        d = msp.add_linear_dim(base=(x0, F.y0+24200), p1=(x0+prev, F.y0+22800), p2=(x0+b, F.y0+22800),
                               dimstyle="D100", dxfattribs={"layer": "S-DIM"}); d.render()
        prev = b
    for a, b in [(0,6500),(6500,16300),(16300,22800)]:
        d = msp.add_linear_dim(base=(x0-1200, F.y0), p1=(x0, F.y0+a), p2=(x0, F.y0+b),
                               angle=90, dimstyle="D100", dxfattribs={"layer": "S-DIM"}); d.render()
    d = msp.add_linear_dim(base=(x0-2300, F.y0), p1=(x0, F.y0), p2=(x0, F.y0+22800),
                           angle=90, dimstyle="D100", dxfattribs={"layer": "S-DIM"}); d.render()

# ---------------- 생성 ----------------
F = TF(0, 0, 33000, 22800)
floor_4f(F)
dims_common(F, [0, 7000, 14000, 17500, 24500, 31500])
# 치수선(하단)은 F.y0-2300 부근까지 사용 — 그 아래로 여백을 두고 타이틀/스케줄/주기를 순서대로 배치
Y0 = -3400
F.text("4F 평면도 (로프트베드/복층 유닛 전면 반영판 v2)", (16500, Y0), 900)
F.text("디럭스 로프트 4실(35.0m², 간이주방 포함) + 패밀리 복층 3실(45.0~45.5m²) + 리넨실 · 휴게공간 · 발코니", (16500, Y0-1200), 340, color=8)

Y1 = Y0 - 2400
schedule = [
    "① 디럭스 로프트 (외측형)  35.0m² /10.59PY  ×2실 — 1F 간이주방+소파+라운지(층고 2,600) / 2F 침대다락(층고 1,600)",
    "② 디럭스 로프트 (내측형)  35.0m² /10.59PY  ×2실 — 1F 간이주방+소파+라운지(층고 2,600) / 2F 침대다락(층고 1,600)",
    "③ 패밀리 복층 (코너형)    45.5m² /13.76PY  ×2실 — 1F 부모침실+미니주방+거실(층고 2,200) / 2F 자녀실(층고 2,000)",
    "④ 패밀리 복층 (저심도형)  45.0m² /13.61PY  ×1실 — 1F 부모침실+미니주방+소파(층고 2,200), 나선계단 / 2F 자녀실(층고 2,000)",
    "리넨실 25.0m² /7.56PY ×1실 — 표준형 유지",
]
t = msp.add_text("실 스케줄", dxfattribs={"layer":"0TEXT-1","style":"KOR","height":420})
t.set_placement((0, Y1), align=ezdxf.enums.TextEntityAlignment.LEFT)
for i, n in enumerate(schedule):
    t = msp.add_text(n, dxfattribs={"layer":"0TEXT-1","style":"KOR","height":300})
    t.set_placement((0, Y1 - 700 - i*580), align=ezdxf.enums.TextEntityAlignment.LEFT)

Y2 = Y1 - 700 - len(schedule)*580 - 700
notes = [
    "1. [가정] 층고·단면 수치는 계획도면에 근거 자료가 없어 신규 설정한 값입니다. 4F 층고 4,500mm(2~3F 대비 +1,300), 구조·설비 검토 필요.",
    "2. 디럭스 로프트: 하부 2,600(개방)+슬래브 300+상부 침대존 1,600(좌식) / 패밀리 복층: 하부 2,200+슬래브 300+상부 자녀실 2,000(착석 가능)",
    "3. [재정리 v2] 진입문→욕실 통과동선은 전 유닛에서 가구 없이 확보했고, 침대는 진입·주방·계단 동선에서 가장 먼 안쪽(정적) 공간에 배치했습니다.",
    "4. [재정리 v2] 디럭스 로프트 2종에 간이주방(싱크+2구 인덕션)을 신설했습니다. 사다리는 통과동선 위쪽(y1400~)으로 이동해 겹침 없이 재배치했습니다.",
    "5. [재정리 v2] 패밀리 45.0(저심도형)도 나선계단(지름1,200)을 적용해 복층으로 전환했습니다 — 직선계단 대비 계단실 면적을 최소화해 저심도 비례에서도 확보 가능.",
    "6. 욕실·미니주방·출입문 위치는 기존 2~3F 표준형과 동일 좌표를 유지해 급배수 라이저·복도 연결 정합성을 확보했습니다.",
    "7. 상부(로프트/2F) 평면과 개념단면은 별첨 hotel-gaun-4f-loft-duplex-units.dxf 참조. 이 시트는 4층 전체 평면 반영 결과(하부 기준)입니다.",
]
for i, n in enumerate(notes):
    t = msp.add_text(n, dxfattribs={"layer":"0TEXT-1","style":"KOR","height":330,"color":8})
    t.set_placement((0, Y2 - i*620), align=ezdxf.enums.TextEntityAlignment.LEFT)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hotel-gaun-4f-final.dxf")
doc.saveas(out)
print("saved:", out)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy

fig = plt.figure(figsize=(22, 17), dpi=120)
ax = fig.add_axes([0, 0, 1, 1])
Frontend(RenderContext(doc), MatplotlibBackend(ax),
         config=Configuration(background_policy=BackgroundPolicy.WHITE)).draw_layout(msp, finalize=True)
png = out.replace(".dxf", ".png")
fig.savefig(png, dpi=120, facecolor="white")
print("saved:", png)
