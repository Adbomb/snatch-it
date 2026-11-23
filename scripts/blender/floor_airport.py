"""Этаж «Чемодан на ножках» музея-небоскрёба (шестая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — аэропорт. Снаружи — терминал со стеклянной стеной в частой решётке переплётов, над ней — крыша-волна
на V-образных стойках, вынесенная далеко вперёд, на углу — диспетчерская вышка со стеклянной кабиной и антенной,
сбоку у телетрапа стоит самолёт (фюзеляж с иллюминаторами, крыло, хвост с цветной полосой), перед входом — табло
вылетов со светящимися строками, знак-самолётик, тележки для багажа, тягач с вагончиками чемоданов, конусы,
полосатый ветроуказатель и синие огни перрона. Внутри — зал ожидания: светлый пол в сетку, по бокам огромные окна
с небом и силуэтом самолёта, у дальней стены — большое табло и стойки регистрации с лентами и весами, ряды
кресел, пальмы в кадках, рамка досмотра, жёлтые указатели-стрелки под потолком, светлые потолочные волны;
экспонат — на багажной карусели: стальное основание, тёмная лента из пластин по кругу, центральный остров.
Запуск: blender --background --factory-startup --python scripts/blender/floor_airport.py -- <репо> <превью>
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

WHITE, WHITE2, STEEL, STEEL2, NAVY, GREY = "F2F4F6", "DCE2E8", "A8B0B8", "7A828C", "1E3A6A", "5A626C"
GLASS, SKY, ORANGE, YELLOW, RED, ASPH = "8CB8DC", "78B0E0", "F08A30", "F2C230", "D83A2E", "3A3E44"
BLUE, DARK, SEAT, TEAL = "2E6ADB", "22262C", "3A7AD8", "2AA8A0"
BAGS = ("E84A4A", "3A8AE8", "F2C230", "6AC86A", "B06AE0", "F08A30")

F = B.Floor("AP", "WalkingSuitcase", quiet=(ASPH, "C8CED4", GREY), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def suitcase(p, x, y, z, w, h, d, col, along_x=True):
    """Чемодан: корпус, ручка, два ремня."""
    hw, hd = (w / 2, d / 2) if along_x else (d / 2, w / 2)
    p.box(x - hw, x + hw, y, y + h, z - hd, z + hd, col)
    p.box(x - 0.2, x + 0.2, y + h, y + h + 0.25, z - 0.05, z + 0.05, DARK)
    for e in (-0.3, 0.3):
        if along_x:
            p.box(x + e * w - 0.06, x + e * w + 0.06, y - 0.01, y + h + 0.01, z - hd - 0.02, z + hd + 0.02, DARK)
        else:
            p.box(x - hw - 0.02, x + hw + 0.02, y - 0.01, y + h + 0.01, z + e * w - 0.06, z + e * w + 0.06, DARK)


def board(p, g, pr, gpr, a, y, w, h, d0, d1, gd0, gd1, rows=5):
    """Табло: тёмная доска, светящиеся строки разной длины, значок-самолёт слева."""
    pr(K.rect(a - w / 2, a + w / 2, y - h / 2, y + h / 2), d0, d1, DARK)
    for r in range(rows):
        yy = y + h / 2 - (r + 0.8) * h / (rows + 0.6)
        gpr(K.rect(a - w / 2 + 1.4, a - w / 2 + 1.4 + (w - 2.2) * (0.45 + 0.5 * rng(r, a)), yy - 0.16, yy + 0.16), gd0, gd1,
            ("FFD03A", "F2F4F6", "6AE86A", "FFD03A", "F2F4F6", "FF8A5A")[r % 6])
        gpr(K.rect(a - w / 2 + 0.4, a - w / 2 + 1.0, yy - 0.2, yy + 0.2), gd0, gd1, "8AC8FF")


def plane_icon(pr, a, y, s, d0, d1, col=WHITE):
    """Значок-самолётик (вид сверху) на табличке."""
    pr([(a, y + s), (a + s * 0.12, y + s * 0.6), (a + s * 0.12, y + s * 0.2), (a + s * 0.8, y - s * 0.1), (a + s * 0.8, y - s * 0.3),
        (a + s * 0.12, y - s * 0.1), (a + s * 0.12, y - s * 0.6), (a + s * 0.35, y - s * 0.85), (a + s * 0.35, y - s),
        (a, y - s * 0.85), (a - s * 0.35, y - s), (a - s * 0.35, y - s * 0.85), (a - s * 0.12, y - s * 0.6), (a - s * 0.12, y - s * 0.1),
        (a - s * 0.8, y - s * 0.3), (a - s * 0.8, y - s * 0.1), (a - s * 0.12, y + s * 0.2), (a - s * 0.12, y + s * 0.6)], d0, d1, col)


# ══ ФАСАД: терминал ═══════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, WHITE, WHITE, WHITE2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, ASPH)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.2, GREY)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.2, 15.2, WHITE)
    slab(FR, axis, fixed, out, 1.6, -half - 0.3, half + 0.3, 15.2, 16.0, NAVY)
    slab(FR, axis, fixed, out, 0.88, -half, half, 16.0, 18.9, WHITE2)
    slab(FR, axis, fixed, out, 1.3, -half - 0.2, half + 0.2, 18.4, 18.9, STEEL)
    if axis == "x":  # бока: стеклянная лента и панели
        slab(FG, axis, fixed, out, 0.92, -14.0, 14.0, 3.0, 13.4, GLASS)
        for k in range(12):
            z = -14.0 + 28.0 * k / 11
            slab(FS, axis, fixed, out, 1.1, z - 0.12, z + 0.12, 2.8, 13.6, STEEL2)
        for y in (2.8, 8.2, 13.4):
            slab(FS, axis, fixed, out, 1.15, -14.2, 14.2, y - 0.12, y + 0.12, STEEL2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# разметка перрона
for x in (-16.0, 16.0):
    FQ.box(x - 0.15, x + 0.15, -0.1, -0.06, -FZ - 2.88, -FZ - 0.5, YELLOW)
for k in range(8):
    x = -14.0 + 4.0 * k
    FQ.box(x - 1.0, x + 1.0, -0.1, -0.06, -FZ - 2.4, -FZ - 2.2, WHITE)
# стеклянная стена в частой решётке
FG.box(-13.0, 13.0, 1.2, 14.4, -FZ - 0.94, -FZ - 0.9, GLASS)
for k in range(12):
    x = -13.0 + 26.0 * k / 11
    FS.box(x - 0.12, x + 0.12, 1.2, 14.6, -FZ - 1.25, -FZ - 0.88, STEEL2)
for y in (1.3, 4.2, 7.4, 10.6, 14.4):
    FS.box(-13.2, 13.2, y - 0.12, y + 0.12, -FZ - 1.25, -FZ - 0.88, STEEL2)
FS.box(-2.4, 2.4, 1.2, 6.8, -FZ - 1.05, -FZ - 0.95, "C8E0F0")  # раздвижные двери
FS.box(-0.04, 0.04, 1.2, 6.8, -FZ - 1.12, -FZ - 1.05, STEEL2)
# крыша-волна на V-стойках
for k in range(12):
    x0, x1 = -17.6 + 3.2 * k, -17.6 + 3.2 * (k + 1)
    y0 = 16.0 + 0.8 * math.sin(k * 0.9)
    y1 = 16.0 + 0.8 * math.sin((k + 1) * 0.9)
    FS.loft([(x0, y0, -FZ - 0.9), (x0, y0, -FZ - 6.2), (x0, y0 + 0.45, -FZ - 6.2), (x0, y0 + 0.45, -FZ - 0.9)],
            [(x1, y1, -FZ - 0.9), (x1, y1, -FZ - 6.2), (x1, y1 + 0.45, -FZ - 6.2), (x1, y1 + 0.45, -FZ - 0.9)], WHITE)
    FS.loft([(x0, y0 - 0.05, -FZ - 6.25), (x0, y0 + 0.5, -FZ - 6.25), (x0, y0 + 0.5, -FZ - 6.0), (x0, y0 - 0.05, -FZ - 6.0)],
            [(x1, y1 - 0.05, -FZ - 6.25), (x1, y1 + 0.5, -FZ - 6.25), (x1, y1 + 0.5, -FZ - 6.0), (x1, y1 - 0.05, -FZ - 6.0)], NAVY)
for x in (-12.0, 0.0, 12.0):
    yy = 16.0 + 0.8 * math.sin((x + 17.6) / 3.2 * 0.9)
    FS.box(x - 0.3, x + 0.3, 0.0, 6.0, -FZ - 5.0, -FZ - 4.4, STEEL)
    for e in (-1, 1):
        beam(FS, (x, 6.0, -FZ - 4.7), (x + e * 2.6, yy - 0.05, -FZ - 4.7), 0.35, 0.35, STEEL)
# знак-самолётик и табло вылетов под крышей
FS.box(-1.6, 1.6, 9.4, 12.6, -FZ - 1.4, -FZ - 1.2, BLUE)
plane_icon(FS.prism_xy, 0.0, 11.0, 1.2, -FZ - 1.48, -FZ - 1.4)
board(FS, FG, FS.prism_xy, FG.prism_xy, -7.2, 11.4, 7.0, 3.4, -FZ - 1.6, -FZ - 1.3, -FZ - 1.66, -FZ - 1.6, rows=5)
# диспетчерская вышка на левом углу
vx, vz = FX + 1.6, -FZ - 1.6
FR.prism_xz(K.ngon(vx, vz, 1.3, 10), -1.0, 13.6, WHITE2)
for y in (3.0, 7.0, 11.0):
    FS.prism_xz(K.ngon(vx, vz, 1.4, 10), y, y + 0.25, STEEL2)
FS.prism_xz(K.ngon(vx, vz, 2.4, 10), 13.6, 14.0, NAVY)
FG.prism_xz(K.ngon(vx, vz, 2.2, 10), 14.0, 16.6, "6AA8D8")
for k in range(10):
    t = 2 * math.pi * (k + 0.5) / 10
    FS.box(vx + 2.2 * math.cos(t) - 0.08, vx + 2.2 * math.cos(t) + 0.08, 14.0, 16.6, vz + 2.2 * math.sin(t) - 0.08, vz + 2.2 * math.sin(t) + 0.08, NAVY)
FS.prism_xz(K.ngon(vx, vz, 2.6, 10), 16.6, 17.1, WHITE)
FS.prism_xz(K.ngon(vx, vz, 0.12, 6), 17.1, 18.6, STEEL2)
FG.prism_xz(K.ngon(vx, vz, 0.22, 6), 18.6, 18.9, "FF4A4A")
# правый бок: самолёт у телетрапа (фюзеляж вдоль z)
ax = -FX - 1.9
seg = [(-12.0, 0.7), (-10.0, 1.3), (6.0, 1.3), (10.0, 1.0), (13.0, 0.55)]
for (z0, r0), (z1, r1) in zip(seg, seg[1:]):
    FS.loft([(ax + r0 * math.cos(t), 5.2 + r0 * math.sin(t), z0) for t in [2 * math.pi * k / 10 for k in range(10)]],
            [(ax + r1 * math.cos(t), 5.2 + r1 * math.sin(t), z1) for t in [2 * math.pi * k / 10 for k in range(10)]], WHITE)
FS.box(ax - 1.35, ax - 1.2, 4.9, 5.3, -9.8, 6.0, BLUE)
for k in range(9):
    z = -8.0 + 1.6 * k
    FS.box(ax - 1.32, ax - 1.22, 5.5, 6.0, z - 0.22, z + 0.22, "2A3A5A")
FS.prism_xz([(ax - 1.0, -4.0), (ax - 1.0, 2.0), (ax - 6.0, 3.6), (ax - 6.0, 1.6)], 4.2, 4.5, WHITE2)
FS.prism_xz(K.ngon(ax - 3.4, -0.6, 0.6, 8), 3.2, 4.2, STEEL2)
FS.prism_zy([(9.0, 6.4), (12.6, 6.4), (13.2, 10.4), (11.6, 10.4)], ax - 0.15, ax + 0.15, RED)
FS.prism_zy([(10.6, 8.2), (12.8, 8.2), (13.0, 9.0), (11.2, 9.0)], ax - 0.18, ax + 0.18, WHITE)
FS.prism_xz([(ax - 0.2, 10.8), (ax - 3.0, 12.4), (ax - 3.0, 13.0), (ax - 0.2, 13.0)], 5.6, 5.8, WHITE2)
for z in (-6.0, 2.0):
    FS.box(ax - 0.15, ax + 0.15, 0.0, 3.6, z - 0.15, z + 0.15, STEEL2)
    FS.prism_zy(K.ngon(z, 0.4, 0.4, 8), ax - 0.3, ax + 0.3, DARK)
FS.box(-FX - 0.88, ax + 1.0, 4.4, 7.0, -9.0, -6.4, STEEL)  # телетрап
FG.box(-FX - 0.9, ax + 1.0, 5.0, 6.6, -9.06, -9.0, GLASS)
# тягач с вагончиками чемоданов, тележки, конусы, ветроуказатель, огни перрона
tx, tz = 8.0, -FZ - 6.4
FS.box(tx - 1.2, tx + 1.2, 0.4, 2.2, tz - 1.0, tz + 1.0, YELLOW)
FS.box(tx - 1.0, tx + 0.4, 2.2, 3.4, tz - 0.9, tz + 0.9, DARK)
for k in range(2):
    cx = tx + 3.6 + 3.4 * k
    FS.box(cx - 1.4, cx + 1.4, 0.4, 0.8, tz - 1.0, tz + 1.0, STEEL2)
    for i in range(3):
        suitcase(FS, cx - 0.8 + 0.8 * i, 0.8, tz, 0.7, 1.1 + 0.3 * (i % 2), 1.4, BAGS[(k * 3 + i) % 6], along_x=False)
    for e in (-1, 1):
        FS.prism_xy(K.ngon(cx + e * 0.9, 0.35, 0.35, 8), tz - 1.1, tz + 1.1, DARK)
for e in (-1, 1):
    FS.prism_xy(K.ngon(tx + e * 0.8, 0.4, 0.4, 8), tz - 1.1, tz + 1.1, DARK)
for k in range(3):
    x = -14.0 + 1.0 * k
    FS.box(x - 0.45, x + 0.45, 0.6 + 0.2 * k, 0.7 + 0.2 * k, -FZ - 4.6, -FZ - 3.0, STEEL)
    FS.box(x + 0.35, x + 0.45, 0.6 + 0.2 * k, 2.6 + 0.2 * k, -FZ - 3.1, -FZ - 3.0, STEEL2)
for x, z in ((-4.0, -FZ - 6.8), (-2.0, -FZ - 7.0), (2.0, -FZ - 6.8)):
    FS.cone([(x + 0.4 * math.cos(t), 0.1, z + 0.4 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]], (x, 1.3, z), ORANGE)
    FS.box(x - 0.5, x + 0.5, 0.0, 0.1, z - 0.5, z + 0.5, ORANGE)
FS.prism_xz(K.ngon(-16.6, -FZ - 6.4, 0.1, 6), 0.0, 7.0, STEEL2)
for k in range(4):
    r0, r1 = 0.5 - 0.08 * k, 0.5 - 0.08 * (k + 1)
    FS.loft([(-16.6 + 0.8 * k, 6.7 + r0 * math.cos(t), -FZ - 6.4 + r0 * math.sin(t)) for t in [2 * math.pi * i / 8 for i in range(8)]],
            [(-16.6 + 0.8 * (k + 1), 6.6 + r1 * math.cos(t), -FZ - 6.4 + r1 * math.sin(t)) for t in [2 * math.pi * i / 8 for i in range(8)]],
            (ORANGE, WHITE)[k % 2])
for k in range(10):
    x = -17.0 + 3.8 * k
    FG.prism_xz(K.ngon(x, -FZ - 2.7, 0.16, 6), -0.1, 0.2, "4A8AFF")
# флагштоки с цветными флагами у левого края перрона
for k in range(5):
    x = -13.6 + 1.9 * k
    FS.prism_xz(K.ngon(x, -FZ - 6.2, 0.08, 6), 0.0, 9.0, STEEL)
    cols = (("D83A2E", "F2F4F6", "2E6ADB"), ("3AA84A", "F2F4F6", "D83A2E"), ("F2C230", "2E6ADB", "F2C230"),
            ("2E6ADB", "F2F4F6", "2E6ADB"), ("D83A2E", "F2C230", "D83A2E"))[k]
    for i, col in enumerate(cols):
        FS.box(x + 0.1, x + 1.6, 8.8 - 0.4 * i - 0.4, 8.8 - 0.4 * i, -FZ - 6.22, -FZ - 6.18, col)
# тыл: технический блок
FS.box(-14.0, -4.0, 0.0, 5.0, FZ + 0.88, FZ + 3.4, STEEL)
for k in range(6):
    FS.box(-13.4 + 1.6 * k, -12.6 + 1.6 * k, 1.0, 4.4, FZ + 3.4, FZ + 3.5, STEEL2)

# ══ ИНТЕРЬЕР: зал ожидания ════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.0
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "DCE0E4")
for k in range(-6, 7):
    IQ.box(2.6 * k - 0.05, 2.6 * k + 0.05, 0.02, 0.04, ZF, ZB, "B8C0C8")
    IQ.box(-W, W, 0.02, 0.04, 2.5 * k - 0.05, 2.5 * k + 0.05, "B8C0C8")
IQ.box(-0.3, 0.3, 0.04, 0.06, 1.6, ZB - 0.9, YELLOW)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, WHITE)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 1.0, GREY)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, WHITE)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, BLUE)
    if idx < 2:  # огромные окна с небом и силуэтом самолёта
        slab(IG, axis, fixed, out, 0.9, -13.0, 9.0, 2.2, 14.0, SKY)
        for k in range(8):
            a = -13.0 + 22.0 * k / 7
            slab(IS, axis, fixed, out, 1.1, a - 0.12, a + 0.12, 2.0, 14.2, STEEL2)
        for y in (2.1, 8.0, 14.1):
            slab(IS, axis, fixed, out, 1.15, -13.2, 9.2, y - 0.12, y + 0.12, STEEL2)
        pr = IG.prism_zy
        d0, d1 = sorted((fixed + out * 0.94, fixed + out * 0.98))
        if idx == 0:
            pr([(-9.0, 10.6), (-1.0, 10.9), (0.4, 10.6), (-1.0, 10.3), (-9.0, 10.4)], d0, d1, "F8FCFF")
            pr([(-5.6, 10.6), (-3.8, 10.6), (-5.0, 9.0), (-6.0, 9.0)], d0, d1, "F8FCFF")
            pr([(-9.0, 10.5), (-8.2, 10.5), (-8.8, 11.8), (-9.4, 11.8)], d0, d1, "F8FCFF")
        else:
            for k in range(3):
                pr(K.octa(-8.0 + 6.0 * k, 11.6 - 1.2 * (k % 2), 1.6, 0.6, 0.4), d0, d1, "F8FCFF")
    slab(IR, axis, fixed, out, 1.3, -half, half, 15.0, 15.6, NAVY)
# большое табло и стойки регистрации у дальней стены
board(IS, IG, IS.prism_xy, IG.prism_xy, 0.0, 11.0, 18.0, 5.6, ZF + 0.88, ZF + 1.2, ZF + 1.2, ZF + 1.26, rows=7)
IS.frame_xy(K.rect(-9.4, 9.4, 7.8, 14.2), K.rect(-9.0, 9.0, 8.2, 13.8), ZF + 0.88, ZF + 1.4, NAVY)
for k, x in enumerate((-12.0, -6.0, 6.0, 12.0)):
    IR.box(x - 2.0, x + 2.0, 0.0, 3.0, ZF + 1.6, ZF + 3.2, WHITE2)
    IS.box(x - 2.1, x + 2.1, 3.0, 3.2, ZF + 1.5, ZF + 3.3, NAVY)
    IS.box(x - 1.8, x + 1.8, 3.6, 6.4, ZF + 0.88, ZF + 1.1, (BLUE, ORANGE, TEAL, RED)[k])
    IS.prism_xy(K.ngon(x, 5.0, 0.9, 10), ZF + 1.1, ZF + 1.15, WHITE)
    IS.box(x + 2.0, x + 3.6, 0.0, 0.7, ZF + 1.8, ZF + 3.0, DARK)  # весы-лента
    IS.box(x + 2.1, x + 3.5, 0.7, 0.8, ZF + 1.9, ZF + 2.9, STEEL)
    IS.box(x - 0.6, x + 0.6, 3.2, 3.9, ZF + 2.0, ZF + 2.6, DARK)
# ряды кресел по бокам
for s in (-1, 1):
    for r in range(2):
        z0 = -6.0 + 8.0 * r
        x = s * (W - 4.6 - 2.6 * (r % 2) * 0)
        IS.box(x - 0.4, x + 0.4, 0.0, 0.9, z0 - 3.0, z0 + 3.0, STEEL2)
        for k in range(5):
            z = z0 - 2.4 + 1.2 * k
            IS.box(x - 0.6, x + 0.6, 0.9, 1.2, z - 0.5, z + 0.5, SEAT)
            IS.box(*sorted((x + s * 0.55, x + s * 0.75)), 1.2, 2.6, z - 0.5, z + 0.5, SEAT)
        for z in (z0 - 3.0, z0 + 3.0):
            IS.box(x - 0.6, x + 0.6, 0.9, 1.6, z - 0.06, z + 0.06, STEEL)
# пальмы в кадках, рамка досмотра, чемоданы
for x, z in ((-13.6, 12.6), (13.6, 12.6), (-13.6, -12.0), (13.6, -12.0)):
    IS.prism_xz(K.ngon(x, z, 1.0, 8), 0.0, 1.4, WHITE2)
    D.palm(IS, (x, 1.4, z), (0.3, 0.2), 4.2)
gx, gz = -12.6, 9.0
for e in (-1, 1):
    IS.box(gx - 0.4, gx + 0.4, 0.0, 6.2, gz + e * 1.6 - 0.25, gz + e * 1.6 + 0.25, WHITE2)
IS.box(gx - 0.4, gx + 0.4, 6.2, 6.8, gz - 1.85, gz + 1.85, WHITE2)
IG.box(gx + 0.4, gx + 0.44, 6.3, 6.6, gz - 0.4, gz + 0.4, "6AE86A")
IS.box(gx - 1.4, gx + 1.4, 0.0, 2.2, gz + 2.4, gz + 6.0, STEEL)
IS.box(gx - 1.0, gx + 1.0, 2.2, 3.6, gz + 2.8, gz + 5.6, DARK)
for k, (x, z) in enumerate(((9.6, 4.6), (10.8, 5.2), (10.0, 6.6))):
    suitcase(IS, x, 0.0, z, 1.2, 1.7 - 0.3 * k, 0.6, BAGS[k + 2], along_x=True)
# жёлтые указатели под потолком и потолочные волны
for x, z, e in ((-6.0, 2.0, -1), (6.0, 2.0, 1), (0.0, -11.0, 1)):
    IS.box(x - 0.03, x + 0.03, 13.6, C - 0.6, z - 0.03, z + 0.03, STEEL2)
    IS.box(x - 2.4, x + 2.4, 12.6, 13.6, z - 0.1, z + 0.1, YELLOW)
    IS.prism_xy([(x - 1.6 * e, 12.85), (x - 0.2 * e, 12.85), (x - 0.2 * e, 12.6 + 0.1), (x + 0.9 * e, 13.1), (x - 0.2 * e, 13.5),
                 (x - 0.2 * e, 13.35), (x - 1.6 * e, 13.35)], z - 0.14, z + 0.14, DARK)
for k in range(6):
    z = -13.0 + 5.2 * k
    IS.loft([(-W, C - 0.3, z - 1.2), (W, C - 0.3, z - 1.2), (W, C - 0.3, z + 1.2), (-W, C - 0.3, z + 1.2)],
            [(-W, C - 1.0, z - 0.6), (W, C - 1.0, z - 0.6), (W, C - 1.0, z + 0.6), (-W, C - 1.0, z + 0.6)], WHITE2)
    IG.box(-W + 1.0, W - 1.0, C - 0.2, C - 0.1, z + 1.6, z + 2.4, "F0F8FF")
# багажная карусель-постамент
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.6, 16), 0.0, 0.7, STEEL)
IS.prism_xz(K.ngon(px, pz, 4.7, 16), 0.7, 0.8, STEEL2)
for k in range(20):
    t0, t1 = 2 * math.pi * k / 20, 2 * math.pi * (k + 0.92) / 20
    IS.prism_xz([(px + 3.4 * math.cos(t0), pz + 3.4 * math.sin(t0)), (px + 4.55 * math.cos(t0), pz + 4.55 * math.sin(t0)),
                 (px + 4.55 * math.cos(t1), pz + 4.55 * math.sin(t1)), (px + 3.4 * math.cos(t1), pz + 3.4 * math.sin(t1))],
                0.8, 0.92, ("33373D", "2A2D32")[k % 2])
IR.prism_xz(K.ngon(px, pz, 3.4, 16), 0.0, TOP, STEEL2)
IS.prism_xz(K.ngon(px, pz, 3.2, 16), TOP - 0.02, TOP + 0.01, "C8CED4")
for k, t in enumerate((0.6, 2.4, 4.2)):  # чемоданы на ленте
    suitcase(IS, px + 4.0 * math.cos(t), 0.92, pz + 4.0 * math.sin(t), 0.9, 0.6, 0.9, BAGS[k], along_x=True)
B.lift_leaves(IS, STEEL2, BLUE)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, WHITE)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, ASPH)
SL.box(-13.0, 13.0, 1.2, 14.4, -FZ - 0.5, -FZ, GLASS)
SL.box(-FX, FX, 15.6, 16.8, -FZ - 6.2, -FZ, WHITE2)
SL.prism_xz(K.ngon(vx, vz, 1.4, 8), -1.0, 17.0, WHITE2)
SL.box(ax - 1.6, ax + 1.6, 3.6, 6.8, -12.0, 13.0, WHITE)
SL.prism_zy([(9.0, 6.4), (12.6, 6.4), (13.2, 10.4), (11.6, 10.4)], ax - 0.2, ax + 0.2, RED)

F.build(exhibit=(PED[0], TOP, PED[1], 2.8), lamps=[("Hall", (0, 14, 6), 2600, (0.95, 0.97, 1.0)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.98, 0.95)),
                                                   ("Sky", (0, 9, ZF + 4), 700, (0.8, 0.9, 1.0))])
