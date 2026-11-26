"""Набор коллекции босса 7 «Копилка-громила» (Банк, D73): помощники существ и общие детали.

Берёт помощники эскизов концепта из scripts/blender/boss7/creatures.py (new, glow, kchain, taper, spike, eye2, front_y,
grin, coin, gemstone, jewel, round_ball, tri_ear, face_point, closeup) и подставки D71 из creature_kit; добавляет то,
что нужно 20 новым существам каталога docs/BOSS7_CATALOG.md: точки-накладки на шаре, ноги-столбики с копытцами,
лапы с когтями, пушистые хвосты из шаров, плоские пластины (крылья, плавники).
Координаты как у всех существ: z вверх, лицо в −y, t — верх подставки.
"""

import math
import os
import sys

from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
sys.path.insert(0, BL)
sys.path.insert(0, os.path.join(BL, "boss7"))
sys.path.insert(0, os.path.join(BL, "dragon10"))
from creatures import (A, K, S, S2, V, closeup, coin, common_stand, epic_stand, eye2, face_point, front_y,  # noqa: E402,F401
                       gemstone, glow, grin, jewel, kchain, legendary_stand, new, part, rare_stand, round_ball, spike,
                       taper, tilt, tri_ear, with_matrix)
import creatures as SK  # noqa: E402,F401  (эскизы концепта: 10 утверждённых существ)

__all__ = ["A", "K", "S", "S2", "V", "Matrix", "Vector", "math", "closeup", "coin", "common_stand", "epic_stand",
           "eye2", "face_point", "front_y", "gemstone", "glow", "grin", "jewel", "kchain", "legendary_stand", "new",
           "part", "rare_stand", "round_ball", "spike", "taper", "tilt", "tri_ear", "with_matrix", "SK", "dot",
           "dots_on_ball", "leg", "paw_claws", "fluff", "plate", "collect"]


def dot(a, key, p, normal, r=0.05, h=0.02):
    """Круглая точка-накладка (шестигранник) на поверхности p по нормали normal: выступ h, уходит внутрь на 0.03."""
    m = Matrix.Translation(V(p)) @ V(normal).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    pts = [(r * math.cos(math.radians(60 * i)), r * math.sin(math.radians(60 * i))) for i in range(6)]
    a.prism(key, pts, -0.03, h, bevel=0, matrix=m)


def dots_on_ball(a, key, c, rx, ry, rz, picks, r=0.05):
    """Точки на эллипсоиде (центр c, полуоси): picks = [(азимут°, высота −1…1)] — азимут от −y (лицо) по часовой."""
    for az, el in picks:
        t = math.radians(az)
        d = V((math.sin(t) * math.sqrt(1 - el * el), -math.cos(t) * math.sqrt(1 - el * el), el))
        p = V(c) + V((d.x * rx, d.y * ry, d.z * rz)) * 0.97
        dot(a, key, p, V((d.x / rx, d.y / ry, d.z / rz)), r=r)


def leg(a, key, hip, foot, w0, w1, hoof=None, hoof_h=0.1):
    """Нога-столбик от hip к foot (сужается w0 → w1); hoof — ключ копытца внизу (восьмигранник)."""
    hp, ft = V(hip), V(foot)
    A.limb(a, key, [hp, hp.lerp(ft, 0.5) + V((0, -0.02, 0)), ft + V((0, 0, hoof_h if hoof else 0))],
           [w0, (w0 + w1) / 2, w1], joints=False)
    if hoof:
        r = w1 * 0.62
        a.prism(hoof, S.octagon(ft.x - r, ft.x + r, ft.y - r * 1.1, ft.y + r * 0.9, r * 0.3), ft.z, ft.z + hoof_h + 0.02,
                bevel=0)


def paw_claws(a, key, p, fwd=(0, -1, 0), n=3, ln=0.12, w=0.05, spread=0.06):
    """Когти лапы: n тупых пирамидок вперёд от p."""
    f = V(fwd).normalized()
    side = V((-f.y, f.x, 0)).normalized() if abs(f.z) < 0.9 else V((1, 0, 0))
    for i in range(n):
        o = side * ((i - (n - 1) / 2) * spread)
        b = V(p) + o
        spike(a, key, b, b + f * ln + V((0, 0, -0.03)), w)


def fluff(a, keys, pts, rs, n=3):
    """Пушистый хвост или шерсть: цепочка шаров A.ball по точкам (радиусы rs), цвета по очереди."""
    for i, (p, r) in enumerate(zip(pts, rs)):
        A.ball(a, keys[i % len(keys)], tuple(p), r, n=n)


def plate(a, key, pts2, z0, z1, m):
    """Плоская пластина (крыло, плавник): многоугольник pts2 в осях m (x, y), толщина z0…z1 по локальной z."""
    a.extrude(key, pts2, z0, z1, axis="z", matrix=m)


def collect(order, own):
    """ITEMS в порядке каталога: order = [(id, функция | None, название, редкость)], own — функции этого модуля."""
    out = []
    for item_id, fn, title, rarity in order:
        out.append((item_id, fn or own[item_id], title, rarity))
    return out
