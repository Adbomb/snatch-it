"""Коллекция джунглей босса 6 — Legendary (каталог docs/BOSS6_CATALOG.md, утверждён 2026-11-25).
Каждое существо — функция, возвращающая Art с подвижными частями (part), позой и кадрами; список ITEMS — в порядке
каталога. Признаки вида, эмоция и цвета — из каталога; правила анатомии D64 — в jungle/kit.py и anatomy_kit.
"""

import math
import os
import sys

from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jungle_kit import *  # noqa: E402,F401,F403


def sprout_flytrap():
    """10. Росток-мухоловка: мини-копия мамы-королевы — вырос из клубня посреди розетки листьев-ловушек, раскинул
    руки-лозы: «та-дам!». Голова — ловушка мухоловки: две короткие округлые створки на петле (снаружи тёмно-зелёные,
    внутри малиновые, язык, короткие тупые светлые реснички), глаза-бугорки на верхней створке; за головой — розовый
    венчик, как у мамы; золотая корона набекрень со светящимся малиновым самоцветом, на стебле — светящийся амулет.
    Самый крупный в коллекции.
    Признаки мухоловки: створки-ловушка с ресничками, малиновое нутро, толстый тёмный стебель, розетка листьев-ловушек
    на земле, клубень с корешками."""
    a = new("SproutFlytrap", {"trap": ("1F6634", True), "trapD": ("174A27", False), "faceL": ("C2F29A", False),
                              "maw": ("FF4F80", False), "mawD": ("C8285E", False), "cilia": ("C8F59A", False),
                              "stem": ("3B5A2B", True), "stemD": ("243D1E", False), "leafL": ("8FD957", True),
                              "leafV": ("4E9A3A", False), "vine": ("BDEB6E", True), "root": ("8F5A31", True),
                              "rootD": ("6B4224", False), "petal": ("FF8FC0", True), "petalD": ("E0569A", False),
                              "goldC": ("F5B21C", False), "goldCD": ("C27E0E", False), "halo": ("FFB8DA", False),
                              "neonGem": ("FF1A7A", False)})
    glow(a)
    t = legendary_stand(a, 1.75)
    part(a, "Body", "Stand", (0, 0, t + 0.4))
    # клубень: широкий, приплюснутый, стоит на подставке; короткие корешки-ступни прямо под ним
    A.body(a, "root", (0, 0.02, t), 0.74, 0.7, 0.56, "dome", n=3)
    for k in range(5):
        ang = math.radians(270 + 72 * k)
        dv = V((math.cos(ang), math.sin(ang), 0))
        spike(a, "rootD", V((0, 0.02, t + 0.14)) + dv * 0.55, V((0, 0.02, t + 0.07)) + dv * 0.92, 0.16)
    # розетка из пяти светлых листьев-ловушек на земле вокруг клубня (как у мамы), спереди — проход к амулету
    for k in range(5):
        ang = math.radians(306 + 72 * k)
        dv = V((math.cos(ang), math.sin(ang), 0))
        root, tip = V((0, 0, t + 0.24)) + dv * 0.4, V((0, 0, t + 0.14)) + dv * 1.26
        flat_leaf(a, "leafL", "leafV", root, tip, 0.76, 0.1, (0, 0, 1))
        x = dv
        y = V((0, 0, 1)).cross(x)
        mt = Matrix(((x.x, y.x, 0, tip.x - x.x * 0.08), (x.y, y.y, 0, tip.y - x.y * 0.08), (0, 0, 1, tip.z + 0.03),
                     (0, 0, 0, 1)))
        for sd in S2:
            trap_lobe(a, mt, sd, 0.56, 0.27 - 0.01 * (k % 2), 0.07)
    # стебель-ствол: толстый, тёмный, с узлом; на нём амулет со светящимся камнем в светлой кайме
    kchain(a, "stem", [(0, 0, t + 0.3), (0, -0.03, t + 1.2), (0, 0.03, t + 2.0)], [0.68, 0.6, 0.5], up=(0, -1, 0))
    a.prism("stemD", S.octagon(-0.37, 0.37, -0.38, 0.34, 0.11), t + 1.5, t + 1.6, bevel=0)  # узел стебля
    a.prism("goldC", S.octagon(-0.2, 0.2, t + 0.84, t + 1.22, 0.08), -0.44, -0.26, axis="y")  # амулет
    a.prism("goldCD", S.octagon(-0.23, 0.23, t + 1.22, t + 1.3, 0.03), -0.38, -0.22, axis="y", bevel=0)  # петелька
    a.prism("halo", S.octagon(-0.15, 0.15, t + 0.88, t + 1.18, 0.06), -0.48, -0.4, axis="y", bevel=0)  # ореол
    a.prism("neonGem", S.octagon(-0.1, 0.1, t + 0.93, t + 1.13, 0.045), -0.53, -0.44, axis="y", bevel=0)
    for s, nm in ((1, "ArmL"), (-1, "ArmR")):  # руки-лозы светлые на тёмном стебле, раскинуты: «та-дам!»
        part(a, nm, "Body", (s * 0.12, -0.02, t + 1.62))
        leaf_blade(a, "vine", "leafV", [(s * 0.1, -0.02, t + 1.62), (s * 0.55, -0.12, t + 1.66),
                                         (s * 1.0, -0.2, t + 1.8), (s * 1.36, -0.26, t + 2.02)],
                   [0.18, 0.44, 0.46, 0.12], 0.08, up=(0, -1, 0.25))
    # голова-ловушка: петля сзади, верхняя створка приоткрыта вверх, нижняя — вниз
    part(a, "Head", "Body", (0, 0.02, t + 2.05))
    hg = V((0, 0.22, t + 2.3))
    R = 0.72
    mu = Matrix.Translation(hg) @ Matrix.Rotation(math.radians(-20), 4, "X")
    kchain(a, "stem", [(0, 0.0, t + 1.95), (0, 0.18, t + 2.26)], [0.4, 0.3], up=(0, -1, 0))  # шея к петле
    A.ball(a, "trapD", tuple(hg), 0.26, n=3)  # петля
    lay = [(0.3, 1, 1), (0.48, 0.9, 0.85), (0.62, 0.72, 0.62)]
    valve(a, True, mu, R, 0.86, lay)
    for s in S2:  # глаза-бугорки на макушке верхней створки (светлое лицо), видны над её краем
        bc = mu @ V((s * 0.35, -0.98, 0.6))
        A.ball(a, "faceL", tuple(bc), 0.25, n=3)
        eye2(a, tuple(bc + V((s * 0.02, -0.22, 0.05))), 0.15, (s * 0.25, -1, 0.12), "proud", s, "faceL", "trapD")
    # корона набекрень между глазами: обод, пять зубцов, самоцвет спереди (в светлой кайме) и сверху светятся
    mc = mu @ Matrix.Translation((0.04, -0.9, 0.78)) @ Matrix.Rotation(math.radians(22), 4, "X") @ Matrix.Rotation(
        math.radians(-14), 4, "Y")  # корона лежит на глазах-бугорках
    a.prism("goldC", S.octagon(-0.28, 0.28, -0.26, 0.26, 0.09), 0.0, 0.26, matrix=mc)
    a.frame("goldCD", S.octagon(-0.3, 0.3, -0.28, 0.28, 0.1), 0.06, -0.01, 0.08, axis="z", bevel=0, matrix=mc)
    for i in range(5):
        th = 2 * math.pi * i / 5 - math.pi / 2
        px, py = 0.22 * math.cos(th), 0.2 * math.sin(th)
        a.frustum("goldC", (px - 0.085, px + 0.085, py - 0.065, py + 0.065), (px, px, py, py), 0.24, 0.66, bevel=0,
                  matrix=mc)
    a.prism("halo", S.octagon(-0.16, 0.16, 0.0, 0.26, 0.06), -0.3, -0.2, axis="y", bevel=0, matrix=mc)  # ореол
    a.prism("neonGem", S.octagon(-0.12, 0.12, 0.02, 0.24, 0.045), -0.35, -0.24, axis="y", bevel=0, matrix=mc)
    gem(a, "neonGem", tuple(mc @ V((0, 0, 0.38))), 0.22, turn=20)
    # розовый венчик за головой, как у мамы: диск-чашечка и плоские лепестки по кругу (снизу — стебель)
    pc = V((0, 0.36, t + 2.56))
    a.prism("petalD", S.octagon(-0.6, 0.6, pc.z - 0.6, pc.z + 0.6, 0.22), 0.3, 0.42, axis="y", bevel=0)
    n = 11
    for i in range(n):
        ang = -90 + 360 * (i + 0.5) / n
        if abs(ang + 90) < 50:
            continue
        dd = V((math.cos(math.radians(ang)), 0, math.sin(math.radians(ang))))
        pp = V((-dd.z, 0, dd.x))
        poly = [pc + dd * r + pp * w for r, w in ((0.45, -0.13), (1.0, -0.26), (1.44, -0.13), (1.44, 0.13),
                                                  (1.0, 0.26), (0.45, 0.13))]
        y0 = 0.32 + 0.014 * (i % 3)  # соседние лепестки на разной глубине — грани не совпадают
        a.extrude("petal" if i % 2 else "petalD", [(q.x, q.z) for q in poly], y0, y0 + 0.08, axis="y")
    # нижняя створка — челюсть: язык, раскрывается в позе
    part(a, "Jaw", "Head", tuple(hg))
    ml = Matrix.Translation(hg) @ Matrix.Rotation(math.radians(16), 4, "X")
    valve(a, False, ml, R, 0.7, lay)
    taper(a, "tongue", ml @ V((0, -0.3, 0.03)), ml @ V((0, -1.15, 0.08)), 0.36, 0.3, 0.1, 0.09, cut=0.3)
    face_point(a, tuple(mu @ V((0, -1.0, 0.3))))
    tg = mu @ V((0, -0.95, 0.12))
    FACE_CAM["SproutFlytrap"] = (tuple(tg + V((-1.5, -6.6, 1.2))), tuple(tg))
    closeup(a, (0.0, -0.5, t + 0.3), eye_off=(-0.9, -2.2, 0.9))
    a.pose = {"Jaw": ((18, 0, 0), (0, 0, 0)), "Head": ((-8, 0, 6), (0, 0, 0)), "ArmL": ((0, -18, 0), (0, 0, 0)),
              "ArmR": ((0, 14, 0), (0, 0, 0))}
    return a


_OWN = [("SproutFlytrap", sprout_flytrap, "Росток-мухоловка", "Legendary")]

# порядок каталога; новые существа — по модулю на существо (jungle/<snake_case>.py с ITEM), см. jungle_kit.collect
ORDER = "SproutFlytrap ParadiseDancer LightningEel".split()
ITEMS = collect(ORDER, _OWN)
