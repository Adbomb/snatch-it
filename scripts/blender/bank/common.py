"""Коллекция «Банк» босса 7 — Common (каталог docs/BOSS7_CATALOG.md, D73). 4 утверждённых эскиза — из boss7/creatures.py,
8 новых — здесь. Признаки вида, эмоция и цвета — из каталога; правила анатомии D64 — anatomy_kit и bank_kit.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bank_kit import *  # noqa: E402,F401,F403


def ring_lemur():
    """5. Лемур-колечки: хвост втрое длиннее тела, в золотых и чёрных кольцах, — гордо держит его над головой
    вопросительным знаком. Признаки: маска вокруг больших глаз, острая мордочка, длинные лапы с цепкими пальцами,
    хвост в кольцах, светлое брюшко."""
    a = new("RingLemur", {"lem": ("A3A7B4", True), "lemW": ("F4F4F8", True), "lemD": ("2A2D3A", False),
                          "gold": ("F5B21C", False), "iris": ("FFB21C", False)})
    t = common_stand(a, 1.5)
    part(a, "Body", "Stand", (0, 0.15, t + 0.45))
    A.body(a, "lem", (0, 0.15, t), 0.4, 0.36, 0.85, "egg", n=4, front=("lemW", 0.62, t + 0.1, t + 0.7))
    for s in S2:  # задние лапы сидя, передние — длинные, кисти на коленях
        A.body(a, "lem", (s * 0.3, 0.05, t), 0.17, 0.3, 0.3, "egg", n=2)
        taper(a, "lemD", (s * 0.32, -0.15, t + 0.06), (s * 0.34, -0.42, t + 0.05), 0.15, 0.13, 0.1, 0.09)
        A.limb(a, "lem", [(s * 0.32, -0.02, t + 0.72), (s * 0.4, -0.25, t + 0.42), (s * 0.32, -0.35, t + 0.22)],
               [0.13, 0.11, 0.1])
        A.ball(a, "lemD", (s * 0.31, -0.38, t + 0.2), 0.08, n=2)
    part(a, "Head", "Body", (0, 0.05, t + 0.85))
    hc = V((0, -0.02, t + 1.08))
    th = A.body(a, "lemW", (hc.x, hc.y, hc.z - 0.26), 0.3, 0.28, 0.5, "ball", n=3)
    fy = front_y(th, 0, hc.z)
    taper(a, "lemW", (0, fy + 0.08, hc.z - 0.1), (0, fy - 0.2, hc.z - 0.14), 0.18, 0.1, 0.15, 0.09)  # мордочка
    a.box("lemD", -0.035, 0.035, fy - 0.24, fy - 0.17, hc.z - 0.14, hc.z - 0.08, bevel=0)  # нос
    for s in S2:
        x = s * 0.13
        a.prism("lemD", S.octagon(x - 0.1, x + 0.1, hc.z - 0.02, hc.z + 0.16, 0.04), front_y(th, x, hc.z) - 0.02,
                front_y(th, x, hc.z) + 0.06, axis="y", bevel=0)  # тёмная маска вокруг глаза
        eye2(a, (x, front_y(th, x, hc.z + 0.07) - 0.01, hc.z + 0.07), 0.07, (s * 0.2, -1, 0), "sly", s, "lemD", "lemD",
             show_brow=False)
        a.box("iris", x - 0.035, x + 0.035, front_y(th, x, hc.z + 0.07) - 0.07, front_y(th, x, hc.z + 0.07) - 0.05,
              hc.z + 0.035, hc.z + 0.085, bevel=0)  # жёлтая радужка
        tri_ear(a, "lemD", "lem", (s * 0.18, hc.y + 0.05, hc.z + 0.18), (s * 0.32, hc.y + 0.06, hc.z + 0.38), 0.15)
    part(a, "Tail", "Body", (0, 0.45, t + 0.2))
    A.ball(a, "lem", (0, 0.42, t + 0.17), 0.12, n=2)
    pts = [(0, 0.42, t + 0.15), (0, 0.78, t + 0.32), (0, 0.98, t + 0.7), (0, 0.82, t + 1.12), (0, 0.78, t + 1.5),
           (0, 0.98, t + 1.86), (0, 1.18, t + 2.0), (0, 1.32, t + 1.9)]  # S-дуга за спиной (не крючок над головой)
    for i in range(len(pts) - 1):  # кольца: золото и чёрный
        kchain(a, "gold" if i % 2 == 0 else "lemD", [pts[i], pts[i + 1]], [0.2, 0.19 - 0.008 * i], up=(1, 0, 0))
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.0, 0.5, t + 1.2))
    a.pose = {"Tail": ((10, 0, 0), (0, 0, 0)), "Head": ((0, 0, -10), (0, 0, 0))}
    return a


def ring_seahorse():
    """6. Конёк-колечко: морской конёк свернул хвост в идеальное золотое кольцо и прыгает на нём, как на пружинке.
    Признаки: голова «лошадкой» с трубочкой-рылом, корона-гребень, сегменты тела, спинной плавничок, хвост-завиток."""
    a = new("RingSeahorse", {"sea": ("FF7A5A", True), "seaL": ("FFC2A8", False), "gold": ("F5B21C", True),
                             "fin": ("FFE07A", False)})
    t = common_stand(a, 1.4)
    part(a, "Body", "Stand", (0, 0.1, t + 0.5))
    rc, R = V((0, 0.12, t + 0.42)), 0.33
    pts = [tuple(rc + V((0, R * math.cos(math.radians(g)), R * math.sin(math.radians(g))))) for g in range(95, 440, 35)]
    kchain(a, "gold", pts, [0.2 - 0.008 * i for i in range(len(pts))], up=(1, 0, 0), overlap=0.5)  # хвост-кольцо
    tb = A.body(a, "sea", (0, 0.05, t + 0.68), 0.27, 0.3, 0.85, "egg", n=5, lean=-0.12)
    for k in range(4):  # светлые кольца-сегменты брюшка
        z = t + 0.78 + 0.16 * k
        y = front_y(tb, 0, z + 0.035)
        a.box("seaL", -0.16, 0.16, y - 0.025, y + 0.06, z, z + 0.07, bevel=0)
    kchain(a, "fin", [(0, 0.3, t + 0.9), (0, 0.4, t + 1.15), (0, 0.32, t + 1.35)], [0.05, 0.06, 0.04],
           [0.22, 0.3, 0.16], up=(1, 0, 0))  # спинной плавник
    part(a, "Head", "Body", (0, 0.0, t + 1.5))
    hc = V((0, -0.02, t + 1.72))
    th = A.body(a, "sea", (hc.x, hc.y, hc.z - 0.2), 0.22, 0.28, 0.42, "ball", n=3)
    fy = front_y(th, 0, hc.z)
    kchain(a, "sea", [(0, fy + 0.1, hc.z - 0.04), (0, fy - 0.2, hc.z - 0.07), (0, fy - 0.38, hc.z - 0.1)],
           [0.13, 0.1, 0.1], up=(0, 0, 1))  # трубочка-рыло
    a.box("mouth", -0.04, 0.04, fy - 0.43, fy - 0.37, hc.z - 0.14, hc.z - 0.07, bevel=0)
    for k, (dx, h) in enumerate(((0.0, 0.2), (-0.07, 0.14), (0.07, 0.14))):  # корона-гребень
        spike(a, "gold", (dx, hc.y + 0.04, hc.z + 0.16), (dx, hc.y + 0.06, hc.z + 0.16 + h), 0.07)
    for s in S2:
        eye2(a, (s * 0.15, front_y(th, s * 0.15, hc.z + 0.05) + 0.02, hc.z + 0.05), 0.07, (s * 0.6, -1, 0.1), "goofy",
             s, "sea", "mouth")
    face_point(a, (0, fy - 0.15, hc.z))
    closeup(a, (0.0, -0.2, t + 0.5))
    a.pose = {"Head": ((0, 0, 10), (0, 0, 0))}
    return a


def pearl_guineafowl():
    """7. Цесарка-жемчужинка: тело — идеальный шар в белый «жемчужный» горошек, наверху крошечная голова со шлемом.
    Признаки: голая голубая голова с роговым шлемом, красные бородки, круглое тело в белых пятнах, тонкие ноги."""
    a = new("PearlGuineafowl", {"gui": ("2A3550", True), "spot": ("F6F4FF", False), "guiB": ("5AB4E8", False),
                                "red": ("E8283C", False), "casq": ("D2A86A", False), "beak": ("F0D9A8", False),
                                "leg": ("8A93A6", False)})
    t = common_stand(a, 1.45)
    part(a, "Body", "Stand", (0, 0.1, t + 0.8))
    bc = V((0, 0.1, t + 0.82))
    A.body(a, "gui", (bc.x, bc.y, bc.z - 0.55), 0.56, 0.58, 1.1, "ball", n=6, floor=0.35)
    picks = [(az, el) for el, n0 in ((-0.45, 10), (-0.15, 12), (0.15, 12), (0.45, 10), (0.72, 6)) for az in
             [((360 / n0) * i + 17 * el * 10) % 360 for i in range(n0)]]
    dots_on_ball(a, "spot", bc, 0.56, 0.58, 0.55, picks, r=0.07)  # «жемчужный» горошек
    for s in S2:
        A.limb(a, "leg", [(s * 0.17, 0.1, t + 0.35), (s * 0.18, 0.05, t + 0.16), (s * 0.18, 0.0, t + 0.03)],
               [0.07, 0.06, 0.05], joints=False)
        for dx in (-0.06, 0.0, 0.06):
            taper(a, "leg", (s * 0.18, 0.0, t + 0.03), (s * 0.18 + dx, -0.18, t + 0.03), 0.04, 0.03)
    part(a, "Head", "Body", (0, -0.25, t + 1.3))
    kchain(a, "guiB", [(0, -0.22, t + 1.2), (0, -0.3, t + 1.42), (0, -0.33, t + 1.55)], [0.13, 0.11, 0.11],
           up=(0, -1, 0))  # голая шея
    hc = V((0, -0.34, t + 1.62))
    th = A.body(a, "guiB", (hc.x, hc.y, hc.z - 0.12), 0.13, 0.15, 0.25, "ball", n=3)
    fy = front_y(th, 0, hc.z)
    a.frustum("casq", (-0.06, 0.06, hc.y - 0.04, hc.y + 0.07), (-0.02, 0.02, hc.y + 0.02, hc.y + 0.06), hc.z + 0.1,
              hc.z + 0.28, bevel=0)  # роговой шлем
    A.beak(a, "beak", (0, fy + 0.03, hc.z - 0.02), (0, -1, -0.1), 0.12, 0.08)
    for s in S2:
        a.box("red", s * 0.05 - 0.035, s * 0.05 + 0.035, fy - 0.02, fy + 0.03, hc.z - 0.16, hc.z - 0.06, bevel=0)
        eye2(a, (s * 0.08, front_y(th, s * 0.08, hc.z + 0.03) + 0.01, hc.z + 0.03), 0.045, (s * 0.5, -1, 0),
             "surprised", s, "guiB", "gui")
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.0, -0.3, t + 0.8))
    a.pose = {"Head": ((0, 0, 12), (0, 0, 0))}
    return a


def stash_squirrel():
    """8. Белка-хвостохран: хвост втрое больше белки — в нём она прячет золотые жёлуди, они торчат из шерсти.
    Признаки: кисточки на ушах, большой пушистый хвост, передние лапки у груди, светлое брюшко."""
    a = new("StashSquirrel", {"sq": ("D9692E", True), "sqL": ("FCE3C4", True), "sqD": ("8A3F18", False),
                              "gold": ("F5B21C", False), "goldD": ("C9820E", False)})
    t = common_stand(a, 1.5)
    part(a, "Body", "Stand", (0, 0.0, t + 0.45))
    A.body(a, "sq", (0, 0.0, t), 0.34, 0.32, 0.78, "egg", n=4, front=("sqL", 0.6, t + 0.08, t + 0.65))
    for s in S2:
        A.body(a, "sq", (s * 0.26, -0.05, t), 0.15, 0.28, 0.26, "egg", n=2)
        taper(a, "sqD", (s * 0.28, -0.2, t + 0.05), (s * 0.3, -0.42, t + 0.04), 0.12, 0.1, 0.08, 0.07)
        A.limb(a, "sq", [(s * 0.2, -0.15, t + 0.62), (s * 0.18, -0.36, t + 0.5), (s * 0.08, -0.38, t + 0.56)],
               [0.09, 0.08, 0.07])
    part(a, "Head", "Body", (0, -0.05, t + 0.78))
    hc = V((0, -0.1, t + 1.0))
    th = A.body(a, "sq", (hc.x, hc.y, hc.z - 0.24), 0.26, 0.26, 0.46, "ball", n=3)
    fy = front_y(th, 0, hc.z)
    a.prism("sqL", S.octagon(-0.13, 0.13, hc.z - 0.2, hc.z - 0.04, 0.05), fy - 0.03, fy + 0.08, axis="y", bevel=0)
    a.box("sqD", -0.04, 0.04, fy - 0.06, fy - 0.02, hc.z - 0.07, hc.z - 0.02, bevel=0)
    for s in S2:
        eye2(a, (s * 0.11, front_y(th, s * 0.11, hc.z + 0.05) + 0.01, hc.z + 0.05), 0.06, (s * 0.3, -1, 0), "sly", s,
             "sq", "sqD", look=(s * 0.6, 0))
        tri_ear(a, "sq", "sqL", (s * 0.14, hc.y + 0.05, hc.z + 0.18), (s * 0.2, hc.y + 0.08, hc.z + 0.42), 0.13)
        spike(a, "sqD", (s * 0.2, hc.y + 0.08, hc.z + 0.4), (s * 0.22, hc.y + 0.1, hc.z + 0.56), 0.07)  # кисточка
    part(a, "Tail", "Body", (0, 0.3, t + 0.2))
    A.ball(a, "sq", (0, 0.3, t + 0.22), 0.14, n=2)
    tp = [V((0, 0.45, t + 0.3)), V((0, 0.82, t + 0.62)), V((0, 0.68, t + 1.15)), V((0, 0.6, t + 1.6)),
          V((0, 0.8, t + 1.95))]  # пушистый хвост буквой S
    fluff(a, ["sq", "sqD", "sq", "sq", "sqD"], tp, [0.3, 0.38, 0.36, 0.32, 0.24], n=3)
    for p, d in ((tp[1] + V((-0.34, -0.2, 0.0)), (-0.7, -0.6, 0.2)), (tp[2] + V((0.32, -0.24, 0.05)), (0.7, -0.6, 0.2)),
                 (tp[3] + V((-0.26, -0.2, 0.05)), (-0.6, -0.7, 0.3))):  # крупные золотые жёлуди наружу
        dd = V(d).normalized()
        taper(a, "gold", p, p + dd * 0.3, 0.26, 0.2, 0.26, 0.2, up=(0, 0, 1))  # жёлудь
        taper(a, "goldD", p + dd * 0.26, p + dd * 0.4, 0.3, 0.16, 0.3, 0.16, up=(0, 0, 1))  # шляпка
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.0, 0.5, t + 1.0))
    a.pose = {"Tail": ((15, 0, 0), (0, 0, 0)), "Head": ((0, 0, 15), (0, 0, 0))}
    return a


def pearl_platypus():
    """9. Утконос-перламутр: будто собран из трёх зверей — утиный клюв, бобровый хвост, лапы выдры, — а клюв
    переливается перламутром. Признаки: широкий плоский клюв, плоский хвост-лопата, перепончатые лапы, бурая шерсть,
    маленькие глаза. v2 (владелец 2026-11-26): голова поднята, сам крупнее на плите."""
    a = new("PearlPlatypus", {"plat": ("8A5A36", True), "platL": ("C99A6A", False), "bill": ("9FC6E8", False),
                              "billL": ("E2F0FF", False), "web": ("B07A5A", False), "tailP": ("5A3A24", True)})
    t = common_stand(a, 1.55)
    part(a, "Body", "Stand", (0, 0.1, t + 0.4))
    kchain(a, "plat", [(0, -0.32, t + 0.42), (0, 0.2, t + 0.44), (0, 0.72, t + 0.38)], [0.8, 0.88, 0.7],
           [0.64, 0.68, 0.54], up=(0, 0, 1), overlap=0.5)
    a.prism("platL", S.octagon(-0.3, 0.3, -0.3, 0.55, 0.12), t + 0.08, t + 0.13, bevel=0)  # светлое брюхо снизу
    for s in S2:
        for y0 in (-0.22, 0.52):
            A.limb(a, "plat", [(s * 0.34, y0, t + 0.34), (s * 0.5, y0 - 0.05, t + 0.08)], [0.15, 0.13], joints=False)
            a.extrude("web", [(-0.15, 0), (0.15, 0), (0.21, -0.26), (-0.21, -0.26)], 0.0, 0.05, axis="z",
                      matrix=Matrix.Translation((s * 0.52, y0 - 0.06, t + 0.01)))
    part(a, "Tail", "Body", (0, 0.78, t + 0.34))
    A.ball(a, "plat", (0, 0.78, t + 0.34), 0.15, n=2)
    kchain(a, "tailP", [(0, 0.78, t + 0.32), (0, 1.1, t + 0.24), (0, 1.36, t + 0.2)], [0.5, 0.56, 0.46],
           [0.11, 0.1, 0.09], up=(0, 0, 1))  # хвост-лопата
    part(a, "Head", "Body", (0, -0.45, t + 0.55))
    A.ball(a, "plat", (0, -0.45, t + 0.55), 0.22, n=2)  # шея
    hc = V((0, -0.62, t + 0.78))  # голова поднята
    th = A.body(a, "plat", (hc.x, hc.y, hc.z - 0.26), 0.32, 0.3, 0.52, "ball", n=3)
    fy = front_y(th, 0, hc.z - 0.05)
    kchain(a, "bill", [(0, fy + 0.12, hc.z - 0.08), (0, fy - 0.24, hc.z - 0.02), (0, fy - 0.5, hc.z + 0.08)],
           [0.42, 0.5, 0.52], [0.12, 0.11, 0.1], up=(0, 0.3, 1), overlap=0.4)  # широкий клюв, вверх
    kchain(a, "billL", [(-0.05, fy - 0.12, hc.z + 0.02), (-0.05, fy - 0.42, hc.z + 0.12)], [0.16, 0.14],
           [0.03, 0.03], up=(0, 0.3, 1), overlap=0.2)  # перламутровый блик
    for s in S2:
        eye2(a, (s * 0.16, front_y(th, s * 0.16, hc.z + 0.1) + 0.01, hc.z + 0.1), 0.06, (s * 0.4, -1, 0.2), "calm",
             s, "plat", "tailP", lid=0.25)
    face_point(a, (0, fy - 0.2, hc.z))
    closeup(a, (0.0, -0.4, t + 0.5))
    a.pose = {"Tail": ((0, 0, 15), (0, 0, 0)), "Head": ((-10, 0, 0), (0, 0, 0))}
    return a


def greedy_wolverine():
    """10. Росомаха-обжора: так объелась, что сидит, выпятив большой живот, и гладит его лапой; тело обычной формы.
    Признаки: светлая полоса по бокам от плеч к хвосту, тёмная маска, короткие толстые лапы с когтями, пушистый
    хвост, маленькие круглые уши."""
    a = new("GreedyWolverine", {"wol": ("4A3022", True), "wolB": ("C49466", True), "wolS": ("E0A040", False),
                                "wolL": ("C9A27A", False), "claw": ("F3E9D2", False)})
    t = common_stand(a, 1.55)
    part(a, "Body", "Stand", (0, 0.15, t + 0.5))
    A.body(a, "wol", (0, 0.18, t), 0.48, 0.42, 1.0, "egg", n=4)
    A.body(a, "wolB", (0, -0.18, t + 0.1), 0.42, 0.36, 0.66, "ball", n=4)  # большой живот вперёд
    for s in S2:  # светлая полоса по боку
        kchain(a, "wolS", [(s * 0.44, -0.05, t + 0.85), (s * 0.5, 0.25, t + 0.55), (s * 0.4, 0.5, t + 0.25)],
               [0.1, 0.12, 0.1], [0.06, 0.06, 0.06], up=(s, 0, 0))
        A.body(a, "wol", (s * 0.34, -0.05, t), 0.17, 0.3, 0.26, "egg", n=2)
        taper(a, "wol", (s * 0.36, -0.2, t + 0.06), (s * 0.38, -0.45, t + 0.05), 0.15, 0.14, 0.1, 0.09)
        paw_claws(a, "claw", (s * 0.38, -0.48, t + 0.06), n=3, ln=0.08, w=0.04, spread=0.05)
    part(a, "ArmL", "Body", (0.36, -0.05, t + 0.75))  # одна лапа гладит живот
    A.ball(a, "wol", (0.36, -0.05, t + 0.75), 0.17, n=2)
    A.limb(a, "wol", [(0.36, -0.05, t + 0.75), (0.42, -0.3, t + 0.55), (0.12, -0.42, t + 0.48)], [0.15, 0.13, 0.12])
    part(a, "ArmR", "Body", (-0.36, -0.05, t + 0.75))
    A.ball(a, "wol", (-0.36, -0.05, t + 0.75), 0.17, n=2)
    A.limb(a, "wol", [(-0.36, -0.05, t + 0.75), (-0.48, -0.2, t + 0.45), (-0.45, -0.25, t + 0.12)], [0.15, 0.13, 0.12])
    part(a, "Tail", "Body", (0, 0.55, t + 0.2))
    fluff(a, ["wol"], [V((0, 0.62, t + 0.15)), V((0.15, 0.85, t + 0.12))], [0.18, 0.15], n=3)
    part(a, "Head", "Body", (0, 0.05, t + 1.0))
    hc = V((0, 0.0, t + 1.22))
    th = A.body(a, "wol", (hc.x, hc.y, hc.z - 0.26), 0.32, 0.3, 0.5, "ball", n=3)
    fy = front_y(th, 0, hc.z)
    a.prism("wolL", S.octagon(-0.3, 0.3, hc.z + 0.12, hc.z + 0.26, 0.04), fy - 0.02, fy + 0.1, axis="y", bevel=0)  # светлый лоб
    a.prism("wolL", S.octagon(-0.24, 0.24, hc.z - 0.2, hc.z - 0.02, 0.06), fy - 0.03, fy + 0.1, axis="y", bevel=0)  # светлая морда
    taper(a, "wol", (0, fy + 0.06, hc.z - 0.1), (0, fy - 0.16, hc.z - 0.14), 0.2, 0.15, 0.15, 0.12)
    a.box("dark", -0.05, 0.05, fy - 0.2, fy - 0.14, hc.z - 0.12, hc.z - 0.06, bevel=0)
    a.box("tongue", 0.04, 0.12, fy - 0.17, fy - 0.12, hc.z - 0.22, hc.z - 0.16, bevel=0)  # облизывается
    for s in S2:
        eye2(a, (s * 0.14, front_y(th, s * 0.14, hc.z + 0.05) - 0.01, hc.z + 0.05), 0.08, (s * 0.3, -1, 0), "sleepy",
             s, "wol", "wolL")
        A.ball(a, "wol", (s * 0.22, hc.y + 0.05, hc.z + 0.22), 0.08, n=2)
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.0, -0.4, t + 0.5))
    a.pose = {"ArmL": ((-15, 0, 0), (0, 0, 0)), "Head": ((0, 0, 10), (0, 0, 0))}
    return a


def jump_jerboa():
    """11. Тушканчик-прыгун: огромные ступни и уши при крошечном тельце, длинный хвост с золотой кисточкой —
    подпрыгнул от восторга. Признаки: длинные задние ноги с огромными ступнями, огромные уши, крошечные передние
    лапки, большие глаза, хвост с кисточкой."""
    a = new("JumpJerboa", {"jer": ("E0B878", True), "jerW": ("FFF4E2", False), "earP": ("FFB3C6", False),
                           "gold": ("F5B21C", False)})
    t = common_stand(a, 1.5)
    part(a, "Body", "Stand", (0, 0.05, t + 0.75))
    bc = V((0, 0.05, t + 0.8))
    A.body(a, "jer", (bc.x, bc.y, bc.z - 0.26), 0.26, 0.26, 0.52, "ball", n=4, front=("jerW", 0.6, bc.z - 0.2, bc.z + 0.1))
    for s in S2:  # длинные ноги-пружины и огромные ступни
        A.limb(a, "jer", [(s * 0.16, 0.12, bc.z - 0.12), (s * 0.22, 0.35, bc.z - 0.4), (s * 0.2, 0.15, t + 0.08)],
               [0.13, 0.08, 0.07])
        kchain(a, "jer", [(s * 0.2, 0.25, t + 0.04), (s * 0.21, -0.25, t + 0.04), (s * 0.22, -0.55, t + 0.04)],
               [0.12, 0.14, 0.12], [0.07, 0.07, 0.06], up=(0, 0, 1))
        A.limb(a, "jer", [(s * 0.12, -0.15, bc.z), (s * 0.14, -0.28, bc.z - 0.1)], [0.05, 0.045], joints=False)
    part(a, "Tail", "Body", (0, 0.28, bc.z - 0.15))
    A.ball(a, "jer", (0, 0.26, bc.z - 0.14), 0.08, n=2)
    kchain(a, "jer", [(0, 0.28, bc.z - 0.15), (0, 0.7, bc.z - 0.35), (0, 1.1, bc.z - 0.2), (0, 1.35, bc.z + 0.15)],
           [0.05, 0.045, 0.04, 0.035], up=(1, 0, 0))
    for k, (dx, dz) in enumerate(((0.0, 0.32), (-0.1, 0.22), (0.1, 0.22), (0.0, 0.1))):  # золотая кисточка
        spike(a, "gold", (0, 1.33, bc.z + 0.12), (dx, 1.45, bc.z + 0.12 + dz), 0.09)
    part(a, "Head", "Body", (0, -0.05, bc.z + 0.2))
    hc = V((0, -0.12, bc.z + 0.36))
    th = A.body(a, "jer", (hc.x, hc.y, hc.z - 0.19), 0.2, 0.21, 0.36, "ball", n=3)
    fy = front_y(th, 0, hc.z)
    a.box("pink", -0.025, 0.025, fy - 0.05, fy - 0.01, hc.z - 0.07, hc.z - 0.03, bevel=0)
    grin(a, (0, fy - 0.01, hc.z - 0.12), 0.08, h=0.035)
    for s in S2:
        eye2(a, (s * 0.09, front_y(th, s * 0.09, hc.z + 0.04) + 0.01, hc.z + 0.04), 0.07, (s * 0.35, -1, 0), "goofy",
             s, "jer", "dark")
        tri_ear(a, "jer", "earP", (s * 0.1, hc.y + 0.04, hc.z + 0.12), (s * 0.3, hc.y + 0.12, hc.z + 0.75), 0.24,
                th=0.06)  # огромные уши
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.2, -0.3, t + 0.3))
    a.pose = {"Tail": ((-10, 0, 0), (0, 0, 0)), "Head": ((0, 0, 10), (0, 0, 0))}
    return a


def whisker_shrimp():
    """12. Креветка-златоус: золотые усы втрое длиннее тела — гордо закрутила их колечками, стоя на веере хвоста.
    Признаки: сегментированное изогнутое тело, длинные усики, ножки-плавнички, хвостовой веер, глаза на стебельках."""
    a = new("WhiskerShrimp", {"shr": ("E8283C", True), "shrL": ("FF7A7A", False), "shrF": ("FF9A5A", False),
                              "gold": ("F5B21C", False)})
    t = common_stand(a, 1.45)
    part(a, "Body", "Stand", (0, 0.2, t + 0.5))
    for k, ang in enumerate((-40, -14, 14, 40)):  # хвостовой веер на подставке
        a.extrude("shrF", [(-0.08, 0), (0.08, 0), (0.12, 0.34), (-0.12, 0.34)], 0.0, 0.05, axis="z",
                  matrix=Matrix.Translation((0, 0.3, t + 0.01 + 0.004 * k)) @ Matrix.Rotation(math.radians(ang), 4, "Z"))
    seg = [(0, 0.3, t + 0.1), (0, 0.36, t + 0.4), (0, 0.32, t + 0.72), (0, 0.18, t + 0.98), (0, -0.02, t + 1.12)]
    ws = [0.2, 0.28, 0.34, 0.36, 0.34]
    for i in range(len(seg) - 1):  # сегменты: красный и светлый по очереди
        kchain(a, "shr" if i % 2 == 0 else "shrL", [seg[i], seg[i + 1]], [ws[i], ws[i + 1]], up=(0, -1, 0), overlap=0.5)
    for k in range(3):  # ножки-плавнички спереди
        z = t + 0.5 + 0.18 * k
        for s in S2:
            taper(a, "shrL", (s * 0.08, 0.2 - 0.06 * k, z), (s * 0.16, 0.02 - 0.06 * k, z - 0.14), 0.05, 0.035)
    part(a, "Head", "Body", (0, -0.02, t + 1.12))
    hc = V((0, -0.12, t + 1.18))
    taper(a, "shr", (0, 0.05, hc.z), (0, -0.38, hc.z + 0.08), 0.36, 0.18, 0.3, 0.16)  # панцирь головы
    spike(a, "shr", (0, -0.36, hc.z + 0.12), (0, -0.62, hc.z + 0.2), 0.08)  # рострум
    for s in S2:  # глаза на стебельках
        kchain(a, "shr", [(s * 0.1, -0.15, hc.z + 0.12), (s * 0.16, -0.2, hc.z + 0.3)], [0.06, 0.05], up=(0, -1, 0))
        A.ball(a, "white", (s * 0.17, -0.22, hc.z + 0.36), 0.08, n=2)
        a.box("dark", s * 0.17 - 0.035, s * 0.17 + 0.035, -0.31, -0.29, hc.z + 0.34, hc.z + 0.4, bevel=0)
        a.box("shr", s * 0.17 - 0.08, s * 0.17 + 0.08, -0.3, -0.22, hc.z + 0.42, hc.z + 0.46, bevel=0,
              matrix=tilt((s * 0.17, -0.26, hc.z + 0.44), "Y", -s * 15))  # бровь-веко «напыщенная»
        pts = [(s * 0.06, -0.3, hc.z + 0.02), (s * 0.16, -0.48, hc.z + 0.36), (s * 0.3, -0.3, hc.z + 0.74),
               (s * 0.42, 0.15, hc.z + 0.9), (s * 0.5, 0.6, hc.z + 0.72), (s * 0.56, 0.92, hc.z + 0.36)]  # длинная дуга назад
        c = V((s * 0.62, 0.98, hc.z + 0.22))
        for k in range(5):  # маленький завиток на кончике
            g = math.radians(120 - k * 70)
            pts.append(tuple(c + V((s * 0.1 * math.cos(g), 0.08 * math.sin(g), 0.1 * math.sin(g)))))
        kchain(a, "gold", pts, [0.055] * 6 + [0.045] * 5, up=(s, 0, 0.2), overlap=0.4)
    a.box("mouth", -0.05, 0.05, -0.34, -0.3, hc.z - 0.1, hc.z - 0.06, bevel=0)
    face_point(a, (0, -0.3, hc.z + 0.2))
    closeup(a, (0.0, 0.2, t + 0.6))
    a.pose = {"Head": ((0, 0, -10), (0, 0, 0))}
    return a


_OWN = {"RingLemur": ring_lemur, "RingSeahorse": ring_seahorse, "PearlGuineafowl": pearl_guineafowl,
        "StashSquirrel": stash_squirrel, "PearlPlatypus": pearl_platypus, "GreedyWolverine": greedy_wolverine,
        "JumpJerboa": jump_jerboa, "WhiskerShrimp": whisker_shrimp}
ORDER = [("HoardHamster", SK.hoard_hamster, "Хомяк-щекастик", "Common"),
         ("GoldAxolotl", SK.gold_axolotl, "Аксолотль-златожабр", "Common"),
         ("RaccoonMagpie", SK.raccoon_magpie, "Сорока-енот", "Common"),
         ("StarNoseMole", SK.star_nose_mole, "Крот-звездонос", "Common"),
         ("RingLemur", None, "Лемур-колечки", "Common"), ("RingSeahorse", None, "Конёк-колечко", "Common"),
         ("PearlGuineafowl", None, "Цесарка-жемчужинка", "Common"), ("StashSquirrel", None, "Белка-хвостохран", "Common"),
         ("PearlPlatypus", None, "Утконос-перламутр", "Common"), ("GreedyWolverine", None, "Росомаха-обжора", "Common"),
         ("JumpJerboa", None, "Тушканчик-прыгун", "Common"), ("WhiskerShrimp", None, "Креветка-златоус", "Common")]
ITEMS = collect(ORDER, _OWN)
