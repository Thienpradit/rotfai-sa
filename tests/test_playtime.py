# ⏱ เวลาเล่นทั้งหมด (18 พ.ย.) แทน "กำจัดสูงสุด/เกม" · บัญชีเดิมเริ่มจากเวลาเล่นที่เซิร์ฟเวอร์จด (audit) · เล่นแล้วนับเพิ่ม · โปรไฟล์คนอื่นเห็น
# รันเซิร์ฟเวอร์ PORT=3470 เอง · สำรอง/คืน data/users.json
import asyncio, json, os, subprocess, time, urllib.request, urllib.error, shutil, sys
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));D=os.path.join(ROOT,'data');PORT='3470';URL='http://127.0.0.1:'+PORT
def api(path,body=None,tok=None):
    req=urllib.request.Request(URL+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+tok} if tok else {})})
    try:
        with urllib.request.urlopen(req) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e: return {'_status':e.code,**json.loads(e.read() or b'{}')}
ok=0;bad=0
def check(c,msg):
    global ok,bad
    if c: ok+=1;print('  ✓',msg)
    else: bad+=1;print('  ✗',msg)
U=os.path.join(D,'users.json')
if os.path.exists(U): shutil.move(U,U+'.ptbak')
js="""const c=require('crypto'),mk=(n,data,audit)=>{const s=c.randomBytes(16).toString('hex');return{lname:n.toLowerCase(),name:n,salt:s,hash:c.scryptSync('pass1234',s,32).toString('hex'),rp:+data.rp||0,updated:1,data,audit}};
const db={};db.pim=mk('Pim',{coins:0,rp:100,onrp:100,onv:2,owned:{},st:{kills:50,games:40,killsGame:7},ach:{}},{'2026-11':{sec:5400,g:30,k:50,ml:900,rp0:0}});
db.nok=mk('Nok',{coins:0,rp:0,onrp:0,onv:2,owned:{},st:{games:1},ach:{}},null);
require('fs').mkdirSync(require('path').dirname(process.argv[1]),{recursive:true});require('fs').writeFileSync(process.argv[1],JSON.stringify(db))"""
subprocess.run(['node','-e',js,U],check=True,cwd=ROOT)
srv=subprocess.Popen(['node','server.js'],cwd=ROOT,env={**os.environ,'PORT':PORT},stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT);time.sleep(2)
async def main():
    p=api('/api/profile?name=Pim');check(p.get('st',{}).get('playSec')==5400,'บัญชีเดิมได้เวลาเล่นตั้งต้นจากที่เซิร์ฟเวอร์จด (5,400 วิ = 1 ชม. 30 น.) '+str(p.get('st',{}).get('playSec')))
    n=api('/api/profile?name=Nok');check(n.get('st',{}).get('playSec')==0,'ไม่เคยจด = 0')
    t=api('/api/login',{'name':'Pim','pass':'pass1234'})['token']
    async with async_playwright() as pw:
        b=await pw.chromium.launch();pg=await (await b.new_context(viewport={'width':900,'height':700})).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.add_init_script(f"localStorage.setItem('rsAuth',JSON.stringify({{name:'Pim',token:'{t}'}}))")
        await pg.goto(URL);await pg.wait_for_timeout(1500)
        s0=await pg.evaluate("[ACCT.mode,+prof.st.playSec||0]");check(s0[0]=='acct' and s0[1]==5400,'เครื่องโหลดเวลาเล่นจากบัญชี '+str(s0))
        await pg.evaluate("player&&(player.die=function(){});startGame('inf');player.die=function(){};0");await pg.wait_for_timeout(4000)
        s1=await pg.evaluate("+prof.st.playSec");check(5403<=s1<=5406,'เล่น 4 วิ → นับเพิ่ม ~4 วิ ('+str(round(s1,1))+')')
        await pg.evaluate("PAUSED=true;0");a=await pg.evaluate("+prof.st.playSec");await pg.wait_for_timeout(1000);c=await pg.evaluate("+prof.st.playSec");check(abs(c-a)<.05,'หยุดเกมอยู่ไม่นับ')
        await pg.evaluate("PAUSED=false;pushProf();0");await pg.wait_for_timeout(1500)
        p=api('/api/profile?name=Pim');check(5402<=p['st']['playSec']<=5410,'บันทึกขึ้นเซิร์ฟเวอร์ '+str(p['st']['playSec']))
        await pg.evaluate("state='menu';openAccount();0");await pg.wait_for_timeout(600)
        h=await pg.evaluate("document.getElementById('sheet').innerText");check('เวลาเล่นทั้งหมด' in h and '1 ชม. 30 น.' in h,'หน้าบัญชีโชว์ ⏱ เวลาเล่นทั้งหมด 1 ชม. 30 น.')
        check('กำจัดสูงสุด/เกม' not in h,'เอา "กำจัดสูงสุด/เกม" ออกแล้ว')
        await pg.evaluate("openProfile('Pim');0");await pg.wait_for_timeout(1000)
        h=await pg.evaluate("document.getElementById('sheet').innerText");check('เวลาเล่นทั้งหมด' in h and '1 ชม. 30 น.' in h,'โปรไฟล์ (คนอื่นดู) โชว์เวลาเล่นด้วย')
        r=api('/api/save',{'data':{**api('/api/me',tok=t)['data'],'st':{**api('/api/me',tok=t)['data']['st'],'playSec':99999999}}},t)
        check(r.get('play',0)<5410+200 and not r.get('fix'),'ส่งเวลาเกินจริงมา → ปรับเงียบ ๆ ไม่เกินเวลาที่ผ่านไป ('+str(r.get('play'))+')')
        check(not errs,'ไม่มี error '+str(errs[:2]))
        await b.close()
try: asyncio.run(main())
finally:
    srv.terminate();srv.wait()
    if os.path.exists(U+'.ptbak'): shutil.move(U+'.ptbak',U)
    elif os.path.exists(U): os.remove(U)
print(f'{ok} ผ่าน · {bad} ไม่ผ่าน');print('PASS' if not bad else 'FAIL');sys.exit(1 if bad else 0)
