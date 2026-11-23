"""Этаж «Часовой голем» музея-небоскрёба (десятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — мастерская часовщика. Снаружи — тёмно-зелёная викторианская лавка с золотыми полосами, над входом
— один большой циферблат с римскими метками и стрелками в латунной раме, рядом — открытая «механика»: шестерни
разного размера в сцеплении, витрина с часами разной формы, полосатый навес, латунные трубы, высокие напольные
часы-маятник у двери, фонарь на кронштейне. Внутри — зал механизмов: огромные шестерни на боковых стенах, длинный
маятник посреди дальней стены, верстак с инструментами и лампой-лупой, полки с часами-домиками, ковёр с
узором-шестернёй; экспонат — на платформе-шестерне с зубцами.
Запуск: blender --background --factory-startup --python scripts/blender/floor_clockwork.py -- <репо> <превью>
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
from floorbase import C, FX, FZ, W, ZB, ZF, beam, rng, slab  # noqa: E402

GREEN, GREEN2, GOLD, BRASS, BRASS2, CREAM = "2A5A4A", "1E4236", "E8B840", "C8963A", "A8782A", "F4ECD8"
DARK, WOOD, WOOD2, RED, STEEL, GLASS = "2A2A30", "8A5A32", "5E3C20", "B83A3A", "8A929C", "F8E8C0"

F = B.Floor("CG", "ClockGolem", quiet=(GREEN2, "8A8070", "5A4A3A"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def gear(p, c, n, r, teeth, t, col, hub=None):
    """Шестерня: обод-кольцо, зубцы, ступица со спицами; c — центр, n — нормаль."""
    from mathutils import Vector

    nn, u, v = S._basis(n)
    c = Vector(c)
    S.annulus(p, c, nn, r * 0.72, r, t, col, seg=max(10, teeth))
    for k in range(teeth):
        a = 2 * math.pi * (k + 0.5) / teeth
        d = u * math.cos(a) + v * math.sin(a)
        q = c + d * (r + 0.18 * r / 1.5)
        side = (u * -math.sin(a) + v * math.cos(a)) * (math.pi * r / teeth * 0.5)
        pts = [c + d * r - side, c + d * r + side, q + side * 0.6, q - side * 0.6]
        p.loft([tuple(x) for x in pts], [tuple(x + nn * t) for x in pts], col)
    S.disc(p, c, nn, r * 0.22, t * 1.4, hub or col, seg=8)
    for k in range(4):
        a = math.pi / 2 * k + 0.3
        d = u * math.cos(a) + v * math.sin(a)
        beam(p, tuple(c + d * r * 0.2 + nn * t * 0.5), tuple(c + d * r * 0.74 + nn * t * 0.5), r * 0.12, t * 0.8, col, up=tuple(nn))


def clock_face(p, x, y, z, r, rim=BRASS):
    """Циферблат на фасаде (в плоскости xy, лицом к −z): рама, метки, стрелки."""
    S.disc(p, (x, y, z), (0, 0, -1), r, 0.15, CREAM, seg=18)
    S.annulus(p, (x, y, z - 0.05), (0, 0, -1), r, r + 0.35, 0.3, rim, seg=18)
    for k in range(12):
        a = 2 * math.pi * k / 12
        L = 0.5 if k % 3 == 0 else 0.25
        beam(p, (x + (r - 0.2) * math.cos(a), y + (r - 0.2) * math.sin(a), z - 0.2), (x + (r - 0.2 - L) * math.cos(a), y + (r - 0.2 - L) * math.sin(a), z - 0.2),
             0.12, 0.06, DARK, up=(0, 0, 1))
    beam(p, (x, y, z - 0.25), (x + r * 0.5 * math.cos(1.1), y + r * 0.5 * math.sin(1.1), z - 0.25), 0.18, 0.06, DARK, up=(0, 0, 1))
    beam(p, (x, y, z - 0.3), (x + r * 0.78 * math.cos(-0.5), y + r * 0.78 * math.sin(-0.5), z - 0.3), 0.12, 0.06, DARK, up=(0, 0, 1))


# ══ ФАСАД: лавка часовщика ════════════════════════════════════════════════════════════════════════════════════
S.facade(F, GREEN, GREEN2, GOLD, "8A8070", "2A3A34", roof="flat", roof_col=GREEN, top=16.0, pilaster=GREEN2,
         band=(9.6, 10.2, GOLD), side=S.side_windows(F, GOLD, GLASS, kind="arch", y0=11.0, y1=14.6, w=2.0, xs=(-13.0, -7.0, -1.0, 5.0, 11.0)))
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FS, axis, fixed, out, 1.05, -half, half, 15.0, 15.2, GOLD)
# большой циферблат над входом
clock_face(FS, 0.0, 12.8, -FZ - 1.1, 2.6)
# открытая «механика»: шестерни в сцеплении слева (по фасаду +x)
gear(FS, (9.6, 12.6, -FZ - 1.1), (0, 0, -1), 2.0, 14, 0.3, BRASS)
gear(FS, (12.8, 10.6, -FZ - 1.3), (0, 0, -1), 1.2, 10, 0.3, BRASS2)
gear(FS, (14.6, 13.2, -FZ - 1.1), (0, 0, -1), 0.8, 8, 0.3, GOLD)
# витрина с часами разной формы, полосатый навес
FG.box(-15.4, -4.6, 1.8, 7.8, -FZ - 0.92, -FZ - 0.88, GLASS)
FS.frame_xy(K.rect(-15.7, -4.3, 1.5, 8.1), K.rect(-15.4, -4.6, 1.8, 7.8), -FZ - 1.1, -FZ - 0.88, GOLD)
FS.box(-15.4, -4.6, 1.8, 2.4, -FZ - 1.6, -FZ - 0.92, WOOD)
F.objects(True)
for k, (x, r, kind) in enumerate(((-13.6, 0.9, 0), (-10.4, 0.6, 1), (-8.0, 0.6, 2), (-5.8, 0.5, 2))):  # без пар одинаковых циферблатов
    if kind == 1:
        FS.box(x - 0.6, x + 0.6, 2.4, 5.4, -FZ - 1.5, -FZ - 1.1, WOOD2)
        clock_face(FS, x, 4.4, -FZ - 1.5, r * 0.7, rim=GOLD)
    elif kind == 2:
        FS.prism_xz(K.ngon(x, -FZ - 1.3, 0.45, 8), 2.4, 3.0, BRASS)
        S.disc(FS, (x, 3.8, -FZ - 1.3), (0, 0, -1), 0.6, 0.3, BRASS, seg=12)
        S.disc(FS, (x, 3.8, -FZ - 1.62), (0, 0, -1), 0.45, 0.04, CREAM, seg=12)
    else:
        clock_face(FS, x, 2.4 + r + 0.4, -FZ - 1.4, r, rim=BRASS if k == 0 else RED)
F.objects(False)
for k in range(8):
    x0 = -16.0 + 1.5 * k
    FS.loft([(x0, 9.0, -FZ - 0.9), (x0 + 1.5, 9.0, -FZ - 0.9), (x0 + 1.5, 9.15, -FZ - 0.9), (x0, 9.15, -FZ - 0.9)],
            [(x0, 8.2, -FZ - 2.6), (x0 + 1.5, 8.2, -FZ - 2.6), (x0 + 1.5, 8.35, -FZ - 2.6), (x0, 8.35, -FZ - 2.6)], (RED, CREAM)[k % 2])
# дверь, напольные часы-маятник, латунные трубы, фонарь
FS.box(-1.8, 1.8, 1.0, 8.4, -FZ - 1.0, -FZ - 0.88, WOOD2)
FG.box(-1.3, 1.3, 4.6, 7.8, -FZ - 1.04, -FZ - 1.0, GLASS)
FS.box(1.0, 1.3, 3.8, 4.2, -FZ - 1.15, -FZ - 1.04, BRASS)
F.objects(True)
GX = 4.0
FS.box(GX - 0.9, GX + 0.9, -0.1, 7.6, -FZ - 2.0, -FZ - 1.0, WOOD)
FS.prism_xy([(GX - 1.0, 7.6), (GX + 1.0, 7.6), (GX, 8.6)], -FZ - 2.05, -FZ - 0.95, WOOD2)
clock_face(FS, GX, 6.6, -FZ - 2.05, 0.65)
FG.box(GX - 0.6, GX + 0.6, 0.8, 5.4, -FZ - 2.04, -FZ - 2.0, "FFF0C8")
FS.box(GX - 0.04, GX + 0.04, 2.2, 5.4, -FZ - 2.1, -FZ - 2.06, BRASS)
S.disc(FS, (GX, 2.0, -FZ - 2.1), (0, 0, -1), 0.4, 0.08, BRASS, seg=10)
F.objects(False)
for x in (-17.2, 17.2):
    FS.prism_xz(K.ngon(x, -FZ - 1.2, 0.3, 8), -0.1, 16.0, BRASS2)
    for y in (4.0, 8.0, 12.0):
        FS.prism_xz(K.ngon(x, -FZ - 1.2, 0.42, 8), y - 0.15, y + 0.15, BRASS)
FS.box(-3.4, -2.4, 9.0, 9.2, -FZ - 2.2, -FZ - 0.88, DARK)
D.lantern(FS, FG, -3.0, 8.0, -FZ - 2.0, s=1.0, cap=DARK, light="FFE8A0")

# ══ ИНТЕРЬЕР: зал механизмов ══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.4
S.interior(F, "D8CCB0", "8A6A4A", GREEN2, GOLD, wain=(3.2, WOOD), beams=(5, WOOD2), beam_dir="x")
F.objects(True)
for s in (-1, 1):  # огромные шестерни на боковых стенах
    x = s * (W - 1.0)
    n = (-s, 0, 0)
    gear(IS, (x, 9.0, -8.0), n, 4.0, 20, 0.5, BRASS, hub=GOLD)
    gear(IS, (x, 4.4 + 1.6 * (s > 0), -1.4), n, 2.2, 12, 0.5, BRASS2, hub=GOLD)
    gear(IS, (x, 13.4, -1.0 + 1.4 * s), n, 1.6, 10, 0.5, GOLD)
# длинный маятник посреди дальней стены
IS.box(-3.0, 3.0, C - 2.6, C - 2.0, ZF + 0.88, ZF + 1.6, WOOD2)
beam(IS, (0.0, C - 2.4, ZF + 1.5), (1.6, 4.6, ZF + 1.5), 0.3, 0.2, BRASS)
S.disc(IS, (1.7, 4.2, ZF + 1.4), (0, 0, 1), 1.4, 0.4, GOLD, seg=16)
S.annulus(IS, (1.7, 4.2, ZF + 1.8), (0, 0, 1), 1.0, 1.4, 0.06, BRASS2, seg=16)
# верстак с инструментами и лампой-лупой
BX = W - 4.6
IS.box(BX - 1.8, BX + 1.8, 2.8, 3.1, 1.0, 8.0, WOOD)
for e in (-1.6, 1.6):
    for f in (1.2, 7.8):
        IS.box(BX + e - 0.12, BX + e + 0.12, 0.0, 2.8, f - 0.12, f + 0.12, WOOD2)
for k in range(5):
    IS.box(BX - 1.2 + 0.5 * k, BX - 1.0 + 0.5 * k, 3.1, 3.2, 2.0, 3.6 + 0.3 * k, STEEL)
gear(IS, (BX + 0.6, 3.1, 5.0), (0, 1, 0), 0.6, 8, 0.12, BRASS)
gear(IS, (BX - 0.6, 3.1, 6.2), (0, 1, 0), 0.4, 6, 0.12, GOLD)
beam(IS, (BX + 1.4, 3.1, 7.4), (BX + 0.6, 5.6, 6.2), 0.12, 0.12, DARK)
S.annulus(IS, (BX + 0.4, 5.4, 5.8), (0, 1, 0.4), 0.4, 0.6, 0.12, DARK, seg=10)
IG.prism_xz(K.ngon(BX + 0.4, 5.8, 0.4, 10), 5.45, 5.5, "D8F0FF")
# полки с часами-домиками (ку-ку) на левой стене у лифта
x0 = -W + 0.88
for row, y in enumerate((5.0, 8.4)):
    IS.box(x0, x0 + 1.0, y - 0.2, y, 2.0, 12.0, WOOD2)
    for k in range(4):
        z = 3.2 + 2.4 * k + (1.2 if row else 0.0)
        if z > 11.4:
            continue
        IS.box(x0 + 0.1, x0 + 0.9, y, y + 1.4, z - 0.6, z + 0.6, (WOOD, RED, GREEN, WOOD)[(k + row) % 4])
        IS.prism_zy([(z - 0.8, y + 1.4), (z + 0.8, y + 1.4), (z, y + 2.1)], x0 + 0.05, x0 + 0.95, WOOD2)
        S.disc(IS, (x0 + 0.92, y + 0.75, z), (1, 0, 0), 0.38, 0.06, CREAM, seg=10)
F.objects(False)
# ковёр с узором-шестернёй у лифта
gear(IQ, (0.0, 0.02, 7.0), (0, 1, 0), 2.6, 14, 0.04, "6A3A2A", hub=GOLD)
for x, z in ((-6.0, -6.0), (6.0, -6.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.0, C - 0.8, z - 0.03, z + 0.03, DARK)
    D.lantern(IS, IG, x, C - 4.0, z, s=1.0, cap=BRASS2, light="FFE8B0")
# постамент: платформа-шестерня с зубцами
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 3.6, 16), 0.0, TOP - 0.3, DARK)
# верх — тёмная сталь: жёлтый голем читается на ней, латунь — только зубчатый обод
IS.prism_xz(K.ngon(px, pz, 2.9, 16), TOP - 0.3, TOP - 0.02, "3A3C44")
gear(IS, (px, TOP - 0.3, pz), (0, 1, 0), 3.9, 18, 0.3, BRASS, hub="4A4C54")
B.lift_leaves(IS, GREEN2, GOLD)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, GREEN, "8A8070", GREEN, top=16.0)
SL.prism_xy(K.ngon(0.0, 12.8, 2.9, 10), -FZ - 1.4, -FZ, CREAM)

F.build(exhibit=(PED[0], TOP, PED[1], 2.0), lamps=[("Hall", (0, 14, 6), 1700, (1.0, 0.93, 0.82)),
                                                   ("Spot", (0, 13, -3), 3700, (1.0, 0.96, 0.88)),
                                                   ("Brass", (12, 6, -6), 700, (1.0, 0.8, 0.45))])
