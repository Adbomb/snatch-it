"""Этаж «Кристальный динозавр» музея-небоскрёба (вторая партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — расколотая жеода. Снаружи — грубая тёмная скала: гранёные глыбы трёх тонов с уступами, по ним —
светящиеся трещины-жилы; на углах и по верхнему краю растут друзы острых кристаллов (аметист, бирюза, розовый
кварц); спереди скала расколота — овальная пасть жеоды обрамлена кольцом кристаллов, внутри светится лиловое
нутро; по бокам — окаменелые следы трёхпалых лап, сзади — малые друзы.
Внутри — кристальная пещера: тёмные стены с гранёными выступами, из стен, пола и потолка растут кристаллы
(сверху — кристаллы-сосульки), светящиеся бирюзовые озерца, тропа из светящихся камней, на полу — светящиеся
следы динозавра; экспонат стоит на кристаллическом постаменте, окружённом короной из кристаллов.
Запуск: blender --background --factory-startup --python scripts/blender/floor_crystal.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, rng, slab, taper  # noqa: E402

ROCK, ROCK2, ROCK3, ROCKD = "4A4060", "3A3250", "5E5478", "241E34"
AME, AME2, CYAN, CYAN2, PINK, WHITE = "A66CFF", "7A3FE0", "4FD8F0", "2AA8D0", "FF6FD0", "E8F8FF"
GLOW, GLOW2 = "C49CFF", "8AF0FF"

F = B.Floor("CD", "CrystalDino", quiet=(ROCK2, ROCKD), bevel_min=1.0, keep_arch=True)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL
COLORS = (AME, CYAN, PINK, AME2, CYAN2)


def crystal(p, base, direction, length, width, color, cap=None):
    """Кристалл: призма-шестигранник (как сужающийся брус) и острая верхушка."""
    bx, by, bz = base
    dx, dy, dz = direction
    n = math.sqrt(dx * dx + dy * dy + dz * dz)
    dx, dy, dz = dx / n, dy / n, dz / n
    mid = (bx + dx * length * 0.72, by + dy * length * 0.72, bz + dz * length * 0.72)
    tip = (bx + dx * length, by + dy * length, bz + dz * length)
    taper(p, base, mid, width, width * 0.92, color)
    taper(p, mid, tip, width * 0.92, 0.04, cap or color)


def druse(p, center, normal, n, size, seed, palette=COLORS):
    """Друза: n кристаллов веером от точки по нормали."""
    cx, cy, cz = center
    nx, ny, nz = normal
    for k in range(n):
        jx, jy, jz = (rng(seed, k, 1) - 0.5) * 1.2, (rng(seed, k, 2) - 0.5) * 1.2, (rng(seed, k, 3) - 0.5) * 1.2
        L = size * (0.6 + rng(seed, k, 4) * 0.7)
        off = ((rng(seed, k, 5) - 0.5) * size * 0.5, 0.0, (rng(seed, k, 6) - 0.5) * size * 0.5)
        crystal(p, (cx + off[0] * (1 - abs(nx)), cy + off[1], cz + off[2] * (1 - abs(nz))),
                (nx + jx * 0.6, ny + jy * 0.6, nz + jz * 0.6), L, size * 0.28, palette[(k + seed) % len(palette)], WHITE)


def footprint(p, axis, fixed, out, a, y, s, d0, d1, color):
    """Трёхпалый след."""
    lo, hi = sorted((fixed + out * d0, fixed + out * d1))
    shapes = [K.octa(a, y, 0.7 * s, 0.6 * s, 0.25 * s)]
    for t in (-35, 0, 35):
        r = math.radians(t)
        u, v = math.sin(r), math.cos(r)
        shapes.append([(a + u * 0.6 * s - v * 0.18 * s, y + v * 0.6 * s + u * 0.18 * s),
                       (a + u * 1.6 * s, y + v * 1.6 * s),
                       (a + u * 0.6 * s + v * 0.18 * s, y + v * 0.6 * s - u * 0.18 * s)])
    for pts in shapes:
        if axis == "z":
            p.prism_xy(pts, lo, hi, color)
        elif axis == "x":
            p.prism_zy(pts, lo, hi, color)
        else:
            p.prism_xz(pts, lo, hi, color)


# ══ ФАСАД: расколотая жеода ═══════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, ROCKD, ROCKD, ROCKD)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FR, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, 1.0, ROCK2)
    # гранёные глыбы: ряды неровной высоты, разный вынос
    y = 1.0
    for r, rh in enumerate((4, 3, 4, 3, 4)):
        a = -half - 1.0
        k = 0
        while a < half + 1.0 - 0.5:
            w = 3 + int(rng(fi, r, k) * 4)
            a1 = min(a + w, half + 1.0)
            d = 0.88 + (1.0 if rng(fi, r, k, 3) > 0.6 else 0.0)
            slab(FR, axis, fixed, out, d, a + 0.06, a1 - 0.06, y + 0.06, min(y + rh, 19.0) - 0.06,
                 (ROCK, ROCK3, ROCK2)[int(rng(fi, r, k, 7) * 3)])
            a, k = a1, k + 1
        y += rh
    slab(FS, axis, fixed, out, 0.8, -half - 0.8, half + 0.8, 1.0, 19.0, ROCKD)
    # светящиеся жилы-трещины зигзагом
    for v in range(3):
        a = -half + 4.0 + v * (2 * half - 8.0) / 2 + (rng(fi, v) - 0.5) * 3
        yy = 2.0
        for seg in range(5):
            na = a + (rng(fi, v, seg) - 0.5) * 3.0
            ny = yy + 3.0
            lo_a, hi_a = sorted((a, na))
            slab(FG, axis, fixed, out, 1.95, lo_a - 0.12, hi_a + 0.12, yy, yy + 0.25, GLOW if v % 2 else GLOW2, back=-1.8)
            slab(FG, axis, fixed, out, 1.95, na - 0.12, na + 0.12, yy, ny, GLOW if v % 2 else GLOW2, back=-1.8)
            a, yy = na, ny
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
F.objects(True)
# друзы на углах и по верхнему краю
for sx in (-1, 1):
    for sz in (-1, 1):
        druse(FS, (sx * (FX + 1.2), 1.0, sz * (FZ + 1.2)), (sx * 0.45, 0.8, sz * 0.45), 6, 5.2, int(7 + sx * 3 + sz))
        druse(FS, (sx * (FX + 1.0), 13.0, sz * (FZ + 1.0)), (sx * 0.7, 0.35, sz * 0.7), 5, 3.8, int(17 + sx * 3 + sz))
for k in range(6):
    x = -13.0 + 5.2 * k
    druse(FS, (x, 16.4, -FZ - 1.4), (0.0, 0.25, -1.0), 3, 2.4, 40 + k)
# пасть жеоды спереди: кольцо кристаллов вокруг светящегося нутра
gx, gy = 0.0, 9.0
FS.prism_xy(K.octa(gx, gy, 6.4, 6.6, 2.6), -FZ - 2.0, -FZ - 0.5, ROCK3)
FS.prism_xy(K.octa(gx, gy, 5.2, 5.4, 2.1), -FZ - 2.05, -FZ - 2.0, ROCKD)
FG.prism_xy(K.octa(gx, gy, 3.2, 3.6, 1.3), -FZ - 2.1, -FZ - 2.05, GLOW)
for k in range(16):
    t = 2 * math.pi * k / 16
    bx, by = gx + 5.0 * math.cos(t), gy + 5.2 * math.sin(t)
    crystal(FS, (bx, by, -FZ - 2.0), (-math.cos(t) * 0.8, -math.sin(t) * 0.8, -0.9), 2.2 + rng(k, 88) * 1.0, 0.75,
            COLORS[k % 5], WHITE)
druse(FG, (gx, gy - 2.6, -FZ - 2.1), (0.0, 0.6, -0.5), 4, 2.2, 61, (AME, PINK, CYAN))
F.objects(False)
# бока: окаменелые следы
for s in (-1, 1):
    for k, (z, y) in enumerate(((-11.0, 5.0), (-5.5, 8.0), (0.5, 5.4), (6.0, 8.4), (11.5, 5.8))):
        footprint(FS, "x", s * FX, s, z, y, 0.9, 1.88, 2.05, ROCKD)
F.objects(True)
# тыл: малые друзы
for x in (-8.0, 2.0, 10.0):
    druse(FS, (x, 6.0 + rng(x, 3) * 6.0, FZ + 1.6), (0.0, 0.2, 1.0), 3, 2.2, int(70 + x))

F.objects(False)
# ══ ИНТЕРЬЕР: кристальная пещера ══════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.3
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), ROCK2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    y = 0.0
    for r, rh in enumerate((3, 4, 3, 4, 4)):
        a = -half
        k = 0
        while a < half - 0.3:
            w = 3 + int(rng(idx, r, k, 11) * 4)
            a1 = min(a + w, half)
            if not (gap and y < DOOR[1] + 0.3 and a1 > -DOOR[0] - 0.6 and a < DOOR[0] + 0.6):
                d = 0.88 + (0.6 if rng(idx, r, k, 12) > 0.55 else 0.0)
                slab(IR, axis, fixed, out, d, a + 0.06, a1 - 0.06, y + 0.06, min(y + rh, C) - 0.06,
                     (ROCK, ROCK3, ROCK2)[int(rng(idx, r, k, 13) * 3)])
            a, k = a1, k + 1
        y += rh
    slab(IQ, axis, fixed, out, 0.7, -half, half, 0.0, C, ROCKD)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 14.0, ROCK)
    # друзы из стен
    for k in range(3):
        a = -half * 0.65 + half * 0.65 * k
        if gap and abs(a) < DOOR[0] + 2.5:
            continue
        yy = 3.0 + rng(idx, k, 21) * 9.0
        if axis == "x":
            druse(IS, (fixed + out * 1.2, yy, a), (out, 0.25, 0.0), 4, 2.6, 100 + idx * 5 + k)
        else:
            druse(IS, (a, yy, fixed + out * 1.2), (0.0, 0.25, out), 4, 2.6, 100 + idx * 5 + k)
F.objects(True)
# кристаллы-сосульки с потолка
for k in range(16):
    x, z = (rng(k, 141) - 0.5) * 28, (rng(k, 142) - 0.5) * 26
    if abs(x - PED[0]) < 3 and abs(z - PED[1]) < 3:
        continue
    crystal(IS, (x, C, z), ((rng(k, 143) - 0.5) * 0.4, -1.0, (rng(k, 144) - 0.5) * 0.4), 2.0 + rng(k, 145) * 2.5,
            0.6 + rng(k, 146) * 0.3, COLORS[k % 5], WHITE)
# друзы на полу по углам и вдоль тропы
for k, (x, z, sz_) in enumerate(((-13.0, -12.5, 4.2), (12.5, -12.0, 4.6), (-13.5, 4.0, 3.4), (13.0, 2.0, 3.6),
                                  (-8.5, 12.5, 2.6), (8.5, 12.0, 2.4))):
    druse(IS, (x, 0.0, z), (0.0, 1.0, 0.0), 6, sz_, 150 + k)
F.objects(False)
# светящиеся озерца, тропа, следы
for x, z, rx, rz in ((-10.0, -4.0, 2.6, 2.0), (10.5, -6.0, 2.2, 2.8)):
    IG.prism_xz(K.octa(x, z, rx, rz, 0.8), 0.02, 0.07, CYAN)
    IS.frame_xz(K.octa(x, z, rx + 0.4, rz + 0.4, 0.9), K.octa(x, z, rx, rz, 0.8), 0.0, 0.25, ROCK3)
for k in range(7):
    z = 3.0 + 1.7 * k
    x = (rng(k, 151) - 0.5) * 1.2
    IG.prism_xz(K.octa(x, z, 0.55, 0.45, 0.2), 0.02, 0.1, (GLOW, GLOW2)[k % 2])
for k, (x, z) in enumerate(((-5.5, 6.0), (-4.0, 9.0), (-5.5, 12.0), (5.0, 7.5), (6.5, 10.5))):
    footprint(IG, "y", 0.0, 1, x, z, 0.6, 0.02, 0.06, GLOW2)
F.objects(True)
# кристаллический постамент с короной кристаллов
px, pz = PED
IR.prism_xz(K.octa(px, pz, 4.4, 4.4, 1.8), 0.0, 0.7, ROCK3)
IR.prism_xz(K.octa(px, pz, 3.6, 3.6, 1.5), 0.7, TOP, AME2)
IG.frame_xz(K.octa(px, pz, 3.8, 3.8, 1.55), K.octa(px, pz, 3.6, 3.6, 1.5), 0.7, 0.85, GLOW)
for k in range(10):
    t = 2 * math.pi * (k + 0.5) / 10
    bx, bz = px + 4.6 * math.cos(t), pz + 4.6 * math.sin(t)
    if math.sin(t) > 0.6:  # спереди от лифта — без кристаллов, чтобы не закрывать экспонат
        continue
    crystal(IS, (bx, 0.0, bz), (math.cos(t) * 0.35, 1.0, math.sin(t) * 0.35), 2.4 + rng(k, 161) * 2.0, 0.7,
            COLORS[k % 5], WHITE)
F.objects(False)
B.lift_leaves(IS, ROCK3, AME)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, ROCK)
SL.box(-FX - 2.9, FX + 2.9, -1, 1.0, -FZ - 2.9, FZ + 2.9, ROCK2)
SL.box(-FX - 1.3, FX + 1.3, 1.0, 19.0, -FZ - 1.3, FZ + 1.3, ROCK3)
SL.box(-6.0, 6.0, 3.0, 15.0, -FZ - 2.2, -FZ, AME2)
SL.box(-3.2, 3.2, 5.6, 12.6, -FZ - 2.3, -FZ - 2.2, GLOW)
for sx in (-1, 1):
    for sz in (-1, 1):
        SL.box(sx * (FX + 0.5), sx * (FX + 3.2), 1.0, 5.5, sz * (FZ + 0.5), sz * (FZ + 3.2), (AME, CYAN)[sz > 0])
        SL.box(sx * (FX + 0.4), sx * (FX + 2.4), 16.0, 18.8, sz * (FZ + 0.4), sz * (FZ + 2.4), (PINK, AME)[sz > 0])

F.build(exhibit=(PED[0], TOP, PED[1], 2.5), lamps=[("Hall", (0, 14, 6), 2600, (0.85, 0.8, 1.0)),
                                                   ("Spot", (0, 13, -3), 3200, (0.95, 0.95, 1.0))])
