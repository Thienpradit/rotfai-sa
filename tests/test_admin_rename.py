# ผู้ดูแลเปลี่ยนชื่อ / ถูกถอดจาก ADMINS → หมดสิทธิ์ผู้ดูแล + ของฟรีจากสิทธิ์ผู้ดูแลต้องหายจากบัญชี (เจ้าของแจ้ง 13 พ.ย. 21:24)
# รันเซิร์ฟเวอร์ PORT=3459 เอง (ADMINS=boss2) · สำรอง/คืน data/users.json
import json, os, subprocess, time, urllib.request, urllib.error, shutil, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));D=os.path.join(ROOT,'data')
sys.path.insert(0,ROOT)
def api(path,body=None,tok=None):
    req=urllib.request.Request('http://127.0.0.1:3459'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+tok} if tok else {})})
    try:
        with urllib.request.urlopen(req) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e: return {'_status':e.code,**json.loads(e.read() or b'{}')}
def login(n): return api('/api/login',{'name':n,'pass':'pass1234'})
ok=0;bad=0
def check(c,msg):
    global ok,bad
    if c: ok+=1;print('  ✓',msg)
    else: bad+=1;print('  ✗',msg)
ALL=json.loads(subprocess.run(['node','-e',"const A=require('./anticheat');const o={};for(const c of A.CATS)o[c]=Object.keys(A.SHOP[c]);for(const [c,id] of A.LIMITED)if(!o[c].includes(id))o[c].push(id);console.log(JSON.stringify(o))"],cwd=ROOT,capture_output=True,text=True).stdout)
NALL=sum(len(v) for v in ALL.values())
def nown(o): return sum(len(set(o.get(c,[]))&set(ALL[c])) for c in ALL)
bak=os.path.join(D,'users.json.admbak')
if os.path.exists(os.path.join(D,'users.json')): shutil.copy(os.path.join(D,'users.json'),bak)
# oldadm = ผู้ดูแลเดิมที่เปลี่ยนชื่อไปแล้ว (บัญชีติดของครบทุกชิ้นจากสิทธิ์ผู้ดูแล) · boss2 = ผู้ดูแลตอนนี้ (ซื้อดีเซลจริง 1 ชิ้น)
users={'oldadm':{'owned':ALL,'coins':5000},'boss2':{'owned':{'loco':['classic','diesel']},'coins':300000},'normal':{'owned':{'loco':['classic','bullet']},'coins':900},'gemreaper':{'owned':{'loco':['classic'],'kfx':['none']},'coins':31426}}
js="""const c=require('crypto'),db={},U=JSON.parse(process.argv[2]);for(const [l,v] of Object.entries(U)){const s=c.randomBytes(16).toString('hex'),h=c.scryptSync('pass1234',s,32).toString('hex');
  db[l]={lname:l,name:l.toUpperCase(),salt:s,hash:h,rp:100,updated:1,data:{coins:v.coins,rp:100,onrp:100,onv:2,season:'2026-11',owned:v.owned,eq:{loco:v.owned.loco[v.owned.loco.length-1]},st:{},ach:{}}}}
  require('fs').writeFileSync(process.argv[1],JSON.stringify(db))"""
subprocess.run(['node','-e',js,os.path.join(D,'users.json'),json.dumps(users)],check=True)
srv=subprocess.Popen(['node','server.js'],cwd=ROOT,env={**os.environ,'PORT':'3459','ADMINS':'boss2'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT);time.sleep(1.8)
try:
    j=login('OLDADM');o=j['data']['owned']
    check(not j.get('admin'),'ผู้ดูแลเดิม (เปลี่ยนชื่อแล้ว) ไม่ใช่ผู้ดูแล')
    check(nown(o)<=8 and 'comet' not in o.get('loco',[]),f'ของจากสิทธิ์ผู้ดูแลหายแล้ว (เหลือ {nown(o)}/{NALL} = ของฟรี)')
    check(j['data']['coins']==5000,'เหรียญไม่ถูกหัก')
    check(api('/api/admin/review?key=2026-11',tok=j['token']).get('_status')==403,'เปิดหน้าผู้ดูแลไม่ได้ (403)')
    # หน้าเว็บเก่าที่ยังเปิดค้าง ส่งของครบทุกชิ้นกลับมา → ไม่ได้ของคืน และไม่หักเหรียญ
    d=dict(j['data']);d['owned']=ALL;r=api('/api/save',{'data':d},j['token'])
    check(r.get('ok') and r.get('fix') and nown(r['fix']['owned'])<=8 and r['fix']['coins']==5000,'หน้าเว็บเก่าส่งของครบมา → เซิร์ฟเวอร์ไม่รับ ส่งของจริงกลับ ไม่หักเหรียญ')
    j2=login('OLDADM');check(nown(j2['data']['owned'])<=8 and j2['data']['coins']==5000,'ข้อมูลบัญชีที่บันทึกยังไม่มีของผู้ดูแล')
    # ผู้ดูแลตอนนี้: ใช้ของครบได้ แต่ไม่บันทึกลงบัญชี
    b=login('BOSS2');check(b.get('admin') and nown(b['data']['owned'])==NALL,'ผู้ดูแลตอนนี้ใช้ของครบทุกชิ้น')
    d=dict(b['data']);d['eq']={'loco':'comet'};r=api('/api/save',{'data':d},b['token']);check(r.get('ok') and not r.get('fix'),'ผู้ดูแลใส่ดาวหางได้ ไม่โดนปรับ')
    raw=json.load(open(os.path.join(D,'users.json')))['boss2']['data']
    check(raw['owned'].get('loco')==['classic','diesel'] and raw['coins']==300000,'ที่บันทึกในบัญชีผู้ดูแล = ของที่ซื้อจริงเท่านั้น '+str(raw['owned'].get('loco')))
    # ผู้ดูแลเปลี่ยนชื่อ → หมดสิทธิ์ทันที เหลือของจริง
    r=api('/api/rename',{'name':'BOSSX','data':b['data']},b['token'])
    check(r.get('token') and not r.get('admin'),'ผู้ดูแลเปลี่ยนชื่อ → คำตอบไม่มีสิทธิ์ผู้ดูแล')
    check(r['data']['owned'].get('loco')==['classic','diesel'],'หลังเปลี่ยนชื่อเหลือของที่ซื้อจริง '+str(r['data']['owned'].get('loco')))
    x=login('BOSSX');check(not x.get('admin') and nown(x['data']['owned'])<NALL,'เข้าสู่ระบบชื่อใหม่ = ผู้เล่นธรรมดา')
    n=login('NORMAL');check(n['data']['owned'].get('loco')==['classic','bullet'],'ผู้เล่นทั่วไปของเหมือนเดิม')
    g=login('GEMREAPER');check(g['data']['owned'].get('loco')==['classic','diesel'] and g['data']['coins']==31426,'GemReaper ได้หัวจักรดีเซลคืน (เหรียญเท่าเดิม) '+str(g['data']['owned'].get('loco')))
    # ปิดเปิดเซิร์ฟเวอร์ใหม่ → ไม่คืนซ้ำ · ถ้าผู้เล่นมีอยู่แล้วก็ไม่ซ้ำ
    srv.terminate();srv.wait();srv=subprocess.Popen(['node','server.js'],cwd=ROOT,env={**os.environ,'PORT':'3459','ADMINS':'boss2'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT);time.sleep(1.8)
    raw=json.load(open(os.path.join(D,'users.json')))['gemreaper']['data'];g2=login('GEMREAPER');time.sleep(.6);raw=json.load(open(os.path.join(D,'users.json')))['gemreaper']['data'];check(g2['data']['owned']['loco'].count('diesel')==1 and raw.get('restored')==['r1'],'คืนครั้งเดียว ไม่ซ้ำ '+str(raw['owned'].get('loco'))+str(raw.get('restored')))
finally:
    srv.terminate();srv.wait()
    if os.path.exists(bak): shutil.move(bak,os.path.join(D,'users.json'))
print(f'{ok} ผ่าน · {bad} ไม่ผ่าน');print('PASS' if not bad else 'FAIL');sys.exit(1 if bad else 0)
