// ทดสอบบอทบนเซิร์ฟเวอร์ (botsim.js) แบบไม่ต้องเปิดเบราว์เซอร์:  node tests/test_botsim.js
const botsim = require('../botsim');
let fail = 0; const ok = (c, msg) => { console.log((c ? '✓ ' : '✗ ') + msg); if (!c) fail++; };
function mkRoom(ffa) {
  const room = { ffa, cfg: { R: ffa ? 3000 : 2200 }, players: new Map(), bots: new Map(), foods: new Map(), whites: new Map(), exp: new Map(), phase: 'play', nid: 1, timeLeft: 300 };
  room.msgs = []; return room;
}
const bc = room => (r, o) => room.msgs.push(o);
const drops = []; const drop = (r, d, v, ttl) => drops.push({ n: d.length, v, ttl });
const step = (room, n = 1) => { for (let i = 0; i < n; i++) botsim.step(room, 1 / 20, bc(room), drop); };
const live = room => [...room.bots.values()].filter(b => b.alive && !b.isBoss);

// 1) โลกออนไลน์: คน 1 คน → บอทเติมเกือบ 29
let room = mkRoom(true);
room.players.set(1, { id: 1, kills: 0, st: { x: 0, y: 0, a: 0, m: 40, f: 4 } });
step(room, 3); ok(live(room).length >= 27 && live(room).length <= 29, 'ffa เติมบอท 27–29 ตัว (ได้ ' + live(room).length + ')');
ok(room.msgs.some(m => m.t === 'binfo'), 'ส่ง binfo ให้ผู้เล่น');
ok(live(room).every(b => b.st && b.st[0] < 0 && b.st[5] & 4), 'สถานะบอทมี id ติดลบ + flag มีชีวิต');
// คนเพิ่มอีก 4 → บอทลดทีละตัว
for (let i = 2; i <= 5; i++) room.players.set(i, { id: i, kills: 0, st: { x: i * 300, y: 0, a: 0, m: 40, f: 4 } });
step(room, 60); ok(live(room).length <= 25, 'คนเข้า 4 → บอทลดเหลือ ≤25 (ได้ ' + live(room).length + ')');

// 2) หัวบอทชนลำตัวผู้เล่น → บอทตาย ผู้เล่นได้แต้ม
room = mkRoom(true); room.players.set(7, { id: 7, kills: 0, st: { x: 500, y: 0, a: 0, m: 200, f: 4 } });
step(room, 1); const p7 = room.players.get(7);
// ให้ผู้เล่นวิ่งตรงไป 60 tick เพื่อให้มีลำตัวยาว
for (let i = 0; i < 40; i++) { p7.st.x += 8; step(room, 1); }
const b = live(room)[0]; const q = p7.body.pts[30];
for (const pt of b.pts) { pt.x += q.x - b.pts[0].x; pt.y += q.y - b.pts[0].y; }
b.safe = b.ghost = 0; b.ai.t = 999; room.msgs = []; step(room, 1);
ok(!b.alive && p7.kills === 1, 'บอทชนลำตัวผู้เล่น → บอทตาย ผู้เล่นได้ +1 กำจัด');
ok(room.msgs.some(m => m.t === 'kill' && m.v === b.id && m.k === 7), 'ส่ง kill{v:บอท,k:ผู้เล่น}');
ok(drops.some(d => d.ttl === 30), 'บอทตายทิ้งพลอยที่หายใน 30 วิ');

// (บอทชนบอท → ตายตามปกติ)

// 3) ผู้เล่นผี (flag 32) → บอทชนทะลุ
const b2 = live(room)[0]; p7.st.f = 4 | 32; step(room, 1); const q2 = p7.body.pts[30];
for (const pt of b2.pts) { pt.x += q2.x - b2.pts[0].x; pt.y += q2.y - b2.pts[0].y; } b2.safe = b2.ghost = 0; step(room, 1);
ok(b2.alive, 'ผู้เล่นเพิ่งเกิด (ผี) → บอทชนไม่ตาย'); p7.st.f = 4;

// 4) ระเบิด / แช่แข็ง / ร่างทองชนขาด
const t = live(room)[1]; const h = t.pts[0]; t.safe = t.ghost = 0;
botsim.onFreeze(room, p7, h.x + 100, h.y); ok(t.slow > 0, 'แช่แข็งโดนบอท');
const t2 = live(room).find(x => x !== t && x.pts.length > 40) || live(room)[2]; const m0 = t2.mass;
botsim.onCut(room, p7, t2.id, t2.pts[20].x, t2.pts[20].y); ok(t2.mass < m0 && t2.alive, 'ร่างทองชน → บอทขบวนขาดแต่ไม่ตาย (' + (m0 | 0) + '→' + (t2.mass | 0) + ')');
room.msgs = []; const k0 = p7.kills; botsim.onBomb(room, p7, h.x, h.y);
ok(!t.alive && p7.kills > k0 && room.msgs.some(m => m.t === 'kill' && m.b === 1 && m.k === 7), 'ระเบิด → บอทตาย ได้แต้ม ข้อความมี b:1');

// 5) บอส: ชนลด HP ล้มได้ → kill ให้ผู้ชน
room.sim.bossT = 0; step(room, 1); const boss = [...room.bots.values()].find(x => x.isBoss);
ok(boss && boss.hp === 3 && boss.st.length === 8 && boss.st[7] === 3, 'บอสเกิดมีหัวใจ 3 ดวง และส่งในสถานะ');
botsim.onBossHit(room, p7, boss.id); ok(boss.hp === 2 && boss.alive, 'บอสชนผู้เล่น (bhit) → บอสเหลือ 2 ดวง');
botsim.onBossHit(room, p7, boss.id); ok(boss.hp === 2, 'ส่งซ้ำทันที (ภายใน 1.5 วิ) ไม่ลดซ้ำ');
botsim.onBomb(room, p7, boss.pts[0].x, boss.pts[0].y); ok(boss.hp === 2 && boss.alive, 'ระเบิดไม่ลดหัวใจบอส');
boss.hitCD = 0; botsim.onBossHit(room, p7, boss.id); ok(boss.hp === 1, 'ครั้งที่ 2 → เหลือ 1');
boss.hitCD = 0; room.msgs = []; botsim.onBossHit(room, p7, boss.id);
ok(!boss.alive && room.msgs.some(m => m.t === 'kill' && m.v === boss.id && m.k === 7), 'ครั้งที่ 3 → บอสตาย kill ให้ผู้เล่น');

// 6) บอสชนลำตัวผู้เล่น → เซิร์ฟเวอร์ไม่ตัด (client ตรวจเอง)
room.sim.bossT = 0; step(room, 1); const boss2 = [...room.bots.values()].find(x => x.isBoss && x.alive);
const q3 = p7.body.pts[25]; for (const pt of boss2.pts) { pt.x += q3.x - boss2.pts[0].x; pt.y += q3.y - boss2.pts[0].y; } boss2.safe = boss2.ghost = 0;
room.msgs = []; step(room, 1);
ok(boss2.alive && !room.msgs.some(m => m.t === 'cut' && m.v === 7), 'บอสชนผู้เล่น → เซิร์ฟเวอร์ไม่สั่งตัด (ให้เครื่องผู้เล่นตรวจเองจากภาพจริง)');

// 6b) ชดเชยดีเลย์: หัวบอทเมื่อ ~0.2 วิก่อนอยู่บนลำตัวผู้เล่น (ผู้เล่นเห็นแบบนั้นบนจอ) แม้ตอนนี้วิ่งเลยไปแล้ว → บอทต้องตาย
{ const r2 = mkRoom(true); r2.players.set(9, { id: 9, kills: 0, st: { x: 0, y: 0, a: 0, m: 200, f: 4 } });
  step(r2, 1); const p9 = r2.players.get(9); for (let i = 0; i < 40; i++) { p9.st.x += 8; step(r2, 1); }
  const bb = live(r2).find(b => Math.hypot(b.pts[0].x - p9.st.x, b.pts[0].y) > 600); bb.safe = bb.ghost = 0; bb.ai.t = 999;
  const q = p9.body.pts[30]; bb.hist = []; for (let i = 0; i < 13; i++) bb.hist.push(q.x, q.y);   // เมื่อ 0.2 วิก่อนอยู่บนลำตัว
  for (const pt of bb.pts) { pt.x += q.x + 400 - bb.pts[0].x; pt.y += q.y + 400 - bb.pts[0].y; }  // ตอนนี้อยู่ห่างแล้ว
  r2.msgs = []; botsim.step(r2, 1 / 20, bc(r2), drop);
  ok(!bb.alive && p9.kills === 1, 'ชดเชยดีเลย์: บอทที่ผู้เล่นเห็นวิ่งทะลุลำตัว → ตาย ผู้เล่นได้แต้ม'); }


// 6c) ลอดอุโมงค์แบบค่อย ๆ โผล่: หัวไปทางออกก่อน ท้ายยังอยู่ทางเข้า แล้วค่อย ๆ ตามออกมาจนครบ
{ const r3 = mkRoom(true); r3.players.set(1, { id: 1, kills: 0, st: { x: 2500, y: 0, a: 0, m: 40, f: 4 } }); step(r3, 1);
  const W = r3.sim.world, P0 = W.portals[0], Q0 = W.portals[P0.pair];
  const tb = live(r3).sort((a, b) => b.pts.length - a.pts.length)[0]; tb.mass = 300; tb.ai.t = 1e9; tb.boost = false; tb.slow = 0;
  const ang = 0.3; tb.angle = tb.target = ang; tb.pts = []; for (let i = 0; i < 150; i++) tb.pts.push({ x: P0.x - Math.cos(ang) * (30 + i * 8), y: P0.y - Math.sin(ang) * (30 + i * 8) });
  tb.tunCD = 0; tb.safe = 99; let moved = false, maxGap = 0, frames = 0;
  for (let i = 0; i < 300 && (tb.tun || !moved); i++) { botsim.step(r3, 1 / 20, bc(r3), drop); tb.target = tb.angle; tb.safe = 99; frames++;
    if (tb.tun) { moved = true; const k = tb.tun.k; if (i === 0 || frames === 2) ok(Math.hypot(tb.pts[0].x - Q0.x, tb.pts[0].y - Q0.y) < 200 && Math.hypot(tb.pts[tb.pts.length - 1].x - P0.x, tb.pts[tb.pts.length - 1].y - P0.y) < 1400, 'ลอดอุโมงค์: หัวโผล่ทางออก ท้ายยังอยู่ฝั่งทางเข้า');
      for (let j = 1; j < tb.pts.length; j++) if (j !== k) maxGap = Math.max(maxGap, Math.hypot(tb.pts[j].x - tb.pts[j - 1].x, tb.pts[j].y - tb.pts[j - 1].y)); } }
  ok(moved && !tb.tun, 'ลอดอุโมงค์: ตู้ทั้งขบวนตามออกมาครบ (' + frames + ' tick)');
  ok(maxGap < 30, 'ระหว่างลอด ตู้ติดกันไม่ขาดยืด (ห่างสุด ' + maxGap.toFixed(1) + ')');
  ok(Math.hypot(tb.pts[tb.pts.length - 1].x - P0.x, tb.pts[tb.pts.length - 1].y - P0.y) > 400, 'ลอดเสร็จ ท้ายขบวนไม่ค้างฝั่งทางเข้า'); }

// 7) 2v2: คน 2 คนทีม A → บอท 2 ตัวทีม B, ทีม A ไม่มีบอท
room = mkRoom(false); room.arena = () => 2200;
room.players.set(1, { id: 1, team: 'A', kills: 0, st: { x: -900, y: 0, a: 0, m: 30, f: 4 } });
room.players.set(2, { id: 2, team: 'A', kills: 0, st: { x: -900, y: 300, a: 0, m: 30, f: 4 } });
step(room, 2); const vb = live(room);
ok(vb.length === 2 && vb.every(x => x.team === 'B' && x.info.team === 'B'), '2v2 เติมบอททีม B 2 ตัว');
botsim.onBomb(room, room.players.get(1), vb[0].pts[0].x, vb[0].pts[0].y);
ok(!vb[0].alive && vb[0].dead && room.bots.has(vb[0].id), '2v2 บอทตาย → เก็บไว้นับแต้มตอนจบ');
step(room, 70); ok(live(room).length === 2, '2v2 บอทเกิดใหม่ภายใน ~3 วิ');
room.phase = 'lobby'; const n0 = room.msgs.length; step(room, 5); ok(room.msgs.length === n0, 'ล็อบบี้ 2v2 บอทไม่ขยับ');

// 8) ความเร็ว: 30 ขบวน ต่อ tick ต้องเร็วพอ
room = mkRoom(true); room.players.set(1, { id: 1, kills: 0, st: { x: 0, y: 0, a: 0, m: 40, f: 4 } });
for (let i = 0; i < 1400; i++) { const a = Math.random() * 6.28, r = Math.sqrt(Math.random()) * 2900; room.foods.set(room.nid, [room.nid++, Math.cos(a) * r, Math.sin(a) * r, 1, 0]); }
step(room, 20); const t0 = process.hrtime.bigint(); step(room, 200); const ms = Number(process.hrtime.bigint() - t0) / 1e6 / 200;
ok(ms < 8, 'เวลาคำนวณต่อ tick ' + ms.toFixed(2) + ' ms (< 8 ms)');

console.log(fail ? `\n${fail} ข้อไม่ผ่าน` : '\nผ่านทั้งหมด'); process.exit(fail ? 1 : 0);
