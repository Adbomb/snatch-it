"""Коллекция босса 2 «Музей безумных находок» (D42), стиль D39: каждый предмет — своя объёмная модель.

Барахолка: странные, смешные, мемные и редкие находки — понятные детям, яркие, с крупным силуэтом. 30 предметов:
12 Common, 10 Rare (4 картины), 8 Epic. «Сотворение Адама» и «Рождение Венеры» исключены
(2026-11-03): обнажённые фигуры — Roblox заблокировал аккаунт владельца за их карты (docs/RECOVERY_STATUS.md);
вместо них — золотой микрофон и золотой геймпад (выбор владельца). Новых картин не добавлять; перед загрузкой в
Roblox каждую картинку смотреть на наготу и сомнительное. Общие инструменты (блоки, кольца D39, изображение на холсте, запекание,
рендеры) — art_style.py. Стекло (банка, бутылка, купол автомата) — без прозрачности: голубые рёбра-грани с бликами,
содержимое видно (у предмета один меш и одна SurfaceAppearance). Изображения картин — файлы Wikimedia Commons из
общественного достояния (assets/art_sources/SOURCES.md).

Пишет assets/models/art/<id>.fbx (меш Art_<id>), assets/textures/art/<id>_{color,normal}.png, а в папку превью —
повороты, крупные кадры, общие кадры по редкостям с манекеном, <id>.json для Studio и report.json.
Запуск: blender --background --factory-startup --python scripts/blender/art_flea.py -- <репо> <превью> [check] [id…]
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
ONLY = [x for x in argv[2:] if x != "check"]
TEXDIR = os.path.join(REPO, "assets", "textures", "art")
SOURCES = os.path.join(REPO, "assets", "art_sources")
os.makedirs(PREVIEWS, exist_ok=True)
os.makedirs(os.path.join(REPO, "assets", "models", "art"), exist_ok=True)


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
    """Восьмигранный (n-гранный) «цилиндр» вдоль оси: в плоскости xy для z, xz для y, zy для x."""
    a.prism(key, ngon(cx, cy, r, n), a0, a1, axis=axis, bevel=bevel, matrix=matrix)


def bar(a, key, p0, p1, w, h=None, bevel=S.BEVEL):
    """Брусок от точки p0 до p1 с сечением w × h."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    up = "Y" if abs(d.normalized().z) > 0.95 else "Z"
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("X", up).to_matrix().to_4x4()
    h = h or w
    a.box(key, -d.length / 2, d.length / 2, -w / 2, w / 2, -h / 2, h / 2, bevel=bevel, matrix=m)


def chain(a, keys, pts, w, h=None, grow=0.0):
    """Ломаная из брусков (изгиб — стыки внахлёст на grow с каждой стороны); цвета чередуются по keys. Сечение
    у соседних брусков чуть разное (через один на 8 % толще): боковые грани не совпадают."""
    for i in range(len(pts) - 1):
        p0, p1 = Vector(pts[i]), Vector(pts[i + 1])
        d = (p1 - p0).normalized() * grow
        k = 1.08 if i % 2 else 1.0
        bar(a, keys[i % len(keys)], p0 - d, p1 + d, w * k, h * k if h else None)


def sparkle(a, key, c, size, plane="xz", depth=0.04):
    """Четырёхлучевая искра: два тонких бруска крестом (блик, магия)."""
    x, y, z = c
    t = size * 0.18
    if plane == "xz":
        a.box(key, x - size / 2, x + size / 2, y - depth / 2, y + depth / 2, z - t / 2, z + t / 2, bevel=0)
        a.box(key, x - t / 2, x + t / 2, y - depth / 2 - 0.005, y + depth / 2 + 0.005, z - size / 2, z + size / 2,
              bevel=0)
    else:  # горизонтальная (сверху)
        a.box(key, x - size / 2, x + size / 2, y - t / 2, y + t / 2, z - depth / 2, z + depth / 2, bevel=0)
        a.box(key, x - t / 2, x + t / 2, y - size / 2, y + size / 2, z - depth / 2 - 0.005, z + depth / 2 + 0.005,
              bevel=0)


def cushion(a, key, w, d, z0, h, tassel="gold", cx=0.0):
    """Бархатная подушка с пухлым верхом и золотыми кистями по углам (витринная подставка)."""
    a.box(key, cx - w / 2, cx + w / 2, -d / 2, d / 2, z0, z0 + h)
    a.box(key, cx - w / 2 + 0.1, cx + w / 2 - 0.1, -d / 2 + 0.1, d / 2 - 0.1, z0 + h - 0.02, z0 + h + 0.1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = cx + sx * w / 2, sy * d / 2
            a.box(tassel, x - 0.08, x + 0.08, y - 0.08, y + 0.08, z0 + h * 0.15, z0 + h * 0.8)
    return z0 + h + 0.1


def glass_cage(a, key, cx, cy, r, z0, z1, n=8, post=0.07, ring=0.1, phase=None):
    """Стекло без прозрачности: рёбра по вершинам n-угольника и кольца сверху и снизу — содержимое видно.
    phase — поворот многоугольника (по умолчанию спереди грань, а не ребро)."""
    for x, y in ngon(cx, cy, r, n, phase):  # концы рёбер спрятаны в кольцах: их грани не совпадают с гранями колец
        a.box(key, x - post, x + post, y - post, y + post, z0 + ring / 3, z1 - ring / 3)
    a.frame(key, ngon(cx, cy, r + post, n, phase), post * 2, z0, z0 + ring, axis="z")
    a.frame(key, ngon(cx, cy, r + post, n, phase), post * 2, z1 - ring, z1, axis="z")


def painting_image(name, width):
    """Уменьшенная копия исходника картины (PNG в папке превью): холст на карте ≈ 500 пикселей в ширину."""
    img = bpy.data.images.load(os.path.join(SOURCES, name))
    w, h = img.size
    img.scale(width, round(h * width / w))
    path = os.path.join(PREVIEWS, os.path.splitext(name)[0] + ".png")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return path


DOLLAR = [".#.",
          "###",
          "#..",
          "###",
          "..#",
          "###",
          ".#."]
STAR = ["..#..",
        ".###.",
        "#####",
        ".###.",
        ".#.#."]
BOLT = ["..##",
        ".##.",
        "####",
        ".##.",
        "##..",
        "#..."]
HEART = [".##.##.",
         "#######",
         "#######",
         ".#####.",
         "..###..",
         "...#..."]


# ══ COMMON ═══════════════════════════════════════════════════════════════════════════════════════════════════

# ── 1. Золотой банан: изогнутый золотой банан на красной бархатной подушке, искры, табличка ─────────────────


def golden_banana():
    a = S.Art("Art_GoldenBanana", ring_z0=0.4)
    a.paint("velvet", "C62828", rings=True)
    a.paint("wood", "5E3A24", rings=True)
    for key, code in (("gold", "F7C531"), ("gold2", "D99A16"), ("stem", "8A5A12"), ("tip", "4A3010"),
                      ("tassel", "F2C230"), ("shine", "FFF6C8"), ("plate", "F2C230")):
        a.paint(key, code)
    a.box("wood", -1.35, 1.35, -0.95, 0.95, 0.0, 0.3)
    a.box("plate", -0.5, 0.5, -0.99, -0.94, 0.06, 0.24, bevel=0)
    top = cushion(a, "velvet", 2.3, 1.5, 0.28, 0.32, tassel="tassel")
    # банан — дуга «улыбкой» из брусков, к концам тоньше; лежит на подушке, концы приподняты
    R, n = 1.55, 7
    pts = []
    for i in range(n + 1):
        t = -1 + 2 * i / n
        th = math.radians(58) * t
        pts.append((R * math.sin(th), 0.0, top + 0.28 + R * (1 - math.cos(th))))
    for i in range(n):
        t = abs((i + 0.5) / n * 2 - 1)
        w = 0.56 * (1 - 0.42 * t * t)
        p0, p1 = Vector(pts[i]), Vector(pts[i + 1])
        d = (p1 - p0).normalized() * w * 0.32
        bar(a, "gold" if i % 2 == 0 else "gold2", p0 - d, p1 + d, w, w * 0.92)
    # плодоножка и тёмный кончик
    p, q = Vector(pts[-1]), Vector(pts[-2])
    d = (p - q).normalized()
    bar(a, "stem", p - d * 0.05, p + d * 0.32, 0.2)
    p, q = Vector(pts[0]), Vector(pts[1])
    d = (p - q).normalized()
    bar(a, "tip", p - d * 0.02, p + d * 0.12, 0.2)
    # блик вдоль верха и искры
    for i in (2, 3, 4):
        p0, p1 = Vector(pts[i]), Vector(pts[i + 1])
        off = Vector((0, -0.28 - 0.012 * (i % 2), 0.12))
        bar(a, "shine", p0 + off, p1 + off, 0.07, 0.07, bevel=0)
    sparkle(a, "shine", (-1.05, -0.2, top + 1.25), 0.36)
    sparkle(a, "shine", (1.2, -0.2, top + 1.55), 0.28)
    sparkle(a, "shine", (0.15, -0.2, top + 1.0), 0.22)
    return a


# ── 2. Проклятый телевизор: оранжевый ламповый ТВ, на экране зелёная ухмылка, антенны-рожки, язык ───────────

TV_FACE = ["..........",
           ".##....##.",
           "..##..##..",
           "..........",
           ".#......#.",
           ".##WWWW##.",
           "..#W##W#..",
           "...####..."]


def cursed_tv():
    a = S.Art("Art_CursedTV", ring_z0=1.3)
    a.paint("body", "E0782C", rings=True)
    a.paint("side", "B85A1E", rings=True)
    for key, code in (("bezel", "2B2B33"), ("screen", "1B1530"), ("face", "9CFF4A"), ("teeth", "FFFFFF"),
                      ("knob", "F2E2C4"), ("dark", "15161C"), ("horn", "E53935"), ("metal", "B8C2CC"),
                      ("tongue", "F07A8C"), ("glint", "D8FFC0")):
        a.paint(key, code)
    # ножки-распорки
    for x in (-0.75, 0.75):
        for y in (-0.5, 0.5):
            a.box("dark", x - 0.08, x + 0.08, y - 0.08, y + 0.08, 0.0, 0.42, matrix=tilt((x, y, 0.42), "Y", -x * 12))
    a.box("side", -1.05, 1.05, -0.78, 0.78, 0.38, 0.52)
    a.box("body", -1.1, 1.1, -0.82, 0.8, 0.5, 2.2)  # корпус
    a.box("side", -0.9, 0.9, -0.6, 0.98, 0.7, 2.0)  # кинескоп сзади
    # экран в рамке, справа — панель с ручками
    a.frame("bezel", S.octagon(-0.98, 0.42, 0.62, 2.08, 0.18), 0.12, -0.9, -0.8, axis="y")
    a.prism("screen", S.octagon(-0.88, 0.32, 0.72, 1.98, 0.13), -0.86, -0.8, axis="y")
    a.pixels(TV_FACE, {"#": ("face", 0.02), "W": ("teeth", 0.025)}, 0.11, -0.83, 1.86, "xz", 0.86)
    a.box("glint", -0.8, -0.62, -0.885, -0.86, 1.72, 1.88, bevel=0)
    a.box("bezel", 0.52, 0.98, -0.88, -0.8, 0.62, 2.08)
    for z in (1.75, 1.3):
        disc(a, "knob", 0.75, z, 0.15, -0.98, -0.86, axis="y")
        a.box("dark", 0.72, 0.78, -1.0, -0.97, z - 0.1, z + 0.1, bevel=0)
    for z in (0.8, 0.9, 1.0):
        a.box("dark", 0.6, 0.9, -0.89, -0.86, z - 0.02, z + 0.02, bevel=0)  # решётка динамика
    # язык свисает из-под экрана
    a.box("tongue", -0.5, -0.12, -0.98, -0.8, 0.36, 0.62)
    a.box("tongue", -0.46, -0.16, -1.02, -0.9, 0.22, 0.4)
    # антенны-рожки с красными наконечниками
    for s in (1, -1):
        p0 = Vector((s * 0.2, 0.1, 2.18))
        p1 = Vector((s * 0.85, 0.1, 3.1))
        bar(a, "metal", p0, p1, 0.07)
        a.frustum("horn", (s * 0.85 - 0.12, s * 0.85 + 0.12, -0.02, 0.22), (s * 0.95, s * 0.95, 0.1, 0.1), 3.05,
                  3.45, bevel=0)
    a.box("dark", -0.3, 0.3, -0.12, 0.32, 2.18, 2.34)
    return a


# ── 3. НЛО в банке: банка-«клетка» из стеклянных рёбер, внутри большая тарелка с пришельцем ловит лучом корову ──


def ufo_jar():
    a = S.Art("Art_UfoJar", ring_z0=1.3)
    a.paint("lid", "D8352A", rings=True)
    a.paint("base", "4A5A78", rings=True)
    for key, code in (("glass", "A8E6F0"), ("shine", "FFFFFF"), ("saucer", "D6DCE6"), ("band", "E040A0"),
                      ("dome", "6FD8FF"), ("alien", "7CE84A"), ("eye", "15161C"), ("light", "FFD84A"),
                      ("light2", "4FE3F0"), ("beam", "E8FF9A"), ("label", "FFF6E0"), ("ink", "1F3E9A"),
                      ("ground", "5FAE45"), ("cow", "FFFFFF"), ("spot", "15161C"), ("pink", "FF9AB0")):
        a.paint(key, code)
    disc(a, "base", 0, 0, 1.0, 0.0, 0.26)
    disc(a, "ground", 0, 0, 0.78, 0.24, 0.36)
    glass_cage(a, "glass", 0, 0, 0.88, 0.24, 2.6, post=0.055)
    disc(a, "lid", 0, 0, 1.02, 2.58, 2.84)
    disc(a, "lid", 0, 0, 0.8, 2.82, 2.96)
    disc(a, "base", 0, 0, 0.22, 2.94, 3.1)  # ручка крышки
    # блики на стекле спереди слева
    a.box("shine", -0.66, -0.6, -0.8, -0.76, 1.95, 2.42, bevel=0)
    a.box("shine", -0.52, -0.48, -0.82, -0.78, 2.18, 2.42, bevel=0)
    # летающая тарелка: серебряный диск, розовый пояс с огнями, купол, пришелец с антеннами
    disc(a, "saucer", 0, 0, 0.42, 1.48, 1.62)
    disc(a, "band", 0, 0, 0.76, 1.6, 1.74)
    disc(a, "saucer", 0, 0, 0.6, 1.72, 1.84)
    for i, (x, y) in enumerate(ngon(0, 0, 0.76, 8)):
        a.box("light" if i % 2 == 0 else "light2", x - 0.07, x + 0.07, y - 0.07, y + 0.07, 1.62, 1.72, bevel=0)
    disc(a, "dome", 0, 0, 0.36, 1.82, 2.2)
    a.box("alien", -0.22, 0.22, -0.4, -0.04, 1.86, 2.22)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.03, s * 0.19))
        a.box("eye", x0, x1, -0.43, -0.39, 1.98, 2.14, bevel=0)
        bar(a, "alien", (s * 0.12, -0.22, 2.2), (s * 0.22, -0.22, 2.42), 0.04)
        disc(a, "light", s * 0.22, -0.22, 0.05, 2.4, 2.48)
    # луч — кольца света, внутри парит корова
    for i, (z, rr) in enumerate(((0.5, 0.5), (0.86, 0.42), (1.22, 0.34))):
        a.frame("beam", ngon(0, 0, rr, 8), 0.07, z - 0.03, z + 0.03, axis="z")
    a.box("cow", -0.2, 0.2, -0.11, 0.11, 0.86, 1.08, matrix=tilt((0, 0, 0.97), "Y", -12))
    a.box("cow", -0.32, -0.16, -0.08, 0.08, 0.92, 1.1, matrix=tilt((0, 0, 0.97), "Y", -12))
    a.box("pink", -0.38, -0.3, -0.06, 0.06, 0.92, 1.0, matrix=tilt((0, 0, 0.97), "Y", -12))
    a.box("spot", 0.02, 0.14, -0.13, -0.1, 0.94, 1.04, bevel=0, matrix=tilt((0, 0, 0.97), "Y", -12))
    for x in (-0.12, 0.12):
        a.box("cow", x - 0.04, x + 0.04, -0.06, 0.06, 0.74, 0.88, matrix=tilt((0, 0, 0.97), "Y", -12))
    # этикетка на крышке
    a.box("label", -0.42, 0.42, -1.05, -1.0, 2.62, 2.8, bevel=0)
    a.box("ink", -0.32, 0.32, -1.07, -1.04, 2.68, 2.74, bevel=0)
    return a


# ── 4. Кот в шлеме: рыжий кот-космонавт в белом скафандре, шлем-аквариум из стеклянных рёбер, ранец, луна ──


def astro_cat():
    a = S.Art("Art_AstroCat", ring_z0=1.2)
    a.paint("suit", "EEF0F3", rings=True)
    a.paint("moon", "9AA0AC", rings=True)
    for key, code in (("fur", "F08A2C"), ("stripe", "C8641A"), ("muzzle", "FFF1DC"), ("nose", "F07A8C"),
                      ("eye", "2E9E4F"), ("dark", "15161C"), ("glint", "FFFFFF"), ("accent", "FF7A1A"),
                      ("glass", "A8E6F0"), ("gold", "F2C230"), ("crater", "6E7480"), ("red", "E53935"),
                      ("glove", "FF7A1A"), ("cap", "C8F0F8"), ("inner", "FFB0C0"), ("shine", "FFFFFF")):
        a.paint(key, code)
    # лунный камень с кратерами
    a.box("moon", -1.0, 1.0, -0.85, 0.85, 0.0, 0.34)
    a.box("moon", -0.8, 0.8, -0.68, 0.68, 0.32, 0.44)
    for x, y in ((-0.7, -0.5), (0.65, -0.55), (0.6, 0.45)):
        disc(a, "crater", x, y, 0.13, 0.33, 0.36, bevel=0)
    # тело в скафандре (сидит), лапы в оранжевых перчатках, сапоги
    a.box("suit", -0.55, 0.55, -0.4, 0.5, 0.42, 1.4)
    a.box("accent", -0.57, 0.57, -0.42, 0.52, 0.86, 0.96)  # пояс
    a.box("gold", -0.12, 0.12, -0.45, -0.41, 1.04, 1.28, bevel=0)  # пульт на груди
    a.box("red", -0.06, 0.06, -0.47, -0.44, 1.18, 1.24, bevel=0)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.12, s * 0.5))
        a.box("suit", x0, x1, -0.78, -0.3, 0.42, 0.7)  # колени-сапоги вперёд
        a.box("accent", x0 - 0.02, x1 + 0.02, -0.82, -0.62, 0.4, 0.6)
        x0, x1 = sorted((s * 0.5, s * 0.74))
        a.box("suit", x0, x1, -0.3, 0.2, 0.7, 1.3)  # руки
        a.box("glove", x0 - 0.02, x1 + 0.02, -0.44, 0.0, 0.52, 0.78)
    # ранец с баллонами
    a.box("suit", -0.48, 0.48, 0.48, 0.86, 0.6, 1.36)
    for s in (1, -1):
        disc(a, "accent", s * 0.26, 0.92, 0.16, 0.66, 1.42)
    # голова кота
    a.box("fur", -0.46, 0.46, -0.5, 0.3, 1.46, 2.16)
    a.box("muzzle", -0.24, 0.24, -0.58, -0.4, 1.52, 1.76)
    a.box("nose", -0.07, 0.07, -0.61, -0.56, 1.7, 1.78, bevel=0)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.08, s * 0.32))
        a.box("eye", x0, x1, -0.54, -0.48, 1.82, 2.04, bevel=0)
        x0, x1 = sorted((s * 0.16, s * 0.24))
        a.box("dark", x0, x1, -0.56, -0.53, 1.84, 2.02, bevel=0)
        g = 0.27 if s > 0 else -0.2
        a.box("glint", g - 0.03, g + 0.03, -0.57, -0.55, 1.95, 2.01, bevel=0)
        x0, x1 = sorted((s * 0.3, s * 0.47))
        a.box("stripe", x0, x1, -0.52, -0.46, 2.02, 2.12, bevel=0)
        x0, x1 = sorted((s * 0.12, s * 0.42))
        a.frustum("fur", (x0, x1, -0.3, -0.04), (s * 0.3, s * 0.3, -0.17, -0.17), 2.14, 2.5, bevel=0)
        x0, x1 = sorted((s * 0.2, s * 0.34))
        a.frustum("inner", (x0, x1, -0.32, -0.27), (s * 0.29, s * 0.29, -0.295, -0.295), 2.18, 2.42, bevel=0)
    # шлем-аквариум: воротник, стеклянные рёбра, кольца, прозрачная «крышка», антенна; блики спереди
    a.frame("suit", ngon(0, -0.1, 0.96, 6, 0), 0.26, 1.36, 1.52, axis="z")
    glass_cage(a, "glass", 0, -0.1, 0.84, 1.5, 2.62, n=6, post=0.05, ring=0.08, phase=0)
    disc(a, "cap", 0, -0.1, 0.72, 2.6, 2.66, n=6, bevel=0)
    a.box("shine", -0.74, -0.7, -0.5, -0.36, 2.2, 2.5, bevel=0)
    a.box("suit", 0.3, 0.38, -0.14, -0.06, 2.64, 3.0, bevel=0)
    disc(a, "red", 0.34, -0.1, 0.08, 2.98, 3.14)
    # хвост в полоску лежит на камне
    chain(a, ["fur", "stripe"], [(0.5, 0.2, 0.53), (0.74, 0.2, 0.53), (0.96, 0.26, 0.56), (1.12, 0.38, 0.66)], 0.22,
          0.18, grow=0.04)
    return a


# ── 5. Магический гриб: огромная фиолетовая шляпка в белых пятнах, светящиеся грибочки, мох, искры ─────────


def magic_mushroom():
    a = S.Art("Art_MagicMushroom", ring_z0=1.0)
    a.paint("cap", "8E44D9", rings=True)
    a.paint("stem", "F2EADF", rings=True)
    a.paint("moss", "5FAE45", rings=True)
    for key, code in (("spot", "FFFFFF"), ("gill", "5A2A8A"), ("glow", "4FE3F0"), ("glow2", "FF6FD8"),
                      ("eye", "2B1840"), ("blush", "FF9AC4"), ("shine", "FFF6C8"), ("dirt", "6B4A2A"),
                      ("grass", "74BD58"), ("swirl", "C79BFF")):
        a.paint(key, code)
    a.box("dirt", -1.05, 1.05, -0.9, 0.9, 0.0, 0.22)
    a.box("moss", -1.0, 1.0, -0.85, 0.85, 0.2, 0.36)
    for x, y in ((-0.85, -0.7), (0.8, -0.65), (0.9, 0.6), (-0.7, 0.62)):
        a.box("grass", x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0.34, 0.6)
    # ножка: две ступени, внизу шире, лицо-улыбка
    disc(a, "stem", 0, 0, 0.5, 0.34, 0.8)
    disc(a, "stem", 0, 0, 0.42, 0.78, 1.5)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.08, s * 0.2))
        a.box("eye", x0, x1, -0.45, -0.41, 1.06, 1.14, bevel=0)  # довольные глаза-щёлочки
        x0, x1 = sorted((s * 0.18, s * 0.32))
        a.box("blush", x0, x1, -0.44, -0.4, 0.92, 0.98, bevel=0)
    a.box("eye", -0.07, 0.07, -0.45, -0.41, 0.9, 0.95, bevel=0)
    for z, x in ((0.6, -0.2), (1.32, 0.18)):
        a.box("swirl", x - 0.12, x + 0.12, -0.52, -0.48, z - 0.03, z + 0.03, bevel=0)  # магические узоры
    # шляпка: широкий низ, ступени к макушке, тёмные пластинки снизу
    disc(a, "gill", 0, 0, 1.12, 1.46, 1.58)
    disc(a, "cap", 0, 0, 1.3, 1.56, 1.92)
    disc(a, "cap", 0, 0, 1.08, 1.9, 2.22)
    disc(a, "cap", 0, 0, 0.72, 2.2, 2.46)
    disc(a, "cap", 0, 0, 0.34, 2.44, 2.58)
    # белые пятна на боках и сверху шляпки
    for i, ang in enumerate((-90, -40, 30, 100, 160, 220)):
        r = math.radians(ang)
        x, y = 1.31 * math.cos(r), 1.31 * math.sin(r)
        m = Matrix.Translation((x, y, 1.74)) @ Matrix.Rotation(r, 4, "Z")
        a.box("spot", -0.03, 0.03, -0.16, 0.16, -0.12, 0.12, bevel=0, matrix=m)
    for x, y in ((-0.5, -0.4), (0.45, 0.35), (0.15, -0.55), (-0.4, 0.5)):
        a.box("spot", x - 0.14, x + 0.14, y - 0.14, y + 0.14, 2.21, 2.25, bevel=0)
    # светящиеся грибочки вокруг
    for (x, y, h, key) in ((-0.7, -0.45, 0.42, "glow"), (0.75, -0.35, 0.34, "glow2"), (0.55, 0.55, 0.5, "glow"),
                           (-0.62, 0.45, 0.3, "glow2")):
        a.box("stem", x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.34, 0.34 + h)
        disc(a, key, x, y, 0.16, 0.34 + h - 0.02, 0.34 + h + 0.12)
    sparkle(a, "shine", (-1.0, -0.4, 2.5), 0.3)
    sparkle(a, "shine", (1.05, -0.3, 2.75), 0.24)
    return a


# ── 6. Живая кассета: VHS с глазами-катушками, клыками и языком из плёнки, на кроссовках ──────────────────────


def living_cassette():
    a = S.Art("Art_LivingCassette", ring_z0=1.0)
    a.paint("shell", "26272E", rings=True)
    for key, code in (("label", "FFF6E0"), ("red", "E53935"), ("orange", "FF8A1F"), ("yellow", "FFD12E"),
                      ("white", "FFFFFF"), ("pupil", "15161C"), ("window", "3A4A5A"), ("tape", "5A3A22"),
                      ("tooth", "FFFFFF"), ("mouth", "8E2433"), ("shoe", "2F6BD8"), ("sole", "F2F2F2"),
                      ("lace", "FFFFFF"), ("glint", "FFFFFF")):
        a.paint(key, code)
    # кроссовки
    for s in (1, -1):
        x0, x1 = sorted((s * 0.35, s * 0.95))
        a.box("sole", x0, x1, -0.62, 0.3, 0.0, 0.1)
        a.box("shoe", x0 + 0.02 * s, x1 - 0.02 * s, -0.6, 0.28, 0.08, 0.36)
        a.box("lace", sorted((s * 0.5, s * 0.8))[0], sorted((s * 0.5, s * 0.8))[1], -0.62, -0.58, 0.22, 0.27, bevel=0)
        x0, x1 = sorted((s * 0.6, s * 0.7))
        a.box("shell", x0, x1, -0.1, 0.1, 0.34, 0.5)  # ножки
    # корпус кассеты стоя на длинном ребре
    a.box("shell", -1.4, 1.4, -0.3, 0.3, 0.48, 2.06)
    # наклейка в полоску 80-х наверху
    a.box("label", -1.18, 1.18, -0.34, -0.29, 1.56, 1.98, bevel=0)
    for i, (key, z) in enumerate((("red", 1.86), ("orange", 1.78), ("yellow", 1.7))):
        a.box(key, -1.1, 1.1, -0.355, -0.335, z - 0.035, z + 0.035, bevel=0)
    # окна катушек — глаза
    a.box("window", -1.0, 1.0, -0.34, -0.29, 0.98, 1.48, bevel=0)
    for s in (1, -1):
        disc(a, "white", s * 0.55, 1.23, 0.27, -0.38, -0.33, axis="y")
        disc(a, "pupil", s * 0.48, 1.2, 0.13, -0.41, -0.37, axis="y")
        a.box("glint", s * 0.48 + 0.02, s * 0.48 + 0.08, -0.43, -0.4, 1.25, 1.31, bevel=0)
    # рот-шторка внизу: клыки и язык из плёнки
    a.box("mouth", -0.9, 0.9, -0.34, -0.29, 0.56, 0.9, bevel=0)
    for x in (-0.65, -0.3, 0.3, 0.65):
        a.frustum("tooth", (x - 0.1, x + 0.1, -0.38, -0.34), (x, x, -0.36, -0.36), 0.9, 0.68, bevel=0)
    chain(a, ["tape"], [(0.05, -0.36, 0.62), (0.15, -0.6, 0.5), (0.0, -0.85, 0.4), (-0.25, -0.95, 0.22),
                        (-0.1, -1.05, 0.05)], 0.3, 0.05, grow=0.05)
    return a


# ── 7. Трофейный бургер: огромный бургер на золотой ножке-кубке с ручками и табличкой ─────────────────────────


def trophy_burger():
    a = S.Art("Art_TrophyBurger", ring_z0=1.6)
    a.paint("bun", "E39A43", rings=True)
    a.paint("gold", "F2C230", rings=True)
    for key, code in (("gold2", "C9921A"), ("plinth", "2B2B33"), ("plate", "F2E2C4"), ("patty", "6B3A1E"),
                      ("cheese", "FFC531"), ("lettuce", "5FBF3A"), ("tomato", "E53935"), ("seed", "FFF1D0"),
                      ("bun2", "C77A2A"), ("ink", "2B2B33")):
        a.paint(key, code)
    # постамент и золотая ножка кубка
    a.box("plinth", -0.9, 0.9, -0.8, 0.8, 0.0, 0.42)
    a.box("plate", -0.5, 0.5, -0.84, -0.79, 0.1, 0.32, bevel=0)
    a.box("ink", -0.36, 0.36, -0.86, -0.83, 0.18, 0.24, bevel=0)
    disc(a, "gold", 0, 0, 0.6, 0.4, 0.58)
    disc(a, "gold2", 0, 0, 0.22, 0.56, 1.0)
    disc(a, "gold", 0, 0, 0.4, 0.98, 1.12)
    disc(a, "gold", 0, 0, 0.9, 1.1, 1.26)  # чаша
    for s in (1, -1):  # ручки кубка
        chain(a, ["gold"], [(s * 0.88, 0, 1.2), (s * 1.3, 0, 1.3), (s * 1.38, 0, 1.75), (s * 1.12, 0, 2.0)], 0.13,
              grow=0.06)
    # бургер слоями
    disc(a, "bun", 0, 0, 1.0, 1.24, 1.52)
    disc(a, "patty", 0, 0, 1.1, 1.5, 1.82)
    a.prism("cheese", ngon(0, 0, 1.2, 4, math.pi / 4 + 0.2), 1.8, 1.9)  # квадрат сыра наискосок
    for ang in (0.2, 1.77, 3.34, 4.91):  # капли сыра на углах
        x, y = 1.12 * math.cos(ang + math.pi / 4), 1.12 * math.sin(ang + math.pi / 4)
        a.box("cheese", x - 0.1, x + 0.1, y - 0.1, y + 0.1, 1.62, 1.8)
    disc(a, "lettuce", 0, 0, 1.14, 1.88, 1.98, n=12)
    disc(a, "tomato", 0, 0, 1.04, 1.96, 2.08)
    disc(a, "bun", 0, 0, 1.06, 2.06, 2.4)
    disc(a, "bun", 0, 0, 0.82, 2.38, 2.6)
    disc(a, "bun2", 0, 0, 0.44, 2.58, 2.7)
    for x, y, z in ((-0.5, -0.66, 2.3), (0.3, -0.85, 2.2), (0.75, -0.55, 2.32), (-0.2, -0.6, 2.52),
                    (0.35, -0.45, 2.55), (-0.8, -0.2, 2.25)):
        a.box("seed", x - 0.07, x + 0.07, y - 0.04, y + 0.04, z - 0.04, z + 0.04, matrix=tilt((x, y, z), "Z", 30))
    for x, y in ((-0.25, 0.1), (0.2, -0.15), (0.0, 0.3)):
        a.box("seed", x - 0.07, x + 0.07, y - 0.04, y + 0.04, 2.69, 2.73, bevel=0, matrix=tilt((x, y, 2.7), "Z", 40))
    return a


# ── 8. Кристальный хот-дог: сосиска из розовых кристаллов над булкой, грани светлее и темнее, горчица ─────────


def crystal_hotdog():
    a = S.Art("Art_CrystalHotDog", ring_z0=0.4)
    a.paint("velvet", "2F6BD8", rings=True)
    a.paint("bun", "E39A43", rings=True)
    for key, code in (("tassel", "F2C230"), ("gem", "FF4F7B"), ("gem2", "FFC2D4"), ("gem3", "C8164E"),
                      ("mustard", "FFD12E"), ("shine", "FFFFFF"), ("bun2", "C77A2A"), ("wood", "4A2C1C")):
        a.paint(key, code)
    a.box("wood", -1.5, 1.5, -0.85, 0.85, 0.0, 0.26)
    top = cushion(a, "velvet", 2.6, 1.4, 0.24, 0.3, tassel="tassel")
    # булка: две низкие половинки по бокам сосиски
    for s in (1, -1):
        y0, y1 = sorted((s * 0.12, s * 0.52))
        a.box("bun", -1.15, 1.15, y0, y1, top, top + 0.46)
        a.box("bun2", -1.05, 1.05, y0 + 0.04 * s, y1 - 0.04 * s, top + 0.44, top + 0.52)
    # сосиска-кристалл: шестигранник вдоль x (ребро сверху), светлая верхняя грань, тёмная передняя, острые концы
    r, cz = 0.36, top + 0.56
    a.prism("gem", ngon(cz, 0, r, 6, 0), -1.25, 1.25, axis="x")
    fc = Vector((0, -0.433 * r, cz + 0.75 * r))  # середина верхней передней грани
    a.box("gem2", -1.15, 1.15, -0.1, 0.1, -0.015, 0.015, bevel=0,
          matrix=Matrix.Translation(fc + Vector((0, -0.5, 0.866)) * 0.008) @ Matrix.Rotation(math.radians(30), 4, "X"))
    a.box("gem3", -1.15, 1.15, -r * 0.866 - 0.03, -r * 0.866 + 0.01, cz - 0.1, cz + 0.1, bevel=0)
    for s in (1, -1):
        a.frustum("gem", (-r * 0.86, r * 0.86, -r * 0.86, r * 0.86), (0, 0, 0, 0), s * 1.25, s * 1.66, axis="x",
                  bevel=0, matrix=Matrix.Translation((0, 0, cz)))
    # горчица зигзагом по гребню
    pts = [(-0.95 + 0.24 * i, 0.1 if i % 2 == 0 else -0.1, cz + r + 0.02) for i in range(9)]
    chain(a, ["mustard"], pts, 0.11, 0.07, grow=0.04)
    sparkle(a, "shine", (-0.6, -0.4, cz + 0.1), 0.26)
    sparkle(a, "shine", (1.35, -0.2, cz + 0.6), 0.3)
    sparkle(a, "shine", (-1.3, -0.2, cz + 0.7), 0.22)
    return a


# ── 9. Робо-утёнок: жёлтый механический утёнок на колёсах, заводной ключ, антенна, глаз-линза ────────────────


def robo_duck():
    a = S.Art("Art_RoboDuck", ring_z0=1.1)
    a.paint("duck", "FFD12E", rings=True)
    for key, code in (("beak", "FF8A1F"), ("metal", "B8C2CC"), ("metal2", "7D8790"), ("bolt", "5A6270"),
                      ("eye", "15161C"), ("glint", "FFFFFF"), ("lens", "E53935"), ("lens2", "FF9A8A"),
                      ("tire", "2B2B33"), ("gold", "F2C230"), ("bulb", "4FE3F0"), ("cheek", "FF9A6A")):
        a.paint(key, code)
    # колёса с колпаками
    for x, y in ((-0.6, -0.42), (0.6, -0.42), (-0.6, 0.42), (0.6, 0.42)):
        sgn = 1 if x > 0 else -1
        x0, x1 = sorted((sgn * 0.55, sgn * 0.72))
        disc(a, "tire", 0.28, y, 0.28, x0, x1, axis="x")
        h0, h1 = (x0, x1 + 0.03) if sgn > 0 else (x0 - 0.03, x1)
        disc(a, "metal", 0.28, y, 0.12, h0, h1, axis="x")
    a.box("metal2", -0.6, 0.6, -0.55, 0.55, 0.22, 0.4)  # шасси
    # тело-утка: корпус, хвост, грудь
    a.box("duck", -0.7, 0.7, -0.6, 0.6, 0.38, 1.3)
    a.box("duck", -0.55, 0.55, 0.5, 0.95, 0.9, 1.5)  # хвостик вверх
    a.box("duck", -0.45, 0.45, 0.85, 1.05, 1.3, 1.62)
    # металлические панели с болтами (крыло)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.7, s * 0.78))
        a.box("metal", x0, x1, -0.35, 0.45, 0.6, 1.15)
        for y in (-0.25, 0.35):
            for z in (0.7, 1.05):
                x2 = s * 0.8
                a.box("bolt", min(x2, s * 0.77), max(x2, s * 0.77), y - 0.04, y + 0.04, z - 0.04, z + 0.04, bevel=0)
    # голова, клюв, глаза: один обычный, другой — красная линза
    a.box("duck", -0.48, 0.48, -0.78, 0.02, 1.28, 2.1)
    a.box("beak", -0.32, 0.32, -1.12, -0.7, 1.42, 1.62)
    a.box("beak", -0.26, 0.26, -1.06, -0.72, 1.32, 1.44)
    a.box("eye", 0.12, 0.34, -0.83, -0.77, 1.74, 1.96, bevel=0)
    a.box("glint", 0.25, 0.31, -0.85, -0.82, 1.86, 1.92, bevel=0)
    disc(a, "metal", -0.24, 1.84, 0.18, -0.86, -0.76, axis="y")
    disc(a, "lens", -0.24, 1.84, 0.12, -0.9, -0.84, axis="y")
    a.box("lens2", -0.3, -0.24, -0.92, -0.89, 1.86, 1.92, bevel=0)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.26, s * 0.42))
        a.box("cheek", x0, x1, -0.81, -0.77, 1.48, 1.58, bevel=0)
    # антенна с лампочкой и заводной ключ сзади
    a.box("metal2", -0.04, 0.04, -0.4, -0.32, 2.08, 2.5, bevel=0)
    disc(a, "bulb", 0, -0.36, 0.11, 2.48, 2.66)
    a.box("gold", -0.06, 0.06, 0.94, 1.3, 0.85, 0.97)
    a.prism("gold", S.octagon(-0.4, 0.4, 0.62, 1.2, 0.12), 1.28, 1.38, axis="y")
    return a


# ── 10. Магическая газировка: банка в розовом с молнией, полосатая трубочка, радужная шипучка фонтаном ────────


def magic_soda():
    a = S.Art("Art_MagicSoda", ring_z0=1.2)
    a.paint("can", "E040A0", rings=True)
    for key, code in (("rim", "C9D3DD"), ("rim2", "8A96A6"), ("bolt", "FFD12E"), ("label", "FFFFFF"),
                      ("straw", "FFFFFF"), ("straw2", "E53935"), ("r1", "FF4F4F"), ("r2", "FF9A1F"),
                      ("r3", "FFE14A"), ("r4", "4FD86A"), ("r5", "4FB8FF"), ("r6", "A06BFF"), ("shine", "FFFFFF"),
                      ("puddle", "4FB8FF"), ("star", "FFF6C8")):
        a.paint(key, code)
    disc(a, "puddle", 0.1, 0, 0.95, 0.0, 0.06, n=10)
    disc(a, "rim2", 0, 0, 0.66, 0.04, 0.2)
    disc(a, "can", 0, 0, 0.72, 0.18, 2.1)
    disc(a, "rim", 0, 0, 0.66, 2.08, 2.26)
    disc(a, "rim2", 0, 0, 0.5, 2.24, 2.28, bevel=0)
    # этикетка: белая полоса и молния
    a.box("label", -0.42, 0.42, -0.74, -0.68, 0.7, 1.7, bevel=0)
    a.pixels(BOLT, {"#": ("bolt", 0.025)}, 0.15, -0.3, 1.62, "xz", 0.74)
    a.box("shine", -0.6, -0.5, -0.66, -0.56, 0.4, 1.9, bevel=0, matrix=tilt((-0.55, -0.61, 1.15), "Z", -30))
    # трубочка
    for i in range(4):
        z0 = 2.2 + i * 0.32
        bar(a, "straw" if i % 2 == 0 else "straw2", (0.28 + i * 0.06, 0, z0), (0.28 + (i + 1) * 0.06, 0, z0 + 0.32),
            0.14 + 0.012 * (i % 2))
    bar(a, "straw", (0.52, 0, 3.48), (0.82, 0, 3.66), 0.15)
    # шипучка: радужные кубики-пузыри фонтаном
    bubbles = [(-0.2, -0.1, 2.36, 0.34, "r5"), (0.0, 0.2, 2.5, 0.3, "r4"), (-0.35, 0.15, 2.66, 0.28, "r6"),
               (-0.15, -0.2, 2.86, 0.3, "r3"), (-0.45, -0.1, 3.06, 0.26, "r2"), (-0.1, 0.1, 3.16, 0.24, "r1"),
               (-0.6, 0.05, 3.32, 0.2, "r5"), (-0.3, -0.15, 3.5, 0.18, "r4"), (-0.75, -0.1, 3.6, 0.16, "r6"),
               (0.1, -0.15, 3.42, 0.16, "r2")]
    for x, y, z, s, key in bubbles:
        a.box(key, x - s / 2, x + s / 2, y - s / 2, y + s / 2, z - s / 2, z + s / 2, matrix=tilt((x, y, z), "Z", 20))
    sparkle(a, "star", (0.75, -0.3, 2.9), 0.3)
    sparkle(a, "star", (-1.0, -0.3, 2.4), 0.24)
    return a


# ── 11. Монстр-радио: красное ретро-радио, динамики-глаза под бровями, зубастая решётка, ручка, антенна ──────


def monster_radio():
    a = S.Art("Art_MonsterRadio", ring_z0=1.2)
    a.paint("body", "D8352A", rings=True)
    for key, code in (("trim", "F2E2C4"), ("speaker", "2B2B33"), ("white", "FFFFFF"), ("pupil", "15161C"),
                      ("brow", "15161C"), ("grille", "3A2418"), ("tooth", "FFFFFF"), ("gold", "F2C230"),
                      ("dial", "FFE9A8"), ("needle", "E53935"), ("metal", "B8C2CC"), ("foot", "2B2B33"),
                      ("glint", "FFFFFF")):
        a.paint(key, code)
    for x in (-0.95, 0.95):
        a.box("foot", x - 0.16, x + 0.16, -0.45, 0.45, 0.0, 0.18)
    a.box("body", -1.25, 1.25, -0.6, 0.6, 0.16, 1.9)
    a.box("body", -1.05, 1.05, -0.6, 0.6, 1.88, 2.16)  # скруглённый верх ступенькой
    a.box("trim", -1.27, 1.27, -0.62, 0.62, 0.16, 0.3)
    # глаза-динамики с бровями
    for s in (1, -1):
        disc(a, "speaker", s * 0.62, 1.38, 0.42, -0.68, -0.6, axis="y")
        disc(a, "white", s * 0.62, 1.38, 0.32, -0.72, -0.67, axis="y")
        disc(a, "pupil", s * 0.56, 1.32, 0.15, -0.76, -0.71, axis="y")
        a.box("glint", s * 0.56 + 0.03, s * 0.56 + 0.09, -0.78, -0.75, 1.38, 1.44, bevel=0)
        b0, b1 = sorted((s * 0.25, s * 1.0))
        a.box("brow", b0, b1, -0.72, -0.62, 1.82, 1.94, matrix=tilt((s * 0.62, -0.67, 1.88), "Y", -s * 14))
    # шкала-нос
    a.box("dial", -0.24, 0.24, -0.68, -0.6, 1.0, 1.24)
    a.box("needle", -0.02, 0.02, -0.7, -0.67, 1.04, 1.2, bevel=0)
    # рот-решётка с зубами
    a.box("grille", -0.9, 0.9, -0.68, -0.6, 0.4, 0.86)
    for x in (-0.7, -0.42, -0.14, 0.14, 0.42, 0.7):
        a.frustum("tooth", (x - 0.11, x + 0.11, -0.72, -0.66), (x, x, -0.69, -0.69), 0.84, 0.62, bevel=0)
    for x in (-0.55, 0.0, 0.55):
        a.frustum("tooth", (x - 0.09, x + 0.09, -0.72, -0.66), (x, x, -0.69, -0.69), 0.42, 0.6, bevel=0)
    # ручки-уши по бокам
    for s in (1, -1):
        x0, x1 = sorted((s * 1.24, s * 1.42))
        disc(a, "gold", 1.1, 0, 0.2, x0, x1, axis="x")
    # ручка для переноски и антенна
    a.box("metal", -0.62, -0.5, -0.08, 0.08, 2.14, 2.6)
    a.box("metal", 0.5, 0.62, -0.08, 0.08, 2.14, 2.6)
    a.box("metal", -0.62, 0.62, -0.08, 0.08, 2.58, 2.7)
    chain(a, ["metal"], [(0.85, 0.2, 2.1), (1.15, 0.2, 2.9), (1.0, 0.2, 3.3)], 0.06, grow=0.03)
    disc(a, "needle", 1.0, 0.2, 0.08, 3.28, 3.42)
    return a


# ── 12. Карманный сейф: толстый сейф с кодовым колесом, золотые ножки, из двери торчат купюры, монеты сверху ──


def pocket_safe():
    a = S.Art("Art_PocketSafe", ring_z0=1.1)
    a.paint("steel", "3E6B9E", rings=True)
    for key, code in (("door", "4A7BB0"), ("dark", "1E2A3A"), ("dial", "D6DCE6"), ("tick", "2B2B33"),
                      ("gold", "F2C230"), ("gold2", "C9921A"), ("money", "4CAF50"), ("money2", "2E7D32"),
                      ("handle", "E8B530"), ("shine", "FFFFFF")):
        a.paint(key, code)
    for x in (-0.82, 0.82):
        for y in (-0.6, 0.6):
            disc(a, "gold", x, y, 0.14, 0.0, 0.2)
    a.box("steel", -1.05, 1.05, -0.85, 0.85, 0.18, 2.1)
    a.box("dark", -0.86, 0.86, -0.89, -0.84, 0.36, 1.92, bevel=0)  # щель двери
    a.box("door", -0.82, 0.82, -0.98, -0.84, 0.4, 1.88)
    for z in (0.62, 1.66):  # петли слева
        a.box("gold2", -0.95, -0.82, -1.0, -0.86, z - 0.14, z + 0.14)
    # кодовое колесо с рисками
    disc(a, "dial", 0.0, 1.26, 0.38, -1.08, -0.96, axis="y")
    disc(a, "tick", 0.0, 1.26, 0.12, -1.12, -1.06, axis="y")
    for i in range(8):
        ang = i * math.pi / 4
        x, z = 0.3 * math.cos(ang), 1.26 + 0.3 * math.sin(ang)
        a.box("tick", x - 0.025, x + 0.025, -1.1, -1.07, z - 0.025, z + 0.025, bevel=0)
    # ручка-штурвал
    a.box("handle", 0.38, 0.72, -1.08, -0.98, 0.66, 0.76)
    a.box("handle", 0.5, 0.6, -1.1, -0.98, 0.54, 0.88)
    # купюры из щели справа и сверху сейфа
    for i, (z, ang) in enumerate(((0.9, -12), (1.15, 8), (1.42, -6))):
        a.box("money" if i % 2 == 0 else "money2", 0.8, 1.55, -0.9 - 0.02 * i, -0.5 + 0.02 * i, z - 0.05, z + 0.05,
              matrix=tilt((0.95, -0.7, z), "Y", ang))
    # стопки монет на крыше
    for x, y, h in ((-0.5, -0.2, 3), (-0.1, 0.25, 5), (0.45, -0.1, 2)):
        for k in range(h):
            disc(a, "gold" if k % 2 == 0 else "gold2", x + 0.02 * (k % 2), y, 0.24, 2.1 + k * 0.1, 2.2 + k * 0.1)
    a.box("shine", -0.75, -0.6, -1.0, -0.97, 1.4, 1.8, bevel=0)
    return a


# ══ RARE ═════════════════════════════════════════════════════════════════════════════════════════════════════

# ── 13. Живой сундук-мимик: открытая пасть с клыками, глаза на крышке, длинный язык до земли, рассыпанные монеты ──


def mimic_chest():
    a = S.Art("Art_MimicChest", ring_z0=0.6)
    a.paint("wood", "8A4E2B", rings=True)
    for key, code in (("gold", "F2C230"), ("gold2", "C9921A"), ("mouth", "5A1020"), ("tooth", "FFFFFF"),
                      ("tongue", "F0607A"), ("tongue2", "C8405A"), ("eye", "FFD84A"), ("pupil", "15161C"),
                      ("brow", "3A2214"), ("glint", "FFFFFF"), ("dark", "3A2214")):
        a.paint(key, code)
    # корпус: низ, золотая окантовка, края пасти, тёмная глотка
    a.box("gold2", -1.14, 1.14, -0.76, 0.76, 0.0, 0.14)
    a.box("wood", -1.1, 1.1, -0.72, 0.72, 0.12, 0.92)
    a.frame("wood", [(-1.1, -0.72), (1.1, -0.72), (1.1, 0.72), (-1.1, 0.72)], 0.14, 0.9, 1.14, axis="z")
    a.box("mouth", -0.97, 0.97, -0.59, 0.59, 0.86, 1.0, bevel=0)
    for x in (-0.74, 0.74):  # кованые полосы
        a.box("gold", x - 0.1, x + 0.1, -0.78, 0.78, 0.1, 1.16)
    a.prism("gold", S.octagon(-0.2, 0.2, 0.44, 0.84, 0.08), -0.8, -0.72, axis="y")  # замок
    a.box("dark", -0.05, 0.05, -0.82, -0.79, 0.52, 0.72, bevel=0)
    for x in (-0.82, -0.5, -0.2, 0.15, 0.45, 0.8):  # нижние клыки
        a.frustum("tooth", (x - 0.09, x + 0.09, -0.66, -0.52), (x, x, -0.59, -0.59), 1.12, 1.38, bevel=0)
    # крышка открыта на 42° вокруг задней петли
    a.transform = tilt((0, 0.72, 1.14), "X", -42)
    a.box("wood", -1.12, 1.12, -0.74, 0.74, 1.14, 1.5)
    a.box("wood", -1.0, 1.0, -0.62, 0.62, 1.48, 1.72)
    for x in (-0.74, 0.74):
        a.box("gold", x - 0.11, x + 0.11, -0.79, 0.79, 1.12, 1.52)
        a.box("gold", x - 0.08, x + 0.08, -0.66, 0.66, 1.5, 1.74)
    a.box("mouth", -0.98, 0.98, -0.6, 0.6, 1.1, 1.16, bevel=0)  # нёбо
    for x in (-0.66, -0.33, 0.0, 0.33, 0.66):  # верхние клыки
        a.frustum("tooth", (x - 0.1, x + 0.1, -0.68, -0.5), (x, x, -0.59, -0.59), 1.16, 0.86, bevel=0)
    for s in (1, -1):  # жёлтые глаза со зрачками-щёлочками и злые брови на крышке
        x0, x1 = sorted((s * 0.16, s * 0.56))
        a.box("eye", x0, x1, -0.8, -0.73, 1.2, 1.46)
        p0, p1 = sorted((s * 0.33, s * 0.39))
        a.box("pupil", p0, p1, -0.83, -0.79, 1.22, 1.44, bevel=0)
        a.box("glint", s * 0.45 - 0.03, s * 0.45 + 0.03, -0.84, -0.8, 1.36, 1.42, bevel=0)
        a.box("brow", x0 - 0.02, x1 + 0.02, -0.82, -0.74, 1.5, 1.58, matrix=tilt((s * 0.36, -0.78, 1.54), "Y", -s * 16))
    a.transform = None
    # язык из пасти до земли
    chain(a, ["tongue", "tongue2"], [(0.0, -0.2, 1.0), (0.05, -0.78, 1.16), (0.12, -1.18, 0.84), (0.0, -1.4, 0.36),
                                     (-0.26, -1.62, 0.08)], 0.46, 0.13, grow=0.08)
    # монеты
    for x, y, h in ((-1.25, -0.95, 2), (1.3, -0.7, 3), (0.75, -1.15, 1), (-0.7, -1.3, 1), (1.35, 0.4, 1)):
        for k in range(h):
            disc(a, "gold" if k % 2 == 0 else "gold2", x + 0.03 * (k % 2), y, 0.17, k * 0.08, k * 0.08 + 0.08)
    return a


# ── 14. Зеркало-портал: резная золотая рама на ножке, внутри закручен фиолетово-розовый вихрь ────────────────


def portal_mirror():
    a = S.Art("Art_PortalMirror", ring_z0=2.3)
    a.paint("gold", "F2C230", rings=True)
    a.paint("wood", "4A2C5E", rings=True)
    for key, code in (("gold2", "C9921A"), ("back", "2A1840"), ("p1", "3B1A6E"), ("p2", "7A3FD8"), ("p3", "E040A0"),
                      ("p4", "4FE3F0"), ("p5", "FFFFFF"), ("gem", "4FE3F0"), ("gem2", "E040A0"), ("star", "FFF6C8")):
        a.paint(key, code)
    # подставка: полоз и стойки по бокам
    a.box("wood", -1.3, 1.3, -0.6, 0.6, 0.0, 0.22)
    for s in (1, -1):
        x0, x1 = sorted((s * 1.0, s * 1.22))
        a.box("wood", x0, x1, -0.16, 0.16, 0.2, 2.6)
        a.prism("gold", S.octagon(x0 - 0.04, x1 + 0.04, 2.56, 2.86, 0.08), -0.2, 0.2, axis="y")
    # рама-восьмиугольник
    outer = S.octagon(-0.98, 0.98, 0.32, 4.0, 0.5)
    a.frame("gold", outer, 0.26, -0.2, 0.2, axis="y")
    a.prism("back", S.octagon(-0.8, 0.8, 0.5, 3.82, 0.4), 0.02, 0.16, axis="y")
    # вихрь: кольца-восьмиугольники, каждое меньше и повёрнуто, ближе к зрителю
    cz = 2.16
    for i, key in enumerate(("p1", "p2", "p3", "p2", "p4", "p3")):
        k = 0.78 - i * 0.12
        pts = [(x * k, cz + (z - cz) * k) for x, z in outer]
        a.frame(key, pts, 0.11, -0.02 - 0.03 * i, 0.04 + 0.01 * i, axis="y", matrix=tilt((0, 0, cz), "Y", 17 * (i + 1)))
    disc(a, "p5", 0, cz, 0.16, -0.24, 0.0, axis="y")
    # навершие: корона из лучей и большой камень; камни по бокам и внизу
    a.box("gold", -0.5, 0.5, -0.18, 0.18, 3.94, 4.14)
    for i, ang in enumerate((-50, -25, 0, 25, 50)):
        r = math.radians(ang)
        bar(a, "gold2", (0.0, 0.0, 4.0), (0.85 * math.sin(r), 0.0, 4.0 + 0.85 * math.cos(r)), 0.12 + 0.012 * i, 0.2)
    disc(a, "gem", 0, 4.4, 0.24, -0.26, -0.12, axis="y")
    for s in (1, -1):
        disc(a, "gem2", s * 0.8, 2.16, 0.13, -0.26, -0.16, axis="y")
    disc(a, "gem2", 0, 0.42, 0.13, -0.26, -0.16, axis="y")
    sparkle(a, "star", (-1.45, -0.2, 3.5), 0.34)
    sparkle(a, "star", (1.5, -0.2, 1.4), 0.28)
    return a


# ── 15. Всевидящее око: огромный глаз в золотой оправе-шестерне с лучами, на бархатной колонне ──────────────


def all_seeing_eye():
    a = S.Art("Art_AllSeeingEye", ring_z0=0.6)
    a.paint("velvet", "4A2C8A", rings=True)
    a.paint("gold", "F2C230", rings=True)
    for key, code in (("gold2", "C9921A"), ("white", "F6F4EE"), ("iris", "2E7BEF"), ("iris2", "7FC4FF"),
                      ("pupil", "15161C"), ("glint", "FFFFFF"), ("vein", "E5534B"), ("ray", "FFE14A"),
                      ("lid", "8E44D9")):
        a.paint(key, code)
    a.box("velvet", -0.9, 0.9, -0.8, 0.8, 0.0, 0.3)
    a.box("gold2", -0.74, 0.74, -0.64, 0.64, 0.28, 0.4)
    disc(a, "velvet", 0, 0, 0.36, 0.38, 1.1)
    a.box("gold", -0.5, 0.5, -0.36, 0.36, 1.08, 1.2)
    cz = 2.25
    # лучи за глазом
    for i in range(10):
        r = math.radians(i * 36 + 18)
        p0 = (0.95 * math.cos(r), 0.24, cz + 0.95 * math.sin(r))
        p1 = (1.55 * math.cos(r), 0.24, cz + 1.55 * math.sin(r))
        bar(a, "ray", p0, p1, 0.22 if i % 2 else 0.16, 0.1 + 0.01 * (i % 2))
    # оправа-шестерня
    a.frame("gold", ngon(0, cz, 1.12, 16), 0.2, -0.18, 0.18, axis="y")
    for i in range(16):
        r = 2 * math.pi * i / 16
        c = Vector((1.18 * math.cos(r), 0, cz + 1.18 * math.sin(r)))
        a.box("gold2", -0.1, 0.1, -0.12 - 0.005 * (i % 2), 0.12, -0.08, 0.08,
              matrix=Matrix.Translation(c) @ Matrix.Rotation(-r, 4, "Y"))
    # держатели к колонне
    for s in (1, -1):
        bar(a, "gold", (s * 0.4, 0, 1.15), (s * 0.82, 0, 1.55), 0.16)
    # глазное яблоко из восьмигранных слоёв
    for r, z0, z1 in ((0.5, cz - 0.86, cz - 0.7), (0.76, cz - 0.72, cz - 0.42), (0.88, cz - 0.44, cz + 0.44),
                      (0.76, cz + 0.42, cz + 0.72), (0.5, cz + 0.7, cz + 0.86)):
        disc(a, "white", 0, 0, r, z0, z1)
    disc(a, "iris", 0, cz, 0.46, -0.86, -0.8, axis="y")
    disc(a, "iris2", 0, cz, 0.32, -0.88, -0.84, axis="y")
    disc(a, "pupil", 0, cz, 0.2, -0.91, -0.86, axis="y")
    a.box("glint", 0.1, 0.22, -0.94, -0.9, cz + 0.12, cz + 0.24, bevel=0)
    for x0, z0, x1, z1 in ((-0.6, cz - 0.1, -0.42, cz - 0.02), (0.44, cz + 0.06, 0.62, cz + 0.12),
                           (0.42, cz - 0.3, 0.58, cz - 0.4)):
        bar(a, "vein", (x0, -0.83, z0), (x1, -0.83, z1), 0.04, 0.03, bevel=0)
    # тяжёлое веко сверху — взгляд с прищуром
    a.box("lid", -0.84, 0.84, -0.86, 0.4, cz + 0.5, cz + 0.68)
    a.box("lid", -0.62, 0.62, -0.7, 0.3, cz + 0.66, cz + 0.84)
    return a


# ── 16. Королевская утка: большая жёлтая утка в короне и красной мантии с горностаем, скипетр под крылом ─────

ERMINE = ["#..#..#..#..#..#..#",
          "...................",
          ".#..#..#..#..#..#.."]


def royal_duck():
    a = S.Art("Art_RoyalDuck", ring_z0=1.2)
    a.paint("duck", "FFD12E", rings=True)
    a.paint("velvet", "6B3FB8", rings=True)
    a.paint("mantle", "C62828", rings=True)
    for key, code in (("tassel", "F2C230"), ("ermine", "FBFBF5"), ("spot", "15161C"), ("beak", "FF8A1F"),
                      ("eye", "15161C"), ("glint", "FFFFFF"), ("gold", "F2C230"), ("ruby", "E53935"),
                      ("sapphire", "2E5BD8"), ("emerald", "2E9E4F"), ("cheek", "FF9A6A")):
        a.paint(key, code)
    top = cushion(a, "velvet", 2.2, 1.7, 0.0, 0.34, tassel="tassel")
    # тело и хвост
    a.box("duck", -0.82, 0.82, -0.7, 0.76, top, top + 1.1)
    a.box("duck", -0.6, 0.6, 0.6, 1.0, top + 0.6, top + 1.3)
    # мантия: спинка и бока, белая горностаевая кайма снизу и спереди
    a.box("mantle", -0.9, 0.9, -0.3, 0.84, top + 0.14, top + 1.2)
    a.box("mantle", -0.72, 0.72, 0.4, 0.94, top + 1.18, top + 1.4)
    a.box("ermine", -0.94, 0.94, -0.34, 0.88, top - 0.02, top + 0.2)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.88, s * 0.96))
        a.box("ermine", x0, x1, -0.38, -0.24, top + 0.18, top + 1.2)
    a.pixels(ERMINE, {"#": ("spot", 0.02)}, 0.1, 0.95, top + 0.17, "xz", 0.88, sides=(1,), flip=True)
    a.box("ermine", -0.66, 0.66, -0.5, 0.02, top + 1.12, top + 1.3)  # воротник
    # голова, клюв, глаза, щёки
    a.box("duck", -0.55, 0.55, -0.82, 0.08, top + 1.24, top + 2.12)
    a.box("beak", -0.38, 0.38, -1.2, -0.75, top + 1.38, top + 1.6)
    a.box("beak", -0.3, 0.3, -1.12, -0.78, top + 1.28, top + 1.4)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.14, s * 0.36))
        a.box("eye", x0, x1, -0.86, -0.8, top + 1.7, top + 1.94, bevel=0)
        g = 0.3 if s > 0 else -0.2
        a.box("glint", g - 0.03, g + 0.03, -0.88, -0.85, top + 1.84, top + 1.9, bevel=0)
        x0, x1 = sorted((s * 0.36, s * 0.52))
        a.box("cheek", x0, x1, -0.85, -0.8, top + 1.5, top + 1.63, bevel=0)
    # корона: обруч, пять зубцов, камни
    a.box("gold", -0.5, 0.5, -0.62, 0.0, top + 2.1, top + 2.36)
    for x in (-0.42, -0.21, 0.0, 0.21, 0.42):
        h = 0.48 if x == 0.0 else 0.34
        a.frustum("gold", (x - 0.09, x + 0.09, -0.4, -0.22), (x, x, -0.31, -0.31), top + 2.34, top + 2.34 + h, bevel=0)
    for x, key in ((-0.27, "sapphire"), (0.0, "ruby"), (0.27, "emerald")):
        a.box(key, x - 0.08, x + 0.08, -0.66, -0.61, top + 2.16, top + 2.3, bevel=0)
    # крыло-рука со скипетром справа
    a.box("duck", -0.98, -0.8, -0.5, 0.3, top + 0.4, top + 1.0)
    bar(a, "gold", (-1.12, -0.6, top + 0.1), (-1.0, -0.42, top + 2.0), 0.1)
    disc(a, "gold", -1.0, -0.42, 0.18, top + 2.0, top + 2.32)
    disc(a, "ruby", -1.0, -0.42, 0.12, top + 2.3, top + 2.46)
    return a


# ── 17. Цветок-монстр: терракотовый горшок, листья-руки, малиновые лепестки, зубастая пасть с языком ─────────


def monster_flower():
    a = S.Art("Art_MonsterFlower", ring_z0=0.5)
    a.paint("pot", "C8643A", rings=True)
    for key, code in (("pot2", "A84E2A"), ("soil", "3A2418"), ("stem", "3FA34A"), ("leaf", "5FBF3A"),
                      ("leaf2", "3E8E2E"), ("petal", "E040A0"), ("petal2", "FF7AC8"), ("head", "B8E04A"),
                      ("mouth", "5A1020"), ("tooth", "FFFFFF"), ("tongue", "F0607A"), ("eye", "FFFFFF"),
                      ("pupil", "15161C"), ("claw", "F2E2C4")):
        a.paint(key, code)
    # горшок: расширяется кверху, бортик, земля
    a.frustum("pot", (-0.55, 0.55, -0.55, 0.55), (-0.7, 0.7, -0.7, 0.7), 0.0, 0.95)
    a.box("pot2", -0.78, 0.78, -0.78, 0.78, 0.92, 1.18)
    a.box("soil", -0.66, 0.66, -0.66, 0.66, 1.16, 1.24, bevel=0)
    # стебель S-образно
    chain(a, ["stem"], [(0.0, 0.0, 1.2), (0.12, 0.0, 1.7), (-0.05, 0.0, 2.2), (0.0, -0.05, 2.5)], 0.24, grow=0.06)
    # листья-руки с когтями
    for s in (1, -1):
        bar(a, "leaf", (s * 0.08, 0, 1.6), (s * 0.85, -0.2, 2.1), 0.22, 0.14)
        bar(a, "leaf2", (s * 0.8, -0.18, 2.06), (s * 1.08, -0.3, 2.5), 0.32, 0.12)
        for d in (-0.1, 0.1):
            a.frustum("claw", (s * 1.08 + d - 0.05, s * 1.08 + d + 0.05, -0.36, -0.26),
                      (s * 1.1 + d, s * 1.1 + d, -0.31, -0.31), 2.52, 2.72, bevel=0)
    # голова: малиновые лепестки кольцом, лайм-голова, пасть
    cz = 3.05
    for i in range(10):
        r = 2 * math.pi * i / 10
        c = Vector((0.82 * math.cos(r), 0.08, cz + 0.82 * math.sin(r)))
        a.box("petal" if i % 2 == 0 else "petal2", -0.3, 0.3, -0.06 - 0.01 * (i % 2), 0.06 + 0.012 * (i % 2), -0.18, 0.18,
              matrix=Matrix.Translation(c) @ Matrix.Rotation(-r, 4, "Y"))
    disc(a, "head", 0, cz, 0.66, -0.22, 0.2, axis="y")
    disc(a, "mouth", 0, cz - 0.12, 0.44, -0.27, -0.2, axis="y")
    for x in (-0.28, -0.1, 0.1, 0.28):
        a.frustum("tooth", (x - 0.07, x + 0.07, -0.31, -0.25), (x, x, -0.28, -0.28), cz + 0.2, cz + 0.02, bevel=0)
    for x in (-0.2, 0.0, 0.2):
        a.frustum("tooth", (x - 0.07, x + 0.07, -0.31, -0.25), (x, x, -0.28, -0.28), cz - 0.44, cz - 0.26, bevel=0)
    a.box("tongue", -0.16, 0.16, -0.36, -0.26, cz - 0.52, cz - 0.3)
    a.box("tongue", -0.12, 0.12, -0.42, -0.3, cz - 0.7, cz - 0.5)
    for s in (1, -1):  # глаза над пастью
        disc(a, "eye", s * 0.24, cz + 0.36, 0.14, -0.28, -0.2, axis="y")
        disc(a, "pupil", s * 0.21, cz + 0.33, 0.07, -0.31, -0.27, axis="y")
    return a


# ── 18. Мир в бутылке: бутылка на деревянной подставке, внутри море, остров с пальмой и маяк ─────────────────


def world_in_bottle():
    a = S.Art("Art_WorldInBottle", ring_z0=0.4)
    a.paint("wood", "8A5A3A", rings=True)
    for key, code in (("glass", "A8E6F0"), ("shine", "FFFFFF"), ("cork", "C9925A"), ("sea", "2E7BEF"),
                      ("sea2", "4FB8FF"), ("sand", "F2D38A"), ("trunk", "8A5A12"), ("palm", "3FBF5A"),
                      ("palm2", "2E9E4F"), ("white", "FFFFFF"), ("red", "E53935"), ("light", "FFE14A")):
        a.paint(key, code)
    zc, r = 1.05, 0.72
    # подставка-люлька
    a.box("wood", -1.5, 1.5, -0.62, 0.62, 0.0, 0.16)
    for x in (-0.8, 0.6):
        a.box("wood", x - 0.12, x + 0.12, -0.55, 0.55, 0.14, 0.42)
    # стекло вдоль x: рёбра, кольца на концах, дно, горлышко, пробка
    for z, y in ngon(zc, 0, r, 8):  # точки (z, y)
        a.box("glass", -1.25, 1.0, y - 0.06, y + 0.06, z - 0.06, z + 0.06)
    for x0, x1 in ((-1.3, -1.18), (0.94, 1.06)):
        a.frame("glass", ngon(zc, 0, r + 0.07, 8), 0.14, x0, x1, axis="x")
    a.prism("glass", ngon(zc, 0, r - 0.05, 8), -1.32, -1.26, axis="x")  # дно
    for z, y in ngon(zc, 0, 0.3, 8):
        a.box("glass", 1.0, 1.55, y - 0.05, y + 0.05, z - 0.05, z + 0.05)
    a.frame("glass", ngon(zc, 0, 0.36, 8), 0.12, 1.5, 1.6, axis="x")
    disc(a, "cork", zc, 0, 0.26, 1.56, 1.84, axis="x")
    bar(a, "shine", (-0.9, -0.76, zc + 0.36), (0.4, -0.76, zc + 0.5), 0.07, 0.04, bevel=0)
    bar(a, "shine", (-0.6, -0.7, zc + 0.52), (-0.1, -0.7, zc + 0.6), 0.05, 0.04, bevel=0)
    # море и остров
    a.box("sea", -1.16, 0.92, -0.5, 0.5, zc - 0.62, zc - 0.28)
    a.box("sea2", -1.0, 0.8, -0.44, 0.44, zc - 0.3, zc - 0.24, bevel=0)
    a.box("sand", -0.75, 0.15, -0.36, 0.36, zc - 0.3, zc - 0.12)
    a.box("sand", -0.55, -0.05, -0.26, 0.26, zc - 0.14, zc - 0.02)
    chain(a, ["trunk"], [(-0.32, 0, zc - 0.04), (-0.26, 0, zc + 0.18), (-0.34, 0, zc + 0.4)], 0.09, grow=0.03)
    for ang in (0, 60, 120, 180, 240, 300):
        rr = math.radians(ang)
        bar(a, "palm" if ang % 120 == 0 else "palm2", (-0.34, 0, zc + 0.42),
            (-0.34 + 0.32 * math.cos(rr), 0.32 * math.sin(rr), zc + 0.32), 0.12, 0.04 + 0.005 * (ang // 60 % 2))
    # маяк в полоску
    for i, key in enumerate(("white", "red", "white", "red")):
        disc(a, key, 0.45, 0.05, 0.11 - i * 0.012, zc - 0.28 + i * 0.12, zc - 0.16 + i * 0.12)
    disc(a, "light", 0.45, 0.05, 0.08, zc + 0.2, zc + 0.3)
    disc(a, "red", 0.45, 0.05, 0.1, zc + 0.3, zc + 0.36)
    return a


# ── 19, 21. Картины Rare в своих рамах ─────────────────────────────────────────────────────────────────────────


def painting(name, image, cw, ch, colors, border=0.44, z=0.34, boost=3.0):
    """Картина: рама из четырёх планок border, уступ, холст cw × ch, задник, подставка с упорами и табличкой.
    colors: frame (с кольцами D39), step. Возвращает (Art, низ холста, верх рамы, полуширина рамы)."""
    a = S.Art(name, ring_z0=z + border / 2)
    a.paint("frame", colors["frame"], rings=True)
    a.paint("step", colors["step"])
    for key, code in (("wood", "4A2C1C"), ("wood2", "5E3A24"), ("back", "3A2418"), ("plate", "F2C230")):
        a.paint(key, code)
    hw = cw / 2 + border
    top = z + ch + 2 * border
    sw = min(hw + 0.3, 2.1)
    a.box("wood", -sw, sw, -0.62, 0.62, 0.0, 0.24)
    a.box("wood2", -sw + 0.07, sw - 0.07, -0.5, 0.5, 0.22, z + 0.02)
    a.box("plate", -0.55, 0.55, -0.665, -0.6, 0.05, 0.19, bevel=0)
    for x in (-hw + 0.4, hw - 0.4):
        a.prism("wood2", [(z, 0.24), (z, 0.5), (z + 1.0, 0.24)], x - 0.08, x + 0.08, axis="x")
    for s in (1, -1):
        x0, x1 = sorted((s * cw / 2, s * hw))
        a.box("frame", x0, x1, -0.25, 0.25, z, top)
    a.box("frame", -cw / 2, cw / 2, -0.25, 0.25, z, z + border)
    a.box("frame", -cw / 2, cw / 2, -0.25, 0.25, top - border, top)
    a.frame("step", [(-cw / 2 - 0.06, z + border - 0.09), (cw / 2 + 0.06, z + border - 0.09),
                     (cw / 2 + 0.06, top - border + 0.09), (-cw / 2 - 0.06, top - border + 0.09)], 0.12, -0.18, -0.03,
            axis="y")
    window = (-cw / 2 + 0.06, cw / 2 - 0.06, z + border + 0.03, top - border - 0.03)
    a.paint_image("canvas", painting_image(image, 1100), window, boost=boost)
    a.box("canvas", -cw / 2, cw / 2, -0.06, 0.06, z + border, top - border, bevel=0)
    a.box("back", -cw / 2 - 0.02, cw / 2 + 0.02, 0.04, 0.2, z + border - 0.02, top - border + 0.02, bevel=0)
    return a, z + border, top, hw


def mona_lisa():
    # окно 1.7 × 2.5 (доска 53 × 77 см): необычная золотая рама — розетки с рубинами в углах, гребень-веер с
    # изумрудом и жемчугом сверху, колонки по бокам, картуш снизу
    a, z0, top, hw = painting("Art_MonaLisa", "MonaLisa_Louvre_C2RMF.jpg", 1.7, 2.5,
                              {"frame": "E8B530", "step": "7A1E2A"})
    for key, code in (("gold2", "B8860B"), ("ruby", "E53935"), ("emerald", "2E9E4F"), ("pearl", "F6F0E1")):
        a.paint(key, code)
    zb = z0 - 0.44
    for x in (-hw + 0.22, hw - 0.22):
        for zc in (zb + 0.22, top - 0.22):
            a.prism("gold2", S.octagon(x - 0.2, x + 0.2, zc - 0.2, zc + 0.2, 0.08), -0.32, -0.24, axis="y")
            a.box("ruby", x - 0.08, x + 0.08, -0.36, -0.31, zc - 0.08, zc + 0.08, bevel=0)
    for s in (1, -1):  # колонки по бокам
        x0, x1 = sorted((s * (hw - 0.02), s * (hw + 0.14)))
        a.box("gold2", x0, x1, -0.18, 0.18, zb + 0.5, top - 0.5)
        for zc in (zb + 0.5, top - 0.5):
            a.box("frame", x0 - 0.04, x1 + 0.04, -0.22, 0.22, zc - 0.08, zc + 0.08)
    # гребень-веер с жемчужинами
    a.box("frame", -0.7, 0.7, -0.2, 0.2, top - 0.02, top + 0.2)
    for i, ang in enumerate((-60, -30, 0, 30, 60)):
        r = math.radians(ang)
        bar(a, "frame" if i % 2 == 0 else "gold2", (0, 0, top + 0.1),
            (0.75 * math.sin(r), 0, top + 0.1 + 0.75 * math.cos(r)), 0.16 + 0.015 * i, 0.25)
        disc(a, "pearl", 0.84 * math.sin(r), top + 0.1 + 0.84 * math.cos(r), 0.08, -0.14, 0.14, axis="y")
    disc(a, "emerald", 0, top + 0.42, 0.22, -0.3, -0.14, axis="y")
    # картуш снизу
    a.prism("gold2", S.octagon(-0.5, 0.5, zb - 0.06, zb + 0.3, 0.1), -0.32, -0.24, axis="y")
    a.box("pearl", -0.36, 0.36, -0.35, -0.31, zb + 0.06, zb + 0.18, bevel=0)
    return a


SWIRL = ["####.",
         "#...#",
         "#.#.#",
         "#..##",
         ".###."]


def van_gogh_self_portrait():
    # яркая объёмная рама кобальт с оранжевым уступом (цвета ван Гога), жёлтые «вихри» в углах, снизу палитра с
    # красками и кисти; окно 1.8 × 2.27 (картон 1920 × 2427)
    a, z0, top, hw = painting("Art_VanGoghSelfPortrait", "VanGoghSelfPortrait_AIC.jpg", 1.8, 2.27,
                              {"frame": "2F5BD8", "step": "FF8A1F"})
    for key, code in (("swirl", "FFD12E"), ("palette", "D9A86A"), ("p1", "E53935"), ("p2", "FFD12E"),
                      ("p3", "2E7BEF"), ("p4", "3FBF5A"), ("p5", "FFFFFF"), ("brush", "8A5A12"), ("ferrule", "C9D3DD"),
                      ("frame2", "1F3E9A")):
        a.paint(key, code)
    zb = z0 - 0.44
    for x in (-hw + 0.22, hw - 0.22):
        for zc in (zb + 0.22, top - 0.22):
            a.box("frame2", x - 0.26, x + 0.26, -0.33, -0.24, zc - 0.26, zc + 0.26)
            a.pixels(SWIRL, {"#": ("swirl", 0.025)}, 0.08, x - 0.2, zc + 0.2, "xz", 0.33)
    for s in (1, -1):  # выступы-волны по бокам
        for zc in (zb + 1.0, zb + 1.9):
            x0, x1 = sorted((s * (hw - 0.04), s * (hw + 0.16)))
            a.box("frame2", x0, x1, -0.2, 0.2, zc - 0.22, zc + 0.22)
    # палитра с красками и кисти
    a.prism("palette", S.octagon(-0.85, 0.85, -0.75, -0.25, 0.18), 0.24, 0.34, axis="z")
    for (x, y, key) in ((-0.55, -0.62, "p1"), (-0.25, -0.66, "p2"), (0.05, -0.64, "p3"), (0.35, -0.62, "p4"),
                        (0.6, -0.5, "p5")):
        a.box(key, x - 0.1, x + 0.1, y - 0.08, y + 0.08, 0.32, 0.4)
    for s, key in ((1, "p3"), (-1, "p1")):
        p0 = Vector((s * 0.3, -0.42, 0.36))
        p1 = Vector((s * 1.1, -0.95, 0.62))
        bar(a, "brush", p0, p1, 0.08)
        d = (p1 - p0).normalized()
        bar(a, "ferrule", p1 - d * 0.02, p1 + d * 0.16, 0.1)
        bar(a, key, p1 + d * 0.14, p1 + d * 0.34, 0.12)
    return a


# ── 20. Золотой микрофон: микрофон звезды на стойке, камни, цепь, светящийся подиум, ноты ─────────────────────

NOTE = [".###",
        ".#.#",
        ".#.#",
        "##.#",
        "##.."]


def golden_mic():
    a = S.Art("Art_GoldenMic", ring_z0=0.15)
    a.paint("stage", "2B2B33", rings=True)
    a.paint("gold", "F2C230", rings=True)
    for key, code in (("gold2", "C9921A"), ("light", "A06BFF"), ("bulb", "FFE14A"), ("grille", "FFF1C8"),
                      ("grille2", "B8860B"), ("gem", "BFF4FF"), ("ruby", "E53935"), ("note", "FF6FD8"),
                      ("note2", "4FE3F0"), ("shine", "FFFFFF")):
        a.paint(key, code)
    # подиум: тёмные ступени, светящееся кольцо с лампочками
    disc(a, "stage", 0, 0, 1.0, 0.0, 0.24)
    disc(a, "light", 0, 0, 0.9, 0.22, 0.3)
    for x, y in ngon(0, 0, 0.9, 8):
        a.box("bulb", x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0.28, 0.34, bevel=0)
    disc(a, "stage", 0, 0, 0.74, 0.28, 0.42)
    # стойка: основание, штанга, зажим
    disc(a, "gold", 0, 0, 0.44, 0.4, 0.5)
    disc(a, "gold2", 0, 0, 0.1, 0.48, 2.32)
    a.box("gold2", -0.13, 0.13, -0.13, 0.13, 2.26, 2.42)
    # золотая цепь вьётся вокруг штанги
    pts = [(0.14 * math.cos(t * 1.4), 0.14 * math.sin(t * 1.4) - 0.0, 0.7 + t * 0.13) for t in range(12)]
    chain(a, ["gold", "gold2"], pts, 0.07, grow=0.02)
    # микрофон наклонён к зрителю: ручка с камнями, пояс с рубинами, головка-решётка
    a.transform = tilt((0, 0, 2.34), "X", 16)
    a.prism("gold", ngon(0, 0, 0.13, 8), 2.3, 2.5)
    a.prism("gold", ngon(0, 0, 0.17, 8), 2.48, 3.08)
    for z in (2.62, 2.82):
        for x, y in ngon(0, 0, 0.18, 4, math.pi / 4):
            a.box("gem", x - 0.04, x + 0.04, y - 0.04, y + 0.04, z - 0.04, z + 0.04, bevel=0)
    disc(a, "gold2", 0, 0, 0.24, 3.06, 3.16)
    for x, y in ngon(0, 0, 0.245, 6):
        a.box("ruby", x - 0.04, x + 0.04, y - 0.04, y + 0.04, 3.08, 3.14, bevel=0)
    for r, z0, z1 in ((0.28, 3.14, 3.24), (0.36, 3.22, 3.36), (0.39, 3.34, 3.56), (0.36, 3.54, 3.68), (0.28, 3.66, 3.78)):
        disc(a, "grille", 0, 0, r, z0, z1)
    disc(a, "grille2", 0, 0, 0.395, 3.43, 3.47, bevel=0)  # металлический обод решётки
    disc(a, "gold", 0, 0, 0.18, 3.76, 3.84)
    a.box("shine", -0.22, -0.16, -0.4, -0.37, 3.4, 3.62, bevel=0)
    a.transform = None
    # ноты и искры вокруг
    a.pixels(NOTE, {"#": ("note", 0.04)}, 0.09, -1.05, 3.45, "xz", 0.02)
    a.pixels(NOTE, {"#": ("note2", 0.04)}, 0.07, 0.7, 2.75, "xz", 0.02)
    sparkle(a, "shine", (0.85, -0.3, 3.85), 0.3)
    sparkle(a, "shine", (-0.8, -0.3, 2.55), 0.24)
    return a


# ── 22. Золотой геймпад: огромный контроллер на подставке-витрине, неоновые кнопки, стики, подсветка, провод ────


def golden_gamepad():
    a = S.Art("Art_GoldenGamepad", ring_z0=1.2)
    a.paint("gold", "F2C230", rings=True)
    a.paint("stand", "2B2B33", rings=True)
    for key, code in (("gold2", "C9921A"), ("dark", "1E1E24"), ("stick", "8A96A6"), ("pink", "FF4FA8"),
                      ("cyan", "3FE0F0"), ("lime", "9CF03A"), ("orange", "FF9A1F"), ("glow", "6FF2FF"),
                      ("gem", "A06BFF"), ("plate", "F2C230"), ("shine", "FFFFFF"), ("cable", "2B2B33")):
        a.paint(key, code)
    # подставка с табличкой и два упора под ручки
    a.box("stand", -1.5, 1.5, -0.8, 0.8, 0.0, 0.3)
    a.box("gold2", -1.54, 1.54, -0.84, -0.72, 0.01, 0.32)
    a.box("plate", -0.5, 0.5, -0.88, -0.83, 0.08, 0.24, bevel=0)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.95, s * 1.25))
        a.box("gold2", x0, x1, -0.2, 0.2, 0.28, 0.6)
    # контроллер стоит лицом к зрителю, чуть откинут назад
    a.transform = tilt((0, 0, 0.5), "X", -10)
    outline = [(-1.0, 1.95), (1.0, 1.95), (1.18, 1.86), (1.3, 1.62), (1.48, 0.86), (1.4, 0.56), (1.12, 0.48),
               (0.86, 0.74), (0.58, 1.0), (-0.58, 1.0), (-0.86, 0.74), (-1.12, 0.48), (-1.4, 0.56), (-1.48, 0.86),
               (-1.3, 1.62), (-1.18, 1.86)]
    a.extrude("gold", outline, -0.25, 0.25, axis="y")
    # плечевые кнопки
    for s in (1, -1):
        x0, x1 = sorted((s * 0.42, s * 0.98))
        a.box("dark", x0, x1, -0.18, 0.18, 1.9, 2.06)
    # крестовина
    a.box("dark", -1.0, -0.5, -0.3, -0.22, 1.38, 1.52)
    a.box("dark", -0.82, -0.68, -0.32, -0.22, 1.2, 1.7)
    # четыре неоновые кнопки ромбом
    for (x, z, key) in ((0.75, 1.66, "pink"), (0.95, 1.45, "cyan"), (0.75, 1.24, "lime"), (0.55, 1.45, "orange")):
        disc(a, key, x, z, 0.1, -0.33, -0.22, axis="y")
    # стики
    for x in (-0.36, 0.36):
        disc(a, "dark", x, 1.12, 0.17, -0.3, -0.22, axis="y")
        disc(a, "stick", x, 1.12, 0.12, -0.42, -0.29, axis="y")
    # центр: светящаяся полоса, кнопки меню, камень «домой»
    a.box("glow", -0.32, 0.32, -0.29, -0.22, 1.74, 1.82, bevel=0)
    for x in (-0.16, 0.16):
        a.box("dark", x - 0.07, x + 0.07, -0.28, -0.22, 1.55, 1.61, bevel=0)
    disc(a, "gem", 0, 1.36, 0.1, -0.31, -0.22, axis="y")
    a.box("shine", -1.2, -1.05, -0.27, -0.24, 1.55, 1.8, bevel=0)
    # провод от верхнего края к подставке
    chain(a, ["cable"], [(0.0, 0.1, 1.93), (0.15, 0.35, 2.25), (0.55, 0.5, 2.3), (1.0, 0.55, 1.95), (1.35, 0.6, 1.2),
                         (1.38, 0.62, 0.3)], 0.08, grow=0.03)
    a.transform = None
    sparkle(a, "shine", (-1.35, -0.4, 2.3), 0.3)
    sparkle(a, "shine", (1.4, -0.4, 2.45), 0.24)
    return a


# ══ EPIC ═════════════════════════════════════════════════════════════════════════════════════════════════════

# ── 23. Золотой трон: смешно огромный — золото, стёганый бархат, гигантский рубин на гребне, ступени, монеты ──


def golden_throne():
    a = S.Art("Art_GoldenThrone", ring_z0=2.0)
    a.paint("gold", "F2C230", rings=True)
    a.paint("velvet", "C62828", rings=True)
    a.paint("carpet", "6B3FB8", rings=True)
    for key, code in (("gold2", "C9921A"), ("button", "F2C230"), ("ruby", "E53935"), ("ruby2", "FF8A8A"),
                      ("emerald", "2E9E4F"), ("sapphire", "2E5BD8"), ("glint", "FFFFFF"), ("coin", "FFD84A")):
        a.paint(key, code)
    # ступени с ковром
    a.box("carpet", -1.55, 1.55, -1.35, 1.05, 0.0, 0.24)
    a.box("gold2", -1.58, 1.58, -1.39, -1.27, 0.01, 0.26)
    a.box("carpet", -1.28, 1.28, -1.02, 0.95, 0.22, 0.46)
    # сиденье и стёганая подушка
    a.box("gold", -1.0, 1.0, -0.78, 0.78, 0.44, 1.26)
    a.box("velvet", -0.84, 0.84, -0.74, 0.6, 1.24, 1.48)
    # спинка: золотой короб, бархатная панель с пуговицами
    a.box("gold", -1.02, 1.02, 0.46, 0.84, 1.2, 3.62)
    a.box("velvet", -0.76, 0.76, 0.38, 0.48, 1.5, 3.34)
    for x in (-0.45, 0.0, 0.45):
        for z in (1.85, 2.4, 2.95):
            a.box("button", x - 0.06, x + 0.06, 0.34, 0.39, z - 0.06, z + 0.06, bevel=0)
    # гребень: корона из трёх зубцов с камнями, огромный рубин посередине
    a.box("gold", -0.9, 0.9, 0.42, 0.86, 3.58, 3.92)
    for x, h, gem in ((-0.62, 0.55, "sapphire"), (0.62, 0.55, "emerald")):
        a.frustum("gold", (x - 0.2, x + 0.2, 0.5, 0.78), (x, x, 0.64, 0.64), 3.9, 3.9 + h, bevel=0)
        a.box(gem, x - 0.1, x + 0.1, 0.4, 0.45, 3.66, 3.86, bevel=0)
    a.prism("gold2", S.octagon(-0.46, 0.46, 3.72, 4.66, 0.18), 0.44, 0.74, axis="y")
    a.prism("ruby", S.octagon(-0.36, 0.36, 3.82, 4.56, 0.14), 0.36, 0.46, axis="y")
    a.box("ruby2", -0.22, -0.06, 0.33, 0.37, 4.3, 4.46, bevel=0)
    a.box("glint", -0.24, -0.16, 0.31, 0.34, 4.38, 4.48, bevel=0)
    # подлокотники на столбиках, шары с камнями на концах
    for s in (1, -1):
        x0, x1 = sorted((s * 1.0, s * 1.34))
        a.box("gold", x0, x1, -0.76, 0.66, 1.22, 1.52)
        x0, x1 = sorted((s * 1.05, s * 1.28))
        a.box("gold2", x0, x1, -0.74, -0.5, 0.44, 1.24)
        disc(a, "gold", s * 1.17, -0.78, 0.24, 1.18, 1.68)
        disc(a, "emerald" if s > 0 else "sapphire", s * 1.17, 1.43, 0.12, -1.03, -0.97, axis="y")
        x0, x1 = sorted((s * 1.02, s * 1.1))
        a.box("ruby", x0, x1, 0.55, 0.75, 2.6, 2.84, bevel=0)
    # лапы-когти спереди
    for s in (1, -1):
        x0, x1 = sorted((s * 0.7, s * 1.02))
        a.box("gold2", x0, x1, -0.92, -0.62, 0.44, 0.62)
    # куча монет на ступени
    for x, y, h in ((-1.05, -1.1, 3), (-0.7, -1.18, 2), (1.0, -1.1, 4), (0.62, -1.2, 1)):
        for k in range(h):
            disc(a, "coin" if k % 2 == 0 else "gold2", x + 0.03 * (k % 2), y, 0.18, 0.24 + k * 0.08, 0.32 + k * 0.08)
    return a


# ── 24. Чёрная кошка-идол: мистическая кошка с поднятой лапой и светящимися глазами на куче монет, свечи ──────

MOON = [".##.",
        "#...",
        "#...",
        ".##."]


def black_cat_idol():
    a = S.Art("Art_BlackCatIdol", ring_z0=1.4)
    a.paint("fur", "26232E", rings=True)
    a.paint("altar", "3B1A6E", rings=True)
    for key, code in (("gold", "F2C230"), ("gold2", "C9921A"), ("eye", "C8FF3A"), ("slit", "15161C"),
                      ("pink", "FF8AB0"), ("gem", "B23CFF"), ("candle", "F6F0E1"), ("flame", "FF9A1F"),
                      ("flame2", "FFE14A"), ("whisker", "D6DCE6"), ("glint", "FFFFFF")):
        a.paint(key, code)
    # алтарь в две ступени, золотой кант
    a.box("altar", -1.0, 1.0, -0.85, 0.85, 0.0, 0.32)
    a.box("gold2", -0.86, 0.86, -0.71, 0.71, 0.3, 0.38)
    a.box("altar", -0.8, 0.8, -0.66, 0.66, 0.36, 0.56)
    # свечи в передних углах
    for s in (1, -1):
        x = s * 0.82
        disc(a, "gold", x, -0.66, 0.13, 0.3, 0.4)
        disc(a, "candle", x, -0.66, 0.08, 0.38, 0.86)
        a.frustum("flame", (x - 0.05, x + 0.05, -0.71, -0.61), (x, x, -0.66, -0.66), 0.86, 1.06, bevel=0)
    # монеты под кошкой
    for x, y, h in ((-0.5, -0.42, 2), (0.45, -0.45, 3), (0.0, -0.55, 1), (-0.55, 0.4, 2), (0.55, 0.35, 1)):
        for k in range(h):
            disc(a, "gold" if k % 2 == 0 else "gold2", x + 0.02 * (k % 2), y, 0.17, 0.54 + k * 0.07, 0.61 + k * 0.07)
    # тело: сидит, задние лапы, грудь
    a.box("fur", -0.46, 0.46, -0.3, 0.46, 0.54, 1.62)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.2, s * 0.52))
        a.box("fur", x0, x1, -0.5, 0.36, 0.54, 0.98)  # бёдра
    a.box("fur", -0.2, 0.06, -0.62, -0.3, 0.6, 1.3)  # левая передняя лапа вниз
    a.box("fur", -0.22, 0.08, -0.7, -0.38, 0.58, 0.72)
    # правая лапа поднята — манит монеты
    a.box("fur", 0.42, 0.72, -0.28, 0.0, 1.2, 1.5)  # плечо
    a.box("fur", 0.56, 0.84, -0.32, -0.02, 1.44, 2.18)  # лапа вверх сбоку от головы
    a.box("fur", 0.54, 0.86, -0.4, 0.0, 2.12, 2.44)
    a.box("pink", 0.6, 0.8, -0.44, -0.39, 2.18, 2.38, bevel=0)
    # ошейник с полумесяцем
    a.box("gold", -0.42, 0.42, -0.36, 0.42, 1.52, 1.64)
    a.prism("gold", S.octagon(-0.16, 0.16, 1.18, 1.5, 0.06), -0.4, -0.34, axis="y")
    a.pixels(MOON, {"#": ("gem", 0.02)}, 0.06, -0.12, 1.46, "xz", 0.4)
    # голова, уши, глаза-огни, нос, усы, камень во лбу
    a.box("fur", -0.5, 0.5, -0.5, 0.24, 1.6, 2.32)
    a.box("fur", -0.24, 0.24, -0.6, -0.42, 1.66, 1.86)
    a.box("pink", -0.06, 0.06, -0.63, -0.58, 1.8, 1.88, bevel=0)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.1, s * 0.42))
        a.frustum("fur", (x0, x1, -0.36, -0.06), (s * 0.3, s * 0.3, -0.21, -0.21), 2.3, 2.82, bevel=0)
        x0, x1 = sorted((s * 0.18, s * 0.34))
        a.frustum("pink", (x0, x1, -0.38, -0.33), (s * 0.29, s * 0.29, -0.355, -0.355), 2.36, 2.68, bevel=0)
        x0, x1 = sorted((s * 0.1, s * 0.38))
        a.box("eye", x0, x1, -0.55, -0.49, 1.94, 2.16, bevel=0)
        x0, x1 = sorted((s * 0.215, s * 0.265))
        a.box("slit", x0, x1, -0.57, -0.54, 1.96, 2.14, bevel=0)
        for z in (1.72, 1.8):
            x0, x1 = sorted((s * 0.26, s * 0.62))
            a.box("whisker", x0, x1, -0.6, -0.57, z - 0.012, z + 0.012, bevel=0)
    a.prism("gem", S.octagon(-0.1, 0.1, 2.18, 2.38, 0.05), -0.56, -0.5, axis="y")
    a.box("glint", -0.06, -0.01, -0.58, -0.55, 2.3, 2.35, bevel=0)
    # хвост вокруг бока
    chain(a, ["fur"], [(-0.4, 0.4, 0.62), (-0.66, 0.1, 0.62), (-0.7, -0.35, 0.66), (-0.5, -0.62, 0.78)], 0.18,
          grow=0.06)
    return a


# ── 25. Кристальный динозавр: длинношеий динозавр из голубых кристаллов, цветные осколки на спине, друза ──────


def crystal_dino():
    a = S.Art("Art_CrystalDino", ring_z0=0.15)
    a.paint("stone", "3A3550", rings=True)
    for key, code in (("ice", "4FD8F0"), ("ice2", "B8F6FF"), ("ice3", "1E9AC0"), ("pink", "FF6FD8"),
                      ("purple", "A06BFF"), ("yellow", "FFE14A"), ("eye", "15161C"), ("glint", "FFFFFF"),
                      ("gold", "F2C230")):
        a.paint(key, code)
    a.box("stone", -2.0, 2.0, -0.85, 0.85, 0.0, 0.3)
    a.box("gold", -0.6, 0.6, -0.89, -0.84, 0.06, 0.24, bevel=0)
    # друза кристаллов у ног
    for x, y, h, key in ((-1.6, -0.5, 0.6, "purple"), (-1.4, -0.6, 0.42, "pink"), (1.7, 0.45, 0.5, "pink"),
                         (1.55, 0.6, 0.34, "purple"), (-1.7, 0.5, 0.36, "ice")):
        a.frustum(key, (x - 0.12, x + 0.12, y - 0.12, y + 0.12), (x, x, y, y), 0.28, 0.28 + h, bevel=0)
    # тело — шестигранный кристалл вдоль x, светлая грань сверху, тёмная снизу
    zc = 1.55
    a.prism("ice", ngon(zc, 0, 0.5, 6, 0), -0.95, 0.75, axis="x")
    a.box("ice2", -0.85, 0.65, -0.2, 0.2, zc + 0.42, zc + 0.48, bevel=0)
    a.box("ice3", -0.85, 0.65, -0.2, 0.2, zc - 0.48, zc - 0.42, bevel=0)
    a.frustum("ice", (-0.42, 0.42, -0.45, 0.45), (0, 0, 0, 0), -0.95, -1.25, axis="x", bevel=0,
              matrix=Matrix.Translation((0, 0, zc)))
    # ноги — шестигранные колонны
    for x in (-0.65, 0.45):
        for y in (-0.3, 0.3):
            a.prism("ice3" if y < 0 else "ice", ngon(x, y, 0.17, 6), 0.28, zc - 0.2)
    # шея и голова
    chain(a, ["ice", "ice2"], [(0.6, 0, zc + 0.1), (1.05, 0, zc + 0.7), (1.35, 0, zc + 1.35), (1.5, 0, zc + 1.9)],
          0.34, grow=0.12)
    a.box("ice", 1.32, 1.95, -0.24, 0.24, zc + 1.8, zc + 2.16)
    a.box("ice2", 1.38, 1.9, -0.2, 0.2, zc + 2.14, zc + 2.2, bevel=0)
    for s in (1, -1):
        y0, y1 = sorted((s * 0.24, s * 0.27))
        a.box("eye", 1.6, 1.72, y0, y1, zc + 1.96, zc + 2.08, bevel=0)
        a.box("glint", 1.66, 1.7, s * 0.27 - 0.005 if s > 0 else -0.285, s * 0.285 if s > 0 else -0.27, zc + 2.02,
              zc + 2.06, bevel=0)
    # хвост
    chain(a, ["ice", "ice3"], [(-1.2, 0, zc - 0.05), (-1.6, 0, zc - 0.45), (-1.95, 0, zc - 0.8),
                               (-2.15, 0.1, zc - 1.05)], 0.3, 0.26, grow=0.06)
    # осколки на спине и шее
    for i, (x, z, h) in enumerate(((-0.6, zc + 0.45, 0.5), (-0.2, zc + 0.48, 0.62), (0.2, zc + 0.46, 0.55),
                                   (0.55, zc + 0.42, 0.42), (0.95, zc + 0.85, 0.32), (1.2, zc + 1.4, 0.26))):
        key = ("pink", "purple", "yellow")[i % 3]
        a.frustum(key, (x - 0.13, x + 0.13, -0.1, 0.1), (x, x, 0, 0), z, z + h, bevel=0)
    # кристаллы по бокам тела и рог на голове
    for s in (1, -1):
        for x, h, key in ((-0.5, 0.42, "purple"), (0.2, 0.34, "pink")):
            y0 = s * 0.42
            m = Matrix.Translation((x, y0, zc)) @ Matrix.Rotation(math.radians(-s * 90 + s * 25), 4, "X")
            a.frustum(key, (-0.11, 0.11, -0.11, 0.11), (0, 0, 0, 0), 0.0, h, bevel=0, matrix=m)
    a.frustum("yellow", (1.55, 1.73, -0.09, 0.09), (1.62, 1.62, 0, 0), zc + 2.14, zc + 2.5, bevel=0)
    a.frustum("pink", (1.38, 1.5, -0.07, 0.07), (1.42, 1.42, 0, 0), zc + 2.14, zc + 2.36, bevel=0)
    sparkle(a, "glint", (0.0, -0.55, zc + 0.1), 0.3)
    sparkle(a, "glint", (1.7, -0.3, zc + 2.7), 0.24)
    return a


# ── 26. Легендарный автомат с призами: красный корпус, стеклянный купол с капсулами, ручка, лоток с призом ─────


def prize_machine():
    a = S.Art("Art_PrizeMachine", ring_z0=0.8)
    a.paint("body", "D8352A", rings=True)
    for key, code in (("gold", "F2C230"), ("gold2", "C9921A"), ("glass", "A8E6F0"), ("shine", "FFFFFF"),
                      ("dark", "2B2B33"), ("metal", "C9D3DD"), ("c1", "FF4F7B"), ("c2", "4FB8FF"), ("c3", "FFE14A"),
                      ("c4", "4FD86A"), ("c5", "A06BFF"), ("c6", "FF9A1F"), ("white", "FFFFFF"), ("bulb", "FFF29A"),
                      ("blue", "2F6BD8")):
        a.paint(key, code)
    # корпус с полосами
    a.box("body", -0.82, 0.82, -0.72, 0.72, 0.0, 1.62)
    a.box("gold2", -0.86, 0.86, -0.76, 0.76, 0.0, 0.12)
    a.box("blue", -0.84, 0.84, -0.74, 0.74, 1.3, 1.42)
    # окно лотка, капсула-приз, щель для монеты, ручка
    a.box("dark", -0.34, 0.34, -0.76, -0.71, 0.26, 0.68, bevel=0)
    a.box("metal", -0.4, 0.4, -0.9, -0.7, 0.2, 0.28)
    a.box("c1", -0.16, 0.0, -0.86, -0.7, 0.28, 0.44)
    a.box("white", 0.0, 0.16, -0.86, -0.7, 0.28, 0.44)
    a.box("metal", -0.22, 0.22, -0.78, -0.72, 0.84, 1.18)
    a.box("dark", -0.03, 0.03, -0.8, -0.77, 0.9, 1.12, bevel=0)
    disc(a, "gold", 0.5, 1.0, 0.18, -0.84, -0.72, axis="y")
    a.box("metal", 0.46, 0.54, -0.92, -0.82, 0.82, 1.18)
    disc(a, "c1", 0.5, 1.18, 0.07, -0.96, -0.9, axis="y")
    a.pixels(STAR, {"#": ("gold", 0.025)}, 0.07, -0.66, 1.22, "xz", 0.72)
    # шея купола
    disc(a, "gold", 0, 0, 0.8, 1.6, 1.76)
    # купол: стекло-клетка и капсулы
    glass_cage(a, "glass", 0, 0, 0.72, 1.74, 3.18, post=0.06)
    caps = ("c1", "c2", "c3", "c4", "c5", "c6")
    k = 0
    for layer, (z, rr) in enumerate(((1.86, 0.48), (2.12, 0.42), (2.38, 0.3))):
        n = 7 - layer * 2
        for i in range(n):
            ang = 2 * math.pi * i / n + layer * 0.5
            x, y = rr * math.cos(ang), rr * math.sin(ang)
            key = caps[k % 6]
            k += 1
            a.box(key, x - 0.12, x + 0.12, y - 0.12, y + 0.12, z - 0.12, z + 0.12, matrix=tilt((x, y, z), "Z", 20 + 15 * i))
    bar(a, "shine", (-0.52, -0.7, 2.0), (-0.32, -0.7, 2.95), 0.06, 0.04, bevel=0)
    # крышка с лампочками и звездой
    disc(a, "body", 0, 0, 0.82, 3.16, 3.4)
    for x, y in ngon(0, 0, 0.82, 8):
        a.box("bulb", x - 0.07, x + 0.07, y - 0.07, y + 0.07, 3.22, 3.34, bevel=0)
    disc(a, "gold", 0, 0, 0.42, 3.38, 3.52)
    a.box("gold2", -0.05, 0.05, -0.05, 0.05, 3.5, 3.66, bevel=0)
    a.prism("gold", S.octagon(-0.3, 0.3, 3.64, 4.2, 0.1), -0.06, 0.06, axis="y")
    a.pixels(STAR, {"#": ("c1", 0.03)}, 0.09, -0.225, 4.145, "xz", 0.06, sides=(-1, 1))
    return a


# ── 27. Портативный дракон: зелёный дракончик с крыльями сидит на сокровищах и обнимает камень ────────────────


def pocket_dragon():
    a = S.Art("Art_PocketDragon", ring_z0=1.0)
    a.paint("scale", "3FBF5A", rings=True)
    a.paint("gold", "F2C230", rings=True)
    for key, code in (("belly", "F2D38A"), ("belly2", "D9B060"), ("wing", "FF7A3A"), ("bone", "2E8A44"),
                      ("horn", "FFF1C8"), ("eye", "FFB020"), ("pupil", "15161C"), ("glint", "FFFFFF"),
                      ("gem", "A06BFF"), ("gem2", "E040A0"), ("ruby", "E53935"), ("sapphire", "2E5BD8"),
                      ("nostril", "1E5A2A"), ("gold2", "C9921A"), ("spike", "2E8A44")):
        a.paint(key, code)
    # гора сокровищ
    a.box("gold", -1.05, 1.05, -0.85, 0.85, 0.0, 0.3)
    a.box("gold", -0.8, 0.8, -0.62, 0.62, 0.28, 0.5)
    for x, y, key in ((-0.9, -0.7, "ruby"), (0.85, -0.68, "sapphire"), (0.7, 0.62, "gem2"), (-0.75, 0.55, "ruby")):
        a.box(key, x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0.28, 0.46, matrix=tilt((x, y, 0.37), "Z", 30))
    for x, y in ((-0.55, -0.7), (0.4, -0.72), (0.95, 0.1)):
        disc(a, "gold2", x, y, 0.15, 0.28, 0.36)
    # тело, живот с полосами, задние лапы
    a.box("scale", -0.46, 0.46, -0.36, 0.44, 0.48, 1.4)
    a.box("belly", -0.3, 0.3, -0.42, -0.34, 0.56, 1.34)
    for z in (0.75, 0.95, 1.15):
        a.box("belly2", -0.28, 0.28, -0.44, -0.41, z - 0.02, z + 0.02, bevel=0)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.24, s * 0.56))
        a.box("scale", x0, x1, -0.5, 0.3, 0.48, 0.84)
        a.box("horn", x0, x1, -0.58, -0.48, 0.48, 0.58)  # когти
    # передние лапы обнимают большой камень
    a.prism("gem", S.octagon(-0.24, 0.24, 0.92, 1.4, 0.1), -0.66, -0.4, axis="y")
    a.box("glint", -0.14, -0.06, -0.68, -0.65, 1.24, 1.32, bevel=0)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.2, s * 0.42))
        a.box("scale", x0, x1, -0.62, -0.3, 1.0, 1.32)
    # голова: морда, ноздри, глаза, рога, шипы
    a.box("scale", -0.42, 0.42, -0.62, 0.18, 1.38, 1.98)
    a.box("scale", -0.3, 0.3, -0.92, -0.56, 1.42, 1.72)
    a.box("belly", -0.26, 0.26, -0.9, -0.56, 1.4, 1.47)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.08, s * 0.18))
        a.box("nostril", x0, x1, -0.94, -0.9, 1.6, 1.66, bevel=0)
        x0, x1 = sorted((s * 0.1, s * 0.36))
        a.box("eye", x0, x1, -0.66, -0.6, 1.66, 1.9, bevel=0)
        x0, x1 = sorted((s * 0.2, s * 0.28))
        a.box("pupil", x0, x1, -0.68, -0.65, 1.68, 1.88, bevel=0)
        g = 0.32 if s > 0 else -0.16
        a.box("glint", g - 0.03, g + 0.03, -0.69, -0.66, 1.82, 1.88, bevel=0)
        x0, x1 = sorted((s * 0.18, s * 0.36))
        a.frustum("horn", (x0, x1, -0.2, 0.0), (s * 0.34, s * 0.34, 0.16, 0.16), 1.96, 2.42, bevel=0)
    for z in (0.7, 1.0, 1.3):
        a.frustum("spike", (-0.08, 0.08, 0.38, 0.5), (0, 0, 0.44, 0.44), z, z + 0.2, axis="z", bevel=0,
                  matrix=tilt((0, 0.44, z + 0.1), "X", -70))
    # крылья: перепонка оранжевая, кости зелёные
    for s in (1, -1):
        wing = [(0.0, 0.0), (0.5, 0.55), (1.0, 0.95), (1.25, 0.6), (1.05, 0.25), (0.8, 0.35), (0.6, -0.05),
                (0.35, 0.05)]
        pts = [(s * u, v) for u, v in wing]
        if s < 0:
            pts = pts[::-1]
        m = Matrix.Translation((s * 0.3, 0.4, 1.25)) @ Matrix.Rotation(math.radians(-s * 28), 4, "Z")
        a.extrude("wing", pts, -0.03, 0.03, axis="y", matrix=m)
        bar(a, "bone", (m @ Vector((0, 0, 0))), (m @ Vector((s * 1.0, 0, 0.95))), 0.09, 0.1)
        bar(a, "bone", (m @ Vector((s * 0.5, 0, 0.55))), (m @ Vector((s * 1.25, 0, 0.6))), 0.08, 0.09)
    # хвост с наконечником на сокровищах
    chain(a, ["scale"], [(0.3, 0.4, 0.56), (0.7, 0.2, 0.52), (0.85, -0.25, 0.54), (0.65, -0.62, 0.56)], 0.18,
          grow=0.05)
    a.frustum("spike", (0.5, 0.74, -0.84, -0.6), (0.62, 0.62, -0.72, -0.72), 0.5, 0.82, bevel=0)
    return a


# ── 28. Сердце из неона: розовое сердце-энергия слоями (свечение), молнии, медные катушки, кольца энергии ──────

HEART_IN = [".#.#.",
            "#####",
            ".###.",
            "..#.."]


def neon_heart():
    a = S.Art("Art_NeonHeart", ring_z0=0.15)
    a.paint("base", "2B2B33", rings=True)
    for key, code in (("pink", "FF2E7E"), ("pink2", "FF9AC4"), ("core", "FFE6F0"), ("copper", "C87533"),
                      ("copper2", "8A4A1C"), ("cyan", "4FE3F0"), ("bolt", "FFE14A"), ("metal", "8A96A6"),
                      ("glint", "FFFFFF")):
        a.paint(key, code)
    a.box("base", -1.1, 1.1, -0.7, 0.7, 0.0, 0.32)
    a.box("metal", -0.8, 0.8, -0.5, 0.5, 0.3, 0.42)
    # медные катушки по бокам с голубыми огнями
    for s in (1, -1):
        x = s * 0.82
        for i in range(6):
            disc(a, "copper" if i % 2 == 0 else "copper2", x, 0, 0.2 - 0.03 * (i % 2), 0.3 + i * 0.14,
                 0.44 + i * 0.14)
        disc(a, "cyan", x, 0, 0.12, 1.14, 1.3)
    # стойка и кольца энергии
    a.box("metal", -0.1, 0.1, -0.1, 0.1, 0.4, 1.3)
    for z, rr in ((0.75, 0.32), (1.1, 0.26)):
        a.frame("cyan", ngon(0, 0, rr, 8), 0.06, z - 0.03, z + 0.03, axis="z")
    # сердце: внешний слой, светлый внутренний, белая сердцевина — свечение слоями
    cell = 0.3
    w = len(HEART[0]) * cell
    z_top = 1.25 + len(HEART) * cell
    for c, r, cw, rh in S.greedy_rects([[ch == "#" for ch in row] for row in HEART]):
        x0 = -w / 2 + c * cell
        a.box("pink", x0, x0 + cw * cell, -0.22, 0.22, z_top - (r + rh) * cell, z_top - r * cell)
    a.pixels(HEART, {"#": ("pink2", 0.06)}, cell * 0.66, -w * 0.33, z_top - 0.18, "xz", 0.22, sides=(-1, 1))
    a.pixels(HEART_IN, {"#": ("core", 0.1)}, 0.16, -0.4, z_top - 0.42, "xz", 0.27, sides=(-1, 1))
    a.box("glint", -0.72, -0.56, -0.36, -0.32, z_top - 0.36, z_top - 0.2, bevel=0)
    # молнии по бокам
    for s in (1, -1):
        a.pixels(BOLT, {"#": ("bolt", 0.06)}, 0.12, s * 1.15 - 0.24, z_top - 0.1, "xz", 0.03, sides=(-1,))
    return a


# ── 29. Гигантский космический шлем: белый шлем с золотым визором, гоночная полоса, огни, антенны, подставка ──


def space_helmet():
    a = S.Art("Art_SpaceHelmet", ring_z0=1.5)
    a.paint("shell", "EEF0F3", rings=True)
    for key, code in (("base", "2B2B33"), ("ring", "2F6BD8"), ("bolt", "C9D3DD"), ("visor", "F2B632"),
                      ("visor2", "D9901A"), ("shine", "FFF6D8"), ("stripe", "FF7A1A"), ("lamp", "FFE14A"),
                      ("red", "E53935"), ("metal", "8A96A6"), ("patch", "1F3E9A"), ("star", "FFFFFF")):
        a.paint(key, code)
    a.box("base", -1.15, 1.15, -1.15, 1.15, 0.0, 0.28)
    disc(a, "metal", 0, 0, 0.8, 0.26, 0.4)
    # горловое кольцо с болтами
    disc(a, "ring", 0, 0, 1.0, 0.38, 0.66)
    for x, y in ngon(0, 0, 1.0, 8):
        a.box("bolt", x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0.46, 0.58, bevel=0)
    # шлем слоями
    disc(a, "shell", 0, 0, 0.98, 0.64, 0.84)
    disc(a, "shell", 0, 0, 1.15, 0.82, 2.2)
    disc(a, "shell", 0, 0, 1.0, 2.18, 2.5)
    disc(a, "shell", 0, 0, 0.7, 2.48, 2.7)
    # гоночная полоса через верх
    a.box("stripe", -0.18, 0.18, -0.62, 0.62, 2.68, 2.74, bevel=0)
    # визор: золотое стекло, рамка, блики, отражения звёзд
    a.frame("bolt", S.octagon(-0.88, 0.88, 0.9, 2.16, 0.34), 0.1, -1.13, -1.03, axis="y")
    a.prism("visor", S.octagon(-0.8, 0.8, 0.98, 2.08, 0.3), -1.1, -1.02, axis="y")
    bar(a, "shine", (-0.55, -1.12, 1.25), (-0.15, -1.12, 1.95), 0.14, 0.03, bevel=0)
    bar(a, "shine", (-0.2, -1.12, 1.2), (0.0, -1.12, 1.55), 0.07, 0.03, bevel=0)
    for x, z in ((0.45, 1.85), (0.6, 1.5), (0.3, 1.3)):
        a.box("star", x - 0.03, x + 0.03, -1.13, -1.1, z - 0.03, z + 0.03, bevel=0)
    a.box("visor2", -0.8, 0.8, -1.12, -1.09, 0.98, 1.06, bevel=0)
    # фонари, антенны, нашивка
    for s in (1, -1):
        x0, x1 = sorted((s * 1.06, s * 1.22))
        a.box("metal", x0, x1, -0.5, -0.1, 1.5, 1.9)
        x0, x1 = sorted((s * 1.2, s * 1.26))
        a.box("lamp", x0, x1, -0.44, -0.16, 1.56, 1.84, bevel=0)
    bar(a, "metal", (0.55, 0.4, 2.55), (0.9, 0.55, 3.3), 0.07)
    disc(a, "red", 0.9, 0.55, 0.1, 3.28, 3.44)
    bar(a, "metal", (-0.45, 0.5, 2.5), (-0.6, 0.6, 3.0), 0.06)
    disc(a, "lamp", -0.6, 0.6, 0.08, 2.98, 3.1)
    a.box("patch", -0.25, 0.25, 1.04, 1.1, 1.0, 1.4)
    a.pixels(STAR, {"#": ("star", 0.02)}, 0.07, 0.175, 1.375, "xz", 1.1, sides=(1,), flip=True)
    return a


# ── 30. Тёмная корона хаоса: чёрно-фиолетовая корона с шипами, пылающий камень, фиолетовое пламя, подушка ────


def chaos_crown():
    a = S.Art("Art_ChaosCrown", ring_z0=1.0)
    a.paint("velvet", "8E1B2A", rings=True)
    a.paint("crown", "2A1F3D", rings=True)
    for key, code in (("tassel", "F2C230"), ("gold", "F2C230"), ("spike", "3B1A6E"), ("gem", "FF2EB8"),
                      ("gem2", "FF9AE0"), ("gem3", "B23CFF"), ("flame", "B23CFF"), ("flame2", "FF6FD8"),
                      ("flame3", "FFE6F6"), ("inner", "4A1A6E"), ("orb", "3B1A6E"), ("glint", "FFFFFF")):
        a.paint(key, code)
    top = cushion(a, "velvet", 2.0, 2.0, 0.0, 0.4, tassel="tassel")
    # обруч, золотые канты, бархат внутри
    a.frame("crown", ngon(0, 0, 0.88, 8), 0.2, top, top + 0.5, axis="z")
    a.frame("gold", ngon(0, 0, 0.93, 8), 0.12, top - 0.02, top + 0.1, axis="z")
    a.frame("gold", ngon(0, 0, 0.93, 8), 0.12, top + 0.44, top + 0.56, axis="z")
    disc(a, "inner", 0, 0, 0.72, top + 0.02, top + 0.62)
    disc(a, "inner", 0, 0, 0.5, top + 0.6, top + 0.82)
    # шипы: высокие и низкие через один, на высоких — камни
    for i, (x, y) in enumerate(ngon(0, 0, 0.78, 8)):
        h = 1.0 if i % 2 == 0 else 0.6
        a.frustum("spike", (x - 0.16, x + 0.16, y - 0.16, y + 0.16), (x, x, y, y), top + 0.54, top + 0.54 + h, bevel=0)
        if i % 2 == 0:
            a.box("gem3", x - 0.07, x + 0.07, y - 0.07, y + 0.07, top + 0.54 + h - 0.02, top + 0.54 + h + 0.12,
                  matrix=tilt((x, y, top + 0.6 + h), "Z", 45))
    # пылающий камень спереди и камни по кругу
    a.prism("gold", S.octagon(-0.3, 0.3, top + 0.04, top + 0.6, 0.1), -0.98, -0.88, axis="y")
    a.prism("gem", S.octagon(-0.22, 0.22, top + 0.1, top + 0.54, 0.08), -1.04, -0.96, axis="y")
    a.box("gem2", -0.12, 0.0, -1.07, -1.03, top + 0.36, top + 0.48, bevel=0)
    for ang in (90, 135, 225, 270, 315, 45):
        r = math.radians(ang)
        x, y = 0.93 * math.cos(r), 0.93 * math.sin(r)
        m = Matrix.Translation((x, y, top + 0.27)) @ Matrix.Rotation(r, 4, "Z")
        a.box("gem3", -0.04, 0.04, -0.09, 0.09, -0.09, 0.09, bevel=0, matrix=m)
    # фиолетовое пламя над короной
    for i, (rr, h, key) in enumerate(((0.36, 0.5, "flame"), (0.24, 0.48, "flame2"), (0.12, 0.36, "flame3"))):
        z0 = top + 0.8 + i * 0.22
        a.frustum(key, (-rr, rr, -rr, rr), (0, 0, 0, 0), z0, z0 + h, bevel=0, matrix=tilt((0, 0, z0), "Z", 45 * i))
    # парящие тёмные сферы
    for x, z in ((-1.25, top + 1.1), (1.2, top + 1.5)):
        a.box("orb", x - 0.16, x + 0.16, -0.16, 0.16, z - 0.16, z + 0.16, matrix=tilt((x, 0, z), "Z", 45))
        a.box("gem", x - 0.07, x + 0.07, -0.2, -0.15, z - 0.07, z + 0.07, bevel=0, matrix=tilt((x, 0, z), "Z", 45))
    sparkle(a, "glint", (0.95, -0.9, top + 2.0), 0.28)
    return a


# ══ Сборка, запекание, экспорт, проверочные рендеры ════════════════════════════════════════════════════════

COMMON = [("GoldenBanana", golden_banana), ("CursedTV", cursed_tv), ("UfoJar", ufo_jar), ("AstroCat", astro_cat),
          ("MagicMushroom", magic_mushroom), ("LivingCassette", living_cassette), ("TrophyBurger", trophy_burger),
          ("CrystalHotDog", crystal_hotdog), ("RoboDuck", robo_duck), ("MagicSoda", magic_soda),
          ("MonsterRadio", monster_radio), ("PocketSafe", pocket_safe)]
RARE = [("MimicChest", mimic_chest), ("PortalMirror", portal_mirror), ("AllSeeingEye", all_seeing_eye),
        ("RoyalDuck", royal_duck), ("MonsterFlower", monster_flower), ("WorldInBottle", world_in_bottle),
        ("MonaLisa", mona_lisa), ("GoldenMic", golden_mic), ("VanGoghSelfPortrait", van_gogh_self_portrait),
        ("GoldenGamepad", golden_gamepad)]
EPIC = [("GoldenThrone", golden_throne), ("BlackCatIdol", black_cat_idol), ("CrystalDino", crystal_dino),
        ("PrizeMachine", prize_machine), ("PocketDragon", pocket_dragon), ("NeonHeart", neon_heart),
        ("SpaceHelmet", space_helmet), ("ChaosCrown", chaos_crown)]
GROUPS = {"common": COMMON, "rare": RARE, "epic": EPIC}
ITEMS = [(i, f, g) for g, items in GROUPS.items() for i, f in items if not ONLY or i in ONLY]

bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new("MadFinds")
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
    uv = S.bake(obj, art, TEXDIR, item_id)
    lo, hi = S.bounds(obj)
    report[item_id] = {**art.stats, **{k: round(v, 3) for k, v in uv.items()},
                       "size": [round(hi[i] - lo[i], 2) for i in range(3)]}
    S.studio_json(obj, os.path.join(PREVIEWS, f"{item_id}.json"))
    S.export_fbx([obj], os.path.join(REPO, "assets", "models", "art", f"{item_id}.fbx"))
    objs.append((obj, group))
    print("ITEM_OK", item_id, report[item_id]["tris"], flush=True)

prev = S.Preview(collection)
heroes = [S.render_item(prev, obj, PREVIEWS) for obj, _ in objs]
S.strip(heroes, os.path.join(PREVIEWS, "sheet.png"), gap=12)

# Общие кадры по редкостям: предметы в ряд и манекен Roblox (5.2 стада).
for group in GROUPS:
    row = [obj for obj, g in objs if g == group]
    if not row:
        continue
    for o, _ in objs:
        o.hide_render = o not in row
    x = 0.0
    for obj in row:
        lo, hi = S.bounds(obj)
        obj.location.x = x - lo.x
        x += (hi.x - lo.x) + 0.7
    S.mannequin(collection, x + 0.9)
    center = Vector(((x + 2.0) / 2, 0, 2.2))
    prev.aim_lights(center)
    span = x + 2.4
    prev.shot(os.path.join(PREVIEWS, f"group_{group}.png"), (center.x, -1.25 * span, 0.12 * span + 2.5),
              (center.x, 0, 1.9), 50, (2000, 760))
    for o in [o for o in collection.objects if o.name.startswith("Mannequin")]:
        bpy.data.objects.remove(o)
    for obj in row:
        obj.location.x = 0
for o, _ in objs:
    o.hide_render = False

with open(os.path.join(PREVIEWS, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("FLEA_OK " + json.dumps({k: v["tris"] for k, v in report.items()}, ensure_ascii=False))
