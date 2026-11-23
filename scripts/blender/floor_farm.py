"""Этаж «Страусёнок-песочник» музея-небоскрёба (восьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — ферма с красным амбаром. Снаружи — красные доски с белыми углами и наличниками, большие ворота
амбара с белыми косыми перекладинами, над ними — дверца сеновала с балкой-блоком и висящим тюком; на левом углу —
серебристая силосная башня с куполом, на парапете — флюгер-петушок; перед амбаром — деревянная изгородь, круглые
тюки сена, бидоны, корыто, курятник с лесенкой. Внутри — амбар: дощатые стены и балки,
стойла с воротцами, ряд гнёзд-ящиков с яйцами, сеновал на столбах с лестницей, кучи сена, вилы, бидоны, фонари;
экспонат — в огромном соломенном гнезде с яйцами на дощатом помосте.
Запуск: blender --background --factory-startup --python scripts/blender/floor_farm.py -- <репо> <превью>
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

RED, RED2, WHITE, WOOD, WOOD2, HAY = "B8342E", "962A26", "F2EEE4", "A87A48", "7A5432", "E8C460"
HAY2, SILVER, SILVER2, GREEN, DARK, EGG = "C8A040", "C8CCD2", "9AA0A8", "4A8A3A", "2E2E34", "F4ECD8"
GLASS = "FFE8B0"

F = B.Floor("FM", "SandChick", quiet=(HAY2, "8AA858", "A88458"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def bale(p, x, z, y, r=1.1, length=1.6, along_x=False):
    """Круглый тюк сена: лежащий цилиндр с обвязкой."""
    pts = K.ngon(z if along_x else x, y + r, r, 10)
    if along_x:
        p.prism_zy(pts, x - length / 2, x + length / 2, HAY)
        for e in (-0.35, 0.35):
            p.prism_zy(K.ngon(z, y + r, r + 0.03, 10), x + e * length - 0.05, x + e * length + 0.05, HAY2)
    else:
        p.prism_xy(pts, z - length / 2, z + length / 2, HAY)
        for e in (-0.35, 0.35):
            p.prism_xy(K.ngon(x, y + r, r + 0.03, 10), z + e * length - 0.05, z + e * length + 0.05, HAY2)


def milk_can(p, x, z, y=0.0):
    p.prism_xz(K.ngon(x, z, 0.4, 8), y, y + 1.0, SILVER)
    p.prism_xz(K.ngon(x, z, 0.25, 8), y + 1.0, y + 1.3, SILVER)
    p.prism_xz(K.ngon(x, z, 0.32, 8), y + 1.3, y + 1.45, SILVER2)


def egg(p, x, z, y, s=0.3):
    p.prism_xz(K.octa(x, z, s, s, s * 0.4), y, y + s * 1.0, EGG)
    p.prism_xz(K.octa(x, z, s * 0.7, s * 0.7, s * 0.28), y + s * 1.0, y + s * 1.45, EGG)


def fence(p, x0, x1, z, y=0.0):
    """Деревянная изгородь: столбики и две жерди."""
    n = max(1, int((x1 - x0) // 1.8))
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n
        p.box(x - 0.12, x + 0.12, y, y + 1.6, z - 0.12, z + 0.12, WOOD)
    for yy in (0.6, 1.2):
        p.box(x0, x1, y + yy, y + yy + 0.15, z - 0.06, z + 0.06, WOOD)


# ══ ФАСАД: красный амбар ══════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, RED, RED, WOOD2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "8AA858")
    slab(FR, axis, fixed, out, 1.18, -half - 0.2, half + 0.2, -0.1, 1.0, "7A7A74")
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.0, 16.6, RED)
    for k in range(int(2 * half // 1.2)):  # вертикальные доски
        a = -half + 0.6 + 1.2 * k
        slab(FS, axis, fixed, out, 0.94, a - 0.05, a + 0.05, 1.0, 16.6, RED2)
    for a in (-half, half - 1.0):
        slab(FR, axis, fixed, out, 1.18, a, a + 1.0, 1.0, 16.6, WHITE)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, 16.6, 17.3, WHITE)
    B.chamfer(FR, axis, fixed, out, -half - 1.4, half + 1.4, [(0.88, 18.9), (2.2, 17.3), (2.2, 17.1), (0.88, 17.1)], "5A5A60")
    if fi > 0:  # бока и тыл: окна в белых рамах с крестом
        for a in (-10.0, -2.0, 6.0):
            d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
            pr, fr = (FG.prism_zy, FS.frame_zy) if axis == "x" else (FG.prism_xy, FS.frame_xy)
            pr(K.rect(a, a + 2.4, 9.0, 12.0), d0, d1, GLASS)
            fr(K.rect(a - 0.3, a + 2.7, 8.7, 12.3), K.rect(a, a + 2.4, 9.0, 12.0), *sorted((fixed + out * 0.88, fixed + out * 1.1)), WHITE)
            slab(FS, axis, fixed, out, 1.0, a + 1.15, a + 1.25, 9.0, 12.0, WHITE)
            slab(FS, axis, fixed, out, 1.0, a, a + 2.4, 10.45, 10.55, WHITE)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# большие ворота амбара с белыми косыми перекладинами
GX = -3.0
for e in (-1, 1):
    x0, x1 = sorted((GX, GX + e * 3.8))
    FS.box(x0, x1, 1.0, 9.6, -FZ - 1.1, -FZ - 0.88, RED2)
    FS.frame_xy(K.rect(x0, x1, 1.0, 9.6), K.rect(x0 + 0.3, x1 - 0.3, 1.3, 9.3), -FZ - 1.3, -FZ - 1.1, WHITE)
    beam(FS, (x0 + 0.3, 1.4, -FZ - 1.2), (x1 - 0.3, 9.2, -FZ - 1.2), 0.3, 0.16, WHITE)
    beam(FS, (x1 - 0.3, 1.4, -FZ - 1.2), (x0 + 0.3, 9.2, -FZ - 1.2), 0.3, 0.16, WHITE)
FS.box(GX - 4.2, GX + 4.2, 9.6, 10.0, -FZ - 1.4, -FZ - 0.88, WHITE)
# дверца сеновала, балка-блок и висящий тюк
FS.box(GX - 1.6, GX + 1.6, 11.4, 15.0, -FZ - 1.0, -FZ - 0.88, "2A1E18")
FS.frame_xy(K.rect(GX - 1.9, GX + 1.9, 11.1, 15.3), K.rect(GX - 1.6, GX + 1.6, 11.4, 15.0), -FZ - 1.2, -FZ - 0.88, WHITE)
FS.box(GX - 0.2, GX + 0.2, 16.0, 16.4, -FZ - 3.2, -FZ - 0.88, WOOD2)
FS.prism_xy(K.ngon(GX, 15.7, 0.3, 8), -FZ - 3.1, -FZ - 2.9, DARK)
FS.box(GX - 0.03, GX + 0.03, 12.6, 15.4, -FZ - 3.03, -FZ - 2.97, "C8B890")
F.objects(True)
FS.box(GX - 0.8, GX + 0.8, 11.6, 12.6, -FZ - 3.5, -FZ - 2.5, HAY)
F.objects(False)
# серебристая силосная башня с куполом на левом (по фасаду +x) углу
SX, SZ = 14.2, -FZ - 0.8
FR.prism_xz(K.ngon(SX, SZ, 2.9, 12), -0.1, 15.6, SILVER)
for y in range(2, 16, 2):
    FS.prism_xz(K.ngon(SX, SZ, 2.98, 12), y - 0.1, y + 0.1, SILVER2)
for k in range(4):
    a0, a1 = math.pi / 2 * k / 4, math.pi / 2 * (k + 1) / 4
    FS.prism_xz(K.ngon(SX, SZ, 2.95 * math.cos((a0 + a1) / 2), 12), 15.6 + 3.2 * math.sin(a0), 15.6 + 3.2 * math.sin(a1), RED)
for k in range(9):  # лесенка на силосе
    FS.box(SX - 0.5, SX + 0.5, 1.0 + 1.6 * k, 1.1 + 1.6 * k, SZ - 3.1, SZ - 2.95, DARK)
for e in (-1, 1):
    FS.box(SX + e * 0.5 - 0.05, SX + e * 0.5 + 0.05, 0.8, 15.0, SZ - 3.1, SZ - 2.95, DARK)
# флюгер-петушок на парапете
FS.box(-12.0 - 0.06, -12.0 + 0.06, 17.3, 18.9, -FZ - 1.4, -FZ - 1.3, DARK)
FS.prism_xy([(-12.6, 18.0), (-11.2, 18.0), (-11.0, 18.6), (-11.5, 18.4), (-12.2, 18.8), (-12.4, 18.4)], -FZ - 1.4, -FZ - 1.3, DARK)
# изгородь, тюки, бидоны, корыто, курятник
F.objects(True)
fence(FS, -FX - 2.4, -10.0, -FZ - 2.6, y=-0.1)
fence(FS, 3.0, 10.4, -FZ - 2.6, y=-0.1)
bale(FS, -12.4, -FZ - 1.5, -0.1, r=1.1, length=1.6, along_x=False)
bale(FS, -9.6, -FZ - 1.5, -0.1, r=1.0, length=1.4, along_x=False)
bale(FS, -11.0, -FZ - 1.5, 1.8, r=0.9, length=1.4, along_x=False)
for x in (3.8, 4.7):
    milk_can(FS, x, -FZ - 1.4, y=-0.1)
FS.box(5.6, 8.0, -0.1, 0.9, -FZ - 1.9, -FZ - 1.0, WOOD)
FG.box(5.8, 7.8, 0.75, 0.85, -FZ - 1.8, -FZ - 1.1, "6AB8E0")
CX = -16.6  # курятник с лесенкой
FS.box(CX - 1.2, CX + 1.2, 1.0, 3.2, -FZ - 2.4, -FZ - 1.0, WOOD)
FS.prism_xy([(CX - 1.5, 3.2), (CX + 1.5, 3.2), (CX, 4.4)], -FZ - 2.5, -FZ - 0.9, RED2)
for e in (-1, 1):
    FS.box(CX + e * 1.0 - 0.1, CX + e * 1.0 + 0.1, -0.1, 1.0, -FZ - 2.3, -FZ - 2.1, WOOD2)
FS.box(CX - 0.4, CX + 0.4, 1.4, 2.4, -FZ - 2.44, -FZ - 2.4, "2A1E18")
beam(FS, (CX + 0.2, 1.4, -FZ - 2.5), (CX + 1.6, -0.1, -FZ - 2.8), 0.5, 0.08, WOOD2)
F.objects(False)

# ══ ИНТЕРЬЕР: амбар ═══════════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.1
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "A88458")
for k in range(14):  # рассыпанная солома
    x, z = -W + 2.0 + (2 * W - 4) * rng(k, 31), ZF + 2.0 + (ZB - ZF - 6) * rng(k, 32)
    IQ.prism_xz(K.octa(x, z, 1.2, 0.8, 0.4), 0.02, 0.06, HAY2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, WOOD)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, WOOD)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, WHITE)
    for k in range(int(2 * half // 1.2)):
        a = -half + 0.6 + 1.2 * k
        if not (gap and abs(a) < DOOR[0] + 0.8):
            slab(IS, axis, fixed, out, 0.93, a - 0.05, a + 0.05, 0.0, C, WOOD2)
    slab(IR, axis, fixed, out, 1.3, -half, half, 15.4, 16.0, WOOD2)
for k in range(-3, 4):
    IS.box(-W, W, C - 0.8, C - 0.2, 4.4 * k - 0.3, 4.4 * k + 0.3, WOOD2)
# стойла с воротцами вдоль правой стены, гнёзда с яйцами вдоль левой
F.objects(True)
for k in range(3):
    z0 = -14.4 + 5.0 * k
    x0 = W - 0.88
    IS.box(x0 - 4.4, x0, 0.0, 3.6, z0 - 0.15, z0 + 0.15, WOOD2)
    IS.box(x0 - 4.4, x0 - 4.2, 0.0, 3.6, z0, z0 + 4.4, WOOD2)
    for yy in (0.8, 2.0, 3.2):
        IS.box(x0 - 4.5, x0 - 4.1, yy, yy + 0.3, z0 + 0.2, z0 + 4.4, WOOD)
    beam(IS, (x0 - 4.3, 0.4, z0 + 0.4), (x0 - 4.3, 3.4, z0 + 4.2), 0.2, 0.2, WOOD)
    bale(IS, x0 - 2.0, z0 + 2.2, 0.0, r=0.9, length=1.6, along_x=True)
IS.box(W - 5.3, W - 0.88, 0.0, 3.6, 0.6, 0.9, WOOD2)
x = -W + 0.88
for row in range(2):
    y = 1.2 + 2.4 * row
    IS.box(x, x + 1.8, y - 0.2, y, -12.0, 2.0, WOOD2)
    for k in range(7):
        z = -11.0 + 2.0 * k
        IS.box(x, x + 1.8, y, y + 1.6, z - 0.9, z - 0.8, WOOD2)
        IS.prism_xz(K.octa(x + 0.9, z, 0.7, 0.7, 0.25), y, y + 0.35, HAY)
        egg(IS, x + 0.9, z, y + 0.35, s=0.28)
IS.box(x, x + 1.8, 4.6, 4.8, -12.0, 2.0, WOOD2)
F.objects(False)
# сеновал на столбах у дальней стены с лестницей
LY = 8.4
# под сеновалом за экспонатом — красные ворота амбара с белыми откосами: жёлтый цыплёнок читается на красном,
# а не на соломе и дереве того же тона
GX = 6.4
IR.box(-GX, GX, 0.0, LY - 0.2, ZF + 0.88, ZF + 0.98, RED)
for x0, x1 in ((-GX, -GX + 0.5), (-0.25, 0.25), (GX - 0.5, GX)):
    IS.box(x0, x1, 0.0, LY - 0.2, ZF + 0.98, ZF + 1.08, WHITE)
for y0 in (0.0, LY - 0.7):
    IS.box(-GX, GX, y0, y0 + 0.5, ZF + 0.98, ZF + 1.08, WHITE)
for s0 in (-1, 1):  # белые косые раскосы в каждой створке
    beam(IS, (s0 * 0.25 + s0 * 0.3, 0.6, ZF + 1.05), (s0 * (GX - 0.8), LY - 0.9, ZF + 1.05), 0.3, 0.06, WHITE, up=(0, 0, 1))
IR.box(-W + 0.88, W - 0.88, LY, LY + 0.5, ZF + 0.88, ZF + 5.0, WOOD)
for x in (-12.0, -4.0, 4.0, 12.0):
    IS.box(x - 0.3, x + 0.3, 0.0, LY, ZF + 4.6, ZF + 5.2, WOOD2)
F.objects(True)
for x in (-14.0, -9.0, 8.0, 13.0):
    IS.prism_xz(K.octa(x, ZF + 2.8, 2.2, 1.6, 0.8), LY + 0.5, LY + 2.2, HAY)
    IS.prism_xz(K.octa(x + 0.4, ZF + 2.8, 1.3, 1.0, 0.5), LY + 2.2, LY + 3.2, HAY2)
for e in (-1, 1):
    beam(IS, (6.0 + e * 0.6, 0.0, ZF + 6.6), (6.0 + e * 0.6, LY + 1.6, ZF + 5.0), 0.15, 0.15, WOOD2)
for k in range(8):
    t = (k + 0.5) / 8
    IS.box(5.4, 6.6, (LY + 1.6) * t - 0.06, (LY + 1.6) * t + 0.06, ZF + 6.6 - 1.6 * t - 0.06, ZF + 6.6 - 1.6 * t + 0.06, WOOD)
IS.prism_xz(K.octa(-6.0, -12.0, 2.0, 1.4, 0.7), 0.0, 1.4, HAY)
IS.prism_xz(K.octa(-5.6, -12.0, 1.2, 0.9, 0.4), 1.4, 2.2, HAY2)
beam(IS, (-3.8, 0.0, -11.6), (-3.2, 4.2, -12.4), 0.12, 0.12, WOOD)
for k in range(3):
    taper(IS, (-3.2 - 0.25 + 0.25 * k, 4.2, -12.4), (-3.1 - 0.4 + 0.4 * k, 5.2, -12.6), 0.08, 0.04, SILVER2)
for x in (-10.0, -9.1):
    milk_can(IS, x, 6.4)
F.objects(False)
for x, z in ((-6.0, -6.0), (6.0, -6.0), (-6.0, 3.0), (6.0, 3.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.0, C - 0.8, z - 0.03, z + 0.03, DARK)
    D.lantern(IS, IG, x, C - 4.0, z, s=1.0, cap=DARK, light=GLASS)
# постамент: огромное соломенное гнездо с яйцами на дощатом помосте
px, pz = PED
IR.box(px - 4.0, px + 4.0, 0.0, 0.5, pz - 4.0, pz + 4.0, WOOD)
for k in range(5):
    IS.box(px - 4.0, px + 4.0, 0.5, 0.52, pz - 4.0 + 1.6 * k, pz - 3.9 + 1.6 * k, WOOD2)
# гнездо из тёмной прошлогодней соломы: жёлтый цыплёнок не сливается с подстилкой
ring_y(IS, px, pz, 2.9, 3.8, 0.5, TOP + 0.5, "9A7434", n=14)
ring_y(IS, px, pz, 3.1, 3.7, TOP + 0.5, TOP + 0.9, "7A5A2A", n=14, a0=10.0, a1=370.0)
IS.prism_xz(K.ngon(px, pz, 3.0, 14), 0.5, TOP, "5A4026")
for k in range(3):
    a = 2 * math.pi * k / 3 + 0.5
    egg(IS, px + 3.3 * math.cos(a), pz + 3.3 * math.sin(a), TOP + 0.9, s=0.4)
B.lift_leaves(IS, WOOD2, WHITE)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 17.3, -FZ, FZ, RED)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "8AA858")
SL.prism_zy([(-FZ - 2.2, 17.3), (FZ + 2.2, 17.3), (FZ + 0.88, 18.9), (-FZ - 0.88, 18.9)], -FX - 2.2, FX + 2.2, "5A5A60")
SL.prism_xz(K.ngon(SX, SZ, 2.9, 8), -0.1, 15.6, SILVER)
SL.cone([(x, 15.6, z) for x, z in K.ngon(SX, SZ, 2.9, 8)], (SX, 18.8, SZ), RED)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.92, 0.8)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Loft", (0, 12, ZF + 4), 600, (1.0, 0.85, 0.6))])
