"""Этаж «Статуя Свободы» музея-небоскрёба (вторая партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — пьедестал статуи на острове в гавани. Снаружи — гранитный пьедестал классического ордера:
снизу звёздчатый форт (острые бастионы на углах) в воде гавани, стены из розовато-серого гранита с рустом,
дорические пилястры, пояс круглых щитов, наверху — лоджия с колонками; всё медное — зелёное (патина): на фасаде
огромный рельеф руки с факелом и золотым светящимся пламенем, над порталом — лучи короны, по бокам — скрижаль и
высокие окна в медных рамах, на углах — медные фонари.
Внутри — зал под сводом из плитки «ёлочкой» (крем и терракота) с арками-нервюрами; нижняя часть стен — гранит,
выше — высокие арочные окна с видом на гавань и город; статуя на ступенчатом гранитном постаменте со звездой,
вокруг — медная копия пламени факела, корона-лучи, листы зелёной меди, скамьи, латунные стойки с канатом.
Запуск: blender --background --factory-startup --python scripts/blender/floor_liberty.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab  # noqa: E402

GRAN, GRAN2, GRAN3, GRAND = "CDB8A6", "B8A290", "DDCDBD", "84705E"
PAT, PAT2, PAT3, COPPER = "5FB59A", "3E8F78", "8AD0B8", "C87533"
FLAME, FLAME2, GOLD, NAVY, SEA, SEA2 = "FFC24A", "FF8A2A", "E8B84A", "23344F", "3A8FC0", "2A6E9E"
CREAM, TERRA, SKY, SKY2, CITY, CITY2 = "F0E6D2", "C98A5A", "9ED4F0", "C8E8F8", "6E86A8", "566E90"
WOOD, BRASS, VELVET = "6A4428", "D8A84A", "A8263A"

F = B.Floor("SL", "StatueOfLiberty", quiet=(SEA, SEA2, SKY, SKY2, CREAM), bevel_min=1.0, keep_arch=True)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL

STAR7 = [(-75 + 25 * k) for k in range(7)]  # углы лучей короны, градусы от вертикали


def rays(p, axis, fixed, out, a, y, r0, r1, d0, d1, color):
    """Лучи короны веером над точкой (a, y)."""
    lo, hi = sorted((fixed + out * d0, fixed + out * d1))
    for t in STAR7:
        t = math.radians(t)
        u, v = math.sin(t), math.cos(t)
        n0, n1 = (-v * 0.45, u * 0.45), (-v * 0.08, u * 0.08)
        pts = [(a + u * r0 + n0[0], y + v * r0 + n0[1]), (a + u * r1 + n1[0], y + v * r1 + n1[1]),
               (a + u * r1 - n1[0], y + v * r1 - n1[1]), (a + u * r0 - n0[0], y + v * r0 - n0[1])]
        (p.prism_xy if axis == "z" else p.prism_zy)(pts, lo, hi, color)


# ══ ФАСАД: гранитный пьедестал на звёздчатом форте ═══════════════════════════════════════════════════════════
B.shell_planes(F, GRAND, GRAND, CREAM)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.2, SEA)  # вода гавани
    slab(FR, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, -0.2, 2.0, GRAN2)  # стена форта
    slab(FS, axis, fixed, out, 1.95, -half - 1.95, half + 1.95, 2.0, 2.4, GRAN3)
    # руст нижнего яруса: ряды блоков со швами
    for r in range(3):
        y0 = 2.4 + 1.6 * r
        off = 0.0 if r % 2 == 0 else 1.5
        a = -half - off
        while a < half:
            a0, a1 = max(a, -half), min(a + 3.0, half)
            slab(FR, axis, fixed, out, 0.88, a0 + 0.06, a1 - 0.06, y0 + 0.06, y0 + 1.54, GRAN)
            a += 3.0
    slab(FS, axis, fixed, out, 0.8, -half, half, 2.4, 7.2, GRAND)
    slab(FS, axis, fixed, out, 1.1, -half - 1.1, half + 1.1, 7.2, 7.6, GRAN3)
    # средний ярус: гладкий гранит, пилястры, пояс щитов
    slab(FR, axis, fixed, out, 0.88, -half, half, 7.6, 14.0, GRAN3)
    for e in (-1, 1):
        for a in (e * (half - 1.4), e * (half - 6.8)):
            slab(FS, axis, fixed, out, 1.4, a - 0.8, a + 0.8, 7.6, 13.4, GRAN)
            slab(FS, axis, fixed, out, 1.6, a - 1.0, a + 1.0, 13.0, 13.5, GRAN2)
    slab(FS, axis, fixed, out, 1.5, -half - 1.5, half + 1.5, 13.5, 14.0, GRAN2)
    n = 7 if axis == "z" else 6
    for k in range(n):
        a = -half + 2.4 + (2 * half - 4.8) * k / (n - 1)
        (FS.prism_xy if axis == "z" else FS.prism_zy)(K.octa(a, 14.8, 0.6, 0.6, 0.25), fixed + out * 0.88,
                                                     fixed + out * 1.3, PAT)
    # лоджия: колонки, балюстрада, карниз
    slab(FR, axis, fixed, out, 0.88, -half, half, 14.0, 19.0, GRAN)
    slab(FS, axis, fixed, out, 1.7, -half - 1.7, half + 1.7, 15.6, 16.0, GRAN3)
    for k in range(int(2 * half // 2.2)):
        a = -half + 1.1 + 2.2 * k
        slab(FS, axis, fixed, out, 1.5, a - 0.28, a + 0.28, 16.0, 18.2, GRAN3)
        slab(FS, axis, fixed, out, 1.0, a + 0.4, a + 1.8, 16.2, 18.0, NAVY)
    slab(FS, axis, fixed, out, 1.9, -half - 1.9, half + 1.9, 18.2, 19.0, GRAN2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# бастионы-звёзды на углах форта
for sx in (-1, 1):
    for sz in (-1, 1):
        cx, cz = sx * (FX + 1.0), sz * (FZ + 1.0)
        FS.prism_xz([(cx - sx * 2.8, cz), (cx + sx * 2.6, cz + sz * 2.6), (cx, cz - sz * 2.8)], -0.2, 2.2, GRAN2)
        FS.prism_xz([(cx - sx * 2.4, cz), (cx + sx * 2.2, cz + sz * 2.2), (cx, cz - sz * 2.4)], 2.2, 2.5, GRAN3)
        # медный фонарь
        lx, lz = cx + sx * 1.0, cz + sz * 1.0
        FS.prism_xz(K.octa(lx, lz, 0.35, 0.35, 0.14), 2.5, 6.0, PAT2)
        FS.prism_xz(K.octa(lx, lz, 0.6, 0.6, 0.25), 6.0, 6.2, PAT)
        FG.prism_xz(K.octa(lx, lz, 0.45, 0.45, 0.18), 6.2, 7.2, "FFE7A0")
        FS.prism_xz(K.octa(lx, lz, 0.6, 0.6, 0.25), 7.2, 7.5, PAT)
# перед: портал, лучи короны, рельеф факела
FS.box(-4.2, 4.2, 2.4, 10.4, -FZ - 1.0, -FZ, GRAND)
FS.prism_xy(K.octa(0, 10.4, 4.2, 2.0, 1.2), -FZ - 1.0, -FZ, GRAND)
FS.frame_xy(K.octa(0, 10.4, 4.9, 2.6, 1.5), K.octa(0, 10.4, 4.2, 2.0, 1.2), -FZ - 1.6, -FZ, GRAN3)
for s in (-1, 1):
    FS.box(s * 4.2, s * 4.9, 2.4, 10.4, -FZ - 1.6, -FZ, GRAN3)
    FS.box(s * 0.05, s * 3.6, 2.4, 9.6, -FZ - 1.2, -FZ - 1.0, PAT2)  # медные двери
    for k in range(3):
        FS.box(s * 0.5, s * 3.1, 3.2 + 2.2 * k, 4.8 + 2.2 * k, -FZ - 1.3, -FZ - 1.2, PAT)
rays(FS, "z", -FZ, -1, 0.0, 12.6, 1.2, 3.4, 1.6, 1.9, PAT)
FS.prism_xy(K.octa(0, 12.6, 1.1, 0.7, 0.3), -FZ - 2.0, -FZ - 1.6, PAT2)
F.objects(True)
for s in (-1, 1):  # рука с факелом — рельеф на боковых полях фасада
    x = s * 11.6
    FS.box(x - 0.9, x + 0.9, 7.6, 11.0, -FZ - 1.6, -FZ, PAT2)  # предплечье
    FS.box(x - 1.2, x + 1.2, 11.0, 12.4, -FZ - 1.8, -FZ, PAT)  # кулак
    FS.prism_xy([(x - 0.7, 12.4), (x + 0.7, 12.4), (x + 1.2, 13.4), (x - 1.2, 13.4)], -FZ - 1.9, -FZ, PAT)
    FS.prism_xy(K.octa(x, 13.6, 1.4, 0.35, 0.15), -FZ - 2.0, -FZ, GOLD)
    FG.prism_xy([(x - 1.0, 13.9), (x + 1.0, 13.9), (x + 0.6, 15.0), (x + 0.2, 15.6), (x - 0.3, 15.2), (x - 0.7, 15.5),
                 (x - 0.9, 14.6)], -FZ - 1.9, -FZ - 0.9, FLAME)
    FG.prism_xy([(x - 0.5, 14.0), (x + 0.5, 14.0), (x + 0.2, 14.9), (x - 0.3, 14.7)], -FZ - 2.05, -FZ - 1.9, FLAME2)
F.objects(False)
# высокие окна в медных рамах между порталом и факелами
for s in (-1, 1):
    x = s * 7.6
    FS.box(x - 1.5, x + 1.5, 8.0, 12.8, -FZ - 1.1, -FZ, PAT2)
    FG.box(x - 1.2, x + 1.2, 8.3, 12.5, -FZ - 1.15, -FZ - 1.1, "BFE6F2")
    FS.box(x - 0.08, x + 0.08, 8.3, 12.5, -FZ - 1.25, -FZ - 1.15, PAT2)
    FS.box(x - 1.2, x + 1.2, 10.3, 10.45, -FZ - 1.25, -FZ - 1.15, PAT2)
    FS.box(x - 1.8, x + 1.8, 12.8, 13.3, -FZ - 1.3, -FZ, GRAN2)
    FS.box(x - 1.7, x + 1.7, 7.6, 8.0, -FZ - 1.3, -FZ, GRAN2)
# бока: скрижаль и высокие окна в медных рамах
for s in (-1, 1):
    fx = s * FX
    FS.prism_zy([(-2.2, 8.2), (2.2, 8.2), (2.2, 12.4), (-2.2, 12.8)], fx, fx + s * 1.4, PAT2)
    for k in range(4):
        FS.box(fx + s * 1.4, fx + s * 1.5, 9.0 + 0.8 * k, 9.2 + 0.8 * k, -1.6, 1.6, PAT3)
    for z in (-10.0, 10.0):
        FS.box(fx, fx + s * 1.4, 2.6, 6.8, z - 1.6, z + 1.6, PAT2)
        FG.box(fx + s * 1.4, fx + s * 1.45, 2.9, 6.5, z - 1.3, z + 1.3, "BFE6F2")
        FS.box(fx + s * 1.45, fx + s * 1.55, 2.9, 6.5, z - 0.08, z + 0.08, PAT2)
        FS.box(fx, fx + s * 1.3, 8.6, 12.6, z - 1.3, z + 1.3, PAT2)
        FG.box(fx + s * 1.3, fx + s * 1.35, 8.9, 12.3, z - 1.0, z + 1.0, "BFE6F2")
F.objects(True)
# тыл: причал с медными тумбами
FS.box(-7.0, 7.0, -0.2, 0.6, FZ + 1.9, FZ + 2.8, WOOD)
for x in (-6.0, 0.0, 6.0):
    FS.prism_xz(K.octa(x, FZ + 2.35, 0.35, 0.35, 0.14), 0.6, 1.4, PAT2)

F.objects(False)
# ══ ИНТЕРЬЕР: зал под сводом с видом на гавань ════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), CREAM)
for i in range(-4, 5):  # пол: гранитные полосы
    IS.box(-W, W, 0.02, 0.05, 3.4 * i - 0.1, 3.4 * i + 0.1, GRAN2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 3.0, GRAN)
        slab(IS, axis, fixed, out, 1.0, a0, a1, 3.0, 3.3, GRAN3)
    # окна: вид на гавань (небо, город, вода) в медных арках
    n = 3
    for i in range(n):
        a = -half + 2 * half * (i + 0.5) / n
        if gap and abs(a) < DOOR[0] + 2:
            continue
        lo, hi = a - 3.2, a + 3.2
        slab(IQ, axis, fixed, out, 0.88, lo, hi, 3.3, 5.5, SEA2)
        slab(IQ, axis, fixed, out, 0.88, lo, hi, 5.5, 13.0, SKY)
        for k in range(6):  # силуэт города
            b = lo + 0.5 + 0.95 * k
            h = 1.2 + rng(idx, i, k) * 3.4
            slab(IS, axis, fixed, out, 0.95, b, b + 0.8, 5.5, 5.5 + h, CITY if k % 2 else CITY2)
        slab(IS, axis, fixed, out, 1.05, lo - 0.4, lo, 3.3, 13.0, PAT2)
        slab(IS, axis, fixed, out, 1.05, hi, hi + 0.4, 3.3, 13.0, PAT2)
        slab(IS, axis, fixed, out, 1.0, a - 0.1, a + 0.1, 3.3, 13.0, PAT2)
        slab(IS, axis, fixed, out, 1.0, lo, hi, 8.6, 8.8, PAT2)
        slab(IS, axis, fixed, out, 1.05, lo - 0.4, hi + 0.4, 13.0, 13.6, PAT2)
        mid = (lo + hi) / 2
        (IS.frame_xy if axis == "z" else IS.frame_zy)(K.octa(mid, 13.6, 3.6, 1.8, 1.0), K.octa(mid, 13.6, 3.2, 1.4, 0.8),
                                                      fixed + out * 0.88, fixed + out * 1.05, PAT2)
    # простенки — гранит, выше — крем
    for i in range(n + 1):
        a = -half + 2 * half * i / n
        lo, hi = max(-half, a - 2 * half / n / 2 + 3.6), min(half, a + 2 * half / n / 2 - 3.6)
    slab(IR, axis, fixed, out, 0.7, -half, half, 3.3, 13.6, GRAN3)
    slab(IR, axis, fixed, out, 0.7, -half, half, 13.6, C, CREAM)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 13.6, GRAN3)
# свод: плитка «ёлочкой» крем/терракота, арки-нервюры
for i in range(-8, 8):
    for j in range(-8, 8):
        x, z = 2.0 * i + 1.0, 1.8 * j + 0.9
        if abs(x) > 16 or abs(z) > 15:
            continue
        if (i + j) % 2 == 0:
            IS.box(x - 0.9, x + 0.9, C - 0.06, C - 0.02, z - 0.3, z + 0.3, TERRA)
        else:
            IS.box(x - 0.3, x + 0.3, C - 0.06, C - 0.02, z - 0.8, z + 0.8, "E8D0B0")
for k in (-11.0, -3.0, 5.0, 13.0):
    beam(IS, (-W, 13.6, k), (-8.0, 17.4, k), 0.5, 0.6, GRAN3)
    beam(IS, (-8.0, 17.4, k), (8.0, 17.4, k), 0.5, 0.6, GRAN3)
    beam(IS, (8.0, 17.4, k), (W, 13.6, k), 0.5, 0.6, GRAN3)
F.objects(True)
# постамент: ступени со звездой
px, pz = PED
IR.box(px - 4.6, px + 4.6, 0.0, 0.6, pz - 4.6, pz + 4.6, GRAN2)
IR.box(px - 3.6, px + 3.6, 0.6, TOP, pz - 3.6, pz + 3.6, GRAN)
# медное пламя на стойке, корона-лучи, листы меди
for s, (x, z) in ((-1, (-9.5, -10.0)), (1, (9.5, -10.0))):
    IS.prism_xz(K.octa(x, z, 1.0, 1.0, 0.4), 0.0, 0.8, GRAN2)
    IS.prism_xz(K.octa(x, z, 0.35, 0.35, 0.14), 0.8, 4.0, PAT2)
    IS.prism_xz(K.octa(x, z, 0.9, 0.9, 0.37), 4.0, 4.5, GOLD)
    IG.prism_xz(K.octa(x, z, 0.8, 0.8, 0.33), 4.5, 5.6, FLAME2)
    IG.prism_xz(K.octa(x, z, 0.5, 0.5, 0.2), 5.6, 6.8, FLAME)
    IG.prism_xz(K.octa(x + 0.2, z, 0.25, 0.25, 0.1), 6.8, 7.6, FLAME)
rays(IS, "x", -W, 1, 9.5, 14.2, 1.2, 3.2, 0.9, 1.2, PAT)  # корона над скамьями слева
IS.frame_zy(K.octa(9.5, 14.2, 1.4, 0.9, 0.45), K.octa(9.5, 14.2, 1.0, 0.55, 0.28), -W + 0.9, -W + 1.25, PAT2)
for x, z, w in ((-13.0, 2.0, 1.6), (12.5, 3.0, 1.8)):  # листы меди на подставках
    IS.box(x - 0.15, x + 0.15, 0.0, 3.4, z - w, z + w, PAT2)
    IS.box(x - 0.2, x + 0.2, 0.0, 0.4, z - w - 0.3, z + w + 0.3, WOOD)
for x in (-6.5, 6.5):  # скамьи
    for z in (3.5, 7.5):
        IS.box(x - 2.2, x + 2.2, 0.8, 1.0, z - 0.6, z + 0.6, WOOD)
        for e in (-1, 1):
            IS.box(x + e * 1.8 - 0.15, x + e * 1.8 + 0.15, 0.0, 0.8, z - 0.5, z + 0.5, NAVY)
for z in (0.0, -6.0):  # латунные стойки с канатом вокруг постамента
    for s in (-1, 1):
        x = s * 6.0
        IS.prism_xz(K.octa(x, z, 0.3, 0.3, 0.12), 0.0, 0.1, BRASS)
        IS.box(x - 0.07, x + 0.07, 0.1, 2.4, z - 0.07, z + 0.07, BRASS)
        IS.prism_xz(K.octa(x, z, 0.18, 0.18, 0.07), 2.4, 2.6, BRASS)
for s in (-1, 1):
    beam(IS, (s * 6.0, 2.3, 0.0), (s * 6.0, 1.9, -3.0), 0.12, 0.12, VELVET)
    beam(IS, (s * 6.0, 1.9, -3.0), (s * 6.0, 2.3, -6.0), 0.12, 0.12, VELVET)
F.objects(False)
B.lift_leaves(IS, PAT2, GOLD)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, GRAN3)
SL.box(-FX - 2.9, FX + 2.9, -1, -0.2, -FZ - 2.9, FZ + 2.9, SEA)
SL.box(-FX - 1.9, FX + 1.9, -0.2, 2.4, -FZ - 1.9, FZ + 1.9, GRAN2)
SL.box(-FX - 0.9, FX + 0.9, 2.4, 7.2, -FZ - 0.9, FZ + 0.9, GRAN)
SL.box(-FX - 1.9, FX + 1.9, 18.2, 19.0, -FZ - 1.9, FZ + 1.9, GRAN2)
SL.box(-FX - 1.0, FX + 1.0, 16.0, 18.2, -FZ - 1.0, FZ + 1.0, NAVY)
SL.box(-4.9, 4.9, 2.4, 12.4, -FZ - 1.6, -FZ, PAT2)
SL.box(-3.4, 3.4, 12.6, 15.6, -FZ - 1.9, -FZ, PAT)
for s in (-1, 1):
    SL.box(s * 10.4, s * 12.8, 7.6, 13.4, -FZ - 1.8, -FZ, PAT)
    SL.box(s * 10.6, s * 12.6, 13.4, 15.6, -FZ - 1.9, -FZ - 0.9, FLAME)
    SL.box(s * FX, s * (FX + 1.4), 2.6, 12.8, -11.6, 11.6, PAT2)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 3000, (1.0, 0.97, 0.92)),
                                                   ("Spot", (0, 14, -3), 3200, (1.0, 0.98, 0.9))])
