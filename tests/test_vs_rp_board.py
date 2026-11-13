# 2v2 (13 พ.ย. 20:1x): ทีมแพ้ = กำจัด×2 − (5+3×ขั้น) ไม่เกิน 0 · ชนะ = กำจัด×2+15 · เสมอ = กำจัด×2 · ป้ายเวลา/คะแนนกลางจอ (drawVsBoard)
# รัน: PORT=3456 MATCH_SECS=120 node server.js
import asyncio,time
from playwright.async_api import async_playwright
ok=[]
def chk(n,c):ok.append(c);print(('✓ ' if c else '✗ ')+n)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await (await b.new_context(viewport={'width':844,'height':390})).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(700)
        async def round_(winner,kills):
            await pg.evaluate("document.getElementById('sheet').classList.add('hidden');openSheet('🌐 ออนไลน์ 2v2',renderOnlineJoin);netConnect('RP"+str(int(time.time()*1000)%100000)+"','')");await pg.wait_for_timeout(900)
            await pg.evaluate("netSend({t:'start'})");await pg.wait_for_timeout(1800)
            board=await pg.evaluate("({on:document.body.classList.contains('vsOn'),bottom:VSB.bottom})")
            my=await pg.evaluate("NET.me?NET.me.team:'A'");other='B' if my=='A' else 'A'
            w={'win':my,'lose':other,'draw':'draw'}[winner]
            r0=await pg.evaluate(f"prof.rp=3000;prof.onrp=3000;player.kills={kills};prof.rp")   # ทอง (ขั้น 2) → แพ้หัก 11
            await pg.evaluate("document.getElementById('rwPop')&&document.getElementById('rwPop').remove()")
            await pg.evaluate(f"netEnd({{winner:'{w}',A:300,B:200,mvp:null,players:[]}})");await pg.wait_for_timeout(300)
            r1=await pg.evaluate("prof.rp");rp=await pg.evaluate("NET.lastEnd&&NET.lastEnd.rp")
            await pg.evaluate("try{netLeave&&netLeave()}catch(e){};try{NET&&NET.ws.close()}catch(e){};NET=null;document.getElementById('rwPop')&&document.getElementById('rwPop').remove();toMenu()");await pg.wait_for_timeout(600)
            return board,r1-r0,rp
        board,d,rp=await round_('lose',4);chk(f'ระหว่างเล่น 2v2 มีป้ายเวลา/คะแนนกลางจอ ({board})',board['on'] and board['bottom']>60)
        chk(f'ทีมแพ้ แรงก์ทอง (กำจัด 4) = 8−11 = −3: เปลี่ยน {d} · ผลรอบ {rp}',d==-3 and rp==-3)
        _,d,rp=await round_('lose',0);chk(f'ทีมแพ้ แรงก์ทอง (กำจัด 0) = −11: เปลี่ยน {d}',d==-11)
        _,d,rp=await round_('lose',7);chk(f'ทีมแพ้ แรงก์ทอง (กำจัด 7) ไม่เกิน 0: เปลี่ยน {d}',d==0)
        _,d,rp=await round_('win',4);chk(f'ทีมชนะ (กำจัด 4) ได้ 4×2+15 = 23: เปลี่ยน {d}',d==23)
        _,d,rp=await round_('draw',3);chk(f'เสมอ (กำจัด 3) ได้ 3×2 = 6: เปลี่ยน {d}',d==6)
        chk('ออกจาก 2v2 แล้วป้ายหาย',await pg.evaluate("!document.body.classList.contains('vsOn')"))
        chk('ไม่มี error',not errs);print(errs[:3])
        print('PASS' if all(ok) else 'FAIL');await b.close()
asyncio.run(main())
