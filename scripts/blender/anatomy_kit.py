"""Набор анатомии существ (D64 «Анатомия», 2026-11-24): объёмные тела и конечности вместо ящиков и плоских досок.

- body — тело-яйцо, бочка, капля, груша, шар: ярусы-«бочонки» с фаской вдоль оси (лофт ступенями, как у дракона),
  каждый ярус — усечённая призма между двумя кольцами профиля, поэтому силуэт идёт по кривой, а шов яруса виден
  тонкой ступенью; сужение к плечам и лапам задаёт профиль.
- limb — конечность из сужающихся звеньев с шарами-суставами в изгибах (части заходят друг в друга);
  flipper — ласт или лапа-лопасть с изгибом и толщиной; foot — стопа с пальцами; folded_wing — сложенное крыло
  с перьями ступенями.
- eye — глаз (белок + зрачок + два блика) по нормали поверхности, утоплен в голову на sink (≥ 0.05); closed=True —
  закрытый глаз для сна (веко и полоска ресниц); snout — морда вперёд с носом и ртом; beak — клюв из двух половин;
  facial_disc — лицевой диск совы («сердце» вокруг глаз).
Все детали — выпуклые куски Art (art_style.py): грани внутри других деталей убирает конвейер (drop_enclosed).
Подключается из коллекций: import anatomy_kit as A; A.body(a, "navy", (0, 0, z), 1.2, 1.0, 2.4, "egg").
Зависит от art_style.py (Art, фаска), dragon10/v4_kit.py (звенья-цепи).
"""

import math
import os
import sys

import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "dragon10"))
import art_style as S  # noqa: E402
import v4_kit as K  # noqa: E402

V = Vector
TIER_BEVEL = S.BEVEL  # фаска яруса — как у всех деталей D39 (0.012): шов читается ступенью, силуэт — кривой
SINK = 0.06  # глаза и морды заходят в голову не меньше чем на 0.05 (правило D64)


# ---------------------------------------------------------------- профили тел (t — 0 низ … 1 верх → доля радиуса)
def _bulge(t, mid, half):
    u = (t - mid) / half
    return math.sqrt(max(1.0 - u * u, 0.0))


PROFILES = {
    "ball": lambda t: _bulge(t, 0.5, 0.5),
    "egg": lambda t: _bulge(t, 0.42, 0.42 if t < 0.42 else 0.58),  # шире внизу, сужение к плечам
    "barrel": lambda t: 0.72 + 0.28 * math.sin(math.pi * t),  # бока выпуклые, верх и низ широкие
    "drop": lambda t: _bulge(t, 0.3, 0.3) if t < 0.3 else ((1.0 - t) / 0.7) ** 0.85,  # капля, кончик вверху
    "pear": lambda t: max(_bulge(t, 0.32, 0.34), 0.62 * _bulge(t, 0.76, 0.26)),  # груша: низ большой, верх малый
    "dome": lambda t: math.sqrt(max(1.0 - t * t, 0.0)),  # купол: широкое основание, кругло кверху
}


def ring(rx, ry, sides=8, phase=None):
    """Кольцо-эллипс из sides точек (правильный восьмиугольник при rx = ry)."""
    phase = math.pi / sides if phase is None else phase
    return [(rx * math.cos(phase + 2 * math.pi * i / sides), ry * math.sin(phase + 2 * math.pi * i / sides))
            for i in range(sides)]


def tier(a, key, lo, z0, hi, z1, bevel=TIER_BEVEL, matrix=None):
    """Ярус: выпуклая усечённая призма между кольцами lo (на z0) и hi (на z1) с одинаковым числом точек."""
    bm = bmesh.new()
    vl = [bm.verts.new((x, y, z0)) for x, y in lo]
    vh = [bm.verts.new((x, y, z1)) for x, y in hi]
    bm.faces.new(vl)
    bm.faces.new(list(reversed(vh)))
    for i in range(len(vl)):
        j = (i + 1) % len(vl)
        bm.faces.new((vl[i], vl[j], vh[j], vh[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    planes = S._convex_planes(bm)
    S._bevel(bm, bevel)
    a._add(bm, key, planes, matrix)


_N = [0]


def _count():
    _N[0] += 1
    return _N[0]


def body(a, key, base, rx, ry, h, shape="egg", n=8, t0=0.0, t1=1.0, lean=0.0, sides=8, floor=0.25, bevel=TIER_BEVEL,
         matrix=None, keys=None):
    """Объёмное тело: n ярусов вдоль оси z от base (середина низа) высотой h; радиусы rx, ry × профиль shape.
    t0/t1 — срез профиля снизу/сверху (опора на землю — плоский низ); lean — сдвиг по y к верху (грудь вперёд < 0);
    floor — наименьшая доля радиуса (верх и низ не схлопываются в иглу); keys — свои цвета по ярусам снизу вверх
    (полосы, живот); matrix — поворот всего тела (лежащее тело, наклон)."""
    prof = PROFILES[shape] if isinstance(shape, str) else shape
    bx, by, bz = base
    ts = [t0 + (t1 - t0) * k / n for k in range(n + 1)]
    for k in range(n):
        ta, tb = ts[k], ts[k + 1]
        ra, rb = max(prof(ta), floor), max(prof(tb), floor)
        rmin = min(rx, ry) * min(ra, rb)
        q = 1.0 - min(0.02, 0.012 / max(rmin, 1e-3)) * (k % 2)  # соседние ярусы чуть разной ширины на стыке (грани
        # не совпадают); множитель, а не вычитание: кольца яруса подобны, боковые грани плоские
        za, zb = bz + h * (ta - t0) / (t1 - t0), bz + h * (tb - t0) / (t1 - t0)
        ya, yb = by + lean * (ta - t0) / (t1 - t0), by + lean * (tb - t0) / (t1 - t0)
        lo = [(bx + x, ya + y) for x, y in ring(rx * ra * q, ry * ra * q, sides)]
        hi = [(bx + x, yb + y) for x, y in ring(rx * rb * q, ry * rb * q, sides)]
        ov = 0.01 if k else -(0.004 + 0.0017 * (_count() % 12))  # ярусы заходят друг в друга; низ над опорой (у разных
        # тел на разной высоте — нижние грани не совпадают)
        # мелкие тела без фаски (треугольники); фаска не больше трети самого узкого кольца — иначе грани выворачиваются
        bv = min(bevel, h / n / 3, rmin * 0.3) if min(rx, ry) >= 0.3 else 0.0
        tier(a, keys[k % len(keys)] if keys else key, lo, za - ov, hi, zb + 0.01, bevel=bv, matrix=matrix)


def ball(a, key, c, r, n=4, ry=None, rz=None, matrix=None):
    """Шар-сустав или голова: body формы ball вокруг центра c."""
    rz = rz or r
    body(a, key, (c[0], c[1], c[2] - rz), r, ry or r, 2 * rz, "ball", n=n, floor=0.35, matrix=matrix)


# ---------------------------------------------------------------- конечности
def limb(a, key, pts, ws, hs=None, up=(0, -1, 0), joint_key=None, joints=True):
    """Конечность по точкам pts (плечо → локоть → запястье …) сужающимися звеньями; в каждом изгибе шар-сустав
    чуть толще звеньев — части заходят друг в друга, сгиб не раскрывается."""
    hs = hs or ws
    K.KEY = key
    K.chain(a, pts, ws, hs, up=up, cut=0.42, overlap=0.5)
    if joints:
        for i in range(1, len(pts) - 1):
            r = max(ws[i], hs[i]) * 0.56
            ball(a, joint_key or key, pts[i], r, n=3)


def flipper(a, key, root, tip, w0, w1, thick=0.16, bend=(0, 0, 0), up=(0, 0, 1), segments=3):
    """Ласт или лапа-лопасть: от root к tip сужается w0 → w1, толщина thick → thick·0.5, изгиб bend (смещение
    середины); плоскость лопасти поперёк up. Корень заходит в тело на половину ширины."""
    p0, p1, b = V(root), V(tip), V(bend)
    pts, ws, hs = [], [], []
    for k in range(segments + 1):
        t = k / segments
        pts.append(tuple(p0.lerp(p1, t) + b * (4 * t * (1 - t))))
        ws.append(w0 + (w1 - w0) * t ** 0.8)
        hs.append(thick * (1.0 - 0.5 * t))
    K.KEY = key
    K.chain(a, pts, ws, hs, up=up, cut=0.45, overlap=0.5)


def foot(a, key, ankle, forward, length, width, toes=3, toe_key=None, h=0.14, z=None):
    """Стопа: подушка от пятки (под щиколоткой) вперёд на length и пальцы-капли; forward — направление в плоскости."""
    f = V(forward).normalized()
    side = V((-f.y, f.x, 0))
    an = V(ankle)
    gz = an.z if z is None else z
    heel = V((an.x, an.y, gz + h / 2)) - f * width * 0.2
    toe = heel + f * length * 0.78
    K.KEY = key
    K.taper(a, heel, toe, width * 0.8, width, h, h * 0.85, up=(0, 0, 1), cut=0.4)
    K.KEY = toe_key or key
    tw = width / toes * 0.85
    for i in range(toes):
        o = (i - (toes - 1) / 2) * width / toes
        b = toe + side * o - f * 0.04
        K.taper(a, b, b + f * length * (0.26 if i in (0, toes - 1) else 0.32) - V((0, 0, h * 0.12)), tw, tw * 0.55,
                h * 0.8, h * 0.45, up=(0, 0, 1), cut=0.45)


def folded_wing(a, key, tip_key, shoulder, side, length, width, rows=3, down=(0, 0.35, -1), thick=0.12):
    """Сложенное крыло вдоль бока: rows рядов перьев ступенями (верхний — короткий кроющий, нижний — длинные
    маховые), каждый ряд чуть дальше от тела; концы перьев — tip_key. side = ±1 (x)."""
    sh = V(shoulder)
    d = V(down).normalized()
    out = V((side, 0, 0))
    for r in range(rows):
        t = (r + 1) / rows
        ln = length * (0.45 + 0.55 * t)
        w = width * (1.0 - 0.18 * r)
        p0 = sh + out * (0.03 + 0.045 * r) + d * (length * 0.12 * r)
        p1 = p0 + d * ln * 0.72
        p2 = p0 + d * ln + out * 0.02
        K.KEY = key if r < rows - 1 else tip_key
        K.chain(a, [p0, p1, p2], [w, w * 0.8, w * 0.28], [thick, thick * 0.9, thick * 0.6], up=out, cut=0.45,
                overlap=0.4)


# ---------------------------------------------------------------- лицо
def facing(normal, up=(0, 0, 1)):
    """Поворот: ось −y детали смотрит по normal, z — как можно ближе к up."""
    n = V(normal).normalized()
    m = (-n).to_track_quat("Y", "Z").to_matrix().to_4x4()
    return m


def _at(c, normal):
    return Matrix.Translation(V(c)) @ facing(normal)


def eye(a, c, r, normal=(0, -1, 0), look=(0.0, 0.0), pupil=0.58, sink=SINK, lift=0.04, closed=False,
        lid_key="dark", skin_key=None, sides=8):
    """Глаз на поверхности головы в точке c, смотрит по normal: белок выступает на lift и уходит внутрь на sink,
    зрачок со смещением look, два блика. closed — закрытый глаз: веко цвета skin_key и тёмная полоса ресниц."""
    m = _at(c, normal)
    if closed:
        a.prism(skin_key or lid_key, ring(r * 1.02, r * 0.9, sides), -lift * 0.7, sink, axis="y", bevel=0.01,
                matrix=m)
        a.box(lid_key, -r * 0.95, r * 0.95, -lift * 0.7 - 0.03, -lift * 0.7 + 0.01, -r * 0.16, r * 0.02, bevel=0,
              matrix=m)
        return
    a.prism("white", ring(r, r, sides), -lift, sink, axis="y", bevel=0.01 if r >= 0.12 else 0.0, matrix=m)
    pr = r * pupil
    px, pz = look[0] * (r - pr) * 0.8, look[1] * (r - pr) * 0.8
    a.prism("dark", [(px + x, pz + y) for x, y in ring(pr, pr, sides)], -lift - 0.025, -lift + 0.01, axis="y", bevel=0,
            matrix=m)
    g = pr * 0.4
    a.box("glint", px - pr * 0.55, px - pr * 0.55 + g, -lift - 0.045, -lift - 0.02, pz + pr * 0.12,
          pz + pr * 0.12 + g, bevel=0, matrix=m)
    g2 = pr * 0.18
    a.box("glint", px + pr * 0.3, px + pr * 0.3 + g2, -lift - 0.045, -lift - 0.02, pz - pr * 0.5, pz - pr * 0.5 + g2,
          bevel=0, matrix=m)


def snout(a, key, base, direction, length, w0, w1, h0=None, h1=None, nose_key="dark", nose=0.3, mouth_key="mouth",
          mouth=0.7):
    """Морда: сужающийся выступ от base (внутри головы на SINK) по direction на length; на конце нос (доля nose
    от ширины конца), снизу полоса рта (доля mouth от длины, 0 — без рта)."""
    b, d = V(base), V(direction).normalized()
    h0, h1 = h0 or w0 * 0.85, h1 or w1 * 0.85
    tip = b + d * length
    K.KEY = key
    K.taper(a, b - d * SINK, tip, w0, w1, h0, h1, up=(0, 0, 1), cut=0.42)
    if nose:
        ball(a, nose_key, tuple(tip + V((0, 0, h1 * 0.3)) - d * 0.02), w1 * nose + 0.02, n=2, rz=h1 * 0.28)
    if mouth:
        side = d.cross(V((0, 0, 1))).normalized()
        m0 = tip - d * length * mouth - V((0, 0, h1 * 0.42))
        m1 = tip - d * 0.03 - V((0, 0, h1 * 0.42))
        for s in (1, -1):
            K.KEY = mouth_key
            K.taper(a, m0 + side * s * w0 * 0.36, m1 + side * s * w1 * 0.1, 0.05, 0.045, 0.05, 0.045, cut=0.3)


def beak(a, key, base, direction, length, w, h=None, key_low=None, gape=0.0):
    """Клюв: верхняя половина — к острию и чуть вниз, нижняя — короче; gape — щель (открыт)."""
    b, d = V(base), V(direction).normalized()
    h = h or w * 0.8
    up = V((0, 0, 1))
    K.KEY = key
    K.taper(a, b - d * SINK + up * h * 0.18, b + d * length - up * h * 0.25, w, w * 0.1, h * 0.6, h * 0.1, cut=0.42)
    K.KEY = key_low or key
    K.taper(a, b - d * SINK - up * (h * 0.22 + gape), b + d * length * 0.62 - up * (h * 0.32 + gape), w * 0.85,
            w * 0.12, h * 0.42, h * 0.1, cut=0.42)


def facial_disc(a, key, rim_key, c, r, normal=(0, -1, 0), gap=0.55):
    """Лицевой диск совы: два круга вокруг глаз (сердце), светлее перьев; тёмная кайма позади. c — середина лица."""
    m = _at(c, normal)
    for s in (1, -1):
        a.prism(rim_key, [(s * r * gap + x, y) for x, y in ring(r * 1.08, r * 1.12, 10)], 0.0, SINK + 0.02, axis="y",
                bevel=0.01, matrix=m)
        a.prism(key, [(s * r * gap + x, 0.04 + y) for x, y in ring(r, r * 1.02, 10)], -0.04, SINK, axis="y",
                bevel=0.01, matrix=m)


def eye_points(c, r, normal, spread, up=0.0):
    """Точки двух глаз на сфере головы (центр c, радиус r), смотрящих по normal: разведены на spread градусов."""
    n = V(normal).normalized()
    out = []
    for s in (1, -1):
        q = Matrix.Rotation(math.radians(s * spread), 3, "Z") @ n
        q = (q + V((0, 0, up))).normalized()
        out.append((tuple(V(c) + q * r), tuple(q)))
    return out
