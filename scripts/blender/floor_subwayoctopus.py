"""Этаж «Подземный осьминог» музея-небоскрёба (пятая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — затонувшая станция метро, ставшая океанариумом. Снаружи — клёпаная сталь цвета морской волны с
медными поясами, огромное панорамное стекло-аквариум с водой, рыбами, кораллами и водорослями, по фасаду из люка
на тротуаре выползают и обвивают здание огромные фиолетовые щупальца с присосками, вокруг — якорь на цепи, буи,
трубы; бока — ряды иллюминаторов с пузырями; сзади — водолазный колокол. Внутри — подводный зал: стены-аквариумы с
рыбами, коралловый риф (ветвистые кораллы, веера, губки), водоросли до потолка, затонувший вагон метро в песке,
сундук с монетами, пузыри; экспонат — на огромном открытом люке, обросшем кораллами и ракушками.
Запуск: blender --background --factory-startup --python scripts/blender/floor_aquarium.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, ring_y, rng, slab, taper, tube  # noqa: E402

TEAL, TEAL2, TEAL3, COPPER, COPPER2, RUST, DARK = "2E7A84", "1E5A64", "4A9AA0", "D08A4A", "A86A34", "8A4A30", "1A2630"
WATER, WATER2, DEEP, SAND, SAND2 = "3AA8D8", "6AD0F0", "1E4A7A", "E8D4A0", "D0BA84"
OCTO, OCTO2, SUCK, KELP, KELP2 = "9A3AC8", "7A2AA8", "F0B8E8", "3A9A4A", "2A7A3A"
CORAL = ("FF6A6A", "FF9A3A", "FF5AB0", "B06AF0", "FFD04A")
FISH = ("FFB02A", "FF5A3A", "3AE0FF", "FFE84A", "FF7AD0")
GOLD, GOLD2, STEEL = "FFD04A", "E0A82A", "9AA8B4"

F = B.Floor("OC", "SubwayOctopus", quiet=(SAND2, DEEP, TEAL2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def fish(p, axis, x, y, z, s, col, flip=1):
    """Рыба в профиль: ромбическое тело, хвост, плавник (плоская фигура в плоскости стены)."""
    body = [(-0.6 * s, 0.0), (0.0, 0.4 * s), (0.6 * s, 0.05 * s), (0.6 * s, -0.05 * s), (0.0, -0.4 * s)]
    tail = [(-0.5 * s, 0.0), (-1.0 * s, 0.4 * s), (-0.9 * s, 0.0), (-1.0 * s, -0.4 * s)]
    for pts, d in ((body, 0.0), (tail, 0.0)):
        pp = [(u * flip, v) for u, v in pts]
        if axis == "z":
            p.prism_xy([(x + u, y + v) for u, v in pp], z - 0.08 * s, z + 0.08 * s, col)
        else:
            p.prism_zy([(z + u, y + v) for u, v in pp], x - 0.08 * s, x + 0.08 * s, col)


def coral(p, x, z, y, h, col, seed):
    """Ветвистый коралл: ствол и три-четыре загнутые ветви."""
    taper(p, (x, y, z), (x, y + h * 0.5, z), 0.5 * h * 0.3, 0.35 * h * 0.3, col)
    for k in range(3 + seed % 2):
        t = 2 * math.pi * (k + rng(seed, k) * 0.4) / (3 + seed % 2)
        mid = (x + math.cos(t) * h * 0.25, y + h * (0.6 + 0.1 * k % 2), z + math.sin(t) * h * 0.25)
        tip = (x + math.cos(t) * h * 0.35, y + h * (0.95 + 0.1 * rng(k, seed)), z + math.sin(t) * h * 0.35)
        taper(p, (x, y + h * 0.45, z), mid, 0.3 * h * 0.3, 0.24 * h * 0.3, col)
        taper(p, mid, tip, 0.24 * h * 0.3, 0.1 * h * 0.3, col)


def fan(p, x, z, y, h, col, yaw=0.0):
    """Коралл-веер: плоская ромбическая пластина на ножке."""
    c, s = math.cos(yaw), math.sin(yaw)
    pts = [(-0.7 * h, 0.5 * h), (-0.4 * h, 0.95 * h), (0.0, h), (0.4 * h, 0.95 * h), (0.7 * h, 0.5 * h), (0.1, 0.1 * h), (-0.1, 0.1 * h)]
    a = [(x + u * c, y + v, z + u * s) for u, v in pts]
    b = [(x + u * c - s * 0.12, y + v, z + u * s + c * 0.12) for u, v in pts]
    p.loft(a, b, col)
    p.box(x - 0.1, x + 0.1, y, y + 0.15 * h, z - 0.1, z + 0.1, col)


def kelp(p, x, z, y0, h, seed):
    """Водоросль: зигзаг из сужающихся лент."""
    pts = [(x + 0.6 * math.sin(k * 1.3 + seed), y0 + h * k / 4, z + 0.4 * math.cos(k * 1.1 + seed)) for k in range(5)]
    for k, (a, b) in enumerate(zip(pts, pts[1:])):
        taper(p, a, b, 0.7 - 0.12 * k, 0.6 - 0.12 * k, (KELP, KELP2)[k % 2])


def tentacle(p, pts, w0, w1, normal):
    """Щупальце: сужающаяся труба по точкам с присосками на внутренней стороне."""
    n = len(pts)
    widths = [w0 + (w1 - w0) * k / (n - 1) for k in range(n)]
    tube(p, pts, widths, w0 * 0.9, normal, OCTO)
    for k in range(1, n - 1, 1):
        q = pts[k]
        p.prism_xz(K.ngon(q[0], q[2], widths[k] * 0.28, 6), q[1] - widths[k] * 0.55, q[1] - widths[k] * 0.4, SUCK)


def chest(p, x, z, y=0.0, s=1.0):
    """Сундук с монетами: корпус, крышка, оковка, горка монет."""
    p.box(x - 1.2 * s, x + 1.2 * s, y, y + 1.1 * s, z - 0.8 * s, z + 0.8 * s, RUST)
    p.box(x - 1.25 * s, x + 1.25 * s, y + 1.1 * s, y + 1.3 * s, z - 0.85 * s, z + 0.85 * s, COPPER2)
    for e in (-1, 1):
        p.box(x + e * 0.8 * s - 0.1, x + e * 0.8 * s + 0.1, y, y + 1.3 * s, z - 0.86 * s, z + 0.86 * s, GOLD2)
    p.prism_xz(K.ngon(x, z, 0.9 * s, 10), y + 1.3 * s, y + 1.6 * s, GOLD)
    p.prism_xz(K.ngon(x, z, 0.5 * s, 8), y + 1.6 * s, y + 1.85 * s, GOLD)


# ══ ФАСАД: океанариум, обвитый щупальцами ═════════════════════════════════════════════════════════════════════
B.shell_planes(F, TEAL, TEAL, DEEP)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, SAND2)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.0, COPPER2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.0, 15.4, TEAL)
    for k in range(int(2 * half // 3.0)):  # клёпаные листы
        a = -half + 3.0 * k
        for r in range(4):
            y = 1.2 + 3.5 * r
            if fi == 0 and a + 2.9 > -14.2 and a + 0.1 < 14.2 and y + 3.4 > 2.0 and y < 13.8:
                continue  # за аквариумом листов нет — там вода
            slab(FR, axis, fixed, out, 0.96, a + 0.1, a + 2.9, y + 0.1, y + 3.4, (TEAL, TEAL3)[(k + r) % 2])
    slab(FR, axis, fixed, out, 1.88, -half - 0.6, half + 0.6, 15.4, 16.4, COPPER)
    slab(FR, axis, fixed, out, 0.88, -half, half, 16.4, 18.9, TEAL2)
    if axis == "x":  # бока: ряды иллюминаторов (по четыре) с пузырями
        for z in (-12.0, -4.0, 4.0, 12.0):
            for y in (5.0, 10.5):
                FS.prism_zy(K.ngon(z, y, 1.6, 12), *sorted((fixed + out * 0.88, fixed + out * 1.3)), COPPER)
                FG.prism_zy(K.ngon(z, y, 1.15, 12), *sorted((fixed + out * 1.3, fixed + out * 1.34)), WATER2)
        for k in range(8):
            z = -14.0 + 28.0 * rng(fi, k)
            y = 2.0 + 13.0 * rng(k, fi)
            FG.prism_zy(K.ngon(z, y, 0.25 + 0.2 * rng(k, 3), 6), *sorted((fixed + out * 1.0, fixed + out * 1.4)), "E0F8FF")
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# перед: панорамный аквариум в медной раме с рыбами, кораллами, водорослями
FS.frame_xy(K.rect(-14.0, 14.0, 2.0, 13.8), K.rect(-13.2, 13.2, 2.6, 13.2), -FZ - 1.4, -FZ - 0.88, COPPER2)
FG.box(-13.2, 13.2, 2.6, 13.2, -FZ - 0.96, -FZ - 0.92, WATER)  # вода — перед стеной, за рыбами и рифом
FS.box(-13.2, 13.2, 2.6, 3.6, -FZ - 1.3, -FZ - 0.96, SAND)
for k in range(5):
    FS.box(-13.2 + 5.3 * k - 0.12, -13.2 + 5.3 * k + 0.12, 2.6, 13.2, -FZ - 1.7, -FZ - 1.4, COPPER)
for k, (x, y, s, fl) in enumerate(((-9.0, 9.0, 1.6, 1), (-3.0, 11.0, 1.2, -1), (4.0, 7.6, 1.8, 1), (9.6, 10.6, 1.3, -1), (-6.0, 5.6, 1.1, 1),
                                   (11.0, 5.4, 1.0, -1))):
    fish(FS, "z", x, y, -FZ - 1.12, s, FISH[k % 5], fl)
for k, x in enumerate((-11.0, -6.6, 6.0, 11.4)):
    coral(FS, x, -FZ - 1.15, 3.6, 2.6, CORAL[k], k)
for x in (-1.0, 2.0):
    kelp(FS, x, -FZ - 1.15, 3.6, 7.0, x)
# вход под медной аркой
FS.box(-2.6, 2.6, 1.0, 2.0, -FZ - 1.6, -FZ - 1.4, COPPER)
# щупальца из люка у входа, обвивающие фасад
FS.prism_xz(K.ngon(7.0, -FZ - 5.0, 2.2, 12), -0.1, 0.3, DARK)
ring_y(FS, 7.0, -FZ - 5.0, 2.2, 2.6, -0.1, 0.4, STEEL, n=12)
for pts, w0, nrm in (([(6.0, 0.2, -FZ - 5.4), (4.0, 3.0, -FZ - 4.0), (1.0, 6.0, -FZ - 2.6), (-2.0, 9.0, -FZ - 2.0), (-6.0, 11.0, -FZ - 2.2),
                       (-9.0, 13.6, -FZ - 1.9), (-12.0, 15.0, -FZ - 2.4)], 1.5, (0, 0, 1)),
                     ([(7.6, 0.2, -FZ - 4.2), (9.6, 3.6, -FZ - 3.0), (12.0, 6.0, -FZ - 2.4), (14.6, 8.0, -FZ - 2.0), (16.4, 11.0, -FZ - 1.8),
                       (17.0, 14.6, -FZ - 2.2)], 1.4, (0, 0, 1)),
                     ([(7.0, 0.2, -FZ - 6.2), (7.6, 2.6, -FZ - 7.6), (8.8, 4.0, -FZ - 8.0), (9.8, 3.4, -FZ - 7.2)], 1.1, (1, 0, 0))):
    tentacle(FS, pts, w0 * 1.5, 0.5, nrm)
# якорь на цепи, буи
AX, AZ = -15.0, -FZ - 4.0
FS.box(AX - 0.25, AX + 0.25, 0.0, 6.0, AZ - 0.25, AZ + 0.25, DARK)
FS.box(AX - 1.6, AX + 1.6, 5.0, 5.4, AZ - 0.25, AZ + 0.25, DARK)
ring_y(FS, AX, AZ, 0.4, 0.7, 6.0, 6.3, DARK, n=8)
FS.prism_xy([(AX - 2.6, 1.6), (AX - 2.0, 0.6), (AX, 0.0), (AX + 2.0, 0.6), (AX + 2.6, 1.6), (AX + 2.0, 1.2), (AX, 0.6), (AX - 2.0, 1.2)],
            AZ - 0.25, AZ + 0.25, DARK)
for k in range(5):
    y = 6.3 + 1.6 * k
    if k % 2:  # звенья цепи чередуют плоскость
        FS.prism_xy(K.octa(AX, y + 0.8, 0.4, 0.8, 0.2), AZ - 0.12, AZ + 0.12, STEEL)
    else:
        FS.prism_zy(K.octa(AZ, y + 0.8, 0.4, 0.8, 0.2), AX - 0.12, AX + 0.12, STEEL)
for x, col in ((15.0, "FF4A3A"), (16.6, "FFFFFF")):
    FS.prism_xz(K.ngon(x, -FZ - 6.0 + (x - 15.0), 0.9, 10), 0.0, 1.6, col)
    FS.prism_xz(K.ngon(x, -FZ - 6.0 + (x - 15.0), 0.4, 8), 1.6, 2.2, STEEL)
# тыл: водолазный колокол
FS.prism_xz(K.ngon(-4.0, FZ + 3.0, 2.6, 12), 0.0, 3.0, COPPER2)
FS.cone([(-4.0 + 2.6 * math.cos(t), 3.0, FZ + 3.0 + 2.6 * math.sin(t)) for t in [2 * math.pi * k / 12 for k in range(12)]],
        (-4.0, 5.6, FZ + 3.0), COPPER)
ring_y(FS, -4.0, FZ + 3.0, 2.6, 2.8, 1.4, 1.8, COPPER, n=12)

# ══ ИНТЕРЬЕР: подводный зал ═══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), SAND)
for k in range(14):  # песчаные барханчики
    x, z = -14.0 + 28.0 * rng(k, 1), -14.0 + 26.0 * rng(k, 2)
    if abs(x) < 5.0 and -8.0 < z < 2.0 or (abs(x) < 4.5 and z > 7.0):
        continue
    IQ.prism_xz(K.octa(x, z, 1.4, 0.9, 0.4), 0.02, 0.2, SAND2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.6, TEAL2)
        slab(IR, axis, fixed, out, 0.88, a0, a1, 1.6, C if not gap else DOOR[1] + 0.1, DEEP)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, DEEP)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, COPPER)
    else:  # стены-аквариумы: вода, рыбы, медные переплёты
        gp = IG.prism_xy if axis == "z" else IG.prism_zy
        spans_w = ((-14.0, -1.0), (1.0, 14.0)) if axis == "x" else ((-14.0, -4.0), (4.0, 14.0))
        for a0, a1 in spans_w:
            gp(K.rect(a0, a1, 2.2, 13.6), *sorted((fixed + out * 0.9, fixed + out * 0.94)), WATER)
            fr = IS.frame_xy if axis == "z" else IS.frame_zy
            fr(K.rect(a0 - 0.4, a1 + 0.4, 1.8, 14.0), K.rect(a0, a1, 2.2, 13.6), *sorted((fixed + out * 0.88, fixed + out * 1.3)), COPPER2)
            for k in range(3):
                a = a0 + (a1 - a0) * (k + 0.5) / 3
                fish(IS, axis, fixed + out * 1.05 if axis == "x" else a, 4.6 + 3.2 * ((k + idx) % 3), a if axis == "x" else fixed + out * 1.05,
                     1.3, FISH[(k + idx) % 5], (-1) ** (k + idx))
    slab(IR, axis, fixed, out, 1.6, -half, half, 14.6, 15.6, COPPER2)
# коралловый риф, водоросли до потолка, губки
for k, (x, z) in enumerate(((-13.0, -12.0), (-9.0, -13.0), (12.0, -12.6), (8.6, -13.4), (-13.4, 3.0), (13.4, 4.0))):
    coral(IS, x, z, 0.0, 3.2 + 0.4 * (k % 3), CORAL[k % 5], k)
for k, (x, z, yaw) in enumerate(((-6.0, -13.6, 0.0), (5.4, -14.0, 0.3), (-14.0, -6.0, 1.5), (14.0, -5.0, 1.6))):
    fan(IS, x, z, 0.0, 3.6, CORAL[(k + 2) % 5], yaw)
for k, (x, z) in enumerate(((-11.0, -9.0), (11.4, -8.4), (-12.6, 9.0), (12.6, 9.6), (-3.0, -14.0), (3.4, -14.2))):
    kelp(IS, x, z, 0.0, 13.0 + 2.0 * (k % 2), k)
for k, (x, z) in enumerate(((-9.6, -5.0), (9.0, 6.0), (-7.0, 10.0))):
    IS.prism_xz(K.ngon(x, z, 1.0, 8), 0.0, 1.4, CORAL[(k + 3) % 5])
    IS.prism_xz(K.ngon(x, z, 0.5, 6), 1.4, 1.5, DARK)
# затонувший вагон метро в песке, сундук, пузыри
IS.loft([(-14.0, -0.6, ZF + 1.0), (-2.0, -0.6, ZF + 1.0), (-2.0, -0.6, ZF + 4.0), (-14.0, -0.6, ZF + 4.0)],
        [(-14.0, 5.0, ZF + 1.6), (-2.0, 4.0, ZF + 1.6), (-2.0, 4.0, ZF + 4.6), (-14.0, 5.0, ZF + 4.6)], "3A6AB0")
for k in range(4):
    x = -12.6 + 2.8 * k
    yb = 4.8 - 0.25 * k - (x + 14.0) * 0.07
    IG.box(x - 0.9, x + 0.9, 2.0, 3.6 + (yb - 4.8) * 0.5, ZF + 4.66, ZF + 4.7, WATER2)
IS.box(-14.0, -2.0, 1.2, 1.6, ZF + 4.6, ZF + 4.8, "F4F4F4")
chest(IS, 9.0, -9.6, 0.0, 1.2)
for k in range(12):  # мелкие пузырьки
    x, y, z = -13.0 + 26.0 * rng(k, 7), 3.0 + 12.0 * rng(k, 8), -13.0 + 22.0 * rng(k, 9)
    if abs(x) < 6.0 and z > 5.0 or abs(x) < 5.0 and -8.0 < z < 3.0:
        continue
    rr = 0.12 + 0.12 * rng(k, 10)
    IG.prism_xz(K.ngon(x, z, rr, 6), y, y + rr * 2.0, "C8F2FF")
# постамент — огромный открытый люк, обросший кораллами и ракушками
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.2, 16), 0.0, TOP - 0.3, STEEL)
ring_y(IS, px, pz, 3.4, 4.3, TOP - 0.3, TOP, "6A7A88", n=16)
IS.prism_xz(K.ngon(px, pz, 3.4, 16), TOP - 0.3, TOP - 0.2, DARK)
for k in range(12):
    t = 2 * math.pi * k / 12
    IS.box(px + 3.85 * math.cos(t) - 0.2, px + 3.85 * math.cos(t) + 0.2, TOP, TOP + 0.08, pz + 3.85 * math.sin(t) - 0.2,
           pz + 3.85 * math.sin(t) + 0.2, "5A6878")
IS.loft([(px - 3.0, 0.0, pz - 4.6), (px + 3.0, 0.0, pz - 4.6), (px + 3.0, 0.0, pz - 4.3), (px - 3.0, 0.0, pz - 4.3)],
        [(px - 3.0, 4.8, pz - 6.2), (px + 3.0, 4.8, pz - 6.2), (px + 3.0, 4.8, pz - 5.9), (px - 3.0, 4.8, pz - 5.9)], "6A7A88")
for k, (dx, dz) in enumerate(((-4.6, 1.4), (4.4, 1.0), (-4.0, -2.6), (4.8, -2.0))):
    coral(IS, px + dx, pz + dz, 0.0, 1.8, CORAL[k], k + 7)
for k in range(6):
    t = 2 * math.pi * (k + 0.3) / 6
    IS.prism_xz(K.octa(px + 4.4 * math.cos(t), pz + 4.4 * math.sin(t), 0.35, 0.3, 0.1), 0.0, 0.25, ("F8E0D0", "FFC8B0")[k % 2])
B.lift_leaves(IS, TEAL2, COPPER)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, TEAL)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, SAND2)
SL.box(-FX - 1.9, FX + 1.9, 15.4, 16.4, -FZ - 1.9, FZ + 1.9, COPPER)
SL.box(-14.0, 14.0, 2.0, 13.8, -FZ - 1.3, -FZ + 0.1, COPPER2)
SL.box(-13.2, 13.2, 2.6, 13.2, -FZ - 1.4, -FZ - 1.3, WATER)
SL.loft([(5.0, 0.0, -FZ - 3.0), (8.0, 0.0, -FZ - 3.0), (8.0, 0.0, -FZ - 2.0), (5.0, 0.0, -FZ - 2.0)],
        [(-12.0, 15.0, -FZ - 2.6), (-11.0, 15.0, -FZ - 2.6), (-11.0, 15.0, -FZ - 2.0), (-12.0, 15.0, -FZ - 2.0)], OCTO)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 2400, (0.75, 0.9, 1.0)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.97, 0.9)),
                                                   ("Sea", (0, 8, -12), 1000, (0.4, 0.8, 1.0))])
