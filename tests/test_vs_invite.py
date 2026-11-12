# 2v2 ชวนผู้เล่น / กดพร้อม / นับถอยหลัง (12 พ.ย. 2026) · รัน: PORT=3456 MATCH_SECS=40 VS_CD_MS=5000 node server.js
import asyncio
from playwright.async_api import async_playwright
URL='http://127.0.0.1:3456/'
async def mk(p,name):
    b=await p.chromium.launch();pg=await (await b.new_context(viewport={'width':700,'height':640})).new_page()
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.add_init_script(f"localStorage.setItem('wormName','{name}')");await pg.goto(URL);await pg.wait_for_timeout(700)
    await pg.evaluate("document.getElementById('sheet').classList.add('hidden')");pg._errs=errs;return pg
async def vsJoin(pg,code):
    await pg.evaluate(f"openSheet('🌐 ออนไลน์ 2v2',renderOnlineJoin);netConnect('{code}','')");await pg.wait_for_timeout(900)
ok=[]
def chk(name,cond):ok.append(cond);print(('✓ ' if cond else '✗ ')+name)
async def main():
    async with async_playwright() as p:
        # 1) คนเดียว ไม่มีใครออนไลน์ → ไม่มีปุ่ม เริ่มเองใน ~3 วิ
        s=await mk(p,'เดี่ยว');await vsJoin(s,'SOLO1')
        chk('solo: ไม่มีปุ่มเริ่ม/ชวน',await s.evaluate("!document.getElementById('startBtn')&&!document.getElementById('invBtn')&&!!document.getElementById('lobCd')"))
        await s.wait_for_timeout(3800);chk('solo: เริ่มเองกับบอท',await s.evaluate("NET.phase==='play'"))
        await s.evaluate("netLeave()");await s.wait_for_timeout(400)
        # 2) A อยู่โลกออนไลน์ · C เล่นผจญภัย · B เปิดห้อง 2v2 → มีปุ่มชวน
        a=await mk(p,'เอ');await a.evaluate("playEndless()");await a.wait_for_timeout(1500)
        c=await mk(p,'ซี');await c.evaluate("startStage(0)");await c.wait_for_timeout(1500)
        b=await mk(p,'บี');await vsJoin(b,'INV22')
        chk('B: มีปุ่มชวน + เริ่มเลย',await b.evaluate("!!document.getElementById('invBtn')&&!!document.getElementById('startBtn')&&!document.getElementById('startBtn').disabled"))
        print('  avail',await b.evaluate("NET.avail"),await b.evaluate("document.getElementById('invBtn').textContent"))
        await b.click('#invBtn');await b.wait_for_timeout(700)
        print('  ',await b.evaluate("document.getElementById('invMsg').textContent"))
        chk('A (ออนไลน์) ได้คำชวน',await a.evaluate("!document.getElementById('invTip').classList.contains('hidden')"))
        chk('C (ผจญภัย) ได้คำชวน',await c.evaluate("!document.getElementById('invTip').classList.contains('hidden')"))
        print('  A sees:',await a.evaluate("document.getElementById('invTip').innerText.replace(/\\n/g,' | ')"))
        await a.screenshot(path='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad/inv_a.png')
        await a.click('#invYes');await a.wait_for_timeout(1500)
        chk('A เข้าห้อง B แล้ว',await a.evaluate("!!NET&&!NET.ffa&&NET.room==='INV22'&&NET.players.size===2"))
        chk('2 คน: ปุ่มพร้อม + เล่นเลยกดไม่ได้ + นับถอยหลัง',await b.evaluate("!!document.getElementById('readyBtn')&&document.getElementById('startBtn').disabled&&/เริ่มอัตโนมัติ/.test(document.getElementById('lobCd').textContent)"))
        await b.screenshot(path='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad/inv_lobby.png')
        await a.click('#readyBtn');await b.click('#readyBtn');await b.wait_for_timeout(500)
        chk('ทุกคนพร้อม → เล่นเลยกดได้',await b.evaluate("!document.getElementById('startBtn').disabled"))
        await a.screenshot(path='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad/inv_ready.png')
        await a.click('#startBtn');await a.wait_for_timeout(900)
        chk('เริ่มแมตช์ (คนที่ไม่ใช่หัวหน้ากดได้เมื่อทุกคนพร้อม)',await b.evaluate("NET.phase==='play'"))
        # 3) นับถอยหลังหมด → เริ่มเองแม้ยังไม่พร้อม (VS_CD_MS=5000)
        d=await mk(p,'ดี');e=await mk(p,'อี');await vsJoin(d,'CDN33');await vsJoin(e,'CDN33')
        chk('ยังไม่พร้อมทั้งคู่ ยังไม่เริ่ม',await d.evaluate("NET.phase==='lobby'"))
        await d.wait_for_timeout(5600);chk('ครบเวลา → เริ่มเอง',await d.evaluate("NET.phase==='play'"))
        errs=s._errs+a._errs+b._errs+c._errs+d._errs+e._errs;print('errors',errs[:3])
        print('PASS' if all(ok) and not errs else 'FAIL')
asyncio.run(main())
