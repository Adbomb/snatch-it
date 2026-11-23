"""Этаж «Подсолнухи» музея-небоскрёба (четвёртая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — провансальский дом художника посреди подсолнухового поля. Снаружи — тёплые жёлтые оштукатуренные
стены с каменными углами-рустом, синие ставни на окнах и голубая дверь, терракотовая черепичная крыша со скатом и карнизом,
горшки с лавандой у порога, сверху — ветряная мельница-флюгер с крыльями; перед домом — густое поле огромных
подсолнухов разной высоты (круглые жёлто-оранжевые головы с тёмной серединкой), деревянный забор и мольберт с
холстом; бока — оливковые деревья и ряды лаванды; сзади — колодец и тележка с сеном. Внутри — светлая мастерская
художника: деревянные балки потолка, белёные стены с синими рамами окон на летнее поле, мольберты с чистыми
холстами, банки с кистями, палитры, вазы с подсолнухами на столах, плетёные стулья, рулоны холста; экспонат —
на мольберте-подиуме из тёплого дерева в центре, под светом мансардного окна.
Запуск: blender --background --factory-startup --python scripts/blender/floor_sunflowers.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, ring_y, rng, slab, taper, tube  # noqa: E402

YELLOW, YELLOW2, YELLOW3, STONE, STONE2 = "F2C85A", "E0AE40", "F8DC8A", "D8C8A8", "BFAE8A"
SHUTTER, SHUTTER2, TERRA, TERRA2, WOOD, WOOD2 = "3A7AC8", "2A5AA0", "C8663A", "A84E2A", "A87A4A", "7A5430"
PETAL, PETAL2, SEED, STEM, LEAF, LEAF2 = "FFD020", "FFAA18", "5A3A1E", "4A8A2E", "5AA83A", "3E8A2A"
LAV, LAV2, OLIVE, OLIVE2, BARK, WHITE = "9A7AD8", "7A5AC0", "8AA05A", "6A8A4A", "6A5A4A", "F8F4EC"
WALLIN, WALLIN2, FLOOR, FLOOR2, SKY, SKY2 = "FBF4E4", "EEE4CC", "D8A870", "C48E58", "9ED4F4", "C8E8FA"
CANVAS, PAINT = "F8F2E4", ("E83A3A", "3A8AE8", "F2C230", "4AB84A", "E87A2A", "9A5AD8")

F = B.Floor("SF", "Sunflowers", quiet=(YELLOW2, FLOOR2, SKY, SKY2, LAV2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def sunflower(p, x, z, h, r, face=(0.0, -1.0), seed=0):
    """Подсолнух: стебель, два листа, голова — тёмная серединка в кольце лепестков (8-угольники), обращена к face."""
    fx, fz = face
    p.box(x - 0.12, x + 0.12, 0.0, h, z - 0.12, z + 0.12, STEM)
    for e in (-1, 1):
        lx = x + e * 0.9
        taper(p, (x, h * (0.45 + 0.1 * e), z), (lx, h * (0.5 + 0.1 * e) + 0.3, z + 0.2 * e), 0.6, 0.1, (LEAF, LEAF2)[e > 0])
    cx, cy, cz = x + fx * 0.3, h + r * 0.2, z + fz * 0.3
    if abs(fz) >= abs(fx):
        p.prism_xy(K.ngon(cx, cy, r, 10), *sorted((cz, cz + fz * 0.3)), (PETAL, PETAL2)[seed % 2])
        p.prism_xy(K.ngon(cx, cy, r * 0.5, 8), *sorted((cz + fz * 0.3, cz + fz * 0.45)), SEED)
    else:
        p.prism_zy(K.ngon(cz, cy, r, 10), *sorted((cx, cx + fx * 0.3)), (PETAL, PETAL2)[seed % 2])
        p.prism_zy(K.ngon(cz, cy, r * 0.5, 8), *sorted((cx + fx * 0.3, cx + fx * 0.45)), SEED)


def semi(cx, cy, r, n=8):
    """Полукруг над (cx, cy): точки справа налево."""
    return [(cx + r * math.cos(math.pi * k / n), cy + r * math.sin(math.pi * k / n)) for k in range(n + 1)]


def lavender(p, x, z, n=5):
    """Куст лаванды: веер фиолетовых колосков."""
    for k in range(n):
        t = 2 * math.pi * k / n
        taper(p, (x, 0.0, z), (x + 0.5 * math.cos(t), 1.4 + 0.3 * rng(x, k), z + 0.5 * math.sin(t)), 0.3, 0.1, (LAV, LAV2)[k % 2])


def olive(p, x, z, h, s=1.0):
    """Оливковое дерево: кривой ствол и серебристо-зелёная крона из комков."""
    tube(p, [(x, 0.0, z), (x + 0.6 * s, h * 0.5, z), (x + 0.2 * s, h * 0.75, z + 0.3 * s)], [0.9 * s, 0.7 * s, 0.6 * s], 0.7 * s,
         (0, 0, 1), BARK)
    for k in range(4):
        t = 2 * math.pi * k / 4 + 0.4
        cx, cz = x + 1.4 * s * math.cos(t), z + 1.2 * s * math.sin(t)
        r = (1.3 + 0.3 * rng(k, x)) * s
        p.prism_xz(K.ngon(cx, cz, r, 8), h * 0.8, h * 0.8 + r * 1.1, (OLIVE, OLIVE2)[k % 2])


def easel(p, x, z, h=6.0, face=-1, canvas_col=CANVAS, paint_seed=None):
    """Мольберт-тренога с холстом; на холсте — несколько мазков-пятен (абстрактно, без лиц и фигур)."""
    for e in (-1, 1):
        beam(p, (x + e * 1.0, 0.0, z + 0.3 * face), (x + e * 0.2, h, z), 0.18, 0.18, WOOD)
    beam(p, (x, 0.0, z - 1.2 * face), (x, h * 0.92, z - 0.05 * face), 0.16, 0.16, WOOD2)
    p.box(x - 1.3, x + 1.3, h * 0.38, h * 0.42, *sorted((z + 0.1 * face, z + 0.5 * face)), WOOD2)
    p.box(x - 1.2, x + 1.2, h * 0.42, h * 0.42 + 2.6, *sorted((z + 0.2 * face, z + 0.35 * face)), canvas_col)
    if paint_seed is not None:
        for k in range(4):
            px_ = x - 0.8 + 1.6 * rng(paint_seed, k)
            py = h * 0.42 + 0.4 + 1.8 * rng(k, paint_seed)
            p.box(px_ - 0.3, px_ + 0.3, py - 0.2, py + 0.2, *sorted((z + 0.35 * face, z + 0.4 * face)), PAINT[(k + paint_seed) % 6])


def vase_flowers(p, x, z, y, s=1.0):
    """Ваза с тремя подсолнухами."""
    p.prism_xz(K.ngon(x, z, 0.35 * s, 8), y, y + 0.9 * s, SHUTTER)
    p.prism_xz(K.ngon(x, z, 0.45 * s, 8), y + 0.3 * s, y + 0.7 * s, SHUTTER)
    for k in range(3):
        t = 2 * math.pi * k / 3
        tx, tz = x + 0.5 * s * math.cos(t), z + 0.5 * s * math.sin(t)
        beam(p, (x, y + 0.9 * s, z), (tx, y + 2.0 * s, tz), 0.08, 0.08, STEM)
        p.prism_xz(K.ngon(tx, tz, 0.45 * s, 10), y + 2.0 * s, y + 2.15 * s, PETAL)
        p.prism_xz(K.ngon(tx, tz, 0.22 * s, 8), y + 2.15 * s, y + 2.22 * s, SEED)


def window_shutters(p, g, axis, fixed, out, a, y0, y1, w, glow_col):
    """Окно с синими ставнями и каменным подоконником."""
    lo, hi = sorted((fixed + out * 0.88, fixed + out * 1.0))
    (g.prism_xy if axis == "z" else g.prism_zy)([(a - w, y0), (a + w, y0), (a + w, y1), (a - w, y1)], *sorted((fixed + out * 0.9,
                                                fixed + out * 0.94)), glow_col)
    for e in (-1, 1):
        s0, s1 = sorted((a + e * w, a + e * (w + w * 0.95)))
        slab(p, axis, fixed, out, 1.2, s0, s1, y0, y1, SHUTTER)
        for m in range(4):
            yy = y0 + (y1 - y0) * (m + 0.5) / 4
            slab(p, axis, fixed, out, 1.3, s0 + 0.1, s1 - 0.1, yy - 0.08, yy + 0.08, SHUTTER2)
    slab(p, axis, fixed, out, 1.5, a - w - 0.3, a + w + 0.3, y0 - 0.4, y0, STONE)
    slab(p, axis, fixed, out, 1.2, a - w - 0.2, a + w + 0.2, y1, y1 + 0.4, STONE)


# ══ ФАСАД: дом художника в поле подсолнухов ═══════════════════════════════════════════════════════════════════
B.shell_planes(F, YELLOW, YELLOW, WOOD2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.2, LEAF2)
    slab(FR, axis, fixed, out, 1.88, -half - 0.4, half + 0.4, -0.2, 1.4, STONE2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.4, 14.6, YELLOW)
    for e in (-1, 1):  # каменный руст на углах
        for k in range(6):
            y = 1.4 + 2.2 * k
            w = 2.4 if k % 2 else 1.6
            a0, a1 = sorted((e * half, e * (half - w)))
            slab(FR, axis, fixed, out, 1.08, a0, a1, y + 0.1, y + 2.1, STONE)
    if fi != 0:  # окна со ставнями
        for a in (-9.0, 0.0, 9.0) if axis == "z" else (-8.0, 8.0):
            window_shutters(FS, FG, axis, fixed, out, a, 5.0, 10.6, 1.8, SKY)
    # черепичный карниз: два ряда черепицы, кронштейны
    for k, (d, y0, y1) in enumerate(((3.2, 14.6, 15.4), (2.2, 15.4, 16.2))):
        slab(FR, axis, fixed, out, d + 0.88, -half - d, half + d, y0, y1, (TERRA, TERRA2)[k])
    for k in range(int(2 * half // 1.6)):
        a = -half + 0.8 + 1.6 * k
        slab(FS, axis, fixed, out, 4.2, a - 0.3, a + 0.3, 14.6, 15.5, TERRA2)
    # черепичный скат над карнизом: скат и рёбра черепицы через шаг
    B.chamfer(FR, axis, fixed, out, -half - 2.2, half + 2.2, [(0.0, 16.2), (2.2, 16.2), (2.2, 16.5), (0.0, 18.9)], TERRA)
    for k in range(int(2 * half // 2.4) + 2):
        a = -half - 1.4 + 2.4 * k
        B.chamfer(FS, axis, fixed, out, a - 0.3, a + 0.3, [(0.0, 16.4), (2.35, 16.4), (2.35, 16.7), (0.15, 18.9)], TERRA2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# перед: голубая дверь с полукруглым окошком, окна со ставнями, лаванда в горшках
FS.box(-2.4, 2.4, 1.4, 9.0, -FZ - 1.1, -FZ - 0.88, SHUTTER)
for m in range(4):
    FS.box(-2.0, 2.0, 2.0 + 1.6 * m, 2.1 + 1.6 * m, -FZ - 1.2, -FZ - 1.1, SHUTTER2)
FG.prism_xy(semi(0.0, 9.0, 2.4), -FZ - 0.94, -FZ - 0.9, SKY)
FS.frame_xy(semi(0.0, 9.0, 3.0), semi(0.0, 9.0, 2.4), -FZ - 1.2, -FZ - 0.88, STONE)
for a in (-10.0, 10.0):
    window_shutters(FS, FG, "z", -FZ, -1, a, 6.0, 11.6, 2.0, SKY)
for x in (-4.0, 4.0):
    FS.prism_xz(K.ngon(x, -FZ - 1.6, 0.7, 8), -0.2, 0.9, TERRA)
for x in (-4.0, 4.0):
    for k in range(5):
        t = 2 * math.pi * k / 5
        taper(FS, (x, 0.9, -FZ - 1.6), (x + 0.4 * math.cos(t), 2.3, -FZ - 1.6 + 0.4 * math.sin(t)), 0.25, 0.08, (LAV, LAV2)[k % 2])
# поле подсолнухов перед домом (по бокам от двери, разной высоты), забор, мольберт
for k in range(16):
    side = -1 if k % 2 else 1
    x = side * (5.6 + 11.0 * rng(k, 1))
    z = -FZ - 1.8 - 3.2 * rng(k, 2)
    if abs(x) > FX + 1.5:
        continue
    h = 4.0 + 6.0 * rng(k, 3)
    sunflower(FS, x, z, h, 1.0 + 0.5 * rng(k, 4), (0.0, -1.0), k)
for k in range(12):
    x = -FX - 1.0 + (2 * FX + 2.0) * k / 11
    if abs(x) < 3.0:
        continue
    FS.box(x - 0.15, x + 0.15, -0.2, 2.6, -FZ - 5.6, -FZ - 5.3, WOOD)
for y in (0.8, 1.9):
    for s in (-1, 1):
        FS.box(*sorted((s * 3.0, s * (FX + 1.2))), y, y + 0.25, -FZ - 5.55, -FZ - 5.35, WOOD2)
easel(FS, 7.0, -FZ - 6.2, 5.0, -1, CANVAS, 3)
# ветряная мельница-флюгер на крыше
mx, my, mz = -11.0, 17.25, -FZ - 2.75
FS.prism_xz(K.ngon(mx, mz + 0.3, 0.25, 6), 15.4, my, WOOD2)
for k in range(4):
    t = math.pi / 4 + math.pi / 2 * k
    FS.prism_xy([(mx, my), (mx + 1.6 * math.cos(t - 0.18), my + 1.6 * math.sin(t - 0.18)), (mx + 1.7 * math.cos(t + 0.18),
                 my + 1.7 * math.sin(t + 0.18))], mz - 0.1, mz, WHITE)
FS.prism_xy(K.ngon(mx, my, 0.3, 8), mz - 0.25, mz - 0.1, TERRA)
# бока: оливы и лаванда
for s in (-1, 1):
    olive(FS, s * (FX + 2.4), -6.0, 8.0, 1.1)
    for k in range(4):
        z = 4.0 + 3.0 * k
        for kk in range(5):
            t = 2 * math.pi * kk / 5
            taper(FS, (s * (FX + 1.8), -0.2, z), (s * (FX + 1.8) + 0.4 * math.cos(t), 1.4, z + 0.4 * math.sin(t)), 0.3, 0.1,
                  (LAV, LAV2)[kk % 2])
# сзади: колодец и тележка с сеном
FS.prism_xz(K.ngon(-5.0, FZ + 2.4, 1.4, 10), -0.2, 1.6, STONE)
FS.cone([(-5.0 + 1.6 * math.cos(t), 4.0, FZ + 2.4 + 1.6 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]],
        (-5.0, 5.4, FZ + 2.4), TERRA)
for e in (-1, 1):
    FS.box(-5.0 + e * 1.2 - 0.12, -5.0 + e * 1.2 + 0.12, 1.6, 4.0, FZ + 2.28, FZ + 2.52, WOOD2)
FS.box(2.0, 7.0, 1.0, 2.4, FZ + 1.2, FZ + 3.8, WOOD)
FS.box(2.2, 6.8, 2.4, 4.4, FZ + 1.4, FZ + 3.6, "E8C870")
for x in (2.8, 6.2):
    FS.prism_zy(K.ngon(FZ + 2.5, 1.0, 1.0, 10), x - 0.15, x + 0.15, WOOD2)

# ══ ИНТЕРЬЕР: мастерская художника ════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.0
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), FLOOR2)
for k in range(-8, 8):  # широкие доски пола
    if k % 2:
        IR.box(2.1 * k, 2.1 * k + 2.1, 0.0, 0.08, ZF, ZB, FLOOR)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.2, WOOD2)
        slab(IR, axis, fixed, out, 0.88, a0, a1, 1.2, C if not gap else DOOR[1] + 0.1, WALLIN)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, WALLIN)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, SHUTTER)
    else:  # окна на летнее поле: небо, полоса подсолнухов
        for a in ((-9.0, 9.0) if axis == "z" else (-9.0, 0.0, 9.0)):
            if axis == "z" and abs(a) < 1.0:
                continue
            lo, hi = sorted((fixed + out * 0.9, fixed + out * 0.94))
            gp = IG.prism_xy if axis == "z" else IG.prism_zy
            gp([(a - 2.6, 4.0), (a + 2.6, 4.0), (a + 2.6, 12.0), (a - 2.6, 12.0)], lo, hi, SKY2)
            gp([(a - 2.6, 4.0), (a + 2.6, 4.0), (a + 2.6, 6.0), (a - 2.6, 6.0)], *sorted((fixed + out * 0.94, fixed + out * 0.98)), PETAL)
            gp([(a - 2.6, 4.0), (a + 2.6, 4.0), (a + 2.6, 4.8), (a - 2.6, 4.8)], *sorted((fixed + out * 0.98, fixed + out * 1.02)), LEAF2)
            fr = IS.frame_xy if axis == "z" else IS.frame_zy
            fr([(a - 3.0, 3.6), (a + 3.0, 3.6), (a + 3.0, 12.4), (a - 3.0, 12.4)], [(a - 2.6, 4.0), (a + 2.6, 4.0), (a + 2.6, 12.0),
                                                                                    (a - 2.6, 12.0)], *sorted((fixed + out * 0.88,
                                                                                                              fixed + out * 1.4)), SHUTTER)
            slab(IS, axis, fixed, out, 1.2, a - 0.12, a + 0.12, 4.0, 12.0, SHUTTER)
            slab(IS, axis, fixed, out, 1.2, a - 2.6, a + 2.6, 7.9, 8.1, SHUTTER)
# деревянные балки потолка и мансардное окно над экспонатом
for k in range(-3, 4):
    IS.box(-W, W, C - 1.2, C - 0.2, 4.2 * k - 0.4, 4.2 * k + 0.4, WOOD)
IG.box(-3.0, 3.0, C - 0.12, C - 0.04, -5.6, -0.4, "FFF8E0")
# мольберты с холстами, банки с кистями, палитры, столы с вазами подсолнухов, стулья, рулоны холста
for x, z, seed in ((-10.0, -9.0, 1), (10.0, -9.5, 2), (-11.0, 1.0, 3)):
    easel(IS, x, z, 6.0, 1, CANVAS, seed)
for x, z in ((-6.0, -12.6), (6.0, -12.6)):
    IS.box(x - 2.2, x + 2.2, 2.6, 2.9, z - 1.0, z + 1.0, WOOD)
    for e in (-1, 1):
        for f in (-1, 1):
            IS.box(x + e * 1.9 - 0.15, x + e * 1.9 + 0.15, 0.0, 2.6, z + f * 0.7 - 0.15, z + f * 0.7 + 0.15, WOOD2)
    vase_flowers(IS, x, z, 2.9, 1.2)
    for k in range(3):
        IS.prism_xz(K.ngon(x + 1.2 + 0.5 * k - 0.5, z + 0.4, 0.2, 6), 2.9, 3.6, PAINT[k])
for x, z in ((11.5, 1.0), (12.5, 4.0)):  # плетёные стулья
    IS.box(x - 0.9, x + 0.9, 1.6, 1.9, z - 0.9, z + 0.9, "D8B070")
    IS.box(x - 0.9, x + 0.9, 1.9, 3.8, z + 0.7, z + 0.9, "D8B070")
    for e in (-1, 1):
        for f in (-1, 1):
            IS.box(x + e * 0.75 - 0.1, x + e * 0.75 + 0.1, 0.0, 1.6, z + f * 0.75 - 0.1, z + f * 0.75 + 0.1, WOOD2)
for k, z in enumerate((9.0, 10.4, 11.8)):  # рулоны холста у лифта
    IS.prism_xz(K.ngon(-12.0 + 1.1 * k, z, 0.45, 8), 0.0, 5.0 - 0.6 * k, CANVAS)
for k, (x, z) in enumerate(((-13.6, 12.0), (13.6, 12.0), (13.6, -4.0))):  # горшки подсолнухов у стен
    IS.prism_xz(K.ngon(x, z, 0.9, 8), 0.0, 1.2, TERRA)
    sunflower(IS, x, z, 4.0 + k, 0.9, (-1.0 if x > 0 else 1.0, 0.0), k)
# мольберт-подиум для картины: тёплое дерево, ступень, опоры
px, pz = PED
IR.box(px - 4.0, px + 4.0, 0.0, 0.5, pz - 3.0, pz + 3.0, WOOD2)
IR.box(px - 3.4, px + 3.4, 0.5, TOP, pz - 2.4, pz + 2.4, WOOD)
for e in (-1, 1):  # опоры мольберта — позади картины, не перекрывают её
    beam(IS, (px + e * 2.6, TOP, pz - 2.2), (px + e * 1.6, 10.6, pz - 1.5), 0.3, 0.3, WOOD2)
beam(IS, (px, TOP, pz - 2.4), (px, 10.8, pz - 1.6), 0.3, 0.3, WOOD2)
for e in (-1, 1):
    for f in (-1, 1):
        IS.prism_xz(K.ngon(px + e * 3.6, pz + f * 2.6, 0.25, 6), 0.0, 0.6, PETAL2)
B.lift_leaves(IS, SHUTTER2, PETAL)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, YELLOW)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.2, -FZ - 2.9, FZ + 2.9, LEAF2)
SL.box(-FX - 3.2, FX + 3.2, 14.6, 16.2, -FZ - 3.2, FZ + 3.2, TERRA)
for k in range(6):
    x = -15.0 + 6.0 * k
    if abs(x) < 4.0:
        continue
    SL.prism_xy(K.ngon(x, 7.0 + 2.0 * (k % 2), 1.4, 6), -FZ - 3.4, -FZ - 3.1, PETAL)

F.build(tol=0.12, exhibit=(PED[0], TOP, PED[1], 2.0), lamps=[("Hall", (0, 14, 6), 3200, (1.0, 0.96, 0.88)),
                                                   ("Spot", (0, 13, -3), 3200, (1.0, 0.97, 0.9)),
                                                   ("Sun", (0, 10, -12), 900, (1.0, 0.9, 0.6))])
