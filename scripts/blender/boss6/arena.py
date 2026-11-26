"""Арена 6 «Джунгли» v2 (концепт D64): храм Королевы-мухоловки посреди болотистых джунглей, зона 184 × 95 стадов.

Задумка v2 (замечания владельца и дизайнера к v1 «парк, зелёное на зелёном»):
- Главное пятно кадра — королева на фоне храма из тёплого песчаника и терракоты со мхом. За ней — высокий тёмный
  проём в светлой ступенчатой арке: зелёная королева читается на тёмном, храм — на зелени джунглей. Узоры храма —
  вымышленные (квадратные спирали, листья-ромбы), без религиозных символов и лиц; корни дерева-великана лентой
  стекают по уступам.
- Джунгли, а не парк: великаны-деревья в болоте с неровными кронами (груды ступенчатых комьев с тёмным круглым дном),
  нависающими над боковыми дорожками (выше 9 стадов над настилом — «потолок»); у входа — низкие кроны в верхних
  углах кадра игрока, высокая трава, папоротники и монстеры на кочках — в нижних; за храмом и по бокам сплошная стена
  леса; лианы с крон и уступов; зеленоватая дымка за храмом и по краям (глубина), тёплый низкий свет.
- Вода всюду, кроме площадки-острова, храма и путей: болото с кувшинками, рогозом и кочками; дорожки — деревянные
  мостки на сваях, на выходе уходят в зелёный туннель под аркой из корней; центральный путь — дамба из песчаника.
Свободный бег (D66, как «Пустыня» и «Ледник»: MapLayout.Lane {48, 66}, LaneHeight {1.1, 7}): две прямые полосы-мостки
|x| 48–66 (центр 57, ширина 18) насквозь от входа до выхода, центральный путь к площадке, перемычки площадка ↔ полосы
(ширина 10); в прямоугольниках путей нет ни одной детали на высоте 1.1–7 над полом зоны (настил ниже, кроны, арки и
лианы выше 7 — допустимы). Декор — по бокам (|x| 66…92) или в середине (|x| < 48) вне круга боя. Твёрдое у стен
(|x| > 76) — верх не выше 24 (с него не допрыгнуть до кромки обрыва); кроны выше — листва без столкновений
(FOLIAGE, отдельно в arena6_stats.json). Площадка r 32, круг боя r 34 свободен выше 2, 4 места существ (arenas.SLOTS).
Оценка игры (arena6_stats.json): каждый будущий меш (крона, лианы, ствол, храм…) — треугольники без фасок черновика,
деление на MeshPart, предел 20 000 на MeshPart и цель зоны; части игры = MeshPart по плану + простые детали.
Каркас (пол, обрывы, площадка, места существ, вид сверху) — scripts/blender/concepts510/arenas.py; королева —
flytrap.py (поза сна), существа — creatures.py.

Запуск: python blender_locked.py scripts/blender/boss6/arena.py [quick] [player,approach,lane,top] [haze=0.015]
        [sweep=0.006,0.012 sweepdir=<папка>] — перебор плотности дымки на кадре игрока;
        [cams=<file.json> sweepdir=<папка>] — пробные ракурсы {имя: [глаз, цель, объектив]}.
Кадры: assets/concepts/bosses_5_10/boss6_v2/raw/arena6_{player,approach,lane,top}.png и arena6_stats.json (вне git).
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "concepts510"))
import arenas as A  # noqa: E402
import ck as C  # noqa: E402

BOSS, HL, HW = A.BOSS, A.HL, A.HW
HERE_DIR = os.path.dirname(os.path.abspath(__file__))
LANE_X, LANE_W = 57.0, 18.0  # полосы свободного бега |x| 48–66 насквозь: вход → выход (D66, MapLayout.Lane)
LANE_IN, LANE_OUT = LANE_X - LANE_W / 2, LANE_X + LANE_W / 2  # 48 и 66
LINK_W = 10.0  # перемычки площадка ↔ полосы
DECK = 0.95  # верх настила мостков (пол дорожки)
WATER_X = 33.4  # болото от |x| = 33.4 (сразу за площадкой: мостки над водой с обеих сторон) до скал
WATER_Z = 0.45  # уровень воды
FLOOR = 0.3  # верх травы
FIGHT_R = 34.0
LANE_Z = (FLOOR + 1.1, FLOOR + 7.0)  # слой полосы, где нельзя ничего (MapLayout.LaneHeight над полом зоны)
WALL_X, WALL_TOP = 76.0, 24.0  # твёрдое у стен (|x| > 76) — верх не выше 24
FOLIAGE = ("Canopy", "BackCanopy")  # части-листва без столкновений (кроны, лианы): в игре CanCollide = false
HAZE = 0.015  # плотность дымки за храмом и по бокам (перебор 0.001…0.008 сплошной дымкой: замыливала храм)
QUEEN_SCALE = 1.733  # запасной масштаб; основной — export_scale из raw/stats.json (render.py)
Y0, Y1 = -HL - 6, HL + 6  # пол зоны по длине

PAL = {
    # земля и вода
    "grass": "4E9A3A", "grassD": "3C8032", "cliff": "6E6A4A", "cliffTop": "4E8F3A", "mud": "6B4A2B", "mudD": "4E3520",
    "water": "3E9C88", "waterD": "2E7A6C", "waterL": "7FCFB4", "lily": "5DB040", "lilyD": "3F8E35",
    # мостки и площадка
    "path": "C48C58", "pathL": "D6A56E", "pathM": "B47D4B", "pathD": "8A5A33", "post": "6A4426", "plat": "D2B183",
    "platEdge": "A8683E", "slot": "C7774A", "stoneL": "EBD3A6",
    # храм
    "sand": "E2B279", "sandD": "C98F58", "sandL": "F4DDB0", "terra": "CF6A40", "terraD": "A04B2E",
    "cave": "2A1C16", "caveD": "1C130F", "gold": "F5B21C", "goldD": "C27E0E", "jade": "36D6A8",
    # растения
    "moss": "6DB33F", "mossD": "4A9234", "fol": "2F8A45", "folD": "1F6A3A", "folL": "6FBF48", "folY": "B4D65A",
    "folS": "174F2E", "fern": "4FA845", "vine": "3F7A2C", "vineL": "7CC04A", "trunk": "7A5232", "trunkD": "553620", "bark": "9A6E44",
    "reed": "8BAF4A", "cattail": "7A4A26",
    # цветы-акценты
    "flower": "FF6FAE", "flowerD": "E0458C", "orange": "FF9A3C", "petal": "FFD23F", "petalW": "FFF6E0",
    "mush": "E8384F", "white": "FFFFFF",
}
RINGS = ("grass", "cliff", "plat", "sand", "sandD", "terra", "fol", "folD", "trunk", "path", "lily", "mud", "moss")
FREE = []  # прямоугольники путей (x0, x1, y0, y1, пол) — проверка свободного бега
EXIT_Y = 76.0  # мостки полос идут за выход зоны в туннель до y 74: продолжение полосы тоже свободно (D66)
EXIT_FREE = []  # прямоугольники полос за выходом (x0, x1, Y1, EXIT_Y, пол) — та же проверка слоя 1.1–7
GAME = {}  # оценка частей в игре по категориям (крупное — меши)
MESHES = []  # будущие игровые меши: (имя, вид, треугольники черновика, оценка игры без фасок)
CAUSE = 0.8  # верх каменной дамбы центрального пути (над водой)
MESHPART_LIMIT = 20000  # предел треугольников одного MeshPart
ZONE_TRIS = 200000  # цель игровой копии зоны: все меши декора вместе, треугольники
TARGET = {"крона": 3500, "лианы": 1500, "дерево": 2500, "храм": 12000, "корни": 1500, "заросли": 3000,
          "болото": 6000, "мостки": 4000, "рамка": 4000}  # цель игровой копии на один меш, треугольники


def est(cat, n=1):
    GAME[cat] = GAME.get(cat, 0) + n


def tri_est(a, n0=0):
    """Треугольники деталей a.parts[n0:]: всего (с фасками черновика) и без фасок (игровая копия: тонкие грани
    фасок и уголки не считаются)."""
    full = game = 0
    for bm, *_ in a.parts[n0:]:
        for f in bm.faces:
            t = len(f.verts) - 2
            full += t
            ar = f.calc_area()
            longest = max(e.calc_length() for e in f.edges)
            if ar > 1e-3 and ar / max(longest, 1e-9) > 0.03:  # полоса фаски — ширина 0.012, уголок — крошечный
                game += t
    return full, game


def mesh_rec(name, kind, a, n0=0, split=1):
    """Записать будущий игровой меш (split — на сколько MeshPart он делится в игре)."""
    full, game = tri_est(a, n0)
    MESHES.append((name, kind, full, game, split))


def mk(name):
    return A.art(name, PAL, RINGS)


def rnd(seed):
    g = A.rnd(seed)
    return lambda: next(g)


def in_lane(x, y, pad=0.0):
    """Точка над прямоугольником пути (с запасом pad)?"""
    return any(x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad for x0, x1, y0, y1, _ in FREE)


def in_exit(x, y, pad=0.0):
    """Точка над продолжением полосы за выходом зоны (туннель)?"""
    return any(x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad for x0, x1, y0, y1, _ in EXIT_FREE)


def near_fight(x, y, r=0.0):
    return math.hypot(x - BOSS[0], y - BOSS[1]) < FIGHT_R + r


# ── Детали растений (стиль D39: ступенчатые звенья, острые рёбра) ─────────────────────────────────────────────
def blade(a, key, rib, p0, yaw, length, width, pitch, droop, segs=3, th=0.22, taper=0.3):
    """Лист-лопасть: segs плоских звеньев, каждое уже и круче вниз (ступени); rib — светлая жилка по центру."""
    p = Vector(p0)
    yaw, pitch, droop = math.radians(yaw), math.radians(pitch), math.radians(droop)
    for i in range(segs):
        w = width * max(1.0 - taper * i, 0.25)
        d = Vector((math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)))
        q = p + d * (length / segs)
        C.bar(a, key, p - d * 0.2, q, w, th)
        if rib and i < segs - 1:
            C.bar(a, rib, p - d * 0.1, q, min(0.22, w * 0.2), th + 0.1, bevel=0)
        p = q
        pitch -= droop
    return p


def fan(n, g, yaws, step, jit):
    """Углы листьев: равномерно по кругу или веером в секторе yaws = (от, до) (рамка у пути — листья наружу)."""
    if yaws is None:
        return [k * step + jit * g() for k in range(n)]
    lo, hi = yaws
    return [lo + (hi - lo) * (k + 0.3 + 0.4 * g()) / n for k in range(n)]


def fern(a, x, y, s, g, keys=("fern", "folL"), z=FLOOR, yaws=None, n=8):
    """Папоротник: розетка из дугой изогнутых вай с жилкой, кочка-основание."""
    a.prism("mossD", C.ngon(x, y, 0.9 * s, 7), z - 0.05, z + 0.5 * s)
    for k, yaw in enumerate(fan(n, g, yaws, 360 / n, 20)):
        blade(a, keys[k % 2], "folY", (x, y, z + 0.4 * s), yaw, 3.6 * s, 0.95 * s, 58 - 10 * g(), 42, segs=3,
              th=0.16)
    est("папоротники")


def tall_grass(a, x, y, h, g, z=FLOOR, yaws=None, n=7, w=0.42):
    """Высокая трава: пучок узких изогнутых травинок разной высоты."""
    for k, yaw in enumerate(fan(n, g, yaws, 51, 30)):
        hh = h * (0.6 + 0.4 * g())
        blade(a, ("folY", "folL", "fern")[k % 3], None, (x, y, z - 0.05), yaw, hh, w, 82 - 8 * g(),
              14 + 8 * g(), segs=3, th=0.14, taper=0.25)
    est("трава")


def monstera(a, x, y, s, g, z=FLOOR, yaws=None, n=6, pitch=48):
    """Куст монстеры: огромные листья с жилкой, сужаются к концу (в игре — один меш)."""
    for k, yaw in enumerate(fan(n, g, yaws, 60, 25)):
        blade(a, "fol" if k % 2 else "folD", "folL", (x, y, z + 0.3), yaw, 6.0 * s, 2.6 * s,
              pitch + 10 * g(), 30, segs=3, th=0.24, taper=0.3)
    est("монстеры")


def flower(a, x, y, z, r, g, key="flower", core="petal"):
    """Гигантский цветок: 6 лепестков-брусков веером, серединка ступенькой."""
    for k in range(6):
        t = math.radians(k * 60 + 30 * g())
        px, py = x + r * 0.8 * math.cos(t), y + r * 0.8 * math.sin(t)
        m = C.tilt((px, py, z + 0.3), "Z", math.degrees(t))
        a.box(key if k % 2 else key + "D" if key == "flower" else key, px - r * 0.55, px + r * 0.55,
              py - r * 0.3, py + r * 0.3, z, z + 0.5, matrix=m @ C.tilt((px, py, z), "Y", -18))
    a.prism(core, C.ngon(x, y, r * 0.38, 8), z, z + 0.9)
    a.prism("gold", C.ngon(x, y, r * 0.2, 6), z + 0.9, z + 1.2)


def liana(a, top, z_end, g, leaf_every=3, bloom=False):
    """Свисающая лиана: звенья 1.6 с лёгким зигзагом, пары листиков; конец не ниже z_end."""
    x, y, z = top
    i = 0
    while z - 1.6 >= z_end:
        dx = 0.25 if i % 2 else -0.25
        C.bar(a, "vine", (x, y, z + 0.1), (x + dx, y, z - 1.6), 0.34, 0.34)
        x += dx
        z -= 1.6
        if i % leaf_every == 1:
            for s in (1, -1):
                a.box("vineL", x - 0.1, x + s * 1.0, y - 0.32, y + 0.32, z - 0.12, z + 0.12, bevel=0,
                      matrix=C.tilt((x, y, z), "Y", s * 28))
        i += 1
    if bloom:  # цветок-колокольчик на конце: 5 лепестков вниз-наружу и жёлтая серединка (не «розовый кубик»)
        for k in range(5):
            t = math.radians(72 * k + 20)
            C.bar(a, "flower" if k % 2 else "flowerD", (x, y, z - 0.1),
                  (x + 0.75 * math.cos(t), y + 0.75 * math.sin(t), z - 0.6), 0.42, 0.12)
        a.prism("petal", C.ngon(x, y, 0.22, 6), z - 0.45, z - 0.05)
    est("лианы")
    return z


def drape(a, p0, p1, sag, g):
    """Лиана-гирлянда между двумя точками: провис sag, листики по длине."""
    n = 9
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(Vector(p0).lerp(Vector(p1), t) - Vector((0, 0, sag * 4 * t * (1 - t))))
    for i in range(n):
        C.bar(a, "vine", pts[i], pts[i + 1], 0.36, 0.36)
        if i % 2:
            c = pts[i]
            a.box("vineL", c.x - 0.5, c.x + 0.5, c.y - 0.3, c.y + 0.3, c.z - 0.9, c.z - 0.2, bevel=0)
    est("лианы")


# ── Пути: мостки на сваях, перемычки, каменный путь ──────────────────────────────────────────────────────────
PLANKS = ("path", "pathL", "path", "pathM", "pathL", "path", "pathM")  # доски разнотонные, без тёмных полос


def deck(p, xa, xb, y0, y1, g, outer):
    """Настил мостков между y0 и y1: сваи, балки, доски почти встык (светлые, разного тона и длины), брус-бортик
    только с внешней стороны (outer = x бортика)."""
    rails = (xa + 0.8, (xa + xb) / 2, xb - 0.8) if xb - xa > 12 else (xa + 0.8, xb - 0.8)  # широкий — и посередине
    y = y0
    while y < y1 + 0.1:  # сваи под балками каждые 6
        for xp in rails:
            p.prism("post", C.ngon(xp, y, 0.55, 6), 0.1, DECK - 0.15)
        y += 6.0
    for xr in rails:  # балки
        p.box("pathD", xr - 0.45, xr + 0.45, y0, y1, DECK - 0.45, DECK - 0.17)
    y = y0
    i = 0
    while y < y1 - 0.05:  # доски: шов 0.08, у каждой третьей — свой сдвиг концов (не «шпалы»)
        y2 = min(y + 1.9 + 0.5 * g(), y1)
        jx = 0.25 * g() if i % 3 == 0 else 0.0
        p.box(PLANKS[i % len(PLANKS)], xa + 0.1 + jx, xb - 0.1 - jx, y + 0.04, y2 - 0.04, DECK - 0.2, DECK)
        y = y2
        i += 1
    if outer is not None:  # брус-бортик (≤ 0.35 над настилом) только снаружи, за краем полосы, на своих столбиках
        p.box("pathM", outer - 0.3, outer + 0.3, y0, y1, DECK - 0.05, DECK + 0.35)
        y = y0
        while y < y1 + 0.1:
            p.prism("post", C.ngon(outer, y, 0.35, 6), 0.1, DECK - 0.05)
            y += 6.0


def lanes():
    """Мостки над болотом: сваи, продольные балки, светлые разнотонные доски, бортик только с внешней стороны.
    Перемычки к площадке — такие же мостки. Центральный путь — дамба из песчаника над водой."""
    p = mk("Lanes")
    g = rnd(41)
    for s in (1, -1):
        x0, x1 = s * LANE_X - LANE_W / 2, s * LANE_X + LANE_W / 2
        FREE.append((min(x0, x1), max(x0, x1), Y0, Y1, DECK))
        EXIT_FREE.append((min(x0, x1), max(x0, x1), Y1, EXIT_Y, DECK))
        xa, xb = min(x0, x1), max(x0, x1)
        deck(p, xa, xb, Y0, Y1, g, s * (LANE_OUT + 0.35))  # бортик |x| 66.05–66.65 — за краем полосы
        est("мостки", int((Y1 - Y0) / 10) + 1)
    for s in (1, -1):  # перемычки площадка ↔ мостки
        xa, xb = sorted((s * (A.PLAT_R - 1.0), s * (LANE_X - LANE_W / 2 + 0.3)))
        y0, y1 = BOSS[1] - LINK_W / 2, BOSS[1] + LINK_W / 2
        FREE.append((xa, xb, y0, y1, DECK))
        for yy in (y0 + 0.8, y1 - 0.8):
            p.box("pathD", xa, xb, yy - 0.45, yy + 0.45, DECK - 0.45, DECK - 0.17)
            p.prism("post", C.ngon((xa + xb) / 2 + s * 1.2, yy, 0.5, 6), 0.1, DECK - 0.15)
        x = xa
        i = 0
        while x < xb - 0.2:
            p.box(PLANKS[i % len(PLANKS)], x + 0.04, min(x + 1.96, xb), y0 + 0.1, y1 - 0.1, DECK - 0.2, DECK)
            x += 2.0
            i += 1
        est("мостки")
    # центральный путь — дамба из песчаника над водой: основание и плиты (верх CAUSE)
    yt = BOSS[1] - A.PLAT_R + 1
    FREE.append((-6.0, 6.0, Y0, yt, CAUSE))
    p.box("sandD", -6.2, 6.2, Y0, yt, FLOOR - 0.1, CAUSE - 0.18)
    p.box("terraD", -6.5, 6.5, Y0, yt, FLOOR - 0.1, WATER_Z + 0.12)  # цоколь у воды
    for k, y in enumerate(range(int(Y0), int(yt), 3)):  # плиты встык со швом
        dx = 0.35 if k % 2 else -0.35
        p.box("stoneL" if k % 3 else "sand", -5.9 + dx, 5.9 + dx, y + 0.05, min(y + 2.95, yt), CAUSE - 0.2, CAUSE)
    est("каменный путь", 4)
    mesh_rec("мостки ×2, перемычки, дамба", "мостки", p, split=3)


def theme():
    return dict(pal=PAL, rings=RINGS, floor="grass", cliff="cliff", cliffTop="cliffTop", path="grassD",
                plat="plat", platEdge="platEdge", slot="slot", plat_fn=plat_mosaic, path_w=12.0)


def plat_mosaic(q):
    """Терраса из тёплого камня: терракотовые кольца, листья-мозаика, мох пятнами."""
    bx, by = BOSS
    q.frame("terra", C.ngon(bx, by, 25.0, 32), 0.9, 0.58, 0.64, axis="z")
    q.frame("sandD", C.ngon(bx, by, 13.0, 24), 0.7, 0.58, 0.64, axis="z")
    for i in range(8):  # листья-ромбы мозаикой между кольцами, с жилкой
        t = math.radians(22.5 + 45 * i)
        c, s_ = math.cos(t), math.sin(t)
        cx, cy = bx + 19 * c, by + 19 * s_
        dia = [(cx + 4.6 * c, cy + 4.6 * s_), (cx - 1.9 * s_, cy + 1.9 * c), (cx - 4.6 * c, cy - 4.6 * s_),
               (cx + 1.9 * s_, cy - 1.9 * c)]
        q.prism("terraD" if i % 2 else "terra", dia, 0.57, 0.64)
        C.bar(q, "sandL", (cx - 3.4 * c, cy - 3.4 * s_, 0.645), (cx + 3.4 * c, cy + 3.4 * s_, 0.645), 0.3, 0.04,
              bevel=0)
    g = rnd(61)
    for k in range(16):  # мох пятнами у края
        t = g() * 2 * math.pi
        r = 26.5 + 3.5 * g()
        x, y = bx + r * math.cos(t), by + r * math.sin(t)
        q.box("moss" if k % 3 else "mossD", x - 1.0 - g(), x + 1.0 + g(), y - 0.8 - g(), y + 0.8 + g(), 0.58, 0.66)
    est("площадка", 24)


def mossy_border():
    """Бордюр из мха и мелких цветов по краю площадки: ≤ 0.8 над полом, проходы к путям широкие."""
    b = mk("Border")
    R = A.PLAT_R + 1.4
    gaps = (-90, 0, 180)  # вход и обе перемычки
    for a in range(-180, 180, 6):
        if any(abs(((a - gp + 180) % 360) - 180) < 16 for gp in gaps):
            continue
        t = math.radians(a)
        x, y = BOSS[0] + R * math.cos(t), BOSS[1] + R * math.sin(t)
        b.prism("moss" if a % 12 else "mossD", C.ngon(x, y, 1.25, 6), 0.3, 0.88)
        if a % 18 == 0:
            b.prism("flower" if a % 36 else "orange", C.ngon(x, y, 0.45, 5), 0.88, 1.08)
    est("площадка", 8)


# ── Храм из песчаника с тёмным проёмом ────────────────────────────────────────────────────────────────────────
DOOR = 12.0  # полуширина проёма внизу
TIERS = ((33.0, 33.0, 2.2, 10.0, "sand"), (27.0, 35.5, 10.0, 17.5, "sandD"), (21.0, 38.0, 17.5, 24.0, "sand"),
         (15.0, 40.5, 24.0, 30.0, "sandD"))  # (полуширина, перед y, z0, z1, цвет)
Y_BACK = HL + 0.5


def spiral(t, x, y, z, s, key):
    """Квадратная спираль-рельеф на фасаде (лицом к −y): 5 брусков по сходящейся спирали."""
    pts = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-0.6, 1.0), (-0.6, -0.4), (0.4, -0.4), (0.4, 0.3)]
    for (u0, w0), (u1, w1) in zip(pts, pts[1:]):
        xa, xb = sorted((x + u0 * s, x + u1 * s))
        za, zb = sorted((z + w0 * s, z + w1 * s))
        t.box(key, xa - 0.16 * s, xb + 0.16 * s, y - 0.28, y + 0.05, za - 0.16 * s, zb + 0.16 * s, bevel=0.01)


def leaf_rhomb(t, x, y, z, s, key, inner):
    m = C.tilt((x, y, z), "Y", 45)
    t.box(key, x - 0.85 * s, x + 0.85 * s, y - 0.22, y + 0.05, z - 0.85 * s, z + 0.85 * s, matrix=m)
    t.box(inner, x - 0.32 * s, x + 0.32 * s, y - 0.34, y - 0.15, z - 0.32 * s, z + 0.32 * s, matrix=m, bevel=0)
    C.bar(t, inner, (x, y - 0.3, z - 1.1 * s), (x, y - 0.3, z + 1.1 * s), 0.14, 0.12, bevel=0)


def moss_edge(t, x0, x1, y_front, z_top, g, drips=True):
    """Мох шапкой по краю уступа и «подтёки» мха вниз по фасаду ступенями."""
    x = x0
    while x < x1 - 0.5:
        ln = min(2.5 + 3.0 * g(), x1 - x)
        t.box("moss" if g() > 0.4 else "mossD", x, x + ln, y_front - 0.5, y_front + 2.2, z_top - 0.05,
              z_top + 0.35 + 0.4 * g())
        if drips and g() > 0.45:
            d = 0.8 + 2.4 * g()
            xm = x + ln * (0.3 + 0.4 * g())
            t.box("moss", xm - 0.7, xm + 0.7, y_front - 0.45, y_front + 0.1, z_top - d, z_top + 0.1)
            if d > 1.6:
                t.box("mossD", xm - 0.35, xm + 0.35, y_front - 0.4, y_front + 0.1, z_top - d - 0.8, z_top - d + 0.1)
        x += ln + 0.15


def temple():
    """Ступенчатый храм из песчаника: цоколь, 4 уступа с терракотовыми карнизами, мох шапками и подтёками,
    рельефы-спирали и листья-ромбы; посередине — высокий тёмный проём в светлой ступенчатой арке; наверху — святилище
    с огромным цветком; по углам нижнего уступа — вазы с цветами."""
    t = mk("Temple")
    g = rnd(66)
    # цоколь и ступени к проёму (вне круга боя: от y 29.4)
    t.box("sandD", -33.5, 33.5, 31.0, Y_BACK, FLOOR - 0.1, 2.2)
    t.box("sandL", -33.8, 33.8, 30.7, 32.0, 1.9, 2.4)
    for i in range(3):
        t.box("sandL" if i % 2 == 0 else "sand", -15 + i, 15 - i, 29.4 + i * 0.6, 31.2, FLOOR - 0.05, 0.95 + i * 0.6)
    est("храм", 3)
    # уступы: у первых двух — разрез под проём
    for k, (w, yf, z0, z1, key) in enumerate(TIERS):
        if k < 3:
            for s in (1, -1):
                t.box(key, s * DOOR, s * w, yf, Y_BACK, z0, z1)
        else:
            t.box(key, -w, w, yf, Y_BACK, z0, z1)
        spans = ((-w - 0.3, -DOOR), (DOOR, w + 0.3)) if k < 3 else ((-w - 0.3, w + 0.3),)  # проём не перекрывать
        for xa, xb in spans:
            t.box("terra", xa, xb, yf - 0.4, yf + 1.4, z1 - 0.9, z1 + 0.05)  # карниз
            t.box("terraD", xa + (0.2 if xa < -DOOR else 0), xb - (0.2 if xb > DOOR else 0), yf - 0.3, yf + 1.4,
                  z1 - 1.25, z1 - 0.85)
            moss_edge(t, xa + 0.1, xb - 0.1, yf, z1, g, drips=True)
        # рельефы на фасаде: спирали и листья через один, крупно; середину прячет арка
        zc = (z0 + z1) / 2 - 0.4
        n = 0
        for x in range(int(-w) + 3, int(w) - 2, 6):
            if abs(x) < DOOR + 6.5:
                continue
            if n % 2 == 0:
                spiral(t, x, yf, zc, 1.15, "sandL" if key == "sandD" else "terra")
            else:
                leaf_rhomb(t, x, yf, zc, 1.4, "sandL" if key == "sandD" else "terraD", "mossD")
            n += 1
        est("храм", 3)
    # тёмный проём: глубокая ниша (в игре — тёмная деталь + неон-полоса не нужна)
    t.box("cave", -DOOR, DOOR, 40.0, Y_BACK - 2, 2.2, 27.0)
    t.box("caveD", -DOOR + 1.5, DOOR - 1.5, 39.8, 40.2, 3.6, 19.0)  # «глубина» — ещё темнее в середине
    for i, (y0, z1, key) in enumerate(((36.0, 2.8, "sandD"), (37.4, 3.3, "terraD"), (38.7, 3.8, "cave"))):
        t.box(key, -DOOR + 0.01, DOOR - 0.01, y0, 40.1, 2.2, z1)  # ступени уходят в темноту
    # светлая ступенчатая арка: пилоны, ступени-консоли, перемычка с золотым знаком
    for s in (1, -1):
        t.box("sandL", s * DOOR, s * (DOOR + 4.5), 31.0, 37.5, 2.2, 19.0)  # пилон
        t.box("terra", s * (DOOR - 0.2), s * (DOOR + 4.8), 30.6, 37.0, 2.2, 3.4)  # база пилона
        for zb in (8.0, 14.0):
            t.box("terra", s * (DOOR - 0.2), s * (DOOR + 4.8), 30.7, 36.0, zb, zb + 0.8)
        spiral(t, s * (DOOR + 2.25), 31.0, 5.8, 1.0, "terraD")
        spiral(t, s * (DOOR + 2.25), 31.0, 11.5, 1.0, "terraD")
        leaf_rhomb(t, s * (DOOR + 2.25), 31.0, 16.6, 1.0, "terra", "mossD")
        # консоли сужают проём ступенями
        t.box("sandL", s * 9.0, s * (DOOR + 4.5), 31.0, 37.5, 19.0, 22.5)
        t.box("terra", s * 8.8, s * (DOOR + 4.8), 30.7, 36.0, 18.8, 19.4)
        t.box("sandL", s * 6.0, s * (DOOR + 4.5), 31.0, 37.5, 22.5, 26.0)
        t.box("terra", s * 5.8, s * (DOOR + 4.8), 30.7, 36.0, 22.3, 22.9)
    t.box("sandL", -(DOOR + 5.0), DOOR + 5.0, 30.8, 37.5, 26.0, 30.0)  # перемычка
    t.box("terra", -(DOOR + 5.3), DOOR + 5.3, 30.4, 37.0, 29.4, 30.5)
    t.box("terraD", -(DOOR + 5.0), DOOR + 5.0, 30.5, 36.0, 25.7, 26.3)
    moss_edge(t, -(DOOR + 5.3), DOOR + 5.3, 30.4, 30.5, g, drips=True)
    # знак на замке арки: золотая спираль в терракотовом ромбе с нефритом
    m = C.tilt((0, 30.4, 28.0), "Y", 45)
    t.box("terraD", -2.0, 2.0, 30.1, 30.6, 26.0, 30.0, matrix=m)
    spiral(t, 0, 30.1, 28.0, 1.0, "gold")
    C.gem(t, "jade", (0, 29.8, 28.0), 0.9)
    est("храм", 8)
    # святилище наверху: без цветка на оси — над головой королевы чистый камень и тёмная листва
    t.box("sand", -9, 9, 42.0, Y_BACK, 30.0, 33.0)
    t.box("terra", -9.4, 9.4, 41.6, Y_BACK, 32.6, 33.6)
    moss_edge(t, -9.4, 9.4, 41.6, 33.6, g, drips=False)
    est("храм", 3)
    # вазы на углах нижнего уступа
    for s in (1, -1):
        x = s * 28.5
        t.prism("terraD", C.ngon(x, 34.4, 2.4, 8), 10.0, 11.0)
        t.prism("terra", C.ngon(x, 34.4, 3.2, 8), 11.0, 13.4)
        t.prism("sandL", C.ngon(x, 34.4, 3.5, 8), 13.4, 13.9)
        flower(t, x, 34.4, 13.9, 3.0, g, key="flower" if s > 0 else "orange", core="petal")
        est("храм", 2)
    # лианы с карнизов (не над проёмом)
    for k, (w, yf, z0, z1, key) in enumerate(TIERS):
        for x in range(int(-w) + 2, int(w) - 1, 5):
            if abs(x) < DOOR + 5.5 or g() < 0.35:
                continue
            liana(t, (x + 0.3, yf - 0.7, z1 - 0.9), max(FLOOR + 2.5, z1 - 3.0 - 6.0 * g()), g, bloom=g() > 0.7)
    for s in (1, -1):  # лианы по краям арки — рамка проёма, середина тёмная
        for dx in (0.6, 2.2, 3.8):
            liana(t, (s * (DOOR + dx), 30.2, 29.4), 14.0 + 6.0 * g(), g, bloom=dx > 3)
    mesh_rec("храм: уступы, арка, рельефы, вазы, лианы карнизов", "храм", t, split=2)


def root_drape(tr, s, g):
    """Корень дерева храма сплошной лентой: с крыши святилища ложится на уступы и стекает по фасадам, прижатый к
    камню (не торчит палками); толстый вверху, тоньше книзу; на горизонтальных участках — шапки мха; внизу
    раздваивается в воду. Идёт сбоку от арки ступенями наискось (|x| 15…22), рельефов и консолей не касается."""

    def b(key, u0, u1, y0, y1, z0, z1):
        xa, xb = sorted((s * u0, s * u1))
        tr.box(key, xa, xb, y0, y1, z0, z1)

    b("trunk", 3.5, 15.4, 44.9, 48.7, 29.9, 31.7)  # по крыше 4-го уступа (z 30) от ствола в сторону
    b("moss", 9.6, 14.2, 45.3, 48.2, 31.6, 32.0)
    b("trunk", 14.9, 17.7, 44.5, 48.7, 23.9, 31.75)  # вниз по боковой грани 4-го уступа
    # дальше лента идёт ступенями наискось наружу: на каждом уступе сдвигается на ~1.5 и сужается (3.3 → 2.6)
    b("trunk", 15.95, 19.25, 37.3, 47.0, 23.85, 25.3)  # по верху 3-го уступа вперёд
    b("moss", 16.3, 18.9, 38.6, 44.5, 25.2, 25.65)
    b("trunk", 16.6, 19.6, 37.2, 38.25, 17.35, 25.25)  # по фасаду 3-го
    b("trunkD", 19.1, 19.75, 37.0, 38.2, 17.4, 25.2)  # тёмная кромка ленты — объём
    b("trunk", 16.9, 21.0, 34.7, 38.2, 17.3, 18.45)  # по верху 2-го — шаг наружу
    b("moss", 17.4, 20.4, 35.3, 37.7, 18.4, 18.8)
    b("trunk", 18.15, 21.05, 34.75, 35.75, 9.9, 18.4)  # по фасаду 2-го
    b("trunkD", 20.55, 21.2, 34.55, 35.7, 9.95, 18.35)
    b("trunk", 18.4, 22.3, 32.3, 35.7, 9.85, 10.95)  # по верху 1-го — шаг наружу
    b("moss", 18.8, 21.9, 32.8, 35.1, 10.9, 11.3)
    b("trunk", 19.6, 22.2, 32.35, 33.25, 2.1, 10.9)  # по фасаду 1-го
    b("trunkD", 21.7, 22.25, 32.15, 33.2, 2.15, 10.85)
    b("trunk", 19.8, 22.4, 30.3, 32.5, 1.9, 2.95)  # через бортик цоколя
    # корешки вбок по фасадам (над рельефами), с загибом вниз
    b("trunkD", 21.0, 25.4, 35.6, 36.4, 17.4, 18.15)
    b("trunkD", 24.6, 25.4, 34.85, 35.65, 15.3, 18.15)
    b("trunkD", 22.1, 27.6, 32.45, 33.2, 7.9, 8.7)
    b("trunkD", 26.8, 27.6, 32.45, 33.2, 6.0, 8.7)
    for u0, u1, y1 in ((20.4, 18.0, 28.4), (21.8, 24.8, 28.9)):  # раздвоение у воды
        C.bar(tr, "trunk", (s * u0, 30.6, 2.3), (s * u1, y1, FLOOR + 0.1), 1.3, 1.0)
    est("храм", 2)


def temple_tree():
    """Дерево-великан, проросшее сквозь храм: ствол за святилищем, корни стекают по уступам по бокам от арки,
    огромная крона закрывает небо над храмом (тёплый камень читается на тёмной зелени)."""
    tr = mk("TempleTree")
    cn = mk("CanopyTemple")
    g = rnd(77)
    x, y, h = 0.0, 51.0, 41.0
    for k, (r, z0, z1) in enumerate(((4.4, 20.0, 30.0), (3.8, 29.8, 35.0), (3.2, 34.8, 39.0), (2.7, 38.8, h))):
        tr.prism("trunk" if k % 2 == 0 else "bark", C.ngon(x, y, r, 9), z0, z1)
        tr.prism("moss", C.ngon(x, y, r + 0.3, 9), z0 + 0.8, z0 + 1.5)
    mesh_rec("ствол храмового дерева", "дерево", tr)
    n0 = len(tr.parts)
    for s in (1, -1):
        root_drape(tr, s, g)
        for zz in (36.0, 39.0):  # ветви
            C.bar(cn, "trunk", (x, y, zz), (s * 13.0, y - 3.0 + 3 * g(), h + 1.0), 1.4, 1.4)
    mesh_rec("корни храмового дерева ×2", "корни", tr, n0, split=2)
    est("храм", 4)
    n0 = len(tr.parts)
    for s in (1, -1):  # храм зарос: кусты на уступах по краям
        bush(tr, s * 30.0, 43.0, 3.0, g, z=10.0)
        bush(tr, s * 24.0, 46.0, 2.6, g, z=17.5)
        bush(tr, s * 31.0, 50.0, 3.4, g, z=10.0)
    mesh_rec("кусты на уступах храма", "заросли", tr, n0)
    cl = [(0, 52, 14.0, h + 2.5), (-15, 50, 11.0, h), (15, 50, 10.0, h + 1.6), (-8, 44, 8.5, h - 2.0),
          (8, 45, 9.5, h - 0.8), (-26, 54, 9.0, h - 2.2), (26, 54, 10.0, h + 0.4)]  # разная высота — не «ряд зонтиков»
    n0 = len(cn.parts)
    vines = []
    for cx, cy, r0, h0 in cl:
        clump(cn, cx, cy, r0, h0, g, sy=0.8, hk=0.7)
        for j in range(6):
            t = 2 * math.pi * j / 6 + g()
            px, py = cx + r0 * 0.8 * math.cos(t), cy + r0 * 0.64 * math.sin(t)
            blade(cn, "folS" if j % 2 else "folD", "fol", (px, py, h0 - 0.8), math.degrees(t), 4.0 + 2.0 * g(), 2.2,
                  -30, 28, segs=3, th=0.22)
        for j in range(3):  # лианы с кроны — до крыши храма
            t = 2 * math.pi * g()
            vines.append(((cx + r0 * 0.6 * math.cos(t), cy - r0 * 0.5 * abs(math.sin(t)), h0 - 1.0), 32.0 + 3 * g()))
        est("кроны", 2)
    mesh_rec("крона храмового дерева (7 комьев)", "крона", cn, n0, split=2)
    n0 = len(cn.parts)
    for top, z_end in vines:
        liana(cn, top, z_end, g)
    mesh_rec("лианы храмового дерева (21)", "лианы", cn, n0)


# ── Болото: вода, кувшинки, рогоз, кочки, водопады ────────────────────────────────────────────────────────────
def lily_pad(a, x, y, r, turn, key):
    pts = []
    for i in range(11):
        t = math.radians(turn + 20 + i * 32)
        pts.append((x + r * math.cos(t), y + r * math.sin(t)))
    pts.append((x, y))
    a.extrude(key, pts, WATER_Z - 0.02, WATER_Z + 0.1, axis="z")


def swamp(side):
    """Болото одной стороны: вода с пятнами ряски и бликами, кочки с папоротниками и травой, кувшинки с цветами,
    рогоз, грибы; всё вне прямоугольника мостков."""
    s = side
    w = mk("Swamp" + ("R" if s > 0 else "L"))
    g = rnd(80 + (s > 0))
    xa, xb = sorted((s * WATER_X, s * HW))
    w.box("mud", xa - (0.6 if s > 0 else 0), xb + (0.6 if s < 0 else 0), Y0, Y1, FLOOR - 0.2, FLOOR + 0.08)
    w.box("water", xa, xb, Y0, Y1, FLOOR, WATER_Z)
    est("болото", 3)
    for k in range(18):  # ряска и блики (плоско)
        x, y = s * (WATER_X + 2 + (HW - WATER_X - 4) * g()), Y0 + (Y1 - Y0) * g()
        w.prism("waterD" if k % 3 else "waterL", C.ngon(x, y, 1.5 + 2.5 * g(), 7, sy=0.6 + 0.6 * g()),
                WATER_Z - 0.01, WATER_Z + 0.02, bevel=0)
    # кочки (мох и ил) с растениями
    islands = []
    # (снаружи полосы — центр |x| ≥ 73, растения не дотягиваются до полосы; в середине — |x| 39…42 вне перемычки)
    for x, y in ((s * 80.0, -36.0), (s * 76.0, -26.0), (s * 82.0, -8.0), (s * 76.5, 1.0), (s * 79.0, 21.0),
                 (s * 76.0, 30.0), (s * 77.0, 46.0), (s * 78.0, -46.0)):
        r = 3.0 + 2.0 * g()
        w.prism("mud", C.ngon(x, y, r, 9), FLOOR, WATER_Z + 0.3)
        w.prism("moss", C.ngon(x, y, r * 0.8, 9), WATER_Z + 0.3, WATER_Z + 0.7)
        islands.append((x, y, r))
        est("болото")
    for i, (x, y, r) in enumerate(islands):
        if i % 3 == 0:
            fern(w, x, y, 1.3, g)
        elif i % 3 == 1:
            tall_grass(w, x + 0.8, y, 4.5, g)
            fern(w, x - 1.2, y + 1.0, 1.0, g, keys=("folL", "fern"))
        else:
            monstera(w, x, y, 1.0, g, z=WATER_Z + 0.4)
    # кувшинки: стайки у кочек и у мостков (не под ними)
    for k in range(18):
        x, y = s * (36.0 + 52 * g()), Y0 + 4 + (Y1 - Y0 - 8) * g()
        if in_lane(x, y, 1.5):
            continue
        for j in range(3):
            lx, ly = x + 2.6 * math.cos(j * 2.2), y + 2.6 * math.sin(j * 2.2)
            lily_pad(w, lx, ly, 1.1 + 0.6 * g(), 360 * g(), "lily" if j % 2 else "lilyD")
        if k % 2 == 0:
            for j in range(5):
                tt = math.radians(j * 72)
                w.prism("petalW" if k % 4 else "flower", C.ngon(x + 0.45 * math.cos(tt), y + 0.45 * math.sin(tt),
                                                               0.4, 5), WATER_Z + 0.08, WATER_Z + 0.5)
            w.prism("petal", C.ngon(x, y, 0.3, 6), WATER_Z + 0.08, WATER_Z + 0.65)
        est("кувшинки")
    # рогоз вдоль обоих краёв мостков (вне полосы, наклон от неё) — кроме перемычки
    for y in range(int(Y0) + 5, int(Y1) - 3, 9):
        for side_out in (1, -1):
            if side_out < 0 and (abs(y - BOSS[1]) < LINK_W / 2 + 3 or y > 36):
                continue
            o = s * side_out
            x = s * LANE_X + o * (LANE_W / 2 + 2.2 + 1.5 * g())
            for j in range(4):
                xx, yy = x + o * 0.9 * math.cos(j * 1.6), y + 0.9 * math.sin(j * 1.6)
                h = 3.2 + 2.0 * g()
                C.bar(w, "reed", (xx, yy, FLOOR), (xx + o * 0.4, yy, h), 0.22, 0.22)
                if j % 2 == 0:
                    w.prism("cattail", C.ngon(xx + o * 0.4, yy, 0.32, 6), h - 1.4, h - 0.1)
            est("рогоз")
    # середина между площадкой и полосой (|x| 34…47): кочки с бананом, монстерой, папоротником и травой
    for x, y, kind in ((39.0, -40.0, "banana"), (40.5, -27.0, "monstera"), (41.5, -17.0, "fern"),
                       (41.0, 12.0, "grass"), (40.5, 24.0, "monstera"), (41.5, 36.0, "fern")):
        xx = s * x
        z = hummock(w, xx, y, 2.6)
        if kind == "banana":
            banana(w, xx, y, 8.2 + 1.5 * g(), g)  # листья выше 7.3 — над краем полосы можно
        elif kind == "monstera":
            monstera(w, xx, y, 1.0, g, z=z)
        elif kind == "fern":
            fern(w, xx, y, 1.2, g, z=z)
        else:
            tall_grass(w, xx + 0.6, y, 4.5, g, z=z)
            fern(w, xx - 1.0, y + 1.0, 1.0, g, keys=("folL", "fern"), z=z)
    # грибы-зонтики на кочках у скал — красные акценты
    for x, y in ((s * 82.0, -30.0), (s * 84.0, 40.0)):
        h = 3.0 + 2.0 * g()
        w.prism("mud", C.ngon(x, y, 2.6, 8), FLOOR, WATER_Z + 0.4)
        w.prism("petalW", C.ngon(x, y, 0.8, 8), WATER_Z + 0.4, h)
        for k, (r, z0) in enumerate(((3.2, h), (2.5, h + 0.7), (1.5, h + 1.3))):
            w.prism("mush" if k != 1 else "white", C.ngon(x, y, r, 10), z0, z0 + 0.75)
        est("болото")
    # водопад со скалы в болото
    y = 16.0
    xf = s * 87.5
    for yy, h in ((y - 8.0, 17.0), (y + 8.0, 16.0)):
        for k, (r, z0, z1) in enumerate(((4.6, FLOOR, h * 0.45), (3.8, h * 0.45 - 0.2, h * 0.8),
                                          (2.8, h * 0.8 - 0.2, h))):
            w.prism("cliff" if k % 2 == 0 else "mudD", C.ngon(s * 89.0, yy, r, 7), z0, z1)
        w.prism("moss", C.ngon(s * 89.0, yy, 3.0, 7), h - 0.1, h + 0.6)
    w.box("water", xf - s * 0.2, xf + s * 1.6, y - 4.8, y + 4.8, WATER_Z, 15.4, bevel=0)
    for k in range(6):
        yy = y - 3.8 + 1.5 * k
        w.box("waterL", xf - s * 0.35, xf - s * 0.18, yy - 0.25, yy + 0.25, 1.0 + (k % 3) * 1.4, 14.8 - (k % 2) * 2,
              bevel=0)
    for k in range(5):
        t = 2 * math.pi * k / 5
        w.prism("petalW", C.ngon(xf - s * 2.0 + 1.6 * math.cos(t), y + 2.4 * math.sin(t), 0.8, 6), WATER_Z,
                WATER_Z + 0.5)
    est("болото", 4)
    mesh_rec("болото " + ("R" if s > 0 else "L") + ": вода, кочки, кувшинки, рогоз, водопад", "болото", w, split=3)


def inner_water():
    """Площадка — остров: всё внутри, что не площадка, не храм и не путь, — мелкая вода с ряской и кувшинками;
    у входа — кочки (на них растения рамки). В круге боя только плоское (≤ 0.7)."""
    w = mk("InnerWater")
    g = rnd(55)
    w.box("water", -WATER_X, WATER_X, Y0, Y1, FLOOR, WATER_Z)
    est("болото", 1)

    def free_spot(x, y, r):
        return (math.hypot(x - BOSS[0], y - BOSS[1]) > A.PLAT_R + 1.6 + r and not in_lane(x, y, r + 0.6)
                and y < 30.0 - r and abs(x) < WATER_X - r)

    for k in range(70):  # ряска и блики
        x, y = (2 * g() - 1) * WATER_X, Y0 + (32.0 - Y0) * g()
        r = 1.0 + 1.8 * g()
        if free_spot(x, y, r * 0.6):
            w.prism("waterD" if k % 3 else "waterL", C.ngon(x, y, r, 7, sy=0.6 + 0.5 * g()), WATER_Z - 0.01,
                    WATER_Z + 0.02, bevel=0)
    n = 0
    for k in range(160):  # кувшинки стайками
        x, y = (2 * g() - 1) * WATER_X, Y0 + 2 + (31.0 - Y0) * g()
        if n >= 26 or not free_spot(x, y, 2.4):
            continue
        for j in range(3):
            lx, ly = x + 1.6 * math.cos(j * 2.2 + k), y + 1.6 * math.sin(j * 2.2 + k)
            lily_pad(w, lx, ly, 0.8 + 0.5 * g(), 360 * g(), "lily" if j % 2 else "lilyD")
        if n % 2 == 0:
            for j in range(5):
                tt = math.radians(j * 72)
                w.prism("petalW" if n % 4 else "flower", C.ngon(x + 0.4 * math.cos(tt), y + 0.4 * math.sin(tt),
                                                               0.36, 5), WATER_Z + 0.08, WATER_Z + 0.45)
            w.prism("petal", C.ngon(x, y, 0.28, 6), WATER_Z + 0.08, WATER_Z + 0.6)
        n += 1
        est("кувшинки", 0.5)
    mesh_rec("вода у острова, ряска, кувшинки", "болото", w)


# ── Деревья-великаны и кроны над дорожками ────────────────────────────────────────────────────────────────────
DOME = ((0.48, -0.46, -0.2, "folS"), (0.76, -0.28, 0.02, "folS"), (0.95, -0.1, 0.24, "folD"), (1.0, 0.16, 0.42, "fol"),
        (0.84, 0.36, 0.6, "fol"), (0.6, 0.55, 0.78, "folL"), (0.34, 0.74, 0.92, "folL"))
# ярусы кома: (радиус, низ, верх) в долях радиуса — снизу ступенями сужается (круглое дно, не «зонтик»)
DARK = {"folL": "fol", "fol": "folD", "folD": "folS", "folS": "folS"}  # дальние кроны — темнее, без светлой макушки


def clump(cn, x0, y0, r0, h0, g, sy=0.85, hk=0.62, light=True, dark=False, lobes=3):
    """Ком листвы — неровная груда из нескольких ступенчатых «облаков» разного размера и высоты: ярусы сдвинуты,
    многоугольники разной формы и поворота — край рваный, не «зонтик». Низ тёмный и опущен; светлая макушка
    (folY) — только у ближних комьев."""
    parts = [(0.0, 0.0, 1.0, 0.0)]
    a0 = 2 * math.pi * g()
    for k in range(lobes - 1):
        t = a0 + k * (2.2 + 0.8 * g())
        parts.append((0.5 * math.cos(t), 0.5 * math.sin(t), 0.6 + 0.2 * g(), (g() - 0.65) * 0.6))
    for li, (ux, uy, ur, dz) in enumerate(parts):
        r1 = r0 * ur
        cx, cy = x0 + ux * r0, y0 + uy * r0 * sy
        hh = r1 * hk * 1.3  # высота кома над серединой
        hz = h0 + dz * r0 * hk
        sy1 = sy * (0.85 + 0.3 * g())
        for rr, z0, z1, key in DOME:
            key = DARK[key] if dark else key
            ox, oy = (g() - 0.5) * 0.24 * r1, (g() - 0.5) * 0.24 * r1 * sy
            za = hz + (z0 * r1 * 0.8 if z0 < 0 else z0 * hh)
            zb = hz + (z1 * r1 * 0.8 if z1 < 0 else z1 * hh)
            cn.prism(key, C.ngon(cx + ox, cy + oy, r1 * rr * (0.92 + 0.16 * g()), 7 + int(4 * g()),
                                 phase=2 * math.pi * g(), sy=sy1), za - 0.05, zb)
        if light and not dark and li == 0:
            cn.prism("folY", C.ngon(cx + (g() - 0.5) * 0.2 * r1, cy, r1 * 0.2, 7, phase=g()), hz + 0.9 * hh,
                     hz + 1.0 * hh)


def tree(tr, cn, x, y, h, crown, g, light=True, dark=False, vine_min=2.0, vines=None, label="", roots=True,
         rim=True, branches=True, fringe=1.0, bloom=True):
    """Дерево джунглей: ступенчатый ствол с досковидными корнями и мхом, ветви к кроне; крона — неровная груда
    комьев разной высоты с тёмной опущенной бахромой и поникшими листьями по краю; лианы с кроны (над путями и
    кругом боя — до z ≥ 10.8). crown = (cx, cy, r, sy) — крона смещена к дорожке и нависает над ней.
    dark — дальнее дерево: темнее, без светлых макушек."""
    cx, cy, cr, sy = crown
    lean = Vector((cx - x, cy - y, 0)) * 0.08
    secs = ((2.6, FLOOR - 0.1, h * 0.3), (2.2, h * 0.3 - 0.1, h * 0.55), (1.8, h * 0.55 - 0.1, h * 0.8),
            (1.5, h * 0.8 - 0.1, h + 0.5))
    n0 = len(tr.parts)
    for k, (r, z0, z1) in enumerate(secs):
        ox, oy = lean.x * k, lean.y * k
        tr.prism("trunk" if k % 2 == 0 else "bark", C.ngon(x + ox, y + oy, r, 8), z0, z1)
        if k in (1, 2):
            tr.prism("moss", C.ngon(x + ox, y + oy, r + 0.25, 8), z0 + 0.6, z0 + 1.2)
    if roots:
        for k in range(4):  # корни-доски: от ствола расходятся и уходят в воду
            t = math.radians(30 + 90 * k + 25 * g())
            C.bar(tr, "trunkD", (x + 4.6 * math.cos(t), y + 4.6 * math.sin(t), FLOOR), (x + 1.4 * math.cos(t),
                                                                                         y + 1.4 * math.sin(t), 4.6),
                  0.7, 2.0)
    top = Vector((x + lean.x * 3, y + lean.y * 3, h * 0.95))
    for k in range(3 if branches else 0):  # ветви
        t = math.radians(120 * k + 60 * g())
        end = Vector((cx + cr * 0.45 * math.cos(t), cy + cr * 0.45 * sy * math.sin(t), h + 0.6))
        C.bar(tr, "trunk", top - Vector((0, 0, 2)), end, 1.0, 1.0)
    mesh_rec("ствол " + label, "дерево", tr, n0)
    est("деревья", 1)
    # крона: центральный ком и 3 вокруг на разной высоте; каждый — неровная груда ярусов
    n0 = len(cn.parts)
    cl = [(0.0, 0.0, 0.58, 1.6, 3)] + [(0.5 * math.cos(t), 0.5 * math.sin(t), 0.44 + 0.1 * g(), dz, 2) for t, dz in
                                       ((0.3 + g(), -0.2), (2.4 + g(), 1.0), (4.3 + g(), -0.7))]
    for ux, uy, ur, dz, lobes in cl:
        x0, y0, r0, h0 = cx + ux * cr, cy + uy * cr * sy, ur * cr, h + dz
        clump(cn, x0, y0, r0, h0, g, sy=sy * 0.95 + 0.05, light=light, dark=dark, lobes=lobes)
        nf = 3 if dark else 4
        for j in range(nf):  # бахрома: тёмные листья свисают из-под кома (у дальних тёмных деревьев — 3)
            t = 2 * math.pi * j / nf + g()
            px, py = x0 + r0 * 0.75 * math.cos(t), y0 + r0 * 0.75 * sy * math.sin(t)
            blade(cn, "folS" if j % 2 else "folD", None, (px, py, h0 - 0.4), math.degrees(t),
                  (3.0 + 1.6 * g()) * fringe, 1.8 * fringe, -40, 28, segs=2, th=0.2)
    n = (max(6, int(cr * 0.55)) if dark else max(7, int(cr * 0.7))) if rim else 0
    for k in range(n):  # поникшие листья по краю — рваный край
        t = 2 * math.pi * k / n + 0.3 * g()
        rr = cr * (0.82 + 0.2 * g())
        px, py = cx + rr * math.cos(t), cy + rr * sy * math.sin(t)
        blade(cn, ("folD" if k % 2 else "fol") if not dark else "folS", None if dark else "folL",
              (px, py, h + 0.2 + 1.2 * g()), math.degrees(t), 4.0 + 2.5 * g(), 2.2, -12, 30, segs=3, th=0.22)
    mesh_rec("крона " + label, "крона", cn, n0)
    est("кроны", 1)
    # лианы с кроны
    n0 = len(cn.parts)
    for k in range(int(cr * 0.7) if vines is None else vines):
        t = 2 * math.pi * g()
        rr = cr * (0.35 + 0.55 * g())
        px, py = cx + rr * math.cos(t), cy + rr * sy * math.sin(t)
        over = in_lane(px, py, 1.5) or in_exit(px, py, 1.5) or near_fight(px, py, 2.0)
        z_end = 10.8 + 2.0 * g() if over else max(vine_min, 2.0) + 6.0 * g()
        liana(cn, (px, py, h - 0.6), z_end, g, bloom=bloom and g() > 0.75)
    if len(cn.parts) > n0:
        mesh_rec("лианы " + label, "лианы", cn, n0)


def banana(a, x, y, h, g):
    """Банан: ствол из звеньев и 6 огромных листьев со светлой жилкой: 4 звена, сужаются к концу и поникают дугой
    (не «доски»)."""
    C.bar(a, "fern", (x, y, FLOOR), (x, y, h * 0.6), 0.9, 0.9)
    C.bar(a, "folL", (x, y, h * 0.6 - 0.2), (x, y, h), 0.7, 0.7)
    for k in range(6):
        blade(a, "fol" if k % 2 else "folL", "folY", (x, y, h - 0.3), k * 60 + 20 * g(), 7.0, 2.3, 50 + 8 * g(), 30,
              segs=4, th=0.2, taper=0.24)
    est("бананы")


def bush(a, x, y, r, g, z=FLOOR, dark=False):
    """Куст: ступенчатые ярусы листвы из воды (сдвинуты, разной формы), сверху — листья веером."""
    keys = ("folS", "folD", "fol") if dark else ("folD", "fol", "folL")
    for k, (rr, z0, z1) in enumerate(((1.0, 0.0, 1.9), (0.8, 1.7, 3.5), (0.5, 3.3, 4.5))):
        a.prism(keys[k], C.ngon(x + 0.3 * k * (g() - 0.3), y + 0.3 * (g() - 0.5), r * rr, 7 + int(3 * g()),
                                phase=6.28 * g()), z + z0, z + z1 + r * 0.3)
    for k in range(4):
        blade(a, keys[2] if k % 2 else keys[1], None, (x, y, z + 3.3 + r * 0.3), k * 90 + 30 * g(), 3.5, 1.6, 40, 35,
              segs=2, th=0.2)
    est("заросли")


def jungle(side):
    """Деревья-великаны одной стороны: ряд снаружи полосы (стволы |x| 71.5…73, кроны нависают над мостками выше 7,
    слиты комьями-перемычками), дерево у входа (крона — рамка верхнего угла кадра игрока), великан за храмом (в
    середине), стена деревьев у скал (стволы и всё твёрдое ниже 24, кроны выше — листва без столкновений)."""
    s = side
    sd = "R" if s > 0 else "L"
    tr = mk("Trees" + sd)
    cn = mk("Canopy" + sd)
    g = rnd(90 + (s > 0))
    # ряд снаружи полосы: ствол с корнями не ближе 66.5 и не дальше 75.6 (не «у стены»), крона над полосой
    row = ((-44.0, 22.0, 13.0), (-17.0, 25.0, 14.0), (10.0, 23.0, 13.5), (37.0, 26.0, 14.0))
    for y, h, r in row:
        x = s * (71.5 + 1.5 * g())
        cx = s * (62.0 - 0.3 * r + 1.5 * g())
        tree(tr, cn, x, y, h, (cx, y + 2.0 * g(), r, 0.8), g, vines=int(r * 0.5), label=f"{sd} у мостков y {y:.0f}")
    # комья-перемычки между кронами ряда: сплошная масса листвы над полосой
    n0 = len(cn.parts)
    for (ya, ha, _), (yb, hb, _) in zip(row, row[1:]):
        ym, hm = (ya + yb) / 2, (ha + hb) / 2 + 1.0
        clump(cn, s * 60.0, ym, 9.0, hm, g, sy=0.9, lobes=2)
        for j in range(4):
            t = 2 * math.pi * j / 4 + g()
            blade(cn, "folS" if j % 2 else "folD", None, (s * 60.0 + 6.5 * math.cos(t), ym + 6.0 * math.sin(t),
                                                          hm - 0.5), math.degrees(t), 3.6, 1.9, -35, 28, segs=2)
        est("кроны")
    mesh_rec(f"кроны-перемычки {sd} ×3", "крона", cn, n0)
    # у входа: ствол вне кадра, низкая крона входит в верхний угол кадра игрока; вне круга боя
    tree(tr, cn, s * 24.0, -58.0, 17.5, (s * 16.5, -48.5, 9.0, 0.8), g, vine_min=8.5, vines=6, rim=False,
         branches=False, fringe=0.6, bloom=False, label=f"{sd} у входа (рамка)")
    # за храмом — великан в середине (ствол |x| 40, корни до 45), крона закрывает небо за уступами
    tree(tr, cn, s * 40.0, 50.0, 32.0, (s * 30.0, 51.0, 17.0, 0.75), g, vines=6, label=f"{sd} великан за храмом")
    # бананы и кусты снаружи полосы — средний ярус зелени (листья не дотягиваются до полосы ниже 7)
    n0 = len(tr.parts)
    for y in (-31.0, -4.0, 23.0, 46.0):
        banana(tr, s * (75.0 + 2.0 * g()), y + 3.0 * g(), 7.0 + 2.0 * g(), g)
    for y in (-48.0, -24.0, -10.0, 4.0, 17.0, 31.0):
        r = 2.5 + 1.5 * g()
        bush(tr, s * max(76.0 + 10.0 * g(), 66.6 + r + 3.0), y + 2.0 * g(), r, g)
    mesh_rec(f"бананы и кусты {sd}", "заросли", tr, n0)
    # стена у скал: стволы ниже 24 (у стены твёрдое не выше 24), кроны внахлёст выше — тёмные, без столкновений
    cn = mk("CanopyWall" + sd)
    for y, h in ((-30.0, 21.0), (-4.0, 22.5), (24.0, 20.5), (48.0, 22.0)):  # ветви — до h + 1.1
        x = s * (85.0 + 2.0 * g())
        tree(tr, cn, x, y, h, (s * 80.0, y, 13.0, 1.0), g, light=False, dark=True, vines=3,
             label=f"{sd} у скал y {y:.0f}")
    # кусты-заросли у скальной стены (закрывают обрыв)
    n0 = len(cn.parts)
    y = Y0
    i = 0
    while y < Y1:
        r = 3.0 + 2.0 * g()
        if abs(y - 16) > 12:
            cn.prism("folS" if i % 2 else "folD", C.ngon(s * 90.0, y, r, 8, phase=g()), FLOOR, 4.0 + 3.0 * g())
            cn.prism("fol", C.ngon(s * 90.0, y, r * 0.6, 7, phase=g()), 3.5, 5.5 + 2.0 * g())
            est("заросли", 0.5)
        y += r * 1.6
        i += 1
    # гирлянды лиан между кронами над полосой (высоко)
    xs = s * LANE_X
    for y0, y1 in ((-38.0, -14.0), (-12.0, 12.0), (14.0, 38.0)):
        drape(cn, (xs + s * 4.0, y0, 21.0), (xs - s * 1.0, y1, 22.0), 5.5, g)
    mesh_rec(f"заросли у скал и гирлянды лиан {sd}", "заросли", cn, n0)


def back_wall(side):
    """Сплошная тёмная стена джунглей за храмом и по его бокам (y 44…72): деревья с кронами внахлёст, под ними
    заросли до z ~8 — ниже линии крон неба нет. Полоса (|x| 48…66) свободна: заросли в середине (|x| 18…47) и снаружи
    (|x| 67…90), над полосой — только кроны выше 7."""
    s = side
    sd = "R" if s > 0 else "L"
    tr = mk("BackTrees" + sd)
    cn = mk("BackCanopy" + sd)
    g = rnd(120 + (s > 0))
    trees_ = ((s * 25.0, 60.0, 20.0, (s * 27.0, 57.0, 10.5, 0.8)), (s * 42.0, 62.0, 22.0, (s * 47.0, 58.0, 11.0, 0.8)),
              (s * 30.5, 70.0, 25.0, (s * 40.0, 66.0, 12.0, 0.8)), (s * 73.0, 64.0, 23.0, (s * 64.0, 61.0, 12.0, 0.8)))
    for x, y, h, crown in trees_:
        tree(tr, cn, x, y, h, crown, g, light=False, vines=3, label=f"{sd} за храмом ({abs(x):.0f}, {y:.0f})")
    n0 = len(tr.parts)
    for xa, xb in ((18.0, 47.0), (67.0, 90.0)):  # заросли до z ~8: листья куста (r + 3) не заходят в полосу
        y = 44.0 if xa > 40 else 47.0
        while y < 72.0:
            r = 2.4 + 1.2 * g()
            x = xa + r + (xb - xa - 2 * r) * g()
            x = min(x, LANE_IN - 0.6 - r - 3.0) if xb < 50 else max(x, LANE_OUT + 0.6 + r + 3.0)
            bush(tr, s * x, y, r, g, dark=True)
            y += 2.9 + 1.4 * g()
    mesh_rec(f"заросли за храмом {sd}", "заросли", tr, n0)


def exit_tunnel(side):
    """Выход дорожки: мостки продолжаются за край зоны (y 53.5 → 74) в зелёный туннель — арка из корней (низ
    ≥ 11 над настилом), по бокам заросли, над ней кроны; дальше — тёмная стена леса (не небо)."""
    s = side
    sd = "R" if s > 0 else "L"
    a = mk("Exit" + sd)
    g = rnd(140 + (s > 0))
    xa, xb = sorted((s * (LANE_X - LANE_W / 2), s * (LANE_X + LANE_W / 2)))
    deck(a, xa, xb, Y1, 74.0, g, s * (LANE_OUT + 0.35))
    ya = 57.0
    for xp in (xa - 2.6, xb + 2.6):  # корни-столбы арки — вне полосы
        for k, (r, z0, z1) in enumerate(((2.0, FLOOR, 4.5), (1.7, 4.4, 8.5), (1.45, 8.4, 12.6))):
            a.prism("trunk" if k % 2 == 0 else "bark", C.ngon(xp, ya, r, 8, phase=0.3 * k), z0, z1)
        a.prism("moss", C.ngon(xp, ya, 1.95, 8), 5.0, 5.7)
        sx = -1.0 if xp < xa else 1.0
        C.bar(a, "trunkD", (xp, ya - 0.4, FLOOR + 0.2), (xp + sx * 2.2, ya - 2.8, FLOOR), 1.0, 0.9)
    a.box("trunk", xa - 3.5, xb + 3.5, ya - 1.2, ya + 1.2, 12.4, 14.0)  # перемычка арки
    a.box("trunkD", xa - 2.9, xb + 2.9, ya - 1.0, ya + 1.0, 14.0, 14.8)
    a.box("moss", xa - 2.3, xb + 2.1, ya - 1.5, ya + 0.9, 14.6, 15.2)
    for k in range(8):  # лианы-занавес с арки (низ ≥ 11)
        x = xa - 1.0 + (xb - xa + 2.0) * (k + 0.5) / 8
        liana(a, (x, ya - 1.3, 12.6), 11.0 + 1.5 * g(), g, bloom=k % 3 == 0)
    for x0 in (xa - 6.5, xb + 6.5):  # заросли по бокам туннеля (листья не заходят в полосу)
        y = 59.0
        while y < 76.0:
            bush(a, x0 + (g() - 0.5) * 1.2, y, 2.4 + g(), g, dark=True)
            y += 3.0 + g()
    for y, h0 in ((63.0, 21.0), (72.0, 19.0)):  # кроны-потолок туннеля (низ ≥ 12)
        clump(a, s * LANE_X, y, 11.0, h0, g, sy=0.8, dark=True, light=False, lobes=3)
    mesh_rec(f"выход-туннель {sd}: мостки, арка, заросли, кроны", "рамка", a, split=2)


def forest_backdrop():
    """Дальняя стена леса за зоной (y 78…92): тёмные груды крон от воды до z ~38 и стволы в просветах; под дымкой
    светлеет и зеленеет — глубина, а не небо за храмом и в конце дорожек."""
    a = mk("Backdrop")
    g = rnd(150)
    a.box("water", -HW - 20, HW + 20, Y1, 96.0, -1.0, WATER_Z)
    # сплошной тёмный задник за грудами крон до z 24 (прячется под верхним рядом комьев): без него между
    # нижним и средним рядом просвечивало небо — светлые «дыры» в кадре игрока и в конце туннеля полосы
    a.box("folS", -HW - 20, HW + 20, 92.0, 94.0, WATER_Z - 0.1, 24.0)
    x = -HW - 14.0
    while x < HW + 14.0:
        y = 82.0 + 4.0 * g()
        C.bar(a, "trunkD", (x + 3.0, y + 2.0, FLOOR), (x + 3.0, y + 2.0, 30.0), 2.4, 2.4)
        clump(a, x, y, 9.0 + 2.0 * g(), 3.0 + 2.0 * g(), g, sy=0.7, dark=True, light=False, lobes=1)
        clump(a, x + 6.0, y + 2.0, 10.0 + 2.0 * g(), 14.0 + 4.0 * g(), g, sy=0.7, dark=True, light=False, lobes=1)
        clump(a, x - 2.0, y + 5.0, 12.0 + 2.0 * g(), 26.0 + 6.0 * g(), g, sy=0.7, dark=True, light=False, lobes=1)
        x += 15.0 + 3.0 * g()
    est("земля и обрывы", 2)
    mesh_rec("дальний лес за зоной", "рамка", a, split=4)


def hummock(f, x, y, r):
    """Кочка в воде под растением рамки; возвращает высоту её верха."""
    f.prism("mud", C.ngon(x, y, r, 8, phase=0.2), FLOOR - 0.05, WATER_Z + 0.35)
    f.prism("moss", C.ngon(x, y, r * 0.82, 8, phase=0.4), WATER_Z + 0.3, WATER_Z + 0.75)
    return WATER_Z + 0.7


def entry_frame():
    """Рамка у входа на кочках в воде: высокая трава, папоротники, монстеры и цветы между центральным путём и
    мостками, вне круга боя. Ближе к камере игрока — крупные листья и пучки травы, входящие в нижние углы кадра;
    листья только наружу от пути (путь ±6 свободен). У храма — монстеры по углам."""
    f = mk("Frame")
    g = rnd(33)
    for s in (1, -1):

        def out(lo, hi, s=s):  # сектор углов «наружу» для этой стороны (0° — +x)
            return (lo, hi) if s > 0 else (180 - hi, 180 - lo)

        for x, y, kind in ((22, -50, "monstera"), (27.5, -46, "grass"), (29, -52, "fern"), (25, -40.5, "flower"),
                           (29.5, -38, "grass"), (19, -55.5, "grass")):
            xx = s * x
            z = hummock(f, xx, y, 2.4)
            if kind == "fern":
                fern(f, xx, y, 1.4, g, z=z)
            elif kind == "monstera":
                monstera(f, xx, y, 1.25, g, z=z)
            elif kind == "grass":
                tall_grass(f, xx, y, 4.5 + 1.5 * g(), g, z=z)
            else:
                hh = 3.5 + 1.5 * g()
                C.bar(f, "fern", (xx, y, z), (xx + 0.4, y, hh), 0.5, 0.5)
                blade(f, "folL", None, (xx + 0.2, y, hh * 0.4), 0 if s > 0 else 180, 2.4, 1.1, 30, 30, segs=2)
                flower(f, xx + 0.4, y, hh, 1.8, g, key="flower" if g() > 0.4 else "orange")
                est("цветы")
        # крупная рамка нижних углов кадра игрока (камера (0, −68, 10.5)): листья поднимаются до z 7…10
        z = hummock(f, s * 11.5, -47.5, 2.6) + 0.4
        monstera(f, s * 11.5, -47.5, 1.7, g, z=z, yaws=out(-35, 85), n=5, pitch=50)
        z = hummock(f, s * 15.5, -43.5, 2.4)
        fern(f, s * 15.5, -43.5, 1.8, g, z=z, yaws=out(-40, 110), n=7)
        z = hummock(f, s * 8.6, -50.0, 1.8)
        tall_grass(f, s * 8.6, -50.0, 8.5, g, z=z, yaws=out(-60, 75), n=9, w=0.5)
        z = hummock(f, s * 18.0, -50.5, 2.0)
        tall_grass(f, s * 18.0, -50.5, 7.5, g, z=z, n=8, w=0.5)
        banana(f, s * 22.0, -43.0, 8.5, g)
        # монстеры у углов храма
        monstera(f, s * 29.0, 29.5, 1.1, g)
        fern(f, s * 23.0, 30.0, 1.1, g)
    mesh_rec("рамка у входа: трава, папоротники, монстеры, кочки", "рамка", f, split=2)


def signs():
    """Указатели «В БАНК» — на столбе в болоте сбоку от мостков (не на них); текст — в игре."""
    s = mk("Signs")
    for sx in (1, -1):
        x = sx * (LANE_OUT + 3.6)  # табличка 66.9…71.7 — вне полосы
        s.box("post", x - 0.3, x + 0.3, 38.0, 38.6, FLOOR, 4.5)
        s.box("path", x - 2.4, x + 2.4, 37.9, 38.2, 3.2, 4.6)
        est("таблички", 2)


# ── Проверки ──────────────────────────────────────────────────────────────────────────────────────────────────
SKIP_CHECK = ("Ground", "Platform")  # пол и обрывы каркаса, площадка (настил путей проверяется: он ниже 1.1)
TOL = 0.2  # допуск касания краёв прямоугольника (рамки деталей с наклоном шире самой детали)


def is_foliage(name):
    return name.startswith(FOLIAGE)


def check_free(arts):
    """Проверки D66 по рамкам деталей (с запасом: рамка наклонной детали шире её самой):
    - lanes: в прямоугольниках путей (полосы |x| 48–66 на всю длину, перемычки, центральный путь) нет ни одной детали
      — ни твёрдой, ни листвы, ни лианы — в слое 1.1–7 над полом зоны (LANE_Z);
    - wall: у стен (рамка заходит за |x| 76) твёрдое не выше 24; листва (FOLIAGE) выше 24 — без столкновений, считается
      отдельно;
    - fight: круг боя r 34 — ничего выше 2 над полом, кроме бордюра площадки.
    - exit: продолжение полос за выходом (туннель, y Y1…EXIT_Y) — тот же слой 1.1–7 свободен;
    Детали за пределами зоны по длине (выход-туннель, дальний лес за y > Y1) в проверку стен не входят."""
    bad, wall, fight, ext = [], [], [], []
    leafy = {"parts": 0, "tris": 0, "arts": set()}
    for a in arts:
        if a.name in SKIP_CHECK:
            continue
        leaf = is_foliage(a.name)
        for bm, _key, _solid, _grp in a.parts:
            xs = [v.co.x for v in bm.verts]
            ys = [v.co.y for v in bm.verts]
            zs = [v.co.z for v in bm.verts]
            lo, hi = min(zs), max(zs)
            box = (a.name, round(min(xs), 1), round(max(xs), 1), round(min(ys), 1), round(max(ys), 1), round(lo, 1),
                   round(hi, 1))
            for x0, x1, y0, y1, _fl in FREE:
                if min(xs) < x1 - TOL and max(xs) > x0 + TOL and min(ys) < y1 - TOL and max(ys) > y0 + TOL:
                    if lo < LANE_Z[1] and hi > LANE_Z[0]:
                        bad.append(box)
                        break
            for x0, x1, y0, y1, _fl in EXIT_FREE:
                if min(xs) < x1 - TOL and max(xs) > x0 + TOL and min(ys) < y1 - TOL and max(ys) > y0 + TOL:
                    if lo < LANE_Z[1] and hi > LANE_Z[0]:
                        ext.append(box)
                        break
            in_zone = min(ys) < Y1 and max(ys) > Y0
            if in_zone and max(abs(min(xs)), abs(max(xs))) > WALL_X and hi > WALL_TOP:
                if leaf:
                    leafy["parts"] += 1
                    leafy["tris"] += sum(len(f.verts) - 2 for f in bm.faces)
                    leafy["arts"].add(a.name)
                elif a.name != "Backdrop":
                    wall.append(box)
            if hi > FLOOR + 2.0 and a.name != "Border":
                nx = min(max(BOSS[0], min(xs)), max(xs))
                ny = min(max(BOSS[1], min(ys)), max(ys))
                if math.hypot(nx - BOSS[0], ny - BOSS[1]) < FIGHT_R - 0.3:
                    fight.append(box[:5] + (box[6],))
    leafy["arts"] = sorted(leafy["arts"])
    return bad, wall, fight, ext, leafy


def overlay():
    """Схема сверху: круг боя r 34 (белый пунктир), места существ (красные), свободные пути — полосы |x| 48–66,
    перемычки, центральный путь (зелёные контуры), граница «у стен» |x| 76 (жёлтый пунктир: дальше твёрдое ≤ 24)."""
    o = C.new_art("Overlay")
    o.paint("neonW", "FFFFFF")
    o.paint("neonR", "FF3048")
    o.paint("neonG", "3DFF7A")
    o.paint("neonY", "FFD400")
    for s_ in (1, -1):
        y = -HL
        while y < HL:
            C.bar(o, "neonY", (s_ * WALL_X, y, 3.0), (s_ * WALL_X, min(y + 4.0, HL), 3.0), 0.7, 0.1, bevel=0)
            y += 8.0
    for i in range(36):
        if i % 2 == 0:
            t0, t1 = math.radians(i * 10), math.radians(i * 10 + 10)
            C.bar(o, "neonW", (BOSS[0] + FIGHT_R * math.cos(t0), BOSS[1] + FIGHT_R * math.sin(t0), 3.0),
                  (BOSS[0] + FIGHT_R * math.cos(t1), BOSS[1] + FIGHT_R * math.sin(t1), 3.0), 0.7, 0.1, bevel=0)
    for x, y in A.SLOTS:
        o.frame("neonR", C.ngon(x, y, 3.6, 12), 0.6, 3.0, 3.1, axis="z")
    for x0, x1, y0, y1, _ in FREE + EXIT_FREE:  # контуры ровно по прямоугольникам проверки (и продолжение за выходом)
        o.frame("neonG", [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 0.6, 3.0, 3.1, axis="z")
    return o


# ── Свет и дымка ──────────────────────────────────────────────────────────────────────────────────────────────
def sky(top, mid, bottom):
    """Небо: три цвета по высоте взгляда (у горизонта — тёплая дымка, выше — бирюза)."""
    nt = bpy.context.scene.world.node_tree
    ramp = next(n for n in nt.nodes if n.type == "VALTORGB")
    els = ramp.color_ramp.elements
    els[0].position, els[1].position = 0.0, 0.42  # Generated у мира: z = синус угла над горизонтом
    els[0].color, els[1].color = (*C.S.lin(bottom), 1), (*C.S.lin(top), 1)
    e = els.new(0.12)
    e.color = (*C.S.lin(mid), 1)


def haze(col, density):
    """Лёгкая зеленоватая дымка: рассеивающий объём в коробках (объём мира в EEVEE гасит солнце целиком). Дымка
    начинается за храмом (y ≥ 40) и по бокам дальше |x| 68 (снаружи полос): королева, храм и передний план чистые, а лес за ними
    светлее и зеленее — глубина. Коробки не пересекаются (плотность не складывается)."""
    scene = bpy.context.scene
    boxes = ((-HW - 40, HW + 40, 40.0, Y1 + 60), (68.0, HW + 40, Y0 - 40, 40.0), (-HW - 40, -68.0, Y0 - 40, 40.0))
    mat = bpy.data.materials.new("HazeVol")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    vs = nt.nodes.new("ShaderNodeVolumeScatter")
    vs.inputs["Color"].default_value = (0.55, 1.0, 0.5, 1)
    vs.inputs["Density"].default_value = density
    vs.inputs["Anisotropy"].default_value = 0.3
    nt.links.new(vs.outputs[0], out.inputs["Volume"])
    obs = []
    for i, (x0, x1, y0, y1) in enumerate(boxes):
        z0, z1 = -2.0, 70.0
        me = bpy.data.meshes.new(f"Haze{i}")
        vs_ = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        me.from_pydata(vs_, [], [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
        me.materials.append(mat)
        ob = bpy.data.objects.new(f"Haze{i}", me)
        col.objects.link(ob)
        obs.append(ob)
    for attr, val in (("volumetric_end", 260.0), ("volumetric_tile_size", "8"), ("volumetric_samples", 64),
                      ("use_volumetric_shadows", True), ("volumetric_light_clamp", 0.0)):
        try:
            setattr(scene.eevee, attr, val)
        except (AttributeError, TypeError):
            pass
    return obs


def queen_scale(out):
    try:
        with open(os.path.join(out, "stats.json"), encoding="utf-8") as f:
            return float(json.load(f).get("export_scale", QUEEN_SCALE))
    except (OSError, ValueError):
        return QUEEN_SCALE


def game_queen(col, k, pose_name):
    """Игровая королева (быстрая сборка без карт, цвета палитры) в позе pose_name на месте босса."""
    from mathutils import Matrix

    sys.path.insert(0, os.path.dirname(HERE_DIR))
    import boss6_flytrap as Q  # noqa: E402

    Q.rest_frames()
    parts, tris = {}, 0
    for m in ("Head", "Body", "Limbs"):
        a = Q.build(m)
        obj = a.build(col)
        tris += a.stats["tris"]
        parts.update(Q._split_keep(obj, a, col))
    W = Q.pose_world(Q.POSES[pose_name])
    place = Matrix.Translation((BOSS[0], BOSS[1], 0.58)) @ Matrix.Scale(k, 4)
    for n, o in parts.items():
        o.matrix_world = place @ W[n] @ Q.T(Q.PIVOTS[n])
    bpy.context.view_layer.update()
    return {"tris": tris, "scale": k, "model": "game", "pose": pose_name}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    repo = os.path.abspath(argv[0])
    quick = "quick" in argv[1:]
    opts = dict(a.split("=", 1) for a in argv[1:] if "=" in a)
    views = next((a.split(",") for a in argv[1:] if a != "quick" and "=" not in a),
                 ["player", "approach", "lane", "top"])
    out = os.path.join(repo, "assets", "concepts", "bosses_5_10", "boss6_v2", "raw")
    os.makedirs(out, exist_ok=True)
    k_queen = queen_scale(out)
    if "out" in opts:  # свои кадры (например, игровая королева на арене) — в другую папку
        out = os.path.abspath(opts["out"])
        os.makedirs(out, exist_ok=True)

    A.ARTS.clear()
    A.EXIT_PATHS[:] = []  # свои пути: мостки насквозь (lanes), без диагоналей каркаса
    A.ENTRY_PATHS[:] = []
    FREE.clear()
    EXIT_FREE.clear()
    GAME.clear()
    col = C.reset_scene()
    cam = C.outdoor("6FB9C4", "F1E3AE", (1.0, 0.86, 0.64), 4.3, (50, 0, -32), 0.62)
    bpy.context.scene.view_settings.exposure = -0.05
    sky("5BB8D0", "B5E0C8", "EEF0C2")
    hz = haze(col, float(opts.get("haze", HAZE)))
    if quick:
        bpy.context.scene.eevee.taa_render_samples = 12
    A.frame_zone(theme(), col)
    est("земля и обрывы", 6)
    lanes()
    mossy_border()
    temple()
    temple_tree()
    inner_water()
    for s in (1, -1):
        swamp(s)
        jungle(s)
        back_wall(s)
        exit_tunnel(s)
    forest_backdrop()
    entry_frame()
    signs()
    bad, wall, fight, ext, leafy = check_free(A.ARTS)
    print("FREE_LANES", "ok" if not bad else f"FAIL {len(bad)}: {bad[:20]}", flush=True)
    print("FREE_LANES exit_lanes", "ok" if not ext else f"FAIL {len(ext)}: {ext[:20]}", flush=True)
    print("FREE_LANES walls_24", "ok" if not wall else f"FAIL {len(wall)}: {wall[:20]}", flush=True)
    print("FREE_LANES fight_r34", "ok" if not fight else f"FAIL {len(fight)}: {fight[:12]}", flush=True)
    print("FREE_LANES foliage_above_24_nonsolid", leafy, flush=True)
    tris, prims = {}, {}
    objs = {}
    for a in A.ARTS:
        prims[a.name] = len(a.parts)
        objs[a.name] = C.finish(a, col, glow=3.0)
        tris[a.name] = a.stats["tris"]
    queen = {}
    try:
        if opts.get("queen") == "game":  # игровая модель (scripts/blender/boss6_flytrap.py), поза из queen_pose=…
            queen = game_queen(col, k_queen, opts.get("queen_pose", "stand"))
        else:
            import flytrap  # noqa: E402

            qa = flytrap.flytrap("sleep")
            qo = C.finish(qa, col, glow=4.0)
            qo.scale = (k_queen,) * 3
            qo.location = (BOSS[0], BOSS[1], 0.58)
            queen = {"tris": qa.stats["tris"], "scale": k_queen}
    except Exception as e:  # noqa: BLE001 — королеву правит другой поток; арена рендерится и без неё
        print("BUILD queen failed:", repr(e)[:300], flush=True)
    picked = []
    try:
        import creatures  # noqa: E402  (по одному на место: обычное, редкое, эпическое, легендарное)

        names = [c[0] for c in creatures.CREATURES]
        want = (("FrogBubble", 0), ("ManyEyeCaterpillar", 4), ("FlowerJaguar", 8), ("SproutFlytrap", 9))
        for (x, y), (nm, idx) in zip(A.SLOTS, want):
            i = names.index(nm) if nm in names else min(idx, len(names) - 1)
            try:
                for ob in creatures.build(i, col):
                    ob.scale = (1.5, 1.5, 1.5)
                    ob.location = (x, y, 0.95)
                    ob.rotation_euler = (0, 0, math.radians(-20 if x > 0 else 20))
                picked.append(names[i])
            except Exception as e:  # noqa: BLE001
                print("BUILD creature", names[i], "failed:", repr(e)[:200], flush=True)
    except Exception as e:  # noqa: BLE001
        print("BUILD creatures failed:", repr(e)[:300], flush=True)
    ov = C.finish(overlay(), col, glow=4.0)
    ov.hide_render = True
    res = (800, 450) if quick else (1600, 900)
    shots = {
        "player": ((0, -68, 10.5), (0, 4, 13.5), 26),
        "approach": ((-8, -46, 17), (2, 12, 9), 24),  # голова королевы — на тёмном проёме и светлом откосе арки
        "lane": ((-LANE_X, -62, 7.5), (-LANE_X, 30, 6.0), 24),
    }
    if "sweep" in opts:  # подбор плотности дымки: кадр игрока при нескольких значениях (в папку sweepdir)
        vol = next(n for n in hz[0].data.materials[0].node_tree.nodes if n.type == "VOLUME_SCATTER")
        for d in opts["sweep"].split(","):
            vol.inputs["Density"].default_value = float(d)
            eye, tgt, lens = shots["player"]
            C.shot(cam, os.path.join(opts.get("sweepdir", out), f"arena6_player_haze{d}.png"), eye, tgt, lens, res)
        vol.inputs["Density"].default_value = float(opts.get("haze", HAZE))
    if "cams" in opts:  # подбор ракурса: {имя: [[глаз], [цель], объектив]} из json → кадры в sweepdir
        with open(opts["cams"], encoding="utf-8") as f:
            for nm, (eye, tgt, lens) in json.load(f).items():
                C.shot(cam, os.path.join(opts.get("sweepdir", out), f"arena6_cam_{nm}.png"), eye, tgt, lens, res)
    for v in views:
        if v in shots:
            eye, tgt, lens = shots[v]
            C.shot(cam, os.path.join(out, f"arena6_{v}.png"), eye, tgt, lens, res)
    if "top" in views:  # сверху: кроны и дымка скрыты, видна схема путей
        ov.hide_render = False
        for nm, ob in objs.items():
            if nm.startswith(("Canopy", "BackCanopy")):
                ob.hide_render = True
        for ob in hz:
            ob.hide_render = True
        A.top_view(cam, os.path.join(out, "arena6_top.png"))
    # части игры: каждый будущий меш (с делением на MeshPart) + простые детали (пол, обрывы, площадка, таблички);
    # ручные категории est() — только для справки (они уже внутри мешей)
    SIMPLE = ("земля и обрывы", "площадка", "таблички")
    parts_plan = {}
    for name, kind, full, game, split in MESHES:
        parts_plan["меши: " + kind] = parts_plan.get("меши: " + kind, 0) + split
    for k in SIMPLE:
        parts_plan["детали: " + k] = round(GAME.get(k, 0))
    total_game = sum(parts_plan.values())
    meshes = []
    for name, kind, full, game, split in MESHES:
        per = math.ceil(game / split)
        meshes.append({"mesh": name, "kind": kind, "meshparts": split, "concept_tris": full,
                       "game_tris_no_bevel": game, "per_meshpart": per, "target_per_meshpart": TARGET[kind],
                       "under_limit": per <= MESHPART_LIMIT, "fits_target": per <= TARGET[kind]})
    by_kind = {}
    for m in meshes:
        k = by_kind.setdefault(m["kind"], {"meshparts": 0, "game_tris_no_bevel": 0, "target": 0})
        k["meshparts"] += m["meshparts"]
        k["game_tris_no_bevel"] += m["game_tris_no_bevel"]
        k["target"] += TARGET[m["kind"]] * m["meshparts"]
    game_tris = sum(m["game_tris_no_bevel"] for m in meshes)
    target_tris = sum(v["target"] for v in by_kind.values())
    worst = max(meshes, key=lambda m: m["per_meshpart"])
    stats = {
        "scene_primitives": prims, "scene_primitives_total": sum(prims.values()),
        "scene_tris": tris, "scene_tris_total": sum(tris.values()), "queen": queen, "creatures_on_slots": picked,
        "game_parts_estimate": dict(sorted(parts_plan.items(), key=lambda kv: -kv[1])),
        "game_parts_total": total_game,
        "game_parts_note": "MeshPart по плану мешей (game_meshes) + простые детали; лианы, листья и т. п. — внутри мешей",
        "game_parts_budget": 800, "game_parts_ok": total_game <= 800,
        "game_meshes_note": ("концепт → игра: число треугольников без фасок (фаски черновика не считаются), та же "
                             "детализация; target — цель упрощённой игровой копии на один MeshPart"),
        "meshpart_tri_limit": MESHPART_LIMIT, "game_tris_no_bevel_total": game_tris,
        "zone_tris_target": ZONE_TRIS, "zone_tris_ok": game_tris <= ZONE_TRIS,
        "sum_of_per_mesh_targets": target_tris, "game_tris_by_kind": by_kind,
        "largest_meshpart": {k: worst[k] for k in ("mesh", "per_meshpart", "under_limit")},
        "all_under_meshpart_limit": all(m["under_limit"] for m in meshes),
        "over_target": [m["mesh"] for m in meshes if not m["fits_target"]],
        "game_meshes": meshes,
        "lane_rule": "D66: полосы |x| 48–66 от входа до выхода, перемычки и центральный путь — ничего на высоте "
                     "1.1–7 над полом зоны; у стен |x| > 76 твёрдое не выше 24",
        "free_lanes": "ok" if not bad else [list(b) for b in bad[:30]],
        "exit_lanes": "ok" if not ext else [list(b) for b in ext[:30]],
        "exit_rects": [[round(v, 1) for v in r] for r in EXIT_FREE],
        "walls_solid_le_24": "ok" if not wall else [list(b) for b in wall[:30]],
        "nonsolid_foliage_above_24_at_walls": {**leafy, "note": "кроны и лианы у стен выше 24 — листва без "
                                               "столкновений (CanCollide = false), твёрдое — стволы, ветви, скалы — ниже 24"},
        "fight_circle_r34": "ok" if not fight else [list(b) for b in fight[:30]],
        "free_rects": [[round(v, 1) for v in r] for r in FREE],
    }
    with open(os.path.join(out, "arena6_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    print("STATS", json.dumps({k: stats[k] for k in ("scene_primitives_total", "scene_tris_total",
                                                     "game_parts_total", "free_lanes", "exit_lanes",
                                                     "walls_solid_le_24",
                                                     "fight_circle_r34",
                                                     "game_tris_no_bevel_total", "zone_tris_target",
                                                     "largest_meshpart", "all_under_meshpart_limit",
                                                     "over_target")},
                              ensure_ascii=False)[:1500], flush=True)
    print("DONE", flush=True)


main()
