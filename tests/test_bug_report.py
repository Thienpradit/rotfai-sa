# 🐞 แจ้งบั๊ก + 📈 ความลื่น (14 พ.ย.): Guest ส่งจากหน้าแรก · ส่งจากในเกมพร้อมภาพหน้าจอ · ผู้ดูแลเห็นในแท็บ 🐞/📈 · กดแก้แล้ว · เครื่องส่งสรุปความลื่นตอนจบเกมออนไลน์
# รันเซิร์ฟเวอร์ PORT=3467 เอง (ADMINS=boss3) · สำรอง/คืน data/users.json และ data/bugs.json
import json, os, subprocess, time, urllib.request, urllib.error, shutil, sys
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));D=os.path.join(ROOT,'data');PORT='3467';URL='http://127.0.0.1:'+PORT
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
baks=[]
for f in ('users.json','bugs.json'):
    p=os.path.join(D,f)
    if os.path.exists(p): shutil.move(p,p+'.bugbak');baks.append(p)
js="""const c=require('crypto'),s=c.randomBytes(16).toString('hex'),h=c.scryptSync('pass1234',s,32).toString('hex');
require('fs').mkdirSync(require('path').dirname(process.argv[1]),{recursive:true});require('fs').writeFileSync(process.argv[1],JSON.stringify({boss3:{lname:'boss3',name:'boss3',salt:s,hash:h,rp:0,updated:1,data:{coins:0,onv:2,owned:{},st:{},ach:{}}}}))"""
subprocess.run(['node','-e',js,os.path.join(D,'users.json')],check=True,cwd=ROOT)
srv=subprocess.Popen(['node','server.js'],cwd=ROOT,env={**os.environ,'PORT':PORT,'ADMINS':'boss3'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT);time.sleep(1.8)
try:
    r=api('/api/login',{'name':'boss3','pass':'pass1234'});tok=r.get('token');check(tok and r.get('admin'),'เข้าสู่ระบบบัญชีผู้ดูแล '+str(r)[:80])
    check(api('/api/admin/bugs').get('_status')==403,'ไม่ล็อกอิน → ดูรายงานบั๊กไม่ได้ (403)')
    check(api('/api/bug',{'cat':'other','text':''}).get('_status')==400,'ไม่เล่าอะไรเลย → ส่งไม่ได้')
    with sync_playwright() as p:
        b=p.chromium.launch(args=['--disable-renderer-backgrounding']);errs=[]
        g=b.new_page(viewport={'width':844,'height':390});g.on('pageerror',lambda e:errs.append(str(e)))
        g.add_init_script("localStorage.setItem('rotSeen','1');localStorage.setItem('trainNewsSeen','99')")
        g.goto(URL);g.wait_for_timeout(1200);g.evaluate("document.getElementById('sheet').classList.add('hidden')")
        g.fill('#name','ทดสอบบั๊ก')
        check(g.is_visible('#bugMenu'),'มีปุ่ม 🐞 ที่หน้าแรก')
        g.click('#bugMenu');g.wait_for_timeout(300)
        check('แจ้งบั๊ก' in g.inner_text('#sheet'),'กด 🐞 → หน้าแจ้งบั๊กเปิด')
        g.click('#bugSend');g.wait_for_timeout(200);check('เลือกเรื่อง' in g.inner_text('#bugErr'),'ยังไม่เลือกเรื่อง → เตือน')
        g.click('#bugCat div[data-k=lag]');g.fill('#bugTxt','รถไฟคนอื่นกระตุกทุก ๆ 10 วิ');g.click('#bugSend');g.wait_for_timeout(900)
        check('ส่งแล้ว' in g.inner_text('#sheet'),'Guest ส่งรายงานจากหน้าแรกได้')
        g.click('#bugOk')
        # ในเกม: ⚙️ → 🐞 → มีภาพหน้าจอแนบ
        g.evaluate("startGame('inf')");g.wait_for_timeout(2500)
        g.click('#setGame');g.wait_for_timeout(300);check(g.is_visible('#setBug'),'ในเกม ⚙️ ตั้งค่ามีปุ่ม 🐞 แจ้งบั๊ก')
        g.click('#setBug');g.wait_for_timeout(300)
        check(g.is_visible('.bugshot img'),'แนบภาพหน้าจอเกมได้ (มีรูปตัวอย่าง)')
        g.evaluate("bugLast=0");g.click('#bugCat div[data-k=crash]');g.fill('#bugTxt','เกมค้างตอนเก็บระเบิด');g.click('#bugSend');g.wait_for_timeout(900)
        check('ส่งแล้ว' in g.inner_text('#sheet'),'ส่งจากในเกมพร้อมรูปได้')
        bl=api('/api/admin/bugs',tok=tok).get('bugs',[])
        check(len(bl)==2 and bl[0]['cat']=='crash' and bl[0]['hasShot'] and not bl[1]['hasShot'],'เซิร์ฟเวอร์เก็บ 2 เรื่อง (เรื่องในเกมมีรูป)')
        i=bl[0].get('info',{}) if bl else {}
        check(i.get('dev',{}).get('os') and 'perf' in i and 'ออฟไลน์' in i.get('where',''),'แนบข้อมูลเครื่อง/ความลื่น/โหมดอัตโนมัติ '+str(i.get('where')))
        check(bl and bl[1].get('name')=='ทดสอบบั๊ก','Guest ใช้ชื่อที่พิมพ์ไว้')
        one=api('/api/admin/bug?id=%d'%bl[0]['id'],tok=tok) if bl else {};check(str(one.get('shot','')).startswith('data:image/jpeg'),'เปิดรูปหน้าจอได้ (%d KB)'%(len(one.get('shot',''))//1024))
        # ความลื่น: เล่นออนไลน์ 22 วิแล้วออก → ส่งสรุป
        g.evaluate("$('sheet').classList.add('hidden');toMenu()");g.wait_for_timeout(500)
        g.evaluate("OD='normal';playEndless();window.__imm=setInterval(()=>{if(player&&!player.__nd){const d=player.die.bind(player);player.die=()=>{};player.__nd=1}},100)");g.wait_for_timeout(23000)
        g.evaluate("finish(false,true,true)");g.wait_for_timeout(1200)
        pr=api('/api/admin/perf',tok=tok);rows=pr.get('rows',[])
        check(len(rows)>=1 and rows[-1].get('fps',0)>20 and rows[-1].get('mode')=='ffa-normal','ส่งสรุปความลื่นตอนจบเกมออนไลน์ '+json.dumps(rows[-1] if rows else {},ensure_ascii=False)[:200])
        sv=pr.get('server') or {};check(sv.get('ticks',0)>100 and 'late' in sv and sv.get('rooms',0)>=1,'เซิร์ฟเวอร์รายงานเวลาต่อรอบ '+json.dumps({k:sv.get(k) for k in ('cpu','tick','late','loop')}))
        # หน้าผู้ดูแล
        a=b.new_page(viewport={'width':390,'height':844});a.on('pageerror',lambda e:errs.append(str(e)))
        a.add_init_script("localStorage.setItem('rotSeen','1');localStorage.setItem('trainNewsSeen','99');localStorage.setItem('rsAuth',JSON.stringify({token:'%s',name:'boss3'}))"%tok)
        a.goto(URL);a.wait_for_timeout(1800);a.evaluate("$('sheet').classList.add('hidden')")
        check(a.evaluate("IS_ADMIN&&ADM_BUGS")==2,'ผู้ดูแลเปิดเกม → รู้ว่ามีบั๊กใหม่ 2 เรื่อง')
        a.evaluate("openAdmin()");a.wait_for_timeout(600);a.click('#admTabs .tab[data-k=bugs]');a.wait_for_timeout(800)
        t=a.inner_text('#admList');check('เกมค้างตอนเก็บระเบิด' in t and 'ทดสอบบั๊ก' in t,'แท็บ 🐞 แสดงรายงาน')
        a.click('#admList button[data-s]');a.wait_for_timeout(600);check(a.is_visible('#admList .shot img'),'ดูภาพหน้าจอในหน้าผู้ดูแลได้')
        a.screenshot(path='/tmp/bug_admin.png')
        a.click('#admList button[data-d]');a.wait_for_timeout(700)
        check(sum(1 for x in api('/api/admin/bugs',tok=tok)['bugs'] if x['done'])==1,'กด ✅ แก้แล้ว → บันทึก')
        a.click('#admTabs .tab[data-k=perf]');a.wait_for_timeout(800);t=a.inner_text('#admList')
        check('เซิร์ฟเวอร์' in t and 'รวม' in t,'แท็บ 📈 ความลื่นแสดงตาราง + เซิร์ฟเวอร์')
        a.screenshot(path='/tmp/perf_admin.png')
        check(not errs,'ไม่มี error '+str(errs[:2]))
        b.close()
finally:
    srv.terminate();srv.wait()
    for f in ('users.json','bugs.json'):
        pth=os.path.join(D,f)
        if os.path.exists(pth): os.remove(pth)
    for pth in baks: shutil.move(pth+'.bugbak',pth)
print(f'{ok} ผ่าน · {bad} ไม่ผ่าน');print('PASS' if not bad else 'FAIL');sys.exit(1 if bad else 0)
