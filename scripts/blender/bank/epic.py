"""Коллекция «Банк» босса 7 — Epic (каталог docs/BOSS7_CATALOG.md, D73). 2 утверждённых эскиза — из boss7/creatures.py,
4 новых — здесь."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bank_kit import *  # noqa: E402,F401,F403


def mirror_morpho():
    """3. Морфо-зеркальце: крылья синие и блестят, как зеркало, — бабочка любуется в них собой. Признаки: две пары
    широких скруглённых крыльев с тёмной каймой и белыми точками, толстенькое тельце, булавовидные усики, хоботок.
    v2 (владелец 2026-11-26): классическая бабочка — 4 широких скруглённых крыла раскрыты в стороны, тело толще,
    ноги короткие."""
    a = new("MirrorMorpho", {"mor": ("2A3044", True), "morB": ("2E7BFF", False), "morL": ("8FD0FF", False),
                             "morK": ("101422", False)})
    t = epic_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0.05, t + 0.32))
    A.ball(a, "mor", (0, -0.02, t + 0.36), 0.18, n=3)  # грудь
    kchain(a, "mor", [(0, 0.12, t + 0.34), (0, 0.42, t + 0.3), (0, 0.66, t + 0.26)], [0.24, 0.2, 0.1],
           [0.22, 0.18, 0.09], up=(0, 0, 1))  # брюшко
    for s in S2:  # короткие ножки
        for k in range(3):
            y = -0.08 + 0.1 * k
            A.limb(a, "mor", [(s * 0.1, y, t + 0.3), (s * 0.2, y - 0.03, t + 0.14), (s * 0.24, y - 0.05, t + 0.02)],
                   [0.045, 0.04, 0.035], joints=False)
    fore = [(0.0, -0.1), (0.2, -0.55), (0.58, -0.82), (0.95, -0.72), (1.06, -0.36), (0.9, 0.04), (0.42, 0.12)]
    hind = [(0.0, 0.1), (0.36, 0.14), (0.8, 0.34), (0.92, 0.7), (0.66, 1.0), (0.26, 0.9), (0.05, 0.46)]  # широкие, скруглённые
    for s in S2:
        nm = "Wing" + ("L" if s > 0 else "R")
        root = V((s * 0.1, 0.0, t + 0.4))
        part(a, nm, "Body", tuple(root))
        A.ball(a, "mor", tuple(root), 0.1, n=2)
        for k, shape in enumerate((fore, hind)):
            m = Matrix.Translation(root + V((0, 0, 0.01 * k))) @ Matrix.Rotation(math.radians(-s * (26 - 6 * k)), 4, "Y")
            q = [(s * x, -y) for x, y in shape]
            if s < 0:
                q = list(reversed(q))
            cx = sum(p[0] for p in q) / len(q)
            cy = sum(p[1] for p in q) / len(q)
            inner = [(cx + (px - cx) * 0.84, cy + (py - cy) * 0.84) for px, py in q]
            shine = [(cx + (px - cx) * 0.45 - s * 0.05, cy + (py - cy) * 0.45) for px, py in q]
            a.extrude("morK", q, -0.02, 0.0, axis="z", matrix=m)  # тёмная кайма
            a.extrude("morB", inner, 0.0, 0.025, axis="z", matrix=m)  # зеркально-синее крыло сверху
            a.extrude("morB", inner, -0.045, -0.02, axis="z", matrix=m)  # и снизу
            a.extrude("morL", shine, 0.025, 0.04, axis="z", matrix=m)  # блик-«зеркало»
            for px, py in q[1:-1]:  # белые точки на кайме
                x, y = cx + (px - cx) * 0.93, cy + (py - cy) * 0.93
                a.box("white", x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 0.012, bevel=0, matrix=m)
        a.group = "Body"
    part(a, "Head", "Body", (0, -0.15, t + 0.4))
    A.ball(a, "mor", (0, -0.16, t + 0.4), 0.1, n=2)
    hc = V((0, -0.27, t + 0.42))
    A.ball(a, "mor", tuple(hc), 0.14, n=3)
    for s in S2:
        kchain(a, "mor", [(s * 0.05, hc.y - 0.05, hc.z + 0.1), (s * 0.15, hc.y - 0.18, hc.z + 0.34),
                          (s * 0.2, hc.y - 0.24, hc.z + 0.5)], [0.03, 0.026, 0.022], up=(0, -1, 0))  # усики
        A.ball(a, "mor", (s * 0.205, hc.y - 0.25, hc.z + 0.54), 0.05, n=2)  # булавы
        eye2(a, (s * 0.06, hc.y - 0.12, hc.z + 0.03), 0.05, (s * 0.4, -1, 0), "sly", s, "mor", "morL")
    kchain(a, "morK", [(0, hc.y - 0.12, hc.z - 0.06), (0, hc.y - 0.2, hc.z - 0.14), (0, hc.y - 0.13, hc.z - 0.2)],
           [0.025, 0.025, 0.025], up=(0, -1, 0))  # хоботок-спираль
    face_point(a, (0, hc.y - 0.12, hc.z))
    closeup(a, (0.6, 0.1, t + 0.45))
    a.pose = {"WingL": ((0, -12, 0), (0, 0, 0)), "WingR": ((0, 12, 0), (0, 0, 0))}
    return a


def ribbon(a, key, p0, p1, sag, wave, w0, w1, up, n=8):
    """Вуаль: длинная плоская лента от p0 к p1, плавно провисает на sag (вектор) и мягко волнится на wave (вектор),
    n звеньев по синусу — без изломов «молнией»; ширина w0 → w1, толщина 0.03."""
    a0, a1, sg, wv = V(p0), V(p1), V(sag), V(wave)
    pts = [a0.lerp(a1, i / n) + sg * math.sin(math.pi * i / n) + wv * math.sin(2 * math.pi * i / n) for i in range(n + 1)]
    kchain(a, key, pts, [w0 + (w1 - w0) * i / n for i in range(n + 1)], [0.03] * (n + 1), up=up, overlap=0.3)


def veil_goldfish():
    """4. Рыбка-златовуаль: плавники-вуали вчетверо больше тела — висит над всплеском, как золотое облачко.
    Признаки: круглое тело, вуалевые хвост и плавники, крупная чешуя, большие глаза, рот-«о».
    v2 (владелец 2026-11-26): цельная круглая рыбка над всплеском (не «леденец на палочке»); вуали — длинные волнистые
    полупрозрачные ленты, хвост развёрнут к игроку."""
    a = new("VeilGoldfish", {"gf": ("FF9A1E", True), "gfL": ("FFD86E", False), "fin": ("FFD9A8", False),
                             "finO": ("FF8A3A", False), "water": ("3BA7E0", True), "foam": ("E6F7FF", False)})
    a.transparent_parts = ("Fins",)
    t = epic_stand(a, 1.6)
    part(a, "Splash", "Stand", (0, 0, t))  # всплеск — широкий бугор воды с пеной, не столбик
    a.prism("water", S.octagon(-0.85, 0.85, -0.85, 0.85, 0.3), t, t + 0.12, bevel=0)
    A.body(a, "water", (0, 0.05, t + 0.1), 0.55, 0.55, 0.42, "dome", n=4)
    for k, ang in enumerate(range(0, 360, 45)):
        r = math.radians(ang)
        spike(a, "foam", (0.48 * math.cos(r), 0.05 + 0.48 * math.sin(r), t + 0.12),
              (0.66 * math.cos(r), 0.05 + 0.66 * math.sin(r), t + 0.38 + 0.08 * (k % 2)), 0.14)
    part(a, "Body", "Splash", (0, 0.05, t + 0.9))
    bc = V((0, 0.05, t + 0.92))
    round_ball(a, ["gf"], bc, 0.44, n=10)  # цельное круглое тело (16-гранные ярусы)
    dots_on_ball(a, "gfL", bc, 0.45, 0.45, 0.44, [(az, el) for el in (-0.3, 0.15, 0.5) for az in
                                                  (50, 90, 130, 230, 270, 310)], r=0.06)  # крупная чешуя
    fy = bc.y - 0.44
    part(a, "Fins", "Body", (0, 0.05, t + 0.92))  # вуали — полупрозрачная часть
    for s in S2:  # грудные вуали: длинные ленты свисают волной по бокам
        ribbon(a, "fin", (s * 0.4, -0.05, bc.z - 0.1), (s * 0.78, 0.15, bc.z - 0.42), (s * 0.04, 0, -0.08),
               (0, 0.05, 0.04), 0.32, 0.2, up=(s, 0, 0.6), n=5)  # грудные вуали короче, веером
        # хвост-вуаль развёрнут к игроку: широкие ленты из-за спины вверх-вбок и вниз
        ribbon(a, "fin", (s * 0.05, 0.46, bc.z + 0.05), (s * 0.95, 1.0, bc.z - 0.15), (0, 0.0, 0.3),
               (0, 0.04, 0.06), 0.46, 0.28, up=(0, -1, 0.4))  # хвост-вуаль веером назад и в стороны
        ribbon(a, "finO", (s * 0.05, 0.5, bc.z - 0.12), (s * 0.62, 0.95, bc.z - 0.72), (s * 0.1, 0.05, 0.05),
               (0, 0.04, 0.06), 0.36, 0.16, up=(0, -1, 0.2))  # нижние ленты хвоста
    ribbon(a, "finO", (0, -0.08, bc.z + 0.38), (0, 0.68, bc.z + 0.5), (0, 0, 0.22), (0, 0, 0.04), 0.3, 0.18,
           up=(1, 0, 0))  # спинной плавник-парус
    a.group = "Body"
    part(a, "Head", "Body", (0, -0.3, bc.z))
    for s in S2:
        eye2(a, (s * 0.2, fy + 0.07, bc.z + 0.1), 0.1, (s * 0.45, -1, 0.05), "sly", s, "gf", "finO", look=(0, 0.3))
    a.frame("mouth", S.octagon(-0.08, 0.08, bc.z - 0.2, bc.z - 0.05, 0.03), 0.035, fy - 0.03, fy + 0.06, axis="y",
            bevel=0)  # рот-«о»
    face_point(a, (0, fy, bc.z))
    closeup(a, (0.3, 0.4, bc.z - 0.2))
    a.pose = {"Fins": ((0, 0, 8), (0, 0, 0))}
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
    Признаки: бисерная чешуя узором, толстый короткий хвост-запас, широкая голова, короткие лапы с когтями.
    v2 (владелец 2026-11-26): голова поднята, сам крупнее на плите."""
    a = new("BeadGila", {"gil": ("F08A24", True), "gilD": ("1E1E26", True), "bead": ("FFC55A", False),
                         "beadD": ("3A3A48", False), "claw": ("F3E9D2", False)})
    t = epic_stand(a, 1.65)
    part(a, "Body", "Stand", (0, 0.1, t + 0.38))
    keys = ["gil", "gilD", "gil", "gilD"]
    pts = [(0, -0.5, t + 0.42), (0, -0.08, t + 0.4), (0, 0.32, t + 0.4), (0, 0.68, t + 0.37)]
    for i in range(3):
        kchain(a, keys[i], [pts[i], pts[i + 1]], [0.64, 0.62], [0.44, 0.43], up=(0, 0, 1))
    for i in range(10):  # бусины на спине
        y = -0.45 + 0.12 * i
        for x in (-0.15, 0.15):
            dot(a, "bead" if (i + (x > 0)) % 2 else "beadD", (x, y, t + 0.6), (0, 0, 1), r=0.055, h=0.035)
    for s in S2:
        for y0 in (-0.32, 0.52):
            A.limb(a, "gil", [(s * 0.27, y0, t + 0.32), (s * 0.48, y0 - 0.03, t + 0.15), (s * 0.54, y0 - 0.12, t + 0.05)],
                   [0.15, 0.13, 0.11])
            paw_claws(a, "claw", (s * 0.54, y0 - 0.18, t + 0.05), n=3, ln=0.1, w=0.04, spread=0.05)
    part(a, "Tail", "Body", (0, 0.7, t + 0.38))
    A.ball(a, "gil", (0, 0.7, t + 0.38), 0.22, n=2)
    kchain(a, "gil", [(0, 0.7, t + 0.38), (0, 1.1, t + 0.34), (0.18, 1.42, t + 0.28), (0.36, 1.58, t + 0.22)],
           [0.74, 0.78, 0.6, 0.24], [0.5, 0.52, 0.4, 0.18], up=(0, 0, 1), overlap=0.5)  # толстый хвост-запас
    for k in range(3):
        dot(a, "gilD", (0.02 * k, 0.88 + 0.2 * k, t + 0.62), (0, 0, 1), r=0.12, h=0.02)
    part(a, "Head", "Body", (0, -0.6, t + 0.5))
    A.ball(a, "gilD", (0, -0.62, t + 0.52), 0.24, n=2)  # шея
    hc = V((0, -0.86, t + 0.72))  # голова поднята
    th = A.body(a, "gilD", (hc.x, hc.y, hc.z - 0.2), 0.36, 0.31, 0.4, "ball", n=3)
    fy = front_y(th, 0, hc.z)
    for s in S2:
        eye2(a, (s * 0.18, front_y(th, s * 0.18, hc.z + 0.08) + 0.01, hc.z + 0.08), 0.065, (s * 0.4, -1, 0.1), "sly",
             s, "gilD", "bead")
        dot(a, "bead", (s * 0.14, hc.y + 0.06, hc.z + 0.2), (0, 0, 1), r=0.05)
    grin(a, (0, fy - 0.01, hc.z - 0.08), 0.28, h=0.045, key="bead")
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.0, 0.3, t + 0.5))
    a.pose = {"Tail": ((0, 0, 15), (0, 0, 0)), "Head": ((-10, 0, 0), (0, 0, 0))}
    return a


_OWN = {"MirrorMorpho": mirror_morpho, "VeilGoldfish": veil_goldfish, "GoldToothHippo": gold_tooth_hippo,
        "BeadGila": bead_gila}
ORDER = [("GoldenPheasant", SK.golden_pheasant, "Фазан-златовлас", "Epic"),
         ("FleeceAlpaca", SK.fleece_alpaca, "Альпака-золотое руно", "Epic"),
         ("MirrorMorpho", None, "Морфо-зеркальце", "Epic"), ("VeilGoldfish", None, "Рыбка-златовуаль", "Epic"),
         ("GoldToothHippo", None, "Бегемот-златозуб", "Epic"), ("BeadGila", None, "Ядозуб-бусинка", "Epic")]
ITEMS = collect(ORDER, _OWN)
