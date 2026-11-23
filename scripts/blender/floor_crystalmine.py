"""Этаж «Кристальный скорпион» музея-небоскрёба (десятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — кристальная шахта в скале. Снаружи — скальный фасад из слоёв песчаника, деревянный портал штольни
с подпорками и вывеской-киркой, из штольни выходят рельсы с вагонеткой, полной самоцветов, на скале — друзы
кристаллов (фиолетовые, голубые, розовые), фонари на крюках, кирки и лопаты у стены, бочки, тачка с рудой,
леса-подъёмник с блоком и ведром. Внутри — пещера-жеода: стены с кристальными друзами, деревянные крепи-рамы
вдоль зала, рельсы с вагонеткой, светящиеся кристаллы-колонны, ящики с камнями, лампы на проводе;
экспонат — на половинке огромной жеоды: тёмная корка и кольцо кристаллов.
Запуск: blender --background --factory-startup --python scripts/blender/floor_crystalmine.py -- <репо> <превью>
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

ROCK, ROCK2, ROCK3, ROCK4, TIMBER, TIMBER2 = "B88A5E", "9A6E48", "D2A878", "7A5A40", "8A6038", "5E4026"
IRON, IRON2, PURPLE, BLUE, PINK, TEAL = "5A5E66", "3A3E46", "A060F0", "50C8F8", "F070C0", "40E0C0"
GOLD, LAMP, CAVE, CAVE2 = "F2C040", "FFD070", "5A4A5E", "40364A"
GEMS = (PURPLE, BLUE, PINK, TEAL)

F = B.Floor("CR", "CrystalScorpion", quiet=(ROCK2, "B0946C", "4A3E50"), bevel_min=1.2)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def crystal(p, x, y, z, h, w, col, lean=(0.0, 0.0)):
    """Кристалл: шестигранная призма с острием, наклон lean (dx, dz)."""
    base = [(x + w * math.cos(a), y, z + w * math.sin(a)) for a in [2 * math.pi * k / 6 for k in range(6)]]
    mid = [(x + lean[0] * 0.7 + w * math.cos(a), y + h * 0.75, z + lean[1] * 0.7 + w * math.sin(a)) for a in [2 * math.pi * k / 6 for k in range(6)]]
    p.loft(base, mid, col)
    p.cone(mid, (x + lean[0], y + h, z + lean[1]), col)


def druse(p, x, y, z, s, seed, out=(0.0, 0.0)):
    """Друза: 4–5 кристаллов веером."""
    for k in range(5):
        a = 2 * math.pi * k / 5 + seed
        r = 0.4 * s
        crystal(p, x + r * math.cos(a), y, z + r * math.sin(a), s * (1.2 + 0.8 * rng(k, seed)), 0.28 * s, GEMS[(k + int(seed * 3)) % 4],
                lean=(out[0] * s + 0.5 * s * math.cos(a), out[1] * s + 0.5 * s * math.sin(a)))


# ══ ФАСАД: скала со штольней ══════════════════════════════════════════════════════════════════════════════════
S.facade(F, ROCK, ROCK4, ROCK2, "B0946C", "3A2E40", roof="none", top=16.4,
         side=S.side_windows(F, TIMBER2, "2A2228", kind="slit", y0=8.0, y1=12.0, w=1.4, xs=(-13.20, -8.20, -3.20, 1.80, 6.80, 11.80)))
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # слои песчаника и рваный верх скалы
    for j, (y0, y1, col, d) in enumerate(((3.0, 5.4, ROCK2, 1.1), (7.6, 9.2, ROCK3, 1.3), (11.4, 13.6, ROCK2, 1.05))):
        n = 6
        for k in range(n):
            a0 = -half + 2 * half * k / n
            a1 = a0 + 2 * half / n
            dy = 0.5 * math.sin(k * 1.7 + j + fi)
            spans = [(a0, a1)]
            if fi == 0 and y0 + dy < 11.4:  # пласты обходят портал штольни, а не идут поперёк проёма
                spans = [(u0, u1) for u0, u1 in ((a0, min(a1, -5.0)), (max(a0, 5.0), a1)) if u1 - u0 > 0.3]
            for u0, u1 in spans:
                slab(FR, axis, fixed, out, d + 0.15 * (k % 2), u0, u1, y0 + dy, y1 + dy, col)
    for k in range(10):
        a0 = -half + 2 * half * k / 10
        h = 17.2 + 1.5 * rng(k, fi, 5)
        slab(FR, axis, fixed, out, 1.3 - 0.3 * (k % 2), a0, a0 + 2 * half / 10 + 0.05, 16.4, min(h, 18.9), ROCK if k % 2 else ROCK2)
# портал штольни: тёмный проём, подпорки, балка, вывеска-кирка
FS.box(-4.0, 4.0, 1.0, 9.0, -FZ - 0.92, -FZ - 0.88, "1E1820")
for e in (-1, 1):
    FR.box(e * 4.4 - 0.6, e * 4.4 + 0.6, 0.0, 9.8, -FZ - 2.0, -FZ - 0.88, TIMBER)
    beam(FS, (e * 4.4, 9.0, -FZ - 1.4), (e * 2.4, 11.0, -FZ - 1.4), 0.6, 0.5, TIMBER2)
FR.box(-5.6, 5.6, 9.8, 11.2, -FZ - 2.2, -FZ - 0.88, TIMBER)
FS.box(-3.2, 3.2, 11.6, 13.8, -FZ - 1.2, -FZ - 0.88, TIMBER2)
beam(FS, (-1.8, 12.0, -FZ - 1.3), (1.8, 13.4, -FZ - 1.3), 0.25, 0.15, TIMBER, up=(0, 0, 1))
FS.prism_xy([(0.9, 13.6), (2.4, 13.0), (1.2, 12.4), (0.6, 13.0)], -FZ - 1.35, -FZ - 1.25, IRON)
FS.prism_xy([(0.6, 13.0), (-0.6, 13.9), (0.2, 13.2)], -FZ - 1.35, -FZ - 1.25, IRON)
# рельсы со шпалами и вагонетка с самоцветами
for k in range(9):
    z = -FZ - 0.9 - 0.3 * k
    FS.box(-2.0, 2.0, -0.1, 0.1, z - 0.12, z + 0.12, TIMBER2)
for e in (-1.2, 1.2):
    FS.box(e - 0.08, e + 0.08, 0.1, 0.25, -FZ - 3.4, -FZ + 0.0, IRON)
F.objects(True)
FS.loft([(-1.6, 0.8, -FZ - 3.2), (1.6, 0.8, -FZ - 3.2), (1.6, 0.8, -FZ - 1.4), (-1.6, 0.8, -FZ - 1.4)],
        [(-1.9, 2.4, -FZ - 3.4), (1.9, 2.4, -FZ - 3.4), (1.9, 2.4, -FZ - 1.2), (-1.9, 2.4, -FZ - 1.2)], IRON)
for e in (-1.2, 1.2):
    for f in (-FZ - 2.9, -FZ - 1.7):
        S.disc(FS, (e * 1.4, 0.55, f), (1, 0, 0), 0.4, 0.15, IRON2, seg=8)
for k in range(6):
    crystal(FG, -1.2 + 0.5 * k, 2.2, -FZ - 2.3 + 0.3 * (k % 2), 0.9 + 0.3 * (k % 3), 0.22, GEMS[k % 4], lean=(0.1 * (k - 3), 0.0))
F.objects(False)
# друзы кристаллов на скале
for (x, y, s, sd) in ((-13.0, 5.6, 1.4, 0.3), (-8.2, 11.8, 1.0, 1.1), (9.6, 7.6, 1.2, 2.0), (14.6, 13.0, 1.0, 2.7), (-15.6, 14.4, 0.8, 3.3)):
    druse(FG, x, y, -FZ - 1.0, s, sd, out=(0.0, -0.9))  # растут из скалы: основание в камне
# фонари на крюках, кирки и лопаты, бочки, тачка с рудой, подъёмник
for x in (-6.0, 6.0):
    FS.box(x - 0.08, x + 0.08, 8.0, 8.2, -FZ - 1.8, -FZ - 0.88, IRON2)
    D.lantern(FS, FG, x, 7.0, -FZ - 1.7, s=1.0, cap=IRON2, light=LAMP)
F.objects(True)
for k, x in enumerate((-11.6, -11.0, -10.4)):
    beam(FS, (x, -0.1, -FZ - 1.2), (x + 0.4, 3.6, -FZ - 1.0), 0.14, 0.14, TIMBER)
    if k % 2:
        FS.box(x + 0.0, x + 0.9, 3.4, 3.6, -FZ - 1.15, -FZ - 0.95, IRON)
    else:
        FS.box(x - 0.1, x + 0.8, -0.1, 0.9, -FZ - 1.3, -FZ - 1.1, IRON)
D.barrel(FS, 7.6, -FZ - 1.8, y=-0.1, r=0.7, h=1.6, wood=TIMBER, hoop=IRON2)
D.barrel(FS, 9.0, -FZ - 1.6, y=-0.1, r=0.6, h=1.4, wood=TIMBER, hoop=IRON2)
FS.box(11.4, 13.6, 0.6, 1.4, -FZ - 2.6, -FZ - 1.6, IRON)
FS.prism_xz(K.octa(12.5, -FZ - 2.1, 1.0, 0.45, 0.2), 1.4, 1.9, ROCK4)
S.disc(FS, (11.2, 0.5, -FZ - 2.1), (1, 0, 0), 0.5, 0.2, IRON2, seg=8)
for e in (-1, 1):
    beam(FS, (13.6, 1.0, -FZ - 2.1 + e * 0.4), (15.0, 1.8, -FZ - 2.1 + e * 0.4), 0.12, 0.12, TIMBER2)
F.objects(False)
for x in (-16.4, -13.6):
    FS.box(x - 0.2, x + 0.2, -0.1, 12.0, -FZ - 2.6, -FZ - 2.2, TIMBER)
FS.box(-17.0, -13.0, 12.0, 12.4, -FZ - 2.7, -FZ - 1.0, TIMBER)
FS.prism_zy(K.ngon(-FZ - 2.4, 11.6, 0.35, 8), -15.2, -14.8, IRON)
FS.box(-15.02, -14.98, 6.0, 11.4, -FZ - 2.42, -FZ - 2.38, "C8B890")
FS.prism_xz(K.ngon(-15.0, -FZ - 2.4, 0.45, 8), 5.2, 6.0, IRON)

# ══ ИНТЕРЬЕР: пещера-жеода ════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.4
S.interior(F, CAVE, "5A4E5A", CAVE2, TIMBER2, wain=None, beams=None)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS[:3]):  # неровная порода стен
    for k in range(7):
        a0 = -half + 2 * half * k / 7
        y0 = 1.0 + 3.0 * rng(k, idx)
        slab(IR, axis, fixed, out, 1.3 + 0.4 * (k % 2), a0, a0 + 2 * half / 7, y0, y0 + 4.0 + 3.0 * rng(k, idx, 2), (CAVE, "6A5A70", "4E4060")[k % 3])
F.objects(True)
for k in range(5):  # деревянные крепи-рамы поперёк зала
    z = -13.0 + 5.0 * k
    if z > 6:
        continue
    for e in (-1, 1):
        IS.box(e * (W - 1.6) - 0.4, e * (W - 1.6) + 0.4, 0.0, C - 1.0, z - 0.4, z + 0.4, TIMBER)
    IS.box(-W + 1.0, W - 1.0, C - 1.6, C - 0.8, z - 0.45, z + 0.45, TIMBER2)
# рельсы вдоль левой стены с вагонеткой
for e in (-0.9, 0.9):
    IS.box(-W + 4.0 + e - 0.08, -W + 4.0 + e + 0.08, 0.0, 0.2, ZF + 1.0, ZB - 3.0, IRON)
for k in range(14):
    z = ZF + 1.6 + 2.0 * k
    IS.box(-W + 2.6, -W + 5.4, 0.0, 0.08, z - 0.2, z + 0.2, TIMBER2)
IS.loft([(-W + 2.8, 0.8, -8.0), (-W + 5.2, 0.8, -8.0), (-W + 5.2, 0.8, -5.0), (-W + 2.8, 0.8, -5.0)],
        [(-W + 2.6, 2.4, -8.2), (-W + 5.4, 2.4, -8.2), (-W + 5.4, 2.4, -4.8), (-W + 2.6, 2.4, -4.8)], IRON)
for k in range(5):
    crystal(IG, -W + 3.4 + 0.5 * (k % 3), 2.2, -7.4 + 0.6 * k, 1.0, 0.25, GEMS[k % 4])
# ящики с камнями и большие кристаллы-колонны у дальней стены
for k, x in enumerate((-10.0, -6.5, 6.5, 10.0)):  # середина за экспонатом свободна
    crystal(IG, x, 0.0, ZF + 2.4, 6.0 + 2.0 * (k % 2), 0.9, GEMS[k], lean=(0.3 * (1 if x < 0 else -1), 0.4))
    druse(IG, x + 1.6, 0.0, ZF + 3.4, 1.0, k + 0.5)
for row in range(3):  # ящики с камнями у правой стены
    D.crate(IS, W - 3.4, -4.0 + 2.2 * row, y=0.0, s=1.6, wood=TIMBER, board=TIMBER2)
    crystal(IG, W - 3.4, 1.6, -4.0 + 2.2 * row, 0.8, 0.25, GEMS[row])
F.objects(False)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS[:2]):  # друзы на стенах
    for k in range(4):
        a = -12.0 + 5.0 * k
        y = 6.0 + 4.0 * rng(k, idx)
        if axis == "x":
            druse(IG, fixed + out * 0.35, y, a, 0.9, k + idx, out=(out * 0.9, 0.0))  # растут из стены
for x, z in ((-6.0, -9.0), (6.0, -9.0), (-6.0, 2.0), (6.0, 2.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.0, C - 1.6, z - 0.03, z + 0.03, IRON2)
    D.lantern(IS, IG, x, C - 4.0, z, s=1.0, cap=IRON2, light=LAMP)
# постамент: половинка жеоды — тёмная корка и кольцо кристаллов
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.2, 14), 0.0, 0.6, ROCK4)
IR.prism_xz(K.ngon(px, pz, 3.8, 14), 0.6, TOP - 0.2, "6A5A70")
IS.prism_xz(K.ngon(px, pz, 3.2, 14), TOP - 0.2, TOP, CAVE2)
F.objects(True)
for k in range(6):  # редкое низкое кольцо, наклон наружу: кристаллы не заслоняют хрустального скорпиона
    a = 2 * math.pi * (k + 0.5) / 6
    crystal(IG, px + 3.6 * math.cos(a), TOP - 0.3, pz + 3.6 * math.sin(a), 0.8 + 0.3 * (k % 2), 0.28, GEMS[k % 4],
            lean=(0.7 * math.cos(a), 0.7 * math.sin(a)))
F.objects(False)
B.lift_leaves(IS, IRON2, TIMBER)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, ROCK, "B0946C", ROCK2, top=16.4, roof="none")
SL.box(-FX - 0.3, FX + 0.3, 16.4, 18.0, -FZ - 1.3, FZ + 0.3, ROCK2)
SL.box(-5.6, 5.6, 0.0, 11.2, -FZ - 2.2, -FZ, TIMBER)

F.build(exhibit=(PED[0], TOP, PED[1], 3.2), lamps=[("Hall", (0, 14, 6), 1300, (0.95, 0.88, 1.0)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.96, 1.0)),
                                                   ("Gems", (0, 4, -12), 900, (0.7, 0.5, 1.0))])
