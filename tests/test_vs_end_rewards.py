# 2v2 จบแมตช์ต้องได้สรุปผล + เหรียญ/RP (12 พ.ย. 13:48 เจ้าของแจ้งว่าเด้งออกไม่ได้อะไร)
# ส่วน A: รัน PORT=3456 MATCH_SECS=20 VS_CD_MS=5000 node server.js  (ส่วน B เปิดเซิร์ฟเวอร์ 3458 เอง GRACEFUL=1 แล้ว SIGTERM ระหว่างแมตช์)
import asyncio,subprocess,os,signal,time
from playwright.async_api import async_playwright
ok=[]
def chk(n,c):ok.append(c);print(('✓ ' if c else '✗ ')+n)
async def mk(p,name,url):
    b=await p.chromium.launch();pg=await (await b.new_context(viewport={'width':700,'height':640})).new_page()
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.add_init_script(f"localStorage.setItem('wormName','{name}')");await pg.goto(url);await pg.wait_for_timeout(700)
    await pg.evaluate("document.getElementById('sheet').classList.add('hidden');prof.coins=0;prof.rp=500");pg._errs=errs;return pg
async def match(p,url,code,endfn):
    a=await mk(p,'เอ',url);b=await mk(p,'บี',url)
    for pg in (a,b):await pg.evaluate(f"openSheet('🌐 ออนไลน์ 2v2',renderOnlineJoin);netConnect('{code}','')");await pg.wait_for_timeout(700)
    for pg in (a,b):await pg.evaluate("netSend({t:'ready',v:true})")
    await a.wait_for_timeout(400);await a.evaluate("netSend({t:'start'})");await a.wait_for_timeout(1500)
    chk('เริ่มแมตช์',await a.evaluate("NET.phase==='play'"))
    for pg in (a,b):await pg.evaluate("player.ghost=999;player.safe=999;player.mass=400;player.maxMass=400;player.kills=3")
    await endfn(a,b)
    for nm,pg in (('A',a),('B',b)):
        r=await pg.evaluate("({ph:NET&&NET.phase,title:document.getElementById('sheetTitle').textContent,sheet:!document.getElementById('sheet').classList.contains('hidden'),pop:!!document.getElementById('rwPop'),coins:prof.coins,menu:!document.getElementById('menu').classList.contains('hidden')})")
        print('  ',nm,r);chk(nm+' ได้หน้าสรุปผล + ป๊อปอัปรางวัล',r['sheet'] and ('ชนะ' in r['title'] or 'แพ้' in r['title'] or 'เสมอ' in r['title']) and r['pop'])
        chk(nm+' ได้เหรียญ',r['coins']>0)   # ตายแล้วเกิดใหม่ ความยาวคิดแค่ชีวิตสุดท้าย (ข้อ 73)
    return a,b
async def main():
    async with async_playwright() as p:
        # A) จบแมตช์ปกติ
        async def wait_end(a,b):await a.wait_for_timeout(20000)
        a,b=await match(p,'http://127.0.0.1:3456/','END'+str(int(time.time())%1000),wait_end)
        await a.wait_for_timeout(9000)
        chk('ยังดูหน้าสรุปอยู่ 9 วิ → ไม่โดนดึงเข้าแมตช์ใหม่',await a.evaluate("NET.phase==='lobby'&&!document.getElementById('sheet').classList.contains('hidden')"))
        for pg in (a,b):
            await pg.evaluate("document.getElementById('rwPop')&&document.getElementById('rwPop').remove()");await pg.click('#toLobby');await pg.wait_for_timeout(300)
        await a.wait_for_timeout(6000);chk('กลับห้องรอครบ → นับ 5 วิแล้วเริ่มเอง',await a.evaluate("NET.phase==='play'"))
        # B) อัปเดตเซิร์ฟเวอร์ระหว่างเล่น → จบแมตช์ให้ก่อน
        env=dict(os.environ,PORT='3458',MATCH_SECS='300',GRACEFUL='1',RESET_SECS='8')
        srv=subprocess.Popen(['node','server.js'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1.5)
        async def term(a,b):
            await a.wait_for_timeout(3000);srv.send_signal(signal.SIGTERM);await a.wait_for_timeout(1500)
        try: await match(p,'http://127.0.0.1:3458/','UPD1',term)
        finally: srv.kill()
        print('PASS' if all(ok) else 'FAIL')
asyncio.run(main())
