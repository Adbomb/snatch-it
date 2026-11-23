"""Этаж «Пицца-НЛО» музея-небоскрёба (десятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — пиццерия-закусочная в стиле космической эры 50-х. Снаружи — бирюзово-кремовая закусочная с
наклонными стёклами, крыша-«бумеранг» с козырьком, над входом — летающая тарелка-вывеска с куполом и огнями,
рядом — огромный ломоть пиццы с пепперони, звёзды-«спутники», хромированные полосы, окно выдачи с прилавком,
табуреты-грибки, ракета-флюгер на стойке, шахматный цоколь. Внутри — зал: красные диваны-кабинки со столиками,
стойка с табуретами, кирпичная печь-купол с огнём, музыкальный автомат, шахматный пол, лампы-«спутники»,
планеты на нитях; экспонат — на огромной пицце на подставке.
Запуск: blender --background --factory-startup --python scripts/blender/floor_pizzaufo.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
import floorshell as S  # noqa: E402
from floorbase import C, FX, FZ, W, ZB, ZF, beam, rng, slab, taper  # noqa: E402

TURQ, TURQ2, CREAM, RED, RED2, CHROME = "4AC8C0", "2A9A92", "F6EEDC", "E04040", "B02A2A", "C8D0D8"
BLACK, WHITE, CRUST, CHEESE, PEPPER, BRICK = "2A2A30", "F4F4F0", "E0A050", "F6D050", "C8342A", "B85A3A"
FIRE, NEON, GLASS, YEL = "FF8A30", "6AF0FF", "C8F0F0", "F6D040"

F = B.Floor("PU", "PizzaUfo", quiet=(TURQ2, "C8C0B0", "6A6A70"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def saucer(p, g, x, y, z, r, axis_front=True):
    """Летающая тарелка: широкий диск-обод, верхний купол, огни по кромке."""
    p.prism_xz(K.ngon(x, z, r, 16), y - 0.3, y + 0.3, CHROME)
    p.loft([(x + r * math.cos(a), y + 0.3, z + r * math.sin(a)) for a in [2 * math.pi * k / 16 for k in range(16)]],
           [(x + r * 0.55 * math.cos(a), y + 0.9, z + r * 0.55 * math.sin(a)) for a in [2 * math.pi * k / 16 for k in range(16)]], TURQ)
    p.loft([(x + r * math.cos(a), y - 0.3, z + r * math.sin(a)) for a in [2 * math.pi * k / 16 for k in range(16)]],
           [(x + r * 0.4 * math.cos(a), y - 0.8, z + r * 0.4 * math.sin(a)) for a in [2 * math.pi * k / 16 for k in range(16)]], CHROME)
    g.cone([(x + r * 0.5 * math.cos(a), y + 0.9, z + r * 0.5 * math.sin(a)) for a in [2 * math.pi * k / 12 for k in range(12)]],
           (x, y + 0.9 + r * 0.45, z), GLASS)
    for k in range(10):
        a = 2 * math.pi * k / 10
        g.prism_xz(K.ngon(x + r * 1.02 * math.cos(a), z + r * 1.02 * math.sin(a), 0.16, 6), y - 0.12, y + 0.12, (YEL, NEON)[k % 2])


def pizza(p, x, z, y, r, t=0.3, n=16, slice_gap=False):
    p.prism_xz(K.ngon(x, z, r, n), y, y + t, CRUST)
    p.prism_xz(K.ngon(x, z, r * 0.88, n), y + t, y + t + 0.08, CHEESE)
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.3
        rr = r * (0.35 + 0.35 * (k % 2))
        p.prism_xz(K.ngon(x + rr * math.cos(a), z + rr * math.sin(a), r * 0.12, 8), y + t + 0.08, y + t + 0.14, PEPPER)


def star(p, x, y, z, r, col):
    p.prism_xy([(x + r * (1 if k % 2 == 0 else 0.45) * math.cos(math.pi / 2 + k * math.pi / 5),
                 y + r * (1 if k % 2 == 0 else 0.45) * math.sin(math.pi / 2 + k * math.pi / 5)) for k in range(10)], z - 0.08, z + 0.08, col)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, CREAM, BLACK, TURQ, "C8C0B0", "2A3A48", roof="flat", roof_col=TURQ, top=15.6, band=(8.6, 9.0, CHROME),
         side=S.side_windows(F, TURQ2, GLASS, kind="rect", y0=3.0, y1=7.6, w=3.0, xs=(-9.50, -1.50, 6.50)))
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # шахматный цоколь
    for k in range(int(2 * half // 0.8)):
        a = -half + 0.8 * k
        for j in range(2):
            if (k + j) % 2 == 0:
                slab(FS, axis, fixed, out, 1.24, a, a + 0.8, 0.0 + 0.5 * j, 0.5 + 0.5 * j, WHITE)
# наклонное остекление зала и козырёк-«бумеранг»
FG.loft([(-17.0, 1.0, -FZ - 1.6), (-2.0, 1.0, -FZ - 1.6), (-2.0, 1.04, -FZ - 1.6), (-17.0, 1.04, -FZ - 1.6)],
        [(-17.0, 8.4, -FZ - 0.92), (-2.0, 8.4, -FZ - 0.92), (-2.0, 8.44, -FZ - 0.92), (-17.0, 8.44, -FZ - 0.92)], GLASS)
FG.box(-17.0, -2.0, 1.0, 8.4, -FZ - 0.92, -FZ - 0.88, GLASS)
for k in range(6):
    x = -17.0 + 3.0 * k
    beam(FS, (x, 1.0, -FZ - 1.66), (x, 8.4, -FZ - 0.98), 0.2, 0.14, CHROME)
FS.prism_xz([(-17.6, -FZ - 0.9), (17.6, -FZ - 0.9), (17.0, -FZ - 3.2), (2.0, -FZ - 2.2), (-9.0, -FZ - 3.6), (-17.6, -FZ - 2.6)],
            9.0, 9.4, TURQ)
FS.prism_xz([(-17.6, -FZ - 0.9), (17.6, -FZ - 0.9), (17.0, -FZ - 3.2), (2.0, -FZ - 2.2), (-9.0, -FZ - 3.6), (-17.6, -FZ - 2.6)],
            8.8, 9.0, RED)
# дверь, окно выдачи с прилавком, табуреты-грибки
FS.box(0.0, 3.2, 1.0, 8.0, -FZ - 1.0, -FZ - 0.88, RED)
FG.box(0.4, 2.8, 4.0, 7.4, -FZ - 1.04, -FZ - 1.0, GLASS)
FS.box(2.4, 2.8, 3.4, 3.7, -FZ - 1.15, -FZ - 1.04, CHROME)
FG.box(5.0, 13.0, 3.6, 7.4, -FZ - 0.92, -FZ - 0.88, "FFE8B8")
FS.frame_xy(K.rect(4.7, 13.3, 3.3, 7.7), K.rect(5.0, 13.0, 3.6, 7.4), -FZ - 1.1, -FZ - 0.88, CHROME)
FS.box(4.6, 13.4, 3.2, 3.6, -FZ - 2.0, -FZ - 0.88, RED)
F.objects(True)
for k in range(4):
    x = 5.8 + 2.2 * k
    FS.box(x - 0.08, x + 0.08, -0.1, 2.0, -FZ - 2.6, -FZ - 2.44, CHROME)
    FS.prism_xz(K.ngon(x, -FZ - 2.52, 0.55, 10), 2.0, 2.3, RED if k % 2 else TURQ)
    FS.prism_xz(K.ngon(x, -FZ - 2.52, 0.5, 8), -0.1, 0.0, CHROME)
F.objects(False)
# летающая тарелка-вывеска над входом и огромный ломоть пиццы
F.objects(True)
saucer(FS, FG, 1.6, 12.6, -FZ - 2.2, 3.2)
for e in (-1, 1):
    beam(FS, (1.6 + e * 1.2, 11.9, -FZ - 2.0), (1.6 + e * 2.4, 9.4, -FZ - 1.0), 0.2, 0.2, CHROME)
F.objects(False)
FS.prism_xy([(9.0, 15.4), (16.6, 15.4), (12.8, 9.6)], -FZ - 1.2, -FZ - 0.88, CRUST)
FS.prism_xy([(9.5, 14.9), (16.1, 14.9), (12.8, 10.3)], -FZ - 1.3, -FZ - 1.2, CHEESE)
for (x, y) in ((11.4, 14.0), (14.2, 14.0), (12.8, 12.0)):
    FS.prism_xy(K.ngon(x, y, 0.55, 10), -FZ - 1.36, -FZ - 1.3, PEPPER)
# звёзды-«спутники» и ракета-флюгер на стойке
for (x, y, r) in ((-13.6, 12.0, 0.9), (-8.0, 14.4, 0.6), (-4.0, 11.6, 0.7), (6.4, 14.6, 0.5)):
    star(FS, x, y, -FZ - 1.0, r, YEL if r > 0.65 else NEON)
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4
        beam(FS, (x, y, -FZ - 1.05), (x + 1.8 * r * math.cos(a), y + 1.8 * r * math.sin(a), -FZ - 1.05), 0.06, 0.06, CHROME, up=(0, 0, 1))
RX = -FX - 1.4
F.objects(True)
FS.box(RX - 0.15, RX + 0.15, -0.1, 12.0, -FZ - 1.6, -FZ - 1.3, CHROME)
FS.prism_xz(K.ngon(RX, -FZ - 1.45, 0.6, 10), 12.0, 15.6, WHITE)
FS.cone([(a, 15.6, b) for a, b in K.ngon(RX, -FZ - 1.45, 0.6, 10)], (RX, 17.4, -FZ - 1.45), RED)
for k in range(3):
    a = 2 * math.pi * k / 3
    FS.prism_xy([(RX + 0.55 * math.cos(a), 12.0), (RX + 1.3 * math.cos(a), 11.6), (RX + 0.55 * math.cos(a), 13.6)],
                -FZ - 1.45 + 0.55 * math.sin(a) - 0.06, -FZ - 1.45 + 0.55 * math.sin(a) + 0.06, RED)
FG.prism_xz(K.ngon(RX, -FZ - 1.45, 0.3, 8), 11.6, 12.0, FIRE)
F.objects(False)

# ══ ИНТЕРЬЕР: зал закусочной ══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.6
S.interior(F, CREAM, BLACK, "2A3A48", TURQ, wain=(3.0, TURQ), beams=None, floor_q=True)
for k in range(17):  # шахматный пол крупной клеткой
    for j in range(16):
        if (k + j) % 2 == 0:
            x, z = -W + 1.0 + 2.0 * k, ZF + 1.0 + 2.0 * j
            if x < W - 0.9 and z < ZB - 0.9:
                IQ.box(x - 1.0, x + 1.0, 0.02, 0.04, z - 1.0, z + 1.0, WHITE)
F.objects(True)
for s in (-1, 1):  # диваны-кабинки со столиками вдоль стен
    for k in range(3):
        z = -12.0 + 5.4 * k
        x0 = s * (W - 0.88)
        for e in (-1, 1):
            zz = z + e * 1.8
            IS.box(*sorted((x0, x0 - s * 4.4)), 0.0, 1.6, zz - 0.5, zz + 0.5, RED)
            IS.box(*sorted((x0, x0 - s * 4.4)), 1.6, 3.6, zz + e * 0.2 - 0.3, zz + e * 0.2 + 0.3, RED2)
        IS.box(*sorted((x0 - s * 0.2, x0 - s * 3.8)), 2.4, 2.6, z - 1.0, z + 1.0, WHITE)
        IS.box(*sorted((x0 - s * 1.9, x0 - s * 2.1)), 0.0, 2.4, z - 0.1, z + 0.1, CHROME)
        pizza(IS, x0 - s * 2.0, z, 2.6, 0.7, t=0.15, n=10)
# кирпичная печь-купол с огнём у дальней стены
OX, OZ = -7.0, ZF + 3.4
IR.prism_xz(K.ngon(OX, OZ, 3.0, 12), 0.0, 2.6, BRICK)
for k in range(4):
    a0, a1 = math.pi / 2 * k / 4, math.pi / 2 * (k + 1) / 4
    IR.prism_xz(K.ngon(OX, OZ, 3.0 * math.cos((a0 + a1) / 2), 12), 2.6 + 3.2 * math.sin(a0), 2.6 + 3.2 * math.sin(a1), BRICK)
IS.box(OX - 1.2, OX + 1.2, 2.6, 4.2, OZ + 2.6, OZ + 3.1, "1E1410")
IG.box(OX - 0.9, OX + 0.9, 2.6, 3.4, OZ + 2.5, OZ + 2.62, FIRE)
IS.box(OX - 0.3, OX + 0.3, 5.8, C - 1.0, OZ - 0.3, OZ + 0.3, BRICK)
# стойка с табуретами и музыкальный автомат
IS.box(2.0, 12.0, 0.0, 3.2, ZF + 3.0, ZF + 4.4, TURQ)
IS.box(1.8, 12.2, 3.2, 3.5, ZF + 2.8, ZF + 4.6, WHITE)
for k in range(4):
    x = 3.4 + 2.4 * k
    IS.box(x - 0.08, x + 0.08, 0.0, 2.2, ZF + 5.4 - 0.08, ZF + 5.4 + 0.08, CHROME)
    IS.prism_xz(K.ngon(x, ZF + 5.4, 0.6, 10), 2.2, 2.5, RED)
JX = W - 2.0
IS.box(JX - 1.2, JX + 1.2, 0.0, 4.2, 7.0, 9.0, RED2)
IS.loft([(JX - 1.2, 4.2, 7.0), (JX + 1.2, 4.2, 7.0), (JX + 1.2, 4.2, 9.0), (JX - 1.2, 4.2, 9.0)],
        [(JX - 0.6, 5.8, 7.0), (JX + 0.6, 5.8, 7.0), (JX + 0.6, 5.8, 9.0), (JX - 0.6, 5.8, 9.0)], RED2)
IG.box(JX - 1.24, JX - 1.2, 1.6, 4.0, 7.3, 8.7, "FFD070")
for k in range(4):
    IS.box(JX - 1.28, JX - 1.24, 1.8 + 0.55 * k, 2.0 + 0.55 * k, 7.4, 8.6, (NEON, YEL, RED, NEON)[k])
F.objects(False)
# лампы-«спутники» и планеты на нитях
for k, (x, z) in enumerate(((-4.0, -8.0), (4.0, -8.0), (0.0, 2.0))):
    IS.box(x - 0.03, x + 0.03, 12.0, C - 0.3, z - 0.03, z + 0.03, CHROME)
    IG.prism_xz(K.ngon(x, z, 0.6, 8), 11.2, 12.0, "FFF0C8")
    for j in range(6):
        a = 2 * math.pi * j / 6
        beam(IS, (x, 11.6, z), (x + 1.4 * math.cos(a), 11.6 + 0.4 * (j % 2), z + 1.4 * math.sin(a)), 0.06, 0.06, CHROME)
        IS.prism_xz(K.ngon(x + 1.4 * math.cos(a), z + 1.4 * math.sin(a), 0.15, 6), 11.5 + 0.4 * (j % 2), 11.8 + 0.4 * (j % 2), YEL)
for k, (x, z, r, col) in enumerate(((-10.0, -2.0, 0.9, "E0A060"), (10.0, -6.0, 0.7, TURQ), (8.0, 4.0, 0.5, RED))):
    IS.box(x - 0.02, x + 0.02, 12.0, C - 0.3, z - 0.02, z + 0.02, CHROME)
    IS.prism_xz(K.ngon(x, z, r, 10), 12.0 - r * 2, 12.0, col)
    S.annulus(IS, (x, 12.0 - r, z), (0.2, 1, 0.1), r * 1.3, r * 1.7, 0.08, CREAM, seg=12)
# постамент: огромная пицца на подставке
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 1.6, 10), 0.0, 0.3, CHROME)
IR.prism_xz(K.ngon(px, pz, 0.6, 10), 0.3, TOP - 0.45, CHROME)
pizza(IS, px, pz, TOP - 0.45, 4.0, t=0.3, n=18)
B.lift_leaves(IS, TURQ2, RED)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, CREAM, "C8C0B0", TURQ, top=15.6)
SL.prism_xz(K.ngon(1.6, -FZ - 2.2, 3.2, 8), 12.3, 12.9, CHROME)
SL.prism_xy([(9.0, 15.4), (16.6, 15.4), (12.8, 9.6)], -FZ - 1.2, -FZ, CRUST)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 1900, (1.0, 0.95, 0.9)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Oven", (-7, 3, -12), 800, (1.0, 0.6, 0.3))])
