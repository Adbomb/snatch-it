"""Этаж «Скорпион-лейка» музея-небоскрёба (девятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — садовый центр. Снаружи — шалфейно-зелёный дощатый магазин с белыми наличниками, слева — стеклянная
пристройка-оранжерея в белых рамах со скатной крышей, витрина с пирамидой терракотовых горшков, дверь с полукруглым
верхом, шпалера с вьющимися розами, ящики с цветами под окнами, вывеска-лейка, стойка с лейками, тачка с землёй,
катушка шланга, мешки грунта, кусты в кадках, белый штакетник. Внутри — торговый зал: столы-стеллажи с рядами
горшков и рассады, подвесные корзины с ампельными цветами, стена-перфорация с лейками и инструментами, высокие
кадки с кактусами, штабель мешков, полки с пакетиками семян; экспонат — на огромном терракотовом горшке
с землёй и цветами по краю.
Запуск: blender --background --factory-startup --python scripts/blender/floor_garden.py -- <репо> <превью>
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
from floorbase import C, FX, FZ, W, ZB, ZF, beam, rng, taper  # noqa: E402

SAGE, SAGE2, WHITE, POT, POT2, SOIL = "8AB08A", "6A906A", "F4F2EA", "C8643A", "A84E2C", "5A3A26"
LEAF, LEAF2, ROSE, PINK, YEL, BLUE = "4AA84A", "2E8A3C", "E0405A", "F28AB0", "F2C83A", "5A8AE0"
WOOD, WOOD2, GLASS, CAN, CAN2, STEEL = "B08A5A", "7A5A3A", "D8F0E8", "4AA0D8", "E8A030", "A8B0B8"

F = B.Floor("GC", "CanScorpion", quiet=(SAGE2, "A89A78", "8A7A5A"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def pot(p, x, z, y, r, h, plant=True, flower=None):
    """Терракотовый горшок-усечённый конус с ободком и растением."""
    p.loft([(x + a, y, z + b) for a, b in [(r * 0.7 * math.cos(t), r * 0.7 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]]],
           [(x + a, y + h, z + b) for a, b in [(r * math.cos(t), r * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]]], POT)
    p.prism_xz(K.ngon(x, z, r * 1.08, 8), y + h - 0.15, y + h + 0.05, POT2)
    if plant:
        D.bush(p, x, z, y=y + h - 0.1, r=r * 0.95, c1=LEAF, c2=LEAF2)
        if flower:
            for k in range(3):
                a = 2 * math.pi * k / 3 + x
                p.prism_xz(K.ngon(x + r * 0.5 * math.cos(a), z + r * 0.5 * math.sin(a), r * 0.28, 5), y + h + r * 0.7, y + h + r * 0.9, flower)


def can(p, x, z, y, s, col, face=-1):
    """Лейка: бочонок, носик-конус с розеткой, дужка."""
    p.prism_xz(K.ngon(x, z, 0.5 * s, 10), y, y + 1.0 * s, col)
    taper(p, (x - 0.4 * s, y + 0.4 * s, z), (x - 1.4 * s, y + 1.2 * s, z), 0.2 * s, 0.1 * s, col)
    S.disc(p, (x - 1.4 * s, y + 1.2 * s, z), (-1, 0.6, 0), 0.22 * s, 0.08 * s, col, seg=8)
    for k in range(4):
        a0, a1 = math.pi * k / 4, math.pi * (k + 1) / 4
        beam(p, (x + 0.45 * s * math.cos(a0), y + 1.0 * s + 0.45 * s * math.sin(a0), z),
             (x + 0.45 * s * math.cos(a1), y + 1.0 * s + 0.45 * s * math.sin(a1), z), 0.1 * s, 0.1 * s, col)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, SAGE, WHITE, WHITE, "A89A78", "4A6A4A", roof="hip", roof_col="8A5A3A", top=15.8, boards=(1.1, SAGE2),
         side=S.side_windows(F, WHITE, GLASS, kind="rect", y0=8.0, y1=12.0, w=2.6, xs=(-12.55, -5.05, 2.45, 9.95)))
# оранжерея-пристройка слева (по фасаду +x): стеклянный короб в белых рамах со скатной крышей
G0, G1, GD = 4.0, 16.8, -FZ - 2.8
FG.box(G0, G1, 1.0, 8.6, GD, GD + 0.04, GLASS)
for x in (G0, G1):
    FG.box(x - 0.02, x + 0.02, 1.0, 8.6, GD, -FZ - 0.9, GLASS)
FG.loft([(G0, 8.6, GD), (G1, 8.6, GD), (G1, 8.64, GD), (G0, 8.64, GD)],
        [(G0, 11.2, -FZ - 0.9), (G1, 11.2, -FZ - 0.9), (G1, 11.24, -FZ - 0.9), (G0, 11.24, -FZ - 0.9)], GLASS)
for k in range(7):
    x = G0 + (G1 - G0) * k / 6
    FS.box(x - 0.1, x + 0.1, 1.0, 8.7, GD - 0.1, GD + 0.1, WHITE)
    beam(FS, (x, 8.7, GD), (x, 11.3, -FZ - 0.9), 0.2, 0.14, WHITE)
    if k < 6:
        FS.box(x + 0.1, x + (G1 - G0) / 6 - 0.1, 4.6, 4.75, GD - 0.08, GD + 0.08, WHITE)
for x in (G0, G1):
    FS.box(x - 0.1, x + 0.1, 1.0, 8.7, GD, -FZ - 0.88, WHITE)
FR.box(G0 - 0.2, G1 + 0.2, -0.1, 1.0, GD - 0.2, -FZ - 0.88, WHITE)
F.objects(True)
for k in range(6):  # горшки на полках внутри оранжереи
    pot(FS, G0 + 1.1 + 2.1 * k, -FZ - 1.9, 1.0, 0.5, 0.7, flower=(ROSE, YEL, PINK)[k % 3])
    pot(FS, G0 + 1.1 + 2.1 * k, -FZ - 1.9, 4.75, 0.45, 0.6, flower=(PINK, None, BLUE)[k % 3])
F.objects(False)
# витрина с пирамидой горшков и дверь с полукруглым верхом
FG.box(-11.6, -4.6, 2.0, 7.6, -FZ - 0.92, -FZ - 0.88, GLASS)
FS.frame_xy(K.rect(-11.9, -4.3, 1.7, 7.9), K.rect(-11.6, -4.6, 2.0, 7.6), -FZ - 1.1, -FZ - 0.88, WHITE)
F.objects(True)
for row, cnt in enumerate((4, 3, 2, 1)):
    for k in range(cnt):
        pot(FS, -10.6 + 1.6 * k + 0.8 * row, -FZ - 1.4, 2.0 + 0.9 * row, 0.5, 0.8, plant=False)
F.objects(False)
S.window(F, "z", -FZ, -1, -2.6, 1.0, 8.0, 4.0, WHITE, "6A4A3A", kind="arch", mull=False)
FS.box(-2.3, 1.1, 1.0, 6.4, -FZ - 1.0, -FZ - 0.9, "3A6A4A")
FG.box(-1.6, 0.4, 4.0, 6.0, -FZ - 1.04, -FZ - 1.0, GLASS)
# шпалера с вьющимися розами по обе стороны двери
for x0 in (-4.0, 1.6):
    for k in range(4):
        FS.box(x0 + 0.6 * k - 0.04, x0 + 0.6 * k + 0.04, 1.0, 9.6, -FZ - 1.2, -FZ - 1.12, WHITE)
    for k in range(6):
        FS.box(x0 - 0.1, x0 + 1.9, 2.0 + 1.4 * k, 2.08 + 1.4 * k, -FZ - 1.2, -FZ - 1.12, WHITE)
    for k in range(9):
        x, y = x0 + 1.8 * rng(k, x0), 2.0 + 7.4 * rng(k, 3, x0)
        FS.prism_xy(K.ngon(x, y, 0.35, 6), -FZ - 1.4, -FZ - 1.2, LEAF if k % 3 else LEAF2)
        if k % 2 == 0:
            FS.prism_xy(K.ngon(x + 0.2, y + 0.2, 0.22, 5), -FZ - 1.5, -FZ - 1.4, ROSE)
# вывеска-лейка над дверью
FS.box(-6.0, 6.0, 12.6, 15.4, -FZ - 1.1, -FZ - 0.88, WHITE)
FS.frame_xy(K.rect(-6.2, 6.2, 12.4, 15.6), K.rect(-6.0, 6.0, 12.6, 15.4), -FZ - 1.2, -FZ - 0.88, SAGE2)
FS.box(-1.6, 1.0, 12.9, 14.9, -FZ - 1.25, -FZ - 1.1, CAN)
FS.prism_xy([(-1.6, 13.4), (-1.6, 14.0), (-4.2, 15.0), (-4.2, 14.5)], -FZ - 1.25, -FZ - 1.1, CAN)
for k in range(5):
    FS.prism_xy(K.ngon(-4.6 - 0.2 * k, 14.2 - 0.5 * k, 0.12, 6), -FZ - 1.3, -FZ - 1.2, BLUE)
for k, (x, y, r) in enumerate(((2.3, 13.3, 0.34), (3.4, 13.9, 0.46), (4.6, 14.6, 0.38))):  # цветы по диагонали из лейки
    FS.box(x - 0.05, x + 0.05, 12.9, y, -FZ - 1.2, -FZ - 1.12, LEAF2)
    FS.prism_xy(K.ngon(x, y, r, 5), -FZ - 1.25, -FZ - 1.1, (ROSE, YEL, PINK)[k])
# ящики с цветами, стойка с лейками, тачка, шланг, мешки, кусты, штакетник
F.objects(True)
FS.box(-11.8, -4.4, 1.0, 1.7, -FZ - 1.8, -FZ - 0.88, WOOD)
for k in range(8):
    D.flower(FS, -11.4 + 0.95 * k, -FZ - 1.35, y=1.7, h=0.8, stem=LEAF2, petal=(ROSE, YEL, PINK, BLUE)[k % 4])
for x in (-17.0, -14.0):
    FS.box(x - 0.1, x + 0.1, -0.1, 4.6, -FZ - 2.6, -FZ - 2.4, WOOD2)
for y in (1.2, 3.2):
    FS.box(-17.2, -13.8, y - 0.1, y, -FZ - 2.8, -FZ - 1.4, WOOD)
    for k in range(2):
        can(FS, -16.2 + 1.6 * k, -FZ - 2.1, y, 0.7, (CAN, CAN2, "4AC07A", ROSE)[k + (2 if y > 2 else 0)])
FS.box(-3.4, -0.6, 0.6, 1.6, -FZ - 3.0, -FZ - 2.0, "3A7A3A")
FS.prism_xz(K.octa(-2.0, -FZ - 2.5, 1.2, 0.4, 0.2), 1.6, 2.0, SOIL)
S.disc(FS, (-3.8, 0.5, -FZ - 2.5), (1, 0, 0), 0.6, 0.25, "2A2A2A", seg=10)
for e in (-1, 1):
    beam(FS, (-0.6, 1.2, -FZ - 2.5 + e * 0.4), (1.2, 2.0, -FZ - 2.5 + e * 0.4), 0.12, 0.12, WOOD2)
S.annulus(FS, (2.4, 1.4, -FZ - 1.4), (0, 0, -1), 0.5, 1.2, 0.5, "3AA040", seg=12)
for k in range(3):
    FS.prism_xz(K.octa(6.0 + 1.3 * k, -FZ - 2.3, 0.6, 0.45, 0.15), -0.1 + 0.5 * (k == 2), 0.4 + 0.5 * (k == 2), "8A6A3A")
for x in (-FX - 1.4, FX + 1.4):
    pot(FS, x, -FZ - 1.6, -0.1, 1.0, 1.4, flower=None)
for k in range(14):
    x = -FX - 2.6 + (2 * FX + 5.2) * k / 13
    FS.box(x - 0.15, x + 0.15, -0.1, 1.5, -FZ - 3.3, -FZ - 3.1, WHITE)
    FS.prism_xy([(x - 0.15, 1.5), (x + 0.15, 1.5), (x, 1.8)], -FZ - 3.3, -FZ - 3.1, WHITE)
FS.box(-FX - 2.6, FX + 2.6, 0.9, 1.05, -FZ - 3.36, -FZ - 3.3, WHITE)
F.objects(False)

# ══ ИНТЕРЬЕР: торговый зал ════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.8
S.interior(F, "EEF0E4", "B8A888", "F4F2EA", SAGE2, wain=(3.0, SAGE), beams=(6, WOOD), beam_dir="x")
F.objects(True)
for s in (-1, 1):  # столы-стеллажи с горшками вдоль стен
    for k in range(2):
        z = -10.0 + 9.0 * k
        x = s * (W - 3.6)
        IS.box(x - 2.0, x + 2.0, 2.4, 2.6, z - 3.6, z + 3.6, WOOD)
        IS.box(x - 2.0, x + 2.0, 0.8, 0.95, z - 3.6, z + 3.6, WOOD2)
        for e in (-1.8, 1.8):
            for f in (-3.4, 3.4):
                IS.box(x + e - 0.1, x + e + 0.1, 0.0, 2.4, z + f - 0.1, z + f + 0.1, WOOD2)
        for i in range(2):
            for j in range(3):
                pot(IS, x - 1.0 + 2.0 * i, z - 2.4 + 2.4 * j, 2.6, 0.6, 0.75, flower=(ROSE, YEL, PINK, BLUE, None)[(i + j + k) % 5])
                pot(IS, x - 1.0 + 2.0 * i, z - 2.4 + 2.4 * j, 0.95, 0.5, 0.6, plant=False)
# стена-перфорация с лейками и инструментами (дальняя)
IS.box(-9.0, 9.0, 4.0, 11.6, ZF + 0.88, ZF + 1.05, "D8C8A0")
for j in range(3):
    for k in range(16):
        IS.box(-8.4 + 1.12 * k - 0.05, -8.4 + 1.12 * k + 0.05, 5.0 + 2.6 * j - 0.05, 5.0 + 2.6 * j + 0.05, ZF + 1.05, ZF + 1.08, "8A7A5A")
for k in range(5):
    can(IS, -6.8 + 3.4 * k, ZF + 1.7, 8.2, 0.9, (CAN, CAN2, "4AC07A", ROSE, BLUE)[k])
for k in range(6):
    x = -7.6 + 3.0 * k
    IS.box(x - 0.08, x + 0.08, 4.4, 7.2, ZF + 1.1, ZF + 1.3, WOOD2)
    IS.box(x - 0.5, x + 0.5, 4.2 if k % 2 else 7.2, 4.6 if k % 2 else 7.6, ZF + 1.1, ZF + 1.3, STEEL)
# высокие кадки с кактусами и штабель мешков у стены
for x in (-13.0, 13.0):
    pot(IS, x, ZF + 3.0, 0.0, 1.3, 1.6, plant=False)
    IS.prism_xz(K.ngon(x, ZF + 3.0, 0.6, 8), 1.6, 6.4, LEAF2)
    IS.box(x, x + 1.4, 3.6, 4.2, ZF + 2.7, ZF + 3.3, LEAF2)
    IS.prism_xz(K.ngon(x + 1.2, ZF + 3.0, 0.35, 6), 4.2, 5.6, LEAF2)
for row in range(3):
    for k in range(3 - row):
        IS.prism_xz(K.octa(-11.0 + 1.6 * k + 0.8 * row, 7.0, 0.8, 1.2, 0.3), 0.7 * row, 0.7 * row + 0.7, ("8A6A3A", "6A8A3A")[(k + row) % 2])
# подвесные корзины с ампельными цветами
for x, z in ((-8.0, -6.0), (8.0, -6.0), (-8.0, 4.0), (8.0, 4.0)):
    for a in range(3):
        beam(IS, (x + 0.8 * math.cos(a * 2.1), 9.6, z + 0.8 * math.sin(a * 2.1)), (x, 12.0, z), 0.04, 0.04, "6A6A60")
    IS.box(x - 0.03, x + 0.03, 12.0, C - 0.8, z - 0.03, z + 0.03, "6A6A60")
    IS.prism_xz(K.ngon(x, z, 0.5, 8), 8.9, 9.2, WOOD2)  # круглое кашпо, не ящик
    IS.prism_xz(K.ngon(x, z, 0.72, 8), 9.2, 9.6, WOOD2)
    D.bush(IS, x, z, y=9.5, r=0.75, c1=LEAF, c2=LEAF2)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        taper(IS, (x + 0.62 * math.cos(a), 9.4, z + 0.62 * math.sin(a)), (x + 0.85 * math.cos(a), 7.8 - 0.3 * (k % 2), z + 0.85 * math.sin(a)), 0.2, 0.08, LEAF2)
        IS.prism_xz(K.ngon(x + 0.85 * math.cos(a), z + 0.85 * math.sin(a), 0.17, 5), 7.6 - 0.3 * (k % 2), 7.8 - 0.3 * (k % 2), (ROSE, PINK, YEL)[k % 3])
F.objects(False)
# полки с пакетиками семян на правой стене у лифта
x = W - 0.88
for y in (4.0, 5.4, 6.8):
    IS.box(x - 0.8, x, y - 0.1, y, 6.0, 12.0, WOOD)
    for k in range(10):
        IS.box(x - 0.5, x - 0.4, y, y + 0.9, 6.2 + 0.56 * k, 6.6 + 0.56 * k, (ROSE, YEL, BLUE, LEAF, PINK, CAN2)[(k + int(y)) % 6])
for x, z in ((-4.0, -11.0), (4.0, -11.0), (0.0, 6.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.0, C - 0.8, z - 0.03, z + 0.03, "3A3A40")
    D.lantern(IS, IG, x, C - 4.0, z, s=1.0, cap=SAGE2, light="FFF4D8")
# постамент: огромный горшок тёмно-зелёной глазури с землёй и цветами по краю (оранжевый скорпион — не на терракоте)
px, pz = PED
IR.loft([(px + 3.0 * math.cos(t), 0.0, pz + 3.0 * math.sin(t)) for t in [2 * math.pi * (k + 0.5) / 16 for k in range(16)]],
        [(px + 3.8 * math.cos(t), TOP - 0.3, pz + 3.8 * math.sin(t)) for t in [2 * math.pi * (k + 0.5) / 16 for k in range(16)]], "2E5A4E")
IS.prism_xz(K.ngon(px, pz, 4.2, 16), TOP - 0.3, TOP + 0.1, "3E7466")
IS.prism_xz(K.ngon(px, pz, 3.7, 16), TOP - 0.1, TOP, SOIL)
F.objects(True)
for k in range(10):
    a = 2 * math.pi * k / 10
    D.flower(IS, px + 3.4 * math.cos(a), pz + 3.4 * math.sin(a), y=TOP, h=0.8, stem=LEAF2, petal=(ROSE, YEL, PINK, BLUE, CAN2)[k % 5])
F.objects(False)
B.lift_leaves(IS, SAGE2, WHITE)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, SAGE, "A89A78", "8A5A3A", top=15.8, roof="hip")
SL.box(G0, G1, -0.1, 9.6, GD, -FZ, GLASS)

F.build(exhibit=(PED[0], TOP, PED[1], 3.4), lamps=[("Hall", (0, 14, 6), 1900, (1.0, 0.97, 0.9)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.98, 0.92)),
                                                   ("Green", (-12, 6, -6), 600, (0.8, 1.0, 0.75))])
