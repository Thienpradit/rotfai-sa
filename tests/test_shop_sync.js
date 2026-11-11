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
{ const cd = {}; new Function('cd', grab('function mulberry(', '}}') + ';' + grab('function hashStr(', 'return h>>>0}') + ';' + grab('const SHOP={', '\n};') + ';' + grab('const LIMITED=[', '];') + ';const CATS=Object.keys(SHOP);' + grab('const SALE_POOL=', ';') + grab('const DEAL_OFFS=', ';') + grab('function dealPick(', 'return a[dn-k*n]}') + grab('function dealOf(', 'return{lims,sales}}') + ';cd.f=dealOf;')(cd);
  const hist = [];
  for (let d = 0; d < 400; d++) {
    const day = new Date(Date.UTC(2026, 10, 1) + d * 864e5).toISOString().slice(0, 10), c = cd.f(day), s = AC.dealOf(day);
    assert.deepStrictEqual(c.lims.map(l => [l.cat, l.id, l.p]), s.lims, 'ของหายากวันที่ ' + day + ' ไม่ตรง');
    assert.deepStrictEqual(c.sales.map(x => [x.cat, x.id, x.p, x.off, x.price]), s.sales, 'ของลดราคาวันที่ ' + day + ' ไม่ตรง');
    assert.strictEqual(c.lims.length, 1); assert.strictEqual(c.sales.length, 1);
    hist.push([s.lims[0].join(), s.sales[0].slice(0, 2).join()]);
  }
  // วันละ 2 ชิ้น ไม่ซ้ำ: ของหายาก/ของลดราคาชิ้นเดิมกลับมาเร็วสุด 6 วัน และวนครบทุกชิ้นก่อนซ้ำ
  const gap = col => { let g = 1e9; const last = {}; hist.forEach((h, i) => { if (h[col] in last) g = Math.min(g, i - last[h[col]]); last[h[col]] = i; }); return g; };
  assert(gap(0) >= 6, 'ของหายากซ้ำเร็วไป ' + gap(0)); const nS = AC.SALE_POOL.length; assert(gap(1) >= Math.min(7, Math.floor(nS / 3)) + 1, 'ของลดราคาซ้ำเร็วไป ' + gap(1));
  assert.strictEqual(new Set(hist.map(h => h[0])).size, AC.LIMITED.length, 'ของหายากต้องวนครบทุกชิ้น'); assert.strictEqual(new Set(hist.map(h => h[1])).size, nS, 'ของลดราคาต้องวนครบทุกชิ้น');
  console.log('  deal min gap: rare', gap(0), 'days, sale', gap(1), 'days'); }
// รางวัลจบฤดูกาลตามอันดับ: สูตรในเกมต้องตรงกับเซิร์ฟเวอร์
{ const cp = {}; new Function('cp', grab('const PRIZE_BANDS=', 'Math.round(b*prizeScale(n)/100)*100)}') + ';cp.f=seasonPrize;')(cp);
  for (const n of [1, 2, 3, 7, 10, 25, 49, 50, 51, 120, 999]) for (let pos = 0; pos <= Math.min(n, 130); pos++) assert.strictEqual(cp.f(pos, n), AC.seasonPrize(pos, n), `รางวัลอันดับ ${pos}/${n} ไม่ตรง`); }
console.log('shop sync OK —', Object.values(AC.SHOP).reduce((n, c) => n + Object.keys(c).length, 0), 'items +', AC.LIMITED.length, 'limited, 400 days of deals match');
