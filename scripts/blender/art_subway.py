"""Коллекция босса 3 «Подземка» (D54), стиль D39: каждый предмет — своя объёмная модель.

Крысиный король собрал в подземке ценные находки: метро, сыр, золото, странные вещи. 30 предметов (12 Common,
10 Rare, 8 Epic, docs/CATALOG.md) — делаются партиями; сейчас первые три по указанию владельца: сыр-рекордсмен,
вагонетка с золотом, скипетр Крысиного короля. Предмет — ценная коллекционная вещь на своей подставке, а не декор
станции: крупный силуэт, яркие чистые цвета, квадраты-контуры D39 на крупных деталях, мелкие накладки гладкие.
Картин, людей и логотипов нет; свечение (фонарь) — яркие цвета, запечённые в карту, без материала Neon (как D42).
Общие инструменты (блоки, кольца D39, запекание, рендеры) — art_style.py.

Пишет assets/models/art/<id>.fbx (меш Art_<id>), assets/textures/art/<id>_{color,normal}.png, а в папку превью —
повороты, крупные кадры, общий кадр с манекеном Roblox (5.2 стада), <id>.json для Studio и report.json.
Запуск: blender --background --factory-startup --python scripts/blender/art_subway.py -- <репо> <превью>
[check|quick] [id…]
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, PREVIEWS = os.path.abspath(argv[0]), os.path.abspath(argv[1])
CHECK = "check" in argv[2:]
QUICK = "quick" in argv[2:]  # рендеры без запекания и экспорта (материалы сборки) — для быстрых правок
ONLY = [x for x in argv[2:] if x not in ("check", "quick")]
TEXDIR = os.path.join(REPO, "assets", "textures", "art")
os.makedirs(PREVIEWS, exist_ok=True)
os.makedirs(os.path.join(REPO, "assets", "models", "art"), exist_ok=True)
os.makedirs(TEXDIR, exist_ok=True)


# ── Общие детали ─────────────────────────────────────────────────────────────────────────────────────────────


def tilt(c, axis, deg):
    """Поворот детали вокруг точки c."""
    c = Vector(c)
    return Matrix.Translation(c) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-c)


def ngon(cx, cy, r, n=8, phase=None):
    """Правильный многоугольник (точки в плоскости, поперечной оси призмы)."""
    phase = math.pi / n if phase is None else phase
    return [(cx + r * math.cos(phase + 2 * math.pi * i / n), cy + r * math.sin(phase + 2 * math.pi * i / n))
            for i in range(n)]


def disc(a, key, cx, cy, r, a0, a1, n=8, axis="z", bevel=S.BEVEL, matrix=None):
    """Многогранный «цилиндр» вдоль оси: в плоскости xy для z, xz для y, zy для x."""
    a.prism(key, ngon(cx, cy, r, n), a0, a1, axis=axis, bevel=bevel, matrix=matrix)


def bar(a, key, p0, p1, w, h=None, bevel=S.BEVEL):
    """Брусок от точки p0 до p1 с сечением w × h."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    up = "Y" if abs(d.normalized().z) > 0.95 else "Z"
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("X", up).to_matrix().to_4x4()
    h = h or w
    a.box(key, -d.length / 2, d.length / 2, -w / 2, w / 2, -h / 2, h / 2, bevel=bevel, matrix=m)


def gem(a, key, c, size, turn=0.0):
    """Самоцвет: куб на вершине (ромб со всех сторон)."""
    m = Matrix.Translation(c) @ Matrix.Rotation(math.radians(turn), 4, "Z") @ Matrix.Rotation(
        math.radians(45), 4, "X") @ Matrix.Rotation(math.radians(35), 4, "Y")
    h = size / 2
    a.box(key, -h, h, -h, h, -h, h, bevel=0, matrix=m)


def sparkle(a, key, c, size, depth=0.04):
    """Искра-блик драгоценности: три тонких бруска крестом по x, z и y — «плюс» с любой стороны, а не палочка
    в профиль; у бруска по y сечение чуть тоньше, чтобы грани не совпадали."""
    x, y, z = c
    t = size * 0.18
    a.box(key, x - size / 2, x + size / 2, y - depth / 2, y + depth / 2, z - t / 2, z + t / 2, bevel=0)
    a.box(key, x - t / 2, x + t / 2, y - depth / 2 - 0.005, y + depth / 2 + 0.005, z - size / 2, z + size / 2, bevel=0)
    a.box(key, x - t * 0.42, x + t * 0.42, y - size / 2, y + size / 2, z - t * 0.42, z + t * 0.42, bevel=0)


def pixel_boxes(a, key, rows, cell, x0, ztop, y0, y1, matrix=None):
    """Пиксельный знак на плоской грани (в плоскости x–z, толщина y0…y1) прямоугольниками без общих граней
    (S.greedy_rects); matrix — поворот знака вместе с гранью (табличка на наклонном борту, медаль на боку)."""
    for c, r, cw, rh in S.greedy_rects([[ch == "#" for ch in row] for row in rows]):
        a.box(key, x0 + c * cell, x0 + (c + cw) * cell, y0, y1, ztop - (r + rh) * cell, ztop - r * cell, bevel=0,
              matrix=matrix)


def cushion(a, key, w, d, z0, h, tassel="gold", cx=0.0):
    """Бархатная подушка с пухлым верхом и золотыми кистями по углам (витринная подставка)."""
    a.box(key, cx - w / 2, cx + w / 2, -d / 2, d / 2, z0, z0 + h)
    a.box(key, cx - w / 2 + 0.1, cx + w / 2 - 0.1, -d / 2 + 0.1, d / 2 - 0.1, z0 + h - 0.02, z0 + h + 0.1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = cx + sx * w / 2, sy * d / 2
            a.box(tassel, x - 0.08, x + 0.08, y - 0.08, y + 0.08, z0 + h * 0.15, z0 + h * 0.8)
    return z0 + h + 0.1


ONE = [".#.",
       "##.",
       ".#.",
       ".#.",
       "###"]
CROWN = ["#..#..#",
         "##.#.##",
         "#######",
         "#######"]
STAR = ["..#..",
        ".###.",
        "#####",
        ".###.",
        ".#.#."]


# ══ COMMON ═══════════════════════════════════════════════════════════════════════════════════════════════════

# ── 6. Сыр-рекордсмен: огромная головка сыра с вырезанным клином (кусок выдвинут), дырки, синяя розетка «1»,
#       двухъярусная доска с латунной табличкой ───────────────────────────────────────────────────────────────


def champion_cheese():
    a = S.Art("Art_ChampionCheese", ring_z0=0.4)
    a.paint("wood", "9A6236", rings=True)
    # Сыр без квадратов D39: его рисунок — дырки (с квадратами головка читалась как плиточная башня).
    for key, code in (("cheese", "F7C531"), ("rind", "E39A22"), ("inside", "FDE38C"), ("hole", "D9951C"),
                      ("holeIn", "A9620E"), ("wood2", "6B4226"), ("brass", "E0B040"), ("blue", "2F6BD8"),
                      ("blue2", "1E4FA8"), ("gold", "F2C230"), ("goldL", "FFE07A"), ("ruby", "E53935"),
                      ("sapph", "2F7DE1"), ("white", "FFF6E0"), ("glint", "FFFFFF")):
        a.paint(key, code)
    # Доска двумя ярусами и латунная табличка с короной.
    a.prism("wood2", S.octagon(-1.62, 1.62, -1.62, 1.62, 0.5), 0.0, 0.3)
    a.prism("wood", S.octagon(-1.48, 1.48, -1.48, 1.48, 0.44), 0.28, 0.52)
    a.box("brass", -0.55, 0.55, -1.67, -1.6, 0.07, 0.24, bevel=0)
    pixel_boxes(a, "wood2", CROWN, 0.035, -0.1225, 0.225, -1.685, -1.655)

    # Головка — двенадцатигранный «пакман»: четверть (180°…270°) вырезана и смотрит к зрителю спереди-слева,
    # светлая мякоть с дырками видна на главном ракурсе. Головка шире своей высоты — читается как сыр, не башня.
    cx, cy, r, z0, z1 = 0.0, 0.08, 1.4, 0.52, 1.8
    g0, g1 = 180, 270
    ap = r * math.cos(math.radians(15))  # до середины грани

    def arc(rad, degs):
        return [(cx + rad * math.cos(math.radians(d)), cy + rad * math.sin(math.radians(d))) for d in degs]

    a.extrude("cheese", [(cx, cy)] + arc(r, range(g1, g0 + 361, 30)), z0, z1, axis="z")
    # Корка — оранжевые бортики-кольца снизу и сверху (верхний выше головки); у срезов отступают на 3°.
    degs = [g1 + 3] + list(range(g1 + 30, g0 + 360, 30)) + [g0 + 357]
    for za, zb in ((z0, z0 + 0.12), (z1 - 0.12, z1 + 0.03)):
        a.extrude("rind", arc(r + 0.04, degs) + arc(r - 0.1, degs[::-1]), za, zb, axis="z")
    # Срезы: светлая мякоть почти во всю грань (без рамки — иначе похоже на дверцу) и дырки «вглубь»:
    # тёмный край, ещё темнее середина. Срез 180° смотрит вперёд (−y), срез 270° — влево (−x).
    a.box("inside", cx - r + 0.06, cx - 0.05, cy - 0.03, cy, z0 + 0.05, z1 - 0.05, bevel=0)
    a.box("inside", cx - 0.03, cx, cy - r + 0.06, cy - 0.08, z0 + 0.08, z1 - 0.08, bevel=0)
    for hx, hz, hr in ((-0.45, 1.05, 0.18), (-1.0, 1.5, 0.12), (-0.98, 0.84, 0.1), (-0.22, 1.56, 0.1),
                       (-1.2, 1.18, 0.07)):
        a.prism("hole", ngon(hx, hz, hr), cy - 0.055, cy - 0.025, axis="y", bevel=0)
        a.prism("holeIn", ngon(hx, hz, hr * 0.62), cy - 0.07, cy - 0.05, axis="y", bevel=0)
    for hy, hz, hr in ((-0.55, 1.2, 0.16), (-1.05, 0.82, 0.12), (-0.95, 1.55, 0.1), (-0.22, 0.78, 0.09),
                       (-0.3, 1.55, 0.07)):
        a.prism("hole", ngon(hz, cy + hy, hr), cx - 0.055, cx - 0.025, axis="x", bevel=0)
        a.prism("holeIn", ngon(hz, cy + hy, hr * 0.62), cx - 0.07, cx - 0.05, axis="x", bevel=0)
    # Дырки сверху (не под короной и не на корке).
    for hx, hy, hr in ((0.8, -0.45, 0.2), (-0.6, 0.62, 0.16), (1.0, 0.35, 0.11), (0.3, -0.75, 0.12),
                       (-0.2, 1.0, 0.1), (-1.0, 0.35, 0.09)):
        disc(a, "hole", hx, hy, hr, z1 - 0.01, z1 + 0.015, bevel=0)
        disc(a, "holeIn", hx, hy, hr * 0.62, z1 + 0.01, z1 + 0.025, bevel=0)
    # Дырки на боковых гранях (в середине грани; на грани 285° — розетка).
    for th, dx, hz, hr in ((315, 0.05, 0.95, 0.16), (315, -0.12, 1.45, 0.11), (345, 0.0, 1.25, 0.18),
                           (15, 0.1, 0.85, 0.12), (15, -0.1, 1.5, 0.1), (45, 0.0, 1.2, 0.15), (75, 0.05, 0.9, 0.12),
                           (105, 0.0, 1.4, 0.16), (135, -0.05, 0.95, 0.14), (165, 0.0, 1.35, 0.15),
                           (165, 0.12, 0.8, 0.09)):
        m = tilt((cx, cy, 0), "Z", th - 270)
        a.prism("hole", ngon(cx + dx, hz, hr), cy - ap - 0.02, cy - ap + 0.01, axis="y", bevel=0, matrix=m)
        a.prism("holeIn", ngon(cx + dx, hz, hr * 0.62), cy - ap - 0.03, cy - ap - 0.015, axis="y", bevel=0,
                matrix=m)
    # Крумсы сыра на доске в вырезе.
    for x, y, s, ang in ((-0.55, -0.72, 0.16, 20), (-1.02, -0.32, 0.12, 50), (-0.3, -1.08, 0.1, 70)):
        a.box("cheese", x - s / 2, x + s / 2, y - s / 2, y + s / 2, 0.5, 0.5 + s * 0.85, matrix=tilt((x, y, 0), "Z", ang))
    # Золотая корона чемпиона на макушке (сзади справа, не закрывает вырез): зубцы через один выше, на высоких —
    # светлые шарики, на обруче рубин и сапфир.
    kx, ky, kz = 0.4, 0.55, z1 - 0.03
    a.frame("gold", ngon(kx, ky, 0.46, 8), 0.12, kz, kz + 0.28, axis="z")
    for i in range(8):
        ang = math.pi / 8 + i * math.pi / 4
        px, py = kx + 0.4 * math.cos(ang), ky + 0.4 * math.sin(ang)
        tip = kz + (0.62 if i % 2 == 0 else 0.46)
        a.frustum("gold", (px - 0.08, px + 0.08, py - 0.08, py + 0.08), (px, px, py, py), kz + 0.26, tip, bevel=0)
        if i % 2 == 0:
            a.box("goldL", px - 0.055, px + 0.055, py - 0.055, py + 0.055, tip - 0.05, tip + 0.06, bevel=0)
    gem(a, "ruby", (kx, ky - 0.45, kz + 0.14), 0.15)
    gem(a, "sapph", (kx - 0.32, ky - 0.32, kz + 0.14), 0.13, 45)
    # Розетка победителя на грани 285° (рядом с вырезом, видна спереди и на главном ракурсе): синие лепестки,
    # золотой центр с «1», две ленты.
    rm = tilt((cx, cy, 0), "Z", 15)
    yb, zc, ox = cy - ap, 1.22, 0.02
    a.frame("blue", ngon(ox, zc, 0.38, 12), 0.15, yb - 0.05, yb + 0.01, axis="y", matrix=rm)
    a.prism("blue2", ngon(ox, zc, 0.24, 12), yb - 0.04, yb + 0.01, axis="y", matrix=rm)
    a.prism("gold", ngon(ox, zc, 0.21, 8), yb - 0.09, yb - 0.03, axis="y", matrix=rm)
    # «1» тремя брусками: основание, ствол над ним, флажок (нижние грани на разной высоте).
    for x0, x1, za, zb in ((-0.075, 0.075, -0.125, -0.075), (-0.025, 0.025, -0.075, 0.125),
                           (-0.075, -0.025, 0.025, 0.075)):
        a.box("white", ox + x0, ox + x1, yb - 0.115, yb - 0.085, zc + za, zc + zb, bevel=0, matrix=rm)
    for s in (-1, 1):
        a.box("blue", -0.11, 0.11, yb - 0.035, yb, 0.7, 1.0, matrix=rm @ tilt((ox + s * 0.14, yb, 1.0), "Y", s * 14)
              @ Matrix.Translation((ox + s * 0.14, 0, 0)))
    sparkle(a, "glint", (-1.4, 0.3, 2.2), 0.3)
    return a


# ══ RARE ═════════════════════════════════════════════════════════════════════════════════════════════════════

# ── 13. Вагонетка с золотом — королевская, не путать с серыми вагонетками декора станции: красный кузов с золотыми
#        оковками, герб-щит с короной, золотые колёса, гора золота с короной короля и самоцветами, флажок,
#        витринная плита с золотой каймой и кусок пути ────────────────────────────────────────────────────────


def gold_mine_cart():
    a = S.Art("Art_GoldMineCart", ring_z0=1.45)
    # Королевская вагонетка: кузов красный с золотом, как тронный вагон (декоративные вагонетки станции — серые).
    a.paint("royal", "C2263A", rings=True)
    a.paint("gold", "F2C230", rings=True)
    a.paint("wood", "8A5A34", rings=True)
    a.paint("base", "3B3346", rings=True)
    for key, code in (("rail", "B8C0CA"), ("rail2", "7E8794"), ("wheel", "2B2F38"), ("gold2", "C9921A"),
                      ("goldL", "FFE07A"), ("ruby", "E53935"), ("sapph", "2F7DE1"), ("emer", "2E9E4F"),
                      ("amet", "9B59D0"), ("crownR", "8E1A2A"), ("velvet", "6B3FB8"), ("glint", "FFFFFF")):
        a.paint(key, code)
    # Витринная плита с золотой каймой, на ней кусок пути: шпалы, рельсы (головка светлее).
    # Ширина 3.6 — подушка у босса 3.7 × 3.7.
    a.box("base", -1.72, 1.72, -1.06, 1.06, 0.0, 0.18)
    a.frame("gold", S.octagon(-1.8, 1.8, -1.12, 1.12, 0.2), 0.1, 0.1, 0.22, axis="z")  # срез > рамки: без вырожденных углов
    for x in (-1.3, 0.0, 1.3):
        a.box("wood", x - 0.22, x + 0.22, -0.96, 0.96, 0.16, 0.34)
    for y in (-0.62, 0.62):
        a.box("rail2", -1.68, 1.68, y - 0.09, y + 0.09, 0.32, 0.44)
        a.box("rail", -1.7, 1.7, y - 0.07, y + 0.07, 0.43, 0.52)
    # Колёса: тёмная шина, золотой диск, светлая ступица; оси.
    for x in (-0.82, 0.82):
        bar(a, "gold2", (x, -0.55, 0.86), (x, 0.55, 0.86), 0.12)
        for s in (-1, 1):
            y0, y1 = sorted((s * 0.54, s * 0.72))
            disc(a, "wheel", x, 0.86, 0.34, y0, y1, axis="y")
            d0, d1 = sorted((s * 0.7, s * 0.75))
            disc(a, "gold", x, 0.86, 0.25, d0, d1, axis="y", bevel=0)
            h0, h1 = sorted((s * 0.74, s * 0.79))
            disc(a, "goldL", x, 0.86, 0.1, h0, h1, axis="y", bevel=0)
    # Кузов шире кверху (красный с кольцами D39), золотой обод, оковки по углам, посередине сзади и с боков,
    # светлые заклёпки.
    a.frustum("royal", (-1.1, 1.1, -0.62, 0.62), (-1.38, 1.38, -0.86, 0.86), 0.95, 2.0)
    a.frame("gold", S.octagon(-1.46, 1.46, -0.94, 0.94, 0.04), 0.12, 1.94, 2.12, axis="z")
    for sx in (-1, 1):
        for sy in (-1, 1):
            bar(a, "gold", (sx * 1.1, sy * 0.62, 0.95), (sx * 1.39, sy * 0.87, 2.0), 0.14)
    bar(a, "gold", (0, 0.64, 0.95), (0, 0.88, 2.0), 0.18, 0.06)  # спереди посередине — герб
    for sx in (-1, 1):
        bar(a, "gold", (sx * 1.12, 0, 0.95), (sx * 1.4, 0, 2.0), 0.06, 0.18)
    for x in (-1.0, -0.55, 0.55, 1.0):
        for sy in (-1, 1):
            a.box("goldL", x - 0.05, x + 0.05, sy * 0.97 - 0.03, sy * 0.97 + 0.03, 1.95, 2.05, bevel=0)
    # Герб Крысиного короля на переднем борту (борт наклонён на ≈13°): золотой щит ступенями, тёмно-красная
    # корона, рубин в острие; по бокам сапфиры.
    pm = tilt((0, -0.76, 1.45), "X", 12.9)
    shield = [(-0.46, 1.74), (0.46, 1.74), (0.46, 1.36), (0.32, 1.22), (0.16, 1.12), (0.0, 1.06), (-0.16, 1.12),
              (-0.32, 1.22), (-0.46, 1.36)]
    a.extrude("gold", shield, -0.79, -0.73, axis="y", matrix=pm)
    pixel_boxes(a, "crownR", CROWN, 0.09, -0.315, 1.66, -0.81, -0.785, matrix=pm)
    gem(a, "ruby", tuple(pm @ Vector((0.0, -0.8, 1.2))), 0.13)
    for x in (-0.78, 0.78):
        gem(a, "sapph", tuple(pm @ Vector((x, -0.78, 1.45))), 0.16)
    # Гора золота ступенями, самородки, монеты на ребре.
    a.box("gold", -1.3, 1.3, -0.78, 0.78, 1.9, 2.26)
    a.box("gold", -1.0, 0.95, -0.6, 0.62, 2.22, 2.52)
    a.box("gold", -0.55, 0.62, -0.36, 0.4, 2.48, 2.76)
    for x, y, z, s, t in ((-1.05, -0.5, 2.3, 0.26, 20), (0.95, 0.45, 2.33, 0.24, 50), (-0.6, 0.3, 2.58, 0.2, 10),
                          (0.7, -0.3, 2.6, 0.2, 35)):
        gem(a, "goldL", (x, y, z), s, t)
    for x, y, z, ang in ((-0.6, -0.72, 2.32, -20), (0.35, -0.7, 2.36, 25)):
        disc(a, "gold2", x, z, 0.17, y - 0.03, y + 0.03, axis="y", matrix=tilt((x, y, z), "Y", ang))
    # Корона короля на вершине горы: золотой обруч с бархатной шапочкой, зубцы со светлыми шариками, рубин.
    kx, ky, kz = 0.05, 0.02, 2.74
    a.frame("gold", ngon(kx, ky, 0.42, 8), 0.1, kz, kz + 0.26, axis="z")
    a.prism("velvet", ngon(kx, ky, 0.34, 8), kz + 0.02, kz + 0.38)
    for i in range(0, 8, 2):
        ang = math.pi / 8 + i * math.pi / 4
        px, py = kx + 0.37 * math.cos(ang), ky + 0.37 * math.sin(ang)
        a.frustum("gold", (px - 0.08, px + 0.08, py - 0.08, py + 0.08), (px, px, py, py), kz + 0.24, kz + 0.6,
                  bevel=0)
        a.box("goldL", px - 0.06, px + 0.06, py - 0.06, py + 0.06, kz + 0.55, kz + 0.67, bevel=0)
    gem(a, "ruby", (kx, ky - 0.43, kz + 0.13), 0.16)
    # Самоцветы вокруг короны.
    for key, c, size in (("ruby", (-0.78, -0.3, 2.62), 0.34), ("sapph", (0.78, 0.2, 2.62), 0.3),
                         ("emer", (-1.1, 0.35, 2.36), 0.26), ("amet", (1.08, -0.4, 2.36), 0.26),
                         ("sapph", (-0.3, 0.5, 2.6), 0.22), ("ruby", (0.35, -0.5, 2.6), 0.2)):
        gem(a, key, c, size, 25)
    # Королевский флажок, воткнутый в золото сзади слева.
    bar(a, "gold2", (-1.25, 0.72, 1.95), (-1.25, 0.72, 3.7), 0.08)
    a.extrude("velvet", [(-1.21, 3.66), (-0.5, 3.48), (-1.21, 3.28)], 0.7, 0.74, axis="y")
    gem(a, "goldL", (-1.25, 0.72, 3.76), 0.15)
    # Монеты высыпались на плиту перед вагонеткой: одна лежит, рядом стопка из трёх.
    disc(a, "gold", -0.62, -0.82, 0.15, 0.17, 0.23)
    for i, (dx, key) in enumerate(((0.0, "gold2"), (0.03, "gold"), (-0.02, "gold2"))):
        disc(a, key, 0.62 + dx, -0.82, 0.14, 0.17 + i * 0.06, 0.23 + i * 0.06)
    # Тормозной рычаг на правом торце с рубиновой рукояткой.
    bar(a, "gold2", (1.45, 0.3, 0.86), (1.62, 0.3, 2.35), 0.1)
    a.box("ruby", 1.53, 1.73, 0.2, 0.4, 2.3, 2.52)
    sparkle(a, "glint", (-1.4, -0.5, 3.0), 0.32)
    sparkle(a, "glint", (1.4, -0.9, 3.0), 0.22)
    return a


# ══ EPIC ═════════════════════════════════════════════════════════════════════════════════════════════════════

# ── 23. Скипетр Крысиного короля: фонарь обходчика (как у босса) на толстом золотом жезле; державное яблоко с
#        большим центральным рубином, завитки-«крылья», корона шире фонаря с дугами и рубином на вершине; скромная
#        подставка — подушка на фиолетовом восьмиграннике ───────────────────────────────────────────────────────


def rat_scepter():
    a = S.Art("Art_RatScepter", ring_z0=0.26)
    a.paint("velvet", "6B3FB8", rings=True)
    a.paint("gold", "F2C230", rings=True)
    a.paint("red", "C2263A", rings=True)
    a.paint("lamp", "FF9226", rings=True)  # стекло фонаря: оранжевее золота рамки, крупная деталь — с квадратами
    for key, code in (("gold2", "C9921A"), ("goldL", "FFE07A"), ("core", "FFF4C8"), ("ruby", "E53935"),
                      ("sapph", "2F7DE1"), ("emer", "2E9E4F"), ("grip", "55309A"), ("glint", "FFFFFF")):
        a.paint(key, code)
    # Подставка скромнее скипетра (по замечанию владельца): узкий фиолетовый восьмигранник с золотой каймой,
    # пиксельная корона и два камня спереди, маленькая подушка с кистями.
    a.prism("gold2", S.octagon(-1.0, 1.0, -1.0, 1.0, 0.3), 0.0, 0.1)
    a.prism("velvet", S.octagon(-0.9, 0.9, -0.9, 0.9, 0.27), 0.08, 0.44)
    a.prism("gold", S.octagon(-0.98, 0.98, -0.98, 0.98, 0.29), 0.42, 0.52)
    pixel_boxes(a, "gold", CROWN, 0.07, -0.245, 0.4, -0.935, -0.895)
    for x in (-0.47, 0.47):
        gem(a, "ruby" if x < 0 else "sapph", (x, -0.9, 0.26), 0.15)
    top = cushion(a, "red", 1.3, 1.3, 0.52, 0.2)
    # Скипетр стоит в золотой чаше: навершие-противовес с рубином, толстый жезл, фиолетовая рукоять с кольцами.
    disc(a, "gold2", 0, 0, 0.34, top - 0.02, top + 0.12)
    disc(a, "gold", 0, 0, 0.28, top + 0.1, top + 0.34)
    gem(a, "ruby", (0, -0.27, top + 0.22), 0.18)
    a.box("gold", -0.17, 0.17, -0.17, 0.17, top + 0.32, 2.74)  # жезл
    a.box("grip", -0.22, 0.22, -0.22, 0.22, 1.3, 2.0)  # обмотка рукояти
    for z in (1.22, 2.0):
        a.box("goldL", -0.25, 0.25, -0.25, 0.25, z, z + 0.09)
    # Державное яблоко и центральный рубин: большой камень в ступенчатой золотой оправе-ромбе спереди,
    # сапфиры по бокам, изумруд сзади.
    a.frustum("gold", (-0.2, 0.2, -0.2, 0.2), (-0.4, 0.4, -0.4, 0.4), 2.12, 2.28)
    a.prism("goldL", S.octagon(-0.42, 0.42, -0.42, 0.42, 0.12), 2.26, 2.42)
    a.frustum("gold", (-0.4, 0.4, -0.4, 0.4), (-0.2, 0.2, -0.2, 0.2), 2.4, 2.56)
    a.prism("gold2", [(0.0, 2.68), (0.34, 2.34), (0.0, 2.0), (-0.34, 2.34)], -0.47, -0.4, axis="y")
    a.prism("goldL", [(0.0, 2.61), (0.27, 2.34), (0.0, 2.07), (-0.27, 2.34)], -0.52, -0.46, axis="y", bevel=0)
    gm = tilt((0, 0, 2.34), "Y", 45)  # гранёный рубин ромбом: широкое основание в оправе, площадка спереди, блик
    a.frustum("ruby", (-0.1, 0.1, 2.24, 2.44), (-0.17, 0.17, 2.17, 2.51), -0.62, -0.5, axis="y", matrix=gm)
    a.box("glint", -0.06, -0.01, -0.635, -0.615, 2.37, 2.42, bevel=0, matrix=gm)
    for x in (-0.43, 0.43):
        gem(a, "sapph", (x, 0, 2.34), 0.15, 90)
    gem(a, "emer", (0, 0.43, 2.34), 0.15)
    # Завитки-«крылья»: шире головы фонаря, загибаются внутрь; на локтях сапфиры, на концах светлые шарики.
    for s in (-1, 1):
        bar(a, "gold", (s * 0.34, 0, 2.34), (s * 0.74, 0, 2.56), 0.13)
        bar(a, "gold", (s * 0.74, 0, 2.5), (s * 0.82, 0, 3.0), 0.12, 0.14)
        bar(a, "gold", (s * 0.82, 0, 2.96), (s * 0.66, 0, 3.24), 0.11, 0.12)
        gem(a, "goldL", (s * 0.63, 0, 3.32), 0.2)
        gem(a, "sapph", (s * 0.79, -0.09, 2.76), 0.13)
    # Фонарь (как у босса): основание с зубцами, стекло тёплого света с ярким сердцем, золотые стойки и перекладины.
    zb = 2.66
    disc(a, "gold", 0, 0, 0.52, zb, zb + 0.14)
    for i in range(8):
        ang = math.pi / 8 + i * math.pi / 4
        px, py = 0.46 * math.cos(ang), 0.46 * math.sin(ang)
        a.frustum("goldL" if i % 2 else "gold", (px - 0.07, px + 0.07, py - 0.07, py + 0.07), (px, px, py, py),
                  zb + 0.12, zb + 0.38, bevel=0)
    g0, g1 = zb + 0.14, zb + 0.82
    a.box("lamp", -0.36, 0.36, -0.36, 0.36, g0, g1)
    for k in (-1, 1):
        a.box("core", -0.19, 0.19, k * 0.36 - 0.012, k * 0.36 + 0.012, g0 + 0.14, g1 - 0.14, bevel=0)
        a.box("core", k * 0.36 - 0.012, k * 0.36 + 0.012, -0.19, 0.19, g0 + 0.14, g1 - 0.14, bevel=0)
        a.box("gold2", -0.33, 0.33, k * 0.36 - 0.035, k * 0.36 + 0.035, (g0 + g1) / 2 - 0.03, (g0 + g1) / 2 + 0.03,
              bevel=0)
        a.box("gold2", k * 0.36 - 0.035, k * 0.36 + 0.035, -0.33, 0.33, (g0 + g1) / 2 - 0.025, (g0 + g1) / 2 + 0.035,
              bevel=0)
    for dx in (-1, 1):
        for dy in (-1, 1):
            a.box("gold", dx * 0.36 - 0.075, dx * 0.36 + 0.075, dy * 0.36 - 0.075, dy * 0.36 + 0.075, g0 - 0.02,
                  g1 + 0.02)
    a.frustum("gold", (-0.5, 0.5, -0.5, 0.5), (-0.22, 0.22, -0.22, 0.22), g1, g1 + 0.22)
    # Корона короля — шире фонаря: обруч с камнями, бархатная шапка, восемь зубцов (высокие и низкие через один)
    # со светлыми шариками, четыре дуги к золотой чашечке и большой рубин на вершине.
    kz = g1 + 0.18
    a.frame("gold", ngon(0, 0, 0.54, 8), 0.12, kz, kz + 0.26, axis="z")
    a.prism("velvet", ngon(0, 0, 0.44, 8), kz + 0.02, kz + 0.36)
    for i in range(8):
        ang = math.pi / 8 + i * math.pi / 4
        px, py = 0.47 * math.cos(ang), 0.47 * math.sin(ang)
        tall = i % 2 == 0
        tip = kz + (0.64 if tall else 0.46)
        w = 0.09 if tall else 0.07
        a.frustum("gold", (px - w, px + w, py - w, py + w), (px, px, py, py), kz + 0.24, tip, bevel=0)
        b = 0.065 if tall else 0.05
        a.box("goldL", px - b, px + b, py - b, py + b, tip - 0.05, tip + 2 * b, bevel=0)
    for ang, w in ((0, 0.08), (90, 0.085), (180, 0.09), (270, 0.095)):  # разная толщина: без общих граней
        r = math.radians(ang)
        bar(a, "gold", (0.44 * math.cos(r), 0.44 * math.sin(r), kz + 0.24), (0, 0, kz + 0.56), w, 0.1)
    disc(a, "gold2", 0, 0, 0.14, kz + 0.52, kz + 0.7)  # чашечка: рубин над зубцами
    rm = tilt((0, 0, 0), "Z", 45)  # большой огранённый рубин на вершине: низ-конус в чашечке, площадка сверху
    a.frustum("ruby", (-0.07, 0.07, -0.07, 0.07), (-0.21, 0.21, -0.21, 0.21), kz + 0.66, kz + 0.85, matrix=rm)
    a.frustum("ruby", (-0.21, 0.21, -0.21, 0.21), (-0.12, 0.12, -0.12, 0.12), kz + 0.85, kz + 1.0, matrix=rm)
    gem(a, "ruby", (0, -0.55, kz + 0.13), 0.17)
    for x in (-0.55, 0.55):
        gem(a, "sapph", (x, 0, kz + 0.13), 0.15, 90)
    gem(a, "emer", (0, 0.55, kz + 0.13), 0.15)
    sparkle(a, "glint", (-1.3, 0.1, 3.5), 0.36)
    sparkle(a, "glint", (0.82, -0.4, kz + 0.75), 0.24)
    return a


# ══ Сборка, запекание, экспорт, проверочные рендеры ════════════════════════════════════════════════════════

COMMON = [("ChampionCheese", champion_cheese)]
RARE = [("GoldMineCart", gold_mine_cart)]
EPIC = [("RatScepter", rat_scepter)]
GROUPS = {"common": COMMON, "rare": RARE, "epic": EPIC}
ITEMS = [(i, f, g) for g, items in GROUPS.items() for i, f in items if not ONLY or i in ONLY]

bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new("Subway")
bpy.context.scene.collection.children.link(collection)

if CHECK:
    for item_id, make, _ in ITEMS:
        art = make()
        art.build(collection)
        print("CHECK", item_id, json.dumps(art.stats, ensure_ascii=False))
    sys.exit(0)

report, objs = {}, []
for item_id, make, group in ITEMS:
    art = make()
    obj = art.build(collection)
    uv = {} if QUICK else S.bake(obj, art, TEXDIR, item_id)
    lo, hi = S.bounds(obj)
    report[item_id] = {**art.stats, **{k: round(v, 3) for k, v in uv.items()},
                       "size": [round(hi[i] - lo[i], 2) for i in range(3)]}
    if not QUICK:
        S.studio_json(obj, os.path.join(PREVIEWS, f"{item_id}.json"))
        S.export_fbx([obj], os.path.join(REPO, "assets", "models", "art", f"{item_id}.fbx"))
    objs.append((obj, group))
    print("ITEM_OK", item_id, report[item_id]["tris"], flush=True)

prev = S.Preview(collection)
heroes = [S.render_item(prev, obj, PREVIEWS) for obj, _ in objs]
S.strip(heroes, os.path.join(PREVIEWS, "sheet.png"), gap=12)

# Общий кадр: все предметы партии в ряд и манекен Roblox (5.2 стада) — масштаб.
x = 0.0
for obj, _ in objs:
    lo, hi = S.bounds(obj)
    obj.location.x = x - lo.x
    x += (hi.x - lo.x) + 0.8
S.mannequin(collection, x + 1.2)
right = x + 1.2 + 2.0  # правый край манекена (руки ±2)
center = Vector((right / 2, 0, 2.4))
prev.aim_lights(center)
dist = (right + 1.6) / 2 / 0.36  # объектив 50 мм на кадре 36 мм: половина ширины кадра = 0.36 расстояния
prev.shot(os.path.join(PREVIEWS, "group_scale.png"), (center.x, -dist, 5.0), (center.x, 0, 2.5), 50, (2000, 900))
for obj, _ in objs:
    obj.location.x = 0

with open(os.path.join(PREVIEWS, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("SUBWAY_OK " + json.dumps({k: v["tris"] for k, v in report.items()}, ensure_ascii=False))
