// รถไฟซ่า.io — ตรวจข้อมูลที่เครื่องผู้เล่นส่งมาบันทึก (กันโกงเหรียญ / RP / ของในร้าน)
// หลักการ: เซิร์ฟเวอร์เทียบกับข้อมูลเดิมในฐานข้อมูล
//   • ของที่ซื้อใหม่ต้องมีอยู่จริงในร้าน และหักเหรียญตามราคาจริง
//   • เหรียญ/RP ที่เพิ่มขึ้นต้องไม่เร็วเกินที่เล่นได้จริง (ถังโควตาเติมตามเวลา) + โควตาพิเศษจากเหรียญตรา ภารกิจ และรางวัลฤดูกาล
//   • ถ้าเกิน → ตัดให้เหลือเท่าที่เป็นไปได้ แล้วส่งค่าที่แก้แล้วกลับไปให้เครื่องผู้เล่น
// ⚠️ ราคาต้องตรงกับ SHOP / LIMITED ใน public/index.html (tests/test_shop_sync.js เช็คให้)
const crypto = require('crypto');

const SHOP = {
  loco: { classic: 0, diesel: 15000, bullet: 30000, tram: 40000, metro: 55000, comet: 80000 },
  wagon: { gem: 0, cargo: 12000, coach: 18000, glass: 30000 },
  smoke: { normal: 0, sparkle: 10000, rainbow: 20000 },
  skin: { candy: 10000, galaxy: 15000, lava: 15000, neon: 25000 },
  kfx: { none: 0, firework: 15000, gems: 20000, coins: 35000 },
  horn: { classic: 0, deep: 8000, chime: 12000, tune: 18000 },
  title: { speed: 10000, gemking: 25000, rich: 60000 },
};
const LIMITED = [['skin', 'sunset', 22000], ['skin', 'ocean', 22000], ['skin', 'sakura', 24000], ['skin', 'aurora', 28000], ['skin', 'royal', 30000],
  ['smoke', 'hearts', 26000], ['smoke', 'leaves', 22000], ['title', 'lucky', 20000], ['title', 'night', 24000]];
const SALE = 0.7;
const CATS = Object.keys(SHOP);
const SALE_POOL = CATS.flatMap(c => Object.entries(SHOP[c]).filter(([, p]) => p > 0).map(([id, p]) => [c, id, p]));
const ACH_IDS = ['k1', 'k100', 'l500', 'l1000', 'b3', 'g1', 'boss', 'st20', 'w100', 'hard1', 'team', 'rich'];
const ACH_COINS = 300;
const RANK_MIN = [0, 600, 2500, 6000, 12000, 25000, 50000];
const SEASON_COINS = [500, 1500, 3000, 6000, 10000, 15000, 25000];
// โควตา: เหรียญเก็บได้สูงสุด 5,000 ต่อรอบ เติม 15/วินาที (900/นาที) · RP สูงสุด 400 เติม 1/วินาที
const COIN_CAP = 5000, COIN_RATE = 15, RP_CAP = 400, RP_RATE = 1, MISSION_MAX = 300;
// ลงทะเบียนครั้งแรก (ย้ายเหรียญ Guest/ข้อมูลเก่าในเครื่องเข้าบัญชี): เหรียญ+มูลค่าของรวมได้ไม่เกิน 60,000 และ RP ไม่เกิน 6,000
const REG_COINS = 60000, REG_RP = 6000;

function hashStr(s) { let h = 2166136261; for (const c of s) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; }
const bkkDay = (o = 0, now = Date.now()) => new Date(now + 7 * 36e5 + o * 864e5).toISOString().slice(0, 10);
const seasonKey = (now = Date.now()) => bkkDay(0, now).slice(0, 7);
function dealOf(day) { const h = hashStr('deal:' + day), s = SALE_POOL[(h >>> 8) % SALE_POOL.length], l = LIMITED[h % LIMITED.length];
  return { lim: l, sale: s, salePrice: Math.round(s[2] * SALE / 100) * 100 }; }
const tierOf = rp => { let t = 0; while (t < RANK_MIN.length - 1 && rp >= RANK_MIN[t + 1]) t++; return t; };

// ราคาที่ถูกที่สุดที่ซื้อของชิ้นนี้ได้ตอนนี้ (null = ซื้อไม่ได้ / ไม่มีในร้าน)
function priceFor(cat, id, now) {
  if (cat === 'title' && /^S:\d{4}-\d{2}:[0-6]$/.test(id)) return id.slice(2, 9) < seasonKey(now) ? 0 : null;   // ฉายาฤดูกาลที่จบไปแล้ว
  let best = SHOP[cat] && SHOP[cat][id] !== undefined ? SHOP[cat][id] : null;
  for (const o of [-1, 0, 1]) {   // เผื่อเวลาเครื่องต่างกันข้ามเที่ยงคืน
    const d = dealOf(bkkDay(o, now));
    if (d.lim[0] === cat && d.lim[1] === id) best = best === null ? d.lim[2] : Math.min(best, d.lim[2]);
    if (d.sale[0] === cat && d.sale[1] === id) best = best === null ? d.salePrice : Math.min(best, d.salePrice);
  }
  return best;
}
function dayOk(k, now) {   // วันที่ของภารกิจรายวัน (รูปแบบ ปี-เดือน-วัน ของเครื่องผู้เล่น) ต้องห่างจากวันนี้ไม่เกิน ~1 วัน
  const m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(String(k || '')); if (!m) return false;
  return Math.abs(Date.UTC(+m[1], +m[2] - 1, +m[3]) + 12 * 36e5 - now) < 40 * 36e5;
}
const num = v => Math.max(0, Math.floor(+v || 0));

// old = ข้อมูลที่เซิร์ฟเวอร์มี (null = ลงทะเบียนใหม่), nu = ข้อมูลที่เครื่องส่งมา → { data, fixed }
function validate(old, nu, now = Date.now()) {
  const reg = !old; old = old || { coins: 0, rp: 0, owned: {}, ach: {} };
  const o0 = old._srv;
  const srv = o0 ? { ...o0 } : { cb: reg ? REG_COINS : COIN_CAP, rb: reg ? REG_RP : RP_CAP, t: now,
    paid: Object.keys(old.ach || {}), claims: ((old.daily || {}).m || []).map((m, i) => m.c ? old.daily.date + ':' + i : null).filter(Boolean), sp: '' };
  const el = o0 ? Math.max(0, (now - (+srv.t || now)) / 1000) : 0;
  if (o0) { srv.cb = Math.min(COIN_CAP, (+srv.cb || 0) + el * COIN_RATE); srv.rb = Math.min(RP_CAP, (+srv.rb || 0) + el * RP_RATE); }
  srv.t = now;
  let fixed = false, extra = 0, spent = 0;
  // เหรียญตรา (ได้ครั้งเดียวต่อเหรียญ ตลอดไป)
  const paid = new Set(srv.paid || []);
  for (const k of Object.keys(nu.ach || {})) if (ACH_IDS.includes(k) && !paid.has(k)) { paid.add(k); extra += ACH_COINS; }
  // ภารกิจรายวันที่กดรับ
  const claims = new Set(srv.claims || []), dl = nu.daily;
  if (dl && Array.isArray(dl.m) && dayOk(dl.date, now)) dl.m.slice(0, 3).forEach((m, i) => {
    const k = dl.date + ':' + i; if (m && m.c && !claims.has(k)) { claims.add(k); extra += Math.min(MISSION_MAX, num(m.r)); } });
  // รางวัลจบฤดูกาล
  const cur = seasonKey(now);
  if (nu.season === cur && old.season && old.season < cur && srv.sp !== cur) { extra += SEASON_COINS[tierOf(num(old.rp))]; srv.sp = cur; }
  // ของในร้าน: ของใหม่ต้องมีจริงในร้าน และต้องมีเหรียญพอจ่าย (เหรียญเดิม + ที่หาได้จริง) ไม่พอ → เอาชิ้นแพงสุดออกก่อน
  const owned = {}, oo = old.owned || {}, no = nu.owned && typeof nu.owned === 'object' ? nu.owned : {}, buys = [];
  for (const c of CATS) {
    const have = new Set(Array.isArray(oo[c]) ? oo[c] : []);
    for (const id of Array.isArray(no[c]) ? no[c].slice(0, 80) : []) {
      if (typeof id !== 'string' || have.has(id) || buys.some(b => b[0] === c && b[1] === id)) continue;
      const p = priceFor(c, id, now);
      if (p === null) { fixed = true; continue; }
      buys.push([c, id, p]);
    }
    owned[c] = [...have];
  }
  const oc = num(old.coins), canPay = oc + extra + srv.cb;
  buys.sort((x, y) => y[2] - x[2]); spent = buys.reduce((n, b) => n + b[2], 0);
  while (buys.length && spent > canPay) { spent -= buys.shift()[2]; fixed = true; }
  for (const [c, id] of buys) owned[c].push(id);
  // เหรียญ
  const want = num(nu.coins) - oc + spent;
  let coins = num(nu.coins);
  if (want > extra) { const need = want - extra;
    if (need > srv.cb) { coins = Math.max(0, oc - spent + extra + Math.floor(srv.cb)); srv.cb = 0; fixed = true; } else srv.cb -= need; }
  // RP (ลดลงได้เสมอ เช่น โดนหัก / ขึ้นฤดูกาลใหม่)
  const orp = num(old.rp); let rp = Math.min(1e7, num(nu.rp));
  if (rp > orp) { const g = rp - orp; if (g > srv.rb) { rp = orp + Math.floor(srv.rb); srv.rb = 0; fixed = true; } else srv.rb -= g; }
  // สถิติ: ต้องเป็นตัวเลข · ความยาวสูงสุด (ใช้ในตารางอันดับ) เพิ่มได้ไม่เกิน 300 + 40/วินาที (ลงทะเบียนครั้งแรกไม่เกิน 3,000)
  const st = {}, ist = nu.st && typeof nu.st === 'object' ? nu.st : {};
  for (const k of Object.keys(ist).slice(0, 60)) { const v = +ist[k]; st[k] = Number.isFinite(v) ? Math.max(0, Math.min(1e7, v)) : 0; }
  const oml = +((old.st || {}).maxLen) || 0, mlCap = reg ? 3000 : oml + 300 + 40 * Math.min(el, 600);
  if ((st.maxLen || 0) > Math.max(oml, mlCap)) { st.maxLen = Math.floor(Math.max(oml, mlCap)); fixed = true; }
  srv.paid = [...paid]; srv.claims = [...claims].slice(-30);
  if (reg) { srv.cb = Math.min(srv.cb, COIN_CAP); srv.rb = Math.min(srv.rb, RP_CAP); }   // โควตาย้ายข้อมูลใช้ได้ตอนลงทะเบียนครั้งเดียว
  srv.cb = Math.round(srv.cb * 100) / 100; srv.rb = Math.round(srv.rb * 100) / 100;
  // ของที่ใส่อยู่ต้องเป็นของที่มีจริง (ฉายาโชว์ในตารางอันดับ) ไม่งั้นกลับเป็นค่าเริ่มต้น
  const DEF = { loco: 'classic', wagon: 'gem', smoke: 'normal', kfx: 'none', horn: 'classic', title: '' }, eq = { ...DEF, ...(nu.eq && typeof nu.eq === 'object' ? nu.eq : {}) };
  for (const c of Object.keys(DEF)) { const v = String(eq[c] || ''); if (v === DEF[c]) continue;
    const ok = c === 'title' && v.startsWith('a:') ? paid.has(v.slice(2)) : owned[c].includes(v); if (!ok) eq[c] = DEF[c]; }
  return { data: { ...nu, coins, rp, owned, st, eq, _srv: srv }, fixed };
}

// ---------- รหัสกู้คืน ----------
const RC_ABC = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
function newRecovery() { const b = crypto.randomBytes(12); let s = ''; for (let i = 0; i < 12; i++) { s += RC_ABC[b[i] % RC_ABC.length]; if (i === 3 || i === 7) s += '-'; } return s; }
const normRecovery = c => String(c || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
const hashRecovery = (code, salt) => crypto.createHash('sha256').update('rc:' + salt + ':' + normRecovery(code)).digest('hex');

module.exports = { validate, priceFor, dealOf, seasonKey, bkkDay, newRecovery, hashRecovery, SHOP, LIMITED, CATS, COIN_CAP, RP_CAP };
