"""Этаж «Тёмная корона хаоса» музея-небоскрёба (третья партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — цитадель тёмного чародея. Снаружи — кладка из чёрного обсидиана со швами, контрфорсы с острыми
пинаклями, стрельчатые окна с фиолетовым светом и тёмным переплётом; спереди — глубокий стрельчатый портал из трёх
уступов, в проёме — фиолетовая мгла полосами, перед ним парит кольцо рун, к порталу тянутся цепи; весь парапет —
гигантская тёмная корона: острые зубцы с самоцветами по кругу; над карнизом парят обломки обсидиана со светящимися
трещинами; бока — светящиеся рунные камни; тыл — тонкий шпиль. Внутри — склеп короны: тёмный пол с рунным кругом
(кольца и насечки), стены со стрельчатыми нишами, в которых тлеет свет, обсидиановые колонны с фиолетовыми жаровнями,
парящие камни вокруг экспоната, цепи из дальних углов к алтарю, рунный круг на потолке; экспонат — на ступенчатом
алтаре с золотым кантом.
Запуск: blender --background --factory-startup --python scripts/blender/floor_chaoscrown.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab, taper  # noqa: E402

OBS, OBS2, OBS3, STONE, STONE2 = "2A2238", "362C48", "1E1828", "4A4060", "5A5072"
PURP, PURP2, PURP3, MAG, GOLDC, GOLDC2, IRON = "9A4AFF", "6A2AC8", "4A1E90", "E040A0", "C8A030", "A88420", "3A3A44"

F = B.Floor("CC", "ChaosCrown", quiet=(OBS3, STONE), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def lancet(cx, y0, w, h, n=6):
    """Стрельчатая арка: прямые бока до y0 + h - w*1.2, верх — два дуговых ската к острию."""
    ys = y0 + h - w * 1.3
    left = [(cx - w + w * (1 - math.cos(math.pi / 2 * k / n)), ys + w * 1.3 * math.sin(math.pi / 2 * k / n)) for k in range(n + 1)]
    right = [(2 * cx - x, y) for x, y in reversed(left)]
    return [(cx - w, y0)] + left + right[1:] + [(cx + w, y0)]


def shard(p, g, cx, cy, cz, r, seed):
    """Парящий обломок обсидиана: неровный многогранник со светящейся трещиной снизу."""
    top = [(cx + r * (0.7 + 0.5 * rng(seed, k)) * math.cos(2 * math.pi * k / 5), cy + 0.3 * rng(k, seed),
            cz + r * (0.7 + 0.5 * rng(k, seed, 2)) * math.sin(2 * math.pi * k / 5)) for k in range(5)]
    p.cone(top, (cx + 0.2 * r, cy + r * 1.1, cz - 0.1 * r), OBS2)
    p.cone(list(reversed(top)), (cx - 0.1 * r, cy - r * 1.4, cz + 0.1 * r), OBS)
    g.prism_xz(K.octa(cx, cz, r * 0.35, r * 0.35, r * 0.14), cy - r * 0.6, cy - r * 0.45, MAG)


def rune_ring(prism_ring, cx, cz, r, y, color, ticks=12):
    prism_ring(K.ngon(cx, cz, r, 24), K.ngon(cx, cz, r - 0.18, 24), y, y + 0.04, color)
    out = []
    for k in range(ticks):
        t = 2 * math.pi * k / ticks
        c, s = math.cos(t), math.sin(t)
        w = 0.12
        L0, L1 = r + 0.25, r + 0.25 + (0.9 if k % 3 == 0 else 0.5)
        out.append([(cx + c * L0 - s * w, cz + s * L0 + c * w), (cx + c * L1 - s * w, cz + s * L1 + c * w),
                    (cx + c * L1 + s * w, cz + s * L1 - c * w), (cx + c * L0 + s * w, cz + s * L0 - c * w)])
    return out


# ══ ФАСАД: цитадель под короной ═══════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, OBS, OBS, OBS3)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 3.88, -half - 3.88, half + 3.88, -1.0, -0.2, OBS3)
    B.chamfer(FR, axis, fixed, out, -half - 1.9, half + 1.9, [(0.0, -0.2), (1.9, -0.2), (1.2, 2.0), (0.0, 2.0)], OBS2)
    for r, (y0, y1) in enumerate(((2, 4), (4, 6), (6, 8), (8, 10), (10, 12), (12, 14))):  # обсидиановая кладка
        a, k = -half - (r % 2) * 1.5, 0
        while a < half:
            w = 3 + int(rng(fi, r, k) * 3)
            b0, b1 = max(a, -half), min(a + w, half)
            if b1 - b0 > 0.4:
                slab(FR, axis, fixed, out, 0.88, b0 + 0.06, b1 - 0.06, y0 + 0.06, y1 - 0.06, (OBS, OBS2, OBS)[k % 3])
            a, k = a + w, k + 1
    slab(FS, axis, fixed, out, 0.8, -half, half, 2.0, 14.0, PURP3)  # швы светятся тёмным фиолетовым
    slab(FR, axis, fixed, out, 1.88, -half - 0.6, half + 0.6, 14.0, 15.0, STONE)  # карниз
    slab(FG, axis, fixed, out, 1.95, -half - 0.6, half + 0.6, 14.4, 14.6, PURP2)
    slab(FR, axis, fixed, out, 1.88, -half - 0.6, half + 0.6, 15.0, 16.0, OBS2)
    # корона: острые зубцы с самоцветами
    n = int(2 * half // 4.0)
    for k in range(n):
        a = -half + (k + 0.5) * 2 * half / n
        h = 18.9 if k % 2 == 0 else 17.8
        d0, d1 = sorted((fixed + out * 0.4, fixed + out * 1.7))
        prism = FS.prism_xy if axis == "z" else FS.prism_zy
        prism([(a - 1.8, 16.0), (a + 1.8, 16.0), (a + 0.25, h), (a - 0.25, h)], d0, d1, OBS2)
        g0, g1 = sorted((fixed + out * 1.7, fixed + out * 1.85))
        (FG.prism_xy if axis == "z" else FG.prism_zy)(K.octa(a, 16.9, 0.45, 0.55, 0.2), g0, g1, MAG if k % 2 else PURP)
        c0, c1 = sorted((fixed + out * 1.68, fixed + out * 1.78))
        (FS.prism_xy if axis == "z" else FS.prism_zy)(K.octa(a, 16.9, 0.62, 0.72, 0.26), c0, c1, GOLDC)
    # контрфорсы с пинаклями и стрельчатые окна между ними
    for k in range(4):
        a = -half + (k + 0.5) * 2 * half / 4
        if fi == 0 and abs(a) < 8.0:
            continue
        slab(FR, axis, fixed, out, 1.88, a - 0.8, a + 0.8, 2.0, 13.0, OBS2)
        B.chamfer(FS, axis, fixed, out, a - 0.8, a + 0.8, [(0.0, 13.0), (1.88, 13.0), (1.2, 14.0), (0.0, 14.0)], OBS2)
        x, z = (a, fixed + out * 1.0) if axis == "z" else (fixed + out * 1.0, a)
        FS.cone([(x - 0.5, 14.0, z - 0.5), (x + 0.5, 14.0, z - 0.5), (x + 0.5, 14.0, z + 0.5), (x - 0.5, 14.0, z + 0.5)],
                (x, 15.8, z), STONE)
    wins = (-16.0, -10.2, 10.2, 16.0) if fi == 0 else ((-9.0, 0.0, 9.0) if axis == "z" else (-9.0, 0.0, 9.0))
    for a in wins:  # на фасаде — четыре окна в ряд (без пары «глаз» у портала)
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 1.2))
        prism = FS.prism_xy if axis == "z" else FS.prism_zy
        gprism = FG.prism_xy if axis == "z" else FG.prism_zy
        w_ = 1.3 if fi == 0 else 1.5
        prism(lancet(a, 4.0, w_, 8.6), d0, d1, STONE)
        g0, g1 = sorted((fixed + out * 1.2, fixed + out * 1.25))
        gprism(lancet(a, 4.4, w_ - 0.4, 7.8), g0, g1, PURP2)
        t0, t1 = sorted((fixed + out * 1.25, fixed + out * 1.35))
        prism([(a - 0.08, 4.4), (a + 0.08, 4.4), (a + 0.08, 11.6), (a - 0.08, 11.6)], t0, t1, OBS3)
        prism([(a - w_ + 0.4, 8.2), (a + w_ - 0.4, 8.2), (a + w_ - 0.4, 8.36), (a - w_ + 0.4, 8.36)], t0, t1, OBS3)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# портал: три уступа стрельчатой арки, мгла полосами, парящее кольцо рун, цепи
for k, (w, h, d) in enumerate(((6.0, 13.4, 2.6), (5.0, 12.2, 2.0), (4.0, 11.0, 1.4))):
    FS.frame_xy(lancet(0.0, 2.0, w, h), lancet(0.0, 2.0, w - 1.0, h - 1.2), -FZ - d, -FZ + 0.05, (STONE, OBS2, STONE2)[k])
for k, col in enumerate((PURP3, PURP2, PURP, PURP2, PURP3)):
    y0, y1 = 2.0 + 1.6 * k, 2.0 + 1.6 * (k + 1)
    FG.box(-3.0 + 0.3 * abs(k - 2), 3.0 - 0.3 * abs(k - 2), y0, y1, -FZ - 1.0, -FZ - 0.92, col)
FG.prism_xy(lancet(0.0, 10.0, 2.2, 2.6), -FZ - 1.0, -FZ - 0.92, PURP3)
FG.frame_xy(K.ngon(0.0, 7.6, 3.6, 16), K.ngon(0.0, 7.6, 3.35, 16), -FZ - 3.6, -FZ - 3.5, MAG)
for k in range(8):
    t = 2 * math.pi * k / 8
    x, y = 3.9 * math.cos(t), 7.6 + 3.9 * math.sin(t)
    FG.prism_xy(K.octa(x, y, 0.22, 0.4 if k % 2 else 0.22, 0.09), -FZ - 3.62, -FZ - 3.5, MAG)
for s in (-1, 1):
    pts = [(s * 13.0, 15.0, -FZ - 1.6), (s * 9.0, 12.0, -FZ - 2.6), (s * 6.2, 10.6, -FZ - 2.8)]
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        for m in range(int(L // 0.7)):
            t0 = m / int(L // 0.7)
            q = tuple(a[i] + (b[i] - a[i]) * t0 for i in range(3))
            FS.box(q[0] - 0.18, q[0] + 0.18, q[1] - 0.3, q[1] + 0.3, q[2] - (0.18 if m % 2 else 0.06),
                   q[2] + (0.18 if m % 2 else 0.06), IRON)
# парящие обломки над карнизом и у углов
for k, (x, y, z, r) in enumerate(((-12.6, 16.6, -FZ - 3.6, 1.3), (11.0, 16.2, -FZ - 4.0, 1.1), (-FX - 3.4, 11.0, -10.0, 1.4),
                                  (FX + 3.6, 9.4, 6.0, 1.2), (-5.4, 17.2, -FZ - 4.6, 0.9))):
    shard(FS, FG, x, y, z, r, k)
# бока: рунные камни; тыл: шпиль
for s in (-1, 1):
    fx = s * FX
    for k, z in enumerate((-12.0, 12.0)):
        FS.box(fx + s * 0.9, fx + s * 3.4, -0.2, 4.6, z - 1.0, z + 1.0, STONE)
        for m in range(3):
            FG.box(fx + s * 3.4, fx + s * 3.46, 1.0 + 1.1 * m, 1.6 + 1.1 * m, z - 0.5 + 0.2 * m, z + 0.1 + 0.2 * m, PURP)
FS.prism_xz(K.octa(0.0, FZ + 2.2, 1.6, 1.6, 0.65), -0.2, 12.0, OBS2)
FS.cone([(x, 12.0, z) for x, z in K.octa(0.0, FZ + 2.2, 1.6, 1.6, 0.65)], (0.0, 18.9, FZ + 2.2), OBS)
FG.prism_xz(K.octa(0.0, FZ + 2.2, 1.66, 1.66, 0.67), 9.0, 9.4, PURP2)

# ══ ИНТЕРЬЕР: склеп короны ════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.6
px, pz = PED
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), OBS3)
for i in range(-4, 5):  # плиты пола
    IS.box(4.0 * i - 0.06, 4.0 * i + 0.06, 0.02, 0.05, ZF, ZB, OBS2)
for j in range(-3, 4):
    IS.box(-W, W, 0.02, 0.05, 4.2 * j - 0.06, 4.2 * j + 0.06, OBS2)
for r in (5.6, 7.6):  # рунный круг на полу
    for pts in rune_ring(IG.frame_xz, px, pz, r, 0.06, PURP2 if r > 6 else PURP, 16 if r > 6 else 12):
        IG.prism_xz(pts, 0.06, 0.1, PURP2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    slab(IQ, axis, fixed, out, 0.7, -half, half, 0.0, C, OBS3)
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.0, OBS2)
    n = 4 if axis == "z" else 4
    for k in range(n):  # стрельчатые ниши с тлеющим светом
        a = -half + (k + 0.5) * 2 * half / n
        if gap and abs(a) < DOOR[0] + 3.0:
            continue
        prism = IS.prism_xy if axis == "z" else IS.prism_zy
        d0, d1 = sorted((fixed + out * 0.7, fixed + out * 0.88))
        prism(lancet(a, 1.0, 2.4, 10.6), d0, d1, STONE)
        g0, g1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
        # дальняя стена светится ярче: тёмные зубцы короны читаются силуэтом на светлой сирени, а не тонут во тьме
        (IG.prism_xy if axis == "z" else IG.prism_zy)(lancet(a, 1.4, 1.8, 9.6), g0, g1, "B88AFF" if idx == 2 else PURP3)
    for k in range(n + 1):  # тяжи между нишами
        a = -half + k * 2 * half / n
        if gap and abs(a) < DOOR[0] + 1.0:
            continue
        slab(IR, axis, fixed, out, 1.88, max(a - 0.9, -half), min(a + 0.9, half), 0.0, 12.0, OBS)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 12.0, OBS2)
    slab(IR, axis, fixed, out, 1.88, -half, half, 12.0, 13.0, STONE)
    slab(IG, axis, fixed, out, 1.95, -half, half, 12.4, 12.6, PURP2)
    slab(IR, axis, fixed, out, 0.88, -half, half, 13.0, C, OBS2)
# колонны с фиолетовыми жаровнями
for x, z in ((-9.0, -11.0), (9.0, -11.0), (-11.0, 3.0), (11.0, 3.0)):
    IR.prism_xz(K.octa(x, z, 1.3, 1.3, 0.54), 0.0, 1.0, STONE)
    IS.prism_xz(K.octa(x, z, 1.0, 1.0, 0.41), 1.0, 8.0, OBS2)
    IS.prism_xz(K.octa(x, z, 1.4, 1.4, 0.58), 8.0, 8.6, GOLDC2)
    IS.prism_xz(K.octa(x, z, 1.1, 1.1, 0.45), 8.6, 9.2, OBS)
    IG.prism_xz(K.octa(x, z, 0.8, 0.8, 0.33), 9.2, 10.2, PURP)
    IG.prism_xz(K.octa(x, z, 0.4, 0.4, 0.16), 10.2, 11.0, MAG)
# парящие камни вокруг экспоната
for k in range(7):
    t = 2 * math.pi * (k + 0.3) / 7
    x, z = px + 6.8 * math.cos(t), pz + 6.0 * math.sin(t)
    if z > pz + 3.0 and abs(x) < 4.0:
        continue
    shard(IS, IG, x, 6.0 + 3.0 * rng(k, 5), z, 0.5 + 0.35 * rng(k, 6), k + 20)
# цепи из дальних углов к алтарю
for sx in (-1, 1):
    a, b = (sx * (W - 0.5), 15.0, ZF + 0.5), (px + sx * 3.4, 1.4, pz - 2.6)
    L = math.dist(a, b)
    n = int(L // 0.8)
    for m in range(n):
        q = tuple(a[i] + (b[i] - a[i]) * m / n for i in range(3))
        w = 0.2 if m % 2 else 0.07
        IS.box(q[0] - w, q[0] + w, q[1] - 0.32, q[1] + 0.32, q[2] - (0.07 if m % 2 else 0.2), q[2] + (0.07 if m % 2 else 0.2),
               IRON)
# рунный круг на потолке
for pts in rune_ring(IG.frame_xz, px, pz, 4.6, C - 0.1, PURP2, 12):
    IG.prism_xz(pts, C - 0.1, C - 0.06, PURP2)
# ступенчатый алтарь
IR.prism_xz(K.octa(px, pz, 4.6, 4.2, 1.8), 0.0, 0.5, OBS2)
IR.prism_xz(K.octa(px, pz, 3.8, 3.5, 1.5), 0.5, 1.0, STONE)
IR.prism_xz(K.octa(px, pz, 3.0, 2.8, 1.2), 1.0, TOP, OBS)
IS.frame_xz(K.octa(px, pz, 3.1, 2.9, 1.25), K.octa(px, pz, 3.0, 2.8, 1.2), TOP - 0.16, TOP + 0.02, GOLDC)
IG.frame_xz(K.octa(px, pz, 4.7, 4.3, 1.84), K.octa(px, pz, 4.6, 4.2, 1.8), 0.3, 0.42, MAG)
B.lift_leaves(IS, OBS2, PURP2)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, OBS)
SL.box(-FX - 1.9, FX + 1.9, -1.0, 2.0, -FZ - 1.9, FZ + 1.9, OBS2)
SL.box(-FX - 1.9, FX + 1.9, 14.0, 16.0, -FZ - 1.9, FZ + 1.9, STONE)
for s in (-1, 1):
    SL.prism_xy([(s * 2.0, 16.0), (s * 8.0, 16.0), (s * 5.0, 18.9)], -FZ - 1.7, -FZ - 0.4, OBS2)
    SL.prism_xy([(s * 10.0, 16.0), (s * 16.0, 16.0), (s * 13.0, 18.9)], -FZ - 1.7, -FZ - 0.4, OBS2)
SL.box(-6.0, 6.0, 2.0, 13.0, -FZ - 2.6, -FZ, STONE)
SL.box(-3.0, 3.0, 2.0, 10.0, -FZ - 2.7, -FZ - 2.6, PURP2)

F.build(exhibit=(PED[0], TOP, PED[1], 3.2), lamps=[("Hall", (0, 14, 6), 2000, (0.85, 0.8, 1.0)),
                                                   ("Spot", (0, 13, -3), 3200, (0.95, 0.92, 1.0))])
