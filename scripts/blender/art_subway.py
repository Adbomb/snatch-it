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

# ── 13. Вагонетка с золотом: кусок пути, кузов шире кверху с медными оковками и заклёпками, колёса на рельсах,
#        гора золота ступенями, самородки, монеты, слиток, самоцветы, тормозной рычаг ─────────────────────────


def gold_mine_cart():
    a = S.Art("Art_GoldMineCart", ring_z0=1.45)
    a.paint("iron", "4E5A6E", rings=True)
    a.paint("gold", "F2C230", rings=True)
    a.paint("wood", "8A5A34", rings=True)
    for key, code in (("gravel", "5A4F47"), ("rail", "B8C0CA"), ("rail2", "7E8794"), ("band", "C8702C"),
                      ("rivet", "F0B24A"), ("wheel", "2B2F38"), ("hub", "F2C230"), ("gold2", "C9921A"),
                      ("goldL", "FFE07A"), ("ruby", "E53935"), ("sapph", "2F7DE1"), ("emer", "2E9E4F"),
                      ("amet", "9B59D0"), ("red", "D8352A"), ("glint", "FFFFFF")):
        a.paint(key, code)
    # Кусок пути: щебень, три шпалы, рельсы (головка светлее). Ширина ≤ 3.6 — подушка у босса 3.7 × 3.7.
    a.box("gravel", -1.78, 1.78, -1.1, 1.1, 0.0, 0.18)
    for x in (-1.3, 0.0, 1.3):
        a.box("wood", x - 0.22, x + 0.22, -1.02, 1.02, 0.16, 0.34)
    for y in (-0.62, 0.62):
        a.box("rail2", -1.68, 1.68, y - 0.09, y + 0.09, 0.32, 0.44)
        a.box("rail", -1.7, 1.7, y - 0.07, y + 0.07, 0.43, 0.52)
    # Колёса на рельсах, оси, ступицы.
    for x in (-0.82, 0.82):
        bar(a, "rail2", (x, -0.55, 0.86), (x, 0.55, 0.86), 0.12)
        for s in (-1, 1):
            y0, y1 = sorted((s * 0.54, s * 0.72))
            disc(a, "wheel", x, 0.86, 0.34, y0, y1, axis="y")
            h0, h1 = sorted((s * 0.71, s * 0.77))
            disc(a, "hub", x, 0.86, 0.13, h0, h1, axis="y", bevel=0)
    # Кузов шире кверху (железо с кольцами D39), обод, оковки по углам и посередине, заклёпки.
    a.frustum("iron", (-1.1, 1.1, -0.62, 0.62), (-1.38, 1.38, -0.86, 0.86), 0.95, 2.0)
    a.frame("band", S.octagon(-1.46, 1.46, -0.94, 0.94, 0.04), 0.12, 1.94, 2.12, axis="z")
    for sx in (-1, 1):
        for sy in (-1, 1):
            bar(a, "band", (sx * 1.1, sy * 0.62, 0.95), (sx * 1.39, sy * 0.87, 2.0), 0.14)
    bar(a, "band", (0, 0.64, 0.95), (0, 0.88, 2.0), 0.18, 0.06)  # спереди посередине — табличка
    for sx in (-1, 1):
        bar(a, "band", (sx * 1.12, 0, 0.95), (sx * 1.4, 0, 2.0), 0.06, 0.18)
    for x in (-1.0, -0.55, 0.55, 1.0):
        for sy in (-1, 1):
            z = 1.95
            a.box("rivet", x - 0.05, x + 0.05, sy * 0.97 - 0.03, sy * 0.97 + 0.03, z, z + 0.1, bevel=0)
    # Табличка с короной Крысиного короля на переднем борту (борт наклонён на ≈13°).
    pm = tilt((0, -0.76, 1.45), "X", 12.9)
    a.box("gold", -0.42, 0.42, -0.79, -0.73, 1.22, 1.68, matrix=pm)
    pixel_boxes(a, "red", CROWN, 0.09, -0.315, 1.63, -0.81, -0.785, matrix=pm)
    # Гора золота ступенями.
    a.box("gold", -1.3, 1.3, -0.78, 0.78, 1.9, 2.26)
    a.box("gold", -1.0, 0.95, -0.6, 0.62, 2.22, 2.52)
    a.box("gold", -0.55, 0.62, -0.36, 0.4, 2.48, 2.76)
    for x, y, z, s, t in ((-1.05, -0.5, 2.3, 0.26, 20), (0.95, 0.45, 2.33, 0.24, 50), (-0.3, 0.45, 2.58, 0.22, 10),
                          (0.75, -0.42, 2.58, 0.2, 35), (0.1, -0.2, 2.82, 0.22, 60), (-0.75, 0.15, 2.55, 0.2, 75)):
        gem(a, "goldL", (x, y, z), s, t)  # самородки
    for x, y, z, ang in ((-0.6, -0.72, 2.32, -20), (0.35, -0.7, 2.36, 25), (1.12, -0.1, 2.3, 70)):
        disc(a, "gold2", x, z, 0.17, y - 0.03, y + 0.03, axis="y", matrix=tilt((x, y, z), "Y", ang))  # монеты на ребре
    # Слиток на вершине.
    a.frustum("goldL", (-0.36, 0.36, -0.2, 0.2), (-0.28, 0.28, -0.13, 0.13), 2.76, 2.98,
              matrix=tilt((0.05, 0.02, 2.76), "Z", 18))
    for key, c, size in (("ruby", (-0.25, -0.3, 2.9), 0.34), ("sapph", (0.6, 0.1, 2.7), 0.32),
                         ("emer", (-0.85, -0.28, 2.5), 0.3), ("amet", (0.98, -0.32, 2.46), 0.28),
                         ("sapph", (-0.5, 0.42, 2.66), 0.24), ("ruby", (0.35, -0.55, 2.42), 0.22)):
        gem(a, key, c, size, 25)
    # Монеты высыпались на щебень перед вагонеткой: одна лежит, рядом стопка из трёх.
    disc(a, "gold", -0.62, -0.9, 0.15, 0.17, 0.23)
    for i, (dx, key) in enumerate(((0.0, "gold2"), (0.03, "gold"), (-0.02, "gold2"))):
        disc(a, key, 0.62 + dx, -0.88, 0.14, 0.17 + i * 0.06, 0.23 + i * 0.06)
    # Тормозной рычаг на правом торце с красной рукояткой.
    bar(a, "band", (1.45, 0.3, 0.86), (1.62, 0.3, 2.35), 0.1)
    a.box("red", 1.53, 1.73, 0.2, 0.4, 2.3, 2.52)
    sparkle(a, "glint", (-1.4, -0.5, 3.0), 0.32)
    sparkle(a, "glint", (1.4, -0.9, 3.0), 0.22)
    return a


# ══ EPIC ═════════════════════════════════════════════════════════════════════════════════════════════════════

# ── 23. Скипетр Крысиного короля: фонарь обходчика на золотом жезле (как у босса) стоит в золотой подставке на
#        красной бархатной подушке; фиолетовый постамент с золотой каймой, короной и камнями ─────────────────────


def rat_scepter():
    a = S.Art("Art_RatScepter", ring_z0=0.6)
    a.paint("velvet", "6B3FB8", rings=True)
    a.paint("gold", "F2C230", rings=True)
    a.paint("red", "C2263A", rings=True)
    a.paint("lamp", "FF9226", rings=True)  # стекло фонаря: оранжевее золота рамки, крупная деталь — с квадратами
    for key, code in (("gold2", "C9921A"), ("goldL", "FFE07A"), ("core", "FFF4C8"), ("ruby", "E53935"),
                      ("sapph", "2F7DE1"), ("emer", "2E9E4F"), ("grip", "55309A"), ("glint", "FFFFFF")):
        a.paint(key, code)
    # Постамент: фиолетовый восьмигранник с золотой каймой снизу и сверху, корона спереди, камни по углам.
    a.prism("gold2", S.octagon(-1.22, 1.22, -1.22, 1.22, 0.37), 0.0, 0.12)
    a.prism("velvet", S.octagon(-1.12, 1.12, -1.12, 1.12, 0.34), 0.1, 0.5)
    a.prism("gold", S.octagon(-1.2, 1.2, -1.2, 1.2, 0.36), 0.48, 0.58)
    pixel_boxes(a, "gold", CROWN, 0.09, -0.315, 0.43, -1.145, -1.105)
    for x in (-0.66, 0.66):
        gem(a, "ruby" if x < 0 else "sapph", (x, -1.06, 0.3), 0.2)
    # Подушка с кистями; скипетр стоит в золотой чаше (без стойки-кронштейна: с ней он читался как фонарный столб).
    top = cushion(a, "red", 1.7, 1.7, 0.58, 0.24)
    disc(a, "gold2", 0, 0, 0.36, top - 0.02, top + 0.12)
    disc(a, "gold", 0, 0, 0.28, top + 0.1, top + 0.34)  # навершие-противовес
    gem(a, "ruby", (0, -0.27, top + 0.22), 0.18)
    zs0 = top + 0.32
    a.box("gold", -0.13, 0.13, -0.13, 0.13, zs0, 2.84)  # жезл
    a.box("grip", -0.17, 0.17, -0.17, 0.17, 1.38, 2.05)  # обмотка рукояти
    for z in (1.3, 2.05):
        a.box("goldL", -0.2, 0.2, -0.2, 0.2, z, z + 0.09)
    # Державное яблоко под фонарём: два усечённых конуса и пояс с камнями.
    a.frustum("gold", (-0.2, 0.2, -0.2, 0.2), (-0.33, 0.33, -0.33, 0.33), 2.26, 2.42)
    a.prism("goldL", S.octagon(-0.35, 0.35, -0.35, 0.35, 0.1), 2.4, 2.52)
    a.frustum("gold", (-0.33, 0.33, -0.33, 0.33), (-0.2, 0.2, -0.2, 0.2), 2.5, 2.66)
    for key, c, turn in (("ruby", (0, -0.37, 2.46), 0), ("emer", (0, 0.37, 2.46), 0), ("sapph", (-0.37, 0, 2.46), 90),
                         ("sapph", (0.37, 0, 2.46), 90)):
        gem(a, key, c, 0.15, turn)
    # Завитки-«крылья» по бокам: от яблока вверх-наружу, держат фонарь чашей; на концах светлые шарики.
    for s in (-1, 1):
        bar(a, "gold", (s * 0.28, 0, 2.46), (s * 0.6, 0, 2.62), 0.11)
        bar(a, "gold", (s * 0.6, 0, 2.58), (s * 0.66, 0, 2.94), 0.1, 0.12)  # другая толщина: без общих граней
        gem(a, "goldL", (s * 0.64, 0, 3.02), 0.18)
    # Фонарь: основание с зубцами короны, стекло тёплого света с ярким сердцем на гранях, золотые стойки и
    # перекладины, крыша, сверху маленькая корона с рубином.
    zb = 2.8
    disc(a, "gold", 0, 0, 0.5, zb, zb + 0.14)
    for i in range(8):  # зубцы короны вокруг основания
        ang = math.pi / 8 + i * math.pi / 4
        px, py = 0.44 * math.cos(ang), 0.44 * math.sin(ang)
        a.frustum("goldL" if i % 2 else "gold", (px - 0.07, px + 0.07, py - 0.07, py + 0.07), (px, px, py, py),
                  zb + 0.12, zb + 0.38, bevel=0)
    g0, g1 = zb + 0.14, zb + 0.9
    a.box("lamp", -0.34, 0.34, -0.34, 0.34, g0, g1)
    for k in (-1, 1):
        a.box("core", -0.18, 0.18, k * 0.34 - 0.012, k * 0.34 + 0.012, g0 + 0.16, g1 - 0.16, bevel=0)
        a.box("core", k * 0.34 - 0.012, k * 0.34 + 0.012, -0.18, 0.18, g0 + 0.16, g1 - 0.16, bevel=0)
        a.box("gold2", -0.31, 0.31, k * 0.34 - 0.035, k * 0.34 + 0.035, (g0 + g1) / 2 - 0.03, (g0 + g1) / 2 + 0.03,
              bevel=0)
        a.box("gold2", k * 0.34 - 0.035, k * 0.34 + 0.035, -0.31, 0.31, (g0 + g1) / 2 - 0.025, (g0 + g1) / 2 + 0.035,
              bevel=0)
    for dx in (-1, 1):
        for dy in (-1, 1):
            a.box("gold", dx * 0.34 - 0.07, dx * 0.34 + 0.07, dy * 0.34 - 0.07, dy * 0.34 + 0.07, g0 - 0.02, g1 + 0.02)
    a.frustum("gold", (-0.46, 0.46, -0.46, 0.46), (-0.16, 0.16, -0.16, 0.16), g1, g1 + 0.3)
    a.box("gold", -0.16, 0.16, -0.16, 0.16, g1 + 0.28, g1 + 0.38)
    a.frame("gold", ngon(0, 0, 0.24, 8), 0.07, g1 + 0.36, g1 + 0.48, axis="z")  # корона на крыше
    for i in range(0, 8, 2):
        ang = math.pi / 8 + i * math.pi / 4
        px, py = 0.21 * math.cos(ang), 0.21 * math.sin(ang)
        a.frustum("goldL", (px - 0.05, px + 0.05, py - 0.05, py + 0.05), (px, px, py, py), g1 + 0.46, g1 + 0.66,
                  bevel=0)
    gem(a, "ruby", (0, 0, g1 + 0.6), 0.26)
    sparkle(a, "glint", (-1.15, -0.2, g1 - 0.2), 0.36)
    sparkle(a, "glint", (0.58, -0.4, g1 + 0.62), 0.24)
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
