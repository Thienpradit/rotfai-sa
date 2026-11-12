# ทดสอบออนไลน์ 4 คน: รันเซิร์ฟเวอร์ก่อนด้วย  PORT=3456 MATCH_SECS=40 npm start  แล้ว python tests/test_online.py
import asyncio
_PAGES=[]
async def __readyall():
    for pg in _PAGES:
        try: await pg.evaluate("NET&&netSend({t:'ready',v:true})")
        except Exception: pass
    await asyncio.sleep(.4)
from playwright.async_api import async_playwright
URL='http://127.0.0.1:3456/'
async def main():
    async with async_playwright() as p:
        pages=[];errs=[];bs=[]
        for i in range(4):
            b=await p.chromium.launch(args=['--disable-renderer-backgrounding','--disable-background-timer-throttling','--disable-backgrounding-occluded-windows']);bs.append(b)
            ctxb=await b.new_context(viewport={'width':400,'height':800},has_touch=True)
            pg=await ctxb.new_page();_PAGES.append(pg);pg.on('pageerror',lambda e,i=i:errs.append((i,str(e))))
            await pg.goto(URL);await pg.wait_for_timeout(500)
            await pg.evaluate("document.getElementById('sheet').classList.add('hidden')")
            await pg.fill('#name',f'P{i+1}')
            await pg.click('#playOnline');await pg.wait_for_timeout(150)
            await pg.fill('#roomIn','TEST');await pg.click('#joinBtn');await pg.wait_for_timeout(500)
            pages.append(pg)
        await pages[0].screenshot(path='/tmp/n0.png')
        teams=[await pg.evaluate("NET&&NET.me&&NET.me.team") for pg in pages]
        print('teams',teams,'host',await pages[0].evaluate("NET.host"))
        await __readyall();await pages[0].click('#startBtn');await pages[0].wait_for_timeout(1500)
        st=[await pg.evaluate("[state,!!player,worms.length,NET.phase]") for pg in pages]
        await pages[1].wait_for_timeout(1000)
        print('remotes visible',[await pg.evaluate("worms.filter(w=>w.isRemote&&w.alive).length") for pg in pages])
        print('after start',st)
        for pg in pages: await pg.evaluate("player.safe=0")
        await pages[1].screenshot(path='/tmp/n1.png')
        # find an enemy pair: page0 (team A) and enemy page
        ti=teams.index('B') if teams[0]=='A' else teams.index('A')
        # Move enemy head into page0 player's body: do on enemy page by teleporting its own train to page0 body point
        body=await pages[0].evaluate("(()=>{const q=player.pts[10];return [q.x,q.y]})()")
        await pages[0].evaluate("player.safe=99")
        await pages[ti].evaluate(f"(()=>{{const h=player.pts[0];const dx={body[0]}-h.x,dy={body[1]}-h.y;for(const q of player.pts){{q.x+=dx;q.y+=dy}}player.safe=0}})()")
        await pages[0].wait_for_timeout(1200)
        print('kills on page0',await pages[0].evaluate("player.kills"),'enemy alive',await pages[ti].evaluate("player.alive"),'respawnT',await pages[ti].evaluate("NET.respawnT"))
        print('page0 sees enemy alive',await pages[0].evaluate(f"(worms.find(w=>w.netId===({await pages[ti].evaluate('NET.id')}))||{{}}).alive"))
        await pages[0].wait_for_timeout(3500)
        print('enemy respawned',await pages[ti].evaluate("player.alive"))
        # bomb from page0 next to enemy
        await pages[0].evaluate("player.tgs=1")
        epos=await pages[ti].evaluate("[player.pts[0].x,player.pts[0].y]")
        await pages[ti].evaluate("player.safe=0")
        await pages[0].evaluate(f"(()=>{{const h=player.pts[0];const dx={epos[0]}+150-h.x,dy={epos[1]}-h.y;for(const q of player.pts){{q.x+=dx;q.y+=dy}};useBomb()}})()")
        await pages[0].wait_for_timeout(800)
        print('after bomb: enemy alive',await pages[ti].evaluate("player.alive"),'page0 kills',await pages[0].evaluate("player.kills"))
        await pages[0].screenshot(path='/tmp/n2.png')
        sc=await pages[2].evaluate("JSON.stringify(NET.score)")
        print('score',sc)
        # wait for match end (30s)
        await pages[0].wait_for_timeout(33000)
        print('end state',[await pg.evaluate("[state,NET&&NET.phase,document.getElementById('sheetTitle').textContent]") for pg in pages])
        await pages[0].screenshot(path='/tmp/n3.png')
        print('errors',errs[:5])
        await b.close()
asyncio.run(main())
