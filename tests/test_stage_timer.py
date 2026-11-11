# ⏱ เวลาด่านผจญภัยตรงกลางบนสุด (11 พ.ย. 2026) · รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start
import asyncio
from playwright.async_api import async_playwright
OUT='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();errs=[];res=[]
        for nm,vp in [('port',{'width':390,'height':844}),('p360',{'width':360,'height':740}),('land',{'width':844,'height':390})]:
            pg=await (await b.new_context(viewport=vp,device_scale_factor=2,has_touch=True,is_mobile=True)).new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(500);await pg.evaluate("startStage(0)");await pg.wait_for_timeout(700)
            await pg.screenshot(path=OUT+f'/timer_{nm}.png')
            # pixel at top center should be the timer pill (dark/green border), ann pushed down
            r=await pg.evaluate("(()=>{const a=document.getElementById('ann').getBoundingClientRect();return{stageOn:document.body.classList.contains('stageOn'),annTop:Math.round(a.top),annVis:getComputedStyle(document.getElementById('ann')).opacity}})()")
            await pg.evaluate("stageClock=STAGE_T-8");await pg.wait_for_timeout(300);await pg.screenshot(path=OUT+f'/timer_{nm}_crit.png')
            await pg.evaluate("toMenu()");await pg.wait_for_timeout(200);r['after']=await pg.evaluate("document.body.classList.contains('stageOn')");res.append(r)
        print(res);print('errors',errs[:3]);ok=all(x['stageOn'] and not x['after'] and x['annTop']>=50 for x in res);print('PASS' if ok and not errs else 'FAIL');await b.close()
asyncio.run(main())
