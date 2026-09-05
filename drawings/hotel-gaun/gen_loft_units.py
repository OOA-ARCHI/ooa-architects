# -*- coding: utf-8 -*-
"""호텔 가은 4층 — 층고 상향형 객실 유닛 제안 (디럭스: 로프트베드 3안 / 패밀리: 복층 3안)

*** 가정(설계 전제) ***
- 2~3F 표준 층고 약 3,200mm 대비 4F만 4,500mm로 상향(+1,300mm) — 구조/설비 검토 필요한 제안값
- 디럭스(로프트베드): 하부 2,600 + 슬래브 300 + 상부(침대존) 1,600 — 침대만 다락화, 사다리 진입
- 패밀리(복층): 하부 2,200 + 슬래브 300 + 상부(자녀실) 2,000 — 실 단위 복층화, 계단 진입
- 참고도면·계획도면에는 단면/층고 정보가 없어 신규 가정 수치이며, 실시설계 전 구조기술사 검토 필수

블록 평면치수는 기존과 동일 유지: 디럭스 7.0×5.0m(35.0m²), 패밀리 7.0×6.5m(45.5m²)
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
          ("0TEXT-1",7),("S-DIM",1),("0CEN",9),("0LOFT",6),("0OTB",9),("STAIR",2)]
for n,c in LAYERS: doc.layers.add(n, color=c)
doc.layers.get("0CEN").dxf.linetype = "DASHDOT"
doc.layers.get("0LOFT").dxf.linetype = "DASHED"
msp = doc.modelspace()

ds = doc.dimstyles.add("D100")
for k,v in dict(dimtxt=230, dimasz=170, dimexe=110, dimexo=140, dimgap=70,
                dimdec=0, dimtad=1, dimclrd=1, dimclre=1, dimclrt=1).items():
    setattr(ds.dxf, k, v)
ds.dxf.dimtxsty = "KOR"

class TF:
    def __init__(self, x0, y0, W, D):
        self.x0, self.y0, self.W, self.D = x0, y0, W, D
    def pt(self, u, v): return (self.x0+u, self.y0+v)
    def rect(self, layer, x1, y1, x2, y2):
        msp.add_lwpolyline([self.pt(x1,y1), self.pt(x2,y1), self.pt(x2,y2), self.pt(x1,y2)],
                           close=True, dxfattribs={"layer": layer})
    def poly(self, layer, pts, close=True):
        msp.add_lwpolyline([self.pt(*p) for p in pts], close=close, dxfattribs={"layer": layer})
    def line(self, layer, p1, p2):
        msp.add_line(self.pt(*p1), self.pt(*p2), dxfattribs={"layer": layer})
    def circle(self, layer, c, r):
        msp.add_circle(self.pt(*c), r, dxfattribs={"layer": layer})
    def ellipse(self, layer, c, rx, ry):
        cc = self.pt(*c)
        if rx >= ry: msp.add_ellipse(cc, major_axis=(rx,0), ratio=ry/rx, dxfattribs={"layer": layer})
        else: msp.add_ellipse(cc, major_axis=(0,ry), ratio=rx/ry, dxfattribs={"layer": layer})
    def arc(self, layer, c, r, a1, a2):
        msp.add_arc(self.pt(*c), r, a1, a2, dxfattribs={"layer": layer})
    def wall(self, x1, y1, x2, y2):
        self.wallpoly([(x1,y1),(x2,y1),(x2,y2),(x1,y2)])
    def wallpoly(self, pts):
        wpts = [self.pt(*p) for p in pts]
        msp.add_lwpolyline(wpts, close=True, dxfattribs={"layer": "0CONC"})
        h = msp.add_hatch(color=8, dxfattribs={"layer": "해치벽체"})
        h.paths.add_polyline_path(wpts, is_closed=True)
        h.set_pattern_fill("ANSI31", scale=14.0, color=8)
    def text(self, s, pos, h, color=None, layer="0TEXT-1"):
        at = {"layer": layer, "style": "KOR", "height": h}
        if color is not None: at["color"] = color
        t = msp.add_text(s, dxfattribs=at)
        t.set_placement(self.pt(*pos), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    def door(self, hinge, leaf_angle, sweep, width, layer="DOOR"):
        a = math.radians(leaf_angle)
        tip = (hinge[0]+width*math.cos(a), hinge[1]+width*math.sin(a))
        self.line(layer, hinge, tip)
        a1, a2 = sorted([leaf_angle, leaf_angle+sweep])
        self.arc(layer, hinge, width, a1, a2)
    def window(self, x1, x2, yw1, yw2):
        t3 = (yw2-yw1)/3.0
        for y in (yw1, yw1+t3, yw2-t3, yw2): self.line("0WIN", (x1,y), (x2,y))
        self.line("0WIN", (x1,yw1), (x1,yw2)); self.line("0WIN", (x2,yw1), (x2,yw2))
    def dim(self, p1, p2, base, angle=0):
        d = msp.add_linear_dim(base=self.pt(*base), p1=self.pt(*p1), p2=self.pt(*p2),
                               angle=angle, dimstyle="D100", dxfattribs={"layer": "S-DIM"})
        d.render()

# ---- 가구 ----
def bed_v(tf, x1, y1, x2, y2, head="bottom"):
    tf.rect("FUR", x1, y1, x2, y2)
    w = x2-x1
    py1, py2 = (y1+120, y1+480) if head=="bottom" else (y2-480, y2-120)
    if w >= 1500:
        pw = (w-3*140)/2
        tf.rect("FUR", x1+140, py1, x1+140+pw, py2); tf.rect("FUR", x2-140-pw, py1, x2-140, py2)
    else:
        tf.rect("FUR", x1+160, py1, x2-160, py2)
    fy = y1+(y2-y1)*0.64 if head=="bottom" else y2-(y2-y1)*0.64
    tf.line("FUR", (x1,fy), (x2,fy))

def bed_h(tf, x1, y1, x2, y2, head="right"):
    tf.rect("FUR", x1, y1, x2, y2)
    h = y2-y1
    px1, px2 = (x2-480, x2-120) if head=="right" else (x1+120, x1+480)
    if h >= 1500:
        ph = (h-3*140)/2
        tf.rect("FUR", px1, y1+140, px2, y1+140+ph); tf.rect("FUR", px1, y2-140-ph, px2, y2-140)
    else:
        tf.rect("FUR", px1, y1+160, px2, y2-160)
    fx = x2-(x2-x1)*0.64 if head=="right" else x1+(x2-x1)*0.64
    tf.line("FUR", (fx,y1), (fx,y2))

def nightstand(tf, x1, y1, x2, y2):
    tf.rect("FUR", x1, y1, x2, y2); tf.circle("FUR", ((x1+x2)/2,(y1+y2)/2), 90)

def toilet(tf, cx, ty1, ty2):
    tf.rect("TOIL", cx-200, ty1, cx+200, ty2); tf.ellipse("TOIL", (cx, ty2+300), 210, 280)

def basin(tf, x1, y1, x2, y2):
    tf.rect("TOIL", x1, y1, x2, y2)
    cx, cy = (x1+x2)/2, (y1+y2)/2
    tf.ellipse("TOIL", (cx,cy), 240, 170); tf.circle("TOIL", (cx, y1+80), 40)

def shower(tf, x1, y1, x2, y2):
    tf.rect("TOIL", x1, y1, x2, y2)
    tf.line("TOIL", (x1,y1), (x2,y2)); tf.line("TOIL", (x1,y2), (x2,y1))

def wardrobe(tf, x1, y1, x2, y2, split="v"):
    tf.rect("FUR", x1, y1, x2, y2); tf.line("FUR", (x1,y1), (x2,y2))
    if split=="v": tf.line("FUR", ((x1+x2)/2,y1), ((x1+x2)/2,y2))
    else: tf.line("FUR", (x1,(y1+y2)/2), (x2,(y1+y2)/2))

def kitchenette(tf, x1, x2):
    tf.rect("FUR", x1, 200, x2, 750)
    tf.rect("TOIL", x1+120, 360, x1+560, 630); tf.circle("TOIL", (x1+340, 300), 40)
    tf.circle("FUR", (x2-380, 470), 140); tf.circle("FUR", (x2-700, 470), 140)

# ---- 로프트 전용 심볼 ----
def loft_edge(tf, pts):
    """다락/복층 바닥판 외곽선(점선) — 상부평면에서 아래층 윤곽과 구분용"""
    wpts = [tf.pt(*p) for p in pts]
    msp.add_lwpolyline(wpts, close=True, dxfattribs={"layer": "0LOFT", "lineweight": 30})

def guardrail(tf, p1, p2):
    tf.line("0LOFT", p1, p2)
    dx, dy = p2[0]-p1[0], p2[1]-p1[1]
    L = math.hypot(dx, dy)
    n = max(2, int(L/300))
    for i in range(n+1):
        x = p1[0] + dx*i/n; y = p1[1] + dy*i/n
        tf.line("0LOFT", (x,y), (x + (0 if dx else 60)*0, y))  # placeholder no-op safeguard
    # 난간 세로살 간략표기(중심점 3개)
    for t in (0.2, 0.5, 0.8):
        x = p1[0]+dx*t; y = p1[1]+dy*t
        tf.circle("0LOFT", (x,y), 30)

def otb_hatch(tf, x1, y1, x2, y2, label="OPEN TO BELOW"):
    """오픈보이드(하부개방) 표기: 사선 해치 + 점선 테두리"""
    tf.rect("0OTB", x1, y1, x2, y2)
    n = int((x2-x1+y2-y1)/450)
    for i in range(1, n):
        off = i*450
        x_a, y_a = x1+off, y1
        x_b, y_b = x1, y1+off
        if x_a > x2: y_a += (x_a-x2); x_a = x2
        if y_b > y2: x_b += (y_b-y2); y_b = y2
        if x_a >= x1 and y_b <= y2:
            tf.line("0OTB", (min(x_a,x2), y_a), (x_b, min(y_b,y2)))
    tf.text(label, ((x1+x2)/2, (y1+y2)/2), 150, color=9)

def ladder(tf, x, y1, y2, w=500):
    tf.line("STAIR", (x,y1), (x,y2)); tf.line("STAIR", (x+w,y1), (x+w,y2))
    n = int((y2-y1)/260)
    for i in range(1, n):
        y = y1 + (y2-y1)*i/n
        tf.line("STAIR", (x,y), (x+w,y))
    tf.text("사다리\nUP", (x+w/2, (y1+y2)/2), 130, color=9)

def stair_straight(tf, x1, y1, x2, y2, nsteps=8, vertical=True):
    tf.rect("STAIR", x1, y1, x2, y2)
    if vertical:
        for i in range(1, nsteps):
            y = y1 + (y2-y1)*i/nsteps
            tf.line("STAIR", (x1,y), (x2,y))
        tf.line("STAIR", (x1,(y1+y2)/2), (x2,y2))
        tf.text("UP", ((x1+x2)/2, y1+300), 160, color=9)
    else:
        for i in range(1, nsteps):
            x = x1 + (x2-x1)*i/nsteps
            tf.line("STAIR", (x,y1), (x,y2))
        tf.text("UP", (x1+300, (y1+y2)/2), 160, color=9)

def spiral_stair(tf, cx, cy, r, nsteps=12):
    tf.circle("STAIR", (cx,cy), r)
    tf.circle("STAIR", (cx,cy), r*0.22)
    for i in range(nsteps):
        a = math.radians(360*i/nsteps)
        x1, y1 = cx + r*0.22*math.cos(a), cy + r*0.22*math.sin(a)
        x2, y2 = cx + r*math.cos(a), cy + r*math.sin(a)
        tf.line("STAIR", (x1,y1), (x2,y2))
    tf.text("나선계단 UP", (cx, cy-r-260), 150, color=9)

def shell(tf, door_x1, door_x2, win_x1, win_x2):
    W, D = tf.W, tf.D
    tf.wall(0, 0, door_x1, 200); tf.wall(door_x2, 0, W, 200)
    tf.wall(0, D-200, win_x1, D); tf.wall(win_x2, D-200, W, D)
    tf.wall(0, 200, 200, D-200); tf.wall(W-200, 200, W, D-200)
    tf.window(win_x1, win_x2, D-200, D)
    tf.door((door_x2, 200), 90, 90, door_x2-door_x1)

def shell_dashed(tf):
    """상부(로프트/복층) 평면의 외곽 — 벽체 없이 하부 외곽선만 점선 참조"""
    W, D = tf.W, tf.D
    tf.rect("0CEN", 0, 0, W, D)

# ================= 디럭스: 로프트베드 3안 (7000×5000, F2F 4500 가정) =================

def dlx_loft_A_lower(tf):
    """A. 사다리형 — 욕실 위 침대 다락. 하부: 라운지+워크스루"""
    shell(tf, 2700, 3600, 1200, 5800)
    tf.wall(2400, 200, 2500, 2400); tf.wall(200, 2300, 2400, 2400)
    shower(tf, 200, 1400, 1100, 2300); toilet(tf, 700, 250, 470); basin(tf, 1500, 200, 2400, 750)
    tf.text("욕실", (1600, 1150), 180); tf.door((2400, 1300), 180, -90, 800)
    tf.rect("FUR", 5900, 2500, 6800, 4700)             # 하부 소파(창측 라운지)
    tf.rect("FUR", 5970, 2570, 6730, 4630)
    tf.circle("FUR", (5400, 3600), 260)
    wardrobe(tf, 4200, 200, 6000, 850, split="v")
    ladder(tf, 3500, 1600, 3900, w=550)                 # 다락 진입 사다리 (욕실 옆)
    tf.text("오픈 라운지\n(층고 2,600)", (5450, 4900), 170, color=9)
    tf.text("워크스루", (3500, 1350), 150, color=9)

def dlx_loft_A_upper(tf):
    shell_dashed(tf)
    loft_edge(tf, [(2900,200),(6800,200),(6800,4800),(2900,4800)])   # 침대 다락 슬래브
    otb_hatch(tf, 200, 200, 2900, 4800, "오픈보이드\n(하부 라운지)")
    bed_v(tf, 3400, 2700, 5200, 4700, head="bottom")
    nightstand(tf, 3400, 2200, 3850, 2650); nightstand(tf, 4750, 2200, 5200, 2650)
    tf.rect("FUR", 5600, 2700, 6600, 3300)              # 낮은 협탁겸 수납
    guardrail(tf, (2900,200), (2900,4800))
    tf.text("침대 다락 (UP)", (5000, 1000), 200, color=6)
    tf.text("상부 층고 1,600 (좌식)", (5000, 500), 160, color=8)

def dlx_loft_B_lower(tf):
    """B. 계단식 좌대 — 침대 하부를 수납계단으로, 낮은 진입"""
    shell(tf, 2700, 3600, 1200, 5800)
    tf.wall(5600, 200, 5700, 2400); tf.wall(5700, 2300, 6800, 2400)
    shower(tf, 5900, 1400, 6800, 2300); toilet(tf, 6350, 250, 470); basin(tf, 4600, 200, 5600, 750)
    tf.text("욕실", (6250, 1150), 180); tf.door((5700, 1400), 0, -90, 800)
    wardrobe(tf, 200, 200, 2000, 850, split="v")
    tf.rect("FUR", 200, 1200, 3600, 2100)                # 소파(하부 리빙)
    tf.rect("FUR", 250, 1250, 3550, 2050)
    tf.circle("FUR", (4100, 1650), 250)
    # 계단식 수납 스텝(침대 다락 진입 겸 서랍장)
    for i in range(4):
        tf.rect("FUR", 200+ i*550, 2400, 200+(i+1)*530, 2400+ (i+1)*180)
    tf.text("계단식 수납\n(다락 진입)", (1400, 3450), 160, color=9)
    tf.text("오픈 리빙 (층고 2,600)", (2000, 900), 170, color=9)

def dlx_loft_B_upper(tf):
    shell_dashed(tf)
    loft_edge(tf, [(200,2500),(6800,2500),(6800,4800),(200,4800)])
    otb_hatch(tf, 200, 200, 6800, 2500, "오픈보이드\n(하부 리빙+욕실)")
    bed_h(tf, 300, 2700, 3900, 4700, head="left")
    nightstand(tf, 3950, 2700, 4400, 3150)
    tf.rect("FUR", 4700, 2700, 6600, 3600)               # 세컨드 라운지(다락)
    tf.rect("FUR", 4770, 2770, 6530, 3530)
    guardrail(tf, (200,2500), (6800,2500))
    tf.text("침대 다락 (UP)", (3500, 3900), 200, color=6)
    tf.text("상부 층고 1,600 (좌식)", (3500, 4300), 160, color=8)

def dlx_loft_C_lower(tf):
    """C. 2단 벙커형 — 실제 2층침대(트윈+트윈) 다락, 1~2인 유동수요 대응"""
    shell(tf, 2700, 3600, 1200, 5800)
    tf.wall(2400, 200, 2500, 1300); tf.wall(2400, 2100, 2500, 2400); tf.wall(200, 2300, 2400, 2400)
    shower(tf, 200, 1400, 1100, 2300); toilet(tf, 700, 250, 470); basin(tf, 1500, 200, 2400, 750)
    tf.text("욕실", (1600, 1150), 180); tf.door((2400, 1300), 180, -90, 800)
    tf.rect("FUR", 2650, 200, 4450, 800)                 # 데스크(하부)
    tf.rect("FUR", 4600, 200, 6000, 850)
    tf.rect("FUR", 5900, 2500, 6800, 4600); tf.rect("FUR", 5970, 2570, 6730, 4530)  # 라운지 체어
    ladder(tf, 4600, 1600, 2050, w=500)
    tf.text("오픈 데스크존\n(층고 2,600)", (3500, 3400), 170, color=9)

def dlx_loft_C_upper(tf):
    shell_dashed(tf)
    loft_edge(tf, [(2900,200),(6800,200),(6800,4800),(2900,4800)])
    otb_hatch(tf, 200, 200, 2900, 4800, "오픈보이드\n(하부 데스크존)")
    bed_h(tf, 3200, 2900, 6600, 3850, head="right")      # 상단 벙커 (트윈)
    bed_h(tf, 3200, 900, 6600, 1850, head="right")       # 하단 벙커 (트윈) — 다락 슬래브 위 배치
    tf.line("FUR", (3200, 2400), (6600, 2400))           # 벙커 프레임 표시선
    guardrail(tf, (2900,200), (2900,4800))
    tf.text("벙커 침대 다락 (UP)", (4900, 4300), 190, color=6)
    tf.text("상부 층고 1,600 (좌식) · 트윈×2", (4900, 3950), 150, color=8)

# ================= 패밀리: 복층 3안 (7000×6500, F2F 4500 가정) =================

def fam_duplex_A_lower(tf):
    """A. 1F 부모+거실 / 2F 자녀 다락실 — 계단은 코너 직선형"""
    shell(tf, 2900, 3800, 1200, 5800)
    tf.wall(2600, 200, 2700, 1350); tf.wall(2600, 2150, 2700, 2500); tf.wall(200, 2400, 2600, 2500)
    shower(tf, 200, 1650, 1700, 2400); toilet(tf, 550, 250, 470); basin(tf, 1500, 200, 2600, 750)
    tf.text("욕실", (1150, 1150), 180); tf.door((2600, 2150), 180, 90, 800)
    kitchenette(tf, 4400, 6100)
    tf.text("미니주방", (5250, 980), 160)
    tf.rect("FUR", 650, 2600, 2550, 2700)
    bed_v(tf, 700, 2700, 2500, 4600, head="bottom")
    nightstand(tf, 2600, 2700, 3050, 3150)
    stair_straight(tf, 6100, 2700, 6800, 5600, nsteps=9, vertical=True)
    tf.rect("FUR", 3200, 5000, 5800, 6100); tf.rect("FUR", 3270, 5070, 5730, 6030)  # 소파(리빙)
    tf.text("부모존 + 거실 (층고 2,200)", (1600, 5800), 190, color=9)

def fam_duplex_A_upper(tf):
    shell_dashed(tf)
    loft_edge(tf, [(200,200),(6800,200),(6800,6300),(200,6300)])
    stair_straight(tf, 6100, 4600, 6800, 6300, nsteps=9, vertical=True)  # 상부 계단참(연속 표기)
    bed_h(tf, 300, 3200, 2300, 4300, head="left")
    bed_h(tf, 300, 4700, 2300, 5800, head="left")
    tf.rect("FUR", 2600, 3200, 4600, 5800)               # 놀이존 매트
    tf.circle("FUR", (3600, 4500), 350)
    wardrobe(tf, 200, 200, 1900, 850, split="v")
    tf.text("자녀실 (UP)", (3500, 1300), 220, color=6)
    tf.text("상부 층고 2,000 · 싱글×2 + 놀이존", (3500, 780), 160, color=8)

def fam_duplex_B_lower(tf):
    """B. 1F 리빙+주방 / 2F 마스터침실 — 계단은 스킵플로어 중앙 배치"""
    shell(tf, 2900, 3800, 1200, 5800)
    tf.wall(5900, 200, 6000, 1350); tf.wall(5900, 2150, 6000, 2500); tf.wall(6000, 2400, 6800, 2500)
    shower(tf, 5900, 1650, 6800, 2400); toilet(tf, 6350, 250, 470); basin(tf, 4900, 200, 5900, 750)
    tf.text("욕실", (6400, 1150), 180); tf.door((6000, 1650), 0, -90, 800)
    kitchenette(tf, 200, 2000)
    tf.text("미니주방", (1100, 980), 160)
    tf.rect("FUR", 2500, 2700, 5300, 4400); tf.rect("FUR", 2570, 2770, 5230, 4330)  # 대형 소파
    tf.rect("FUR", 3200, 4700, 4600, 5500); tf.circle("FUR", (3900, 5000), 60)      # 티테이블
    stair_straight(tf, 200, 4600, 900, 6300, nsteps=9, vertical=True)
    tf.text("리빙 + 주방 (층고 2,200)", (3900, 5900), 190, color=9)

def fam_duplex_B_upper(tf):
    shell_dashed(tf)
    loft_edge(tf, [(200,200),(6800,200),(6800,6300),(200,6300)])
    stair_straight(tf, 200, 200, 900, 1900, nsteps=9, vertical=False)
    bed_v(tf, 3000, 3800, 4900, 5800, head="bottom")
    nightstand(tf, 2450, 3850, 2950, 4300); nightstand(tf, 4950, 3850, 5450, 4300)
    wardrobe(tf, 5500, 3800, 6800, 4600, split="h")
    tf.rect("FUR", 1200, 3900, 2200, 4500)               # 화장대
    tf.text("마스터침실 (UP)", (3900, 2600), 220, color=6)
    tf.text("상부 층고 2,000", (3900, 2100), 160, color=8)

def fam_duplex_C_lower(tf):
    """C. 스킵플로어(반층) — 나선계단, 1F 주방+욕실+거실, 2F 통합 베드룸(더블+트윈)"""
    shell(tf, 2900, 3800, 1200, 5800)
    tf.wall(2600, 200, 2700, 1350); tf.wall(2600, 2150, 2700, 2500); tf.wall(200, 2400, 2600, 2500)
    shower(tf, 200, 1650, 1700, 2400); toilet(tf, 550, 250, 470); basin(tf, 1500, 200, 2600, 750)
    tf.text("욕실", (1150, 1150), 180); tf.door((2600, 2150), 180, 90, 800)
    kitchenette(tf, 4400, 6100)
    tf.text("미니주방", (5250, 980), 160)
    tf.rect("FUR", 700, 2700, 3600, 4300); tf.rect("FUR", 770, 2770, 3530, 4230)   # 소파
    spiral_stair(tf, 5600, 3400, 700, nsteps=12)
    tf.text("거실 (층고 2,200)", (2100, 5800), 190, color=9)

def fam_duplex_C_upper(tf):
    shell_dashed(tf)
    loft_edge(tf, [(200,200),(6800,200),(6800,6300),(200,6300)])
    spiral_stair(tf, 5600, 5200, 700, nsteps=12)
    bed_v(tf, 700, 3900, 2600, 5900, head="bottom")       # 더블(부모)
    nightstand(tf, 200, 3950, 650, 4400)
    bed_h(tf, 3100, 900, 5100, 1950, head="left")         # 트윈(자녀) 1
    bed_h(tf, 3100, 2150, 5100, 3200, head="left")        # 트윈(자녀) 2
    tf.line("0LOFT", (2900, 700), (2900, 6100))           # 침실 내 소프트 구획선(반투명 표기)
    tf.text("복합 베드룸 (UP)", (3900, 5300), 200, color=6)
    tf.text("상부 층고 2,000 · 더블+트윈×2", (3900, 4900), 150, color=8)

# ================= 개념 단면 (측면도, 유형별 2종) =================
def section_loftbed(tf, title):
    """디럭스 로프트베드 단면 개념: W=depth 5000, H=4500"""
    W, H = 5000, 4500
    tf.rect("0CONC", 0, 0, W, 200)                        # 바닥슬래브(하부)
    tf.rect("0CONC", 0, H-200, W, H)                       # 천장슬래브(상부)
    tf.rect("0CONC", 0, 200, 150, H-200); tf.rect("0CONC", W-150, 200, W, H-200)  # 벽
    # 다락 슬래브(2600 위치, depth 절반부터)
    tf.rect("0LOFT", W*0.4, 2600, W, 2900)
    tf.rect("FUR", W*0.55, 2950, W*0.85, 3500)             # 침대(측면)
    tf.line("0LOFT", (W*0.4, 200), (W*0.4, 2600))          # 사다리 개념선
    tf.dim((0,0), (0,2600), (-500,0), 90)
    tf.dim((0,2600), (0,2900), (-500,0), 90)
    tf.dim((0,2900), (0,H), (-500,0), 90)
    tf.dim((0,0), (0,H), (-1200,0), 90)
    tf.text("하부(라운지)\n2,600", (W*0.2, 1300), 130, color=8)
    tf.text("슬래브 300", (W*0.2, 2750), 120, color=8)
    tf.text("상부(침대다락)\n1,600", (W*0.7, 3750), 130, color=8)
    tf.text(title, (W/2, H+500), 240)

def section_duplex(tf, title):
    """패밀리 복층 단면 개념: W=depth 6500, H=4500"""
    W, H = 6500, 4500
    tf.rect("0CONC", 0, 0, W, 200)
    tf.rect("0CONC", 0, H-200, W, H)
    tf.rect("0CONC", 0, 200, 150, H-200); tf.rect("0CONC", W-150, 200, W, H-200)
    tf.rect("0LOFT", 0, 2200, W, 2500)                     # 복층 슬래브(전체 폭)
    tf.rect("FUR", W*0.55, 2550, W*0.85, 3200)             # 상부 침대(측면)
    tf.rect("FUR", W*0.1, 350, W*0.35, 1200)               # 하부 소파(측면)
    tf.line("0LOFT", (W*0.42, 200), (W*0.42, 2200))        # 계단 개념선
    tf.dim((0,0), (0,2200), (-500,0), 90)
    tf.dim((0,2200), (0,2500), (-500,0), 90)
    tf.dim((0,2500), (0,H), (-500,0), 90)
    tf.dim((0,0), (0,H), (-1200,0), 90)
    tf.text("하부(주방·욕실·거실)\n2,200", (W*0.2, 1100), 130, color=8)
    tf.text("슬래브 300", (W*0.2, 2350), 120, color=8)
    tf.text("상부(자녀실/침실)\n2,000", (W*0.7, 3500), 130, color=8)
    tf.text(title, (W/2, H+500), 240)

# ================= 배치 =================
def unit_triptych(x0, y0, W, D, lower_fn, upper_fn, title, sub, tags):
    GAP = 1400
    tf_low = TF(x0, y0, W, D); lower_fn(tf_low)
    tf_up  = TF(x0+W+GAP, y0, W, D); upper_fn(tf_up)
    for tf in (tf_low, tf_up):
        tf.dim((0,0),(W,0),(0,-650),0); tf.dim((0,0),(0,D),(-650,0),90)
    tf_low.text("하부평면 (1F)", (W/2, -1550), 260)
    tf_up.text("상부평면 (로프트/2F)", (W/2, -1550), 260)
    cx = x0 + W + GAP/2
    t = msp.add_text(title, dxfattribs={"layer":"0TEXT-1","style":"KOR","height":420})
    t.set_placement((cx, y0-2500), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    t = msp.add_text(sub, dxfattribs={"layer":"0TEXT-1","style":"KOR","height":260,"color":8})
    t.set_placement((cx, y0-3150), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    t = msp.add_text(tags, dxfattribs={"layer":"0TEXT-1","style":"KOR","height":230,"color":9})
    t.set_placement((cx, y0-3700), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    return x0 + 2*W + GAP

# 디럭스 로프트 3안 (Row 1)
Y_DLX = 0
x = 0
x = unit_triptych(x, Y_DLX, 7000, 5000, dlx_loft_A_lower, dlx_loft_A_upper,
                   "디럭스 로프트 A — 사다리형", "35.0m² /10.59PY · 욕실 위 침대다락 + 하부 라운지", "사다리 진입 · 상부 층고 1,600") + 3000
x = unit_triptych(x, Y_DLX, 7000, 5000, dlx_loft_B_lower, dlx_loft_B_upper,
                   "디럭스 로프트 B — 계단식수납형", "35.0m² /10.59PY · 계단식 수납 진입 + 세컨드 라운지", "수납겸용 스텝 · 상부 층고 1,600") + 3000
x = unit_triptych(x, Y_DLX, 7000, 5000, dlx_loft_C_lower, dlx_loft_C_upper,
                   "디럭스 로프트 C — 벙커형(2층침대)", "35.0m² /10.59PY · 실제 2층침대(트윈×2) + 하부 데스크존", "1~4인 유동수요 대응")

# 단면 (디럭스 로프트 공통 개념)
tf_sec = TF(x+1500, Y_DLX+400, 5000, 4500)
section_loftbed(tf_sec, "로프트베드 개념단면 (디럭스 공통)")

# 패밀리 복층 3안 (Row 2)
Y_FAM = -15500
x = 0
x = unit_triptych(x, Y_FAM, 7000, 6500, fam_duplex_A_lower, fam_duplex_A_upper,
                   "패밀리 복층 A — 코너계단형", "45.5m² /13.76PY · 1F 부모+거실 / 2F 자녀 다락실", "직선계단 · 상부 층고 2,000") + 3000
x = unit_triptych(x, Y_FAM, 7000, 6500, fam_duplex_B_lower, fam_duplex_B_upper,
                   "패밀리 복층 B — 마스터업형", "45.5m² /13.76PY · 1F 리빙+주방 / 2F 마스터침실", "대형소파+티테이블") + 3000
x = unit_triptych(x, Y_FAM, 7000, 6500, fam_duplex_C_lower, fam_duplex_C_upper,
                   "패밀리 복층 C — 나선계단형", "45.5m² /13.76PY · 1F 거실+주방 / 2F 통합베드룸(더블+트윈)", "나선계단 · 최소면적 코어")

tf_sec2 = TF(x+1500, Y_FAM+400, 6500, 4500)
section_duplex(tf_sec2, "복층 개념단면 (패밀리 공통)")

# ---- 시트 타이틀/전제 주기 ----
t = msp.add_text("호텔 가은 4층 — 층고 상향형 객실 유닛 제안 (디럭스 로프트베드 3안 · 패밀리 복층 3안)",
                 dxfattribs={"layer":"0TEXT-1","style":"KOR","height":950})
t.set_placement((15000, 9700), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
t = msp.add_text("4F 층고 4,500mm 상향 가정(2~3F 대비 +1,300) · 디럭스=침대만 다락화(로프트베드) · 패밀리=실 단위 복층화",
                 dxfattribs={"layer":"0TEXT-1","style":"KOR","height":360,"color":8})
t.set_placement((15000, 8600), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

NOTE_Y0 = Y_FAM - 5200
notes = [
    "1. [가정] 본 제안의 층고·단면 수치는 계획도면에 근거 자료가 없어 신규 설정한 값입니다. 구조기술사·설비 협의 후 확정 필요.",
    "2. 4F 층고안: 4,500mm (2~3F 표준 약 3,200mm 대비 +1,300). 디럭스: 하부 2,600+슬래브 300+상부 1,600 / 패밀리: 하부 2,200+슬래브 300+상부 2,000",
    "3. 디럭스(로프트베드): 침대만 다락으로 올려 하부에 라운지·데스크 등 개방형 공간 확보. 상부는 좌식 눈높이(입식 불가) — 사다리/계단식 수납으로 진입",
    "4. 패밀리(복층): 실(자녀실·마스터침실) 단위로 상부를 구성해 상부에서도 착석 가능한 층고(2,000) 확보. 계단(직선/나선)으로 진입, 안전난간 필수",
    "5. 상부평면 점선(0LOFT)은 다락/복층 슬래브 외곽선, 해치존(0OTB)은 오픈보이드(하부 개방)를 의미. 난간고 1,100 이상, 계단 단높이 200 이하 권장",
    "6. 평면 폭(7.0m)은 기존 2~3F 블록치수와 동일 — 4F만 대상으로 하되 구조체(슬래브 증타·계단실) 반영 시 실면적 일부 조정 가능",
]
for i, n in enumerate(notes):
    t = msp.add_text(n, dxfattribs={"layer":"0TEXT-1","style":"KOR","height":300,"color":8})
    t.set_placement((0, NOTE_Y0 - i*580), align=ezdxf.enums.TextEntityAlignment.LEFT)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hotel-gaun-4f-loft-duplex-units.dxf")
doc.saveas(out)
print("saved:", out)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy

fig = plt.figure(figsize=(34, 26), dpi=105)
ax = fig.add_axes([0, 0, 1, 1])
Frontend(RenderContext(doc), MatplotlibBackend(ax),
         config=Configuration(background_policy=BackgroundPolicy.WHITE)).draw_layout(msp, finalize=True)
png = out.replace(".dxf", ".png")
fig.savefig(png, dpi=105, facecolor="white")
print("saved:", png)
