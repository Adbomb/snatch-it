"""Этаж «Мусорный обжора» музея-небоскрёба (шестая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — весёлый завод переработки на свалке. Снаружи — стены из разноцветного профлиста лоскутами,
рулонные ворота, из верхнего проёма наклонно спускается конвейер с банками, бутылками и коробками, на парапете —
знак переработки из трёх изогнутых стрелок, справа — жёлтый кран-мачта со стрелой и круглым магнитом, держащим
спрессованную машину, перед заводом — штабель цветных спрессованных кубов, стопка шин, контейнеры для сортировки
(синий, жёлтый, зелёный) с крышками, слева — сетчатый забор; сзади — полосатая труба. Внутри — сортировочный цех:
бетонный пол с жёлтой разметкой, стены из профлиста на стальных колоннах, вдоль левой стены — конвейер на ножках
с разноцветным мусором, у дальней стены — бункер с наклонной лентой, справа — гидравлический пресс и кубы,
вилочный погрузчик, большие баки по цветам, кран-балка с крюком, промышленные лампы-купола;
экспонат — на платформе весов с жёлто-чёрной кромкой и стойкой с табло.
Запуск: blender --background --factory-startup --python scripts/blender/floor_recycling.py -- <репо> <превью>
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

RUST, TEALM, BLUEM, YEL, GREY, DARK = "C8703A", "3A9A94", "3A6AB0", "F2C230", "8A8E92", "2E3236"
CONC, DIRT, GREEN, RED, TYRE, WHITE = "A8A49C", "8A847A", "3AA84A", "D83A2E", "26262A", "F2F2EE"
PURPLE, PINK = "8A5AC8", "FF7AB0"
JUNK = ("D83A2E", "3A6AB0", "F2C230", "3AA84A", "FF7AB0", "8A5AC8", "F08A30", "F2F2EE")
PANELS = (RUST, TEALM, BLUEM, "D8A040", "6A9A4A", "B85A5A")

F = B.Floor("JY", "TrashGobbler", quiet=(DIRT, "6A6660", CONC), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def junk(p, x, y, z, k):
    """Кусочек мусора на ленте: банка, бутылка, коробка или скомканный лист — по номеру."""
    kind = k % 4
    col = JUNK[(k * 3) % 8]
    if kind == 0:
        p.prism_xz(K.ngon(x, z, 0.28, 8), y, y + 0.6, col)
        p.prism_xz(K.ngon(x, z, 0.3, 8), y + 0.6, y + 0.66, GREY)
    elif kind == 1:
        p.prism_xz(K.ngon(x, z, 0.24, 6), y, y + 0.7, col)
        p.prism_xz(K.ngon(x, z, 0.1, 6), y + 0.7, y + 1.0, col)
    elif kind == 2:
        p.box(x - 0.4, x + 0.4, y, y + 0.55, z - 0.35, z + 0.35, "C8A070")
        p.box(x - 0.42, x + 0.42, y + 0.25, y + 0.32, z - 0.37, z + 0.37, col)
    else:
        p.prism_xz(K.octa(x, z, 0.4, 0.32, 0.15), y, y + 0.4, col)


def cube(p, x, y, z, s, col):
    """Спрессованная машина: куб с полосами-вмятинами и пятном-окном."""
    p.box(x - s / 2, x + s / 2, y, y + s, z - s / 2, z + s / 2, col)
    for k in range(3):
        yy = y + s * (0.2 + 0.3 * k)
        p.box(x - s / 2 - 0.04, x + s / 2 + 0.04, yy, yy + 0.08, z - s / 2 - 0.04, z + s / 2 + 0.04, DARK)
    p.box(x - s * 0.3, x + s * 0.1, y + s * 0.55, y + s * 0.8, z - s / 2 - 0.06, z - s / 2, "8AC8E8")


def tyre(p, x, y, z):
    """Шина, лежащая плашмя."""
    ring_y(p, x, z, 0.45, 1.0, y, y + 0.55, TYRE, n=10)


def bin_(p, x, z, col, face=-1):
    """Контейнер для сортировки: корпус, крышка, ручка, колёса."""
    p.box(x - 1.3, x + 1.3, 0.3, 2.8, z - 1.0, z + 1.0, col)
    p.loft([(x - 1.4, 2.8, z - 1.1), (x + 1.4, 2.8, z - 1.1), (x + 1.4, 2.8, z + 1.1), (x - 1.4, 2.8, z + 1.1)],
           [(x - 1.4, 3.1, z - 1.1), (x + 1.4, 3.1, z - 1.1), (x + 1.4, 3.3, z + 1.1), (x - 1.4, 3.3, z + 1.1)], col)
    zf = z + face * 1.0
    p.box(x - 0.8, x + 0.8, 2.2, 2.35, *sorted((zf, zf + face * 0.15)), DARK)
    p.prism_xy([(x, 1.9), (x + 0.5, 1.0), (x - 0.5, 1.0)], *sorted((zf, zf + face * 0.04)), WHITE)
    for e in (-1, 1):
        p.prism_zy(K.ngon(z, 0.3, 0.3, 8), x + e * 1.0 - 0.15, x + e * 1.0 + 0.15, TYRE)


def recycle_sign(p, cx, cy, r, d0, d1, col=GREEN):
    """Знак переработки: три стрелки по кругу треугольником."""
    for k in range(3):
        a0 = math.pi / 2 + k * 2 * math.pi / 3 + 0.25
        a1 = a0 + 2 * math.pi / 3 - 0.75
        pts_out = [(cx + r * math.cos(a0 + (a1 - a0) * i / 4), cy + r * math.sin(a0 + (a1 - a0) * i / 4)) for i in range(5)]
        pts_in = [(cx + r * 0.62 * math.cos(a0 + (a1 - a0) * i / 4), cy + r * 0.62 * math.sin(a0 + (a1 - a0) * i / 4)) for i in range(5)]
        for i in range(4):
            p.prism_xy([pts_in[i], pts_out[i], pts_out[i + 1], pts_in[i + 1]], d0, d1, col)
        tip = (cx + r * 0.81 * math.cos(a1 + 0.42), cy + r * 0.81 * math.sin(a1 + 0.42))
        p.prism_xy([(cx + r * 1.12 * math.cos(a1), cy + r * 1.12 * math.sin(a1)), tip,
                    (cx + r * 0.5 * math.cos(a1), cy + r * 0.5 * math.sin(a1))], d0, d1, col)


# ══ ФАСАД: завод переработки ═════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, RUST, GREY, DARK)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, DIRT)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.2, CONC)
    n = int(2 * half // 4.0)
    for k in range(n + 1):  # лоскуты профлиста
        a0 = -half + 4.0 * k
        a1 = min(a0 + 4.0, half)
        if a1 - a0 < 0.5:
            continue
        top = 15.6 - 1.2 * ((k + fi) % 3 == 0)
        slab(FR, axis, fixed, out, 0.88 + 0.06 * (k % 2), a0, a1, 1.2, top, PANELS[(k + fi * 2) % 6])
        if fi == 0:
            for i in range(4):
                a = a0 + 0.5 + 1.0 * i
                if a < a1 - 0.2:
                    slab(FS, axis, fixed, out, 1.0 + 0.06 * (k % 2), a - 0.12, a + 0.12, 1.2, top, PANELS[(k + 3) % 6])
    slab(FR, axis, fixed, out, 1.6, -half - 0.3, half + 0.3, 15.6, 16.2, DARK)
    slab(FR, axis, fixed, out, 0.88, -half, half, 16.2, 18.9, GREY)
    slab(FR, axis, fixed, out, 1.3, -half - 0.2, half + 0.2, 18.4, 18.9, YEL)
    if axis == "x":  # бока: заклёпанные заплаты и ящики
        for k, (z, y) in enumerate(((-9.0, 6.0), (4.0, 9.0), (10.0, 4.0))):
            slab(FS, axis, fixed, out, 1.05, z - 1.5, z + 1.5, y, y + 2.0, PANELS[(k + 4) % 6])
            for e in (-1, 1):
                for f in (-1, 1):
                    slab(FS, axis, fixed, out, 1.12, z + e * 1.3 - 0.1, z + e * 1.3 + 0.1, y + 1.0 + f * 0.8 - 0.1, y + 1.0 + f * 0.8 + 0.1, GREY)
        for k in range(3):
            D.crate(FS, fixed + out * 2.0, -13.0 + 1.3 * k, 0.0, 1.2, "B08048", "8A6234")
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# рулонные ворота
FS.box(-14.0, -6.0, 1.2, 9.6, -FZ - 1.1, -FZ - 0.88, GREY)
for k in range(14):
    y = 1.4 + 0.58 * k
    FS.box(-14.0, -6.0, y, y + 0.1, -FZ - 1.16, -FZ - 1.1, "6A6E72")
FS.box(-14.4, -5.6, 9.6, 10.6, -FZ - 1.6, -FZ - 0.88, DARK)
for k in range(3):
    FS.box(-13.6 + 2.8 * k, -11.6 + 2.8 * k, 0.0, 0.3, -FZ - 1.6, -FZ - 1.1, YEL if k % 2 else DARK)
# конвейер из верхнего проёма наклонно вниз, с мусором
FS.box(-2.0, 4.0, 10.0, 14.0, -FZ - 1.0, -FZ - 0.88, DARK)
for k in range(3):  # лампы над проёмом конвейера
    FG.box(-1.4 + 2.2 * k, -0.6 + 2.2 * k, 14.2, 14.5, -FZ - 1.3, -FZ - 0.9, "FFD070")
cx0, cy0, cz0 = 1.0, 11.0, -FZ - 1.2
cx1, cy1, cz1 = 1.0, 2.4, -FZ - 7.0
beam(FS, (cx0, cy0, cz0), (cx1, cy1, cz1), 2.6, 0.4, "4A4E52", up=(0, 1, 0))
for e in (-1, 1):
    beam(FS, (cx0 + e * 1.4, cy0 + 0.3, cz0), (cx1 + e * 1.4, cy1 + 0.3, cz1), 0.15, 0.5, YEL)
for t in (0.45, 0.85):
    x, y, z = cx0, cy0 + (cy1 - cy0) * t, cz0 + (cz1 - cz0) * t
    for e in (-1, 1):
        FS.box(x + e * 1.2 - 0.15, x + e * 1.2 + 0.15, 0.0, y, z - 0.15, z + 0.15, GREY)
for k in range(6):
    t = 0.08 + 0.15 * k
    junk(FS, cx0 - 0.6 + 1.2 * (k % 2), cy0 + (cy1 - cy0) * t + 0.2, cz0 + (cz1 - cz0) * t, k)
FS.box(-1.6, 3.6, 0.0, 1.8, -FZ - 7.4, -FZ - 5.8, BLUEM)  # приёмный ящик внизу
# знак переработки на парапете
FS.box(-5.2, 5.2, 15.2, 18.8, -FZ - 2.0, -FZ - 1.75, WHITE)
FS.frame_xy(K.rect(-5.4, 5.4, 15.0, 18.9), K.rect(-5.2, 5.2, 15.2, 18.7), -FZ - 2.1, -FZ - 1.75, YEL)
recycle_sign(FS, 0.0, 16.95, 1.55, -FZ - 2.1, -FZ - 2.0)
for x in (-3.8, 3.8):
    FS.box(x - 0.2, x + 0.2, 13.8, 15.2, -FZ - 1.9, -FZ - 0.88, GREY)
# кран-мачта с магнитом и спрессованной машиной
mx, mz = 14.4, -FZ - 4.6
for e in (-1, 1):
    for f in (-1, 1):
        FS.box(mx + e * 0.6 - 0.12, mx + e * 0.6 + 0.12, 0.0, 15.0, mz + f * 0.6 - 0.12, mz + f * 0.6 + 0.12, YEL)
for k in range(7):
    y = 1.0 + 2.0 * k
    beam(FS, (mx - 0.6, y, mz - 0.6), (mx + 0.6, y + 2.0, mz - 0.6), 0.1, 0.1, YEL)
    beam(FS, (mx - 0.6, y, mz + 0.6), (mx + 0.6, y + 2.0, mz + 0.6), 0.1, 0.1, YEL)
FS.box(mx - 1.2, mx + 1.2, 15.0, 16.4, mz - 1.2, mz + 1.2, DARK)
FG.prism_xz(K.ngon(mx, mz, 0.3, 8), 16.4, 16.9, "FF8A30")  # мигалка крана
FG.box(mx - 1.0, mx + 1.0, 15.3, 16.0, mz - 1.24, mz - 1.2, "FFE8A0")  # окно кабины
beam(FS, (mx + 1.0, 16.0, mz), (mx - 7.4, 17.2, mz), 0.8, 0.8, YEL)
beam(FS, (mx + 1.0, 16.0, mz), (mx + 3.2, 16.4, mz), 1.0, 1.0, GREY)
FS.box(mx - 7.05, mx - 6.95, 10.6, 17.0, mz - 0.05, mz + 0.05, DARK)
FS.prism_xz(K.ngon(mx - 7.0, mz, 1.1, 12), 9.8, 10.6, "4A4E52")
FS.prism_xz(K.ngon(mx - 7.0, mz, 1.15, 12), 9.6, 9.8, RED)
cube(FS, mx - 7.0, 7.4, mz, 2.2, BLUEM)
# штабель кубов, шины, контейнеры, забор
for k, (x, y, z, col) in enumerate(((8.4, 0.0, -FZ - 4.2, RED), (10.6, 0.0, -FZ - 4.2, TEALM), (9.5, 2.2, -FZ - 4.2, YEL),
                                     (12.2, 0.0, -FZ - 2.0, PURPLE))):
    cube(FS, x, y, z, 2.2, col)
for k in range(4):
    tyre(FS, 16.6, 0.55 * k, -FZ - 2.2)
for k, (x, col) in enumerate(((-4.2, BLUEM), (-7.4, YEL), (-10.6, GREEN))):
    bin_(FS, x, -FZ - 4.6, col)
for x in (-17.2, -15.2, -13.2):
    FS.box(x - 0.08, x + 0.08, 0.0, 4.6, -FZ - 4.2, -FZ - 4.04, GREY)
FS.frame_xy(K.rect(-17.3, -13.0, 0.4, 4.2), K.rect(-17.2, -13.1, 0.5, 4.1), -FZ - 4.16, -FZ - 4.08, GREY)
for i in range(8):
    x = -17.2 + 0.52 * i
    FS.box(x - 0.02, x + 0.02, 0.5, 4.1, -FZ - 4.14, -FZ - 4.1, "A8ACB0")
for i in range(7):
    y = 0.5 + 0.52 * i
    FS.box(-17.2, -13.1, y - 0.02, y + 0.02, -FZ - 4.14, -FZ - 4.1, "A8ACB0")
D.chain(FS, (-17.2, 4.6, -FZ - 4.12), (-13.0, 4.6, -FZ - 4.12), 6, 0.08, DARK, sag=0.15)
# тыл: полосатая труба
for k in range(6):
    FS.prism_xz(K.ngon(8.0, FZ + 2.4, 1.1 - 0.05 * k, 10), 3.0 * k - 1.0, 3.0 * k + 2.0, (RED, WHITE)[k % 2])

# ══ ИНТЕРЬЕР: сортировочный цех ══════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 0.9
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), CONC)
for x in (-6.4, 6.4):
    IQ.box(x - 0.15, x + 0.15, 0.02, 0.05, -13.0, ZB - 0.9, YEL)
for k in range(5):
    z = -12.0 + 5.0 * k
    IQ.box(-1.2, 1.2, 0.02, 0.05, z - 0.4, z + 0.4, "6A6660")
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, GREY)
        n = int((a1 - a0) // 4.0)
        for k in range(n + 1):
            b0, b1 = a0 + 4.0 * k, min(a0 + 4.0 * (k + 1), a1)
            if b1 - b0 > 0.5:
                slab(IR, axis, fixed, out, 0.94 + 0.04 * (k % 2), b0, b1, 1.2, (C - 2.0) if not gap else DOOR[1], PANELS[(k + idx) % 6])
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, GREY)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.7, YEL)
    slab(IR, axis, fixed, out, 1.0, -half, half, 0.0, 1.2, CONC)
    for k in range(-3, 4):  # стальные колонны
        a = 4.4 * k
        if gap and abs(a) < DOOR[0] + 1.0:
            continue
        slab(IS, axis, fixed, out, 1.4, a - 0.3, a + 0.3, 0.0, C, DARK)
# конвейер вдоль левой стены с мусором
IS.box(-W + 1.4, -W + 4.4, 3.0, 3.4, -14.0, 6.0, "4A4E52")
for e in (-1, 1):
    IS.box(-W + 2.9 + e * 1.5 - 0.1, -W + 2.9 + e * 1.5 + 0.1, 3.4, 3.9, -14.0, 6.0, YEL)
for z in (-12.0, -6.0, 0.0, 5.0):
    for e in (-1, 1):
        IS.box(-W + 2.9 + e * 1.2 - 0.12, -W + 2.9 + e * 1.2 + 0.12, 0.0, 3.0, z - 0.12, z + 0.12, GREY)
for k in range(12):
    junk(IS, -W + 2.4 + 1.0 * (k % 2), 3.4, -13.0 + 1.6 * k, k)
# бункер с наклонной лентой у дальней стены
IS.loft([(-6.0, 9.0, ZF + 0.9), (-1.0, 9.0, ZF + 0.9), (-1.0, 9.0, ZF + 4.0), (-6.0, 9.0, ZF + 4.0)],
        [(-7.0, 13.0, ZF + 0.9), (0.0, 13.0, ZF + 0.9), (0.0, 13.0, ZF + 5.0), (-7.0, 13.0, ZF + 5.0)], TEALM)
IS.box(-5.6, -1.4, 4.0, 9.0, ZF + 0.9, ZF + 3.6, "2F7A76")
for e in (-1, 1):
    IS.box(-3.5 + e * 1.9 - 0.15, -3.5 + e * 1.9 + 0.15, 0.0, 4.0, ZF + 3.3, ZF + 3.6, GREY)
beam(IS, (-12.0, 1.0, ZF + 3.0), (-4.0, 12.6, ZF + 3.0), 2.0, 0.35, "4A4E52", up=(0, 0, 1))
for k in range(4):
    t = 0.15 + 0.2 * k
    junk(IS, -12.0 + 8.0 * t, 1.2 + 11.6 * t, ZF + 3.0, k + 5)
# гидравлический пресс и кубы справа
IR.box(9.0, 15.4, 0.0, 2.0, -14.4, -8.0, YEL)
for e in (-1, 1):
    IS.box(12.2 + e * 2.9 - 0.4, 12.2 + e * 2.9 + 0.4, 2.0, 11.0, -11.6, -10.8, YEL)
IS.box(9.0, 15.4, 11.0, 12.6, -12.0, -10.4, YEL)
IS.prism_xz(K.ngon(12.2, -11.2, 0.6, 10), 7.0, 11.0, "C8CCD0")
IS.box(9.8, 14.6, 6.2, 7.0, -12.6, -9.8, DARK)
cube(IS, 12.2, 2.0, -11.2, 2.0, RED)
for k, (x, z, y, col) in enumerate(((7.4, -13.4, 0.0, TEALM), (7.4, -13.4, 2.0, PURPLE), (5.2, -13.4, 0.0, GREEN))):
    cube(IS, x, y, z, 2.0, col)
for k in range(6):
    t = 2 * math.pi * k / 6
    IS.box(12.2 + 2.0 * math.cos(t) - 0.15, 12.2 + 2.0 * math.cos(t) + 0.15, 2.0, 2.2, -11.2 + 1.2 * math.sin(t) - 0.15, -11.2 + 1.2 * math.sin(t) + 0.15, DARK)
# вилочный погрузчик
fx, fz = 11.4, 0.6
IS.box(fx - 1.2, fx + 1.2, 0.5, 2.4, fz - 1.6, fz + 1.4, YEL)
IS.box(fx - 1.0, fx + 1.0, 2.4, 2.6, fz - 0.8, fz + 1.2, DARK)
for e in (-1, 1):
    IS.box(fx + e * 0.9 - 0.06, fx + e * 0.9 + 0.06, 2.6, 4.8, fz - 0.6, fz - 0.5, DARK)
    IS.box(fx + e * 0.9 - 0.06, fx + e * 0.9 + 0.06, 2.6, 4.8, fz + 1.0, fz + 1.1, DARK)
IS.box(fx - 1.0, fx + 1.0, 4.8, 4.95, fz - 0.6, fz + 1.1, DARK)
for e in (-1, 1):
    IS.box(fx + e * 0.9 - 0.12, fx + e * 0.9 + 0.12, 0.0, 5.2, fz - 1.9, fz - 1.6, GREY)
    IS.box(fx + e * 0.6 - 0.12, fx + e * 0.6 + 0.12, 0.3, 0.45, fz - 3.6, fz - 1.9, GREY)
    for f in (-1.0, 0.9):
        IS.prism_zy(K.ngon(fz + f, 0.5, 0.5, 8), fx + e * 1.2 - 0.15 + e * 0.15, fx + e * 1.2 + 0.15 + e * 0.15, TYRE)
# большие баки по цветам у правой стены
for k, (z, col) in enumerate(((-5.2, BLUEM), (-2.2, GREEN))):
    IS.box(W - 3.4, W - 1.0, 0.0, 3.2, z - 1.3, z + 1.3, col)
    IS.box(W - 3.5, W - 0.9, 3.2, 3.5, z - 1.4, z + 1.4, DARK)
    IS.prism_zy([(z, 2.4), (z + 0.6, 1.2), (z - 0.6, 1.2)], W - 3.45, W - 3.4, WHITE)
# кран-балка с крюком и промышленные лампы
IS.box(-W, W, C - 1.6, C - 0.9, 4.6, 5.4, YEL)
IS.box(-2.0, 0.0, C - 2.4, C - 1.6, 4.2, 5.8, DARK)
IS.box(-1.05, -0.95, 9.4, C - 2.4, 4.95, 5.05, DARK)
IS.prism_zy([(4.6, 9.4), (5.4, 9.4), (5.6, 8.6), (5.2, 8.0), (4.8, 8.6)], -1.2, -0.8, GREY)
for i in (-1, 1):
    for j in (-1, 1):
        x, z = i * 7.0, -3.0 + j * 6.0
        IS.box(x - 0.03, x + 0.03, C - 3.0, C, z - 0.03, z + 0.03, DARK)
        IS.cone([(x + 1.2 * math.cos(t), C - 3.6, z + 1.2 * math.sin(t)) for t in [2 * math.pi * k / 10 for k in range(10)]], (x, C - 2.9, z), GREEN)
        IG.prism_xz(K.ngon(x, z, 0.5, 8), C - 3.75, C - 3.6, "FFF0C8")
for z in (-10.0, 9.0):  # цепи с крюками
    for k in range(6):
        y = C - 1.0 - 0.5 * k
        if k % 2:
            IS.box(-9.04, -8.96, y - 0.4, y, z - 0.12, z + 0.12, GREY)
        else:
            IS.box(-9.12, -8.88, y - 0.4, y, z - 0.04, z + 0.04, GREY)
# платформа весов с кромкой и табло
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.1, 8, turn=0.5), 0.0, 0.5, "4A4E52")
for k in range(8):
    t0, t1 = 2 * math.pi * (k + 0.5) / 8, 2 * math.pi * (k + 1.5) / 8
    pts = [(px + 3.8 * math.cos(t0), pz + 3.8 * math.sin(t0)), (px + 4.15 * math.cos(t0), pz + 4.15 * math.sin(t0)),
           (px + 4.15 * math.cos(t1), pz + 4.15 * math.sin(t1)), (px + 3.8 * math.cos(t1), pz + 3.8 * math.sin(t1))]
    IS.prism_xz(pts, 0.5, TOP, (YEL, DARK)[k % 2])
IS.prism_xz(K.ngon(px, pz, 3.8, 8, turn=0.5), 0.5, TOP, "5A5E62")
for k in range(5):
    IS.box(px - 3.0 + 1.5 * k - 0.04, px - 3.0 + 1.5 * k + 0.04, TOP, TOP + 0.02, pz - 3.0, pz + 3.0, DARK)
IS.box(px + 4.6, px + 5.0, 0.0, 4.4, pz - 0.2, pz + 0.2, GREY)
IS.box(px + 4.2, px + 5.4, 4.4, 5.6, pz - 0.5, pz + 0.5, DARK)
for k in range(4):
    IG.box(px + 4.3 + 0.28 * k, px + 4.5 + 0.28 * k, 4.7, 5.3, pz + 0.5, pz + 0.54, "FF5A3A")
B.lift_leaves(IS, GREY, YEL)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, RUST)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, DIRT)
SL.box(-FX - 0.3, FX + 0.3, 15.6, 18.9, -FZ - 0.3, FZ + 0.3, GREY)
SL.box(-5.4, 5.4, 15.0, 18.9, -FZ - 1.7, -FZ, WHITE)
SL.box(mx - 0.7, mx + 0.7, 0.0, 16.4, mz - 0.7, mz + 0.7, YEL)
SL.box(mx - 7.4, mx + 1.0, 16.0, 17.2, mz - 0.4, mz + 0.4, YEL)
SL.box(7.3, 12.1, 0.0, 4.4, -FZ - 7.5, -FZ - 3.1, RED)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 2600, (1.0, 0.95, 0.85)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.98, 0.95)),
                                                   ("Fill", (-10, 8, -3), 700, (0.9, 0.95, 1.0))])
