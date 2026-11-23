"""Этаж «Золотой банан» музея-небоскрёба (вторая партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — затерянный храм в джунглях. Снаружи — ступенчатая кладка из замшелого серо-зелёного камня
(каждый ярус выступает), спереди — широкая лестница к каменным воротам под ступенчатым «ложным сводом»: створки
светлого песчаника с золотым швом и поясом, по бокам жаровни; над перемычкой — ромб с бананом по диагонали; по углам —
банановые пальмы с гроздьями, с карниза свисают лианы, справа водопад в каменную чашу, на боках резные плиты.
Внутри (v2, 2026-11-21) — зал древнего храма, который забирают джунгли: кладка рядами разной высоты с выступающими
камнями и выпавшими блоками, пилястры, ниши с урнами и золотыми гроздьями, ступенчатый «ложный свод» с пологом листьев,
корни дерева в углах, пруд с кувшинками, дорожка из плит; банан на алтаре с золотым кантом, за ним ступенчатый портал
с тёмной глубиной, по бокам стелы с золотыми поясами и жаровни.
Откат v1 — assets/concepts/tower_batch2/backup_v1/.
Запуск: blender --background --factory-startup --python scripts/blender/floor_banana.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab, taper, tube  # noqa: E402

STONE, STONE2, STONE3, DARKST = "8C9A7A", "76846A", "A2AE8E", "3A4234"
MOSS, MOSS2, LEAF, LEAF2, LEAF3 = "4C9A2E", "6AB83E", "2E8B3A", "5CC24A", "1F6A2C"
WOOD, WOOD2, BANANA, BANANA2, WATER, WATER2 = "7A5230", "5A3A20", "F7C531", "D9A21A", "3FC6E0", "8AE6F2"
FLOWER, FLOWER2, FLAME, FLAME2, ROPE = "FF5A8A", "FF9A3A", "FFC24A", "FF8A2A", "B8935A"

F = B.Floor("GB", "GoldenBanana", quiet=(MOSS, STONE2, LEAF3), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def banana_palm(p, base, h, lean=(0.0, 0.0)):
    """Банановая пальма: ствол, широкие листья дугами, жёлтая гроздь."""
    bx, by, bz = base
    lx, lz = lean
    top = (bx + lx, by + h, bz + lz)
    tube(p, [(bx, by, bz), (bx + lx * 0.4, by + h * 0.5, bz + lz * 0.4), top], [0.9, 0.75, 0.6], 0.8, (1, 0, 0), WOOD)
    for k in range(6):
        t = 2 * math.pi * (k + 0.3 * rng(k, h)) / 6
        L = 3.2 + rng(k, 3, h) * 0.8
        mid = (top[0] + math.cos(t) * L * 0.5, top[1] + 0.9, top[2] + math.sin(t) * L * 0.5)
        tip = (top[0] + math.cos(t) * L, top[1] - 0.6, top[2] + math.sin(t) * L)
        taper(p, top, mid, 1.3, 1.5, LEAF if k % 2 else LEAF2)
        taper(p, mid, tip, 1.5, 0.2, LEAF if k % 2 else LEAF2)
    for k in range(5):  # гроздь
        y = top[1] - 0.9 - 0.35 * k
        r = 0.55 - 0.06 * k
        p.prism_xz(K.octa(top[0] + 0.5, top[2], r, r, r * 0.4), y - 0.3, y, BANANA if k % 2 else BANANA2)


def vine(p, x, y, z, L, axis_out):
    """Лиана: тонкий изгибающийся стебель и листочки."""
    ox, oz = axis_out
    pts = [(x, y, z), (x + ox * 0.3, y - L * 0.4, z + oz * 0.3), (x + ox * 0.1, y - L, z + oz * 0.1)]
    tube(p, pts, [0.18, 0.16, 0.12], 0.16, (oz, 0, ox) if abs(ox) + abs(oz) else (1, 0, 0), LEAF3)
    for k in range(3):
        yy = y - L * (0.3 + 0.25 * k)
        p.box(x - 0.35 + ox * 0.3, x + 0.35 + ox * 0.3, yy - 0.2, yy + 0.2, z - 0.35 + oz * 0.3, z + 0.35 + oz * 0.3,
              LEAF2 if k % 2 else LEAF)


# ══ ФАСАД: ступенчатый храм ═══════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, DARKST, DARKST, LEAF3)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    # ярусы, выступающие книзу: каждый ряд — блоки двух тонов, сверху — мох
    tiers = ((-1.0, 3.0, 2.88), (3.0, 7.0, 2.38), (7.0, 11.0, 1.88), (11.0, 15.0, 1.38), (15.0, 19.0, 0.88))
    for t, (y0, y1, d) in enumerate(tiers):
        slab(FR, axis, fixed, out, d - 0.1, -half - d + 0.1, half + d - 0.1, y0, y1, STONE2)
        a = -half - d + 0.1
        k = 0
        while a < half + d - 0.2:
            w = 5.0 + int(rng(fi, t, k) * 3)
            a1 = min(a + w, half + d - 0.1)
            slab(FR, axis, fixed, out, d, a + 0.06, a1 - 0.06, y0 + 0.06, y1 - 0.15,  # верх блока ниже мха: не мерцает
                 (STONE, STONE3, STONE, MOSS2, STONE)[int(rng(fi, t, k, 5) * 5)])
            a, k = a1, k + 1
        m = half + d if axis == "z" else half - 0.05  # углы мха — у переда/тыла, бока встык
        slab(FQ, axis, fixed, out, d + 0.05, -m, m, y1 - 0.7, y1 - 0.05, MOSS)  # мох по уступу
    # лианы с карниза
    for k in range(int(2 * half // 7.0)):
        a = -half + 3.5 + 7.0 * k + (rng(fi, k, 7) - 0.5)
        L = 3.0 + rng(fi, k, 8) * 5.0
        if axis == "z":
            vine(FS, a, 18.9, fixed + out * 1.0, L, (0, out))
        else:
            vine(FS, fixed + out * 1.0, 18.9, a, L, (out, 0))
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# перед: лестница к тёмному входу, перемычка со спиралями
for k in range(6):
    w = 5.0 - 0.3 * k
    FS.box(-w, w, -1.0, 0.8 + 0.6 * k, -FZ - 2.9 + 0.5 * k, -FZ - 2.4 + 0.5 * k + 2.0, STONE3 if k % 2 else STONE)
# вход: каменные ворота под ступенчатым «ложным сводом», створки светлого песчаника с золотым швом и меандром
DOORC, DOORB = "C2B48A", "A89A72"
for s_ in (-1, 1):
    FS.box(s_ * 3.4, s_ * 4.8, 4.4, 9.4, -FZ - 2.7, -FZ, STONE3)
    for y0, y1, x in ((9.4, 10.4, 2.6), (10.4, 11.4, 1.8), (11.4, 12.2, 1.0)):
        FS.box(s_ * x, s_ * 4.8, y0, y1, -FZ - 2.7, -FZ, STONE3)
        FS.box(s_ * (x - 0.3), s_ * x, y0, y1, -FZ - 2.45, -FZ - 1.6, DOORB)  # внутренний уступ
    FS.box(s_ * 3.1, s_ * 3.4, 4.4, 9.4, -FZ - 2.45, -FZ - 1.6, DOORB)
    FS.box(s_ * 0.08, s_ * 3.1, 4.4, 9.4, -FZ - 1.9, -FZ - 1.6, DOORC)  # створки
    for y0, y1, x in ((9.4, 10.4, 2.3), (10.4, 11.4, 1.5), (11.4, 12.2, 0.7)):
        FS.box(s_ * 0.08, s_ * x, y0, y1, -FZ - 1.9, -FZ - 1.6, DOORC)
    for y in (5.4, 7.2):  # рельефные пояса створок
        FS.box(s_ * 0.5, s_ * 2.7, y, y + 0.5, -FZ - 2.05, -FZ - 1.85, DOORB)
    # жаровни у ворот
    FS.prism_xz(K.octa(s_ * 6.6, -FZ - 3.0, 0.7, 0.7, 0.28), -1.0, 3.4, STONE3)
    FS.prism_xz(K.octa(s_ * 6.6, -FZ - 3.0, 1.0, 1.0, 0.4), 3.4, 4.0, BANANA2)
    FG.prism_xz(K.octa(s_ * 6.6, -FZ - 3.0, 0.62, 0.62, 0.25), 4.0, 4.8, FLAME2)
    FG.prism_xz(K.octa(s_ * 6.6, -FZ - 3.0, 0.3, 0.3, 0.12), 4.8, 5.5, FLAME)
FG.box(-0.08, 0.08, 4.4, 12.2, -FZ - 1.98, -FZ - 1.85, BANANA)  # золотой шов
FS.box(-3.1, 3.1, 8.5, 8.9, -FZ - 2.1, -FZ - 1.85, BANANA2)  # золотой пояс через обе створки
FS.box(-5.8, 5.8, 12.2, 13.6, -FZ - 2.7, -FZ, STONE3)  # перемычка
# над перемычкой — ромбовидная плита с золотым бананом по диагонали (один знак, без «глаз»)
FS.prism_xy([(0.0, 13.4), (2.6, 16.0), (0.0, 18.6), (-2.6, 16.0)], -FZ - 1.6, -FZ - 1.2, STONE3)
FS.frame_xy([(0.0, 13.0), (3.0, 16.0), (0.0, 19.0), (-3.0, 16.0)], [(0.0, 13.4), (2.6, 16.0), (0.0, 18.6), (-2.6, 16.0)],
            -FZ - 1.5, -FZ - 1.2, MOSS2)
BAN = [(-1.5, -0.2), (-0.9, -0.9), (0.0, -1.2), (0.9, -0.9), (1.5, -0.2), (1.6, 0.4), (1.0, -0.2), (0.0, -0.5),
       (-1.0, -0.2), (-1.6, 0.4)]
c, s_ = math.cos(math.radians(50)), math.sin(math.radians(50))
FG.prism_xy([(u * c - v * s_, 16.0 + u * s_ + v * c) for u, v in BAN], -FZ - 1.75, -FZ - 1.6, BANANA)
for k in range(6):  # резьба по перемычке — ступенчатые блоки
    x = -5.0 + 2.0 * k
    FS.box(x - 0.6, x + 0.6, 12.5, 12.9 + 0.3 * (k % 2), -FZ - 2.85, -FZ - 2.7, MOSS2)
# водопад справа: поток, брызги, чаша
wx = 11.0
for k in range(4):
    FG.box(wx - 2.2 + 1.1 * k, wx - 1.3 + 1.1 * k, 1.6, 18.6 - 0.6 * (k % 2), -FZ - 3.05, -FZ - 2.95,
           WATER if k % 2 else WATER2)
FS.box(wx - 3.0, wx + 3.0, 18.4, 19.0, -FZ - 3.2, -FZ - 1.0, STONE3)  # слив
FS.box(wx - 3.6, wx + 3.6, -1.0, 1.6, -FZ - 3.4, -FZ - 1.4, STONE)  # чаша
FG.box(wx - 3.2, wx + 3.2, 1.6, 1.7, -FZ - 3.1, -FZ - 1.7, WATER)
for k in range(6):
    x = wx - 2.6 + 1.05 * k
    FS.prism_xz(K.octa(x, -FZ - 3.2, 0.3, 0.3, 0.12), 1.6, 2.0 + 0.3 * (k % 3), "E8FAFF")
# углы: банановые пальмы
for sx in (-1, 1):
    banana_palm(FS, (sx * (FX + 1.4), 15.0, -FZ - 1.4), 1.9, (sx * 0.4, -0.3))
    banana_palm(FS, (sx * (FX + 1.4), 15.0, FZ + 1.4), 1.8, (sx * 0.4, 0.3))
# бока: резные плиты (солнце, змейка)
for s in (-1, 1):
    fx = s * (FX + 1.88)
    FS.box(fx, fx + s * 0.4, 7.6, 10.6, -9.0, -3.0, STONE3)
    for k in range(8):
        t = 2 * math.pi * k / 8
        z, y = -6.0 + 1.1 * math.cos(t), 9.1 + 1.1 * math.sin(t)
        FS.box(fx + s * 0.4, fx + s * 0.55, y - 0.2, y + 0.2, z - 0.2, z + 0.2, MOSS2)
    FS.prism_zy(K.octa(-6.0, 9.1, 0.6, 0.6, 0.25), fx + s * 0.4, fx + s * 0.6, BANANA2)
    FS.box(fx, fx + s * 0.4, 7.6, 10.6, 3.0, 9.0, STONE3)
    for k in range(6):
        z = 3.6 + 0.9 * k
        y = 9.1 + (0.6 if k % 2 else -0.6)
        FS.box(fx + s * 0.4, fx + s * 0.55, y - 0.3, y + 0.3, z - 0.45, z + 0.45, MOSS2)

# ══ ИНТЕРЬЕР v2: зал древнего храма, который забирают джунгли ══════════════════════════════════════════════
ALTAR = (0.0, -5.0)
TOP = 1.6
WARM, VELVET, CLAY, CLAY2, RECESS = "A39E82", "2E5A2A", "B5653A", "8E4A2A", "2A3326"
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), MOSS)
# дорожка из плит от лифта к алтарю (часть плит утонула во мху)
for i in range(3):
    for j in range(7):
        if rng(i, j, 7) < 0.14:
            continue
        x0, z0 = -3.0 + 2.0 * i, 1.0 + 2.0 * j
        IS.box(x0 + 0.1, x0 + 1.9, 0.0, 0.12 + 0.05 * (j % 2), z0 + 0.1, z0 + 1.9, (STONE3, WARM, STONE)[int(rng(i, j, 8) * 3)])


def free(a0, a1, holes):
    """Отрезки [a0, a1] без дыр."""
    out, cur = [], a0
    for h0, h1 in sorted(holes):
        if h1 <= cur or h0 >= a1:
            continue
        if h0 > cur:
            out.append((cur, h0))
        cur = max(cur, h1)
    if cur < a1:
        out.append((cur, a1))
    return out


ROWS = ((1, 3), (3, 5), (5, 6), (6, 8), (8, 11), (11, 13))  # ряды кладки: толстые и тонкие
PILS = (-8.0, 8.0)  # пилястры
NICHES = {0: (-12.0, 0.0), 1: (0.0, 12.0), 2: (-12.0, 12.0), 3: ()}
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    lift = idx == 3
    slab(IQ, axis, fixed, out, 0.7, -half, half, 0.0, C, DARKST)  # тёмная толща за кладкой
    for a0, a1 in free(-half, half, [(-DOOR[0] - 0.6, DOOR[0] + 0.6)] if lift else []):
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.0, STONE2)  # цоколь
        slab(IQ, axis, fixed, out, 1.0, a0, a1, 0.85, 1.1, MOSS2)
    for r, (y0, y1) in enumerate(ROWS):
        holes = [] if lift else [(P - 1.0, P + 1.0) for P in PILS]
        if lift and y0 < 11:
            holes.append((-DOOR[0] - 0.6, DOOR[0] + 0.6))
        if y0 >= 3 and y1 <= 8:
            holes += [(c - 1.5, c + 1.5) for c in NICHES[idx]]
        if idx == 2:
            holes.append((-5.0, 5.0))  # портал за алтарём
        a = -17.0 + (r % 3)
        k = 0
        while a < half:
            w = 3 + int(rng(idx, r, k) * 4)
            for b0, b1 in free(max(a, -half), min(a + w, half), holes):
                if b1 - b0 < 0.5:
                    continue
                ruined = idx < 2 and y0 >= 8 and rng(idx, r, k, 3) < 0.16
                if ruined:  # выпавший камень: тёмная дыра и пучок мха
                    slab(IQ, axis, fixed, out, 0.8, b0 + 0.3, b1 - 0.3, y0 + 0.05, y0 + 0.35, MOSS)
                    continue
                d = 1.88 if rng(idx, r, k, 5) < 0.12 else 0.88
                c = (STONE, STONE3, WARM, STONE, STONE2, MOSS2)[int(rng(idx, r, k, 9) * 6)]
                slab(IR, axis, fixed, out, d, b0 + 0.06, b1 - 0.06, y0 + 0.06, y1 - 0.06, c)
            a, k = a + w, k + 1
    for P in () if lift else PILS:  # пилястры: ствол и капитель с мхом
        slab(IR, axis, fixed, out, 1.88, P - 1.0, P + 1.0, 0.0, 12.0, STONE3)
        slab(IR, axis, fixed, out, 2.88, P - 1.3, P + 1.3, 12.0, 13.0, STONE3)
        slab(IQ, axis, fixed, out, 2.95, P - 1.2, P + 1.2, 12.9, 13.15, MOSS)
    for cn in NICHES[idx]:  # ниши: порог, перемычка, подношение
        slab(IR, axis, fixed, out, 1.88, cn - 2.0, cn + 2.0, 2.0, 3.0, STONE3)
        slab(IR, axis, fixed, out, 1.88, cn - 2.0, cn + 2.0, 8.0, 9.0, STONE3)
        slab(IS, axis, fixed, out, 0.75, cn - 1.5, cn + 1.5, 3.0, 8.0, RECESS)
        nx, nz = (fixed + out * 1.0, cn) if axis == "x" else (cn, fixed + out * 1.0)
        if int(cn) % 24 == 0:  # гроздь золотых бананов
            for k in range(4):
                y, r_ = 3.3 + 0.34 * k, 0.6 - 0.08 * k
                IS.prism_xz(K.octa(nx, nz, r_, r_, r_ * 0.4), y, y + 0.3, BANANA if k % 2 else BANANA2)
        else:  # глиняная урна
            IS.prism_xz(K.octa(nx, nz, 0.45, 0.45, 0.18), 3.0, 3.4, CLAY2)
            IS.prism_xz(K.octa(nx, nz, 0.75, 0.75, 0.3), 3.4, 4.6, CLAY)
            IS.prism_xz(K.octa(nx, nz, 0.4, 0.4, 0.16), 4.6, 5.2, CLAY2)
    if lift:  # перемычка над лифтом
        slab(IR, axis, fixed, out, 1.88, -5.0, 5.0, 11.0, 13.0, STONE3)
    # ступенчатый «ложный свод»: потолок сходится уступами, в проёме — полог листьев
    slab(IR, axis, fixed, out, 1.88, -half, half, 13.0, 15.0, STONE2)
    slab(IR, axis, fixed, out, 2.88, -half, half, 15.0, 17.0, STONE)
    slab(IR, axis, fixed, out, 3.88, -half, half, 17.0, C, STONE2)
    slab(IQ, axis, fixed, out, 1.95, -half, half, 14.85, 15.1, MOSS)
    slab(IQ, axis, fixed, out, 2.95, -half, half, 16.85, 17.1, MOSS2)
    # лианы со свода — редко, по пилястрам и между нишами
    for k, a in enumerate((-14.0, -4.5, 9.5)):
        if lift and abs(a) < DOOR[0] + 1:
            continue
        L = 3.0 + rng(idx, k, 9) * 6.0
        if axis == "z":
            vine(IS, a, 13.0, fixed + out * 2.0, L, (0, out))
        else:
            vine(IS, fixed + out * 2.0, 13.0, a, L, (out, 0))
# портал за алтарём: ступенчатый проём, тёмная глубина, золотой кант
for s_ in (-1, 1):
    IR.box(s_ * 4.0, s_ * 6.0, 1.0, 9.0, ZF, ZF + 1.88, STONE3)
    for y0, y1, x in ((9.0, 10.0, 3.0), (10.0, 11.0, 2.0), (11.0, 12.0, 1.0)):
        IR.box(s_ * x, s_ * 6.0, y0, y1, ZF, ZF + 1.88, STONE3)
    IS.box(s_ * 3.85, s_ * 4.0, 1.0, 9.0, ZF + 1.5, ZF + 1.95, BANANA2)
IR.box(-6.0, 6.0, 12.0, 13.0, ZF, ZF + 1.88, STONE3)
IS.box(-5.0, 5.0, 1.0, 12.0, ZF, ZF + 0.3, RECESS)
for k, (w, y) in enumerate(((3.4, 1.0), (2.6, 3.0), (1.8, 5.0), (1.0, 7.0))):  # рельеф-пирамида в глубине
    IS.box(-w, w, y, y + 2.0, ZF + 0.3, ZF + 0.55 + 0.1 * k, STONE2 if k % 2 else DARKST)
# полог листьев в проёме свода и лучи света
for k in range(9):
    x, z = (rng(k, 101) - 0.5) * 22, (rng(k, 102) - 0.5) * 20
    t = rng(k, 103) * math.pi
    L = 3.0 + rng(k, 104) * 2.0
    a = (x - math.cos(t) * L, C - 0.4 - rng(k, 105) * 0.8, z - math.sin(t) * L)
    b = (x + math.cos(t) * L, C - 0.4 - rng(k, 106) * 0.8, z + math.sin(t) * L)
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 0.5, (a[2] + b[2]) / 2)
    taper(IS, a, m, 0.6, 2.4, (LEAF, LEAF2, LEAF3)[k % 3])
    taper(IS, m, b, 2.4, 0.4, (LEAF, LEAF2, LEAF3)[k % 3])
for x, z in ((-3.0, -6.0), (2.5, -3.5), (7.0, 4.0)):
    IG.box(x - 0.5, x + 0.5, C - 0.1, C - 0.04, z - 0.5, z + 0.5, "FFF6C0")
# корни огромного дерева: спускаются со свода в двух углах и расползаются по полу
for pts, ws in (([(-12.6, 17.0, -11.6), (-14.6, 12.0, -13.6), (-15.4, 6.0, -14.4), (-14.2, 1.4, -13.2), (-11.0, 0.25, -11.0)],
                 [1.5, 1.3, 1.1, 0.9, 0.5]),
                ([(-14.2, 5.0, -14.0), (-15.2, 1.2, -10.0), (-14.6, 0.2, -7.4)], [0.8, 0.6, 0.35]),
                ([(12.6, 17.0, 11.6), (14.8, 11.0, 13.8), (15.4, 4.0, 14.4), (14.0, 0.8, 12.6), (11.8, 0.2, 13.4)],
                 [1.4, 1.2, 1.0, 0.7, 0.4])):
    tube(IS, pts, ws, 0.9, (1, 0, -1), WOOD2)
# упавшие камни у обрушенных мест, мох на них
for x, z, w, h in ((-14.6, -3.0, 1.0, 0.9), (-13.4, -1.6, 0.7, 0.6), (14.4, -6.4, 1.1, 1.0), (13.4, -4.6, 0.6, 0.5)):
    IS.box(x - w, x + w, 0.0, h, z - w * 0.8, z + w * 0.8, STONE if w > 0.8 else STONE3)
    IQ.box(x - w * 0.7, x + w * 0.7, h - 0.05, h + 0.12, z - w * 0.5, z + w * 0.5, MOSS2)
# пруд с кувшинками слева (каменная оправа, камни-переходы)
IG.prism_xz(K.octa(-11.0, 1.0, 3.6, 4.4, 1.6), 0.03, 0.08, WATER)
IS.frame_xz(K.octa(-11.0, 1.0, 4.0, 4.8, 1.7), K.octa(-11.0, 1.0, 3.6, 4.4, 1.6), 0.0, 0.3, STONE3)
for k in range(5):
    x, z = -11.0 + (rng(k, 111) - 0.5) * 5, 1.0 + (rng(k, 112) - 0.5) * 6
    IS.prism_xz(K.octa(x, z, 0.7, 0.7, 0.28), 0.08, 0.14, LEAF2)
    if k % 2 == 0:
        IS.prism_xz(K.octa(x + 0.2, z, 0.25, 0.25, 0.1), 0.14, 0.4, FLOWER)
# алтарь: платформа, два яруса с золотым кантом, лестница к лифту, стелы и жаровни
ax, az = ALTAR
IR.box(ax - 7.0, ax + 7.0, 0.0, 0.4, az - 6.0, az + 6.0, STONE2)
IR.box(ax - 5.0, ax + 5.0, 0.0, 0.8, az - 4.0, az + 4.0, STONE)
IR.box(ax - 4.0, ax + 4.0, 0.8, TOP, az - 3.2, az + 3.2, STONE3)
IQ.box(ax - 4.05, ax + 4.05, TOP - 0.25, TOP + 0.02, az - 3.25, az + 3.25, VELVET)
IS.frame_xz(K.rect(ax - 5.08, ax + 5.08, az - 4.08, az + 4.08), K.rect(ax - 4.9, ax + 4.9, az - 3.9, az + 3.9), 0.62, 0.82,
            BANANA2)
IS.frame_xz(K.rect(ax - 4.1, ax + 4.1, az - 3.3, az + 3.3), K.rect(ax - 3.9, ax + 3.9, az - 3.1, az + 3.1), TOP - 0.05,
            TOP + 0.06, BANANA)
for k in range(3):
    IS.box(ax - 2.2, ax + 2.2, 0.4 + 0.4 * k, 0.8 + 0.4 * k, az + 4.0 + 0.6 * (2 - k), az + 4.6 + 0.6 * (2 - k), STONE3)
for s_ in (-1, 1):
    sx_, sz_ = ax + s_ * 6.2, az - 4.6  # стелы
    IS.prism_xz(K.octa(sx_, sz_, 1.1, 1.1, 0.45), 0.4, 1.2, STONE2)
    IS.prism_xz(K.octa(sx_, sz_, 0.85, 0.85, 0.34), 1.2, 8.4, STONE3)
    for y in (3.0, 5.6):
        IS.prism_xz(K.octa(sx_, sz_, 0.92, 0.92, 0.37), y, y + 0.35, BANANA2)
    IS.prism_xz(K.octa(sx_, sz_, 1.15, 1.15, 0.46), 8.4, 9.0, STONE)
    IQ.prism_xz(K.octa(sx_, sz_, 1.0, 1.0, 0.4), 9.0, 9.3, MOSS2)
    bx_, bz_ = ax + s_ * 6.0, az + 5.0  # жаровни у передних углов платформы
    IS.prism_xz(K.octa(bx_, bz_, 0.35, 0.35, 0.14), 0.4, 1.4, STONE3)
    IS.prism_xz(K.octa(bx_, bz_, 0.75, 0.75, 0.3), 1.4, 1.9, BANANA2)
    IG.prism_xz(K.octa(bx_, bz_, 0.5, 0.5, 0.2), 1.9, 2.5, FLAME2)
    IG.prism_xz(K.octa(bx_, bz_, 0.24, 0.24, 0.1), 2.5, 3.0, FLAME)
    for k in range(4):  # грозди-подношения
        y = 0.5 + 0.32 * k
        r = 0.7 - 0.1 * k
        IS.prism_xz(K.octa(ax + s_ * 5.9, az - 1.0, r, r, r * 0.4), y - 0.1, y + 0.2, BANANA if k % 2 else BANANA2)
# папоротники и цветы — по краям, проход свободен
for k in range(7):
    x, z = (rng(k, 121) - 0.5) * 28, -12.0 + rng(k, 122) * 26
    if (abs(x) < 8.0 and z < 2.0) or abs(x) < 4.5 or (x < -6.0 and -4.5 < z < 6.5):
        continue
    for m in range(5):
        t = 2 * math.pi * m / 5 + k
        taper(IS, (x, 0.0, z), (x + math.cos(t) * 1.8, 1.6, z + math.sin(t) * 1.8), 0.5, 0.1, LEAF if m % 2 else LEAF2)
for k in range(10):
    x, z = (rng(k, 131) - 0.5) * 30, 4.0 + rng(k, 132) * 11
    if abs(x) < 5.0 or (x < -6.0 and z < 6.5):
        continue
    IS.box(x - 0.06, x + 0.06, 0.0, 0.9, z - 0.06, z + 0.06, LEAF3)
    IS.prism_xz(K.octa(x, z, 0.35, 0.35, 0.14), 0.9, 1.15, (FLOWER, FLOWER2, BANANA)[k % 3])
# факелы у лифта
for x in (-5.5, 5.5):
    IS.box(x - 0.15, x + 0.15, 0.0, 4.0, 9.0 - 0.15, 9.0 + 0.15, WOOD2)
    IS.prism_xz(K.octa(x, 9.0, 0.4, 0.4, 0.16), 4.0, 4.6, WOOD)
    IG.prism_xz(K.octa(x, 9.0, 0.3, 0.3, 0.12), 4.6, 5.3, FLAME2)
    IG.prism_xz(K.octa(x, 9.0, 0.16, 0.16, 0.06), 5.3, 5.9, FLAME)
for x, z in ((12.0, -11.0), (12.6, 6.5)):
    banana_palm(IS, (x, 0.0, z), 10.5, (-1.0, 0.5))
B.lift_leaves(IS, STONE2, BANANA2)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, STONE)
for y0, y1, d, c in ((-1.0, 3.0, 2.88, STONE2), (3.0, 7.0, 2.38, STONE), (7.0, 11.0, 1.88, STONE2), (11.0, 15.0, 1.38, STONE)):
    SL.box(-FX - d, FX + d, y0, y1, -FZ - d, FZ + d, c)
SL.box(-5.8, 5.8, 4.4, 13.6, -FZ - 2.7, -FZ, STONE3)
SL.box(-3.0, 3.0, 4.4, 11.0, -FZ - 2.8, -FZ - 2.6, DOORC)
SL.box(wx - 2.2, wx + 2.2, 1.6, 18.6, -FZ - 3.1, -FZ - 2.9, WATER)
for sx in (-1, 1):
    for sz in (-1, 1):
        SL.box(sx * (FX + 0.4), sx * (FX + 2.4), 15.0, 17.6, sz * (FZ + 0.4), sz * (FZ + 2.4), LEAF)

F.build(exhibit=(ALTAR[0], TOP, ALTAR[1], 3.2), lamps=[("Hall", (0, 14, 6), 3000, (0.9, 1.0, 0.85)),
                                                       ("Spot", (0, 13, -5), 3200, (1.0, 0.97, 0.85))])
