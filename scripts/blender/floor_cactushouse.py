"""Этаж «Кактус-великан» музея-небоскрёба (десятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — викторианская оранжерея пустынных растений. Снаружи — стеклянные стены в белом чугунном
переплёте, выступающий центральный ризалит с высокой арочной дверью и полукруглым окном-«веером», пилястры
с вазонами, ажурный парапет с шишечками; перед оранжереей — каменистый сад: кактусы-колонны, шары и опунции,
валуны, гравийная дорожка, табличка на столбике, тачка с горшками. Внутри — пустынный сад под белыми арочными
рёбрами: песчаные грядки с кактусами разных видов, валуны, сухое русло с мостиком, каменная тропа, таблички,
скамья; экспонат — в круглой каменной клумбе с песком и галькой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_cactushouse.py -- <репо> <превью>
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

IRONW, IRONW2, PANE, PANE2, STONE, STONE2 = "F4F4EE", "D8DCD4", "BEE4DC", "A8D4CC", "C8B8A0", "A89880"
SAND, SAND2, CACT, CACT2, CACT3, FLOWER = "E8D2A0", "CDB482", "3E9A4A", "2E7A3A", "6AB84A", "F070A0"
YEL, POT, WOOD, GRAVEL = "F2C83A", "C8643A", "8A6038", "B8AA94"

F = B.Floor("GK", "GiantCactus", quiet=(STONE2, GRAVEL, "8AA090"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def saguaro(p, x, z, y, h, arms=2):
    p.prism_xz(K.ngon(x, z, 0.45 * h / 4, 8), y, y + h, CACT)
    p.prism_xz(K.ngon(x, z, 0.3 * h / 4, 8), y + h, y + h + 0.3, CACT3)
    for k in range(arms):
        e = 1 if k % 2 == 0 else -1
        ay = y + h * (0.4 + 0.15 * k)
        p.box(*sorted((x, x + e * 0.9 * h / 4)), ay, ay + 0.5 * h / 4, z - 0.25 * h / 4, z + 0.25 * h / 4, CACT)
        p.prism_xz(K.ngon(x + e * 0.9 * h / 4, z, 0.3 * h / 4, 8), ay, ay + h * 0.35, CACT)


def barrel_cactus(p, x, z, y, r):
    for k in range(3):
        rr = r * (0.8 + 0.2 * math.sin(math.pi * (k + 0.5) / 3))
        p.prism_xz(K.ngon(x, z, rr, 10), y + r * 0.6 * k, y + r * 0.6 * (k + 1), CACT2 if k % 2 else CACT)
    p.prism_xz(K.ngon(x, z, r * 0.35, 6), y + r * 1.8, y + r * 2.0, FLOWER)


def opuntia(p, x, z, y, s):
    p.prism_xy(K.octa(x, y + s, s * 0.6, s, s * 0.3), z - 0.15, z + 0.15, CACT3)
    for e in (-1, 1):
        p.prism_xy(K.octa(x + e * s * 0.7, y + s * 2.1, s * 0.45, s * 0.75, s * 0.2), z - 0.12, z + 0.12, CACT3)
        p.prism_xy(K.ngon(x + e * s * 0.7, y + s * 2.95, s * 0.15, 5), z - 0.14, z + 0.14, YEL)


# ══ ФАСАД: стеклянная оранжерея ═══════════════════════════════════════════════════════════════════════════════
S.facade(F, PANE, STONE, IRONW, GRAVEL, "DCE8E4", roof="flat", roof_col=IRONW2, top=16.0, side=None)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # чугунный переплёт по всем стенам
    for k in range(int(2 * half // 2.4) + 1):
        a = -half + 2.4 * k
        slab(FS, axis, fixed, out, 1.0, a - 0.12, a + 0.12, 1.0, 16.0, IRONW)
    for y in (5.6, 10.8):
        slab(FS, axis, fixed, out, 1.0, -half, half, y - 0.12, y + 0.12, IRONW)
    for k in range(int(2 * half // 2.4)):
        a = -half + 2.4 * k + 1.2
        slab(FQ, axis, fixed, out, 0.9, a - 1.06, a + 1.06, 11.0, 15.8, PANE2)
for k in range(15):  # ажурный парапет с шишечками
    x = -FX + 0.6 + (2 * FX - 1.2) * k / 14
    FS.prism_xz(K.ngon(x, -FZ - 1.1, 0.25, 6), 18.3, 18.8, IRONW)
# центральный ризалит: пилястры, арочная дверь, окно-«веер»
FR.box(-6.0, 6.0, 1.0, 16.0, -FZ - 1.8, -FZ - 0.88, PANE2)
for x in (-6.0, -2.6, 2.6, 6.0):
    FR.box(x - 0.45, x + 0.45, 0.0, 16.4, -FZ - 2.1, -FZ - 0.88, IRONW)
    FS.prism_xz(K.ngon(x, -FZ - 1.5, 0.5, 8), 16.4, 16.8, IRONW2)
    FS.prism_xz(K.ngon(x, -FZ - 1.5, 0.35, 8), 16.8, 17.6, POT)
    FS.prism_xz(K.ngon(x, -FZ - 1.5, 0.5, 8), 17.6, 17.8, POT)
S.window(F, "z", -FZ - 0.92, -1, -1.9, 1.0, 8.6, 3.8, IRONW, "2E5A4A", kind="arch", mull=True)  # арка ниже окна-веера
FS.box(-2.2, 2.2, 10.0, 10.3, -FZ - 2.0, -FZ - 1.7, IRONW)
for k in range(7):  # окно-веер
    a = math.pi * k / 6
    beam(FS, (0.0, 10.6, -FZ - 1.9), (2.0 * math.cos(a), 10.6 + 2.0 * math.sin(a), -FZ - 1.9), 0.14, 0.1, IRONW, up=(0, 0, 1))
FG.prism_xy([(-2.0, 10.6)] + [(2.0 * math.cos(math.pi * (1 - k / 10)), 10.6 + 2.0 * math.sin(math.pi * (1 - k / 10))) for k in range(11)],
            -FZ - 1.84, -FZ - 1.8, PANE)
S.annulus(FS, (0.0, 10.6, -FZ - 1.8), (0, 0, -1), 2.0, 2.35, 0.2, IRONW, seg=16)
# каменистый сад перед оранжереей
FQ.box(-FX - 2.8, FX + 2.8, -0.1, 0.0, -FZ - 2.8, -FZ - 0.9, GRAVEL)
FQ.box(-1.6, 1.6, 0.0, 0.04, -FZ - 2.88, -FZ - 0.9, STONE)
F.objects(True)
for (x, h, arms) in ((-14.6, 7.0, 2), (-9.0, 5.0, 1), (10.4, 8.0, 2), (15.8, 4.6, 1)):
    saguaro(FS, x, -FZ - 2.0, 0.0, h, arms)
for (x, r) in ((-12.0, 0.7), (-5.0, 0.6), (5.4, 0.8), (13.2, 0.55)):
    barrel_cactus(FS, x, -FZ - 1.6, 0.0, r)
for x in (-7.0, 7.8):
    opuntia(FS, x, -FZ - 2.4, 0.0, 0.7)
for (x, w, h) in ((-16.6, 1.2, 0.9), (-3.6, 0.8, 0.6), (3.8, 1.0, 0.7), (12.0, 0.7, 0.5)):
    FS.prism_xz(K.octa(x, -FZ - 2.4, w, w * 0.7, w * 0.3), 0.0, h, STONE2)
FS.box(-17.6, -17.4, 0.0, 2.6, -FZ - 1.4, -FZ - 1.2, WOOD)
FS.box(-18.4, -16.6, 2.0, 3.0, -FZ - 1.45, -FZ - 1.35, "F4ECD8")
FS.prism_xy([(-17.8, 2.2), (-17.2, 2.2), (-17.5, 2.8)], -FZ - 1.48, -FZ - 1.45, CACT)
F.objects(False)

# ══ ИНТЕРЬЕР: пустынный сад под арками ════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.4
S.interior(F, "E8F0EA", SAND, "DCEAE6", IRONW2, wain=(1.6, STONE2), beams=None)
for k in range(6):  # белые арочные рёбра потолка
    z = -13.0 + 4.0 * k
    pts = [(-W + 0.9 + (2 * W - 1.8) * j / 12, C - 0.3 - 3.0 * (-1 + 2 * j / 12) ** 2) for j in range(13)]
    for a, b in zip(pts, pts[1:]):
        beam(IS, (a[0], a[1], z), (b[0], b[1], z), 0.35, 0.35, IRONW, up=(0, 0, 1))
for idx, (axis, fixed, out, half) in enumerate(B.WALLS[:3]):  # стёкла-переплёт на стенах выше панели
    for k in range(int(2 * half // 3.0)):
        a = -half + 3.0 * k + 1.5
        slab(IS, axis, fixed, out, 0.95, a - 0.1, a + 0.1, 1.6, C - 2.6, IRONW)
F.objects(True)
for s in (-1, 1):  # песчаные грядки с кактусами вдоль стен
    x0 = s * (W - 0.88)
    x1 = x0 - s * 5.0
    IR.box(*sorted((x0, x1)), 0.0, 0.8, -13.5, 6.0, STONE)
    IS.box(*sorted((x0 - s * 0.1, x1 + s * 0.3)), 0.8, 0.9, -13.2, 5.7, SAND)
    for k in range(4):
        z = -11.8 + 5.0 * k
        xx = x0 - s * 2.6
        if k % 2 == 0:  # в зале только низкие кактусы: высокий кактус здесь один — экспонат
            barrel_cactus(IS, xx + s * 0.6, z + 0.6, 0.9, 1.1)
            opuntia(IS, xx - s * 0.9, z - 0.8, 0.9, 0.9)
        else:
            barrel_cactus(IS, xx - s * 0.8, z, 0.9, 0.8)
            opuntia(IS, xx + s * 0.6, z + 1.2, 0.9, 0.6)
        IS.prism_xz(K.octa(xx + s * 1.2, z - 1.6, 0.7, 0.5, 0.2), 0.9, 1.4, STONE2)
# сухое русло с мостиком у дальней стены
IQ.box(-12.0, 12.0, 0.02, 0.05, ZF + 2.6, ZF + 5.4, GRAVEL)
for k in range(9):
    IS.prism_xz(K.octa(-11.0 + 2.7 * k, ZF + 4.0 + 0.6 * math.sin(k), 0.5, 0.4, 0.15), 0.05, 0.35, STONE2)
for k in range(7):
    t = k / 6
    y = 0.6 + 0.9 * math.sin(math.pi * t)
    IS.box(-2.4, 2.4, y - 0.15, y, ZF + 1.6 + 4.6 * t - 0.35, ZF + 1.6 + 4.6 * t + 0.35, WOOD)
for e in (-2.3, 2.3):
    for k in range(4):
        t = k / 3
        IS.box(e - 0.08, e + 0.08, 0.6 + 0.9 * math.sin(math.pi * t), 1.8 + 0.9 * math.sin(math.pi * t), ZF + 1.6 + 4.6 * t - 0.08,
               ZF + 1.6 + 4.6 * t + 0.08, WOOD)
# скамья и таблички
IS.box(6.0, 10.0, 1.4, 1.7, 7.0, 8.0, WOOD)
for x in (6.4, 9.6):
    IS.box(x - 0.2, x + 0.2, 0.0, 1.4, 7.2, 7.8, IRONW2)
F.objects(False)
for k, (x, z) in enumerate(((-10.6, 7.6), (10.6, -12.0), (-10.6, -12.0))):
    IS.box(x - 0.08, x + 0.08, 0.9, 2.2, z - 0.08, z + 0.08, WOOD)
    IS.box(x - 0.6, x + 0.6, 2.2, 2.9, z - 0.04, z + 0.04, "F4ECD8")
for x, z in ((-4.0, -9.0), (4.0, -9.0), (0.0, 4.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.2, C - 2.0, z - 0.03, z + 0.03, "4A4A50")
    D.lantern(IS, IG, x, C - 4.2, z, s=1.0, cap=IRONW2, light="FFF4D8")
# постамент: круглая каменная клумба с песком и галькой
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, TOP - 0.1, STONE)
for k in range(16):
    a = 2 * math.pi * (k + 0.5) / 16
    IS.box(px + 4.0 * math.cos(a) - 0.05, px + 4.0 * math.cos(a) + 0.05, 0.2, TOP - 0.2, pz + 4.0 * math.sin(a) - 0.05,
           pz + 4.0 * math.sin(a) + 0.05, STONE2)
IS.prism_xz(K.ngon(px, pz, 3.6, 16), TOP - 0.1, TOP, SAND)
F.objects(True)
for k in range(10):
    a = 2 * math.pi * k / 10
    IS.prism_xz(K.octa(px + 3.2 * math.cos(a), pz + 3.2 * math.sin(a), 0.35, 0.25, 0.1), TOP, TOP + 0.2, (STONE2, GRAVEL, "8A7A66")[k % 3])
F.objects(False)
B.lift_leaves(IS, IRONW2, CACT)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, PANE, GRAVEL, IRONW2, top=16.0)
SL.box(-6.5, 6.5, 0.0, 16.4, -FZ - 2.1, -FZ, IRONW)
SL.prism_xz(K.ngon(-14.6, -FZ - 2.0, 0.9, 4), 0.0, 7.0, CACT)
SL.prism_xz(K.ngon(10.4, -FZ - 2.0, 1.0, 4), 0.0, 8.0, CACT)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 2100, (1.0, 0.98, 0.92)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.98, 0.94)),
                                                   ("Sun", (0, 15, -12), 800, (1.0, 0.95, 0.8))])
