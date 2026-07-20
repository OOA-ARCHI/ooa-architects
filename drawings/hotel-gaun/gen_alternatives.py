# -*- coding: utf-8 -*-
"""호텔 가은 — 객실 단위평면 디자인 제안 (디럭스 3안 / 패밀리 3안)

사례 참고:
- 사례1: 사선 벽 전실 버퍼 / 다이아몬드 가구 → DLX-C
- 사례2: 스파인월(자유벽) 양면 활용 + 조망향 침대 → DLX-A, FAM-B
- 사례3: 세면 오픈 + 변기/샤워 분리형 욕실, 트윈 변형 → DLX-B, FAM-A
- 사례4: 통로 치수 기준(침대옆 0.8m, 통로 0.9m, 풋존 1.15~1.2m) → 전 유닛 검증치수
블록 치수: 디럭스 7.0×5.0m(35.0m²), 패밀리 7.0×6.5m(45.5m²) — 층평면에 즉시 적용 가능
단위: mm / 복도=하부, 창=상부
"""
import ezdxf
from ezdxf import units
import math, os

doc = ezdxf.new("R2010", setup=True)
doc.units = units.MM
doc.header["$INSUNITS"] = 4
doc.styles.add("KOR", font="Pretendard-Regular.ttf")

LAYERS = [("0CONC",7),("해치벽체",8),("0WIN",4),("DOOR",2),("FUR",3),("TOIL",5),
          ("0TEXT-1",7),("S-DIM",1),("0CEN",9)]
for n,c in LAYERS: doc.layers.add(n, color=c)
doc.layers.get("0CEN").dxf.linetype = "DASHDOT"
msp = doc.modelspace()

ds = doc.dimstyles.add("D100")
for k,v in dict(dimtxt=250, dimasz=180, dimexe=120, dimexo=150, dimgap=80,
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
        h.set_pattern_fill("ANSI31", scale=15.0, color=8)
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
    def sliding(self, x1, x2, y):
        """미서기문(슬라이딩) 평면 기호 — 수직벽 개구부용 (y1~y2, x)"""
        pass
    def sliding_v(self, x, y1, y2):
        ym = (y1+y2)/2
        self.rect("DOOR", x-60, y1, x+20, ym+60)
        self.rect("DOOR", x-20, ym-60, x+60, y2)
        self.line("DOOR", (x+140, y1), (x+140, ym)); self.line("DOOR", (x-140, ym), (x-140, y2))
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
    if head == "bottom":
        py1, py2 = y1+120, y1+520
    else:
        py1, py2 = y2-520, y2-120
    if w >= 1500:
        pw = (w-3*160)/2
        tf.rect("FUR", x1+160, py1, x1+160+pw, py2)
        tf.rect("FUR", x2-160-pw, py1, x2-160, py2)
    else:
        tf.rect("FUR", x1+180, py1, x2-180, py2)
    fy = y1+(y2-y1)*0.62 if head=="bottom" else y2-(y2-y1)*0.62
    tf.line("FUR", (x1,fy), (x2,fy)); tf.line("FUR", (x1,fy+120), (x2,fy+120))

def bed_h(tf, x1, y1, x2, y2, head="right"):
    tf.rect("FUR", x1, y1, x2, y2)
    h = y2-y1
    if head == "right": px1, px2 = x2-520, x2-120
    else: px1, px2 = x1+120, x1+520
    if h >= 1500:
        ph = (h-3*160)/2
        tf.rect("FUR", px1, y1+160, px2, y1+160+ph)
        tf.rect("FUR", px1, y2-160-ph, px2, y2-160)
    else:
        tf.rect("FUR", px1, y1+180, px2, y2-180)
    fx = x2-(x2-x1)*0.62 if head=="right" else x1+(x2-x1)*0.62
    tf.line("FUR", (fx,y1), (fx,y2)); tf.line("FUR", (fx+120,y1), (fx+120,y2))

def nightstand(tf, x1, y1, x2, y2):
    tf.rect("FUR", x1, y1, x2, y2); tf.circle("FUR", ((x1+x2)/2,(y1+y2)/2), 100)

def toilet(tf, cx, ty1, ty2, rot=None):
    tf.rect("TOIL", cx-220, ty1, cx+220, ty2)
    tf.ellipse("TOIL", (cx, ty2+330), 230, 310)

def basin(tf, x1, y1, x2, y2, n=1):
    tf.rect("TOIL", x1, y1, x2, y2)
    cy = (y1+y2)/2
    if n == 1:
        cx = (x1+x2)/2
        tf.ellipse("TOIL", (cx,cy), 260, 185); tf.circle("TOIL", (cx, y1+90), 45)
    else:
        for cx in (x1+(x2-x1)*0.28, x1+(x2-x1)*0.72):
            tf.ellipse("TOIL", (cx,cy), 230, 170); tf.circle("TOIL", (cx, y1+90), 40)

def shower(tf, x1, y1, x2, y2):
    tf.rect("TOIL", x1, y1, x2, y2)
    tf.line("TOIL", (x1,y1), (x2,y2)); tf.line("TOIL", (x1,y2), (x2,y1))

def bathtub(tf, x1, y1, x2, y2):
    tf.rect("TOIL", x1, y1, x2, y2); tf.rect("TOIL", x1+80, y1+80, x2-80, y2-80)
    tf.circle("TOIL", (x1+250,(y1+y2)/2), 80)

def wardrobe(tf, x1, y1, x2, y2, split="v"):
    tf.rect("FUR", x1, y1, x2, y2); tf.line("FUR", (x1,y1), (x2,y2))
    if split=="v": tf.line("FUR", ((x1+x2)/2,y1), ((x1+x2)/2,y2))
    else: tf.line("FUR", (x1,(y1+y2)/2), (x2,(y1+y2)/2))

def diamond(tf, cx, cy, half):
    tf.poly("FUR", [(cx,cy-half),(cx+half,cy),(cx,cy+half),(cx-half,cy)])
    tf.circle("FUR", (cx,cy), half*0.35)

def shell(tf, door_x1, door_x2, win_x1, win_x2):
    """외곽 벽체 공통: 하부(문개구), 상부(창개구), 양측"""
    W, D = tf.W, tf.D
    tf.wall(0, 0, door_x1, 200); tf.wall(door_x2, 0, W, 200)
    tf.wall(0, D-200, win_x1, D); tf.wall(win_x2, D-200, W, D)
    tf.wall(0, 200, 200, D-200); tf.wall(W-200, 200, W, D-200)
    tf.window(win_x1, win_x2, D-200, D)
    tf.door((door_x2, 200), 90, 90, door_x2-door_x1)

# ================= 디럭스 3안 (7000x5000) =================

def dlx_A(tf):
    """A. 스파인월 타입 (사례2) — 조망향 침대 + 자유벽 뒷면 데스크"""
    shell(tf, 2700, 3600, 1200, 5800)
    # 욕실 (좌하단, 샤워형)
    tf.wall(2400, 200, 2500, 1300); tf.wall(2400, 2100, 2500, 2400)
    tf.wall(200, 2300, 2400, 2400)
    shower(tf, 200, 1400, 1100, 2300); toilet(tf, 700, 250, 470)
    basin(tf, 1500, 200, 2400, 750)
    tf.text("욕실", (1600, 1150), 190)
    tf.door((2400, 1300), 180, -90, 800)
    # 스파인월 (자유벽 200THK) + 침대(조망향)
    tf.wall(1700, 2600, 4500, 2800)
    bed_v(tf, 2200, 2800, 4000, 4800, head="bottom")
    nightstand(tf, 1700, 2850, 2150, 3300)
    nightstand(tf, 4050, 2850, 4500, 3300)
    # 스파인월 뒷면: 데스크 + TV
    tf.rect("FUR", 2600, 2200, 4500, 2600)
    tf.rect("FUR", 2900, 2500, 3900, 2580)          # TV(벽걸이)
    tf.rect("FUR", 3200, 1650, 3700, 2150)          # 체어
    # 옷장+미니바 (우하단)
    wardrobe(tf, 4200, 200, 6000, 850, split="v")
    tf.rect("FUR", 6100, 200, 6800, 850); tf.line("FUR", (6100,200),(6800,850))
    # 라운지 (좌측 회유부)
    tf.rect("FUR", 550, 3600, 1150, 4200); tf.rect("FUR", 620, 3670, 1080, 4130)
    tf.circle("FUR", (900, 4550), 280)
    # 데스크존 (우측 회유부)
    tf.rect("FUR", 6350, 2900, 6800, 4300)
    tf.rect("FUR", 5750, 3300, 6250, 3800)
    tf.text("회유동선", (900, 3350), 170, color=9)
    tf.text("회유동선", (5450, 4450), 170, color=9)

def dlx_B(tf):
    """B. 분리욕실 타입 (사례3) — 세면 오픈 + 변기/샤워 분리, 윈도우시트"""
    shell(tf, 2700, 3600, 1200, 5800)
    # 오픈 세면존 (더블베이슨, 사례4A)
    basin(tf, 200, 200, 2500, 750, n=2)
    tf.text("오픈 세면존", (1350, 1000), 180, color=9)
    # 변기실 / 샤워실 분리
    tf.wall(200, 1200, 1300, 1300)                   # WC 하부벽
    tf.wall(200, 2200, 1300, 2300)                   # WC/샤워 구획
    tf.wall(200, 3200, 1400, 3300)                   # 샤워 상부벽
    tf.wall(1300, 1200, 1400, 1450)                  # 수직벽(문개구 2개소)
    tf.wall(1300, 2050, 1400, 2400)
    tf.wall(1300, 3000, 1400, 3200)
    toilet(tf, 750, 1330, 1550)
    tf.door((1400, 1450), 0, 90, 600)                # 변기실문
    tf.text("WC", (1050, 2050), 150)
    shower(tf, 250, 2400, 1250, 3150)
    tf.door((1400, 2400), 0, 90, 600)                # 샤워실문
    tf.text("샤워", (750, 2750), 160)
    # 킹베드 (창과 평행, 머리=우측벽)
    tf.rect("FUR", 6700, 2300, 6800, 4200)
    bed_h(tf, 4800, 2350, 6800, 4150, head="right")
    nightstand(tf, 6250, 1750, 6750, 2250)
    # 윈도우시트 (창측 데이베드)
    tf.rect("FUR", 1500, 4350, 4300, 4800)
    tf.line("FUR", (1500, 4500), (4300, 4500))
    tf.text("윈도우시트", (2900, 4050), 180, color=9)
    tf.circle("FUR", (2500, 3500), 300)              # 티테이블
    # TV장 (좌측벽 상부, 화면=동측)
    tf.rect("FUR", 200, 3450, 650, 4250)
    tf.rect("FUR", 560, 3550, 630, 4150)
    # 옷장 (우하단)
    wardrobe(tf, 4200, 200, 6000, 850, split="v")
    tf.rect("FUR", 6100, 200, 6800, 850); tf.line("FUR", (6100,200),(6800,850))

def dlx_C(tf):
    """C. 사선 전실 타입 (사례1) — 사선 워크인 + 다이아몬드 라운지"""
    shell(tf, 2700, 3600, 1200, 5800)
    # 욕실 (좌하단)
    tf.wall(2400, 200, 2500, 1300); tf.wall(2400, 2100, 2500, 2400)
    tf.wall(200, 2300, 2400, 2400)
    shower(tf, 200, 1400, 1100, 2300); toilet(tf, 700, 250, 470)
    basin(tf, 1500, 200, 2400, 750)
    tf.text("욕실", (1600, 1150), 190)
    tf.door((2400, 1300), 180, -90, 800)
    # 사선 워크인클로젯 (우하단 쐐기, 사례1)
    tf.wallpoly([(4300, 200), (6300, 1560), (6420, 1640), (4470, 320)])
    tf.line("FUR", (4700, 350), (6250, 1400))        # 행거레일(사선)
    tf.line("FUR", (5100, 200), (5100, 750))
    tf.line("FUR", (6000, 200), (6000, 1360))
    tf.text("워크인", (5950, 700), 180)
    # 킹베드 (머리=욕실벽)
    tf.rect("FUR", 950, 2400, 2850, 2500)
    bed_v(tf, 1000, 2500, 2800, 4500, head="bottom")
    nightstand(tf, 400, 2500, 900, 3000)
    nightstand(tf, 2900, 2500, 3400, 3000)
    # TV장 (우측벽, 워크인 위)
    tf.rect("FUR", 6350, 2400, 6800, 3800)
    tf.rect("FUR", 6380, 2650, 6450, 3550)
    # 다이아몬드 라운지 (창측, 사례1)
    diamond(tf, 4400, 4100, 500)
    tf.rect("FUR", 5150, 4150, 5750, 4750); tf.rect("FUR", 5220, 4220, 5680, 4680)
    tf.rect("FUR", 3350, 4300, 3800, 4750)
    tf.text("라운지", (4400, 3350), 180, color=9)

# ================= 패밀리 3안 (7000x6500) =================

def fam_A(tf):
    """A. 알코브 분리 타입 (사례3·4B) — 슬라이딩 파티션 자녀존"""
    shell(tf, 2900, 3800, 1200, 5800)
    # 욕실 (좌하단, 욕조형)
    tf.wall(2600, 200, 2700, 1350); tf.wall(2600, 2150, 2700, 2500)
    tf.wall(200, 2400, 2600, 2500)
    bathtub(tf, 200, 1650, 1700, 2400); toilet(tf, 550, 250, 470)
    basin(tf, 1500, 200, 2600, 750)
    tf.text("욕실", (1150, 1150), 190)
    tf.door((2600, 2150), 180, 90, 800)
    # 미니주방 (우하단)
    tf.rect("FUR", 4300, 200, 6100, 800)
    tf.rect("TOIL", 4450, 380, 4950, 680); tf.circle("TOIL", (4700, 300), 45)
    tf.circle("FUR", (5400, 500), 150); tf.circle("FUR", (5750, 500), 150)
    tf.rect("FUR", 6200, 200, 6800, 750); tf.line("FUR", (6200,200),(6800,750))
    tf.text("미니주방", (5200, 980), 170)
    # 슬라이딩 파티션 (자녀 알코브 구획, 침대 사이 개구)
    tf.wall(4600, 2600, 4700, 3700)
    tf.sliding_v(4650, 3700, 4600)
    tf.wall(4600, 4600, 4700, 6300)
    tf.text("슬라이딩도어", (4100, 4150), 160, color=9)
    # 자녀존: 싱글 2 (머리=우측벽, 간격 900 >= 사례4B 0.72m)
    bed_h(tf, 4800, 2600, 6800, 3700, head="right")
    bed_h(tf, 4800, 4600, 6800, 5700, head="right")
    tf.rect("FUR", 6300, 3900, 6800, 4400)
    tf.dim((5600,3700), (5600,4600), (5600,0), 90)   # 트윈 간격 900
    # 부모존: 더블베드 (머리=욕실벽)
    tf.rect("FUR", 650, 2500, 2550, 2600)
    bed_v(tf, 700, 2600, 2500, 4600, head="bottom")
    nightstand(tf, 2600, 2600, 3100, 3100)
    # TV장 (좌측벽 상부) + 좌식테이블
    tf.rect("FUR", 200, 4800, 650, 6100); tf.rect("FUR", 560, 5000, 630, 5900)
    tf.circle("FUR", (2900, 5700), 350)
    tf.rect("FUR", 2200, 5500, 2600, 5900); tf.rect("FUR", 3200, 5500, 3600, 5900)
    # 통로 검증 (사례4)
    tf.text("부모존", (1600, 4900), 200, color=9)
    tf.text("자녀존", (5800, 6000), 200, color=9)

def fam_B(tf):
    """B. 스파인월 타입 (사례2) — 자유벽 양면: 더블(창측)/트윈(입구측)"""
    shell(tf, 2900, 3800, 1200, 5800)
    # 욕실 (좌하단, 욕조형)
    tf.wall(2600, 200, 2700, 1350); tf.wall(2600, 2150, 2700, 2500)
    tf.wall(200, 2400, 2600, 2500)
    bathtub(tf, 200, 1650, 1700, 2400); toilet(tf, 550, 250, 470)
    basin(tf, 1500, 200, 2600, 750)
    tf.text("욕실", (1150, 1150), 190)
    tf.door((2600, 2150), 180, 90, 800)
    # 미니주방 (우하단)
    tf.rect("FUR", 4300, 200, 6100, 800)
    tf.rect("TOIL", 4450, 380, 4950, 680); tf.circle("TOIL", (4700, 300), 45)
    tf.circle("FUR", (5400, 500), 150); tf.circle("FUR", (5750, 500), 150)
    tf.rect("FUR", 6200, 200, 6800, 750); tf.line("FUR", (6200,200),(6800,750))
    tf.text("미니주방", (5200, 980), 170)
    # 스파인월 (자유벽, 양면 수납)
    tf.wall(1700, 3600, 5300, 3800)
    tf.rect("FUR", 2900, 3400, 5300, 3600)           # 남면 오픈수납(자녀존 헤드)
    # 입구측: 트윈 싱글 (머리=스파인월, 간격 800 = 사례4B)
    bed_v(tf, 2700, 1600, 3800, 3400, head="top")
    bed_v(tf, 4600, 1600, 5700, 3400, head="top")
    tf.dim((3800,2500), (4600,2500), (0,2500), 0)    # 트윈 간격 800
    # 창측: 더블베드 (머리=스파인월 북면)
    bed_v(tf, 2600, 3800, 4400, 5800, head="bottom")
    nightstand(tf, 2000, 3850, 2500, 4350)
    nightstand(tf, 4500, 3850, 5000, 4350)
    # 옷장 (좌측벽) + TV(좌측벽 상부) + 라운지
    wardrobe(tf, 200, 2700, 850, 4500, split="h")
    tf.rect("FUR", 200, 4700, 650, 6000); tf.rect("FUR", 560, 4900, 630, 5800)
    tf.circle("FUR", (1300, 5800), 300)
    tf.rect("FUR", 5600, 5300, 6300, 6000); tf.rect("FUR", 5670, 5370, 6230, 5930)
    tf.text("자녀존", (4200, 1100), 200, color=9)
    tf.text("부모존", (5600, 4700), 200, color=9)

def fam_C(tf):
    """C. 좌식 툇마루 타입 (사례1·2 데크 개념의 실내화) — 창측 평상 + 2단침대"""
    shell(tf, 2900, 3800, 1200, 5800)
    # 욕실 (좌하단, 욕조형)
    tf.wall(2600, 200, 2700, 1350); tf.wall(2600, 2150, 2700, 2500)
    tf.wall(200, 2400, 2600, 2500)
    bathtub(tf, 200, 1650, 1700, 2400); toilet(tf, 550, 250, 470)
    basin(tf, 1500, 200, 2600, 750)
    tf.text("욕실", (1150, 1150), 190)
    tf.door((2600, 2150), 180, 90, 800)
    # 미니주방 (우하단)
    tf.rect("FUR", 4300, 200, 6100, 800)
    tf.rect("TOIL", 4450, 380, 4950, 680); tf.circle("TOIL", (4700, 300), 45)
    tf.circle("FUR", (5400, 500), 150); tf.circle("FUR", (5750, 500), 150)
    tf.rect("FUR", 6200, 200, 6800, 750); tf.line("FUR", (6200,200),(6800,750))
    tf.text("미니주방", (5200, 980), 170)
    # 창측 전폭 평상(툇마루, 단차 +300)
    tf.rect("FUR", 200, 5300, 6800, 6300)
    tf.line("FUR", (200, 5400), (6800, 5400))
    tf.circle("FUR", (3500, 5850), 380)
    for sx in (2500, 4100):
        tf.rect("FUR", sx, 5650, sx+400, 6050)
    tf.text("평상(좌식존) +300", (1500, 5850), 200, color=9)
    # 더블베드 (머리=좌측벽)
    bed_h(tf, 300, 3250, 2300, 5050, head="left")
    nightstand(tf, 2400, 3250, 2900, 3750)
    # 2단침대 (자녀 2인)
    tf.rect("FUR", 5600, 2900, 6800, 4900)
    tf.line("FUR", (5600, 2900), (6800, 4900)); tf.line("FUR", (5600, 4900), (6800, 2900))
    tf.rect("FUR", 5680, 4380, 6720, 4820)
    tf.text("2단침대", (6200, 2650), 190)
    # 소파 + TV (중앙)
    tf.rect("FUR", 3800, 1400, 5000, 2100); tf.rect("FUR", 3870, 1470, 4930, 2030)
    tf.rect("FUR", 6350, 1100, 6800, 2500); tf.rect("FUR", 6380, 1350, 6450, 2250)
    # 옷장 (욕실 상부벽, 북향)
    wardrobe(tf, 200, 2550, 1900, 3150, split="v")
    tf.text("가족 좌식존", (3800, 4900), 200, color=9)

# ================= 배치/치수/타이틀 =================
def annotate(tf, title, sub, tags):
    W, D = tf.W, tf.D
    tf.dim((0,0), (W,0), (0,-700), 0)
    tf.dim((0,0), (0,D), (-700,0), 90)
    tf.text(title, (W/2, -1900), 420)
    tf.text(sub, (W/2, -2550), 260, color=8)
    tf.text(tags, (W/2, -3150), 230, color=9)

UNITS = [
    (dlx_A, 0,      0, 7000, 5000, "디럭스 A — 스파인월", "35.0m² /10.59PY · 킹베드(조망향) + 회유동선", "참고: 사례2 (자유벽 뒷면 데스크·TV)"),
    (dlx_B, 11000,  0, 7000, 5000, "디럭스 B — 분리욕실", "35.0m² /10.59PY · 세면오픈 + WC/샤워 분리 + 윈도우시트", "참고: 사례3·4A (더블베이슨)"),
    (dlx_C, 22000,  0, 7000, 5000, "디럭스 C — 사선 전실", "35.0m² /10.59PY · 사선 워크인클로젯 + 다이아몬드 라운지", "참고: 사례1 (사선 버퍼)"),
    (fam_A, 0,     -13000, 7000, 6500, "패밀리 A — 알코브 분리", "45.5m² /13.76PY · 슬라이딩 파티션 부모/자녀존", "참고: 사례3·4B (트윈 간격 0.8m)"),
    (fam_B, 11000, -13000, 7000, 6500, "패밀리 B — 스파인월", "45.5m² /13.76PY · 자유벽 양면 더블+트윈 4인", "참고: 사례2·4B"),
    (fam_C, 22000, -13000, 7000, 6500, "패밀리 C — 좌식 툇마루", "45.5m² /13.76PY · 창측 평상 좌식존 + 2단침대", "참고: 사례1·2 (데크의 실내화)"),
]
for fn, x0, y0, W, D, title, sub, tags in UNITS:
    tf = TF(x0, y0, W, D)
    fn(tf)
    annotate(tf, title, sub, tags)

# 복도 표기
for y in (-4400, -17400):
    msp.add_line((-1000, y), (30000, y), dxfattribs={"layer": "0CEN"})
t = msp.add_text("복도 (CORRIDOR)", dxfattribs={"layer":"0TEXT-1","style":"KOR","height":300,"color":8})
t.set_placement((14500, -4150), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

# 시트 타이틀
t = msp.add_text("호텔 가은 — 객실 단위평면 디자인 제안 (디럭스 3안 · 패밀리 3안)",
                 dxfattribs={"layer":"0TEXT-1","style":"KOR","height":900})
t.set_placement((14500, 7600), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
t = msp.add_text("사례1 사선버퍼 · 사례2 스파인월 · 사례3 분리욕실 · 사례4 통로치수 기준 반영 / 블록치수 유지(층평면 호환)",
                 dxfattribs={"layer":"0TEXT-1","style":"KOR","height":360,"color":8})
t.set_placement((14500, 6700), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
notes = [
    "1. 전 유닛 호텔가은 객실 블록치수 유지: 디럭스 7.0×5.0m(35.0m²), 패밀리 7.0×6.5m(45.5m²) — 2~4F 층평면에 그대로 적용 가능",
    "2. 통로 치수 기준(사례4): 침대 양측 800 이상, 주통로 900 이상, 침대 풋존 1150~1200 확보",
    "3. 디럭스 A/패밀리 B 스파인월: 구조벽 아님(경량벽) — 객실 리뉴얼 시 가변 가능",
    "4. 패밀리 A 슬라이딩 파티션: 개방 시 원룸형, 폐쇄 시 투룸형 운영",
    "5. 패밀리 C 평상: 단차 +300, 온돌패널 적용 시 좌식 숙박 수요 대응",
]
for i, n in enumerate(notes):
    t = msp.add_text(n, dxfattribs={"layer":"0TEXT-1","style":"KOR","height":330,"color":8})
    t.set_placement((-500, -19000 - i*650), align=ezdxf.enums.TextEntityAlignment.LEFT)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hotel-gaun-unit-alternatives.dxf")
doc.saveas(out)
print("saved:", out)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy

fig = plt.figure(figsize=(24, 20), dpi=110)
ax = fig.add_axes([0, 0, 1, 1])
Frontend(RenderContext(doc), MatplotlibBackend(ax),
         config=Configuration(background_policy=BackgroundPolicy.WHITE)).draw_layout(msp, finalize=True)
png = out.replace(".dxf", ".png")
fig.savefig(png, dpi=110, facecolor="white")
print("saved:", png)
