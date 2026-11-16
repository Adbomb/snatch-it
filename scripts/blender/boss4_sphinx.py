"""Босс 4 «Сфинкс-лежебока», стиль D39: подвижная модель из частей для процедурных анимаций (D18), как пёс, торговец и
Крысиный король. Этап А — модель и визуальная проверка; в игру не подключён (скелет для игры пишется только в
assets/models/Boss4_Sphinx.rig.json, модуля в src/ нет).

По референсу владельца (assets/concepts/boss4/reference.png): живой пухлый лев — самодовольный, ленивый и смешной.
Голова крупная (собрана в прежних координатах и увеличена в HEAD_SCALE раз вокруг шеи): светлые щёки-брыли, морда
двумя ступенями, терракотовый нос, ухмылка «W» с задранными уголками, полуприкрытые сиреневые глаза под тяжёлыми
веками с тёмной стрелкой, дуги бровей, уши торчат над платком. Платок (немес) — ступенчатые слои бирюзы и золота с
терракотовой изнанкой, шире головы; на лбу золотой восьмигранный медальон с тёмно-красным камнем и зубцами, под ним
бирюзовый камень-щиток; концы платка свисают на плечи, на каждом — подвеска (шарик и колокольчик). Воротник: золотое
кольцо на шее и нагрудник ступенями с бирюзовыми вставками и ромбом. Тело тяжёлое и приземистое: грудь-бочка шире и
ниже живота, светлая грудь колесом под нагрудником, живот подтянут к паху, круп восьмигранником, терракотовая попона
с золотой каймой и бляхами. Лапы расставлены широко: лопатка с выступающим локтем и мышцей ступенькой, короткое
предплечье клином, огромная лапа с четырьмя пальцами и золотой манжетой с бирюзой на запястье (три крупных камня
сверху видны, когда лапа лежит или поднята); задние — мощное бедро, голень наклонена назад к скакательному суставу,
лапа с манжетой.
Хвост из трёх звеньев с золотым кольцом и большой бордовой кистью-«кистенём».

Формы — ступенями из блоков и восьмигранников с острыми рёбрами (D39), квадраты-контуры D39 на крупных деталях, мелкие
накладки (глаза, брови, камни, подвески) — гладкие.

Части (Motor6D), 27: Torso (корень) → Head → Jaw, EyelidL/R, BrowL/R, EarL/R, NemesL/R (концы платка);
Torso → Tail1 → Tail2 → Tail3 → Tassel; лапы из трёх частей (FUpper → FLower → FPaw, BUpper → BLower → BPaw);
L — левый бок босса (+x). Веки в модели закрыты (сон); в позах сдвигаются вверх под надбровье: наполовину — ленивый
прищур, выше — глаза открыты (Motor6D не масштабирует). Собрано в масштабе предметов (квадраты D39 того же вида),
затем увеличено в SCALE раз. Три карты 1024² (голова с платком; туловище с хвостом; лапы); окклюзия запекается с
разнесёнными частями, чтобы в любой позе не было чужих теней.

Проверки (во всех режимах, в report.json и в выводе CHECK_…): пересечения частей в каждой позе — глубина, на которую
точки одной части заходят в тела другой, сверх той же пары в стойке; опора лап на землю; переходы между позами тем же
способом, что в игре (Shared/BossAnim: CFrame:Lerp каждого сустава со сглаживанием) — пересечения и отрыв от земли
в промежуточных кадрах.

Пишет assets/models/Boss4_Sphinx.fbx (части Boss4_Sphinx<Карта>_<Часть>, начало координат — точка вращения),
assets/models/Boss4_Sphinx.blend, assets/models/Boss4_Sphinx.rig.json (точки вращения, габариты и позы в осях Roblox),
assets/textures/art/Boss4_Sphinx{Head,Body,Limbs}_{color,normal}.png, а в папку превью — ракурсы, позы, кадр с
манекеном и кадр «камера Roblox». Режимы: check — сборка и проверки; quick — рендеры без запекания (материалы сборки).
Переменная окружения SPHINX_SHOTS (turns | poses | hero | game | trans | all | none | lab:<поза>,<поза>) ограничивает
рендеры: trans — промежуточные кадры переходов и удара хвостом, lab — выбранные позы с четырёх сторон.
Запуск: blender --background --factory-startup --python scripts/blender/boss4_sphinx.py -- <репо> <превью> [check|quick]
Анимации — scripts/blender/boss4_sphinx_anim.py (подключает этот файл как модуль).
"""

import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style as S  # noqa: E402

# Прямой запуск собирает модель; при import (scripts/blender/boss4_sphinx_anim.py) берутся только скелет, позы,
# кинематика и проверки — файлы модели не трогаются.
DIRECT = __name__ == "__main__"
argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
REPO = os.path.abspath(argv[0]) if argv else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                          "..", ".."))
PREVIEWS = os.path.abspath(argv[1]) if len(argv) > 1 else os.path.join(REPO, "assets", "concepts", "boss4", "sphinx_v2")
MODE = argv[2] if DIRECT and len(argv) > 2 else ""
TEXDIR = os.path.join(REPO, "assets", "textures", "art")

SCALE = 3.0  # в игре босс в SCALE раз больше модели
# Быстрый просмотр: меш не масштабируется, масштаб — у объекта (рисунок D39 в материалах сборки — в единицах модели).
OBJ_SCALE = Matrix.Scale(SCALE, 4) if MODE == "quick" else Matrix.Identity(4)

HEAD_SCALE = 1.13  # голова крупнее (правка владельца: +10…15 %); квадраты D39 остаются прежнего размера
HEAD_BACK = 0.5  # голова сдвинута к груди (сборка головы — в прежних координатах)
DROP = 0.12  # корпус опущен: лапы короче, силуэт приземистее (сборка туловища — в прежних координатах)
NECK0 = Vector((0.0, -2.0, 3.05))  # шея в координатах сборки головы: вокруг неё голова увеличена
HEAD_M = (Matrix.Translation((0.0, HEAD_BACK, -DROP)) @ Matrix.Translation(NECK0) @ Matrix.Scale(HEAD_SCALE, 4)
          @ Matrix.Translation(-NECK0))
BODY_M = Matrix.Translation((0.0, 0.0, -DROP))


def hp(x, y, z):
    """Точка из координат сборки головы — в координаты модели."""
    return tuple(round(c, 4) for c in HEAD_M @ Vector((x, y, z)))


def bp(x, y, z):
    """Точка из координат сборки туловища — в координаты модели."""
    return (x, y, round(z - DROP, 4))


# Хвост (координаты сборки туловища): основание → два сустава → кисть. Длиннее прежнего на 11 %: кисть дальше достаёт.
TAIL = ((0.0, 2.42, 2.0), (0.0, 3.2, 2.0), (0.0, 3.78, 2.72), (0.0, 3.9, 3.72))

# Часть → (родитель, точка вращения в координатах модели). Лицо смотрит в −y, верх +z, L — +x.
RIG = {
    "Torso": (None, bp(0.0, 0.3, 1.75)),
    "Head": ("Torso", hp(0.0, -2.0, 3.05)),
    "Jaw": ("Head", hp(0.0, -2.6, 3.0)),
    "EyelidL": ("Head", hp(0.55, -3.17, 3.78)),
    "EyelidR": ("Head", hp(-0.55, -3.17, 3.78)),
    "BrowL": ("Head", hp(0.56, -3.28, 4.23)),
    "BrowR": ("Head", hp(-0.56, -3.28, 4.23)),
    "EarL": ("Head", hp(0.9, -2.4, 4.6)),
    "EarR": ("Head", hp(-0.9, -2.4, 4.6)),
    "NemesL": ("Head", hp(1.44, -2.55, 2.84)),
    "NemesR": ("Head", hp(-1.44, -2.55, 2.84)),
    "Tail1": ("Torso", bp(*TAIL[0])),
    "Tail2": ("Tail1", bp(*TAIL[1])),
    "Tail3": ("Tail2", bp(*TAIL[2])),
    "Tassel": ("Tail3", bp(*TAIL[3])),
}
FX, BX = 0.98, 1.1  # середина передней и задней лапы по x: лапы расставлены шире туловища
for side, s in (("L", 1), ("R", -1)):
    RIG["FUpper" + side] = ("Torso", (s * FX, -0.95, 1.78))
    RIG["FLower" + side] = ("FUpper" + side, (s * FX, -0.95, 0.98))
    RIG["FPaw" + side] = ("FLower" + side, (s * FX, -1.0, 0.5))
    RIG["BUpper" + side] = ("Torso", (s * 1.05, 1.7, 1.73))
    RIG["BLower" + side] = ("BUpper" + side, (s * BX, 1.48, 0.98))
    RIG["BPaw" + side] = ("BLower" + side, (s * BX, 1.78, 0.46))

MAPS = {"Head": ("Head", "Jaw", "EyelidL", "EyelidR", "BrowL", "BrowR", "EarL", "EarR", "NemesL", "NemesR"),
        "Body": ("Torso", "Tail1", "Tail2", "Tail3", "Tassel"),
        "Limbs": tuple(p + side for p in ("FUpper", "FLower", "FPaw", "BUpper", "BLower", "BPaw") for side in "LR")}
MAP_OF = {part: m for m, parts in MAPS.items() for part in parts}


def colors(a):
    a.paint("fur", "E39C48", rings=True)  # песочная шерсть
    a.paint("furL", "F6C56A", rings=True)  # светлее: щёки, морда, грудь, пальцы
    a.paint("gold", "F8B21C", rings=True)  # золото украшений — ярче и желтее шерсти
    a.paint("ngold", "EFA428", rings=True)  # золотые полосы платка — теплее, ближе к шерсти
    a.paint("teal", "157888", rings=True)  # полосы платка
    a.paint("terra", "9E3A2E", rings=True)  # терракота: изнанка платка, лента на лбу, попона
    a.paint("tassel", "9E3A4E", rings=True)  # кисть хвоста
    for key, code in (("furS", "E39C48"), ("furLS", "F6C56A"), ("furD", "C98230"), ("goldS", "F8B21C"),
                      ("goldL", "FFD75A"), ("rim", "B97A10"), ("tealS", "157888"), ("turq", "2FC4BA"),
                      ("turqL", "9BEFE6"), ("terraS", "9E3A2E"), ("ruby", "9C3550"), ("rubyL", "CC6078"),
                      ("tasselD", "7A2A3E"), ("gemgrey", "8FC3C4"), ("nose", "A04A2A"), ("noseL", "BE6540"),
                      ("line", "5A2A1A"), ("brow", "552A18"), ("lash", "3A1E14"), ("eye", "F6ECF8"),
                      ("iris", "B58BDA"), ("pupil", "6F4399"), ("glint", "FFFFFF"), ("mouth", "7A2433"),
                      ("tongue", "F07A8C"), ("tooth", "FFF8EA"), ("earin", "C9783F"), ("groove", "B06A26"), ("pad", "8C4628")):
        a.paint(key, code)


def tilt(c, axis, deg):
    """Поворот детали вокруг точки c."""
    c = Vector(c)
    return Matrix.Translation(c) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-c)


def bar(a, key, p0, p1, w, h=None, bevel=S.BEVEL):
    """Брусок от точки p0 до p1 с сечением w × h (звенья хвоста, линии рта)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    up = "Y" if abs(d.normalized().z) > 0.95 else "Z"
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("X", up).to_matrix().to_4x4()
    h = h or w
    a.box(key, -d.length / 2, d.length / 2, -w / 2, w / 2, -h / 2, h / 2, bevel=bevel, matrix=m)
    return m, d.length


def oct_y(a, key, x0, x1, z0, z1, cut, y0, y1, matrix=None):
    """Восьмигранник в плоскости x–z, вытянутый вдоль y (спереди — со срезанными углами)."""
    a.prism(key, S.octagon(x0, x1, z0, z1, cut), y0, y1, axis="y", matrix=matrix)


def oct_z(a, key, x0, x1, y0, y1, cut, z0, z1, matrix=None):
    """Восьмигранник в плоскости x–y, вытянутый вдоль z (сверху — со срезанными углами)."""
    a.prism(key, S.octagon(x0, x1, y0, y1, cut), z0, z1, axis="z", matrix=matrix)


def oct_x(a, key, z0, z1, y0, y1, cut, x0, x1, matrix=None):
    """Восьмигранник в плоскости z–y, вытянутый вдоль x (сбоку — со срезанными углами)."""
    a.prism(key, S.octagon(z0, z1, y0, y1, cut), min(x0, x1), max(x0, x1), axis="x", matrix=matrix)


def regular_oct(cx, cz, r):
    """Правильный восьмиугольник радиуса r (до стороны) с центром (cx, cz) — «пиксельный круг»."""
    return S.octagon(cx - r, cx + r, cz - r, cz + r, r * (2 - math.sqrt(2)))


def sx(s, u, v):
    return sorted((s * u, s * v))


# Слои платка сверху вниз: (z0, z1, полуширина, цвет); каждый ниже — шире, ближе к зрителю и дальше назад.
WING = [(4.3, 4.62, 1.2, "ngold"), (4.0, 4.3, 1.42, "teal"), (3.7, 4.0, 1.6, "ngold"), (3.4, 3.7, 1.74, "teal"),
        (3.1, 3.4, 1.84, "ngold"), (2.82, 3.1, 1.9, "teal")]


# ── Голова: череп, щёки, морда, нос, ухмылка, глаза, платок, медальон; челюсть, веки, брови, уши, концы платка ──


def sphinx_head():
    a = S.Art("Boss4_SphinxHead", ring_z0=hp(0.0, 0.0, 3.44)[2])
    colors(a)
    a.transform = HEAD_M  # голова крупнее и ближе к груди: платок лежит на плечах
    a.group = "Head"
    a.box("fur", -1.0, 1.0, -3.1, -1.85, 2.95, 4.35)  # череп
    oct_y(a, "furL", -1.14, 1.14, 2.78, 3.46, 0.22, -3.18, -2.25)  # щёки-брыли: низ лица шире и светлее
    a.box("fur", -0.96, 0.96, -3.25, -3.0, 4.1, 4.33)  # надбровье-козырёк: под него уходят поднятые веки
    # морда двумя ступенями: широкие подушечки и выступ под носом
    oct_y(a, "furL", -0.76, 0.76, 2.98, 3.48, 0.16, -3.42, -3.1)
    oct_y(a, "furL", -0.46, 0.46, 3.04, 3.48, 0.1, -3.5, -3.4)
    a.prism("furS", [(3.46, -3.42), (3.46, -3.1), (3.92, -3.1), (3.6, -3.42)], -0.2, 0.2, axis="x")  # переносица
    a.prism("nose", [(-0.28, 3.58), (0.28, 3.58), (0.17, 3.33), (-0.17, 3.33)], -3.6, -3.42, axis="y")
    a.box("noseL", -0.18, 0.18, -3.615, -3.595, 3.5, 3.545, bevel=0)
    # ухмылка «W»: желобок под носом, две дуги и задранные уголки на щеках
    a.box("line", -0.035, 0.035, -3.516, -3.49, 3.14, 3.33, bevel=0)
    for s in (1, -1):
        d = 0.003 * s  # линии рта на разной глубине: без совпадающих граней
        bar(a, "line", (0.0, -3.507 + d, 3.17), (s * 0.24, -3.507 + d, 3.09), 0.036, 0.07, bevel=0)
        bar(a, "line", (s * 0.21, -3.5 + d, 3.09), (s * 0.46, -3.5 + d, 3.15), 0.036, 0.07, bevel=0)
        bar(a, "line", (s * 0.45, -3.425, 3.15), (s * 0.73, -3.425, 3.32), 0.036, 0.07, bevel=0)
        a.box("line", *sx(s, 0.7, 0.78), -3.45, -3.414, 3.3, 3.4, bevel=0)
    a.box("mouth", -0.46, 0.46, -3.34, -2.6, 2.94, 3.02, bevel=0)  # пасть изнутри — видна, когда челюсть опущена
    # глаза: светлый белок, сиреневая радужка, зрачок, блик; оба смотрят чуть вправо от босса; нижняя черта
    for s in (1, -1):
        a.box("eye", *sx(s, 0.2, 0.9), -3.15, -3.08, 3.5, 4.06, bevel=0.02)
        c = s * 0.55 - 0.1
        a.box("iris", c - 0.22, c + 0.22, -3.17, -3.145, 3.51, 4.03, bevel=0)
        a.box("pupil", c - 0.1, c + 0.1, -3.185, -3.165, 3.54, 3.9, bevel=0)
        a.box("glint", c - 0.2, c - 0.11, -3.195, -3.18, 3.62, 3.71, bevel=0)
        a.box("lash", *sx(s, 0.2, 0.9), -3.155, -3.12, 3.46, 3.5, bevel=0)
    # платок: слои бирюзы и золота, терракотовая изнанка выступает кантом сзади; сзади — «коса» платка
    for i, (z0, z1, hw, key) in enumerate(WING):
        front, back = -2.7 - 0.04 * i, -1.6 + 0.05 * i
        a.box(key, -hw, hw, front, back, z0, z1)
        if i:
            a.box("terra", -hw - 0.06, hw + 0.06, back - 0.3, back - 0.04, z0 + 0.03, z1 - 0.03, bevel=0)
    a.box("teal", -0.42, 0.42, -1.4, -1.1, 2.9, 3.34)
    a.box("goldS", -0.46, 0.46, -1.42, -1.08, 3.0, 3.12)
    for s in (1, -1):
        a.box("goldS", *sx(s, 1.0, 1.13), -3.0, -2.7, 2.84, 4.28)  # золотой кант вдоль лица
        a.box("teal", *sx(s, 0.34, 0.62), -2.65, -1.66, 4.62, 4.68)  # полосы на темени
    a.box("teal", -0.11, 0.11, -2.65, -1.66, 4.62, 4.68)
    a.box("terra", -1.05, 1.05, -3.29, -2.7, 4.33, 4.46)  # лента на лбу
    a.box("ngold", -1.09, 1.09, -3.33, -2.7, 4.46, 4.6)  # золотой край платка
    # медальон: золотой восьмигранник с тёмно-красным камнем, три зубца; под ним бирюзовый щиток
    a.prism("goldS", regular_oct(0.0, 4.8, 0.43), -3.47, -3.3, axis="y")
    a.frame("rim", regular_oct(0.0, 4.8, 0.45), 0.085, -3.51, -3.45, axis="y")
    a.prism("ruby", regular_oct(0.0, 4.8, 0.29), -3.56, -3.47, axis="y")
    a.prism("rubyL", regular_oct(-0.07, 4.87, 0.11), -3.585, -3.56, axis="y", bevel=0)
    for deg in (0, 45, -45):
        a.box("goldS", -0.1, 0.1, -3.45, -3.32, 5.2, 5.4, matrix=tilt((0, -3.38, 4.8), "Y", deg))
    a.prism("goldS", [(-0.23, 4.42), (0.23, 4.42), (0.23, 4.26), (0.0, 4.06), (-0.23, 4.26)], -3.41, -3.25, axis="y")
    a.prism("turq", [(-0.13, 4.37), (0.13, 4.37), (0.13, 4.27), (0.0, 4.15), (-0.13, 4.27)], -3.45, -3.41, axis="y",
            bevel=0)

    a.group = "Jaw"  # подбородок, язык, два маленьких клыка (прячутся в морде, пока пасть закрыта)
    oct_y(a, "furL", -0.5, 0.5, 2.72, 3.0, 0.12, -3.37, -2.6)
    a.box("tongue", -0.24, 0.24, -3.26, -2.7, 3.0, 3.035, bevel=0)
    for s in (1, -1):
        x0, x1 = sx(s, 0.28, 0.42)
        t0, t1 = sx(s, 0.33, 0.37)
        a.frustum("tooth", (x0, x1, -3.32, -3.18), (t0, t1, -3.27, -3.23), 3.0, 3.16, bevel=0)

    for side, s in (("L", 1), ("R", -1)):
        a.group = "Eyelid" + side  # закрытое веко с тёмной стрелкой по нижнему краю
        a.box("furS", *sx(s, 0.17, 0.93), -3.21, -3.13, 3.49, 4.07, bevel=0)
        a.box("lash", *sx(s, 0.15, 0.95), -3.235, -3.2, 3.482, 3.58, bevel=0)
        a.box("lash", *sx(s, 0.89, 1.08), -3.239, -3.204, 3.55, 3.64, bevel=0,
              matrix=tilt((s * 0.92, -3.22, 3.59), "Y", -s * 28))

        a.group = "Brow" + side  # тяжёлая бровь дугой: середина выше, наружный конец опущен
        a.box("brow", *sx(s, 0.14, 0.6), -3.33, -3.24, 4.15, 4.32, bevel=0,
              matrix=tilt((s * 0.56, -3.28, 4.23), "Y", -s * 8))
        a.box("brow", *sx(s, 0.52, 0.98), -3.334, -3.244, 4.15, 4.32, bevel=0,
              matrix=tilt((s * 0.56, -3.28, 4.23), "Y", s * 18))

        a.group = "Ear" + side  # ухо над платком: пятиугольник, тёмная середина, наклонено наружу
        c = s * 0.9
        m = tilt((c, -2.4, 4.6), "Y", s * 10)
        a.prism("fur", [(c - 0.33, 4.56), (c + 0.33, 4.56), (c + 0.33, 4.92), (c + s * 0.06, 5.32), (c - 0.33, 4.92)],
                -2.56, -2.24, axis="y", matrix=m)
        a.prism("earin", [(c - 0.19, 4.64), (c + 0.19, 4.64), (c + 0.19, 4.88), (c + s * 0.05, 5.12), (c - 0.19, 4.88)],
                -2.595, -2.56, axis="y", bevel=0, matrix=m)

        a.group = "Nemes" + side  # конец платка на плече и подвеска у щеки: шарик и колокольчик
        a.box("ngold", *sx(s, 1.02, 1.88), -2.98, -2.14, 2.56, 2.84)
        a.box("teal", *sx(s, 1.04, 1.86), -2.96, -2.16, 2.3, 2.56)
        a.box("terraS", *sx(s, 1.08, 1.82), -2.92, -2.2, 2.18, 2.3)
        c = s * 1.6  # подвеска у наружного угла: не закрывает лапу и браслет
        a.box("rim", c - 0.035, c + 0.035, -2.885, -2.815, 2.08, 2.18, bevel=0)
        a.prism("goldS", regular_oct(c, 1.99, 0.105), -2.955, -2.745, axis="y")
        a.frustum("goldS", (c - 0.16, c + 0.16, -3.01, -2.69), (c - 0.07, c + 0.07, -2.92, -2.78), 1.58, 1.9)
        a.box("rim", c - 0.18, c + 0.18, -3.03, -2.67, 1.54, 1.59, bevel=0)
    return a


# ── Тело: грудь-бочка, живот, круп, шея, воротник с нагрудником, попона; хвост из трёх звеньев и кисть ─────────


def sphinx_body():
    a = S.Art("Boss4_SphinxBody", ring_z0=1.86 - DROP)
    colors(a)
    a.transform = BODY_M  # корпус опущен на DROP
    a.group = "Torso"
    oct_x(a, "fur", 0.8, 2.68, -1.7, -0.08, 0.28, -1.28, 1.28)  # грудь-бочка: шире и ниже живота
    oct_x(a, "fur", 1.1, 2.42, -1.56, -0.25, 0.2, -1.4, 1.4)  # плечевая масса под лопатками
    a.box("fur", -0.98, 0.98, -1.5, -0.3, 2.68, 2.9)  # холка
    # живот: спереди ниже, к паху подтянут — снизу не прямоугольный просвет, а ступень и скос
    a.prism("fur", [(0.98, -0.15), (0.98, 0.55), (1.24, 1.35), (2.5, 1.35), (2.5, -0.15)], -1.08, 1.08, axis="x")
    a.box("fur", -1.18, 1.18, -0.05, 1.25, 1.3, 2.3)  # бока
    oct_x(a, "fur", 0.95, 2.58, 1.3, 2.5, 0.32, -1.2, 1.2)  # круп ниже холки
    oct_z(a, "furL", -0.9, 0.9, -1.92, -1.5, 0.18, 0.94, 1.62)  # светлая грудь колесом под нагрудником
    a.box("furL", -0.9, 0.9, -0.05, 0.5, 0.92, 0.98)  # светлое брюхо
    a.prism("fur", [(2.4, -1.2), (2.4, -1.95), (3.2, -2.2), (3.2, -1.45)], -0.76, 0.76, axis="x")  # шея вперёд-вверх
    # воротник: золотое кольцо на шее с бирюзой и нагрудник двумя ступенями с ромбом
    oct_z(a, "gold", -1.02, 1.02, -2.14, -1.15, 0.3, 2.36, 2.7)
    for x in (-0.46, 0.0, 0.46):
        a.box("turq", x - 0.15, x + 0.15, -2.17, -2.14, 2.44, 2.62, bevel=0)
    for s in (1, -1):
        a.box("turq", *sx(s, 1.02, 1.05), -1.95, -1.6, 2.44, 2.62, bevel=0)
    a.box("gold", -1.02, 1.02, -1.86, -1.6, 2.02, 2.36)
    a.box("gold", -0.7, 0.7, -1.84, -1.6, 1.74, 2.02)
    for x in (-0.74, 0.74):
        a.box("turq", x - 0.15, x + 0.15, -1.89, -1.86, 2.09, 2.29, bevel=0)
    for x in (-0.52, 0.52):
        a.box("turq", x - 0.1, x + 0.1, -1.87, -1.84, 1.81, 1.95, bevel=0)
    a.prism("goldS", [(0.0, 2.44), (0.38, 2.06), (0.0, 1.68), (-0.38, 2.06)], -1.97, -1.84, axis="y")
    a.frame("rim", [(0.0, 2.47), (0.41, 2.06), (0.0, 1.65), (-0.41, 2.06)], 0.07, -2.0, -1.95, axis="y")
    a.prism("turq", [(0.0, 2.31), (0.25, 2.06), (0.0, 1.81), (-0.25, 2.06)], -2.03, -1.97, axis="y", bevel=0)
    a.prism("turqL", [(-0.05, 2.21), (0.06, 2.1), (-0.05, 1.99), (-0.16, 2.1)], -2.05, -2.03, axis="y", bevel=0)
    # попона: терракота с золотой каймой, бляха с бирюзой на спине и по бляхе с серым камнем на боках
    a.box("terra", -0.86, 0.86, -0.02, 1.5, 2.5, 2.63)
    for y in (-0.02, 1.5):
        a.box("goldS", -0.92, 0.92, y - 0.08, y + 0.08, 2.52, 2.69)
    oct_z(a, "goldS", -0.33, 0.33, 0.41, 1.07, 0.19, 2.63, 2.71)
    oct_z(a, "turq", -0.2, 0.2, 0.54, 0.94, 0.12, 2.71, 2.76)
    for s in (1, -1):
        a.box("terra", *sx(s, 1.18, 1.26), -0.02, 0.82, 1.74, 2.5)
        a.box("terra", *sx(s, 0.86, 1.24), 0.0, 0.8, 2.44, 2.53)
        a.box("goldS", *sx(s, 1.18, 1.3), -0.07, 0.87, 1.62, 1.76)
        oct_x(a, "goldS", 1.9, 2.34, 0.18, 0.62, 0.13, s * 1.26, s * 1.33)
        oct_x(a, "gemgrey", 1.99, 2.25, 0.27, 0.53, 0.08, s * 1.33, s * 1.36)

    # хвост: толстый, три звена назад и вверх дугой, на третьем золотое кольцо с бирюзой; кисть — бордовый «кистень»
    for i, w in ((0, 0.46), (1, 0.44), (2, 0.42)):
        a.group = f"Tail{i + 1}"
        p0, p1 = TAIL[i], TAIL[i + 1]
        k = w / 2 + 0.02
        a.box("furS", -k, k, p0[1] - k, p0[1] + k, p0[2] - k, p0[2] + k, bevel=0)  # сустав
        m, length = bar(a, "furS", p0, p1, w)
    a.box("goldS", length / 2 - 0.42, length / 2 - 0.1, -0.28, 0.28, -0.28, 0.28, matrix=m)
    a.box("rim", length / 2 - 0.45, length / 2 - 0.41, -0.295, 0.295, -0.295, 0.295, bevel=0, matrix=m)
    a.box("turq", length / 2 - 0.34, length / 2 - 0.18, -0.305, 0.305, -0.1, 0.1, bevel=0, matrix=m)
    a.group = "Tassel"
    cy, z = TAIL[3][1] + 0.02, TAIL[3][2] - 0.06
    oct_z(a, "goldS", -0.26, 0.26, cy - 0.26, cy + 0.26, 0.13, z, z + 0.18)
    for z0, z1, r, key in ((0.18, 0.4, 0.4, "tasselD"), (0.4, 0.88, 0.58, "tassel"), (0.88, 1.18, 0.48, "tasselD"),
                           (1.18, 1.4, 0.32, "tassel"), (1.4, 1.52, 0.16, "tasselD")):
        oct_z(a, key, -r, r, cy - r, cy + r, r * 0.55, z + z0, z + z1)
    return a


# ── Лапы: лопатка, предплечье, огромная лапа с манжетой и четырьмя пальцами; бедро, голень, лапа с манжетой ────


def toes(a, s, x_in, width, y_back, y_front, top):
    """Четыре пальца: срезанные спереди бруски вдоль x, между ними тёмные ложбинки."""
    d = -1 if y_front < y_back else 1  # вперёд — к −y
    step = width / 4
    for i in range(4):
        x0, x1 = sx(s, x_in + i * step + 0.016, x_in + (i + 1) * step - 0.016)
        a.prism("furL", [(0.0, y_back), (0.0, y_front - d * 0.03), (top * 0.5, y_front), (top * 0.92, y_front - d * 0.16),
                         (top, y_back)], x0, x1, axis="x")
    a.box("groove", *sx(s, x_in + 0.03, x_in + width - 0.03), y_back + d * 0.02, y_front - d * 0.08, 0.02, top * 0.86,
          bevel=0)


def bracelet(a, s, x0, x1, y0, y1, z0, z1, top=None):
    """Золотая манжета на запястье (часть лапы) с тёмным кантом и бирюзой: по три камня спереди, по два сзади и с
    боков; top = (y_a, y_b) — ещё три крупных камня сверху: видны, когда лапа лежит или поднята тыльной стороной
    к зрителю (в стойке их прячет предплечье)."""
    a.box("goldS", *sx(s, x0, x1), y0, y1, z0, z1)
    a.box("rim", *sx(s, x0 - 0.018, x1 + 0.018), y0 - 0.018, y1 + 0.018, z0 + 0.03, z0 + 0.08, bevel=0)
    a.box("rim", *sx(s, x0 - 0.018, x1 + 0.018), y0 - 0.018, y1 + 0.018, z1 - 0.08, z1 - 0.03, bevel=0)
    zc, h = (z0 + z1) / 2, (z1 - z0) * 0.26
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    front = y0 if abs(y0) > abs(y1) else y1  # сторона пальцев: дальше от середины тела
    back = y1 if front == y0 else y0
    d = -1 if front < back else 1
    for dx in (-0.42, 0.0, 0.42):
        a.box("turq", *sx(s, xm + dx - 0.13, xm + dx + 0.13), front, front + d * 0.035, zc - h, zc + h, bevel=0)
        if top:
            a.box("turq", *sx(s, xm + dx - 0.15, xm + dx + 0.15), top[0], top[1], z1, z1 + 0.035, bevel=0)
    for dx in (-0.26, 0.26):
        a.box("turq", *sx(s, xm + dx - 0.13, xm + dx + 0.13), back, back - d * 0.035, zc - h, zc + h, bevel=0)
    for dy in (-0.2, 0.2):
        a.box("turq", *sx(s, x1, x1 + 0.035), ym + dy - 0.12, ym + dy + 0.12, zc - h, zc + h, bevel=0)
        a.box("turq", *sx(s, x0 - 0.035, x0), ym + dy - 0.12, ym + dy + 0.12, zc - h, zc + h, bevel=0)


def sphinx_limbs():
    a = S.Art("Boss4_SphinxLimbs", ring_z0=1.44)
    colors(a)
    for side, s in (("L", 1), ("R", -1)):
        a.group = "FUpper" + side  # лопатка: сверху широкая, к локтю уже, локоть выступает назад; мышца ступенькой
        a.prism("fur", [(1.0, -1.44), (0.9, -0.62), (1.15, -0.3), (2.0, -0.22), (2.3, -0.42), (2.3, -1.52),
                        (2.08, -1.72), (1.42, -1.72)], *sx(s, 0.54, 1.48), axis="x")
        a.prism("fur", [(1.36, -1.4), (1.3, -0.7), (1.62, -0.46), (2.0, -0.44), (2.16, -0.6), (2.16, -1.46),
                        (2.0, -1.6), (1.62, -1.6)], *sx(s, 1.48, 1.62), axis="x")
        a.group = "FLower" + side  # короткое предплечье клином: у локтя шире, у запястья уже
        x0, x1 = sx(s, 0.6, 1.36)
        t0, t1 = sx(s, 0.54, 1.44)
        a.frustum("fur", (x0, x1, -1.36, -0.62), (t0, t1, -1.46, -0.48), 0.46, 1.12)
        a.group = "FPaw" + side  # огромная лапа: основание, манжета на запястье, четыре пальца, подушечки
        a.box("fur", *sx(s, 0.3, 1.66), -1.76, -0.5, 0.0, 0.56)
        bracelet(a, s, 0.26, 1.7, -1.46, -0.56, 0.56, 0.9, top=(-1.26, -0.78))
        toes(a, s, 0.3, 1.36, -1.76, -2.32, 0.68)
        a.box("pad", *sx(s, 0.6, 1.36), -1.54, -0.84, -0.006, 0.02, bevel=0)
        for i in range(4):
            a.box("pad", *sx(s, 0.39 + i * 0.34, 0.39 + i * 0.34 + 0.16), -2.16, -1.9, -0.006, 0.02, bevel=0)

        a.group = "BUpper" + side  # мощное бедро: сверху и сзади шире, колено вперёд; мышца ступенькой наружу
        a.prism("fur", [(0.92, 1.0), (0.92, 1.9), (1.3, 2.5), (2.2, 2.66), (2.46, 2.4), (2.46, 1.02), (2.2, 0.76),
                        (1.4, 0.74)], *sx(s, 0.74, 1.58), axis="x")
        a.prism("fur", [(1.3, 1.16), (1.3, 1.9), (1.56, 2.3), (2.14, 2.44), (2.3, 2.26), (2.3, 1.16), (2.12, 0.96),
                        (1.6, 0.94)], *sx(s, 1.58, 1.72), axis="x")
        a.group = "BLower" + side  # голень наклонена назад — к скакательному суставу
        a.prism("fur", [(1.1, 1.08), (1.1, 1.8), (0.44, 2.14), (0.44, 1.42)], *sx(s, 0.72, 1.48), axis="x")
        a.group = "BPaw" + side
        a.box("fur", *sx(s, 0.5, 1.7), 1.02, 2.24, 0.0, 0.5)
        bracelet(a, s, 0.46, 1.74, 1.22, 2.2, 0.5, 0.82)
        toes(a, s, 0.5, 1.2, 1.02, 0.52, 0.6)
    return a


# ── Позы: часть → (поворот XYZ в градусах относительно родителя, сдвиг в единицах модели) ─────────────────────
# Поворот вокруг x: + — вниз-назад (кивок, лапа назад), − — вверх-вперёд; вокруг y: + — крен влево (+x);
# вокруг z: + — поворот влево (+x).

Z3 = (0, 0, 0)
CLOSED, SQUINT, HALF, OPEN = (Z3, (0, 0, 0.2 * HEAD_SCALE), (0, 0, 0.33 * HEAD_SCALE), (0, 0, 0.5 * HEAD_SCALE))


def mirror(r):
    return (r[0], -r[1], -r[2])


def rot(deg):
    return Euler([math.radians(d) for d in deg], "XYZ").to_matrix()


def rel(parent, child):
    """Поворот дочерней части относительно родителя по их поворотам относительно туловища (XYZ, градусы)."""
    e = (rot(parent).inverted() @ rot(child)).to_euler("XYZ")
    return tuple(round(math.degrees(v), 3) for v in e)


def lids(off, off_r=None):
    return {"EyelidL": (Z3, off), "EyelidR": (Z3, off_r or off)}


def brows(deg, lift=0.0, deg_r=None, lift_r=None):
    """Брови: поворот в плоскости лица (+ — наружный конец левой вниз, хмурый — отрицательный) и подъём."""
    dr = deg if deg_r is None else deg_r
    lr = lift if lift_r is None else lift_r
    return {"BrowL": ((0, deg, 0), (0, 0, lift)), "BrowR": ((0, -dr, 0), (0, 0, lr))}


def fleg(side, upper, lower, paw, off=Z3):
    """Передняя лапа: повороты лопатки, предплечья и лапы относительно туловища."""
    return {"FUpper" + side: (upper, off), "FLower" + side: (rel(upper, lower), Z3), "FPaw" + side: (rel(lower, paw), Z3)}


def bleg(side, upper, lower, paw, off=Z3):
    return {"BUpper" + side: (upper, off), "BLower" + side: (rel(upper, lower), Z3), "BPaw" + side: (rel(lower, paw), Z3)}


def legs4(fl, fr, bl, br):
    out = {}
    out.update(fleg("L", *fl))
    out.update(fleg("R", *fr))
    out.update(bleg("L", *bl))
    out.update(bleg("R", *br))
    return out


def tail(t1, t2, t3, tassel):
    """Хвост: повороты звеньев и кисти относительно туловища."""
    return {"Tail1": (t1, Z3), "Tail2": (rel(t1, t2), Z3), "Tail3": (rel(t2, t3), Z3), "Tassel": (rel(t3, tassel), Z3)}


def X(d):
    return (d, 0, 0)


def yawed(r, z):
    """Тот же поворот, развёрнутый вокруг вертикали туловища на z градусов."""
    return (r[0], r[1], r[2] + z)


def aim(toes, top):
    """Поворот лапы относительно туловища (XYZ, градусы): пальцы смотрят по toes, верх лапы — по top."""
    t = Vector(toes).normalized()
    n = Vector(top)
    n = (n - n.dot(t) * t).normalized()
    y = -t
    m = Matrix((y.cross(n), y, n)).transposed()
    return tuple(round(math.degrees(v), 3) for v in m.to_euler("XYZ"))


def orient(down, front):
    """Поворот части лапы относительно туловища (XYZ, градусы): её низ (к следующему суставу) смотрит по down,
    перед — по front."""
    d = Vector(down).normalized()
    f = Vector(front)
    return aim(tuple(f - f.dot(d) * d), tuple(-d))


LEGS = {"FL": ("F", "L"), "FR": ("F", "R"), "BL": ("B", "L"), "BR": ("B", "R")}


def plant(torso=(Z3, Z3), follow=None, **feet):
    """Лапы по точкам опоры (обратная кинематика двух костей), чтобы в позах с наклонённым или сдвинутым туловищем
    лапы стояли на земле. torso — (поворот, сдвиг) туловища в позе. Для каждой лапы FL, FR, BL, BR — (dx, dy, dz,
    наклон, разворот): сдвиг запястья от места в стойке, наклон лапы (+ — пальцами вниз) и её разворот в градусах;
    без записи лапа стоит на своём месте плашмя. follow — лапа: доля, на которую её место переносится вслед за
    туловищем (1 — под своё плечо). Локти сгибаются назад, колени — вперёд."""
    r, off = rot(torso[0]), Vector(torso[1])
    p = Vector(RIG["Torso"][1])
    out = {}
    for key, (fb, side) in LEGS.items():
        up, lo, paw = fb + "Upper" + side, fb + "Lower" + side, fb + "Paw" + side
        s, e, w = Vector(RIG[up][1]), Vector(RIG[lo][1]), Vector(RIG[paw][1])
        dx, dy, dz, pitch, yaw = (tuple(feet.get(key, ())) + (0, 0, 0, 0, 0))[:5]
        k = (follow or {}).get(key, 0.0)
        moved = p + off + r @ (w - p)
        base = w.lerp(Vector((moved.x, moved.y, w.z)), k)
        local = p + r.inverted() @ (base + Vector((dx, dy, dz)) - p - off)  # цель в покоящихся осях туловища
        l1, l2 = (e - s).length, (w - e).length
        d = local - s
        if d.length > l1 + l2 + 0.01:
            print(f"PLANT {key} {torso}: short by {d.length - l1 - l2:.2f}")
        dist = min(d.length, l1 + l2 - 0.002)
        u = d.normalized()
        along = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
        pole = Vector((0, 1, 0)) if fb == "F" else Vector((0, -1, 0))
        pole = (pole - pole.dot(u) * u).normalized()
        bend = s + along * u + math.sqrt(max(l1 * l1 - along * along, 0.0)) * pole

        def deg(m):
            return tuple(round(math.degrees(v), 3) for v in m.to_euler("XYZ"))

        q_up = (e - s).rotation_difference(bend - s).to_matrix()
        q_lo = (w - e).rotation_difference(s + dist * u - bend).to_matrix()
        q_paw = r.inverted() @ rot((pitch, 0, yaw))
        out.update((fleg if fb == "F" else bleg)(side, deg(q_up), deg(q_lo), deg(q_paw)))
    return out


POSES = {}
# стойка на четырёх лапах: ленивый прищур, хвост вверх
POSES["stand"] = {
    **lids(HALF), **brows(0),
    **tail(X(0), X(0), X(0), X(0)),
}
# лёжа: грудь на земле, локти у земли, предплечья и лапы вперёд; задние поджаты — колено вперёд, голень назад вдоль
# земли, лапа вперёд вдоль живота; хвост лежит дугой позади левого бедра, кисть торчит вверх
LIE_DROP = -0.7
LIE_F = (X(-34), X(-88), X(0))
LIE_B = (X(-26), X(56), X(0))
LIE_TAIL = ((0, 0, -30), (4, 0, -70), (-28, 0, -130), (-50, 0, -130))
# сон по референсу: голова повёрнута и наклонена к правой лапе; правая лапа — подпорка: локоть у земли рядом с
# грудью, предплечье поднято, ладонь прижата к щеке, пальцы вверх, тыльная сторона наружу; левая лапа расслабленно
# вытянута вперёд и чуть в сторону; глаза закрыты
LIE_G = 0.68  # высота земли в координатах модели, когда босс лежит (низ груди и предплечий)


def reach(side, off, wrist, toes_dir, top_dir, pole=(0, 0, -1), front=(0, -1, 0)):
    """Передняя лапа по цели: запястье в точке wrist = (x, y, высота над землёй лёжа), локоть — как можно дальше
    по pole (вниз — к земле); лапа задана направлениями пальцев и тыльной стороны. Плечо сдвинуто на off."""
    up, lo = "FUpper" + side, "FLower" + side
    l1 = (Vector(RIG[lo][1]) - Vector(RIG[up][1])).length
    l2 = (Vector(RIG["FPaw" + side][1]) - Vector(RIG[lo][1])).length
    s = Vector(RIG[up][1]) + Vector(off)
    w = Vector((wrist[0], wrist[1], wrist[2] + LIE_G))
    d = (w - s).length
    if d > l1 + l2 - 0.01:
        print(f"REACH {side}: не дотягивается на {d - l1 - l2 + 0.01:.2f}")
        d = l1 + l2 - 0.01
    u = (w - s).normalized()
    along = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    side_v = Vector(pole) - Vector(pole).dot(u) * u
    e = s + along * u + math.sqrt(max(l1 * l1 - along * along, 0.0)) * side_v.normalized()
    return fleg(side, orient(tuple(e - s), front), orient(tuple(s + d * u - e), front), aim(toes_dir, top_dir), off)


# правая лапа — подпорка, как в референсе: локоть на земле перед грудью, предплечье стоит столбиком, на нём манжета
# и лапа-кулак подошвой вверх, пальцами к зрителю; щека лежит на лапе сверху
PROP = reach("R", (-0.1, -0.28, -0.1), (-1.04, -1.9, 0.78), (0.1, -0.93, 0.34), (0.0, -0.34, -0.94), pole=(-1.4, 0, -1),
             front=(0, 0.6, 0.8))
POSES["sleep"] = {
    "Torso": (Z3, (0, 0, LIE_DROP)),
    "Head": ((2, -9, 12), (-0.05, 0.0, -0.02)), **lids(CLOSED), **brows(4),
    "EarL": ((0, 14, 0), Z3), "EarR": ((0, -8, 0), Z3),
    "NemesL": ((-22, -6, 0), Z3), "NemesR": ((4, 30, 0), (-0.56, 0, 0.2)),
    **fleg("L", yawed(LIE_F[0], 14), yawed(LIE_F[1], 14), yawed(LIE_F[2], 14)), **PROP,
    **bleg("L", *LIE_B), **bleg("R", *LIE_B),
    **tail(*LIE_TAIL),
}
# как в референсе владельца: лежит щекой на лапе, глаза лениво приоткрыты (для сравнения; в игре — сон и alert)
POSES["lazy"] = {**POSES["sleep"], **lids(HALF), **brows(-2, 0.02, 6, 0.06)}
# проснулся лёжа: голова поднята, ленивый взгляд, бровь задрана, обе лапы вытянуты вперёд (поза сфинкса)
POSES["alert"] = {
    "Torso": (Z3, (0, 0, LIE_DROP)),
    "Head": ((-6, 0, 0), (0, 0, -0.1)), **lids(HALF), **brows(-4, 0.0, 6, 0.06),
    "NemesL": ((-16, 8, 0), Z3), "NemesR": ((-16, -8, 0), Z3),
    **legs4(LIE_F, LIE_F, LIE_B, LIE_B),
    **tail(LIE_TAIL[0], LIE_TAIL[1], LIE_TAIL[2], (-64, 0, -130)),
}
# боевая стойка: пригнулся, голова вперёд, хмурые брови, хвост занесён
T_COMBAT = ((5, 0, 0), (0, 0, -0.14))
POSES["combat"] = {
    "Torso": T_COMBAT,
    "Head": ((6, 0, 0), Z3), "Jaw": (X(8), Z3), **lids(SQUINT), **brows(-12, -0.03),
    "EarL": (X(-14), Z3), "EarR": (X(-14), Z3),
    **plant(T_COMBAT),
    **tail(X(-24), X(-44), X(-66), X(-80)),
}


def _merge(base, *groups, **parts):
    out = dict(POSES[base])
    for g in groups:
        out.update(g)
    out.update(parts)
    return out


T_COMBAT2 = ((6, 0, 0), (0, 0, -0.19))
POSES["combat2"] = _merge("combat", plant(T_COMBAT2), tail(X(-18), X(-36), X(-56), X(-68)), Torso=T_COMBAT2,
                          Head=((8, 0, 0), Z3), Jaw=(X(4), Z3), NemesL=(X(-8), Z3), NemesR=(X(-8), Z3))
# «Тяжёлая лапа», замах: привстал, правая лапа высоко над головой
T_PAWUP = ((-8, 0, -4), (0, 0.08, -0.2))
POSES["pawUp"] = _merge("combat", plant(T_PAWUP),
                        fleg("R", (-100, 0, -70), (-150, 0, -70), (-80, 0, -70), off=(-0.5, -0.2, 0.1)),
                        tail(X(-8), X(-16), X(-24), X(-24)),
                        Torso=T_PAWUP, Head=((2, 0, 4), Z3), Jaw=(X(20), Z3),
                        NemesR=((-30, 0, 0), (0.1, 0, 0.34)), **lids(OPEN), **brows(-16, -0.03))
# «Тяжёлая лапа», удар: корпус вперёд-вниз, правая лапа плашмя далеко впереди
T_SLAM = ((13, 0, 4), (0, -0.3, -0.31))
POSES["pawSlam"] = _merge("combat", plant(T_SLAM, FR=(-0.1, -1.3, 0.0), FL=(0.0, -0.1, 0.0)),
                          tail(X(-34), X(-60), X(-90), X(-110)),
                          Torso=T_SLAM, Head=((-6, 0, -4), Z3), Jaw=(X(16), Z3), NemesR=((28, 10, 0), (0, 0, 0.36)),
                          **lids(SQUINT), **brows(-16, -0.03))


def pivot_turn(yaw, pitch=0.0, about=-1.0, off=Z3):
    """Туловище повёрнуто вокруг вертикали, проходящей между передними лапами (y = about): передние лапы остаются
    на месте, таз уходит в сторону. Возвращает (поворот, сдвиг) туловища."""
    lever = Vector((0.0, about - RIG["Torso"][1][1], 0.0))
    shift = lever - Matrix.Rotation(math.radians(yaw), 3, "Z") @ lever
    return ((pitch, 0, yaw), tuple(round(c + o, 4) for c, o in zip(shift, off)))


# «Хвост-кистень»: передние лапы на месте, таз заносит влево на WHIP градусов, хвост по широкой дуге хлещет вперёд
# снаружи от тела — кисть бьёт сбоку от головы; голова смотрит на цель
WHIP = -58
T_WHIP = pivot_turn(WHIP, 3.0, off=(0, 0, -0.3))
POSES["tailWhip"] = _merge(
    "combat",
    plant(T_WHIP, follow={"FL": 0.45, "FR": 0.45, "BL": 1.0, "BR": 1.0}, FL=(0.12, 0, 0, 0, WHIP * 0.3),
          FR=(-0.12, 0, 0, 0, WHIP * 0.3), BL=(0.1, -0.15, 0, 0, WHIP), BR=(-0.1, 0.15, 0, 0, WHIP)),
    tail((-6, 0, -34), (-46, 0, -84), (-90, 0, -120), (-104, 0, -146)),
    Torso=T_WHIP, Head=((0, -6, -WHIP * 0.8), (0, 0, 0.14)), Jaw=(X(6), Z3),
    **lids(SQUINT), NemesL=((-30, -6, 0), (0, 0, 0.25)), NemesR=((0, 10, 0), Z3))
# получил удар: отшатнулся, зажмурился, уши прижаты
T_HIT = ((-9, 0, 0), (0, 0.26, -0.12))
POSES["hit"] = _merge("combat", plant(T_HIT, FL=(0, 0.1, 0.3, -12), FR=(0, 0.16, 0.36, -16)),
                      tail(X(10), X(20), X(20), X(30)), Torso=T_HIT,
                      Head=((-14, 0, 8), Z3), Jaw=(X(12), Z3), EarL=(X(-34), Z3), EarR=(X(-34), Z3),
                      NemesL=((-18, 10, 0), Z3), NemesR=((-18, -10, 0), Z3), **lids(CLOSED), **brows(10, 0.04))
# победа: грудь вперёд, морда вверх, смеётся, хвост машет
T_PROUD = ((-5, 0, 0), (0, 0, -0.12))
POSES["proud"] = _merge("stand", plant(T_PROUD), tail((0, 0, 24), (-10, 0, 34), (-24, 0, 40), (-30, 0, 44)),
                        Torso=T_PROUD, Head=((-16, 0, 6), Z3), Jaw=(X(22), Z3), **lids(SQUINT),
                        **brows(6, 0.05))
POSES["proud2"] = _merge("stand", plant(T_PROUD), tail((0, 0, -24), (-10, 0, -34), (-24, 0, -40), (-30, 0, -44)),
                         Torso=T_PROUD, Head=((-12, 0, -6), Z3), Jaw=(X(8), Z3), **lids(SQUINT),
                         **brows(6, 0.05))
# поражение: распластался, язык наружу, глаза в щёлку
POSES["dizzy"] = _merge("alert", fleg("L", *(yawed(r, 26) for r in LIE_F)), fleg("R", *(yawed(r, -26) for r in LIE_F)),
                        tail((8, 0, 30), (-40, 0, 62), (-92, 0, 84), (-98, 0, 100)),
                        Head=((8, 6, 12), (0, -0.1, 0.0)), Jaw=(X(18), Z3), EarL=((0, 22, 0), Z3),
                        EarR=((0, -22, 0), Z3), NemesL=((-32, -8, 0), (0, 0, 0.3)), NemesR=((-12, 8, 0), Z3),
                        **lids(SQUINT, CLOSED), **brows(12, 0.02))
# шаг: диагональные пары — одна пара стоит впереди, другая сзади и приподнята, пальцами вниз
STEP, LIFT = 0.3, 0.3
T_WALKA, T_WALKB = ((0, 0, 2), (0, 0, -0.14)), ((0, 0, -2), (0, 0, -0.14))
POSES["walkA"] = _merge("stand", plant(T_WALKA, FL=(0, -STEP, 0), BR=(0, -STEP, 0), FR=(0, STEP, LIFT, 14),
                                       BL=(0, STEP, LIFT, 14)),
                        tail(X(-6), X(-10), (-14, 0, 14), (-14, 0, 22)), Torso=T_WALKA, Head=((2, 0, -3), Z3))
POSES["walkB"] = _merge("stand", plant(T_WALKB, FR=(0, -STEP, 0), BL=(0, -STEP, 0), FL=(0, STEP, LIFT, 14),
                                       BR=(0, STEP, LIFT, 14)),
                        tail(X(-6), X(-10), (-14, 0, -14), (-14, 0, -22)), Torso=T_WALKB, Head=((2, 0, 3), Z3))

# Позы в игре называются, как у пса (Shared/BossAnim): bite — основной выпад («Тяжёлая лапа»), swipe — каждый третий
# («Хвост-кистень»), bark и bark2 — победа. Какая из двух поз лапы пойдёт в bite — решается на этапе анимаций.
EXPORT = {"sleep": "sleep", "alert": "alert", "stand": "stand", "combat": "combat", "combat2": "combat2",
          "walkA": "walkA", "walkB": "walkB", "hit": "hit", "dizzy": "dizzy", "bite": "pawSlam", "swipe": "tailWhip",
          "bark": "proud", "bark2": "proud2"}
# Переходы игры между экспортными позами (BossAnim.Sample): проверяются промежуточные кадры.
TRANSITIONS = (("sleep", "alert"), ("alert", "stand"), ("stand", "combat"), ("combat", "bite"), ("combat", "swipe"),
               ("combat", "hit"), ("combat", "bark"), ("hit", "dizzy"), ("dizzy", "stand"), ("walkA", "walkB"),
               ("stand", "alert"), ("alert", "sleep"))


def pose_tr(pose):
    """Поза → часть: (кватернион поворота, сдвиг) относительно покоя — то же, что Transform сустава в игре."""
    out = {}
    for n in RIG:
        r, off = pose.get(n, (Z3, Z3))
        out[n] = (Euler([math.radians(d) for d in r], "XYZ").to_quaternion(), Vector(off))
    return out


def blend_tr(a, b, alpha):
    """Промежуточный кадр, как в игре (BossAnim: CFrame:Lerp каждого сустава): поворот — по кратчайшей дуге."""
    return {n: (a[n][0].slerp(b[n][0], alpha), a[n][1].lerp(b[n][1], alpha)) for n in RIG}


def tr_matrices(tr):
    """Мировые матрицы частей (в стадах) по поворотам и сдвигам суставов."""
    out = {}

    def world(name):
        if name in out:
            return out[name]
        parent, pivot = RIG[name]
        q, off = tr[name]
        local = Vector(pivot) - (Vector(RIG[parent][1]) if parent else Vector())
        m = Matrix.Translation((local + off) * SCALE) @ q.to_matrix().to_4x4()
        out[name] = (world(parent) @ m) if parent else m
        return out[name]

    for name in RIG:
        world(name)
    return out


def pose_matrices(pose):
    """Мировые матрицы частей в позе (в стадах)."""
    return tr_matrices(pose_tr(pose))


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ── Проверки поз: пересечения частей, опора на землю, переходы ───────────────────────────────────────────────


def collect(arts):
    """Выпуклые тела и точки (вершины, середины рёбер, точки граней) каждой части в координатах модели — до сборки
    меша (сборка освобождает детали)."""
    solids, points = {}, {}
    for art in arts:
        for bm, _, solid, group in art.parts:
            p = points.setdefault(group, [])
            p.extend(tuple(v.co) for v in bm.verts)
            p.extend(tuple((e.verts[0].co + e.verts[1].co) / 2) for e in bm.edges)
            for f in bm.faces:
                c = f.calc_center_median()
                p.append(tuple(c))
                p.extend(tuple((c + v.co) / 2) for v in f.verts)
            if solid is not None:
                co = np.array([tuple(v.co) for v in bm.verts])
                solids.setdefault(group, []).append((
                    np.array(solid.inv), np.array([tuple(n) for n, _ in solid.planes]),
                    np.array([d for _, d in solid.planes]), 1.0 / solid.inv.to_scale()[0],
                    co.min(axis=0) - 0.01, co.max(axis=0) + 0.01))
    return solids, {g: np.array(p) for g, p in points.items()}


def world_points(mats):
    out = {}
    for g, p in POINTS.items():
        m = np.array(mats[g])
        out[g] = ((p - np.array(RIG[g][1])) * SCALE) @ m[:3, :3].T + m[:3, 3]
    return out


def clash(mats):
    """Пара частей → наибольшая глубина в стадах, на которую точки одной части заходят внутрь тел другой."""
    world = world_points(mats)
    out = {}
    for b, sols in SOLIDS.items():
        mb = np.array(mats[b].inverted())
        pivot = np.array(RIG[b][1])
        for a, w in world.items():
            if a == b:
                continue
            q = (w @ mb[:3, :3].T + mb[:3, 3]) / SCALE + pivot
            best = 0.0
            for inv, n, d, scale, lo, hi in sols:
                mask = np.all((q >= lo) & (q <= hi), axis=1)
                if mask.any():
                    ql = q[mask] @ inv[:3, :3].T + inv[:3, 3]
                    best = max(best, float((d[None, :] - ql @ n.T).min(axis=1).max()) * scale)
            if best > 1e-4:
                key = "+".join(sorted((a, b)))
                out[key] = max(out.get(key, 0.0), round(best * SCALE, 2))
    return out


def joined(pair):
    """Части пары соединены суставом (у сустава они заходят друг в друга по построению)."""
    a, b = pair.split("+")
    return RIG[a][0] == b or RIG[b][0] == a


PAWS = ("FPawL", "FPawR", "BPawL", "BPawR")
CLASH_STEP = 0.3  # стады: меньшую разницу со стойкой не считаем пересечением


def new_clashes(mats):
    """Пересечения сверх стойки: пара → (глубина в позе, глубина в стойке)."""
    now = clash(mats)
    return {k: (v, BASE.get(k, 0.0)) for k, v in sorted(now.items(), key=lambda kv: -kv[1])
            if v - BASE.get(k, 0.0) >= CLASH_STEP}


def check_poses():
    """Все позы: пересечения сверх стойки и высота каждой лапы над землёй; переходы игры — худшие кадры."""
    out = {"poses": {}, "transitions": {}}
    lows = {}
    for name, source in list(EXPORT.items()) + [("pawUp", "pawUp"), ("lazy", "lazy")]:
        mats = pose_matrices(POSES[source])
        world = world_points(mats)
        low = min(float(w[:, 2].min()) for w in world.values())
        lows[name] = low
        out["poses"][name] = {
            "source": source,
            "clash": {k: v for k, v in new_clashes(mats).items()},
            "paws_above_ground": {p: round(float(world[p][:, 2].min()) - low, 2) for p in PAWS},
            "size": [round(float(max(w[:, i].max() for w in world.values()) - min(w[:, i].min() for w in world.values())), 2)
                     for i in range(3)],
        }
    for a, b in TRANSITIONS:
        ta, tb = pose_tr(POSES[EXPORT[a]]), pose_tr(POSES[EXPORT[b]])
        worst, sink, lift, sink_at = {}, 0.0, 0.0, ""
        for k in range(1, 10):
            s = smooth(k / 10)
            mats = tr_matrices(blend_tr(ta, tb, s))
            for pair, (v, base) in new_clashes(mats).items():
                if v > worst.get(pair, (0.0, 0.0, 0))[0]:
                    worst[pair] = (v, base, k * 10)
            # в игре высота туловища — та же интерполяция между высотами двух поз
            part_low = {g: float(w[:, 2].min()) for g, w in world_points(mats).items()}
            who = min(part_low, key=part_low.get)
            err = part_low[who] - (lows[a] + (lows[b] - lows[a]) * s)
            if err < sink:
                sink, sink_at = err, f"{who} на {k * 10}%"
            lift = max(lift, err)
        out["transitions"][f"{a}>{b}"] = {"clash": worst, "sinks": round(-sink, 2), "floats": round(lift, 2),
                                          "sinks_at": sink_at if sink < -0.005 else ""}
    return out


SOLIDS, POINTS, BASE = {}, {}, {}


def init_checks():
    """Собрать детали (без меша) и подготовить проверки пересечений; возвращает сборки трёх карт."""
    global SOLIDS, POINTS, BASE
    arts = [sphinx_head(), sphinx_body(), sphinx_limbs()]
    SOLIDS, POINTS = collect(arts)
    BASE = clash(pose_matrices(POSES["stand"]))
    return arts


def apply_mats(parts, mats, place=Matrix.Identity(4), low=None):
    """Расставить части по матрицам; low — высота нижней точки (None — поставить на землю)."""
    if low is None:
        low = min((mats[n] @ OBJ_SCALE @ v.co).z for n, o in parts.items() for v in o.data.vertices)
    ground = Matrix.Translation((0, 0, -low))
    for n, o in parts.items():
        o.matrix_world = place @ ground @ mats[n] @ OBJ_SCALE
    return low


def apply_pose(parts, pose, place=Matrix.Identity(4)):
    return apply_mats(parts, pose_matrices(POSES[pose]), place)


if DIRECT:
    # ── Сборка ───────────────────────────────────────────────────────────────────────────────────────────────────

    os.makedirs(PREVIEWS, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    collection = bpy.data.collections.new("Boss4")
    bpy.context.scene.collection.children.link(collection)

    arts = init_checks()
    report = {"scale": SCALE, "head_scale": HEAD_SCALE, "checks": check_poses()}
    for name, data in report["checks"]["poses"].items():
        print("CHECK_POSE", name, json.dumps(data, ensure_ascii=False))
    for name, data in report["checks"]["transitions"].items():
        print("CHECK_TRANS", name, json.dumps(data, ensure_ascii=False))
    PROBE = os.environ.get("SPHINX_PROBE")
    if PROBE:  # отладка позы: где оказались ключевые точки (единицы модели, высота — над землёй)
        for pose in PROBE.split(","):
            mats = pose_matrices(POSES[pose])
            low = min(float(w[:, 2].min()) for w in world_points(mats).values())

            def at(part, point):
                v = mats[part] @ ((Vector(point) - Vector(RIG[part][1])) * SCALE)
                return [round(c, 2) for c in (v.x / SCALE, v.y / SCALE, (v.z - low) / SCALE)]

            for label, part, point in (
                    ("neck", "Head", RIG["Head"][1]), ("cheekR front-low", "Head", hp(-1.14, -3.18, 2.78)),
                    ("cheekR back-low", "Head", hp(-1.14, -2.25, 2.78)), ("cheekR mid side", "Head", hp(-1.14, -2.7, 3.1)),
                    ("jaw low", "Head", hp(0.0, -3.3, 2.72)), ("muzzle front", "Head", hp(0.0, -3.5, 3.2)),
                    ("nemesR low-front", "NemesR", hp(-1.5, -2.98, 2.18)), ("pendantR", "NemesR", hp(-1.6, -2.85, 1.56)),
                    ("shoulderR", "FUpperR", RIG["FUpperR"][1]), ("elbowR", "FLowerR", RIG["FLowerR"][1]),
                    ("wristR", "FPawR", RIG["FPawR"][1]), ("pawR toes", "FPawR", (-FX, -2.32, 0.3)),
                    ("pawR heel", "FPawR", (-FX, -0.5, 0.25)), ("pawR sole mid", "FPawR", (-FX, -1.2, 0.0)),
                    ("pawR top mid", "FPawR", (-FX, -1.6, 0.5)),
                    ("elbowL", "FLowerL", RIG["FLowerL"][1]), ("wristL", "FPawL", RIG["FPawL"][1]),
                    ("pawL toes", "FPawL", (FX, -2.32, 0.3)), ("chest low", "Torso", bp(0.0, -1.0, 0.8)),
                    ("tail tip", "Tassel", bp(0.0, 3.92, 5.18)), ("tassel mid", "Tassel", bp(0.0, 3.92, 4.4)),
                    ("tail base", "Tail1", RIG["Tail1"][1])):
                print("PROBE", pose, label, at(part, point))
            lows = {g: round((float(w[:, 2].min()) - low) / SCALE, 2) for g, w in world_points(mats).items()}
            print("PROBE", pose, "lows", json.dumps(lows))
    if MODE == "check":
        total = 0
        for art in arts:
            art.build(collection)
            total += art.stats["tris"]
            print("CHECK", art.name, json.dumps(art.stats, ensure_ascii=False))
        print("CHECK_TOTAL", total)
        sys.exit(0)

    AX = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))  # оси Roblox: (x, y, z) Blender → (x, z, −y) Roblox


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


    def write_rig_json(path, parts):
        """Скелет в осях Roblox (стады, лицо в +Z модели): части, точки вращения, габариты мешей от точки вращения и
        позы (часть → {x, y, z, r00…r22} — Transform сустава относительно покоя; у Torso — вместе с подъёмом к земле)."""
        out = {"scale": SCALE, "order": list(RIG), "parts": {}, "poses": {}, "heights": {}}
        for n, (parent, pivot) in RIG.items():
            co = [AX @ v.co for v in parts[n].data.vertices]
            lo = Vector([min(c[i] for c in co) for i in range(3)])
            hi = Vector([max(c[i] for c in co) for i in range(3)])
            out["parts"][n] = {"parent": parent, "pivot": [round(c, 4) for c in AX @ (Vector(pivot) * SCALE)],
                               "center": [round(c, 4) for c in (lo + hi) / 2], "size": [round(c, 4) for c in hi - lo],
                               "map": MAP_OF[n]}
        for name, source in EXPORT.items():
            pose = POSES[source]
            mats = pose_matrices(pose)
            low = min((mats[n] @ v.co).z for n, o in parts.items() for v in o.data.vertices)
            high = max((mats[n] @ v.co).z for n, o in parts.items() for v in o.data.vertices)
            out["heights"][name] = round(high - low, 2)
            out["poses"][name] = {}
            for n in RIG:
                r, off = pose.get(n, (Z3, Z3))
                m3 = AX @ Euler([math.radians(d) for d in r], "XYZ").to_matrix() @ AX.transposed()
                t = AX @ (Vector(off) * SCALE)
                if n == "Torso":
                    t.y -= low
                out["poses"][name][n] = [round(x, 4) for x in [t.x, t.y, t.z] + [m3[i][j] for i in range(3) for j in range(3)]]
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("RIG_OK", path, len(EXPORT), "поз", json.dumps(out["heights"]))


    parts = part_objects(bake=(MODE == ""))
    if MODE == "":
        S.export_fbx([parts[n] for n in RIG], os.path.join(REPO, "assets", "models", "Boss4_Sphinx.fbx"))
        write_rig_json(os.path.join(REPO, "assets", "models", "Boss4_Sphinx.rig.json"), parts)
    apply_pose(parts, "stand")
    report["size_studs"] = [round(max((o.matrix_world @ v.co)[i] for o in parts.values() for v in o.data.vertices)
                                  - min((o.matrix_world @ v.co)[i] for o in parts.values() for v in o.data.vertices), 2)
                            for i in range(3)]

    # ── Проверочные рендеры ──────────────────────────────────────────────────────────────────────────────────────

    prev = S.Preview(collection)
    floor = bpy.data.objects["Floor"]
    floor.scale = (1.4, 3.6, 3.6)
    floor.location.y = 14
    for i, (light, loc) in enumerate(prev.lights):
        light.data.energy *= 14
        light.data.size *= 3.6
        prev.lights[i] = (light, loc * 3.8)
    prev.aim_lights(Vector((0, 0, 0)))


    def turn(deg):
        return Matrix.Rotation(math.radians(deg), 4, "Z")


    EYE, LOOK = (0, -46, 12.0), 6.8
    SHOTS = os.environ.get("SPHINX_SHOTS", "all")
    TURNS = (("front", 0), ("34", -38), ("side", -90), ("back", 180), ("34back", 142))


    def shot(name, pose, deg, eye=EYE, look=LOOK, lens=50, res=(1000, 860)):
        apply_pose(parts, pose, turn(deg))
        return prev.shot(os.path.join(PREVIEWS, name + ".png"), eye, (0, 0, look), lens, res)


    def blend_shot(name, a, b, s, deg, eye=EYE, look=LOOK, lens=50, res=(640, 560)):
        """Промежуточный кадр перехода a → b (доля s уже сглажена); высота туловища — как в игре."""
        mats = tr_matrices(blend_tr(pose_tr(POSES[a]), pose_tr(POSES[b]), s))
        lows = [apply_mats(parts, pose_matrices(POSES[p])) for p in (a, b)]
        apply_mats(parts, mats, turn(deg), lows[0] + (lows[1] - lows[0]) * s)
        return prev.shot(os.path.join(PREVIEWS, name + ".png"), eye, (0, 0, look), lens, res)


    TOP = ((0.0, -3.0, 62.0), 0.0)  # камера сверху: (точка, высота взгляда)

    if SHOTS.startswith("lab:"):
        for pose in SHOTS[4:].split(","):
            tiles = [shot(f"lab_{pose}_{label}", pose, deg, look=5.6, res=(640, 560))
                     for label, deg in (("front", 0), ("34", -38), ("side", -90), ("34r", 38))]
            tiles.append(shot(f"lab_{pose}_top", pose, 0, eye=TOP[0], look=TOP[1], res=(640, 560)))
            S.strip(tiles, os.path.join(PREVIEWS, f"lab_{pose}.png"))
    if SHOTS in ("all", "turns"):
        for pose, look in (("stand", 7.4), ("lazy", 5.2)):
            tiles = [shot(f"sphinx_{pose}_{label}", pose, deg, look=look) for label, deg in TURNS]
            S.strip(tiles[:3], os.path.join(PREVIEWS, f"sphinx_turns_{pose}_1.png"))
            S.strip(tiles[3:], os.path.join(PREVIEWS, f"sphinx_turns_{pose}_2.png"))
        for label, deg in TURNS[:3]:
            shot(f"sphinx_sleep_{label}", "sleep", deg, look=5.2)
    if SHOTS in ("all", "poses"):
        tiles = [shot(f"sphinx_pose_{pose}", pose, -38, look=6.0, res=(760, 760))
                 for pose in ("sleep", "alert", "stand", "combat", "combat2", "pawUp", "pawSlam", "tailWhip", "hit", "proud",
                              "proud2", "dizzy", "walkA", "walkB")]
        for k in range(0, len(tiles), 4):
            S.strip(tiles[k:k + 4], os.path.join(PREVIEWS, f"sphinx_poses_{k // 4 + 1}.png"))
    if SHOTS in ("all", "trans"):
        # переходы сон → пробуждение → стойка и удар хвостом: промежуточные кадры тем же смешиванием, что в игре
        for a, b, look in (("sleep", "alert", 5.4), ("alert", "stand", 6.4)):
            for k in range(6):
                blend_shot(f"sphinx_trans_{a}_{b}_{k}", a, b, smooth(k / 5), -38, look=look)
        for k in range(4):
            s = smooth(k / 3)
            blend_shot(f"sphinx_whip_34_{k}", "combat", "tailWhip", s, -38, look=6.0)
            blend_shot(f"sphinx_whip_top_{k}", "combat", "tailWhip", s, 0, eye=TOP[0], look=TOP[1])
            blend_shot(f"sphinx_whip_front_{k}", "combat", "tailWhip", s, 0, look=6.0)
    if SHOTS in ("all", "hero"):
        # как в референсе: лежит, камера слева-спереди чуть сверху
        shot("sphinx_hero_lazy", "lazy", -36, eye=(0, -40, 8.5), look=5.6, res=(1536, 1024))
        shot("sphinx_hero_sleep", "sleep", -36, eye=(0, -40, 8.5), look=5.6, res=(1536, 1024))
        shot("sphinx_hero_stand", "stand", -36, eye=(0, -46, 11.0), look=7.6, res=(1536, 1024))
        apply_pose(parts, "stand")
        for name, eye, target, lens in (("sphinx_face", (-8.5, -32.5, 13.6), (0.0, -6.5, 11.5), 58),
                                        ("sphinx_top", (9.0, -22.0, 34.0), (0.0, 0.5, 6.0), 50)):
            prev.shot(os.path.join(PREVIEWS, name + ".png"), eye, target, lens, (1200, 1000))
    if SHOTS in ("all", "game"):
        # камера Roblox: игрок (манекен 5.2 стада) в 24 стадах перед боссом, камера за его спиной, угол обзора 70°
        apply_pose(parts, "stand", turn(-18))
        S.mannequin(collection, 3.0, y=-24.0)
        for name, eye, res in (("sphinx_game_pc", (5.0, -43.0, 13.0), (1280, 720)),
                               ("sphinx_game_phone", (5.0, -47.0, 14.0), (844, 390))):
            prev.shot(os.path.join(PREVIEWS, name + ".png"), eye, (0, 0, 6.0), 20.0, res)
        apply_pose(parts, "sleep", turn(-18))
        prev.shot(os.path.join(PREVIEWS, "sphinx_game_sleep.png"), (5.0, -43.0, 13.0), (0, 0, 4.0), 20.0, (1280, 720))

    if MODE == "":
        apply_pose(parts, "stand")
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(REPO, "assets", "models", "Boss4_Sphinx.blend"))

    with open(os.path.join(PREVIEWS, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("SPHINX_OK " + json.dumps({k: v for k, v in report.items() if k != "checks"}, ensure_ascii=False))
