# 📶 เน็ตขาดช่วงระหว่างเล่น → ต่อใหม่เองแล้วเล่นต่อในโลกเดิม ขบวนเดิม (17 พ.ย.) · รันเซิร์ฟเวอร์ PORT=3469 เอง
import asyncio, os, subprocess, time, sys, json, urllib.request
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));URL='http://127.0.0.1:3469'
ok=0;bad=0
def check(c,msg):
    global ok,bad
    if c: ok+=1;print('  ✓',msg)
    else: bad+=1;print('  ✗',msg)
def wsinfo(): return json.load(urllib.request.urlopen(URL+'/wsinfo'))
async def main():
    srv=subprocess.Popen(['node','server.js'],cwd=ROOT,env={**os.environ,'PORT':'3469','RESUME_MS':'5000','PING_MS':'1500'},stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT);time.sleep(1.5)
    try:
        async with async_playwright() as p:
            bs=[]
            async def page(name):
                b=await p.chromium.launch();bs.append(b);pg=await (await b.new_context(viewport={'width':900,'height':700})).new_page()
                errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));await pg.goto(URL);await pg.wait_for_timeout(1200)
                if await pg.is_visible('#acGuest'): await pg.click('#acGuest');await pg.wait_for_timeout(300)
                await pg.evaluate(f"try{{localStorage.setItem('wormName','{name}')}}catch(e){{}}")
                await pg.click('#playInf');await pg.wait_for_timeout(300);await pg.click('.omode[data-k=normal]')
                await pg.wait_for_function("state==='play'&&player&&NET&&NET.id");await pg.evaluate("player.die=function(){};0");await pg.wait_for_timeout(1500)   # เทสต์: ไม่ให้ตายเพราะบอทระหว่างรอ
                await pg.evaluate("window.__left=[];const o=netMsg;netMsg=m=>{if(m.t==='left')__left.push(m.id);o(m)};0")
                return pg,errs
            A,eA=await page('เอ');B,eB=await page('บี')
            info=await A.evaluate("[NET.id,NET.room,!!NET.rkey,state]");check(info[2] and info[3]=='play','ได้ rkey ตอนเข้าโลก '+str(info))
            check((await B.evaluate("NET.room"))==info[1],'สองคนอยู่โลกเดียวกัน')
            # ping ทุก 1.5 วิ ต้องไม่ตัดสายที่ปกติ
            await A.wait_for_timeout(5000)
            check(await A.evaluate("!!NET&&NET.ws.readyState===1&&!NET.reconn&&state==='play'"),'ping/pong ไม่ตัดสายปกติ (เล่นมา 5 วิ)')
            # 1) สายเงียบ (ข้อมูลไม่มา) → ต่อใหม่เองภายในไม่กี่วิ ได้ id เดิม ขบวนเดิม
            await A.evaluate("window.__nw=[];const _nw=netWarn;netWarn=(on,t)=>{if(on)__nw.push(document.getElementById('netWarn')?1:0);_nw(on,t);if(on)__nw.push(document.getElementById('netWarn').textContent)};player.mass=300;player.safe=0;player.ghost=0;NET.ws.onmessage=()=>{};0")   # จำลองสัญญาณหาย: สายยังเปิดแต่ข้อมูลไม่มา
            await A.wait_for_timeout(3000)
            w=await A.evaluate("[PERF.rc,__nw.join(' '),player.safe>0,player.ghost>0]")
            check(w[0]>=1 and 'ต่อใหม่' in w[1],'ข้อมูลไม่มา > 2.5 วิ → ขึ้นป้ายกำลังต่อใหม่ '+str(w))
            check(w[2] and w[3],'ระหว่างต่อใหม่ เรามีเกราะ+เป็นผี (ไม่ตายเพราะรถไฟค้างบนจอ)')
            await A.wait_for_timeout(2500)
            r=await A.evaluate("[NET&&NET.id,NET&&!NET.reconn,state,player&&player.alive,Math.round(player.mass),!!document.getElementById('netWarn'),NET&&NET.ws.readyState]")
            check(r[0]==info[0] and r[1] and r[2]=='play' and r[3],'ต่อกลับแล้ว id เดิม เล่นต่อ '+str(r))
            check(r[4]>=290,'ขบวนยาวเท่าเดิม (ไม่ได้เกิดใหม่) '+str(r[4]))
            check(not r[5],'ป้ายสัญญาณหายไปแล้ว')
            await A.wait_for_timeout(1500)
            ok1=await A.evaluate("(()=>{const w=worms.find(o=>o.isRemote&&o.isBot&&o.alive);if(!w)return false;const a=w.pts[0].x;return new Promise(r=>setTimeout(()=>r(Math.abs(w.pts[0].x-a)>1),500))})()")
            check(ok1,'หลังต่อกลับ รถไฟคนอื่นวิ่งต่อ ไม่ค้าง')
            check(info[0] not in await B.evaluate("__left"),'อีกเครื่องไม่เห็นเราออกจากโลก')
            check(await B.evaluate(f"!!worms.find(o=>o.netId==={info[0]}&&o.alive)"),'อีกเครื่องยังเห็นขบวนเรา')
            # 2) สายหลุดจริง (close) → ต่อใหม่เหมือนกัน
            await A.evaluate("NET.ws.close();0");await A.wait_for_timeout(2500)
            r=await A.evaluate("[NET&&NET.id,NET&&!NET.reconn,state,player&&player.alive]")
            check(r[0]==info[0] and r[1] and r[2]=='play' and r[3],'สายหลุด (close) → ต่อกลับ id เดิม '+str(r))
            ws=wsinfo()['resume'];check(ws['ok']>=2,'เซิร์ฟเวอร์นับต่อกลับสำเร็จ '+str(ws))
            # 3) ต่อไม่ได้เลย → เซิร์ฟเวอร์ปล่อยขบวนหลัง RESUME_MS · เครื่องเราสรุปผล (ไม่เด้งหน้าแรกเสียเหรียญ)
            await A.evaluate("window.WebSocket=function(){throw new Error('no net')};NET.ws.onmessage=()=>{};0")
            await B.wait_for_timeout(9000)
            check(info[0] in await B.evaluate("__left"),'ต่อไม่ได้นานเกิน RESUME_MS → อีกเครื่องเห็นเราออก')
            await A.wait_for_timeout(8000)
            r=await A.evaluate("[NET,state,!document.getElementById('over').classList.contains('hidden'),document.getElementById('overTitle').textContent,!!document.getElementById('netWarn')]")
            check(r[0] is None and r[1]=='over' and r[2],'ต่อไม่ได้ 14 วิ → หน้าสรุปผล (ไม่เสียเหรียญ) '+str(r))
            check(not r[4],'ป้ายสัญญาณหาย')
            errs=eA+eB;check(not errs,'ไม่มี error '+str(errs[:3]))
            for b in bs: await b.close()
    finally:
        srv.terminate();srv.wait()
    print(f'{ok} ผ่าน · {bad} ไม่ผ่าน');print('PASS' if not bad else 'FAIL');sys.exit(1 if bad else 0)
asyncio.run(main())
