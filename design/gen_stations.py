#!/usr/bin/env python3
"""สร้าง design/Stations.dc.html — สถานีส่งพลอย 4 แบบ (มองจากบน แบบเดียวกับในเกม)
st1 ทับทิม (สถานีไม้หลังคาแดงทรงไทย) · st2 มรกต (โดมกระจกเรือนต้นไม้) · st3 ไพลิน (หลังคาคลื่นทันสมัย) · st4 บุษราคัม (ลานขนแร่ มีกรวย+สายพาน)
พิกัดกลุ่ม: x -130..130, y -75..75 · +y = ด้านที่หันเข้ากลางสนาม (ขอบชานชาลาเส้นเหลือง) · ป้ายชื่อวางที่ (0,4) ในเกมเขียนตัวหนังสือทับ
รัน: python3 design/gen_stations.py  (เจ้าของสั่ง 12 พ.ย. 00:57 "ใช้ Claude design ทำสถานีใหม่ให้สวยสิ")"""
import math,random,pathlib
OUT=pathlib.Path(__file__).with_name('Stations.dc.html')
F=lambda v:f'{v:.1f}'.rstrip('0').rstrip('.')

GEMC={'ruby':('#ffe0e6','#ff4d6d','#9e1030'),'emer':('#dcfff0','#2ee59d','#0b7a4f'),'sapp':('#e2ecff','#4d8dff','#14307e'),
      'topa':('#fff4d0','#ffb627','#a35a00'),'ame':('#f2e2ff','#b26bff','#5a1a9e'),'dia':('#ffffff','#bfefff','#5aa8c8')}
def defs():
    o=[]
    for k,(a,b,c) in GEMC.items():
        o.append(f'<linearGradient id="sg_{k}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a}"></stop><stop offset="0.45" stop-color="{b}"></stop><stop offset="1" stop-color="{c}"></stop></linearGradient>')
    o+=['<linearGradient id="sConc" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a7adc4"></stop><stop offset="1" stop-color="#7b8199"></stop></linearGradient>',
        '<linearGradient id="sRoofR1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7a1f2a"></stop><stop offset="1" stop-color="#b8343f"></stop></linearGradient>',
        '<linearGradient id="sRoofR2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ef5a5f"></stop><stop offset="1" stop-color="#c33a44"></stop></linearGradient>',
        '<linearGradient id="sGoldH" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#9a6d08"></stop><stop offset="0.3" stop-color="#fff1a8"></stop><stop offset="0.6" stop-color="#ffd23f"></stop><stop offset="1" stop-color="#8a5f06"></stop></linearGradient>',
        '<linearGradient id="sGoldV" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff1a8"></stop><stop offset="0.5" stop-color="#e8b12c"></stop><stop offset="1" stop-color="#8a5f06"></stop></linearGradient>',
        '<linearGradient id="sGlass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#c9fff0" stop-opacity="0.85"></stop><stop offset="0.5" stop-color="#4fd6a8" stop-opacity="0.6"></stop><stop offset="1" stop-color="#0d6a55" stop-opacity="0.85"></stop></linearGradient>',
        '<linearGradient id="sBlueRoof" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a4fae"></stop><stop offset="0.55" stop-color="#4d8dff"></stop><stop offset="1" stop-color="#9cc2ff"></stop></linearGradient>',
        '<linearGradient id="sCorr" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#c97a12"></stop><stop offset="0.5" stop-color="#ffc24a"></stop><stop offset="1" stop-color="#c97a12"></stop></linearGradient>',
        '<linearGradient id="sWood" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c98a4b"></stop><stop offset="1" stop-color="#7a4a22"></stop></linearGradient>',
        '<radialGradient id="sLamp" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#fff6c2" stop-opacity="0.9"></stop><stop offset="0.35" stop-color="#ffd23f" stop-opacity="0.35"></stop><stop offset="1" stop-color="#ffd23f" stop-opacity="0"></stop></radialGradient>',
        '<radialGradient id="sHalo" cx="0.5" cy="0.5" r="0.5"><stop offset="0.55" stop-color="#ffd23f" stop-opacity="0.55"></stop><stop offset="1" stop-color="#ffd23f" stop-opacity="0"></stop></radialGradient>',
        '<pattern id="sTac" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="#ffd23f"></rect><circle cx="3" cy="3" r="1.3" fill="#c99a12"></circle></pattern>',
        '<pattern id="sHaz" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="12" height="12" fill="#ffd23f"></rect><rect width="6" height="12" fill="#1a1a22"></rect></pattern>',
        '<g id="sSpk"><path d="M0 -10 L1.8 -1.8 L10 0 L1.8 1.8 L0 10 L-1.8 1.8 L-10 0 L-1.8 -1.8 Z" fill="#ffffff"></path><circle r="2.2" fill="#ffffff"></circle></g>',
        '<g id="sGem"><path d="M0 -12 L8.5 -8.5 L12 0 L8.5 8.5 L0 12 L-8.5 8.5 L-12 0 L-8.5 -8.5 Z" stroke="#ffffff" stroke-opacity="0.6" stroke-width="1"></path>'
        '<path d="M0 -5.5 L4 -4 L5.5 0 L4 4 L0 5.5 L-4 4 L-5.5 0 L-4 -4 Z" fill="#ffffff" fill-opacity="0.3"></path>'
        '<path d="M-8.5 -8.5 L0 -12 L0 -5.5 L-4 -4 Z" fill="#ffffff" fill-opacity="0.45"></path><path d="M8.5 8.5 L0 12 L0 5.5 L4 4 Z" fill="#000" fill-opacity="0.2"></path>'
        '<circle cx="-3.5" cy="-6.5" r="1.6" fill="#ffffff"></circle></g>']
    return ''.join(o)

def gem(x,y,s,k,rot=0): return (f'<use href="#sGem" transform="translate({F(x+1.6*s)} {F(y+2.2*s)}) rotate({rot}) scale({F(s)})" fill="#000" opacity="0.3"></use>'
                               f'<use href="#sGem" transform="translate({F(x)} {F(y)}) rotate({rot}) scale({F(s)})" fill="url(#sg_{k})"></use>')
def pile(seed,cx,cy,rx,ry,n,kinds,smin=.42,smax=.62):
    R=random.Random(seed);pts=[];t=0
    while len(pts)<n and t<5000:
        t+=1;a=R.random()*6.283;d=math.sqrt(R.random());x=cx+math.cos(a)*rx*d;y=cy+math.sin(a)*ry*d;s=smin+(smax-smin)*(1-d)
        if all(math.hypot(x-q[0],y-q[1])>10*(s+q[2]) for q in pts):pts.append((x,y,s,d))
    pts.sort(key=lambda q:-q[3]);return ''.join(gem(x,y,s,kinds[R.randrange(len(kinds))],R.randint(-25,25)) for x,y,s,d in pts)
spk=lambda x,y,k=.5:f'<use href="#sSpk" transform="translate({F(x)} {F(y)}) scale({F(k)})"></use>'
def crate(x,y,k,seed,w=26,h=20):
    return (f'<rect x="{F(x-w/2+2)}" y="{F(y-h/2+3)}" width="{w}" height="{h}" rx="3" fill="#000" opacity="0.3"></rect>'
            f'<rect x="{F(x-w/2)}" y="{F(y-h/2)}" width="{w}" height="{h}" rx="3" fill="url(#sWood)" stroke="#4a2c12" stroke-width="1.5"></rect>'
            f'<rect x="{F(x-w/2+3)}" y="{F(y-h/2+3)}" width="{w-6}" height="{h-6}" rx="2" fill="#2a1a0e"></rect>'
            +pile(seed,x,y,w/2-6,h/2-6,4,[k],.32,.42))
def lamp(x,y): return (f'<circle cx="{F(x)}" cy="{F(y)}" r="16" fill="url(#sLamp)"></circle><circle cx="{F(x)}" cy="{F(y)}" r="4.2" fill="#2b2f44" stroke="#11131f" stroke-width="1.2"></circle>'
                       f'<circle cx="{F(x)}" cy="{F(y)}" r="2.4" fill="#fff6c2"></circle>')
def bench(x,y,w=22): return (f'<rect x="{F(x-w/2+1.5)}" y="{F(y-3+2)}" width="{w}" height="6" rx="2" fill="#000" opacity="0.3"></rect>'
                             f'<rect x="{F(x-w/2)}" y="{F(y-3)}" width="{w}" height="6" rx="2" fill="#a8663a" stroke="#5a3418" stroke-width="1"></rect>'
                             f'<path d="M{F(x-w/2+2)} {F(y)} H{F(x+w/2-2)}" stroke="#5a3418" stroke-width="0.8"></path>')
def platform(x0=-126,x1=126,y0=14,y1=60):
    o=f'<rect x="{x0+3}" y="{y0+5}" width="{x1-x0}" height="{y1-y0}" rx="6" fill="#000" opacity="0.35"></rect>'
    o+=f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" rx="6" fill="url(#sConc)" stroke="#4e5268" stroke-width="2"></rect>'
    o+='<g stroke="#ffffff" stroke-opacity="0.13" stroke-width="1">'+''.join(f'<path d="M{x} {y0+2} V{y1-9}"></path>' for x in range(x0+18,x1,18))+f'<path d="M{x0+2} {(y0+y1)/2-3} H{x1-2}"></path></g>'
    o+=f'<rect x="{x0+4}" y="{y1-9}" width="{x1-x0-8}" height="5" rx="2" fill="url(#sTac)"></rect><path d="M{x0+4} {y1-2} H{x1-4}" stroke="#ffffff" stroke-width="1.6" stroke-dasharray="8 6" opacity="0.7"></path>'
    return o
def sign(fill,stroke,text_col='#3a1a10'):   # ป้ายเปล่า ตำแหน่งที่เกมเขียนชื่อทับ
    return (f'<rect x="-50" y="-6" width="100" height="20" rx="6" fill="#000" opacity="0.35" transform="translate(1.5 2.5)"></rect>'
            f'<rect x="-50" y="-6" width="100" height="20" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="2.2"></rect>'
            f'<rect x="-46" y="-3" width="92" height="3" rx="1.5" fill="#ffffff" opacity="0.35"></rect>')

# ---------- 1) ทับทิม: สถานีไม้หลังคาแดงทรงไทย ----------
def st_ruby():
    o=platform()
    o+='<rect x="-104" y="-52" width="214" height="80" rx="4" fill="#000" opacity="0.35"></rect>'
    o+='<rect x="-96" y="-46" width="192" height="66" fill="#f1e2c0" stroke="#8a6a3a" stroke-width="1.5"></rect>'
    up='M-110 -62 L110 -62 L100 -18 L-100 -18 Z';lo='M-100 -18 L100 -18 L112 22 L-112 22 Z'
    o+=f'<path d="{up}" fill="url(#sRoofR1)" stroke="#5a121a" stroke-width="2"></path><path d="{lo}" fill="url(#sRoofR2)" stroke="#5a121a" stroke-width="2"></path>'
    tl='<g stroke="#5a121a" stroke-width="1" opacity="0.55">'
    for i in range(1,6):
        y=-62+i*44/6;x=110-(i*10/6);tl+=f'<path d="M{F(-x)} {F(y)} H{F(x)}"></path>'
    for i in range(1,6):
        y=-18+i*40/6;x=100+(i*12/6);tl+=f'<path d="M{F(-x)} {F(y)} H{F(x)}"></path>'
    tl+='</g><g stroke="#ff9aa0" stroke-width="1" opacity="0.35">'+''.join(f'<path d="M{x} -16 V20"></path>' for x in range(-96,100,12))+'</g>'
    o+=tl
    o+='<rect x="-104" y="-21" width="208" height="6" rx="3" fill="url(#sGoldH)" stroke="#6a4a06" stroke-width="1"></rect>'
    o+='<path d="M-112 22 H112" stroke="url(#sGoldH)" stroke-width="3.5" stroke-linecap="round"></path>'
    for sx in (-1,1):   # ปลายจั่วทอง (ลวดลายโค้งเรียบ ๆ)
        o+=f'<path d="M{sx*104} -18 q{sx*12} -6 {sx*14} -18 q{sx*-2} 8 {sx*-6} 12 q{sx*8} 2 {sx*12} 10 q{sx*-8} -2 {sx*-20} -4 Z" fill="url(#sGoldV)" stroke="#6a4a06" stroke-width="1.2"></path>'
    o+='<circle cx="0" cy="-40" r="11" fill="#f6efe0" stroke="url(#sGoldH)" stroke-width="3"></circle><path d="M0 -40 V-47 M0 -40 L5 -37" stroke="#3a2a1a" stroke-width="1.6" stroke-linecap="round"></path>'
    o+=''.join(f'<rect x="{x-3}" y="22" width="6" height="7" rx="1.5" fill="#6b3a1c"></rect>' for x in (-90,-45,45,90))
    o+=lamp(-112,36)+lamp(112,36)+bench(-62,34)+bench(62,34)
    o+=crate(-28,38,'ruby',3)+crate(28,40,'ruby',4,22,18)
    o+=f'<g transform="translate(0 4)">{sign("#fff4dc","#b8343f")}</g>'
    o+=spk(-30,30,.45)+spk(30,33,.4)
    return o

# ---------- 2) มรกต: โดมกระจกเรือนต้นไม้ ----------
def st_emer():
    o=platform()
    o+='<rect x="-102" y="-60" width="208" height="84" rx="38" fill="#000" opacity="0.35"></rect>'
    o+='<rect x="-100" y="-64" width="200" height="84" rx="38" fill="#0e3a33"></rect>'
    o+=pile(21,-30,-26,40,22,10,['emer','emer','dia'],.5,.72)+pile(22,40,-24,30,18,7,['emer','emer','topa'],.45,.6)
    o+='<rect x="-100" y="-64" width="200" height="84" rx="38" fill="url(#sGlass)" stroke="#e8fff6" stroke-width="3"></rect>'
    o+='<g stroke="#e8fff6" stroke-width="1.6" opacity="0.8" fill="none">'+''.join(f'<path d="M{x} -63 Q{x+x*0.08} -22 {x} 19"></path>' for x in range(-75,80,25))
    o+='<path d="M-96 -40 Q0 -54 96 -40"></path><path d="M-99 -14 Q0 -26 99 -14"></path><path d="M-96 8 Q0 -2 96 8"></path></g>'
    o+='<rect x="-14" y="-70" width="28" height="12" rx="6" fill="url(#sGoldV)" stroke="#6a4a06" stroke-width="1.4"></rect><circle cx="0" cy="-72" r="5" fill="url(#sg_emer)" stroke="#ffffff" stroke-width="1"></circle>'
    o+='<path d="M-80 -54 Q-58 -60 -36 -54 L-60 6 Q-76 -10 -80 -54 Z" fill="#ffffff" opacity="0.22"></path><path d="M30 -60 L46 -60 L22 14 L8 14 Z" fill="#ffffff" opacity="0.12"></path>'
    for x,y,r in ((-116,-30,13),(-118,-6,10),(116,-28,13),(118,-4,10),(-108,-56,9),(110,-56,9)):   # ต้นไม้รอบโดม
        o+=f'<circle cx="{x+2}" cy="{y+3}" r="{r}" fill="#000" opacity="0.3"></circle><circle cx="{x}" cy="{y}" r="{r}" fill="#2f9e5a"></circle><circle cx="{x-r*.3}" cy="{y-r*.3}" r="{r*.55}" fill="#5fd38a"></circle>'
        o+=f'<circle cx="{x+r*.35}" cy="{y-r*.1}" r="1.6" fill="#ff7cc6"></circle>'
    o+=lamp(-112,36)+lamp(112,36)+bench(-70,34)+bench(70,34)+crate(-30,38,'emer',5)+crate(30,38,'emer',6)
    o+=f'<g transform="translate(0 4)">{sign("#eafff5","#1f9e6e")}</g>'+spk(-40,-34,.6)+spk(52,-20,.5)+spk(-6,-10,.4)
    return o

# ---------- 3) ไพลิน: หลังคาคลื่นทันสมัย ----------
def st_sapp():
    o=platform()
    o+='<rect x="-70" y="-62" width="140" height="56" rx="6" fill="#0b1433" stroke="#2c3e7a" stroke-width="2"></rect>'
    o+='<g fill="#9cc2ff" opacity="0.55">'+''.join(f'<rect x="{x}" y="{y}" width="14" height="9" rx="1.5"></rect>' for x in range(-62,62,20) for y in (-56,-42,-28))+'</g>'
    wave='M-118 -40 C-96 -58 -74 -58 -52 -40 C-30 -22 -8 -22 14 -40 C36 -58 58 -58 80 -40 C96 -28 108 -26 118 -32 L118 18 L-118 18 Z'
    o+=f'<path d="{wave}" fill="#000" opacity="0.35" transform="translate(3 5)"></path><path d="{wave}" fill="url(#sBlueRoof)" stroke="#0d1838" stroke-width="2.2" opacity="0.96"></path>'
    o+='<g stroke="#ffffff" stroke-width="1.3" opacity="0.4">'+''.join(f'<path d="M{x} -30 V16"></path>' for x in range(-108,118,18))+'</g>'
    o+='<path d="M-118 -40 C-96 -58 -74 -58 -52 -40 C-30 -22 -8 -22 14 -40 C36 -58 58 -58 80 -40 C96 -28 108 -26 118 -32" fill="none" stroke="#e6f1ff" stroke-width="3" opacity="0.8"></path>'
    o+='<path d="M-118 17 H118" stroke="#5ff6ff" stroke-width="3.2" stroke-linecap="round"></path><path d="M-118 17 H118" stroke="#5ff6ff" stroke-width="9" stroke-linecap="round" opacity="0.18"></path>'
    o+=''.join(f'<circle cx="{x}" cy="26" r="4" fill="#c4cbe0" stroke="#4e5268" stroke-width="1.4"></circle>' for x in (-96,-48,48,96))
    o+=lamp(-118,40)+lamp(118,40)+bench(-72,40,18)+bench(72,40,18)+crate(-24,40,'sapp',7,24,18)+crate(24,40,'sapp',8,24,18)
    o+=f'<g transform="translate(0 2)">{sign("#eef4ff","#2a5bd7")}</g>'+spk(-24,32,.4)+spk(26,34,.42)
    o+=gem(98,-2,.55,'sapp',10)+gem(-98,-2,.55,'sapp',-10)
    return o

# ---------- 4) บุษราคัม: ลานขนแร่ กรวย + สายพาน ----------
def st_topa():
    o=platform()
    o+='<rect x="-112" y="-58" width="132" height="76" rx="4" fill="#000" opacity="0.35"></rect>'
    o+='<rect x="-116" y="-62" width="132" height="76" rx="4" fill="url(#sCorr)" stroke="#6a3a06" stroke-width="2"></rect>'
    o+='<g stroke="#8a4a06" stroke-width="1.3" opacity="0.6">'+''.join(f'<path d="M{x} -61 V13"></path>' for x in range(-110,16,7))+'</g>'
    o+='<path d="M-116 -26 H16" stroke="#8a4a06" stroke-width="2.5"></path><rect x="-116" y="-62" width="132" height="5" fill="#ffe7a0" opacity="0.5"></rect>'
    hx,hy=66,-24   # กรวยใส่แร่
    o+=f'<rect x="{hx-36}" y="{hy-36}" width="76" height="76" rx="6" fill="#000" opacity="0.35"></rect>'
    o+=f'<rect x="{hx-40}" y="{hy-40}" width="80" height="80" rx="6" fill="#5a5f74" stroke="#1d2030" stroke-width="2"></rect>'
    o+=f'<path d="M{hx-36} {hy-36} L{hx+36} {hy-36} L{hx+14} {hy-14} L{hx-14} {hy-14} Z" fill="#8b91a8"></path><path d="M{hx-36} {hy+36} L{hx+36} {hy+36} L{hx+14} {hy+14} L{hx-14} {hy+14} Z" fill="#40445a"></path>'
    o+=f'<path d="M{hx-36} {hy-36} L{hx-14} {hy-14} L{hx-14} {hy+14} L{hx-36} {hy+36} Z" fill="#6c7189"></path><path d="M{hx+36} {hy-36} L{hx+14} {hy-14} L{hx+14} {hy+14} L{hx+36} {hy+36} Z" fill="#4c5068"></path>'
    o+=pile(31,hx,hy,26,26,12,['topa','topa','topa','ruby','dia'],.48,.68)
    o+=f'<rect x="{hx-40}" y="{hy-40}" width="80" height="80" rx="6" fill="none" stroke="url(#sHaz)" stroke-width="5"></rect>'
    o+=f'<rect x="{hx-9}" y="{hy+40}" width="18" height="34" fill="#22252f" stroke="#11131a" stroke-width="1.4"></rect>'   # สายพานลงชานชาลา
    o+=''.join(f'<path d="M{hx-9} {hy+44+i*6} H{hx+9}" stroke="#3c4152" stroke-width="1.6"></path>' for i in range(5))
    o+=gem(hx,hy+52,.42,'topa',15)+gem(hx-1,hy+66,.38,'topa',-20)
    o+='<path d="M-30 -40 L30 -12" stroke="#ffd23f" stroke-width="6" stroke-linecap="round"></path><path d="M-30 -40 L30 -12" stroke="#1a1a22" stroke-width="6" stroke-dasharray="5 5" stroke-linecap="round" opacity="0.7"></path>'   # แขนเครน
    o+='<circle cx="-30" cy="-40" r="8" fill="#4c5068" stroke="#1d2030" stroke-width="2"></circle><circle cx="30" cy="-12" r="4" fill="#1d2030"></circle><path d="M30 -12 v10" stroke="#1d2030" stroke-width="1.5"></path>'
    o+=lamp(-118,36)+lamp(118,36)+crate(-80,38,'topa',9)+crate(-50,38,'topa',10,22,18)+bench(20,34,20)
    o+=f'<g transform="translate(-40 4)">{sign("#fff3d0","#c97a12")}</g>'
    o+='<rect x="-126" y="56" width="252" height="4" fill="url(#sHaz)" opacity="0.9"></rect>'+spk(58,-34,.6)+spk(76,-12,.45)
    return o

ST=[('stRuby','สถานีทับทิม','สถานีไม้หลังคาแดงสองชั้นทรงไทย สันหลังคาทอง ปลายจั่วทอง นาฬิกากลางหลังคา ลังทับทิมบนชานชาลา',st_ruby),
    ('stEmer','สถานีมรกต','โดมกระจกเรือนต้นไม้ ข้างในมองเห็นกองมรกตเปล่งประกาย รอบโดมมีพุ่มไม้ดอกไม้',st_emer),
    ('stSapp','สถานีไพลิน','หลังคาคลื่นสีน้ำเงินแบบทันสมัย ไฟ LED ฟ้าตามชายคา เสาเหล็ก อาคารกระจก',st_sapp),
    ('stTopa','สถานีบุษราคัม','ลานขนแร่ หลังคาสังกะสีทอง กรวยเหล็กเต็มบุษราคัม สายพานลำเลียงลงชานชาลา แขนเครน แถบเตือนเหลืองดำ',st_topa)]

VB='-135 -82 270 160'
def card(gid,name,desc):
    return (f'<div style="background:#151a42;border:1px solid #2c3366;border-radius:18px;padding:18px 20px 16px;display:flex;flex-direction:column;gap:10px">'
            f'<svg viewBox="{VB}" width="608" height="330" style="background:radial-gradient(ellipse at center,#1d2350,#0c1027);border-radius:12px"><use href="#{gid}"></use></svg>'
            f'<div style="font-size:22px;font-weight:600;color:#ffd23f">{name}</div><p style="margin:0;font-size:14px;color:#cfd6ff;line-height:1.5">{desc}</p></div>')
def state_demo():
    # ขนาดในเกม (สถานีกว้าง ~180px) · พร้อมส่ง (เรืองทอง) / รอ (จาง + เวลา)
    s=(f'<svg viewBox="0 0 1312 250" width="1312" height="250" style="background:#0c1027;border-radius:14px">'
       '<g stroke="#ffffff" stroke-opacity="0.05">'+''.join(f'<path d="M{x} 0 V250"></path>' for x in range(0,1312,40))+''.join(f'<path d="M0 {y} H1312"></path>' for y in range(0,250,40))+'</g>'
       '<g transform="translate(330 128)"><ellipse rx="170" ry="96" fill="url(#sHalo)"><animate attributeName="opacity" values="0.55;1;0.55" dur="1.6s" repeatCount="indefinite"></animate></ellipse>'
       '<use href="#stRuby"></use><text x="0" y="9" text-anchor="middle" font-family="Mitr, sans-serif" font-size="12" font-weight="600" fill="#5a121a">🚉 สถานีส่งพลอย</text></g>'
       '<g transform="translate(980 128)" opacity="0.55" style="filter:grayscale(0.85)"><use href="#stSapp"></use></g>'
       '<g transform="translate(980 128)"><rect x="-50" y="-4" width="100" height="20" rx="6" fill="#1b2150" stroke="#8a93c8" stroke-width="2"></rect><text x="0" y="11" text-anchor="middle" font-family="Mitr, sans-serif" font-size="12" font-weight="600" fill="#e9ecff">⏳ รอ 18 วิ</text></g>'
       '<text x="330" y="236" text-anchor="middle" font-family="Mitr, sans-serif" font-size="16" fill="#ffd23f">พร้อมส่งพลอย — เรืองทองเต้นเป็นจังหวะ</text>'
       '<text x="980" y="236" text-anchor="middle" font-family="Mitr, sans-serif" font-size="16" fill="#aab3e6">เพิ่งส่งไป — สีจางลง ป้ายบอกเวลารอ</text></svg>')
    return s

def build():
    groups=''.join(f'\n      <g id="{gid}">{fn()}</g>' for gid,_,_,fn in ST)
    cards=''.join(card(g,n,d) for g,n,d,_ in ST)
    html=f'''<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<title>สถานีส่งพลอย</title>
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
<div style="width: 1440px; height: 1400px; box-sizing: border-box; padding: 48px 64px; background: #0e1230; color: #e9ecff; font-family: Mitr, sans-serif; display: flex; flex-direction: column; gap: 22px">
  <svg width="0" height="0" style="position: absolute" aria-hidden="true">
    <defs>{defs()}{groups}
    </defs>
  </svg>
  <div><div style="font-size: 34px; font-weight: 600">🚉 สถานีส่งพลอย 4 แบบ</div><div style="font-size: 16px; color: #aab3e6; margin-top: 4px">มองจากบนแบบเดียวกับในเกม · 4 สถานีในสนามได้คนละแบบ · ขอบชานชาลาเส้นเหลืองหันเข้ากลางสนาม · ป้ายตรงกลางเกมเขียนชื่อ/เวลารอทับ</div></div>
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 22px">{cards}</div>
  {state_demo()}
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":1440,"height":1400}}}}'>
class Component extends DCLogic {{
  renderVals() {{ return {{}}; }}
}}
</script>
</body>
</html>
'''
    OUT.write_text(html);print('wrote',OUT,len(html))
build()
