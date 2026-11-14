# ทดสอบโหมดไม่จำกัดแบบ free-for-all 3 คน: รันเซิร์ฟเวอร์ก่อนด้วย  PORT=3456 TEST_FREE_ITEMS=1 npm start  แล้ว python tests/test_ffa.py
import asyncio
from playwright.async_api import async_playwright
URL = 'http://127.0.0.1:3456/'
ARGS = ['--disable-renderer-backgrounding', '--disable-background-timer-throttling', '--disable-backgrounding-occluded-windows']
BOTS = "worms.filter(w=>w.isBot&&w.alive&&!w.isBoss).length"

async def main():
    async with async_playwright() as p:
        pages, errs, bs = [], [], []
        async def open_page(i, url=URL):
            b = await p.chromium.launch(args=ARGS); bs.append(b)
            ctx = await b.new_context(viewport={'width': 400, 'height': 800}, has_touch=True)
            pg = await ctx.new_page(); pg.on('pageerror', lambda e, i=i: errs.append((i, str(e))))
            await pg.goto(url); await pg.wait_for_timeout(500)
            await pg.evaluate("document.getElementById('sheet').classList.add('hidden')")   # ปิดหน้าต่างต้อนรับ (ถ้ามี)
            return pg
        for i in range(3):
            pg = await open_page(i); await pg.fill('#name', f'P{i+1}')
            await pg.click('#playInf'); await pg.click('.omode[data-k=normal]'); await pg.wait_for_timeout(2500 if i == 0 else 1500); pages.append(pg)
            print(f'P{i+1} joined', await pg.evaluate(f"[state,mode,NET&&NET.ffa,NET&&NET.room,NET&&NET.host,NET&&NET.players.size,{BOTS}]"))
        await pages[0].wait_for_timeout(3000)
        print('bots after 3 humans (want 30-3=27):', [await pg.evaluate(BOTS) for pg in pages])
        async def revive(pg):
            if not await pg.evaluate("player.alive"): await pg.click('#again'); await pg.wait_for_timeout(500)
        for pg in pages: await revive(pg); await pg.evaluate("player.safe=99")
        print('alive', [await pg.evaluate("player.alive") for pg in pages])
        # P2 head into P3 body -> P2 dies (FFA), P3 credited
        body = await pages[2].evaluate("(()=>{const q=player.pts[12];return [q.x,q.y]})()")
        await pages[2].evaluate("player.safe=99")
        await pages[1].evaluate(f"(()=>{{const h=player.pts[0];const dx={body[0]}-h.x,dy={body[1]}-h.y;for(const q of player.pts){{q.x+=dx;q.y+=dy}};player.safe=0;const d=player.die.bind(player);player.die=k=>{{window._k=k&&k.netId;d(k)}}}})()")
        await pages[1].wait_for_timeout(2200)
        print('P2 hit P3 -> P2 alive', await pages[1].evaluate("player.alive"), 'over shown', await pages[1].evaluate("!document.getElementById('over').classList.contains('hidden')"),
              'killed by', await pages[1].evaluate("window._k"), 'P3 id', await pages[2].evaluate("NET.id"), 'P3 kills', await pages[2].evaluate("player.kills"), 'P2 rp', await pages[1].evaluate("[prof.rp,roundRP]"))
        await pages[1].click('#again'); await pages[1].wait_for_timeout(800)
        print('P2 play again', await pages[1].evaluate("[state,player.alive,NET&&NET.ffa]"))
        # P3 bombs next to P1 -> P1 dies
        for pg in (pages[0], pages[2]): await revive(pg)
        await pages[0].evaluate("player.safe=0")
        pos = await pages[0].evaluate("[player.pts[0].x,player.pts[0].y]")
        await pages[2].evaluate(f"(()=>{{player.tgs=1;const h=player.pts[0];const dx={pos[0]}+150-h.x,dy={pos[1]}-h.y;for(const q of player.pts){{q.x+=dx;q.y+=dy}};useBomb()}})()")
        await pages[0].wait_for_timeout(800)
        print('bomb: P1 alive', await pages[0].evaluate("player.alive"), 'P3 kills', await pages[2].evaluate("player.kills"))
        # P1 (host) back to menu -> P2 becomes host, bots return for 2 humans
        await pages[0].wait_for_timeout(1500); await pages[0].click('#toMenu'); await pages[0].wait_for_timeout(3000)
        print('after host left', [await pages[i].evaluate(f"[NET.host,NET.players.size,{BOTS}]") for i in (1, 2)])
        # P3 quits with exit button
        await revive(pages[2]); await pages[2].click('#coopExit'); await pages[2].wait_for_timeout(400)
        print('P3 exit ->', await pages[2].evaluate("[state,document.getElementById('overTitle').textContent]"))
        await pages[1].screenshot(path='/tmp/f1.png')
        print('errors', errs[:5])
        for b in bs: await b.close()
asyncio.run(main())
