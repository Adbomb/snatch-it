"""Этаж «Черепаха-бархан» музея-небоскрёба (девятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — станция заповедника морских черепах на дюнах. Снаружи — бирюзовый дощатый дом смотрителей на сваях:
низ — решётка из перекрещённых реек между сваями, над ней — длинная веранда на столбах с верёвочными перилами,
лестница вниз к песку, зелёная вальмовая крыша, вывеска-панцирь из шестигранников, подзорная труба на треноге;
перед домом — песчаные дюны с колышками-флажками над гнёздами, черепашата ползут к полоске моря, спасательный
круг, табличка. Внутри — инкубатор: деревянные лотки с песком и черепашатами под красными лампами обогрева,
шкафы-инкубаторы с яйцами за стеклом, длинный аквариум с водорослями, мозаика панциря на стене;
экспонат — на песчаном бархане с ободом из шестигранных щитков.
Запуск: blender --background --factory-startup --python scripts/blender/floor_turtle.py -- <репо> <превью>
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

TEAL, TEAL2, WHITE, GREEN, GREEN2, SAND = "3AA8A0", "2A8880", "F4F0E6", "3E8A4A", "2E6A3A", "E8CC96"
SAND2, WOOD, WOOD2, ORANGE, SHELL, SHELL2 = "D2B47E", "B08A5A", "7A5A3A", "F08A30", "8A9A4A", "5E7A36"
SEA, RED, ROPE, EGG, GLASS = "3AB0E0", "E04A3A", "D8C090", "F4ECD8", "D8F0F0"

F = B.Floor("TH", "DuneTurtle", quiet=(SAND2, SAND, "A88A60"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def hexa(p, x, y, z, r, col, axis="z", t=0.1):
    pts = K.ngon(x, y, r, 6, turn=0.0)
    if axis == "z":
        p.prism_xy(pts, z, z + t, col)
    else:
        p.prism_xz(K.ngon(x, z, r, 6, turn=0.0), y, y + t, col)


def baby(p, x, z, y, s=0.5, a=0.0):
    """Черепашонок: панцирь-купол, голова, ласты."""
    p.prism_xz(K.octa(x, z, s, s * 0.85, s * 0.3), y, y + s * 0.35, SHELL)
    p.prism_xz(K.octa(x, z, s * 0.72, s * 0.62, s * 0.24), y + s * 0.35, y + s * 0.6, SHELL2)  # купол панциря ярусами
    p.prism_xz(K.octa(x, z, s * 0.38, s * 0.32, s * 0.12), y + s * 0.6, y + s * 0.78, SHELL)
    ca, sa = math.cos(a), math.sin(a)
    hx, hz = x + ca * s * 1.2, z + sa * s * 1.2
    p.box(hx - s * 0.25, hx + s * 0.25, y + 0.05, y + s * 0.4, hz - s * 0.25, hz + s * 0.25, "9AB86A")
    for f, side, ln in ((0.45, 1, 0.9), (0.45, -1, 0.9), (-0.55, 1, 0.55), (-0.55, -1, 0.55)):  # ласты
        cx = x + ca * s * f - sa * s * side * 0.95
        cz = z + sa * s * f + ca * s * side * 0.95
        p.prism_xz(K.ngon(cx, cz, s * 0.26 * ln + 0.04, 5), y, y + 0.07, "8AA85A")


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
DECK = 5.0
S.facade(F, TEAL, WOOD2, WHITE, SAND, "6A5038", roof="hip", roof_col=GREEN, top=16.0, boards=None,
         band=(DECK - 0.3, DECK, WHITE), side=S.side_windows(F, WHITE, GLASS, kind="rect", y0=8.0, y1=12.0, w=2.6, xs=(-11.30, -3.30, 4.70)))
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # дощатая обшивка: горизонтальные рейки
    for k in range(int((16.0 - DECK) // 0.7)):
        y = DECK + 0.35 + 0.7 * k
        B.slab(FS, axis, fixed, out, 0.93, -half, half, y - 0.04, y + 0.04, TEAL2)
# низ на сваях: решётка из перекрещённых реек
for k in range(9):
    x0 = -FX + 4.0 * k
    for e in (0, 1):
        beam(FS, (x0 + 4.0 * e, 1.0, -FZ - 1.0), (x0 + 4.0 * (1 - e), DECK - 0.3, -FZ - 1.0), 0.25, 0.1, WHITE, up=(0, 0, 1))
for k in range(10):
    x = -FX + 4.0 * k
    FS.box(x - 0.3, x + 0.3, -0.1, DECK, -FZ - 1.4, -FZ - 0.88, WOOD2)
# веранда на столбах с верёвочными перилами
FR.box(-FX - 0.2, FX + 0.2, DECK - 0.4, DECK, -FZ - 2.8, -FZ - 0.88, WOOD)
for k in range(12):
    x = -FX + 0.3 + (2 * FX - 0.6) * k / 11
    FS.box(x - 0.18, x + 0.18, -0.1, DECK - 0.4, -FZ - 2.6, -FZ - 2.3, WOOD2)
    FS.box(x - 0.12, x + 0.12, DECK, DECK + 2.6, -FZ - 2.7, -FZ - 2.5, WOOD2)
for y in (DECK + 1.2, DECK + 2.4):
    FS.box(-FX - 0.1, FX + 0.1, y - 0.06, y + 0.06, -FZ - 2.64, -FZ - 2.56, ROPE)
# дверь, большие окна, вывеска-панцирь
FS.box(-1.8, 1.8, DECK, DECK + 6.4, -FZ - 1.0, -FZ - 0.88, WHITE)
FS.box(-1.4, 1.4, DECK, DECK + 6.0, -FZ - 1.08, -FZ - 1.0, WOOD)
FG.box(-1.0, 1.0, DECK + 3.4, DECK + 5.4, -FZ - 1.12, -FZ - 1.08, GLASS)
for x in (-12.0, -7.0, 4.0, 9.0):
    S.window(F, "z", -FZ, -1, x, DECK + 2.0, DECK + 6.4, 3.0, WHITE, GLASS, kind="rect")
FS.box(-5.0, 5.0, DECK + 7.4, DECK + 10.4, -FZ - 1.1, -FZ - 0.88, WOOD)
FS.prism_xy(K.octa(0.0, DECK + 8.9, 3.0, 1.3, 0.8), -FZ - 1.25, -FZ - 1.1, SHELL2)
for k, (dx, dy) in enumerate(((0, 0), (-1.35, 0.42), (1.35, 0.42), (-1.35, -0.42), (1.35, -0.42), (-2.4, 0), (2.4, 0))):
    FS.prism_xy(K.ngon(dx, DECK + 8.9 + dy * 1.1, 0.55, 6, turn=0.0), -FZ - 1.4, -FZ - 1.25, SHELL if k % 2 else "A8B860")
# лестница с веранды к песку вдоль бока
for k in range(7):
    t = (k + 1) / 7
    z = -FZ - 2.4 + 6.4 * t
    FS.box(FX + 0.4, FX + 2.6, DECK * (1 - t) - 0.2, DECK * (1 - t), z - 0.5, z + 0.5, WOOD)
for e in (0.4, 2.6):
    beam(FS, (FX + e, DECK + 1.6, -FZ - 2.4), (FX + e, 1.6, -FZ + 4.0), 0.12, 0.12, ROPE)
# подзорная труба на треноге на веранде
F.objects(True)
for k in range(3):
    a = 2 * math.pi * k / 3
    beam(FS, (-8.0 + 0.7 * math.cos(a), DECK, -FZ - 1.9 + 0.5 * math.sin(a)), (-8.0, DECK + 2.4, -FZ - 1.9), 0.1, 0.1, "3A3A40")
beam(FS, (-8.6, DECK + 2.2, -FZ - 1.4), (-7.0, DECK + 3.0, -FZ - 2.6), 0.4, 0.4, "D8A840")
# дюны с колышками-флажками, черепашата, полоска моря, спасательный круг
for (x, w, h) in ((-12.0, 4.0, 1.0), (-3.0, 5.0, 1.3), (6.0, 3.6, 0.9)):
    FS.prism_xz(K.octa(x, -FZ - 2.0, w, 1.0, 0.8), -0.1, h * 0.5, SAND)
    FS.prism_xz(K.octa(x + 0.4, -FZ - 2.0, w * 0.6, 0.7, 0.5), h * 0.5, h, SAND2)
for k, x in enumerate((-13.4, -10.6, -4.6, -1.4, 5.0, 7.0)):
    FS.box(x - 0.06, x + 0.06, -0.1, 1.8, -FZ - 2.2, -FZ - 2.1, WOOD2)
    FS.prism_xy([(x + 0.06, 1.8), (x + 0.9, 1.55), (x + 0.06, 1.3)], -FZ - 2.17, -FZ - 2.13, ORANGE)
for k, x in enumerate((-17.2, 10.8, 13.2, 15.6)):  # черепашата ползут к морю — на песке перед ним, не над пустотой
    baby(FS, x, -FZ - 2.2 - 0.15 * rng(k, 4), -0.1, s=0.5, a=-math.pi / 2 + 0.4 * (rng(k, 3) - 0.5))
F.objects(False)
FG.box(-FX - 2.9, FX + 2.9, -0.12, -0.08, -FZ - 2.9, -FZ - 2.5, SEA)
F.objects(True)
S.annulus(FS, (15.2, DECK + 3.2, -FZ - 0.95), (0, 0, -1), 0.6, 1.1, 0.2, RED, seg=12)
for k in range(4):
    a = math.pi / 2 * k + math.pi / 4
    FS.box(15.2 + 0.85 * math.cos(a) - 0.22, 15.2 + 0.85 * math.cos(a) + 0.22, DECK + 3.2 + 0.85 * math.sin(a) - 0.22,
           DECK + 3.2 + 0.85 * math.sin(a) + 0.22, -FZ - 1.2, -FZ - 1.12, WHITE)
F.objects(False)

# ══ ИНТЕРЬЕР: инкубатор ═══════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
S.interior(F, "E8E2D0", "C8A878", WOOD2, TEAL, wain=(3.0, TEAL), beams=(5, WOOD2), beam_dir="z")
F.objects(True)
# лотки с песком и черепашатами под лампами вдоль боковых стен
for s in (-1, 1):
    for k in range(3):
        z = -11.0 + 6.4 * k
        x = s * (W - 4.0)
        IS.box(x - 2.4, x + 2.4, 0.0, 2.4, z - 2.2, z + 2.2, WOOD)
        IS.box(x - 2.2, x + 2.2, 2.4, 2.6, z - 2.0, z + 2.0, SAND)
        for j in range(3):
            baby(IS, x - 1.3 + 1.3 * j, z - 0.8 + 1.4 * rng(j, k, s), 2.6, s=0.6, a=rng(k, j) * 6.28)
        IS.box(x - 0.03, x + 0.03, 6.0, C - 0.8, z - 0.03, z + 0.03, "3A3A40")
        IS.prism_xz(K.ngon(x, z, 0.7, 8), 5.4, 6.0, "3A3A40")
        IG.prism_xz(K.ngon(x, z, 0.5, 8), 5.2, 5.4, "FF5A3A")
# шкафы-инкубаторы с яйцами у дальней стены
for x in (-12.0, -7.6, 7.6, 12.0):
    # открытый шкаф: задняя стенка, бока, крыша, цоколь, рама витрины — яйца на полках видны
    IS.box(x - 2.0, x + 2.0, 0.0, 7.6, ZF + 0.88, ZF + 1.1, WHITE)
    for e in (-1, 1):
        IS.box(*sorted((x + e * 2.0, x + e * 1.78)), 0.0, 7.6, ZF + 1.1, ZF + 3.2, WHITE)
    IS.box(x - 1.78, x + 1.78, 7.3, 7.6, ZF + 1.1, ZF + 3.2, WHITE)
    IS.box(x - 1.78, x + 1.78, 0.0, 0.9, ZF + 1.1, ZF + 3.2, WHITE)
    IG.box(x - 1.7, x + 1.7, 6.9, 7.0, ZF + 1.2, ZF + 2.9, "FFB070")  # лампа обогрева под крышей
    for y in (1.4, 3.6, 5.8):
        IS.box(x - 1.78, x + 1.78, y - 0.1, y, ZF + 1.1, ZF + 3.0, "C8C8C8")
        IS.box(x - 1.78, x + 1.78, y - 0.1, y + 0.12, ZF + 3.0, ZF + 3.2, WHITE)  # кромка полки — рама витрины
        for j in range(4):
            IS.prism_xz(K.octa(x - 1.2 + 0.8 * j, ZF + 2.1, 0.28, 0.28, 0.1), y, y + 0.45, EGG)
F.objects(False)
# длинный аквариум с водорослями над шкафами
IS.box(-5.0, 5.0, 2.0, 2.4, ZF + 0.88, ZF + 3.0, WOOD2)
IG.box(-4.8, 4.8, 2.4, 7.4, ZF + 1.0, ZF + 1.06, "7ACCE8")  # вода — фон за водорослями
for k in range(8):
    x = -4.2 + 1.2 * k
    IS.loft([(x - 0.15, 2.4, ZF + 1.8), (x + 0.15, 2.4, ZF + 1.8), (x + 0.15, 2.4, ZF + 1.9), (x - 0.15, 2.4, ZF + 1.9)],
            [(x + 0.3 * math.sin(k), 4.0 + 2.0 * rng(k, 7), ZF + 1.8), (x + 0.3 * math.sin(k) + 0.1, 4.0 + 2.0 * rng(k, 7), ZF + 1.8),
             (x + 0.3 * math.sin(k) + 0.1, 4.0 + 2.0 * rng(k, 7), ZF + 1.9), (x + 0.3 * math.sin(k), 4.0 + 2.0 * rng(k, 7), ZF + 1.9)], GREEN)
# мозаика панциря на дальней стене над аквариумом
for j in range(3):
    for k in range(7):
        hx = -5.4 + 1.8 * k
        hy = 9.6 + 1.6 * j + (0.8 if k % 2 else 0.0)
        hexa(IS, hx, hy, ZF + 0.88, 0.85, (SHELL, SHELL2, "A8B860")[(j + k) % 3], t=0.12)
for x, z in ((-6.0, 2.0), (6.0, 2.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.0, C - 0.8, z - 0.03, z + 0.03, "3A3A40")
    D.lantern(IS, IG, x, C - 4.0, z, s=1.0, cap=TEAL2, light="FFF0C8")
# постамент: песчаный бархан с ободом из шестигранных щитков
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 12, turn=0.0), 0.0, 0.5, SHELL2)
for k in range(12):
    a = 2 * math.pi * k / 12
    hexa(IS, px + 3.6 * math.cos(a), 0.5, pz + 3.6 * math.sin(a), 0.7, SHELL if k % 2 else "A8B860", axis="y", t=0.12)
IS.prism_xz(K.octa(px, pz, 3.4, 3.2, 1.2), 0.5, TOP - 0.3, SAND)
IS.prism_xz(K.octa(px, pz, 2.8, 2.6, 1.0), TOP - 0.3, TOP, SAND2)
B.lift_leaves(IS, TEAL2, WHITE)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, TEAL, SAND, GREEN, top=16.0, roof="hip")
SL.box(-FX - 0.2, FX + 0.2, DECK - 0.4, DECK, -FZ - 2.8, -FZ, WOOD)

F.build(exhibit=(PED[0], TOP, PED[1], 3.4), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.95, 0.88)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Heat", (-12, 5, -4), 600, (1.0, 0.5, 0.35))])
