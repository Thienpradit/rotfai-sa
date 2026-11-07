# รางวัลจบฤดูกาลตามอันดับ: ผู้เล่นฤดูกาล 2026-10 (12 คน) → เซิร์ฟเวอร์ถ่ายภาพนิ่งอันดับ → ล็อกอินแล้วได้เหรียญตามอันดับ + ปรับตามจำนวนคน
# สคริปต์นี้เขียน data/users.json ใหม่ (สำรองไฟล์เดิมเอง) แล้วรันเซิร์ฟเวอร์ PORT=3457 เอง
import asyncio, json, os, subprocess, time, hashlib, urllib.request, shutil
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));D=os.path.join(ROOT,'data')
def api(path,body=None,tok=None):
    req=urllib.request.Request('http://127.0.0.1:3457'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+tok} if tok else {})})
    with urllib.request.urlopen(req) as r: return json.loads(r.read())
async def main():
    bak=os.path.join(D,'users.json.testbak');shutil.copy(os.path.join(D,'users.json'),bak) if os.path.exists(os.path.join(D,'users.json')) else None
    # สร้างผู้เล่น 12 คน (รหัสผ่าน 'pass1234') ด้วย node (scrypt เหมือนเซิร์ฟเวอร์)
    js="""const c=require('crypto'),db={};for(let i=1;i<=12;i++){const s=c.randomBytes(16).toString('hex'),h=c.scryptSync('pass1234',s,32).toString('hex'),l='p'+i;
      db[l]={lname:l,name:'P'+i,salt:s,hash:h,rp:i===12?0:1300-i*100,updated:i,data:{coins:100,rp:i===12?0:1300-i*100,season:'2026-10',owned:{title:[]},eq:{},st:{},ach:{}}}}
      db.p13={...db.p1,lname:'p13',name:'P13',rp:5000,data:{...db.p1.data,rp:5000,season:'2026-11'}};require('fs').writeFileSync(process.argv[1],JSON.stringify(db))"""
    subprocess.run(['node','-e',js,os.path.join(D,'users.json')],check=True)
    for f in ['seasons.json']:
        if os.path.exists(os.path.join(D,f)): os.remove(os.path.join(D,f))
    srv=subprocess.Popen(['node','server.js'],cwd=ROOT,env={**os.environ,'PORT':'3457'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT);time.sleep(1.5)
    try:
        st=api('/api/status');snap=json.load(open(os.path.join(D,'seasons.json')))
        print('snapshot 2026-10: n =',snap['2026-10']['n'],'p1 =',snap['2026-10']['ranks'].get('p1'),'p12 (rp 0) =',snap['2026-10']['ranks'].get('p12'))
        for who in ['p1','p2','p5','p12']:
            j=api('/api/login',{'name':who.upper(),'pass':'pass1234'});print(who,'prize',j['prize'])
        j=api('/api/login',{'name':'P2','pass':'pass1234'});tok=j['token']
        # เครื่องผู้เล่น: เปิดเกมแบบล็อกอินอยู่ → ได้เหรียญ + ฉายา + RP ครึ่ง แล้วบันทึกผ่านกันโกง
        async with async_playwright() as p:
            b=await p.chromium.launch();ctx=await b.new_context(**p.devices['iPhone 13']);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.add_init_script(f"localStorage.setItem('rsAuth',JSON.stringify({{name:'P2',token:'{tok}'}}))")
            await pg.goto('http://127.0.0.1:3457/');await pg.wait_for_timeout(1500)
            print('client after roll:',await pg.evaluate("[prof.coins,prof.rp,prof.season,prof.owned.title]"),'| announce:',await pg.evaluate("(document.getElementById('ann')||{}).textContent||''"))
            await pg.evaluate("pushProf&&pushProf()");await pg.wait_for_timeout(1200)
            me=api('/api/me',tok=tok);print('server saved:',me['data']['coins'],me['data']['rp'],me['data']['season'],'prize now',me['prize'])
            # หน้าแรงก์: ตารางรางวัล (ฤดูกาลนี้มี p13 + P2 = 2 คน)
            await pg.evaluate("document.getElementById('sheet').classList.add('hidden');openSheet('🏆 แรงก์',renderRanks)");await pg.wait_for_timeout(800)
            await pg.evaluate("document.getElementById('przBox').scrollIntoView()");await pg.wait_for_timeout(200)
            await pg.screenshot(path='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad/season_prize.png')
            print('prize box:',(await pg.evaluate("document.getElementById('przBox').innerText")).replace('\n',' | ')[:400])
            print('errors',errs[:3]);await b.close()
    finally:
        srv.terminate();
        if bak and os.path.exists(bak): shutil.move(bak,os.path.join(D,'users.json'))
        if os.path.exists(os.path.join(D,'seasons.json')): os.remove(os.path.join(D,'seasons.json'))
asyncio.run(main())
