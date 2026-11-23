"""Этаж «Королевский крысовоз» музея-небоскрёба (шестая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — королевская лавка игрушек. Снаружи — кремовый фасад с пилястрами в красно-белую «карамельную»
полоску, слева — широкий выступающий эркер-витрина с игрушками на подоконнике (кубики, юла, ракета, мяч, кораблик),
дверь со стеклом, справа — пирамида из огромных кубиков со звездой, сердцем и кругом, над всем — полосатая
маркиза с фестонами; выше по всему фасаду идёт полка-эстакада с игрушечной железной дорогой: красный паровозик
с вагончиками въезжает в тоннель; на парапете — золотая корона с самоцветами, у двери — связка воздушных шаров;
на боку — гигантский заводной ключ и арочные окна со ставнями. Внутри — лавка: дощатый пол и круглый пёстрый ковёр,
вокруг постамента — кольцо рельсов с паровозиком, по стенам — полки с игрушками, у дальней стены — стена-ячейки
с коробками и короной, лошадка-качалка, кукольный домик, огромные карандаши, коробки-подарки, под потолком —
воздушные змеи и подвеска со звёздами и планетами; экспонат — на круглом мятном постаменте-шкатулке
с золотой каймой и красно-белой лентой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_toyshop.py -- <репо> <превью>
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

RED, CREAM, CREAM2, MINT, SKY, YELLOW = "E8404A", "FFF0D8", "F2DEC0", "7AD8B8", "6AB8F0", "FFD03A"
PURPLE, PINK, GOLD, WOOD, WOOD2, DARK = "9A6AE0", "FF8AC0", "E8B840", "B07A48", "8A5A34", "3A2E3A"
WHITE, GREEN, BLUE, ORANGE = "FFFFFF", "5AC86A", "3A7AE8", "F59A3A"
TOYS = (RED, SKY, YELLOW, GREEN, PURPLE, PINK, ORANGE, MINT)

F = B.Floor("TS", "RoyalRatTrain", quiet=("C8A070", WOOD2, MINT), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def star(cx, cy, r, inner=0.45):
    return [(cx + r * (1.0 if i % 2 == 0 else inner) * math.cos(math.pi / 2 + i * math.pi / 5),
             cy + r * (1.0 if i % 2 == 0 else inner) * math.sin(math.pi / 2 + i * math.pi / 5)) for i in range(10)]


def block(p, x, y, z, s, col, sym, face=-1):
    """Кубик-игрушка: куб, рамка-кант, символ (звезда / сердце / круг / треугольник) на грани face (по z)."""
    p.box(x - s / 2, x + s / 2, y, y + s, z - s / 2, z + s / 2, col)
    zf = z + face * s / 2
    lo, hi = sorted((zf, zf + face * 0.06))
    p.frame_xy(K.rect(x - s / 2, x + s / 2, y, y + s), K.rect(x - s * 0.4, x + s * 0.4, y + s * 0.1, y + s * 0.9), lo, hi, WHITE)
    lo2, hi2 = sorted((zf, zf + face * 0.08))
    cy = y + s / 2
    if sym == 0:
        p.prism_xy(star(x, cy, s * 0.3), lo2, hi2, WHITE)
    elif sym == 1:
        p.prism_xy([(x, cy - s * 0.28), (x + s * 0.3, cy + s * 0.02), (x + s * 0.18, cy + s * 0.2), (x, cy + s * 0.08),
                    (x - s * 0.18, cy + s * 0.2), (x - s * 0.3, cy + s * 0.02)], lo2, hi2, WHITE)
    elif sym == 2:
        p.prism_xy(K.ngon(x, cy, s * 0.26, 10), lo2, hi2, WHITE)
    else:
        p.prism_xy([(x - s * 0.28, cy - s * 0.22), (x + s * 0.28, cy - s * 0.22), (x, cy + s * 0.26)], lo2, hi2, WHITE)


def loco(p, g, x, y, z, s=1.0, along_x=True, col=RED):
    """Игрушечный паровозик: котёл, будка, труба, колёса, фонарь (вдоль x или z, нос — в +)."""
    if along_x:
        p.box(x - 1.4 * s, x + 0.6 * s, y + 0.4 * s, y + 1.3 * s, z - 0.5 * s, z + 0.5 * s, col)
        p.prism_zy(K.ngon(z, y + 1.0 * s, 0.5 * s, 8), x - 0.4 * s, x + 1.2 * s, DARK)
        p.box(x - 1.4 * s, x - 0.4 * s, y + 1.3 * s, y + 2.1 * s, z - 0.55 * s, z + 0.55 * s, col)
        p.box(x - 1.5 * s, x - 0.3 * s, y + 2.1 * s, y + 2.3 * s, z - 0.65 * s, z + 0.65 * s, GOLD)
        p.prism_xz(K.ngon(x + 0.8 * s, z, 0.22 * s, 6), y + 1.4 * s, y + 2.1 * s, DARK)
        p.prism_xz(K.ngon(x + 0.8 * s, z, 0.32 * s, 6), y + 2.1 * s, y + 2.3 * s, GOLD)
        g.prism_zy(K.ngon(z, y + 1.0 * s, 0.18 * s, 6), x + 1.2 * s, x + 1.26 * s, "FFE8A0")
        for k, xx in enumerate((-1.0, -0.2, 0.6)):
            for e in (-1, 1):
                p.prism_xy(K.ngon(x + xx * s, y + 0.35 * s, 0.32 * s, 8), z + e * 0.5 * s - 0.08 * s, z + e * 0.5 * s + 0.08 * s, GOLD)
    else:
        p.box(x - 0.5 * s, x + 0.5 * s, y + 0.4 * s, y + 1.3 * s, z - 1.4 * s, z + 0.6 * s, col)
        p.prism_xy(K.ngon(x, y + 1.0 * s, 0.5 * s, 8), z - 0.4 * s, z + 1.2 * s, DARK)
        p.box(x - 0.55 * s, x + 0.55 * s, y + 1.3 * s, y + 2.1 * s, z - 1.4 * s, z - 0.4 * s, col)
        p.prism_xz(K.ngon(x, z + 0.8 * s, 0.22 * s, 6), y + 1.4 * s, y + 2.1 * s, DARK)
        for zz in (-1.0, -0.2, 0.6):
            for e in (-1, 1):
                p.prism_zy(K.ngon(z + zz * s, y + 0.35 * s, 0.32 * s, 8), x + e * 0.5 * s - 0.08 * s, x + e * 0.5 * s + 0.08 * s, GOLD)


def wagon(p, x, y, z, s, col):
    """Открытый вагончик с кубиками (вдоль x)."""
    p.box(x - 0.9 * s, x + 0.9 * s, y + 0.4 * s, y + 1.2 * s, z - 0.5 * s, z + 0.5 * s, col)
    for k in range(2):
        p.box(x - 0.6 * s + 0.7 * k * s, x - 0.1 * s + 0.7 * k * s, y + 1.2 * s, y + 1.7 * s, z - 0.25 * s, z + 0.25 * s, TOYS[(k + 2) % 8])
    for xx in (-0.5, 0.5):
        for e in (-1, 1):
            p.prism_xy(K.ngon(x + xx * s, y + 0.35 * s, 0.3 * s, 8), z + e * 0.5 * s - 0.08 * s, z + e * 0.5 * s + 0.08 * s, GOLD)


def candy_pilaster(p, axis, fixed, out, a, y0, y1, w=0.8):
    """Пилястра в красно-белую полоску."""
    n = int((y1 - y0) // 0.8)
    for k in range(n):
        slab(p, axis, fixed, out, 1.2, a - w / 2, a + w / 2, y0 + 0.8 * k, y0 + 0.8 * (k + 1), (RED, WHITE)[k % 2])


def balloon(p, x, y, z, col):
    p.prism_xz(K.octa(x, z, 0.6, 0.6, 0.25), y, y + 1.3, col)
    p.box(x - 0.02, x + 0.02, y - 3.0, y, z - 0.02, z + 0.02, DARK)


def crown(p, cx, cy, s, d0, d1, gems=True):
    """Корона: зубцы, обод, самоцветы (плоский профиль в xy)."""
    p.prism_xy([(cx - 2.0 * s, cy), (cx + 2.0 * s, cy), (cx + 2.0 * s, cy + 1.6 * s), (cx + 1.3 * s, cy + 0.9 * s), (cx + 0.7 * s, cy + 2.0 * s),
                (cx, cy + 1.0 * s), (cx - 0.7 * s, cy + 2.0 * s), (cx - 1.3 * s, cy + 0.9 * s), (cx - 2.0 * s, cy + 1.6 * s)], d0, d1, GOLD)
    p.prism_xy(K.rect(cx - 2.1 * s, cx + 2.1 * s, cy - 0.3 * s, cy + 0.3 * s), d0 - 0.05, d1 + 0.05, "C89028")
    if gems:
        for k, xx in enumerate((-1.3, 0.0, 1.3)):
            p.prism_xy(K.ngon(cx + xx * s, cy, 0.22 * s, 6), d0 - 0.1, d1 + 0.1, (RED, BLUE, GREEN)[k])
        for xx in (-2.0, -0.7, 0.7, 2.0):
            p.prism_xy(K.ngon(cx + xx * s, cy + (1.6 if abs(xx) > 1.5 else 2.0) * s, 0.2 * s, 8), d0 - 0.05, d1 + 0.05, WHITE)


# ══ ФАСАД: лавка игрушек ═════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, CREAM, CREAM, CREAM2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "C8A070")
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.0, MINT)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.0, 15.4, CREAM)
    for s in (-1, 1):
        candy_pilaster(FS, axis, fixed, out, s * (half - 0.5), 1.0, 15.4)
    slab(FR, axis, fixed, out, 1.88, -half - 0.5, half + 0.5, 15.4, 16.2, PINK)
    slab(FR, axis, fixed, out, 0.88, -half, half, 16.2, 18.9, CREAM2)
    slab(FR, axis, fixed, out, 1.3, -half - 0.2, half + 0.2, 18.4, 18.9, MINT)
    for k in range(int(2 * half // 2.0)):  # фестоны под карнизом
        a = -half + 1.0 + 2.0 * k
        pr = FS.prism_xy if axis == "z" else FS.prism_zy
        d0, d1 = sorted((fixed + out * 1.9, fixed + out * 2.0))
        pr([(a - 1.0, 15.4), (a + 1.0, 15.4), (a + 0.5, 14.9), (a, 14.75), (a - 0.5, 14.9)], d0, d1, (SKY, YELLOW, PURPLE)[k % 3])
    if axis == "x":  # бока: арочные окна со ставнями
        for k, z in enumerate((-8.0, 0.0, 8.0)):
            d = lambda v: fixed + out * v  # noqa: E731
            slab(FG, axis, fixed, out, 0.92, z - 1.4, z + 1.4, 5.0, 9.4, "FFE8C0")
            FS.frame_zy([(z - 1.7, 4.7), (z + 1.7, 4.7), (z + 1.7, 9.4), (z, 10.9), (z - 1.7, 9.4)],
                        [(z - 1.4, 5.0), (z + 1.4, 5.0), (z + 1.4, 9.3), (z, 10.5), (z - 1.4, 9.3)], *sorted((d(0.88), d(1.2))), WHITE)
            for e in (-1, 1):
                slab(FS, axis, fixed, out, 1.15, *sorted((z + e * 1.8, z + e * 3.0)), 5.0, 9.4, TOYS[(k + 3) % 8])
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# эркер-витрина слева с игрушками на подоконнике
FS.box(-15.4, -3.6, 1.0, 2.6, -FZ - 3.2, -FZ - 0.88, MINT)
FS.box(-15.6, -3.4, 2.6, 2.9, -FZ - 3.4, -FZ - 0.88, WHITE)
FG.box(-15.0, -4.0, 2.9, 8.6, -FZ - 1.0, -FZ - 0.94, "FFE8C8")
for x in (-15.4, -9.5, -3.6):
    FS.box(x - 0.2, x + 0.2, 2.9, 8.8, -FZ - 3.3, -FZ - 3.0, WHITE)
FS.box(-15.6, -3.4, 8.6, 9.2, -FZ - 3.4, -FZ - 0.88, WHITE)
for k, (x, sym) in enumerate(((-14.0, 0), (-12.6, 1))):
    block(FS, x, 2.9, -FZ - 2.0, 1.2, TOYS[k], sym)
block(FS, -13.3, 4.1, -FZ - 2.0, 1.2, TOYS[2], 2)
FS.cone([(-10.4 + 0.8 * math.cos(t), 3.6, -FZ - 2.0 + 0.8 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]], (-10.4, 2.9, -FZ - 2.0), PURPLE)
FS.cone([(-10.4 + 0.8 * math.cos(t), 3.6, -FZ - 2.0 + 0.8 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]], (-10.4, 4.4, -FZ - 2.0), YELLOW)
FS.prism_xz(K.ngon(-8.4, -FZ - 2.0, 0.35, 8), 2.9, 5.4, WHITE)  # ракета
FS.cone([(-8.4 + 0.35 * math.cos(t), 5.4, -FZ - 2.0 + 0.35 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]], (-8.4, 6.4, -FZ - 2.0), RED)
for e in (-1, 1):
    FS.prism_xy([(-8.4 + e * 0.35, 2.9), (-8.4 + e * 0.8, 2.9), (-8.4 + e * 0.35, 3.8)], -FZ - 2.05, -FZ - 1.95, RED)
FS.prism_xz(K.octa(-6.6, -FZ - 2.0, 0.7, 0.7, 0.3), 2.9, 4.3, BLUE)  # мяч
FS.box(-5.6, -4.0, 2.9, 3.4, -FZ - 2.4, -FZ - 1.6, WOOD)  # кораблик
FS.box(-4.85, -4.75, 3.4, 5.2, -FZ - 2.05, -FZ - 1.95, WOOD2)
FS.prism_xy([(-4.7, 3.6), (-4.7, 5.2), (-3.8, 3.6)], -FZ - 2.02, -FZ - 1.98, WHITE)
# дверь
FG.box(-1.2, 3.6, 1.0, 8.2, -FZ - 0.94, -FZ - 0.9, "FFE0A8")
FS.frame_xy(K.rect(-1.6, 4.0, 1.0, 8.6), K.rect(-1.2, 3.6, 1.0, 8.2), -FZ - 1.3, -FZ - 0.88, RED)
FS.box(-1.2, 3.6, 1.0, 3.6, -FZ - 1.0, -FZ - 0.92, RED)
FS.prism_xy(K.ngon(3.0, 4.6, 0.18, 6), -FZ - 1.1, -FZ - 1.0, GOLD)
for k, col in enumerate((RED, YELLOW, BLUE, GREEN, PINK)):  # шары у двери
    balloon(FS, 5.2 + 0.5 * math.cos(k * 1.3), 6.6 + 0.6 * (k % 3), -FZ - 1.8 + 0.5 * math.sin(k * 1.3), col)
# пирамида кубиков справа
for k, (x, y, sym) in enumerate(((8.6, 0.0, 0), (11.2, 0.0, 1), (13.8, 0.0, 2), (16.4, 0.0, 3), (9.9, 2.5, 2), (12.5, 2.5, 0),
                                  (15.1, 2.5, 1), (11.2, 5.0, 3), (13.8, 5.0, 0))):
    block(FS, x, y, -FZ - 2.2, 2.4, TOYS[(k * 3) % 8], sym)
# маркиза над эркером и дверью
for k in range(11):
    x0 = -15.8 + 2.0 * k
    col = (RED, WHITE)[k % 2]
    FS.loft([(x0, 10.0, -FZ - 0.9), (x0 + 2.0, 10.0, -FZ - 0.9), (x0 + 2.0, 10.1, -FZ - 0.9), (x0, 10.1, -FZ - 0.9)],
            [(x0, 9.2, -FZ - 4.0), (x0 + 2.0, 9.2, -FZ - 4.0), (x0 + 2.0, 9.3, -FZ - 4.0), (x0, 9.3, -FZ - 4.0)], col)
    FS.prism_xy([(x0, 9.25), (x0 + 2.0, 9.25), (x0 + 1.6, 8.8), (x0 + 1.0, 8.65), (x0 + 0.4, 8.8)], -FZ - 4.05, -FZ - 3.95, col)
# полка-эстакада с железной дорогой и тоннелем
FS.box(-FX - 0.4, FX + 0.4, 11.4, 11.9, -FZ - 2.6, -FZ - 0.88, WOOD)
for k in range(9):
    x = -16.0 + 4.0 * k
    FS.prism_zy([(-FZ - 0.88, 11.4), (-FZ - 2.4, 11.4), (-FZ - 0.88, 10.0)], x - 0.15, x + 0.15, WOOD2)
for e in (-0.5, 0.5):
    FS.box(-FX, FX, 11.9, 12.0, -FZ - 1.8 + e - 0.06, -FZ - 1.8 + e + 0.06, "8A8E92")
for k in range(24):
    x = -FX + 0.5 + 1.5 * k
    FS.box(x - 0.15, x + 0.15, 11.9, 11.95, -FZ - 2.5, -FZ - 1.1, WOOD2)
loco(FS, FG, -3.0, 11.95, -FZ - 1.8, 1.0, True)
for k, col in enumerate((SKY, YELLOW)):
    wagon(FS, -5.6 - 2.1 * k, 11.95, -FZ - 1.8, 1.0, col)
FS.box(11.6, 16.6, 11.9, 14.6, -FZ - 2.6, -FZ - 0.88, GREEN)  # тоннель-горка
FS.frame_xy([(12.2, 11.9), (14.4, 11.9), (14.4, 13.2), (13.3, 13.9), (12.2, 13.2)],
            [(12.6, 11.9), (14.0, 11.9), (14.0, 13.0), (13.3, 13.5), (12.6, 13.0)], -FZ - 2.7, -FZ - 2.6, "8A8E92")
FS.prism_xy([(12.6, 11.9), (14.0, 11.9), (14.0, 13.0), (13.3, 13.5), (12.6, 13.0)], -FZ - 2.62, -FZ - 2.6, DARK)
FS.prism_xz(K.octa(14.6, -FZ - 1.7, 1.2, 0.8, 0.4), 14.6, 15.2, "4AA85A")
# гирлянды флажков между пилястрами
for x0, x1 in ((-17.4, -6.0), (-6.0, 6.0), (6.0, 17.4)):
    pts = D.chain(FS, (x0, 14.6, -FZ - 1.0), (x1, 14.6, -FZ - 1.0), 8, 0.05, DARK, sag=0.9)
    for i, (x, y, z) in enumerate(pts[1:-1]):
        FS.prism_xy([(x - 0.45, y), (x + 0.45, y), (x, y - 0.9)], z - 0.04, z + 0.04, TOYS[(i + int(x0)) % 8])
# корона на парапете
crown(FS, 0.0, 16.2, 1.25, -FZ - 1.8, -FZ - 1.5)
# правый бок: гигантский заводной ключ
kz = 2.0
FS.prism_zy(K.ngon(kz, 9.0, 0.5, 8), FX + 0.88, FX + 3.6, GOLD)
for e in (-1, 1):
    FS.frame_zy(K.ngon(kz + e * 1.6, 9.0, 1.5, 10), K.ngon(kz + e * 1.6, 9.0, 0.8, 10), FX + 3.4, FX + 3.9, GOLD)
FS.prism_zy(K.ngon(kz, 9.0, 0.8, 8), FX + 3.2, FX + 3.5, "C89028")

# ══ ИНТЕРЬЕР: лавка ═══════════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "C8A070")
for k in range(-13, 14):
    if k % 2:
        IQ.box(1.25 * k + 0.03, 1.25 * k + 1.22, 0.02, 0.04, ZF, ZB, "B8905E")
for k in range(16):  # круглый пёстрый ковёр
    t0, t1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
    for r0, r1, off in ((4.8, 6.6, 0), (6.6, 7.2, 1)):
        IQ.prism_xz([(r0 * math.cos(t0), -3.0 + r0 * math.sin(t0)), (r1 * math.cos(t0), -3.0 + r1 * math.sin(t0)),
                     (r1 * math.cos(t1), -3.0 + r1 * math.sin(t1)), (r0 * math.cos(t1), -3.0 + r0 * math.sin(t1))], 0.04, 0.06,
                    TOYS[(k + off * 3) % 8] if off == 0 else WHITE)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, CREAM)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 3.6, WOOD)
        slab(IR, axis, fixed, out, 1.1, a0, a1, 3.6, 3.9, WHITE)
        for k in range(int((a1 - a0) // 2.4)):  # мятные полосы обоев
            a = a0 + 0.6 + 2.4 * k
            slab(IS, axis, fixed, out, 0.94, a, a + 1.0, 3.9, 14.6 if not gap else DOOR[1], MINT)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, CREAM)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, RED)
    slab(IR, axis, fixed, out, 1.4, -half, half, 14.6, 15.2, PINK)
# полки с игрушками по боковым стенам
for s in (-1, 1):
    for r in range(3):
        y = 5.0 + 2.6 * r
        IS.box(*sorted((s * (W - 2.2), s * (W - 0.88))), y - 0.2, y, -13.0, 2.0, WOOD2)
        for k in range(7):
            z = -12.2 + 2.1 * k
            x = s * (W - 1.6)
            kind = (k + r + (s > 0)) % 5
            col = TOYS[(k * 3 + r) % 8]
            if kind == 0:
                IS.box(x - 0.5, x + 0.5, y, y + 1.0, z - 0.5, z + 0.5, col)
                IS.box(x - 0.3, x + 0.3, y + 1.0, y + 1.6, z - 0.3, z + 0.3, TOYS[(k + 5) % 8])
            elif kind == 1:
                IS.prism_xz(K.octa(x, z, 0.6, 0.6, 0.25), y, y + 1.2, col)
            elif kind == 2:
                IS.prism_xz(K.ngon(x, z, 0.6, 10), y, y + 0.9, col)
                IS.prism_xz(K.ngon(x, z, 0.62, 10), y + 0.9, y + 1.0, WHITE)
            elif kind == 3:
                IS.box(x - 0.4, x + 0.4, y + 0.3, y + 0.9, z - 0.9, z + 0.9, col)
                for e in (-1, 1):
                    IS.prism_zy(K.ngon(z + e * 0.55, y + 0.25, 0.25, 8), x - 0.45, x + 0.45, DARK)
            else:
                IS.prism_xz(K.ngon(x, z, 0.28, 8), y, y + 1.6, WHITE)
                IS.cone([(x + 0.28 * math.cos(t), y + 1.6, z + 0.28 * math.sin(t)) for t in [2 * math.pi * i / 8 for i in range(8)]],
                        (x, y + 2.2, z), col)
# стена-ячейки у дальней стены с коробками и короной
IR.box(-10.0, 10.0, 0.0, 12.0, ZF + 0.88, ZF + 2.4, WOOD)
for i in range(5):
    for j in range(4):
        x0, y0 = -9.6 + 3.9 * i, 0.4 + 2.9 * j
        IS.box(x0, x0 + 3.5, y0, y0 + 2.6, ZF + 2.4, ZF + 2.44, "8A5A34")
        IS.box(x0 + 0.4, x0 + 3.1, y0, y0 + 1.6 + 0.6 * ((i + j) % 2), ZF + 1.4, ZF + 2.38, TOYS[(i * 2 + j * 3) % 8])
        IS.box(x0 + 1.6, x0 + 1.9, y0, y0 + 1.62 + 0.6 * ((i + j) % 2), ZF + 2.38, ZF + 2.42, WHITE)
crown(IS, 0.0, 13.0, 1.4, ZF + 1.2, ZF + 1.5)
# кольцо рельсов с паровозиком вокруг постамента
for r in (5.1, 5.9):
    ring_y(IS, 0.0, -3.0, r - 0.08, r + 0.08, 0.06, 0.24, "8A8E92", n=28)
for k in range(14):
    t = 2 * math.pi * (2 * k + 1) / 28
    IS.box(5.5 * math.cos(t) - 0.6, 5.5 * math.cos(t) + 0.6, 0.06, 0.14, -3.0 + 5.5 * math.sin(t) - 0.6, -3.0 + 5.5 * math.sin(t) + 0.6, WOOD2)
loco(IS, IG, -5.5, 0.2, -3.0, 0.9, along_x=False, col=BLUE)
# лошадка-качалка, кукольный домик, карандаши, подарки
hx, hz = 11.2, 6.0
IS.prism_zy([(hz - 2.6, 0.6), (hz - 1.2, 0.0), (hz + 1.2, 0.0), (hz + 2.6, 0.6), (hz + 2.6, 0.75), (hz + 1.2, 0.2), (hz - 1.2, 0.2), (hz - 2.6, 0.75)],
            hx - 0.9, hx + 0.9, RED)
for e in (-1, 1):
    for f in (-1, 1):
        beam(IS, (hx + e * 0.6, 0.2, hz + f * 1.2), (hx + e * 0.4, 1.8, hz + f * 0.8), 0.3, 0.3, WHITE)
IS.box(hx - 0.6, hx + 0.6, 1.8, 3.0, hz - 1.2, hz + 1.2, WHITE)
IS.box(hx - 0.65, hx + 0.65, 2.6, 3.05, hz - 0.5, hz + 0.3, RED)
beam(IS, (hx, 2.8, hz - 1.0), (hx, 4.2, hz - 1.9), 0.7, 0.7, WHITE)
IS.box(hx - 0.45, hx + 0.45, 3.9, 4.6, hz - 2.9, hz - 1.6, WHITE)
IS.box(hx - 0.2, hx + 0.2, 3.0, 4.8, hz - 1.5, hz - 0.8, PURPLE)
dx, dz = -12.4, -12.6
IS.box(dx - 2.0, dx + 2.0, 0.0, 5.0, dz - 1.6, dz + 1.6, PINK)
IS.prism_xy([(dx - 2.4, 5.0), (dx + 2.4, 5.0), (dx, 7.4)], dz - 1.8, dz + 1.8, PURPLE)
for i in range(2):
    for j in range(2):
        IG.box(dx - 1.5 + 1.8 * i, dx - 0.3 + 1.8 * i, 0.8 + 2.2 * j, 2.0 + 2.2 * j, dz + 1.6, dz + 1.64, "FFE8C0")
for k, col in enumerate((RED, BLUE, YELLOW, GREEN)):
    x = 13.4 + 0.9 * k
    IS.prism_xz(K.ngon(x, -14.4, 0.4, 6), 0.0, 7.0 - 0.8 * k, col)
    IS.cone([(x + 0.4 * math.cos(t), 7.0 - 0.8 * k, -14.4 + 0.4 * math.sin(t)) for t in [2 * math.pi * i / 6 for i in range(6)]],
            (x, 8.0 - 0.8 * k, -14.4), "E8C8A0")
for k, (x, z, s, col) in enumerate(((-13.0, 9.0, 2.2, SKY), (-11.0, 8.4, 1.6, PINK), (-12.4, 8.8, 1.2, YELLOW))):
    y = 0.0 if k < 2 else 2.2
    IS.box(x - s / 2, x + s / 2, y, y + s, z - s / 2, z + s / 2, col)
    IS.box(x - 0.15, x + 0.15, y, y + s + 0.02, z - s / 2 - 0.02, z + s / 2 + 0.02, WHITE)
    IS.box(x - s / 2 - 0.02, x + s / 2 + 0.02, y, y + s + 0.02, z - 0.15, z + 0.15, WHITE)
# воздушные змеи и подвеска со звёздами
for k, (x, z) in enumerate(((-8.0, -9.0), (8.0, 3.0))):
    IS.prism_xy([(x, 15.4), (x + 1.4, 14.0), (x, 11.8), (x - 1.4, 14.0)], z - 0.05, z + 0.05, (YELLOW, SKY)[k])
    IS.box(x - 0.02, x + 0.02, 15.4, C, z - 0.02, z + 0.02, DARK)
    for i in range(4):
        IS.prism_xy([(x - 0.3, 11.4 - 0.9 * i), (x + 0.3, 11.4 - 0.9 * i), (x, 11.0 - 0.9 * i)], z - 0.04, z + 0.04, TOYS[(i + k) % 8])
mx, mz = 0.0, -3.0
IS.box(mx - 3.4, mx + 3.4, 14.6, 14.75, mz - 0.06, mz + 0.06, WOOD2)
IS.box(mx - 0.06, mx + 0.06, 14.6, 14.75, mz - 3.4, mz + 3.4, WOOD2)
IS.box(mx - 0.03, mx + 0.03, 14.75, C, mz - 0.03, mz + 0.03, DARK)
for k, (x, z) in enumerate(((mx - 3.2, mz), (mx + 3.2, mz), (mx, mz - 3.2), (mx, mz + 3.2))):
    IS.box(x - 0.02, x + 0.02, 13.2, 14.6, z - 0.02, z + 0.02, DARK)
    if k % 2:
        IS.prism_xy(star(x, 12.7, 0.6), z - 0.06, z + 0.06, YELLOW)
    else:
        IS.prism_xz(K.octa(x, z, 0.55, 0.55, 0.22), 12.1, 13.2, (BLUE, ORANGE)[k // 2])
# мятный постамент-шкатулка
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.1, 16), 0.0, 0.5, MINT)
IS.prism_xz(K.ngon(px, pz, 4.2, 16), 0.5, 0.62, GOLD)
for k in range(16):
    t0, t1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
    IS.prism_xz([(px + 3.7 * math.cos(t0), pz + 3.7 * math.sin(t0)), (px + 3.85 * math.cos(t0), pz + 3.85 * math.sin(t0)),
                 (px + 3.85 * math.cos(t1), pz + 3.85 * math.sin(t1)), (px + 3.7 * math.cos(t1), pz + 3.7 * math.sin(t1))],
                0.62, TOP - 0.12, (RED, WHITE)[k % 2])
IS.prism_xz(K.ngon(px, pz, 3.7, 16), 0.62, TOP - 0.12, "5AC0A0")
IS.prism_xz(K.ngon(px, pz, 3.95, 16), TOP - 0.12, TOP, GOLD)
B.lift_leaves(IS, WOOD2, RED)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, CREAM)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "C8A070")
SL.box(-FX - 0.5, FX + 0.5, 15.4, 16.2, -FZ - 0.5, FZ + 0.5, PINK)
SL.box(-15.6, -3.4, 1.0, 9.2, -FZ - 3.4, -FZ, MINT)
SL.box(-15.8, 6.2, 8.6, 10.1, -FZ - 4.0, -FZ, RED)
SL.box(7.4, 17.6, 0.0, 6.2, -FZ - 3.4, -FZ, YELLOW)
SL.box(-FX, FX, 11.4, 12.0, -FZ - 2.6, -FZ, WOOD)
SL.prism_xy([(-2.5, 16.2), (2.5, 16.2), (2.5, 18.2), (0.0, 17.4), (-2.5, 18.2)], -FZ - 1.8, -FZ, GOLD)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 2600, (1.0, 0.95, 0.88)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.97, 0.9)),
                                                   ("Warm", (-10, 6, 6), 700, (1.0, 0.85, 0.7))])
