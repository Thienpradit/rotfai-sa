# คนชนคน: ตายเฉพาะปลายหัว (8 พ.ย. 2026) + ไม่ตายเพราะผู้เล่นที่ยังไม่โผล่บนจอเรา
# รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start
import asyncio
from playwright.async_api import async_playwright
JS="""(async()=>{const fr=()=>new Promise(r=>requestAnimationFrame(r));const out={};
  const om=netMsg;window.netMsg=m=>{if(m.t==='s'||m.t==='binfo'||m.t==='kill')return;om(m)};
  const sent=[];const ns=netSend;window.netSend=o=>{sent.push(o);ns(o)};
  let died=null;player.die=function(k){died=k||'x'};
  async function run(name,bx,by,ba,o={}){
    worms=[player];died=null;sent.length=0;player.safe=0;player.ghost=0;player.mass=60;player.angle=0;player.target=0;input.angle=0;input.boost=false;player.tun=null;
    const sp=player.r()*.42;for(let i=0;i<player.pts.length;i++){player.pts[i].x=-i*sp;player.pts[i].y=0}
    const w=new Worm('B',SKINS[2],bx,by,false,{a:ba});w.isRemote=true;w.netId=5000+Object.keys(out).length;w.mass=60;w.safe=0;w.ghost=0;
    w.seenAt=o.fresh?performance.now():0;w.snaps=[{t:Date.now()+9e5,x:bx,y:by,a:ba,m:60}];worms.push(w);
    for(let i=0;i<3;i++){await fr();if(died)break}
    out[name]={aDied:!!died,hitme:sent.some(s=>s.t==='hitme')};return w}
  await run('tipIntoSide',26,0,Math.PI/2);          // ปลายหัวเรา (A) ชนข้างหัว B → A ตายคนเดียว
  await run('sideRammed',0,24,-Math.PI/2);          // ปลายหัว B ชนข้างหัวเรา → B ตายคนเดียว (เดิมตายทั้งคู่)
  await run('headOn',30,0,Math.PI);                 // หัวชนหัวตรง ๆ → ตายทั้งคู่
  await run('fresh',30,0,Math.PI,{fresh:1});        // เพิ่งโผล่บนจอ → ยังไม่ชน
  // crash จากเซิร์ฟเวอร์
  const cr=async(w)=>{died=null;player.safe=0;player.ghost=0;om({t:'crash',k:w?w.netId:777777});return !!died};
  worms=[player];out.crashUnknown=await cr(null);
  const far=new Worm('F',SKINS[1],2500,0,false);far.isRemote=true;far.netId=8001;far.seenAt=0;worms.push(far);out.crashFar=await cr(far);
  const nf=new Worm('N',SKINS[1],40,0,false,{a:Math.PI});nf.isRemote=true;nf.netId=8002;nf.seenAt=performance.now();worms.push(nf);out.crashFresh=await cr(nf);
  nf.seenAt=0;out.crashNear=await cr(nf);
  window.netMsg=om;window.netSend=ns;return out})()"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--disable-renderer-backgrounding']);pg=await (await b.new_context(viewport={'width':700,'height':500})).new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://127.0.0.1:3456/');await pg.wait_for_timeout(600)
        await pg.evaluate("document.getElementById('sheet').classList.add('hidden');playEndless()");await pg.wait_for_timeout(2500)
        r=await pg.evaluate(JS);print(r)
        exp={'tipIntoSide':{'aDied':True,'hitme':False},'sideRammed':{'aDied':False,'hitme':True},'headOn':{'aDied':True,'hitme':True},
             'fresh':{'aDied':False,'hitme':False},'crashUnknown':False,'crashFar':False,'crashFresh':False,'crashNear':True}
        bad={k:(r.get(k),v) for k,v in exp.items() if r.get(k)!=v}
        print('errors',errs[:3]);print('bad',bad);print('PASS' if not bad and not errs else 'FAIL');await b.close()
asyncio.run(main())
