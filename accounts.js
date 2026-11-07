// รถไฟซ่า — ระบบบัญชีผู้เล่น (ลงทะเบียน / เข้าสู่ระบบ / บันทึกเหรียญ-แรงก์ / ตารางอันดับ)
// มี DATABASE_URL (Postgres เช่น Neon) → เก็บในฐานข้อมูล · ไม่มี → เก็บในไฟล์ data/users.json (ไว้ทดสอบในเครื่องเท่านั้น)
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const DB_URL = process.env.DATABASE_URL || '';
const SECRET = process.env.TOKEN_SECRET || crypto.createHash('sha256').update('rotfai:' + (DB_URL || 'dev-secret')).digest('hex');
const MAX_DATA = 40 * 1024;
const AC = require('./anticheat');

// ---------- storage ----------
let store;
function fileStore(note) {
  const FILE = path.join(__dirname, 'data', 'users.json');
  let db = {}; try { db = JSON.parse(fs.readFileSync(FILE, 'utf8')); } catch (e) {}
  const SFILE = path.join(__dirname, 'data', 'seasons.json'); let seasons = {}; try { seasons = JSON.parse(fs.readFileSync(SFILE, 'utf8')); } catch (e) {}
  let t = null; const flush = () => { clearTimeout(t); t = setTimeout(() => { fs.mkdirSync(path.dirname(FILE), { recursive: true }); fs.writeFileSync(FILE, JSON.stringify(db)); }, 300); };
  console.log('accounts: ' + note);
  return {
    kind: 'file', note, ready: Promise.resolve(),
    async get(l) { return db[l] || null; },
    async create(u) { if (db[u.lname]) return false; db[u.lname] = u; flush(); return true; },
    async save(l, data, rp) { if (db[l]) { db[l].data = data; db[l].rp = rp; db[l].updated = Date.now(); flush(); } },
    async setAuth(l, salt, hash) { if (db[l]) { db[l].salt = salt; db[l].hash = hash; flush(); } },
    async setRecovery(l, rhash) { if (db[l]) { db[l].rhash = rhash; flush(); } },
    async top(n, season, by, me) {   // by: rp (ฤดูกาลนี้) / len (ยาวสุดตลอดกาล) / coins (เหรียญที่มีตอนนี้)
      const all = Object.values(db).filter(u => by !== 'rp' || (u.data || {}).season === season).map(u => ({ name: u.name, lname: u.lname, val: LB_VAL[by](u), rp: +u.rp || 0, tid: ((u.data || {}).eq || {}).title || '' })).filter(u => u.val > 0).sort((a, b) => b.val - a.val);
      const i = me ? all.findIndex(u => u.lname === me) : -1;
      return { top: all.slice(0, n).map(({ lname, ...u }) => u), me: i >= 0 ? { pos: i + 1, val: all[i].val } : null, n: all.length }; },
    async getSeason(k) { return seasons[k] || null; },
    async migrateOnline() { let n = 0; for (const u of Object.values(db)) if ((u.data || {}).onv !== 2) { u.data = AC.seedOnline(u.data); n++; } if (n) flush(); return n; },
    async snapSeason(k) { if (seasons[k]) return seasons[k];   // ภาพนิ่งอันดับตอนจบฤดูกาล (ทำครั้งเดียว)
      const all = Object.values(db).filter(u => (u.data || {}).season === k && LB_VAL.rp(u) > 0).sort((a, b) => LB_VAL.rp(b) - LB_VAL.rp(a) || (a.updated || 0) - (b.updated || 0)), ranks = {};
      all.forEach((u, i) => { ranks[u.lname] = [i + 1, LB_VAL.rp(u)]; });
      seasons[k] = { n: all.length, ranks }; fs.mkdirSync(path.dirname(SFILE), { recursive: true }); fs.writeFileSync(SFILE, JSON.stringify(seasons)); return seasons[k]; },
  };
}
// บอกลักษณะของ DATABASE_URL แบบไม่เปิดเผยรหัสผ่าน (ไว้เช็คว่าค่าที่ใส่ใน Render ตรงกับของ Neon ไหม)
function describeUrl(u) {
  try { const x = new URL(u); const pw = decodeURIComponent(x.password);
    return `user=${x.username} host=${x.hostname} db=${x.pathname.slice(1)} passLen=${pw.length} passSha=${crypto.createHash('sha256').update(pw).digest('hex').slice(0, 8)}`;
  } catch (e) { return 'unparseable DATABASE_URL (len ' + u.length + ')'; }
}
if (DB_URL) {
  const { Pool } = require('pg');
  const url = DB_URL.trim().replace(/[?&]channel_binding=[^&]*/, '').replace(/\?&/, '?');
  const pool = new Pool({ connectionString: url, ssl: /localhost|127\.0\.0\.1/.test(url) ? false : { rejectUnauthorized: false }, max: 5 });
  pool.on('error', e => console.error('accounts: pool error', e.message));
  let dbStore = null;
  const ready = pool.query(`CREATE TABLE IF NOT EXISTS players (
      lname TEXT PRIMARY KEY, name TEXT NOT NULL, salt TEXT NOT NULL, hash TEXT NOT NULL,
      data JSONB NOT NULL DEFAULT '{}', rp INTEGER NOT NULL DEFAULT 0,
      created TIMESTAMPTZ NOT NULL DEFAULT now(), updated TIMESTAMPTZ NOT NULL DEFAULT now())`)
    .then(() => pool.query('CREATE INDEX IF NOT EXISTS players_rp ON players (rp DESC)'))
    .then(() => pool.query('ALTER TABLE players ADD COLUMN IF NOT EXISTS rhash TEXT'))
    .then(() => pool.query(`CREATE TABLE IF NOT EXISTS seasons (key TEXT PRIMARY KEY, n INTEGER NOT NULL, ranks JSONB NOT NULL, created TIMESTAMPTZ NOT NULL DEFAULT now())`))
    .then(() => { console.log('accounts: using Postgres (' + describeUrl(url) + ')'); })
    .catch(e => {   // ต่อฐานข้อมูลไม่ได้ → ไม่ให้เซิร์ฟเวอร์ล่ม ใช้ไฟล์ชั่วคราวแทน
      console.error('accounts: database error ' + e.message + ' | ' + describeUrl(url));
      store = fileStore('DATABASE FAILED → temporary file store (fix DATABASE_URL)'); store.dbError = e.message;
    });
  dbStore = {
    kind: 'db', ready,
    async get(l) { await ready; if (store !== dbStore) return store.get(l); const r = await pool.query('SELECT * FROM players WHERE lname=$1', [l]); return r.rows[0] || null; },
    async create(u) { await ready; if (store !== dbStore) return store.create(u); const r = await pool.query('INSERT INTO players (lname,name,salt,hash,data,rp) VALUES ($1,$2,$3,$4,$5,$6) ON CONFLICT DO NOTHING RETURNING lname', [u.lname, u.name, u.salt, u.hash, u.data, u.rp]); return r.rowCount === 1; },
    async save(l, data, rp) { await ready; if (store !== dbStore) return store.save(l, data, rp); await pool.query('UPDATE players SET data=$2, rp=$3, updated=now() WHERE lname=$1', [l, data, rp]); },
    async setAuth(l, salt, hash) { await ready; if (store !== dbStore) return store.setAuth(l, salt, hash); await pool.query('UPDATE players SET salt=$2, hash=$3 WHERE lname=$1', [l, salt, hash]); },
    async setRecovery(l, rhash) { await ready; if (store !== dbStore) return store.setRecovery(l, rhash); await pool.query('UPDATE players SET rhash=$2 WHERE lname=$1', [l, rhash]); },
    async top(n, season, by, me) { await ready; if (store !== dbStore) return store.top(n, season, by, me);
      const ex = LB_SQL[by], w = by === 'rp' ? "data->>'season'=$1 AND " : '$1::text IS NOT NULL AND ';
      const r = await pool.query(`SELECT name, rp, ${ex} AS val, COALESCE(data->'eq'->>'title','') AS tid FROM players WHERE ${w}${ex} > 0 ORDER BY val DESC, updated ASC LIMIT $2`, [season, n]);
      let mine = null;
      if (me) { const q = await pool.query(`SELECT ${ex} AS val FROM players WHERE lname=$1 AND (${by !== 'rp'} OR data->>'season'=$2)`, [me, season]); const v = q.rows[0] ? +q.rows[0].val : 0;
        if (v > 0) { const c = await pool.query(`SELECT count(*)::int AS n FROM players WHERE ${w}${ex} > $2`, [season, v]); mine = { pos: c.rows[0].n + 1, val: v }; } }
      const cn = await pool.query(`SELECT count(*)::int AS n FROM players WHERE ${w}${ex} > 0`, [season]);
      return { top: r.rows.map(x => ({ name: x.name, val: +x.val, rp: +x.rp || 0, tid: x.tid })), me: mine, n: cn.rows[0].n }; },
    async migrateOnline() { await ready; if (store !== dbStore) return store.migrateOnline();
      const r = await pool.query("SELECT lname, data FROM players WHERE COALESCE(data->>'onv','') <> '2'"); for (const u of r.rows) await pool.query("UPDATE players SET data=$2 WHERE lname=$1 AND COALESCE(data->>'onv','') <> '2'", [u.lname, AC.seedOnline(u.data)]); return r.rows.length; },
    async getSeason(k) { await ready; if (store !== dbStore) return store.getSeason(k); const r = await pool.query('SELECT n, ranks FROM seasons WHERE key=$1', [k]); return r.rows[0] || null; },
    async snapSeason(k) { await ready; if (store !== dbStore) return store.snapSeason(k);   // ภาพนิ่งอันดับตอนจบฤดูกาล (ทำครั้งเดียว)
      const have = await this.getSeason(k); if (have) return have;
      const r = await pool.query(`SELECT lname, ${LB_SQL.rp} AS v FROM players WHERE data->>'season'=$1 AND ${LB_SQL.rp} > 0 ORDER BY v DESC, updated ASC`, [k]), ranks = {};
      r.rows.forEach((u, i) => { ranks[u.lname] = [i + 1, +u.v || 0]; });
      await pool.query('INSERT INTO seasons (key, n, ranks) VALUES ($1,$2,$3) ON CONFLICT DO NOTHING', [k, r.rows.length, ranks]);
      return this.getSeason(k); },
  };
  store = dbStore;
} else {
  store = fileStore('no DATABASE_URL → using local file (test only, data is lost when the server restarts on Render)');
}

// บน Render (มีตัวแปร RENDER) ถ้าไม่ได้ต่อฐานข้อมูล → ปิดลงทะเบียน/เข้าสู่ระบบ ไม่ให้บัญชีไปอยู่ในไฟล์ชั่วคราวแล้วหายตอนเซิร์ฟเวอร์รีสตาร์ท
const LIVE = !!process.env.RENDER && !process.env.ALLOW_FILE_STORE;
const accountsDown = () => LIVE && store.kind === 'file';

// ตารางอันดับ 3 แบบ: rp = แรงก์ฤดูกาลนี้, len = ความยาวสูงสุดตลอดกาล, coins = เหรียญที่มีตอนนี้
// ตารางอันดับนับเฉพาะโหมดออนไลน์ (เจ้าของสั่ง 7 พ.ย. 18:45): onrp / st.okills / st.omaxLen (ดู AC.seedOnline)
const LB_VAL = { rp: u => Math.floor(+(u.data || {}).onrp || 0), len: u => Math.floor(+((u.data || {}).st || {}).omaxLen || 0), coins: u => Math.floor(+(u.data || {}).coins || 0), kills: u => Math.floor(+((u.data || {}).st || {}).okills || 0) };
// โปรไฟล์สาธารณะของผู้เล่น (แตะชื่อในตารางอันดับ) — ส่งเฉพาะสถิติ ไม่ส่งข้อมูลส่วนตัว
const PUB_ST = ['kills', 'boss', 'maxLen', 'games', 'teamWin', 'vsGames', 'killsGame', 'jewels', 'stations'];
function pubProfile(u) { const d = u.data || {}, st = d.st || {}, o = {}; for (const k of PUB_ST) o[k] = Math.floor(+st[k] || 0);
  return { name: u.name, rp: +u.rp || 0, season: d.season || '', tid: (d.eq || {}).title || '', loco: (d.eq || {}).loco || '', ach: Object.keys(d.ach || {}).length, st: o }; }
const LB_SQL = { rp: "floor(COALESCE((data->>'onrp')::float,0))", len: "floor(COALESCE((data->'st'->>'omaxLen')::float,0))", coins: "floor(COALESCE((data->>'coins')::float,0))", kills: "floor(COALESCE((data->'st'->>'okills')::float,0))" };

// ---------- helpers ----------
const b64u = s => Buffer.from(s, 'utf8').toString('base64url');
const unb64u = s => { try { return Buffer.from(s, 'base64url').toString('utf8'); } catch (e) { return ''; } };
const sign = (l, salt) => crypto.createHmac('sha256', SECRET).update(l + ':' + salt).digest('base64url');
const makeToken = u => b64u(u.lname) + '.' + sign(u.lname, u.salt);
const hashPass = (pass, salt) => new Promise((ok, no) => crypto.scrypt(pass, salt, 32, (e, k) => e ? no(e) : ok(k.toString('hex'))));
const lower = n => n.normalize('NFC').toLowerCase();
function cleanName(n) { return String(n || '').normalize('NFC').replace(/[<>&"'`\\]/g, '').replace(/\s+/g, ' ').trim(); }
function cleanData(d) {
  if (!d || typeof d !== 'object' || Array.isArray(d)) return {};
  const s = JSON.stringify(d); if (s.length > MAX_DATA) return null;
  return JSON.parse(s);
}
const rpOf = d => Math.max(0, Math.min(1e7, Math.floor(+d.rp || 0)));
// รหัสกู้คืน: เก็บแค่ค่า hash (มี salt ของตัวเอง แยกจากรหัสผ่าน)
function makeRecovery() { const code = AC.newRecovery(), rs = crypto.randomBytes(8).toString('hex'); return { code, rhash: rs + '$' + AC.hashRecovery(code, rs) }; }
function checkRecovery(rhash, code) { const [rs, h] = String(rhash || '').split('$'); if (!rs || !h) return false;
  const a = Buffer.from(h), b = Buffer.from(AC.hashRecovery(code, rs)); return a.length === b.length && crypto.timingSafeEqual(a, b); }
const passOk = p => p.length >= 4 && p.length <= 64;
async function authUser(req) {
  const h = req.headers.authorization || ''; const tok = h.startsWith('Bearer ') ? h.slice(7) : '';
  const [a, sig] = tok.split('.'); if (!a || !sig) return null;
  const u = await store.get(unb64u(a)); if (!u) return null;
  const want = Buffer.from(sign(u.lname, u.salt)), got = Buffer.from(sig);
  return want.length === got.length && crypto.timingSafeEqual(want, got) ? u : null;
}
function readBody(req) {
  return new Promise(ok => { let b = ''; req.on('data', c => { b += c; if (b.length > MAX_DATA + 4096) { b = ''; req.destroy(); } });
    req.on('end', () => { try { ok(JSON.parse(b || '{}')); } catch (e) { ok({}); } }); req.on('error', () => ok({})); });
}
const tries = new Map();   // กันเดารหัสผ่าน: ต่อ IP ไม่เกิน 30 ครั้ง / 10 นาที
function limited(req) {
  const ip = (req.headers['x-forwarded-for'] || req.socket.remoteAddress || '').split(',')[0].trim(), now = Date.now();
  const t = (tries.get(ip) || []).filter(x => now - x < 600000); t.push(now); tries.set(ip, t); return t.length > 30;
}

// ---------- รางวัลจบฤดูกาลตามอันดับ ----------
// ขึ้นเดือนใหม่ (เวลาไทย) → ถ่ายภาพนิ่งอันดับของเดือนที่แล้วก่อนรับคำขอใด ๆ (ผู้เล่นที่ล็อกอินจะย้ายไปฤดูกาลใหม่ แล้วหายจากตารางเดิม)
let snapFor = '', snapping = null;
let migrated = null;   // ข้อมูลเก่า → เติมสถิติออนไลน์ (ครั้งเดียวตอนเปิดเซิร์ฟเวอร์)
const migrateOnce = () => migrated || (migrated = Promise.resolve().then(() => store.migrateOnline()).then(n => { if (n) console.log(`online stats seeded for ${n} players`); }).catch(e => { console.error('online seed error', e.message); migrated = null; }));
function ensureSnap() { const cur = AC.seasonKey(); if (snapFor === cur || accountsDown()) return accountsDown() ? Promise.resolve() : migrateOnce();
  if (!snapping) snapping = migrateOnce().then(() => store.snapSeason(AC.prevSeason(cur))).then(s => { snapFor = cur; if (s) console.log(`season ${AC.prevSeason(cur)} final standings saved: ${s.n} players`); })
    .catch(e => console.error('season snapshot error', e.message)).finally(() => { snapping = null; });
  return snapping; }
setInterval(ensureSnap, 5 * 60 * 1000).unref(); setTimeout(ensureSnap, 3000).unref();
// รางวัลของผู้เล่นคนนี้ (ถ้าข้อมูลยังอยู่ฤดูกาลเก่า) → {season,pos,n,coins} · ไม่ติดอันดับ/ไม่มีภาพนิ่ง → coins 0
async function prizeOf(u) { const d = (u && u.data) || {}; if (!d.season || d.season >= AC.seasonKey()) return null;
  const sn = await store.getSeason(d.season).catch(() => null); if (!sn) return { season: d.season, pos: 0, n: 0, coins: 0 };
  const e = (sn.ranks || {})[u.lname], pos = e ? e[0] : 0; return { season: d.season, pos, n: sn.n, coins: AC.seasonPrize(pos, sn.n) }; }

// ---------- API ----------
async function handleApi(req, res, p) {
  const out = (code, o) => { res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }); res.end(JSON.stringify(o)); };
  try {
    await ensureSnap();
    if (p === '/api/status') { await store.ready.catch(() => {}); return out(200, { accounts: true, store: store.kind, dbError: store.dbError || undefined, down: accountsDown() || undefined, season: AC.seasonKey() }); }
    if (p === '/api/top' && req.method === 'GET') {
      const by = LB_VAL[new URL(req.url, 'http://x').searchParams.get('by')] ? new URL(req.url, 'http://x').searchParams.get('by') : 'rp';
      const u = req.headers.authorization ? await authUser(req).catch(() => null) : null;
      return out(200, { season: AC.seasonKey(), by, ...(await store.top(50, AC.seasonKey(), by, u && u.lname)) });
    }
    if (p === '/api/profile' && req.method === 'GET') {
      const nm = lower(String(new URL(req.url, 'http://x').searchParams.get('name') || '').trim().slice(0, 40));
      const u = nm ? await store.get(nm) : null; if (!u) return out(404, { err: 'ไม่พบผู้เล่นคนนี้' });
      return out(200, pubProfile(u));
    }
    if (accountsDown()) return out(503, { err: 'ระบบบัญชีปิดปรับปรุงชั่วคราว (ยังไม่ได้ต่อฐานข้อมูล) เล่นแบบ Guest ไปก่อนได้' });
    if (req.method === 'GET' && p === '/api/me') {
      const u = await authUser(req); if (!u) return out(401, { err: 'กรุณาเข้าสู่ระบบใหม่' });
      return out(200, { name: u.name, data: AC.seedOnline(u.data), prize: await prizeOf(u) });
    }
    if (req.method !== 'POST') return out(404, { err: 'not found' });
    const body = await readBody(req);
    if (p === '/api/register' || p === '/api/login') {
      if (limited(req)) return out(429, { err: 'ลองบ่อยเกินไป รอสักครู่แล้วลองใหม่' });
      const name = cleanName(body.name), pass = String(body.pass || '');
      if ([...name].length < 2 || [...name].length > 14) return out(400, { err: 'ชื่อต้องยาว 2–14 ตัวอักษร' });
      if (!passOk(pass)) return out(400, { err: 'รหัสผ่านต้องยาว 4 ตัวขึ้นไป' });
      const l = lower(name);
      if (p === '/api/register') {
        const raw = cleanData(body.data); if (raw === null) return out(400, { err: 'ข้อมูลใหญ่เกินไป' });
        const data = AC.validate(null, raw).data, rc = makeRecovery();
        const salt = crypto.randomBytes(16).toString('hex'), u = { lname: l, name, salt, hash: await hashPass(pass, salt), data, rp: rpOf(data) };
        if (!(await store.create(u))) return out(409, { err: 'ชื่อนี้มีคนใช้แล้ว ลองชื่ออื่น' });
        await store.setRecovery(l, rc.rhash);
        return out(200, { token: makeToken(u), name, data, code: rc.code });
      }
      const u = await store.get(l);
      if (!u || (await hashPass(pass, u.salt)) !== u.hash) return out(401, { err: 'ชื่อหรือรหัสผ่านไม่ถูกต้อง' });
      return out(200, { token: makeToken(u), name: u.name, data: AC.seedOnline(u.data), prize: await prizeOf(u) });
    }
    if (p === '/api/reset') {   // ลืมรหัสผ่าน: ชื่อ + รหัสกู้คืน → ตั้งรหัสผ่านใหม่ (ได้รหัสกู้คืนชุดใหม่ด้วย)
      if (limited(req)) return out(429, { err: 'ลองบ่อยเกินไป รอสักครู่แล้วลองใหม่' });
      const pass = String(body.pass || ''); if (!passOk(pass)) return out(400, { err: 'รหัสผ่านใหม่ต้องยาว 4 ตัวขึ้นไป' });
      const u = await store.get(lower(cleanName(body.name)));
      if (!u || !checkRecovery(u.rhash, body.code)) return out(401, { err: 'ชื่อหรือรหัสกู้คืนไม่ถูกต้อง' });
      const salt = crypto.randomBytes(16).toString('hex'), rc = makeRecovery();
      await store.setAuth(u.lname, salt, await hashPass(pass, salt)); await store.setRecovery(u.lname, rc.rhash);
      return out(200, { token: makeToken({ lname: u.lname, salt }), name: u.name, data: AC.seedOnline(u.data), code: rc.code, prize: await prizeOf(u) });
    }
    const u = await authUser(req); if (!u) return out(401, { err: 'กรุณาเข้าสู่ระบบใหม่' });
    if (p === '/api/save') {
      const raw = cleanData(body.data); if (raw === null) return out(400, { err: 'ข้อมูลใหญ่เกินไป' });
      const pz = await prizeOf(u), { data, fixed } = AC.validate(u.data || {}, raw, Date.now(), pz ? pz.coins : 0);
      await store.save(u.lname, data, rpOf(data));
      return out(200, fixed ? { ok: true, fix: { coins: data.coins, rp: data.rp, onrp: data.onrp, owned: data.owned, maxLen: data.st.maxLen || 0 } } : { ok: true });
    }
    if (p === '/api/password') {   // เปลี่ยนรหัสผ่าน (token เดิมของทุกเครื่องใช้ไม่ได้อีก)
      if (limited(req)) return out(429, { err: 'ลองบ่อยเกินไป รอสักครู่แล้วลองใหม่' });
      if ((await hashPass(String(body.old || ''), u.salt)) !== u.hash) return out(401, { err: 'รหัสผ่านเดิมไม่ถูกต้อง' });
      const pass = String(body.pass || ''); if (!passOk(pass)) return out(400, { err: 'รหัสผ่านใหม่ต้องยาว 4 ตัวขึ้นไป' });
      const salt = crypto.randomBytes(16).toString('hex'); await store.setAuth(u.lname, salt, await hashPass(pass, salt));
      return out(200, { token: makeToken({ lname: u.lname, salt }) });
    }
    if (p === '/api/recovery') { const rc = makeRecovery(); await store.setRecovery(u.lname, rc.rhash); return out(200, { code: rc.code }); }
    return out(404, { err: 'not found' });
  } catch (e) {
    console.error('api error', e.message);
    return out(503, { err: 'ระบบบัญชีมีปัญหาชั่วคราว ลองใหม่อีกครั้ง' });
  }
}
module.exports = { handleApi, storeKind: () => store.kind };
