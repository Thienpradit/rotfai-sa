// รถไฟซ่า.io — เซิร์ฟเวอร์: โหมดไม่จำกัดแบบ free-for-all (ทุกคนอยู่โลกเดียวกัน คนจริงเข้ามาแทนบอท) + ออนไลน์ 2v2
// รัน:  npm install  แล้ว  npm start   (ค่าเริ่มต้นพอร์ต 3000 หรือกำหนดด้วยตัวแปร PORT)
const http = require('http');
const fs = require('fs');
const path = require('path');
const { WebSocketServer } = require('ws');
const { handleApi } = require('./accounts');

const PORT = process.env.PORT || 3000;
const R2 = 2200, RF = 3000;  // รัศมีสนาม: 2v2 / free-for-all
const CFG = { vs: { R: R2, food: 700, white: 40, pu: 10, max: 4 }, ffa: { R: RF, food: 1400, white: 60, pu: 16, max: 30 } };   // ออนไลน์: โลกละ 30 คน (ขาดเติมบอท)
const DIFFS = ['easy', 'normal', 'hard'];
const MATCH = +process.env.MATCH_SECS || 300;   // วินาทีต่อแมตช์
const SHRINK = Math.min(120, Math.round(MATCH * .4));   // วงเริ่มหดเมื่อเหลือกี่วินาที
const TEAM_MAX = 2;
const PU_KEYS = ['magnet', 'x3', 'speed', 'freeze'];
const TICK = 1 / 20;   // ส่งสถานะ 20 ครั้ง/วินาที

// ---------- static files ----------
const PUBLIC = path.join(__dirname, 'public');
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.json': 'application/json', '.webmanifest': 'application/manifest+json' };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent((req.url || '/').split('?')[0]);
  if (p === '/health') { res.writeHead(200, { 'Content-Type': 'text/plain' }); return res.end('ok'); }
  // ย้ายเซิร์ฟเวอร์: ตั้ง env REDIRECT_TO=https://ที่อยู่ใหม่ แล้วลิงก์เก่าจะพาไปที่ใหม่เอง (เก็บ ?w=โค้ดโลก ไว้ด้วย)
  if (process.env.REDIRECT_TO) { res.writeHead(301, { Location: process.env.REDIRECT_TO.replace(/\/$/, '') + (req.url || '/') }); return res.end(); }
  if (p.startsWith('/api/')) return handleApi(req, res, p);
  if (p === '/') p = '/index.html';
  const file = path.join(PUBLIC, path.normalize(p));
  if (!file.startsWith(PUBLIC)) { res.writeHead(403); return res.end(); }
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); return res.end('not found'); }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
    res.end(data);
  });
});

// ---------- helpers ----------
const rooms = new Map();
let nextId = 1;
const rnd = (a, b) => a + Math.random() * (b - a);
const arena = room => !room.ffa && room.phase === 'play' && room.timeLeft < SHRINK ? room.cfg.R * (.3 + .7 * Math.max(0, room.timeLeft) / SHRINK) : room.cfg.R;
function randIn(room, m) { const a = Math.random() * Math.PI * 2, r = Math.sqrt(Math.random()) * Math.max(50, arena(room) - m); return [Math.round(Math.cos(a) * r), Math.round(Math.sin(a) * r)]; }
function send(ws, o) { if (ws.readyState === 1) ws.send(JSON.stringify(o)); }
function bcast(room, o, except) { const s = JSON.stringify(o); for (const p of room.players.values()) if (p.ws !== except && p.ws.readyState === 1) p.ws.send(s); }
const clean = (s, n) => String(s || '').replace(/[<>&]/g, '').slice(0, n);

const DROP_TTL = 30;   // พลอยที่หล่นตอนตายอยู่ได้ 30 วินาที ถ้าไม่มีใครเก็บจะหายไป
function newFood(room, x, y, v, ttl) {
  if (x === undefined) [x, y] = randIn(room, 40);
  const f = [room.nid++, Math.round(x), Math.round(y), Math.round((v || 1) * 100) / 100, (Math.random() * 7) | 0];
  if (ttl) { f.push(ttl); room.exp.set(f[0], Date.now() + ttl * 1000); }
  room.foods.set(f[0], f); return f;
}
// ส่งอาหารให้คนที่เพิ่งเข้าห้อง: พลอยที่กำลังจะหายให้บอกเวลาที่เหลือจริง
const foodsNow = room => { const now = Date.now(); return [...room.foods.values()].map(f => f.length > 5 ? [f[0], f[1], f[2], f[3], f[4], Math.max(1, Math.round(((room.exp.get(f[0]) || now) - now) / 1000))] : f); };
function newWhite(room) { const [x, y] = randIn(room, 60); const w = [room.nid++, x, y]; room.whites.set(w[0], w); return w; }
function newPu(room) { const [x, y] = randIn(room, 150); const p = [room.nid++, x, y, PU_KEYS[(Math.random() * PU_KEYS.length) | 0]]; room.pups.set(p[0], p); return p; }

function getRoom(code, ffa) {
  const key = (ffa ? 'F:' : 'V:') + code;
  let r = rooms.get(key);
  if (!r) {
    const cfg = ffa ? CFG.ffa : CFG.vs;
    r = { key, code, ffa, diff: 'normal', cfg, players: new Map(), foods: new Map(), whites: new Map(), pups: new Map(), items: { tgs: null, gold: null },
      timers: { tgs: 30, gold: 50 }, phase: ffa ? 'play' : 'lobby', timeLeft: MATCH, nid: 1, bots: new Map(), exp: new Map() };
    for (let i = 0; i < cfg.food; i++) newFood(r);
    for (let i = 0; i < cfg.white; i++) newWhite(r);
    for (let i = 0; i < cfg.pu; i++) newPu(r);
    rooms.set(key, r);
  }
  return r;
}
const pubPlayers = room => [...room.players.values()].map(p => ({ id: p.id, name: p.name, team: p.team, host: p.host, skin: p.skin, loco: p.loco, smoke: p.smoke, wag: p.wag, kfx: p.kfx, title: p.title, rk: p.rk }));
const pubBots = room => [...room.bots.values()].map(b => b.info);
// free-for-all: รถไฟ AI ทั้งหมดรันอยู่ในเครื่องหัวหน้าห้อง ถ้าหัวหน้าเปลี่ยน ต้องล้าง AI ชุดเก่าทิ้ง
function clearBots(room) { room.deadBots = 0; if (!room.bots.size) return; room.bots.clear(); bcast(room, { t: 'bclr' }); }
function setHost(room, p) { for (const q of room.players.values()) q.host = q === p; clearBots(room); lobby(room); }
const lobby = room => bcast(room, { t: 'lobby', players: pubPlayers(room), phase: room.phase });
function teamScore(room) {
  const sc = { A: { k: 0, l: 0 }, B: { k: 0, l: 0 } };
  for (const p of room.players.values()) { if (!sc[p.team]) continue; sc[p.team].k += p.kills; if (p.st && p.st.f & 4) sc[p.team].l += p.st.m; }
  if (!room.ffa) for (const b of room.bots.values()) { const t = sc[b.info.team]; if (!t) continue; t.k += b.kills || 0; if (b.st && b.st[5] & 4) t.l += b.st[4]; }   // 2v2: บอทที่เติมให้ทีมนับคะแนนด้วย
  return sc;
}

// ---------- match flow ----------
function startMatch(room) {
  clearBots(room);
  room.phase = 'play'; room.timeLeft = MATCH; room.items = { tgs: null, gold: null }; room.timers = { tgs: 30, gold: 50 };
  const spawns = {}; const per = { A: 0, B: 0 };
  for (const p of room.players.values()) {
    p.kills = 0; p.maxLen = 20; p.st = null;
    const side = p.team === 'A' ? Math.PI : 0, a = side + (per[p.team]++ ? .5 : -.5);
    spawns[p.id] = [Math.round(Math.cos(a) * room.cfg.R * .55), Math.round(Math.sin(a) * room.cfg.R * .55), +(side + Math.PI).toFixed(2)];
  }
  bcast(room, { t: 'start', spawns, timeLeft: MATCH, players: pubPlayers(room) });
  bcast(room, { t: 'it', items: room.items });
}
function endMatch(room) {
  const sc = teamScore(room);
  const A = sc.A.k * 100 + Math.floor(sc.A.l), B = sc.B.k * 100 + Math.floor(sc.B.l);
  const ps = [...room.players.values()];
  let mvp = null, mv = -1; for (const p of ps) { const v = p.kills * 100 + p.maxLen; if (v > mv) { mv = v; mvp = p.id; } }
  const bots = [...room.bots.values()].filter(b => !b.dead || b.kills).map(b => ({ id: b.info.id, name: b.info.name, team: b.info.team, kills: b.kills || 0, maxLen: b.maxLen || 20, bot: true }));
  for (const b of bots) { const v = b.kills * 100 + b.maxLen; if (v > mv) { mv = v; mvp = b.id; } }
  bcast(room, { t: 'end', winner: A > B ? 'A' : B > A ? 'B' : 'draw', A, B, mvp,
    players: ps.map(p => ({ id: p.id, name: p.name, team: p.team, kills: p.kills, maxLen: p.maxLen })).concat(bots) });
  clearBots(room);
  room.phase = 'lobby'; room.timeLeft = MATCH; room.items = { tgs: null, gold: null };
  lobby(room);
}

// ---------- connections ----------
const wss = new WebSocketServer({ server, path: '/ws', maxPayload: 64 * 1024 });
wss.on('connection', ws => {
  let room = null, me = null;
  ws.on('message', raw => {
    let m; try { m = JSON.parse(raw); } catch (e) { return; }
    if (!me) {
      if (m.t !== 'join') return;
      const ffa = m.mode === 'ffa' || m.mode === 'coop', d = ffa ? 'normal' : (DIFFS.includes(m.diff) ? m.diff : 'normal');   // ออนไลน์ใช้ Normal อย่างเดียว ทุกคนอยู่โลกเดียวกัน
      let code = clean(m.room, 8).toUpperCase().replace(/[^0-9A-Z]/g, '');
      if (ffa && !code) {   // จับคู่อัตโนมัติ: เข้าโลกที่ระดับความยากเดียวกันและยังไม่เต็ม ถ้าไม่มีก็เปิดโลกใหม่
        const open = [...rooms.values()].find(r => r.ffa && r.diff === d && r.players.size < r.cfg.max);
        if (open) code = open.code; else do code = d[0].toUpperCase() + Math.random().toString(36).slice(2, 5).toUpperCase(); while (rooms.has('F:' + code));
      }
      code = code || 'PUBLIC';
      const fresh = !rooms.has((ffa ? 'F:' : 'V:') + code);
      room = getRoom(code, ffa);
      if (fresh && ffa) room.diff = d;
      if (room.players.size >= room.cfg.max) { send(ws, { t: 'err', msg: `ห้องนี้เต็มแล้ว (${room.cfg.max} คน) ลองรหัสห้องอื่น` }); room = null; return; }
      const nA = [...room.players.values()].filter(p => p.team === 'A').length;
      me = { id: nextId++, ws, name: clean(m.name, 14) || 'ผู้เล่น', team: ffa ? null : nA <= room.players.size - nA ? 'A' : 'B',
        host: room.players.size === 0, skin: Array.isArray(m.skin) ? m.skin.slice(0, 3).map(c => clean(c, 9)) : ['#ffd23f', '#ff8c42'],
        loco: clean(m.loco, 10), smoke: clean(m.smoke, 10), wag: clean(m.wag, 10), kfx: clean(m.kfx, 10), title: clean(m.title, 24), rk: Math.max(0, Math.min(30, m.rk | 0)), kills: 0, maxLen: 20, st: null, lastT: Date.now() };
      room.players.set(me.id, me);
      send(ws, { t: 'welcome', id: me.id, R: room.cfg.R, mode: ffa ? 'ffa' : 'vs', code: room.code, diff: room.diff, shrink: SHRINK, phase: room.phase, timeLeft: room.timeLeft, players: pubPlayers(room),
        foods: foodsNow(room), whites: [...room.whites.values()], pups: [...room.pups.values()], items: room.items, bots: pubBots(room) });
      lobby(room);
      return;
    }
    switch (m.t) {
      case 'team':
        if (room.ffa || room.phase !== 'lobby') break;
        { const want = m.k === 'A' || m.k === 'B' ? m.k : me.team === 'A' ? 'B' : 'A';
          if (want !== me.team && [...room.players.values()].filter(p => p.team === want).length < TEAM_MAX) { me.team = want; lobby(room); } }
        break;
      case 'start':
        if (!room.ffa && me.host && room.phase === 'lobby') {
          const ps = [...room.players.values()];
          if (ps.length) startMatch(room);   // คนไม่ครบ → เครื่องหัวหน้าห้องเติมบอทให้ทีมที่ขาด
        }
        break;
      case 'st':
        me.lastT = Date.now();
        me.st = { x: +m.x || 0, y: +m.y || 0, a: +m.a || 0, m: Math.min(5000, +m.m || 0), f: m.f | 0, ts: +m.ts || Date.now() };   // ts = เวลาของเครื่องผู้ส่ง ใช้ทำการเคลื่อนไหวให้ลื่น
        if (me.st.m > me.maxLen) me.maxLen = me.st.m;
        if (Array.isArray(m.eat) && m.eat.length) {
          const gone = [];
          for (const id of m.eat.slice(0, 200)) if (room.foods.delete(id)) { gone.push(id); room.exp.delete(id); }
          if (gone.length) bcast(room, { t: 'fr', f: gone }, ws);
        }
        break;
      case 'white': if (room.whites.delete(m.id)) bcast(room, { t: 'wr', id: m.id }, ws); break;
      case 'pu': if (room.pups.delete(m.id)) bcast(room, { t: 'pr', id: m.id }, ws); break;
      case 'item':
        if ((m.k === 'tgs' || m.k === 'gold') && room.items[m.k]) {
          room.items[m.k] = null; room.timers[m.k] = m.k === 'tgs' ? rnd(45, 75) : rnd(60, 90);
          bcast(room, { t: 'it', items: room.items });
        }
        break;
      case 'die': {
        if (me.st) me.st.f &= ~4;
        const killer = room.players.get(m.k), kb = !killer && room.bots.get(m.k);
        if (killer && (room.ffa || killer.team !== me.team)) killer.kills++;
        if (kb && kb.info.team !== me.team) kb.kills = (kb.kills || 0) + 1;
        bcast(room, { t: 'kill', v: me.id, k: killer ? killer.id : kb ? kb.info.id : null }, ws);
        dropFoods(room, m.drop, m.v, DROP_TTL);
        break;
      }
      case 'drop': dropFoods(room, m.drop, m.v); break;
      case 'bomb': bcast(room, { t: 'bomb', by: me.id, x: +m.x || 0, y: +m.y || 0 }, ws); break;
      case 'cut': bcast(room, { t: 'cut', by: me.id, v: m.v, x: +m.x || 0, y: +m.y || 0 }, ws); break;
      case 'frz': bcast(room, { t: 'frz', by: me.id, x: +m.x || 0, y: +m.y || 0 }, ws); break;
      case 'horn': { const now = Date.now(); if (now - (me.hornT || 0) > 2000) { me.hornT = now; bcast(room, { t: 'horn', by: me.id, k: clean(m.k, 10) }, ws); } break; }
      // ---- free-for-all: หัวหน้าห้องส่งข้อมูลรถไฟ AI ----
      case 'binfo':
        if (!(room.ffa || room.phase === 'play') || !me.host || !Array.isArray(m.b)) break;
        { const add = [];
          for (const b of m.b.slice(0, 40)) {
            const id = Math.round(+b.id); if (!(id < 0) || room.bots.size - (room.deadBots || 0) >= 60) continue;
            const info = { id, name: clean(b.name, 20), skin: Array.isArray(b.skin) ? b.skin.slice(0, 3).map(c => clean(c, 9)) : ['#ffffff', '#888888'],
              loco: clean(b.loco, 10), boss: !!b.boss, mhp: Math.max(0, Math.min(5000, b.mhp | 0)) };
            if (!room.ffa) info.team = b.team === 'B' ? 'B' : 'A';
            room.bots.set(id, { info, st: null }); add.push(info);
          }
          if (add.length) bcast(room, { t: 'binfo', b: add }, ws); }
        break;
      case 'bs':
        if (!(room.ffa || room.phase === 'play') || !me.host || !Array.isArray(m.b)) break;
        me.lastT = Date.now();
        { const ts = +m.ts || Date.now();
          for (const a of m.b.slice(0, 60)) { if (!Array.isArray(a)) continue; const b = room.bots.get(a[0]); if (b) { b.st = [a[0], +a[1] || 0, +a[2] || 0, +a[3] || 0, Math.min(5000, +a[4] || 0), a[5] | 0, ts]; if (b.st[4] > (b.maxLen || 0)) b.maxLen = b.st[4]; if (b.info.boss && a.length > 6) b.st.push(Math.max(0, +a[6] || 0)); } } }
        break;
      case 'bhit': {   // ผู้เล่นชนบอส → ส่งให้เครื่องหัวหน้าห้องที่คุมบอสอยู่คำนวณ
        if (!room.ffa) break;
        const host = [...room.players.values()].find(p => p.host);
        if (host && host !== me) send(host.ws, { t: 'bhit', id: m.id, d: Math.max(0, Math.min(60, +m.d || 0)), by: me.id });
        break;
      }
      case 'bdie': {
        const dead = room.bots.get(m.id);
        if (!me.host || !dead) break;
        if (room.ffa) room.bots.delete(m.id); else if (!dead.dead) { dead.st = null; dead.dead = true; room.deadBots = (room.deadBots || 0) + 1; }   // 2v2: เก็บบอทไว้นับแต้มตอนจบ แต่ไม่ส่งตำแหน่งแล้ว
        const killer = room.players.get(m.k), kb = !killer && room.bots.get(m.k);
        if (killer && (room.ffa || killer.team !== dead.info.team)) killer.kills++;
        if (kb && kb !== dead && kb.info.team !== dead.info.team) kb.kills = (kb.kills || 0) + 1;
        bcast(room, { t: 'kill', v: m.id, k: killer ? killer.id : kb ? kb.info.id : null }, ws);
        dropFoods(room, m.drop, m.v, DROP_TTL);
        break;
      }
    }
  });
  ws.on('close', () => {
    if (!room || !me) return;
    room.players.delete(me.id);
    bcast(room, { t: 'left', id: me.id });
    if (!room.players.size) { rooms.delete(room.key); return; }
    if (me.host) setHost(room, room.players.values().next().value); else lobby(room);
  });
});
function dropFoods(room, drop, v, ttl) {
  if (!Array.isArray(drop)) return;
  v = Math.max(.1, Math.min(20, +v || 1));
  const add = [];
  for (const d of drop.slice(0, 200)) if (Array.isArray(d)) add.push(newFood(room, +d[0] || 0, +d[1] || 0, v, ttl));
  if (add.length) bcast(room, { t: 'fa', f: add });
}

// ---------- game loop ----------
setInterval(() => {
  for (const room of rooms.values()) {
    if (room.phase !== 'play') continue;
    if (!room.ffa) room.timeLeft -= TICK;
    else {
      // หัวหน้าห้องเงียบไป (เช่น สลับแอปบนมือถือ) → ย้ายหัวหน้าให้คนที่ยังเล่นอยู่ เพื่อให้ AI ขยับต่อได้
      const now = Date.now(), host = [...room.players.values()].find(p => p.host);
      if (host && now - host.lastT > 4000) { const alt = [...room.players.values()].find(p => p !== host && now - p.lastT < 1500); if (alt) setHost(room, alt); }
    }
    // พลอยจากการตายที่หมดเวลา → ลบทิ้ง
    if (room.exp.size) { const now = Date.now(), gone = [];
      for (const [id, t] of room.exp) if (t <= now) { room.exp.delete(id); if (room.foods.delete(id)) gone.push(id); }
      if (gone.length) bcast(room, { t: 'fr', f: gone }); }
    // top up world
    const fa = [], cfg = room.cfg;
    for (let i = 0; i < 10 && room.foods.size < cfg.food; i++) fa.push(newFood(room));
    if (fa.length) bcast(room, { t: 'fa', f: fa });
    if (room.whites.size < cfg.white && Math.random() < .1) bcast(room, { t: 'wa', w: [newWhite(room)] });
    if (room.pups.size < cfg.pu && Math.random() < .03) bcast(room, { t: 'pa', p: [newPu(room)] });
    for (const k of ['tgs', 'gold']) {
      if (!room.items[k]) { room.timers[k] -= TICK; if (room.timers[k] <= 0) { room.items[k] = randIn(room, 300); bcast(room, { t: 'it', items: room.items }); } }
    }
    // states
    const p = [];
    for (const pl of room.players.values()) if (pl.st) p.push([pl.id, pl.st.x, pl.st.y, pl.st.a, pl.st.m, pl.st.f, pl.st.ts]);
    for (const b of room.bots.values()) if (b.st) p.push(b.st);
    bcast(room, { t: 's', p, tl: +room.timeLeft.toFixed(2), sc: teamScore(room) });
    if (!room.ffa && room.timeLeft <= 0) endMatch(room);
  }
}, TICK * 1000);

server.listen(PORT, () => console.log(`รถไฟซ่า.io server running → http://localhost:${PORT}`));
