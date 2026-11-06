# ทดสอบ: อุโมงค์ที่ปลายทางอยู่นอกวง (วงหด) ต้องปิด ไม่วาร์ปไปตาย · ขบวนเกิดใหม่ไกลจากทุกคัน + 2.5 วิแรกชนทะลุ (ออนไลน์ด้วย)
# รันเซิร์ฟเวอร์ก่อน: PORT=3456 MATCH_SECS=40 npm start
import asyncio
from playwright.async_api import async_playwright
URL = 'http://127.0.0.1:3456/'
ARGS = ['--disable-renderer-backgrounding', '--disable-background-timer-throttling', '--disable-backgrounding-occluded-windows']
MOVE = "(x,y)=>{const h=player.pts[0];const dx=x-h.x,dy=y-h.y;for(const q of player.pts){q.x+=dx;q.y+=dy}}"
async def main():
    async with async_playwright() as p:
        errs, pages = [], []
        async def page(i):
            b = await p.chromium.launch(args=ARGS); pg = await (await b.new_context(viewport={'width': 700, 'height': 600})).new_page()
            pg.on('pageerror', lambda e, i=i: errs.append((i, str(e)))); await pg.goto(URL); await pg.wait_for_timeout(600)
            await pg.evaluate("document.getElementById('sheet').classList.add('hidden')"); return pg
        a = await page(0); ev = a.evaluate
        # ---- อุโมงค์ ----
        await ev("startGame('time')"); await a.wait_for_timeout(300)
        await ev(f"window.MV={MOVE};player.safe=99;player.tunCD=0;timeLeft=300")
        print('full ring: open portals', await ev("portals.filter(portalOpen).length"), '/', await ev("portals.length"))
        await ev("timeLeft=10"); await a.wait_for_timeout(200)
        print('shrunk ring AR', round(await ev("AR")), 'open portals', await ev("portals.filter(portalOpen).length"))
        r = await ev("""(()=>{const p=portals.find(p=>!portalOpen(p)&&Math.hypot(p.x,p.y)<AR-60);if(!p)return 'no inner closed portal';player.tunCD=0;MV(p.x,p.y);return [p.x|0,p.y|0]})()""")
        await a.wait_for_timeout(300)
        print('enter closed portal', r, '-> warped?', await ev("Math.hypot(player.pts[0].x,player.pts[0].y)|0"), 'alive', await ev("player.alive"), 'msg', await ev("texts.some(t=>t.txt.includes('อุโมงค์ปิด'))"))
        await a.screenshot(path='/tmp/t_closed.png')
        await ev("timeLeft=300"); await a.wait_for_timeout(100)
        r = await ev("(()=>{const p=portals[0];player.tunCD=0;MV(p.x,p.y);return 1})()"); await a.wait_for_timeout(300)
        print('full ring warp works', await ev("player.tunCD>0"))
        # ---- เกิดใหม่ไกล + ชนทะลุ ----
        d = await ev("""(()=>{let m=1e9;for(let i=0;i<20;i++){spawnAI();const w=worms[worms.length-1],h=w.pts[0];for(const o of worms)if(o!==w&&o.alive)for(let k=0;k<o.pts.length;k+=8)m=Math.min(m,Math.hypot(o.pts[k].x-h.x,o.pts[k].y-h.y))}return m|0})()""")
        print('20 new bots: closest distance to any train', d, '(want >= ~300)')
        await ev("player.safe=0")
        r = await ev("""(()=>{const w=worms[worms.length-1];w.ghost=2.5;const q=w.pts[12];MV(q.x,q.y);return w.ghost})()""")
        await a.wait_for_timeout(250)
        print('hit ghost body -> alive', await ev("player.alive"))
        await ev("worms[worms.length-1].ghost=0;player.safe=0;(()=>{const w=worms[worms.length-1],q=w.pts[12];MV(q.x,q.y)})()"); await a.wait_for_timeout(250)
        print('hit normal body -> alive', await ev("player.alive"))
        await a.wait_for_timeout(1600); await ev("toMenu()")
        # ---- ออนไลน์ 2v2: บอทเกิดใหม่ คนอื่นเห็นเป็นผี ชนทะลุ ----
        await ev("netConnect('GHOST','')"); await a.wait_for_timeout(1200)
        c = await page(1); await c.evaluate("netConnect('GHOST','')"); await c.wait_for_timeout(1200)
        await c.click("button.tpick[data-t=A]"); await c.wait_for_timeout(400); await a.click('#startBtn'); await a.wait_for_timeout(1200)
        print('guest sees new bots as ghost', await c.evaluate("worms.filter(w=>w.isBot&&w.alive).map(w=>w.ghost)"))
        await c.evaluate(f"window.MV={MOVE};player.safe=0;player.ghost=0;(()=>{{const w=worms.find(w=>w.isBot&&w.alive&&w.ghost>0);const q=w.pts[10];MV(q.x,q.y)}})()"); await c.wait_for_timeout(250)
        print('guest hits ghost bot -> alive', await c.evaluate("player.alive"))
        await a.wait_for_timeout(2500)
        print('after 2.5s bots ghost', await c.evaluate("worms.filter(w=>w.isBot&&w.alive).map(w=>w.ghost)"))
        # คนเกิดใหม่: ห่างทุกคัน หันเข้ากลาง
        await c.evaluate("player.die(null)"); await c.wait_for_timeout(3600)
        print('guest respawn: ghost', await c.evaluate("player.ghost>0"), 'nearest train', await c.evaluate("(()=>{const h=player.pts[0];let m=1e9;for(const o of worms)if(o!==player&&o.alive)for(const q of o.pts)m=Math.min(m,Math.hypot(q.x-h.x,q.y-h.y));return m|0})()"),
              'host sees guest ghost', await a.evaluate("(worms.find(w=>w.netId&&w.netId>0&&w.isRemote)||{}).ghost"))
        print('errors', errs)
asyncio.run(main())
