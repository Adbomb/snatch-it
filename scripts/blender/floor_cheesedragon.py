"""Этаж «Сырный дракон» музея-небоскрёба (десятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — альпийская сыроварня у драконьей пещеры. Снаружи — шале: каменный цоколь из крупных валунов,
деревянный верх с резным балконом, ящики с красной геранью, глубокий свес крыши на резных кронштейнах, кованая
вывеска-дракон с висящей головкой сыра, справа — вход в пещеру с каменной аркой и золотыми «чешуйками», тележка
с головками сыра, бидоны, колокольчик, поленница. Внутри — сырный погреб: каменные своды, стеллажи от пола до
потолка с головками сыра, медный чан с мешалкой, гнездо с золотыми драконьими яйцами в соломе, драконья
чешуя-мозаика на дальней стене, фонари; экспонат — на гигантской головке сыра с дырками.
Запуск: blender --background --factory-startup --python scripts/blender/floor_cheesedragon.py -- <репо> <превью>
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

STONE, STONE2, STONE3, WOOD, WOOD2, WOOD3 = "A8A298", "8A847A", "6A645C", "B07A44", "8A5A30", "5E3C20"
CHEESE, CHEESE2, HOLE, RED, GREEN, COPPER = "F6CE4A", "E2A830", "C88A20", "D83A3A", "3E8A3A", "C8743A"
IRON, GOLD, STRAW, WHITE, GLASS = "3A3A40", "F2B830", "D8B860", "F4F0E4", "FFE8B8"

F = B.Floor("DR", "CheeseDragon", quiet=(STONE2, "B0A890", "8A7A60"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def wheel(p, x, z, y, r, h, holes=True, axis="y"):
    """Головка сыра с дырками на боку и сверху."""
    p.prism_xz(K.ngon(x, z, r, 10), y, y + h, CHEESE)
    p.prism_xz(K.ngon(x, z, r * 1.02, 10), y + h * 0.45, y + h * 0.55, CHEESE2)
    if holes:
        for k in range(3):
            a = 2 * math.pi * k / 3 + x
            p.prism_xz(K.ngon(x + r * 0.5 * math.cos(a), z + r * 0.5 * math.sin(a), r * 0.13, 6), y + h, y + h + 0.03, HOLE)


def flowers(p, x0, x1, y, z):
    p.box(x0, x1, y, y + 0.7, z - 0.5, z + 0.5, WOOD2)
    n = int((x1 - x0) / 0.6)
    for k in range(n):
        x = x0 + 0.3 + 0.6 * k
        p.prism_xz(K.ngon(x, z, 0.3, 5), y + 0.7, y + 1.1, GREEN)
        p.prism_xz(K.ngon(x + 0.1, z - 0.1, 0.18, 5), y + 1.1, y + 1.3, RED)


# ══ ФАСАД: шале и пещера ══════════════════════════════════════════════════════════════════════════════════════
S.facade(F, WOOD, STONE2, WOOD3, "B0A890", "4A3A2A", roof="hip", roof_col="6A4A3A", top=15.4, boards=(1.0, WOOD2),
         side=S.side_windows(F, WHITE, GLASS, kind="rect", y0=8.6, y1=11.8, w=2.4, xs=(-7.20, 0.80, 8.80)))
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # каменный цоколь: валуны спереди, крупная кладка сбоку и сзади
    if fi == 1:  # сзади — три ряда кладки разного тона (бюджет фасада)
        for j in range(3):
            slab(FR, axis, fixed, out, 1.08 + 0.06 * (j % 2), -half, half, 1.0 + 1.6 * j, 2.6 + 1.6 * j, (STONE, STONE2, STONE)[j])
        continue
    if fi > 1:  # с боков — крупные блоки вразбежку (не сплошная серая плита)
        slab(FR, axis, fixed, out, 1.0, -half, half, 1.0, 5.8, STONE3)
        n = int(2 * half // 6.0)
        step = 2 * half / n
        for j in range(3):
            y = 1.0 + 1.6 * j
            for k in range(n + j % 2):
                a0 = max(-half + step * (k - 0.5 * (j % 2)), -half)
                a1 = min(a0 + step if a0 > -half else -half + step * (k + 1 - 0.5 * (j % 2)), half)
                slab(FR, axis, fixed, out, 1.08 + 0.06 * ((k + j) % 2), a0 + 0.06, a1 - 0.06, y + 0.06, y + 1.54,
                     (STONE, STONE2)[(k + j) % 2])
        continue
    n = int(2 * half // 2.2)
    for k in range(n):
        a = -half + 2 * half * k / n
        for j in range(3):
            y = 1.0 + 1.6 * j
            slab(FR, axis, fixed, out, 1.05 + 0.1 * ((k + j) % 2), a + 0.05 + (0.6 if j % 2 else 0.0), a + 2 * half / n - 0.05, y + 0.05, y + 1.55,
                 (STONE, STONE2, STONE3)[(k + j) % 3])
# окна шале со ставнями, резной балкон, ящики с геранью
for x in (-2.0, 4.6, 11.2):
    S.window(F, "z", -FZ, -1, x, 7.4, 11.4, 2.4, WHITE, GLASS, kind="rect")
    for e in (-1, 1):
        x0 = x - 1.2 if e < 0 else x + 2.4
        FS.box(x0 + 0.05, x0 + 1.15, 7.2, 11.6, -FZ - 1.05, -FZ - 0.88, GREEN)
        FS.box(x0 + 0.2, x0 + 1.0, 9.2, 9.5, -FZ - 1.1, -FZ - 1.05, WHITE)
FS.box(-4.0, 15.6, 6.6, 6.9, -FZ - 2.6, -FZ - 0.88, WOOD2)
for k in range(24):
    x = -3.8 + 19.2 * k / 23
    FS.prism_xy([(x - 0.3, 6.9), (x + 0.3, 6.9), (x + 0.2, 7.6), (x + 0.32, 8.2), (x - 0.32, 8.2), (x - 0.2, 7.6)], -FZ - 2.56, -FZ - 2.44, WOOD)
FS.box(-4.0, 15.6, 8.2, 8.45, -FZ - 2.65, -FZ - 2.35, WOOD3)
for x in (-3.6, 15.2):
    beam(FS, (x, 6.6, -FZ - 2.4), (x, 4.6, -FZ - 0.9), 0.3, 0.3, WOOD3)
flowers(FS, -1.6, 2.0, 8.45, -FZ - 2.5)
flowers(FS, 10.6, 14.6, 8.45, -FZ - 2.5)
# резные кронштейны под свесом крыши
for k in range(9):
    x = -FX + 2.0 + (2 * FX - 4.0) * k / 8
    FS.prism_zy([(-FZ - 0.9, 15.4), (-FZ - 2.2, 15.9), (-FZ - 2.2, 16.1), (-FZ - 0.9, 13.8)], x - 0.18, x + 0.18, WOOD3)
# вход в сыроварню под навесом
FS.box(5.0, 9.0, 1.0, 6.2, -FZ - 1.1, -FZ - 0.88, WOOD3)
FS.box(5.3, 8.7, 1.0, 5.9, -FZ - 1.2, -FZ - 1.1, WOOD2)
for k in range(3):
    FS.box(5.3, 8.7, 2.0 + 1.3 * k, 2.15 + 1.3 * k, -FZ - 1.25, -FZ - 1.2, WOOD3)
# пещера дракона справа (по фасаду −x): каменная арка, тёмный зев, золотые чешуйки
CX, CW = -11.0, 7.0
FR.prism_xy([(CX - CW / 2 - 1.4, 1.0), (CX + CW / 2 + 1.4, 1.0)] + [(CX + (CW / 2 + 1.4) * math.cos(math.pi * k / 8), 6.0 + (CW / 2 + 1.4) * 0.9 * math.sin(math.pi * k / 8))
                                                                    for k in range(9)], -FZ - 2.0, -FZ - 0.88, STONE2)
FS.prism_xy([(CX - CW / 2, 1.0), (CX + CW / 2, 1.0)] + [(CX + CW / 2 * math.cos(math.pi * k / 8), 6.0 + CW / 2 * 0.9 * math.sin(math.pi * k / 8))
                                                        for k in range(9)], -FZ - 2.06, -FZ - 2.0, "1A1410")
for k in range(11):
    a = math.pi * k / 10
    FS.prism_xy(K.ngon(CX + (CW / 2 + 0.7) * math.cos(a), 6.0 + (CW / 2 + 0.7) * 0.9 * math.sin(a), 0.5, 4, turn=0.0),
                -FZ - 2.2, -FZ - 2.0, GOLD if k % 2 else CHEESE2)
for k in range(5):
    FG.prism_xy(K.ngon(CX - 1.6 + 0.8 * k, 3.0 + 0.4 * math.sin(k), 0.22, 6), -FZ - 2.1, -FZ - 2.06, "FFB040")
# кованая вывеска-дракон с головкой сыра
FS.box(1.0, 4.4, 13.2, 13.4, -FZ - 2.4, -FZ - 0.88, IRON)
FS.prism_zy([(-FZ - 2.4, 13.4), (-FZ - 1.4, 14.8), (-FZ - 0.9, 13.4)], 1.0, 1.2, IRON)
for k in range(5):
    t = k / 4
    FS.box(1.2 + 0.6 * k, 1.5 + 0.6 * k, 13.4, 13.6 + 0.6 * math.sin(math.pi * t), -FZ - 1.8, -FZ - 1.6, IRON)
FS.prism_xy([(4.4, 13.3), (5.2, 13.9), (4.8, 13.3), (5.2, 12.8)], -FZ - 1.8, -FZ - 1.6, IRON)
FS.box(3.0 - 0.03, 3.0 + 0.03, 11.4, 13.2, -FZ - 2.0, -FZ - 1.94, IRON)
wheel(FS, 3.0, -FZ - 1.97, 10.4, 0.9, 1.0, holes=False)
# тележка с сыром, бидоны, колокольчик, поленница
F.objects(True)
FS.box(-5.6, -2.4, 0.8, 1.4, -FZ - 2.8, -FZ - 1.4, WOOD2)
S.disc(FS, (-4.0, 0.7, -FZ - 2.9), (0, 0, -1), 0.75, 0.2, WOOD3, seg=10)
for k in range(3):
    wheel(FS, -5.0 + 1.2 * k, -FZ - 2.1, 1.4, 0.55, 0.45)
wheel(FS, -4.4, -FZ - 2.1, 1.85, 0.5, 0.4)
for x in (13.4, 14.4):
    FS.prism_xz(K.ngon(x, -FZ - 1.6, 0.4, 8), -0.1, 1.0, "C8CCD2")
    FS.prism_xz(K.ngon(x, -FZ - 1.6, 0.25, 8), 1.0, 1.4, "C8CCD2")
FS.loft([(16.3, 3.6, -FZ - 1.4), (16.9, 3.6, -FZ - 1.4), (16.9, 3.6, -FZ - 1.0), (16.3, 3.6, -FZ - 1.0)],
        [(16.1, 2.6, -FZ - 1.5), (17.1, 2.6, -FZ - 1.5), (17.1, 2.6, -FZ - 0.9), (16.1, 2.6, -FZ - 0.9)], GOLD)
for row in range(4):  # поленница у правого угла
    for k in range(5 - row % 2):
        x = -FX - 2.3 + 0.6 * k + 0.3 * (row % 2)
        FS.prism_xy(K.ngon(x, 0.2 + 0.55 * row, 0.27, 6), -FZ - 2.8, -FZ - 1.4, WOOD if (k + row) % 2 else WOOD2)
F.objects(False)

# ══ ИНТЕРЬЕР: сырный погреб ═══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.8
S.interior(F, STONE, "8A7A66", STONE3, WOOD3, wain=(1.4, STONE2), beams=None)
for k in range(6):  # каменные своды-рёбра
    z = -13.0 + 4.2 * k
    pts = [(-W + 0.9 + (2 * W - 1.8) * j / 12, C - 0.4 - 4.0 * (-1 + 2 * j / 12) ** 2) for j in range(13)]
    for a, b in zip(pts, pts[1:]):
        beam(IR, (a[0], a[1], z), (b[0], b[1], z), 0.9, 0.9, STONE2, up=(0, 0, 1))
F.objects(True)
for s in (-1, 1):  # стеллажи с головками сыра вдоль боковых стен
    x0 = s * (W - 0.88)
    x1 = x0 - s * 2.6
    for z in (-13.0, -6.0, 1.0):
        IS.box(*sorted((x1, x1 + s * 0.3)), 0.0, 12.0, z - 0.15, z + 0.15, WOOD3)
        IS.box(*sorted((x1, x1 + s * 0.3)), 0.0, 12.0, z + 5.85, z + 6.15, WOOD3)
    for y in (0.4, 3.2, 6.0, 8.8, 11.6):
        IS.box(*sorted((x0, x1)), y - 0.2, y, -13.0, 7.0, WOOD2)
        if y < 11:
            for k in range(5):
                wheel(IS, x0 - s * 1.3, -11.6 + 3.8 * k, y, 1.1, 0.8, holes=k % 2 == 0)
# медный чан с мешалкой у дальней стены
VX, VZ = 7.0, ZF + 3.6
IR.loft([(VX + 2.0 * math.cos(a), 0.0, VZ + 2.0 * math.sin(a)) for a in [2 * math.pi * k / 14 for k in range(14)]],
        [(VX + 2.6 * math.cos(a), 3.6, VZ + 2.6 * math.sin(a)) for a in [2 * math.pi * k / 14 for k in range(14)]], COPPER)
IS.prism_xz(K.ngon(VX, VZ, 2.75, 14), 3.6, 3.9, "A85A2A")
IS.prism_xz(K.ngon(VX, VZ, 2.4, 14), 3.4, 3.5, "F8F0D0")
beam(IS, (VX - 0.6, 3.2, VZ), (VX + 1.6, 7.2, VZ - 0.4), 0.2, 0.2, WOOD3)
# гнездо с золотыми драконьими яйцами в соломе
NX, NZ = -7.0, ZF + 3.6
IS.prism_xz(K.octa(NX, NZ, 3.0, 2.4, 1.0), 0.0, 0.6, STRAW)
S.annulus(IS, (NX, 0.6, NZ), (0, 1, 0), 1.6, 2.6, 0.6, STRAW, seg=12)
for k in range(3):
    a = 2 * math.pi * k / 3
    ex, ez = NX + 0.8 * math.cos(a), NZ + 0.7 * math.sin(a)
    IS.prism_xz(K.octa(ex, ez, 0.55, 0.55, 0.2), 0.6, 1.4, GOLD)
    IS.prism_xz(K.octa(ex, ez, 0.38, 0.38, 0.14), 1.4, 1.9, GOLD)
F.objects(False)
for j in range(4):  # драконья чешуя-мозаика на дальней стене: тёмный сланец и медь — жёлтый дракон не тонет в золоте
    for k in range(10):
        x = -6.75 + 1.5 * k + (0.75 if j % 2 else 0.0)
        y = 8.0 + 1.1 * j
        if abs(x) < 7.2:
            IS.prism_xy([(x - 0.7, y + 0.6), (x + 0.7, y + 0.6), (x + 0.5, y - 0.2), (x, y - 0.6), (x - 0.5, y - 0.2)], ZF + 0.88, ZF + 1.0,
                        (STONE3, "4E4840", "7A5A3A")[(j + k) % 3])
for x, z in ((-5.0, -8.0), (5.0, -8.0), (0.0, 4.0)):
    IS.box(x - 0.03, x + 0.03, C - 4.2, C - 2.4, z - 0.03, z + 0.03, IRON)
    D.lantern(IS, IG, x, C - 5.2, z, s=1.0, cap=IRON, light="FFD080")
# постамент: гигантская головка сыра с дырками
px, pz = PED
# тёмная дубовая бочка с железными обручами и сланцевой доской — жёлтый экспонат не сливается с постаментом
IR.prism_xz(K.ngon(px, pz, 4.0, 18), 0.0, TOP - 0.3, "6A4428")
for y in (0.35, TOP - 0.75):
    IS.prism_xz(K.ngon(px, pz, 4.06, 18), y, y + 0.22, "3A3A40")
IS.prism_xz(K.ngon(px, pz, 4.15, 18), TOP - 0.3, TOP, "3A3640")
B.lift_leaves(IS, WOOD3, CHEESE)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, WOOD, "B0A890", "6A4A3A", top=15.4, roof="hip")
SL.box(-FX, FX, -0.1, 5.8, -FZ - 0.4, -FZ, STONE2)
SL.box(-4.0, 15.6, 6.6, 8.4, -FZ - 2.6, -FZ, WOOD2)

F.build(exhibit=(PED[0], TOP, PED[1], 2.3), lamps=[("Hall", (0, 14, 6), 1500, (1.0, 0.9, 0.75)),
                                                   ("Spot", (0, 13, -3), 3800, (1.0, 0.96, 0.86)),
                                                   ("Gold", (-7, 3, -12), 700, (1.0, 0.8, 0.3))])
