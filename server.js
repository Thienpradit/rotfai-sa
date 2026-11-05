// รถไฟซ่า.io — เซิร์ฟเวอร์โหมดออนไลน์ 2v2 + โหมดเล่นกับเพื่อน (co-op เข้ามาจอยได้ตลอด)
// รัน:  npm install  แล้ว  npm start   (ค่าเริ่มต้นพอร์ต 3000 หรือกำหนดด้วยตัวแปร PORT)
const http = require('http');
const fs = require('fs');
const path = require('path');
const { WebSocketServer } = require('ws');

const PORT = process.env.PORT || 3000;
const R2 = 2200, RC = 3000;  // รัศมีสนาม: 2v2 / เล่นกับเพื่อน
const CFG = { vs: { R: R2, food: 700, white: 40, pu: 10, max: 4 }, coop: { R: RC, food: 1200, white: 50, pu: 14, max: 8 } };
const MATCH = +process.env.MATCH_SECS || 300;   // วินาทีต่อแมตช์
const SHRINK = Math.min(120, Math.round(MATCH * .4));   // วงเริ่มหดเมื่อเหลือกี่วินาที
const TEAM_MAX = 2;
const PU_KEYS = ['magnet', 'x3', 'speed', 'freeze'];
const TICK = 1 / 15;

// ---------- static files ----------
const PUBLIC = path.join(__dirname, 'public');
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent((req.url || '/').split('?')[0]);
  if (p === '/health') { res.writeHead(200, { 'Content-Type': 'text/plain' }); return res.end('ok'); }
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
const arena = room => !room.coop && room.phase === 'play' && room.timeLeft < SHRINK ? room.cfg.R * (.3 + .7 * Math.max(0, room.timeLeft) / SHRINK) : room.cfg.R;
function randIn(room, m) { const a = Math.random() * Math.PI * 2, r = Math.sqrt(Math.random()) * Math.max(50, arena(room) - m); return [Math.round(Math.cos(a) * r), Math.round(Math.sin(a) * r)]; }
function send(ws, o) { if (ws.readyState === 1) ws.send(JSON.stringify(o)); }
function bcast(room, o, except) { const s = JSON.stringify(o); for (const p of room.players.values()) if (p.ws !== except && p.ws.readyState === 1) p.ws.send(s); }
const clean = (s, n) => String(s || '').replace(/[<>&]/g, '').slice(0, n);

function newFood(room, x, y, v) {
  if (x === undefined) [x, y] = randIn(room, 40);
  const f = [room.nid++, Math.round(x), Math.round(y), Math.round((v || 1) * 100) / 100, (Math.random() * 7) | 0];
  room.foods.set(f[0], f); return f;
}
function newWhite(room) { const [x, y] = randIn(room, 60); const w = [room.nid++, x, y]; room.whites.set(w[0], w); return w; }
function newPu(room) { const [x, y] = randIn(room, 150); const p = [room.nid++, x, y, PU_KEYS[(Math.random() * PU_KEYS.length) | 0]]; room.pups.set(p[0], p); return p; }

function getRoom(code, coop) {
  const key = (coop ? 'C:' : 'V:') + code;
  let r = rooms.get(key);
  if (!r) {
    const cfg = coop ? CFG.coop : CFG.vs;
    r = { key, code, coop, cfg, players: new Map(), foods: new Map(), whites: new Map(), pups: new Map(), items: { tgs: null, gold: null },
      timers: { tgs: 30, gold: 50 }, phase: coop ? 'play' : 'lobby', timeLeft: MATCH, nid: 1, bots: new Map() };
    for (let i = 0; i < cfg.food; i++) newFood(r);
    for (let i = 0; i < cfg.white; i++) newWhite(r);
    for (let i = 0; i < cfg.pu; i++) newPu(r);
    rooms.set(key, r);
  }
  return r;
}
const pubPlayers = room => [...room.players.values()].map(p => ({ id: p.id, name: p.name, team: p.team, host: p.host, skin: p.skin, loco: p.loco, smoke: p.smoke, rk: p.rk }));
const pubBots = room => [...room.bots.values()].map(b => b.info);
// co-op: รถไฟ AI ทั้งหมดรันอยู่ในเครื่องหัวหน้าห้อง ถ้าหัวหน้าเปลี่ยน ต้องล้าง AI ชุดเก่าทิ้ง
function clearBots(room) { if (!room.bots.size) return; room.bots.clear(); bcast(room, { t: 'bclr' }); }
function setHost(room, p) { for (const q of room.players.values()) q.host = q === p; clearBots(room); lobby(room); }
const lobby = room => bcast(room, { t: 'lobby', players: pubPlayers(room), phase: room.phase });
function teamScore(room) {
  const sc = { A: { k: 0, l: 0 }, B: { k: 0, l: 0 } };
  for (const p of room.players.values()) { sc[p.team].k += p.kills; if (p.st && p.st.f & 4) sc[p.team].l += p.st.m; }
  return sc;
}

// ---------- match flow ----------
function startMatch(room) {
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
  bcast(room, { t: 'end', winner: A > B ? 'A' : B > A ? 'B' : 'draw', A, B, mvp,
    players: ps.map(p => ({ id: p.id, name: p.name, team: p.team, kills: p.kills, maxLen: p.maxLen })) });
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
      const code = clean(m.room, 8).toUpperCase() || 'PUBLIC', coop = m.mode === 'coop';
      room = getRoom(code, coop);
      if (room.players.size >= room.cfg.max) { send(ws, { t: 'err', msg: `ห้องนี้เต็มแล้ว (${room.cfg.max} คน) ลองรหัสห้องอื่น` }); room = null; return; }
      const nA = [...room.players.values()].filter(p => p.team === 'A').length;
      me = { id: nextId++, ws, name: clean(m.name, 14) || 'ผู้เล่น', team: coop || nA <= room.players.size - nA ? 'A' : 'B',
        host: room.players.size === 0, skin: Array.isArray(m.skin) ? m.skin.slice(0, 3).map(c => clean(c, 9)) : ['#ffd23f', '#ff8c42'],
        loco: clean(m.loco, 10), smoke: clean(m.smoke, 10), rk: Math.max(0, Math.min(30, m.rk | 0)), kills: 0, maxLen: 20, st: null, lastT: Date.now() };
      room.players.set(me.id, me);
      send(ws, { t: 'welcome', id: me.id, R: room.cfg.R, coop, shrink: SHRINK, phase: room.phase, timeLeft: room.timeLeft, players: pubPlayers(room),
        foods: [...room.foods.values()], whites: [...room.whites.values()], pups: [...room.pups.values()], items: room.items, bots: pubBots(room) });
      lobby(room);
      return;
    }
    switch (m.t) {
      case 'team':
        if (room.coop || room.phase !== 'lobby') break;
        { const want = m.k === 'A' || m.k === 'B' ? m.k : me.team === 'A' ? 'B' : 'A';
          if (want !== me.team && [...room.players.values()].filter(p => p.team === want).length < TEAM_MAX) { me.team = want; lobby(room); } }
        break;
      case 'start':
        if (!room.coop && me.host && room.phase === 'lobby') {
          const ps = [...room.players.values()];
          if (ps.some(p => p.team === 'A') && ps.some(p => p.team === 'B')) startMatch(room);
        }
        break;
      case 'st':
        me.lastT = Date.now();
        me.st = { x: +m.x || 0, y: +m.y || 0, a: +m.a || 0, m: Math.min(5000, +m.m || 0), f: m.f | 0 };
        if (me.st.m > me.maxLen) me.maxLen = me.st.m;
        if (Array.isArray(m.eat) && m.eat.length) {
          const gone = [];
          for (const id of m.eat.slice(0, 200)) if (room.foods.delete(id)) gone.push(id);
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
        const killer = room.players.get(m.k);
        if (killer && killer.team !== me.team) killer.kills++;
        bcast(room, { t: 'kill', v: me.id, k: killer ? killer.id : null }, ws);
        dropFoods(room, m.drop, m.v);
        break;
      }
      case 'drop': dropFoods(room, m.drop, m.v); break;
      case 'bomb': bcast(room, { t: 'bomb', by: me.id, x: +m.x || 0, y: +m.y || 0 }, ws); break;
      case 'cut': bcast(room, { t: 'cut', by: me.id, v: m.v, x: +m.x || 0, y: +m.y || 0 }, ws); break;
      case 'frz': bcast(room, { t: 'frz', by: me.id, x: +m.x || 0, y: +m.y || 0 }, ws); break;
      // ---- co-op: หัวหน้าห้องส่งข้อมูลรถไฟ AI ----
      case 'binfo':
        if (!room.coop || !me.host || !Array.isArray(m.b)) break;
        { const add = [];
          for (const b of m.b.slice(0, 40)) {
            const id = Math.round(+b.id); if (!(id < 0) || room.bots.size >= 60) continue;
            const info = { id, name: clean(b.name, 20), skin: Array.isArray(b.skin) ? b.skin.slice(0, 3).map(c => clean(c, 9)) : ['#ffffff', '#888888'],
              loco: clean(b.loco, 10), boss: !!b.boss };
            room.bots.set(id, { info, st: null }); add.push(info);
          }
          if (add.length) bcast(room, { t: 'binfo', b: add }, ws); }
        break;
      case 'bs':
        if (!room.coop || !me.host || !Array.isArray(m.b)) break;
        me.lastT = Date.now();
        for (const a of m.b.slice(0, 60)) { if (!Array.isArray(a)) continue; const b = room.bots.get(a[0]); if (b) b.st = [a[0], +a[1] || 0, +a[2] || 0, +a[3] || 0, Math.min(5000, +a[4] || 0), a[5] | 0]; }
        break;
      case 'bdie': {
        if (!room.coop || !me.host || !room.bots.delete(m.id)) break;
        const killer = room.players.get(m.k);
        if (killer) killer.kills++;
        bcast(room, { t: 'kill', v: m.id, k: killer ? killer.id : null }, ws);
        dropFoods(room, m.drop, m.v);
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
function dropFoods(room, drop, v) {
  if (!Array.isArray(drop)) return;
  v = Math.max(.1, Math.min(20, +v || 1));
  const add = [];
  for (const d of drop.slice(0, 200)) if (Array.isArray(d)) add.push(newFood(room, +d[0] || 0, +d[1] || 0, v));
  if (add.length) bcast(room, { t: 'fa', f: add });
}

// ---------- game loop ----------
setInterval(() => {
  for (const room of rooms.values()) {
    if (room.phase !== 'play') continue;
    if (!room.coop) room.timeLeft -= TICK;
    else {
      // หัวหน้าห้องเงียบไป (เช่น สลับแอปบนมือถือ) → ย้ายหัวหน้าให้คนที่ยังเล่นอยู่ เพื่อให้ AI ขยับต่อได้
      const now = Date.now(), host = [...room.players.values()].find(p => p.host);
      if (host && now - host.lastT > 4000) { const alt = [...room.players.values()].find(p => p !== host && now - p.lastT < 1500); if (alt) setHost(room, alt); }
    }
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
    for (const pl of room.players.values()) if (pl.st) p.push([pl.id, pl.st.x, pl.st.y, pl.st.a, pl.st.m, pl.st.f]);
    for (const b of room.bots.values()) if (b.st) p.push(b.st);
    bcast(room, { t: 's', p, tl: +room.timeLeft.toFixed(2), sc: teamScore(room) });
    if (!room.coop && room.timeLeft <= 0) endMatch(room);
  }
}, TICK * 1000);

server.listen(PORT, () => console.log(`รถไฟซ่า.io server running → http://localhost:${PORT}`));
