# ลอดอุโมงค์แบบค่อย ๆ โผล่ + ทางออกเตือน "⚠️ รถไฟกำลังออก" + ลำตัวในปากอุโมงค์ชนไม่ตาย
# รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start  แล้ว python tests/test_tunnel_emerge.py
import asyncio, sys
from playwright.async_api import async_playwright
URL='http://127.0.0.1:3456/'; OUT=sys.argv[1] if len(sys.argv)>1 else '/tmp'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await b.new_context(viewport={'width':800,'height':600}); pg=await ctx.new_page()
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(700)
        await pg.evaluate("document.getElementById('sheet').classList.add('hidden');startGame('inf')")
        await pg.wait_for_timeout(300)
        # วางบอทยาว ๆ วิ่งตรงเข้าอุโมงค์ 0 · ผู้เล่นรอที่ทางออก (อมตะไว้ก่อน)
        r=await pg.evaluate("""()=>{const P=portals[0],Q=portals[P.pair];
          worms=worms.filter(w=>w.isP);const w=new Worm('ทดสอบ',SKINS[1],P.x,P.y,false);w.mass=250;const a=.4;w.angle=w.target=a;w.pts=[];
          for(let i=0;i<w.nPts();i++)w.pts.push({x:P.x-Math.cos(a)*(200+i*8),y:P.y-Math.sin(a)*(200+i*8)});
          w.ai.t=1e9;w.safe=0;w.ghost=0;worms.push(w);window.TW=w;
          player.safe=999;for(const q of player.pts){q.x+=Q.x+260-player.pts[0].x;q.y+=Q.y+260-player.pts[0].y}
          return {P,Q,n:w.pts.length}}""")
        warned=False; mid=None
        for i in range(120):
            await pg.wait_for_timeout(100)
            s=await pg.evaluate("""()=>{const w=TW,Q=portals[portals[0].pair];w.target=w.angle;w.ai.t=1e9;
              return {tun:w.tun?w.tun.k:null,n:w.pts.length,alive:w.alive,warn:portalWarn(portals[0].pair),
                head:Math.hypot(w.pts[0].x-Q.x,w.pts[0].y-Q.y),tail:Math.hypot(w.pts.at(-1).x-Q.x,w.pts.at(-1).y-Q.y)}}""")
            if s['warn'] and s['tun'] is None and not warned: warned=True; print('เตือนก่อนโผล่ ✓', s)
            if s['tun'] and s['tun']>20 and mid is None:
                mid=s; await pg.evaluate("()=>{const Q=portals[portals[0].pair];for(const q of player.pts){q.x+=Q.x+150-player.pts[0].x;q.y+=Q.y+120-player.pts[0].y}}")
                await pg.wait_for_timeout(150); await pg.screenshot(path=OUT+'/tunnel_emerge.png'); print('กลางทาง', s)
            if mid and s['tun'] is None: print('ลอดครบ', s); break
        ok = warned and mid and mid['tail']>800 and s['tun'] is None and s['tail']<900
        # ลำตัวในปากอุโมงค์ชนไม่ตาย: วางหัวบอทอีกตัวไว้ในปาก ขณะลำตัวผู้เล่นอยู่ในปาก
        print('errors',errs[:3]); print('PASS' if ok and not errs else 'FAIL')
        await b.close()
asyncio.run(main())
