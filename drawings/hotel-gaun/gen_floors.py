# -*- coding: utf-8 -*-
"""호텔 가은 2·3·4층 전체 평면도 생성 — 층별 출입구 위치 반영

계획도면(0718)에서 추출한 데이터:
- 건물 외곽(ㄷ자형): 남측동 x5000~33000/y0~6500, 북측동 x0~31500/y16300~22800,
  연결부 x17400~28000/y6500~16300 (코어 EV·계단 6630×6300 at x21370,y6500)
- 남측동(2~4F 동일): 패밀리 45.5 ×2(측벽 코너 출입), 패밀리 45(북측벽 x17400~18200 출입),
  리넨실 25(북측벽 서단 출입)
- 북측 2F: 패밀리 55.9(동측벽 남단 출입) + 패밀리 48 ×2(남측벽, 중앙 휴게공간 양측 출입)
- 북측 3F/4F: 디럭스 35 ×4 엇갈림 배치 — 외측 2실 측벽 출입 + 북측 발코니,
  내측 2실 남측벽 휴게공간 양측 출입
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
          ("0TEXT-1",7),("S-DIM",1),("0CEN",9),("COL",8)]
for n,c in LAYERS: doc.layers.add(n, color=c)
doc.layers.get("0CEN").dxf.linetype = "DASHDOT"

msp = doc.modelspace()

ds = doc.dimstyles.add("D100")
for k,v in dict(dimtxt=300, dimasz=220, dimexe=150, dimexo=200, dimgap=90,
                dimdec=0, dimtad=1, dimclrd=1, dimclre=1, dimclrt=1).items():
    setattr(ds.dxf, k, v)
ds.dxf.dimtxsty = "KOR"

# ---------------- 변환(TF): 유닛 설계좌표 -> 월드좌표 ----------------
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
    # ---- primitives ----
    def rect(self, layer, x1, y1, x2, y2):
        p1, p2 = self.pt(x1,y1), self.pt(x2,y2)
        xa, xb = sorted((p1[0], p2[0])); ya, yb = sorted((p1[1], p2[1]))
        msp.add_lwpolyline([(xa,ya),(xb,ya),(xb,yb),(xa,yb)], close=True,
                           dxfattribs={"layer": layer})
    def line(self, layer, p1, p2):
        msp.add_line(self.pt(*p1), self.pt(*p2), dxfattribs={"layer": layer})
    def circle(self, layer, c, r):
        msp.add_circle(self.pt(*c), r, dxfattribs={"layer": layer})
    def ellipse(self, layer, c, rx, ry):
        cc = self.pt(*c)
        if rx >= ry:
            msp.add_ellipse(cc, major_axis=(rx,0), ratio=ry/rx, dxfattribs={"layer": layer})
        else:
            msp.add_ellipse(cc, major_axis=(0,ry), ratio=rx/ry, dxfattribs={"layer": layer})
    def arc(self, layer, c, r, a1, a2):
        odd = self.mx != self.my
        na1, na2 = (self.ang(a2), self.ang(a1)) if odd else (self.ang(a1), self.ang(a2))
        msp.add_arc(self.pt(*c), r, na1, na2, dxfattribs={"layer": layer})
    def wall(self, x1, y1, x2, y2):
        p1, p2 = self.pt(x1,y1), self.pt(x2,y2)
        xa, xb = sorted((p1[0], p2[0])); ya, yb = sorted((p1[1], p2[1]))
        msp.add_lwpolyline([(xa,ya),(xb,ya),(xb,yb),(xa,yb)], close=True,
                           dxfattribs={"layer": "0CONC"})
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
        for y in (yw1, yw1+t3, yw2-t3, yw2):
            self.line("0WIN", (x1,y), (x2,y))
        self.line("0WIN", (x1,yw1), (x1,yw2))
        self.line("0WIN", (x2,yw1), (x2,yw2))
    def window_v(self, y1, y2, xw1, xw2):
        t3 = (xw2 - xw1) / 3.0
        for x in (xw1, xw1+t3, xw2-t3, xw2):
            self.line("0WIN", (x,y1), (x,y2))
        self.line("0WIN", (xw1,y1), (xw2,y1))
        self.line("0WIN", (xw1,y2), (xw2,y2))

# ---------------- 가구/위생기구 (설계프레임) ----------------
def bed_v(tf, x1, y1, x2, y2):
    """세로 침대, 머리=하단"""
    tf.rect("FUR", x1, y1, x2, y2)
    w = x2 - x1
    if w >= 1500:
        pw = (w - 3*160)/2
        tf.rect("FUR", x1+160, y1+120, x1+160+pw, y1+520)
        tf.rect("FUR", x2-160-pw, y1+120, x2-160, y1+520)
    else:
        tf.rect("FUR", x1+180, y1+120, x2-180, y1+520)
    fy = y1 + (y2-y1)*0.62
    tf.line("FUR", (x1,fy), (x2,fy)); tf.line("FUR", (x1,fy+140), (x2,fy+140))
    tf.line("FUR", (x1,y2-220), (x1+220,y2))

def bed_h(tf, x1, y1, x2, y2, head="right"):
    """가로 침대"""
    tf.rect("FUR", x1, y1, x2, y2)
    h = y2 - y1
    if head == "right":
        if h >= 1500:
            ph = (h - 3*160)/2
            tf.rect("FUR", x2-520, y1+160, x2-120, y1+160+ph)
            tf.rect("FUR", x2-520, y2-160-ph, x2-120, y2-160)
        else:
            tf.rect("FUR", x2-520, y1+180, x2-120, y2-180)
        fx = x2 - (x2-x1)*0.62
        tf.line("FUR", (fx,y1), (fx,y2)); tf.line("FUR", (fx-140,y1), (fx-140,y2))
        tf.line("FUR", (x1+220,y1), (x1,y1+220))
    else:  # head left
        if h >= 1500:
            ph = (h - 3*160)/2
            tf.rect("FUR", x1+120, y1+160, x1+520, y1+160+ph)
            tf.rect("FUR", x1+120, y2-160-ph, x1+520, y2-160)
        else:
            tf.rect("FUR", x1+120, y1+180, x1+520, y2-180)
        fx = x1 + (x2-x1)*0.62
        tf.line("FUR", (fx,y1), (fx,y2)); tf.line("FUR", (fx+140,y1), (fx+140,y2))
        tf.line("FUR", (x2-220,y2), (x2,y2-220))

def bed_v_headtop(tf, x1, y1, x2, y2):
    """세로 침대, 머리=상단(창측)"""
    tf.rect("FUR", x1, y1, x2, y2)
    tf.rect("FUR", x1+180, y2-520, x2-180, y2-120)
    fy = y2 - (y2-y1)*0.62
    tf.line("FUR", (x1,fy), (x2,fy)); tf.line("FUR", (x1,fy-140), (x2,fy-140))
    tf.line("FUR", (x1,y1+220), (x1+220,y1))

def nightstand(tf, x1, y1, x2, y2):
    tf.rect("FUR", x1, y1, x2, y2)
    tf.circle("FUR", ((x1+x2)/2,(y1+y2)/2), 110)

def toilet(tf, cx, ty1, ty2):
    tf.rect("TOIL", cx-220, ty1, cx+220, ty2)
    tf.ellipse("TOIL", (cx, ty2+330), 230, 310)

def basin(tf, x1, y1, x2, y2):
    tf.rect("TOIL", x1, y1, x2, y2)
    cx, cy = (x1+x2)/2, (y1+y2)/2
    tf.ellipse("TOIL", (cx,cy), 270, 190)
    tf.circle("TOIL", (cx, y1+90), 45)

def shower(tf, x1, y1, x2, y2):
    tf.rect("TOIL", x1, y1, x2, y2)
    tf.line("TOIL", (x1,y1), (x2,y2)); tf.line("TOIL", (x1,y2), (x2,y1))

def bathtub(tf, x1, y1, x2, y2):
    tf.rect("TOIL", x1, y1, x2, y2)
    tf.rect("TOIL", x1+80, y1+80, x2-80, y2-80)
    tf.circle("TOIL", (x1+250, (y1+y2)/2), 80)

def wardrobe(tf, x1, y1, x2, y2, split="v"):
    tf.rect("FUR", x1, y1, x2, y2)
    tf.line("FUR", (x1,y1), (x2,y2))
    if split == "v": tf.line("FUR", ((x1+x2)/2,y1), ((x1+x2)/2,y2))
    else: tf.line("FUR", (x1,(y1+y2)/2), (x2,(y1+y2)/2))

def kitchenette(tf, x1, x2, fx1, fx2):
    """하단벽 카운터(y200~800) + 냉장고"""
    tf.rect("FUR", x1, 200, x2, 800)
    tf.rect("TOIL", x1+150, 380, x1+650, 680)          # 싱크
    tf.circle("TOIL", (x1+400, 300), 45)
    tf.circle("FUR", (x2-900, 500), 160)               # 쿡탑
    tf.circle("FUR", (x2-500, 500), 160)
    tf.rect("FUR", fx1, 200, fx2, 750)                 # 냉장고
    tf.line("FUR", (fx1,200), (fx2,750))

def tvunit_wall(tf, x1, y1, x2, y2, face):
    """TV장: face='E'|'W' 화면 방향"""
    tf.rect("FUR", x1, y1, x2, y2)
    if face == "E": tf.rect("FUR", x2-90, y1+200, x2-20, y2-200)
    else:           tf.rect("FUR", x1+20, y1+200, x1+90, y2-200)

# ---------------- 객실 유닛 (설계프레임: 창=상단) ----------------

def unit_fam_corner(tf, wide=False):
    """패밀리 45.5(7000x6500) / 55.9(8600x6500) — 출입: 우측벽 하단(v300~1100)"""
    W, D = tf.W, tf.D
    # 욕실 (좌하단)
    tf.wall(2600, 200, 2700, 1350); tf.wall(2600, 2150, 2700, 2500)
    tf.wall(200, 2400, 2600, 2500)
    bathtub(tf, 200, 1650, 1700, 2400)
    toilet(tf, 550, 250, 470)
    basin(tf, 1500, 200, 2600, 750)
    tf.text("욕실", (1150, 1150), 200)
    tf.door((2600, 2150), 180, 90, 800)               # 욕실문 -> 욕실 안쪽
    # 미니주방
    kitchenette(tf, 2800, W-2000, W-1900, W-1300)
    tf.text("미니주방", (3600, 980), 180)
    # 출입문 (우측벽 하단)
    tf.door((W-200, 300), 180, -90, 900)
    # 옷장 (우측벽, 출입문 위)
    wardrobe(tf, W-850, 1500, W-200, 3300, split="h")
    # 더블베드 (좌측, 머리=욕실벽)
    tf.rect("FUR", 650, 2500, 2550, 2600)
    bed_v(tf, 700, 2600, 2500, 4600)
    nightstand(tf, 2600, 2600, 3100, 3100)
    # 싱글베드 2 (우측벽, 머리=우측)
    bed_h(tf, W-2200, 3600, W-200, 4700, head="right")
    bed_h(tf, W-2200, 5000, W-200, 6100, head="right")
    # TV장 (좌측벽 상부)
    tvunit_wall(tf, 200, 4800, 650, 6100, face="E")
    # 좌식테이블 + 방석
    cxt = 3600 if not wide else 4200
    tf.circle("FUR", (cxt, 5600), 400)
    tf.rect("FUR", cxt-950, 5400, cxt-550, 5800)
    tf.rect("FUR", cxt+550, 5400, cxt+950, 5800)
    tf.rect("FUR", cxt-200, 4900, cxt+200, 5300)
    if wide:  # 55.9: 소파 추가
        tf.rect("FUR", 3400, 3300, 5200, 3950)
        tf.line("FUR", (3400, 3450), (5200, 3450))
    # 창 (상단)
    tf.window(1200, W-1200, D-200, D)

def unit_fam45(tf):
    """패밀리 45.0 (9000x5000) — 출입: 하단벽 u5400~6200"""
    W, D = tf.W, tf.D
    # 욕실 (우하단)
    tf.wall(6300, 200, 6400, 1350); tf.wall(6300, 2150, 6400, 2400)
    tf.wall(6400, 2300, 8800, 2400)
    shower(tf, 7900, 1400, 8800, 2300)
    toilet(tf, 8350, 250, 470)
    basin(tf, 6500, 200, 7400, 700)
    tf.text("욕실", (7150, 1150), 200)
    tf.door((6400, 2150), 0, -90, 800)
    # 출입문
    tf.door((6200, 200), 90, 90, 900)
    # 미니주방(문 좌측) + 냉장고
    kitchenette(tf, 3400, 5200, 2700, 3300)
    tf.text("미니주방", (4300, 980), 180)
    # 옷장 (좌하단)
    wardrobe(tf, 200, 200, 2000, 850, split="v")
    # 더블베드 (머리=좌측벽)
    bed_h(tf, 300, 2300, 2300, 4100, head="left")
    nightstand(tf, 300, 1750, 800, 2250)
    # 싱글베드 2 (우측벽, 머리=우측)
    bed_h(tf, 6800, 2450, 8800, 3550, head="right")
    bed_h(tf, 6800, 3700, 8800, 4800, head="right")
    # TV장 (욕실 칸막이벽, 화면=서측)
    tvunit_wall(tf, 5850, 2700, 6300, 4100, face="W")
    # 테이블 + 방석
    tf.circle("FUR", (4300, 4200), 350)
    tf.rect("FUR", 3550, 3950, 3950, 4350)
    tf.rect("FUR", 4650, 3950, 5050, 4350)
    # 창
    tf.window(1500, 7500, D-200, D)

def unit_fam48(tf):
    """패밀리 48.0 (9600x5000) — 출입: 하단벽 우측단 u8700~9500"""
    W, D = tf.W, tf.D
    # 욕실 (출입구 좌측)
    tf.wall(6200, 200, 6300, 2400)
    tf.wall(8600, 200, 8700, 1350); tf.wall(8600, 2150, 8700, 2400)
    tf.wall(6300, 2300, 8700, 2400)
    shower(tf, 6300, 1400, 7200, 2300)
    toilet(tf, 6750, 250, 470)
    basin(tf, 7500, 200, 8600, 750)
    tf.text("욕실", (7450, 1150), 200)
    tf.door((8600, 2150), 180, 90, 800)
    # 출입문
    tf.door((9500, 200), 90, 90, 900)
    # 옷장 (우측벽) / 옷장2 (좌하단)
    wardrobe(tf, 9000, 2600, 9600, 4400, split="h")
    wardrobe(tf, 200, 200, 1900, 850, split="v")
    # 미니주방
    kitchenette(tf, 3900, 6100, 3300, 3900)
    tf.text("미니주방", (4900, 980), 180)
    # TV장 (하단벽)
    tvunit_wall(tf, 2000, 200, 3200, 650, face="E")
    tf.rect("FUR", 2200, 560, 3000, 630)
    # 더블베드 (머리=좌측벽)
    bed_h(tf, 300, 2500, 2300, 4300, head="left")
    nightstand(tf, 300, 1950, 800, 2450)
    # 싱글베드 2 (중앙, 머리=창측)
    bed_v_headtop(tf, 4600, 2800, 5700, 4800)
    bed_v_headtop(tf, 6100, 2800, 7200, 4800)
    # 티테이블
    tf.circle("FUR", (8100, 3600), 350)
    tf.rect("FUR", 7900, 2750, 8300, 3150)
    # 창
    tf.window(1500, 8100, D-200, D)

def unit_dlx_b(tf):
    """디럭스 35.0 내측형 (7000x5000) — 출입: 하단벽 u5700~6600 (휴게공간측)"""
    W, D = tf.W, tf.D
    # 욕실
    tf.wall(3300, 200, 3400, 2400)
    tf.wall(5600, 200, 5700, 1350); tf.wall(5600, 2150, 5700, 2400)
    tf.wall(3400, 2300, 5700, 2400)
    shower(tf, 3400, 1400, 4300, 2300)
    toilet(tf, 3850, 250, 470)
    basin(tf, 4600, 200, 5600, 750)
    tf.text("욕실", (4450, 1150), 200)
    tf.door((5600, 2150), 180, 90, 800)
    # 출입문
    tf.door((6600, 200), 90, 90, 900)
    # 옷장 (우측벽)
    wardrobe(tf, 6150, 2500, 6800, 4300, split="h")
    # 킹베드 (머리=좌측벽)
    tf.rect("FUR", 200, 1550, 300, 3450)
    bed_h(tf, 300, 1600, 2300, 3400, head="left")
    nightstand(tf, 300, 1050, 800, 1550)
    nightstand(tf, 300, 3450, 800, 3950)
    # TV장 (욕실 칸막이벽, 화면=서측)
    tvunit_wall(tf, 3450, 1600, 3900, 3300, face="W")
    # 라운지 (창측)
    tf.rect("FUR", 5950, 4150, 6550, 4750); tf.rect("FUR", 6020, 4220, 6480, 4680)
    tf.circle("FUR", (5350, 4450), 300)
    tf.rect("FUR", 4600, 4200, 5050, 4650)
    # 창
    tf.window(1200, 5800, D-200, D)

def unit_dlx_a(tf):
    """디럭스 35.0 외측형 (7000x5000) — 출입: 우측벽 하단(v300~1100), 상부 발코니"""
    W, D = tf.W, tf.D
    # 욕실 (좌하단)
    tf.wall(2400, 200, 2500, 1300); tf.wall(2400, 2100, 2500, 2400)
    tf.wall(200, 2300, 2400, 2400)
    shower(tf, 200, 1400, 1100, 2300)
    toilet(tf, 700, 250, 470)
    basin(tf, 1500, 200, 2400, 750)
    tf.text("욕실", (1600, 1150), 200)
    tf.door((2400, 1300), 180, -90, 800)
    # 출입문 (우측벽 하단)
    tf.door((W-200, 300), 180, -90, 900)
    # 옷장 + 캐리어받침 (하단벽)
    wardrobe(tf, 2700, 200, 4500, 850, split="v")
    tf.rect("FUR", 4650, 250, 5350, 800)
    tf.line("FUR", (4650,250), (5350,800)); tf.line("FUR", (4650,800), (5350,250))
    # 킹베드 (머리=욕실벽)
    tf.rect("FUR", 950, 2400, 2850, 2500)
    bed_v(tf, 1000, 2500, 2800, 4500)
    nightstand(tf, 400, 2500, 900, 3000)
    nightstand(tf, 2900, 2500, 3400, 3000)
    # TV장 (우측벽)
    tvunit_wall(tf, 6350, 2500, 6800, 3900, face="W")
    # 라운지 (창측)
    tf.rect("FUR", 5750, 4100, 6350, 4700); tf.rect("FUR", 5820, 4170, 6280, 4630)
    tf.circle("FUR", (5300, 4400), 300)
    tf.rect("FUR", 4550, 4150, 5000, 4650)
    # 발코니창 (상단)
    tf.window(1200, 5800, D-200, D)

def unit_linen(tf):
    """리넨실 25 (5000x5000) — 출입: 하단벽 u150~950"""
    W, D = tf.W, tf.D
    tf.door((950, 200), 90, 90, 800)
    # 선반 (우측·상단), 세탁기/건조기 (좌측벽)
    tf.rect("FUR", 4300, 200, 4800, 4800); tf.line("FUR", (4550,200), (4550,4800))
    tf.rect("FUR", 200, 4300, 4300, 4800); tf.line("FUR", (200,4550), (4300,4550))
    tf.rect("FUR", 200, 2900, 850, 3550); tf.circle("FUR", (525, 3225), 240)
    tf.rect("FUR", 200, 3650, 850, 4300); tf.circle("FUR", (525, 3975), 240)
    tf.text("세탁", (525, 2650), 180)

# ---------------- 층 공통 골격 ----------------
ROOM_LABELS_S = [
    ("패밀리룸", "45.5m² /13.76PY", (8900, 3300)),
    ("패밀리룸", "45.0m² /13.61PY", (16100, 3375)),
    ("리넨실",   "25.0m² /7.56PY",  (23500, 2450)),
    ("패밀리룸", "45.5m² /13.76PY", (29100, 3300)),
]

def south_wing(F):
    """남측동 (2~4F 동일)"""
    # 외벽
    F.wall(5000, 0, 6200, 200); F.wall(10800, 0, 13500, 200)
    F.wall(19500, 0, 27200, 200); F.wall(31800, 0, 33000, 200)
    F.window(6200, 10800, 0, 200); F.window(13500, 19500, 0, 200)
    F.window(27200, 31800, 0, 200)
    F.wall(5000, 200, 5200, 6500)                      # 서측 외벽
    F.wall(32800, 200, 33000, 6500)                    # 동측 외벽
    F.wall(5200, 6300, 12000, 6500)                    # 45.5#1 북측 외벽
    F.wall(12000, 6300, 12400, 6500); F.wall(17000, 6300, 17400, 6500)
    F.window(12400, 17000, 6300, 6500)                 # 복도 창
    F.wall(26000, 6300, 32800, 6500)                   # 45.5#2 북측벽
    # 세대간벽 + 코너출입 개구부(y5400~6200)
    F.wall(11900, 200, 12100, 5400); F.wall(11900, 6200, 12100, 6300)
    F.wall(25900, 200, 26100, 5400); F.wall(25900, 6200, 26100, 6300)
    F.wall(20900, 200, 21100, 4900)                    # 45/리넨
    # 복도벽 (y4900~5100): 45문 17400~18200, 리넨문 21150~21950
    F.wall(12100, 4900, 17400, 5100)
    F.wall(18200, 4900, 21150, 5100)
    F.wall(21950, 4900, 25900, 5100)
    F.text("복도", (15100, 5750), 280, color=8)
    # 유닛
    unit_fam_corner(TF(F.x0+5000, F.y0+0, 7000, 6500, my=True))
    unit_fam_corner(TF(F.x0+26000, F.y0+0, 7000, 6500, mx=True, my=True))
    unit_fam45(TF(F.x0+12000, F.y0+0, 9000, 5000, my=True))
    unit_linen(TF(F.x0+21000, F.y0+0, 5000, 5000, my=True))
    for name, area, pos in ROOM_LABELS_S:
        F.text(name, (pos[0], pos[1]+250), 380)
        F.text(area, (pos[0], pos[1]-250), 260)

def connector_core(F):
    """연결부 + 코어 (2~4F 동일)"""
    # 연결부 외벽 (서: 홀 창 / 동)
    F.wall(17400, 6500, 17600, 8000); F.wall(17400, 14500, 17600, 16300)
    F.window_v(6500+1500, 14500, 17400, 17600)         # placeholder (아래에서 재정의)
    F.wall(27800, 6500, 28000, 16300)
    # 코어 (EV+계단) x21370~28000, y6500~12800
    F.wall(21370, 6500, 28000, 6700)                   # 남측벽
    F.wall(21570, 12600, 27800, 12800)                 # 북측벽
    F.wall(21370, 6700, 21570, 8600); F.wall(21370, 9400, 21570, 10900)
    F.wall(21370, 11700, 21570, 12800)                 # 서측벽 (EV 개구 2)
    F.wall(24000, 6700, 24200, 12600)                  # EV/계단 구획
    # EV 2대
    F.rect("FUR", 21570, 8000, 23900, 10000); F.line("FUR", (21570,8000),(23900,10000)); F.line("FUR", (21570,10000),(23900,8000))
    F.rect("FUR", 21570, 10300, 23900, 12300); F.line("FUR", (21570,10300),(23900,12300)); F.line("FUR", (21570,12300),(23900,10300))
    F.text("EV", (22700, 9000), 300); F.text("EV", (22700, 11300), 300)
    F.text("12인승 장애인겸용", (22700, 7350), 200, color=8)
    # 계단 (2련)
    for i in range(9):
        x = 24600 + i*300
        F.line("FUR", (x, 6900), (x, 9500)); F.line("FUR", (x, 9900), (x, 12500))
    F.line("FUR", (24200, 9700), (27800, 9700))
    F.text("계단", (26500, 9700), 300)
    F.text("홀", (19400, 10900), 380)
    F.text("마주침 마당", (9000, 11300), 300, color=8)

def floor_2f(F):
    south_wing(F); connector_core(F)
    # ---- 북측동 외벽 ----
    F.wall(0, 22600, 1200, 22800); F.wall(7400, 22600, 10100, 22800)
    F.wall(16700, 22600, 18500, 22800); F.wall(21600, 22600, 23400, 22800)
    F.wall(30000, 22600, 31500, 22800)
    F.window(1200, 7400, 22600, 22800)                 # 55.9 창
    F.window(18500, 21600, 22600, 22800)               # 휴게공간 창
    F.wall(0, 16300, 200, 22600)                       # 서측
    F.wall(31300, 16300, 31500, 22600)                 # 동측
    F.wall(200, 16300, 8600, 16500)                    # 55.9 남측 외벽
    F.wall(8600, 16300, 9000, 16500); F.wall(17000, 16300, 17400, 16500)
    F.window(9000, 17000, 16300, 16500)                # 복도 창(서)
    F.wall(28000, 16300, 28400, 16500); F.wall(31100, 16300, 31300, 16500)
    F.window(28400, 31100, 16300, 16500)               # 복도 창(동)
    # ---- 내벽 ----
    F.wall(8500, 16500, 8700, 16600); F.wall(8500, 17400, 8700, 22600)  # 55.9 동측벽+문개구
    F.wall(8700, 17700, 17300, 17900)                  # 복도벽(서) : 48#1 문 17300~18100
    F.wall(22800, 17700, 31300, 17900)                 # 복도벽(동) : 48#2 문 22000~22800
    F.wall(18100, 17900, 18300, 22600)                 # 48#1/휴게
    F.wall(21800, 17900, 22000, 22600)                 # 휴게/48#2
    F.text("복도", (13000, 17100), 280, color=8)
    # ---- 유닛 ----
    unit_fam_corner(TF(F.x0+0, F.y0+16300, 8600, 6500), wide=True)      # 55.9
    unit_fam48(TF(F.x0+8600, F.y0+17800, 9600, 5000))                   # 48#1
    unit_fam48(TF(F.x0+21900, F.y0+17800, 9600, 5000, mx=True))         # 48#2
    lounge(F, 18300, 21800, west_vend=False)
    F.text("패밀리룸", (4500, 20950), 380); F.text("55.9m² /16.91PY", (4500, 20450), 260)
    F.text("패밀리룸", (12050, 20150), 380); F.text("48.0m² /14.52PY", (12050, 19650), 260)
    F.text("패밀리룸", (28050, 20150), 380); F.text("48.0m² /14.52PY", (28050, 19650), 260)

def lounge(F, x1, x2, west_vend=True):
    """휴게공간 (자판기)"""
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
    F.text("휴게공간", (cx, 21000-350), 300)
    F.text("(자판기)", (cx, 20250), 240, color=8)

def floor_34f(F):
    south_wing(F); connector_core(F)
    # ---- 북측동 외벽 (밴드B 구간만 y22600~22800 벽) ----
    F.wall(7000, 22600, 8200, 22800); F.wall(12800, 22600, 14300, 22800)
    F.wall(17200, 22600, 18700, 22800); F.wall(23300, 22600, 24500, 22800)
    F.window(8200, 12800, 22600, 22800)                # DLX2 창
    F.window(14300, 17200, 22600, 22800)               # 휴게공간 창
    F.window(18700, 23300, 22600, 22800)               # DLX3 창
    # 발코니 (밴드A 상부): 난간
    for xa, xb in [(0, 7000), (24500, 31500)]:
        F.line("0WIN", (xa, 22650), (xb, 22650)); F.line("0WIN", (xa, 22780), (xb, 22780))
        F.text("발코니", ((xa+xb)/2, 22150), 280, color=8)
    F.line("0WIN", (50, 21300), (50, 22780)); F.line("0WIN", (31450, 21300), (31450, 22780))
    # 밴드A 객실 북측벽 (발코니창 포함)
    F.wall(0, 21100, 1200, 21300); F.wall(5800, 21100, 7000, 21300)
    F.window(1200, 5800, 21100, 21300)
    F.wall(24500, 21100, 25700, 21300); F.wall(30300, 21100, 31500, 21300)
    F.window(25700, 30300, 21100, 21300)
    F.wall(0, 16300, 200, 21100)                       # 서측 외벽
    F.wall(31300, 16300, 31500, 21100)                 # 동측 외벽
    F.wall(200, 16300, 7000, 16500)                    # DLX1 남측 외벽
    F.wall(7000, 16300, 7400, 16500); F.wall(17000, 16300, 17400, 16500)
    F.window(7400, 17000, 16300, 16500)                # 복도 창
    F.wall(24500, 16300, 31300, 16500)                 # DLX4 남측벽
    # ---- 내벽 ----
    F.wall(6900, 16500, 7100, 16600); F.wall(6900, 17400, 7100, 22600)    # DLX1 동측벽+문
    F.wall(24400, 16500, 24600, 16600); F.wall(24400, 17400, 24600, 22600) # DLX4 서측벽+문
    F.wall(7100, 17700, 12700, 17900)                  # 복도벽: DLX2 문 12700~13600
    F.wall(13600, 17700, 14000, 17900)
    F.wall(17500, 17700, 17900, 17900)                 # DLX3 문 17900~18800
    F.wall(18800, 17700, 24400, 17900)
    F.wall(13900, 17900, 14100, 22600)                 # DLX2/휴게
    F.wall(17400, 17900, 17600, 22600)                 # 휴게/DLX3
    F.text("복도", (12000, 17100), 280, color=8)
    # ---- 유닛 ----
    unit_dlx_a(TF(F.x0+0, F.y0+16300, 7000, 5000))                       # DLX1
    unit_dlx_a(TF(F.x0+24500, F.y0+16300, 7000, 5000, mx=True))          # DLX4
    unit_dlx_b(TF(F.x0+7000, F.y0+17800, 7000, 5000))                    # DLX2
    unit_dlx_b(TF(F.x0+17500, F.y0+17800, 7000, 5000, mx=True))          # DLX3
    lounge(F, 14100, 17400, west_vend=True)
    for cx, cy in [(4600, 19500), (26900, 19500)]:
        F.text("디럭스룸", (cx, cy+250), 380); F.text("35.0m² /10.59PY", (cx, cy-250), 260)
    for cx, cy in [(12050, 20850), (19450, 20850)]:
        F.text("디럭스룸", (cx, cy+250), 380); F.text("35.0m² /10.59PY", (cx, cy-250), 260)

# ---------------- 치수/타이틀 ----------------
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
GAP = 41000
FLOORS = [
    ("2F", 0, floor_2f, [0, 8600, 18200, 21900, 31500],
     "패밀리룸 6실 (45.0~55.9m²) + 리넨실 · 휴게공간"),
    ("3F", GAP, floor_34f, [0, 7000, 14000, 17500, 24500, 31500],
     "디럭스룸 4실 (35.0m²) + 패밀리룸 3실 + 리넨실 · 휴게공간 · 발코니"),
    ("4F", GAP*2, floor_34f, [0, 7000, 14000, 17500, 24500, 31500],
     "디럭스룸 4실 (35.0m²) + 패밀리룸 3실 + 리넨실 · 휴게공간 · 발코니"),
]
for name, xoff, fn, chain, subtitle in FLOORS:
    F = TF(xoff, 0, 33000, 22800)
    fn(F)
    dims_common(F, chain)
    F.text(f"{name} 평면도", (16500, -4200), 900)
    F.text(subtitle, (16500, -5400), 380, color=8)
    F.text("진입마당 방향", (16500, -2900), 280, color=8)

# 시트 타이틀/주기
t = msp.add_text("호텔 가은 — 2·3·4층 객실 평면도 (층별 출입구 위치 반영)",
                 dxfattribs={"layer":"0TEXT-1","style":"KOR","height":1400})
t.set_placement((GAP+16500, 27500), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
notes = [
    "1. 벽체: 외벽·세대간벽 200THK, 욕실 칸막이벽 100THK / 치수단위 mm",
    "2. 남측동(2~4F 공통): 패밀리룸 45.5 코너 측벽 출입(복도 단부), 패밀리룸 45.0 복도 중앙 출입, 리넨실 복도 서단 출입",
    "3. 북측동 2F: 패밀리룸 55.9 동측벽 출입 / 패밀리룸 48.0 2실은 중앙 휴게공간 양측에서 출입",
    "4. 북측동 3·4F: 디럭스룸 4실 엇갈림 배치 — 외측 2실 측벽 출입 + 북측 발코니, 내측 2실 휴게공간 양측 출입",
    "5. 출입구 위치는 계획도면(0718)의 A-Wall Brk 표기 기준, 3·4F 디럭스 내측 2실은 2F 패턴 준용",
    "6. 코어: 승용승강기 2대(12인승 장애인겸용) + 피난계단 / 홀에서 남·북 복도 연결",
]
for i, n in enumerate(notes):
    t = msp.add_text(n, dxfattribs={"layer":"0TEXT-1","style":"KOR","height":420,"color":8})
    t.set_placement((0, -8200 - i*750), align=ezdxf.enums.TextEntityAlignment.LEFT)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hotel-gaun-floorplans-2f-4f.dxf")
doc.saveas(out)
print("saved:", out)

# ---- PNG ----
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy

fig = plt.figure(figsize=(30, 10), dpi=120)
ax = fig.add_axes([0, 0, 1, 1])
Frontend(RenderContext(doc), MatplotlibBackend(ax),
         config=Configuration(background_policy=BackgroundPolicy.WHITE)).draw_layout(msp, finalize=True)
png = out.replace(".dxf", ".png")
fig.savefig(png, dpi=120, facecolor="white")
print("saved:", png)
