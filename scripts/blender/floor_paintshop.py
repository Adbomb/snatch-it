"""Этаж «Хамелеон-калейдоскоп» музея-небоскрёба (восьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — лавка красок. Снаружи — белый дом, по которому с карниза стекают разноцветные потёки краски;
на углу крыши опрокинута огромная банка, из неё по стене льётся струя краски в лужу у цоколя; посередине наверху —
круглое окно-калейдоскоп из цветных клиньев, ниже — пояс из квадратов-образцов всех цветов радуги, вывеска-кисть,
витрина с пирамидой банок под радужным навесом, леса маляра с доской, вёдрами и валиком, лестница. Внутри — зал
красок: стеллажи с банками по цветам радуги, машина для смешивания, стена веерами образцов, ленты-растяжки
под потолком, на полу вокруг постамента — розетка-калейдоскоп из цветных клиньев; экспонат — на белой банке-тумбе
с радужными потёками.
Запуск: blender --background --factory-startup --python scripts/blender/floor_paintshop.py -- <репо> <превью>
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

WHITE, WHITE2, GREY, DARK, WOOD, WOOD2 = "F6F4EE", "E2DED4", "8A8E96", "2E3038", "B08450", "7A5432"
SILVER, GLASS = "C8CCD4", "FFF4D8"
RAINBOW = ("E8343A", "F08A20", "F0C820", "4AB04A", "2EA8E0", "3A5AD8", "8A4AD0", "E860B0")

F = B.Floor("PT", "KaleidoChameleon", quiet=(GREY, "C8C4BC"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def can(p, x, z, y, r, h, col, lid=SILVER, n=10):
    """Банка краски: корпус, цветная этикетка, крышка (n — грани; на стеллажах — проще)."""
    p.prism_xz(K.ngon(x, z, r, n), y, y + h, WHITE)
    p.prism_xz(K.ngon(x, z, r * 1.02, n), y + h * 0.25, y + h * 0.75, col)
    if lid:
        p.prism_xz(K.ngon(x, z, r * 1.04, n), y + h, y + h + 0.08, lid)


def rosette(p, cx, cy, z0, z1, r, n=16, inner=0.25):
    """Калейдоскоп-розетка (вид спереди): цветные клинья по кругу и центр."""
    for k in range(n):
        t0, t1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        p.prism_xy([(cx + r * inner * math.cos(t0), cy + r * inner * math.sin(t0)), (cx + r * math.cos(t0), cy + r * math.sin(t0)),
                    (cx + r * math.cos(t1), cy + r * math.sin(t1)), (cx + r * inner * math.cos(t1), cy + r * inner * math.sin(t1))],
                   z0, z1, RAINBOW[k % len(RAINBOW)])
    p.prism_xy(K.ngon(cx, cy, r * inner, n), z0, z1, WHITE)


def drip(p, axis, fixed, out, a, y_top, length, w, col, depth=0.12):
    """Потёк краски по стене: полоса, сужающаяся книзу, с каплей на конце."""
    lo, hi = sorted((fixed, fixed + out * depth))
    pts = [(a - w, y_top), (a + w, y_top), (a + w * 0.6, y_top - length), (a, y_top - length - w * 0.8), (a - w * 0.6, y_top - length)]
    (p.prism_xy if axis == "z" else p.prism_zy)(pts, lo, hi, col)


# ══ ФАСАД: лавка красок ═══════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, WHITE, WHITE, DARK)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "C8C4BC")
    slab(FR, axis, fixed, out, 1.18, -half - 0.2, half + 0.2, -0.1, 1.2, GREY)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.2, 16.6, WHITE)
    n = int(2 * half // 1.6)
    for k in range(n):  # пояс из квадратов-образцов
        a = -half + (2 * half - 1.6 * n) / 2 + 1.6 * k
        slab(FS, axis, fixed, out, 1.06, a + 0.1, a + 1.5, 9.0, 10.4, RAINBOW[k % len(RAINBOW)])
    slab(FR, axis, fixed, out, 1.88, -half - 0.5, half + 0.5, 16.6, 17.4, WHITE2)
    slab(FR, axis, fixed, out, 1.18, -half - 0.2, half + 0.2, 17.4, 18.9, WHITE)
    for k in range(int(2 * half // 2.6)):  # потёки с карниза
        a = -half + 1.3 + 2.6 * k
        L = 1.4 + 3.6 * rng(fi, k)
        drip(FS, axis, fixed + out * 0.88, out, a, 16.6, L, 0.45 + 0.2 * rng(k, fi), RAINBOW[(k + fi * 3) % len(RAINBOW)])
    if fi > 0:  # бока и тыл: окна
        for a in (-10.0, -2.0, 6.0):
            d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
            pr, fr = (FG.prism_zy, FS.frame_zy) if axis == "x" else (FG.prism_xy, FS.frame_xy)
            pr(K.rect(a, a + 2.6, 3.0, 7.0), d0, d1, GLASS)
            fr(K.rect(a - 0.3, a + 2.9, 2.7, 7.3), K.rect(a, a + 2.6, 3.0, 7.0), *sorted((fixed + out * 0.88, fixed + out * 1.1)), DARK)
            pr(K.rect(a, a + 2.6, 11.6, 15.0), d0, d1, GLASS)
            fr(K.rect(a - 0.3, a + 2.9, 11.3, 15.3), K.rect(a, a + 2.6, 11.6, 15.0), *sorted((fixed + out * 0.88, fixed + out * 1.1)), DARK)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# окно-калейдоскоп наверху
FS.frame_xy(K.ngon(-1.0, 13.4, 2.9, 16), K.ngon(-1.0, 13.4, 2.5, 16), -FZ - 1.3, -FZ - 0.88, DARK)
rosette(FG, -1.0, 13.4, -FZ - 1.0, -FZ - 0.9, 2.5, n=16)
# витрина с пирамидой банок под радужным навесом, дверь, вывеска-кисть
FS.box(-15.6, -6.0, 1.2, 7.4, -FZ - 0.96, -FZ - 0.88, DARK)
FG.box(-15.2, -6.4, 1.6, 7.0, -FZ - 1.0, -FZ - 0.96, GLASS)
FS.box(-15.4, -6.2, 1.4, 1.7, -FZ - 1.9, -FZ - 0.88, WOOD)
F.objects(True)
k = 0
for row, cnt in enumerate((5, 4, 3, 2)):
    for i in range(cnt):
        x = -13.6 + 0.95 * row + 1.9 * i
        can(FS, x, -FZ - 1.4, 1.7 + 1.0 * row, 0.42, 0.85, RAINBOW[k % len(RAINBOW)])
        k += 1
F.objects(False)
for j in range(9):
    x0 = -16.0 + 1.1 * j
    FS.loft([(x0, 8.4, -FZ - 0.9), (x0 + 1.1, 8.4, -FZ - 0.9), (x0 + 1.1, 8.55, -FZ - 0.9), (x0, 8.55, -FZ - 0.9)],
            [(x0, 7.5, -FZ - 2.7), (x0 + 1.1, 7.5, -FZ - 2.7), (x0 + 1.1, 7.65, -FZ - 2.7), (x0, 7.65, -FZ - 2.7)], RAINBOW[j % len(RAINBOW)])
FS.box(-3.6, 1.6, 1.2, 8.2, -FZ - 0.96, -FZ - 0.88, DARK)
FS.box(-3.2, 1.2, 1.2, 7.8, -FZ - 1.06, -FZ - 0.96, "3A7AC8")
FG.box(-2.6, 0.6, 4.4, 7.0, -FZ - 1.1, -FZ - 1.06, GLASS)
F.objects(True)  # вывеска-кисть над дверью
beam(FS, (-5.4, 10.9, -FZ - 1.4), (1.0, 10.9, -FZ - 1.4), 0.5, 0.5, WOOD)
FS.box(1.0, 1.8, 10.4, 11.4, -FZ - 1.75, -FZ - 1.05, SILVER)
taper(FS, (1.8, 10.9, -FZ - 1.4), (4.6, 10.9, -FZ - 1.4), 1.2, 0.5, "E8343A")
F.objects(False)
# леса маляра справа: стойки, доска, вёдра, валик, лестница
F.objects(True)
SX0, SX1 = 5.2, 15.6
for x in (SX0, SX1):
    for z in (-FZ - 1.2, -FZ - 2.6):
        FS.box(x - 0.1, x + 0.1, -0.1, 7.2, z - 0.1, z + 0.1, SILVER)
FS.box(SX0 - 0.2, SX1 + 0.2, 6.0, 6.25, -FZ - 2.8, -FZ - 1.0, WOOD)
FS.box(SX0 - 0.2, SX1 + 0.2, 7.0, 7.1, -FZ - 2.7, -FZ - 2.5, SILVER)
for k, x in enumerate((7.0, 9.4, 13.2)):
    can(FS, x, -FZ - 1.9, 6.25, 0.45, 0.8, RAINBOW[(k * 3) % len(RAINBOW)], lid=RAINBOW[(k * 3) % len(RAINBOW)])
beam(FS, (11.4, 6.25, -FZ - 1.8), (11.0, 9.0, -FZ - 1.1), 0.1, 0.1, DARK)
FS.prism_zy(K.ngon(-FZ - 1.0, 9.0, 0.35, 8), 10.3, 11.7, RAINBOW[4])
for e in (-1, 1):
    beam(FS, (3.4 + e * 0.6, -0.1, -FZ - 2.4), (3.4 + e * 0.5, 6.6, -FZ - 1.0), 0.15, 0.15, WOOD2)
for k in range(8):
    t = (k + 0.5) / 8
    FS.box(2.8 + 0.02, 4.0 - 0.02, -0.1 + 6.7 * t - 0.06, -0.1 + 6.7 * t + 0.06, -FZ - 2.4 + 1.4 * t - 0.06, -FZ - 2.4 + 1.4 * t + 0.06, WOOD2)
F.objects(False)
# опрокинутая банка на углу крыши и струя краски в лужу
F.objects(True)
BX, BZ = -19.0, -FZ - 1.4  # банка свисает с угла, струя левее навеса витрины
beam(FS, (BX - 1.0, 17.5, BZ + 0.4), (BX + 1.4, 16.9, BZ - 0.8), 2.0, 2.0, WHITE)
beam(FS, (BX - 0.6, 17.4, BZ + 0.2), (BX + 0.9, 17.0, BZ - 0.6), 2.1, 2.1, RAINBOW[6])
F.objects(False)
FS.loft([(BX + 1.2, 17.0, BZ - 1.4), (BX + 2.6, 17.0, BZ - 1.4), (BX + 2.6, 17.0, BZ - 1.0), (BX + 1.2, 17.0, BZ - 1.0)],
        [(BX + 1.6, 0.0, BZ - 1.2), (BX + 2.4, 0.0, BZ - 1.2), (BX + 2.4, 0.0, BZ - 0.9), (BX + 1.6, 0.0, BZ - 0.9)], RAINBOW[6])
FS.prism_xz(K.octa(BX + 2.0, BZ - 1.0, 1.6, 1.1, 0.5), -0.1, 0.0, RAINBOW[6])

# ══ ИНТЕРЬЕР: зал красок ══════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.1
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "D8D4CC")
px, pz = PED
# розетка на полу: тёмное кольцо у постамента (радужный экспонат читается на нём), радуга — только тонкий обод
IS.prism_xz(K.ngon(px, pz, 7.0, 32), 0.02, 0.05, "3A3C44")
for k in range(16):
    t0, t1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
    IS.prism_xz([(px + 7.0 * math.cos(t0), pz + 7.0 * math.sin(t0)), (px + 7.6 * math.cos(t0), pz + 7.6 * math.sin(t0)),
                 (px + 7.6 * math.cos(t1), pz + 7.6 * math.sin(t1)), (px + 7.0 * math.cos(t1), pz + 7.0 * math.sin(t1))],
                0.02, 0.05, RAINBOW[k % len(RAINBOW)])
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, WHITE)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 1.2, GREY)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, WHITE)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, DARK)
    for k in range(int(2 * half // 2.6)):  # потёки с потолка
        a = -half + 1.3 + 2.6 * k
        if not (gap and abs(a) < DOOR[0] + 1.0):
            drip(IS, axis, fixed + out * 0.88, out, a, C - 0.4, 1.0 + 2.4 * rng(idx, k), 0.4, RAINBOW[(k + idx) % len(RAINBOW)])
for k in range(-3, 4):
    IS.box(-W, W, C - 0.5, C - 0.2, 4.4 * k - 0.2, 4.4 * k + 0.2, DARK)
# стеллажи с банками по цветам радуги вдоль боковых стен
F.objects(True)
for s in (-1, 1):
    x = s * (W - 0.88)
    d0, d1 = sorted((x, x - s * 1.6))
    for z0, z1 in ((-14.6, -5.6), (-3.6, 5.4)):
        IS.box(d0, d1, 0.0, 0.3, z0, z1, DARK)
        for y in (3.0, 6.0, 9.0):
            IS.box(d0, d1, y - 0.15, y, z0, z1, WOOD)
        for zz in (z0, z1):
            IS.box(d0, d1, 0.0, 10.0, zz - 0.12, zz + 0.12, DARK)
        n = int((z1 - z0) // 1.3)
        for row, y in enumerate((0.3, 3.0, 6.0, 9.0)):
            for i in range(n):
                zz = z0 + 0.7 + 1.3 * i
                can(IS, x - s * 0.8, zz, y, 0.42, 1.0, RAINBOW[(i + row * 2) % len(RAINBOW)], lid=None, n=6)
F.objects(False)
# машина для смешивания красок и стена с веерами образцов
F.objects(True)
MX, MZ = 10.4, -12.4
IS.box(MX - 1.6, MX + 1.6, 0.0, 4.2, MZ - 1.4, MZ + 1.4, SILVER)
IS.box(MX - 1.4, MX + 1.4, 4.2, 5.4, MZ - 1.2, MZ + 1.2, GREY)
IG.box(MX - 0.9, MX + 0.4, 3.0, 3.8, MZ + 1.4, MZ + 1.44, "3AD0F0")
for k in range(5):
    IS.prism_xz(K.ngon(MX - 1.0 + 0.5 * k, MZ, 0.18, 6), 5.4, 6.4, RAINBOW[k])
can(IS, MX, MZ + 1.0, 1.4, 0.5, 1.0, RAINBOW[2])
F.objects(False)
# за экспонатом — тёмная грифельная доска в серебряной раме: радужный хамелеон не тонет в радуге вееров
IR.box(-4.6, 4.6, 2.4, 12.4, ZF + 0.88, ZF + 0.98, "3A3C44")
IS.frame_xy(K.rect(-5.0, 5.0, 2.0, 12.8), K.rect(-4.6, 4.6, 2.4, 12.4), ZF + 0.88, ZF + 1.1, SILVER)
for cx in (-13.0, -8.0, 8.0, 13.0):  # веера образцов на дальней стене — по сторонам от доски
    for j in range(6):
        a = math.radians(60 + 12 * j)
        IS.prism_xy([(cx, 6.0), (cx + 4.0 * math.cos(a) - 0.45 * math.sin(a), 6.0 + 4.0 * math.sin(a) + 0.45 * math.cos(a)),
                     (cx + 4.0 * math.cos(a) + 0.45 * math.sin(a), 6.0 + 4.0 * math.sin(a) - 0.45 * math.cos(a))],
                    ZF + 0.9 + 0.02 * j, ZF + 0.94 + 0.02 * j, RAINBOW[(j + k) % len(RAINBOW)])
# ленты-растяжки под потолком
for k in range(6):
    z = -12.0 + 4.0 * k
    if z > 6:
        continue
    D.chain(IS, (-W + 1.0, C - 1.0, z), (W - 1.0, C - 1.0, z + 1.0), 8, 0.14, RAINBOW[k % len(RAINBOW)], sag=1.4)
# постамент: белая банка-тумба с радужными потёками, уже прежней (3.5): ветка экспоната (7.5 шириной, опора у правого
# конца) стоит на крышке, а хамелеон — над её серединой; крышка тёмная, без пустого белого круга
IR.prism_xz(K.ngon(px, pz, 3.5, 16), 0.0, TOP - 0.1, WHITE)
IS.prism_xz(K.ngon(px, pz, 3.3, 16), TOP - 0.1, TOP, "3A3C44")
ring_y(IS, px, pz, 3.3, 3.6, TOP - 0.1, TOP, SILVER, n=16)
for k in range(8):
    a = 2 * math.pi * k / 8
    x, z = px + 3.52 * math.cos(a), pz + 3.52 * math.sin(a)
    IS.prism_xz(K.ngon(x, z, 0.32, 6), 0.3 + 0.2 * (k % 3), TOP - 0.1, RAINBOW[k])
B.lift_leaves(IS, DARK, RAINBOW[4])
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, WHITE)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "C8C4BC")
SL.box(-FX - 0.3, FX + 0.3, 9.0, 10.4, -FZ - 0.3, FZ + 0.3, RAINBOW[4])
SL.box(-FX - 0.5, FX + 0.5, 16.6, 17.4, -FZ - 0.5, FZ + 0.5, WHITE2)
SL.box(BX - 1.4, BX + 2.6, 0.0, 17.4, BZ - 1.4, BZ - 0.9, RAINBOW[6])

F.build(exhibit=(PED[0] - 0.8, TOP, PED[1], 2.8), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.98, 0.95)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Fan", (0, 8, ZF + 5), 500, (1.0, 0.95, 0.9))])
