"""Набор коллекции джунглей босса 6 (производство, шаг 2 D64): палитра, свечение neon*, ступенчатые формы D39,
глаза и лица, листья, створки. Перенесено из концепта scripts/blender/boss6/creatures.py (v2, утверждён 2026-11-25)
без изменений поведения; подставки — creature_kit (D71: цвет редкости из UITokens).
Зависит от creature_kit.py, anatomy_kit.py, art_style.py, dragon10/v4_kit.py.
"""

import math
import os
import re
import sys

from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)  # scripts/blender
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


def snake(item_id):
    """RainbowChameleon → rainbow_chameleon (имя модуля существа)."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", item_id).lower()


def collect(order, own):
    """Список ITEMS в порядке каталога: свои функции модуля редкости (own) и модули новых существ jungle/<snake>.py
    (в каждом — ITEM = (id, функция, имя, редкость)). Модуль с ошибкой пропускается с пометкой SKIP — сборка других
    существ не ломается; если такое существо запрошено явно, конвейер его просто не найдёт (видно в CREATURES_OK)."""
    import importlib
    by_id = {x[0]: x for x in own}
    out = []
    for item_id in order:
        if item_id in by_id:
            out.append(by_id[item_id])
            continue
        try:
            mod = importlib.import_module(snake(item_id))
            out.append(mod.ITEM)
        except ModuleNotFoundError as e:
            if e.name != snake(item_id):
                print(f"SKIP {item_id}: {e!r}", flush=True)
        except Exception as e:  # noqa: BLE001 — чужой незаконченный модуль не должен ронять сборку
            print(f"SKIP {item_id}: {e!r}", flush=True)
    return out
