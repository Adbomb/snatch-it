"""Этаж «Гигантский космический шлем» музея-небоскрёба — исследовательский корабль из мешей по эталону GoldenThrone v6
и TRexSkeleton v1 (утверждены владельцем 2026-11-21): крупные блоки, крупные квадраты по одному на стад
(MaterialVariant LegoSquaresFar / LegoSquaresQuiet), фаска рёбер, тени и яркость сторон — в цветах вершин.

Замысел (просьба владельца 2026-11-21: «впечатляющая космическая станция или исследовательский корабль, а не белая
комната с неоновыми полосками; шлем сразу привлекает внимание; глубокие сине-серые тона, яркие чистые акценты»):
  Снаружи — корпус корабля: тёмная сине-серая обшивка панелями с зазорами, цоколь с решётками, скошенный карниз со
  световой линией, четыре белые угловые колонны с оранжевыми поясами и навигационными огнями. Спереди — огромный
  золотой визор в белой раме (как у шлема): ступенчатый купол, блики, болты; по бокам — фонари шлема, внизу — синее
  шейное кольцо, над рамой — антенна. По бокам — солнечные батареи в золотых рамах и двигательные гондолы; сзади —
  три сопла с голубым свечением.
  Внутри — исследовательский отсек: скошенные углы и карниз со светом, стены панелями, силовые шпангоуты, иллюминаторы,
  пульты с экранами, стойки оборудования, трубы; двери лифта — шлюз с полосами «опасность». Шлем — на ступенчатом
  восьмигранном подиуме со светящимися кольцами, к нему наклонены четыре пилона-излучателя, над ним парит кольцо с
  прожектором; за ним — панорамное окно в космос: звёзды, планета с атмосферой, луна.
Детали (MeshPart): Rings — Plastic + LegoSquaresFar (обшивка, рамы, колонны), Quiet — LegoSquaresQuiet (палуба),
Smooth — SmoothPlastic, Glass — огни, экраны, окна в космос, свечение (без затенения).
Пишет assets/models/floors/SpaceHelmetFloor.fbx и .json, рендеры — в папку превью.
Запуск: blender --background --factory-startup --python scripts/blender/floor_space.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorkit as K  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
FLAGS = set(argv[2:])
os.makedirs(OUT, exist_ok=True)

# ── Палитра ────────────────────────────────────────────────────────────────────────────────────────────────────
WHITE0 = "FFFFFF"
HULL, HULL2, PLATE, PLATE2, PLATE3 = "34425E", "222C42", "4A5B7C", "40506E", "56688A"  # обшивка снаружи
WHITE, WHITE2, METAL = "E6ECF4", "C3CCDA", "8C98AE"
ORANGE, GOLD, GOLD2, GOLD_HI, YELLOW = "F07A1E", "F2B630", "C98A1A", "FFD45A", "F2C230"
BLUE, SOLAR, NAVY = "2A62D8", "1D3270", "0E1830"
CYAN, ICE, GLINT, RED, GREEN = "56D6FF", "8FE6FF", "FFF4D6", "FF4A4A", "4AFF8A"
# внутри — глубже и темнее: светлым остаётся шлем, рамы и чистые акценты
HULL_I, HULL2_I, PLATE_I, PLATE2_I, PANEL_I = "232D44", "1A2236", "33405C", "2C3852", "4A5A7A"
WHITE_I, DECK, DECK2 = "D6DEEA", "2A3550", "323F5C"
SPACE, PLANET, PLANET2, ATMO, MOON, LIGHT = "070D1C", "2858C8", "6FA4FF", "8FD8FF", "C8CCD8", "AFC4E6"
SCREEN, SCREEN2 = "3FA7FF", "FFB04A"
SHADE = (0.52, 0.52, 0.52)

HX, HZ, YB, YT = 18.0, 17.0, -1.0, 19.0
SK = 0.12
FX, FZ = HX + SK, HZ + SK
NARROW = 0.9
W, ZB, C = 16.88, 15.88, 18.0
ZF = -15.88

parts = []


def part(name, tier, material, **kw):
    p = K.Part(name, tier, material, WHITE0, SHADE, **kw)
    parts.append(p)
    return p


EDGE = 0.1
FS = part("SH_F_Smooth", "facade", "smooth", adapt=True)
FR = part("SH_F_Rings", "facade", "tile", adapt=True, partner=FS, narrow=NARROW, bevel=EDGE, bevel_min=1.0)
FQ = part("SH_F_Quiet", "facade", "tile", adapt=True, partner=FS, narrow=NARROW)
FG = part("SH_F_Glass", "facade", "glass", occlude=False)
IS = part("SH_I_Smooth", "interior", "smooth", adapt=True)
IR = part("SH_I_Rings", "interior", "tile", adapt=True, partner=IS, narrow=NARROW, bevel=EDGE, bevel_min=1.0)
IQ = part("SH_I_Quiet", "interior", "tile", adapt=True, partner=IS, narrow=NARROW)
IG = part("SH_I_Glass", "interior", "glass", occlude=False)
# Вещи этажа (статуи, мебель, механизмы, растения) — в стиле предметов и боссов: Plastic + LegoRingsD39Boss
# (решение владельца 2026-11-21, эталон — Крысиный король); узкие грани (< 0.5) — гладкие. Гладкие тела уходят
# в Props только на участках, отмеченных objects(True) … objects(False); архитектура остаётся как была.
FP = part("SH_F_Props", "facade", "props", adapt=True, partner=FS, narrow=0.5)
IP = part("SH_I_Props", "interior", "props", adapt=True, partner=IS, narrow=0.5)
OBJ = [0]


def objects(on=True):
    """Начало (True) / конец (False) участка с вещами: гладкие тела уходят в Props; архитектура остаётся как была."""
    OBJ[0] += 1 if on else -1
    FS.force, IS.force = (FP, IP) if OBJ[0] > 0 else (None, None)
    FR.force, IR.force = (FP, IP) if OBJ[0] > 0 else (None, None)


SL = part("SH_S_All", "silhouette", "smooth", limit=99)
QUIET = (DECK, DECK2)


# ── Помощники ──────────────────────────────────────────────────────────────────────────────────────────────────

def slab(p, axis, fixed, out, depth, a0, a1, y0, y1, color, back=0.05):
    """Накладка на стену: axis 'x' — стена x = fixed (вдоль z от a0 до a1), 'z' — стена z = fixed; out — куда выступает."""
    a0, a1 = sorted((a0, a1))
    lo, hi = sorted((fixed - out * back, fixed + out * depth))
    if axis == "x":
        p.box(lo, hi, y0, y1, a0, a1, color)
    else:
        p.box(a0, a1, y0, y1, lo, hi, color)


def quad(p, axis, fixed, out, a0, a1, y0, y1, color):
    if axis == "x":
        pts = [(fixed, y0, a0), (fixed, y0, a1), (fixed, y1, a1), (fixed, y1, a0)]
        p.plane(pts, [], (out, 0, 0), color)
    else:
        pts = [(a0, y0, fixed), (a1, y0, fixed), (a1, y1, fixed), (a0, y1, fixed)]
        p.plane(pts, [], (0, 0, out), color)


def beam(p, a, b, w, d, color, up=(0, 1, 0)):
    """Брус между точками a и b (оси этажа), сечение w × d; d — вдоль up, перпендикулярно брусу."""
    a, b = Vector(a), Vector(b)
    n = (b - a).normalized()
    u = Vector(up).cross(n)
    if u.length < 1e-4:
        u = Vector((1, 0, 0)).cross(n)
    u.normalize()
    v = n.cross(u).normalized()

    def ring(c):
        return [tuple(c + u * su * w / 2 + v * sv * d / 2) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]

    p.loft(ring(a), ring(b), color)


def rng(*k):
    h = 2166136261
    for v in k:
        h = ((h ^ (int(v * 1000) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (h % 10007) / 10007.0


def anchor(p, lo, hi):
    """Габариты детали — ровно этот брус, центр целый: рисунок материала совпадает с сеткой блоков."""
    layer = p.bm.loops.layers.float_color["tone"]
    for (x, y, z), d in ((lo, 0.01), (hi, -0.01)):
        f = p.bm.faces.new([p.bm.verts.new(K.P(*q)) for q in ((x, y, z), (x + d, y, z), (x, y + d, z))])
        for loop in f.loops:
            loop[layer] = (*K.rgb(HULL2), 1.0)


def oct_xy(cx, cy, hw, hh, cut):
    return K.octa(cx, cy, hw, hh, cut)


def plates(R, axis, fixed, out, half, rows, tones, seed, skip=None, width=4.0, depth=0.88, gap=0.12, margin=2.8):
    """Обшивка панелями: столбцы шириной width между угловыми колоннами, ряды rows [(y0, y1)], зазор gap — шов панели."""
    n = max(1, int((2 * half - 2 * margin) // width))
    a_lo = -half + margin
    step = (2 * half - 2 * margin) / n
    for i in range(n):
        a0, a1 = a_lo + i * step, a_lo + (i + 1) * step
        for j, (y0, y1) in enumerate(rows):
            if skip and skip(a0, a1, y0, y1):
                continue
            color = tones[int(rng(seed, i, j) * len(tones)) % len(tones)]
            slab(R, axis, fixed, out, depth, a0 + gap / 2, a1 - gap / 2, y0 + gap / 2, y1 - gap / 2, color)


def chamfer(p, axis, fixed, out, a0, a1, prof, color):
    """Скошенная полоса вдоль стены: prof — профиль [(глубина, y)] (наружу от стены), вытянут вдоль стены от a0 до a1."""
    if axis == "z":
        pts = [(fixed + out * d, y) for d, y in prof]
        p.prism_zy(pts, a0, a1, color)
    else:
        pts = [(fixed + out * d, y) for d, y in prof]
        p.prism_xy(pts, a0, a1, color)


# ══ ФАСАД: корпус исследовательского корабля ═══════════════════════════════════════════════════════════════════

FACES = (("z", -FZ, -1, FX), ("z", FZ, 1, FX), ("x", -FX, -1, FZ), ("x", FX, 1, FZ))
for axis, fixed, out, half in FACES:
    quad(FR, axis, fixed, out, -half, half, YB, YT, HULL2)


def inside(a0, a1, y0, y1, rects):
    """Ячейка целиком под одной из крупных деталей (x0, x1, y0, y1) — её не видно, не строим."""
    return any(a0 >= r[0] and a1 <= r[1] and y0 >= r[2] and y1 <= r[3] for r in rects)


FRONT_COVER = ((-7.2, 7.2, 2.8, 14.0), (-13.0, -10.2, 6.6, 12.2), (10.2, 13.0, 6.6, 12.2))
SIDE_COVER = ((-13.6, -1.0, 7.0, 13.6), (1.0, 13.6, 7.0, 13.6))
BACK_COVER = ()
SKIPS = tuple(lambda a0, a1, y0, y1, r=r: inside(a0, a1, y0, y1, r) for r in (FRONT_COVER, BACK_COVER, SIDE_COVER,
                                                                               SIDE_COVER))
ROWS = ((2.8, 5.6), (5.6, 8.4), (8.4, 11.2), (11.2, 14.0))
for idx, (axis, fixed, out, half) in enumerate(FACES):
    # цоколь с решётками, белая кромка
    slab(FR, axis, fixed, out, 1.88, -half, half, YB, 2.4, HULL)
    for k in range(int(2 * half // 6)):
        a = -half + 4.5 + 6 * k
        if a > half - 4:
            break
        for y in (0.2, 0.8, 1.4):
            slab(FS, axis, fixed, out, 1.98, a - 1.4, a + 1.4, y, y + 0.28, NAVY)
    slab(FS, axis, fixed, out, 2.1, -half, half, 2.4, 2.8, WHITE)
    plates(FR, axis, fixed, out, half, ROWS, (PLATE, PLATE2, PLATE3, PLATE2), seed=7 + idx, skip=SKIPS[idx],
           width=3.0)
    # карниз: белая кромка, световая линия, скос
    slab(FS, axis, fixed, out, 1.4, -half, half, 14.0, 14.5, WHITE)
    slab(FG, axis, fixed, out, 1.46, -half, half, 14.5, 14.72, CYAN, back=-1.0)
    chamfer(FR, axis, fixed, out, -half, half, [(0.0, 14.72), (2.2, 14.72), (2.2, 16.3), (1.1, 19.0), (0.0, 19.0)], HULL)
    k = -half + 3.0
    while k < half - 2.5:
        chamfer(FS, axis, fixed, out, k - 0.2, k + 0.2, [(0.0, 14.72), (2.34, 14.72), (2.34, 16.3), (1.24, 18.85),
                                                          (0.0, 18.85)], HULL2)
        k += 3.0

# угловые колонны: белые восьмигранники с оранжевым поясом, навигационные огни
for sx in (-1, 1):
    for sz in (-1, 1):
        cx, cz = sx * FX, sz * FZ
        for y0, y1, r, color in ((YB, 2.8, 2.5, WHITE2), (2.8, 12.2, 2.6, WHITE), (12.2, 13.1, 2.78, ORANGE),
                                 (13.1, 17.6, 2.6, WHITE), (17.6, YT, 2.35, HULL2), (6.2, 6.6, 2.7, HULL2)):
            dst = FR if r == 2.6 else FS
            dst.prism_xz(K.octa(cx, cz, r, r, r * 0.4), y0, y1, color)
        dx, dz = sx * 1.9, sz * 1.9  # огонь на внешней диагонали
        FG.box(cx + dx - 0.35, cx + dx + 0.35, 17.9, 18.6, cz + dz - 0.35, cz + dz + 0.35, RED if sx < 0 else GREEN)

# ── перед: золотой визор в белой раме, фонари шлема, шейное кольцо, антенна ──
VY = 9.4
FR.frame_xy(oct_xy(0, VY, 9.4, 6.6, 2.8), oct_xy(0, VY, 7.8, 5.0, 2.2), -FZ + 0.05, -FZ - 2.88, WHITE)
FS.frame_xy(oct_xy(0, VY, 7.8, 5.0, 2.2), oct_xy(0, VY, 7.35, 4.55, 2.0), -FZ + 0.05, -FZ - 2.62, ORANGE)
FS.prism_xy(oct_xy(0, VY, 7.4, 4.6, 2.0), -FZ + 0.05, -FZ - 1.5, GOLD2)
FS.prism_xy(oct_xy(0, VY + 0.1, 6.4, 3.8, 1.7), -FZ - 1.4, -FZ - 2.0, GOLD)
FS.prism_xy(oct_xy(0, VY + 0.25, 4.8, 2.6, 1.2), -FZ - 1.9, -FZ - 2.35, GOLD_HI)
for pts in ([(-4.2, 11.6), (-3.2, 11.6), (-4.9, 8.2), (-5.9, 8.2)], [(-2.6, 11.6), (-2.1, 11.6), (-3.8, 8.2), (-4.3, 8.2)]):
    FG.prism_xy(pts, -FZ - 2.3, -FZ - 2.45, GLINT)  # блики на визоре
for k in range(8):  # болты рамы
    ang = 2 * math.pi * (k + 0.5) / 8
    x, y = 8.6 * math.cos(ang), VY + 5.8 * math.sin(ang)
    FS.box(x - 0.3, x + 0.3, y - 0.3, y + 0.3, -FZ - 2.8, -FZ - 3.05, METAL)
for s in (-1, 1):  # фонари шлема по бокам визора
    x = s * 11.6
    slab(FR, "z", -FZ, -1, 2.88, x - 1.4, x + 1.4, 6.6, 12.2, WHITE)
    slab(FS, "z", -FZ, -1, 3.0, x - 1.0, x + 1.0, 6.2, 6.6, ORANGE)
    FG.box(x - 0.85, x + 0.85, 8.2, 10.6, -FZ - 2.8, -FZ - 3.05, ICE)
    slab(FS, "z", -FZ, -1, 3.0, x - 1.1, x + 1.1, 11.2, 11.6, HULL2)
slab(FS, "z", -FZ, -1, 2.4, -7.6, 7.6, 1.9, 2.8, BLUE)  # шейное кольцо
for k in range(7):
    x = -6.0 + 2.0 * k
    FS.box(x - 0.25, x + 0.25, 2.1, 2.6, -FZ - 2.4, -FZ - 2.55, WHITE)
beam(FS, (12.6, 14.6, -FZ - 1.7), (12.6, 18.4, -FZ - 1.7), 0.28, 0.28, METAL)  # антенна
FG.box(12.35, 12.85, 18.35, 18.85, -FZ - 1.95, -FZ - 1.45, RED)
beam(FS, (11.8, 16.6, -FZ - 1.7), (13.4, 16.6, -FZ - 1.7), 0.2, 0.2, METAL)

# ── бока: солнечные батареи и двигательные гондолы ──
for s in (-1, 1):
    fx = s * FX
    for z0, z1 in ((-13.6, -1.0), (1.0, 13.6)):
        FS.frame_zy([(z0, 7.0), (z1, 7.0), (z1, 13.6), (z0, 13.6)], [(z0 + 0.4, 7.4), (z1 - 0.4, 7.4), (z1 - 0.4, 13.2),
                    (z0 + 0.4, 13.2)], fx, fx + s * 1.3, GOLD)
        slab(FS, "x", fx, s, 1.0, z0 + 0.4, z1 - 0.4, 7.4, 13.2, SOLAR)
        k = z0 + 0.4 + 1.9
        while k < z1 - 0.6:
            slab(FS, "x", fx, s, 1.1, k - 0.08, k + 0.08, 7.4, 13.2, GOLD2)
            k += 1.9
        slab(FS, "x", fx, s, 1.1, z0 + 0.4, z1 - 0.4, 10.22, 10.38, GOLD2)
    cx, cy, r = s * (FX + 1.7), 4.5, 1.55
    FS.prism_xy(K.octa(cx, cy, r, r, r * 0.4), -11.0, 7.0, WHITE2)
    for z in (-6.0, 2.0):
        FS.prism_xy(K.octa(cx, cy, r + 0.12, r + 0.12, (r + 0.12) * 0.4), z, z + 0.6, ORANGE)
    nose = [(x, y, -11.0) for x, y in K.octa(cx, cy, r, r, r * 0.4)]
    tip = [(x, y, -12.8) for x, y in K.octa(cx, cy, 0.5, 0.5, 0.2)]
    FS.loft(nose, tip, WHITE)
    FS.loft([(x, y, 7.0) for x, y in K.octa(cx, cy, 1.15, 1.15, 0.46)],
            [(x, y, 8.8) for x, y in K.octa(cx, cy, 1.6, 1.6, 0.64)], HULL2)
    FG.prism_xy(K.octa(cx, cy, 1.2, 1.2, 0.48), 8.6, 8.75, ICE)
    for z in (-7.5, 3.5):
        slab(FS, "x", fx, s, 1.75, z - 0.5, z + 0.5, 4.0, 5.0, METAL)

objects(True)
# радарная тарелка на левом боку — между батареями
fx = -FX
FS.box(fx - 0.9, fx + 0.05, 9.6, 11.0, -0.5, 0.5, METAL)
FS.loft([(fx - 1.0, y, z) for z, y in K.octa(0.0, 10.3, 0.5, 0.5, 0.2)],
        [(fx - 2.3, y, z) for z, y in K.octa(0.0, 10.3, 2.3, 2.3, 0.92)], WHITE)
beam(FS, (fx - 2.2, 10.3, 0.0), (fx - 3.4, 10.3, 0.0), 0.2, 0.2, METAL)
FG.box(fx - 3.6, fx - 3.3, 10.15, 10.45, -0.15, 0.15, ORANGE)

objects(False)
# ── тыл: три сопла с голубым свечением, теплозащита ──
for x in (-9.0, 0.0, 9.0):
    cy = 9.0
    FS.prism_xy(K.octa(x, cy, 2.3, 2.3, 0.92), FZ - 0.05, FZ + 0.9, WHITE)
    FS.loft([(px, py, FZ + 0.9) for px, py in K.octa(x, cy, 1.8, 1.8, 0.72)],
            [(px, py, FZ + 3.4) for px, py in K.octa(x, cy, 2.7, 2.7, 1.08)], HULL2)
    FG.prism_xy(K.octa(x, cy, 2.25, 2.25, 0.9), FZ + 3.3, FZ + 3.42, "1F4FA8")
    FG.prism_xy(K.octa(x, cy, 1.25, 1.25, 0.5), FZ + 3.38, FZ + 3.5, "8FD0FF")
    FS.prism_xy(K.octa(x, cy, 2.75, 2.75, 1.1), FZ + 2.6, FZ + 3.0, ORANGE)
slab(FR, "z", FZ, 1, 1.88, -13.0, 13.0, 3.0, 5.4, HULL)
for k in range(9):
    x = -12.0 + 3.0 * k
    FS.prism_xy([(x - 0.9, 3.4), (x - 0.2, 3.4), (x + 0.9, 5.0), (x + 0.2, 5.0)], FZ + 1.85, FZ + 2.0, ORANGE)
anchor(FR, (-21, -1, -20), (21, 19, 20))
anchor(FQ, (-21, -1, -20), (21, 19, 20))
anchor(FP, (-21, -1, -20), (21, 19, 20))

# ══ ИНТЕРЬЕР: исследовательский отсек ══════════════════════════════════════════════════════════════════════════

DOOR = (3.5, 10.5)
DAIS = (0.0, -4.0)  # центр подиума
WIN = (0.0, 9.2, 11.0, 7.0, 3.0)  # окно в космос: центр x, y, полуширина, полувысота, срез
PORTS = (12.0, 3.0, -7.5)  # иллюминаторы по бокам (z)
CONSOLES = (3.0, -7.5)  # пульты под иллюминаторами (z)
FRAMES = (8.5, -1.5)  # силовые шпангоуты (z)

IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), DECK)
IR.plane([(-W, C, ZF), (W, C, ZF), (W, C, ZB), (-W, C, ZB)], [], (0, -1, 0), HULL_I)
for s in (-1, 1):
    IR.plane([(s * W, 0, ZF), (s * W, 0, ZB), (s * W, C, ZB), (s * W, C, ZF)], [], (-s, 0, 0), HULL2_I)
IR.plane([(-W, 0, ZF), (W, 0, ZF), (W, C, ZF), (-W, C, ZF)], [], (0, 0, 1), HULL2_I)
IR.plane([(x, y, ZB) for x, y in [(-W, 0), (-DOOR[0], 0), (-DOOR[0], DOOR[1]), (DOOR[0], DOOR[1]), (DOOR[0], 0),
                                   (W, 0), (W, C), (-W, C)]], [], (0, 0, -1), HULL2_I)

# палуба: плиты через одну приподняты, вокруг подиума — жёлтая полоса, к подиуму — световые дорожки
for i in range(-4, 4):
    for j in range(-4, 4):
        if (i + j) % 2:
            continue
        x0, z0 = i * 4 + 0.1, j * 4 + 0.1
        if abs(x0 + 2 - DAIS[0]) < 7 and abs(z0 + 2 - DAIS[1]) < 7:
            continue
        IQ.box(x0, x0 + 3.8, 0.02, 0.1, max(z0, ZF), min(z0 + 3.8, ZB), DECK2)
IS.frame_xz(K.octa(DAIS[0], DAIS[1], 7.6, 7.6, 2.9), K.octa(DAIS[0], DAIS[1], 7.15, 7.15, 2.75), 0.02, 0.09, YELLOW)
for x in (-2.3, 2.3):
    IG.box(x - 0.08, x + 0.08, 0.02, 0.07, 3.8, 13.6, CYAN)


def skip_wall(axis, a0, a1, y0, y1, s=0):
    if axis == "x":
        for z in PORTS:
            if a1 > z - 2.2 and a0 < z + 2.2 and y1 > 6.3 and y0 < 10.7:
                return True
        return False
    if axis == "zf":
        return a1 > WIN[0] - WIN[2] - 0.1 and a0 < WIN[0] + WIN[2] + 0.1 and y1 > WIN[1] - WIN[3] and y0 < WIN[1] + WIN[3]
    return a1 > -DOOR[0] - 1.6 and a0 < DOOR[0] + 1.6 and y0 < DOOR[1] + 1.8


IN_ROWS = ((1.2, 5.0), (5.0, 8.8), (8.8, 12.4))
WALLS = (("x", -W, 1, ZB, "x"), ("x", W, -1, ZB, "x"), ("z", ZF, 1, W, "zf"), ("z", ZB, -1, W, "zb"))
for idx, (axis, fixed, out, half, kind) in enumerate(WALLS):
    if kind != "zb":
        slab(IR, axis, fixed, out, 1.88, -half, half, 0.0, 1.2, HULL2_I)
    plates(IR, axis, fixed, out, half, IN_ROWS, (PLATE_I, PLATE2_I, PLATE_I, PANEL_I), seed=30 + idx,
           skip=lambda a0, a1, y0, y1, k=kind: skip_wall(k, a0, a1, y0, y1), margin=0.0)
    slab(IR, axis, fixed, out, 0.88, -half, half, 12.4, 13.6, PLATE2_I)
    slab(IG, axis, fixed, out, 1.3, -half, half, 13.6, 13.85, LIGHT, back=-0.6)
    chamfer(IR, axis, fixed, out, -half, half, [(0.0, 13.85), (1.2, 13.85), (3.6, C), (0.0, C)], PLATE2_I)
# цоколь задней стены — по бокам от шлюза
for a0, a1 in ((-W, -DOOR[0] - 1.6), (DOOR[0] + 1.6, W)):
    slab(IR, "z", ZB, -1, 1.88, a0, a1, 0.0, 1.2, HULL2_I)
# скошенные углы зала
for sx in (-1, 1):
    for sz in (-1, 1):
        x, z = sx * W, sz * (ZB if sz > 0 else -ZF)
        IR.prism_xz([(x, z), (x - sx * 3.0, z), (x, z - sz * 3.0)], 0.0, C, PLATE_I)

# иллюминаторы и пульты по бокам
for s in (-1, 1):
    x0 = s * W
    for z in PORTS:
        IR.frame_zy(K.octa(z, 8.5, 2.1, 2.1, 0.85), K.octa(z, 8.5, 1.5, 1.5, 0.6), x0, x0 - s * 1.3, WHITE_I)
        IS.frame_zy(K.octa(z, 8.5, 1.55, 1.55, 0.62), K.octa(z, 8.5, 1.35, 1.35, 0.55), x0, x0 - s * 1.42, ORANGE)
        quad(IG, "x", x0 - s * 0.06, -s, z - 1.6, z + 1.6, 6.9, 10.1, SPACE)
        for k in range(4):
            dz, dy = (rng(s, z, k) - 0.5) * 2.0, (rng(z, k, s) - 0.5) * 2.0
            quad(IG, "x", x0 - s * 0.1, -s, z + dz - 0.08, z + dz + 0.08, 8.5 + dy - 0.08, 8.5 + dy + 0.08, "FFFFFF")
    for z in CONSOLES:
        IR.box(x0 - s * 2.4, x0, 0.0, 2.4, z - 2.0, z + 2.0, PANEL_I)
        IS.prism_xy([(x0 - s * 2.4, 2.4), (x0, 2.4), (x0, 3.3), (x0 - s * 1.3, 3.3)], z - 2.0, z + 2.0, PLATE_I)
        IS.box(x0 - s * 2.45, x0 - s * 2.35, 1.0, 1.3, z - 1.9, z + 1.9, CYAN)
        for k, color in enumerate((ORANGE, CYAN, GREEN, CYAN)):  # кнопки на скосе
            zz = z - 1.4 + 0.9 * k
            IG.box(x0 - s * 1.9, x0 - s * 1.5, 2.5, 2.62, zz - 0.2, zz + 0.2, color)
        slab(IS, "x", x0, -s, 0.5, z - 1.8, z + 1.8, 3.3, 5.9, HULL2_I)  # экран над пультом
        quad(IG, "x", x0 - s * 0.56, -s, z - 1.5, z + 1.5, 3.6, 5.6, SCREEN)
        for k in range(3):
            quad(IG, "x", x0 - s * 0.6, -s, z - 1.2, z - 1.2 + 0.6 + 0.5 * k, 4.0 + 0.5 * k, 4.25 + 0.5 * k, SCREEN2)
    # стойки оборудования у передних углов, трубы вдоль стен
    IR.box(x0 - s * 2.2, x0, 0.0, 9.0, -13.0, -10.0, HULL2_I)
    for k in range(6):
        IG.box(x0 - s * 2.25, x0 - s * 2.18, 1.5 + 1.1 * k, 1.8 + 1.1 * k, -12.4, -11.9, GREEN if k % 3 else CYAN)
        IG.box(x0 - s * 2.25, x0 - s * 2.18, 1.5 + 1.1 * k, 1.8 + 1.1 * k, -11.2, -10.7, ORANGE if k % 2 else CYAN)
    for y, color in ((12.0, METAL), (12.55, ORANGE)):
        beam(IS, (x0 - s * 0.55, y, -13.0), (x0 - s * 0.55, y, 13.0), 0.38, 0.38, color)

# окно в космос: рама, звёзды, планета с атмосферой, луна
cx, cy, hw, hh, cut = WIN
IR.frame_xy(K.octa(cx, cy, hw, hh, cut), K.octa(cx, cy, hw - 1.4, hh - 1.2, cut - 0.5), ZF - 0.05, ZF + 1.9, WHITE_I)
IS.frame_xy(K.octa(cx, cy, hw - 1.4, hh - 1.2, cut - 0.5), K.octa(cx, cy, hw - 1.8, hh - 1.6, cut - 0.65), ZF - 0.05,
            ZF + 2.05, ORANGE)
IG.prism_xy(K.octa(cx, cy, hw - 1.4, hh - 1.2, cut - 0.5), ZF + 0.05, ZF + 0.12, SPACE)
for k in range(46):
    x = cx + (rng(k, 1) - 0.5) * 2 * (hw - 2.6)
    y = cy + (rng(k, 2) - 0.5) * 2 * (hh - 2.2)
    r = 0.07 + 0.11 * rng(k, 3)
    IG.prism_xy([(x - r, y), (x, y - r), (x + r, y), (x, y + r)], ZF + 0.12, ZF + 0.16, "FFFFFF" if k % 3 else "B8D4FF")
PX, PY, PR = 5.2, 7.4, 3.9
IG.prism_xy(K.ngon(PX, PY, PR + 0.35, 16), ZF + 0.16, ZF + 0.2, ATMO)
IG.prism_xy(K.ngon(PX, PY, PR, 16), ZF + 0.2, ZF + 0.26, PLANET)
for dy, w in ((1.4, 0.35), (-0.6, 0.5), (-2.2, 0.3)):
    half = math.sqrt(max(PR * PR - dy * dy, 0.0)) - 0.25
    IG.prism_xy([(PX - half, PY + dy - w / 2), (PX + half, PY + dy - w / 2), (PX + half - 0.4, PY + dy + w / 2),
                 (PX - half + 0.4, PY + dy + w / 2)], ZF + 0.26, ZF + 0.3, PLANET2)
IG.prism_xy(K.ngon(-6.4, 12.6, 1.0, 12), ZF + 0.16, ZF + 0.22, MOON)

# силовые шпангоуты: стойка, скос, перекладина (угловые рамы), светлая полоса по низу перекладины
for z in FRAMES:
    for s in (-1, 1):
        beam(IR, (s * 15.6, 0.0, z), (s * 15.6, 12.6, z), 1.3, 1.4, PANEL_I, up=(0, 0, 1))
        beam(IR, (s * 15.6, 12.0, z), (s * 11.4, 16.9, z), 1.3, 1.4, PANEL_I, up=(0, 0, 1))
        IS.box(s * 15.0, s * 16.4, 0.0, 0.8, z - 0.85, z + 0.85, HULL2_I)
    IR.box(-11.6, 11.6, 16.25, 17.55, z - 0.7, z + 0.7, PANEL_I)
    IG.box(-10.4, 10.4, 16.15, 16.25, z - 0.3, z + 0.3, LIGHT)

# потолок: световой короб по оси, поперечины
IG.box(-2.4, 2.4, C - 0.06, C - 0.02, -12.0, 13.0, LIGHT)
for k in range(9):
    z = -12.0 + 25.0 * k / 8
    IS.box(-2.7, 2.7, C - 0.4, C - 0.01, z - 0.18, z + 0.18, HULL2_I)
IS.box(-2.7, -2.4, C - 0.4, C - 0.01, -12.0, 13.0, HULL2_I)
IS.box(2.4, 2.7, C - 0.4, C - 0.01, -12.0, 13.0, HULL2_I)

# шлюз лифта: рама, полосы «опасность», створки
for s in (-1, 1):
    IR.box(s * (DOOR[0] + 0.1), s * (DOOR[0] + 1.5), 0.0, DOOR[1] + 1.7, ZB + 0.05, ZB - 1.4, WHITE_I)
    for k in range(4):
        IS.box(s * (DOOR[0] + 0.2), s * (DOOR[0] + 1.4), 0.2 + 0.8 * k, 0.6 + 0.8 * k, ZB - 1.4, ZB - 1.52,
               YELLOW if k % 2 == 0 else HULL2_I)
    IS.box(s * 0.06, s * DOOR[0], 0, DOOR[1], 16.15, 16.45, WHITE2)
    IS.box(s * 0.4, s * (DOOR[0] - 0.3), 5.0, 5.6, 16.0, 16.17, ORANGE)
    IS.box(s * 0.5, s * 0.75, 1.0, 9.6, 16.0, 16.17, HULL2_I)  # продольный шов створки (окошки читались «глазами»)
IR.box(-DOOR[0] - 1.5, DOOR[0] + 1.5, DOOR[1] + 0.2, DOOR[1] + 1.7, ZB + 0.05, ZB - 1.6, WHITE_I)
for s in (-1, 1):  # приборные щиты по бокам шлюза: экран, индикаторы, знак «опасность»
    x = s * 9.5
    IS.box(x - 2.0, x + 2.0, 3.4, 8.6, ZB + 0.05, ZB - 1.05, PANEL_I)
    quad(IG, "z", ZB - 1.1, -1, x - 1.5, x + 1.5, 5.6, 8.0, SCREEN)
    for k in range(4):
        IG.box(x - 1.5 + 0.8 * k, x - 1.1 + 0.8 * k, 4.2, 4.6, ZB - 1.05, ZB - 1.15, (GREEN, CYAN, ORANGE, CYAN)[k])
    IS.prism_xy([(x - 0.7, 9.2), (x + 0.7, 9.2), (x, 10.4)], ZB - 0.95, ZB - 1.1, YELLOW)
IG.box(-1.6, 1.6, DOOR[1] + 0.6, DOOR[1] + 1.3, ZB - 1.62, ZB - 1.7, ORANGE)

objects(True)
# ── экспозиция шлема: ступенчатый восьмигранный подиум, кольца света, пилоны-излучатели, парящее кольцо ──
dx, dz = DAIS
IR.prism_xz(K.octa(dx, dz, 6.4, 6.4, 2.5), 0.0, 0.8, PLATE_I)
IS.prism_xz(K.octa(dx, dz, 6.5, 6.5, 2.55), 0.8, 0.95, ORANGE)
IR.prism_xz(K.octa(dx, dz, 4.8, 4.8, 1.9), 0.95, 1.9, WHITE_I)
IG.frame_xz(K.octa(dx, dz, 5.15, 5.15, 2.05), K.octa(dx, dz, 4.8, 4.8, 1.9), 0.95, 1.12, CYAN)
IS.prism_xz(K.octa(dx, dz, 3.3, 3.3, 1.3), 1.9, 2.15, NAVY)
IG.frame_xz(K.octa(dx, dz, 3.6, 3.6, 1.42), K.octa(dx, dz, 3.3, 3.3, 1.3), 1.9, 2.2, CYAN)
HELMET = (dx, 6.6, dz)
PYLONS = (0.0, 180.0, 240.0, 300.0)  # углы пилонов: по бокам и сзади (у лифта — +z, туда пилоны не ставим)
for deg in PYLONS:
    ang = math.radians(deg)
    ca, sa = math.cos(ang), math.sin(ang)
    base = (dx + 5.9 * ca, 0.8, dz + 5.9 * sa)
    top = (dx + 3.9 * ca, 10.4, dz + 3.9 * sa)
    beam(IR, base, top, 1.0, 1.0, WHITE_I)
    beam(IS, (dx + 4.3 * ca, 8.4, dz + 4.3 * sa), (dx + 4.1 * ca, 9.4, dz + 4.1 * sa), 1.15, 1.15, ORANGE)
    IG.box(top[0] - 0.35, top[0] + 0.35, 10.3, 10.95, top[2] - 0.35, top[2] + 0.35, CYAN)
    IS.box(base[0] - 0.9, base[0] + 0.9, 0.8, 1.2, base[2] - 0.9, base[2] + 0.9, HULL2_I)
IS.frame_xz(K.octa(dx, dz, 4.7, 4.7, 1.85), K.octa(dx, dz, 3.95, 3.95, 1.55), 13.5, 14.05, WHITE_I)
IG.frame_xz(K.octa(dx, dz, 4.55, 4.55, 1.8), K.octa(dx, dz, 4.1, 4.1, 1.6), 13.4, 13.5, CYAN)
for deg in PYLONS:
    ang = math.radians(deg)
    x, z = dx + 4.3 * math.cos(ang), dz + 4.3 * math.sin(ang)
    IS.box(x - 0.07, x + 0.07, 14.05, C - 0.02, z - 0.07, z + 0.07, METAL)
objects(False)
anchor(IR, (-17, 0, -16), (17, 18, 16))
anchor(IQ, (-17, 0, -16), (17, 18, 16))
anchor(IP, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════

SL.box(-FX, FX, YB, YT, -FZ, FZ, PLATE2)
SL.box(-FX - 1.9, FX + 1.9, -1, 2.8, -FZ - 1.9, FZ + 1.9, HULL)
SL.box(-FX - 1.5, FX + 1.5, 14.0, 14.7, -FZ - 1.5, FZ + 1.5, CYAN)
SL.box(-FX - 2.2, FX + 2.2, 14.7, 17.0, -FZ - 2.2, FZ + 2.2, HULL)
for sx in (-1, 1):
    for sz in (-1, 1):
        SL.box(sx * FX - 2.5, sx * FX + 2.5, -1, 19, sz * FZ - 2.5, sz * FZ + 2.5, WHITE)
SL.box(-9.4, 9.4, 2.8, 16.0, -FZ - 2.88, -FZ, WHITE)  # рама визора
SL.box(-7.4, 7.4, 4.8, 14.0, -FZ - 3.1, -FZ - 2.88, GOLD)  # визор
for s in (-1, 1):
    SL.box(s * 10.2, s * 13.0, 6.6, 12.2, -FZ - 2.88, -FZ, WHITE)  # фонари
    SL.box(s * FX, s * (FX + 1.3), 7.0, 13.6, -13.6, 13.6, SOLAR)  # батареи
    SL.box(s * FX, s * (FX + 3.25), 2.95, 6.05, -12.8, 8.8, WHITE2)  # гондола
for x in (-9.0, 0.0, 9.0):
    SL.box(x - 2.7, x + 2.7, 6.3, 11.7, FZ, FZ + 3.45, HULL2)  # сопла
    SL.box(x - 2.2, x + 2.2, 6.8, 11.2, FZ + 3.45, FZ + 3.6, "1F4FA8")

# ══ СБОРКА, ЗАТЕНЕНИЕ ═════════════════════════════════════════════════════════════════════════════════════════

collection = bpy.data.collections.new("SpaceHelmetFloor")
bpy.context.scene.collection.children.link(collection)


def proxy(name, y0, y1):
    me = bpy.data.meshes.new(name)
    pts = [K.P(sx * HX, y, sz * HZ) for y in (y0, y1) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
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

TOL = float(next((f[4:] for f in FLAGS if f.startswith("tol=")), 0.11))
ML = int(next((f[3:] for f in FLAGS if f.startswith("ml=")), 3))
MLF = int(next((f[4:] for f in FLAGS if f.startswith("mlf=")), 2))
FORM_IN = {"up": 1.0, "pz": 0.96, "px": 0.88, "nx": 0.88, "nz": 0.84, "down": 0.74, "edge": 1.14}
FORM_OUT = {"up": 1.0, "pz": 0.95, "px": 0.86, "nx": 0.86, "nz": 0.97, "down": 0.70, "edge": 1.12}
print("QUIET facade", FR.give_tones(FQ, QUIET), "interior", IR.give_tones(IQ, QUIET), flush=True)
if "nocoplanar" not in FLAGS:  # мерцание совпадающих граней — меньшая выдвигается
    print("COPLANAR", K.resolve_coplanar([p for p in parts if p.tier != "silhouette"]), flush=True)
print("LINES facade", K.adaptive_cut(facade, [above, below], radius=5.0, tol=TOL, fine=1.0, min_size=2.0,
                                     max_lines=MLF), flush=True)
print("LINES interior", K.adaptive_cut(interior, radius=3.5, tol=TOL, fine=1.2, min_size=2.4, max_lines=ML), flush=True)
for p in sorted(parts, key=lambda q: q.partner is None):
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
    path = os.path.join(REPO, "assets", "models", "floors", "SpaceHelmetFloor.fbx")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    K.export_fbx([p.obj for p in parts], path)
    K.write_json(os.path.splitext(path)[0] + ".json", info)
    print("EXPORTED", path, flush=True)

# ══ ПРОВЕРОЧНЫЕ РЕНДЕРЫ ═══════════════════════════════════════════════════════════════════════════════════════

EXHIBIT = (DAIS[0], 2.2, DAIS[1], 2.8)  # место и масштаб показа шлема (как в Floors/SpaceHelmet)

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
    next(n for n in grey.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.8, 0.8, 0.82, 1)
    above.data.materials.append(grey)
    below.data.materials.append(grey)
    for name, at, energy, color in (("Hall", (0, 15.0, 5.0), 5000, (0.86, 0.9, 1.0)),
                                    ("Spot", (0, 13.0, -4.0), 2500, (1.0, 1.0, 1.0))):
        lamp = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT"))
        lamp.data.energy, lamp.data.color, lamp.data.shadow_soft_size = energy, color, 2.0
        lamp.data.use_shadow = False
        lamp.location = K.P(*at)
        scene.collection.objects.link(lamp)
    item_path = os.path.join(REPO, "assets", "models", "art", "SpaceHelmet.fbx")
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.fbx(filepath=item_path)
    except Exception as err:  # noqa: BLE001
        print("ITEM_IMPORT_FAILED", err)
    item = [o for o in bpy.data.objects if o not in before]
    if item:
        img = bpy.data.images.load(os.path.join(REPO, "assets", "textures", "art", "SpaceHelmet_color.png"))
        mat = bpy.data.materials.new("Item")
        mat.use_nodes = True
        tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = img
        bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        root = bpy.data.objects.new("ItemRoot", None)
        scene.collection.objects.link(root)
        for o in item:
            if o.type == "MESH":
                o.data.materials.clear()
                o.data.materials.append(mat)
            if o.parent is None:
                o.parent = root
        root.scale = (EXHIBIT[3],) * 3
        root.rotation_euler = (0, 0, math.pi)
        root.location = K.P(EXHIBIT[0], EXHIBIT[1] + 0.07, EXHIBIT[2])
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

    inside = ("SH_S_",)
    outside = ("SH_S_", "Item", "Hall", "Spot")
    only = [f for f in FLAGS if f.startswith("shot=")]
    shots = {
        "f1_front": lambda: shot("f1_front", (0, 9, -84), (0, 9, -17), 32, hide=outside),
        "f2_side": lambda: shot("f2_side", (84, 10, -4), (18, 9, -4), 32, hide=outside),
        "f3_three_quarter": lambda: shot("f3_three_quarter", (-50, 16, -60), (0, 8.5, -12), 36, hide=outside),
        "f5_back": lambda: shot("f5_back", (32, 14, 74), (0, 9, 17), 32, hide=outside),
        "i1_lift": lambda: shot("i1_lift", (0, 5.5, 14.6), (0, 7.0, -8), 70, hide=inside),
        "i2_helmet": lambda: shot("i2_helmet", (6.5, 7.0, 4.5), (0, 6.5, -5.0), 55, hide=inside),
        "i3_side": lambda: shot("i3_side", (-12, 6.5, 10), (2.0, 6.0, -10), 70, hide=inside),
        "i4_back": lambda: shot("i4_back", (0, 6.5, 3.0), (0, 6.0, 16), 70, hide=inside),
        "s1_silhouette": lambda: shot("s1_silhouette", (-50, 16, -60), (0, 8.5, -12), 36,
                                      hide=("SH_F_", "SH_I_", "Item", "Hall", "Spot")),
    }
    for key, run in shots.items():
        if not only or ("shot=" + key) in only:
            run()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "SpaceHelmetFloor.blend"))
print("DONE", flush=True)
