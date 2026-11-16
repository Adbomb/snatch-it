"""Набор форм для силуэтов Короля-дракона v4: ступенчатая анатомия в духе D39 (острые рёбра, ступени), без брони.

Приёмы:
- слоёные профили: крупная масса (голова, грудь, бедро) — несколько пластин по оси x; средняя пластина несёт полный
  боковой профиль (анатомию), внешние — тот же профиль, уменьшенный к опорной точке. Спереди — ступенчатое сужение,
  сбоку — живой анатомический контур, без гладкой органики;
- звенья: шея, лапы, хвост, рога, кости крыльев — сужающиеся восьмигранные звенья вдоль изгиба (ступени на стыках);
- перепонки — плоские панели с вырезами по краю, через одну со сдвигом по толщине (ступень);
- когти и шипы — острые пирамиды.
Всё строится на art_style.Art (как Сфинкс), материал на этапе силуэтов — один нейтральный.
"""

import math
import os
import sys

import bmesh
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import art_style as S  # noqa: E402

V = Vector
KEY = "clay"


def new_art(name):
    a = S.Art(name, ring_z0=3.0)
    a.paint(KEY, "B9B2A8")
    return a


def slab(a, prof, x0, x1, matrix=None):
    """Пластина: боковой профиль prof [(y, z)…], вытянутый по x от x0 до x1."""
    a.extrude(KEY, [(z, y) for y, z in prof], min(x0, x1), max(x0, x1), axis="x", matrix=matrix)


def scaled(prof, anchor, sy, sz):
    ay, az = anchor
    return [(ay + (y - ay) * sy, az + (z - az) * sz) for y, z in prof]


def layered(a, prof, layers, anchor, xc=0.0, matrix=None):
    """Слоёная масса: layers = [(полуширина, масштаб_y, масштаб_z)…] от средней пластины к внешней."""
    for w, sy, sz in layers:
        slab(a, scaled(prof, anchor, sy, sz), xc - w, xc + w, matrix)


def taper(a, p0, p1, w0, w1, h0=None, h1=None, up=(0, 0, 1), cut=0.3, ext0=0.0, ext1=0.0):
    """Сужающееся восьмигранное звено от p0 до p1 (сечение w × h, срезанные углы cut)."""
    p0, p1 = V(p0), V(p1)
    d = p1 - p0
    f = d.normalized()
    u = V(up) - f * V(up).dot(f)
    if u.length < 1e-4:
        u = V((0, -1, 0)) - f * f.dot(V((0, -1, 0)))
    u.normalize()
    r = f.cross(u).normalized()
    h0, h1 = h0 or w0, h1 or w1

    def ring(c, w, h):
        return [c + r * x + u * y for x, y in S.octagon(-w / 2, w / 2, -h / 2, h / 2, cut * min(w, h))]

    bm = bmesh.new()
    lo = [bm.verts.new(p) for p in ring(p0 - f * ext0, w0, h0)]
    hi = [bm.verts.new(p) for p in ring(p1 + f * ext1, w1, h1)]
    bm.faces.new(lo)
    bm.faces.new(list(reversed(hi)))
    n = len(lo)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    a._add(bm, KEY, None, None)


def chain(a, pts, ws, hs=None, up=(0, 0, 1), cut=0.3, overlap=0.45):
    """Цепь звеньев по точкам pts; ws/hs — сечения в точках (len(pts)); стыки перекрываются ступенью."""
    hs = hs or ws
    P = [V(p) for p in pts]
    for i in range(len(P) - 1):
        taper(a, P[i], P[i + 1], ws[i], ws[i + 1], hs[i], hs[i + 1], up=up, cut=cut,
              ext0=ws[i] * overlap * (0 if i == 0 else 0.5), ext1=ws[i + 1] * overlap * 0.5)


def spike(a, base, tip, w):
    """Острая пирамида (коготь, шип, рог-острие) от основания base к вершине tip."""
    base, tip = V(base), V(tip)
    m = Matrix.Translation(base) @ (tip - base).to_track_quat("Z", "Y").to_matrix().to_4x4()
    a.frustum(KEY, (-w / 2, w / 2, -w / 2, w / 2), (0, 0, 0, 0), 0.0, (tip - base).length, bevel=0, matrix=m)


def spines(a, pts, sizes, up=(0, 0, 1), lean=0.35):
    """Ряд спинных шипов по точкам гребня; наклон назад вдоль цепи."""
    P = [V(p) for p in pts]
    for i, (p, s) in enumerate(zip(P, sizes)):
        nxt = P[min(i + 1, len(P) - 1)] if i < len(P) - 1 else P[i] + (P[i] - P[i - 1])
        back = (nxt - p).normalized() if (nxt - p).length > 1e-4 else V((0, 1, 0))
        spike(a, p, p + V(up) * s + back * s * lean, s * 0.55)


def head(a, origin, L, H, W, pitch=0.0, jaw=0.42, brow=0.22, snout_w=0.5):
    """Голова дракона слоёными пластинами. origin — основание черепа сзади на линии рта; морда к −y.
    L — длина, H — высота черепа над линией рта, W — полуширина скул, jaw — глубина нижней челюсти (доля H),
    brow — выступ надбровья (доля H), snout_w — ширина морды (доля W). Возвращает матрицу головы."""
    M = Matrix.Translation(origin) @ Matrix.Rotation(math.radians(-pitch), 4, "X")
    a.transform = M
    # череп + задняя часть морды (средняя пластина)
    skull = [(0.15, -0.1 * H), (0.22, 0.55 * H), (0.0, 0.95 * H), (-0.32 * L, 1.0 * H), (-0.46 * L, 0.9 * H),
             (-0.56 * L, 0.68 * H), (-0.78 * L, 0.52 * H), (-0.78 * L, 0.0), (-0.3 * L, 0.0), (-0.12 * L, -0.25 * H)]
    slab(a, skull, -snout_w * W * 1.25, snout_w * W * 1.25)
    # морда ступенью уже: от переносицы к носу
    snout = [(-0.6 * L, 0.66 * H), (-0.86 * L, 0.5 * H), (-1.0 * L, 0.44 * H), (-1.04 * L, 0.2 * H), (-1.0 * L, 0.0),
             (-0.6 * L, 0.0)]
    slab(a, snout, -snout_w * W, snout_w * W)
    tip = [(-0.86 * L, 0.48 * H), (-1.02 * L, 0.43 * H), (-1.08 * L, 0.2 * H), (-1.02 * L, 0.04 * H), (-0.86 * L, 0.06 * H)]
    slab(a, tip, -snout_w * W * 0.72, snout_w * W * 0.72)
    # скулы — самая широкая пластина, сзади
    cheek = [(0.08, -0.2 * H), (0.12, 0.62 * H), (-0.2 * L, 0.86 * H), (-0.46 * L, 0.62 * H), (-0.52 * L, 0.12 * H),
             (-0.32 * L, -0.32 * H)]
    slab(a, cheek, -W, W)
    # надбровья: козырёк над глазами, ступенью вперёд
    br = [(-0.22 * L, 0.98 * H), (-0.5 * L - brow * H, 0.86 * H), (-0.5 * L - brow * H * 0.8, 0.7 * H),
          (-0.26 * L, 0.74 * H)]
    slab(a, br, -W * 0.92, W * 0.92)
    # нижняя челюсть: мощная, ступенью уже морды
    jw = [(-0.18 * L, -0.02 * H), (-0.98 * L, -0.02 * H), (-1.0 * L, -0.14 * H), (-0.86 * L, -jaw * 0.8 * H),
          (-0.4 * L, -jaw * H), (-0.1 * L, -jaw * 0.7 * H)]
    slab(a, jw, -snout_w * W * 0.95, snout_w * W * 0.95)
    # ноздри — бугры на носу; клыки
    for s in (1, -1):
        slab(a, [(-0.94 * L, 0.42 * H), (-1.02 * L, 0.5 * H), (-1.06 * L, 0.36 * H), (-0.98 * L, 0.3 * H)],
             s * snout_w * W * 0.25, s * snout_w * W * 0.6)
        spike(a, (s * snout_w * W * 0.7, -0.9 * L, 0.04 * H), (s * snout_w * W * 0.72, -0.92 * L, -0.3 * H), 0.16 * H)
        spike(a, (s * snout_w * W * 0.7, -0.62 * L, 0.04 * H), (s * snout_w * W * 0.72, -0.63 * L, -0.2 * H), 0.12 * H)
        # глаз: миндалина под надбровьем, внешний угол выше — уверенный взгляд
        e = [(-0.36 * L, 0.66 * H), (-0.48 * L, 0.72 * H), (-0.5 * L, 0.6 * H), (-0.38 * L, 0.54 * H)]
        slab(a, e, s * W * 0.84, s * W * 0.96)
    return M


def wing(a, root, s, local, sweep, lean=0.0, tilt=0.0, bone=(0.36, 0.26, 0.15), offset=0.05):
    """Крыло в своей плоскости (u — наружу, v — вверх): local = {"E","W","F":[…],"T"}; корень root.
    sweep — отвод назад (градусы вокруг z), lean — наклон плоскости назад (вокруг u), tilt — подъём."""
    M = (Matrix.Translation(root) @ Matrix.Rotation(math.radians(s * sweep), 4, "Z")
         @ Matrix.Rotation(math.radians(-s * tilt), 4, "Y") @ Matrix.Rotation(math.radians(lean), 4, "X")
         @ Matrix.Scale(s, 4, V((1, 0, 0))))
    E, W, T = V(local["E"]), V(local["W"]), V(local["T"])
    F = [V(f) for f in local["F"]]

    def P(v):
        return M @ V((v.x, 0.0, v.y))

    def notch(p, q, k=0.3):
        mid = (p + q) / 2
        return mid + (W - mid) * k

    a.transform = None
    for i, (p, q) in enumerate(zip(F, F[1:])):
        dy = offset * (i % 2)
        a.extrude(KEY, [tuple(W), tuple(p), tuple(notch(p, q)), tuple(q)], -0.05 + dy, 0.05 + dy, axis="y", matrix=M)
    a.extrude(KEY, [tuple(W), tuple(F[-1]), tuple(notch(F[-1], T, 0.25)), tuple(T), (0.0, 0.0), tuple(E)], -0.05, 0.05,
              axis="y", matrix=M)
    chain(a, [P(V((0, 0))), P(E), P(W)], [bone[0], bone[0] * 0.85, bone[1]], up=(0, 0, 1))
    for f in F:
        chain(a, [P(W), P(f)], [bone[1] * 0.85, bone[2] * 0.5], up=(0, 0, 1), overlap=0.2)
        spike(a, P(f), P(f) + (P(f) - P(W)).normalized() * 0.45, bone[2] * 0.6)
    spike(a, P(W), P(W) + (M.to_3x3() @ V((0.1, 0.0, 1.0))).normalized() * 0.7, bone[1] * 0.8)
    return M


def claws(a, front, s_x, n, spread, size, down=0.15):
    """n когтей из передней кромки лапы front (x, y, z), вперёд-вниз."""
    fx, fy, fz = front
    for k in range(n):
        x = fx + (k - (n - 1) / 2) * spread
        spike(a, (x, fy + 0.05, fz), (x, fy - size, fz - down), size * 0.55)
