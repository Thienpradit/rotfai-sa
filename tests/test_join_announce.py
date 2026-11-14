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
                await pg.evaluate("window.__gj=[];const o=gjShow;gjShow=m=>{__gj.push(m.name+'|'+m.d);o(m)};0")
                return pg,errs
            async def play(pg,k):
                await pg.click('#playInf');await pg.wait_for_timeout(300);await pg.click(f'.omode[data-k={k}]');await pg.wait_for_timeout(2500)
            A,eA=await page('เมนูเอ');await A.wait_for_timeout(800)   # อยู่หน้าแรก (presence)
            B,eB=await page('ฮาร์ดบี');await play(B,'hard')
            C,eC=await page('นอร์มอลซี');await play(C,'normal')
            await A.wait_for_timeout(600)
            t=await A.evaluate("[document.querySelector('#gjBig .gjn')?.textContent||'',document.getElementById('gjBig').className,__gj]")
            check('นอร์มอลซี' in t[0] and 'show' in t[1] and 'ฮาร์ดบี|hard' in t[2] and 'menu' in t[1] and 'นอร์มอลซี|normal' in t[2],'หน้าแรกเห็นแบนเนอร์ใหญ่ (ต่อคิว): '+str(t))
            await A.screenshot(path=os.environ.get('SHOTS','/tmp')+'/gj_menu.png')
            f=await B.evaluate("[__gj,document.querySelector('#gjBig .gjn')?.textContent||'',document.getElementById('gjBig').className]")
            check('นอร์มอลซี|normal' in f[0] and 'นอร์มอลซี' in f[1] and 'ingame' in f[2],'คนในโลก Hard เห็นแบนเนอร์ในเกม: '+str(f))
            await B.screenshot(path=os.environ.get('SHOTS','/tmp')+'/gj_game.png')
            # Easy ไม่ประกาศ
            E,eE=await page('อีซี่อี');await play(E,'easy');await A.wait_for_timeout(600)
            check(not any('easy' in x for x in await A.evaluate("__gj")),'เข้าโหมด Easy ไม่ประกาศ')
            # คนในโลกเดียวกับคนเข้าใหม่ ไม่ได้ gj ซ้ำ (ได้ "เข้ามาในโลกนี้แล้ว" แทน)
            D,eD=await page('ฮาร์ดดี');await play(D,'hard');await B.wait_for_timeout(600)
            check(not any('ฮาร์ดดี' in x for x in await B.evaluate("__gj")),'คนโลกเดียวกันไม่ได้ป้ายซ้ำ')
            check('ฮาร์ดดี|hard' in await A.evaluate("__gj"),'หน้าแรกเห็นคนเข้า Hard')
            await A.wait_for_timeout(4600);await A.evaluate("gjShow({name:'คิวหนึ่ง',d:'hard'});gjShow({name:'คิวสอง',d:'normal'});0");await A.wait_for_timeout(300)
            t1=await A.evaluate("document.querySelector('#gjBig .gjn')?.textContent||''");await A.wait_for_timeout(4300)
            t2=await A.evaluate("document.querySelector('#gjBig .gjn')?.textContent||''");check(t1=='คิวหนึ่ง' and t2=='คิวสอง','มาหลายคน → ต่อคิวขึ้นทีละคน '+t1+' → '+t2)
            errs=eA+eB+eC+eD+eE;check(not errs,'ไม่มี error '+str(errs[:3]))
            for b in bs: await b.close()
    finally:
        srv.terminate();srv.wait()
    print(f'{ok} ผ่าน · {bad} ไม่ผ่าน');print('PASS' if not bad else 'FAIL');sys.exit(1 if bad else 0)
asyncio.run(main())
