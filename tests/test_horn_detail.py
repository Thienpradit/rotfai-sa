# ร้านค้าแท็บหวูด: แตะแถวหวูด → หน้ารายละเอียด (ภาพจำลอง + ความสามารถ + เทียบทุกแบบ) · รัน PORT=3456 npm start ก่อน
import asyncio
from playwright.async_api import async_playwright
SP='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad/'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(**p.devices['iPhone 13']);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(700)
        await pg.evaluate("document.getElementById('sheet').classList.add('hidden');document.getElementById('fsTip').classList.add('hidden')")
        await pg.evaluate("openShop('horn')");await pg.wait_for_timeout(300)
        rows=await pg.evaluate("document.querySelectorAll('#sheetBody .item.tap').length");print('tappable horn rows',rows)
        await pg.screenshot(path=SP+'horn_shop.png')
        await pg.click('#sheetBody .item.tap >> nth=4');await pg.wait_for_timeout(400)   # ไซเรน
        print('title',await pg.evaluate("document.getElementById('sheetTitle').textContent"))
        for t in [0.5,1.9,3.0]:
            await pg.evaluate(f"(()=>{{const cv=document.querySelector('#sheetBody .pv');}})()")
        await pg.wait_for_timeout(900);await pg.screenshot(path=SP+'horn_siren_a.png')
        await pg.wait_for_timeout(700);await pg.screenshot(path=SP+'horn_siren_b.png')
        await pg.evaluate("document.querySelector('#sheet .panel').scrollTop=2000");await pg.wait_for_timeout(200);await pg.screenshot(path=SP+'horn_siren_bottom.png')
        # ค่าที่แสดงตรงกับ HORN_PERK และแตะแถวเทียบ → เปลี่ยนหวูด
        await pg.click('.hrow[data-h="dragon"]');await pg.wait_for_timeout(1500)
        print('after tap',await pg.evaluate("document.getElementById('sheetTitle').textContent"),await pg.evaluate("document.querySelector('#sheetBody .perkbox').innerText.split('\\n').slice(0,3).join(' | ')"))
        await pg.evaluate("document.querySelector('#sheet .panel').scrollTop=0");await pg.wait_for_timeout(300);await pg.screenshot(path=SP+'horn_dragon.png')
        await pg.click('.hrow[data-h="classic"]');await pg.wait_for_timeout(1500);await pg.evaluate("document.querySelector('#sheet .panel').scrollTop=0");await pg.screenshot(path=SP+'horn_classic.png')
        await pg.click('#hTry');await pg.wait_for_timeout(300)
        await pg.click('#itBack');await pg.wait_for_timeout(300)
        print('back to shop',await pg.evaluate("document.getElementById('sheetTitle').textContent"),'errors',errs[:3])
        await ctx.close();await b.close()
asyncio.run(main())
