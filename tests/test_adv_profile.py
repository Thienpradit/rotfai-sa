# โปรไฟล์โชว์ผจญภัยถึงด่านไหน + ดาวรวม ทั้งหน้าบัญชีเราและโปรไฟล์ที่คนอื่นเห็น (11 พ.ย. 2026) · รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start
import asyncio,random
from playwright.async_api import async_playwright
OUT='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();ctx=lambda: b.new_context(viewport={'width':390,'height':844},device_scale_factor=2)
        pg=await (await ctx()).new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(600)
        nm='นักผจญ'+str(random.randint(100,999))
        await pg.evaluate(f"""(async()=>{{const j=await api('/api/register',{{name:'{nm}',pass:'abcd1234',data:prof}});saveAuth('{nm}',j.token);setProfile('acct',j.data,j.name,j.token)}})()""");await pg.wait_for_timeout(500)
        # ผ่าน 12 ด่าน (ด่าน 2-2) ดาว 3,2,1,...
        await pg.evaluate("prof.stage=Array.from({length:12},(_,i)=>i%3+1);saveProf();openAccount()");await pg.wait_for_timeout(1500)
        t=await pg.evaluate("document.getElementById('sheetBody').innerText");await pg.screenshot(path=OUT+'/adv_me.png')
        # อีกคน (เบราว์เซอร์ใหม่ ไม่ได้ล็อกอิน) เปิดโปรไฟล์
        pg2=await (await ctx()).new_page();pg2.on('pageerror',lambda e:errs.append(str(e)))
        await pg2.goto('http://127.0.0.1:3456/');await pg2.wait_for_timeout(600)
        pub=await pg2.evaluate(f"api('/api/profile?name='+encodeURIComponent('{nm}'))")
        await pg2.evaluate(f"openProfile('{nm}')");await pg2.wait_for_timeout(800);t2=await pg2.evaluate("document.getElementById('sheetBody').innerText")
        await pg2.screenshot(path=OUT+'/adv_pub.png')
        # ยังไม่เคยเล่น
        await pg2.evaluate("document.getElementById('sheetBody').innerHTML=advHTML(advOf([]))");t3=await pg2.evaluate("document.getElementById('sheetBody').innerText")
        print('me',[l for l in t.split('\n') if 'ด่าน' in l]);print('pub adv',pub.get('adv'));print('pub',[l for l in t2.split('\n') if 'ด่าน' in l]);print('none',t3.replace('\n',' | '))
        ok=pub.get('adv')=={'top':12,'stars':24} and 'ผ่านถึงด่าน 2-2' in t and 'ผ่านถึงด่าน 2-2' in t2 and '12/30' in t2 and '24/90' in t2 and 'ยังไม่เคยผ่านด่าน' in t3
        print('errors',errs[:3]);print('PASS' if ok and not errs else 'FAIL');await b.close()
asyncio.run(main())
