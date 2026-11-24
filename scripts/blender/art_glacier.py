"""Коллекция босса 5 «Йети-коллекционер» (Ледник) — ледяная коллекция v2, 30 существ по каталогу docs/BOSS5_CATALOG.md
(утверждён владельцем 2026-11-24: странные звери и монстрики без бытовых вещей — смешное в самом теле). Стиль D39 v2 (эталон — фенек №20 босса 4): детали D39, подвижные части с точками
вращения (D18, D54, D55), корень — подставка Stand (в игре скрыта), запекание ×4, карты Common 512², Rare и выше
1024² (D64), FBX из частей и скелет rig.json в осях Roblox, кадры и отчёт — общий цикл creature_kit.run.
У каждого — своя нелепость в теле (пропорции, лишние головы и глаза, гибрид двух животных); семьи силуэтов — как
в каталоге (не больше 3 на семью).
Без людей, текста, логотипов, оружия, бытовых вещей и мемных или чужих персонажей.

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
import anatomy_kit as A  # noqa: E402

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
        wx, wy = max(rx * f - 0.012 * k, 0.02), max(ry * f - 0.012 * k, 0.02)  # ярусы не равны: грани не совпадают
        bevel = S.BEVEL if min(wx, wy, (a1 - a0) / 2) > 0.06 else 0.0  # мелкий ярус — без фаски
        a.prism(key, S.octagon(c[0] - wx, c[0] + wx, c[1] - wy, c[1] + wy, min(wx, wy) * cut),
                c[2] + a0 - (0.008 if k else -0.006), c[2] + a1 + 0.008, matrix=matrix, bevel=bevel)  # низ — над опорой


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
    for k, ang in enumerate((0, 60, 120)):
        d = w / 2 * (1.0 + 0.6 * k)  # толщина по нормали у каждого бруска своя: грани не совпадают
        if axis == "y":
            m = Matrix.Translation(c) @ Matrix.Rotation(math.radians(ang), 4, "Y")
            a.box(key, -w / 2, w / 2, -d, d, -r, r, bevel=0, matrix=m)
        else:
            m = Matrix.Translation(c) @ Matrix.Rotation(math.radians(ang), 4, "Z")
            a.box(key, -r, r, -w / 2, w / 2, -d, d, bevel=0, matrix=m)


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

def penguin_giraffe():
    """1. Пингвин-жираф: шея длиннее тела в жирафьих пятнах, крошечная голова с рожками качается сверху."""
    a = new("PenguinGiraffe", {"navy": ("273A6E", True), "orange": ("FF9F1C", False), "patch": ("F2B33D", False),
                               "horn": ("C9773E", False)})
    t = common_stand(a, 1.2)
    part(a, "Body", "Stand", (0, 0, t + 0.6))
    z = t
    for s in S2:
        a.box("orange", s * 0.28 - 0.2, s * 0.28 + 0.2, -0.5, 0.1, z, z + 0.14)
    blob(a, "navy", (0, 0.05, z + 0.75), 0.68, 0.62, 0.72, n=5)
    slab(a, "white", [(-0.55, z + 0.2), (-0.7, z + 0.75), (-0.58, z + 1.25), (-0.3, z + 1.25), (-0.3, z + 0.2)],
         -0.46, 0.46)
    for s, name in ((1, "FlipperL"), (-1, "FlipperR")):
        part(a, name, "Body", (s * 0.66, 0.0, z + 1.1))
        kchain(a, "navy", [(s * 0.66, 0.0, z + 1.1), (s * 0.95, -0.05, z + 0.6)], [0.32, 0.2], [0.12, 0.1])
    part(a, "Neck", "Body", (0, -0.05, z + 1.35))
    pts = [V((0, -0.05, z + 1.3)), V((0, -0.1, z + 2.0)), V((0, -0.05, z + 2.7)), V((0, 0.05, z + 3.3))]
    kchain(a, "navy", [tuple(p) for p in pts], [0.42, 0.36, 0.32, 0.28])
    for k, (dz, dx) in enumerate(((1.6, 0.1), (2.05, -0.08), (2.5, 0.06), (2.95, -0.05))):  # жирафьи пятна
        a.box("patch", dx - 0.1, dx + 0.1, -0.29 + 0.02 * k, -0.2, z + dz - 0.1, z + dz + 0.08, bevel=0)
    part(a, "Head", "Neck", (0, 0.05, z + 3.3))
    hz = z + 3.3
    blob(a, "navy", (0, 0.0, hz + 0.25), 0.3, 0.32, 0.26, n=3)
    a.box("white", -0.22, 0.22, -0.31, -0.27, hz + 0.12, hz + 0.32, bevel=0)
    eyes(a, 0.12, -0.32, hz + 0.3, 0.07)
    spike(a, "orange", (0, -0.28, hz + 0.18), (0, -0.62, hz + 0.14), 0.16)
    for s in S2:  # рожки жирафа
        bar(a, "horn", (s * 0.12, 0.05, hz + 0.45), (s * 0.16, 0.05, hz + 0.68), 0.07)
        blob(a, "horn", (s * 0.16, 0.05, hz + 0.72), 0.07, 0.07, 0.06, n=2)
    face_point(a, (0, -0.35, hz + 0.25))
    closeup(a, (0.0, -0.4, z + 0.8))
    a.pose = {"Neck": ((-8, 0, 6), (0, 0, 0)), "Head": ((12, 0, -14), (0, 0, 0)), "FlipperL": ((0, 22, 0), (0, 0, 0))}
    return a


def jelly(a, key, c, rx, ry, rz, n=5, z0=None):
    """Желейный ком: как blob, но из невыпуклых ярусов — детали внутри (рыбка) не прячутся при сборке."""
    lo = -rz if z0 is None else max(-rz, z0 - c[2])
    for k in range(n):
        a0 = lo + (rz - lo) * k / n
        a1 = lo + (rz - lo) * (k + 1) / n
        zm = (a0 + a1) / 2
        f = max(math.sqrt(max(1 - (zm / rz) ** 2, 0.0)), 0.42)
        wx, wy = rx * f - 0.012 * k, ry * f - 0.012 * k
        a.extrude(key, S.octagon(c[0] - wx, c[0] + wx, c[1] - wy, c[1] + wy, min(wx, wy) * 0.38),
                  c[2] + a0 + (0.006 if k == 0 else -0.008), c[2] + a1 + 0.008, axis="z")


def snow_slime():
    """2. Снежный слизень: прозрачная желейная капля (в игре — прозрачность части), внутри застряла рыбка;
    спереди три глаза разного размера."""
    a = new("SnowSlime", {"slime": ("8FE0FF", True), "slimeD": ("4FBFEA", False), "fish": ("FF8A1F", True),
                          "fishD": ("D9651A", False)})
    t = common_stand(a, 1.5)
    a.transparent_parts = ("Body", "Top")  # желе полупрозрачное: рыбку видно
    part(a, "Body", "Stand", (0, 0, t + 0.3))
    z = t
    jelly(a, "slimeD", (0, 0.0, z + 0.12), 1.35, 1.25, 0.15, n=2, z0=z)
    jelly(a, "slime", (0, 0.05, z + 0.6), 1.05, 1.0, 0.7, n=3, z0=z + 0.1)  # мало ярусов: желе не мутнеет
    part(a, "Top", "Body", (0, 0.05, z + 1.2))
    jelly(a, "slime", (0.05, 0.1, z + 1.35), 0.45, 0.42, 0.42, n=2)
    K.KEY = "slime"
    K.spike(a, (0.1, 0.1, z + 1.7), (0.25, 0.18, z + 2.05), 0.22)
    part(a, "Fish", "Body", (0.0, -0.3, z + 0.5))  # крупная рыбка внутри желе, у передней стенки — видна насквозь
    taper(a, "fish", (-0.6, -0.3, z + 0.5), (0.35, -0.35, z + 0.55), 0.36, 0.48, 0.38, 0.52, up=(0, 0, 1))
    taper(a, "fish", (0.35, -0.35, z + 0.55), (0.62, -0.35, z + 0.55), 0.48, 0.2, 0.52, 0.2, up=(0, 0, 1))
    spike(a, "fishD", (0.6, -0.35, z + 0.55), (0.88, -0.35, z + 0.82), 0.26)
    spike(a, "fishD", (0.6, -0.35, z + 0.55), (0.88, -0.35, z + 0.28), 0.26)
    a.box("dark", -0.5, -0.4, -0.58, -0.52, z + 0.58, z + 0.68, bevel=0)
    part(a, "Eyes", "Top", (0, -0.7, z + 1.1))  # три глаза прямо на поверхности желе (непрозрачные)
    for x, y, zz, r in ((-0.42, -0.84, z + 0.98, 0.24), (0.12, -0.36, z + 1.5, 0.17), (0.45, -0.84, z + 0.92, 0.28)):
        round_eye(a, (x, y, zz), r, look=(0.0, 0.2))
    a.box("mouth", -0.22, 0.22, -0.98, -0.92, z + 0.6, z + 0.68, bevel=0)
    face_point(a, (0, -1.05, z + 1.1))
    closeup(a, (0.1, -0.4, z + 0.6), eye_off=(-1.2, -2.0, 0.6))
    a.pose = {"Top": ((0, 10, 0), (0, 0, 0.06)), "Eyes": ((0, 0, 10), (0, 0, 0)), "Fish": ((0, 0, 20), (0, 0, 0))}
    return a


def two_head_fox():
    """3. Двухголовый песец: сидит, обвив лапы хвостом; из плеч буквой V растут две шеи — головы спорят, глядя
    в разные стороны (D64 «Анатомия»: грудь, передние лапы, бедро, хвост вокруг лап)."""
    a = new("TwoHeadFox", {"fox": ("F4F8FF", True), "foxT": ("BFD3EA", False), "earIn": ("FFB7C8", False)})
    t = common_stand(a, 1.4)
    part(a, "Body", "Stand", (0, 0.1, t + 0.5))
    z = t
    A.body(a, "fox", (0, 0.28, z), 0.6, 0.62, 1.32, "pear", n=4, t0=0.06, lean=-0.42,
           front=("snow", 0.9, z + 0.4, z + 1.32))  # сидит: круп сзади, грудь вперёд; белая грудка вписана в ярусы
    for s in S2:
        A.body(a, "fox", (s * 0.43, 0.42, z), 0.2, 0.42, 0.62, "egg", n=2, t0=0.12)  # бедро задней лапы
        A.foot(a, "fox", (s * 0.42, 0.1, z), (0, -1, 0), 0.5, 0.26, toes=3, toe_key="foxT", h=0.13, z=z)
        A.limb(a, "fox", [(s * 0.22, -0.3, z + 0.92), (s * 0.24, -0.42, z + 0.45), (s * 0.25, -0.46, z + 0.12)],
               [0.27, 0.22, 0.2], joints=False)  # передняя лапа-колонна под грудью
        A.foot(a, "fox", (s * 0.25, -0.46, z), (0, -1, 0), 0.32, 0.24, toes=3, toe_key="foxT", h=0.12, z=z)
    part(a, "Tail", "Body", (0.45, 0.6, z + 0.25))
    kchain(a, "fox", [(0.4, 0.62, z + 0.25), (0.92, 0.3, z + 0.27), (0.86, -0.4, z + 0.26), (0.36, -0.84, z + 0.21)],
           [0.42, 0.56, 0.5, 0.36], up=(0, 0, 1), cut=A.CUT)  # пушистый хвост брусками обвивает лапы
    spike(a, "foxT", (0.3, -0.84, z + 0.2), (-0.12, -0.92, z + 0.18), 0.3)
    for s, name in ((1, "HeadL"), (-1, "HeadR")):
        base = V((s * 0.16, -0.32, z + 1.12))
        part(a, name, "Body", tuple(base))
        hc = V((s * 0.56, -0.44, z + 1.64))
        A.limb(a, "fox", [tuple(base), tuple((base + hc) / 2 + V((s * 0.04, 0, 0.03))), tuple(hc)], [0.46, 0.4, 0.34],
               joints=False)  # толстая шея из плеча
        with_matrix(a, tilt(hc, "Z", s * 38))  # каждая голова отвернулась в свою сторону
        A.ball(a, "fox", tuple(hc), 0.32, n=2, ry=0.34, rz=0.28)
        A.body(a, "snow", tuple(hc + V((0, -0.12, -0.3))), 0.24, 0.2, 0.2, "ball", n=2)  # белые щёки
        A.snout(a, "fox", tuple(hc + V((0, -0.24, -0.06))), (0, -1, -0.18), 0.42, 0.28, 0.1, 0.22, 0.08,
                mouth_key="mouth", mouth=0.75)
        for e in S2:
            ep = hc + V((e * 0.15, -0.27, 0.08))
            A.eye(a, tuple(ep), 0.075, normal=(e * 0.45, -1, 0.15), look=(s * 0.6, 0.0), sides=6)
            bar(a, "foxT", tuple(ep + V((-e * 0.09, -0.05, 0.11))), tuple(ep + V((e * 0.09, -0.05, 0.07))), 0.05, 0.04,
                bevel=0)  # сердитые брови — спорят
            spike(a, "fox", tuple(hc + V((e * 0.17, 0.02, 0.18))), tuple(hc + V((e * 0.27, 0.06, 0.62))), 0.24)
            spike(a, "earIn", tuple(hc + V((e * 0.17, -0.07, 0.22))), tuple(hc + V((e * 0.25, -0.03, 0.52))), 0.13)
        with_matrix(a, None)
    face_point(a, (0, -0.8, z + 1.8))
    closeup(a, (0.3, -0.5, z + 0.8))
    a.pose = {"HeadL": ((0, 12, 10), (0, 0, 0)), "HeadR": ((0, -8, -14), (0, 0, 0)), "Tail": ((0, 0, -18), (0, 0, 0))}
    return a


def fluff_cyclops():
    """4. Пушистик-циклоп: лиловый шар меха с одним огромным глазом на тонких длинных ножках."""
    a = new("FluffCyclops", {"fluff": ("B98CF2", True), "fluffD": ("8E5FD8", False), "leg": ("2E2A48", False),
                             "iris": ("5BE7FF", False)})
    t = common_stand(a, 1.2)
    part(a, "Body", "Stand", (0, 0, t + 2.2))
    z = t
    c = V((0, 0, z + 2.55))
    blob(a, "fluff", tuple(c), 0.95, 0.9, 0.88, n=5)
    for k in range(10):  # пучки меха
        ang = math.radians(k * 36)
        p = c + V((0.85 * math.cos(ang), 0.8 * math.sin(ang), 0.35 * math.sin(k)))
        spike(a, "fluffD" if k % 2 else "fluff", tuple(p), tuple(p + V((0.35 * math.cos(ang), 0.32 * math.sin(ang), -0.1))),
              0.3)
    part(a, "Eye", "Body", (0, -0.8, c.z + 0.1))
    disc(a, "white", 0, c.z + 0.1, 0.55, -0.98, -0.78, n=10, axis="y")
    disc(a, "iris", 0, c.z + 0.05, 0.3, -1.02, -0.96, n=10, axis="y", bevel=0)
    disc(a, "dark", 0, c.z + 0.05, 0.16, -1.05, -1.0, n=8, axis="y", bevel=0)
    a.box("glint", -0.12, -0.03, -1.07, -1.04, c.z + 0.15, c.z + 0.24, bevel=0)
    a.box("fluffD", -0.6, 0.6, -1.06, -0.9, c.z + 0.6, c.z + 0.72, bevel=0.02)  # бровь-козырёк
    a.box("mouth", -0.18, 0.18, -0.9, -0.84, c.z - 0.55, c.z - 0.48, bevel=0)
    for s, name in ((1, "LegL"), (-1, "LegR")):
        part(a, name, "Body", (s * 0.35, 0.0, c.z - 0.7))
        kchain(a, "leg", [(s * 0.35, 0.0, c.z - 0.7), (s * 0.48, -0.15, z + 0.95), (s * 0.4, -0.05, z + 0.12)],
               [0.14, 0.11, 0.1])
        a.box("leg", s * 0.4 - 0.18, s * 0.4 + 0.18, -0.4, 0.1, z, z + 0.14, bevel=0.02)
    face_point(a, (0, -1.0, c.z))
    closeup(a, (0.5, -0.5, c.z + 0.3), eye_off=(-1.2, -2.0, 0.6))
    a.pose = {"Body": ((0, 8, 0), (0, 0, -0.1)), "Eye": ((0, 0, 12), (0, 0, 0)), "LegL": ((-14, 0, 0), (0, 0, 0))}
    return a


def mustache_walrus():
    """5. Морж-усач: усы до земли, заплетены в две косы с голубыми бантами, сам — довольный и важный."""
    a = new("MustacheWalrus", {"walrus": ("C98A63", True), "muzzle": ("E8CDB0", False), "stache": ("F2EEE6", True),
                               "bow": ("4FA8E0", False)})
    t = common_stand(a, 1.5)
    part(a, "Body", "Stand", (0, 0.2, t + 0.6))
    z = t
    blob(a, "walrus", (0, 0.25, z + 0.8), 1.0, 0.9, 0.82, n=5)
    for s, name in ((1, "FlipperL"), (-1, "FlipperR")):
        part(a, name, "Body", (s * 0.85, -0.2, z + 0.7))
        kchain(a, "walrus", [(s * 0.85, -0.2, z + 0.7), (s * 1.15, -0.5, z + 0.12)], [0.34, 0.28], [0.16, 0.12])
    part(a, "Head", "Body", (0, -0.35, z + 1.45))
    hz = z + 1.45
    blob(a, "walrus", (0, -0.4, hz + 0.25), 0.62, 0.55, 0.5, n=4)
    eyes(a, 0.24, -0.88, hz + 0.45, 0.07, lid=0.5, lid_key="walrus")
    disc(a, "dark", 0, hz + 0.28, 0.08, -1.06, -0.98, n=6, axis="y")
    for s in S2:
        blob(a, "muzzle", (s * 0.2, -0.92, hz + 0.08 + (0.018 if s < 0 else 0)), 0.24, 0.18, 0.2, n=3)  # не вровень
        spike(a, "ivory", (s * 0.16, -0.98, hz - 0.08), (s * 0.2, -1.05, hz - 0.62), 0.12)
    for s, name in ((1, "BraidL"), (-1, "BraidR")):  # усы-косы до земли
        base = V((s * 0.32, -1.02, hz + 0.12))
        part(a, name, "Head", tuple(base))
        pts = [base, base + V((s * 0.35, -0.12, -0.25)), base + V((s * 0.45, -0.2, -0.75)),
               base + V((s * 0.4, -0.25, -1.2)), V((s * 0.62, -1.35, z + 0.05))]
        kchain(a, "stache", [tuple(p) for p in pts], [0.24, 0.2, 0.18, 0.16, 0.14], overlap=0.3)
        for p in pts[1:-1]:  # переплетения косы
            a.box("stache", p.x - 0.12, p.x + 0.12, p.y - 0.11, p.y + 0.11, p.z - 0.05, p.z + 0.05, bevel=0)
        q = pts[3]
        a.box("bow", q.x - 0.16, q.x + 0.16, q.y - 0.12, q.y + 0.12, q.z - 0.08, q.z + 0.08, bevel=0.01)
    face_point(a, (0, -1.0, hz + 0.25))
    closeup(a, (0.4, -0.3, z + 0.9))
    a.pose = {"Head": ((0, 0, 10), (0, 0, 0)), "BraidL": ((0, 12, 0), (0, 0, 0)), "BraidR": ((0, -6, 0), (0, 0, 0))}
    return a


def seal_caterpillar():
    """6. Тюлень-гусеница: длинный пятнистый тюлень из трёх сегментов на шести ластах, выгнулся аркой."""
    a = new("SealCaterpillar", {"seal": ("A9B8CC", True), "sealD": ("6F7F99", False), "sealL": ("DCE4EE", False)})
    t = common_stand(a, 1.6)
    segs = [("Rear", "Stand", V((0, 1.05, t + 0.4))), ("Mid", "Rear", V((0, 0.2, t + 0.85))),
            ("Front", "Mid", V((0, -0.65, t + 0.5)))]
    for name, parent, c in segs:
        part(a, name, parent, tuple(c))
        blob(a, "seal", tuple(c), 0.55, 0.52, 0.42, n=3)
        for s in S2:  # пара ласт у каждого сегмента
            spike(a, "sealD", (s * 0.45, c.y, c.z - 0.2), (s * 0.82, c.y - 0.1, t + 0.02), 0.28)
        a.box("sealD", c.x + 0.1, c.x + 0.26, c.y + 0.1, c.y + 0.26, c.z + 0.36, c.z + 0.42, bevel=0)  # пятно
    spike(a, "sealD", (0, 1.5, t + 0.35), (0, 1.85, t + 0.2), 0.3)
    part(a, "Head", "Front", (0, -1.0, t + 0.75))
    hz = t + 0.75
    blob(a, "seal", (0, -1.15, hz + 0.3), 0.45, 0.42, 0.4, n=4)
    blob(a, "sealL", (0, -1.5, hz + 0.2), 0.26, 0.18, 0.16, n=2)
    disc(a, "dark", 0, hz + 0.28, 0.07, -1.7, -1.63, n=6, axis="y")
    eyes(a, 0.2, -1.5, hz + 0.45, 0.1)
    for s in S2:
        for dz in (0.16, 0.24):
            bar(a, "dark", (s * 0.12, -1.66, hz + dz), (s * 0.4, -1.6, hz + dz + 0.04), 0.025)
    face_point(a, (0, -1.6, hz + 0.3))
    closeup(a, (0.0, 0.2, t + 0.9), eye_off=(-1.2, -2.0, 1.0))
    a.pose = {"Mid": ((0, 0, 12), (0, 0, 0.08)), "Front": ((-10, 0, -10), (0, 0, 0)), "Head": ((0, 0, 15), (0, 0, 0))}
    return a


def hedge_owl():
    """7. Сова-ёж: круглая коричневая сова, вместо перьев на спине и макушке — ледяные иглы."""
    a = new("HedgeOwl", {"owl": ("A8774E", True), "owlL": ("F1DCC0", False), "yellow": ("FFD23F", False),
                         "beak": ("3A3A4A", False), "iceS": ("8FE8FF", False), "iceL": ("DFFBFF", False)})
    t = common_stand(a, 1.3)
    part(a, "Body", "Stand", (0, 0, t + 0.8))
    z = t
    blob(a, "owl", (0, 0.05, z + 1.0), 0.88, 0.8, 0.95, n=5)
    blob(a, "owlL", (0, -0.5, z + 0.85), 0.55, 0.3, 0.6, n=3)
    for s in S2:
        for dx in (-0.12, 0.0, 0.12):
            spike(a, "yellow", (s * 0.3 + dx, -0.5, z + 0.08), (s * 0.3 + dx, -0.72, z), 0.1)
    part(a, "Quills", "Body", (0, 0.4, z + 1.4))
    n = 0
    for el in (15, 40, 65, 88):
        for az in range(-170, 171, 34 if el < 80 else 85):
            ti, p = math.radians(az), math.radians(el)
            d = V((math.sin(ti) * math.cos(p), math.cos(ti) * math.cos(p) + 0.2, math.sin(p))).normalized()
            if d.y < -0.2:
                continue
            base = V((0, 0.05, z + 1.0)) + V((d.x * 0.78, d.y * 0.72, d.z * 0.85))
            spike(a, "iceS" if n % 2 else "iceL", tuple(base), tuple(base + d * 0.55), 0.24)
            n += 1
    for s, name in ((1, "WingL"), (-1, "WingR")):
        part(a, name, "Body", (s * 0.82, 0.0, z + 1.2))
        slab(a, "owl", [(-0.35, z + 0.45), (-0.45, z + 1.2), (0.0, z + 1.45), (0.5, z + 1.1), (0.55, z + 0.4)],
             s * 0.78, s * 0.98)
    part(a, "Face", "Body", (0, -0.7, z + 1.35))
    for s in S2:
        round_eye(a, (s * 0.3, -0.86, z + 1.42), 0.2, pupil=0.55)
        a.frame("yellow", ngon(s * 0.3, z + 1.42, 0.24, 8), 0.06, -0.92, -0.86, axis="y")
    spike(a, "beak", (0, -0.9, z + 1.22), (0, -1.02, z + 1.02), 0.15)
    face_point(a, (0, -0.95, z + 1.35))
    closeup(a, (0.3, 0.3, z + 1.7), eye_off=(-1.0, -2.2, 1.0))
    a.pose = {"Face": ((0, 0, 14), (0, 0, 0)), "WingL": ((0, -18, 0), (0, 0, 0)), "Quills": ((-6, 0, 0), (0, 0, 0.04))}
    return a


def ice_crab():
    """8. Краб-льдина: панцирь — глыба льда, одна клешня гигантская (больше тела), другая крошечная."""
    a = new("IceCrab", {"ice": ("A8E8FF", True), "iceE": ("E6FBFF", False), "crab": ("FF6B4A", True),
                        "crabD": ("D9472E", False)})
    t = common_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0.2, t + 0.5))
    z = t + 0.3
    a.prism("ice", S.octagon(-0.7, 0.7, -0.35, 0.85, 0.2), z + 0.1, z + 0.85)  # панцирь-глыба
    a.frustum("iceE", (-0.55, 0.55, -0.2, 0.7), (-0.25, 0.1, 0.1, 0.4), z + 0.85, z + 1.15, bevel=0)
    a.box("crab", -0.62, 0.62, -0.42, 0.78, z, z + 0.14)  # брюшко
    for s in S2:
        for y in (-0.15, 0.25, 0.65):
            kchain(a, "crabD", [(s * 0.62, y, z + 0.1), (s * 1.0, y + 0.05, z + 0.3), (s * 1.15, y + 0.08, t)],
                   [0.12, 0.1, 0.07], up=(0, 0, 1))
    for s, name in ((1, "EyeL"), (-1, "EyeR")):
        part(a, name, "Body", (s * 0.22, -0.38, z + 0.4))
        bar(a, "crabD", (s * 0.22, -0.38, z + 0.4), (s * 0.28, -0.45, z + 0.95), 0.07)
        round_eye(a, (s * 0.28, -0.55, z + 1.02), 0.12, look=(-s * 0.4, 0))
    part(a, "ClawBig", "Body", (-0.65, -0.3, z + 0.35))
    kchain(a, "crab", [(-0.65, -0.3, z + 0.35), (-1.05, -0.75, z + 0.55)], [0.3, 0.32], up=(0, 0, 1))
    blob(a, "crab", (-1.12, -1.15, z + 0.95), 0.62, 0.62, 0.62, n=4)  # огромная клешня — больше тела
    spike(a, "crabD", (-1.12, -1.68, z + 1.2), (-1.0, -2.0, z + 1.55), 0.42)
    spike(a, "crabD", (-1.12, -1.68, z + 0.7), (-1.08, -2.02, z + 0.5), 0.4)
    part(a, "ClawSmall", "Body", (0.65, -0.3, z + 0.35))
    kchain(a, "crab", [(0.65, -0.3, z + 0.35), (0.82, -0.6, z + 0.45)], [0.12, 0.1], up=(0, 0, 1))
    blob(a, "crab", (0.86, -0.7, z + 0.48), 0.08, 0.1, 0.08, n=2)
    face_point(a, (0, -0.6, z + 1.0))
    closeup(a, (0.0, 0.3, z + 0.6), eye_off=(-1.0, -2.0, 1.2))
    a.pose = {"ClawBig": ((0, 0, -12), (0, 0, 0.1)), "EyeL": ((0, -14, 0), (0, 0, 0)), "ClawSmall": ((0, 0, 20), (0, 0, 0))}
    return a


def ski_ear_hare():
    """9. Заяц-лыжник: уши такие длинные, что легли на снег и стали лыжами — заяц катится, пригнувшись."""
    a = new("SkiEarHare", {"fur": ("F4F8FF", True), "furS": ("DDE6F2", False), "earIn": ("FFB7C8", False),
                           "skiTip": ("9FDDF7", True)})
    t = common_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0.2, t + 0.7))
    z = t + 0.18
    layered(a, "fur", [(-0.5, z + 0.3), (-0.6, z + 0.8), (-0.3, z + 1.2), (0.45, z + 1.05), (0.7, z + 0.5),
                       (0.5, z + 0.15), (-0.3, z + 0.15)], [(0.42, 1, 1), (0.56, 0.9, 0.9)], (0.1, z + 0.65))
    blob(a, "fur", (0, 0.78, z + 0.55), 0.2, 0.18, 0.18, n=2)
    for s in S2:
        a.box("fur", s * 0.12, s * 0.4, -0.55, 0.45, z + 0.04, z + 0.22)  # лапы на ушах
    part(a, "Head", "Body", (0, -0.4, z + 1.05))
    hz = z + 1.0
    blob(a, "fur", (0, -0.62, hz + 0.25), 0.42, 0.38, 0.36, n=4)
    eyes(a, 0.17, -0.98, hz + 0.32, 0.09, look=(0, 0.3))
    disc(a, "pink", 0, hz + 0.18, 0.05, -1.04, -0.98, n=6, axis="y")
    a.box("white", -0.06, 0.06, -1.02, -0.98, hz + 0.02, hz + 0.1, bevel=0.005)
    for s, name in ((1, "EarL"), (-1, "EarR")):  # уши — лыжи: с затылка вниз и далеко вперёд по снегу
        base = V((s * 0.18, -0.4, hz + 0.45))
        part(a, name, "Head", tuple(base))
        x = s * 0.28
        kchain(a, "fur", [tuple(base), (x, 0.0, hz + 0.2), (x, 0.4, z - 0.02)], [0.22, 0.22, 0.24], [0.08, 0.08, 0.08],
               up=(0, 0, 1))
        a.box("fur", x - 0.16, x + 0.16, -1.45, 0.45, z - 0.16, z - 0.04)
        a.box("earIn", x - 0.1, x + 0.1, -1.4, 0.4, z - 0.04, z - 0.015, bevel=0)
        # кончик уха — светло-голубой, загнут вверх ступенями, как нос лыжи
        a.box("skiTip", x - 0.16, x + 0.16, -1.7, -1.44, z - 0.16, z - 0.02)
        a.box("skiTip", x - 0.15, x + 0.15, -1.86, -1.66, z - 0.08, z + 0.14)
        a.box("skiTip", x - 0.14, x + 0.14, -1.98, -1.82, z + 0.08, z + 0.36)
    face_point(a, (0, -1.0, hz + 0.25))
    closeup(a, (0.2, -0.4, z), eye_off=(-1.2, -2.0, 1.2))
    a.pose = {"Body": ((8, 0, 0), (0, 0, 0)), "Head": ((-10, 0, 8), (0, 0, 0)), "EarL": ((0, 0, 4), (0, 0, 0))}
    return a


def snow_worm():
    """10. Снежный червь: лиловый червь вылез из снежка аркой, широкая улыбка с зубами-сосульками."""
    a = new("SnowWorm", {"worm": ("C78BE8", True), "wormL": ("F0D2FF", False), "iceS": ("CFF6FF", False)})
    t = common_stand(a, 1.5)
    part(a, "Ball", "Stand", (0.7, 0.55, t))
    blob(a, "snow", (0.7, 0.55, t + 0.55), 0.62, 0.6, 0.56, n=4)
    for x, y, r in ((0.3, 0.95, 0.2), (1.15, 0.3, 0.18)):
        blob(a, "snowS", (x, y, t + 0.85), r, r, r, n=2)
    part(a, "Mid", "Ball", (0.45, 0.2, t + 1.0))
    pts = [V((0.55, 0.3, t + 0.9)), V((0.2, -0.05, t + 1.5)), V((-0.35, -0.3, t + 1.75)), V((-0.7, -0.45, t + 1.4))]
    keys = ("worm", "wormL")
    for i, (p0, p1) in enumerate(zip(pts, pts[1:])):
        kchain(a, keys[i % 2], [tuple(p0), tuple(p1)], [0.5 - 0.03 * i, 0.47 - 0.03 * i], overlap=0.2)
    part(a, "Head", "Mid", (-0.7, -0.45, t + 1.4))
    hz = t + 1.15
    blob(a, "worm", (-0.75, -0.55, hz), 0.48, 0.45, 0.44, n=4)
    for s in S2:
        round_eye(a, (-0.75 + s * 0.2, -0.98, hz + 0.18), 0.1)
    a.box("mouth", -1.1, -0.4, -1.0, -0.94, hz - 0.22, hz - 0.08, bevel=0.01)  # широкая улыбка
    for k in range(5):  # зубы-сосульки
        x = -1.02 + k * 0.135
        spike(a, "iceS", (x, -1.01, hz - 0.08), (x, -1.03, hz - 0.2), 0.07)
    for s in S2:
        spike(a, "wormL", (-0.75 + s * 0.12, -0.5, hz + 0.4), (-0.75 + s * 0.3, -0.5, hz + 0.72), 0.08)
    face_point(a, (-0.75, -1.0, hz + 0.05))
    closeup(a, (0.0, -0.2, t + 1.4), eye_off=(-1.0, -2.0, 0.8))
    a.pose = {"Mid": ((0, 10, 0), (0, 0, 0)), "Head": ((0, -14, 12), (0, 0, 0))}
    return a


def walking_fish():
    """11. Рыба на лапках: удивлённая треска стоит на коротких зелёных лягушачьих лапах, рот буквой «О»."""
    a = new("WalkingFish", {"fish": ("8FA89A", True), "fishL": ("E8EEE0", False), "frog": ("6CC24A", False),
                            "fin": ("6E8A7C", False)})
    t = common_stand(a, 1.5)
    for s, name in ((1, "LegL"), (-1, "LegR")):
        part(a, name, "Stand", (s * 0.3, 0.1, t + 0.85))
        kchain(a, "frog", [(s * 0.3, 0.1, t + 0.85), (s * 0.45, -0.2, t + 0.45), (s * 0.38, 0.05, t + 0.1)],
               [0.22, 0.2, 0.18])
        for dx in (-0.14, 0.0, 0.14):
            spike(a, "frog", (s * 0.38 + dx, -0.05, t + 0.05), (s * 0.38 + dx * 1.8, -0.42, t + 0.03), 0.12)
    part(a, "Body", "Stand", (0, 0.1, t + 1.3))
    z = t + 1.3
    layered(a, "fish", [(-1.25, z + 0.05), (-1.1, z + 0.45), (-0.3, z + 0.65), (0.8, z + 0.45), (1.2, z + 0.1),
                        (0.8, z - 0.3), (-0.3, z - 0.45), (-1.1, z - 0.3)], [(0.38, 1, 1), (0.5, 0.88, 0.85)],
            (0.0, z + 0.05))
    slab(a, "fishL", [(-1.15, z - 0.2), (-0.3, z - 0.42), (0.7, z - 0.28), (0.7, z - 0.18), (-1.0, z - 0.1)],
         -0.4, 0.4)
    for s in S2:
        round_eye(a, (s * 0.38, -0.85, z + 0.25), 0.16, pupil=0.4)  # выпученные глаза по бокам
    disc(a, "mouth", 0, z - 0.05, 0.14, -1.3, -1.2, n=8, axis="y")  # рот «О»
    a.frame("fishL", ngon(0, z - 0.05, 0.2, 8), 0.06, -1.28, -1.18, axis="y")
    part(a, "Tail", "Body", (0, 1.15, z + 0.05))
    a.extrude("fin", [(z + 0.6, 1.1), (z + 0.05, 1.5), (z - 0.5, 1.1), (z - 0.1, 1.85), (z + 0.2, 1.85)], -0.05, 0.05,
              axis="x")
    part(a, "Fin", "Body", (0, -0.2, z + 0.6))
    a.extrude("fin", [(z + 0.6, -0.4), (z + 1.0, -0.1), (z + 0.95, 0.4), (z + 0.55, 0.5)], -0.04, 0.04, axis="x")
    face_point(a, (0, -1.25, z + 0.1))
    closeup(a, (0.0, -0.4, z + 0.3), eye_off=(-1.2, -2.0, 0.6))
    a.pose = {"LegL": ((-20, 0, 0), (0, 0, 0)), "Tail": ((0, 0, 20), (0, 0, 0)), "Fin": ((0, 10, 0), (0, 0, 0))}
    return a


def antler_fawn():
    """12. Оленёнок-рога: пятнистый малыш, рога втрое больше тела — еле держит голову, коленки дрожат."""
    a = new("AntlerFawn", {"fawn": ("D99A5B", True), "spot": ("FFF3DC", False), "antler": ("F3E3C2", True),
                           "hoof": ("3A2A24", False)})
    t = common_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0.3, t + 0.9))
    z = t
    layered(a, "fawn", [(-0.65, z + 0.8), (-0.7, z + 1.15), (0.6, z + 1.15), (0.75, z + 0.85), (0.5, z + 0.62),
                        (-0.5, z + 0.62)], [(0.32, 1, 1), (0.42, 0.9, 0.9)], (0.0, z + 0.9))
    for x, y in ((0.2, 0.1), (-0.15, 0.4), (0.1, 0.55), (-0.2, -0.2)):  # пятнышки
        a.box("spot", x - 0.06, x + 0.06, y - 0.06, y + 0.06, z + 1.15, z + 1.19, bevel=0)
    for (s, f), name in (((1, -1), "LegFL"), ((-1, -1), "LegFR"), ((1, 1), "LegBL"), ((-1, 1), "LegBR")):
        y = -0.45 if f < 0 else 0.5
        part(a, name, "Body", (s * 0.18, y, z + 0.7))
        kchain(a, "fawn", [(s * 0.18, y, z + 0.7), (s * (0.22 + 0.06 * (f < 0)), y, z + 0.35), (s * 0.2, y, z + 0.08)],
               [0.13, 0.11, 0.1])  # ножки чуть врозь — дрожат
        a.box("hoof", s * 0.2 - 0.07, s * 0.2 + 0.07, y - 0.08, y + 0.06, z, z + 0.08, bevel=0)
    part(a, "Head", "Body", (0, -0.6, z + 1.05))
    hz = z + 0.85
    kchain(a, "fawn", [(0, -0.6, z + 1.05), (0, -0.85, hz + 0.1)], [0.26, 0.22])
    blob(a, "fawn", (0, -1.0, hz), 0.24, 0.3, 0.22, n=3)  # голова опущена под тяжестью
    blob(a, "dark", (0, -1.28, hz - 0.06), 0.06, 0.05, 0.05, n=2)
    for s in S2:
        round_eye(a, (s * 0.12, -1.18, hz + 0.08), 0.06, look=(0, 0.5))
        spike(a, "fawn", (s * 0.18, -0.95, hz + 0.12), (s * 0.45, -0.9, hz + 0.18), 0.12)
    part(a, "Antlers", "Head", (0, -0.95, hz + 0.18))
    for s in S2:  # огромные рога — ветвятся широко и высоко
        p = [V((s * 0.08, -0.95, hz + 0.18)), V((s * 0.4, -0.9, hz + 0.8)), V((s * 0.75, -0.7, hz + 1.4)),
             V((s * 1.15, -0.4, hz + 1.9)), V((s * 1.35, -0.1, hz + 2.4))]
        kchain(a, "antler", [tuple(q) for q in p], [0.14, 0.13, 0.12, 0.1, 0.08], overlap=0.2)
        for q, d in ((p[1], (0.35, -0.2, 0.4)), (p[2], (-0.3, -0.25, 0.55)), (p[3], (0.4, 0.1, 0.35)),
                     (p[3], (-0.2, -0.3, 0.5)), (p[2], (0.45, 0.2, 0.2))):
            spike(a, "antler", tuple(q), tuple(q + V((s * d[0], d[1], d[2]))), 0.09)
    face_point(a, (0, -1.25, hz + 0.05))
    closeup(a, (0.0, 0.2, z + 1.1), eye_off=(-1.0, -2.0, 0.8))
    a.pose = {"Head": ((10, 0, 8), (0, 0, 0)), "Antlers": ((0, 8, 0), (0, 0, 0)), "LegFL": ((-8, 0, 0), (0, 0, 0))}
    return a


COMMON = [("PenguinGiraffe", penguin_giraffe, "Пингвин-жираф", "Common"),
          ("SnowSlime", snow_slime, "Снежный слизень", "Common"),
          ("TwoHeadFox", two_head_fox, "Двухголовый песец", "Common"),
          ("FluffCyclops", fluff_cyclops, "Пушистик-циклоп", "Common"),
          ("MustacheWalrus", mustache_walrus, "Морж-усач", "Common"),
          ("SealCaterpillar", seal_caterpillar, "Тюлень-гусеница", "Common"),
          ("HedgeOwl", hedge_owl, "Сова-ёж", "Common"),
          ("IceCrab", ice_crab, "Краб-льдина", "Common"),
          ("SkiEarHare", ski_ear_hare, "Заяц-лыжник", "Common"),
          ("SnowWorm", snow_worm, "Снежный червь", "Common"),
          ("WalkingFish", walking_fish, "Рыба на лапках", "Common"),
          ("AntlerFawn", antler_fawn, "Оленёнок-рога", "Common")]


# ══ RARE (1024²) ═══════════════════════════════════════════════════════════════════════════════════════════════

def spring_mammoth():
    """13. Мамонтёнок-пружина: хобот длиной в три тела скручен пружиной перед ним, кончик задорно вверх."""
    a = new("SpringMammoth", {"fur": ("C9773E", True), "furD": ("A35A2A", True)})
    t = rare_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0.45, t + 0.9))
    z = t
    blob(a, "fur", (0, 0.5, z + 0.95), 0.75, 0.85, 0.62, n=4)
    for (s, f), name in (((1, -1), "LegFL"), ((-1, -1), "LegFR"), ((1, 1), "LegBL"), ((-1, 1), "LegBR")):
        x, y = s * 0.42, (0.05 if f < 0 else 0.95)
        part(a, name, "Body", (x, y, z + 0.5))
        a.prism("fur", ngon(x, y, 0.26, 8), z, z + 0.55)
        for dx in (-0.1, 0.1):
            a.box("ivory", x + dx - 0.05, x + dx + 0.05, y - 0.28, y - 0.22, z + 0.012, z + 0.1, bevel=0)
    part(a, "Head", "Body", (0, -0.25, z + 1.2))
    hz = z + 1.2
    blob(a, "fur", (0, -0.3, hz + 0.15), 0.55, 0.5, 0.5, n=4)
    for k, x in enumerate((-0.12, 0.0, 0.14)):
        spike(a, "furD", (x, -0.3, hz + 0.6), (x * 2, -0.35, hz + 0.95), 0.18)
    eyes(a, 0.22, -0.72, hz + 0.3, 0.09)
    for s in S2:
        spike(a, "ivory", (s * 0.2, -0.7, hz - 0.15), (s * 0.28, -0.98, hz - 0.25), 0.11)
        slab(a, "furD", [(-0.5, hz - 0.15), (-0.7, hz + 0.3), (-0.45, hz + 0.6), (-0.1, hz + 0.45), (-0.05, hz - 0.05)],
             s * 0.48, s * 0.62)
    part(a, "Trunk", "Head", (0, -0.8, hz - 0.05))
    pts = [V((0, -0.8, hz - 0.05)), V((0, -0.98, hz - 0.35))]
    c = V((0, -1.2, z + 0.65))  # пружина: витки вокруг горизонтальной оси y
    for k in range(11):
        ang = math.radians(90 + k * 70)
        pts.append(c + V((0.32 * math.cos(ang), -0.055 * k, 0.32 * math.sin(ang))))
    pts.append(pts[-1] + V((0, -0.15, 0.4)))
    ws = [0.3 - 0.012 * i for i in range(len(pts))]
    kchain(a, "fur", [tuple(p) for p in pts], ws, up=(0, 0, 1), overlap=0.25)
    face_point(a, (0, -0.75, hz + 0.25))
    closeup(a, (0.0, -1.4, z + 0.7), eye_off=(-1.4, -1.6, 0.6))
    a.pose = {"Trunk": ((-10, 0, 8), (0, 0, 0)), "Head": ((0, 0, 10), (0, 0, 0)), "LegFL": ((-12, 0, 0), (0, 0, 0))}
    return a


def accordion_bear():
    """14. Медведь-гармошка: длинное белое тело собрано голубыми складками, перед и зад — на своих лапах."""
    a = new("AccordionBear", {"fur": ("F4F8FF", True), "fold": ("8FC8F0", True), "nose": ("2E2A38", False)})
    t = rare_stand(a, 1.6)
    part(a, "Rear", "Stand", (0, 0.9, t + 0.7))
    z = t
    blob(a, "fur", (0, 1.0, z + 0.75), 0.6, 0.45, 0.55, n=4)
    blob(a, "fur", (0, 1.42, z + 0.95), 0.14, 0.12, 0.12, n=2)
    for s in S2:
        a.prism("fur", ngon(s * 0.35, 1.0, 0.2, 8), z, z + 0.4)
    part(a, "Folds", "Rear", (0, 0.5, z + 0.75))
    for k in range(5):  # меха-гармошка: чередование широких светлых и узких голубых складок
        y = 0.55 - k * 0.22
        r = 0.56 if k % 2 == 0 else 0.36
        a.prism("fur" if k % 2 == 0 else "fold", S.octagon(-r, r, z + 0.75 - r, z + 0.75 + r, r * 0.35),
                y - 0.12, y + 0.1, axis="y")
    part(a, "Front", "Folds", (0, -0.55, z + 0.75))
    blob(a, "fur", (0, -0.6, z + 0.75), 0.58, 0.42, 0.55, n=4)
    for s in S2:
        a.prism("fur", ngon(s * 0.35, -0.6, 0.2, 8), z, z + 0.4)
    part(a, "Head", "Front", (0, -0.9, z + 1.0))
    hz = z + 1.0
    blob(a, "fur", (0, -1.05, hz + 0.15), 0.42, 0.36, 0.38, n=4)
    blob(a, "fur", (0, -1.38, hz + 0.05), 0.2, 0.16, 0.16, n=2)
    disc(a, "nose", 0, hz + 0.1, 0.07, -1.56, -1.5, n=6, axis="y")
    eyes(a, 0.15, -1.38, hz + 0.28, 0.07)
    for s in S2:
        disc(a, "fur", s * 0.3, hz + 0.48, 0.1, -1.12, -1.0, n=6, axis="y")
    face_point(a, (0, -1.45, hz + 0.15))
    closeup(a, (0.0, 0.0, z + 0.8), eye_off=(-1.4, -1.6, 0.6))
    a.pose = {"Folds": ((0, 0, 10), (0, 0.1, 0)), "Front": ((0, 0, -12), (0, 0, 0)), "Head": ((-10, 0, 8), (0, 0, 0))}
    return a


def ice_spider():
    """15. Ледяной паук: тело-снежок с шестью глазками на восьми длинных ногах-сосульках."""
    a = new("IceSpider", {"iceS": ("8FE8FF", False), "iceL": ("DFFBFF", True), "eyeB": ("2E2A48", False)})
    t = rare_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0.2, t + 1.4))
    z = t
    blob(a, "snow", (0, 0.35, z + 1.45), 0.62, 0.68, 0.55, n=4)
    part(a, "Head", "Body", (0, -0.3, z + 1.4))
    blob(a, "snow", (0, -0.45, z + 1.35), 0.38, 0.32, 0.32, n=3)
    for x, zz, r in ((-0.15, 0.08, 0.09), (0.15, 0.08, 0.09), (-0.28, -0.06, 0.06), (0.28, -0.06, 0.06),
                     (-0.08, -0.16, 0.05), (0.08, -0.16, 0.05)):
        round_eye(a, (x, -0.76, z + 1.4 + zz), r, look=(0, 0.2))
    for s, name in ((1, "LegsL"), (-1, "LegsR")):
        part(a, name, "Body", (s * 0.45, 0.3, z + 1.4))
        for k, y in enumerate((-0.25, 0.1, 0.45, 0.8)):
            knee = V((s * 1.05, y - 0.1 * (1.5 - k), z + 1.95))
            foot = V((s * 1.5, y - 0.25 * (1.5 - k), z + 0.04))
            kchain(a, "iceL", [(s * 0.45, y, z + 1.4), tuple(knee)], [0.12, 0.1], up=(0, 0, 1))
            spike(a, "iceS", tuple(knee), tuple(foot), 0.12)
    face_point(a, (0, -0.8, z + 1.38))
    closeup(a, (0.0, 0.4, z + 1.8), eye_off=(-1.0, -2.0, 0.6))
    a.pose = {"LegsL": ((0, -8, 0), (0, 0, 0)), "Head": ((0, 0, 12), (0, 0, 0)), "Body": ((0, 0, 0), (0, 0, 0.08))}
    return a


def legged_narwhal():
    """16. Нарвал на ножках: пятнистый нарвал вылез на сушу и ходит на четырёх коротких розовых ножках."""
    a = new("LeggedNarwhal", {"whale": ("6F86B8", True), "spot": ("4A5F8C", False), "belly": ("E8EEF6", False),
                              "leg": ("FF9FB2", False), "neonHorn": ("BFF3FF", False)})
    t = rare_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0.2, t + 0.9))
    z = t + 0.4
    layered(a, "whale", [(-1.15, z + 0.35), (-1.1, z + 0.85), (-0.5, z + 1.15), (0.6, z + 1.05), (1.15, z + 0.6),
                         (0.9, z + 0.2), (-0.8, z + 0.15)], [(0.5, 1, 1), (0.64, 0.9, 0.86)], (0.0, z + 0.6))
    slab(a, "belly", [(-1.1, z + 0.3), (-1.16, z + 0.6), (0.6, z + 0.3), (0.5, z + 0.15), (-0.8, z + 0.18)],
         -0.46, 0.46)
    for x, y in ((0.2, 0.2), (-0.25, 0.5), (0.3, 0.75), (-0.2, -0.3)):
        a.box("spot", x - 0.08, x + 0.08, y - 0.08, y + 0.08, z + 1.1, z + 1.16, bevel=0)
    for s in S2:
        round_eye(a, (s * 0.32, -1.08, z + 0.72), 0.09)
    a.box("dark", -0.25, 0.25, -1.17, -1.13, z + 0.42, z + 0.46, bevel=0)
    for (s, f), name in (((1, -1), "LegFL"), ((-1, -1), "LegFR"), ((1, 1), "LegBL"), ((-1, 1), "LegBR")):
        x, y = s * 0.32, (-0.55 if f < 0 else 0.55)
        part(a, name, "Body", (x, y, z + 0.2))
        a.prism("leg", ngon(x, y, 0.13, 8), t, z + 0.22)
        a.box("leg", x - 0.15, x + 0.15, y - 0.22, y + 0.1, t + 0.012, t + 0.1)
    part(a, "Horn", "Body", (0.1, -1.05, z + 0.8))
    for k in range(3):
        p0 = V((0.1 + 0.05 * k, -1.05 - 0.28 * k, z + 0.8 + 0.12 * k))
        p1 = V((0.1 + 0.05 * (k + 1), -1.05 - 0.28 * (k + 1), z + 0.8 + 0.12 * (k + 1)))
        taper(a, "neonHorn" if k % 2 == 0 else "belly", tuple(p0), tuple(p1), 0.16 - k * 0.035,
              0.13 - k * 0.035, up=(0, 0, 1))
    part(a, "Tail", "Body", (0, 1.1, z + 0.5))
    a.extrude("whale", [(-0.6, 1.5), (-0.1, 1.15), (0, 1.25), (0.1, 1.15), (0.6, 1.5), (0.35, 1.1), (-0.35, 1.1)],
              z + 0.6, z + 0.72, axis="z")
    face_point(a, (0, -1.15, z + 0.7))
    closeup(a, (0.0, 0.2, z + 1.0), eye_off=(-1.2, -2.0, 0.8))
    a.pose = {"LegFL": ((-20, 0, 0), (0, 0, 0)), "LegBR": ((15, 0, 0), (0, 0, 0)), "Tail": ((0, 12, 0), (0, 0, 0))}
    return a


def penguin_stack():
    """17. Пингвинья пирамида: шесть пушистых пингвинят пирамидой 3-2-1, верхний машет крылышками."""
    a = new("PenguinStack", {"chick": ("8C97B5", True), "chickL": ("DCE4EE", False), "orange": ("FF9F1C", False)})
    t = rare_stand(a, 1.6)
    r = 0.42

    def chick(c, k, wave=False):
        blob(a, "chick", tuple(c), r, r * 0.92, r * 0.95, n=2)
        a.box("chickL", c.x - r * 0.5, c.x + r * 0.5, c.y - r * 0.86, c.y - r * 0.5, c.z - r * 0.7, c.z + r * 0.2,
              bevel=0.02)  # светлое брюшко
        for s in S2:  # простые глазки (6 пингвинят — экономим треугольники)
            ex, ez = c.x + s * r * 0.32, c.z + r * 0.35
            disc(a, "white", ex, ez, r * 0.17, c.y - r * 0.9, c.y - r * 0.8, n=6, axis="y", bevel=0)
            disc(a, "dark", ex, ez + (0.02 if not wave else -0.02), r * 0.09, c.y - r * 0.93, c.y - r * 0.89, n=6,
                 axis="y", bevel=0)
            a.box("orange", c.x + s * r * 0.4 - 0.12, c.x + s * r * 0.4 + 0.12, c.y - r * 0.6, c.y - r * 0.1,
                  c.z - r * 0.95 + 0.012, c.z - r * 0.95 + 0.08, bevel=0)
            tip = (c.x + s * (r * 1.5 if wave else r * 1.15), c.y - 0.05, c.z + (0.4 if wave else -0.25))
            bar(a, "chick", (c.x + s * r * 0.95, c.y, c.z + 0.1), tip, 0.16, 0.06, bevel=0)
        spike(a, "orange", (c.x, c.y - r * 0.82, c.z + r * 0.12), (c.x, c.y - r * 1.2, c.z + r * 0.06), r * 0.3)

    rows = (("Bottom", "Stand", (-0.86, 0.0, 0.86)), ("Middle", "Bottom", (-0.43, 0.43)), ("Top", "Middle", (0.0,)))
    z = t + r * 0.95
    for k, (name, parent, xs) in enumerate(rows):
        part(a, name, parent, (0, 0, z - r * 0.9))
        for i, x in enumerate(xs):
            chick(V((x, 0.02 * i, z)), k, wave=(k == 2))
        z += r * 1.75  # следующий ряд стоит на головах нижнего
    face_point(a, (0, -0.4, z - r * 1.75))
    closeup(a, (0.0, -0.4, t + 0.6))
    a.pose = {"Middle": ((0, 6, 0), (0, 0, 0)), "Top": ((0, -10, 8), (0, 0, 0))}
    return a


def swivel_owl():
    """18. Филин-вертушка: тело смотрит вперёд (грудка, лапы, крылья по бокам), а голова повёрнута ровно назад —
    спереди видна только спина головы с хохолками; лицо смотрит назад."""
    a = new("SwivelOwl", {"owl": ("C9CDD8", True), "owlD": ("8C93A6", False), "owlF": ("F7F7FA", False),
                          "chest": ("EEF0F6", True), "orange": ("FF9F1C", False), "beak": ("3A3A4A", False),
                          "branch": ("8F5A31", True)})
    t = rare_stand(a, 1.3)
    part(a, "Branch", "Stand", (0, 0, t))
    a.prism("branch", ngon(0, 0, 0.5, 8), t, t + 0.25)
    z = t + 0.25
    part(a, "Body", "Branch", (0, 0.0, z + 0.6))
    blob(a, "owl", (0, 0.05, z + 0.85), 0.75, 0.68, 0.85, n=5)
    blob(a, "chest", (0, -0.45, z + 0.8), 0.48, 0.28, 0.6, n=3)  # светлая грудка — к нам
    for i, (x, zz) in enumerate(((-0.2, z + 1.05), (0.15, z + 0.85), (-0.05, z + 0.6), (0.25, z + 1.15))):
        a.box("owlD", x - 0.07, x + 0.07, -0.76, -0.72, zz - 0.03, zz + 0.03, bevel=0)  # пестрины на грудке
    for s in S2:  # лапы — вперёд
        for dx in (-0.12, 0.0, 0.12):
            spike(a, "orange", (s * 0.28 + dx, -0.45, z + 0.08), (s * 0.28 + dx, -0.7, z + 0.012), 0.11)
    for s, name in ((1, "WingL"), (-1, "WingR")):
        part(a, name, "Body", (s * 0.66, 0.0, z + 1.25))
        slab(a, "owlD", [(-0.3, z + 0.4), (-0.45, z + 1.2), (0.0, z + 1.42), (0.45, z + 1.05), (0.4, z + 0.3)],
             s * 0.66, s * 0.82)
    spike(a, "owlD", (0, 0.6, z + 0.4), (0, 0.95, z + 0.1), 0.4)  # хвост — сзади
    for k in range(4):  # шея закручена: косые полосы по кругу
        a.box("orange" if k % 2 else "owlD", -0.5, 0.5, -0.05, 0.05, z + 1.45, z + 1.53, bevel=0,
              matrix=tilt((0, 0.05, z + 1.49), "Z", k * 45) @ tilt((0, 0.05, z + 1.49), "Y", 12))
    part(a, "Head", "Body", (0, 0.0, z + 1.55))
    hz = z + 1.55
    blob(a, "owl", (0, 0.0, hz + 0.35), 0.6, 0.55, 0.45, n=4)
    # спереди — затылок: тёмная «шапочка» перьев и несколько перышек вразброс (без пар — не складываются в лицо)
    blob(a, "owlD", (0, -0.25, hz + 0.6), 0.42, 0.34, 0.16, n=2)
    for x, zz in ((-0.28, hz + 0.18), (0.12, hz + 0.3), (0.3, hz + 0.08)):
        a.box("owlD", x - 0.06, x + 0.06, -0.58, -0.54, zz - 0.04, zz + 0.04, bevel=0)
    for s in S2:  # хохолки — над затылком к нам
        spike(a, "owl", (s * 0.35, -0.05, hz + 0.72), (s * 0.5, -0.12, hz + 1.0), 0.2)
    blob(a, "owlF", (0, 0.36, hz + 0.32), 0.48, 0.22, 0.34, n=3)  # лицо — назад
    for s in S2:
        disc(a, "white", s * 0.22, hz + 0.38, 0.16, 0.55, 0.6, n=8, axis="y")
        disc(a, "dark", s * 0.22, hz + 0.4, 0.08, 0.6, 0.63, n=8, axis="y", bevel=0)
    spike(a, "beak", (0, 0.58, hz + 0.22), (0, 0.7, hz + 0.05), 0.12)
    face_point(a, (0, -0.6, hz + 0.35))
    closeup(a, (0.0, -0.6, hz + 0.3), eye_off=(-1.0, -2.0, 0.6))
    a.pose = {"Head": ((0, 0, 25), (0, 0, 0)), "WingL": ((0, -15, 0), (0, 0, 0)), "Body": ((0, 6, 0), (0, 0, 0))}
    return a


def walking_jelly():
    """19. Медуза-ходок: полупрозрачный купол с фестонами шагает на шести щупальцах-ногах с волной; под куполом —
    короткие ротовые щупальца, внутри светится ядро (D64 «Анатомия»)."""
    a = new("WalkingJelly", {"dome": ("FF9FD6", True), "domeD": ("E86FB8", False), "leg": ("FFC8E8", False),
                             "neonCore": ("FF4FA3", False)})
    t = rare_stand(a, 1.6)
    z = t
    bz = z + 1.6
    part(a, "Bell", "Stand", (0, 0, bz + 0.2))
    A.body(a, "dome", (0, 0, bz), 0.98, 0.98, 1.1, "dome", n=6, sides=10, floor=0.12)  # купол-полусфера
    a.frame("domeD", ngon(0, 0, 0.99, 10), 0.14, bz - 0.06, bz + 0.1, axis="z")
    for k in range(10):  # фестоны по краю
        ang = math.radians(18 + 36 * k)
        d = V((math.cos(ang), math.sin(ang), 0))
        spike(a, "domeD", tuple(d * 0.9 + V((0, 0, bz + 0.02))), tuple(d * 1.02 + V((0, 0, bz - 0.2))), 0.26)
    for k in range(4):  # ротовые щупальца — короткие, с волной
        ang = math.radians(45 + 90 * k)
        d = V((math.cos(ang), math.sin(ang), 0))
        side = V((-d.y, d.x, 0))
        kchain(a, "leg", [tuple(d * 0.12 + V((0, 0, bz + 0.05))), tuple(d * 0.2 + side * 0.08 + V((0, 0, bz - 0.3))),
                          tuple(d * 0.16 - side * 0.08 + V((0, 0, bz - 0.6)))], [0.16, 0.12, 0.06], up=(0, 0, 1))
    part(a, "Face", "Bell", (0, -0.4, bz + 0.45))  # лицо и ядро — непрозрачные, видны сквозь купол
    A.ball(a, "neonCore", (0, 0.32, bz + 0.52), 0.24, n=3, rz=0.22)  # ядро в глубине купола, над глазами
    for s in S2:
        A.eye(a, (s * 0.28, -0.79, bz + 0.45), 0.13, normal=(s * 0.33, -1, 0.42), look=(0, 0.2))
        disc(a, "pink", s * 0.5, bz + 0.2, 0.07, -0.86, -0.8, n=8, axis="y", bevel=0)
    a.box("mouth", -0.1, 0.1, -0.9, -0.84, bz + 0.26, bz + 0.31, bevel=0)
    for i, name in enumerate(("LegsA", "LegsB", "LegsC")):
        part(a, name, "Bell", (0, 0, bz))
        for s in S2:
            ang = math.radians(30 + 60 * i) * s
            d = V((math.sin(ang), -math.cos(ang), 0))
            side = V((-d.y, d.x, 0)) * s
            pts = [d * 0.6 + V((0, 0, bz + 0.05)), d * 1.0 + side * 0.12 + V((0, 0, bz - 0.35)),
                   d * 1.22 - side * 0.14 + V((0, 0, z + 0.95)), d * 1.36 + side * 0.1 + V((0, 0, z + 0.42)),
                   d * 1.5 + V((0, 0, z + 0.08)), d * 1.72 + V((0, 0, z + 0.06))]
            kchain(a, "leg", [tuple(p) for p in pts], [0.24, 0.2, 0.17, 0.14, 0.12, 0.08], up=(0, 0, 1))
    a.transparent_parts = ("Bell",)
    face_point(a, (0, -0.9, bz + 0.45))
    closeup(a, (0.4, -0.4, bz + 0.7), eye_off=(-1.0, -1.8, 0.8))
    a.pose = {"Bell": ((0, 6, 0), (0, 0, 0.1)), "LegsA": ((0, 0, 8), (0, 0, 0)), "LegsC": ((0, 0, -8), (0, 0, 0))}
    return a


def elephant_seal():
    """20. Морской слон-надувала: сидит, раздувая нос-пузырь больше собственной головы."""
    a = new("ElephantSeal", {"seal": ("9C8574", True), "sealD": ("6E5A4C", False), "bubble": ("FF8FB0", True)})
    t = rare_stand(a, 1.5)
    part(a, "Body", "Stand", (0, 0.3, t + 0.6))
    z = t
    layered(a, "seal", [(-0.6, z), (-0.8, z + 0.6), (-0.65, z + 1.3), (-0.3, z + 1.65), (0.4, z + 1.55),
                        (0.6, z + 0.9), (1.2, z + 0.3), (1.5, z), ], [(0.6, 1, 1), (0.8, 0.9, 0.9)], (0.2, z + 0.7))
    for s in S2:
        spike(a, "sealD", (s * 0.35, 1.3, z + 0.12), (s * 0.75, 1.65, z + 0.05), 0.3)
    for s, name in ((1, "FlipperL"), (-1, "FlipperR")):
        part(a, name, "Body", (s * 0.7, -0.3, z + 0.8))
        kchain(a, "seal", [(s * 0.7, -0.3, z + 0.8), (s * 0.95, -0.6, z + 0.25)], [0.3, 0.22], [0.13, 0.1])
    part(a, "Head", "Body", (0, -0.25, z + 1.6))
    hz = z + 1.6
    blob(a, "seal", (0, -0.3, hz + 0.3), 0.5, 0.48, 0.42, n=4)
    eyes(a, 0.22, -0.72, hz + 0.45, 0.08, lid=0.4, lid_key="sealD")
    part(a, "Nose", "Head", (0, -0.75, hz + 0.2))
    blob(a, "seal", (0, -0.8, hz + 0.2), 0.2, 0.18, 0.17, n=2)
    blob(a, "bubble", (0, -1.35, hz + 0.1), 0.62, 0.55, 0.6, n=5)  # нос-пузырь больше головы
    a.box("white", -0.35, -0.15, -1.85, -1.8, hz + 0.32, hz + 0.48, bevel=0)  # блик на пузыре
    face_point(a, (0, -0.9, hz + 0.35))
    closeup(a, (0.0, -1.3, hz + 0.1), eye_off=(-1.2, -1.8, 0.6))
    a.pose = {"Nose": ((0, 0, 0), (0, -0.05, 0.05)), "Head": ((-8, 0, 0), (0, 0, 0)), "FlipperL": ((0, 18, 0), (0, 0, 0))}
    return a


def tooth_beaver():
    """21. Бобр-зубастик: передние зубы в половину тела, плоский хвост, гордая улыбка."""
    a = new("ToothBeaver", {"beaver": ("8A5A3C", True), "beaverL": ("C49A70", False), "tooth": ("FFF3C8", True),
                            "tail": ("4A3A30", False)})
    t = rare_stand(a, 1.4)
    part(a, "Body", "Stand", (0, 0.1, t + 0.7))
    z = t
    blob(a, "beaver", (0, 0.1, z + 0.75), 0.65, 0.58, 0.75, n=5)
    blob(a, "beaverL", (0, -0.35, z + 0.65), 0.4, 0.22, 0.48, n=3)
    for s in S2:
        a.box("beaver", s * 0.2 - 0.15, s * 0.2 + 0.15, -0.45, 0.0, z, z + 0.14)
    part(a, "Tail", "Body", (0, 0.6, z + 0.2))
    a.prism("tail", S.octagon(-0.32, 0.32, 0.6, 1.55, 0.2), z + 0.02, z + 0.15)
    for s, name in ((1, "ArmL"), (-1, "ArmR")):
        part(a, name, "Body", (s * 0.5, -0.25, z + 1.0))
        bar(a, "beaver", (s * 0.5, -0.25, z + 1.0), (s * 0.35, -0.6, z + 0.8), 0.16, 0.15)
    part(a, "Head", "Body", (0, -0.1, z + 1.45))
    hz = z + 1.45
    blob(a, "beaver", (0, -0.15, hz + 0.3), 0.48, 0.45, 0.4, n=4)
    blob(a, "beaverL", (0, -0.55, hz + 0.15), 0.28, 0.16, 0.18, n=2)
    disc(a, "dark", 0, hz + 0.25, 0.07, -0.74, -0.68, n=6, axis="y")
    for s in S2:
        round_eye(a, (s * 0.2, -0.52, hz + 0.45), 0.08)
        disc(a, "beaver", s * 0.35, hz + 0.62, 0.1, -0.2, -0.08, n=6, axis="y")
    for s in S2:  # два огромных зуба — до середины живота
        a.box("tooth", s * 0.12 - 0.11, s * 0.12 + 0.11, -0.78, -0.66, hz - 0.75, hz + 0.08, bevel=0.02)
    a.box("dark", -0.012, 0.012, -0.785, -0.77, hz - 0.75, hz + 0.08, bevel=0)
    face_point(a, (0, -0.7, hz + 0.1))
    closeup(a, (0.0, -0.7, hz - 0.3), eye_off=(-1.0, -1.8, 0.6))
    a.pose = {"Head": ((-12, 0, 0), (0, 0, 0)), "Tail": ((-15, 0, 0), (0, 0, 0)), "ArmL": ((-20, 0, 0), (0, 0, 0))}
    return a


RARE = [("SpringMammoth", spring_mammoth, "Мамонтёнок-пружина", "Rare"),
        ("AccordionBear", accordion_bear, "Медведь-гармошка", "Rare"),
        ("IceSpider", ice_spider, "Ледяной паук", "Rare"),
        ("LeggedNarwhal", legged_narwhal, "Нарвал на ножках", "Rare"),
        ("PenguinStack", penguin_stack, "Пингвинья пирамида", "Rare"),
        ("SwivelOwl", swivel_owl, "Филин-вертушка", "Rare"),
        ("WalkingJelly", walking_jelly, "Медуза-ходок", "Rare"),
        ("ElephantSeal", elephant_seal, "Морской слон-надувала", "Rare"),
        ("ToothBeaver", tooth_beaver, "Бобр-зубастик", "Rare")]


# ══ EPIC (1024²) ═══════════════════════════════════════════════════════════════════════════════════════════════

def winged_walrus():
    """22. Морж с крылышками: огромный морж оторвался от льдины на крошечных белых крыльях, пыхтит."""
    a = new("WingedWalrus", {"walrus": ("B87A55", True), "muzzle": ("E3C2A2", False), "wing": ("FFFFFF", True),
                             "floe": ("DDF2FF", True)})
    t = epic_stand(a, 1.6)
    part(a, "Floe", "Stand", (0, 0, t))
    a.prism("floe", ngon(0, 0.1, 1.2, 10), t, t + 0.14)
    a.prism("floe", ngon(0, 0.1, 0.16, 6), t + 0.14, t + 0.7)  # стойка-сосулька: он «парит»
    z = t + 0.7
    part(a, "Body", "Floe", (0, 0.1, z + 0.7))
    blob(a, "walrus", (0, 0.15, z + 0.95), 1.05, 0.95, 0.92, n=5)
    for s in S2:  # ласты болтаются
        kchain(a, "walrus", [(s * 0.75, -0.2, z + 0.4), (s * 1.0, -0.4, z + 0.0)], [0.3, 0.22], [0.14, 0.1])
        spike(a, "walrus", (s * 0.35, 0.95, z + 0.4), (s * 0.6, 1.3, z + 0.1), 0.3)
    for s, name in ((1, "WingL"), (-1, "WingR")):
        part(a, name, "Body", (s * 0.75, 0.35, z + 1.55))
        for k in range(3):  # крошечные крылышки трёх перьев
            p0 = V((s * 0.75, 0.35, z + 1.55))
            p1 = p0 + V((s * (0.62 - 0.1 * k), 0.15 + 0.1 * k, 0.6 - 0.18 * k))
            kchain(a, "wing", [tuple(p0), tuple(p1)], [0.28, 0.12], [0.06, 0.05])
    part(a, "Head", "Body", (0, -0.45, z + 1.55))
    hz = z + 1.55
    blob(a, "walrus", (0, -0.55, hz + 0.2), 0.62, 0.55, 0.5, n=4)
    for s in S2:
        blob(a, "muzzle", (s * 0.22, -1.05, hz - 0.04 + (0.018 if s < 0 else 0)), 0.25, 0.18, 0.22, n=3)
        spike(a, "ivory", (s * 0.18, -1.12, hz - 0.18), (s * 0.22, -1.2, hz - 0.8), 0.13)
        round_eye(a, (s * 0.26, -1.0, hz + 0.38), 0.08, look=(0, 0.8))  # смотрит вверх — «лечу!»
    disc(a, "dark", 0, hz + 0.18, 0.09, -1.2, -1.12, n=6, axis="y")
    a.box("mouth", -0.1, 0.1, -1.22, -1.18, hz - 0.12, hz - 0.04, bevel=0)  # пыхтит
    face_point(a, (0, -1.1, hz + 0.2))
    closeup(a, (0.6, 0.3, z + 1.5), eye_off=(-1.0, -2.0, 0.8))
    a.pose = {"WingL": ((0, -30, 0), (0, 0, 0)), "WingR": ((0, 30, 0), (0, 0, 0)), "Body": ((0, 4, 0), (0, 0, 0.15))}
    return a


def owl_totem():
    """23. Сова-тотем: три совы срослись в столбик — синяя сонная, фиолетовая удивлённая, бирюзовая сердитая."""
    a = new("OwlTotem", {"owlB": ("4F7BD8", True), "owlP": ("9C6BE8", True), "owlT": ("2FC4B0", True),
                         "owlF": ("F7F7FA", False), "beak": ("FFB01C", False), "yellow": ("FFD23F", False)})
    t = epic_stand(a, 1.4)
    z = t
    looks = (("owlB", "sleep"), ("owlP", "wow"), ("owlT", "angry"))
    for k, (name, parent) in enumerate((("OwlLow", "Stand"), ("OwlMid", "OwlLow"), ("OwlTop", "OwlMid"))):
        key_, mood = looks[k]
        r = 0.7 - 0.06 * k
        part(a, name, parent, (0, 0, z + 0.05))
        c = V((0, 0.015 * k, z + r))  # каждая сова чуть сдвинута: грани соседних не совпадают
        blob(a, key_, tuple(c), r, r * 0.9, r, n=4)
        blob(a, "owlF", (0, -r * 0.55, c.z + 0.05), r * 0.62, r * 0.3, r * 0.55, n=3)
        for s in S2:
            if mood == "sleep":
                closed_eye(a, (s * r * 0.34, -r * 0.85, c.z + 0.12), 0.2, happy=False)
            else:
                round_eye(a, (s * r * 0.34, -r * 0.85, c.z + 0.12), 0.15 if mood == "wow" else 0.12, pupil=0.5)
                a.frame("yellow", ngon(s * r * 0.34, c.z + 0.12, 0.18, 8), 0.05, -r * 0.9, -r * 0.85, axis="y")
                if mood == "angry":
                    bar(a, "dark", (s * r * 0.15, -r * 0.92, c.z + 0.28), (s * r * 0.5, -r * 0.92, c.z + 0.38), 0.05)
        spike(a, "beak", (0, -r * 0.88, c.z - 0.05), (0, -r * 1.05, c.z - 0.22), 0.13)
        if k == 0:
            for s in S2:  # крылья только у нижней
                slab(a, key_, [(-0.3, z + 0.2), (-0.4, z + 0.9), (0.0, z + 1.1), (0.5, z + 0.8), (0.5, z + 0.2)],
                     s * r * 0.92, s * (r + 0.18))
                for dx in (-0.1, 0.1):
                    spike(a, "beak", (s * 0.3 + dx, -0.4, z + 0.05), (s * 0.3 + dx, -0.62, z), 0.1)
        if k == 2:
            for s in S2:
                spike(a, key_, (s * r * 0.55, 0, c.z + r * 0.7), (s * r * 0.8, 0.05, c.z + r * 1.35), 0.24)
        z = c.z + r * 0.85
    face_point(a, (0, -0.6, z - 0.3))
    closeup(a, (0.0, -0.5, t + 0.8))
    a.pose = {"OwlMid": ((0, 0, 15), (0, 0, 0)), "OwlTop": ((0, 0, -25), (0, 0, 0))}
    return a


def nest_deer():
    """24. Олень-гнездо: на ветвистых рогах свиты два гнезда, в них живут птички."""
    a = new("NestDeer", {"deer": ("B07A4A", True), "deerL": ("E8C9A0", False), "antler": ("F3E3C2", True),
                         "nest": ("8F5A31", True), "bird": ("4FA8E0", False), "birdR": ("E8384F", False),
                         "beak": ("FFB01C", False), "hoof": ("2E2A38", False)})
    t = epic_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0.1, t + 1.3))
    z = t
    layered(a, "deer", [(-0.95, z + 1.05), (-1.05, z + 1.55), (-0.7, z + 1.75), (0.75, z + 1.65), (1.05, z + 1.35),
                        (0.9, z + 0.95), (-0.8, z + 0.95)], [(0.42, 1, 1), (0.54, 0.92, 0.9)], (0, z + 1.35))
    for (s, f), name in (((1, -1), "LegFL"), ((-1, -1), "LegFR"), ((1, 1), "LegBL"), ((-1, 1), "LegBR")):
        y = -0.62 if f < 0 else 0.62
        part(a, name, "Body", (s * 0.26, y, z + 1.05))
        kchain(a, "deer", [(s * 0.26, y, z + 1.1), (s * 0.26, y - 0.05, z + 0.5), (s * 0.26, y, z + 0.1)],
               [0.24, 0.19, 0.17])
        a.box("hoof", s * 0.26 - 0.11, s * 0.26 + 0.11, y - 0.13, y + 0.09, z, z + 0.12, bevel=0.01)
    part(a, "Tail", "Body", (0, 0.98, z + 1.5))
    spike(a, "deerL", (0, 0.98, z + 1.5), (0, 1.2, z + 1.7), 0.22)
    part(a, "Head", "Body", (0, -0.85, z + 1.65))
    kchain(a, "deer", [(0, -0.8, z + 1.55), (0, -1.05, z + 2.15)], [0.46, 0.38])
    hz = z + 2.15
    blob(a, "deer", (0, -1.15, hz + 0.2), 0.32, 0.38, 0.28, n=3)
    taper(a, "deerL", (0, -1.4, hz + 0.15), (0, -1.72, hz + 0.05), 0.32, 0.22, 0.28, 0.2)
    blob(a, "dark", (0, -1.76, hz + 0.08), 0.1, 0.07, 0.08, n=2)
    for s in S2:
        round_eye(a, (s * 0.17, -1.42, hz + 0.3), 0.07, look=(0, 0.6))  # косится вверх на жильцов
        spike(a, "deer", (s * 0.28, -1.1, hz + 0.32), (s * 0.65, -1.0, hz + 0.42), 0.2)
    part(a, "Antlers", "Head", (0, -1.1, hz + 0.45))
    for s in S2:
        p = [V((s * 0.12, -1.1, hz + 0.45)), V((s * 0.45, -1.05, hz + 0.85)), V((s * 0.75, -0.9, hz + 1.2)),
             V((s * 0.95, -0.7, hz + 1.5))]
        kchain(a, "antler", [tuple(q) for q in p], [0.13, 0.11, 0.1, 0.08], overlap=0.2)
        for q, d in ((p[1], (0.3, -0.25, 0.3)), (p[2], (-0.2, -0.3, 0.35))):
            spike(a, "antler", tuple(q), tuple(q + V((s * d[0], d[1], d[2]))), 0.08)
        nc = p[2] + V((s * 0.05, 0.0, 0.05))  # гнездо на развилке
        a.frame("nest", ngon(nc.x, nc.y, 0.32, 8), 0.1, nc.z - 0.05, nc.z + 0.12, axis="z")
        a.prism("nest", ngon(nc.x, nc.y, 0.24, 8), nc.z - 0.08, nc.z - 0.02)
    for k, s in enumerate((1, -1)):
        nc = V((s * 0.8, -0.9, hz + 1.25))
        name = f"Bird{k + 1}"
        part(a, name, "Antlers", tuple(nc))
        key_ = "bird" if k == 0 else "birdR"
        blob(a, key_, (nc.x, nc.y, nc.z + 0.18), 0.16, 0.15, 0.15, n=2)
        spike(a, "beak", (nc.x, nc.y - 0.15, nc.z + 0.2), (nc.x, nc.y - 0.3, nc.z + 0.18), 0.06)
        disc(a, "dark", nc.x + 0.06, nc.z + 0.24, 0.03, nc.y - 0.17, nc.y - 0.14, n=6, axis="y", bevel=0)
        disc(a, "dark", nc.x - 0.06, nc.z + 0.24, 0.03, nc.y - 0.17, nc.y - 0.14, n=6, axis="y", bevel=0)
    face_point(a, (0, -1.5, hz + 0.25))
    closeup(a, (0.8, -0.9, hz + 1.3), eye_off=(-0.8, -1.6, 0.6))
    a.pose = {"Head": ((8, 0, 10), (0, 0, 0)), "Bird1": ((0, 0, 30), (0, 0, 0.05)), "LegFL": ((-20, 0, 0), (0, 0, 0))}
    return a


def giant_penguin():
    """25. Пингвин-гигант: огромное тело-яйцо с вписанным белым животом, ласты-лопасти вдоль боков, крупные лапы —
    и крошечная головка (шутка), но с явным лицом: большие глаза и клюв (D64 «Анатомия»)."""
    a = new("GiantPenguin", {"navy": ("273A6E", True), "orange": ("FF9F1C", False)})
    t = epic_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0, t + 1.3))
    z = t
    A.body(a, "navy", (0, 0.06, z), 1.42, 1.26, 2.72, "egg", n=8, t0=0.07, t1=0.96,
           front=("white", 1.0, z + 0.1, z + 2.3))  # тело-яйцо ступенями, белый живот вписан в ярусы
    for s in S2:
        A.foot(a, "orange", (s * 0.56, -0.5, z), (s * 0.12, -1, 0), 0.82, 0.58, toes=3, h=0.16, z=z)
    for s, name in ((1, "FlipperL"), (-1, "FlipperR")):
        part(a, name, "Body", (s * 1.22, 0.05, z + 2.05))
        A.flipper(a, "navy", (s * 1.18, 0.05, z + 2.1), (s * 1.58, 0.12, z + 0.95), 0.62, 0.16, thick=0.24,
                  bend=(s * 0.16, 0.0, 0.0), up=(s, 0, 0))
    part(a, "Head", "Body", (0, 0.0, z + 2.72))
    hz = z + 2.93
    A.ball(a, "navy", (0, 0.0, hz), 0.27, n=4, rz=0.25)  # крошечная головка
    for s in S2:
        A.body(a, "white", (s * 0.12, -0.18, hz - 0.15), 0.09, 0.07, 0.26, "egg", n=2)  # белые щёчки под глазами
        A.eye(a, (s * 0.11, -0.22, hz + 0.06), 0.1, normal=(s * 0.4, -1, 0.15), look=(0, 0.1), pupil=0.55)
    A.beak(a, "orange", (0, -0.24, hz - 0.06), (0, -1, -0.2), 0.26, 0.16)
    face_point(a, (0, -0.3, hz))
    closeup(a, (0.0, -1.2, z + 1.4))
    a.pose = {"Head": ((0, 15, 0), (0, 0, 0)), "FlipperL": ((0, 25, 0), (0, 0, 0)), "FlipperR": ((0, -10, 0), (0, 0, 0))}
    return a


def ball_bear():
    """26. Медведь-шар: совершенно круглый белый медведь, лапки торчат в стороны, катится."""
    a = new("BallBear", {"fur": ("F4F8FF", True), "furS": ("DCE6F2", False), "nose": ("2E2A38", False)})
    t = epic_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0, t + 1.3))
    c = V((0, 0, t + 1.4))
    blob(a, "fur", tuple(c), 1.35, 1.35, 1.35, n=7)
    blob(a, "furS", (0, -1.12, c.z + 0.1), 0.42, 0.28, 0.32, n=3)  # мордочка
    disc(a, "nose", 0, c.z + 0.22, 0.12, -1.42, -1.34, n=8, axis="y")
    a.box("mouth", -0.12, 0.12, -1.4, -1.36, c.z - 0.06, c.z - 0.02, bevel=0)
    eyes(a, 0.38, -1.2, c.z + 0.5, 0.11)
    cheeks(a, 0.65, -1.1, c.z + 0.12, 0.1)
    for s, name in ((1, "EarL"), (-1, "EarR")):
        part(a, name, "Body", (s * 0.75, -0.2, c.z + 1.05))
        disc(a, "fur", s * 0.75, c.z + 1.15, 0.26, -0.35, -0.08, n=8, axis="y")
        disc(a, "furS", s * 0.75, c.z + 1.15, 0.14, -0.39, -0.34, n=8, axis="y", bevel=0)
    for (sx, sz), name in (((1, 1), "PawFL"), ((-1, 1), "PawFR"), ((1, -1), "PawBL"), ((-1, -1), "PawBR")):
        p = c + V((sx * 1.15, -0.45, sz * 0.55))
        part(a, name, "Body", tuple(p))
        blob(a, "fur", tuple(p + V((sx * 0.2, -0.05, 0))), 0.26, 0.22, 0.22, n=3)
        disc(a, "furS", p.x + sx * 0.2, p.z, 0.1, p.y - 0.3, p.y - 0.25, n=6, axis="y", bevel=0)
    face_point(a, (0, -1.4, c.z + 0.25))
    closeup(a, (0.6, -0.6, c.z + 0.8), eye_off=(-1.0, -2.0, 0.6))
    a.pose = {"Body": ((0, 20, 0), (0, 0, 0)), "PawFL": ((0, 0, 20), (0, 0, 0)), "PawBR": ((0, 0, -20), (0, 0, 0))}
    return a


def stilt_whale():
    """27. Кит на ходулях: маленький синий кит шагает на двух длинных ногах-сосульках с коленками."""
    a = new("StiltWhale", {"whale": ("3D5AA8", True), "belly": ("F1E6CF", False), "iceS": ("8FE8FF", False),
                           "iceL": ("DFFBFF", True)})
    t = epic_stand(a, 1.4)
    z = t
    bz = z + 2.6
    for s, name in ((1, "LegL"), (-1, "LegR")):
        part(a, name, "Stand", (s * 0.35, 0.0, bz))
        knee = V((s * 0.45, -0.35 if s > 0 else 0.25, z + 1.4))
        foot = V((s * 0.45, -0.1 if s > 0 else 0.15, z + 0.16))
        kchain(a, "iceL", [(s * 0.35, 0.0, bz), tuple(knee)], [0.18, 0.15])
        blob(a, "iceS", tuple(knee), 0.14, 0.14, 0.14, n=2)
        kchain(a, "iceL", [tuple(knee), tuple(foot)], [0.15, 0.12])
        a.box("iceS", foot.x - 0.2, foot.x + 0.2, foot.y - 0.35, foot.y + 0.15, z, z + 0.16, bevel=0.02)
    part(a, "Body", "Stand", (0, 0.0, bz + 0.2))
    layered(a, "whale", [(-1.0, bz + 0.3), (-1.05, bz + 0.75), (-0.7, bz + 1.05), (0.4, bz + 1.0), (0.95, bz + 0.6),
                         (0.8, bz + 0.15), (-0.7, bz + 0.05)], [(0.5, 1, 1), (0.65, 0.88, 0.85)], (0.0, bz + 0.5))
    slab(a, "belly", [(-1.0, bz + 0.25), (-1.08, bz + 0.5), (0.5, bz + 0.2), (0.4, bz + 0.06), (-0.7, bz + 0.08)],
         -0.45, 0.45)
    for s in S2:
        round_eye(a, (s * 0.32, -0.98, bz + 0.62), 0.09, look=(0, -0.8))  # смотрит вниз — высоко!
        kchain(a, "whale", [(s * 0.5, -0.2, bz + 0.35), (s * 0.85, -0.05, bz + 0.15)], [0.28, 0.12], [0.08, 0.06])
    a.box("mouth", -0.18, 0.18, -1.05, -1.01, bz + 0.32, bz + 0.38, bevel=0)
    part(a, "Tail", "Body", (0, 0.9, bz + 0.5))
    a.extrude("whale", [(-0.55, 1.3), (-0.1, 0.95), (0, 1.05), (0.1, 0.95), (0.55, 1.3), (0.3, 0.92), (-0.3, 0.92)],
              bz + 0.55, bz + 0.67, axis="z")
    face_point(a, (0, -1.05, bz + 0.55))
    closeup(a, (0.0, 0.0, bz + 0.6), eye_off=(-1.2, -2.0, 0.4))
    a.pose = {"LegL": ((-14, 0, 0), (0, 0, 0)), "LegR": ((12, 0, 0), (0, 0, 0)), "Tail": ((0, 15, 0), (0, 0, 0))}
    return a


EPIC = [("WingedWalrus", winged_walrus, "Морж с крылышками", "Epic"),
        ("OwlTotem", owl_totem, "Сова-тотем", "Epic"),
        ("NestDeer", nest_deer, "Олень-гнездо", "Epic"),
        ("GiantPenguin", giant_penguin, "Пингвин-гигант", "Epic"),
        ("BallBear", ball_bear, "Медведь-шар", "Epic"),
        ("StiltWhale", stilt_whale, "Кит на ходулях", "Epic")]


def three_head_serpent():
    """30. Ледяной змей: из полыньи поднимаются кольца и три длинные шеи с головами-сосульками и гребнями."""
    a = new("ThreeHeadSerpent", {"water": ("1F6FB8", True), "foam": ("DFFBFF", False), "serp": ("5CC3EB", True),
                                 "serpL": ("BFF3FF", False), "crest": ("2E5BD8", False), "neonEye": ("FFE27A", False)})
    t = legendary_stand(a, 1.6)
    part(a, "Water", "Stand", (0, 0, t))
    a.prism("water", ngon(0, 0, 1.5, 12), t, t + 0.12)
    a.frame("foam", ngon(0, 0, 1.15, 12), 0.16, t + 0.1, t + 0.18, axis="z")
    z = t + 0.12
    part(a, "Body", "Water", (0, 0.3, z + 0.4))
    for k, (x, y) in enumerate(((0.75, 0.6), (-0.8, 0.45))):  # кольца над водой
        tube(a, ("serp", "serpL"), [(x - 0.35, y, z), (x - 0.25, y, z + 0.55), (x + 0.25, y, z + 0.6),
                                    (x + 0.35, y, z)], 0.2)
    for i, (dx, lean, name) in enumerate(((0.0, 0, "HeadMid"), (0.62, 22, "HeadL"), (-0.62, -22, "HeadR"))):
        base = V((dx * 0.5, -0.1, z))
        part(a, name, "Body", tuple(base))
        top = V((dx, -0.35, z + (2.85 if i == 0 else 2.3)))
        mid = base.lerp(top, 0.5) + V((dx * 0.25, 0.25, 0))
        kchain(a, "serp", [tuple(base), tuple(mid), tuple(top)], [0.34, 0.3, 0.26])
        blob(a, "serp", (top.x, top.y - 0.1, top.z + 0.12), 0.26, 0.32, 0.22, n=3)
        taper(a, "serpL", (top.x, top.y - 0.35, top.z + 0.08), (top.x, top.y - 0.7, top.z + 0.02), 0.26, 0.14, 0.2,
              0.1)
        for s in S2:
            disc(a, "neonEye", top.x + s * 0.13, top.z + 0.22, 0.06, top.y - 0.4, top.y - 0.34, n=6, axis="y", bevel=0)
        for k in range(3):  # гребень-сосульки
            spike(a, "crest", (top.x, top.y + 0.05 + 0.12 * k, top.z + 0.28), (top.x, top.y + 0.1 + 0.18 * k,
                                                                                top.z + 0.65 - 0.1 * k), 0.12)
    face_point(a, (0, -0.75, z + 2.95))
    closeup(a, (0.0, 0.3, z + 0.5), eye_off=(-1.2, -2.0, 1.0))
    a.pose = {"HeadL": ((0, 12, 10), (0, 0, 0)), "HeadR": ((0, -10, -12), (0, 0, 0)), "HeadMid": ((8, 0, 0), (0, 0, 0))}
    return a


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
    a.prism("water", ngon(0, 0.0, 1.55, 12), t, t + 0.12)
    a.frame("foam", ngon(0, 0.0, 1.2, 12), 0.18, t + 0.1, t + 0.18, axis="z")
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
    for k in range(2):  # бивень-кристалл витками
        p0 = V((0.1 + 0.07 * k, -1.3 - 0.22 * k, z + 0.82 + 0.1 * k))
        p1 = V((0.1 + 0.07 * (k + 1), -1.3 - 0.22 * (k + 1), z + 0.82 + 0.1 * (k + 1)))
        taper(a, "neonHorn" if k % 2 else "berg", tuple(p0), tuple(p1), 0.18 - k * 0.035, 0.15 - k * 0.035,
              up=(0, 0, 1))
    spike(a, "neonHorn", (0.24, -1.74, z + 1.02), (0.28, -1.95, z + 1.1), 0.1)
    for s, name in ((1, "FinL"), (-1, "FinR")):
        part(a, name, "Body", (s * 0.6, -0.5, z + 0.3))
        kchain(a, "whale", [(s * 0.6, -0.5, z + 0.3), (s * 1.05, -0.3, z + 0.15), (s * 1.25, 0.0, z + 0.12)],
               [0.4, 0.3, 0.14], [0.1, 0.08, 0.07], up=(0, 0, 1))
    part(a, "Tail", "Body", (0, 1.2, z + 0.4))
    kchain(a, "whale", [(0, 1.2, z + 0.4), (0, 1.38, z + 0.75)], [0.4, 0.28], up=(0, 0, 1))
    a.extrude("whale", [(-0.7, 1.55), (-0.1, 1.33), (0, 1.43), (0.1, 1.33), (0.7, 1.55), (0.42, 1.25), (0, 1.2),
                        (-0.42, 1.25)], z + 0.72, z + 0.84, axis="z")
    part(a, "Iceberg", "Body", (0, 0.3, z + 1.25))
    a.frustum("berg", (-0.75, 0.75, -0.4, 1.05), (-0.55, 0.55, -0.15, 0.8), z + 1.2, z + 1.65, bevel=0)
    a.frustum("bergD", (-0.5, 0.5, -0.1, 0.75), (-0.3, 0.15, 0.2, 0.5), z + 1.65, z + 2.4, bevel=0)
    a.frustum("berg", (-0.3, 0.15, 0.2, 0.5), (-0.12, -0.02, 0.32, 0.4), z + 2.4, z + 2.85, bevel=0)
    house(a, -0.35, -0.05, z + 1.65, 0.34, 0.3, 0.28, "wallR")
    house(a, 0.3, 0.05, z + 1.65, 0.3, 0.28, 0.26, "wallY")
    house(a, -0.1, 0.45, z + 2.4, 0.26, 0.24, 0.22, "wallT")
    for x, y, zz in ((-0.6, 0.6, z + 1.65), (0.62, 0.82, z + 1.65)):
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
    a.group = "Body"  # дальше — снова туловище (после цикла ног)
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


LEGENDARY = [("YetiCub", yeti_cub, "Йетёнок-коллекционер", "Legendary"),
             ("IcebergNarwhal", iceberg_narwhal, "Нарвал-айсберг", "Legendary"),
             ("ThreeHeadSerpent", three_head_serpent, "Ледяной змей", "Legendary")]


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    repo, shots = os.path.abspath(argv[0]), os.path.abspath(argv[1])
    quick = "quick" in argv[2:]
    only = [x for x in argv[2:] if x != "quick"]
    items = [x for x in COMMON + RARE + EPIC + LEGENDARY if not only or x[0] in only]
    name = "report.json" if not only else "report_" + "+".join(only)[:120] + ".json"
    out = os.environ.get("GLACIER_OUT")  # предпросмотр полной сборки вне assets (листы «до/после»)
    models = os.path.join(out, "models") if out else os.path.join(repo, "assets", "models", "art", "boss5")
    tex = os.path.join(out, "textures") if out else os.path.join(repo, "assets", "textures", "art", "boss5")
    run(items, repo, shots, models, tex, quick=quick, report_name=name)


if __name__ == "__main__":
    main()
