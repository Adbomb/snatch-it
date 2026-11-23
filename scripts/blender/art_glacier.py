"""Коллекция босса 5 «Йети-коллекционер» (Ледник) — ледяная коллекция, 30 существ по каталогу docs/BOSS5_CATALOG.md
(утверждён владельцем 2026-11-23). Стиль D39 v2 (эталон — фенек №20 босса 4): детали D39, подвижные части с точками
вращения (D18, D54, D55), корень — подставка Stand (в игре скрыта), запекание ×4, карты Common 512², Rare и выше
1024² (D64), FBX из частей и скелет rig.json в осях Roblox, кадры и отчёт — общий цикл creature_kit.run.
У каждого существа своя анатомия и своя «изюминка»; семьи силуэтов — как в каталоге (не больше 3 на семью).
Без людей, текста, логотипов, оружия и узнаваемых чужих персонажей (у оленя нос чёрный).

Пишет assets/models/art/boss5/<id>.{fbx,rig.json,blend}, assets/textures/art/boss5/<id>_{color,normal}.png, кадры —
в <кадры>/<id>_*.png и report_*.json.
Запуск: blender --background --factory-startup --python scripts/blender/art_glacier.py -- <репо> <кадры> [quick] [id…]
quick — без запекания и экспорта (материалы сборки).
"""

import math
import os
import sys

from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "dragon10"))
from creature_kit import (S, bar, chain, closed_eye, common_stand, d39v2, disc, epic_stand, gem,  # noqa: E402
                          legendary_stand, ngon, part, rare_stand, round_eye, run, stripe_chain, tilt, tube,
                          with_matrix)
import v4_kit as K  # noqa: E402

V = Vector
S2 = (1, -1)
BASE = {"white": ("FFFFFF", False), "dark": ("1B1B2A", False), "glint": ("FFFFFF", False),
        "mouth": ("5A1E2E", False), "blush": ("FF9FB2", False), "pink": ("FF7F9F", False),
        "ivory": ("F3E9D2", False), "snow": ("F4F8FF", True), "snowS": ("DCE8F7", False)}


def new(item_id, pal, rings=()):
    a = S.Art(f"Art_{item_id}", ring_z0=1.0)
    d39v2(a)
    for k, (code, r) in {**BASE, **pal}.items():
        a.paint(k, code, rings=r or k in rings)
    return a


def blob(a, key, c, rx, ry, rz, n=6, cut=0.38, z0=None, z1=None, matrix=None):
    """Эллипсоид ступенями D39: n ярусов-восьмигранников вокруг c (z0/z1 — обрезать снизу/сверху)."""
    lo = -rz if z0 is None else max(-rz, z0 - c[2])
    hi = rz if z1 is None else min(rz, z1 - c[2])
    for k in range(n):
        a0 = lo + (hi - lo) * k / n
        a1 = lo + (hi - lo) * (k + 1) / n
        zm = (a0 + a1) / 2
        f = max(math.sqrt(max(1 - (zm / rz) ** 2, 0.0)), 0.42)
        wx, wy = rx * f, ry * f
        a.prism(key, S.octagon(c[0] - wx, c[0] + wx, c[1] - wy, c[1] + wy, min(wx, wy) * cut),
                c[2] + a0 - (0.008 if k else 0), c[2] + a1 + 0.008, matrix=matrix)


def spike(a, key, base, tip, w):
    K.KEY = key
    K.spike(a, base, tip, w)


def kchain(a, key, pts, ws, hs=None, up=(0, -1, 0), cut=0.3, overlap=0.45):
    K.KEY = key
    K.chain(a, pts, ws, hs, up=up, cut=cut, overlap=overlap)


def taper(a, key, p0, p1, w0, w1, h0=None, h1=None, up=(0, 0, 1), cut=0.3):
    K.KEY = key
    K.taper(a, p0, p1, w0, w1, h0, h1, up=up, cut=cut)


def layered(a, key, prof, layers, anchor, xc=0.0, matrix=None):
    K.KEY = key
    K.layered(a, prof, layers, anchor, xc=xc, matrix=matrix)


def slab(a, key, prof, x0, x1, matrix=None):
    K.KEY = key
    K.slab(a, prof, x0, x1, matrix=matrix)


def eyes(a, x, y, z, r, look=(0.0, 0.0), lid=0.0, lid_key=None, pupil=0.6):
    for s in S2:
        round_eye(a, (s * x, y, z), r, look=look, pupil=pupil, lid=lid, lid_key=lid_key)


def cheeks(a, x, y, z, r=0.1):
    for s in S2:
        disc(a, "blush", s * x, z, r, y - 0.02, y + 0.01, n=8, axis="y", bevel=0)


def snowflake(a, key, c, r, w=0.05, axis="y"):
    """Снежинка из трёх брусков в плоскости лица (axis y) или горизонтальной (axis z)."""
    for ang in (0, 60, 120):
        if axis == "y":
            m = Matrix.Translation(c) @ Matrix.Rotation(math.radians(ang), 4, "Y")
            a.box(key, -w / 2, w / 2, -w / 2, w / 2, -r, r, bevel=0, matrix=m)
        else:
            m = Matrix.Translation(c) @ Matrix.Rotation(math.radians(ang), 4, "Z")
            a.box(key, -r, r, -w / 2, w / 2, -w / 2, w / 2, bevel=0, matrix=m)


def beanie(a, key, keyS, c, r, h, pom_key="white", n=4):
    """Вязаная шапка: купол ступенями, отворот другим цветом, помпон."""
    x, y, z = c
    a.frame(keyS, ngon(x, y, r + 0.03, 10), 0.12, z, z + h * 0.28, axis="z")
    blob(a, key, (x, y, z + h * 0.28), r, r, h * 0.72, n=n, z0=z + h * 0.28)
    blob(a, pom_key, (x, y, z + h * 1.02), r * 0.32, r * 0.32, r * 0.3, n=max(2, n - 1))


def face_point(a, p):
    a.face = tuple(p)


def closeup(a, target, eye_off=(-1.2, -2.2, 1.0)):
    t = V(target)
    a.closeup = (tuple(t + V(eye_off)), tuple(t))


# ══ COMMON (512²) ══════════════════════════════════════════════════════════════════════════════════════════════

def snowball_hamster():
    """1. Снежок-хомяк: свернулся в снежный ком — наружу мордочка с набитыми щеками, ушки, лапки со снежком."""
    a = new("SnowballHamster", {"tan": ("E9A15C", True), "cream": ("FFE7C4", False), "cheek": ("F5B98A", False)})
    t = common_stand(a, 1.3)
    part(a, "Body", "Stand", (0, 0.1, t + 0.4))
    blob(a, "snow", (0, 0.15, t + 1.22), 1.22, 1.18, 1.18, n=5, cut=0.42)
    for x, y, z, r in ((0.9, -0.42, t + 2.0, 0.32), (-1.05, 0.2, t + 1.7, 0.28), (0.3, 0.88, t + 2.2, 0.28)):
        blob(a, "snowS", (x, y, z), r, r, r, n=2)
    for s in S2:
        blob(a, "tan", (s * 0.56, -0.8, t + 0.14), 0.28, 0.34, 0.13, n=2)  # ступни
    part(a, "Head", "Body", (0, -0.7, t + 1.15))
    blob(a, "tan", (0, -0.82, t + 1.22), 0.86, 0.46, 0.78, n=4)
    blob(a, "cream", (0, -1.12, t + 0.98), 0.54, 0.26, 0.46, n=3)
    for s in S2:
        blob(a, "cheek", (s * 0.52, -1.06, t + 0.96), 0.38, 0.3, 0.33, n=3)
    eyes(a, 0.33, -1.24, t + 1.45, 0.16, look=(0.0, -0.1))
    disc(a, "pink", 0, t + 1.2, 0.09, -1.4, -1.3, n=8, axis="y")
    a.box("white", -0.12, 0.12, -1.39, -1.33, t + 0.8, t + 0.98, bevel=0.01)
    a.box("dark", -0.012, 0.012, -1.4, -1.38, t + 0.8, t + 0.98, bevel=0)
    for s, name in ((1, "EarL"), (-1, "EarR")):
        part(a, name, "Head", (s * 0.56, -0.62, t + 1.88))
        a.prism("tan", S.octagon(s * 0.56 - 0.33, s * 0.56 + 0.33, t + 1.82, t + 2.46, 0.13), -0.72, -0.52, axis="y")
        a.prism("pink", S.octagon(s * 0.56 - 0.18, s * 0.56 + 0.18, t + 1.94, t + 2.34, 0.07), -0.76, -0.71, axis="y")
    for s, name in ((1, "PawL"), (-1, "PawR")):
        part(a, name, "Body", (s * 0.4, -1.1, t + 0.62))
        blob(a, "tan", (s * 0.4, -1.32, t + 0.56), 0.2, 0.18, 0.16, n=2)
    part(a, "Snowball", "PawR", (0, -1.55, t + 0.6))
    blob(a, "snow", (0, -1.56, t + 0.66), 0.27, 0.25, 0.25, n=2)
    face_point(a, (0, -1.3, t + 1.3))
    closeup(a, (0.5, -0.9, t + 1.8))
    a.pose = {"Head": ((0, 8, -12), (0, 0, 0)), "EarL": ((0, -15, 0), (0, 0, 0)), "EarR": ((0, 10, 0), (0, 0, 0)),
              "PawR": ((-20, 0, 0), (0, 0, 0.05))}
    return a


def snowboard_penguin():
    """2. Пингвин-сноубордист: на доске, очки на лбу, шарф по ветру, ласты в стороны для равновесия."""
    a = new("SnowboardPenguin", {"navy": ("273A6E", True), "orange": ("FF9F1C", False), "board": ("FF5A3D", True),
                                 "boardS": ("FFD23F", False), "strap": ("2FB3A8", False), "gogF": ("F5B21C", False),
                                 "lens": ("7FF4FF", False), "scarf": ("E8384F", True), "scarfS": ("FFF3DC", False)})
    t = common_stand(a, 1.6)
    part(a, "Board", "Stand", (0, 0, t))
    a.prism("board", S.octagon(-1.62, 1.62, -0.48, 0.48, 0.44), t, t + 0.14)
    a.box("boardS", -1.15, 1.15, -0.14, 0.14, t + 0.14, t + 0.17, bevel=0)
    for s in S2:
        a.box("strap", s * 0.55 - 0.28, s * 0.55 + 0.28, -0.36, 0.36, t + 0.14, t + 0.26)
        a.box("orange", s * 0.55 - 0.24, s * 0.55 + 0.24, -0.5, 0.1, t + 0.26, t + 0.4)
    part(a, "Body", "Board", (0, 0, t + 0.4))
    z = t + 0.38
    body = [(-0.58, z), (-0.78, z + 0.75), (-0.72, z + 1.45), (-0.5, z + 1.75), (0.45, z + 1.75), (0.72, z + 1.3),
            (0.74, z + 0.6), (0.48, z)]
    layered(a, "navy", body, [(0.6, 1, 1), (0.78, 0.88, 0.9)], (0.05, z + 0.85))
    slab(a, "white", [(-0.64, z + 0.08), (-0.84, z + 0.75), (-0.78, z + 1.4), (-0.3, z + 1.4), (-0.3, z + 0.08)],
         -0.52, 0.52)
    a.frame("scarf", S.octagon(-0.72, 0.72, -0.8, 0.64, 0.28), 0.16, z + 1.5, z + 1.72, axis="z")
    part(a, "Head", "Body", (0, -0.05, z + 1.72))
    hz = z + 1.72
    blob(a, "navy", (0, 0.0, hz + 0.5), 0.6, 0.6, 0.55, n=5)
    slab(a, "white", [(-0.5, hz + 0.12), (-0.6, hz + 0.45), (-0.5, hz + 0.72), (-0.3, hz + 0.72), (-0.3, hz + 0.12)],
         -0.42, 0.42)
    eyes(a, 0.2, -0.6, hz + 0.48, 0.1)
    spike(a, "orange", (0, -0.55, hz + 0.3), (0, -0.98, hz + 0.24), 0.28)
    a.frame("strap", S.octagon(-0.62, 0.62, -0.6, 0.62, 0.24), 0.08, hz + 0.7, hz + 0.84, axis="z")
    for s in S2:
        a.box("gogF", s * 0.24 - 0.22, s * 0.24 + 0.22, -0.72, -0.56, hz + 0.64, hz + 0.94, bevel=0.02)
        a.box("lens", s * 0.24 - 0.15, s * 0.24 + 0.15, -0.76, -0.7, hz + 0.7, hz + 0.88, bevel=0)
    for s, name in ((1, "FlipperL"), (-1, "FlipperR")):
        part(a, name, "Body", (s * 0.72, 0.0, z + 1.3))
        kchain(a, "navy", [(s * 0.72, 0.0, z + 1.3), (s * 1.25, -0.1, z + 0.85), (s * 1.55, 0.0, z + 0.55)],
               [0.38, 0.32, 0.18], [0.14, 0.12, 0.1])
    part(a, "Scarf", "Body", (0.35, 0.6, z + 1.6))
    kchain(a, "scarf", [(0.35, 0.6, z + 1.6), (0.55, 0.95, z + 1.25), (0.8, 1.28, z + 1.1)], [0.4, 0.38, 0.36],
           [0.1, 0.1, 0.1], up=(0, -1, 0), cut=0.2)
    for k in (0.4, 0.75):
        p = V((0.35, 0.6, z + 1.6)).lerp(V((0.8, 1.28, z + 1.1)), k)
        a.box("scarfS", p.x - 0.21, p.x + 0.21, p.y - 0.07, p.y + 0.07, p.z - 0.07, p.z + 0.07, bevel=0)
    face_point(a, (0, -0.6, hz + 0.5))
    closeup(a, (0.4, -0.5, z + 0.9))
    a.pose = {"Body": ((0, -6, 8), (0, 0, 0)), "FlipperL": ((0, 18, 0), (0, 0, 0)),
              "FlipperR": ((0, -12, 0), (0, 0, 0)), "Head": ((-8, 0, -10), (0, 0, 0)), "Scarf": ((0, 0, 15), (0, 0, 0))}
    return a


def hockey_seal():
    """3. Тюлень-хоккеист: сидит столбиком, шлем, свитер с полосой, клюшка в ласте, шайба перед ним."""
    a = new("HockeySeal", {"seal": ("A9B8CC", True), "sealD": ("6F7F99", False), "sealL": ("DCE4EE", False),
                           "jersey": ("2E6FE0", True), "helmet": ("E8384F", True), "stick": ("C8893F", False)})
    t = common_stand(a, 1.55)
    part(a, "Body", "Stand", (0, 0.2, t + 0.3))
    z = t
    body = [(-0.55, z), (-0.8, z + 0.55), (-0.7, z + 1.3), (-0.5, z + 1.85), (0.38, z + 1.85), (0.52, z + 1.2),
            (1.0, z + 0.45), (1.55, z + 0.15), (1.55, z)]
    layered(a, "seal", body, [(0.52, 1, 1), (0.72, 0.9, 0.9)], (0.2, z + 0.9))
    slab(a, "jersey", [(-0.86, z + 0.85), (-0.77, z + 1.7), (0.46, z + 1.7), (0.6, z + 0.85)], -0.76, 0.76)
    slab(a, "white", [(-0.88, z + 1.08), (-0.86, z + 1.24), (0.55, z + 1.24), (0.6, z + 1.08)], -0.78, 0.78)
    for x, y, zz in ((0.3, 0.8, z + 0.45), (-0.3, 1.1, z + 0.35), (0.1, 1.35, z + 0.22)):
        a.box("sealD", x - 0.13, x + 0.13, y - 0.11, y + 0.11, zz - 0.07, zz + 0.07, bevel=0.01)
    part(a, "Tail", "Body", (0, 1.4, z + 0.12))
    for s in S2:
        spike(a, "sealD", (s * 0.25, 1.45, z + 0.12), (s * 0.68, 1.95, z + 0.08), 0.32)
    part(a, "Head", "Body", (0, -0.1, z + 1.85))
    hz = z + 1.85
    blob(a, "seal", (0, -0.12, hz + 0.42), 0.58, 0.55, 0.5, n=5)
    blob(a, "sealL", (0, -0.62, hz + 0.28), 0.36, 0.24, 0.22, n=3)
    disc(a, "dark", 0, hz + 0.38, 0.1, -0.9, -0.82, n=8, axis="y")
    eyes(a, 0.24, -0.55, hz + 0.56, 0.12)
    for s in S2:
        for dz in (0.0, 0.09):
            a.box("dark", s * 0.2 - 0.03, s * 0.2 + 0.03, -0.87, -0.83, hz + 0.2 + dz, hz + 0.24 + dz, bevel=0)
    a.prism("helmet", S.octagon(-0.6, 0.6, -0.58, 0.5, 0.22), hz + 0.68, hz + 0.92)
    a.frustum("helmet", (-0.6, 0.6, -0.58, 0.5), (-0.34, 0.34, -0.28, 0.26), hz + 0.92, hz + 1.12)
    a.box("white", -0.07, 0.07, -0.6, 0.52, hz + 0.92, hz + 1.14, bevel=0.01)
    a.box("helmet", -0.64, 0.64, -0.62, -0.5, hz + 0.62, hz + 0.72, bevel=0.01)
    part(a, "FlipperR", "Body", (-0.6, -0.2, z + 1.6))
    kchain(a, "seal", [(-0.6, -0.2, z + 1.6), (-0.82, -0.55, z + 1.2)], [0.3, 0.22], [0.13, 0.1], up=(0, 0, 1))
    part(a, "FlipperL", "Body", (0.6, -0.2, z + 1.6))
    kchain(a, "seal", [(0.6, -0.2, z + 1.6), (0.82, -0.62, z + 1.32), (0.76, -0.82, z + 1.24)], [0.3, 0.26, 0.22],
           [0.13, 0.11, 0.1], up=(0, 0, 1))
    part(a, "Stick", "FlipperL", (0.78, -0.82, z + 1.3))
    bar(a, "stick", (0.78, -0.84, z + 1.62), (0.88, -1.2, z + 0.16), 0.11)
    bar(a, "dark", (0.88, -1.24, z + 0.1), (0.32, -1.46, z + 0.06), 0.15, 0.11)
    part(a, "Puck", "Body", (-0.3, -1.42, z + 0.06))
    a.prism("dark", ngon(-0.3, -1.42, 0.22, 8), z, z + 0.13)
    face_point(a, (0, -0.6, hz + 0.45))
    closeup(a, (0.0, -0.8, z + 1.2))
    a.pose = {"Head": ((0, 0, 14), (0, 0, 0)), "FlipperL": ((-14, 0, 0), (0, 0, 0)), "Tail": ((10, 0, 0), (0, 0, 0)),
              "Puck": ((0, 0, 0), (0.25, 0, 0))}
    return a


def ushanka_hare():
    """4. Заяц в ушанке: беляк сидит столбиком, длинные уши торчат сквозь ушанку, пушистые щёки."""
    a = new("UshankaHare", {"fur": ("F4F8FF", True), "furS": ("DDE6F2", False), "hat": ("8A5A3C", True),
                            "hatF": ("C49A70", False), "earIn": ("FFB7C8", False), "gold": ("F2C230", False)})
    t = common_stand(a, 1.3)
    part(a, "Body", "Stand", (0, 0.1, t + 0.4))
    z = t
    body = [(-0.48, z), (-0.66, z + 0.7), (-0.5, z + 1.35), (-0.22, z + 1.62), (0.4, z + 1.55), (0.72, z + 0.95),
            (0.72, z)]
    layered(a, "fur", body, [(0.52, 1, 1), (0.7, 0.9, 0.9)], (0.1, z + 0.8))
    slab(a, "furS", [(-0.54, z + 0.3), (-0.7, z + 0.75), (-0.56, z + 1.25), (-0.3, z + 1.25), (-0.3, z + 0.3)],
         -0.36, 0.36)
    for s in S2:
        a.box("fur", s * 0.18, s * 0.6, -1.0, -0.2, z, z + 0.22)  # большие задние ступни
        a.box("furS", s * 0.22, s * 0.56, -1.06, -0.96, z + 0.02, z + 0.16, bevel=0)
    blob(a, "fur", (0, 0.86, z + 0.42), 0.26, 0.24, 0.24, n=3)  # хвостик
    part(a, "Head", "Body", (0, -0.12, z + 1.55))
    hz = z + 1.55
    blob(a, "fur", (0, -0.12, hz + 0.45), 0.56, 0.5, 0.5, n=5)
    for s in S2:  # пушистые щёки
        spike(a, "fur", (s * 0.45, -0.3, hz + 0.3), (s * 0.82, -0.25, hz + 0.18), 0.3)
    eyes(a, 0.24, -0.56, hz + 0.55, 0.12, look=(0.2, 0.0))
    disc(a, "pink", 0, hz + 0.36, 0.07, -0.66, -0.58, n=8, axis="y")
    a.box("mouth", -0.08, 0.08, -0.62, -0.58, hz + 0.24, hz + 0.27, bevel=0)
    a.box("white", -0.07, 0.07, -0.63, -0.58, hz + 0.14, hz + 0.24, bevel=0.005)
    cheeks(a, 0.36, -0.52, hz + 0.34, 0.08)
    part(a, "Hat", "Head", (0, -0.1, hz + 0.78))
    a.prism("hat", S.octagon(-0.62, 0.62, -0.6, 0.48, 0.22), hz + 0.72, hz + 1.05)
    a.frustum("hat", (-0.62, 0.62, -0.6, 0.48), (-0.42, 0.42, -0.42, 0.3), hz + 1.05, hz + 1.22)
    a.box("hatF", -0.66, 0.66, -0.7, -0.5, hz + 0.7, hz + 0.98, bevel=0.02)
    snowflake(a, "gold", V((0, -0.72, hz + 0.84)), 0.11, 0.04)
    for s, name in ((1, "FlapL"), (-1, "FlapR")):
        part(a, name, "Hat", (s * 0.66, -0.05, hz + 0.78))
        a.box("hat", s * 0.6, s * 0.74, -0.32, 0.26, hz + 0.18, hz + 0.8, bevel=0.03)
        a.box("hatF", s * 0.58, s * 0.76, -0.34, 0.28, hz + 0.16, hz + 0.24, bevel=0)
    for s, name in ((1, "EarL"), (-1, "EarR")):
        base = V((s * 0.24, 0.0, hz + 1.1))
        part(a, name, "Hat", tuple(base))
        with_matrix(a, Matrix.Translation(base) @ Matrix.Rotation(math.radians(s * 12), 4, "Y"))
        a.box("fur", -0.15, 0.15, -0.1, 0.1, 0.0, 1.0)
        a.box("fur", -0.11, 0.11, -0.08, 0.08, 1.0, 1.16)
        a.box("earIn", -0.08, 0.08, -0.13, -0.09, 0.1, 0.92, bevel=0)
        with_matrix(a, None)
    for s, name in ((1, "PawL"), (-1, "PawR")):
        part(a, name, "Body", (s * 0.3, -0.5, z + 1.15))
        bar(a, "fur", (s * 0.3, -0.5, z + 1.15), (s * 0.24, -0.72, z + 0.82), 0.2, 0.18)
    face_point(a, (0, -0.58, hz + 0.45))
    closeup(a, (0.3, -0.5, z + 0.8))
    a.pose = {"Head": ((0, 0, -10), (0, 0, 0)), "EarL": ((10, -14, 0), (0, 0, 0)), "EarR": ((-6, 20, 0), (0, 0, 0)),
              "FlapL": ((0, 18, 0), (0, 0, 0)), "PawR": ((-30, 0, 0), (0, 0, 0))}
    return a


def mitten_pika():
    """5. Пищуха в варежке: огромная вязаная варежка лежит, большой палец вверх; из манжеты выглядывает пищуха."""
    a = new("MittenPika", {"mitten": ("E8384F", True), "mittenS": ("FFF3DC", False), "pika": ("A88C74", True),
                           "pikaL": ("D9C2A8", False), "pom": ("FFF3DC", False)})
    t = common_stand(a, 1.6)
    part(a, "Mitten", "Stand", (0, 0.3, t + 0.3))
    z = t
    # варежка лежит на боку: ладонь — пухлый ком к +y, большой палец вверх, манжета к −y (вход)
    blob(a, "mitten", (0, 0.55, z + 0.62), 1.05, 1.0, 0.62, n=5, z0=z)
    blob(a, "mitten", (0.72, 0.15, z + 1.05), 0.3, 0.3, 0.55, n=4)  # большой палец
    for k in range(3):  # вязаные полоски
        y = 0.1 + k * 0.42
        a.box("mittenS", -1.0, 1.0, y - 0.07, y + 0.07, z + 1.08, z + 1.18, bevel=0)
    a.frame("mittenS", S.octagon(-0.88, 0.88, z + 0.02, z + 1.22, 0.3), 0.24, -0.72, -0.38, axis="y")  # манжета
    a.prism("dark", S.octagon(-0.64, 0.64, z + 0.24, z + 1.0, 0.22), -0.42, -0.36, axis="y")  # тёмный вход
    part(a, "Pom", "Mitten", (-0.75, -0.55, z + 1.2))
    bar(a, "mittenS", (-0.75, -0.55, z + 1.2), (-1.12, -0.8, z + 0.6), 0.06)
    blob(a, "pom", (-1.15, -0.82, z + 0.48), 0.22, 0.22, 0.22, n=3)
    part(a, "Pika", "Mitten", (0, -0.5, z + 0.55))
    blob(a, "pika", (0, -0.62, z + 0.72), 0.52, 0.42, 0.44, n=5)
    blob(a, "pikaL", (0, -0.94, z + 0.6), 0.3, 0.14, 0.22, n=3)
    eyes(a, 0.2, -1.0, z + 0.86, 0.1, look=(0.3, 0.1))
    disc(a, "dark", 0, z + 0.68, 0.06, -1.09, -1.03, n=6, axis="y")
    for s in S2:
        blob(a, "pika", (s * 0.3, -1.02, z + 0.28), 0.14, 0.14, 0.1, n=2)  # лапки на краю манжеты
    for s, name in ((1, "EarL"), (-1, "EarR")):
        part(a, name, "Pika", (s * 0.32, -0.62, z + 1.08))
        disc(a, "pika", s * 0.36, z + 1.24, 0.22, -0.7, -0.56, n=8, axis="y")
        disc(a, "pikaL", s * 0.36, z + 1.24, 0.12, -0.74, -0.69, n=8, axis="y", bevel=0)
    face_point(a, (0, -1.0, z + 0.8))
    closeup(a, (0.2, 0.0, z + 1.1), eye_off=(-1.3, -2.0, 1.2))
    a.pose = {"Pika": ((10, 0, -12), (0, -0.08, 0.04)), "EarL": ((0, 20, 0), (0, 0, 0)), "Pom": ((0, 18, 0), (0, 0, 0))}
    return a


def icicle_bat():
    """6. Летучая мышь-сосулька: висит вниз головой на ледяной перекладине, завернулась в крылья, как в плед."""
    a = new("IcicleBat", {"ice": ("9FE6FF", True), "iceD": ("4FC3EA", False), "bat": ("5B4A7A", True),
                          "batD": ("3E3158", False), "batIn": ("B28BD6", False)})
    t = common_stand(a, 1.3)
    part(a, "Perch", "Stand", (0, 0, t))
    z = t
    for s in S2:  # ледяная арка: две стойки и перекладина
        a.prism("ice", S.octagon(s * 1.0 - 0.16, s * 1.0 + 0.16, -0.16, 0.16, 0.06), z, z + 3.3)
        spike(a, "iceD", (s * 1.0, 0, z + 3.28), (s * 1.08, 0.02, z + 3.62), 0.26)
    a.box("ice", -1.18, 1.18, -0.16, 0.16, z + 3.1, z + 3.34)
    for x, h in ((-0.7, 0.55), (0.62, 0.42)):
        spike(a, "iceD", (x, 0, z + 3.1), (x, 0, z + 3.1 - h), 0.2)
    part(a, "Bat", "Perch", (0, 0, z + 3.1))
    for s in S2:  # лапки держат перекладину
        a.box("batD", s * 0.16 - 0.06, s * 0.16 + 0.06, -0.12, 0.12, z + 2.9, z + 3.2, bevel=0.01)
    blob(a, "bat", (0, 0, z + 2.3), 0.52, 0.42, 0.62, n=5)  # кокон из крыльев
    slab(a, "batIn", [(-0.42, z + 1.8), (-0.47, z + 2.3), (-0.4, z + 2.75), (-0.3, z + 2.75), (-0.3, z + 1.8)],
         -0.12, 0.12)  # шов складки спереди
    part(a, "WingL", "Bat", (0.42, -0.1, z + 2.7))
    slab(a, "bat", [(-0.3, z + 2.7), (-0.42, z + 2.3), (-0.3, z + 1.75), (0.05, z + 1.9), (0.1, z + 2.6)], 0.3, 0.52)
    part(a, "WingR", "Bat", (-0.42, -0.1, z + 2.7))
    slab(a, "bat", [(-0.3, z + 2.7), (-0.42, z + 2.3), (-0.3, z + 1.75), (0.05, z + 1.9), (0.1, z + 2.6)], -0.52, -0.3)
    part(a, "Head", "Bat", (0, -0.05, z + 1.75))
    blob(a, "bat", (0, -0.05, z + 1.45), 0.42, 0.38, 0.36, n=4)
    for s in S2:  # уши вниз (висит вниз головой)
        spike(a, "bat", (s * 0.26, -0.05, z + 1.18), (s * 0.4, -0.05, z + 0.82), 0.26)
        spike(a, "batIn", (s * 0.26, -0.11, z + 1.16), (s * 0.38, -0.11, z + 0.9), 0.14)
    for s in S2:  # глаза закрыты (дремлет): дуги, перевёрнутые — «довольная» улыбка вверх ногами
        closed_eye(a, (s * 0.17, -0.42, z + 1.5), 0.16, happy=True)
    a.box("white", 0.06, 0.12, -0.42, -0.38, z + 1.62, z + 1.72, bevel=0)  # клычок (вверх — висит вниз головой)
    cheeks(a, 0.28, -0.4, z + 1.38, 0.06)
    face_point(a, (0, -0.42, z + 1.45))
    closeup(a, (0.0, -0.3, z + 2.3), eye_off=(-1.0, -2.0, 0.4))
    a.pose = {"Bat": ((0, 10, 0), (0, 0, 0)), "WingL": ((0, 0, -14), (0, 0, 0)), "Head": ((10, 0, 0), (0, 0, 0))}
    return a


def scarf_caterpillar():
    """7. Гусеница-шарф: длинная вязаная полосатая гусеница аркой («пядь»), лапки — помпоны, шапочка."""
    a = new("ScarfCaterpillar", {"knitR": ("E8384F", True), "knitW": ("FFF3DC", True), "knitG": ("2FB3A8", False),
                                 "face": ("F7D9B0", False), "pom": ("FFD23F", False)})
    t = common_stand(a, 1.6)
    keys = ("knitR", "knitW")
    segs = [V((1.2, 0.3, t + 0.32)), V((0.85, 0.2, t + 0.9)), V((0.4, 0.0, t + 1.35)), V((-0.15, -0.15, t + 1.4)),
            V((-0.6, -0.3, t + 1.0)), V((-0.9, -0.4, t + 0.5))]
    names = ["Rear", "Mid", "Front"]
    groups = [(0, 2), (2, 4), (4, 6)]
    for gi, (i0, i1) in enumerate(groups):
        part(a, names[gi], "Stand" if gi == 0 else names[gi - 1], tuple(segs[i0]))
        for i in range(i0, i1):
            c = segs[i]
            blob(a, keys[i % 2], tuple(c), 0.42, 0.4, 0.38, n=3)
            for s in S2:  # лапки-помпоны снизу
                if c.z < t + 0.55:
                    blob(a, "pom", (c.x + s * 0.05, c.y + s * 0.3, t + 0.12), 0.12, 0.12, 0.11, n=2)
    part(a, "Head", "Front", (-0.9, -0.5, t + 0.75))
    hz = t + 0.75
    blob(a, "face", (-1.0, -0.7, hz + 0.25), 0.44, 0.38, 0.4, n=3)
    for s in S2:
        round_eye(a, (-1.0 + s * 0.18, -1.06, hz + 0.36), 0.1)
    a.box("mouth", -1.1, -0.9, -1.1, -1.06, hz + 0.12, hz + 0.15, bevel=0)
    beanie(a, "knitG", "knitW", (-1.0, -0.68, hz + 0.55), 0.36, 0.4, pom_key="pom", n=3)
    for s in S2:  # усики
        spike(a, "knitG", (-1.0 + s * 0.15, -0.6, hz + 0.98), (-1.0 + s * 0.32, -0.6, hz + 1.3), 0.06)
    face_point(a, (-1.0, -1.05, hz + 0.3))
    closeup(a, (0.4, 0.0, t + 1.4))
    a.pose = {"Mid": ((0, 0, -10), (0, 0, 0)), "Front": ((12, 0, 0), (0, 0, 0)), "Head": ((0, 0, 15), (0, 0, 0))}
    return a


def plow_crab():
    """8. Краб-снегоуборщик: в жёлтой каске, правая клешня — лопата со снегом, глаза на стебельках."""
    a = new("PlowCrab", {"crab": ("FF6B4A", True), "crabD": ("D9472E", False), "hat": ("FFC83D", True),
                         "shovel": ("8C97B5", False), "handle": ("C8893F", False)})
    t = common_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0, t + 0.5))
    z = t + 0.35
    blob(a, "crab", (0, 0.1, z + 0.35), 0.95, 0.72, 0.36, n=4)
    a.box("crabD", -0.6, 0.6, -0.64, -0.56, z + 0.2, z + 0.28, bevel=0)  # рот-полоса
    for s in S2:  # ноги: по три с каждой стороны
        for k, y in enumerate((-0.2, 0.15, 0.5)):
            kchain(a, "crabD", [(s * 0.8, y, z + 0.3), (s * 1.25, y + 0.05, z + 0.45), (s * 1.45, y + 0.1, t)],
                   [0.14, 0.12, 0.08], up=(0, 0, 1))
    a.prism("hat", S.octagon(-0.5, 0.5, -0.3, 0.6, 0.18), z + 0.68, z + 0.9)  # каска
    a.frustum("hat", (-0.5, 0.5, -0.3, 0.6), (-0.3, 0.3, -0.1, 0.4), z + 0.9, z + 1.08)
    a.box("hat", -0.62, 0.62, -0.42, 0.72, z + 0.66, z + 0.72, bevel=0.01)
    for s, name in ((1, "EyeL"), (-1, "EyeR")):
        part(a, name, "Body", (s * 0.28, -0.42, z + 0.6))
        bar(a, "crabD", (s * 0.28, -0.42, z + 0.6), (s * 0.34, -0.5, z + 1.05), 0.08)
        round_eye(a, (s * 0.34, -0.6, z + 1.12), 0.13, look=(0, -0.2))
    part(a, "ClawL", "Body", (0.8, -0.45, z + 0.35))
    kchain(a, "crab", [(0.8, -0.45, z + 0.35), (1.0, -0.9, z + 0.55)], [0.22, 0.2], up=(0, 0, 1))
    blob(a, "crab", (1.05, -1.1, z + 0.6), 0.24, 0.26, 0.2, n=3)
    spike(a, "crabD", (1.05, -1.3, z + 0.66), (1.0, -1.55, z + 0.75), 0.14)
    spike(a, "crabD", (1.05, -1.3, z + 0.52), (1.02, -1.55, z + 0.45), 0.14)
    part(a, "ClawR", "Body", (-0.8, -0.45, z + 0.35))
    kchain(a, "crab", [(-0.8, -0.45, z + 0.35), (-0.95, -0.85, z + 0.5)], [0.22, 0.2], up=(0, 0, 1))
    bar(a, "handle", (-0.95, -0.85, z + 0.5), (-0.85, -1.25, z + 0.2), 0.08)
    a.prism("shovel", S.octagon(-1.25, -0.45, -1.62, -1.22, 0.1), z + 0.02, z + 0.08)  # лопата
    a.box("shovel", -1.25, -0.45, -1.28, -1.22, z + 0.08, z + 0.3, bevel=0)
    blob(a, "snow", (-0.85, -1.42, z + 0.22), 0.36, 0.2, 0.18, n=3)  # снег на лопате
    face_point(a, (0, -0.65, z + 0.85))
    closeup(a, (0.0, -0.5, z + 0.4), eye_off=(-1.2, -2.0, 1.2))
    a.pose = {"EyeL": ((0, -15, 0), (0, 0, 0)), "EyeR": ((0, 10, 0), (0, 0, 0)), "ClawR": ((0, 0, 0), (0, 0, 0.18)),
              "ClawL": ((0, 0, -15), (0, 0, 0))}
    return a


def ski_lemming():
    """9. Лемминг-лыжник: на двух лыжах с палками, полосатый свитер, шапка с помпоном."""
    a = new("SkiLemming", {"fur": ("C98A4F", True), "furL": ("F1DCC0", False), "sweat": ("2E6FE0", True),
                           "sweatS": ("FFF3DC", False), "ski": ("E8384F", True), "pole": ("8C97B5", False),
                           "hat": ("FF9F1C", True)})
    t = common_stand(a, 1.6)
    part(a, "Skis", "Stand", (0, 0, t))
    for s in S2:
        x = s * 0.32
        a.box("ski", x - 0.15, x + 0.15, -1.5, 1.2, t, t + 0.08)
        a.prism("ski", S.octagon(x - 0.15, x + 0.15, t, t + 0.34, 0.05), -1.72, -1.5, axis="y")  # загнутый нос
        a.box("dark", x - 0.17, x + 0.17, -0.3, 0.2, t + 0.08, t + 0.2)  # крепление-ботинок
    part(a, "Body", "Skis", (0, 0, t + 0.3))
    z = t + 0.2
    blob(a, "sweat", (0, 0, z + 0.65), 0.58, 0.5, 0.58, n=4)
    for k in range(2):
        zz = z + 0.5 + k * 0.32
        a.frame("sweatS", ngon(0, 0, 0.56, 10), 0.08, zz, zz + 0.1, axis="z")
    part(a, "Head", "Body", (0, -0.05, z + 1.15))
    hz = z + 1.15
    blob(a, "fur", (0, -0.05, hz + 0.38), 0.52, 0.48, 0.45, n=4)
    blob(a, "furL", (0, -0.44, hz + 0.26), 0.3, 0.16, 0.2, n=2)
    eyes(a, 0.2, -0.46, hz + 0.48, 0.1)
    disc(a, "pink", 0, hz + 0.34, 0.06, -0.64, -0.58, n=6, axis="y")
    a.box("white", -0.06, 0.06, -0.62, -0.58, hz + 0.12, hz + 0.22, bevel=0.005)
    cheeks(a, 0.32, -0.42, hz + 0.3, 0.07)
    for s in S2:
        disc(a, "fur", s * 0.34, hz + 0.7, 0.13, -0.15, 0.05, n=8, axis="y")  # круглые ушки
    beanie(a, "hat", "sweatS", (0, -0.05, hz + 0.68), 0.46, 0.5)
    for s, name in ((1, "ArmL"), (-1, "ArmR")):
        part(a, name, "Body", (s * 0.52, 0.0, z + 0.9))
        bar(a, "sweat", (s * 0.52, 0.0, z + 0.9), (s * 0.78, -0.35, z + 0.6), 0.2, 0.18)
        blob(a, "fur", (s * 0.8, -0.4, z + 0.55), 0.1, 0.1, 0.1, n=2)
        bar(a, "pole", (s * 0.8, -0.42, z + 0.95), (s * 0.95, -0.3, t + 0.02), 0.06)
        disc(a, "pole", s * 0.93, -0.32, 0.12, t + 0.18, t + 0.22, n=6, bevel=0)
    face_point(a, (0, -0.48, hz + 0.4))
    closeup(a, (0.0, -0.4, z + 0.6))
    a.pose = {"Body": ((-8, 0, 0), (0, 0, 0)), "ArmL": ((-20, 0, 0), (0, 0, 0)), "ArmR": ((15, 0, 0), (0, 0, 0)),
              "Head": ((0, 0, 10), (0, 0, 0))}
    return a


def snowdrift_mole():
    """10. Крот-сугроб: звездорылый крот выглядывает из сугроба, на голове каска с фонариком."""
    a = new("SnowdriftMole", {"mole": ("4A4458", True), "moleD": ("2E2A38", False), "star": ("FF8FB0", False),
                              "hat": ("FFC83D", True), "neonLamp": ("FFF27A", False), "claw": ("F3E9D2", False)})
    t = common_stand(a, 1.6)
    part(a, "Drift", "Stand", (0, 0, t))
    blob(a, "snow", (0, 0.2, t + 0.3), 1.4, 1.3, 0.62, n=4, z0=t)
    for x, y, r in ((0.95, -0.7, 0.3), (-1.0, -0.55, 0.26), (0.4, 1.05, 0.28)):
        blob(a, "snowS", (x, y, t + 0.3), r, r, r * 0.8, n=3, z0=t)
    part(a, "Mole", "Drift", (0, -0.2, t + 0.7))
    blob(a, "mole", (0, -0.25, t + 1.05), 0.62, 0.55, 0.6, n=5)
    part(a, "Head", "Mole", (0, -0.4, t + 1.5))
    hz = t + 1.5
    blob(a, "mole", (0, -0.45, hz + 0.18), 0.5, 0.46, 0.42, n=4)
    for i in range(8):  # нос-звезда
        ang = math.radians(i * 45)
        p0 = V((0.0, -0.92, hz + 0.08))
        spike(a, "star", p0, p0 + V((0.24 * math.cos(ang), -0.06, 0.24 * math.sin(ang))), 0.1)
    disc(a, "star", 0, hz + 0.08, 0.09, -0.98, -0.88, n=8, axis="y")
    for s in S2:  # крошечные глаза
        disc(a, "dark", s * 0.2, hz + 0.32, 0.05, -0.86, -0.82, n=6, axis="y", bevel=0)
    a.prism("hat", S.octagon(-0.44, 0.44, -0.72, 0.1, 0.16), hz + 0.46, hz + 0.66)
    a.frustum("hat", (-0.44, 0.44, -0.72, 0.1), (-0.26, 0.26, -0.5, -0.1), hz + 0.66, hz + 0.82)
    a.box("hat", -0.52, 0.52, -0.82, 0.14, hz + 0.42, hz + 0.48, bevel=0.01)
    disc(a, "moleD", 0, hz + 0.62, 0.13, -0.86, -0.72, n=8, axis="y")
    disc(a, "neonLamp", 0, hz + 0.62, 0.09, -0.9, -0.85, n=8, axis="y", bevel=0)
    for s, name in ((1, "PawL"), (-1, "PawR")):
        part(a, name, "Mole", (s * 0.5, -0.6, t + 0.9))
        a.box("star", s * 0.38, s * 0.82, -1.0, -0.66, t + 0.62, t + 0.72)  # широкая розовая ладонь на снегу
        for dx in (0.0, 0.14, 0.28):
            x = s * (0.42 + dx)
            spike(a, "claw", (x, -1.0, t + 0.67), (x, -1.2, t + 0.62), 0.07)
    face_point(a, (0, -0.9, hz + 0.25))
    closeup(a, (0.5, -0.4, t + 0.6), eye_off=(-1.3, -2.0, 1.2))
    a.pose = {"Mole": ((0, 0, 0), (0, 0, 0.15)), "Head": ((0, 0, -14), (0, 0, 0)), "PawL": ((0, 0, 10), (0, 0, 0))}
    return a


def icecube_frog():
    """11. Лягушка-ледышка: вмёрзла в кубик льда по шею, лапки на краю, на макушке красная грелка."""
    a = new("IceCubeFrog", {"ice": ("A8E8FF", True), "iceE": ("E6FBFF", False), "frog": ("6CC24A", True),
                            "frogL": ("C8E86A", False), "bottle": ("E8384F", True), "cap": ("2E2A38", False)})
    t = common_stand(a, 1.4)
    part(a, "Cube", "Stand", (0, 0, t))
    a.extrude("ice", S.octagon(-1.0, 1.0, -0.9, 0.9, 0.18), t, t + 1.5, axis="z")
    for x in (-0.98, 0.98):
        a.box("iceE", x - 0.03, x + 0.03, -0.6, -0.3, t + 0.2, t + 1.3, bevel=0)  # блики
    a.box("iceE", -0.6, -0.2, -0.93, -0.9, t + 1.0, t + 1.36, bevel=0)
    part(a, "Frog", "Cube", (0, -0.05, t + 1.5))
    hz = t + 1.45
    blob(a, "frog", (0, -0.05, hz + 0.3), 0.78, 0.62, 0.42, n=4, z0=hz)
    blob(a, "frogL", (0, -0.42, hz + 0.18), 0.5, 0.26, 0.22, n=3, z0=hz)
    for s in S2:  # глаза на макушке — выпуклые
        blob(a, "frog", (s * 0.4, -0.2, hz + 0.68), 0.24, 0.22, 0.2, n=3)
        round_eye(a, (s * 0.4, -0.42, hz + 0.72), 0.14, look=(0, 0.1))
    a.box("mouth", -0.4, 0.4, -0.66, -0.62, hz + 0.22, hz + 0.26, bevel=0)
    cheeks(a, 0.52, -0.56, hz + 0.32, 0.07)
    part(a, "Bottle", "Frog", (0, 0.1, hz + 0.72))
    with_matrix(a, Matrix.Translation((0, 0.1, hz + 0.72)) @ Matrix.Rotation(math.radians(70), 4, "Y"))
    a.prism("bottle", S.octagon(-0.2, 0.2, -0.28, 0.28, 0.08), -0.5, 0.36, axis="x")
    a.prism("cap", S.octagon(-0.08, 0.08, -0.1, 0.1, 0.03), 0.36, 0.5, axis="x")
    with_matrix(a, None)
    for s, name in ((1, "ArmL"), (-1, "ArmR")):
        part(a, name, "Cube", (s * 0.62, -0.55, hz))
        a.box("frog", s * 0.5, s * 0.86, -0.95, -0.55, hz - 0.08, hz + 0.08)
        for dx in (-0.1, 0.06, 0.2):
            disc(a, "frogL", s * (0.68 + dx), -1.0, 0.07, hz + 0.02, hz + 0.1, n=6, bevel=0)
    face_point(a, (0, -0.65, hz + 0.45))
    closeup(a, (0.0, -0.9, t + 0.8), eye_off=(-1.2, -2.2, 0.6))
    a.pose = {"Frog": ((0, 0, 12), (0, 0, 0)), "Bottle": ((0, -15, 0), (0, 0, 0.05)), "ArmL": ((0, 12, 0), (0, 0, 0))}
    return a


def puffer_muskox():
    """12. Овцебычок-пуховик: шерсть до земли, как стёганый пуховик, рожки — наушники, чёлка на глазах."""
    a = new("PufferMuskOx", {"coat": ("7A5A44", True), "coatL": ("A27D5E", True), "horn": ("F3E9D2", False),
                             "nose": ("3A2A24", False), "hoof": ("2E2A38", False)})
    t = common_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0.2, t + 0.6))
    z = t
    for k, (zz, w, key) in enumerate(((z + 0.05, 1.3, "coat"), (z + 0.42, 1.24, "coatL"), (z + 0.79, 1.15, "coat"),
                                      (z + 1.12, 1.0, "coatL"))):  # стёганые ярусы
        a.prism(key, S.octagon(-w * 0.92, w * 0.92, -w * 0.95 + 0.25, w * 0.95 + 0.25, w * 0.32), zz, zz + 0.4)
    blob(a, "coat", (0, 0.25, z + 1.62), 0.82, 0.95, 0.32, n=3, z0=z + 1.5)  # горб
    for s in S2:
        for y in (-0.6, 0.95):
            a.box("hoof", s * 0.55 - 0.16, s * 0.55 + 0.16, y - 0.18, y + 0.18, z, z + 0.08, bevel=0.01)
    part(a, "Tail", "Body", (0, 1.4, z + 1.1))
    spike(a, "coat", (0, 1.38, z + 1.15), (0, 1.62, z + 0.75), 0.3)
    part(a, "Head", "Body", (0, -0.85, z + 1.3))
    hz = z + 1.0
    blob(a, "coat", (0, -1.05, hz + 0.32), 0.66, 0.58, 0.55, n=4)
    blob(a, "coatL", (0, -1.48, hz + 0.08), 0.42, 0.26, 0.28, n=3)  # светлая морда
    disc(a, "nose", 0, hz + 0.12, 0.14, -1.78, -1.7, n=8, axis="y")
    a.box("mouth", -0.14, 0.14, -1.76, -1.72, hz - 0.08, hz - 0.05, bevel=0)
    cheeks(a, 0.3, -1.62, hz - 0.02, 0.07)
    for s in S2:
        a.box("dark", s * 0.11 - 0.035, s * 0.11 + 0.035, -1.79, -1.76, hz + 0.1, hz + 0.16, bevel=0)
        # рожки — изогнуты вниз и вперёд, как дуги наушников; на концах круглые «чашки»
        kchain(a, "horn", [(s * 0.22, -1.0, hz + 0.78), (s * 0.68, -0.95, hz + 0.8), (s * 0.82, -1.0, hz + 0.4)],
               [0.22, 0.18, 0.15], up=(0, -1, 0))
        disc(a, "horn", s * 0.84, hz + 0.26, 0.2, -1.14, -0.88, n=8, axis="y")
    part(a, "Fringe", "Head", (0, -1.35, hz + 0.75))
    for i, x in enumerate((-0.34, -0.12, 0.12, 0.34)):  # чёлка над глазами — глаза видны
        spike(a, "coat", (x, -1.4, hz + 0.86), (x * 1.1, -1.62, hz + 0.6 + 0.04 * (i % 2)), 0.22)
    for s in S2:
        round_eye(a, (s * 0.24, -1.55, hz + 0.42), 0.09)
    face_point(a, (0, -1.6, hz + 0.3))
    closeup(a, (0.6, -0.4, z + 0.8))
    a.pose = {"Head": ((10, 0, 8), (0, 0, 0)), "Fringe": ((-8, 0, 0), (0, 0, 0)), "Tail": ((0, 18, 0), (0, 0, 0))}
    return a


COMMON = [("SnowballHamster", snowball_hamster, "Снежок-хомяк", "Common"),
          ("SnowboardPenguin", snowboard_penguin, "Пингвин-сноубордист", "Common"),
          ("HockeySeal", hockey_seal, "Тюлень-хоккеист", "Common"),
          ("UshankaHare", ushanka_hare, "Заяц в ушанке", "Common"),
          ("MittenPika", mitten_pika, "Пищуха в варежке", "Common"),
          ("IcicleBat", icicle_bat, "Летучая мышь-сосулька", "Common"),
          ("ScarfCaterpillar", scarf_caterpillar, "Гусеница-шарф", "Common"),
          ("PlowCrab", plow_crab, "Краб-снегоуборщик", "Common"),
          ("SkiLemming", ski_lemming, "Лемминг-лыжник", "Common"),
          ("SnowdriftMole", snowdrift_mole, "Крот-сугроб", "Common"),
          ("IceCubeFrog", icecube_frog, "Лягушка-ледышка", "Common"),
          ("PufferMuskOx", puffer_muskox, "Овцебычок-пуховик", "Common")]

# ══ RARE (1024²) ═══════════════════════════════════════════════════════════════════════════════════════════════

def fishing_walrus():
    """13. Морж-рыбак: сидит на льдине у лунки с удочкой, шапка с помпоном, бивни, усы, ведро с рыбой."""
    a = new("FishingWalrus", {"walrus": ("B87A55", True), "muzzle": ("E3C2A2", False), "nose": ("3A2418", False),
                              "hat": ("FF8A1F", True), "hatS": ("2FB3A8", False), "rod": ("6E4A2E", False),
                              "line": ("DDF6FF", False), "floe": ("DDF2FF", True), "hole": ("1F3A6E", False),
                              "iceE": ("EAFBFF", False), "bucket": ("8C97B5", True), "fish": ("FF9F1C", False),
                              "gold": ("F2C230", False)})
    t = rare_stand(a, 1.6)
    part(a, "Floe", "Stand", (0, 0, t))
    a.prism("floe", ngon(0, 0, 1.55, 10), t, t + 0.14)
    a.prism("hole", ngon(0.8, -0.9, 0.36, 8), t + 0.14, t + 0.16)
    a.frame("iceE", ngon(0.8, -0.9, 0.46, 8), 0.12, t + 0.14, t + 0.22, axis="z")
    z = t + 0.14
    part(a, "Body", "Floe", (0, 0.25, z + 0.6))
    blob(a, "walrus", (-0.1, 0.3, z + 0.85), 1.0, 0.92, 0.85, n=6)
    part(a, "Head", "Body", (-0.1, -0.35, z + 1.5))
    hz = z + 1.5
    blob(a, "walrus", (-0.1, -0.45, hz + 0.1), 0.66, 0.58, 0.55, n=5)
    for s in S2:
        x = -0.1 + s * 0.22
        blob(a, "muzzle", (x, -0.98, hz - 0.08), 0.28, 0.2, 0.24, n=3)
        for dz in (0.0, 0.1):
            a.box("dark", x - 0.03, x + 0.03, -1.19, -1.15, hz - 0.1 + dz, hz - 0.05 + dz, bevel=0)
        spike(a, "ivory", (-0.1 + s * 0.17, -1.05, hz - 0.22), (-0.1 + s * 0.22, -1.12, hz - 0.85), 0.14)
        round_eye(a, (-0.1 + s * 0.28, -0.98, hz + 0.32), 0.08)
    disc(a, "nose", -0.1, hz + 0.12, 0.1, -1.12, -1.04, n=8, axis="y")
    a.prism("hat", S.octagon(-0.62, 0.42, -0.85, 0.1, 0.2), hz + 0.48, hz + 0.75)
    a.frustum("hat", (-0.62, 0.42, -0.85, 0.1), (-0.38, 0.18, -0.6, -0.15), hz + 0.75, hz + 0.95)
    a.box("hatS", -0.65, 0.45, -0.88, 0.13, hz + 0.48, hz + 0.58, bevel=0.01)
    blob(a, "white", (-0.1, -0.38, hz + 1.08), 0.17, 0.17, 0.15, n=3)
    for s, name in ((1, "FlipperL"), (-1, "FlipperR")):
        part(a, name, "Body", (-0.1 + s * 0.85, -0.3, z + 0.95))
        kchain(a, "walrus", [(-0.1 + s * 0.85, -0.3, z + 0.95), (-0.1 + s * 1.0, -0.75, z + 0.5)], [0.36, 0.28],
               [0.18, 0.14], up=(0, 0, 1))
    part(a, "Rod", "FlipperL", (0.9, -0.78, z + 0.55))
    bar(a, "rod", (0.88, -0.72, z + 0.45), (1.25, -1.15, z + 2.2), 0.08)
    bar(a, "line", (1.25, -1.15, z + 2.2), (0.85, -0.95, z + 0.1), 0.025)
    a.box("gold", 0.82, 0.92, -1.0, -0.9, z + 0.28, z + 0.4, bevel=0)
    part(a, "Bucket", "Floe", (-1.05, -0.55, z))
    a.prism("bucket", ngon(-1.05, -0.55, 0.32, 8), z, z + 0.5)
    a.frame("iceE", ngon(-1.05, -0.55, 0.35, 8), 0.07, z + 0.42, z + 0.52, axis="z")
    part(a, "Fish", "Bucket", (-1.05, -0.55, z + 0.5))
    spike(a, "fish", (-1.05, -0.55, z + 0.45), (-1.12, -0.6, z + 0.95), 0.22)
    spike(a, "fish", (-1.12, -0.6, z + 0.95), (-1.25, -0.6, z + 1.12), 0.26)
    face_point(a, (-0.1, -1.05, hz + 0.1))
    closeup(a, (-0.1, -0.5, z + 0.9))
    a.pose = {"Head": ((0, 0, -12), (0, 0, 0)), "Rod": ((10, 0, 0), (0, 0, 0)), "Fish": ((0, 25, 0), (0, 0, 0.06))}
    return a


def earmuff_owl():
    """14. Полярная сова в наушниках: пятнистая, огромные жёлтые глаза, наушники-муфты, снежный пенёк."""
    a = new("EarmuffOwl", {"owl": ("F7FAFF", True), "owlF": ("FFFFFF", False), "yellow": ("FFD23F", False),
                           "beak": ("3A3A4A", False), "muff": ("FF6FAE", True), "muffB": ("8C97B5", False),
                           "spot": ("3A4256", False), "orange": ("FFB01C", False), "stump": ("8F5A31", True)})
    t = rare_stand(a, 1.3)
    part(a, "Stump", "Stand", (0, 0, t))
    a.prism("stump", ngon(0, 0, 0.72, 8), t, t + 0.5)
    a.prism("snow", ngon(0, 0, 0.78, 8), t + 0.5, t + 0.64)
    z = t + 0.64
    part(a, "Body", "Stump", (0, 0, z + 0.4))
    blob(a, "owl", (0, 0, z + 0.75), 0.85, 0.72, 0.78, n=5)
    for i, (x, zz) in enumerate(((-0.62, z + 1.1), (0.58, z + 0.85), (-0.7, z + 0.55), (0.25, z + 0.3),
                                 (-0.35, z + 0.22), (0.7, z + 0.42))):  # пестрины — одиночные штрихи
        c = V((x, -0.66 + abs(x) * 0.35, zz))
        a.box("spot", -0.09, 0.09, -0.03, 0.03, -0.025, 0.025, bevel=0,
              matrix=Matrix.Translation(c) @ Matrix.Rotation(math.radians(25 if i % 2 else -25), 4, "Y"))
    for s in S2:
        for dx in (-0.14, 0.0, 0.14):
            spike(a, "orange", (s * 0.3 + dx, -0.45, z + 0.06), (s * 0.3 + dx, -0.7, z - 0.04), 0.11)
    for s, name in ((1, "WingL"), (-1, "WingR")):
        part(a, name, "Body", (s * 0.72, 0.0, z + 1.2))
        slab(a, "owl", [(-0.4, z + 0.3), (-0.5, z + 1.15), (0.0, z + 1.4), (0.6, z + 1.05), (0.7, z + 0.25)],
             s * 0.68, s * 0.92)
    part(a, "Head", "Body", (0, 0, z + 1.45))
    hz = z + 1.45
    blob(a, "owl", (0, 0, hz + 0.42), 0.78, 0.66, 0.5, n=4)
    blob(a, "owlF", (0, -0.4, hz + 0.38), 0.62, 0.28, 0.4, n=3)
    for s in S2:
        round_eye(a, (s * 0.28, -0.66, hz + 0.44), 0.2, pupil=0.55)
        a.frame("yellow", ngon(s * 0.28, hz + 0.44, 0.24, 8), 0.06, -0.72, -0.66, axis="y")
        spike(a, "owl", (s * 0.42, -0.1, hz + 0.82), (s * 0.6, 0.0, hz + 1.15), 0.26)
        blob(a, "muff", (s * 0.82, -0.05, hz + 0.45), 0.22, 0.3, 0.3, n=3)
    spike(a, "beak", (0, -0.7, hz + 0.28), (0, -0.82, hz + 0.08), 0.16)
    kchain(a, "muffB", [(-0.82, -0.05, hz + 0.7), (-0.5, -0.05, hz + 1.0), (0, -0.05, hz + 1.08),
                        (0.5, -0.05, hz + 1.0), (0.82, -0.05, hz + 0.7)], [0.1] * 5, overlap=0.2)
    face_point(a, (0, -0.7, hz + 0.4))
    closeup(a, (0.4, -0.5, z + 0.8))
    a.pose = {"Head": ((0, 0, 25), (0, 0, 0)), "WingL": ((0, -20, 0), (0, 0, 0)), "WingR": ((0, 8, 0), (0, 0, 0))}
    return a


def icicle_hedgehog():
    """15. Ёжик-сосулька: колючки — ледяные сосульки, носик-кнопка, румяные щёки."""
    a = new("IcicleHedgehog", {"hedge": ("8A5A3C", True), "cream": ("F3D7B0", False), "iceS": ("7FE6FF", False),
                               "iceL": ("DFFBFF", False), "neonIce": ("6FF2FF", False)})
    t = rare_stand(a, 1.4)
    part(a, "Body", "Stand", (0, 0.1, t + 0.5))
    blob(a, "hedge", (0, 0.15, t + 0.82), 0.9, 1.05, 0.78, n=5)
    part(a, "Spines", "Body", (0, 0.3, t + 1.2))
    n = 0
    for el in (20, 45, 70, 90):
        for az in range(-150, 151, 30 if el < 80 else 60):
            ti, p = math.radians(az), math.radians(el)
            d = V((math.sin(ti) * math.cos(p), math.cos(ti) * math.cos(p) * 1.15 + 0.15, math.sin(p) * 0.85)).normalized()
            if d.y < -0.45 and el < 60:
                continue
            base = V((0, 0.15, t + 0.82)) + V((d.x * 0.8, d.y * 0.95, d.z * 0.7))
            spike(a, ("iceS", "iceL", "neonIce")[n % 3] if n % 5 else "iceL", base,
                  base + d * (0.62 + 0.12 * (n % 3)) + V((0, 0.18, 0)), 0.28)
            n += 1
    part(a, "Head", "Body", (0, -0.6, t + 0.75))
    blob(a, "cream", (0, -0.75, t + 0.72), 0.56, 0.4, 0.48, n=4)
    taper(a, "cream", (0, -1.0, t + 0.68), (0, -1.45, t + 0.6), 0.34, 0.12, 0.28, 0.12)
    blob(a, "dark", (0, -1.5, t + 0.61), 0.1, 0.08, 0.08, n=2)
    eyes(a, 0.23, -1.08, t + 0.9, 0.09)
    cheeks(a, 0.4, -1.0, t + 0.62, 0.08)
    for s, name in ((1, "FootL"), (-1, "FootR")):
        part(a, name, "Body", (s * 0.42, -0.55, t + 0.15))
        blob(a, "cream", (s * 0.42, -0.62, t + 0.1), 0.17, 0.22, 0.1, n=2)
    face_point(a, (0, -1.1, t + 0.8))
    closeup(a, (0.3, 0.2, t + 1.4), eye_off=(-1.2, -2.0, 1.2))
    a.pose = {"Head": ((0, 0, 14), (0, 0, 0)), "Spines": ((-6, 0, 0), (0, 0, 0.04)), "FootL": ((-20, 0, 0), (0, 0, 0))}
    return a


def baker_cub():
    """16. Медвежонок-пекарь: белый медвежонок в колпаке и фартуке несёт поднос с печеньем-снежинками."""
    a = new("BakerCub", {"fur": ("F4F8FF", True), "furS": ("DCE6F2", False), "nose": ("2E2A38", False),
                         "apron": ("FF8FB0", True), "hat": ("FFFFFF", True), "tray": ("C9D3E6", False),
                         "cookie": ("E0A45A", False), "icing": ("FFFFFF", False)})
    t = rare_stand(a, 1.4)
    part(a, "Body", "Stand", (0, 0, t + 0.6))
    z = t
    for s in S2:
        blob(a, "fur", (s * 0.36, -0.12, z + 0.32), 0.3, 0.38, 0.32, n=2)  # ножки
        disc(a, "furS", s * 0.36, z + 0.22, 0.14, -0.52, -0.48, n=8, axis="y", bevel=0)
    blob(a, "fur", (0, 0, z + 1.05), 0.72, 0.6, 0.7, n=4)
    slab(a, "apron", [(-0.62, z + 0.5), (-0.66, z + 1.1), (-0.56, z + 1.45), (-0.4, z + 1.45), (-0.4, z + 0.5)],
         -0.42, 0.42)
    snowflake(a, "icing", V((0, -0.68, z + 0.95)), 0.13, 0.04)
    part(a, "Head", "Body", (0, -0.05, z + 1.65))
    hz = z + 1.65
    blob(a, "fur", (0, -0.05, hz + 0.42), 0.6, 0.54, 0.5, n=4)
    blob(a, "furS", (0, -0.5, hz + 0.28), 0.3, 0.18, 0.22, n=2)
    disc(a, "nose", 0, hz + 0.36, 0.09, -0.7, -0.62, n=8, axis="y")
    a.box("mouth", -0.1, 0.1, -0.68, -0.64, hz + 0.14, hz + 0.17, bevel=0)
    eyes(a, 0.24, -0.52, hz + 0.56, 0.1)
    cheeks(a, 0.38, -0.48, hz + 0.32, 0.08)
    for s in S2:
        disc(a, "fur", s * 0.42, hz + 0.86, 0.16, -0.12, 0.08, n=8, axis="y")
    part(a, "Hat", "Head", (0, -0.05, hz + 0.88))
    a.prism("hat", ngon(0, -0.05, 0.42, 10), hz + 0.82, hz + 1.02)
    for dx, dz in ((-0.22, 0.0), (0.22, 0.0), (0.0, 0.1)):
        blob(a, "hat", (dx, -0.05, hz + 1.18 + dz), 0.3, 0.3, 0.24, n=2)
    for s, name in ((1, "ArmL"), (-1, "ArmR")):
        part(a, name, "Body", (s * 0.62, -0.05, z + 1.4))
        bar(a, "fur", (s * 0.62, -0.05, z + 1.4), (s * 0.62, -0.55, z + 1.15), 0.24, 0.22)
        blob(a, "fur", (s * 0.6, -0.68, z + 1.15), 0.14, 0.14, 0.13, n=2)
    part(a, "Tray", "ArmL", (0, -0.78, z + 1.22))
    a.prism("tray", S.octagon(-0.72, 0.72, -1.1, -0.5, 0.1), z + 1.2, z + 1.26)
    a.frame("tray", S.octagon(-0.72, 0.72, -1.1, -0.5, 0.1), 0.06, z + 1.26, z + 1.34, axis="z")
    for x in (-0.44, 0.0, 0.44):
        disc(a, "cookie", x, -0.8, 0.17, z + 1.26, z + 1.33, n=8, bevel=0)
        snowflake(a, "icing", V((x, -0.8, z + 1.345)), 0.12, 0.03, axis="z")
    face_point(a, (0, -0.6, hz + 0.45))
    closeup(a, (0.0, -0.8, z + 1.3), eye_off=(-0.9, -1.6, 1.0))
    a.pose = {"Head": ((0, 0, -10), (0, 0, 0)), "Hat": ((0, 12, 0), (0, 0, 0)), "Tray": ((0, 6, 0), (0, 0, 0.05))}
    return a


def puffin_postman():
    """17. Тупик-почтальон: чёрная спина, белые щёки, полосатый клюв, синяя фуражка, сумка с конвертами."""
    a = new("PuffinPostman", {"black": ("23263A", True), "white2": ("F7F7FA", False), "beakO": ("FF7A1A", False),
                              "beakY": ("FFC83D", False), "cap": ("2E5BD8", True), "capS": ("FFD23F", False),
                              "bag": ("A9582C", True), "paper": ("FFFFFF", False), "stamp": ("2FB3A8", False),
                              "orange": ("FF8A1F", False)})
    t = rare_stand(a, 1.3)
    part(a, "Body", "Stand", (0, 0, t + 0.6))
    z = t
    for s in S2:
        a.box("orange", s * 0.28 - 0.18, s * 0.28 + 0.18, -0.45, 0.05, z, z + 0.14)
    blob(a, "black", (0, 0.05, z + 0.85), 0.62, 0.58, 0.75, n=5)
    slab(a, "white2", [(-0.5, z + 0.25), (-0.62, z + 0.85), (-0.52, z + 1.35), (-0.3, z + 1.35), (-0.3, z + 0.25)],
         -0.42, 0.42)
    part(a, "Head", "Body", (0, -0.05, z + 1.5))
    hz = z + 1.5
    blob(a, "black", (0, -0.05, hz + 0.38), 0.52, 0.48, 0.45, n=4)
    for s in S2:
        a.prism("white2", S.octagon(s * 0.05, s * 0.5, hz + 0.15, hz + 0.65, 0.1), -0.56, -0.44, axis="y")
    eyes(a, 0.22, -0.58, hz + 0.48, 0.08)
    for key, y0, y1, h in (("beakY", -0.6, -0.72, 0.28), ("beakO", -0.72, -0.9, 0.22), ("beakY", -0.9, -0.98, 0.14)):
        a.frustum(key, (-0.12, 0.12, hz + 0.3 - h, hz + 0.3 + h * 0.6),
                  (-0.08, 0.08, hz + 0.3 - h * 0.6, hz + 0.3 + h * 0.4), y0, y1, axis="y")
    part(a, "Cap", "Head", (0, -0.05, hz + 0.78))
    a.prism("cap", ngon(0, 0.0, 0.46, 10), hz + 0.72, hz + 0.96)
    a.prism("cap", S.octagon(-0.36, 0.36, -0.66, -0.3, 0.1), hz + 0.72, hz + 0.78)
    a.box("capS", -0.12, 0.12, -0.48, -0.42, hz + 0.78, hz + 0.9, bevel=0)
    for s, name in ((1, "WingL"), (-1, "WingR")):
        part(a, name, "Body", (s * 0.58, 0.0, z + 1.2))
        slab(a, "black", [(-0.35, z + 0.45), (-0.42, z + 1.15), (0.0, z + 1.35), (0.5, z + 0.9), (0.55, z + 0.35)],
             s * 0.55, s * 0.72)
    part(a, "Bag", "Body", (0.45, 0.0, z + 1.2))
    bar(a, "bag", (-0.4, -0.5, z + 1.38), (0.55, -0.45, z + 0.7), 0.1, 0.04)
    a.box("bag", 0.45, 0.95, -0.55, 0.0, z + 0.4, z + 0.85, bevel=0.03)
    a.box("bag", 0.43, 0.97, -0.58, -0.4, z + 0.68, z + 0.87, bevel=0.02)
    part(a, "Letter", "Bag", (0.7, -0.3, z + 0.85))
    a.box("paper", 0.55, 0.85, -0.34, -0.3, z + 0.82, z + 1.12, bevel=0.005)
    a.box("stamp", 0.74, 0.82, -0.36, -0.34, z + 1.02, z + 1.1, bevel=0)
    face_point(a, (0, -0.6, hz + 0.4))
    closeup(a, (0.2, -0.5, z + 0.9))
    a.pose = {"Head": ((0, 0, 12), (0, 0, 0)), "Cap": ((0, -10, 0), (0, 0, 0)), "Letter": ((0, 0, 0), (0, 0, 0.1)),
              "WingR": ((0, 25, 0), (0, 0, 0))}
    return a


def sleepy_irbis():
    """18. Ирбис-соня: снежный барс свернулся калачиком, хвост-шарф с кисточкой, рядом кружка какао."""
    a = new("SleepyIrbis", {"fur": ("E8E6E0", True), "furS": ("F7F6F2", False), "ros": ("4A4E5E", False),
                            "nose": ("FF9FB2", False), "mug": ("2FB3A8", True), "cocoa": ("6E4128", False),
                            "marsh": ("FFFFFF", False)})
    t = rare_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0.2, t + 0.5))
    z = t
    blob(a, "fur", (0.1, 0.25, z + 0.48), 1.15, 0.85, 0.5, n=4, z0=z)
    for x, y in ((-0.5, 0.0), (0.2, 0.55), (0.75, 0.05), (0.45, 0.7), (-0.3, 0.75)):  # розетки (вразброс)
        a.frame("ros", ngon(x, y, 0.14, 6), 0.05, z + 0.86, z + 0.92, axis="z")
    part(a, "Head", "Body", (-0.65, -0.35, z + 0.6))
    hz = z + 0.55
    blob(a, "fur", (-0.65, -0.55, hz + 0.38), 0.6, 0.52, 0.45, n=4)
    blob(a, "furS", (-0.65, -0.98, hz + 0.26), 0.3, 0.15, 0.17, n=2)
    disc(a, "nose", -0.65, hz + 0.36, 0.08, -1.14, -1.08, n=6, axis="y")
    a.box("ros", -0.71, -0.59, -1.1, -1.06, hz + 0.18, hz + 0.21, bevel=0)
    for s in S2:
        a.box("ros", -0.65 + s * 0.24 - 0.13, -0.65 + s * 0.24 + 0.13, -1.06, -1.02, hz + 0.48, hz + 0.53,
              bevel=0)  # сомкнутые веки
        spike(a, "fur", (-0.65 + s * 0.34, -0.55, hz + 0.72), (-0.65 + s * 0.46, -0.5, hz + 1.02), 0.24)
        spike(a, "ros", (-0.65 + s * 0.42, -0.52, hz + 0.92), (-0.65 + s * 0.48, -0.5, hz + 1.06), 0.1)
        blob(a, "furS", (-0.65 + s * 0.3, -1.05, z + 0.12), 0.18, 0.2, 0.1, n=2)  # лапы под подбородком
    for x, zz in ((-0.95, hz + 0.62), (-0.32, hz + 0.55)):  # розетки на лбу — по одной с разной высоты
        a.frame("ros", ngon(x, zz, 0.08, 6), 0.03, -0.98, -0.94, axis="y")
    part(a, "Tail", "Body", (0.95, 0.4, z + 0.4))
    tube(a, ("fur", "furS"), [(0.95, 0.4, z + 0.4), (1.2, -0.2, z + 0.42), (0.8, -0.75, z + 0.42),
                              (0.0, -0.95, z + 0.42)], 0.26)
    part(a, "TailTip", "Tail", (0.0, -0.95, z + 0.42))
    tube(a, ("ros",), [(0.0, -0.95, z + 0.42), (-0.35, -1.05, z + 0.5)], 0.3)
    part(a, "Mug", "Body", (-1.25, 0.35, z))
    a.prism("mug", ngon(-1.25, 0.35, 0.24, 8), z, z + 0.42)
    a.prism("cocoa", ngon(-1.25, 0.35, 0.19, 8), z + 0.42, z + 0.44)
    a.frame("mug", S.octagon(-0.16, 0.16, -0.14, 0.14, 0.05), 0.06, -0.04, 0.04, axis="y",
            matrix=Matrix.Translation((-1.53, 0.35, z + 0.22)))
    blob(a, "marsh", (-1.2, 0.3, z + 0.5), 0.09, 0.09, 0.07, n=2)
    face_point(a, (-0.65, -1.05, hz + 0.4))
    closeup(a, (0.2, 0.3, z + 0.9), eye_off=(-1.0, -2.2, 1.4))
    a.pose = {"Head": ((0, 0, 10), (0, 0, 0)), "Tail": ((0, 0, -10), (0, 0, 0)), "TailTip": ((0, 0, 20), (0, 0, 0))}
    return a


def snowflake_star():
    """19. Морская звезда-снежинка: шагает на двух лучах, верхние лучи машут, кончики — снежинки, шапочка."""
    a = new("SnowflakeStar", {"star": ("FF8A5C", True), "starL": ("FFC4A8", False), "flake": ("DFFBFF", False),
                              "hat": ("6B3FB8", True), "hatS": ("FFF3DC", False)})
    t = rare_stand(a, 1.4)
    c = V((0, 0, t + 1.6))
    part(a, "Body", "Stand", tuple(c))
    a.prism("star", ngon(0, c.z, 0.55, 10), -0.18, 0.18, axis="y")
    a.prism("starL", ngon(0, c.z, 0.32, 10), -0.22, -0.17, axis="y")
    eyes(a, 0.15, -0.22, c.z + 0.05, 0.08)
    a.box("mouth", -0.08, 0.08, -0.24, -0.21, c.z - 0.14, c.z - 0.11, bevel=0)

    def ray(name, ang, length, flake=True):
        d = V((math.sin(math.radians(ang)), 0, math.cos(math.radians(ang))))
        p0 = c + d * 0.42
        part(a, name, "Body", tuple(p0))
        p1 = p0 + d * length
        taper(a, "star", tuple(p0), tuple(p1), 0.46, 0.22, 0.3, 0.18, up=(0, -1, 0))
        if flake:
            q = p0 + d * length * 0.6
            for sd in (-1, 1):
                e = V((math.sin(math.radians(ang + sd * 50)), 0, math.cos(math.radians(ang + sd * 50))))
                bar(a, "flake", tuple(q), tuple(q + e * 0.28), 0.06)
            spike(a, "flake", tuple(p1), tuple(p1 + d * 0.22), 0.14)

    ray("ArmL", 70, 0.75)
    ray("ArmR", -70, 0.75)
    ray("LegL", 150, 1.0, flake=False)
    ray("LegR", -150, 1.0, flake=False)
    ray("Top", 0, 0.42, flake=False)
    beanie(a, "hat", "hatS", tuple(c + V((0, 0, 0.82))), 0.22, 0.34)
    face_point(a, (0, -0.25, c.z))
    closeup(a, (0.0, -0.2, c.z), eye_off=(-1.0, -2.0, 0.6))
    a.pose = {"ArmL": ((0, -25, 0), (0, 0, 0)), "ArmR": ((0, 15, 0), (0, 0, 0)), "LegL": ((0, 10, 0), (0, 0, 0)),
              "Top": ((0, 12, 0), (0, 0, 0))}
    return a


def skating_seahorse():
    """20. Морской конёк на коньках: S-изгиб, хвост завитком на ботинке конька, шарф, гребень."""
    a = new("SkatingSeahorse", {"horse": ("2FC4C0", True), "horseL": ("A8F0E0", False), "fin": ("FFD23F", False),
                                "blade": ("C9D3E6", False), "boot": ("FFFFFF", True), "scarf": ("FF6FAE", True)})
    t = rare_stand(a, 1.2)
    part(a, "Skate", "Stand", (0, 0, t))
    a.box("blade", -0.06, 0.06, -0.8, 0.7, t, t + 0.12)
    a.prism("blade", S.octagon(-0.06, 0.06, t, t + 0.24, 0.04), -0.95, -0.8, axis="y")
    a.box("boot", -0.22, 0.22, -0.55, 0.45, t + 0.12, t + 0.5, bevel=0.03)
    part(a, "Tail", "Skate", (0, 0.1, t + 0.5))
    tube(a, ("horse", "horseL"), [(0, 0.2, t + 0.5), (0, 0.55, t + 0.75), (0, 0.6, t + 1.15), (0, 0.25, t + 1.3)], 0.26)
    part(a, "Body", "Tail", (0, 0.1, t + 1.25))
    pts = [V((0, 0.15, t + 1.2)), V((0, -0.15, t + 1.7)), V((0, -0.05, t + 2.3)), V((0, 0.15, t + 2.75))]
    kchain(a, "horse", [tuple(p) for p in pts], [0.72, 0.9, 0.8, 0.62], up=(0, -1, 0))
    for k in range(4):
        p = pts[1].lerp(pts[2], k / 3)
        a.box("horseL", -0.3, 0.3, p.y - 0.48, p.y - 0.4, p.z - 0.07, p.z + 0.07, bevel=0)
    part(a, "Fin", "Body", (0, 0.35, t + 2.1))
    for k in range(3):
        spike(a, "fin", (0, 0.32, t + 1.85 + k * 0.22), (0, 0.65, t + 1.9 + k * 0.24), 0.18)
    a.frame("scarf", S.octagon(-0.4, 0.4, -0.4, 0.5, 0.12), 0.12, t + 2.4, t + 2.56, axis="z")
    kchain(a, "scarf", [(0.2, 0.3, t + 2.45), (0.45, 0.65, t + 2.3)], [0.22, 0.2], [0.06, 0.06])
    part(a, "Head", "Body", (0, 0.1, t + 2.8))
    hz = t + 2.8
    blob(a, "horse", (0, 0.05, hz + 0.25), 0.46, 0.52, 0.42, n=4)
    taper(a, "horse", (0, -0.35, hz + 0.16), (0, -1.0, hz + 0.04), 0.32, 0.2, 0.3, 0.2)  # морда-трубочка
    for s in S2:  # глаза по бокам головы
        a.prism("white", ngon(-0.12, hz + 0.34, 0.16, 8), s * 0.4, s * 0.47, axis="x")
        a.prism("dark", ngon(-0.16, hz + 0.35, 0.08, 8), s * 0.46, s * 0.5, axis="x", bevel=0)
    for k in range(3):
        spike(a, "fin", (0, 0.05 + k * 0.1, hz + 0.45), (0, 0.15 + k * 0.12, hz + 0.72), 0.12)
    face_point(a, (0.4, -0.3, hz + 0.25))
    closeup(a, (0.0, -0.2, t + 1.9), eye_off=(-1.4, -1.8, 0.6))
    a.pose = {"Body": ((0, 0, 10), (0, 0, 0)), "Head": ((-10, 0, 0), (0, 0, 0)), "Tail": ((6, 0, 0), (0, 0, 0))}
    return a


def sled_badger():
    """21. Барсук на санках с печкой: санки с полозьями, буржуйка с огоньком и дымком, верёвка в лапах."""
    a = new("SledBadger", {"wood": ("C8893F", True), "runner": ("E8384F", False), "grey": ("8C8C96", True),
                           "black": ("23232E", False), "stove": ("3A3A48", True), "neonFire": ("FF8A1F", False),
                           "smoke": ("E6EAF2", False), "rope": ("F2E6C8", False)})
    t = rare_stand(a, 1.6)
    part(a, "Sled", "Stand", (0, 0, t))
    for s in S2:
        a.box("runner", s * 0.55 - 0.06, s * 0.55 + 0.06, -1.1, 1.2, t, t + 0.08)
        a.prism("runner", S.octagon(-0.06, 0.06, t, t + 0.45, 0.03), -1.35, -1.1, axis="y",
                matrix=Matrix.Translation((s * 0.55, 0, 0)))
        for y in (-0.6, 0.4):
            a.box("runner", s * 0.55 - 0.05, s * 0.55 + 0.05, y - 0.05, y + 0.05, t + 0.08, t + 0.3, bevel=0)
    for k in range(5):
        y = -1.0 + k * 0.48
        a.box("wood", -0.72, 0.72, y - 0.2, y + 0.2, t + 0.3, t + 0.4)
    z = t + 0.4
    part(a, "Stove", "Sled", (0, 0.85, z))
    a.box("stove", -0.34, 0.34, 0.55, 1.15, z, z + 0.7, bevel=0.03)
    a.box("neonFire", -0.16, 0.16, 0.5, 0.56, z + 0.15, z + 0.42, bevel=0)
    a.prism("stove", ngon(0.15, 1.0, 0.1, 6), z + 0.7, z + 1.4)
    part(a, "Smoke", "Stove", (0.15, 1.0, z + 1.4))
    for dx, dz, r in ((0.05, 0.2, 0.13), (0.15, 0.48, 0.17), (0.05, 0.8, 0.2)):
        blob(a, "smoke", (0.15 + dx, 1.0, z + 1.4 + dz), r, r, r, n=2)
    part(a, "Body", "Sled", (0, -0.2, z + 0.4))
    blob(a, "grey", (0, -0.15, z + 0.5), 0.6, 0.58, 0.5, n=4)
    part(a, "Head", "Body", (0, -0.45, z + 0.95))
    hz = z + 0.95
    blob(a, "grey", (0, -0.5, hz + 0.25), 0.44, 0.42, 0.38, n=3)
    a.box("white", -0.09, 0.09, -0.9, -0.2, hz + 0.12, hz + 0.66, bevel=0.02)  # белая полоса от носа ко лбу
    for s in S2:  # чёрные полосы через глаза, белые щёки, серые ушки с белой каймой
        a.box("black", s * 0.09, s * 0.25, -0.88, -0.24, hz + 0.16, hz + 0.6, bevel=0.02)
        a.box("white", s * 0.25, s * 0.42, -0.84, -0.3, hz - 0.02, hz + 0.26, bevel=0.02)
        round_eye(a, (s * 0.17, -0.9, hz + 0.36), 0.065)
        disc(a, "grey", s * 0.36, hz + 0.62, 0.1, -0.5, -0.4, n=6, axis="y")
        disc(a, "white", s * 0.36, hz + 0.62, 0.055, -0.52, -0.49, n=6, axis="y", bevel=0)
    disc(a, "black", 0, hz + 0.12, 0.08, -0.94, -0.86, n=8, axis="y")
    cheeks(a, 0.34, -0.85, hz + 0.12, 0.06)
    for s, name in ((1, "ArmL"), (-1, "ArmR")):
        part(a, name, "Body", (s * 0.5, -0.4, z + 0.7))
        bar(a, "grey", (s * 0.5, -0.4, z + 0.7), (s * 0.3, -0.85, z + 0.5), 0.18, 0.16)
        blob(a, "black", (s * 0.28, -0.92, z + 0.5), 0.1, 0.1, 0.09, n=2)
    kchain(a, "rope", [(-0.28, -0.95, z + 0.48), (0, -1.15, z + 0.3), (0.0, -1.35, t + 0.2)], [0.05] * 3)
    face_point(a, (0, -0.9, hz + 0.3))
    closeup(a, (0.2, 0.0, t + 0.4), eye_off=(-1.2, -2.0, 1.2))
    a.pose = {"Head": ((0, 0, 12), (0, 0, 0)), "Smoke": ((0, 15, 0), (0, 0, 0.08)), "ArmL": ((15, 0, 0), (0, 0, 0))}
    return a


RARE = [("FishingWalrus", fishing_walrus, "Морж-рыбак", "Rare"),
        ("EarmuffOwl", earmuff_owl, "Полярная сова в наушниках", "Rare"),
        ("IcicleHedgehog", icicle_hedgehog, "Ёжик-сосулька", "Rare"),
        ("BakerCub", baker_cub, "Медвежонок-пекарь", "Rare"),
        ("PuffinPostman", puffin_postman, "Тупик-почтальон", "Rare"),
        ("SleepyIrbis", sleepy_irbis, "Ирбис-соня", "Rare"),
        ("SnowflakeStar", snowflake_star, "Морская звезда-снежинка", "Rare"),
        ("SkatingSeahorse", skating_seahorse, "Морской конёк на коньках", "Rare"),
        ("SledBadger", sled_badger, "Барсук на санках с печкой", "Rare")]


# ══ EPIC (1024²) ═══════════════════════════════════════════════════════════════════════════════════════════════

def sweater_mammoth():
    """22. Мамонтёнок в свитере: рыжий пух, красный вязаный свитер со снежинками, хобот завитком, бивни-кнопки."""
    a = new("SweaterMammoth", {"fur": ("C9773E", True), "furD": ("A35A2A", True), "sweater": ("D8344A", True),
                               "sweaterD": ("A61E33", False), "flakeW": ("FFFFFF", False)})
    t = epic_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0.2, t + 1.0))
    z = t
    blob(a, "fur", (0, 0.25, z + 1.25), 1.05, 1.2, 0.85, n=5)
    blob(a, "sweater", (0, 0.2, z + 1.25), 1.12, 1.18, 0.9, n=5, z0=z + 0.75, z1=z + 1.85)
    a.frame("sweaterD", S.octagon(-1.12, 1.12, -0.95, 1.4, 0.4), 0.12, z + 0.72, z + 0.86, axis="z")
    for x, y, zz in ((1.13, 0.0, z + 1.35), (1.13, 0.75, z + 1.15), (-1.13, 0.0, z + 1.35), (-1.13, 0.75, z + 1.15)):
        for ang in (0, 60, 120):
            m = Matrix.Translation((x, y, zz)) @ Matrix.Rotation(math.radians(ang), 4, "X")
            a.box("flakeW", -0.035, 0.035, -0.035, 0.035, -0.17, 0.17, bevel=0, matrix=m)
    names = {(1, -1): "LegFL", (-1, -1): "LegFR", (1, 1): "LegBL", (-1, 1): "LegBR"}
    for (s, f), name in names.items():
        x, y = s * 0.55, -0.35 if f < 0 else 0.85
        part(a, name, "Body", (x, y, z + 0.75))
        a.prism("fur", ngon(x, y, 0.36, 8), z, z + 0.78)
        a.frame("sweaterD", ngon(x, y, 0.4, 8), 0.08, z + 0.5, z + 0.64, axis="z")
        if f < 0:
            for dx in (-0.16, 0.0, 0.16):
                a.box("ivory", x + dx - 0.06, x + dx + 0.06, y - 0.4, y - 0.33, z, z + 0.12, bevel=0.01)
    part(a, "Tail", "Body", (0, 1.4, z + 1.4))
    spike(a, "furD", (0, 1.38, z + 1.4), (0, 1.7, z + 1.0), 0.18)
    part(a, "Head", "Body", (0, -0.75, z + 1.75))
    hz = z + 1.75
    blob(a, "fur", (0, -0.95, hz + 0.2), 0.75, 0.66, 0.7, n=5)
    eyes(a, 0.3, -1.5, hz + 0.38, 0.11)
    cheeks(a, 0.48, -1.42, hz + 0.05, 0.1)
    for s in S2:
        spike(a, "ivory", (s * 0.26, -1.42, hz - 0.28), (s * 0.36, -1.78, hz - 0.42), 0.15)
    for k, x in enumerate((-0.16, 0.0, 0.18)):  # хохолок
        spike(a, "furD", (x, -0.95, hz + 0.8), (x * 2.0, -1.05, hz + 1.25), 0.22)
    for s, name in ((1, "EarL"), (-1, "EarR")):
        part(a, name, "Head", (s * 0.68, -0.85, hz + 0.3))
        slab(a, "furD", [(-0.75, hz - 0.2), (-1.0, hz + 0.4), (-0.7, hz + 0.85), (-0.25, hz + 0.62), (-0.2, hz - 0.05)],
             s * 0.62, s * 0.82, matrix=tilt((s * 0.7, -0.8, hz + 0.3), "Z", -s * 18))
    part(a, "Trunk", "Head", (0, -1.42, hz - 0.1))
    kchain(a, "fur", [(0, -1.42, hz - 0.1), (0, -1.72, hz - 0.55), (0, -1.82, hz - 0.92), (0, -2.08, hz - 0.98),
                      (0, -2.1, hz - 0.72)], [0.4, 0.33, 0.27, 0.22, 0.18], up=(0, -1, 0), overlap=0.3)
    face_point(a, (0, -1.5, hz + 0.25))
    closeup(a, (1.0, 0.2, z + 1.4), eye_off=(-0.6, -2.2, 1.0))
    a.pose = {"Head": ((0, 0, 12), (0, 0, 0)), "Trunk": ((-25, 0, 0), (0, 0, 0)), "EarL": ((0, 0, 20), (0, 0, 0)),
              "LegFL": ((-15, 0, 0), (0, 0, 0)), "Tail": ((0, 20, 0), (0, 0, 0))}
    return a


def aurora_reindeer():
    """23. Олень с рогами-сиянием: рога из светящихся звеньев (зелёный и фиолетовый), белое жабо, бубенец; нос чёрный."""
    a = new("AuroraReindeer", {"deer": ("B07A4A", True), "deerL": ("E8C9A0", False), "ruff": ("F4F1E6", False),
                               "collar": ("D8344A", False), "gold": ("F2C230", False), "neonAur": ("3DFFB0", False),
                               "neonAurP": ("B57CFF", False), "hoof": ("2E2A38", False)})
    t = epic_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0.1, t + 1.6))
    z = t
    layered(a, "deer", [(-1.05, z + 1.25), (-1.15, z + 1.82), (-0.75, z + 2.05), (0.85, z + 1.95), (1.2, z + 1.6),
                        (1.05, z + 1.15), (-0.85, z + 1.1)], [(0.46, 1, 1), (0.58, 0.92, 0.9)], (0, z + 1.6))
    for x in (-0.28, 0.0, 0.28):  # жабо
        spike(a, "ruff", (x, -1.08, z + 1.85), (x * 1.2, -1.3, z + 1.3), 0.34)
    names = {(1, -1): "LegFL", (-1, -1): "LegFR", (1, 1): "LegBL", (-1, 1): "LegBR"}
    for (s, f), name in names.items():
        y = -0.72 if f < 0 else 0.78
        part(a, name, "Body", (s * 0.3, y, z + 1.3))
        kchain(a, "deer", [(s * 0.3, y, z + 1.35), (s * 0.3, y - 0.05, z + 0.62), (s * 0.3, y, z + 0.12)],
               [0.28, 0.22, 0.2])
        a.box("hoof", s * 0.3 - 0.13, s * 0.3 + 0.13, y - 0.15, y + 0.11, z, z + 0.14, bevel=0.01)
    part(a, "Tail", "Body", (0, 1.15, z + 1.8))
    spike(a, "ruff", (0, 1.15, z + 1.82), (0, 1.48, z + 2.05), 0.28)
    part(a, "Head", "Body", (0, -1.0, z + 2.0))
    kchain(a, "deer", [(0, -0.95, z + 1.9), (0, -1.28, z + 2.75)], [0.58, 0.44])
    a.frame("collar", S.octagon(-0.34, 0.34, -1.36, -0.72, 0.16), 0.11, z + 2.08, z + 2.24, axis="z")
    blob(a, "gold", (0, -1.44, z + 1.98), 0.15, 0.15, 0.15, n=3)
    hz = z + 2.75
    blob(a, "deer", (0, -1.4, hz + 0.25), 0.38, 0.46, 0.34, n=4)
    taper(a, "deerL", (0, -1.7, hz + 0.2), (0, -2.12, hz + 0.08), 0.4, 0.28, 0.34, 0.24)
    blob(a, "dark", (0, -2.16, hz + 0.12), 0.14, 0.09, 0.11, n=2)
    for s in S2:
        round_eye(a, (s * 0.2, -1.74, hz + 0.38), 0.08)
        spike(a, "deer", (s * 0.32, -1.3, hz + 0.42), (s * 0.8, -1.2, hz + 0.56), 0.24)
    for s, name in ((1, "AntlerL"), (-1, "AntlerR")):
        pts = [V((s * 0.16, -1.3, hz + 0.56)), V((s * 0.5, -1.25, hz + 1.15)), V((s * 0.72, -1.05, hz + 1.72)),
               V((s * 0.88, -0.7, hz + 2.2))]
        part(a, name, "Head", tuple(pts[0]))
        for i, (p0, p1) in enumerate(zip(pts, pts[1:])):
            kchain(a, "neonAur" if i % 2 == 0 else "neonAurP", [tuple(p0), tuple(p1)],
                   [0.16 - i * 0.03, 0.13 - i * 0.03], overlap=0.2)
        for i, (p, d) in enumerate(((pts[1], (0.1, -0.35, 0.45)), (pts[2], (0.3, -0.2, 0.45)),
                                    (pts[2], (-0.15, -0.35, 0.4)), (pts[3], (0.25, 0.1, 0.35)))):
            spike(a, "neonAurP" if i % 2 == 0 else "neonAur", tuple(p), tuple(p + V((s * d[0], d[1], d[2]))), 0.12)
    face_point(a, (0, -1.8, hz + 0.3))
    closeup(a, (0.5, 0.1, z + 1.6), eye_off=(-0.8, -2.2, 1.0))
    a.pose = {"Head": ((10, 0, 14), (0, 0, 0)), "LegFL": ((-25, 0, 0), (0, 0, 0)), "Tail": ((0, 20, 0), (0, 0, 0)),
              "AntlerL": ((0, 6, 0), (0, 0, 0))}
    return a


def rink_manta():
    """24. Скат-каток: ледяной скат парит на ледяном шпиле, на спине каток с крошечными пингвинятами."""
    a = new("RinkManta", {"manta": ("2E5BD8", True), "mantaL": ("BFE2FF", False), "ice": ("A8E8FF", True),
                          "rink": ("E6FBFF", False), "peng": ("23263A", False), "pengO": ("FF9F1C", False)})
    t = epic_stand(a, 1.5)
    part(a, "Spire", "Stand", (0, 0, t))
    a.frustum("ice", (-0.42, 0.42, -0.42, 0.42), (-0.12, 0.12, -0.12, 0.12), t, t + 1.5)
    for ang in (0, 120, 240):
        d = V((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
        spike(a, "ice", tuple(V((0, 0, t)) + d * 0.35), tuple(V((0, 0, t + 0.9)) + d * 0.7), 0.3)
    z = t + 1.55
    part(a, "Body", "Spire", (0, 0, z))
    a.prism("manta", S.octagon(-0.55, 0.55, -1.0, 0.9, 0.35), z, z + 0.35)
    a.frustum("manta", (-0.55, 0.55, -1.0, 0.9), (-0.38, 0.38, -0.8, 0.7), z + 0.35, z + 0.5)
    a.prism("rink", S.octagon(-0.36, 0.36, -0.55, 0.55, 0.18), z + 0.5, z + 0.56)
    a.frame("mantaL", S.octagon(-0.4, 0.4, -0.6, 0.6, 0.2), 0.06, z + 0.5, z + 0.6, axis="z")
    eyes(a, 0.32, -1.0, z + 0.22, 0.1)
    a.box("mouth", -0.2, 0.2, -1.03, -0.99, z + 0.06, z + 0.09, bevel=0)
    for s in S2:  # рожки-плавники у морды
        spike(a, "manta", (s * 0.42, -0.95, z + 0.2), (s * 0.5, -1.35, z + 0.25), 0.2)
    for s, name in ((1, "WingL"), (-1, "WingR")):
        part(a, name, "Body", (s * 0.55, 0.0, z + 0.18))
        slab(a, "manta", [(-0.8, z + 0.3), (-0.3, z + 0.36), (0.6, z + 0.26), (0.5, z + 0.08), (-0.6, z + 0.06)],
             s * 0.55, s * 1.65, matrix=tilt((s * 0.55, 0, z + 0.18), "Y", -s * 8))
        slab(a, "mantaL", [(-0.78, z + 0.06), (0.5, z + 0.06), (0.4, z + 0.02), (-0.6, z + 0.02)], s * 0.6, s * 1.5,
             matrix=tilt((s * 0.55, 0, z + 0.18), "Y", -s * 8))
    part(a, "Tail", "Body", (0, 0.9, z + 0.2))
    taper(a, "manta", (0, 0.9, z + 0.2), (0, 1.75, z + 0.32), 0.16, 0.05, 0.12, 0.05)
    for k, (x, y) in enumerate(((-0.15, -0.2), (0.15, 0.25))):
        part(a, f"Peng{k + 1}", "Body", (x, y, z + 0.56))
        blob(a, "peng", (x, y, z + 0.72), 0.1, 0.09, 0.16, n=3)
        a.box("white", x - 0.06, x + 0.06, y - 0.1, y - 0.07, z + 0.62, z + 0.8, bevel=0)
        spike(a, "pengO", (x, y - 0.08, z + 0.82), (x, y - 0.17, z + 0.8), 0.05)
    face_point(a, (0, -1.0, z + 0.25))
    closeup(a, (0.0, 0.0, z + 0.5), eye_off=(-0.8, -1.8, 1.4))
    a.pose = {"WingL": ((0, -20, 0), (0, 0, 0)), "WingR": ((0, 20, 0), (0, 0, 0)), "Body": ((5, 0, 8), (0, 0, 0.1)),
              "Peng1": ((0, 0, 90), (0, 0, 0))}
    return a


def magic_ermine():
    """25. Горностай-фокусник: в плаще, держит цилиндр, из шляпы вылетают снежинки."""
    a = new("MagicErmine", {"fur": ("F7F6F2", True), "tip": ("1E1E28", False), "cape": ("6B3FB8", True),
                            "capeIn": ("D8344A", False), "hat": ("23232E", True), "band": ("F2C230", False),
                            "flake": ("BFF3FF", False)})
    t = epic_stand(a, 1.4)
    part(a, "Body", "Stand", (0, 0, t + 0.8))
    z = t
    for s in S2:
        a.box("fur", s * 0.12, s * 0.42, -0.42, 0.08, z, z + 0.16)
    kchain(a, "fur", [(0, 0.0, z + 0.15), (0, -0.05, z + 0.9), (0, 0.0, z + 1.55)], [0.62, 0.58, 0.5])
    part(a, "Tail", "Body", (0, 0.3, z + 0.4))
    kchain(a, "fur", [(0, 0.3, z + 0.4), (0.4, 0.75, z + 0.6), (0.6, 0.85, z + 1.05)], [0.22, 0.22, 0.2])
    spike(a, "tip", (0.6, 0.85, z + 1.05), (0.68, 0.88, z + 1.45), 0.26)
    part(a, "Cape", "Body", (0, 0.1, z + 1.45))
    slab(a, "cape", [(0.1, z + 1.5), (0.55, z + 1.2), (0.6, z + 0.3), (0.25, z + 0.2), (-0.05, z + 1.4)], -0.6, 0.6)
    slab(a, "capeIn", [(0.12, z + 1.4), (0.28, z + 0.35), (0.2, z + 0.32), (0.05, z + 1.38)], -0.56, 0.56)
    a.frame("cape", S.octagon(-0.38, 0.38, -0.3, 0.3, 0.1), 0.1, z + 1.42, z + 1.58, axis="z")
    part(a, "Head", "Body", (0, -0.05, z + 1.6))
    hz = z + 1.6
    blob(a, "fur", (0, -0.1, hz + 0.25), 0.36, 0.42, 0.3, n=4)
    taper(a, "fur", (0, -0.4, hz + 0.18), (0, -0.7, hz + 0.12), 0.32, 0.14, 0.24, 0.12)
    blob(a, "dark", (0, -0.73, hz + 0.13), 0.06, 0.05, 0.05, n=2)
    eyes(a, 0.15, -0.46, hz + 0.32, 0.07, look=(0.4, 0.3))
    for s in S2:
        disc(a, "fur", s * 0.24, hz + 0.5, 0.1, -0.15, -0.02, n=8, axis="y")
    part(a, "ArmL", "Body", (0.3, -0.1, z + 1.3))
    bar(a, "fur", (0.3, -0.1, z + 1.3), (0.62, -0.2, z + 1.8), 0.14)
    blob(a, "fur", (0.66, -0.22, z + 1.88), 0.08, 0.08, 0.08, n=2)
    part(a, "ArmR", "Body", (-0.3, -0.1, z + 1.3))
    bar(a, "fur", (-0.3, -0.1, z + 1.3), (-0.62, -0.45, z + 1.15), 0.14)
    part(a, "Hat", "ArmR", (-0.7, -0.55, z + 1.12))
    hc = V((-0.72, -0.6, z + 1.25))  # цилиндр вверх дном: тулья снизу, поля сверху
    a.prism("hat", ngon(hc.x, hc.y, 0.24, 10), hc.z - 0.42, hc.z)
    a.prism("hat", ngon(hc.x, hc.y, 0.36, 10), hc.z, hc.z + 0.05)
    a.frame("band", ngon(hc.x, hc.y, 0.25, 10), 0.03, hc.z - 0.12, hc.z - 0.04, axis="z")
    part(a, "Flakes", "Hat", tuple(hc + V((0, 0, 0.1))))
    for k, (dx, dy, dz, r) in enumerate(((0.0, 0.0, 0.35, 0.12), (-0.25, 0.1, 0.65, 0.1), (0.2, -0.05, 0.85, 0.09),
                                         (-0.05, 0.05, 1.1, 0.08))):
        snowflake(a, "flake", hc + V((dx, dy, dz)), r, 0.035)
    face_point(a, (0, -0.55, hz + 0.25))
    closeup(a, (0.0, 0.3, z + 0.9), eye_off=(-1.0, 2.0, 0.8))
    a.pose = {"ArmL": ((0, -20, 0), (0, 0, 0)), "Hat": ((15, 0, 0), (0, 0, 0)), "Flakes": ((0, 0, 30), (0, 0, 0.1)),
              "Cape": ((-8, 0, 0), (0, 0, 0)), "Tail": ((0, 0, 15), (0, 0, 0))}
    return a


def kite_tern():
    """26. Крачка с воздушным змеем: полярная крачка на сугробе держит в клюве нить змея-снежинки с лентой."""
    a = new("KiteTern", {"tern": ("F4F6FA", True), "cap": ("1E1E28", False), "beakR": ("E8384F", False),
                         "grey": ("B8C2D6", False), "kite": ("2FB3A8", True), "kiteE": ("FFD23F", False),
                         "ribbon": ("FF6FAE", False), "string": ("FFFFFF", False)})
    t = epic_stand(a, 1.4)
    part(a, "Mound", "Stand", (0, 0, t))
    blob(a, "snow", (0, 0.3, t + 0.2), 1.1, 0.95, 0.4, n=3, z0=t)
    z = t + 0.5
    part(a, "Body", "Mound", (0, 0.3, z + 0.3))
    taper(a, "tern", (0, 1.0, z + 0.45), (0, -0.25, z + 0.45), 0.5, 0.55, 0.45, 0.55, up=(0, 0, 1))
    spike(a, "grey", (0, 1.0, z + 0.45), (0, 1.5, z + 0.55), 0.3)  # хвост-вилка
    for s in S2:
        a.box("beakR", s * 0.15 - 0.05, s * 0.15 + 0.05, 0.1, 0.3, z - 0.02, z + 0.25, bevel=0)  # лапки
    for s, name in ((1, "WingL"), (-1, "WingR")):
        part(a, name, "Body", (s * 0.25, 0.3, z + 0.65))
        slab(a, "grey", [(-0.25, z + 0.6), (0.45, z + 0.72), (0.9, z + 0.7), (0.3, z + 0.55)], s * 0.22, s * 1.4,
             matrix=tilt((s * 0.25, 0.3, z + 0.65), "Y", -s * 24))
    part(a, "Head", "Body", (0, -0.3, z + 0.65))
    hz = z + 0.65
    blob(a, "tern", (0, -0.45, hz + 0.18), 0.3, 0.32, 0.28, n=3)
    blob(a, "cap", (0, -0.4, hz + 0.34), 0.3, 0.3, 0.14, n=2, z0=hz + 0.28)
    spike(a, "beakR", (0, -0.72, hz + 0.12), (0, -1.12, hz + 0.08), 0.14)
    for s in S2:
        a.prism("white", ngon(-0.55, hz + 0.24, 0.08, 8), s * 0.26, s * 0.31, axis="x")
        a.prism("dark", ngon(-0.57, hz + 0.25, 0.045, 8), s * 0.3, s * 0.33, axis="x", bevel=0)
    part(a, "Kite", "Head", (0, -1.05, hz + 0.1))
    k0 = V((0, -1.05, hz + 0.1))
    kc = V((0.4, -1.2, hz + 2.2))
    bar(a, "string", tuple(k0), tuple(kc - V((0, 0, 0.35))), 0.025)
    a.prism("kite", [(kc.x, kc.z + 0.55), (kc.x + 0.42, kc.z), (kc.x, kc.z - 0.4), (kc.x - 0.42, kc.z)],
            kc.y - 0.04, kc.y + 0.04, axis="y")
    snowflake(a, "kiteE", V((kc.x, kc.y - 0.06, kc.z + 0.05)), 0.22, 0.04)
    part(a, "Ribbon", "Kite", tuple(kc - V((0, 0, 0.4))))
    stripe_chain(a, ("ribbon", "kiteE"), [tuple(kc - V((0, 0, 0.4))), tuple(kc + V((0.25, 0.05, -0.75))),
                                         tuple(kc + V((0.1, 0.05, -1.05))), tuple(kc + V((0.35, 0.05, -1.35)))],
                 0.1, 0.03)
    face_point(a, (0.35, -0.6, hz + 0.2))
    closeup(a, (0.4, -1.2, hz + 2.2), eye_off=(-1.0, -1.8, 0.4))
    a.pose = {"WingL": ((0, -15, 0), (0, 0, 0)), "WingR": ((0, 20, 0), (0, 0, 0)), "Kite": ((0, 12, 0), (0, 0, 0)),
              "Ribbon": ((0, -20, 0), (0, 0, 0))}
    return a


def ice_beaver():
    """27. Бобёр-ледостроитель: в каске складывает иглу из ледяных кирпичей, хвост-лопатка, кирпич в лапах."""
    a = new("IceBeaver", {"beaver": ("8A5A3C", True), "beaverL": ("C49A70", False), "tooth": ("FFF3C8", False),
                          "hat": ("FFC83D", True), "brick": ("A8E8FF", True), "brickE": ("E6FBFF", False),
                          "tail": ("4A3A30", False)})
    t = epic_stand(a, 1.6)
    part(a, "Igloo", "Stand", (0.55, 0.45, t))
    for row, (r, z0, n) in enumerate(((0.95, t, 9), (0.82, t + 0.32, 7), (0.6, t + 0.64, 5))):
        for k in range(n):
            if row == 2 and k > 2:
                continue  # недостроено
            ang = math.radians(-60 + k * (240 / max(n - 1, 1)) + row * 10)
            cx, cy = 0.55 + r * math.cos(ang), 0.45 + r * math.sin(ang)
            m = Matrix.Translation((cx, cy, z0)) @ Matrix.Rotation(ang, 4, "Z")
            a.box("brick", -0.13, 0.13, -0.17, 0.17, 0.0, 0.3, matrix=m)
            a.box("brickE", 0.12, 0.14, -0.15, 0.15, 0.03, 0.27, bevel=0, matrix=m)
    part(a, "Body", "Stand", (-0.45, -0.1, t + 0.7))
    z = t
    blob(a, "beaver", (-0.45, -0.1, z + 0.75), 0.62, 0.55, 0.72, n=5)
    blob(a, "beaverL", (-0.45, -0.5, z + 0.7), 0.38, 0.2, 0.46, n=3)
    for s in S2:
        a.box("beaver", -0.45 + s * 0.18 - 0.14, -0.45 + s * 0.18 + 0.14, -0.55, -0.15, z, z + 0.14)
    part(a, "Tail", "Body", (-0.45, 0.4, z + 0.25))
    a.prism("tail", S.octagon(-0.75, -0.15, 0.4, 1.35, 0.22), z + 0.02, z + 0.14)
    for k in range(3):  # насечки
        a.box("beaver", -0.7, -0.2, 0.62 + k * 0.22 - 0.02, 0.62 + k * 0.22 + 0.02, z + 0.14, z + 0.16, bevel=0)
    part(a, "Head", "Body", (-0.45, -0.15, z + 1.4))
    hz = z + 1.4
    blob(a, "beaver", (-0.45, -0.2, hz + 0.28), 0.45, 0.42, 0.38, n=4)
    blob(a, "beaverL", (-0.45, -0.58, hz + 0.15), 0.26, 0.14, 0.18, n=2)
    disc(a, "dark", -0.45, hz + 0.26, 0.07, -0.76, -0.7, n=8, axis="y")
    a.box("tooth", -0.53, -0.37, -0.73, -0.69, hz - 0.05, hz + 0.1, bevel=0.005)
    a.box("dark", -0.455, -0.445, -0.74, -0.73, hz - 0.05, hz + 0.1, bevel=0)
    for s in S2:
        round_eye(a, (-0.45 + s * 0.18, -0.56, hz + 0.4), 0.08)
        disc(a, "beaver", -0.45 + s * 0.32, hz + 0.56, 0.1, -0.2, -0.08, n=6, axis="y")
    a.prism("hat", S.octagon(-0.82, -0.08, -0.55, 0.15, 0.16), hz + 0.55, hz + 0.72)
    a.frustum("hat", (-0.82, -0.08, -0.55, 0.15), (-0.62, -0.28, -0.36, -0.04), hz + 0.72, hz + 0.86)
    a.box("hat", -0.88, -0.02, -0.66, 0.2, hz + 0.52, hz + 0.58, bevel=0.01)
    for s, name in ((1, "ArmL"), (-1, "ArmR")):
        part(a, name, "Body", (-0.45 + s * 0.45, -0.3, z + 1.05))
        bar(a, "beaver", (-0.45 + s * 0.45, -0.3, z + 1.05), (-0.45 + s * 0.3, -0.72, z + 0.9), 0.16, 0.15)
    part(a, "Brick", "ArmL", (-0.45, -0.85, z + 0.9))
    a.box("brick", -0.7, -0.2, -0.98, -0.7, z + 0.82, z + 1.08)
    a.box("brickE", -0.7, -0.2, -1.0, -0.97, z + 0.85, z + 1.05, bevel=0)
    face_point(a, (-0.45, -0.7, hz + 0.25))
    closeup(a, (0.55, 0.45, t + 0.5), eye_off=(-0.6, -2.0, 1.2))
    a.pose = {"Head": ((0, 0, -10), (0, 0, 0)), "Brick": ((0, 0, 0), (0, 0, 0.12)), "Tail": ((-10, 0, 0), (0, 0, 0))}
    return a


EPIC = [("SweaterMammoth", sweater_mammoth, "Мамонтёнок в свитере", "Epic"),
        ("AuroraReindeer", aurora_reindeer, "Олень с рогами-сиянием", "Epic"),
        ("RinkManta", rink_manta, "Скат-каток", "Epic"),
        ("MagicErmine", magic_ermine, "Горностай-фокусник", "Epic"),
        ("KiteTern", kite_tern, "Крачка с воздушным змеем", "Epic"),
        ("IceBeaver", ice_beaver, "Бобёр-ледостроитель", "Epic")]


# ══ LEGENDARY (1024²) ══════════════════════════════════════════════════════════════════════════════════════════

def house(a, x, y, z, w, d, h, wall):
    a.box(wall, x - w / 2, x + w / 2, y - d / 2, y + d / 2, z, z + h, bevel=0.01)
    a.extrude("snow", [(z + h, y - d / 2 - 0.06), (z + h, y + d / 2 + 0.06), (z + h + d * 0.55, y)],
              x - w / 2 - 0.06, x + w / 2 + 0.06, axis="x")
    a.box("neonWin", x - w * 0.18, x + w * 0.18, y - d / 2 - 0.02, y - d / 2 + 0.02, z + h * 0.35, z + h * 0.7, bevel=0)


def iceberg_narwhal():
    """28. Нарвал-айсберг: из воды выныривает нарвал, на спине — айсберг с деревушкой и маяком, бивень-кристалл."""
    a = new("IcebergNarwhal", {"water": ("3FA9E0", True), "foam": ("F4FBFF", False), "whale": ("4E6A9E", True),
                               "spot": ("33496E", False), "belly": ("E8EEF6", False), "berg": ("C9F0FF", True),
                               "bergD": ("8FD6F5", True), "wallR": ("E8384F", False), "wallY": ("FFC83D", False),
                               "wallT": ("2FB3A8", False), "neonWin": ("FFE27A", False), "pine": ("2F7A5A", False),
                               "neonHorn": ("BFF3FF", False)})
    t = legendary_stand(a, 1.6)
    part(a, "Water", "Stand", (0, 0, t))
    a.prism("water", ngon(0, 0.2, 1.55, 12), t, t + 0.12)
    a.frame("foam", ngon(0, 0.2, 1.2, 12), 0.18, t + 0.1, t + 0.18, axis="z")
    z = t + 0.1
    part(a, "Body", "Water", (0, 0.2, z + 0.5))
    layered(a, "whale", [(-1.25, z + 0.25), (-1.35, z + 0.75), (-1.05, z + 1.15), (0.2, z + 1.3), (1.1, z + 0.95),
                         (1.4, z + 0.45), (1.0, z + 0.1), (-1.0, z + 0.05)],
            [(0.55, 1, 1), (0.72, 0.9, 0.86)], (0.0, z + 0.65))
    slab(a, "belly", [(-1.3, z + 0.2), (-1.38, z + 0.55), (-0.6, z + 0.25), (-0.6, z + 0.08)], -0.5, 0.5)
    for x, y in ((0.25, 0.4), (-0.3, 0.6), (0.6, 0.85), (-0.55, 0.2)):  # пятна на спине (вразброс)
        a.box("spot", x - 0.09, x + 0.09, y - 0.09, y + 0.09, z + 1.18, z + 1.24, bevel=0)
    for s in S2:
        round_eye(a, (s * 0.4, -1.18, z + 0.72), 0.09)
    a.box("dark", -0.32, 0.32, -1.38, -1.34, z + 0.38, z + 0.42, bevel=0)  # улыбка
    for s in S2:
        a.box("dark", s * 0.32 - 0.04, s * 0.32 + 0.04, -1.37, -1.33, z + 0.42, z + 0.5, bevel=0)
    part(a, "Horn", "Body", (0.1, -1.3, z + 0.82))
    for k in range(4):  # бивень-кристалл витками
        p0 = V((0.1 + 0.08 * k, -1.3 - 0.32 * k, z + 0.82 + 0.12 * k))
        p1 = V((0.1 + 0.08 * (k + 1), -1.3 - 0.32 * (k + 1), z + 0.82 + 0.12 * (k + 1)))
        taper(a, "neonHorn" if k % 2 else "berg", tuple(p0), tuple(p1), 0.18 - k * 0.035, 0.15 - k * 0.035,
              up=(0, 0, 1))
    spike(a, "neonHorn", (0.42, -2.58, z + 1.3), (0.5, -2.9, z + 1.42), 0.08)
    for s, name in ((1, "FinL"), (-1, "FinR")):
        part(a, name, "Body", (s * 0.6, -0.5, z + 0.3))
        kchain(a, "whale", [(s * 0.6, -0.5, z + 0.3), (s * 1.05, -0.3, z + 0.15), (s * 1.25, 0.0, z + 0.12)],
               [0.4, 0.3, 0.14], [0.1, 0.08, 0.07], up=(0, 0, 1))
    part(a, "Tail", "Body", (0, 1.3, z + 0.4))
    kchain(a, "whale", [(0, 1.3, z + 0.4), (0, 1.65, z + 0.75)], [0.4, 0.28], up=(0, 0, 1))
    a.extrude("whale", [(-0.75, 1.95), (-0.1, 1.68), (0, 1.8), (0.1, 1.68), (0.75, 1.95), (0.45, 1.6), (0, 1.55),
                        (-0.45, 1.6)], z + 0.72, z + 0.84, axis="z")
    part(a, "Iceberg", "Body", (0, 0.3, z + 1.25))
    a.frustum("berg", (-0.75, 0.75, -0.4, 1.05), (-0.55, 0.55, -0.15, 0.8), z + 1.2, z + 1.65, bevel=0)
    a.frustum("bergD", (-0.5, 0.5, -0.1, 0.75), (-0.3, 0.15, 0.2, 0.5), z + 1.65, z + 2.4, bevel=0)
    a.frustum("berg", (-0.3, 0.15, 0.2, 0.5), (-0.12, -0.02, 0.32, 0.4), z + 2.4, z + 2.85, bevel=0)
    house(a, -0.35, -0.05, z + 1.65, 0.34, 0.3, 0.28, "wallR")
    house(a, 0.3, 0.05, z + 1.65, 0.3, 0.28, 0.26, "wallY")
    house(a, -0.1, 0.45, z + 2.4, 0.26, 0.24, 0.22, "wallT")
    for x, y, zz in ((-0.6, 0.6, z + 1.65), (0.55, 0.65, z + 1.65)):
        a.frustum("pine", (x - 0.13, x + 0.13, y - 0.13, y + 0.13), (x, x, y, y), zz, zz + 0.4, bevel=0)
    part(a, "Lighthouse", "Iceberg", (0.45, 0.45, z + 1.65))
    a.prism("white", ngon(0.45, 0.45, 0.13, 8), z + 1.65, z + 1.95)
    a.prism("wallR", ngon(0.45, 0.45, 0.12, 8), z + 1.95, z + 2.2)
    a.prism("white", ngon(0.45, 0.45, 0.11, 8), z + 2.2, z + 2.4)
    a.prism("neonWin", ngon(0.45, 0.45, 0.09, 8), z + 2.4, z + 2.55)
    a.frustum("wallR", (0.33, 0.57, 0.33, 0.57), (0.45, 0.45, 0.45, 0.45), z + 2.55, z + 2.72, bevel=0)
    face_point(a, (0, -1.3, z + 0.7))
    closeup(a, (0.0, 0.3, z + 1.9), eye_off=(-1.0, -2.0, 0.8))
    a.pose = {"Body": ((-6, 0, 0), (0, 0, 0.08)), "FinL": ((0, -20, 0), (0, 0, 0)), "Tail": ((15, 0, 0), (0, 0, 0)),
              "Lighthouse": ((0, 0, 45), (0, 0, 0))}
    return a


def yeti_cub():
    """29. Йетёнок-коллекционер: маленький пушистый малыш (не копия босса) — лупа в лапе, крошечная ледяная
    глыба-рюкзачок с самоцветом; лицо сиреневое, круглое, глаза большие, улыбка с одним зубиком; без монокля,
    портупеи и прикуса с бивнями."""
    a = new("YetiCub", {"fur": ("F4F8FF", True), "furS": ("D6E2F5", True), "face": ("B9A8F0", False),
                        "faceD": ("8E7CD8", False), "ice": ("A8E8FF", True), "iceE": ("E6FBFF", False),
                        "gold": ("F2C230", False), "lens": ("BFF3FF", False), "neonGem": ("FF4FA3", False),
                        "strap": ("2FB3A8", False)})
    t = legendary_stand(a, 1.4)
    part(a, "Body", "Stand", (0, 0, t + 0.7))
    z = t
    for s, name in ((1, "LegL"), (-1, "LegR")):
        part(a, name, "Body", (s * 0.3, 0.0, z + 0.45))
        blob(a, "fur", (s * 0.3, -0.05, z + 0.25), 0.28, 0.34, 0.26, n=3)
        disc(a, "face", s * 0.3, z + 0.14, 0.13, -0.4, -0.36, n=8, axis="y", bevel=0)
    blob(a, "fur", (0, 0.0, z + 0.95), 0.66, 0.56, 0.6, n=5)
    blob(a, "furS", (0, -0.42, z + 0.9), 0.4, 0.18, 0.42, n=3)
    for i, (x, zz) in enumerate(((-0.55, z + 1.1), (0.58, z + 1.0), (0.0, z + 0.4))):  # пушистые пряди
        spike(a, "fur", (x, -0.1, zz), (x * 1.35, -0.2, zz - 0.25), 0.26)
    part(a, "Pack", "Body", (0, 0.45, z + 1.0))
    for s in S2:
        bar(a, "strap", (s * 0.38, -0.3, z + 1.42), (s * 0.4, 0.5, z + 1.35), 0.08, 0.04)
    a.extrude("ice", S.octagon(-0.38, 0.38, 0.5, 0.95, 0.1), z + 0.75, z + 1.42, axis="z")
    a.frustum("iceE", (-0.3, 0.3, 0.56, 0.9), (-0.1, 0.1, 0.68, 0.78), z + 1.42, z + 1.62, bevel=0)
    gem(a, "neonGem", (0, 0.72, z + 1.08), 0.22)
    for x in (-0.38, 0.38):
        a.box("gold", x - 0.04, x + 0.04, 0.48, 0.62, z + 0.73, z + 0.85, bevel=0)
    part(a, "Head", "Body", (0, -0.05, z + 1.48))
    hz = z + 1.48
    blob(a, "fur", (0, -0.05, hz + 0.55), 0.78, 0.68, 0.66, n=5)
    for i, x in enumerate((-0.35, -0.12, 0.12, 0.35)):  # хохолок
        spike(a, "fur", (x, -0.1, hz + 1.1), (x * 1.6, 0.0, hz + 1.5 - 0.06 * (i % 2)), 0.3)
    blob(a, "face", (0, -0.52, hz + 0.48), 0.52, 0.22, 0.42, n=4)
    eyes(a, 0.22, -0.76, hz + 0.58, 0.15, look=(0.25, 0.1))
    cheeks(a, 0.38, -0.72, hz + 0.32, 0.08)
    a.box("faceD", -0.1, 0.1, -0.78, -0.74, hz + 0.24, hz + 0.28, bevel=0)  # улыбка
    a.box("white", 0.0, 0.07, -0.78, -0.75, hz + 0.17, hz + 0.24, bevel=0.005)  # один зубик
    disc(a, "faceD", 0, hz + 0.42, 0.06, -0.78, -0.73, n=6, axis="y")
    for s in S2:
        spike(a, "fur", (s * 0.66, -0.2, hz + 0.6), (s * 1.0, -0.15, hz + 0.75), 0.26)
    part(a, "ArmL", "Body", (0.6, -0.1, z + 1.25))
    kchain(a, "fur", [(0.6, -0.1, z + 1.25), (0.82, -0.45, z + 1.4), (0.8, -0.62, z + 1.62)], [0.28, 0.25, 0.22])
    part(a, "Loupe", "ArmL", (0.8, -0.65, z + 1.65))
    bar(a, "gold", (0.8, -0.65, z + 1.55), (0.8, -0.68, z + 1.85), 0.07)
    a.frame("gold", ngon(0.8, z + 2.05, 0.22, 10), 0.06, -0.72, -0.64, axis="y")
    a.prism("lens", ngon(0.8, z + 2.05, 0.17, 10), -0.7, -0.66, axis="y")
    part(a, "ArmR", "Body", (-0.6, -0.1, z + 1.25))
    kchain(a, "fur", [(-0.6, -0.1, z + 1.25), (-0.78, -0.35, z + 0.95)], [0.28, 0.24])
    face_point(a, (0, -0.78, hz + 0.5))
    closeup(a, (0.0, 0.7, z + 1.1), eye_off=(-1.2, 2.0, 0.8))
    a.pose = {"Head": ((0, 0, 12), (0, 0, 0)), "ArmL": ((-15, 0, 0), (0, 0, 0)), "Loupe": ((10, 0, 0), (0, 0, 0)),
              "LegR": ((-12, 0, 0), (0, 0, 0)), "Pack": ((0, 0, 0), (0, 0, 0.03))}
    return a


def aurora_jelly():
    """30. Медуза-сияние: огромный ледяной купол со светящейся сердцевиной, щупальца — ленты северного сияния."""
    a = new("AuroraJelly", {"dome": ("BFE9FF", True), "domeD": ("8FD0F2", True), "neonCore": ("FF7FD6", False),
                            "neonAur": ("3DFFB0", False), "neonAurP": ("B57CFF", False), "frost": ("FFFFFF", False)})
    t = legendary_stand(a, 1.5)
    z = t
    part(a, "Bell", "Stand", (0, 0, z + 2.0))
    bz = z + 2.0
    blob(a, "dome", (0, 0, bz + 0.6), 1.25, 1.2, 0.95, n=6, z0=bz)
    a.frame("domeD", ngon(0, 0, 1.28, 12), 0.2, bz - 0.05, bz + 0.18, axis="z")
    blob(a, "neonCore", (0, 0, bz + 0.55), 0.45, 0.45, 0.4, n=3)
    for k in range(6):  # морозный узор на куполе
        ang = math.radians(k * 60)
        p = V((1.05 * math.cos(ang), 1.0 * math.sin(ang), bz + 0.7))
        spike(a, "frost", tuple(p), tuple(p + V((0.18 * math.cos(ang), 0.18 * math.sin(ang), 0.3))), 0.12)
    eyes(a, 0.32, -1.12, bz + 0.62, 0.14)
    cheeks(a, 0.55, -1.02, bz + 0.38, 0.09)
    a.box("mouth", -0.14, 0.14, -1.14, -1.1, bz + 0.34, bz + 0.38, bevel=0)
    for i in range(4):
        ang = math.radians(45 + i * 90)
        r0 = V((0.7 * math.cos(ang), 0.7 * math.sin(ang), bz))
        part(a, f"Tent{i + 1}", "Bell", tuple(r0))
        pts = [r0]
        for k in range(1, 5):
            pts.append(r0 + V((0.12 * math.sin(k * 1.3 + i), 0.12 * math.cos(k * 1.1 + i), -0.5 * k)))
        pts[-1] = V((pts[-1].x * 1.6, pts[-1].y * 1.6, z + 0.05))
        stripe_chain(a, ("neonAur", "neonAurP"), [tuple(p) for p in pts], 0.18, 0.06)
    for i in range(4):  # короткие ленты между
        ang = math.radians(i * 90)
        r0 = V((0.45 * math.cos(ang), 0.45 * math.sin(ang), bz))
        stripe_chain(a, ("neonAurP", "neonAur"), [tuple(r0), tuple(r0 + V((0.05, 0.05, -0.6))),
                                                 tuple(r0 + V((-0.05, 0.0, -1.1)))], 0.12, 0.05)
    face_point(a, (0, -1.15, bz + 0.55))
    closeup(a, (0.6, -0.6, bz + 0.9), eye_off=(-1.0, -1.8, 0.8))
    a.pose = {"Bell": ((0, 0, 0), (0, 0, 0.15)), "Tent1": ((12, 0, 0), (0, 0, 0)), "Tent3": ((-12, 0, 0), (0, 0, 0))}
    return a


LEGENDARY = [("IcebergNarwhal", iceberg_narwhal, "Нарвал-айсберг", "Legendary"),
             ("YetiCub", yeti_cub, "Йетёнок-коллекционер", "Legendary"),
             ("AuroraJelly", aurora_jelly, "Медуза-сияние", "Legendary")]



def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    repo, shots = os.path.abspath(argv[0]), os.path.abspath(argv[1])
    quick = "quick" in argv[2:]
    only = [x for x in argv[2:] if x != "quick"]
    items = [x for x in COMMON + RARE + EPIC + LEGENDARY if not only or x[0] in only]
    name = "report.json" if not only else "report_" + "+".join(only)[:120] + ".json"
    run(items, repo, shots, os.path.join(repo, "assets", "models", "art", "boss5"),
        os.path.join(repo, "assets", "textures", "art", "boss5"), quick=quick, report_name=name)


if __name__ == "__main__":
    main()
