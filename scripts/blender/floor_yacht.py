"""Этаж «Кит-бархан» музея-небоскрёба (десятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — клуб песчаных яхт на краю дюн. Снаружи — бело-синий эллинг из досок с широкими воротами под
двускатным фронтоном, во фронтоне — штурвал-эмблема, по бокам — медные хвосты кита, ряды круглых окошек-иллюминаторов,
мачта с сигнальными флажками, у ворот — две песчаные яхты на колёсах с парусами, бухты каната, якорь, буи,
спасательные круги на стене, песок волнами. Внутри — парусная мастерская: паруса и флаги под потолком, корпус
лодки на стапеле из рёбер-шпангоутов, стол с картой дюн и компасом, модели яхт на полках, бухты канатов,
вёсла на стене; экспонат — на «волне» из песка с палубными досками.
Запуск: blender --background --factory-startup --python scripts/blender/floor_yacht.py -- <репо> <превью>
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

WHITE, WHITE2, NAVY, NAVY2, SKY, SAND = "F4F2EC", "D8D4CA", "24406E", "1A2E52", "6AB0E0", "E6CC92"
SAND2, WOOD, WOOD2, COPPER, RED, YEL = "CDB078", "B08A5A", "7A5A3A", "C87A40", "D84A3A", "F2C83A"
ROPE, SAIL, GLASS = "D8C090", "F8F4E8", "C8E8F8"

F = B.Floor("DW", "DuneWhale", quiet=(SAND2, SAND, "9AB0C8"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def sand_yacht(p, x, z, y, s, hull, sail):
    """Песчаная яхта: корпус-лодочка, поперечина с колёсами, мачта, треугольный парус (вдоль x)."""
    p.loft([(x - 2.0 * s, y + 0.8 * s, z - 0.4 * s), (x + 2.2 * s, y + 0.8 * s, z - 0.15 * s), (x + 2.2 * s, y + 0.8 * s, z + 0.15 * s),
            (x - 2.0 * s, y + 0.8 * s, z + 0.4 * s)],
           [(x - 2.0 * s, y + 1.3 * s, z - 0.5 * s), (x + 2.4 * s, y + 1.3 * s, z - 0.1 * s), (x + 2.4 * s, y + 1.3 * s, z + 0.1 * s),
            (x - 2.0 * s, y + 1.3 * s, z + 0.5 * s)], hull)
    p.box(x - 0.6 * s, x - 0.3 * s, y + 0.7 * s, y + 0.9 * s, z - 1.4 * s, z + 1.4 * s, WOOD2)
    for e in (-1, 1):
        S.disc(p, (x - 0.45 * s, y + 0.5 * s, z + e * 1.45 * s), (0, 0, e), 0.5 * s, 0.15 * s, "2A2A30", seg=10)
    S.disc(p, (x + 1.9 * s, y + 0.4 * s, z - 0.1 * s), (0, 0, 1), 0.4 * s, 0.2 * s, "2A2A30", seg=10)
    p.box(x - 0.1 * s, x + 0.1 * s, y + 1.3 * s, y + 6.0 * s, z - 0.1 * s, z + 0.1 * s, WOOD2)
    p.prism_xy([(x + 0.1 * s, y + 6.0 * s), (x + 0.1 * s, y + 1.6 * s), (x + 2.8 * s, y + 1.6 * s)], z - 0.04, z + 0.04, sail)


def coil(p, x, z, y, r):
    for k in range(3):
        S.annulus(p, (x, y + 0.2 * k, z), (0, 1, 0), r * 0.4, r, 0.2, ROPE, seg=10)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, WHITE, NAVY, NAVY, SAND, "2A3A5A", roof="hip", roof_col=NAVY2, top=15.6, boards=(1.0, WHITE2),
         side=S.side_windows(F, NAVY, GLASS, kind="rect", y0=8.0, y1=11.6, w=2.4, xs=(-13.20, -7.20, -1.20, 4.80, 10.80)))
# двускатный фронтон над широкими воротами
FR.prism_xy([(-9.0, 9.6), (9.0, 9.6), (0.0, 15.4)], -FZ - 1.2, -FZ - 0.88, WHITE)
for e in (-1, 1):
    beam(FS, (e * 9.4, 9.4, -FZ - 1.4), (0.0, 15.8, -FZ - 1.4), 0.6, 0.4, NAVY)
FS.box(-8.2, 8.2, 1.0, 9.4, -FZ - 0.96, -FZ - 0.88, NAVY2)
for k in range(8):  # створки ворот из досок со скобами
    x0 = -8.0 + 2.0 * k
    FS.box(x0 + 0.05, x0 + 1.95, 1.0, 9.2, -FZ - 1.1, -FZ - 0.96, (NAVY, SKY)[k % 2] if k in (0, 7) else NAVY)
    FS.box(x0 + 0.05, x0 + 1.95, 2.0, 2.3, -FZ - 1.16, -FZ - 1.1, WHITE)
    FS.box(x0 + 0.05, x0 + 1.95, 7.8, 8.1, -FZ - 1.16, -FZ - 1.1, WHITE)
FS.box(-0.08, 0.08, 1.0, 9.2, -FZ - 1.2, -FZ - 1.1, WHITE)
# штурвал-эмблема во фронтоне
S.annulus(FS, (0.0, 12.0, -FZ - 1.25), (0, 0, -1), 1.1, 1.4, 0.2, COPPER, seg=14)
S.disc(FS, (0.0, 12.0, -FZ - 1.3), (0, 0, -1), 0.35, 0.25, COPPER, seg=8)
for k in range(8):
    a = math.pi * k / 4
    beam(FS, (0.35 * math.cos(a), 12.0 + 0.35 * math.sin(a), -FZ - 1.35), (1.9 * math.cos(a), 12.0 + 1.9 * math.sin(a), -FZ - 1.35),
         0.18, 0.18, COPPER, up=(0, 0, 1))
for k, x0 in enumerate((-14.2, 14.2)):  # медные хвосты кита по бокам вверху
    FS.prism_xy([(x0 - 0.3, 13.0), (x0 + 0.3, 13.0), (x0 + 0.2, 13.8), (x0 + 1.8, 14.6), (x0 + 1.5, 15.0), (x0, 14.3), (x0 - 1.5, 15.0),
                 (x0 - 1.8, 14.6), (x0 - 0.2, 13.8)], -FZ - 1.12, -FZ - 0.88, COPPER)
# иллюминаторы: по одному ряду из трёх с каждой стороны ворот, на разной высоте (без «пар глаз»)
for x, y in ((-16.6, 4.4), (-14.2, 4.4), (-11.8, 4.4), (11.8, 9.4), (14.2, 9.4), (16.6, 9.4)):
    FG.prism_xy(K.ngon(x, y, 0.8, 12), -FZ - 0.92, -FZ - 0.88, GLASS)
    S.annulus(FS, (x, y, -FZ - 0.88), (0, 0, -1), 0.8, 1.1, 0.25, NAVY, seg=12)
# спасательные круги на стене — на разной высоте: пара по бокам штурвала читалась «лицом»
for x, y in ((-10.4, 12.8), (10.4, 6.2)):
    S.annulus(FS, (x, y, -FZ - 0.9), (0, 0, -1), 0.5, 0.95, 0.3, RED, seg=12)
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4
        FS.box(x + 0.72 * math.cos(a) - 0.2, x + 0.72 * math.cos(a) + 0.2, y + 0.72 * math.sin(a) - 0.2,
               y + 0.72 * math.sin(a) + 0.2, -FZ - 1.24, -FZ - 1.2, WHITE)
# мачта с сигнальными флажками
MX = FX + 1.6
FS.prism_xz(K.ngon(MX, -FZ - 1.8, 0.2, 8), -0.1, 18.6, WOOD2)
FS.box(MX - 2.0, MX + 0.2, 15.0, 15.2, -FZ - 1.9, -FZ - 1.7, WOOD2)
for k in range(6):
    y = 17.8 - 1.3 * k
    t = k / 6
    FS.prism_xy([(MX - 0.2 - 3.0 * t, y), (MX - 0.2 - 3.0 * t - 1.0, y), (MX - 0.2 - 3.0 * t - 0.5, y - 0.9)], -FZ - 1.84, -FZ - 1.76,
                (RED, YEL, NAVY, WHITE, SKY, RED)[k])
beam(FS, (MX, 18.4, -FZ - 1.8), (MX - 4.0, 10.6, -FZ - 1.8), 0.05, 0.05, ROPE)
# песчаные яхты, бухты, якорь, буи, песчаные волны
F.objects(True)
sand_yacht(FS, -14.6, -FZ - 2.2, -0.1, 0.9, RED, SAIL)
sand_yacht(FS, 11.0, -FZ - 2.2, -0.1, 0.8, SKY, YEL)
coil(FS, -9.6, -FZ - 1.6, -0.1, 0.8)
coil(FS, 6.0, -FZ - 1.7, -0.1, 0.7)
FS.box(-6.0, -5.7, -0.1, 3.0, -FZ - 1.8, -FZ - 1.5, "4A5260")
FS.box(-7.0, -4.7, 2.4, 2.7, -FZ - 1.8, -FZ - 1.5, "4A5260")
for e in (-1, 1):
    beam(FS, (-5.85, 0.3, -FZ - 1.65), (-5.85 + e * 1.3, 1.2, -FZ - 1.65), 0.3, 0.3, "4A5260")
for k, x in enumerate((-2.6, 2.8)):
    FS.prism_xz(K.ngon(x, -FZ - 2.4, 0.55, 10), -0.1, 1.2, (RED, YEL)[k])
    FS.prism_xz(K.ngon(x, -FZ - 2.4, 0.6, 10), 0.4, 0.65, WHITE)
F.objects(False)
for k in range(5):
    FQ.prism_xz(K.octa(-14.0 + 7.0 * k, -FZ - 3.2, 2.6, 0.5, 0.4), -0.1, 0.15, SAND)

# ══ ИНТЕРЬЕР: парусная мастерская ═════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
S.interior(F, "EAE6DC", "C8A878", "3A5070", NAVY, wain=(3.0, WOOD), beams=(5, WOOD2), beam_dir="z")
for k in range(5):  # паруса и флаги под потолком
    x = -12.0 + 6.0 * k
    IS.prism_zy([(-12.0 + 1.5 * k, C - 1.2), (-4.0 + 1.5 * k, C - 1.2), (-8.0 + 1.5 * k, C - 6.0)], x - 0.04, x + 0.04,
                (SAIL, SKY, SAIL, YEL, SAIL)[k])
F.objects(True)
# корпус лодки на стапеле из шпангоутов вдоль левой стены
HX = -W + 4.0
for k in range(9):
    z = -12.0 + 2.0 * k
    t = 1.0 - abs(k - 4) / 5.0
    pts = [(HX + 2.4 * t * math.cos(a), 1.6 + 2.4 * t * math.sin(a)) for a in [math.pi + math.pi * j / 6 for j in range(7)]]
    for a, b in zip(pts, pts[1:]):
        beam(IS, (a[0], a[1] + 2.4 * t, z), (b[0], b[1] + 2.4 * t, z), 0.25, 0.25, WOOD)
IS.box(HX - 0.2, HX + 0.2, 1.2, 1.6, -12.4, 4.4, WOOD2)
ribs = []
for k in range(9):
    z = -12.0 + 2.0 * k
    t = 1.0 - abs(k - 4) / 5.0
    ribs.append([(HX + 2.4 * t * math.cos(a), 1.6 + 2.4 * t * math.sin(a) + 2.4 * t, z) for a in [math.pi + math.pi * j / 6 for j in range(7)]])
for k in range(8):  # стрингеры по всей длине и обшивка днища: корпус читается лодкой
    for j in range(7):
        w = 0.62 if 2 <= j <= 4 else 0.18
        beam(IS, ribs[k][j], ribs[k + 1][j], w, 0.14, WOOD2 if w < 0.5 else "C89A60", up=(0, 1, 0))
for z in (-11.0, -4.0, 3.0):
    IS.box(HX - 1.6, HX + 1.6, 0.0, 1.2, z - 0.3, z + 0.3, WOOD2)
# стол с картой дюн и компасом у правой стены
TX = W - 4.0
IS.box(TX - 2.0, TX + 2.0, 2.8, 3.1, -10.0, -4.0, WOOD)
for e in (-1.8, 1.8):
    for f in (-9.8, -4.2):
        IS.box(TX + e - 0.12, TX + e + 0.12, 0.0, 2.8, f - 0.12, f + 0.12, WOOD2)
IS.box(TX - 1.7, TX + 1.7, 3.1, 3.14, -9.6, -4.4, SAND)
for k in range(4):
    z0 = -9.2 + 1.2 * k
    IS.box(TX - 1.5, TX + 1.5, 3.14, 3.17, z0, z0 + 0.12, SAND2)
IS.prism_xz(K.ngon(TX + 0.8, -5.2, 0.45, 10), 3.14, 3.3, COPPER)
# полки с моделями яхт и бухты канатов у дальней стены
for y in (5.0, 8.4):
    IS.box(-8.0, 8.0, y - 0.2, y, ZF + 0.88, ZF + 2.0, WOOD2)
    for k in range(4):
        sand_yacht(IS, -6.0 + 4.0 * k, ZF + 1.4, y, 0.35, (RED, SKY, YEL, NAVY)[k], SAIL)
for x in (-11.0, 11.0, 13.4):
    coil(IS, x, ZF + 2.4, 0.0, 1.0)
for z0 in (-1.0, -9.0):  # мачта на козлах между корпусом и постаментом
    for e in (-0.7, 0.7):
        beam(IS, (-8.0 + e, 0.0, z0), (-8.0, 1.6, z0), 0.14, 0.14, WOOD2)
IS.prism_xy(K.ngon(-8.0, 1.9, 0.32, 8), -12.0, 1.0, WOOD)
for k, (x, z, col) in enumerate(((8.4, 6.0, SAIL), (9.6, 6.6, SKY), (9.0, 7.6, SAIL))):  # рулоны парусины
    IS.prism_zy(K.ngon(z, 0.45 + 0.8 * (k == 2), 0.45, 10), x - 1.2, x + 1.2, col)
# штурвал на дальней стене справа от полок
S.annulus(IS, (12.0, 10.0, ZF + 0.95), (0, 0, 1), 1.3, 1.55, 0.2, WOOD2, seg=16)
for k in range(8):
    a = math.pi * k / 4
    beam(IS, (12.0, 10.0, ZF + 1.05), (12.0 + 1.9 * math.cos(a), 10.0 + 1.9 * math.sin(a), ZF + 1.05), 0.14, 0.14, WOOD)
S.disc(IS, (12.0, 10.0, ZF + 0.95), (0, 0, 1), 0.35, 0.3, COPPER, seg=10)
F.objects(False)
for k in range(4):  # вёсла на правой стене
    z = 2.0 + 1.6 * k
    beam(IS, (W - 0.95, 4.0, z), (W - 0.95, 11.0, z + 0.4), 0.16, 0.16, WOOD)
    IS.box(W - 1.0, W - 0.9, 10.0, 12.0, z - 0.1, z + 0.9, WOOD2)
for x, z in ((-5.0, -6.0), (5.0, -6.0), (0.0, 5.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.0, C - 0.8, z - 0.03, z + 0.03, "3A3A40")
    D.lantern(IS, IG, x, C - 4.0, z, s=1.0, cap=NAVY, light="FFF0C8")
# постамент: песчаная «волна» с палубными досками
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, 0.4, NAVY)
for k in range(7):
    x0 = px - 3.5 + 1.0 * k
    IS.box(x0 + 0.04, x0 + 0.96, 0.4, TOP - 0.3, pz - 3.3 + abs(k - 3) * 0.25, pz + 3.3 - abs(k - 3) * 0.25, WOOD)
IS.prism_xz(K.octa(px, pz, 3.2, 3.0, 1.0), TOP - 0.3, TOP, SAND)
F.objects(True)
for k in range(5):
    a = 2 * math.pi * k / 5 + 0.3
    IS.prism_xz(K.octa(px + 3.7 * math.cos(a), pz + 3.7 * math.sin(a), 0.9, 0.5, 0.3), 0.4, 1.0, SAND2)
F.objects(False)
B.lift_leaves(IS, NAVY, WHITE)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, WHITE, SAND, NAVY2, top=15.6, roof="hip")
SL.prism_xy([(-9.0, 9.6), (9.0, 9.6), (0.0, 15.4)], -FZ - 1.2, -FZ, WHITE)

F.build(exhibit=(PED[0], TOP, PED[1], 2.9), lamps=[("Hall", (0, 14, 6), 1900, (1.0, 0.96, 0.9)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.98, 0.94)),
                                                   ("Sky", (0, 12, -12), 600, (0.7, 0.85, 1.0))])
