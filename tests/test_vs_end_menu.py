# 2v2 จบแมตช์ → ออกจากห้อง → ต้องกลับหน้าแรกได้ (เคยค้างเพราะ farSpot คืน null ตอนวงหด) · รัน: PORT=3456 MATCH_SECS=12 npm start
import asyncio
from playwright.async_api import async_playwright
SP='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad/'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--disable-renderer-backgrounding']);ctx=await b.new_context(**p.devices['iPhone 13']);pg=await ctx.new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(800)
        await pg.evaluate("document.getElementById('sheet').classList.add('hidden');document.getElementById('fsTip').classList.add('hidden')")
        btns=await pg.evaluate("[...document.querySelectorAll('#menu .btn.play')].map(b=>b.id+':'+b.textContent.slice(0,12))");print(btns)
        await pg.evaluate("netConnect('ENDT','','vs')");await pg.wait_for_timeout(1500)
        await pg.click('#startBtn');await pg.wait_for_timeout(1500)
        print('playing',await pg.evaluate("[state,NET&&NET.phase]"))
        await pg.wait_for_timeout(13000)
        print('after end',await pg.evaluate("[state,NET&&NET.phase,document.getElementById('sheet').classList.contains('hidden'),document.getElementById('sheetTitle').textContent]"))
        await pg.screenshot(path=SP+'vsend1.png')
        await pg.click('#leave2');await pg.wait_for_timeout(800)
        print('ERRS',errs[-3:]);print('after leave',await pg.evaluate("[state,!!NET,document.getElementById('menu').classList.contains('hidden'),worms.length,AR]"))
        await pg.evaluate("document.getElementById('sheet').classList.add('hidden')");await pg.click('#bShop');await pg.wait_for_timeout(500);print('menu works (shop opens)',await pg.evaluate("document.getElementById('sheetTitle').textContent"))
        await pg.screenshot(path=SP+'vsend2.png')
        print(errs[:5]);await b.close()
asyncio.run(main())
