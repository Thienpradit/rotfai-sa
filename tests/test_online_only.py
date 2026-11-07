# ตารางอันดับนับเฉพาะโหมดออนไลน์ + เอาโหมดเล่นกับบอทออก (7 พ.ย.)
# A, B (เคยเล่นกับบอท) → ยกคะแนนเดิมมาทั้งคู่ · ต่อจากนี้นับเพิ่มเฉพาะออนไลน์
# เขียน data/users.json ใหม่ (สำรอง/คืนให้เอง) แล้วรันเซิร์ฟเวอร์ PORT=3457 เอง
import asyncio, json, os, subprocess, time, urllib.request, shutil
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));D=os.path.join(ROOT,'data');U=os.path.join(D,'users.json')
def api(path,body=None,tok=None):
    req=urllib.request.Request('http://127.0.0.1:3457'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+tok} if tok else {})})
    with urllib.request.urlopen(req) as r: return json.loads(r.read())
def top(by,tok=None): j=api('/api/top?by='+by,tok=tok);return [(u['name'],u['val']) for u in j['top']],j.get('me')
async def main():
    bak=U+'.testbak';had=os.path.exists(U)
    if had: shutil.copy(U,bak)
    js="""const c=require('crypto'),db={},mk=(l,n,d)=>{const s=c.randomBytes(16).toString('hex');db[l]={lname:l,name:n,salt:s,hash:c.scryptSync('pass1234',s,32).toString('hex'),rp:d.rp,updated:1,data:{coins:0,season:'2026-11',owned:{title:[]},eq:{},ach:{},...d}}};
      mk('aa','AA',{rp:500,st:{kills:20,maxLen:900},best:{online:900}});mk('bb','BB',{rp:800,st:{kills:50,maxLen:2000},best:{online:300,hard:2000}});
      require('fs').writeFileSync(process.argv[1],JSON.stringify(db))"""
    subprocess.run(['node','-e',js,U],check=True)
    srv=subprocess.Popen(['node','server.js'],cwd=ROOT,env={**os.environ,'PORT':'3457'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT);time.sleep(1.5)
    try:
        for by in ['rp','kills','len']: print('top',by,top(by)[0])
        tok=api('/api/login',{'name':'BB','pass':'pass1234'})['token']
        async with async_playwright() as p:
            b=await p.chromium.launch();ctx=await b.new_context(**p.devices['iPhone 13']);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.add_init_script(f"localStorage.setItem('rsAuth',JSON.stringify({{name:'BB',token:'{tok}'}}))")
            await pg.goto('http://127.0.0.1:3457/');await pg.wait_for_timeout(1200)
            print('menu buttons:',await pg.evaluate("[...document.querySelectorAll('.btn.play .bt')].map(x=>x.textContent)"),'| playBot exists:',await pg.evaluate("!!document.getElementById('playBot')"))
            print('client start:',await pg.evaluate("[prof.rp,prof.onrp,prof.st.okills,prof.st.omaxLen]"))
            # ออฟไลน์ (ต่อเซิร์ฟเวอร์ไม่ได้ → เล่นกับบอทในเครื่อง) ไม่ได้ RP
            await pg.evaluate("document.getElementById('sheet').classList.add('hidden');endlessFallback()");await pg.wait_for_timeout(500)
            await pg.evaluate("player.mass=player.maxMass=1200;finish(false,true)");print('after offline game:',await pg.evaluate("[prof.rp,prof.onrp,roundRP]"))
            await pg.evaluate("document.getElementById('over').classList.add('hidden');toMenu()");await pg.wait_for_timeout(300)
            # ออนไลน์: เข้าโลก แล้วออก (ยาว 1200) → +20 RP ทั้ง rp และ onrp
            await pg.evaluate("playEndless()");await pg.wait_for_timeout(2500)
            print('online state:',await pg.evaluate("[!!NET,NET&&NET.ffa,state]"))
            await pg.evaluate("player.mass=player.maxMass=1200;player.kills=0;finish(false,true)");await pg.wait_for_timeout(200)
            print('after online game:',await pg.evaluate("[prof.rp,prof.onrp,roundRP,prof.st.omaxLen]"))
            await pg.evaluate("pushProf()");await pg.wait_for_timeout(1200)
            me=api('/api/me',tok=tok)['data'];print('server:',me['rp'],me['onrp'],me['st'].get('okills'),me['st'].get('omaxLen'))
            for by in ['rp','len']: print('top',by,top(by,tok))
            await pg.evaluate("document.getElementById('over').classList.add('hidden');openSheet('🏆 แรงก์',renderRanks)");await pg.wait_for_timeout(900)
            print('lb note:',await pg.evaluate("[...document.querySelectorAll('#lbList .lbnote')].map(x=>x.textContent)"))
            print('errors',errs[:3]);await b.close()
    finally:
        srv.terminate()
        if had: shutil.move(bak,U)
        sp=os.path.join(D,'seasons.json')
        if os.path.exists(sp): os.remove(sp)
asyncio.run(main())
