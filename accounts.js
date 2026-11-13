// รถไฟซ่า — ระบบบัญชีผู้เล่น (ลงทะเบียน / เข้าสู่ระบบ / บันทึกเหรียญ-แรงก์ / ตารางอันดับ)
// มี DATABASE_URL (Postgres เช่น Neon) → เก็บในฐานข้อมูล · ไม่มี → เก็บในไฟล์ data/users.json (ไว้ทดสอบในเครื่องเท่านั้น)
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const DB_URL = process.env.DATABASE_URL || '';
const SECRET = process.env.TOKEN_SECRET || crypto.createHash('sha256').update('rotfai:' + (DB_URL || 'dev-secret')).digest('hex');
const MAX_DATA = 40 * 1024;
const RENAME_COST = 20000;   // เปลี่ยนชื่อ (เจ้าของสั่ง 11 พ.ย. 2026) — ต้องตรงกับ RENAME_COST ใน public/index.html
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
    async setBan(l, why) { if (db[l]) { db[l].ban = why || null; flush(); } },
    async setAudit(l, a) { if (db[l]) { db[l].audit = a; flush(); } },
    async rank(season, n) { return Object.values(db).filter(u => !u.ban && (u.data || {}).season === season && LB_VAL.rp(u) > 0).sort((a, b) => LB_VAL.rp(b) - LB_VAL.rp(a) || (a.updated || 0) - (b.updated || 0)).slice(0, n).map((u, i) => ({ l: u.lname, name: u.name, rp: LB_VAL.rp(u), pos: i + 1 })); },
    async rename(ol, nl, name, data, rp) { const u = db[ol]; if (!u || (nl !== ol && db[nl])) return false; delete db[ol]; Object.assign(u, { lname: nl, name, data, rp, updated: Date.now() }); db[nl] = u; flush(); return true; },
    async top(n, season, by, me) {   // by: rp (ฤดูกาลนี้) / len (ยาวสุดตลอดกาล) / coins (เหรียญที่มีตอนนี้)
      const all = Object.values(db).filter(u => !u.ban && (by !== 'rp' || (u.data || {}).season === season)).map(u => ({ name: u.name, lname: u.lname, val: LB_VAL[by](u), rp: +u.rp || 0, tid: ((u.data || {}).eq || {}).title || '' })).filter(u => u.val > 0).sort((a, b) => b.val - a.val);
      const i = me ? all.findIndex(u => u.lname === me) : -1;
      return { top: all.slice(0, n).map(({ lname, ...u }) => u), me: i >= 0 ? { pos: i + 1, val: all[i].val } : null, n: all.length }; },
    async getSeason(k) { return seasons[k] || null; },
    async migrateOnline() { let n = 0; for (const u of Object.values(db)) if ((u.data || {}).onv !== 2) { u.data = AC.seedOnline(u.data); n++; } if (n) flush(); return n; },
    async cleanAdminOwned() { const fixed = []; for (const u of Object.values(db)) { if (adminPolluted((u.data || {}).owned)) { u.data = cleanOwnedData(u.data); fixed.push(u.name); }
        const r = restoreOwned(u.lname, u.data); if (r) { u.data = r; fixed.push('+' + u.name); } } if (fixed.length) flush(); return fixed; },
    async snapSeason(k) { if (seasons[k]) return seasons[k];   // ภาพนิ่งอันดับตอนจบฤดูกาล (ทำครั้งเดียว)
      const all = Object.values(db).filter(u => !u.ban && (u.data || {}).season === k && LB_VAL.rp(u) > 0).sort((a, b) => LB_VAL.rp(b) - LB_VAL.rp(a) || (a.updated || 0) - (b.updated || 0)), ranks = {};
      all.forEach((u, i) => { ranks[u.lname] = [i + 1, LB_VAL.rp(u)]; });
      seasons[k] = { n: all.length, ranks, top: all.slice(0, SNAP_TOP).map((u, i) => topRow(u, i + 1)), at: new Date().toISOString() }; fs.mkdirSync(path.dirname(SFILE), { recursive: true }); fs.writeFileSync(SFILE, JSON.stringify(seasons)); return seasons[k]; },
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
    .then(() => pool.query('ALTER TABLE players ADD COLUMN IF NOT EXISTS ban TEXT'))
    .then(() => pool.query('ALTER TABLE players ADD COLUMN IF NOT EXISTS audit JSONB'))
    .then(() => pool.query(`CREATE TABLE IF NOT EXISTS seasons (key TEXT PRIMARY KEY, n INTEGER NOT NULL, ranks JSONB NOT NULL, created TIMESTAMPTZ NOT NULL DEFAULT now())`))
    .then(() => pool.query('ALTER TABLE seasons ADD COLUMN IF NOT EXISTS top JSONB'))
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
    async setBan(l, why) { await ready; if (store !== dbStore) return store.setBan(l, why); await pool.query('UPDATE players SET ban=$2 WHERE lname=$1', [l, why || null]); },
    async setAudit(l, a) { await ready; if (store !== dbStore) return store.setAudit(l, a); await pool.query('UPDATE players SET audit=$2 WHERE lname=$1', [l, JSON.stringify(a)]); },
    async rank(season, n) { await ready; if (store !== dbStore) return store.rank(season, n);
      const r = await pool.query(`SELECT lname, name, ${LB_SQL.rp} AS v FROM players WHERE ban IS NULL AND data->>'season'=$1 AND ${LB_SQL.rp} > 0 ORDER BY v DESC, updated ASC LIMIT $2`, [season, n]);
      return r.rows.map((u, i) => ({ l: u.lname, name: u.name, rp: +u.v || 0, pos: i + 1 })); },
    async rename(ol, nl, name, data, rp) { await ready; if (store !== dbStore) return store.rename(ol, nl, name, data, rp);
      try { const r = await pool.query('UPDATE players SET lname=$2, name=$3, data=$4, rp=$5, updated=now() WHERE lname=$1', [ol, nl, name, data, rp]); return r.rowCount === 1; }
      catch (e) { if (e.code === '23505') return false; throw e; } },
    async top(n, season, by, me) { await ready; if (store !== dbStore) return store.top(n, season, by, me);
      const ex = LB_SQL[by], w = 'ban IS NULL AND ' + (by === 'rp' ? "data->>'season'=$1 AND " : '$1::text IS NOT NULL AND ');
      const r = await pool.query(`SELECT name, rp, ${ex} AS val, COALESCE(data->'eq'->>'title','') AS tid FROM players WHERE ${w}${ex} > 0 ORDER BY val DESC, updated ASC LIMIT $2`, [season, n]);
      let mine = null;
      if (me) { const q = await pool.query(`SELECT ${ex} AS val FROM players WHERE lname=$1 AND (${by !== 'rp'} OR data->>'season'=$2)`, [me, season]); const v = q.rows[0] ? +q.rows[0].val : 0;
        if (v > 0) { const c = await pool.query(`SELECT count(*)::int AS n FROM players WHERE ${w}${ex} > $2`, [season, v]); mine = { pos: c.rows[0].n + 1, val: v }; } }
      const cn = await pool.query(`SELECT count(*)::int AS n FROM players WHERE ${w}${ex} > 0`, [season]);
      return { top: r.rows.map(x => ({ name: x.name, val: +x.val, rp: +x.rp || 0, tid: x.tid })), me: mine, n: cn.rows[0].n }; },
    async migrateOnline() { await ready; if (store !== dbStore) return store.migrateOnline();
      const r = await pool.query("SELECT lname, data FROM players WHERE COALESCE(data->>'onv','') <> '2'"); for (const u of r.rows) await pool.query("UPDATE players SET data=$2 WHERE lname=$1 AND COALESCE(data->>'onv','') <> '2'", [u.lname, AC.seedOnline(u.data)]); return r.rows.length; },
    async cleanAdminOwned() { await ready; if (store !== dbStore) return store.cleanAdminOwned(); const fixed = [];
      const r = await pool.query("SELECT lname, name, data FROM players WHERE data ? 'owned' OR lname = ANY($1)", [OWN_RESTORE.map(x => x[0])]);
      for (const u of r.rows) { let d = u.data, ch = false; if (adminPolluted((d || {}).owned)) { d = cleanOwnedData(d); ch = true; fixed.push(u.name); }
        const rs = restoreOwned(u.lname, d); if (rs) { d = rs; ch = true; fixed.push('+' + u.name); }
        if (ch) await pool.query('UPDATE players SET data=$2 WHERE lname=$1', [u.lname, d]); } return fixed; },
    async getSeason(k) { await ready; if (store !== dbStore) return store.getSeason(k); const r = await pool.query('SELECT n, ranks, top, created AS at FROM seasons WHERE key=$1', [k]); return r.rows[0] || null; },
    async snapSeason(k) { await ready; if (store !== dbStore) return store.snapSeason(k);   // ภาพนิ่งอันดับตอนจบฤดูกาล (ทำครั้งเดียว)
      const have = await this.getSeason(k); if (have) return have;
      const r = await pool.query(`SELECT lname, ${LB_SQL.rp} AS v FROM players WHERE ban IS NULL AND data->>'season'=$1 AND ${LB_SQL.rp} > 0 ORDER BY v DESC, updated ASC`, [k]), ranks = {};
      r.rows.forEach((u, i) => { ranks[u.lname] = [i + 1, +u.v || 0]; });
      const top = []; for (const [i, row] of r.rows.slice(0, SNAP_TOP).entries()) { const u = await this.get(row.lname); if (u) top.push(topRow(u, i + 1)); }
      await pool.query('INSERT INTO seasons (key, n, ranks, top) VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING', [k, r.rows.length, ranks, JSON.stringify(top)]);
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
  return { name: u.name, rp: +u.rp || 0, season: d.season || '', tid: (d.eq || {}).title || '', loco: (d.eq || {}).loco || '', horn: (d.eq || {}).horn || '', ach: Object.keys(d.ach || {}).length, st: o, adv: advOf(d.stage) }; }
// ผจญภัย (เจ้าของสั่ง 11 พ.ย. 2026): ผ่านถึงด่านไหน + ดาวรวม — stage = [ดาว 0–3 ต่อด่าน] 30 ด่าน
function advOf(a) { a = Array.isArray(a) ? a.slice(0, 30).map(v => Math.max(0, Math.min(3, Math.floor(+v || 0)))) : []; let top = 0; a.forEach((v, i) => { if (v > 0) top = i + 1; }); return { top, stars: a.reduce((x, v) => x + v, 0) }; }
const LB_SQL = { rp: "floor(COALESCE((data->>'onrp')::float,0))", len: "floor(COALESCE((data->'st'->>'omaxLen')::float,0))", coins: "floor(COALESCE((data->>'coins')::float,0))", kills: "floor(COALESCE((data->'st'->>'okills')::float,0))" };

// ผลจบฤดูกาล (เจ้าของสั่ง 13 พ.ย. 2026 · รางวัลอัญมณีอันดับ 1–3): เก็บชื่อ + สถิติ 10 อันดับแรกไว้ตอนตัดผล
const SNAP_TOP = 10;
function topRow(u, pos) { const d = u.data || {}, st = d.st || {}; return { pos, l: u.lname, name: u.name, rp: LB_VAL.rp(u), kills: Math.floor(+st.okills || 0), len: Math.floor(+st.omaxLen || 0), games: Math.floor(+st.games || 0), title: (d.eq || {}).title || '' }; }
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
const migrateOnce = () => migrated || (migrated = Promise.resolve().then(() => store.migrateOnline()).then(n => { if (n) console.log(`online stats seeded for ${n} players`); })
  .then(() => store.cleanAdminOwned()).then(f => { if (f.length) console.log(`owned fix (admin items removed / +restored): ${f.join(', ')}`); }).catch(e => { console.error('online seed error', e.message); migrated = null; }));
function ensureSnap() { const cur = AC.seasonKey(); if (snapFor === cur || accountsDown()) return accountsDown() ? Promise.resolve() : migrateOnce();
  if (!snapping) snapping = migrateOnce().then(() => store.snapSeason(AC.prevSeason(cur))).then(s => { snapFor = cur; if (s) console.log(`season ${AC.prevSeason(cur)} final standings saved: ${s.n} players`); })
    .catch(e => console.error('season snapshot error', e.message)).finally(() => { snapping = null; });
  return snapping; }
setInterval(ensureSnap, 5 * 60 * 1000).unref(); setTimeout(ensureSnap, 3000).unref();
// ตัดผลตรงเที่ยงคืนเวลาไทย (00:00:01) ไม่ต้องรอรอบ 5 นาที — ตั้งเวลาใหม่ทุกวัน
(function atBkkMidnight() { const DAY = 864e5, BKK = 7 * 36e5, now = Date.now(); const ms = DAY - ((now + BKK) % DAY) + 1000;
  setTimeout(() => { ensureSnap(); atBkkMidnight(); }, ms).unref(); })();
// รางวัลของผู้เล่นคนนี้ (ถ้าข้อมูลยังอยู่ฤดูกาลเก่า) → {season,pos,n,coins} · ไม่ติดอันดับ/ไม่มีภาพนิ่ง → coins 0
async function prizeOf(u) { const d = (u && u.data) || {}; if (!d.season || d.season >= AC.seasonKey()) return null;
  const sn = await store.getSeason(d.season).catch(() => null); if (!sn) return { season: d.season, pos: 0, n: 0, coins: 0 };
  const e = (sn.ranks || {})[u.lname], pos = e ? e[0] : 0; return { season: d.season, pos, n: sn.n, coins: AC.seasonPrize(pos, sn.n) }; }

// ---------- รางวัลอัญมณีจริง + ตรวจโกง + แบน (เจ้าของสั่ง 13 พ.ย. 2026) ----------
// GEM_SEASONS: ฤดูกาลที่มีรางวัลอัญมณี → จำนวนผู้ชนะ (อันดับ 1–N ของ 🏅 แรงก์ ที่ไม่ถูกแบน/ตัดสิทธิ์) · ของรางวัลแสดงใน index.html (GEM_PRIZES)
const GEM_SEASONS = { '2026-12': 3 }, CLAIM_DAYS = 14;
for (const x of String(process.env.GEM_EXTRA || '').split(',')) { const m = /^(\d{4}-\d{2}):(\d)$/.exec(x.trim()); if (m) GEM_SEASONS[m[1]] = +m[2]; }   // ทดสอบ: GEM_EXTRA=2026-10:3
// ผู้ดูแล = ชื่อบัญชีใน env ADMINS (คั่นด้วย ,) — เห็นปุ่ม 🛡️ ผู้ดูแล ในหน้าบัญชี: ดูผลตรวจ แบน/ปลดแบน ให้สิทธิ์คืน ตรวจรหัสรับรางวัล
// ค่าเริ่มต้น = บัญชีเจ้าของ "พล" (เจ้าของยืนยัน 13 พ.ย.) — ตั้ง env ADMINS ทับได้ · ชื่อผู้ดูแลสงวนไว้: คนอื่นสมัคร/เปลี่ยนชื่อเป็นชื่อนี้ไม่ได้
const ADMINS = new Set(String(process.env.ADMINS || 'พล').split(',').map(x => lower(x.trim())).filter(Boolean));
const isAdmin = u => !!u && ADMINS.has(u.lname);
const seasonEnd = k => Date.UTC(+k.slice(0, 4), +k.slice(5, 7), 1) - 7 * 36e5;   // 00:00 วันที่ 1 เดือนถัดไป เวลาไทย
const claimCode = (season, l) => { const h = crypto.createHmac('sha256', SECRET).update('gem:' + season + ':' + l).digest(); let c = '';
  for (let i = 0; i < 8; i++) { c += 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'[h[i] % 32]; if (i === 3) c += '-'; } return c; };
// การเล่นออนไลน์ที่เซิร์ฟเวอร์เห็นเอง (server.js ส่งมา) ต่อบัญชีต่อฤดูกาล: sec เวลาที่มีชีวิตในเกม, g เกม (ตาย/ออก), k กำจัดที่เซิร์ฟเวอร์ยืนยัน, ml ยาวสุด,
// fix = ครั้งที่ส่งข้อมูลเกินจริงแล้วระบบกันโกงปรับคืน, rp0 = RP ตอนเริ่มเก็บข้อมูล, ok = ผู้ดูแลให้สิทธิ์คืน
const audQ = new Map();
function bumpAudit(l, fn, season) {
  const p = (audQ.get(l) || Promise.resolve()).then(async () => { const u = await store.get(l); if (!u || u.ban) return;
    const k = season || AC.seasonKey(), all = { ...(u.audit && typeof u.audit === 'object' ? u.audit : {}) }, d = u.data || {};
    const a = all[k] || (all[k] = { sec: 0, g: 0, k: 0, ml: 0, fix: 0, rp0: d.season === k ? LB_VAL.rp(u) : Math.floor(LB_VAL.rp(u) / 2), t0: Date.now() });
    fn(a); for (const s of Object.keys(all).sort().slice(0, -3)) delete all[s]; await store.setAudit(l, all); }).catch(e => console.error('audit error', e.message));
  audQ.set(l, p); p.then(() => { if (audQ.get(l) === p) audQ.delete(l); }); return p; }
async function tokenUser(tok) { const [a, sig] = String(tok || '').split('.'); if (!a || !sig) return null; const u = await store.get(unb64u(a)).catch(() => null); if (!u || u.ban) return null;
  const want = Buffer.from(sign(u.lname, u.salt)), got = Buffer.from(sig); return want.length === got.length && crypto.timingSafeEqual(want, got) ? u.lname : null; }
function addPlay(l, d) { if (!l || accountsDown()) return; const sec = Math.max(0, Math.min(3600, +d.sec || 0)), g = Math.max(0, Math.min(100, d.g | 0)), k = Math.max(0, Math.min(500, d.k | 0)), ml = Math.max(0, Math.min(5000, +d.ml || 0));
  if (!sec && !g && !k) return; return bumpAudit(l, a => { a.sec = Math.round(a.sec + sec); a.g += g; a.k += k; a.ml = Math.max(a.ml, Math.round(ml)); }); }
// ตรวจความผิดปกติ: RP ที่ได้มากกว่าที่เล่นจริงจะทำได้ / เล่นออนไลน์จริงน้อยมาก / ส่งข้อมูลเกินจริงบ่อย → ตัดสิทธิ์อัตโนมัติ (ผู้ดูแลกดให้สิทธิ์คืนได้)
// ระบบเริ่มจดเวลาเล่นจริง 13 พ.ย. 2026 ~15:20 → ฤดูกาลก่อน AUDIT_FROM มีข้อมูลไม่ครบเดือน ไม่ใช้เกณฑ์ 10 นาที (เจ้าของแจ้ง 13 พ.ย.: ผู้เล่นทุกคนเล่นเกิน 10 นาทีแน่นอน)
const AUDIT_FROM = process.env.AUDIT_FROM || '2026-12', AUDIT_SINCE = '13 พ.ย. 2026 15:20';
const auditPartial = season => season < AUDIT_FROM;
function reviewOf(u, season, rp) {
  const a = u && u.audit && u.audit[season] || null, flags = [], part = auditPartial(season);
  if (!a || a.sec < 600) { if (!part) flags.push('เล่นออนไลน์จริงที่ระบบเห็น ' + Math.round((a ? a.sec : 0) / 60) + ' นาที (ต้อง 10 นาทีขึ้นไป)'); }
  if (a && a.sec >= 600 || part && a) { const gain = Math.max(0, rp - (a.rp0 || 0)), plaus = 60 + a.g * 120 + a.k * 2;   // 13 พ.ย. 18:39 ความยาวทุก 30 = +1 RP (เดิม 60) → เผื่อต่อเกม 70 → 120
    if (gain > plaus * 1.5) flags.push(`RP เพิ่ม ${gain} แต่เล่นจริง ${a.g} เกม กำจัด ${a.k} (ทำได้ไม่เกิน ~${Math.round(plaus * 1.5)})`); }
  if (a && a.fix >= 3) flags.push(`ส่งข้อมูลเกินจริง ${a.fix} ครั้ง (ระบบกันโกงปรับคืนแล้ว)`);
  return { a, flags, dq: flags.length > 0 && !(a && a.ok) };
}
async function standings(season) {
  if (season >= AC.seasonKey()) return store.rank(season, SNAP_TOP);
  const sn = await store.getSeason(season); if (!sn) return [];
  if (Array.isArray(sn.top) && sn.top.length && sn.top[0].l) return sn.top;
  return Object.entries(sn.ranks || {}).sort((a, b) => a[1][0] - b[1][0]).slice(0, SNAP_TOP).map(([l, e]) => ({ l, pos: e[0], rp: e[1] }));
}
const revCache = new Map();
async function reviewList(season, fresh) {
  const c = revCache.get(season); if (!fresh && c && Date.now() - c.t < 30000) return c.rows;
  const N = GEM_SEASONS[season] || 0, rows = []; let place = 0;
  for (const r of await standings(season)) { const u = await store.get(r.l), rv = reviewOf(u, season, r.rp), status = !u ? 'gone' : u.ban ? 'ban' : isAdmin(u) ? 'admin' : rv.dq ? 'dq' : 'ok';   // ผู้ดูแลไม่ร่วมชิงพลอย (เจ้าของสั่ง 13 พ.ย.)
    const pl = status === 'ok' && place < N ? ++place : 0, a = rv.a;
    rows.push({ pos: r.pos, l: r.l, name: u ? u.name : (r.name || r.l), rp: r.rp, status, why: u && u.ban || '', place: pl, code: pl ? claimCode(season, r.l) : '', flags: rv.flags, ok: !!(a && a.ok),
      aud: a ? { min: Math.round(a.sec / 60), g: a.g, k: a.k, ml: a.ml, fix: a.fix, rp0: a.rp0 } : null }); }
  revCache.set(season, { t: Date.now(), rows }); return rows;
}
// ผู้ชนะอัญมณีของฤดูกาลที่จบแล้ว (ภายใน CLAIM_DAYS วัน) → โชว์ป๊อปอัปรหัสรับรางวัลในเกม
async function gemOf(u) { const now = Date.now();
  for (const k of Object.keys(GEM_SEASONS)) { if (k >= AC.seasonKey() || now > seasonEnd(k) + CLAIM_DAYS * 864e5) continue;
    const r = (await reviewList(k)).find(x => x.l === u.lname); if (!r) continue;
    if (r.place) return { season: k, place: r.place, pos: r.pos, rp: r.rp, claimed: (u.audit && u.audit[k] && u.audit[k].claim) || 0, until: seasonEnd(k) + CLAIM_DAYS * 864e5 };
    if (r.status === 'dq' && r.pos <= (GEM_SEASONS[k] || 0) + 2) return { season: k, review: true }; }
  return null; }
// ผู้ดูแล: เปิดเกมหลังจบฤดูกาลชิงพลอย → ได้รายชื่อผู้ชนะ 1–3 เลย (เจ้าของสั่ง 13 พ.ย.: ไม่ต้องใช้รหัสรับรางวัล ระบบจำผลแล้วแจ้งเจ้าของ)
async function winnersFor(u) { if (!isAdmin(u)) return undefined; const now = Date.now(), out = [];
  for (const k of Object.keys(GEM_SEASONS).sort()) { if (k >= AC.seasonKey() || now > seasonEnd(k) + 30 * 864e5) continue;
    const rows = await reviewList(k); const claimOf = async l => { const x = await store.get(l).catch(() => null); return (x && x.audit && x.audit[k] && x.audit[k].claim) || 0; };
    const win = []; for (const r of rows.filter(r => r.place)) win.push({ place: r.place, name: r.name, rp: r.rp, pos: r.pos, claimed: await claimOf(r.l) });
    out.push({ season: k, at: seasonEnd(k), win,
      dq: rows.filter(r => (r.status === 'dq' || r.status === 'ban') && r.pos <= (GEM_SEASONS[k] || 0) + 2).map(r => ({ pos: r.pos, name: r.name, status: r.status })) }); }
  return out.length ? out : undefined; }
// ผู้ดูแลใช้ของในร้านได้ทุกชิ้นไม่ต้องซื้อ (เจ้าของสั่ง 13 พ.ย.) → ให้ owned ครบทุกชิ้นทั้งตอนส่งข้อมูลให้เครื่องและตอนตรวจ /api/save
const ALL_OWNED = (() => { const o = {}; for (const c of AC.CATS) o[c] = Object.keys(AC.SHOP[c]); for (const [c, id] of AC.LIMITED) if (o[c] && !o[c].includes(id)) o[c].push(id); return o; })();
function withAdmin(u, d) { if (!isAdmin(u) || !d || typeof d !== 'object') return d; const owned = { ...(d.owned || {}) };
  for (const c of AC.CATS) owned[c] = [...new Set([...(Array.isArray(owned[c]) ? owned[c] : []), ...ALL_OWNED[c]])]; return { ...d, owned }; }
// ของที่ผู้ดูแลได้ใช้ฟรี (withAdmin) ห้ามบันทึกลงบัญชี — เดิมบันทึกไปด้วย → เปลี่ยนชื่อ/ถอดผู้ดูแลแล้วยังมีของครบ (เจ้าของแจ้ง 13 พ.ย. 21:24)
// "ของครบเกือบทุกชิ้น" (≥ 90% ของร้าน รวมของหายาก) = ของที่ติดมาจากสิทธิ์ผู้ดูแล — ซื้อจริงไม่มีทางได้ (รวมหลายล้านเหรียญ + ของหายากวนวันละชิ้น)
const ALL_N = AC.CATS.reduce((n, c) => n + ALL_OWNED[c].length, 0);
function adminPolluted(owned) { if (!owned || typeof owned !== 'object') return false; let n = 0;
  for (const c of AC.CATS) { const have = new Set(Array.isArray(owned[c]) ? owned[c] : []); for (const id of ALL_OWNED[c]) if (have.has(id)) n++; } return n >= ALL_N * 0.9; }
const FREE_OWNED = (() => { const o = {}; for (const c of AC.CATS) o[c] = Object.keys(AC.SHOP[c]).filter(id => AC.SHOP[c][id] === 0); return o; })();
// ของจริงของบัญชี: ติดมาจากผู้ดูแล → เหลือของฟรี (ไม่รู้ว่าเคยซื้ออะไรเองก่อนเป็นผู้ดูแล)
const realOwned = d => adminPolluted((d || {}).owned) ? JSON.parse(JSON.stringify(FREE_OWNED)) : ((d || {}).owned || {});
// คืนของที่เคยซื้อจริงให้บัญชีที่โดนล้างของผู้ดูแล (เจ้าของแจ้ง) · ทำครั้งเดียวต่อรายการ (จำใน data.restored)
const OWN_RESTORE = [['gemreaper', 'loco', 'diesel', 'r1']];   // 13 พ.ย. 21:33 บัญชีผู้ดูแลเดิม (GemReaper) เคยซื้อหัวจักรดีเซล
function restoreOwned(l, d) { let ch = false; d = { ...(d || {}) };
  for (const [ll, c, id, key] of OWN_RESTORE) { if (ll !== l || (d.restored || []).includes(key)) continue;
    const o = { ...(d.owned || {}) }; o[c] = [...new Set([...(Array.isArray(o[c]) ? o[c] : []), id])]; d.owned = o; d.restored = [...(d.restored || []), key]; ch = true; }
  return ch ? d : null; }
const cleanOwnedData = d => (d && adminPolluted(d.owned)) ? { ...d, owned: realOwned(d), ownFix: Date.now() } : d;
// ข้อมูลที่เครื่องส่งมา: ถ้า owned ติดของผู้ดูแลมา (หน้าเว็บเก่าที่ยังเปิดค้าง) → ใช้ของที่บัญชีมีจริง ไม่นับเป็นการซื้อ (ไม่หักเหรียญ)
const stripSent = (u, raw) => (!isAdmin(u) && raw && adminPolluted(raw.owned)) ? { ...raw, owned: realOwned(u.data) } : raw;
// บันทึก: ผู้ดูแลไม่ซื้อของ → owned ที่บันทึก = ของจริงเดิมเสมอ
const keepReal = (u, data) => isAdmin(u) ? { ...data, owned: realOwned(u.data) } : data;
const BAN_MSG = why => 'บัญชีนี้ถูกระงับ' + (why ? ' (' + why + ')' : '') + ' — ถ้าคิดว่าผิดพลาด ติดต่อทีมงาน';

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
    if (p === '/api/season' && req.method === 'GET') {   // ผลจบฤดูกาล: ?key=YYYY-MM (ไม่ใส่ = เดือนที่แล้ว)
      const q = String(new URL(req.url, 'http://x').searchParams.get('key') || ''), key = /^\d{4}-\d{2}$/.test(q) ? q : AC.prevSeason(AC.seasonKey());
      if (key >= AC.seasonKey()) return out(200, { key, live: true });
      const sn = await store.getSeason(key); if (!sn) return out(200, { key, n: 0, top: [] });
      let top = Array.isArray(sn.top) ? sn.top : null;
      if (!top) { top = []; for (const [l, e] of Object.entries(sn.ranks || {}).sort((a, b) => a[1][0] - b[1][0]).slice(0, SNAP_TOP)) { const u = await store.get(l); top.push({ pos: e[0], name: u ? u.name : l, rp: e[1] }); } }
      return out(200, { key, n: sn.n, at: sn.at || null, top: top.map(({ l, ...t }) => t) });
    }
    if (p === '/api/profile' && req.method === 'GET') {
      const nm = lower(String(new URL(req.url, 'http://x').searchParams.get('name') || '').trim().slice(0, 40));
      const u = nm ? await store.get(nm) : null; if (!u) return out(404, { err: 'ไม่พบผู้เล่นคนนี้' });
      return out(200, pubProfile(u));
    }
    if (accountsDown()) return out(503, { err: 'ระบบบัญชีปิดปรับปรุงชั่วคราว (ยังไม่ได้ต่อฐานข้อมูล) เล่นแบบ Guest ไปก่อนได้' });
    if (req.method === 'GET' && p === '/api/me') {
      const u = await authUser(req); if (!u) return out(401, { err: 'กรุณาเข้าสู่ระบบใหม่' });
      if (u.ban) return out(403, { err: BAN_MSG(u.ban), banned: true });
      return out(200, { name: u.name, data: withAdmin(u, AC.seedOnline(u.data)), prize: await prizeOf(u), gem: await gemOf(u).catch(() => null), admin: isAdmin(u) || undefined, winners: await winnersFor(u).catch(() => undefined) });
    }
    if (p.startsWith('/api/admin/')) {   // ผู้ดูแล (ADMINS) เท่านั้น
      const u = await authUser(req); if (!isAdmin(u)) return out(403, { err: 'เฉพาะผู้ดูแล' });
      const q = new URL(req.url, 'http://x').searchParams;
      if (p === '/api/admin/review') { const key = /^\d{4}-\d{2}$/.test(q.get('key') || '') ? q.get('key') : AC.seasonKey();
        return out(200, { key, live: key >= AC.seasonKey(), gems: GEM_SEASONS[key] || 0, partial: auditPartial(key) ? AUDIT_SINCE : '', seasons: Object.keys(GEM_SEASONS), rows: (await reviewList(key, true)).map(({ l, ...r }) => r) }); }
      if (p === '/api/admin/claim') { const code = String(q.get('code') || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
        for (const k of Object.keys(GEM_SEASONS)) { if (k >= AC.seasonKey()) continue; const r = (await reviewList(k, true)).find(x => x.code.replace('-', '') === code);
          if (r) return out(200, { ok: true, season: k, place: r.place, name: r.name, rp: r.rp }); }
        return out(200, { ok: false }); }
      if (req.method === 'POST') { const b = await readBody(req), t = await store.get(lower(cleanName(b.name)));
        if (!t) return out(404, { err: 'ไม่พบผู้เล่นคนนี้' }); if (isAdmin(t) && p === '/api/admin/ban') return out(400, { err: 'แบนผู้ดูแลไม่ได้' });
        if (p === '/api/admin/ban') { const why = b.unban ? null : String(b.why || 'โกง').slice(0, 80); await store.setBan(t.lname, why); revCache.clear();
          console.log(`admin ${u.name}: ${why ? 'ban' : 'unban'} ${t.name}${why ? ' — ' + why : ''}`); return out(200, { ok: true, name: t.name, ban: why }); }
        if (p === '/api/admin/allow') { const key = /^\d{4}-\d{2}$/.test(b.key || '') ? b.key : AC.seasonKey(), v = !!b.v;
          await bumpAudit(t.lname, () => {}); const t2 = await store.get(t.lname), all = { ...(t2.audit || {}) }; all[key] = { ...(all[key] || { sec: 0, g: 0, k: 0, ml: 0, fix: 0, rp0: 0 }), ok: v };
          await store.setAudit(t.lname, all); revCache.clear(); console.log(`admin ${u.name}: allow ${t.name} ${key} = ${v}`); return out(200, { ok: true }); } }
      return out(404, { err: 'not found' });
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
        if (ADMINS.has(l)) return out(409, { err: 'ชื่อนี้มีคนใช้แล้ว ลองชื่ออื่น' });   // ชื่อผู้ดูแลสงวนไว้
        if (!(await store.create(u))) return out(409, { err: 'ชื่อนี้มีคนใช้แล้ว ลองชื่ออื่น' });
        await store.setRecovery(l, rc.rhash);
        return out(200, { token: makeToken(u), name, data, code: rc.code });
      }
      const u = await store.get(l);
      if (!u || (await hashPass(pass, u.salt)) !== u.hash) return out(401, { err: 'ชื่อหรือรหัสผ่านไม่ถูกต้อง' });
      if (u.ban) return out(403, { err: BAN_MSG(u.ban), banned: true });
      return out(200, { token: makeToken(u), name: u.name, data: withAdmin(u, AC.seedOnline(u.data)), prize: await prizeOf(u), gem: await gemOf(u).catch(() => null), admin: isAdmin(u) || undefined, winners: await winnersFor(u).catch(() => undefined) });
    }
    if (p === '/api/reset') {   // ลืมรหัสผ่าน: ชื่อ + รหัสกู้คืน → ตั้งรหัสผ่านใหม่ (ได้รหัสกู้คืนชุดใหม่ด้วย)
      if (limited(req)) return out(429, { err: 'ลองบ่อยเกินไป รอสักครู่แล้วลองใหม่' });
      const pass = String(body.pass || ''); if (!passOk(pass)) return out(400, { err: 'รหัสผ่านใหม่ต้องยาว 4 ตัวขึ้นไป' });
      const u = await store.get(lower(cleanName(body.name)));
      if (!u || !checkRecovery(u.rhash, body.code)) return out(401, { err: 'ชื่อหรือรหัสกู้คืนไม่ถูกต้อง' });
      if (u.ban) return out(403, { err: BAN_MSG(u.ban), banned: true });
      const salt = crypto.randomBytes(16).toString('hex'), rc = makeRecovery();
      await store.setAuth(u.lname, salt, await hashPass(pass, salt)); await store.setRecovery(u.lname, rc.rhash);
      return out(200, { token: makeToken({ lname: u.lname, salt }), name: u.name, data: withAdmin(u, AC.seedOnline(u.data)), code: rc.code, prize: await prizeOf(u), gem: await gemOf(u).catch(() => null), admin: isAdmin(u) || undefined, winners: await winnersFor(u).catch(() => undefined) });
    }
    const u = await authUser(req); if (!u) return out(401, { err: 'กรุณาเข้าสู่ระบบใหม่' });
    if (u.ban) return out(403, { err: BAN_MSG(u.ban), banned: true });
    if (p === '/api/claim') {   // ผู้ชนะกด 🎁 เคลมรางวัล → จดเวลาไว้ให้ผู้ดูแลเห็น (แล้วเครื่องเปิดเฟซบุ๊กเจ้าของให้ส่งที่อยู่)
      const g = await gemOf(u).catch(() => null); if (!g || !g.place) return out(400, { err: 'ไม่มีรางวัลให้เคลม' });
      if (!g.claimed) { await bumpAudit(u.lname, a => { a.claim = a.claim || Date.now(); }, g.season); revCache.delete(g.season); }
      return out(200, { ok: true }); }
    if (p === '/api/save') {
      const raw = cleanData(body.data); if (raw === null) return out(400, { err: 'ข้อมูลใหญ่เกินไป' });
      const pz = await prizeOf(u), { data, fixed } = AC.validate(withAdmin(u, u.data || {}), stripSent(u, raw), Date.now(), pz ? pz.coins : 0);
      await store.save(u.lname, keepReal(u, data), rpOf(data));
      if (fixed) bumpAudit(u.lname, a => { a.fix++; });
      const resync = !isAdmin(u) && adminPolluted(raw.owned);   // หน้าเว็บเก่าส่งของผู้ดูแลมา → ส่งของจริงกลับไปให้เครื่องปรับ
      return out(200, fixed || resync ? { ok: true, fix: { coins: data.coins, rp: data.rp, onrp: data.onrp, owned: data.owned, maxLen: data.st.maxLen || 0 } } : { ok: true });
    }
    if (p === '/api/password') {   // เปลี่ยนรหัสผ่าน (token เดิมของทุกเครื่องใช้ไม่ได้อีก)
      if (limited(req)) return out(429, { err: 'ลองบ่อยเกินไป รอสักครู่แล้วลองใหม่' });
      if ((await hashPass(String(body.old || ''), u.salt)) !== u.hash) return out(401, { err: 'รหัสผ่านเดิมไม่ถูกต้อง' });
      const pass = String(body.pass || ''); if (!passOk(pass)) return out(400, { err: 'รหัสผ่านใหม่ต้องยาว 4 ตัวขึ้นไป' });
      const salt = crypto.randomBytes(16).toString('hex'); await store.setAuth(u.lname, salt, await hashPass(pass, salt));
      return out(200, { token: makeToken({ lname: u.lname, salt }) });
    }
    if (p === '/api/rename') {   // เปลี่ยนชื่อ จ่าย RENAME_COST เหรียญ (หักบนเซิร์ฟเวอร์) · token ใหม่ (เครื่องอื่นต้องเข้าสู่ระบบด้วยชื่อใหม่)
      if (limited(req)) return out(429, { err: 'ลองบ่อยเกินไป รอสักครู่แล้วลองใหม่' });
      const name = cleanName(body.name); if ([...name].length < 2 || [...name].length > 14) return out(400, { err: 'ชื่อต้องยาว 2–14 ตัวอักษร' });
      if (name === u.name) return out(400, { err: 'ชื่อนี้เป็นชื่อปัจจุบันของคุณอยู่แล้ว' });
      { const g = await gemOf(u).catch(() => null); if (g && g.place) return out(409, { err: 'คุณมีรางวัลอัญมณีรอรับอยู่ เปลี่ยนชื่อได้หลังรับรางวัลแล้ว (' + CLAIM_DAYS + ' วันหลังจบฤดูกาล)' }); }
      const nl = lower(name); if (nl !== u.lname && (ADMINS.has(nl) || await store.get(nl))) return out(409, { err: 'ชื่อนี้มีคนใช้แล้ว ลองชื่ออื่น' });
      if (await prizeOf(u)) return out(409, { err: 'กำลังรับรางวัลจบฤดูกาล ปิดแล้วเปิดเกมใหม่ แล้วลองเปลี่ยนชื่ออีกครั้ง' });
      const raw = cleanData(body.data); if (raw === null) return out(400, { err: 'ข้อมูลใหญ่เกินไป' });
      let { data } = AC.validate(withAdmin(u, u.data || {}), stripSent(u, raw), Date.now(), 0); data = keepReal(u, data);   // บันทึกความคืบหน้าล่าสุดก่อน (ผ่านกันโกง) แล้วค่อยหักเหรียญ
      if ((+data.coins || 0) < RENAME_COST) { await store.save(u.lname, data, rpOf(data)); return out(400, { err: 'เหรียญไม่พอ ต้องใช้ ' + RENAME_COST.toLocaleString() + ' 🪙', coins: data.coins }); }
      data.coins -= RENAME_COST; data.renames = (+data.renames || 0) + 1;
      if (!(await store.rename(u.lname, nl, name, data, rpOf(data)))) return out(409, { err: 'ชื่อนี้มีคนใช้แล้ว ลองชื่ออื่น' });
      console.log(`rename: ${u.name} → ${name}`);
      const nu = { ...u, lname: nl, name, data };   // สิทธิ์ผู้ดูแลผูกกับชื่อ → เปลี่ยนชื่อแล้วหมดสิทธิ์ (ถ้าชื่อใหม่ไม่อยู่ใน ADMINS)
      return out(200, { token: makeToken({ lname: nl, salt: u.salt }), name, data: withAdmin(nu, AC.seedOnline(data)), admin: isAdmin(nu) || undefined, cost: RENAME_COST });
    }
    if (p === '/api/recovery') { const rc = makeRecovery(); await store.setRecovery(u.lname, rc.rhash); return out(200, { code: rc.code }); }
    return out(404, { err: 'not found' });
  } catch (e) {
    console.error('api error', e.message);
    return out(503, { err: 'ระบบบัญชีมีปัญหาชั่วคราว ลองใหม่อีกครั้ง' });
  }
}
module.exports = { handleApi, storeKind: () => store.kind, tokenUser, addPlay, reviewOf };
