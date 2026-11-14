# 🌍 โลกออนไลน์ 3 โหมด (14 พ.ย.): หน้าเลือกโหมด · Easy ไม่ได้อะไรเลย + บอกว่าถ้าเล่น Normal ได้เท่าไร · Hard ×1.3 + หิน
# รันเซิร์ฟเวอร์ PORT=3463 เอง
import asyncio, json, os, subprocess, time, urllib.request, sys
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));URL='http://127.0.0.1:3463'
SHOTS=os.environ.get('SHOTS','/tmp')
ok=0;bad=0
def check(c,msg):
    global ok,bad
    if c: ok+=1;print('  ✓',msg)
    else: bad+=1;print('  ✗',msg)
async def main():
    srv=subprocess.Popen(['node','server.js'],cwd=ROOT,env={**os.environ,'PORT':'3463'},stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT);time.sleep(1.5)
    try:
        async with async_playwright() as p:
            async def page(w=900,h=700):
                b=await p.chromium.launch();pg=await (await b.new_context(viewport={'width':w,'height':h})).new_page()
                errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));await pg.goto(URL);await pg.wait_for_timeout(1200)
                if await pg.is_visible('#acGuest'): await pg.click('#acGuest');await pg.wait_for_timeout(300)
                return b,pg,errs
            # --- หน้าเลือกโหมด ---
            b1,e,err1=await page()
            await e.click('#playInf');await e.wait_for_timeout(600)
            cards=await e.eval_on_selector_all('.omode','els=>els.map(x=>[x.dataset.k,x.innerText])')
            check([c[0] for c in cards]==['easy','normal','hard'],'มี 3 โหมด '+str([c[0] for c in cards]))
            check(all('คน' in c[1] for c in cards),'แต่ละโหมดบอกจำนวนคนเล่น')
            await e.screenshot(path=SHOTS+'/omode_pick.png')
            # --- Easy ---
            await e.click('.omode[data-k=easy]');await e.wait_for_timeout(2500)
            check(await e.evaluate("NET&&NET.diff")=='easy','เข้าโลก Easy (รหัส '+await e.evaluate("NET.room")+')')
            check('Easy' in await e.inner_text('#coopMode'),'ป้ายโหมดในเกม: '+await e.inner_text('#coopMode'))
            c0,rp0,k0,g0=await e.evaluate("[prof.coins,prof.rp,prof.st.kills||0,prof.st.games||0]")
            await e.evaluate("addCoins(100);track('kills',3);player.kills=3;player.maxMass=600;player.mass=600")
            await e.evaluate("finish(false)");await e.wait_for_timeout(400)
            c1,rp1,k1,g1=await e.evaluate("[prof.coins,prof.rp,prof.st.kills||0,prof.st.games||0]")
            check(c1==c0 and rp1==rp0 and k1==k0 and g1==g0,f'Easy ไม่ได้เหรียญ/RP/สถิติ (เหรียญ {c0}→{c1} RP {rp0}→{rp1} กำจัด {k0}→{k1} เกม {g0}→{g1})')
            t=await e.inner_text('#coinEarn');print('    ',t.replace('\n',' | '))
            check('Normal' in t and '+175' in t and '+18 RP' in t,'จบเกม Easy บอกว่าถ้าเล่น Normal ได้ +175 🪙 (100+60+15) · +18 RP')
            await e.screenshot(path=SHOTS+'/omode_easy_over.png')
            # --- Hard ---
            b2,h,err2=await page()
            await h.click('#playInf');await h.wait_for_timeout(300);await h.click('.omode[data-k=hard]');await h.wait_for_timeout(2500)
            check(await h.evaluate("NET.diff")=='hard' and await h.evaluate("OBST.length")>=35,'เข้าโลก Hard มีหิน '+str(await h.evaluate("OBST.length"))+' ก้อน')
            check(await h.evaluate("!OBST.some(o=>Math.hypot(o.x-player.pts[0].x,o.y-player.pts[0].y)<o.r+60)"),'ผู้เล่นเกิดไม่ทับหิน')
            c0=await h.evaluate("prof.coins");await h.evaluate("addCoins(100)");check(await h.evaluate("prof.coins")-c0==130,'Hard เหรียญ ×1.3 (100 → 130)')
            o=await (await h.request.get(URL+'/online')).json();check(o.get('easy')==1 and o.get('hard')==1,'/online นับคนแต่ละโหมด '+str(o))
            # ชนหิน = ตาย
            await h.evaluate("const o=OBST[0],hd=player.pts[0];player.ghost=0;player.safe=0;player.tun=null;for(const q of player.pts){q.x+=o.x-hd.x;q.y+=o.y-hd.y}")
            await h.wait_for_timeout(500);check(not await h.evaluate("player.alive"),'Hard เอาหัวชนหิน → ตาย')
            await h.wait_for_timeout(3600)
            await h.screenshot(path=SHOTS+'/omode_hard.png')
            # RP ×1.3
            b3,h2,err3=await page()
            await h2.click('#playInf');await h2.wait_for_timeout(300);await h2.click('.omode[data-k=hard]');await h2.wait_for_timeout(2500)
            rp0=await h2.evaluate("prof.rp");await h2.evaluate("player.kills=3;player.maxMass=600;player.mass=600;finish(false)")
            check(await h2.evaluate("prof.rp")-rp0==round(18*1.3),'Hard RP ×1.3 (18 → 23) ได้ '+str(await h2.evaluate("prof.rp")-rp0))
            check('Hard ×1.3' in await h2.inner_text('#coinEarn'),'หน้าจบบอก Hard ×1.3')
            # ปุ่ม "ไปเล่น Normal" จากหน้าจบ Easy
            await e.click('#easyGo');await e.wait_for_timeout(2500)
            check(await e.evaluate("NET&&NET.diff")=='normal','กดปุ่มในหน้าจบ Easy → เข้าโลก Normal')
            c0=await e.evaluate("prof.coins");await e.evaluate("addCoins(100)");check(await e.evaluate("prof.coins")-c0==100,'Normal เหรียญเท่าเดิม')
            # มือถือแนวนอน: หน้าเลือกโหมดพอดีจอ
            b4,m,err4=await page(844,390);await m.click('#playInf');await m.wait_for_timeout(600);await m.screenshot(path=SHOTS+'/omode_pick_land.png')
            for b in (b1,b2,b3,b4): await b.close()
            errs=err1+err2+err3+err4;check(not errs,'ไม่มี error '+str(errs[:3]))
    finally:
        srv.terminate();srv.wait()
    print(f'{ok} ผ่าน · {bad} ไม่ผ่าน');print('PASS' if not bad else 'FAIL');sys.exit(1 if bad else 0)
asyncio.run(main())
