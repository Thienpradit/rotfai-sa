# ร้านค้าแท็บฉายา (รายการยาว) เลื่อนลงสุดแล้วปุ่ม ✕ ต้องยังเห็นและกดปิดได้ (หัวหน้าต่างติดด้านบน) · รัน PORT=3456 npm start ก่อน
import asyncio
from playwright.async_api import async_playwright
SP='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad/'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for name,dev in [('ip13',p.devices['iPhone 13']),('se',p.devices['iPhone SE']),('ip13L',p.devices['iPhone 13 landscape'])]:
            ctx=await b.new_context(**dev);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(700)
            await pg.evaluate("document.getElementById('sheet').classList.add('hidden');document.getElementById('fsTip').classList.add('hidden')")
            await pg.evaluate("openShop('title')");await pg.wait_for_timeout(300)
            await pg.evaluate("document.querySelector('#sheet .panel').scrollTop=2000");await pg.wait_for_timeout(200)
            box=await pg.evaluate("(()=>{const r=document.getElementById('sheetClose').getBoundingClientRect();const p=document.querySelector('#sheet .panel');return [Math.round(r.top),Math.round(r.bottom),innerHeight,p.scrollHeight>p.clientHeight]})()")
            await pg.screenshot(path=SP+f'shop_{name}.png')
            await pg.click('#sheetClose');await pg.wait_for_timeout(200)
            print(name,'X box top/bottom/viewport/scrollable',box,'closed',await pg.evaluate("document.getElementById('sheet').classList.contains('hidden')"),errs[:2])
            await ctx.close()
        await b.close()
asyncio.run(main())
