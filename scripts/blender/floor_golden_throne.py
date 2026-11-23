"""Этаж «Золотой трон» музея-небоскрёба — архитектура из мешей в стиле референса владельца 2026-11-19 (забор из
брусков): крупные блоки по сетке в один стад, на гранях — крупные вдавленные квадраты с фаской, по одному на стад
(MaterialVariant LegoSquaresBold, scripts/textures/squares_bold.py). Цвета — предмета GoldenThrone
(scripts/blender/art_flea.golden_throne): золото F2C230, тёмное золото C9921A, бархат C62828, пурпур 6B3FB8, камни.

Сетка: все грани блоков с квадратами стоят на целых координатах этажа (допуск 0.2 — квадрат занимает середину
клетки), поэтому квадраты не режутся краями; тонкие накладки (бархат, дорожки) выровнены по сетке в своей плоскости.
Камни, пуговицы, монеты, зубцы и кромки — гладкие. Центр габаритов деталей с квадратами — целый (anchor): рисунок
материала привязан к центру детали.

Замысел (2026-11-20, по просьбе владельца «этаж — не только кресло; кресло красивое и выделяется на фоне роскошного
королевского этажа»): этаж — королевский тронный зал, а трон — единственная целиком золотая вещь в нём.
  Снаружи — дворец: светлый мрамор, золотые пояса и пилястры, синий фриз с золотыми розетками, витражные окна со
  ступенчатым верхом, посередине — выступ с балконом, большим витражом и золотой короной с камнями; красные знамёна.
  Внутри — зал: мраморный пол в крупную клетку, синие бархатные стены с мраморной панелью, по бокам колоннада со
  ступенчатыми арками и знамёнами, витражи в простенках, кессонный потолок, люстра; красная дорожка от лифта ведёт
  на мраморный помост; за троном — балдахин: тёмная бархатная ниша в складках с золотым ореолом, красные занавеси и
  полог с бахромой и короной. Тёмный фон и свободное место вокруг — трон читается первым.

Детали (MeshPart): Rings — Plastic + LegoSquaresBold (фасад — LegoSquaresFar), Quiet — ткань на LegoSquaresQuiet,
Smooth — SmoothPlastic, Glass — витражи и огоньки (светятся сами, без затенения); цвета, тени в углах и под выступами и
своя яркость у каждой стороны блока — в цветах вершин (floorkit.shade_parts); сетку вершин под тени кладёт
floorkit.adaptive_cut — только там, где тень меняется.
Пишет assets/models/floors/GoldenThroneFloor.fbx и .json (центры, размеры), рендеры — в папку превью.
Запуск: blender --background --factory-startup --python scripts/blender/floor_golden_throne.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorkit as K  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
FLAGS = set(argv[2:])
os.makedirs(OUT, exist_ok=True)

# ── Палитра: цвета — в вершинах; цвет детали в игре — общий множитель яркости ──────────────────────────────────
# Зал — королевский синий бархат, светлый мрамор и тонкое золото: золотым целиком остаётся только сам трон.
WHITE = "FFFFFF"
GOLD, GOLD2 = "F2C230", "C9921A"
IVORY, IVORY2, SLATE = "F1E9D8", "D9CCB2", "C3C9DB"  # мрамор, его отделка, тёмная клетка пола
WALL = "EEE2C8"  # поле стен фасада: теплее мрамора — этаж отделяется от белой башни, пилястры и выступ светлее
BLUE, NAVY = "2F4FA6", "17245A"  # бархат стен, тёмный бархат балдахина
VELVET, CRIMSON = "C62828", "8E1B2A"  # ковёр и знамёна, сундуки
RUBY, EMERALD, SAPPHIRE, GLINT, COIN = "E53935", "2E9E4F", "2E5BD8", "FFFFFF", "FFD84A"
# витраж (светится сам — без затенения)
G_BLUE, G_SKY, G_RED, G_GOLD, G_GREEN, G_LEAD, FLAME = (
    "3F7BEA", "8EC0FF", "E8484C", "FFD45A", "46C27A", "1B2550", "FFE38A")
SHADE = (0.52, 0.52, 0.52)  # цвет × (0.52 + 0.48 × окклюзия)

HX, HZ, YB, YT = 18.0, 17.0, -1.0, 19.0
SK = 0.12  # обшивка поверх стен каркаса
FX, FZ = HX + SK, HZ + SK
NARROW = 0.9  # грани уже одной клетки — гладкие: ряд квадратов на них не помещается
SKIN = 0.14  # толщина накладок (ковёр, знамёна)

parts = []


def part(name, tier, material, **kw):
    p = K.Part(name, tier, material, WHITE, SHADE, **kw)
    parts.append(p)
    return p


EDGE = 0.1  # фаска рёбер брусков с рисунком (скруглённое ребро, как на референсе); сама фаска — гладкая
FS = part("GT_F_Smooth", "facade", "smooth", adapt=True)
FR = part("GT_F_Rings", "facade", "tile", adapt=True, partner=FS, narrow=NARROW, bevel=EDGE, bevel_min=1.0)
FQ = part("GT_F_Quiet", "facade", "tile", adapt=True, partner=FS, narrow=NARROW)
FG = part("GT_F_Glass", "facade", "glass", occlude=False)
IS = part("GT_I_Smooth", "interior", "smooth", adapt=True)
IR = part("GT_I_Rings", "interior", "tile", adapt=True, partner=IS, narrow=NARROW, bevel=EDGE, bevel_min=1.0)
IQ = part("GT_I_Quiet", "interior", "tile", adapt=True, partner=IS, narrow=NARROW)
IG = part("GT_I_Glass", "interior", "glass", occlude=False)
# Вещи этажа (статуи, мебель, механизмы, растения) — в стиле предметов и боссов: Plastic + LegoRingsD39Boss
# (решение владельца 2026-11-21, эталон — Крысиный король); узкие грани (< 0.5) — гладкие. Гладкие тела уходят
# в Props только на участках, отмеченных objects(True) … objects(False); архитектура остаётся как была.
FP = part("GT_F_Props", "facade", "props", adapt=True, partner=FS, narrow=0.5)
IP = part("GT_I_Props", "interior", "props", adapt=True, partner=IS, narrow=0.5)
OBJ = [0]


def objects(on=True):
    """Начало (True) / конец (False) участка с вещами: гладкие тела уходят в Props; архитектура остаётся как была."""
    OBJ[0] += 1 if on else -1
    FS.force, IS.force = (FP, IP) if OBJ[0] > 0 else (None, None)
    FR.force, IR.force = (FP, IP) if OBJ[0] > 0 else (None, None)


FABRIC = (BLUE, NAVY, VELVET, CRIMSON)  # ткань — на тихий материал (Quiet): квадраты едва заметны
SL = part("GT_S_All", "silhouette", "smooth", limit=99)


def arch(hw, h, s, d=0.0, y0=0.0):
    """Проём со ступенчатым верхом (две ступени s), расширенный на d; низ на y0."""
    r = [(hw + d, y0), (hw + d, h - 2 * s + d), (hw - s + d, h - 2 * s + d), (hw - s + d, h - s + d), (hw - 2 * s + d, h - s + d),
         (hw - 2 * s + d, h + d)]
    return [(-x, y) for x, y in r] + r[::-1]


def slab(p, axis, fixed, out, depth, a0, a1, y0, y1, color):
    """Накладка на стену: axis 'x' — стена x = fixed (вдоль z от a0 до a1), 'z' — стена z = fixed; out — куда выступает."""
    a0, a1 = sorted((a0, a1))
    lo, hi = sorted((fixed - out * 0.05, fixed + out * depth))
    if axis == "x":
        p.box(lo, hi, y0, y1, a0, a1, color)
    else:
        p.box(a0, a1, y0, y1, lo, hi, color)


def quad(p, axis, fixed, out, a0, a1, y0, y1, color):
    """Плоский квадрат на стене (клетка витража), лицом в сторону out."""
    if axis == "x":
        pts = [(fixed, y0, a0), (fixed, y0, a1), (fixed, y1, a1), (fixed, y1, a0)]
        p.plane(pts, [], (out, 0, 0), color)
    else:
        pts = [(a0, y0, fixed), (a1, y0, fixed), (a1, y1, fixed), (a0, y1, fixed)]
        p.plane(pts, [], (0, 0, out), color)


def outline(hw, y0, y1, d=0.0):
    """Контур окна со ступенчатым верхом: полные ряды до y1, выше — каждый ряд уже на клетку с каждой стороны."""
    r = [(hw + d, y0 - d)]
    cur, y = hw, y1
    while cur > 0.5 + 1e-6:
        r += [(cur + d, y + d), (cur - 1 + d, y + d)]
        cur, y = cur - 1, y + 1
    r.append((cur + d, y + d))
    return [(-x, yy) for x, yy in r] + r[::-1]


def stained(G, S, R, axis, fixed, out, a, y0, hw, y1, frame=GOLD):
    """Витраж: клетки 1 × 1 цветного стекла на тёмной свинцовой подложке, золотая рама, мраморный подоконник.
    Посередине — золото и рубин, по бокам — синее и голубое, наверху — золото."""
    rows = []
    cur, y = hw, y0
    while y < y1:
        rows.append((y, cur))
        y += 1
    while cur > 0.5 + 1e-6:
        cur -= 1
        rows.append((y, cur))
        y += 1
    top = y
    n_full = int(round(2 * hw))
    for y, w in rows:
        k = int(round(2 * w))
        for i in range(k):
            col = i + (n_full - k) // 2  # номер столбца в полной ширине
            mid = col == n_full // 2
            row = int(y - y0)
            if y >= y1:
                c = G_GOLD
            elif mid:
                c = G_GOLD if row % 2 == 0 else G_RED
            elif min(col, n_full - 1 - col) == 0:
                c = G_BLUE if row % 2 == 0 else G_SKY
            else:
                c = G_SKY if row % 2 == 0 else G_GREEN if row % 4 == 1 else G_BLUE
            a0 = a - w + i + 0.07
            quad(G, axis, fixed + out * 0.24, out, a0, a0 + 0.86, y + 0.07, y + 0.93, c)
    # свинцовая подложка ступенями (полные ряды — одним бруском)
    slab(S, axis, fixed, out, 0.12, a - hw, a + hw, y0, y1, G_LEAD)
    for y, w in rows:
        if y >= y1:
            slab(S, axis, fixed, out, 0.12, a - w, a + w, y, y + 1, G_LEAD)
    # рама: та же ступенчатая форма, выступает
    o, i = outline(hw, y0, y1, 0.5), outline(hw, y0, y1, 0.0)
    lo, hi = sorted((fixed - out * 0.05, fixed + out * 0.42))
    if axis == "x":
        S.frame_zy([(a + u, v) for u, v in o], [(a + u, v) for u, v in i], lo, hi, frame)
    else:
        S.frame_xy([(a + u, v) for u, v in o], [(a + u, v) for u, v in i], lo, hi, frame)
    # подоконник
    slab(R, axis, fixed, out, 0.9, a - hw - 1, a + hw + 1, y0 - 1.0, y0 - 0.5, IVORY2)
    return top


def crown(S, axis, fixed, out, a, y, w, h, gem=RUBY, big=False):
    """Корона-эмблема: обруч и зубцы (по краям и посередине — высокие), камень посередине (гладкая накладка)."""
    slab(S, axis, fixed, out, 0.3, a - w, a + w, y, y + h * 0.35, GOLD)
    for k in range(5 if big else 3):
        u = a - w + (2 * w) * k / (4 if big else 2)
        hk = h * (1.0 if k % 2 == 0 or not big else 0.7)
        slab(S, axis, fixed, out, 0.3, u - w * 0.12, u + w * 0.12, y + h * 0.3, y + hk, GOLD)
    slab(S, axis, fixed + out * 0.26, out, 0.2, a - w * 0.18, a + w * 0.18, y + h * 0.05, y + h * 0.3, gem)


def banner(Q, S, axis, fixed, out, a, y0, y1, hw, cloth=VELVET):
    """Знамя: полотнище с золотой каймой и короной, золотой прут сверху, раздвоенный низ."""
    slab(Q, axis, fixed, out, SKIN + 0.05, a - hw, a + hw, y0 + 0.6, y1, cloth)
    for s in (-1, 1):  # раздвоенный низ: два хвоста
        slab(Q, axis, fixed, out, SKIN + 0.05, a + s * hw, a + s * hw * 0.2, y0, y0 + 0.6, cloth)
    slab(S, axis, fixed, out, SKIN + 0.17, a - hw, a + hw, y1 - 0.55, y1 - 0.3, GOLD)
    slab(S, axis, fixed, out, SKIN + 0.17, a - hw, a + hw, y0 + 0.6, y0 + 0.85, GOLD)
    slab(S, axis, fixed, out, 0.5, a - hw - 0.35, a + hw + 0.35, y1, y1 + 0.35, GOLD2)
    crown(S, axis, fixed + out * (SKIN + 0.1), out, a, (y0 + y1) / 2 - 0.2, hw * 0.62, hw * 0.9)


def coins(S, x, z, y0, n, r=1.25, t=0.5):
    """Стопка монет (восьмигранные диски, через одну темнее)."""
    for k in range(n):
        dx = 0.14 * (k % 2)
        S.prism_xz(K.octa(x + dx, z, r, r, r * 0.42), y0 + k * t, y0 + (k + 1) * t - 0.04, COIN if k % 2 == 0 else GOLD2)


def anchor(p, lo, hi):
    """Две крошечные скрытые грани в углах (lo, hi): габариты детали — ровно этот брус, его центр целый. Материал с
    квадратами привязан к центру детали — так клетки рисунка совпадают с сеткой блоков."""
    layer = p.bm.loops.layers.float_color["tone"]
    for (x, y, z), d in ((lo, 0.01), (hi, -0.01)):
        f = p.bm.faces.new([p.bm.verts.new(K.P(*q)) for q in ((x, y, z), (x + d, y, z), (x, y + d, z))])
        for loop in f.loops:
            loop[layer] = (*K.rgb(GOLD2), 1.0)


# ══ ФАСАД: дворец ═════════════════════════════════════════════════════════════════════════════════════════════
# Светлый мрамор, золотые пилястры и пояса, синий фриз с золотыми розетками, витражные окна со ступенчатым верхом,
# посередине фасада — выступ с балконом, большим витражом и золотой короной над карнизом; красные знамёна.
# Полировка (2026-11-20): поле стен теплее мрамора (этаж отделяется от белой башни), руст на углах, в центре выступа —
# синее поле в золотой рамке: издалека центр фасада — самое яркое пятно этажа.

FACES = (("z", -FZ, -1, FX), ("z", FZ, 1, FX), ("x", -FX, -1, FZ), ("x", FX, 1, FZ))  # ось, плоскость, наружу, полуширина

# стены — тёплый мрамор (поле), отделка — светлый мрамор и золото
FR.plane([(-FX, YB, -FZ), (FX, YB, -FZ), (FX, YT, -FZ), (-FX, YT, -FZ)], [], (0, 0, -1), WALL)
FR.plane([(-FX, YB, FZ), (FX, YB, FZ), (FX, YT, FZ), (-FX, YT, FZ)], [], (0, 0, 1), WALL)
for s in (-1, 1):
    FR.plane([(s * FX, YB, -FZ), (s * FX, YB, FZ), (s * FX, YT, FZ), (s * FX, YT, -FZ)], [], (s, 0, 0), WALL)

for axis, fixed, out, half in FACES:
    # цоколь, золотой пояс над ним; антаблемент: золотой пояс, синий фриз с розетками, карниз
    slab(FR, axis, fixed, out, 0.88, -half - 0.88, half + 0.88, -1, 1, IVORY2)
    slab(FS, axis, fixed, out, 1.02, -half - 1.02, half + 1.02, 1, 1.4, GOLD)
    slab(FS, axis, fixed, out, 0.5, -half - 0.5, half + 0.5, 14.6, 15.0, GOLD)
    slab(FQ, axis, fixed, out, 0.42, -half - 0.42, half + 0.42, 15.0, 17.0, BLUE)
    slab(FS, axis, fixed, out, 1.3, -half - 1.3, half + 1.3, 17.0, 17.6, GOLD)
    slab(FR, axis, fixed, out, 0.88, -half - 0.88, half + 0.88, 17.6, 19.0, IVORY2)
    k = -half + 2.0
    while k < half - 1.0:
        if not (axis == "z" and out < 0 and abs(k) < 6.5):  # над выступом — корона
            slab(FS, axis, fixed + out * 0.4, out, 0.3, k - 0.5, k + 0.5, 15.5, 16.5, GOLD)
        k += 3.0
    # угловые пилястры (охватывают угол)
    for e in (-1, 1):
        slab(FR, axis, fixed, out, 0.88, e * (half - 2.0), e * (half + 0.88), 1.4, 14.6, IVORY)
        slab(FS, axis, fixed, out, 1.1, e * (half - 2.2), e * (half + 1.1), 13.6, 14.6, GOLD)
        slab(FS, axis, fixed, out, 1.1, e * (half - 2.2), e * (half + 1.1), 1.4, 2.0, GOLD2)
        # руст: гладкие камни через один длинные и короткие — угол читается издалека
        for k, y in enumerate((2.4, 4.6, 6.8, 9.0, 11.2)):
            w = 2.7 if k % 2 == 0 else 1.6
            slab(FS, axis, fixed, out, 1.02, e * (half - w), e * (half + 1.02), y, y + 1.8, IVORY2)

# перед: выступ с балконом посередине
CX = 5.5
FR.box(-CX, CX, -1, 17.0, -FZ - 1.5, -FZ + 0.05, IVORY)
slab(FS, "z", -FZ - 1.5, -1, 0.3, -CX - 0.3, CX + 0.3, 14.6, 15.0, GOLD)
for e in (-1, 1):  # пилястры выступа
    FR.box(e * (CX - 1.5), e * (CX + 0.5), 1.4, 14.6, -FZ - 2.3, -FZ - 1.45, IVORY)
    FS.box(e * (CX - 1.7), e * (CX + 0.7), 13.6, 14.6, -FZ - 2.5, -FZ - 1.45, GOLD)
    FS.box(e * (CX - 1.7), e * (CX + 0.7), 1.4, 2.0, -FZ - 2.5, -FZ - 1.45, GOLD2)
# синее поле в золотой рамке между пилястрами выступа: центр фасада — самое яркое пятно этажа издалека
slab(FS, "z", -FZ - 1.5, -1, 0.1, -3.9, 3.9, 1.7, 14.5, GOLD)
slab(FQ, "z", -FZ - 1.5, -1, 0.22, -3.6, 3.6, 2.0, 14.2, BLUE)
top = stained(FG, FS, FR, "z", -FZ - 1.72, -1, 0.0, 6.0, 2.5, 11.0)
# балкон: плита на ступенчатых консолях, балясины, перила
FR.box(-4.5, 4.5, 4.4, 5.0, -FZ - 4.5, -FZ - 1.45, IVORY2)
for k in (-3.4, 3.4):
    FR.box(k - 0.75, k + 0.75, 3.0, 4.4, -FZ - 2.8, -FZ - 1.45, IVORY2)
    FR.box(k - 0.75, k + 0.75, 3.7, 4.4, -FZ - 3.8, -FZ - 2.75, IVORY2)
# под балконом — красный геральдический щит с короной в золотой раме (на синем поле)
slab(FS, "z", -FZ - 1.5, -1, 0.55, -2.3, 2.3, 1.6, 4.2, GOLD2)
slab(FQ, "z", -FZ - 2.0, -1, 0.2, -1.9, 1.9, 1.9, 3.9, VELVET)
crown(FS, "z", -FZ - 2.15, -1, 0.0, 2.3, 1.2, 1.3, big=True)
for k in range(-4, 5):
    FS.box(k - 0.22, k + 0.22, 5.0, 6.3, -FZ - 4.2, -FZ - 3.76, GOLD)
for e in (-1, 1):
    for z in (-FZ - 3.0, -FZ - 2.0):
        FS.box(e * 4.22, e * 3.78, 5.0, 6.3, z - 0.22, z + 0.22, GOLD)
FS.box(-4.6, 4.6, 6.3, 6.7, -FZ - 4.4, -FZ - 3.56, GOLD)
for e in (-1, 1):
    FS.box(e * 4.6, e * 4.0, 6.3, 6.7, -FZ - 4.4, -FZ - 1.45, GOLD)
objects(True)
# корона над карнизом выступа: обруч с камнями, пять зубцов с шарами
FR.box(-4.5, 4.5, 15.0, 17.0, -FZ - 2.3, -FZ - 1.45, GOLD)
for k, (u, hk) in enumerate(((-4.0, 19.0), (-2.0, 18.4), (0.0, 19.0), (2.0, 18.4), (4.0, 19.0))):
    FS.cone([(u - 0.8, 16.98, -FZ - 2.2), (u + 0.8, 16.98, -FZ - 2.2), (u + 0.8, 16.98, -FZ - 1.5), (u - 0.8, 16.98, -FZ - 1.5)],
            (u, hk - 0.4, -FZ - 1.85), GOLD)
    FS.box(u - 0.3, u + 0.3, hk - 0.6, hk, -FZ - 2.15, -FZ - 1.55, GOLD2)
for u, gem in ((-3.0, SAPPHIRE), (0.0, RUBY), (3.0, EMERALD)):
    FS.box(u - 0.75, u + 0.75, 15.25, 16.75, -FZ - 2.62, -FZ - 2.25, gem)
    FS.box(u - 0.5, u - 0.15, 16.2, 16.55, -FZ - 2.72, -FZ - 2.6, GLINT)

objects(False)
# окна и знамёна: перед — по окну с каждой стороны выступа и знамя между; бока — три окна и четыре знамени;
# тыл — два окна и три знамени
for e in (-1, 1):
    stained(FG, FS, FR, "z", -FZ, -1, e * 11.5, 4.0, 1.5, 11.0)
    crown(FS, "z", -FZ, -1, e * 11.5, 12.6, 1.1, 1.4)
    banner(FQ, FS, "z", -FZ, -1, e * 7.5, 6.0, 14.2, 1.0)
for s in (-1, 1):
    for z in (-8.0, 0.0, 8.0):
        stained(FG, FS, FR, "x", s * FX, s, z, 4.0, 1.5, 11.0)
        crown(FS, "x", s * FX, s, z, 12.6, 1.1, 1.4)
    for z in (-12.5, -4.0, 4.0, 12.5):
        banner(FQ, FS, "x", s * FX, s, z, 7.0, 14.2, 0.9)
for e in (-1, 1):
    stained(FG, FS, FR, "z", FZ, 1, e * 9.0, 4.0, 1.5, 11.0)
    crown(FS, "z", FZ, 1, e * 9.0, 12.6, 1.1, 1.4)
    banner(FQ, FS, "z", FZ, 1, e * 13.5, 7.0, 14.2, 1.0)
banner(FQ, FS, "z", FZ, 1, 0.0, 6.0, 14.2, 1.2)
anchor(FR, (-21, -1, -22), (21, 19, 20))
anchor(FQ, (-21, -1, -22), (21, 19, 20))
anchor(FP, (-21, -1, -22), (21, 19, 20))

# ══ ИНТЕРЬЕР: тронный зал ═════════════════════════════════════════════════════════════════════════════════════
# Мраморный пол в крупную клетку, синие бархатные стены с мраморной панелью, по бокам колоннада со ступенчатыми
# арками и красными знамёнами, в простенках витражи, кессонный потолок с люстрой. Красная дорожка ведёт от лифта
# к помосту; трон стоит перед балдахином — тёмная бархатная ниша с золотым ореолом и короной: на тёмном фоне
# золотой трон — самое яркое в зале.

W, ZB, C = 16.88, 15.88, 18.0  # стены и потолок изнутри
ZF = -9.0  # задняя стена с нишей балдахина
DOOR = (3.5, 10.5, 0.9)
TIERS = ((10, -15, 4), (8, -15, 3), (6, -15, 2))  # ступени помоста: полуширина, z0, z1
NICHE = (7.0, 16.5, -15.0)  # ниша балдахина: полуширина, высота, задняя стенка
COLS = (11.0, 5.0, -1.0)  # колонны (z), по обе стороны зала на x = ±12
CXI = 12.0
THRONE = (0.0, 3.0, -4.3)  # место предмета (масштаб показа 2.8, лицом к лифту)

# пол: мрамор в клетку 4 × 4
for i in range(-5, 5):
    for j in range(-3, 4):
        x0, x1 = max(i * 4, -W), min(i * 4 + 4, W)
        z0, z1 = max(j * 4, ZF), min(j * 4 + 4, ZB)
        if x1 - x0 > 0.01 and z1 - z0 > 0.01:
            IR.plane([(x0, 0.02, z0), (x1, 0.02, z0), (x1, 0.02, z1), (x0, 0.02, z1)], [], (0, 1, 0),
                     IVORY if (i + j) % 2 == 0 else SLATE)
# стены: синий бархат; потолок — синий между кессонами
IR.plane([(-W, C, ZF), (W, C, ZF), (W, C, ZB), (-W, C, ZB)], [], (0, -1, 0), BLUE)
IR.plane([(x, y, ZB) for x, y in [(-W, 0)] + arch(*DOOR) + [(W, 0), (W, C), (-W, C)]], [], (0, 0, -1), BLUE)
for s in (-1, 1):
    IR.plane([(s * W, 0, ZF), (s * W, 0, ZB), (s * W, C, ZB), (s * W, C, ZF)], [], (-s, 0, 0), BLUE)
NW, NH, NZ = NICHE
IR.plane([(x, y, ZF) for x, y in [(-W, 0)] + arch(NW, NH, 1.0) + [(W, 0), (W, C), (-W, C)]], [], (0, 0, 1), BLUE)

# мраморная панель понизу стен с золотой кромкой, карниз под потолком
for s in (-1, 1):
    slab(IR, "x", s * W, -s, 0.4, ZF, ZB, 0, 3, IVORY)
    slab(IS, "x", s * W, -s, 0.55, ZF, ZB, 3, 3.35, GOLD)
    slab(IR, "x", s * W, -s, 0.88, ZF, ZB, 16, C, IVORY)
    slab(IS, "x", s * W, -s, 1.02, ZF, ZB, 15.6, 16, GOLD)
    for zf, out, a, b in ((ZB, -1, s * (DOOR[0] + 1.3), s * W), (ZF, 1, s * (NW + 1.3), s * W)):
        a, b = sorted((a, b))
        slab(IR, "z", zf, out, 0.4, a, b, 0, 3, IVORY)
        slab(IS, "z", zf, out, 0.55, a, b, 3, 3.35, GOLD)
    for zf, out in ((ZB, -1), (ZF, 1)):
        a, b = sorted((s * (DOOR[0] + 1.3 if zf == ZB else NW + 1.3), s * W))
        slab(IR, "z", zf, out, 0.88, a if zf == ZB else a, b, 16, C, IVORY)
        slab(IS, "z", zf, out, 1.02, a, b, 15.6, 16, GOLD)
slab(IR, "z", ZB, -1, 0.88, -DOOR[0] - 1.3, DOOR[0] + 1.3, 16, C, IVORY)
slab(IS, "z", ZB, -1, 1.02, -DOOR[0] - 1.3, DOOR[0] + 1.3, 15.6, 16, GOLD)

# двери лифта в золотой раме со ступенчатым верхом (размер дверей задан лифтом, не сеткой)
IS.frame_xy(arch(*DOOR, 1.3), arch(*DOOR, 0.0), 15.95, 15.2, GOLD)
IS.frame_xy(arch(*DOOR, 0.4), arch(*DOOR, 0.03), 15.22, 15.0, GOLD2)
for s in (-1, 1):
    IS.box(s * 0.06, s * 3.5, 0, 10.5, 16.15, 16.45, GOLD)
    IS.box(s * 1.35, s * 2.15, 5.0, 5.8, 16.0, 16.17, GOLD2)
crown(IS, "z", ZB, -1, 0.0, 12.0, 1.6, 2.0, big=True)

# колоннада: база, ствол, золотая капитель, ступенчатые арки под архитравом, поперечные балки к стенам
for s in (-1, 1):
    x0, x1 = sorted((s * (CXI - 1.0), s * (CXI + 1.0)))
    for z in COLS:
        IR.box(s * (CXI - 1.5), s * (CXI + 1.5), 0, 1.0, z - 1.5, z + 1.5, IVORY2)
        IS.box(s * (CXI - 1.25), s * (CXI + 1.25), 1.0, 1.4, z - 1.25, z + 1.25, GOLD)
        IR.box(x0, x1, 1.4, 13.0, z - 1.0, z + 1.0, IVORY)
        IR.box(s * (CXI - 1.5), s * (CXI + 1.5), 13.0, 14.0, z - 1.5, z + 1.5, GOLD)
        IR.box(s * (CXI - 1.0), s * (CXI + 1.0), 13.4, 14.6, z - 2.5, z + 2.5, IVORY2)
        IR.box(s * (CXI + 1.0), s * W, 16.0, C, z - 0.75, z + 0.75, IVORY)  # балка над боковым проходом
        slab(IR, "x", s * W, -s, 0.5, z - 1.0, z + 1.0, 3.35, 15.6, IVORY)  # пилястра на стене напротив колонны
        slab(IS, "x", s * W, -s, 0.7, z - 1.2, z + 1.2, 14.6, 15.6, GOLD)
        # знамя на стволе, лицом к проходу
        banner(IQ, IS, "x", s * (CXI - 1.0), -s, z, 6.0, 12.4, 0.8)
    # архитрав от задней стены до лифта
    IR.box(s * (CXI - 1.5), s * (CXI + 1.5), 14.6, C, ZF, ZB, IVORY)
    slab(IS, "x", s * (CXI - 1.5), -s, 0.14, ZF, ZB, 15.2, 15.6, GOLD)
    # пилястра колоннады у задней стены
    IR.box(s * (CXI - 1.0), s * (CXI + 1.0), 0, 14.6, ZF, ZF + 1.0, IVORY)
    IS.box(s * (CXI - 1.3), s * (CXI + 1.3), 13.0, 14.0, ZF - 0.02, ZF + 1.3, GOLD)

# витражи в простенках боковых стен
for s in (-1, 1):
    for z in (8.0, 2.0, -4.0):
        stained(IG, IS, IR, "x", s * W, -s, z, 5.0, 1.5, 12.0)

# кессонный потолок: балки поперёк (над колоннами) и вдоль, в кессонах — золотые розетки
for z in COLS + (ZF + 0.75,):
    IR.box(-CXI + 1.5, CXI - 1.5, 16.6, C, z - 0.75, z + 0.75, IVORY)
for x in (-4.0, 4.0):
    IR.box(x - 0.75, x + 0.75, 16.6, C, ZF, ZB, IVORY)
for z0, z1 in ((COLS[0], ZB), (COLS[1], COLS[0]), (COLS[2], COLS[1]), (ZF + 1.5, COLS[2])):
    for x in (0.0,):  # розетки — только над дорожкой (бюджет треугольников)
        zc = (z0 + z1) / 2
        IS.prism_xz(K.octa(x, zc, 1.0, 1.0, 0.4), 17.5, C + 0.02, GOLD)

objects(True)
# люстра над дорожкой: цепь, ярусы золотых обручей, свечи с огоньками, хрустальные подвески
LZ = 8.0
IS.box(-0.2, 0.2, 14.0, C, LZ - 0.2, LZ + 0.2, GOLD2)
for y, r, n in ((12.6, 3.0, 8), (13.8, 1.8, 6)):
    IS.frame_xz(K.octa(0.0, LZ, r + 0.4, r + 0.4, (r + 0.4) * 0.42), K.octa(0.0, LZ, r, r, r * 0.42), y, y + 0.45, GOLD)
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        cx, cz = r * 0.98 * math.cos(a), LZ + r * 0.98 * math.sin(a)
        IS.box(cx - 0.18, cx + 0.18, y + 0.45, y + 1.15, cz - 0.18, cz + 0.18, "FFF6E0")
        IG.box(cx - 0.12, cx + 0.12, y + 1.15, y + 1.5, cz - 0.12, cz + 0.12, FLAME)
        if n == 8:  # хрустальные подвески — у нижнего обруча
            IG.box(cx - 0.1, cx + 0.1, y - 0.7, y - 0.05, cz - 0.1, cz + 0.1, G_SKY)
IS.prism_xz(K.octa(0.0, LZ, 0.9, 0.9, 0.38), 11.8, 14.0, GOLD)
IS.prism_xz(K.octa(0.0, LZ, 0.5, 0.5, 0.2), 11.2, 11.8, GOLD2)

objects(False)
# красная дорожка от лифта до помоста, золотые кромки
IQ.box(-3, 3, 0.02, 0.02 + SKIN, 4, 15.6, VELVET)
for s in (-1, 1):
    IS.box(s * 3.0, s * 3.35, 0.02, 0.2, 4, 15.6, GOLD)

# помост: мраморные ступени с золотой кромкой, по ступеням — та же дорожка; наверху — красный бархат под троном
for i, (hw, z0, z1) in enumerate(TIERS):
    IR.box(-hw, hw, i, i + 1, z0, z1, IVORY)
    IS.box(-hw - 0.02, hw + 0.02, i + 0.75, i + 1.02, z1 - 0.02, z1 + 0.12, GOLD)
    if i < 2:
        IQ.box(-3, 3, i + 1, i + 1 + SKIN, TIERS[i + 1][2], z1, VELVET)
        slab(IQ, "z", z1, 1, SKIN, -3, 3, i, i + 0.74, VELVET)
IQ.box(-5.5, 5.5, 3, 3 + SKIN, NZ, TIERS[2][2] - 0.5, VELVET)
slab(IQ, "z", TIERS[2][2], 1, SKIN, -3, 3, 2, 2.74, VELVET)

objects(True)
# канделябры на первой ступени помоста — по бокам трона
CANDLE = (8.6, 1.0)  # x (по обе стороны), z
for s in (-1, 1):
    x, z, y = s * CANDLE[0], CANDLE[1], 1.0
    IS.prism_xz(K.octa(x, z, 0.8, 0.8, 0.32), y, y + 0.5, GOLD2)
    IS.box(x - 0.22, x + 0.22, y + 0.5, y + 5.6, z - 0.22, z + 0.22, GOLD)
    IS.box(x - 1.3, x + 1.3, y + 5.2, y + 5.6, z - 0.22, z + 0.22, GOLD)
    for dx in (-1.1, 0.0, 1.1):
        y0 = y + (5.6 if dx else 5.9)
        if not dx:
            IS.box(x - 0.3, x + 0.3, y + 5.6, y + 5.9, z - 0.3, z + 0.3, GOLD)
        IS.box(x + dx - 0.16, x + dx + 0.16, y0, y0 + 0.8, z - 0.16, z + 0.16, "FFF6E0")
        IG.box(x + dx - 0.11, x + dx + 0.11, y0 + 0.8, y0 + 1.15, z - 0.11, z + 0.11, FLAME)

# сундуки с монетами у лифта
for s in (-1, 1):
    x, z = s * 14.8, 13.8
    IQ.box(x - 1.5, x + 1.5, 0.0, 1.8, z - 1.0, z + 1.0, CRIMSON)
    IR.box(x - 1.6, x + 1.6, 1.8, 2.6, z - 1.1, z + 1.1, GOLD)
    for dx in (-1.0, 1.0):
        IS.box(x + dx - 0.25, x + dx + 0.25, -0.0, 1.82, z - 1.06, z + 1.06, GOLD2)
    IS.box(x - 0.35, x + 0.35, 0.9, 1.5, z - 1.12, z - 0.98, GOLD)
    coins(IS, x - 0.6, z + 0.1, 2.6, 2, 0.55, 0.25)

objects(False)
# ══ Балдахин: ниша тёмного бархата в складках, золотой ореол за троном, занавеси, полог с бахромой и короной ════
IR.plane([(-NW, 0, NZ), (NW, 0, NZ), (NW, NH, NZ), (-NW, NH, NZ)], [], (0, 0, 1), NAVY)
for s in (-1, 1):
    IR.plane([(s * NW, 0, NZ), (s * NW, 0, ZF), (s * NW, NH, ZF), (s * NW, NH, NZ)], [], (-s, 0, 0), NAVY)
IR.plane([(-NW, NH, NZ), (NW, NH, NZ), (NW, NH, ZF), (-NW, NH, ZF)], [], (0, -1, 0), NAVY)
# складки задника: вертикальные полосы через стад
for k in range(-6, 7, 2):
    IQ.box(k - 0.5, k + 0.5, 3.0, NH - 0.02, NZ - 0.05, NZ + 0.35, NAVY)
# ореол: восьмиугольное кольцо и лучи
HY = 11.2
IS.frame_xy(K.ngon(0.0, HY, 5.2, 16, 0.0), K.ngon(0.0, HY, 4.6, 16, 0.0), NZ + 0.4, NZ + 0.75, GOLD2)
for k in range(16):
    a = 2 * math.pi * k / 16
    ca, sa = math.cos(a), math.sin(a)
    r0, r1, w = 5.4, 6.4 if k % 2 == 0 else 5.9, 0.24
    pts = [(r0 * ca - w * sa, HY + r0 * sa + w * ca), (r0 * ca + w * sa, HY + r0 * sa - w * ca),
           (r1 * ca, HY + r1 * sa)]
    if HY + r1 * sa < NH - 0.3 and abs(r1 * ca) < NW - 0.3:
        IS.prism_xy(pts, NZ + 0.4, NZ + 0.7, GOLD2)
# занавеси: красный бархат по краям ниши, подхваты с кистями
for s in (-1, 1):
    x0, x1 = sorted((s * (NW - 1.6), s * (NW + 0.2)))
    for k, (dx, dz) in enumerate(((0.0, 0.0), (0.55, 0.3), (1.1, 0.0))):
        a0 = s * (NW + 0.2) - s * dx
        xa, xb = sorted((a0, a0 - s * 0.55))
        IQ.box(xa, xb, 0.0, NH - 1.0, ZF - 0.9 - dz, ZF - 0.3 - dz, VELVET if k != 1 else CRIMSON)
    IS.box(x0 - 0.05, x1 + 0.05, 6.0, 6.5, ZF - 1.35, ZF - 0.15, GOLD)
    IS.box(s * (NW - 1.75) - 0.25, s * (NW - 1.75) + 0.25, 4.6, 6.0, ZF - 1.0, ZF - 0.5, GOLD2)
# рама ниши — ступенчатая, золото и мрамор
IR.frame_xy(arch(NW, NH, 1.0, 1.3), arch(NW, NH, 1.0, 0.0), ZF - 0.05, ZF + 0.6, IVORY2)
IS.frame_xy(arch(NW, NH, 1.0, 0.35), arch(NW, NH, 1.0, 0.02), ZF + 0.55, ZF + 0.85, GOLD)
# полог над троном: выступает из ниши, бахрома зубцами, корона на пологе
PZ0, PZ1, PY = ZF - 0.5, -3.0, 15.0
IQ.box(-4.8, 4.8, PY - 0.3, PY + 1.2, PZ0, PZ1, CRIMSON)
IS.box(-5.0, 5.0, PY - 0.35, PY + 0.1, PZ1 - 0.3, PZ1 + 0.2, GOLD)
for k in range(-4, 5):
    IS.box(k - 0.3, k + 0.3, PY - 0.9, PY - 0.3, PZ1 - 0.1, PZ1 + 0.2, GOLD if k % 2 == 0 else GOLD2)
for s in (-1, 1):
    for z in (PZ0 + 1.5, PZ0 + 3.5, PZ0 + 5.5):
        IS.box(s * 4.7, s * 5.0, PY - 0.9, PY - 0.3, z - 0.3, z + 0.3, GOLD)
crown(IS, "z", PZ1 + 0.2, 1, 0.0, PY + 0.4, 2.2, 2.2, big=True)
anchor(IR, (-17, 0, -17), (17, 18, 17))
anchor(IQ, (-17, 0, -17), (17, 18, 17))
anchor(IP, (-17, 0, -17), (17, 18, 17))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════

SL.box(-FX, FX, YB, YT, -FZ, FZ, WALL)
SL.box(-FX - 0.9, FX + 0.9, -1, 1, -FZ - 0.9, FZ + 0.9, IVORY2)
SL.box(-FX - 0.45, FX + 0.45, 15, 17, -FZ - 0.45, FZ + 0.45, BLUE)
SL.box(-FX - 1.3, FX + 1.3, 17, 17.6, -FZ - 1.3, FZ + 1.3, GOLD)
SL.box(-CX, CX, -1, 17, -FZ - 1.5, -FZ, IVORY)
SL.box(-4.5, 4.5, 15, 19, -FZ - 2.3, -FZ - 1.5, GOLD)
SL.box(-3.6, 3.6, 2, 14.2, -FZ - 1.62, -FZ - 1.5, BLUE)
SL.box(-2.5, 2.5, 6, 13, -FZ - 1.75, -FZ - 1.55, G_BLUE)
SL.box(-4.5, 4.5, 4.4, 6.7, -FZ - 4.5, -FZ - 1.5, GOLD2)
for e in (-1, 1):
    SL.box(e * 10.0, e * 13.0, 4, 12, -FZ - 0.2, -FZ, G_BLUE)
    SL.box(e * 6.5, e * 8.5, 6, 14, -FZ - 0.2, -FZ, VELVET)
    SL.box(e * 9.5, e * 7.5, 4, 12, FZ, FZ + 0.2, G_BLUE)
    SL.box(e * 12.5, e * 14.5, 7, 14, FZ, FZ + 0.2, VELVET)
    for z in (-8.0, 0.0, 8.0):
        SL.box(e * FX, e * (FX + 0.2), 4, 12, z - 1.5, z + 1.5, G_BLUE)
    for z in (-12.5, -4.0, 4.0, 12.5):
        SL.box(e * FX, e * (FX + 0.2), 7, 14, z - 0.9, z + 0.9, VELVET)

# ══ СБОРКА, ЗАТЕНЕНИЕ ═════════════════════════════════════════════════════════════════════════════════════════

collection = bpy.data.collections.new("GoldenThroneFloor")
bpy.context.scene.collection.children.link(collection)


def proxy(name, y0, y1):
    """Соседний этаж башни (заслоняет при затенении, виден на рендерах)."""
    me = bpy.data.meshes.new(name)
    x, z = HX, HZ
    pts = [K.P(sx * x, y, sz * z) for y in (y0, y1) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    me.from_pydata(pts, [], [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    obj = bpy.data.objects.new(name, me)
    collection.objects.link(obj)
    return obj


above, below = proxy("TowerAbove", 19.0, 39.0), proxy("TowerBelow", -21.0, -1.0)
bpy.context.view_layer.update()
facade = [p for p in parts if p.tier == "facade" and p.material != "glass"]
interior = [p for p in parts if p.tier == "interior" and p.material != "glass"]
glow = [p for p in parts if p.material == "glass"]
silhouette = [p for p in parts if p.tier == "silhouette"]

# Свет игры объёма в зале не даёт (теней нет, лампы без теней только засвечивают, BUGS.md) — всё запечено в цвета
# вершин, без градиентов «для красоты»:
#   1) окклюзия — тень в углах, стыках, нишах и под выступами; сетку вершин под неё кладёт adaptive_cut только там,
#      где тень меняется (ровная стена остаётся одной гранью);
#   2) своя ровная яркость у каждой стороны блока — светлые и тёмные стороны объёмов.
TOL = float(next((f[4:] for f in FLAGS if f.startswith("tol=")), 0.07))
ML = int(next((f[3:] for f in FLAGS if f.startswith("ml=")), 6))  # предел линий разреза на грань зала (бюджет треугольников)
FORM_IN = {"up": 1.0, "pz": 0.96, "px": 0.88, "nx": 0.88, "nz": 0.84, "down": 0.74, "edge": 1.14}
FORM_OUT = {"up": 1.0, "pz": 0.95, "px": 0.86, "nx": 0.86, "nz": 0.97, "down": 0.70, "edge": 1.12}
print("FABRIC facade", FR.give_tones(FQ, FABRIC), "interior", IR.give_tones(IQ, FABRIC), flush=True)
if "nocoplanar" not in FLAGS:  # мерцание совпадающих граней — меньшая выдвигается
    print("COPLANAR", K.resolve_coplanar([p for p in parts if p.tier != "silhouette"]), flush=True)
print("LINES facade", K.adaptive_cut(facade, [above, below], radius=5.0, tol=TOL, fine=1.0, min_size=2.0), flush=True)
print("LINES interior", K.adaptive_cut(interior, radius=3.5, tol=TOL, fine=1.2, min_size=2.4, max_lines=ML), flush=True)
for p in sorted(parts, key=lambda q: q.partner is None):  # сначала детали с квадратами: они отдают узкие грани гладким
    p.finish(collection)
bpy.context.view_layer.update()
K.shade_parts(facade, extra=[above, below], radius=5.0, rays=32, form=FORM_OUT, floor_lo=0.34)
K.shade_parts(interior, radius=3.5, rays=32, form=FORM_IN, floor_lo=0.30)
K.flat_parts(silhouette + glow)
info = K.manifest(parts)
for name, d in info.items():
    print("PART", name, d["tier"], d["material"], d["tris"], d["size"], flush=True)
for tier in ("facade", "interior", "silhouette"):
    print("TIER", tier, sum(d["tris"] for d in info.values() if d["tier"] == tier), flush=True)

if "export" in FLAGS:
    path = os.path.join(REPO, "assets", "models", "floors", "GoldenThroneFloor.fbx")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    K.export_fbx([p.obj for p in parts], path)
    K.write_json(os.path.splitext(path)[0] + ".json", info)
    print("EXPORTED", path, flush=True)

# ══ ПРОВЕРОЧНЫЕ РЕНДЕРЫ ═══════════════════════════════════════════════════════════════════════════════════════

if "render" in FLAGS:
    scene = bpy.context.scene
    engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("Sky")
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.55, 0.72, 1.0, 1)
    bg.inputs["Strength"].default_value = 1.0
    scene.world = world
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 2.6
    sun.rotation_euler = (math.radians(52), 0, math.radians(-150))
    scene.collection.objects.link(sun)
    for p in parts:
        K.preview_material(p)
    grey = bpy.data.materials.new("Tower")
    grey.use_nodes = True
    next(n for n in grey.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.82, 0.78, 0.7, 1)
    above.data.materials.append(grey)
    below.data.materials.append(grey)
    # лампа зала (в игре — одна, под потолком)
    for name, at, energy, color in (("Hall", (0, 15.6, 4.0), 7000, (1.0, 0.95, 0.84)),):
        lamp = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT"))
        lamp.data.energy, lamp.data.color, lamp.data.shadow_soft_size = energy, color, 2.0
        lamp.data.use_shadow = False
        lamp.location = K.P(*at)
        scene.collection.objects.link(lamp)
    # оригинал предмета на помосте (масштаб показа 2.8, лицом к лифту)
    throne_path = os.path.join(REPO, "assets", "models", "art", "GoldenThrone.fbx")
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.fbx(filepath=throne_path)
    except Exception as err:  # noqa: BLE001
        print("THRONE_IMPORT_FAILED", err)
    throne = [o for o in bpy.data.objects if o not in before]
    if throne:
        img = bpy.data.images.load(os.path.join(REPO, "assets", "textures", "art", "GoldenThrone_color.png"))
        mat = bpy.data.materials.new("Throne")
        mat.use_nodes = True
        tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = img
        bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        root = bpy.data.objects.new("ThroneRoot", None)
        scene.collection.objects.link(root)
        for o in throne:
            if o.type == "MESH":
                o.data.materials.clear()
                o.data.materials.append(mat)
            if o.parent is None:
                o.parent = root
        root.scale = (2.8, 2.8, 2.8)
        root.rotation_euler = (0, 0, math.pi)
        root.location = K.P(THRONE[0], THRONE[1] + 0.07, THRONE[2])
    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.sensor_fit = "VERTICAL"
    cam_data.clip_start, cam_data.clip_end = 0.2, 800

    def shot(name, eye, target, fov=70, res=(1280, 720), hide=()):
        for o in bpy.data.objects:
            o.hide_render = any(o.name.startswith(h) for h in hide)
        scene.render.resolution_x, scene.render.resolution_y = res
        cam_data.angle_y = math.radians(fov)
        e, t = K.P(*eye), K.P(*target)
        cam.location = e
        cam.rotation_euler = (e - t).to_track_quat("Z", "Y").to_euler()
        scene.render.filepath = os.path.join(OUT, name + ".png")
        bpy.ops.render.render(write_still=True)
        print("SHOT", name, flush=True)

    inside = ("GT_S_",)
    outside = ("GT_S_", "Throne", "Hall")
    only = [f for f in FLAGS if f.startswith("shot=")]
    shots = {
        "f1_front": lambda: shot("f1_front", (0, 9, -84), (0, 9, -17), 30, hide=outside),
        "f2_low": lambda: shot("f2_low", (-36, -24, -68), (0, 8, -19), 38, hide=outside),
        "f3_three_quarter": lambda: shot("f3_three_quarter", (-50, 16, -60), (0, 8.5, -12), 34, hide=outside),
        "f4_side": lambda: shot("f4_side", (-82, 10, -6), (-18, 9, -6), 32, hide=outside),
        "f5_back": lambda: shot("f5_back", (32, 14, 74), (0, 9, 17), 32, hide=outside),
        "i1_lift": lambda: shot("i1_lift", (0, 5.5, 14.6), (0, 8.5, -8), 70, hide=inside),
        "i2_mid": lambda: shot("i2_mid", (0, 5.0, 6.5), (0, 9.0, -8), 70, hide=inside),
        "i3_side": lambda: shot("i3_side", (8.6, 5.5, 9.5), (-3.0, 7.5, -8), 70, hide=inside),
        "i4_back": lambda: shot("i4_back", (0, 6.5, 1.5), (0, 6.0, 16), 70, hide=inside),
        "i5_throne": lambda: shot("i5_throne", (5.0, 5.0, 4.5), (0, 9.5, -5.5), 62, hide=inside),
        "s1_silhouette": lambda: shot("s1_silhouette", (-50, 16, -60), (0, 8.5, -12), 34,
                                      hide=("GT_F_", "GT_I_", "Throne", "Hall")),
    }
    for key, run in shots.items():
        if not only or ("shot=" + key) in only:
            run()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "GoldenThroneFloor.blend"))
print("DONE", flush=True)
