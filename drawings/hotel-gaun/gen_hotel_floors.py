# -*- coding: utf-8 -*-
"""호텔 가은 — 2·3·4층 기준층 평면도 (객실 유닛 반영판)

기준: 26.07.27 개략평면(D안)의 실 경계·코어·복도·리넨실 위치를 그대로 사용, 내부 가구만 배치.
- 로컬좌표 X=0(건물 서측단) / Y=0(남측테일 남단), 북측바 Y7500~16500, 복도 Y7500~9000
- 2·3F 단층형 / 4F 패밀리=복층(계단+상부해치), 디럭스=로프트 2층침대(사다리+상부해치)
- 배치원칙: ①출입문 스윙+진입통로 무가구 ②침대는 진입·주방·계단에서 가장 먼 정적존
단위: mm
"""
import ezdxf, math, os
from ezdxf import units
from ezdxf.enums import TextEntityAlignment as TA

doc = ezdxf.new("R2010", setup=True)
doc.units = units.MM; doc.header["$INSUNITS"] = 4
doc.styles.add("KOR", font="Pretendard-Regular.ttf")
for n,c in [("0CONC",7),("해치벽체",8),("0WIN",4),("DOOR",2),("FUR",3),("TOIL",5),
            ("0TEXT",7),("0CEN",9),("0OTB",9),("STAIR",2)]:
    doc.layers.add(n, color=c)
doc.layers.get("0CEN").dxf.linetype = "DASHDOT"
msp = doc.modelspace()

OFF = [0.0, 0.0]
def W_(x,y): return (x+OFF[0], y+OFF[1])
def rect(l,x1,y1,x2,y2): msp.add_lwpolyline([W_(x1,y1),W_(x2,y1),W_(x2,y2),W_(x1,y2)],close=True,dxfattribs={"layer":l})
def line(l,p1,p2): msp.add_line(W_(*p1),W_(*p2),dxfattribs={"layer":l})
def circ(l,c,r): msp.add_circle(W_(*c),r,dxfattribs={"layer":l})
def ell(l,c,rx,ry):
    cc=W_(*c)
    if rx>=ry: msp.add_ellipse(cc,major_axis=(rx,0),ratio=ry/rx,dxfattribs={"layer":l})
    else:      msp.add_ellipse(cc,major_axis=(0,ry),ratio=rx/ry,dxfattribs={"layer":l})
def wall(x1,y1,x2,y2):
    rect("0CONC",x1,y1,x2,y2)
    h=msp.add_hatch(color=8,dxfattribs={"layer":"해치벽체"})
    h.paths.add_polyline_path([W_(x1,y1),W_(x2,y1),W_(x2,y2),W_(x1,y2)],is_closed=True)
    h.set_pattern_fill("ANSI31",scale=16.0,color=8)
def txt(s,pos,h,color=None,align=TA.MIDDLE_CENTER):
    at={"layer":"0TEXT","style":"KOR","height":h}
    if color is not None: at["color"]=color
    t=msp.add_text(s,dxfattribs=at); t.set_placement(W_(*pos),align=align)
def otb(x1,y1,x2,y2):
    rect("0OTB",x1,y1,x2,y2); step=700
    n=int((x2-x1+y2-y1)/step)
    for i in range(1,n):
        o=i*step; ax,ay,bx,by=x1+o,y1,x1,y1+o
        if ax>x2: ay+=(ax-x2); ax=x2
        if by>y2: bx+=(by-y2); by=y2
        if ax>=x1 and by<=y2: line("0OTB",(min(ax,x2),ay),(bx,min(by,y2)))
def winline(x1,y1,x2,y2,horiz=True):
    if horiz:
        for t in (0,1/3,2/3,1): line("0WIN",(x1,y1+(y2-y1)*t),(x2,y1+(y2-y1)*t))
        line("0WIN",(x1,y1),(x1,y2)); line("0WIN",(x2,y1),(x2,y2))
    else:
        for t in (0,1/3,2/3,1): line("0WIN",(x1+(x2-x1)*t,y1),(x1+(x2-x1)*t,y2))
        line("0WIN",(x1,y1),(x2,y1)); line("0WIN",(x1,y2),(x2,y2))

# ---------------- 유닛 프레임 (문=v0, 창=vD) ----------------
class F:
    def __init__(s,X1,Y1,X2,Y2,rot=0):
        s.X1,s.Y1,s.X2,s.Y2,s.rot=X1,Y1,X2,Y2,rot
        s.W,s.D = (X2-X1,Y2-Y1) if rot in (0,180) else (Y2-Y1,X2-X1)
    def p(s,u,v):
        if   s.rot==0:   return (s.X1+u, s.Y1+v)
        elif s.rot==180: return (s.X2-u, s.Y2-v)
        elif s.rot==90:  return (s.X2-v, s.Y1+u)
        else:            return (s.X1+v, s.Y2-u)
    def ang(s,a): return (a+s.rot)%360
    def rect(s,l,u1,v1,u2,v2):
        a,b=s.p(u1,v1),s.p(u2,v2)
        rect(l,min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1]))
    def wall(s,u1,v1,u2,v2):
        a,b=s.p(u1,v1),s.p(u2,v2)
        wall(min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1]))
    def otb(s,u1,v1,u2,v2):
        a,b=s.p(u1,v1),s.p(u2,v2)
        otb(min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1]))
    def line(s,l,p1,p2): line(l,s.p(*p1),s.p(*p2))
    def circ(s,l,c,r): circ(l,s.p(*c),r)
    def ell(s,l,c,rx,ry):
        if s.rot in (0,180): ell(l,s.p(*c),rx,ry)
        else: ell(l,s.p(*c),ry,rx)
    def txt(s,t,pos,h,color=None): txt(t,s.p(*pos),h,color)
    def label(s,name,area,u,v,h=225,ha=185):
        """실명/면적 라벨 — 회전유닛에서도 글자가 u축을 따라 흐르고 이름이 항상 면적 위."""
        x,y=s.p(u,v)
        if s.rot in (0,180): r,dn,da = 0,(0,195),(0,-195)
        else:                r,dn,da = 90,(-195,0),(195,0)
        for s_,hh,cc,d in ((name,h,None,dn),(area,ha,9,da)):
            at={"layer":"0TEXT","style":"KOR","height":hh,"rotation":r}
            if cc is not None: at["color"]=cc
            t=msp.add_text(s_,dxfattribs=at)
            t.set_placement(W_(x+d[0],y+d[1]),align=TA.MIDDLE_CENTER)
    def win(s,u1,u2,v1,v2):
        a,b=s.p(u1,v1),s.p(u2,v2)
        x1,x2=min(a[0],b[0]),max(a[0],b[0]); y1,y2=min(a[1],b[1]),max(a[1],b[1])
        winline(x1,y1,x2,y2, horiz=(s.rot in (0,180)))
    def door(s,u,v,width,side,sweep=+1,into=+1):
        """side: 캐노니컬 벽면 S/N/E/W · u,v=힌지 · sweep:개구부 방향 · into:열리는 쪽"""
        hx,hy=s.p(u,v)
        closed={"S":0,"N":0,"E":90,"W":90}[side]
        if sweep<0: closed=(closed+180)%360
        openA={"S":90,"N":270,"E":180,"W":0}[side]
        if into<0: openA=(openA+180)%360
        d=(openA-closed)%360
        a1=closed
        if d>180: a1=openA; d=360-d
        A0=math.radians(s.ang(openA))
        msp.add_line(W_(hx,hy), W_(hx+width*math.cos(A0), hy+width*math.sin(A0)),
                     dxfattribs={"layer":"DOOR"})
        st=s.ang(a1)
        msp.add_arc(W_(hx,hy),width,st,st+d,dxfattribs={"layer":"DOOR"})

# ---------------- 가구 ----------------
def bed(Fr,u1,v1,u2,v2,head):
    Fr.rect("FUR",u1,v1,u2,v2); du,dv=u2-u1,v2-v1
    if head in ("W","E"):
        px1,px2=(u1+110,u1+470) if head=="W" else (u2-470,u2-110)
        if dv>=1500:
            ph=(dv-3*130)/2
            Fr.rect("FUR",px1,v1+130,px2,v1+130+ph); Fr.rect("FUR",px1,v2-130-ph,px2,v2-130)
        else: Fr.rect("FUR",px1,v1+150,px2,v2-150)
        fu=u1+du*0.62 if head=="W" else u2-du*0.62
        Fr.line("FUR",(fu,v1),(fu,v2))
    else:
        py1,py2=(v1+110,v1+470) if head=="S" else (v2-470,v2-110)
        if du>=1500:
            pw=(du-3*130)/2
            Fr.rect("FUR",u1+130,py1,u1+130+pw,py2); Fr.rect("FUR",u2-130-pw,py1,u2-130,py2)
        else: Fr.rect("FUR",u1+150,py1,u2-150,py2)
        fv=v1+dv*0.62 if head=="S" else v2-dv*0.62
        Fr.line("FUR",(u1,fv),(u2,fv))
def nstand(Fr,u1,v1,u2,v2): Fr.rect("FUR",u1,v1,u2,v2); Fr.circ("FUR",((u1+u2)/2,(v1+v2)/2),95)
def wardrobe(Fr,u1,v1,u2,v2,sp="h"):
    Fr.rect("FUR",u1,v1,u2,v2); Fr.line("FUR",(u1,v1),(u2,v2))
    if sp=="v": Fr.line("FUR",((u1+u2)/2,v1),((u1+u2)/2,v2))
    else: Fr.line("FUR",(u1,(v1+v2)/2),(u2,(v1+v2)/2))
def sofa(Fr,u1,v1,u2,v2,back="S"):
    Fr.rect("FUR",u1,v1,u2,v2); t=150
    if back=="S": Fr.rect("FUR",u1,v1,u2,v1+t)
    elif back=="N": Fr.rect("FUR",u1,v2-t,u2,v2)
    elif back=="W": Fr.rect("FUR",u1,v1,u1+t,v2)
    else: Fr.rect("FUR",u2-t,v1,u2,v2)
def tvunit(Fr,u1,v1,u2,v2,face):
    Fr.rect("FUR",u1,v1,u2,v2)
    if face=="E": Fr.rect("FUR",u2-110,v1+180,u2-40,v2-180)
    elif face=="W": Fr.rect("FUR",u1+40,v1+180,u1+110,v2-180)
    elif face=="N": Fr.rect("FUR",u1+180,v2-110,u2-180,v2-40)
    else: Fr.rect("FUR",u1+180,v1+40,u2-180,v1+110)
def toilet(Fr,cu,v1,v2): Fr.rect("TOIL",cu-200,v1,cu+200,v2); Fr.ell("TOIL",(cu,v2+300),205,270)
def basin(Fr,u1,v1,u2,v2):
    Fr.rect("TOIL",u1,v1,u2,v2); cu,cv=(u1+u2)/2,(v1+v2)/2
    Fr.ell("TOIL",(cu,cv),230,165); Fr.circ("TOIL",(cu,v1+75),38)
def shower(Fr,u1,v1,u2,v2):
    Fr.rect("TOIL",u1,v1,u2,v2); Fr.line("TOIL",(u1,v1),(u2,v2)); Fr.line("TOIL",(u1,v2),(u2,v1))
def tub(Fr,u1,v1,u2,v2):
    Fr.rect("TOIL",u1,v1,u2,v2); Fr.rect("TOIL",u1+70,v1+70,u2-70,v2-70)
    Fr.circ("TOIL",(u1+230,(v1+v2)/2),70)
def kitchen(Fr,u1,v1,u2,v2):
    Fr.rect("FUR",u1,v1,u2,v2); du=u2-u1
    Fr.rect("TOIL",u1+110,v1+110,u1+590,v2-110)
    Fr.circ("FUR",(u2-du*0.30,(v1+v2)/2),130); Fr.circ("FUR",(u2-du*0.55,(v1+v2)/2),130)
def stair10(Fr,u1,v1,u2,v2):
    Fr.rect("STAIR",u1,v1,u2,v2)
    for i in range(1,10): Fr.line("STAIR",(u1,v1+(v2-v1)*i/10),(u2,v1+(v2-v1)*i/10))
    Fr.txt("UP",((u1+u2)/2,v1+320),210,color=9)
def ladder(Fr,u1,v1,u2,v2):
    Fr.rect("STAIR",u1,v1,u2,v2)
    n=max(4,int((v2-v1)/280))
    for i in range(1,n): Fr.line("STAIR",(u1,v1+(v2-v1)*i/n),(u2,v1+(v2-v1)*i/n))
    Fr.txt("사다리 UP",((u1+u2)/2,v1-330),165,color=9)

# ---------------- 유닛 템플릿 ----------------
def u_deluxe(Fr, name, area, loft=False):
    """디럭스 : 진입통로 u0~1500 / 욕실 우측 / 침대 우측 정적존"""
    Wd,D=Fr.W,Fr.D
    Fr.door(300,0,900,"S",sweep=+1,into=+1)
    # 욕실 (전폭, 진입통로 우측)
    Fr.wall(1500,0,1600,2400); Fr.wall(1600,2300,Wd,2400)
    Fr.door(1600,1550,800,"W",sweep=+1,into=+1)      # 욕실 안쪽으로 열림
    basin(Fr,1750,150,2900,800)
    toilet(Fr,3300,150,370)
    shower(Fr,Wd-1100,1200,Wd-120,2280)
    Fr.txt("욕실",(2300,1750),195)
    # 라벨 밴드 (v2500~3300 무가구)
    Fr.label(name,area,Wd/2,3060)
    if loft:
        ladder(Fr,120,3700,720,4900)
        Fr.otb(900,3500,Wd-120,D-120)
        Fr.txt("상부 2층침대 (로프트)",(1750,6350),185,color=9)
        sofa(Fr,Wd-2000,3600,Wd-120,5000,back="E")
        Fr.circ("FUR",(Wd-2700,4300),320)
        tvunit(Fr,120,5400,620,6700,face="E")
        Fr.rect("FUR",Wd-1900,6100,Wd-120,6800)      # 데스크
        Fr.rect("FUR",Wd-1300,5500,Wd-800,6000)
    else:
        wardrobe(Fr,120,3500,820,5100)
        bed(Fr,Wd-2100,3500,Wd-120,5100,head="E")
        nstand(Fr,Wd-620,2900,Wd-120,3400)
        tvunit(Fr,120,5400,620,6700,face="E")
        sofa(Fr,Wd-1900,6300,Wd-120,7100,back="E")
        Fr.circ("FUR",(Wd-2600,6700),320)

def u_family(Fr, name, area, duplex=False):
    """패밀리 : 진입통로 우측 / 욕실 좌측 / 더블 좌측·싱글 우측 정적존"""
    Wd,D=Fr.W,Fr.D
    Fr.door(Wd-300,0,900,"S",sweep=-1,into=+1)
    # 욕실 (좌측)
    Fr.wall(2400,0,2500,2500); Fr.wall(0,2400,2400,2500)
    Fr.door(2400,1600,800,"E",sweep=+1,into=+1)   # 욕실 안쪽으로 열림
    tub(Fr,120,1150,1550,2380)
    toilet(Fr,480,120,340)
    basin(Fr,1250,120,2350,720)
    Fr.txt("욕실",(1150,1750),195)
    # 미니주방 (통로 북측 벽면)
    kitchen(Fr,2700,120,4600,820)
    Fr.txt("미니주방",(3650,1060),170,color=9)
    wardrobe(Fr,Wd-820,1200,Wd-120,2600)
    # 라벨 밴드 (v2700~3300)
    Fr.label(name,area,Wd/2+300,2900)
    bed(Fr,120,3400,2120,5000,head="W")               # 더블
    nstand(Fr,120,5150,620,5650)
    if duplex:
        stair10(Fr,Wd-1120,3400,Wd-120,5650)
        Fr.otb(120,2900,Wd-1300,D-120)
        Fr.txt("상부 자녀실 (복층)",(1700,5400),185,color=9)
        sofa(Fr,2500,5900,4900,6700,back="S")
        Fr.circ("FUR",(5500,6300),330)
        tvunit(Fr,120,6000,620,7100,face="E")
    else:
        bed(Fr,Wd-2100,3400,Wd-120,4400,head="E")     # 싱글
        bed(Fr,Wd-2100,4700,Wd-120,5700,head="E")
        tvunit(Fr,120,5900,620,7100,face="E")
        Fr.circ("FUR",(Wd/2+200,6500),400)
        Fr.rect("FUR",Wd/2-750,6250,Wd/2-350,6650)
        Fr.rect("FUR",Wd/2+1150,6250,Wd/2+1550,6650)

def u_family_wide(Fr, name, area):
    """2F 서측 패밀리 55 : 캐노니컬 W8600 × D5900 (문=동측/홀), 3면 외기(남·북·서)"""
    Wd,D=Fr.W,Fr.D
    Fr.door(900,0,900,"S",sweep=+1,into=+1)
    # 욕실 (진입통로 우측)
    Fr.wall(2100,0,2200,2500); Fr.wall(2200,2400,5100,2500)
    Fr.door(2200,700,800,"W",sweep=+1,into=+1)
    tub(Fr,3450,150,5000,1350)
    toilet(Fr,2600,1800,2020)
    basin(Fr,3300,1700,4950,2350)
    Fr.txt("욕실",(2650,1150),195)
    # 진입부 수납 / 미니주방 (홀측 벽면)
    wardrobe(Fr,5350,120,6800,820,sp="v")
    kitchen(Fr,7000,120,Wd-120,820)
    Fr.txt("미니주방",(7750,1080),170,color=9)
    # 라벨 밴드
    Fr.label(name,area,1450,3365,235,190)
    # 더블베드 (욕실 안쪽 정적존)
    bed(Fr,2900,2800,4500,4800,head="S")
    nstand(Fr,4600,2800,5100,3300)
    # 싱글 2 (북측 정적존)
    bed(Fr,6500,2700,Wd-120,3700,head="W")
    bed(Fr,6500,4000,Wd-120,5000,head="W")
    # 창측 라운지 (서측)
    sofa(Fr,800,4900,2800,5700,back="N")
    Fr.circ("FUR",(3800,5250),380)
    tvunit(Fr,5300,5250,6600,5750,face="S")

# ---------------- 층 골격 ----------------
BW,BD=45620,16500
COR_S,COR_N,BAR_N=7500,9000,16500
TAIL_X1,TAIL_X2=31320,42220
CORE_X1,CORE_X2,CORE_S=11570,18170,10200
ST2_X1,ST2_X2=42220,45620
VOID_X1,VOID_X2=38720,42220

def shell(hall_x1, wins_n, wins_s, wins_w):
    seg=[0]
    for a,b in wins_n: seg+=[a,b]
    seg+=[BW]
    for i in range(0,len(seg),2):
        if seg[i]<seg[i+1]: wall(seg[i],BAR_N-200,seg[i+1],BAR_N)
    for a,b in wins_n: winline(a,BAR_N-200,b,BAR_N,horiz=True)
    # 남측(복도측) 외벽 — 창 개구부 반영
    segs=[0]
    for a,b in wins_s: segs+=[a,b]
    segs+=[TAIL_X1]
    for i in range(0,len(segs),2):
        if segs[i]<segs[i+1]: wall(segs[i],COR_S,segs[i+1],COR_S+200)
    for a,b in wins_s: winline(a,COR_S,b,COR_S+200,horiz=True)
    wall(TAIL_X2,COR_S,BW,COR_S+200)
    # 서측 외벽 — 창 개구부 반영
    segw=[COR_S]
    for a,b in wins_w: segw+=[a,b]
    segw+=[BAR_N]
    for i in range(0,len(segw),2):
        if segw[i]<segw[i+1]: wall(0,segw[i],200,segw[i+1])
    for a,b in wins_w: winline(0,a,200,b,horiz=False)
    wall(BW-200,COR_S,BW,BAR_N)
    wall(TAIL_X1,0,TAIL_X1+200,COR_S); wall(TAIL_X2-200,0,TAIL_X2,COR_S)
    wall(TAIL_X1,0,TAIL_X1+1300,200); wall(TAIL_X2-1300,0,TAIL_X2,200)
    winline(TAIL_X1+1300,0,TAIL_X2-1300,200,horiz=True)
    # 보이드
    wall(VOID_X1,COR_N,VOID_X1+200,BAR_N); wall(VOID_X2-200,COR_N,VOID_X2,BAR_N)
    wall(VOID_X1,COR_N,VOID_X2,COR_N+200)
    otb(VOID_X1+200,COR_N+200,VOID_X2-200,BAR_N-200)
    txt("창고 상부\n(보이드)",((VOID_X1+VOID_X2)/2,(COR_N+BAR_N)/2),215,color=9)
    # 코어
    wall(CORE_X1,CORE_S,CORE_X2,CORE_S+200)
    wall(CORE_X1,CORE_S,CORE_X1+200,BAR_N); wall(CORE_X2-200,CORE_S,CORE_X2,BAR_N)
    wall(CORE_X1+3000,CORE_S+200,CORE_X1+3200,BAR_N)
    for a,b in [(CORE_S+450,CORE_S+2750),(CORE_S+3050,CORE_S+5350)]:
        rect("FUR",CORE_X1+400,a,CORE_X1+2800,b)
        line("FUR",(CORE_X1+400,a),(CORE_X1+2800,b)); line("FUR",(CORE_X1+400,b),(CORE_X1+2800,a))
        txt("EV",(CORE_X1+1600,(a+b)/2),270)
    rect("STAIR",CORE_X1+3400,CORE_S+450,CORE_X2-400,CORE_S+5350)
    for i in range(1,10):
        yy=CORE_S+450+i*(4900/10); line("STAIR",(CORE_X1+3400,yy),(CORE_X2-400,yy))
    txt("계단실 1",(CORE_X1+4900,CORE_S+5800),215)
    # 계단실2
    wall(ST2_X1,COR_S,ST2_X1+200,BAR_N)
    rect("STAIR",ST2_X1+600,COR_S+1000,ST2_X2-500,BAR_N-1000)
    for i in range(1,10):
        yy=COR_S+1000+i*((BAR_N-2000-COR_S)/10); line("STAIR",(ST2_X1+600,yy),(ST2_X2-500,yy))
    txt("계단실 2",((ST2_X1+ST2_X2)/2,COR_S+600),215)
    txt("복    도    (유효 1.5m)",(24800,COR_S+760),260,color=9)

def linen(x1,x2,area):
    wall(x1,COR_N,x1+100,BAR_N); wall(x2-100,COR_N,x2,BAR_N)
    rect("FUR",x1+250,BAR_N-2300,x2-250,BAR_N-400)
    line("FUR",(x1+250,BAR_N-1350),(x2-250,BAR_N-1350))
    rect("FUR",x1+250,COR_N+1500,x2-250,COR_N+2700)
    F(x1,COR_N,x2,BAR_N,0).door((x2-x1)/2-400,0,800,"S",sweep=+1,into=+1)
    txt("리넨실",((x1+x2)/2,COR_N+4100),225)
    txt(area,((x1+x2)/2,COR_N+3750),180,color=9)

def hall(x1,x2):
    cx=(x1+x2)/2
    txt("홀",(cx,COR_S+4600),300)
    circ("FUR",(cx,COR_S+2500),430)
    for a in (0,90,180,270):
        px=cx+880*math.cos(math.radians(a)); py=COR_S+2500+880*math.sin(math.radians(a))
        rect("FUR",px-270,py-270,px+270,py+270)

def bar_room(x1,x2,kind,name,area,special=False):
    wall(x1,COR_N,x1+100,BAR_N)
    Fr=F(x1+100,COR_N+100,x2,BAR_N-200,rot=0)
    if kind=="F": u_family(Fr,name,area,duplex=special)
    else:         u_deluxe(Fr,name,area,loft=special)

def tail_room(x1,x2,kind,name,area,special=False):
    Fr=F(x1+200,200,x2-100,COR_S,rot=180)
    if kind=="F": u_family(Fr,name,area,duplex=special)
    else:         u_deluxe(Fr,name,area,loft=special)

def floor_2F():
    HX1=6100
    shell(HX1,
      wins_n=[(700,5600),(6900,11000),(21500,26900),(28000,33400),(34500,38200),(42800,45100)],
      wins_s=[(700,5600),(12600,17200),(22200,29000)],
      wins_w=[(COR_S+800,BAR_N-800)])
    wall(HX1,COR_S,HX1+200,BAR_N)
    u_family_wide(F(200,COR_S+200,HX1,BAR_N-200,rot=90),"패밀리룸 55타입","54.9 m²")
    hall(HX1+200,CORE_X1); linen(18200,21030,"21.2 m²")
    bar_room(21030,27520,"F","패밀리룸 48타입","48.6 m²")
    bar_room(27520,34010,"F","패밀리룸 48타입","48.6 m²")
    bar_room(34010,38710,"D","디럭스룸 35타입","35.2 m²")
    wall(38710,COR_N,38810,BAR_N)
    tail_room(31320,37320,"F","패밀리룸 45타입","45.0 m²")
    tail_room(37320,42220,"D","디럭스룸 36타입","36.7 m²")
    wall(37320-100,200,37320,COR_S)

def floor_34F(is4F):
    HX1=7701
    shell(HX1,
      wins_n=[(700,7100),(8600,11000),(21200,26100),(27200,32100),(33200,38100),(42800,45100)],
      wins_s=[(700,7100),(12600,17200),(22200,29000)],
      wins_w=[(COR_S+700,COR_S+3900),(COR_S+4900,BAR_N-700)])
    wall(HX1,COR_S,HX1+200,BAR_N)
    wall(200,COR_S+4300,HX1,COR_S+4400)
    for ya,yb in [(COR_S+4400,BAR_N-200),(COR_S+200,COR_S+4300)]:
        u_deluxe(F(200,ya,HX1,yb,rot=90),"디럭스룸 34타입","34.6 m²",loft=is4F)
    hall(HX1+200,CORE_X1); linen(18200,20710,"18.8 m²")
    for x1,x2 in [(20710,26710),(26710,32710),(32710,38710)]:
        bar_room(x1,x2,"F","패밀리룸 45타입","45.0 m²",special=is4F)
    wall(38710,COR_N,38810,BAR_N)
    tail_room(31320,37320,"F","패밀리룸 45타입","45.0 m²",special=is4F)
    tail_room(37320,42220,"D","디럭스룸 36타입","36.7 m²",special=is4F)
    wall(37320-100,200,37320,COR_S)

# ---------------- 생성 ----------------
SHEETS=[("2F",0,floor_2F,("단층형","6실 (패밀리 4 / 디럭스 2)")),
        ("3F",-26000,lambda:floor_34F(False),("단층형","7실 (패밀리 4 / 디럭스 3)")),
        ("4F",-52000,lambda:floor_34F(True),("복층 + 로프트형","7실 (패밀리 복층 4 / 디럭스 로프트 3)"))]
for nm,yo,fn,sub in SHEETS:
    OFF[0],OFF[1]=0.0,float(yo); fn()
    txt(nm,(-4600,BAR_N-2600),2600)
    txt("466 m²",(-4600,BAR_N-4600),700,color=9)
    for i,ln in enumerate(sub):
        txt(ln,(-1500,BAR_N-6400-i*1000),520,color=8,align=TA.RIGHT)

OFF[0],OFF[1]=0.0,0.0
txt("호텔 가은 — 기준층 평면도 (객실 유닛 반영)",(21000,21800),1600)
txt("2·3F 단층형 / 4F 복층·로프트형    ·    출입문 스윙과 진입통로를 비우고, 침대는 진입·주방·계단에서 가장 먼 정적존에 배치",
    (21000,19900),640,color=8)
notes=[
 "1. 실 경계·코어·복도·리넨실·보이드 위치는 26.07.27 개략평면(D안)을 그대로 사용하고 내부 가구만 배치했습니다.",
 "2. 가구배치 원칙 — ① 출입문 스윙구간 및 진입통로(1,500mm) 무가구  ② 욕실문 앞 여유 확보  ③ 침대는 정적존(진입동선 반대편) 배치",
 "3. 4F 해치 영역 = 상부층(자녀실 / 2층침대) 투영범위. 패밀리는 벽체밀착 직선계단 10단, 디럭스는 로프트 경계 사다리로 진입합니다.",
 "4. [가정] 4F 층고 4,500mm 상향(2~3F 대비 +1,300) — 구조·설비 검토 필요. 복층 2,200+300+2,000 / 로프트 2,600+300+1,600",
 "5. 복도 1,500mm는 양옆거실 구간 법정 최소치와 동일 → 마감두께 감안 시 1,600~1,800mm 확대 검토 필요(기 지적사항).",
]
for i,n in enumerate(notes):
    txt(n,(-9500,-60500-i*1000),500,color=8,align=TA.LEFT)

out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"hotel-gaun-typical-floors.dxf")
doc.saveas(out); print("saved:",out)

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy
def render(png, x1, y1, x2, y2, Wi=26):
    """finalize=False + 명시적 extent — finalize=True는 figsize를 덮어써서 사용하지 않음."""
    fig=plt.figure(dpi=110); ax=fig.add_axes([0,0,1,1]); ax.set_axis_off()
    Frontend(RenderContext(doc),MatplotlibBackend(ax),
             config=Configuration(background_policy=BackgroundPolicy.WHITE)).draw_layout(msp,finalize=False)
    fig.set_size_inches(Wi, Wi*(y2-y1)/(x2-x1))
    ax.set_position([0,0,1,1]); ax.set_axis_off()
    ax.set_aspect('equal'); ax.set_adjustable('box')
    ax.set_xlim(x1,x2); ax.set_ylim(y1,y2)
    fig.savefig(png,dpi=110,facecolor="white"); plt.close(fig); print("saved:",png)

D=os.path.dirname(os.path.abspath(__file__))
render(out.replace(".dxf",".png"), -21000, -66000, 48500, 23000, Wi=26)
for nm,yo,_,_ in SHEETS:
    render(os.path.join(D,f"floor-{nm}.png"), -21000, yo-1600, 48500, yo+BAR_N+1600, Wi=24)
