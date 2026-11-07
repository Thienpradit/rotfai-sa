# อัปเดตเซิร์ฟเวอร์: เครื่องเก่า (A) เห็นว่าที่อยู่สาธารณะ (B) เป็นเวอร์ชันใหม่ → ส่ง reset ให้ทุกคน → นับถอยหลัง → ออกจากเกม (ไม่หักแต้ม) → โหลดหน้าใหม่
# + ผู้เล่นหน้าเมนู: ถาม /version แล้วไม่ตรง → นับถอยหลัง 15 วิ · รันเซิร์ฟเวอร์เอง (พอร์ต 3461/3462)
import asyncio, os, subprocess, time
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(port,ver,extra={}): return subprocess.Popen(['node','server.js'],cwd=ROOT,env={**os.environ,'PORT':str(port),'APP_VERSION':ver,**extra},stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
async def main():
    A=run(3461,'oldver'); time.sleep(1.2)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch();ctx=await b.new_context(**p.devices['iPhone 13']);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
            loads=[];pg.on('load',lambda: loads.append(time.time()))
            await pg.goto('http://127.0.0.1:3461/');await pg.wait_for_timeout(800)
            print('APP_VER in page:',await pg.evaluate('APP_VER'))
            await pg.evaluate("document.getElementById('sheet').classList.add('hidden');playEndless()");await pg.wait_for_timeout(2500)
            await pg.evaluate("player.mass=player.maxMass=900;prof.rp=700");rp0=await pg.evaluate('prof.rp')
            # เปิดเครื่องใหม่ (B) แล้วให้ A คอยถาม B
            B=run(3462,'newver');time.sleep(1.0)
            A.terminate();A.wait();A2=run(3461,'oldver',{'SELF_URL':'http://127.0.0.1:3462','RESET_SECS':'6','VERSION_POLL_MS':'1000'})
            time.sleep(1.2)
            # หน้าเว็บต่อ A2 ใหม่ (A เดิมปิดไปแล้ว) → เข้าโลกอีกครั้ง
            await pg.reload();await pg.wait_for_timeout(800);loads.clear()
            await pg.evaluate("document.getElementById('sheet').classList.add('hidden');playEndless()");await pg.wait_for_timeout(1500)
            await pg.evaluate("player.mass=player.maxMass=900");rp0=await pg.evaluate('prof.rp')
            await pg.wait_for_timeout(1500)
            print('banner:',await pg.evaluate("document.getElementById('resetBar').classList.contains('hidden')?'(hidden)':document.getElementById('resetTxt').innerText.replace(/\\n/g,' | ')"))
            await pg.screenshot(path='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad/reset_bar.png')
            await pg.wait_for_timeout(5200)
            print('at zero: state',await pg.evaluate("[state,document.getElementById('resetTxt').textContent]"),'roundRP',await pg.evaluate('roundRP'))
            await pg.wait_for_timeout(3000)
            print('page reloaded:',len(loads)>0,'| errors',errs[:3])
            # เมนู: เวอร์ชันไม่ตรง → 15 วิ
            pg2=await ctx.new_page();await pg2.goto('http://127.0.0.1:3462/');await pg2.wait_for_timeout(600)
            await pg2.evaluate("startResetCountdown(inGameNow()||NET?60:15)");await pg2.wait_for_timeout(400)
            print('menu banner:',await pg2.evaluate("document.getElementById('resetTxt').innerText.replace(/\\n/g,' | ')"))
            await b.close()
        A2.terminate();B.terminate()
    finally:
        A.terminate()
asyncio.run(main())
