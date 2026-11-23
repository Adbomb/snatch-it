"""Этаж «Робо-утёнок» музея-небоскрёба (третья партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — фабрика роботов-игрушек. Снаружи — красный кирпич со швами, цоколь из бетона с полосой «внимание»,
большие стальные окна в мелкую клетку, светящиеся тёплым, спереди — пилообразный парапет («шед»-крыша фабрики),
жёлтый промышленный манипулятор держит огромного утёнка, по конвейеру едут утята (в профиль, один глаз), справа —
две сцепленные шестерни и круглая вывеска с утёнком; по бокам — кирпичные трубы с дымом, рулонные ворота, ящики;
тыл — цистерны и трубы. Внутри — сборочный цех: бетонный пол с жёлтой разметкой, побелённый кирпич, стальные фермы
под потолком, П-образный конвейер с утятами вдоль стен, два манипулятора, пресс, покрасочная камера, ящики,
промышленные лампы; экспонат — на поворотном столе под порталом с крюком.
Запуск: blender --background --factory-startup --python scripts/blender/floor_roboduck.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab, tube  # noqa: E402

BRICK, BRICK2, MORTAR, STEEL, STEEL2, DARKM = "B5523A", "9A4230", "7A3326", "8A94A0", "6A7480", "2E3440"
YEL, YEL2, ORANGE, HAZ, HAZ2, GLASSW = "FFC420", "E8A010", "FF7A1A", "F2C230", "2A2A2A", "FFE6A0"
CONC, CONC2, WHITEB, RUBBER, GREENW, SMOKE, RED = "B8B4AC", "A09C94", "E6E0D6", "2A2A30", "2E5A4A", "D8DCE0", "D8352A"

F = B.Floor("RD", "RoboDuck", quiet=(CONC, CONC2, WHITEB), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def hazard(p, axis, fixed, out, depth, a0, a1, y0, y1, step=1.2):
    for k in range(int((a1 - a0) // step)):
        slab(p, axis, fixed, out, depth, a0 + step * k, a0 + step * (k + 1), y0, y1, HAZ if k % 2 else HAZ2)


def duck(p, x, y, z, s, facing=1, color=YEL, eye_side=-1):
    """Утёнок в профиль вдоль x: тело, голова, клюв, хвостик; один глаз со стороны eye_side (по z)."""
    p.prism_xz(K.octa(x, z, 1.0 * s, 0.7 * s, 0.35 * s), y, y + 0.9 * s, color)
    p.box(x + facing * 0.15 * s - 0.45 * s, x + facing * 0.15 * s + 0.45 * s, y + 0.9 * s, y + 1.6 * s, z - 0.4 * s, z + 0.4 * s,
          color)
    bx = x + facing * 0.6 * s
    p.box(min(bx, bx + facing * 0.5 * s), max(bx, bx + facing * 0.5 * s), y + 1.05 * s, y + 1.3 * s, z - 0.2 * s, z + 0.2 * s,
          ORANGE)
    p.box(x - facing * 1.0 * s - 0.15 * s, x - facing * 1.0 * s + 0.15 * s, y + 0.7 * s, y + 1.1 * s, z - 0.2 * s, z + 0.2 * s,
          color)
    ez = z + eye_side * 0.41 * s
    p.box(x + facing * 0.3 * s - 0.1 * s, x + facing * 0.3 * s + 0.1 * s, y + 1.3 * s, y + 1.45 * s, min(ez, ez + eye_side * 0.04),
          max(ez, ez + eye_side * 0.04), "1A1A1A")


def gear(prism, cx, cy, r, teeth, d0, d1, color):
    prism(K.ngon(cx, cy, r, 12), d0, d1, color)
    for k in range(teeth):
        t = 2 * math.pi * k / teeth
        c, s = math.cos(t), math.sin(t)
        w, L = 0.45, r + 0.7
        pts = [(cx + c * (r - 0.2) - s * w, cy + s * (r - 0.2) + c * w), (cx + c * L - s * w * 0.7, cy + s * L + c * w * 0.7),
               (cx + c * L + s * w * 0.7, cy + s * L - c * w * 0.7), (cx + c * (r - 0.2) + s * w, cy + s * (r - 0.2) - c * w)]
        prism(pts, d0, d1, color)
    prism(K.ngon(cx, cy, r * 0.35, 8), d0 - 0.15 if d0 < 0 else d0, d1 + 0.15 if d1 > 0 else d1, DARKM)


def arm(p, base, joints, w, color):
    """Манипулятор: тумба, звенья-брусья, шарниры."""
    bx, by, bz = base
    p.prism_xz(K.octa(bx, bz, 1.4, 1.4, 0.55), by, by + 0.8, DARKM)
    p.prism_xz(K.octa(bx, bz, 1.0, 1.0, 0.4), by + 0.8, by + 1.6, color)
    pts = [(bx, by + 1.6, bz)] + joints
    for a, b in zip(pts, pts[1:]):
        beam(p, a, b, w, w, color)
    for x, y, z in pts[1:]:
        p.prism_xz(K.octa(x, z, w * 0.75, w * 0.75, w * 0.3), y - w * 0.6, y + w * 0.6, DARKM)


# ══ ФАСАД: фабрика игрушек ════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, BRICK2, BRICK2, STEEL2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 5.88 if fi == 0 else 2.88, -half - 2.88, half + 2.88, -1.0, -0.2, CONC2)
    slab(FR, axis, fixed, out, 4.88 if fi == 0 else 1.88, -half - 1.88, half + 1.88, -0.2, 1.6, CONC)  # спереди — погрузочная платформа
    hazard(FS, axis, fixed, out, 1.95, -half - 1.8, half + 1.8, 1.0, 1.4)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.6, 15.6, BRICK)
    for k in range(14):  # швы кладки
        y = 2.4 + 1.0 * k
        slab(FS, axis, fixed, out, 0.93, -half, half, y, y + 0.12, MORTAR)
    for k in range(int(2 * half // 6.0) + 1):  # пилястры
        a = -half + 6.0 * k
        slab(FR, axis, fixed, out, 1.88, max(a - 0.8, -half), min(a + 0.8, half), 1.6, 15.6, BRICK2)
    slab(FR, axis, fixed, out, 1.88, -half - 0.6, half + 0.6, 15.6, 16.4, CONC)  # бетонный пояс
    if axis == "z":  # окна в мелкую клетку между пилястрами
        for k in range(int(2 * half // 6.0)):
            a = -half + 3.0 + 6.0 * k
            if fi == 0 and -12.5 < a < 3.0:
                continue
            slab(FS, axis, fixed, out, 1.2, a - 2.0, a + 2.0, 7.0, 13.6, GREENW)
            slab(FG, axis, fixed, out, 1.25, a - 1.75, a + 1.75, 7.25, 13.35, GLASSW)
            for m in range(1, 4):
                slab(FS, axis, fixed, out, 1.32, a - 2.0 + m, a - 1.9 + m, 7.25, 13.35, GREENW)
            for m in range(1, 5):
                slab(FS, axis, fixed, out, 1.32, a - 1.75, a + 1.75, 7.25 + 1.22 * m, 7.37 + 1.22 * m, GREENW)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# пилообразный парапет: спереди и сзади — профиль «шед»-крыши, по бокам — ровный с остеклением
for z0, z1 in ((-FZ - 1.6, -FZ + 0.05), (FZ - 0.05, FZ + 1.6)):
    for k in range(6):
        x0 = -FX + 6.04 * k
        FR.prism_xy([(x0, 16.4), (x0 + 6.04, 16.4), (x0 + 6.04, 18.9), (x0 + 0.3, 16.9)], z0, z1, BRICK2)
        FG.prism_xy([(x0 + 5.3, 16.9), (x0 + 5.9, 16.9), (x0 + 5.9, 18.6), (x0 + 5.3, 18.2)],
                    z0 - 0.06 if z0 < 0 else z0, z1 + 0.06 if z1 > 0 else z1, GLASSW)
for s in (-1, 1):
    slab(FR, "x", s * FX, s, 1.6, -FZ, FZ, 16.4, 17.6, BRICK2)
    slab(FS, "x", s * FX, s, 1.7, -FZ, FZ, 17.6, 17.8, CONC)
# манипулятор держит большого утёнка, конвейер с утятами
arm(FS, (-14.0, 1.6, -FZ - 3.0), [(-12.6, 7.4, -FZ - 3.4), (-8.4, 10.8, -FZ - 3.6), (-6.4, 9.4, -FZ - 3.6)], 1.0, YEL)
for e in (-1, 1):
    FS.box(-6.6, -5.4, 8.6, 9.4, -FZ - 3.6 + e * 0.9 - 0.2, -FZ - 3.6 + e * 0.9 + 0.2, STEEL)
duck(FS, -5.2, 5.6, -FZ - 3.6, 2.4, 1, YEL)
FS.box(-12.0, 3.0, 3.2, 4.0, -FZ - 3.6, -FZ - 1.6, RUBBER)  # конвейер
for x in (-12.0, 3.0):
    FS.prism_zy(K.octa(-FZ - 2.6, 3.6, 1.05, 0.5, 0.2), x - 0.3, x + 0.3, STEEL2)
for x in (-10.0, -5.0, 0.0):
    FS.box(x - 0.2, x + 0.2, 1.6, 3.2, -FZ - 3.4, -FZ - 3.0, STEEL2)
for k, x in enumerate((-10.4, -7.6, -1.6, 1.4)):
    duck(FS, x, 4.0, -FZ - 2.6, 0.75, 1, YEL if k % 2 else "C8CCD4")
for s_, (cx, cy, r) in enumerate(((7.4, 9.2, 2.6), (11.6, 12.6, 1.8))):  # шестерни
    gear(FS.prism_xy, cx, cy, r, 10 if s_ == 0 else 8, -FZ - 1.6, -FZ - 1.2, (STEEL, YEL2)[s_])
FS.frame_xy(K.ngon(13.6, 6.0, 2.1, 12), K.ngon(13.6, 6.0, 1.7, 12), -FZ - 1.5, -FZ, YEL)  # круглая вывеска
FS.prism_xy(K.ngon(13.6, 6.0, 1.75, 12), -FZ - 1.2, -FZ, "3060B0")
duck(FS, 13.5, 4.9, -FZ - 1.4, 1.0, 1, YEL)
# бока: кирпичные трубы с дымом, рулонные ворота, ящики
for s in (-1, 1):
    fx = s * FX
    cx = fx + s * 2.2
    for k in range(6):
        FR.prism_xz(K.ngon(cx, 12.0, 1.8 - 0.06 * k, 12), 3.0 * k - 0.2, 3.0 * k + 2.8, BRICK if k % 2 else BRICK2)
    for y in (6.0, 12.0):
        FS.prism_xz(K.ngon(cx, 12.0, 1.9, 12), y, y + 0.4, HAZ)
    for k, (dx, y, r) in enumerate(((0.0, 18.0, 1.2), (s * 0.9, 18.4, 0.9), (-s * 0.6, 18.5, 0.7))):
        FS.prism_xz(K.octa(cx + dx, 12.0 + 0.5 * k, r, r, r * 0.4), y - 0.5, min(y + 0.45, 18.95), SMOKE)
    FS.box(fx, fx + s * 1.3, 1.6, 9.6, -6.0, 2.0, STEEL2)  # рулонные ворота
    for k in range(10):
        FS.box(fx + s * 1.3, fx + s * 1.4, 1.9 + 0.75 * k, 2.3 + 0.75 * k, -5.8, 1.8, STEEL)
    hazard(FS, "x", fx, s, 1.45, -6.4, 2.4, 9.6, 10.2, 1.1)
    for k, (z, w, h) in enumerate(((-12.0, 1.4, 1.6), (-12.4, 1.0, 1.0), (6.0, 1.3, 2.4))):
        FS.box(fx + s * 0.2, fx + s * (0.2 + 2 * w), 1.6, 1.6 + h, z - w, z + w, ("C89A5A", "A87A40")[k % 2])
# тыл: цистерны и трубы
for x in (-9.0, 9.0):
    FS.prism_xz(K.ngon(x, FZ + 3.0, 2.6, 12), -0.2, 10.0, STEEL)
    FS.prism_xz(K.ngon(x, FZ + 3.0, 2.7, 12), 3.0, 3.4, HAZ)
    FS.cone([(px_, 10.0, pz_) for px_, pz_ in K.ngon(x, FZ + 3.0, 2.6, 12)], (x, 11.6, FZ + 3.0), STEEL2)
tube(FS, [(-9.0, 8.0, FZ + 0.6), (0.0, 9.2, FZ + 0.6), (9.0, 8.0, FZ + 0.6)], [0.6] * 3, 0.6, (0, 0, 1), YEL2)

# ══ ИНТЕРЬЕР: сборочный цех ═══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), CONC)
for x in (-4.4, 4.4):  # жёлтая разметка прохода
    IS.box(x - 0.12, x + 0.12, 0.02, 0.05, 1.0, 15.5, HAZ)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.0, CONC2)
        hazard(IS, axis, fixed, out, 0.95, a0, a1, 0.2, 0.6, 1.0)
        slab(IQ, axis, fixed, out, 0.88, a0, a1, 1.0, 13.0, WHITEB)
    for k in range(11):  # швы побелённой кладки
        y = 1.8 + 1.0 * k
        for a0, a1 in (spans if y < DOOR[1] else ((-half, half),)):
            slab(IS, axis, fixed, out, 0.92, a0, a1, y, y + 0.08, "D2CCC2")
    if gap:
        slab(IQ, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 13.0, WHITEB)
    slab(IR, axis, fixed, out, 0.88, -half, half, 13.0, C, STEEL2)
    for k in range(int(2 * half // 6.0) + 1):  # стальные колонны
        a = -half + 6.0 * k
        if gap and abs(a) < DOOR[0] + 1.5:
            continue
        slab(IS, axis, fixed, out, 1.5, max(a - 0.4, -half), min(a + 0.4, half), 0.0, C, STEEL)
# фермы под потолком
for z in (-10.0, -2.0, 6.0, 13.0):
    beam(IS, (-W, 16.8, z), (W, 16.8, z), 0.4, 0.4, STEEL)
    beam(IS, (-W, 14.6, z), (W, 14.6, z), 0.3, 0.3, STEEL)
    for k in range(8):
        x0 = -W + 4.22 * k
        beam(IS, (x0, 14.6, z), (x0 + 4.22, 16.8, z), 0.18, 0.18, STEEL2)
for x, z in ((-8.0, -8.0), (8.0, -8.0), (-8.0, 4.0), (8.0, 4.0)):  # промышленные лампы
    IS.box(x - 0.05, x + 0.05, 13.0, 14.6, z - 0.05, z + 0.05, DARKM)
    IS.loft([(x + 1.0 * math.cos(2 * math.pi * k / 8), 12.2, z + 1.0 * math.sin(2 * math.pi * k / 8)) for k in range(8)],
            [(x + 0.3 * math.cos(2 * math.pi * k / 8), 13.0, z + 0.3 * math.sin(2 * math.pi * k / 8)) for k in range(8)], GREENW)
    IG.prism_xz(K.octa(x, z, 0.5, 0.5, 0.2), 12.1, 12.2, GLASSW)
# П-образный конвейер с утятами
belts = ((-13.6, -11.6, -12.6, 6.0), (-13.6, 13.6, -13.6, -11.6), (11.6, 13.6, -12.6, 6.0))
for x0, x1, z0, z1 in belts:
    IS.box(x0, x1, 1.8, 2.2, z0, z1, RUBBER)
    IS.box(x0 - 0.1, x1 + 0.1, 1.6, 1.8, z0 - 0.1, z1 + 0.1, STEEL2)
for x, z in ((-13.4, -11.4), (13.4, -11.4), (-12.6, 5.6), (12.6, 5.6), (-12.6, -4.0), (12.6, -4.0)):
    IS.box(x - 0.2, x + 0.2, 0.0, 1.6, z - 0.2, z + 0.2, STEEL2)
for k in range(5):
    duck(IS, -12.6, 2.2, -9.0 + 3.4 * k, 0.6, 1, YEL if k % 2 else "C8CCD4", eye_side=1)
    duck(IS, 12.6, 2.2, -9.0 + 3.4 * k, 0.6, -1, YEL if k % 2 == 0 else "C8CCD4", eye_side=-1)
for k in range(6):
    duck(IS, -9.0 + 3.6 * k, 2.2, -12.6, 0.6, 1, (YEL, "C8CCD4", ORANGE)[k % 3], eye_side=1)
arm(IS, (-9.0, 0.0, -9.0), [(-9.2, 4.6, -9.4), (-11.4, 6.0, -10.6), (-12.4, 3.4, -11.8)], 0.6, YEL)
arm(IS, (9.0, 0.0, -9.0), [(9.2, 4.6, -9.4), (11.4, 6.0, -10.6), (12.4, 3.4, -11.8)], 0.6, ORANGE)
# пресс и покрасочная камера
IS.box(-15.6, -10.6, 0.0, 1.0, 9.0, 13.6, DARKM)
IS.box(-15.2, -11.0, 1.0, 2.0, 9.4, 13.2, STEEL)
for x in (-14.8, -11.4):
    IS.box(x - 0.3, x + 0.3, 2.0, 8.0, 10.9, 11.7, STEEL2)
IS.box(-15.4, -10.8, 8.0, 9.2, 9.4, 13.2, YEL2)
IS.box(-13.6, -12.6, 4.0, 8.0, 10.8, 11.8, STEEL)
IS.box(10.6, 15.8, 0.0, 6.6, 9.0, 14.0, "C8D0D8")
IS.box(10.4, 16.0, 6.6, 7.2, 8.8, 14.2, YEL)
IG.box(10.5, 10.6, 2.0, 5.6, 9.6, 13.4, "FFF0B0")
# поворотный стол под порталом с крюком
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.2, 16), 0.0, 0.6, DARKM)
IR.prism_xz(K.ngon(px, pz, 3.6, 16), 0.6, TOP, STEEL)
for k in range(16):  # жёлто-чёрная кромка
    t0, t1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
    pts = [(px + 4.2 * math.cos(t0), pz + 4.2 * math.sin(t0)), (px + 4.32 * math.cos(t0), pz + 4.32 * math.sin(t0)),
           (px + 4.32 * math.cos(t1), pz + 4.32 * math.sin(t1)), (px + 4.2 * math.cos(t1), pz + 4.2 * math.sin(t1))]
    IS.prism_xz(pts, 0.1, 0.5, HAZ if k % 2 else HAZ2)
gz = pz - 3.6  # портал позади экспоната, крюк — на консоли над ним
for s in (-1, 1):
    IS.box(px + s * 6.0 - 0.5, px + s * 6.0 + 0.5, 0.0, 13.0, gz - 0.5, gz + 0.5, YEL)
    IS.box(px + s * 6.0 - 0.8, px + s * 6.0 + 0.8, 0.0, 0.5, gz - 0.8, gz + 0.8, DARKM)
IS.box(px - 6.5, px + 6.5, 13.0, 14.0, gz - 0.6, gz + 0.6, YEL)
IS.box(px - 0.5, px + 0.5, 13.1, 13.9, gz + 0.6, pz + 0.6, YEL2)
IS.box(px - 0.8, px + 0.8, 12.2, 13.1, pz - 0.8, pz + 0.8, DARKM)
IS.box(px - 0.05, px + 0.05, 9.6, 12.2, pz - 0.05, pz + 0.05, DARKM)
tube(IS, [(px, 9.6, pz), (px + 0.5, 9.0, pz), (px, 8.6, pz), (px - 0.4, 9.0, pz)], [0.2] * 4, 0.2, (0, 0, 1), STEEL2)
B.lift_leaves(IS, STEEL2, HAZ)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, BRICK)
SL.box(-FX - 1.9, FX + 1.9, -1.0, 1.6, -FZ - 1.9, FZ + 1.9, CONC)
SL.box(-FX - 0.6, FX + 0.6, 15.6, 17.6, -FZ - 1.9, FZ + 1.9, CONC)
SL.box(-FX, FX, 17.6, 18.9, -FZ - 1.6, -FZ, BRICK2)
SL.box(-8.0, -2.4, 5.6, 9.4, -FZ - 4.8, -FZ - 2.4, YEL)
SL.box(5.0, 13.4, 6.6, 14.4, -FZ - 1.6, -FZ, STEEL)
for s in (-1, 1):
    SL.box(s * (FX + 0.4), s * (FX + 4.0), -0.2, 18.8, 10.2, 13.8, BRICK2)

F.build(exhibit=(PED[0], TOP, PED[1], 3.2), lamps=[("Hall", (0, 14, 6), 3000, (1.0, 0.95, 0.88)),
                                                   ("Spot", (0, 12, -3), 3200, (1.0, 0.97, 0.9))])
