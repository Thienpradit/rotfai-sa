# ป้ายหมุนแนวนอนบนมือถือ (#rotTip) โชว์ครั้งแรกครั้งเดียว: รันเซิร์ฟเวอร์ PORT=3456 ก่อน
import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch();ok=True
    ctx=await b.new_context(**p.devices['iPhone 13']);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    vis=lambda:pg.evaluate("!$('rotTip').classList.contains('hidden')")
    await pg.goto('http://localhost:3456/?rot=1');await pg.wait_for_timeout(1800)
    a=await vis();await pg.set_viewport_size({'width':844,'height':390});await pg.wait_for_timeout(600);b1=await vis()
    await pg.set_viewport_size({'width':390,'height':844});await pg.wait_for_timeout(1800);c=await vis()
    await pg.reload();await pg.wait_for_timeout(1800);d=await vis()
    print('first visit shown',a,'| rotated hidden',not b1,'| back portrait (same visit) not shown',not c,'| reload not shown',not d)
    ok&=a and not b1 and not c and not d
    # ผู้เล่นใหม่อีกเครื่อง: กด "เล่นแนวตั้งต่อ" → ไม่ขึ้นอีกแม้โหลดใหม่
    ctx2=await b.new_context(**p.devices['iPhone 13']);pg=await ctx2.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto('http://localhost:3456/?rot=1');await pg.wait_for_timeout(1800);e=await vis()
    await pg.click('#rtSkip');await pg.wait_for_timeout(300);f=await vis();await pg.reload();await pg.wait_for_timeout(1800);g=await vis()
    print('new phone shown',e,'| skip hides',not f,'| reload not shown',not g);ok&=e and not f and not g
    pg=await b.new_page(viewport={'width':500,'height':900});await pg.goto('http://localhost:3456/?rot=1');await pg.wait_for_timeout(1500)
    h=await pg.evaluate("!$('rotTip').classList.contains('hidden')");print('desktop not shown',not h);ok&=not h
    print('errors',errs);print('PASS' if ok and not errs else 'FAIL');await b.close()
asyncio.run(main())
