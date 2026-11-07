// รถไฟซ่า — เซิร์ฟเวอร์: โหมดไม่จำกัดแบบ free-for-all (ทุกคนอยู่โลกเดียวกัน คนจริงเข้ามาแทนบอท) + ออนไลน์ 2v2
// รัน:  npm install  แล้ว  npm start   (ค่าเริ่มต้นพอร์ต 3000 หรือกำหนดด้วยตัวแปร PORT)
const http = require('http');
const fs = require('fs');
const path = require('path');
const { WebSocketServer } = require('ws');
const { handleApi } = require('./accounts');
const botsim = require('./botsim');   // บอทรันบนเซิร์ฟเวอร์

const PORT = process.env.PORT || 3000;
const R2 = 2200, RF = 3000;  // รัศมีสนาม: 2v2 / free-for-all
const CFG = { vs: { R: R2, food: 700, white: 40, pu: 10, max: 4 }, ffa: { R: RF, food: 1400, white: 60, pu: 16, max: 30 } };   // ออนไลน์: โลกละ 30 คน (ขาดเติมบอท)
const DIFFS = ['easy', 'normal', 'hard'];
const MATCH = +process.env.MATCH_SECS || 300;   // วินาทีต่อแมตช์
const SHRINK = Math.min(120, Math.round(MATCH * .4));   // วงเริ่มหดเมื่อเหลือกี่วินาที
const TEAM_MAX = 2;
const PU_KEYS = ['magnet', 'x3', 'speed', 'freeze'];
const TICK = 1 / 20;   // ส่งสถานะ 20 ครั้ง/วินาที

// ---------- เวอร์ชัน + รีเซ็ตตอนอัปเดต (เจ้าของสั่ง 7 พ.ย. 19:13) ----------
// Render: deploy ใหม่พร้อม → สลับคนเข้าใหม่ไปเครื่องใหม่ → 60 วิต่อมาส่ง SIGTERM ให้เครื่องเก่า (+ รอได้อีก 30 วิ)
// เครื่องเก่าคอยถามที่อยู่สาธารณะว่าเวอร์ชันเปลี่ยนหรือยัง → เปลี่ยนแล้วส่ง reset{s:60} ให้ทุกคน (นับถอยหลังบนจอ ครบแล้วออกจากเกม + โหลดเวอร์ชันใหม่)
const VERSION = (process.env.RENDER_GIT_COMMIT || process.env.APP_VERSION || require('crypto').createHash('sha1').update(fs.readFileSync(path.join(__dirname, 'public', 'index.html'))).update(fs.readFileSync(__filename)).digest('hex')).slice(0, 10);
const RESET_SECS = +process.env.RESET_SECS || 60;
const SELF_URL = (process.env.SELF_URL || process.env.RENDER_EXTERNAL_URL || '').replace(/\/$/, '');
let resetAt = 0;   // เวลา (ms) ที่จะรีเซ็ต · 0 = ยังไม่รีเซ็ต
function startReset(secs, why) {
  if (resetAt) return; resetAt = Date.now() + secs * 1000; console.log(`reset countdown ${secs}s (${why})`);
  const msg = JSON.stringify({ t: 'reset', s: secs });
  for (const ws of wss.clients) if (ws.readyState === 1) ws.send(msg);
  setTimeout(() => { console.log('reset: closing'); for (const ws of wss.clients) try { ws.close(4000, 'update'); } catch (e) {} setTimeout(() => process.exit(0), 1500).unref(); }, secs * 1000 + 3000);
}
function checkNewVersion() {
  if (resetAt || !SELF_URL) return;
  const req = (SELF_URL.startsWith('https') ? require('https') : http).get(SELF_URL + '/version?from=' + VERSION, { timeout: 4000 }, r => {
    let b = ''; r.on('data', d => b += d); r.on('end', () => { try { const v = JSON.parse(b).v; if (r.statusCode === 200 && v && v !== VERSION) startReset(RESET_SECS, 'new version ' + v); } catch (e) {} });
  });
  req.on('error', () => {}); req.on('timeout', () => req.destroy());
}
if (SELF_URL) setInterval(checkNewVersion, +process.env.VERSION_POLL_MS || 5000).unref();
if (process.env.RENDER || process.env.GRACEFUL) process.on('SIGTERM', () => { if (!resetAt) startReset(Math.min(RESET_SECS, 25), 'SIGTERM'); });   // เฉพาะบน Render (ในเครื่อง pkill แล้วปิดทันที)   // ไม่ได้ตรวจเจอก่อน (เช่น รีสตาร์ท) → แจ้งเท่าที่เวลาเหลือ

// ---------- static files ----------
const PUBLIC = path.join(__dirname, 'public');
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.json': 'application/json', '.webmanifest': 'application/manifest+json' };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent((req.url || '/').split('?')[0]);
  if (p === '/wsinfo') { res.writeHead(200, { 'Content-Type': 'application/json' }); return res.end(JSON.stringify({ deflate: !!DEFLATE, ...WSZ })); }
  if (p === '/version') { res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }); return res.end(JSON.stringify({ v: VERSION, reset: resetAt ? Math.max(0, Math.ceil((resetAt - Date.now()) / 1000)) : 0 })); }
  if (p === '/health') { res.writeHead(200, { 'Content-Type': 'text/plain' }); return res.end('ok'); }
  // ย้ายเซิร์ฟเวอร์: ตั้ง env REDIRECT_TO=https://ที่อยู่ใหม่ แล้วลิงก์เก่าจะพาไปที่ใหม่เอง (เก็บ ?w=โค้ดโลก ไว้ด้วย)
  if (process.env.REDIRECT_TO) { res.writeHead(301, { Location: process.env.REDIRECT_TO.replace(/\/$/, '') + (req.url || '/') }); return res.end(); }
  if (p.startsWith('/api/')) return handleApi(req, res, p);
  if (p === '/') p = '/index.html';
  const file = path.join(PUBLIC, path.normalize(p));
  if (!file.startsWith(PUBLIC)) { res.writeHead(403); return res.end(); }
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); return res.end('not found'); }
    const html = path.extname(file) === '.html';
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream', ...(html ? { 'Cache-Control': 'no-cache' } : {}) });
    res.end(html ? data.toString('utf8').replace(/__APP_VER__/g, VERSION) : data);
  });
});

// ---------- helpers ----------
const rooms = new Map();
let nextId = 1;
const rnd = (a, b) => a + Math.random() * (b - a);
const arena = room => !room.ffa && room.phase === 'play' && room.timeLeft < SHRINK ? room.cfg.R * (.3 + .7 * Math.max(0, room.timeLeft) / SHRINK) : room.cfg.R;
// พลอย/เพชรขาว: กระจุกกลางสนามมากกว่าขอบ (เจ้าของขอ) · r = u^0.8 → ครึ่งในของสนามได้ ~42% ของพลอย (เดิม 25%), ขอบนอก 20% ได้ ~24% (เดิม 36%)
const GEM_POW = 0.8;
function gemIn(room, m) { const a = Math.random() * Math.PI * 2, r = Math.pow(Math.random(), GEM_POW) * Math.max(50, arena(room) - m); return [Math.round(Math.cos(a) * r), Math.round(Math.sin(a) * r)]; }
function randIn(room, m) { const a = Math.random() * Math.PI * 2, r = Math.sqrt(Math.random()) * Math.max(50, arena(room) - m); return [Math.round(Math.cos(a) * r), Math.round(Math.sin(a) * r)]; }
function send(ws, o) { if (ws.readyState === 1) ws.send(JSON.stringify(o)); }
function bcast(room, o, except) { const s = JSON.stringify(o); for (const p of room.players.values()) if (p.ws !== except && p.ws.readyState === 1) p.ws.send(s); }
const clean = (s, n) => String(s || '').replace(/[<>&]/g, '').slice(0, n);

const DROP_TTL = 30;   // พลอยที่หล่นตอนตายอยู่ได้ 30 วินาที ถ้าไม่มีใครเก็บจะหายไป
// 💍📿 เครื่องประดับ (สีพลอย index 7/8/9) = พลอย 5 เม็ด — ต้องตรงกับ index.html
// 6% ของของที่เกิดเอง · รอบ ๆ เครื่องประดับ (JEWEL_CLEAR) ไม่มีพลอย · นับเป็นพลอย 5 เม็ดในเพดานจำนวนพลอย (foodWeight) → พลอยรวมน้อยลง
const JEWEL_V = 5, JEWEL_P = .06, JEWEL_CLEAR = 110;
const isJewel = f => f[4] >= 7;
const nearJewel = (room, x, y) => { for (const f of room.foods.values()) if (isJewel(f) && (f[1] - x) ** 2 + (f[2] - y) ** 2 < JEWEL_CLEAR * JEWEL_CLEAR) return true; return false; };
function foodWeight(room) { let n = 0; for (const f of room.foods.values()) n += isJewel(f) ? JEWEL_V : 1; return n; }
function newFood(room, x, y, v, ttl, gone) {
  let ci = (Math.random() * 7) | 0;
  if (x === undefined) {
    if (!v && Math.random() < JEWEL_P) { v = JEWEL_V; ci = 7 + ((Math.random() * 3) | 0); [x, y] = gemIn(room, 40);
      for (const f of room.foods.values()) if (!isJewel(f) && !room.exp.has(f[0]) && (f[1] - x) ** 2 + (f[2] - y) ** 2 < JEWEL_CLEAR * JEWEL_CLEAR) { room.foods.delete(f[0]); if (gone) gone.push(f[0]); } }   // เคลียร์พลอยรอบ ๆ
    else for (let k = 0; k < 6; k++) { [x, y] = gemIn(room, 40); if (!nearJewel(room, x, y)) break; } }
  const f = [room.nid++, Math.round(x), Math.round(y), Math.round((v || 1) * 100) / 100, ci];
  if (ttl) { f.push(ttl); room.exp.set(f[0], Date.now() + ttl * 1000); }
  room.foods.set(f[0], f); return f;
}
// ส่งอาหารให้คนที่เพิ่งเข้าห้อง: พลอยที่กำลังจะหายให้บอกเวลาที่เหลือจริง
const foodsNow = room => { const now = Date.now(); return [...room.foods.values()].map(f => f.length > 5 ? [f[0], f[1], f[2], f[3], f[4], Math.max(1, Math.round(((room.exp.get(f[0]) || now) - now) / 1000))] : f); };
function newWhite(room) { const [x, y] = gemIn(room, 60); const w = [room.nid++, x, y]; room.whites.set(w[0], w); return w; }
function newPu(room) { const [x, y] = randIn(room, 150); const p = [room.nid++, x, y, PU_KEYS[(Math.random() * PU_KEYS.length) | 0]]; room.pups.set(p[0], p); return p; }

function getRoom(code, ffa) {
  const key = (ffa ? 'F:' : 'V:') + code;
  let r = rooms.get(key);
  if (!r) {
    const cfg = ffa ? CFG.ffa : CFG.vs;
    r = { key, code, ffa, diff: 'normal', cfg, players: new Map(), foods: new Map(), whites: new Map(), pups: new Map(), items: { tgs: null, gold: null },
      timers: { tgs: 30, gold: 50 }, phase: ffa ? 'play' : 'lobby', timeLeft: MATCH, nid: 1, bots: new Map(), exp: new Map() };
    for (let w = 0; w < cfg.food;) w += isJewel(newFood(r)) ? JEWEL_V : 1;
    for (let i = 0; i < cfg.white; i++) newWhite(r);
    for (let i = 0; i < cfg.pu; i++) newPu(r);
    rooms.set(key, r);
  }
  return r;
}
const pubPlayers = room => [...room.players.values()].map(p => ({ id: p.id, name: p.name, team: p.team, host: p.host, skin: p.skin, loco: p.loco, smoke: p.smoke, wag: p.wag, kfx: p.kfx, title: p.title, rk: p.rk }));
const pubBots = room => [...room.bots.values()].map(b => b.info);
// บอททั้งหมดรันบนเซิร์ฟเวอร์ (botsim.js) — หัวหน้าห้องมีไว้กดเริ่มแมตช์ 2v2 เท่านั้น
function clearBots(room) { room.deadBots = 0; const had = room.bots.size; botsim.clear(room); if (had) bcast(room, { t: 'bclr' }); }
function setHost(room, p) { for (const q of room.players.values()) q.host = q === p; lobby(room); }
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
// บีบอัดข้อมูล (permessage-deflate): ข้อมูลต่อผู้เล่นลด ~65% (60 → 21 KB/วิ ที่ 30 คน) · ช้าลงไม่ถึง 3ms · เบราว์เซอร์ไม่รองรับ = ส่งแบบเดิมอัตโนมัติ
// ปิดได้ด้วย env WS_DEFLATE=0
const DEFLATE = process.env.WS_DEFLATE === '0' ? false : { threshold: 256, serverMaxWindowBits: 13, clientMaxWindowBits: 13, zlibDeflateOptions: { level: 3, memLevel: 7 } };
const wss = new WebSocketServer({ server, path: '/ws', maxPayload: 64 * 1024, perMessageDeflate: DEFLATE });
const WSZ = { offered: 0, negotiated: 0 };   // ตรวจว่าการบีบอัดใช้ได้จริงไหม (เปิดดู /wsinfo)
wss.on('connection', (ws, req) => {
  if (/permessage-deflate/.test(req.headers['sec-websocket-extensions'] || '')) WSZ.offered++;
  if (/permessage-deflate/.test(ws.extensions || '')) WSZ.negotiated++;
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
      me = { id: nextId++, ws, cz: !!m.cz, name: clean(m.name, 14) || 'ผู้เล่น', team: ffa ? null : nA <= room.players.size - nA ? 'A' : 'B',
        host: room.players.size === 0, skin: Array.isArray(m.skin) ? m.skin.slice(0, 3).map(c => clean(c, 9)) : ['#ffd23f', '#ff8c42'],
        loco: clean(m.loco, 10), smoke: clean(m.smoke, 10), wag: clean(m.wag, 10), kfx: clean(m.kfx, 10), title: clean(m.title, 24), rk: Math.max(0, Math.min(30, m.rk | 0)), kills: 0, maxLen: 20, st: null, lastT: Date.now() };
      room.players.set(me.id, me);
      send(ws, { t: 'welcome', id: me.id, R: room.cfg.R, mode: ffa ? 'ffa' : 'vs', code: room.code, diff: room.diff, shrink: SHRINK, phase: room.phase, timeLeft: room.timeLeft, players: pubPlayers(room),
        foods: foodsNow(room), whites: [...room.whites.values()], pups: [...room.pups.values()], items: room.items, bots: pubBots(room) });
      if (resetAt) send(ws, { t: 'reset', s: Math.max(1, Math.ceil((resetAt - Date.now()) / 1000)) });
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
          if (ps.length) startMatch(room);   // คนไม่ครบ → เซิร์ฟเวอร์เติมบอทให้ทีมที่ขาด
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
      case 'bomb': { const x = +m.x || 0, y = +m.y || 0; bcast(room, { t: 'bomb', by: me.id, x, y }, ws); botsim.onBomb(room, me, x, y); break; }
      case 'cut': { const x = +m.x || 0, y = +m.y || 0; if (m.v < 0) botsim.onCut(room, me, m.v, x, y); else bcast(room, { t: 'cut', by: me.id, v: m.v, x, y }, ws); break; }
      case 'frz': { const x = +m.x || 0, y = +m.y || 0; bcast(room, { t: 'frz', by: me.id, x, y }, ws); botsim.onFreeze(room, me, x, y); break; }
      case 'horn': { const now = Date.now(); const k = clean(m.k, 10); if (now - (me.hornT || 0) > (k === 'classic' ? 2000 : 7000)) { me.hornT = now; bcast(room, { t: 'horn', by: me.id, k }, ws); if (m.x !== undefined) botsim.onHorn(room, me, +m.x || 0, +m.y || 0, k); } break; }   // หวูดไล่บอท (ใช้ได้ทุก 8 วิ)
      // ---- ผลกับบอทบนเซิร์ฟเวอร์ ----
      case 'bhit': if (typeof m.id === 'number') botsim.onBossHit(room, me, m.id, m.d); break;
      // ---- คนชนคน: เครื่องเจ้าของลำตัวเห็นหัวผู้เล่นอื่นแตะลำตัวตัวเองบนจอ → ผู้เล่นนั้นตาย (ชดเชยดีเลย์ เหมือนบอท) ----
      // ตรวจว่าเป็นไปได้: ทั้งคู่ยังมีชีวิต, คนชนไม่ใช่ผี/อมตะ, ไม่ใช่ทีมเดียวกัน, หัวคนชนจริงอยู่ใกล้ลำตัวเรา ≤ 400px, กันซ้ำ 1.5 วิ
      case 'hitme': {
        const a = room.players.get(m.id), now = Date.now();
        if (!a || a === me || !a.st || !(a.st.f & 4) || (a.st.f & 48) || !me.st || !(me.st.f & 4) || (me.st.f & 32)) break;
        if (!room.ffa && a.team === me.team) break;
        if (now - (a.crashT || 0) < 1500) break;
        const b = me.body; let near = false;
        if (b) for (let i = 0; i < b.pts.length; i += 3) { const q = b.pts[i]; if ((q.x - a.st.x) ** 2 + (q.y - a.st.y) ** 2 < 400 * 400) { near = true; break; } }
        if (!near) break;
        a.crashT = now; send(a.ws, { t: 'crash', k: me.id }); break;
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
    // พลอยจากการตายที่หมดเวลา → ลบทิ้ง
    if (room.exp.size) { const now = Date.now(), gone = [];
      for (const [id, t] of room.exp) if (t <= now) { room.exp.delete(id); if (room.foods.delete(id)) gone.push(id); }
      if (gone.length) bcast(room, { t: 'fr', f: gone }); }
    // top up world
    const fa = [], cfg = room.cfg;
    const fgone = []; let fw = foodWeight(room);
    for (let i = 0; i < 10 && fw < cfg.food; i++) { const f = newFood(room, undefined, undefined, undefined, undefined, fgone); fa.push(f); fw += isJewel(f) ? JEWEL_V : 1; }
    if (fgone.length) bcast(room, { t: 'fr', f: fgone });
    if (fa.length) bcast(room, { t: 'fa', f: fa });
    if (room.whites.size < cfg.white && Math.random() < .1) bcast(room, { t: 'wa', w: [newWhite(room)] });
    if (room.pups.size < cfg.pu && Math.random() < .03) bcast(room, { t: 'pa', p: [newPu(room)] });
    for (const k of ['tgs', 'gold']) {
      if (!room.items[k]) { room.timers[k] -= TICK; if (room.timers[k] <= 0) { room.items[k] = randIn(room, 300); bcast(room, { t: 'it', items: room.items }); } }
    }
    // บอท: คิด + ขยับ + ชน + กิน บนเซิร์ฟเวอร์
    botsim.step(room, TICK, bcast, dropFoods);
    // states
    // ส่งแบบย่อ (cz) ให้เครื่องที่รองรับ: เวลาเป็นส่วนต่างจาก T, id บอทสั้นลง (−(1e8+k) → −(k+1)) · Render ตัด permessage-deflate ทิ้ง เลยย่อเองแทน
    const p = [], pc = [], T = Date.now(), tl = +room.timeLeft.toFixed(2), sc = teamScore(room);
    for (const pl of room.players.values()) if (pl.st) { const s = pl.st; p.push([pl.id, s.x, s.y, s.a, s.m, s.f, s.ts]); pc.push([pl.id, s.x, s.y, +(+s.a).toFixed(2), s.m, s.f, s.ts - T]); }
    for (const b of room.bots.values()) if (b.st && b.alive) { p.push(b.st); const r = [b.st[0] + 1e8 - 1, b.st[1], b.st[2], b.st[3], b.st[4], b.st[5], b.st[6] - T]; if (b.st.length > 7) r.push(b.st[7]); pc.push(r); }
    let sL = null, sC = null;
    for (const pl of room.players.values()) if (pl.ws.readyState === 1) pl.ws.send(pl.cz ? (sC || (sC = JSON.stringify({ t: 's', p: pc, T, tl, sc }))) : (sL || (sL = JSON.stringify({ t: 's', p, tl, sc }))));
    if (!room.ffa && room.timeLeft <= 0) endMatch(room);
  }
}, TICK * 1000);

server.listen(PORT, () => console.log(`รถไฟซ่า server running → http://localhost:${PORT}`));
