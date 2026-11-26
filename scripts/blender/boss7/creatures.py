"""Коллекция босса 7 «Копилка-громила» (Банк) — 10 эскизов из 30 для концепт-листа (шаг 1 D64).

Тема — сокровища и жадность. Как утверждённые коллекции 5 и 6: странные и смешные звери, смешное в самом теле
(нелепые пропорции, гибрид двух животных), без гибридов с бытовыми вещами, без людей, текста, логотипов, купюр, оружия
и мемных или чужих персонажей. Сокровища — только акцентом (монеты в щеках и сумке, самородок, жемчужина, самоцветы
брони, горка монет у грифона). Не повторяет зверей и шуток коллекций 1–6 (многоголовость, стопки, длинная шея,
огромные зубы и глаза, хвост-колесо, тело-шар и т. п.). Правила анатомии D64: 3–5 признаков вида (в докстринге),
голова ≈ 1/3 тела (у малышей до 1/2), ноги под центром масс, ярусы D39 со скосами, суставы перекрываются, лицо с
эмоцией; ≤ 3 000 треугольников без подставки. Подставки — цвет редкости (D71, creature_kit).
Редкости эскизов — 4 Common, 3 Rare, 2 Epic, 1 Legendary (доля как в коллекции 12 / 9 / 6 / 3); на арену идёт первое
существо каждой редкости.

Сборка — общий конвейер существ (creature_kit.run, quick — без запекания и экспорта): подвижные части, проверка
суставов joint_check, кадры hero / front / side / face / pose / scale.
Запуск: blender --background --factory-startup --python scripts/blender/boss7/creatures.py -- <репо> [id…]
Кадры: assets/concepts/bosses_5_10/boss7/raw/creatures/ (вне git). build(i, col) — модель для арены.
Помощники (пятна, улыбка, звенья) скопированы из boss6/creatures.py — чужой поток их правит, общей зависимости нет.
Зависит от creature_kit.py, anatomy_kit.py, art_style.py, dragon10/v4_kit.py.
"""

import math
import os
import sys

from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
sys.path.insert(0, BL)
sys.path.insert(0, os.path.join(BL, "dragon10"))
from creature_kit import (S, common_stand, d39v2, epic_stand, legendary_stand, part, rare_stand, run,  # noqa: E402
                          tilt, with_matrix)
import anatomy_kit as A  # noqa: E402
import v4_kit as K  # noqa: E402

V = Vector
S2 = (1, -1)
BASE = {"white": ("FFFFFF", False), "dark": ("1B1B2A", False), "glint": ("FFFFFF", False),
        "mouth": ("5A1E2E", False), "pink": ("FF7F9F", False), "ivory": ("F3E9D2", False),
        "tongue": ("FF6F91", False), "coin": ("FFC93A", False), "coinL": ("FFE27A", False)}
GLOW = 1.1


def new(item_id, pal):
    a = S.Art(f"Art_{item_id}", ring_z0=1.0)
    d39v2(a)
    for k, (code, r) in {**BASE, **pal}.items():
        a.paint(k, code, rings=r)
    return a


def glow(a, strength=GLOW):
    """Материалы ключей neon* светятся (эмиссия цветом ключа)."""
    build0 = a.build

    def build(collection):
        obj = build0(collection)
        for key, mat in zip(list(a.colors), a.materials):
            if key.startswith("neon"):
                b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
                b.inputs["Emission Color"].default_value = (*S.lin(a.colors[key][0]), 1)
                b.inputs["Emission Strength"].default_value = strength
        return obj

    a.build = build


def kchain(a, key, pts, ws, hs=None, up=(0, -1, 0), cut=A.CUT, overlap=0.45):
    K.KEY = key
    K.chain(a, pts, ws, hs, up=up, cut=cut, overlap=overlap)


def taper(a, key, p0, p1, w0, w1, h0=None, h1=None, up=(0, 0, 1), cut=0.26):
    K.KEY = key
    K.taper(a, p0, p1, w0, w1, h0, h1, up=up, cut=cut)


def spike(a, key, base, tip, w):
    K.KEY = key
    K.spike(a, base, tip, w)


def face_point(a, p):
    a.face = tuple(p)


def closeup(a, target, eye_off=(-1.2, -2.2, 1.0)):
    t = V(target)
    a.closeup = (tuple(t + V(eye_off)), tuple(t))


def eye2(a, c, r, normal, mood, s, skin, brow="dark", closed=False, look=(0.0, 0.0), show_brow=True, **kw):
    A.eye(a, c, r, normal=normal, mood=mood, side=s, skin_key=skin, brow_key=brow, closed=closed, look=look,
          brow=show_brow, **kw)


def front_y(tiers, x, z):
    """Передняя (−y) поверхность ярусов A.body в точке (x, z), с учётом скоса углов."""
    best = min(tiers, key=lambda tr: abs((tr[0] + tr[1]) / 2 - z))
    za, zb, bx, by, wx, wy, cut = best
    dx = abs(x - bx)
    return by - wy + max(dx - (wx - cut), 0.0)


def grin(a, c, w, h=0.07, key="mouth", teeth=0):
    """Улыбка-брусок с уголками вверх (и белыми зубками)."""
    x, y, z = c
    a.box(key, x - w / 2, x + w / 2, y - 0.03, y + 0.04, z - h / 2, z + h / 2, bevel=0)
    for s in S2:
        a.box(key, x + s * w / 2 - 0.035, x + s * w / 2 + 0.035, y - 0.036, y + 0.034, z, z + h * 1.4, bevel=0)
    for i in range(teeth):
        tx = x - w / 3 + i * (2 * w / 3) / max(teeth - 1, 1)
        a.box("white", tx - 0.03, tx + 0.03, y - 0.045, y - 0.025, z - h / 2 - 0.05, z - h / 2 + 0.005, bevel=0)


def coin(a, c, normal, r=0.16, th=0.05, spin=0.0):
    """Монетка: восьмигранный диск и выпуклая середина, плоскость поперёк normal."""
    m = Matrix.Translation(V(c)) @ V(normal).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4() @ \
        Matrix.Rotation(math.radians(spin), 4, "Z")
    a.prism("coin", S.octagon(-r, r, -r, r, r * 0.29), -th / 2, th / 2, bevel=0, matrix=m)
    q = r * 0.64
    a.prism("coinL", S.octagon(-q, q, -q, q, q * 0.29), th / 2 - 0.01, th / 2 + 0.018, bevel=0, matrix=m)


def gemstone(a, key, keyL, c, r, h, turn=0.0, tilt_deg=0.0):
    """Ограненный камень: восьмигранная площадка сверху, павильон-пирамида снизу (в поверхность), светлая грань-блик;
    tilt_deg — наклон вокруг y (камень на скосе)."""
    m = Matrix.Translation(V(c)) @ Matrix.Rotation(math.radians(tilt_deg), 4, "Y") @         Matrix.Rotation(math.radians(turn), 4, "Z")
    a.prism(key, S.octagon(-r, r, -r, r, r * 0.4), -h * 0.15, h * 0.25, bevel=0, matrix=m)
    a.frustum(key, (-r * 0.92, r * 0.92, -r * 0.92, r * 0.92), (0, 0, 0, 0), -h * 0.15, -h * 0.75, bevel=0, matrix=m)
    a.prism(keyL, S.octagon(-r * 0.55, r * 0.55, -r * 0.55, r * 0.55, r * 0.22), h * 0.2, h * 0.33, bevel=0,
            matrix=m)


def jewel(a, key, c, r, tilt_deg=0.0):
    """Гранёный самоцвет в золотой оправе на поверхности: оправа — низкий золотой восьмигранник шире камня, камень —
    восьмигранник с гранёной верхушкой (усечённая пирамида, повёрнутая на 22.5°), блик; tilt_deg — наклон вокруг y."""
    m = Matrix.Translation(V(c)) @ Matrix.Rotation(math.radians(tilt_deg), 4, "Y")
    hexa = [(r * 1.3 * math.cos(math.radians(60 * i)), r * 1.3 * math.sin(math.radians(60 * i))) for i in range(6)]
    a.prism("gold", hexa, -0.03 - 0.004 * (int(abs(c[1]) * 37) % 5), 0.04, bevel=0, matrix=m)  # оправа
    a.prism(key, S.octagon(-r, r, -r, r, r * 0.4), 0.0, 0.08, bevel=0, matrix=m)
    a.frustum(key, (-r * 0.8, r * 0.8, -r * 0.8, r * 0.8), (-r * 0.3, r * 0.3, -r * 0.3, r * 0.3), 0.075, 0.15,
              bevel=0, matrix=m @ Matrix.Rotation(math.radians(22.5), 4, "Z"))  # гранёная верхушка


def round_ball(a, keys, c, r, n=8, sides=16):
    """Круглый шар: n ярусов-16-угольников (силуэт круглый, ступени D39); keys — цвета ярусов снизу вверх."""
    x, y, z = c
    for k in range(n):
        za, zb = -r + 2 * r * k / n, -r + 2 * r * (k + 1) / n
        zm = (za + zb) / 2
        rr = max(math.sqrt(max(r * r - zm * zm, 0.0)), r * 0.3) / math.cos(math.pi / sides)  # ширина по граням = 2r
        pts = [(x + rr * math.cos(math.pi / sides + 2 * math.pi * i / sides),
                y + rr * math.sin(math.pi / sides + 2 * math.pi * i / sides)) for i in range(sides)]
        a.prism(keys[k % len(keys)], pts, z + za - (0.005 if k else 0), z + zb + 0.005, bevel=0)


def tri_ear(a, key, inner, base, tip, w, th=0.07, up=(0, -1, 0)):
    """Ухо-лист: от основания к кончику сужается, с внутренней светлой вставкой."""
    b, t = V(base), V(tip)
    kchain(a, key, [b, b.lerp(t, 0.55), t], [w, w * 0.75, w * 0.18], [th, th, th * 0.8], up=up, overlap=0.4)
    if inner:
        n = V(up).normalized() * 0.04
        kchain(a, inner, [b - n, b.lerp(t, 0.55) - n, b.lerp(t, 0.9) - n], [w * 0.6, w * 0.45, w * 0.1],
               [th * 0.5] * 3, up=up, overlap=0.3)


# ══ COMMON ═════════════════════════════════════════════════════════════════════════════════════════════════════

def hoard_hamster():
    """1. Хомяк-щекастик: набил щёки монетами так, что щёки шире его самого; из губ торчат две монетки, лапками
    придерживает щёку — жадно-довольная ухмылка. Признаки: защёчные мешки, короткое плотное тело, маленькие круглые
    уши, пара резцов, короткие лапки с розовыми пальцами, хвостик-пенёк."""
    a = new("HoardHamster", {"ham": ("F0A050", True), "hamL": ("FFF1DC", True), "hamD": ("C8763A", False),
                             "paw": ("FFB3C6", False)})
    t = common_stand(a, 1.55)
    part(a, "Body", "Stand", (0, 0.15, t + 0.5))
    A.body(a, "ham", (0, 0.2, t), 0.62, 0.56, 1.0, "egg", n=4, front=("hamL", 0.66, t + 0.1, t + 0.8))
    for s in S2:  # лапки-ступни впереди
        A.foot(a, "paw", (s * 0.34, -0.1, t), (s * 0.15, -1, 0), 0.34, 0.2, toes=3, h=0.1, z=t)
    taper(a, "hamD", (0, 0.7, t + 0.2), (0, 0.86, t + 0.26), 0.16, 0.12)  # хвостик-пенёк
    part(a, "Head", "Body", (0, 0.1, t + 1.0))
    hc = V((0, 0.02, t + 1.35))
    th = A.body(a, "ham", (hc.x, hc.y, hc.z - 0.4), 0.46, 0.42, 0.78, "ball", n=3)
    # щёки-мешки: два огромных светлых шара по бокам, шире тела (полуширина тела 0.62 — щёки до 1.05)
    for s in S2:
        A.body(a, "ham", (s * 0.5, -0.12, hc.z - 0.62), 0.46, 0.44, 0.8, "ball", n=4, floor=0.4)
        a.prism("hamL", S.octagon(s * 0.5 - 0.26, s * 0.5 + 0.26, hc.z - 0.5, hc.z - 0.08, 0.1), -0.58, -0.5,
                axis="y", bevel=0)  # светлая щека спереди
    for s in S2:  # уши
        A.ball(a, "ham", (s * 0.3, 0.12, hc.z + 0.38), 0.15, n=2, ry=0.07)
        a.prism("paw", S.octagon(s * 0.3 - 0.08, s * 0.3 + 0.08, hc.z + 0.32, hc.z + 0.46, 0.03), 0.02, 0.06,
                axis="y", bevel=0)
        eye2(a, (s * 0.17, front_y(th, s * 0.17, hc.z + 0.12) + 0.02, hc.z + 0.12), 0.08, (s * 0.2, -1, 0.1), "sly",
             s, "ham", "hamD")
    fy = front_y(th, 0, hc.z - 0.05)
    a.prism("pink", S.octagon(-0.07, 0.07, -0.05, 0.05, 0.02), fy - 0.06, fy + 0.04, axis="y", bevel=0,
            matrix=Matrix.Translation((0, 0, hc.z - 0.04)))  # нос
    a.box("mouth", -0.11, 0.11, fy - 0.03, fy + 0.04, hc.z - 0.19, hc.z - 0.14, bevel=0)
    a.box("white", -0.06, 0.06, fy - 0.05, fy + 0.02, hc.z - 0.27, hc.z - 0.18, bevel=0)  # резцы
    a.box("mouth", -0.008, 0.008, fy - 0.06, fy - 0.04, hc.z - 0.27, hc.z - 0.18, bevel=0)
    for s, ang in ((1, 18), (-1, -24)):  # две монетки торчат из уголков рта
        coin(a, (s * 0.17, fy - 0.04, hc.z - 0.2), (s * 0.4, -1, 0.15), r=0.11, th=0.035, spin=ang)
    for s, nm in ((1, "ArmL"), (-1, "ArmR")):  # лапки обнимают щёки
        part(a, nm, "Body", (s * 0.4, -0.1, t + 0.75))
        A.limb(a, "ham", [(s * 0.4, -0.1, t + 0.75), (s * 0.62, -0.42, t + 0.78), (s * 0.55, -0.55, t + 0.98)],
               [0.17, 0.15, 0.13])
        A.ball(a, "paw", (s * 0.55, -0.6, t + 1.0), 0.09, n=2)
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.6, -0.4, hc.z - 0.3))
    a.pose = {"Head": ((0, 0, 8), (0, 0, 0)), "ArmL": ((-15, 0, 0), (0, 0, 0))}
    return a


def star_nose_mole():
    """2. Крот-звездонос: нашёл золотой самородок и прижал его огромными лапами-лопатами, нос-звезда распушился от
    счастья, глазки зажмурены (кроты почти не видят). Признаки: розовая «звезда» из мясистых лучей на кончике
    морды, огромные широкие передние лапы с когтями, бархатная тёмная шерсть, крошечные глаза, толстый хвост."""
    a = new("StarNoseMole", {"mole": ("4E3F6E", True), "moleL": ("7C6AA6", False), "star": ("FF6FA8", False),
                             "starD": ("E0457F", False), "palm": ("FFB3C6", False), "claw": ("F3E9D2", False),
                             "nug": ("F5B21C", False), "nugL": ("FFE27A", False)})
    t = common_stand(a, 1.5)
    part(a, "Body", "Stand", (0, 0.2, t + 0.5))
    A.body(a, "mole", (0, 0.25, t), 0.7, 0.66, 0.85, "egg", n=4, front=("moleL", 0.55, t + 0.12, t + 0.6))
    taper(a, "mole", (0, 0.75, t + 0.25), (0, 1.05, t + 0.12), 0.22, 0.16)  # хвост
    for s in S2:
        A.foot(a, "palm", (s * 0.36, 0.0, t), (s * 0.2, -1, 0), 0.3, 0.2, toes=3, h=0.09, z=t)
    part(a, "Head", "Body", (0, -0.05, t + 0.85))
    hc = V((0, -0.25, t + 1.12))
    th = A.body(a, "moleL", (hc.x, hc.y, hc.z - 0.32), 0.4, 0.4, 0.64, "ball", n=4)
    fy = front_y(th, 0, hc.z - 0.05)
    taper(a, "moleL", (0, fy + 0.15, hc.z - 0.05), (0, fy - 0.32, hc.z - 0.1), 0.34, 0.26, 0.28, 0.22)  # морда
    sc = V((0, fy - 0.36, hc.z - 0.1))
    a.prism("starD", S.octagon(-0.13, 0.13, -0.13, 0.13, 0.05), sc.y - 0.05, sc.y + 0.08, axis="y", bevel=0,
            matrix=Matrix.Translation((0, 0, sc.z)))
    for i in range(10):  # звезда: 10 тупых мясистых лучей
        ang = math.radians(i * 36 + 18)
        d = V((math.cos(ang), 0, math.sin(ang)))
        taper(a, "star", sc + d * 0.08 + V((0, 0.02, 0)), sc + d * (0.34 + 0.04 * (i % 2)) + V((0, -0.03, 0)), 0.1,
              0.07, 0.07, 0.05, up=(0, -1, 0))
    for s in S2:  # зажмуренные глазки-щёлочки
        x = s * 0.2
        a.box("dark", x - 0.07, x + 0.07, front_y(th, x, hc.z + 0.12) - 0.02, front_y(th, x, hc.z + 0.12) + 0.04,
              hc.z + 0.1, hc.z + 0.14, bevel=0, matrix=tilt((x, 0, hc.z + 0.12), "Y", -s * 15))
    a.box("mouth", -0.1, 0.1, fy - 0.02, fy + 0.05, hc.z - 0.3, hc.z - 0.25, bevel=0)
    # огромные лапы-лопаты держат самородок у груди
    nug = V((0, -0.72, t + 0.45))
    part(a, "Nugget", "Body", tuple(nug))
    for i, (dx, dy, dz, r) in enumerate(((0, 0, 0, 0.2), (0.14, -0.05, 0.1, 0.13), (-0.13, 0.02, 0.12, 0.12))):
        A.ball(a, "nug" if i else "nugL", tuple(nug + V((dx, dy, dz))), r, n=2)
    for s, nm in ((1, "ArmL"), (-1, "ArmR")):
        sh = V((s * 0.55, -0.2, t + 0.6))
        part(a, nm, "Body", tuple(sh))
        A.limb(a, "mole", [sh, sh + V((s * 0.12, -0.3, -0.05))], [0.24, 0.22], joints=False)
        w = sh + V((s * 0.12, -0.33, -0.05))
        palm = w + V((-s * 0.12, -0.22, 0.0))
        kchain(a, "palm", [w, palm], [0.42, 0.5], [0.12, 0.1], up=(s * 0.6, -1, 0), overlap=0.4)  # широкая ладонь
        for k in range(5):  # когти веером
            o = (k - 2) * 0.09
            b = palm + V((0, 0, o))
            spike(a, "claw", b + V((-s * 0.05, -0.02, 0)), b + V((-s * 0.25, -0.06, o * 0.4)), 0.07)
    face_point(a, (0, fy - 0.2, hc.z))
    closeup(a, (0.2, -0.3, t + 0.6))
    a.pose = {"Head": ((0, 0, -10), (0, 0, 0)), "Nugget": ((0, 0, 15), (0, 0, 0))}
    return a


def gold_axolotl():
    """3. Аксолотль-златожабр: золотой, а жабры разрослись в огромную розовую «корону» вокруг головы — уверен, что
    он и есть главное сокровище хранилища. Признаки: широкая плоская голова с улыбкой, наружные жабры (по 3 ветки
    с каждой стороны, с бахромой), маленькие глаза, 4 короткие лапки с пальцами, хвост с плавником-гребнем."""
    a = new("GoldAxolotl", {"axo": ("FFC23A", True), "axoL": ("FFE59A", False), "gill": ("FF4FA0", False),
                            "gillL": ("FF9FCB", False), "fin": ("FFD86E", False)})
    glow(a, 0)
    t = common_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0.4, t + 0.3))
    pts = [(0, -0.2, t + 0.3), (0, 0.25, t + 0.3), (0, 0.7, t + 0.28), (0.15, 1.1, t + 0.24), (0.35, 1.35, t + 0.2)]
    kchain(a, "axo", pts, [0.72, 0.66, 0.5, 0.34, 0.16], [0.5, 0.48, 0.4, 0.3, 0.16], up=(0, 0, 1))
    kchain(a, "fin", [(0, 0.3, t + 0.5), (0, 0.75, t + 0.48), (0.15, 1.12, t + 0.4), (0.35, 1.4, t + 0.3)],
           [0.07, 0.07, 0.06, 0.05], [0.18, 0.26, 0.24, 0.14], up=(0, 0, 1))  # гребень вдоль спины и хвоста
    for s in S2:
        for y0 in (-0.1, 0.62):
            A.limb(a, "axo", [(s * 0.3, y0, t + 0.24), (s * 0.55, y0 - 0.1, t + 0.12), (s * 0.6, y0 - 0.15, t + 0.04)],
                   [0.14, 0.12, 0.1])
            for k in range(3):
                taper(a, "axoL", (s * 0.6, y0 - 0.15, t + 0.04), (s * (0.68 + 0.04 * k), y0 - 0.32 + 0.1 * k, t + 0.03),
                      0.05, 0.04)
    part(a, "Head", "Body", (0, -0.3, t + 0.4))
    hc = V((0, -0.55, t + 0.42))
    th = A.body(a, "axo", (hc.x, hc.y, hc.z - 0.26), 0.58, 0.42, 0.56, "barrel", n=3, floor=0.6)
    fy = front_y(th, 0, hc.z)
    for s in S2:
        eye2(a, (s * 0.3, front_y(th, s * 0.3, hc.z + 0.12) + 0.02, hc.z + 0.12), 0.075, (s * 0.3, -1, 0.1),
             "proud", s, "axo", "dark", show_brow=False)
        a.box("pink", s * 0.42 - 0.06, s * 0.42 + 0.06, front_y(th, s * 0.42, hc.z - 0.02) - 0.02,
              front_y(th, s * 0.42, hc.z - 0.02) + 0.04, hc.z - 0.05, hc.z + 0.01, bevel=0)  # румянец
    mp = [(-0.34, 0.0), (-0.18, -0.07), (0.0, -0.09), (0.18, -0.07), (0.34, 0.0)]  # широкая улыбка
    kchain(a, "mouth", [(x, front_y(th, x, hc.z - 0.1 + dz) - 0.01, hc.z - 0.1 + dz) for x, dz in mp],
           [0.045] * 5, [0.045] * 5, up=(0, -1, 0), cut=0.2, overlap=0.3)
    # жабры-корона: по 3 ветки с каждой стороны головы, на каждой — бахрома светлых пёрышек
    for s in S2:
        for k, (ang, ln) in enumerate(((35, 0.62), (70, 0.7), (105, 0.58))):
            r = math.radians(ang)
            root = V((s * 0.45, hc.y + 0.12, hc.z + 0.1 + 0.05 * k))
            d = V((s * math.cos(r) * 0.95, 0.15, math.sin(r)))
            tip = root + d * ln
            kchain(a, "gill", [root, root.lerp(tip, 0.5), tip], [0.11, 0.1, 0.08], up=(0, -1, 0), overlap=0.4)
            for j in range(3):
                p = root.lerp(tip, 0.4 + 0.25 * j)
                side = V((-d.z, 0, d.x * 1.0)).normalized() * s
                taper(a, "gillL", p, p + side * 0.16 + d * 0.06, 0.06, 0.03, up=(0, -1, 0))
                taper(a, "gillL", p, p - side * 0.14 + d * 0.06, 0.06, 0.03, up=(0, -1, 0))
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.2, 0.3, t + 0.4))
    a.pose = {"Head": ((0, 0, 10), (0, 0, 0))}
    return a


def raccoon_magpie():
    """4. Сорока-енот: два знаменитых воришки в одном звере — тело и крылья сороки, а голова с чёрной маской и
    круглыми ушами и пушистый полосатый хвост — енота; в клюве уносит монету, хитро щурится. Признаки: сорока —
    чёрно-белое оперение с сине-зелёным отливом крыла, клюв, тонкие лапы 3+1; енот — тёмная маска через глаза,
    светлая морда, круглые уши со светлой каймой, хвост в тёмных кольцах."""
    a = new("RaccoonMagpie", {"mag": ("23263A", True), "magW": ("F4F4F8", True), "magB": ("2E7BE0", False),
                              "magT": ("26C6B0", False), "rac": ("9AA0AE", True), "racL": ("E9EBF0", False),
                              "racD": ("2A2D3A", False), "leg": ("2A2D3A", False)})
    t = common_stand(a, 1.45)
    part(a, "Body", "Stand", (0, 0.1, t + 0.5))
    A.body(a, "mag", (0, 0.15, t + 0.32), 0.48, 0.5, 0.9, "egg", n=5, lean=-0.12,
           front=("magW", 0.75, t + 0.35, t + 1.0))
    for s in S2:  # тонкие лапы и пальцы
        A.limb(a, "leg", [(s * 0.2, 0.1, t + 0.4), (s * 0.22, 0.05, t + 0.16), (s * 0.22, -0.02, t + 0.03)],
               [0.08, 0.07, 0.06], joints=False)
        for dx in (-0.08, 0.0, 0.08):
            taper(a, "leg", (s * 0.22, -0.02, t + 0.03), (s * 0.22 + dx, -0.22, t + 0.03), 0.05, 0.04)
        part(a, "Wing" + ("L" if s > 0 else "R"), "Body", (s * 0.42, 0.1, t + 1.0))
        A.folded_wing(a, "magB", "magT", (s * 0.36, 0.05, t + 1.05), s, 0.75, 0.3, rows=2, down=(0, 0.6, -1))
        a.group = "Body"
    part(a, "Tail", "Body", (0, 0.55, t + 0.5))
    pts = [(0, 0.55, t + 0.5), (0, 0.85, t + 0.62), (0, 1.05, t + 0.95), (0, 1.12, t + 1.35)]
    for i in range(len(pts) - 1):  # пушистый енотовый хвост кольцами
        kchain(a, "rac" if i % 2 == 0 else "racD", [pts[i], pts[i + 1]], [0.3 + 0.02 * i, 0.32], up=(0, 1, 0))
    spike(a, "racD", pts[-1], (0, 1.12, t + 1.6), 0.24)
    part(a, "Head", "Body", (0, 0.05, t + 1.2))
    hc = V((0, -0.02, t + 1.45))
    th = A.body(a, "rac", (hc.x, hc.y, hc.z - 0.3), 0.4, 0.38, 0.62, "ball", n=4)
    fy = front_y(th, 0, hc.z)
    a.prism("racD", S.octagon(-0.38, 0.38, hc.z - 0.02, hc.z + 0.16, 0.05), fy - 0.03, fy + 0.15, axis="y",
            bevel=0)  # чёрная маска через глаза
    a.prism("racL", S.octagon(-0.2, 0.2, hc.z - 0.22, hc.z - 0.02, 0.06), fy - 0.03, fy + 0.15, axis="y", bevel=0)
    for s in S2:
        eye2(a, (s * 0.17, fy - 0.03, hc.z + 0.07), 0.075, (0, -1, 0), "sly", s, "racD", "racL")
        A.ball(a, "rac", (s * 0.26, hc.y + 0.05, hc.z + 0.33), 0.13, n=2, ry=0.06)  # круглые уши
        a.prism("racL", S.octagon(s * 0.26 - 0.09, s * 0.26 + 0.09, hc.z + 0.27, hc.z + 0.42, 0.03), hc.y - 0.02,
                hc.y + 0.0, axis="y", bevel=0)
    A.beak(a, "racD", (0, fy + 0.02, hc.z - 0.1), (0, -1, -0.15), 0.3, 0.13)
    coin(a, (0.0, fy - 0.27, hc.z - 0.2), (1, 0, 0), r=0.15, th=0.045)  # монета в клюве
    face_point(a, (0, fy, hc.z))
    closeup(a, (-0.2, -0.2, t + 0.8))
    a.pose = {"Tail": ((20, 0, 0), (0, 0, 0)), "Head": ((0, 0, -12), (0, 0, 0))}
    return a


# ══ RARE ═══════════════════════════════════════════════════════════════════════════════════════════════════════

def pouch_kangaroo():
    """5. Кенгуру-кубышка: сумка так набита монетами, что перевешивает — кенгуру откинулась назад и сидит на своём
    хвосте, как на стуле; монеты горкой торчат из сумки. Признаки: длинные ступни задних лап, толстый хвост-опора,
    маленькие передние лапки, длинные уши, вытянутая морда, сумка на животе."""
    a = new("PouchKangaroo", {"roo": ("E0874A", True), "rooL": ("FBE3C2", True), "rooD": ("A85E2C", False)})
    t = rare_stand(a, 1.6)
    part(a, "Body", "Stand", (0, 0.2, t + 0.6))
    A.body(a, "roo", (0, 0.35, t + 0.15), 0.5, 0.48, 1.25, "pear", n=5, lean=0.25,
           front=("rooL", 0.6, t + 0.6, t + 1.3))
    kchain(a, "roo", [(0, 0.6, t + 0.45), (0, 1.0, t + 0.25), (0, 1.35, t + 0.08), (0, 1.5, t + 0.05)],
           [0.36, 0.3, 0.22, 0.14], up=(0, 0, 1))  # хвост-опора до земли
    for s in S2:  # бедро, длинная ступня вперёд
        A.body(a, "roo", (s * 0.42, 0.35, t + 0.1), 0.24, 0.42, 0.5, "egg", n=3)
        taper(a, "rooD", (s * 0.44, 0.2, t + 0.07), (s * 0.48, -0.6, t + 0.05), 0.2, 0.16, 0.12, 0.1)
    # сумка: большой светлый шар на животе, сверху — горка монет
    part(a, "Pouch", "Body", (0, -0.2, t + 0.6))
    pc = V((0, -0.32, t + 0.25))
    tp = A.body(a, "rooL", tuple(pc), 0.5, 0.42, 0.72, "egg", n=4)
    a.frame("rooD", S.octagon(-0.4, 0.4, pc.y - 0.33, pc.y + 0.3, 0.12), 0.07, pc.z + 0.66, pc.z + 0.74, axis="z",
            bevel=0)  # край сумки
    a.prism("coin", S.octagon(-0.33, 0.33, pc.y - 0.26, pc.y + 0.24, 0.12), pc.z + 0.62, pc.z + 0.8, bevel=0)
    for i, (dx, dy, dz, ang) in enumerate(((-0.15, -0.1, 0.86, 20), (0.12, 0.0, 0.9, -30), (0.0, -0.18, 0.96, 70),
                                           (0.22, -0.15, 0.84, 50))):
        coin(a, (dx, pc.y + dy, pc.z + dz), (math.sin(math.radians(ang)), -0.5, 1), r=0.13, th=0.04, spin=ang)
    part(a, "Head", "Body", (0, 0.4, t + 1.3))
    hc = V((0, 0.38, t + 1.6))
    th = A.body(a, "roo", (hc.x, hc.y, hc.z - 0.25), 0.3, 0.3, 0.52, "ball", n=3)
    fy = front_y(th, 0, hc.z)
    A.snout(a, "roo", (0, fy + 0.08, hc.z - 0.08), (0, -1, -0.15), 0.3, 0.24, 0.17, nose_key="dark", nose=0.4,
            mouth=0.6)
    for s in S2:
        eye2(a, (s * 0.15, fy + 0.03, hc.z + 0.08), 0.075, (s * 0.25, -1, 0.1), "worried", s, "roo", "rooD")
        tri_ear(a, "roo", "rooL", (s * 0.15, hc.y + 0.05, hc.z + 0.22), (s * 0.3, hc.y + 0.1, hc.z + 0.75), 0.2)
    for s, nm in ((1, "ArmL"), (-1, "ArmR")):  # лапки держат край сумки
        part(a, nm, "Body", (s * 0.32, -0.05, t + 1.1))
        A.limb(a, "roo", [(s * 0.32, -0.05, t + 1.12), (s * 0.4, -0.35, t + 0.98), (s * 0.3, -0.62, t + 0.98)],
               [0.13, 0.11, 0.1])
    face_point(a, (0, fy - 0.2, hc.z))
    closeup(a, (0.1, -0.5, t + 0.7))
    a.pose = {"Head": ((0, 0, 12), (0, 0, 0)), "ArmL": ((-20, 0, 0), (0, 0, 0))}
    return a


def gem_armadillo():
    """6. Броненосец-самоцвет: вся его броня — ряды огранённых самоцветов в золотой оправе; носит богатство на себе
    и гордо задрал нос. Признаки: поясной панцирь из колец (5 поясов), щиток на голове, длинная узкая морда, большие
    торчащие уши, короткие лапы с когтями, хвост в кольцах."""
    a = new("GemArmadillo", {"dil": ("F2C3A8", True), "dilD": ("C98E72", False), "shell": ("B8875A", True),
                             "gemR": ("E8283C", False), "gemS": ("2E6FE0", False), "gemE": ("2FC46A", False),
                             "gemA": ("A64BFF", False), "gemT": ("2ED1C0", False), "gemTL": ("A6FFF4", False),
                             "gold": ("F5B21C", False), "claw": ("F3E9D2", False)})
    t = rare_stand(a, 1.65)
    part(a, "Body", "Stand", (0, 0.1, t + 0.4))
    A.body(a, "dil", (0, 0.1, t + 0.18), 0.55, 0.78, 0.55, "barrel", n=3)  # тело под панцирем
    for s in S2:
        for y0 in (-0.35, 0.55):
            A.limb(a, "dil", [(s * 0.42, y0, t + 0.35), (s * 0.5, y0 - 0.05, t + 0.1)], [0.2, 0.18], joints=False)
            for dx in (-0.06, 0.06):
                spike(a, "claw", (s * 0.5 + dx, y0 - 0.12, t + 0.05), (s * 0.5 + dx, y0 - 0.25, t + 0.0), 0.06)
    # панцирь: 5 поясов-арок цвета панциря, между поясами — золотые ободки; на каждом поясе — 4 гранёных камня
    # разных цветов в золотой оправе (на верху и скосах — видны с ракурса игрока)
    cols = ("gemR", "gemS", "gemE", "gemA", "gemT")
    g = 0
    for k in range(5):
        y = -0.55 + 0.27 * k
        w, h = 0.72 - 0.04 * abs(k - 2), 0.62 - 0.05 * abs(k - 2)
        a.prism("shell", A._clip(S.octagon(-w, w, t + 0.2, t + 0.2 + 2 * h, w * 0.5), (0, -1), -(t + 0.3)),
                y - 0.13, y + 0.13, axis="y", bevel=0)
        a.frame("gold", S.octagon(-w - 0.03, w + 0.03, t + 0.17, t + 0.23 + 2 * h, w * 0.5), 0.05, y + 0.12,
                y + 0.15, axis="y", bevel=0)
        zc, c = t + 0.2 + h, w * 0.5
        for gx, gz, tl in ((-0.17, zc + h, 0), (0.17, zc + h, 0), (w - c / 2, zc + h - c / 2, -45),
                           (-(w - c / 2), zc + h - c / 2, 45)):
            jewel(a, cols[g % len(cols)], (gx, y, gz), 0.1, tl)
            g += 1
    part(a, "Head", "Body", (0, -0.65, t + 0.45))
    hc = V((0, -0.82, t + 0.55))
    th = A.body(a, "dil", (hc.x, hc.y, hc.z - 0.22), 0.28, 0.26, 0.44, "ball", n=3)
    a.prism("gemT", S.octagon(-0.24, 0.24, hc.y - 0.2, hc.y + 0.18, 0.08), hc.z + 0.12, hc.z + 0.25, bevel=0.01)
    gemstone(a, "gemTL", "white", (0, hc.y - 0.02, hc.z + 0.3), 0.09, 0.14)
    fy = front_y(th, 0, hc.z)
    taper(a, "dil", (0, fy + 0.1, hc.z - 0.05), (0, fy - 0.38, hc.z + 0.08), 0.2, 0.1, 0.18, 0.09)  # морда вверх
    a.box("dilD", -0.05, 0.05, fy - 0.42, fy - 0.36, hc.z + 0.05, hc.z + 0.12, bevel=0)
    for s in S2:
        eye2(a, (s * 0.15, front_y(th, s * 0.15, hc.z + 0.05) + 0.02, hc.z + 0.05), 0.06, (s * 0.3, -1, 0.1),
             "proud", s, "dil", "dilD")
        tri_ear(a, "dil", "pink", (s * 0.17, hc.y + 0.08, hc.z + 0.15), (s * 0.32, hc.y + 0.12, hc.z + 0.55), 0.17)
    part(a, "Tail", "Body", (0, 0.75, t + 0.3))
    pts = [(0, 0.7, t + 0.3), (0, 0.95, t + 0.22), (0.1, 1.2, t + 0.12), (0.2, 1.38, t + 0.06)]
    for i in range(3):
        kchain(a, "gemS" if i % 2 else "shell", [pts[i], pts[i + 1]], [0.2 - 0.05 * i, 0.15 - 0.05 * i], up=(0, 0, 1))
    face_point(a, (0, fy - 0.1, hc.z))
    closeup(a, (0.3, -0.3, t + 0.9))
    a.pose = {"Head": ((0, 0, 10), (0, 0, 0)), "Tail": ((0, 0, 15), (0, 0, 0))}
    return a


def pearl_otter():
    """7. Выдра-жемчужница: лежит на спине на маленькой волне и обнимает лапками по бокам одну круглую блестящую
    жемчужину размером с её голову, с розовым перламутровым бликом — любуется ею и никому не отдаст. Признаки: светлая голова и морда калана, тёмное длинное
    тело, перепончатые задние лапы торчат вверх, плоский хвост, маленькие передние лапки, усы.
    v2 (владелец 2026-11-26): жемчужина одна, крупная, на груди в лапках; выдра лежит поперёк кадра (голова влево) —
    жемчужина не прячется за головой."""
    a = new("PearlOtter", {"ott": ("7A4E33", True), "ottL": ("F0DFC4", True), "ottD": ("4E3020", False),
                           "pearl": ("F6F0FF", False), "pearlP": ("FFB6DD", False), "pearlB": ("D6CCF4", False),
                           "pearlW": ("FFFFFF", False),
                           "water": ("3BA7E0", True), "foam": ("E6F7FF", False)})
    t = rare_stand(a, 1.6)
    rz = Matrix.Rotation(math.radians(-90), 4, "Z")  # голова (−y модели) смотрит влево, к камере 3/4

    def P(p):
        return tuple(rz @ V(p))

    part(a, "Body", "Stand", P((0, 0.1, t + 0.4)))
    with_matrix(a, rz)
    a.prism("water", S.octagon(-1.0, 1.0, -1.25, 1.25, 0.5), t, t + 0.14, bevel=0.01)  # волна-лужица
    for x, y in ((-0.8, -0.6), (0.85, 0.4), (-0.55, 0.95), (0.6, -0.95)):
        a.prism("foam", S.octagon(x - 0.14, x + 0.14, y - 0.09, y + 0.09, 0.04), t + 0.12, t + 0.2, bevel=0)
    m = Matrix.Translation((0, 0.2, t + 0.38)) @ Matrix.Rotation(math.radians(-90), 4, "X")
    A.body(a, "ott", (0, 0, -0.6), 0.5, 0.3, 1.3, "egg", n=5, matrix=m)  # тело лёжа на спине, голова к −y
    a.prism("ottL", S.octagon(-0.36, 0.36, -0.45, 0.6, 0.12), t + 0.6, t + 0.68, bevel=0)  # светлое брюхо
    for s in S2:  # перепончатые задние лапы вверх
        kchain(a, "ott", [(s * 0.2, 0.8, t + 0.45), (s * 0.28, 1.0, t + 0.75)], [0.16, 0.14], up=(0, 1, 0))
        kchain(a, "ottD", [(s * 0.28, 1.0, t + 0.75), (s * 0.34, 1.1, t + 1.0)], [0.26, 0.32], [0.06, 0.05],
               up=(0, 1, 0.3), overlap=0.3)
    kchain(a, "ottD", [(0, 0.95, t + 0.35), (0, 1.22, t + 0.3), (0, 1.42, t + 0.28)], [0.28, 0.26, 0.2],
           [0.08, 0.08, 0.07], up=(0, 0, 1))  # плоский хвост
    # жемчужина — одна, крупная, круглая, на груди; блики сверху (видны с ракурса игрока)
    part(a, "Pearl", "Body", P((0, -0.15, t + 0.7)))
    with_matrix(a, rz)
    r = 0.3  # шар: диаметр 0.6 — меньше головы выдры (0.66), ширина = высоте
    pc = V((0, -0.12, t + 0.68 + r - 0.04))  # лежит на груди
    round_ball(a, ["pearlB", "pearlB", "pearlB"] + ["pearl"] * 9, pc, r, n=12)  # 12 ярусов — круглее
    a.prism("pearlP", S.octagon(-0.2, 0.04, pc.y - 0.17, pc.y + 0.05, 0.07), pc.z + r - 0.05, pc.z + r + 0.006,
            bevel=0)  # розовый перламутровый блик
    a.box("white", -0.14, -0.06, pc.y - 0.12, pc.y - 0.04, pc.z + r - 0.03, pc.z + r + 0.01, bevel=0)
    for s, nm in ((1, "ArmL"), (-1, "ArmR")):  # лапки обнимают жемчужину с боков
        part(a, nm, "Body", P((s * 0.32, -0.42, t + 0.62)))
        with_matrix(a, rz)
        A.limb(a, "ott", [(s * 0.32, -0.42, t + 0.62), (s * 0.46, -0.24, t + 0.8), (s * 0.35, -0.12, t + 0.94)],
               [0.13, 0.12, 0.11])
    part(a, "Head", "Body", P((0, -0.65, t + 0.55)))
    with_matrix(a, rz)
    hc = V((0, -0.8, t + 0.64))
    th = A.body(a, "ottL", (hc.x, hc.y, hc.z - 0.27), 0.33, 0.3, 0.52, "ball", n=4)
    fy = front_y(th, 0, hc.z)
    for s in S2:
        eye2(a, (s * 0.15, front_y(th, s * 0.15, hc.z + 0.12) + 0.02, hc.z + 0.12), 0.07, (s * 0.2, -1, 0.35),
             "proud", s, "ottL", "ottD", look=(0.0, 0.8))
        A.ball(a, "ott", (s * 0.3, hc.y + 0.05, hc.z + 0.24), 0.08, n=2)
        for k in range(2):  # усы
            taper(a, "ottD", (s * 0.1, fy - 0.04, hc.z - 0.08 + 0.05 * k), (s * 0.36, fy - 0.1, hc.z - 0.03 + 0.08 * k),
                  0.025, 0.02)
    a.prism("ottD", S.octagon(-0.08, 0.08, -0.05, 0.05, 0.02), fy - 0.05, fy + 0.04, axis="y", bevel=0,
            matrix=Matrix.Translation((0, 0, hc.z - 0.02)))
    grin(a, (0, fy - 0.01, hc.z - 0.15), 0.14, h=0.05)
    a.transform = None
    face_point(a, P((0, fy, hc.z)))
    closeup(a, P((0.0, -0.15, t + 1.0)))
    a.pose = {"Head": ((0, 0, 12), (0, 0, 0)), "Pearl": ((0, 0, 0), (0, 0, 0.05))}
    return a


# ══ EPIC ═══════════════════════════════════════════════════════════════════════════════════════════════════════

def golden_pheasant():
    """8. Фазан-златовлас: золотой хохол такой длинный, что струится с макушки по спине до самого хвоста, как
    грива, — и фазан гордо задрал клюв. Признаки настоящего золотого фазана: золотой хохол, оранжевая накидка на шее
    с тёмными полосками, алая грудь и брюхо, зелёная спина, синее крыло, длинный пятнистый хвост, светлый клюв, лапы."""
    a = new("GoldenPheasant", {"red": ("E8283C", True), "crest": ("FFD23A", True), "crestL": ("FFF0A0", False),
                               "cape": ("FF8A1E", True), "capeD": ("2A2D3A", False), "green": ("2FB06A", False),
                               "blue": ("2E6FE0", False), "tail": ("C9863A", False), "tailD": ("7A4A1E", False),
                               "beak": ("FFD8A0", False), "leg": ("D9A66A", False)})
    t = epic_stand(a, 1.65)
    part(a, "Body", "Stand", (0, 0.05, t + 0.8))
    # тело — яйцо лёжа (птичья посадка): грудь вперёд-вверх, круп назад
    kchain(a, "red", [(0, -0.45, t + 0.95), (0, -0.1, t + 0.85), (0, 0.3, t + 0.85), (0, 0.6, t + 0.92)],
           [0.5, 0.64, 0.6, 0.4], [0.62, 0.7, 0.6, 0.42], up=(0, 0, 1), overlap=0.5)
    a.prism("green", S.octagon(-0.24, 0.24, -0.05, 0.55, 0.08), t + 1.14, t + 1.22, bevel=0)  # зелёная спина
    for s in S2:
        A.limb(a, "leg", [(s * 0.16, 0.05, t + 0.62), (s * 0.18, 0.12, t + 0.32), (s * 0.18, 0.0, t + 0.04)],
               [0.09, 0.08, 0.07], joints=False)
        for dx in (-0.08, 0.0, 0.08):
            taper(a, "leg", (s * 0.18, 0.0, t + 0.04), (s * 0.18 + dx, -0.2, t + 0.035), 0.05, 0.04)
        part(a, "Wing" + ("L" if s > 0 else "R"), "Body", (s * 0.3, -0.1, t + 1.05))
        A.folded_wing(a, "green", "blue", (s * 0.3, -0.3, t + 1.08), s, 0.85, 0.34, rows=2, down=(0, 1, -0.3))
        a.group = "Body"
    part(a, "Tail", "Body", (0, 0.6, t + 0.92))
    pts = [(0, 0.6, t + 0.95), (0, 0.95, t + 0.78), (0, 1.3, t + 0.5), (0, 1.55, t + 0.2), (0, 1.68, t + 0.06)]
    for i in range(4):  # длинный пятнистый хвост вниз-назад до земли
        kchain(a, "tail" if i % 2 == 0 else "tailD", [pts[i], pts[i + 1]], [0.26 - 0.04 * i, 0.22 - 0.04 * i],
               [0.06, 0.05], up=(0, 0.5, 1))
    part(a, "Head", "Body", (0, -0.5, t + 1.15))
    neck = [(0, -0.48, t + 1.05), (0, -0.56, t + 1.22), (0, -0.6, t + 1.36)]
    kchain(a, "cape", neck, [0.46, 0.38, 0.3], up=(0, -1, 0))  # оранжевая накидка
    for k, (y, z, w) in enumerate(((-0.5, t + 1.12, 0.44), (-0.55, t + 1.24, 0.38))):
        a.frame("capeD", S.octagon(-w / 2 - 0.02, w / 2 + 0.02, y - w / 2 - 0.02, y + w / 2 + 0.02, w * 0.15), 0.035,
                z, z + 0.035, axis="z", bevel=0)  # тёмные полоски накидки
    hc = V((0, -0.64, t + 1.55))
    th = A.body(a, "crest", (hc.x, hc.y, hc.z - 0.17), 0.18, 0.2, 0.34, "ball", n=3)
    fy = front_y(th, 0, hc.z)
    A.beak(a, "beak", (0, fy + 0.03, hc.z - 0.01), (0, -1, 0.3), 0.2, 0.1)
    for s in S2:
        eye2(a, (s * 0.11, front_y(th, s * 0.11, hc.z + 0.05) + 0.01, hc.z + 0.05), 0.055, (s * 0.45, -1, 0.1),
             "proud", s, "crest", "capeD")
    # золотой хохол-грива: от макушки по шее и спине до кончика хвоста, три пряди, кончики светлые
    for k, dx in enumerate((-0.1, 0.0, 0.1)):
        p = [(dx * 0.6, hc.y + 0.02, hc.z + 0.15), (dx, hc.y + 0.3, hc.z + 0.2), (dx * 1.3, -0.25, t + 1.32),
             (dx * 1.5, 0.25, t + 1.3), (dx * 1.4, 0.7, t + 1.14), (dx * 1.2 + 0.02 * k, 1.05, t + 0.92)]
        kchain(a, "crest", p[:5], [0.17, 0.22, 0.24, 0.23, 0.2], [0.1 + 0.006 * k] * 5, up=(0, 0, 1),
               overlap=0.35)
        kchain(a, "crestL", p[4:], [0.19, 0.1], [0.09 + 0.006 * k, 0.06], up=(0, 0, 1), overlap=0.35)
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.0, 0.2, t + 1.2))
    a.pose = {"Head": ((0, 0, -10), (0, 0, 0)), "Tail": ((10, 0, 0), (0, 0, 0))}
    return a


def fleece_alpaca():
    """9. Альпака-золотое руно: шерсть золотая и такая пышная, что альпака стала облаком кудрей на тонких ножках —
    торчат только шея и довольная мордочка. Признаки: длинная шея, уши-«бананы», большие глаза с ресницами, мягкая
    морда с раздвоенной губой, тонкие ноги с двупалыми копытцами, чёлка-помпон."""
    a = new("FleeceAlpaca", {"fl": ("FFC23D", True), "flL": ("FFE38A", True), "alp": ("FFF3DC", False),
                             "alpD": ("C9A77A", False), "hoof": ("5E4636", False)})
    t = epic_stand(a, 1.65)
    part(a, "Body", "Stand", (0, 0.15, t + 0.9))
    for s in S2:  # тонкие ноги
        for y0 in (-0.3, 0.55):
            A.limb(a, "alp", [(s * 0.32, y0, t + 0.75), (s * 0.34, y0, t + 0.3), (s * 0.34, y0 - 0.02, t + 0.08)],
                   [0.12, 0.1, 0.09], joints=False)
            a.prism("hoof", S.octagon(s * 0.34 - 0.08, s * 0.34 + 0.08, y0 - 0.12, y0 + 0.06, 0.03), t, t + 0.09,
                    bevel=0)
    # облако руна: кудри-шары разного размера (двух тонов) вокруг тела
    curls = ((0, 0.15, 1.15, 0.62, "fl"), (0.45, -0.1, 1.05, 0.42, "flL"), (-0.45, -0.1, 1.05, 0.42, "flL"),
             (0.5, 0.45, 1.1, 0.42, "fl"), (-0.5, 0.45, 1.1, 0.42, "fl"), (0.0, 0.7, 1.2, 0.42, "flL"),
             (0.25, 0.1, 1.6, 0.38, "flL"), (-0.25, 0.25, 1.55, 0.38, "fl"), (0.0, -0.3, 1.25, 0.4, "fl"),
             (0.35, 0.5, 1.5, 0.3, "flL"), (-0.4, -0.05, 1.45, 0.3, "flL"))
    for x, y, z, r, k in curls:
        A.ball(a, k, (x, y, t + z), r, n=3)
    part(a, "Head", "Body", (0, -0.35, t + 1.55))
    kchain(a, "fl", [(0, -0.35, t + 1.45), (0, -0.48, t + 1.9), (0, -0.52, t + 2.2)], [0.36, 0.32, 0.3],
           up=(0, -1, 0))  # шея в руне
    hc = V((0, -0.6, t + 2.4))
    th = A.body(a, "alp", (hc.x, hc.y, hc.z - 0.22), 0.25, 0.26, 0.44, "ball", n=3)
    fy = front_y(th, 0, hc.z)
    taper(a, "alp", (0, fy + 0.1, hc.z - 0.1), (0, fy - 0.14, hc.z - 0.13), 0.24, 0.2, 0.2, 0.17)  # морда
    a.box("alpD", -0.08, 0.08, fy - 0.17, fy - 0.12, hc.z - 0.12, hc.z - 0.07, bevel=0)  # нос
    a.box("mouth", -0.008, 0.008, fy - 0.17, fy - 0.13, hc.z - 0.22, hc.z - 0.12, bevel=0)  # раздвоенная губа
    grin(a, (0, fy - 0.15, hc.z - 0.2), 0.12, h=0.04)
    for s in S2:
        eye2(a, (s * 0.13, front_y(th, s * 0.13, hc.z + 0.06) + 0.01, hc.z + 0.06), 0.07, (s * 0.3, -1, 0.1),
             "calm", s, "alp", "alpD", lid=0.3)
        for k in range(2):  # ресницы
            taper(a, "dark", (s * (0.1 + 0.06 * k), front_y(th, s * 0.13, hc.z + 0.12) - 0.01, hc.z + 0.12),
                  (s * (0.12 + 0.09 * k), front_y(th, s * 0.13, hc.z + 0.12) - 0.06, hc.z + 0.19), 0.02, 0.015)
        kchain(a, "alp", [(s * 0.14, hc.y + 0.05, hc.z + 0.16), (s * 0.24, hc.y + 0.02, hc.z + 0.4),
                          (s * 0.2, hc.y - 0.06, hc.z + 0.56)], [0.11, 0.1, 0.05], up=(0, -1, 0))  # уши-бананы
    A.ball(a, "flL", (0, hc.y + 0.02, hc.z + 0.24), 0.16, n=2)  # чёлка-помпон
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.3, -0.2, t + 1.2))
    a.pose = {"Head": ((0, 0, 10), (0, 0, 0))}
    return a


# ══ LEGENDARY ══════════════════════════════════════════════════════════════════════════════════════════════════

def treasure_griffin():
    """10. Грифон-казначей: перед — орёл, зад — лев; лежит на своей горке золотых монет, как лев-сфинкс: грудь
    вперёд, орлиные лапы с когтями вытянуты вперёд, львиный круп и задние лапы по бокам, хвост с кисточкой, крылья
    раскрыты «моё!»; на лбу светится бирюзовый самоцвет. Признаки: белая орлиная голова с крючковатым клювом и хохлом,
    передние птичьи лапы с когтями, львиное тело, задние львиные лапы, хвост с кисточкой, большие крылья.
    v2 (владелец 2026-11-26): белая голова и грудь, синее львиное тело, крылья бирюзовые с золотыми концами; золото —
    только монеты. v3 (2026-11-26): не «птица в шортах» на двух лапах — четвероногий, лежит, как лев."""
    a = new("TreasureGriffin", {"fea": ("F7F7FA", True), "feaD": ("B9C6E2", False), "lion": ("2F62D6", True),
                                "lionD": ("1C3C92", False), "wing": ("2ED1C0", True), "wingT": ("FFC23A", False),
                                "beak": ("FF9A2E", False), "talon": ("FF9A2E", False), "neonGem": ("39F5E0", False),
                                "goldH": ("F5B21C", True)})
    glow(a, 2.0)
    t = legendary_stand(a, 1.7)
    part(a, "Hoard", "Stand", (0, 0, t))  # горка монет — часть композиции
    a.prism("goldH", S.octagon(-1.25, 1.25, -1.2, 1.25, 0.45), t, t + 0.22, bevel=0.01)
    a.prism("coinL", S.octagon(-0.9, 0.9, -0.85, 0.95, 0.3), t + 0.2, t + 0.34, bevel=0)
    for i, (x, y, ang) in enumerate(((-1.0, -0.85, 20), (1.02, -0.7, -35), (0.85, 0.95, 50), (-0.95, 0.8, -10),
                                     (0.15, -1.08, 75))):
        coin(a, (x, y, t + 0.3), (math.sin(math.radians(ang)), -0.6, 1), r=0.16, th=0.045, spin=ang)
    z0 = t + 0.34
    part(a, "Body", "Hoard", (0, 0.2, z0 + 0.4))
    # львиное тело лёжа вдоль y (синее), круп сзади
    kchain(a, "lion", [(0, -0.45, z0 + 0.36), (0, 0.25, z0 + 0.42), (0, 0.82, z0 + 0.38)], [0.8, 0.84, 0.68],
           [0.62, 0.64, 0.54], up=(0, 0, 1), overlap=0.5)
    # орлиная грудь — белая, выпячена вперёд и вверх
    A.body(a, "fea", (0, -0.52, z0 + 0.22), 0.36, 0.26, 0.66, "egg", n=4, lean=-0.1)  # белый нагрудник
    for s in S2:
        # передние орлиные лапы вытянуты вперёд по монетам, белые «штаны» из перьев, когти
        A.body(a, "fea", (s * 0.26, -0.45, z0 + 0.06), 0.15, 0.17, 0.32, "egg", n=2)
        taper(a, "talon", (s * 0.26, -0.52, z0 + 0.12), (s * 0.28, -0.95, z0 + 0.07), 0.14, 0.12, 0.11, 0.1)
        for dx in (-0.07, 0.0, 0.07):
            spike(a, "dark", (s * 0.28 + dx, -0.98, z0 + 0.07), (s * 0.28 + dx * 1.4, -1.12, z0 + 0.02), 0.06)
        # львиные задние лапы: бедро-окорок сбоку, лапа вперёд вдоль бока
        A.body(a, "lion", (s * 0.4, 0.62, z0 + 0.02), 0.2, 0.38, 0.5, "egg", n=3)
        taper(a, "lionD", (s * 0.47, 0.42, z0 + 0.08), (s * 0.5, 0.02, z0 + 0.07), 0.17, 0.16, 0.12, 0.11)
        part(a, "Wing" + ("L" if s > 0 else "R"), "Body", (s * 0.32, -0.05, z0 + 0.8))
        root = V((s * 0.32, -0.02, z0 + 0.8))
        for k, (dz, ln) in enumerate(((0.0, 1.05), (-0.16, 0.92), (-0.32, 0.78))):  # три ряда перьев, вверх-вбок
            tip = root + V((s * ln * 0.78, 0.3, 0.5 + dz + 0.22 * (2 - k)))
            kchain(a, "wing", [root + V((0, 0.06 * k, dz)), root.lerp(tip, 0.6) + V((0, 0.06 * k, dz))],
                   [0.34, 0.3], [0.08, 0.07], up=(0, 1, 0), overlap=0.4)
            kchain(a, "wingT", [root.lerp(tip, 0.6) + V((0, 0.06 * k, dz)), tip + V((0, 0.06 * k, dz))],
                   [0.3, 0.12], [0.07, 0.05], up=(0, 1, 0), overlap=0.4)
        a.group = "Body"
    # львиный хвост: от крупа выходит из-за крыла на сторону игрока (−x) и обвивает горку монет сбоку
    part(a, "Tail", "Body", (0, 1.05, z0 + 0.3))
    kchain(a, "lion", [(0, 1.02, z0 + 0.32), (-0.5, 1.2, z0 + 0.16), (-0.98, 0.85, z0 + 0.06), (-1.12, 0.3, z0 + 0.04),
                       (-1.02, -0.25, z0 + 0.08)], [0.14, 0.13, 0.12, 0.11, 0.1], up=(0, 0, 1), overlap=0.5)
    A.ball(a, "lionD", (-0.95, -0.42, z0 + 0.12), 0.16, n=2)  # кисточка
    part(a, "Head", "Body", (0, -0.55, z0 + 0.85))
    hc = V((0, -0.64, z0 + 1.15))
    th = A.body(a, "fea", (hc.x, hc.y, hc.z - 0.28), 0.32, 0.34, 0.56, "ball", n=4)
    fy = front_y(th, 0, hc.z)
    A.beak(a, "beak", (0, fy + 0.05, hc.z - 0.02), (0, -1, -0.35), 0.32, 0.17)
    for s in S2:
        eye2(a, (s * 0.15, front_y(th, s * 0.15, hc.z + 0.08) + 0.02, hc.z + 0.08), 0.075, (s * 0.35, -1, 0.1),
             "proud", s, "fea", "feaD")
        for k in range(3):  # хохол-перья назад
            spike(a, "feaD", (s * 0.08 * k, hc.y + 0.1, hc.z + 0.24), (s * 0.12 * k, hc.y + 0.45, hc.z + 0.42 - 0.05 * k),
                  0.12)
    gemstone(a, "neonGem", "white", (0, front_y(th, 0, hc.z + 0.22) + 0.02, hc.z + 0.24), 0.09, 0.14)
    face_point(a, (0, fy, hc.z))
    closeup(a, (0.0, -0.2, z0 + 0.6))
    a.pose = {"WingL": ((0, -15, 0), (0, 0, 0)), "WingR": ((0, 15, 0), (0, 0, 0)), "Head": ((0, 0, 10), (0, 0, 0))}
    return a


CREATURES = [("HoardHamster", hoard_hamster, "Хомяк-щекастик", "Common"),
             ("StarNoseMole", star_nose_mole, "Крот-звездонос", "Common"),
             ("GoldAxolotl", gold_axolotl, "Аксолотль-златожабр", "Common"),
             ("RaccoonMagpie", raccoon_magpie, "Сорока-енот", "Common"),
             ("PouchKangaroo", pouch_kangaroo, "Кенгуру-кубышка", "Rare"),
             ("GemArmadillo", gem_armadillo, "Броненосец-самоцвет", "Rare"),
             ("PearlOtter", pearl_otter, "Выдра-жемчужница", "Rare"),
             ("GoldenPheasant", golden_pheasant, "Фазан-златовлас", "Epic"),
             ("FleeceAlpaca", fleece_alpaca, "Альпака-золотое руно", "Epic"),
             ("TreasureGriffin", treasure_griffin, "Грифон-казначей", "Legendary")]


def build(i, col):
    """Модель i для арены: один объект (без разбиения на части)."""
    art = CREATURES[i][1]()
    return [art.build(col)]


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    repo = os.path.abspath(argv[0])
    only = argv[1:]
    shots = os.path.join(repo, "assets", "concepts", "bosses_5_10", "boss7", "raw", "creatures")
    tmp = os.path.join(shots, "_quick")
    items = [x for x in CREATURES if not only or x[0] in only]
    name = "report.json" if not only else "report_" + "+".join(only)[:120] + ".json"
    run(items, repo, shots, tmp, tmp, quick=True, report_name=name)


if __name__ == "__main__":
    main()
