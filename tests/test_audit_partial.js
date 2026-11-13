// ฤดูกาลก่อน AUDIT_FROM (2026-12) ข้อมูลเวลาเล่นไม่ครบเดือน → ไม่ตัดสิทธิ์เพราะเล่นไม่ถึง 10 นาที · ธ.ค. ขึ้นไปใช้เกณฑ์เต็ม
process.env.DATABASE_URL = ''; const A = require('../accounts.js'); let bad = 0;
const ok = (c, m) => { console.log((c ? '✅ ' : '❌ ') + m); if (!c) bad++; };
const u0 = { lname: 'x', audit: {} }, u3 = { lname: 'y', audit: { '2026-11': { sec: 180, g: 3, k: 2, ml: 300, fix: 0, rp0: 1000 }, '2026-12': { sec: 180, g: 3, k: 2, ml: 300, fix: 0, rp0: 0 } } };
ok(!A.reviewOf(u0, '2026-11', 7800).dq, 'พ.ย. ไม่มีข้อมูล → ไม่ตัดสิทธิ์');
ok(!A.reviewOf(u3, '2026-11', 1050).dq, 'พ.ย. เล่น 3 นาที RP เพิ่มนิดเดียว → ไม่ตัดสิทธิ์');
ok(A.reviewOf(u3, '2026-11', 5000).dq, 'พ.ย. เล่น 3 นาทีแต่ RP เพิ่ม 4000 → ยังตัดสิทธิ์');
ok(A.reviewOf(u0, '2026-12', 500).dq, 'ธ.ค. ไม่มีข้อมูล → ตัดสิทธิ์');
ok(A.reviewOf(u3, '2026-12', 50).dq, 'ธ.ค. เล่น 3 นาที → ตัดสิทธิ์ (ต้อง 10 นาที)');
console.log(bad ? 'FAIL ' + bad : 'ALL OK'); process.exit(bad ? 1 : 0);
