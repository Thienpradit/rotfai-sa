# รางวัลอัญมณีจริง + ตรวจโกง + แบน + ผู้ดูแล (13 พ.ย. 2026)
# รันเซิร์ฟเวอร์ PORT=3457 เอง (ADMINS=boss1, GEM_EXTRA=2026-10:3) · สำรอง/คืน data/users.json + seasons.json
import asyncio, json, os, subprocess, time, urllib.request, urllib.error, shutil
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));D=os.path.join(ROOT,'data')
SP=os.environ.get('SHOTS','/tmp')
def api(path,body=None,tok=None):
    req=urllib.request.Request('http://127.0.0.1:3457'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+tok} if tok else {})})
    try:
        with urllib.request.urlopen(req) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e: return {'_status':e.code,**json.loads(e.read() or b'{}')}
def login(n): return api('/api/login',{'name':n,'pass':'pass1234'})
ok=0;bad=0
def check(c,msg):
    global ok,bad
    if c: ok+=1;print('  ✓',msg)
    else: bad+=1;print('  ✗',msg)
async def main():
    bak={f:os.path.join(D,f+'.gembak') for f in ('users.json','seasons.json')}
    for f,b in bak.items():
        if os.path.exists(os.path.join(D,f)): shutil.copy(os.path.join(D,f),b)
    AUD=lambda sec,g,k: {'2026-10':{'sec':sec,'g':g,'k':k,'ml':900,'fix':0,'rp0':100}}
    users=[('w1',900,AUD(3000,20,40)),('cheat',800,AUD(120,1,0)),('w2',700,AUD(2400,15,20)),('w3',600,AUD(2000,12,10)),('w4',500,AUD(1800,10,8)),('boss1',0,None)]
    js="""const c=require('crypto'),db={},U=JSON.parse(process.argv[2]);for(const [l,rp,aud] of U){const s=c.randomBytes(16).toString('hex'),h=c.scryptSync('pass1234',s,32).toString('hex');
      db[l]={lname:l,name:l.toUpperCase(),salt:s,hash:h,rp,updated:rp,audit:aud||undefined,data:{coins:100,rp,onrp:rp,onv:2,season:l==='boss1'?'2026-11':'2026-10',owned:{title:[]},eq:{},st:{okills:5,omaxLen:900,games:9},ach:{}}}}
      require('fs').writeFileSync(process.argv[1],JSON.stringify(db))"""
    subprocess.run(['node','-e',js,os.path.join(D,'users.json'),json.dumps(users)],check=True)
    if os.path.exists(os.path.join(D,'seasons.json')): os.remove(os.path.join(D,'seasons.json'))
    srv=subprocess.Popen(['node','server.js'],cwd=ROOT,env={**os.environ,'PORT':'3457','ADMINS':'boss1','GEM_EXTRA':'2026-10:3'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT);time.sleep(1.8)
    try:
        se=api('/api/season?key=2026-10');print('season 2026-10:',[(t['pos'],t['name']) for t in se['top']])
        check(se['top'][0]['name']=='W1' and 'l' not in se['top'][0],'ผลจบฤดูกาลบันทึกไว้ (ไม่มี lname หลุดออกไป)')
        j=login('W1');check(j.get('gem',{}).get('place')==1 and len(j['gem']['code'])==9,'W1 ได้อันดับรางวัล 1 + รหัส '+str(j.get('gem')))
        c1=j['gem']['code'];w1tok=j['token']
        j=login('CHEAT');check(j.get('gem',{}).get('review') is True,'CHEAT เล่นจริง 2 นาที → ตัดสิทธิ์ (กำลังตรวจสอบ)')
        j=login('W2');check(j.get('gem',{}).get('place')==2,'W2 เลื่อนเป็นรางวัลที่ 2');w2tok=j['token']
        j=login('W4');check(j.get('gem') is None,'W4 ไม่ได้รางวัล')
        b=login('BOSS1');tok=b['token'];check(b.get('admin') is True,'BOSS1 เป็นผู้ดูแล')
        check(api('/api/admin/review?key=2026-10',tok=w1tok).get('_status')==403,'คนทั่วไปเข้าหน้าผู้ดูแลไม่ได้')
        r=api('/api/admin/review?key=2026-10',tok=tok);print('  review:',[(x['name'],x['status'],x['place']) for x in r['rows']])
        check([x['place'] for x in r['rows']][:5]==[1,0,2,3,0],'ลำดับผู้ชนะ W1/W2/W3 (ข้าม CHEAT)')
        check(api('/api/admin/claim?code='+c1,tok=tok).get('name')=='W1','ตรวจรหัสรับรางวัล W1 ถูกต้อง')
        check(api('/api/admin/claim?code=AAAA-BBBB',tok=tok).get('ok') is False,'รหัสมั่วไม่ผ่าน')
        api('/api/admin/ban',{'name':'W2','why':'แก้ RP'},tok=tok)
        r=api('/api/admin/review?key=2026-10',tok=tok);print('  after ban W2:',[(x['name'],x['status'],x['place']) for x in r['rows']])
        check([x['place'] for x in r['rows']][:5]==[1,0,0,2,3],'แบน W2 → W3 ที่ 2, W4 ที่ 3')
        j=login('W2');check(j.get('_status')==403 and 'ระงับ' in j.get('err',''),'W2 ล็อกอินไม่ได้: '+j.get('err',''))
        check(api('/api/save',{'data':{}},tok=w2tok).get('_status')==403,'W2 บันทึกข้อมูลไม่ได้')
        check(all(t['name']!='W2' for t in api('/api/top?by=kills')['top']),'W2 หายจากตารางอันดับ')
        api('/api/admin/allow',{'name':'CHEAT','key':'2026-10','v':True},tok=tok)
        r=api('/api/admin/review?key=2026-10',tok=tok);print('  after allow CHEAT:',[(x['name'],x['status'],x['place']) for x in r['rows']])
        check([x['place'] for x in r['rows']][:5]==[1,2,0,3,0],'ผู้ดูแลให้สิทธิ์ CHEAT คืน → ที่ 2')
        api('/api/admin/ban',{'name':'W2','unban':True},tok=tok);check('token' in login('W2'),'ปลดแบน W2 ล็อกอินได้')
        api('/api/admin/allow',{'name':'CHEAT','key':'2026-10','v':False},tok=tok)
        async with async_playwright() as p:
            br=await p.chromium.launch()
            async def page(tk,name,w=390,h=844):
                ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=2,has_touch=True);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
                if tk: await pg.add_init_script(f"localStorage.setItem('rsAuth',JSON.stringify({{name:'{name}',token:'{tk}'}}));localStorage.setItem('trainNewsSeen','999');localStorage.setItem('rotSeen','1')")
                await pg.goto('http://127.0.0.1:3457/');await pg.evaluate("GEM_PRIZES['2026-10']=GEM_PRIZES['2026-11']");return pg,errs
            pg,errs=await page(login('W1')['token'],'W1');await pg.wait_for_timeout(2200)
            t=await pg.evaluate("document.getElementById('sheet').classList.contains('hidden')?'':document.getElementById('sheetBody').innerText")
            check(c1 in t and 'LINE' in t,'W1 เปิดเกม → ป๊อปอัปรหัสรับรางวัล')
            await pg.screenshot(path=SP+'/gem_win.png')
            await pg.evaluate("$('sheet').classList.add('hidden')");await pg.wait_for_timeout(300)
            check(await pg.evaluate("!!document.getElementById('gemStrip')"),'หน้าแรกมีแถบ 💎 ลุ้นเพชรแท้');await pg.screenshot(path=SP+'/gem_home.png')
            await pg.evaluate("openPrizes()");await pg.wait_for_timeout(900);await pg.screenshot(path=SP+'/gem_prizes.png',full_page=False)
            await pg.evaluate("document.querySelector('#sheet .panel').scrollTop=330");await pg.wait_for_timeout(200);await pg.screenshot(path=SP+'/gem_prizes2.png')
            check(not errs,'ไม่มี error ฝั่งผู้เล่น '+str(errs[:2]))
            pg,errs=await page(login('CHEAT')['token'],'CHEAT');await pg.wait_for_timeout(2200)
            check('ตรวจสอบ' in await pg.evaluate("document.getElementById('sheetBody').innerText"),'CHEAT เห็น "กำลังตรวจสอบ"')
            pg,errs=await page(tok,'BOSS1');await pg.wait_for_timeout(1500)
            await pg.evaluate("$('sheet').classList.add('hidden');admKey='2026-10';openAdmin()");await pg.wait_for_timeout(1200)
            t=await pg.evaluate("document.getElementById('sheetBody').innerText");check('ตัดสิทธิ์อัตโนมัติ' in t and 'ได้รางวัลที่ 1' in t,'หน้าผู้ดูแลแสดงผลตรวจ')
            await pg.screenshot(path=SP+'/gem_admin.png')
            # แบนจากหน้าผู้ดูแล (กด 2 ครั้ง + เหตุผล)
            row=pg.locator('.adrow').nth(3);await row.locator('button[data-a=ban]').click();await row.locator('input').fill('ทดสอบแบน');await pg.screenshot(path=SP+'/gem_admin_banask.png');await row.locator('button[data-a=ban]').click();await pg.wait_for_timeout(1000)
            r=api('/api/admin/review?key=2026-10',tok=tok);check(r['rows'][3]['status']=='ban' and r['rows'][3]['why']=='ทดสอบแบน','แบนผ่านปุ่มในหน้าผู้ดูแล ('+r['rows'][3]['name']+')')
            await pg.screenshot(path=SP+'/gem_admin_ban.png')
            # เล่นออนไลน์จริง → เซิร์ฟเวอร์จดเวลาเล่นของบัญชี
            await pg.evaluate("$('sheet').classList.add('hidden');playEndless()");await pg.wait_for_timeout(9000)
            await pg.evaluate("NET&&NET.ws.close()");await pg.wait_for_timeout(1500)
            u=json.load(open(os.path.join(D,'users.json')))['boss1'];a=(u.get('audit') or {}).get('2026-11',{})
            check(a.get('sec',0)>=4,'เซิร์ฟเวอร์จดเวลาเล่นออนไลน์ของ BOSS1: '+str(a))
            # ระเบิดโดยไม่มีระเบิดจริง → เซิร์ฟเวอร์ไม่สน
            await br.close()
    finally:
        srv.terminate();srv.wait()
        for f,b in bak.items():
            if os.path.exists(b): shutil.move(b,os.path.join(D,f))
            elif os.path.exists(os.path.join(D,f)) and f=='seasons.json': os.remove(os.path.join(D,f))
    print(f'ผ่าน {ok} / ไม่ผ่าน {bad}')
asyncio.run(main())
