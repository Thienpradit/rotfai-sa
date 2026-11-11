# ⭐ ร้านวันนี้ 6 ชิ้น (หายาก 2 + ลดราคา 4) เปลี่ยนทุกเที่ยงคืน + เปิดค้างข้ามวันรีเฟรชเอง (11 พ.ย. 2026) · รัน: PORT=3456 npm start
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await (await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2)).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(600)
        await pg.evaluate("prof.coins=500000;openShop('deal')");await pg.wait_for_timeout(400)
        names=lambda: pg.evaluate("[...document.querySelectorAll('#shopList .item.deal .tx')].map(e=>e.childNodes[0].textContent+'|'+(e.querySelector('.tag')||{}).textContent)")
        n0=await names();await pg.screenshot(path='/tmp/claude-0/-home-claude/25cb9392-c762-56ab-9405-b678b539416b/scratchpad/daily_shop.png',full_page=True)
        # ซื้อของลดราคาชิ้นแรก → เหรียญลดเท่าราคาลด
        r=await pg.evaluate("(()=>{const s=dealOf(bkkDay()).sales[0],c0=prof.coins;const btn=[...document.querySelectorAll('#shopList .item.deal')][2].querySelector('button');btn.click();return {paid:c0-prof.coins,price:s.price,full:s.p,owned:isOwned(s.cat,s.id)}})()")
        # ข้ามเที่ยงคืน (เลื่อนนาฬิกาในหน้า +1 วัน) → ภายใน ~15 วิ รายการเปลี่ยนเอง
        await pg.evaluate("(()=>{const o=Date.now;Date.now=()=>o()+864e5})()");await pg.wait_for_timeout(16500)
        n1=await names()
        print('today',n0);print('buy',r);print('tomorrow',n1)
        ok=len(n0)==6 and sum('หายาก' in x for x in n0)==2 and sum('ลด' in x for x in n0)==4 and r['paid']==r['price']<r['full'] and r['owned'] and len(n1)==6 and n1!=n0
        print('errors',errs[:3]);print('PASS' if ok and not errs else 'FAIL');await b.close()
asyncio.run(main())
