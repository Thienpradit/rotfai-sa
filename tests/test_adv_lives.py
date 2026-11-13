# ผจญภัย: 3 ชีวิตต่อด่าน · หมดแล้วเริ่มด่านใหม่เอง (11 พ.ย. 2026) · รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start
import asyncio
from playwright.async_api import async_playwright
OUT='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await (await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2)).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(600)
        await pg.evaluate("startStage(1)") if False else await pg.evaluate("prof.stage[0]=1;STAGES[1].g=['kills',5];startStage(1)")   # 1-2 = กำจัด
        await pg.wait_for_timeout(800)
        r=[]
        for k in range(2):
            await pg.evaluate("player.kills=1;player.ghost=0;player.safe=0;player.die(null)");await pg.wait_for_timeout(1900)
            r.append(await pg.evaluate("({life:STAGE_LIFE,state,alive:player.alive,kills:player.kills,ghost:player.ghost>0,clock:stageClock>2,over:!document.getElementById('over').classList.contains('hidden'),ws:worms.filter(w=>w.isP).length})"))
        await pg.screenshot(path=OUT+'/adv_life.png')
        await pg.evaluate("player.ghost=0;player.safe=0;player.die(null)");await pg.wait_for_timeout(1900)
        o=await pg.evaluate("({life:STAGE_LIFE,state,t:document.getElementById('overTitle').textContent,a:document.getElementById('again').textContent,res:STAGE_RES&&STAGE_RES.why,st:prof.stage[1]||0})")
        await pg.screenshot(path=OUT+'/adv_out.png')
        await pg.wait_for_timeout(5600)
        rs=await pg.evaluate("({life:STAGE_LIFE,state,code:STAGE&&STAGE.code,clock:stageClock<2,over:!document.getElementById('over').classList.contains('hidden'),res:STAGE_RES})")
        # หมดชีวิตแล้วกดกลับหน้าแรก = ไม่เริ่มใหม่เอง
        for k in range(3):
            await pg.evaluate("player.ghost=0;player.safe=0;player.die(null)");await pg.wait_for_timeout(1900)
        await pg.click('#toMenu');await pg.wait_for_timeout(6000);cm=await pg.evaluate("({state,stage:!!STAGE})")
        print('lives',r);print('out',o);print('restart',rs);print('cancel',cm)
        ok=[x['life'] for x in r]==[2,1] and all(x['alive'] and x['state']=='play' and x['kills']==1 and x['ghost'] and not x['over'] and x['ws']==1 for x in r) \
          and o['life']==0 and 'หมด 3 ชีวิต' in o['t'] and 'เริ่มด่านใหม่ใน' in o['a'] and o['res']=='lives' and o['st']==0 \
          and rs['life']==3 and rs['state']=='play' and rs['code']=='1-2' and rs['clock'] and not rs['over'] and rs['res'] is None and cm['state']=='menu' and not cm['stage']
        print('errors',errs[:3]);print('PASS' if ok and not errs else 'FAIL');await b.close()
asyncio.run(main())
