"""Ящерица-воротник (FrillLizard, Epic, №25 каталога docs/BOSS6_CATALOG.md) — собралась чихнуть и от неожиданности
распахнула складчатый воротник шире себя и встала на задние лапы.
Признаки вида (плащеносная ящерица): плоский воротник-веер вокруг шеи на «спицах»; стоит на двух задних лапах, корпус
наклонён вперёд, голова впереди бёдер; длинный хвост-противовес поднят от основания и только кончиком касается пола;
ярко-жёлтая пасть без зубов (жёлтое — только внутри); чешуя ярусами (ряды черепицы со сдвигом на полширины на спине и
боках, кольца хвоста).
Эмоция — удивление на чихе «ап-…»: голова запрокинута, пасть распахнута, ноздри раздуты, глаза круглые, брови высоко
над глазами дугой.
Цвета: кобальтово-синее тело со светло-голубым брюшком, воротник красно-оранжево-жёлтый, как закат, пасть жёлтая.
Зависит от jungle_kit.py (creature_kit, anatomy_kit, art_style, v4_kit).
"""

import math
import os
import sys

from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jungle_kit import *  # noqa: E402,F401,F403

FRILL_T = 0.09  # толщина пластин воротника (не тоньше 0.07 — не мерцает)
BANDS = (("frY", 0.1, 0.6, -0.03), ("frO", 0.56, 0.8, -0.015), ("frR", 0.76, 1.0, 0.0))  # закат от шеи к краю
LEAN = 17  # наклон корпуса и шеи вперёд, градусы: голова впереди бёдер, хвост уравновешивает
HEAD_UP = 13  # голова запрокинута на «ап-…»
GAPE = 38  # раскрытие нижней челюсти


def _frill_r(deg):
    """Радиус воротника под углом deg (0 — к +x, 90 — вверх): широкий овал, внизу у груди короче."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    ry = 1.38 if s >= 0 else 0.95
    return 1.0 / math.sqrt((c / 1.5) ** 2 + (s / ry) ** 2)


def _frill(a, m, a_lo, a_hi, n):
    """Складчатый воротник-веер в осях m (плоскость xz, лицо к −y): n секторов-складок от a_lo до a_hi градусов,
    у каждого три полосы заката (жёлтая у шеи, оранжевая, красная по краю). Складки чередуются: чётные выступают
    вперёд, нечётные утоплены на 0.045 и чуть шире (заходят под соседей) — края пластин не совпадают; край
    зубчатый: середина сектора выступает, нечётные короче. По середине каждого сектора — тёмная «спица».
    Сзади все складки до 0.8 радиуса закрывает одна цельная оранжевая пластина — без швов между складками."""
    span = (a_hi - a_lo) / n
    for i in range(n):
        p = i % 2
        a0, a1 = a_lo + i * span, a_lo + (i + 1) * span
        am = (a0 + a1) / 2
        y0 = 0.045 * p
        k_len = 0.93 if p else 1.0  # нечётные складки короче — край веера зубчатый
        for b, (key, r0, r1, dy) in enumerate(BANDS):
            e = (1.6 if p else 0.0) + 0.35 * b  # у каждой полосы своя ширина — боковые грани не совпадают
            b0, b1 = math.radians(a0 - e), math.radians(a1 + e)
            ra, rb, rm = _frill_r(a0) * k_len, _frill_r(a1) * k_len, _frill_r(am) * k_len
            pts = [(r0 * ra * math.cos(b0), r0 * ra * math.sin(b0))]
            if b == 2:  # внешняя полоса — с острым краем-зубцом посередине
                pts += [(0.88 * ra * math.cos(b0), 0.88 * ra * math.sin(b0)),
                        (r1 * rm * math.cos(math.radians(am)), r1 * rm * math.sin(math.radians(am))),
                        (0.88 * rb * math.cos(b1), 0.88 * rb * math.sin(b1))]
            else:
                pts += [(r1 * ra * math.cos(b0), r1 * ra * math.sin(b0)),
                        (r1 * rb * math.cos(b1), r1 * rb * math.sin(b1))]
            pts.append((r0 * rb * math.cos(b1), r0 * rb * math.sin(b1)))
            a.prism(key, pts, y0 + dy, y0 + dy + FRILL_T, axis="y", bevel=0, matrix=m)
        # спица по середине складки: брусок на передней грани (выступает из жёлтой полосы на 0.03)
        ms = m @ Matrix.Rotation(math.radians(-am), 4, "Y")
        a.box("frD", 0.2 * rm, 0.86 * rm, y0 - 0.06, y0 - 0.005, -0.045, 0.045, bevel=0, matrix=ms)
    # цельная задняя пластина: веер от a_lo до a_hi на 0.8 радиуса, от y 0.05 (за всеми передними гранями) до 0.16
    # (за всеми задними) — грани ни с чем не совпадают
    pts = [(0.0, 0.0)]
    k = 26
    for j in range(k + 1):
        d = a_lo + (a_hi - a_lo) * j / k
        r = 0.8 * _frill_r(d)
        pts.append((r * math.cos(math.radians(d)), r * math.sin(math.radians(d))))
    a.extrude("frO", pts, 0.05, 0.16, axis="y", matrix=m)


def _oct_dist(wx, wy, cut, phi):
    """Расстояние от середины яруса-восьмиугольника (полуширины wx, wy, скос cut) до его стенки под углом phi."""
    d = (math.cos(math.radians(phi)), math.sin(math.radians(phi)))
    q = 1 / math.sqrt(2)
    planes = [((1, 0), wx), ((-1, 0), wx), ((0, 1), wy), ((0, -1), wy)]
    planes += [((sx * q, sy * q), (wx + wy - cut) * q) for sx in (1, -1) for sy in (1, -1)]
    return min(h / (n[0] * d[0] + n[1] * d[1]) for n, h in planes if n[0] * d[0] + n[1] * d[1] > 1e-6)


def _scales(a, key, tiers, rows=(1, 2, 3)):
    """Чешуя ярусами на спине и боках: на каждом ярусе тела — ряд черепиц (верх утоплен в ярус, низ отогнут наружу
    и нависает на 0.1 над рядом ниже); соседние ряды сдвинуты на полширины черепицы (4 и 5 штук по задней половине)."""
    for k in rows:
        za, zb, bx, by, wx, wy, cut = tiers[k]
        lo = tiers[k - 1]
        phis = (36, 72, 108, 144) if k % 2 else (14, 54, 90, 126, 166)
        for i, phi in enumerate(phis):
            r = _oct_dist(wx, wy, cut, phi)
            rl = _oct_dist(lo[4], lo[5], lo[6], phi)
            d = V((math.cos(math.radians(phi)), math.sin(math.radians(phi)), 0))
            nrm = V((d.x / wx, d.y / wy, 0)).normalized()
            px, py = bx + d.x * r, by + d.y * r
            ob = max(rl - r, 0.0) * d.dot(nrm) + 0.1  # низ черепицы снаружи ряда ниже
            f = Matrix(((nrm.y, nrm.x, 0, px), (-nrm.x, nrm.y, 0, py), (0, 0, 1, 0), (0, 0, 0, 1)))
            jt, jb = zb - 0.03 - 0.007 * i, za - 0.1 - 0.006 * i  # у соседних черепиц верх и низ на разной высоте
            pts = [(jt, -0.08), (jt, 0.015), (jb, ob), (jb, ob - 0.09)]
            a.prism(key, pts, -0.1, 0.1, axis="x", bevel=0, matrix=f)


def _foot(a, key, ankle, s, z):
    """Лапа ящерицы: подушка стопы вперёд и четыре длинных пальца веером (у пальцев разная высота — низы не
    совпадают)."""
    an = V(ankle)
    taper(a, key, (an.x, an.y + 0.1, z + 0.065), (an.x + s * 0.04, an.y - 0.2, z + 0.06), 0.22, 0.2, 0.13, 0.11,
          cut=0.25)
    root = V((an.x + s * 0.04, an.y - 0.16, 0))
    f = V((s * 0.15, -1, 0)).normalized()
    for i in range(4):
        d = Matrix.Rotation((i - 1.5) * 0.36, 3, "Z") @ f
        r = root + V((0, 0, z + 0.045 + 0.006 * i))
        taper(a, key, r, r + d * (0.3 if i in (1, 2) else 0.24), 0.085, 0.075, 0.075 - 0.003 * i, 0.07, cut=0.25)


def _hand(a, key, wrist, s):
    """Лапка ящерицы, поджатая перед грудью: три пальца-коготка вперёд и чуть врозь (не «ладошки вверх»)."""
    w = V(wrist)
    knob(a, key, tuple(w), 0.075, n=1)
    for k in range(3):
        d = V((s * (-0.22 + 0.3 * k), -1, 0.3 - 0.06 * k)).normalized()
        taper(a, key, w + d * 0.02, w + d * 0.19, 0.08, 0.072, 0.075, 0.07, up=(0, 0, 1), cut=0.25)


def frill_lizard():
    a = new("FrillLizard", {"cob": ("2456E0", True), "cobD": ("163A9E", True), "cobL": ("8CC4FF", False),
                            "frY": ("FFD23A", True), "frO": ("FF8A1E", True), "frR": ("E8344A", True),
                            "frD": ("9E1434", False), "mouthY": ("FFE14D", False)})
    t = epic_stand(a, 1.7)
    lm = tilt((0, 0.12, t + 0.7), "X", LEAN)  # корпус наклонён вперёд вокруг бёдер

    # тело: кобальтовое яйцо, наклонено вперёд; светло-голубое брюшко; на спине и боках — чешуя ярусами
    part(a, "Body", "Stand", tuple(lm @ V((0, 0.12, t + 0.95))))
    with_matrix(a, lm)
    tb = A.body(a, "cob", (0, 0.12, t + 0.48), 0.4, 0.35, 1.0, "egg", n=4,
                front=("cobL", 0.7, t + 0.6, t + 1.42))
    _scales(a, "cobD", tb)
    with_matrix(a, None)

    # задние лапы: мощные бёдра, колени вперёд-наружу, стопы под центром масс
    for s in S2:
        nm = "Leg" + ("L" if s > 0 else "R")
        part(a, nm, "Body", (s * 0.26, 0.12, t + 0.72))
        A.limb(a, "cob", [(s * 0.26, 0.12, t + 0.72), (s * 0.42, -0.16, t + 0.44), (s * 0.34, 0.02, t + 0.14)],
               [0.3, 0.24, 0.18], joints=False)
        knob(a, "cob", (s * 0.42, -0.16, t + 0.44), 0.15)  # колено
        _foot(a, "cob", (s * 0.34, 0.02, t + 0.14), s, t)

    # передние лапки поджаты перед грудью от неожиданности (плечи узкие, у самой шеи)
    for s in S2:
        nm = "Arm" + ("L" if s > 0 else "R")
        sh = (s * 0.24, 0.02, t + 1.24)
        part(a, nm, "Body", tuple(lm @ V(sh)))
        with_matrix(a, lm)
        knob(a, "cob", sh, 0.1, n=1)
        elbow, wrist = (s * 0.4, -0.14, t + 1.04), (s * 0.4, -0.44, t + 1.16)
        A.limb(a, "cob", [sh, elbow, wrist], [0.14, 0.12, 0.1], joints=False)
        knob(a, "cob", elbow, 0.075, n=1)  # локоть
        _hand(a, "cob", wrist, s)
        with_matrix(a, None)

    # хвост-противовес: поднят от основания на ~20°, дугой назад-влево, пола касается только у кончика; кольцами
    # двух синих (чешуя ярусами), сужается от 0.36 к 0.14
    part(a, "Tail", "Body", tuple(lm @ V((0, 0.3, t + 0.62))))
    tail = [V((0, 0.22, t + 0.66)), V((0, 0.72, t + 0.84)), V((-0.12, 1.16, t + 0.8)), V((-0.46, 1.4, t + 0.56)),
            V((-0.9, 1.3, t + 0.3)), V((-1.2, 0.95, t + 0.085)), V((-1.28, 0.58, t + 0.22))]
    ws = [0.36, 0.32, 0.27, 0.23, 0.19, 0.16, 0.14]
    for i in range(len(tail) - 1):
        K.KEY = "cob" if i % 2 == 0 else "cobD"
        K.taper(a, tail[i], tail[i + 1], ws[i] * 1.06, ws[i + 1], ws[i] * 0.95 * 1.06, ws[i + 1] * 0.95, up=(0, 0, 1),
                cut=0.26, ext0=ws[i] * 0.15 if i else 0.0, ext1=ws[i + 1] * 0.1)

    # голова: клин ящерицы на наклонённой шее, впереди бёдер; запрокинута на «ап-…»
    hc = lm @ V((0, -0.1, t + 1.92))
    part(a, "Head", "Body", tuple(lm @ V((0, 0.04, t + 1.62))))
    with_matrix(a, lm)
    taper(a, "cob", (0, 0.1, t + 1.35), (0, -0.02, t + 1.86), 0.4, 0.34, 0.36, 0.3, cut=0.3)  # шея
    hy, hz = hc.y, hc.z
    hm = tilt(hc, "X", -HEAD_UP)
    with_matrix(a, hm)
    # череп и сужающаяся морда (клин ящерицы); нёбо уже плоского низа морды и не доходит до кончика: спереди жёлтое,
    # в глубине пасти тёмное — открытый рот, а не клюв
    taper(a, "cob", (0, hy + 0.22, hz + 0.08), (0, hy - 0.22, hz + 0.08), 0.6, 0.62, 0.34, 0.36, cut=0.3)
    taper(a, "cob", (0, hy - 0.16, hz + 0.04), (0, hy - 0.66, hz + 0.0), 0.54, 0.36, 0.24, 0.15, cut=0.3)
    taper(a, "mouthY", (0, hy - 0.26, hz - 0.1), (0, hy - 0.48, hz - 0.095), 0.26, 0.22, 0.11, 0.11, cut=0.15)
    taper(a, "mouth", (0, hy - 0.0, hz - 0.095), (0, hy - 0.3, hz - 0.095), 0.24, 0.2, 0.09, 0.09, cut=0.15)  # глубина
    a.box("mouth", -0.14, 0.14, hy - 0.11, hy + 0.14, hz - 0.3, hz - 0.06, bevel=0)  # тёмная глотка в глубине пасти
    for s in S2:  # раздутые ноздри: тёмные бруски 0.10 × 0.07 на верхнем крае кончика морды, развёрнуты наружу
        nc = V((s * 0.08, hy - 0.64, hz + 0.055))
        a.box("dark", nc.x - 0.05, nc.x + 0.05, nc.y - 0.05, nc.y + 0.04, nc.z - 0.035, nc.z + 0.035, bevel=0,
              matrix=tilt(nc, "Z", s * 22))
    # глаза на двух буграх, развёрнуты чуть наружу; брови высоко над глазами (синий зазор) дугой — концы вниз
    for s in S2:
        em = hm @ Matrix.Translation((s * 0.21, hy - 0.28, hz + 0.26)) @ Matrix.Rotation(math.radians(s * 16), 4, "Z")
        with_matrix(a, em)
        a.prism("cob", S.octagon(-0.135, 0.135, 0.02, 0.26, 0.05), -0.17, 0.355, axis="z")  # бугор глаза
        eye2(a, (0, 0, 0), 0.11, (0, -1, 0.12), "surprised", s, "cob", "dark", pupil=0.44, show_brow=False,
             look=(-s * 0.3, 0.35))
        bz = 0.11 * 1.1 + 0.13  # низ брови на 0.13 выше верха белка
        a.box("dark", -0.15, 0.15, -0.04, 0.12, bz, bz + 0.08, bevel=0, matrix=tilt((0, 0, bz), "Y", s * 4))
    with_matrix(a, None)

    # нижняя челюсть распахнута: снаружи синяя, внутри жёлтая (уже челюсти, внутри её контура), зубов нет
    hinge = (0, hy + 0.14, hz - 0.1)
    part(a, "Jaw", "Head", tuple(hm @ V(hinge)))
    with_matrix(a, hm @ tilt(hinge, "X", GAPE))
    taper(a, "cob", (0, hy + 0.18, hz - 0.16), (0, hy - 0.58, hz - 0.15), 0.5, 0.32, 0.15, 0.1, cut=0.3)
    taper(a, "mouthY", (0, hy - 0.22, hz - 0.08), (0, hy - 0.46, hz - 0.085), 0.24, 0.17, 0.11, 0.11, cut=0.2)
    taper(a, "mouth", (0, hy + 0.06, hz - 0.085), (0, hy - 0.26, hz - 0.09), 0.26, 0.2, 0.09, 0.09, cut=0.15)
    with_matrix(a, None)

    # воротник-веер вокруг шеи за головой, почти отвесно (чуть откинут), раскрыт от −40° до 220° (под горлом — грудь)
    fc = V((0, hy + 0.19, hz - 0.04))  # череп заходит в воротник на 0.06
    part(a, "Frill", "Head", tuple(fc))
    fm = Matrix.Translation(fc) @ Matrix.Rotation(math.radians(-6), 4, "X")
    _frill(a, fm, -40, 220, 12)

    face_point(a, tuple(hm @ V((0, hy - 0.35, hz + 0.12))))
    closeup(a, (0.0, -0.3, t + 1.3), eye_off=(-1.4, -3.0, 1.0))
    a.pose = {"Head": ((-12, 0, 10), (0, 0, 0)), "Jaw": ((8, 0, 0), (0, 0, 0)), "Frill": ((-5, 0, 0), (0, 0, 0)),
              "ArmL": ((-25, 0, -10), (0, 0, 0)), "ArmR": ((-15, 0, 15), (0, 0, 0)), "Tail": ((8, 0, -18), (0, 0, 0))}
    return a


ITEM = ("FrillLizard", frill_lizard, "Ящерица-воротник", "Epic")
