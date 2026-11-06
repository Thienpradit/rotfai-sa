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
const hashStr = s => { let h = 2166136261; for (const c of s) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; };
const CATS = Object.keys(ctx.SHOP), POOL = CATS.flatMap(c => ctx.SHOP[c].filter(i => i.p > 0).map(i => ({ cat: c, ...i })));
for (let d = 0; d < 400; d++) {
  const day = new Date(Date.UTC(2026, 10, 1) + d * 864e5).toISOString().slice(0, 10), h = hashStr('deal:' + day);
  const s = AC.dealOf(day), cs = POOL[(h >>> 8) % POOL.length], cl = ctx.LIMITED[h % ctx.LIMITED.length];
  assert.deepStrictEqual([s.sale[0], s.sale[1], s.lim[1]], [cs.cat, cs.id, cl.id], 'ของประจำวัน ' + day + ' ไม่ตรง');
  assert.strictEqual(s.salePrice, Math.round(cs.p * .7 / 100) * 100);
}
console.log('shop sync OK —', Object.values(AC.SHOP).reduce((n, c) => n + Object.keys(c).length, 0), 'items +', AC.LIMITED.length, 'limited, 400 days of deals match');
