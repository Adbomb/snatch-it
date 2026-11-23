"""Этаж «Фенек-загадочник» музея-небоскрёба (восьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — клуб загадок и шахмат. Снаружи — кремовый особняк: цоколь шахматной клеткой из чёрных и белых
плит, высокие окна в тёмно-зелёных рамах, наверху — зубчатый парапет как у шахматной ладьи; у входа под зелёным
навесом — огромные фигуры: ладья и король по сторонам двери, ряд пешек вдоль тротуара, над входом — золотая
эмблема-пазл; на боках — тот же ритм окон и клетки. Внутри — зал-доска: весь пол вокруг постамента — огромная
шахматная доска с фигурами-статуями в разгар партии (ладьи, слоны, ферзь, пешки), по стенам — шкафы с коробками
головоломок, столики с маленькими досками и стульями, лампы с зелёными абажурами, кубики-головоломки на полках;
экспонат — на квадратной тумбе с клеткой на крышке.
Запуск: blender --background --factory-startup --python scripts/blender/floor_chess.py -- <репо> <превью>
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

CREAM, CREAM2, BLACK, WHITE, GREEN, GREEN2 = "EDE3CC", "D8CBB0", "2A2A30", "F2F0EA", "2E6A4A", "1E4A34"
GOLD, WOOD, WOOD2, GLASS, IVORY, EBONY = "D8A83A", "8A5A34", "5A3A22", "FFE8B0", "EEE6D6", "34303A"
PUZZLE = ("E8483A", "3A8AE8", "F0C020", "4AB04A")

F = B.Floor("CS", "FennecRiddler", quiet=("C8C0B0", BLACK, WHITE), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def base(p, x, z, y, r, col):
    p.prism_xz(K.ngon(x, z, r, 12), y, y + 0.35 * r, col)
    p.prism_xz(K.ngon(x, z, r * 0.8, 12), y + 0.35 * r, y + 0.5 * r, col)


def pawn(p, x, z, y, s, col):
    """Пешка: основание, столбик, воротник, шар."""
    base(p, x, z, y, 0.9 * s, col)
    p.prism_xz(K.ngon(x, z, 0.45 * s, 10), y + 0.45 * s, y + 1.4 * s, col)
    p.prism_xz(K.ngon(x, z, 0.65 * s, 10), y + 1.4 * s, y + 1.55 * s, col)
    p.prism_xz(K.octa(x, z, 0.55 * s, 0.55 * s, 0.2 * s), y + 1.55 * s, y + 2.4 * s, col)


def rook(p, x, z, y, s, col):
    """Ладья: основание, башня, зубцы."""
    base(p, x, z, y, 1.0 * s, col)
    p.prism_xz(K.ngon(x, z, 0.6 * s, 10), y + 0.5 * s, y + 2.4 * s, col)
    p.prism_xz(K.ngon(x, z, 0.85 * s, 10), y + 2.4 * s, y + 2.9 * s, col)
    for k in range(5):
        a = 2 * math.pi * k / 5
        xx, zz = x + 0.68 * s * math.cos(a), z + 0.68 * s * math.sin(a)
        p.box(xx - 0.16 * s, xx + 0.16 * s, y + 2.9 * s, y + 3.3 * s, zz - 0.16 * s, zz + 0.16 * s, col)


def bishop(p, x, z, y, s, col):
    """Слон: основание, столбик, воротник, капля с прорезью, шарик."""
    base(p, x, z, y, 0.95 * s, col)
    p.prism_xz(K.ngon(x, z, 0.45 * s, 10), y + 0.48 * s, y + 1.9 * s, col)
    p.prism_xz(K.ngon(x, z, 0.65 * s, 10), y + 1.9 * s, y + 2.05 * s, col)
    p.loft([(x + 0.55 * s * math.cos(a), y + 2.05 * s, z + 0.55 * s * math.sin(a)) for a in [2 * math.pi * k / 8 for k in range(8)]],
           [(x + 0.25 * s * math.cos(a), y + 3.0 * s, z + 0.25 * s * math.sin(a)) for a in [2 * math.pi * k / 8 for k in range(8)]], col)
    p.prism_xz(K.ngon(x, z, 0.15 * s, 6), y + 3.0 * s, y + 3.3 * s, col)


def king(p, x, z, y, s, col, cross=GOLD):
    """Король: высокое тело, корона-воротник, крест."""
    base(p, x, z, y, 1.1 * s, col)
    p.loft([(x + 0.6 * s * math.cos(a), y + 0.55 * s, z + 0.6 * s * math.sin(a)) for a in [2 * math.pi * k / 10 for k in range(10)]],
           [(x + 0.4 * s * math.cos(a), y + 2.8 * s, z + 0.4 * s * math.sin(a)) for a in [2 * math.pi * k / 10 for k in range(10)]], col)
    p.prism_xz(K.ngon(x, z, 0.75 * s, 10), y + 2.8 * s, y + 3.0 * s, col)
    p.prism_xz(K.ngon(x, z, 0.6 * s, 10), y + 3.0 * s, y + 3.6 * s, col)
    p.box(x - 0.1 * s, x + 0.1 * s, y + 3.6 * s, y + 4.5 * s, z - 0.1 * s, z + 0.1 * s, cross)
    p.box(x - 0.35 * s, x + 0.35 * s, y + 4.0 * s, y + 4.2 * s, z - 0.1 * s, z + 0.1 * s, cross)


def queen(p, x, z, y, s, col):
    """Ферзь: тело, корона зубчиками, шарик."""
    base(p, x, z, y, 1.05 * s, col)
    p.loft([(x + 0.55 * s * math.cos(a), y + 0.55 * s, z + 0.55 * s * math.sin(a)) for a in [2 * math.pi * k / 10 for k in range(10)]],
           [(x + 0.35 * s * math.cos(a), y + 2.6 * s, z + 0.35 * s * math.sin(a)) for a in [2 * math.pi * k / 10 for k in range(10)]], col)
    p.prism_xz(K.ngon(x, z, 0.7 * s, 10), y + 2.6 * s, y + 2.8 * s, col)
    for k in range(8):
        a = 2 * math.pi * k / 8
        taper(p, (x + 0.5 * s * math.cos(a), y + 2.8 * s, z + 0.5 * s * math.sin(a)),
              (x + 0.62 * s * math.cos(a), y + 3.3 * s, z + 0.62 * s * math.sin(a)), 0.18 * s, 0.06 * s, col)
    p.prism_xz(K.octa(x, z, 0.22 * s, 0.22 * s, 0.08 * s), y + 3.2 * s, y + 3.6 * s, GOLD)


def puzzle_piece(p, cx, cy, z0, z1, s, col):
    """Деталь пазла (вид спереди): квадрат с выступом сверху и справа, выемка слева."""
    p.prism_xy(K.rect(cx - s, cx + s, cy - s, cy + s), z0, z1, col)
    p.prism_xy(K.ngon(cx, cy + s + 0.3 * s, 0.38 * s, 10), z0, z1, col)
    p.prism_xy(K.ngon(cx + s + 0.3 * s, cy, 0.38 * s, 10), z0, z1, col)


def puzzle_cube(p, x, y, z, s=0.5):
    """Кубик-головоломка: 2 × 2 разноцветные грани."""
    for i in range(2):
        for j in range(2):
            for k in range(2):
                p.box(x - s + s * i, x + s * i, y + s * j, y + s * (j + 1), z - s + s * k, z + s * k, PUZZLE[(i + j + k) % 4])


# ══ ФАСАД: клуб загадок ═══════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, CREAM, CREAM, "3A3434")
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "C8C0B0")
    slab(FR, axis, fixed, out, 0.88, -half, half, -0.1, 16.4, CREAM)
    n = int(2 * half // 2.0)
    for k in range(n):  # цоколь шахматной клеткой в два ряда
        a = -half + (2 * half - 2.0 * n) / 2 + 2.0 * k
        for r in range(2 if fi == 0 else 1):  # спереди два ряда клетки, на боках и сзади — один
            col = BLACK if (k + r) % 2 == 0 else WHITE
            slab(FR, axis, fixed, out, 1.18, a, a + 2.0, 0.0 + 2.0 * r, 2.0 + 2.0 * r, col)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, 4.0, 4.5, GREEN2)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, 15.8, 16.4, GREEN2)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, 16.4, 17.4, CREAM2)
    for k in range(int(2 * half // 3.0) + 1):  # зубцы парапета «ладьи»
        a = -half - 0.3 + 3.0 * k
        if a + 1.8 <= half + 0.3:
            slab(FR, axis, fixed, out, 1.38, a, a + 1.8, 17.4, 18.9, CREAM2)
    wins = (-12.0, -6.0, 6.0, 12.0) if fi == 0 else (-12.0, -6.0, 0.0, 6.0, 12.0)
    for a in wins:  # высокие окна в зелёных рамах
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
        f0, f1 = sorted((fixed + out * 0.88, fixed + out * 1.15))
        pr, fr = (FG.prism_zy, FS.frame_zy) if axis == "x" else (FG.prism_xy, FS.frame_xy)
        top = 14.6
        pr(K.rect(a - 1.2, a + 1.2, 6.0, top), d0, d1, GLASS)
        fr(K.rect(a - 1.5, a + 1.5, 5.7, top + 0.3), K.rect(a - 1.2, a + 1.2, 6.0, top), f0, f1, GREEN)
        slab(FS, axis, fixed, out, 1.1, a - 1.2, a + 1.2, 10.2, 10.35, GREEN)
        slab(FS, axis, fixed, out, 1.1, a - 0.06, a + 0.06, 6.0, top, GREEN)
        slab(FR, axis, fixed, out, 1.3, a - 1.8, a + 1.8, 5.3, 5.7, CREAM2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# вход: дверь, зелёный навес, латунные фонари, эмблема-пазл
FS.box(-2.6, 2.6, 0.0, 9.0, -FZ - 1.3, -FZ - 0.88, GREEN2)
FS.box(-2.0, 2.0, 0.0, 8.0, -FZ - 1.4, -FZ - 1.3, WOOD2)
FS.box(-0.05, 0.05, 0.0, 8.0, -FZ - 1.44, -FZ - 1.4, GOLD)
FG.box(-1.6, 1.6, 6.0, 7.6, -FZ - 1.44, -FZ - 1.4, GLASS)
FS.box(-1.2, -0.8, 3.6, 4.0, -FZ - 1.5, -FZ - 1.4, GOLD)
FS.loft([(-4.4, 9.4, -FZ - 0.9), (4.4, 9.4, -FZ - 0.9), (4.4, 9.6, -FZ - 0.9), (-4.4, 9.6, -FZ - 0.9)],
        [(-4.4, 8.6, -FZ - 3.0), (4.4, 8.6, -FZ - 3.0), (4.4, 8.8, -FZ - 3.0), (-4.4, 8.8, -FZ - 3.0)], GREEN)
FS.box(-4.5, 4.5, 8.4, 8.62, -FZ - 3.1, -FZ - 2.9, GOLD)
puzzle_piece(FS, -0.4, 12.4, -FZ - 1.1, -FZ - 0.88, 1.3, GOLD)
FS.frame_xy(K.rect(-3.0, 3.0, 10.2, 14.8), K.rect(-2.7, 2.7, 10.5, 14.5), -FZ - 1.1, -FZ - 0.88, GREEN)
for e in (-1, 1):
    FS.box(e * 3.3 - 0.06, e * 3.3 + 0.06, 6.0, 7.4, -FZ - 1.6, -FZ - 0.88, "2A2A2A")
    D.lantern(FS, FG, e * 3.3, 5.2, -FZ - 1.6, s=0.8, cap="2A2A2A", light=GLASS)
for k in range(3):
    FS.box(-3.2 + 0.3 * k, 3.2 - 0.3 * k, -0.1, 0.2 + 0.25 * k, -FZ - 2.6 + 0.5 * k, -FZ - 0.88, "B8B0A0")
# огромные фигуры у входа: ладья и король, ряд пешек
F.objects(True)
rook(FS, -7.0, -FZ - 1.9, -0.1, 2.0, IVORY)
king(FS, 7.2, -FZ - 1.9, -0.1, 1.9, EBONY)
for k, x in enumerate((-16.8, -13.8, -10.8, 10.8, 13.8, 16.8)):
    pawn(FS, x, -FZ - 1.9, -0.1, 1.3, IVORY if x < 0 else EBONY)
F.objects(False)

# ══ ИНТЕРЬЕР: зал-доска ═══════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.1
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "8A6A48")
SQ = 2.4
for i in range(8):  # огромная доска 8 × 8 вокруг постамента
    for j in range(8):
        x0, z0 = -4 * SQ + SQ * i, -3.0 - 4 * SQ + SQ * j
        IQ.box(x0, x0 + SQ, 0.02, 0.06, z0, z0 + SQ, WHITE if (i + j) % 2 else BLACK)
IS.frame_xz(K.rect(-4 * SQ - 0.5, 4 * SQ + 0.5, -3.0 - 4 * SQ - 0.5, -3.0 + 4 * SQ + 0.5), K.rect(-4 * SQ, 4 * SQ, -3.0 - 4 * SQ, -3.0 + 4 * SQ),
            0.02, 0.1, WOOD2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, "2E5A44")
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 3.2, WOOD)
        slab(IS, axis, fixed, out, 1.05, a0, a1, 3.2, 3.4, GOLD)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, "2E5A44")
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, WOOD2)
    slab(IR, axis, fixed, out, 1.4, -half, half, 15.6, 16.4, CREAM)
    slab(IS, axis, fixed, out, 1.45, -half, half, 16.4, 16.6, GOLD)
for k in range(-3, 4):
    IS.box(-W, W, C - 0.6, C - 0.2, 4.4 * k - 0.25, 4.4 * k + 0.25, WOOD2)
# фигуры-статуи на доске (в разгар партии; к лифту путь свободен)
F.objects(True)
cell = lambda i, j: (-4 * SQ + SQ * (i + 0.5), -3.0 - 4 * SQ + SQ * (j + 0.5))  # noqa: E731
for (i, j, kind, col) in ((0, 0, "rook", EBONY), (7, 0, "rook", EBONY), (2, 0, "bishop", EBONY), (5, 1, "pawn", EBONY),
                          (1, 1, "pawn", EBONY), (6, 1, "pawn", EBONY), (4, 0, "queen", EBONY),
                          (0, 6, "rook", IVORY), (7, 7, "rook", IVORY), (5, 6, "bishop", IVORY), (1, 5, "pawn", IVORY),
                          (6, 5, "pawn", IVORY), (1, 3, "pawn", IVORY)):
    x, z = cell(i, j)
    {"rook": rook, "bishop": bishop, "pawn": pawn, "queen": queen}[kind](IS, x, z, 0.06, 1.0 if kind != "pawn" else 0.9, col)
F.objects(False)
# шкафы с коробками головоломок, столики с досками и стульями, кубики
F.objects(True)
for s in (-1, 1):
    x = s * (W - 0.88)
    d0, d1 = sorted((x, x - s * 1.2))
    for z0 in (-14.4, 9.0):
        IS.box(d0, d1, 0.0, 9.0, z0, z0 + 4.6, WOOD2)
        for y in (2.0, 4.4, 6.8):
            IS.box(d0, d1, y, y + 0.15, z0 + 0.2, z0 + 4.4, WOOD)
            for k in range(4):
                zz = z0 + 0.4 + 1.0 * k
                IS.box(*sorted((x - s * 0.2, x - s * 1.0)), y + 0.15, y + 0.15 + 0.6 + 0.3 * (k % 2), zz, zz + 0.8, PUZZLE[(k + int(y)) % 4])
    for z in (-6.0, 1.0):  # столик с доской и два стула
        tx = s * (W - 3.2)
        IS.prism_xz(K.ngon(tx, z, 0.25, 8), 0.0, 2.4, WOOD2)
        IS.box(tx - 1.0, tx + 1.0, 2.4, 2.6, z - 1.0, z + 1.0, WOOD)
        for i in range(4):
            for j in range(4):
                IS.box(tx - 0.8 + 0.4 * i, tx - 0.4 + 0.4 * i, 2.6, 2.63, z - 0.8 + 0.4 * j, z - 0.4 + 0.4 * j, WHITE if (i + j) % 2 else BLACK)
        pawn(IS, tx - 0.2, z + 0.2, 2.63, 0.25, IVORY)
        king(IS, tx + 0.2, z - 0.2, 2.63, 0.2, EBONY)
        for e in (-1, 1):
            cz = z + e * 1.8
            IS.box(tx - 0.6, tx + 0.6, 1.4, 1.6, cz - 0.6, cz + 0.6, GREEN)
            IS.box(tx - 0.6, tx + 0.6, 1.6, 3.4, cz + e * 0.5 - 0.1, cz + e * 0.5 + 0.1, GREEN2)
            for f in (-1, 1):
                IS.box(tx + f * 0.5 - 0.08, tx + f * 0.5 + 0.08, 0.0, 1.4, cz - 0.08, cz + 0.08, WOOD2)
        IS.box(tx - 0.03, tx + 0.03, 6.0, C - 0.6, z - 0.03, z + 0.03, "2A2A2A")
        IS.cone([(xx, 6.0, zz) for xx, zz in K.ngon(tx, z, 0.9, 8)], (tx, 6.8, z), GREEN)
        IG.prism_xz(K.ngon(tx, z, 0.35, 6), 5.7, 6.0, GLASS)
puzzle_cube(IS, -8.4, 0.0, 8.4, s=0.6)
puzzle_cube(IS, 8.6, 0.0, 8.0, s=0.5)
F.objects(False)
# дальняя стена: огромная эмблема-пазл из четырёх деталей
for k, (dx, dy) in enumerate(((-1.4, 1.4), (1.4, 1.4), (-1.4, -1.4), (1.4, -1.4))):
    puzzle_piece(IS, dx, 10.4 + dy, ZF + 0.9, ZF + 1.1, 1.2, PUZZLE[k])
IS.frame_xy(K.rect(-4.6, 4.6, 5.6, 15.2), K.rect(-4.2, 4.2, 6.0, 14.8), ZF + 0.88, ZF + 1.2, GOLD)
# постамент: квадратная тумба с клеткой на крышке
px, pz = PED
IR.box(px - 3.0, px + 3.0, 0.06, 0.6, pz - 3.0, pz + 3.0, WOOD2)
IS.box(px - 3.1, px + 3.1, 0.6, 0.72, pz - 3.1, pz + 3.1, GOLD)
IS.box(px - 2.8, px + 2.8, 0.72, TOP - 0.04, pz - 2.8, pz + 2.8, EBONY)
for i in range(4):
    for j in range(4):
        IS.box(px - 2.8 + 1.4 * i, px - 1.4 + 1.4 * i, TOP - 0.04, TOP, pz - 2.8 + 1.4 * j, pz - 1.4 + 1.4 * j, IVORY if (i + j) % 2 else EBONY)
B.lift_leaves(IS, WOOD2, GOLD)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 17.4, -FZ, FZ, CREAM)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "C8C0B0")
SL.box(-FX - 0.3, FX + 0.3, -0.1, 4.0, -FZ - 0.3, FZ + 0.3, BLACK)
SL.box(-FX - 0.3, FX + 0.3, 15.8, 18.6, -FZ - 0.3, FZ + 0.3, CREAM2)
SL.box(-9.0, -5.0, -0.1, 6.5, -FZ - 3.0, -FZ - 0.8, IVORY)
SL.box(5.2, 9.2, -0.1, 8.4, -FZ - 3.0, -FZ - 0.8, EBONY)

F.build(exhibit=(PED[0], TOP, PED[1], 2.2), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.95, 0.85)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Emblem", (0, 9, ZF + 5), 600, (1.0, 0.9, 0.7))])
