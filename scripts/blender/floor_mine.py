"""Этаж «Живой сундук-мимик» музея-небоскрёба (четвёртая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — заброшенная шахта кладоискателей в скале. Снаружи — скальный утёс слоями серого и бурого камня с
жилами светящихся самоцветов, посередине — вход в штольню: деревянная крепь из толстых брёвен, тёмный проход,
над ним — табличка-доска на цепях и висящий фонарь; из штольни по рельсам выкатывается вагонетка с горой
золота; у входа — бочки, ящики, кирка и лопата, деревянный подъёмник-ворот с верёвкой; по скале — деревянные
мостки и лестница; бока — пещеры с кристаллами; сзади — водяное колесо. Внутри — главная выработка: неровные
скальные стены с кристаллическими жилами, крепь-арки из брёвен вдоль зала, рельсы с вагонетками золота, горы
монет и самоцветов, сундуки, фонари на крюках, сталактиты; экспонат — на каменном уступе в кольце из рельсов
под светом фонарей.
Запуск: blender --background --factory-startup --python scripts/blender/floor_mine.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, ring_y, rng, slab, taper  # noqa: E402

ROCK, ROCK2, ROCK3, ROCKB, ROCKB2, DARK = "8A8478", "6E6A62", "A8A294", "8A6A4A", "6E523A", "1E1A18"
LOG, LOG2, PLANK, PLANK2, IRON, IRON2 = "8A5A30", "6A4224", "B8844A", "9A6A38", "4A4A52", "6A6A74"
GOLD, GOLD2, GEM1, GEM2, GEM3, GEM4 = "F2C230", "D9A21A", "4AE0FF", "FF4ADA", "7AFF6A", "9A6AFF"
LAMP, WATER, MOSS = "FFC860", "3AA8D8", "5A8A3A"

F = B.Floor("MC", "MimicChest", quiet=(ROCK, ROCK2, ROCKB2, MOSS), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def crystal(p, g, x, y, z, h, color, lean=(0.0, 0.0), glow=True):
    """Кристалл: шестигранная призма и острая верхушка; верхушка светится."""
    r = h * 0.18
    top = (x + lean[0], y + h * 0.7, z + lean[1])
    p.loft([(x + r * math.cos(t), y, z + r * math.sin(t)) for t in [2 * math.pi * k / 6 for k in range(6)]],
           [(top[0] + r * math.cos(t), top[1], top[2] + r * math.sin(t)) for t in [2 * math.pi * k / 6 for k in range(6)]], color)
    (g if glow else p).cone([(top[0] + r * math.cos(t), top[1], top[2] + r * math.sin(t)) for t in [2 * math.pi * k / 6 for k in range(6)]],
                            (top[0] + lean[0] * 0.3, y + h, top[2] + lean[1] * 0.3), color)


def cluster(p, g, x, y, z, s, colors, seed):
    """Друза из 3–4 кристаллов."""
    for k in range(4):
        t = 2 * math.pi * (k + rng(seed, k)) / 4
        crystal(p, g, x + 0.4 * s * math.cos(t), y, z + 0.4 * s * math.sin(t), s * (1.0 + 0.6 * rng(k, seed)),
                colors[k % len(colors)], (0.5 * s * math.cos(t), 0.5 * s * math.sin(t)))


def cart(p, x, z, y=0.0, along_x=True, gold=True):
    """Вагонетка: колёса, кузов-трапеция, гора золота."""
    if along_x:
        p.loft([(x - 1.4, y + 0.6, z - 0.8), (x + 1.4, y + 0.6, z - 0.8), (x + 1.4, y + 0.6, z + 0.8), (x - 1.4, y + 0.6, z + 0.8)],
               [(x - 1.7, y + 2.0, z - 1.0), (x + 1.7, y + 2.0, z - 1.0), (x + 1.7, y + 2.0, z + 1.0), (x - 1.7, y + 2.0, z + 1.0)], IRON)
        for e in (-1, 1):
            for f in (-1, 1):
                p.prism_zy(K.ngon(z + f * 0.85, y + 0.45, 0.42, 8), x + e * 0.9 - 0.15, x + e * 0.9 + 0.15, IRON2) if False else \
                    p.prism_xy(K.ngon(x + e * 0.9, y + 0.45, 0.42, 8), z + f * 0.85 - 0.12, z + f * 0.85 + 0.12, IRON2)
        if gold:
            p.loft([(x - 1.6, y + 2.0, z - 0.9), (x + 1.6, y + 2.0, z - 0.9), (x + 1.6, y + 2.0, z + 0.9), (x - 1.6, y + 2.0, z + 0.9)],
                   [(x - 0.6, y + 2.9, z - 0.3), (x + 0.6, y + 2.9, z - 0.3), (x + 0.6, y + 2.9, z + 0.3), (x - 0.6, y + 2.9, z + 0.3)], GOLD)
    else:
        p.loft([(x - 0.8, y + 0.6, z - 1.4), (x + 0.8, y + 0.6, z - 1.4), (x + 0.8, y + 0.6, z + 1.4), (x - 0.8, y + 0.6, z + 1.4)],
               [(x - 1.0, y + 2.0, z - 1.7), (x + 1.0, y + 2.0, z - 1.7), (x + 1.0, y + 2.0, z + 1.7), (x - 1.0, y + 2.0, z + 1.7)], IRON)
        for e in (-1, 1):
            for f in (-1, 1):
                p.prism_zy(K.ngon(z + e * 0.9, y + 0.45, 0.42, 8), x + f * 0.85 - 0.12, x + f * 0.85 + 0.12, IRON2)
        if gold:
            p.loft([(x - 0.9, y + 2.0, z - 1.6), (x + 0.9, y + 2.0, z - 1.6), (x + 0.9, y + 2.0, z + 1.6), (x - 0.9, y + 2.0, z + 1.6)],
                   [(x - 0.3, y + 2.9, z - 0.6), (x + 0.3, y + 2.9, z - 0.6), (x + 0.3, y + 2.9, z + 0.6), (x - 0.3, y + 2.9, z + 0.6)], GOLD)


def rails(p, x0, x1, z0, z1, y=0.0):
    """Рельсы: две полосы и шпалы."""
    along_x = abs(x1 - x0) > abs(z1 - z0)
    if along_x:
        for e in (-0.7, 0.7):
            p.box(x0, x1, y + 0.18, y + 0.32, z0 + e - 0.08, z0 + e + 0.08, IRON2)
        n = int(abs(x1 - x0) / 1.4)
        for k in range(n + 1):
            x = x0 + (x1 - x0) * k / max(n, 1)
            p.box(x - 0.25, x + 0.25, y, y + 0.18, z0 - 1.1, z0 + 1.1, LOG2)
    else:
        for e in (-0.7, 0.7):
            p.box(x0 + e - 0.08, x0 + e + 0.08, y + 0.18, y + 0.32, z0, z1, IRON2)
        n = int(abs(z1 - z0) / 1.4)
        for k in range(n + 1):
            z = z0 + (z1 - z0) * k / max(n, 1)
            p.box(x0 - 1.1, x0 + 1.1, y, y + 0.18, z - 0.25, z + 0.25, LOG2)


def coin_pile(p, x, z, r, h):
    """Гора монет: ступенчатый курган из золота."""
    for k in range(3):
        rr = r * (1 - k / 3)
        p.prism_xz(K.ngon(x, z, rr, 10), h * k / 3, h * (k + 1) / 3, (GOLD, GOLD2)[k % 2])


def chest(p, x, z, y=0.0, s=1.0, rot=False):
    """Сундук: ящик, крышка-призма, железные полосы, замок."""
    w, d = (1.0 * s, 0.7 * s) if not rot else (0.7 * s, 1.0 * s)
    p.box(x - w, x + w, y, y + 1.0 * s, z - d, z + d, PLANK2)
    if not rot:
        p.prism_zy([(z - d, y + 1.0 * s), (z + d, y + 1.0 * s), (z + d * 0.6, y + 1.5 * s), (z - d * 0.6, y + 1.5 * s)], x - w, x + w, PLANK)
    else:
        p.prism_xy([(x - w, y + 1.0 * s), (x + w, y + 1.0 * s), (x + w * 0.6, y + 1.5 * s), (x - w * 0.6, y + 1.5 * s)], z - d, z + d, PLANK)
    for e in (-0.6, 0.6):
        if not rot:
            p.box(x + e * w - 0.1, x + e * w + 0.1, y, y + 1.52 * s, z - d - 0.04, z + d + 0.04, IRON)
        else:
            p.box(x - w - 0.04, x + w + 0.04, y, y + 1.52 * s, z + e * d - 0.1, z + e * d + 0.1, IRON)
    p.box(x - 0.2 * s, x + 0.2 * s, y + 0.6 * s, y + 1.0 * s, z - d - 0.1, z - d, GOLD)


def lantern_hook(p, g, x, y, z):
    p.box(x - 0.04, x + 0.04, y + 1.0, y + 1.8, z - 0.04, z + 0.04, IRON)
    D.lantern(p, g, x, y, z, 1.1, IRON, LAMP)


def rock_layers(R, Q, axis, fixed, out, half, y0, y1, seed, skip=None, step=3.0):
    """Скала слоями: полосы камня с неровной глубиной и высотой (участки по 3 стада)."""
    layers = ((y0, ROCK2), (y0 + (y1 - y0) * 0.25, ROCKB), (y0 + (y1 - y0) * 0.45, ROCK), (y0 + (y1 - y0) * 0.7, ROCKB2),
              (y0 + (y1 - y0) * 0.85, ROCK3))
    n = int(2 * half // step)
    for k in range(n):
        a0 = -half + 2 * half * k / n
        a1 = -half + 2 * half * (k + 1) / n
        if skip and skip(a0, a1):
            continue
        for m, (ly, col) in enumerate(layers):
            top = layers[m + 1][0] if m + 1 < len(layers) else y1
            j = (rng(seed, k, m) - 0.5) * 1.0 if 0 < m < len(layers) - 1 else 0.0
            d = 0.88 + (1.0 if rng(k, m, seed) > 0.5 else 0.0) + (1.0 if m % 2 else 0.0)
            slab(R, axis, fixed, out, d, a0, a1, ly + (j if m else 0.0), top + (j if m + 1 < len(layers) else 0.0), col)


# ══ ФАСАД: скала со штольней ══════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, ROCK2, ROCK2, DARK)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.2, ROCK2)
    rock_layers(FR, FQ, axis, fixed, out, half, -0.2, 18.9, fi, (lambda a0, a1: -7.0 < a1 and a0 < 7.0) if fi == 0 else None)
    slab(FQ, axis, fixed, out, 1.2, -half - 0.6, half + 0.6, 18.3, 18.9, MOSS)  # мох по верху
    for k in range(7):  # жилы самоцветов
        a = -half + 2.5 + (2 * half - 5.0) * rng(fi, k, 9)
        if fi == 0 and abs(a) < 9.0:
            continue
        y = 3.0 + 12.0 * rng(k, fi, 4)
        lo, hi = sorted((fixed + out * 2.0, fixed + out * 2.3))
        col = (GEM1, GEM2, GEM3, GEM4)[(k + fi) % 4]
        pr = FG.prism_xy if axis == "z" else FG.prism_zy
        pr([(a - 1.6, y - 0.4), (a + 0.8, y + 1.0), (a + 2.4, y + 0.2), (a + 0.4, y - 1.2)], lo, hi, col)
    if axis == "x":  # бока: пещеры с кристаллами
        z = -4.0 if out < 0 else 4.0
        d0, d1 = sorted((fixed + out * 2.88, fixed + out * 3.1))
        FS.prism_zy([(z - 3.4, -0.2), (z + 3.4, -0.2), (z + 2.6, 4.6), (z, 6.0), (z - 2.6, 4.8)], *sorted((fixed + out * 2.7,
                    fixed + out * 2.9)), DARK)
        cluster(FS, FG, fixed + out * 3.3, -0.2, z, 1.6, (GEM1, GEM4, GEM2), fi)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))

# перед: вход в штольню — крепь из брёвен, тёмный проход, табличка, фонарь
FS.box(-7.0, 7.0, -0.2, 14.0, -FZ - 0.5, -FZ, DARK)  # глубина проходa
FR.box(-7.0, 7.0, 14.0, 18.9, -FZ - 2.88, -FZ, ROCKB)
for k, (x, cols) in enumerate(((-4.0, (GEM1, GEM4)), (0.6, (GEM2, GEM4, GEM1)), (4.6, (GEM3, GEM1)))):
    cluster(FS, FG, x, 14.0, -FZ - 3.4, 1.2 + 0.4 * (k == 1), cols, 40 + k)
FS.box(-5.0, 5.0, -0.2, 10.0, -FZ - 1.0, -FZ - 0.5, DARK)
for s in (-1, 1):  # стойки крепи и каменные откосы
    FS.box(*sorted((s * 5.0, s * 6.2)), -0.2, 11.0, -FZ - 3.2, -FZ - 1.6, LOG)
    FS.box(*sorted((s * 6.2, s * 7.0)), -0.2, 14.0, -FZ - 2.88, -FZ, ROCK3)
FS.box(-6.8, 6.8, 10.0, 11.4, -FZ - 3.4, -FZ - 1.4, LOG2)  # верхняя балка
for s in (-1, 1):
    beam(FS, (s * 5.5, 8.0, -FZ - 2.4), (s * 3.6, 10.2, -FZ - 2.4), 0.5, 0.5, LOG)  # распорки
# табличка-доска на цепях над входом
FS.box(-3.6, 3.6, 12.0, 14.0, -FZ - 3.3, -FZ - 3.0, PLANK)
for x in (-3.0, 3.0):
    FS.box(x - 0.06, x + 0.06, 11.4, 12.0, -FZ - 3.2, -FZ - 3.1, IRON)
for k in range(5):
    FS.box(-2.8 + 1.2 * k, -2.4 + 1.2 * k, 12.4, 13.6, -FZ - 3.36, -FZ - 3.3, (GOLD2, PLANK2)[k % 2])
lantern_hook(FS, FG, 0.0, 8.4, -FZ - 2.6)
# рельсы из штольни и вагонетка с золотом
rails(FS, 0.0, 0.0, -FZ - 1.0, -FZ - 5.6, -0.2)
cart(FS, 0.0, -FZ - 4.0, -0.2, along_x=False)
# у входа: бочки, ящики, кирка и лопата, ворот с верёвкой
for x, z in ((-9.0, -FZ - 2.2), (-10.6, -FZ - 3.0)):
    D.barrel(FS, x, z, -0.2, 0.75, 1.6, LOG, IRON)
for k, (x, z) in enumerate(((9.0, -FZ - 2.0), (10.4, -FZ - 2.0), (9.7, -FZ - 2.0))):
    D.crate(FS, x, z, -0.2 + (1.2 if k == 2 else 0.0), 1.2, PLANK, PLANK2)
beam(FS, (-7.6, -0.2, -FZ - 4.6), (-8.4, 2.6, -FZ - 4.2), 0.18, 0.18, LOG)  # кирка
FS.prism_xy([(-9.4, 2.4), (-7.4, 2.9), (-7.4, 2.6), (-9.2, 2.2)], -FZ - 4.3, -FZ - 4.1, IRON2)
wx = 12.0  # ворот на козлах
for e in (-1, 1):
    beam(FS, (wx + e * 1.4, -0.2, -FZ - 4.6), (wx, 3.8, -FZ - 4.6), 0.3, 0.3, LOG)
FS.prism_zy(K.ngon(-FZ - 4.6, 3.6, 0.5, 8), wx - 1.2, wx + 1.2, LOG2)
FS.box(wx - 0.05, wx + 0.05, 0.6, 3.4, -FZ - 5.15, -FZ - 5.05, PLANK)
FS.box(wx - 0.4, wx + 0.4, 0.2, 0.6, -FZ - 5.4, -FZ - 4.8, IRON)
# мостки и лестница по скале справа
FS.box(8.0, 16.0, 9.4, 9.8, -FZ - 3.0, -FZ - 1.6, PLANK)
for x in (8.4, 12.0, 15.6):
    FS.box(x - 0.2, x + 0.2, -0.2, 9.4, -FZ - 2.6, -FZ - 2.2, LOG2)
for k in range(8):
    FS.box(15.0, 16.0, 1.2 * k + 0.6, 1.2 * k + 0.8, -FZ - 3.2, -FZ - 3.0, PLANK2)
for e in (15.0, 16.0):
    FS.box(e - 0.08, e + 0.08, -0.2, 9.6, -FZ - 3.2, -FZ - 3.0, LOG)
lantern_hook(FS, FG, -12.0, 11.0, -FZ - 2.4)
cluster(FS, FG, -15.4, -0.2, -FZ - 2.0, 1.4, (GEM2, GEM4, GEM1), 5)
# сзади: водяное колесо
for k in range(8):
    t = 2 * math.pi * k / 8
    beam(FS, (0.0, 6.0, FZ + 1.6), (5.0 * math.cos(t), 6.0 + 5.0 * math.sin(t), FZ + 1.6), 0.4, 1.4, LOG)
FS.prism_xy(K.ngon(0.0, 6.0, 0.9, 8), FZ + 0.88, FZ + 2.6, IRON)
FS.box(-1.0, 1.0, 11.0, 18.9, FZ + 0.88, FZ + 2.0, PLANK2)
FG.box(-0.8, 0.8, 11.0, 11.4, FZ + 2.0, FZ + 2.1, WATER)

# ══ ИНТЕРЬЕР: главная выработка ═══════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.4
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), ROCKB2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    sk = (lambda a0, a1: a1 > -DOOR[0] - 0.6 and a0 < DOOR[0] + 0.6) if gap else None
    rock_layers(IR, IQ, axis, fixed, out, half, 0.0, C, idx + 10, sk, step=5.4)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, ROCK2)
        for s in (-1, 1):  # крепь вокруг дверей лифта
            slab(IS, axis, fixed, out, 1.88, s * (DOOR[0] + 0.1), s * (DOOR[0] + 1.3), 0.0, DOOR[1] + 0.6, LOG)
        slab(IS, axis, fixed, out, 2.0, -DOOR[0] - 1.6, DOOR[0] + 1.6, DOOR[1] + 0.2, DOOR[1] + 1.4, LOG2)
    for k in range(6):  # кристаллические жилы в стенах
        a = -half + 2.0 + (2 * half - 4.0) * rng(idx, k, 7)
        if gap and abs(a) < DOOR[0] + 2.0:
            continue
        y = 4.0 + 10.0 * rng(k, idx, 8)
        lo, hi = sorted((fixed + out * 2.0, fixed + out * 2.2))
        pr = IG.prism_xy if axis == "z" else IG.prism_zy
        pr([(a - 1.0, y - 0.2), (a + 0.4, y + 0.7), (a + 1.4, y + 0.2), (a + 0.1, y - 0.7)], lo, hi, (GEM1, GEM2, GEM3, GEM4)[(k + idx) % 4])
# крепь-арки из брёвен поперёк зала (у стен, не над экспонатом)
for z in (-12.0, 2.0, 9.0):
    for s in (-1, 1):
        IS.box(s * 14.2 - 0.6, s * 14.2 + 0.6, 0.0, 12.0, z - 0.6, z + 0.6, LOG)
        beam(IS, (s * 14.2, 10.0, z), (s * 11.6, 12.4, z), 0.6, 0.6, LOG2)
    IS.box(-15.0, 15.0, 12.0, 13.2, z - 0.7, z + 0.7, LOG2)
    for s in (-1, 1):
        lantern_hook(IS, IG, s * 10.0, 10.2, z)
# сталактиты
for k in range(14):
    x = -14.0 + 28.0 * rng(k, 31)
    z = ZF + 2.0 + (ZB - ZF - 5.0) * rng(k, 32)
    if abs(x) < 5.0 and -8.0 < z < 2.0:
        continue
    h = 1.4 + 2.0 * rng(k, 33)
    taper(IS, (x, C, z), (x, C - h, z), 1.0 + 0.4 * rng(k, 34), 0.08, (ROCK2, ROCK)[k % 2])
# рельсы с вагонетками
rails(IS, -15.5, 15.5, 7.0, 7.0)
cart(IS, -11.0, 7.0)
cart(IS, 11.5, 7.0, gold=True)
rails(IS, -12.5, -12.5, -14.0, 5.6)
cart(IS, -12.5, -6.0, along_x=False)
# горы монет, сундуки, друзы
for x, z, r, h in ((-9.5, -12.0, 2.6, 1.8), (10.5, -12.5, 3.0, 2.2), (12.5, -3.0, 2.0, 1.2), (-7.0, -1.0, 1.4, 0.8)):
    coin_pile(IS, x, z, r, h)
for x, z, s, rot in ((-6.0, -13.0, 1.1, False), (7.0, -13.4, 1.2, False), (14.2, 2.0 - 4.4, 1.0, True), (-14.0, 11.0, 1.0, True)):
    chest(IS, x, z, 0.0, s, rot)
for x, z, cols, s in ((-14.6, -14.0, (GEM1, GEM4), 1.6), (14.4, -14.2, (GEM2, GEM4), 1.8), (-4.6, -14.2, (GEM3, GEM1), 1.2),
                      (4.8, -14.4, (GEM4, GEM2), 1.2), (14.6, 12.0, (GEM1, GEM3), 1.2)):
    cluster(IS, IG, x, 0.0, z, s, cols, int(x * 10 + z))
# каменный уступ под экспонатом, кольцо рельсов, золотые блики
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.4, 10), 0.0, 0.6, ROCK2)
IR.prism_xz(K.ngon(px, pz, 3.6, 10), 0.6, TOP, ROCK3)
ring_y(IS, px, pz, 4.5, 4.7, 0.0, 0.3, IRON2, n=16)
ring_y(IS, px, pz, 5.7, 5.9, 0.0, 0.3, IRON2, n=16)
for k in range(12):
    t = 2 * math.pi * k / 12
    IS.box(px + 5.2 * math.cos(t) - 0.6, px + 5.2 * math.cos(t) + 0.6, 0.0, 0.16, pz + 5.2 * math.sin(t) - 0.6,
           pz + 5.2 * math.sin(t) + 0.6, LOG2)
for k in range(5):
    t = 2 * math.pi * k / 5 + 0.3
    IS.prism_xz(K.ngon(px + 3.0 * math.cos(t), pz + 3.0 * math.sin(t), 0.35, 8), TOP, TOP + 0.15, GOLD)
B.lift_leaves(IS, LOG2, IRON2)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, ROCK)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.2, -FZ - 2.9, FZ + 2.9, ROCK2)
SL.box(-FX - 1.9, FX + 1.9, 4.5, 9.0, -FZ - 1.9, FZ + 1.9, ROCKB)
SL.box(-FX - 1.4, FX + 1.4, 13.0, 18.9, -FZ - 1.4, FZ + 1.4, ROCK3)
SL.box(-6.8, 6.8, -0.2, 11.4, -FZ - 3.4, -FZ - 1.4, LOG)
SL.box(-5.0, 5.0, -0.2, 10.0, -FZ - 3.5, -FZ - 3.4, DARK)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 2400, (1.0, 0.85, 0.65)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.92, 0.8)),
                                                   ("Gem", (-12, 4, -12), 900, (0.5, 0.9, 1.0))])
