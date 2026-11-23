"""Этаж «Скелет тираннозавра» музея-небоскрёба — доисторическая экспозиция из мешей по эталону GoldenThrone v6
(утверждён владельцем 2026-11-21): крупные блоки по сетке в один стад, на гранях — крупные квадраты по одному на стад
(MaterialVariant LegoSquaresFar / LegoSquaresQuiet), фаска рёбер, тени и яркость сторон — в цветах вершин.

Замысел (просьба владельца 2026-11-21: «впечатляющий доисторический мир, этаж — достопримечательность, а не комната
со скелетом; скелет — главный экспонат; фасад узнаётся издалека»):
  Снаружи — обрыв из слоёв породы (базальт, сланец, ржавый железняк, песчаник, охра) с неровными ступенчатыми
  границами и уступами, сверху — пояс папоротников с лианами. Спереди из скалы выступает огромный череп тираннозавра в
  профиле: ступенчатый рельеф кости, открытая пасть с зубами, глазница со светящимся янтарём, тёмные окна черепа.
  По бокам — позвоночник по верху стен и рёбра, свисающие по обрыву; сзади — хвост; в слоях — янтарь и аммониты.
  Внутри — зал-раскоп: стены из тех же слоёв (темнее, пещера), у лифта — крепь шахты из брёвен, через зал — две арки
  гигантских рёбер и позвоночник по потолку, гирлянды рабочих ламп. Скелет стоит на скальном постаменте в профиль
  к лифту; за ним — диорама: вулкан с лавой на закатном небе (тёмный вулкан — фон для светлых костей). На полу —
  дощатый настил от лифта, следы тираннозавра, сетка раскопа с колышками, вскрытые квадраты с костями, лампы на
  треногах, ящики с находками и инструментом; на уступах у стен — саговники и папоротники.

Детали (MeshPart): Rings — Plastic + LegoSquaresFar (порода, кость), Quiet — LegoSquaresQuiet (песок, земля, зелень),
Smooth — SmoothPlastic (зубы, дерево, верёвки, мелочь), Glass — янтарь, лава, небо диорамы, лампы (светятся сами).
Пишет assets/models/floors/TRexSkeletonFloor.fbx и .json (центры, размеры), рендеры — в папку превью.
Запуск: blender --background --factory-startup --python scripts/blender/floor_trex.py -- <репо> <превью>
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

# ── Палитра: цвета — в вершинах; цвет детали в игре — общий множитель яркости ──────────────────────────────────
WHITE = "FFFFFF"
# порода снаружи (днём на солнце) — тёплая, слои различимы и по тону, и по цвету
BASALT, SLATE, RUST, SANDST, OCHRE = "4E4844", "7C7A78", "A35A2E", "D8BC86", "B9853F"
GRASS, GRASS2, LEAF, LEAF2 = "4E8F34", "3A7029", "5DA83E", "3C8A2E"
# порода внутри (пещера) — темнее: светлым в зале остаётся только скелет
BASALT_I, SLATE_I, RUST_I, SANDST_I, OCHRE_I, CAVE = "3B3633", "5B5855", "7A4426", "9C8660", "86622F", "2C2622"
SAND, DIGSOIL, DUST = "B39468", "7D6446", "A08A66"  # пол раскопа, вскрытые квадраты, верх постамента
BONE, BONE_HI, BONE_OLD = "E7D9B4", "F4EAD0", "B7A47C"  # кость черепа и рёбер снаружи, гребни, кость арок зала
TOOTH, HOLE = "FBF5E6", "241C17"
WOOD, WOOD2, ROPE, IRON = "8A5A32", "5E3B20", "6B4A28", "3A3632"
AMBER, AMBER2 = "FFA51F", "FFCC4A"
# диорама: небо и лава светятся сами (Glass), горы и вулкан — рельефом
SKY_A, SKY_B, SKY_C, SKY_D = "7A2E66", "D24A32", "F38A3A", "FFC968"
LAVA, LAVA2 = "FF5A14", "FFB33A"
VOLC, VOLC2, MOUNT, SMOKE, JUNGLE, JUNGLE2 = "2E2422", "4A3430", "5C3036", "4A3C3C", "2E5A2C", "1B3A1E"
LAMPC = "FFE6A8"
SHADE = (0.52, 0.52, 0.52)

HX, HZ, YB, YT = 18.0, 17.0, -1.0, 19.0
SK = 0.12
FX, FZ = HX + SK, HZ + SK
NARROW = 0.9
W, ZB, C = 16.88, 15.88, 18.0  # стены и потолок изнутри
ZF = -15.88

parts = []


def part(name, tier, material, **kw):
    p = K.Part(name, tier, material, WHITE, SHADE, **kw)
    parts.append(p)
    return p


EDGE = 0.1
FS = part("TR_F_Smooth", "facade", "smooth", adapt=True)
FR = part("TR_F_Rings", "facade", "tile", adapt=True, partner=FS, narrow=NARROW, bevel=EDGE, bevel_min=1.0)
FQ = part("TR_F_Quiet", "facade", "tile", adapt=True, partner=FS, narrow=NARROW)
FG = part("TR_F_Glass", "facade", "glass", occlude=False)
IS = part("TR_I_Smooth", "interior", "smooth", adapt=True)
IR = part("TR_I_Rings", "interior", "tile", adapt=True, partner=IS, narrow=NARROW, bevel=EDGE, bevel_min=1.0)
IQ = part("TR_I_Quiet", "interior", "tile", adapt=True, partner=IS, narrow=NARROW)
IG = part("TR_I_Glass", "interior", "glass", occlude=False)
# Вещи этажа (статуи, мебель, механизмы, растения) — в стиле предметов и боссов: Plastic + LegoRingsD39Boss
# (решение владельца 2026-11-21, эталон — Крысиный король); узкие грани (< 0.5) — гладкие. Гладкие тела уходят
# в Props только на участках, отмеченных objects(True) … objects(False); архитектура остаётся как была.
FP = part("TR_F_Props", "facade", "props", adapt=True, partner=FS, narrow=0.5)
IP = part("TR_I_Props", "interior", "props", adapt=True, partner=IS, narrow=0.5)
OBJ = [0]


def objects(on=True):
    """Начало (True) / конец (False) участка с вещами: гладкие тела уходят в Props; архитектура остаётся как была."""
    OBJ[0] += 1 if on else -1
    FS.force, IS.force = (FP, IP) if OBJ[0] > 0 else (None, None)
    FR.force, IR.force = (FP, IP) if OBJ[0] > 0 else (None, None)


SL = part("TR_S_All", "silhouette", "smooth", limit=99)
QUIET = (GRASS, GRASS2, SAND, DIGSOIL, DUST)  # песок, земля, трава — на тихий материал


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
    """Плоский прямоугольник на стене, лицом в сторону out."""
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


def taper(p, a, b, w0, w1, color):
    """Сужающийся квадратный брус от a (сечение w0) к b (w1): лист, зуб, шип."""
    a, b = Vector(a), Vector(b)
    n = (b - a).normalized()
    u = Vector((0, 1, 0)).cross(n)
    if u.length < 1e-4:
        u = Vector((1, 0, 0)).cross(n)
    u.normalize()
    v = n.cross(u).normalized()

    def ring(c, w):
        return [tuple(c + u * su * w / 2 + v * sv * w / 2) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]

    p.loft(ring(a, w0), ring(b, w1), color)


def tube(p, pts, widths, thick, normal, color):
    """Изогнутая кость по точкам pts (оси этажа): ширина widths[i] поперёк, толщина thick вдоль normal. Соседние
    кольца общие — кость гладкая, без ступенек."""
    n = Vector(normal).normalized()
    pp = [Vector(q) for q in pts]
    rings = []
    for i, c in enumerate(pp):
        t = (pp[min(i + 1, len(pp) - 1)] - pp[max(i - 1, 0)]).normalized()
        u = t.cross(n).normalized()
        w = widths[i]
        rings.append([tuple(c + u * su * w / 2 + n * sv * thick / 2) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for a, b in zip(rings, rings[1:]):
        p.loft(a, b, color)


def rng(*k):
    """Детерминированное «случайное» 0…1 по ключу."""
    h = 2166136261
    for v in k:
        h = ((h ^ (int(v * 1000) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (h % 10007) / 10007.0


def rects(cells):
    """Жадное слияние клеток (c, r) в прямоугольники (c0, c1, r0, r1) — сначала по строке, затем вниз."""
    left = set(cells)
    out = []
    for r, c in sorted((r, c) for c, r in cells):
        if (c, r) not in left:
            continue
        c1 = c
        while (c1 + 1, r) in left:
            c1 += 1
        r1 = r
        while all((k, r1 + 1) in left for k in range(c, c1 + 1)):
            r1 += 1
        for rr in range(r, r1 + 1):
            for k in range(c, c1 + 1):
                left.discard((k, rr))
        out.append((c, c1 + 1, r, r1 + 1))
    return out


def anchor(p, lo, hi):
    """Две крошечные скрытые грани в углах (lo, hi): габариты детали — ровно этот брус, его центр целый (рисунок
    материала привязан к центру детали — клетки рисунка совпадают с сеткой блоков)."""
    layer = p.bm.loops.layers.float_color["tone"]
    for (x, y, z), d in ((lo, 0.01), (hi, -0.01)):
        f = p.bm.faces.new([p.bm.verts.new(K.P(*q)) for q in ((x, y, z), (x + d, y, z), (x, y + d, z))])
        for loop in f.loops:
            loop[layer] = (*K.rgb(BASALT), 1.0)


def strata(R, Q, axis, fixed, out, half, layers, seed, skip=None, step=4.0, ytop=YT, wrap=True):
    """Обрыв слоями: layers — [(низ слоя, цвет, глубина)] снизу вверх; границы слоёв ступенчатые (±1 стад по участкам
    шириной step), у краёв — ровные (слои сходятся на углу). Соседние участки с одинаковыми границами — один брусок.
    skip(a0, a1, y0, y1) → True — участок не строить (проём). Глубины 0.88 / 1.88 — грани на целых координатах."""
    lo_a, hi_a = (-half, half) if isinstance(half, (int, float)) else half
    n = max(1, int(round((hi_a - lo_a) / step)))
    edges = [lo_a + (hi_a - lo_a) * i / n for i in range(n + 1)]
    dmax = max(d for _, _, d in layers)
    bounds = []
    for i in range(n):
        corner = i in (0, n - 1)
        b = []
        for k, (y, _, _) in enumerate(layers):
            r = rng(seed, k, i)
            b.append(y + (0 if corner or k == 0 else (-1 if r < 0.3 else 1 if r > 0.72 else 0)))
        b.append(ytop)
        bounds.append(b)
    for k, (_, color, depth) in enumerate(layers):
        dst = Q if color in QUIET else R
        span = [(bounds[i][k], min(bounds[i][k + 1], ytop)) for i in range(n)]
        off = [bool(skip and skip(edges[i], edges[i + 1], *span[i])) for i in range(n)]
        i = 0
        while i < n:
            j = i
            while j + 1 < n and span[j + 1] == span[i] and off[j + 1] == off[i]:
                j += 1
            y0, y1 = span[i]
            a0, a1 = edges[i], edges[j + 1]
            if wrap and i == 0:
                a0 -= dmax
            if wrap and j == n - 1:
                a1 += dmax
            if y1 - y0 >= 0.4 and not off[i]:
                slab(dst, axis, fixed, out, depth, a0, a1, y0, y1, color)
            i = j + 1
        for i in range(1, n - 1):  # валун: участок слоя выступает ещё на стад
            y0, y1 = span[i]
            if rng(seed, 77, k, i) > 0.84 and y1 - y0 >= 2.5 and depth < 1.5 and not off[i]:
                b0 = y0 + 0.5 * int(rng(seed, 5, k, i) * 2)
                slab(R, axis, fixed, out, depth + 1.0, edges[i] + 0.5, edges[i + 1] - 0.5, b0, b0 + 2.0, color)


def amber(G, S, axis, fixed, out, a, y, size, depth):
    """Янтарь в породе: светящийся камень в тёмной оправе."""
    slab(S, axis, fixed, out, depth + 0.12, a - size / 2 - 0.2, a + size / 2 + 0.2, y - size / 2 - 0.2,
         y + size / 2 + 0.2, BASALT)
    slab(G, axis, fixed, out, depth + 0.42, a - size / 2, a + size / 2, y - size / 2, y + size / 2, AMBER, back=-depth)
    slab(G, axis, fixed, out, depth + 0.5, a - size / 4, a + size / 6, y, y + size / 3, AMBER2, back=-(depth + 0.3))


def ammonite(S, axis, fixed, out, a, y, r, depth, color):
    """Аммонит: три вложенных ступенчатых кольца-восьмиугольника и завиток."""
    for k, rr in enumerate((r, r * 0.55)):
        o = K.octa(a, y, rr, rr, rr * 0.42)
        i = K.octa(a, y, rr - 0.28, rr - 0.28, max(0.05, (rr - 0.28) * 0.42))
        d = depth + 0.2 + 0.12 * k
        lo, hi = sorted((fixed - out * 0.05, fixed + out * d))
        if axis == "z":
            S.frame_xy(o, i, lo, hi, color)
        else:
            S.frame_zy(o, i, lo, hi, color)


def frond(p, base, direction, length, width, color):
    """Лист папоротника: сужающийся брус от основания по направлению."""
    d = Vector(direction).normalized()
    taper(p, base, Vector(base) + d * length, width, 0.12, color)


def cycad(p, x, y, z, h, color_trunk=WOOD2, leaf=LEAF):
    """Саговник: ступенчатый ствол и венец из восьми листьев."""
    objects(True)
    for k in range(3):
        r = 0.55 - 0.08 * k
        p.prism_xz(K.octa(x, z, r, r, r * 0.4), y + k * h / 3, y + (k + 1) * h / 3 - 0.05, color_trunk)
    top = (x, y + h, z)
    for k in range(8):
        ang = 2 * math.pi * k / 8 + 0.3
        frond(p, top, (math.cos(ang), 0.35 if k % 2 else -0.15, math.sin(ang)), 2.6 if k % 2 else 2.2, 0.55,
              leaf if k % 2 else LEAF2)
    objects(False)


def fern(p, x, y, z, s, color=LEAF):
    objects(True)
    for k in range(5):
        ang = 2 * math.pi * k / 5
        frond(p, (x, y, z), (math.cos(ang), 0.8, math.sin(ang)), 1.4 * s, 0.4 * s, color if k % 2 else LEAF2)
    objects(False)


def bone(p, a, b, r, color):
    """Кость: стержень и утолщения на концах."""
    beam(p, a, b, r, r, color)
    for c in (a, b):
        c = Vector(c)
        p.box(c.x - r * 0.9, c.x + r * 0.9, c.y - r * 0.6, c.y + r * 0.9, c.z - r * 0.9, c.z + r * 0.9, color)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════

FACES = (("z", -FZ, -1, FX), ("z", FZ, 1, FX), ("x", -FX, -1, FZ), ("x", FX, 1, FZ))
STEP_OUT = float(next((f[5:] for f in FLAGS if f.startswith("step=")), 6.0))  # ширина участков слоёв снаружи
OUT_LAYERS = [(-1.0, BASALT, 1.88), (1.5, SLATE, 0.88), (5.0, RUST, 1.88), (8.0, SANDST, 0.88), (12.0, OCHRE, 1.88),
              (16.0, GRASS, 0.88)]

# стены за слоями (видны только в щелях)
for axis, fixed, out, half in FACES:
    if axis == "z":
        FR.plane([(-FX, YB, fixed), (FX, YB, fixed), (FX, YT, fixed), (-FX, YT, fixed)], [], (0, 0, out), BASALT)
    else:
        FR.plane([(fixed, YB, -FZ), (fixed, YB, FZ), (fixed, YT, FZ), (fixed, YT, -FZ)], [], (out, 0, 0), BASALT)

def behind_skull(a0, a1, y0, y1):
    return a0 >= -14.0 and a1 <= 14.5 and y0 >= 4.0 and y1 <= 15.0


for idx, (axis, fixed, out, half) in enumerate(FACES):
    strata(FR, FQ, axis, fixed, out, half, OUT_LAYERS, seed=11 + idx, skip=behind_skull if idx == 0 else None,
           step=STEP_OUT)
    # пояс зелени: козырёк травы над обрывом, свисающие лианы
    slab(FQ, axis, fixed, out, 2.38, -half - 2.38, half + 2.38, 17.6, 18.6, GRASS2)
    for k in range(int(2 * half / 3.5)):
        a = -half + 1.5 + k * 3.5
        if rng(idx, k, 3) > 0.6 and not (idx == 0 and -11.5 < a < 5.5):  # спереди лианы не закрывают череп
            ln = 1.5 + 3.5 * rng(idx, k, 4)
            slab(FS, axis, fixed, out, 2.2, a - 0.25, a + 0.25, 17.6 - ln, 17.65, GRASS if k % 2 else LEAF2)
        if rng(idx, k, 6) > 0.62:  # листья папоротника над козырьком
            base = (a, 18.3, fixed + out * 2.0) if axis == "z" else (fixed + out * 2.0, 18.3, a)
            d = (0.3 * (1 if k % 2 else -1), -0.25, out) if axis == "z" else (out, -0.25, 0.3 * (1 if k % 2 else -1))
            frond(FS, base, d, 1.6, 0.5, LEAF)

# ── перед: череп тираннозавра в профиле (рельеф по сетке в стад), морда — влево на снимке спереди ──
SKULL = [  # один череп в профиле: глазница с янтарём под надбровьем, перед ней окно черепа, ноздря на морде
    ".................#===#####....",
    "...........#######====#####...",
    "......#############EE########.",
    "..#######oooooo####EE#########",
    "#o########ooooo###############",
    "#####################========#",
    "TmTmTmTmTmTmTmTmTm############",
    "mmmmmmmmmmmmmmmmmm############",
    "mmtmtmtmtmtmtmtmtm############",
    ".#################==========#.",
    "...##########################.",
    "......######################..",
    "..........################....",
]
assert all(len(r) == 30 for r in SKULL)
SK_TOP = 16  # верх черепа


def skull_span(c0, c1, r0, r1):
    """Прямоугольник клеток [c0, c1) × [r0, r1) → x0, x1, y0, y1."""
    return 15 - c1, 15 - c0, SK_TOP - r1, SK_TOP - r0


def skull_xy(c, r):
    """Клетка (столбец, строка) → x0, x1, y0, y1; столбец 0 — морда (x = +15)."""
    return 15 - c - 1, 15 - c, SK_TOP - r - 1, SK_TOP - r


bonecells = {(c, r) for r, row in enumerate(SKULL) for c, ch in enumerate(row) if ch in "#="}


def dist(c, r):
    for d in range(1, 4):
        for dc in range(-d, d + 1):
            for dr in range(-d, d + 1):
                if max(abs(dc), abs(dr)) == d and (c + dc, r + dr) not in bonecells:
                    return d
    return 4


groups = {}
for c, r in bonecells:
    ch = SKULL[r][c]
    lvl = 2 if ch == "=" or dist(c, r) >= 2 else 1
    groups.setdefault((lvl, ch), set()).add((c, r))
for (lvl, ch), cells in groups.items():
    depth = 2.88 if lvl == 1 else 3.88
    color = BONE_HI if ch == "=" else BONE
    for c0, c1, r0, r1 in rects(cells):
        x0, x1, y0, y1 = skull_span(c0, c1, r0, r1)
        FR.box(x0, x1, y0, y1, -FZ + 0.05, -FZ - depth, color)
# окна черепа, пасть — тёмные углубления; глаз — янтарь
dark = {(c, r) for r, row in enumerate(SKULL) for c, ch in enumerate(row) if ch in "omEtT"}
for c0, c1, r0, r1 in rects(dark):
    x0, x1, y0, y1 = skull_span(c0, c1, r0, r1)
    FS.box(x0, x1, y0, y1, -FZ + 0.05, -FZ - 2.0, HOLE)
eye = [(c, r) for r, row in enumerate(SKULL) for c, ch in enumerate(row) if ch == "E"]
ex = sum(skull_xy(c, r)[0] + 0.5 for c, r in eye) / len(eye)
ey = sum(skull_xy(c, r)[2] + 0.5 for c, r in eye) / len(eye)
FG.box(ex - 0.85, ex + 0.85, ey - 0.8, ey + 0.85, -FZ - 1.9, -FZ - 2.45, AMBER)
FG.box(ex - 0.2, ex + 0.5, ey + 0.05, ey + 0.6, -FZ - 2.3, -FZ - 2.6, AMBER2)
# зубы: клинья вниз (верхняя челюсть) и вверх (нижняя)
for r, row in enumerate(SKULL):
    for c, ch in enumerate(row):
        if ch not in "Tt":
            continue
        x0, x1, y0, y1 = skull_xy(c, r)
        zc = -FZ - 2.9
        if ch == "T":
            ring = [(x0 + 0.08, y1, zc - 0.55), (x1 - 0.08, y1, zc - 0.55), (x1 - 0.08, y1, zc + 0.55), (x0 + 0.08, y1, zc + 0.55)]
            FS.cone(ring, ((x0 + x1) / 2 + 0.15, y0 - 0.35, zc), TOOTH)
        else:
            ring = [(x0 + 0.1, y0, zc - 0.5), (x1 - 0.1, y0, zc - 0.5), (x1 - 0.1, y0, zc + 0.5), (x0 + 0.1, y0, zc + 0.5)]
            FS.cone(ring, ((x0 + x1) / 2 + 0.15, y1 + 0.25, zc), TOOTH)
# шейные позвонки уходят в скалу за затылком
for k, (x, y) in enumerate(((-15.6, 9.5), (-17.0, 8.3))):
    FR.box(x - 0.6, x + 0.6, y - 1.2, y + 1.2, -FZ + 0.05, -FZ - 2.88, BONE)
objects(True)
# раскоп под пастью: помост из досок на столбах, лестница, рабочая лампа
for x in (6.5, 13.5):
    FS.box(x - 0.25, x + 0.25, -1.0, 2.4, -FZ - 3.4, -FZ - 2.9, WOOD2)
FS.box(5.8, 14.2, 2.4, 2.75, -FZ - 3.8, -FZ - 1.9, WOOD)
for k in range(5):
    FS.box(6.2 + k * 1.6, 6.4 + k * 1.6, 2.75, 2.8, -FZ - 3.8, -FZ - 1.9, WOOD2)
for x in (-12.6, -11.4):
    beam(FS, (x, -0.8, -FZ - 3.6), (x + 0.4, 6.0, -FZ - 2.2), 0.22, 0.22, WOOD)
for k in range(6):
    y = 0.0 + k * 1.1
    FS.box(-12.6 + y * 0.057, -11.4 + y * 0.057, y, y + 0.16, -FZ - 3.5 + y * 0.2, -FZ - 3.2 + y * 0.2, WOOD2)

objects(False)
# ── бока: позвоночник по верху и рёбра, свисающие по обрыву (плавные изогнутые кости) ──
for s in (-1, 1):
    fx = s * FX
    for k in range(7):
        z = -12 + 4 * k
        slab(FR, "x", fx, s, 3.0, z - 1.3, z + 1.3, 15.0, 17.0, BONE)  # тело позвонка
        slab(FS, "x", fx, s, 2.7, z - 2.0, z + 2.0, 15.7, 16.3, BONE)  # поперечные отростки
        taper(FS, (fx + s * 2.1, 16.9, z + 0.2), (fx + s * 2.1, 18.7, z + 1.0), 0.9, 0.35, BONE)  # остистый
    for z0 in (-8.0, -4.0, 0.0, 4.0, 8.0):
        pts, ws = [], []
        for i in range(8):
            t = i / 7
            pts.append((fx + s * 2.25, 15.4 - 12.0 * t, z0 + 3.4 * t ** 1.4))
            ws.append(1.5 - 0.9 * t)
        tube(FR, pts, ws, 1.2, (s, 0, 0), BONE)
    for z, y in ((14.6, 7.5), (-6.0, 9.5), (-14.6, 9.0)):  # янтарь — между рёбрами, не под ними
        amber(FG, FS, "x", fx, s, z, y, 0.9, 0.88)
    ammonite(FS, "x", fx, s, -12.5, 3.2, 1.3, 0.88, BONE)  # перед первым ребром, не под ним

# ── тыл: хвост по верху, янтарь, аммонит; ниша дверей лифта — у каркаса ──
for k in range(8):
    x = -14 + 4 * k
    sz = 1.0 - 0.06 * k
    slab(FR, "z", FZ, 1, 3.0 * sz, x - 1.3 * sz, x + 1.3 * sz, 15.0, 15.0 + 2.0 * sz, BONE)
    slab(FS, "z", FZ, 1, 2.7 * sz, x - 2.0 * sz, x + 2.0 * sz, 15.7, 16.3, BONE)
    taper(FS, (x + 0.2, 15.0 + 1.9 * sz, FZ + 2.1 * sz), (x - 0.9, 15.0 + 3.6 * sz, FZ + 2.1 * sz), 0.8 * sz, 0.3, BONE)
for x, y in ((-11.0, 6.5), (4.0, 3.2), (12.5, 10.0)):
    amber(FG, FS, "z", FZ, 1, x, y, 0.9, 0.88)
ammonite(FS, "z", FZ, 1, -4.0, 9.8, 1.6, 0.88, BONE)
# янтарь и спереди — по краям черепа
for x, y in ((-16.2, 5.0), (16.5, 13.0)):
    amber(FG, FS, "z", -FZ, -1, x, y, 0.8, 1.88)
anchor(FR, (-23, -1, -22), (23, 19, 22))
anchor(FQ, (-23, -1, -22), (23, 19, 22))
anchor(FP, (-23, -1, -22), (23, 19, 22))

# ══ ИНТЕРЬЕР: зал-раскоп ═══════════════════════════════════════════════════════════════════════════════════════

DOOR = (3.5, 10.5)
PLINTH = ((9.0, -11.0, -1.0, 1.2), (7.5, -10.0, -2.0, 2.2))  # постамент: полуширина, z0, z1, верх
TERR = (12.5, -14.0, 8.0, 2.0)  # уступы у боковых стен: внутренний край x, z0, z1, верх
WIN = (-11.0, 11.0, 3.0, 15.0)  # окно диорамы в передней стене зала
ARCHES = (9.0, 0.0)
IN_LAYERS = [(0.0, BASALT_I, 1.88), (2.0, SLATE_I, 0.88), (5.0, RUST_I, 1.88), (8.5, SANDST_I, 0.88),
             (12.0, OCHRE_I, 1.88), (15.5, CAVE, 0.88)]

# пол: песок раскопа (тихий материал)
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), SAND)
# потолок — тёмная порода
IR.plane([(-W, C, ZF), (W, C, ZF), (W, C, ZB), (-W, C, ZB)], [], (0, -1, 0), CAVE)
# стены (видны в щелях между слоями)
for s in (-1, 1):
    IR.plane([(s * W, 0, ZF), (s * W, 0, ZB), (s * W, C, ZB), (s * W, C, ZF)], [], (-s, 0, 0), BASALT_I)
IR.plane([(-W, 0, ZF), (W, 0, ZF), (W, C, ZF), (-W, C, ZF)], [], (0, 0, 1), BASALT_I)
IR.plane([(x, y, ZB) for x, y in [(-W, 0), (-DOOR[0], 0), (-DOOR[0], DOOR[1]), (DOOR[0], DOOR[1]), (DOOR[0], 0),
                                   (W, 0), (W, C), (-W, C)]], [], (0, 0, -1), BASALT_I)


def in_window(a0, a1, y0, y1):
    return a1 > WIN[0] and a0 < WIN[1] and y1 > WIN[2] and y0 < WIN[3]


def in_door(a0, a1, y0, y1):
    return a1 > -DOOR[0] - 1.2 and a0 < DOOR[0] + 1.2 and y0 < DOOR[1] + 1.4


for s in (-1, 1):
    strata(IR, IQ, "x", s * W, -s, ZB, IN_LAYERS, seed=40 + s, ytop=C, wrap=False, step=5.0)
for k, rng_a in enumerate(((-W, WIN[0]), (WIN[1], W))):
    strata(IR, IQ, "z", ZF, 1, rng_a, IN_LAYERS, seed=50 + k, ytop=C, wrap=False, step=3.0)
for a0, a1, y0, y1, color, depth in ((WIN[0], WIN[1], 0.0, 2.0, BASALT_I, 1.88), (WIN[0], WIN[1], 2.0, 3.0, SLATE_I, 0.88),
                                      (WIN[0], WIN[1], 15.0, C, CAVE, 0.88)):
    slab(IR, "z", ZF, 1, depth, a0, a1, y0, y1, color)
DX = DOOR[0] + 1.25
for k, rng_a in enumerate(((-W, -DX), (DX, W))):
    strata(IR, IQ, "z", ZB, -1, rng_a, IN_LAYERS, seed=60 + k, ytop=C, wrap=False, step=4.0)
for y0, y1, color, depth in ((DOOR[1] + 1.5, 15.5, OCHRE_I, 1.88), (15.5, C, CAVE, 0.88)):
    slab(IR, "z", ZB, -1, depth, -DX, DX, y0, y1, color)

# ── диорама: вулкан на закате в окне передней стены (небо и лава светятся, горы и вулкан — силуэты) ──
for y0, y1, color in ((13.0, 15.0, SKY_A), (11.0, 13.0, SKY_B), (8.5, 11.0, SKY_C), (3.0, 8.5, SKY_D)):
    quad(IG, "z", ZF + 0.15, 1, WIN[0], WIN[1], y0, y1, color)
IG.prism_xy(K.octa(7.6, 12.0, 1.4, 1.4, 0.58), ZF + 0.22, ZF + 0.3, "FFF0B0")  # солнце
RIDGE = [(-11, 3), (-11, 6.0), (-9.5, 7.2), (-8.0, 6.4), (-6.5, 7.8), (-5.2, 6.8), (5.0, 6.8), (6.5, 8.2), (8.0, 7.0),
         (9.6, 8.6), (11, 7.4), (11, 3)]
IS.prism_xy(RIDGE, ZF + 0.2, ZF + 0.55, MOUNT)
VX = -3.0  # вершина вулкана — за головой скелета (с площадки лифта голова слева)
VOLCANO = [(VX - 8.0, 3), (VX - 5.0, 7.0), (VX - 2.8, 11.2), (VX - 2.0, 13.4), (VX - 0.9, 13.0), (VX, 12.5),
           (VX + 0.9, 13.0), (VX + 2.0, 13.4), (VX + 3.0, 11.0), (VX + 6.5, 6.5), (VX + 11.0, 3.6), (VX + 11.0, 3)]
IS.prism_xy(VOLCANO, ZF + 0.5, ZF + 1.0, VOLC)
IS.prism_xy([(VX, 3), (VX, 12.5), (VX + 0.9, 13.0), (VX + 2.0, 13.4), (VX + 3.0, 11.0), (VX + 6.5, 6.5),
             (VX + 11.0, 3.6), (VX + 11.0, 3)], ZF + 0.95, ZF + 1.1, VOLC2)  # склон на свету
for path in ([(VX, 12.6), (VX + 0.6, 11.0), (VX - 0.4, 9.2), (VX + 0.9, 7.2), (VX - 0.2, 5.2), (VX + 0.8, 3.0)],
             [(VX - 1.2, 12.8), (VX - 2.4, 10.4), (VX - 2.0, 8.4), (VX - 3.6, 6.0), (VX - 4.6, 3.0)]):
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        w = 0.45
        IG.prism_xy([(ax - w, ay), (ax + w, ay), (bx + w * 0.8, by), (bx - w * 0.8, by)], ZF + 1.1, ZF + 1.22, LAVA)
IG.prism_xy([(VX - 2.0, 13.4), (VX - 0.9, 13.05), (VX, 12.55), (VX + 0.9, 13.05), (VX + 2.0, 13.4)], ZF + 1.0,
            ZF + 1.25, LAVA2)  # жерло
for x, y, r in ((VX + 0.4, 14.0, 0.9), (VX + 1.6, 14.4, 0.8), (VX - 0.9, 14.5, 0.7)):  # дым
    IS.prism_xy(K.octa(x, y, r, r * 0.8, r * 0.35), ZF + 0.3, ZF + 0.62, SMOKE)
JUNGLE_LINE = [(-11, 3), (-11, 4.6), (-10.2, 5.2), (-9.4, 4.4), (-8.4, 5.0), (-7.2, 4.2), (-5.8, 4.8), (-4.6, 4.0),
               (4.6, 4.0), (5.8, 4.9), (7.0, 4.3), (8.2, 5.1), (9.4, 4.4), (10.3, 5.3), (11, 4.7), (11, 3)]
IS.prism_xy(JUNGLE_LINE, ZF + 1.2, ZF + 1.6, JUNGLE)
for x, h in ((-9.4, 8.6), (9.6, 7.8)):  # силуэты саговников
    IS.box(x - 0.3, x + 0.3, 3.0, h, ZF + 1.25, ZF + 1.55, JUNGLE2)
    for k in range(5):
        ang = math.radians(20 + 35 * k)
        tip = (x + 2.6 * math.cos(ang), h + 1.6 * math.sin(ang) - 0.6)
        IS.prism_xy([(x - 0.2, h - 0.2), (x + 0.2, h + 0.2), tip], ZF + 1.25, ZF + 1.55, JUNGLE2)
# рама-устье пещеры: неровные глыбы по краю окна
for k in range(11):
    a = WIN[0] + 2 * k
    h = 1.0 + int(rng(9, k) * 2)
    slab(IR, "z", ZF, 1, 2.38, a, a + 2, WIN[3] - h + 1, WIN[3] + 0.6, BASALT_I)
    h2 = 1 + int(rng(8, k) * 2) if k in (0, 1, 9, 10) else 0
    if h2:
        slab(IR, "z", ZF, 1, 2.38, a, a + 2, WIN[2] - 0.6, WIN[2] + h2, BASALT_I)
for k in range(6):
    y = WIN[2] + 2 * k
    for s, x in ((-1, WIN[0]), (1, WIN[1])):
        w = 1.0 + int(rng(7, k, s) * 2)
        lo, hi = (x - 0.6, x + w) if s < 0 else (x - w, x + 0.6)
        slab(IR, "z", ZF, 1, 2.38, lo, hi, y, y + 2, BASALT_I)
IS.box(WIN[0] - 0.6, WIN[1] + 0.6, WIN[2] - 1.0, WIN[2] - 0.6, ZF - 0.05, ZF + 2.7, SANDST_I)  # уступ под окном

# ── крепь шахты вокруг дверей лифта ──
for s in (-1, 1):
    IS.box(s * (DOOR[0] + 0.15), s * (DOOR[0] + 1.25), 0, DOOR[1] + 1.3, ZB + 0.05, ZB - 1.2, WOOD)
    beam(IS, (s * (DOOR[0] + 0.7), DOOR[1] - 2.0, ZB - 0.8), (s * (DOOR[0] - 1.3), DOOR[1] + 0.6, ZB - 0.8), 0.45,
         0.45, WOOD2)
IS.box(-DOOR[0] - 2.0, DOOR[0] + 2.0, DOOR[1] + 0.3, DOOR[1] + 1.5, ZB + 0.05, ZB - 1.5, WOOD)
for x in (-DOOR[0] - 1.6, DOOR[0] + 1.6):
    IS.box(x - 0.12, x + 0.12, DOOR[1] + 0.5, DOOR[1] + 1.3, ZB - 1.55, ZB - 1.65, IRON)
IS.box(-0.06, 0.06, DOOR[1] - 0.9, DOOR[1] + 0.3, ZB - 1.0, ZB - 1.12, IRON)
IG.box(-0.35, 0.35, DOOR[1] - 1.7, DOOR[1] - 0.9, ZB - 0.71, ZB - 1.41, LAMPC)
for s in (-1, 1):  # створки лифта (утоплены в проём стены каркаса): кованое железо с ржавой полосой
    IS.box(s * 0.06, s * DOOR[0], 0, DOOR[1], 16.15, 16.45, IRON)
    IS.box(s * 0.4, s * (DOOR[0] - 0.3), 5.0, 5.8, 16.0, 16.17, RUST)

# ── постамент: скальный выход слоями (базальт, ржавый слой, светлый верх), по краю валуны ──
hw, z0, z1, top = PLINTH[0]
IR.box(-hw, hw, 0.0, 0.6, z0, z1, BASALT_I)
IR.box(-hw + 0.1, hw - 0.1, 0.6, top, z0 + 0.1, z1 - 0.1, RUST_I)
hw2, z2, z3, top2 = PLINTH[1]
IR.box(-hw2, hw2, top, top2 - 0.25, z2, z3, SANDST_I)
IS.box(-hw2 - 0.12, hw2 + 0.12, top2 - 0.25, top2, z2 - 0.12, z3 + 0.12, BASALT_I)  # тёмная кромка верха
IQ.box(-hw2 + 0.2, hw2 - 0.2, top2, top2 + 0.06, z2 + 0.2, z3 - 0.2, DUST)
for k, (x, z, w, h) in enumerate(((-8.6, -1.6, 1.6, 1.6), (8.4, -1.4, 1.8, 1.4), (-9.4, -7.0, 1.4, 1.8),
                                  (9.3, -9.5, 1.6, 1.5), (3.0, -0.7, 1.2, 0.8), (-4.5, -0.6, 1.4, 0.7),
                                  (6.2, -0.6, 1.0, 1.0), (-9.2, -10.6, 1.2, 1.2))):
    IR.box(x - w / 2, x + w / 2, 0, h, z - w / 2, z + w / 2, SLATE_I if k % 2 else BASALT_I)
for x, z in ((-7.8, -2.6), (7.6, -9.4)):  # кисть и совок на углах постамента
    beam(IS, (x, top2 + 0.1, z), (x + 0.9, top2 + 0.1, z + 0.3), 0.14, 0.14, WOOD)
    IS.box(x + 0.85, x + 1.25, top2 + 0.02, top2 + 0.2, z + 0.15, z + 0.55, IRON)

# ── уступы у боковых стен: порода, на них саговники, папоротники, кости ──
for s in (-1, 1):
    x0, x1 = s * TERR[0], s * (W - 1.88)
    IR.box(x0, x1, 0, TERR[3], TERR[1], TERR[2], BASALT_I)
    IQ.box(x0 + s * 0.2, x1, TERR[3], TERR[3] + 0.08, TERR[1] + 0.2, TERR[2] - 0.2, GRASS2)
    cycad(IS, s * 14.4, TERR[3], -11.5, 3.4)
    cycad(IS, s * 14.6, TERR[3], 4.5, 2.8)
    fern(IS, s * 13.6, TERR[3], -4.0, 1.1)
    fern(IS, s * 14.8, TERR[3], 0.5, 0.9)
    bone(IS, (s * 13.4, TERR[3] + 0.3, -7.5), (s * 15.0, TERR[3] + 0.3, -5.6), 0.35, BONE_OLD)
    for z, y in ((-6.5, 6.5), (2.0, 10.5), (11.0, 4.0)):
        amber(IG, IS, "x", s * W, -s, z, y, 0.8, 1.88 if y > 5 and y < 8.5 else 0.88)
    ammonite(IS, "x", s * W, -s, -12.5 if s < 0 else 10.5, 3.4, 1.2, 0.88, BONE_OLD)

# ── арки гигантских рёбер (плавные кости от пола до свода) и позвоночник по потолку ──
for z in ARCHES:
    for s in (-1, 1):
        pts, ws = [], []
        for i in range(8):
            th = math.radians(90 * i / 7)
            pts.append((s * 14.4 * math.cos(th), 0.25 + 16.35 * math.sin(th), z))
            ws.append(2.0 - 0.7 * i / 7)
        tube(IR, pts, ws, 1.6, (0, 0, 1), BONE_OLD)
    IR.box(-1.4, 1.4, 15.6, 17.6, z - 1.2, z + 1.2, BONE_OLD)  # позвонок в замке арки
for k in range(9):
    z = -12.0 + 3.0 * k
    if any(abs(z - a) < 1.5 for a in ARCHES):
        continue
    IR.box(-1.1, 1.1, 16.4, C - 0.02, z - 1.0, z + 1.0, BONE_OLD)

# ── гирлянды рабочих ламп ──
for x in (-7.0, 7.0):
    IS.box(x - 0.06, x + 0.06, 16.9, 17.02, ZF + 2, ZB - 2, IRON)
    for k in range(7):
        z = -11.5 + 4.0 * k
        IS.box(x - 0.05, x + 0.05, 16.3, 16.9, z - 0.05, z + 0.05, IRON)
        IG.box(x - 0.28, x + 0.28, 15.8, 16.3, z - 0.28, z + 0.28, LAMPC)

# ── пол: настил от лифта, следы, сетка раскопа, вскрытые квадраты, находки ──
for k in range(13):
    z = 14.6 - k * 1.05
    IS.box(-1.9, 1.9, 0.02, 0.24, z - 0.45, z + 0.45, WOOD if k % 2 else WOOD2)
FOOT = [(-0.25, 0.0), (0.25, 0.0), (0.45, 0.6), (1.0, 1.5), (0.7, 1.6), (0.18, 0.9), (0.12, 1.9), (-0.12, 1.9),
        (-0.18, 0.9), (-0.7, 1.6), (-1.0, 1.5), (-0.45, 0.6)]
for k, (x, z) in enumerate(((3.4, 13.0), (-3.4, 10.4), (3.4, 7.8), (-3.4, 5.2), (3.4, 2.6))):
    IS.prism_xz([(x + px * 0.9, z - pz * 0.9) for px, pz in FOOT], 0.02, 0.07, DIGSOIL)
GRID = (-12.0, 12.0, -14.0, 0.0)
for gx in range(int(GRID[0]), int(GRID[1]) + 1, 3):
    if abs(gx) < 9.5:
        continue
    IS.box(gx - 0.04, gx + 0.04, 0.32, 0.4, GRID[2], GRID[3], ROPE)
for gz in range(int(GRID[2]), int(GRID[3]) + 1, 3):
    for lo, hi in ((GRID[0], -9.5), (9.5, GRID[1])):
        IS.box(lo, hi, 0.32, 0.4, gz - 0.04, gz + 0.04, ROPE)
for gx in (-12, -9.5, 9.5, 12):
    for gz in range(int(GRID[2]), int(GRID[3]) + 1, 6):
        IS.box(gx - 0.1, gx + 0.1, 0.02, 0.55, gz - 0.1, gz + 0.1, WOOD2)
for x, z in ((-11.0, -9.5), (10.5, -6.5), (-10.8, -3.5)):
    IQ.box(x - 0.95, x + 0.95, 0.02, 0.09, z - 1.4, z + 1.4, DIGSOIL)
    bone(IS, (x - 0.6, 0.2, z - 0.8), (x + 0.5, 0.2, z + 0.7), 0.3, BONE_OLD)
for a, b in (((-6.0, 0.15, 5.0), (-4.6, 0.15, 6.4)), ((5.2, 0.15, 3.0), (6.6, 0.15, 4.4)), ((-7.5, 0.15, -12.8),
                                                                                              (-5.9, 0.15, -13.6))):
    bone(IS, a, b, 0.32, BONE_OLD)

objects(True)
# ── лампы на треногах у постамента ──
for s in (-1, 1):
    x, z = s * 10.6, 0.6
    for k in range(3):
        ang = 2 * math.pi * k / 3 + 0.4
        beam(IS, (x + 0.9 * math.cos(ang), 0.0, z + 0.9 * math.sin(ang)), (x, 4.6, z), 0.16, 0.16, IRON)
    IS.box(x - 0.45, x + 0.45, 4.6, 4.9, z - 0.45, z + 0.45, IRON)
    IG.box(x - 0.38, x + 0.38, 4.9, 5.6, z - 0.38, z + 0.38, LAMPC)

# ── ящики с находками и инструмент у лифта ──
for s in (-1, 1):
    x, z = s * 9.0, 13.2
    IS.box(x - 1.1, x + 1.1, 0, 1.6, z - 0.9, z + 0.9, WOOD)
    for y in (0.35, 1.15):
        IS.box(x - 1.15, x + 1.15, y, y + 0.18, z - 0.95, z + 0.95, WOOD2)
    bone(IS, (x - 0.5, 1.75, z - 0.3), (x + 0.6, 2.1, z + 0.3), 0.3, BONE_OLD)
    IS.box(x + s * 1.5 - 0.5, x + s * 1.5 + 0.5, 0, 0.9, z - 0.5, z + 0.5, WOOD2)
beam(IS, (-10.4, 0.0, 11.9), (-11.2, 3.2, 12.6), 0.18, 0.18, WOOD)  # черенок лопаты
IS.box(-10.75, -10.05, 0.0, 0.9, 11.75, 11.95, IRON)
beam(IS, (10.5, 0.0, 11.9), (11.0, 3.0, 12.7), 0.18, 0.18, WOOD)  # кирка
beam(IS, (10.0, 3.0, 12.6), (12.0, 2.7, 12.8), 0.22, 0.22, IRON)
for x, z in ((-12.5, 9.5), (12.6, 10.0)):  # вёдра
    IS.prism_xz(K.octa(x, z, 0.55, 0.55, 0.22), 0.0, 1.0, IRON)
    IQ.prism_xz(K.octa(x, z, 0.42, 0.42, 0.17), 1.0, 1.04, DIGSOIL)
objects(False)
anchor(IR, (-17, 0, -16), (17, 18, 16))
anchor(IQ, (-17, 0, -16), (17, 18, 16))
anchor(IP, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════

SL.box(-FX, FX, YB, YT, -FZ, FZ, RUST)
SL.box(-FX - 0.9, FX + 0.9, -1, 1.5, -FZ - 0.9, FZ + 0.9, BASALT)
SL.box(-FX - 0.5, FX + 0.5, 8, 12, -FZ - 0.5, FZ + 0.5, SANDST)
SL.box(-FX - 1.4, FX + 1.4, 16, 19, -FZ - 1.4, FZ + 1.4, GRASS)
SL.box(-14, 15, 10, 14, -FZ - 3.2, -FZ, BONE)  # череп: свод
SL.box(-11, -2, 14, 16, -FZ - 3.0, -FZ, BONE)
SL.box(0, 6, 11, 13, -FZ - 3.35, -FZ - 3.1, HOLE)  # окно черепа
SL.box(-6, -4, 12, 14, -FZ - 3.35, -FZ - 3.1, AMBER)  # глаз
SL.box(-3, 15, 9, 10, -FZ - 2.6, -FZ, TOOTH)  # зубы
SL.box(-3, 15, 8, 9, -FZ - 2.4, -FZ, HOLE)  # пасть
SL.box(-14, 14, 3, 8, -FZ - 3.2, -FZ, BONE)  # челюсть
for s in (-1, 1):
    SL.box(s * FX, s * (FX + 3.2), 15.0, 17.0, -13.5, 13.5, BONE)  # позвоночник
    for z0 in (-8.0, -4.0, 0.0, 4.0, 8.0):  # рёбра: наклонные кости
        tube(SL, [(s * (FX + 1.4), 15.0, z0), (s * (FX + 1.4), 3.4, z0 + 3.4)], [1.4, 0.7], 1.6, (s, 0, 0), BONE)
SL.box(-16, 16, 15.4, 17.6, FZ, FZ + 3.0, BONE)  # хвост

# ══ СБОРКА, ЗАТЕНЕНИЕ ═════════════════════════════════════════════════════════════════════════════════════════

collection = bpy.data.collections.new("TRexSkeletonFloor")
bpy.context.scene.collection.children.link(collection)


def proxy(name, y0, y1):
    """Соседний этаж башни (заслоняет при затенении, виден на рендерах)."""
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

TOL = float(next((f[4:] for f in FLAGS if f.startswith("tol=")), 0.11))  # допуск сетки под тени (бюджет треугольников)
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
    path = os.path.join(REPO, "assets", "models", "floors", "TRexSkeletonFloor.fbx")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    K.export_fbx([p.obj for p in parts], path)
    K.write_json(os.path.splitext(path)[0] + ".json", info)
    print("EXPORTED", path, flush=True)

# ══ ПРОВЕРОЧНЫЕ РЕНДЕРЫ ═══════════════════════════════════════════════════════════════════════════════════════

EXHIBIT = (0.0, 2.2, -6.0, 3.4)  # место и масштаб показа скелета (как в Floors/TRexSkeleton)

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
    for name, at, energy, color in (("Hall", (0, 15.0, 6.0), 6000, (1.0, 0.92, 0.78)),
                                    ("Spot", (0, 13.0, -4.0), 2500, (1.0, 0.95, 0.85))):
        lamp = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT"))
        lamp.data.energy, lamp.data.color, lamp.data.shadow_soft_size = energy, color, 2.0
        lamp.data.use_shadow = False
        lamp.location = K.P(*at)
        scene.collection.objects.link(lamp)
    item_path = os.path.join(REPO, "assets", "models", "art", "TRexSkeleton.fbx")
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.fbx(filepath=item_path)
    except Exception as err:  # noqa: BLE001
        print("ITEM_IMPORT_FAILED", err)
    item = [o for o in bpy.data.objects if o not in before]
    if item:
        img = bpy.data.images.load(os.path.join(REPO, "assets", "textures", "art", "TRexSkeleton_color.png"))
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

    inside = ("TR_S_",)
    outside = ("TR_S_", "Item", "Hall", "Spot")
    only = [f for f in FLAGS if f.startswith("shot=")]
    shots = {
        "f1_front": lambda: shot("f1_front", (0, 9, -84), (0, 9, -17), 32, hide=outside),
        "f2_side": lambda: shot("f2_side", (84, 10, -4), (18, 9, -4), 32, hide=outside),
        "f3_three_quarter": lambda: shot("f3_three_quarter", (-50, 16, -60), (0, 8.5, -12), 36, hide=outside),
        "f5_back": lambda: shot("f5_back", (32, 14, 74), (0, 9, 17), 32, hide=outside),
        "i1_lift": lambda: shot("i1_lift", (0, 5.5, 14.6), (0, 7.0, -8), 70, hide=inside),
        "i2_skel": lambda: shot("i2_skel", (7.5, 6.5, 3.0), (0, 5.0, -6.0), 60, hide=inside),
        "i3_side": lambda: shot("i3_side", (-12, 6.5, 10), (2.0, 6.0, -10), 70, hide=inside),
        "i4_back": lambda: shot("i4_back", (0, 6.5, -1.5), (0, 6.0, 16), 70, hide=inside),
        "s1_silhouette": lambda: shot("s1_silhouette", (-50, 16, -60), (0, 8.5, -12), 36,
                                      hide=("TR_F_", "TR_I_", "Item", "Hall", "Spot")),
    }
    for key, run in shots.items():
        if not only or ("shot=" + key) in only:
            run()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "TRexSkeletonFloor.blend"))
print("DONE", flush=True)
