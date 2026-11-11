# ผจญภัย: ปุ่ม ⏸ หยุด / 🚪 ออก (11 พ.ย. 2026) · รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start
import asyncio
from playwright.async_api import async_playwright
OUT='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await (await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2)).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(600)
        await pg.evaluate("startStage(0)");await pg.wait_for_timeout(1200)
        vis=await pg.evaluate("!document.getElementById('advBar').classList.contains('hidden')")
        await pg.click('#advPause');await pg.wait_for_timeout(200)
        a=await pg.evaluate("({c:stageClock,x:player.pts[0].x,y:player.pts[0].y,b:worms.filter(w=>!w.isP).map(w=>w.pts[0].x).join()})")
        await pg.wait_for_timeout(1500)
        b2=await pg.evaluate("({c:stageClock,x:player.pts[0].x,y:player.pts[0].y,b:worms.filter(w=>!w.isP).map(w=>w.pts[0].x).join(),ov:!document.getElementById('pauseOv').classList.contains('hidden'),t:document.getElementById('pauseOv').innerText})")
        await pg.screenshot(path=OUT+'/adv_pause.png')
        frozen=a==dict((k,b2[k]) for k in a) and b2['ov']
        await pg.click('#pResume');await pg.wait_for_timeout(800)
        c=await pg.evaluate("({c:stageClock,ov:!document.getElementById('pauseOv').classList.contains('hidden')})");resumed=c['c']>b2['c'] and not c['ov']
        await pg.keyboard.press('KeyP');await pg.wait_for_timeout(200);kp=await pg.evaluate("PAUSED");await pg.keyboard.press('Escape');await pg.wait_for_timeout(200);ke=await pg.evaluate("PAUSED")
        await pg.click('#advExit');await pg.wait_for_timeout(200);t2=await pg.evaluate("document.getElementById('pauseOv').innerText");await pg.screenshot(path=OUT+'/adv_exit.png')
        await pg.click('#pQuit');await pg.wait_for_timeout(600)
        q=await pg.evaluate("({state,mode,stage:!!STAGE,paused:PAUSED,bar:document.getElementById('advBar').classList.contains('hidden'),sheet:document.getElementById('sheetTitle')?document.getElementById('sheetTitle').textContent:document.querySelector('#sheet').innerText.slice(0,30),menu:!document.getElementById('menu').classList.contains('hidden'),st:prof.stage[0]||0})")
        # เริ่มใหม่ + สลับแอป = หยุดเอง
        await pg.evaluate("startStage(0)");await pg.wait_for_timeout(500)
        await pg.evaluate("Object.defineProperty(document,'visibilityState',{value:'hidden',configurable:true});document.dispatchEvent(new Event('visibilitychange'))");vp=await pg.evaluate("PAUSED")
        await pg.click('#pRetry');await pg.wait_for_timeout(300);rt=await pg.evaluate("({p:PAUSED,c:stageClock<1,s:STAGE&&STAGE.code})")
        print('bar',vis,'frozen',frozen,a,b2['c']);print('overlay',b2['t'].replace('\n',' | '));print('resumed',resumed,c);print('key P',kp,'Esc',ke);print('exit ask',t2.replace('\n',' | '));print('quit',q);print('visibility pause',vp,'retry',rt)
        ok=vis and frozen and resumed and kp and not ke and 'ออกจากด่าน?' in t2 and q['state']=='menu' and not q['stage'] and q['bar'] and 'ผจญภัย' in q['sheet'] and q['st']==0 and vp and not rt['p'] and rt['c'] and rt['s']=='1-1'
        print('errors',errs[:3]);print('PASS' if ok and not errs else 'FAIL');await b.close()
asyncio.run(main())
