# ทดสอบโหมดเล่นกับเพื่อน (co-op) 3 คน: รันเซิร์ฟเวอร์ก่อนด้วย  PORT=3456 npm start  แล้ว python tests/test_coop.py
import asyncio
from playwright.async_api import async_playwright
URL = 'http://127.0.0.1:3456/'
ARGS = ['--disable-renderer-backgrounding', '--disable-background-timer-throttling', '--disable-backgrounding-occluded-windows']

async def main():
    async with async_playwright() as p:
        pages, errs, bs = [], [], []
        async def open_page(i, url=URL):
            b = await p.chromium.launch(args=ARGS); bs.append(b)
            ctx = await b.new_context(viewport={'width': 400, 'height': 800}, has_touch=True)
            pg = await ctx.new_page(); pg.on('pageerror', lambda e, i=i: errs.append((i, str(e))))
            await pg.goto(url); await pg.wait_for_timeout(500)
            return pg
        # P1 creates room from the menu
        pg = await open_page(0); await pg.fill('#name', 'P1')
        await pg.click('#playCoop'); await pg.wait_for_timeout(150)
        await pg.fill('#roomIn', 'COOP'); await pg.click('#joinBtn'); await pg.wait_for_timeout(2500)
        pages.append(pg)
        print('P1 alone', await pg.evaluate("[state,NET.coop,NET.host,mode,worms.filter(w=>w.isBot).length,!document.getElementById('coopBar').classList.contains('hidden')]"))
        # P2, P3 join through invite link
        for i in (1, 2):
            pg = await open_page(i, URL + '?coop=COOP'); await pg.fill('#name', f'P{i+1}')
            print(f'P{i+1} sheet', await pg.evaluate("document.getElementById('sheetTitle').textContent"), await pg.input_value('#roomIn'))
            await pg.click('#joinBtn'); await pg.wait_for_timeout(1200); pages.append(pg)
        await pages[2].wait_for_timeout(1500)
        for i, pg in enumerate(pages):
            print(f'P{i+1}', await pg.evaluate("[state,NET.host,NET.players.size,worms.filter(w=>w.isBot&&w.alive).length,worms.filter(w=>w.isRemote&&!w.isBot&&w.alive).length,AR]"))
        await pages[1].screenshot(path='/tmp/c1.png')
        for pg in pages: await pg.evaluate("player.safe=0")
        # friendly pass-through: P2 head into P3 body
        body = await pages[2].evaluate("(()=>{const q=player.pts[12];return [q.x,q.y]})()")
        await pages[2].evaluate("player.safe=99")
        await pages[1].evaluate(f"(()=>{{const h=player.pts[0];const dx={body[0]}-h.x,dy={body[1]}-h.y;for(const q of player.pts){{q.x+=dx;q.y+=dy}};player.safe=0}})()")
        await pages[1].wait_for_timeout(600)
        print('friend collide -> P2 alive (want true):', await pages[1].evaluate("player.alive"))
        # P2 head into a bot body -> P2 dies, respawns
        bb = await pages[1].evaluate("(()=>{const b=worms.find(w=>w.isBot&&w.alive&&w.pts.length>30&&!w.isBoss);const q=b.pts[20];return [q.x,q.y]})()")
        await pages[1].evaluate(f"(()=>{{const h=player.pts[0];const dx={bb[0]}-h.x,dy={bb[1]}-h.y;for(const q of player.pts){{q.x+=dx;q.y+=dy}};player.safe=0}})()")
        await pages[1].wait_for_timeout(500)
        print('P2 hit bot -> alive (want false):', await pages[1].evaluate("player.alive"), 'coins', await pages[1].evaluate("prof.coins"), 'rp', await pages[1].evaluate("prof.rp"))
        await pages[1].wait_for_timeout(3500)
        print('P2 respawned:', await pages[1].evaluate("player.alive"))
        # host bot runs into P3's body (decided on host) -> bot dies, P3 credited
        await pages[2].evaluate("player.safe=99")
        b3 = await pages[0].evaluate(f"(()=>{{const fr=worms.find(w=>w.isRemote&&w.netId==={await pages[2].evaluate('NET.id')});const q=fr.pts[Math.min(15,fr.pts.length-1)];const b=worms.find(w=>w.isBot&&!w.isRemote&&w.alive&&!w.isBoss);const h=b.pts[0];const dx=q.x-h.x,dy=q.y-h.y;for(const p of b.pts){{p.x+=dx;p.y+=dy}};b.safe=0;return b.netId}})()")
        await pages[0].wait_for_timeout(800)
        print('bot', b3, 'gone on P3:', await pages[2].evaluate(f"!(worms.find(w=>w.netId==={b3})||{{}}).alive"), 'P3 kills', await pages[2].evaluate("player.kills"))
        # P3 bombs near bots
        pos = await pages[0].evaluate("(()=>{const b=worms.filter(w=>w.isBot&&!w.isRemote&&w.alive&&!w.isBoss)[0];return [b.pts[0].x,b.pts[0].y]})()")
        await pages[2].evaluate(f"(()=>{{player.tgs=1;const h=player.pts[0];const dx={pos[0]}+120-h.x,dy={pos[1]}-h.y;for(const q of player.pts){{q.x+=dx;q.y+=dy}};useBomb()}})()")
        await pages[2].wait_for_timeout(800)
        print('after P3 bomb: P3 kills', await pages[2].evaluate("player.kills"), 'P1 alive', await pages[0].evaluate("player.alive"))
        # host leaves -> next player becomes host and bots come back
        await pages[0].click('#coopExit'); await pages[0].wait_for_timeout(300)
        print('P1 back at menu:', await pages[0].evaluate("[state,NET===null]"))
        await pages[1].wait_for_timeout(2500)
        for i in (1, 2):
            print(f'P{i+1} after host left', await pages[i].evaluate("[NET.host,NET.players.size,worms.filter(w=>w.isBot&&w.alive).length]"))
        await pages[2].screenshot(path='/tmp/c2.png')
        print('errors', errs[:5])
        for b in bs: await b.close()
asyncio.run(main())
