# ประกาศ/ข้อความลอยต้องไม่บังหัวรถไฟ (7 พ.ย. 20:03): ประกาศขึ้นบนสุด · ข้อความที่เกิดตรงหัวเรา → แถบล่างจอ
import asyncio
from playwright.async_api import async_playwright
SP='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad/'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for nm,dev in [('portrait',p.devices['iPhone 13']),('landscape',p.devices['iPhone 13 landscape'])]:
            ctx=await b.new_context(**dev);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(700)
            await pg.evaluate("document.getElementById('sheet').classList.add('hidden');playEndless()");await pg.wait_for_timeout(2500)
            await pg.evaluate("""(()=>{const h=player.pts[0];texts.push({x:h.x,y:h.y-30,txt:'💎 +5 วิ พลังเร่ง!',t:3,c:'#fff'});texts.push({x:h.x,y:h.y-50,txt:'{G} ร่างทอง! ชนศัตรูให้ขาดได้ 1 ครั้ง',t:3,c:'#ffd23f'});
              texts.push({x:h.x,y:h.y-30,txt:'กำจัด บอท!',t:3,c:'#ffd23f'});announce('🌍 โลก ABCD · กด 📤 ชวนเพื่อนเข้ามาเล่นด้วยได้')})()""")
            await pg.wait_for_timeout(500)
            r=await pg.evaluate("(()=>{const a=document.getElementById('ann').getBoundingClientRect();return {annTop:Math.round(a.top),annBottom:Math.round(a.bottom),vh:innerHeight,headY:Math.round(innerHeight/2),meToasts:texts.filter(t=>t.me).length}})()")
            print(nm,r,errs[:2]);await pg.screenshot(path=SP+f'nocover_{nm}.png');await ctx.close()
        await b.close()
asyncio.run(main())
