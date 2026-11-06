# ระบบหัวใจบอท: บอทชนลำตัวผู้เล่น = เสียหัวใจ (3 ดวง) ครบ 3 ครั้งตาย · บอทชนบอทผ่านกันได้ · หัวใจโชว์เหนือบอท (ออฟไลน์ + ออนไลน์)
# รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start
import asyncio
from playwright.async_api import async_playwright
SP='/tmp/'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--disable-renderer-backgrounding']);pg=await (await b.new_context(viewport={'width':900,'height':650})).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(600)
        await pg.evaluate("document.getElementById('sheet').classList.add('hidden')")
        await pg.evaluate("startGame('inf')");await pg.wait_for_timeout(500)
        r=await pg.evaluate("""(async()=>{const fr=()=>new Promise(r=>requestAnimationFrame(r));player.mass=200;player.safe=999;await new Promise(r=>setTimeout(r,800));
          const bots=worms.filter(w=>w.isBot&&w.alive);const w=bots[0];const res=[];
          const hit=async()=>{const q=player.pts[30];for(const pt of w.pts){pt.x+=q.x-w.pts[0].x;pt.y+=q.y-w.pts[0].y}w.safe=0;w.ghost=0;await fr();await fr();res.push([w.alive,w.hearts])};
          await hit();await hit();const k0=player.kills;await hit();
          const [x1,x2]=worms.filter(o=>o.isBot&&o.alive&&o.pts.length>30);const q=x2.pts[20];for(const pt of x1.pts){pt.x+=q.x-x1.pts[0].x;pt.y+=q.y-x1.pts[0].y}x1.safe=x1.ghost=0;await fr();await fr();
          return {hits:res,kills:player.kills-k0,botbot:[x1.alive,x1.hearts,x2.alive,x2.hearts],allBotsHaveHearts:worms.filter(o=>o.isBot).every(o=>o.hearts!==undefined)}})()""")
        print('offline',r)
        await pg.evaluate("toMenu()");await pg.evaluate("playEndless()");await pg.wait_for_timeout(3500)
        r=await pg.evaluate("(()=>{const bs=worms.filter(w=>w.isBot&&w.alive&&!w.isBoss);return [bs.length,bs.filter(w=>w.hearts===3).length]})()")
        print('online bots with 3 hearts',r)
        await pg.evaluate("cam.z=.9;player.safe=999");await pg.wait_for_timeout(600);await pg.screenshot(path=SP+'hearts.png')
        print('errors',errs);await b.close()
asyncio.run(main())
