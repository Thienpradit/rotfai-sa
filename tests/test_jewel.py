# เครื่องประดับ 💍📿 (แหวน/สร้อย/ต่างหู) = พลอย 5 เม็ด · 6% · รอบ ๆ ไม่มีพลอย · ออฟไลน์ + ออนไลน์ (เซิร์ฟเวอร์ส่ง index สี 7–9)
# รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start  แล้ว python tests/test_jewel.py [โฟลเดอร์ภาพ]
import asyncio, sys
from playwright.async_api import async_playwright
OUT=sys.argv[1] if len(sys.argv)>1 else '/tmp'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await (await b.new_context(viewport={'width':700,'height':500})).new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/'); await pg.wait_for_timeout(600)
        await pg.evaluate("document.getElementById('sheet').classList.add('hidden');startGame('inf');player.safe=999")
        n=await pg.evaluate("foods.filter(f=>f.j!==undefined).length"); print('offline jewels in world', n, 'gems', await pg.evaluate("foods.filter(f=>f.j===undefined).length"), 'weight', await pg.evaluate("foodW()"))
        near=await pg.evaluate("foods.filter(f=>f.j===undefined&&!f.ttl&&!f.dead&&foods.some(g=>g.j!==undefined&&Math.hypot(g.x-f.x,g.y-f.y)<JEWEL_CLEAR)).length"); print('offline gems near jewels', near)
        g=await pg.evaluate("""(()=>{const h=player.pts[0];foods=foods.filter(f=>Math.hypot(f.x-h.x,f.y-h.y)>400);const a=player.angle;
          for(let j=0;j<3;j++)foods.push(mkFood(h.x+Math.cos(a)*(120+j*70)+Math.sin(a)*(j-1)*60,h.y+Math.sin(a)*(120+j*70)-Math.cos(a)*(j-1)*60,JEWEL_V,undefined,7+j));
          foods.push(mkFood(h.x+Math.cos(a)*60,h.y+Math.sin(a)*60,1,undefined,2));return player.mass})()""")
        await pg.wait_for_timeout(250); await pg.screenshot(path=OUT+'/jewels.png')
        m0=await pg.evaluate("player.mass")
        await pg.evaluate("(()=>{const h=player.pts[0],f=foods.find(f=>f.j===0);f.x=h.x+5;f.y=h.y})()"); await pg.wait_for_timeout(200)
        m1=await pg.evaluate("player.mass"); print('jewel gain', round(m1-m0,2), 'expect', 5*0.7)
        ok_off = 40 <= n <= 160 and near < 10 and abs((m1-m0)-3.5)<.6
        # ออนไลน์
        await pg.evaluate("toMenu()"); await pg.evaluate("playEndless()"); await pg.wait_for_timeout(2500)
        on=await pg.evaluate("[!!NET,foods.length,foods.filter(f=>f.j!==undefined).length,foods.filter(f=>f.j!==undefined).every(f=>f.v===5),foods.filter(f=>f.j===undefined&&!f.ttl&&foods.some(g=>g.j!==undefined&&Math.hypot(g.x-f.x,g.y-f.y)<110)).length]"); print('online foods/jewels/v=5/gems near jewels', on)
        print('errors',errs[:3]); print('PASS' if ok_off and on[0] and on[2]>=30 and on[3] and on[4]<15 and not errs else 'FAIL'); await b.close()
asyncio.run(main())
