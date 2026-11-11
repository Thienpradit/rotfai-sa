# ⚔️ 2v2 ไม่นับความยาวเข้าสถิติ (11 พ.ย. 2026) + ป้ายเตือนก่อนเล่น · กำจัด/RP/เกมยังนับ · โลกออนไลน์ยังนับยาว · รัน: PORT=3456 npm start
import asyncio,json
from playwright.async_api import async_playwright
SNAP="JSON.stringify({ml:prof.st.maxLen||0,oml:prof.st.omaxLen||0,k:prof.st.kills||0,g:prof.st.games||0,vg:prof.st.vsGames||0,rp:prof.rp})"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await (await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2)).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(600)
        await pg.evaluate("document.getElementById('playOnline').click()");await pg.wait_for_timeout(300)
        join_note=await pg.evaluate("(document.querySelector('#sheetBody .vsnote')||{}).textContent||''")
        await pg.evaluate("document.getElementById('sheet').classList.add('hidden');netConnect('NOLEN','')");await pg.wait_for_timeout(1200)
        lobby_note=await pg.evaluate("(document.querySelector('#sheetBody .vsnote')||{}).textContent||''");await pg.screenshot(path='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad/vs_lobby_note.png')
        await pg.click('#startBtn');await pg.wait_for_timeout(3300)
        ann=await pg.evaluate("document.getElementById('ann').textContent")
        b0=json.loads(await pg.evaluate(SNAP))
        await pg.evaluate("(async()=>{player.safe=99;player.die=()=>{};player.mass=player.maxMass=4000;for(let i=0;i<5;i++)await new Promise(r=>requestAnimationFrame(r));const bt=worms.find(w=>w.isBot&&w.alive);netMsg({t:'kill',v:bt.netId,k:NET.id});netEnd({winner:NET.me.team,A:5,B:1,mvp:NET.id,players:[]})})()");await pg.wait_for_timeout(500)
        a0=json.loads(await pg.evaluate(SNAP));end_note='ไม่นับความยาว' in await pg.evaluate("document.getElementById('sheetBody').textContent")
        await pg.evaluate("netLeave(true);toMenu();playEndless()");await pg.wait_for_timeout(2500)
        await pg.evaluate("(async()=>{player.safe=99;player.mass=player.maxMass=3000;for(let i=0;i<5;i++)await new Promise(r=>requestAnimationFrame(r))})()");await pg.wait_for_timeout(300)
        f0=json.loads(await pg.evaluate(SNAP))
        print('join note:',join_note[:40],'| lobby note:',bool(lobby_note),'| start announce:',ann);print('2v2 before',b0,'after',a0,'end note',end_note);print('ffa after',f0)
        ok=bool(join_note) and bool(lobby_note) and '2v2' in ann and a0['ml']==b0['ml'] and a0['oml']==b0['oml'] and a0['k']==b0['k']+1 and a0['vg']==b0['vg']+1 and a0['g']==b0['g']+1 and a0['rp']>b0['rp'] and end_note and f0['ml']>=3000 and f0['oml']>=3000
        print('errors',errs[:3]);print('PASS' if ok and not errs else 'FAIL');await b.close()
asyncio.run(main())
