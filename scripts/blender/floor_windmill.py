"""Этаж «Гриф-вентилятор» музея-небоскрёба (восьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — мельница-пекарня. Снаружи — белёные стены с тёмным фахверком, кирпичный цоколь и красная черепичная
кровля-пояс; на фасаде крутятся четыре огромных крыла мельницы (решётчатые лопасти с парусиной) на деревянной
ступице; внизу — витрина пекарни с хлебами под полосатым навесом, дверь с вывеской-кренделем, мешки муки, тележка
со снопами, кадки с тюльпанами; по углам — две маленькие белые ветряные турбины на мачтах. Внутри — мукомольный
зал: деревянные балки, жернова под вертикальным валом с зубчатым колесом, кирпичная печь с огнём, длинный стол с
хлебами, полки с караваями, мешки и снопы, подвесные фонари; экспонат — на круглом жёрнове с бороздами.
Запуск: blender --background --factory-startup --python scripts/blender/floor_windmill.py -- <репо> <превью>
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

PLASTER, PLASTER2, TIMBER, TIMBER2, ROOF, ROOF2 = "F2EBDD", "E2D8C4", "6A4426", "4E3018", "B04A32", "8A3A2A"
BRICK, SAIL, WOOD, STONE, STONE2, BREAD = "B5563A", "F4EEDD", "A87440", "9A9A92", "7A7A74", "D89A50"
WHEAT, FLOUR, FIRE, GLASS, WHITE = "E8C060", "F0EAD8", "FF9A30", "FFE8B0", "F6F6F2"
TULIPS = ("E8343A", "F0C020", "E870B0", "F08A20")

F = B.Floor("WM", "FanVulture", quiet=(STONE2, "B8A888", ROOF2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def sail(p, cx, cy, z, ang, length=7.6, w=1.9):
    """Крыло мельницы: брус-махалка, решётка с перекладинами и парусина на одной стороне."""
    ca, sa = math.cos(ang), math.sin(ang)
    tip = (cx + length * ca, cy + length * sa, z)
    beam(p, (cx, cy, z), tip, 0.3, 0.3, TIMBER2)
    nx, ny = -sa, ca  # поперёк махалки
    r0 = 1.4
    a0 = (cx + r0 * ca, cy + r0 * sa)
    a1 = (cx + length * ca, cy + length * sa)
    edge0 = (a0[0] + nx * w, a0[1] + ny * w)
    edge1 = (a1[0] + nx * w, a1[1] + ny * w)
    beam(p, (*edge0, z - 0.05), (*edge1, z - 0.05), 0.12, 0.12, TIMBER)
    for k in range(7):  # перекладины
        t = k / 6
        x, y = a0[0] + (a1[0] - a0[0]) * t, a0[1] + (a1[1] - a0[1]) * t
        beam(p, (x, y, z - 0.05), (x + nx * w, y + ny * w, z - 0.05), 0.1, 0.1, TIMBER)
    p.prism_xy([a0, a1, edge1, edge0], z + 0.02, z + 0.08, SAIL)


def turbine(p, x, z, y0, h, face=-1):
    """Маленькая ветряная турбина: мачта, гондола, три лопасти."""
    p.prism_xz(K.ngon(x, z, 0.3, 8), y0, y0 + h, "D8DCE0")
    p.box(x - 0.35, x + 0.35, y0 + h - 0.3, y0 + h + 0.4, z - 0.7, z + 0.3, "D8DCE0")
    hub = (x, y0 + h + 0.05, z + face * 0.65)
    for k in range(3):
        a = math.pi / 2 + 2 * math.pi * k / 3
        taper(p, hub, (x + 2.2 * math.cos(a), hub[1] + 2.2 * math.sin(a), hub[2]), 0.55, 0.15, "D8DCE0")


def loaf(p, x, y, z, s=1.0, col=BREAD):
    """Каравай: гранёный ком с насечками."""
    p.prism_xz(K.octa(x, z, 0.55 * s, 0.35 * s, 0.15 * s), y, y + 0.25 * s, col)
    p.prism_xz(K.octa(x, z, 0.45 * s, 0.28 * s, 0.12 * s), y + 0.25 * s, y + 0.42 * s, col)


def sack(p, x, z, y=0.0, s=1.0):
    """Мешок муки: тело, перевязанная горловина."""
    p.prism_xz(K.octa(x, z, 0.55 * s, 0.45 * s, 0.18 * s), y, y + 1.0 * s, FLOUR)
    p.prism_xz(K.ngon(x, z, 0.22 * s, 6), y + 1.0 * s, y + 1.25 * s, "C8B890")
    p.prism_xz(K.ngon(x, z, 0.3 * s, 6), y + 1.25 * s, y + 1.4 * s, FLOUR)


def sheaf(p, x, z, y=0.0, h=1.8):
    """Сноп пшеницы: связка, пояс, колосья веером."""
    p.prism_xz(K.ngon(x, z, 0.35, 8), y, y + h * 0.7, WHEAT)
    p.prism_xz(K.ngon(x, z, 0.4, 8), y + h * 0.35, y + h * 0.45, TIMBER)
    for k in range(5):
        a = 2 * math.pi * k / 5
        taper(p, (x, y + h * 0.65, z), (x + 0.5 * math.cos(a), y + h, z + 0.5 * math.sin(a)), 0.25, 0.08, WHEAT)


def gear(p, x, y, z, r, teeth=12, col=WOOD):
    """Зубчатое колесо в горизонтальной плоскости: обод, спицы, зубья."""
    ring_y(p, x, z, r - 0.35, r, y, y + 0.3, col, n=teeth)
    for k in range(4):
        a = math.pi / 4 * k
        beam(p, (x - r * math.cos(a), y + 0.15, z - r * math.sin(a)), (x + r * math.cos(a), y + 0.15, z + r * math.sin(a)), 0.2, 0.2, col)
    for k in range(teeth):
        a = 2 * math.pi * (k + 0.5) / teeth
        p.box(x + r * math.cos(a) - 0.1, x + r * math.cos(a) + 0.1, y + 0.3, y + 0.6, z + r * math.sin(a) - 0.1, z + r * math.sin(a) + 0.1, TIMBER2)


# ══ ФАСАД: мельница-пекарня ═══════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, PLASTER, PLASTER, TIMBER2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "B8A888")
    slab(FR, axis, fixed, out, 1.18, -half - 0.2, half + 0.2, -0.1, 1.8, BRICK)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.8, 15.0, PLASTER)
    slab(FR, axis, fixed, out, 1.2, -half - 0.2, half + 0.2, 8.6, 9.2, TIMBER2)
    slab(FR, axis, fixed, out, 1.2, -half - 0.2, half + 0.2, 14.6, 15.2, TIMBER2)
    B.chamfer(FR, axis, fixed, out, -half - 1.6, half + 1.6, [(0.88, 18.9), (2.6, 15.6), (2.6, 15.2), (0.88, 15.2)], ROOF)
    for k in range(int(2 * half // 1.4) + 2):  # ряды черепицы
        a = -half - 1.4 + 1.4 * k
        if a > half + 1.4:
            continue
        p0 = (fixed + out * 1.1, 18.7, a) if axis == "x" else (a, 18.7, fixed + out * 1.1)
        p1 = (fixed + out * 2.55, 15.75, a) if axis == "x" else (a, 15.75, fixed + out * 2.55)
        beam(FS, p0, p1, 0.16, 0.12, ROOF2)
    for k in range(int(2 * half // 4.0) + 1):  # фахверк: стойки и раскосы
        a = -half + 0.3 + 4.0 * k
        if a + 0.4 > half:
            continue
        slab(FS, axis, fixed, out, 1.02, a, a + 0.4, 1.8, 14.6, TIMBER)
        if k % 2 == 0 and a + 4.0 < half:
            lo = fixed + out * 0.96
            if axis == "z":
                beam(FS, (a + 0.4, 9.2, lo), (a + 4.0, 14.6, lo), 0.3, 0.12, TIMBER)
            else:
                beam(FS, (lo, 9.2, a + 0.4), (lo, 14.6, a + 4.0), 0.3, 0.12, TIMBER)
    if fi > 0:  # бока и тыл: окна со ставнями
        for a in (-10.0, -2.0, 6.0):
            d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
            pr = FG.prism_zy if axis == "x" else FG.prism_xy
            pr(K.rect(a, a + 2.0, 11.0, 13.4), d0, d1, GLASS)
            for e in (-1, 1):
                s0, s1 = (a - 1.1, a - 0.05) if e < 0 else (a + 2.05, a + 3.1)
                slab(FS, axis, fixed, out, 1.0, s0, s1, 11.0, 13.4, "3A6A4A")
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# башня мельницы посреди фасада: сужающийся восьмигранный корпус в дранке, галерея, шатёр, крылья на ступице
HX, HY = 2.0, 10.2
TZ = -FZ - 0.35  # башня стоит на крыльце: тыл не заходит за плоскость зала (-FZ + 2.1)
bot = [(HX + 2.25 * math.cos(a), TZ + 2.25 * math.sin(a)) for a in [2 * math.pi * (k + 0.5) / 8 for k in range(8)]]
top = [(HX + 1.7 * math.cos(a), TZ + 1.7 * math.sin(a)) for a in [2 * math.pi * (k + 0.5) / 8 for k in range(8)]]
FR.loft([(x, 1.8, z) for x, z in bot], [(x, 15.4, z) for x, z in top], "7A5A3A")
FR.prism_xz(K.ngon(HX, TZ, 2.4, 8), 0.0, 1.8, BRICK)
for y in (5.0, 12.0):  # пояса дранки
    t = (y - 1.8) / 13.6
    r = 2.25 + (1.7 - 2.25) * t
    FS.prism_xz(K.ngon(HX, TZ, r + 0.12, 8), y, y + 0.3, TIMBER2)
ring_y(FS, HX, TZ, 1.95, 2.6, 8.4, 8.7, WOOD, n=16, a0=180.0, a1=360.0)  # галерея
for k in range(9):
    a = math.radians(180 + 22.5 * k)
    FS.box(HX + 2.5 * math.cos(a) - 0.06, HX + 2.5 * math.cos(a) + 0.06, 8.7, 9.7, TZ + 2.5 * math.sin(a) - 0.06, TZ + 2.5 * math.sin(a) + 0.06, TIMBER)
ring_y(FS, HX, TZ, 2.4, 2.6, 9.6, 9.75, TIMBER, n=16, a0=180.0, a1=360.0)
FS.cone([(x, 15.4, z) for x, z in K.ngon(HX, TZ, 2.1, 8)], (HX, 18.6, TZ), ROOF2)
FG.prism_xy([(HX - 0.5, 2.6), (HX + 0.5, 2.6), (HX + 0.5, 4.6), (HX, 5.1), (HX - 0.5, 4.6)], TZ - 2.12, TZ - 2.08, GLASS)
FG.prism_xy(K.rect(HX - 0.4, HX + 0.4, 12.6, 13.8), TZ - 1.74, TZ - 1.70, GLASS)
HZ = TZ - 2.55
FS.prism_xy(K.ngon(HX, HY, 0.9, 10), HZ, TZ - 1.6, TIMBER)
FS.prism_xy(K.ngon(HX, HY, 0.5, 8), HZ - 0.3, HZ, STONE2)
F.objects(True)
for k in range(4):
    sail(FS, HX, HY, HZ - 0.1, math.radians(20 + 90 * k), length=8.4, w=2.1)
F.objects(False)
# витрина пекарни под полосатым навесом, дверь с кренделем
FS.box(-14.0, -5.2, 1.8, 6.6, -FZ - 0.96, -FZ - 0.88, TIMBER2)
FG.box(-13.6, -5.6, 2.2, 6.2, -FZ - 1.0, -FZ - 0.96, GLASS)
FS.box(-13.8, -5.4, 2.0, 2.3, -FZ - 1.8, -FZ - 0.88, WOOD)
F.objects(True)
for k in range(6):
    loaf(FS, -13.0 + 1.4 * k, 2.3, -FZ - 1.35, s=1.0, col=(BREAD, "C88040", "E8B868")[k % 3])
F.objects(False)
for k in range(9):
    x0 = -14.4 + 1.0 * k
    FS.loft([(x0, 7.6, -FZ - 0.9), (x0 + 1.0, 7.6, -FZ - 0.9), (x0 + 1.0, 7.75, -FZ - 0.9), (x0, 7.75, -FZ - 0.9)],
            [(x0, 6.7, -FZ - 2.6), (x0 + 1.0, 6.7, -FZ - 2.6), (x0 + 1.0, 6.85, -FZ - 2.6), (x0, 6.85, -FZ - 2.6)],
            "C83A30" if k % 2 else WHITE)
DX = 10.4
FS.box(DX - 1.6, DX + 1.6, 1.8, 7.0, -FZ - 0.96, -FZ - 0.88, TIMBER2)
FS.box(DX - 1.3, DX + 1.3, 1.8, 6.6, -FZ - 1.06, -FZ - 0.96, WOOD)
FG.box(DX - 0.8, DX + 0.8, 4.4, 6.0, -FZ - 1.1, -FZ - 1.06, GLASS)
FS.box(DX - 0.08, DX + 0.08, 7.0, 8.6, -FZ - 1.6, -FZ - 1.5, "2A2A2A")
FS.box(DX - 0.08, DX + 1.6, 8.3, 8.45, -FZ - 1.6, -FZ - 0.88, "2A2A2A")
B.tube(FS, [(DX + 1.4, 7.6, -FZ - 1.55), (DX + 0.8, 7.0, -FZ - 1.55), (DX + 1.4, 6.4, -FZ - 1.55), (DX + 2.0, 7.0, -FZ - 1.55),
          (DX + 1.4, 7.6, -FZ - 1.55)], [0.3] * 5, 0.25, (0, 0, 1), BREAD)
# мешки, тележка со снопами, кадки с тюльпанами
F.objects(True)
for k, (x, z) in enumerate(((-3.8, -FZ - 1.6), (-4.9, -FZ - 1.7), (-4.3, -FZ - 2.5))):
    sack(FS, x, z, y=-0.1, s=0.9)
CX = 14.4
FS.box(CX - 1.8, CX + 1.8, 0.9, 1.1, -FZ - 2.7, -FZ - 1.3, WOOD)
for e in (-1, 1):
    FS.box(CX - 1.8, CX + 1.8, 1.1, 1.9, -FZ - 2.0 + e * 0.7 - 0.06, -FZ - 2.0 + e * 0.7 + 0.06, TIMBER)
FS.prism_xy(K.ngon(CX, 0.6, 0.65, 10), -FZ - 2.85, -FZ - 2.72, TIMBER2)
FS.prism_xy(K.ngon(CX, 0.6, 0.65, 10), -FZ - 1.28, -FZ - 1.15, TIMBER2)
beam(FS, (CX + 1.8, 1.0, -FZ - 2.0), (CX + 3.4, 0.2, -FZ - 2.0), 0.15, 0.15, TIMBER)
for k in range(3):
    sheaf(FS, CX - 1.0 + 1.0 * k, -FZ - 2.0, y=1.1, h=1.6)
for k, x in enumerate((-17.0, -15.6, 7.0, 8.2)):
    FS.prism_xz(K.ngon(x, -FZ - 1.8, 0.55, 8), -0.1, 0.8, TIMBER)
    for j in range(3):
        a = 2 * math.pi * j / 3 + k
        xx, zz = x + 0.25 * math.cos(a), -FZ - 1.8 + 0.25 * math.sin(a)
        FS.box(xx - 0.04, xx + 0.04, 0.8, 1.5, zz - 0.04, zz + 0.04, "3A8A3A")
        FS.prism_xz(K.octa(xx, zz, 0.16, 0.16, 0.05), 1.5, 1.85, TULIPS[(k + j) % 4])
F.objects(False)
# маленькие ветряные турбины по передним углам
F.objects(True)
for e in (-1, 1):
    turbine(FS, e * (FX + 0.9), -FZ - 1.2, -0.1, 15.2)
F.objects(False)

# ══ ИНТЕРЬЕР: мукомольный зал ═════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.0
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "B08A5A")
for k in range(-13, 14):  # доски пола
    if k % 2:
        IQ.box(1.2 * k, 1.2 * k + 1.2, 0.02, 0.04, ZF + 0.9, ZB - 0.9, "9A7448")
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, PLASTER)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 1.6, BRICK)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, PLASTER)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, TIMBER2)
    for k in range(int(2 * half // 4.0) + 1):  # стойки фахверка изнутри
        a = -half + 0.3 + 4.0 * k
        if a + 0.4 <= half and not (gap and abs(a + 0.2) < DOOR[0] + 0.8):
            slab(IS, axis, fixed, out, 1.05, a, a + 0.4, 1.6, C, TIMBER)
    slab(IR, axis, fixed, out, 1.3, -half, half, 14.0, 14.6, TIMBER2)
for k in range(-3, 4):
    IS.box(-W, W, C - 0.8, C - 0.2, 4.4 * k - 0.3, 4.4 * k + 0.3, TIMBER2)
# жернова под вертикальным валом с зубчатым колесом (у дальней стены справа)
MX, MZ = 9.0, -10.4
F.objects(True)
IS.box(MX - 2.4, MX + 2.4, 0.0, 1.6, MZ - 2.4, MZ + 2.4, WOOD)
IS.prism_xz(K.ngon(MX, MZ, 2.0, 16), 1.6, 2.2, STONE)
IS.prism_xz(K.ngon(MX, MZ, 2.0, 16), 2.3, 2.9, STONE2)
IS.prism_xz(K.ngon(MX, MZ, 0.3, 8), 2.2, C - 0.8, TIMBER2)
gear(IS, MX, 10.0, MZ, 2.2)
IS.cone([(x, 4.2, z) for x, z in K.ngon(MX, MZ, 1.2, 8)], (MX, 3.0, MZ), WOOD)  # бункер-воронка
IS.prism_xz(K.ngon(MX, MZ, 1.3, 8), 4.2, 5.4, WOOD)
F.objects(False)
# кирпичная печь с огнём (слева у дальней стены)
OX, OZ = -11.0, -11.6
IR.box(OX - 3.0, OX + 3.0, 0.0, 2.4, OZ - 2.6, OZ + 2.6, BRICK)
IR.prism_xz(K.octa(OX, OZ, 2.6, 2.2, 0.8), 2.4, 5.0, BRICK)
IR.prism_xz(K.octa(OX, OZ, 1.8, 1.5, 0.6), 5.0, 6.0, BRICK)
IS.box(OX - 0.5, OX + 0.5, 6.0, C - 0.8, OZ - 0.5, OZ + 0.5, BRICK)
IS.prism_xy([(OX - 1.2, 2.4), (OX + 1.2, 2.4), (OX + 1.2, 3.6), (OX, 4.3), (OX - 1.2, 3.6)], OZ + 2.2, OZ + 2.62, "2A1A14")
IG.prism_xy([(OX - 0.9, 2.5), (OX + 0.9, 2.5), (OX + 0.6, 3.4), (OX, 3.9), (OX - 0.6, 3.4)], OZ + 2.1, OZ + 2.2, FIRE)
F.objects(True)
beam(IS, (OX + 3.4, 0.0, OZ + 3.0), (OX + 3.0, 4.6, OZ + 2.7), 0.14, 0.14, WOOD)  # лопата для хлеба
IS.box(OX + 3.0, OX + 3.9, 0.0, 0.1, OZ + 2.6, OZ + 3.6, WOOD)
F.objects(False)
# длинный стол с хлебами и полки с караваями
F.objects(True)
TX, TBZ = -12.4, -1.0
IS.box(TX - 1.4, TX + 1.4, 2.6, 2.9, TBZ - 4.0, TBZ + 4.0, WOOD)
for e in (-1, 1):
    for f in (-1, 1):
        IS.box(TX + e * 1.2 - 0.15, TX + e * 1.2 + 0.15, 0.0, 2.6, TBZ + f * 3.7 - 0.15, TBZ + f * 3.7 + 0.15, TIMBER)
for k in range(5):
    loaf(IS, TX + (0.5 if k % 2 else -0.5), 2.9, TBZ - 3.0 + 1.5 * k, s=1.1, col=(BREAD, "C88040", "E8B868")[k % 3])
x = W - 0.88
for y in (3.4, 5.6, 7.8):
    IS.box(x - 1.4, x, y, y + 0.2, -6.0, 3.0, WOOD)
    for k in range(6):
        loaf(IS, x - 0.7, y + 0.2, -5.2 + 1.5 * k, s=0.9, col=(BREAD, "E8B868")[k % 2])
for k, (sx, sz) in enumerate(((-14.6, 6.0), (-13.4, 6.4), (-14.0, 7.4), (13.6, 6.6), (14.6, 7.2))):
    sack(IS, sx, sz, s=1.0)
for x0 in (6.4, 7.4):
    sheaf(IS, x0, -14.2, h=2.2)
F.objects(False)
for x, z in ((-6.0, -6.0), (6.0, -6.0), (-6.0, 3.0), (6.0, 3.0)):
    IS.box(x - 0.04, x + 0.04, C - 3.2, C - 0.8, z - 0.04, z + 0.04, TIMBER2)
    D.lantern(IS, IG, x, C - 4.2, z, s=1.0, cap=TIMBER2, light=GLASS)
# постамент: круглый жёрнов с бороздами
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, 0.5, WOOD)
IS.prism_xz(K.ngon(px, pz, 3.7, 16), 0.5, TOP - 0.06, STONE)
IS.prism_xz(K.ngon(px, pz, 3.8, 16), TOP - 0.06, TOP, STONE2)
for k in range(8):
    a = 2 * math.pi * k / 8
    beam(IS, (px + 0.8 * math.cos(a), TOP + 0.01, pz + 0.8 * math.sin(a)), (px + 3.4 * math.cos(a + 0.3), TOP + 0.01, pz + 3.4 * math.sin(a + 0.3)),
         0.18, 0.04, "6A6A64")
B.lift_leaves(IS, TIMBER, BRICK)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 15.2, -FZ, FZ, PLASTER)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "B8A888")
SL.prism_xz(K.ngon(HX, TZ, 2.1, 8), -0.1, 15.4, "7A5A3A")
SL.cone([(x, 15.4, z) for x, z in K.ngon(HX, TZ, 2.1, 8)], (HX, 18.6, TZ), ROOF2)
SL.prism_zy([(-FZ - 2.6, 15.2), (FZ + 2.6, 15.2), (FZ + 0.88, 18.9), (-FZ - 0.88, 18.9)], -FX - 2.6, FX + 2.6, ROOF)
for k in range(4):
    a = math.radians(20 + 90 * k)
    SL.prism_xy([(HX + 1.4 * math.cos(a), HY + 1.4 * math.sin(a)), (HX + 8.4 * math.cos(a), HY + 8.4 * math.sin(a)),
                 (HX + 8.4 * math.cos(a) - 2.1 * math.sin(a), HY + 8.4 * math.sin(a) + 2.1 * math.cos(a)),
                 (HX + 1.4 * math.cos(a) - 2.1 * math.sin(a), HY + 1.4 * math.sin(a) + 2.1 * math.cos(a))], HZ - 0.2, HZ, SAIL)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.92, 0.82)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Oven", (-11, 4, -8), 600, (1.0, 0.6, 0.3))])
