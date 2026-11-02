"""Босс 2 «Торговец-громила» (D42), стиль D39: подвижная модель из частей для процедурных анимаций (D18), как пёс.

Крупный харизматичный барыга с Барахолки: бочкообразная грудь и живот, огромные кулаки с золотыми перстнями,
фиолетовый жилет с карманами и ценниками, бирюзовая рубашка, золотая цепь с медальоном «$», красная кепка со знаком
«$», тёмные очки-авиаторы, густые усы, ухмылка с золотым зубом, небритый подбородок, мешок добычи за спиной (из него
торчат золотой подсвечник и кубок). Опасный, но смешной — не страшный. Крупнее пса: в стойке ≈ 13.8 стада.

Части (Motor6D): Torso (корень) → Head → Jaw; Torso → Sack; руки и ноги из двух частей (ArmUpper → ArmLower,
LegUpper → LegLower), L — левый бок босса (+x). Собрано в масштабе предметов (квадраты D39 того же вида), затем
увеличено в SCALE раз. Три карты 1024² (голова, туловище с мешком, руки и ноги); окклюзия запекается с разнесёнными
частями, чтобы в любой позе не было чужих теней.

Пишет assets/models/Boss2_Trader.fbx (части Boss2_Trader<Карта>_<Часть>, начало координат — точка вращения),
assets/textures/art/Boss2_Trader{Head,Body,Limbs}_{color,normal}.png, а в папку превью — ракурсы, позы, кадр с
манекеном, Trader_<часть>.json и rig.json (точки вращения и позы в осях Roblox) для Studio. Режим rig пишет модуль
скелета для игры (src/shared/Config/Boss2TraderRig.luau) — при интеграции.
Запуск: blender --background --factory-startup --python scripts/blender/boss2_trader.py -- <репо> <превью> [check|rig]
"""

import json
import math
import os
import sys

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

# Часть → (родитель, точка вращения в координатах модели).
RIG = {
    "Torso": (None, (0.0, 0.0, 1.62)),
    "Head": ("Torso", (0.0, -0.05, 3.42)),
    "Jaw": ("Head", (0.0, 0.05, 3.62)),
    "Sack": ("Torso", (0.0, 0.62, 3.3)),
}
for side, s in (("L", 1), ("R", -1)):
    RIG["ArmUpper" + side] = ("Torso", (s * 1.2, 0.0, 3.18))
    RIG["ArmLower" + side] = ("ArmUpper" + side, (s * 1.24, 0.0, 2.36))
    RIG["LegUpper" + side] = ("Torso", (s * 0.42, 0.0, 1.55))
    RIG["LegLower" + side] = ("LegUpper" + side, (s * 0.42, 0.0, 0.9))
MAPS = {"Head": ("Head", "Jaw"), "Body": ("Torso", "Sack"),
        "Limbs": tuple(p + side for p in ("ArmUpper", "ArmLower", "LegUpper", "LegLower") for side in ("L", "R"))}
MAP_OF = {part: m for m, parts in MAPS.items() for part in parts}


def colors(a):
    a.paint("skin", "F0B088", rings=True)
    a.paint("stubble", "D49572", rings=True)  # небритый подбородок
    a.paint("shirt", "2CB5A8", rings=True)  # бирюзовая рубашка
    a.paint("vest", "6B3FB8", rings=True)  # фиолетовый жилет
    a.paint("pants", "3C5BA8", rings=True)
    a.paint("cap", "D8352A", rings=True)
    a.paint("sack", "C9A06A", rings=True)  # мешковина
    for key, code in (("pocket", "55309A"), ("belt", "4A2C1C"), ("boot", "5A3A22"), ("sole", "2A1E16"),
                      ("gold", "F2C230"), ("rim", "B87A12"), ("dark", "15161C"), ("glint", "FFFFFF"),
                      ("tooth", "FFFFFF"), ("mouth", "8E2433"), ("tongue", "F07A8C"), ("stache", "4A2A18"),
                      ("brow", "3A2214"), ("nose", "E68E6E"), ("cap2", "A82820"), ("rope", "8A6238"),
                      ("patch", "8A5A3A"), ("tag", "FFF6E0"), ("red", "E53935"), ("money", "2E9E4F"),
                      ("button", "F2E2C4"), ("ink", "1F3E9A"), ("candle", "F6F0E1"), ("flame", "FF9A1F")):
        a.paint(key, code)


def tilt(c, axis, deg):
    """Поворот детали вокруг точки c."""
    c = Vector(c)
    return Matrix.Translation(c) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-c)


def bar(a, key, p0, p1, w, h=None):
    """Брусок от точки p0 до p1 с сечением w × h (звенья цепи, ремешки)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    up = "Y" if abs(d.normalized().z) > 0.95 else "Z"
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("X", up).to_matrix().to_4x4()
    h = h or w
    a.box(key, -d.length / 2, d.length / 2, -w / 2, w / 2, -h / 2, h / 2, matrix=m)


DOLLAR = [".#.",
          "###",
          "#..",
          "###",
          "..#",
          "###",
          ".#."]
ANCHOR = [".#.",
          "###",
          ".#.",
          ".#.",
          "#.#",
          ".#."]


# ── Голова: череп, нос, очки-авиаторы, брови, усы, ухмылка с золотым зубом, уши, кепка; подбородок ─────────────


def trader_head():
    a = S.Art("Boss2_TraderHead", ring_z0=3.9)
    colors(a)
    a.group = "Head"
    a.box("skin", -0.5, 0.5, -0.56, 0.36, 3.62, 4.22)  # голова — широкий короб
    a.box("skin", -0.44, 0.44, -0.5, 0.3, 3.4, 3.64)  # шея короткая и толстая
    a.box("mouth", -0.3, 0.3, -0.52, -0.2, 3.5, 3.63, bevel=0)  # рот изнутри — виден, когда челюсть опущена
    a.box("tooth", -0.3, 0.3, -0.585, -0.5, 3.56, 3.7, bevel=0)  # ухмылка: верхние зубы
    a.box("gold", 0.07, 0.17, -0.6, -0.57, 3.57, 3.69, bevel=0)  # золотой зуб
    a.box("skin", -0.44, 0.44, -0.6, -0.46, 3.69, 3.8)  # верхняя губа
    # усы: широкая щётка и опущенные концы
    a.box("stache", -0.42, 0.42, -0.66, -0.52, 3.72, 3.86)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.3, s * 0.53))
        a.box("stache", x0, x1, -0.64, -0.5, 3.56, 3.76)
    a.box("nose", -0.13, 0.13, -0.72, -0.5, 3.8, 3.99)  # картошкой
    # очки-авиаторы: золотая оправа, тёмные стёкла с бликом, перемычка
    for s in (1, -1):
        x0, x1 = sorted((s * 0.04, s * 0.47))
        a.box("rim", x0, x1, -0.6, -0.55, 3.87, 4.11, bevel=0)
        x0, x1 = sorted((s * 0.07, s * 0.44))
        a.box("dark", x0, x1, -0.625, -0.58, 3.9, 4.08, bevel=0)
        g0 = 0.3 if s > 0 else -0.2
        a.box("glint", g0, g0 + 0.08, -0.64, -0.6, 4.0, 4.06, bevel=0)
        x0, x1 = sorted((s * 0.47, s * 0.52))
        a.box("rim", x0, x1, -0.5, 0.06, 4.02, 4.07, bevel=0)  # дужки
        # нахмуренная бровь над очками
        b0, b1 = sorted((s * 0.06, s * 0.46))
        a.box("brow", b0, b1, -0.63, -0.55, 4.08, 4.14, bevel=0, matrix=tilt((s * 0.26, -0.59, 4.11), "Y", -s * 12))
        # ухо
        x0, x1 = sorted((s * 0.49, s * 0.6))
        a.box("skin", x0, x1, -0.22, 0.1, 3.76, 4.06)
    # кепка: тулья, верх, козырёк, околыш, нашивка «$», ценник сбоку
    a.box("cap", -0.55, 0.55, -0.6, 0.42, 4.14, 4.5)
    a.box("cap", -0.46, 0.46, -0.52, 0.34, 4.49, 4.6)
    a.box("cap2", -0.47, 0.47, -1.02, -0.5, 4.14, 4.23)
    a.box("cap2", -0.56, 0.56, -0.61, 0.43, 4.12, 4.2)  # околыш
    a.box("gold", -0.06, 0.06, -0.12, 0.0, 4.59, 4.65)  # пуговка
    a.prism("gold", S.octagon(-0.17, 0.17, 4.2, 4.46, 0.06), -0.64, -0.59, axis="y")
    a.pixels(DOLLAR, {"#": ("money", 0.02)}, 0.032, -0.048, 4.445, "xz", 0.64)
    a.box("tag", 0.58, 0.62, -0.05, 0.2, 4.0, 4.24, matrix=tilt((0.58, 0.07, 4.12), "X", 12))
    a.box("red", 0.575, 0.625, 0.0, 0.15, 4.12, 4.17, bevel=0, matrix=tilt((0.58, 0.07, 4.12), "X", 12))

    a.group = "Jaw"  # тяжёлый небритый подбородок чуть впереди — упрямый прикус
    a.box("stubble", -0.47, 0.47, -0.64, 0.18, 3.24, 3.57)
    a.box("stubble", -0.36, 0.36, -0.68, -0.2, 3.2, 3.42)  # подбородок-кирпич
    a.box("tongue", -0.2, 0.2, -0.48, -0.24, 3.56, 3.59, bevel=0)
    a.box("tooth", -0.26, 0.26, -0.59, -0.52, 3.52, 3.58, bevel=0)  # нижние зубы
    return a


# ── Туловище: таз, живот, грудь, жилет с карманами, цепь с медальоном, ремень с пряжкой; мешок добычи ─────────


def trader_body():
    a = S.Art("Boss2_TraderBody", ring_z0=2.85)
    colors(a)
    a.group = "Torso"
    a.box("pants", -0.72, 0.72, -0.42, 0.42, 1.38, 1.86)  # таз
    a.box("belt", -0.76, 0.76, -0.5, 0.46, 1.62, 1.84)
    a.box("shirt", -0.8, 0.8, -0.7, 0.5, 1.76, 2.42)  # живот выпирает над ремнём
    a.box("shirt", -0.94, 0.94, -0.56, 0.56, 2.36, 3.3)  # грудь-бочка
    a.box("shirt", -1.02, 1.02, -0.42, 0.46, 2.98, 3.42)  # плечи
    # пряжка «$»
    a.prism("gold", S.octagon(-0.22, 0.22, 1.6, 1.86, 0.05), -0.56, -0.48, axis="y")
    a.pixels(DOLLAR, {"#": ("money", 0.02)}, 0.032, -0.048, 1.842, "xz", 0.56)
    # пуговицы рубашки по животу
    for z in (1.92, 2.18):
        a.box("button", -0.06, 0.06, -0.73, -0.69, z - 0.05, z + 0.05, bevel=0)
    # жилет: спинка и две полы, между полами — рубашка
    a.box("vest", -0.99, 0.99, 0.0, 0.6, 2.32, 3.36)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.24, s * 0.99))
        a.box("vest", x0, x1, -0.62, 0.0, 2.32, 3.36)
        # карман с клапаном и ценник на верёвочке
        x0, x1 = sorted((s * 0.46, s * 0.84))
        a.box("pocket", x0, x1, -0.67, -0.6, 2.44, 2.76)
        a.box("pocket", x0 - 0.02, x1 + 0.02, -0.69, -0.6, 2.72, 2.8)
        a.box("gold", s * 0.65 - 0.04, s * 0.65 + 0.04, -0.71, -0.68, 2.73, 2.79, bevel=0)  # кнопка
    a.box("rope", 0.62, 0.65, -0.72, -0.69, 2.44, 2.6, bevel=0)
    a.box("tag", 0.54, 0.76, -0.74, -0.7, 2.18, 2.46, matrix=tilt((0.65, -0.72, 2.32), "Y", 10))
    a.box("red", 0.58, 0.72, -0.755, -0.735, 2.3, 2.38, bevel=0, matrix=tilt((0.65, -0.72, 2.32), "Y", 10))
    # толстая золотая цепь на шее (V) и медальон «$»
    for s in (1, -1):
        pts = [(s * 0.5, -0.5, 3.4), (s * 0.4, -0.62, 3.2), (s * 0.26, -0.66, 2.98), (s * 0.1, -0.68, 2.82)]
        for i in range(len(pts) - 1):
            bar(a, "gold" if i % 2 == 0 else "rim", pts[i], pts[i + 1], 0.1)
    a.prism("rim", S.octagon(-0.26, 0.26, 2.42, 2.94, 0.09), -0.75, -0.67, axis="y")
    a.prism("gold", S.octagon(-0.22, 0.22, 2.46, 2.9, 0.08), -0.78, -0.74, axis="y")
    a.pixels(DOLLAR, {"#": ("money", 0.02)}, 0.05, -0.075, 2.855, "xz", 0.78)

    a.group = "Sack"  # мешок за спиной: перевязан верёвкой, заплатка, большой «$», из горловины торчит добыча
    a.box("sack", -0.74, 0.74, 0.58, 1.36, 1.7, 3.2)
    a.box("sack", -0.56, 0.56, 0.66, 1.28, 3.18, 3.6)
    a.box("rope", -0.38, 0.38, 0.74, 1.2, 3.58, 3.72)
    a.box("sack", -0.46, 0.46, 0.7, 1.24, 3.7, 3.92)
    a.box("patch", -0.6, -0.18, 1.34, 1.4, 1.86, 2.28, bevel=0)
    for x in (-0.54, -0.24):
        a.box("rope", x - 0.015, x + 0.015, 1.395, 1.415, 1.9, 2.24, bevel=0)  # стежки
    a.pixels(DOLLAR, {"#": ("gold", 0.03)}, 0.11, 0.165, 3.0, "xz", 1.36, sides=(1,), flip=True)
    a.box("gold", 0.2, 0.3, 0.9, 1.0, 3.8, 4.6)  # золотой подсвечник
    a.box("gold", 0.1, 0.4, 0.85, 1.05, 4.56, 4.64)
    a.box("candle", 0.2, 0.3, 0.9, 1.0, 4.62, 4.86)
    a.box("flame", 0.22, 0.28, 0.92, 0.98, 4.85, 4.96, bevel=0)
    a.box("gold", -0.5, -0.4, 0.9, 1.0, 3.8, 4.42)  # золотой кубок: ножка, чаша, ручки
    a.box("gold", -0.62, -0.28, 0.84, 1.06, 4.3, 4.36)
    a.box("gold", -0.68, -0.22, 0.8, 1.1, 4.34, 4.7)
    a.box("rim", -0.64, -0.26, 0.84, 1.06, 4.68, 4.72, bevel=0)
    for x0, x1 in ((-0.78, -0.68), (-0.22, -0.12)):
        a.box("gold", x0, x1, 0.9, 1.0, 4.42, 4.64)
    return a


# ── Руки и ноги: рукава, бицепс с татуировкой, предплечья, часы, огромные кулаки с перстнями; штаны, ботинки ────


def trader_limbs():
    a = S.Art("Boss2_TraderLimbs", ring_z0=2.0)
    colors(a)
    for side, s in (("L", 1), ("R", -1)):
        def sx(u, v):
            return sorted((s * u, s * v))

        a.group = "ArmUpper" + side
        a.box("shirt", *sx(1.0, 1.54), -0.38, 0.38, 2.86, 3.46)  # короткий рукав
        a.box("skin", *sx(1.02, 1.46), -0.32, 0.32, 2.26, 2.9)  # бицепс
        if s > 0:  # татуировка-якорь на левом плече
            a.pixels(ANCHOR, {"#": ("ink", 0.02)}, 0.05, -0.075, 2.78, "yz", 1.46, sides=(1,))
        a.group = "ArmLower" + side
        a.box("skin", *sx(0.98, 1.5), -0.36, 0.36, 1.64, 2.32)  # мощное предплечье
        a.box("gold", *sx(0.96, 1.52), -0.38, 0.38, 1.58, 1.7)  # часы-браслет
        a.box("skin", *sx(0.92, 1.56), -0.44, 0.42, 0.98, 1.62)  # кулак
        a.box("skin", *sx(0.9, 1.04), -0.5, -0.12, 1.18, 1.5)  # большой палец сбоку-внутри
        for z in (1.12, 1.27, 1.42):  # складки пальцев на лицевой стороне кулака
            a.box("stubble", *sx(0.98, 1.5), -0.455, -0.435, z - 0.015, z + 0.015, bevel=0)
        for x in (1.1, 1.36):  # золотые перстни
            a.box("gold", *sx(x - 0.07, x + 0.07), -0.47, -0.42, 1.36, 1.48, bevel=0)
        a.box("money", *sx(1.31, 1.41), -0.48, -0.465, 1.39, 1.45, bevel=0)  # камень в перстне

        a.group = "LegUpper" + side
        a.box("pants", *sx(0.16, 0.7), -0.34, 0.34, 0.86, 1.6)
        a.group = "LegLower" + side
        a.box("pants", *sx(0.18, 0.68), -0.32, 0.32, 0.4, 0.92)
        a.box("pants", *sx(0.15, 0.71), -0.35, 0.33, 0.32, 0.5)  # подвёрнутая штанина
        a.box("boot", *sx(0.14, 0.72), -0.62, 0.34, 0.06, 0.36)  # тяжёлый ботинок носком вперёд
        a.box("sole", *sx(0.12, 0.74), -0.64, 0.36, 0.0, 0.1)
        a.box("boot", *sx(0.2, 0.66), -0.7, -0.4, 0.08, 0.3)  # круглый нос
    return a


# ── Позы: часть → (поворот XYZ в градусах относительно родителя, сдвиг в единицах модели) ─────────────────────

Z3 = (0, 0, 0)


def arms(ul, ll, ur=None, lr=None):
    """Руки: (поворот плеча, поворот локтя) для L; R — зеркально (знаки Y и Z меняются), если не задано."""
    def mirror(r):
        return (r[0], -r[1], -r[2])
    ur = ur or mirror(ul)
    lr = lr or mirror(ll)
    return {"ArmUpperL": (ul, Z3), "ArmLowerL": (ll, Z3), "ArmUpperR": (ur, Z3), "ArmLowerR": (lr, Z3)}


def legs(ul, ll, ur=None, lr=None):
    def mirror(r):
        return (r[0], -r[1], -r[2])
    ur = ur or mirror(ul)
    lr = lr or mirror(ll)
    return {"LegUpperL": (ul, Z3), "LegLowerL": (ll, Z3), "LegUpperR": (ur, Z3), "LegLowerR": (lr, Z3)}


POSES = {
    "stand": {**arms((0, -6, 0), (-8, 0, 0))},
    "sleep": {  # сидит на земле, привалившись к мешку, ноги вытянуты, кепка на глаза, кулаки на животе
        "Torso": ((-12, 0, 0), (0, 0.1, -1.2)),
        "Head": ((38, 0, 0), (0, 0, 0)),
        "Jaw": ((6, 0, 0), Z3),
        "Sack": ((-6, 0, 0), (0, 0.04, -0.06)),
        **arms((-8, -6, 0), (-88, 0, -55)),
        **legs((-80, -12, 0), (6, 0, 0)),
    },
    "combat": {  # боксёрская стойка: кулаки у подбородка, ноги шире, корпус вперёд
        "Torso": ((8, 0, 0), (0, 0, -0.1)),
        "Head": ((-6, 0, 0), Z3),
        **arms((-62, -14, 0), (-78, 10, 0)),
        **legs((-14, -10, 0), (20, 0, 0)),
    },
}


def _pose(base, **parts):
    out = dict(POSES[base])
    out.update(parts)
    return out


# Ключевые позы будущих анимаций (D18): между ними клиент плавно переходит.
POSES["alert"] = _pose("sleep", Head=((-8, 0, 0), Z3), Jaw=((18, 0, 0), Z3))  # проснулся: голова вверх, рот открыт
POSES["combat2"] = _pose("combat", Torso=((10, 0, 0), (0, 0, -0.14)), **arms((-58, -14, 0), (-84, 10, 0)))
POSES["punch"] = _pose("combat", Torso=((10, 0, -16), (0, -0.08, -0.1)), Jaw=((10, 0, 0), Z3),
                       **arms((-62, -14, 0), (-78, 10, 0), (-88, 0, 0), (0, 0, 0)))  # прямой правой
POSES["slam"] = _pose("combat", Torso=((-8, 0, 0), (0, 0, 0.02)), Head=((-14, 0, 0), Z3), Jaw=((22, 0, 0), Z3),
                      **arms((-168, -12, 0), (-24, 0, 0)))  # кулаки над головой
POSES["slam2"] = _pose("combat", Torso=((26, 0, 0), (0, -0.1, -0.22)), Head=((-10, 0, 0), Z3), Jaw=((16, 0, 0), Z3),
                       **arms((-40, -6, 0), (-6, 0, 0)), **legs((-24, -12, 0), (36, 0, 0)))  # удар по земле
POSES["hit"] = _pose("combat", Torso=((-10, 0, 0), (0, 0.22, -0.04)), Head=((-16, 0, 0), Z3), Jaw=((14, 0, 0), Z3),
                     **arms((-20, -38, 0), (-30, 0, 0)))
POSES["taunt"] = _pose("stand", Head=((-12, 0, 0), Z3), Jaw=((22, 0, 0), Z3),
                       **arms((0, -6, 0), (-8, 0, 0), (-172, 0, 0), (-14, 0, 0)))  # победа: кулак вверх, хохочет
POSES["dizzy"] = _pose("sleep", Torso=((-16, 14, 0), (0, 0.1, -1.2)), Head=((10, 0, 22), Z3), Jaw=((20, 0, 0), Z3),
                       **arms((-10, -30, 0), (-20, 0, 0)))  # поражение: сел, голова набок
POSES["walkA"] = _pose("stand", Torso=((4, 0, 0), (0, 0, 0.04)), **arms((20, -6, 0), (-14, 0, 0), (-20, 6, 0), (-24, 0, 0)),
                       **legs((-22, 0, 0), (16, 0, 0), (20, 0, 0), (8, 0, 0)))
POSES["walkB"] = _pose("stand", Torso=((4, 0, 0), (0, 0, 0.04)), **arms((-20, -6, 0), (-24, 0, 0), (20, 6, 0), (-14, 0, 0)),
                       **legs((20, 0, 0), (8, 0, 0), (-22, 0, 0), (16, 0, 0)))


def pose_matrices(pose):
    """Мировые матрицы частей в позе (в стадах)."""
    out = {}

    def world(name):
        if name in out:
            return out[name]
        parent, pivot = RIG[name]
        rot, off = pose.get(name, (Z3, Z3))
        r = Euler([math.radians(d) for d in rot], "XYZ").to_matrix().to_4x4()
        local = Vector(pivot) - (Vector(RIG[parent][1]) if parent else Vector())
        m = Matrix.Translation((local + Vector(off)) * SCALE) @ r
        out[name] = (world(parent) @ m) if parent else m
        return out[name]

    for name in RIG:
        world(name)
    return out


def apply_pose(parts, pose, place=Matrix.Identity(4)):
    mats = pose_matrices(POSES[pose])
    low = min((mats[n] @ v.co).z for n, o in parts.items() for v in o.data.vertices)
    ground = Matrix.Translation((0, 0, -low))
    for n, o in parts.items():
        o.matrix_world = place @ ground @ mats[n]
    return {n: ground @ mats[n] for n in parts}


# ── Сборка ───────────────────────────────────────────────────────────────────────────────────────────────────

bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new("Boss2")
bpy.context.scene.collection.children.link(collection)

arts = [trader_head(), trader_body(), trader_limbs()]
report = {"scale": SCALE}
if MODE == "check":
    for art in arts:
        art.build(collection)
        print("CHECK", art.name, json.dumps(art.stats, ensure_ascii=False))
    sys.exit(0)

AX = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))  # оси Roblox: (x, y, z) Blender → (x, z, −y) Roblox
PART_COLOR = {"Head": "F0B088", "Jaw": "D49572", "Torso": "2CB5A8", "Sack": "C9A06A"}  # заготовка до импорта


def write_rig_module(path):
    """Скелет для игры (без запекания): части, точки вращения, габариты, позы — модуль Luau."""
    parts = {}
    for art in arts:
        obj = art.build(collection)
        groups = dict.fromkeys(art.face_groups)
        for g, o in S.split_groups(obj, art, {g: RIG[g][1] for g in groups}, collection).items():
            o.data.transform(Matrix.Scale(SCALE, 4))
            o.location = Vector(RIG[g][1]) * SCALE
            parts[g] = o

    def v3(v):
        return "Vector3.new(%s)" % ", ".join("%.4f" % c for c in v)

    lines = ["-- Скелет босса 2 «Торговец-громила» для Motor6D (D18, D42): части, точки вращения, габариты и ключевые позы.",
             "-- Сгенерировано scripts/blender/boss2_trader.py (режим rig) — руками не править. Оси Roblox, стады; лицо",
             "-- смотрит в +Z модели. pivot — точка вращения части в покое (низ подошв на y = 0), center и size — габариты",
             "-- меша относительно точки вращения. Позы: часть → {x, y, z, r00…r22} — Transform сустава относительно покоя",
             "-- (у Torso — вместе с подъёмом к земле). Ни от чего не зависит.", "", "return {",
             "\tScale = %s," % SCALE, "\tOrder = { %s }," % ", ".join('"%s"' % n for n in RIG), "\tParts = {"]
    for n, (parent, pivot) in RIG.items():
        co = [AX @ v.co for v in parts[n].data.vertices]
        lo = Vector([min(c[i] for c in co) for i in range(3)])
        hi = Vector([max(c[i] for c in co) for i in range(3)])
        lines.append('\t\t%s = { parent = %s, pivot = %s, center = %s, size = %s, map = "%s", color = "%s" },' % (
            n, '"%s"' % parent if parent else "nil", v3(AX @ (Vector(pivot) * SCALE)), v3((lo + hi) / 2),
            v3(hi - lo), MAP_OF[n], PART_COLOR.get(n, "F0B088")))
    lines += ["\t},", "\tPoses = {"]
    for name, pose in POSES.items():
        mats = pose_matrices(pose)
        low = min((mats[n] @ v.co).z for n, o in parts.items() for v in o.data.vertices)
        lines.append("\t\t%s = {" % name)
        for n in RIG:
            rot, off = pose.get(n, (Z3, Z3))
            r = AX @ Euler([math.radians(d) for d in rot], "XYZ").to_matrix() @ AX.transposed()
            t = AX @ (Vector(off) * SCALE)
            if n == "Torso":
                t.y -= low
            nums = [t.x, t.y, t.z] + [r[i][j] for i in range(3) for j in range(3)]
            lines.append("\t\t\t%s = { %s }," % (n, ", ".join("%.4f" % x for x in nums)))
        lines.append("\t\t},")
    lines += ["\t},", "}", ""]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print("RIG_OK", path, len(POSES), "поз")


if MODE == "rig":
    write_rig_module(os.path.join(REPO, "src", "shared", "Config", "Boss2TraderRig.luau"))
    sys.exit(0)


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


parts = {}
for art in arts:
    obj = art.build(collection)
    explode(obj, art, 1)
    uv = S.bake(obj, art, TEXDIR, art.name)
    explode(obj, art, -1)
    report[art.name] = {**art.stats, "uv_fill": round(uv["uv_fill"], 3),
                        "texels_per_stud": round(uv["texels_per_stud"] / SCALE, 1)}
    groups = dict.fromkeys(art.face_groups)
    split = S.split_groups(obj, art, {g: RIG[g][1] for g in groups}, collection)
    for g, o in split.items():
        o.data.transform(Matrix.Scale(SCALE, 4))
        o.location = Vector(RIG[g][1]) * SCALE
        o.data.calc_loop_triangles()
        report.setdefault("tris", {})[g] = len(o.data.loop_triangles)
        parts[g] = o
report["tris_total"] = sum(report["tris"].values())

S.export_fbx([parts[n] for n in RIG], os.path.join(REPO, "assets", "models", "Boss2_Trader.fbx"))

TO_RBX = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
rig = {"parents": {n: RIG[n][0] for n in RIG}, "maps": MAP_OF, "poses": {}}
for n, o in parts.items():
    S.studio_json(o, os.path.join(PREVIEWS, f"Trader_{n}.json"))
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
floor.scale = (1, 2.6, 2.6)
floor.location.y = 8
for i, (light, loc) in enumerate(prev.lights):
    light.data.energy *= 8
    light.data.size *= 2.8
    prev.lights[i] = (light, loc * 2.9)
prev.aim_lights(Vector((0, 0, 0)))


def turn(deg):
    return Matrix.Rotation(math.radians(deg), 4, "Z")


EYE, LOOK = (0, -36, 9.5), 6.5
for pose in ("combat", "stand"):
    tiles = []
    for label, deg in (("front", 0), ("34", -40), ("side", -90), ("back", 180), ("34back", 140)):
        apply_pose(parts, pose, turn(deg))
        tiles.append(prev.shot(os.path.join(PREVIEWS, f"trader_{pose}_{label}.png"), EYE, (0, 0, LOOK), 50, (800, 900)))
    S.strip(tiles, os.path.join(PREVIEWS, f"trader_turns_{pose}.png"))
tiles = []
for label, deg in (("34", -40), ("side", -90), ("front", 0)):
    apply_pose(parts, "sleep", turn(deg))
    tiles.append(prev.shot(os.path.join(PREVIEWS, f"trader_sleep_{label}.png"), EYE, (0, 0, 4.0), 50, (800, 900)))
S.strip(tiles, os.path.join(PREVIEWS, "trader_turns_sleep.png"))
tiles = []
for pose in ("alert", "punch", "slam", "slam2", "hit", "taunt", "dizzy", "walkA"):
    apply_pose(parts, pose, turn(-35))
    tiles.append(prev.shot(os.path.join(PREVIEWS, f"trader_pose_{pose}.png"), EYE, (0, 0, 6.0), 50, (600, 800)))
S.strip(tiles, os.path.join(PREVIEWS, "trader_poses.png"))
apply_pose(parts, "combat", turn(-30))
prev.shot(os.path.join(PREVIEWS, "trader_34_combat.png"), EYE, (0, 0, LOOK), 50, (1100, 1200))
apply_pose(parts, "stand", turn(-24))
prev.shot(os.path.join(PREVIEWS, "trader_head_close.png"), (-5.0, -17.0, 12.6), (-0.6, -1.6, 11.4), 50, (1100, 1100))

# Масштаб: в стойке и спящий рядом с манекеном Roblox (5.2 стада).
apply_pose(parts, "combat", Matrix.Translation((-9.5, 0, 0)) @ turn(-25))
sleeper = {n: o.copy() for n, o in parts.items()}
for o in sleeper.values():
    collection.objects.link(o)
apply_pose(sleeper, "sleep", Matrix.Translation((10.0, 0, 0)) @ turn(-35))
S.mannequin(collection, 0.0, y=-1.5)
prev.aim_lights(Vector((0, 0, 0)))
prev.shot(os.path.join(PREVIEWS, "trader_scale.png"), (0, -58, 10.0), (0, 0, 5.5), 50, (1800, 900))

with open(os.path.join(PREVIEWS, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("TRADER_OK " + json.dumps(report, ensure_ascii=False))
