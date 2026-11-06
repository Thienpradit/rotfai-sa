# บอสออนไลน์ชนลำตัวเรา: ตรวจในเครื่องจากภาพจริง (ห่าง = ไม่ขาด, แตะ = ขาด 1 ครั้ง + กันซ้ำ 1.5 วิ) · รันเซิร์ฟเวอร์ก่อน PORT=3456 npm start
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--disable-renderer-backgrounding','--disable-background-timer-throttling']);pg=await (await b.new_context(viewport={'width':800,'height':600})).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(600)
        await pg.evaluate("document.getElementById('sheet').classList.add('hidden');playEndless()");await pg.wait_for_timeout(3500)
        r=await pg.evaluate("""(async()=>{NET.ws.onmessage=null;worms=worms.filter(w=>w===player);player.mass=300;player.ghost=0;player.safe=0;player.pu={};await new Promise(r=>setTimeout(r,900));
          const fr=()=>new Promise(r=>requestAnimationFrame(r));
          const bs=new Worm('👑 บอส',['#300','#f33'],0,0,false,{});bs.mass=900;bs.isRemote=true;bs.isBot=true;bs.isBoss=true;bs.netId=-999;bs.maxHp=120;bs.hp=120;worms.push(bs);bossActive=bs;
          const put=(i,off)=>{const q=player.pts[Math.min(i,player.pts.length-1)];for(const t of bs.pts){t.x=q.x+off;t.y=q.y+off}};
          const n0=player.pts.length;
          for(let k=0;k<8;k++){put(90,300);await fr()}
          const n1=player.pts.length;
          put(90,0);await fr();await fr();
          const n2=player.pts.length,cd=player.bossCD;
          for(let k=0;k<8;k++){put(40,0);await fr()}
          const n3=player.pts.length;
          return {n0,far:n1,touch:n2,cd,cooldown:n3,alive:player.alive,msg:texts.some(t=>t.txt.includes('บอสชนขาด'))}})()""")
        print(r,errs[:2]);await b.close()
asyncio.run(main())
