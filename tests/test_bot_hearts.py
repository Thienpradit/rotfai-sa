# บอส 👑 หัวใจ 3 ดวง: บอสชนตัวเรา = บอสเสีย 1 ดวง (เราไม่ขาด) ครบ 3 ครั้งบอสตาย · เราชนบอส = เด้งกลับ ไม่เสียอะไร · บอทธรรมดาชนเราครั้งเดียวตาย
# (ออฟไลน์ + ออนไลน์) รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--disable-renderer-backgrounding']);pg=await (await b.new_context(viewport={'width':900,'height':650})).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(600)
        await pg.evaluate("document.getElementById('sheet').classList.add('hidden')")
        await pg.evaluate("startGame('inf')");await pg.wait_for_timeout(500)
        r=await pg.evaluate("""(async()=>{const fr=()=>new Promise(r=>requestAnimationFrame(r));player.mass=250;player.safe=0;player.ghost=0;await new Promise(r=>setTimeout(r,900));
          const put=(w,i)=>{const q=player.pts[i];for(const pt of w.pts){pt.x=q.x;pt.y=q.y}w.safe=0;w.ghost=0};
          spawnBoss();const bs=bossActive;const res=[];const n0=player.pts.length;
          for(let k=0;k<3;k++){player.safe=999;put(bs,40);bs.safe=0;await fr();await fr();res.push([bs.alive,bs.hp]);}
          const bot=worms.find(w=>!w.isP&&!w.isBoss&&w.alive);put(bot,40);await fr();await fr();
          return {bossHits:res,playerNotCut:player.pts.length>=n0-2,botDiesOneHit:!bot.alive}})()""")
        print('offline',r)
        await pg.evaluate("toMenu()");await pg.evaluate("playEndless()");await pg.wait_for_timeout(3000)
        r=await pg.evaluate("(()=>{const bs=worms.filter(w=>w.isBot&&w.alive&&!w.isBoss);return [bs.length,bs.every(w=>w.hearts===undefined)]})()")
        print('online normal bots have no hearts',r)
        print('errors',errs);await b.close()
asyncio.run(main())
