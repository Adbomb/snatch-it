"""Этаж «Всевидящее око» музея-небоскрёба (одиннадцатая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — театр иллюзиониста. Снаружи — фиолетово-чёрный фасад со звёздами, бархатные шторы-кулисы по
обеим сторонам золотой двери, над входом — треугольный фронтон с одним большим символом-оком в лучах (знак
театра), афишные тумбы с цилиндром и колодой, огромный перевёрнутый цилиндр с выглядывающими ушами-кроликами
(без морды), ящик с пилой, хрустальный шар на подставке, гирлянда лампочек по краю кровли. Внутри — сцена и
зрительный зал: полукруглая сцена с бархатным занавесом и рампой, ряды кресел, ложи-балкончики по бокам, люстра,
реквизит (ящик-исчезатель, кольца, шкаф-портал), звёзды-блёстки на тёмном потолке; экспонат — на круглой
вращающейся тумбе фокусника со звёздами.
Запуск: blender --background --factory-startup --python scripts/blender/floor_illusion.py -- <репо> <превью>
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

PURPLE, PURPLE2, BLACK, GOLD, GOLD2, VELVET = "4A2A7A", "301A54", "1E1A26", "F0C040", "C8962A", "A81E3A"
VELVET2, WHITE, CRYSTAL, BULB, SILVER, PINK = "7A1428", "F4F0F0", "B8E0FF", "FFF0A0", "C8CCD4", "F0A0C0"

F = B.Floor("EY", "AllSeeingEye", quiet=(PURPLE2, "5A4A6A", "2A2A3A"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def star(p, x, y, z0, z1, r, col):
    p.prism_xy([(x + r * (1 if k % 2 == 0 else 0.42) * math.cos(math.pi / 2 + k * math.pi / 5),
                 y + r * (1 if k % 2 == 0 else 0.42) * math.sin(math.pi / 2 + k * math.pi / 5)) for k in range(10)], z0, z1, col)


def top_hat(p, x, z, y, s, upside=False):
    """Цилиндр фокусника: тулья, поля, лента; upside — перевёрнут."""
    if upside:
        p.prism_xz(K.ngon(x, z, 1.6 * s, 14), y, y + 0.2 * s, BLACK)
        p.prism_xz(K.ngon(x, z, 1.0 * s, 14), y + 0.2 * s, y + 2.2 * s, BLACK)
        p.prism_xz(K.ngon(x, z, 1.03 * s, 14), y + 0.3 * s, y + 0.7 * s, VELVET)
    else:
        p.prism_xz(K.ngon(x, z, 1.0 * s, 14), y + 0.2 * s, y + 2.2 * s, BLACK)
        p.prism_xz(K.ngon(x, z, 1.6 * s, 14), y, y + 0.2 * s, BLACK)
        p.prism_xz(K.ngon(x, z, 1.03 * s, 14), y + 0.2 * s, y + 0.6 * s, VELVET)


def curtain(p, x0, x1, y0, y1, z, col, n=6):
    """Бархатная штора складками."""
    for k in range(n):
        xa = x0 + (x1 - x0) * k / n
        d = 0.25 if k % 2 else 0.0
        p.box(xa, xa + (x1 - x0) / n + 0.02, y0, y1, z - 0.3 - d, z - d, col if k % 2 else VELVET2)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, PURPLE, BLACK, GOLD, "5A4A6A", BLACK, roof="flat", roof_col=PURPLE, top=16.0, band=(15.0, 15.4, GOLD),
         side=S.side_windows(F, GOLD, "2A1A3A", kind="arch", y0=8.0, y1=12.0, w=1.8, xs=(-8.90, -0.90, 7.10)))
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # звёзды по фасаду
    for k in range(9):
        a = -half + 2 * half * rng(k, fi, 9)
        y = 2.0 + 12.0 * rng(k, fi, 8)
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.94))
        pts = [(a + 0.35 * (1 if j % 2 == 0 else 0.42) * math.cos(math.pi / 2 + j * math.pi / 5),
                y + 0.35 * (1 if j % 2 == 0 else 0.42) * math.sin(math.pi / 2 + j * math.pi / 5)) for j in range(10)]
        (FS.prism_zy if axis == "x" else FS.prism_xy)(pts, d0, d1, GOLD)
# гирлянда лампочек по краю кровли
for k in range(24):
    x = -FX + 0.6 + (2 * FX - 1.2) * k / 23
    FG.prism_xy(K.ngon(x, 15.7, 0.18, 6), -FZ - 1.45, -FZ - 1.35, BULB)
# золотая дверь, кулисы-шторы, фронтон с оком в лучах
FS.box(-2.4, 2.4, 1.0, 8.4, -FZ - 1.0, -FZ - 0.88, GOLD2)
for k in range(2):
    FS.box(-2.1 + 2.25 * k, -0.15 + 2.25 * k, 1.4, 8.0, -FZ - 1.05, -FZ - 1.0, GOLD)
for e in (-1, 1):
    curtain(FS, *sorted((e * 3.0, e * 7.6)), 1.0, 11.0, -FZ - 0.88, VELVET)
    FS.box(*sorted((e * 3.0, e * 7.6)), 10.8, 11.4, -FZ - 1.5, -FZ - 0.88, GOLD)
    beam(FS, (e * 3.2, 5.0, -FZ - 1.4), (e * 7.4, 4.4, -FZ - 1.4), 0.12, 0.12, GOLD)
FR.prism_xy([(-7.8, 11.4), (7.8, 11.4), (0.0, 15.0)], -FZ - 1.3, -FZ - 0.88, PURPLE2)
FS.frame_xy([(-8.2, 11.2), (8.2, 11.2), (0.0, 15.3)], [(-7.4, 11.6), (7.4, 11.6), (0.0, 14.7)], -FZ - 1.45, -FZ - 0.88, GOLD)
FS.prism_xy(K.octa(0.0, 12.8, 1.4, 0.7, 0.5), -FZ - 1.45, -FZ - 1.3, WHITE)
FS.prism_xy(K.ngon(0.0, 12.8, 0.5, 10), -FZ - 1.55, -FZ - 1.45, PURPLE)
FS.prism_xy(K.ngon(0.0, 12.8, 0.22, 8), -FZ - 1.6, -FZ - 1.55, BLACK)
for k in range(9):
    a = math.pi * (0.1 + 0.8 * k / 8)
    beam(FS, (2.0 * math.cos(a), 12.8 + 1.0 * math.sin(a), -FZ - 1.42), (3.4 * math.cos(a), 12.8 + 1.9 * math.sin(a), -FZ - 1.42),
         0.12, 0.08, GOLD, up=(0, 0, 1))
# афишные тумбы, перевёрнутый цилиндр с ушами, ящик с пилой, хрустальный шар
F.objects(True)
for k, x in enumerate((-14.6, 14.6)):
    FS.prism_xz(K.ngon(x, -FZ - 2.0, 1.1, 12), -0.1, 5.4, VELVET if k else PURPLE2)
    FS.cone([(x + 1.2 * math.cos(a), 5.4, -FZ - 2.0 + 1.2 * math.sin(a)) for a in [2 * math.pi * j / 12 for j in range(12)]],
            (x, 6.6, -FZ - 2.0), GOLD)
    FS.prism_xz(K.ngon(x, -FZ - 2.0, 1.15, 12), 1.0, 1.3, GOLD)
    if k == 0:
        top_hat(FS, x, -FZ - 2.0, 6.6, 0.4)
    else:
        for j in range(3):
            FS.box(x - 0.7 + 0.5 * j, x - 0.3 + 0.5 * j, 2.6 + 0.6 * j, 3.2 + 0.6 * j, -FZ - 3.16, -FZ - 3.1, (WHITE, VELVET, WHITE)[j])
top_hat(FS, -9.6, -FZ - 1.9, -0.1, 0.6, upside=True)
for e in (-1, 1):
    FS.loft([(-9.6 + e * 0.3 - 0.18, 0.9, -FZ - 2.0), (-9.6 + e * 0.3 + 0.18, 0.9, -FZ - 2.0), (-9.6 + e * 0.3 + 0.18, 0.9, -FZ - 1.8),
             (-9.6 + e * 0.3 - 0.18, 0.9, -FZ - 1.8)],
            [(-9.6 + e * 0.45 - 0.14, 2.8, -FZ - 2.0), (-9.6 + e * 0.45 + 0.14, 2.8, -FZ - 2.0), (-9.6 + e * 0.45 + 0.14, 2.8, -FZ - 1.8),
             (-9.6 + e * 0.45 - 0.14, 2.8, -FZ - 1.8)], WHITE)
    FS.box(-9.6 + e * 0.42 - 0.07, -9.6 + e * 0.42 + 0.07, 1.6, 2.6, -FZ - 2.03, -FZ - 2.0, PINK)
FS.box(5.6, 10.6, 0.8, 2.6, -FZ - 2.6, -FZ - 1.2, VELVET)
for x in (5.6, 10.6):
    FS.box(x - 0.15, x + 0.15, -0.1, 0.8, -FZ - 2.5, -FZ - 1.3, GOLD)
for k in range(4):
    star(FS, 6.4 + 1.2 * k, 1.7, -FZ - 2.64, -FZ - 2.6, 0.35, GOLD)
FS.box(7.9, 8.1, 2.6, 4.2, -FZ - 2.4, -FZ - 1.4, SILVER)
FS.box(7.85, 8.15, 4.2, 4.6, -FZ - 2.0, -FZ - 1.8, "6A4A2A")
FS.prism_xz(K.ngon(-5.0, -FZ - 1.8, 0.4, 8), -0.1, 1.8, GOLD2)
FS.prism_xz(K.ngon(-5.0, -FZ - 1.8, 0.7, 8), 1.8, 2.0, GOLD)
F.objects(False)
for k in range(6):  # хрустальный шар поясами
    t0, t1 = -1 + 2 * k / 6, -1 + 2 * (k + 1) / 6
    r = 0.8 * math.cos(math.asin(max(-1.0, min(1.0, (t0 + t1) / 2))))
    FG.prism_xz(K.ngon(-5.0, -FZ - 1.8, r + 0.05, 10), 2.8 + 0.8 * t0, 2.8 + 0.8 * t1, CRYSTAL)

# ══ ИНТЕРЬЕР: сцена и зрительный зал ══════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.3
S.interior(F, PURPLE2, "3A2A4A", BLACK, GOLD, wain=(2.2, VELVET2), beams=None)
for k in range(40):  # блёстки-звёзды на потолке
    x, z = -W + 1.0 + (2 * W - 2.0) * rng(k, 21), ZF + 1.0 + (ZB - ZF - 2.0) * rng(k, 22)
    IS.prism_xz([(x + 0.3 * (1 if j % 2 == 0 else 0.42) * math.cos(j * math.pi / 5), z + 0.3 * (1 if j % 2 == 0 else 0.42) * math.sin(j * math.pi / 5))
                 for j in range(10)], C - 0.05, C - 0.02, GOLD)
# сцена у дальней стены: полукруглый подиум, занавес, рампа, портал
IR.prism_xz([(-10.0, ZF + 0.9)] + [(10.0 * math.cos(math.pi * k / 12), ZF + 0.9 + 4.6 * math.sin(math.pi * k / 12)) for k in range(13)],
            0.0, 1.0, "6A3A2A")
IS.prism_xz([(-10.1, ZF + 0.9)] + [(10.1 * math.cos(math.pi * k / 12), ZF + 0.9 + 4.7 * math.sin(math.pi * k / 12)) for k in range(13)],
            1.0, 1.1, GOLD)
curtain(IS, -10.0, 10.0, 1.1, 12.0, ZF + 1.6, VELVET, n=14)
IS.box(-11.0, 11.0, 12.0, 13.6, ZF + 0.9, ZF + 2.2, GOLD2)
for e in (-1, 1):
    IS.box(e * 10.0 - 1.0, e * 10.0 + 1.0, 0.0, 13.6, ZF + 0.9, ZF + 2.2, GOLD2)
for k in range(9):
    a = math.pi * (k + 0.5) / 9
    IG.prism_xz(K.ngon(9.4 * math.cos(a), ZF + 0.9 + 4.3 * math.sin(a), 0.2, 6), 1.1, 1.3, BULB)
F.objects(True)
for s in (-1, 1):  # ряды кресел и ложи-балкончики
    for j in range(3):
        for k in range(3):
            x = s * (7.0 + 2.0 * k)
            z = 1.0 + 2.6 * j
            IS.box(x - 0.8, x + 0.8, 0.0, 1.2, z - 0.7, z + 0.7, VELVET)
            IS.box(x - 0.8, x + 0.8, 1.2, 2.8, z + 0.5, z + 0.8, VELVET2)
    IS.box(*sorted((s * (W - 0.88), s * (W - 3.4))), 6.6, 7.0, -10.0, -2.0, GOLD2)
    IS.box(*sorted((s * (W - 3.2), s * (W - 3.4))), 7.0, 8.4, -10.0, -2.0, VELVET)
    IS.box(*sorted((s * (W - 3.1), s * (W - 3.5))), 8.4, 8.6, -10.0, -2.0, GOLD)
    for z in (-9.4, -6.0, -2.6):  # кронштейны-консоли под ложей
        xw = s * (W - 0.88)
        IS.prism_xy([(xw, 6.6), (xw - s * 2.2, 6.6), (xw - s * 0.5, 5.2), (xw, 4.4)], z - 0.22, z + 0.22, GOLD2)
    IS.box(*sorted((s * (W - 0.88), s * (W - 0.96))), 7.0, 10.4, -7.2, -4.8, BLACK)  # дверь в ложу
    IS.box(*sorted((s * (W - 0.88), s * (W - 1.02))), 10.4, 10.7, -7.5, -4.5, GOLD)
    for z0, z1 in ((-14.6, -11.0), (-1.0, 3.0), (4.0, 8.0), (9.0, 13.0)):  # панели в золотых рамах
        IS.frame_zy(K.rect(z0, z1, 9.0, 14.0), K.rect(z0 + 0.25, z1 - 0.25, 9.25, 13.75), *sorted((s * (W - 0.88), s * (W - 1.02))), GOLD)
        IS.box(*sorted((s * (W - 0.88), s * (W - 0.94))), 9.25, 13.75, z0 + 0.25, z1 - 0.25, PURPLE)
# реквизит: ящик-исчезатель, кольца, шкаф-портал
IS.box(-12.4, -9.6, 0.0, 4.4, -12.6, -10.4, PURPLE)
for k in range(3):
    star(IS, -11.0, 1.2 + 1.3 * k, -10.42, -10.38, 0.4, GOLD)
for k in range(3):
    S.annulus(IS, (11.0 + 0.6 * k, 3.4 + 0.5 * k, -11.0), (0, 0, 1), 0.7, 0.85, 0.08, SILVER, seg=12)
IS.box(9.4, 13.2, 0.0, 6.0, -13.6, -12.8, BLACK)
IS.box(9.8, 12.8, 0.4, 5.6, -12.84, -12.78, PURPLE2)
F.objects(False)
IS.box(-0.04, 0.04, C - 2.6, C - 0.2, 4.0 - 0.04, 4.0 + 0.04, GOLD2)  # люстра
for k in range(3):
    S.annulus(IS, (0.0, C - 2.6 - 0.7 * k, 4.0), (0, 1, 0), 1.6 - 0.4 * k, 1.75 - 0.4 * k, 0.1, GOLD, seg=14)
    for j in range(8 - 2 * k):
        a = 2 * math.pi * j / (8 - 2 * k)
        IG.prism_xz(K.ngon((1.65 - 0.4 * k) * math.cos(a), 4.0 + (1.65 - 0.4 * k) * math.sin(a), 0.1, 6), C - 2.5 - 0.7 * k, C - 2.2 - 0.7 * k, BULB)
# постамент: круглая вращающаяся тумба фокусника со звёздами
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 3.4, 16), 0.0, 0.3, GOLD2)
IR.prism_xz(K.ngon(px, pz, 3.0, 16), 0.3, TOP - 0.15, PURPLE)
IS.prism_xz(K.ngon(px, pz, 3.2, 16), TOP - 0.15, TOP, GOLD)
for k in range(8):
    a = 2 * math.pi * k / 8
    sx, sz = px + 3.02 * math.cos(a), pz + 3.02 * math.sin(a)
    IS.prism_xz(K.ngon(sx, sz, 0.22, 5), 0.6, 0.9, GOLD)
B.lift_leaves(IS, PURPLE2, GOLD)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, PURPLE, "5A4A6A", PURPLE, top=16.0)
SL.prism_xy([(-7.8, 11.4), (7.8, 11.4), (0.0, 15.0)], -FZ - 1.3, -FZ, GOLD)

F.build(exhibit=(PED[0], TOP, PED[1], 2.3), lamps=[("Hall", (0, 14, 6), 1400, (0.95, 0.85, 1.0)),
                                                   ("Spot", (0, 13, -3), 4000, (1.0, 0.96, 0.9)),
                                                   ("Stage", (0, 6, -12), 900, (1.0, 0.5, 0.6))])
