"""Этаж «Автомат-пожиратель» музея-небоскрёба (шестая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — круглосуточный японский магазинчик (комбини) с квартирами наверху. Внизу — стеклянная витрина
с автоматической дверью сбоку, над ней — вывеска из трёх цветных полос и светящийся короб со значком, слева на
улице — ряд из четырёх ярких торговых автоматов со светящимися витринами напитков; наверху — плиточный фасад
с окнами, наружными блоками кондиционеров и балкончиками; на углу — столб с проводами и трансформатором,
перед входом — высокие флаги-нобори, велосипеды, урны для сортировки, разметка парковки; на боку — наружная
лестница. Внутри — магазин: светлая плитка, по левой стене — холодильники со стеклянными дверцами и бутылками,
по правой — полки с яркими пачками, два стеллажа-островка, у дальней стены — касса, витрина с горячей едой,
кофемашина и светящиеся меню-картинки, у лифта — капсульные автоматы и стойка журналов, светлые панели на
потолке; экспонат — на тёмном восьмиугольном помосте с жёлтой светящейся лентой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_konbini.py -- <репо> <превью>
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

WHITE, WHITE2, TILE, TILE2, GREEN, ORANGE = "F4F6F8", "DDE2E6", "E8D8C0", "D4C0A4", "3AB86A", "F08A30"
BLUE, RED, YELLOW, DARK, GREY, ASPH = "2E6ADB", "D83A2E", "F2C230", "2A2E34", "8A929C", "4A4E54"
NAVY, GLASS, PINK = "26305A", "6FA4C8", "FF6AB0"
GOODS = ("FF5A5A", "5AB8FF", "FFD03A", "6AE86A", "FF8AC0", "B07AE8", "F08A30", "F4F6F8")

F = B.Floor("VM", "DevourerVending", quiet=(ASPH, "C8CCD0", TILE2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def vending(p, g, x, z, col, seed, face=-1):
    """Торговый автомат лицом к face (по z): корпус, светящаяся витрина с рядами бутылок, кнопки, лоток."""
    p.box(x - 1.05, x + 1.05, 0.0, 4.6, z - 0.9, z + 0.9, col)
    zf = z + face * 0.9
    lo, hi = sorted((zf, zf + face * 0.04))
    g.box(x - 0.85, x + 0.85, 2.2, 4.2, lo, hi, "F4FAFF")
    for r in range(3):
        for k in range(5):
            xx = x - 0.7 + 0.35 * k
            yy = 2.35 + 0.62 * r
            lo2, hi2 = sorted((zf + face * 0.04, zf + face * 0.08))
            p.box(xx - 0.1, xx + 0.1, yy, yy + 0.42, lo2, hi2, GOODS[(k + r + seed) % 8])
    lo3, hi3 = sorted((zf, zf + face * 0.08))
    for k in range(5):
        p.box(x - 0.7 + 0.35 * k - 0.08, x - 0.7 + 0.35 * k + 0.08, 2.0, 2.12, lo3, hi3, "FF4A4A")
    p.box(x - 0.7, x + 0.7, 0.4, 1.0, lo3, hi3, DARK)
    p.box(x + 0.5, x + 0.85, 1.3, 1.8, lo3, hi3, GREY)
    p.box(x - 1.1, x + 1.1, 4.6, 4.8, z - 0.95, z + 0.95, WHITE)


def bicycle(p, x, z, col):
    """Велосипед вдоль x: два колеса-кольца, рама, руль, седло."""
    for e in (-1, 1):
        p.frame_xy(K.ngon(x + e * 1.0, 0.75, 0.75, 12), K.ngon(x + e * 1.0, 0.75, 0.6, 12), z - 0.06, z + 0.06, DARK)
    beam(p, (x - 1.0, 0.75, z), (x, 0.8, z), 0.12, 0.12, col)
    beam(p, (x, 0.8, z), (x + 1.0, 0.75, z), 0.12, 0.12, col)
    beam(p, (x - 0.3, 1.6, z), (x, 0.8, z), 0.12, 0.12, col)
    beam(p, (x - 0.3, 1.6, z), (x + 0.8, 1.6, z), 0.12, 0.12, col)
    beam(p, (x + 0.8, 1.6, z), (x + 1.0, 0.75, z), 0.12, 0.12, col)
    p.box(x - 0.55, x - 0.05, 1.7, 1.85, z - 0.15, z + 0.15, DARK)
    p.box(x + 0.7, x + 0.9, 1.6, 2.0, z - 0.06, z + 0.06, GREY)
    p.box(x + 0.75, x + 0.85, 2.0, 2.1, z - 0.4, z + 0.4, DARK)


def nobori(p, x, z, col, col2):
    """Флаг-нобори: шест и узкое вертикальное полотнище с полосой."""
    p.prism_xz(K.ngon(x, z, 0.07, 6), 0.0, 7.0, GREY)
    p.box(x + 0.08, x + 1.0, 7.0, 7.08, z - 0.03, z + 0.03, GREY)
    p.box(x + 0.1, x + 1.0, 2.0, 7.0, z - 0.03, z + 0.03, col)
    p.box(x + 0.1, x + 1.0, 6.2, 6.7, z - 0.05, z + 0.05, col2)
    p.box(x + 0.1, x + 1.0, 2.0, 2.4, z - 0.05, z + 0.05, col2)


def ac_unit(p, axis, fixed, out, a, y):
    """Наружный блок кондиционера с решёткой вентилятора."""
    d = lambda v: fixed + out * v  # noqa: E731
    if axis == "z":
        p.box(a - 0.9, a + 0.9, y, y + 1.2, *sorted((d(0.88), d(1.8))), WHITE2)
        p.prism_xy(K.ngon(a - 0.2, y + 0.6, 0.42, 10), *sorted((d(1.8), d(1.84))), GREY)
        p.prism_xy(K.ngon(a - 0.2, y + 0.6, 0.12, 6), *sorted((d(1.84), d(1.88))), DARK)
    else:
        p.box(*sorted((d(0.88), d(1.8))), y, y + 1.2, a - 0.9, a + 0.9, WHITE2)
        p.prism_zy(K.ngon(a - 0.2, y + 0.6, 0.42, 10), *sorted((d(1.8), d(1.84))), GREY)


# ══ ФАСАД: комбини с квартирами ══════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, WHITE, WHITE, WHITE2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, ASPH)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 0.8, GREY)
    slab(FR, axis, fixed, out, 0.88, -half, half, 0.8, 10.8, WHITE)
    slab(FR, axis, fixed, out, 0.88, -half, half, 10.8, 18.9, TILE)
    for r in range(4):  # швы плитки
        slab(FS, axis, fixed, out, 0.94, -half, half, 12.4 + 1.6 * r - 0.06, 12.4 + 1.6 * r + 0.06, TILE2)
    slab(FR, axis, fixed, out, 1.5, -half - 0.3, half + 0.3, 10.6, 11.0, WHITE2)
    slab(FR, axis, fixed, out, 1.3, -half - 0.2, half + 0.2, 18.4, 18.9, WHITE2)
    for k, col in enumerate((GREEN, ORANGE, BLUE)):  # полосы вывески по кругу
        slab(FS, axis, fixed, out, 1.2, -half - 0.1, half + 0.1, 8.4 + 0.7 * k, 9.1 + 0.7 * k, col)
    if axis == "x":  # бока: окна квартир, кондиционеры
        for k, z in enumerate((-10.0, -2.0, 6.0)):
            slab(FG, axis, fixed, out, 0.92, z - 1.6, z + 1.6, 12.6, 15.8, "FFE8C0")
            slab(FS, axis, fixed, out, 1.1, z - 1.8, z + 1.8, 12.4, 12.6, WHITE2)
            slab(FS, axis, fixed, out, 1.1, z - 0.06, z + 0.06, 12.6, 15.8, WHITE2)
            ac_unit(FS, axis, fixed, out, z + 3.2, 12.0)
        slab(FG, axis, fixed, out, 0.92, -14.0, 10.0, 2.0, 7.6, GLASS)
        for k in range(7):
            z = -14.0 + 4.0 * k
            slab(FS, axis, fixed, out, 1.1, z - 0.1, z + 0.1, 2.0, 7.6, GREY)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# парковочная разметка
for k in range(5):
    x = -16.0 + 3.0 * k
    FQ.box(x - 0.1, x + 0.1, -0.1, -0.06, -FZ - 2.88, -FZ - 0.8, WHITE)
# витрина и автоматическая дверь
FG.box(-6.0, 9.6, 1.0, 7.8, -FZ - 0.94, -FZ - 0.9, GLASS)
for x in (-6.0, -2.1, 1.8, 5.7, 9.6):
    FS.box(x - 0.12, x + 0.12, 0.8, 8.0, -FZ - 1.2, -FZ - 0.88, GREY)
FS.box(-6.2, 9.8, 0.8, 1.0, -FZ - 1.2, -FZ - 0.88, GREY)
FS.box(-6.2, 9.8, 7.8, 8.4, -FZ - 1.2, -FZ - 0.88, GREY)
for k in range(9):  # плакаты на стекле
    x = -5.4 + 1.7 * k
    if k % 3 == 1:
        FS.box(x - 0.5, x + 0.5, 5.6, 7.0, -FZ - 1.0, -FZ - 0.96, GOODS[k % 8])
FG.box(10.8, 15.6, 0.8, 7.6, -FZ - 0.94, -FZ - 0.9, "88B8D8")
FS.frame_xy(K.rect(10.6, 15.8, 0.8, 7.8), K.rect(10.8, 15.6, 0.8, 7.6), -FZ - 1.2, -FZ - 0.88, GREY)
FS.box(13.16, 13.24, 0.8, 7.6, -FZ - 1.0, -FZ - 0.94, GREY)
FS.box(10.6, 15.8, 7.8, 8.4, -FZ - 1.4, -FZ - 0.88, DARK)
# светящийся короб со значком над витриной
FG.box(-1.6, 5.2, 8.2, 11.4, -FZ - 1.86, -FZ - 1.8, WHITE)
FS.box(-1.8, 5.4, 8.0, 11.6, -FZ - 1.8, -FZ - 0.88, GREY)
FS.prism_xy(K.octa(1.8, 9.8, 1.2, 1.2, 0.4), -FZ - 1.92, -FZ - 1.86, ORANGE)
FS.prism_xy(K.octa(1.8, 9.8, 0.7, 0.7, 0.24), -FZ - 1.96, -FZ - 1.92, WHITE)
FS.prism_xy(K.octa(1.8, 9.8, 0.4, 0.4, 0.14), -FZ - 2.0, -FZ - 1.96, GREEN)
# ряд торговых автоматов слева
for k, (x, col) in enumerate(((-16.2, RED), (-13.9, BLUE), (-11.6, WHITE), (-9.3, YELLOW))):
    vending(FS, FG, x, -FZ - 1.9, col, k)
FS.box(-17.4, -8.1, 0.0, 0.2, -FZ - 3.0, -FZ - 0.9, GREY)
# урны для сортировки
FS.box(-7.8, -6.6, 0.0, 1.6, -FZ - 2.6, -FZ - 1.6, BLUE)
FS.box(-7.8, -6.6, 0.0, 1.6, -FZ - 3.8, -FZ - 2.8, GREEN)
FS.box(-7.8, -6.6, 0.0, 1.6, -FZ - 5.0, -FZ - 4.0, YELLOW)
for z in (-FZ - 2.1, -FZ - 3.3, -FZ - 4.5):
    FS.box(-7.9, -6.5, 1.6, 1.8, z - 0.6, z + 0.6, GREY)
# квартиры наверху: окна, кондиционеры, балкончики
for k, x in enumerate((-13.0, -5.0, 3.0, 11.0)):
    FG.box(x - 1.8, x + 1.8, 12.4, 16.0, -FZ - 0.94, -FZ - 0.9, "FFE8C0")
    FS.frame_xy(K.rect(x - 2.0, x + 2.0, 12.2, 16.2), K.rect(x - 1.8, x + 1.8, 12.4, 16.0), -FZ - 1.1, -FZ - 0.88, WHITE2)
    FS.box(x - 0.06, x + 0.06, 12.4, 16.0, -FZ - 1.05, -FZ - 0.95, WHITE2)
    FS.box(x - 2.4, x + 2.4, 11.6, 11.9, -FZ - 2.6, -FZ - 0.88, GREY)
    for i in range(9):
        FS.box(x - 2.3 + 0.575 * i - 0.04, x - 2.3 + 0.575 * i + 0.04, 11.9, 13.2, -FZ - 2.58, -FZ - 2.5, GREY)
    FS.box(x - 2.4, x + 2.4, 13.2, 13.35, -FZ - 2.62, -FZ - 2.46, GREY)
    if k in (1, 3):
        ac_unit(FS, "z", -FZ, -1, x + 1.0, 16.6)
    if k in (0, 2):  # бельё на верёвке
        D.chain(FS, (x - 2.3, 14.8, -FZ - 2.4), (x + 2.3, 14.8, -FZ - 2.4), 4, 0.04, GREY, sag=0.2)
        for i in range(3):
            xx = x - 1.4 + 1.4 * i
            FS.box(xx - 0.45, xx + 0.45, 13.6, 14.7, -FZ - 2.44, -FZ - 2.36, GOODS[(i + k) % 8])
# столб с проводами и трансформатором на правом углу
px0, pz0 = 17.4, -FZ - 5.6
FS.prism_xz(K.ngon(px0, pz0, 0.35, 8), 0.0, 18.6, GREY)
for y in (15.6, 17.4):
    FS.box(px0 - 2.0, px0 + 1.0, y, y + 0.25, pz0 - 0.15, pz0 + 0.15, GREY)
FS.prism_xz(K.ngon(px0 + 0.8, pz0, 0.6, 10), 12.0, 14.2, WHITE2)
for x in (px0 - 1.8, px0 - 0.6):
    D.chain(FS, (x, 17.6, pz0), (x - 6.0, 16.6, -FZ - 0.9), 6, 0.05, DARK, sag=0.6)
# нобори, велосипеды
for k, x in enumerate((-4.4, -1.4, 1.6)):
    nobori(FS, x, -FZ - 4.2, (RED, BLUE, GREEN)[k], WHITE)
bicycle(FS, 6.0, -FZ - 4.6, BLUE)
bicycle(FS, 6.4, -FZ - 6.0, PINK)
# правый бок: наружная лестница в квартиры
for k in range(12):
    y, z = 0.9 * k, -12.0 + 1.3 * k
    FS.box(FX + 1.0, FX + 2.6, y, y + 0.15, z - 0.4, z + 0.4, GREY)
beam(FS, (FX + 2.6, 1.0, -12.0), (FX + 2.6, 11.4, 2.4), 0.08, 0.08, DARK)
FS.box(FX + 0.9, FX + 2.8, 10.6, 10.8, 2.4, 6.0, GREY)
# тыл: мусорный контейнер
FS.box(-12.0, -8.0, 0.0, 2.6, FZ + 1.0, FZ + 3.0, GREEN)

# ══ ИНТЕРЬЕР: магазин ═════════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.0
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "E8ECEE")
for k in range(-8, 9):
    IQ.box(2.0 * k - 0.04, 2.0 * k + 0.04, 0.02, 0.04, ZF, ZB, "C8CED2")
    IQ.box(-W, W, 0.02, 0.04, 2.0 * k - 0.04, 2.0 * k + 0.04, "C8CED2")
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, WHITE)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 0.6, GREY)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, WHITE)
    for k, col in enumerate((GREEN, ORANGE, BLUE)):
        slab(IS, axis, fixed, out, 1.0, -half, half, 13.0 + 0.6 * k, 13.6 + 0.6 * k, col)
# холодильники со стеклянными дверцами по левой стене
for k in range(6):
    z = -13.0 + 3.2 * k
    IR.box(-W + 0.88, -W + 1.2, 0.0, 9.0, z - 1.55, z + 1.55, WHITE2)
    IG.box(-W + 1.2, -W + 1.24, 0.8, 8.4, z - 1.4, z + 1.4, "CFE6FF")
    IS.box(-W + 1.2, -W + 2.8, 0.0, 0.8, z - 1.55, z + 1.55, WHITE2)
    IS.box(-W + 1.2, -W + 2.8, 8.4, 9.0, z - 1.55, z + 1.55, WHITE2)
    for e in (-1, 1):
        IS.box(-W + 1.2, -W + 2.8, 0.8, 8.4, z + e * 1.5 - 0.06, z + e * 1.5 + 0.06, GREY)
    IS.box(-W + 2.7, -W + 2.8, 0.8, 8.4, z - 0.04, z + 0.04, GREY)
    for r in range(4):
        y = 1.0 + 1.9 * r
        IS.box(-W + 1.24, -W + 2.5, y - 0.1, y, z - 1.44, z + 1.44, "B8C8D4")
        for i in range(5):
            zz = z - 1.1 + 0.55 * i
            IS.prism_xz(K.ngon(-W + 1.9, zz, 0.2, 6), y, y + 1.1, GOODS[(i + r + k) % 8])
    IS.box(-W + 2.8, -W + 2.92, 4.0, 5.6, z + 0.2, z + 0.32, GREY)
# полки с яркими пачками по правой стене
for k in range(4):
    z = -13.0 + 4.0 * k
    IR.box(W - 1.2, W - 0.88, 0.0, 7.6, z - 1.9, z + 1.9, WHITE2)
    IS.box(W - 2.6, W - 1.2, 0.0, 0.6, z - 1.9, z + 1.9, WHITE2)
    for e in (-1, 1):
        IS.box(W - 2.6, W - 1.2, 0.0, 7.6, z + e * 1.85 - 0.08, z + e * 1.85 + 0.08, WHITE2)
    for r in range(4):
        y = 0.8 + 1.7 * r
        IS.box(W - 2.6, W - 0.88, y - 0.12, y, z - 1.9, z + 1.9, GREY)
        for i in range(5):
            zz = z - 1.5 + 0.75 * i
            IS.box(W - 2.4, W - 1.3, y, y + 1.0 + 0.3 * ((i + r) % 2), zz - 0.3, zz + 0.3, GOODS[(i * 3 + r + k) % 8])
# стеллажи-островки
for x in (-8.0, 8.0):
    IR.box(x - 1.2, x + 1.2, 0.0, 3.2, -13.0, -4.0, WHITE2)
    IS.box(x - 1.3, x + 1.3, 3.2, 3.4, -13.1, -3.9, GREY)
    for s in (-1, 1):
        for r in range(2):
            y = 0.6 + 1.3 * r
            for i in range(7):
                zz = -12.4 + 1.2 * i
                IS.box(*sorted((x + s * 1.2, x + s * 1.5)), y, y + 0.9, zz - 0.45, zz + 0.45, GOODS[(i + r + (s > 0)) % 8])
# касса, горячая витрина, кофемашина, светящееся меню у дальней стены
IR.box(-7.0, 7.0, 0.0, 3.4, ZF + 2.4, ZF + 4.4, WHITE2)
IS.box(-7.2, 7.2, 3.4, 3.6, ZF + 2.2, ZF + 4.6, GREY)
for x in (-4.6, 4.6):
    IS.box(x - 0.8, x + 0.8, 3.6, 4.2, ZF + 2.8, ZF + 3.8, DARK)
    IS.loft([(x - 0.7, 4.2, ZF + 3.2), (x + 0.7, 4.2, ZF + 3.2), (x + 0.7, 4.2, ZF + 3.6), (x - 0.7, 4.2, ZF + 3.6)],
            [(x - 0.7, 5.2, ZF + 3.0), (x + 0.7, 5.2, ZF + 3.0), (x + 0.7, 5.2, ZF + 3.3), (x - 0.7, 5.2, ZF + 3.3)], DARK)
    IG.box(x - 0.6, x + 0.6, 4.6, 5.0, ZF + 3.33, ZF + 3.36, "6AE8FF")
IG.box(-2.4, 1.6, 3.6, 5.6, ZF + 2.6, ZF + 4.2, "FFC880")
for i in range(4):
    IS.prism_xz(K.octa(-1.8 + 1.1 * i, ZF + 3.4, 0.4, 0.3, 0.12), 3.8, 4.3, ("E8A040", "F0D070", "C86A30", "F0D070")[i])
IS.box(2.4, 3.6, 3.6, 5.8, ZF + 2.6, ZF + 3.8, DARK)
IG.box(2.6, 3.4, 4.8, 5.4, ZF + 3.8, ZF + 3.84, "FF8A5A")
for k in range(6):  # меню-картинки: онигири, миски, напитки
    x = -10.0 + 4.0 * k
    IS.box(x - 1.8, x + 1.8, 8.6, 11.6, ZF + 0.88, ZF + 1.1, DARK)
    IG.box(x - 1.6, x + 1.6, 8.8, 11.4, ZF + 1.1, ZF + 1.14, ("FFF4D8", "FFE0E8", "E0F4FF")[k % 3])
    kind = k % 3
    if kind == 0:
        IS.prism_xy([(x - 1.0, 9.3), (x + 1.0, 9.3), (x, 10.9)], ZF + 1.14, ZF + 1.2, WHITE)
        IS.prism_xy(K.rect(x - 0.6, x + 0.6, 9.3, 9.9), ZF + 1.2, ZF + 1.24, DARK)
    elif kind == 1:
        IS.prism_xy([(x - 1.2, 10.2), (x + 1.2, 10.2), (x + 0.8, 9.3), (x - 0.8, 9.3)], ZF + 1.14, ZF + 1.2, RED)
        IS.prism_xy(K.octa(x, 10.4, 1.0, 0.4, 0.2), ZF + 1.14, ZF + 1.18, "F0D070")
    else:
        IS.prism_xy(K.rect(x - 0.5, x + 0.5, 9.2, 10.9), ZF + 1.14, ZF + 1.2, BLUE)
        IS.prism_xy(K.rect(x - 0.5, x + 0.5, 9.9, 10.3), ZF + 1.2, ZF + 1.24, WHITE)
# капсульные автоматы и журналы у лифта
for k in range(4):
    x = 9.6 + 1.6 * k
    IS.box(x - 0.7, x + 0.7, 0.0, 2.4, 9.0, 10.4, (RED, BLUE, YELLOW, GREEN)[k])
    IG.box(x - 0.6, x + 0.6, 2.4, 4.0, 9.1, 10.3, "E8F4FF")
    for i in range(4):
        IS.prism_xz(K.ngon(x - 0.3 + 0.6 * (i % 2), 9.45 + 0.5 * (i // 2), 0.22, 6), 2.45, 2.85, GOODS[(i + k * 2) % 8])
    IS.box(x - 0.75, x + 0.75, 4.0, 4.3, 8.95, 10.45, (RED, BLUE, YELLOW, GREEN)[k])
IS.box(-14.0, -10.0, 0.0, 4.0, 12.6, 13.4, GREY)
for r in range(3):
    for i in range(4):
        IS.box(-13.8 + 1.0 * i, -13.0 + 1.0 * i, 0.6 + 1.2 * r, 1.7 + 1.2 * r, 12.4, 12.6, GOODS[(i + r * 3) % 8])
# светлые панели на потолке
for i in range(-2, 3):
    for j in range(-2, 3):
        IG.box(6.2 * i - 1.6, 6.2 * i + 1.6, C - 0.1, C - 0.04, 6.0 * j - 0.8, 6.0 * j + 0.8, "F4FAFF")
# тёмный восьмиугольный помост с жёлтой лентой
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.2, 8, turn=0.5), 0.0, 0.5, NAVY)
IG.prism_xz(K.ngon(px, pz, 4.25, 8, turn=0.5), 0.5, 0.7, YELLOW)
IS.prism_xz(K.ngon(px, pz, 3.9, 8, turn=0.5), 0.7, TOP, NAVY)
for k in range(8):
    t = 2 * math.pi * k / 8
    IS.box(px + 3.0 * math.cos(t) - 0.4, px + 3.0 * math.cos(t) + 0.4, TOP, TOP + 0.03, pz + 3.0 * math.sin(t) - 0.4,
           pz + 3.0 * math.sin(t) + 0.4, GREY)
B.lift_leaves(IS, GREY, GREEN)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 10.8, -FZ, FZ, WHITE)
SL.box(-FX, FX, 10.8, 18.9, -FZ, FZ, TILE)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, ASPH)
SL.box(-FX - 0.3, FX + 0.3, 8.4, 10.5, -FZ - 0.3, FZ + 0.3, ORANGE)
SL.box(-6.0, 9.6, 1.0, 7.8, -FZ - 0.4, -FZ, GLASS)
for k, (x, col) in enumerate(((-16.2, RED), (-13.9, BLUE), (-11.6, WHITE), (-9.3, YELLOW))):
    SL.box(x - 1.05, x + 1.05, 0.0, 4.6, -FZ - 2.8, -FZ, col)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 2800, (1.0, 1.0, 1.0)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.98, 0.95)),
                                                   ("Fridge", (-12, 6, -3), 700, (0.8, 0.9, 1.0))])
