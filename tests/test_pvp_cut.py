# คนชนคนออนไลน์ (ฝั่งเครื่องผู้เล่น): (1) หัวผู้เล่นคนอื่นแตะลำตัวเราบนจอเรา → ส่ง hitme · ผีไม่ส่ง
# (2) ได้รับ crash → เราตาย + ส่ง die{k:คนที่เราชน}   (ฝั่งเซิร์ฟเวอร์ดู tests/test_pvp_cut.js)
# รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--disable-renderer-backgrounding']);pg=await (await b.new_context(viewport={'width':700,'height':500})).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(600)
        await pg.evaluate("document.getElementById('sheet').classList.add('hidden');playEndless()");await pg.wait_for_timeout(2000)
        r=await pg.evaluate("""(async()=>{const fr=()=>new Promise(r=>requestAnimationFrame(r));player.safe=999;player.mass=200;
          const h0=player.pts[0];for(const pt of player.pts){pt.x-=h0.x;pt.y-=h0.y}for(let i=0;i<40;i++)await fr();
          const a0=player.alive;const sent=[];const ns=netSend;window.netSend=o=>{sent.push(o);ns(o)};
          const w=new Worm('คนอื่น',SKINS[2],0,0,false);w.isRemote=true;w.netId=987654;w.mass=60;w.safe=0;w.ghost=0;worms.push(w);
          const keep=setInterval(()=>{w.alive=true;if(!worms.includes(w))worms.push(w)},5);const at=q=>{w.snaps=[{t:Date.now()+9e5,x:q.x,y:q.y,a:0,m:60}]};
          player.ghost=1;at(player.pts[60]);for(let i=0;i<5;i++)await fr();const ghostSent=sent.filter(o=>o.t==='hitme').length;const a1=player.alive;
          player.ghost=0;at(player.pts[60]);for(let i=0;i<5;i++)await fr();const hit=sent.filter(o=>o.t==='hitme');const a2=[player.alive,w.pts[0].x|0,player.pts[60].x|0,w.safe,w.ghost,w.alive];
          const kw=w;
          clearInterval(keep);player.safe=0;player.ghost=0;netMsg({t:'crash',k:987654});worms=worms.filter(o=>o!==kw);const die=sent.find(o=>o.t==='die');
          window.netSend=ns;return {types:sent.map(o=>o.t).filter(t=>t!=='st'),a0,a1,a2,ghostSent,hitme:hit.map(o=>o.id),died:!player.alive,dieK:die&&die.k}})()""")
        print(r);ok=r['ghostSent']==0 and r['hitme']==[987654] and r['died'] and r['dieK']==987654
        print('errors',errs[:3]);print('PASS' if ok and not errs else 'FAIL');await b.close()
asyncio.run(main())
