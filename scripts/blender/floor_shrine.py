"""Этаж «Чёрная кошка-идол» музея-небоскрёба (четвёртая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — ночное святилище удачи в японском стиле. Снаружи — тёмное дерево и белая штукатурка в клетку
балок, изогнутая двускатная крыша-карниз из тёмной черепицы с золотыми концами, посередине — огромные красные
ворота-тории перед входом с раздвижными решётчатыми дверями сёдзи, светящимися изнутри; по бокам от ворот —
каменные фонари и кошки-хранители на постаментах, на фасаде — висящие красные бумажные фонари и гирлянда
с бумажными лентами, большая золотая монета-«рё» над входом; бока — цветущие сакуры, падающие лепестки, бамбук;
сзади — пруд с карпами и мостиком. Внутри — ночной сад святилища: тёмно-синее небо с полной луной, сакура с
розовой кроной, дорожка через ряд маленьких тории к алтарю, каменные фонари, горы золотых монет, бочонки-
подношения, пруд с кои, бумажные фонари на шнурах; экспонат — на алтаре из красного лака с золотым кантом.
Запуск: blender --background --factory-startup --python scripts/blender/floor_shrine.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, ring_y, rng, slab, taper, tube  # noqa: E402

WOOD, WOOD2, PLASTER, PLASTER2, ROOF, ROOF2 = "4A2E24", "3A2018", "F2EAD8", "E0D4BC", "2E3442", "3E4656"
RED, RED2, GOLD, GOLD2, STONE, STONE2 = "D8342A", "A82420", "F2C230", "D9A21A", "A8A498", "8A867C"
SAKURA, SAKURA2, BARK, BAMBOO, BAMBOO2 = "FFB8D0", "FF94BC", "5A3A2A", "7AB04A", "5A9038"
NIGHT, NIGHT2, NIGHT3, MOON, LANTERN = "141A3A", "1E2A52", "2A3A6A", "FFF4C8", "FF7A4A"
WATER, KOI, KOI2, GRAVEL, GRAVEL2, BLACK = "2A6A9A", "FF8A3A", "F4F4F4", "D8D0C0", "C4BCAA", "1E1E24"
SHOJI = "FFE8B8"

F = B.Floor("BC", "BlackCatIdol", quiet=(GRAVEL, GRAVEL2, NIGHT, NIGHT2, PLASTER2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def torii(p, x, z, w, h, along_x=True, col=RED, top=BLACK):
    """Ворота тории: два столба, нижняя балка, верхняя изогнутая (концы приподняты), подпорка по центру."""
    for e in (-1, 1):
        cx = x + e * w / 2
        p.prism_xz(K.ngon(cx, z, w * 0.06, 8), 0.0, h, col) if along_x else p.prism_xz(K.ngon(x, z + e * w / 2, w * 0.06, 8), 0.0, h, col)
    if along_x:
        p.box(x - w * 0.6, x + w * 0.6, h * 0.72, h * 0.8, z - w * 0.05, z + w * 0.05, col)
        p.prism_xy([(x - w * 0.74, h * 0.92), (x - w * 0.5, h * 0.86), (x + w * 0.5, h * 0.86), (x + w * 0.74, h * 0.92), (x + w * 0.76, h),
                    (x - w * 0.76, h)], z - w * 0.07, z + w * 0.07, top)
        p.box(x - w * 0.66, x + w * 0.66, h * 0.84, h * 0.9, z - w * 0.06, z + w * 0.06, col)
        p.box(x - w * 0.05, x + w * 0.05, h * 0.8, h * 0.86, z - w * 0.05, z + w * 0.05, col)
    else:
        p.box(x - w * 0.05, x + w * 0.05, h * 0.72, h * 0.8, z - w * 0.6, z + w * 0.6, col)
        p.prism_zy([(z - w * 0.74, h * 0.92), (z - w * 0.5, h * 0.86), (z + w * 0.5, h * 0.86), (z + w * 0.74, h * 0.92), (z + w * 0.76, h),
                    (z - w * 0.76, h)], x - w * 0.07, x + w * 0.07, top)
        p.box(x - w * 0.06, x + w * 0.06, h * 0.84, h * 0.9, z - w * 0.66, z + w * 0.66, col)


def stone_lantern(p, g, x, z, y=0.0, s=1.0):
    """Каменный фонарь торо: основание, столб, светящаяся камера, крыша-шляпа, навершие."""
    p.prism_xz(K.ngon(x, z, 0.9 * s, 6), y, y + 0.4 * s, STONE2)
    p.prism_xz(K.ngon(x, z, 0.35 * s, 6), y + 0.4 * s, y + 2.0 * s, STONE)
    p.prism_xz(K.ngon(x, z, 0.75 * s, 6), y + 2.0 * s, y + 2.3 * s, STONE2)
    g.prism_xz(K.ngon(x, z, 0.55 * s, 6), y + 2.3 * s, y + 3.1 * s, "FFD080")
    p.loft([(x + 1.2 * s * math.cos(t), y + 3.1 * s, z + 1.2 * s * math.sin(t)) for t in [2 * math.pi * k / 6 for k in range(6)]],
           [(x + 0.3 * s * math.cos(t), y + 3.8 * s, z + 0.3 * s * math.sin(t)) for t in [2 * math.pi * k / 6 for k in range(6)]], STONE)
    p.prism_xz(K.ngon(x, z, 0.22 * s, 6), y + 3.8 * s, y + 4.2 * s, STONE2)


def paper_lantern(p, g, x, y, z, s=1.0, col=LANTERN):
    """Бумажный фонарь: светящийся бочонок, тёмные крышки, кисточка."""
    p.prism_xz(K.ngon(x, z, 0.4 * s, 8), y + 1.3 * s, y + 1.45 * s, BLACK)
    g.prism_xz(K.ngon(x, z, 0.55 * s, 8), y + 0.25 * s, y + 1.3 * s, col)
    p.prism_xz(K.ngon(x, z, 0.4 * s, 8), y + 0.1 * s, y + 0.25 * s, BLACK)
    p.box(x - 0.05, x + 0.05, y - 0.5 * s, y + 0.1 * s, z - 0.05, z + 0.05, GOLD)


def sakura(p, x, z, h, s=1.0, seed=0, spread=(2.2, 1.6)):
    """Сакура: изогнутый ствол с двумя ветвями, крона из розовых гранёных облаков."""
    tube(p, [(x, 0.0, z), (x + 0.4 * s, h * 0.5, z + 0.2 * s), (x + 0.2 * s, h * 0.8, z)], [1.0 * s, 0.8 * s, 0.6 * s], 0.8 * s,
         (0, 0, 1), BARK)
    for e in (-1, 1):
        beam(p, (x + 0.2 * s, h * 0.7, z), (x + e * 2.4 * s, h * 0.92, z + 0.6 * s * e), 0.4 * s, 0.4 * s, BARK)
    for k in range(5):
        t = 2 * math.pi * k / 5 + rng(seed, k)
        cx, cz = x + spread[0] * s * math.cos(t), z + spread[1] * s * math.sin(t)
        r = (1.6 + 0.6 * rng(k, seed)) * s
        cy = h * 0.95 + 0.6 * s * rng(seed, k, 2)
        p.prism_xz(K.ngon(cx, cz, r * 0.7, 8), cy - r * 0.5, cy - r * 0.2, SAKURA2)
        p.prism_xz(K.ngon(cx, cz, r, 8), cy - r * 0.2, cy + r * 0.3, (SAKURA, SAKURA2)[k % 2])
        p.prism_xz(K.ngon(cx, cz, r * 0.6, 8), cy + r * 0.3, cy + r * 0.6, SAKURA)


def guardian_cat(p, g, x, z, y, s, face=-1):
    """Кошка-хранитель (маленькая, сидящая): тело, голова с ушками, поднятая лапка, красный бант."""
    p.box(x - 0.7 * s, x + 0.7 * s, y, y + 1.4 * s, z - 0.6 * s, z + 0.6 * s, BLACK)
    p.box(x - 0.6 * s, x + 0.6 * s, y + 1.4 * s, y + 2.4 * s, z - 0.55 * s, z + 0.55 * s, BLACK)
    for e in (-1, 1):
        p.prism_xy([(x + e * 0.6 * s, y + 2.4 * s), (x + e * 0.15 * s, y + 2.4 * s), (x + e * 0.45 * s, y + 3.0 * s)], z - 0.2 * s,
                   z + 0.2 * s, BLACK)
    p.box(x + 0.5 * s, x + 0.9 * s, y + 1.4 * s, y + 2.6 * s, z + face * 0.2 * s - 0.2 * s, z + face * 0.2 * s + 0.2 * s, BLACK)
    p.box(x - 0.72 * s, x + 0.72 * s, y + 1.3 * s, y + 1.5 * s, z - 0.62 * s, z + 0.62 * s, RED)
    p.prism_xy(K.octa(x, y + 1.25 * s, 0.22 * s, 0.22 * s, 0.09 * s), *sorted((z + face * 0.62 * s, z + face * 0.7 * s)), GOLD)


def coin(p, x, y, z, r, axis="y"):
    """Монета-«рё»: овал с квадратным отверстием (по оси y лежит, по z стоит)."""
    if axis == "y":
        p.prism_xz([(x + r * math.cos(2 * math.pi * k / 10), z + r * 1.3 * math.sin(2 * math.pi * k / 10)) for k in range(10)], y,
                   y + 0.12, GOLD)
    else:
        p.prism_xy([(x + r * math.cos(2 * math.pi * k / 12), y + r * 1.4 * math.sin(2 * math.pi * k / 12)) for k in range(12)], z - 0.2,
                   z, GOLD)
        p.prism_xy([(x + r * 0.8 * math.cos(2 * math.pi * k / 12), y + r * 1.1 * math.sin(2 * math.pi * k / 12)) for k in range(12)], z - 0.3,
                   z - 0.2, GOLD2)


# ══ ФАСАД: святилище ══════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, PLASTER, PLASTER, NIGHT)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.2, GRAVEL)
    slab(FR, axis, fixed, out, 1.88, -half - 0.4, half + 0.4, -0.2, 1.4, STONE)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.4, 14.0, PLASTER)
    for k in range(int(2 * half // 4.0) + 1):  # клетка тёмных балок
        a = -half + 4.0 * k
        if a > half:
            break
        slab(FS, axis, fixed, out, 1.1, a - 0.3, a + 0.3, 1.4, 14.0, WOOD)
    for y in (1.4, 7.4, 13.4):
        slab(FS, axis, fixed, out, 1.1, -half, half, y, y + 0.6, WOOD)
    # изогнутый карниз-крыша: ступени черепицы, концы приподняты
    for k, (d, y0, y1) in enumerate(((4.2, 14.0, 14.8), (3.2, 14.8, 15.8), (2.2, 15.8, 16.8), (1.2, 16.8, 17.8))):
        slab(FR, axis, fixed, out, d + 0.88, -half - d, half + d, y0, y1, (ROOF, ROOF2)[k % 2])
    slab(FR, axis, fixed, out, 0.88, -half, half, 17.8, 18.9, ROOF)
    slab(FS, axis, fixed, out, 5.2, -half - 4.2, half + 4.2, 14.0, 14.25, GOLD2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
for sx in (-1, 1):  # загнутые золотые концы карниза
    for sz in (-1, 1):
        taper(FS, (sx * (FX + 4.4), 14.2, sz * (FZ + 4.4)), (sx * (FX + 5.4), 16.0, sz * (FZ + 5.4)), 0.9, 0.2, GOLD)
# перед: раздвижные двери сёдзи (светятся), огромные тории, монета-«рё», фонари, кошки-хранители
FS.box(-6.0, 6.0, 1.4, 12.4, -FZ - 1.0, -FZ - 0.88, WOOD2)
FG.box(-5.6, 5.6, 1.8, 12.0, -FZ - 1.04, -FZ - 1.0, SHOJI)
for k in range(9):
    x = -5.6 + 1.4 * k
    FS.box(x - 0.1, x + 0.1, 1.8, 12.0, -FZ - 1.12, -FZ - 1.04, WOOD)
for k in range(8):
    y = 1.8 + 1.4 * k
    FS.box(-5.6, 5.6, y - 0.08, y + 0.08, -FZ - 1.12, -FZ - 1.04, WOOD)
torii(FS, 0.0, -FZ - 3.6, 16.0, 14.0)
coin(FS, 0.0, 11.2, -FZ - 4.8, 1.6, axis="z")  # перед тории, не за брусом
for s in (-1, 1):
    stone_lantern(FS, FG, s * 11.0, -FZ - 3.6, -0.2, 1.4)
    FS.box(s * 6.4 - 1.0, s * 6.4 + 1.0, -0.2, 1.6, -FZ - 5.2, -FZ - 3.2, STONE)
    guardian_cat(FS, FG, s * 6.4, -FZ - 4.2, 1.6, 1.4, -1)
for k, x in enumerate((-15.0, -10.0, 10.0, 15.0)):  # бумажные фонари под карнизом
    FS.box(x - 0.04, x + 0.04, 12.4, 14.0, -FZ - 3.0 - 0.04, -FZ - 3.0 + 0.04, BLACK)
    paper_lantern(FS, FG, x, 10.6, -FZ - 3.0, 1.4)
pts = D.chain(FS, (-16.0, 13.6, -FZ - 1.4), (16.0, 13.6, -FZ - 1.4), 12, 0.12, WOOD, 1.0)  # гирлянда-«сидэ»
for m, q in enumerate(pts[1:-1]):
    FS.prism_xy([(q[0] - 0.35, q[1]), (q[0] + 0.35, q[1]), (q[0] + 0.2, q[1] - 0.7), (q[0] + 0.4, q[1] - 1.1), (q[0] - 0.2, q[1] - 1.1),
                 (q[0] - 0.05, q[1] - 0.7)], q[2] - 0.05, q[2] + 0.05, PLASTER if m % 2 else "FFFFFF")
# бока: сакуры и бамбук
for s in (-1, 1):
    sakura(FS, s * (FX + 2.6), -8.0, 9.0, 1.2, 1 + s, spread=(0.8, 2.4))  # крона вдоль стены, не сквозь неё
    for k in range(5):
        z = 6.0 + 1.2 * k
        h = 9.0 + 3.0 * rng(k, s)
        for m in range(int(h / 2.2)):
            FS.prism_xz(K.ngon(s * (FX + 1.8), z, 0.3, 6), -0.2 + 2.2 * m, -0.2 + 2.2 * m + 2.1, (BAMBOO, BAMBOO2)[m % 2])
for k in range(16):  # падающие лепестки
    x = -FX - 3.0 + (2 * FX + 6.0) * rng(k, 71)
    y = 2.0 + 12.0 * rng(k, 72)
    z = -FZ - 1.6 - 3.0 * rng(k, 73)
    FS.prism_xz(K.octa(x, z, 0.3, 0.2, 0.08), y, y + 0.08, SAKURA)
# сзади: пруд с кои и мостик
FS.prism_xz(K.ngon(0.0, FZ + 2.6, 2.6, 10), -0.2, 0.1, STONE2)
FG.prism_xz(K.ngon(0.0, FZ + 2.6, 2.3, 10), 0.1, 0.16, WATER)
for k, (x, col) in enumerate(((-1.0, KOI), (0.8, KOI2))):
    FS.prism_xz(K.octa(x, FZ + 2.6, 0.5, 0.2, 0.08), 0.16, 0.26, col)
for k in range(5):
    t = k / 4
    FS.box(-3.2 + 6.4 * t - 0.7, -3.2 + 6.4 * t + 0.7, 0.4 + 1.2 * math.sin(math.pi * t), 0.6 + 1.2 * math.sin(math.pi * t), FZ + 1.0,
           FZ + 4.2, RED)

# ══ ИНТЕРЬЕР: ночной сад святилища ════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.6
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), GRAVEL)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 3.0, STONE)  # каменная ограда
        slab(IR, axis, fixed, out, 1.2, a0, a1, 3.0, 3.4, ROOF)
        slab(IQ, axis, fixed, out, 0.88, a0, a1, 3.4, 7.0 if not gap else DOOR[1] + 0.1, NIGHT3)
        if not gap:
            slab(IQ, axis, fixed, out, 0.88, a0, a1, 7.0, 12.0, NIGHT2)
    slab(IQ, axis, fixed, out, 0.88, -half, half, 12.0, C, NIGHT)
    if gap:
        slab(IQ, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 12.0, NIGHT2)
        torii(IS, 0.0, ZB - 1.2, 9.0, 12.4)
    if not gap:  # силуэты холмов и пагоды на горизонте
        for k in range(3):
            a = -half + 4.0 + (2 * half - 8.0) * k / 2
            pr = IS.prism_xy if axis == "z" else IS.prism_zy
            lo, hi = sorted((fixed + out * 0.9, fixed + out * 1.0))
            pr([(a - 5.0, 3.4), (a + 5.0, 3.4), (a + 2.0, 5.6), (a - 1.5, 6.4)], lo, hi, "1A2448")
for k in range(40):  # звёзды
    x = -W + 1.0 + (2 * W - 2.0) * rng(k, 81)
    z = ZF + 1.0 + (ZB - ZF - 2.0) * rng(k, 82)
    s = 0.1 + 0.12 * rng(k, 83)
    IG.box(x - s, x + s, C - 0.05, C - 0.01, z - s, z + s, MOON)
IG.prism_xy(K.ngon(-9.0, 13.6, 2.2, 16), ZF + 0.9, ZF + 0.98, MOON)  # полная луна слева от экспоната
# пагода на передней стене (силуэт справа)
for k in range(4):
    w = 3.2 - 0.6 * k
    IS.box(9.0 - w, 9.0 + w, 3.4 + 2.2 * k, 3.6 + 2.2 * k, ZF + 0.9, ZF + 1.0, "1A2448")
    IS.box(9.0 - w * 0.6, 9.0 + w * 0.6, 3.6 + 2.2 * k, 5.6 + 2.2 * k, ZF + 0.9, ZF + 1.0, "141C3A")
# дорожка через маленькие тории к алтарю
for k in range(5):
    z = 9.6 - 2.2 * k
    IQ.box(-1.4, 1.4, 0.0, 0.1, z - 0.9, z + 0.9, GRAVEL2)
torii(IS, 0.0, 4.6, 10.0, 11.0)  # высокие тории над дорожкой: экспонат виден под верхними балками
# сакура слева, пруд с кои справа, каменные фонари, бумажные фонари на шнурах
sakura(IS, -11.5, -8.0, 9.0, 1.4, 5)
sakura(IS, 12.0, 8.0, 7.0, 1.0, 9)
IS.prism_xz(K.ngon(10.5, -6.0, 4.0, 12), 0.0, 0.3, STONE2)
IG.prism_xz(K.ngon(10.5, -6.0, 3.6, 12), 0.3, 0.36, WATER)
for k, (x, z, col) in enumerate(((9.5, -7.0, KOI), (11.5, -5.0, KOI2), (10.0, -4.4, KOI))):
    IS.prism_xz(K.octa(x, z, 0.7, 0.28, 0.1), 0.36, 0.5, col)
for x, z in ((-5.6, -8.6), (5.6, -8.6), (-5.6, 3.6), (5.6, 3.6)):
    stone_lantern(IS, IG, x, z, 0.0, 1.0)
for k in range(3):
    z = -10.0 + 7.0 * k
    pts = D.chain(IS, (-W + 1.0, 14.0, z), (W - 1.0, 14.0, z), 8, 0.08, BLACK, 1.4)
    for m, q in enumerate(pts[1:-1]):
        if m % 2 == 0:
            paper_lantern(IS, IG, q[0], q[1] - 1.6, q[2], 0.9, (LANTERN, "FFD060")[(m + k) % 2])
# горы монет и бочонки-подношения у алтаря
for x, z, r in ((-6.6, -12.0, 2.0), (6.6, -12.4, 2.2), (-13.0, 2.0, 1.6)):
    for k in range(3):
        rr = r * (1 - k / 3)
        IS.prism_xz(K.ngon(x, z, rr, 10), 0.6 * k, 0.6 * (k + 1), (GOLD, GOLD2)[k % 2])
for k, x in enumerate((-3.6, -2.2, 2.2, 3.6)):
    D.barrel(IS, x, -9.4, 0.0, 0.6, 1.2, "F4EEDC" if k % 2 else RED, BLACK)
# алтарь красного лака с золотым кантом
px, pz = PED
IR.box(px - 4.2, px + 4.2, 0.0, 0.6, pz - 3.6, pz + 3.6, STONE)
IR.box(px - 3.4, px + 3.4, 0.6, TOP, pz - 2.8, pz + 2.8, RED)
IS.frame_xz(K.rect(px - 3.5, px + 3.5, pz - 2.9, pz + 2.9), K.rect(px - 3.2, px + 3.2, pz - 2.6, pz + 2.6), TOP - 0.12, TOP + 0.04, GOLD)
for e in (-1, 1):
    IS.box(px + e * 3.4 - 0.2, px + e * 3.4 + 0.2, 0.6, TOP, pz - 2.9, pz + 2.9, GOLD2)
B.lift_leaves(IS, WOOD2, RED)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, PLASTER)
SL.box(-FX - 2.9, FX + 2.9, -1.0, 1.4, -FZ - 2.9, FZ + 2.9, STONE)
SL.box(-FX - 4.2, FX + 4.2, 14.0, 15.8, -FZ - 4.2, FZ + 4.2, ROOF)
SL.box(-FX - 2.2, FX + 2.2, 15.8, 17.8, -FZ - 2.2, FZ + 2.2, ROOF2)
SL.box(-8.0, -7.0, -0.2, 14.0, -FZ - 4.0, -FZ - 3.2, RED)
SL.box(7.0, 8.0, -0.2, 14.0, -FZ - 4.0, -FZ - 3.2, RED)
SL.box(-12.0, 12.0, 12.6, 14.0, -FZ - 4.2, -FZ - 3.0, BLACK)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 2400, (0.8, 0.82, 1.0)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.95, 0.88)),
                                                   ("Lantern", (0, 8, 0), 900, (1.0, 0.6, 0.4))])
