// รถไฟซ่า.io — เซิร์ฟเวอร์โหมดออนไลน์ 2v2
// รัน:  npm install  แล้ว  npm start   (ค่าเริ่มต้นพอร์ต 3000 หรือกำหนดด้วยตัวแปร PORT)
const http = require('http');
const fs = require('fs');
const path = require('path');
const { WebSocketServer } = require('ws');

const PORT = process.env.PORT || 3000;
const R = 2200;            // รัศมีสนามออนไลน์
const FOOD_N = 700, WHITE_N = 40, PU_N = 10;
const MATCH = +process.env.MATCH_SECS || 300;   // วินาทีต่อแมตช์
const SHRINK = Math.min(120, Math.round(MATCH * .4));   // วงเริ่มหดเมื่อเหลือกี่วินาที
const MAX_PLAYERS = 4, TEAM_MAX = 2;
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
const arena = room => room.phase === 'play' && room.timeLeft < SHRINK ? R * (.3 + .7 * Math.max(0, room.timeLeft) / SHRINK) : R;
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

function getRoom(code) {
  let r = rooms.get(code);
  if (!r) {
    r = { code, players: new Map(), foods: new Map(), whites: new Map(), pups: new Map(), items: { tgs: null, gold: null },
      timers: { tgs: 30, gold: 50 }, phase: 'lobby', timeLeft: MATCH, nid: 1 };
    for (let i = 0; i < FOOD_N; i++) newFood(r);
    for (let i = 0; i < WHITE_N; i++) newWhite(r);
    for (let i = 0; i < PU_N; i++) newPu(r);
    rooms.set(code, r);
  }
  return r;
}
const pubPlayers = room => [...room.players.values()].map(p => ({ id: p.id, name: p.name, team: p.team, host: p.host, skin: p.skin, loco: p.loco, smoke: p.smoke }));
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
    spawns[p.id] = [Math.round(Math.cos(a) * R * .55), Math.round(Math.sin(a) * R * .55), +(side + Math.PI).toFixed(2)];
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
      const code = clean(m.room, 8).toUpperCase() || 'PUBLIC';
      room = getRoom(code);
      if (room.players.size >= MAX_PLAYERS) { send(ws, { t: 'err', msg: 'ห้องนี้เต็มแล้ว (4 คน) ลองรหัสห้องอื่น' }); room = null; return; }
      const nA = [...room.players.values()].filter(p => p.team === 'A').length;
      me = { id: nextId++, ws, name: clean(m.name, 14) || 'ผู้เล่น', team: nA <= room.players.size - nA ? 'A' : 'B',
        host: room.players.size === 0, skin: Array.isArray(m.skin) ? m.skin.slice(0, 3).map(c => clean(c, 9)) : ['#ffd23f', '#ff8c42'],
        loco: clean(m.loco, 10), smoke: clean(m.smoke, 10), kills: 0, maxLen: 20, st: null };
      room.players.set(me.id, me);
      send(ws, { t: 'welcome', id: me.id, R, shrink: SHRINK, phase: room.phase, timeLeft: room.timeLeft, players: pubPlayers(room),
        foods: [...room.foods.values()], whites: [...room.whites.values()], pups: [...room.pups.values()], items: room.items });
      lobby(room);
      return;
    }
    switch (m.t) {
      case 'team':
        if (room.phase !== 'lobby') break;
        { const other = me.team === 'A' ? 'B' : 'A';
          if ([...room.players.values()].filter(p => p.team === other).length < TEAM_MAX) { me.team = other; lobby(room); } }
        break;
      case 'start':
        if (me.host && room.phase === 'lobby') {
          const ps = [...room.players.values()];
          if (ps.some(p => p.team === 'A') && ps.some(p => p.team === 'B')) startMatch(room);
        }
        break;
      case 'st':
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
    }
  });
  ws.on('close', () => {
    if (!room || !me) return;
    room.players.delete(me.id);
    bcast(room, { t: 'left', id: me.id });
    if (!room.players.size) { rooms.delete(room.code); return; }
    if (me.host) { const n = room.players.values().next().value; n.host = true; }
    lobby(room);
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
    room.timeLeft -= TICK;
    // top up world
    const fa = [];
    for (let i = 0; i < 10 && room.foods.size < FOOD_N; i++) fa.push(newFood(room));
    if (fa.length) bcast(room, { t: 'fa', f: fa });
    if (room.whites.size < WHITE_N && Math.random() < .1) bcast(room, { t: 'wa', w: [newWhite(room)] });
    if (room.pups.size < PU_N && Math.random() < .03) bcast(room, { t: 'pa', p: [newPu(room)] });
    for (const k of ['tgs', 'gold']) {
      if (!room.items[k]) { room.timers[k] -= TICK; if (room.timers[k] <= 0) { room.items[k] = randIn(room, 300); bcast(room, { t: 'it', items: room.items }); } }
    }
    // states
    const p = [];
    for (const pl of room.players.values()) if (pl.st) p.push([pl.id, pl.st.x, pl.st.y, pl.st.a, pl.st.m, pl.st.f]);
    bcast(room, { t: 's', p, tl: +room.timeLeft.toFixed(2), sc: teamScore(room) });
    if (room.timeLeft <= 0) endMatch(room);
  }
}, TICK * 1000);

server.listen(PORT, () => console.log(`รถไฟซ่า.io server running → http://localhost:${PORT}`));
