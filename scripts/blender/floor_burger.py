"""Этаж «Трофейный бургер» музея-небоскрёба (вторая партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — закусочная в духе 1950-х. Снаружи — гофрированная нержавейка горизонтальными рёбрами,
красно-белые пояса, широкие окна-витрины с хромовыми рамами (внутри видны красные диваны), козырёк-навес в
красно-белую полоску, неоновые зигзаги и звёзды; на крыше над входом — огромная вывеска-бургер (булка с
кунжутом, салат, сыр, котлета) на хромовых стойках; угол — скруглённая башенка с неоновым кольцом;
бока — меню-табло (без текста, картинками: коктейль, картошка), сзади — вытяжка и ящики с бутылками.
Внутри — сама закусочная: пол в чёрно-белую шашку, хромовая стойка с табуретами, красные диваны-кабинки
со столиками, музыкальный автомат, неоновые вывески-картинки, подвесные лампы; бургер-экспонат на вращающемся
торте-подставке с хромовым ободом и кольцом из звёзд.
Запуск: blender --background --factory-startup --python scripts/blender/floor_burger.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab  # noqa: E402

CHROME, CHROME2, CHROME3, RED, RED2 = "C3CAD6", "8E96A4", "E2E6EE", "D3263A", "A81C2C"
WHITE, CREAM, MINT, MINT2, BLACK = "F4F0E6", "FFF4DC", "7FD8C4", "4AB8A0", "222228"
BUN, BUN2, SESAME, LETTUCE, CHEESE, PATTY, TOMATO = "E8A040", "C9802A", "FFF0C8", "6AC23A", "FFC83A", "6A3A24", "E8402A"
NEON, NEON2, NEON3, GLASS = "FF4FA8", "38D6F0", "FFE066", "BFE6F2"

F = B.Floor("TB", "TrophyBurger", quiet=(WHITE, CREAM, BLACK), bevel_min=1.0, keep_arch=True)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def burger(p, x, y, z, r):
    """Бургер из слоёв-восьмигранников: нижняя булка, котлета, сыр уголками, салат, помидор, верхняя булка с кунжутом."""
    layers = ((r, 0.0, 0.5, BUN2), (r * 1.02, 0.5, 0.95, PATTY), (r * 1.05, 0.95, 1.1, CHEESE), (r * 1.08, 1.1, 1.3, LETTUCE),
              (r * 0.96, 1.3, 1.5, TOMATO), (r, 1.5, 2.0, BUN), (r * 0.86, 2.0, 2.4, BUN), (r * 0.6, 2.4, 2.6, BUN))
    s = r / 3.0
    for rr, y0, y1, color in layers:
        p.prism_xz(K.octa(x, z, rr, rr, rr * 0.41), y + y0 * s, y + y1 * s, color)
    for k in range(4):  # уголки сыра свисают
        t = math.pi / 4 + math.pi / 2 * k
        cx, cz = x + r * 1.0 * math.cos(t), z + r * 1.0 * math.sin(t)
        p.prism_xz(K.octa(cx, cz, 0.45 * s, 0.45 * s, 0.1 * s), y + 0.6 * s, y + 1.1 * s, CHEESE)
    for k in range(9):  # кунжут
        t = 2 * math.pi * k / 9
        rr = r * (0.35 + 0.3 * (k % 2))
        cx, cz = x + rr * math.cos(t), z + rr * math.sin(t)
        p.box(cx - 0.12 * s, cx + 0.12 * s, y + 2.35 * s, y + 2.48 * s, cz - 0.08 * s, cz + 0.08 * s, SESAME)


def star(p, axis, fixed, out, a, y, r, d0, d1, color):
    pts = []
    for k in range(10):
        t = math.pi / 2 + math.pi * k / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((a + rr * math.cos(t), y + rr * math.sin(t)))
    lo, hi = sorted((fixed + out * d0, fixed + out * d1))
    tris = [[(a, y), pts[k], pts[(k + 1) % 10]] for k in range(10)]
    for tri in tris:
        (p.prism_xy if axis == "z" else p.prism_zy)(tri, lo, hi, color)


# ══ ФАСАД: закусочная из нержавейки ═══════════════════════════════════════════════════════════════════════════
B.shell_planes(F, CHROME2, BLACK, WHITE)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FR, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, -1.0, 1.0, BLACK)  # цоколь
    for k in range(int((2 * half + 3.6) // 1.8)):  # шашка цоколя
        a = -half - 1.8 + 1.8 * k
        if k % 2 == 0:
            slab(FS, axis, fixed, out, 1.95, a, a + 0.9, -0.5, 0.4, WHITE)
    slab(FS, axis, fixed, out, 1.0, -half - 1.0, half + 1.0, 1.0, 2.0, RED)
    # нижние рёбра нержавейки
    for k in range(3):
        y = 2.0 + 0.6 * k
        slab(FS, axis, fixed, out, 0.95, -half, half, y, y + 0.3, CHROME3)
    slab(FR, axis, fixed, out, 0.88, -half, half, 2.0, 15.0, CHROME)
    # витрины: хромовые рамы, стекло, внутри — красные диваны
    n = 3 if axis == "z" else 3
    for i in range(n):
        a = -half + 2 * half * (i + 0.5) / n
        if fi == 0 and i == 1:
            continue  # по центру спереди — вход
        w = 2 * half / n / 2 - 0.9
        slab(FS, axis, fixed, out, 1.1, a - w - 0.3, a + w + 0.3, 4.0, 11.3, CHROME3)
        slab(FS, axis, fixed, out, 0.6, a - w, a + w, 4.3, 11.0, RED2)  # диван за стеклом
        slab(FS, axis, fixed, out, 0.7, a - w, a + w, 4.3, 6.2, RED)
        slab(FG, axis, fixed, out, 1.12, a - w, a + w, 4.3, 11.0, GLASS)
        for k in range(1, 3):
            b = a - w + 2 * w * k / 3
            slab(FS, axis, fixed, out, 1.2, b - 0.1, b + 0.1, 4.3, 11.0, CHROME3)
    # красно-белые пояса и навес в полоску
    slab(FS, axis, fixed, out, 1.0, -half - 1.0, half + 1.0, 11.6, 12.2, RED)
    slab(FS, axis, fixed, out, 1.0, -half - 1.0, half + 1.0, 12.2, 12.6, WHITE)
    m = int((2 * half + 4) // 1.4)
    for k in range(m):
        a = -half - 2.0 + 1.4 * k
        B.chamfer(FS, axis, fixed, out, a, a + 1.4, [(1.0, 13.8), (1.0, 13.4), (2.8, 12.8), (2.8, 13.2)], RED if k % 2 else WHITE)
    slab(FR, axis, fixed, out, 0.88, -half, half, 15.0, 19.0, RED)
    slab(FS, axis, fixed, out, 1.0, -half - 1.0, half + 1.0, 15.0, 15.4, CHROME3)
    slab(FS, axis, fixed, out, 1.0, -half - 1.0, half + 1.0, 18.6, 19.0, CHROME3)
    # неоновые зигзаги
    for k in range(int(2 * half // 2.0)):
        a = -half + 1.0 + 2.0 * k
        y0, y1 = (16.0, 17.8) if k % 2 == 0 else (17.8, 16.0)
        (FG.prism_xy if axis == "z" else FG.prism_zy)(
            [(a - 1.0, y0 - 0.12), (a + 1.0, y1 - 0.12), (a + 1.0, y1 + 0.12), (a - 1.0, y0 + 0.12)],
            *sorted((fixed + out * 1.0, fixed + out * 1.08)), NEON2 if axis == "z" else NEON)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
# перед: вход, звёзды, вывеска-бургер на стойках
FS.box(-3.4, 3.4, 2.0, 11.3, -FZ - 1.2, -FZ, CHROME3)
FG.box(-2.9, 2.9, 2.0, 10.8, -FZ - 1.25, -FZ - 1.2, GLASS)
FS.box(-0.1, 0.1, 2.0, 10.8, -FZ - 1.35, -FZ - 1.25, CHROME3)
for s in (-1, 1):
    FS.box(s * 0.5, s * 1.8, 6.0, 6.3, -FZ - 1.5, -FZ - 1.25, CHROME)  # ручки
    star(FG, "z", -FZ, -1, s * 5.0, 9.4, 0.9, 1.0, 1.1, NEON3)
F.objects(True)
for x in (-4.0, 4.0):
    FS.box(x - 0.2, x + 0.2, 15.0, 17.0, -FZ - 1.2, -FZ - 0.8, CHROME3)
burger(FS, 0.0, 15.1, -FZ - 4.4, 3.8)
F.objects(False)
# угловые башенки с неоновым кольцом
for sx in (-1, 1):
    cx, cz = sx * (FX + 0.2), -FZ - 0.2
    FS.prism_xz(K.octa(cx, cz, 2.0, 2.0, 0.83), 1.0, 15.0, CHROME3)
    FG.frame_xz(K.octa(cx, cz, 2.15, 2.15, 0.9), K.octa(cx, cz, 2.0, 2.0, 0.83), 13.4, 13.8, NEON)
    FS.prism_xz(K.octa(cx, cz, 2.3, 2.3, 0.95), 15.0, 15.4, RED)
    FS.prism_xz(K.octa(cx, cz, 0.5, 0.5, 0.2), 15.4, 18.0, CHROME3)
    star(FG, "z", cz - 0.4, -1, cx, 18.0, 0.8, 0.0, 0.1, NEON3)
# бока: табло-картинки (коктейль, картошка)
for s in (-1, 1):
    fx = s * FX
    FS.box(fx, fx + s * 1.2, 16.0, 18.4, -6.0, 6.0, BLACK)
    # коктейль
    FG.prism_zy([(-4.2, 16.4), (-2.6, 16.4), (-2.2, 18.0), (-4.6, 18.0)], fx + s * 1.2, fx + s * 1.3, NEON)
    FG.box(fx + s * 1.2, fx + s * 1.3, 18.0, 18.2, -4.4, -2.4, CREAM)
    # картошка
    for k in range(4):
        FG.box(fx + s * 1.2, fx + s * 1.3, 17.0, 18.2 - 0.15 * (k % 2), 2.4 + 0.45 * k, 2.7 + 0.45 * k, NEON3)
    FG.prism_zy([(2.2, 16.4), (4.2, 16.4), (4.4, 17.3), (2.0, 17.3)], fx + s * 1.2, fx + s * 1.32, RED)
# тыл: вытяжка, ящики с бутылками
FS.box(-2.4, 2.4, 13.0, 18.0, FZ, FZ + 1.4, CHROME2)
for k in range(4):
    FS.box(-2.0, 2.0, 13.6 + 1.1 * k, 13.9 + 1.1 * k, FZ + 1.4, FZ + 1.5, BLACK)
F.objects(True)
for x in (-9.0, -6.6, 8.0):
    FS.box(x - 1.1, x + 1.1, -1.0, 1.6, FZ, FZ + 2.2, RED2)
    for k in range(3):
        FS.prism_xz(K.octa(x - 0.6 + 0.6 * k, FZ + 1.1, 0.22, 0.22, 0.09), 1.6, 2.6, MINT2)

F.objects(False)
# ══ ИНТЕРЬЕР: закусочная ══════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -2.0)
TOP = 1.5
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), WHITE)
for i in range(-8, 8):
    for j in range(-8, 8):
        if (i + j) % 2 == 0:
            x, z = 2.0 * i, 2.0 * j
            if -W <= x and x + 2 <= W + 0.2 and ZF <= z and z + 2 <= ZB + 0.2:
                IS.box(x, min(x + 2.0, W), 0.02, 0.05, z, min(z + 2.0, ZB), BLACK)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 4.0, MINT)
        slab(IS, axis, fixed, out, 1.0, a0, a1, 4.0, 4.4, CHROME3)
    slab(IQ, axis, fixed, out, 0.7, -half, half, 0.0, C, CREAM)
    if gap:
        slab(IQ, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, CREAM)
    slab(IS, axis, fixed, out, 1.0, -half, half, 13.0, 13.6, RED)
    slab(IS, axis, fixed, out, 1.0, -half, half, 13.6, 14.0, WHITE)
    # неоновые картинки на стенах: звезда, коктейль
    for k in range(2):
        a = -half * 0.5 + half * k
        if gap:
            continue
        star(IG, axis, fixed, out, a, 9.0, 1.4, 0.9, 1.0, (NEON3, NEON2)[k])
F.objects(True)
# стойка с табуретами у передней стены
IS.box(-12.0, 12.0, 0.0, 3.4, ZF + 3.0, ZF + 4.6, RED)
IS.box(-12.2, 12.2, 3.4, 3.7, ZF + 2.8, ZF + 4.8, CHROME3)
for k in range(9):
    x = -10.0 + 2.5 * k
    IS.prism_xz(K.octa(x, ZF + 6.0, 0.3, 0.3, 0.12), 0.0, 2.2, CHROME)
    IS.prism_xz(K.octa(x, ZF + 6.0, 0.8, 0.8, 0.33), 2.2, 2.6, RED)
IS.box(-12.0, 12.0, 6.0, 6.2, ZF + 0.9, ZF + 2.2, CHROME3)  # полка с посудой
for k in range(10):
    x = -11.0 + 2.4 * k
    IS.prism_xz(K.octa(x, ZF + 1.5, 0.3, 0.3, 0.12), 6.2, 7.0, (MINT, NEON, CREAM)[k % 3])
# кабинки: красные диваны со столиками вдоль боковых стен
for s in (-1, 1):
    for z in (-3.5, 3.5):
        x0 = s * W
        for dz in (-1.8, 1.8):
            IS.box(*sorted((x0, x0 - s * 4.2)), 0.0, 1.4, z + dz - 0.6, z + dz + 0.6, RED)
            IS.box(*sorted((x0, x0 - s * 4.2)), 1.4, 3.6, z + dz + (0.3 if dz > 0 else -0.6), z + dz + (0.6 if dz > 0 else -0.3), RED2)
        IS.box(*sorted((x0 - s * 0.6, x0 - s * 3.6)), 2.4, 2.6, z - 1.0, z + 1.0, WHITE)
        IS.box(*sorted((x0 - s * 2.0, x0 - s * 2.2)), 0.0, 2.4, z - 0.1, z + 0.1, CHROME)
        IS.prism_xz(K.octa(x0 - s * 2.6, z, 0.25, 0.25, 0.1), 2.6, 3.4, NEON)  # коктейль
# музыкальный автомат у лифта
jx, jz = 10.5, 11.5
IS.box(jx - 1.6, jx + 1.6, 0.0, 4.6, jz - 1.0, jz + 1.0, RED2)
IG.prism_xy([(jx - 1.6, 4.6), (jx - 1.1, 5.8), (jx, 6.2), (jx + 1.1, 5.8), (jx + 1.6, 4.6)], jz - 1.0, jz + 0.9, NEON3)
IG.box(jx - 1.2, jx + 1.2, 2.2, 4.2, jz - 1.05, jz - 1.0, NEON2)
for k in range(5):
    IS.box(jx - 1.1 + 0.5 * k, jx - 0.8 + 0.5 * k, 0.8, 1.8, jz - 1.08, jz - 1.0, CHROME3)
# подвесные лампы
for x, z in ((-6.0, -8.0), (6.0, -8.0), (-6.0, 6.0), (6.0, 6.0)):
    IS.box(x - 0.04, x + 0.04, 13.8, C, z - 0.04, z + 0.04, CHROME2)
    IS.prism_xz(K.octa(x, z, 0.9, 0.9, 0.37), 13.0, 13.8, RED)
    IG.prism_xz(K.octa(x, z, 0.6, 0.6, 0.25), 12.85, 13.0, CREAM)
# торт-подставка с хромовым ободом и кольцом звёзд
px, pz = PED
IR.prism_xz(K.octa(px, pz, 4.4, 4.4, 1.8), 0.0, 0.6, CHROME)
IR.prism_xz(K.octa(px, pz, 3.8, 3.8, 1.57), 0.6, TOP, WHITE)
IS.frame_xz(K.octa(px, pz, 3.95, 3.95, 1.63), K.octa(px, pz, 3.8, 3.8, 1.57), 0.6, 0.9, RED)
IS.frame_xz(K.octa(px, pz, 3.95, 3.95, 1.63), K.octa(px, pz, 3.8, 3.8, 1.57), TOP - 0.3, TOP, RED)
for k in range(8):
    t = 2 * math.pi * k / 8
    x, z = px + 5.4 * math.cos(t), pz + 5.4 * math.sin(t)
    if math.sin(t) > 0.5:
        continue
    IS.box(x - 0.06, x + 0.06, 0.0, 2.4, z - 0.06, z + 0.06, CHROME)
    star(IG, "z", z, -1, x, 2.9, 0.55, -0.05, 0.05, NEON3)
F.objects(False)
B.lift_leaves(IS, CHROME, RED)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, CHROME)
SL.box(-FX - 1.9, FX + 1.9, -1.0, 1.0, -FZ - 1.9, FZ + 1.9, BLACK)
SL.box(-FX - 1.0, FX + 1.0, 11.6, 12.6, -FZ - 1.0, FZ + 1.0, RED)
SL.box(-FX - 2.8, FX + 2.8, 12.8, 13.8, -FZ - 2.8, FZ + 2.8, WHITE)
SL.box(-FX - 0.9, FX + 0.9, 15.0, 19.0, -FZ - 0.9, FZ + 0.9, RED)
SL.box(-4.0, 4.0, 15.1, 18.5, -FZ - 8.4, -FZ - 0.4, BUN)
for sx in (-1, 1):
    SL.box(sx * (FX - 1.8), sx * (FX + 2.2), 1.0, 15.4, -FZ - 2.2, -FZ + 1.8, CHROME)

F.build(exhibit=(PED[0], TOP, PED[1], 3.2), lamps=[("Hall", (0, 14, 6), 3000, (1.0, 0.95, 0.9)),
                                                   ("Spot", (0, 13, -2), 3200, (1.0, 0.97, 0.9))])
