"""Этаж «Сердце из неона» музея-небоскрёба (третья партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — ночной клуб в стиле синтвейв. Снаружи — тёмно-фиолетовые панели с хромовыми рёбрами и неоновыми
поясами; спереди — огромное ретро-солнце в полосах над неоновой сеткой-горизонтом, перед солнцем — вывеска-сердце из
розового неона, по сторонам — неоновые пальмы, внизу — хромированные двери с рамкой из лампочек; углы — хромовые
пилоны с вертикальным неоном; бока — неоновый «эквалайзер» из столбиков разной высоты и волна; тыл — колонки.
Внутри — клуб: тёмный пол и светодиодный танцпол клетками вокруг постамента, две неоновые арки-тоннель от лифта к
экспонату, зеркальный шар, бархатные диваны со столиками у стен, пульт диджея, на стене за экспонатом — ретро-солнце
с горами-сеткой, неоновые полосы по стенам и потолку.
Запуск: blender --background --factory-startup --python scripts/blender/floor_neonheart.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab  # noqa: E402

DARK, DARK2, DARK3, CHROME, CHROME2, FLOORC = "1E1430", "2A1E40", "362A52", "C8CCD8", "9AA0B4", "160E22"
PINK, PINK2, CYAN, PURPLE, SUNY, SUNO, SUNP = "FF2E7E", "FF7AB8", "3FE6FF", "9A4AFF", "FFD84A", "FF8A3A", "FF4A8A"
VELVET, VELVET2, BULB = "6A1E5A", "541848", "FFF0C0"

F = B.Floor("NH", "NeonHeart", quiet=(FLOORC, VELVET), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def heart(cx, cy, s, n=10):
    """Контур сердца (две доли сверху, остриё снизу)."""
    pts = []
    for k in range(2 * n):
        t = math.pi * 2 * k / (2 * n)
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * s / 16, cy + y * s / 16))
    return pts


def sun_bands(prism, cx, cy, r, d0, d1, n_bands=6):
    """Ретро-солнце: верхняя половина круга полосами с растущими щелями, цвет от жёлтого к розовому."""
    cols = (SUNY, SUNY, SUNO, SUNO, SUNP, SUNP)
    y = cy
    for k in range(n_bands):
        top = cy + r * (1 - k / n_bands)
        bot = cy + r * (1 - (k + 1) / n_bands) + (0.1 + 0.12 * k if k else 0.0)
        pts = []
        for yy in (bot, top):
            w = math.sqrt(max(r * r - (yy - cy) ** 2, 0.0))
            pts.append((cx - w, yy))
            pts.append((cx + w, yy))
        prism([pts[0], pts[1], pts[3], pts[2]], d0, d1, cols[k])
        y = bot


def tube_line(p, a, b, w, color):
    beam(p, a, b, w, w, color)


# ══ ФАСАД: клуб в стиле синтвейв ══════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, DARK, DARK, DARK2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.2, FLOORC)
    slab(FR, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, -0.2, 1.4, DARK2)
    slab(FG, axis, fixed, out, 1.95, -half - 1.8, half + 1.8, 1.0, 1.2, CYAN)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.4, 16.0, DARK)
    for k in range(int(2 * half // 4.0)):  # хромовые рёбра-пилястры
        a = -half + 2.0 + 4.0 * k
        if fi == 0 and abs(a) < 11.0:
            continue
        slab(FS, axis, fixed, out, 1.15, a - 0.25, a + 0.25, 1.4, 16.0, CHROME2)
    slab(FS, axis, fixed, out, 2.0, -half - 2.0, half + 2.0, 16.0, 17.0, CHROME)  # карниз
    slab(FG, axis, fixed, out, 2.05, -half - 2.0, half + 2.0, 16.35, 16.6, PINK)
    slab(FR, axis, fixed, out, 0.88, -half, half, 17.0, 19.0, DARK2)
    for k in range(int(2 * half // 1.2)):  # лампочки по карнизу
        a = -half + 0.6 + 1.2 * k
        slab(FG, axis, fixed, out, 2.1, a - 0.15, a + 0.15, 16.72, 16.92, BULB)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# углы: хромовые пилоны с вертикальным неоном
for sx in (-1, 1):
    for sz in (-1, 1):
        cx, cz = sx * (FX + 0.6), sz * (FZ + 0.6)
        FS.prism_xz(K.octa(cx, cz, 1.5, 1.5, 0.55), -0.2, 18.6, CHROME)
        FG.prism_xz(K.octa(cx, cz, 1.56, 1.56, 0.57), 3.0, 15.0, (PINK, CYAN)[(sx + sz) // 2 % 2])
        FS.prism_xz(K.octa(cx, cz, 1.62, 1.62, 0.6), 7.0, 7.4, CHROME2)
        FS.prism_xz(K.octa(cx, cz, 1.62, 1.62, 0.6), 11.0, 11.4, CHROME2)
# перед: ретро-солнце над неоновой сеткой, сердце-вывеска, пальмы, двери в рамке из лампочек
Z0 = -FZ - 0.95
sun_bands(FS.prism_xy, 0.0, 8.4, 7.2, Z0 - 0.25, Z0)
FG.box(-12.0, 12.0, 8.25, 8.45, Z0 - 0.3, Z0 - 0.2, CYAN)  # горизонт
for k in range(4):  # сетка-горизонт: линии к точке схода
    y = 8.0 - 1.6 * (k + 1) ** 0.85
    FG.box(-12.0, 12.0, y - 0.08, y + 0.08, Z0 - 0.3, Z0 - 0.2, PURPLE if k % 2 else CYAN)
for k in range(-5, 6):
    if k == 0:
        continue
    tube_line(FG, (k * 0.9, 8.2, Z0 - 0.25), (k * 2.6, 1.6, Z0 - 0.25), 0.14, PURPLE)
FG.box(-0.07, 0.07, 1.6, 8.2, Z0 - 0.3, Z0 - 0.2, PURPLE)
HEART = heart(0.0, 12.0, 4.4)
FS.frame_xy([(x, y) for x, y in heart(0.0, 12.0, 4.9)], HEART, -FZ - 2.3, -FZ - 1.6, DARK3)
FG.frame_xy(HEART, heart(0.0, 12.0, 4.0), -FZ - 2.4, -FZ - 1.7, PINK)
FG.frame_xy(heart(0.0, 12.0, 3.2), heart(0.0, 12.0, 2.9), -FZ - 2.35, -FZ - 1.75, PINK2)
for y0 in (0.0,):  # стойки вывески
    for x in (-2.2, 2.2):
        FS.box(x - 0.15, x + 0.15, 8.4, 9.4, -FZ - 2.1, -FZ - 0.9, CHROME2)
for s in (-1, 1):  # неоновые пальмы
    bx = s * 14.0
    pts = [(bx, 1.6), (bx + s * 0.3, 6.0), (bx - s * 0.2, 10.0), (bx - s * 0.6, 12.6)]
    for a, b in zip(pts, pts[1:]):
        tube_line(FG, (a[0], a[1], Z0 - 0.3), (b[0], b[1], Z0 - 0.3), 0.32, PINK)
    tx, ty = pts[-1]
    for k in range(6):
        t = math.radians(-10 + 38 * k)
        mx, my = tx + math.cos(t) * 2.0, ty + 0.8 + math.sin(t) * 0.6
        ex, ey = tx + math.cos(t) * 3.6, ty - 0.6 + math.sin(t) * 0.2
        tube_line(FG, (tx, ty, Z0 - 0.3), (mx, my, Z0 - 0.3), 0.26, CYAN if k % 2 else PINK2)
        tube_line(FG, (mx, my, Z0 - 0.3), (ex, ey, Z0 - 0.3), 0.22, CYAN if k % 2 else PINK2)
FS.box(-3.0, 3.0, 1.4, 6.0, -FZ - 1.2, -FZ, CHROME)  # двери
FS.box(-2.6, -0.1, 1.4, 5.6, -FZ - 1.35, -FZ - 1.2, DARK3)
FS.box(0.1, 2.6, 1.4, 5.6, -FZ - 1.35, -FZ - 1.2, DARK3)
for k in range(13):  # рамка из лампочек
    t = k / 12
    pts = [(-3.2, 1.6 + 4.6 * t), (3.2, 1.6 + 4.6 * t), (-3.2 + 6.4 * t, 6.25)]
    for x, y in pts:
        FG.box(x - 0.13, x + 0.13, y - 0.13, y + 0.13, -FZ - 1.4, -FZ - 1.3, BULB)
FS.box(-4.0, 4.0, 6.4, 6.7, -FZ - 3.0, -FZ, CHROME)  # козырёк
FG.box(-4.0, 4.0, 6.25, 6.4, -FZ - 3.0, -FZ - 2.8, PINK)
# бока: неоновый эквалайзер и волна
for s in (-1, 1):
    fx = s * FX
    for k in range(12):
        z = -13.2 + 2.4 * k
        h = 3.0 + 9.0 * abs(math.sin(k * 0.9 + (s > 0) * 1.3)) * (0.5 + 0.5 * rng(k, s))
        col = (CYAN, PURPLE, PINK)[min(2, int(h // 4.2))]
        slab(FG, "x", fx, s, 1.3, z - 0.7, z + 0.7, 2.6, 2.6 + h, col)
        slab(FS, "x", fx, s, 1.2, z - 0.85, z + 0.85, 2.4, 2.6 + h + 0.2, DARK3)
    wave = [(-15.0 + 1.5 * k, 14.2 + 0.7 * math.sin(k * 0.8)) for k in range(21)]
    for a, b in zip(wave, wave[1:]):
        tube_line(FG, (fx + s * 1.3, a[1], a[0]), (fx + s * 1.3, b[1], b[0]), 0.22, PINK2)
# тыл: колонки
for x in (-10.0, -5.0, 5.0, 10.0):
    FS.box(x - 2.0, x + 2.0, -0.2, 6.0, FZ, FZ + 2.6, DARK2)
    for y, r in ((1.8, 1.3), (4.6, 0.8)):
        FS.prism_xy(K.octa(x, y, r, r, r * 0.41), FZ + 2.6, FZ + 2.75, CHROME2)
        FS.prism_xy(K.octa(x, y, r * 0.5, r * 0.5, r * 0.2), FZ + 2.75, FZ + 2.9, DARK3)
    FG.box(x - 2.0, x + 2.0, 6.0, 6.15, FZ + 2.5, FZ + 2.65, CYAN)

# ══ ИНТЕРЬЕР: неоновый клуб ═══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -4.0)
TOP = 1.2
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), FLOORC)
px, pz = PED
for i in range(-4, 5):  # светодиодный танцпол клетками
    for j in range(-3, 5):
        x0, z0 = 2.0 * i - 1.0, pz + 2.0 * j - 1.0
        if abs(x0 + 1 - px) < 4.2 and abs(z0 + 1 - pz) < 3.8:
            continue
        if (i + j) % 2:
            IS.box(x0 + 0.08, x0 + 1.92, 0.02, 0.06, z0 + 0.08, z0 + 1.92, DARK3)
        else:
            IG.box(x0 + 0.08, x0 + 1.92, 0.02, 0.06, z0 + 0.08, z0 + 1.92, (PINK, PURPLE, CYAN)[(i * 2 + j) % 3])
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.0, DARK2)
        n = max(1, int((a1 - a0) // 4.0))
        for k in range(n):  # стеганые тёмные панели
            b0, b1 = a0 + (a1 - a0) * k / n, a0 + (a1 - a0) * (k + 1) / n
            slab(IR, axis, fixed, out, 0.88, b0 + 0.08, b1 - 0.08, 1.0, 11.0, DARK if k % 2 else DARK3)
    slab(IQ, axis, fixed, out, 0.7, -half, half, 0.0, C, DARK)
    slab(IG, axis, fixed, out, 0.95, -half, half, 1.0, 1.15, CYAN)
    slab(IS, axis, fixed, out, 1.0, -half, half, 11.0, 11.6, CHROME2)
    slab(IG, axis, fixed, out, 1.05, -half, half, 11.2, 11.4, PINK)
    slab(IR, axis, fixed, out, 0.88, -half, half, 11.6, C, DARK2)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 11.0, DARK3)
# стена за экспонатом: ретро-солнце и горы-сетка
sun_bands(IS.prism_xy, 0.0, 4.4, 5.6, ZF + 0.9, ZF + 1.05)
for k in range(5):
    x0 = -15.0 + 6.0 * k + (3.0 if k > 2 else 0.0)
    if abs(x0 + 3.0) < 5.0:
        continue
    for a, b in (((x0, 1.2), (x0 + 3.0, 6.0)), ((x0 + 3.0, 6.0), (x0 + 6.0, 1.2))):
        tube_line(IG, (a[0], a[1], ZF + 1.1), (b[0], b[1], ZF + 1.1), 0.16, PURPLE)
IG.box(-W, W, 4.3, 4.45, ZF + 1.0, ZF + 1.15, CYAN)
# потолок: неоновая решётка
for k in range(-3, 4):
    IG.box(-12.0, 12.0, C - 0.1, C - 0.04, 4.0 * k - 0.06, 4.0 * k + 0.06, PURPLE if k % 2 else "5A2A9A")
# две неоновые арки-тоннель от лифта к экспонату
for k, z in enumerate((9.6, 6.6)):
    col = (PINK, CYAN)[k]
    outer = [(-5.0, 0.0)] + [(-5.0 + 5.0 * (1 - math.cos(math.pi * m / 8)), 7.0 + 3.0 * math.sin(math.pi * m / 8))
                             for m in range(9)] + [(5.0, 0.0)]
    inner = [(-4.6, 0.0)] + [(-4.6 + 4.6 * (1 - math.cos(math.pi * m / 8)), 7.0 + 2.6 * math.sin(math.pi * m / 8))
                             for m in range(9)] + [(4.6, 0.0)]
    IG.frame_xy(outer, inner, z - 0.15, z + 0.15, col)
    IS.box(-5.2, -4.4, 0.0, 0.5, z - 0.4, z + 0.4, CHROME2)
    IS.box(4.4, 5.2, 0.0, 0.5, z - 0.4, z + 0.4, CHROME2)
# зеркальный шар
IS.box(-0.05, 0.05, 13.6, C, 3.0 - 0.05, 3.0 + 0.05, CHROME2)
for k in range(4):
    y0, y1 = 11.0 + 0.65 * k, 11.0 + 0.65 * (k + 1)
    r0 = 1.3 * math.sin(math.pi * (k + 0.0) / 4) + 0.2
    r1 = 1.3 * math.sin(math.pi * (k + 1.0) / 4) + 0.2
    IS.loft([(r0 * math.cos(2 * math.pi * m / 10), y0, 3.0 + r0 * math.sin(2 * math.pi * m / 10)) for m in range(10)],
            [(r1 * math.cos(2 * math.pi * m / 10), y1, 3.0 + r1 * math.sin(2 * math.pi * m / 10)) for m in range(10)],
            "D8DCE8" if k % 2 else "B0B8CC")
# бархатные диваны и столики у боковых стен, пульт диджея
for s in (-1, 1):
    for zc in (-10.0, 2.0):
        x0 = s * W
        IS.box(x0, x0 - s * 2.4, 0.0, 1.6, zc - 3.0, zc + 3.0, VELVET)
        IS.box(x0, x0 - s * 1.0, 1.6, 4.2, zc - 3.0, zc + 3.0, VELVET2)
        for k in range(3):
            IS.box(x0 - s * 0.95, x0 - s * 1.1, 1.8, 4.0, zc - 2.8 + 2.0 * k, zc - 1.2 + 2.0 * k, VELVET)
        tx = x0 - s * 4.0
        IS.prism_xz(K.octa(tx, zc, 0.25, 0.25, 0.1), 0.0, 2.0, CHROME2)
        IS.prism_xz(K.octa(tx, zc, 1.2, 1.2, 0.5), 2.0, 2.2, CHROME)
        for dz, col in ((-0.4, PINK2), (0.45, CYAN)):
            IG.prism_xz(K.octa(tx + 0.3 * s, zc + dz, 0.18, 0.18, 0.07), 2.2, 2.75, col)
IS.box(9.0, 14.0, 0.0, 2.8, -15.0, -12.6, DARK3)  # пульт диджея
IS.box(8.8, 14.2, 2.8, 3.0, -15.2, -12.4, CHROME)
for x in (10.2, 12.8):
    IS.prism_xz(K.octa(x, -13.8, 0.8, 0.8, 0.33), 3.0, 3.15, "26262E")
    IG.prism_xz(K.octa(x, -13.8, 0.25, 0.25, 0.1), 3.15, 3.2, PINK)
IG.box(9.0, 14.0, 1.2, 1.4, -12.58, -12.54, CYAN)
# постамент: хромовый, с неоновым кольцом
IR.prism_xz(K.octa(px, pz, 4.0, 3.6, 1.6), 0.0, 0.6, DARK3)
IR.prism_xz(K.octa(px, pz, 3.3, 3.0, 1.3), 0.6, TOP, DARK2)
IG.frame_xz(K.octa(px, pz, 4.1, 3.7, 1.64), K.octa(px, pz, 3.9, 3.5, 1.56), 0.35, 0.5, PINK)
IS.frame_xz(K.octa(px, pz, 3.4, 3.1, 1.34), K.octa(px, pz, 3.3, 3.0, 1.3), TOP - 0.15, TOP + 0.02, CHROME)
B.lift_leaves(IS, CHROME2, PINK)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, DARK)
SL.box(-FX - 1.9, FX + 1.9, -1.0, 1.4, -FZ - 1.9, FZ + 1.9, DARK2)
SL.box(-FX - 2.0, FX + 2.0, 16.0, 17.0, -FZ - 2.0, FZ + 2.0, CHROME)
SL.box(-7.2, 7.2, 8.4, 15.6, -FZ - 1.2, -FZ, SUNO)
SL.box(-4.4, 4.4, 7.6, 16.4, -FZ - 2.4, -FZ - 1.2, PINK)
for s in (-1, 1):
    SL.box(s * FX, s * (FX + 1.3), 2.6, 12.0, -13.0, 13.0, PURPLE)

F.build(exhibit=(PED[0], TOP, PED[1], 3.0), lamps=[("Hall", (0, 14, 6), 1800, (0.9, 0.8, 1.0)),
                                                   ("Spot", (0, 13, -4), 3000, (1.0, 0.92, 0.98))])
