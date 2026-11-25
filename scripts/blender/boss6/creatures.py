"""Коллекция босса 6 «Королева-мухоловка» (Джунгли) — 10 эскизов из 30 для концепт-листа (шаг 3 D64), v2.

Стиль коллекции — как утверждённая ледяная коллекция v2 босса 5: странные и смешные звери джунглей, смешное в самом
теле (нелепые пропорции, глаза врозь, тело-колесо, лист в 10 раз больше муравья), без бытовых вещей, людей, текста,
логотипов, оружия и мемных или чужих персонажей. Правила анатомии D64: у каждого — 3–5 признаков вида (в докстринге),
голова ≈ 1/3 тела, ноги под центром масс, ярусы D39 со скосами, суставы перекрываются, лицо с эмоцией; ≤ 3 000
треугольников без подставки. Редкости эскизов — 4 Common, 3 Rare, 2 Epic, 1 Legendary (доля как в коллекции
12 / 9 / 6 / 3); существа с индексами 0, 4, 7, 9 стоят на арене.
v2 (замечания владельца и дизайнера к v1): шутки ледяной коллекции не повторяем — «много голов» только у попугая,
«башня жуков» заменена муравьём-силачом; на зелёной арене звери не зелёные (лягушка-древолаз красно-синяя, хамелеон
в радужных полосах, гусеница жёлто-чёрная); у хамелеона глаза-башенки, у лягушки круглый полупрозрачный мешок под
подбородком, у ягуара вместо пятен — крупные цветы; Росток — мини-копия мамы: створки-ловушка, розовый венчик,
золотая корона и светящийся самоцвет (ключи neon* светятся, glow()).

Сборка — общий конвейер существ (creature_kit.run, quick — без запекания и экспорта): подвижные части, проверка
суставов joint_check, кадры hero / front / side / face / pose / ingame_phone.
Запуск: blender --background --factory-startup --python scripts/blender/boss6/creatures.py -- <репо> [id…]
Кадры: assets/concepts/bosses_5_10/boss6_v2/raw/creatures/ (вне git). build(i, col) — модель для арены.
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
from creature_kit import (S, bar, common_stand, d39v2, epic_stand, gem, legendary_stand, part, petals,  # noqa: E402
                          rare_stand, run, tilt, with_matrix)
import anatomy_kit as A  # noqa: E402
import v4_kit as K  # noqa: E402

V = Vector
S2 = (1, -1)
BASE = {"white": ("FFFFFF", False), "dark": ("1B1B2A", False), "glint": ("FFFFFF", False),
        "mouth": ("5A1E2E", False), "blush": ("FF9FB2", False), "pink": ("FF7F9F", False),
        "ivory": ("F3E9D2", False), "tongue": ("FF6F91", False)}
GLOW = 1.1  # сила свечения ключей neon*: цвет эмиссии = цвет ключа; сильнее — камень белеет (вид Standard)
FACE_CAM = {}  # id → (камера, цель) кадра face, когда стандартный (спереди) не показывает лицо: у тукана — клюв

_shot0 = S.Preview.shot


def _shot(self, path, eye, target, lens, res):
    """Кадр face по FACE_CAM (своя камера для существа), остальные кадры — как в конвейере."""
    for k, (e, tg) in FACE_CAM.items():
        if os.path.basename(path) == f"{k}_face.png":
            eye, target = e, tg
    return _shot0(self, path, eye, target, lens, res)


S.Preview.shot = _shot


def new(item_id, pal):
    a = S.Art(f"Art_{item_id}", ring_z0=1.0)
    d39v2(a)
    for k, (code, r) in {**BASE, **pal}.items():
        a.paint(k, code, rings=r)
    return a


def glow(a, strength=GLOW):
    """Материалы ключей neon* светятся (эмиссия): обёртка a.build, конвейер creature_kit.run собирает как обычно."""
    build0 = a.build

    def build(collection):
        obj = build0(collection)
        for key, mat in zip(list(a.colors), a.materials):
            if key.startswith("neon"):
                b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
                b.inputs["Emission Color"].default_value = (*S.lin(a.colors[key][0]), 1)  # насыщенный цвет ключа
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


def layered(a, key, prof, layers, anchor, xc=0.0, matrix=None):
    K.KEY = key
    K.layered(a, prof, layers, anchor, xc=xc, matrix=matrix)


def knob(a, key, c, r, n=2):
    """Шар-сустав или кулак без фаски: на мелкой детали фаска почти не видна, а треугольников с ней втрое больше."""
    A.body(a, key, (c[0], c[1], c[2] - r), r, r, 2 * r, "ball", n=n, floor=0.35, bevel=0)


def face_point(a, p):
    a.face = tuple(p)


def closeup(a, target, eye_off=(-1.2, -2.2, 1.0)):
    t = V(target)
    a.closeup = (tuple(t + V(eye_off)), tuple(t))


def eye2(a, c, r, normal, mood, s, skin, brow="dark", closed=False, look=(0.0, 0.0), show_brow=True, **kw):
    A.eye(a, c, r, normal=normal, mood=mood, side=s, skin_key=skin, brow_key=brow, closed=closed, look=look,
          brow=show_brow, **kw)


def brow_bar(a, key, c, normal, w, up, tilt_deg, thick=0.03, depth=0.14):
    """Тонкая бровь-брусок в осях глаза (c, normal): на up выше центра, наклон tilt_deg, уходит в голову на depth —
    сидит на бугре, а не висит над ним."""
    m = Matrix.Translation(V(c)) @ A.facing(normal) @ Matrix.Translation((0, 0, up)) @ Matrix.Rotation(
        math.radians(tilt_deg), 4, "Y")
    a.box(key, -w, w, -0.06, depth, -thick / 2, thick / 2, bevel=0, matrix=m)


FACES = {"R": 0, "B": 90, "L": 180, "F": 270}
_BLOB = [0]


def blob(a, key, tiers, face, u, zc, R, lift=0.024, depth=0.07):
    """Круглое пятно радиуса R на грани ярусов: face — "R"/"B"/"L"/"F" (±x, ±y) или угол нормали грани в градусах
    (45, 135, 225, 315 — скошенные углы восьмиугольника; 225 — грань к игроку в hero), центр zc по высоте и u (−1…1)
    вдоль плоской части грани. На каждом ярусе — брусок шириной по кругу: ступени пятна = ступени тела; выступает на
    lift и уходит в ярус на depth (не летает)."""
    ang = math.radians(FACES.get(face, face))
    n = V((math.cos(ang), math.sin(ang), 0))
    t = V((-n.y, n.x, 0))
    diag = abs(n.x) > 0.3 and abs(n.y) > 0.3
    _BLOB[0] += 1
    e = 0.0025 * (_BLOB[0] % 4)  # у соседних пятен на одном ярусе низ и верх на разной высоте — грани не совпадают
    for za, zb, bx, y, wx, wy, cut in tiers:
        lo, hi = max(za + 0.008 + e, zc - R), min(zb - 0.004 - e, zc + R)
        if hi - lo < 0.03:
            continue
        if diag:
            d = (wx * abs(n.x) + wy * abs(n.y)) - cut * 0.7071
            half = cut * 0.7071 - 0.02
        else:
            d = wx * abs(n.x) + wy * abs(n.y)
            half = (wy if abs(n.x) > 0.5 else wx) - cut - 0.02
        c = u * half
        zs = [lo] + ([zc] if lo + 0.02 < zc < hi - 0.02 else []) + [hi]
        left, right = [], []
        for z in zs:  # срез круга: ширина по высоте — пятно круглое, а не прямоугольник
            hw = max(math.sqrt(max(R * R - (z - zc) ** 2, 0.0)), 0.035)
            left.append((max(c - hw, -half), z))
            right.append((min(c + hw, half), z))
        if min(r[0] - l[0] for l, r in zip(left, right)) < 0.04:
            continue
        o = V((bx, y, 0)) + n * d
        m = Matrix(((t.x, n.x, 0, o.x), (t.y, n.y, 0, o.y), (0, 0, 1, 0), (0, 0, 0, 1)))
        a.extrude(key, left + list(reversed(right)), -depth, lift, axis="y", matrix=m)


_PLATE = [0]


def plate_spot(a, key, tiers, face, u, zc, R, lift=0.025, depth=0.06):
    """Круглое (восьмиугольное) пятно-накладка радиуса R на плоской грани ярусов тела: face — "R" / "L" (±x),
    "B" / "F" (±y), u (−1…1) — сдвиг вдоль плоской части грани, zc — центр по высоте. На каждом ярусе, который
    задевает пятно, — свой срез восьмиугольника на плоскости этого яруса: пятно лежит на ступенях тела и не торчит
    (выступ lift, в ярус уходит на depth)."""
    _PLATE[0] += 1  # свой счётчик: пятна-кляксы blob других существ при общем прогоне не сдвигаются
    e = 0.0025 * (_PLATE[0] % 4)  # у соседних пятен края на разной высоте — грани не совпадают
    side = 1 if face in ("R", "B") else -1
    for za, zb, bx, by, wx, wy, cut in tiers:
        half = (wy if face in ("R", "L") else wx) - cut - 0.02
        if half < R * 0.5:
            continue
        hc = (by if face in ("R", "L") else bx) + u * max(half - R, 0.0)
        oct_ = S.octagon(zc - R, zc + R, hc - R, hc + R, R * 0.42)  # точки (z, h)
        poly = A._clip(A._clip(oct_, (-1, 0), -(za + 0.008 + e)), (1, 0), zb - 0.004 - e)
        c0 = (by if face in ("R", "L") else bx) - half
        poly = A._clip(A._clip(poly, (0, -1), -c0), (0, 1), c0 + 2 * half)
        if len(poly) < 3 or max(p[0] for p in poly) - min(p[0] for p in poly) < 0.03:
            continue
        if face in ("R", "L"):
            f = bx + side * wx
            a.prism(key, poly, f - side * depth, f + side * lift, axis="x", bevel=0)  # точки (z, y): ось x
        else:
            f = by + side * wy
            a.prism(key, [(h, z) for z, h in poly], f - side * depth, f + side * lift, axis="y", bevel=0)


def front_y(tiers, x, z):
    """Передняя (−y) поверхность ярусов A.body в точке (x, z), с учётом скоса углов."""
    best = min(tiers, key=lambda tr: abs((tr[0] + tr[1]) / 2 - z))
    za, zb, bx, by, wx, wy, cut = best
    dx = abs(x - bx)
    return by - wy + max(dx - (wx - cut), 0.0)


def top_spot(a, key, tier, xc, yc, R, lift=0.024):
    """Восьмиугольное пятно на верхней грани яруса tier (из A.body)."""
    za, zb = tier[0], tier[1]
    a.prism(key, S.octagon(xc - R, xc + R, yc - R, yc + R, R * 0.55), zb - 0.04, zb + 0.01 + lift, bevel=0)


def grin(a, c, w, h=0.07, key="mouth", teeth=0):
    """Улыбка-брусок с уголками вверх (и белыми зубками)."""
    x, y, z = c
    a.box(key, x - w / 2, x + w / 2, y - 0.03, y + 0.04, z - h / 2, z + h / 2, bevel=0)
    for s in S2:
        a.box(key, x + s * w / 2 - 0.035, x + s * w / 2 + 0.035, y - 0.036, y + 0.034, z, z + h * 1.4, bevel=0)
    for i in range(teeth):
        tx = x - w / 3 + i * (2 * w / 3) / max(teeth - 1, 1)
        a.box("white", tx - 0.03, tx + 0.03, y - 0.045, y - 0.025, z - h / 2 - 0.05, z - h / 2 + 0.005, bevel=0)


def spots(a, key, tiers, picks, depth=0.05, lift=0.022):
    """Пятна-накладки на плоских гранях ярусов тела (tiers из A.body без matrix): picks = [(ярус, грань, доля, размер)],
    грань: "R" / "L" (±x), "B" (спина, +y), "F" (перед, −y); доля −1…1 — сдвиг вдоль плоской части грани.
    Пятно выступает на lift и уходит в ярус на depth (не летает, грани не совпадают)."""
    for k, face, u, s in picks:
        za, zb, bx, y, wx, wy, cut = tiers[k]
        s = min(s, (zb - za) / 2 - 0.012)
        zc = (za + zb) / 2
        if face in ("R", "L"):
            sx = 1 if face == "R" else -1
            yc = y + u * max(wy - cut - s - 0.02, 0.0)
            x1 = bx + sx * wx
            a.box(key, x1 - sx * depth, x1 + sx * lift, yc - s, yc + s, zc - s, zc + s, bevel=0)
        else:
            sy = 1 if face == "B" else -1
            xc = bx + u * max(wx - cut - s - 0.02, 0.0)
            y1 = y + sy * wy
            a.box(key, xc - s, xc + s, y1 - sy * depth, y1 + sy * lift, zc - s, zc + s, bevel=0)


def pad_hand(a, key, pad_key, wrist, fwd, n=3, length=0.3, spread=0.5, w=0.09, z=0.0):
    """Кисть древолаза: n пальцев веером из запястья вдоль земли, на концах — круглые подушечки (признак вида)."""
    f = V((fwd[0], fwd[1], 0)).normalized()
    wr = V(wrist)
    for i in range(n):
        ang = (i - (n - 1) / 2) * spread
        d = Matrix.Rotation(ang, 3, "Z") @ f
        tip = wr + d * length
        tip.z = z + 0.06 + 0.013 * i  # у пальцев разная высота — нижние грани не совпадают
        taper(a, key, wr, tip, w, w * 0.8, w * 0.75 + 0.004 * i, w * 0.6 + 0.004 * i, cut=0.2)
        r = w * 0.72
        a.prism(pad_key, S.octagon(tip.x - r, tip.x + r, tip.y - r, tip.y + r, r * 0.3), z + 0.004 + 0.005 * i,
                z + 0.1 + 0.011 * i, bevel=0)


def leaf_blade(a, key, vkey, pts, ws, thick, up):
    """Лист-лопасть по точкам pts (ширины ws, толщина thick, плоскость поперёк up) с жилкой вдоль середины."""
    kchain(a, key, pts, ws, [thick] * len(pts), up=up, cut=0.3, overlap=0.3)
    P = [V(p) for p in pts]
    vp = P[:-1] + [P[-2].lerp(P[-1], 0.7)]
    kchain(a, vkey, vp, [0.05] * len(vp), [thick + 0.035] * len(vp), up=up, cut=0.2, overlap=0.2)


# ══ COMMON ═════════════════════════════════════════════════════════════════════════════════════════════════════

def frog_bubble():
    """1. Лягушка-пузырь (древолаз): гордо раздула горловой мешок — круглый прозрачный пузырь почти с неё ростом.
    Признаки: ядовитая окраска (красное тело, синие лапы, чёрные пятна), глаза-бугры на макушке, рот-щель во всю
    голову, сложенные задние лапы, пальцы с круглыми подушечками, горловой мешок под подбородком."""
    a = new("FrogBubble", {"frog": ("E8283C", True), "legB": ("2E6FE0", True), "padB": ("9CC8FF", False),
                           "spot": ("1B1B2A", False), "sac": ("FFD3E4", False)})
    a.transparent_parts = ("Sac",)
    t = common_stand(a, 1.55)
    part(a, "Body", "Stand", (0, 0.2, t + 0.5))
    tb = A.body(a, "frog", (0, 0.32, t), 0.64, 0.58, 1.1, "egg", n=5, lean=-0.32)  # сидит прямо, грудь вперёд
    hc = V((0, -0.1, t + 1.18))
    th = A.body(a, "frog", (hc.x, hc.y, hc.z - 0.34), 0.6, 0.5, 0.68, "ball", n=4)  # широкая плоская голова
    # окраска древолаза: круглые чёрные пятна — плоские накладки на плоских гранях ярусов (бока, спина, макушка),
    # выступ 0.025; на углах морды и скошенных гранях пятен нет (там они читались шипами). Каждое пятно — внутри
    # одного яруса (центр в середине яруса: ступень не режет пятно надвое), разного размера, по диагонали, без пар
    # на одной высоте (схема «два рядом и одно под ними» читается лицом); ниже верха бедра (t + 0.52) на боках пятен
    # нет — там их закрывает бедро, а срез над ним торчал пластиной
    for face, u, zc, R in (("L", -0.8, t + 0.552, 0.1), ("L", 0.7, t + 0.77, 0.06),
                           ("R", 0.4, t + 0.77, 0.095), ("R", -0.8, t + 0.56, 0.06),
                           ("B", -0.5, t + 0.552, 0.1), ("B", 0.6, t + 0.77, 0.07)):  # u > 0 — к спине (+y) или
        plate_spot(a, "spot", tb, face, u, zc, R)  # к +x, u < 0 — к морде; не касаются
    for face, u, zc, R in (("R", 0.7, t + 1.095, 0.06), ("B", 0.3, t + 1.265, 0.07)):  # голова: одно сбоку, одно сзади
        plate_spot(a, "spot", th, face, u, zc, R)
    top_spot(a, "spot", th[-1], -0.05, 0.08, 0.13, lift=0.005)  # пятно на макушке между буграми, почти вровень
    for s in S2:  # глаза-бугры на макушке, прищур «горжусь собой»: веки до середины (бровей нет — на буграх они
        # читались как палочки; гордость держат веки и ухмылка)
        A.ball(a, "frog", (s * 0.34, -0.22, t + 1.5), 0.23, n=3)
        eye2(a, (s * 0.36, -0.41, t + 1.56), 0.13, (s * 0.35, -1, 0.3), "proud", s, "frog", "spot", show_brow=False)
    # рот — самодовольная ухмылка одной дугой по поверхности головы (точки — на гранях яруса, включая скосы углов):
    # щель во всю ширину лица, уголки плавно поднимаются к щекам в 2–3 звена, левый (−x) — выше
    mouth = []
    for i, (x, z) in enumerate(((0.5, 1.13), (0.36, 1.08), (0.16, 1.05), (-0.1, 1.05), (-0.3, 1.075), (-0.43, 1.115),
                                (-0.51, 1.165))):  # глубина точек чередуется на 0.006 — грани звеньев не совпадают
        mouth.append((x, front_y(th, x, t + z) - 0.005 - 0.006 * (i % 2), t + z))
    kchain(a, "mouth", mouth, [0.06, 0.065, 0.07, 0.07, 0.065, 0.06, 0.055], [0.07] * len(mouth), up=(0, -1, 0),
           cut=0.2, overlap=0.3)
    for s in S2:
        # передние лапы по бокам от мешка, пальцы с подушечками
        A.limb(a, "legB", [(s * 0.42, -0.26, t + 0.66), (s * 0.66, -0.42, t + 0.36), (s * 0.66, -0.58, t + 0.1)],
               [0.22, 0.2, 0.17])
        pad_hand(a, "legB", "padB", (s * 0.64, -0.6, t + 0.07), (s * 0.3, -1, 0), length=0.28, spread=0.55, z=t)
        # сложенная задняя лапа: бедро сбоку, голень и стопа вперёд
        thigh = A.body(a, "legB", (s * 0.6, 0.38, t), 0.28, 0.46, 0.52, "egg", n=4, corner=0.5)  # круглое бедро
        for u, zm, R in ((0.6, 0.065, 0.045), (0.0, 0.195, 0.06), (-0.6, 0.325, 0.05)):  # три пятна по диагонали,
            plate_spot(a, "spot", thigh, "R" if s > 0 else "L", u, t + zm, R)  # каждое в середине своего яруса
        taper(a, "legB", (s * 0.66, 0.2, t + 0.13), (s * 0.74, -0.05, t + 0.09), 0.2, 0.16, 0.17, 0.14)
        pad_hand(a, "legB", "padB", (s * 0.74, -0.05, t + 0.07), (s * 0.55, -1, 0), length=0.34, spread=0.5,
                 z=t)
    # горловой мешок — шар из 7 правильных восьмиугольных ярусов: верх сразу под линией рта, низ над подставкой,
    # лапы видны по бокам и под ним; сзади заходит в грудь
    part(a, "Sac", "Body", (0, -0.42, t + 0.85))
    sc = V((0, -0.6, t + 0.64))
    st = A.body(a, "sac", (sc.x, sc.y, sc.z - 0.4), 0.42, 0.4, 0.8, "ball", n=7, floor=0.3, corner=0.58, bevel=0)
    za, zb, bx, yy, wx, wy, cut = st[5]
    a.box("white", -0.17, -0.05, yy - wy - 0.02, yy - wy + 0.03, za + 0.02, zb - 0.01, bevel=0)  # блик
    face_point(a, (0, -0.6, t + 1.25))
    closeup(a, (0.3, 0.3, t + 0.6))
    a.pose = {"Sac": ((0, 0, 0), (0, -0.05, 0.04))}
    return a


def big_beak_toucan():
    """2. Тукан-клювище: клюв вдвое длиннее тела — птица откинулась на хвост, чтобы не клюнуть носом.
    Голова гордо повёрнута к игроку, клюв задран, глаз хитро прищурен.
    Признаки: огромный яркий клюв, чёрное тело и большая светлая манишка, голубое кольцо у глаза, лапы с пальцами
    2+2, хвост."""
    a = new("BigBeakToucan", {"black": ("23243A", True), "throat": ("FFF6D6", False), "beakY": ("FFC21C", True),
                              "beakO": ("FF7A1C", False), "beakR": ("E8384F", False), "ring": ("3FC4F0", False),
                              "feet": ("5B7BD8", False)})
    t = common_stand(a, 1.5)
    z = t + 0.28
    for s in S2:
        part(a, "Leg" + ("L" if s > 0 else "R"), "Stand", (s * 0.22, 0.1, t + 0.35))
        A.limb(a, "feet", [(s * 0.22, 0.15, t + 0.45), (s * 0.24, 0.05, t + 0.05)], [0.14, 0.12], joints=False)
        for k, d in enumerate(((0, -1, 0), (0, 1, 0))):  # пальцы 2 + 2, разной толщины — грани не совпадают
            K.KEY = "feet"
            K.taper(a, (s * 0.25, 0.05, t + 0.05 + 0.006 * k), (s * 0.265, 0.05 + d[1] * 0.32, t + 0.04 + 0.006 * k),
                    0.1 - 0.012 * k, 0.07, 0.07 + 0.01 * k, 0.06, cut=0.2)
    part(a, "Body", "Stand", (0, 0.2, z + 0.4))
    A.body(a, "black", (0, 0.3, z), 0.46, 0.48, 1.05, "egg", n=4, lean=0.2, front=("throat", 0.95, z + 0.3, z + 1.05))
    # большая светлая манишка от горла до живота — тело не «чёрная стопка»
    for s in S2:
        A.folded_wing(a, "black", "black", (s * 0.42, 0.3, z + 0.85), s, 0.85, 0.42, rows=2, down=(0, 0.45, -1))
    part(a, "Tail", "Body", (0, 0.65, z + 0.25))
    A.flipper(a, "black", (0, 0.62, z + 0.3), (0, 1.25, t + 0.02), 0.42, 0.34, thick=0.1, up=(0, 0.3, 1))  # хвост
    part(a, "Head", "Body", (0, 0.35, z + 1.0))
    hc = V((0, 0.32, z + 1.28))
    # голова повёрнута к игроку на 28° (клюв уходит вправо) и клюв задран на 12° — гордо: спереди виден левый глаз
    hm = Matrix.Translation(hc) @ Matrix.Rotation(math.radians(28), 4, "Z") @ Matrix.Rotation(
        math.radians(-12), 4, "X") @ Matrix.Translation(-hc)
    with_matrix(a, hm)
    A.ball(a, "black", tuple(hc), 0.4, n=3, rz=0.46)  # средний ярус высокий — глаз целиком на нём
    for s in S2:  # крупный глаз в голубом кольце кожи на скошенном углу головы, хитрый прищур с бровью
        a.prism("ring", S.octagon(-0.19, 0.19, -0.19, 0.19, 0.07), -0.04, 0.03, axis="y",
                matrix=Matrix.Translation(hc + V((s * 0.31, -0.31, 0.0))) @ A.facing((s, -1, 0.12)))
        eye2(a, tuple(hc + V((s * 0.33, -0.33, 0.0))), 0.13, (s, -1, 0.12), "sly", s, "black", "ring",
             look=(-0.3 * s, 0.1), lid=0.3)  # хитрый прищур: веко на треть; бровь голубая — видна на чёрной голове
    for k, (dy, h) in enumerate(((0.02, 0.2), (0.2, 0.14))):  # два пера-хохолка на макушке, зачёсаны назад
        taper(a, "black", hc + V((0, dy - 0.05, 0.3)), hc + V((0, dy + 0.42, 0.3 + h)), 0.2 - 0.04 * k, 0.07,
              0.1, 0.05, up=(0, 0, 1), cut=0.3)
    # клюв: три цветные секции (жёлтый корень, оранжевая середина, красный кончик), верх и низ
    beak = [(-0.15, 0.35), (-0.7, 0.42), (-1.5, 0.28), (-2.05, -0.05), (-1.9, -0.18), (-1.2, -0.12), (-0.2, -0.22)]
    for i, (key, y0, y1) in enumerate((("beakY", 0.2, -0.75), ("beakO", -0.72, -1.45), ("beakR", -1.42, -2.2))):
        prof = clip_band(beak, y1, y0)  # срез контура полосой (без слипшихся точек — нет вырожденных граней)
        # высота секций чуть разная (−3 % на секцию): в перекрытии верхние грани соседних секций не совпадают
        layered(a, key, [(y, z + 1.2 + zz) for y, zz in prof],
                [(0.2 - 0.01 * i, 1, 1 - 0.03 * i), (0.27 - 0.01 * i, 0.9, 0.82 - 0.03 * i)], (-1.0, z + 1.2),
                matrix=None)
    a.box("dark", -0.24, 0.24, -1.6, -0.2, z + 1.07, z + 1.1, bevel=0)  # линия клюва
    with_matrix(a, None)
    eye_w = hm @ (hc + V((-0.33, -0.33, 0.0)))
    FACE_CAM["BigBeakToucan"] = (tuple(eye_w + V((-1.6, -3.4, 0.6))), tuple(eye_w + V((0.45, -0.2, -0.1))))
    face_point(a, tuple(eye_w))
    closeup(a, (0.0, -1.0, z + 1.2))
    a.pose = {"Head": ((10, 0, 0), (0, 0, 0)), "Tail": ((-10, 0, 0), (0, 0, 0))}
    return a


def clip_band(poly, lo, hi):
    """Выпуклый или простой контур [(u, v)…], обрезанный полосой lo ≤ u ≤ hi (Сазерленд — Ходжмен), без повторов."""
    def cut(pts, inside, at):
        out = []
        for k, p in enumerate(pts):
            q = pts[k - 1]
            if inside(p):
                if not inside(q):
                    out.append(at(q, p))
                out.append(p)
            elif inside(q):
                out.append(at(q, p))
        return out

    def at_u(u0):
        return lambda q, p: (u0, q[1] + (p[1] - q[1]) * (u0 - q[0]) / (p[0] - q[0]))

    pts = cut(list(poly), lambda p: p[0] >= lo, at_u(lo))
    pts = cut(pts, lambda p: p[0] <= hi, at_u(hi))
    res = []
    for p in pts:
        if not res or abs(p[0] - res[-1][0]) + abs(p[1] - res[-1][1]) > 1e-4:
            res.append(p)
    if len(res) > 1 and abs(res[0][0] - res[-1][0]) + abs(res[0][1] - res[-1][1]) <= 1e-4:
        res.pop()
    return res


RAINBOW = ("cR", "cO", "cY", "cG", "cB", "cV")  # от головы к хвосту


def rainbow_chameleon():
    """3. Хамелеон-радуга: не смог выбрать цвет и стал полосатым сразу во все; глаза-башенки смотрят в разные
    стороны (один на игрока, другой в небо), хвост закручен тугой спиралью, хитрая улыбка во всю ширину морды.
    Признаки: шлем-гребень на голове, глаза-башенки (шарик, конус, белок со зрачком на вершине), высокое плотное
    тело с гребнем на спине, лапы-клещи (пальцы вилкой обхватывают ветку), хвост-спираль."""
    a = new("RainbowChameleon", {"cR": ("E8384F", True), "cO": ("FF8A3D", True), "cY": ("FFC21C", True),
                                 "cG": ("7ED957", True), "cB": ("2F7BE8", True), "cV": ("8A4FE0", True),
                                 "head": ("2FC4B2", True), "headD": ("1C8C80", False), "crest": ("FFE45C", False),
                                 "branch": ("8F5A31", True)})
    t = common_stand(a, 1.55)
    zc = t + 0.86
    for s in S2:  # две ветки вдоль тела — лапы-клещи обхватывают их
        K.KEY = "branch"
        K.taper(a, (s * 0.44, -0.95, t + 0.1), (s * 0.44, 0.98, t + 0.1 + 0.012 * s), 0.19, 0.17, 0.2, 0.18,
                up=(0, 0, 1), cut=0.3)
    # ноги: локоть наружу и вверх, лапа-клещи — две толстые «варежки» вилкой по бокам ветки
    for i, (x, y, key) in enumerate(((0.22, -0.42, "cO"), (-0.22, -0.42, "cO"), (0.22, 0.42, "cB"), (-0.22, 0.42, "cB"))):
        s = 1 if x > 0 else -1
        nm = "Leg" + "FB"[i // 2] + "LR"[i % 2]
        part(a, nm, "Stand", (x, y, zc - 0.2))
        ank = V((s * 0.44, y, t + 0.36))
        A.limb(a, key, [(x, y, zc - 0.12), (s * 0.62, y - 0.05, zc - 0.1), tuple(ank)], [0.19, 0.16, 0.15])  # звенья не в одной плоскости
        for dx in (-0.13, 0.13):  # пальцы вилкой: внутренняя и наружная пара охватывают ветку
            taper(a, key, ank + V((dx * 0.2, 0, 0.02)), (s * 0.44 + dx, y + 0.02 * dx / 0.13, t + 0.1), 0.14, 0.11,
                  0.16, 0.12, up=(0, 1, 0), cut=0.3)
    # тело: ярусы вдоль длины (ось z яруса → −y мира), каждый ярус — свой цвет радуги; высокое и плотное
    part(a, "Body", "Stand", (0, 0, zc))
    mb = Matrix.Translation((0, 0.7, zc)) @ Matrix.Rotation(math.radians(90), 4, "X")
    tiers = A.body(a, "cV", (0, 0, 0), 0.38, 0.52, 1.45, lambda u: 0.56 + 0.44 * math.sin(math.pi * u), n=6,
                   keys=list(reversed(RAINBOW)), matrix=mb, lean=0.12)
    for za, zb, bx, ty, wx, wy, cut in tiers:  # гребень на спине
        yy = 0.7 - (za + zb) / 2
        ztop = zc + ty + wy
        spike(a, "crest", (0, yy, ztop - 0.06), (0, yy + 0.1, ztop + 0.2), 0.15)
    # голова: клин с открытой мордой, шлем-гребень назад
    part(a, "Head", "Body", (0, -0.68, zc + 0.12))
    anc = (-1.0, zc + 0.15)
    prof = [(-0.58, zc - 0.12), (-1.1, zc - 0.2), (-1.45, zc - 0.02), (-1.45, zc + 0.14), (-1.15, zc + 0.36),
            (-0.75, zc + 0.5), (-0.55, zc + 0.4), (-0.52, zc + 0.0)]
    layered(a, "head", prof, [(0.2, 1, 1), (0.3, 0.9, 0.86)], anc)
    # шлем-гребень цвета головы (тёмно-бирюзовый): начинается за глазами, высокий, уходит назад над шеей — отдельно
    # от жёлтого гребня спины
    layered(a, "headD", [(-0.9, zc + 0.38), (-0.74, zc + 0.76), (-0.5, zc + 1.04), (-0.27, zc + 1.08),
                         (-0.24, zc + 0.84), (-0.42, zc + 0.44)], [(0.1, 1, 1), (0.17, 0.9, 0.86)], (-0.58, zc + 0.72))
    # хитрая улыбка на плоском торце морды (y = −1.45, |x| < 0.2): тонкая дуга (0.045) почти вровень с мордой
    # (выступ 0.014), уголки загнуты вверх, за бока морды не заходит — не ремешок и не намордник; под серединой
    # дуги — узкая тёмная щель приоткрытого рта (выступ 0.005, ниже дуги), из неё свисает язычок
    smile = [(-0.165, zc + 0.1), (-0.13, zc + 0.058), (-0.05, zc + 0.037), (0.05, zc + 0.037), (0.13, zc + 0.058),
             (0.165, zc + 0.1)]
    smile = [(x, -1.439 + 0.004 * (i % 2), z) for i, (x, z) in enumerate(smile)]  # глубина звеньев чередуется
    kchain(a, "mouth", smile, [0.045] * len(smile), [0.05] * len(smile), up=(0, -1, 0), cut=0.2, overlap=0.3)
    a.box("dark", -0.01, 0.12, -1.455, -1.42, zc - 0.012, zc + 0.03, bevel=0)  # щель рта у основания языка
    # язычок свисает из щели вниз-вперёд (не выходит за край подставки)
    taper(a, "tongue", (0.055, -1.44, zc + 0.0), (0.1, -1.53, zc - 0.18), 0.1, 0.09, 0.06, 0.055, cut=0.25)
    A.ball(a, "tongue", (0.11, -1.54, zc - 0.21), 0.07, n=2)
    # глаза-башенки (в 1.5 раза крупнее): шарик на голове, конус, жёлтое кольцо век, белок со зрачком на торце;
    # ближний к игроку смотрит прямо на него, дальний — почти вверх, «в небо», чуть к игроку (белок со зрачком виден
    # в hero и спереди)
    for s, d, nm, mood in ((-1, (-0.5, -0.82, 0.3), "EyeR", "sly"), (1, (-0.12, -0.52, 0.85), "EyeL", "surprised")):
        d = V(d).normalized()
        b = V((s * 0.2, -1.0, zc + 0.3))
        part(a, nm, "Head", tuple(b))
        A.ball(a, "head", tuple(b + d * 0.08), 0.28, n=3)
        taper(a, "head", b + d * 0.14, b + d * 0.5, 0.48, 0.34, cut=0.3)
        taper(a, "crest", b + d * 0.47, b + d * 0.62, 0.34, 0.26, cut=0.3)  # жёлтое кольцо век
        m = Matrix.Translation(b + d * 0.62) @ A.facing(d)
        a.box("white", -0.125, 0.125, -0.03, 0.03, -0.125, 0.125, bevel=0, matrix=m)
        a.box("dark", -0.075, 0.075, -0.055, -0.025, -0.075, 0.075, bevel=0, matrix=m)
        a.box("glint", -0.06, -0.02, -0.07, -0.05, 0.02, 0.06, bevel=0, matrix=m)
        if mood == "sly":  # бровь на кольце век ближнего глаза: хитро нахмурена (дальний глаз — удивлён, без брови)
            a.box("dark", -0.17, 0.17, -0.06, 0.1, -0.025, 0.025, bevel=0,
                  matrix=m @ Matrix.Translation((0, 0, 0.16)) @ Matrix.Rotation(math.radians(22 * -s), 4, "Y"))
    # хвост: тугая спираль сбоку-сзади, плоскость спирали развёрнута к игроку (виден в hero), полосы радуги
    part(a, "Tail", "Body", (0, 0.6, zc))
    n = V((-0.72, -0.69, 0.0)).normalized()  # нормаль плоскости спирали — к камере hero
    h = V((-n.y, n.x, 0.0))  # в плоскости, горизонтально: от тела назад-влево
    if h.y < 0:
        h = -h
    vz = V((0, 0, 1))
    cc = V((-0.37, 0.98, zc - 0.36))  # на 0.15 внутрь от края подставки
    pts = [V((0, 0.55, zc - 0.02)), V((-0.16, 0.86, zc + 0.02))]
    for k in range(12):
        th = math.radians(100 - k * 38)
        r = 0.42 * (1 - k / 15)
        pts.append(cc + h * (r * math.cos(th)) + vz * (r * math.sin(th)))
    ws = [0.3 - 0.2 * i / (len(pts) - 1) for i in range(len(pts))]
    for i in range(len(pts) - 1):
        K.KEY = RAINBOW[(i + 3) % 6]
        K.taper(a, pts[i], pts[i + 1], ws[i], ws[i + 1], ws[i] * 1.1, ws[i + 1] * 1.1, up=tuple(n), cut=0.26,
                ext0=ws[i] * 0.2 if i else 0.0, ext1=ws[i + 1] * 0.2)
    face_point(a, (0, -1.3, zc + 0.3))
    tg = V((-0.1, -1.2, zc + 0.25))
    FACE_CAM["RainbowChameleon"] = (tuple(tg + V((-1.7, -3.7, 0.9))), tuple(tg))
    closeup(a, (0.3, 0.0, zc), eye_off=(-0.2, -2.4, 0.9))
    a.pose = {"EyeL": ((0, 20, -15), (0, 0, 0)), "EyeR": ((0, -15, 20), (0, 0, 0)), "Tail": ((0, 0, -12), (0, 0, 0))}
    return a


def knot_sloth():
    """4. Ленивец-узел: лапы такие длинные, что он завязал их узлом над головой — и уснул, довольный.
    Признаки: светлая маска с тёмными полосами от глаз, длинные изогнутые когти, лохматая шерсть, сонная улыбка."""
    a = new("KnotSloth", {"fur": ("A27A55", True), "furD": ("7A5638", False), "mask": ("F1DDB8", False),
                          "claw": ("F3E9D2", False), "moss": ("6E9F45", False), "mossD": ("4C7A34", False)})
    t = common_stand(a, 1.45)
    part(a, "Body", "Stand", (0, 0.1, t + 0.5))
    tb = A.body(a, "fur", (0, 0.15, t), 0.66, 0.6, 1.15, "pear", n=5, lean=-0.1, front=("mask", 0.6, t + 0.15, t + 0.75))
    # мох в шерсти: неровные пятна из двух приглушённых оттенков (круг побольше и сдвинутый поменьше поверх)
    for face, u, zc, R, u2, dz, R2 in (("B", 0.45, t + 0.85, 0.15, 0.15, 0.1, 0.09), ("B", -0.4, t + 0.35, 0.12, -0.15,
                                                                                       -0.06, 0.07)):
        blob(a, "moss", tb, face, u, zc, R)
        blob(a, "mossD", tb, face, u2, zc + dz, R2, lift=0.036, depth=0.055)  # дно мельче — не совпадает с дном пятна
    blob(a, "mossD", tb, "R", 0.4, t + 0.62, 0.1)
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
    a.box("furD", -0.07, 0.07, -0.545, -0.47, hc.z - 0.1, hc.z - 0.02, bevel=0)  # нос
    grin(a, (0, -0.5, hc.z - 0.18), 0.22)
    for s, nm in ((1, "ArmL"), (-1, "ArmR")):  # руки вверх, крест-накрест над головой, кисти свисают на другой бок
        sh = V((s * 0.34, 0.08, t + 1.0))
        part(a, nm, "Body", tuple(sh))
        A.ball(a, "fur", (s * 0.4, 0.06, t + 1.02), 0.24, n=3)  # плечо входит в тело
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
    """5. Гусеница-многоглазка: пугает птиц ложными глазками — на каждом сегменте по круглому «глазу», а настоящее
    лицо одно, на голове, и очень довольно своей хитростью. Ползёт боком к игроку, тело изогнуто волной.
    Признаки: «осиная» жёлто-чёрная окраска (широкий чёрный пояс на каждом сегменте), ложные глазки (чёрный круг
    в белом кольце, без зрачка и бровей), короткие толстые ложноножки под каждым сегментом, щетинки на спине, жёлтая
    голова с чёрной маской-повязкой на уровне глаз и рожками-бугорками."""
    a = new("ManyEyeCaterpillar", {"cat": ("FFD21C", True), "catD": ("2B2B36", False), "catO": ("FF8A1F", True),
                                   "catL": ("FFE36A", False), "pad": ("FF9A3D", False), "ocW": ("FFF8E0", False)})
    t = rare_stand(a, 1.6)
    lifts = (0.0, 0.15, 0.34, 0.24, 0.06, 0.1)  # волна: горб посередине
    xs = [1.12 - 0.38 * k for k in range(6)]
    segs = [(xs[k], t + 0.3 + 0.01 * k + lifts[k], 0.3 + 0.01 * k) for k in range(6)]  # (x, z центра, радиус)
    seg_tiers = []
    for k, (x, zc, r) in enumerate(segs):
        nm = "Body" if k == 0 else f"Seg{k}"
        part(a, nm, "Stand" if k == 0 else ("Body" if k == 1 else f"Seg{k - 1}"), (x + 0.19, 0, zc))
        tiers = A.body(a, "cat", (x, 0, zc - r), r, r * 0.95, 2 * r, "ball", n=3, t0=0.1, t1=0.9, floor=0.35)  # бочонок
        seg_tiers.append(tiers)
        # ложный глазок на боку к игроку и на спине-боку сзади: чёрный восьмиугольник в белом кольце на среднем
        # (самом широком) ярусе; без зрачка-взгляда и бровей — пятно, а не лицо
        wy = tiers[1][5]
        for sy in (-1, 1):
            a.prism("ocW", S.octagon(x - 0.105, x + 0.105, zc - 0.105, zc + 0.105, 0.04), sy * (wy - 0.06),
                    sy * (wy + 0.022), axis="y", bevel=0)
            a.prism("catD", S.octagon(x - 0.06, x + 0.06, zc - 0.06, zc + 0.06, 0.023), sy * (wy - 0.04),
                    sy * (wy + 0.045), axis="y", bevel=0)
        # щетинки на спине — короткие тупые, как у гусениц; основание в верхнем ярусе (верх сегмента — zc + 0.8·r),
        # без перекладины между ними: сверху она с поясом складывалась в рамку
        for e in S2:
            blunt(a, "catD", (x + e * 0.07, 0.06, zc + r * 0.7), (x + e * 0.1 + 0.04, 0.16, zc + r + 0.17), 0.08, 0.04)
        # короткие толстые ложноножки-обрубки под сегментом, подушечка снизу
        for e in S2:
            K.KEY = "catD"
            K.taper(a, (x, e * 0.15, zc - r * 0.55), (x - 0.02, e * 0.17, t + 0.07), 0.15, 0.13, 0.13, 0.12, cut=0.3)
            a.box("pad", x - 0.1, x + 0.06, e * 0.17 - 0.08, e * 0.17 + 0.08, t + 0.005 + 0.004 * k, t + 0.08,
                  bevel=0)
        # чёрный пояс-кольцо («осиная» окраска) на хвостовом краю своего сегмента, за ложным глазком: контур —
        # сечение только этого сегмента (ступени ярусов), выступ 0.04 — пояс лежит на своём сегменте и нигде не
        # поднимается над соседом рамкой; где сосед выше, пояс уходит в него
        belt(a, "catD", x + 0.16, (tiers,), 0.05, 0.04)
    # голова: круглая, повёрнута к игроку на 30°; жёлтая с чёрной маской (ярус глаз), рожки-бугорки
    # оранжевые, жвалы; единственное лицо — хитрое и довольное (глаза с прищуром, ухмылка)
    x, zc, r = segs[-1]
    hc = V((x - 0.42, -0.04, zc + 0.24))
    part(a, "Head", "Seg5", (x - 0.2, 0, zc + 0.1))
    hm = Matrix.Translation(hc) @ Matrix.Rotation(math.radians(-30), 4, "Z")
    with_matrix(a, hm)
    # 6 ярусов — голова круглая, без «цилиндра» сверху; два яруса на уровне глаз — чёрная маска-повязка вокруг
    # головы, веки цвета маски (прищур), бровей нет — эмоцию держат веки и ухмылка
    A.body(a, "cat", (0, 0, -0.4), 0.41, 0.39, 0.8, "ball", n=6, t0=0.1, t1=0.86, floor=0.42, corner=0.48,
           keys=["cat", "cat", "catD", "catD", "cat", "cat"])  # профиль срезан сверху: макушка широкая, без «шапки»
    for e in S2:
        eye2(a, (e * 0.16, -0.37, 0.02), 0.11, (e * 0.15, -1, 0.05), "sly", e, "catD", "catD", show_brow=False,
             lid=0.34, lid_tilt=12)  # веки прищурены, внутренние концы ниже — хитрый взгляд
        blunt(a, "catO", (e * 0.17, 0.02, 0.33), (e * 0.24, 0.04, 0.52), 0.13, 0.08)  # рожки-бугорки
    grin(a, (0, -0.345, -0.2), 0.24, teeth=0)
    with_matrix(a, None)
    face_point(a, tuple(hm @ V((0, -0.4, 0.0))))
    closeup(a, (0.3, -0.3, t + 0.45), eye_off=(-0.6, -2.4, 0.8))
    a.pose = {"Seg2": ((0, 10, 0), (0, 0, 0)), "Seg3": ((0, -8, 0), (0, 0, 0)), "Head": ((0, 12, -14), (0, 0, 0))}
    return a


def _section(tiers, x, z):
    """Полуширина (по y) сечения тела из ярусов A.body плоскостью x на высоте z; 0 — вне тела."""
    for za, zb, bx, by, wx, wy, cut in tiers:
        if za <= z <= zb:
            dx = abs(x - bx)
            if dx <= wx - cut:
                return wy
            return max(wy - (dx - (wx - cut)), 0.0) if dx < wx else 0.0
    return 0.0


def belt(a, key, mx, bodies, half, out):
    """Пояс-кольцо в плоскости x = mx толщиной 2·half: контур — пересечение сечений тел bodies (ярусы A.body):
    на каждой высоте — меньшее из сечений всех тел на обеих гранях пояса (x = mx ± half), ступенями, раздутое на out
    по всему периметру. Пояс нигде не выходит за силуэт более низкого тела больше чем на out — полоса окраски
    в складке, а не рамка над спиной."""
    zs = sorted({z for tiers in bodies for tr in tiers for z in tr[:2]})
    levels = []
    for z0, z1 in zip(zs, zs[1:]):
        zm = (z0 + z1) / 2
        e = min(min(_section(tiers, mx - half, zm), _section(tiers, mx + half, zm)) for tiers in bodies)
        if e <= 0.0:
            continue
        if levels and abs(levels[-1][2] - e) < 0.03 and abs(levels[-1][1] - z0) < 1e-6:
            levels[-1] = (levels[-1][0], z1, max(levels[-1][2], e))
        else:
            levels.append((z0, z1, e))
    if not levels:
        return
    right = []
    for i, (z0, z1, e) in enumerate(levels):
        right += [(z0 - (out if i == 0 else 0.0), e + out), (z1 + (out if i == len(levels) - 1 else 0.0), e + out)]
    pts = right + [(z, -y) for z, y in reversed(right)]  # точки (z, y): ось x
    a.extrude(key, pts, mx - half, mx + half, axis="x")


def wheel_monkey():
    """6. Обезьяна-колесо: хвост такой длинный, что свернулся в обруч вокруг неё — сидит в нём, как в колесе.
    Признаки: светлая маска-сердечко, большие круглые уши, длинные руки, цепкий хвост, хохолок."""
    a = new("WheelMonkey", {"mon": ("B36B3A", True), "monD": ("7E4626", False), "monL": ("F6D9B0", False),
                            "tuft": ("6A3A1E", False)})
    t = rare_stand(a, 1.6)
    R0, cz = 1.15, t + 1.2  # обруч хвоста
    part(a, "Body", "Stand", (0, 0.05, t + 0.5))
    A.body(a, "mon", (0, 0.1, t + 0.05), 0.45, 0.42, 0.85, "pear", n=4, front=("monL", 0.7, t + 0.15, t + 0.7))
    for s in S2:  # ноги упираются в обод, руки держатся за обод сбоку
        A.limb(a, "mon", [(s * 0.3, -0.1, t + 0.25), (s * 0.5, -0.35, t + 0.25), (s * 0.55, -0.3, t + 0.08)],
               [0.18, 0.16, 0.14])
        nm = "Arm" + ("L" if s > 0 else "R")
        part(a, nm, "Body", (s * 0.2, 0.08, t + 0.75))
        A.ball(a, "mon", (s * 0.26, 0.08, t + 0.76), 0.15, n=3)  # плечо входит в тело
        A.limb(a, "mon", [(s * 0.24, 0.08, t + 0.76), (s * 0.85, -0.1, t + 1.0), (s * 1.05, 0.05, cz + 0.2)],
               [0.17, 0.15, 0.14])
        A.ball(a, "monL", (s * 1.08, 0.05, cz + 0.22), 0.12, n=2)  # ладонь на ободе
    part(a, "Head", "Body", (0, 0.05, t + 0.9))
    hc = V((0, -0.02, t + 1.25))
    A.ball(a, "mon", tuple(hc), 0.4, n=3)
    a.prism("monL", S.octagon(-0.3, 0.3, hc.z - 0.28, hc.z + 0.2, 0.1), -0.42, -0.3, axis="y")  # маска
    for s in S2:
        a.prism("monL", S.octagon(-0.13, 0.13, -0.13, 0.13, 0.04), -0.08, 0.08, axis="x",
                matrix=Matrix.Translation(hc + V((s * 0.44, 0.0, 0.05))))  # ухо
        a.prism("mon", S.octagon(-0.17, 0.17, -0.17, 0.17, 0.05), -0.06, 0.04, axis="x",
                matrix=Matrix.Translation(hc + V((s * 0.49, 0.03, 0.05))))
        eye2(a, tuple(hc + V((s * 0.13, -0.43, 0.06))), 0.09, (0, -1, 0), "goofy", s, "monL", "monD")
    grin(a, tuple(hc + V((0, -0.44, -0.16))), 0.28, teeth=3)
    for k, (dx, dz) in enumerate(((-0.24, 0.5), (0.05, 0.66), (0.26, 0.48))):  # растрёпанный хохолок
        spike(a, "tuft", tuple(hc + V((-0.1 + 0.1 * k, 0.04, 0.34))), tuple(hc + V((dx, 0.12, dz))), 0.13)
    part(a, "Tail", "Body", (0, 0.4, t + 0.25))
    pts = [(0, 0.35, t + 0.25)]
    for k in range(17):  # обруч: почти полный круг вокруг, кончик закручен внутрь
        ang = math.radians(-100 + k * 21)
        pts.append((R0 * math.cos(ang), 0.4 + 0.02 * k, cz + R0 * math.sin(ang)))
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
        for k, dy in enumerate((-0.3, 0.3)):  # пальцы 2 + 2 (вперёд и назад), разной толщины — грани не совпадают
            K.KEY = "beak"
            K.taper(a, (s * 0.22, -0.05, t + 0.05 + 0.006 * k), (s * 0.24, -0.05 + dy, t + 0.04 + 0.006 * k),
                    0.09 - 0.012 * k, 0.06, 0.07 + 0.01 * k, 0.05, cut=0.2)
    part(a, "Body", "Stand", (0, 0.1, t + 0.7))
    z = t + 0.35
    A.body(a, "green", (0, 0.1, z), 0.5, 0.48, 1.0, "egg", n=4, lean=-0.1, front=("yel", 0.7, z + 0.2, z + 0.75))
    for s in S2:
        A.folded_wing(a, "green", "blue", (s * 0.46, 0.15, z + 0.85), s, 0.85, 0.45, rows=2, down=(0, 0.4, -1))
    part(a, "Tail", "Body", (0, 0.3, z + 0.3))  # ось хвоста внутри тела — сгиб не раскрывается
    for k, (dx, key) in enumerate(((-0.12, "red"), (0.0, "blue"), (0.12, "yel"))):
        A.flipper(a, key, (dx, 0.28, z + 0.3), (dx * 3, 1.5, t + 0.05), 0.18, 0.12, thick=0.06, up=(0, 0.3, 1))
    heads = ((-1, "HeadR", "red", "angry", -32), (0, "HeadM", "blue", "goofy", 0), (1, "HeadL", "yel", "surprised", 32))
    for s, nm, key, mood, turn in heads:
        base = V((s * 0.25, -0.05, z + 0.9))
        part(a, nm, "Body", tuple(base))
        hc = V((s * 0.55, -0.15, z + 1.45 + (0.15 if s == 0 else 0)))
        A.limb(a, key, [tuple(base), tuple(hc)], [0.3, 0.26], joints=False)
        with_matrix(a, tilt(hc, "Z", turn))
        A.ball(a, key, tuple(hc), 0.27, n=3)
        a.prism("face", S.octagon(-0.17, 0.17, hc.z - 0.12, hc.z + 0.12, 0.05), hc.y - 0.276, hc.y - 0.17, axis="y",
                matrix=Matrix.Translation((hc.x, 0, 0)))
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

def leaf_outline(u0, u1, n=9, wmax=0.88):
    """Контур листа (u вдоль жилки от черешка u0 к острому кончику u1, w поперёк): выпуклый, кончик острый."""
    up, lo = [], []
    for i in range(n + 1):
        f = i / n
        u = u0 + (u1 - u0) * f
        hw = wmax * (math.sin(math.pi * f) ** 0.7) * (1.12 - 0.3 * f)
        up.append((u, hw))
        if 0 < i < n:
            lo.append((u, -hw))
    return up + list(reversed(lo)), lambda f: wmax * (math.sin(math.pi * f) ** 0.7) * (1.12 - 0.3 * f)


def leaf_half(a, ml, s, u0, u1, wmax, sag, n=8, under=True):
    """Половина листа (s = ±1 — сторона от главной жилки) в осях ml (x — вдоль жилки, z — вверх): повёрнута вокруг
    жилки вниз на sag° — края провисают под тяжестью. Ступени: тёмный край, средний слой с кольцами D39, светлая
    середина, снизу у жилки — утолщение (лист толще у середины); боковые жилки утоплены. Заходит за жилку на 0.05."""
    hw = leaf_outline(u0, u1, n=n, wmax=wmax)[1]
    mh = ml @ Matrix.Rotation(math.radians(-s * sag), 4, "X")
    uc = (u0 + u1) / 2
    edge = [(u0 + (u1 - u0) * i / n, s * hw(i / n)) for i in range(n + 1)]

    def poly(ku, kw):
        pts = [(uc + (u - uc) * ku, w * kw) for u, w in edge]
        return pts + [(uc + (u1 - uc) * ku, -s * 0.05), (uc + (u0 - uc) * ku, -s * 0.05)]

    a.extrude("leafE", poly(1.0, 1.0), -0.06, 0.02, axis="z", matrix=mh)
    a.extrude("leaf", poly(0.92, 0.86), 0.0, 0.07, axis="z", matrix=mh)
    a.extrude("leafL", poly(0.72, 0.6), 0.05, 0.12, axis="z", matrix=mh)
    if under:
        a.extrude("leafE", poly(0.6, 0.42), -0.15, -0.05, axis="z", matrix=mh)  # снизу: лист толще у середины
    with_matrix(a, mh)
    for k in range(4):  # боковые жилки ёлочкой
        f = 0.2 + 0.17 * k
        u = u0 + (u1 - u0) * f
        bar(a, "leafV", (u, s * 0.04, 0.075 + 0.004 * s), (u + 0.32, s * hw(f + 0.08) * 0.7, 0.075 + 0.004 * s),
            0.06, 0.06, bevel=0)
    with_matrix(a, None)


def ant_strongman():
    """8. Муравей-силач: как штангист, выжал над головой лист в десять раз больше себя — держит его за нижний край,
    лист стоит почти торчком и перекошен по диагонали; присел на согнутых лапах (колени выше таза), руки с буграми
    бицепсов, стиснул зубы, вспотел.
    Признаки муравья: три отдела тела (голова, грудь, брюшко в кольцах), тонкая талия-стебелёк, шесть лап (четыре
    стоят в приседе, две выпрямлены вверх и держат лист), коленчатые усики с булавой, крупные светлые жвалы.
    Муравей собран в масштабе SC вокруг середины подставки — лист (≈ 3.1 вдоль, ≈ 1.7 поперёк) укладывается
    в габарит подставки и не задевает соседей в музее."""
    a = new("AntStrongman", {"ant": ("D2452B", True), "antD": ("6E2216", False), "antM": ("E8A640", False),
                             "leafE": ("3E9A45", False), "leaf": ("74CF45", True), "leafL": ("A8E86A", True),
                             "leafV": ("2F7A36", False), "sweat": ("9FE3FF", False)})
    t = epic_stand(a, 1.7)
    SC, DZ = 0.75, -0.32  # масштаб муравья и присед: всё тело ниже на DZ, стопы остаются на подставке
    sm = Matrix.Translation((0, 0, t)) @ Matrix.Scale(SC, 4) @ Matrix.Translation((0, 0, DZ - t))

    def q(p):
        return tuple(sm @ V(p))

    with_matrix(a, sm)
    part(a, "Body", "Stand", q((0, 0.2, t + 0.8)))
    # брюшко: кольца вдоль оси назад-вниз, прижато к задним лапам (не висит); приподнято над подставкой — присед
    # глубже, а брюшко не уходит в неё
    d = V((0, 0.95, -0.22)).normalized()
    mg = Matrix.Translation((0, 0.36, t + 0.76)) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    A.body(a, "ant", (0, 0, 0), 0.42, 0.38, 0.92, "egg", n=4, keys=["ant", "antD", "ant", "antD"], matrix=mg)
    A.ball(a, "antD", (0, 0.27, t + 0.74), 0.12, n=3)  # тонкая талия-стебелёк
    # грудь — широкая, как у штангиста: к ней по бокам крепятся плечи рук
    kchain(a, "ant", [(0, 0.2, t + 0.72), (0, 0.04, t + 0.94), (0, -0.05, t + 1.22)], [0.4, 0.62, 0.46],
           [0.34, 0.44, 0.34], up=(0, -1, 0))
    # четыре опорные лапы в глубоком приседе: бедро почти горизонтально наружу, колено выше таза, голень короткая и
    # толстая, круто вниз под колено, стопа вперёд; сустав-колено — свой шар n=2 (бюджет треугольников)
    for s in S2:
        for y0, yk, yf in ((-0.02, -0.18, -0.34), (0.16, 0.36, 0.56)):
            hip = (s * 0.16, y0, t + 0.86)
            knee = (s * 0.62, yk, t + 1.02)
            foot = (s * 0.8, yf, t + 0.1 - DZ)
            A.limb(a, "antD", [hip, knee, foot], [0.3, 0.26, 0.21], joints=False)
            knob(a, "antD", knee, 0.16)
            taper(a, "antD", (s * 0.8, yf, t + 0.08 - DZ), (s * 0.88, yf - 0.24 if y0 < 0 else yf + 0.2, t + 0.05 - DZ),
                  0.16, 0.11, 0.12, 0.08)
    # голова
    part(a, "Head", "Body", q((0, -0.06, t + 1.25)))
    A.body(a, "ant", (0, -0.12, t + 1.2), 0.42, 0.38, 0.76, "ball", n=4)
    for s in S2:
        eye2(a, (s * 0.17, -0.48, t + 1.66), 0.12, (s * 0.3, -1, 0.1), "angry", s, "ant", "antD")
        # жвалы: крупные светлые клещи под ртом, концы сведены к середине
        kchain(a, "antM", [(s * 0.2, -0.32, t + 1.3), (s * 0.25, -0.58, t + 1.28), (s * 0.07, -0.68, t + 1.27)],
               [0.15, 0.13, 0.09], [0.12, 0.11, 0.08], up=(0, 0, 1), cut=0.25, overlap=0.3)
        A.limb(a, "antD", [(s * 0.12, -0.3, t + 1.86), (s * 0.34, -0.44, t + 2.06), (s * 0.64, -0.74, t + 1.98)],
               [0.07, 0.06, 0.05], joints=False)  # коленчатый усик
        A.ball(a, "antD", (s * 0.65, -0.76, t + 1.96), 0.08, n=2)  # булава
    a.box("mouth", -0.18, 0.18, -0.52, -0.44, t + 1.42, t + 1.52, bevel=0)  # стиснутые зубы: тужится
    a.box("white", -0.15, 0.15, -0.535, -0.5, t + 1.445, t + 1.495, bevel=0)
    for x in (-0.075, 0.0, 0.075):
        a.box("mouth", x - 0.012, x + 0.012, -0.545, -0.53, t + 1.438, t + 1.502, bevel=0)
    A.ball(a, "sweat", (0.37, -0.3, t + 1.8), 0.07, n=2)  # капля пота
    spike(a, "sweat", (0.38, -0.3, t + 1.83), (0.42, -0.33, t + 1.98), 0.1)
    with_matrix(a, None)
    # лист: огромный (≈ 3.1 × 1.7), поднят над головой и стоит почти торчком — откинут назад на 35° от вертикали и
    # перекошен по диагонали (левый край выше): муравей выжал его, как штангу, держит за нижний край; половины
    # чуть согнуты от тяжести. Сначала лист (в мире), потом руки — ладони ровно под нижним краем.
    u0, u1, wmax, sag, tilt_x, roll = -1.45, 1.6, 0.86, 8, 55, -12
    hw = leaf_outline(u0, u1, wmax=wmax)[1]
    rot = Matrix.Rotation(math.radians(roll), 4, "Y") @ Matrix.Rotation(math.radians(tilt_x), 4, "X")
    low = Matrix.Rotation(math.radians(sag), 4, "X")  # нижняя половина (s = −1) в своих осях
    e0 = rot @ low @ V((0, -hw((0.0 - u0) / (u1 - u0)), 0))
    ml = Matrix.Translation(V((0, -0.06, t + 1.66)) - e0) @ rot
    GRIP = 0.6  # хват — шире плеч, как у штангиста
    part(a, "Leaf", "ArmL", tuple(ml @ low @ V((GRIP, -hw((GRIP - u0) / (u1 - u0)), 0))))
    for s in S2:
        leaf_half(a, ml, s, u0, u1, wmax, sag, n=6, under=False)
    a.box("leafV", u0 + 0.12, u1 - 0.2, -0.06, 0.06, 0.06, 0.16, bevel=0, matrix=ml)  # главная жилка
    taper(a, "leafV", ml @ V((u0 + 0.14, 0, -0.01)), ml @ V((u0 - 0.26, 0, -0.1)), 0.11, 0.08, cut=0.2)  # черешок
    smi = sm.inverted()
    # руки-лапы растут из боков широкой груди (ниже головы): плечо от груди наружу и вверх, локоть широко в сторону,
    # толстое предплечье вверх-внутрь к листу; на плече — бугор бицепса (2 ступени, красный на тёмной руке) вдоль
    # самой руки; крупные кулаки упираются в нижний край листа (в осях муравья)
    with_matrix(a, sm)
    for s, nm in ((1, "ArmL"), (-1, "ArmR")):
        u = s * GRIP
        palm = smi @ (ml @ low @ V((u, -hw((u - u0) / (u1 - u0)) - 0.04, -0.03)))  # кулак заходит в край
        sh = V((s * 0.2, -0.02, t + 0.96))  # плечо начинается внутри груди, ниже головы
        part(a, nm, "Body", q(tuple(sh)))
        elbow = V((s * 1.06, -0.1, t + 1.6))
        A.limb(a, "antD", [tuple(sh), tuple(elbow), tuple(palm)], [0.26, 0.27, 0.24], joints=False)
        knob(a, "antD", tuple(elbow), 0.17)
        dv = (elbow - sh).normalized()
        L = (elbow - sh).length * 0.7
        bc = sh.lerp(elbow, 0.5) + V((0, -0.04, 0)) + V((-dv.z * s, 0, abs(dv.x))).normalized() * 0.05
        mb = Matrix.Translation(bc - dv * L / 2) @ dv.to_track_quat("Z", "Y").to_matrix().to_4x4()
        A.body(a, "ant", (0, 0, 0), 0.2, 0.21, L, "ball", n=3, floor=0.5, bevel=0, matrix=mb)  # бицепс: 2 ступени
        knob(a, "antD", tuple(palm + V((0, 0, 0.02))), 0.2, n=3)  # кулак упирается в край листа
    with_matrix(a, None)
    face_point(a, q((0, -0.5, t + 1.55)))
    closeup(a, q((0.6, -0.1, t + 2.3)), eye_off=(-0.6, -2.4, 1.4))
    a.pose = {"Leaf": ((0, 8, 0), (0, 0, 0)), "Head": ((0, 0, 10), (0, 0, 0))}
    return a


def flower_jaguar():
    """9. Ягуар-клумба: вместо пятен на шкуре распустились крупные яркие цветы, а кончик хвоста зацвёл.
    Признаки: мощное кошачье тело, круглые уши, длинный хвост, «пятна»-цветы по бокам и спине, усы и розовый нос."""
    a = new("FlowerJaguar", {"jag": ("EE8A2C", True), "jagL": ("FFE6B8", False), "jagD": ("8A4A1C", False),
                             "petP": ("FF4FA3", False), "petW": ("FFFFFF", False), "petV": ("B46CFF", False),
                             "core": ("FFD23F", False), "coreD": ("FF8A3D", False), "leaf": ("3FAE4A", False)})
    t = epic_stand(a, 1.7)
    z = t + 0.85
    for i, (x, y) in enumerate(((0.32, -0.6), (-0.32, -0.6), (0.32, 0.6), (-0.32, 0.6))):
        nm = "Leg" + "FB"[i // 2] + "LR"[i % 2]
        part(a, nm, "Stand", (x, y, z - 0.1))
        A.limb(a, "jag", [(x, y, z), (x * 1.05, y + (0.08 if i >= 2 else -0.04), z - 0.45), (x, y - 0.05, t + 0.1)],
               [0.3, 0.226, 0.2])
        A.foot(a, "jag", (x, y - 0.05, t), (0, -1, 0), 0.32, 0.26, toes=3, toe_key="jagL", h=0.11, z=t)
    part(a, "Body", "Stand", (0, 0, z))
    body = [(-0.85, z - 0.05), (-0.75, z + 0.35), (0.0, z + 0.42), (0.8, z + 0.35), (0.9, z - 0.05), (0.6, z - 0.32),
            (-0.6, z - 0.32)]
    layered(a, "jag", body, [(0.3, 1, 1), (0.4, 0.9, 0.85)], (0.0, z + 0.05))
    a.extrude("jagL", [(z - 0.33, -0.55), (z - 0.2, -0.55), (z - 0.2, 0.55), (z - 0.33, 0.55)], -0.31, 0.31, axis="x")
    # цветы вместо пятен: крупные, яркие, на боках и спине (пять лепестков и серединка)
    flowers = (((0.4, -0.38, z + 0.1), (1, 0, 0), ("petP",), "core", 0),
               ((0.4, 0.4, z + 0.02), (1, 0, 0), ("petW",), "coreD", 30),
               ((-0.4, -0.36, z + 0.02), (-1, 0, 0), ("petV",), "core", 10),
               ((-0.4, 0.4, z + 0.1), (-1, 0, 0), ("petP",), "core", 40),
               ((0.1, 0.12, z + 0.42), (0, 0, 1), ("petW",), "coreD", 20),
               ((-0.12, -0.5, z + 0.39), (0, 0, 1), ("petV",), "core", 0))
    for c, n, keys, ck, spin in flowers:
        petals(a, c, 5, 0.25, 0.17, keys, ck, 0.1, normal=n, lift=14, spin=spin, bevel=0)
    part(a, "Head", "Body", (0, -0.85, z + 0.2))
    hc = V((0, -1.05, z + 0.42))
    A.ball(a, "jag", tuple(hc), 0.42, n=3, ry=0.38)
    A.snout(a, "jagL", tuple(hc + V((0, -0.3, -0.1))), (0, -1, -0.1), 0.24, 0.36, 0.3, 0.22, 0.2, nose_key="pink",
            nose=0.45, mouth=0.6)
    for s in S2:
        eye2(a, tuple(hc + V((s * 0.17, -0.36, 0.1))), 0.09, (s * 0.3, -1, 0.05), "sly", s, "jag", "jagD")
        a.prism("jag", S.octagon(-0.13, 0.13, -0.11, 0.11, 0.04), 0.0, 0.08, axis="y",
                matrix=Matrix.Translation(hc + V((s * 0.3, 0.05, 0.38))))  # круглое ухо
        a.prism("jagD", S.octagon(-0.08, 0.08, -0.07, 0.07, 0.03), -0.02, 0.0, axis="y", bevel=0,
                matrix=Matrix.Translation(hc + V((s * 0.3, 0.05, 0.38))))
        for k in range(2):  # усы
            a.box("white", s * 0.25 - 0.18, s * 0.25 + 0.18, -1.58, -1.56, hc.z - 0.18 + 0.06 * k, hc.z - 0.17 + 0.06 * k,
                  bevel=0, matrix=tilt((s * 0.25, -1.57, hc.z - 0.15), "Y", s * (8 - 16 * k)))
    petals(a, tuple(hc + V((-0.16, 0.02, 0.43))), 5, 0.15, 0.11, ("petP",), "core", 0.07, normal=(-0.3, -0.2, 1), lift=16,
           bevel=0)  # цветок за ухом
    part(a, "Tail", "Body", (0, 0.85, z + 0.1))
    kchain(a, "jag", [(0, 0.85, z + 0.1), (0, 1.35, z + 0.15), (0.2, 1.6, z + 0.65), (0.1, 1.5, z + 1.1)],
           [0.18, 0.16, 0.14, 0.12], up=(1, 0, 0))
    A.ball(a, "leaf", (0.1, 1.5, z + 1.18), 0.13, n=2)
    petals(a, (0.1, 1.5, z + 1.26), 5, 0.27, 0.18, ("petV", "petP"), "core", 0.1, normal=(0, -0.2, 1), lift=30,
           bevel=0)  # кончик хвоста зацвёл
    face_point(a, tuple(hc + V((0, -0.4, 0.05))))
    closeup(a, (0.4, 0.0, z + 0.1), eye_off=(-0.5, -2.4, 0.8))
    a.pose = {"Head": ((0, 0, 15), (0, 0, 0)), "Tail": ((0, 0, -20), (0, 0, 0)), "LegFL": ((-20, 0, 0), (0, 0, 0))}
    return a


# ══ LEGENDARY ══════════════════════════════════════════════════════════════════════════════════════════════════

def blunt(a, key, base, tip, w0, w1):
    """Тупой зубец-ресничка: усечённая четырёхгранная пирамида от base к tip (дёшево: 12 треугольников)."""
    base, tip = V(base), V(tip)
    m = Matrix.Translation(base) @ (tip - base).to_track_quat("Z", "Y").to_matrix().to_4x4()
    a.frustum(key, (-w0 / 2, w0 / 2, -w0 / 2, w0 / 2), (-w1 / 2, w1 / 2, -w1 / 2, w1 / 2), 0.0, (tip - base).length,
              bevel=0, matrix=m)


def flat_leaf(a, key, vkey, root, tip, w, thick, normal):
    """Плоский лист-шестиугольник от root к tip шириной w (плоскость поперёк normal) с жилкой — дёшево."""
    root, tip = V(root), V(tip)
    x = (tip - root).normalized()
    y = V(normal).cross(x).normalized()
    z = x.cross(y)
    m = Matrix(((x.x, y.x, z.x, root.x), (x.y, y.y, z.y, root.y), (x.z, y.z, z.z, root.z), (0, 0, 0, 1)))
    ln = (tip - root).length
    pts = [(0, -w * 0.22), (0.45 * ln, -w / 2), (0.85 * ln, -w * 0.3), (ln, 0), (0.85 * ln, w * 0.3), (0.45 * ln, w / 2),
           (0, w * 0.22)]
    a.extrude(key, pts, -thick / 2, thick / 2, axis="z", matrix=m)
    a.box(vkey, 0.04 * ln, 0.86 * ln, -0.025, 0.025, -thick / 2 - 0.018, thick / 2 + 0.018, bevel=0, matrix=m)


def valve(a, upper, m, R, hz, layers):
    """Створка ловушки в осях m (начало — петля, створка вперёд к −y): сбоку полукруг (плоская сторона — плоскость
    смыкания z = 0), спереди ступенчатая; внутри малиновая выстилка с прожилками, по краю — короткие тупые реснички."""
    sg = 1 if upper else -1
    prof = [(-R + R * math.cos(math.radians(p)), sg * R * math.sin(math.radians(p)) * hz) for p in range(0, 181, 20)]
    layered(a, "trap", prof, layers, (-R, 0.0), matrix=m)
    a.prism("maw", S.octagon(-0.81 * R, 0.81 * R, -2 * R + 0.14, -0.1, 0.28), -0.035 if upper else -0.02,
            0.02 if upper else 0.035, bevel=0, matrix=m)  # малиновая выстилка (выступает из створки)
    for x in (-0.3, 0.0, 0.3):  # прожилки
        a.box("mawD", x - 0.03, x + 0.03, -2 * R + 0.35, -0.3, -sg * 0.055, -sg * 0.03, bevel=0, matrix=m)
    n = 5 if upper else 4
    for i in range(n):  # реснички: короткие (≈ 0.1), тупые, светло-зелёные, редкие — не зубы
        ang = math.radians(-64 + 128 * (i + (0.0 if upper else 0.5)) / (n - (1 if upper else 0)))
        p = V((0.81 * R * math.sin(ang), -R - R * 0.96 * math.cos(ang), 0.0))
        d = (V((math.sin(ang), -math.cos(ang), 0)) * 0.9 + V((0, 0, 0.35 * sg))).normalized()
        blunt(a, "cilia", m @ (p - d * 0.06), m @ (p + d * (0.1 + 0.008 * (i % 2))), 0.11, 0.075)


def trap_lobe(a, m, side, ln, w, th):
    """Створка мини-ловушки на конце листа розетки (оси m: x вдоль листа, z вверх): полукруг, открыт наружу,
    снаружи тёмно-зелёный, внутри малиновый."""
    mm = m @ Matrix.Rotation(math.radians(side * 38), 4, "X")
    pts = [(0.0, 0.0), (ln * 0.15, side * w * 0.75), (ln * 0.5, side * w), (ln * 0.85, side * w * 0.75), (ln, 0.0)]
    a.extrude("trap", pts, -th, 0.0, axis="z", matrix=mm)
    a.extrude("maw", [(x * 0.84 + ln * 0.08, y * 0.8) for x, y in pts], -0.01, 0.018, axis="z", matrix=mm)


def sprout_flytrap():
    """10. Росток-мухоловка: мини-копия мамы-королевы — вырос из клубня посреди розетки листьев-ловушек, раскинул
    руки-лозы: «та-дам!». Голова — ловушка мухоловки: две короткие округлые створки на петле (снаружи тёмно-зелёные,
    внутри малиновые, язык, короткие тупые светлые реснички), глаза-бугорки на верхней створке; за головой — розовый
    венчик, как у мамы; золотая корона набекрень со светящимся малиновым самоцветом, на стебле — светящийся амулет.
    Самый крупный в коллекции.
    Признаки мухоловки: створки-ловушка с ресничками, малиновое нутро, толстый тёмный стебель, розетка листьев-ловушек
    на земле, клубень с корешками."""
    a = new("SproutFlytrap", {"trap": ("1F6634", True), "trapD": ("174A27", False), "faceL": ("C2F29A", False),
                              "maw": ("FF4F80", False), "mawD": ("C8285E", False), "cilia": ("C8F59A", False),
                              "stem": ("3B5A2B", True), "stemD": ("243D1E", False), "leafL": ("8FD957", True),
                              "leafV": ("4E9A3A", False), "vine": ("BDEB6E", True), "root": ("8F5A31", True),
                              "rootD": ("6B4224", False), "petal": ("FF8FC0", True), "petalD": ("E0569A", False),
                              "goldC": ("F5B21C", False), "goldCD": ("C27E0E", False), "halo": ("FFB8DA", False),
                              "neonGem": ("FF1A7A", False)})
    glow(a)
    t = legendary_stand(a, 1.75)
    part(a, "Body", "Stand", (0, 0, t + 0.4))
    # клубень: широкий, приплюснутый, стоит на подставке; короткие корешки-ступни прямо под ним
    A.body(a, "root", (0, 0.02, t), 0.74, 0.7, 0.56, "dome", n=3)
    for k in range(5):
        ang = math.radians(270 + 72 * k)
        dv = V((math.cos(ang), math.sin(ang), 0))
        spike(a, "rootD", V((0, 0.02, t + 0.14)) + dv * 0.55, V((0, 0.02, t + 0.07)) + dv * 0.92, 0.16)
    # розетка из пяти светлых листьев-ловушек на земле вокруг клубня (как у мамы), спереди — проход к амулету
    for k in range(5):
        ang = math.radians(306 + 72 * k)
        dv = V((math.cos(ang), math.sin(ang), 0))
        root, tip = V((0, 0, t + 0.24)) + dv * 0.4, V((0, 0, t + 0.14)) + dv * 1.26
        flat_leaf(a, "leafL", "leafV", root, tip, 0.76, 0.1, (0, 0, 1))
        x = dv
        y = V((0, 0, 1)).cross(x)
        mt = Matrix(((x.x, y.x, 0, tip.x - x.x * 0.08), (x.y, y.y, 0, tip.y - x.y * 0.08), (0, 0, 1, tip.z + 0.03),
                     (0, 0, 0, 1)))
        for sd in S2:
            trap_lobe(a, mt, sd, 0.56, 0.27 - 0.01 * (k % 2), 0.07)
    # стебель-ствол: толстый, тёмный, с узлом; на нём амулет со светящимся камнем в светлой кайме
    kchain(a, "stem", [(0, 0, t + 0.3), (0, -0.03, t + 1.2), (0, 0.03, t + 2.0)], [0.68, 0.6, 0.5], up=(0, -1, 0))
    a.prism("stemD", S.octagon(-0.37, 0.37, -0.38, 0.34, 0.11), t + 1.5, t + 1.6, bevel=0)  # узел стебля
    a.prism("goldC", S.octagon(-0.2, 0.2, t + 0.84, t + 1.22, 0.08), -0.44, -0.26, axis="y")  # амулет
    a.prism("goldCD", S.octagon(-0.23, 0.23, t + 1.22, t + 1.3, 0.03), -0.38, -0.22, axis="y", bevel=0)  # петелька
    a.prism("halo", S.octagon(-0.15, 0.15, t + 0.88, t + 1.18, 0.06), -0.48, -0.4, axis="y", bevel=0)  # ореол
    a.prism("neonGem", S.octagon(-0.1, 0.1, t + 0.93, t + 1.13, 0.045), -0.53, -0.44, axis="y", bevel=0)
    for s, nm in ((1, "ArmL"), (-1, "ArmR")):  # руки-лозы светлые на тёмном стебле, раскинуты: «та-дам!»
        part(a, nm, "Body", (s * 0.12, -0.02, t + 1.62))
        leaf_blade(a, "vine", "leafV", [(s * 0.1, -0.02, t + 1.62), (s * 0.55, -0.12, t + 1.66),
                                         (s * 1.0, -0.2, t + 1.8), (s * 1.36, -0.26, t + 2.02)],
                   [0.18, 0.44, 0.46, 0.12], 0.08, up=(0, -1, 0.25))
    # голова-ловушка: петля сзади, верхняя створка приоткрыта вверх, нижняя — вниз
    part(a, "Head", "Body", (0, 0.02, t + 2.05))
    hg = V((0, 0.22, t + 2.3))
    R = 0.72
    mu = Matrix.Translation(hg) @ Matrix.Rotation(math.radians(-20), 4, "X")
    kchain(a, "stem", [(0, 0.0, t + 1.95), (0, 0.18, t + 2.26)], [0.4, 0.3], up=(0, -1, 0))  # шея к петле
    A.ball(a, "trapD", tuple(hg), 0.26, n=3)  # петля
    lay = [(0.3, 1, 1), (0.48, 0.9, 0.85), (0.62, 0.72, 0.62)]
    valve(a, True, mu, R, 0.86, lay)
    for s in S2:  # глаза-бугорки на макушке верхней створки (светлое лицо), видны над её краем
        bc = mu @ V((s * 0.35, -0.98, 0.6))
        A.ball(a, "faceL", tuple(bc), 0.25, n=3)
        eye2(a, tuple(bc + V((s * 0.02, -0.22, 0.05))), 0.15, (s * 0.25, -1, 0.12), "proud", s, "faceL", "trapD")
    # корона набекрень между глазами: обод, пять зубцов, самоцвет спереди (в светлой кайме) и сверху светятся
    mc = mu @ Matrix.Translation((0.04, -0.9, 0.78)) @ Matrix.Rotation(math.radians(22), 4, "X") @ Matrix.Rotation(
        math.radians(-14), 4, "Y")  # корона лежит на глазах-бугорках
    a.prism("goldC", S.octagon(-0.28, 0.28, -0.26, 0.26, 0.09), 0.0, 0.26, matrix=mc)
    a.frame("goldCD", S.octagon(-0.3, 0.3, -0.28, 0.28, 0.1), 0.06, -0.01, 0.08, axis="z", bevel=0, matrix=mc)
    for i in range(5):
        th = 2 * math.pi * i / 5 - math.pi / 2
        px, py = 0.22 * math.cos(th), 0.2 * math.sin(th)
        a.frustum("goldC", (px - 0.085, px + 0.085, py - 0.065, py + 0.065), (px, px, py, py), 0.24, 0.66, bevel=0,
                  matrix=mc)
    a.prism("halo", S.octagon(-0.16, 0.16, 0.0, 0.26, 0.06), -0.3, -0.2, axis="y", bevel=0, matrix=mc)  # ореол
    a.prism("neonGem", S.octagon(-0.12, 0.12, 0.02, 0.24, 0.045), -0.35, -0.24, axis="y", bevel=0, matrix=mc)
    gem(a, "neonGem", tuple(mc @ V((0, 0, 0.38))), 0.22, turn=20)
    # розовый венчик за головой, как у мамы: диск-чашечка и плоские лепестки по кругу (снизу — стебель)
    pc = V((0, 0.36, t + 2.56))
    a.prism("petalD", S.octagon(-0.6, 0.6, pc.z - 0.6, pc.z + 0.6, 0.22), 0.3, 0.42, axis="y", bevel=0)
    n = 11
    for i in range(n):
        ang = -90 + 360 * (i + 0.5) / n
        if abs(ang + 90) < 50:
            continue
        dd = V((math.cos(math.radians(ang)), 0, math.sin(math.radians(ang))))
        pp = V((-dd.z, 0, dd.x))
        poly = [pc + dd * r + pp * w for r, w in ((0.45, -0.13), (1.0, -0.26), (1.44, -0.13), (1.44, 0.13),
                                                  (1.0, 0.26), (0.45, 0.13))]
        y0 = 0.32 + 0.014 * (i % 3)  # соседние лепестки на разной глубине — грани не совпадают
        a.extrude("petal" if i % 2 else "petalD", [(q.x, q.z) for q in poly], y0, y0 + 0.08, axis="y")
    # нижняя створка — челюсть: язык, раскрывается в позе
    part(a, "Jaw", "Head", tuple(hg))
    ml = Matrix.Translation(hg) @ Matrix.Rotation(math.radians(16), 4, "X")
    valve(a, False, ml, R, 0.7, lay)
    taper(a, "tongue", ml @ V((0, -0.3, 0.03)), ml @ V((0, -1.15, 0.08)), 0.36, 0.3, 0.1, 0.09, cut=0.3)
    face_point(a, tuple(mu @ V((0, -1.0, 0.3))))
    tg = mu @ V((0, -0.95, 0.12))
    FACE_CAM["SproutFlytrap"] = (tuple(tg + V((-1.5, -6.6, 1.2))), tuple(tg))
    closeup(a, (0.0, -0.5, t + 0.3), eye_off=(-0.9, -2.2, 0.9))
    a.pose = {"Jaw": ((18, 0, 0), (0, 0, 0)), "Head": ((-8, 0, 6), (0, 0, 0)), "ArmL": ((0, -18, 0), (0, 0, 0)),
              "ArmR": ((0, 14, 0), (0, 0, 0))}
    return a


CREATURES = [("FrogBubble", frog_bubble, "Лягушка-пузырь", "Common"),
             ("BigBeakToucan", big_beak_toucan, "Тукан-клювище", "Common"),
             ("RainbowChameleon", rainbow_chameleon, "Хамелеон-радуга", "Common"),
             ("KnotSloth", knot_sloth, "Ленивец-узел", "Common"),
             ("ManyEyeCaterpillar", many_eye_caterpillar, "Гусеница-многоглазка", "Rare"),
             ("WheelMonkey", wheel_monkey, "Обезьяна-колесо", "Rare"),
             ("ThreeHeadParrot", three_head_parrot, "Попугай-трёхглав", "Rare"),
             ("AntStrongman", ant_strongman, "Муравей-силач", "Epic"),
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
