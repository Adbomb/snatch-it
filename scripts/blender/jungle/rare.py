"""Коллекция джунглей босса 6 — Rare (каталог docs/BOSS6_CATALOG.md, утверждён 2026-11-25).
Каждое существо — функция, возвращающая Art с подвижными частями (part), позой и кадрами; список ITEMS — в порядке
каталога. Признаки вида, эмоция и цвета — из каталога; правила анатомии D64 — в jungle/kit.py и anatomy_kit.
"""

import math
import os
import sys

from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jungle_kit import *  # noqa: E402,F401,F403


def many_eye_caterpillar():
    """5. Гусеница-многоглазка: пугает птиц ложными глазками — на каждом сегменте по круглому «глазу», а настоящее
    лицо одно, на голове, и очень довольно своей хитростью. Ползёт боком к игроку, тело изогнуто волной.
    Признаки: «осиная» жёлто-чёрная окраска (широкий чёрный пояс на каждом сегменте), ложные глазки (чёрный круг
    в белом кольце, без зрачка и бровей), короткие толстые ложноножки под каждым сегментом, щетинки на спине, жёлтая
    голова с чёрной маской-повязкой на уровне глаз и рожками-бугорками."""
    a = new("ManyEyeCaterpillar", {"cat": ("FFD21C", True), "catD": ("2B2B36", False), "catO": ("FF8A1F", True),
                                   "catL": ("FFE36A", False), "pad": ("FF9A3D", False), "ocW": ("FFF8E0", False)})
    t = rare_stand(a, 1.6)
    lifts = (0.0, 0.15, 0.34, 0.24, 0.06, 0.1)  # волна: горб посередине
    xs = [1.12 - 0.38 * k for k in range(6)]
    segs = [(xs[k], t + 0.3 + 0.01 * k + lifts[k], 0.3 + 0.01 * k) for k in range(6)]  # (x, z центра, радиус)
    seg_tiers = []
    for k, (x, zc, r) in enumerate(segs):
        nm = "Body" if k == 0 else f"Seg{k}"
        part(a, nm, "Stand" if k == 0 else ("Body" if k == 1 else f"Seg{k - 1}"), (x + 0.19, 0, zc))
        tiers = A.body(a, "cat", (x, 0, zc - r), r, r * 0.95, 2 * r, "ball", n=3, t0=0.1, t1=0.9, floor=0.35)  # бочонок
        seg_tiers.append(tiers)
        # ложный глазок на боку к игроку и на спине-боку сзади: чёрный восьмиугольник в белом кольце на среднем
        # (самом широком) ярусе; без зрачка-взгляда и бровей — пятно, а не лицо
        wy = tiers[1][5]
        for sy in (-1, 1):
            a.prism("ocW", S.octagon(x - 0.105, x + 0.105, zc - 0.105, zc + 0.105, 0.04), sy * (wy - 0.06),
                    sy * (wy + 0.022), axis="y", bevel=0)
            a.prism("catD", S.octagon(x - 0.06, x + 0.06, zc - 0.06, zc + 0.06, 0.023), sy * (wy - 0.04),
                    sy * (wy + 0.045), axis="y", bevel=0)
        # щетинки на спине — короткие тупые, как у гусениц; основание в верхнем ярусе (верх сегмента — zc + 0.8·r),
        # без перекладины между ними: сверху она с поясом складывалась в рамку
        for e in S2:
            blunt(a, "catD", (x + e * 0.07, 0.06, zc + r * 0.7), (x + e * 0.1 + 0.04, 0.16, zc + r + 0.17), 0.08, 0.04)
        # короткие толстые ложноножки-обрубки под сегментом, подушечка снизу
        for e in S2:
            K.KEY = "catD"
            K.taper(a, (x, e * 0.15, zc - r * 0.55), (x - 0.02, e * 0.17, t + 0.07), 0.15, 0.13, 0.13, 0.12, cut=0.3)
            a.box("pad", x - 0.1, x + 0.06, e * 0.17 - 0.08, e * 0.17 + 0.08, t + 0.005 + 0.004 * k, t + 0.08,
                  bevel=0)
        # чёрный пояс-кольцо («осиная» окраска) на хвостовом краю своего сегмента, за ложным глазком: контур —
        # сечение только этого сегмента (ступени ярусов), выступ 0.04 — пояс лежит на своём сегменте и нигде не
        # поднимается над соседом рамкой; где сосед выше, пояс уходит в него
        belt(a, "catD", x + 0.16, (tiers,), 0.05, 0.04)
    # голова: круглая, повёрнута к игроку на 30°; жёлтая с чёрной маской (ярус глаз), рожки-бугорки
    # оранжевые, жвалы; единственное лицо — хитрое и довольное (глаза с прищуром, ухмылка)
    x, zc, r = segs[-1]
    hc = V((x - 0.42, -0.04, zc + 0.24))
    part(a, "Head", "Seg5", (x - 0.2, 0, zc + 0.1))
    hm = Matrix.Translation(hc) @ Matrix.Rotation(math.radians(-30), 4, "Z")
    with_matrix(a, hm)
    # 6 ярусов — голова круглая, без «цилиндра» сверху; два яруса на уровне глаз — чёрная маска-повязка вокруг
    # головы, веки цвета маски (прищур), бровей нет — эмоцию держат веки и ухмылка
    A.body(a, "cat", (0, 0, -0.4), 0.41, 0.39, 0.8, "ball", n=6, t0=0.1, t1=0.86, floor=0.42, corner=0.48,
           keys=["cat", "cat", "catD", "catD", "cat", "cat"])  # профиль срезан сверху: макушка широкая, без «шапки»
    for e in S2:
        eye2(a, (e * 0.16, -0.37, 0.02), 0.11, (e * 0.15, -1, 0.05), "sly", e, "catD", "catD", show_brow=False,
             lid=0.34, lid_tilt=12)  # веки прищурены, внутренние концы ниже — хитрый взгляд
        blunt(a, "catO", (e * 0.17, 0.02, 0.33), (e * 0.24, 0.04, 0.52), 0.13, 0.08)  # рожки-бугорки
    grin(a, (0, -0.345, -0.2), 0.24, teeth=0)
    with_matrix(a, None)
    face_point(a, tuple(hm @ V((0, -0.4, 0.0))))
    closeup(a, (0.3, -0.3, t + 0.45), eye_off=(-0.6, -2.4, 0.8))
    a.pose = {"Seg2": ((0, 10, 0), (0, 0, 0)), "Seg3": ((0, -8, 0), (0, 0, 0)), "Head": ((0, 12, -14), (0, 0, 0))}
    return a


def wheel_monkey():
    """6. Обезьяна-колесо: хвост такой длинный, что свернулся в обруч вокруг неё — сидит в нём, как в колесе.
    Признаки: светлая маска-сердечко, большие круглые уши, длинные руки, цепкий хвост, хохолок."""
    a = new("WheelMonkey", {"mon": ("B36B3A", True), "monD": ("7E4626", False), "monL": ("F6D9B0", False),
                            "tuft": ("6A3A1E", False)})
    t = rare_stand(a, 1.6)
    R0, cz = 1.15, t + 1.2  # обруч хвоста
    part(a, "Body", "Stand", (0, 0.05, t + 0.5))
    A.body(a, "mon", (0, 0.1, t + 0.05), 0.45, 0.42, 0.85, "pear", n=4, front=("monL", 0.7, t + 0.15, t + 0.7))
    for s in S2:  # ноги упираются в обод, руки держатся за обод сбоку
        A.limb(a, "mon", [(s * 0.3, -0.1, t + 0.25), (s * 0.5, -0.35, t + 0.25), (s * 0.55, -0.3, t + 0.08)],
               [0.18, 0.16, 0.14])
        nm = "Arm" + ("L" if s > 0 else "R")
        part(a, nm, "Body", (s * 0.2, 0.08, t + 0.75))
        A.ball(a, "mon", (s * 0.26, 0.08, t + 0.76), 0.15, n=3)  # плечо входит в тело
        A.limb(a, "mon", [(s * 0.24, 0.08, t + 0.76), (s * 0.85, -0.1, t + 1.0), (s * 1.05, 0.05, cz + 0.2)],
               [0.17, 0.15, 0.14])
        A.ball(a, "monL", (s * 1.08, 0.05, cz + 0.22), 0.12, n=2)  # ладонь на ободе
    part(a, "Head", "Body", (0, 0.05, t + 0.9))
    hc = V((0, -0.02, t + 1.25))
    A.ball(a, "mon", tuple(hc), 0.4, n=3)
    a.prism("monL", S.octagon(-0.3, 0.3, hc.z - 0.28, hc.z + 0.2, 0.1), -0.42, -0.3, axis="y")  # маска
    for s in S2:
        a.prism("monL", S.octagon(-0.13, 0.13, -0.13, 0.13, 0.04), -0.08, 0.08, axis="x",
                matrix=Matrix.Translation(hc + V((s * 0.44, 0.0, 0.05))))  # ухо
        a.prism("mon", S.octagon(-0.17, 0.17, -0.17, 0.17, 0.05), -0.06, 0.04, axis="x",
                matrix=Matrix.Translation(hc + V((s * 0.49, 0.03, 0.05))))
        eye2(a, tuple(hc + V((s * 0.13, -0.43, 0.06))), 0.09, (0, -1, 0), "goofy", s, "monL", "monD")
    grin(a, tuple(hc + V((0, -0.44, -0.16))), 0.28, teeth=3)
    for k, (dx, dz) in enumerate(((-0.24, 0.5), (0.05, 0.66), (0.26, 0.48))):  # растрёпанный хохолок
        spike(a, "tuft", tuple(hc + V((-0.1 + 0.1 * k, 0.04, 0.34))), tuple(hc + V((dx, 0.12, dz))), 0.13)
    part(a, "Tail", "Body", (0, 0.4, t + 0.25))
    pts = [(0, 0.35, t + 0.25)]
    for k in range(17):  # обруч: почти полный круг вокруг, кончик закручен внутрь
        ang = math.radians(-100 + k * 21)
        pts.append((R0 * math.cos(ang), 0.4 + 0.02 * k, cz + R0 * math.sin(ang)))
    kchain(a, "monD", pts, [0.2] * len(pts), up=(0, 1, 0))
    face_point(a, tuple(hc + V((0, -0.42, 0))))
    closeup(a, (0.0, -0.3, t + 0.5))
    a.pose = {"Tail": ((0, 10, 0), (0, 0, 0)), "Head": ((0, 0, -12), (0, 0, 0))}
    return a


def three_head_parrot():
    """7. Попугай-трёхглав: одно тело и три головы разных цветов — и все три говорят одновременно.
    Признаки: крючковатые клювы, лапы 2+2, яркое оперение, длинный хвост из перьев, хохолки."""
    a = new("ThreeHeadParrot", {"red": ("E8384F", True), "blue": ("2F7BE8", True), "yel": ("FFC21C", True),
                                "green": ("3FC45A", True), "beak": ("2B2B36", False), "face": ("FFFFFF", False)})
    t = rare_stand(a, 1.5)
    for s in S2:
        A.limb(a, "beak", [(s * 0.2, 0.0, t + 0.45), (s * 0.22, -0.05, t + 0.06)], [0.12, 0.1], joints=False)
        for k, dy in enumerate((-0.3, 0.3)):  # пальцы 2 + 2 (вперёд и назад), разной толщины — грани не совпадают
            K.KEY = "beak"
            K.taper(a, (s * 0.22, -0.05, t + 0.05 + 0.006 * k), (s * 0.24, -0.05 + dy, t + 0.04 + 0.006 * k),
                    0.09 - 0.012 * k, 0.06, 0.07 + 0.01 * k, 0.05, cut=0.2)
    part(a, "Body", "Stand", (0, 0.1, t + 0.7))
    z = t + 0.35
    A.body(a, "green", (0, 0.1, z), 0.5, 0.48, 1.0, "egg", n=4, lean=-0.1, front=("yel", 0.7, z + 0.2, z + 0.75))
    for s in S2:
        A.folded_wing(a, "green", "blue", (s * 0.46, 0.15, z + 0.85), s, 0.85, 0.45, rows=2, down=(0, 0.4, -1))
    part(a, "Tail", "Body", (0, 0.3, z + 0.3))  # ось хвоста внутри тела — сгиб не раскрывается
    for k, (dx, key) in enumerate(((-0.12, "red"), (0.0, "blue"), (0.12, "yel"))):
        A.flipper(a, key, (dx, 0.28, z + 0.3), (dx * 3, 1.5, t + 0.05), 0.18, 0.12, thick=0.06, up=(0, 0.3, 1))
    heads = ((-1, "HeadR", "red", "angry", -32), (0, "HeadM", "blue", "goofy", 0), (1, "HeadL", "yel", "surprised", 32))
    for s, nm, key, mood, turn in heads:
        base = V((s * 0.25, -0.05, z + 0.9))
        part(a, nm, "Body", tuple(base))
        hc = V((s * 0.55, -0.15, z + 1.45 + (0.15 if s == 0 else 0)))
        A.limb(a, key, [tuple(base), tuple(hc)], [0.3, 0.26], joints=False)
        with_matrix(a, tilt(hc, "Z", turn))
        A.ball(a, key, tuple(hc), 0.27, n=3)
        a.prism("face", S.octagon(-0.17, 0.17, hc.z - 0.12, hc.z + 0.12, 0.05), hc.y - 0.276, hc.y - 0.17, axis="y",
                matrix=Matrix.Translation((hc.x, 0, 0)))
        for e in S2:
            eye2(a, tuple(hc + V((e * 0.1, -0.29, 0.05))), 0.065, (e * 0.3, -1, 0), mood, e, "face", "beak")
        A.beak(a, "beak", tuple(hc + V((0, -0.26, -0.06))), (0, -1, -0.6), 0.28, 0.16, gape=0.05)
        for k in range(3):  # хохолок
            spike(a, key, tuple(hc + V((0, 0.05 * k, 0.22))), tuple(hc + V((0, 0.2 + 0.12 * k, 0.55 - 0.06 * k))),
                  0.1)
        with_matrix(a, None)
    face_point(a, (0, -0.5, z + 1.5))
    closeup(a, (0.0, -0.4, z + 0.5))
    a.pose = {"HeadR": ((0, 0, -15), (0, 0, 0)), "HeadL": ((0, 0, 15), (0, 0, 0)), "HeadM": ((-10, 0, 0), (0, 0, 0))}
    return a


_OWN = [("ManyEyeCaterpillar", many_eye_caterpillar, "Гусеница-многоглазка", "Rare"),
         ("WheelMonkey", wheel_monkey, "Обезьяна-колесо", "Rare"),
         ("ThreeHeadParrot", three_head_parrot, "Попугай-трёхглав", "Rare")]

# порядок каталога; новые существа — по модулю на существо (jungle/<snake_case>.py с ITEM), см. jungle_kit.collect
ORDER = "ThreeHeadParrot ArchBoto CrocLanternfly WheelMonkey LionTamarin ManyEyeCaterpillar PoodleMoth LickyOkapi ConePangolin".split()
ITEMS = collect(ORDER, _OWN)
