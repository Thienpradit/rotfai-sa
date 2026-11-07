# หวูดโดนผู้เล่นจริง → ช้าลงตามขั้นหวูด (8 พ.ย.) · รัน PORT=3456 npm start ก่อน
import asyncio
from playwright.async_api import async_playwright
SP='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad/'
async def main():
    async with async_playwright() as p:
        pages=[]
        for nm in ['เอ','บี','ซี']:
            b=await p.chromium.launch();ctx=await b.new_context(**p.devices['iPhone 13']);pg=await ctx.new_page()
            await pg.add_init_script(f"localStorage.setItem('wormName','{nm}')");await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(600)
            await pg.evaluate("document.getElementById('sheet').classList.add('hidden');document.getElementById('fsTip').classList.add('hidden');playEndless()");pages.append(pg)
        await pages[0].wait_for_timeout(3500)
        A,B,C=pages
        await A.evaluate("player.ghost=0;player.safe=0;player.die=()=>{}")   # กันตายเพราะบอทระหว่างเทสต์
        ax,ay=await A.evaluate("[player.pts[0].x,player.pts[0].y]")
        # วัดความเร็วก่อนโดน
        sp0=await A.evaluate("new Promise(r=>{const a={...player.pts[0]};setTimeout(()=>{const b=player.pts[0];r(Math.hypot(b.x-a.x,b.y-a.y))},1000)})")
        ax,ay=await A.evaluate("[player.pts[0].x,player.pts[0].y]")
        await B.evaluate(f"netSend({{t:'horn',k:'dragon',x:{ax},y:{ay}}})");await A.wait_for_timeout(400)
        st=await A.evaluate("[player.hslow,player.hslowF,state,player.alive]");print('A slowed (t,f,state,alive):',st)
        sp1=await A.evaluate("new Promise(r=>{const a={...player.pts[0]};setTimeout(()=>{const b=player.pts[0];r(Math.hypot(b.x-a.x,b.y-a.y))},1000)})")
        print('A speed px/s before %.0f after %.0f (ratio %.2f)'%(sp0,sp1,sp1/sp0))
        print('C (far) slowed:',await C.evaluate("player.hslow||0"))
        await A.wait_for_timeout(200);await A.screenshot(path=SP+'horn_player_slow.png')
        await A.wait_for_timeout(3300);print('after 3.5s A hslow:',round(await A.evaluate("player.hslow"),2))
        print('state',await A.evaluate('[state,player.alive]'))
asyncio.run(main())
