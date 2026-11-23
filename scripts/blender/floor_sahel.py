"""Этаж «Верблюжонок-фляга» музея-небоскрёба (девятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — глиняная фактория у колодца в стиле сахельской архитектуры. Снаружи — глиняная стена с круглыми
контрфорсами, увенчанными коническими башенками, ряды торчащих деревянных кольев-торонов, высокие ниши,
резная деревянная дверь с металлическими шляпками, треугольные продухи; перед ней — колодец с деревянной рамой,
воротом и ведром, стойка с висящими флягами, пальмы, кувшины, седло на подставке, ковры на перекладине.
Внутри — склад-лавка: квадратные глиняные столбы и потолок из пальмовых брёвен, мешки зерна горкой, стойки с
флягами по стенам, большие кувшины, ниши с треугольным верхом; экспонат — на круглом каменном срубе колодца
с водой и мотком верёвки.
Запуск: blender --background --factory-startup --python scripts/blender/floor_sahel.py -- <репо> <превью>
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
from floorbase import C, FX, FZ, W, ZB, ZF, beam, rng  # noqa: E402

MUD, MUD2, MUD3, WOOD, WOOD2, STONE = "C88A58", "A8683E", "DDA676", "8A5A32", "6A4226", "B0A08A"
CLAY, TEAL, RED, CREAM, WATER, ROPE = "B8562E", "2A8A8A", "B83A2E", "F0E2C4", "4AB8D8", "D8B878"

F = B.Floor("OA", "CanteenCamel", quiet=(MUD2, "D8B888", "8A6A4A"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def canteen(p, x, y, z, r=0.55, col=TEAL, normal=(0, 0, -1)):
    """Фляга: плоский диск, горлышко, ремень."""
    S.disc(p, (x, y, z), normal, r, 0.35, col, seg=10)
    p.box(x - 0.12, x + 0.12, y + r - 0.05, y + r + 0.3, z - 0.12 + 0.17 * normal[2], z + 0.12 + 0.17 * normal[2], WOOD2)


def jar(p, x, z, y, h, col=CLAY):
    p.prism_xz(K.ngon(x, z, h * 0.22, 10), y, y + h * 0.15, col)
    p.prism_xz(K.ngon(x, z, h * 0.34, 10), y + h * 0.15, y + h * 0.7, col)
    p.prism_xz(K.ngon(x, z, h * 0.18, 10), y + h * 0.7, y + h * 0.95, col)
    p.prism_xz(K.ngon(x, z, h * 0.24, 10), y + h * 0.95, y + h, col)


def buttress(p, x, z0, y1, r, col):
    """Круглый контрфорс с конической башенкой."""
    p.prism_xz(K.ngon(x, z0, r, 10), -0.1, y1, col)
    p.cone([(a, y1, b) for a, b in K.ngon(x, z0, r, 10)], (x, min(y1 + r * 2.4, 18.8), z0), col)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, MUD, MUD2, MUD2, "D8B888", "5A3A22", roof="crenel", roof_col=MUD, top=15.8,
         side=S.side_windows(F, WOOD2, "3A2A20", kind="tall", y0=7.0, y1=11.0, w=1.6, xs=(-11.0, -5.0, 1.0, 7.0)))
for x in (-FX + 0.6, -9.0, 9.0, FX - 0.6):  # контрфорсы с башенками
    buttress(FR, x, -FZ - 1.1, 16.2, 1.25, MUD)
for x in (-15.0, -12.2, -5.6, -3.0, 3.0, 5.6, 12.2, 15.0):  # высокие ниши
    FR.box(x - 0.7, x + 0.7, 3.0, 13.6, -FZ - 0.94, -FZ - 0.88, MUD2)
    FR.prism_xy([(x - 0.7, 13.6), (x + 0.7, 13.6), (x, 14.6)], -FZ - 0.94, -FZ - 0.88, MUD2)
for row, y in enumerate((5.2, 9.6, 14.0)):  # колья-тороны
    for k in range(12):  # реже и толще: читаются брёвнами, а не точками
        x = -FX + 1.2 + (2 * FX - 2.4) * k / 11 + (0.8 if row % 2 else 0.0)
        if abs(abs(x) - 9.0) < 1.5 or abs(x) > FX - 1.5:
            continue
        FR.box(x - 0.24, x + 0.24, y - 0.22, y + 0.22, -FZ - 2.3, -FZ - 0.88, WOOD)
# главный вход: глубокий портал, резная дверь со шляпками, треугольные продухи
FR.box(-4.6, 4.6, 1.0, 12.6, -FZ - 1.6, -FZ - 0.88, MUD3)
FR.prism_xy([(-4.6, 12.6), (4.6, 12.6), (0, 15.4)], -FZ - 1.6, -FZ - 0.88, MUD3)
FS.box(-2.4, 2.4, 1.0, 8.6, -FZ - 1.7, -FZ - 1.6, WOOD2)
FS.prism_xy([(-2.4, 8.6), (2.4, 8.6), (0, 10.4)], -FZ - 1.7, -FZ - 1.6, WOOD2)
for k in range(4):
    FS.box(-2.4 + 1.2 * k + 0.55, -2.4 + 1.2 * k + 0.65, 1.0, 8.6, -FZ - 1.78, -FZ - 1.7, WOOD)
for j in range(5):
    for k in range(4):
        FS.prism_xy(K.ngon(-1.8 + 1.2 * k, 2.0 + 1.5 * j, 0.12, 6), -FZ - 1.82, -FZ - 1.7, "C8C0A8")
for k in range(5):
    FS.prism_xy([(-2.0 + k, 11.6), (-1.6 + k, 11.6), (-1.8 + k, 12.2)], -FZ - 1.66, -FZ - 1.6, "3A2A20")
# колодец с рамой, воротом и ведром
WX, WZ = -12.4, -FZ - 2.0
FR.prism_xz(K.ngon(WX, WZ, 1.4, 10), -0.1, 1.6, STONE)
FG.prism_xz(K.ngon(WX, WZ, 1.1, 10), 1.3, 1.35, WATER)
F.objects(True)
for e in (-1, 1):
    FS.box(WX + e * 1.3 - 0.15, WX + e * 1.3 + 0.15, 1.6, 4.6, WZ - 0.15, WZ + 0.15, WOOD)
FS.prism_zy(K.ngon(WZ, 4.2, 0.25, 8), WX - 1.5, WX + 1.5, WOOD2)
FS.box(WX + 1.5, WX + 1.6, 3.6, 4.4, WZ - 0.05, WZ + 0.05, WOOD2)
FS.box(WX - 0.02, WX + 0.02, 2.6, 4.0, WZ - 0.02, WZ + 0.02, ROPE)
FS.prism_xz(K.ngon(WX, WZ, 0.4, 8), 2.0, 2.6, WOOD)
# стойка с флягами
for x in (3.4, 8.6):
    FS.box(x - 0.15, x + 0.15, -0.1, 4.4, -FZ - 2.4, -FZ - 2.1, WOOD)
FS.box(3.2, 8.8, 4.2, 4.5, -FZ - 2.4, -FZ - 2.1, WOOD2)
for k in range(5):
    canteen(FS, 4.2 + 1.05 * k, 3.1 - 0.2 * (k % 2), -FZ - 2.6, col=(TEAL, RED, CREAM, TEAL, "C88A28")[k])
# кувшины, седло, ковры
jar(FS, 11.0, -FZ - 1.6, -0.1, 1.8)
jar(FS, 12.2, -FZ - 2.2, -0.1, 1.3, "A84E2A")
FS.box(-6.8, -5.6, -0.1, 1.6, -FZ - 2.2, -FZ - 1.6, WOOD2)
FS.loft([(-7.4, 1.6, -FZ - 2.4), (-5.0, 1.6, -FZ - 2.4), (-5.0, 1.6, -FZ - 1.4), (-7.4, 1.6, -FZ - 1.4)],
        [(-7.2, 2.2, -FZ - 2.3), (-5.2, 2.2, -FZ - 2.3), (-5.2, 2.2, -FZ - 1.5), (-7.2, 2.2, -FZ - 1.5)], RED)
FS.box(-6.5, -5.9, 2.2, 2.9, -FZ - 2.0, -FZ - 1.8, WOOD2)
F.objects(False)
FS.box(13.4, 17.6, 6.0, 6.2, -FZ - 2.5, -FZ - 2.3, WOOD2)
for k, col in enumerate((RED, TEAL, "C88A28")):
    x0 = 13.6 + 1.35 * k
    FS.box(x0, x0 + 1.2, 2.4, 6.0, -FZ - 2.42, -FZ - 2.36, col)
    FS.box(x0, x0 + 1.2, 3.6 + 0.6 * k, 4.0 + 0.6 * k, -FZ - 2.46, -FZ - 2.42, CREAM)
D.palm(FS, (-FX - 1.4, -0.1, -FZ - 1.4), (0.6, -0.3), 12.0)
D.palm(FS, (16.6, -0.1, -FZ - 1.6), (-0.4, -0.4), 9.0)

# ══ ИНТЕРЬЕР: склад-лавка ═════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.3
S.interior(F, MUD3, "C8A070", WOOD2, MUD2, wain=(1.2, MUD2), beams=None)
for k in range(22):  # потолок из пальмовых брёвен
    x = -W + 0.8 + (2 * W - 1.6) * k / 21
    IS.prism_zy([(ZF, C - 0.75), (ZB, C - 0.75), (ZB, C - 0.15), (ZF, C - 0.15)], x - 0.32, x + 0.32, WOOD if k % 2 else WOOD2)
for x in (-12.6, 12.6):  # квадратные глиняные столбы с балками (у стен: ближние не заслоняют зал от лифта)
    for z in (-10.0, 4.0):
        IR.loft([(x - 1.0, 0.0, z - 1.0), (x + 1.0, 0.0, z - 1.0), (x + 1.0, 0.0, z + 1.0), (x - 1.0, 0.0, z + 1.0)],
                [(x - 0.7, C - 1.6, z - 0.7), (x + 0.7, C - 1.6, z - 0.7), (x + 0.7, C - 1.6, z + 0.7), (x - 0.7, C - 1.6, z + 0.7)], MUD)
        IR.box(x - 1.0, x + 1.0, C - 1.6, C - 0.75, z - 1.0, z + 1.0, MUD2)
    IS.box(x - 0.5, x + 0.5, C - 1.6, C - 0.75, ZF, ZB, WOOD2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS[:3]):  # ниши с треугольным верхом
    for a in (-10.0, -2.0, 6.0) if idx < 2 else (-10.0, 6.0):
        if axis == "x":
            IS.box(*sorted((fixed + out * 0.88, fixed + out * 0.92)), 6.0, 10.0, a, a + 2.4, MUD2)
            IS.prism_zy([(a, 10.0), (a + 2.4, 10.0), (a + 1.2, 11.4)], *sorted((fixed + out * 0.88, fixed + out * 0.92)), MUD2)
        else:
            IS.box(a, a + 2.4, 6.0, 10.0, *sorted((fixed + out * 0.88, fixed + out * 0.92)), MUD2)
            IS.prism_xy([(a, 10.0), (a + 2.4, 10.0), (a + 1.2, 11.4)], *sorted((fixed + out * 0.88, fixed + out * 0.92)), MUD2)
F.objects(True)
# мешки зерна горкой
for row, cnt in enumerate((4, 3, 2)):
    for k in range(cnt):
        x = -14.4 + 1.5 * k + 0.75 * row
        IS.prism_xz(K.octa(x, -12.6, 0.8, 0.9, 0.3), 1.1 * row, 1.1 * row + 1.1, CREAM if (k + row) % 2 else "D8C8A0")
        IS.box(x - 0.3, x + 0.3, 1.1 * row + 1.1, 1.1 * row + 1.35, -12.8, -12.4, ROPE)
# стойки с флягами по левой и правой стенам
for s in (-1, 1):
    x0 = s * (W - 0.88)
    for y in (5.0, 8.6):
        IS.box(*sorted((x0, x0 - s * 0.6)), y, y + 0.3, -6.0, 4.0, WOOD2)
        for k in range(8):
            z = -5.4 + 1.25 * k
            canteen(IS, x0 - s * 0.9, y - 0.9, z, r=0.5, col=(TEAL, RED, CREAM, "C88A28")[(k + int(y)) % 4], normal=(-s, 0, 0))
# большие кувшины у дальней стены
for k, x in enumerate((-4.0, -1.6, 1.6, 4.0, 12.0, 14.2)):
    jar(IS, x, ZF + 1.95, 0.0, 2.6 if k % 2 == 0 else 2.0, (CLAY, "A84E2A", "C87A3A")[k % 3])
F.objects(False)
for x, z in ((-4.0, -9.0), (4.0, -9.0), (-4.0, 4.0), (4.0, 4.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.0, C - 0.75, z - 0.03, z + 0.03, "3A3A40")
    D.lantern(IS, IG, x, C - 4.0, z, s=1.1, cap="6A4A2A", light="FFC860")
# ковры на полу
for (x, z, col) in ((-8.0, 6.0, RED), (8.0, 6.0, TEAL)):
    IQ.box(x - 2.4, x + 2.4, 0.02, 0.06, z - 3.0, z + 3.0, col)
    IQ.box(x - 2.0, x + 2.0, 0.06, 0.08, z - 2.6, z + 2.6, "C88A28")
# за экспонатом — тканый ковёр на дальней стене: песочный верблюд читается на тёмной бирюзе, а не на глине
IR.box(-5.2, 5.2, 3.4, 12.6, ZF + 0.88, ZF + 0.98, TEAL)
for y in (4.2, 11.8):
    IS.box(-5.2, 5.2, y - 0.3, y + 0.3, ZF + 0.98, ZF + 1.04, RED)
IS.box(-5.6, 5.6, 12.6, 13.0, ZF + 0.88, ZF + 1.3, WOOD2)  # перекладина
# постамент: тёмный каменный сруб колодца с водой и мотком верёвки
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 3.9, 14), 0.0, TOP, "7A6E60")
for k in range(14):
    a = 2 * math.pi * (k + 0.5) / 14
    IS.box(px + 3.9 * math.cos(a) - 0.04, px + 3.9 * math.cos(a) + 0.04, 0.0, TOP, pz + 3.9 * math.sin(a) - 0.04, pz + 3.9 * math.sin(a) + 0.04, "8A7A68")
S.annulus(IS, (px, TOP, pz), (0, 1, 0), 3.2, 4.1, 0.25, "C8B8A0", seg=14)
IS.prism_xz(K.ngon(px, pz, 3.2, 14), TOP - 0.1, TOP, "6A5A48")
F.objects(True)
for k in range(3):
    S.annulus(IS, (px + 4.9, 0.25 * k, pz + 2.6), (0, 1, 0), 0.4, 0.75, 0.22, ROPE, seg=10)
F.objects(False)
B.lift_leaves(IS, WOOD2, MUD3)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, MUD, "D8B888", MUD, top=15.8)
for x in (-FX + 0.6, -9.0, 9.0, FX - 0.6):
    SL.prism_xz(K.ngon(x, -FZ - 1.1, 1.25, 6), -0.1, 16.2, MUD)
    SL.cone([(a, 16.2, b) for a, b in K.ngon(x, -FZ - 1.1, 1.25, 6)], (x, 18.8, -FZ - 1.1), MUD)

F.build(exhibit=(PED[0], TOP, PED[1], 3.0), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.9, 0.78)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.96, 0.88)),
                                                   ("Warm", (-10, 6, -8), 700, (1.0, 0.75, 0.45))])
