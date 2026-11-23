"""Этаж «Кактус-боксёр» музея-небоскрёба (пятая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — салун на Диком Западе, где проходят бои. Снаружи — дощатый фасад с высоким ступенчатым
«ложным фронтоном», крытая веранда на столбах, двери-«крылья», коновязь, бочки, корыто с водой, над верандой
висит огромная боксёрская перчатка-вывеска, вокруг — кактусы-сагуаро, колесо фургона, на стенах — цветные
афиши боёв (без текста); бока — доски и афиши, кактусы; сзади — водонапорная бочка на сваях. Внутри — салун:
дощатый пол, стойка с полками бутылок лимонада, колесо-люстра с фонарями, лавки зрителей, гонг на стойке,
афиши, горшки с кактусами, груша; экспонат — в центре настоящего ринга: помост с канатами на угловых столбах.
Запуск: blender --background --factory-startup --python scripts/blender/floor_saloon.py -- <репо> <превью>
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

WOOD, WOOD2, WOOD3, WOOD4, SAND, SAND2 = "C08A50", "9A6A3A", "D8A66A", "7A5030", "E8C890", "D4AE70"
RED, RED2, BLUE, WHITE, GOLD, CACT, CACT2 = "D83A2E", "A82A22", "2A5AB0", "F4EEE0", "E8B040", "4A9A4A", "3A7A3A"
DARK, STEEL, CANVAS, POSTER = "2A2220", "8A8A90", "EDE4CC", ("E8C870", "F0B070", "D8E0A0", "F4D0A0")

F = B.Floor("CB", "CactusBoxer", quiet=(SAND2, WOOD4, WOOD2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def saguaro(p, x, z, h, s=1.0):
    """Кактус-сагуаро: ствол с рёбрами-гранями и две изогнутые «руки»."""
    p.prism_xz(K.ngon(x, z, 0.6 * s, 8), 0.0, h, CACT)
    p.prism_xz(K.ngon(x, z, 0.45 * s, 8), h, h + 0.4 * s, CACT2)
    for e, y0, up in ((-1, h * 0.35, h * 0.3), (1, h * 0.5, h * 0.25)):
        beam(p, (x, y0, z), (x + e * 1.4 * s, y0, z), 0.7 * s, 0.7 * s, CACT2)
        beam(p, (x + e * 1.4 * s, y0 - 0.3 * s, z), (x + e * 1.4 * s, y0 + up, z), 0.7 * s, 0.7 * s, CACT)


def glove(p, x, y, z, s, col=RED, along_x=True):
    """Боксёрская перчатка: кулак, большой палец, манжета со шнуровкой (профиль вдоль x или z)."""
    fist = [(-0.9, 0.2), (-0.6, 0.9), (0.2, 1.1), (0.9, 0.7), (1.0, -0.1), (0.6, -0.6), (-0.6, -0.6)]
    thumb = [(0.4, 0.0), (1.0, -0.1), (1.1, 0.4), (0.6, 0.5)]
    cuff = [(-0.6, -0.6), (0.5, -0.6), (0.5, -1.6), (-0.6, -1.6)]
    for pts, w, c in ((fist, 0.7, col), (thumb, 0.8, RED2 if col == RED else col), (cuff, 0.55, WHITE)):
        pp = [(u * s, v * s) for u, v in pts]
        if along_x:
            p.prism_xy([(x + u, y + v) for u, v in pp], z - w * s, z + w * s, c)
        else:
            p.prism_zy([(z + u, y + v) for u, v in pp], x - w * s, x + w * s, c)


def poster(p, axis, fixed, out, a, y, w, h, seed):
    """Афиша боя: бумажный лист, цветная звезда, две перчатки-силуэта и полосы (без надписей)."""
    slab(p, axis, fixed, out, 1.0, a - w / 2, a + w / 2, y - h / 2, y + h / 2, POSTER[seed % 4])
    pr = p.prism_xy if axis == "z" else p.prism_zy
    d0, d1 = sorted((fixed + out * 1.0, fixed + out * 1.06))
    star = [(a + 0.5 * w * 0.5 * math.cos(math.pi / 2 + k * math.pi / 5) * (1.0 if k % 2 == 0 else 0.45),
             y + h * 0.15 + 0.5 * w * 0.5 * math.sin(math.pi / 2 + k * math.pi / 5) * (1.0 if k % 2 == 0 else 0.45)) for k in range(10)]
    pr(star, d0, d1, (RED, BLUE)[seed % 2])
    for k in range(2):
        yy = y - h * 0.22 - k * h * 0.14
        pr(K.rect(a - w * 0.38, a + w * 0.38, yy - h * 0.04, yy + h * 0.04), d0, d1, DARK)


def lantern(p, g, x, y, z):
    """Фонарь «летучая мышь»: крышка, светящееся стекло, ручка."""
    p.prism_xz(K.ngon(x, z, 0.35, 6), y + 0.7, y + 0.85, DARK)
    g.prism_xz(K.ngon(x, z, 0.26, 6), y + 0.15, y + 0.7, "FFC860")
    p.prism_xz(K.ngon(x, z, 0.32, 6), y, y + 0.15, DARK)


# ══ ФАСАД: салун с ложным фронтоном ═══════════════════════════════════════════════════════════════════════════
B.shell_planes(F, WOOD, WOOD, WOOD4)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, SAND2)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.0, WOOD4)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.0, 15.0, WOOD)
    for k in range(int(2 * half // 1.2)):  # вертикальные доски разной высоты кромки
        a = -half + 1.2 * k
        slab(FR, axis, fixed, out, 0.96 + 0.04 * (k % 3), a + 0.05, a + 1.15, 1.0, 15.0 - 0.3 * rng(fi, k), (WOOD, WOOD3, WOOD2)[k % 3])
    slab(FR, axis, fixed, out, 1.88, -half - 0.5, half + 0.5, 15.0, 15.8, WOOD4)
    slab(FR, axis, fixed, out, 0.88, -half, half, 15.8, 18.9, WOOD2)
    if axis == "x":  # бока: афиши и кактусы
        for k, z in enumerate((-10.0, -3.0, 4.0, 11.0)):
            poster(FS, axis, fixed, out, z, 8.0 + 0.8 * (k % 2), 3.2, 4.4, k + int(fixed > 0))
        saguaro(FS, fixed + out * 3.4, -14.0, 7.0)
        saguaro(FS, fixed + out * 3.0, 13.0, 5.6, 0.85)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# ступенчатый ложный фронтон над передним фасадом
FR.prism_xy([(-FX, 15.0), (FX, 15.0), (FX, 16.4), (12.0, 16.4), (12.0, 17.6), (6.0, 17.6), (6.0, 18.8), (-6.0, 18.8), (-6.0, 17.6),
             (-12.0, 17.6), (-12.0, 16.4), (-FX, 16.4)], -FZ - 1.4, -FZ - 0.88, WOOD3)
FS.box(-6.0, 6.0, 18.4, 18.9, -FZ - 1.6, -FZ - 0.88, WOOD4)
for s in (-1, 1):
    FS.box(*sorted((s * 6.0, s * 12.0)), 17.2, 17.7, -FZ - 1.6, -FZ - 1.3, WOOD4)
# веранда: настил, столбы, навес, перила
FS.box(-FX, FX, 0.0, 1.0, -FZ - 5.6, -FZ - 0.88, WOOD2)
for k in range(9):
    FS.box(-FX + 4.53 * k - 0.04, -FX + 4.53 * k + 0.04, 0.99, 1.02, -FZ - 5.6, -FZ - 0.9, WOOD4)
for x in (-16.0, -8.0, 8.0, 16.0):
    FS.box(x - 0.3, x + 0.3, 1.0, 10.2, -FZ - 5.2, -FZ - 4.6, WOOD4)
FS.loft([(-FX - 0.4, 10.2, -FZ - 6.0), (FX + 0.4, 10.2, -FZ - 6.0), (FX + 0.4, 10.2, -FZ - 0.9), (-FX - 0.4, 10.2, -FZ - 0.9)],
        [(-FX - 0.4, 10.7, -FZ - 6.0), (FX + 0.4, 10.7, -FZ - 6.0), (FX + 0.4, 11.6, -FZ - 0.9), (-FX - 0.4, 11.6, -FZ - 0.9)], RED2)
for k in range(10):
    x = -FX + 3.6 * k + 0.3
    FS.box(x, x + 1.8, 10.0, 10.25, -FZ - 6.1, -FZ - 5.9, WHITE)
for s in (-1, 1):
    FS.box(*sorted((s * 8.0, s * 16.0)), 3.0, 3.25, -FZ - 5.15, -FZ - 4.95, WOOD3)
    for k in range(6):
        x = s * (9.0 + 1.3 * k)
        FS.box(x - 0.1, x + 0.1, 1.0, 3.0, -FZ - 5.1, -FZ - 5.0, WOOD3)
# дверь-«крылья», окна с занавесками
FS.box(-3.0, 3.0, 1.0, 9.0, -FZ - 1.0, -FZ - 0.88, DARK)
for s in (-1, 1):
    FS.box(*sorted((s * 0.08, s * 2.4)), 3.2, 6.8, -FZ - 1.3, -FZ - 1.1, WOOD3)
    for k in range(3):
        FS.box(*sorted((s * 0.3, s * 2.2)), 4.0 + 1.0 * k, 4.3 + 1.0 * k, -FZ - 1.36, -FZ - 1.3, WOOD2)
for x in (-11.0, 11.0):
    FG.box(x - 2.6, x + 2.6, 4.0, 8.6, -FZ - 0.94, -FZ - 0.9, "FFD890")
    FS.frame_xy(K.rect(x - 2.9, x + 2.9, 3.7, 8.9), K.rect(x - 2.6, x + 2.6, 4.0, 8.6), -FZ - 1.3, -FZ - 0.88, WOOD4)
    for e in (-1, 1):
        FS.prism_xy([(x + e * 2.6, 8.6), (x + e * 0.4, 8.6), (x + e * 1.6, 6.0), (x + e * 2.6, 5.4)], -FZ - 1.0, -FZ - 0.94, RED)
# огромная перчатка-вывеска на цепях под навесом
glove(FS, 0.0, 13.6, -FZ - 3.0, 1.9, RED)
for e in (-1, 1):
    beam(FS, (e * 1.0, 15.6, -FZ - 3.0), (e * 0.8, 15.0, -FZ - 3.0), 0.08, 0.08, STEEL)
FS.box(-0.4, 0.4, 15.4, 15.8, -FZ - 3.4, -FZ - 0.9, WOOD4)
# коновязь, корыто, бочки, колесо фургона, кактусы
FS.box(-15.0, -9.0, 2.0, 2.3, -FZ - 6.9, -FZ - 6.6, WOOD2)
for x in (-14.6, -9.4):
    FS.box(x - 0.15, x + 0.15, 0.0, 2.3, -FZ - 6.9, -FZ - 6.6, WOOD4)
FS.box(9.0, 13.0, 0.0, 1.2, -FZ - 7.2, -FZ - 6.0, WOOD4)
FG.box(9.2, 12.8, 1.0, 1.1, -FZ - 7.0, -FZ - 6.2, "6AC8E8")
for x, z in ((15.6, -FZ - 6.4), (16.8, -FZ - 7.4)):
    D.barrel(FS, x, z, 0.0, 0.8, 1.7, WOOD2, DARK)
ring_y(FS, -5.6, -FZ - 6.4, 1.3, 1.6, 0.0, 0.3, WOOD4, n=12)
for k in range(6):
    t = math.pi * k / 6
    beam(FS, (-5.6 - 1.3 * math.cos(t), 0.15, -FZ - 6.4 - 1.3 * math.sin(t)), (-5.6 + 1.3 * math.cos(t), 0.15, -FZ - 6.4 + 1.3 * math.sin(t)),
         0.12, 0.12, WOOD4)
saguaro(FS, -17.0, -FZ - 7.0, 6.4)
saguaro(FS, 4.6, -FZ - 7.2, 4.2, 0.7)
# тыл: водонапорная бочка на сваях
for e in (-1, 1):
    for f in (-1, 1):
        beam(FS, (6.0 + e * 1.6, 0.0, FZ + 3.2 + f * 1.6), (6.0 + e * 1.2, 9.0, FZ + 3.2 + f * 1.2), 0.3, 0.3, WOOD4)
FS.prism_xz(K.ngon(6.0, FZ + 3.2, 2.2, 12), 9.0, 13.2, WOOD2)
for y in (9.8, 12.4):
    ring_y(FS, 6.0, FZ + 3.2, 2.2, 2.32, y - 0.15, y + 0.15, DARK, n=12)
FS.cone([(6.0 + 2.4 * math.cos(t), 13.2, FZ + 3.2 + 2.4 * math.sin(t)) for t in [2 * math.pi * k / 12 for k in range(12)]],
        (6.0, 14.6, FZ + 3.2), WOOD4)

# ══ ИНТЕРЬЕР: салун с рингом ══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.4
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), WOOD2)
for k in range(-14, 14):
    if k % 2:
        IQ.box(1.2 * k + 0.03, 1.2 * k + 1.17, 0.02, 0.04, ZF, ZB, WOOD)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, WOOD)
        for k in range(int((a1 - a0) // 1.4)):
            a = a0 + 1.4 * k
            slab(IR, axis, fixed, out, 0.95 + 0.03 * (k % 2), a + 0.05, a + 1.35, 0.0, 4.0, (WOOD2, WOOD4)[k % 2])
        slab(IR, axis, fixed, out, 1.2, a0, a1, 4.0, 4.4, WOOD4)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, WOOD)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, RED)
    for k, a in enumerate((-11.0, -5.0, 5.0, 11.0) if not gap else (-12.0, 12.0)):  # афиши
        if idx == 2 and abs(a) < 8.0:
            continue
        poster(IS, axis, fixed, out, a, 8.6, 3.0, 4.2, k + idx)
    slab(IR, axis, fixed, out, 1.6, -half, half, 14.6, 15.4, WOOD4)
for k in range(-3, 4):  # потолочные балки
    IS.box(-W, W, C - 0.8, C - 0.2, 4.4 * k - 0.35, 4.4 * k + 0.35, WOOD4)
# стойка бара у дальней стены с полками лимонада и гонгом
IR.box(-14.0, -4.0, 0.0, 3.4, ZF + 2.0, ZF + 4.0, WOOD2)
IS.box(-14.2, -3.8, 3.4, 3.7, ZF + 1.8, ZF + 4.2, WOOD4)
for k in range(10):
    IS.box(-13.8 + 1.0 * k, -13.4 + 1.0 * k, 0.4, 3.0, ZF + 4.0, ZF + 4.05, WOOD3)
for r in range(2):
    y = 7.0 + 2.4 * r
    IS.box(-14.0, -4.0, y - 0.2, y, ZF + 0.88, ZF + 2.0, WOOD4)
    for k in range(7):
        x = -13.2 + 1.4 * k
        IS.prism_xz(K.ngon(x, ZF + 1.4, 0.28, 6), y, y + 1.1, ("6AC07A", "E8A040", "B05AC0", "5AA8E0")[(k + r) % 4])
        IS.prism_xz(K.ngon(x, ZF + 1.4, 0.12, 6), y + 1.1, y + 1.6, WHITE)
IS.box(-6.2, -5.0, 3.7, 6.2, ZF + 2.6, ZF + 3.4, WOOD4)
IS.prism_xy(K.ngon(-5.6, 5.6, 1.0, 14), ZF + 2.4, ZF + 2.6, GOLD)
# колесо-люстра с фонарями над рингом
ring_y(IS, 0.0, -3.0, 3.0, 3.4, C - 3.2, C - 2.9, WOOD4, n=16)
for k in range(8):
    t = 2 * math.pi * k / 8
    beam(IS, (0.0, C - 3.05, -3.0), (3.2 * math.cos(t), C - 3.05, -3.0 + 3.2 * math.sin(t)), 0.16, 0.16, WOOD4)
    if k % 2 == 0:
        lantern(IS, IG, 3.2 * math.cos(t), C - 3.9, -3.0 + 3.2 * math.sin(t))
for x in (-2.2, 2.2):
    IS.box(x - 0.03, x + 0.03, C - 2.9, C, -3.03, -2.97, STEEL)
# лавки зрителей по бокам, горшки с кактусами, груша
for s in (-1, 1):
    for k, z in enumerate((-9.0, -4.0, 1.0)):
        x = s * (9.6 + 1.4 * (k % 2))
        IS.box(x - 0.6, x + 0.6, 1.0, 1.3, z - 1.8, z + 1.8, WOOD3)
        for e in (-1, 1):
            IS.box(x - 0.5, x + 0.5, 0.0, 1.0, z + e * 1.5 - 0.12, z + e * 1.5 + 0.12, WOOD4)
for k, (x, z) in enumerate(((-14.0, 9.0), (14.0, 8.6), (14.0, -13.6))):
    IS.prism_xz(K.ngon(x, z, 0.9, 8), 0.0, 1.2, "C86A3A")
    saguaro(IS, x, z, 3.2 + k * 0.6, 0.55)
IS.box(13.0 - 0.04, 13.0 + 0.04, 10.0, C, -10.04, -9.96, STEEL)
IS.prism_xz(K.ngon(13.0, -10.0, 0.7, 10), 6.0, 10.0, RED2)
# ринг-постамент: помост, канвас, угловые столбы с подушками, канаты трёх цветов
px, pz = PED
IR.box(px - 4.6, px + 4.6, 0.0, TOP - 0.15, pz - 4.6, pz + 4.6, BLUE)
IS.box(px - 4.4, px + 4.4, TOP - 0.15, TOP, pz - 4.4, pz + 4.4, CANVAS)
IS.box(px - 4.7, px + 4.7, 0.2, 0.5, pz - 4.7, pz + 4.7, WHITE)
for e in (-1, 1):
    for f in (-1, 1):
        cx, cz = px + e * 4.2, pz + f * 4.2
        IS.prism_xz(K.ngon(cx, cz, 0.22, 8), TOP, TOP + 3.4, STEEL)
        IS.box(cx - 0.32, cx + 0.32, TOP + 0.9, TOP + 3.2, cz - 0.32, cz + 0.32, (RED, BLUE)[(e + f) % 4 == 0])
for h, col in ((TOP + 1.2, RED), (TOP + 2.0, WHITE), (TOP + 2.8, BLUE)):
    for (x0, z0, x1, z1) in ((-4.2, -4.2, 4.2, -4.2), (-4.2, 4.2, 4.2, 4.2), (-4.2, -4.2, -4.2, 4.2), (4.2, -4.2, 4.2, 4.2)):
        beam(IS, (px + x0, h, pz + z0), (px + x1, h, pz + z1), 0.12, 0.12, col)
IS.box(px + 0.2, px + 1.8, 0.0, 0.7, pz + 4.7, pz + 5.6, WOOD4)  # ступенька к рингу
B.lift_leaves(IS, WOOD4, RED)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 15.0, -FZ, FZ, WOOD)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, SAND2)
SL.prism_xy([(-FX, 15.0), (FX, 15.0), (FX, 16.4), (12.0, 16.4), (12.0, 17.6), (6.0, 17.6), (6.0, 18.8), (-6.0, 18.8), (-6.0, 17.6),
             (-12.0, 17.6), (-12.0, 16.4), (-FX, 16.4)], -FZ - 0.4, FZ, WOOD3)
SL.box(-FX - 0.4, FX + 0.4, 10.2, 11.0, -FZ - 6.0, -FZ, RED2)
SL.box(-1.4, 1.4, 11.2, 15.4, -FZ - 3.6, -FZ - 2.4, RED)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 2600, (1.0, 0.88, 0.7)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.95, 0.85)),
                                                   ("Lamp", (0, 10, -3), 900, (1.0, 0.75, 0.4))])
