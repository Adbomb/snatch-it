"""Птица-танцор (ParadiseDancer, Legendary, №29 каталога docs/BOSS6_CATALOG.md) — лофорина раскрыла за головой
бархатно-чёрный плащ огромным овалом (вдвое выше себя), на груди сияет бирюзовый щит-полумесяц, и она пританцовывает
боком: тело развёрнуто к игроку боком, таз сдвинут к опорной лапке, другая лапка согнута и поднята над подставкой,
голова склонена к плечу и повёрнута к игроку.
Признаки вида: плащ — вертикальный вогнутый овал из трёх широких сегментов (середина за головой, края выходят вперёд,
как у настоящей лофорины), по краю — сине-фиолетовый отлив, за головой — светлый ореол; светящийся бирюзовый
нагрудный щит полумесяцем, выгнутый по груди; бирюзовая шапочка на темени и бирюзовые «брови»; короткий чёрный
клюв с жёлтым кончиком и жёлтым зевом; прямые лапки (пальцы 3 + 1).
Эмоция — кураж и самолюбование: гордый прищур нижним веком (белок срезан снизу), брови внешними концами вверх,
взгляд искоса, клюв приоткрыт в улыбке — уголки жёлтого зева подняты.
Цвета: бархатно-чёрный с фиолетово-синим отливом, неоново-бирюзовый (светится), жёлтый зев, лапы графитовые.
Зависит от jungle_kit.py (палитра, свечение, звенья, подставка Legendary) и anatomy_kit (ярусы тела, A.facing).
"""

import math
import os
import sys

from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jungle_kit import *  # noqa: E402,F401,F403

BODY_YAW = 40.0  # тело развёрнуто к игроку боком (грудь смотрит вправо-вперёд), градусы вокруг z
LEAN = 6.0  # тело качнулось к опорной лапке, градусы вокруг y
PELVIS = 0.15  # таз сдвинут к опорной лапке (по x)
HEAD_YAW = -12.0  # голова повёрнута обратно к игроку (итоговый поворот головы вокруг z)
HEAD_ROLL = 10.0  # голова склонена к плечу
CAPE_X = 0.06  # середина плаща по x (за головой)
CAPE_Y = 0.52  # передняя грань середины плаща
CAPE_ZC = 2.66  # центр овала над верхом подставки
CAPE_R = (1.24, 1.83)  # полуоси наружного (сине-фиолетового) овала: ширина ≈ 2.4, высота ≈ 3.65
CAPE_RIM = 0.11  # ширина сине-фиолетовой каймы
CAPE_MID = 0.44  # полуширина среднего сегмента
CAPE_BEND = 32.0  # боковые сегменты выходят краем вперёд (вогнутая чаша)
GLOW_K = 1.55  # бирюза щита и темени светится сильнее обычного


def _oval(rx, rz, xc, zc, n=24):
    """Овал (x, z) из n точек: выпуклый многоугольник для prism по оси y."""
    return [(xc + rx * math.cos(2 * math.pi * (i + 0.5) / n), zc + rz * math.sin(2 * math.pi * (i + 0.5) / n))
            for i in range(n)]


def _clip(pts, axis, lo, hi):
    """Многоугольник (x, z), обрезанный полосой lo ≤ p[axis] ≤ hi (Сазерленд — Ходжман по двум прямым). Исходные
    вершины ближе 0.03 к точке среза выбрасываются — без коротких рёбер (вырожденных граней после фаски)."""

    def cut(poly, keep, at):
        out = []
        for i, p in enumerate(poly):
            q = poly[(i + 1) % len(poly)]
            ip, iq = keep(p[axis]), keep(q[axis])
            if ip:
                out.append((p, False))
            if ip != iq:
                k = (at - p[axis]) / (q[axis] - p[axis])
                out.append(((p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k), True))
        cuts = [p for p, c in out if c]
        res = [p for p, c in out if c or all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > 0.03 ** 2 for q in cuts)]
        return res

    poly = cut(list(pts), lambda v: v >= lo, lo)
    return cut(poly, lambda v: v <= hi, hi) if len(poly) >= 3 else []


def _scaled(pts, k, c):
    """Многоугольник (x, z), уменьшенный в k раз к точке c."""
    return [(c[0] + (x - c[0]) * k, c[1] + (z - c[1]) * k) for x, z in pts]


def _clip_x(pts, lo, hi):
    return _clip(pts, 0, lo, hi)


def _crescent(zc, rx0, rz0, rx1, rz1, tip, n=9):
    """Полумесяц рогами вверх (x, z): нижняя дуга овала rx0 × rz0, верхняя (вырез) — rx1 × rz1, рога сходятся
    в точках (±tip[0], zc + tip[1])."""
    outer, inner = [], []
    for i in range(n + 1):
        ang = math.radians(196 + (344 - 196) * i / n)
        outer.append((rx0 * math.cos(ang), zc + rz0 * math.sin(ang)))
    for i in range(n + 1):
        ang = math.radians(344 - (344 - 196) * i / n)
        inner.append((rx1 * math.cos(ang), zc + 0.03 + rz1 * math.sin(ang)))
    return [(-tip[0], zc + tip[1])] + outer + [(tip[0], zc + tip[1])] + inner


def _eye(a, c, r, normal, s, look):
    """Гордый прищур: белок срезан снизу на 44–60 % (верх ровный), нижний край поднят к внешнему уголку — глаз
    «улыбается»; зрачок искоса; бровь сине-фиолетовая, внешний конец вверх на 12°, брови высоко и на разной
    высоте (самодовольно, не хмуро).
    Подвесок и тонких полос нет."""
    m = Matrix.Translation(V(c)) @ A.facing(normal)
    w, hh, lift, sink = r, r * 1.1, 0.04, 0.06
    z_in, z_out = -0.12 * hh, 0.2 * hh  # срез снизу: 44 % высоты белка у внутреннего уголка, 60 % у внешнего
    a.prism("white", [(-w, hh), (w, hh)] + ([(w, z_out), (-w, z_in)] if s > 0 else [(w, z_in), (-w, z_out)]),
            -lift, sink, axis="y", bevel=0.01, matrix=m)
    pr = 0.4 * hh
    pz = (hh + max(z_in, z_out)) / 2
    px = look * (w - pr) * 0.8
    a.box("dark", px - pr, px + pr, -lift - 0.025, -lift + 0.01, pz - pr, pz + pr, bevel=0, matrix=m)
    g = 0.045
    a.box("glint", px - pr + 0.016, px - pr + 0.016 + g, -lift - 0.045, -lift - 0.02, pz + pr - 0.016 - g,
          pz + pr - 0.016, bevel=0, matrix=m)
    up = -s  # знак поворота вокруг оси y глаза, при котором внешний конец (x = s·w) поднимается
    raise_ = 0.055 + (0.025 if s > 0 else 0.0)  # бровь над глазом; одна выше другой — «бровь вскинута»
    mb = m @ Matrix.Translation((0, 0, hh + raise_)) @ Matrix.Rotation(math.radians(12 * up), 4, "Y")
    a.box("velvetB", -w * 1.02, w * 1.02, -lift - 0.02, sink * 2.2, -0.03, 0.03, bevel=0, matrix=mb)  # бровь


def _leg(a, nm, hip, knee, foot, fwd, t_toe, hang=False):
    """Лапка: бедро в бархатных перьях (уходит в тело), цевка не тоньше 0.13, стопа — три пальца вперёд по fwd
    и один назад. t_toe — высота низа пальцев; hang — лапка поднята, пальцы свисают."""
    part(a, nm, "Body", tuple(hip))
    hip, knee, foot, fwd = V(hip), V(knee), V(foot), V(fwd).normalized()
    side = V((-fwd.y, fwd.x, 0))
    kchain(a, "velvet", [hip + V((0, 0, 0.12)), knee], [0.3, 0.2], up=(0, -1, 0))
    knob(a, "leg", knee, 0.085)
    taper(a, "leg", knee, foot + V((0, 0, 0.06)), 0.15, 0.13, 0.15, 0.13, cut=0.24)
    knob(a, "leg", foot + V((0, 0, 0.07)), 0.095)
    for k, (ds, df, ln) in enumerate(((-0.4, 1, 0.3), (0.0, 1, 0.34), (0.4, 1, 0.3), (0.0, -1, 0.22))):
        d = (fwd * df + side * ds).normalized()
        p0 = V((foot.x, foot.y, t_toe + 0.045 + 0.005 * k))
        drop = -0.06 if hang else -0.01
        taper(a, "leg", p0, p0 + d * ln + V((0, 0, drop)), 0.12 - 0.004 * k, 0.09, 0.09 + 0.004 * k, 0.07,
              cut=0.22)


def _cape(a, t):
    """Плащ: вертикальный овал из трёх широких сегментов — средний за головой (светлый ореол вокруг головы),
    боковые повёрнуты краем вперёд (вогнутая чаша). Каждый сегмент — бархатно-чёрная пластина поверх
    сине-фиолетовой: кайма отлива идёт по всему краю овала. Сзади плащ сплошной, низ уходит в спину."""
    zc = t + CAPE_ZC
    rx, rz = CAPE_R
    outer = _oval(rx, rz, 0.0, zc)
    inner = _oval(rx - CAPE_RIM, rz - CAPE_RIM, 0.0, zc - 0.01)
    y0 = CAPE_Y
    base = Matrix.Translation((CAPE_X, 0, 0))
    # средний сегмент
    a.prism("velvetB", _clip_x(outer, -CAPE_MID, CAPE_MID), y0 + 0.035, y0 + 0.115, axis="y", matrix=base)
    a.prism("velvet", _clip_x(inner, -CAPE_MID + 0.006, CAPE_MID - 0.006), y0, y0 + 0.075, axis="y", matrix=base)
    # боковые сегменты: заходят за средний на 0.06, повёрнуты вокруг вертикали на шве
    for s in S2:
        hinge = Matrix.Translation((CAPE_X + s * CAPE_MID, y0 + 0.06, 0)) @ Matrix.Rotation(
            math.radians(-s * CAPE_BEND), 4, "Z") @ Matrix.Translation((-s * CAPE_MID, -(y0 + 0.06), 0))
        lo, hi = (CAPE_MID - 0.06, rx + 0.01) if s > 0 else (-rx - 0.01, -CAPE_MID + 0.06)
        a.prism("velvetB", _clip_x(outer, lo, hi), y0 + 0.045, y0 + 0.125, axis="y", matrix=hinge)
        lo2, hi2 = (lo + 0.004, hi) if s > 0 else (lo, hi - 0.004)
        a.prism("velvet", _clip_x(inner, lo2, hi2), y0 + 0.012, y0 + 0.087, axis="y", matrix=hinge)
    # светлый ореол за головой (фиолетово-синий отлив, светлее плаща): голова не сливается с плащом
    a.prism("halo", _oval(0.62, 0.72, CAPE_X, t + 1.56, n=16), y0 - 0.035, y0 + 0.03, axis="y")


def _size_report(a):
    """Габарит без подставки — в отчёт (size_without_stand_xyz) и в лог: потолок высоты 4.55 проверяется явно."""
    build0 = a.build

    def build(collection):
        obj = build0(collection)
        me = obj.data
        lo, hi = [1e9] * 3, [-1e9] * 3
        for poly, g in zip(me.polygons, a.face_groups):
            if g == "Stand":
                continue
            for vi in poly.vertices:
                co = obj.matrix_world @ me.vertices[vi].co
                for i in range(3):
                    lo[i], hi[i] = min(lo[i], co[i]), max(hi[i], co[i])
        size = [round(hi[i] - lo[i], 3) for i in range(3)]
        a.stats["size_without_stand_xyz"] = size
        a.stats["size_without_stand_ok"] = size[0] <= 3.7 and size[1] <= 3.7 and size[2] <= 4.55
        print("SIZE_NO_STAND", a.name, size, flush=True)
        return obj

    a.build = build


def paradise_dancer():
    a = new("ParadiseDancer", {"velvet": ("1E1A33", True), "velvetB": ("3E37A0", True), "halo": ("4C44A8", True),
                               "headV": ("29234A", True), "neonT": ("19F0DA", False), "teal": ("12C4BE", False),
                               "gape": ("FFD21C", False), "beak": ("121019", False), "leg": ("5A5570", False)})
    glow(a, GLOW * GLOW_K)
    _size_report(a)
    t = legendary_stand(a, 1.75)

    # оси тела: развёрнуто боком на BODY_YAW, качнулось к опорной лапке, таз сдвинут на PELVIS
    bm = Matrix.Translation((PELVIS, 0, 0)) @ tilt((0, 0, t + 0.5), "Y", LEAN) @ tilt((0, 0.05, 0), "Z", BODY_YAW)
    fwd = (bm.to_3x3() @ V((0, -1, 0))).normalized()

    # ── тело: бархатное яйцо, ярусы через один чёрный и с фиолетово-синим отливом ──
    z0 = t + 0.42
    part(a, "Body", "Stand", tuple(bm @ V((0, 0.05, t + 0.85))))
    with_matrix(a, bm)
    tiers = A.body(a, "velvet", (0, 0.05, z0), 0.47, 0.43, 0.92, "egg", n=5, lean=-0.06,
                   keys=("velvet", "velvetB", "velvet", "velvetB", "velvet"))
    # нагрудный щит-полумесяц: выступ над грудью ≤ 0.11, выгнут по груди — средний кусок на передней грани,
    # боковые (с рогами) лежат на скошенных углах ярусов; рога не шире корпуса
    zc = z0 + 0.6
    under = [tr for tr in tiers if tr[1] > zc - 0.28 + 0.03 and tr[0] < zc + 0.14 - 0.03]
    back = max(under, key=lambda tr: tr[3] - tr[5])  # самый узкий (задний) ярус под щитом
    za, zb, tx, ty, wx, wy, cut = back
    fy = ty - wy
    hx = wx - cut
    cres = _crescent(zc, hx + cut * 0.9, 0.28, hx + 0.03, 0.08, (hx + cut * 0.92, 0.14))
    y_front, y_back = fy - 0.11, fy + 0.05
    a.extrude("neonT", _clip_x(cres, -hx, hx), y_front, y_back, axis="y")
    for s in S2:
        bend = tilt((s * hx, fy, 0), "Z", s * 45.0)
        lo, hi = (hx - 0.03, 2.0) if s > 0 else (-2.0, -hx + 0.03)
        a.extrude("neonT", _clip_x(cres, lo, hi), y_front + 0.004, y_back - 0.004, axis="y", matrix=bend)
    for s in S2:  # сложенные крылья по бокам, из-под рогов щита
        A.folded_wing(a, "velvetB", "velvet", (s * 0.45, 0.16, z0 + 0.72), s, 0.56, 0.34, rows=2,
                      down=(0, 0.35, -1), thick=0.11)
    with_matrix(a, None)

    # ── хвостик: короткий и толстый, торчит назад-вниз из-под плаща ──
    part(a, "Tail", "Body", tuple(bm @ V((0, 0.36, z0 + 0.2))))
    with_matrix(a, bm)
    A.flipper(a, "velvet", (0, 0.3, z0 + 0.26), (0, 0.62, z0 + 0.02), 0.34, 0.3, thick=0.2, up=(0, 0.4, 1))
    with_matrix(a, None)

    # ── лапки: левая — опорная прямо под телом, правая согнута в колене и поднята над подставкой ──
    hipL = bm @ V((0.17, 0.06, t + 0.55))
    footL = V((hipL.x - 0.06, hipL.y - 0.03, t))
    _leg(a, "LegL", hipL, hipL.lerp(footL, 0.38) + V((0.02, -0.02, 0)), footL, fwd, t)
    hipR = bm @ V((-0.17, 0.06, t + 0.55))
    kneeR = hipR + V((-0.13, -0.07, -0.15))
    footR = hipR + V((-0.4, -0.04, -0.36))  # ступня в 0.15 над подставкой, колено согнуто ≈ 30°
    _leg(a, "LegR", hipR, kneeR, footR, fwd, footR.z - 0.02, hang=True)

    # ── голова: одна округлая ступенчатая, ширина ≈ 0.7; повёрнута к игроку и склонена к плечу ──
    top = bm @ V((0, 0.02, z0 + 0.92))
    hc = top + V((0.0, -0.02, 0.17))
    HX, HY, HZ = 0.35, 0.33, 0.31
    part(a, "Head", "Body", tuple(top + V((0, 0, 0.02))))
    hm = Matrix.Translation(hc) @ Matrix.Rotation(math.radians(HEAD_YAW), 4, "Z") @ Matrix.Rotation(
        math.radians(-HEAD_ROLL), 4, "Y")
    with_matrix(a, hm)
    htiers = A.body(a, "headV", (0, 0, -HZ), HX, HY, 2 * HZ, "ball", n=4, floor=0.45)
    # бирюзовая шапочка на темени: плоская, во всю верхнюю грань
    za_t, zb_t, x_t, y_t, wx_t, wy_t, cut_t = htiers[-1]
    a.prism("neonT", S.octagon(-wx_t * 0.8, wx_t * 0.8, y_t - wy_t * 0.86, y_t + wy_t * 0.55, cut_t * 0.8),
            zb_t - 0.03, zb_t + 0.035, axis="z")
    ze = 0.07
    for s in S2:
        fe = front_y(htiers, s * 0.15, ze)
        _eye(a, (s * 0.155, fe + 0.025, ze), 0.11, (s * 0.32, -1, 0.04), s, look=-0.45)
    # клюв: короткий чёрный клин ступенями вперёд с жёлтым кончиком; приоткрыт — между надклювьем и подклювьем
    # жёлтый зев полосой-улыбкой (уголки выше середины)
    zb = -0.08
    fb = front_y(htiers, 0, zb)
    up1 = [(-0.125, zb + 0.035), (0.125, zb + 0.035), (0.095, zb - 0.055), (0.0, zb - 0.1), (-0.095, zb - 0.055)]
    a.prism("beak", up1, fb - 0.08, fb + 0.05, axis="y", bevel=0.01)
    a.prism("beak", _scaled(up1, 0.72, (0, zb - 0.04)), fb - 0.15, fb - 0.07, axis="y", bevel=0.01)
    a.prism("gape", _scaled(up1, 0.44, (0, zb - 0.06)), fb - 0.2, fb - 0.14, axis="y", bevel=0.01)
    a.prism("gape", [(-0.14, zb + 0.01), (0.14, zb + 0.01), (0.11, zb - 0.13), (0.0, zb - 0.23), (-0.11, zb - 0.13)],
            fb - 0.065, fb + 0.04, axis="y", bevel=0.01)  # зев
    with_matrix(a, None)

    part(a, "Jaw", "Head", tuple(hm @ V((0, fb + 0.1, zb - 0.13))))
    with_matrix(a, hm)
    a.extrude("beak", [(-0.12, zb - 0.1), (0.0, zb - 0.2), (0.12, zb - 0.1), (0.09, zb - 0.19),
                       (0.0, zb - 0.27), (-0.09, zb - 0.19)], fb - 0.12, fb + 0.14, axis="y")  # подклювье-улыбка
    with_matrix(a, None)

    # ── плащ за головой: фронтально к игроку ──
    part(a, "Cape", "Body", (CAPE_X, 0.4, t + 1.15))
    _cape(a, t)

    fpt = hm @ V((0, fb, 0.0))
    face_point(a, tuple(fpt))
    closeup(a, (CAPE_X + 0.6, CAPE_Y - 0.1, t + 2.6), eye_off=(-1.0, -2.4, 0.6))
    # поза — другая фаза танца: прыжок в другую сторону (зеркальный шаг), голова к другому плечу, клюв шире
    a.pose = {"Body": ((0, -10, -16), (-0.22, 0, 0.08)), "LegR": ((0, -38, 0), (0, 0, 0)),
              "LegL": ((0, -34, 0), (0, 0, 0)), "Head": ((0, 22, -10), (0, 0, 0)), "Jaw": ((18, 0, 0), (0, 0, 0)),
              "Cape": ((0, 6, 10), (0, 0, 0)), "Tail": ((12, 0, -10), (0, 0, 0))}
    return a


ITEM = ("ParadiseDancer", paradise_dancer, "Птица-танцор", "Legendary")
