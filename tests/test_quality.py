# ทดสอบกราฟิก: ค่าเริ่มต้น 'สวยสุด' ไม่ลดเองแม้เครื่องช้า · ตั้งเป็น 'อัตโนมัติ' แล้วเครื่องช้า (CPU ช้าลง 12 เท่า) → ลดระดับเอง
# รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start  แล้ว python tests/test_quality.py
import asyncio
from playwright.async_api import async_playwright
URL = 'http://127.0.0.1:3456/'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        errs = []
        async def run(slow,gfx=None):
            ctx = await b.new_context(viewport={'width': 400, 'height': 800}, device_scale_factor=3, has_touch=True)
            pg = await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
            if slow:
                cdp = await ctx.new_cdp_session(pg); await cdp.send('Emulation.setCPUThrottlingRate', {'rate': 12})
            await pg.goto(URL); await pg.wait_for_timeout(800)
            if gfx: await pg.evaluate(f"setGfx('{gfx}')")
            await pg.evaluate("document.getElementById('sheet').classList.add('hidden')")
            await pg.evaluate("startGame('timed')"); await pg.evaluate("player.safe=999")
            q = []
            for _ in range(5):
                await pg.wait_for_timeout(3000); q.append(await pg.evaluate("[QUAL,DPR,cv.width]"))
            print(('slow' if slow else 'fast')+'/'+(gfx or 'default'), q)
            await ctx.close()
        await run(False); await run(True); await run(True,'auto')
        print('errors', errs[:3])
        await b.close()
asyncio.run(main())
