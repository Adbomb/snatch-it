"""Этаж «Голова моаи» музея-небоскрёба (вторая партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — священная платформа аху на скалистом берегу острова. Снаружи — стена из подогнанных глыб
тёмного базальта (неровные блоки трёх тонов на тёмном растворе), снизу — прибой с пеной, сверху — травяной склон
с кочками и камнями; спереди — плита с высеченным человеком-птицей, по бокам — огромные головы моаи в профиль
(тяжёлый лоб, длинный нос, губы, красный пукао-шапка), на углах — наклонённые пальмы с кокосами.
Внутри — пляж на закате: песок и бирюзовая лагуна у передней стены, стены — панорама неба (оранжевый, розовый,
лиловый) с заходящим солнцем и силуэтами островов, на потолке — первые звёзды; моаи-экспонат на ступенчатой
аху из базальта, к ней ведёт дорожка из плоских камней, по сторонам — факелы тики, пальмы, лодка с балансиром,
камни с петроглифами, ракушки.
Запуск: blender --background --factory-startup --python scripts/blender/floor_moai.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab, taper, tube  # noqa: E402

BAS, BAS2, BAS3, MORTAR = "5A5A62", "4A4A52", "6C6A70", "2E2E34"
GRASS, GRASS2, MOSS = "6DBE45", "4E9A34", "86C85A"
SEA, SEA2, FOAM, SAND, SAND2 = "2FB5D0", "1F8FB0", "EEF8FA", "F0D9A0", "E2C485"
PUKAO, TRUNK, TRUNK2, LEAF, LEAF2, NUT = "B5523A", "8A6A48", "6E5236", "3FA34A", "2E8A3C", "6A4A2A"
SUN, ORANGE, PINK, LILAC, NIGHT = "FFD36A", "FF9A5A", "FF7A9A", "9A6AC8", "3A3A78"
FLAME, FLAME2, WOOD, CLOTH = "FFC24A", "FF8A2A", "9A6A40", "E8D8B0"

F = B.Floor("MO", "Moai", quiet=(SAND, SAND2, SEA, SEA2, GRASS, GRASS2, LILAC, NIGHT, PINK, ORANGE), bevel_min=1.0, keep_arch=True)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def palm(p, base, lean, h, color_trunk=TRUNK):
    """Пальма: изогнутый ствол кольцами, веер листьев-шипов, гроздь кокосов."""
    bx, by, bz = base
    lx, lz = lean
    pts = [(bx + lx * (t ** 1.6), by + h * t, bz + lz * (t ** 1.6)) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
    tube(p, pts, [0.9, 0.8, 0.72, 0.66, 0.6], 0.75, (1, 0, 0) if abs(lz) > abs(lx) else (0, 0, 1), color_trunk)
    top = pts[-1]
    for k in range(7):
        t = 2 * math.pi * (k + rng(k, h) * 0.3) / 7
        L = 3.4 + rng(k, 7) * 0.8
        mid = (top[0] + math.cos(t) * L * 0.55, top[1] + 0.7, top[2] + math.sin(t) * L * 0.55)
        tip = (top[0] + math.cos(t) * L, top[1] - 1.2, top[2] + math.sin(t) * L)
        taper(p, top, mid, 0.9, 0.7, LEAF if k % 2 else LEAF2)
        taper(p, mid, tip, 0.7, 0.08, LEAF if k % 2 else LEAF2)
    for k in range(3):
        t = 2 * math.pi * k / 3 + 0.4
        x, z = top[0] + 0.45 * math.cos(t), top[2] + 0.45 * math.sin(t)
        p.prism_xz(K.octa(x, z, 0.3, 0.3, 0.12), top[1] - 0.7, top[1] - 0.15, NUT)


# ══ ФАСАД: аху из базальта на берегу ═════════════════════════════════════════════════════════════════════════
B.shell_planes(F, MORTAR, MORTAR, NIGHT)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    # прибой: вода, гребни пены неровной высоты
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, 0.4, SEA)
    n = int(2 * half // 3.5)
    for k in range(n):
        a = -half - 1.5 + (2 * half + 3) * (k + 0.5) / n
        h = 0.5 + rng(fi, k, 3) * 0.6
        slab(FS, axis, fixed, out, 3.0, a - 1.1, a + 1.1, 0.4, 0.4 + h, FOAM if k % 2 else "D4EEF4")
    # раствор и глыбы базальта: ряды неровной высоты, блоки неровной ширины, три тона
    slab(FS, axis, fixed, out, 0.7, -half - 0.7, half + 0.7, 0.4, 14.0, MORTAR)
    y = 0.0
    for r, rh in enumerate((3, 2, 3, 2, 2, 2)):
        a = -half - 1.0
        k = 0
        while a < half + 1.0 - 0.5:
            w = 3 + int(rng(fi, r, k) * 3)
            a1 = min(a + w, half + 1.0)
            tone = (BAS, BAS2, BAS3)[int(rng(fi, r, k, 9) * 3)]
            slab(FR, axis, fixed, out, 0.88 + (0.1 if (r + k) % 3 == 0 else 0.0), a + 0.08, a1 - 0.08, y + 0.08,
                 y + rh - 0.08, tone)
            a, k = a1, k + 1
        y += rh
    # травяной склон: дёрн, свисающие пучки, кочки и камни наверху
    slab(FQ, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, 14.0, 15.6, GRASS)
    for k in range(int(2 * half // 2.4)):
        a = -half + 1.2 + 2.4 * k
        L = 0.8 + rng(fi, k, 5) * 1.3
        slab(FS, axis, fixed, out, 1.95, a - 0.35, a + 0.35, 14.0 - L, 14.1, GRASS2 if k % 2 else GRASS)
    slab(FQ, axis, fixed, out, 1.0, -half - 1.0, half + 1.0, 15.6, 19.0, GRASS2)
    for k in range(int(2 * half // 4.0)):
        a = -half + 2.0 + 4.0 * k + (rng(fi, k, 11) - 0.5)
        hh = 16.2 + rng(fi, k, 12) * 1.6
        slab(FS, axis, fixed, out, 1.5, a - 0.9, a + 0.9, 15.6, hh, MOSS if k % 3 else BAS3)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))

# перед: плита с человеком-птицей (рельеф), по сторонам — пукао-валуны
FS.box(-4.2, 4.2, 3.0, 12.6, -FZ - 1.2, -FZ, "7E7A78")
FS.box(-3.8, 3.8, 3.4, 12.2, -FZ - 1.3, -FZ - 1.2, "8E8A86")
BIRDMAN = [(-0.4, 4.0), (0.6, 4.4), (1.9, 3.7), (0.9, 3.4), (1.2, 2.4), (2.3, 1.2), (1.6, -0.6), (1.9, -2.6),
           (0.7, -3.4), (0.9, -1.0), (-0.6, -0.6), (-1.6, -2.8), (-2.2, -2.2), (-1.4, 0.4), (-2.0, 1.8), (-1.0, 2.6)]
FS.prism_xy([(x, 7.8 + y) for x, y in BIRDMAN], -FZ - 1.5, -FZ - 1.3, BAS2)
FS.prism_xy(K.octa(0.3, 11.6, 0.35, 0.35, 0.14), -FZ - 1.6, -FZ - 1.5, MORTAR)
for s in (-1, 1):
    x = s * 5.2  # факелы у плиты
    FS.box(x - 0.18, x + 0.18, 2.0, 9.6, -FZ - 1.4, -FZ - 1.04, WOOD)
    FS.prism_xz(K.octa(x, -FZ - 1.22, 0.45, 0.45, 0.18), 9.6, 10.3, "6A4A2A")
    FG.prism_xz(K.octa(x, -FZ - 1.22, 0.34, 0.34, 0.14), 10.3, 11.0, FLAME2)
    FG.prism_xz(K.octa(x, -FZ - 1.22, 0.18, 0.18, 0.07), 11.0, 11.7, FLAME)

F.objects(True)
# бока: головы моаи в профиль (смотрят вперёд, к −Z), красный пукао
PROFILE = [(4.2, 0.0), (4.2, 6.2), (3.6, 8.6), (3.9, 9.4), (3.0, 10.0), (-0.6, 10.4), (-1.0, 9.8), (-1.6, 8.0),
           (-3.4, 6.4), (-3.0, 5.6), (-2.0, 5.2), (-2.6, 4.4), (-2.0, 3.8), (-2.4, 3.0), (-1.6, 2.2), (-2.2, 1.0),
           (-1.4, 0.0)]  # (z — назад, y — вверх) от подбородка; нос у z ≈ −3.4
for s in (-1, 1):
    fx = s * FX
    zc = -2.0
    prof = [(zc + z * 1.15, 1.6 + y * 1.18) for z, y in PROFILE]
    FS.prism_zy(prof, fx, fx + s * 2.4, "8A8680")
    FS.prism_zy([(zc + z * 0.95 + 0.4, 2.2 + y * 1.06) for z, y in PROFILE], fx + s * 2.4, fx + s * 2.7, "9A968E")
    FS.prism_zy([(zc - 1.6, 12.6), (zc + 0.6, 12.6), (zc + 0.4, 11.8), (zc - 1.3, 11.9)], fx + s * 2.7, fx + s * 2.85,
                MORTAR)  # глазница под лбом
    FS.prism_zy([(zc - 3.4, 6.2), (zc - 1.6, 6.0), (zc - 1.8, 5.6), (zc - 3.0, 5.7)], fx + s * 2.7, fx + s * 2.85, BAS2)
    FS.box(fx, fx + s * 2.2, 13.6, 14.6, zc - 1.4, zc + 4.2, "8A8680")  # макушка
    FS.prism_zy(K.octa(zc + 1.4, 16.0, 2.9, 1.4, 0.58), fx, fx + s * 2.5, PUKAO)
    FS.prism_zy(K.octa(zc + 1.4, 17.7, 2.0, 0.4, 0.17), fx, fx + s * 2.2, "9A4430")
    FS.box(fx, fx + s * 1.2, 1.0, 2.6, zc - 3.0, zc + 5.0, BAS3)  # аху под головой
    for zz in (-11.5, 10.5):  # петроглифы на боках: рыба и черепаха
        FS.prism_zy([(zz - 1.6, 8.0), (zz + 0.8, 9.0), (zz + 1.6, 8.2), (zz + 2.0, 9.0), (zz + 2.0, 7.0), (zz + 1.6, 7.8),
                     (zz + 0.8, 7.0)], fx + s * 0.85, fx + s * 1.0, MORTAR)
# перед: два моаи в профиль по сторонам плиты, носами к углам
for s in (-1, 1):
    xc = s * 10.6
    prof = [(xc - s * z * 1.15, 1.6 + y * 1.18) for z, y in PROFILE]
    FS.prism_xy(prof, -FZ - 2.4, -FZ, "8A8680")
    FS.prism_xy([(xc - s * (z * 0.95 + 0.4), 2.2 + y * 1.06) for z, y in PROFILE], -FZ - 2.7, -FZ - 2.4, "9A968E")
    FS.prism_xy([(xc + s * 1.6, 12.6), (xc - s * 0.6, 12.6), (xc - s * 0.4, 11.8), (xc + s * 1.3, 11.9)],
                -FZ - 2.85, -FZ - 2.7, MORTAR)
    FS.box(xc - 2.4, xc + 2.4, 13.6, 14.6, -FZ - 2.2, -FZ, "8A8680")
    FS.prism_xy(K.octa(xc - s * 1.4, 16.0, 2.9, 1.4, 0.58), -FZ - 2.5, -FZ, PUKAO)
    FS.prism_xy(K.octa(xc - s * 1.4, 17.7, 2.0, 0.4, 0.17), -FZ - 2.2, -FZ, "9A4430")
# углы: пальмы, наклонённые наружу
for sx in (-1, 1):
    for sz in (-1, 1):
        palm(FS, (sx * (FX + 0.9), 15.4, sz * (FZ + 0.9)), (sx * 1.2, sz * 1.0), 2.1)
F.objects(False)
# тыл: ступени к воде и сеть рыбаков
for k in range(4):
    FS.box(-3.0 - k * 0.6, 3.0 + k * 0.6, 0.4 + 0.0, 1.2 + 0.8 * (3 - k), FZ, FZ + 0.6 + 0.6 * k, BAS3)

# ══ ИНТЕРЬЕР: пляж на закате ═════════════════════════════════════════════════════════════════════════════════
AHU = (0.0, -3.0)  # центр аху
TOP = 1.6
IQ.plane([(-W, 0.02, -9.5), (W, 0.02, -9.5), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), SAND)
IG.plane([(-W, 0.03, ZF), (W, 0.03, ZF), (W, 0.03, -9.5), (-W, 0.03, -9.5)], [], (0, 1, 0), SEA)
for k in range(9):  # кромка прибоя
    x = -W + 0.2 + 3.8 * k
    IS.box(x, x + 2.6 + rng(k, 1) * 0.8, 0.0, 0.1, -9.7 - rng(k, 2) * 0.5, -9.3, FOAM)
# стены — панорама неба полосами, ниже — море
BANDS = ((0.0, 3.0, SEA2), (3.0, 3.4, "7FD0E0"), (3.4, 6.0, ORANGE), (6.0, 9.0, PINK), (9.0, 13.0, LILAC),
         (13.0, C, NIGHT))
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    for y0, y1, color in BANDS:
        if idx == 3 and y0 < DOOR[1] + 0.5:
            for a0, a1 in ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)):
                slab(IQ, axis, fixed, out, 0.88, a0, a1, y0, y1, color)
        else:
            slab(IQ, axis, fixed, out, 0.88, -half, half, y0, y1, color)
    # силуэты островов на горизонте
    for k in range(2):
        a = (-0.5 + k) * half * 0.9 + (rng(idx, k) - 0.5) * 4
        if idx == 3 and abs(a) < DOOR[0] + 4:
            continue
        w = 3.0 + rng(idx, k, 2) * 3
        pts = [(a - w, 3.0), (a - w * 0.4, 4.6 + rng(idx, k, 3)), (a + w * 0.2, 4.0), (a + w * 0.6, 5.0), (a + w, 3.0)]
        if axis == "z":
            IS.prism_xy(pts, fixed + out * 0.9, fixed + out * 1.0, "5A3A6A")
        else:
            IS.prism_zy(pts, fixed + out * 0.9, fixed + out * 1.0, "5A3A6A")
# заходящее солнце на передней стене, блик на воде
IG.prism_xy(K.octa(0, 3.4, 3.6, 3.6, 1.5), ZF + 0.9, ZF + 1.0, SUN)
IS.box(-W, W, 0.0, 3.4, ZF + 1.0, ZF + 1.1, SEA2)
for k in range(5):
    w = 2.6 - 0.45 * k
    IG.box(-w, w, 2.6 - 0.55 * k, 2.8 - 0.55 * k, ZF + 1.1, ZF + 1.15, SUN)
# звёзды на потолке
for k in range(26):
    x, z = (rng(k, 51) - 0.5) * 31, (rng(k, 52) - 0.5) * 29
    IG.box(x - 0.1, x + 0.1, C - 0.05, C - 0.02, z - 0.1, z + 0.1, "FFF4D8")
F.objects(True)
# аху: ступени из базальтовых глыб, рампа из гальки перед ней
ax, az = AHU
IR.box(ax - 6.0, ax + 6.0, 0.0, 0.8, az - 3.0, az + 3.0, BAS2)
IR.box(ax - 5.0, ax + 5.0, 0.8, TOP, az - 2.0, az + 2.0, BAS)
for k in range(6):  # швы-глыбы на лицевой стороне
    x = ax - 6.0 + 2.0 * k
    IS.box(x + 0.1, x + 1.9, 0.1, 0.7, az - 3.08, az - 3.0, (BAS3, BAS2)[k % 2])
for k in range(5):
    x = ax - 5.0 + 2.0 * k
    IS.box(x + 0.1, x + 1.9, 0.9, TOP - 0.1, az - 2.08, az - 2.0, (BAS2, BAS3)[k % 2])
for k in range(7):  # дорожка камней к лифту
    z = 4.0 + 1.6 * k
    x = (rng(k, 61) - 0.5) * 0.8
    IS.prism_xz(K.octa(x, z, 1.0 + rng(k, 62) * 0.3, 0.6, 0.25), 0.0, 0.1, BAS3 if k % 2 else "8E8A86")
# факелы тики у аху и у лифта
for x, z in ((-7.5, -5.5), (7.5, -5.5), (-5.0, 6.0), (5.0, 6.0)):
    IS.box(x - 0.16, x + 0.16, 0.0, 4.2, z - 0.16, z + 0.16, WOOD)
    IS.prism_xz(K.octa(x, z, 0.4, 0.4, 0.16), 4.2, 4.9, "6A4A2A")
    IG.prism_xz(K.octa(x, z, 0.3, 0.3, 0.12), 4.9, 5.5, FLAME2)
    IG.prism_xz(K.octa(x, z, 0.16, 0.16, 0.06), 5.5, 6.1, FLAME)
# пальмы по углам пляжа
for x, z, lx, lz, h in ((-13.0, -6.0, 1.6, 0.6, 12.0), (13.5, -7.0, -1.8, 0.4, 11.0), (-13.5, 7.0, 1.2, -0.8, 10.0),
                        (13.0, 6.5, -1.4, -0.6, 12.5)):
    palm(IS, (x, 0.0, z), (lx, lz), h)
    IS.prism_xz(K.octa(x, z, 1.1, 1.1, 0.45), 0.0, 0.3, SAND2)
# лодка с балансиром на песке справа
bx, bz = 9.5, 0.5
IS.prism_xz([(bx - 0.7, bz - 3.6), (bx + 0.7, bz - 3.6), (bx + 0.9, bz + 3.0), (bx, bz + 3.9), (bx - 0.9, bz + 3.0)],
            0.0, 0.9, WOOD)
IS.prism_xz([(bx - 0.5, bz - 3.3), (bx + 0.5, bz - 3.3), (bx + 0.6, bz + 2.8), (bx - 0.6, bz + 2.8)], 0.9, 0.95, "6A4A2A")
for dz in (-1.5, 1.5):
    beam(IS, (bx, 0.85, bz + dz), (bx - 3.2, 0.5, bz + dz), 0.18, 0.18, TRUNK2)
IS.box(bx - 3.6, bx - 2.8, 0.0, 0.45, bz - 2.4, bz + 2.4, WOOD)
beam(IS, (bx + 0.3, 0.9, bz + 1.0), (bx + 2.5, 0.05, bz + 2.2), 0.16, 0.16, TRUNK2)  # весло
# камни с петроглифами и ракушки
for x, z, r in ((-9.0, 2.0, 1.4), (-10.5, -1.0, 0.9), (11.5, 11.0, 1.1)):
    IS.prism_xz(K.octa(x, z, r, r * 0.8, r * 0.35), 0.0, r * 1.1, BAS2)
    IS.prism_xz(K.octa(x, z, r * 0.7, r * 0.55, r * 0.25), r * 1.1, r * 1.4, BAS3)
for k in range(10):
    x, z = (rng(k, 71) - 0.5) * 28, -8.5 + rng(k, 72) * 22
    if abs(x) < 6 and -6 < z < 16:
        continue
    IS.prism_xz(K.octa(x, z, 0.35, 0.3, 0.12), 0.0, 0.18, ("F4C8B8", "FFF0D8", "F2A07A")[k % 3])
F.objects(False)
B.lift_leaves(IS, TRUNK2, PUKAO)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, BAS2)
SL.box(-FX - 2.9, FX + 2.9, -1, 0.4, -FZ - 2.9, FZ + 2.9, SEA)
SL.box(-FX - 1.9, FX + 1.9, 14.0, 15.6, -FZ - 1.9, FZ + 1.9, GRASS)
SL.box(-FX - 1.0, FX + 1.0, 15.6, 19.0, -FZ - 1.0, FZ + 1.0, GRASS2)
SL.box(-FX - 0.9, FX + 0.9, 0.4, 14.0, -FZ - 0.9, FZ + 0.9, BAS)
SL.box(-4.2, 4.2, 3.0, 12.6, -FZ - 1.4, -FZ, "8E8A86")
for s in (-1, 1):
    SL.box(s * FX, s * (FX + 1.9), 2.6, 13.0, -5.4, 3.0, BAS2)
    SL.box(s * FX, s * (FX + 1.8), 13.8, 16.6, -3.6, 1.2, PUKAO)
    for sz in (-1, 1):
        SL.box(s * (FX + 0.4), s * (FX + 1.4), 15.4, 18.4, sz * (FZ + 0.4), sz * (FZ + 1.4), TRUNK)
        SL.box(s * (FX - 1.0), s * (FX + 4.0), 18.0, 19.0, sz * (FZ - 1.0) - 1.5, sz * (FZ + 1.0) + 1.5, LEAF)

F.build(exhibit=(AHU[0], TOP, AHU[1], 3.2), lamps=[("Hall", (0, 14, 6), 3200, (1.0, 0.85, 0.75)),
                                                   ("Spot", (0, 13, -3), 3000, (1.0, 0.95, 0.85))])
