"""Этаж «Антилопа-родник» музея-небоскрёба (восьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — курортная галерея минеральных источников. Снаружи — мятные стены с белыми пилястрами и карнизом,
внизу — открытая аркада на белых колоннах вдоль фасада, наверху — высокие окна с полукруглым верхом и балюстрада
по парапету; в центре — выступающая ротонда-беседка: полукруг колонн под куполом, в ней — каменная чаша родника с
бьющей водой; перед галереей — чугунные фонари, скамейки, клумбы с цветами и пальмы в кадках. Внутри — бювет:
пол мозаикой, по стенам — глухие арки и ряд латунных краников над раковинами, кольцо из колонн вокруг постамента
(со стороны лифта проход открыт), над ним — кессонный купол-кольцо со световым фонарём, пальмы, скамьи;
экспонат — на круглой мраморной чаше со светящейся водой и листьями кувшинок.
Запуск: blender --background --factory-startup --python scripts/blender/floor_spa.py -- <репо> <превью>
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

MINT, MINT2, WHITE, MARBLE, MARBLE2, AQUA = "8ED8C4", "6EC0AA", "F4F4EE", "E8E4DA", "CFC8BA", "4AD8E8"
AQUA2, BRASS, IRON, LEAF, LEAF2, GLASS = "9AF0F4", "C8982E", "2E3A3A", "3A9A4A", "2A7A3A", "FFF0C8"
FLOWERS = ("E8483A", "F0C020", "E870B0", "8A5AE0")

F = B.Floor("SP", "SpringAntelope", quiet=(MARBLE2, "C8C0B0", "B8E0D4"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def arch(a, y0, y1, w, n=5):
    """Контур проёма с полукруглым верхом (y1 — пята)."""
    return [(a - w, y0), (a + w, y0)] + [(a + w * math.cos(math.pi * k / n), y1 + w * math.sin(math.pi * k / n)) for k in range(n + 1)]


def band(p, plane, outer, inner, d0, d1, col):
    """Арка без нижней перемычки (контуры одной длины)."""
    for i in range(1, len(outer)):
        j = (i + 1) % len(outer)
        (p.prism_xy if plane == "xy" else p.prism_zy)([outer[i], outer[j], inner[j], inner[i]], d0, d1, col)


def column(p, x, z, y0, y1, r=0.5):
    """Белая колонна: база, ствол, капитель."""
    p.box(x - r * 1.4, x + r * 1.4, y0, y0 + 0.4, z - r * 1.4, z + r * 1.4, MARBLE2)
    p.prism_xz(K.ngon(x, z, r, 10), y0 + 0.4, y1 - 0.5, WHITE)
    p.prism_xz(K.ngon(x, z, r * 1.2, 10), y1 - 0.5, y1 - 0.3, WHITE)
    p.box(x - r * 1.5, x + r * 1.5, y1 - 0.3, y1, z - r * 1.5, z + r * 1.5, MARBLE)


def lamp_post(p, g, x, z, y=0.0, h=4.4):
    """Чугунный фонарь: столб с кольцами, кронштейн, светящийся колпак."""
    p.prism_xz(K.ngon(x, z, 0.35, 8), y, y + 0.5, IRON)
    p.prism_xz(K.ngon(x, z, 0.14, 8), y + 0.5, y + h, IRON)
    for yy in (y + 1.4, y + h - 0.6):
        p.prism_xz(K.ngon(x, z, 0.22, 8), yy, yy + 0.15, IRON)
    D.lantern(p, g, x, y + h, z, s=0.8, cap=IRON, light=GLASS)


def bench(p, x, z, along_x=True, y=0.0):
    """Парковая скамья: чугунные боковины, деревянные рейки."""
    L = 2.6
    for e in (-1, 1):
        if along_x:
            p.box(x + e * L / 2 - 0.1, x + e * L / 2 + 0.1, y, y + 1.6, z - 0.5, z + 0.5, IRON)
        else:
            p.box(x - 0.5, x + 0.5, y, y + 1.6, z + e * L / 2 - 0.1, z + e * L / 2 + 0.1, IRON)
    for k in range(3):
        if along_x:
            p.box(x - L / 2, x + L / 2, y + 0.8, y + 0.9, z - 0.45 + 0.3 * k, z - 0.25 + 0.3 * k, "A87440")
        else:
            p.box(x - 0.45 + 0.3 * k, x - 0.25 + 0.3 * k, y + 0.8, y + 0.9, z - L / 2, z + L / 2, "A87440")
    if along_x:
        p.box(x - L / 2, x + L / 2, y + 1.1, y + 1.6, z + 0.4, z + 0.5, "A87440")
    else:
        p.box(x + 0.4, x + 0.5, y + 1.1, y + 1.6, z - L / 2, z + L / 2, "A87440")


def palm_pot(p, x, z, y=0.0, h=4.0):
    p.prism_xz(K.ngon(x, z, 0.7, 8), y, y + 1.0, "B8583A")
    p.prism_xz(K.ngon(x, z, 0.8, 8), y + 1.0, y + 1.15, MARBLE)
    D.palm(p, (x, y + 1.1, z), (0.3, 0.2), h)


# ══ ФАСАД: галерея источников ═════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, MINT, MINT, "2E5A54")
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "C8C0B0")
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 0.8, MARBLE2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 0.8, 16.4, MINT)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, 8.4, 9.0, WHITE)
    slab(FR, axis, fixed, out, 1.88, -half - 0.5, half + 0.5, 16.4, 17.2, WHITE)
    slab(FR, axis, fixed, out, 1.18, -half - 0.2, half + 0.2, 17.2, 17.5, MARBLE2)
    if fi == 0:
        for k in range(int(2 * half // 0.9)):  # балюстрада (спереди; по бокам и сзади — сплошной парапет)
            a = -half + 0.4 + 0.9 * k
            slab(FS, axis, fixed, out, 1.5, a - 0.14, a + 0.14, 17.5, 18.5, WHITE)
    else:
        slab(FR, axis, fixed, out, 1.38, -half - 0.2, half + 0.2, 17.5, 18.5, MINT2)
    slab(FR, axis, fixed, out, 1.58, -half - 0.3, half + 0.3, 18.5, 18.9, WHITE)
    for k in range(int(2 * half // 4.0) + 1):  # пилястры
        a = -half + 0.2 + 4.0 * k
        if a + 0.8 <= half:
            slab(FR, axis, fixed, out, 1.18, a, a + 0.8, 0.8, 16.4, WHITE)
    for k in range(int(2 * half // 4.0)):  # окна с полукруглым верхом
        a = -half + 2.6 + 4.0 * k
        if a + 1.4 > half or (fi == 0 and -6.0 < a < 6.0):
            continue
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
        f0, f1 = sorted((fixed + out * 0.88, fixed + out * 1.1))
        pl = "zy" if axis == "x" else "xy"
        (FG.prism_zy if axis == "x" else FG.prism_xy)(arch(a, 10.2, 13.8, 1.1), d0, d1, GLASS)
        band(FS, pl, arch(a, 10.2, 13.8, 1.4), arch(a, 10.2, 13.8, 1.1), f0, f1, WHITE)
        if fi > 0:
            (FG.prism_zy if axis == "x" else FG.prism_xy)(arch(a, 2.4, 5.6, 1.1), d0, d1, "BFE8E0")
            band(FS, pl, arch(a, 2.4, 5.6, 1.4), arch(a, 2.4, 5.6, 1.1), f0, f1, WHITE)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# открытая аркада вдоль фасада (по бокам от ротонды)
AZ = -FZ - 2.4
for x0, x1 in ((-17.4, -6.4), (6.4, 17.4)):
    n = 4
    xs = [x0 + (x1 - x0) * k / n for k in range(n + 1)]
    for x in xs:
        column(FS, x, AZ, -0.1, 7.4, r=0.42)
    for a, b in zip(xs, xs[1:]):
        c = (a + b) / 2
        hw = (b - a) / 2 - 0.45
        band(FS, "xy", arch(c, 6.0, 6.6, hw + 0.35), arch(c, 6.0, 6.6, hw), AZ - 0.4, AZ + 0.4, WHITE)
    FS.box(x0 - 0.7, x1 + 0.7, 7.4, 8.4, AZ - 0.6, -FZ - 0.88, WHITE)
    FS.box(x0 - 0.8, x1 + 0.8, 8.4, 8.6, AZ - 0.7, -FZ - 0.88, MARBLE2)
# ротонда-беседка под куполом с чашей родника
RZ = -FZ - 0.9
F.objects(True)
for k in range(7):
    a = math.pi * (1.0 + k / 6)
    column(FS, 4.6 * math.cos(a), RZ + 4.6 * math.sin(a) * 0.42, -0.1 + 0.6, 11.4, r=0.45)
F.objects(False)
FS.prism_xz([(5.2 * math.cos(math.pi * (1 + k / 12)), RZ + 5.2 * math.sin(math.pi * (1 + k / 12)) * 0.42) for k in range(13)], -0.1, 0.5, MARBLE2)
FS.prism_xz([(5.6 * math.cos(math.pi * (1 + k / 12)), RZ + 5.6 * math.sin(math.pi * (1 + k / 12)) * 0.42) for k in range(13)], 11.4, 12.2, WHITE)
for j in range(5):  # полукупол ярусами
    t0, t1 = j / 5, (j + 1) / 5
    r0, r1 = 5.4 * math.cos(math.pi / 2 * t0), 5.4 * math.cos(math.pi / 2 * t1)
    y0, y1 = 12.2 + 3.6 * math.sin(math.pi / 2 * t0), 12.2 + 3.6 * math.sin(math.pi / 2 * t1)
    FS.prism_xz([(r0 * math.cos(math.pi * (1 + k / 12)), RZ + r0 * math.sin(math.pi * (1 + k / 12)) * 0.42) for k in range(13)], y0, y1,
                MINT2 if j % 2 else MINT)
FS.prism_xz(K.ngon(0.0, RZ - 0.6, 0.3, 6), 15.8, 16.8, BRASS)
F.objects(True)
FS.prism_xz(K.ngon(0.0, RZ - 1.4, 1.6, 12), 0.5, 1.4, MARBLE)  # чаша родника
FG.prism_xz(K.ngon(0.0, RZ - 1.4, 1.35, 12), 1.4, 1.46, AQUA)
FS.prism_xz(K.ngon(0.0, RZ - 1.4, 0.3, 8), 1.4, 3.0, MARBLE2)
FG.prism_xz(K.octa(0.0, RZ - 1.4, 0.35, 0.35, 0.12), 3.0, 3.6, AQUA2)
for k in range(4):
    a = math.pi / 2 * k + math.pi / 4
    taper(FG, (0.0, 3.4, RZ - 1.4), (0.9 * math.cos(a), 1.6, RZ - 1.4 + 0.9 * math.sin(a)), 0.18, 0.08, AQUA2)
F.objects(False)
# фонари, скамейки, клумбы, пальмы
F.objects(True)
for x in (-13.3, 13.3):
    lamp_post(FS, FG, x, -FZ - 1.3, y=-0.1, h=4.6)
for x in (-9.0, 9.0):
    bench(FS, x, -FZ - 1.4, along_x=True, y=-0.1)
for x in (-14.6, 14.6):
    FS.box(x - 1.3, x + 1.3, -0.1, 0.5, -FZ - 1.9, -FZ - 0.9, MARBLE2)
    for k in range(6):
        FS.prism_xz(K.octa(x - 1.0 + 0.4 * k, -FZ - 1.4 + 0.2 * (k % 2), 0.22, 0.22, 0.08), 0.5, 0.95, FLOWERS[k % 4])
F.objects(False)

# ══ ИНТЕРЬЕР: бювет ═══════════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.1
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "CFC6B4")  # не пересвечен
for i in range(-6, 7):
    for j in range(-6, 7):
        x, z = 2.4 * i, -3.0 + 2.4 * j
        if (i + j) % 2 == 0 and abs(x) < W - 1.6 and ZF + 1.6 < z < ZB - 1.6 and math.hypot(x, z + 3.0) > 4.4:
            IQ.prism_xz([(x, z - 1.0), (x + 1.0, z), (x, z + 1.0), (x - 1.0, z)], 0.02, 0.04, MINT2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, MINT)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 1.4, MARBLE2)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, MINT)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, WHITE)
    slab(IR, axis, fixed, out, 1.4, -half, half, 15.4, 16.2, WHITE)
    if idx < 2:  # глухие арки и краники с раковинами
        for a in (-11.0, -5.0, 1.0, 7.0):
            pl = "zy"
            d0, d1 = sorted((fixed + out * 0.88, fixed + out * 1.1))
            band(IS, pl, arch(a, 1.4, 10.4, 2.4), arch(a, 1.4, 10.4, 2.0), d0, d1, WHITE)
            IS.prism_zy(arch(a, 1.4, 10.4, 2.0), *sorted((fixed + out * 0.88, fixed + out * 0.92)), MINT2)
            F.objects(True)
            IS.box(*sorted((fixed + out * 0.9, fixed + out * 1.9)), 3.0, 3.4, a - 1.0, a + 1.0, MARBLE)
            IS.box(*sorted((fixed + out * 0.9, fixed + out * 1.6)), 2.0, 3.0, a - 0.3, a + 0.3, MARBLE2)
            IS.box(*sorted((fixed + out * 0.9, fixed + out * 1.5)), 4.4, 4.6, a - 0.08, a + 0.08, BRASS)
            IS.box(*sorted((fixed + out * 1.35, fixed + out * 1.5)), 4.0, 4.4, a - 0.08, a + 0.08, BRASS)
            IG.box(*sorted((fixed + out * 1.38, fixed + out * 1.47)), 3.4, 4.0, a - 0.04, a + 0.04, AQUA2)
            F.objects(False)
# за экспонатом — глубокая зелёная арка-ниша в белом обрамлении: белая антилопа читается на тёмном, а не на мяте
d0, d1 = ZF + 0.88, ZF + 1.1
IR.prism_xy(arch(0.0, 1.4, 8.0, 4.4), ZF + 0.88, ZF + 0.94, "2A6A5C")
band(IS, "xy", arch(0.0, 1.4, 8.0, 4.9), arch(0.0, 1.4, 8.0, 4.4), d0, d1, WHITE)
for k in range(-3, 4):
    IS.box(-W, W, C - 0.6, C - 0.2, 4.4 * k - 0.2, 4.4 * k + 0.2, WHITE)
# кольцо колонн вокруг постамента и кессонное кольцо-купол
px, pz = PED
for k in range(8):
    a = 2 * math.pi * k / 8 + math.pi / 8
    x, z = px + 6.2 * math.cos(a), pz + 6.2 * math.sin(a)
    if z > pz + 4.0 and abs(x) < 3.0:
        continue
    column(IR, x, z, 0.0, 12.4, r=0.55)
ring_y(IR, px, pz, 5.6, 6.9, 12.4, 13.2, WHITE, n=16)
for j in range(3):
    ring_y(IS, px, pz, 5.6 - 1.4 * j - 1.2, 5.6 - 1.4 * j, 13.2 + 1.2 * j, 13.6 + 1.2 * j, (MINT2, WHITE, MINT)[j], n=16)
IG.prism_xz(K.ngon(px, pz, 1.6, 12), C - 0.1, C - 0.04, GLASS)
# пальмы и скамьи
F.objects(True)
for x, z in ((-13.6, 6.6), (13.6, 6.6), (-13.6, -13.4), (13.6, -13.4)):
    palm_pot(IS, x, z, h=4.4)
for x in (-9.6, 9.6):
    bench(IS, x, 6.0, along_x=True)
F.objects(False)
# постамент: чаша тёмно-зелёного мрамора с латунным бортиком, светящейся водой и кувшинками (белое — только экспонат)
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, 0.5, MARBLE2)
IS.prism_xz(K.ngon(px, pz, 3.9, 16), 0.5, TOP - 0.1, "2A6A5C")
ring_y(IS, px, pz, 3.5, 3.9, TOP - 0.1, TOP + 0.15, BRASS, n=16)
IG.prism_xz(K.ngon(px, pz, 3.5, 16), TOP - 0.1, TOP, AQUA)
for k in range(5):
    a = 2 * math.pi * k / 5 + 0.4
    x, z = px + 3.0 * math.cos(a), pz + 3.0 * math.sin(a)
    IS.prism_xz(K.ngon(x, z, 0.42, 8), TOP, TOP + 0.05, LEAF)
B.lift_leaves(IS, WHITE, MINT2)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, MINT)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "C8C0B0")
SL.box(-FX - 0.5, FX + 0.5, 16.4, 17.2, -FZ - 0.5, FZ + 0.5, WHITE)
SL.box(-17.6, 17.6, 7.4, 8.6, AZ - 0.7, -FZ, WHITE)
SL.prism_xz([(5.4 * math.cos(math.pi * (1 + k / 6)), RZ + 5.4 * math.sin(math.pi * (1 + k / 6)) * 0.42) for k in range(7)], 0.5, 15.8, MINT)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.98, 0.95)),
                                                   ("Spot", (0, 13, -3), 2600, (1.0, 0.97, 0.92)),
                                                   ("Spring", (0, 4, -3), 600, (0.6, 1.0, 1.0))])
