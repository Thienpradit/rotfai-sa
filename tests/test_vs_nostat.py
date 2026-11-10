# ⚔️ 2v2 ไม่นับเข้าสถิติ/แรงก์/ตารางอันดับ (10 พ.ย. 2026) — นับแค่ vsGames/vsKills/teamWin (ภารกิจ 2v2) · เหรียญยังได้
# โลกออนไลน์ยังนับเหมือนเดิม · รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start
import asyncio
from playwright.async_api import async_playwright
SNAP="JSON.stringify({st:prof.st,rp:prof.rp,onrp:prof.onrp,coins:prof.coins,best:prof.best})"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--disable-renderer-backgrounding']);pg=await (await b.new_context(viewport={'width':700,'height':600})).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(600)
        await pg.evaluate("document.getElementById('sheet').classList.add('hidden');netConnect('NOST','')");await pg.wait_for_timeout(1200)
        await pg.click('#startBtn');await pg.wait_for_timeout(2500)
        import json
        before=json.loads(await pg.evaluate(SNAP))
        await pg.evaluate("""(()=>{player.safe=99;player.mass=900;player.maxMass=900;const b=worms.find(w=>w.isBot&&w.alive);
          netMsg({t:'kill',v:b.netId,k:NET.id});netMsg({t:'kill',v:b.netId,k:NET.id,b:1});track('whites');trackMax('maxLen',5000);addRP(50);
          netEnd({winner:NET.me.team,A:5,B:1,mvp:NET.id,players:[]})})()""")
        after=json.loads(await pg.evaluate(SNAP));note=await pg.evaluate("document.getElementById('sheetBody').textContent.includes('2v2 ไม่นับ')")
        d={k:(before['st'].get(k,0),after['st'].get(k,0)) for k in set(before['st'])|set(after['st']) if before['st'].get(k,0)!=after['st'].get(k,0)}
        print('stat changes',d);print('rp',before['rp'],after['rp'],'onrp',before['onrp'],after['onrp'],'coins',before['coins'],'->',after['coins'],'best',before['best']==after['best'],'note',note)
        ok_vs=set(d)<= {'vsGames','vsKills','teamWin','coinsEarned'} and d.get('vsGames')==(before['st'].get('vsGames',0),before['st'].get('vsGames',0)+1) and d.get('vsKills',(0,0))[1]-d.get('vsKills',(0,0))[0]==2 \
            and after['rp']==before['rp'] and after['onrp']==before['onrp'] and after['coins']>before['coins'] and before['best']==after['best'] and note
        # โลกออนไลน์ยังนับ
        await pg.evaluate("netLeave(true);toMenu();playEndless()");await pg.wait_for_timeout(2500)
        b2=json.loads(await pg.evaluate(SNAP))
        await pg.evaluate("(()=>{player.safe=99;const b=worms.find(w=>w.isBot&&w.alive);netMsg({t:'kill',v:b.netId,k:NET.id});addRP(7)})()")
        a2=json.loads(await pg.evaluate(SNAP))
        ok_ffa=a2['st'].get('kills',0)==b2['st'].get('kills',0)+1 and a2['st'].get('okills',0)==b2['st'].get('okills',0)+1 and a2['rp']==b2['rp']+7
        print('ffa kills',b2['st'].get('kills'),'->',a2['st'].get('kills'),'rp',b2['rp'],'->',a2['rp'])
        print('errors',errs[:3]);print('PASS' if ok_vs and ok_ffa and not errs else 'FAIL',ok_vs,ok_ffa);await b.close()
asyncio.run(main())
