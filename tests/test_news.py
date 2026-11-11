# 📰 มีอะไรใหม่: ผู้เล่นเก่ากลับมา → เห็นวันละครั้ง · ผู้เล่นใหม่ไม่เห็น · เห็นแล้วไม่ขึ้นซ้ำ
import asyncio,pathlib
from playwright.async_api import async_playwright
GAME=pathlib.Path(__file__).resolve().parent.parent.joinpath('public','index.html').as_uri()
async def run(b,pre):
  ctx=await b.new_context(viewport={'width':390,'height':844})
  await ctx.add_init_script("if(!sessionStorage.getItem('_i')){sessionStorage.setItem('_i','1');localStorage.clear();"+pre+"}")
  pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.goto(GAME);await pg.wait_for_timeout(2500)
  r1=await pg.evaluate("({open:!$('sheet').classList.contains('hidden'),title:$('sheetTitle').textContent,n:document.querySelectorAll('#sheetBody .news').length,seen:localStorage.getItem('trainNewsSeen')})")
  if r1['open'] and 'ใหม่' in r1['title']:await pg.click('#nwOk')
  await pg.reload();await pg.wait_for_timeout(2500)
  r2=await pg.evaluate("({open:!$('sheet').classList.contains('hidden'),title:$('sheetTitle').textContent})")
  await ctx.close();return r1,r2,errs
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    new=await run(b,"")
    old=await run(b,"localStorage.setItem('wormName','ทดสอบ')")
    cur=await run(b,"localStorage.setItem('wormName','x');localStorage.setItem('trainNewsSeen','6')")
    day=await run(b,"localStorage.setItem('wormName','x');localStorage.setItem('trainNewsSeen','3');localStorage.setItem('trainNewsDay',new Date(Date.now()+7*36e5).toISOString().slice(0,10))")
    # ปุ่มใน ❓ วิธีเล่น
    ctx=await b.new_context(viewport={'width':390,'height':844});pg=await ctx.new_page();await pg.goto(GAME);await pg.wait_for_timeout(1500)
    await pg.evaluate("$('sheet').classList.add('hidden');helpTab='rules';$('bHelp').click()");await pg.click('#hNews');await pg.wait_for_timeout(300)
    allN=await pg.evaluate("document.querySelectorAll('#sheetBody .news').length");await pg.screenshot(path='/tmp/news_all.png');await ctx.close()
    for k,v in [('new',new),('old',old),('cur',cur),('day',day)]:print(k,v)
    print('help news',allN)
    ok=(not new[0]['open'] and new[0]['seen']=='6' and old[0]['open'] and old[0]['n']==3 and not old[1]['open'] and not cur[0]['open'] and not day[0]['open'] and allN>=6
        and not any(x[2] for x in [new,old,cur,day]))
    print('PASS' if ok else 'FAIL');await b.close()
asyncio.run(main())
