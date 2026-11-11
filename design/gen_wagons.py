#!/usr/bin/env python3
"""สร้างกลุ่มตู้ 4 แบบ (wgGem/wgChest/wgGiant/wgGlass) + พลอย (bg1/bg2) ใน design/Wagons.dc.html
พลอยกองพอดีล้นขอบนิดหน่อย ยังเห็นตัวตู้ · พลอยมีประกายวาว (เจ้าของสั่ง 11 พ.ย. 22:45)
รัน: python3 design/gen_wagons.py แล้ว python3 tools/gen_sprites.py"""
import re,random,math,pathlib
P=pathlib.Path(__file__).with_name('Wagons.dc.html');s=P.read_text()
COL=['gRed','gBlue','gGreen','gPurple','gYellow','gCyan','gPink']
def gem(x,y,sc,rot,col,shape,R):
    sh='bg1' if shape==0 else 'bg2'
    out=(f'<use href="#{sh}" transform="translate({x+2.2*sc:.1f} {y+3*sc:.1f}) rotate({rot}) scale({sc:.2f})" fill="#000" opacity="0.3"></use>'
         f'<use href="#{sh}" transform="translate({x:.1f} {y:.1f}) rotate({rot}) scale({sc:.2f})" fill="url(#{col})"></use>')
    if R.random()<0.3:  # ประกายบนพลอยบางเม็ด
        out+=f'<use href="#spk" transform="translate({x-4*sc:.1f} {y-5*sc:.1f}) scale({0.55*sc:.2f})"></use>'
    return out
def heap(seed,cx,cy,rx,ry,n,smin,smax,sep=0.66):
    R=random.Random(seed);pts=[];t=0
    while len(pts)<n and t<8000:
        t+=1;a=R.random()*2*math.pi;d=math.sqrt(R.random())
        x=cx+math.cos(a)*rx*d;y=cy+math.sin(a)*ry*d;sc=smin+(smax-smin)*(1-d)**0.8
        if all(math.hypot(x-q[0],y-q[1])>sep*11*(sc+q[2]) for q in pts):pts.append((x,y,sc,d))
    pts.sort(key=lambda q:-q[3])
    return ''.join(gem(x,y,sc,R.randint(-30,30),COL[R.randrange(len(COL))],R.randrange(2),R) for x,y,sc,d in pts)
def spill(seed,lst):
    R=random.Random(seed);return ''.join(gem(x,y,sc,R.randint(-40,40),COL[R.randrange(len(COL))],R.randrange(2),R) for x,y,sc in lst)
spk=lambda pts:''.join(f'<use href="#spk" transform="translate({x} {y}) scale({k})"></use>' for x,y,k in pts)
glow=lambda cx,cy,rx,ry:f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#gGlow)"></ellipse>'
DEFS=('<linearGradient id="gCyan" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e6fdff"></stop><stop offset="0.45" stop-color="#5fe0f5"></stop><stop offset="1" stop-color="#0f8fb3"></stop></linearGradient>'
 '<linearGradient id="gPink" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffe3f4"></stop><stop offset="0.45" stop-color="#ff7cc6"></stop><stop offset="1" stop-color="#c0257a"></stop></linearGradient>'
 '<radialGradient id="gGlow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#fff6d6" stop-opacity="0.35"></stop><stop offset="1" stop-color="#fff6d6" stop-opacity="0"></stop></radialGradient>'
 '<g id="spk"><path d="M0 -10 L1.8 -1.8 L10 0 L1.8 1.8 L0 10 L-1.8 1.8 L-10 0 L-1.8 -1.8 Z" fill="#ffffff"></path><circle r="2.2" fill="#ffffff"></circle></g>'
 # bg1 = กลมเจียระไน (มองจากบน) · bg2 = สี่เหลี่ยมตัดมุม · ขอบสว่าง + หน้าเหลี่ยมสะท้อนแสง + จุดวาว
 '<g id="bg1"><path d="M0 -12 L8.5 -8.5 L12 0 L8.5 8.5 L0 12 L-8.5 8.5 L-12 0 L-8.5 -8.5 Z" stroke="#ffffff" stroke-opacity="0.55" stroke-width="1"></path>'
 '<path d="M0 -5.5 L4 -4 L5.5 0 L4 4 L0 5.5 L-4 4 L-5.5 0 L-4 -4 Z" fill="#ffffff" fill-opacity="0.28"></path>'
 '<path d="M0 -12 L0 -5.5 M8.5 -8.5 L4 -4 M12 0 L5.5 0 M8.5 8.5 L4 4 M0 12 L0 5.5 M-8.5 8.5 L-4 4 M-12 0 L-5.5 0 M-8.5 -8.5 L-4 -4" stroke="#ffffff" stroke-width="0.8" stroke-opacity="0.5"></path>'
 '<path d="M-8.5 -8.5 L0 -12 L0 -5.5 L-4 -4 Z" fill="#ffffff" fill-opacity="0.45"></path><path d="M8.5 8.5 L0 12 L0 5.5 L4 4 Z" fill="#000" fill-opacity="0.18"></path>'
 '<circle cx="-3.5" cy="-6.5" r="1.6" fill="#ffffff"></circle></g>'
 '<g id="bg2"><path d="M-8 -12 L8 -12 L12 -8 L12 8 L8 12 L-8 12 L-12 8 L-12 -8 Z" stroke="#ffffff" stroke-opacity="0.55" stroke-width="1"></path>'
 '<path d="M-5 -7 L5 -7 L7 -5 L7 5 L5 7 L-5 7 L-7 5 L-7 -5 Z" fill="#ffffff" fill-opacity="0.25"></path>'
 '<path d="M-8 -12 L-5 -7 M8 -12 L5 -7 M12 8 L7 5 M-12 8 L-7 5" stroke="#ffffff" stroke-width="0.8" stroke-opacity="0.5"></path>'
 '<path d="M-8 -12 L8 -12 L5 -7 L-5 -7 Z" fill="#ffffff" fill-opacity="0.4"></path><path d="M-8 12 L8 12 L5 7 L-5 7 Z" fill="#000" fill-opacity="0.18"></path>'
 '<circle cx="-4" cy="-9" r="1.5" fill="#ffffff"></circle></g>')
# ล้างของเก่า (defs พลอย + 4 กลุ่ม) แล้วใส่ใหม่
s=re.sub(r'<linearGradient id="gCyan".*?</g><g id="bg2">.*?</g>(?=\s)','',s,flags=re.S)
for gid in ['wgGem','wgChest','wgGiant','wgGlass']:
    a=s.index(f'      <g id="{gid}">');b=s.index('</g>\n',s.index('\n',a)-1 if False else a);
    # หา </g> ที่ปิดกลุ่ม: กลุ่มเขียนเป็นบรรทัดเดียว (ใหม่) หรือหลายบรรทัด (เดิม)
    depth=0;i=a
    while True:
        m=re.compile(r'<g[ >]|</g>').search(s,i)
        if m.group()=='</g>':depth-=1
        else:depth+=1
        i=m.end()
        if depth==0:break
    e=s.index('\n',i)+1;s=s[:a]+f'@@{gid}@@\n'+s[e:]
UNDER='<use href="#under"></use>'
BODY='<rect x="-90" y="-77" width="180" height="154" rx="14" fill="url(#wBody)" stroke="{{c.dark}}" stroke-width="3"></rect><rect x="-90" y="-77" width="14" height="154" rx="6" fill="{{c.sec}}"></rect><rect x="76" y="-77" width="14" height="154" rx="6" fill="{{c.sec}}"></rect>'
RIV='<g fill="{{c.dark}}"><circle cx="-80" cy="-67" r="4"></circle><circle cx="80" cy="-67" r="4"></circle><circle cx="-80" cy="67" r="4"></circle><circle cx="80" cy="67" r="4"></circle></g>'
G={}
G['wgGem']=(UNDER+BODY+RIV+'<rect x="-70" y="-60" width="140" height="120" rx="10" fill="#14172a"></rect>'+glow(0,0,70,60)
  +heap(11,0,0,56,52,15,1.05,1.6)+spill(12,[(-36,-62,1.0),(30,63,0.95),(58,-50,0.85)])
  +spk([(-30,-30,1.2),(34,-10,1.0),(-8,26,1.1),(48,36,0.8),(-52,12,0.8)]))
c=UNDER+'<rect x="-90" y="-77" width="180" height="154" rx="12" fill="url(#wBody)" stroke="{{c.dark}}" stroke-width="3"></rect><rect x="-90" y="-77" width="180" height="12" fill="{{c.sec}}"></rect><rect x="-90" y="65" width="180" height="12" fill="{{c.sec}}"></rect>'
for cx,seed in [(-41,21),(41,22)]:
    x0=cx-37
    c+=(f'<rect x="{x0+4}" y="-53" width="74" height="116" rx="8" fill="#000" opacity="0.3"></rect><rect x="{x0}" y="-58" width="74" height="116" rx="8" fill="url(#wChest)" stroke="#3a2412" stroke-width="3"></rect>'
        f'<rect x="{x0+8}" y="-48" width="58" height="96" rx="5" fill="#1a1222"></rect>'+glow(cx,0,30,46)+heap(seed,cx,0,24,38,7,1.0,1.4)
        +f'<g fill="#e8c64a"><rect x="{x0}" y="-58" width="74" height="7" rx="3"></rect><rect x="{x0}" y="51" width="74" height="7" rx="3"></rect><rect x="{cx-4}" y="-58" width="8" height="10" rx="2"></rect><rect x="{cx-4}" y="48" width="8" height="10" rx="2"></rect></g>')
c+=spill(23,[(-30,-58,1.05),(48,-56,0.95),(20,60,1.0)])+spk([(-50,-28,1.1),(30,-30,1.0),(52,26,1.1),(-28,30,0.9)])
G['wgChest']=c
G['wgGiant']=(UNDER+BODY+'<ellipse cx="0" cy="0" rx="66" ry="60" fill="#5a1a3a"></ellipse><ellipse cx="0" cy="0" rx="66" ry="60" fill="none" stroke="#e8c64a" stroke-width="4"></ellipse>'
  +glow(0,0,70,64)+spill(31,[(-52,-34,0.95),(54,-30,0.9),(-56,30,0.9),(50,36,0.95),(-20,-56,0.8),(24,56,0.8)])
  +'<path d="M3 -50 L40 -32 L54 3 L40 38 L3 56 L-34 38 L-48 3 L-34 -32 Z" fill="#000" opacity="0.3"></path>'
  '<path d="M0 -54 L38 -36 L54 0 L38 36 L0 54 L-38 36 L-54 0 L-38 -36 Z" fill="url(#wBig)" stroke="#ffffff" stroke-opacity="0.7" stroke-width="2.5"></path>'
  '<path d="M0 -24 L21 -13 L21 13 L0 24 L-21 13 L-21 -13 Z" fill="#f2fdff" opacity="0.85" stroke="#9fd0f5" stroke-width="2"></path>'
  '<g stroke="#9fd0f5" stroke-width="2" opacity="0.8"><line x1="0" y1="-54" x2="0" y2="-24"></line><line x1="38" y1="-36" x2="21" y2="-13"></line><line x1="54" y1="0" x2="21" y2="0"></line><line x1="38" y1="36" x2="21" y2="13"></line><line x1="0" y1="54" x2="0" y2="24"></line><line x1="-38" y1="36" x2="-21" y2="13"></line><line x1="-54" y1="0" x2="-21" y2="0"></line><line x1="-38" y1="-36" x2="-21" y2="-13"></line></g>'
  '<path d="M-28 -34 L-12 -42 L-18 -24 Z" fill="#ffffff" opacity="0.9"></path>'
  '<g fill="#e8c64a" stroke="#8a6a12" stroke-width="2"><rect x="-6" y="-66" width="12" height="14" rx="3"></rect><rect x="-6" y="52" width="12" height="14" rx="3"></rect></g>'
  +spk([(-62,-50,1.3),(64,46,1.2),(30,-40,1.0),(-36,36,0.9),(8,-8,0.9)]))
G['wgGlass']=(UNDER+'<rect x="-90" y="-77" width="180" height="154" rx="16" fill="#1c2140" stroke="{{c.dark}}" stroke-width="3"></rect>'
  +glow(0,0,70,60)+heap(41,0,4,62,50,13,1.0,1.35)
  +'<rect x="-80" y="-67" width="160" height="134" rx="12" fill="url(#wGlass)" stroke="#d9ecff" stroke-width="2" stroke-opacity="0.6"></rect>'
  '<rect x="-90" y="-77" width="180" height="154" rx="16" fill="none" stroke="{{c.main}}" stroke-width="10"></rect>'
  '<g stroke="{{c.sec}}" stroke-width="5"><line x1="-27" y1="-70" x2="-27" y2="70"></line><line x1="27" y1="-70" x2="27" y2="70"></line></g>'
  +spill(43,[(-6,-70,1.0),(14,-74,0.85),(-60,72,0.9)])
  +'<path d="M-66 -56 L-40 -56 M-66 -46 L-56 -46" stroke="#ffffff" stroke-width="4" stroke-linecap="round" opacity="0.75"></path>'
  +spk([(-40,-20,1.1),(30,30,1.2),(60,-40,0.9),(0,8,0.8)]))
first=True
for gid,body in G.items():
    s=s.replace(f'@@{gid}@@\n',(DEFS if first else '')+f'      <g id="{gid}">'+body+'</g>\n');first=False
s=s.replace('ตู้ขนเพชรพลอย 4 แบบ — พลอยล้นตู้','ตู้ขนเพชรพลอย 4 แบบ — พลอยวาวล้นนิด ๆ')
s=re.sub(r'พลอยเม็ดใหญ่ 2 ทรง[^·]*·','พลอยเม็ดใหญ่ 2 ทรง (กลมเจียระไน/สี่เหลี่ยมตัดมุม) 7 สี เปล่งประกาย กองพอดีล้นขอบนิดหน่อย ยังเห็นตัวตู้ ·',s)
for a,b in [('ตู้เปิดหลังคา พลอยเม็ดโตกองพูนจนล้นขอบตู้ทั้งสองข้าง','ตู้เปิดหลังคา พลอยเม็ดโตวาววับ กองพอดีล้นขอบนิดหน่อย'),
            ('หีบสมบัติ 2 ใบ พลอยล้นปากหีบจนร่วงออกมาที่ขอบตู้','หีบสมบัติ 2 ใบ พลอยเต็มหีบ ร่วงออกมาบนตู้ 2–3 เม็ด'),
            ('เพชรยักษ์ใหญ่ขึ้น วางบนกองพลอยที่ล้นรอบแท่น','เพชรยักษ์บนแท่นกำมะหยี่ มีพลอยเม็ดเล็กวางรอบ เปล่งประกาย'),
            ('พลอยอัดแน่นในตู้กระจก แล้วยังกองล้นบนหลังคา','พลอยเต็มตู้กระจก มีบางเม็ดวางบนหลังคา')]:
    s=s.replace(a,b)
P.write_text(s);print('ok',len(s))
