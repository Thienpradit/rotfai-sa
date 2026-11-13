# 🗺️ ผจญภัย 30 ด่าน (11 พ.ย. 2026): เลือกด่าน, สิ่งกีดขวางชนตาย/โคลนช้า/ไม้กั้นเปิดปิด, ผ่านด่านได้ดาว+เหรียญครั้งแรก, ปลดด่านถัดไป, ไม่ได้ RP · รัน: PORT=3456 npm start
import asyncio
from playwright.async_api import async_playwright
SP='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await (await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2)).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(700)
        await pg.evaluate("document.getElementById('sheet').classList.add('hidden')");await pg.screenshot(path=SP+'/adv_menu.png')
        await pg.evaluate("$('playAdv').classList.remove('hidden')");await pg.click('#playAdv');await pg.wait_for_timeout(400)
        cards=await pg.evaluate("[...document.querySelectorAll('.stc')].map(e=>e.className)")
        await pg.screenshot(path=SP+'/adv_select.png')
        await pg.evaluate("document.querySelector('.stc[data-i=\"1\"]').click()");await pg.wait_for_timeout(200)
        locked=await pg.evaluate("mode")
        await pg.evaluate("document.querySelector('.stc[data-i=\"0\"]').click()");await pg.wait_for_timeout(1500)
        st0=await pg.evaluate("JSON.stringify(prof.st)")
        r1=await pg.evaluate("({mode,stage:STAGE&&STAGE.code,ai:worms.filter(w=>!w.isP).length,obst:OBST.length,muds:MUDS.length,alive:player.alive,rp:prof.rp,coins:prof.coins,inRock:OBST.some(o=>obstStatic(player.pts[0].x,player.pts[0].y,0))})")
        # ชนหิน = ตาย
        await pg.evaluate("(()=>{player.ghost=0;player.safe=0;const o=OBST.find(o=>o.k==='rock');const h=player.pts[0];const dx=o.x-h.x,dy=o.y-h.y;for(const q of player.pts){q.x+=dx;q.y+=dy}})()");await pg.wait_for_timeout(400)
        dead=await pg.evaluate("player.alive");await pg.wait_for_timeout(1800)
        resp=await pg.evaluate("[STAGE_LIFE,state,player.alive]")   # ❤️ 3 ชีวิต: ตายครั้งแรกเกิดใหม่ในด่านเดิม
        await pg.evaluate("STAGE_LIFE=1;player.ghost=0;player.safe=0;player.die(null)");await pg.wait_for_timeout(1900)
        fail=await pg.evaluate("[state,document.getElementById('overTitle').textContent,document.getElementById('again').textContent,prof.coins]");print('respawn',resp)
        assert resp==[2,'play',True],resp
        # เล่นใหม่ → ผ่านด่าน (ยาวถึงเป้า) เร็ว ๆ = 3 ดาว
        await pg.click('#again');await pg.wait_for_timeout(800)
        await pg.evaluate("player.mass=STAGE.g[1]+5");await pg.wait_for_timeout(500)
        win=await pg.evaluate("[state,document.getElementById('overTitle').textContent,document.getElementById('coinEarn').innerText,document.getElementById('again').textContent,prof.stage.slice(0,3),prof.coins,prof.rp,prof.st.maxLen||0]")
        await pg.screenshot(path=SP+'/adv_clear.png')
        await pg.evaluate("track('kills');trackMax('maxLen',9999)")
        st1=await pg.evaluate("JSON.stringify(Object.fromEntries(Object.entries(prof.st).filter(([k])=>k!=='coinsEarned')))");st0=__import__('json').loads(st0);st0.pop('coinsEarned',None)
        stats_same=__import__('json').loads(st1)==st0;note=await pg.evaluate("document.getElementById('rankOver').textContent");print('stats unchanged',stats_same,'| note',note)
        # ด่านถัดไป + ไม้กั้น/โคลน (ด่าน 15)
        pop=await pg.evaluate("!!document.getElementById('rwPop')&&document.getElementById('rwN').textContent");print('reward popup',pop);await pg.click('#rwOk')
        await pg.click('#again');await pg.wait_for_timeout(800);nxt=await pg.evaluate("STAGE.code")
        await pg.evaluate("prof.stage=Array(14).fill(1);startStage(14)");await pg.wait_for_timeout(1200)
        g=await pg.evaluate("""(()=>{const o=OBST.find(o=>o.k==='gate');const res=[];for(const t of [0,.55,.7,.95]){stageClock=((t*o.per-o.ph)%o.per+o.per)%o.per;res.push(gatePhase(o)+':'+!!obstHit(o.x,o.y,10))}stageClock=0;
          const m=MUDS[0];const w=player;w.ghost=99;const h=w.pts[0];const dx=m.x-h.x,dy=m.y-h.y;for(const q of w.pts){q.x+=dx;q.y+=dy}return {gate:res,kinds:[...new Set(OBST.map(o=>o.k))],n:OBST.length,ai:worms.filter(x=>!x.isP).length,mud:inMud(w.pts[0])}})()""")
        await pg.evaluate("(()=>{const o=OBST.find(o=>o.k==='gate');const h=player.pts[0];const dx=o.x-120*Math.cos(o.a-Math.PI/2)-h.x,dy=o.y-120*Math.sin(o.a-Math.PI/2)-h.y;for(const q of player.pts){q.x+=dx;q.y+=dy}player.angle=o.a-Math.PI/2;cam.x=o.x;cam.y=o.y})()")
        await pg.wait_for_timeout(600);await pg.screenshot(path=SP+'/adv_stage15.png')
        print('cards',len(cards),sum('lock' in c for c in cards),'| locked click mode',locked);print('stage1',r1);print('rock death',dead,fail);print('clear',win);print('next',nxt);print('stage15',g)
        ok=len(cards)==30 and r1['stage']=='1-1' and r1['obst']>0 and not r1['inRock'] and not dead and 'หมด 3 ชีวิต' in fail[1] and fail[3]==r1['coins'] and win[4][0]==3 and win[5]==r1['coins']+3*40+20 and win[6]==r1['rp'] and win[3]=='ด่านต่อไป ▶' and nxt=='1-2' and g['gate'][0].startswith('open:false') and g['gate'][3].startswith('closed:true') and g['mud'] and 'gate' in g['kinds'] and stats_same and 'ไม่นับสถิติ' in note
        print('errors',errs[:3]);print('PASS' if ok and not errs else 'FAIL');await b.close()
asyncio.run(main())
