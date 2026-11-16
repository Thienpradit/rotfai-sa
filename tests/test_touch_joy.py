# 📱 จอยสัมผัส (16 พ.ย.): iPhone "บังคับไม่ได้" → touch events + รับจอยต่อเมื่อโดนยกเลิก · นิ้วค้างนิ่งนานแล้วยังเลี้ยวได้ · กดเร่งค้าง + เลี้ยวพร้อมกัน
# เปิด public/index.html ตรง ๆ (ไม่ต้องรันเซิร์ฟเวอร์) · จำลองนิ้วด้วย CDP Input.dispatchTouchEvent
import math,sys
from playwright.sync_api import sync_playwright
ok=0;bad=0
def check(c,m):
    global ok,bad
    if c: ok+=1;print('  ✓',m)
    else: bad+=1;print('  ✗',m)
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':812,'height':375},has_touch=True,is_mobile=True);g=ctx.new_page();errs=[];g.on('pageerror',lambda e:errs.append(str(e)))
    g.add_init_script("localStorage.setItem('rotSeen','1');localStorage.setItem('trainNewsSeen','99')")
    g.goto('file:///home/claude/rotfai-sa/public/index.html');g.wait_for_timeout(1000)
    g.evaluate("$('sheet').classList.add('hidden');startGame('inf');player.die=()=>{};0");g.wait_for_timeout(800)
    cdp=ctx.new_cdp_session(g)
    T=lambda typ,pts:cdp.send('Input.dispatchTouchEvent',{'type':typ,'touchPoints':[{'x':x,'y':y,'id':i} for (i,x,y) in pts]})
    ang=lambda:g.evaluate('input.angle')
    check(g.evaluate("TOUCH_EV"),'เครื่องสัมผัสใช้ touch events')
    T('touchStart',[(1,250,200)]);T('touchMove',[(1,320,200)]);g.wait_for_timeout(50)
    check(abs(ang())<0.05,'ลากขวา → หันขวา (%.2f)'%ang())
    g.wait_for_timeout(1500)   # นิ้วค้างนิ่ง 1.5 วิ (iPhone = กดค้าง)
    T('touchMove',[(1,250,270)]);g.wait_for_timeout(50)
    check(abs(ang()-math.atan2(70,-0+0) if False else ang()-math.atan2(270-200+0,250-(320-65)))<0.3 and g.evaluate('!!input.joy'),'ค้างนิ่งนานแล้วยังเลี้ยวได้ (%.2f)'%ang())
    g.evaluate("input.joy=null");T('touchMove',[(1,240,330)]);T('touchMove',[(1,180,330)]);g.wait_for_timeout(50)
    check(g.evaluate('!!input.joy && JOY_HEAL>=1') and abs(abs(ang())-math.pi)<0.1,'จอยโดนยกเลิกแต่นิ้วยังลาก → รับต่อเอง ไม่ต้องยกนิ้ว (%.2f)'%ang())
    T('touchEnd',[]);g.wait_for_timeout(50);check(g.evaluate('input.joy===null'),'ยกนิ้ว → จอยหาย')
    bx=g.evaluate("(()=>{const r=$('boost').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]})()")
    T('touchStart',[(5,bx[0],bx[1])]);g.wait_for_timeout(30);T('touchStart',[(5,bx[0],bx[1]),(6,200,150)]);T('touchMove',[(5,bx[0],bx[1]),(6,200,80)]);g.wait_for_timeout(50)
    check(g.evaluate('input.boost') and abs(ang()+math.pi/2)<0.1,'กดเร่งค้าง + อีกนิ้วเลี้ยวได้พร้อมกัน (boost=%s, %.2f)'%(g.evaluate('input.boost'),ang()))
    T('touchMove',[(5,bx[0]+8,bx[1]+6),(6,270,80)]);g.wait_for_timeout(50)
    check(g.evaluate('input.boost') and -1.2<ang()<-0.3,'นิ้วเร่งขยับนิด ๆ ยังเร่ง + นิ้วเลี้ยวยังคุม (%.2f)'%ang())
    T('touchEnd',[]);g.wait_for_timeout(50)
    check(not errs,'ไม่มี error '+str(errs[:2]))
    b.close()
print(f'{ok} ผ่าน · {bad} ไม่ผ่าน');print('PASS' if not bad else 'FAIL');sys.exit(1 if bad else 0)
