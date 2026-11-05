// รถไฟซ่า.io — ระบบบัญชีผู้เล่น (ลงทะเบียน / เข้าสู่ระบบ / บันทึกเหรียญ-แรงก์ / ตารางอันดับ)
// มี DATABASE_URL (Postgres เช่น Neon) → เก็บในฐานข้อมูล · ไม่มี → เก็บในไฟล์ data/users.json (ไว้ทดสอบในเครื่องเท่านั้น)
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const DB_URL = process.env.DATABASE_URL || '';
const SECRET = process.env.TOKEN_SECRET || crypto.createHash('sha256').update('rotfai:' + (DB_URL || 'dev-secret')).digest('hex');
const MAX_DATA = 40 * 1024;

// ---------- storage ----------
let store;
function fileStore(note) {
  const FILE = path.join(__dirname, 'data', 'users.json');
  let db = {}; try { db = JSON.parse(fs.readFileSync(FILE, 'utf8')); } catch (e) {}
  let t = null; const flush = () => { clearTimeout(t); t = setTimeout(() => { fs.mkdirSync(path.dirname(FILE), { recursive: true }); fs.writeFileSync(FILE, JSON.stringify(db)); }, 300); };
  console.log('accounts: ' + note);
  return {
    kind: 'file', note, ready: Promise.resolve(),
    async get(l) { return db[l] || null; },
    async create(u) { if (db[u.lname]) return false; db[u.lname] = u; flush(); return true; },
    async save(l, data, rp) { if (db[l]) { db[l].data = data; db[l].rp = rp; db[l].updated = Date.now(); flush(); } },
    async top(n) { return Object.values(db).sort((a, b) => b.rp - a.rp).slice(0, n).map(u => ({ name: u.name, rp: u.rp })); },
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
    async top(n) { await ready; if (store !== dbStore) return store.top(n); const r = await pool.query('SELECT name, rp FROM players ORDER BY rp DESC, updated ASC LIMIT $1', [n]); return r.rows; },
  };
  store = dbStore;
} else {
  store = fileStore('no DATABASE_URL → using local file (test only, data is lost when the server restarts on Render)');
}

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

// ---------- API ----------
async function handleApi(req, res, p) {
  const out = (code, o) => { res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }); res.end(JSON.stringify(o)); };
  try {
    if (p === '/api/status') { await store.ready.catch(() => {}); return out(200, { accounts: true, store: store.kind, dbError: store.dbError || undefined }); }
    if (p === '/api/top' && req.method === 'GET') return out(200, { top: await store.top(30) });
    if (req.method === 'GET' && p === '/api/me') {
      const u = await authUser(req); if (!u) return out(401, { err: 'กรุณาเข้าสู่ระบบใหม่' });
      return out(200, { name: u.name, data: u.data });
    }
    if (req.method !== 'POST') return out(404, { err: 'not found' });
    const body = await readBody(req);
    if (p === '/api/register' || p === '/api/login') {
      if (limited(req)) return out(429, { err: 'ลองบ่อยเกินไป รอสักครู่แล้วลองใหม่' });
      const name = cleanName(body.name), pass = String(body.pass || '');
      if ([...name].length < 2 || [...name].length > 14) return out(400, { err: 'ชื่อต้องยาว 2–14 ตัวอักษร' });
      if (pass.length < 4 || pass.length > 64) return out(400, { err: 'รหัสผ่านต้องยาว 4 ตัวขึ้นไป' });
      const l = lower(name);
      if (p === '/api/register') {
        const data = cleanData(body.data); if (data === null) return out(400, { err: 'ข้อมูลใหญ่เกินไป' });
        const salt = crypto.randomBytes(16).toString('hex'), u = { lname: l, name, salt, hash: await hashPass(pass, salt), data, rp: rpOf(data) };
        if (!(await store.create(u))) return out(409, { err: 'ชื่อนี้มีคนใช้แล้ว ลองชื่ออื่น' });
        return out(200, { token: makeToken(u), name, data });
      }
      const u = await store.get(l);
      if (!u || (await hashPass(pass, u.salt)) !== u.hash) return out(401, { err: 'ชื่อหรือรหัสผ่านไม่ถูกต้อง' });
      return out(200, { token: makeToken(u), name: u.name, data: u.data });
    }
    if (p === '/api/save') {
      const u = await authUser(req); if (!u) return out(401, { err: 'กรุณาเข้าสู่ระบบใหม่' });
      const data = cleanData(body.data); if (data === null) return out(400, { err: 'ข้อมูลใหญ่เกินไป' });
      await store.save(u.lname, data, rpOf(data));
      return out(200, { ok: true });
    }
    return out(404, { err: 'not found' });
  } catch (e) {
    console.error('api error', e.message);
    return out(503, { err: 'ระบบบัญชีมีปัญหาชั่วคราว ลองใหม่อีกครั้ง' });
  }
}
module.exports = { handleApi, storeKind: () => store.kind };
