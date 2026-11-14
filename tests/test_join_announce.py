# ประกาศคนเข้าโหมด Normal/Hard ให้ทุกคนที่ออนไลน์ (14 พ.ย.) · รันเซิร์ฟเวอร์ PORT=3464 เอง
import asyncio, os, subprocess, time, sys
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));URL='http://127.0.0.1:3464'
ok=0;bad=0
def check(c,msg):
    global ok,bad
    if c: ok+=1;print('  ✓',msg)
    else: bad+=1;print('  ✗',msg)
async def main():
    srv=subprocess.Popen(['node','server.js'],cwd=ROOT,env={**os.environ,'PORT':'3464'},stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT);time.sleep(1.5)
    try:
        async with async_playwright() as p:
            bs=[]
            async def page(name):
                b=await p.chromium.launch();bs.append(b);pg=await (await b.new_context(viewport={'width':900,'height':700})).new_page()
                errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));await pg.goto(URL);await pg.wait_for_timeout(1200)
                if await pg.is_visible('#acGuest'): await pg.click('#acGuest');await pg.wait_for_timeout(300)
                await pg.fill('#name',name) if await pg.is_visible('#name') else None
                await pg.evaluate(f"try{{localStorage.setItem('wormName','{name}')}}catch(e){{}}")
                return pg,errs
            async def play(pg,k):
                await pg.click('#playInf');await pg.wait_for_timeout(300);await pg.click(f'.omode[data-k={k}]');await pg.wait_for_timeout(2500)
            A,eA=await page('เมนูเอ');await A.wait_for_timeout(800)   # อยู่หน้าแรก (presence)
            B,eB=await page('ฮาร์ดบี');await play(B,'hard')
            C,eC=await page('นอร์มอลซี');await play(C,'normal')
            await A.wait_for_timeout(600)
            t=await A.evaluate("[document.getElementById('gjTip').textContent,document.getElementById('gjTip').classList.contains('show')]")
            check('เข้าโหมด Normal' in t[0] and t[1],'หน้าแรกเห็นป้าย: '+t[0])
            f=await B.evaluate("killFeed.map(k=>k.txt)")
            check(any('เข้าโหมด Normal' in x for x in f),'คนในโลก Hard เห็นในเกม: '+str(f))
            await A.screenshot(path=os.environ.get('SHOTS','/tmp')+'/gj_menu.png')
            # Easy ไม่ประกาศ
            E,eE=await page('อีซี่อี');await A.evaluate("document.getElementById('gjTip').textContent=''");await play(E,'easy');await A.wait_for_timeout(600)
            check('Easy' not in await A.evaluate("document.getElementById('gjTip').textContent"),'เข้าโหมด Easy ไม่ประกาศ')
            # คนในโลกเดียวกับคนเข้าใหม่ ไม่ได้ gj ซ้ำ (ได้ "เข้ามาในโลกนี้แล้ว" แทน)
            D,eD=await page('ฮาร์ดดี');await B.evaluate("killFeed.length=0");await play(D,'hard');await B.wait_for_timeout(600)
            check(not any('เข้าโหมด' in x for x in await B.evaluate("killFeed.map(k=>k.txt)")),'คนโลกเดียวกันไม่ได้ป้ายซ้ำ')
            check('เข้าโหมด Hard' in await A.evaluate("document.getElementById('gjTip').textContent"),'หน้าแรกเห็นคนเข้า Hard')
            errs=eA+eB+eC+eD+eE;check(not errs,'ไม่มี error '+str(errs[:3]))
            for b in bs: await b.close()
    finally:
        srv.terminate();srv.wait()
    print(f'{ok} ผ่าน · {bad} ไม่ผ่าน');print('PASS' if not bad else 'FAIL');sys.exit(1 if bad else 0)
asyncio.run(main())
