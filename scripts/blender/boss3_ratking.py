"""Босс 3 «Крысиный король» (D54), стиль D39: подвижная модель из частей для процедурных анимаций (D18), как пёс и
торговец.

Важный, самодовольный и смешной король подземки — не хоррор. Стоит на задних лапах; голова шире тела: пухлые светлые
щёки, длинная кремовая морда ступенями, большой розовый нос, два крупных белых резца в тёмной обводке, усы веером;
большие глаза с бликами под полуприкрытыми веками, одна бровь задрана; огромные круглые уши с розовой чашей. Тело —
груша: кремовое брюхо, фиолетовый пояс с пряжкой, золотая цепь с медальоном-сыром, горностаевый воротник мантии.
Корона чуть мала и сидит набекрень (рубины, сапфиры, изумруды, жемчуг), красный плащ ступенями со складками,
горностаевой опушкой и золотой эмблемой на спине; кошель монет на бедре; скипетр — фонарь обходчика на золотом жезле;
длинный розовый хвост «S» с кольцами и золотым перстнем; длинные розовые ступни. В стойке ≈ 15 стадов.

Формы — ступенями из блоков и восьмигранников с острыми рёбрами (D39: силуэт ступенями, без мягких скруглений),
квадраты-контуры D39 на крупных деталях, мелкие накладки (глаза, брови, пятнышки) — гладкие.

Части (Motor6D): Torso (корень) → Head → Jaw, EyelidL/R, EarL/R, Crown; Torso → Cape, Pouch, Tail1 → Tail2;
руки и ноги из двух частей (ArmUpper → ArmLower, LegUpper → LegLower), ArmLowerR → Scepter; L — левый бок босса (+x).
Веки в модели закрыты (сон); в позах сдвигаются: вверх под надбровье — самодовольный прищур, назад внутрь головы —
глаза открыты (как у пса — сдвигом, Motor6D не масштабирует). Собрано в масштабе предметов (квадраты D39 того же вида),
затем увеличено в SCALE раз. Три карты 1024² (голова; туловище с плащом и хвостом; руки, ноги, скипетр и корона);
окклюзия запекается с разнесёнными частями, чтобы в любой позе не было чужих теней.

Пишет assets/models/Boss3_RatKing.fbx (части Boss3_RatKing<Карта>_<Часть>, начало координат — точка вращения),
assets/textures/art/Boss3_RatKing{Head,Body,Limbs}_{color,normal}.png, а в папку превью — ракурсы, позы, кадр с
манекеном, крупный план, RatKing_<часть>.json и rig.json для Studio. Режимы: check — сборка и проверки; quick —
рендеры без запекания (материалы сборки); where — где кисть, фонарь и корона в позах; rig — модуль скелета для игры
(src/shared/Config/Boss3RatKingRig.luau). Переменная окружения RATKING_SHOTS (turns | poses | hero | all)
ограничивает рендеры.
Запуск: blender --background --factory-startup --python scripts/blender/boss3_ratking.py -- <репо> <превью>
[check|quick|where|rig]
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, PREVIEWS = os.path.abspath(argv[0]), os.path.abspath(argv[1])
MODE = argv[2] if len(argv) > 2 else ""
TEXDIR = os.path.join(REPO, "assets", "textures", "art")
os.makedirs(PREVIEWS, exist_ok=True)

SCALE = 3.0  # в игре босс в SCALE раз больше модели
# Быстрый просмотр: меш не масштабируется, масштаб — у объекта (рисунок D39 в материалах сборки — в единицах модели).
OBJ_SCALE = Matrix.Scale(SCALE, 4) if MODE == "quick" else Matrix.Identity(4)

# Часть → (родитель, точка вращения в координатах модели).
RIG = {
    "Torso": (None, (0.0, 0.05, 0.95)),
    "Head": ("Torso", (0.0, 0.0, 2.36)),
    "Jaw": ("Head", (0.0, -0.45, 2.42)),
    "EyelidL": ("Head", (0.4, -0.7, 3.86)),
    "EyelidR": ("Head", (-0.4, -0.7, 3.86)),
    "EarL": ("Head", (0.78, 0.1, 3.85)),
    "EarR": ("Head", (-0.78, 0.1, 3.85)),
    "Crown": ("Head", (0.0, 0.04, 4.2)),
    "Cape": ("Torso", (0.0, 0.6, 2.3)),
    "Pouch": ("Torso", (0.98, -0.2, 1.3)),
    "Tail1": ("Torso", (0.0, 0.6, 0.62)),
    "Tail2": ("Tail1", (0.0, 1.72, 0.22)),
}
for side, s in (("L", 1), ("R", -1)):
    RIG["ArmUpper" + side] = ("Torso", (s * 0.96, 0.0, 2.2))
    RIG["ArmLower" + side] = ("ArmUpper" + side, (s * 0.98, 0.0, 1.72))
    RIG["LegUpper" + side] = ("Torso", (s * 0.68, 0.05, 0.86))
    RIG["LegLower" + side] = ("LegUpper" + side, (s * 0.67, 0.08, 0.38))
RIG["Scepter"] = ("ArmLowerR", (-0.99, -0.02, 1.07))

MAPS = {"Head": ("Head", "Jaw", "EyelidL", "EyelidR", "EarL", "EarR"),
        "Body": ("Torso", "Cape", "Pouch", "Tail1", "Tail2"),
        "Limbs": tuple(p + side for p in ("ArmUpper", "ArmLower", "LegUpper", "LegLower") for side in ("L", "R"))
        + ("Scepter", "Crown")}
MAP_OF = {part: m for m, parts in MAPS.items() for part in parts}


def colors(a):
    a.paint("fur", "8790B0", rings=True)  # серо-голубая шерсть
    a.paint("furlight", "A8AFCB", rings=True)  # щёки светлее черепа
    a.paint("cream", "F2E6CF", rings=True)  # морда, брюхо
    a.paint("pink", "F49AB0", rings=True)  # уши внутри, нос, лапы, хвост
    a.paint("cape", "D8352A", rings=True)
    a.paint("cape2", "B82A22", rings=True)  # складки плаща в тени
    a.paint("ermine", "F7F4EE", rings=True)  # горностай
    a.paint("gold", "F2C230", rings=True)
    a.paint("velvet", "6B3FB8", rings=True)  # пояс, кошель, шапочка короны, обмотка скипетра
    for key, code in (("pinkdark", "D9768F"), ("tooth", "FFFFFF"), ("eye", "FAFAF5"), ("dark", "1C1B22"),
                      ("glint", "FFFFFF"), ("brow", "3E3550"), ("whisker", "4A4560"), ("mouth", "6E1E2C"),
                      ("tongue", "F07A8C"), ("rim", "B87A12"), ("ruby", "E53935"), ("sapphire", "2F7DE1"),
                      ("emerald", "2E9E4F"), ("pearl", "FFF1D6"), ("spot", "1B1B1B"), ("cheese", "F6C445"),
                      ("hole", "D9A21E"), ("lamp", "FFB23F"), ("core", "FFF0B0"), ("blush", "F28FAA"),
                      ("velvet2", "55309A"), ("claw", "FFF3E0")):
        a.paint(key, code)


def tilt(c, axis, deg):
    """Поворот детали вокруг точки c."""
    c = Vector(c)
    return Matrix.Translation(c) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-c)


def bar(a, key, p0, p1, w, h=None, bevel=S.BEVEL):
    """Брусок от точки p0 до p1 с сечением w × h (усы, звенья цепи, хвост)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    up = "Y" if abs(d.normalized().z) > 0.95 else "Z"
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("X", up).to_matrix().to_4x4()
    h = h or w
    a.box(key, -d.length / 2, d.length / 2, -w / 2, w / 2, -h / 2, h / 2, bevel=bevel, matrix=m)


def oct_y(a, key, x0, x1, z0, z1, cut, y0, y1, matrix=None):
    """Восьмигранник в плоскости x–z, вытянутый вдоль y (спереди — со срезанными углами)."""
    a.prism(key, S.octagon(x0, x1, z0, z1, cut), y0, y1, axis="y", matrix=matrix)


def oct_z(a, key, x0, x1, y0, y1, cut, z0, z1, matrix=None):
    """Восьмигранник в плоскости x–y, вытянутый вдоль z (сверху — со срезанными углами)."""
    a.prism(key, S.octagon(x0, x1, y0, y1, cut), z0, z1, axis="z", matrix=matrix)


def oct_x(a, key, z0, z1, y0, y1, cut, x0, x1, matrix=None):
    """Восьмигранник в плоскости z–y, вытянутый вдоль x (сбоку — со срезанными углами)."""
    a.prism(key, S.octagon(z0, z1, y0, y1, cut), x0, x1, axis="x", matrix=matrix)


def regular_oct(cx, cz, r):
    """Правильный восьмиугольник радиуса r (до стороны) с центром (cx, cz) — «пиксельный круг»."""
    return S.octagon(cx - r, cx + r, cz - r, cz + r, r * (2 - math.sqrt(2)))


CROWN = ["#..#..#",
         "##.#.##",
         "#######",
         "#######"]


# ── Голова: щёки, череп, надбровье, морда, нос, резцы, усы, глаза, брови, уши; челюсть, веки ─────────────────


def king_head():
    a = S.Art("Boss3_RatKingHead", ring_z0=3.3)
    colors(a)
    a.group = "Head"
    # щёки — самая широкая часть головы, двумя слоями (спереди и сбоку — ступени вместо скругления)
    oct_y(a, "furlight", -1.0, 1.0, 2.32, 3.3, 0.3, -0.52, 0.42)
    oct_y(a, "furlight", -0.86, 0.86, 2.4, 3.22, 0.24, -0.6, 0.5)
    # череп и темя: спереди восьмигранник, сверху сбоку — скос
    oct_y(a, "fur", -0.84, 0.84, 2.9, 4.12, 0.28, -0.48, 0.62)
    oct_y(a, "fur", -0.68, 0.68, 3.0, 4.06, 0.22, -0.58, 0.74)
    oct_x(a, "fur", 3.6, 4.24, -0.4, 0.58, 0.16, -0.62, 0.62)
    # надбровье-козырёк: под ним прячутся поднятые веки, на нём брови
    oct_y(a, "fur", -0.78, 0.78, 3.8, 4.3, 0.12, -0.8, -0.3)
    # морда ступенями: основание, кончик, спинка носа скатом ко лбу, большой нос с бликом и ноздрями
    oct_y(a, "cream", -0.58, 0.58, 2.42, 3.18, 0.18, -0.95, -0.45)
    oct_y(a, "cream", -0.44, 0.44, 2.5, 3.1, 0.14, -1.2, -0.9)
    a.prism("fur", [(2.98, -1.1), (2.98, -0.5), (3.62, -0.5), (3.22, -1.1)], -0.17, 0.17, axis="x")
    oct_y(a, "pink", -0.23, 0.23, 2.92, 3.26, 0.08, -1.36, -1.08)
    a.box("glint", 0.04, 0.12, -1.38, -1.355, 3.15, 3.21, bevel=0)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.06, s * 0.15))
        a.box("pinkdark", x0, x1, -1.38, -1.355, 2.97, 3.03, bevel=0)
    a.box("mouth", -0.38, 0.38, -1.12, -0.5, 2.36, 2.46, bevel=0)  # пасть изнутри — видна, когда челюсть опущена
    # два крупных белых резца в тёмной обводке
    a.box("mouth", -0.23, 0.23, -1.1, -1.04, 2.1, 2.52, bevel=0)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.025, s * 0.2))
        a.box("tooth", x0, x1, -1.17, -1.07, 2.13, 2.54, bevel=0.012)
    # усы веером
    for s in (1, -1):
        for z, dz in ((2.98, 0.2), (2.9, 0.02), (2.82, -0.16)):
            bar(a, "whisker", (s * 0.54, -0.8, z), (s * 1.5, -0.7, z + dz), 0.045, bevel=0)
    # глаза: белки, крупные зрачки, два блика (у обоих глаз с одной стороны), румянец
    for s in (1, -1):
        x0, x1 = sorted((s * 0.18, s * 0.62))
        a.box("eye", x0, x1, -0.66, -0.5, 3.22, 3.84, bevel=0.03)
        x0, x1 = sorted((s * 0.2, s * 0.52))
        a.box("dark", x0, x1, -0.685, -0.65, 3.26, 3.66, bevel=0)
        g0 = 0.4 if s > 0 else -0.33
        a.box("glint", g0, g0 + 0.09, -0.7, -0.68, 3.5, 3.59, bevel=0)
        g1 = 0.24 if s > 0 else -0.48
        a.box("glint", g1, g1 + 0.05, -0.7, -0.68, 3.31, 3.36, bevel=0)
        x0, x1 = sorted((s * 0.6, s * 0.84))
        a.box("blush", x0, x1, -0.615, -0.59, 2.8, 2.94, bevel=0)
    # брови: левая (+x) задрана и изогнута, правая ниже и опущена к носу — самодовольная гримаса
    a.box("brow", 0.14, 0.7, -0.85, -0.78, 4.16, 4.28, bevel=0, matrix=tilt((0.42, -0.8, 4.22), "Y", -10))
    a.box("brow", -0.7, -0.14, -0.85, -0.78, 3.93, 4.05, bevel=0, matrix=tilt((-0.42, -0.8, 3.99), "Y", 11))
    # ухмылка: уголок рта задран к левой щеке
    bar(a, "mouth", (0.2, -0.97, 2.48), (0.42, -0.97, 2.58), 0.05, 0.065, bevel=0)
    a.box("mouth", 0.39, 0.47, -1.0, -0.94, 2.57, 2.65, bevel=0)

    for side, s in (("L", 1), ("R", -1)):
        a.group = "Ear" + side  # огромное круглое ухо: шерстяной обод, розовая чаша внутри, развёрнуто вперёд-наружу
        p = (s * 0.78, 0.1, 3.85)
        m = tilt(p, "Z", s * 22) @ tilt(p, "Y", -s * 10)
        c = s * 1.22
        a.frame("fur", regular_oct(c, 4.2, 0.64), 0.14, 0.04, 0.26, axis="y", matrix=m)
        a.prism("fur", regular_oct(c, 4.2, 0.52), 0.17, 0.26, axis="y", matrix=m)
        a.prism("pink", regular_oct(c, 4.2, 0.51), 0.12, 0.18, axis="y", matrix=m)


    a.group = "Jaw"  # подбородок шерстяной: на нём видны белые резцы
    oct_y(a, "furlight", -0.4, 0.4, 2.12, 2.42, 0.1, -1.02, -0.4)
    a.box("tongue", -0.22, 0.22, -0.92, -0.5, 2.4, 2.445, bevel=0)

    for side, s in (("L", 1), ("R", -1)):
        a.group = "Eyelid" + side  # закрытое веко с чертой ресниц
        x0, x1 = sorted((s * 0.16, s * 0.64))
        a.box("fur", x0, x1, -0.735, -0.675, 3.2, 3.86, bevel=0)
        a.box("brow", x0 - 0.005, x1 + 0.005, -0.745, -0.725, 3.195, 3.245, bevel=0)
    return a


def king_crown(a):
    """Корона чуть мала и сидит набекрень (часть Crown, карта Limbs: на карте головы ей не хватало места)."""
    a.group = "Crown"
    cy, z0 = 0.04, 4.2
    a.transform = tilt((0.0, cy, z0), "Y", -12) @ Matrix.Translation((0.12, 0.0, 0.0))
    a.box("velvet", -0.42, 0.42, cy - 0.42, cy + 0.42, z0 - 0.02, z0 + 0.42)  # бархатная шапочка ступенями
    a.box("velvet", -0.3, 0.3, cy - 0.3, cy + 0.3, z0 + 0.4, z0 + 0.52)
    a.frame("rim", S.octagon(-0.64, 0.64, cy - 0.64, cy + 0.64, 0.19), 0.09, z0 - 0.05, z0 + 0.07, axis="z")
    a.frame("gold", S.octagon(-0.6, 0.6, cy - 0.6, cy + 0.6, 0.18), 0.14, z0 - 0.01, z0 + 0.34, axis="z")
    for y in (cy - 0.53, cy + 0.53):
        for x, h in ((-0.34, 0.34), (0.0, 0.52), (0.34, 0.34)):
            a.frustum("gold", (x - 0.11, x + 0.11, y - 0.06, y + 0.06), (x, x, y, y), z0 + 0.32, z0 + 0.32 + h,
                      bevel=0)
            tip = "ruby" if (x == 0.0 and y < cy) else "pearl"
            a.box(tip, x - 0.065, x + 0.065, y - 0.065, y + 0.065, z0 + 0.26 + h, z0 + 0.39 + h, bevel=0)
    for x in (-0.53, 0.53):
        a.frustum("gold", (x - 0.06, x + 0.06, cy - 0.11, cy + 0.11), (x, x, cy, cy), z0 + 0.32, z0 + 0.68, bevel=0)
        a.box("pearl", x - 0.06, x + 0.06, cy - 0.06, cy + 0.06, z0 + 0.62, z0 + 0.74, bevel=0)
    for sgn in (-1, 1):  # камни на ободе спереди и сзади: утоплены на 0.02, выступают на 0.06
        y0, y1 = sorted((cy + sgn * 0.58, cy + sgn * 0.66))
        a.prism("ruby" if sgn < 0 else "emerald", S.octagon(-0.12, 0.12, z0 + 0.06, z0 + 0.28, 0.05), y0, y1,
                axis="y")
        for x in (-0.36, 0.36):
            a.box("sapphire", x - 0.07, x + 0.07, y0, y1, z0 + 0.09, z0 + 0.25, bevel=0)
    for sgn in (-1, 1):
        x0, x1 = sorted((sgn * 0.58, sgn * 0.66))
        a.box("emerald", x0, x1, cy - 0.08, cy + 0.08, z0 + 0.09, z0 + 0.25, bevel=0)
    a.box("gold", -0.1, 0.1, cy - 0.1, cy + 0.1, z0 + 0.5, z0 + 0.68)  # держава с крестиком
    a.box("gold", -0.03, 0.03, cy - 0.03, cy + 0.03, z0 + 0.67, z0 + 0.88)
    a.box("gold", -0.1, 0.1, cy - 0.025, cy + 0.025, z0 + 0.76, z0 + 0.82)
    a.transform = None


# ── Туловище: таз, брюхо, грудь, пояс с пряжкой, горностаевый воротник, цепь с медальоном-сыром; плащ ступенями со
#    складками, опушкой и эмблемой; кошель; хвост из двух частей ────────────────────────────────────────────────


def cape_tier(a, z0, z1, hw, y0, back, deep, side_from, inner=(0.62, 0.22)):
    """Ярус плаща: полосы-складки разной глубины (выступающие — красные, утопленные — в тени), бока заходят вперёд
    до side_from, по краям — золотая кромка."""
    edges = [-hw, -inner[0], -inner[1], inner[1], inner[0], hw]
    for i in range(5):
        a.box("cape" if deep[i] >= max(deep) - 1e-6 or i == 2 else "cape2", edges[i], edges[i + 1], y0,
              back + deep[i], z0, z1)
    for s in (1, -1):
        x0, x1 = sorted((s * (hw - 0.16), s * hw))
        a.box("cape", x0, x1, side_from, y0 + 0.02, z0, z1)
        x0, x1 = sorted((s * (hw - 0.09), s * (hw + 0.025)))  # кромка по заднему ребру
        a.box("gold", x0, x1, back + deep[0] - 0.08, back + deep[0] + 0.025, z0 + 0.01, z1 - 0.01, bevel=0)
        x0, x1 = sorted((s * (hw - 0.18), s * (hw + 0.025)))  # и по переднему краю бока
        a.box("gold", x0, x1, side_from - 0.025, side_from + 0.08, z0 + 0.01, z1 - 0.01, bevel=0)


def king_body():
    a = S.Art("Boss3_RatKingBody", ring_z0=1.5)
    colors(a)
    a.group = "Torso"
    oct_z(a, "fur", -0.98, 0.98, -0.6, 0.62, 0.32, 0.4, 1.4)  # таз — низ груши
    oct_z(a, "fur", -0.82, 0.82, -0.48, 0.52, 0.26, 0.28, 0.42)
    oct_z(a, "fur", -0.8, 0.8, -0.5, 0.52, 0.24, 1.38, 2.3)  # грудь уже
    oct_y(a, "cream", -0.66, 0.66, 0.52, 1.86, 0.24, -0.74, -0.3)  # брюхо выпирает
    oct_y(a, "cream", -0.44, 0.44, 1.8, 2.26, 0.12, -0.62, -0.3)
    oct_z(a, "velvet", -1.0, 1.0, -0.78, 0.66, 0.34, 1.26, 1.42)  # пояс
    oct_y(a, "rim", -0.2, 0.2, 1.2, 1.48, 0.06, -0.84, -0.76)  # пряжка
    oct_y(a, "gold", -0.16, 0.16, 1.24, 1.44, 0.05, -0.87, -0.82)
    # горностаевый воротник мантии двумя ступенями, пятнышки спереди, сзади и по бокам
    oct_z(a, "ermine", -1.28, 1.28, -0.7, 0.86, 0.36, 2.16, 2.42)
    oct_z(a, "ermine", -1.06, 1.06, -0.58, 0.74, 0.3, 2.4, 2.56)
    for x, z in ((-0.86, 2.27), (-0.42, 2.31), (0.42, 2.31), (0.86, 2.27)):
        a.box("spot", x - 0.04, x + 0.04, -0.72, -0.68, z - 0.07, z + 0.07, bevel=0)
        a.box("spot", x - 0.04, x + 0.04, 0.84, 0.88, z - 0.07, z + 0.07, bevel=0)
    for s in (1, -1):
        for y in (-0.16, 0.36):
            x0, x1 = sorted((s * 1.26, s * 1.3))
            a.box("spot", x0, x1, y - 0.04, y + 0.04, 2.22, 2.36, bevel=0)
    # золотая цепь V и медальон с клином сыра
    for s in (1, -1):
        pts = [(s * 0.62, -0.66, 2.22), (s * 0.44, -0.75, 2.0), (s * 0.26, -0.8, 1.84), (s * 0.1, -0.82, 1.78)]
        for i in range(len(pts) - 1):
            bar(a, "gold" if i % 2 == 0 else "rim", pts[i], pts[i + 1], 0.1, bevel=0)
    oct_y(a, "rim", -0.31, 0.31, 1.44, 2.02, 0.1, -0.86, -0.72)
    oct_y(a, "gold", -0.27, 0.27, 1.48, 1.98, 0.09, -0.89, -0.84)
    a.prism("cheese", [(-0.19, 1.56), (0.21, 1.56), (0.21, 1.9)], -0.93, -0.87, axis="y")
    for x, z in ((0.1, 1.63), (0.15, 1.76), (-0.04, 1.61)):
        a.box("hole", x - 0.03, x + 0.03, -0.95, -0.92, z - 0.03, z + 0.03, bevel=0)

    a.group = "Cape"  # плащ: три яруса шире книзу, складки, бока заходят вперёд, опушка, эмблема-корона
    cape_tier(a, 1.5, 2.3, 1.0, 0.56, 0.72, (0.0, 0.07, 0.1, 0.07, 0.0), 0.26, inner=(0.58, 0.2))
    cape_tier(a, 0.82, 1.52, 1.2, 0.58, 0.8, (0.1, 0.0, 0.1, 0.0, 0.1), 0.08, inner=(0.92, 0.56))
    cape_tier(a, 0.2, 0.84, 1.42, 0.6, 0.92, (0.12, 0.0, 0.12, 0.0, 0.12), -0.08, inner=(0.98, 0.34))
    a.box("ermine", -1.46, 1.46, 0.58, 1.1, 0.06, 0.26)  # опушка по низу — шлейф шире и дальше назад
    for s in (1, -1):
        x0, x1 = sorted((s * 1.23, s * 1.47))
        a.box("ermine", x0, x1, -0.14, 1.09, 0.07, 0.25)
    for x in (-1.2, -0.6, 0.0, 0.6, 1.2):
        a.box("spot", x - 0.045, x + 0.045, 1.09, 1.13, 0.09, 0.23, bevel=0)
    a.pixels(CROWN, {"#": ("gold", 0.03)}, 0.15, 0.525, 1.46, "xz", 0.9, sides=(1,), flip=True)

    a.group = "Pouch"  # кошель монет на левом бедре
    oct_z(a, "velvet", 0.84, 1.24, -0.46, 0.04, 0.12, 0.78, 1.2)
    a.box("velvet2", 0.92, 1.16, -0.38, -0.04, 1.18, 1.3)
    a.box("gold", 0.9, 1.18, -0.4, -0.02, 1.22, 1.27, bevel=0.008)  # шнурок
    for x, y, deg in ((0.97, -0.24, 14), (1.1, -0.16, -12)):
        a.prism("gold", S.octagon(x - 0.1, x + 0.1, 1.26, 1.46, 0.04), y - 0.025, y + 0.025, axis="y",
                matrix=tilt((x, y, 1.36), "Y", deg))
    oct_y(a, "rim", 0.95, 1.13, 0.9, 1.08, 0.05, -0.5, -0.44)  # монетка-бляха спереди
    bar(a, "gold", (0.96, -0.2, 1.28), (0.94, -0.3, 1.36), 0.04)

    a.group = "Tail1"  # длинный розовый хвост с кольцами: из-под плаща назад и вниз
    bar(a, "pink", (0.0, 0.5, 0.64), (0.0, 1.24, 0.28), 0.3)
    bar(a, "pink", (0.0, 1.16, 0.32), (0.0, 1.8, 0.2), 0.27)
    for p0, p1, w in (((0.0, 1.0, 0.405), (0.0, 1.05, 0.38), 0.32), ((0.0, 1.5, 0.255), (0.0, 1.55, 0.245), 0.29)):
        bar(a, "pinkdark", p0, p1, w, bevel=0)
    a.group = "Tail2"  # и вверх петлёй «S», золотой перстень
    bar(a, "pink", (0.0, 1.7, 0.22), (0.0, 2.18, 0.44), 0.24)
    bar(a, "pink", (0.0, 2.12, 0.38), (0.0, 2.34, 0.98), 0.21)
    bar(a, "pink", (0.0, 2.34, 0.9), (0.0, 2.25, 1.52), 0.18)
    bar(a, "pink", (0.0, 2.28, 1.45), (0.0, 2.0, 1.8), 0.15)
    bar(a, "pink", (0.0, 2.05, 1.79), (0.0, 1.84, 1.76), 0.12)
    bar(a, "pinkdark", (0.0, 1.98, 0.35), (0.0, 2.03, 0.375), 0.26, bevel=0)
    bar(a, "gold", (0.0, 2.21, 0.56), (0.0, 2.26, 0.7), 0.29)
    bar(a, "pinkdark", (0.0, 2.32, 1.15), (0.0, 2.315, 1.2), 0.2, bevel=0)
    bar(a, "pinkdark", (0.0, 2.2, 1.6), (0.0, 2.165, 1.64), 0.17, bevel=0)
    return a


# ── Руки, ноги, скипетр, корона ───────────────────────────────────────────────────────────────────────────────────────


def king_limbs():
    a = S.Art("Boss3_RatKingLimbs", ring_z0=1.1)
    colors(a)
    for side, s in (("L", 1), ("R", -1)):
        def sx(u, v):
            return sorted((s * u, s * v))

        a.group = "ArmUpper" + side
        a.box("fur", *sx(0.78, 1.18), -0.25, 0.25, 1.66, 2.34)
        a.group = "ArmLower" + side
        a.box("fur", *sx(0.82, 1.16), -0.22, 0.22, 1.3, 1.76)
        a.box("ermine", *sx(0.79, 1.19), -0.26, 0.26, 1.2, 1.36)  # горностаевый манжет
        a.box("spot", *sx(0.97, 1.03), -0.29, -0.255, 1.23, 1.33, bevel=0)
        a.box("pink", *sx(0.82, 1.16), -0.25, 0.2, 0.92, 1.22)  # лапа
        for i, x in enumerate((0.88, 0.99, 1.1)):  # пальцы спереди и коготки
            a.box("pink", *sx(x - 0.05, x + 0.05), -0.34, -0.2, 0.86 + 0.02 * (i == 1), 1.1, bevel=0)
            a.box("claw", *sx(x - 0.03, x + 0.03), -0.37, -0.32, 0.875, 0.935, bevel=0)
        a.box("pink", *sx(0.77, 0.86), -0.2, 0.0, 1.0, 1.18, bevel=0)  # большой палец внутрь

        a.group = "LegUpper" + side  # мощное бедро-окорочок
        oct_x(a, "fur", 0.2, 0.92, -0.46, 0.5, 0.2, *sx(0.5, 1.06))
        a.group = "LegLower" + side  # голень и длинная розовая ступня носком вперёд
        a.box("fur", *sx(0.52, 0.84), -0.14, 0.3, 0.1, 0.44)
        a.box("pink", *sx(0.44, 0.9), -0.86, 0.32, 0.0, 0.16)
        for x in (0.5, 0.67, 0.84):
            a.box("pink", *sx(x - 0.065, x + 0.065), -0.98, -0.78, 0.012, 0.14, bevel=0)
            a.box("claw", *sx(x - 0.03, x + 0.03), -1.02, -0.96, 0.02, 0.08, bevel=0)

    a.group = "Scepter"  # фонарь обходчика на золотом жезле, рукоять — в правой лапе
    x, y = -0.99, -0.02
    a.box("gold", x - 0.065, x + 0.065, y - 0.065, y + 0.065, 0.12, 2.44)
    a.box("velvet", x - 0.085, x + 0.085, y - 0.085, y + 0.085, 0.8, 1.34)  # обмотка рукояти
    for z in (0.62, 1.4):
        a.box("rim", x - 0.1, x + 0.1, y - 0.1, y + 0.1, z, z + 0.08)
    oct_z(a, "gold", x - 0.13, x + 0.13, y - 0.13, y + 0.13, 0.045, 0.01, 0.15)  # навершие
    a.box("ruby", x - 0.05, x + 0.05, y - 0.155, y - 0.12, 0.04, 0.12, bevel=0)
    oct_z(a, "rim", x - 0.25, x + 0.25, y - 0.25, y + 0.25, 0.06, 2.42, 2.52)  # основание фонаря
    a.box("lamp", x - 0.18, x + 0.18, y - 0.18, y + 0.18, 2.52, 3.02)  # стекло: тёплый свет
    for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):  # стойки рамки
        a.box("gold", x + dx * 0.18 - 0.04, x + dx * 0.18 + 0.04, y + dy * 0.18 - 0.04, y + dy * 0.18 + 0.04,
              2.5, 3.04)
    for k in (-1, 1):  # светящаяся середина и перекладина на каждой грани
        a.box("core", x - 0.09, x + 0.09, y + k * 0.18 - 0.01, y + k * 0.18 + 0.01, 2.6, 2.94, bevel=0)
        a.box("core", x + k * 0.18 - 0.01, x + k * 0.18 + 0.01, y - 0.09, y + 0.09, 2.6, 2.94, bevel=0)
        a.box("gold", x - 0.15, x + 0.15, y + k * 0.18 - 0.025, y + k * 0.18 + 0.025, 2.75, 2.79, bevel=0)
        a.box("gold", x + k * 0.18 - 0.025, x + k * 0.18 + 0.025, y - 0.15, y + 0.15, 2.75, 2.79, bevel=0)
    a.frustum("gold", (x - 0.25, x + 0.25, y - 0.25, y + 0.25), (x - 0.09, x + 0.09, y - 0.09, y + 0.09), 3.02, 3.22)
    a.box("gold", x - 0.09, x + 0.09, y - 0.09, y + 0.09, 3.21, 3.28)
    a.box("gold", x - 0.13, x - 0.08, y - 0.03, y + 0.03, 3.27, 3.46)  # ручка-дуга
    a.box("gold", x + 0.08, x + 0.13, y - 0.03, y + 0.03, 3.27, 3.46)
    a.box("gold", x - 0.13, x + 0.13, y - 0.03, y + 0.03, 3.44, 3.5)
    a.box("ruby", x - 0.07, x + 0.07, y - 0.07, y + 0.07, 3.5, 3.64)
    king_crown(a)
    return a


# ── Позы: часть → (поворот XYZ в градусах относительно родителя, сдвиг в единицах модели) ─────────────────────

Z3 = (0, 0, 0)


def mirror(r):
    return (r[0], -r[1], -r[2])


def arms(ul, ll, ur=None, lr=None):
    """Руки: (поворот плеча, поворот локтя) для L; R — зеркально, если не задано."""
    return {"ArmUpperL": (ul, Z3), "ArmLowerL": (ll, Z3), "ArmUpperR": (ur or mirror(ul), Z3),
            "ArmLowerR": (lr or mirror(ll), Z3)}


def legs(ul, ll, ur=None, lr=None):
    return {"LegUpperL": (ul, Z3), "LegLowerL": (ll, Z3), "LegUpperR": (ur or mirror(ul), Z3),
            "LegLowerR": (lr or mirror(ll), Z3)}


def lids(off):
    """Веки: (0, 0, 0) — закрыты; вверх под надбровье — прищур; назад внутрь головы — открыты."""
    return {"EyelidL": (Z3, off), "EyelidR": (Z3, off)}


CLOSED, SMUG, FOCUS, SLEEPY, OPEN = (0, 0, 0), (0, 0, 0.46), (0, 0, 0.52), (0, 0, 0.16), (0, 0.55, 0.3)


def rot(deg):
    return Euler([math.radians(d) for d in deg], "XYZ").to_matrix()


def held(pose, world):
    """Поворот скипетра относительно предплечья, чтобы в мире он был повёрнут на world (XYZ, градусы)."""
    chain = rot(pose.get("Torso", (Z3, Z3))[0]) @ rot(pose["ArmUpperR"][0]) @ rot(pose["ArmLowerR"][0])
    rel = (chain.inverted() @ rot(world)).to_euler("XYZ")
    out = dict(pose)
    out["Scepter"] = (tuple(math.degrees(v) for v in rel), Z3)
    return out


POSES = {}
# стойка: грудь колесом, подбородок вверх, левая лапа на брюхе, скипетр стоит в правой, хвост «S» сбоку
POSES["stand"] = held({
    "Torso": ((-3, 0, 0), Z3), "Head": ((-6, 0, 0), Z3), **lids(SMUG),
    **arms((-24, -8, 0), (-72, 0, -38), (-14, 10, 0), (-62, 0, 0)),
    "Tail1": ((-6, 0, -36), Z3), "Tail2": ((-12, 0, -20), Z3),
}, (0, -8, 0))
# сон: сидит, свернувшись, голова на груди, корона съехала, плащ укрывает, скипетр поперёк колен
POSES["sleep"] = held({
    "Torso": ((14, 0, 0), (0, -0.05, -0.36)), "Head": ((12, 0, -10), Z3), "Jaw": ((3, 0, 0), Z3), **lids(CLOSED),
    "EarL": ((0, 20, 0), Z3), "EarR": ((0, -20, 0), Z3), "Crown": ((8, -24, 0), (-0.16, -0.1, -0.14)),
    "Cape": ((-16, 0, 0), (0, 0.04, 0)), **arms((-36, -10, 0), (-80, 0, -30)),
    **legs((-84, -12, 0), (10, 0, 0)), "Tail1": ((0, 0, -80), Z3), "Tail2": ((24, 0, -50), Z3),
}, (0, 82, 0))
# боевая стойка: пригнулся, голова вверх на врага, оскал, когти вперёд, скипетр наготове, хвост поднят
POSES["combat"] = held({
    "Torso": ((14, 0, 0), (0, 0, -0.1)), "Head": ((-12, 0, 0), Z3), "Jaw": ((14, 0, 0), Z3), **lids(FOCUS),
    **arms((-58, -14, 0), (-40, 0, 0), (-64, 26, 0), (-74, 0, 0)),
    **legs((-32, -10, 0), (38, 0, 0)), "Tail1": ((-24, 0, -28), Z3), "Tail2": ((-30, 0, -12), Z3),
}, (-22, -40, 0))


def _pose(base, world=None, **parts):
    out = dict(POSES[base])
    out.pop("Scepter", None)
    out.update(parts)
    return held(out, world) if world else out


# проснулся: голова вверх, глаза круглые, уши торчком, корона подпрыгнула
POSES["alert"] = _pose("sleep", (0, 82, 0), Torso=((8, 0, 0), (0, -0.05, -0.36)), Head=((-14, 0, 0), Z3),
                       Jaw=((16, 0, 0), Z3), EarL=((0, -10, 0), Z3), EarR=((0, 10, 0), Z3),
                       Crown=((0, -12, 0), (-0.04, 0, 0.12)), **lids(OPEN))
POSES["combat2"] = _pose("combat", (-28, -36, 0), Torso=((17, 0, 0), (0, 0, -0.15)), Head=((-14, 0, 0), Z3),
                         **arms((-52, -14, 0), (-46, 0, 0), (-60, 26, 0), (-80, 0, 0)), Tail2=((-36, 0, -20), Z3))
# выпад «ЧАВК»: корпус вперёд, пасть настежь, резцы вперёд, уши прижаты, руки назад
POSES["chomp"] = _pose("combat", (-50, 0, 0), Torso=((34, 0, 0), (0, -0.34, -0.2)), Head=((8, 0, 0), Z3),
                       Jaw=((40, 0, 0), Z3), EarL=((-30, 0, 0), Z3), EarR=((-30, 0, 0), Z3), **lids(OPEN),
                       **arms((20, -30, 0), (-20, 0, 0), (10, 30, 0), (-30, 0, 0)),
                       **legs((-50, -10, 0), (40, 0, 0), (16, 10, 0), (16, 0, 0)),
                       Tail1=((-34, 0, -8), Z3), Tail2=((-36, 0, 0), Z3))
# замах скипетром над головой (для показа; в игре выпад идёт из стойки)
POSES["windup"] = _pose("combat", (-30, -40, 0), Torso=((-10, 0, 0), (0, 0.05, 0)), Head=((-18, 0, 0), Z3),
                        Jaw=((20, 0, 0), Z3), **lids(OPEN),
                        **arms((-60, -16, 0), (-40, 0, 0), (-160, 30, 0), (-24, 0, 0)))
# удар скипетром по земле
POSES["slam"] = _pose("combat", (110, 0, 0), Torso=((32, 0, 0), (0, -0.18, -0.24)), Head=((-8, 0, 0), Z3),
                      Jaw=((24, 0, 0), Z3), **lids(OPEN),
                      **arms((-50, -24, 0), (-30, 0, 0), (-84, 6, 0), (-8, 0, 0)), **legs((-46, -12, 0), (48, 0, 0)))
# получил удар: отшатнулся, зажмурился, уши прижаты, корона подскочила
POSES["hit"] = _pose("combat", (-24, -20, 0), Torso=((-12, 0, 0), (0, 0.22, -0.06)), Head=((-18, 0, 10), Z3),
                     Jaw=((14, 0, 0), Z3), **lids(CLOSED), EarL=((-40, 0, 0), Z3), EarR=((-40, 0, 0), Z3),
                     Crown=((0, 16, 0), (0.06, 0, 0.34)), **arms((-30, -50, 0), (-50, 0, 0)),
                     Tail2=((16, 0, -40), Z3))
# поражение: плюхнулся назад, лапы врозь, корона съехала на глаз
POSES["dizzy"] = _pose("sleep", (0, -70, 0), Torso=((-16, 8, 0), (0, 0.08, -0.38)), Head=((6, 0, 22), Z3),
                       Jaw=((18, 0, 0), Z3), **lids(SLEEPY), Crown=((22, 30, 0), (0.2, -0.22, -0.46)),
                       EarL=((0, 24, 0), Z3), EarR=((0, -24, 0), Z3), **arms((-12, -66, 0), (-24, 0, 0)),
                       **legs((-80, -28, 0), (10, 0, 0)), Tail1=((24, 0, -40), Z3), Tail2=((30, 0, 0), Z3))
# победный танец: скипетр высоко, хохочет, притопывает, хвост виляет
POSES["dance"] = _pose("stand", (-8, 0, 0), Torso=((-6, 0, 6), Z3), Head=((-16, 0, 6), Z3), Jaw=((30, 0, 0), Z3),
                       **lids((0, 0, 0.14)), **arms((-30, -20, 0), (-78, 0, -34), (-172, 8, 0), (-14, 0, 0)),
                       **legs((-48, -8, 0), (62, 0, 0), (0, 4, 0), (0, 0, 0)),
                       Tail1=((-14, 0, -52), Z3), Tail2=((-22, 0, -30), Z3))
POSES["dance2"] = _pose("stand", (-20, -30, 0), Torso=((-6, 0, -6), Z3), Head=((-12, 0, -6), Z3),
                        Jaw=((18, 0, 0), Z3), **lids((0, 0, 0.18)),
                        **arms((-30, -20, 0), (-78, 0, -34), (-150, 26, 0), (-36, 0, 0)),
                        **legs((0, -4, 0), (0, 0, 0), (-48, 8, 0), (62, 0, 0)),
                        Tail1=((-14, 0, -14), Z3), Tail2=((-22, 0, 10), Z3))
POSES["walkA"] = _pose("stand", (0, -6, 0), Torso=((4, 4, 0), (0, 0, 0.03)),
                       **arms((16, -10, 0), (-22, 0, 0), (-24, 10, 0), (-58, 0, 0)),
                       **legs((-26, 0, 0), (20, 0, 0), (18, 0, 0), (10, 0, 0)), Tail1=((-8, 0, -20), Z3))
POSES["walkB"] = _pose("stand", (0, -6, 0), Torso=((4, -4, 0), (0, 0, 0.03)),
                       **arms((-16, -10, 0), (-30, 0, 0), (-10, 10, 0), (-66, 0, 0)),
                       **legs((18, 0, 0), (10, 0, 0), (-26, 0, 0), (20, 0, 0)), Tail1=((-8, 0, -46), Z3))
# засыпание (для показа): зевает во всю пасть, потягивается
POSES["yawn"] = _pose("stand", (-10, 0, 0), Torso=((-8, 0, 0), Z3), Head=((-24, 0, 0), Z3), Jaw=((46, 0, 0), Z3),
                      **lids(CLOSED), **arms((-160, -20, 0), (-20, 0, 0), (-150, 24, 0), (-40, 0, 0)))


def pose_matrices(pose):
    """Мировые матрицы частей в позе (в стадах)."""
    out = {}

    def world(name):
        if name in out:
            return out[name]
        parent, pivot = RIG[name]
        r, off = pose.get(name, (Z3, Z3))
        m3 = Euler([math.radians(d) for d in r], "XYZ").to_matrix().to_4x4()
        local = Vector(pivot) - (Vector(RIG[parent][1]) if parent else Vector())
        m = Matrix.Translation((local + Vector(off)) * SCALE) @ m3
        out[name] = (world(parent) @ m) if parent else m
        return out[name]

    for name in RIG:
        world(name)
    return out


def apply_pose(parts, pose, place=Matrix.Identity(4)):
    mats = pose_matrices(POSES[pose])
    low = min((mats[n] @ OBJ_SCALE @ v.co).z for n, o in parts.items() for v in o.data.vertices)
    ground = Matrix.Translation((0, 0, -low))
    for n, o in parts.items():
        o.matrix_world = place @ ground @ mats[n] @ OBJ_SCALE
    return {n: ground @ mats[n] for n in parts}


# ── Сборка ───────────────────────────────────────────────────────────────────────────────────────────────────

if MODE == "where":  # отладка поз: где кисть со скипетром, фонарь и макушка (стады, до подъёма к земле)
    for name, pose in POSES.items():
        mats = pose_matrices(pose)
        lamp = mats["Scepter"] @ (Vector((0, 0, 2.3)) * SCALE)
        hand = mats["Scepter"] @ Vector()
        top = mats["Crown"] @ Vector()
        print("WHERE %-8s hand %s lamp %s crown %s" % (name, tuple(round(c, 1) for c in hand),
                                                       tuple(round(c, 1) for c in lamp), tuple(round(c, 1) for c in top)))
    sys.exit(0)

bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new("Boss3")
bpy.context.scene.collection.children.link(collection)

arts = [king_head(), king_body(), king_limbs()]
report = {"scale": SCALE}
if MODE == "check":
    total = 0
    for art in arts:
        art.build(collection)
        total += art.stats["tris"]
        print("CHECK", art.name, json.dumps(art.stats, ensure_ascii=False))
    print("CHECK_TOTAL", total)
    sys.exit(0)

AX = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))  # оси Roblox: (x, y, z) Blender → (x, z, −y) Roblox
# Цвет заготовки части до импорта мешей: шерсть, корона, плащ, кошель, хвост, ступни, скипетр.
PART_COLOR = {"Jaw": "A9AEC2", "Crown": "F2C230", "Cape": "D8352A", "Pouch": "6B3FB8", "Tail1": "F49AB0",
              "Tail2": "F49AB0", "Scepter": "F2C230", "LegLowerL": "F49AB0", "LegLowerR": "F49AB0"}
# Позы в модуле игры называются, как у пса (Shared/BossAnim): выпады bite и swipe, победа bark и bark2.
EXPORT = {"sleep": "sleep", "alert": "alert", "stand": "stand", "combat": "combat", "combat2": "combat2",
          "walkA": "walkA", "walkB": "walkB", "hit": "hit", "dizzy": "dizzy", "bite": "chomp", "swipe": "slam",
          "bark": "dance", "bark2": "dance2"}


def explode(obj, art, sign):
    """Разнести части по x на 10 шагов квадратов D39 (рисунок не сдвигается), чтобы окклюзия была только своя."""
    order = {g: i for i, g in enumerate(dict.fromkeys(art.face_groups))}
    me = obj.data
    done = set()
    for poly in me.polygons:
        dx = order[art.face_groups[poly.index]] * 10 * S.RING["step"] * sign
        for v in poly.vertices:
            if v not in done:
                me.vertices[v].co.x += dx
                done.add(v)


def split_keep(obj, art):
    """Как S.split_groups, но со всеми материалами сборки (быстрый просмотр без запекания)."""
    out = {}
    me = obj.data
    for group in dict.fromkeys(art.face_groups):
        pivot = Vector(RIG[group][1])
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if art.face_groups[f.index] != group], context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        bmesh.ops.translate(bm, vec=-pivot, verts=bm.verts)
        part = bpy.data.meshes.new(f"{obj.name}_{group}")
        bm.to_mesh(part)
        bm.free()
        for m in me.materials:
            part.materials.append(m)
        o = bpy.data.objects.new(f"{obj.name}_{group}", part)
        o.location = pivot
        collection.objects.link(o)
        out[group] = o
    bpy.data.objects.remove(obj)
    return out


def part_objects(bake):
    """Части модели. bake — с запеканием карт и масштабом игры в меше; иначе материалы сборки (быстрый просмотр)."""
    parts = {}
    for art in arts:
        obj = art.build(collection)
        if bake:
            explode(obj, art, 1)
            uv = S.bake(obj, art, TEXDIR, art.name)
            explode(obj, art, -1)
            report[art.name] = {**art.stats, "uv_fill": round(uv["uv_fill"], 3),
                                "texels_per_stud": round(uv["texels_per_stud"] / SCALE, 1)}
            groups = dict.fromkeys(art.face_groups)
            split = S.split_groups(obj, art, {g: RIG[g][1] for g in groups}, collection)
        else:
            report[art.name] = art.stats
            split = split_keep(obj, art)
        for g, o in split.items():
            if MODE != "quick":
                o.data.transform(Matrix.Scale(SCALE, 4))
                o.location = Vector(RIG[g][1]) * SCALE
            o.data.calc_loop_triangles()
            report.setdefault("tris", {})[g] = len(o.data.loop_triangles)
            parts[g] = o
    report["tris_total"] = sum(report["tris"].values())
    return parts


def write_rig_module(path, parts):
    """Скелет для игры: части, точки вращения, габариты, позы — модуль Luau."""
    def v3(v):
        return "Vector3.new(%s)" % ", ".join("%.4f" % c for c in v)

    lines = ["-- Скелет босса 3 «Крысиный король» для Motor6D (D18, D54): части, точки вращения, габариты и ключевые позы.",
             "-- Сгенерировано scripts/blender/boss3_ratking.py (режим rig) — руками не править. Оси Roblox, стады; лицо",
             "-- смотрит в +Z модели. pivot — точка вращения части в покое (низ ступней на y = 0), center и size — габариты",
             "-- меша относительно точки вращения. Позы: часть → {x, y, z, r00…r22} — Transform сустава относительно покоя",
             "-- (у Torso — вместе с подъёмом к земле). Имена поз — как у пса (Shared/BossAnim): bite — выпад «чавк»,",
             "-- swipe — удар скипетром по земле, bark и bark2 — победный танец. Ни от чего не зависит.", "", "return {",
             "\tScale = %s," % SCALE, "\tOrder = { %s }," % ", ".join('"%s"' % n for n in RIG), "\tParts = {"]
    for n, (parent, pivot) in RIG.items():
        co = [AX @ v.co for v in parts[n].data.vertices]
        lo = Vector([min(c[i] for c in co) for i in range(3)])
        hi = Vector([max(c[i] for c in co) for i in range(3)])
        lines.append('\t\t%s = { parent = %s, pivot = %s, center = %s, size = %s, map = "%s", color = "%s" },' % (
            n, '"%s"' % parent if parent else "nil", v3(AX @ (Vector(pivot) * SCALE)), v3((lo + hi) / 2),
            v3(hi - lo), MAP_OF[n], PART_COLOR.get(n, "8A8FA3")))
    lines += ["\t},", "\tPoses = {"]
    for name, source in EXPORT.items():
        pose = POSES[source]
        mats = pose_matrices(pose)
        low = min((mats[n] @ v.co).z for n, o in parts.items() for v in o.data.vertices)
        high = max((mats[n] @ v.co).z for n, o in parts.items() for v in o.data.vertices)
        print("RIG_HEIGHT %-6s %.1f" % (name, high - low))
        lines.append("\t\t%s = {" % name)
        for n in RIG:
            r, off = pose.get(n, (Z3, Z3))
            m3 = AX @ Euler([math.radians(d) for d in r], "XYZ").to_matrix() @ AX.transposed()
            t = AX @ (Vector(off) * SCALE)
            if n == "Torso":
                t.y -= low
            nums = [t.x, t.y, t.z] + [m3[i][j] for i in range(3) for j in range(3)]
            lines.append("\t\t\t%s = { %s }," % (n, ", ".join("%.4f" % x for x in nums)))
        lines.append("\t\t},")
    lines += ["\t},", "}", ""]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print("RIG_OK", path, len(EXPORT), "поз")


parts = part_objects(bake=(MODE == ""))
if MODE == "rig":
    write_rig_module(os.path.join(REPO, "src", "shared", "Config", "Boss3RatKingRig.luau"), parts)
    sys.exit(0)

if MODE == "":
    S.export_fbx([parts[n] for n in RIG], os.path.join(REPO, "assets", "models", "Boss3_RatKing.fbx"))
    TO_RBX = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
    rig = {"parents": {n: RIG[n][0] for n in RIG}, "maps": MAP_OF, "poses": {}}
    for n, o in parts.items():
        S.studio_json(o, os.path.join(PREVIEWS, f"RatKing_{n}.json"))
    for pose in POSES:
        mats = apply_pose(parts, pose)
        rig["poses"][pose] = {}
        for n, m in mats.items():
            r = TO_RBX @ m @ TO_RBX.inverted()
            rig["poses"][pose][n] = [round(r[0][3], 4), round(r[1][3], 4), round(r[2][3], 4)] + [
                round(r[i][j], 5) for i in range(3) for j in range(3)]
    with open(os.path.join(PREVIEWS, "rig.json"), "w", encoding="utf-8") as f:
        json.dump(rig, f)

# ── Проверочные рендеры ──────────────────────────────────────────────────────────────────────────────────────

prev = S.Preview(collection)
floor = bpy.data.objects["Floor"]
floor.scale = (1, 2.8, 2.8)
floor.location.y = 9
for i, (light, loc) in enumerate(prev.lights):
    light.data.energy *= 9
    light.data.size *= 3.0
    prev.lights[i] = (light, loc * 3.1)
prev.aim_lights(Vector((0, 0, 0)))


def turn(deg):
    return Matrix.Rotation(math.radians(deg), 4, "Z")


EYE, LOOK = (0, -40, 10.5), 7.4
FAST = MODE == "quick"
TILE = (600, 700) if FAST else (800, 900)
SHOTS = os.environ.get("RATKING_SHOTS", "all")

if SHOTS in ("all", "turns"):
    for pose in ("stand",) if FAST else ("stand", "combat"):
        tiles = []
        for label, deg in (("front", 0), ("34", -40), ("side", -90), ("back", 180), ("34back", 140)):
            apply_pose(parts, pose, turn(deg))
            tiles.append(prev.shot(os.path.join(PREVIEWS, f"king_{pose}_{label}.png"), EYE, (0, 0, LOOK), 50, TILE))
        S.strip(tiles, os.path.join(PREVIEWS, f"king_turns_{pose}.png"))
if SHOTS in ("all", "poses"):
    tiles = []
    for pose in ("sleep", "alert", "combat", "chomp", "slam", "hit", "dizzy", "dance", "walkA", "yawn"):
        apply_pose(parts, pose, turn(-35))
        tiles.append(prev.shot(os.path.join(PREVIEWS, f"king_pose_{pose}.png"), EYE, (0, 0, 6.6), 50, (560, 760)))
    S.strip(tiles[:5], os.path.join(PREVIEWS, "king_poses_1.png"))
    S.strip(tiles[5:], os.path.join(PREVIEWS, "king_poses_2.png"))
if SHOTS in ("all", "hero"):
    apply_pose(parts, "stand", turn(-28))
    prev.shot(os.path.join(PREVIEWS, "king_34_stand.png"), EYE, (0, 0, LOOK), 50, (1100, 1200))
    apply_pose(parts, "stand", turn(-18))
    prev.shot(os.path.join(PREVIEWS, "king_head_close.png"), (-4.6, -20.0, 12.0), (-0.4, -1.8, 10.4), 50, (1100, 1100))
if not FAST and SHOTS == "all":
    tiles = []
    for label, deg in (("34", -40), ("side", -90), ("front", 0)):
        apply_pose(parts, "sleep", turn(deg))
        tiles.append(prev.shot(os.path.join(PREVIEWS, f"king_sleep_{label}.png"), EYE, (0, 0, 4.4), 50, (800, 900)))
    S.strip(tiles, os.path.join(PREVIEWS, "king_turns_sleep.png"))
    apply_pose(parts, "combat", turn(-30))
    prev.shot(os.path.join(PREVIEWS, "king_34_combat.png"), EYE, (0, 0, LOOK), 50, (1100, 1200))
    # Масштаб: в стойке и спящий рядом с манекеном Roblox (5.2 стада).
    apply_pose(parts, "stand", Matrix.Translation((-10.0, 0, 0)) @ turn(-25))
    sleeper = {n: o.copy() for n, o in parts.items()}
    for o in sleeper.values():
        collection.objects.link(o)
    apply_pose(sleeper, "sleep", Matrix.Translation((10.5, 0, 0)) @ turn(-35))
    S.mannequin(collection, 0.0, y=-1.5)
    prev.aim_lights(Vector((0, 0, 0)))
    prev.shot(os.path.join(PREVIEWS, "king_scale.png"), (0, -62, 11.0), (0, 0, 6.0), 50, (1800, 900))

with open(os.path.join(PREVIEWS, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("KING_OK " + json.dumps(report, ensure_ascii=False))
