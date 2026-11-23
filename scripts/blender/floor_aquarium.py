"""Этаж «Верблюд-аквариум» музея-небоскрёба (девятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — океанариум посреди пустыни. Снаружи — тёмно-синий фасад с бирюзовыми поясами-волнами, ряд из пяти
иллюминаторов, стеклянный вход под козырьком-волной, над ним — большая рыба-скульптура с плавниками и пузырями,
по углам — хвост кита из песка и якорь с цепью, кадки с кораллами, буй. Внутри — тёмный зал: большие аквариумы
во всю стену с рыбками, водорослями и кораллами, медузы-светильники под потолком, своды-рёбра «подводного
туннеля», скамьи; экспонат — на круглом рифе из кораллов с водяным кольцом.
Запуск: blender --background --factory-startup --python scripts/blender/floor_aquarium.py -- <репо> <превью>
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
from floorbase import C, FX, FZ, W, ZB, ZF, beam, rng, taper  # noqa: E402

NAVY, NAVY2, AQUA, AQUA2, WHITE, SAND = "1E3A6E", "142A52", "3AC8D8", "2A9AB8", "F0F4F8", "E8D4A0"
CORAL, CORAL2, ORANGE, YEL, PURPLE, WATER = "F27A6A", "E0508A", "F29A30", "F2D040", "9A6AE0", "5AB8F0"
GLASS, SEAWEED, IRON, DEEP = "B8E8F8", "3AA05A", "4A5260", "2A5AA8"

F = B.Floor("AQ", "AquariumCamel", quiet=(NAVY2, SAND, "2A4A7A"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def fish(p, x, y, z, s, col, d=1, axis="z", t=0.25):
    """Рыбка в профиль: тело-восьмиугольник и хвост; d — куда плывёт."""
    if axis == "z":
        p.prism_xy(K.octa(x, y, s, s * 0.55, s * 0.3), z - t / 2, z + t / 2, col)
        p.prism_xy([(x - d * s * 0.9, y), (x - d * s * 1.6, y + s * 0.55), (x - d * s * 1.6, y - s * 0.55)], z - t / 4, z + t / 4, col)
    else:
        p.prism_zy(K.octa(z, y, s, s * 0.55, s * 0.3), x - t / 2, x + t / 2, col)
        p.prism_zy([(z - d * s * 0.9, y), (z - d * s * 1.6, y + s * 0.55), (z - d * s * 1.6, y - s * 0.55)], x - t / 4, x + t / 4, col)


def coral(p, x, z, y, h, col):
    """Коралл-кустик: ствол и ветки-шипы."""
    p.prism_xz(K.ngon(x, z, h * 0.12, 6), y, y + h * 0.5, col)
    for k in range(4):
        a = 2 * math.pi * k / 4 + x
        taper(p, (x, y + h * 0.4, z), (x + h * 0.35 * math.cos(a), y + h * (0.8 + 0.2 * (k % 2)), z + h * 0.35 * math.sin(a)),
              h * 0.16, h * 0.06, col)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, NAVY, NAVY2, AQUA, SAND, "142A52", roof="flat", roof_col=NAVY, top=16.2,
         side=S.side_windows(F, AQUA, GLASS, kind="slit", y0=5.0, y1=13.0, w=1.2, xs=(-12.0, -6.0, 0.0, 6.0, 12.0)))
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # пояса-волны по всему периметру
    for j, (y, col) in enumerate(((3.6, AQUA2), (4.4, AQUA))):
        for k in range(int(2 * half // 2.0)):
            a = -half + 2.0 * k
            top = y + 0.35 + 0.25 * math.sin(k * 1.2 + j)
            B.chamfer(FS, axis, fixed, out, a, a + 2.0, [(0.88, y), (1.05, y), (1.05, top), (0.88, top)], col)
B.slab(FS, "z", -FZ, -1, 1.05, -FX, FX, 15.0, 15.4, AQUA)
# пять иллюминаторов в ряд
for k in range(5):
    x = -12.0 + 6.0 * k
    FG.prism_xy(K.ngon(x, 12.4, 1.1, 14), -FZ - 0.92, -FZ - 0.88, GLASS)
    S.annulus(FS, (x, 12.4, -FZ - 0.88), (0, 0, -1), 1.1, 1.5, 0.3, "C8D0D8", seg=14)
    for j in range(6):
        a = 2 * math.pi * j / 6
        FS.prism_xy(K.ngon(x + 1.3 * math.cos(a), 12.4 + 1.3 * math.sin(a), 0.1, 6), -FZ - 1.24, -FZ - 1.18, IRON)
# стеклянный вход под козырьком-волной
FG.box(-4.0, 4.0, 1.0, 7.2, -FZ - 0.94, -FZ - 0.88, GLASS)
FS.frame_xy(K.rect(-4.3, 4.3, 1.0, 7.5), K.rect(-4.0, 4.0, 1.0, 7.2), -FZ - 1.1, -FZ - 0.88, AQUA2)
for x in (-1.35, 1.35):
    FS.box(x - 0.08, x + 0.08, 1.0, 7.2, -FZ - 1.0, -FZ - 0.9, AQUA2)
for k in range(10):
    x0 = -6.0 + 1.2 * k
    y = 8.0 + 0.5 * math.sin(k * 0.8)
    FS.loft([(x0, y, -FZ - 0.9), (x0 + 1.2, y, -FZ - 0.9), (x0 + 1.2, y + 0.3, -FZ - 0.9), (x0, y + 0.3, -FZ - 0.9)],
            [(x0, y - 0.5, -FZ - 3.0), (x0 + 1.2, y - 0.5, -FZ - 3.0), (x0 + 1.2, y - 0.2, -FZ - 3.0), (x0, y - 0.2, -FZ - 3.0)], AQUA)
# большая рыба над входом с плавниками и пузырями
F.objects(True)
FS.prism_xy(K.octa(0.0, 15.0 - 3.0, 3.8, 1.8, 1.0), -FZ - 1.8, -FZ - 1.0, ORANGE)
FS.prism_xy([(3.2, 12.0), (5.6, 13.8), (5.0, 12.0), (5.6, 10.2)], -FZ - 1.6, -FZ - 1.2, ORANGE)
FS.prism_xy([(-1.0, 13.6), (1.4, 13.6), (0.6, 14.8)], -FZ - 1.5, -FZ - 1.3, CORAL)
for x in (-1.0, 0.6, 2.0):
    FS.box(x - 0.18, x + 0.18, 10.4, 13.6, -FZ - 1.86, -FZ - 1.8, WHITE)
FS.prism_xy(K.ngon(-2.4, 12.4, 0.35, 8), -FZ - 1.9, -FZ - 1.8, NAVY2)
for k, (x, y, r) in enumerate(((-4.6, 13.6, 0.4), (-5.4, 14.6, 0.3), (-4.8, 15.4, 0.22))):
    S.annulus(FS, (x, y, -FZ - 1.2), (0, 0, -1), r * 0.6, r, 0.1, WHITE, seg=10)
# хвост кита из песка и якорь с цепью по углам, кадки с кораллами, буй
WX = 14.2
FS.prism_xz(K.octa(WX, -FZ - 2.0, 2.0, 0.9, 0.6), -0.1, 0.8, SAND)
FS.loft([(WX - 0.5, 0.8, -FZ - 2.2), (WX + 0.5, 0.8, -FZ - 2.2), (WX + 0.5, 0.8, -FZ - 1.8), (WX - 0.5, 0.8, -FZ - 1.8)],
        [(WX - 0.3, 3.6, -FZ - 2.1), (WX + 0.3, 3.6, -FZ - 2.1), (WX + 0.3, 3.6, -FZ - 1.9), (WX - 0.3, 3.6, -FZ - 1.9)], DEEP)
FS.prism_xy([(WX, 3.4), (WX + 2.6, 5.0), (WX + 2.2, 5.6), (WX + 0.4, 4.4), (WX - 0.4, 4.4), (WX - 2.2, 5.6), (WX - 2.6, 5.0)],
            -FZ - 2.2, -FZ - 1.8, DEEP)
AX = -14.4
FS.box(AX - 0.25, AX + 0.25, -0.1, 4.6, -FZ - 2.0, -FZ - 1.6, IRON)
FS.box(AX - 1.2, AX + 1.2, 3.8, 4.2, -FZ - 2.0, -FZ - 1.6, IRON)
S.annulus(FS, (AX, 5.0, -FZ - 1.8), (0, 0, -1), 0.3, 0.6, 0.3, IRON, seg=10)
for e in (-1, 1):
    beam(FS, (AX, 0.4, -FZ - 1.8), (AX + e * 1.6, 1.6, -FZ - 1.8), 0.4, 0.3, IRON)
    FS.prism_xy([(AX + e * 1.6, 1.2), (AX + e * 2.1, 2.2), (AX + e * 1.3, 1.9)], -FZ - 2.0, -FZ - 1.6, IRON)
D.chain(FS, (AX, 5.4, -FZ - 1.8), (AX + 3.0, -0.1, -FZ - 2.6), 8, 0.2, IRON, sag=0.3)
for k, x in enumerate((-9.0, -6.4, 6.4, 9.0)):
    FS.prism_xz(K.ngon(x, -FZ - 2.0, 0.9, 8), -0.1, 1.0, "C8D0D8")
    coral(FS, x, -FZ - 2.0, 1.0, 2.0 + 0.4 * (k % 2), (CORAL, PURPLE, YEL, CORAL2)[k])
FS.prism_xz(K.ngon(FX + 1.6, -FZ - 2.0, 0.7, 10), -0.1, 1.4, "E04A3A")
FS.prism_xz(K.ngon(FX + 1.6, -FZ - 2.0, 0.75, 10), 0.6, 0.9, WHITE)
F.objects(False)

# ══ ИНТЕРЬЕР: тёмный зал аквариумов ═══════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.3
S.interior(F, "1E3260", "2A3A5A", "0E1A38", AQUA2, wain=(1.4, NAVY2), beams=None)
for k in range(7):  # своды-рёбра «подводного туннеля»
    z = -13.0 + 4.2 * k
    pts = [(-W + 0.9 + (2 * W - 1.8) * j / 12, C - 0.4 - 3.0 * (1 - ((-1 + 2 * j / 12) ** 2))) for j in range(13)]
    for a, b in zip(pts, pts[1:]):
        beam(IS, (a[0], a[1], z), (b[0], b[1], z), 0.5, 0.5, AQUA2 if k % 2 else "2A6A9A", up=(0, 0, 1))
F.objects(True)
for s in (-1, 1):  # аквариумы во всю боковую стену
    x0 = s * (W - 0.88)
    x1 = x0 - s * 2.6
    IS.box(*sorted((x0, x1)), 0.0, 1.6, -14.0, 6.0, IRON)
    IS.box(*sorted((x0, x1)), 10.6, 11.4, -14.0, 6.0, IRON)
    IG.box(*sorted((x0 - s * 0.12, x0 - s * 0.18)), 1.6, 10.6, -14.0, 6.0, "2E78A8")  # вода — фон за рыбами (стекло непрозрачно), глубже и темнее
    IS.box(*sorted((x0, x0 - s * 0.1)), 1.6, 10.6, -14.0, 6.0, DEEP)
    for z in (-14.0, -4.0, 6.0):
        IS.box(*sorted((x1 - s * 0.1, x1 + s * 0.2)), 1.6, 10.6, z - 0.25, z + 0.25, IRON)
    IS.box(*sorted((x0 - s * 0.1, x1 + s * 0.1)), 1.6, 2.2, -14.0, 6.0, SAND)
    for k in range(9):
        z = -13.0 + 2.2 * k
        coral(IS, x0 - s * 1.2, z, 2.2, 1.4 + 0.8 * rng(k, s), (CORAL, PURPLE, YEL, CORAL2, ORANGE)[k % 5])
        IS.loft([(x0 - s * 0.6, 2.2, z + 1.0), (x0 - s * 0.7, 2.2, z + 1.0), (x0 - s * 0.7, 2.2, z + 1.2), (x0 - s * 0.6, 2.2, z + 1.2)],
                [(x0 - s * 0.6, 6.0 + 3.0 * rng(k, 2), z + 1.4), (x0 - s * 0.7, 6.0 + 3.0 * rng(k, 2), z + 1.4),
                 (x0 - s * 0.7, 6.0 + 3.0 * rng(k, 2), z + 1.6), (x0 - s * 0.6, 6.0 + 3.0 * rng(k, 2), z + 1.6)], SEAWEED)
    for k in range(10):
        fish(IS, x0 - s * 1.6, 3.6 + 6.0 * rng(k, s, 3), -13.0 + 18.0 * rng(k, s, 4), 0.5 + 0.3 * rng(k, 5),
             (ORANGE, YEL, CORAL, AQUA, PURPLE, WHITE)[k % 6], d=(1 if k % 2 else -1), axis="x")
# медузы-светильники
for k, (x, z) in enumerate(((-7.0, -10.0), (6.0, -9.0), (-5.0, 3.0), (7.0, 4.0), (0.0, -12.0))):
    y = 11.0 + 1.2 * (k % 2)
    IS.box(x - 0.03, x + 0.03, y + 1.2, C - 0.4, z - 0.03, z + 0.03, "6A7A9A")
    IG.prism_xz(K.ngon(x, z, 1.1, 10), y, y + 0.5, "E8A8F0")
    IG.prism_xz(K.ngon(x, z, 0.75, 10), y + 0.5, y + 1.2, "F0C8F8")
    for j in range(5):
        a = 2 * math.pi * j / 5
        beam(IS, (x + 0.7 * math.cos(a), y, z + 0.7 * math.sin(a)), (x + 0.9 * math.cos(a + 0.4), y - 2.6 - 0.6 * (j % 2), z + 0.9 * math.sin(a + 0.4)),
             0.08, 0.08, "C8A0E0")
# скамьи и большой аквариум на дальней стене
for z in (-12.0, 6.0):
    for x in (-8.0, 8.0):
        IS.box(x - 2.0, x + 2.0, 1.2, 1.5, z - 0.6, z + 0.6, AQUA2)
        IS.box(x - 1.8, x - 1.4, 0.0, 1.2, z - 0.4, z + 0.4, IRON)
        IS.box(x + 1.4, x + 1.8, 0.0, 1.2, z - 0.4, z + 0.4, IRON)
IS.box(-6.0, 6.0, 1.0, 1.6, ZF + 0.88, ZF + 2.6, IRON)
IG.box(-5.8, 5.8, 1.6, 9.4, ZF + 1.02, ZF + 1.08, "2E78A8")  # вода — фон за рыбами, глубже и темнее
IS.box(-5.8, 5.8, 1.6, 9.4, ZF + 0.9, ZF + 1.0, DEEP)
for k in range(5):
    fish(IS, -4.0 + 2.0 * k, 3.4 + 4.6 * rng(k, 8), ZF + 1.7, 0.6, (YEL, ORANGE, WHITE, CORAL, AQUA)[k], d=(-1) ** k)
F.objects(False)
# постамент: коралловый риф с водяным кольцом
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, 0.5, "C8C0A8")
IG.prism_xz(K.ngon(px, pz, 3.9, 16), 0.5, 0.75, WATER)
IR.prism_xz(K.octa(px, pz, 2.9, 2.7, 1.0), 0.5, TOP, "E8B8A0")
F.objects(True)
for k in range(9):
    a = 2 * math.pi * k / 9
    coral(IS, px + 3.4 * math.cos(a), pz + 3.4 * math.sin(a), 0.5, 1.2 + 0.5 * (k % 2), (CORAL, PURPLE, YEL, CORAL2)[k % 4])
F.objects(False)
B.lift_leaves(IS, AQUA2, NAVY2)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, NAVY, SAND, NAVY, top=16.2)
SL.prism_xy(K.octa(0.0, 12.0, 3.8, 1.8, 1.0), -FZ - 1.8, -FZ, ORANGE)

F.build(exhibit=(PED[0], TOP, PED[1], 2.8), lamps=[("Hall", (0, 14, 6), 1300, (0.7, 0.85, 1.0)),
                                                   ("Spot", (0, 13, -3), 3600, (0.95, 0.98, 1.0)),
                                                   ("Tank", (-12, 6, -4), 900, (0.4, 0.8, 1.0))])
