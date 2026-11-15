# 💾 สำรองข้อมูลทุกชั่วโมง + คืนข้อมูลรายคน + คืนสถิติ GemReaper (15 พ.ย.)
# รันเซิร์ฟเวอร์ PORT=3468 เอง (BACKUP_MS=4000, ADMINS=boss5) · สำรอง/คืน data/users.json + data/backups
import json, os, subprocess, time, urllib.request, urllib.error, shutil, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));D=os.path.join(ROOT,'data');PORT='3468';URL='http://127.0.0.1:'+PORT
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
U=os.path.join(D,'users.json');BK=os.path.join(D,'backups')
if os.path.exists(U): shutil.move(U,U+'.bkbak')
if os.path.exists(BK): shutil.move(BK,BK+'.bkbak')
js="""const c=require('crypto'),mk=(n,data)=>{const s=c.randomBytes(16).toString('hex');return{lname:n.toLowerCase(),name:n,salt:s,hash:c.scryptSync('pass1234',s,32).toString('hex'),rp:+data.rp||0,updated:1,data}};
const db={};for(const [n,d] of [['boss5',{coins:0,onv:2,owned:{},st:{},ach:{}}],['GemReaper',{coins:0,rp:0,onrp:0,onv:2,season:'2026-11',owned:{loco:['classic','diesel']},st:{okills:2343,omaxLen:1740,games:3},ach:{},restored:['r1']}],['Pim',{coins:5000,rp:900,onrp:900,onv:2,season:'2026-11',owned:{},st:{kills:50,games:40,maxLen:800},ach:{k1:1}}]])db[n.toLowerCase()]=mk(n,d);
require('fs').mkdirSync(require('path').dirname(process.argv[1]),{recursive:true});require('fs').writeFileSync(process.argv[1],JSON.stringify(db))"""
subprocess.run(['node','-e',js,U],check=True,cwd=ROOT)
srv=subprocess.Popen(['node','server.js'],cwd=ROOT,env={**os.environ,'PORT':PORT,'ADMINS':'boss5','BACKUP_MS':'4000'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);time.sleep(2)
try:
    g=api('/api/login',{'name':'GemReaper','pass':'pass1234'});d=g.get('data',{});st=d.get('st',{})
    check(d.get('rp')==2495 and d.get('onrp')==2495 and d.get('coins')==31426 and st.get('kills')==2343 and st.get('maxLen')==1740 and st.get('games')==4 and 'diesel' in d.get('owned',{}).get('loco',[]),'คืนสถิติ GemReaper (RP 2,495 · เหรียญ 31,426 · กำจัด 2,343 · ยาวสุด 1,740 · เกม +1 · ดีเซลยังอยู่)')
    gt=g['token'];r=api('/api/save',{'data':{**d,'rp':0,'onrp':0,'coins':0,'st':{'games':3},'ach':{}}},gt)
    g2=api('/api/me',tok=gt)['data'];check(g2['rp']==2495 and g2['coins']==31426 and g2['st'].get('kills')==2343 and r.get('fix',{}).get('st'),'เครื่องที่ถือโปรไฟล์ว่างค้าง ส่งมาทับไม่ได้แล้ว '+json.dumps(r.get('fix',{}))[:120])
    a=api('/api/login',{'name':'boss5','pass':'pass1234'})['token']
    time.sleep(5.5);L=api('/api/admin/backups',tok=a).get('list',[])
    check(len(L)>=1 and L[0].get('n')==3,'สำรองอัตโนมัติตามรอบ ('+str(len(L))+' ชุด) '+json.dumps(L[:1]))
    check(api('/api/admin/backups').get('_status')==403,'ไม่ใช่ผู้ดูแล → ดูชุดสำรองไม่ได้')
    p=api('/api/login',{'name':'Pim','pass':'pass1234'});pt=p['token'];pd=p['data']
    api('/api/save',{'data':{**pd,'coins':1000,'rp':880,'onrp':880,'st':{**pd['st'],'games':41}}},pt)   # Pim ใช้เหรียญ/โดนหักแรงก์ตามปกติ
    bid=L[0]['id'];v=api('/api/admin/backup?id=%s&name=pim'%bid,tok=a)
    check(v.get('then',{}).get('coins')==5000 and v.get('now',{}).get('coins')==1000,'ดูเทียบชุดสำรอง/ตอนนี้ได้ '+json.dumps({'then':v.get('then',{}).get('coins'),'now':v.get('now',{}).get('coins')}))
    n0=len(api('/api/admin/backups',tok=a)['list']);x=api('/api/admin/restore',{'id':bid,'name':'Pim'},a)
    pd2=api('/api/me',tok=pt)['data'];check(x.get('ok') and pd2['coins']==5000 and pd2['rp']==900,'คืนข้อมูล Pim จากชุดสำรองได้ (เหรียญ 5,000 · RP 900)')
    check(len(api('/api/admin/backups',tok=a)['list'])>=n0+1,'ก่อนคืนข้อมูล ระบบสำรองชุดปัจจุบันไว้ให้ก่อน')
    check(api('/api/admin/restore',{'id':bid,'name':'nobody'},a).get('_status')==404,'ชื่อที่ไม่มี → 404')
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b=pw.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.add_init_script("localStorage.setItem('rotSeen','1');localStorage.setItem('trainNewsSeen','99');localStorage.setItem('rsAuth',JSON.stringify({token:'%s',name:'boss5'}))"%a)
        pg.goto(URL);pg.wait_for_timeout(1800);pg.evaluate("$('sheet').classList.add('hidden');openAdmin();0");pg.wait_for_timeout(700)
        pg.click('#admTabs .tab[data-k=bk]');pg.wait_for_timeout(800);pg.fill('#bkName','Pim');pg.click('#bkLook');pg.wait_for_timeout(700)
        t=pg.inner_text('#admList');check('คืนข้อมูล Pim' in t and 'เหรียญ' in t,'หน้า 🛡️ แท็บ 💾 สำรอง: เลือกชุด + ชื่อ → ตารางเทียบ + ปุ่มคืนข้อมูล')
        pg.screenshot(path='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad/bk_admin.png')
        check(not errs,'ไม่มี error '+str(errs[:2]));b.close()
    srv.terminate();out=srv.communicate(timeout=5)[0]
    check('stats restored for gemreaper' in out and 'backup #' in out,'log: คืนสถิติ + สำรอง')
    srv=subprocess.Popen(['node','server.js'],cwd=ROOT,env={**os.environ,'PORT':PORT,'ADMINS':'boss5','BACKUP_MS':'4000'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);time.sleep(2)
    g3=api('/api/me',tok=gt)['data'];check(g3['st']['games']==4 and g3['rp']==2495,'เปิดเซิร์ฟเวอร์ซ้ำ ไม่คืนซ้ำ (เกมยัง 4)')
finally:
    srv.terminate()
    try: srv.communicate(timeout=5)
    except Exception: pass
    if os.path.exists(U): os.remove(U)
    if os.path.exists(BK): shutil.rmtree(BK)
    if os.path.exists(U+'.bkbak'): shutil.move(U+'.bkbak',U)
    if os.path.exists(BK+'.bkbak'): shutil.move(BK+'.bkbak',BK)
print(f'{ok} ผ่าน · {bad} ไม่ผ่าน');print('PASS' if not bad else 'FAIL');sys.exit(1 if bad else 0)
