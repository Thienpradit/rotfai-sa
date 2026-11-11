# ✏️ เปลี่ยนชื่อ จ่าย 20,000 🪙 (11 พ.ย. 2026) · รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start
import asyncio,random,json,urllib.request
from playwright.async_api import async_playwright
OUT='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad'
B='http://127.0.0.1:3456'
def call(path,body=None,tok=None):
    req=urllib.request.Request(B+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+tok} if tok else {})})
    try:
        with urllib.request.urlopen(req) as r: return r.status,json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code,json.loads(e.read() or b'{}')
async def main():
    r=random.randint(1000,9999);a='เปลี่ยน'+str(r);b2='ใหม่'+str(r);poor='จน'+str(r);taken='มีแล้ว'+str(r)
    s,j=call('/api/register',{'name':a,'pass':'abcd1234','data':{'coins':25000}});assert s==200,j
    call('/api/register',{'name':taken,'pass':'abcd1234','data':{}})
    s,jp=call('/api/register',{'name':poor,'pass':'abcd1234','data':{'coins':500}})
    # API: เหรียญไม่พอ / ชื่อซ้ำ / ชื่อเดิม
    e1=call('/api/rename',{'name':'อะไรก็ได้'+str(r),'data':jp['data']},jp['token'])
    e2=call('/api/rename',{'name':taken,'data':j['data']},j['token'])
    e3=call('/api/rename',{'name':a,'data':j['data']},j['token'])
    print('poor',e1[0],e1[1].get('err'));print('taken',e2[0],e2[1].get('err'));print('same',e3[0],e3[1].get('err'))
    async with async_playwright() as p:
        br=await p.chromium.launch();pg=await (await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2)).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(B+'/');await pg.wait_for_timeout(500)
        await pg.evaluate(f"(()=>{{saveAuth({json.dumps(a)},{json.dumps(j['token'])});setProfile('acct',{json.dumps(j['data'])},{json.dumps(a)},{json.dumps(j['token'])});openAccount()}})()");await pg.wait_for_timeout(600)
        await pg.click('#acRn');await pg.wait_for_timeout(200);await pg.fill('#rnName',b2);await pg.screenshot(path=OUT+'/rename1.png')
        await pg.click('#rnGo');await pg.wait_for_timeout(200);conf=await pg.text_content('#rnGo')
        await pg.click('#rnGo');await pg.wait_for_timeout(1200)
        res=await pg.evaluate("({name:ACCT.name,coins:prof.coins,mode:ACCT.mode,tok:ACCT.token,btn:document.getElementById('acctBtn').textContent,msg:document.getElementById('acMore').innerText,pn:playerName()})")
        await pg.screenshot(path=OUT+'/rename2.png')
        # เซฟต่อได้ด้วย token ใหม่ ไม่โดนปรับเหรียญกลับ
        await pg.evaluate("prof.coins+=10;pushProf()");await pg.wait_for_timeout(800);fx=await pg.evaluate("prof.coins")
        await br.close()
    old_login=call('/api/login',{'name':a,'pass':'abcd1234'});new_login=call('/api/login',{'name':b2,'pass':'abcd1234'})
    oldtok=call('/api/me',None,j['token']);prof=call('/api/profile?name='+urllib.parse.quote(b2))
    print('confirm btn',conf);print('after',{k:v for k,v in res.items() if k!='tok'});print('save after',fx)
    print('old login',old_login[0],'new login',new_login[0],new_login[1].get('name'),new_login[1].get('data',{}).get('coins'),'old token',oldtok[0],'profile',prof[0])
    ok=e1[0]==400 and 'ไม่พอ' in e1[1]['err'] and e2[0]==409 and e3[0]==400 and 'ยืนยัน' in conf and res['name']==b2 and res['coins']==5000 and res['mode']=='acct' and b2 in res['btn'] and res['pn']==b2 and 'เปลี่ยนชื่อจาก' in res['msg'] \
       and fx==5010 and old_login[0]==401 and new_login[0]==200 and new_login[1]['data']['coins']==5010 and oldtok[0]==401 and prof[0]==200
    print('errors',errs[:3]);print('PASS' if ok and not errs else 'FAIL')
import urllib.parse
asyncio.run(main())
