"""Этаж «Портативный дракон» музея-небоскрёба (третья партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — замок, в котором поселился дракон. Снаружи — донжон из грубого серого камня с откосом цоколя,
навесными бойницами (машикулями) и зубцами, по углам — круглые башни с зубцами и флажками; спереди — арка ворот с
железной решёткой и опущенным подъёмным мостом на цепях; зелёный дракон обвил правую переднюю
башню: голова в профиле над зубцами (один глаз), крыло раскинуто по фасаду, хвост с шипами уходит по правому боку;
слева — следы когтей и факелы, сзади — деревянный кран с мешками добычи. Внутри — сокровищница дракона: плиты пола,
каменные стены с круглыми колоннами и рёбрами свода, факелы, следы когтей; горы золотых монет, сундуки,
кубки, мечи в золоте, круглые щиты на стенах, гнездо с тремя яйцами; экспонат — на каменном помосте среди золота.
Запуск: blender --background --factory-startup --python scripts/blender/floor_dragon.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab, taper, tube  # noqa: E402

STONE, STONE2, STONE3, DARK, SOOT = "8C8C94", "76767E", "A2A2AA", "3A3A42", "2E2A2A"
WOOD, WOOD2, IRON, RED, CLOTH = "7A5230", "5A3A20", "3A3A44", "C2463A", "E8D8B0"
GREEN, GREEN2, GREEN3, HORN, EYE = "3FBF5A", "2E8A44", "8ADF6A", "EDE3C8", "FFD040"
GOLD, GOLD2, GOLD3, FIRE, FLAME = "F2C230", "D9A21A", "FFE07A", "FF8A2A", "FFC24A"
EGG1, EGG2, EGG3, STRAW = "4FD8B0", "8E6AD8", "E87A4A", "C8A060"

F = B.Floor("PD", "PocketDragon", quiet=(STONE2, CLOTH), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def ring_pts(cx, cz, r, n=12, off=0.5):
    return [(cx + r * math.cos(2 * math.pi * (k + off) / n), cz + r * math.sin(2 * math.pi * (k + off) / n)) for k in range(n)]


def coin_hill(p, cx, cz, r, h, steps=4):
    """Гора монет: уступы-восьмиугольники, сверху — россыпь."""
    for k in range(steps):
        rr = r * (1 - k / steps)
        p.prism_xz(K.octa(cx, cz, rr, rr * 0.85, rr * 0.4), h * k / steps, h * (k + 1) / steps, GOLD if k % 2 else GOLD2)
    for k in range(5):
        t = 2 * math.pi * k / 5 + r
        x, z = cx + r * 0.8 * math.cos(t), cz + r * 0.7 * math.sin(t)
        p.prism_xz(K.octa(x, z, 0.3, 0.3, 0.12), 0.0, 0.12, GOLD3)


def chest(p, x, z, ang_open=True, w=1.4):
    p.box(x - w, x + w, 0.0, 1.3, z - 0.8, z + 0.8, WOOD)
    for e in (-0.7, 0.7):
        p.box(x + e * w - 0.12, x + e * w + 0.12, 0.0, 1.35, z - 0.85, z + 0.85, GOLD2)
    p.box(x - w + 0.1, x + w - 0.1, 1.15, 1.3, z - 0.7, z + 0.7, GOLD)
    if ang_open:  # открытая крышка
        p.box(x - w, x + w, 1.3, 2.7, z + 0.7, z + 0.95, WOOD2)
    else:
        p.box(x - w, x + w, 1.3, 1.8, z - 0.8, z + 0.8, WOOD2)


# ══ ФАСАД: замковый донжон с драконом ═════════════════════════════════════════════════════════════════════════
B.shell_planes(F, STONE2, STONE2, WOOD2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 8.88 if fi == 0 else 2.88, -half - 2.88, half + 2.88, -1.0, -0.2, STONE2)  # мощение (спереди — двор под мостом)
    B.chamfer(FR, axis, fixed, out, -half - 2.0, half + 2.0, [(0.0, -0.2), (2.0, -0.2), (0.9, 2.8), (0.0, 2.8)], STONE)
    for r, (y0, y1) in enumerate(((2.8, 5), (5, 7), (7, 9), (9, 11), (11, 13), (13, 15))):  # грубая кладка
        a, k = -half - (r % 2), 0
        while a < half:
            w = 2 + int(rng(fi, r, k) * 3)
            a1 = min(a + w, half)
            if a1 - max(a, -half) > 0.4:
                slab(FR, axis, fixed, out, 0.88, max(a, -half) + 0.05, a1 - 0.05, y0 + 0.05, y1 - 0.05,
                     (STONE, STONE2, STONE3, STONE)[int(rng(fi, r, k, 3) * 4)])
            a, k = a1, k + 1
    slab(FR, axis, fixed, out, 1.88, -half, half, 15.0, 16.0, STONE3)  # пояс машикулей
    for k in range(int(2 * half // 2.0)):
        a = -half + 1.0 + 2.0 * k
        slab(FS, axis, fixed, out, 1.85, a - 0.45, a + 0.45, 14.2, 15.0, STONE2)  # консоли
    slab(FR, axis, fixed, out, 1.88, -half, half, 16.0, 17.0, STONE)
    for k in range(int(2 * half // 2.4)):  # зубцы
        a = -half + 1.2 + 2.4 * k
        slab(FR, axis, fixed, out, 1.88, a - 0.7, a + 0.7, 17.0, 18.8, STONE3 if k % 2 else STONE)
    for k in range(4):  # бойницы
        a = -half + (k + 0.5) * 2 * half / 4
        if fi == 0 and abs(a) < 7:
            continue
        slab(FS, axis, fixed, out, 0.95, a - 0.22, a + 0.22, 8.0, 11.0, SOOT)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# угловые башни: круглые, с зубцами и флажками
for sx in (-1, 1):
    for sz in (-1, 1):
        cx, cz = sx * (FX + 1.2), sz * (FZ + 1.2)
        FR.prism_xz(ring_pts(cx, cz, 3.2), -0.2, 16.0, STONE)
        FS.prism_xz(ring_pts(cx, cz, 3.7), -0.2, 1.4, STONE2)
        FS.prism_xz(ring_pts(cx, cz, 3.6), 16.0, 17.0, STONE3)
        for k in range(8):
            t = 2 * math.pi * k / 8
            x, z = cx + 3.25 * math.cos(t), cz + 3.25 * math.sin(t)
            FS.prism_xz(K.octa(x, z, 0.55, 0.55, 0.2), 17.0, 18.6, STONE3)
        for k in range(3):
            t = 2 * math.pi * (k * 3 + 1.5) / 12 + (0.5 if sz > 0 else 3.6)
            x, z = cx + 3.24 * math.cos(t), cz + 3.24 * math.sin(t)
            FS.box(x - 0.2, x + 0.2, 7.0 + 3.0 * k, 9.0 + 3.0 * k, z - 0.2, z + 0.2, SOOT)
        if not (sx > 0 and sz < 0):  # флажок (у правой передней башни сидит дракон)
            FS.box(cx - 0.08, cx + 0.08, 17.0, 18.95, cz - 0.08, cz + 0.08, IRON)
            FS.prism_xy([(cx + 0.08, 18.9), (cx + 1.9, 18.4), (cx + 0.08, 17.9)], cz - 0.04, cz + 0.04, RED)
# ворота: арка, железная решётка, подъёмный мост на цепях
ARCH = [(-4.4, 1.0)] + [(-4.4 + 4.4 * (1 - math.cos(math.pi * k / 8)), 8.0 + 3.6 * math.sin(math.pi * k / 8)) for k in range(9)] + \
       [(4.4, 1.0)]
OUTER = [(-6.0, 1.0)] + [(-6.0 + 6.0 * (1 - math.cos(math.pi * k / 8)), 8.0 + 5.0 * math.sin(math.pi * k / 8)) for k in range(9)] + \
        [(6.0, 1.0)]
FR.frame_xy(OUTER, ARCH, -FZ - 1.9, -FZ + 0.05, STONE3)
FS.prism_xy(ARCH, -FZ - 0.4, -FZ + 0.05, "1E1A18")
for k in range(9):  # решётка
    x = -3.6 + 0.9 * k
    top = 8.0 + 3.6 * math.sin(math.acos(max(-1.0, min(1.0, x / 4.4))))
    FS.box(x - 0.12, x + 0.12, 1.0, top - 0.1, -FZ - 1.2, -FZ - 0.95, IRON)
    FS.box(x - 0.2, x + 0.2, 0.7, 1.0, -FZ - 1.25, -FZ - 0.9, IRON)
for y in (3.0, 5.2, 7.4, 9.6):
    w = 4.3 if y < 8 else 3.6
    FS.box(-w, w, y - 0.1, y + 0.1, -FZ - 1.3, -FZ - 1.15, IRON)
FS.loft([(-4.0, 1.0, -FZ - 1.9), (4.0, 1.0, -FZ - 1.9), (4.0, 1.35, -FZ - 1.9), (-4.0, 1.35, -FZ - 1.9)],
        [(-4.0, -0.1, -FZ - 8.0), (4.0, -0.1, -FZ - 8.0), (4.0, 0.25, -FZ - 8.0), (-4.0, 0.25, -FZ - 8.0)], WOOD)
for k in range(6):  # доски моста
    t = (k + 0.5) / 6
    y, z = 1.35 - 1.1 * t, -FZ - 1.9 - 6.1 * t
    FS.box(-4.1, 4.1, y - 0.05, y + 0.05, z - 0.05, z + 0.05, WOOD2)
for x in (-3.6, 3.6):
    beam(FS, (x * 1.4, 10.4, -FZ - 1.9), (x, 0.3, -FZ - 7.8), 0.16, 0.16, IRON)
# дракон: обвил правую переднюю башню, голова в профиле над зубцами, крыло по фасаду, хвост по боку
tcx, tcz = FX + 1.2, -FZ - 1.2
coil = []
for k in range(14):  # тело — спираль вокруг башни снизу вверх
    t = math.radians(-40 + 32 * k)
    coil.append((tcx + 3.9 * math.cos(t), 2.6 + 1.05 * k, tcz + 3.9 * math.sin(t)))
tube(FS, coil, [1.7 + 0.25 * math.sin(k * 0.6) for k in range(14)], 1.6, (0, 1, 0), GREEN)
for k in range(1, 13):  # шипы по хребту
    x, y, z = coil[k]
    FS.cone([(x - 0.3, y + 0.75, z - 0.3), (x + 0.3, y + 0.75, z - 0.3), (x + 0.3, y + 0.75, z + 0.3), (x - 0.3, y + 0.75, z + 0.3)],
            (x, y + 1.6, z), HORN)
hx, hy, hz = tcx - 3.8, 17.6, tcz - 1.0
FS.prism_xy([(hx + 3.0, hy - 1.6), (hx + 0.6, hy - 1.2), (hx - 2.6, hy - 0.9), (hx - 3.4, hy - 0.3), (hx - 2.8, hy + 0.3),
             (hx - 0.6, hy + 0.5), (hx + 0.8, hy + 1.3), (hx + 2.6, hy + 1.0), (hx + 3.4, hy - 0.4)], hz - 0.8, hz + 0.8, GREEN)
FS.prism_xy([(hx - 3.2, hy - 0.5), (hx - 0.4, hy - 0.8), (hx + 1.0, hy - 1.4), (hx - 0.6, hy - 1.3), (hx - 2.8, hy - 1.0)],
            hz - 0.7, hz + 0.7, GREEN3)  # нижняя челюсть светлее
for dx in (0.6, 1.6):  # рога назад
    taper(FS, (hx + dx, hy + 0.9, hz), (hx + dx + 1.6, hy + 1.35, hz), 0.5, 0.1, HORN)
FG.box(hx - 0.3, hx + 0.3, hy + 0.05, hy + 0.4, hz - 0.85, hz - 0.8, EYE)  # один глаз, со стороны фасада
FS.box(hx - 2.9, hx - 2.6, hy - 0.05, hy + 0.15, hz - 0.85, hz - 0.8, "1A2A1A")  # ноздря
WING = [(16.0, 14.8), (12.0, 16.6), (8.0, 17.4), (4.6, 16.0), (6.4, 13.6), (5.4, 11.6), (8.6, 12.4), (8.4, 10.0),
        (11.4, 11.4), (12.0, 9.2), (14.6, 11.0)]
FS.prism_xy(WING, -FZ - 1.15, -FZ - 0.95, GREEN2)
for tip in ((8.0, 17.4), (5.4, 11.6), (8.4, 10.0), (12.0, 9.2)):  # пальцы крыла
    beam(FS, (16.0, 14.8, -FZ - 1.25), (tip[0], tip[1], -FZ - 1.25), 0.3, 0.3, GREEN, up=(0, 0, 1))
tail = [(FX + 3.6, 2.4, -FZ + 2.0), (FX + 3.0, 1.6, -6.0), (FX + 2.6, 2.6, 2.0), (FX + 2.2, 1.4, 9.0), (FX + 2.0, 2.2, 13.0)]
tube(FS, tail, [1.4, 1.2, 0.9, 0.6, 0.3], 1.0, (1, 0, 0), GREEN)
for k in range(4):
    x, y, z = tail[k]
    FS.cone([(x - 0.25, y + 0.45, z - 0.3), (x + 0.25, y + 0.45, z - 0.3), (x + 0.25, y + 0.45, z + 0.3),
             (x - 0.25, y + 0.45, z + 0.3)], (x, y + 1.3, z), HORN)
FS.prism_zy([(13.0, 1.6), (15.0, 2.4), (13.4, 3.6)], FX + 1.8, FX + 2.2, GREEN2)  # пика хвоста
# слева: следы когтей и факелы
for k in range(3):
    beam(FS, (-FX - 0.93, 12.5 - 0.3 * k, -6.0 + 1.0 * k), (-FX - 0.93, 6.0 - 0.3 * k, -3.0 + 1.0 * k), 0.3, 0.1, SOOT,
         up=(1, 0, 0))
for s in (-1, 1):
    for z in (-10.0, 10.0):
        fx = s * FX
        FS.box(fx + s * 0.9, fx + s * 1.6, 7.6, 7.9, z - 0.2, z + 0.2, IRON)
        FS.prism_xz(K.octa(fx + s * 1.5, z, 0.3, 0.3, 0.12), 7.9, 8.6, WOOD2)
        FG.prism_xz(K.octa(fx + s * 1.5, z, 0.26, 0.26, 0.1), 8.6, 9.4, FIRE)
        FG.prism_xz(K.octa(fx + s * 1.5, z, 0.13, 0.13, 0.05), 9.4, 9.9, FLAME)
# тыл: деревянный кран с мешками добычи
FS.box(-6.2, -5.6, -0.2, 17.0, FZ + 1.0, FZ + 1.6, WOOD)
beam(FS, (-5.9, 16.4, FZ + 1.3), (-1.0, 16.4, FZ + 5.0), 0.5, 0.5, WOOD2)
beam(FS, (-5.9, 12.0, FZ + 1.3), (-2.6, 16.2, FZ + 3.8), 0.3, 0.3, WOOD2)
FS.box(-1.05, -0.95, 9.0, 16.2, FZ + 4.95, FZ + 5.05, "B89060")
for k, (x, y) in enumerate(((-1.0, 8.0), (2.0, 0.6), (3.6, 0.6), (2.8, 1.8))):
    FS.prism_xz(K.octa(x, FZ + 5.0 if k == 0 else FZ + 3.2, 0.8, 0.8, 0.32), y - 0.4 if k == 0 else y - 0.6,
                y + 1.0, CLOTH)
    FS.prism_xz(K.octa(x, FZ + 5.0 if k == 0 else FZ + 3.2, 0.35, 0.35, 0.14), y + 1.0, y + 1.3, GOLD)

# ══ ИНТЕРЬЕР: сокровищница дракона ════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.4
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), STONE2)
for i in range(-8, 9):  # швы плит пола
    IS.box(2.0 * i - 0.05, 2.0 * i + 0.05, 0.02, 0.05, ZF, ZB, DARK)
for j in range(-7, 8):
    IS.box(-W, W, 0.02, 0.05, 2.1 * j - 0.05, 2.1 * j + 0.05, DARK)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    lift = idx == 3
    for r, (y0, y1) in enumerate(((0, 2), (2, 4), (4, 6), (6, 8), (8, 10), (10, 12))):
        a, k = -half - (r % 2) * 1.5, 0
        while a < half:
            w = 3 + int(rng(idx, r, k) * 3)
            b0, b1 = max(a, -half), min(a + w, half)
            if lift and y0 < 11 and b1 > -DOOR[0] - 0.6 and b0 < DOOR[0] + 0.6:
                parts = [(b0, -DOOR[0] - 0.6), (DOOR[0] + 0.6, b1)]
            else:
                parts = [(b0, b1)]
            for c0, c1 in parts:
                if c1 - c0 > 0.4:
                    slab(IR, axis, fixed, out, 0.88, c0 + 0.05, c1 - 0.05, y0 + 0.05, y1 - 0.05,
                         (STONE, STONE2, STONE3, STONE)[int(rng(idx, r, k, 7) * 4)])
            a, k = a + w, k + 1
    slab(IQ, axis, fixed, out, 0.7, -half, half, 0.0, C, DARK)
    if lift:
        slab(IR, axis, fixed, out, 1.88, -5.0, 5.0, 11.0, 12.5, STONE3)
    slab(IR, axis, fixed, out, 1.88, -half, half, 12.0, 13.0, STONE3)  # карниз
    slab(IR, axis, fixed, out, 0.88, -half, half, 13.0, C, STONE2)
    for k, a in enumerate((-11.0, 0.0, 11.0)):  # факелы
        if lift and abs(a) < 5:
            continue
        nx, nz = (fixed + out * 1.4, a) if axis == "x" else (a, fixed + out * 1.4)
        slab(IS, axis, fixed, out, 1.6, a - 0.2, a + 0.2, 7.4, 7.7, IRON)
        IS.prism_xz(K.octa(nx, nz, 0.3, 0.3, 0.12), 7.7, 8.4, WOOD2)
        IG.prism_xz(K.octa(nx, nz, 0.26, 0.26, 0.1), 8.4, 9.2, FIRE)
        IG.prism_xz(K.octa(nx, nz, 0.13, 0.13, 0.05), 9.2, 9.7, FLAME)
    for k, a in enumerate((-6.0, 6.0)):  # круглые щиты
        if lift:
            continue
        prism = IS.prism_xy if axis == "z" else IS.prism_zy
        d0, d1 = sorted((fixed + out * 0.9, fixed + out * 1.2))
        prism(K.octa(a, 8.6, 1.4, 1.4, 0.58), d0, d1, (RED, "3060B0")[k])
        d2, d3 = sorted((fixed + out * 1.2, fixed + out * 1.3))
        prism(K.octa(a, 8.6, 0.5, 0.5, 0.2), d2, d3, GOLD)
        prism([(a - 1.3, 8.45), (a + 1.3, 8.45), (a + 1.3, 8.75), (a - 1.3, 8.75)], d2, d3, GOLD2)
# колонны и рёбра свода
for x, z in ((-12.0, -10.0), (12.0, -10.0), (-12.0, 4.0), (12.0, 4.0)):
    IS.prism_xz(ring_pts(x, z, 1.5), 0.0, 1.0, STONE2)
    IR.prism_xz(ring_pts(x, z, 1.2), 1.0, 12.0, STONE)
    IS.prism_xz(ring_pts(x, z, 1.6), 12.0, 12.8, STONE3)
for z in (-10.0, 4.0):
    tube(IS, [(-12.0, 12.8, z), (-6.0, 16.6, z), (0.0, 17.6, z), (6.0, 16.6, z), (12.0, 12.8, z)], [0.9] * 5, 0.9, (0, 0, 1),
         STONE3)
for x in (-12.0, 12.0):
    tube(IS, [(x, 12.8, -10.0), (x, 15.4, -3.0), (x, 12.8, 4.0)], [0.9] * 3, 0.9, (1, 0, 0), STONE3)
# следы когтей на передней стене
for k in range(3):
    beam(IS, (-9.0 + 0.9 * k, 10.5, ZF + 0.93), (-11.0 + 0.9 * k, 4.5, ZF + 0.93), 0.32, 0.1, SOOT, up=(0, 0, 1))
# золото: горы монет, сундуки, кубки, мечи
px, pz = PED
for cx, cz, r, h in ((-9.5, -12.0, 3.2, 2.4), (10.0, -12.5, 3.6, 2.8), (-13.0, -3.0, 2.2, 1.4), (13.2, -2.0, 2.4, 1.6),
                     (-5.6, -9.0, 1.8, 1.0), (5.8, -9.4, 1.8, 1.1)):
    coin_hill(IS, cx, cz, r, h)
chest(IS, -12.6, 8.5)
chest(IS, 12.4, 9.5, False)
chest(IS, 9.2, -6.0, True, 1.1)
for x, z, t in ((-10.0, -11.0, 0.3), (10.6, -12.0, -0.4), (-6.0, -8.6, 0.6)):  # мечи, воткнутые в золото
    IS.box(x - 0.1, x + 0.1, 1.0, 4.4, z - 0.04, z + 0.04, "D8DCE4")
    IS.box(x - 0.6, x + 0.6, 3.0, 3.25, z - 0.12, z + 0.12, GOLD2)
    IS.box(x - 0.12, x + 0.12, 3.25, 4.2, z - 0.12, z + 0.12, WOOD2)
for x, z in ((-12.2, 1.0), (12.4, 0.8), (-8.0, 10.0)):  # кубки
    IS.prism_xz(K.octa(x, z, 0.35, 0.35, 0.14), 0.0, 0.15, GOLD2)
    IS.box(x - 0.08, x + 0.08, 0.15, 0.7, z - 0.08, z + 0.08, GOLD2)
    IS.prism_xz(K.octa(x, z, 0.4, 0.4, 0.16), 0.7, 1.3, GOLD)
# гнездо с тремя яйцами
for k in range(10):
    t0 = 2 * math.pi * k / 10
    x, z = -8.6 + 1.7 * math.cos(t0), 2.0 + 1.7 * math.sin(t0)
    beam(IS, (x, 0.3, z), (-8.6 + 1.7 * math.cos(t0 + 0.9), 0.55, 2.0 + 1.7 * math.sin(t0 + 0.9)), 0.35, 0.3, STRAW)
for k, (dx, dz, col) in enumerate(((-0.5, -0.4, EGG1), (0.6, -0.2, EGG2), (0.0, 0.6, EGG3))):
    x, z = -8.6 + dx, 2.0 + dz
    IS.prism_xz(K.octa(x, z, 0.5, 0.5, 0.2), 0.2, 0.6, col)
    IS.prism_xz(K.octa(x, z, 0.62, 0.62, 0.25), 0.6, 1.3, col)
    IS.prism_xz(K.octa(x, z, 0.42, 0.42, 0.17), 1.3, 1.8, col)
    IS.prism_xz(K.octa(x + 0.1, z, 0.12, 0.3, 0.05), 1.0, 1.5, GOLD3)
# помост среди золота
IR.prism_xz(K.octa(px, pz, 4.4, 4.4, 1.8), 0.0, 0.7, STONE)
IR.prism_xz(K.octa(px, pz, 3.6, 3.6, 1.5), 0.7, TOP, STONE3)
IS.frame_xz(K.octa(px, pz, 3.7, 3.7, 1.55), K.octa(px, pz, 3.6, 3.6, 1.5), TOP - 0.2, TOP + 0.02, GOLD)
for k in range(8):  # монеты у подножия помоста
    t = 2 * math.pi * (k + 0.5) / 8
    x, z = px + 5.0 * math.cos(t), pz + 5.0 * math.sin(t)
    if z > pz + 3.5:
        continue
    IS.prism_xz(K.octa(x, z, 1.1, 0.9, 0.4), 0.0, 0.35, GOLD2)
    IS.prism_xz(K.octa(x, z, 0.6, 0.5, 0.2), 0.35, 0.6, GOLD)
B.lift_leaves(IS, IRON, GOLD2)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, STONE)
SL.box(-FX - 2.0, FX + 2.0, -1.0, 2.8, -FZ - 2.0, FZ + 2.0, STONE2)
SL.box(-FX - 1.9, FX + 1.9, 15.0, 18.6, -FZ - 1.9, FZ + 1.9, STONE3)
for sx in (-1, 1):
    for sz in (-1, 1):
        SL.prism_xz(K.octa(sx * (FX + 1.2), sz * (FZ + 1.2), 3.2, 3.2, 1.3), -0.2, 18.4, STONE)
SL.box(-4.4, 4.4, 1.0, 10.0, -FZ - 0.5, -FZ, "1E1A18")
SL.box(FX - 2.0, FX + 5.2, 2.6, 17.0, -FZ - 5.2, -FZ + 2.0, GREEN)
SL.box(4.6, 16.0, 9.2, 17.4, -FZ - 1.2, -FZ - 0.9, GREEN2)

F.build(exhibit=(PED[0], TOP, PED[1], 3.4), lamps=[("Hall", (0, 14, 6), 2600, (1.0, 0.85, 0.65)),
                                                   ("Spot", (0, 13, -3), 3200, (1.0, 0.95, 0.85))])
