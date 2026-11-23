"""Этаж «Трёхголовая крыса» музея-небоскрёба (седьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — врата подземного царства, которые стережёт трёхголовый страж. Снаружи — тёмный базальтовый храм:
широкие ступени, портик из шести гранёных колонн с бронзовыми капителями, треугольный фронтон с бронзовым
трёхзубцем, бронзовые решётчатые ворота с кольцами; перед ступенями — светящаяся бирюзовая река с чёрной лодкой
перевозчика и фонарём на шесте, по бокам ворот — чаши с призрачно-голубым огнём, у ворот — три огромные миски для
трёх голов, огромная кость и разорванная цепь с ошейником в шипах; бока — колоннада с чашами огня, по камню —
светящиеся трещины. Внутри — тронный зал стража: пол из базальтовых плит со светящимися швами, колонны по бокам,
сталактиты с потолка, вдоль дальней стены — светящаяся подземная река с мостиком-аркой, амфоры, гранатовое дерево
в кадке, три миски и груда костей-игрушек; экспонат — на тёмном круглом постаменте с тремя чашами голубого огня.
Запуск: blender --background --factory-startup --python scripts/blender/floor_underworld.py -- <репо> <превью>
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

BAS, BAS2, BAS3, BRONZE, BRONZE2 = "4A4E62", "62677E", "2A2C36", "C08A40", "8A5A2A"
SHAFT = "747A94"
GHOST, GHOST2, BONE, RED, POM = "3AE8D0", "B8FFF4", "EDE4CC", "8A2A2A", "C8283A"
WATER, WATER2, BOAT, LEAF = "1EA8A0", "60E0D0", "2A2226", "2E6A3A"

F = B.Floor("UW", "ThreeHeadedRat", quiet=(BAS2, "3A3C48"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def column(p, x, z, y0, y1, r=0.8, shaft=SHAFT, cap=BRONZE):
    """Гранёная колонна: база, ствол из двух ярусов (тонкие грани — каннелюры), бронзовая капитель."""
    p.prism_xz(K.ngon(x, z, r * 1.35, 8), y0, y0 + 0.5, BAS)
    p.prism_xz(K.ngon(x, z, r, 12), y0 + 0.5, y1 - 0.9, shaft)
    p.prism_xz(K.ngon(x, z, r * 1.08, 12), y0 + 0.5, y0 + 0.9, BAS)
    p.prism_xz(K.ngon(x, z, r * 1.25, 8), y1 - 0.9, y1 - 0.5, cap)
    p.box(x - r * 1.5, x + r * 1.5, y1 - 0.5, y1, z - r * 1.5, z + r * 1.5, BAS)


def brazier(p, g, x, z, y=0.0, h=2.4, r=0.9):
    """Чаша на треножнике с призрачным огнём."""
    for k in range(3):
        t = 2 * math.pi * k / 3 + 0.3
        beam(p, (x + r * 0.8 * math.cos(t), y, z + r * 0.8 * math.sin(t)), (x + 0.2 * math.cos(t), y + h, z + 0.2 * math.sin(t)),
             0.16, 0.16, BRONZE2)
    p.prism_xz(K.ngon(x, z, r * 0.6, 8), y + h, y + h + 0.3, BRONZE)
    p.prism_xz(K.ngon(x, z, r, 8), y + h + 0.3, y + h + 0.7, BRONZE)
    g.prism_xz(K.ngon(x, z, r * 0.8, 6), y + h + 0.7, y + h + 1.1, GHOST)
    g.cone([(xx, y + h + 1.1, zz) for xx, zz in K.ngon(x, z, r * 0.8, 6)], (x, y + h + 2.6, z), GHOST)
    g.cone([(xx, y + h + 1.1, zz) for xx, zz in K.ngon(x + 0.1, z - 0.1, r * 0.4, 5)], (x + 0.15, y + h + 2.0, z - 0.15), GHOST2)


def bowl(p, x, z, y=0.0, r=1.3, col=RED):
    """Большая миска для одной из трёх голов."""
    p.prism_xz(K.ngon(x, z, r * 0.8, 12), y, y + 0.25, col)
    p.prism_xz(K.ngon(x, z, r, 12), y + 0.25, y + 0.75, col)
    p.prism_xz(K.ngon(x, z, r * 0.85, 12), y + 0.6, y + 0.72, "6A3A22")


def bone(p, a, b, w=0.45):
    """Кость: стержень и по два «мосла» на концах."""
    beam(p, a, b, w, w, BONE)
    for c in (a, b):
        dx, dz = b[0] - a[0], b[2] - a[2]
        n = math.hypot(dx, dz) or 1.0
        ox, oz = -dz / n * w * 0.7, dx / n * w * 0.7
        for e in (-1, 1):
            p.prism_xz(K.octa(c[0] + e * ox, c[2] + e * oz, w * 0.75, w * 0.75, w * 0.3), c[1] - w * 0.7, c[1] + w * 0.7, BONE)


def crack(g, axis, fixed, out, a, y, n, seed):
    """Светящаяся трещина-молния по камню."""
    d0, d1 = sorted((fixed, fixed + out * 0.06))
    for k in range(n):
        da = (rng(seed, k) - 0.5) * 1.4
        pts = [(a - 0.07, y), (a + 0.07, y), (a + da + 0.07, y + 1.1), (a + da - 0.07, y + 1.1)]
        if axis == "z":
            g.prism_xy(pts, d0, d1, GHOST)
        else:
            g.prism_zy(pts, d0, d1, GHOST)
        a, y = a + da, y + 1.1


# ══ ФАСАД: храм-врата ═════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, BAS, BAS, BAS3)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    if fi != 0:
        slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "3A3C48")
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -1.0, 1.0, BAS2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.0, 14.4, BAS)
    slab(FR, axis, fixed, out, 1.58, -half - 0.4, half + 0.4, 14.4, 15.2, BAS2)
    slab(FS, axis, fixed, out, 1.62, -half - 0.4, half + 0.4, 15.2, 15.45, BRONZE)
    slab(FG, axis, fixed, out, 0.95, -half, half, 13.9, 14.4, GHOST)
    slab(FR, axis, fixed, out, 0.88, -half, half, 15.45, 17.4, BAS)
    slab(FR, axis, fixed, out, 1.88, -half - 0.6, half + 0.6, 17.4, 18.2, BAS2)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, 18.2, 18.9, BAS)
    for k in range(int(2 * half // 1.6)):  # зубчики-дентикулы под карнизом
        a = -half + 0.2 + 1.6 * k
        slab(FS, axis, fixed, out, 1.2, a, a + 0.8, 16.6, 17.4, BAS2)
    if fi > 0:  # бока и тыл: колоннада у стены, чаши огня, трещины
        for a in (-12.0, -4.0, 4.0, 12.0):
            cx = fixed + out * 1.9
            if axis == "x":
                column(FS, cx, a, 1.0, 14.4, r=0.7)
            else:
                column(FS, a, cx, 1.0, 14.4, r=0.7)
        for a in (-8.0, 8.0):
            if axis == "x":
                F.objects(True)
                brazier(FS, FG, fixed + out * 2.0, a, y=-0.1, h=1.8, r=0.7)
                F.objects(False)
            crack(FG, axis, fixed + out * 0.88, out, a + 1.5, 2.0, 6, fi * 10 + int(a))
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# перед храмом: площадка, справа — заводь подземной реки с лодкой перевозчика
FQ.box(-FX - 2.88, 12.2, -1.0, -0.1, -FZ - 2.88, -FZ - 0.88, "3A3C48")
FR.box(12.2, 12.8, -1.0, 0.2, -FZ - 2.88, -FZ - 0.88, BAS2)
FG.box(12.8, FX, -1.0, -0.5, -FZ - 2.88, -FZ - 0.88, WATER)
for k in range(4):
    x = 13.2 + 1.2 * k
    FG.box(x, x + 0.8, -0.5, -0.46, -FZ - 2.6 + 1.2 * rng(k, 5), -FZ - 2.4 + 1.2 * rng(k, 5), WATER2)
F.objects(True)
BX0, BX1, BZ = 14.0, 16.6, -FZ - 1.9
FS.prism_xy([(BX0 - 0.8, 0.4), (BX1 + 0.8, 0.4), (BX1 + 0.1, -0.7), (BX0 - 0.1, -0.7)], BZ - 0.75, BZ + 0.75, BOAT)
FS.prism_xy([(BX1 + 0.8, 0.4), (BX1 + 1.3, 1.5), (BX1 + 0.9, 1.5), (BX1 + 0.4, 0.4)], BZ - 0.35, BZ + 0.35, BOAT)
FS.box(BX0 - 0.5, BX1 + 0.5, 0.25, 0.4, BZ - 0.62, BZ + 0.62, "4A3A3A")
FS.box(BX0 - 0.1, BX0 + 0.1, 0.4, 5.8, BZ - 0.1, BZ + 0.1, "5A4A3A")  # шест с фонарём
beam(FS, (BX0, 5.6, BZ), (BX0 + 1.2, 6.2, BZ), 0.12, 0.12, "5A4A3A")
D.lantern(FS, FG, BX0 + 1.2, 5.0, BZ, s=0.8, cap=BRONZE2, light=GHOST2)
F.objects(False)
# подиум с двумя ступенями и портик из четырёх колонн
FR.box(-11.4, 11.4, -0.1, 0.95, -FZ - 2.4, -FZ - 0.88, BAS2)
FS.box(-11.5, 11.5, 0.8, 0.95, -FZ - 2.45, -FZ - 0.88, BRONZE2)
for k in range(2):
    FR.box(-3.8 + 0.2 * k, 3.8 - 0.2 * k, -0.1, 0.25 + 0.35 * k, -FZ - 2.88 + 0.24 * k, -FZ - 2.4, BAS2)
PZ = -FZ - 1.7
for x in (-10.0, -5.0, 5.0, 10.0):
    column(FS, x, -FZ - 1.4, 0.95, 13.6, r=0.7)
FR.box(-11.6, 11.6, 13.6, 14.6, PZ - 0.9, -FZ - 0.5, BAS2)  # архитрав
FS.box(-11.6, 11.6, 14.1, 14.3, PZ - 0.94, PZ - 0.88, BRONZE)
FR.prism_xy([(-12.0, 14.6), (12.0, 14.6), (0.0, 18.8)], PZ - 1.0, -FZ - 0.5, BAS)  # фронтон
FS.frame_xy([(-12.4, 14.4), (12.4, 14.4), (0.0, 19.0)], [(-11.0, 14.9), (11.0, 14.9), (0.0, 18.2)], PZ - 1.1, PZ - 0.96, BAS2)
for e in (-1, 0, 1):  # бронзовый трёхзубец на фронтоне
    FS.box(e * 0.9 - 0.14, e * 0.9 + 0.14, 16.3, 17.6 if e == 0 else 17.3, PZ - 1.14, PZ - 1.0, BRONZE)
    FS.prism_xy([(e * 0.9 - 0.3, 17.6 if e == 0 else 17.3), (e * 0.9 + 0.3, 17.6 if e == 0 else 17.3),
                 (e * 0.9, 18.1 if e == 0 else 17.8)], PZ - 1.14, PZ - 1.0, BRONZE)
FS.box(-1.1, 1.1, 16.1, 16.35, PZ - 1.14, PZ - 1.0, BRONZE)
FS.box(-0.12, 0.12, 15.2, 16.1, PZ - 1.14, PZ - 1.0, BRONZE)
# бронзовые решётчатые ворота с кольцами, проём светится
FS.box(-3.4, 3.4, 1.0, 11.0, -FZ - 0.96, -FZ - 0.88, BAS3)
FG.box(-3.0, 3.0, 1.0, 10.4, -FZ - 1.0, -FZ - 0.96, "1E6A70")
FS.frame_xy(K.rect(-3.6, 3.6, 1.0, 11.2), K.rect(-3.0, 3.0, 1.0, 10.4), -FZ - 1.4, -FZ - 0.88, BAS2)
for k in range(9):
    x = -2.7 + 0.675 * k
    FS.box(x - 0.08, x + 0.08, 1.0, 10.4, -FZ - 1.2, -FZ - 1.04, BRONZE)
    FS.prism_xy([(x - 0.16, 10.4), (x + 0.16, 10.4), (x, 10.9)], -FZ - 1.2, -FZ - 1.04, BRONZE)
for y in (2.6, 6.0, 9.2):
    FS.box(-3.0, 3.0, y, y + 0.22, -FZ - 1.26, -FZ - 1.04, BRONZE2)
FS.box(-0.7, 0.7, 4.2, 6.4, -FZ - 1.34, -FZ - 1.26, BRONZE2)  # один замок на створках: накладка и кольцо
FS.frame_xy(K.ngon(0.0, 4.4, 0.55, 10), K.ngon(0.0, 4.4, 0.38, 10), -FZ - 1.42, -FZ - 1.34, BRONZE)
# трещины по фасаду
for a, y in ((-15.0, 2.0), (14.2, 3.2), (-13.0, 9.2)):
    crack(FG, "z", -FZ - 0.88, -1, a, y, 5, int(a))
# чаши призрачного огня между колоннами, три миски (в красной — кость)
F.objects(True)
for x in (-7.5, 7.5):
    brazier(FS, FG, x, -FZ - 1.7, y=0.95, h=1.8, r=0.75)
for x, col in ((-12.8, RED), (-14.9, "2A5A8A"), (-17.0, "3A7A3A")):
    bowl(FS, x, -FZ - 1.85, y=-0.1, r=0.9, col=col)
bone(FS, (-13.2, 0.5, -FZ - 1.85), (-12.0, 1.7, -FZ - 2.2), w=0.3)
F.objects(False)

# ══ ИНТЕРЬЕР: зал стража ══════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.1
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "3A3C48")
for i in range(-3, 4):  # светящиеся швы между плитами — реже и тусклее
    x = 4.5 * i
    if abs(x) < W - 0.5:
        IG.box(x - 0.04, x + 0.04, 0.02, 0.05, ZF + 0.9, ZB - 0.9, "1A5A58")
for j in range(-3, 4):
    z = 4.5 * j
    if ZF + 0.9 < z < ZB - 0.9:
        IG.box(-W + 0.9, W - 0.9, 0.02, 0.05, z - 0.04, z + 0.04, "1A5A58")
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, BAS)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 1.0, BAS2)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, BAS)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, BRONZE)
    slab(IR, axis, fixed, out, 1.6, -half, half, 14.6, 15.4, BAS2)
    slab(IS, axis, fixed, out, 1.7, -half, half, 15.4, 15.6, BRONZE2)
    if idx < 2:
        for a in (-9.0, 4.0):
            crack(IG, axis, fixed + out * 0.88, out, a, 2.0, 7, idx * 7 + int(a))
# колонны по бокам
for s in (-1, 1):
    for z in (-12.0, -5.0, 2.0):
        column(IR, s * (W - 2.6), z, 0.0, 14.6, r=0.9)
# сталактиты
for k in range(16):
    x, z = -W + 2.0 + (2 * W - 4) * rng(k, 11), ZF + 2.0 + (ZB - ZF - 6) * rng(k, 12)
    if abs(x) < 5 and -8 < z < 2:
        continue
    L = 1.2 + 2.0 * rng(k, 13)
    IS.cone([(xx, C, zz) for xx, zz in K.ngon(x, z, 0.5 + 0.3 * rng(k, 14), 5)], (x, C - L, z), BAS2)
# дальняя стена: светящаяся подземная река с мостиком-аркой
IG.box(-W + 0.9, W - 0.9, 0.0, 0.3, ZF + 0.9, ZF + 3.4, WATER)
IR.box(-W + 0.9, W - 0.9, 0.0, 0.6, ZF + 3.4, ZF + 3.8, BAS2)
for k in range(7):
    x = -13.0 + 4.0 * k + rng(k, 3)
    IG.box(x, x + 1.2, 0.3, 0.34, ZF + 1.6 + rng(k, 6), ZF + 1.8 + rng(k, 6), WATER2)
F.objects(True)
for k in range(9):  # мостик-арка
    t0, t1 = k / 9, (k + 1) / 9
    y0, y1 = 0.6 + 1.6 * math.sin(math.pi * t0), 0.6 + 1.6 * math.sin(math.pi * t1)
    z0, z1 = ZF + 4.0 - 3.4 * t0, ZF + 4.0 - 3.4 * t1
    IS.prism_zy([(z0, y0), (z1, y1), (z1, y1 + 0.3), (z0, y0 + 0.3)], -9.4, -7.0, BAS2)
F.objects(False)
IS.frame_xy([(-6.0, 0.6), (6.0, 0.6), (6.0, 10.0), (0.0, 13.6), (-6.0, 10.0)], [(-5.0, 0.6), (5.0, 0.6), (5.0, 9.6), (0.0, 12.6), (-5.0, 9.6)],
            ZF + 0.88, ZF + 1.6, BAS2)
IG.prism_xy([(-5.0, 0.6), (5.0, 0.6), (5.0, 9.6), (0.0, 12.6), (-5.0, 9.6)], ZF + 0.9, ZF + 0.94, "164A58")
IG.prism_xy([(-3.0, 0.6), (3.0, 0.6), (3.0, 7.0), (0.0, 9.0), (-3.0, 7.0)], ZF + 0.94, ZF + 0.98, "2A8A90")
# амфоры, гранатовое дерево, три миски и груда костей
F.objects(True)
for x, z, h in ((11.6, -12.0, 2.4), (12.8, -10.6, 1.8), (-12.6, 5.0, 2.2)):
    IS.prism_xz(K.ngon(x, z, 0.4, 8), 0.0, 0.3, BRONZE2)
    IS.prism_xz(K.ngon(x, z, 0.75, 8), 0.3, h * 0.7, "A85A30")
    IS.prism_xz(K.ngon(x, z, 0.35, 8), h * 0.7, h, "A85A30")
    IS.box(x - 0.08, x + 0.08, h * 0.4, h * 0.6, z - 0.95, z + 0.95, BAS3)
TX, TZ = -11.0, -11.0
IS.prism_xz(K.ngon(TX, TZ, 1.2, 8), 0.0, 1.4, BAS2)
beam(IS, (TX, 1.4, TZ), (TX + 0.3, 5.4, TZ + 0.2), 0.45, 0.45, "5A3A2A")
for k in range(5):
    t = 2 * math.pi * k / 5
    D.bush(IS, TX + 1.3 * math.cos(t), TZ + 1.3 * math.sin(t), y=4.6 + 0.6 * (k % 2), r=1.0, c1=LEAF, c2="245A30")
    IS.prism_xz(K.octa(TX + 1.6 * math.cos(t + 0.5), TZ + 1.6 * math.sin(t + 0.5), 0.3, 0.3, 0.1), 4.4, 5.0, POM)
for x, col in ((8.6, RED), (10.8, "2A5A8A"), (13.0, "3A7A3A")):
    bowl(IS, x, 4.6, r=1.0, col=col)
bone(IS, (-13.4, 0.35, -3.0), (-11.0, 0.35, -2.0), w=0.35)
bone(IS, (-12.8, 0.9, -1.4), (-11.4, 0.7, -3.4), w=0.3)
bone(IS, (-10.8, 0.35, -4.6), (-12.6, 0.35, -5.6), w=0.3)
ring_y(IS, -12.0, 1.4, 0.9, 1.25, 0.0, 0.4, RED, n=12)  # ошейник в шипах и разорванная цепь
for k in range(8):
    t = 2 * math.pi * k / 8
    taper(IS, (-12.0 + 1.2 * math.cos(t), 0.2, 1.4 + 1.2 * math.sin(t)), (-12.0 + 1.7 * math.cos(t), 0.2, 1.4 + 1.7 * math.sin(t)),
          0.28, 0.04, "C8C8D0")
for k in range(4):
    IS.frame_zy(K.octa(2.9 + 0.6 * k, 0.25, 0.32, 0.22, 0.08), K.octa(2.9 + 0.6 * k, 0.25, 0.18, 0.1, 0.04),
                -12.1 + 0.15 * (k % 2), -11.9 + 0.15 * (k % 2), "5A5A66")
F.objects(False)
# постамент: тёмный круг с тремя чашами голубого огня
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.2, 16), 0.0, 0.5, BAS2)
IS.prism_xz(K.ngon(px, pz, 4.3, 16), 0.5, 0.62, BRONZE)
IS.prism_xz(K.ngon(px, pz, 3.8, 16), 0.62, TOP - 0.1, BAS3)
IS.prism_xz(K.ngon(px, pz, 3.9, 16), TOP - 0.1, TOP, BAS2)
ring_y(IG, px, pz, 3.82, 3.9, 0.7, 0.86, GHOST, n=16)
F.objects(True)
for k in range(3):
    t = 2 * math.pi * k / 3 - math.pi / 2
    brazier(IS, IG, px + 5.4 * math.cos(t), pz + 5.4 * math.sin(t), h=1.8, r=0.7)
F.objects(False)
B.lift_leaves(IS, BAS2, BRONZE)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, BAS)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.4, -FZ - 2.9, FZ + 2.9, "3A3C48")
SL.box(-FX - 0.6, FX + 0.6, 17.4, 18.2, -FZ - 0.6, FZ + 0.6, BAS2)
SL.box(-11.6, 11.6, 13.6, 14.6, PZ - 0.9, -FZ, BAS2)
SL.prism_xy([(-12.0, 14.6), (12.0, 14.6), (0.0, 18.8)], PZ - 1.0, -FZ, BAS)
SL.box(-11.4, 11.4, -0.1, 0.95, -FZ - 2.4, -FZ, BAS2)
for x in (-10.0, -5.0, 5.0, 10.0):
    SL.box(x - 0.7, x + 0.7, 0.95, 13.6, -FZ - 2.1, -FZ - 0.7, BAS2)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 1400, (0.85, 0.95, 1.0)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("River", (0, 4, ZF + 3), 700, (0.4, 1.0, 0.9))])
