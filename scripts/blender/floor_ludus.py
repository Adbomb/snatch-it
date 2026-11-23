"""Этаж «Шлем гладиатора» музея-небоскрёба (одиннадцатая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — школа гладиаторов (лудус). Снаружи — красная штукатурка с травертиновым цоколем, ворота-арка
с тяжёлой решёткой и бронзовыми гвоздями, над ней — бронзовый шлем-эмблема с гребнем и лавровый венок, по бокам
— стойки с круглыми и прямоугольными щитами, копья в пирамиде, деревянный тренировочный столб-палус, бочки
с водой, амфоры, натянутый тент над скамьёй. Внутри — тренировочный двор под портиком: песчаная арена, столбы-
палусы со следами ударов, стойки с деревянными мечами, ряды щитов на стене, скамьи, бронзовые жаровни, крюки с
доспехами; экспонат — на круглом бронзовом щите-постаменте с умбоном.
Запуск: blender --background --factory-startup --python scripts/blender/floor_ludus.py -- <репо> <превью>
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

RED, RED2, TRAV, TRAV2, BRONZE, BRONZE2 = "B8402E", "8E2E22", "E8DCC0", "C8B896", "C8863A", "9A6428"
WOOD, WOOD2, IRON, SAND, LAUREL, CANVAS = "A0784A", "6A4A2A", "4A4A52", "E2CC98", "5A8A3A", "E8D8B0"
BLUE, FIRE = "2A4A8A", "FF9A30"

F = B.Floor("LU", "GladiatorHelmet", quiet=(RED2, SAND, "8A7A60"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def shield_round(p, c, n, r, col, rim=BRONZE):
    S.disc(p, c, n, r, 0.2, col, seg=14)
    S.annulus(p, c, n, r * 0.85, r, 0.26, rim, seg=14)
    from mathutils import Vector
    nn = Vector(n).normalized()
    S.disc(p, tuple(Vector(c) + nn * 0.2), n, r * 0.25, 0.2, rim, seg=8)


def shield_rect(p, x, y, z, w, h, col, face=-1):
    p.box(x - w / 2, x + w / 2, y, y + h, z - 0.12, z + 0.12, col)
    p.box(x - w / 2 - 0.08, x + w / 2 + 0.08, y + h * 0.45, y + h * 0.55, z - 0.16, z + 0.16, BRONZE)
    p.prism_xy(K.ngon(x, y + h / 2, w * 0.18, 8), z + face * 0.12, z + face * 0.3, BRONZE)


def helmet(p, x, y, z, s):
    """Шлем-эмблема: купол, широкие поля, решётчатое забрало, гребень."""
    for k in range(4):
        a0, a1 = math.pi / 2 * k / 4, math.pi / 2 * (k + 1) / 4
        p.prism_xz(K.ngon(x, z, 1.4 * s * math.cos((a0 + a1) / 2), 12), y + 1.8 * s * math.sin(a0), y + 1.8 * s * math.sin(a1), BRONZE)
    p.prism_xz(K.ngon(x, z, 2.1 * s, 12), y - 0.2 * s, y, BRONZE2)
    p.box(x - 0.9 * s, x + 0.9 * s, y - 1.4 * s, y, z - 1.4 * s, z - 1.2 * s, BRONZE2)
    for k in range(4):
        p.box(x - 0.7 * s + 0.46 * s * k - 0.05 * s, x - 0.7 * s + 0.46 * s * k + 0.05 * s, y - 1.3 * s, y - 0.1 * s, z - 1.46 * s, z - 1.4 * s, IRON)
    for k in range(7):
        a = math.pi * (k + 0.5) / 7
        p.box(x - 0.15 * s, x + 0.15 * s, y + 1.6 * s + 0.6 * s * math.sin(a), y + 2.2 * s + 0.6 * s * math.sin(a),
              z - 1.2 * s * math.cos(a) - 0.2 * s, z - 1.2 * s * math.cos(a) + 0.2 * s, RED)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, RED, TRAV2, TRAV, SAND, "4A3A2A", roof="hip", roof_col="B05A3A", top=15.6, band=(4.0, 4.6, TRAV),
         side=S.side_windows(F, TRAV, "2A2420", kind="arch", y0=7.0, y1=11.0, w=1.8, xs=(-12.90, -6.90, -0.90, 5.10, 11.10)))
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # травертиновый цоколь и пилястры
    slab(FR, axis, fixed, out, 1.15, -half, half, 1.0, 4.0, TRAV)
    for k in range(int(2 * half // 6.0) + 1):
        a = -half + 6.0 * k
        slab(FR, axis, fixed, out, 1.2, a - 0.5, a + 0.5, 4.6, 15.6, TRAV2)
# ворота-арка с решёткой и гвоздями
AW = 7.0
arc_o = [(-AW / 2 - 1.0, 1.0), (AW / 2 + 1.0, 1.0)] + [((AW / 2 + 1.0) * math.cos(math.pi * k / 8), 7.0 + (AW / 2 + 1.0) * math.sin(math.pi * k / 8))
                                                       for k in range(9)]
arc_i = [(-AW / 2, 1.0), (AW / 2, 1.0)] + [(AW / 2 * math.cos(math.pi * k / 8), 7.0 + AW / 2 * math.sin(math.pi * k / 8)) for k in range(9)]
FS.frame_xy(arc_o, arc_i, -FZ - 1.5, -FZ - 0.88, TRAV)
FS.prism_xy(arc_i, -FZ - 0.92, -FZ - 0.88, "2A1E16")
for k in range(7):
    x = -AW / 2 + 0.5 + (AW - 1.0) * k / 6
    top = 7.0 + math.sqrt(max((AW / 2) ** 2 - x * x, 0.0)) - 0.2
    FS.box(x - 0.14, x + 0.14, 1.0, top, -FZ - 1.2, -FZ - 1.0, IRON)
for y in (3.0, 5.6, 8.2):
    FS.box(-AW / 2, AW / 2, y - 0.14, y + 0.14, -FZ - 1.3, -FZ - 1.15, IRON)
    for k in range(7):
        x = -AW / 2 + 0.5 + (AW - 1.0) * k / 6
        FS.prism_xy(K.ngon(x, y, 0.16, 6), -FZ - 1.38, -FZ - 1.3, BRONZE)
# бронзовый шлем-эмблема и лавровый венок над аркой
F.objects(True)
helmet(FS, 0.0, 13.0, -FZ - 2.0, 0.8)
for e in (-1, 1):
    for k in range(6):
        a = math.pi * (0.15 + 0.12 * k)
        x, y = e * 2.6 * math.cos(a), 12.0 - 1.6 * math.sin(a)
        FS.prism_xy(K.octa(x, y, 0.35, 0.18, 0.08), -FZ - 1.1, -FZ - 0.95, LAUREL)
F.objects(False)
# стойки со щитами, пирамида копий, палус, бочки, амфоры, тент над скамьёй
F.objects(True)
shield_round(FS, (-15.4, 6.0, -FZ - 1.0), (0, 0, -1), 1.2, BLUE)  # один круглый щит рядом с прямоугольным — не «глаза»
shield_rect(FS, -12.6, 4.6, -FZ - 1.1, 2.0, 3.2, RED)
for k, x in enumerate((12.6, 15.4)):
    shield_rect(FS, x, 4.6, -FZ - 1.1, 2.0, 3.2, (RED, BLUE)[k])
for k in range(5):
    a = 2 * math.pi * k / 5
    beam(FS, (-9.0 + 0.9 * math.cos(a), -0.1, -FZ - 2.2 + 0.9 * math.sin(a)), (-9.0, 4.6, -FZ - 2.2), 0.12, 0.12, WOOD2)
FS.prism_xz(K.ngon(-9.0, -FZ - 2.2, 0.25, 6), 4.6, 5.0, IRON)
FS.prism_xz(K.ngon(8.0, -FZ - 2.2, 0.45, 8), -0.1, 4.0, WOOD)
for y in (1.4, 2.6):
    FS.box(7.4, 8.6, y, y + 0.12, -FZ - 2.75, -FZ - 2.6, WOOD2)
D.barrel(FS, 5.4, -FZ - 2.0, y=-0.1, r=0.7, h=1.6, wood=WOOD, hoop=IRON)
for x in (-5.6, -4.6):
    FS.prism_xz(K.ngon(x, -FZ - 1.6, 0.3, 8), -0.1, 0.3, "C86A3A")
    FS.prism_xz(K.ngon(x, -FZ - 1.6, 0.5, 8), 0.3, 1.4, "C86A3A")
    FS.prism_xz(K.ngon(x, -FZ - 1.6, 0.2, 8), 1.4, 1.9, "C86A3A")
F.objects(False)
FS.loft([(10.6, 7.6, -FZ - 0.9), (17.6, 7.6, -FZ - 0.9), (17.6, 7.75, -FZ - 0.9), (10.6, 7.75, -FZ - 0.9)],
        [(10.6, 6.8, -FZ - 2.8), (17.6, 6.8, -FZ - 2.8), (17.6, 6.95, -FZ - 2.8), (10.6, 6.95, -FZ - 2.8)], CANVAS)
for x in (10.8, 17.4):
    FS.box(x - 0.1, x + 0.1, -0.1, 6.9, -FZ - 2.8, -FZ - 2.6, WOOD2)
FS.box(11.2, 17.0, 1.2, 1.5, -FZ - 2.2, -FZ - 1.4, WOOD)

# ══ ИНТЕРЬЕР: тренировочный двор ══════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
S.interior(F, TRAV, SAND, "6A4A2A", RED2, wain=(2.4, RED), beams=(5, WOOD2), beam_dir="z")
IQ.prism_xz(K.octa(0.0, -3.0, 11.0, 10.0, 3.0), 0.02, 0.05, "E8D2A0")  # песок арены
F.objects(True)
for s in (-1, 1):  # портик: колонны вдоль боковых стен
    for z in (-12.0, -6.0, 0.0, 6.0):
        x = s * (W - 2.4)
        IR.prism_xz(K.ngon(x, z, 0.6, 10), 0.0, C - 0.8, TRAV)
        IS.box(x - 0.8, x + 0.8, C - 1.4, C - 0.8, z - 0.8, z + 0.8, TRAV2)
for (x, z) in ((-7.0, -10.0), (7.0, -10.0), (-7.5, 3.5)):  # столбы-палусы со следами ударов
    IS.prism_xz(K.ngon(x, z, 0.5, 8), 0.0, 5.2, WOOD)
    for k in range(4):
        IS.box(x - 0.52, x + 0.52, 1.6 + 0.9 * k, 1.75 + 0.9 * k, z - 0.15, z + 0.15, WOOD2)
# стойки с деревянными мечами, щиты на дальней стене, скамьи
for x0 in (-13.0, 9.0):
    IS.box(x0, x0 + 4.0, 0.0, 0.3, ZF + 1.6, ZF + 2.0, WOOD2)
    IS.box(x0, x0 + 4.0, 3.4, 3.6, ZF + 1.6, ZF + 2.0, WOOD2)
    for k in range(6):
        x = x0 + 0.4 + 0.65 * k
        IS.box(x - 0.08, x + 0.08, 0.3, 4.2, ZF + 1.72, ZF + 1.88, WOOD)
        IS.box(x - 0.3, x + 0.3, 1.0, 1.15, ZF + 1.7, ZF + 1.9, WOOD2)
for k in range(5):  # круглый щит один — синий за экспонатом; по бокам прямоугольные (пара круглых читалась «глазами»)
    x = -6.0 + 3.0 * k
    if k == 2:
        shield_round(IS, (x, 9.0, ZF + 0.9), (0, 0, 1), 1.1, BLUE)
    else:
        shield_rect(IS, x, 7.6, ZF + 1.0, 1.8, 2.8, (BLUE, RED, None, RED, BLUE)[k], face=1)
for z in (-6.0, 2.0):
    IS.box(-W + 4.0, -W + 7.0, 1.2, 1.5, z - 0.6, z + 0.6, WOOD)
    for e in (-1.2, 1.2):
        IS.box(-W + 5.5 + e - 0.2, -W + 5.5 + e + 0.2, 0.0, 1.2, z - 0.4, z + 0.4, WOOD2)
# бронзовые жаровни и крюки с доспехами
for x in (-4.0, 4.0):
    IS.prism_xz(K.ngon(x, 5.0, 0.25, 6), 0.0, 2.4, BRONZE2)
    IS.loft([(x + 0.4 * math.cos(a), 2.4, 5.0 + 0.4 * math.sin(a)) for a in [2 * math.pi * k / 8 for k in range(8)]],
            [(x + 1.0 * math.cos(a), 3.0, 5.0 + 1.0 * math.sin(a)) for a in [2 * math.pi * k / 8 for k in range(8)]], BRONZE)
    IG.prism_xz(K.ngon(x, 5.0, 0.6, 6), 3.0, 3.6, FIRE)
F.objects(False)
for k, z in enumerate((-12.0, -6.0)):
    x = W - 0.95
    IS.box(x - 0.2, x, 7.6, 7.8, z - 0.1, z + 0.1, IRON)
    IS.box(x - 0.6, x - 0.2, 5.0, 7.6, z - 1.0, z + 1.0, BRONZE)
    IS.box(x - 0.6, x - 0.2, 6.6, 7.2, z - 1.4, z + 1.4, BRONZE2)
# постамент: круглый бронзовый щит с умбоном
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 18), 0.0, TOP - 0.3, BRONZE2)
IS.prism_xz(K.ngon(px, pz, 4.1, 18), TOP - 0.3, TOP, IRON)  # тёмное железо: золотой шлем не сливается с бронзой
S.annulus(IS, (px, TOP, pz), (0, 1, 0), 3.4, 3.7, 0.06, RED, seg=18)
for k in range(12):
    a = 2 * math.pi * k / 12
    IS.prism_xz(K.ngon(px + 3.85 * math.cos(a), pz + 3.85 * math.sin(a), 0.14, 6), TOP, TOP + 0.08, BRONZE2)
B.lift_leaves(IS, RED2, BRONZE)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, RED, SAND, "B05A3A", top=15.6, roof="hip")
SL.prism_xy(arc_o, -FZ - 1.5, -FZ, TRAV)

F.build(exhibit=(PED[0], TOP, PED[1], 2.9), lamps=[("Hall", (0, 14, 6), 1900, (1.0, 0.93, 0.82)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.96, 0.88)),
                                                   ("Fire", (0, 4, 5), 700, (1.0, 0.6, 0.3))])
