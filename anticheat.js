// รถไฟซ่า.io — ตรวจข้อมูลที่เครื่องผู้เล่นส่งมาบันทึก (กันโกงเหรียญ / RP / ของในร้าน)
// หลักการ: เซิร์ฟเวอร์เทียบกับข้อมูลเดิมในฐานข้อมูล
//   • ของที่ซื้อใหม่ต้องมีอยู่จริงในร้าน และหักเหรียญตามราคาจริง
//   • เหรียญ/RP ที่เพิ่มขึ้นต้องไม่เร็วเกินที่เล่นได้จริง (ถังโควตาเติมตามเวลา) + โควตาพิเศษจากเหรียญตรา ภารกิจ และรางวัลฤดูกาล
//   • ถ้าเกิน → ตัดให้เหลือเท่าที่เป็นไปได้ แล้วส่งค่าที่แก้แล้วกลับไปให้เครื่องผู้เล่น
// ⚠️ ราคาต้องตรงกับ SHOP / LIMITED ใน public/index.html (tests/test_shop_sync.js เช็คให้)
const crypto = require('crypto');

const SHOP = {
  loco: { classic: 0, diesel: 25000, bullet: 60000, tram: 120000, metro: 250000, comet: 500000 },
  wagon: { gem: 0, cargo: 12000, coach: 18000, glass: 30000, mine: 22000, sweets: 25000, crystal: 35000, pearl: 40000, magma: 45000, vault: 50000, royal: 60000, cosmos: 80000 },
  smoke: { normal: 0, sparkle: 10000, bubbles: 15000, rainbow: 20000, snow: 25000, flame: 40000 },
  skin: { candy: 10000, galaxy: 15000, lava: 15000, neon: 25000, mango: 12000, matcha: 12000, thaitea: 14000, bubblegum: 15000, toxic: 20000, rosegold: 22000, chrome: 25000, blackice: 30000, opal: 35000 },
  kfx: { none: 0, firework: 15000, gems: 20000, ring: 25000, confetti: 30000, coins: 35000, bolt: 45000 },
  horn: { classic: 0, deep: 20000, chime: 35000, tune: 60000, siren: 100000, thunder: 180000, dragon: 300000 },
  title: { speed: 10000, gemking: 25000, rich: 60000, zaab: 15000, maiwai: 12000, pang: 15000, tueng: 18000, tuamae: 18000, tuengpria: 22000, koentan: 25000, jaopo: 35000, storm: 40000, ninja: 45000, speeddemon: 50000, irondragon: 60000, reaper: 80000, unbeaten: 100000 },
};
const LIMITED = [['skin', 'sunset', 22000], ['skin', 'ocean', 22000], ['skin', 'sakura', 24000], ['skin', 'aurora', 28000], ['skin', 'royal', 30000],
  ['smoke', 'hearts', 26000], ['smoke', 'leaves', 22000], ['title', 'lucky', 20000], ['title', 'night', 24000],
  ['skin', 'mint', 20000], ['skin', 'peacock', 26000], ['skin', 'ember', 24000], ['skin', 'midnight', 28000], ['title', 'gemhunter', 22000], ['title', 'stationmaster', 20000], ['title', 'speedking', 26000]];
const SALE = 0.7;
const CATS = Object.keys(SHOP);
const SALE_POOL = CATS.flatMap(c => Object.entries(SHOP[c]).filter(([, p]) => p > 0).map(([id, p]) => [c, id, p]));
const ACH_IDS = ['k1', 'k100', 'l500', 'l1000', 'b3', 'g1', 'boss', 'st20', 'w100', 'hard1', 'team', 'rich'];
const ACH_COINS = 300;
const RANK_MIN = [0, 600, 2500, 6000, 12000, 25000, 50000];
// รางวัลจบฤดูกาลตามอันดับ (เจ้าของสั่ง 7 พ.ย.): [อันดับถึง, เหรียญ] เต็มจำนวนเมื่อมีผู้เล่นติดอันดับ ≥ 50 คน · น้อยกว่านั้นลดตามสัดส่วน (ต่ำสุด 10%)
// ต้องตรงกับ PRIZE_BANDS / seasonPrize ใน public/index.html
const PRIZE_BANDS = [[1, 50000], [2, 35000], [3, 25000], [10, 10000], [20, 5000], [50, 2500], [100, 1000], [Infinity, 300]], PRIZE_FULL = 50;
const prizeScale = n => Math.min(1, Math.max(0.1, n / PRIZE_FULL));
function seasonPrize(pos, n) { if (!(pos >= 1) || !(n >= 1)) return 0; const b = PRIZE_BANDS.find(x => pos <= x[0])[1]; return Math.max(100, Math.round(b * prizeScale(n) / 100) * 100); }
const prevSeason = k => { let y = +k.slice(0, 4), m = +k.slice(5, 7) - 1; if (m < 1) { m = 12; y--; } return y + '-' + String(m).padStart(2, '0'); };
// โควตา: เหรียญเก็บได้สูงสุด 5,000 ต่อรอบ เติม 15/วินาที (900/นาที) · RP สูงสุด 400 เติม 1/วินาที
const RANK_ZERO = ['2026-12'];   // ฤดูกาลที่แรงก์เริ่มใหม่จาก 0 ทุกคน (เจ้าของสั่ง 13 พ.ย. 2026)
const COIN_CAP = 5000, COIN_RATE = 15, RP_CAP = 400, RP_RATE = 1, MISSION_MAX = 360;   // รางวัลภารกิจรายวันสูงสุด (เพิ่ม 20% 12 พ.ย.: 300→360)
// ลงทะเบียนครั้งแรก (ย้ายเหรียญ Guest/ข้อมูลเก่าในเครื่องเข้าบัญชี): เหรียญ+มูลค่าของรวมได้ไม่เกิน 60,000 และ RP ไม่เกิน 6,000
const REG_COINS = 60000, REG_RP = 6000;

function hashStr(s) { let h = 2166136261; for (const c of s) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; }
const bkkDay = (o = 0, now = Date.now()) => new Date(now + 7 * 36e5 + o * 864e5).toISOString().slice(0, 10);
const seasonKey = (now = Date.now()) => bkkDay(0, now).slice(0, 7);
// ร้านวันนี้: ของหายาก 1 + ลดราคา 1 (ลด 20–40%) ไม่ซ้ำวันติดกัน · ต้องตรงกับ dealOf ใน public/index.html (tests/test_shop_sync.js เช็คให้)
function mulberry(a) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const DEAL_OFFS = [20, 25, 30, 35, 40];
function dealPick(tag, n, dn) { const raw = k => { const R = mulberry(hashStr(tag + k)), a = [...Array(n).keys()]; for (let i = n - 1; i > 0; i--) { const j = Math.floor(R() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const w = Math.min(7, Math.floor(n / 3)), k = Math.floor(dn / n), a = raw(k), tail = new Set(raw(k - 1).slice(n - w));
  for (let i = 0; i < w; i++) if (tail.has(a[i])) for (let j = w; j < n - w; j++) if (!tail.has(a[j])) { [a[i], a[j]] = [a[j], a[i]]; break; }
  return a[dn - k * n]; }
function dealOf(day) { const dn = Math.round(Date.parse(day + 'T00:00:00Z') / 864e5), R = mulberry(hashStr('deal:' + day));
  const lims = [LIMITED[dealPick('dealL:', LIMITED.length, dn)]], s = SALE_POOL[dealPick('dealS:', SALE_POOL.length, dn)], off = DEAL_OFFS[Math.floor(R() * DEAL_OFFS.length)];
  const sales = [[s[0], s[1], s[2], off, Math.round(s[2] * (100 - off) / 100 / 100) * 100]];
  return { lims, sales }; }
const tierOf = rp => { let t = 0; while (t < RANK_MIN.length - 1 && rp >= RANK_MIN[t + 1]) t++; return t; };

// ราคาที่ถูกที่สุดที่ซื้อของชิ้นนี้ได้ตอนนี้ (null = ซื้อไม่ได้ / ไม่มีในร้าน)
function priceFor(cat, id, now) {
  if (cat === 'title' && /^S:\d{4}-\d{2}:[0-6]$/.test(id)) return id.slice(2, 9) < seasonKey(now) ? 0 : null;   // ฉายาฤดูกาลที่จบไปแล้ว
  let best = SHOP[cat] && SHOP[cat][id] !== undefined ? SHOP[cat][id] : null;
  for (const o of [-1, 0, 1]) {   // เผื่อเวลาเครื่องต่างกันข้ามเที่ยงคืน
    const d = dealOf(bkkDay(o, now));
    for (const l of d.lims) if (l[0] === cat && l[1] === id) best = best === null ? l[2] : Math.min(best, l[2]);
    for (const s of d.sales) if (s[0] === cat && s[1] === id) best = best === null ? s[4] : Math.min(best, s[4]);
  }
  return best;
}
function dayOk(k, now) {   // วันที่ของภารกิจรายวัน (รูปแบบ ปี-เดือน-วัน ของเครื่องผู้เล่น) ต้องห่างจากวันนี้ไม่เกิน ~1 วัน
  const m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(String(k || '')); if (!m) return false;
  return Math.abs(Date.UTC(+m[1], +m[2] - 1, +m[3]) + 12 * 36e5 - now) < 40 * 36e5;
}
const num = v => Math.max(0, Math.floor(+v || 0));

// old = ข้อมูลที่เซิร์ฟเวอร์มี (null = ลงทะเบียนใหม่), nu = ข้อมูลที่เครื่องส่งมา → { data, fixed }
function validate(old, nu, now = Date.now(), prize = 0) {   // prize = เหรียญรางวัลจบฤดูกาลที่เซิร์ฟเวอร์คำนวณจากอันดับ (ถ้าข้อมูลนี้ขึ้นฤดูกาลใหม่)
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
  if (dl && Array.isArray(dl.m) && dayOk(dl.date, now)) dl.m.slice(0, 5).forEach((m, i) => {
    const k = dl.date + ':' + i; if (m && m.c && !claims.has(k)) { claims.add(k); extra += Math.min(MISSION_MAX, num(m.r)); } });
  // รางวัลจบฤดูกาล
  const cur = seasonKey(now);
  if (nu.season === cur && old.season && old.season < cur && srv.sp !== cur) { extra += Math.max(0, +prize || 0); srv.sp = cur; }
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
  // ฤดูกาลที่แรงก์เริ่มใหม่จาก 0 (RANK_ZERO ต้องตรงกับ index.html): บันทึกแรกที่ขึ้นฤดูกาลนี้ → RP ไม่เกิน 200 (เผื่อเกมแรกของเดือน) · เครื่องเก่าที่ยังหารครึ่ง → โดนปรับ
  if (RANK_ZERO.includes(seasonKey(now)) && nu.season === seasonKey(now) && old.season && old.season < nu.season && rp > 200) { rp = 200; fixed = true; }
  if (rp > orp) { const g = rp - orp; if (g > srv.rb) { rp = orp + Math.floor(srv.rb); srv.rb = 0; fixed = true; } else srv.rb -= g; }
  // สถิติ: ต้องเป็นตัวเลข · ความยาวสูงสุด (ใช้ในตารางอันดับ) เพิ่มได้ไม่เกิน 300 + 40/วินาที (ลงทะเบียนครั้งแรกไม่เกิน 3,000)
  const st = {}, ist = nu.st && typeof nu.st === 'object' ? nu.st : {};
  for (const k of Object.keys(ist).slice(0, 60)) { const v = +ist[k]; st[k] = Number.isFinite(v) ? Math.max(0, Math.min(1e7, v)) : 0; }
  const oml = +((old.st || {}).maxLen) || 0, mlCap = reg ? 3000 : oml + 300 + 40 * Math.min(el, 600);
  if ((st.maxLen || 0) > Math.max(oml, mlCap)) { st.maxLen = Math.floor(Math.max(oml, mlCap)); fixed = true; }
  // สถิติออนไลน์: RP ออนไลน์เพิ่มได้ไม่เกิน RP ที่เพิ่มจริง (และไม่เกิน RP ทั้งหมด) · กำจัด/ยาวสุดออนไลน์ไม่เกินของรวม · เครื่องเก่าที่ไม่ส่งค่า → ใช้ค่าเดิม
  { const so = seedOnline(old), newSeason = nu.season && so.season && nu.season > so.season, ost = so.st || {};
    nu = { ...nu, onrp: rp, onv: 2 };   // RP ได้เฉพาะออนไลน์แล้ว → RP ออนไลน์ = RP (ผ่านกันโกง rp แล้ว)
    if (!('okills' in ist)) st.okills = Math.floor((+ost.okills || 0) + Math.max(0, (st.kills || 0) - (+ost.kills || 0)));   // เครื่องเก่า: นับกำจัดที่เพิ่มด้วย
    if (!('omaxLen' in ist)) st.omaxLen = Math.floor(Math.max(+ost.omaxLen || 0, st.maxLen || 0));
    if (st.okills > Math.max(+ost.okills || 0, st.kills || 0)) { st.okills = Math.floor(Math.max(+ost.okills || 0, st.kills || 0)); fixed = true; }
    const omc = Math.max(+ost.omaxLen || 0, Math.min(st.maxLen || 0, reg ? 3000 : (+ost.omaxLen || 0) + 300 + 40 * Math.min(el, 600)));
    if (st.omaxLen > omc) { st.omaxLen = Math.floor(omc); fixed = true; } }
  srv.paid = [...paid]; srv.claims = [...claims].slice(-30);
  if (reg) { srv.cb = Math.min(srv.cb, COIN_CAP); srv.rb = Math.min(srv.rb, RP_CAP); }   // โควตาย้ายข้อมูลใช้ได้ตอนลงทะเบียนครั้งเดียว
  srv.cb = Math.round(srv.cb * 100) / 100; srv.rb = Math.round(srv.rb * 100) / 100;
  // ของที่ใส่อยู่ต้องเป็นของที่มีจริง (ฉายาโชว์ในตารางอันดับ) ไม่งั้นกลับเป็นค่าเริ่มต้น
  const DEF = { loco: 'classic', wagon: 'gem', smoke: 'normal', kfx: 'none', horn: 'classic', title: '' }, eq = { ...DEF, ...(nu.eq && typeof nu.eq === 'object' ? nu.eq : {}) };
  for (const c of Object.keys(DEF)) { const v = String(eq[c] || ''); if (v === DEF[c]) continue;
    const ok = c === 'title' && v.startsWith('a:') ? paid.has(v.slice(2)) : owned[c].includes(v); if (!ok) eq[c] = DEF[c]; }
  return { data: { ...nu, coins, rp, owned, st, eq, _srv: srv }, fixed };
}

// ---------- สถิติออนไลน์ (ตารางอันดับนับเฉพาะโหมดออนไลน์ — เจ้าของสั่ง 7 พ.ย. 18:45 เอาโหมดเล่นกับบอทออก) ----------
// onrp = RP ออนไลน์ของฤดูกาลนี้ (เรียงตารางอันดับ/แจกรางวัลจบเดือน) · st.okills = กำจัดในโหมดออนไลน์ · st.omaxLen = ยาวสุดในโหมดออนไลน์
// ข้อมูลเก่าที่ยังไม่มีค่าพวกนี้: ยกคะแนนเดิมมาทั้งหมด (เจ้าของสั่ง 7 พ.ย. 18:56 — ไม่ลบคะแนนเดิมของคนที่เคยเล่นกับบอท) · ต่อจากนี้นับเพิ่มเฉพาะออนไลน์
// onv:2 (7 พ.ย. 20:15): เครื่องเก่าที่ยังเปิดค้างหลังอัปเดตส่ง RP/กำจัดเพิ่มแต่ไม่ส่งค่าออนไลน์ → ตารางอันดับไม่ขยับ · ตอนนี้ไม่มีโหมดบอทแล้ว RP ได้เฉพาะออนไลน์ → onrp = rp เสมอ
function seedOnline(d) { d = d && typeof d === 'object' ? d : {}; if (d.onv === 2) return d;
  const st = { ...(d.st || {}) };
  st.okills = Math.floor(Math.max(+st.okills || 0, +st.kills || 0)); st.omaxLen = Math.floor(Math.max(+st.omaxLen || 0, +st.maxLen || 0, +((d.best || {}).online) || 0));
  return { ...d, onrp: Math.max(0, Math.floor(+d.rp || 0)), onv: 2, st }; }

// ---------- รหัสกู้คืน ----------
const RC_ABC = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
function newRecovery() { const b = crypto.randomBytes(12); let s = ''; for (let i = 0; i < 12; i++) { s += RC_ABC[b[i] % RC_ABC.length]; if (i === 3 || i === 7) s += '-'; } return s; }
const normRecovery = c => String(c || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
const hashRecovery = (code, salt) => crypto.createHash('sha256').update('rc:' + salt + ':' + normRecovery(code)).digest('hex');

module.exports = { RANK_ZERO, validate, seedOnline, seasonPrize, prevSeason, PRIZE_BANDS, priceFor, dealOf, seasonKey, bkkDay, newRecovery, hashRecovery, SHOP, LIMITED, SALE_POOL, CATS, COIN_CAP, RP_CAP };
