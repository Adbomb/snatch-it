"""Этаж «НЛО в банке» музея-небоскрёба (вторая партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — исследовательский комплекс, поймавший летающую тарелку (фасад v2, 2026-11-21). Снаружи — светлые
бронепанели на тёмных швах со световыми щелями, цоколь в полосах «внимание», скошенный карниз со световой линией, по углам —
восьмигранные пилоны-излучатели со шпилями; спереди в центре — огромная тарелка (наклонена к зрителю) выходит из
восьмигранного портала удержания с зажимами и энергетическими кольцами, её держат манипуляторы, из излучателя бьёт
притягивающий луч на посадочную площадку; на боках — огромные банки-капсулы с образцами (маленькие тарелки внутри),
энергомагистрали от банок к порталу, короба, ящики; на крыше радар, сзади генератор.
Откат v1 — assets/concepts/tower_batch2/backup_v1/.
Внутри — лаборатория: светлый пол из плит с разметкой, стены из панелей, капсулы с зелёной жидкостью и
пузырями, пульты с экранами, трубы и кабели; банка-экспонат на платформе сканера под аркой с кольцами, сверху —
луч-конус «притягивающего света», ящики «совершенно секретно» без надписей, тележка с инструментами.
Запуск: blender --background --factory-startup --python scripts/blender/floor_ufojar.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab, tube  # noqa: E402

METAL, METAL2, METAL3, DARK = "9AA4B0", "7E8894", "B8C0CA", "2C3038"
CONC, CONC2, HAZ, HAZ2 = "B8B2A6", "9E988C", "F2C230", "2A2A2A"
ALIEN, ALIEN2, CYAN, RED, ORANGE = "5CFF6A", "2EC24A", "5AE6F0", "FF4A3A", "FF9A3A"
SAUCER, SAUCER2, FLOOR, FLOOR2, WHITE = "C8D0DA", "8A96A6", "DDE2E8", "C4CAD2", "F4F6F8"
CRATE, CRATE2, SAND = "8A9A5A", "6E7C46", "E0C890"

F = B.Floor("UF", "UfoJar", quiet=(FLOOR, FLOOR2, CONC2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def hazard(p, axis, fixed, out, depth, a0, a1, y0, y1, step=1.2):
    """Полосы «внимание» — косые жёлто-чёрные (ступеньками)."""
    n = int((a1 - a0) // step)
    for k in range(n):
        slab(p, axis, fixed, out, depth, a0 + step * k, a0 + step * (k + 1), y0, y1, HAZ if k % 2 else HAZ2)


def ribs(p, axis, fixed, out, a0, a1, y0, y1, step, depth, color):
    for k in range(int((a1 - a0) // step) + 1):
        a = a0 + step * k
        slab(p, axis, fixed, out, depth, a - 0.18, a + 0.18, y0, y1, color)


# ══ ФАСАД v2: исследовательский комплекс с пойманной тарелкой ══════════════════════════════════════════════
PANEL, PANEL2, SEAM, GRAPH, BEAM, JAR = "D6DCE4", "B6BFCB", "3A4250", "505A6A", "9CFFB0", "6EE8B4"
B.shell_planes(F, SEAM, DARK, METAL2)
SCX, SCY, SCZ, SR = 0.0, 10.2, -FZ - 3.2, 7.8  # тарелка: центр и радиус
SS = SR / 7.2  # масштаб остальных радиусов тарелки
PR = 9.2  # портал удержания вокруг тарелки
PITCH, ROLL = math.radians(9), math.radians(-6)
ZCLIP = -FZ - 0.6  # всё, что за этой плоскостью, — в стене (в зал не попадает)


def T(lx, ly, lz):
    """Точка тарелки: крен, наклон передним краем вниз, перенос к центру; задняя часть прижата к стене."""
    x1 = lx * math.cos(ROLL) - ly * math.sin(ROLL)
    y1 = lx * math.sin(ROLL) + ly * math.cos(ROLL)
    y2 = y1 * math.cos(PITCH) + lz * math.sin(PITCH)
    z2 = -y1 * math.sin(PITCH) + lz * math.cos(PITCH)
    return (SCX + x1, SCY + y2, min(SCZ + z2, ZCLIP))


def sring(r, ly, n=24):
    r = r * SS if r != SR else r
    return [T(r * math.cos(2 * math.pi * k / n), ly, r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def arc_ring(p, cx, cz, r0, r1, y0, y1, color, n=16, zmax=-FZ - 0.05):
    """Кольцо в плане без сегментов, заходящих в стену."""
    for k in range(n):
        t0, t1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        pts = [(cx + r0 * math.cos(t0), cz + r0 * math.sin(t0)), (cx + r1 * math.cos(t0), cz + r1 * math.sin(t0)),
               (cx + r1 * math.cos(t1), cz + r1 * math.sin(t1)), (cx + r0 * math.cos(t1), cz + r0 * math.sin(t1))]
        if max(z for _, z in pts) <= zmax:
            p.prism_xz(pts, y0, y1, color)


def in_portal(a0, a1, y0, y1):
    nx, ny = min(max(SCX, a0), a1), min(max(SCY, y0), y1)
    return math.hypot(nx - SCX, ny - SCY) < PR + 0.2


# стены: светлые бронепанели на тёмных швах, световые щели, цоколь «внимание», скошенный карниз со световой линией
ROWS = ((1.9, 6.2), (6.5, 10.8), (11.1, 15.4))
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.2, SAND)  # песок пустыни
    slab(FR, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, -0.2, 1.6, GRAPH)  # цоколь
    hazard(FS, axis, fixed, out, 1.95, -half - 1.8, half + 1.8, 1.0, 1.5, 1.2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.6, 15.6, SEAM)  # швы
    cols = 7 if axis == "z" else 6
    wcol = 2 * half / cols
    for c in range(cols):
        a0, a1 = -half + wcol * c + 0.16, -half + wcol * (c + 1) - 0.16
        for r, (y0, y1) in enumerate(ROWS):
            if fi == 0 and in_portal(a0, a1, y0, y1):
                continue
            slab(FS, axis, fixed, out, 1.15, a0, a1, y0, y1, PANEL if (c + r) % 2 else PANEL2)
            if r == 1 and c % 2 == 0:  # световая щель
                slab(FG, axis, fixed, out, 1.2, a0 + 0.5, a1 - 0.5, y1 - 0.55, y1 - 0.35, ALIEN)
    B.chamfer(FS, axis, fixed, out, -half - 0.6, half + 0.6,
              [(0.0, 15.5), (1.6, 15.6), (2.3, 16.3), (2.3, 17.2), (1.7, 17.7), (0.0, 17.7)], GRAPH)
    slab(FG, axis, fixed, out, 2.36, -half - 0.6, half + 0.6, 16.55, 16.8, ALIEN)
    slab(FR, axis, fixed, out, 0.88, -half, half, 17.7, 19.0, DARK)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))

# угловые пилоны-излучатели: восьмигранные, со световыми поясами и шпилем
for sx in (-1, 1):
    for sz in (-1, 1):
        px_, pz_ = sx * (FX + 0.7), sz * (FZ + 0.7)
        FS.prism_xz(K.octa(px_, pz_, 1.9, 1.9, 0.7), -0.2, 17.9, GRAPH)
        FS.prism_xz(K.octa(px_, pz_, 2.2, 2.2, 0.8), -0.2, 1.8, SEAM)
        for y in (5.6, 11.2):
            FG.prism_xz(K.octa(px_, pz_, 2.0, 2.0, 0.74), y, y + 0.45, ALIEN)
        FS.prism_xz(K.octa(px_, pz_, 2.15, 2.15, 0.8), 15.4, 16.2, DARK)
        FS.cone([(x, 17.9, z) for x, z in K.octa(px_, pz_, 1.6, 1.6, 0.6)], (px_, 18.85, pz_), METAL3)
        FG.box(px_ - 0.22, px_ + 0.22, 18.3, 18.75, pz_ - 0.22, pz_ + 0.22, RED if sz < 0 else ALIEN)

# портал удержания: восьмигранная рама с зажимами, тёмная ниша с энергетическими кольцами
FS.frame_xy(K.ngon(SCX, SCY, PR, 8), K.ngon(SCX, SCY, PR - 1.0, 8), -FZ - 1.5, -FZ + 0.05, GRAPH)
FG.frame_xy(K.ngon(SCX, SCY, PR - 1.0, 8), K.ngon(SCX, SCY, PR - 1.35, 8), -FZ - 1.2, -FZ - 1.05, ALIEN)
FS.prism_xy(K.ngon(SCX, SCY, PR - 0.9, 8), -FZ - 0.45, -FZ + 0.05, "1E2630")
for r in (6.4, 4.4):
    FG.frame_xy(K.ngon(SCX, SCY, r, 8), K.ngon(SCX, SCY, r - 0.22, 8), -FZ - 0.52, -FZ - 0.45, ALIEN2)
for k in range(8):  # зажимы на вершинах рамы
    t = 2 * math.pi * (k + 0.5) / 8
    x, y = SCX + (PR - 0.3) * math.cos(t), SCY + (PR - 0.3) * math.sin(t)
    FS.box(x - 0.65, x + 0.65, max(y - 0.65, 1.6), min(y + 0.65, 18.9), -FZ - 1.95, -FZ - 1.4, HAZ if k % 2 else DARK)

# тарелка: нижняя чаша, обод с огнями, верхний скат, купол-кабина
F.FP.loft(sring(2.6, -1.7), sring(5.4, -0.75), SAUCER2)
F.FP.loft(sring(5.4, -0.75), sring(SR, 0.0), SAUCER2)
F.FP.loft(sring(SR, 0.0), sring(SR, 0.55), SAUCER)
F.FP.loft(sring(SR, 0.55), sring(5.0, 1.2), SAUCER)
F.FP.loft(sring(5.0, 1.2), sring(3.4, 1.65), METAL3)
FG.loft(sring(3.2, 1.65), sring(2.7, 2.8), "A6F6FF")
FG.loft(sring(2.7, 2.8), sring(1.5, 3.6), "A6F6FF")
FG.cone(sring(1.5, 3.6), T(0, 3.85, 0), "C8FBFF")
for k in range(16):  # огни по ободу
    t = 2 * math.pi * (k + 0.5) / 16
    x, y, z = T(SR * math.cos(t), 0.28, SR * math.sin(t))
    if z < ZCLIP - 0.3:
        FG.box(x - 0.28, x + 0.28, y - 0.16, y + 0.16, z - 0.28, z + 0.28, (ALIEN, CYAN, ORANGE, CYAN)[k % 4])
for k in range(8):  # огни снизу чаши
    t = 2 * math.pi * k / 8
    x, y, z = T(4.1 * SS * math.cos(t), -1.2, 4.1 * SS * math.sin(t))
    if z < ZCLIP - 0.3:
        FG.box(x - 0.3, x + 0.3, y - 0.3, y + 0.15, z - 0.3, z + 0.3, ALIEN)
FG.loft(sring(2.7, -1.72, 12), sring(1.5, -2.15, 12), ALIEN)  # излучатель луча

# захваты: два манипулятора держат обод снизу
for sx in (-1, 1):
    for start, tip in (((sx * 7.6, 3.6, -FZ - 1.3), T(sx * 7.1, -0.15, -1.5)),):
        beam(FS, start, tip, 0.9, 0.9, GRAPH)
        x, y, z = tip
        FS.box(x - 0.7, x + 0.7, y - 0.55, y + 0.55, z - 0.7, z + 0.7, HAZ)

# притягивающий луч и посадочная площадка
ex, ey, ez = T(0, -2.15, 0)
FS.prism_xz([(x, min(z, -FZ + 0.4)) for x, z in K.ngon(ex, ez, 4.6, 12)], -1.0, 1.75, GRAPH)
arc_ring(FG, ex, ez, 3.7, 4.05, 1.75, 1.85, ALIEN)
arc_ring(FS, ex, ez, 2.2, 3.7, 1.75, 1.8, METAL3)
for k in range(10):
    t = 2 * math.pi * (k + 0.25) / 10
    top = (ex + 1.4 * math.cos(t), ey + 0.1, ez + 1.4 * math.sin(t))
    bot = (ex + 3.3 * math.cos(t), 1.85, ez + 3.3 * math.sin(t))
    if max(top[2], bot[2]) < -FZ - 0.3:
        B.taper(FG, top, bot, 0.3, 0.42, BEAM)
for y, r in ((3.6, 3.0), (5.6, 2.5)):
    arc_ring(FG, ex, ez, r - 0.2, r, y, y + 0.16, BEAM)

# энергомагистрали: от банок по бокам к порталу
for sx in (-1, 1):
    FG.box(sx * (FX + 1.2), sx * (FX + 1.7), 14.55, 15.05, -FZ, -8.5, ALIEN)
    FG.box(sx * 8.4, sx * FX, 14.55, 15.05, -FZ - 1.2, -FZ - 1.7, ALIEN)
    FG.box(sx * 8.7, sx * FX, 4.35, 4.85, -FZ - 1.2, -FZ - 1.7, ALIEN2)
    for x in (10.5, 13.5):
        FS.box(sx * (x - 0.3), sx * (x + 0.3), 14.35, 15.25, -FZ - 1.1, -FZ - 1.85, GRAPH)
        FS.box(sx * (x - 0.3), sx * (x + 0.3), 4.15, 5.05, -FZ - 1.1, -FZ - 1.85, GRAPH)
    for z in (-14.0, -11.0):
        FS.box(sx * (FX + 1.1), sx * (FX + 1.8), 14.35, 15.25, z - 0.3, z + 0.3, GRAPH)

# бока: банки-капсулы с образцами (маленькие тарелки внутри), короб вентиляции, ящики
for s in (-1, 1):
    fx = s * FX
    for jz in (-8.5, 6.5):
        jx = fx + s * 1.0
        FS.prism_xz(K.octa(jx, jz, 1.9, 3.2, 0.9), 1.6, 2.9, GRAPH)
        FG.prism_xz(K.octa(jx, jz, 1.5, 2.8, 0.8), 2.9, 13.3, JAR)
        FS.prism_xz(K.octa(jx, jz, 1.9, 3.2, 0.9), 13.3, 14.3, GRAPH)
        FS.prism_xz(K.octa(jx, jz, 1.2, 2.0, 0.5), 14.3, 14.9, HAZ)
        for y in (5.6, 10.6):  # обручи
            FS.prism_xz(K.octa(jx, jz, 1.62, 2.92, 0.84), y, y + 0.3, METAL3)
        ox = jx + s * 1.52  # внешняя грань банки: силуэт тарелки внутри и пузыри
        FS.prism_zy([(jz - 1.95, 8.0), (jz - 0.9, 8.45), (jz + 0.9, 8.45), (jz + 1.95, 8.0), (jz + 1.1, 7.6), (jz - 1.1, 7.6)],
                    ox - s * 0.02, ox + s * 0.1, SAUCER2)
        FS.prism_zy([(jz - 1.95, 8.0), (jz + 1.95, 8.0), (jz + 1.95, 8.12), (jz - 1.95, 8.12)], ox, ox + s * 0.14, SAUCER)
        FG.prism_zy(K.octa(jz, 8.7, 0.62, 0.3, 0.22), ox - s * 0.02, ox + s * 0.1, "A6F6FF")
        for e in (-1.3, 0.0, 1.3):
            FG.box(ox, ox + s * 0.16, 7.95, 8.17, jz + e - 0.12, jz + e + 0.12, ALIEN)
        for k in range(4):
            bz, by = jz + (rng(s, jz, k) - 0.5) * 3.2, 4.0 + 2.2 * k + (k > 1) * 1.4
            FG.box(ox, ox + s * 0.1, by, by + 0.4, bz - 0.2, bz + 0.2, "E4FFF6")
    FS.box(fx, fx + s * 1.9, 10.0, 13.0, 10.8, 14.8, METAL2)
    for k in range(4):
        FS.box(fx + s * 1.9, fx + s * 2.0, 10.4 + 0.65 * k, 10.7 + 0.65 * k, 11.1, 14.5, DARK)
    for k, (z, w, h) in enumerate(((-13.2, 1.3, 1.5), (-1.2, 1.1, 1.2), (12.4, 1.4, 1.5))):
        FS.box(fx, fx + s * 2.4, 1.6, 1.6 + h, z - w, z + w, CRATE if k % 2 else CRATE2)
        FS.box(fx + s * 2.4, fx + s * 2.5, 1.9, 1.3 + h, z - w + 0.2, z + w - 0.2, CRATE2 if k % 2 else CRATE)
# крыша: радар
FS.box(-12.6, -11.4, C + 0.05, 18.4, 8.8, 10.0, DARK)  # опора радара — над потолком зала
FS.loft([(-14.2, 18.8, 8.0), (-9.8, 18.4, 8.0), (-9.8, 18.4, 10.8), (-14.2, 18.8, 10.8)],
        [(-14.0, 18.95, 8.2), (-10.0, 18.6, 8.2), (-10.0, 18.6, 10.6), (-14.0, 18.95, 10.6)], WHITE)
# тыл: генератор с кабелями
FS.box(-5.0, 5.0, -0.2, 4.6, FZ, FZ + 2.6, HAZ)
FS.box(-4.6, 4.6, 4.6, 5.0, FZ + 0.2, FZ + 2.4, DARK)
for k in range(6):
    FS.box(-4.2 + 1.5 * k, -3.6 + 1.5 * k, 1.0, 3.8, FZ + 2.6, FZ + 2.7, DARK)
for s in (-1, 1):
    tube(FS, [(s * 4.0, 3.0, FZ + 2.6), (s * 7.0, 1.2, FZ + 2.4), (s * 10.0, 6.0, FZ + 1.3), (s * 12.0, 11.0, FZ + 1.3)],
         [0.45] * 4, 0.45, (0, 0, 1), DARK)

# ══ ИНТЕРЬЕР: лаборатория ═════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.3
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), FLOOR)
for i in range(-4, 5):  # швы плит
    IS.box(-W, W, 0.02, 0.04, 3.4 * i - 0.05, 3.4 * i + 0.05, FLOOR2)
    IS.box(3.6 * i - 0.05, 3.6 * i + 0.05, 0.02, 0.04, ZF, ZB, FLOOR2)
for k in range(12):  # жёлтая разметка вокруг платформы
    t = 2 * math.pi * k / 12
    x, z = PED[0] + 6.4 * math.cos(t), PED[1] + 6.4 * math.sin(t)
    IS.box(x - 0.35, x + 0.35, 0.02, 0.06, z - 0.35, z + 0.35, HAZ)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.0, METAL2)
        hazard(IS, axis, fixed, out, 0.95, a0, a1, 0.2, 0.6, 1.0)
        for k in range(int((a1 - a0) // 3.0)):  # панели стены
            b0 = a0 + 3.0 * k
            slab(IR, axis, fixed, out, 0.88, b0 + 0.06, b0 + 2.94, 1.0, 10.6, WHITE if k % 2 else METAL3)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 12.0, METAL3)
    slab(IR, axis, fixed, out, 0.7, -half, half, 1.0, 12.0, METAL2)
    slab(IS, axis, fixed, out, 1.2, -half, half, 10.6, 11.0, DARK)
    slab(IG, axis, fixed, out, 1.25, -half, half, 10.75, 10.85, ALIEN)
    slab(IR, axis, fixed, out, 0.88, -half, half, 11.0, C, METAL)
    for y in (13.4, 14.4):  # трубы под потолком
        slab(IS, axis, fixed, out, 1.6, -half, half, y, y + 0.5, METAL2 if y < 14 else "5A6A80")
# капсулы с зелёной жидкостью вдоль боковых стен
for s in (-1, 1):
    for z in (-12.0, -6.5, 6.5):
        x = s * (W - 2.4)
        IS.prism_xz(K.octa(x, z, 1.6, 1.6, 0.66), 0.0, 1.2, METAL2)
        IG.prism_xz(K.octa(x, z, 1.3, 1.3, 0.54), 1.2, 8.0, ALIEN2)
        IS.prism_xz(K.octa(x, z, 1.6, 1.6, 0.66), 8.0, 9.0, METAL2)
        IS.box(x - 0.2, x + 0.2, 9.0, 13.4, z - 0.2, z + 0.2, DARK)
        for k in range(5):
            bx, by, bz = x + (rng(s, z, k) - 0.5) * 1.4, 2.0 + 1.2 * k, z + (rng(z, k, s) - 0.5) * 1.4
            IG.box(bx - 0.15, bx + 0.15, by, by + 0.3, bz - 0.15, bz + 0.15, "D8FFE0")
# пульты с экранами у передней стены
for x in (-10.0, -4.0, 4.0, 10.0):
    IS.box(x - 2.4, x + 2.4, 0.0, 2.6, ZF + 0.9, ZF + 2.6, METAL2)
    IS.prism_zy([(ZF + 2.6, 2.6), (ZF + 3.4, 2.6), (ZF + 3.4, 2.9), (ZF + 2.0, 3.6)], x - 2.4, x + 2.4, DARK)
    for k in range(5):
        IG.box(x - 2.0 + 0.85 * k, x - 1.6 + 0.85 * k, 3.05, 3.2, ZF + 2.7, ZF + 3.0, (ALIEN, CYAN, RED, ORANGE, ALIEN)[k])
    IS.box(x - 2.2, x + 2.2, 3.6, 7.0, ZF + 0.95, ZF + 1.2, DARK)
    IG.box(x - 1.95, x + 1.95, 3.85, 6.75, ZF + 1.2, ZF + 1.25, ("103820", "102838")[int(x > 0)])
    for k in range(4):  # кривые на экранах
        IG.box(x - 1.7, x - 1.7 + 0.8 + 0.7 * k, 4.3 + 0.6 * k, 4.42 + 0.6 * k, ZF + 1.25, ZF + 1.3, ALIEN if x < 0 else CYAN)
# платформа сканера и арка с кольцами
px, pz = PED
IR.prism_xz(K.octa(px, pz, 4.2, 4.2, 1.7), 0.0, 0.8, METAL2)
IR.prism_xz(K.octa(px, pz, 3.4, 3.4, 1.4), 0.8, TOP, WHITE)
IG.frame_xz(K.octa(px, pz, 4.4, 4.4, 1.8), K.octa(px, pz, 4.2, 4.2, 1.7), 0.5, 0.65, ALIEN)
IG.frame_xz(K.octa(px, pz, 3.6, 3.6, 1.5), K.octa(px, pz, 3.4, 3.4, 1.4), TOP - 0.1, TOP + 0.02, CYAN)
for s in (-1, 1):
    IS.box(px + s * 5.2 - 0.5, px + s * 5.2 + 0.5, 0.0, 13.0, pz - 0.5, pz + 0.5, METAL2)
    IG.box(px + s * 4.65, px + s * 4.7, 1.0, 12.0, pz - 0.3, pz + 0.3, ALIEN)
IS.box(px - 5.7, px + 5.7, 13.0, 14.0, pz - 0.6, pz + 0.6, METAL2)
for y in (5.0, 9.5):  # кольца сканера
    IG.frame_xz(K.octa(px, pz, 3.6, 3.6, 1.5), K.octa(px, pz, 3.3, 3.3, 1.35), y, y + 0.2, CYAN)
# луч «притягивающего света» с потолка
IS.prism_xz(K.octa(px, pz, 2.4, 2.4, 1.0), C - 0.6, C, DARK)
IG.frame_xz(K.octa(px, pz, 2.2, 2.2, 0.9), K.octa(px, pz, 1.6, 1.6, 0.66), C - 0.66, C - 0.6, ALIEN)
# ящики и тележка
for x, z, w, h in ((-12.0, 2.5, 1.5, 1.6), (-12.3, 4.6, 1.0, 1.0), (12.0, 1.5, 1.3, 2.4), (11.6, 11.5, 1.5, 1.6)):
    IS.box(x - w, x + w, 0.0, h, z - w, z + w, CRATE)
    IS.box(x - w - 0.05, x + w + 0.05, h * 0.45, h * 0.55, z - w - 0.05, z + w + 0.05, CRATE2)
IS.box(-9.6, -6.4, 2.0, 2.2, 8.0, 10.0, METAL3)
IS.box(-9.6, -6.4, 0.8, 1.0, 8.0, 10.0, METAL3)
for x in (-9.4, -6.6):
    for z in (8.2, 9.8):
        IS.box(x - 0.08, x + 0.08, 0.2, 2.2, z - 0.08, z + 0.08, METAL2)
IS.box(-9.2, -8.0, 2.2, 2.8, 8.4, 9.0, RED)
IS.box(-7.6, -6.8, 2.2, 3.4, 9.0, 9.6, HAZ)
B.lift_leaves(IS, METAL2, HAZ)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, PANEL2)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.2, -FZ - 2.9, FZ + 2.9, SAND)
SL.box(-FX - 1.9, FX + 1.9, -0.2, 1.6, -FZ - 1.9, FZ + 1.9, GRAPH)
SL.box(-FX - 2.3, FX + 2.3, 15.6, 17.7, -FZ - 2.3, FZ + 2.3, GRAPH)
SL.box(-PR + 0.6, PR - 0.6, SCY - PR + 0.8, SCY + PR - 0.8, -FZ - 1.5, -FZ, "1E2630")
SL.prism_xz(K.ngon(SCX, SCZ - 0.6, SR, 8), SCY - 1.4, SCY + 0.5, SAUCER)
SL.box(-2.6, 2.6, SCY + 0.5, SCY + 2.8, SCZ - 2.6, SCZ + 1.6, "A6F6FF")
for s in (-1, 1):
    for jz in (-8.5, 6.5):
        SL.box(s * FX, s * (FX + 2.5), 1.6, 14.3, jz - 2.8, jz + 2.8, JAR)

F.build(mlf=1, exhibit=(PED[0], TOP, PED[1], 3.0), lamps=[("Hall", (0, 14, 6), 3000, (0.9, 1.0, 0.95)),
                                                   ("Spot", (0, 13, -3), 3200, (0.9, 1.0, 0.9))])
