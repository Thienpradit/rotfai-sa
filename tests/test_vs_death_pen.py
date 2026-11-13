# 2v2 ตายตอนยาวไม่ถึงเกณฑ์แรงก์ → ไม่หัก RP (เจ้าของสั่งเอาออก 13 พ.ย. 10:10 · เดิมหักตามข้อ 129) · รัน: PORT=3456 MATCH_SECS=20 VS_CD_MS=5000 node server.js
import asyncio,time
from playwright.async_api import async_playwright
ok=[]
def chk(n,c):ok.append(c);print(('✓ ' if c else '✗ ')+n)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await (await b.new_context(viewport={'width':800,'height':640})).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(700)
        await pg.evaluate("document.getElementById('sheet').classList.add('hidden');prof.rp=1000;prof.onrp=1000")   # แรงก์เงิน (ต้องยาว 175 · หัก 8)
        await pg.evaluate("openSheet('🌐 ออนไลน์ 2v2',renderOnlineJoin);netConnect('PEN"+str(int(time.time())%1000)+"','')");await pg.wait_for_timeout(900)
        await pg.evaluate("netSend({t:'start'})");await pg.wait_for_timeout(1500)
        chk('เริ่มแมตช์',await pg.evaluate("NET.phase==='play'"))
        need,loss=await pg.evaluate("[rpNeed(rankOf(prof.rp).t),rpLoss(rankOf(prof.rp).t)]")
        r0=await pg.evaluate("prof.rp")
        await pg.evaluate("player.ghost=0;player.safe=0;player.maxMass=60;player.die(null)");await pg.wait_for_timeout(500)
        r1=await pg.evaluate("prof.rp");chk(f'ตายตอนยาว 60 (ต้อง {need}) → ไม่หัก RP ({r0}→{r1})',r1==r0)
        await pg.wait_for_timeout(3500)
        chk('เกิดใหม่แล้ว',await pg.evaluate("!!player&&player.alive"))
        await pg.evaluate(f"player.ghost=0;player.safe=0;player.maxMass={need+50};player.die(null)");await pg.wait_for_timeout(500)
        r2=await pg.evaluate("prof.rp");chk(f'ตายตอนยาวเกินเกณฑ์ → ไม่หัก ({r1}→{r2})',r2==r1)
        await pg.wait_for_timeout(3500);await pg.evaluate("player.ghost=999;player.safe=999")
        await pg.wait_for_timeout(15000)
        pop=await pg.evaluate("document.getElementById('rwPop')&&document.getElementById('rwPop').textContent||''")
        chk('ป๊อปอัปรางวัลไม่มีบรรทัดหัก RP',('ยาวไม่ถึงเกณฑ์' not in pop) and len(pop)>0)
        rp=await pg.evaluate("NET.lastEnd&&NET.lastEnd.rp")
        chk(f'ผลรอบรวมที่โดนหักด้วย (RP รอบนี้ {rp} · เปลี่ยนจริง {await pg.evaluate("prof.rp")-r0})',rp==await pg.evaluate("prof.rp")-r0)
        chk('ไม่มี error',not errs);print(errs[:3])
        print('PASS' if all(ok) else 'FAIL');await b.close()
asyncio.run(main())
