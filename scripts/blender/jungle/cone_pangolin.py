"""Панголин-шишка (ConePangolin, Rare, №21 каталога docs/BOSS6_CATALOG.md) — стоит столбиком на задних лапах
и опирается на широкий хвост, а каждая чешуйка у него размером с голову: ходячая бронзовая шишка.
Силуэт — конус-шишка: широкий низ (≤ 2.6), ровное сужение к маленькой голове, высота ≈ 4.
Признаки вида: крупная чешуя черепицей (6 рядов, каждый заходит на нижний на треть, кончики вниз) от макушки до
кончика хвоста; маленькая конусная голова с вытянутой мордочкой; ходит на задних лапах; широкий хвост-подпорка
(третья опора за пятками); длинные загнутые когти на передних лапах.
Эмоция — застенчивость: прикрыл мордочку лапками с боков и подглядывает поверх них из-под полуопущенных век,
брови домиком, румянец на щеках.
Цвета: чешуя — бронзовая середина D9822B, медная кайма снизу и по бокам A84E24, светлый блик по верхнему краю;
мордочка, брюшко и ладошки розовые; когти — тёмный рог 5A3A28; зелёного нет.
Зависит от jungle_kit.py (creature_kit, anatomy_kit, art_style, v4_kit).
"""

import math
import os
import sys

from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jungle_kit import *  # noqa: E402,F401,F403

_TURN = [0]


def _scale(a, root, n, d, w, h, lean, th=0.12, hi=True):
    """Чешуйка-щиток (пятиугольник кончиком вниз) шириной w и длиной h от корня root к кончику по направлению d
    (вдоль поверхности), нормаль поверхности n; кончик отогнут наружу на lean°. Внутренняя грань щита проходит на 0.03
    глубже root. Медный щит — кайма; бронзовая середина сдвинута к корню (медь видна снизу и по бокам) и выступает на
    0.03; hi — светлый блик-полоска по верхнему краю середины."""
    n = V(n).normalized()
    d = V(d)
    d = (d - n * d.dot(n)).normalized()
    tr = math.radians(lean)
    dt = d * math.cos(tr) + n * math.sin(tr)  # к кончику и наружу
    yl = n * math.cos(tr) - d * math.sin(tr)
    zl = -dt
    xl = yl.cross(zl)
    r = V(root)
    m = Matrix(((xl.x, yl.x, zl.x, r.x), (xl.y, yl.y, zl.y, r.y), (xl.z, yl.z, zl.z, r.z), (0, 0, 0, 1)))
    _TURN[0] += 1
    e = 0.006 * (_TURN[0] % 3)  # у соседних чешуек своя толщина — грани не совпадают
    pts = [(-0.5 * w, 0.0), (0.5 * w, 0.0), (0.5 * w, -0.5 * h), (0.0, -h), (-0.5 * w, -0.5 * h)]
    a.extrude("copper", pts, -0.03, th + e, axis="y", matrix=m)
    inner = [(u * 0.72, v * 0.74 - 0.01 * h) for u, v in pts]
    a.extrude("bronze", inner, th * 0.5, th + e + 0.03, axis="y", matrix=m)
    if hi:  # блик: полоска 0.07 вдоль верхнего края середины, чуть выше её
        a.box("shine", -0.33 * w, 0.33 * w, th * 0.6, th + e + 0.045, -0.1 * h - 0.075, -0.1 * h, bevel=0, matrix=m)


def _ray(tier, phi):
    """Расстояние от оси яруса A.body до его стенки по горизонтальному лучу под углом phi (градусы, 0 — +x)."""
    za, zb, bx, by, wx, wy, cut = tier
    pts = S.octagon(bx - wx, bx + wx, by - wy, by + wy, cut)
    dx, dy = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    best = 0.0
    for i in range(len(pts)):
        (px, py), (qx, qy) = pts[i], pts[(i + 1) % len(pts)]
        ex, ey = qx - px, qy - py
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        ox, oy = px - bx, py - by
        tt = (ox * ey - oy * ex) / den
        u = (ox * dy - oy * dx) / den
        if -1e-6 <= u <= 1 + 1e-6 and tt > best:
            best = tt
    return best


def _tier(tiers, z):
    return min(tiers, key=lambda tr: 0 if tr[0] <= z <= tr[1] else min(abs(z - tr[0]), abs(z - tr[1])))


def _scale_rows(a, tb, t, rows, lean_add):
    """Чешуя черепицей по ярусам тела tb: ряды (высота корня над t, число, длина, шаг по кругу °); ширина — по шагу
    с запасом на перекрытие соседей; ряды с чётным и нечётным числом чередуются — чешуя сидит в шахматном порядке, как
    у шишки. Корень утоплен в тело на 0.1; наклон — по склону конуса плюс отгиб."""
    for zr, cnt, h, step in rows:
        for i in range(cnt):
            phi = 90 + (i - (cnt - 1) / 2) * step
            zroot, ztip = t + zr, t + zr - h * 0.9
            tr0, tr1 = _tier(tb, zroot), _tier(tb, ztip)
            r0, r1 = _ray(tr0, phi), _ray(tr1, phi)
            lean = max(math.degrees(math.atan2(r1 - r0, h)), 0.0) + lean_add
            w = r0 * math.radians(step) * 1.32
            c, s = math.cos(math.radians(phi)), math.sin(math.radians(phi))
            root = V((tr0[2] + c * (r0 - 0.1), tr0[3] + s * (r0 - 0.1), zroot))
            _scale(a, root, (c, s, 0), (0, 0, -1), w, h, lean)


def cone_pangolin():
    a = new("ConePangolin", {"copper": ("A84E24", True), "bronze": ("D9822B", True), "shine": ("F6BE78", False),
                             "skinP": ("FFB3C4", True), "nose": ("E0607F", False), "blushR": ("FF7FA0", False),
                             "claw": ("5A3A28", False)})
    t = rare_stand(a, 1.55)
    yb = -0.08  # ось тела чуть впереди центра подставки: сзади — хвост-подпорка

    # ── тело-шишка: стоит столбиком; шире всего внизу и ровно сужается к голове; розовое брюшко спереди
    part(a, "Body", "Stand", (0, yb, t + 0.7))
    z0, hb = t + 0.4, 2.72

    def cone(u):
        return 1.0 - 0.56 * u

    tb = A.body(a, "copper", (0, yb, z0), 0.86, 0.76, hb, cone, n=6, lean=-0.03, bevel=0, floor=0.4,
                front=("skinP", 0.46, z0 + 0.04, z0 + hb - 0.5))
    # шесть рядов чешуи (каждая — с голову) от шеи вниз; шаг рядов 0.43 = 0.7 длины — перекрытие на треть;
    # нижний кончик на 0.45 над подставкой — лапы видны; спереди открыто брюшко
    _scale_rows(a, tb, t, ((0.98, 6, 0.62, 52), (1.41, 7, 0.62, 42), (1.84, 6, 0.6, 48), (2.27, 7, 0.58, 38),
                           (2.68, 6, 0.56, 40), (3.06, 3, 0.52, 66)), 14)

    # ── задние лапы: короткие и толстые, прямо под телом; розовая стопа с тёмными когтями вперёд
    for s in S2:
        nm = "Leg" + ("L" if s > 0 else "R")
        part(a, nm, "Body", (s * 0.36, yb, z0 + 0.15))
        kchain(a, "copper", [(s * 0.36, yb, z0 + 0.35), (s * 0.42, yb - 0.08, t + 0.3), (s * 0.42, yb - 0.08, t + 0.1)],
               [0.38, 0.34, 0.3], up=(0, -1, 0), overlap=0.6)
        A.foot(a, "skinP", (s * 0.42, yb - 0.1, t), (s * 0.12, -1, 0), 0.46, 0.32, toes=3, toe_key="claw", h=0.13,
               z=t)

    # ── хвост-подпорка: широкий, от низа спины вниз-назад под 35–40° к подставке; кончик упирается в неё за пятками
    # (третья опора); сверху — та же чешуя черепицей, кончиками к кончику хвоста
    part(a, "Tail", "Body", (0, yb + 0.5, t + 1.0))
    tail = [V((0, yb + 0.3, t + 1.22)), V((0, yb + 0.9, t + 0.66)), V((0, yb + 1.5, t + 0.17))]
    tw = [1.0, 0.86, 0.58]
    thk = [0.46, 0.36, 0.24]
    kchain(a, "copper", tail, tw, thk, up=(0, 0, 1), overlap=0.3)
    for f, xs, wf, hh in ((0.3, (-0.2, 0.2), 0.6, 0.5), (0.58, (0.0,), 0.92, 0.5), (0.84, (0.0,), 0.86, 0.4)):
        seg = f * (len(tail) - 1)
        i = min(int(seg), len(tail) - 2)
        u = seg - i
        c = tail[i].lerp(tail[i + 1], u)
        dv = (tail[i + 1] - tail[i]).normalized()
        side = dv.cross(V((0, 0, 1))).normalized()
        up = side.cross(dv).normalized()
        if up.z < 0:
            up = -up
        th = thk[i] + (thk[i + 1] - thk[i]) * u
        wd = tw[i] + (tw[i + 1] - tw[i]) * u
        for x in xs:
            _scale(a, c + up * (th * 0.5 - 0.1) + side * x - dv * 0.08, up, dv, wd * wf, hh, 10)

    # ── голова: маленький бронзовый конус от затылка (0.9) к основанию мордочки (0.45), из него вперёд-вниз —
    # вытянутая розовая мордочка; на темени и затылке — три чешуйки, они переходят в верхние ряды спины
    hz = t + 3.36  # уровень оси головы
    part(a, "Head", "Body", (0, yb + 0.05, t + 3.08))
    # череп-конус: сверху линия спускается от затылка к мордочке — в профиль голова клином, а не коробкой
    taper(a, "copper", (0, yb + 0.36, hz + 0.02), (0, yb - 0.22, hz - 0.02), 0.9, 0.5, 0.84, 0.58, up=(0, 0, 1))
    sn = [V((0, yb - 0.16, hz - 0.12)), V((0, yb - 0.5, hz - 0.2)), V((0, yb - 0.8, hz - 0.3))]
    kchain(a, "skinP", sn, [0.36, 0.28, 0.2], [0.32, 0.26, 0.18], up=(0, 0, 1), overlap=0.3)
    a.box("nose", -0.085, 0.085, yb - 0.91, yb - 0.82, hz - 0.38, hz - 0.24, bevel=0)  # кончик носа
    ez = hz + 0.1
    for s in S2:  # глаза: полуопущенные веки, брови домиком, взгляд вбок — подглядывает на игрока поверх лапок
        eye2(a, (s * 0.23, yb - 0.2, ez), 0.14, (s * 0.5, -1, 0.15), "worried", s, "copper", "dark",
             look=(-0.6, 0.4), lid=0.37, brow_lift=0.2)
        cm = Matrix.Translation(V((s * 0.27, yb - 0.1, hz - 0.17))) @ A.facing((s * 1.0, -0.8, 0))
        a.box("blushR", -0.125, 0.125, -0.025, 0.06, -0.06, 0.06, bevel=0, matrix=cm)  # румянец-пятно на щеке
    # темя: чешуйка лежит по склону черепа, кончиком к затылку; затылок: две чешуйки ложатся на верхний ряд спины
    _scale(a, V((0, yb - 0.1, hz + 0.24)), (0, -0.28, 0.96), (0, 1, 0.29), 0.5, 0.46, 3)
    for s in S2:
        _scale(a, V((s * 0.2, yb + 0.12, hz + 0.32)), (s * 0.35, 0.75, 0.55), (0, 0.3, -1), 0.52, 0.5, 2)

    # ── передние лапы: поднялись к мордочке и обхватили её с боков (между лапами — щель, видны нос и мордочка);
    # по три длинных когтя-крючка вперёд и вниз
    for s in S2:
        nm = "Arm" + ("L" if s > 0 else "R")
        sh = V((s * 0.46, yb - 0.22, t + 2.62))
        el = V((s * 0.5, yb - 0.68, t + 2.52))
        wrist = V((s * 0.3, yb - 0.56, hz - 0.2))
        part(a, nm, "Body", tuple(sh))
        knob(a, "copper", tuple(sh), 0.17)  # плечо входит в тело
        kchain(a, "bronze", [sh, el, wrist], [0.26, 0.24, 0.2], up=(0, -1, 0), overlap=0.6)
        knob(a, "skinP", tuple(wrist + V((-s * 0.02, -0.04, 0.0))), 0.115)  # ладошка на боку мордочки
        for k, dz in enumerate((0.04, -0.06, -0.16)):
            b = wrist + V((-s * 0.05, -0.12, dz))
            mid = b + V((-s * 0.04, -0.2, 0.03 - 0.02 * k))
            tip = mid + V((-s * 0.01, -0.07, -0.16))
            blunt(a, "claw", b, mid, 0.1, 0.085)
            blunt(a, "claw", mid - (mid - b).normalized() * 0.03, tip, 0.085, 0.07)

    face_point(a, (0, yb - 0.5, hz + 0.02))
    closeup(a, (0.0, yb - 0.2, t + 2.2), eye_off=(-1.6, -3.4, 1.0))
    a.pose = {"Head": ((10, 0, -16), (0, 0, 0)), "ArmL": ((-24, 0, 0), (0, 0, 0)), "Tail": ((0, 0, 12), (0, 0, 0))}
    return a


ITEM = ("ConePangolin", cone_pangolin, "Панголин-шишка", "Rare")
