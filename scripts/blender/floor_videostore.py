"""Этаж «Живая кассета» музея-небоскрёба (четвёртая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — видеопрокат 90-х. Снаружи — тёмно-синяя стена в неоновой «молнии» и треугольниках мемфис, широкая
витрина магазина в розовой неоновой раме с полками кассет за стеклом, над витриной — огромная VHS-кассета-вывеска
с крутящимися катушками и розовой наклейкой, у входа — стойка возврата кассет, автомат с попкорном и неоновые
звёзды; бока — стена из гигантских кассет-«кирпичей» разных цветов и телевизоры-«бочонки» с цветными полосами
настроечной таблицы; сзади — разгрузочная рампа с коробками. Внутри — зал проката: ковёр с узором мемфис, ряды
стеллажей с кассетами по стенам и островками, стойка кассира с кассовым аппаратом, стена телевизоров с цветными
полосами, машина для попкорна, неоновые стрелки и звёзды на потолке; экспонат — на вращающемся подиуме-«бобине».
Запуск: blender --background --factory-startup --python scripts/blender/floor_videostore.py -- <репо> <превью>
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

NAVY, NAVY2, NAVY3, BLACK, BLACK2, GREY = "1E2050", "2A2E6A", "14163A", "1C1C24", "2E2E3A", "8A8C9A"
PINK, CYAN, YELLOW, LIME, PURPLE, ORANGE = "FF3E9A", "2EE6FF", "FFD83A", "7AEA4A", "9A5AFF", "FF8A2A"
CARPET, CARPET2, SHELF, SHELF2, WHITE, RED = "3A2A6A", "4E3A8A", "D8D2C8", "A8A098", "F4F4F8", "E83A3A"
TAPE_COLS = ("FF3E9A", "2EE6FF", "FFD83A", "7AEA4A", "9A5AFF", "FF8A2A", "F4F4F8", "E83A3A")

F = B.Floor("LC", "LivingCassette", quiet=(CARPET, CARPET2, NAVY3), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def vhs(p, g, x, y, z, s, label=PINK, axis="z", out=-1):
    """VHS-кассета лицом к out по оси axis: корпус, окошко с двумя катушками, наклейка. s — ширина."""
    h, d = s * 0.56, s * 0.18
    if axis == "z":
        z0, z1 = sorted((z, z + out * d))
        p.box(x - s / 2, x + s / 2, y, y + h, z0, z1, BLACK)
        f0, f1 = sorted((z + out * d, z + out * (d + 0.06)))
        p.box(x - s * 0.42, x + s * 0.42, y + h * 0.62, y + h * 0.92, f0, f1, label)
        p.box(x - s * 0.3, x + s * 0.3, y + h * 0.16, y + h * 0.52, f0, f1, NAVY3)
        for e in (-1, 1):
            p.prism_xy(K.ngon(x + e * s * 0.17, y + h * 0.34, s * 0.1, 8), *sorted((z + out * (d + 0.06), z + out * (d + 0.14))), WHITE)
    else:
        x0, x1 = sorted((x, x + out * d))
        p.box(x0, x1, y, y + h, z - s / 2, z + s / 2, BLACK)
        f0, f1 = sorted((x + out * d, x + out * (d + 0.06)))
        p.box(f0, f1, y + h * 0.62, y + h * 0.92, z - s * 0.42, z + s * 0.42, label)
        p.box(f0, f1, y + h * 0.16, y + h * 0.52, z - s * 0.3, z + s * 0.3, NAVY3)


def shelf(p, x0, x1, z0, z1, y_top, rows, facing_axis, facing_out, seed):
    """Стеллаж с кассетами корешками наружу: каркас, полки, корешки разных цветов."""
    p.box(x0, x1, 0.0, y_top, z0, z1, SHELF2)
    span = (x1 - x0) if facing_axis == "z" else (z1 - z0)
    for r in range(rows):
        y = 0.6 + (y_top - 1.0) * r / rows
        n = int(span / 0.8)
        for k in range(n):
            if rng(seed, r, k) < 0.12:
                continue
            col = TAPE_COLS[int(rng(k, r, seed) * len(TAPE_COLS))]
            a = (x0 if facing_axis == "z" else z0) + 0.2 + span * k / n
            hh = 0.9 + 0.25 * rng(r, k)
            if facing_axis == "z":
                zf = z0 if facing_out < 0 else z1
                p.box(a, a + span / n - 0.06, y, y + hh, *sorted((zf, zf + facing_out * 0.12)), col)
            else:
                xf = x0 if facing_out < 0 else x1
                p.box(*sorted((xf, xf + facing_out * 0.12)), y, y + hh, a, a + span / n - 0.06, col)
        if facing_axis == "z":
            p.box(x0 - 0.05, x1 + 0.05, y - 0.15, y, *sorted(((z0 if facing_out < 0 else z1) - facing_out * 0.05,
                                                              (z0 if facing_out < 0 else z1) + facing_out * 0.2)), SHELF)


def crt(p, g, x, y, z, s, face_out=-1, axis="z", seed=0):
    """Телевизор-«бочонок» с настроечной таблицей (цветные полосы светятся)."""
    if axis == "z":
        p.box(x - s / 2, x + s / 2, y, y + s * 0.8, *sorted((z, z + face_out * s * 0.8)), GREY if seed % 2 else BLACK2)
        zf = z + face_out * s * 0.8
        p.box(x - s * 0.42, x + s * 0.3, y + s * 0.1, y + s * 0.7, *sorted((zf, zf + face_out * 0.06)), BLACK)
        cols = ("F4F4F8", "FFD83A", "2EE6FF", "7AEA4A", "FF3E9A", "E83A3A", "3A4AFF")
        for k, col in enumerate(cols):
            a0 = x - s * 0.38 + s * 0.64 * k / 7
            g.box(a0, a0 + s * 0.64 / 7, y + s * 0.15, y + s * 0.65, *sorted((zf + face_out * 0.06, zf + face_out * 0.08)), col)
        for k in range(2):
            p.prism_xy(K.ngon(x + s * 0.38, y + s * (0.5 - 0.22 * k), s * 0.05, 6), *sorted((zf, zf + face_out * 0.1)), GREY)
    else:
        p.box(*sorted((x, x + face_out * s * 0.8)), y, y + s * 0.8, z - s / 2, z + s / 2, GREY if seed % 2 else BLACK2)
        xf = x + face_out * s * 0.8
        p.box(*sorted((xf, xf + face_out * 0.06)), y + s * 0.1, y + s * 0.7, z - s * 0.42, z + s * 0.3, BLACK)
        cols = ("F4F4F8", "FFD83A", "2EE6FF", "7AEA4A", "FF3E9A", "E83A3A", "3A4AFF")
        for k, col in enumerate(cols):
            a0 = z - s * 0.38 + s * 0.64 * k / 7
            g.box(*sorted((xf + face_out * 0.06, xf + face_out * 0.08)), y + s * 0.15, y + s * 0.65, a0, a0 + s * 0.64 / 7, col)


def popcorn(p, g, x, z, y=0.0):
    """Машина для попкорна: красная тумба, стеклянный короб с горкой попкорна, жёлтая крыша."""
    p.box(x - 1.0, x + 1.0, y, y + 2.2, z - 0.8, z + 0.8, RED)
    p.box(x - 1.1, x + 1.1, y + 2.2, y + 2.4, z - 0.9, z + 0.9, YELLOW)
    g.box(x - 0.95, x + 0.95, y + 2.4, y + 4.2, z - 0.75, z + 0.75, "FFF0B8")
    p.box(x - 1.15, x + 1.15, y + 4.2, y + 4.6, z - 0.95, z + 0.95, RED)
    p.cone([(x - 1.15, y + 4.6, z - 0.95), (x + 1.15, y + 4.6, z - 0.95), (x + 1.15, y + 4.6, z + 0.95), (x - 1.15, y + 4.6, z + 0.95)],
           (x, y + 5.4, z), YELLOW)


def star(p, axis, fixed, out, a, y, r, d0, d1, color):
    pts = []
    for k in range(10):
        t = math.pi / 2 + math.pi * k / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((a + rr * math.cos(t), y + rr * math.sin(t)))
    lo, hi = sorted((fixed + out * d0, fixed + out * d1))
    (p.prism_xy if axis == "z" else p.prism_zy)(pts, lo, hi, color)


# ══ ФАСАД: видеопрокат ════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, NAVY, NAVY, NAVY3)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FR, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, 0.0, BLACK2)  # тротуар
    slab(FR, axis, fixed, out, 1.88, -half - 0.8, half + 0.8, 0.0, 1.0, GREY)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.0, 16.0, NAVY)
    slab(FR, axis, fixed, out, 1.88, -half - 0.8, half + 0.8, 16.0, 18.9, BLACK2)  # тёмный карниз
    slab(FS, axis, fixed, out, 2.0, -half - 0.8, half + 0.8, 16.4, 16.7, PINK)
    slab(FS, axis, fixed, out, 2.0, -half - 0.8, half + 0.8, 18.2, 18.5, CYAN)
    lo, hi = sorted((fixed + out * 1.88, fixed + out * 1.98))
    for k in range(int(2 * half // 3.0)):  # мемфис: треугольники и зигзаг на карнизе
        a = -half + 1.5 + 3.0 * k
        pr = FS.prism_xy if axis == "z" else FS.prism_zy
        pr([(a - 0.6, 16.9), (a + 0.6, 16.9), (a, 17.9)] if k % 2 else [(a - 0.6, 17.9), (a + 0.6, 17.9), (a, 16.9)], lo, hi,
           (YELLOW, LIME, PURPLE)[k % 3])
    if axis == "x":  # бока: стена из гигантских кассет
        for r in range(5):
            for k in range(6):
                a = -half + 0.4 + (k + 0.5 * (r % 2)) * 5.6
                if a + 5.0 > half:
                    continue
                vhs(FS, FG, fixed, 1.4 + 2.9 * r, a + 2.5, 5.0, TAPE_COLS[(r * 3 + k) % 8], axis="x", out=out)
    if fi == 1:  # тыл: рампа с коробками
        FR.box(-10.0, 10.0, 0.0, 1.0, FZ + 0.88, FZ + 4.0, GREY)
        for k, x in enumerate((-8.0, -6.6, -7.3, 6.0, 7.4)):
            D.crate(FS, x, FZ + 2.4, 1.0 + (1.2 if k == 2 else 0.0), 1.2, "C8A070", "A07A48")
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))

# перед: широкая витрина в розовой неоновой раме, полки кассет за стеклом, двери, вывеска-кассета
FR.box(-15.0, 15.0, 1.0, 9.4, -FZ - 0.2, -FZ, NAVY3)  # глубина витрины
FS.frame_xy(K.rect(-15.6, 15.6, 0.6, 10.0), K.rect(-15.0, 15.0, 1.0, 9.4), -FZ - 1.6, -FZ, BLACK2)
FG.frame_xy(K.rect(-15.2, 15.2, 0.8, 9.6), K.rect(-14.9, 14.9, 1.1, 9.3), -FZ - 1.72, -FZ - 1.6, PINK)
for k in range(12):  # полосатый козырёк над витриной
    x0 = -15.6 + 2.6 * k
    FS.prism_zy([(-FZ - 1.6, 10.0), (-FZ - 4.2, 9.0), (-FZ - 4.2, 9.3), (-FZ - 1.6, 10.3)], x0, x0 + 2.6, (PINK, WHITE)[k % 2])
for k in range(13):
    FG.prism_xz(K.octa(-15.6 + 2.6 * k, -FZ - 4.2, 0.16, 0.16, 0.06), 8.75, 9.0, YELLOW)
for x0, x1 in ((-14.6, -3.4), (3.4, 14.6)):
    for r in range(3):
        y = 1.6 + 2.6 * r
        FS.box(x0, x1, y - 0.15, y, -FZ - 1.5, -FZ - 0.2, SHELF)
        n = int((x1 - x0) / 0.5)
        for k in range(n):
            if rng(r, k, x0) < 0.15:
                continue
            FS.box(x0 + 0.5 * k + 0.06, x0 + 0.5 * k + 0.44, y, y + 1.0 + 0.3 * rng(k, r), -FZ - 1.45, -FZ - 1.15,
                   TAPE_COLS[int(rng(k, r, 3) * 8)])
FS.box(-3.0, 3.0, 1.0, 8.0, -FZ - 1.3, -FZ - 0.2, BLACK2)  # двери
FG.box(-2.7, -0.15, 1.3, 7.6, -FZ - 1.36, -FZ - 1.3, "8AD8FF")
FG.box(0.15, 2.7, 1.3, 7.6, -FZ - 1.36, -FZ - 1.3, "8AD8FF")
for x0, x1 in ((-14.8, -3.2), (3.2, 14.8)):  # лампы над полками витрины
    FG.box(x0, x1, 9.0, 9.3, -FZ - 1.0, -FZ - 0.3, "FFF4D8")
# огромная кассета-вывеска над витриной: катушки, окошко, наклейка
vhs(FS, FG, 0.0, 10.4, -FZ - 1.6, 15.0, PINK)
for e in (-1, 1):  # зубцы катушек
    for k in range(6):
        t = 2 * math.pi * k / 6
        FS.box(e * 2.55 + 1.0 * math.cos(t) - 0.15, e * 2.55 + 1.0 * math.cos(t) + 0.15, 13.23 + 1.0 * math.sin(t) - 0.15,
               13.23 + 1.0 * math.sin(t) + 0.15, -FZ - 4.86, -FZ - 4.78, BLACK2)
FG.frame_xy(K.rect(-8.3, 8.3, 10.5, 18.9), K.rect(-8.1, 8.1, 10.7, 18.7), -FZ - 1.0, -FZ - 0.94, CYAN)
# плёнка выползает из кассеты и вьётся вниз к попкорну
tube = B.tube
tube(FS, [(4.2, 10.4, -FZ - 4.6), (5.6, 9.6, -FZ - 5.6), (6.4, 8.0, -FZ - 5.2), (5.4, 6.4, -FZ - 5.8), (6.6, 5.2, -FZ - 5.0)],
     [0.5, 0.5, 0.5, 0.5, 0.5], 0.08, (0, 0, 1), "5A3A2A")
# у входа: стойка возврата кассет, машина для попкорна, неоновые звёзды
FS.box(-9.0, -6.6, 1.0, 3.6, -FZ - 3.0, -FZ - 1.8, RED)
FS.box(-8.6, -7.0, 3.0, 3.2, -FZ - 3.06, -FZ - 3.0, BLACK)
FS.box(-9.1, -6.5, 3.6, 3.9, -FZ - 3.1, -FZ - 1.7, YELLOW)
popcorn(FS, FG, 7.6, -FZ - 2.6, 1.0)
for x, y, col in ((-17.0, 12.4, YELLOW), (17.0, 12.0, CYAN), (-12.0, 15.0, LIME)):
    star(FG, "z", -FZ, -1, x, y, 1.1, 0.9, 1.0, col)
# неоновые молнии на передней стене
for x, col in ((-11.5, CYAN), (11.5, YELLOW)):
    FG.prism_xy([(x - 0.3, 15.4), (x + 0.6, 15.4), (x + 0.1, 13.6), (x + 0.7, 13.6), (x - 0.5, 11.0), (x - 0.1, 12.9),
                 (x - 0.7, 12.9)], -FZ - 0.98, -FZ - 0.9, col)

# ══ ИНТЕРЬЕР: зал проката ═════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), CARPET)
for i in range(-7, 7):  # мемфис-узор ковра: треугольники и полоски
    for j in range(-6, 7):
        x, z = 2.4 * i + 1.2, 2.4 * j
        if rng(i, j) < 0.18:
            IS.prism_xz([(x - 0.4, z - 0.3), (x + 0.4, z - 0.3), (x, z + 0.4)], 0.02, 0.05, (YELLOW, CYAN, PINK)[(i + j) % 3])
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    slab(IR, axis, fixed, out, 0.88, -half, half, 13.0, C, NAVY2)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 13.0 if not gap else DOOR[1] + 0.1, NAVY)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 13.0, NAVY)
        slab(IG, axis, fixed, out, 1.0, -DOOR[0] - 0.7, DOOR[0] + 0.7, DOOR[1] + 0.2, DOOR[1] + 0.5, PINK)
    slab(IS, axis, fixed, out, 1.0, -half, half, 12.6, 13.0, PINK)
    slab(IS, axis, fixed, out, 1.0, -half, half, 13.0, 13.3, CYAN)
# стеллажи кассет вдоль боковых стен и передней
for s in (-1, 1):
    x0, x1 = sorted((s * W, s * (W - 2.2)))
    shelf(IS, x0, x1, -14.0, 9.0, 9.0, 4, "x", -s, s)
for x0, x1 in ((-15.0, -6.0), (6.0, 15.0)):
    shelf(IS, x0, x1, ZF, ZF + 2.2, 9.0, 4, "z", 1, x0)
# островки-стеллажи (низкие) у лифта
for x in (-9.5, 9.5):
    shelf(IS, x - 2.0, x + 2.0, 3.0, 4.2, 4.6, 2, "z", -1, x)
    shelf(IS, x - 2.0, x + 2.0, 4.2, 5.4, 4.6, 2, "z", 1, x + 1)
# стена телевизоров за экспонатом
for r in range(3):
    for k in range(5):
        x = -5.6 + 2.8 * k
        crt(IS, IG, x, 3.0 + 2.4 * r, ZF + 0.88, 2.4, face_out=1, seed=r + k)
IS.box(-7.2, 7.2, 0.0, 3.0, ZF + 0.88, ZF + 2.4, BLACK2)
IS.box(-7.3, 7.3, 2.8, 3.0, ZF + 0.8, ZF + 2.6, PINK)
# стойка кассира с кассовым аппаратом (справа у лифта), попкорн слева
IS.box(9.0, 15.0, 0.0, 3.2, 9.8, 11.4, PURPLE)
IS.box(8.8, 15.2, 3.2, 3.5, 9.6, 11.6, CYAN)
IS.box(12.0, 14.0, 3.5, 4.6, 10.0, 11.2, GREY)
IG.box(12.3, 13.7, 4.2, 4.5, 9.95, 10.0, LIME)
popcorn(IS, IG, -12.0, 10.6)
# неоновые стрелки и звёзды на потолке
for k, (x, z, col) in enumerate(((-8.0, -6.0, PINK), (8.0, -6.0, CYAN), (0.0, 6.0, YELLOW), (-8.0, 4.0, LIME), (8.0, 4.0, PURPLE))):
    pts = [(x + 1.4 * math.cos(math.pi / 2 + math.pi * m / 5) * (1 if m % 2 == 0 else 0.45),
            z + 1.4 * math.sin(math.pi / 2 + math.pi * m / 5) * (1 if m % 2 == 0 else 0.45)) for m in range(10)]
    IG.prism_xz(pts, C - 0.12, C - 0.04, col)
# подиум-бобина: две «щёки» катушки, ступица, плёнка
px, pz = PED
ring_y(IS, px, pz, 0.0, 3.8, 0.0, 0.3, BLACK2, n=16)
IR.prism_xz(K.ngon(px, pz, 3.6, 16), 0.0, 0.3, BLACK2)
IS.prism_xz(K.ngon(px, pz, 2.2, 16), 0.3, 0.9, "5A4A3A")
IR.prism_xz(K.ngon(px, pz, 3.6, 16), 0.9, TOP, BLACK)
for k in range(6):
    t = 2 * math.pi * k / 6
    IG.box(px + 2.8 * math.cos(t) - 0.25, px + 2.8 * math.cos(t) + 0.25, TOP, TOP + 0.05, pz + 2.8 * math.sin(t) - 0.25,
           pz + 2.8 * math.sin(t) + 0.25, PINK)
ring_y(IG, px, pz, 3.6, 3.75, 0.9, TOP, CYAN, n=16)
B.lift_leaves(IS, BLACK2, PINK)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, NAVY)
SL.box(-FX - 1.9, FX + 1.9, 16.0, 18.9, -FZ - 1.9, FZ + 1.9, BLACK2)
SL.box(-FX - 2.9, FX + 2.9, -1.0, 0.0, -FZ - 2.9, FZ + 2.9, GREY)
SL.box(-15.0, 15.0, 1.0, 9.4, -FZ - 1.0, -FZ, PINK)
SL.box(-8.0, 8.0, 9.9, 18.86, -FZ - 3.0, -FZ, BLACK)
SL.box(-6.7, 6.7, 15.0, 17.6, -FZ - 3.1, -FZ - 3.0, PINK)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 2600, (0.9, 0.85, 1.0)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.96, 0.92)),
                                                   ("Neon", (0, 4, -12), 900, (1.0, 0.5, 0.8))])
