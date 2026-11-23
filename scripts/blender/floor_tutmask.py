"""Этаж «Золотая маска Тутанхамона» музея-небоскрёба (вторая партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — вход в гробницу фараона. Снаружи — храмовый пилон из песчаника: две скошенные башни по сторонам
врат с карнизом-выкружкой в полосах золота и лазури, над вратами — крылатый солнечный диск, по всему этажу —
фриз в полоску «как платок немес» (лазурь и золото), на башнях — картуши с анкхом и скарабеем, у углов —
обелиски с золотыми навершиями; бока — колоннады с капителями-папирусами, сзади — ступени и ложные двери.
Внутри — сокровищница гробницы: потолок тёмно-синий в золотых звёздах, стены — лазурный цоколь, песчаник с
поясами росписи (золото, бирюза, красная охра), четыре колонны-папируса вокруг ступенчатого постамента из чёрного
камня с золотой кромкой, на нём — маска под лучом света; вокруг — сундуки, горы золотых монет, канопы, жаровни,
у лифта — два золотых анкха.
Запуск: blender --background --factory-startup --python scripts/blender/floor_tutmask.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, rng, slab  # noqa: E402

SANDST, SANDST2, SANDST3, SHADOW = "E8C98A", "D9B574", "C6A061", "8A6A3E"
GOLD, GOLD2, LAPIS, LAPIS2, TURQ, OCHRE = "F2C230", "C9921A", "2448A8", "1A3478", "2FB8B0", "B8452A"
BASALT, BASALT2, NIGHT, STAR, FLAME, FLAME2 = "2A2630", "3A3442", "1A2050", "FFD86A", "FFC24A", "FF8A2A"
WOOD, CREAM = "7A4A28", "F2E6C8"

F = B.Floor("TU", "TutMask", quiet=(SANDST2, NIGHT, LAPIS2), bevel_min=1.0, keep_arch=True)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def stripes(p, axis, fixed, out, depth, a0, a1, y0, y1, w, colors):
    """Полосы «немес» вдоль стены."""
    n = max(1, int(round((a1 - a0) / w)))
    for k in range(n):
        slab(p, axis, fixed, out, depth, a0 + (a1 - a0) * k / n, a0 + (a1 - a0) * (k + 1) / n, y0, y1,
             colors[k % len(colors)])


def column(p, x, z, y0, y1, r, cap_color):
    """Колонна-папирус: ствол с поясами, капитель раструбом, абака."""
    p.prism_xz(K.octa(x, z, r * 1.25, r * 1.25, r * 0.5), y0, y0 + 0.5, SANDST3)
    p.prism_xz(K.octa(x, z, r, r, r * 0.41), y0 + 0.5, y1 - 2.0, SANDST)
    for yy in (y0 + 1.2, y1 - 2.6):
        p.prism_xz(K.octa(x, z, r + 0.06, r + 0.06, r * 0.43), yy, yy + 0.35, LAPIS)
        p.prism_xz(K.octa(x, z, r + 0.08, r + 0.08, r * 0.44), yy + 0.35, yy + 0.55, GOLD)
    p.loft([(x + dx * r, y1 - 2.0, z + dz * r) for dx, dz in ((-1, -1), (1, -1), (1, 1), (-1, 1))],
           [(x + dx * r * 1.7, y1 - 0.6, z + dz * r * 1.7) for dx, dz in ((-1, -1), (1, -1), (1, 1), (-1, 1))], cap_color)
    p.box(x - r * 1.5, x + r * 1.5, y1 - 0.6, y1, z - r * 1.5, z + r * 1.5, SANDST3)


def ankh(p, axis, fixed, out, a, y, s, d0, d1, color):
    """Анкх: петля, перекладина, стержень."""
    lo, hi = sorted((fixed + out * d0, fixed + out * d1))
    shapes = [(K.octa(a, y + 1.6 * s, 0.75 * s, 0.95 * s, 0.35 * s), K.octa(a, y + 1.6 * s, 0.4 * s, 0.55 * s, 0.18 * s))]
    for outer, inner in shapes:
        (p.frame_xy if axis == "z" else p.frame_zy)(outer, inner, lo, hi, color)
    bars = [K.rect(a - 1.0 * s, a + 1.0 * s, y + 0.45 * s, y + 0.75 * s), K.rect(a - 0.2 * s, a + 0.2 * s, y - 1.8 * s, y + 0.6 * s)]
    for pts in bars:
        (p.prism_xy if axis == "z" else p.prism_zy)(pts, lo, hi, color)


# ══ ФАСАД: храмовый пилон ═════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, SHADOW, SHADOW, NIGHT)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FR, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, 0.0, SANDST3)  # цоколь
    slab(FR, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, 0.0, 1.0, SANDST2)
    slab(FS, axis, fixed, out, 1.95, -half - 1.95, half + 1.95, 1.0, 1.3, GOLD)
    # кладка песчаника рядами (смещение швов через ряд)
    for r in range(6):
        y0 = 1.3 + 2.0 * r
        off = 0.0 if r % 2 == 0 else 3.0
        a = -half - 0.88 - off
        k = 0
        while a < half + 0.88:
            a0, a1 = max(a, -half - 0.88), min(a + 6.0, half + 0.88)
            slab(FR, axis, fixed, out, 0.88, a0 + 0.06, a1 - 0.06, y0 + 0.06, min(y0 + 2.0, 13.3) - 0.06,
                 SANDST if (r + k) % 3 else SANDST2)
            a, k = a + 6.0, k + 1
    slab(FS, axis, fixed, out, 0.8, -half - 0.8, half + 0.8, 1.3, 13.3, SHADOW)
    # фриз «немес» и карниз-выкружка
    stripes(FS, axis, fixed, out, 1.3, -half - 1.3, half + 1.3, 13.3, 15.3, 1.0, (LAPIS, GOLD))
    slab(FS, axis, fixed, out, 1.4, -half - 1.4, half + 1.4, 15.3, 15.6, GOLD2)
    slab(FR, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, 15.6, 16.6, SANDST)
    stripes(FS, axis, fixed, out, 2.4, -half - 2.4, half + 2.4, 16.6, 17.8, 1.5, (TURQ, GOLD, LAPIS, GOLD))
    slab(FS, axis, fixed, out, 2.6, -half - 2.6, half + 2.6, 17.8, 19.0, SANDST3)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))

# перед: две скошенные башни пилона, врата, крылатый диск, обелиски
for s in (-1, 1):
    x0, x1 = s * 4.6, s * (FX + 0.6)
    pts = [(x0, 1.3), (x1, 1.3), (s * (FX - 0.6), 15.3), (s * 5.4, 15.3)]
    FS.prism_xy(pts, -FZ - 2.0, -FZ, SANDST)
    for k in range(5):  # швы башни
        y = 3.6 + 2.4 * k
        FS.box(s * 5.0, s * (FX - 0.2), y, y + 0.12, -FZ - 2.06, -FZ - 1.98, SANDST3)
    # картуш с анкхом и скарабеем
    cx = s * 11.2
    FS.frame_xy(K.octa(cx, 8.4, 2.4, 4.6, 1.0), K.octa(cx, 8.4, 2.0, 4.2, 0.85), -FZ - 2.3, -FZ - 2.0, GOLD)
    FS.prism_xy(K.octa(cx, 8.4, 2.0, 4.2, 0.85), -FZ - 2.1, -FZ - 2.0, LAPIS)
    ankh(FS, "z", -FZ, -1, cx, 9.6, 1.05, 2.1, 2.35, GOLD)
    FS.prism_xy(K.octa(cx, 5.6, 0.7, 0.9, 0.3), -FZ - 2.35, -FZ - 2.1, TURQ)  # скарабей
    for e in (-1, 1):
        FS.prism_xy([(cx + e * 0.6, 5.8), (cx + e * 1.6, 6.3), (cx + e * 1.5, 5.4)], -FZ - 2.3, -FZ - 2.1, TURQ)
    F.objects(True)
    # обелиск у угла
    ox = s * (FX + 1.6)
    FS.loft([(ox - 0.9, 0.0, -FZ - 2.5), (ox + 0.9, 0.0, -FZ - 2.5), (ox + 0.9, 0.0, -FZ - 0.7), (ox - 0.9, 0.0, -FZ - 0.7)],
            [(ox - 0.55, 15.6, -FZ - 2.15), (ox + 0.55, 15.6, -FZ - 2.15), (ox + 0.55, 15.6, -FZ - 1.05),
             (ox - 0.55, 15.6, -FZ - 1.05)], SANDST2)
    FS.cone([(ox - 0.55, 15.6, -FZ - 2.15), (ox + 0.55, 15.6, -FZ - 2.15), (ox + 0.55, 15.6, -FZ - 1.05),
             (ox - 0.55, 15.6, -FZ - 1.05)], (ox, 17.2, -FZ - 1.6), GOLD)
    F.objects(False)
# врата: глубокий проём, косяки, притолока, двери из золота с лазурными полосами
FS.box(-4.6, 4.6, 1.3, 12.6, -FZ - 1.0, -FZ, SHADOW)
for s in (-1, 1):
    FS.box(s * 3.4, s * 4.6, 1.3, 11.6, -FZ - 1.9, -FZ, SANDST2)
FS.box(-4.8, 4.8, 11.6, 12.8, -FZ - 2.0, -FZ, SANDST2)
stripes(FS, "z", -FZ, -1, 2.1, -4.6, 4.6, 12.0, 12.5, 0.92, (LAPIS, GOLD))
for s in (-1, 1):
    FS.box(s * 0.05, s * 3.3, 1.3, 11.5, -FZ - 1.3, -FZ - 1.0, GOLD2)
    for k in range(4):
        FS.box(s * 0.4, s * 3.0, 2.4 + 2.4 * k, 3.0 + 2.4 * k, -FZ - 1.4, -FZ - 1.3, LAPIS)
FG.box(-0.05, 0.05, 1.3, 11.5, -FZ - 1.2, -FZ - 1.1, "FFE7A0")  # свет из щели между створками
# крылатый солнечный диск над вратами
FS.prism_xy(K.octa(0, 14.3, 1.4, 1.4, 0.58), -FZ - 2.0, -FZ - 1.4, GOLD)
FG.prism_xy(K.octa(0, 14.3, 0.9, 0.9, 0.37), -FZ - 2.1, -FZ - 2.0, "FFB830")
for s in (-1, 1):
    for k, (color, dy) in enumerate(((GOLD, 0.0), (TURQ, -0.45), (LAPIS, -0.9))):
        FS.prism_xy([(s * 1.4, 14.9 + dy), (s * (5.2 - k * 0.6), 15.1 + dy), (s * (5.0 - k * 0.6), 14.5 + dy),
                     (s * 1.4, 14.4 + dy)], -FZ - 1.9 + 0.05 * k, -FZ - 1.4, color)
    FS.box(s * 1.2, s * 2.2, 12.8, 14.0, -FZ - 1.8, -FZ - 1.4, "D8402A")  # уреи у диска
# бока: колоннады с капителями-папирусами
for s in (-1, 1):
    fx = s * FX
    for k in range(5):
        z = -12.0 + 6.0 * k
        column(FS, fx + s * 1.3, z, 1.3, 13.3, 0.75, (TURQ, "6AAE4A")[k % 2])
    for k in range(4):
        z = -9.0 + 6.0 * k
        ankh(FS, "x", fx, s, z, 6.8, 0.9, 0.88, 1.05, GOLD)
# тыл: ложные двери и ступени
for s in (-1, 1):
    x = s * 8.0
    for k in range(3):
        w = 2.8 - 0.6 * k
        slab(FS, "z", FZ, 1, 0.5 + 0.3 * k, x - w, x + w, 1.3, 11.8 - 1.0 * k, (SANDST2, SANDST3, SHADOW)[k])
for k in range(4):
    FS.box(-3.6 + 0.4 * k, 3.6 - 0.4 * k, 0.0, 0.35 * (k + 1), FZ, FZ + 2.4 - 0.5 * k, SANDST2)

# ══ ИНТЕРЬЕР: сокровищница гробницы ═══════════════════════════════════════════════════════════════════════════
PED = (0.0, -4.0)
TOP = 1.6
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), SANDST2)
for z in (-12.0, -8.0, 0.0, 4.0, 8.0):  # лазурные полосы-инкрустации пола
    IS.box(-W, W, 0.02, 0.05, z - 0.12, z + 0.12, LAPIS)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.8), (DOOR[0] + 0.8, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 2.0, LAPIS2)
        slab(IS, axis, fixed, out, 1.0, a0, a1, 2.0, 2.3, GOLD)
    for a0, a1 in spans:
        for r in range(4):
            y0 = 2.3 + 2.0 * r
            slab(IR, axis, fixed, out, 0.88, a0, a1, y0, y0 + 2.0 + (0.4 if r == 3 else 0.0), SANDST if r % 2 else SANDST2)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.2, 13.0, SANDST)
    # пояса росписи: золото — бирюза — охра, ряд звёзд-лотосов
    stripes(IS, axis, fixed, out, 1.0, -half, half, 10.7, 11.1, 1.0, (GOLD, TURQ, GOLD, OCHRE))
    slab(IS, axis, fixed, out, 1.05, -half, half, 11.1, 11.4, LAPIS)
    stripes(IS, axis, fixed, out, 1.0, -half, half, 11.4, 13.0, 2.0, (SANDST3, SANDST2))
    for k in range(int(2 * half // 4)):
        a = -half + 2.0 + 4.0 * k
        (IS.prism_xy if axis == "z" else IS.prism_zy)(K.octa(a, 12.2, 0.55, 0.55, 0.22), fixed + out * 1.0,
                                                     fixed + out * 1.1, GOLD)
    slab(IS, axis, fixed, out, 1.2, -half, half, 13.0, 13.4, GOLD2)
    slab(IR, axis, fixed, out, 0.88, -half, half, 13.4, C, NIGHT)
    # картуши на стенах (кроме стены лифта)
    if not gap:
        for a in (-half * 0.55, half * 0.55):
            (IS.frame_xy if axis == "z" else IS.frame_zy)(K.octa(a, 6.3, 1.3, 2.8, 0.55), K.octa(a, 6.3, 1.0, 2.5, 0.42),
                                                          fixed + out * 0.88, fixed + out * 1.1, GOLD)
            (IS.prism_xy if axis == "z" else IS.prism_zy)(K.octa(a, 6.3, 1.0, 2.5, 0.42), fixed + out * 0.88,
                                                          fixed + out * 0.95, LAPIS)
            ankh(IS, axis, fixed, out, a, 6.6, 0.6, 0.95, 1.1, GOLD)
# потолок: золотые звёзды
for k in range(40):
    x, z = (rng(k, 81) - 0.5) * 31, (rng(k, 82) - 0.5) * 29
    IG.prism_xz([(x, z - 0.35), (x + 0.12, z - 0.12), (x + 0.35, z), (x + 0.12, z + 0.12), (x, z + 0.35),
                 (x - 0.12, z + 0.12), (x - 0.35, z), (x - 0.12, z - 0.12)], C - 0.06, C - 0.02, STAR)
F.objects(True)
# постамент: ступени из чёрного камня с золотой кромкой
px, pz = PED
for k, (hw, y0, y1) in enumerate(((4.6, 0.0, 0.55), (3.8, 0.55, 1.1), (3.0, 1.1, TOP))):
    IR.prism_xz(K.octa(px, pz, hw, hw, hw * 0.3), y0, y1, BASALT if k != 1 else BASALT2)
    IS.frame_xz(K.octa(px, pz, hw + 0.06, hw + 0.06, hw * 0.3), K.octa(px, pz, hw - 0.12, hw - 0.12, hw * 0.29),
                y1 - 0.12, y1 + 0.02, GOLD)
F.objects(False)
# колонны-папирусы вокруг
for x, z in ((-7.0, -10.5), (7.0, -10.5), (-9.5, 1.5), (9.5, 1.5)):
    column(IS, x, z, 0.0, 13.4, 0.85, TURQ if z < 0 else "6AAE4A")
# луч света на маску (тонкий конус-призма)
IG.frame_xz(K.octa(px, pz, 2.2, 2.2, 0.9), K.octa(px, pz, 1.8, 1.8, 0.75), C - 0.08, C - 0.02, "FFE7A0")  # световой круг
F.objects(True)
# сокровища: сундуки, горы монет, канопы, жаровни
for x, z, yaw in ((-11.5, -11.0, 0), (11.0, -12.0, 1), (-12.5, 1.0, 1)):
    w, d = (1.6, 1.0) if yaw == 0 else (1.0, 1.6)
    IS.box(x - w, x + w, 0.0, 1.5, z - d, z + d, WOOD)
    IS.box(x - w - 0.05, x + w + 0.05, 1.5, 2.1, z - d - 0.05, z + d + 0.05, GOLD2)
    IS.box(x - w - 0.08, x + w + 0.08, 0.7, 0.9, z - d - 0.08, z + d + 0.08, GOLD)
    IS.box(x - 0.25, x + 0.25, 1.1, 1.6, z - d - 0.12 if yaw == 0 else z - 0.25, z - d if yaw == 0 else z + 0.25, LAPIS)
for x, z, r in ((-10.0, -7.5, 1.6), (12.0, -7.0, 1.9), (11.5, 3.0, 1.3), (-11.0, 5.0, 1.2)):
    for k in range(4):
        rr = r * (1.0 - 0.22 * k)
        IS.prism_xz(K.octa(x, z, rr, rr, rr * 0.4), 0.3 * k, 0.3 * (k + 1), GOLD if k % 2 == 0 else GOLD2)
    for k in range(5):
        a = 2 * math.pi * k / 5
        cx, cz = x + (r + 0.4) * math.cos(a), z + (r + 0.4) * math.sin(a)
        IS.prism_xz(K.octa(cx, cz, 0.35, 0.35, 0.14), 0.0, 0.12, GOLD)
for k in range(4):  # канопы у постамента
    x = -4.5 + 3.0 * k
    z = pz - 5.4
    IS.prism_xz(K.octa(x, z, 0.45, 0.45, 0.18), 0.0, 1.0, CREAM)
    IS.prism_xz(K.octa(x, z, 0.38, 0.38, 0.15), 1.0, 1.5, (GOLD, TURQ, LAPIS, OCHRE)[k])
for x, z in ((-4.8, 2.2), (4.8, 2.2)):  # жаровни
    IS.prism_xz(K.octa(x, z, 0.3, 0.3, 0.12), 0.0, 2.6, GOLD2)
    IS.prism_xz(K.octa(x, z, 0.8, 0.8, 0.33), 2.6, 3.2, GOLD)
    IG.prism_xz(K.octa(x, z, 0.55, 0.55, 0.22), 3.2, 3.8, FLAME2)
    IG.prism_xz(K.octa(x, z, 0.3, 0.3, 0.12), 3.8, 4.5, FLAME)
for s in (-1, 1):  # золотые анкхи у лифта
    ankh(IS, "z", ZB, -1, s * 6.0, 5.4, 1.4, 0.88, 1.2, GOLD)
F.objects(False)
B.lift_leaves(IS, GOLD2, LAPIS)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, SANDST)
SL.box(-FX - 2.9, FX + 2.9, -1, 1.3, -FZ - 2.9, FZ + 2.9, SANDST2)
SL.box(-FX - 1.3, FX + 1.3, 13.3, 15.3, -FZ - 1.3, FZ + 1.3, LAPIS)
SL.box(-FX - 2.4, FX + 2.4, 16.6, 17.8, -FZ - 2.4, FZ + 2.4, GOLD)
SL.box(-FX - 2.6, FX + 2.6, 17.8, 19.0, -FZ - 2.6, FZ + 2.6, SANDST3)
SL.box(-4.6, 4.6, 1.3, 12.6, -FZ - 1.0, -FZ, GOLD2)
SL.box(-5.0, 5.0, 13.6, 15.2, -FZ - 1.9, -FZ, GOLD)
for s in (-1, 1):
    SL.box(s * 4.6, s * (FX + 0.6), 1.3, 13.3, -FZ - 2.0, -FZ, SANDST)
    SL.box(s * (FX + 0.7), s * (FX + 2.5), 0.0, 15.6, -FZ - 2.5, -FZ - 0.7, SANDST2)
    SL.box(s * (FX + 0.5), s * (FX + 2.1), 1.3, 13.3, -13.0, 13.0, TURQ)

F.build(exhibit=(PED[0], TOP, PED[1], 3.4), lamps=[("Hall", (0, 14, 6), 3000, (1.0, 0.9, 0.7)),
                                                   ("Spot", (0, 13, -4), 3200, (1.0, 0.95, 0.8))])
