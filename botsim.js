// รถไฟซ่า — บอทรันบนเซิร์ฟเวอร์ (โลกออนไลน์ free-for-all + 2v2 เติมบอท)
// เดิมบอทรันในมือถือ "หัวหน้าห้อง" → เครื่องช้า/สลับแอป บอทกระตุกทั้งโลก · ตอนนี้เซิร์ฟเวอร์คำนวณเองทุกตัว ทุกคนเห็นลื่นเท่ากัน
// กติกาการเคลื่อนที่/AI/ชน/กิน ลอกมาจาก public/index.html (class Worm, aiThink, step) — ถ้าแก้กติกาที่นั่น ให้แก้ที่นี่ด้วย
const TAU = Math.PI * 2, CS = 100, SELF_IDX = 20, GROW = .7, BOMB_R_FFA = 500, BOMB_R_VS = 300, FREEZE_R = 650, FREEZE_T = 6, PORTAL_EDGE = 260;
const LAG_STEPS = 12;
const BOSS_HEARTS = 3, BOSS_HIT_CD = 1.5;   // บอส 👑 มีหัวใจ 3 ดวง เสียเฉพาะตอนบอสเอาหัวชนตัวผู้เล่น (เครื่องผู้เล่นส่ง bhit มา) · บอทธรรมดาชนครั้งเดียวตายเหมือนเดิม
const SPAWN_GHOST = 2.5, TUNNEL_SAFE = 2, FFA_MAX = 40, TEAM_MAX = 2, DROP_TTL = 30;
const RAGE_SPD = [1, 1.4, 2], RAGE_TURN = .15, BOSS_CAP = 2.7 * 2;   // บอสเสียหัวใจ → เร็วขึ้น ×1.4 / ชีวิตสุดท้าย ×2 (= ผู้เล่นเร่งเพชร) และไม่เร็วกว่านั้น (ต้องตรงกับ index.html)
const bossRage = w => w.isBoss ? Math.max(0, (w.maxHp || BOSS_HEARTS) - w.hp) : 0;
// หวูดไล่ศัตรู: ต้องตรงกับ HORN_PERK ใน index.html
const HORN_PERK = { classic: { r: 0, t: 0 }, deep: { r: 150, t: 1.3 }, chime: { r: 200, t: 1.6 }, tune: { r: 260, t: 1.9 }, siren: { r: 330, t: 2.3 }, thunder: { r: 410, t: 2.7 }, dragon: { r: 500, t: 3.2 } };
const D = { huntP: .8, huntR: 700, others: .3, look: 1, think: [10, 25], big: .25, boss: 120, bossM: 900, bossHp: BOSS_HEARTS };   // ระดับ Normal
// pick +30% (13 พ.ย. 19:14) — ต้องตรงกับ index.html
const LOCO_PERK = { classic: { pick: 0, en: 20 }, diesel: { pick: 20, en: 24 }, bullet: { pick: 39, en: 28 }, tram: { pick: 59, en: 32 }, metro: { pick: 78, en: 40 }, comet: { pick: 104, en: 50 } };
const SKINS = [['#ffd23f', '#ff8c42'], ['#77ccff', '#3a7bff'], ['#ff6b9a', '#ffe0ec'], ['#7cfc9a', '#1fa35c'], ['#c08cff', '#5b2bd6'], ['#ff5e5e', '#ffffff'], ['#ffffff', '#30344a'], ['#ffb3e6', '#9ad9ff', '#fff59a'], ['#ff8c42', '#30344a'], ['#5ef2e0', '#ff6b9a']];
const NAMES = ['ไส้เดือนสายซิ่ง', 'น้องหนอนน้อย', 'Wiggle', 'Noodle', 'ต้มยำกุ้ง', 'SlimJim', 'หนอนชาเขียว', 'กัปตันหนอน', 'มะม่วงสุก', 'Zigzag', 'ข้าวเหนียว', 'Spaghetti', 'หนอนหิว', 'Bubbles', 'Doodle', 'ลูกชิ้นปิ้ง', 'Mochi', 'Sneaky', 'Turbo', 'ปลาทูทอด', 'Pixel', 'Squiggle', 'Banana', 'ส้มตำ', 'Ninja', 'Gummy', 'ขนมครก', 'Shadow', 'หนอนบุ้ง', 'Lucky', 'ชาไทย', 'Bobo'];
// 2v2 (เจ้าของสั่ง 12 พ.ย. 01:53 "บอทใน 2v2 ให้เป็นสีอื่น"): บอทประจำทีมใช้สีทีม (แดง/น้ำเงิน) · นักล่ากลางสีเหลือง (เดิมส้มดำ)
const TEAM_SKIN = { A: ['#ff5e5e', '#ffd0d0', '#b02a2a'], B: ['#4da3ff', '#d6ebff', '#1f5fb8'] }, HUNTER_SKIN = ['#ffd60a', '#fff3a6', '#d9a600'];   // นักล่ากลาง 2v2 = สีเหลือง ต่างจากทีมแดง/น้ำเงิน (เจ้าของสั่ง 12 พ.ย. 20:25)
const BOSS_SKIN = ['#3a0d0d', '#ff3b3b', '#1a1a1a'], LOCOS = ['classic', 'classic', 'diesel', 'bullet'];
const rnd = (a, b) => a + Math.random() * (b - a), pick = a => a[(Math.random() * a.length) | 0];
const key = (cx, cy) => (cx + 500) * 1000 + (cy + 500);
const rOf = m => Math.min(10 + Math.sqrt(m) * .75, 44), nOf = m => Math.min(Math.floor(14 + m * .45), 700);
let nextBot = 1;

// ---------- โลก: อุโมงค์ (ตำแหน่งตายตัวตามรัศมี เหมือน buildWorld ในเกม) · รางรถไฟเอาออกแล้ว 11 พ.ย. ----------
function buildWorld(R) {
  const portals = [];
  for (let k = 0; k < 3; k++) { const a = k * TAU / 3 + 1.05; portals.push({ x: Math.cos(a) * R * .33, y: Math.sin(a) * R * .33, pair: k * 2 + 1 }); portals.push({ x: Math.cos(a + Math.PI * .85) * R * .82, y: Math.sin(a + Math.PI * .85) * R * .82, pair: k * 2 }); }
  return { portals };
}
// ---------- ขบวน (บอท / ร่างจำลองของผู้เล่นจริงที่ใช้ตรวจชน) ----------
function follow(t) {
  const n = nOf(t.mass), p = t.pts;
  while (p.length < n) { const q = p[p.length - 1]; p.push({ x: q.x, y: q.y }); }
  if (p.length > n) p.length = n;
  const s = rOf(t.mass) * .42, T = t.tun;
  for (let i = 1; i < p.length; i++) { let ax = p[i - 1].x, ay = p[i - 1].y; if (T && i === T.k) { ax -= T.dx; ay -= T.dy; }
    const b = p[i], dx = ax - b.x, dy = ay - b.y, dd = Math.hypot(dx, dy); if (dd > s) { const k = (dd - s) / dd; b.x += dx * k; b.y += dy * k; } }
  // ตู้ลอดตามระยะที่หัววิ่งออกมาแล้ว (เหมือน index.html tunFeed) — ไม่ค้าง ไม่โผล่ทีเดียวทั้งขบวน · หยุดนิ่งเกิน 6 วิค่อยย้ายที่เหลือ
  if (T) { const h = p[0]; if (T.hx !== undefined) T.d += Math.hypot(h.x - T.hx, h.y - T.hy); T.hx = h.x; T.hy = h.y;
    while (T.k < p.length) { const b = p[T.k]; if (T.t > 6 || T.d >= T.k * s - 1 || (b.x - T.ex) ** 2 + (b.y - T.ey) ** 2 < MOUTH * MOUTH) { b.x += T.dx; b.y += T.dy; T.k++; T.t = 0; } else break; } if (T.k >= p.length) t.tun = null; }
}
// ลอดอุโมงค์แบบค่อย ๆ โผล่ (เหมือน index.html: tunStart/tunFeed) — หัววาร์ปก่อน ตู้ที่เหลือวิ่งตามเข้าปากอุโมงค์ทีละจุด
const MOUTH = 44;
function tunStart(world, t, p) { if (t.tun) { const T = t.tun; for (let i = T.k; i < t.pts.length; i++) { t.pts[i].x += T.dx; t.pts[i].y += T.dy; } }
  const q = world.portals[p.pair], dx = q.x - p.x, dy = q.y - p.y; t.pts[0].x += dx; t.pts[0].y += dy; t.tun = { dx, dy, ex: p.x, ey: p.y, k: 1, t: 0, d: 0, hx: t.pts[0].x, hy: t.pts[0].y }; }
function inMouth(room, q) { for (const p of room.sim.world.portals) if ((q.x - p.x) ** 2 + (q.y - p.y) ** 2 < MOUTH * MOUTH && portalOpen(room, p)) return true; return false; }
function mkPts(x, y, a, mass) { const n = nOf(mass), s = rOf(mass) * .42, pts = []; for (let i = 0; i < n; i++) pts.push({ x: x - Math.cos(a) * i * s, y: y - Math.sin(a) * i * s }); return pts; }

function arenaR(room) { return room.arena ? room.arena(room) : room.cfg.R; }
function randIn(room, m) { const a = Math.random() * TAU, r = Math.sqrt(Math.random()) * Math.max(50, arenaR(room) - m); return [Math.cos(a) * r, Math.sin(a) * r]; }
// ที่เกิดใหม่: ไกลจากทุกขบวนให้มากที่สุด (2v2 เกิดฝั่งทีมตัวเอง)
function farSpot(room, trains, margin, minD, side) {
  let best = null, bd = -Infinity; const AR = arenaR(room);   // -Infinity: คืนจุดที่ดีที่สุดเสมอ (เดิม -1 → วงหดแน่นแล้วคืน null → เซิร์ฟเวอร์ล่ม 12 พ.ย. 13:10)
  for (let i = 0; i < 36; i++) { let x, y;
    if (side !== undefined && i < 24) { const a = side + rnd(-.8, .8), rr = Math.sqrt(Math.random()) * Math.max(100, AR - margin); x = Math.cos(a) * rr; y = Math.sin(a) * rr; } else [x, y] = randIn(room, margin);
    let d = 1e9; for (const t of trains) { if (!t.alive) continue; const p = t.pts; for (let k = 0; k < p.length; k += 8) { const dd = Math.hypot(p[k].x - x, p[k].y - y) - (k ? 0 : 350); if (dd < d) d = dd; } }
    if (d >= minD) return [x, y]; if (d > bd) { bd = d; best = [x, y]; } }
  return best || randIn(room, margin);
}

function freeName(room) {   // ชื่อไม่ซ้ำกับบอทที่ยังอยู่ (ถ้าชื่อหมดค่อยยอมซ้ำ)
  const used = new Set([...room.bots.values()].filter(b => b.alive).map(b => b.name.replace('🤖 ', '')));
  const free = NAMES.filter(n => !used.has(n)); return pick(free.length ? free : NAMES);
}
function spawnBot(room, o = {}) {
  const S = room.sim, trains = allTrains(room);
  const side = o.team ? (o.team === 'A' ? Math.PI : 0) : undefined;
  const [x, y] = farSpot(room, trains, o.boss ? 500 : 400, o.boss ? 1100 : 650, side);
  const a = side !== undefined ? side + Math.PI + rnd(-.5, .5) : Math.random() * TAU;
  let mass = o.boss ? D.bossM : rnd(25, 120); if (!o.boss && !o.team && !o.hunter && Math.random() < D.big) mass = rnd(150, 450); if (o.team) mass = rnd(40, 80); if (o.hunter) mass = rnd(80, 140);
  const id = -(100000000 + (nextBot++ % 90000000));
  const b = { id, bot: true, name: o.boss ? '👑 บอสยักษ์' : (o.hunter ? '🎯 ' : o.team ? '🤖 ' : '') + freeName(room), skin: o.boss ? BOSS_SKIN : o.hunter ? HUNTER_SKIN : o.team ? TEAM_SKIN[o.team] : pick(SKINS), loco: o.boss ? 'diesel' : pick(LOCOS), team: o.team,
    mass, maxLen: mass, pts: mkPts(x, y, a, mass), angle: a, target: a, boost: false, energy: o.boss ? 10 : 5, alive: true, safe: SPAWN_GHOST, ghost: SPAWN_GHOST, slow: 0, selfCD: 0, tunCD: 0,
    kills: 0, isBoss: !!o.boss, hp: o.boss ? D.bossHp : 0, maxHp: o.boss ? D.bossHp : 0, ai: { t: 0, tx: x, ty: y, boostT: 0, hunt: null } };
  b.info = { id, name: b.name, skin: b.skin, loco: b.loco, boss: b.isBoss, mhp: b.maxHp }; if (b.team) b.info.team = b.team; if (o.hunter) { b.hunter = true; b.info.hunter = 1; }
  room.bots.set(id, b); if (b.isBoss) S.boss = b;
  S.bcast(room, { t: 'binfo', b: [b.info] });
  return b;
}

// ผู้เล่นจริง: เซิร์ฟเวอร์รู้แค่ตำแหน่งหัว → สร้างลำตัวตามหัวแบบเดียวกับที่เกมวาดรถไฟคนอื่น (ใช้ตรวจว่าบอทชนลำตัวผู้เล่น)
function syncPlayers(room) {
  for (const p of room.players.values()) {
    const st = p.st; if (!st || !(st.f & 4)) { p.body = null; continue; }
    if (!p.body) p.body = { pid: p.id, human: true, alive: true, pts: mkPts(st.x, st.y, st.a, Math.max(10, st.m)), mass: Math.max(10, st.m) };
    const b = p.body, h = b.pts[0], dx = st.x - h.x, dy = st.y - h.y;
    if (dx * dx + dy * dy > 300 * 300) { let ent = null; const W = room.sim && room.sim.world;
      if (W) for (const pp of W.portals) { const qq = W.portals[pp.pair]; if (Math.hypot(h.x - pp.x, h.y - pp.y) < 170 && Math.hypot(st.x - qq.x, st.y - qq.y) < 260) { ent = pp; break; } }
      if (ent) { tunStart(W, b, ent); h.x = st.x; h.y = st.y; } else { b.tun = null; for (const q of b.pts) { q.x += dx; q.y += dy; } } }
    else { h.x = st.x; h.y = st.y; }
    if (b.tun) b.tun.t += 1 / 20;
    { let da = st.a - (b.angle ?? st.a); da = Math.atan2(Math.sin(da), Math.cos(da)); b.av = (b.av || 0) * .75 + da * 20 * .25; }   // ความเร็วเลี้ยว (เรเดียน/วิ) ไว้ให้บอท 2v2 เดาทางโค้ง
    b.mass = Math.max(10, st.m); b.angle = st.a; b.boost = !!(st.f & 1); b.team = p.team; b.ghost = st.f & 32 ? 1 : 0; b.safe = st.f & 16 ? 1 : 0; b.alive = true; follow(b);
  }
}
const allTrains = room => { const t = []; for (const p of room.players.values()) if (p.body) t.push(p.body); for (const b of room.bots.values()) if (b.alive) t.push(b); return t; };
const ally = (a, b) => !!(a.team && a.team === b.team);

function buildGrid(trains) { const g = new Map(); for (const w of trains) { const p = w.pts; for (let i = 0; i < p.length; i += 2) { const k = key(Math.floor(p[i].x / CS), Math.floor(p[i].y / CS)); let a = g.get(k); if (!a) g.set(k, a = []); a.push(w, i); } } return g; }
function bodyNear(S, room, x, y, rad, self) {
  const AR = arenaR(room); if (x * x + y * y > (AR - 30) ** 2) return true;
  const cx = Math.floor(x / CS), cy = Math.floor(y / CS);
  for (let gx = cx - 1; gx <= cx + 1; gx++) for (let gy = cy - 1; gy <= cy + 1; gy++) { const a = S.bgrid.get(key(gx, gy)); if (!a) continue;
    for (let k = 0; k < a.length; k += 2) { const o = a[k]; if (!o.alive || (o === self && a[k + 1] < SELF_IDX)) continue; const q = o.pts[a[k + 1]]; if (!q) continue; const rr = rad + rOf(o.mass), dx = q.x - x, dy = q.y - y; if (dx * dx + dy * dy < rr * rr) return true; } }
  return false;
}

// ---------- AI (เหมือน aiThink ในเกม ระดับ Normal) ----------
// ผู้เล่นยาวเกินทุก ๆ 1,000 → บอทเข้ามาไล่มากขึ้น (11 พ.ย. 2026 · ต้องตรงกับ index.html bigTier)
const BIG_START = 2000, BIG_STEP = 1000, BIG_MAX = 5, bigTier = o => o.human && (o.mass || 0) >= BIG_START ? Math.min(BIG_MAX, 1 + Math.floor(((o.mass || 0) - BIG_START) / BIG_STEP)) : 0;   // เริ่ม 2,000 (เจ้าของปรับ 11 พ.ย. 17:42)
// ⚔️ 2v2: บอทโหดขึ้น (เจ้าของสั่ง 12 พ.ย. 00:45 — ไล่ล่า โจมตี หลบเก่ง) · ใช้เฉพาะห้อง 2v2 (!room.ffa) · โลกออนไลน์ใช้ D เดิม
const VS_HUNTERS = 2;   // จำนวนนักล่ากลางในห้อง 2v2
// huntR 4800 = ทั้งสนาม 2v2 (กว้าง 4400): ทีมเกิดคนละฝั่ง ห่างกัน 1800–3000 เดิมระยะ 1900 เลยแทบไม่เคยไล่ (เจ้าของแจ้ง 13 พ.ย. 08:27)
// โหดขึ้นอีกรอบ (เจ้าของสั่ง 13 พ.ย. 06:54): คิดถี่ขึ้น ไล่ไกลขึ้น เร่งบ่อยขึ้น เลี้ยวไวขึ้น (VS_TURN) ขบวนเกิดยาวขึ้น · 2 ตัวไล่เป้าเดียวกัน = ประกบสองข้าง (คีม)
const DV = { huntP: .99, huntR: 4800, others: .9, othersR: 1800, look: 1.5, think: [3, 8], leadK: .7, boostR: 950, regen: .9, enMax: 8, dodge: 1 };
const VS_TURN = 1.15, VS_RESPAWN = 2, VS_HUNT_RESPAWN = 4;
const enemyHeadNear = (room, w, x, y, rr, trains) => { for (const o of trains) { if (o === w || !o.alive || ally(o, w) || o.ghost > 0) continue;   // หลบหัวศัตรูที่กำลังพุ่งมา (คาดตำแหน่งล่วงหน้า ~0.3 วิ)
    const oh = o.pts[0], oa = o.angle || 0, sp = (o.boost ? 5.4 : 2.7) * 18, px = oh.x + Math.cos(oa) * sp, py = oh.y + Math.sin(oa) * sp, R = rr + rOf(o.mass) + 14;
    if ((px - x) ** 2 + (py - y) ** 2 < R * R || (oh.x - x) ** 2 + (oh.y - y) ** 2 < R * R) return true; } return false; };
function aiThink(S, room, w, f, trains) {
  const h = w.pts[0], r = rOf(w.mass), ai = w.ai; ai.t -= f;
  const vs = !room.ffa && !w.isBoss, P = vs ? DV : D;
  if (vs && w.energy < DV.enMax) w.energy += f / 60 * DV.regen;   // 2v2: บอทเติมพลังเร่งเองช้า ๆ ไว้พุ่งตัดหน้า/หนี
  if (ai.t <= 0) {
    ai.t = rnd(P.think[0], P.think[1]) / (1 + .4 * bossRage(w)); ai.hunt = null;
    let bh = null, bd0 = 1100 + 250 * bossRage(w);
    if (w.isBoss) for (const o of trains) { if (!o.alive || !o.human || o.safe || o.ghost) continue; const d = Math.hypot(o.pts[0].x - h.x, o.pts[0].y - h.y); if (d < bd0) { bd0 = d; bh = o; } }
    if (bh) ai.hunt = bh;
    else if (w.mass > (vs ? 12 : 22)) { let bd = 1e9; for (const o of trains) { if (o === w || !o.alive || ally(o, w) || (w.hunter && !o.human)) continue; const oh = o.pts[0], d = Math.hypot(oh.x - h.x, oh.y - h.y), hu = !!o.human, bt = bigTier(o), de = d / (1 + .4 * bt) / (vs && hu ? 1.8 : 1);   // 2v2: เล็งคนจริงก่อนบอท
      if (!(hu ? (o.safe || o.ghost) : vs && (o.safe > 0 || o.ghost > 0)) && d < (hu ? P.huntR + 200 * bt : vs ? DV.othersR : 380) && de < bd && Math.random() < (hu ? P.huntP + (1 - P.huntP) * Math.min(1, .1 * bt) : P.others)) { bd = de; ai.hunt = o; } }
      // นักล่ากลาง 🎯 ล่าผู้เล่นจริงอย่างเดียว ไม่ยุ่งกับบอท (เจ้าของสั่ง 13 พ.ย. 09:22) · เลือกคนใหม่ทุกครั้งที่คิด (กระจายไล่ทั้งสองทีม)
      if (vs && (w.hunter || (ai.hunt && !ai.hunt.human))) { let hb = null, hd = 1e9;
      for (const o of trains) if (o.human && o.alive && !ally(o, w) && !(o.safe || o.ghost)) { let d = Math.hypot(o.pts[0].x - h.x, o.pts[0].y - h.y); if (d >= DV.huntR) continue;
        // นักล่า: คนที่นักล่าอีกตัวไล่อยู่แล้ว นับว่าไกลขึ้น 3 เท่า → นักล่า 2 ตัวแยกไล่คนละคน (บอททีมยังรุมประกบคนเดียวกันได้)
        if (w.hunter) for (const q of trains) if (q !== w && q.hunter && q.alive && q.ai && q.ai.hunt === o) { d *= 3; break; }
        if (d < hd) { hd = d; hb = o; } } if (hb) ai.hunt = hb; } }   // 2v2: มีคนจริงในระยะ = ไล่คนก่อนเสมอ
    if (!ai.hunt) {
      let best = null, bs = 0; const cx = Math.floor(h.x / CS), cy = Math.floor(h.y / CS);
      for (let gx = cx - 4; gx <= cx + 4; gx++) for (let gy = cy - 4; gy <= cy + 4; gy++) { const a = S.fgrid.get(key(gx, gy)); if (!a) continue;
        for (const fd of a) { const s = fd[3] / (Math.hypot(fd[1] - h.x, fd[2] - h.y) + 40); if (s > bs) { bs = s; best = { x: fd[1], y: fd[2], v: fd[3] }; } } }
      if (w.energy < 4) for (const wd of room.whites.values()) { const s = 6 / (Math.hypot(wd[1] - h.x, wd[2] - h.y) + 40); if (s > bs) { bs = s; best = { x: wd[1], y: wd[2], v: 0 }; } }
      if (best) { ai.tx = best.x; ai.ty = best.y; ai.boostT = best.v > 1.5 && w.mass > 25 ? 40 : 0; } else [ai.tx, ai.ty] = randIn(room, 500);
    }
  }
  let tx = ai.tx, ty = ai.ty, boost = false;
  if (ai.hunt && ai.hunt.alive) { const o = ai.hunt, oh = o.pts[0], d = Math.hypot(oh.x - h.x, oh.y - h.y);
    if (d > (w.isBoss ? 1300 + 250 * bossRage(w) : vs ? (o.human ? DV.huntR : 1700) : 850 + 200 * bigTier(o)) || (vs && (o.ghost > 0))) ai.hunt = null;
    else if (vs) {   // 2v2: วิ่งขนาน แล้วพุ่งตัดหน้าให้ศัตรูชนลำตัวเรา
      const oa = o.angle || 0, osp = o.boost ? 5.4 : 2.7; let cut = 90 + rOf(o.mass) * 4, side = Math.sign(Math.cos(oa) * (h.y - oh.y) - Math.sin(oa) * (h.x - oh.x)) || 1;
      // เดาว่าเป้าจะอยู่ไหนตอนเราไปถึง: วิ่งโค้งด้วยความเร็วเลี้ยวปัจจุบัน (o.av) · τ = เวลาที่เราใช้ไปถึง (เพดาน 2.2 วิ)
      const tau = Math.min(2.2, d / (2.7 * 60 * 1.3)), v = osp * 60, om = Math.max(-3, Math.min(3, o.av || 0)), pa = oa + om * tau;
      const px = Math.abs(om) < .05 ? oh.x + Math.cos(oa) * v * tau : oh.x + v / om * (Math.sin(pa) - Math.sin(oa)), py = Math.abs(om) < .05 ? oh.y + Math.sin(oa) * v * tau : oh.y + v / om * (Math.cos(oa) - Math.cos(pa));
      // คีม: มีพวกเดียวกัน (หรือนักล่าตัวอื่น) ไล่เป้าเดียวกันอยู่ → ตัวที่ id น้อยกว่าอ้อมไปอีกข้าง + ตัดไกลกว่า ปิดทางหนีสองฝั่ง
      for (const q of trains) if (q !== w && q.bot && q.alive && q.ai && q.ai.hunt === o && (ally(q, w) || (q.hunter && w.hunter)) && q.id < w.id) { side = -(Math.sign(Math.cos(oa) * (q.pts[0].y - oh.y) - Math.sin(oa) * (q.pts[0].x - oh.x)) || 1); cut *= 1.8; break; }
      const off = d > 380 ? 140 * side : 0; tx = px + Math.cos(pa) * cut - Math.sin(pa) * off; ty = py + Math.sin(pa) * cut + Math.cos(pa) * off;
      boost = w.mass > 14 && ((d < DV.boostR || osp > 3) && w.energy > .4 || o.human && d > 1100 && w.energy > 4.5); }   // ไกลคนจริง + พลังเหลือ = เร่งตามไปก่อน (เก็บไว้ ≥4.5 วิสำหรับพุ่งตัดหน้า)
    else { const lead = 60 + rOf(o.mass) * 3 + d * .45, oa = o.angle || 0; tx = oh.x + Math.cos(oa) * lead; ty = oh.y + Math.sin(oa) * lead; boost = d < 450 + 150 * bossRage(w) && w.mass > 18; } }
  else if (ai.boostT > 0) { ai.boostT -= f; boost = true; }
  if (w.flee && w.flee.t > 0) { w.flee.t -= f / 60; tx = h.x + Math.cos(w.flee.a) * 400; ty = h.y + Math.sin(w.flee.a) * 400; boost = false; }   // โดนหวูดไล่
  if (Math.hypot(h.x, h.y) > arenaR(room) - 350) { tx = 0; ty = 0; boost = false; }
  const want = Math.atan2(ty - h.y, tx - h.x), lk = w.isBoss ? 1.3 : P.look, near = (r * 1.4 + 25) * lk, look = (r * 3 + 65) * lk, mid = (r * 2.2 + 45) * lk;
  const blocked = a => bodyNear(S, room, h.x + Math.cos(a) * near, h.y + Math.sin(a) * near, r + 12, w) || bodyNear(S, room, h.x + Math.cos(a) * look, h.y + Math.sin(a) * look, r + 18, w)
    || (vs && (bodyNear(S, room, h.x + Math.cos(a) * mid, h.y + Math.sin(a) * mid, r + 14, w) || enemyHeadNear(room, w, h.x + Math.cos(a) * near, h.y + Math.sin(a) * near, r, trains)));
  let pk = want;
  if (blocked(want)) { pk = null; const side = Math.sign(Math.atan2(Math.sin(want - w.angle), Math.cos(want - w.angle))) || 1;
    for (const o of vs ? [0, .35, -.35, .7, -.7, 1.1, -1.1, 1.6, -1.6, 2.2, -2.2, 2.8, -2.8] : [0, .6, -.6, 1.2, -1.2, 1.9, -1.9, 2.6, -2.6]) { const a = w.angle + o * side; if (!blocked(a)) { pk = a; break; } }
    if (pk === null) pk = w.angle + Math.PI * side; boost = boost || (w.mass > (vs ? 14 : 30) && Math.random() < (vs ? .75 : .4)); }
  w.target = pk; w.boost = boost;
}

function portalOpen(room, p) { const q = room.sim.world.portals[p.pair], AR = arenaR(room); return Math.hypot(q.x, q.y) < AR - PORTAL_EDGE && Math.hypot(p.x, p.y) < AR - 60; }
function moveBot(S, room, w, f, dt) {
  const r = rOf(w.mass); let d = w.target - w.angle; d = Math.atan2(Math.sin(d), Math.cos(d));
  const rg = bossRage(w), tr = .12 / (1 + r / 30) * f * (1 + RAGE_TURN * rg) * (!room.ffa && !w.isBoss ? VS_TURN : 1); w.angle += Math.max(-tr, Math.min(tr, d));
  let sp = 2.7 * (w.isBoss ? RAGE_SPD[Math.min(2, rg)] : 1); const slowed = w.slow > 0; if (slowed) { w.slow -= dt; sp *= .45; }
  if (w.boost && w.energy > 0) { sp *= 2; w.energy = Math.max(0, w.energy - dt); }
  if (w.isBoss) sp = Math.min(sp, BOSS_CAP * (slowed ? .45 : 1));
  const h = w.pts[0]; h.x += Math.cos(w.angle) * sp * f; h.y += Math.sin(w.angle) * sp * f; follow(w);
  (w.hist || (w.hist = [])).push(h.x, h.y); if (w.hist.length > LAG_STEPS * 2 + 2) w.hist.splice(0, 2);   // ตำแหน่งหัวย้อนหลัง (ไว้ชดเชยดีเลย์)
  if (w.tun) w.tun.t += dt; if (w.safe > 0) w.safe -= dt; if (w.hitCD > 0) w.hitCD -= dt; if (w.ghost > 0) w.ghost -= dt; if (w.selfCD > 0) w.selfCD -= dt;
  if (w.tunCD > 0) w.tunCD -= dt; else for (const p of S.world.portals) if ((h.x - p.x) ** 2 + (h.y - p.y) ** 2 < 38 * 38) { if (!portalOpen(room, p)) break;
    tunStart(S.world, w, p); w.hist = null; w.tunCD = 1.5; w.safe = Math.max(w.safe, TUNNEL_SAFE); break; }
  if (w.mass > w.maxLen) w.maxLen = w.mass;
  if (w.isBoss && w.energy < 20) w.energy += dt * .5 * (1 + bossRage(w));
  if (h.x * h.x + h.y * h.y > (arenaR(room) - r * .5) ** 2) killBot(room, w, null);
}

// ---------- ตาย / ขาด ----------
function killBot(room, w, killer, how) {
  if (!w.alive) return; w.alive = false; const S = room.sim;
  if (how !== 'trim') { const m = w.mass * .8, cnt = Math.max(6, Math.min(160, Math.floor(w.pts.length / 2))), drop = [];
    for (let i = 0; i < cnt; i++) { const q = w.pts[Math.floor(i / cnt * w.pts.length)]; drop.push([Math.round(q.x + rnd(-10, 10)), Math.round(q.y + rnd(-10, 10))]); }
    S.drop(room, drop, m / cnt, DROP_TTL); }
  let kid = null;
  if (killer && killer.human) { const p = room.players.get(killer.pid); if (p && (room.ffa || p.team !== w.team)) { p.kills++; kid = p.id; } }
  else if (killer && killer.bot && killer !== w) { if (!ally(killer, w)) killer.kills++; kid = killer.id; }
  if (room.ffa) room.bots.delete(w.id); else { w.st = null; w.dead = true; }
  if (w.isBoss) { S.boss = null; S.bossT = 150; }
  const msg = { t: 'kill', v: w.id, k: kid }; if (how === 'bomb') msg.b = 1; S.bcast(room, msg);
}
function cutBot(room, w, idx) {
  const p = w.pts; if (idx >= p.length) return; const removed = p.slice(idx), old = w.mass;
  w.mass = Math.max(10, (idx - 14) / .45); p.length = Math.min(p.length, nOf(w.mass));
  const lost = Math.max(0, old - w.mass); if (lost > 0) { const cnt = Math.max(3, Math.min(80, Math.floor(removed.length / 3))), drop = [];
    for (let i = 0; i < cnt; i++) { const q = removed[Math.floor(i / cnt * removed.length)]; drop.push([Math.round(q.x + rnd(-8, 8)), Math.round(q.y + rnd(-8, 8))]); }
    room.sim.drop(room, drop, lost * .5 / cnt); }
  w.selfCD = .8;
}
const nearestIdx = (w, x, y) => { let bi = 8, bd = 1e18; w.pts.forEach((q, i) => { const d = (q.x - x) ** 2 + (q.y - y) ** 2; if (d < bd) { bd = d; bi = i; } }); return Math.max(bi, 8); };
function hurtBoss(room, b, by) { if (!b || !b.alive || !b.isBoss || b.hitCD > 0) return; b.hitCD = BOSS_HIT_CD; b.hp -= 1;   // กันหลายเครื่องส่งซ้ำ: 1 ดวงต่อ 1.5 วิ
  if (b.hp <= 0) { b.hp = 0; killBot(room, b, by); } else { b.angle += Math.PI; b.target = b.angle; b.safe = Math.max(b.safe, BOSS_HIT_CD); b.ai.t = 60; } }

// ชดเชยดีเลย์: ผู้เล่นเห็นบอทช้ากว่าเซิร์ฟเวอร์ ~0.2 วิ (วาดย้อนหลัง 130ms + เน็ต) → บนจอผู้เล่นบอทวิ่งทะลุลำตัวเราได้
// เลยเช็คหัวบอททั้ง "ตอนนี้" และ "เมื่อ ~0.2 วิก่อน" (= ตำแหน่งที่ผู้เล่นเห็นบนจอ) กับลำตัวผู้เล่นจริง แตะอันไหนก็ตาย
function hitsHuman(w, o, idx, r) { const q = o.pts[idx], hs = w.hist; if (!q || !hs || hs.length < LAG_STEPS * 2) return false;
  const px = hs[hs.length - LAG_STEPS * 2], py = hs[hs.length - LAG_STEPS * 2 + 1], rr = r * .7 + rOf(o.mass) * .9; return (q.x - px) ** 2 + (q.y - py) ** 2 < rr * rr; }
function collide(S, room) {
  for (const w of room.bots.values()) {
    if (!w.alive || w.safe > 0) continue; const h = w.pts[0], r = rOf(w.mass), cx = Math.floor(h.x / CS), cy = Math.floor(h.y / CS);
    let hit = null, hitIdx = 0, cut = -1;
    for (let gx = cx - 1; gx <= cx + 1 && !hit; gx++) for (let gy = cy - 1; gy <= cy + 1 && !hit; gy++) { const a = S.bgrid.get(key(gx, gy)); if (!a) continue;
      for (let k = 0; k < a.length; k += 2) { const o = a[k], idx = a[k + 1]; if (!o.alive) continue;
        if (o === w && (idx < SELF_IDX || w.selfCD > 0)) continue; if (o !== w && (ally(o, w) || o.ghost > 0)) continue;
        if (w.isBoss && o.human) continue;   // บอสชนผู้เล่น → เครื่องผู้เล่นตัดสินเองจากภาพที่เห็น (เซิร์ฟเวอร์เห็นตำแหน่งช้ากว่า เลยขาดทั้งที่ยังไม่แตะ)
        const q = o.pts[idx]; if (!q) continue; const rr = r * .7 + rOf(o.mass) * .9, dx = q.x - h.x, dy = q.y - h.y;
        if (dx * dx + dy * dy < rr * rr) { if (o === w) { if (cut < 0 || idx < cut) cut = idx; } else if (!(idx > 0 && inMouth(room, q))) { hit = o; hitIdx = idx; break; } } } }
    if (!hit && !w.isBoss && w.hist) {   // หัวบอทเมื่อ ~0.2 วิก่อน (ที่ผู้เล่นเห็นบนจอ) แตะลำตัวผู้เล่น → ตายเหมือนกัน
      const hs = w.hist, px = hs[0], py = hs[1], pcx = Math.floor(px / CS), pcy = Math.floor(py / CS);
      for (let gx = pcx - 1; gx <= pcx + 1 && !hit; gx++) for (let gy = pcy - 1; gy <= pcy + 1 && !hit; gy++) { const a = S.bgrid.get(key(gx, gy)); if (!a) continue;
        for (let k = 0; k < a.length; k += 2) { const o = a[k]; if (!o.human || !o.alive || ally(o, w) || o.ghost > 0) continue; if (hitsHuman(w, o, a[k + 1], r) && !inMouth(room, o.pts[a[k + 1]])) { hit = o; break; } } } }
    if (hit && w.isBoss) {   // บอสชนบอทตัวอื่น → บอทขาด (บอสไม่ตาย) · ชนผู้เล่นจริง client ตรวจเอง
      w.safe = .8; cutBot(room, hit, Math.max(hitIdx, 8));
    } else if (hit) killBot(room, w, hit);
    else if (cut > 0) cutBot(room, w, cut);
  }
}

function eat(S, room) {
  const gone = [], wgone = [];
  for (const w of room.bots.values()) {
    if (!w.alive) continue; const h = w.pts[0], r = rOf(w.mass), lb = (LOCO_PERK[w.loco] || LOCO_PERK.classic).pick, reach = r + 14 + lb + 12;
    const x0 = Math.floor((h.x - reach) / CS), x1 = Math.floor((h.x + reach) / CS), y0 = Math.floor((h.y - reach) / CS), y1 = Math.floor((h.y + reach) / CS);
    for (let gx = x0; gx <= x1; gx++) for (let gy = y0; gy <= y1; gy++) { const a = S.fgrid.get(key(gx, gy)); if (!a) continue;
      for (const fd of a) { if (fd.eaten) continue; const fr = 3 + Math.sqrt(fd[3]) * 2.4, er = r + fr + 6 + lb, dx = fd[1] - h.x, dy = fd[2] - h.y;
        if (dx * dx + dy * dy < er * er && room.foods.delete(fd[0])) { fd.eaten = true; room.exp.delete(fd[0]); w.mass += fd[3] * GROW; gone.push(fd[0]); } } }
    for (const wd of room.whites.values()) if (Math.hypot(wd[1] - h.x, wd[2] - h.y) < r + 20 + lb) { room.whites.delete(wd[0]); wgone.push(wd[0]); w.energy = Math.min((LOCO_PERK[w.loco] || LOCO_PERK.classic).en, w.energy + 5); }
  }
  if (gone.length) S.bcast(room, { t: 'fr', f: gone });
  for (const id of wgone) S.bcast(room, { t: 'wr', id });
}

function fill(S, room, dt) {
  const live = [...room.bots.values()].filter(b => b.alive && !b.isBoss);
  if (room.ffa) {
    const want = Math.max(0, FFA_MAX - room.players.size); let n = live.length;
    if (n < want) { const add = n < want - 2 ? want - n - 2 : (Math.random() < .03 ? 1 : 0); for (let i = 0; i < add; i++) spawnBot(room); }
    else if (n > want && (S.trimT -= dt) <= 0) { S.trimT = .4;   // คนจริงเข้ามา → เอาบอทที่ไกลคนที่สุดออกทีละตัว
      const hs = [...room.players.values()].filter(p => p.body).map(p => p.body.pts[0]); let far = null, fd = -1;
      for (const b of live) { const h = b.pts[0]; let d = 1e9; for (const q of hs) d = Math.min(d, Math.hypot(q.x - h.x, q.y - h.y)); if (d > fd) { fd = d; far = b; } }
      if (far) killBot(room, far, null, 'trim'); }
    if (!S.boss || !S.boss.alive) { S.boss = null; S.bossT -= dt; if (S.bossT <= 0 && room.players.size) { S.bossT = D.boss; spawnBot(room, { boss: true }); } }
  } else if (room.phase === 'play') {
    const hum = { A: 0, B: 0 }; for (const p of room.players.values()) if (hum[p.team] !== undefined) hum[p.team]++;
    for (const t of ['A', 'B']) { const mine = live.filter(b => b.team === t), want = Math.max(0, TEAM_MAX - hum[t]);
      if (mine.length > want) killBot(room, mine[0], null, 'trim');
      else if (mine.length < want) { S.vsT[t] -= dt; if (S.vsT[t] <= 0) { for (let i = mine.length; i < want; i++) spawnBot(room, { team: t }); S.vsT[t] = VS_RESPAWN; } } else S.vsT[t] = VS_RESPAWN; }
    // 🎯 นักล่ากลาง (เจ้าของสั่ง 12 พ.ย. 01:22 "2v2 ให้มีบอทไล่ฆ่าทั้ง 2 ทีม"): ไม่มีทีม ไล่ฆ่าทุกคนทั้งทีมแดง/น้ำเงิน · ตายแล้วเกิดใหม่ใน 6 วิ · แต้มที่มันทำไม่เข้าทีมไหน
    const hn = live.filter(b => b.hunter).length;
    if (hn < VS_HUNTERS) { S.vsT.H = (S.vsT.H ?? 4) - dt; if (S.vsT.H <= 0) { for (let i = hn; i < VS_HUNTERS; i++) spawnBot(room, { hunter: true }); S.vsT.H = VS_HUNT_RESPAWN; } } else S.vsT.H = VS_HUNT_RESPAWN;
  }
}

// ---------- เรียกจาก server.js ----------
function ensure(room, bcast, drop) {
  if (!room.sim || room.sim.R !== room.cfg.R) room.sim = { R: room.cfg.R, world: buildWorld(room.cfg.R), bossT: D.boss, boss: null, trimT: 0, vsT: { A: 0, B: 0 }, bgrid: new Map(), fgrid: new Map() };
  room.sim.bcast = bcast; room.sim.drop = drop; return room.sim;
}
function step(room, dt, bcast, drop) {
  if (!room.ffa && room.phase !== 'play') return;
  const S = ensure(room, bcast, drop);
  syncPlayers(room); fill(S, room, dt);
  if (!room.bots.size) return;
  S.fgrid = new Map(); for (const fd of room.foods.values()) { const k = key(Math.floor(fd[1] / CS), Math.floor(fd[2] / CS)); let a = S.fgrid.get(k); if (!a) S.fgrid.set(k, a = []); a.push(fd); }
  const SUB = 3, f = dt * 60 / SUB, sdt = dt / SUB;   // คำนวณ 60 ครั้ง/วิ (3 รอบย่อยต่อ tick) ให้ชนแม่นเหมือนในเกม
  for (let s = 0; s < SUB; s++) {
    const trains = allTrains(room); S.bgrid = buildGrid(trains);
    for (const w of room.bots.values()) if (w.alive) aiThink(S, room, w, f, trains);
    for (const w of room.bots.values()) if (w.alive) moveBot(S, room, w, f, sdt);
    S.bgrid = buildGrid(allTrains(room)); collide(S, room);
  }
  eat(S, room);
  const ts = Date.now();
  for (const w of room.bots.values()) { if (!w.alive) continue; const h = w.pts[0];
    w.st = [w.id, Math.round(h.x), Math.round(h.y), +w.angle.toFixed(2), +w.mass.toFixed(1), (w.boost && w.energy > 0 ? 1 : 0) | 4 | (w.slow > 0 ? 8 : 0) | (w.safe > 0 ? 16 : 0) | (w.ghost > 0 ? 32 : 0), ts];
    if (w.isBoss) w.st.push(Math.ceil(w.hp)); }
}
// การกระทำของผู้เล่นที่มีผลกับบอท
function onBomb(room, by, x, y) { if (!room.sim) return;
  for (const w of [...room.bots.values()]) { if (!w.alive || (by.team && w.team === by.team)) continue;
    if (w.isBoss) continue; const r = bombHitBot(room, w, x, y); if (r === 'head') killBot(room, w, by.body || { human: true, pid: by.id }, 'bomb'); } }
// ระเบิด: โดนหัว (จุด 0–7) = ตาย · โดนแค่ลำตัว = ตัดเฉพาะส่วนในวง (ต้องตรงกับ bombHit ใน index.html)
function bombHitBot(room, w, x, y) { const BR = room.ffa ? BOMB_R_FFA : BOMB_R_VS, p = w.pts, R2 = BR * BR, rh = (BR + rOf(w.mass)) ** 2;
  for (let i = 0; i < Math.min(8, p.length); i++) if ((p[i].x - x) ** 2 + (p[i].y - y) ** 2 < rh) return 'head';
  if (w.tun) { const T = w.tun; for (let i = T.k; i < p.length; i++) { p[i].x += T.dx; p[i].y += T.dy; } w.tun = null; }
  const keep = [], gone = []; p.forEach((q, i) => ((i >= 8 && (q.x - x) ** 2 + (q.y - y) ** 2 < R2) ? gone : keep).push(q)); if (!gone.length) return false;
  const old = w.mass; w.mass = Math.max(10, old - gone.length / .45); w.pts = keep; if (keep.length > nOf(w.mass)) keep.length = nOf(w.mass); w.hist = null;
  const lost = Math.max(0, old - w.mass); if (lost > 0) { const cnt = Math.max(3, Math.min(80, Math.floor(gone.length / 3))), drop = [];
    for (let i = 0; i < cnt; i++) { const q = gone[Math.floor(i / cnt * gone.length)]; drop.push([Math.round(q.x + rnd(-8, 8)), Math.round(q.y + rnd(-8, 8))]); }
    room.sim.drop(room, drop, lost * .5 / cnt); }
  w.selfCD = .8; return 'cut'; }
function onHorn(room, by, x, y, k) { const P = HORN_PERK[k] || HORN_PERK.classic; if (!P.r) return;   // หวูดไอน้ำ (ฟรี) = เสียงอย่างเดียว
  for (const w of room.bots.values()) { if (!w.alive || (by.team && w.team === by.team)) continue; const h = w.pts[0]; if (Math.hypot(h.x - x, h.y - y) > P.r + rOf(w.mass)) continue;
    const away = Math.atan2(h.y - y, h.x - x), s1 = w.angle + Math.PI / 2, s2 = w.angle - Math.PI / 2;
    w.flee = { t: P.t * (w.isBoss ? .5 : 1), a: Math.cos(s1 - away) >= Math.cos(s2 - away) ? s1 : s2 }; } }
function onFreeze(room, by, x, y) { for (const w of room.bots.values()) if (w.alive && !(by.team && w.team === by.team) && Math.hypot(w.pts[0].x - x, w.pts[0].y - y) < FREEZE_R) w.slow = FREEZE_T; }
function onCut(room, by, v, x, y) { const w = room.bots.get(v); if (!w || !w.alive || (by.team && w.team === by.team)) return; cutBot(room, w, nearestIdx(w, x, y)); }
function onBossHit(room, by, id) { const w = room.bots.get(id); if (w && w.isBoss) hurtBoss(room, w, by.body || { human: true, pid: by.id }); }
function clear(room) { room.bots.clear(); if (room.sim) { room.sim.boss = null; room.sim.vsT = { A: 0, B: 0 }; } }

module.exports = { step, onBomb, onFreeze, onHorn, onCut, onBossHit, clear, buildWorld };
