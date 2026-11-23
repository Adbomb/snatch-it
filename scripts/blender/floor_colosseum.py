"""Этаж «Колизей» музея-небоскрёба (первая партия новых этажей, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — сам амфитеатр. Снаружи — римская аркада в три яруса из травертина: глубокие тёмные арки между
столбами с полуколоннами, антаблементы, аттик с консолями и мачтами для навеса; в нижнем ярусе — огни факелов, в
верхнем — бронзовые щиты; правый передний угол обрушен, как у настоящего Колизея: аттик и часть верхнего яруса
отбиты ступенями, за руиной виден внутренний ярус, на обломках трава. Издалека — светлый пояс арок, который ни с чем
не спутать. Внутри — арена: трибуны ярусами с трёх сторон (углы скруглены), песок, мраморный постамент с моделью
Колизея посередине; над ареной полосатый навес-веларий на канатах с окулусом — сквозь него видно небо и падает свет;
у лифта — триумфальная арка с лавровым венком и щитами, жаровни у постамента, колесница, амфоры, стойка с оружием.
Запуск: blender --background --factory-startup --python scripts/blender/floor_colosseum.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, FX, FZ, W, ZB, ZF, beam, quad, rng, slab, taper  # noqa: E402

TRAV, TRAV2, TRAV3, DARK = "EAD3A4", "D6BA8A", "B79B70", "3D2F27"
MARBLE, RED, OCHRE, BRONZE, GOLD = "EFE9DC", "B23A2A", "C98A3A", "A8743A", "E8B84A"
SAND, SAND2, WOOD, WOOD2 = "D9B98A", "C9A672", "8A5A32", "5E3B20"
CANVAS, CANVAS2, ROPE, GRASS, LEAF = "F0E6CF", "C2463A", "6B4A28", "5E8F3A", "4C7A2E"
FLAME, FLAME2, SKY, INNER, IRON = "FFC24A", "FF8A2A", "8CC2EE", "9E8A6A", "3A3632"
ITRAV, ITRAV2, ISAND = "C9AA7E", "AD8E64", "B98A55"  # интерьер темнее фасада: модель-экспонат — самая светлая

F = B.Floor("CO", "Colosseum", quiet=(SAND, SAND2, ISAND, CANVAS, CANVAS2, GRASS), bevel_min=2.0, keep_arch=True)  # камень — острые рёбра
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL

# ══ ФАСАД: римская аркада в три яруса ══════════════════════════════════════════════════════════════════════════
B.shell_planes(F, DARK, "5A4A3A", SKY)

TIERS = ((0.6, 6.0, 3.9, 5.4), (6.8, 11.8, 9.4, 11.0), (12.6, 16.0, 14.4, 15.5))  # низ, верх, импост, верх арки
ENTABL = ((6.0, 6.8), (11.8, 12.6))
BAY = 6.0
PIER = 1.8


def ruined(face, a):
    """Высота обрушения пролёта (None — цел): правый передний угол — перед справа и правый бок спереди."""
    if face == 0 and a > 5.0:
        return 13.6 + 2.2 * rng(face, a)
    if face == 3 and a < -3.0:
        return 13.6 + 2.2 * rng(face, a)
    return None


for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    n = max(1, int(round(2 * half / BAY)))
    bw = 2 * half / n
    centers = [-half + bw * (i + 0.5) for i in range(n)]
    piers = [-half + bw * i for i in range(n + 1)]
    # цоколь: две ступени
    slab(FR, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.2, TRAV3)
    slab(FR, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, -0.2, 0.6, TRAV2)
    for ti, (y0, y1, imp, top) in enumerate(TIERS):
        for i, a in enumerate(piers):
            lo, hi = a - PIER / 2, a + PIER / 2
            if i == 0:
                lo = -half - 1.88
            if i == n:
                hi = half + 1.88
            cap = y1
            if ti == 2:
                r = ruined(fi, a)
                if r is not None:
                    cap = min(cap, r)
            slab(FR, axis, fixed, out, 1.88, lo, hi, y0, cap, TRAV)
            if 0 < i < n and cap > imp:  # полуколонна с базой и капителью
                slab(FS, axis, fixed, out, 2.38, a - 0.42, a + 0.42, y0 + 0.35, min(cap, y1 - 0.35), MARBLE)
                if cap >= y1:
                    slab(FS, axis, fixed, out, 2.5, a - 0.62, a + 0.62, y1 - 0.35, y1, TRAV2)
        for i, a in enumerate(centers):
            hw = (bw - PIER) / 2
            cap = y1
            if ti == 2:
                r = ruined(fi, a)
                if r is not None:
                    cap = r
            # ступенчатая арка: две ступени от импоста, над аркой — надарочная стена
            for k, inset in enumerate((0.45, 0.95)):
                s0 = imp + (top - imp) * k / 2
                s1 = imp + (top - imp) * (k + 1) / 2
                if s1 > cap:
                    continue
                slab(FS, axis, fixed, out, 1.78, a - hw, a - hw + inset, s0, s1, TRAV2)
                slab(FS, axis, fixed, out, 1.78, a + hw - inset, a + hw, s0, s1, TRAV2)
            if cap > top:
                slab(FS, axis, fixed, out, 1.88, a - hw, a + hw, top, cap, TRAV)
            if ti == 0 and i % 2 == 0:  # факел в арке нижнего яруса
                slab(FS, axis, fixed, out, 0.6, a - 0.12, a + 0.12, 2.6, 3.6, IRON)
                slab(FG, axis, fixed, out, 0.75, a - 0.28, a + 0.28, 3.6, 4.3, FLAME, back=-0.4)
            if ti == 2 and cap >= y1 and i % 2 == 1:  # бронзовый щит в арке верхнего яруса
                c = (a, (imp + y0) / 2 + 0.6)
                pts = K.octa(c[0], c[1], 0.9, 0.9, 0.37)
                lo, hi = sorted((fixed - out * 0.6, fixed - out * -0.0))
                if axis == "z":
                    FS.prism_xy(pts, fixed + out * 0.3, fixed + out * 0.7, BRONZE)
                else:
                    FS.prism_zy(pts, fixed + out * 0.3, fixed + out * 0.7, BRONZE)
    # антаблементы между ярусами (выступают, огибают углы)
    for e0, e1 in ENTABL:
        slab(FR, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, e0 + 0.2, e1, TRAV2)
        slab(FS, axis, fixed, out, 2.6, -half - 2.6, half + 2.6, e0, e0 + 0.2, MARBLE)
    # аттик: стена, плоские пилястры, окошки, консоли с мачтами; над обрушением — внутренний ярус и трава
    for i, a in enumerate(piers):
        if ruined(fi, a) is not None:
            continue
        lo, hi = a - 0.6, a + 0.6
        slab(FS, axis, fixed, out, 2.08, lo, hi, 16.0, 19.0, TRAV2)
    for i, a in enumerate(centers):
        r = ruined(fi, a)
        hw = bw / 2
        if r is None:
            slab(FR, axis, fixed, out, 1.88, a - hw, a + hw, 16.0, 19.0, TRAV)
            if i % 2 == 0:
                slab(FS, axis, fixed, out, 1.98, a - 0.5, a + 0.5, 17.0, 18.0, DARK)
            x = a + hw * 0.5  # консоль и мачта навеса — по одной на пролёт
            slab(FS, axis, fixed, out, 2.4, x - 0.3, x + 0.3, 16.1, 16.5, TRAV2)
            slab(FS, axis, fixed, out, 2.25, x - 0.1, x + 0.1, 16.5, 18.85, WOOD)
        else:
            slab(FS, axis, fixed, out, 0.6, a - hw, a + hw, r, 19.0, INNER)  # внутренний ярус за руиной
            slab(FS, axis, fixed, out, 0.7, a - 0.6, a + 0.6, r + 0.6, r + 2.0, DARK)
            for k in range(3):  # трава на обломках
                x = a - hw * 0.6 + hw * 0.6 * k
                if axis == "z":
                    taper(FS, (x, r, fixed + out * 1.4), (x + 0.3, r + 0.9, fixed + out * 1.6), 0.4, 0.1, LEAF)
                else:
                    taper(FS, (fixed + out * 1.4, r, x), (fixed + out * 1.6, r + 0.9, x + 0.3), 0.4, 0.1, LEAF)
B.anchor(FR, (-22, -1, -21), (22, 19, 21))
B.anchor(FQ, (-22, -1, -21), (22, 19, 21))

# ══ ИНТЕРЬЕР: арена ═══════════════════════════════════════════════════════════════════════════════════════════

ARENA = (0.0, -2.0)  # центр арены и постамента
SIDE = ((15.0, 3.0), (13.0, 2.0), (11.0, 1.0))  # ярусы у боковых стен: внутренний край x, высота
FRONT = ((-14.0, 3.0), (-12.0, 2.0), (-10.0, 1.0))  # ярусы у передней стены: внутренний край z, высота
SEAT_Z = 6.0  # трибуны боковых стен — от передней стены до z = 6 (дальше — проход к лифту)

IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), ISAND)
for s in (-1, 1):
    for k, (x, h) in enumerate(SIDE):
        x0, x1 = s * x, s * (W if k == 0 else SIDE[k - 1][0])
        IR.box(x0, x1, 0.0, h, ZF, SEAT_Z, ITRAV)
        IS.box(x0, x0 + s * 0.5, h, h + 0.18, ZF, SEAT_Z, MARBLE)  # кромка сиденья
    for z in (-10.0, -2.0):  # лестницы-проходы по трибунам
        for k, (x, h) in enumerate(SIDE):
            IS.box(s * (x - 0.05), s * (x + 1.95), h - 0.5, h + 0.02, z - 0.7, z + 0.7, ITRAV2)
for k, (z, h) in enumerate(FRONT):
    z1 = ZF if k == 0 else FRONT[k - 1][0]
    IR.box(-W, W, 0.0, h, z1, z, ITRAV)
    IS.box(-W, W, h, h + 0.18, z - 0.5, z, MARBLE)
# скруглённые углы арены: скосы ярусов у передних углов
for s in (-1, 1):
    for k, (x, h) in enumerate(SIDE):
        z = FRONT[k][0]
        IR.prism_xz([(s * x, z), (s * (x - 2.5), z), (s * x, z + 2.5)], 0.0, h, ITRAV)
# стенка арены: красные панели с охряной рамкой по фасаду нижнего яруса
for s in (-1, 1):
    for z0, z1 in ((-9.0, -5.0), (-4.0, 0.0), (1.0, 5.0)):
        slab(IS, "x", s * SIDE[2][0], -s, 0.08, z0, z1, 0.15, 0.85, RED)
        slab(IS, "x", s * SIDE[2][0], -s, 0.05, z0 - 0.12, z1 + 0.12, 0.08, 0.92, OCHRE)
for x0, x1 in ((-9.0, -5.0), (-4.0, 0.0), (1.0, 5.0), (6.0, 9.0)):
    slab(IS, "z", FRONT[2][0], 1, 0.08, x0, x1, 0.15, 0.85, RED)
    slab(IS, "z", FRONT[2][0], 1, 0.05, x0 - 0.12, x1 + 0.12, 0.08, 0.92, OCHRE)

# аркада внутри над трибунами: столбы, тёмные арки, факелы, антаблемент, щиты
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    n = 6
    bw = 2 * half / n
    skip = (lambda a: abs(a) < 9.0) if idx == 3 else (lambda a: False)  # на стене лифта — триумфальная арка
    for i in range(n + 1):
        a = -half + bw * i
        if skip(a):
            continue
        slab(IR, axis, fixed, out, 0.88, a - 0.8, a + 0.8, 3.0, 11.0, ITRAV)
        slab(IS, axis, fixed, out, 1.2, a - 0.35, a + 0.35, 3.0, 11.0, MARBLE)
    for i in range(n):
        a = -half + bw * (i + 0.5)
        hw = bw / 2 - 0.8
        if skip(a):
            continue
        for k, inset in enumerate((0.4, 0.85)):
            slab(IS, axis, fixed, out, 0.78, a - hw, a - hw + inset, 8.6 + 0.8 * k, 9.4 + 0.8 * k, ITRAV2)
            slab(IS, axis, fixed, out, 0.78, a + hw - inset, a + hw, 8.6 + 0.8 * k, 9.4 + 0.8 * k, ITRAV2)
        slab(IR, axis, fixed, out, 0.88, a - hw, a + hw, 10.2, 11.0, ITRAV)
        if i % 2 == 0:
            slab(IS, axis, fixed, out, 0.5, a - 0.1, a + 0.1, 5.6, 6.6, IRON)
            slab(IG, axis, fixed, out, 0.62, a - 0.26, a + 0.26, 6.6, 7.3, FLAME, back=-0.3)
    for e0, e1 in (((-half, -8.2), (8.2, half)) if idx == 3 else ((-half, half),)):
        slab(IR, axis, fixed, out, 1.88, e0, e1, 11.0, 12.0, ITRAV2)
        slab(IS, axis, fixed, out, 1.6, e0, e1, 12.0, 12.25, MARBLE)
    for e0, e1 in (((-half, -8.2), (8.2, half)) if idx == 3 else ((-half, half),)):
        slab(IR, axis, fixed, out, 0.88, e0, e1, 12.25, 16.6, ITRAV)
    for i in range(n):
        a = -half + bw * (i + 0.5)
        if skip(a):
            continue
        pts = K.octa(a, 14.4, 1.0, 1.0, 0.42)
        if axis == "z":
            IS.prism_xy(pts, fixed + out * 0.85, fixed + out * 1.2, BRONZE)
        else:
            IS.prism_zy(pts, fixed + out * 0.85, fixed + out * 1.2, BRONZE)
    slab(IS, axis, fixed, out, 1.3, -half, half, 16.6, 17.1, WOOD2)  # балка навеса

# триумфальная арка у лифта
for s in (-1, 1):
    IR.box(s * 3.7, s * 7.7, 0.0, 13.0, ZB + 0.05, ZB - 1.88, ITRAV)
    for x in (s * 4.4, s * 7.0):
        IS.box(x - 0.42, x + 0.42, 0.4, 12.3, ZB - 1.9, ZB - 2.4, MARBLE)
        IS.box(x - 0.6, x + 0.6, 0.0, 0.4, ZB - 1.9, ZB - 2.5, ITRAV2)
        IS.box(x - 0.6, x + 0.6, 12.3, 12.7, ZB - 1.9, ZB - 2.5, ITRAV2)
    IS.prism_xy(K.octa(s * 5.7, 8.6, 0.9, 0.9, 0.37), ZB - 1.88, ZB - 2.2, BRONZE)
    for x in (s * 10.5, s * 14.0):  # стена по сторонам арки
        IR.box(x - 1.7, x + 1.7, 0.0, 3.0, ZB + 0.05, ZB - 0.88, ITRAV2)
for k, inset in enumerate((0.5, 1.0)):
    for s in (-1, 1):
        IS.box(s * (3.7 - inset), s * 3.7, 10.5 + 0.8 * k, 11.3 + 0.8 * k, ZB + 0.05, ZB - 1.8, ITRAV2)
IR.box(-7.7, 7.7, 12.1, 13.0, ZB + 0.05, ZB - 1.88, ITRAV)
IR.box(-8.2, 8.2, 13.0, 16.6, ZB + 0.05, ZB - 2.0, ITRAV2)
IS.box(-8.4, 8.4, 13.0, 13.3, ZB - 1.9, ZB - 2.2, MARBLE)
IS.frame_xy(K.octa(0, 14.8, 1.35, 1.35, 0.56), K.octa(0, 14.8, 0.85, 0.85, 0.35), ZB - 2.0, ZB - 2.3, LEAF)  # венок
for s in (-1, 1):
    IS.prism_xy([(s * 0.5, 13.6), (s * 1.6, 13.4), (s * 1.1, 13.9)], ZB - 2.0, ZB - 2.25, CANVAS2)  # ленты венка
B.lift_leaves(IS, BRONZE, GOLD)

F.objects(True)
# постамент с моделью Колизея: мрамор, бронзовая кромка
ax, az = ARENA
IR.prism_xz(K.octa(ax, az, 6.6, 5.6, 2.2), 0.0, 0.8, MARBLE)
IS.prism_xz(K.octa(ax, az, 6.75, 5.75, 2.25), 0.8, 0.95, BRONZE)
IR.prism_xz(K.octa(ax, az, 5.9, 4.9, 1.95), 0.95, 1.6, ITRAV)
IQ.prism_xz(K.octa(ax, az, 5.6, 4.6, 1.85), 1.6, 1.64, SAND2)
# жаровни на треногах по углам постамента
for sx, sz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
    x, z = ax + sx * 8.4, az + sz * 6.6
    for k in range(3):
        ang = 2 * math.pi * k / 3 + 0.5
        beam(IS, (x + 0.7 * math.cos(ang), 0.0, z + 0.7 * math.sin(ang)), (x, 3.0, z), 0.14, 0.14, BRONZE)
    IS.prism_xz(K.octa(x, z, 0.75, 0.75, 0.3), 3.0, 3.5, BRONZE)
    IG.prism_xz(K.octa(x, z, 0.55, 0.55, 0.22), 3.5, 3.9, FLAME2)
    IG.prism_xz(K.octa(x, z, 0.3, 0.3, 0.12), 3.9, 4.5, FLAME)

# колесница у левой трибуны, амфоры и стойка с оружием у лифта
cx, cz = -7.5, 5.0
for dz in (-1.1, 1.1):
    IS.frame_zy(K.octa(cz + dz, 1.1, 1.1, 1.1, 0.45), K.octa(cz + dz, 1.1, 0.8, 0.8, 0.33), cx - 0.12, cx + 0.12, WOOD)
    IS.box(cx - 0.1, cx + 0.1, 0.9, 1.3, cz + dz - 0.2, cz + dz + 0.2, GOLD)
IS.box(cx - 0.9, cx + 0.9, 1.0, 1.2, cz - 1.0, cz + 1.0, WOOD2)
IS.prism_zy([(cz - 1.0, 1.2), (cz + 1.0, 1.2), (cz + 0.8, 2.6), (cz - 0.8, 2.6)], cx + 0.2, cx + 0.9, CANVAS2)
IS.box(cx - 0.9, cx + 0.2, 1.2, 2.2, cz - 0.95, cz + 0.95, CANVAS2)
IS.box(cx - 0.95, cx + 0.95, 2.2, 2.45, cz - 1.0, cz + 1.0, GOLD)
beam(IS, (cx + 0.9, 1.1, cz), (cx + 4.0, 1.4, cz), 0.16, 0.16, WOOD)
for x, z in ((-10.5, 12.5), (10.8, 12.0), (-11.4, 13.4)):
    IS.prism_xz(K.octa(x, z, 0.45, 0.45, 0.18), 0.0, 0.5, OCHRE)
    IS.prism_xz(K.octa(x, z, 0.75, 0.75, 0.3), 0.5, 1.6, OCHRE)
    IS.prism_xz(K.octa(x, z, 0.32, 0.32, 0.13), 1.6, 2.3, OCHRE)
    IS.prism_xz(K.octa(x, z, 0.45, 0.45, 0.18), 2.3, 2.5, RED)
IS.box(12.6, 13.0, 0.0, 3.2, 8.0, 11.0, WOOD)
IS.box(12.5, 13.1, 2.6, 2.8, 8.0, 11.0, WOOD2)
for k in range(3):
    z = 8.5 + 1.0 * k
    beam(IS, (12.9, 0.1, z), (12.9, 4.2, z + 0.3), 0.1, 0.1, IRON)
    IS.prism_zy(K.octa(z, 1.6, 0.55, 0.75, 0.25), 12.4, 12.55, CANVAS2 if k % 2 else BRONZE)

F.objects(False)
# веларий: полосатый навес от стен к окулусу над постаментом, канаты по швам, кольцо окулуса
N = 16
for k in range(N):
    t0, t1 = 2 * math.pi * k / N, 2 * math.pi * (k + 1) / N

    def outer(t):
        return (ax + 16.4 * math.cos(t), 16.75, az + 14.2 * math.sin(t))

    def inner(t):
        return (ax + 4.6 * math.cos(t), 14.2, az + 3.8 * math.sin(t))

    a0, a1, b0, b1 = outer(t0), outer(t1), inner(t0), inner(t1)
    ring_a = [a0, a1, (a1[0], a1[1] - 0.12, a1[2]), (a0[0], a0[1] - 0.12, a0[2])]
    ring_b = [b0, b1, (b1[0], b1[1] - 0.12, b1[2]), (b0[0], b0[1] - 0.12, b0[2])]
    IQ.loft(ring_a, ring_b, CANVAS if k % 2 == 0 else CANVAS2)
    beam(IS, (a0[0], a0[1] + 0.05, a0[2]), (b0[0], b0[1] + 0.05, b0[2]), 0.1, 0.1, ROPE)
IS.frame_xz(K.octa(ax, az, 5.0, 4.2, 2.0), K.octa(ax, az, 4.4, 3.6, 1.75), 13.9, 14.4, WOOD2)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, DARK)
SL.box(-FX - 2.9, FX + 2.9, -1, 0.6, -FZ - 2.9, FZ + 2.9, TRAV3)
for y0, y1 in ((6.0, 6.8), (11.8, 12.6)):
    SL.box(-FX - 2.9, FX + 2.9, y0, y1, -FZ - 2.9, FZ + 2.9, TRAV2)
SL.box(-FX - 1.9, FX + 1.9, 16.0, 19.0, -FZ - 1.9, FZ + 1.9, TRAV)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # столбы аркады во всю высоту (кроме тыла)
    if fi == 1:
        continue
    n = max(1, int(round(2 * half / BAY)))
    for i in range(n + 1):
        a = -half + 2 * half * i / n
        slab(SL, axis, fixed, out, 1.9, a - 0.9, a + 0.9, 0.6, 16.0, TRAV)

F.build(tol=0.13, exhibit=(ARENA[0], 1.64, ARENA[1], 3.4), lamps=[("Hall", (0, 15, 4), 5000, (1.0, 0.92, 0.8)),
                                                        ("Sun", (0, 13, -2), 2500, (1.0, 0.95, 0.85))])
