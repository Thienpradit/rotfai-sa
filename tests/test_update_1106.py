# ทดสอบอัปเดต 6 พ.ย. 2026: มินิแมปเห็นตัวเองชัด, อุโมงค์อมตะ 2 วิ, แยกโหมดออนไลน์ (30 คน บอท Normal) กับเล่นกับบอท (เลือกความยาก)
# รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start  แล้ว python tests/test_update_1106.py
import asyncio
from playwright.async_api import async_playwright
URL = 'http://127.0.0.1:3456/'
ARGS = ['--disable-renderer-backgrounding', '--disable-background-timer-throttling', '--disable-backgrounding-occluded-windows']
BOTS = "worms.filter(w=>w.isBot&&w.alive&&!w.isBoss).length"

async def main():
    async with async_playwright() as p:
        errs, pages = [], []
        async def open_page(i, vp={'width': 800, 'height': 700}):
            b = await p.chromium.launch(args=ARGS)
            pg = await (await b.new_context(viewport=vp)).new_page()
            pg.on('pageerror', lambda e, i=i: errs.append((i, str(e))))
            await pg.goto(URL); await pg.wait_for_timeout(600)
            await pg.evaluate("document.getElementById('sheet').classList.add('hidden')")
            return pg
        a = await open_page(0)
        print('menu buttons', await a.evaluate("[...document.querySelectorAll('#menu .btn')].map(b=>b.textContent)"),
              'difficulty on menu?', await a.evaluate("!!document.querySelector('#menu .dbtn')"))
        await a.screenshot(path='/tmp/u_menu.png')
        # --- เล่นกับบอท: ไม่มีปุ่มแล้ว (7 พ.ย.) เรียกตรงเพื่อทดสอบส่วนอื่นต่อ ---
        print('playBot gone', await a.evaluate("!document.getElementById('playBot')"))
        await a.evaluate("setDiff('hard');startGame('inf')"); await a.wait_for_timeout(600)
        print('bot game', await a.evaluate("[state,mode,!!NET,diff,D().label,worms.filter(w=>!w.isP&&!w.isBoss).length]"))
        # --- อุโมงค์ อมตะ 2 วิ ---
        r = await a.evaluate("""(()=>{player.safe=0;player.tunCD=0;const p=portals[0];const h=player.pts[0];const dx=p.x-h.x,dy=p.y-h.y;for(const q of player.pts){q.x+=dx;q.y+=dy}return 1})()""")
        await a.wait_for_timeout(150)
        s1 = await a.evaluate("+player.safe.toFixed(2)")
        await a.wait_for_timeout(2100)
        print('tunnel: safe right after', s1, '(want ~1.8-2.0)', 'after 2.1s', await a.evaluate("+player.safe.toFixed(2)"), 'alive', await a.evaluate("player.alive"))
        # --- มินิแมป ---
        await a.evaluate("player.safe=99"); await a.wait_for_timeout(300)
        await a.screenshot(path='/tmp/u_minimap.png', clip={'x': 0, 'y': 0, 'width': 260, 'height': 260})
        await a.evaluate("toMenu()")
        # --- ออนไลน์: ทุกคนเข้าโลกเดียวกัน, บอท Normal, คน+บอท = 30 ---
        await a.evaluate("setDiff('hard')")      # ผู้เล่นตั้ง Hard ไว้ในโหมดบอท แต่ออนไลน์ต้องเป็น Normal
        await a.click('#playInf'); await a.wait_for_timeout(3500); pages.append(a)
        b = await open_page(1); await b.evaluate("setDiff('easy')"); await b.click('#playInf'); await b.wait_for_timeout(2500); pages.append(b)
        await a.wait_for_timeout(4000)
        for i, pg in enumerate(pages):
            print(f'online P{i+1}', await pg.evaluate(f"[NET.room,NET.host,NET.players.size,{BOTS},D().label,diff,mode]"))
        print('RP multiplier online (score 600, 0 kills) =', await a.evaluate("gameRP(600,0,0)"), '(want 10)')
        print('errors', errs)

asyncio.run(main())
