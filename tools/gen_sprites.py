#!/usr/bin/env python3
"""สร้างโค้ดสไปรต์ (SVG) ของหัวจักร / ตู้ / หวูด จากงานออกแบบใน design/*.dc.html
แล้วแทนที่ลงใน public/index.html ระหว่าง /*SPRITES-BEGIN*/ ... /*SPRITES-END*/
รัน: python3 tools/gen_sprites.py"""
import re, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / 'design'

def mini(s):
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    s = re.sub(r'>\s+<', '><', s)
    return re.sub(r'\s+', ' ', s).strip()

# ---------- หัวจักร: 6 svg ตามลำดับ classic diesel bullet tram metro comet ----------
main = (D / 'Main.dc.html').read_text()
svgs = re.findall(r'<svg viewBox="-200 -115 400 230"[^>]*>(.*?)</svg>', main, re.S)
assert len(svgs) == 6, len(svgs)
LOCO = {}
for lid, v in zip(['classic', 'diesel', 'bullet', 'tram', 'metro', 'comet'], svgs):
    defs, body = v.split('</defs>')
    lines = [l for l in body.strip().split('\n')]
    # ตัดพื้นหลัง: หมอนราง, รางสองเส้น, ลำแสงไฟหน้า (เกมวาดลำแสงเอง)
    assert 'sl)' in lines[0] and '#8d97ad' in lines[1] and 'beam)' in lines[2], lid
    LOCO[lid] = mini(defs + '</defs>' + '\n'.join(lines[3:]))

# ---------- ตู้: defs ทั้งชุด + กลุ่ม wgGem/wgChest/wgGiant/wgGlass ----------
wag = (D / 'Wagons.dc.html').read_text()
wdefs = re.search(r'<svg width="0" height="0"[^>]*>\s*<defs>(.*?)</defs>', wag, re.S).group(1)
# ตู้พิเศษ 8 แบบ (Wagons2.dc.html) — ต่อท้ายเฉพาะส่วน W2 (defs ร่วมมีใน Wagons.dc.html แล้ว)
wdefs += re.search(r'<!--W2-BEGIN-->(.*?)<!--W2-END-->', (D / 'Wagons2.dc.html').read_text(), re.S).group(1)
# ---------- หวูด ----------
hrn = (D / 'Horns.dc.html').read_text()
hdefs = re.search(r'<svg width="0" height="0"[^>]*>\s*<defs>(.*?)</defs>', hrn, re.S).group(1)

js = ('/*SPRITES-BEGIN*/\n'
      '// สร้างอัตโนมัติจาก design/*.dc.html ด้วย tools/gen_sprites.py — ห้ามแก้ตรงนี้ด้วยมือ\n'
      'const LOCO_SVG=' + json.dumps(LOCO, ensure_ascii=False) + ';\n'
      'const WAG_DEFS=' + json.dumps(mini(wdefs), ensure_ascii=False) + ';\n'
      'const HORN_DEFS=' + json.dumps(mini(hdefs), ensure_ascii=False) + ';\n'
      '/*SPRITES-END*/')
p = ROOT / 'public' / 'index.html'
s = p.read_text()
a, b = s.index('/*SPRITES-BEGIN*/'), s.index('/*SPRITES-END*/') + len('/*SPRITES-END*/')
s = s[:a] + js + s[b:]
p.write_text(s)
print('ok', {k: len(v) for k, v in LOCO.items()}, len(wdefs), len(hdefs))
