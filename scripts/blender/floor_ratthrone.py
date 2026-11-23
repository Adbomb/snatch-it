"""Этаж «Крысиный трон» музея-небоскрёба (десятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — подземный дворец крысиного короля в старом коллекторе. Снаружи — тёмная кирпичная стена коллектора
с большим арочным тоннелем за чугунной решёткой, из которого течёт ручей в канавку, по сторонам — толстые трубы
с фланцами и вентилями, над аркой — золотая корона, сырно-жёлтые знамёна, факелы, крысиные дверцы-арочки,
кучи «сокровищ» (ящики, банки, монеты), люк и лесенка. Внутри — тронный зал: кирпичные своды-рёбра, трубы под
потолком, красная ковровая дорожка, знамёна с короной, канделябры со свечами, горы монет, головки сыра,
настенные факелы; экспонат — на ступенчатом бархатном помосте с золотой каймой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_ratthrone.py -- <репо> <превью>
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

BRICK, BRICK2, BRICK3, IRON, IRON2, GOLD = "6A4A44", "523834", "86605A", "4A4E56", "2E3238", "F2C23A"
CHEESE, CHEESE2, VELVET, VELVET2, WATER, MOSS = "F6CE4A", "E0A830", "8A1E3A", "6A142C", "5A9A8A", "5A7A3A"
CANDLE, FLAME, WOOD = "F4ECD8", "FFB040", "7A5232"

F = B.Floor("RT", "RatThrone", quiet=(BRICK2, "6A6058", "4A3A38"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def crown(p, x, y, z, s, col):
    """Корона: обод и пять зубцов с шариками (в плоскости xy)."""
    p.box(x - 1.4 * s, x + 1.4 * s, y, y + 0.6 * s, z - 0.15, z + 0.15, col)
    for k in range(5):
        cx = x - 1.2 * s + 0.6 * s * k
        h = 1.4 * s if k % 2 == 0 else 1.0 * s
        p.prism_xy([(cx - 0.28 * s, y + 0.6 * s), (cx + 0.28 * s, y + 0.6 * s), (cx, y + 0.6 * s + h)], z - 0.12, z + 0.12, col)
        p.prism_xy(K.ngon(cx, y + 0.6 * s + h + 0.15 * s, 0.17 * s, 6), z - 0.14, z + 0.14, col)


def coins(p, x, z, y, r, h):
    for k in range(4):
        rr = r * (1 - k / 4.5)
        p.prism_xz(K.octa(x, z, rr, rr * 0.8, rr * 0.3), y + h * k / 4, y + h * (k + 1) / 4, GOLD if k % 2 == 0 else "E8B030")


def cheese_wheel(p, x, z, y, r, h):
    p.prism_xz(K.ngon(x, z, r, 12), y, y + h, CHEESE)
    p.prism_xz(K.ngon(x, z, r * 1.02, 12), y + h * 0.4, y + h * 0.6, CHEESE2)


# ══ ФАСАД: стена коллектора ═══════════════════════════════════════════════════════════════════════════════════
S.facade(F, BRICK, BRICK2, BRICK3, "5A5048", "2A2224", roof="crenel", roof_col=BRICK, top=16.0, pilaster=BRICK2,
         side=S.side_windows(F, IRON, "2A2A30", kind="arch", y0=9.0, y1=13.0, w=1.8, xs=(-8.90, -0.90, 7.10)))
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # кирпичные ряды и мох понизу
    for j in range(6):
        y = 2.0 + 2.2 * j
        slab(FS, axis, fixed, out, 0.93, -half, half, y - 0.05, y + 0.05, BRICK2)
    for k in range(5):
        a0 = -half + 2 * half * rng(k, fi)
        slab(FS, axis, fixed, out, 0.96, a0, a0 + 1.6, 1.0, 1.6 + 1.0 * rng(k, 2, fi), MOSS)
# большой арочный тоннель с чугунной решёткой и ручьём
TW, TH = 9.0, 11.0
arc_o = [(-TW / 2 - 1.0, 1.0), (TW / 2 + 1.0, 1.0)] + [((TW / 2 + 1.0) * math.cos(math.pi * k / 8), TH - TW / 2 + (TW / 2 + 1.0) * math.sin(math.pi * k / 8))
                                                       for k in range(9)]
arc_i = [(-TW / 2, 1.0), (TW / 2, 1.0)] + [(TW / 2 * math.cos(math.pi * k / 8), TH - TW / 2 + TW / 2 * math.sin(math.pi * k / 8)) for k in range(9)]
FS.frame_xy(arc_o, arc_i, -FZ - 1.6, -FZ - 0.88, BRICK3)
FS.prism_xy(arc_i, -FZ - 0.92, -FZ - 0.88, "141010")
for k in range(9):
    x = -TW / 2 + 0.5 + (TW - 1.0) * k / 8
    top = TH - TW / 2 + math.sqrt(max((TW / 2) ** 2 - x * x, 0.0)) - 0.2
    FS.prism_xz(K.ngon(x, -FZ - 1.2, 0.16, 6), 1.0, top, IRON)
for y in (3.6, 7.2):
    FS.box(-TW / 2, TW / 2, y - 0.15, y + 0.15, -FZ - 1.3, -FZ - 1.1, IRON)
for k in range(9):  # замковые камни свода
    a = math.pi * k / 8
    FR.box((TW / 2 + 0.5) * math.cos(a) - 0.4, (TW / 2 + 0.5) * math.cos(a) + 0.4, TH - TW / 2 + (TW / 2 + 0.5) * math.sin(a) - 0.4,
           TH - TW / 2 + (TW / 2 + 0.5) * math.sin(a) + 0.4, -FZ - 1.8, -FZ - 1.5, BRICK3 if k % 2 else BRICK)
FR.box(-TW / 2 - 0.6, TW / 2 + 0.6, -0.1, 1.0, -FZ - 3.0, -FZ - 0.88, BRICK3)
FG.box(-2.0, 2.0, 0.95, 1.05, -FZ - 3.0, -FZ - 0.9, WATER)
FG.box(-TW / 2 - 0.4, TW / 2 + 0.4, -0.06, 0.0, -FZ - 2.9, -FZ - 2.3, WATER)
# корона над аркой и знамёна
crown(FS, 0.0, 12.4, -FZ - 1.7, 1.3, GOLD)
for x in (-13.4, -9.0, 9.0, 13.4):
    FS.box(x - 0.15, x + 0.15, 15.2, 15.5, -FZ - 1.6, -FZ - 0.88, IRON2)
    FS.prism_xy([(x - 1.2, 15.2), (x + 1.2, 15.2), (x + 1.2, 9.6), (x, 10.4), (x - 1.2, 9.6)], -FZ - 1.2, -FZ - 1.1, CHEESE)
    FS.prism_xy([(x - 0.6, 13.6), (x + 0.6, 13.6), (x, 12.4)], -FZ - 1.24, -FZ - 1.2, VELVET)
# толстые трубы с фланцами и вентилями
for e in (-1, 1):
    x0 = e * 7.2
    FS.prism_zy(K.ngon(-FZ - 2.0, 4.0, 0.8, 12), *sorted((x0, e * (FX - 0.5))), IRON)
    FS.prism_xz(K.ngon(e * (FX - 0.5), -FZ - 2.0, 0.8, 12), -0.1, 4.8, IRON)
    for x in (x0 + e * 2.0, x0 + e * 6.0):
        FS.prism_zy(K.ngon(-FZ - 2.0, 4.0, 1.0, 12), x - 0.2, x + 0.2, IRON2)
    S.annulus(FS, (x0 + e * 4.0, 5.2, -FZ - 2.0), (0, 1, 0), 0.4, 0.7, 0.12, "C83A2A", seg=10)
# факелы, крысиные дверцы, сокровища, люк, лесенка
for x in (-6.4, 6.4):
    D.torch(FS, FG, x, 9.0, -FZ - 1.5, h=2.4)
for x in (-15.6, 14.6):
    FS.prism_xy([(x - 0.7, 1.0), (x + 0.7, 1.0)] + [(x + 0.7 * math.cos(math.pi * k / 6), 2.4 + 0.7 * math.sin(math.pi * k / 6)) for k in range(7)],
                -FZ - 0.94, -FZ - 0.88, WOOD)
F.objects(True)
coins(FS, -11.4, -FZ - 2.2, -0.1, 1.2, 1.2)
coins(FS, 11.2, -FZ - 2.4, -0.1, 1.0, 0.9)
D.crate(FS, -8.4, -FZ - 2.2, y=-0.1, s=1.2, wood=WOOD, board="5A3A22")
cheese_wheel(FS, 8.0, -FZ - 2.2, -0.1, 0.9, 0.7)
cheese_wheel(FS, 8.2, -FZ - 2.2, 0.6, 0.8, 0.6)
FS.prism_xz(K.ngon(-16.4, -FZ - 2.4, 0.9, 12), -0.1, 0.05, IRON2)
for k in range(5):
    FS.box(-16.8, -16.0, -0.06, 0.08, -FZ - 2.8 + 0.2 * k, -FZ - 2.74 + 0.2 * k, IRON)
F.objects(False)
for e in (-0.5, 0.5):
    FS.box(16.4 + e - 0.06, 16.4 + e + 0.06, -0.1, 8.0, -FZ - 1.1, -FZ - 1.0, IRON)
for k in range(10):
    FS.box(15.9, 16.9, 0.6 + 0.75 * k, 0.7 + 0.75 * k, -FZ - 1.1, -FZ - 1.0, IRON)

# ══ ИНТЕРЬЕР: тронный зал коллектора ══════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.8
S.interior(F, BRICK3, "5A5048", BRICK2, GOLD, wain=(2.4, BRICK2), beams=None)
for k in range(6):  # кирпичные своды-рёбра поперёк зала
    z = -13.0 + 4.2 * k
    pts = [(-W + 0.9 + (2 * W - 1.8) * j / 12, C - 0.4 - 4.5 * (-1 + 2 * j / 12) ** 2) for j in range(13)]
    for a, b in zip(pts, pts[1:]):
        beam(IR, (a[0], a[1], z), (b[0], b[1], z), 1.0, 1.0, BRICK2, up=(0, 0, 1))
for x in (-8.0, 8.0):  # трубы под потолком
    IS.prism_xy(K.ngon(x, C - 2.4, 0.5, 10), ZF + 0.9, ZB - 0.9, IRON)
    for z in (-10.0, -2.0, 6.0):
        IS.prism_xy(K.ngon(x, C - 2.4, 0.66, 10), z - 0.15, z + 0.15, IRON2)
# красная ковровая дорожка от лифта к помосту
IQ.box(-2.0, 2.0, 0.02, 0.06, 1.0, ZB - 0.9, VELVET)
IQ.box(-2.3, 2.3, 0.02, 0.04, 1.0, ZB - 0.9, GOLD)
F.objects(True)
for s in (-1, 1):  # знамёна с короной, канделябры, горы монет, сыры вдоль стен
    x = s * (W - 0.95)
    for z in (-11.0, -3.0, 5.0):
        IS.box(*sorted((x, x - s * 0.1)), 6.0, 13.0, z - 1.4, z + 1.4, VELVET)
        IS.prism_zy([(z - 1.4, 6.0), (z + 1.4, 6.0), (z, 5.0)], *sorted((x, x - s * 0.1)), VELVET)
        IS.box(*sorted((x - s * 0.1, x - s * 0.16)), 9.8, 10.4, z - 0.8, z + 0.8, GOLD)
        for k in range(3):
            IS.prism_zy([(z - 0.7 + 0.7 * k - 0.2, 10.4), (z - 0.7 + 0.7 * k + 0.2, 10.4), (z - 0.7 + 0.7 * k, 11.2)],
                        *sorted((x - s * 0.1, x - s * 0.16)), GOLD)
    for z in (-7.0, 1.0):
        cx = s * (W - 3.0)
        IS.prism_xz(K.ngon(cx, z, 0.6, 8), 0.0, 0.3, GOLD)
        IS.prism_xz(K.ngon(cx, z, 0.15, 6), 0.3, 4.0, GOLD)
        IS.box(cx - 1.2, cx + 1.2, 4.0, 4.2, z - 0.1, z + 0.1, GOLD)
        for e in (-1.1, 0.0, 1.1):
            IS.prism_xz(K.ngon(cx + e, z, 0.18, 6), 4.2, 5.2, CANDLE)
            IG.prism_xz(K.ngon(cx + e, z, 0.1, 6), 5.2, 5.6, FLAME)
    coins(IS, s * (W - 3.4), -12.4, 0.0, 1.8, 1.6)
    cheese_wheel(IS, s * (W - 3.0), 7.0, 0.0, 1.2, 1.0)
    cheese_wheel(IS, s * (W - 3.1), 7.0, 1.0, 1.0, 0.8)
F.objects(False)
for x in (-6.0, 6.0):
    D.torch(IS, IG, x, 7.0, ZF + 1.4, h=2.4)
# постамент: ступенчатый бархатный помост с золотой каймой
px, pz = PED
for k, (r, y0, y1) in enumerate(((4.6, 0.0, 0.6), (4.1, 0.6, 1.2), (3.7, 1.2, TOP))):
    IR.box(px - r, px + r, y0, y1 - 0.1, pz - r, pz + r, VELVET if k % 2 == 0 else VELVET2)
    IS.box(px - r - 0.05, px + r + 0.05, y1 - 0.1, y1, pz - r - 0.05, pz + r + 0.05, GOLD)
F.objects(True)
for k in range(4):
    a = math.pi / 2 * k + math.pi / 4
    coins(IS, px + 7.0 * math.cos(a), pz + 7.0 * math.sin(a), 0.0, 0.8, 0.8)
F.objects(False)
B.lift_leaves(IS, IRON2, GOLD)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, BRICK, "5A5048", BRICK, top=16.0)
SL.prism_xy(arc_o, -FZ - 1.6, -FZ, BRICK3)

F.build(exhibit=(PED[0], TOP, PED[1], 2.1), lamps=[("Hall", (0, 14, 6), 1400, (1.0, 0.85, 0.7)),
                                                   ("Spot", (0, 13, -3), 3800, (1.0, 0.95, 0.85)),
                                                   ("Torch", (0, 7, -13), 800, (1.0, 0.6, 0.3))])
