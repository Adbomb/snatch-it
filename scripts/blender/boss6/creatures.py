"""Коллекция босса 6 «Королева-мухоловка» (Джунгли) — 10 эскизов из 30 для концепт-листа (шаг 3 D64).

Стиль коллекции — как утверждённая ледяная коллекция v2 босса 5: странные и смешные звери джунглей, смешное в самом
теле (нелепые пропорции, лишние головы и глаза, тело-колесо, башня из жуков), без бытовых вещей, людей, текста,
логотипов, оружия и мемных или чужих персонажей. Правила анатомии D64: у каждого — 3–5 признаков вида (в докстринге),
голова ≈ 1/3 тела, ноги под центром масс, ярусы D39 со скосами, суставы перекрываются, лицо с эмоцией.
Редкости эскизов — 4 Common, 3 Rare, 2 Epic, 1 Legendary (доля как в коллекции 12 / 9 / 6 / 3).

Сборка — общий конвейер существ (creature_kit.run, quick — без запекания и экспорта): подвижные части, проверка
суставов joint_check, кадры hero / front / side / face / pose / ingame_phone.
Запуск: blender --background --factory-startup --python scripts/blender/boss6/creatures.py -- <репо> [id…]
Кадры: assets/concepts/bosses_5_10/boss6_v2/raw/creatures/ (вне git). build(i, col) — модель для арены.
"""

import math
import os
import sys

from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
sys.path.insert(0, BL)
sys.path.insert(0, os.path.join(BL, "dragon10"))
from creature_kit import (S, common_stand, d39v2, epic_stand, legendary_stand, part, rare_stand, run, tilt,  # noqa: E402
                          with_matrix)
import anatomy_kit as A  # noqa: E402
import v4_kit as K  # noqa: E402

V = Vector
S2 = (1, -1)
BASE = {"white": ("FFFFFF", False), "dark": ("1B1B2A", False), "glint": ("FFFFFF", False),
        "mouth": ("5A1E2E", False), "blush": ("FF9FB2", False), "pink": ("FF7F9F", False),
        "ivory": ("F3E9D2", False), "tongue": ("FF6F91", False)}


def new(item_id, pal):
    a = S.Art(f"Art_{item_id}", ring_z0=1.0)
    d39v2(a)
    for k, (code, r) in {**BASE, **pal}.items():
        a.paint(k, code, rings=r)
    return a


def kchain(a, key, pts, ws, hs=None, up=(0, -1, 0), cut=A.CUT, overlap=0.45):
    K.KEY = key
    K.chain(a, pts, ws, hs, up=up, cut=cut, overlap=overlap)


def spike(a, key, base, tip, w):
    K.KEY = key
    K.spike(a, base, tip, w)


def layered(a, key, prof, layers, anchor, xc=0.0, matrix=None):
    K.KEY = key
    K.layered(a, prof, layers, anchor, xc=xc, matrix=matrix)


def face_point(a, p):
    a.face = tuple(p)


def closeup(a, target, eye_off=(-1.2, -2.2, 1.0)):
    t = V(target)
    a.closeup = (tuple(t + V(eye_off)), tuple(t))


def eye2(a, c, r, normal, mood, s, skin, brow="dark", closed=False, look=(0.0, 0.0)):
    A.eye(a, c, r, normal=normal, mood=mood, side=s, skin_key=skin, brow_key=brow, closed=closed, look=look)


def grin(a, c, w, h=0.07, key="mouth", teeth=0):
    """Улыбка-брусок с уголками вверх (и белыми зубками)."""
    x, y, z = c
    a.box(key, x - w / 2, x + w / 2, y - 0.03, y + 0.04, z - h / 2, z + h / 2, bevel=0)
    for s in S2:
        a.box(key, x + s * w / 2 - 0.035, x + s * w / 2 + 0.035, y - 0.03, y + 0.04, z, z + h * 1.4, bevel=0)
    for i in range(teeth):
        tx = x - w / 3 + i * (2 * w / 3) / max(teeth - 1, 1)
        a.box("white", tx - 0.03, tx + 0.03, y - 0.045, y - 0.025, z - h / 2 - 0.05, z - h / 2 + 0.005, bevel=0)


# ══ COMMON ═════════════════════════════════════════════════════════════════════════════════════════════════════

def frog_bubble():
    """1. Лягушка-пузырь: горловой мешок раздут больше самой лягушки, глаза навыкате от удивления.
    Признаки: глаза на макушке буграми, широкий рот-щель, сложенные мощные задние лапы, пальцы с подушечками."""
    a = new("FrogBubble", {"frog": ("4FC24A", True), "frogD": ("2E8F3A", False), "frogL": ("D6F28A", False),
                           "sac": ("FF9FC0", True), "sacL": ("FFD3E2", False)})
    t = common_stand(a, 1.55)
    part(a, "Body", "Stand", (0, 0.2, t + 0.4))
    A.body(a, "frog", (0, 0.25, t), 0.8, 0.72, 0.95, "dome", n=4, front=("frogL", 0.8, t + 0.1, t + 0.5))
    for x, y, z in ((0.35, 0.45, t + 0.7), (-0.3, 0.6, t + 0.55), (0.05, 0.75, t + 0.4)):  # пятна на спине
        a.box("frogD", x - 0.13, x + 0.13, y - 0.12, y + 0.12, z - 0.12, z + 0.12, bevel=0.01)
    for s in S2:  # глаза-бугры на макушке
        A.ball(a, "frog", (s * 0.36, -0.12, t + 0.92), 0.27, n=3)
        eye2(a, (s * 0.38, -0.33, t + 1.0), 0.17, (s * 0.35, -1, 0.35), "surprised", s, "frog", "frogD")
        A.body(a, "frog", (s * 0.66, 0.35, t), 0.32, 0.5, 0.5, "egg", n=2)  # сложенное бедро
        A.foot(a, "frog", (s * 0.7, -0.05, t), (s * 0.2, -1, 0), 0.5, 0.32, toes=3, toe_key="frogL", h=0.1, z=t)
        A.limb(a, "frog", [(s * 0.42, -0.3, t + 0.45), (s * 0.5, -0.5, t + 0.08)], [0.2, 0.17], joints=False)
        A.foot(a, "frog", (s * 0.5, -0.52, t), (s * 0.3, -1, 0), 0.32, 0.26, toes=3, toe_key="frogL", h=0.09, z=t)
    a.box("mouth", -0.58, 0.58, -0.66, -0.55, t + 0.66, t + 0.73, bevel=0)  # рот-щель во всю ширину
    for s in S2:
        a.box("mouth", s * 0.58 - 0.05, s * 0.58 + 0.05, -0.66, -0.55, t + 0.66, t + 0.82, bevel=0)  # уголки вверх
    part(a, "Sac", "Body", (0, -0.5, t + 0.4))
    A.ball(a, "sac", (0, -0.95, t + 0.34), 0.66, n=5, ry=0.52, rz=0.34)  # мешок под ртом — шире головы
    a.box("sacL", -0.3, -0.05, -1.48, -1.44, t + 0.42, t + 0.55, bevel=0.01)  # блик
    face_point(a, (0, -0.5, t + 0.85))
    closeup(a, (0.0, -0.9, t + 0.5))
    a.pose = {"Sac": ((0, 0, 0), (0, -0.05, 0.05))}
    return a


def big_beak_toucan():
    """2. Тукан-клювище: клюв вдвое длиннее тела — птица откинулась на хвост, чтобы не клюнуть носом.
    Признаки: огромный яркий клюв, чёрное тело и белое горло, голубое кольцо у глаза, лапы с пальцами 2+2, хвост."""
    a = new("BigBeakToucan", {"black": ("23243A", True), "throat": ("FFF3C4", False), "beakY": ("FFC21C", True),
                              "beakO": ("FF7A1C", False), "beakR": ("E8384F", False), "ring": ("3FC4F0", False),
                              "feet": ("5B7BD8", False)})
    t = common_stand(a, 1.5)
    z = t + 0.28
    for s in S2:
        part(a, "Leg" + ("L" if s > 0 else "R"), "Stand", (s * 0.22, 0.1, t + 0.35))
        A.limb(a, "feet", [(s * 0.22, 0.15, t + 0.45), (s * 0.24, 0.05, t + 0.05)], [0.14, 0.12], joints=False)
        for d in ((0, -1, 0), (0, 1, 0)):
            K.KEY = "feet"
            K.taper(a, (s * 0.24, 0.05, t + 0.05), (s * 0.26, 0.05 + d[1] * 0.32, t + 0.04), 0.1, 0.07, 0.07, 0.06,
                    cut=0.2)
    part(a, "Body", "Stand", (0, 0.2, z + 0.4))
    A.body(a, "black", (0, 0.3, z), 0.46, 0.48, 1.05, "egg", n=4, lean=0.2, front=("throat", 0.85, z + 0.62, z + 1.05))
    for s in S2:
        A.folded_wing(a, "black", "black", (s * 0.42, 0.3, z + 0.85), s, 0.85, 0.42, rows=2, down=(0, 0.45, -1))
    part(a, "Tail", "Body", (0, 0.65, z + 0.25))
    A.flipper(a, "black", (0, 0.62, z + 0.3), (0, 1.25, t + 0.02), 0.42, 0.34, thick=0.1, up=(0, 0.3, 1))  # хвост
    part(a, "Head", "Body", (0, 0.35, z + 1.0))
    hc = V((0, 0.32, z + 1.28))
    A.ball(a, "black", tuple(hc), 0.36, n=3)
    for s in S2:
        a.prism("ring", S.octagon(-0.15, 0.15, -0.15, 0.15, 0.05), -0.04, 0.03, axis="y",
                matrix=A.Matrix.Translation(hc + V((s * 0.3, -0.14, 0.06))) @ A.facing((s, -0.4, 0.1)))  # голубое кольцо
        eye2(a, tuple(hc + V((s * 0.31, -0.16, 0.06))), 0.1, (s, -0.4, 0.1), "proud", s, "black")
    # клюв: три цветные секции (жёлтый корень, оранжевая середина, красный кончик), верх и низ
    beak = [(-0.15, 0.35), (-0.7, 0.42), (-1.5, 0.28), (-2.05, -0.05), (-1.9, -0.18), (-1.2, -0.12), (-0.2, -0.22)]
    for i, (key, y0, y1) in enumerate((("beakY", 0.2, -0.75), ("beakO", -0.72, -1.45), ("beakR", -1.42, -2.2))):
        prof = [(max(min(y, y0), y1), zz) for y, zz in beak]
        layered(a, key, [(y, z + 1.2 + zz) for y, zz in prof], [(0.2 - 0.01 * i, 1, 1), (0.27 - 0.01 * i, 0.9, 0.82)],
                (-1.0, z + 1.2), matrix=None)
    a.box("dark", -0.24, 0.24, -1.6, -0.2, z + 1.07, z + 1.1, bevel=0)  # линия клюва
    face_point(a, (0, -0.6, z + 1.3))
    closeup(a, (0.0, -1.0, z + 1.2))
    a.pose = {"Head": ((10, 0, 0), (0, 0, 0)), "Tail": ((-10, 0, 0), (0, 0, 0))}
    return a


def periscope_chameleon():
    """3. Хамелеон-перископ: глаза на высоких стебельках, каждый смотрит в свою сторону; хвост закручен спиралью.
    Признаки: шлем-гребень на голове, глаза-башенки, сплюснутое с боков тело с гребнем, лапы-клещи, хвост-спираль."""
    a = new("PeriscopeChameleon", {"cham": ("4FD06A", True), "chamD": ("2E9E54", False), "chamS": ("FFD23F", False),
                                   "chamB": ("3FA8E8", False)})
    t = common_stand(a, 1.55)
    z = t + 0.75
    for i, (x, y) in enumerate(((0.28, -0.45), (-0.28, -0.45), (0.28, 0.45), (-0.28, 0.45))):
        nm = "Leg" + "FB"[i // 2] + "LR"[i % 2]
        part(a, nm, "Stand", (x * 0.9, y, z - 0.1))
        A.limb(a, "cham", [(x * 0.8, y, z - 0.05), (x * 1.5, y - 0.05, z - 0.35), (x * 1.3, y, t + 0.05)],
               [0.17, 0.15, 0.13])
        for dy in (-0.12, 0.12):  # лапа-клещи: два пальца вперёд-назад
            spike(a, "chamD", (x * 1.3, y, t + 0.06), (x * 1.3, y + dy * 2.2, t + 0.03), 0.1)
    part(a, "Body", "Stand", (0, 0, z))
    body = [(-0.75, z + 0.05), (-0.6, z + 0.42), (0.0, z + 0.6), (0.55, z + 0.45), (0.8, z + 0.1), (0.45, z - 0.3),
            (-0.45, z - 0.32)]
    layered(a, "cham", body, [(0.24, 1, 1), (0.32, 0.88, 0.86)], (0.0, z + 0.1))
    for k, y in enumerate((-0.4, -0.05, 0.3)):  # полосы
        a.box("chamS" if k % 2 else "chamB", -0.335, 0.335, y - 0.07, y + 0.07, z - 0.18, z + 0.32, bevel=0.01)
    for k in range(6):  # гребень на спине
        y = -0.5 + k * 0.22
        spike(a, "chamD", (0, y, z + 0.5 + 0.08 * math.sin(k)), (0, y + 0.06, z + 0.72), 0.14)
    part(a, "Head", "Body", (0, -0.7, z + 0.15))
    hz = z + 0.2
    A.ball(a, "cham", (0, -0.9, hz), 0.34, n=3, ry=0.4, rz=0.3)
    A.snout(a, "cham", (0, -1.15, hz - 0.05), (0, -1, -0.1), 0.2, 0.42, 0.3, 0.34, 0.24, nose=0.0, mouth=0.9)
    layered(a, "chamD", [(-0.75, hz + 0.2), (-0.45, hz + 0.62), (-0.3, hz + 0.55), (-0.5, hz + 0.15)],
            [(0.06, 1, 1), (0.12, 0.85, 0.8)], (-0.5, hz + 0.3))  # шлем-гребень назад
    for s, mood, look in ((1, "sly", (1.0, 0.2)), (-1, "surprised", (-1.0, -0.2))):
        nm = "Eye" + ("L" if s > 0 else "R")
        b = V((s * 0.22, -0.95, hz + 0.15))
        part(a, nm, "Head", tuple(b))
        top = b + V((s * 0.35, -0.1, 0.95 + (0.25 if s < 0 else 0)))
        A.limb(a, "chamD", [tuple(b), tuple(b + V((s * 0.1, 0, 0.5))), tuple(top)], [0.14, 0.12, 0.11], joints=False)
        A.ball(a, "cham", tuple(top + V((0, 0, 0.12))), 0.2, n=3)
        eye2(a, tuple(top + V((s * 0.05, -0.17, 0.13))), 0.12, (s * 0.8, -1, 0.0), mood, s, "cham", "chamD", look=look)
    part(a, "Tail", "Body", (0, 0.75, z))
    pts = [(0, 0.7, z)]
    for k in range(1, 9):
        ang = k * 0.75
        r = 0.55 * (1 - k / 11)
        pts.append((0, 1.05 + r * math.sin(ang), z - 0.35 + r * math.cos(ang) - 0.05 * k))
    kchain(a, "cham", pts, [0.3 - 0.025 * k for k in range(len(pts))], up=(1, 0, 0))
    face_point(a, (0, -1.25, hz + 0.3))
    closeup(a, (0.0, -0.3, z + 0.2))
    a.pose = {"EyeL": ((0, 20, -15), (0, 0, 0)), "EyeR": ((0, -15, 20), (0, 0, 0)), "Tail": ((15, 0, 0), (0, 0, 0))}
    return a


def knot_sloth():
    """4. Ленивец-узел: лапы такие длинные, что он завязал их узлом над головой — и уснул, довольный.
    Признаки: светлая маска с тёмными полосами от глаз, длинные изогнутые когти, лохматая шерсть, сонная улыбка."""
    a = new("KnotSloth", {"fur": ("A27A55", True), "furD": ("7A5638", False), "mask": ("F1DDB8", False),
                          "claw": ("F3E9D2", False), "moss": ("7ED957", False)})
    t = common_stand(a, 1.45)
    part(a, "Body", "Stand", (0, 0.1, t + 0.5))
    A.body(a, "fur", (0, 0.15, t), 0.66, 0.6, 1.15, "pear", n=5, lean=-0.1, front=("mask", 0.6, t + 0.15, t + 0.75))
    for x, z in ((0.5, t + 0.9), (-0.35, t + 0.35)):  # мох в шерсти
        a.box("moss", x - 0.16, x + 0.16, 0.45, 0.72, z - 0.1, z + 0.08, bevel=0.01)
    for s in S2:  # короткие задние лапы с когтями
        A.limb(a, "fur", [(s * 0.4, -0.1, t + 0.3), (s * 0.55, -0.45, t + 0.12)], [0.3, 0.26], joints=False)
        for dx in (-0.08, 0.08):
            spike(a, "claw", (s * 0.55 + dx, -0.55, t + 0.12), (s * 0.55 + dx, -0.75, t + 0.02), 0.08)
    part(a, "Head", "Body", (0, 0.0, t + 1.2))
    hc = V((0, -0.05, t + 1.42))
    A.ball(a, "fur", tuple(hc), 0.46, n=3, ry=0.42, rz=0.4)
    a.prism("mask", S.octagon(-0.36, 0.36, hc.z - 0.3, hc.z + 0.25, 0.12), -0.47, -0.36, axis="y")  # маска
    for s in S2:
        a.box("furD", s * 0.3 - 0.13, s * 0.3 + 0.13, -0.5, -0.45, hc.z - 0.05, hc.z + 0.07, bevel=0,
              matrix=tilt((s * 0.3, -0.48, hc.z), "Y", s * 20))  # тёмная полоса от глаза
        eye2(a, (s * 0.17, -0.5, hc.z + 0.04), 0.09, (0, -1, 0), "sleepy", s, "furD", "furD", closed=True)
    a.box("furD", -0.07, 0.07, -0.53, -0.47, hc.z - 0.1, hc.z - 0.02, bevel=0)  # нос
    grin(a, (0, -0.5, hc.z - 0.18), 0.22)
    for s, nm in ((1, "ArmL"), (-1, "ArmR")):  # руки вверх, крест-накрест над головой, кисти свисают на другой бок
        sh = V((s * 0.55, 0.05, t + 1.0))
        part(a, nm, "Body", tuple(sh))
        dy = 0.08 * s  # руки проходят одна перед другой — узел, а не слипшийся брусок
        pts = [tuple(sh), (s * 0.9, dy, t + 1.6), (s * 0.6, dy, t + 2.35), (-s * 0.25, dy, t + 2.6),
               (-s * 0.85, dy, t + 2.25)]
        A.limb(a, "fur", pts, [0.26, 0.24, 0.22, 0.2, 0.18])
        end = V((-s * 0.85, dy - 0.05, t + 2.2))
        for dx in (-0.08, 0.0, 0.08):  # длинные когти свисают крючком
            spike(a, "claw", end + V((dx, -0.08, 0)), end + V((dx + s * 0.05, -0.18, -0.5)), 0.08)
    face_point(a, (0, -0.55, hc.z))
    closeup(a, (0.0, -0.4, t + 0.7))
    a.pose = {"Head": ((0, 0, 10), (0, 0, 0))}
    return a


# ══ RARE ═══════════════════════════════════════════════════════════════════════════════════════════════════════

def many_eye_caterpillar():
    """5. Гусеница-многоглазка: на каждом сегменте — пара глаз со своим настроением, весь хвост спорит с головой.
    Признаки: тело из сегментов-колец, ложноножки снизу, усики, челюсти-улыбка, точки-дыхальца на боках."""
    a = new("ManyEyeCaterpillar", {"cat": ("9CE04A", True), "catD": ("5FA82E", False), "catS": ("FF8A3D", False),
                                   "catH": ("FFC93D", True)})
    t = rare_stand(a, 1.6)
    moods = ("calm", "sleepy", "worried", "goofy", "angry", "surprised")
    part(a, "Body", "Stand", (0, 0.4, t + 0.4))
    segs = []
    for k in range(6):  # сзади наперёд, перед поднят
        y = 1.05 - k * 0.38
        zc = t + 0.36 + (0.0 if k < 3 else (k - 2) * 0.28)
        r = 0.34 + 0.02 * k
        segs.append((y, zc, r))
    for k, (y, zc, r) in enumerate(segs):
        nm = "Body" if k == 0 else f"Seg{k}"
        if k:
            part(a, nm, "Body" if k == 1 else f"Seg{k - 1}", (0, y + 0.2, zc))
        A.ball(a, "cat" if k % 2 == 0 else "catD", (0, y, zc), r, n=3, ry=r * 0.9)
        a.box("catS", -r - 0.01, -r + 0.06, y - 0.06, y + 0.06, zc - 0.06, zc + 0.06, bevel=0)  # дыхальце
        a.box("catS", r - 0.06, r + 0.01, y - 0.06, y + 0.06, zc - 0.06, zc + 0.06, bevel=0)
        if k < 5:
            for s in S2:
                eye2(a, (s * r * 0.62, y - r * 0.35, zc + r * 0.5), 0.1, (s * 0.85, -0.35, 0.45), moods[k], s,
                     "cat" if k % 2 == 0 else "catD")
        if k < 4:  # ложноножки
            for s in S2:
                A.limb(a, "catD", [(s * r * 0.6, y, zc - r * 0.5), (s * r * 0.75, y - 0.05, t + 0.03)], [0.13, 0.11],
                       joints=False)
    y, zc, r = segs[-1]
    hc = V((0, y - 0.05, zc + 0.05))
    A.ball(a, "catH", tuple(hc), 0.42, n=3)  # голова
    for s in S2:
        eye2(a, tuple(hc + V((s * 0.17, -0.38, 0.1))), 0.11, (s * 0.25, -1, 0.1), "surprised", s, "catH", "catD")
        A.limb(a, "catD", [tuple(hc + V((s * 0.15, 0, 0.36))), tuple(hc + V((s * 0.35, -0.1, 0.85)))], [0.06, 0.05],
               joints=False)
        A.ball(a, "catS", tuple(hc + V((s * 0.36, -0.1, 0.9))), 0.09, n=2)
        spike(a, "catD", tuple(hc + V((s * 0.1, -0.38, -0.2))), tuple(hc + V((s * 0.02, -0.5, -0.3))), 0.08)
    grin(a, tuple(hc + V((0, -0.42, -0.12))), 0.26, teeth=0)
    face_point(a, tuple(hc + V((0, -0.4, 0))))
    closeup(a, (0.0, 0.3, t + 0.5))
    a.pose = {"Seg3": ((10, 0, 0), (0, 0, 0)), "Seg5": ((-12, 0, 10), (0, 0, 0))}
    return a


def wheel_monkey():
    """6. Обезьяна-колесо: хвост такой длинный, что свернулся в обруч вокруг неё — сидит в нём, как в колесе.
    Признаки: светлая маска-сердечко, большие круглые уши, длинные руки, цепкий хвост, хохолок."""
    a = new("WheelMonkey", {"mon": ("B36B3A", True), "monD": ("7E4626", False), "monL": ("F6D9B0", False),
                            "tuft": ("E8A04A", False)})
    t = rare_stand(a, 1.6)
    R0, cz = 1.15, t + 1.2  # обруч хвоста
    part(a, "Body", "Stand", (0, 0.05, t + 0.5))
    A.body(a, "mon", (0, 0.1, t + 0.05), 0.45, 0.42, 0.85, "pear", n=4, front=("monL", 0.7, t + 0.15, t + 0.7))
    for s in S2:  # ноги упираются в обод, руки держатся за обод сбоку
        A.limb(a, "mon", [(s * 0.3, -0.1, t + 0.25), (s * 0.5, -0.35, t + 0.25), (s * 0.55, -0.3, t + 0.08)],
               [0.18, 0.16, 0.14])
        nm = "Arm" + ("L" if s > 0 else "R")
        part(a, nm, "Body", (s * 0.4, 0.05, t + 0.75))
        A.limb(a, "mon", [(s * 0.4, 0.05, t + 0.75), (s * 0.85, -0.1, t + 1.0), (s * 1.05, 0.05, cz + 0.2)],
               [0.17, 0.15, 0.14])
        A.ball(a, "monL", (s * 1.08, 0.05, cz + 0.22), 0.12, n=2)  # ладонь на ободе
    part(a, "Head", "Body", (0, 0.05, t + 0.9))
    hc = V((0, -0.02, t + 1.25))
    A.ball(a, "mon", tuple(hc), 0.4, n=3)
    a.prism("monL", S.octagon(-0.3, 0.3, hc.z - 0.28, hc.z + 0.2, 0.1), -0.42, -0.3, axis="y")  # маска
    for s in S2:
        a.prism("monL", S.octagon(-0.13, 0.13, -0.13, 0.13, 0.04), -0.08, 0.08, axis="x",
                matrix=A.Matrix.Translation(hc + V((s * 0.44, 0.0, 0.05))))  # ухо
        a.prism("mon", S.octagon(-0.17, 0.17, -0.17, 0.17, 0.05), -0.06, 0.04, axis="x",
                matrix=A.Matrix.Translation(hc + V((s * 0.49, 0.03, 0.05))))
        eye2(a, tuple(hc + V((s * 0.13, -0.43, 0.06))), 0.09, (0, -1, 0), "goofy", s, "monL", "monD")
    grin(a, tuple(hc + V((0, -0.44, -0.16))), 0.28, teeth=3)
    for k in range(3):
        spike(a, "tuft", tuple(hc + V((-0.1 + 0.1 * k, 0, 0.36))), tuple(hc + V((-0.2 + 0.2 * k, 0.05, 0.65))), 0.12)
    part(a, "Tail", "Body", (0, 0.4, t + 0.25))
    pts = [(0, 0.35, t + 0.25)]
    for k in range(17):  # обруч: почти полный круг вокруг, кончик закручен внутрь
        ang = math.radians(-100 + k * 21)
        pts.append((R0 * math.cos(ang) * (1 - 0.0 * k), 0.4 + 0.02 * k, cz + R0 * math.sin(ang)))
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
        for dy in (-0.3, 0.3):
            K.KEY = "beak"
            K.taper(a, (s * 0.22, -0.05, t + 0.05), (s * 0.24, -0.05 + dy, t + 0.04), 0.09, 0.06, 0.07, 0.05, cut=0.2)
    part(a, "Body", "Stand", (0, 0.1, t + 0.7))
    z = t + 0.35
    A.body(a, "green", (0, 0.1, z), 0.5, 0.48, 1.0, "egg", n=4, lean=-0.1, front=("yel", 0.7, z + 0.2, z + 0.75))
    for s in S2:
        A.folded_wing(a, "green", "blue", (s * 0.46, 0.15, z + 0.85), s, 0.85, 0.45, rows=2, down=(0, 0.4, -1))
    part(a, "Tail", "Body", (0, 0.5, z + 0.25))
    for k, (dx, key) in enumerate(((-0.12, "red"), (0.0, "blue"), (0.12, "yel"))):
        A.flipper(a, key, (dx, 0.5, z + 0.3), (dx * 3, 1.5, t + 0.05), 0.18, 0.12, thick=0.06, up=(0, 0.3, 1))
    heads = ((-1, "HeadR", "red", "angry", -32), (0, "HeadM", "blue", "goofy", 0), (1, "HeadL", "yel", "surprised", 32))
    for s, nm, key, mood, turn in heads:
        base = V((s * 0.25, -0.05, z + 0.9))
        part(a, nm, "Body", tuple(base))
        hc = V((s * 0.55, -0.15, z + 1.45 + (0.15 if s == 0 else 0)))
        A.limb(a, key, [tuple(base), tuple(hc)], [0.3, 0.26], joints=False)
        with_matrix(a, tilt(hc, "Z", turn))
        A.ball(a, key, tuple(hc), 0.27, n=3)
        a.prism("face", S.octagon(-0.17, 0.17, hc.z - 0.12, hc.z + 0.12, 0.05), hc.y - 0.27, hc.y - 0.17, axis="y",
                matrix=A.Matrix.Translation((hc.x, 0, 0)))
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


# ══ EPIC ═══════════════════════════════════════════════════════════════════════════════════════════════════════

def beetle(a, c, r, key, keyD, mood, horn=True):
    """Жук-носорог радиуса r в точке c: панцирь-купол со швом, голова с рогом, глаза, 6 лап, усики."""
    x, y, z = c
    A.body(a, key, (x, y + 0.1 * r, z + 0.25 * r), r * 0.9, r * 1.1, r * 0.85, "dome", n=3)
    a.box(keyD, x - 0.03 * r - 0.02, x + 0.03 * r + 0.02, y - r * 0.9, y + r * 1.2, z + 0.25 * r, z + 1.06 * r,
          bevel=0)  # шов надкрылий
    A.ball(a, keyD, (x, y - r * 0.95, z + r * 0.5), r * 0.45, n=2)  # голова
    for s in S2:
        eye2(a, (x + s * r * 0.24, y - r * 1.32, z + r * 0.6), r * 0.13, (s * 0.4, -1, 0.1), mood, s, keyD, "dark")
        for k in range(3):  # лапы
            yy = y - r * 0.5 + k * r * 0.55
            A.limb(a, keyD, [(x + s * r * 0.7, yy, z + r * 0.35), (x + s * r * 1.15, yy - 0.05 * r, z + r * 0.4),
                             (x + s * r * 1.25, yy, z)], [r * 0.12, r * 0.1, r * 0.08], joints=False)
        A.limb(a, keyD, [(x + s * r * 0.15, y - r * 1.25, z + r * 0.75), (x + s * r * 0.45, y - r * 1.55, z + r * 1.0)],
               [r * 0.05, r * 0.04], joints=False)  # усики
    if horn:
        spike(a, keyD, (x, y - r * 1.25, z + r * 0.62), (x, y - r * 1.75, z + r * 1.7), r * 0.32)
    return V((x, y - r * 1.62, z + r * 1.45))  # точка на роге, где сидит следующий


def tower_beetle():
    """8. Жук-носорог «башня жуков»: на роге большого жука сидит жук поменьше, на его роге — совсем малыш.
    Признаки: рог на голове, надкрылья со швом, шесть лап, усики, блестящий панцирь."""
    a = new("TowerBeetle", {"bug1": ("6B3FB8", True), "bug1D": ("3E2470", False), "bug2": ("2FB0A8", True),
                            "bug2D": ("1C6E69", False), "bug3": ("FF8A3D", True), "bug3D": ("B85512", False)})
    t = epic_stand(a, 1.65)
    part(a, "Body", "Stand", (0, 0.2, t + 0.4))
    p = beetle(a, (0, 0.35, t), 0.95, "bug1", "bug1D", "proud")
    part(a, "Mid", "Body", tuple(p))
    p2 = beetle(a, tuple(p + V((0, 0.4, -0.1))), 0.48, "bug2", "bug2D", "worried")
    part(a, "Top", "Mid", tuple(p2))
    beetle(a, tuple(p2 + V((0, 0.2, -0.05))), 0.26, "bug3", "bug3D", "surprised", horn=False)
    face_point(a, (0, -1.1, t + 0.9))
    closeup(a, (0.0, 0.0, t + 0.7))
    a.pose = {"Mid": ((0, 0, 12), (0, 0, 0)), "Top": ((-15, 0, -10), (0, 0, 0))}
    return a


def flower_jaguar():
    """9. Ягуар с пятнами-цветами: вместо розеток на шкуре распустились цветы, а кончик хвоста — бутон.
    Признаки: мощное кошачье тело, круглые уши, длинный хвост, пятна-розетки, усы и розовый нос."""
    a = new("FlowerJaguar", {"jag": ("F2A23A", True), "jagL": ("FFE6B8", False), "jagD": ("8A4A1C", False),
                             "petal": ("FF6FAE", False), "petal2": ("FFFFFF", False), "core": ("FFD23F", False),
                             "leaf": ("3FAE4A", False)})
    t = epic_stand(a, 1.7)
    z = t + 0.85
    for i, (x, y) in enumerate(((0.32, -0.6), (-0.32, -0.6), (0.32, 0.6), (-0.32, 0.6))):
        nm = "Leg" + "FB"[i // 2] + "LR"[i % 2]
        part(a, nm, "Stand", (x, y, z - 0.1))
        A.limb(a, "jag", [(x, y, z), (x * 1.05, y + (0.08 if i >= 2 else -0.04), z - 0.45), (x, y - 0.05, t + 0.1)],
               [0.3, 0.24, 0.2])
        A.foot(a, "jag", (x, y - 0.05, t), (0, -1, 0), 0.32, 0.26, toes=3, toe_key="jagL", h=0.11, z=t)
    part(a, "Body", "Stand", (0, 0, z))
    body = [(-0.85, z - 0.05), (-0.75, z + 0.35), (0.0, z + 0.42), (0.8, z + 0.35), (0.9, z - 0.05), (0.6, z - 0.32),
            (-0.6, z - 0.32)]
    layered(a, "jag", body, [(0.3, 1, 1), (0.4, 0.9, 0.85)], (0.0, z + 0.05))
    a.extrude("jagL", [(z - 0.33, -0.55), (z - 0.2, -0.55), (z - 0.2, 0.55), (z - 0.33, 0.55)], -0.3, 0.3, axis="x")
    for k, (x, y, zz) in enumerate(((0.41, -0.35, z + 0.15), (-0.41, 0.15, z + 0.1), (0.41, 0.45, z - 0.05),
                                    (-0.41, -0.45, z - 0.1), (0.0, 0.0, z + 0.45), (0.2, 0.6, z + 0.38),
                                    (-0.2, -0.6, z + 0.38))):
        n = V((math.copysign(1, x), 0, 0)) if abs(x) > 0.1 else V((0, 0, 1))
        m = A.Matrix.Translation((x, y, zz)) @ n.to_track_quat("Z", "Y").to_matrix().to_4x4()
        for j in range(5):  # цветок-розетка: тёмная кайма и пять лепестков
            mm = m @ A.Matrix.Rotation(math.radians(72 * j + 20 * k), 4, "Z")
            a.box("petal" if k % 2 == 0 else "petal2", 0.04, 0.2, -0.05, 0.05, -0.02, 0.05, bevel=0, matrix=mm)
        a.prism("core", S.octagon(-0.06, 0.06, -0.06, 0.06, 0.02), -0.02, 0.08, matrix=m)
        a.prism("jagD", S.octagon(-0.13, 0.13, -0.13, 0.13, 0.04), -0.03, 0.0, matrix=m)
    part(a, "Head", "Body", (0, -0.85, z + 0.2))
    hc = V((0, -1.05, z + 0.42))
    A.ball(a, "jag", tuple(hc), 0.42, n=3, ry=0.38)
    A.snout(a, "jagL", tuple(hc + V((0, -0.3, -0.1))), (0, -1, -0.1), 0.24, 0.36, 0.3, 0.22, 0.2, nose_key="pink",
            nose=0.45, mouth=0.6)
    for s in S2:
        eye2(a, tuple(hc + V((s * 0.17, -0.36, 0.1))), 0.09, (s * 0.3, -1, 0.05), "sly", s, "jag", "jagD")
        a.prism("jag", S.octagon(-0.13, 0.13, -0.11, 0.11, 0.04), 0.0, 0.08, axis="y",
                matrix=A.Matrix.Translation(hc + V((s * 0.3, 0.05, 0.38))))  # круглое ухо
        a.prism("jagD", S.octagon(-0.08, 0.08, -0.07, 0.07, 0.03), -0.02, 0.0, axis="y",
                matrix=A.Matrix.Translation(hc + V((s * 0.3, 0.05, 0.38))))
        for k in range(2):  # усы
            a.box("white", s * 0.25 - 0.18, s * 0.25 + 0.18, -1.58, -1.56, hc.z - 0.18 + 0.06 * k, hc.z - 0.17 + 0.06 * k,
                  bevel=0, matrix=tilt((s * 0.25, -1.57, hc.z - 0.15), "Y", s * (8 - 16 * k)))
    part(a, "Tail", "Body", (0, 0.85, z + 0.1))
    kchain(a, "jag", [(0, 0.85, z + 0.1), (0, 1.35, z + 0.15), (0.2, 1.6, z + 0.65), (0.1, 1.5, z + 1.1)],
           [0.18, 0.16, 0.14, 0.12], up=(1, 0, 0))
    A.ball(a, "leaf", (0.1, 1.5, z + 1.18), 0.14, n=2)
    for j in range(5):  # бутон на кончике хвоста
        ang = math.radians(72 * j)
        spike(a, "petal", (0.1, 1.5, z + 1.2), (0.1 + 0.25 * math.cos(ang), 1.5 + 0.25 * math.sin(ang), z + 1.5), 0.13)
    face_point(a, tuple(hc + V((0, -0.4, 0.05))))
    closeup(a, (0.4, 0.0, z + 0.1), eye_off=(-0.5, -2.4, 0.8))
    a.pose = {"Head": ((0, 0, 15), (0, 0, 0)), "Tail": ((0, 0, -20), (0, 0, 0)), "LegFL": ((-20, 0, 0), (0, 0, 0))}
    return a


# ══ LEGENDARY ══════════════════════════════════════════════════════════════════════════════════════════════════

def sprout_flytrap():
    """10. Росток-мухоловка: малыш-мухоловка шагает на корнях-ножках под листом-зонтиком, крошечная корона набекрень
    (не копия королевы: один бутон-голова, улыбка-ловушка с зубками, лист над головой, ножки-корни).
    Признаки мухоловки: створки-челюсти с ресничками, малиновое нутро, стебель, листья, корни."""
    a = new("SproutFlytrap", {"leaf": ("43B649", True), "leafL": ("9BE15D", False), "leafD": ("23803A", False),
                              "maw": ("E2385A", False), "teeth": ("FFF4DA", False), "root": ("8F5A31", False),
                              "goldC": ("F5B21C", False), "gem": ("FF4FA3", False)})
    t = legendary_stand(a, 1.6)
    for s, nm in ((1, "LegL"), (-1, "LegR")):  # ножки-корни, шаг
        part(a, nm, "Stand", (s * 0.25, 0.0, t + 0.75))
        A.limb(a, "root", [(s * 0.25, 0.0, t + 0.85), (s * 0.35, -0.1 * s, t + 0.4), (s * 0.4, -0.25 * s, t + 0.06)],
               [0.2, 0.17, 0.14])
        for d in (-0.3, 0.0, 0.3):  # корешки-пальцы
            spike(a, "root", (s * 0.4, -0.25 * s, t + 0.06), (s * 0.4 + d, -0.25 * s - 0.3, t + 0.02), 0.08)
    part(a, "Body", "Stand", (0, 0, t + 0.9))
    A.body(a, "leaf", (0, 0, t + 0.7), 0.42, 0.4, 0.75, "egg", n=3, front=("leafL", 0.6, t + 0.8, t + 1.3))
    for s in S2:  # ручки-листья
        A.flipper(a, "leafL", (s * 0.38, -0.05, t + 1.2), (s * 0.95, -0.2, t + 1.0), 0.28, 0.12, thick=0.07,
                  up=(0, -0.3, 1))
    part(a, "Head", "Body", (0, -0.05, t + 1.45))
    hc = V((0, -0.05, t + 1.95))
    A.ball(a, "leaf", tuple(hc), 0.62, n=4, ry=0.55, rz=0.5)
    # пасть-ловушка: обод малиновый, зубки-реснички переплетены — улыбка во весь рот
    a.box("maw", -0.55, 0.55, -0.62, -0.5, hc.z - 0.22, hc.z - 0.08, bevel=0.01)
    for i in range(9):
        x = -0.48 + i * 0.12
        spike(a, "teeth", (x, -0.6, hc.z - 0.16), (x, -0.66, hc.z - 0.16 + (0.2 if i % 2 else -0.2)), 0.06)
    for s in S2:
        eye2(a, tuple(hc + V((s * 0.22, -0.52, 0.2))), 0.13, (s * 0.2, -1, 0.15), "goofy", s, "leaf", "leafD")
        a.box("blush", s * 0.42 - 0.08, s * 0.42 + 0.08, -0.58, -0.55, hc.z - 0.02, hc.z + 0.05, bevel=0)
    part(a, "Umbrella", "Head", (0, 0.0, hc.z + 0.45))
    kchain(a, "leafD", [(0, 0.0, hc.z + 0.4), (0.1, 0.05, hc.z + 1.05)], [0.1, 0.08], up=(0, -1, 0))
    A.flipper(a, "leaf", (0.1, -0.7, hc.z + 1.05), (0.1, 0.9, hc.z + 0.95), 1.3, 0.2, thick=0.1, bend=(0, 0, 0.3),
              up=(0, 0, 1))  # лист-зонтик над головой
    A.flipper(a, "leafL", (0.1, -0.5, hc.z + 1.13), (0.1, 0.7, hc.z + 1.05), 0.12, 0.05, thick=0.04, bend=(0, 0, 0.3),
              up=(0, 0, 1))  # жилка
    mc = A.Matrix.Translation(hc + V((0.25, 0.05, 0.45))) @ A.Matrix.Rotation(math.radians(-18), 4, "Y")
    a.prism("goldC", S.octagon(-0.17, 0.17, -0.15, 0.15, 0.05), 0.0, 0.1, matrix=mc)  # корона набекрень
    for j in range(5):
        ang = 2 * math.pi * j / 5
        px, py = 0.14 * math.cos(ang), 0.12 * math.sin(ang)
        a.frustum("goldC", (px - 0.05, px + 0.05, py - 0.04, py + 0.04), (px, px, py, py), 0.1, 0.26, bevel=0, matrix=mc)
    a.prism("gem", S.octagon(-0.05, 0.05, -0.05, 0.05, 0.02), 0.1, 0.16, matrix=mc @ A.Matrix.Translation((0, -0.1, 0)))
    face_point(a, tuple(hc + V((0, -0.55, 0.05))))
    closeup(a, (0.0, -0.3, t + 1.0))
    a.pose = {"LegL": ((-20, 0, 0), (0, 0, 0)), "LegR": ((15, 0, 0), (0, 0, 0)), "Umbrella": ((0, -12, 0), (0, 0, 0))}
    return a


CREATURES = [("FrogBubble", frog_bubble, "Лягушка-пузырь", "Common"),
             ("BigBeakToucan", big_beak_toucan, "Тукан-клювище", "Common"),
             ("PeriscopeChameleon", periscope_chameleon, "Хамелеон-перископ", "Common"),
             ("KnotSloth", knot_sloth, "Ленивец-узел", "Common"),
             ("ManyEyeCaterpillar", many_eye_caterpillar, "Гусеница-многоглазка", "Rare"),
             ("WheelMonkey", wheel_monkey, "Обезьяна-колесо", "Rare"),
             ("ThreeHeadParrot", three_head_parrot, "Попугай-трёхглав", "Rare"),
             ("TowerBeetle", tower_beetle, "Башня жуков", "Epic"),
             ("FlowerJaguar", flower_jaguar, "Ягуар-клумба", "Epic"),
             ("SproutFlytrap", sprout_flytrap, "Росток-мухоловка", "Legendary")]


def build(i, col):
    """Модель i для арены: один объект (без разбиения на части), подставка спрятана в землю."""
    art = CREATURES[i][1]()
    obj = art.build(col)
    return [obj]


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    repo = os.path.abspath(argv[0])
    only = argv[1:]
    shots = os.path.join(repo, "assets", "concepts", "bosses_5_10", "boss6_v2", "raw", "creatures")
    tmp = os.path.join(shots, "_quick")  # quick не пишет модели и карты, но папки нужны конвейеру
    items = [x for x in CREATURES if not only or x[0] in only]
    name = "report.json" if not only else "report_" + "+".join(only)[:120] + ".json"
    run(items, repo, shots, tmp, tmp, quick=True, report_name=name)


if __name__ == "__main__":
    main()
