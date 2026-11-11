// เช็คว่าราคาร้านค้าในเกม (public/index.html) ตรงกับที่เซิร์ฟเวอร์ใช้ตรวจ (anticheat.js) และของลดราคารายวันตรงกันทุกวัน
// รัน: node tests/test_shop_sync.js
const fs = require('fs'), path = require('path'), assert = require('assert');
const AC = require('../anticheat');
const html = fs.readFileSync(path.join(__dirname, '..', 'public', 'index.html'), 'utf8');
const grab = (start, end) => { const a = html.indexOf(start), b = html.indexOf(end, a); return html.slice(a, b + end.length); };
const ctx = {};
new Function('ctx', grab('const SHOP={', '\n};') + ';' + grab('const LIMITED=[', '];') + ';ctx.SHOP=SHOP;ctx.LIMITED=LIMITED;')(ctx);
for (const c of Object.keys(ctx.SHOP)) for (const it of ctx.SHOP[c]) assert.strictEqual(AC.SHOP[c][it.id], it.p, `ราคา ${c}/${it.id} ไม่ตรง`);
for (const c of Object.keys(AC.SHOP)) assert.strictEqual(Object.keys(AC.SHOP[c]).length, ctx.SHOP[c].length, `จำนวนของหมวด ${c} ไม่ตรง`);
assert.deepStrictEqual(ctx.LIMITED.map(l => [l.cat, l.id, l.p]), AC.LIMITED, 'ของหายาก (LIMITED) ไม่ตรง');
// ของลดราคารายวัน: คำนวณแบบเดียวกับในเกม
{ const cd = {}; new Function('cd', grab('function mulberry(', '}}') + ';' + grab('function hashStr(', 'return h>>>0}') + ';' + grab('const SHOP={', '\n};') + ';' + grab('const LIMITED=[', '];') + ';const CATS=Object.keys(SHOP);' + grab('const SALE_POOL=', ';') + grab('const DEAL_LIM=', ';') + grab('function dealOf(', 'return{lims,sales}}') + ';cd.f=dealOf;')(cd);
  const seen = new Set();
  for (let d = 0; d < 400; d++) {
    const day = new Date(Date.UTC(2026, 10, 1) + d * 864e5).toISOString().slice(0, 10), c = cd.f(day), s = AC.dealOf(day);
    assert.deepStrictEqual(c.lims.map(l => [l.cat, l.id, l.p]), s.lims, 'ของหายากวันที่ ' + day + ' ไม่ตรง');
    assert.deepStrictEqual(c.sales.map(x => [x.cat, x.id, x.p, x.off, x.price]), s.sales, 'ของลดราคาวันที่ ' + day + ' ไม่ตรง');
    assert.strictEqual(c.lims.length, 2); assert.strictEqual(new Set(c.sales.map(x => x.cat + x.id)).size, 4); assert.notStrictEqual(c.lims[0].id, c.lims[1].id);
    seen.add(JSON.stringify(s));
  }
  assert(seen.size > 395, 'ร้านแต่ละวันต้องไม่ซ้ำกัน'); }
// รางวัลจบฤดูกาลตามอันดับ: สูตรในเกมต้องตรงกับเซิร์ฟเวอร์
{ const cp = {}; new Function('cp', grab('const PRIZE_BANDS=', 'Math.round(b*prizeScale(n)/100)*100)}') + ';cp.f=seasonPrize;')(cp);
  for (const n of [1, 2, 3, 7, 10, 25, 49, 50, 51, 120, 999]) for (let pos = 0; pos <= Math.min(n, 130); pos++) assert.strictEqual(cp.f(pos, n), AC.seasonPrize(pos, n), `รางวัลอันดับ ${pos}/${n} ไม่ตรง`); }
console.log('shop sync OK —', Object.values(AC.SHOP).reduce((n, c) => n + Object.keys(c).length, 0), 'items +', AC.LIMITED.length, 'limited, 400 days of deals match');
