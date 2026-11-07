# ภารกิจรายวัน 5 ข้อ (มีกำจัด 1 + 2v2 1) · ภารกิจยากขึ้น · สถิติ/โปรไฟล์ (นับการกำจัด) · ตารางอันดับแท็บ 💀 กำจัด + แตะชื่อดูโปรไฟล์
# รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start  แล้ว python tests/test_missions_profile.py [โฟลเดอร์ภาพ]
import asyncio, sys, random
from playwright.async_api import async_playwright
OUT=sys.argv[1] if len(sys.argv)>1 else '/tmp'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await (await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2)).new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(700)
        # จำลองผู้เล่นเก่าที่มีภารกิจวันนี้ 3 ข้อ → ต้องเติมเป็น 5 โดยไม่ลบของเดิม
        r=await pg.evaluate("""(()=>{const old=prof.daily.m.slice(0,3).map(m=>({...m,p:1}));prof.daily={date:todayKey(),m:old};ensureDaily();
          const keep=old.every((m,i)=>prof.daily.m[i].id===m.id&&prof.daily.m[i].p===1);
          const runs=[];for(let i=0;i<30;i++){prof.daily=null;ensureDaily();const ids=prof.daily.m.map(m=>m.id);runs.push([ids.length,ids.some(i=>MG_KILL.includes(i)),ids.some(i=>MG_VS.includes(i)),new Set(ids).size===ids.length,prof.daily.m.every(m=>m.r<=300&&m.r>=10)])}
          return {keep,len:prof.daily.m.length,ok:runs.every(x=>x[0]===5&&x[1]&&x[2]&&x[3]&&x[4]),sample:prof.daily.m.map(m=>misTxt(m)+' → '+m.r)}})()""")
        print(r)
        # เป้ากำจัดเก่าที่ง่ายเกิน (ยังไม่รับรางวัล) → สุ่มใหม่ตามเกณฑ์ใหม่ เก็บความคืบหน้า · ที่รับรางวัลแล้วไม่แตะ
        up=await pg.evaluate("""(()=>{prof.daily={date:todayKey(),m:[{id:'kills',n:15,r:30,p:5,c:false},{id:'vsPlay',n:3,r:20,p:0,c:false},{id:'whites',n:30,r:20,p:0,c:false},{id:'killsOne',n:6,r:30,p:6,c:true},{id:'games',n:8,r:15,p:1,c:false}]};ensureDaily();const m=prof.daily.m;
          return m[0].n>=50&&m[0].n<=100&&m[0].p===5&&m[3].n===6&&m[3].c&&mkMission(MP.killsOne).n>=10})()""")
        print('upgrade old kill missions:',up);r['ok']=r['ok'] and up
        # ติดตาม: kills/killsGame/vsKills/vsGames/bossHits
        t=await pg.evaluate("""(()=>{prof.daily.m=[mkMission(MP.killsOne),mkMission(MP.vsKills),mkMission(MP.vsPlay),mkMission(MP.bossHit),mkMission(MP.kills)];
          const k0=prof.st.kills||0;track('kills');trackMax('killsGame',3);track('vsKills');track('vsGames');track('bossHits');
          return {kills:(prof.st.kills||0)-k0,prog:prof.daily.m.map(m=>m.id+':'+m.p)}})()""")
        print(t)
        # ลงทะเบียน 2 บัญชี แล้วดูตารางอันดับ กำจัด + โปรไฟล์คนอื่น
        nm='ทดสอบ'+str(random.randint(100,999))
        await pg.evaluate(f"""(async()=>{{const j=await api('/api/register',{{name:'{nm}',pass:'abcd1234',data:{{...prof,st:{{...prof.st,kills:77,boss:2,maxLen:900,games:12,teamWin:3,killsGame:9}}}}}});saveAuth('{nm}',j.token);setProfile('acct',j.data)}})()""")
        await pg.wait_for_timeout(500)
        await pg.evaluate("document.getElementById('bRank').click()");await pg.wait_for_timeout(400)
        await pg.screenshot(path=OUT+'/stats.png')
        await pg.evaluate("document.querySelector('#lbTabs .tab[data-k=kills]').click()");await pg.wait_for_timeout(700)
        rows=await pg.evaluate("[...document.querySelectorAll('#lbList .lbrow')].map(r=>r.textContent)");print('kills lb',rows[:3])
        await pg.evaluate("document.querySelector('#lbList .lbrow[data-name]').scrollIntoView();document.querySelector('#lbList .lbrow[data-name]').click()");await pg.wait_for_timeout(700)
        prof_txt=await pg.evaluate("document.getElementById('sheetBody').innerText");await pg.screenshot(path=OUT+'/profile.png')
        print('profile has kills 77:', '77' in prof_txt)
        ok=r['keep'] and r['len']==5 and r['ok'] and t['kills']==1 and all(x.endswith(':1') or x.endswith(':3') for x in t['prog']) and any('77' in x for x in rows) and '77' in prof_txt
        print('errors',errs[:3]);print('PASS' if ok and not errs else 'FAIL');await b.close()
asyncio.run(main())
