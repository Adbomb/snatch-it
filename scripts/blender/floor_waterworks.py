"""Этаж «Жук-капелька» музея-небоскрёба (девятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — старая водокачка оазиса. Снаружи — краснокирпичный машинный зал с высокими арочными окнами в
стальных переплётах, на правом углу — круглый клёпаный бак на стальных ногах с лестницей, по фасаду — синие трубы
с фланцами и красными вентилями, большая откатная дверь, эмблема-капля, манометр, питьевые краны с поддоном,
лужицы. Внутри — насосный зал: синий коллектор труб вдоль стен с фланцами и вентилями, три насоса с маховиками,
линия розлива с бутылками на ленте, высокие синие баки по углам, пульт с лампочками; экспонат — в круглой
чаше-бассейне с водой и кольцом фонтанчиков.
Запуск: blender --background --factory-startup --python scripts/blender/floor_waterworks.py -- <репо> <превью>
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

BRICK, BRICK2, STONE, PIPE, PIPE2, VALVE = "B04A3A", "8A3428", "D8CCB8", "2E7AC8", "1E5A9E", "E04030"
STEEL, STEEL2, DARK, WATER, GLASS, YEL = "A8B0B8", "6A727C", "2A2E34", "5AC8F0", "B8E0F0", "F2C230"
WHITE, TILE = "EEF2F4", "D8E4E8"

F = B.Floor("WT", "DropBeetle", quiet=(BRICK2, "B8B0A0", "6A727C"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def valve(p, c, n, r=0.6):
    """Красный вентиль-штурвал: обод и спицы."""
    S.annulus(p, c, n, r * 0.75, r, 0.12, VALVE, seg=10)
    S.disc(p, c, n, r * 0.2, 0.2, VALVE, seg=6)


def flange(p, axis, a, c1, c2, r):
    """Фланец на трубе вдоль axis в точке a."""
    if axis == "x":
        p.prism_zy(K.ngon(c2, c1, r, 10), a - 0.15, a + 0.15, PIPE2)
    else:
        p.prism_xy(K.ngon(c1, c2, r, 10), a - 0.15, a + 0.15, PIPE2)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, BRICK, STONE, STONE, "B8B0A0", "3A4048", roof="flat", roof_col=BRICK, top=16.2, pilaster=BRICK2,
         band=(9.4, 9.8, STONE), side=S.side_windows(F, STEEL2, GLASS, kind="arch", y0=10.6, y1=15.0, w=2.4, xs=(-9.20, -1.20, 6.80)))
for x in (-6.8, 6.8):  # пилястры между окнами
    FR.box(x - 0.6, x + 0.6, 1.0, 16.2, -FZ - 1.3, -FZ - 0.88, BRICK2)
# высокие арочные окна в стальных переплётах
for x in (-12.4, 9.2):
    S.window(F, "z", -FZ, -1, x - 2.0, 6.0, 15.0, 4.0, STEEL2, GLASS, kind="arch", mull=False)
    for k in range(1, 4):
        FS.box(x - 2.0, x + 2.0, 6.0 + 2.2 * k - 0.06, 6.0 + 2.2 * k + 0.06, -FZ - 1.0, -FZ - 0.9, STEEL2)
    FS.box(x - 0.06, x + 0.06, 6.0, 14.6, -FZ - 1.0, -FZ - 0.9, STEEL2)
# откатная дверь с рельсом и эмблема-капля над ней
FS.box(-4.4, 4.4, 1.0, 8.4, -FZ - 1.05, -FZ - 0.88, STEEL2)
for k in range(10):
    FS.box(-4.2, 4.2, 1.3 + 0.7 * k, 1.42 + 0.7 * k, -FZ - 1.12, -FZ - 1.05, STEEL)
FS.box(-5.6, 5.6, 8.5, 8.8, -FZ - 1.3, -FZ - 0.88, DARK)
FS.prism_xy([(0.0, 15.2)] + [(1.6 * math.cos(a), 12.2 + 1.6 * math.sin(a)) for a in
                             [math.radians(-30 - 240 * k / 10) for k in range(11)]], -FZ - 1.2, -FZ - 0.88, PIPE)
FS.prism_xy([(0.0, 14.5)] + [(1.1 * math.cos(a), 12.3 + 1.1 * math.sin(a)) for a in
                             [math.radians(-30 - 240 * k / 10) for k in range(11)]], -FZ - 1.3, -FZ - 1.2, WATER)
FS.prism_xy(K.octa(-0.4, 12.9, 0.25, 0.4, 0.1), -FZ - 1.35, -FZ - 1.3, WHITE)
# синие трубы по фасаду с фланцами, вентилями и манометром
PY = 9.0
FS.prism_zy(K.ngon(-FZ - 1.6, PY, 0.45, 10), -FX - 0.3, 15.0, PIPE)
for x in (-14.6, -9.0, 4.0, 12.0):
    flange(FS, "x", x, PY, -FZ - 1.6, 0.62)
for x, y0 in ((-15.4, -0.1), (7.6, -0.1)):
    FS.prism_xz(K.ngon(x, -FZ - 1.6, 0.45, 10), y0, PY, PIPE)
    FS.prism_xz(K.ngon(x, -FZ - 1.6, 0.62, 10), 3.0, 3.3, PIPE2)
F.objects(True)
valve(FS, (-15.4, 4.6, -FZ - 2.1), (0, 0, -1), 0.7)
valve(FS, (7.6, 5.4, -FZ - 2.1), (0, 0, -1), 0.6)
S.disc(FS, (-3.8 + 0.0, PY + 1.5, -FZ - 1.4), (0, 0, -1), 0.7, 0.2, WHITE, seg=12)
S.annulus(FS, (-3.8, PY + 1.5, -FZ - 1.45), (0, 0, -1), 0.65, 0.8, 0.12, STEEL2, seg=12)
beam(FS, (-3.8, PY + 1.5, -FZ - 1.62), (-3.5, PY + 1.95, -FZ - 1.62), 0.08, 0.04, VALVE, up=(0, 0, 1))
FS.box(-3.9, -3.7, PY + 0.4, PY + 0.8, -FZ - 1.7, -FZ - 1.5, PIPE2)
# питьевые краны с поддоном
FS.box(-9.8, -7.0, -0.1, 2.4, -FZ - 1.8, -FZ - 0.88, STONE)
FS.box(-9.6, -7.2, 2.4, 2.6, -FZ - 2.0, -FZ - 1.0, STEEL)
for x in (-9.2, -8.4, -7.6):
    beam(FS, (x, 3.4, -FZ - 1.0), (x, 3.4, -FZ - 1.6), 0.18, 0.18, STEEL)
    FG.box(x - 0.04, x + 0.04, 2.6, 3.3, -FZ - 1.64, -FZ - 1.56, WATER)
F.objects(False)
for (x, w) in ((-5.0, 1.4), (11.0, 1.0), (14.6, 0.8)):  # лужицы
    FG.prism_xz(K.octa(x, -FZ - 2.2, w, w * 0.6, w * 0.3), -0.1, -0.07, WATER)
# круглый клёпаный бак на стальных ногах с лестницей (правый угол по фасаду −x)
TX, TZ = -FX - 1.2, -FZ - 1.1  # бак не заходит за стены зала (x < −W, z < ZF)
F.objects(True)
for k in range(4):
    a = 2 * math.pi * k / 4 + math.pi / 4
    beam(FS, (TX + 2.0 * math.cos(a), -0.1, TZ + 2.0 * math.sin(a)), (TX + 1.7 * math.cos(a), 11.0, TZ + 1.7 * math.sin(a)), 0.3, 0.3, STEEL2)
for y in (3.6, 7.4):
    S.annulus(FS, (TX, y, TZ), (0, 1, 0), 1.6, 1.95, 0.2, STEEL2, seg=8)
F.objects(False)
FR.prism_xz(K.ngon(TX, TZ, 2.3, 14), 11.0, 17.0, PIPE)
for y in (11.6, 13.6, 15.6):
    FS.prism_xz(K.ngon(TX, TZ, 2.38, 14), y - 0.12, y + 0.12, PIPE2)
FS.cone([(x, 17.0, z) for x, z in K.ngon(TX, TZ, 2.4, 14)], (TX, 18.6, TZ), STEEL2)
for k in range(10):  # лестница на баке
    FS.box(TX - 0.5, TX + 0.5, 11.2 + 0.6 * k, 11.3 + 0.6 * k, TZ - 2.5, TZ - 2.42, DARK)
for e in (-1, 1):
    FS.box(TX + e * 0.5 - 0.06, TX + e * 0.5 + 0.06, 11.0, 17.2, TZ - 2.5, TZ - 2.42, DARK)

# ══ ИНТЕРЬЕР: насосный зал ════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
S.interior(F, TILE, "B8C4C8", "4A525C", PIPE2, wain=(3.2, WHITE), beams=(4, STEEL2), beam_dir="z")
for s in (-1, 1):  # коллектор труб вдоль стен
    x = s * (W - 1.6)
    for y in (6.0, 7.4):
        IS.prism_xy(K.ngon(x, y, 0.42, 10), ZF + 0.9, ZB - 0.9, PIPE if y < 7 else PIPE2)
        for z in (-12.0, -6.0, 0.0, 6.0, 12.0):
            IS.prism_xy(K.ngon(x, y, 0.6, 10), z - 0.15, z + 0.15, PIPE2)
F.objects(True)
for k in range(3):  # насосы с маховиками
    z = -11.0 + 6.5 * k
    x = -W + 4.2
    IS.box(x - 2.2, x + 2.2, 0.0, 1.0, z - 2.0, z + 2.0, DARK)
    IS.box(x - 1.6, x + 1.0, 1.0, 3.6, z - 1.2, z + 1.2, PIPE)
    IS.prism_zy(K.ngon(z, 2.3, 1.0, 12), x + 1.0, x + 2.0, PIPE2)
    S.disc(IS, (x + 2.1, 2.3, z), (1, 0, 0), 1.6, 0.3, STEEL2, seg=14)
    S.disc(IS, (x + 2.4, 2.3, z), (1, 0, 0), 0.4, 0.2, VALVE, seg=8)
    IS.prism_xz(K.ngon(x - 0.4, z, 0.4, 10), 3.6, 6.0, PIPE)
# линия розлива: лента на стойках и бутылки
LX = W - 3.6
IS.box(LX - 1.0, LX + 1.0, 2.6, 3.0, -13.0, 6.0, DARK)
for z in (-12.0, -6.0, 0.0, 5.0):
    IS.box(LX - 0.8, LX - 0.6, 0.0, 2.6, z - 0.1, z + 0.1, STEEL2)
    IS.box(LX + 0.6, LX + 0.8, 0.0, 2.6, z - 0.1, z + 0.1, STEEL2)
for k in range(14):
    z = -12.4 + 1.3 * k
    IG.prism_xz(K.ngon(LX, z, 0.3, 8), 3.0, 4.0, WATER)
    IG.prism_xz(K.ngon(LX, z, 0.14, 6), 4.0, 4.5, WATER)
    IS.prism_xz(K.ngon(LX, z, 0.16, 6), 4.5, 4.65, PIPE)
IS.box(LX - 1.4, LX + 1.4, 4.6, 7.6, -4.0, -1.0, STEEL)
IS.box(LX - 0.3, LX + 0.3, 3.6, 4.6, -2.8, -2.2, STEEL2)
for e in (-1, 1):  # стойки-портал разливочной головки: ящик стоит на полу, а не висит над лентой
    for z in (-3.8, -1.4):
        IS.box(LX + e * 1.2 - 0.12, LX + e * 1.2 + 0.12, 0.0, 4.6, z - 0.12, z + 0.12, STEEL2)
# высокие синие баки по углам у дальней стены
for x in (-12.6, 12.6):
    IR.prism_xz(K.ngon(x, ZF + 3.4, 2.4, 14), 0.0, 13.0, PIPE)
    for y in (2.0, 6.5, 11.0):
        IS.prism_xz(K.ngon(x, ZF + 3.4, 2.48, 14), y - 0.12, y + 0.12, PIPE2)
    IS.cone([(a, 13.0, b) for a, b in K.ngon(x, ZF + 3.4, 2.4, 14)], (x, 14.6, ZF + 3.4), STEEL2)
    valve(IS, (x - 2.5 if x > 0 else x + 2.5, 3.0, ZF + 3.4), (-1 if x > 0 else 1, 0, 0), 0.6)
F.objects(False)
# пульт с лампочками на дальней стене
IS.box(-6.0, 6.0, 0.0, 3.2, ZF + 0.88, ZF + 2.4, STEEL)
IS.box(-6.0, 6.0, 3.2, 8.0, ZF + 0.88, ZF + 1.2, DARK)
for j in range(3):
    for k in range(10):
        col = (VALVE, YEL, "5AE070", WATER)[int(rng(j, k) * 4)]
        IS.prism_xy(K.ngon(-5.0 + 1.1 * k, 4.2 + 1.2 * j, 0.22, 6), ZF + 1.2, ZF + 1.32, col)
for x, z in ((-6.0, 4.0), (6.0, 4.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.0, C - 0.8, z - 0.03, z + 0.03, DARK)
    D.lantern(IS, IG, x, C - 4.0, z, s=1.0, cap=STEEL2, light="E8F4FF")
# постамент: чаша-бассейн с водой и кольцом фонтанчиков
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.2, 16), 0.0, 0.9, STONE)
IS.prism_xz(K.ngon(px, pz, 3.6, 16), 0.9, 1.0, "8AA8B8")
IG.prism_xz(K.ngon(px, pz, 3.6, 16), 0.6, 0.85, WATER)
IR.prism_xz(K.ngon(px, pz, 1.6, 12), 0.6, TOP, STONE)
S.annulus(IS, (px, 0.9, pz), (0, 1, 0), 3.6, 4.3, 0.25, WHITE, seg=16)
for k in range(8):
    a = 2 * math.pi * k / 8
    IS.prism_xz(K.ngon(px + 2.6 * math.cos(a), pz + 2.6 * math.sin(a), 0.15, 6), 0.85, 1.05, STEEL2)
    IG.prism_xz(K.ngon(px + 2.6 * math.cos(a), pz + 2.6 * math.sin(a), 0.07, 6), 1.05, 2.2, WATER)
B.lift_leaves(IS, PIPE2, STONE)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, BRICK, "B8B0A0", BRICK, top=16.2)
SL.prism_xz(K.ngon(TX, TZ, 2.3, 8), 11.0, 17.0, PIPE)
SL.cone([(x, 17.0, z) for x, z in K.ngon(TX, TZ, 2.3, 8)], (TX, 18.6, TZ), STEEL2)

F.build(exhibit=(PED[0], TOP, PED[1], 3.6), lamps=[("Hall", (0, 14, 6), 1900, (0.92, 0.96, 1.0)),
                                                   ("Spot", (0, 13, -3), 3600, (0.98, 0.98, 1.0)),
                                                   ("Water", (0, 3, -3), 600, (0.5, 0.85, 1.0))])
