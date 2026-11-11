#!/usr/bin/env python3
"""ตู้รถไฟพิเศษ 8 แบบสำหรับร้านค้า (เจ้าของสั่ง 12 พ.ย. 01:02 "ทำตู้รถไฟให้สวย ขายในร้านค้า หลาย ๆ แบบ")
เขียน design/Wagons2.dc.html (บอร์ดในงานออกแบบ) — ใช้ defs ร่วมจาก Wagons.dc.html (under, bg1/bg2, spk, gGlow, wBody, สีพลอย)
กลุ่มใหม่อยู่ระหว่าง <!--W2-BEGIN--> … <!--W2-END--> → tools/gen_sprites.py ต่อท้าย WAG_DEFS ให้เกมใช้
พิกัดเหมือนตู้เดิม: ตัวตู้ x −90..90 (ทิศวิ่ง) y −77..77 · {{c.main}} {{c.sec}} {{c.dark}} {{c.light}} = สีรถไฟของผู้เล่น
รัน: python3 design/gen_wagons2.py แล้ว python3 tools/gen_sprites.py"""
import re,math,random,pathlib
D=pathlib.Path(__file__).parent;OUT=D/'Wagons2.dc.html'
W1=(D/'Wagons.dc.html').read_text()
SHARED=re.search(r'<svg width="0" height="0"[^>]*>\s*<defs>(.*?)</defs>',W1,re.S).group(1)
F=lambda v:f'{v:.1f}'.rstrip('0').rstrip('.')
GC=['gRed','gBlue','gGreen','gPurple','gYellow','gCyan','gPink']
def gem(x,y,s,col,shape=0,rot=0,shadow=True):
    sh='bg1' if shape==0 else 'bg2'
    o=f'<use href="#{sh}" transform="translate({F(x+2*s)} {F(y+2.6*s)}) rotate({rot}) scale({F(s)})" fill="#000" opacity="0.3"></use>' if shadow else ''
    return o+f'<use href="#{sh}" transform="translate({F(x)} {F(y)}) rotate({rot}) scale({F(s)})" fill="url(#{col})"></use>'
def scatter(seed,cx,cy,rx,ry,n,smin,smax,cols=GC,sep=.66):
    R=random.Random(seed);pts=[];t=0
    while len(pts)<n and t<6000:
        t+=1;a=R.random()*6.283;d=math.sqrt(R.random());x=cx+math.cos(a)*rx*d;y=cy+math.sin(a)*ry*d;s=smin+(smax-smin)*(1-d)**.8
        if all(math.hypot(x-q[0],y-q[1])>sep*11*(s+q[2]) for q in pts):pts.append((x,y,s,d))
    pts.sort(key=lambda q:-q[3]);return ''.join(gem(x,y,s,cols[R.randrange(len(cols))],R.randrange(2),R.randint(-30,30)) for x,y,s,d in pts)
spk=lambda L:''.join(f'<use href="#spk" transform="translate({x} {y}) scale({k})"></use>' for x,y,k in L)
U='<use href="#under"></use>'
def rivets(pts,r=3.5,fill='{{c.dark}}'):return f'<g fill="{fill}">'+''.join(f'<circle cx="{x}" cy="{y}" r="{r}"></circle>' for x,y in pts)+'</g>'
CORN=[(-80,-67),(80,-67),(-80,67),(80,67)]

NEWDEFS=(
 '<linearGradient id="w2Steel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5d647c"></stop><stop offset="0.5" stop-color="#c9cfdd"></stop><stop offset="1" stop-color="#4a5066"></stop></linearGradient>'
 '<radialGradient id="w2Door" cx="0.4" cy="0.35" r="0.7"><stop offset="0" stop-color="#eef2fa"></stop><stop offset="0.55" stop-color="#9aa2b8"></stop><stop offset="1" stop-color="#4a5066"></stop></radialGradient>'
 '<linearGradient id="w2Gold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff3b0"></stop><stop offset="0.45" stop-color="#ffd23f"></stop><stop offset="1" stop-color="#a5700a"></stop></linearGradient>'
 '<linearGradient id="w2Bar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff6c4"></stop><stop offset="0.5" stop-color="#f3c23a"></stop><stop offset="1" stop-color="#b07a0c"></stop></linearGradient>'
 '<linearGradient id="w2Velvet" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5a0a20"></stop><stop offset="0.5" stop-color="#b3203f"></stop><stop offset="1" stop-color="#5a0a20"></stop></linearGradient>'
 '<radialGradient id="w2Dome" cx="0.38" cy="0.32" r="0.75"><stop offset="0" stop-color="#fff8d0"></stop><stop offset="0.45" stop-color="#ffd23f"></stop><stop offset="1" stop-color="#94600a"></stop></radialGradient>'
 '<linearGradient id="w2Ice" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f2fbff"></stop><stop offset="0.5" stop-color="#a9dcf5"></stop><stop offset="1" stop-color="#5aa6d6"></stop></linearGradient>'
 '<linearGradient id="w2Cry" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff"></stop><stop offset="0.5" stop-color="#bff0ff"></stop><stop offset="1" stop-color="#5fb8e8"></stop></linearGradient>'
 '<linearGradient id="w2CryP" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff"></stop><stop offset="0.5" stop-color="#e2d0ff"></stop><stop offset="1" stop-color="#9a72e8"></stop></linearGradient>'
 '<radialGradient id="w2Lava" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#fff3a0"></stop><stop offset="0.35" stop-color="#ffb02e"></stop><stop offset="0.75" stop-color="#ff4a12"></stop><stop offset="1" stop-color="#8a1206"></stop></radialGradient>'
 '<linearGradient id="w2Rock" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4a3a3a"></stop><stop offset="1" stop-color="#1c1416"></stop></linearGradient>'
 '<pattern id="w2Cane" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="16" height="16" fill="#ffffff"></rect><rect width="8" height="16" fill="{{c.main}}"></rect></pattern>'
 '<linearGradient id="w2Cream" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff0f6"></stop><stop offset="1" stop-color="#ffc2dc"></stop></linearGradient>'
 '<linearGradient id="w2Sea" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7fe6ff" stop-opacity="0.85"></stop><stop offset="0.55" stop-color="#1f8fc8" stop-opacity="0.8"></stop><stop offset="1" stop-color="#0b3f78" stop-opacity="0.9"></stop></linearGradient>'
 '<radialGradient id="w2PearlG" cx="0.35" cy="0.3" r="0.75"><stop offset="0" stop-color="#ffffff"></stop><stop offset="0.5" stop-color="#ffeef6"></stop><stop offset="1" stop-color="#c9a6c8"></stop></radialGradient>'
 '<radialGradient id="w2Space" cx="0.5" cy="0.5" r="0.7"><stop offset="0" stop-color="#3a1a7a"></stop><stop offset="0.6" stop-color="#160a3a"></stop><stop offset="1" stop-color="#07041a"></stop></radialGradient>'
 '<radialGradient id="w2NebP" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ff6fd0" stop-opacity="0.7"></stop><stop offset="1" stop-color="#ff6fd0" stop-opacity="0"></stop></radialGradient>'
 '<radialGradient id="w2NebB" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#4fd8ff" stop-opacity="0.6"></stop><stop offset="1" stop-color="#4fd8ff" stop-opacity="0"></stop></radialGradient>'
 '<radialGradient id="w2Planet" cx="0.35" cy="0.3" r="0.8"><stop offset="0" stop-color="#ffe6a8"></stop><stop offset="0.6" stop-color="#ff9a4a"></stop><stop offset="1" stop-color="#8a3a12"></stop></radialGradient>'
 '<g id="w2Star"><path d="M0 -12 L3 -3 L12 0 L3 3 L0 12 L-3 3 L-12 0 L-3 -3 Z"></path></g>'
)

G={}
# 1) ตู้เหมืองแร่ — กระบะผนังเฉียง แร่หิน+พลอยโผล่ อีเตอร์พาดขอบ
o=U+'<rect x="-90" y="-77" width="180" height="154" rx="10" fill="url(#wBody)" stroke="{{c.dark}}" stroke-width="3"></rect>'
o+=('<path d="M-82 -69 L82 -69 L56 -44 L-56 -44 Z" fill="{{c.light}}" stroke="{{c.dark}}" stroke-width="2"></path>'
    '<path d="M-82 69 L82 69 L56 44 L-56 44 Z" fill="{{c.dark}}" stroke="{{c.dark}}" stroke-width="2"></path>'
    '<path d="M-82 -69 L-56 -44 L-56 44 L-82 69 Z" fill="{{c.main}}" stroke="{{c.dark}}" stroke-width="2"></path>'
    '<path d="M82 -69 L56 -44 L56 44 L82 69 Z" fill="{{c.main}}" stroke="{{c.dark}}" stroke-width="2" opacity="0.85"></path>'
    '<rect x="-56" y="-44" width="112" height="88" fill="#2a2026"></rect>')
R=random.Random(5)
for i in range(16):
    x=R.uniform(-48,48);y=R.uniform(-36,36);r=R.uniform(9,15);n=7
    pts=' '.join(f'{F(x+math.cos(k/n*6.283+R.random()*.5)*r*R.uniform(.75,1.1))},{F(y+math.sin(k/n*6.283+R.random()*.5)*r*R.uniform(.75,1.1))}' for k in range(n))
    o+=f'<polygon points="{pts}" fill="{R.choice(["#6b5a56","#7d6b63","#5a4a48","#8a7468"])}" stroke="#2a1f1c" stroke-width="1.5"></polygon>'
o+=scatter(51,0,0,46,34,9,.75,1.05)
o+=('<g transform="translate(40 -52) rotate(-28)"><rect x="-6" y="-3" width="74" height="7" rx="3" fill="#a8663a" stroke="#4a2c12" stroke-width="1.5"></rect>'
    '<path d="M60 -16 Q74 0 60 16 L66 0 Z" fill="#c9cfdd" stroke="#3a3f52" stroke-width="2"></path><rect x="56" y="-5" width="10" height="10" rx="2" fill="#5d647c"></rect></g>')
o+=rivets(CORN+[(0,-72),(0,72)])+'<g fill="{{c.sec}}"><rect x="-90" y="-10" width="8" height="20" rx="2"></rect><rect x="82" y="-10" width="8" height="20" rx="2"></rect></g>'
o+=spk([(-20,-10,1.0),(26,16,0.9),(-34,22,0.8)])
G['w2Mine']=o

# 2) ตู้ราชรถทองคำ — หลังคากำมะหยี่ซ้อนชั้น โดมทอง มงกุฎ ลวดลายทอง
o=U+'<rect x="-90" y="-77" width="180" height="154" rx="16" fill="url(#w2Gold)" stroke="#6a4a06" stroke-width="3"></rect>'
o+='<rect x="-80" y="-67" width="160" height="134" rx="12" fill="url(#w2Velvet)" stroke="#6a4a06" stroke-width="2"></rect>'
o+='<rect x="-73" y="-60" width="146" height="120" rx="10" fill="none" stroke="{{c.main}}" stroke-width="3" opacity="0.9"></rect>'
o+='<g fill="none" stroke="#ffd23f" stroke-width="2.2" stroke-linecap="round">'
for sx in (-1,1):
    for sy in (-1,1):
        o+=f'<path d="M{sx*66} {sy*30} q{sx*-2} {sy*16} {sx*-18} {sy*20} q{sx*-10} {sy*1} {sx*-10} {sy*-8} q{sx*1} {sy*-6} {sx*7} {sy*-4}"></path>'
o+='</g>'
o+='<rect x="-50" y="-44" width="100" height="88" rx="10" fill="url(#w2Gold)" stroke="#6a4a06" stroke-width="2.5"></rect>'
o+='<rect x="-42" y="-36" width="84" height="72" rx="8" fill="url(#w2Velvet)" stroke="#ffd23f" stroke-width="1.5"></rect>'
o+='<circle cx="2" cy="3" r="28" fill="#000" opacity="0.3"></circle><circle cx="0" cy="0" r="28" fill="url(#w2Dome)" stroke="#6a4a06" stroke-width="2.5"></circle>'
o+='<g stroke="#a5700a" stroke-width="1.5" opacity="0.7" fill="none">'+''.join(f'<path d="M0 0 L{F(math.cos(k*.785)*27)} {F(math.sin(k*.785)*27)}"></path>' for k in range(8))+'</g>'
# มงกุฎจากด้านบน: วงทอง 5 แฉก + พลอยกลาง
cr=' '.join(f'{F(math.cos(k/10*6.283-1.571)*(15 if k%2==0 else 9))},{F(math.sin(k/10*6.283-1.571)*(15 if k%2==0 else 9))}' for k in range(10))
o+=f'<polygon points="{cr}" fill="#fff1a8" stroke="#6a4a06" stroke-width="2"></polygon>'+gem(0,0,.62,'gRed',0,0,False)
for k in range(5):
    a=k/5*6.283-1.571;o+=f'<circle cx="{F(math.cos(a)*15)}" cy="{F(math.sin(a)*15)}" r="2.6" fill="#ffffff" stroke="#6a4a06" stroke-width="1"></circle>'
for x,y in CORN:
    o+=f'<circle cx="{x}" cy="{y}" r="9" fill="url(#w2Dome)" stroke="#6a4a06" stroke-width="2"></circle>'+gem(x,y,.38,'gBlue' if x*y>0 else 'gGreen',0,0,False)
for x in (-60,60):o+=gem(x,0,.55,'gPurple',1,0)
o+='<path d="M-30 -20 Q-20 -28 -8 -26" stroke="#ffffff" stroke-width="4" stroke-linecap="round" opacity="0.7" fill="none"></path>'
o+=spk([(-58,-48,1.2),(60,46,1.1),(-12,-18,0.9),(30,-50,0.8)])
G['w2Royal']=o

# 3) ตู้คริสตัลน้ำแข็ง — ก้อนน้ำแข็ง กระจุกผลึกหกเหลี่ยม เกล็ดหิมะ
o=U+'<rect x="-90" y="-77" width="180" height="154" rx="14" fill="{{c.main}}" stroke="{{c.dark}}" stroke-width="3"></rect>'
o+='<rect x="-82" y="-69" width="164" height="138" rx="11" fill="url(#w2Ice)" stroke="#ffffff" stroke-width="2" stroke-opacity="0.8"></rect>'
o+='<g stroke="#ffffff" stroke-width="1.4" opacity="0.5" fill="none"><path d="M-70 -40 L-40 -58 L-20 -30"></path><path d="M30 50 L55 30 L70 52"></path><path d="M-60 40 L-36 54"></path><path d="M40 -56 L66 -36"></path></g>'
def hexp(x,y,r,fill,rot=0):
    P=[(x+math.cos(k*1.0472+rot)*r,y+math.sin(k*1.0472+rot)*r) for k in range(6)]
    s=f'<polygon points="{" ".join(f"{F(a)},{F(b)}" for a,b in P)}" fill="#000" opacity="0.25" transform="translate(2.5 3.5)"></polygon>'
    s+=f'<polygon points="{" ".join(f"{F(a)},{F(b)}" for a,b in P)}" fill="url(#{fill})" stroke="#ffffff" stroke-width="1.6"></polygon>'
    s+=''.join(f'<path d="M{F(x)} {F(y)} L{F(a)} {F(b)}" stroke="#ffffff" stroke-width="1" opacity="0.6"></path>' for a,b in P[::2])
    s+=f'<polygon points="{F(x)},{F(y)} {F(P[4][0])},{F(P[4][1])} {F(P[5][0])},{F(P[5][1])}" fill="#ffffff" opacity="0.55"></polygon>'
    s+=f'<polygon points="{F(x)},{F(y)} {F(P[1][0])},{F(P[1][1])} {F(P[2][0])},{F(P[2][1])}" fill="#2a6ea8" opacity="0.25"></polygon>'
    return s
o+=glow(0,0,70,60) if False else '<ellipse cx="0" cy="0" rx="70" ry="58" fill="url(#gGlow)"></ellipse>'
for x,y,r,f,rt in [(-50,-30,15,'w2Cry',.2),(-52,28,13,'w2CryP',.5),(50,34,15,'w2Cry',.1),(52,-30,12,'w2CryP',.4),(-24,8,18,'w2Cry',.3),(22,-14,21,'w2Cry',0),(18,30,14,'w2CryP',.6),(-12,-40,11,'w2Cry',.5),(-20,46,10,'w2Cry',.2),(62,2,10,'w2Cry',.3)]:
    o+=hexp(x,y,r,f,rt)
for x,y in [(-70,-58),(70,58),(-74,6),(74,-56),(0,62),(36,-62)]:
    o+=f'<g stroke="#ffffff" stroke-width="1.6" stroke-linecap="round" transform="translate({x} {y})">'+''.join(f'<path d="M0 0 L{F(math.cos(k*1.0472)*6)} {F(math.sin(k*1.0472)*6)}"></path>' for k in range(6))+'</g>'
o+=spk([(22,-14,1.3),(-24,8,1.0),(50,34,0.9),(-50,-30,0.9)])
G['w2Crystal']=o

# 4) ตู้ภูเขาไฟ — หินบะซอลต์ รอยแตกลาวาเรือง บ่อลาวามีพลอยลอย
o=U+'<rect x="-90" y="-77" width="180" height="154" rx="12" fill="url(#w2Rock)" stroke="#120c0c" stroke-width="3"></rect>'
o+='<g fill="{{c.main}}" stroke="{{c.dark}}" stroke-width="2"><rect x="-90" y="-77" width="16" height="154" rx="6"></rect><rect x="74" y="-77" width="16" height="154" rx="6"></rect></g>'
o+=rivets([(-82,-60),(-82,0),(-82,60),(82,-60),(82,0),(82,60)],3,'{{c.sec}}')
crk='M-70 -60 L-52 -40 L-60 -20 M60 -64 L44 -44 L52 -30 M-66 60 L-46 44 L-30 56 M68 58 L50 42 L56 26 M-10 -70 L-4 -54 M10 70 L4 56'
o+=f'<path d="{crk}" stroke="#ff6a1a" stroke-width="7" stroke-linecap="round" fill="none" opacity="0.35"></path><path d="{crk}" stroke="#ffcf4a" stroke-width="2.4" stroke-linecap="round" fill="none"></path>'
o+='<path d="M-58 -10 Q-60 -48 -20 -50 Q20 -56 46 -42 Q66 -20 58 12 Q60 46 20 50 Q-20 56 -46 40 Q-62 24 -58 -10 Z" fill="#000" opacity="0.4" transform="translate(2 3)"></path>'
o+='<path d="M-58 -10 Q-60 -48 -20 -50 Q20 -56 46 -42 Q66 -20 58 12 Q60 46 20 50 Q-20 56 -46 40 Q-62 24 -58 -10 Z" fill="url(#w2Lava)" stroke="#3a1006" stroke-width="3"></path>'
o+='<g fill="none" stroke="#fff6b0" stroke-width="1.6" opacity="0.6"><path d="M-36 -20 Q-20 -30 -4 -20 Q12 -10 28 -22"></path><path d="M-30 18 Q-12 8 6 18 Q22 28 38 16"></path></g>'
o+=scatter(61,0,0,40,32,7,.8,1.1,['gRed','gYellow','gRed','gPink'])
for x,y,r in [(-40,-36,2.4),(30,-44,2),(48,30,2.6),(-30,42,2),(4,-56,1.8),(64,-6,2)]:
    o+=f'<circle cx="{x}" cy="{y}" r="{r*2.4}" fill="#ff8a2a" opacity="0.25"></circle><circle cx="{x}" cy="{y}" r="{r}" fill="#ffe28a"></circle>'
o+=spk([(-16,-14,1.0),(22,14,0.9)])
G['w2Magma']=o

# 5) ตู้ขนมหวาน — ขอบลายลูกกวาด ครีมชมพู อมยิ้ม ลูกอมห่อ พลอยน้ำตาล โรยสี
o=U+'<rect x="-90" y="-77" width="180" height="154" rx="18" fill="url(#w2Cane)" stroke="{{c.dark}}" stroke-width="3"></rect>'
o+='<rect x="-80" y="-67" width="160" height="134" rx="14" fill="url(#w2Cream)" stroke="#ffffff" stroke-width="2"></rect>'
o+='<path d="M-80 -40 Q-60 -52 -40 -40 Q-20 -28 0 -40 Q20 -52 40 -40 Q60 -28 80 -40 L80 -67 L-80 -67 Z" fill="#fff8fb" opacity="0.9"></path>'
o+='<path d="M-80 42 Q-60 30 -40 42 Q-20 54 0 42 Q20 30 40 42 Q60 54 80 42 L80 67 L-80 67 Z" fill="#ffe1ee" opacity="0.9"></path>'
def lolly(x,y,r,c1,c2):
    s=f'<circle cx="{x+2}" cy="{y+3}" r="{r}" fill="#000" opacity="0.25"></circle><circle cx="{x}" cy="{y}" r="{r}" fill="{c1}" stroke="#ffffff" stroke-width="2"></circle>'
    pts=' '.join(f'{F(x+math.cos(t*.5)*r*t/16)},{F(y+math.sin(t*.5)*r*t/16)}' for t in range(1,17))
    return s+f'<polyline points="{pts}" fill="none" stroke="{c2}" stroke-width="{F(r*.28)}" stroke-linecap="round"></polyline><circle cx="{F(x-r*.35)}" cy="{F(y-r*.4)}" r="{F(r*.18)}" fill="#ffffff" opacity="0.8"></circle>'
def wrap(x,y,c,rot):
    return (f'<g transform="translate({x} {y}) rotate({rot})"><path d="M-18 -7 L-10 0 L-18 7 Z M18 -7 L10 0 L18 7 Z" fill="{c}" opacity="0.8" stroke="#ffffff" stroke-width="1"></path>'
            f'<ellipse rx="11" ry="8" fill="{c}" stroke="#ffffff" stroke-width="1.6"></ellipse><path d="M-6 -4 Q0 -7 6 -4" stroke="#ffffff" stroke-width="2" fill="none" opacity="0.8"></path></g>')
o+=lolly(-46,-6,17,'#ff7cc6','#ffffff')+lolly(44,10,15,'#7fd8ff','#ffffff')+lolly(4,-30,11,'#ffd23f','#ff7cc6')
o+=wrap(-6,22,'#9b5cff',20)+wrap(58,-36,'#2fbf71',-15)+wrap(-56,40,'#ff9f43',10)
o+=gem(14,40,.7,'gPink',0,10)+gem(-20,-44,.6,'gCyan',1,-10)+gem(-8,0,.62,'gPurple',0,0)+gem(66,40,.5,'gYellow',1,20)
R=random.Random(9)
o+='<g stroke-linecap="round" stroke-width="3">'+''.join(f'<path d="M{F(x)} {F(y)} l{F(math.cos(a)*5)} {F(math.sin(a)*5)}" stroke="{R.choice(["#ff4d6d","#4d8dff","#2fbf71","#ffd23f","#9b5cff"])}"></path>' for x,y,a in [(R.uniform(-72,72),R.uniform(-58,58),R.uniform(0,6.28)) for _ in range(26)])+'</g>'
o+=spk([(-46,-6,0.9),(44,10,0.8),(14,40,0.9)])
G['w2Sweets']=o

# 6) ตู้นิรภัย — เหล็กหมุดย้ำ ประตูกลมวงล้อ ทองคำแท่งสองข้าง
o=U+'<rect x="-90" y="-77" width="180" height="154" rx="10" fill="url(#w2Steel)" stroke="#2a2e3e" stroke-width="3"></rect>'
o+='<g fill="{{c.main}}" stroke="{{c.dark}}" stroke-width="1.5"><rect x="-90" y="-77" width="180" height="11" rx="4"></rect><rect x="-90" y="66" width="180" height="11" rx="4"></rect></g>'
o+=rivets([(x,y) for x in range(-80,90,20) for y in (-58,58)],2.4,'#3a3f52')
def bars(x0,y0):
    s=''
    for i,(dx,dy) in enumerate([(0,0),(0,17),(0,34),(9,8.5),(9,25.5)]):
        x=x0+dx;y=y0+dy
        s+=(f'<path d="M{F(x)} {F(y+3)} L{F(x+26)} {F(y+3)} L{F(x+22)} {F(y+15)} L{F(x+4)} {F(y+15)} Z" fill="#000" opacity="0.3" transform="translate(1.5 2)"></path>'
            f'<path d="M{F(x)} {F(y)} L{F(x+26)} {F(y)} L{F(x+22)} {F(y+13)} L{F(x+4)} {F(y+13)} Z" fill="url(#w2Bar)" stroke="#8a5f06" stroke-width="1.2"></path>'
            f'<rect x="{F(x+5)}" y="{F(y+2)}" width="16" height="3" rx="1" fill="#ffffff" opacity="0.6"></rect>')
    return s
o+=bars(-84,-26)+bars(48,-26)
o+='<circle cx="2" cy="4" r="44" fill="#000" opacity="0.35"></circle><circle cx="0" cy="0" r="44" fill="url(#w2Door)" stroke="#2a2e3e" stroke-width="3"></circle>'
o+='<circle cx="0" cy="0" r="36" fill="none" stroke="{{c.sec}}" stroke-width="4"></circle>'
o+=rivets([(F(math.cos(k*.5236)*40),F(math.sin(k*.5236)*40)) for k in range(12)],2.6,'#3a3f52')
o+='<g stroke="#2a2e3e" stroke-width="5" stroke-linecap="round">'+''.join(f'<path d="M0 0 L{F(math.cos(k*2.094+.3)*24)} {F(math.sin(k*2.094+.3)*24)}"></path>' for k in range(3))+'</g>'
o+=''.join(f'<circle cx="{F(math.cos(k*2.094+.3)*26)}" cy="{F(math.sin(k*2.094+.3)*26)}" r="5" fill="#c9cfdd" stroke="#2a2e3e" stroke-width="2"></circle>' for k in range(3))
o+='<circle r="11" fill="url(#w2Gold)" stroke="#6a4a06" stroke-width="2"></circle>'+gem(0,0,.45,'gBlue',0,0,False)
o+='<path d="M-30 -22 Q-20 -34 -4 -36" stroke="#ffffff" stroke-width="4" stroke-linecap="round" fill="none" opacity="0.6"></path>'
o+=spk([(-70,-24,0.9),(62,8,0.9),(0,0,0.8)])
G['w2Vault']=o

# 7) ตู้ไข่มุกใต้ทะเล — ตู้ปลา น้ำใส หอยเปิดมีไข่มุก สาหร่าย ปลา ฟองอากาศ
o=U+'<rect x="-90" y="-77" width="180" height="154" rx="14" fill="{{c.main}}" stroke="{{c.dark}}" stroke-width="3"></rect>'
o+='<rect x="-82" y="-69" width="164" height="138" rx="10" fill="#f0d9a6"></rect>'
R=random.Random(4)
o+='<g fill="#d8b97a">'+''.join(f'<circle cx="{F(R.uniform(-78,78))}" cy="{F(R.uniform(-64,64))}" r="{F(R.uniform(1,2.2))}"></circle>' for _ in range(40))+'</g>'
for x,y,c in [(-66,-40,'#2fbf71'),(-60,48,'#1f9e6e'),(66,-48,'#2fbf71'),(64,40,'#1f9e6e'),(4,-56,'#3ccf86')]:
    o+=f'<path d="M{x} {y} q8 -8 0 -16 q-8 -8 0 -16 M{x+6} {y} q8 -6 2 -14 q-6 -8 2 -14" stroke="{c}" stroke-width="4.5" stroke-linecap="round" fill="none"></path>'
def clam(x,y,rot,pc='w2PearlG',big=13):
    sc=' '.join(f'{F(math.cos(a)*26)},{F(math.sin(a)*22-2)}' for a in [math.pi+k*math.pi/8 for k in range(9)])
    s=f'<g transform="translate({x} {y}) rotate({rot})">'
    s+=f'<path d="M-26 0 Q-24 18 0 22 Q24 18 26 0 Z" fill="#000" opacity="0.25" transform="translate(2 3)"></path>'
    s+=f'<path d="M-26 0 Q-24 18 0 22 Q24 18 26 0 Z" fill="#f6b8cf" stroke="#b05a80" stroke-width="2"></path>'
    s+=f'<polygon points="{sc}" fill="#ffd2e2" stroke="#b05a80" stroke-width="2"></polygon>'
    s+='<g stroke="#b05a80" stroke-width="1.2" opacity="0.6">'+''.join(f'<path d="M0 -2 L{F(math.cos(math.pi+k*math.pi/4)*24)} {F(math.sin(math.pi+k*math.pi/4)*20-2)}"></path>' for k in range(1,4))+'</g>'
    s+=f'<circle cx="1.5" cy="8.5" r="{big}" fill="#000" opacity="0.2"></circle><circle cx="0" cy="6" r="{big}" fill="url(#{pc})" stroke="#e8d0e8" stroke-width="1"></circle><circle cx="-4" cy="1" r="{F(big*.3)}" fill="#ffffff"></circle></g>'
    return s
o+=clam(-34,-10,0)+clam(36,6,180,big=11)+clam(-2,40,0,big=9)
def fish(x,y,rot,c):return (f'<g transform="translate({x} {y}) rotate({rot})"><path d="M8 0 L16 -7 L16 7 Z" fill="{c}"></path><ellipse rx="10" ry="6" fill="{c}" stroke="#ffffff" stroke-width="1"></ellipse>'
                             f'<circle cx="-5" cy="-1.5" r="1.6" fill="#1a1d2c"></circle><path d="M-1 -5 Q2 0 -1 5" stroke="#ffffff" stroke-width="1.4" fill="none"></path></g>')
o+=fish(30,-44,200,'#ff9f43')+fish(-50,30,-20,'#ffd23f')+fish(58,40,170,'#ff7cc6')
o+='<rect x="-82" y="-69" width="164" height="138" rx="10" fill="url(#w2Sea)" opacity="0.55"></rect>'
o+='<g fill="none" stroke="#ffffff" stroke-width="1.8" opacity="0.45"><path d="M-70 -20 Q-56 -28 -42 -20 T-14 -20"></path><path d="M10 24 Q24 16 38 24 T66 24"></path><path d="M-40 58 Q-26 50 -12 58"></path></g>'
o+='<g fill="none" stroke="#ffffff" stroke-width="1.6" opacity="0.85">'+''.join(f'<circle cx="{x}" cy="{y}" r="{r}"></circle>' for x,y,r in [(-14,-38,4),(-8,-48,2.6),(52,-10,3.4),(58,-20,2.2),(-60,4,3),(18,56,2.8)])+'</g>'
o+='<rect x="-82" y="-69" width="164" height="138" rx="10" fill="none" stroke="#e6faff" stroke-width="2.5" opacity="0.8"></rect><path d="M-70 -58 L-40 -58 M-70 -50 L-58 -50" stroke="#ffffff" stroke-width="4" stroke-linecap="round" opacity="0.75"></path>'
o+='<g fill="{{c.sec}}"><rect x="-90" y="-10" width="8" height="20" rx="2"></rect><rect x="82" y="-10" width="8" height="20" rx="2"></rect></g>'
o+=spk([(-34,-4,1.0),(36,-2,0.8),(-2,46,0.7)])
G['w2Pearl']=o

# 8) ตู้กาแล็กซี — อวกาศในตู้ เนบิวลา ดาวเคราะห์มีวงแหวน พลอยรูปดาว
o=U+'<rect x="-90" y="-77" width="180" height="154" rx="16" fill="{{c.main}}" stroke="{{c.dark}}" stroke-width="3"></rect>'
o+='<rect x="-82" y="-69" width="164" height="138" rx="12" fill="url(#w2Space)"></rect>'
o+='<ellipse cx="-30" cy="-20" rx="56" ry="34" fill="url(#w2NebP)"></ellipse><ellipse cx="34" cy="24" rx="54" ry="36" fill="url(#w2NebB)"></ellipse>'
R=random.Random(12)
o+='<g fill="#ffffff">'+''.join(f'<circle cx="{F(R.uniform(-78,78))}" cy="{F(R.uniform(-64,64))}" r="{F(R.choice([.7,.9,1.1,1.5]))}" opacity="{F(R.uniform(.5,1))}"></circle>' for _ in range(46))+'</g>'
o+='<g transform="translate(-44 30)"><ellipse rx="28" ry="8" fill="none" stroke="#ffe6a8" stroke-width="3" opacity="0.5" transform="rotate(-20)"></ellipse><circle r="15" fill="url(#w2Planet)"></circle>'
o+='<path d="M-26 9 A28 8 -20 0 0 26 -9" fill="none" stroke="#ffe6a8" stroke-width="3" transform="rotate(0)"></path></g>'
o+='<circle cx="52" cy="-40" r="9" fill="#cfd8ff"></circle><circle cx="55" cy="-43" r="9" fill="url(#w2Space)" opacity="0.85"></circle>'
for x,y,s,c in [(10,-10,1.5,'#fff1a8'),(-30,-40,1.0,'#ff9be0'),(44,20,1.1,'#9be7ff'),(-6,44,.9,'#ffd23f'),(66,-2,.8,'#ffffff')]:
    o+=f'<use href="#w2Star" transform="translate({x} {y}) scale({s*2.2})" fill="{c}" opacity="0.25"></use><use href="#w2Star" transform="translate({x} {y}) scale({s})" fill="{c}"></use>'
o+=gem(-12,10,.72,'gPurple',0,10)+gem(28,-30,.6,'gCyan',1,-15)+gem(20,44,.55,'gPink',0,0)
o+='<rect x="-82" y="-69" width="164" height="138" rx="12" fill="url(#wGlass)" opacity="0.6"></rect><path d="M-70 -58 L-44 -58 M-70 -50 L-60 -50" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" opacity="0.7"></path>'
o+=rivets(CORN,3.2,'{{c.sec}}')
G['w2Cosmos']=o

ITEMS=[('w2Mine','ตู้เหมืองแร่','กระบะผนังเฉียง ก้อนแร่มีพลอยโผล่ อีเตอร์พาดขอบ',22000),
       ('w2Sweets','ตู้ขนมหวาน','ขอบลายลูกกวาด ครีมชมพู อมยิ้ม ลูกอมห่อ โรยสี',25000),
       ('w2Crystal','ตู้คริสตัลน้ำแข็ง','ก้อนน้ำแข็ง กระจุกผลึกหกเหลี่ยมฟ้า-ม่วง เกล็ดหิมะ',35000),
       ('w2Pearl','ตู้ไข่มุกใต้ทะเล','ตู้ปลาใส หอยเปิดมีไข่มุก สาหร่าย ปลา ฟองอากาศ',40000),
       ('w2Magma','ตู้ภูเขาไฟ','หินบะซอลต์ รอยแตกเรืองแสง บ่อลาวามีพลอยลอย',45000),
       ('w2Vault','ตู้นิรภัย','เหล็กหมุดย้ำ ประตูกลมวงล้อ ทองคำแท่งสองข้าง',50000),
       ('w2Royal','ตู้ราชรถทองคำ','กำมะหยี่แดงขอบทอง โดมทอง มงกุฎฝังพลอย',60000),
       ('w2Cosmos','ตู้กาแล็กซี','อวกาศในตู้ เนบิวลา ดาวเคราะห์มีวงแหวน พลอยรูปดาว',80000)]

def card(gid,name,desc,price):
    return (f'<div style="background: #161b3f; border: 1.5px solid #2a3170; border-radius: 20px; padding: 16px; display: flex; flex-direction: column; gap: 8px">'
            f'<div style="display: flex; justify-content: space-between; align-items: center"><h2 style="margin: 0; font-size: 21px; font-weight: 600">{name}</h2><span style="font-size: 12.5px; padding: 3px 9px; border-radius: 99px; background: #3a2f10; color: #ffd23f">{price:,} 🪙</span></div>'
            f'<svg viewBox="-115 -100 230 200" style="width: 100%; height: 230px; display: block; border-radius: 14px; background: #121633" role="img" aria-label="{name} มุมบน"><use href="#{gid}"></use></svg>'
            f'<p style="margin: 0; font-size: 14px; line-height: 1.5; color: #cfd6ff">{desc}</p></div>')
def train():
    s='<svg viewBox="0 0 1312 210" style="width: 100%; height: 210px; display: block; border-radius: 14px; background: #12163a" role="img" aria-label="ขบวนตู้ใหม่ทั้ง 8 แบบ">'
    s+='<g stroke="#4a4f66" stroke-width="9" stroke-linecap="round"><line x1="70" y1="105" x2="1250" y2="105"></line></g>'
    for i,(g,_,_,_) in enumerate(ITEMS):s+=f'<g transform="translate({F(86+i*163)} 105) scale(0.78)"><use href="#{g}"></use></g>'
    return s+'</svg>'
def build():
    groups=''.join(f'\n      <g id="{g}">{G[g]}</g>' for g,_,_,_ in ITEMS)
    html=f'''<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<title>ตู้พิเศษ</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Mitr:wght@300;400;500;600&amp;display=swap" rel="stylesheet">
<style>
body{{margin:0}}
</style>
</helmet>
<div style="width: 1440px; height: 1340px; box-sizing: border-box; padding: 52px 64px; background: #0e1230; color: #e9ecff; font-family: Mitr, sans-serif; display: flex; flex-direction: column; gap: 22px">
  <svg width="0" height="0" style="position: absolute" aria-hidden="true">
    <defs>{SHARED}
<!--W2-BEGIN-->{NEWDEFS}{groups}
<!--W2-END-->
    </defs>
  </svg>
  <div style="display: flex; flex-direction: column; gap: 6px">
    <div style="font-size: 15px; color: #ffd23f; letter-spacing: 0.08em">รถไฟซ่า · ร้านค้า</div>
    <h1 style="margin: 0; font-size: 44px; font-weight: 600; line-height: 1.15">ตู้พิเศษ 8 แบบ — ขายในร้านค้า</h1>
    <p style="margin: 0; font-size: 17px; color: #aab3e6; max-width: 980px; line-height: 1.55">มองจากบนขนาดเดียวกับตู้เดิม · ขอบ/คาน/หมุดเปลี่ยนตามสีรถไฟที่ผู้เล่นเลือก (ลองเปลี่ยนสีที่แผงด้านข้าง) · ทุกตู้ยังขนเพชรพลอยตามธีม</p>
  </div>
  <div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px">{''.join(card(*it) for it in ITEMS)}</div>
  <div style="background: #161b3f; border: 1.5px solid #2a3170; border-radius: 20px; padding: 18px; display: flex; flex-direction: column; gap: 10px">
    <div style="display: flex; justify-content: space-between; align-items: baseline"><h2 style="margin: 0; font-size: 22px; font-weight: 600">ต่อเป็นขบวน</h2><span style="font-size: 14px; color: #aab3e6">ในเกมทั้งขบวนใช้ตู้แบบเดียวกัน — ภาพนี้วางเรียงให้เทียบกัน</span></div>
    {train()}
  </div>
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"main":{{"editor":"color","default":"#e84a5f","options":["#e84a5f","#3d8bff","#2fbf71","#9b5cff"],"section":"สีรถไฟ"}},"sec":{{"editor":"color","default":"#ffd23f","options":["#ffd23f","#ffffff","#ff9f43","#9be7ff"],"section":"สีรถไฟ"}},"$preview":{{"width":1440,"height":1340}}}}'>
class Component extends DCLogic {{
  renderVals() {{
    const hex = (h) => {{ h = String(h || '').replace('#', ''); if (h.length === 3) h = h.split('').map((x) => x + x).join(''); const n = parseInt(h, 16) || 0; return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }};
    const mix = (h, t) => {{ const c = hex(h); const f = t < 0 ? c.map((v) => v * (1 + t)) : c.map((v) => v + (255 - v) * t); return '#' + f.map((v) => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, '0')).join(''); }};
    const main = this.props.main ?? '#e84a5f', sec = this.props.sec ?? '#ffd23f';
    return {{ c: {{ main, dark: mix(main, -0.45), light: mix(main, 0.38), sec, secDark: mix(sec, -0.4), secLight: mix(sec, 0.4) }} }};
  }}
}}
</script>
</body>
</html>
'''
    OUT.write_text(html);print('wrote',OUT,len(html),{g:len(G[g]) for g in G})
build()
