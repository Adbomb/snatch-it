"""Этаж «Цветок-монстр» музея-небоскрёба (третья партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — викторианская оранжерея, из которой вырываются хищные растения. Снаружи — кирпичный цоколь с
каменным поясом, выше — белый чугунный переплёт с бледно-зелёными стёклами (оттенки чередуются, несколько стёкол
выбито), спереди над карнизом — полукруглое веерное окно, по верху — чугунный гребень с навершиями; из выбитого
стекла слева вырывается огромная мухоловка на изогнутом стебле с раскрытыми створками (зелёные снаружи, розовые
внутри, с белыми зубцами; без «глаз»), по фасаду ползут лозы с огромными листьями, у углов — кувшиночники в
терракотовых горшках; бока — лозы-щупальца из окон; тыл — сарай для рассады с лейками. Внутри — ботанический зал:
пол из терракотовой плитки, кирпичные грядки с землёй вдоль стен (мухоловки, кувшиночники, росянки с каплями,
огромные листья), стеклянные стены и рёбра свода, подвесные корзины с лозами, трубы туманообразователя, стол для
пересадки; экспонат — на огромном терракотовом горшке с кольцом мха.
Запуск: blender --background --factory-startup --python scripts/blender/floor_greenhouse.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab, taper, tube  # noqa: E402

FRAME, FRAME2, PANE, PANE2, PANE3, DARKP = "F4F6F2", "DDE4DC", "BFE8D8", "A8DCC8", "CFF0E4", "3A5A4A"
BRICK, BRICK2, STONEC, LEAF, LEAF2, LEAF3 = "B5603E", "9A4E32", "D8D2C4", "3FAE4A", "2E8A3A", "6ACB5A"
TRAP, TRAP2, TOOTH, SOIL, POT, POT2, WOOD, MOSS = "E0405A", "FF8AA0", "F4F0D8", "4A3424", "C8703E", "A85A30", "A8743A", "4C9A2E"
TILE, TILE2, DEW, FLOWERP, CAN = "C87850", "B06840", "D8FFF0", "A04AD8", "6A9AB0"

F = B.Floor("MF", "MonsterFlower", quiet=(TILE, SOIL, PANE3), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def leaf(p, base, tip, w, color):
    """Большой лист: сужается к основанию и к кончику."""
    mid = tuple(base[i] + (tip[i] - base[i]) * 0.45 for i in range(3))
    taper(p, base, mid, w * 0.25, w, color)
    taper(p, mid, tip, w, 0.1, color)


def flytrap(p, base, top, size, open_deg=55):
    """Мухоловка: стебель-трубка к top, две створки (снаружи зелёные, внутри розовые) с белыми зубцами."""
    tube(p, [base, tuple((base[i] + top[i]) / 2 + (0.6 if i == 0 else 0.0) for i in range(3)), top],
         [size * 0.32, size * 0.28, size * 0.24], size * 0.28, (0, 0, 1), LEAF2)
    tx, ty, tz = top
    for s in (-1, 1):
        a = math.radians(open_deg) * s
        pts_o, pts_i = [], []
        for k in range(7):
            t = math.pi * k / 6
            u, v = size * math.sin(t) * 0.9, size * (1 - math.cos(t)) * 0.55
            x = tx + u * 1.0 - 0.0
            y = ty + v * math.cos(a)
            z = tz + v * math.sin(a)
            pts_o.append((x - size * 0.9 + 0.9 * size, y, z))
        for k, (x, y, z) in enumerate(pts_o):
            if 0 < k < 6:
                tip = (x, y + size * 0.35 * math.cos(a), z + size * 0.35 * math.sin(a))
                taper(p, (x, y, z), tip, 0.18 * size, 0.03, TOOTH)
        ring_o = [(tx - size * 0.05, ty, tz)] + pts_o + [(tx + size * 0.05, ty, tz)]
        th = 0.12 * size
        p.loft([(x, y, z) for x, y, z in ring_o], [(x, y - th * math.sin(a) * s * 0 + 0.0, z - th * s) for x, y, z in ring_o],
               TRAP2)
        p.loft([(x, y, z - th * s) for x, y, z in ring_o], [(x, y, z - th * 2 * s) for x, y, z in ring_o], LEAF)


def pitcher(p, x, y, z, h, r):
    """Кувшиночник: трубчатый кувшин с крышечкой."""
    p.prism_xz(K.octa(x, z, r * 0.7, r * 0.7, r * 0.28), y, y + h * 0.3, LEAF2)
    p.prism_xz(K.octa(x, z, r, r, r * 0.41), y + h * 0.3, y + h * 0.85, LEAF3)
    p.prism_xz(K.octa(x, z, r * 1.12, r * 1.12, r * 0.45), y + h * 0.85, y + h * 0.95, TRAP)
    p.loft([(x - r * 0.9, y + h, z - r * 0.4), (x + r * 0.9, y + h, z - r * 0.4), (x + r * 0.9, y + h, z + r * 0.4),
            (x - r * 0.9, y + h, z + r * 0.4)],
           [(x - r * 0.7, y + h + r * 0.9, z - r * 0.9), (x + r * 0.7, y + h + r * 0.9, z - r * 0.9),
            (x + r * 0.7, y + h + r * 0.9, z - r * 0.6), (x - r * 0.7, y + h + r * 0.9, z - r * 0.6)], TRAP)


def pot(p, x, z, r, h, y=0.0):
    p.loft([(x + r * 0.75 * math.cos(2 * math.pi * k / 10), y, z + r * 0.75 * math.sin(2 * math.pi * k / 10)) for k in range(10)],
           [(x + r * math.cos(2 * math.pi * k / 10), y + h, z + r * math.sin(2 * math.pi * k / 10)) for k in range(10)], POT)
    p.prism_xz(K.ngon(x, z, r * 1.08, 10), y + h, y + h + r * 0.22, POT2)
    p.prism_xz(K.ngon(x, z, r * 0.92, 10), y + h + r * 0.22, y + h + r * 0.26, SOIL)


# ══ ФАСАД: оранжерея с хищными растениями ═════════════════════════════════════════════════════════════════════
B.shell_planes(F, DARKP, DARKP, PANE3)
BROKEN = {(0, 1, 2), (0, 2, 2), (2, 3, 1), (3, 5, 2)}
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 4.88 if fi == 0 else 2.88, -half - 2.88, half + 2.88, -1.0, -0.2, TILE2)
    slab(FR, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, -0.2, 3.0, BRICK)  # кирпичный цоколь
    for k in range(3):
        slab(FS, axis, fixed, out, 1.93, -half - 1.88, half + 1.88, 0.6 + 0.8 * k, 0.68 + 0.8 * k, BRICK2)
    slab(FR, axis, fixed, out, 2.2, -half - 2.2, half + 2.2, 3.0, 3.6, STONEC)
    cols = 9 if axis == "z" else 8
    wcol = 2 * half / cols
    for c in range(cols):  # чугунный переплёт со стёклами
        a0 = -half + wcol * c
        for r, (y0, y1) in enumerate(((3.6, 7.6), (7.6, 11.6), (11.6, 15.4))):
            col = (PANE, PANE2, PANE3)[(c * 2 + r + fi) % 3]
            if (fi, c, r) in BROKEN:
                col = DARKP
            slab(FS, axis, fixed, out, 0.95, a0 + 0.15, a0 + wcol - 0.15, y0 + 0.15, y1 - 0.15, col)
            slab(FS, axis, fixed, out, 1.05, a0 + wcol / 2 - 0.07, a0 + wcol / 2 + 0.07, y0, y1, FRAME2)
        slab(FS, axis, fixed, out, 1.2, a0 - 0.15, a0 + 0.15, 3.6, 15.4, FRAME)
    for y in (7.6, 11.6):
        slab(FS, axis, fixed, out, 1.2, -half, half, y - 0.15, y + 0.15, FRAME)
    slab(FS, axis, fixed, out, 1.8, -half - 0.6, half + 0.6, 15.4, 16.2, FRAME)  # карниз
    slab(FR, axis, fixed, out, 0.88, -half, half, 16.2, 19.0, FRAME2)
    B.chamfer(FS, axis, fixed, out, -half, half, [(0.0, 16.2), (1.6, 16.2), (0.6, 18.6), (0.0, 18.6)], PANE3)  # скат кровли
    n = int(2 * half // 2.4)
    for k in range(n + 1):  # рёбра ската
        a = -half + 2 * half * k / n
        B.chamfer(FS, axis, fixed, out, a - 0.1, a + 0.1, [(0.0, 16.2), (1.7, 16.2), (0.7, 18.7), (0.0, 18.7)], FRAME)
    for k in range(int(2 * half // 3.0) + 1):  # чугунный гребень с навершиями
        a = -half + 3.0 * k
        x, z = (a, fixed + out * 0.5) if axis == "z" else (fixed + out * 0.5, a)
        FS.prism_xz(K.octa(x, z, 0.15, 0.15, 0.06), 18.6, 18.9, FRAME)
        FS.cone([(x - 0.25, 18.9, z - 0.25), (x + 0.25, 18.9, z - 0.25), (x + 0.25, 18.9, z + 0.25), (x - 0.25, 18.9, z + 0.25)],
                (x, 18.98, z), FRAME)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# перед: полукруглое веерное окно над карнизом
FS.prism_xy([(-6.0, 16.2)] + [(-6.0 * math.cos(math.pi * k / 8), 16.2 + 2.7 * math.sin(math.pi * k / 8)) for k in range(9)],
            -FZ - 1.8, -FZ - 1.6, PANE)
FS.frame_xy([(-6.4, 16.0)] + [(-6.4 * math.cos(math.pi * k / 8), 16.0 + 2.95 * math.sin(math.pi * k / 8)) for k in range(9)],
            [(-6.0, 16.2)] + [(-6.0 * math.cos(math.pi * k / 8), 16.2 + 2.7 * math.sin(math.pi * k / 8)) for k in range(9)],
            -FZ - 1.95, -FZ - 1.6, FRAME)
for k in range(1, 8):
    t = math.pi * k / 8
    beam(FS, (0.0, 16.2, -FZ - 1.9), (-5.9 * math.cos(t), 16.2 + 2.65 * math.sin(t), -FZ - 1.9), 0.14, 0.14, FRAME)
# мухоловка вырывается из выбитого стекла слева, лозы с огромными листьями
flytrap(FS, (-11.0, 5.0, -FZ - 0.6), (-11.6, 11.6, -FZ - 5.6), 4.8, 50)
for a, b in (((-11.0, 4.0, -FZ - 1.0), (-6.6, 2.2, -FZ - 4.6)), ((-12.0, 6.4, -FZ - 1.4), (-17.0, 4.4, -FZ - 4.4)),
             ((-11.4, 8.4, -FZ - 2.6), (-15.6, 10.6, -FZ - 5.0))):
    leaf(FS, a, b, 2.6, LEAF)
vine = [(14.0, 3.6, -FZ - 1.3), (12.0, 7.0, -FZ - 1.4), (14.6, 10.4, -FZ - 1.4), (11.4, 13.6, -FZ - 1.4), (8.0, 15.0, -FZ - 1.6)]
tube(FS, vine, [0.5, 0.45, 0.4, 0.35, 0.3], 0.4, (0, 0, 1), LEAF2)
for k, (x, y, z) in enumerate(vine[1:]):
    leaf(FS, (x, y, z - 0.2), (x + (2.4 if k % 2 else -2.4), y + 0.8, z - 1.6), 1.6, (LEAF, LEAF3)[k % 2])
for x, z in ((-FX - 1.0, -FZ - 1.6), (FX + 1.0, -FZ - 1.6)):  # кувшиночники в горшках у углов
    pot(FS, x, z, 1.4, 2.2, -0.2)
    pitcher(FS, x, 2.3, z, 4.0, 0.9)
    pitcher(FS, x + 0.9, 2.3, z - 0.6, 2.8, 0.6)
FS.box(6.2, 6.5, -0.2, 7.0, -FZ - 3.4, -FZ - 3.1, "3A4A40")  # газовый фонарь справа от дверей (один)
FS.prism_xz(K.octa(6.35, -FZ - 3.25, 0.5, 0.5, 0.2), 7.0, 7.2, "3A4A40")
FG.prism_xz(K.octa(6.35, -FZ - 3.25, 0.4, 0.4, 0.16), 7.2, 8.4, "FFE6A0")
FS.cone([(x, 8.4, z) for x, z in K.octa(6.35, -FZ - 3.25, 0.55, 0.55, 0.22)], (6.35, 9.0, -FZ - 3.25), "3A4A40")
FS.box(-3.0, 3.0, 3.6, 10.0, -FZ - 1.3, -FZ, FRAME)  # двери оранжереи
FS.box(-2.6, -0.1, 3.6, 9.6, -FZ - 1.4, -FZ - 1.3, PANE2)
FS.box(0.1, 2.6, 3.6, 9.6, -FZ - 1.4, -FZ - 1.3, PANE)
for k in range(3):
    FS.box(-3.0, 3.0, -0.2, 3.0 - 0.8 * (k + 1), -FZ - 1.9 - 0.7 * k, -FZ - 1.2 - 0.7 * k, STONEC)  # ступени к дверям
# бока: лозы-щупальца из окон
for s in (-1, 1):
    fx = s * FX
    for z0 in (-6.0, 8.0):
        pts = [(fx + s * 0.6, 9.6, z0), (fx + s * 3.0, 11.6, z0 + 2.0), (fx + s * 4.2, 9.0, z0 + 4.0), (fx + s * 3.2, 6.0, z0 + 3.0)]
        tube(FS, pts, [0.7, 0.55, 0.4, 0.2], 0.5, (0, 1, 0), LEAF2)
        for k, (x, y, z) in enumerate(pts[1:3]):
            leaf(FS, (x, y, z), (x + s * 1.6, y + 1.4, z - 1.6), 1.4, LEAF3)
        FS.prism_xz(K.octa(fx + s * 3.2, z0 + 3.0, 0.5, 0.5, 0.2), 5.4, 6.0, FLOWERP)
# тыл: сарай для рассады с лейками
FS.box(-8.0, 0.0, -0.2, 8.0, FZ + 0.4, FZ + 4.4, WOOD)
FS.loft([(-8.6, 8.0, FZ + 0.2), (0.6, 8.0, FZ + 0.2), (0.6, 8.0, FZ + 5.0), (-8.6, 8.0, FZ + 5.0)],
        [(-8.6, 9.6, FZ + 0.2), (0.6, 9.6, FZ + 0.2), (0.6, 9.6, FZ + 2.0), (-8.6, 9.6, FZ + 2.0)], "6A4A30")
for k in range(5):
    FS.box(-7.8 + 1.6 * k, -7.7 + 1.6 * k, -0.2, 8.0, FZ + 4.4, FZ + 4.5, "8A5A32")
for x in (2.0, 4.0):
    FS.prism_xz(K.octa(x, FZ + 1.6, 0.6, 0.6, 0.24), -0.2, 1.2, CAN)
    beam(FS, (x + 0.5, 0.6, FZ + 1.6), (x + 1.4, 1.4, FZ + 1.6), 0.15, 0.15, CAN)

# ══ ИНТЕРЬЕР: ботанический зал ════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.6
px, pz = PED
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), TILE)
for i in range(-8, 9):
    IS.box(2.0 * i - 0.05, 2.0 * i + 0.05, 0.02, 0.05, ZF, ZB, TILE2)
for j in range(-8, 8):
    IS.box(-W, W, 0.02, 0.05, 2.0 * j - 0.05, 2.0 * j + 0.05, TILE2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    slab(IQ, axis, fixed, out, 0.7, -half, half, 0.0, C, PANE3)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 3.0, BRICK)
        slab(IS, axis, fixed, out, 1.1, a0, a1, 3.0, 3.4, STONEC)
    n = int(2 * half // 3.0)
    for k in range(n + 1):  # белые рёбра переплёта
        a = -half + 2 * half * k / n
        if gap and abs(a) < DOOR[0] + 0.6:
            continue
        slab(IS, axis, fixed, out, 0.9, a - 0.12, a + 0.12, 3.4, C, FRAME)
    for y in (8.0, 13.0):
        for a0, a1 in (spans if y < DOOR[1] else ((-half, half),)):
            slab(IS, axis, fixed, out, 0.9, a0, a1, y - 0.12, y + 0.12, FRAME)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 12.0, BRICK2)
    slab(IS, axis, fixed, out, 1.2, -half, half, 15.6, 16.0, CAN)  # труба туманообразователя
for z in (-12.0, -6.0, 0.0, 6.0, 12.0):  # рёбра свода
    tube(IS, [(-W, C - 2.0, z), (-8.0, C - 0.4, z), (8.0, C - 0.4, z), (W, C - 2.0, z)], [0.3] * 4, 0.3, (0, 0, 1), FRAME)
# кирпичные грядки вдоль боковых стен с хищными растениями
for s in (-1, 1):
    x0, x1 = sorted((s * W, s * (W - 3.2)))
    IR.box(x0, x1, 0.0, 1.0, -14.6, 5.0, BRICK2)
    IQ.box(x0 + 0.2, x1 - 0.2, 0.9, 1.05, -14.4, 4.8, SOIL)
    cx = s * (W - 1.6)
    flytrap(IS, (cx, 1.0, -11.0), (cx - s * 0.6, 4.4, -10.4), 1.6, 45)
    flytrap(IS, (cx, 1.0, 1.6), (cx - s * 0.4, 3.6, 2.2), 1.2, 60)
    pitcher(IS, cx, 1.0, -6.4, 3.0, 0.7)
    pitcher(IS, cx + s * 0.4, 1.0, -4.8, 2.0, 0.5)
    for k in range(3):  # росянки с каплями
        z = -2.6 + 1.0 * k
        IS.box(cx - 0.05, cx + 0.05, 1.0, 2.6 + 0.4 * k, z - 0.05, z + 0.05, LEAF2)
        IG.prism_xz(K.octa(cx, z, 0.18, 0.18, 0.07), 2.6 + 0.4 * k, 2.9 + 0.4 * k, DEW)
    for k in range(4):
        z = -14.0 + 5.0 * k
        leaf(IS, (cx, 1.0, z), (cx - s * 2.6, 4.2 + rng(s, k), z + 1.4), 1.6, (LEAF, LEAF3)[k % 2])
# грядка у передней стены и стол для пересадки
IR.box(-14.0, -6.0, 0.0, 1.0, ZF, ZF + 2.6, BRICK2)
IQ.box(-13.8, -6.2, 0.9, 1.05, ZF + 0.2, ZF + 2.4, SOIL)
for k in range(3):
    leaf(IS, (-12.0 + 2.6 * k, 1.0, ZF + 1.3), (-12.6 + 2.6 * k, 6.0 + rng(k, 7) * 2, ZF + 2.8), 1.8, (LEAF2, LEAF, LEAF3)[k])
flytrap(IS, (9.0, 0.0, ZF + 2.0), (9.6, 6.4, ZF + 3.4), 2.0, 55)
pot(IS, 9.0, ZF + 2.0, 1.6, 1.2)
IS.box(10.6, 15.8, 2.6, 2.8, 9.0, 13.0, WOOD)  # стол для пересадки
for x in (10.9, 15.5):
    for z in (9.3, 12.7):
        IS.box(x - 0.12, x + 0.12, 0.0, 2.6, z - 0.12, z + 0.12, "8A5A32")
for k, x in enumerate((11.6, 13.2, 14.8)):
    pot(IS, x, 11.0, 0.5, 0.6, 2.8)
    IS.prism_xz(K.octa(x, 11.0, 0.3, 0.3, 0.12), 3.5, 4.2, LEAF3 if k % 2 else LEAF)
IS.prism_xz(K.octa(12.4, 7.6, 0.6, 0.6, 0.24), 0.0, 1.3, CAN)
# подвесные корзины с лозами
for x, z in ((-7.0, -8.0), (7.0, -8.0), (-7.0, 5.0), (7.0, 5.0)):
    IS.box(x - 0.04, x + 0.04, 12.0, C - 0.4, z - 0.04, z + 0.04, "5A5A5A")
    IS.prism_xz(K.ngon(x, z, 1.0, 10), 11.2, 12.0, WOOD)
    for k in range(4):
        t = 2 * math.pi * k / 4 + x
        tube(IS, [(x + 0.8 * math.cos(t), 11.6, z + 0.8 * math.sin(t)), (x + 1.2 * math.cos(t), 9.8, z + 1.2 * math.sin(t)),
                  (x + 1.0 * math.cos(t), 8.4 + 0.6 * k % 2, z + 1.0 * math.sin(t))], [0.2, 0.16, 0.1], 0.15, (0, 1, 0), LEAF2)
        IS.prism_xz(K.octa(x + 1.1 * math.cos(t), z + 1.1 * math.sin(t), 0.3, 0.3, 0.12), 9.4, 9.7, LEAF3)
# огромный терракотовый горшок-постамент с кольцом мха
pot_r = 4.0
IR.prism_xz(K.ngon(px, pz, pot_r * 0.82, 12), 0.0, 0.8, POT)
IR.prism_xz(K.ngon(px, pz, pot_r, 12), 0.8, TOP, POT2)
IQ.frame_xz(K.ngon(px, pz, pot_r + 0.05, 12), K.ngon(px, pz, pot_r - 0.6, 12), TOP - 0.05, TOP + 0.12, MOSS)
for k in range(10):  # листья у основания горшка
    t = 2 * math.pi * (k + 0.5) / 10
    if math.sin(t) > 0.6:
        continue
    b = (px + 3.6 * math.cos(t), 0.0, pz + 3.6 * math.sin(t))
    leaf(IS, b, (px + 5.6 * math.cos(t), 1.6, pz + 5.6 * math.sin(t)), 1.2, (LEAF, LEAF3)[k % 2])
B.lift_leaves(IS, FRAME2, LEAF)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, PANE)
SL.box(-FX - 1.9, FX + 1.9, -1.0, 3.6, -FZ - 1.9, FZ + 1.9, BRICK)
SL.box(-FX - 0.6, FX + 0.6, 15.4, 16.2, -FZ - 1.8, FZ + 1.8, FRAME)
SL.box(-6.0, 6.0, 16.2, 18.9, -FZ - 1.2, -FZ, PANE3)
SL.box(-17.0, -7.0, 4.0, 15.0, -FZ - 6.0, -FZ - 0.6, LEAF)
SL.box(-15.0, -8.0, 11.6, 16.4, -FZ - 8.0, -FZ - 3.4, TRAP)

F.build(mlf=1, tol=0.22, exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 3000, (0.92, 1.0, 0.9)),
                                                   ("Spot", (0, 13, -3), 3200, (1.0, 0.98, 0.92))])
