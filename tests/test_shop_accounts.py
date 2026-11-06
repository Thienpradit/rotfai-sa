# ทดสอบร้านค้าใหม่ + บัญชี (รหัสกู้คืน/เปลี่ยนรหัส/ลืมรหัส) + กันโกง + ฤดูกาล + หวูด + เอฟเฟกต์กำจัด
# รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start  แล้ว python tests/test_shop_accounts.py
import asyncio, random
from playwright.async_api import async_playwright
URL = 'http://127.0.0.1:3456/'
ARGS = ['--disable-renderer-backgrounding', '--disable-background-timer-throttling', '--disable-backgrounding-occluded-windows']
NAME = 'ทดสอบ' + str(random.randint(100, 999))
async def main():
    async with async_playwright() as p:
        errs = []
        b = await p.chromium.launch(args=ARGS)
        pg = await (await b.new_context(viewport={'width': 420, 'height': 860})).new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(800)
        ev = pg.evaluate
        # ---------- ลงทะเบียน → รหัสกู้คืน ----------
        print('welcome sheet', await ev("document.getElementById('sheetTitle').textContent"))
        await pg.fill('#acName', NAME); await pg.fill('#acPass', 'pass1111'); await pg.fill('#acPass2', 'pass1111'); await pg.click('#acGo'); await pg.wait_for_timeout(700)
        code = await ev("(document.querySelector('.rcode')||{}).textContent")
        print('registered', await ev("[ACCT.mode,ACCT.name]"), 'recovery code', code, 'sheet', await ev("document.getElementById('sheetTitle').textContent"))
        await pg.screenshot(path='/tmp/s_recovery.png')
        await pg.click('#rcOk')
        # ---------- เปลี่ยนรหัสผ่าน ----------
        await pg.click('#acctBtn'); await pg.click('#acPw')
        await pg.fill('#pw0', 'pass1111'); await pg.fill('#pw1', 'pass2222'); await pg.fill('#pw2', 'pass2222'); await pg.click('#pwGo'); await pg.wait_for_timeout(600)
        print('change pw ->', await ev("document.getElementById('acMore').textContent.trim()"))
        await pg.click('#acOut'); await pg.wait_for_timeout(300)
        await pg.click(".tab[data-k=login]"); await pg.fill('#acName', NAME); await pg.fill('#acPass', 'pass1111'); await pg.click('#acGo'); await pg.wait_for_timeout(500)
        print('login old pw ->', await ev("document.getElementById('acSt').textContent"))
        await pg.fill('#acPass', 'pass2222'); await pg.click('#acGo'); await pg.wait_for_timeout(600)
        print('login new pw ->', await ev("[ACCT.mode,ACCT.name]"))
        # ---------- ลืมรหัสผ่าน ----------
        await pg.click('#acctBtn'); await pg.click('#acOut'); await pg.wait_for_timeout(300)
        await pg.click(".tab[data-k=login]"); await pg.click('#acForgot')
        await pg.fill('#acName', NAME); await pg.fill('#acCode', 'WRON-GCOD-EXXX'); await pg.fill('#acPass', 'pass3333'); await pg.fill('#acPass2', 'pass3333'); await pg.click('#acGo'); await pg.wait_for_timeout(500)
        print('reset wrong code ->', await ev("document.getElementById('acSt').textContent"))
        await pg.fill('#acCode', code.lower().replace('-', ' ')); await pg.click('#acGo'); await pg.wait_for_timeout(700)
        code2 = await ev("(document.querySelector('.rcode')||{}).textContent")
        print('reset ok ->', await ev("[ACCT.mode,ACCT.name]"), 'new code', code2, 'differs', code2 != code)
        await pg.click('#rcOk')
        r = await ev(f"fetch('/api/login',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{name:'{NAME}',pass:'pass3333'}})}}).then(r=>r.status)")
        print('login with reset pw status', r)
        # ---------- กันโกง: แก้เหรียญในเบราว์เซอร์แล้วซื้อของแพง ----------
        await ev("prof.coins=400000;openShop('loco')"); await pg.wait_for_timeout(200)
        await pg.screenshot(path='/tmp/s_shop_loco.png')
        await pg.click("#shopList .item:nth-child(6) .sbtn"); await pg.wait_for_timeout(1200)
        print('cheat buy comet -> coins', await ev("prof.coins"), 'owns comet', await ev("prof.owned.loco.includes('comet')"), 'eq', await ev("prof.eq.loco"), 'announce', await ev("document.getElementById('ann').textContent"))
        # ---------- ซื้อจริง: เหรียญจากการเล่นที่ผ่านโควตา (5,000) → ซื้อหวูดเรือใหญ่ 8,000 ไม่พอ / ได้ 5,000 แล้วซื้อไม่ได้ ----------
        await ev("prof.coins+=4000;saveProf();pushProf()"); await pg.wait_for_timeout(800)
        print('legit +4000 accepted ->', await ev("prof.coins"))
        # ---------- ร้านค้าทุกแท็บ ----------
        for t in ['deal', 'wagon', 'smoke', 'skin', 'kfx', 'horn', 'title']:
            await ev(f"openShop('{t}')"); n = await ev("document.querySelectorAll('#shopList .item').length")
            print('tab', t, 'items', n)
            if t in ('deal', 'title'): await pg.screenshot(path=f'/tmp/s_shop_{t}.png')
        # ---------- ฤดูกาลใหม่ ----------
        await ev("prof.season='2026-10';prof.rp=700");c0 = await ev("prof.coins")
        await ev("ensureSeason()"); await pg.wait_for_timeout(500)
        print('season roll ->', await ev("[prof.season,prof.rp,prof.owned.title.filter(t=>t.startsWith('S:'))]"), 'coins +', await ev("prof.coins") - c0, 'title text', await ev("titleText('S:2026-10:1')"))
        await ev("openSheet('rank',renderRanks)"); await pg.wait_for_timeout(500)
        print('rank sheet season line', await ev("document.querySelector('#sheetBody .help').textContent"), '| lb', await ev("document.getElementById('lbList').textContent.slice(0,60)"))
        await pg.click('#sheetClose')
        # ---------- เล่นกับบอท (Guest) ด้วยของใหม่: ทุกหัวจักร/ตู้ + หวูด + เอฟเฟกต์ ----------
        await ev("pushProf();localStorage.removeItem('rsAuth');setProfile('guest',null)")
        await ev("prof.coins=1e6;for(const c of CATS)for(const it of SHOP[c])if(!prof.owned[c].includes(it.id))prof.owned[c].push(it.id);prof.eq.kfx='firework';prof.eq.title='rich';prof.eq.horn='tune'")
        await ev("setDiff('easy');startGame('inf')"); await pg.wait_for_timeout(600)
        await ev("player.safe=999;player.mass=260")
        print('title on train', await ev("player.title"))
        await pg.keyboard.press('h'); await pg.wait_for_timeout(100)
        print('horn ->', await ev("[hornCD>0, texts.some(t=>t.txt.includes('📯'))]"), 'horn btn visible', await ev("!document.getElementById('horn').classList.contains('hidden')"))
        v = await ev("(()=>{const w=worms.find(w=>!w.isP&&!w.isBoss&&w.alive);const h=player.pts[0];for(const q of w.pts){q.x+=h.x+200-w.pts[0].x;q.y+=h.y-w.pts[0].y}w.die(player);return parts.length})()")
        print('kill fx particles', v)
        await pg.wait_for_timeout(250); await pg.screenshot(path='/tmp/s_killfx.png')
        shots = []
        for loco, wag in [('tram', 'cargo'), ('metro', 'coach'), ('comet', 'glass')]:
            await ev(f"player.loco='{loco}';player.wag='{wag}';player.smokeT='normal'"); await pg.wait_for_timeout(500)
            await pg.screenshot(path=f'/tmp/s_{loco}.png'); shots.append(loco)
        await ev("player.smokeT='hearts'"); await pg.wait_for_timeout(500); await pg.screenshot(path='/tmp/s_hearts.png')
        print('screens', shots)
        # ---------- ตารางอันดับฤดูกาล ----------
        print('top', await ev("fetch('/api/top').then(r=>r.json())"))
        print('errors', errs)
        await b.close()
asyncio.run(main())
