"""Коллекция босса 1 «Музей чудес» (D40), стиль D39: каждый предмет — своя объёмная модель.

Одобрены владельцем (не менять): голова моаи, «Подсолнухи», череп трицератопса. Партия 2 (на одобрение): золотая
маска Тутанхамона, «Звёздная ночь», египетская кошка, шлем гладиатора. Остальные добавляются сюда же партиями по 4.
Общие инструменты (блоки, кольца D39, изображение на холсте, запекание, рендеры) — art_style.py. Изображения
картин — файлы Wikimedia Commons из общественного достояния (assets/art_sources/SOURCES.md).
Собирать только новые предметы (id в командной строке): пересборка одобренных меняет их карты.

Пишет assets/models/art/<id>.fbx (меш Art_<id>), assets/textures/art/<id>_{color,normal}.png, а в папку превью —
повороты, крупные кадры, общий кадр с манекеном, <id>.json для Studio и report.json.
Запуск: blender --background --factory-startup --python scripts/blender/art_wonders.py -- <репо> <превью> [check] [id…]
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


def tilt(c, axis, deg):
    """Поворот детали вокруг точки c."""
    c = Vector(c)
    return Matrix.Translation(c) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-c)


def painting_image(name, width):
    """Уменьшенная копия исходника картины (PNG в папке превью): холст на карте ≈ 500 пикселей в ширину, при
    запекании на тексель приходится примерно два пикселя исходника — без ряби."""
    img = bpy.data.images.load(os.path.join(SOURCES, name))
    w, h = img.size
    img.scale(width, round(h * width / w))
    path = os.path.join(PREVIEWS, os.path.splitext(name)[0] + ".png")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return path


# ── 1. Голова моаи: высокий каменный блок, нависающие брови, длинный нос, надутые губы, руки на животе ──────────


def moai():
    a = S.Art("Art_Moai", ring_z0=0.25)
    a.paint("stone", "8A8278", rings=True)  # серо-бурый вулканический туф: не белый гипс
    a.paint("ahu", "7A6A58", rings=True)  # платформа аху
    for key, code in (("shadow", "3E3A35"), ("groove", "6A635A"), ("moss", "6DBE45"), ("moss2", "4E9A33")):
        a.paint(key, code)
    # платформа аху в две ступени и пучки травы
    a.box("ahu", -1.0, 1.0, -0.75, 0.75, 0.0, 0.5)
    a.box("ahu", -0.86, 0.86, -0.62, 0.62, 0.48, 0.64)
    for x, y in ((-0.82, -0.58), (0.78, -0.55), (0.85, 0.5), (-0.8, 0.52)):
        a.box("moss2", x - 0.1, x + 0.1, y - 0.08, y + 0.08, 0.48, 0.62, bevel=0)
    # плечи; руки вдоль боков, длинные пальцы на животе
    a.box("stone", -0.72, 0.72, -0.42, 0.48, 0.62, 1.22)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.72, s * 0.78))
        a.box("stone", x0, x1, -0.22, 0.3, 0.66, 1.16)
        x0, x1 = sorted((s * 0.14, s * 0.76))
        a.box("stone", x0, x1, -0.47, -0.4, 0.7, 0.84)
    # голова: высокий блок, тяжёлый подбородок, губы, нос, скулы, брови
    a.box("stone", -0.6, 0.6, -0.5, 0.42, 1.15, 3.0)
    a.box("stone", -0.5, 0.5, -0.68, 0.1, 1.04, 1.5)
    a.box("stone", -0.35, 0.35, -0.75, -0.5, 1.5, 1.75)
    a.box("shadow", -0.29, 0.29, -0.765, -0.7, 1.6, 1.64, bevel=0)  # линия рта
    a.box("stone", -0.17, 0.17, -0.78, -0.45, 1.8, 2.64)  # длинный прямой нос
    a.box("stone", -0.26, 0.26, -0.84, -0.45, 1.76, 2.02)  # кончик носа с крыльями
    a.box("stone", -0.58, 0.58, -0.58, -0.3, 1.95, 2.3)  # скулы
    a.box("stone", -0.63, 0.63, -0.8, -0.3, 2.58, 2.86)  # нависающие брови
    for s in (1, -1):
        x0, x1 = sorted((s * 0.16, s * 0.5))
        a.box("shadow", x0, x1, -0.54, -0.48, 2.28, 2.6, bevel=0)  # глубокие глазницы в тени бровей
        x0, x1 = sorted((s * 0.58, s * 0.7))
        a.box("stone", x0, x1, -0.1, 0.18, 1.72, 2.72)  # длинное ухо
        x0, x1 = sorted((s * 0.68, s * 0.715))
        a.box("groove", x0, x1, -0.02, 0.09, 1.95, 2.45, bevel=0)  # завиток уха — неглубокий, не прорезь
    # мох на макушке и по боку
    a.box("moss", -0.45, 0.12, -0.32, 0.18, 2.97, 3.05, bevel=0)
    a.box("moss2", 0.05, 0.47, -0.08, 0.36, 2.97, 3.035, bevel=0)
    a.box("moss", 0.47, 0.62, 0.02, 0.3, 2.62, 3.025, bevel=0)
    return a


# ── 2. «Подсолнухи»: картина в объёмной золотой раме с синими камнями, медальон-подсолнух, подставка ──────────

FLOWER = ["..Y.Y..",
          ".YYYYY.",
          "YYBBBYY",
          ".YBBBY.",
          "YYBBBYY",
          ".YYYYY.",
          "..Y.Y.."]


def sunflowers():
    z = 0.34  # низ рамы: рама стоит на подставке
    a = S.Art("Art_Sunflowers", ring_z0=z + 0.25)  # ряды квадратов D39 — по центрам верхней и нижней планок
    a.paint("gold", "E8B530", rings=True)
    for key, code in (("gold2", "8F5B1E"), ("gem", "2E5BD8"), ("wood", "4A2C1C"), ("wood2", "5E3A24"),
                      ("back", "3A2418"), ("plate", "F2C230"), ("petal", "FFC531"), ("seed", "7A4A1C")):
        a.paint(key, code)
    # подставка с табличкой и упоры сзади
    a.box("wood", -1.6, 1.6, -0.62, 0.62, 0.0, 0.24)
    a.box("wood2", -1.5, 1.5, -0.5, 0.5, 0.22, z + 0.02)
    a.box("plate", -0.55, 0.55, -0.665, -0.6, 0.05, 0.19, bevel=0)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.82, s * 0.98))
        a.prism("wood2", [(z, 0.24), (z, 0.5), (z + 1.1, 0.24)], x0, x1, axis="x")
    # рама: боковые планки на всю высоту, верхняя и нижняя между ними; ширина 0.44–0.5 — квадрат D39 целиком
    for s in (1, -1):
        x0, x1 = sorted((s * 0.98, s * 1.42))
        a.box("gold", x0, x1, -0.25, 0.25, z, z + 3.5)
    a.box("gold", -0.98, 0.98, -0.25, 0.25, z, z + 0.5)
    a.box("gold", -0.98, 0.98, -0.25, 0.25, z + 3.0, z + 3.5)
    for x in (-1.2, 1.2):  # синие камни в углах — как синяя линия стола на картине
        for zc in (z + 0.25, z + 3.25):
            a.box("gem", x - 0.13, x + 0.13, -0.33, -0.2, zc - 0.13, zc + 0.13)
    # внутренний уступ рамы (тёмный — отделяет жёлтую картину от жёлтой рамы) и холст;
    # окно холста 1.84 × 2.38 (пропорции картины 73 × 92 см, края чуть обрезаны)
    window = (-0.92, 0.92, z + 0.56, z + 2.94)
    a.frame("gold2", [(-1.04, z + 0.44), (1.04, z + 0.44), (1.04, z + 3.06), (-1.04, z + 3.06)], 0.12, -0.18, -0.03,
            axis="y")
    a.paint_image("canvas", painting_image("Sunflowers_NG3863.jpg", 900), window, boost=3.0)
    a.box("canvas", -0.98, 0.98, -0.06, 0.06, z + 0.5, z + 3.0, bevel=0)
    a.box("back", -1.0, 1.0, 0.04, 0.2, z + 0.48, z + 3.02, bevel=0)
    # навершие: ступень и медальон с пиксельным подсолнухом
    a.box("gold", -0.62, 0.62, -0.2, 0.2, z + 3.48, z + 3.76)
    a.prism("gold2", S.octagon(-0.3, 0.3, z + 3.62, z + 4.22, 0.12), -0.24, -0.04, axis="y")
    a.pixels(FLOWER, {"Y": ("petal", 0.03), "B": ("seed", 0.05)}, 0.07, -0.245, z + 4.165, "xz", 0.24)
    return a


# ── 3. Череп трицератопса: три рога, клюв, щит-воротник с шипами по краю, музейная подставка ─────────────────


def triceratops_skull():
    a = S.Art("Art_TriceratopsSkull", ring_z0=1.1)
    a.paint("bone", "E9DDBF", rings=True)
    a.paint("frill", "E2D0A8", rings=True)  # щит чуть темнее черепа
    for key, code in (("horn", "E0C48E"), ("tip", "8E6B45"), ("rim", "C9A876"), ("knob", "B48E5C"),
                      ("beak", "CDB68C"), ("socket", "3B2E24"), ("stand", "34405A"), ("stand2", "46546E"),
                      ("post", "8E98A8"), ("plate", "F2C230")):
        a.paint(key, code)
    # подставка: две ступени, табличка, штырь
    a.box("stand", -1.05, 1.05, -1.1, 1.15, 0.0, 0.22)
    a.box("stand2", -0.9, 0.9, -0.95, 1.0, 0.2, 0.3)
    a.box("plate", -0.35, 0.35, -1.14, -1.08, 0.05, 0.17, bevel=0)
    a.box("post", -0.12, 0.12, -0.12, 0.12, 0.28, 0.6)
    # нижняя челюсть, черепная коробка, морда, клюв сверху и снизу
    a.box("bone", -0.36, 0.36, -1.25, 0.25, 0.55, 0.82)
    a.box("bone", -0.56, 0.56, -0.65, 0.55, 0.78, 1.55)
    a.frustum("bone", (-0.44, 0.44, 0.8, 1.42), (-0.26, 0.26, 0.82, 1.2), -0.6, -1.45, axis="y")
    a.frustum("beak", (-0.28, 0.28, 0.8, 1.22), (-0.07, 0.07, 0.74, 0.86), -1.44, -1.85, axis="y")
    a.frustum("beak", (-0.3, 0.3, 0.55, 0.8), (-0.06, 0.06, 0.62, 0.72), -1.24, -1.62, axis="y")
    # рога: светло-охристые с тёмными кончиками — читаются на светлом черепе
    a.frustum("horn", (-0.13, 0.13, -1.34, -1.08), (-0.07, 0.07, -1.28, -1.14), 1.1, 1.46)  # короткий рог на носу
    a.frustum("tip", (-0.075, 0.075, -1.285, -1.135), (0, 0, -1.21, -1.21), 1.44, 1.68)
    for s in (1, -1):
        # длинный рог над глазом: наклонён вперёд и чуть наружу
        cx = s * 0.32
        m = tilt((cx, -0.36, 1.45), "Y", s * 8) @ tilt((cx, -0.36, 1.45), "X", 30)
        a.frustum("horn", (cx - 0.16, cx + 0.16, -0.52, -0.2), (cx - 0.09, cx + 0.09, -0.45, -0.27), 1.4, 2.3,
                  matrix=m)
        a.frustum("tip", (cx - 0.095, cx + 0.095, -0.455, -0.265), (cx, cx, -0.36, -0.36), 2.28, 2.95, matrix=m)
        a.box("bone", cx - 0.2, cx + 0.2, -0.56, -0.16, 1.5, 1.64)  # основание рога
        x0, x1 = sorted((s * 0.36, s * 0.59))
        a.box("socket", x0, x1, -0.67, -0.24, 1.14, 1.42, bevel=0)  # глазница: видна и спереди, и сбоку
        a.frustum("horn", (s * 0.5 - 0.1, s * 0.5 + 0.1, -0.38, -0.16), (s * 0.74, s * 0.74, -0.27, -0.27), 1.0,
                  0.62, bevel=0)  # скуловой шип: остриё вынесено наружу, фаска на нём выворачивает грани
    # щит-воротник: откинут назад, с рантом и шипами по верхнему краю
    back = tilt((0, 0.48, 1.0), "X", -32)  # щит вдвое шире черепа и откинут назад: спереди не закрывает морду
    a.prism("frill", S.octagon(-1.1, 1.1, 0.9, 2.45, 0.48), 0.38, 0.58, axis="y", matrix=back)
    a.frame("rim", S.octagon(-1.13, 1.13, 0.87, 2.48, 0.49), 0.17, 0.34, 0.62, axis="y", matrix=back)
    for x, zc in ((-0.4, 2.48), (0.0, 2.48), (0.4, 2.48), (-0.885, 2.235), (0.885, 2.235), (-1.13, 1.6),
                  (1.13, 1.6)):
        a.box("knob", x - 0.13, x + 0.13, 0.355, 0.605, zc - 0.13, zc + 0.13,
              matrix=back @ tilt((x, 0.48, zc), "Y", 45))
    return a


# ── 4. Золотая маска Тутанхамона: золотое лицо, платок-немес в синюю полоску, борода, ожерелье-воротник ─────────


def tut_mask():
    a = S.Art("Art_TutMask", ring_z0=1.85)
    a.paint("gold", "EFBF3A", rings=True)  # лицо и шея — крупные золотые грани с квадратами D39
    for key, code in (("nemes", "E5AE2C"), ("lapis", "1F3E9A"), ("turq", "2EC4B6"), ("carn", "D9452B"),
                      ("white", "F5F2E8"), ("black", "15161C"), ("liner", "1B2A6B"), ("line", "A8701C"),
                      ("stand", "1F2433"), ("plate", "F2C230")):
        a.paint(key, code)
    # подставка с табличкой
    a.box("stand", -0.95, 0.95, -0.8, 0.75, 0.0, 0.25)
    a.box("plate", -0.4, 0.4, -0.84, -0.78, 0.06, 0.19, bevel=0)
    # ожерелье-воротник ярусами: лазурит, золото, бирюза, золото, сердолик
    for key, w, y0, y1, z0, z1 in (("lapis", 1.05, -0.72, 0.5, 0.24, 0.4), ("nemes", 0.98, -0.66, 0.47, 0.4, 0.5),
                                   ("turq", 0.9, -0.6, 0.44, 0.5, 0.63), ("nemes", 0.82, -0.54, 0.41, 0.63, 0.72),
                                   ("carn", 0.74, -0.48, 0.38, 0.72, 0.84)):
        a.box(key, -w, w, y0, y1, z0, z1)
    a.box("gold", -0.34, 0.34, -0.32, 0.2, 0.8, 1.4)  # шея
    # немес: ярусы-«крылья» вокруг лица и свисающие на грудь концы; синие полосы — обручи вокруг ярусов
    tiers = ((0.98, -0.38, 0.55, 1.55, 2.05, (1.62, 1.84)), (0.84, -0.36, 0.52, 2.05, 2.45, (2.12, 2.3)),
             (0.66, -0.34, 0.48, 2.45, 2.72, (2.52,)), (0.45, -0.3, 0.4, 2.72, 2.82, ()))
    for w, y0, y1, z0, z1, bands in tiers:
        a.box("nemes", -w, w, y0, y1, z0, z1)
        for zb in bands:
            a.box("lapis", -w - 0.02, w + 0.02, y0 - 0.02, y1 + 0.02, zb, zb + 0.1, bevel=0)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.42, s * 1.0))
        a.box("nemes", x0, x1, -0.5, -0.12, 0.84, 1.6)
        for zb in (0.9, 1.12, 1.34):
            x0, x1 = sorted((s * 0.4, s * 1.02))
            a.box("lapis", x0, x1, -0.52, -0.1, zb, zb + 0.1, bevel=0)
    # немес сзади и по бокам спускается до плеч (полосы — за полосами концов, без общих граней) и косица
    a.box("nemes", -0.88, 0.88, -0.14, 0.5, 0.84, 1.56)
    for zb in (0.9, 1.12, 1.34):
        a.box("lapis", -0.9, 0.9, -0.08, 0.52, zb, zb + 0.1, bevel=0)
    a.box("nemes", -0.18, 0.18, 0.5, 0.68, 1.1, 1.6)
    a.box("lapis", -0.2, 0.2, 0.48, 0.7, 1.24, 1.34, bevel=0)
    # лицо: глаза с подводкой, брови, нос, губы, уши; надо лбом — повязка, кобра и коршун
    a.box("gold", -0.36, 0.36, -0.66, -0.25, 1.32, 2.38)
    a.box("nemes", -0.62, 0.62, -0.7, -0.34, 2.34, 2.46)
    a.box("lapis", -0.05, 0.05, -0.8, -0.66, 2.3, 2.6)  # кобра
    a.box("nemes", -0.08, 0.08, -0.83, -0.76, 2.5, 2.64)
    a.box("nemes", -0.17, -0.08, -0.79, -0.68, 2.36, 2.52)  # голова коршуна
    for s in (1, -1):
        x0, x1 = sorted((s * 0.07, s * 0.27))
        a.box("white", x0, x1, -0.69, -0.64, 1.96, 2.1, bevel=0)
        x0, x1 = sorted((s * 0.13, s * 0.2))
        a.box("black", x0, x1, -0.7, -0.67, 1.97, 2.09, bevel=0)
        x0, x1 = sorted((s * 0.05, s * 0.29))
        a.box("liner", x0, x1, -0.695, -0.645, 2.1, 2.15, bevel=0)  # подводка сверху
        x0, x1 = sorted((s * 0.27, s * 0.35))
        a.box("liner", x0, x1, -0.68, -0.64, 2.03, 2.07, bevel=0)  # «хвостик» подводки к виску
        x0, x1 = sorted((s * 0.06, s * 0.3))
        a.box("liner", x0, x1, -0.685, -0.64, 2.2, 2.26, bevel=0)  # бровь
        x0, x1 = sorted((s * 0.36, s * 0.47))
        a.box("gold", x0, x1, -0.42, -0.26, 1.78, 2.03)  # ухо
    a.box("gold", -0.07, 0.07, -0.74, -0.6, 1.68, 1.98)  # нос
    a.box("gold", -0.14, 0.14, -0.69, -0.6, 1.46, 1.62)  # губы
    a.box("line", -0.13, 0.13, -0.705, -0.68, 1.53, 1.56, bevel=0)
    # накладная борода в золотых обручах, кончик загнут вперёд
    a.box("lapis", -0.1, 0.1, -0.62, -0.4, 0.92, 1.34)
    for zb in (1.0, 1.12, 1.24):
        a.box("nemes", -0.12, 0.12, -0.64, -0.38, zb, zb + 0.05, bevel=0)
    a.box("lapis", -0.11, 0.11, -0.7, -0.45, 0.86, 0.96)
    return a


# ── 5. «Звёздная ночь»: горизонтальная картина в эпической раме — фиолетовые камни, медальон с полумесяцем ──────

MOON = ["..YYY..",
        ".YY....",
        "YY...W.",
        "YY..WWW",
        "YY...W.",
        ".YY....",
        "..YYY.."]


def starry_night():
    # Центр по x сдвинут на полшага сетки: боковые планки — ровно на столбцах квадратов D39 (x = −1.2 и 1.8),
    # верхняя и нижняя — на рядах (через 2.4). Окно холста 2.44 × 1.86 (картина 92 × 73 см, края чуть обрезаны).
    z, cx = 0.34, 0.3
    a = S.Art("Art_StarryNight", ring_z0=z + 0.22)
    a.paint("gold", "E8B530", rings=True)
    for key, code in (("night", "1E3A8A"), ("gem", "9A3EF0"), ("wood", "4A2C1C"), ("wood2", "5E3A24"),
                      ("back", "3A2418"), ("plate", "F2C230"), ("moon", "FFD84A"), ("star", "FFFFFF")):
        a.paint(key, code)
    # подставка с табличкой и упоры сзади
    a.box("wood", cx - 1.85, cx + 1.85, -0.62, 0.62, 0.0, 0.24)
    a.box("wood2", cx - 1.78, cx + 1.78, -0.5, 0.5, 0.22, z + 0.02)
    a.box("plate", cx - 0.6, cx + 0.6, -0.665, -0.6, 0.05, 0.19, bevel=0)
    for x in (cx - 1.3, cx + 1.3):
        a.prism("wood2", [(z, 0.24), (z, 0.5), (z + 1.0, 0.24)], x - 0.08, x + 0.08, axis="x")
    # рама: планки 0.44, квадраты D39 целиком
    a.box("gold", -1.42, -0.98, -0.25, 0.25, z, z + 2.84)
    a.box("gold", 1.58, 2.02, -0.25, 0.25, z, z + 2.84)
    a.box("gold", -0.98, 1.58, -0.25, 0.25, z, z + 0.44)
    a.box("gold", -0.98, 1.58, -0.25, 0.25, z + 2.4, z + 2.84)
    for x in (-1.2, 1.8):  # фиолетовые камни (цвет Epic) в углах и посередине боковых планок
        for zc in (z + 0.22, z + 1.42, z + 2.62):
            a.box("gem", x - 0.13, x + 0.13, -0.33, -0.2, zc - 0.13, zc + 0.13)
    # тёмно-синий уступ (небо картины переходит в раму), холст, задник
    window = (-0.92, 1.52, z + 0.47, z + 2.37)
    a.frame("night", [(-1.04, z + 0.35), (1.64, z + 0.35), (1.64, z + 2.49), (-1.04, z + 2.49)], 0.12, -0.18, -0.03,
            axis="y")
    a.paint_image("canvas", painting_image("StarryNight_MoMA.jpg", 1100), window, boost=3.0)
    a.box("canvas", -0.98, 1.58, -0.06, 0.06, z + 0.44, z + 2.4, bevel=0)
    a.box("back", -1.0, 1.6, 0.04, 0.2, z + 0.42, z + 2.42, bevel=0)
    # навершие: ступень и медальон с полумесяцем и звездой
    a.box("gold", cx - 0.8, cx + 0.8, -0.2, 0.2, z + 2.82, z + 3.08)
    a.prism("night", S.octagon(cx - 0.34, cx + 0.34, z + 2.96, z + 3.64, 0.13), -0.24, -0.04, axis="y")
    a.pixels(MOON, {"Y": ("moon", 0.03), "W": ("star", 0.04)}, 0.07, cx - 0.245, z + 3.545, "xz", 0.24)
    return a


# ── 6. Египетская кошка: сидящая чёрная кошка с золотыми серьгой, кольцом в носу и амулетом, постамент ──────────

ANKH = [".###.",
        "#...#",
        ".###.",
        "#####",
        "..#..",
        "..#.."]
WEDJAT = [".###.",
          "#.#.#",
          ".###.",
          "..#.."]


def egyptian_cat():
    a = S.Art("Art_EgyptianCat", ring_z0=1.2)
    a.paint("fur", "2C2D36", rings=True)  # чёрная бронза (с синевой в Studio читалась как тёмно-синяя)
    a.paint("sand", "D9B878", rings=True)  # постамент из песчаника
    for key, code in (("gold", "F2C230"), ("lapis", "1F3E9A"), ("eye", "B8E04A"), ("black", "101014")):
        a.paint(key, code)
    # постамент с синей табличкой и тремя золотыми анхами
    a.box("sand", -0.62, 0.62, -0.8, 0.7, 0.0, 0.32)
    a.box("lapis", -0.42, 0.42, -0.83, -0.79, 0.05, 0.27, bevel=0)
    for x in (-0.25, 0.0, 0.25):
        a.pixels(ANKH, {"#": ("gold", 0.02)}, 0.03, x - 0.075, 0.25, "xz", 0.83)
    # задние лапы и бёдра, хвост вдоль бока к передним лапам
    a.box("fur", -0.42, 0.42, -0.25, 0.6, 0.3, 0.82)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.25, s * 0.45))
        a.box("fur", x0, x1, -0.42, -0.1, 0.3, 0.42)
    a.box("fur", 0.42, 0.54, -0.55, 0.62, 0.3, 0.4)
    a.box("fur", 0.3, 0.54, -0.68, -0.55, 0.3, 0.4)
    # прямые передние лапы, грудь, шея
    for s in (1, -1):
        x0, x1 = sorted((s * 0.05, s * 0.27))
        a.box("fur", x0, x1, -0.7, -0.36, 0.3, 0.44)
        x0, x1 = sorted((s * 0.07, s * 0.25))
        a.box("fur", x0, x1, -0.62, -0.38, 0.4, 1.12)
    a.box("fur", -0.3, 0.3, -0.42, 0.4, 0.75, 1.5)
    a.box("fur", -0.27, 0.27, -0.38, 0.25, 1.45, 1.62)
    # голова, мордочка, нос, высокие уши
    a.box("fur", -0.32, 0.32, -0.55, -0.02, 1.58, 2.02)
    a.box("fur", -0.15, 0.15, -0.65, -0.45, 1.6, 1.78)
    a.box("black", -0.05, 0.05, -0.67, -0.63, 1.74, 1.79, bevel=0)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.1, s * 0.3))
        a.frustum("fur", (x0, x1, -0.36, -0.14), (s * 0.22, s * 0.22, -0.25, -0.25), 1.98, 2.45, bevel=0)
        x0, x1 = sorted((s * 0.08, s * 0.24))
        a.box("eye", x0, x1, -0.58, -0.54, 1.78, 1.88, bevel=0)
        x0, x1 = sorted((s * 0.145, s * 0.175))
        a.box("black", x0, x1, -0.59, -0.56, 1.785, 1.875, bevel=0)  # зрачок-щёлочка
    # золото: серьга в левом ухе, ошейник, амулет-уаджет
    a.box("gold", 0.29, 0.35, -0.27, -0.21, 1.86, 1.98, bevel=0)
    a.box("gold", -0.33, 0.33, -0.45, 0.43, 1.4, 1.48)
    a.box("gold", -0.13, 0.13, -0.46, -0.42, 1.18, 1.38)
    a.pixels(WEDJAT, {"#": ("lapis", 0.02)}, 0.04, -0.1, 1.36, "xz", 0.46)
    return a


# ── 7. Шлем гладиатора: бронзовый купол, решётчатое забрало, гребень с красным плюмажем, широкие поля ─────────────

GRILLE = ["..#.#.#.#..",
          ".#.#.#.#.#.",
          "#.#.#.#.#.#",
          ".#.#.#.#.#.",
          "#.#.#.#.#.#",
          ".#.#.#.#.#.",
          "#.#.#.#.#.#",
          "..#.#.#.#.."]


def gladiator_helmet():
    a = S.Art("Art_GladiatorHelmet", ring_z0=1.3)
    a.paint("bronze", "D19A3E", rings=True)
    a.paint("stone", "5C6270", rings=True)  # постамент
    for key, code in (("bronze2", "A8722C"), ("hole", "1E1A16"), ("plume", "D8352A"), ("plume2", "A82222"),
                      ("rivet", "F4D27A"), ("wood", "4A2C1C"), ("plate", "F2C230")):
        a.paint(key, code)
    # постамент с табличкой и деревянная «шея», на которой стоит шлем
    a.box("stone", -0.75, 0.75, -0.75, 0.75, 0.0, 0.3)
    a.box("plate", -0.35, 0.35, -0.79, -0.73, 0.07, 0.22, bevel=0)
    a.box("wood", -0.3, 0.3, -0.3, 0.3, 0.28, 0.64)
    a.transform = Matrix.Translation((0, 0, -0.3))  # шлем ниже: короткая шея, а не гриб на ножке
    # восьмиугольные поля, купол со скатом, обод с заклёпками
    a.prism("bronze2", S.octagon(-0.92, 0.92, -0.92, 0.92, 0.32), 0.86, 0.96)
    a.box("bronze", -0.6, 0.6, -0.6, 0.6, 0.94, 1.5)
    a.frustum("bronze", (-0.6, 0.6, -0.6, 0.6), (-0.36, 0.36, -0.36, 0.36), 1.5, 2.02)
    a.box("bronze2", -0.62, 0.62, -0.62, 0.62, 0.96, 1.06)
    for s in (1, -1):
        for y in (-0.3, 0.1, 0.5):
            x0, x1 = sorted((s * 0.62, s * 0.66))
            a.box("rivet", x0, x1, y - 0.04, y + 0.04, 0.99, 1.04, bevel=0)
    # забрало: восьмиугольная пластина в рамке и частая решётка (без ребра — иначе «две дверцы»)
    a.prism("bronze2", S.octagon(-0.47, 0.47, 1.0, 1.7, 0.16), -0.72, -0.58, axis="y")
    a.frame("bronze", S.octagon(-0.5, 0.5, 0.97, 1.73, 0.17), 0.07, -0.76, -0.6, axis="y")
    a.pixels(GRILLE, {"#": ("hole", 0.01)}, 0.07, -0.385, 1.63, "xz", 0.72)
    # гребень и большой красный плюмаж-щётка: передний край свисает вперёд, хвост — назад
    a.box("bronze", -0.07, 0.07, -0.42, 0.5, 1.98, 2.3)
    a.box("plume", -0.16, 0.16, -0.55, 0.62, 2.26, 2.76)
    a.box("plume", -0.13, 0.13, -0.42, 0.48, 2.74, 2.96)
    a.box("plume", -0.14, 0.14, -0.7, -0.5, 2.06, 2.62)
    a.box("plume", -0.12, 0.12, 0.58, 0.84, 1.7, 2.66)
    for y in (-0.42, -0.2, 0.02, 0.24, 0.46):  # тёмные пряди щётки
        a.box("plume2", -0.17, 0.17, y - 0.03, y + 0.03, 2.3, 2.74, bevel=0)
    return a


# ── Сборка, запекание, экспорт, проверочные рендеры ─────────────────────────────────────────────────────────

ITEMS = [("Moai", moai), ("Sunflowers", sunflowers), ("TriceratopsSkull", triceratops_skull), ("TutMask", tut_mask),
         ("StarryNight", starry_night), ("EgyptianCat", egyptian_cat), ("GladiatorHelmet", gladiator_helmet)]
ITEMS = [(i, f) for i, f in ITEMS if not ONLY or i in ONLY]

bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new("Wonders")
bpy.context.scene.collection.children.link(collection)

if CHECK:
    for item_id, make in ITEMS:
        art = make()
        art.build(collection)
        print("CHECK", item_id, json.dumps(art.stats, ensure_ascii=False))
    sys.exit(0)

report, objs = {}, []
for item_id, make in ITEMS:
    art = make()
    obj = art.build(collection)
    uv = S.bake(obj, art, TEXDIR, item_id)
    lo, hi = S.bounds(obj)
    report[item_id] = {**art.stats, **{k: round(v, 3) for k, v in uv.items()},
                       "size": [round(hi[i] - lo[i], 2) for i in range(3)]}
    S.studio_json(obj, os.path.join(PREVIEWS, f"{item_id}.json"))
    S.export_fbx([obj], os.path.join(REPO, "assets", "models", "art", f"{item_id}.fbx"))
    objs.append(obj)

prev = S.Preview(collection)
heroes = [S.render_item(prev, obj, PREVIEWS) for obj in objs]
S.strip(heroes, os.path.join(PREVIEWS, "sheet.png"), gap=12)

# Общий кадр: предметы в ряд и манекен Roblox (5.2 стада).
x = -5.0
for obj in objs:
    lo, hi = S.bounds(obj)
    obj.location.x = x - lo.x
    x += (hi.x - lo.x) + 0.8
S.mannequin(collection, x + 0.9)
center = Vector(((-5.0 + x + 2.4) / 2, 0, 2.4))
prev.aim_lights(center)
prev.shot(os.path.join(PREVIEWS, "group.png"), (center.x, -22.0, 4.8), (center.x, 0, 2.3), 50, (1600, 800))

with open(os.path.join(PREVIEWS, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("WONDERS_OK " + json.dumps(report, ensure_ascii=False))
