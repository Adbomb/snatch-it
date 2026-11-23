"""Этаж «Сурикат-часовой» музея-небоскрёба (восьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — маяк на скалистом берегу. Снаружи — дом смотрителя: белая обшивка досками, синие ставни и
наличники, сланцевый пояс крыши; на углу — красно-белый маяк сужающейся башней с галереей, светящимся фонарным
залом и куполом; внизу — серые валуны вдоль цоколя, вода у скал, лодка на камнях, ловушки для омаров, ящики,
сети на стене, у входа — большой латунный телескоп на треноге (дозорный пост). Внутри — комната смотрителя: стены
из синих досок, винтовая лестница наверх, огромная линза Френеля из светящихся колец за постаментом, стол с
морской картой и компасом, полка с кораблём в бутылке, бочонки, якорь на стене; экспонат — на тёмно-синей тумбе
с канатом и латунной каймой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_lighthouse.py -- <репо> <превью>
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

WHITE, WHITE2, BLUE, BLUE2, SLATE, RED = "F4F2EC", "DEDBD2", "2E5A9A", "244A80", "4A5A6A", "D83A34"
ROCK, ROCK2, WATER, WOOD, WOOD2, BRASS = "7A828C", "5E666E", "3A8AC0", "A07448", "6A4A2A", "C8982E"
LAMP, NAVY, ROPE, NET = "FFE890", "1E3050", "D8C090", "8A7A5A"

F = B.Floor("LH", "MeerkatLookout", quiet=(ROCK2, "8A9098"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def boulder(p, x, z, y, r, seed):
    """Валун: два гранёных кома."""
    p.prism_xz(K.octa(x, z, r, r * 0.8, r * 0.4), y, y + r * 0.9, ROCK if seed % 2 else ROCK2)
    p.prism_xz(K.octa(x + 0.2 * r, z - 0.1 * r, r * 0.65, r * 0.55, r * 0.25), y + r * 0.9, y + r * 1.4, ROCK)


def trap(p, x, z, y=0.0):
    """Ловушка для омаров: дощатый ящик с сеткой и поплавком."""
    p.box(x - 0.7, x + 0.7, y, y + 0.12, z - 0.5, z + 0.5, WOOD)
    for k in range(4):
        xx = x - 0.6 + 0.4 * k
        p.box(xx - 0.05, xx + 0.05, y, y + 0.8, z - 0.5, z + 0.5, WOOD2)
    p.box(x - 0.7, x + 0.7, y + 0.8, y + 0.92, z - 0.5, z + 0.5, WOOD)
    p.prism_xz(K.ngon(x + 0.9, z, 0.2, 6), y, y + 0.45, RED)


def telescope(p, x, z, y=0.0, ang=-0.35):
    """Латунный телескоп на треноге."""
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.3
        beam(p, (x + 0.8 * math.cos(a), y, z + 0.8 * math.sin(a)), (x, y + 2.6, z), 0.12, 0.12, WOOD2)
    taper(p, (x + 0.8 * math.sin(ang), y + 2.5, z + 1.0), (x - 0.4 * math.sin(ang), y + 3.6, z - 1.8), 0.32, 0.55, BRASS)
    p.prism_xz(K.ngon(x, z, 0.2, 6), y + 2.5, y + 2.8, WOOD2)


# ══ ФАСАД: дом смотрителя и маяк ══════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, WHITE, WHITE, NAVY)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "8A9098")
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.6, ROCK2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.6, 15.6, WHITE)
    for k in range(10):  # обшивка внахлёст
        y = 2.2 + 1.3 * k
        if y + 0.12 < 15.4:
            slab(FS, axis, fixed, out, 0.96, -half + 0.1, half - 0.1, y, y + 0.12, WHITE2)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, 15.6, 16.2, BLUE)
    B.chamfer(FR, axis, fixed, out, -half - 1.4, half + 1.4, [(0.88, 18.9), (2.2, 16.2), (2.2, 15.9), (0.88, 15.9)], SLATE)
    for a in (-half, half - 1.0):
        slab(FR, axis, fixed, out, 1.18, a, a + 1.0, 1.6, 15.6, BLUE2)
    if fi > 0:  # бока и тыл: окна со ставнями
        for a in (-11.0, -3.0, 5.0):
            for y0 in (4.0, 10.6):
                d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
                pr = FG.prism_zy if axis == "x" else FG.prism_xy
                pr(K.rect(a, a + 2.2, y0, y0 + 2.8), d0, d1, LAMP if y0 > 6 else "BFD8EA")
                for e in (-1, 1):
                    s0, s1 = (a - 1.0, a - 0.05) if e < 0 else (a + 2.25, a + 3.2)
                    slab(FS, axis, fixed, out, 1.0, s0, s1, y0, y0 + 2.8, BLUE)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# маяк на левом (по фасаду +x) переднем углу
LX, LZ = 13.4, -FZ - 0.9
bands = 6
for k in range(bands):
    y0, y1 = 0.0 + 2.5 * k, 2.5 * (k + 1)
    r0, r1 = 2.7 - 0.12 * k, 2.7 - 0.12 * (k + 1)
    bot = [(LX + r0 * math.cos(a), LZ + r0 * math.sin(a)) for a in [2 * math.pi * (i + 0.5) / 10 for i in range(10)]]
    top = [(LX + r1 * math.cos(a), LZ + r1 * math.sin(a)) for a in [2 * math.pi * (i + 0.5) / 10 for i in range(10)]]
    FR.loft([(x, y0, z) for x, z in bot], [(x, y1, z) for x, z in top], RED if k % 2 == 0 else WHITE)
FS.prism_xz(K.ngon(LX, LZ, 2.6, 10), 15.0, 15.4, NAVY)
ring_y(FS, LX, LZ, 2.6, 3.0, 15.0, 15.3, NAVY, n=12)
for k in range(12):  # перила галереи
    a = 2 * math.pi * k / 12
    FS.box(LX + 2.9 * math.cos(a) - 0.05, LX + 2.9 * math.cos(a) + 0.05, 15.3, 16.2, LZ + 2.9 * math.sin(a) - 0.05, LZ + 2.9 * math.sin(a) + 0.05, NAVY)
ring_y(FS, LX, LZ, 2.8, 3.0, 16.1, 16.25, NAVY, n=12)
FG.prism_xz(K.ngon(LX, LZ, 1.9, 10), 15.4, 17.6, LAMP)
for k in range(10):
    a = 2 * math.pi * (k + 0.5) / 10
    FS.box(LX + 1.95 * math.cos(a) - 0.07, LX + 1.95 * math.cos(a) + 0.07, 15.4, 17.6, LZ + 1.95 * math.sin(a) - 0.07, LZ + 1.95 * math.sin(a) + 0.07, NAVY)
FS.cone([(x, 17.6, z) for x, z in K.ngon(LX, LZ, 2.2, 10)], (LX, 18.7, LZ), RED)
FS.prism_xz(K.ngon(LX, LZ, 0.15, 6), 18.5, 18.9, BRASS)
FG.prism_xy([(LX - 0.6, 4.0), (LX + 0.6, 4.0), (LX + 0.6, 5.6), (LX, 6.1), (LX - 0.6, 5.6)], LZ - 2.66, LZ - 2.6, LAMP)
FG.prism_xy([(LX - 0.5, 9.4), (LX + 0.5, 9.4), (LX + 0.5, 10.8), (LX, 11.2), (LX - 0.5, 10.8)], LZ - 2.08, LZ - 2.02, LAMP)
FS.box(LX - 1.0, LX + 1.0, 0.0, 3.0, LZ - 2.78, LZ - 2.5, NAVY)  # дверь маяка
# дом смотрителя: крыльцо, дверь, большое окно, сети на стене
FS.box(-3.4, 1.4, 1.6, 8.4, -FZ - 0.96, -FZ - 0.88, BLUE2)
FS.box(-2.9, 0.9, 1.6, 7.9, -FZ - 1.06, -FZ - 0.96, BLUE)
FG.prism_xy([(-2.4, 5.4), (0.4, 5.4), (0.4, 7.0), (-1.0, 7.5), (-2.4, 7.0)], -FZ - 1.1, -FZ - 1.06, LAMP)
FS.box(-4.4, 2.4, 8.4, 8.8, -FZ - 2.6, -FZ - 0.88, SLATE)
for x in (-4.0, 2.0):
    FS.box(x - 0.12, x + 0.12, 1.6, 8.4, -FZ - 2.5, -FZ - 2.26, WHITE2)
for k in range(3):
    FS.box(-3.8 + 0.3 * k, 1.8 - 0.3 * k, -0.1 + 0.4 * k, 0.3 + 0.4 * k, -FZ - 2.8 + 0.4 * k, -FZ - 0.88, WOOD)
FG.box(-15.2, -7.2, 4.0, 8.2, -FZ - 0.94, -FZ - 0.9, "BFD8EA")
FS.frame_xy(K.rect(-15.6, -6.8, 3.6, 8.6), K.rect(-15.2, -7.2, 4.0, 8.2), -FZ - 1.2, -FZ - 0.88, BLUE)
for x in (-12.6, -9.8):
    FS.box(x - 0.06, x + 0.06, 4.0, 8.2, -FZ - 1.0, -FZ - 0.94, BLUE)
FS.box(-15.6, -6.8, 3.3, 3.6, -FZ - 1.6, -FZ - 0.88, WOOD)
for k in range(9):  # сеть на стене над окном
    x = -15.0 + 1.0 * k
    beam(FS, (x, 13.8, -FZ - 0.95), (x + 0.5, 10.0, -FZ - 0.95), 0.05, 0.05, NET)
    beam(FS, (x + 1.0, 13.8, -FZ - 0.95), (x + 0.5, 10.0, -FZ - 0.95), 0.05, 0.05, NET)
D.chain(FS, (-15.4, 13.8, -FZ - 1.0), (-6.6, 13.8, -FZ - 1.0), 6, 0.1, ROPE, sag=0.6)
for k, x in enumerate((-14.0, -11.0, -8.2)):
    FS.prism_xy(K.ngon(x, 10.6 - 0.3 * (k % 2), 0.3, 8), -FZ - 1.1, -FZ - 0.96, (RED, "F0C020", RED)[k])
# валуны, вода у скал, лодка, ловушки, ящики, телескоп
FG.box(-FX - 2.88, -6.0, -1.0, -0.6, -FZ - 2.88, -FZ - 2.0, WATER)
F.objects(True)
for k, (x, z, r) in enumerate(((-6.4, -FZ - 2.2, 0.9), (4.6, -FZ - 2.3, 1.0), (6.2, -FZ - 1.8, 0.8), (9.2, -FZ - 2.4, 0.7),
                               (-17.6, -FZ - 1.6, 1.0), (17.8, -FZ - 3.0, 0.8))):
    boulder(FS, x, z, -0.1, r, k)
BX0, BX1, BZ = -15.8, -9.6, -FZ - 1.9
FS.prism_xy([(BX0 - 0.6, 1.0), (BX1 + 0.8, 1.0), (BX1, -0.1), (BX0, -0.1)], BZ - 0.75, BZ + 0.75, WOOD)
FS.box(BX0 - 0.4, BX1 + 0.6, 0.85, 1.0, BZ - 0.75, BZ + 0.75, "2E6A9A")
FS.box(BX0 + 1.6, BX0 + 1.9, 0.4, 0.95, BZ - 0.7, BZ + 0.7, WOOD2)
FS.box(BX0 + 3.8, BX0 + 4.1, 0.4, 0.95, BZ - 0.7, BZ + 0.7, WOOD2)
beam(FS, (BX0 + 2.6, 1.0, BZ), (BX0 + 0.4, 1.8, BZ - 1.0), 0.1, 0.1, WOOD2)
trap(FS, 6.6, -FZ - 1.8 - 0.9, y=0.7)
for k in range(2):  # два ящика стопкой
    D.crate(FS, -5.2, -FZ - 1.4, y=-0.1 + 1.0 * k, s=1.0, wood=WOOD, board=WOOD2)
telescope(FS, 3.4, -FZ - 2.3, y=-0.1)
F.objects(False)
ring_y(FS, -7.4, -FZ - 1.2, 0.25, 0.8, -0.1, 0.35, ROPE, n=10)

# ══ ИНТЕРЬЕР: комната смотрителя ══════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.1
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "A07448")
for k in range(-13, 14):
    if k % 2:
        IQ.box(1.2 * k, 1.2 * k + 1.2, 0.02, 0.04, ZF + 0.9, ZB - 0.9, "8A6238")
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, "3A6A9A")
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 3.0, WHITE)
        slab(IS, axis, fixed, out, 1.05, a0, a1, 3.0, 3.2, WOOD2)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, "3A6A9A")
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, WOOD2)
    for k in range(int(2 * half // 1.6)):  # швы досок
        a = -half + 0.8 + 1.6 * k
        if not (gap and abs(a) < DOOR[0] + 0.8):
            slab(IS, axis, fixed, out, 0.92, a - 0.04, a + 0.04, 3.2, C, "2E5A88")
    slab(IR, axis, fixed, out, 1.3, -half, half, 15.6, 16.4, WHITE)
for k in range(-3, 4):
    IS.box(-W, W, C - 0.7, C - 0.2, 4.4 * k - 0.25, 4.4 * k + 0.25, WOOD2)
# огромная линза Френеля за постаментом
LZI = ZF + 2.6
IS.box(-4.6, 4.6, 0.0, 1.6, LZI - 1.6, LZI + 1.6, BRASS)
# линза — холодное голубое стекло на тёмно-синем диске: жёлтый сурикат не тонет в жёлтом свечении
IS.prism_xy(K.ngon(0.0, 8.0, 3.8, 16), LZI - 0.45, LZI - 0.3, NAVY)
for k in range(6):
    r = 3.6 - 0.45 * k
    IG.frame_xy(K.ngon(0.0, 8.0, r, 16), K.ngon(0.0, 8.0, r - 0.3, 16), LZI - 0.2 + 0.12 * k, LZI + 0.1 + 0.12 * k,
                ("A8E0F4", "D8F4FF")[k % 2])
IG.prism_xy(K.ngon(0.0, 8.0, 0.9, 12), LZI + 0.7, LZI + 0.9, "C8F0FF")
IS.frame_xy(K.ngon(0.0, 8.0, 4.1, 16), K.ngon(0.0, 8.0, 3.6, 16), LZI - 0.3, LZI + 0.2, BRASS)
for k in range(4):
    a = math.pi / 4 + math.pi / 2 * k
    beam(IS, (3.9 * math.cos(a), 8.0 + 3.9 * math.sin(a), LZI), (4.6 * math.cos(a), 1.6 if math.sin(a) < 0 else 13.0, LZI), 0.2, 0.2, BRASS)
# винтовая лестница в правом углу
SX, SZ = 11.6, -10.6
F.objects(True)
IS.prism_xz(K.ngon(SX, SZ, 0.35, 8), 0.0, C, WOOD2)
for k in range(16):
    a = 2 * math.pi * k / 10
    y = 0.6 + 1.05 * k
    if y > C - 1.0:
        break
    IS.prism_xz([(SX + 0.3 * math.cos(a), SZ + 0.3 * math.sin(a)), (SX + 2.6 * math.cos(a - 0.25), SZ + 2.6 * math.sin(a - 0.25)),
                 (SX + 2.6 * math.cos(a + 0.35), SZ + 2.6 * math.sin(a + 0.35))], y - 0.15, y, WOOD)
F.objects(False)
IS.frame_xz(K.ngon(SX, SZ, 3.0, 10), K.ngon(SX, SZ, 2.7, 10), C - 0.3, C - 0.05, WOOD2)
# стол с картой и компасом, полка с кораблём в бутылке, бочонки, якорь
F.objects(True)
TX, TZ = -11.4, -9.0
IS.box(TX - 2.0, TX + 2.0, 2.6, 2.9, TZ - 1.4, TZ + 1.4, WOOD)
for e in (-1, 1):
    for f in (-1, 1):
        IS.box(TX + e * 1.8 - 0.15, TX + e * 1.8 + 0.15, 0.0, 2.6, TZ + f * 1.2 - 0.15, TZ + f * 1.2 + 0.15, WOOD2)
IS.box(TX - 1.6, TX + 1.2, 2.9, 2.94, TZ - 1.0, TZ + 1.0, "E8D8A8")
IS.prism_xz(K.ngon(TX + 1.4, TZ + 0.6, 0.4, 10), 2.9, 3.05, BRASS)
for k in range(3):
    D.barrel(IS, -14.4 + 1.6 * (k % 2), 6.4 + 1.4 * (k // 2), r=0.7, h=1.5, wood=WOOD, hoop=NAVY)
x = W - 0.88
IS.box(x - 1.2, x, 6.4, 6.6, 2.0, 8.0, WOOD)
IG.prism_zy(K.octa(5.0, 7.4, 1.4, 0.7, 0.3), x - 1.0, x - 0.5, "BFE8E0")
IS.prism_zy([(4.3, 7.0), (5.7, 7.0), (5.5, 6.75), (4.5, 6.75)], x - 0.8, x - 0.7, WOOD2)
IS.box(x - 0.78, x - 0.72, 7.0, 8.0, 4.98, 5.02, WOOD2)
F.objects(False)
AX = -W + 0.95  # якорь на левой стене
IS.box(AX, AX + 0.25, 6.0, 11.0, 2.9, 3.3, NAVY)
IS.box(AX, AX + 0.25, 10.0, 10.3, 2.0, 4.2, NAVY)
B.tube(IS, [(AX + 0.12, 7.0, 1.4), (AX + 0.12, 6.0, 2.2), (AX + 0.12, 5.7, 3.1), (AX + 0.12, 6.0, 4.0), (AX + 0.12, 7.0, 4.8)],
       [0.35] * 5, 0.25, (1, 0, 0), NAVY)
IS.frame_zy(K.ngon(3.1, 11.6, 0.6, 10), K.ngon(3.1, 11.6, 0.35, 10), AX, AX + 0.25, NAVY)
for x, z in ((-6.0, -6.0), (6.0, 2.0), (-6.0, 4.0)):
    IS.box(x - 0.04, x + 0.04, C - 3.2, C - 0.7, z - 0.04, z + 0.04, NAVY)
    D.lantern(IS, IG, x, C - 4.2, z, s=1.0, cap=NAVY, light=LAMP)
# постамент: тёмно-синяя тумба с канатом и латунной каймой
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, 0.5, ROCK2)
IS.prism_xz(K.ngon(px, pz, 3.7, 16), 0.5, TOP - 0.1, NAVY)
ring_y(IS, px, pz, 3.65, 3.95, 0.6, 0.85, ROPE, n=16)
# верх тумбы тёмно-синий, латунь — только кромка: на свету латунный диск выгорал в жёлтый под жёлтым сурикатом
IS.prism_xz(K.ngon(px, pz, 3.6, 16), TOP - 0.1, TOP, NAVY)
ring_y(IS, px, pz, 3.6, 3.85, TOP - 0.1, TOP, BRASS, n=16)
B.lift_leaves(IS, BLUE2, WHITE)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 15.6, -FZ, FZ, WHITE)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "8A9098")
SL.prism_zy([(-FZ - 2.2, 15.6), (FZ + 2.2, 15.6), (FZ + 0.88, 18.9), (-FZ - 0.88, 18.9)], -FX - 2.2, FX + 2.2, SLATE)
SL.prism_xz(K.ngon(LX, LZ, 2.6, 10), -0.1, 15.4, RED)
SL.cone([(x, 15.4, z) for x, z in K.ngon(LX, LZ, 2.4, 10)], (LX, 18.7, LZ), RED)

F.build(exhibit=(PED[0], TOP, PED[1], 2.8), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.95, 0.88)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Lens", (0, 8, ZF + 5), 900, (1.0, 0.92, 0.6))])
