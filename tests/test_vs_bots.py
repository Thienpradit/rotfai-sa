# ทดสอบ 2v2 เติมบอท: คน 2 คนอยู่ทีมแดง → เซิร์ฟเวอร์เติมบอท 2 ตัวให้ทีมน้ำเงิน, บอทชนคนตายได้แต้ม, จบแมตช์มีบอทในสรุป
# รันเซิร์ฟเวอร์ก่อน: PORT=3456 MATCH_SECS=40 npm start  แล้ว python tests/test_vs_bots.py
import asyncio
_PAGES=[]
async def __readyall():
    for pg in _PAGES:
        try: await pg.evaluate("NET&&netSend({t:'ready',v:true})")
        except Exception: pass
    await asyncio.sleep(.4)
from playwright.async_api import async_playwright
URL = 'http://127.0.0.1:3456/'
ARGS = ['--disable-renderer-backgrounding', '--disable-background-timer-throttling', '--disable-backgrounding-occluded-windows']
async def main():
    async with async_playwright() as p:
        errs, pages = [], []
        for i in range(2):
            b = await p.chromium.launch(args=ARGS)
            pg = await (await b.new_context(viewport={'width': 700, 'height': 600})).new_page(); _PAGES.append(pg)
            pg.on('pageerror', lambda e, i=i: errs.append((i, str(e))))
            await pg.goto(URL); await pg.wait_for_timeout(600)
            await pg.evaluate("document.getElementById('sheet').classList.add('hidden')"); await pg.fill('#name', f'คน{i+1}')
            await pg.evaluate("netConnect('BOTS','')"); await pg.wait_for_timeout(1200); pages.append(pg)
        a, c = pages
        print('lobby', await a.evaluate("[...NET.players.values()].map(p=>p.name+':'+p.team)"), 'start enabled', await a.evaluate("!document.getElementById('startBtn').disabled"))
        await c.click("button.tpick[data-t=A]"); await c.wait_for_timeout(500)
        await a.screenshot(path='/tmp/vs_lobby.png')
        print('after pick', await a.evaluate("[...NET.players.values()].map(p=>p.name+':'+p.team)"), 'slots', await a.evaluate("[...document.querySelectorAll('.tcol div')].map(d=>d.textContent).join(' | ')"))
        await __readyall(); await a.evaluate("netSend({t:'start'})"); await a.wait_for_timeout(2500)
        print('host bots', await a.evaluate("worms.filter(w=>w.isBot&&w.alive).map(w=>w.team)"), 'guest sees', await c.evaluate("worms.filter(w=>w.isBot&&w.alive).map(w=>w.team+(w.isRemote?'(remote)':''))"))
        # คน2 (ไม่ใช่หัวหน้า) พุ่งชนลำตัวบอท → ตาย, บอทได้แต้มให้ทีมน้ำเงิน
        await c.evaluate("player.safe=0")
        tgt = await c.evaluate("(()=>{const w=worms.find(w=>w.isBot&&w.alive);const q=w.pts[Math.min(14,w.pts.length-1)];return [q.x,q.y]})()")
        await c.evaluate(f"(()=>{{const h=player.pts[0];const dx={tgt[0]}-h.x,dy={tgt[1]}-h.y;for(const q of player.pts){{q.x+=dx;q.y+=dy}}}})()")
        await c.wait_for_timeout(1500)
        print('guest hit bot -> respawn timer', await c.evaluate("NET.respawnT>0||player.safe>0"), 'score', await a.evaluate("JSON.stringify(NET.score)"))
        # หัวหน้าห้องโยนระเบิดใส่บอท (เซิร์ฟเวอร์คำนวณ) → บอทตาย เกิดใหม่ใน ~3 วิ
        await a.evaluate("(()=>{const w=worms.find(w=>w.isBot&&w.alive&&!w.ghost);const t=w.pts[0];player.safe=99;player.tgs=1;player.bombT=[15];const h=player.pts[0];const dx=t.x+200-h.x,dy=t.y-h.y;for(const q of player.pts){q.x+=dx;q.y+=dy}useBomb()})()"); await a.wait_for_timeout(500)
        print('bomb kills credited', await a.evaluate("player.kills"), 'score', await a.evaluate("JSON.stringify(NET.score)"))
        n1 = await a.evaluate("worms.filter(w=>w.isBot&&w.alive).length"); await a.wait_for_timeout(3500)
        print('bot died ->', n1, 'after 3.5s ->', await a.evaluate("worms.filter(w=>w.isBot&&w.alive).length"))
        await a.wait_for_timeout(36000)
        print('end title', await a.evaluate("document.getElementById('sheetTitle').textContent"), 'rows', await a.evaluate("[...document.querySelectorAll('#sheetBody .item .tx')].map(e=>e.textContent)"))
        await a.screenshot(path='/tmp/vs_end.png')
        print('errors', errs)
asyncio.run(main())
