# ผู้เล่นกำจัดผู้เล่น → ทุกคนเห็นประกาศ "⚔️ A กำจัด B" บนจอ (8 พ.ย.) · รัน PORT=3456 npm start ก่อน
import asyncio
from playwright.async_api import async_playwright
SP='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad/'
async def main():
    async with async_playwright() as p:
        pages=[]
        for nm in ['สายฟ้า','ภูผา','ดาวเหนือ']:
            b=await p.chromium.launch();ctx=await b.new_context(**p.devices['iPhone 13']);pg=await ctx.new_page()
            await pg.add_init_script(f"localStorage.setItem('wormName','{nm}')");await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(600)
            await pg.evaluate("document.getElementById('sheet').classList.add('hidden');document.getElementById('fsTip').classList.add('hidden');playEndless()");pages.append(pg)
        await pages[0].wait_for_timeout(3000)
        ids=[await pg.evaluate('NET.id') for pg in pages];print('ids',ids,'same world',len({await pg.evaluate('NET.room') for pg in pages})==1)
        # ภูผา (1) ชนสายฟ้า (0) → สายฟ้าตาย ภูผาได้แต้ม
        print('before',await pages[0].evaluate("[state,player&&player.alive,player&&player.ghost]"))
        await pages[1].evaluate("(()=>{window._km=[];const o=netMsg;netMsg=function(m){if(m&&m.t==='kill')_km.push(m);return o(m)};return 1})()")
        await pages[0].evaluate(f"player.ghost=0;player.alive=true;player.die({{netId:{ids[1]}}})");await pages[0].wait_for_timeout(900)
        for i,pg in enumerate(pages):print(i,await pg.evaluate("killFeed.map(k=>k.txt)"))
        print('kill msgs on 1',await pages[1].evaluate('_km'))
        await pages[1].screenshot(path=SP+'pvp_feed_killer.png');await pages[2].screenshot(path=SP+'pvp_feed_other.png')
asyncio.run(main())
