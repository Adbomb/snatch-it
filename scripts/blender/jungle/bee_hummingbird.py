"""Колибри-шмель (BeeHummingbird, Common, №5 каталога docs/BOSS6_CATALOG.md) — самая маленькая птица решила, что она
шмель: малиновая голова колибри с клювом-иголкой, а тело — круглое пушистое полосатое брюшко шмеля; зависла у жёлтого
цветка на стебле и пьёт нектар. Признаки вида: длинный тонкий клюв-иголка, переливчатое горлышко (ряды розовых и
фиолетовых чешуек-пёрышек), крылья — размытые полупрозрачные веера, крошечные поджатые лапки, хвост веером.
Эмоция — деловитая сосредоточенность: бровки чуть нахмурены, щёки надуты, оба глаза косятся на кончик клюва и цветок.
Цвета: малиново-розовые голова и горлышко, оранжево-чёрное полосатое брюшко, крылья прозрачно-голубые; цветок-опора
жёлтый (видимая часть Haze, D58), стебель и лист — зелёный акцент.
"""

import math
import os
import sys

from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jungle_kit import *  # noqa: E402,F401,F403


def _frame(o, x, y):
    """Матрица осей: начало o, ось x — x, ось y — y (ортогонализуется), z = x × y."""
    x = V(x).normalized()
    y = (V(y) - x * V(y).dot(x)).normalized()
    z = x.cross(y)
    return Matrix(((x.x, y.x, z.x, o[0]), (x.y, y.y, z.y, o[1]), (x.z, y.z, z.z, o[2]), (0, 0, 0, 1)))


def _wing(a, s, sh):
    """Крыло-веер: размытый взмах — полупрозрачный сектор от плеча вверх и в стороны, поверх — три светлых
    «призрака» пера (кадры взмаха) на передней стороне веера у обоих крыльев. Корень заходит в тело."""
    m = _frame(sh, (s * 1.0, 0.28, 0.12), (0.0, 0.32, 1.0))
    # ось z рамки: у левого крыла (s = 1) смотрит вперёд (−y), у правого — назад; перья кладём на сторону −y
    R = 1.22
    fan = [(-0.16, -0.06)]
    for k in range(8):
        ang = math.radians(-4 + k * 86 / 7)
        fan.append((R * math.cos(ang), R * math.sin(ang)))
    a.extrude("wing", fan, -0.04, 0.04, axis="z", matrix=m)
    for k, deg in enumerate((14, 40, 66)):  # перья-призраки: длинные ромбы-лопасти, светлее веера; корни врозь
        ang = math.radians(deg)
        d, n = V((math.cos(ang), math.sin(ang))), V((-math.sin(ang), math.cos(ang)))
        pts = [d * 0.22, d * 0.5 + n * 0.11, d * 1.08 + n * 0.06, d * 1.14, d * 1.08 - n * 0.06, d * 0.5 - n * 0.11]
        z0 = s * (0.03 + 0.022 * k)  # толщина 0.08, ступень 0.022 — грани перьев не совпадают
        z1 = z0 + s * 0.08
        a.extrude("wingL", [tuple(p) for p in pts], min(z0, z1), max(z0, z1), axis="z", matrix=m)


def _scale(a, key, x, z, w, h, y0, y1, up=0.0):
    """Чешуйка горлышка: пятиугольник уголком вниз (перо), выступает от y0 вглубь до y1; up — подъём верха (соседние
    чешуйки разной высоты — верхние грани не совпадают)."""
    a.prism(key, [(x - w / 2, z + h * 0.45 + up), (x + w / 2, z + h * 0.45 + up), (x + w / 2, z - h * 0.1), (x, z - h * 0.55),
                  (x - w / 2, z - h * 0.1)], y0, y1, axis="y", bevel=0)


def bee_hummingbird():
    a = new("BeeHummingbird", {"head": ("F25C94", True), "crest": ("A3175A", True), "gorget": ("D4126A", False),
                               "sheen": ("A66BFF", False), "cheek": ("FF6EA6", True),
                               "beak": ("2B2236", False), "beeO": ("FF9A1F", True), "beeK": ("2A2438", True),
                               "fuzz": ("FFC94A", True), "leg": ("5B4A6E", False), "feet": ("3A2E4A", False),
                               "toe": ("FFD3E6", False), "wing": ("A8E2FF", False),
                               "wingL": ("E6F7FF", False), "tail": ("E8357A", True), "tailT": ("7A1E5A", False),
                               "petal": ("FFD21F", True), "petalD": ("FFB000", False), "core": ("FF7A1C", False),
                               "stem": ("5FAE3E", True), "leaf": ("7ED957", True), "leafV": ("3E8A34", False)})
    a.transparent_parts = ("WingL", "WingR")
    t = common_stand(a, 1.5)

    C = V((0.0, 0.58, t + 1.72))  # центр брюшка
    mb = Matrix.Translation(C) @ Matrix.Rotation(math.radians(25), 4, "X")  # брюшко наклонено вперёд (зависла)
    HEAD_TURN = 25  # голова повернута к цветку (вправо-вперёд), лицо видно спереди и в hero
    BEAK = 0.9  # длина клюва-иголки
    hc = V((0.0, 0.1, t + 2.64))  # центр головы
    hm = Matrix.Translation(hc) @ Matrix.Rotation(math.radians(HEAD_TURN), 4, "Z") @ Matrix.Translation(-hc)
    bdir_l = V((0.0, -1.0, -0.7)).normalized()
    broot_l = hc + V((0.0, -0.5, -0.11))  # корень клюва — на конце лобной ступени
    btip = hm @ (broot_l + bdir_l * BEAK)
    bdir = (hm.to_3x3() @ bdir_l).normalized()
    fc = btip + bdir * 0.1  # середина цветка — сразу за кончиком клюва

    # ── цветок-опора (Haze: в игре подставка скрыта, цветок виден): стебель из подставки справа спереди, лист под
    # лапками птицы повернут лицом к зрителю (не «жёрдочка»), жёлтый цветок раскрыт навстречу клюву
    part(a, "Haze", "Stand", (0.8, -0.75, t))
    nf = (V((0, 0, 1.0)) - bdir).normalized()  # цветок раскрыт вверх и к птице
    kchain(a, "stem", [(0.8, -0.72, t - 0.02), (0.86, -0.9, t + 1.0), tuple(fc - nf * 0.36 - V((0, 0, 0.06)))],
           [0.16, 0.14, 0.12], [0.16, 0.14, 0.12], up=(0, -1, 0), cut=0.3)
    legs = []  # лапки: верх в брюшке → ступня
    for s in S2:
        legs.append((s, mb @ V((s * 0.17, -0.3, -0.42)), mb @ V((s * 0.19, -0.4, -0.62))))
    lroot = V((0.86, -0.86, t + 0.94))
    mid = (legs[0][2] + legs[1][2]) / 2
    ldir = V((mid.x - lroot.x, mid.y - lroot.y, 0.0)).normalized()
    ltip = V((mid.x + ldir.x * 0.42, mid.y + ldir.y * 0.42, mid.z - 0.16))
    LN, LT = V((0.15, -0.5, 1.0)), 0.08
    flat_leaf(a, "leaf", "leafV", tuple(lroot), tuple(ltip), 0.6, LT, tuple(LN))
    lx = (ltip - lroot).normalized()
    lz = lx.cross(LN.cross(lx).normalized())  # нормаль плоскости листа (как в flat_leaf)

    def leaf_z(x, y):
        return lroot.z - (lz.x * (x - lroot.x) + lz.y * (y - lroot.y)) / lz.z

    K.KEY = "petalD"
    K.taper(a, fc - nf * 0.38, fc - nf * 0.02, 0.14, 0.32, 0.14, 0.32, up=(0, 1, 0), cut=0.3)  # чашечка-трубка
    petals(a, tuple(fc), 6, 0.26, 0.19, ("petal",), "core", 0.12, normal=tuple(nf), lift=24)

    # ── брюшко шмеля: круглое пушистое яйцо из 9 ярусов, полоски; низ закрыт широким оранжевым ярусом
    part(a, "Body", "Stand", tuple(C))
    A.body(a, "beeO", (0, 0, -0.63), 0.64, 0.6, 1.26, "egg", n=9, floor=0.45, matrix=mb, corner=0.5,
           keys=["beeO", "beeO", "beeK", "beeO", "beeK", "beeO", "beeK", "fuzz", "fuzz"])
    for k in range(9):  # пушистый воротник шмеля под головой: короткие толстые пучки по кругу
        ang = math.radians(10 + k * 40)
        dv = V((math.cos(ang), math.sin(ang), 0.0))
        blunt(a, "fuzz", mb @ (dv * 0.3 + V((0, 0, 0.47 + 0.004 * k))), mb @ (dv * 0.47 + V((0, 0, 0.56))), 0.2, 0.13)
    for k, deg in enumerate((0, 180, 90)):  # пушок на нижнем оранжевом ярусе: бока и спина (перёд — лапки)
        dv = V((math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0.0))
        blunt(a, "beeO", mb @ (dv * 0.26 + V((0, 0, -0.42 - 0.005 * k))), mb @ (dv * 0.5 + V((0, 0, -0.54))), 0.2,
              0.12)
    # крошечные поджатые лапки: тёмные, с двумя светлыми пальчиками, сжимают край листа
    for s, top, foot in legs:
        fz = leaf_z(foot.x, foot.y) + LT / 2 + 0.07
        foot = V((foot.x, foot.y, fz))
        taper(a, "leg", top, foot, 0.12, 0.1, 0.12, 0.1, cut=0.2)
        knob(a, "feet", tuple(foot), 0.1)
        for e in (-1, 1):  # пальчики вперёд, чуть врозь, лежат на листе
            tx, ty = foot.x + e * 0.065, foot.y - 0.11
            tz = leaf_z(tx, ty) + LT / 2
            blunt(a, "toe", (foot.x + e * 0.05, foot.y - 0.03, tz + 0.06), (tx, ty, tz + 0.01), 0.12, 0.09)

    # ── хвост веером: пять перьев вниз-назад, концы тёмные
    part(a, "Tail", "Body", tuple(mb @ V((0, 0.1, -0.5))))
    base = mb @ V((0, 0.12, -0.46))
    for k in range(5):
        ang = math.radians((k - 2) * 22)
        d = V((math.sin(ang) * 0.9, 0.55, -math.cos(ang) * 0.9)).normalized()
        mid = base + d * 0.5
        taper(a, "tail", base, mid, 0.14, 0.2, 0.08 + 0.006 * k, 0.08 + 0.006 * k, up=(0, 1, 0.4), cut=0.3)
        taper(a, "tailT", mid - d * 0.04, base + d * 0.72, 0.2, 0.12, 0.085 + 0.006 * k, 0.075, up=(0, 1, 0.4),
              cut=0.3)

    # ── крылья-веера
    for s, nm in ((1, "WingL"), (-1, "WingR")):
        sh = mb @ V((s * 0.36, 0.08, 0.28))
        part(a, nm, "Body", tuple(sh))
        _wing(a, s, sh)

    # ── голова колибри: повернута к цветку; круглая макушка с хохолком, лобная ступень переходит в клюв-иголку,
    # горлышко из чешуек, надутые щёки, бровки чуть сведены
    part(a, "Head", "Body", (0.0, 0.18, t + 2.3))
    with_matrix(a, hm)
    R, RY, RZ = 0.44, 0.42, 0.42
    th = A.body(a, "head", (hc.x, hc.y, hc.z - RZ), R, RY, 2 * RZ, "ball", n=6, floor=0.4, lean=0.04,
                corner=0.5)
    for k, (dy, dz, w0, w1) in enumerate(((0.04, 0.26, 0.2, 0.12), (0.22, 0.18, 0.16, 0.09))):  # хохолок: 2 ступени
        b = hc + V((0, 0.04 + 0.13 * k, RZ - 0.1 - 0.05 * k))
        blunt(a, "crest", b, b + V((0, dy + 0.06, dz)), w0, w1)
    # лобная ступень: от лба сужается к корню клюва (0.22 → 0.13)
    taper(a, "head", hc + V((0, -0.24, -0.08)), broot_l, 0.24, 0.14, 0.2, 0.13, cut=0.28)
    taper(a, "beak", broot_l - bdir_l * 0.06, broot_l + bdir_l * BEAK, 0.12, 0.075, 0.1, 0.07, cut=0.25)
    # переливчатое горлышко (горжетка): ряды чешуек-пёрышек уголком вниз, малиновые и фиолетовые вперемешку;
    # верхний ряд впереди нижнего (черепица), соседние чешуйки на разной глубине — грани не совпадают
    rows = ((-0.2, (-0.12, 0.0, 0.12)), (-0.28, (-0.18, -0.06, 0.06, 0.18)), (-0.36, (-0.12, 0.0, 0.12)),
            (-0.43, (-0.06, 0.06)))
    for r, (dz, xs) in enumerate(rows):
        for i, x in enumerate(xs):
            key = ("gorget", "sheen")[(r + i) % 2]
            yf = front_y(th, x, hc.z + dz) - 0.018 * (len(rows) - r) - 0.012 * (i % 2)
            _scale(a, key, x, hc.z + dz, 0.135, 0.13, yf, yf + 0.12, up=0.014 * (i % 2))
    for s in S2:
        eye2(a, tuple(hc + V((s * 0.2, -RY - 0.005, 0.1))), 0.125, (s * 0.25, -1, 0.05), None, s, "head", "dark",
             look=(-s * 0.75, -0.7), lid=0.22, lid_tilt=2, brow_tilt=9, brow_lift=0.1)
        # надутая щека: шар из трёх ярусов (ярусы горизонтальны, как у головы) под глазом у корня клюва,
        # наполовину утоплен — выпирает вбок-вперёд и раздувает низ головы шире лба (не плоский «пятак» спереди)
        cx = s * 0.3
        A.body(a, "cheek", (cx, front_y(th, cx, hc.z - 0.15) + 0.08, hc.z - 0.31), 0.18, 0.16, 0.32, "ball", n=3,
               floor=0.55, corner=0.5)
    with_matrix(a, None)

    face_point(a, tuple(hm @ (hc + V((0, -0.4, 0.0)))))
    closeup(a, tuple(mb @ V((-0.4, -0.2, 0.0))))
    a.pose = {"WingL": ((0, -20, 0), (0, 0, 0)), "WingR": ((0, 20, 0), (0, 0, 0)), "Head": ((-6, 0, 6), (0, 0, 0)),
              "Tail": ((10, 0, 0), (0, 0, 0))}
    return a


ITEM = ("BeeHummingbird", bee_hummingbird, "Колибри-шмель", "Common")
