# ยาวเกินทุก 1,000 → บอทไล่มากขึ้น (11 พ.ย. 2026): ชิป 🎯 + ข้อความครั้งเดียวต่อระดับ · ฝั่งบอทดู test_botsim.js · รัน: PORT=3456 npm start
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await (await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2)).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(600)
        await pg.evaluate("document.getElementById('sheet').classList.add('hidden');playEndless()");await pg.wait_for_timeout(2000)
        r=await pg.evaluate("""(async()=>{const fr=()=>new Promise(r=>requestAnimationFrame(r));player.safe=999;player.die=()=>{};
          const T=()=>texts.filter(t=>String(t.txt).includes('บอทไล่ล่า')).map(t=>t.txt);
          player.mass=1900;for(let i=0;i<3;i++)await fr();const t0=T().length,b0=bigTier(player);
          player.mass=3300;for(let i=0;i<3;i++)await fr();const t1=T(),b1=bigTier(player);
          player.mass=3400;for(let i=0;i<3;i++)await fr();const t2=T().length;
          player.mass=9000;for(let i=0;i<3;i++)await fr();return {b0,t0,b1,t1,t2,b5:bigTier(player),bot:bigTier(worms.find(w=>w.isBot)||{})}})()""")
        await pg.evaluate("player.mass=3300");await pg.wait_for_timeout(300);await pg.screenshot(path='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad/big_hunt.png')
        print(r);ok=r['b0']==0 and r['t0']==0 and r['b1']==2 and len(r['t1'])==1 and r['t2']==1 and r['b5']==5 and r['bot']==0
        print('errors',errs[:3]);print('PASS' if ok and not errs else 'FAIL');await b.close()
asyncio.run(main())
