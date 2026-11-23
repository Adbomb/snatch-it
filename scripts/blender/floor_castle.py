"""Этаж «Крыса-рыцарь» музея-небоскрёба (шестая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — рыцарский замок. Снаружи — кладка из крупных камней, по углам фасада круглые башни с зубцами,
в центре выступает надвратная башня с машикулями, стрельчатой аркой и приподнятой решёткой, перед ней — ров с водой
и опущенный подъёмный мост на цепях; над аркой — щит в красно-белую шашку и скрещённые мечи, по бокам — длинные
знамёна и факелы, в стенах — ряд бойниц; перед замком — соломенное чучело для тренировок со щитом, стойка с копьями,
тюки сена, бочка; на боках — контрфорсы, бойницы и плющ. Внутри — рыцарский зал: каменный пол из плит, по бокам
деревянные галереи на столбах, под ними — стойки с доспехами и оружием, у дальней стены — огромный камин с огнём
и гербом над ним, под потолком — фермы и знамёна, люстра-колесо со свечами, красная дорожка от лифта;
экспонат — на круглом каменном помосте в две ступени с красным кругом и золотой каймой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_castle.py -- <репо> <превью>
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

STONE, STONE2, STONE3, DSTONE = "B0ACA2", "9A968C", "C2BEB2", "6E6A62"
WOOD, WOOD2, RED, RED2, WHITE, GOLD = "8A5A34", "6A4226", "C83030", "962424", "F2EEE4", "E0B040"
BLUE, IRON, GRASS, WATER, STRAW, IVY = "3A5AA8", "3A3C42", "6AAA4A", "4A8AC0", "E8C870", "4A8A3C"

F = B.Floor("KN", "RatKnight", quiet=(GRASS, "5A8A3A", STONE2), bevel_min=1.2)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def shield(pr, a, y, s, base, out, checker=True):
    """Геральдический щит в шашку (pr — prism_xy / prism_zy, a — координата вдоль стены; base — плоскость стены,
    out — куда щит выступает, ±1)."""
    lay = lambda u, v: tuple(sorted((base + out * u, base + out * v)))  # noqa: E731
    outline = [(a - s, y + s * 1.1), (a + s, y + s * 1.1), (a + s, y), (a + s * 0.6, y - s * 0.8), (a, y - s * 1.2),
               (a - s * 0.6, y - s * 0.8), (a - s, y)]
    pr(outline, *lay(0.0, 0.3), GOLD)
    inner = [(u * 0.85 + a * 0.15, v * 0.85 + (y) * 0.15 + s * 0.02) for u, v in outline]
    pr(inner, *lay(0.3, 0.36), WHITE)
    if checker:
        for i in range(3):
            for j in range(3):
                if (i + j) % 2 == 0:
                    u0, v0 = a - s * 0.75 + s * 0.5 * i, y + s * 0.85 - s * 0.55 * (j + 1)
                    pr(K.rect(u0, u0 + s * 0.5, v0, v0 + s * 0.55), *lay(0.36, 0.4), RED)


def sword(p, x, y0, y1, z, along="z", d=0.0):
    """Меч остриём вниз: клинок, гарда, рукоять, навершие (плоский профиль вдоль стены)."""
    if along == "z":
        p.prism_zy([(z - 0.18, y0 + 0.5), (z, y0), (z + 0.18, y0 + 0.5), (z + 0.18, y1 - 1.2), (z - 0.18, y1 - 1.2)], x - 0.05 + d, x + 0.05 + d, "D8DCE4")
        p.box(x - 0.08 + d, x + 0.08 + d, y1 - 1.3, y1 - 1.1, z - 0.7, z + 0.7, GOLD)
        p.box(x - 0.08 + d, x + 0.08 + d, y1 - 1.1, y1 - 0.25, z - 0.1, z + 0.1, WOOD2)
        p.prism_zy(K.ngon(z, y1 - 0.15, 0.2, 6), x - 0.1 + d, x + 0.1 + d, GOLD)
    else:
        p.prism_xy([(x - 0.18, y0 + 0.5), (x, y0), (x + 0.18, y0 + 0.5), (x + 0.18, y1 - 1.2), (x - 0.18, y1 - 1.2)], z - 0.05, z + 0.05, "D8DCE4")
        p.box(x - 0.7, x + 0.7, y1 - 1.3, y1 - 1.1, z - 0.08, z + 0.08, GOLD)
        p.box(x - 0.1, x + 0.1, y1 - 1.1, y1 - 0.25, z - 0.08, z + 0.08, WOOD2)
        p.prism_xy(K.ngon(x, y1 - 0.15, 0.2, 6), z - 0.1, z + 0.1, GOLD)


def armour(p, x, z, face):
    """Доспехи на стойке: подставка, ноги, кираса, наплечники, шлем с плюмажем (face — ±1 по x, куда смотрит)."""
    p.box(x - 0.8, x + 0.8, 0.0, 0.3, z - 0.8, z + 0.8, WOOD2)
    for e in (-1, 1):
        p.box(x - 0.3, x + 0.3, 0.3, 3.0, z + e * 0.35 - 0.22, z + e * 0.35 + 0.22, "C8CCD4")
    p.prism_zy([(z - 0.75, 3.0), (z + 0.75, 3.0), (z + 0.85, 5.2), (z - 0.85, 5.2)], x - 0.45, x + 0.45, "D8DCE4")
    for e in (-1, 1):
        p.prism_xz(K.octa(x, z + e * 0.95, 0.4, 0.4, 0.15), 4.7, 5.3, "C8CCD4")
        p.box(x - 0.2, x + 0.2, 3.2, 4.8, z + e * 1.0 - 0.18, z + e * 1.0 + 0.18, "C8CCD4")
    p.prism_xz(K.ngon(x, z, 0.5, 8), 5.3, 6.4, "D8DCE4")
    p.box(x + face * 0.42, x + face * 0.52, 5.8, 5.95, z - 0.3, z + 0.3, IRON)
    p.prism_xz(K.octa(x, z, 0.18, 0.4, 0.06), 6.4, 7.0, RED)


def merlons(p, axis, fixed, out, a0, a1, y0, step=2.0):
    """Зубцы стены: через один, на всю ширину a0…a1."""
    k = 0
    a = a0
    while a + step * 0.5 <= a1 + 1e-6:
        slab(p, axis, fixed, out, 1.4, a, min(a + step * 0.6, a1), y0, y0 + 1.0, STONE3)
        a += step
        k += 1


# ══ ФАСАД: замок ══════════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, STONE, STONE2, WOOD2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, GRASS)
    slab(FR, axis, fixed, out, 1.6, -half - 0.4, half + 0.4, -0.1, 1.4, DSTONE)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.4, 17.0, STONE)
    for r in range(5):  # пояса из крупных камней
        y = 2.0 + 3.0 * r
        off = 1.5 if r % 2 else 0.0
        for k in range(int(2 * half // 3.0) + 1):
            a = -half + off + 3.0 * k
            if a + 2.9 > half:
                break
            if (k + r) % 3 == 0:
                slab(FR, axis, fixed, out, 1.02, a + 0.05, a + 2.95, y + 0.05, y + 0.95, (STONE2, STONE3)[(k + r) % 2])
    slab(FR, axis, fixed, out, 1.9, -half - 0.4, half + 0.4, 16.4, 17.0, STONE3)
    for k in range(int(2 * half // 2.4)):  # машикули — консоли под парапетом
        a = -half + 1.0 + 2.4 * k
        slab(FS, axis, fixed, out, 1.8, a - 0.3, a + 0.3, 15.6, 16.4, DSTONE)
    slab(FR, axis, fixed, out, 1.2, -half, half, 17.0, 17.9, STONE2)
    merlons(FR, axis, fixed, out, -half + 0.2, half - 0.2, 17.9, 2.4)
    slab(FR, axis, fixed, out, 0.88, -half, half, 17.0, 18.9, STONE2)
    if axis == "x":  # бока: контрфорсы, бойницы, плющ
        for z in (-8.0, 2.0, 11.0):
            slab(FR, axis, fixed, out, 2.4, z - 0.9, z + 0.9, 1.4, 12.0, STONE2)
            B.chamfer(FR, "x", fixed, out, z - 0.9, z + 0.9, [(0.88, 12.0), (2.4, 12.0), (0.88, 14.0)], STONE2)
        for z in (-12.0, -3.0, 6.5):
            slab(FS, axis, fixed, out, 0.95, z - 0.25, z + 0.25, 8.0, 11.0, IRON)
        for k in range(6):
            z = -14.0 + 2.4 * k + (0 if fixed < 0 else 10.0)
            if z > 15.0:
                continue
            D.bush(FS, fixed + out * 1.3, z, 2.0 + 1.4 * (k % 3), 0.75, IVY, "3A7A30")
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# угловые башни фасада
for s in (-1, 1):
    tx, tz = s * (FX + 1.6), -FZ - 1.6
    FR.prism_xz(K.ngon(tx, tz, 2.5, 12), -1.0, 17.2, STONE2)
    FR.prism_xz(K.ngon(tx, tz, 2.9, 12), 17.2, 17.9, STONE3)
    for k in range(12):
        if k % 2 == 0:
            t0, t1 = 2 * math.pi * k / 12, 2 * math.pi * (k + 1) / 12
            FS.prism_xz([(tx + 2.2 * math.cos(t0), tz + 2.2 * math.sin(t0)), (tx + 2.9 * math.cos(t0), tz + 2.9 * math.sin(t0)),
                         (tx + 2.9 * math.cos(t1), tz + 2.9 * math.sin(t1)), (tx + 2.2 * math.cos(t1), tz + 2.2 * math.sin(t1))], 17.9, 18.9, STONE3)
    for r in range(4):
        ring_y(FS, tx, tz, 2.45, 2.6, 2.0 + 4.0 * r, 2.4 + 4.0 * r, STONE3, n=12, a0=0, a1=360)
    for y in (6.5, 12.0):
        a = math.radians(-90 - s * 35)
        cx, cz = tx + 2.5 * math.cos(a), tz + 2.5 * math.sin(a)
        FS.box(cx - 0.25, cx + 0.25, y, y + 2.4, cz - 0.25, cz + 0.25, IRON)
# надвратная башня
FR.box(-6.0, 6.0, 1.4, 17.0, -FZ - 2.6, -FZ - 0.88, STONE3)
for k in range(5):
    x = -5.0 + 2.5 * k
    FS.box(x - 0.3, x + 0.3, 15.6, 16.6, -FZ - 3.4, -FZ - 2.6, DSTONE)
FR.box(-6.4, 6.4, 16.6, 17.6, -FZ - 3.5, -FZ - 0.88, STONE2)
for k in range(5):
    if k % 2 == 0:
        x = -6.0 + 2.6 * k
        FS.box(x, x + 1.6, 17.6, 18.9, -FZ - 3.5, -FZ - 2.7, STONE3)
arch = [(-3.4, 0.0), (3.4, 0.0), (3.4, 5.6), (2.4, 7.4), (0.0, 8.6), (-2.4, 7.4), (-3.4, 5.6)]
inner = [(-2.8, 0.0), (2.8, 0.0), (2.8, 5.4), (2.0, 6.9), (0.0, 7.9), (-2.0, 6.9), (-2.8, 5.4)]
FS.frame_xy(arch, inner, -FZ - 2.9, -FZ - 2.6, STONE3)
FS.prism_xy(inner, -FZ - 2.64, -FZ - 2.6, "2A2622")
for k in range(6):  # решётка приподнята
    x = -2.5 + 1.0 * k
    FS.box(x - 0.1, x + 0.1, 4.6, 7.6, -FZ - 2.78, -FZ - 2.66, IRON)
    taper(FS, (x, 4.6, -FZ - 2.72), (x, 4.0, -FZ - 2.72), 0.2, 0.04, IRON)
for y in (5.2, 6.2, 7.2):
    FS.box(-2.8, 2.8, y, y + 0.16, -FZ - 2.8, -FZ - 2.66, IRON)
# ров и опущенный мост на цепях
FQ.box(-5.4, 5.4, -0.5, -0.12, -FZ - 2.88, -FZ - 0.9, WATER)
FS.box(-2.8, 2.8, -0.1, 0.3, -FZ - 6.6, -FZ - 2.6, WOOD)
for k in range(8):
    z = -FZ - 6.5 + 0.5 * k
    FS.box(-2.85, 2.85, 0.3, 0.34, z, z + 0.08, WOOD2)
for e in (-1, 1):
    FS.box(e * 2.6 - 0.12, e * 2.6 + 0.12, 0.3, 0.5, -FZ - 6.6, -FZ - 2.6, IRON)
    D.chain(FS, (e * 2.6, 0.5, -FZ - 6.4), (e * 3.0, 8.0, -FZ - 2.8), 8, 0.12, IRON, sag=0.3)
# щит и скрещённые мечи над аркой, знамёна, факелы
shield(FS.prism_xy, 0.0, 11.6, 2.0, -FZ - 2.6, -1)
for e in (-1, 1):
    beam(FS, (e * 2.6, 9.4, -FZ - 2.75), (-e * 2.6, 14.4, -FZ - 2.75), 0.3, 0.12, "D8DCE4")
    FS.box(e * 2.6 - 0.5, e * 2.6 + 0.5, 9.0, 9.6, -FZ - 2.85, -FZ - 2.65, GOLD)
for x in (-8.6, 8.6):
    FS.box(x - 1.4, x + 1.4, 15.0, 15.3, -FZ - 1.4, -FZ - 0.88, WOOD2)
    for r in range(6):
        for c in range(2):
            FS.box(x - 1.2 + 1.2 * c, x + 1.2 * c, 13.8 - 1.1 * r, 14.9 - 1.1 * r, -FZ - 1.2, -FZ - 1.0, (RED, WHITE)[(r + c) % 2])
    FS.prism_xy([(x - 1.2, 8.3), (x + 1.2, 8.3), (x, 7.3)], -FZ - 1.2, -FZ - 1.0, RED)
for x in (-4.4, 4.4):
    FS.box(x - 0.15, x + 0.15, 5.0, 5.3, -FZ - 3.4, -FZ - 2.6, IRON)
    D.torch(FS, FG, x, 4.6, -FZ - 3.3, 0.6)
# ряд бойниц по фасаду
for x in (-14.4, -12.0, -9.6, 11.0, 13.4):
    FS.box(x - 0.25, x + 0.25, 7.0, 11.0, -FZ - 0.96, -FZ - 0.88, IRON)
    FS.box(x - 0.6, x + 0.6, 6.6, 7.0, -FZ - 1.3, -FZ - 0.88, STONE3)
# тренировочное чучело, стойка с копьями, сено, бочка
dx, dz = -11.0, -FZ - 5.6
FS.box(dx - 0.15, dx + 0.15, 0.0, 5.2, dz - 0.15, dz + 0.15, WOOD2)
FS.box(dx - 2.0, dx + 2.0, 3.8, 4.1, dz - 0.15, dz + 0.15, WOOD2)
FS.prism_xz(K.octa(dx, dz, 0.9, 0.7, 0.3), 2.2, 4.6, STRAW)
FS.prism_xz(K.ngon(dx, dz, 0.55, 8), 4.6, 5.6, STRAW)
shield(FS.prism_xy, dx, 3.6, 0.8, dz - 0.7, -1)
FS.box(9.0, 15.0, 0.0, 0.3, -FZ - 6.0, -FZ - 5.4, WOOD2)
FS.box(9.0, 15.0, 3.0, 3.3, -FZ - 6.0, -FZ - 5.4, WOOD2)
for x in (9.2, 14.8):
    FS.box(x - 0.15, x + 0.15, 0.0, 3.3, -FZ - 6.0, -FZ - 5.4, WOOD2)
for k in range(6):
    x = 9.8 + 0.95 * k
    FS.box(x - 0.07, x + 0.07, 0.3, 6.2, -FZ - 5.75, -FZ - 5.65, WOOD)
    taper(FS, (x, 6.2, -FZ - 5.7), (x, 7.0, -FZ - 5.7), 0.28, 0.02, "D8DCE4")
for k, (x, z, y) in enumerate(((-16.0, -FZ - 4.2, 0.0), (-14.0, -FZ - 4.2, 0.0), (-15.0, -FZ - 4.2, 1.2))):
    FS.box(x - 1.0, x + 1.0, y, y + 1.2, z - 0.7, z + 0.7, STRAW)
    FS.box(x - 1.02, x + 1.02, y + 0.5, y + 0.7, z - 0.72, z + 0.72, "B89850")
D.barrel(FS, 16.4, -FZ - 4.2, 0.0, 0.8, 1.7, WOOD, IRON)
# тыл: колодец
ring_y(FS, -6.0, FZ + 3.0, 1.2, 1.7, 0.0, 1.6, STONE2, n=12)
for e in (-1, 1):
    FS.box(-6.0 + e * 1.5 - 0.15, -6.0 + e * 1.5 + 0.15, 1.6, 4.4, FZ + 2.85, FZ + 3.15, WOOD2)
FS.prism_xy([(-8.0, 4.2), (-4.0, 4.2), (-6.0, 5.6)], FZ + 1.8, FZ + 4.2, RED2)

# ══ ИНТЕРЬЕР: рыцарский зал ═══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), STONE2)
for i in range(-6, 6):  # плиты пола
    for j in range(-6, 6):
        if rng(i, j) > 0.55:
            IQ.box(2.8 * i + 0.06, 2.8 * i + 2.74, 0.02, 0.05, 2.65 * j + 0.06, 2.65 * j + 2.59, (STONE, DSTONE, STONE3)[(i * 7 + j) % 3])
IQ.box(-1.6, 1.6, 0.05, 0.08, 1.2, ZB - 0.88, RED)  # дорожка от лифта
IQ.box(-1.8, 1.8, 0.04, 0.07, 1.2, ZB - 0.88, GOLD)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, STONE)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 1.0, DSTONE)
        for r in range(4):
            y = 2.0 + 3.6 * r
            for k in range(int((a1 - a0) // 3.2)):
                a = a0 + 0.2 + 3.2 * k + (1.6 if r % 2 else 0.0)
                if a + 3.0 > a1 or (k + r) % 2:
                    continue
                slab(IR, axis, fixed, out, 0.98, a, a + 3.0, y, y + 1.2, (STONE2, STONE3)[k % 2])
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, STONE)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, RED)
    slab(IR, axis, fixed, out, 1.4, -half, half, 15.0, 15.6, WOOD2)
# галереи на столбах по бокам, под ними — доспехи и оружие
for s in (-1, 1):
    gx = s * (W - 2.4)
    IS.box(*sorted((s * W, gx)), 8.4, 8.9, -14.0, 7.0, WOOD2)
    IS.box(*sorted((gx, gx + s * 0.2)), 8.9, 10.0, -14.0, 7.0, WOOD)
    for k in range(13):
        z = -13.6 + 1.7 * k
        IS.box(gx - 0.08, gx + 0.08, 8.9, 10.0, z - 0.08, z + 0.08, WOOD)
    for z in (-13.6, -6.6, 0.4, 6.6):
        IS.box(gx - 0.3, gx + 0.3, 0.0, 8.4, z - 0.3, z + 0.3, WOOD2)
        beam(IS, (gx, 6.8, z), (gx + s * 1.8, 8.4, z), 0.25, 0.25, WOOD2)
    for z in (-10.0, -3.2):
        armour(IS, s * (W - 1.6), z, -s)
    for k in range(4):  # стойка мечей
        sword(IS, s * (W - 0.98), 2.0, 6.0, 3.0 + 0.8 * k, along="z")
    for k in range(3):  # знамёна на галерее
        z = -11.0 + 7.0 * k
        IS.box(*sorted((gx + s * 0.22, gx + s * 0.3)), 4.4, 8.9, z - 1.0, z + 1.0, (RED, BLUE, RED)[k])
        IS.prism_zy([(z - 1.0, 4.4), (z + 1.0, 4.4), (z, 3.6)], *sorted((gx + s * 0.22, gx + s * 0.3)), (RED, BLUE, RED)[k])
        IS.prism_zy([(z - 0.4, 6.0), (z + 0.4, 6.0), (z + 0.4, 7.4), (z, 7.8), (z - 0.4, 7.4)], *sorted((gx + s * 0.3, gx + s * 0.34)), GOLD)
# камин у дальней стены с огнём и гербом
for e in (-1, 1):
    IR.box(*sorted((e * 3.6, e * 5.2)), 0.0, 7.0, ZF + 0.88, ZF + 3.0, STONE3)
IR.box(-3.6, 3.6, 4.6, 7.0, ZF + 0.88, ZF + 3.0, STONE3)
IS.box(-3.6, 3.6, 0.0, 4.6, ZF + 0.88, ZF + 1.0, "2A2622")
IS.box(-3.6, 3.6, 0.0, 0.3, ZF + 1.0, ZF + 3.0, DSTONE)
IG.prism_xy([(-2.4, 0.3), (2.4, 0.3), (1.6, 2.2), (0.6, 1.4), (0.0, 3.0), (-0.8, 1.6), (-1.8, 2.4)], ZF + 1.5, ZF + 1.6, "FF8A30")
IG.prism_xy([(-1.2, 0.3), (1.2, 0.3), (0.4, 1.6), (0.0, 1.0), (-0.5, 1.8)], ZF + 1.62, ZF + 1.7, "FFD060")
for k in range(3):
    IS.prism_xy(K.ngon(-1.4 + 1.4 * k, 0.6, 0.35, 7), ZF + 1.8, ZF + 2.8, "8A5A34")
IR.box(-6.0, 6.0, 7.0, 8.0, ZF + 0.88, ZF + 3.6, STONE2)
IR.loft([(-5.0, 8.0, ZF + 0.88), (5.0, 8.0, ZF + 0.88), (5.0, 8.0, ZF + 3.2), (-5.0, 8.0, ZF + 3.2)],
        [(-3.0, 14.0, ZF + 0.88), (3.0, 14.0, ZF + 0.88), (3.0, 14.0, ZF + 1.8), (-3.0, 14.0, ZF + 1.8)], STONE)
shield(IS.prism_xy, 0.0, 11.2, 1.7, ZF + 1.8, 1)
for e in (-1, 1):
    beam(IS, (e * 2.4, 8.6, ZF + 2.0), (-e * 2.6, 13.8, ZF + 2.0), 0.16, 0.16, WOOD)
    taper(IS, (-e * 2.6, 13.8, ZF + 2.0), (-e * 3.0, 14.6, ZF + 2.0), 0.4, 0.04, "D8DCE4")
# фермы, знамёна под потолком, люстра-колесо
for k in range(-3, 4):
    z = 4.4 * k
    IS.box(-W, W, C - 1.4, C - 0.9, z - 0.3, z + 0.3, WOOD2)
    for e in (-1, 1):
        beam(IS, (e * 6.0, C - 1.15, z), (0.0, C - 0.2, z), 0.4, 0.4, WOOD2)
for k, (x, z) in enumerate(((-7.0, -8.8), (7.0, -8.8), (-7.0, 4.4), (7.0, 4.4))):
    IS.box(x - 1.1, x + 1.1, 11.2, C - 1.4, z - 0.05, z + 0.05, (BLUE, RED)[k % 2])
    IS.prism_xy([(x - 1.1, 11.2), (x + 1.1, 11.2), (x, 10.2)], z - 0.05, z + 0.05, (BLUE, RED)[k % 2])
    IS.prism_xy([(x - 1.1, 13.8), (x, 12.8), (x + 1.1, 13.8), (x + 1.1, 13.3), (x, 12.3), (x - 1.1, 13.3)], z - 0.08, z + 0.08, WHITE)
ring_y(IS, 0.0, -3.0, 2.6, 3.0, C - 4.6, C - 4.3, WOOD2, n=14)
for k in range(8):
    t = 2 * math.pi * k / 8
    IS.prism_xz(K.ngon(2.8 * math.cos(t), -3.0 + 2.8 * math.sin(t), 0.14, 6), C - 4.3, C - 3.8, "F2EEDC")
    IG.prism_xz(K.ngon(2.8 * math.cos(t), -3.0 + 2.8 * math.sin(t), 0.1, 6), C - 3.8, C - 3.5, "FFC860")
for k in range(4):
    t = math.pi / 2 * k + math.pi / 4
    IS.box(2.8 * math.cos(t) - 0.04, 2.8 * math.cos(t) + 0.04, C - 4.3, C - 1.4, -3.0 + 2.8 * math.sin(t) - 0.04, -3.0 + 2.8 * math.sin(t) + 0.04, IRON)
# помост-постамент
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.3, 16), 0.0, 0.6, STONE3)
IR.prism_xz(K.ngon(px, pz, 3.7, 16), 0.6, TOP - 0.12, STONE)
IS.prism_xz(K.ngon(px, pz, 3.5, 16), TOP - 0.12, TOP, RED)
ring_y(IS, px, pz, 3.5, 3.75, TOP - 0.14, TOP + 0.02, GOLD, n=16)
B.lift_leaves(IS, WOOD2, GOLD)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 17.9, -FZ, FZ, STONE)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, GRASS)
SL.box(-6.4, 6.4, 1.4, 18.9, -FZ - 3.5, -FZ, STONE3)
for s in (-1, 1):
    SL.prism_xz(K.ngon(s * (FX + 1.6), -FZ - 1.6, 2.7, 8), -1.0, 18.9, STONE2)
SL.box(-2.8, 2.8, -0.1, 0.3, -FZ - 6.6, -FZ - 2.6, WOOD)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 2400, (1.0, 0.88, 0.72)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.95, 0.85)),
                                                   ("Fire", (0, 3, ZF + 5), 1200, (1.0, 0.6, 0.3))])
