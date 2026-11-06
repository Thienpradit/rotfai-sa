# ภาพหน้าจอ iPhone: ตารางอันดับเล็ก, ปุ่มซ้าย/ขวา (ตั้งค่า ⚙️), หน้าจบเกมกะทัดรัด · รันเซิร์ฟเวอร์ก่อน PORT=3456 npm start
# ภาพบันทึกใน SP (แก้ path ได้)
import asyncio
from playwright.async_api import async_playwright
SP='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad/'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for name,dev,side in [('iphone',p.devices['iPhone 13'],'R'),('iphoneL',p.devices['iPhone 13 landscape'],'R'),('iphoneL_left',p.devices['iPhone 13 landscape'],'L'),('iphone_left',p.devices['iPhone 13'],'L'),('se',p.devices['iPhone SE'],'R'),('desk',{'viewport':{'width':1280,'height':800}},'R')]:
            ctx=await b.new_context(**dev);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(700)
            await pg.evaluate("document.getElementById('sheet').classList.add('hidden');document.getElementById('fsTip').classList.add('hidden')")
            if name=='se':await pg.screenshot(path=SP+f'after_{name}_menu.png')
            if side=='L':
                await pg.click('#setMenu');await pg.wait_for_timeout(300)
                if name=='iphone_left':await pg.screenshot(path=SP+f'after_{name}_settings.png')
                await pg.click('#segSide div[data-v=L]');await pg.wait_for_timeout(100);await pg.click('#setDone')
            await pg.evaluate("startGame('inf')");await pg.wait_for_timeout(1500)
            await pg.evaluate("player.tgs=1;player.bombT=[15];player.gold=1;player.goldT=30");await pg.wait_for_timeout(400)
            await pg.screenshot(path=SP+f'after_{name}_play.png')
            await pg.evaluate("player.die(null)");await pg.wait_for_timeout(1800)
            await pg.screenshot(path=SP+f'after_{name}_over.png')
            print(name,errs[:2],await pg.evaluate("[SIDE,localStorage.getItem('trainSide')]"));await ctx.close()
        await b.close()
asyncio.run(main())
