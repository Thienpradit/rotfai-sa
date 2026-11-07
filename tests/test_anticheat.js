// ทดสอบการตรวจเหรียญ/RP/ของในร้านฝั่งเซิร์ฟเวอร์   รัน: node tests/test_anticheat.js
const assert = require('assert'), AC = require('../anticheat');
const T0 = Date.UTC(2026, 10, 6, 6);   // 6 พ.ย. 2026 13:00 เวลาไทย
const base = () => ({ coins: 1000, rp: 100, owned: { loco: ['classic'] }, ach: {}, season: '2026-11' });
const step = (old, nu, dt = 20) => AC.validate(old, nu, T0 + dt * 1000);
let r, o;
// 1) เล่นปกติ: ได้ 800 เหรียญ 40 RP → ผ่าน
o = AC.validate(base(), base(), T0).data;
r = step(o, { ...o, coins: 1800, rp: 140 }); assert(!r.fixed); assert.strictEqual(r.data.coins, 1800); assert.strictEqual(r.data.rp, 140);
// 2) แก้เหรียญเป็นล้าน → ถูกตัดเหลือแค่โควตา (≤ 5,000)
r = step(o, { ...o, coins: 1e6 }); assert(r.fixed); assert(r.data.coins <= 1000 + AC.COIN_CAP, r.data.coins);
// 3) ส่งซ้ำรัว ๆ ทุก 1 วิ ก็ได้ไม่เกินโควตาที่เติมตามเวลา
let d = o, t = 0; for (let i = 0; i < 30; i++) { t += 1; d = AC.validate(d, { ...d, coins: d.coins + 5000 }, T0 + t * 1000).data; }
assert(d.coins <= 1000 + AC.COIN_CAP + 30 * 15 + 1, d.coins);
// 4) ซื้อหัวจักรดีเซลแต่ไม่หักเหรียญ → ต้องหักจากโควตา (เกิน → ตัดเหรียญ)
const DP = AC.SHOP.loco.diesel, C0 = DP + 5000;
o = { ...base(), coins: C0, _srv: { cb: 5000, rb: 400, t: T0, paid: [], claims: [] } };
r = step(o, { ...o, owned: { loco: ['classic', 'diesel'] } }); assert(r.fixed); assert(r.data.owned.loco.includes('diesel')); assert(r.data.coins <= C0 - DP + 5000 + 300);
// 5) ซื้อถูกต้อง (หักเหรียญแล้ว) → ผ่าน
r = step(o, { ...o, coins: C0 - DP, owned: { loco: ['classic', 'diesel'] } }); assert(!r.fixed); assert.strictEqual(r.data.coins, C0 - DP);
// 6) ของที่ไม่มีในร้าน → ถูกเอาออก
r = step(o, { ...o, owned: { loco: ['classic', 'golden-hack'] } }); assert(r.fixed); assert(!r.data.owned.loco.includes('golden-hack'));
// 7) ของหายากซื้อได้เฉพาะวันที่ขาย
const deal = AC.dealOf(AC.bkkDay(0, T0)), [lc, lid, lp] = deal.lim;
o = { ...o, coins: 40000, owned: { loco: ['classic'] } };
r = step(o, { ...o, coins: 40000 - lp, owned: { ...o.owned, [lc]: [lid] } }); assert(!r.fixed, 'ซื้อของหายากของวันนี้ต้องผ่าน');
const other = AC.LIMITED.find(l => ![-1, 0, 1].some(k => AC.dealOf(AC.bkkDay(k, T0)).lim[1] === l[1]));
r = step(o, { ...o, coins: 40000 - other[2], owned: { ...o.owned, [other[0]]: [other[1]] } }); assert(r.fixed); assert(!r.data.owned[other[0]].includes(other[1]), 'ของหายากที่ไม่ได้ขายวันนี้ต้องซื้อไม่ได้');
// 8) ปลดเหรียญตรา → ได้ 300 เพิ่มจากโควตา, ปลดซ้ำไม่ได้อีก
o = { ...base(), _srv: { cb: 0, rb: 0, t: T0, paid: [], claims: [] } };
r = step(o, { ...o, coins: 1300, ach: { k1: 1 } }, 0); assert(!r.fixed); assert.strictEqual(r.data.coins, 1300);
r = step({ ...r.data, ach: {} }, { ...r.data, coins: 1600, ach: { k1: 1 } }, 0); assert(r.fixed); assert.strictEqual(r.data.coins, 1300);
// 9) RP เพิ่มเร็วเกิน → ตัด, RP ลดลงได้เสมอ
o = { ...base(), _srv: { cb: 0, rb: 50, t: T0, paid: [], claims: [] } };
r = step(o, { ...o, rp: 99999 }, 0); assert(r.fixed); assert.strictEqual(r.data.rp, 150);
r = step(o, { ...o, rp: 10 }, 0); assert(!r.fixed); assert.strictEqual(r.data.rp, 10);
// 10) รางวัลจบฤดูกาลตามอันดับ (เซิร์ฟเวอร์ส่งจำนวนเหรียญมา เช่น ที่ 2 จาก 60 คน = 35,000) ได้ครั้งเดียว · ไม่ได้รางวัล (prize 0) ใส่เหรียญเองไม่ได้
assert.strictEqual(AC.seasonPrize(2, 60), 35000); assert.strictEqual(AC.seasonPrize(7, 60), 10000); assert.strictEqual(AC.seasonPrize(150, 60), 300);
assert.strictEqual(AC.seasonPrize(1, 10), 10000); assert.strictEqual(AC.seasonPrize(1, 1), 5000); assert.strictEqual(AC.seasonPrize(0, 10), 0); assert.strictEqual(AC.prevSeason('2027-01'), '2026-12');
o = { coins: 0, rp: 3000, owned: {}, ach: {}, season: '2026-10', _srv: { cb: 0, rb: 0, t: T0, paid: [], claims: [] } };
r = AC.validate(o, { ...o, coins: 35000, rp: 1500, season: '2026-11', owned: { title: ['S:2026-10:2'] } }, T0, 35000); assert(!r.fixed, JSON.stringify(r.data)); assert.strictEqual(r.data.coins, 35000);
r = AC.validate(r.data, { ...r.data, coins: 70000, season: '2026-11' }, T0, 35000); assert(r.fixed); assert.strictEqual(r.data.coins, 35000);
r = AC.validate(o, { ...o, coins: 35000, rp: 1500, season: '2026-11' }, T0, 0); assert(r.fixed); assert.strictEqual(r.data.coins, 0);
// 11) ภารกิจรายวัน: กดรับได้ครั้งเดียวต่อข้อ
o = { ...base(), daily: { date: '2026-11-6', m: [{ id: 'kills', n: 5, r: 50, p: 5, c: false }] }, _srv: { cb: 0, rb: 0, t: T0, paid: [], claims: [] } };
r = step(o, { ...o, coins: 1050, daily: { date: '2026-11-6', m: [{ id: 'kills', n: 5, r: 50, p: 5, c: true }] } }, 0); assert(!r.fixed); assert.strictEqual(r.data.coins, 1050);
r = step(r.data, { ...r.data, coins: 1100 }, 0); assert(r.fixed); assert.strictEqual(r.data.coins, 1050);
// 12) ลงทะเบียน: ย้ายเหรียญ Guest มาได้ไม่เกิน 60,000 / RP 6,000
r = AC.validate(null, { coins: 5e6, rp: 5e5, owned: {} }, T0); assert(r.fixed); assert(r.data.coins <= 60000); assert(r.data.rp <= 6000);
r = AC.validate(null, { coins: 4000, rp: 300, owned: { loco: ['classic'] } }, T0); assert(!r.fixed); assert.strictEqual(r.data.coins, 4000);
// 13) ข้อมูล _srv ที่เครื่องส่งมา (ปลอมโควตา) ไม่มีผล
o = { ...base(), _srv: { cb: 0, rb: 0, t: T0, paid: [], claims: [] } };
r = step(o, { ...o, coins: 1e6, _srv: { cb: 1e9, rb: 1e9, t: T0 } }, 0); assert(r.fixed); assert.strictEqual(r.data.coins, 1000);
// 14) รหัสกู้คืน
const c = AC.newRecovery(); assert(/^[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}$/.test(c)); assert.strictEqual(AC.hashRecovery(c, 's'), AC.hashRecovery(c.toLowerCase().replace(/-/g, ' '), 's'));
console.log('anticheat OK — 14 cases');
// 15) ไม่มีเหรียญพอ → ของใหม่ไม่ได้ (ไม่ใช่ได้ของฟรี)
{ const o = { coins: 100, rp: 0, owned: {}, ach: {}, season: '2026-11', _srv: { cb: 5000, rb: 0, t: T0, paid: [], claims: [] } };
  const r = AC.validate(o, { ...o, coins: 0, owned: { loco: ['comet', 'diesel'] } }, T0); assert(r.fixed); assert(!r.data.owned.loco.includes('comet')); assert(!r.data.owned.loco.includes('diesel')); assert(r.data.coins <= 5100); }
// 16) โควตาย้ายข้อมูลตอนลงทะเบียนใช้ได้ครั้งเดียว
{ const reg = AC.validate(null, { coins: 0, rp: 0, owned: {} }, T0).data; assert(reg._srv.cb <= AC.COIN_CAP, reg._srv.cb); }
console.log('anticheat OK — 16 cases');
// 17) ความยาวสูงสุด (ตารางอันดับ) ปลอมไม่ได้ · ค่าที่ไม่ใช่ตัวเลขถูกล้าง
{ const o = { coins: 0, rp: 0, owned: {}, ach: {}, st: { maxLen: 500 }, season: '2026-11', _srv: { cb: 0, rb: 0, t: T0, paid: [], claims: [] } };
  let r = AC.validate(o, { ...o, st: { maxLen: 999999, kills: 'abc' } }, T0 + 10000); assert(r.fixed); assert.strictEqual(r.data.st.maxLen, 500 + 300 + 400); assert.strictEqual(r.data.st.kills, 0);
  r = AC.validate(o, { ...o, st: { maxLen: 1100 } }, T0 + 10000); assert(!r.fixed); assert.strictEqual(r.data.st.maxLen, 1100); }
console.log('anticheat OK — 17 cases');
// 18) ใส่ฉายา/หัวจักรที่ไม่ได้ซื้อ → กลับเป็นค่าเริ่มต้น
{ const o = { coins: 0, rp: 0, owned: { title: ['gemking'] }, ach: { k1: 1 }, season: '2026-11', _srv: { cb: 0, rb: 0, t: T0, paid: ['k1'], claims: [] } };
  let r = AC.validate(o, { ...o, eq: { title: 'rich', loco: 'comet' } }, T0); assert.strictEqual(r.data.eq.title, ''); assert.strictEqual(r.data.eq.loco, 'classic');
  r = AC.validate(o, { ...o, eq: { title: 'gemking' } }, T0); assert.strictEqual(r.data.eq.title, 'gemking');
  r = AC.validate(o, { ...o, eq: { title: 'a:k1' } }, T0); assert.strictEqual(r.data.eq.title, 'a:k1'); }
console.log('anticheat OK — 18 cases');

// 11) สถิติออนไลน์ (ตารางอันดับ) · onv 2: RP ออนไลน์ = RP เสมอ (ไม่มีโหมดบอทแล้ว) · เครื่องเก่าที่ไม่ส่งค่าออนไลน์ก็ยังขึ้นตาราง
{ const T = Date.now();
  let d = AC.seedOnline({ rp: 900, st: { kills: 40, maxLen: 1200 }, best: { online: 800, hard: 1500 } });
  assert.deepStrictEqual([d.onrp, d.st.okills, d.st.omaxLen, d.onv], [900, 40, 1200, 2]);
  d = AC.seedOnline({ rp: 1422, onrp: 1271, st: { kills: 60, okills: 50, maxLen: 900, omaxLen: 700 } });   // ข้อมูลที่เพี้ยนไปแล้วบนเว็บจริง → ซ่อม
  assert.deepStrictEqual([d.onrp, d.st.okills, d.st.omaxLen], [1422, 60, 900]);
  const o = { coins: 0, rp: 1000, onrp: 1000, onv: 2, season: '2026-11', st: { kills: 10, okills: 10, maxLen: 900, omaxLen: 900 }, owned: {}, ach: {}, _srv: { cb: 0, rb: 500, t: T - 60000, paid: [], claims: [] } };
  let r = AC.validate(o, { ...o, rp: 1030, onrp: 1030, st: { ...o.st, kills: 12, okills: 12 } }, T); assert(!r.fixed, JSON.stringify(r.data)); assert.strictEqual(r.data.onrp, 1030);
  r = AC.validate(o, { ...o, rp: 1030, onrp: 5000 }, T); assert.strictEqual(r.data.onrp, 1030);
  r = AC.validate(o, { ...o, st: { ...o.st, okills: 50 } }, T); assert(r.fixed); assert.strictEqual(r.data.st.okills, 10);
  // เครื่องเก่า (ไม่ส่ง onrp/okills/omaxLen) เล่นได้ +29 RP กำจัด +3 → ตารางอันดับขยับตาม
  const { onrp, ...noOn } = o; r = AC.validate(o, { ...noOn, rp: 1029, st: { kills: 13, maxLen: 950 } }, T);
  assert.deepStrictEqual([r.data.onrp, r.data.st.okills, r.data.st.omaxLen], [1029, 13, 950]);
  r = AC.validate(o, { ...o, rp: 500, onrp: 500, season: '2026-12' }, T, 0); assert.strictEqual(r.data.onrp, 500); }
console.log('online stats OK');
