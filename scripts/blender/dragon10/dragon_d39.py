"""Король-дракон (босс 10), v3 — в стиле D39, как Сфинкс: блоки квадратного сечения с острыми рёбрами, ступенчатый
силуэт, чистые яркие цвета, скруглённые квадраты-контуры на крупных деталях (art_style), мелкие накладки гладкие.

Строится тем же набором, что boss4_sphinx.py: бруски (box, bar), восьмигранники со срезанными углами (oct_x/y/z),
пирамиды (frustum), плоские фигуры (prism, extrude), рамки (frame). Приёмы Сфинкса: слоёные полосы разного цвета,
тёмные канты под краями, медальоны «золото — кант — камень — блик», лицо из плоских накладок (белок, радужка, зрачок,
блик, ресница, тяжёлые брови-бруски). Подвижные части — группы Art (a.group), как у Сфинкса.
Лицо смотрит в −y, верх +z, L — +x. Единица — модель; в игре ×3.
"""

import math
import os
import sys

from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import art_style as S  # noqa: E402

V = Vector
Q = {"pleats": 7, "spots": True, "orb": 3}  # детализация (game — игровая копия)


def colors(a):
    for key, code in (("scale", "D9323F"), ("scaleL", "EE5A5A"), ("belly", "F6D58A"), ("gold", "F8B21C"),
                      ("mantle", "6A2E9C"), ("mantleS", "552283"), ("ermine", "F8F4EC"), ("wing", "B8283F"),
                      ("wingS", "961E36"), ("ivory", "FFF1D2"), ("velvet", "C4213A"), ("scaleD", "9C1C2C")):
        a.paint(key, code, rings=True)
    for key, code in (("rim", "B97A10"), ("goldL", "FFD75A"), ("bellyD", "D9A44E"), ("ruby", "C42450"),
                      ("rubyL", "F07A98"), ("sapph", "2F6BFF"), ("sapphL", "9FC0FF"), ("emer", "1FA874"),
                      ("emerL", "8BE8C0"), ("eye", "FFF6DC"), ("iris", "F2A20C"), ("pupil", "2A120C"),
                      ("glint", "FFFFFF"), ("lash", "4A1414"), ("brow", "6E1420"), ("mouth", "5A1420"),
                      ("tooth", "FFF8EA"), ("dark", "2A1218"), ("spot", "2A2230"), ("groove", "A8202E")):
        a.paint(key, code)


def tilt(c, axis, deg):
    c = V(c)
    return Matrix.Translation(c) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-c)


def bar(a, key, p0, p1, w, h=None, bevel=S.BEVEL, ext=0.0):
    """Брусок квадратного сечения w × h от p0 до p1 (ext — удлинить с обоих концов: стык звеньев)."""
    p0, p1 = V(p0), V(p1)
    d = p1 - p0
    up = "Y" if abs(d.normalized().z) > 0.95 else "Z"
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("X", up).to_matrix().to_4x4()
    h = h or w
    L = d.length / 2 + ext
    a.box(key, -L, L, -w / 2, w / 2, -h / 2, h / 2, bevel=bevel, matrix=m)
    return m


def oct_y(a, key, x0, x1, z0, z1, cut, y0, y1, matrix=None, bevel=S.BEVEL):
    a.prism(key, S.octagon(x0, x1, z0, z1, cut), y0, y1, axis="y", matrix=matrix, bevel=bevel)


def oct_z(a, key, x0, x1, y0, y1, cut, z0, z1, matrix=None, bevel=S.BEVEL):
    a.prism(key, S.octagon(x0, x1, y0, y1, cut), z0, z1, axis="z", matrix=matrix, bevel=bevel)


def roct(cx, cz, r):
    """Правильный восьмиугольник радиуса r — «пиксельный круг»."""
    return S.octagon(cx - r, cx + r, cz - r, cz + r, r * (2 - math.sqrt(2)))


def sx(s, u, v):
    return sorted((s * u, s * v))


def medallion(a, c, r, gem="ruby", gemL="rubyL", face=-1, depth=0.14):
    """Медальон как у Сфинкса: золотой восьмигранник, тёмный кант, камень, светлый блик. Лицом к face·y."""
    x, y, z = c
    lo, hi = sorted((y, y + face * depth))
    a.prism("gold", roct(x, z, r), lo, hi, axis="y")
    yy = y + face * depth
    a.prism("rim", roct(x, z, r + 0.035), *sorted((y + face * 0.02, yy - face * 0.03)), axis="y", bevel=0)
    a.prism(gem, roct(x, z, r * 0.66), *sorted((yy, yy + face * 0.07)), axis="y")
    a.prism(gemL, roct(x - r * 0.18, z + r * 0.18, r * 0.24), *sorted((yy + face * 0.07, yy + face * 0.085)),
            axis="y", bevel=0)


HEAD_M = Matrix.Translation((0, -0.55, 8.0)) @ Matrix.Scale(1.15, 4) @ Matrix.Translation((0, 0.55, -8.0))


# ── голова и корона ──────────────────────────────────────────────────────────────────────────────────────────
def head(a):
    a.group = "Head"
    a.transform = HEAD_M
    # череп сбоку — восьмиугольник со срезами; спереди плоское «лицо» для глаз
    a.prism("scale", [(8.0, -1.0), (8.0, 0.5), (8.4, 0.85), (9.45, 0.8), (9.82, 0.4), (9.82, -0.78), (9.62, -1.05),
                      (8.95, -1.05)], -1.0, 1.0, axis="x")
    # верхняя морда: низ ровный, верх скатом к носу; по бокам ступень «брылей»
    a.prism("scale", [(7.96, -0.98), (7.96, -2.78), (8.5, -2.9), (8.7, -2.74), (8.96, -1.3), (8.96, -0.98)],
            -0.78, 0.78, axis="x")
    for s in (1, -1):
        a.box("scaleL", *sx(s, 0.77, 0.93), -2.25, -0.95, 7.96, 8.5)
        a.box("scale", *sx(s, 0.92, 1.06), -1.45, -0.6, 7.96, 8.72)
    # нос: приподнятая площадка и ноздри; гребешок из трёх ступенчатых щитков
    a.box("scaleD", -0.56, 0.56, -2.96, -2.58, 8.46, 8.74)
    for s in (1, -1):
        a.box("dark", *sx(s, 0.16, 0.42), -2.985, -2.955, 8.53, 8.66, bevel=0)
    for y0, y1, z in ((-1.42, -1.08, 8.92), (-1.88, -1.55, 8.84), (-2.34, -2.0, 8.76)):
        a.box("scaleD", -0.22, 0.22, y0, y1, z, z + 0.14)
    # рот: тёмная линия по боку, уголок вверх (ухмылка), клыки
    for s in (1, -1):
        a.box("lash", *sx(s, 0.775, 0.8), -2.7, -1.0, 7.93, 7.99, bevel=0)
        bar(a, "lash", (s * 0.95, -1.02, 7.96), (s * 0.97, -0.62, 8.2), 0.035, 0.07, bevel=0)
        a.frustum("tooth", (*sx(s, 0.44, 0.64), -2.62, -2.42), (s * 0.54, s * 0.54, -2.52, -2.52), 7.97, 7.56, bevel=0)
        a.frustum("tooth", (*sx(s, 0.5, 0.64), -1.98, -1.84), (s * 0.57, s * 0.57, -1.91, -1.91), 7.97, 7.74, bevel=0)
    a.box("mouth", -0.62, 0.62, -2.55, -0.8, 7.9, 7.95, bevel=0)
    # глаза на «лице»: золотистый белок, оранжевая радужка, вертикальный зрачок, блик, нижняя ресница
    for s in (1, -1):
        a.box("eye", *sx(s, 0.18, 0.9), -1.12, -1.04, 9.0, 9.52, bevel=0.02)
        c = s * 0.56
        a.box("iris", c - 0.21, c + 0.21, -1.14, -1.118, 9.02, 9.5, bevel=0)
        a.box("pupil", c - 0.055, c + 0.055, -1.156, -1.136, 9.06, 9.46, bevel=0)
        a.box("glint", c - 0.19, c - 0.1, -1.165, -1.15, 9.33, 9.43, bevel=0)
        a.box("lash", *sx(s, 0.18, 0.9), -1.126, -1.1, 8.96, 9.0, bevel=0)
    # надбровный козырёк и тяжёлые брови: внутренний край ниже — строгий королевский взгляд
    a.box("scale", -1.02, 1.02, -1.2, -0.95, 9.58, 9.8)
    for s in (1, -1):
        a.box("brow", *sx(s, 0.12, 1.0), -1.29, -1.17, 9.5, 9.72, bevel=0, matrix=tilt((s * 0.56, -1.23, 9.61), "Y", -s * 15))
        a.frustum("scaleD", (*sx(s, 0.86, 1.08), -1.26, -1.04), (s * 1.07, s * 1.07, -1.15, -1.15), 9.68, 10.05,
                  matrix=tilt((s * 0.97, -1.15, 9.7), "Y", -s * 25))
    # гребни-плавники за щеками (ступенчатые), уши-плавники
    for s in (1, -1):
        a.extrude("scaleD", [(8.15, -0.55), (8.85, -0.55), (9.35, 0.65), (8.82, 0.42), (8.35, 0.95)], *sx(s, 1.0, 1.12),
                  axis="x")
        a.extrude("scale", [(8.3, -0.3), (8.7, -0.3), (8.95, 0.45), (8.62, 0.35)], *sx(s, 1.12, 1.2), axis="x")
    # гребень на затылке: три ступенчатых плавника по средней линии (силуэт сзади и сбоку)
    for z0, y0, h in ((9.55, 0.5, 0.42), (9.05, 0.82, 0.38), (8.5, 0.86, 0.32)):
        a.extrude("scaleD", [(z0, y0), (z0 + h, y0 + 0.12), (z0 + h * 0.4, y0 + 0.5), (z0 - 0.1, y0 + 0.3)], -0.07, 0.07,
                  axis="x")
    # рога: звенья квадратного сечения назад-вверх, золотое кольцо у основания, острие
    for s in (1, -1):
        pts = [V((s * 0.72, -0.3, 9.62)), V((s * 0.92, 0.2, 10.05)), V((s * 1.12, 0.78, 10.38)), V((s * 1.24, 1.3, 10.86))]
        for (p0, p1), w in zip(zip(pts, pts[1:]), (0.44, 0.36, 0.28)):
            bar(a, "ivory", p0, p1, w, ext=w * 0.35)
        bar(a, "gold", pts[0] + (pts[1] - pts[0]) * 0.25, pts[0] + (pts[1] - pts[0]) * 0.6, 0.54)
        bar(a, "rim", pts[0] + (pts[1] - pts[0]) * 0.18, pts[0] + (pts[1] - pts[0]) * 0.27, 0.5, bevel=0)
        tip = pts[3] + (pts[3] - pts[2]).normalized() * 0.55
        m = Matrix.Translation(pts[3]) @ (tip - pts[3]).to_track_quat("Z", "Y").to_matrix().to_4x4()
        a.frustum("ivory", (-0.13, 0.13, -0.13, 0.13), (0, 0, 0, 0), -0.05, 0.6, matrix=m)


def crown(a):
    a.group = "Head"
    a.transform = HEAD_M
    oct_z(a, "rim", -0.93, 0.93, -1.05, 0.67, 0.34, 9.76, 9.86)  # нижний кант
    oct_z(a, "gold", -0.88, 0.88, -1.0, 0.62, 0.32, 9.84, 10.21)  # обод
    oct_z(a, "goldL", -0.91, 0.91, -1.03, 0.65, 0.33, 10.19, 10.26)  # верхний кант
    # бархатная шапка двумя ступенями, держава
    oct_z(a, "velvet", -0.72, 0.72, -0.85, 0.48, 0.26, 9.8, 10.42)
    oct_z(a, "velvet", -0.46, 0.46, -0.55, 0.2, 0.16, 10.42, 10.58)
    oct_z(a, "gold", -0.14, 0.14, -0.31, -0.03, 0.05, 10.58, 10.7)
    oct_z(a, "gold", -0.2, 0.2, -0.37, 0.03, 0.07, 10.7, 11.0)
    a.prism("ruby", roct(0.0, 10.85, 0.1), -0.41, -0.37, axis="y")
    # дуги поверх шапки: бруски от обода к державе
    for x0, y0 in ((0.0, -0.98), (0.0, 0.6), (0.86, -0.18), (-0.86, -0.18)):
        bar(a, "gold", (x0, y0, 10.2), (x0 * 0.35, -0.17 + (y0 + 0.17) * 0.35, 10.62), 0.11, bevel=0.01)
    # зубцы: передний высокий с рубином, передние боковые с сапфирами, боковые с изумрудами, задние малые
    a.prism("gold", [(-0.32, 10.16), (0.32, 10.16), (0.32, 10.52), (0.0, 11.0), (-0.32, 10.52)], -1.08, -0.97, axis="y")
    medallion(a, (0.0, -1.07, 10.5), 0.17, depth=0.04)
    for s in (1, -1):
        m = tilt((s * 0.62, -0.82, 10.2), "Z", s * 38)
        a.prism("gold", [(s * 0.62 - 0.22, 10.15), (s * 0.62 + 0.22, 10.15), (s * 0.62 + 0.22, 10.46), (s * 0.62, 10.76),
                         (s * 0.62 - 0.22, 10.46)], -0.92, -0.8, axis="y", matrix=m)
        a.prism("sapph", roct(s * 0.62, 10.43, 0.1), -0.97, -0.92, axis="y", matrix=m)
        a.prism("sapphL", roct(s * 0.6, 10.46, 0.035), -0.985, -0.97, axis="y", matrix=m, bevel=0)
        a.prism("gold", [(10.14, -0.42), (10.14, 0.08), (10.44, 0.08), (10.66, -0.17), (10.44, -0.42)],
                *sx(s, 0.86, 0.98), axis="x")
        a.prism("emer", [(10.33, -0.27), (10.33, -0.07), (10.49, -0.07), (10.49, -0.27)], *sx(s, 0.98, 1.02), axis="x")
        a.prism("gold", [(10.13, 0.18), (10.13, 0.56), (10.38, 0.56), (10.52, 0.37), (10.38, 0.18)], *sx(s, 0.66, 0.78),
                axis="x", matrix=tilt((s * 0.72, 0.37, 10.2), "Z", -s * 40))


def jaw(a):
    a.group = "Jaw"
    a.transform = HEAD_M
    a.prism("scale", [(7.44, -0.6), (7.44, -2.34), (7.66, -2.6), (7.94, -2.6), (7.94, -0.6)], -0.7, 0.7, axis="x")
    a.box("belly", -0.5, 0.5, -2.36, -0.72, 7.37, 7.45)
    for s in (1, -1):
        a.frustum("tooth", (*sx(s, 0.42, 0.56), -2.45, -2.3), (s * 0.49, s * 0.49, -2.38, -2.38), 7.9, 8.1, bevel=0)
    a.transform = None


# ── шея, тело, броня ─────────────────────────────────────────────────────────────────────────────────────────
def neck(a):
    a.transform = None
    a.group = "Neck"
    oct_z(a, "scale", -0.88, 0.88, -0.78, 0.72, 0.26, 6.5, 7.36)
    oct_z(a, "scale", -0.78, 0.78, -1.02, 0.46, 0.22, 7.3, 8.06)
    for (z0, z1), (y0, w) in zip(((6.68, 6.94), (6.98, 7.24), (7.42, 7.66), (7.7, 7.94)),
                                 ((-0.78, 0.52), (-0.78, 0.5), (-1.02, 0.44), (-1.02, 0.42))):
        a.box("belly", -w, w, y0 - 0.15, y0 + 0.04, z0, z1)
        a.box("bellyD", -w + 0.04, w - 0.04, y0 - 0.12, y0 + 0.02, z0 - 0.04, z0, bevel=0)
    for z, y in ((7.0, 0.7), (7.72, 0.44)):
        a.frustum("scaleD", (-0.17, 0.17, y - 0.2, y + 0.14), (0, 0, y + 0.42, y + 0.42), z - 0.1, z + 0.45)


def torso(a):
    a.group = "Pelvis"
    oct_z(a, "scale", -1.36, 1.36, -0.88, 0.98, 0.36, 2.45, 3.46)
    for z0, z1, w in ((2.62, 2.9, 0.54), (2.95, 3.24, 0.66)):  # щитки живота под поясом
        a.box("belly", -w, w, -1.03, -0.82, z0, z1)
        a.box("bellyD", -w + 0.05, w - 0.05, -1.0, -0.84, z0 - 0.05, z0, bevel=0)
    oct_z(a, "gold", -1.42, 1.42, -1.04, 1.04, 0.38, 3.28, 3.56)  # пояс
    oct_z(a, "rim", -1.39, 1.39, -1.01, 1.01, 0.37, 3.23, 3.3, bevel=0)
    medallion(a, (0.0, -1.03, 3.42), 0.3)
    for x0, x1, z0, ang in ((-0.42, 0.42, 2.58, 0), (0.62, 1.3, 2.7, 22), (-1.3, -0.62, 2.7, -22)):  # набедренники
        m = tilt(((x0 + x1) / 2, -0.95, 3.25), "Z", ang)
        oct_y(a, "gold", x0, x1, z0, 3.27, 0.1, -1.08, -0.92, matrix=m)
        a.box("rim", x0 + 0.04, x1 - 0.04, -1.1, -0.94, z0 - 0.06, z0, bevel=0, matrix=m)

    a.group = "Torso"
    oct_z(a, "scale", -1.26, 1.26, -0.96, 0.9, 0.34, 3.44, 4.78)  # живот — уже груди
    oct_z(a, "scale", -1.88, 1.88, -1.16, 1.06, 0.46, 4.72, 6.26)  # грудь
    oct_z(a, "scale", -1.56, 1.56, -0.92, 0.96, 0.36, 6.2, 6.62)  # плечевой пояс
    for i, (z0, w) in enumerate(((3.58, 0.8), (3.88, 0.86), (4.18, 0.9), (4.48, 0.92))):  # щитки живота
        a.box("belly", -w, w, -1.13, -0.93, z0, z0 + 0.26)
        a.box("bellyD", -w + 0.05, w - 0.05, -1.1, -0.95, z0 - 0.05, z0, bevel=0)
    # нагрудник: две грудные пластины ступенью, кант по краю, киль с медальоном
    for s in (1, -1):
        oct_y(a, "gold", *sx(s, 0.1, 1.62), 4.98, 6.16, 0.26, -1.38, -1.12)
        oct_y(a, "rim", *sx(s, 0.06, 1.66), 4.94, 6.2, 0.27, -1.34, -1.2, bevel=0)
        oct_y(a, "gold", *sx(s, 0.28, 1.46), 5.06, 5.56, 0.12, -1.48, -1.36)
        a.box("goldL", *sx(s, 0.3, 1.44), -1.5, -1.47, 5.5, 5.56, bevel=0)
    a.box("gold", -0.16, 0.16, -1.52, -1.3, 4.92, 6.2)
    medallion(a, (0.0, -1.52, 5.86), 0.3)
    # ворот: золото в два яруса
    oct_z(a, "gold", -1.12, 1.12, -1.0, 0.8, 0.32, 6.58, 6.88)
    oct_z(a, "rim", -1.16, 1.16, -1.04, 0.84, 0.34, 6.51, 6.59, bevel=0)


# ── руки, скипетр ────────────────────────────────────────────────────────────────────────────────────────────
ARMS = {1: (V((2.08, 0.0, 5.95)), V((2.78, 0.42, 4.78)), V((2.02, -0.28, 3.86))),
        -1: (V((-2.08, 0.0, 5.95)), V((-2.6, 0.0, 4.62)), V((-2.66, -0.62, 3.96)))}


def arm(a, s, sfx):
    Sh, E, W = ARMS[s]
    a.group = "UpperArm" + sfx
    bar(a, "scale", Sh + V((0, 0, 0.25)), E, 0.84, ext=0.3)
    # наплечник: три золотых слоя ступенью наружу-вниз (как полосы платка Сфинкса), шипы, рубин
    m = tilt((s * 2.0, 0.0, 6.3), "Y", -s * 18)
    for (x0, x1, z0, z1, w, key) in ((1.4, 2.6, 6.3, 6.66, 0.86, "gold"), (1.48, 2.72, 6.02, 6.3, 0.92, "rim"),
                                      (1.56, 2.86, 5.66, 6.02, 0.98, "gold")):
        a.box(key, *sx(s, x0, x1), -w, w, z0, z1, matrix=m)
    a.box("goldL", *sx(s, 1.58, 2.84), -0.99, 0.99, 5.98, 6.02, bevel=0, matrix=m)
    for y in (-0.4, 0.4):
        a.frustum("gold", (*sx(s, 1.85, 2.15), y - 0.15, y + 0.15), (*sx(s, 2.05, 2.05), y, y), 6.66, 7.15, matrix=m)
    medallion(a, (s * 2.25, -0.98, 5.84), 0.17, depth=0.06)
    a.group = "Forearm" + sfx
    bar(a, "scale", E, W, 0.74, ext=0.25)
    bar(a, "gold", E + (W - E) * 0.45, E + (W - E) * 0.92, 0.86)
    bar(a, "rim", E + (W - E) * 0.4, E + (W - E) * 0.46, 0.82, bevel=0)
    bar(a, "goldL", E + (W - E) * 0.91, E + (W - E) * 0.97, 0.9, bevel=0)
    tip = E + V((s * 0.25, 0.75, 0.15))
    mm = Matrix.Translation(E) @ (tip - E).to_track_quat("Z", "Y").to_matrix().to_4x4()
    a.frustum("ivory", (-0.15, 0.15, -0.15, 0.15), (0, 0, 0, 0), 0.0, 0.7, matrix=mm)
    a.group = "Hand" + sfx
    d = (W - E).normalized()
    F = W + d * 0.38
    mf = bar(a, "scale", W, F + d * 0.18, 0.78)
    for k in (-1, 1):  # желобки между тремя пальцами на торце кулака
        a.box("groove", 0.27, 0.295, k * 0.13 - 0.012, k * 0.13 + 0.012, -0.36, 0.36, bevel=0, matrix=mf)
    for k in (-1, 0, 1):  # когти к ладони
        kp = mf @ V((0.3, k * 0.25, -0.3))
        a.frustum("ivory", (kp.x - 0.08, kp.x + 0.08, kp.y - 0.08, kp.y + 0.08), (kp.x, kp.x, kp.y - 0.1, kp.y - 0.1),
                  kp.z - 0.05, kp.z - 0.38, bevel=0)


def scepter(a):
    a.group = "Scepter"
    x, y = -2.68, -0.86
    a.box("gold", x - 0.08, x + 0.08, y - 0.08, y + 0.08, 0.2, 5.52)
    for z in (1.0, 2.0, 3.0, 4.5):
        a.box("rim", x - 0.12, x + 0.12, y - 0.12, y + 0.12, z, z + 0.1)
    oct_z(a, "gold", x - 0.17, x + 0.17, y - 0.17, y + 0.17, 0.06, 0.0, 0.24)
    oct_z(a, "gold", x - 0.22, x + 0.22, y - 0.22, y + 0.22, 0.08, 5.5, 5.66)
    for r, z0, z1 in (((0.2, 5.66, 5.78), (0.31, 5.78, 6.1), (0.2, 6.1, 6.22)) if Q["orb"] == 3 else
                      ((0.26, 5.66, 5.8), (0.31, 5.8, 6.22))):  # держава-рубин «пиксельным шаром»
        oct_z(a, "ruby", x - r, x + r, y - r, y + r, r * 0.42, z0, z1)
    a.box("rubyL", x - 0.2, x - 0.08, y - 0.325, y - 0.31, 5.98, 6.06, bevel=0)
    for dx, dy_ in ((0.33, 0), (-0.33, 0), (0, 0.33), (0, -0.33)):
        a.box("gold", x + dx - 0.035, x + dx + 0.035, y + dy_ - 0.035, y + dy_ + 0.035, 5.7, 6.18)
    a.frustum("gold", (x - 0.1, x + 0.1, y - 0.1, y + 0.1), (x, x, y, y), 6.28, 6.62)


# ── ноги ─────────────────────────────────────────────────────────────────────────────────────────────────────
def leg(a, s, sfx):
    dy = -0.22 if s > 0 else 0.26
    a.group = "Thigh" + sfx
    a.extrude("scale", [(1.5, -0.6 + dy), (1.5, 0.5 + dy * 0.5), (2.2, 0.95), (3.12, 0.9), (3.28, 0.2), (3.02, -0.72),
                        (2.2, -0.95 + dy)], *sx(s, 0.5, 1.78), axis="x")
    oct_y(a, "gold", *sx(s, 0.68, 1.6), 1.58, 2.18, 0.15, -1.14 + dy, -0.9 + dy)
    oct_y(a, "rim", *sx(s, 0.64, 1.64), 1.54, 2.22, 0.16, -1.08 + dy, -0.95 + dy, bevel=0)
    a.frustum("gold", (*sx(s, 1.02, 1.26), -1.1 + dy, -0.95 + dy), (*sx(s, 1.14, 1.14), -1.3 + dy, -1.3 + dy), 1.95, 2.45)
    a.group = "Shin" + sfx
    m = tilt((s * 1.14, dy, 0.4), "X", -10)
    a.box("scale", *sx(s, 0.76, 1.52), -0.46 + dy, 0.38 + dy, 0.38, 1.62, matrix=m)
    a.box("gold", *sx(s, 0.86, 1.42), -0.58 + dy, -0.44 + dy, 0.62, 1.34, matrix=m)
    a.frustum("ivory", (*sx(s, 1.02, 1.26), 0.34 + dy, 0.48 + dy), (*sx(s, 1.14, 1.14), 0.85 + dy, 0.85 + dy), 0.62, 0.48)
    a.group = "Foot" + sfx
    oct_z(a, "scale", *sx(s, 0.62, 1.66), -1.25 + dy, 0.3 + dy, 0.2, 0.0, 0.44)
    for k in range(3):  # пальцы с желобками и когтями, как лапы Сфинкса
        c = s * (0.8 + k * 0.34)
        a.box("scaleL", c - 0.15, c + 0.15, -1.62 + dy, -1.15 + dy, 0.02, 0.36)
        a.frustum("ivory", (c - 0.1, c + 0.1, -1.66 + dy, -1.58 + dy), (c, c, -1.92 + dy, -1.92 + dy), 0.3, 0.04, bevel=0)
    a.box("groove", *sx(s, 0.96, 0.98), -1.63 + dy, -1.14 + dy, 0.06, 0.37, bevel=0)
    a.box("groove", *sx(s, 1.3, 1.32), -1.63 + dy, -1.14 + dy, 0.06, 0.37, bevel=0)
    a.frustum("ivory", (*sx(s, 1.04, 1.24), 0.26 + dy, 0.4 + dy), (*sx(s, 1.14, 1.14), 0.68 + dy, 0.68 + dy), 0.3, 0.05)


# ── хвост ────────────────────────────────────────────────────────────────────────────────────────────────────
TAIL = [V(p) for p in ((0, 0.95, 2.85), (0, 1.9, 1.9), (0.4, 2.7, 0.9), (1.4, 3.35, 0.5), (2.7, 3.3, 0.42),
                       (3.6, 2.5, 0.4), (3.95, 1.4, 0.38))]
TAIL_W = (0.98, 0.84, 0.7, 0.58, 0.47, 0.37)
TAIL_GROUPS = ("Tail1", "Tail1", "Tail2", "Tail2", "Tail3", "Tail4")


def tail(a):
    for i, (p0, p1) in enumerate(zip(TAIL, TAIL[1:])):
        a.group = TAIL_GROUPS[i]
        w = TAIL_W[i]
        m = bar(a, "scale", p0, p1, w, w * 0.9, ext=w * 0.3)
        L = (p1 - p0).length
        a.box("scaleD", -L / 2 - w * 0.3, -L / 2 - w * 0.2, -w * 0.52, w * 0.52, -w * 0.47, w * 0.47, bevel=0, matrix=m)
        a.frustum("gold", (-w * 0.22, w * 0.22, -w * 0.18, w * 0.18), (w * 0.28, w * 0.28, 0, 0), w * 0.42,
                  w * 0.42 + 0.22 + w * 0.42, matrix=m)
    a.group = "Tail4"
    end = TAIL[-1]
    d = (TAIL[-1] - TAIL[-2]).normalized()
    m = Matrix.Translation(end) @ Matrix.Rotation(math.atan2(d.x, -d.y), 4, "Z")
    a.extrude("gold", [(-0.3, 0.05), (0.06, 0.05), (0.06, -0.38), (0.4, -1.08), (0.74, -0.38), (0.74, 0.05),
                       (0.4, 0.15)], -0.09, 0.09, axis="x", matrix=m @ Matrix.Translation((0, 0, -0.04)))
    a.prism("rim", [(0.12, -0.3), (0.68, -0.3), (0.4, -0.86)], -0.1, 0.1, axis="x",
            matrix=m @ Matrix.Translation((0, 0, -0.04)), bevel=0)
    for s in (1, -1):
        a.prism("ruby", roct(0.36, -0.28, 0.1), *sx(s, 0.1, 0.14), axis="x", matrix=m @ Matrix.Translation((0, 0, -0.04)))


# ── крылья ───────────────────────────────────────────────────────────────────────────────────────────────────
# Крыло в своей плоскости (u — наружу, v — вверх), корень в (0, 0); панели перепонки ступенями чередуют цвет.
WING = {"E": (1.5, 1.45), "W": (2.95, 2.85), "F": [(5.6, 2.15), (5.95, 0.0), (4.85, -1.85), (3.2, -2.65)], "T": (0.6, -1.95)}


def wing(a, s, sfx):
    root = V((s * 0.82, 1.2, 6.42))
    M = (Matrix.Translation(root) @ Matrix.Rotation(math.radians(s * 32), 4, "Z") @
         Matrix.Rotation(math.radians(-s * 6), 4, "Y") @ Matrix.Scale(s, 4, V((1, 0, 0))))
    E, W, T = V((*WING["E"],)), V((*WING["W"],)), V((*WING["T"],))
    F = [V(f) for f in WING["F"]]

    def notch(p, q):
        mid = (p + q) / 2
        return mid + (W - mid) * 0.3

    def P(v2, y=0.0):
        return M @ V((v2.x, y, v2.y))

    a.group = "WingHand" + sfx
    for i, (p, q) in enumerate(zip(F, F[1:])):
        dy = 0.035 * (i % 2)
        a.extrude("wing" if i % 2 == 0 else "wingS", [tuple(W), tuple(p), tuple(notch(p, q)), tuple(q)],
                  -0.05 + dy, 0.05 + dy, axis="y", matrix=M)
    for f in F:
        bar(a, "scaleD", P(W), P(f), 0.2, 0.18, ext=0.05)
        tip = P(f) + (P(f) - P(W)).normalized() * 0.45
        mm = Matrix.Translation(P(f)) @ (tip - P(f)).to_track_quat("Z", "Y").to_matrix().to_4x4()
        a.frustum("ivory", (-0.09, 0.09, -0.09, 0.09), (0, 0, 0, 0), 0.0, 0.45, matrix=mm, bevel=0)
    a.box("gold", -0.24, 0.24, -0.24, 0.24, -0.24, 0.24, matrix=Matrix.Translation(P(W)))
    up = P(W) + V((0, -0.15, 0.7))
    mm = Matrix.Translation(P(W)) @ (up - P(W)).to_track_quat("Z", "Y").to_matrix().to_4x4()
    a.frustum("gold", (-0.13, 0.13, -0.13, 0.13), (0, 0, 0, 0), 0.2, 0.75, matrix=mm)
    a.group = "WingArm" + sfx
    a.extrude("wing", [tuple(W), tuple(F[-1]), tuple(notch(F[-1], T)), tuple(T), (0.0, 0.0), tuple(E)], -0.05, 0.05,
              axis="y", matrix=M)
    bar(a, "scaleD", P(V((0, 0))), P(E), 0.34, 0.3, ext=0.1)
    bar(a, "scaleD", P(E), P(W), 0.28, 0.26, ext=0.08)
    a.box("gold", -0.24, 0.24, -0.24, 0.24, -0.24, 0.24, matrix=Matrix.Translation(P(E)))


# ── мантия ───────────────────────────────────────────────────────────────────────────────────────────────────
def cape(a):
    a.group = "Cape"
    cy, top, hem = 0.28, 6.18, 1.72
    n = Q["pleats"]
    for k in range(n):  # складки — наклонные бруски по дуге, через одну глубже и темнее
        th = -72 + 144 * k / (n - 1)
        o = 0.04 * (k % 2)
        r0, r1 = 1.32 + 0.16 * (k % 2), 2.12 + 0.26 * (k % 2)
        m = tilt((0, cy, 0), "Z", -th)
        key = "mantle" if k % 2 == 0 else "mantleS"
        w = 0.5 * 6 / (n - 1)
        a.frustum(key, (-w, w, cy + r1 - 0.14, cy + r1 + 0.14), (-w * 0.76, w * 0.76, cy + r0 - 0.12, cy + r0 + 0.12),
                  hem + 0.32 + o, top + o, matrix=m)
        a.box("gold", -w - 0.02, w + 0.02, cy + r1 - 0.17, cy + r1 + 0.17, hem + 0.24 + o, hem + 0.33 + o, matrix=m)
        a.box("ermine", -w - 0.03, w + 0.03, cy + r1 - 0.18, cy + r1 + 0.18, hem + o, hem + 0.25 + o, matrix=m)
        if Q["spots"]:
            a.box("spot", -0.06, 0.06, cy + r1 + 0.18, cy + r1 + 0.2, hem + 0.06 + o, hem + 0.18 + o, bevel=0, matrix=m)
    # герб на спине: золотой щит, алое поле, корона из трёх зубцов
    yb = cy + 2.12 - (2.12 - 1.32) * (4.45 - hem - 0.32) / (top - hem - 0.32) + 0.16
    sh = [(-0.6, 5.0), (0.6, 5.0), (0.6, 4.45), (0.0, 3.92), (-0.6, 4.45)]
    mc = tilt((0, yb, 4.45), "X", 11)  # герб наклонён вместе со складкой
    a.prism("gold", sh, yb, yb + 0.12, axis="y", matrix=mc)
    a.prism("velvet", [(-0.46, 4.9), (0.46, 4.9), (0.46, 4.5), (0.0, 4.08), (-0.46, 4.5)], yb + 0.12, yb + 0.16,
            axis="y", bevel=0, matrix=mc)
    a.extrude("gold", [(-0.3, 4.38), (0.3, 4.38), (0.34, 4.72), (0.16, 4.55), (0.0, 4.8), (-0.16, 4.55), (-0.34, 4.72)],
            yb + 0.16, yb + 0.2, axis="y", bevel=0, matrix=mc)
    # горностаевый воротник по плечам и спине, пятна; застёжки-медальоны спереди
    a.frame("ermine", S.octagon(-1.86, 1.86, -0.72, 1.32, 0.5), 0.46, 6.2, 6.645, axis="z")
    for x, y in ((-1.5, 0.95), (-0.55, 1.18), (0.55, 1.18), (1.5, 0.95), (1.62, 0.2), (-1.62, 0.2))[: 6 if Q["spots"] else 2]:
        a.box("spot", x - 0.07, x + 0.07, y - 0.11, y + 0.11, 6.64, 6.66, bevel=0)
    for s in (1, -1):
        medallion(a, (s * 1.15, -0.72, 6.42), 0.16, depth=0.06)


PARTS = ["Head", "Jaw", "Neck", "Torso", "Pelvis", "Cape", "UpperArmL", "UpperArmR", "ForearmL", "ForearmR", "HandL",
         "HandR", "Scepter", "ThighL", "ThighR", "ShinL", "ShinR", "FootL", "FootR", "Tail1", "Tail2", "Tail3", "Tail4",
         "WingArmL", "WingArmR", "WingHandL", "WingHandR"]


def build(quality="hero"):
    """quality: hero — концепт (фаска 0.012 на всех деталях); game — игровая копия: у деталей меньше 0.45 фаски нет
    (с игровой дистанции её не видно, а треугольников у бруска с фаской втрое больше)."""
    orig = S._bevel
    Q.update(pleats=7, spots=True, orb=3)
    if quality == "game":
        Q.update(pleats=5, spots=False, orb=2)

        def small(bm, bevel):
            co = [v.co for v in bm.verts]
            if max(max(c[i] for c in co) - min(c[i] for c in co) for i in range(3)) >= 0.7:
                orig(bm, bevel)
        S._bevel = small
    try:
        return _build()
    finally:
        S._bevel = orig


def _build():
    a = S.Art("Boss10_Dragon", ring_z0=5.0)
    frustum = a.frustum

    def spike(key, bottom, top, z0, z1, axis="z", bevel=S.BEVEL, matrix=None):  # острия — без фаски
        if top[1] - top[0] < 1e-6 and top[3] - top[2] < 1e-6:
            bevel = 0
        return frustum(key, bottom, top, z0, z1, axis=axis, bevel=bevel, matrix=matrix)

    a.frustum = spike
    colors(a)
    head(a)
    crown(a)
    jaw(a)
    neck(a)
    torso(a)
    cape(a)
    for s, sfx in ((1, "L"), (-1, "R")):
        arm(a, s, sfx)
        leg(a, s, sfx)
        wing(a, s, sfx)
    scepter(a)
    tail(a)
    return a
