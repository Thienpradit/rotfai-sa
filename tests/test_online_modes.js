// 🌍 โลกออนไลน์ 3 โหมด (14 พ.ย.): บอทแต่ละโหมด + หินโหมด Hard (botsim)   node tests/test_online_modes.js
const botsim = require('../botsim');
let fail = 0; const ok = (c, msg) => { console.log((c ? '✓ ' : '✗ ') + msg); if (!c) fail++; };
const R = 4370;
function mkRoom(diff, code = 'H1AB') {
  const room = { ffa: true, diff, code, cfg: { R }, players: new Map(), bots: new Map(), foods: new Map(), whites: new Map(), exp: new Map(), phase: 'play', nid: 1, timeLeft: 300, msgs: [] };
  if (diff === 'hard') room.rocks = botsim.buildRocks(R, code); return room;
}
let deaths = 0; const drop = () => {};
const step = (room, n = 1) => { for (let i = 0; i < n; i++) botsim.step(room, 1 / 20, (r, o) => { if (o.t === 'kill') deaths++; room.msgs.push(o); }, drop); };
const live = room => [...room.bots.values()].filter(b => b.alive && !b.isBoss);

// 1) หิน: ตำแหน่งตายตัวตามรหัสโลก · ~40 ก้อน · ไม่ทับสถานี/อุโมงค์/กลางสนาม/ขอบ · ไม่ชิดกัน
const A = botsim.buildRocks(R, 'H1AB'), B = botsim.buildRocks(R, 'H1AB'), C = botsim.buildRocks(R, 'H9ZZ');
ok(A.length >= 35 && A.length <= 40, 'หิน ' + A.length + ' ก้อน');
ok(JSON.stringify(A) === JSON.stringify(B) && JSON.stringify(A) !== JSON.stringify(C), 'รหัสโลกเดียวกัน = หินที่เดิม · คนละโลก = ต่างกัน');
const W = botsim.buildWorld(R), st = [0, 1, 2, 3].map(k => [Math.cos(k * Math.PI / 2 + .35) * R * .6, Math.sin(k * Math.PI / 2 + .35) * R * .6]);
ok(A.every(([x, y, r]) => Math.hypot(x, y) > 480 && Math.hypot(x, y) + r < R - 200), 'ไม่อยู่กลางสนาม/ชิดขอบ');
ok(A.every(([x, y, r]) => st.every(([sx, sy]) => Math.hypot(x - sx, y - sy) > 300 + r) && W.portals.every(p => Math.hypot(x - p.x, y - p.y) > 230 + r)), 'ไม่ทับสถานี/อุโมงค์');
ok(A.every((a, i) => A.every((b, j) => i === j || Math.hypot(a[0] - b[0], a[1] - b[1]) > a[2] + b[2] + 200)), 'หินไม่ชิดกัน (ขบวนผ่านระหว่างหินได้)');

// 2) Hard: บอทหลบหินเป็น · ชนหิน = ตาย · ไม่เกิดทับหิน
let room = mkRoom('hard'); room.players.set(1, { id: 1, kills: 0, st: { x: 0, y: 0, a: 0, m: 60, f: 4 } });
step(room, 3);
ok(live(room).every(b => !botsim.rockHit(room, b.pts[0].x, b.pts[0].y, 100)), 'บอทเกิดไม่ทับ/ชิดหิน');
const rk = room.rocks[0], bb = live(room)[0];
for (const p of bb.pts) { p.x += rk[0] - bb.pts[0].x; p.y += rk[1] - bb.pts[0].y; } bb.ghost = bb.safe = 0; bb.tun = null; step(room, 1);
ok(!bb.alive, 'บอทเอาหัวชนหิน → ตาย');
// วิ่ง 90 วิ: นับบอทตายเพราะหิน (หลบเป็น = น้อย)
let rockDeaths = 0; const orig = botsim.rockHit;
for (let t = 0; t < 1800; t++) { const before = new Map(live(room).map(b => [b.id, b])); step(room, 1);
  for (const [id, b] of before) if (!b.alive && botsim.rockHit(room, b.pts[0].x, b.pts[0].y, (10 + Math.sqrt(b.mass) * .75) * .5)) rockDeaths++; }
ok(rockDeaths <= 12, 'บอท 39 ตัว 90 วิ ตายเพราะชนหิน ' + rockDeaths + ' ครั้ง (หลบเป็น)');

// 3) Hard: AI แบบ 2v2 แต่รุมคนจริงคนเดียวได้ไม่เกิน HARD_CAP ตัว
room = mkRoom('hard', 'H2CD'); const P = { id: 2, kills: 0, st: { x: 0, y: 0, a: 0, m: 120, f: 4 } }; room.players.set(2, P);
let maxH = 0, sumH = 0, n = 0;
for (let t = 0; t < 1200; t++) { P.st.x = Math.cos(t / 120) * 900; P.st.y = Math.sin(t / 120) * 900; P.st.a = t / 120 + Math.PI / 2; step(room, 1);
  if (t > 100) { const h = live(room).filter(b => b.ai && b.ai.hunt && b.ai.hunt.human).length; maxH = Math.max(maxH, h); sumH += h; n++; } }
ok(maxH <= botsim.HARD_CAP, 'บอทไล่คนจริงพร้อมกันสูงสุด ' + maxH + ' ตัว (≤ ' + botsim.HARD_CAP + ')');
ok(sumH / n >= 1.5, 'Hard มีบอทไล่ตลอด เฉลี่ย ' + (sumH / n).toFixed(1) + ' ตัว');

// 4) Easy: บอทไล่น้อยกว่า Normal ชัดเจน
const huntAvg = diff => { const r = mkRoom(diff, diff[0].toUpperCase() + 'X1'), p = { id: 3, kills: 0, st: { x: 0, y: 0, a: 0, m: 120, f: 4 } }; r.players.set(3, p); let s = 0, k = 0;
  for (let t = 0; t < 1200; t++) { p.st.x = Math.cos(t / 120) * 900; p.st.y = Math.sin(t / 120) * 900; step(r, 1); if (t > 100) { s += live(r).filter(b => b.ai && b.ai.hunt && b.ai.hunt.human).length; k++; } } return s / k; };
const he = huntAvg('easy'), hn = huntAvg('normal'), hh = huntAvg('hard');
ok(he < hn && hn < hh, `บอทไล่คนจริงเฉลี่ย Easy ${he.toFixed(2)} < Normal ${hn.toFixed(2)} < Hard ${hh.toFixed(2)}`);
ok(!mkRoom('normal').rocks && !mkRoom('easy').rocks, 'Easy/Normal ไม่มีหิน');

// 5) ความเร็ว: Hard 40 ขบวน + หิน
room = mkRoom('hard', 'H3EF'); room.players.set(4, { id: 4, kills: 0, st: { x: 0, y: 0, a: 0, m: 60, f: 4 } }); step(room, 20);
const t0 = process.hrtime.bigint(); step(room, 200); const ms = Number(process.hrtime.bigint() - t0) / 1e6 / 200;
ok(ms < 6, 'Hard ใช้ ' + ms.toFixed(2) + ' ms ต่อ tick (20 ครั้ง/วิ)');

console.log(fail ? `FAIL ${fail}` : 'PASS'); process.exit(fail ? 1 : 0);
