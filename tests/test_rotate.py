# ป้ายหมุนแนวนอนบนมือถือ (#rotTip): รันเซิร์ฟเวอร์ PORT=3456 ก่อน
import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    # iPhone แนวตั้ง
    ctx=await b.new_context(**p.devices['iPhone 13']);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto('http://localhost:3456/?rot=1');await pg.wait_for_timeout(1800)
    print('iphone portrait shown',await pg.evaluate("!$('rotTip').classList.contains('hidden')"),await pg.evaluate("$('rtLock').textContent"))
    await pg.set_viewport_size({'width':844,'height':390});await pg.wait_for_timeout(600)
    print('after rotate hidden',await pg.evaluate("$('rotTip').classList.contains('hidden')"))
    await pg.set_viewport_size({'width':390,'height':844});await pg.wait_for_timeout(600)
    print('back portrait shown',await pg.evaluate("!$('rotTip').classList.contains('hidden')"))
    await pg.click('#rtSkip');await pg.wait_for_timeout(300)
    print('skip hidden',await pg.evaluate("$('rotTip').classList.contains('hidden')"))
    await pg.reload();await pg.wait_for_timeout(1500)
    print('after reload (same session) hidden',await pg.evaluate("$('rotTip').classList.contains('hidden')"),errs)
    await ctx.close()
    # คอม: ไม่ขึ้น
    pg=await b.new_page(viewport={'width':500,'height':900});await pg.goto('http://localhost:3456/');await pg.wait_for_timeout(1500)
    print('desktop shown',await pg.evaluate("!$('rotTip').classList.contains('hidden')"))
    await b.close()
asyncio.run(main())
