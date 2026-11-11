#!/usr/bin/env python3
"""สิ่งกีดขวางโหมดผจญภัยแบบใหม่ (เจ้าของสั่ง 12 พ.ย. 01:23 "Claude design รูปหิน และสิ่งกีดขวางใหม่")
เขียน design/Obstacles.dc.html — 3 โลก (🌾 ทุ่งพลอย / 🏭 ย่านโกดัง / 🌋 หุบเขาไฟ) × หิน 2 แบบ + บ้าน + โคลน · เสาไม้กั้น 1 แบบ
มองจากบนเหมือนในเกม · หิน/โคลน: viewBox -110..110 (วงชน = รัศมี 100) · บ้าน: -100 -62 200 124 (ยืดตาม w×h) · เสาไม้กั้น: -40..40
กลุ่ม: obR{1,2,3}{a,b} obH{1,2,3} obM{1,2,3} obGate → tools/gen_sprites.py ใส่ OB_DEFS ให้เกม
รัน: python3 design/gen_obstacles.py แล้ว python3 tools/gen_sprites.py"""
import math,random,pathlib
OUT=pathlib.Path(__file__).with_name('Obstacles.dc.html')
F=lambda v:f'{v:.1f}'.rstrip('0').rstrip('.')
def pts(P):return ' '.join(f'{F(x)},{F(y)}' for x,y in P)
def blob(seed,n,r,jit,cx=0,cy=0):
    R=random.Random(seed);return [(cx+math.cos(k/n*6.283+R.uniform(-.15,.15))*r*R.uniform(1-jit,1+jit*.4),cy+math.sin(k/n*6.283+R.uniform(-.15,.15))*r*R.uniform(1-jit,1+jit*.4)) for k in range(n)]
def smooth(P):   # เส้นโค้งปิดผ่านจุดกึ่งกลาง
    n=len(P);d=''
    for i in range(n):
        a=P[i];b=P[(i+1)%n];m=((a[0]+b[0])/2,(a[1]+b[1])/2)
        d+=(f'M{F(m[0])} {F(m[1])}' if i==0 else '')
        c=P[(i+1)%n];m2=((b[0]+c[0])/2,(b[1]+c[1])/2);d+=f' Q{F(b[0])} {F(b[1])} {F(m2[0])} {F(m2[1])}'
    return d+' Z'
def shade(hexc,t):
    h=hexc.lstrip('#');c=[int(h[i:i+2],16) for i in (0,2,4)]
    c=[v*(1+t) if t<0 else v+(255-v)*t for v in c];return '#'+''.join(f'{int(max(0,min(255,v))):02x}' for v in c)
def boulder(seed,r,base,cx=0,cy=0,n=9,jit=.22,edge='#1c1e28'):
    """หินเหลี่ยมโลว์โพลี: แต่ละหน้ารับแสงจากซ้ายบน"""
    P=blob(seed,n,r,jit,cx,cy);ix,iy=cx-r*.18,cy-r*.22
    o=f'<polygon points="{pts([(x+r*.1,y+r*.14) for x,y in P])}" fill="#000" opacity="0.35"></polygon>'
    for i in range(n):
        a=P[i];b=P[(i+1)%n];mx,my=(a[0]+b[0])/2-ix,(a[1]+b[1])/2-iy;ang=math.atan2(my,mx)
        lit=math.cos(ang-(-2.35))   # แสงจากซ้ายบน
        o+=f'<polygon points="{pts([(ix,iy),a,b])}" fill="{shade(base,.38*lit if lit>0 else .45*lit)}" stroke="{shade(base,-.25)}" stroke-width="1"></polygon>'
    T=[(ix+(x-ix)*.42,iy+(y-iy)*.42) for x,y in P]
    o+=f'<polygon points="{pts(T)}" fill="{shade(base,.3)}" stroke="{shade(base,.5)}" stroke-width="1" opacity="0.9"></polygon>'
    o+=f'<polygon points="{pts(P)}" fill="none" stroke="{edge}" stroke-width="2.4" stroke-linejoin="round"></polygon>'
    return o
def shard(x,y,L,w,ang,c1,c2,c3):
    ca,sa=math.cos(ang),math.sin(ang);p=lambda u,v:(x+ca*u-sa*v,y+sa*u+ca*v)
    o=f'<polygon points="{pts([p(0,-w),p(L*.75,-w*.7),p(L,0),p(L*.75,w*.7),p(0,w)])}" fill="{c2}" stroke="#ffffff" stroke-width="1.2" stroke-opacity="0.7"></polygon>'
    o+=f'<polygon points="{pts([p(0,-w),p(L*.75,-w*.7),p(L,0),p(0,0)])}" fill="{c1}" opacity="0.9"></polygon>'
    o+=f'<polygon points="{pts([p(0,0),p(L,0),p(L*.75,w*.7),p(0,w)])}" fill="{c3}" opacity="0.6"></polygon>'
    return o
spk=lambda x,y,k:f'<use href="#obSpk" transform="translate({F(x)} {F(y)}) scale({F(k)})"></use>'
def tuft(x,y,c='#5fbf58',k=1):
    return f'<g stroke="{c}" stroke-width="{F(2.4*k)}" stroke-linecap="round" fill="none"><path d="M{F(x)} {F(y)} l{F(-5*k)} {F(-10*k)}"></path><path d="M{F(x)} {F(y)} l0 {F(-12*k)}"></path><path d="M{F(x)} {F(y)} l{F(5*k)} {F(-10*k)}"></path></g>'

DEFS=('<g id="obSpk"><path d="M0 -10 L1.8 -1.8 L10 0 L1.8 1.8 L0 10 L-1.8 1.8 L-10 0 L-1.8 -1.8 Z" fill="#ffffff"></path></g>'
 '<linearGradient id="obWood" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d9a066"></stop><stop offset="1" stop-color="#8a5a2b"></stop></linearGradient>'
 '<radialGradient id="obDrum" cx="0.38" cy="0.35" r="0.7"><stop offset="0" stop-color="#7aa8ff"></stop><stop offset="1" stop-color="#1f4ea8"></stop></radialGradient>'
 '<radialGradient id="obDrumR" cx="0.38" cy="0.35" r="0.7"><stop offset="0" stop-color="#ff8a7a"></stop><stop offset="1" stop-color="#a8261f"></stop></radialGradient>'
 '<radialGradient id="obDrumY" cx="0.38" cy="0.35" r="0.7"><stop offset="0" stop-color="#ffe07a"></stop><stop offset="1" stop-color="#c98a0c"></stop></radialGradient>'
 '<radialGradient id="obMud" cx="0.45" cy="0.42" r="0.6"><stop offset="0" stop-color="#3a2414"></stop><stop offset="0.7" stop-color="#5c3a1e"></stop><stop offset="1" stop-color="#7a5230"></stop></radialGradient>'
 '<radialGradient id="obOil" cx="0.5" cy="0.5" r="0.55"><stop offset="0" stop-color="#05060a"></stop><stop offset="0.8" stop-color="#14161f"></stop><stop offset="1" stop-color="#2a2d3a"></stop></radialGradient>'
 '<linearGradient id="obSheen" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff6fd0" stop-opacity="0.5"></stop><stop offset="0.35" stop-color="#ffd23f" stop-opacity="0.35"></stop><stop offset="0.65" stop-color="#4fd8ff" stop-opacity="0.5"></stop><stop offset="1" stop-color="#7cfc9a" stop-opacity="0.35"></stop></linearGradient>'
 '<radialGradient id="obTar" cx="0.5" cy="0.5" r="0.55"><stop offset="0" stop-color="#2a1006"></stop><stop offset="0.6" stop-color="#1a1214"></stop><stop offset="1" stop-color="#3a2a28"></stop></radialGradient>'
 '<radialGradient id="obEmber" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ffd27a" stop-opacity="0.95"></stop><stop offset="0.4" stop-color="#ff7a1a" stop-opacity="0.6"></stop><stop offset="1" stop-color="#ff3a0a" stop-opacity="0"></stop></radialGradient>'
 '<linearGradient id="obBarn" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7a1f1a"></stop><stop offset="1" stop-color="#c8432f"></stop></linearGradient>'
 '<linearGradient id="obBarn2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e86a4f"></stop><stop offset="1" stop-color="#b8352a"></stop></linearGradient>'
 '<pattern id="obCorr" width="9" height="10" patternUnits="userSpaceOnUse"><rect width="9" height="10" fill="#9aa6bf"></rect><rect width="3" height="10" fill="#c9d2e4"></rect><rect x="6" width="2" height="10" fill="#6f7a92"></rect></pattern>'
 '<pattern id="obHaz" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="12" height="12" fill="#ffd23f"></rect><rect width="6" height="12" fill="#1a1a22"></rect></pattern>'
 '<pattern id="obSlate" width="16" height="10" patternUnits="userSpaceOnUse"><rect width="16" height="10" fill="#2e2a30"></rect><rect x="1" y="1" width="14" height="8" rx="2" fill="#3e3840"></rect><rect x="9" y="5" width="14" height="8" rx="2" fill="#363038"></rect></pattern>'
 '<pattern id="obCane" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="14" height="14" fill="#ffffff"></rect><rect width="7" height="14" fill="#e8302a"></rect></pattern>')

G={}
# ---------- 🌾 ทุ่งพลอย ----------
o=boulder(11,86,'#8a90a8')
o+='<g fill="#4fae4f" opacity="0.85"><ellipse cx="-44" cy="-50" rx="22" ry="10" transform="rotate(-30 -44 -50)"></ellipse><ellipse cx="-62" cy="-18" rx="12" ry="7" transform="rotate(-70 -62 -18)"></ellipse></g>'
o+='<g fill="#7fdc6f" opacity="0.8"><circle cx="-48" cy="-54" r="4"></circle><circle cx="-36" cy="-48" r="3"></circle></g>'
o+=shard(10,-6,46,13,-0.9,'#ffd2dc','#ff4d6d','#9e1030')+shard(18,4,38,11,-0.2,'#d2fff0','#2ee59d','#0b7a4f')+shard(4,10,34,10,0.6,'#e2ecff','#4d8dff','#14307e')
o+=spk(38,-44,.9)+spk(48,6,.7)+tuft(-80,40)+tuft(70,58,'#4fae4f',.9)
G['obR1a']=o
o=boulder(21,56,'#8a90a8',-26,-18,8)+boulder(22,42,'#7d8396',36,22,7)+boulder(23,30,'#969cb2',-30,48,7)
o+=shard(-26,-20,30,9,-1.2,'#fff4d0','#ffb627','#a35a00')+shard(36,22,24,8,-0.4,'#f2e2ff','#b26bff','#5a1a9e')
o+='<g fill="#4fae4f" opacity="0.85"><ellipse cx="-50" cy="-48" rx="14" ry="7" transform="rotate(-35 -50 -48)"></ellipse></g>'
o+=tuft(10,-60)+tuft(78,-20,'#4fae4f')+tuft(-70,30,'#5fbf58',.9)+tuft(6,70)+spk(-14,-46,.7)
G['obR1b']='<g transform="scale(1.28)">'+o+'</g>'   # กองหินเล็กขยายให้เต็มวงชน
o=f'<path d="{smooth(blob(31,14,92,.12))}" fill="#000" opacity="0.25" transform="translate(5 7)"></path>'
o+=f'<path d="{smooth(blob(31,14,92,.12))}" fill="#7a5230"></path><path d="{smooth(blob(32,13,74,.14))}" fill="url(#obMud)"></path>'
o+='<g fill="#2a180c" opacity="0.55"><ellipse cx="-30" cy="-6" rx="9" ry="5" transform="rotate(30 -30 -6)"></ellipse><ellipse cx="-14" cy="10" rx="9" ry="5" transform="rotate(30 -14 10)"></ellipse><ellipse cx="2" cy="26" rx="9" ry="5" transform="rotate(30 2 26)"></ellipse></g>'
o+='<g fill="none" stroke="#2a180c" stroke-width="3" opacity="0.4"><path d="M-60 40 Q0 10 60 -40"></path><path d="M-52 52 Q8 22 66 -26"></path></g>'
o+='<g fill="#ffffff" opacity="0.45"><ellipse cx="-30" cy="-36" rx="14" ry="5" transform="rotate(-20 -30 -36)"></ellipse><ellipse cx="22" cy="-44" rx="8" ry="3" transform="rotate(-20 22 -44)"></ellipse><circle cx="34" cy="30" r="3"></circle></g>'
for a in range(0,360,30):
    x=math.cos(math.radians(a))*92;y=math.sin(math.radians(a))*92;o+=tuft(x,y,'#5fbf58' if a%60 else '#4fae4f',.95)
G['obM1']=o
# บ้านนา: โรงนาหลังคาแดงสองชั้น ขอบขาว ฟางข้าง
o='<rect x="-96" y="-56" width="196" height="120" rx="6" fill="#000" opacity="0.35" transform="translate(5 6)"></rect>'
o+='<path d="M-98 -60 L98 -60 L90 0 L-90 0 Z" fill="url(#obBarn)" stroke="#4a1210" stroke-width="2"></path><path d="M-90 0 L90 0 L98 60 L-98 60 Z" fill="url(#obBarn2)" stroke="#4a1210" stroke-width="2"></path>'
o+='<g stroke="#4a1210" stroke-width="1.3" opacity="0.5">'+''.join(f'<path d="M{x} -58 V58"></path>' for x in range(-86,92,12))+'</g>'
o+='<path d="M-94 0 H94" stroke="#f6efe0" stroke-width="6" stroke-linecap="round"></path><path d="M-98 -60 L98 -60 L98 60 L-98 60 Z" fill="none" stroke="#f6efe0" stroke-width="4" stroke-linejoin="round"></path>'
o+='<rect x="-16" y="-50" width="32" height="24" rx="3" fill="#f6efe0" stroke="#4a1210" stroke-width="2"></rect><path d="M-16 -50 L16 -26 M16 -50 L-16 -26" stroke="#c8432f" stroke-width="3"></path>'
o+='<circle cx="58" cy="-30" r="9" fill="#5a5f74" stroke="#2a2d3a" stroke-width="2"></circle><path d="M52 -30 H64 M58 -36 V-24" stroke="#c9cfdd" stroke-width="2"></path>'
for x,y in [(-70,40),(-50,46)]:o+=f'<g><ellipse cx="{x}" cy="{y}" rx="12" ry="9" fill="#e8c64a" stroke="#a5700a" stroke-width="1.5"></ellipse><path d="M{x-8} {y-2} H{x+8} M{x-8} {y+3} H{x+8}" stroke="#a5700a" stroke-width="1"></path></g>'
G['obH1']=o
# ---------- 🏭 ย่านโกดัง ----------
def crate(x,y,s,rot):
    w=s;return (f'<g transform="translate({F(x)} {F(y)}) rotate({rot})"><rect x="{F(-w/2+4)}" y="{F(-w/2+5)}" width="{F(w)}" height="{F(w)}" rx="3" fill="#000" opacity="0.35"></rect>'
                f'<rect x="{F(-w/2)}" y="{F(-w/2)}" width="{F(w)}" height="{F(w)}" rx="3" fill="url(#obWood)" stroke="#4a2c12" stroke-width="2.5"></rect>'
                f'<rect x="{F(-w/2+5)}" y="{F(-w/2+5)}" width="{F(w-10)}" height="{F(w-10)}" fill="none" stroke="#6a4020" stroke-width="2.5"></rect>'
                f'<path d="M{F(-w/2+5)} {F(-w/2+5)} L{F(w/2-5)} {F(w/2-5)} M{F(w/2-5)} {F(-w/2+5)} L{F(-w/2+5)} {F(w/2-5)}" stroke="#6a4020" stroke-width="3"></path>'
                f'<rect x="{F(-w/2+3)}" y="{F(-w/2+3)}" width="{F(w-6)}" height="3" fill="#ffffff" opacity="0.3"></rect></g>')
o=crate(-34,-30,70,-6)+crate(38,-24,58,8)+crate(-8,40,64,3)+crate(48,48,40,-12)
o+='<path d="M-70 -64 Q-10 -78 70 -52" stroke="#c9a26a" stroke-width="3" fill="none" stroke-dasharray="6 3"></path>'
o+='<rect x="-74" y="58" width="40" height="10" rx="2" fill="#5a3a1f"></rect><rect x="-72" y="52" width="36" height="6" rx="2" fill="#7a5230"></rect>'
G['obR2a']=o
def drum(x,y,r,g):
    return (f'<circle cx="{F(x+4)}" cy="{F(y+5)}" r="{F(r)}" fill="#000" opacity="0.35"></circle><circle cx="{F(x)}" cy="{F(y)}" r="{F(r)}" fill="url(#{g})" stroke="#11131a" stroke-width="2.5"></circle>'
            f'<circle cx="{F(x)}" cy="{F(y)}" r="{F(r*.78)}" fill="none" stroke="#ffffff" stroke-opacity="0.35" stroke-width="2"></circle><circle cx="{F(x)}" cy="{F(y)}" r="{F(r*.5)}" fill="none" stroke="#000" stroke-opacity="0.3" stroke-width="1.5"></circle>'
            f'<circle cx="{F(x+r*.4)}" cy="{F(y-r*.25)}" r="{F(r*.12)}" fill="#c9cfdd" stroke="#2a2d3a" stroke-width="1"></circle><path d="M{F(x-r*.5)} {F(y-r*.55)} q{F(r*.3)} {F(-r*.2)} {F(r*.6)} {F(-r*.1)}" stroke="#ffffff" stroke-width="2.5" fill="none" opacity="0.6" stroke-linecap="round"></path>')
o=drum(-36,-30,30,'obDrum')+drum(30,-38,26,'obDrumY')+drum(-2,22,32,'obDrumR')+drum(52,24,24,'obDrum')+drum(-52,34,22,'obDrumY')
o+='<path d="M-40 58 Q-20 70 10 64 Q30 60 44 70" stroke="#0b0c10" stroke-width="8" fill="none" stroke-linecap="round" opacity="0.6"></path>'
o+='<g transform="translate(-2 22)"><path d="M0 -12 L11 7 L-11 7 Z" fill="#ffd23f" stroke="#1a1a22" stroke-width="2"></path><rect x="-1.4" y="-5" width="2.8" height="7" fill="#1a1a22"></rect><circle cy="4.6" r="1.4" fill="#1a1a22"></circle></g>'
G['obR2b']='<g transform="scale(1.3)">'+o+'</g>'
o=f'<path d="{smooth(blob(41,14,90,.15))}" fill="#000" opacity="0.2" transform="translate(4 6)"></path><path d="{smooth(blob(41,14,90,.15))}" fill="url(#obOil)" stroke="#3a3f52" stroke-width="2"></path>'
o+=f'<path d="{smooth(blob(42,12,62,.2,-8,-6))}" fill="url(#obSheen)" opacity="0.8"></path><path d="{smooth(blob(43,10,34,.2,16,14))}" fill="url(#obSheen)" opacity="0.6" transform="rotate(60 16 14)"></path>'
o+='<g fill="#ffffff" opacity="0.4"><ellipse cx="-34" cy="-40" rx="16" ry="5" transform="rotate(-25 -34 -40)"></ellipse><circle cx="30" cy="-30" r="3"></circle></g>'
o+='<g fill="#0b0c10" opacity="0.8"><circle cx="86" cy="30" r="6"></circle><circle cx="96" cy="44" r="4"></circle><circle cx="-90" cy="-30" r="5"></circle></g>'
G['obM2']=o
o='<rect x="-96" y="-56" width="196" height="120" rx="4" fill="#000" opacity="0.35" transform="translate(5 6)"></rect>'
o+='<rect x="-98" y="-60" width="196" height="120" rx="4" fill="url(#obCorr)" stroke="#2c3346" stroke-width="2.5"></rect>'
o+='<path d="M-98 0 H98" stroke="#5a647c" stroke-width="5"></path><rect x="-98" y="-60" width="196" height="6" fill="#e6ecf7" opacity="0.6"></rect>'
o+=''.join(f'<rect x="{x}" y="-46" width="22" height="34" rx="2" fill="#9be7ff" opacity="0.7" stroke="#e6faff" stroke-width="1.5"></rect><rect x="{x}" y="12" width="22" height="34" rx="2" fill="#7fc8e8" opacity="0.6" stroke="#e6faff" stroke-width="1.5"></rect>' for x in (-70,-20,30))
o+='<rect x="60" y="-48" width="28" height="26" rx="3" fill="#c9cfdd" stroke="#3a3f52" stroke-width="2"></rect><circle cx="74" cy="-35" r="9" fill="#5d647c" stroke="#2a2d3a" stroke-width="1.5"></circle><path d="M66 -35 H82 M74 -43 V-27" stroke="#2a2d3a" stroke-width="1.5"></path>'
o+='<rect x="-98" y="54" width="196" height="6" fill="url(#obHaz)"></rect><text x="-90" y="-20" font-family="Mitr, sans-serif" font-size="13" font-weight="600" fill="#2c3346" opacity="0.5">W-07</text>'
G['obH2']=o
# ---------- 🌋 หุบเขาไฟ ----------
o=boulder(51,86,'#4a3436',edge='#120808')
crk='M-40 -30 L-10 -6 L-20 24 M-10 -6 L30 -16 L56 6 M30 -16 L22 -50 M-20 24 L10 52'
o+=f'<path d="{crk}" stroke="#ff6a1a" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" fill="none" opacity="0.35"></path><path d="{crk}" stroke="#ffcf4a" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none"></path>'
o+='<circle cx="-10" cy="-6" r="16" fill="url(#obEmber)"></circle><circle cx="30" cy="-16" r="12" fill="url(#obEmber)"></circle>'
o+=''.join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#ffd27a"></circle>' for x,y,r in [(-70,-60,2.4),(74,-40,2),(66,62,2.6),(-80,46,2)])
G['obR3a']=o
o=f'<ellipse cx="4" cy="8" rx="78" ry="70" fill="url(#obEmber)" opacity="0.5"></ellipse>'
for i,(x,y,L,w,a) in enumerate([(-6,4,84,18,-2.1),(0,6,70,16,-0.9),(4,2,76,17,0.4),(-2,8,64,15,1.5),(2,4,58,14,2.6),(-4,6,52,13,-2.8)]):
    o+=shard(x,y,L,w,a,'#9a7ae8','#3a1e6a','#120a24')
o+='<circle cx="0" cy="5" r="16" fill="#1a0e2a" stroke="#6a4ab8" stroke-width="2"></circle>'+spk(-30,-56,.9)+spk(56,-26,.7)+spk(40,58,.6)
G['obR3b']='<g transform="scale(1.12)">'+o+'</g>'
o=f'<path d="{smooth(blob(61,15,92,.12))}" fill="#000" opacity="0.25" transform="translate(4 6)"></path><path d="{smooth(blob(61,15,92,.12))}" fill="#4a3a36" stroke="#1a1214" stroke-width="2"></path>'
o+=f'<path d="{smooth(blob(62,13,72,.14))}" fill="url(#obTar)"></path>'
for x,y,r in [(-30,-20,12),(20,-34,8),(28,18,14),(-14,30,9),(52,-6,6)]:
    o+=f'<circle cx="{x}" cy="{y}" r="{r*1.8}" fill="url(#obEmber)" opacity="0.5"></circle><circle cx="{x}" cy="{y}" r="{r}" fill="#2a1a18" stroke="#6a4a40" stroke-width="2"></circle><circle cx="{x-r*.3}" cy="{y-r*.3}" r="{r*.3}" fill="#ffffff" opacity="0.35"></circle>'
o+='<g fill="#8a7a74" opacity="0.6">'+''.join(f'<circle cx="{F(math.cos(a)*84)}" cy="{F(math.sin(a)*84)}" r="3"></circle>' for a in [k*.52 for k in range(12)])+'</g>'
G['obM3']=o
o='<rect x="-96" y="-56" width="196" height="120" rx="6" fill="#000" opacity="0.4" transform="translate(5 6)"></rect>'
o+='<rect x="-98" y="-60" width="196" height="120" rx="6" fill="url(#obSlate)" stroke="#120808" stroke-width="2.5"></rect>'
o+='<path d="M-98 0 H98" stroke="#5a2a20" stroke-width="5"></path>'
o+='<rect x="40" y="-46" width="40" height="40" rx="5" fill="#3a2a28" stroke="#120808" stroke-width="2"></rect><circle cx="60" cy="-26" r="13" fill="#120808"></circle><circle cx="60" cy="-26" r="24" fill="url(#obEmber)"></circle><circle cx="60" cy="-26" r="7" fill="#ffcf4a"></circle>'
o+='<g fill="#ff7a1a" opacity="0.85"><circle cx="40" cy="-58" r="3"></circle><circle cx="72" cy="-66" r="2.4"></circle><circle cx="84" cy="-50" r="2"></circle></g>'
o+='<g stroke="#ff6a1a" stroke-width="3" opacity="0.7" fill="none" stroke-linecap="round"><path d="M-80 30 L-60 40 L-64 54"></path><path d="M-30 -50 L-20 -36"></path></g>'
o+='<rect x="-60" y="12" width="44" height="30" rx="3" fill="#5a4a48" stroke="#120808" stroke-width="2"></rect><path d="M-56 20 H-20 M-56 30 H-20" stroke="#2a1a18" stroke-width="2"></path><circle cx="-38" cy="27" r="6" fill="url(#obEmber)"></circle>'
G['obH3']=o
# ---------- เสาไม้กั้น (ใช้ทุกโลก · ไฟแดงกะพริบเกมวาดทับ) ----------
o='<circle cx="3" cy="4" r="30" fill="#000" opacity="0.35"></circle><circle r="30" fill="#5a5f74" stroke="#2a2d3a" stroke-width="3"></circle><circle r="22" fill="#8a90a8"></circle>'
o+='<g transform="rotate(45)"><rect x="-34" y="-6" width="68" height="12" rx="3" fill="url(#obCane)" stroke="#1a1a22" stroke-width="2"></rect></g><g transform="rotate(-45)"><rect x="-34" y="-6" width="68" height="12" rx="3" fill="url(#obCane)" stroke="#1a1a22" stroke-width="2"></rect></g>'
o+='<circle r="11" fill="#1a1a22" stroke="#ffffff" stroke-width="2.5"></circle><circle r="6" fill="#552222"></circle><circle cx="-2" cy="-2" r="2" fill="#ffffff" opacity="0.5"></circle>'
G['obGate']=o

ROWS=[('🌾 ทุ่งพลอย',[('obR1a','หินพลอย','หินก้อนใหญ่ มีมอส ผลึกพลอยโผล่'),('obR1b','กองหินเล็ก','หิน 3 ก้อน ผลึกบุษราคัม/อเมทิสต์ หญ้าขึ้นรอบ'),('obH1','โรงนา','หลังคาแดงสองชั้น ขอบขาว ฟางข้าว'),('obM1','โคลน','แอ่งโคลนเปียกวาว รอยล้อ รอยเท้า หญ้ารอบขอบ')]),
      ('🏭 ย่านโกดัง',[('obR2a','กองลังไม้','ลังไม้ตอกกากบาท 4 ใบ เชือกคล้อง'),('obR2b','ถังน้ำมัน','ถัง 3 สี ป้ายเตือน คราบน้ำมัน'),('obH2','โกดัง','หลังคาสังกะสีลอน สกายไลต์ พัดลม แถบเตือน'),('obM2','คราบน้ำมัน','น้ำมันดำเงาสีรุ้ง ลื่นช้าลง')]),
      ('🌋 หุบเขาไฟ',[('obR3a','หินลาวา','หินบะซอลต์ รอยแตกเรืองแสง ถ่านไฟ'),('obR3b','ผลึกออบซิเดียน','ผลึกดำม่วงแหลม เรืองส้มที่โคน'),('obH3','โรงตีเหล็ก','หลังคาหินชนวน ปล่องไฟลุก เตาหลอม'),('obM3','บ่อน้ำมันดิน','น้ำมันดินเดือดปุด ๆ ขี้เถ้ารอบขอบ')])]
VB={'R':'-110 -110 220 220','M':'-110 -110 220 220','H':'-106 -68 212 136'}
def card(gid,name,desc):
    k=gid[2];vb=VB[k]
    return (f'<div style="background: #161b3f; border: 1.5px solid #2a3170; border-radius: 18px; padding: 14px; display: flex; flex-direction: column; gap: 8px">'
            f'<div style="font-size: 19px; font-weight: 600">{name}</div><svg viewBox="{vb}" style="width: 100%; height: 200px; display: block; border-radius: 12px; background: {{BG}}" role="img" aria-label="{name}"><use href="#{gid}"></use></svg>'
            f'<p style="margin: 0; font-size: 13.5px; line-height: 1.45; color: #cfd6ff">{desc}</p></div>')
BG=['#1f3326','#1d2232','#2a1a1a']
def gate_demo():
    return ('<div style="background: #161b3f; border: 1.5px solid #2a3170; border-radius: 18px; padding: 14px; display: flex; gap: 18px; align-items: center">'
            '<svg viewBox="-170 -60 340 120" style="width: 560px; height: 198px; border-radius: 12px; background: #1d2232" role="img" aria-label="ไม้กั้นปิด">'
            '<path d="M-115 0 H115" stroke="#ffd23f" stroke-width="5" stroke-dasharray="16 12" opacity="0.6"></path>'
            '<rect x="-115" y="-6" width="105" height="12" rx="6" fill="url(#obCane)" stroke="#1a1a22" stroke-width="2"></rect><rect x="10" y="-6" width="105" height="12" rx="6" fill="url(#obCane)" stroke="#1a1a22" stroke-width="2"></rect>'
            '<use href="#obGate" transform="translate(-125 0) scale(0.8)"></use><use href="#obGate" transform="translate(125 0) scale(0.8)"></use>'
            '<circle cx="-125" cy="0" r="16" fill="#ff2a2a" opacity="0.45"></circle><circle cx="-125" cy="0" r="5" fill="#ff2a2a"></circle><circle cx="125" cy="0" r="5" fill="#552222"></circle></svg>'
            '<div style="display: flex; flex-direction: column; gap: 6px"><div style="font-size: 20px; font-weight: 600">🚧 ไม้กั้น (ทุกโลก)</div>'
            '<p style="margin: 0; font-size: 14px; line-height: 1.5; color: #cfd6ff; max-width: 560px">เสาคอนกรีตกลม ป้ายกากบาทลายแดงขาว ไฟสัญญาณตรงกลาง · ในเกมแขนไม้กั้นยื่นออก/หดเข้าตามจังหวะ ไฟแดงกะพริบสลับ · ภาพนี้ = ตอนปิด</p></div></div>')
def build():
    groups=''.join(f'\n      <g id="{g}">{G[g]}</g>' for g in G)
    rows=''
    for i,(title,items) in enumerate(ROWS):
        rows+=f'<div style="font-size: 22px; font-weight: 600; color: #ffd23f; margin-top: 4px">{title}</div><div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px">'+''.join(card(*it).replace('{BG}',BG[i]) for it in items)+'</div>'
    html=f'''<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<title>สิ่งกีดขวางผจญภัย</title>
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
<div style="width: 1440px; height: 1660px; box-sizing: border-box; padding: 48px 64px; background: #0e1230; color: #e9ecff; font-family: Mitr, sans-serif; display: flex; flex-direction: column; gap: 14px">
  <svg width="0" height="0" style="position: absolute" aria-hidden="true">
    <defs>{DEFS}{groups}
    </defs>
  </svg>
  <div style="display: flex; flex-direction: column; gap: 6px">
    <div style="font-size: 15px; color: #ffd23f; letter-spacing: 0.08em">รถไฟซ่า · โหมดผจญภัย</div>
    <h1 style="margin: 0; font-size: 42px; font-weight: 600; line-height: 1.15">หินและสิ่งกีดขวางแบบใหม่ — 3 โลก</h1>
    <p style="margin: 0; font-size: 16px; color: #aab3e6; max-width: 1000px; line-height: 1.5">มองจากบนเหมือนในเกม · แต่ละโลกมีหิน 2 แบบ บ้าน 1 แบบ และโคลน 1 แบบ (ชน หิน/บ้าน = ตาย · โคลน = ช้าลง) · ขนาดตามวงชนเดิม</p>
  </div>
  {rows}
  {gate_demo()}
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":1440,"height":1660}}}}'>
class Component extends DCLogic {{
  renderVals() {{ return {{}}; }}
}}
</script>
</body>
</html>
'''
    OUT.write_text(html);print('wrote',OUT,len(html))
build()
