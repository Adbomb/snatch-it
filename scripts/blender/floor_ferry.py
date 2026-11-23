"""Этаж «Утка-контролёр» музея-небоскрёба (седьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — речной вокзал с пристанью. Внизу — гранитная набережная, перед ней полоса воды с деревянным
причалом, кнехтами и канатами; слева у причала пришвартован белый речной теплоход с красной трубой и рубкой, у входа
— турникеты контроля билетов и будка кассы; стены белые с бирюзовыми пилястрами, в центре — портал с якорем, по
стенам — спасательные круги; наверху — ряд высоких окон с полуциркульным верхом, бирюзовый карниз, мачта с
сигнальными флажками и шпиль с флюгером-корабликом. Внутри — зал ожидания: пол в бело-синюю клетку, деревянные скамьи
вдоль стен, слева — окошки касс, справа — табло рейсов, у дальней стены — большое окно на реку с проплывающей лодкой,
штурвал и спасательные круги, подвесные фонари; экспонат — на тёмно-синем круглом помосте с канатной каймой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_ferry.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, ring_y, slab, taper, tube  # noqa: E402

WHITE, WHITE2, TEAL, TEAL2, NAVY, RED = "F2F0EA", "DCD8CE", "2E9AA8", "237A86", "1E3A5A", "D8343A"
WOOD, WOOD2, GRANITE, GRANITE2, WATER, ROPE = "9A6A3A", "7A5230", "7A7E86", "62666E", "3A8AC8", "D8C090"
GLASS, BRASS, TILE = "BFE0F0", "C8982E", "E8ECF0"

F = B.Floor("DK", "DuckInspector", quiet=(GRANITE2, "4A6A8A"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def buoy(p, axis, fixed, out, a, y, r=0.9):
    """Спасательный круг на стене: бело-красное кольцо из восьми долек."""
    d0, d1 = sorted((fixed + out * 0.0, fixed + out * 0.3))
    for k in range(8):
        t0, t1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        pts = [(a + r * 0.55 * math.cos(t0), y + r * 0.55 * math.sin(t0)), (a + r * math.cos(t0), y + r * math.sin(t0)),
               (a + r * math.cos(t1), y + r * math.sin(t1)), (a + r * 0.55 * math.cos(t1), y + r * 0.55 * math.sin(t1))]
        col = RED if k % 2 == 0 else WHITE
        if axis == "z":
            p.prism_xy(pts, d0, d1, col)
        else:
            p.prism_zy(pts, d0, d1, col)


def arch(a, y0, y1, w, n=6):
    """Контур окна с полуциркульным верхом (a — центр по горизонтали, y1 — низ полукруга)."""
    return [(a - w, y0), (a + w, y0)] + [(a + w * math.cos(math.pi * k / n), y1 + w * math.sin(math.pi * k / n))
                                         for k in range(n + 1)]


def bollard(p, x, z, y=0.0):
    """Кнехт: тумба с шляпкой."""
    p.prism_xz(K.ngon(x, z, 0.32, 8), y, y + 0.7, "3A3E46")
    p.prism_xz(K.ngon(x, z, 0.44, 8), y + 0.7, y + 0.85, "3A3E46")


def turnstile(p, g, x, z, y=0.0):
    """Турникет: тумба, три штанги-трипод, зелёный огонёк."""
    p.box(x - 0.35, x + 0.35, y, y + 1.6, z - 0.45, z + 0.45, "C8CCD4")
    p.box(x - 0.4, x + 0.4, y + 1.6, y + 1.75, z - 0.5, z + 0.5, NAVY)
    for k in range(3):
        t = 2 * math.pi * k / 3
        beam(p, (x + 0.35, y + 1.2, z), (x + 1.3, y + 1.2 + 0.4 * math.sin(t), z + 0.8 * math.cos(t)), 0.1, 0.1, "C8CCD4")
    g.box(x - 0.15, x + 0.15, y + 1.75, y + 1.85, z - 0.15, z + 0.15, "5AE07A")


def bench(p, x0, x1, z, face, y=0.0):
    """Деревянная скамья вдоль x, спинкой к стене (face — куда смотрит сиденье по z)."""
    p.box(x0, x1, y + 0.9, y + 1.1, z - 0.6, z + 0.6, WOOD)
    p.box(x0, x1, y + 1.1, y + 2.4, z - face * 0.6 - 0.1, z - face * 0.6 + 0.1, WOOD2)
    for x in (x0 + 0.3, x1 - 0.3):
        p.box(x - 0.12, x + 0.12, y, y + 0.9, z - 0.5, z + 0.5, "3A3E46")


def bench_z(p, z0, z1, x, face, y=0.0):
    """Скамья вдоль z (у боковых стен), сиденьем в сторону face по x."""
    p.box(x - 0.6, x + 0.6, y + 0.9, y + 1.1, z0, z1, WOOD)
    p.box(x - face * 0.6 - 0.1, x - face * 0.6 + 0.1, y + 1.1, y + 2.4, z0, z1, WOOD2)
    for z in (z0 + 0.3, z1 - 0.3):
        p.box(x - 0.5, x + 0.5, y, y + 0.9, z - 0.12, z + 0.12, "3A3E46")


# ══ ФАСАД: речной вокзал ══════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, WHITE, WHITE, "DDE8F0")
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    if fi != 0:
        slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, GRANITE2)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -1.0, 1.4, GRANITE)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.4, 9.4, WHITE)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, 9.4, 10.2, TEAL)
    slab(FR, axis, fixed, out, 0.88, -half, half, 10.2, 16.6, WHITE)
    slab(FR, axis, fixed, out, 1.88, -half - 0.5, half + 0.5, 16.6, 17.4, TEAL)
    slab(FR, axis, fixed, out, 0.88, -half, half, 17.4, 18.9, WHITE2)
    slab(FS, axis, fixed, out, 1.3, -half - 0.2, half + 0.2, 18.6, 18.9, TEAL2)
    for a in (-half + 0.6, half - 1.8):  # угловые бирюзовые пилястры
        slab(FR, axis, fixed, out, 1.38, a, a + 1.2, 1.4, 16.6, TEAL)
    if axis == "x":  # бока: окна с полуциркульным верхом и спасательные круги
        for z in (-10.0, -3.0, 4.0, 11.0):
            d = lambda v: fixed + out * v  # noqa: E731
            FG.prism_zy(arch(z, 11.2, 14.6, 1.2), *sorted((d(0.88), d(0.92))), GLASS)
            FS.frame_zy(arch(z, 10.9, 14.6, 1.5), arch(z, 11.2, 14.6, 1.2), *sorted((d(0.88), d(1.15))), TEAL2)
            slab(FG, axis, fixed, out, 0.92, z - 1.0, z + 1.0, 3.4, 7.6, GLASS)
            slab(FS, axis, fixed, out, 1.1, z - 1.2, z + 1.2, 3.1, 3.4, TEAL2)
        for z in (-6.5, 7.5):
            buoy(FS, axis, fixed + out * 0.88, out, z, 6.0)
# вода и деревянный причал перед вокзалом
FQ.box(-FX - 2.88, FX + 2.88, -1.0, -0.4, -FZ - 2.88, -FZ - 0.88, WATER)
FR.box(-FX - 2.88, -FX + 0.2, -1.0, -0.1, -FZ - 2.88, -FZ - 0.88, GRANITE2)
FR.box(FX - 0.2, FX + 2.88, -1.0, -0.1, -FZ - 2.88, -FZ - 0.88, GRANITE2)
for k in range(15):  # доски причала
    x = -2.4 + 1.0 * k
    FS.box(x, x + 0.9, -0.3, -0.1, -FZ - 2.88, -FZ - 0.88, WOOD if k % 2 else WOOD2)
for x in (-2.2, 4.0, 10.0, 12.2):
    FS.prism_xz(K.ngon(x, -FZ - 2.6, 0.22, 8), -1.0, 0.4, WOOD2)  # сваи
for x in (0.4, 7.2, 12.8):
    bollard(FS, x, -FZ - 2.3, -0.1)
D.chain(FS, (0.4, 0.6, -FZ - 2.3), (-3.2, 0.9, -FZ - 2.6), 5, 0.1, ROPE, sag=0.3)
# теплоход у причала (слева): корпус, рубка, труба
F.objects(True)
HX0, HX1, HZ0 = -15.6, -3.6, -FZ - 2.86
FS.prism_xy([(HX0 - 1.4, 1.4), (HX1 + 0.6, 1.4), (HX1, -0.5), (HX0 + 0.4, -0.5)], HZ0, -FZ - 0.95, WHITE)
FS.prism_xy([(HX0 - 1.4, 1.4), (HX1 + 0.6, 1.4), (HX1 + 0.5, 1.0), (HX0 - 1.2, 1.0)], HZ0 - 0.04, -FZ - 0.95, RED)
FS.box(HX0 + 0.6, HX1 - 1.0, 1.4, 3.4, HZ0 + 0.2, -FZ - 1.1, WHITE2)
for k in range(5):
    FG.box(HX0 + 1.0 + 2.0 * k, HX0 + 2.2 + 2.0 * k, 2.2, 3.0, HZ0 + 0.16, HZ0 + 0.2, GLASS)
FS.box(HX0 + 0.4, HX1 - 0.8, 3.4, 3.6, HZ0 + 0.1, -FZ - 1.0, NAVY)
FS.box(HX0 + 1.6, HX0 + 4.6, 3.6, 5.2, HZ0 + 0.4, -FZ - 1.3, WHITE)  # рубка
FG.box(HX0 + 1.8, HX0 + 4.4, 4.3, 4.9, HZ0 + 0.36, HZ0 + 0.4, GLASS)
FS.prism_xz(K.ngon(HX1 - 3.0, -FZ - 1.9, 0.6, 10), 3.6, 6.6, RED)  # труба
FS.prism_xz(K.ngon(HX1 - 3.0, -FZ - 1.9, 0.64, 10), 6.0, 6.6, NAVY)
for k in range(6):  # леера
    x = HX0 + 5.2 + 0.9 * k
    FS.box(x - 0.04, x + 0.04, 3.6, 4.5, HZ0 + 0.15, HZ0 + 0.23, WHITE2)
FS.box(HX0 + 5.2, HX1 - 0.6, 4.4, 4.5, HZ0 + 0.15, HZ0 + 0.23, WHITE2)
buoy(FS, "z", HZ0 + 0.1, -1, HX0 + 3.0, 2.3, r=0.45)
F.objects(False)
# центральный ризалит: выступает вперёд, наверху — ступенчатый фронтон с круглым окном-иллюминатором
FR.box(-2.4, 7.2, 10.2, 17.0, -FZ - 2.0, -FZ - 0.5, WHITE)
FR.box(-2.8, 7.6, 17.0, 17.6, -FZ - 2.4, -FZ - 0.5, TEAL)
FR.prism_xy([(-2.8, 17.6), (7.6, 17.6), (5.0, 18.9), (-0.2, 18.9)], -FZ - 2.3, -FZ - 0.5, WHITE2)
FS.prism_xy([(-3.0, 17.55), (7.8, 17.55), (5.1, 18.95), (-0.3, 18.95)], -FZ - 2.36, -FZ - 2.3, TEAL2)
for x in (-2.4, 6.2):
    FR.box(x, x + 1.2, 10.2, 17.0, -FZ - 2.4, -FZ - 1.9, TEAL)
# галерея вдоль причала: навес в бело-синюю полоску на тонких колоннах
for k in range(16):
    x0 = -FX + 0.9 + 2.2 * k
    FS.loft([(x0, 9.0, -FZ - 0.9), (x0 + 2.2, 9.0, -FZ - 0.9), (x0 + 2.2, 9.2, -FZ - 0.9), (x0, 9.2, -FZ - 0.9)],
            [(x0, 8.0, -FZ - 2.8), (x0 + 2.2, 8.0, -FZ - 2.8), (x0 + 2.2, 8.2, -FZ - 2.8), (x0, 8.2, -FZ - 2.8)],
            WHITE if k % 2 else "2A5AC8")
FS.box(-FX + 0.9, FX - 0.9, 7.6, 8.0, -FZ - 2.9, -FZ - 2.7, WHITE)
for x in (-16.4, -2.6, 7.4, 16.4):
    FS.prism_xz(K.ngon(x, -FZ - 2.75, 0.16, 8), -0.1, 7.6, TEAL2)
# центральный портал с якорем, турникеты и касса
FS.box(-1.6, 6.4, 1.4, 8.4, -FZ - 0.96, -FZ - 0.88, NAVY)
FG.box(-1.2, 6.0, 1.4, 7.8, -FZ - 1.0, -FZ - 0.96, "FFE8B0")
FS.frame_xy([(-2.2, 1.4), (7.0, 1.4), (7.0, 8.0), (2.4, 9.4), (-2.2, 8.0)],
            [(-1.6, 1.4), (6.4, 1.4), (6.4, 7.8), (2.4, 8.9), (-1.6, 7.8)], -FZ - 1.5, -FZ - 0.88, TEAL)
FS.box(2.35, 2.45, 1.4, 7.8, -FZ - 1.06, -FZ - 1.0, WHITE)
AX = 2.4  # якорь над порталом
FS.box(AX - 0.2, AX + 0.2, 10.6, 15.0, -FZ - 2.4, -FZ - 1.9, BRASS)
FS.box(AX - 1.0, AX + 1.0, 14.0, 14.3, -FZ - 2.4, -FZ - 1.9, BRASS)
FS.frame_xy(K.ngon(AX, 15.5, 0.6, 10), K.ngon(AX, 15.5, 0.35, 10), -FZ - 2.4, -FZ - 1.9, BRASS)
FG.prism_xy(K.ngon(AX, 18.1, 0.45, 10), -FZ - 2.4, -FZ - 2.3, GLASS)
FS.frame_xy(K.ngon(AX, 18.1, 0.62, 10), K.ngon(AX, 18.1, 0.45, 10), -FZ - 2.5, -FZ - 2.3, BRASS)
tube(FS, [(AX - 2.0, 12.0, -FZ - 2.15), (AX - 1.5, 11.0, -FZ - 2.15), (AX, 10.5, -FZ - 2.15), (AX + 1.5, 11.0, -FZ - 2.15),
          (AX + 2.0, 12.0, -FZ - 2.15)], [0.4] * 5, 0.5, (0, 0, 1), BRASS)
for e in (-1, 1):
    taper(FS, (AX + e * 2.0, 12.0, -FZ - 2.15), (AX + e * 2.3, 12.8, -FZ - 2.15), 0.45, 0.1, BRASS)
F.objects(True)
for x in (-0.4, 2.4, 5.2):
    turnstile(FS, FG, x - 0.6, -FZ - 2.0)
FS.box(7.6, 11.4, 1.4, 6.0, -FZ - 2.6, -FZ - 0.88, TEAL2)  # будка кассы
FS.box(7.4, 11.6, 6.0, 6.4, -FZ - 2.8, -FZ - 0.88, NAVY)
FG.box(8.2, 10.8, 3.2, 5.2, -FZ - 2.64, -FZ - 2.6, "FFE8B0")
FS.box(8.0, 11.0, 3.0, 3.2, -FZ - 3.0, -FZ - 2.6, WOOD)
F.objects(False)
FS.box(13.0, 15.8, 1.4, 7.6, -FZ - 0.96, -FZ - 0.88, NAVY)  # окно справа
FG.box(13.3, 15.5, 1.8, 7.3, -FZ - 1.0, -FZ - 0.96, GLASS)
# верх фасада: ряд окон с полуциркульным верхом
for x in (-13.0, -7.4, 12.2):
    FG.prism_xy(arch(x, 11.0, 14.4, 1.3), -FZ - 0.94, -FZ - 0.9, GLASS)
    FS.frame_xy(arch(x, 10.7, 14.4, 1.6), arch(x, 11.0, 14.4, 1.3), -FZ - 1.2, -FZ - 0.88, TEAL2)
    FS.box(x - 0.05, x + 0.05, 11.0, 15.6, -FZ - 1.0, -FZ - 0.94, TEAL2)
    FS.box(x - 1.3, x + 1.3, 13.0, 13.1, -FZ - 1.0, -FZ - 0.94, TEAL2)
    FS.box(x - 1.7, x + 1.7, 10.4, 10.7, -FZ - 1.6, -FZ - 0.88, WHITE2)
for x, y in ((-10.2, 12.8), (8.6, 12.8)):
    buoy(FS, "z", -FZ - 0.88, -1, x, y)
# мачта с сигнальными флажками и шпиль с флюгером
FS.prism_xz(K.ngon(AX, -FZ - 1.2, 0.18, 8), 17.6, 18.9, WHITE2)
FLAGS = ("D8343A", "F0C020", "2A5AC8", "F2F0EA", "2E9AA8", "D8343A", "F0C020")
for s in (-1, 1):
    pts = D.chain(FS, (AX, 18.7, -FZ - 1.0), (AX + s * 14.0, 17.6, -FZ - 1.6), 7, 0.06, NAVY, sag=0.2)
    for k, (x, y, z) in enumerate(pts[1:]):
        FS.prism_xy([(x - 0.3, y - 0.05), (x + 0.3, y - 0.05), (x, y - 0.75)], z - 0.04, z + 0.04, FLAGS[k % 7])
FS.box(-0.6, 0.6, 17.4, 18.9, FZ + 0.88, FZ + 1.4, TEAL2)  # тыл: служебная дверь, ящики, бухта каната
FS.box(-1.4, 1.4, 1.4, 7.4, FZ + 0.88, FZ + 0.98, NAVY)
F.objects(True)
for k, x in enumerate((-9.0, -7.6, -8.3)):
    D.crate(FS, x, FZ + 1.9, y=0.0 if k < 2 else 1.3, s=1.3)
ring_y(FS, 6.0, FZ + 2.0, 0.3, 0.9, -0.1, 0.4, ROPE, n=10)
F.objects(False)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))

# ══ ИНТЕРЬЕР: зал ожидания ═══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.0
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), TILE)
for i in range(-7, 7):
    for j in range(-7, 7):
        if (i + j) % 2 == 0:
            x, z = 2.4 * i, 2.4 * j
            if -W + 0.2 < x and x + 2.4 < W - 0.2 and ZF + 0.2 < z and z + 2.4 < ZB - 0.2:
                IQ.box(x, x + 2.4, 0.02, 0.04, z, z + 2.4, "4A6A8A")
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, WHITE)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 3.0, TEAL2)
        slab(IS, axis, fixed, out, 1.1, a0, a1, 3.0, 3.2, WOOD)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, WHITE)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, TEAL)
    slab(IR, axis, fixed, out, 1.6, -half, half, 15.4, 16.2, TEAL)
    slab(IS, axis, fixed, out, 1.8, -half, half, 16.2, 16.4, WOOD)
for k in range(-3, 4):
    IS.box(-W, W, C - 0.6, C - 0.2, 4.4 * k - 0.25, 4.4 * k + 0.25, WOOD2)
# слева — окошки касс, справа — табло рейсов
x = -W + 0.88
for z in (-10.0, -4.0, 2.0):
    IR.box(x, x + 1.2, 3.2, 8.6, z - 2.2, z + 2.2, TEAL)
    IG.box(x + 1.2, x + 1.24, 4.6, 7.4, z - 1.5, z + 1.5, "FFE8B0")
    IS.frame_zy(K.rect(z - 1.8, z + 1.8, 4.3, 7.7), K.rect(z - 1.5, z + 1.5, 4.6, 7.4), x + 1.2, x + 1.4, WOOD2)
    IS.box(x + 1.2, x + 2.2, 4.2, 4.4, z - 1.6, z + 1.6, WOOD)
    IS.box(x + 1.2, x + 1.3, 8.6, 9.6, z - 1.0, z + 1.0, NAVY)
x = W - 0.88
IS.box(x - 0.3, x, 8.0, 13.6, -12.0, 4.0, NAVY)
for k in range(5):
    IG.box(x - 0.34, x - 0.3, 8.6 + 1.0 * k, 9.1 + 1.0 * k, -11.4, -4.0, "F0C020")
    IG.box(x - 0.34, x - 0.3, 8.6 + 1.0 * k, 9.1 + 1.0 * k, -3.4, -0.4, "5AE07A" if k % 2 else "F2F0EA")
    IG.box(x - 0.34, x - 0.3, 8.6 + 1.0 * k, 9.1 + 1.0 * k, 0.2, 3.4, "F0C020")
IS.prism_zy(K.ngon(6.0, 11.6, 1.1, 12), x - 0.4, x, WHITE)  # вокзальные часы рядом с табло — без цифр
IS.box(x - 0.48, x - 0.4, 11.55, 12.3, 5.95, 6.05, NAVY)
IS.box(x - 0.48, x - 0.4, 11.55, 11.65, 6.0, 6.7, NAVY)
# скамьи
F.objects(True)
for s in (-1, 1):
    bench_z(IS, -8.0 if s > 0 else -12.4, 6.0, s * (W - 4.0), -s)
bench(IS, -12.0, -6.0, 5.6, 1)
for x, z in ((-W + 1.8, 7.0), (W - 1.8, 7.0), (-W + 1.8, -13.6), (W - 1.8, -13.6)):  # кадки с растениями
    IS.prism_xz(K.ngon(x, z, 0.7, 8), 0.0, 1.2, TEAL2)
    D.bush(IS, x, z, y=1.2, r=0.8)
bench(IS, 6.0, 12.0, 5.6, 1)
F.objects(False)
# дальняя стена: большое окно на реку с лодкой, штурвал, спасательные круги
IS.frame_xy(K.rect(-9.0, 9.0, 5.0, 14.6), K.rect(-8.4, 8.4, 5.6, 14.0), ZF + 0.88, ZF + 1.3, WOOD2)
IG.prism_xy(K.rect(-8.4, 8.4, 9.6, 14.0), ZF + 0.9, ZF + 0.94, "9AD0F0")
IG.prism_xy(K.rect(-8.4, 8.4, 5.6, 9.6), ZF + 0.9, ZF + 0.94, "3A8AC8")
IS.prism_xy([(-6.0, 8.4), (-1.0, 8.4), (-1.6, 7.6), (-5.4, 7.6)], ZF + 0.94, ZF + 1.0, WHITE)  # лодка в окне
IS.prism_xy(K.rect(-4.6, -2.6, 8.4, 9.2), ZF + 0.94, ZF + 1.0, RED)
IS.box(-0.04, 0.04, 5.6, 14.0, ZF + 0.94, ZF + 1.05, WOOD2)
IS.box(-8.4, 8.4, 9.56, 9.64, ZF + 0.94, ZF + 1.05, WOOD2)
IS.box(-9.4, 9.4, 4.6, 5.0, ZF + 0.88, ZF + 1.8, WOOD)
for s in (-1, 1):
    buoy(IS, "z", ZF + 0.88, 1, s * 12.0, 10.0, r=1.0)
WX, WY = 12.0, 5.6  # штурвал
F.objects(True)
IS.frame_xy(K.ngon(-WX, WY, 1.2, 12), K.ngon(-WX, WY, 0.95, 12), ZF + 1.0, ZF + 1.3, WOOD)
IS.prism_xy(K.ngon(-WX, WY, 0.3, 8), ZF + 0.95, ZF + 1.4, BRASS)
for k in range(8):
    t = 2 * math.pi * k / 8
    beam(IS, (-WX, WY, ZF + 1.15), (-WX + 1.6 * math.cos(t), WY + 1.6 * math.sin(t), ZF + 1.15), 0.14, 0.14, WOOD2)
# подвесные фонари
for x, z in ((-8.0, -8.0), (8.0, -8.0), (-8.0, 2.0), (8.0, 2.0)):
    IS.box(x - 0.04, x + 0.04, C - 3.0, C - 0.6, z - 0.04, z + 0.04, NAVY)
    D.lantern(IS, IG, x, C - 4.0, z, s=1.0, cap=NAVY, light="FFE8B0")
F.objects(False)
# помост: тёмно-синий круг с канатной каймой
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, 0.5, NAVY)
ring_y(IS, px, pz, 3.8, 4.15, 0.5, 0.72, ROPE, n=16)
IS.prism_xz(K.ngon(px, pz, 3.7, 16), 0.5, TOP - 0.08, "2A4A70")
IS.prism_xz(K.ngon(px, pz, 3.8, 16), TOP - 0.08, TOP, WHITE)
F.objects(True)
posts = [(px + 5.0 * math.cos(t), pz + 5.0 * math.sin(t)) for t in [math.pi * (0.15 + 0.7 * k / 4) + math.pi for k in range(5)]]
for x, z in posts:  # стойки ограждения очереди с канатами (со стороны лифта проход открыт)
    IS.prism_xz(K.ngon(x, z, 0.4, 8), 0.0, 0.15, BRASS)
    IS.prism_xz(K.ngon(x, z, 0.1, 8), 0.15, 2.4, BRASS)
    IS.prism_xz(K.ngon(x, z, 0.18, 8), 2.4, 2.65, BRASS)
for (x0, z0), (x1, z1) in zip(posts, posts[1:]):
    D.chain(IS, (x0, 2.3, z0), (x1, 2.3, z1), 4, 0.1, RED, sag=0.25)
F.objects(False)
B.lift_leaves(IS, TEAL2, WHITE)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 9.4, -FZ, FZ, WHITE)
SL.box(-FX, FX, 9.4, 18.9, -FZ, FZ, WHITE2)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.4, -FZ - 2.9, FZ + 2.9, GRANITE2)
SL.box(-FX - 0.5, FX + 0.5, 16.6, 17.4, -FZ - 0.5, FZ + 0.5, TEAL)
SL.box(-FX - 0.3, FX + 0.3, 9.4, 10.2, -FZ - 0.3, FZ + 0.3, TEAL)
SL.box(HX0 - 1.2, HX1, -0.4, 3.4, HZ0, -FZ, WHITE)
SL.box(HX1 - 3.6, HX1 - 2.4, 3.4, 6.6, -FZ - 2.5, -FZ - 1.3, RED)

F.build(exhibit=(PED[0], TOP, PED[1], 2.8), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.95, 0.9)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("River", (0, 9, ZF + 5), 800, (0.8, 0.9, 1.0))])
