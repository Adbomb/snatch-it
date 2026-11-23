"""Этаж «Египетский саркофаг» музея-небоскрёба (одиннадцатая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — ночная колоннада Луксорского храма. Снаружи — открытая колоннада: ряд толстых колонн-папирусов
с закрытыми бутонами-капителями и цветными поясами, на них — тяжёлый архитрав с иероглифическим фризом
(простые знаки: анх, солнечный круг, волны, перо, тростник), за колоннами — тёмно-синяя стена
со звёздами, перед колоннадой — аллея с факелами и низкими сфинксами-постаментами без голов (только лапы и
постамент), каменные плиты, бассейн-канал. Внутри — гипостильный зал: восемь массивных колонн с росписью,
звёздный потолок, саркофаги-ящики и канопы в нишах, свет факелов; экспонат — на погребальных санях
(низкий постамент-полозья с золотыми кольцами).
Запуск: blender --background --factory-startup --python scripts/blender/floor_luxor.py -- <репо> <превью>
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

SAND, SAND2, SAND3, NIGHT, NIGHT2, GOLD = "E0C08A", "C8A470", "F0DCB0", "1A2A5A", "122046", "E8B840"
RED, TEAL, BLUE, WATER, FIRE, WOOD = "C24A3A", "2AA8A0", "2A5AB0", "3A8AC8", "FF9A30", "8A5A30"

F = B.Floor("LX", "EgyptianSarcophagus", quiet=(SAND2, "B89A70", "2A3A6A"), bevel_min=1.2)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def bud_column(p, x, z, y0, y1, r, cols=(RED, TEAL, BLUE)):
    """Колонна с закрытым бутоном: ствол, цветные пояса, бутон-капитель, абака."""
    p.prism_xz(K.ngon(x, z, r * 0.9, 12), y0, y0 + 0.8, SAND2)
    p.loft([(x + r * math.cos(a), y0 + 0.8, z + r * math.sin(a)) for a in [2 * math.pi * k / 12 for k in range(12)]],
           [(x + r * 0.86 * math.cos(a), y1 - 2.4, z + r * 0.86 * math.sin(a)) for a in [2 * math.pi * k / 12 for k in range(12)]], SAND)
    for j, c in enumerate(cols):
        y = y1 - 3.6 + 0.4 * j
        p.prism_xz(K.ngon(x, z, r * 0.9, 12), y, y + 0.3, c)
    p.loft([(x + r * 0.86 * math.cos(a), y1 - 2.4, z + r * 0.86 * math.sin(a)) for a in [2 * math.pi * k / 12 for k in range(12)]],
           [(x + r * 1.15 * math.cos(a), y1 - 1.4, z + r * 1.15 * math.sin(a)) for a in [2 * math.pi * k / 12 for k in range(12)]], SAND3)
    p.loft([(x + r * 1.15 * math.cos(a), y1 - 1.4, z + r * 1.15 * math.sin(a)) for a in [2 * math.pi * k / 12 for k in range(12)]],
           [(x + r * 0.7 * math.cos(a), y1 - 0.5, z + r * 0.7 * math.sin(a)) for a in [2 * math.pi * k / 12 for k in range(12)]], SAND3)
    p.box(x - r * 0.9, x + r * 0.9, y1 - 0.5, y1, z - r * 0.9, z + r * 0.9, SAND2)


def glyph(p, kind, x, y, z0, z1, s, col):
    """Простой знак фриза: 0 — анх, 1 — круг-солнце, 2 — волны, 3 — перо, 4 — тростник."""
    if kind == 0:
        p.box(x - 0.08 * s, x + 0.08 * s, y - 0.6 * s, y + 0.1 * s, z0, z1, col)
        p.box(x - 0.35 * s, x + 0.35 * s, y, y + 0.14 * s, z0, z1, col)
        p.prism_xy(K.ngon(x, y + 0.4 * s, 0.25 * s, 8), z0, z1, col)
    elif kind == 1:
        p.prism_xy(K.ngon(x, y, 0.35 * s, 10), z0, z1, col)
    elif kind == 2:
        for k in range(3):
            p.box(x - 0.4 * s, x + 0.4 * s, y - 0.3 * s + 0.25 * s * k, y - 0.2 * s + 0.25 * s * k, z0, z1, col)
    elif kind == 3:
        p.prism_xy([(x - 0.12 * s, y - 0.5 * s), (x + 0.12 * s, y - 0.5 * s), (x + 0.25 * s, y + 0.3 * s), (x, y + 0.55 * s), (x - 0.2 * s, y + 0.3 * s)],
                   z0, z1, col)
    else:
        p.box(x - 0.06 * s, x + 0.06 * s, y - 0.5 * s, y + 0.4 * s, z0, z1, col)
        p.prism_xy([(x, y + 0.4 * s), (x + 0.3 * s, y + 0.1 * s), (x + 0.05 * s, y + 0.15 * s)], z0, z1, col)


# ══ ФАСАД: колоннада ══════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, NIGHT, SAND2, SAND, "B89A70", NIGHT2, roof="flat", roof_col=SAND, top=15.4,
         side=S.side_windows(F, SAND2, "0E1830", kind="slit", y0=6.0, y1=11.0, w=1.2, xs=(-9.0, -3.0, 3.0, 9.0)))
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # звёзды на ночной стене
    for k in range(10):
        a = -half + 2 * half * rng(k, fi)
        y = 3.0 + 10.0 * rng(k, fi, 3)
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
        (FS.prism_zy if axis == "x" else FS.prism_xy)(K.ngon(a, y, 0.2, 5), d0, d1, GOLD)
# колоннада и архитрав с фризом знаков
for k in range(6):
    x = -15.0 + 6.0 * k
    bud_column(FR, x, -FZ - 2.0, 0.0, 13.0, 1.0)
FR.box(-FX - 0.4, FX + 0.4, 13.0, 15.4, -FZ - 3.2, -FZ - 0.88, SAND)
FS.box(-FX - 0.4, FX + 0.4, 14.9, 15.2, -FZ - 3.3, -FZ - 3.2, BLUE)
for k in range(22):
    x = -FX + 1.0 + (2 * FX - 2.0) * k / 21
    glyph(FS, k % 5, x, 13.9, -FZ - 3.28, -FZ - 3.2, 0.9, (BLUE, RED, TEAL, GOLD, BLUE)[k % 5])
# тёмный вход в глубине между центральными колоннами
FS.box(-2.4, 2.4, 1.0, 9.0, -FZ - 0.92, -FZ - 0.88, "0A0A14")
FS.frame_xy(K.rect(-2.8, 2.8, 1.0, 9.4), K.rect(-2.4, 2.4, 1.0, 9.0), -FZ - 1.1, -FZ - 0.88, GOLD)
# аллея: каменные плиты, канал, факелы, постаменты-сфинксы без голов (лапы на плинте)
for k in range(9):
    FQ.box(-FX - 2.6 + 4.6 * k, -FX - 2.6 + 4.6 * k + 4.4, -0.1, -0.04, -FZ - 3.4, -FZ - 0.9, SAND3 if k % 2 else SAND2)
FR.box(-4.0, 4.0, -0.1, 0.3, -FZ - 3.4, -FZ - 2.6, SAND2)
FG.box(-3.6, 3.6, 0.2, 0.32, -FZ - 3.3, -FZ - 2.7, WATER)
for x in (-12.0, 12.0, -17.6, 17.6):  # факелы между колоннами
    D.torch(FS, FG, x, -0.1, -FZ - 3.0, h=3.2)
F.objects(True)
for x in (-6.0, 6.0):  # постаменты-сфинксы между колоннами
    FS.box(x - 1.4, x + 1.4, -0.1, 0.9, -FZ - 3.4, -FZ - 1.2, SAND2)
    FS.loft([(x - 1.0, 0.9, -FZ - 3.2), (x + 1.0, 0.9, -FZ - 3.2), (x + 1.0, 0.9, -FZ - 1.4), (x - 1.0, 0.9, -FZ - 1.4)],
            [(x - 0.8, 2.2, -FZ - 2.6), (x + 0.8, 2.2, -FZ - 2.6), (x + 0.8, 2.2, -FZ - 1.4), (x - 0.8, 2.2, -FZ - 1.4)], SAND)
    for e in (-0.5, 0.5):
        FS.box(x + e - 0.3, x + e + 0.3, 0.9, 1.4, -FZ - 3.5, -FZ - 2.5, SAND)
F.objects(False)

# ══ ИНТЕРЬЕР: гипостильный зал ════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.0
S.interior(F, SAND, "B89A70", NIGHT, GOLD, wain=(1.4, SAND2), beams=None)
for k in range(40):  # звёзды на потолке
    x, z = -W + 1.0 + (2 * W - 2.0) * rng(k, 11), ZF + 1.0 + (ZB - ZF - 2.0) * rng(k, 12)
    IS.prism_xz(K.ngon(x, z, 0.25, 5), C - 0.05, C - 0.02, GOLD)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS[:3]):  # фриз знаков по стенам
    for k in range(int(2 * half // 1.6)):
        a = -half + 0.8 + 1.6 * k
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.93))
        if axis == "z":
            glyph(IS, k % 5, a, 11.0, d0, d1, 1.0, (BLUE, RED, TEAL, GOLD, BLUE)[k % 5])
    slab(IS, axis, fixed, out, 0.94, -half, half, 12.0, 12.3, BLUE)
    slab(IS, axis, fixed, out, 0.94, -half, half, 9.6, 9.9, RED)
for x in (-11.4, -7.2, 7.2, 11.4):  # массивные колонны (проход к экспонату шире)
    for z in (-11.0, 4.0):
        bud_column(IR, x, z, 0.0, C - 0.2, 1.3)
F.objects(True)
for s in (-1, 1):  # саркофаги-ящики и канопы вдоль стен
    x = s * (W - 2.2)
    for k, z in enumerate((-6.0, 0.0)):
        IS.box(x - 1.2, x + 1.2, 0.0, 1.6, z - 2.2, z + 2.2, (GOLD, TEAL)[k])
        IS.box(x - 1.3, x + 1.3, 1.6, 2.0, z - 2.3, z + 2.3, (BLUE, GOLD)[k])
        IS.box(x - 1.25, x + 1.25, 0.6, 0.9, z - 2.25, z + 2.25, RED)
    for k in range(4):
        z = -13.0 + 1.0 * k
        IS.prism_xz(K.ngon(x, z, 0.35, 8), 0.0, 1.1, SAND3)
        IS.prism_xz(K.ngon(x, z, 0.28, 8), 1.1, 1.5, (GOLD, TEAL, BLUE, RED)[k])
F.objects(False)
for x in (-8.0, 8.0):
    D.torch(IS, IG, x, 0.0, ZF + 1.6, h=3.6)
# постамент: погребальные сани — полозья и плита с золотыми кольцами
px, pz = PED
for e in (-1, 1):
    IR.loft([(px + e * 2.6 - 0.4, 0.0, pz - 4.4), (px + e * 2.6 + 0.4, 0.0, pz - 4.4), (px + e * 2.6 + 0.4, 0.0, pz + 4.0),
             (px + e * 2.6 - 0.4, 0.0, pz + 4.0)],
            [(px + e * 2.6 - 0.4, 0.5, pz - 4.8), (px + e * 2.6 + 0.4, 0.5, pz - 4.8), (px + e * 2.6 + 0.4, 0.5, pz + 4.0),
             (px + e * 2.6 - 0.4, 0.5, pz + 4.0)], WOOD)
IR.box(px - 3.4, px + 3.4, 0.5, TOP, pz - 4.0, pz + 3.6, SAND2)
for k in range(4):
    S.annulus(IS, (px - 3.42, 0.75, pz - 3.0 + 2.0 * k), (1, 0, 0), 0.1, 0.25, 0.06, GOLD, seg=8)
B.lift_leaves(IS, NIGHT2, GOLD)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, NIGHT, "B89A70", SAND, top=15.4)
SL.box(-FX - 0.4, FX + 0.4, 13.0, 15.4, -FZ - 3.2, -FZ, SAND)
for k in range(6):
    SL.prism_xz(K.ngon(-15.0 + 6.0 * k, -FZ - 2.0, 1.0, 6), 0.0, 13.0, SAND)

F.build(exhibit=(PED[0], TOP, PED[1], 3.2), lamps=[("Hall", (0, 14, 6), 1500, (1.0, 0.9, 0.75)),
                                                   ("Spot", (0, 13, -3), 3800, (1.0, 0.95, 0.85)),
                                                   ("Torch", (0, 5, -13), 700, (1.0, 0.6, 0.3))])
