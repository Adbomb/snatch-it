"""Этаж «Феникс-головоломка» музея-небоскрёба (восьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — мастерская фейерверков. Снаружи — тёмно-синяя «ночная» стена со звёздами, по которой разлетаются
три салюта разного размера (светящиеся лучи-искры), внизу — красно-жёлтый цоколь с предупреждающими полосами,
ворота цеха, у фасада на пусковых рамах стоят огромные ракеты в полоску, рядом — батареи-кубы из цветных трубок,
ящики и катушки фитиля; по парапету — ряд маленьких ракет, готовых к пуску. Внутри — цех: тёмный потолок-небо с
вспышками салютов, верстаки с трубками и шарами-звёздками, стеллажи цветных зарядов, большая ракета на стапеле,
бочки с порохом, фонарики; экспонат — на стальной пусковой площадке с красно-жёлтым кольцом и стрелками.
Запуск: blender --background --factory-startup --python scripts/blender/floor_fireworks.py -- <репо> <превью>
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

NIGHT, NIGHT2, RED, RED2, YEL, STEEL = "26386A", "30467E", "D83A2E", "A82A22", "F2C21E", "8A929C"
STEEL2, DARK, WOOD, WOOD2, STAR, GLASS = "6A727C", "22242C", "A87444", "7A5232", "FFF4C0", "FFE0A0"
SPARK = ("FF5A4A", "FFC830", "5AE0FF", "B070FF", "6AF070", "FF70C0")

F = B.Floor("FW", "PuzzlePhoenix", quiet=(DARK, "5A5E66"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def burst(g, cx, cy, z0, z1, r, rays, col, col2, plane="xy"):
    """Салют (вид на плоскости): лучи-искры от центра и точки на концах."""
    for k in range(rays):
        a = 2 * math.pi * (k + 0.3) / rays
        x1, y1 = cx + r * math.cos(a), cy + r * math.sin(a)
        nx, ny = -math.sin(a) * 0.09, math.cos(a) * 0.09
        pts = [(cx + nx, cy + ny), (x1 + nx * 0.4, y1 + ny * 0.4), (x1 - nx * 0.4, y1 - ny * 0.4), (cx - nx, cy - ny)]
        (g.prism_xy if plane == "xy" else g.prism_zy)(pts, z0, z1, col if k % 2 else col2)
        dot = K.ngon(cx + r * 1.12 * math.cos(a), cy + r * 1.12 * math.sin(a), 0.16, 5)
        (g.prism_xy if plane == "xy" else g.prism_zy)(dot, z0, z1, col2 if k % 2 else col)


def rocket(p, g, base, tip, r, stripes=(RED, "F4F4F0")):
    """Ракета: полосатый корпус, конус, стабилизаторы, огонёк фитиля."""
    bx, by, bz = base
    tx, ty, tz = tip
    L = math.dist(base, tip)
    ux, uy, uz = (tx - bx) / L, (ty - by) / L, (tz - bz) / L
    n = 5
    for k in range(n):
        a = (bx + ux * L * 0.8 * k / n, by + uy * L * 0.8 * k / n, bz + uz * L * 0.8 * k / n)
        b = (bx + ux * L * 0.8 * (k + 1) / n, by + uy * L * 0.8 * (k + 1) / n, bz + uz * L * 0.8 * (k + 1) / n)
        beam(p, a, b, r * 2, r * 2, stripes[k % 2])
    nose = (bx + ux * L * 0.8, by + uy * L * 0.8, bz + uz * L * 0.8)
    taper(p, nose, tip, r * 2.1, 0.08, stripes[0])
    for e in (-1, 1):
        beam(p, (bx, by, bz), (bx + ux * 1.2 + e * r * 1.6, by + uy * 1.2, bz + uz * 1.2), 0.12, 0.7, YEL)
    g.prism_xz(K.ngon(bx, bz, 0.18, 5), by - 0.4, by, "FF9A30")


def cake(p, x, z, y, cols, n=3, s=0.42):
    """Батарея салюта: куб из цветных трубок n × n."""
    p.box(x - n * s, x + n * s, y, y + 0.3, z - n * s, z + n * s, DARK)
    for i in range(n):
        for j in range(n):
            xx, zz = x - (n - 1) * s + 2 * s * i, z - (n - 1) * s + 2 * s * j
            p.prism_xz(K.ngon(xx, zz, s * 0.9, 6), y + 0.3, y + 1.4 + 0.2 * ((i + j) % 2), cols[(i + 2 * j) % len(cols)])


def spool(p, x, z, y, r=0.7):
    """Катушка фитиля: две щеки и намотка."""
    for e in (-1, 1):
        p.prism_xy(K.ngon(x, y + r, r, 10), z + e * 0.35 - 0.06, z + e * 0.35 + 0.06, WOOD2)
    p.prism_xy(K.ngon(x, y + r, r * 0.7, 10), z - 0.3, z + 0.3, "C84A2A")


# ══ ФАСАД: мастерская фейерверков ═════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, NIGHT, NIGHT, DARK)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "5A5E66")
    slab(FR, axis, fixed, out, 1.18, -half - 0.2, half + 0.2, -0.1, 2.2, RED)
    for k in range(int(2 * half // 1.6)):  # полосы над цоколем
        a = -half + 1.6 * k
        slab(FS, axis, fixed, out, 1.22, a, a + 0.8, 2.2, 2.8, YEL)
        slab(FS, axis, fixed, out, 1.22, a + 0.8, a + 1.6, 2.2, 2.8, DARK)
    slab(FR, axis, fixed, out, 0.88, -half, half, 2.8, 16.8, NIGHT)
    slab(FR, axis, fixed, out, 1.58, -half - 0.4, half + 0.4, 16.8, 17.5, RED2)
    slab(FR, axis, fixed, out, 1.18, -half - 0.2, half + 0.2, 17.5, 18.9, NIGHT2)
    for k in range(22):  # звёзды
        a = -half + 1.0 + (2 * half - 2.0) * rng(fi, k, 1)
        y = 9.0 + 7.4 * rng(fi, k, 2)
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
        (FG.prism_zy if axis == "x" else FG.prism_xy)(K.ngon(a, y, 0.1 + 0.08 * rng(k, fi), 4), d0, d1, STAR)
    if fi > 0:  # бока и тыл: по одному салюту и окна цеха
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.95))
        burst(FG, (-6.0 if fi % 2 else 7.0), 12.6, d0, d1, 2.6 + 0.4 * fi, 12, SPARK[fi], SPARK[(fi + 2) % 6], "zy" if axis == "x" else "xy")
        for a in (-12.0, -1.0, 10.0):
            (FG.prism_zy if axis == "x" else FG.prism_xy)(K.rect(a - 1.8, a + 1.8, 4.0, 6.6), d0, d1, GLASS)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# три салюта разного размера на передней стене
for (cx, cy, r, rays, c1, c2) in ((-8.6, 13.0, 3.6, 16, SPARK[1], SPARK[0]), (4.4, 11.4, 2.4, 12, SPARK[2], SPARK[3]),
                                  (12.2, 14.6, 1.8, 10, SPARK[4], SPARK[5])):
    burst(FG, cx, cy, -FZ - 0.95, -FZ - 0.9, r, rays, c1, c2)
for (x0, y0, x1, y1) in ((-9.4, 3.0, -8.6, 9.2), (4.0, 3.0, 4.4, 8.8)):  # следы взлёта
    for k in range(6):
        t0, t1 = k / 6, (k + 0.6) / 6
        FG.prism_xy([(x0 + (x1 - x0) * t0 - 0.06, y0 + (y1 - y0) * t0), (x0 + (x1 - x0) * t1 - 0.06, y0 + (y1 - y0) * t1),
                     (x0 + (x1 - x0) * t1 + 0.06, y0 + (y1 - y0) * t1), (x0 + (x1 - x0) * t0 + 0.06, y0 + (y1 - y0) * t0)],
                    -FZ - 0.95, -FZ - 0.9, "FFD890")
# ворота цеха
FS.box(-3.6, 1.6, 2.8, 8.8, -FZ - 0.96, -FZ - 0.88, DARK)
for k in range(6):
    FS.box(-3.3, 1.3, 2.8 + 1.0 * k, 3.7 + 1.0 * k, -FZ - 1.04, -FZ - 0.96, STEEL if k % 2 else STEEL2)
FS.frame_xy(K.rect(-3.9, 1.9, 2.8, 9.1), K.rect(-3.6, 1.6, 2.8, 8.8), -FZ - 1.3, -FZ - 0.88, YEL)
# огромные ракеты на пусковых рамах, батареи, ящики, катушки
F.objects(True)
for (x, lean, r, h, st) in ((-15.6, 0.6, 0.55, 9.6, (RED, "F4F4F0")), (-13.0, -0.4, 0.45, 7.6, ("3A6AE0", YEL)),
                            (13.8, 0.3, 0.6, 10.2, ("8A4AD0", "F4F4F0")), (16.4, -0.6, 0.45, 7.8, (RED, YEL))):
    z = -FZ - 1.9
    rocket(FS, FG, (x, 1.6, z), (x + lean, 1.6 + h, z - 0.2), r, st)
    for e in (-1, 1):
        beam(FS, (x + e * 0.9, -0.1, z - 0.8), (x + lean * 0.4, 1.6 + h * 0.4, z), 0.14, 0.14, STEEL2)
    FS.box(x - 1.0, x + 1.0, -0.1, 1.2, z - 0.7, z + 0.7, STEEL2)
cake(FS, -9.6, -FZ - 1.9, -0.1, SPARK[:4], n=3)
cake(FS, 7.6, -FZ - 1.8, -0.1, SPARK[2:], n=3, s=0.4)
cake(FS, 9.8, -FZ - 1.6, -0.1, SPARK, n=2, s=0.45)
for x in (-6.4, -5.2):
    D.crate(FS, x, -FZ - 1.6, y=-0.1, s=1.1, wood=WOOD, board=RED2)
spool(FS, 4.4, -FZ - 1.6, -0.1)
F.objects(False)
for k in range(17):  # ряд маленьких ракет по парапету
    x = -16.0 + 2.0 * k
    FS.prism_xz(K.ngon(x, -FZ - 1.2, 0.2, 6), 17.5, 18.3, SPARK[k % 6])
    FS.cone([(xx, 18.3, zz) for xx, zz in K.ngon(x, -FZ - 1.2, 0.22, 6)], (x, 18.85, -FZ - 1.2), "F4F4F0")

# ══ ИНТЕРЬЕР: цех ═════════════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.1
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "5A5E66")
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, NIGHT2)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 2.6, RED2)
        slab(IS, axis, fixed, out, 1.05, a0, a1, 2.6, 2.9, YEL)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, NIGHT2)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, YEL)
for k in range(-3, 4):
    IS.box(-W, W, C - 0.5, C - 0.2, 4.4 * k - 0.2, 4.4 * k + 0.2, DARK)
for (cx, cz, r, c1, c2) in ((-8.0, -9.0, 3.0, SPARK[0], SPARK[1]), (8.4, -1.0, 2.4, SPARK[2], SPARK[4]), (-6.0, 6.0, 1.8, SPARK[3], SPARK[5])):
    for k in range(12):  # вспышки на потолке-небе
        a = 2 * math.pi * k / 12
        IG.prism_xz([(cx + 0.08 * math.sin(a), cz - 0.08 * math.cos(a)), (cx + r * math.cos(a), cz + r * math.sin(a)),
                     (cx - 0.08 * math.sin(a), cz + 0.08 * math.cos(a))], C - 0.12, C - 0.08, c1 if k % 2 else c2)
for k in range(30):
    x, z = -W + 1.5 + (2 * W - 3) * rng(k, 21), ZF + 1.5 + (ZB - ZF - 3) * rng(k, 22)
    IG.prism_xz(K.ngon(x, z, 0.1, 4), C - 0.08, C - 0.05, STAR)
# верстаки, стеллажи с зарядами, ракета на стапеле, бочки
F.objects(True)
for s in (-1, 1):
    x = s * (W - 0.88)
    d0, d1 = sorted((x, x - s * 1.4))
    IS.box(d0, d1, 0.0, 8.4, -14.6, -14.2, DARK)
    IS.box(d0, d1, 0.0, 8.4, -5.0, -4.6, DARK)
    for y in (2.6, 5.2, 7.8):
        IS.box(d0, d1, y - 0.15, y, -14.6, -4.6, WOOD)
        for i in range(7):
            zz = -13.8 + 1.3 * i
            IS.prism_xz(K.ngon(x - s * 0.7, zz, 0.38, 6), y, y + 1.0 + 0.4 * (i % 2), SPARK[(i + int(y)) % 6])
    TX = s * (W - 3.4)
    for z0 in (-1.0, 4.0):
        IS.box(TX - 1.2, TX + 1.2, 2.6, 2.9, z0, z0 + 3.4, WOOD)
        for e in (-1, 1):
            for f in (0, 1):
                IS.box(TX + e * 1.0 - 0.12, TX + e * 1.0 + 0.12, 0.0, 2.6, z0 + 0.2 + 3.0 * f - 0.12, z0 + 0.2 + 3.0 * f + 0.12, WOOD2)
        for k in range(4):
            IS.prism_zy(K.ngon(z0 + 0.6 + 0.7 * k, 3.25, 0.3, 6), TX - 0.8, TX + 0.4, SPARK[(k + int(z0)) % 6])
        IS.prism_xz(K.octa(TX + 0.7, z0 + 2.6, 0.35, 0.35, 0.12), 2.9, 3.6, SPARK[1])
rocket(IS, IG, (-9.6, 2.0, -12.0), (-9.6, 13.4, -12.2), 0.8, (RED, "F4F4F0"))
for e in (-1, 1):
    beam(IS, (-9.6 + e * 1.6, 0.0, -12.0), (-9.6 + e * 0.6, 7.0, -12.0), 0.2, 0.2, STEEL2)
IS.box(-11.0, -8.2, 0.0, 1.6, -13.2, -10.8, STEEL2)
for k in range(3):
    D.barrel(IS, 9.4 + 1.6 * (k % 2), -12.4 + 1.4 * (k // 2), r=0.75, h=1.6, wood=RED2, hoop=DARK)
F.objects(False)
for x, z in ((-5.0, -4.0), (5.0, -4.0), (0.0, 4.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.6, C - 0.5, z - 0.03, z + 0.03, DARK)
    D.lantern(IS, IG, x, C - 4.6, z, s=1.0, cap=RED2, light=GLASS)
# постамент: стальная пусковая площадка с красно-жёлтым кольцом и стрелками
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, 0.4, DARK)
for k in range(16):
    t0, t1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
    IS.prism_xz([(px + 3.6 * math.cos(t0), pz + 3.6 * math.sin(t0)), (px + 4.05 * math.cos(t0), pz + 4.05 * math.sin(t0)),
                 (px + 4.05 * math.cos(t1), pz + 4.05 * math.sin(t1)), (px + 3.6 * math.cos(t1), pz + 3.6 * math.sin(t1))],
                0.4, 0.75, RED if k % 2 else YEL)
IS.prism_xz(K.ngon(px, pz, 3.6, 16), 0.4, TOP - 0.06, STEEL)
IS.prism_xz(K.ngon(px, pz, 3.7, 16), TOP - 0.06, TOP, STEEL2)
for k in range(4):
    a = math.pi / 2 * k + math.pi / 4
    x, z = px + 5.0 * math.cos(a), pz + 5.0 * math.sin(a)
    IS.prism_xz([(x + 0.6 * math.cos(a + 2.4), z + 0.6 * math.sin(a + 2.4)), (x - 0.5 * math.cos(a), z - 0.5 * math.sin(a)),
                 (x + 0.6 * math.cos(a - 2.4), z + 0.6 * math.sin(a - 2.4))], 0.02, 0.06, YEL)
B.lift_leaves(IS, STEEL2, YEL)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, NIGHT)
SL.box(-FX - 0.3, FX + 0.3, -0.1, 2.8, -FZ - 0.3, FZ + 0.3, RED)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "5A5E66")
SL.box(-FX - 0.5, FX + 0.5, 16.8, 17.5, -FZ - 0.5, FZ + 0.5, RED2)
for x, h in ((-15.6, 11.2), (13.8, 11.8)):
    SL.box(x - 0.7, x + 0.7, 1.6, h, -FZ - 2.6, -FZ - 1.2, RED)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 1600, (1.0, 0.92, 0.85)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Sparks", (-8, 12, -9), 600, (1.0, 0.8, 0.5))])
