"""Коллекция «Банк» босса 7 — Epic (каталог docs/BOSS7_CATALOG.md, D73). 2 утверждённых эскиза — из boss7/creatures.py,
4 новых — здесь."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bank_kit import *  # noqa: E402,F401,F403


def mirror_morpho():
    """3. Морфо-зеркальце: крылья синие и блестят, как зеркало, — бабочка любуется в них собой, а тельце крошечное.
    Признаки: две пары крыльев с тёмной каймой и белыми точками, тонкое тельце, булавовидные усики, хоботок-спираль."""
    a = new("MirrorMorpho", {"mor": ("1E2430", True), "morB": ("2E7BFF", False), "morL": ("8FD0FF", False),
                             "morK": ("101422", False)})
    t = epic_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0.1, t + 0.6))
    kchain(a, "mor", [(0, -0.1, t + 0.62), (0, 0.15, t + 0.6), (0, 0.55, t + 0.52)], [0.16, 0.14, 0.08],
           [0.16, 0.14, 0.08], up=(0, 0, 1))  # грудь и брюшко
    for s in S2:
        for k in range(3):
            y = -0.05 + 0.13 * k
            A.limb(a, "mor", [(s * 0.05, y, t + 0.58), (s * 0.2, y - 0.05, t + 0.35), (s * 0.24, y - 0.08, t + 0.02)],
                   [0.035, 0.03, 0.025], joints=False)
        part(a, "Wing" + ("L" if s > 0 else "R"), "Body", (s * 0.06, 0.05, t + 0.66))
        for front, (pts, ang) in enumerate((([(0, 0), (1.15, 0.45), (1.3, -0.05), (0.7, -0.38), (0, -0.12)], 62),
                                            ([(0, 0), (0.88, -0.25), (0.76, -0.8), (0.25, -0.7), (0, -0.18)], 52))):
            yo = -0.02 if front == 0 else 0.25
            m = Matrix.Translation((s * 0.06, yo, t + 0.66)) @ Matrix.Rotation(math.radians(-s * ang), 4, "Y")
            q = [(s * x, -y) for x, y in pts]  # y модели: «назад» положительное
            if s < 0:
                q = list(reversed(q))
            a.extrude("morK", q, -0.02, 0.0, axis="z", matrix=m)  # тёмная кайма — чуть больше крыла
            inner = [(px * 0.86 + s * 0.02, py * 0.86 - 0.01) for px, py in q]
            a.extrude("morB", inner, 0.0, 0.025, axis="z", matrix=m)  # зеркально-синее крыло (сверху и снизу)
            a.extrude("morB", inner, -0.045, -0.02, axis="z", matrix=m)
            a.extrude("morL", [(px * 0.5 + s * 0.08, py * 0.5) for px, py in q], -0.06, -0.045, axis="z", matrix=m)
            shine = [(px * 0.5 + s * 0.08, py * 0.5) for px, py in q]
            a.extrude("morL", shine, 0.025, 0.04, axis="z", matrix=m)  # блик
            for px, py in q[1:-1]:
                a.box("white", px * 0.93 - 0.025, px * 0.93 + 0.025, py * 0.93 - 0.025, py * 0.93 + 0.025, 0.0,
                      0.012, bevel=0, matrix=m)  # белые точки на кайме
        a.group = "Body"
    part(a, "Head", "Body", (0, -0.15, t + 0.65))
    hc = V((0, -0.24, t + 0.68))
    th = A.body(a, "mor", (hc.x, hc.y, hc.z - 0.1), 0.11, 0.11, 0.2, "ball", n=2)
    for s in S2:
        kchain(a, "mor", [(s * 0.04, hc.y - 0.05, hc.z + 0.08), (s * 0.12, hc.y - 0.2, hc.z + 0.35),
                          (s * 0.16, hc.y - 0.26, hc.z + 0.55)], [0.025, 0.022, 0.02], up=(0, -1, 0))  # усики
        A.ball(a, "mor", (s * 0.165, hc.y - 0.27, hc.z + 0.58), 0.045, n=2)  # булавы
        eye2(a, (s * 0.05, hc.y - 0.1, hc.z + 0.03), 0.04, (s * 0.4, -1, 0), "sly", s, "mor", "morL")
    kchain(a, "morK", [(0, hc.y - 0.1, hc.z - 0.05), (0, hc.y - 0.18, hc.z - 0.15), (0, hc.y - 0.12, hc.z - 0.22)],
           [0.02, 0.02, 0.02], up=(0, -1, 0))  # хоботок-спираль
    face_point(a, (0, hc.y - 0.1, hc.z))
    closeup(a, (0.5, 0.1, t + 0.8))
    a.pose = {"WingL": ((0, -12, 0), (0, 0, 0)), "WingR": ((0, 12, 0), (0, 0, 0))}
    return a


def veil_goldfish():
    """4. Рыбка-златовуаль: плавники-вуали вчетверо больше тела, висит над всплеском воды, как золотое облачко.
    Признаки: круглое тело, вуалевые хвост и плавники, крупная чешуя, большие глаза, рот-«о»."""
    a = new("VeilGoldfish", {"gf": ("FF9A1E", True), "gfL": ("FFD86E", False), "fin": ("FFE6C6", False),
                             "finO": ("FFB45A", False), "water": ("3BA7E0", True), "foam": ("E6F7FF", False)})
    t = epic_stand(a, 1.6)
    part(a, "Splash", "Stand", (0, 0, t))  # всплеск воды — часть композиции
    a.prism("water", S.octagon(-0.8, 0.8, -0.8, 0.8, 0.3), t, t + 0.12, bevel=0)
    kchain(a, "water", [(0, 0.1, t + 0.1), (0.05, 0.12, t + 0.5), (0, 0.08, t + 0.85)], [0.36, 0.24, 0.18],
           up=(0, -1, 0))  # водяной столбик держит рыбку
    for k, ang in enumerate(range(0, 360, 60)):
        r = math.radians(ang)
        spike(a, "foam", (0.42 * math.cos(r), 0.42 * math.sin(r), t + 0.08), (0.58 * math.cos(r), 0.58 * math.sin(r),
                                                                               t + 0.3 + 0.05 * (k % 2)), 0.12)
    part(a, "Body", "Splash", (0, 0.05, t + 1.15))
    bc = V((0, 0.0, t + 1.15))
    tb = A.body(a, "gf", (bc.x, bc.y, bc.z - 0.33), 0.32, 0.42, 0.66, "ball", n=4)
    dots_on_ball(a, "gfL", bc, 0.32, 0.42, 0.33, [(az, el) for el in (-0.3, 0.2) for az in (60, 100, 140, 220, 260, 300)],
                 r=0.06)  # крупная чешуя
    for s in S2:  # грудные вуали
        a.extrude("fin", [(0, 0), (s * 0.55, -0.15), (s * 0.7, 0.25), (s * 0.3, 0.3)], -0.02, 0.02, axis="y",
                  matrix=Matrix.Translation((s * 0.25, -0.05, bc.z - 0.15)))
    kchain(a, "finO", [(0, 0.05, bc.z + 0.3), (0, 0.25, bc.z + 0.52), (0, 0.5, bc.z + 0.48)], [0.05, 0.05, 0.04],
           [0.3, 0.32, 0.2], up=(1, 0, 0))  # спинной плавник
    part(a, "Tail", "Body", (0, 0.4, bc.z))
    for s in S2:  # хвост-вуаль: две огромные лопасти вниз-назад
        a.extrude("fin", [(0, 0), (0.25, -0.35), (0.25, -0.95), (0.55, -1.15), (0.6, -0.4)], -0.025, 0.025, axis="x",
                  matrix=Matrix.Translation((s * 0.08, 0.35, bc.z + 0.1)) @ Matrix.Rotation(math.radians(s * 14), 4, "Z"))
        a.extrude("finO", [(0.05, -0.05), (0.2, -0.32), (0.22, -0.8), (0.42, -0.95), (0.48, -0.38)], 0.025, 0.04,
                  axis="x", matrix=Matrix.Translation((s * 0.08, 0.35, bc.z + 0.1)) @
                  Matrix.Rotation(math.radians(s * 14), 4, "Z"))
    part(a, "Head", "Body", (0, -0.3, bc.z))
    fy = front_y(tb, 0, bc.z)
    for s in S2:
        eye2(a, (s * 0.14, front_y(tb, s * 0.14, bc.z + 0.08) + 0.03, bc.z + 0.08), 0.09, (s * 0.5, -1, 0.05), "sly",
             s, "gf", "finO", look=(0, 0.3))
    a.frame("mouth", S.octagon(-0.07, 0.07, bc.z - 0.18, bc.z - 0.05, 0.03), 0.03, fy - 0.03, fy + 0.04, axis="y",
            bevel=0)  # рот-«о»
    face_point(a, (0, fy, bc.z))
    closeup(a, (0.3, 0.4, bc.z - 0.2))
    a.pose = {"Tail": ((0, 0, 12), (0, 0, 0))}
    return a


def gold_tooth_hippo():
    """5. Бегемот-златозуб: улыбается во всю пасть, чтобы все видели один золотой зуб; крошечные ушки крутятся от
    гордости. Признаки: огромная широкая морда, ноздри и глаза на макушке, крошечные уши, бочкообразное тело, ноги."""
    a = new("GoldToothHippo", {"hip": ("A98AD8", True), "hipL": ("D8C6F2", False), "hipD": ("6E52A8", False),
                               "gold": ("F5B21C", False), "inner": ("FF8FB2", False)})
    t = epic_stand(a, 1.65)
    part(a, "Body", "Stand", (0, 0.1, t + 0.75))
    kchain(a, "hip", [(0, -0.55, t + 0.8), (0, 0.1, t + 0.8), (0, 0.6, t + 0.74)], [1.02, 1.12, 0.95],
           [0.82, 0.88, 0.76], up=(0, 0, 1), overlap=0.5)  # бочка (перёд заходит под голову)
    for s in S2:
        for y0 in (-0.25, 0.48):
            leg(a, "hip", (s * 0.36, y0, t + 0.5), (s * 0.38, y0, t), 0.3, 0.28, hoof="hipD", hoof_h=0.08)
    part(a, "Tail", "Body", (0, 0.72, t + 0.85))
    spike(a, "hipD", (0, 0.72, t + 0.85), (0, 0.9, t + 0.75), 0.08)
    part(a, "Head", "Body", (0, -0.6, t + 0.95))
    hz = t + 1.0
    kchain(a, "hip", [(0, -0.45, hz + 0.05), (0, -0.88, hz + 0.08)], [0.85, 0.9], [0.62, 0.6], up=(0, 0, 1))  # голова на шее
    # морда: открытая пасть — верхняя и нижняя челюсти, розовое нутро, золотой зуб и два белых клычка
    a.prism("hip", S.octagon(-0.48, 0.48, -1.35, -0.85, 0.15), hz + 0.08, hz + 0.34, bevel=0.01)  # верхняя челюсть
    a.prism("hip", S.octagon(-0.46, 0.46, -1.3, -0.85, 0.15), hz - 0.36, hz - 0.18, bevel=0.01)  # нижняя
    a.prism("inner", S.octagon(-0.38, 0.38, -1.24, -0.9, 0.1), hz - 0.2, hz + 0.1, bevel=0)  # пасть
    a.box("tongue", -0.26, 0.26, -1.2, -0.95, hz - 0.19, hz - 0.12, bevel=0)
    a.box("gold", 0.08, 0.2, -1.3, -1.2, hz - 0.04, hz + 0.09, bevel=0)  # золотой зуб сверху
    for s in S2:
        a.box("white", s * 0.36 - 0.05, s * 0.36 + 0.05, -1.25, -1.17, hz - 0.18, hz - 0.06, bevel=0)  # клычки
        a.box("hipD", s * 0.17 - 0.05, s * 0.17 + 0.05, -1.25, -1.15, hz + 0.32, hz + 0.36, bevel=0)  # ноздри сверху
        A.ball(a, "hip", (s * 0.24, -0.78, hz + 0.42), 0.12, n=2)  # бугры глаз на макушке
        eye2(a, (s * 0.24, -0.89, hz + 0.44), 0.07, (s * 0.2, -1, 0.3), "proud", s, "hip", "hipD")
        A.ball(a, "hipL", (s * 0.36, -0.62, hz + 0.45), 0.06, n=2)  # крошечные уши
    face_point(a, (0, -1.2, hz))
    closeup(a, (0.0, 0.0, t + 1.0))
    a.pose = {"Head": ((-8, 0, 0), (0, 0, 0))}
    return a


def bead_gila():
    """6. Ядозуб-бусинка: чешуя — бусины золота и оникса, а «сбережения» он копит в хвосте: хвост толще туловища.
    Признаки: бисерная чешуя узором, толстый короткий хвост-запас, широкая голова, короткие лапы с когтями."""
    a = new("BeadGila", {"gil": ("F08A24", True), "gilD": ("1E1E26", True), "bead": ("FFC55A", False),
                         "beadD": ("3A3A48", False), "claw": ("F3E9D2", False)})
    t = epic_stand(a, 1.65)
    part(a, "Body", "Stand", (0, 0.1, t + 0.3))
    keys = ["gil", "gilD", "gil", "gilD"]
    pts = [(0, -0.4, t + 0.3), (0, -0.05, t + 0.32), (0, 0.3, t + 0.32), (0, 0.6, t + 0.3)]
    for i in range(3):
        kchain(a, keys[i], [pts[i], pts[i + 1]], [0.52, 0.5], [0.36, 0.35], up=(0, 0, 1))
    for i in range(10):  # бусины на спине
        y = -0.35 + 0.1 * i
        for x in (-0.12, 0.12):
            dot(a, "bead" if (i + (x > 0)) % 2 else "beadD", (x, y, t + 0.48), (0, 0, 1), r=0.045, h=0.03)
    for s in S2:
        for y0 in (-0.25, 0.45):
            A.limb(a, "gil", [(s * 0.22, y0, t + 0.25), (s * 0.4, y0 - 0.03, t + 0.12), (s * 0.45, y0 - 0.1, t + 0.04)],
                   [0.12, 0.1, 0.09])
            paw_claws(a, "claw", (s * 0.45, y0 - 0.15, t + 0.04), n=3, ln=0.08, w=0.035, spread=0.04)
    part(a, "Tail", "Body", (0, 0.6, t + 0.3))
    kchain(a, "gil", [(0, 0.6, t + 0.3), (0, 0.95, t + 0.28), (0.15, 1.25, t + 0.24), (0.3, 1.4, t + 0.2)],
           [0.62, 0.66, 0.5, 0.2], [0.42, 0.44, 0.34, 0.16], up=(0, 0, 1), overlap=0.5)  # толстый хвост-запас
    for k in range(3):
        y = 0.75 + 0.18 * k
        dot(a, "gilD", (0.02 * k, y, t + 0.5), (0, 0, 1), r=0.1, h=0.02)
    part(a, "Head", "Body", (0, -0.45, t + 0.35))
    hc = V((0, -0.62, t + 0.36))
    th = A.body(a, "gilD", (hc.x, hc.y, hc.z - 0.17), 0.3, 0.26, 0.34, "ball", n=3)
    fy = front_y(th, 0, hc.z)
    for s in S2:
        eye2(a, (s * 0.15, front_y(th, s * 0.15, hc.z + 0.07) + 0.01, hc.z + 0.07), 0.055, (s * 0.4, -1, 0.1), "sly",
             s, "gilD", "bead")
        dot(a, "bead", (s * 0.12, hc.y + 0.05, hc.z + 0.17), (0, 0, 1), r=0.04)
    grin(a, (0, fy - 0.01, hc.z - 0.07), 0.24, h=0.04, key="bead")
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.0, 0.3, t + 0.4))
    a.pose = {"Tail": ((0, 0, 15), (0, 0, 0)), "Head": ((-10, 0, 0), (0, 0, 0))}
    return a


_OWN = {"MirrorMorpho": mirror_morpho, "VeilGoldfish": veil_goldfish, "GoldToothHippo": gold_tooth_hippo,
        "BeadGila": bead_gila}
ORDER = [("GoldenPheasant", SK.golden_pheasant, "Фазан-златовлас", "Epic"),
         ("FleeceAlpaca", SK.fleece_alpaca, "Альпака-золотое руно", "Epic"),
         ("MirrorMorpho", None, "Морфо-зеркальце", "Epic"), ("VeilGoldfish", None, "Рыбка-златовуаль", "Epic"),
         ("GoldToothHippo", None, "Бегемот-златозуб", "Epic"), ("BeadGila", None, "Ядозуб-бусинка", "Epic")]
ITEMS = collect(ORDER, _OWN)
