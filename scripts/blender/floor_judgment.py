"""Этаж «Статуя Анубиса» музея-небоскрёба (одиннадцатая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — Зал взвешивания сердца. Снаружи — чёрный базальт с золотыми поясами и бирюзовыми вставками,
по фасаду — ряд высоких золотых жезлов-уас, в центре — огромные золотые весы с чашами (на одной — перо, на другой —
сосуд-сердце), под ними — тяжёлая дверь с золотыми полосами, по углам — чёрные обелиски с золотыми вершинами,
жаровни с огнём, звёзды по верхнему поясу. Внутри — тёмный зал суда: колонны с золотыми кольцами, вдоль стен —
ряд из 12 тронов-ниш, высокие весы рядом с экспонатом, ладьи на подставках, курильницы, синий потолок со
звёздами; экспонат — на ступенчатом чёрном постаменте с золотой каймой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_judgment.py -- <репо> <превью>
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

BASALT, BASALT2, GOLD, GOLD2, TURQ, NIGHT = "2E2E36", "1E1E26", "E8B840", "C8962A", "2AB8B0", "1A2A5A"
WHITE, FIRE, RED, SAND = "F2EEE0", "FF9030", "C83A2A", "C8B490"

F = B.Floor("AN", "AnubisStatue", quiet=(BASALT2, "4A4A52", "2A3A6A"), bevel_min=1.2)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def scales(p, x, y, z, s, axis="z"):
    """Весы: стойка, коромысло, две чаши на цепочках; на левой — перо, на правой — сосуд."""
    p.box(x - 0.25 * s, x + 0.25 * s, y, y + 6.0 * s, z - 0.25 * s, z + 0.25 * s, GOLD)
    p.box(x - 0.8 * s, x + 0.8 * s, y, y + 0.4 * s, z - 0.8 * s, z + 0.8 * s, GOLD2)
    beam(p, (x - 3.2 * s, y + 5.8 * s, z), (x + 3.2 * s, y + 5.4 * s, z), 0.3 * s, 0.3 * s, GOLD)
    p.prism_xy(K.ngon(x, y + 6.2 * s, 0.4 * s, 8), z - 0.2 * s, z + 0.2 * s, GOLD)
    for e, dy in ((-1, 5.8), (1, 5.4)):
        cx = x + e * 3.0 * s
        for f in (-1, 1):
            beam(p, (cx, y + dy * s, z), (cx + f * 0.9 * s, y + (dy - 2.4) * s, z), 0.06 * s, 0.06 * s, GOLD2)
        p.loft([(cx - 0.4 * s, y + (dy - 2.8) * s, z - 0.3 * s), (cx + 0.4 * s, y + (dy - 2.8) * s, z - 0.3 * s),
                (cx + 0.4 * s, y + (dy - 2.8) * s, z + 0.3 * s), (cx - 0.4 * s, y + (dy - 2.8) * s, z + 0.3 * s)],
               [(cx - 1.0 * s, y + (dy - 2.4) * s, z - 0.6 * s), (cx + 1.0 * s, y + (dy - 2.4) * s, z - 0.6 * s),
                (cx + 1.0 * s, y + (dy - 2.4) * s, z + 0.6 * s), (cx - 1.0 * s, y + (dy - 2.4) * s, z + 0.6 * s)], GOLD)
        if e < 0:
            taper(p, (cx - 0.1 * s, y + (dy - 2.4) * s, z), (cx + 0.3 * s, y + (dy - 0.6) * s, z), 0.45 * s, 0.15 * s, WHITE)
        else:
            p.prism_xz(K.ngon(cx, z, 0.35 * s, 8), y + (dy - 2.4) * s, y + (dy - 1.6) * s, RED)
            p.prism_xz(K.ngon(cx, z, 0.18 * s, 6), y + (dy - 1.6) * s, y + (dy - 1.3) * s, RED)


def was_sceptre(p, x, z, y0, y1, col=GOLD):
    """Жезл-уас: древко, раздвоенный низ, наклонная голова-навершие."""
    p.box(x - 0.12, x + 0.12, y0 + 0.6, y1, z - 0.12, z + 0.12, col)
    for e in (-1, 1):
        beam(p, (x, y0 + 0.6, z), (x + e * 0.35, y0, z), 0.12, 0.12, col)
    beam(p, (x - 0.1, y1, z), (x + 0.7, y1 + 0.6, z), 0.3, 0.24, col)
    beam(p, (x - 0.1, y1, z), (x - 0.4, y1 + 0.3, z), 0.2, 0.2, col)


def obelisk(p, x, z, y0, h, w):
    p.loft([(x - w, y0, z - w), (x + w, y0, z - w), (x + w, y0, z + w), (x - w, y0, z + w)],
           [(x - w * 0.6, y0 + h, z - w * 0.6), (x + w * 0.6, y0 + h, z - w * 0.6), (x + w * 0.6, y0 + h, z + w * 0.6),
            (x - w * 0.6, y0 + h, z + w * 0.6)], BASALT)
    p.cone([(x - w * 0.6, y0 + h, z - w * 0.6), (x + w * 0.6, y0 + h, z - w * 0.6), (x + w * 0.6, y0 + h, z + w * 0.6),
            (x - w * 0.6, y0 + h, z + w * 0.6)], (x, y0 + h + w * 1.2, z), GOLD)


def star(p, x, y, z0, z1, r, col):
    p.prism_xy([(x + r * (1 if k % 2 == 0 else 0.4) * math.cos(math.pi / 2 + k * math.pi / 5),
                 y + r * (1 if k % 2 == 0 else 0.4) * math.sin(math.pi / 2 + k * math.pi / 5)) for k in range(10)], z0, z1, col)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, BASALT, BASALT2, GOLD, SAND, NIGHT, roof="flat", roof_col=BASALT, top=16.0, band=(4.6, 5.0, GOLD),
         side=S.side_windows(F, GOLD, "1A1A22", kind="slit", y0=7.0, y1=12.0, w=1.0, xs=(-10.0, -4.0, 2.0, 8.0)))
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # бирюзовые вставки и звёзды по верхнему поясу
    slab(FS, axis, fixed, out, 1.0, -half, half, 13.6, 15.2, NIGHT)
    for k in range(int(2 * half // 2.0)):
        a = -half + 1.0 + 2.0 * k
        d0, d1 = sorted((fixed + out * 1.0, fixed + out * 1.08))
        pts = [(a + 0.45 * (1 if j % 2 == 0 else 0.4) * math.cos(math.pi / 2 + j * math.pi / 5),
                14.4 + 0.45 * (1 if j % 2 == 0 else 0.4) * math.sin(math.pi / 2 + j * math.pi / 5)) for j in range(10)]
        (FS.prism_zy if axis == "x" else FS.prism_xy)(pts, d0, d1, GOLD)
    for k in range(int(2 * half // 3.0)):
        a = -half + 1.5 + 3.0 * k
        slab(FS, axis, fixed, out, 1.0, a - 0.4, a + 0.4, 2.0, 4.4, TURQ)
# тяжёлая дверь с золотыми полосами под весами
FS.box(-2.6, 2.6, 1.0, 8.6, -FZ - 1.0, -FZ - 0.88, BASALT2)
for k in range(5):
    FS.box(-2.4, 2.4, 1.6 + 1.5 * k, 1.8 + 1.5 * k, -FZ - 1.05, -FZ - 1.0, GOLD)
FR.box(-3.2, 3.2, 8.6, 9.4, -FZ - 1.6, -FZ - 0.88, GOLD2)
# огромные весы на фасаде
F.objects(True)
scales(FS, 0.0, 9.4, -FZ - 1.8, 0.75)
F.objects(False)
# жезлы-уас рядом по фасаду
for x in (-15.6, -12.6, -9.6, 9.6, 12.6, 15.6):
    was_sceptre(FS, x, -FZ - 1.1, 1.0, 11.0)
# обелиски по углам и жаровни
F.objects(True)
for x in (-FX - 1.4, FX + 1.4):
    obelisk(FS, x, -FZ - 1.6, -0.1, 13.0, 0.9)
for x in (-5.6, 5.6):
    FS.prism_xz(K.ngon(x, -FZ - 2.2, 0.3, 8), -0.1, 2.0, GOLD2)
    FS.loft([(x + 0.4 * math.cos(a), 2.0, -FZ - 2.2 + 0.4 * math.sin(a)) for a in [2 * math.pi * k / 8 for k in range(8)]],
            [(x + 0.9 * math.cos(a), 2.8, -FZ - 2.2 + 0.9 * math.sin(a)) for a in [2 * math.pi * k / 8 for k in range(8)]], GOLD)
F.objects(False)
for x in (-5.6, 5.6):
    for k in range(3):
        a = 2 * math.pi * k / 3
        FG.cone([(x + 0.25 * math.cos(a) + 0.2 * math.cos(b), 2.8, -FZ - 2.2 + 0.25 * math.sin(a) + 0.2 * math.sin(b))
                 for b in [2 * math.pi * j / 5 for j in range(5)]], (x + 0.25 * math.cos(a), 4.0 - 0.3 * k, -FZ - 2.2 + 0.25 * math.sin(a)), FIRE)

# ══ ИНТЕРЬЕР: зал суда ════════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.8
S.interior(F, BASALT, "3A3A44", NIGHT, GOLD, wain=(1.2, BASALT2), beams=None)
for k in range(30):  # звёзды на синем потолке
    x, z = -W + 1.5 + (2 * W - 3.0) * rng(k, 1), ZF + 1.5 + (ZB - ZF - 3.0) * rng(k, 2)
    IS.prism_xz([(x + 0.4 * (1 if j % 2 == 0 else 0.4) * math.cos(j * math.pi / 5), z + 0.4 * (1 if j % 2 == 0 else 0.4) * math.sin(j * math.pi / 5))
                 for j in range(10)], C - 0.06, C - 0.02, GOLD)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS[:3]):  # золотые пояса стен
    for y in (6.0, 12.6):
        slab(IS, axis, fixed, out, 0.94, -half, half, y, y + 0.3, GOLD)
F.objects(True)
for s in (-1, 1):  # троны-ниши судей вдоль боковых стен
    for k in range(6):
        z = -13.0 + 3.0 * k
        x0 = s * (W - 0.88)
        IS.box(*sorted((x0, x0 - s * 1.6)), 0.0, 1.4, z - 0.9, z + 0.9, BASALT2)
        IS.box(*sorted((x0, x0 - s * 0.4)), 1.4, 4.4, z - 0.9, z + 0.9, GOLD if k % 2 else TURQ)
        IS.box(*sorted((x0 - s * 0.4, x0 - s * 1.6)), 1.4, 1.7, z - 0.9, z + 0.9, GOLD2)
        IS.prism_zy(K.ngon(z, 5.0, 0.4, 6), *sorted((x0, x0 - s * 0.4)), GOLD)
for x in (-9.0, 9.0):  # колонны с золотыми кольцами
    for z in (-10.0, 3.0):
        IR.prism_xz(K.ngon(x, z, 0.9, 10), 0.0, C, BASALT2)
        for y in (2.0, 8.0, 14.0):
            IS.prism_xz(K.ngon(x, z, 1.0, 10), y - 0.25, y + 0.25, GOLD)
# высокие весы у экспоната, ладьи на подставках у дальней стены, курильницы
scales(IS, 6.0, 0.0, -6.0, 0.9)
for x in (-8.0, 8.0):
    IS.box(x - 1.2, x + 1.2, 0.0, 2.0, ZF + 2.0, ZF + 3.0, BASALT2)
    IS.loft([(x - 2.6, 2.6, ZF + 2.2), (x + 2.6, 2.6, ZF + 2.2), (x + 2.6, 2.6, ZF + 2.8), (x - 2.6, 2.6, ZF + 2.8)],
            [(x - 1.8, 2.0, ZF + 2.1), (x + 1.8, 2.0, ZF + 2.1), (x + 1.8, 2.0, ZF + 2.9), (x - 1.8, 2.0, ZF + 2.9)], GOLD)
    for e in (-1, 1):
        beam(IS, (x + e * 2.6, 2.6, ZF + 2.5), (x + e * 3.2, 3.8, ZF + 2.5), 0.3, 0.3, GOLD)
    IS.box(x - 0.6, x + 0.6, 2.6, 3.8, ZF + 2.2, ZF + 2.8, TURQ)
for x in (-4.0, 4.0):
    IS.prism_xz(K.ngon(x, 5.0, 0.3, 8), 0.0, 2.4, GOLD2)
    IS.prism_xz(K.ngon(x, 5.0, 0.7, 8), 2.4, 2.8, GOLD)
    IG.prism_xz(K.ngon(x, 5.0, 0.4, 6), 2.8, 3.3, FIRE)
F.objects(False)
# светлая песчаная стела за экспонатом: чёрный Анубис читается силуэтом, а не тонет в чёрной стене
IR.box(-4.4, 4.4, 2.6, 15.4, ZF + 0.88, ZF + 1.0, "D8C49A")
IS.frame_xy(K.rect(-4.8, 4.8, 2.2, 15.8), K.rect(-4.4, 4.4, 2.6, 15.4), ZF + 0.88, ZF + 1.12, GOLD)
S_DISC = (0.0, 13.2)
IS.prism_xy(K.ngon(S_DISC[0], S_DISC[1], 1.5, 16), ZF + 1.0, ZF + 1.1, GOLD)
IS.prism_xy(K.ngon(S_DISC[0], S_DISC[1], 1.0, 16), ZF + 1.1, ZF + 1.16, RED)
for x in (-6.0, 6.0):  # большие жезлы у дальней стены
    was_sceptre(IS, x, ZF + 1.2, 0.0, 10.0)
# постамент: ступенчатый чёрный с золотой каймой
px, pz = PED
for k, (r, y0, y1) in enumerate(((4.4, 0.0, 0.6), (3.9, 0.6, 1.2), (3.4, 1.2, TOP))):
    IR.box(px - r, px + r, y0, y1 - 0.1, pz - r, pz + r, BASALT2 if k % 2 else BASALT)
    IS.box(px - r - 0.05, px + r + 0.05, y1 - 0.1, y1, pz - r - 0.05, pz + r + 0.05, GOLD)
B.lift_leaves(IS, BASALT2, GOLD)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, BASALT, SAND, BASALT, top=16.0)
for x in (-FX - 1.4, FX + 1.4):
    SL.cone([(x - 0.9, -0.1, -FZ - 2.5), (x + 0.9, -0.1, -FZ - 2.5), (x + 0.9, -0.1, -FZ - 0.7), (x - 0.9, -0.1, -FZ - 0.7)],
            (x, 14.0, -FZ - 1.6), BASALT)

F.build(exhibit=(PED[0], TOP, PED[1], 3.0), lamps=[("Hall", (0, 14, 6), 1500, (1.0, 0.9, 0.75)),
                                                   ("Spot", (0, 13, -3), 4000, (1.0, 0.95, 0.85)),
                                                   ("Fire", (0, 4, 6), 800, (1.0, 0.6, 0.3))])
