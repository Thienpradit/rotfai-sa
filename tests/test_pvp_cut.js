// คนชนคนออนไลน์ (ฝั่งเซิร์ฟเวอร์): A แจ้ง hitme{id:B} → เซิร์ฟเวอร์ส่ง crash ให้ B เฉพาะเมื่อสมเหตุสมผล
// รันเซิร์ฟเวอร์ก่อน: PORT=3456 npm start  แล้ว node tests/test_pvp_cut.js
const WebSocket = require('ws');
let fail = 0; const ok = (c, m) => { console.log((c ? '✓ ' : '✗ ') + m); if (!c) fail++; };
const wait = ms => new Promise(r => setTimeout(r, ms));
function client(name, room) { return new Promise(res => { const ws = new WebSocket('ws://127.0.0.1:3456/ws'), c = { ws, msgs: [] };
  ws.on('open', () => ws.send(JSON.stringify({ t: 'join', mode: 'ffa', room, name, skin: 0 })));
  ws.on('message', d => { const m = JSON.parse(d); c.msgs.push(m); if (m.t === 'welcome') { c.id = m.id; res(c); } }); }); }
const st = (c, x, y, f = 4) => c.ws.send(JSON.stringify({ t: 'st', x, y, a: 0, m: 120, f, ts: Date.now() }));
(async () => {
  const room = 'PVP' + Math.random().toString(36).slice(2, 5).toUpperCase();
  const A = await client('A', room), B = await client('B', room);
  // A วิ่งตามแกน x สร้างลำตัวบนเซิร์ฟเวอร์ · B อยู่ห่างจากลำตัว A 150px
  for (let i = 0; i < 40; i++) { st(A, i * 8, 0); st(B, 150, 150); await wait(50); }
  const crashes = () => B.msgs.filter(m => m.t === 'crash').length;
  A.ws.send(JSON.stringify({ t: 'hitme', id: B.id })); await wait(300);
  ok(crashes() === 1 && B.msgs.find(m => m.t === 'crash').k === A.id, 'A เห็นหัว B แตะลำตัว → B ได้ crash{k:A}');
  A.ws.send(JSON.stringify({ t: 'hitme', id: B.id })); await wait(300);
  ok(crashes() === 1, 'ส่งซ้ำภายใน 1.5 วิ → ไม่ crash ซ้ำ');
  await wait(1400);
  for (let i = 0; i < 5; i++) { st(B, 150, 2000); await wait(50); }
  A.ws.send(JSON.stringify({ t: 'hitme', id: B.id })); await wait(300);
  ok(crashes() === 1, 'B อยู่ไกลจากลำตัว A (> 400px) → ไม่เชื่อ ไม่ crash');
  for (let i = 0; i < 5; i++) { st(B, 150, 150, 4 | 32); await wait(50); }
  A.ws.send(JSON.stringify({ t: 'hitme', id: B.id })); await wait(300);
  ok(crashes() === 1, 'B เป็นผี (เพิ่งเกิด) → ไม่ crash');
  for (let i = 0; i < 5; i++) { st(B, 150, 150, 4 | 16); await wait(50); }
  A.ws.send(JSON.stringify({ t: 'hitme', id: B.id })); await wait(300);
  ok(crashes() === 1, 'B มีเกราะ (อมตะ) → ไม่ crash');
  for (let i = 0; i < 5; i++) { st(B, 150, 150); await wait(50); }
  A.ws.send(JSON.stringify({ t: 'hitme', id: B.id })); await wait(300);
  ok(crashes() === 2, 'กลับมาปกติ → crash ได้อีก');
  A.ws.close(); B.ws.close();
  console.log(fail ? `\n${fail} ข้อไม่ผ่าน` : '\nผ่านทั้งหมด'); process.exit(fail ? 1 : 0);
})();
