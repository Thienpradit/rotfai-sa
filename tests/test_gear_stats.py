# หน้าสถิติ/โปรไฟล์ โชว์หัวจักร + หวูดที่ใช้อยู่ (10 พ.ย. 2026) · รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start
import asyncio,random
from playwright.async_api import async_playwright
OUT='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await (await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2)).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(600)
        nm='เกียร์'+str(random.randint(100,999))
        await pg.evaluate(f"""(async()=>{{const j=await api('/api/register',{{name:'{nm}',pass:'abcd1234',data:prof}});saveAuth('{nm}',j.token);setProfile('acct',j.data)}})()""");await pg.wait_for_timeout(500)
        await pg.evaluate("prof.eq.loco='bullet';prof.eq.horn='siren';openAccount()");await pg.wait_for_timeout(500)
        t=await pg.evaluate("document.getElementById('sheetBody').innerText");drawn=await pg.evaluate("(()=>{const c=document.querySelector('.gear .lic');const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=3;i<d.length;i+=4)if(d[i])n++;return n})()")
        await pg.screenshot(path=OUT+'/gear_me.png')
        pub=await pg.evaluate(f"api('/api/profile?name='+encodeURIComponent('{nm}'))")
        await pg.evaluate(f"openProfile('{nm}')");await pg.wait_for_timeout(800);t2=await pg.evaluate("document.getElementById('sheetBody').innerText")
        await pg.screenshot(path=OUT+'/gear_pub.png')
        print('me',[l for l in t.split('\n') if 'หัว' in l or 'หวูด' in l or 'ไซเรน' in l or 'กระสุน' in l],'drawn px',drawn);print('pub keys',sorted(pub.keys()));print('pub',[l for l in t2.split('\n') if 'ไอน้ำ' in l])
        ok='รถไฟหัวกระสุน' in t and 'ไซเรนรถด่วน' in t and drawn>200 and 'horn' in pub and 'หัวจักรไอน้ำ' in t2 and 'หวูดไอน้ำ' in t2
        print('errors',errs[:3]);print('PASS' if ok and not errs else 'FAIL');await b.close()
asyncio.run(main())
