"""Коллекция «Банк» босса 7 — Rare (каталог docs/BOSS7_CATALOG.md, D73). 3 утверждённых эскиза — из boss7/creatures.py,
6 новых — здесь."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bank_kit import *  # noqa: E402,F401,F403


def quad_body(a, key, y0, y1, z, w, h, keys=None):
    """Тело четвероногого вдоль y: звенья от груди y0 к крупу y1 (keys — цвета звеньев по очереди)."""
    n = len(keys) if keys else 2
    pts = [(0, y0 + (y1 - y0) * k / n, z) for k in range(n + 1)]
    for i in range(n):
        kchain(a, keys[i] if keys else key, [pts[i], pts[i + 1]], [w, w * (0.98 if i % 2 else 1.0)],
               [h, h * (0.98 if i % 2 else 1.0)], up=(0, 0, 1), overlap=0.3)


def handstand_skunk():
    """4. Скунс-стойка: стоит на передних лапах вниз головой, как настоящий пятнистый скунс, задрав золотые полосы и
    хвост-веер. Признаки: полосы-узор (здесь золотые), пушистый хвост, острая мордочка, короткие лапы, чёрная шерсть."""
    a = new("HandstandSkunk", {"sk": ("22222E", True), "gold": ("F5B21C", True), "skW": ("F4F4F8", False)})
    t = rare_stand(a, 1.5)
    part(a, "Body", "Stand", (0, -0.2, t + 0.5))
    for s in S2:  # передние лапы — опора
        A.limb(a, "sk", [(s * 0.2, -0.22, t + 0.62), (s * 0.22, -0.25, t + 0.3), (s * 0.22, -0.28, t + 0.06)],
               [0.13, 0.12, 0.11])
        a.prism("sk", S.octagon(s * 0.22 - 0.09, s * 0.22 + 0.09, -0.4, -0.2, 0.03), t, t + 0.07, bevel=0)
    kchain(a, "sk", [(0, -0.2, t + 0.6), (0, 0.05, t + 0.9), (0, 0.3, t + 1.15)], [0.52, 0.5, 0.44],
           [0.46, 0.46, 0.4], up=(0, -1, 0), overlap=0.5)  # тело наискось вверх-назад
    for s in S2:  # две золотые полосы по спине
        kchain(a, "gold", [(s * 0.13, 0.03, t + 0.6), (s * 0.13, 0.28, t + 0.9), (s * 0.12, 0.5, t + 1.12)],
               [0.09, 0.09, 0.08], [0.06, 0.06, 0.06], up=(0, 1, -0.6))
        A.limb(a, "sk", [(s * 0.17, 0.32, t + 1.15), (s * 0.3, 0.25, t + 1.42), (s * 0.34, 0.12, t + 1.55)],
               [0.12, 0.1, 0.09])  # задние лапы в воздухе
    part(a, "Tail", "Body", (0, 0.4, t + 1.2))
    tp = [V((0, 0.5, t + 1.3)), V((0, 0.85, t + 1.42)), V((0, 1.15, t + 1.3)), V((0, 1.28, t + 0.98))]
    fluff(a, ["sk", "gold", "sk", "gold"], tp, [0.26, 0.36, 0.4, 0.32], n=3)  # пышный хвост-веер дугой назад
    part(a, "Head", "Body", (0, -0.35, t + 0.55))
    hc = V((0, -0.45, t + 0.42))
    th = A.body(a, "sk", (hc.x, hc.y, hc.z - 0.22), 0.24, 0.24, 0.42, "ball", n=3)
    fy = front_y(th, 0, hc.z)
    a.box("gold", -0.04, 0.04, fy - 0.02, fy + 0.06, hc.z + 0.04, hc.z + 0.22, bevel=0)  # полоска на лбу
    taper(a, "sk", (0, fy + 0.05, hc.z - 0.08), (0, fy - 0.16, hc.z - 0.1), 0.15, 0.08, 0.12, 0.07)
    a.box("pink", -0.03, 0.03, fy - 0.2, fy - 0.15, hc.z - 0.1, hc.z - 0.05, bevel=0)
    for s in S2:
        eye2(a, (s * 0.1, front_y(th, s * 0.1, hc.z + 0.04) + 0.01, hc.z + 0.04), 0.06, (s * 0.3, -1, 0), "proud", s,
             "sk", "skW")
        A.ball(a, "sk", (s * 0.17, hc.y + 0.05, hc.z + 0.2), 0.07, n=2)
    grin(a, (0, fy - 0.02, hc.z - 0.17), 0.1, h=0.035, key="skW")
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.0, 0.2, t + 1.1))
    a.pose = {"Tail": ((-15, 0, 0), (0, 0, 0))}
    return a


def cape_ratel():
    """5. Медоед-плащ: серебристая спина — как плащ, а сам маленький и распушился, чтобы казаться огромным.
    Признаки: серебристо-белая спина от макушки до хвоста, чёрные бока и лапы, мощные когти, маленькие глаза."""
    a = new("CapeRatel", {"rat": ("1E1E26", True), "silv": ("D8DCE6", True), "claw": ("F3E9D2", False)})
    t = rare_stand(a, 1.55)
    part(a, "Body", "Stand", (0, 0.05, t + 0.55))
    quad_body(a, "rat", -0.35, 0.55, t + 0.56, 0.66, 0.56)
    kchain(a, "silv", [(0, -0.42, t + 0.78), (0, 0.1, t + 0.86), (0, 0.6, t + 0.8)], [0.7, 0.74, 0.62],
           [0.26, 0.28, 0.24], up=(0, 0, 1))  # серебряный «плащ» по спине
    for k in range(5):  # распушённый край плаща
        y = -0.3 + 0.2 * k
        for s in S2:
            spike(a, "silv", (s * 0.33, y, t + 0.8), (s * 0.48, y + 0.03, t + 0.98), 0.12)
    for s in S2:
        for y0 in (-0.3, 0.45):
            leg(a, "rat", (s * 0.27, y0, t + 0.45), (s * 0.3, y0 - 0.02, t), 0.2, 0.17)
            paw_claws(a, "claw", (s * 0.3, y0 - 0.1, t + 0.04), n=3, ln=0.12, w=0.05, spread=0.05)
    part(a, "Tail", "Body", (0, 0.65, t + 0.7))
    kchain(a, "silv", [(0, 0.66, t + 0.75), (0, 0.88, t + 0.95)], [0.16, 0.1], up=(1, 0, 0))
    part(a, "Head", "Body", (0, -0.5, t + 0.7))
    hc = V((0, -0.65, t + 0.7))
    th = A.body(a, "rat", (hc.x, hc.y, hc.z - 0.24), 0.28, 0.27, 0.46, "ball", n=3)
    a.prism("silv", S.octagon(-0.24, 0.24, hc.y - 0.15, hc.y + 0.25, 0.08), hc.z + 0.1, hc.z + 0.24, bevel=0)  # макушка
    fy = front_y(th, 0, hc.z)
    taper(a, "rat", (0, fy + 0.05, hc.z - 0.08), (0, fy - 0.14, hc.z - 0.1), 0.2, 0.14, 0.15, 0.11)
    a.box("dark", -0.04, 0.04, fy - 0.18, fy - 0.13, hc.z - 0.09, hc.z - 0.04, bevel=0)
    for s in S2:
        eye2(a, (s * 0.11, front_y(th, s * 0.11, hc.z + 0.05) + 0.01, hc.z + 0.05), 0.05, (s * 0.3, -1, 0), "angry",
             s, "rat", "silv")
    a.box("mouth", -0.08, 0.08, fy - 0.12, fy - 0.08, hc.z - 0.2, hc.z - 0.16, bevel=0)
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.0, 0.0, t + 0.9))
    a.pose = {"Head": ((10, 0, 0), (0, 0, 0))}
    return a


def juggler_starfish():
    """6. Морская звезда-жонглёр: на каждом из трёх верхних лучей по монетке — не может решить, какую отдать, и
    жонглирует. Признаки: пять толстых лучей, бугорки по лучам, центральный диск (лицо — в центре)."""
    a = new("JugglerStarfish", {"star": ("FF8A6A", True), "bump": ("FFE2C8", False), "starD": ("E05A4A", False)})
    t = rare_stand(a, 1.5)
    part(a, "Body", "Stand", (0, 0, t + 0.8))
    c = V((0, 0, t + 0.82))
    pts = [(c.x + 0.36 * math.cos(math.radians(90 + 360 * i / 16)),
            c.z + 0.36 * math.sin(math.radians(90 + 360 * i / 16))) for i in range(16)]
    a.prism("star", pts, -0.16, 0.16, axis="y")  # центральный диск
    for k, ang in enumerate((90, 18, 162, 234, 306)):
        r = math.radians(ang)
        d = V((math.cos(r), 0, math.sin(r)))
        ln = 0.8 if ang in (234, 306) else 0.72
        tip = c + d * ln
        if ang in (234, 306):
            tip.z = t + 0.07  # нижние лучи — опора
        kchain(a, "star", [c + d * 0.2, c + d * 0.5, tip], [0.36, 0.26, 0.13], [0.26, 0.2, 0.12], up=(0, -1, 0),
               overlap=0.4)
        for j in range(2):  # бугорки
            p = c + d * (0.35 + 0.18 * j) + V((0, -0.12 + 0.02 * j, 0))
            dot(a, "bump", p, (0, -1, 0), r=0.04)
        if ang not in (234, 306):  # монетка на кончике
            coin(a, tip + d * 0.08 + V((0, 0, 0.17)), (0, -1, 0), r=0.15, th=0.045, spin=15 * k)
    for s in S2:
        eye2(a, (s * 0.11, c.y - 0.16, c.z + 0.07), 0.07, (0, -1, 0), "goofy", s, "star", "starD")
    grin(a, (0, c.y - 0.17, c.z - 0.12), 0.16, h=0.05)
    face_point(a, (0, c.y - 0.17, c.z))
    closeup(a, (0.4, -0.1, c.z + 0.3))
    a.pose = {}
    return a


def zebra_tapir():
    """7. Тапир-зебра: спереди тапир с хоботком, сзади — зебра в золотых и чёрных полосах. Признаки: короткий хоботок,
    круглые уши с белой каймой, плотное тело, копытца; полосатый круп и хвост с кистью."""
    a = new("ZebraTapir", {"tap": ("3A3D4A", True), "zg": ("F5B21C", True), "zb": ("1E1E26", True),
                           "tapW": ("F4F4F8", False), "hoof": ("5E4636", False)})
    t = rare_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0.05, t + 0.8))
    quad_body(a, "tap", -0.45, 0.65, t + 0.8, 0.66, 0.62, keys=["tap", "tap", "zg", "zb", "zg", "zb"])
    for s in S2:
        for y0, k in ((-0.32, "tap"), (0.5, "zg")):
            leg(a, k, (s * 0.24, y0, t + 0.62), (s * 0.25, y0, t), 0.2, 0.15, hoof="hoof")
            if k == "zg":
                a.box("zb", s * 0.25 - 0.09, s * 0.25 + 0.09, y0 - 0.09, y0 + 0.09, t + 0.3, t + 0.4, bevel=0)
    part(a, "Tail", "Body", (0, 0.72, t + 0.9))
    kchain(a, "zg", [(0, 0.72, t + 0.95), (0, 0.85, t + 0.7)], [0.07, 0.06], up=(1, 0, 0))
    A.ball(a, "zb", (0, 0.87, t + 0.62), 0.09, n=2)
    part(a, "Head", "Body", (0, -0.55, t + 0.95))
    hc = V((0, -0.72, t + 0.98))
    th = A.body(a, "tap", (hc.x, hc.y, hc.z - 0.26), 0.27, 0.3, 0.5, "ball", n=3)
    fy = front_y(th, 0, hc.z - 0.05)
    kchain(a, "tap", [(0, fy + 0.08, hc.z - 0.08), (0, fy - 0.15, hc.z - 0.12), (0, fy - 0.24, hc.z - 0.26)],
           [0.16, 0.12, 0.1], up=(0, -1, 0))  # хоботок вниз
    for s in S2:
        eye2(a, (s * 0.13, front_y(th, s * 0.13, hc.z + 0.08) + 0.01, hc.z + 0.08), 0.06, (s * 0.4, -1, 0.1),
             "surprised", s, "tap", "tapW")
        A.ball(a, "tap", (s * 0.2, hc.y + 0.08, hc.z + 0.25), 0.1, n=2, ry=0.05)
        a.frame("tapW", S.octagon(s * 0.2 - 0.1, s * 0.2 + 0.1, hc.z + 0.15, hc.z + 0.35, 0.04), 0.03, hc.y + 0.02,
                hc.y + 0.05, axis="y", bevel=0)  # белая кайма уха
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.0, 0.3, t + 1.0))
    a.pose = {"Head": ((10, 0, 0), (0, 0, 0))}
    return a


def sniff_coati():
    """8. Носуха-нюхач: нос длиннее головы, всё время вертится — чует золото сквозь стены; хвост торчком, как антенна.
    Признаки: длинный подвижный нос-хоботок, светлые «очки» вокруг глаз, полосатый хвост торчком, длинные когти."""
    a = new("SniffCoati", {"coa": ("C8743A", True), "coaL": ("F6DDB5", False), "coaD": ("5A3218", False),
                           "claw": ("F3E9D2", False)})
    t = rare_stand(a, 1.55)
    part(a, "Body", "Stand", (0, 0.1, t + 0.6))
    quad_body(a, "coa", -0.35, 0.55, t + 0.62, 0.5, 0.48)
    a.prism("coaL", S.octagon(-0.18, 0.18, -0.3, 0.45, 0.06), t + 0.36, t + 0.4, bevel=0)  # светлое брюхо
    for s in S2:
        for y0 in (-0.25, 0.45):
            leg(a, "coa", (s * 0.2, y0, t + 0.5), (s * 0.22, y0, t), 0.15, 0.12)
            paw_claws(a, "claw", (s * 0.22, y0 - 0.07, t + 0.04), n=3, ln=0.11, w=0.04, spread=0.045)
    part(a, "Tail", "Body", (0, 0.6, t + 0.7))
    tp = [(0, 0.6, t + 0.75), (0, 0.66, t + 1.05), (0, 0.68, t + 1.35), (0, 0.67, t + 1.65), (0, 0.62, t + 1.95)]
    for i in range(len(tp) - 1):
        kchain(a, "coa" if i % 2 == 0 else "coaD", [tp[i], tp[i + 1]], [0.15 - 0.015 * i, 0.14 - 0.015 * i],
               up=(1, 0, 0))
    part(a, "Head", "Body", (0, -0.45, t + 0.75))
    hc = V((0, -0.55, t + 0.8))
    th = A.body(a, "coa", (hc.x, hc.y, hc.z - 0.22), 0.24, 0.24, 0.44, "ball", n=3)
    fy = front_y(th, 0, hc.z - 0.05)
    kchain(a, "coa", [(0, fy + 0.05, hc.z - 0.06), (0, fy - 0.25, hc.z - 0.08), (0, fy - 0.45, hc.z + 0.02),
                      (0.06, fy - 0.55, hc.z + 0.14)], [0.15, 0.11, 0.08, 0.07], up=(0, 0, 1))  # нос вверх-вбок
    A.ball(a, "coaD", (0.07, fy - 0.57, hc.z + 0.17), 0.06, n=2)
    for s in S2:
        x = s * 0.11
        a.prism("coaL", S.octagon(x - 0.08, x + 0.08, hc.z, hc.z + 0.15, 0.03), front_y(th, x, hc.z) - 0.02,
                front_y(th, x, hc.z) + 0.05, axis="y", bevel=0)  # светлые «очки»
        eye2(a, (x, front_y(th, x, hc.z + 0.07) - 0.01, hc.z + 0.07), 0.05, (s * 0.3, -1, 0), "sly", s, "coaL", "coaD",
             look=(0.5, 0.3))
        A.ball(a, "coa", (s * 0.15, hc.y + 0.06, hc.z + 0.2), 0.07, n=2, ry=0.04)
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.0, 0.2, t + 0.8))
    a.pose = {"Tail": ((0, 10, 0), (0, 0, 0)), "Head": ((0, 0, 12), (0, 0, 0))}
    return a


def gold_horn_kid():
    """9. Козлёнок-златорог: стоит всеми четырьмя копытцами на крошечной вершинке камня, а золотые рога закручены
    спиралью. Признаки: золотые рога-спирали, бородка, раздвоенные копытца, короткий хвостик, прямоугольные зрачки."""
    a = new("GoldHornKid", {"goat": ("F4F1EA", True), "goatB": ("D9C3A0", False), "gold": ("F5B21C", True),
                            "rock": ("8C8FA0", True), "rockD": ("6A6D7E", False), "hoof": ("5E4636", False)})
    t = rare_stand(a, 1.55)
    part(a, "Rock", "Stand", (0, 0, t))  # камень-вершинка — часть композиции
    a.frustum("rock", (-0.75, 0.75, -0.65, 0.7), (-0.18, 0.18, -0.16, 0.18), t, t + 0.75)
    a.frustum("rockD", (-0.45, 0.2, -0.75, -0.3), (-0.2, 0.0, -0.5, -0.4), t, t + 0.35)
    top = t + 0.75
    part(a, "Body", "Rock", (0, 0.0, top + 0.7))
    kchain(a, "goat", [(0, -0.3, top + 0.75), (0, 0.05, top + 0.78), (0, 0.38, top + 0.75)], [0.42, 0.46, 0.4],
           [0.4, 0.42, 0.36], up=(0, 0, 1))
    a.prism("goatB", S.octagon(-0.2, 0.2, -0.05, 0.3, 0.06), top + 0.94, top + 0.98, bevel=0)  # бежевое пятно
    for s in S2:  # все четыре ноги сходятся к вершинке
        for y0 in (-0.22, 0.3):
            leg(a, "goat", (s * 0.15, y0, top + 0.62), (s * 0.06, y0 * 0.25, top), 0.11, 0.08, hoof="hoof", hoof_h=0.07)
    part(a, "Tail", "Body", (0, 0.45, top + 0.85))
    spike(a, "goatB", (0, 0.45, top + 0.85), (0, 0.55, top + 1.05), 0.1)
    part(a, "Head", "Body", (0, -0.35, top + 0.95))
    hc = V((0, -0.45, top + 1.15))
    th = A.body(a, "goat", (hc.x, hc.y, hc.z - 0.22), 0.22, 0.24, 0.42, "ball", n=3)
    fy = front_y(th, 0, hc.z - 0.05)
    taper(a, "goat", (0, fy + 0.08, hc.z - 0.08), (0, fy - 0.12, hc.z - 0.14), 0.18, 0.13, 0.16, 0.12)
    spike(a, "goatB", (0, fy - 0.06, hc.z - 0.2), (0, fy - 0.1, hc.z - 0.38), 0.08)  # бородка
    for s in S2:
        x = s * 0.11
        y = front_y(th, x, hc.z + 0.05)
        a.box("white", x - 0.06, x + 0.06, y - 0.02, y + 0.04, hc.z + 0.01, hc.z + 0.09, bevel=0)
        a.box("dark", x - 0.045, x + 0.045, y - 0.035, y - 0.015, hc.z + 0.035, hc.z + 0.065, bevel=0)  # прямоугольный зрачок
        a.box("goat", x - 0.07, x + 0.07, y - 0.04, y + 0.03, hc.z + 0.08, hc.z + 0.11, bevel=0,
              matrix=tilt((x, y, hc.z + 0.1), "Y", -s * 12))  # дерзкая бровь
        A.ball(a, "goat", (s * 0.22, hc.y + 0.05, hc.z + 0.08), 0.07, n=2, ry=0.04)
        pts = [(s * 0.1, hc.y + 0.02, hc.z + 0.16)]  # золотые рога-спирали назад
        for k in range(7):
            g = math.radians(100 - 55 * k)
            r = 0.2 * (1 - 0.1 * k)
            pts.append((s * (0.14 + 0.025 * k), hc.y + 0.22 + r * math.cos(g), hc.z + 0.3 + r * math.sin(g)))
        kchain(a, "gold", pts, [0.1 - 0.008 * i for i in range(len(pts))], up=(1, 0, 0), overlap=0.4)
    grin(a, (0, fy - 0.12, hc.z - 0.17), 0.08, h=0.035)
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.0, -0.2, top + 0.6))
    a.pose = {"Head": ((-10, 0, 0), (0, 0, 0))}
    return a


_OWN = {"HandstandSkunk": handstand_skunk, "CapeRatel": cape_ratel, "JugglerStarfish": juggler_starfish,
        "ZebraTapir": zebra_tapir, "SniffCoati": sniff_coati, "GoldHornKid": gold_horn_kid}
ORDER = [("PouchKangaroo", SK.pouch_kangaroo, "Кенгуру-кубышка", "Rare"),
         ("GemArmadillo", SK.gem_armadillo, "Броненосец-самоцвет", "Rare"),
         ("PearlOtter", SK.pearl_otter, "Выдра-жемчужница", "Rare"),
         ("HandstandSkunk", None, "Скунс-стойка", "Rare"), ("CapeRatel", None, "Медоед-плащ", "Rare"),
         ("JugglerStarfish", None, "Морская звезда-жонглёр", "Rare"), ("ZebraTapir", None, "Тапир-зебра", "Rare"),
         ("SniffCoati", None, "Носуха-нюхач", "Rare"), ("GoldHornKid", None, "Козлёнок-златорог", "Rare")]
ITEMS = collect(ORDER, _OWN)
