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
            check(await A.evaluate("__gj.length")==0,'หน้าแรกไม่ได้รับประกาศ')
            check(not any('นอร์มอลซี' in x for x in await B.evaluate("__gj")),'คนเล่น Hard ไม่เห็นคนเข้า Normal')
            D,eD=await page('ฮาร์ดดี');await play(D,'hard');await B.wait_for_timeout(700)
            f=await B.evaluate("[__gj,document.querySelector('#gjBig .gjn')?.textContent||'',document.getElementById('gjBig').className,state,NET&&NET.diff,NET&&NET.ffa]")
            check('ฮาร์ดดี|hard' in f[0] and 'ฮาร์ดดี' in f[1] and 'ingame' in f[2],'คนเล่น Hard เห็นป้ายคนเข้า Hard: '+str(f))
            await B.screenshot(path=os.environ.get('SHOTS','/tmp')+'/gj_game.png')
            check(not any('ฮาร์ดดี' in x for x in await C.evaluate("__gj")),'คนเล่น Normal ไม่เห็นคนเข้า Hard')
            F,eF=await page('นอร์มอลเอฟ');await play(F,'normal');await C.wait_for_timeout(700)
            check('นอร์มอลเอฟ' in await C.evaluate("document.querySelector('#gjBig .gjn')?.textContent||''"),'คนเล่น Normal เห็นป้ายคนเข้า Normal')
            E,eE=await page('อีซี่อี');await play(E,'easy');await B.wait_for_timeout(600)
            check(not any('easy' in x for x in await B.evaluate("__gj")+await C.evaluate("__gj")),'เข้าโหมด Easy ไม่ประกาศ')
            check(await A.evaluate("__gj.length")==0,'หน้าแรกยังไม่ได้รับอะไรเลย')
            await B.wait_for_timeout(4200);await B.evaluate("gjShow({name:'คิวหนึ่ง',d:'hard'});gjShow({name:'คิวสอง',d:'hard'});0");await B.wait_for_timeout(300)
            t1=await B.evaluate("document.querySelector('#gjBig .gjn')?.textContent||''");await B.wait_for_timeout(4300)
            t2=await B.evaluate("document.querySelector('#gjBig .gjn')?.textContent||''");check(t1=='คิวหนึ่ง' and t2=='คิวสอง','มาหลายคน → ต่อคิวขึ้นทีละคน '+t1+' → '+t2)
            errs=eA+eB+eC+eD+eE+eF;check(not errs,'ไม่มี error '+str(errs[:3]))
            for b in bs: await b.close()
    finally:
        srv.terminate();srv.wait()
    print(f'{ok} ผ่าน · {bad} ไม่ผ่าน');print('PASS' if not bad else 'FAIL');sys.exit(1 if bad else 0)
asyncio.run(main())
