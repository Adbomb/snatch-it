"""Коллекция «Банк» босса 7 — Legendary (каталог docs/BOSS7_CATALOG.md, D73). Грифон-казначей — из boss7/creatures.py
(v3 по правкам владельца: четвероногий, лежит на монетах, хвост обвивает горку), 2 новых — здесь."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bank_kit import *  # noqa: E402,F401,F403


def sapphire_tiger():
    """2. Тигр-сапфир: белый тигр, у которого полосы синие, как сапфиры, и мягко светятся; ступает важно, задрав хвост.
    Признаки: мощные плечи и лапы, круглые уши с белым пятном, белые бакенбарды, длинный полосатый хвост, розовый нос."""
    a = new("SapphireTiger", {"tig": ("F4F6FB", True), "tigD": ("2A2D3A", False), "neonS": ("2E6BFF", False),
                              "nose": ("FF8FB2", False), "tigL": ("DDE3F0", False)})
    glow(a, 1.6)
    t = legendary_stand(a, 1.7)
    part(a, "Body", "Stand", (0, 0.1, t + 1.0))
    kchain(a, "tig", [(0, -0.5, t + 1.05), (0, 0.1, t + 1.0), (0, 0.65, t + 0.98)], [0.72, 0.66, 0.62],
           [0.66, 0.6, 0.58], up=(0, 0, 1), overlap=0.5)
    for k in range(6):  # сапфировые полосы-шевроны по спине и бокам
        y = -0.35 + 0.18 * k
        for s in S2:
            kchain(a, "neonS", [(0, y, t + 1.35), (s * 0.3, y + 0.06, t + 1.25), (s * 0.36, y + 0.1, t + 0.98)],
                   [0.07, 0.07, 0.06], [0.05, 0.05, 0.05], up=(s * 0.5, 0, 1))
    for s in S2:
        leg(a, "tig", (s * 0.27, 0.5, t + 0.85), (s * 0.29, 0.52, t), 0.26, 0.22)
        A.ball(a, "tig", (s * 0.29, 0.44, t + 0.08), 0.13, n=2)
    part(a, "ArmL", "Body", (0.28, -0.45, t + 0.85))  # правая передняя ступает вперёд, поднята
    A.limb(a, "tig", [(0.28, -0.45, t + 0.9), (0.3, -0.7, t + 0.5), (0.3, -0.82, t + 0.28)], [0.28, 0.24, 0.22])
    A.ball(a, "tig", (0.3, -0.88, t + 0.24), 0.14, n=2)
    part(a, "ArmR", "Body", (-0.28, -0.45, t + 0.85))
    leg(a, "tig", (-0.28, -0.45, t + 0.9), (-0.29, -0.5, t), 0.28, 0.23)
    A.ball(a, "tig", (-0.29, -0.58, t + 0.08), 0.14, n=2)
    part(a, "Tail", "Body", (0, 0.75, t + 1.1))
    tp = [(0, 0.75, t + 1.1), (0, 1.0, t + 1.3), (0, 1.05, t + 1.65), (0, 0.85, t + 1.9), (0, 0.65, t + 1.85)]
    for i in range(len(tp) - 1):  # хвост с сапфировыми кольцами
        kchain(a, "tig" if i % 2 == 0 else "neonS", [tp[i], tp[i + 1]], [0.13, 0.12], up=(1, 0, 0))
    part(a, "Head", "Body", (0, -0.6, t + 1.25))
    hc = V((0, -0.82, t + 1.4))
    th = A.body(a, "tig", (hc.x, hc.y, hc.z - 0.32), 0.38, 0.34, 0.62, "ball", n=4)
    fy = front_y(th, 0, hc.z - 0.05)
    taper(a, "tigL", (0, fy + 0.08, hc.z - 0.12), (0, fy - 0.12, hc.z - 0.14), 0.3, 0.24, 0.2, 0.17)  # морда
    a.box("nose", -0.06, 0.06, fy - 0.15, fy - 0.1, hc.z - 0.08, hc.z - 0.02, bevel=0)
    a.box("tigD", -0.006, 0.006, fy - 0.15, fy - 0.12, hc.z - 0.2, hc.z - 0.08, bevel=0)
    for s in S2:
        eye2(a, (s * 0.15, front_y(th, s * 0.15, hc.z + 0.08) + 0.02, hc.z + 0.08), 0.075, (s * 0.3, -1, 0),
             "calm", s, "tig", "tigD", lid=0.3)
        A.ball(a, "tig", (s * 0.26, hc.y + 0.08, hc.z + 0.3), 0.11, n=2, ry=0.06)  # круглые уши
        a.prism("tigD", S.octagon(s * 0.26 - 0.08, s * 0.26 + 0.08, hc.z + 0.24, hc.z + 0.38, 0.03), hc.y + 0.13,
                hc.y + 0.15, axis="y", bevel=0)  # тёмная спинка уха
        a.prism("white", S.octagon(s * 0.26 - 0.035, s * 0.26 + 0.035, hc.z + 0.28, hc.z + 0.34, 0.01), hc.y + 0.15,
                hc.y + 0.16, axis="y", bevel=0)  # белое пятно
        spike(a, "tigL", (s * 0.28, hc.y - 0.05, hc.z - 0.12), (s * 0.48, hc.y + 0.05, hc.z - 0.2), 0.14)  # бакенбарды
        for k in range(2):  # сапфировые полоски на лбу и щеках
            kchain(a, "neonS", [(s * (0.06 + 0.08 * k), front_y(th, s * 0.1, hc.z + 0.22) - 0.01, hc.z + 0.25 - 0.02 * k),
                                (s * (0.1 + 0.08 * k), front_y(th, s * 0.14, hc.z + 0.3) + 0.0, hc.z + 0.32 - 0.02 * k)],
                   [0.035, 0.03], up=(0, -1, 0))
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.0, 0.0, t + 1.3))
    a.pose = {"ArmL": ((-20, 0, 0), (0, 0, 0)), "Tail": ((0, 12, 0), (0, 0, 0))}
    return a


def gold_mane_hippocamp():
    """3. Гиппокамп-златогрив: спереди конь, сзади рыбий хвост; встал на дыбы из волны, грива и плавники — бирюза с
    золотом. Признаки: конская голова с гривой, передние ноги с плавниками-перепонками, чешуйчатый рыбий хвост с
    веером, перламутровое брюхо."""
    a = new("GoldManeHippocamp", {"hc": ("2EC4C0", True), "hcD": ("1E8E9A", True), "hcB": ("F0F6FF", False),
                                  "gold": ("F5B21C", True), "water": ("3BA7E0", True), "foam": ("E6F7FF", False),
                                  "hoof": ("1E5E6A", False)})
    t = legendary_stand(a, 1.7)
    part(a, "Wave", "Stand", (0, 0, t))  # волна — часть композиции
    a.prism("water", S.octagon(-0.9, 0.9, -0.85, 0.95, 0.35), t, t + 0.18, bevel=0)
    for k, ang in enumerate(range(20, 360, 50)):
        r = math.radians(ang)
        spike(a, "foam", (0.55 * math.cos(r), 0.55 * math.sin(r), t + 0.12),
              (0.72 * math.cos(r), 0.72 * math.sin(r), t + 0.38 + 0.06 * (k % 2)), 0.14)
    part(a, "Body", "Wave", (0, 0.1, t + 0.8))
    # рыбий хвост из волны вверх к телу, чешуя — два тона по очереди
    tail = [(0.1, 0.55, t + 0.12), (0.05, 0.45, t + 0.45), (0, 0.3, t + 0.75), (0, 0.12, t + 1.0)]
    for i in range(len(tail) - 1):
        kchain(a, "hc" if i % 2 else "hcD", [tail[i], tail[i + 1]], [0.36 + 0.06 * i, 0.4 + 0.06 * i], up=(0, -1, 0))
    for s in S2:  # хвостовой веер — золото, поднят из волны сзади
        a.extrude("gold", [(0, 0), (0.18, 0.1), (0.45, 0.42), (0.18, 0.32)], -0.03, 0.03, axis="x",
                  matrix=Matrix.Translation((s * 0.05, 0.62, t + 0.15)) @ Matrix.Rotation(math.radians(s * 20), 4, "Z"))
    A.body(a, "hc", (0, 0.0, t + 0.95), 0.36, 0.34, 0.6, "egg", n=4, lean=-0.15,
           front=("hcB", 0.6, t + 0.95, t + 1.45))  # грудь коня, перламутровое брюхо
    for s in S2:  # передние ноги на дыбах с плавниками-перепонками
        part(a, "Arm" + ("L" if s > 0 else "R"), "Body", (s * 0.2, -0.2, t + 1.35))
        A.limb(a, "hc", [(s * 0.2, -0.2, t + 1.35), (s * 0.26, -0.5, t + 1.3), (s * 0.24, -0.55, t + 1.0)],
               [0.13, 0.11, 0.1])
        a.prism("hoof", S.octagon(s * 0.24 - 0.07, s * 0.24 + 0.07, -0.62, -0.48, 0.03), t + 0.92, t + 1.0, bevel=0)
        a.extrude("gold", [(0, 0), (0.25, -0.05), (0.3, -0.3)], -0.02, 0.02, axis="x",
                  matrix=Matrix.Translation((s * 0.24, -0.5, t + 1.3)))  # плавник-перепонка
        a.group = "Body"
    part(a, "Head", "Body", (0, -0.15, t + 1.5))
    kchain(a, "hc", [(0, -0.05, t + 1.4), (0, -0.15, t + 1.75), (0, -0.2, t + 1.95)], [0.3, 0.26, 0.24],
           up=(0, -1, 0))  # шея
    hc = V((0, -0.3, t + 2.05))
    th = A.body(a, "hc", (hc.x, hc.y, hc.z - 0.16), 0.17, 0.2, 0.32, "ball", n=3)
    fy = front_y(th, 0, hc.z - 0.05)
    taper(a, "hc", (0, fy + 0.08, hc.z - 0.06), (0, fy - 0.3, hc.z - 0.16), 0.24, 0.18, 0.22, 0.16)  # конская морда
    a.box("hcD", -0.05, 0.05, fy - 0.33, fy - 0.29, hc.z - 0.15, hc.z - 0.1, bevel=0)
    grin(a, (0, fy - 0.3, hc.z - 0.22), 0.1, h=0.035)
    for s in S2:
        eye2(a, (s * 0.11, front_y(th, s * 0.11, hc.z + 0.04) + 0.01, hc.z + 0.04), 0.06, (s * 0.5, -1, 0), "goofy",
             s, "hc", "hcD")
        tri_ear(a, "hc", "hcB", (s * 0.08, hc.y + 0.04, hc.z + 0.12), (s * 0.14, hc.y + 0.08, hc.z + 0.34), 0.1)
    for k in range(5):  # золотая грива по шее
        z = t + 1.5 + 0.13 * k
        y = 0.05 - 0.07 * k
        spike(a, "gold", (0, y, z), (0, y + 0.3, z + 0.12), 0.16)
    face_point(a, (0, fy - 0.15, hc.z))
    closeup(a, (0.0, 0.1, t + 1.1))
    a.pose = {"ArmL": ((-20, 0, 0), (0, 0, 0)), "ArmR": ((15, 0, 0), (0, 0, 0))}
    return a


_OWN = {"SapphireTiger": sapphire_tiger, "GoldManeHippocamp": gold_mane_hippocamp}
ORDER = [("TreasureGriffin", SK.treasure_griffin, "Грифон-казначей", "Legendary"),
         ("SapphireTiger", None, "Тигр-сапфир", "Legendary"),
         ("GoldManeHippocamp", None, "Гиппокамп-златогрив", "Legendary")]
ITEMS = collect(ORDER, _OWN)
