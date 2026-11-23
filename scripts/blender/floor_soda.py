"""Этаж «Магическая газировка» музея-небоскрёба (четвёртая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — шипучая лавка газировки. Снаружи — мятные и вишнёвые вертикальные полосы-пилястры, белый карниз-
«крем» с волнистой каймой, по фасаду — огромная наклонная банка газировки, пробившая крышу, с полосатой трубочкой,
из её отверстия бьёт радужная шипучка, вокруг поднимаются светящиеся пузырьки; у входа — фонтан-гейзер в бассейне
из крышек, по бокам от двери — колонны-бутылки; бока — круглые окна-крышечки и ящики бутылок; сзади — цистерна с
шлангом. Внутри — газированный бар: пол в мятно-розовый ромб, барная стойка с кранами сиропов и высокими табуретами,
полки с бутылками за стойкой, вдоль стен — высокие стеклянные чаны со светящейся шипучкой и пузырьками, ящики
бутылок, гирлянды пузырьков под потолком; экспонат — на постаменте-крышке с рифлёным краем.
Запуск: blender --background --factory-startup --python scripts/blender/floor_soda.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, ring_y, rng, slab  # noqa: E402

MINT, MINT2, MINT3, CHERRY, CHERRY2, CREAM, CREAM2 = "7AE0C0", "5AC8A6", "A8F0DA", "E8346A", "C0245A", "FFF4E6", "F0DCC8"
CAN, CAN2, SILVER, SILVER2, STRAW, STRAW2 = "E040A0", "B02A80", "D8DCE4", "A8B0BC", "FFFFFF", "FF4A6A"
FIZZ, FIZZ2, FIZZ3, BUBBLE, GLASS = "FF7AE0", "8AF0FF", "FFE27A", "E8FAFF", "BFEFFF"
WOOD, WOOD2, STOOL, BOTTLE, BOTTLE2, BOTTLE3 = "C8905A", "A0703E", "E8346A", "4AC07A", "FF9A3A", "7A6AF0"
TILE, TILE2, NAVY = "FFD6E8", "C8F4E6", "2A2A4A"

F = B.Floor("SD", "MagicSoda", quiet=(TILE, TILE2, CREAM2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def bottle(p, x, z, y, h, col, cap=CHERRY, n=8):
    """Бутылка: брюшко, плечики, горлышко, крышка (n — число граней)."""
    p.prism_xz(K.ngon(x, z, h * 0.18, n), y, y + h * 0.58, col)
    p.loft([(x + h * 0.18 * math.cos(t), y + h * 0.58, z + h * 0.18 * math.sin(t)) for t in [2 * math.pi * (k + 0.5) / n for k in range(n)]],
           [(x + h * 0.07 * math.cos(t), y + h * 0.78, z + h * 0.07 * math.sin(t)) for t in [2 * math.pi * (k + 0.5) / n for k in range(n)]], col)
    p.prism_xz(K.ngon(x, z, h * 0.07, n), y + h * 0.78, y + h, cap if n < 8 else col)
    if n >= 8:
        p.prism_xz(K.ngon(x, z, h * 0.085, n), y + h * 0.93, y + h, cap)


def bottle_crate(p, x, z, y=0.0, color=CHERRY):
    """Ящик с четырьмя бутылками."""
    p.box(x - 1.0, x + 1.0, y, y + 0.9, z - 0.7, z + 0.7, color)
    for e in (-0.5, 0.5):
        for f in (-0.3, 0.3):
            bottle(p, x + e, z + f, y + 0.6, 1.4, (BOTTLE, BOTTLE2, BOTTLE3)[int(rng(x, z, e, f) * 3)], n=4)


def tank(p, g, x, z, h, fizz, seed):
    """Стеклянный чан с шипучкой: основание, светящийся столб, обручи, крышка, пузырьки."""
    p.prism_xz(K.ngon(x, z, 1.5, 10), 0.0, 0.8, SILVER2)
    g.prism_xz(K.ngon(x, z, 1.25, 10), 0.8, h, fizz)
    for y in (0.8 + (h - 0.8) * 0.33, 0.8 + (h - 0.8) * 0.66):
        ring_y(p, x, z, 1.25, 1.4, y - 0.1, y + 0.1, SILVER, n=10)
    p.prism_xz(K.ngon(x, z, 1.4, 10), h, h + 0.4, SILVER)
    p.cone([(x + 1.4 * math.cos(t), h + 0.4, z + 1.4 * math.sin(t)) for t in [2 * math.pi * k / 10 for k in range(10)]],
           (x, h + 1.2, z), SILVER2)
    for k in range(4):
        y = 1.6 + (h - 2.0) * rng(seed, k)
        t = 2 * math.pi * rng(k, seed)
        g.prism_xz(K.ngon(x + 1.32 * math.cos(t), z + 1.32 * math.sin(t), 0.18, 6), y, y + 0.36, BUBBLE)


def bubbles(g, x0, x1, y0, y1, z0, z1, n, seed, r=0.3):
    """Светящиеся пузырьки в объёме."""
    for k in range(n):
        x = x0 + (x1 - x0) * rng(seed, k, 1)
        y = y0 + (y1 - y0) * rng(seed, k, 2)
        z = z0 + (z1 - z0) * rng(seed, k, 3)
        rr = r * (0.6 + 0.8 * rng(seed, k, 4))
        g.prism_xz(K.ngon(x, z, rr, 6), y - rr, y + rr, BUBBLE if k % 3 else FIZZ2)


# ══ ФАСАД: лавка газировки ════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, CREAM, CREAM, "F4C8E0")
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FR, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, 0.0, MINT2)
    slab(FR, axis, fixed, out, 1.88, -half - 0.6, half + 0.6, 0.0, 1.2, CHERRY2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.2, 15.0, CREAM)
    n = int(2 * half // 3.0)
    for k in range(n):  # вертикальные полосы мята / вишня
        a = -half + 3.0 * k
        if fi == 0 and -11.0 < a + 1.5 < 11.0:
            continue
        slab(FR, axis, fixed, out, 1.08, a + 0.1, a + 1.5, 1.2, 15.0, (MINT, CHERRY)[k % 2])
    slab(FR, axis, fixed, out, 1.88, -half - 0.8, half + 0.8, 15.0, 16.4, CREAM)
    lo, hi = sorted((fixed + out * 1.88, fixed + out * 2.3))
    pr = FS.prism_xy if axis == "z" else FS.prism_zy
    for k in range(int(2 * half // 2.0) + 1):  # волнистая кайма «крема»
        a = -half - 0.8 + 2.0 * k
        pr([(a, 15.0), (a + 2.0, 15.0), (a + 1.5, 14.4), (a + 1.0, 14.2), (a + 0.5, 14.4)], lo, hi, CREAM2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 16.4, 18.9, MINT3)
    slab(FS, axis, fixed, out, 1.0, -half, half, 17.4, 17.8, CHERRY)
    if axis == "x":  # бока: круглые окна-крышечки и ящики бутылок
        for z in (-9.0, 0.0, 9.0):
            d0, d1 = sorted((fixed + out * 1.08, fixed + out * 1.5))
            FS.prism_zy([(z + 2.2 * math.cos(2 * math.pi * k / 20) * (1.0 if k % 2 else 0.9),
                          8.0 + 2.2 * math.sin(2 * math.pi * k / 20) * (1.0 if k % 2 else 0.9)) for k in range(20)], d0, d1, SILVER)
            FG.prism_zy(K.ngon(z, 8.0, 1.5, 12), *sorted((fixed + out * 1.5, fixed + out * 1.56)), (FIZZ, FIZZ2, FIZZ3)[int(z) % 3])
        for k, z in enumerate((-13.0, -4.6, 4.6, 13.0)):
            bottle_crate(FS, fixed + out * 2.0, z, 0.0, (CHERRY, MINT2)[k % 2])
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))

# перед: витринная арка с дверью, колонны-бутылки
FR.box(-11.0, 11.0, 1.2, 15.0, -FZ - 0.88, -FZ, MINT3)
FS.box(-3.2, 3.2, 1.2, 8.0, -FZ - 1.2, -FZ - 0.88, NAVY)
FS.prism_xy(K.ngon(0.0, 8.0, 3.2, 16)[:9], -FZ - 1.2, -FZ - 0.88, NAVY)
FG.prism_xy(K.ngon(0.0, 8.0, 2.6, 16)[:9], -FZ - 1.26, -FZ - 1.2, FIZZ2)
FS.frame_xy(K.rect(-3.8, 3.8, 1.2, 8.0), K.rect(-3.2, 3.2, 1.2, 8.0), -FZ - 1.5, -FZ - 0.88, CHERRY)
for s in (-1, 1):  # колонны-бутылки
    bottle(FS, s * 6.6, -FZ - 2.2, 0.0, 12.0, (BOTTLE, BOTTLE3)[s > 0], CHERRY)
    for k in range(2):  # круглые окна-пузыри
        FG.prism_xy(K.ngon(s * 9.6, 4.0 + 4.0 * k, 0.9, 10), -FZ - 0.94, -FZ - 0.88, (FIZZ, FIZZ3)[k])
# огромная наклонная банка, пробившая карниз: корпус, ободки, верх с язычком, трубочка, шипучка
CX, CY, CZ, R, H = -1.0, 9.6, -FZ - 4.4, 3.7, 10.4
TILT = math.radians(18)
def can_pt(x, y, z):
    dx, dy = x - CX, y - CY
    return (CX + dx * math.cos(TILT) - dy * math.sin(TILT), CY + dx * math.sin(TILT) + dy * math.cos(TILT), z)
for k, (y0, y1, rr, col) in enumerate(((CY - H / 2, CY - H / 2 + 0.5, R * 0.9, SILVER), (CY - H / 2 + 0.5, CY + H / 2 - 0.6, R, CAN),
                                         (CY + H / 2 - 0.6, CY + H / 2, R * 0.88, SILVER))):
    ring0 = [can_pt(CX + rr * math.cos(t), y0, CZ + rr * math.sin(t)) for t in [2 * math.pi * m / 12 for m in range(12)]]
    ring1 = [can_pt(CX + rr * math.cos(t), y1, CZ + rr * math.sin(t)) for t in [2 * math.pi * m / 12 for m in range(12)]]
    FS.loft(ring0, ring1, col)
for y0, y1, col in ((CY - 1.4, CY + 0.6, STRAW), (CY - 2.6, CY - 1.9, CAN2), (CY + 1.2, CY + 1.9, CAN2)):  # этикетка
    ring0 = [can_pt(CX + R * 1.02 * math.cos(t), y0, CZ + R * 1.02 * math.sin(t)) for t in [math.pi + math.pi * m / 6 for m in range(7)]]
    ring1 = [can_pt(CX + R * 1.02 * math.cos(t), y1, CZ + R * 1.02 * math.sin(t)) for t in [math.pi + math.pi * m / 6 for m in range(7)]]
    FS.loft(ring0, ring1, col)
TOPC = can_pt(CX, CY + H / 2, CZ)
for k in range(5):  # трубочка в полоску
    a = can_pt(CX + 0.9, CY + H / 2 + 1.4 * k, CZ)
    b = can_pt(CX + 0.9 + 0.2, CY + H / 2 + 1.4 * (k + 1), CZ)
    if b[1] > 18.8:
        break
    beam(FS, a, b, 0.5, 0.5, (STRAW, STRAW2)[k % 2])
for k, (dx, dy, rr, col) in enumerate(((-1.4, 0.8, 0.9, FIZZ), (-2.6, 1.8, 0.7, FIZZ2), (-3.6, 2.8, 0.6, FIZZ3),
                                       (-0.6, 2.0, 0.6, FIZZ3), (-2.0, 3.6, 0.5, FIZZ))):  # шипучка из банки
    x, y = TOPC[0] + dx, min(TOPC[1] + dy, 18.4)
    FG.prism_xz(K.ngon(x, CZ, rr, 8), y - rr, y + rr, col)
bubbles(FG, -14.0, 12.0, 9.0, 18.0, -FZ - 4.0, -FZ - 2.0, 14, 3, 0.35)
# фонтан-гейзер в бассейне из крышек у входа справа
gx, gz = 8.6, -FZ - 5.2
for k in range(20):
    t = 2 * math.pi * k / 20
    FS.box(gx + 2.4 * math.cos(t) - 0.25, gx + 2.4 * math.cos(t) + 0.25, 0.0, 0.9, gz + 2.4 * math.sin(t) - 0.25,
           gz + 2.4 * math.sin(t) + 0.25, SILVER)
FS.prism_xz(K.ngon(gx, gz, 2.4, 12), 0.0, 0.7, CHERRY2)
FG.prism_xz(K.ngon(gx, gz, 2.1, 12), 0.7, 0.8, FIZZ2)
for k, (rr, y0, y1) in enumerate(((0.5, 0.8, 3.0), (0.35, 3.0, 4.6), (0.22, 4.6, 5.6))):
    FG.prism_xz(K.ngon(gx, gz, rr, 8), y0, y1, (FIZZ2, BUBBLE, FIZZ)[k])
bubbles(FG, gx - 1.4, gx + 1.4, 4.0, 7.0, gz - 1.4, gz + 1.4, 6, 9, 0.25)
# тыл: цистерна со шлангом
for k in range(3):
    FS.box(-6.0 + 0.2 * k, 6.0 - 0.2 * k, 1.0 + 1.6 * k, 2.6 + 1.6 * k, FZ + 1.2, FZ + 5.0, (SILVER, SILVER2, SILVER)[k])
FS.box(-6.4, 6.4, 0.0, 1.0, FZ + 1.0, FZ + 5.2, CHERRY2)
D.chain(FS, (5.0, 5.0, FZ + 3.0), (8.0, 0.4, FZ + 2.0), 6, 0.35, CHERRY, 1.2)

# ══ ИНТЕРЬЕР: газированный бар ════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.3
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), TILE)
for i in range(-8, 9):  # ромбы пола
    for j in range(-7, 8):
        if (i + j) % 2:
            x, z = 2.0 * i, 2.0 * j
            IQ.prism_xz([(x, z - 0.98), (x + 0.98, z), (x, z + 0.98), (x - 0.98, z)], 0.02, 0.05, TILE2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.4, CHERRY2)
        top = DOOR[1] + 0.1 if gap else 12.0
        n = int((a1 - a0) // 2.0)
        for k in range(n):  # полосы мята / крем
            b0 = a0 + (a1 - a0) * k / n
            slab(IR, axis, fixed, out, 0.88, b0, b0 + (a1 - a0) / n, 1.4, top, (MINT3, CREAM)[k % 2])
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 12.0, MINT3)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 1.2, DOOR[0] + 1.2, DOOR[1] + 0.2, DOOR[1] + 0.8, CHERRY)
    slab(IR, axis, fixed, out, 1.88, -half, half, 12.0, 13.0, CREAM)
    slab(IR, axis, fixed, out, 0.88, -half, half, 13.0, C, MINT)
# барная стойка у передней стены за экспонатом: краны сиропов, табуреты, полки с бутылками
IR.box(-10.0, 10.0, 0.0, 3.4, ZF + 3.0, ZF + 5.0, CHERRY)
IS.box(-10.2, 10.2, 3.4, 3.7, ZF + 2.8, ZF + 5.2, CREAM)
for k in range(8):
    x = -8.4 + 2.4 * k
    IS.box(x - 0.2, x + 0.2, 3.7, 4.8, ZF + 3.6, ZF + 4.0, SILVER)
    IS.box(x - 0.4, x + 0.4, 4.6, 5.0, ZF + 3.4, ZF + 4.2, SILVER2)
    IG.prism_xz(K.ngon(x, ZF + 3.8, 0.22, 6), 5.0, 5.5, (FIZZ, FIZZ2, FIZZ3)[k % 3])
for r in range(2):
    y = 6.8 + 2.6 * r
    IS.box(-12.0, 12.0, y - 0.2, y, ZF + 0.88, ZF + 2.2, WOOD)
    for k in range(12):
        x = -11.0 + 2.0 * k
        bottle(IS, x, ZF + 1.5, y, 2.0, (BOTTLE, BOTTLE2, BOTTLE3, CAN)[int(rng(k, r) * 4)], (CHERRY, SILVER)[k % 2], n=5)
for x in (-8.4, -5.4, 5.4, 8.4):  # табуреты
    IS.prism_xz(K.ngon(x, ZF + 6.4, 0.18, 6), 0.0, 2.4, SILVER2)
    IS.prism_xz(K.ngon(x, ZF + 6.4, 0.8, 10), 2.4, 2.8, STOOL)
    IS.prism_xz(K.ngon(x, ZF + 6.4, 0.5, 8), 0.0, 0.12, SILVER)
# стеклянные чаны с шипучкой вдоль боковых стен
for s in (-1, 1):
    for k, z in enumerate((-9.0, -2.0, 5.0)):
        tank(IS, IG, s * (W - 2.2), z, 9.0 + 1.2 * ((k + (s > 0)) % 2), (FIZZ, FIZZ2, FIZZ3)[(k + (s > 0)) % 3], k + 3 * s)
        if k < 2:  # трубы между чанами
            beam(IS, (s * (W - 1.0), 8.0, z + 1.4), (s * (W - 1.0), 8.0, z + 5.6), 0.4, 0.4, SILVER)
# ящики бутылок у лифта, гирлянды пузырьков под потолком
for x, z, col in ((-12.0, 10.6, CHERRY), (-10.0, 12.2, MINT2), (12.0, 10.6, MINT2), (10.2, 12.4, CHERRY)):
    bottle_crate(IS, x, z, 0.0, col)
for k in range(4):
    x = -9.0 + 6.0 * k
    pts = D.chain(IS, (x, 16.8, ZF + 2.0), (x, 16.8, ZB - 3.0), 8, 0.08, SILVER, 1.6)
    for m, q in enumerate(pts[1:-1]):
        IG.prism_xz(K.ngon(q[0], q[2], 0.35, 6), q[1] - 0.7, q[1] - 0.0, (FIZZ, FIZZ2, FIZZ3, BUBBLE)[(m + k) % 4])
# постамент-крышка: рифлёный край, вишнёвый верх, серебряная кромка
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.2, 16), 0.0, 0.4, CHERRY2)
IS.prism_xz([(px + 3.6 * math.cos(2 * math.pi * k / 32) * (1.0 if k % 2 else 0.92),
              pz + 3.6 * math.sin(2 * math.pi * k / 32) * (1.0 if k % 2 else 0.92)) for k in range(32)], 0.4, TOP, SILVER)
IQ.prism_xz(K.ngon(px, pz, 3.0, 16), TOP - 0.05, TOP + 0.02, CHERRY)
bubbles(IG, px - 4.0, px + 4.0, 2.0, 9.0, pz - 3.0, pz + 1.0, 8, 21, 0.3)
B.lift_leaves(IS, CHERRY2, MINT)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, CREAM)
SL.box(-FX - 2.9, FX + 2.9, -1.0, 0.0, -FZ - 2.9, FZ + 2.9, MINT2)
SL.box(-FX - 1.9, FX + 1.9, 15.0, 16.4, -FZ - 1.9, FZ + 1.9, CREAM2)
for s in (-1, 1):
    SL.box(s * 11.0, s * FX, 1.2, 15.0, -FZ - 1.08, -FZ, CHERRY)
ring0 = [can_pt(CX + R * math.cos(t), CY - H / 2, CZ + R * math.sin(t)) for t in [2 * math.pi * m / 6 for m in range(6)]]
ring1 = [can_pt(CX + R * math.cos(t), CY + H / 2, CZ + R * math.sin(t)) for t in [2 * math.pi * m / 6 for m in range(6)]]
SL.loft(ring0, ring1, CAN)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 3000, (1.0, 0.95, 1.0)),
                                                   ("Spot", (0, 13, -3), 3200, (1.0, 0.97, 0.94)),
                                                   ("Fizz", (-12, 6, 0), 800, (1.0, 0.5, 0.9))])
