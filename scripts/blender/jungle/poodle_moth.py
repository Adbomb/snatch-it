"""Мотылёк-пудель (PoodleMoth, Rare, №19 каталога docs/BOSS6_CATALOG.md) — пушистый шар-мотылёк, подстриженный
как пудель: круглое тело-клубок из крупных ярусов белого меха (кольца больших «долек» с волнистым нижним краем, ярус
свисает над ярусом ниже), отдельная круглая голова на пышном воротнике, бритая мордочка, большой кудрявый помпон-
чубчик на макушке и висячие пушистые «уши» по бокам. Бритые лапки с сиреневыми помпонами висят над бутоном, на кончике
брюшка — помпон-хвостик. Сидит на розовом бутоне и машет над ним бледно-сиреневыми крыльями (две пары, без «глазков» —
не путать с Фонарницей: у неё узкое тело и огромная морда). Признаки венесуэльского мотылька-пуделя: густой белый мех
крупными ярусами, перистые кремовые усики-ёлочки, огромные чёрные глаза-купола, две пары крыльев, шесть лапок.
Эмоция — щенячий восторг: рот до ушей с языком, глаза блестят, брови подняты дугой.
Бутон — видимая часть Haze (D58), подставка в игре скрыта.
Зависит от jungle_kit (creature_kit, anatomy_kit, art_style).
"""

import math
import os
import sys

from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jungle_kit import *  # noqa: E402,F401,F403


def lobe(a, key, c, d, rm, out, inn, w, h, tilt=-12.0, corner=0.34, hexa=False):
    """Пушистая «долька» меха: восьмигранный брусок с крупными скосами углов (круглая на вид), ось — луч d из центра
    c, от радиуса inn (внутри тела) до out (снаружи); tilt < 0 — лицевая грань чуть кверху: нижний край дольки
    выступает дальше верхнего и свисает над ярусом ниже, как подстриженная шерсть. hexa — шестигранная долька (втрое
    меньше видна: верх и низ клубка, воротник) — экономия треугольников. Выпуклая деталь."""
    d = V(d).normalized()
    m = Matrix.Translation(V(c) + d * rm) @ A.facing(d) @ Matrix.Rotation(math.radians(tilt), 4, "X")
    if hexa:
        pts = [(-w / 2, 0.0), (-w * 0.27, -h / 2), (w * 0.27, -h / 2), (w / 2, 0.0), (w * 0.27, h / 2),
               (-w * 0.27, h / 2)]
    else:
        pts = S.octagon(-w / 2, w / 2, -h / 2, h / 2, min(w, h) * corner)
    a.prism(key, pts, -(out - rm), rm - inn, axis="y", bevel=0, matrix=m)


def fur_ring(a, key, c, R, phi, n, w, h, off=0.0, depth=0.38, lift=0.06, tilt=-12.0, hexa=False):
    """Ярус меха: кольцо из n долек на широте phi (°) шара радиуса R с центром c; off — сдвиг по кругу (доли шага),
    у соседних ярусов долек «кирпичиком». Угол 0 — к игроку (−y)."""
    p = math.radians(phi)
    for i in range(n):
        th = 2 * math.pi * (i + off) / n
        d = (math.sin(th) * math.cos(p), -math.cos(th) * math.cos(p), math.sin(p))
        lobe(a, key, c, d, R - 0.1, R + lift, R - depth, w, h, tilt, hexa=hexa)


def seg(a, key, p0, p1, width, thick, normal):
    """Выпуклый брусок от p0 к p1: ширина width в плоскости, поперечной normal, толщина thick вдоль normal."""
    p0, p1 = V(p0), V(p1)
    d = p1 - p0
    x = d.normalized()
    y = V(normal) - x * V(normal).dot(x)
    y.normalize()
    z = x.cross(y)
    m = Matrix(((x.x, y.x, z.x, p0.x), (x.y, y.y, z.y, p0.y), (x.z, y.z, z.z, p0.z), (0, 0, 0, 1)))
    a.box(key, 0.0, d.length, -thick / 2, thick / 2, -width / 2, width / 2, bevel=0, matrix=m)


def feather(a, base, tip, normal, barbs=3, reach=0.26):
    """Перистый усик-ёлочка: кремовый стержень и по бокам короткие тупые бородки, наклонённые к кончику (широкие,
    не волоски: ширина и толщина ≥ 0.08); плоскость усика смотрит по normal — к игроку."""
    base, tip = V(base), V(tip)
    x = (tip - base).normalized()
    nrm = V(normal) - x * V(normal).dot(x)
    nrm.normalize()
    side = x.cross(nrm)
    seg(a, "antD", base, tip, 0.11, 0.1, nrm)
    for i in range(barbs):
        f = 0.35 + 0.57 * i / (barbs - 1)
        p = base.lerp(tip, f)
        ln = reach * (1.0 - 0.5 * f) + 0.06
        for s in S2:
            d = (side * s + x * 0.6).normalized()
            seg(a, "antC", p - d * 0.03, p + d * ln, 0.09, 0.08 + 0.004 * (i % 2), nrm)


def _hull(pts):
    """Выпуклая оболочка точек (u, v) — контур крыла всегда выпуклый (выпуклая деталь)."""
    pts = sorted(set(pts))

    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])

    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def wing(a, s, root, yaw, pitch, outline, veins, th=0.08):
    """Крыло мотылька в плоскости x–z (вид спереди), раскрыто в стороны: root — основание внутри тела, yaw — разворот
    назад (°, малый — крылья видны и спереди, и в 3/4), pitch — наклон верха назад (°). Всё крыло бледно-сиреневое,
    три широких жилки от основания (выступают с обеих сторон); «глазков» нет."""
    m = Matrix.Translation(V(root)) @ Matrix.Rotation(math.radians(s * yaw), 4, "Z") @ Matrix.Rotation(
        math.radians(-pitch), 4, "X")
    pts = _hull([(s * u, v) for u, v in outline])
    a.prism("wing", pts, -th / 2, th / 2, axis="y", bevel=0, matrix=m)
    for k, ((u0, v0), (u1, v1)) in enumerate(veins):
        seg(a, "wingV", m @ V((s * u0, 0, v0)), m @ V((s * u1, 0, v1)), 0.11, th + 0.06 + 0.006 * k,
            m.to_3x3() @ V((0, 1, 0)))
    return m


def poodle_moth():
    a = new("PoodleMoth", {"fur": ("FBF8F3", True), "furS": ("E8DFF3", True), "face": ("FFF1E4", True),
                           "top": ("D8C2F8", True), "pom": ("CC82EE", False), "brow": ("B57FE6", False),
                           "eye": ("15151C", False), "wing": ("DCC6F8", False), "wingV": ("A983E0", False),
                           "antC": ("F3E2B4", False), "antD": ("D9B877", False), "bud": ("FF7FB0", True),
                           "budD": ("E8558F", True), "sepal": ("63C24F", False), "sepalV": ("3F8E37", False)})
    t = rare_stand(a, 1.55)

    # ── бутон-опора (видимая часть Haze, в игре подставка скрыта): розовое яйцо, четыре тёмных лепестка-обёртки,
    #    у основания четыре маленьких зелёных чашелистика (единственный зелёный акцент)
    part(a, "Haze", "Stand", (0, 0, t))
    A.body(a, "bud", (0, 0, t), 0.5, 0.5, 0.66, "egg", n=4, bevel=0)
    for k in range(4):
        ang = math.radians(90 * k)
        n = V((math.sin(ang), -math.cos(ang), 0))
        tg = V((-n.y, n.x, 0))
        mp = Matrix(((tg.x, n.x, 0, 0), (tg.y, n.y, 0, 0), (0, 0, 1, t + 0.04), (0, 0, 0, 1))) @ Matrix.Translation(
            (0, 0.45, 0)) @ Matrix.Rotation(math.radians(12), 4, "X")
        a.prism("budD", [(-0.2, 0.0), (0.2, 0.0), (0.25, 0.3), (0.0, 0.55), (-0.25, 0.3)], -0.04 - 0.004 * k,
                0.05, axis="y", bevel=0, matrix=mp)
    for k in range(4):
        ang = math.radians(45 + 90 * k)
        d = V((math.cos(ang), math.sin(ang), 0))
        flat_leaf(a, "sepal", "sepalV", V((0, 0, t + 0.1 + 0.004 * k)) + d * 0.3,
                  V((0, 0, t + 0.03 + 0.004 * k)) + d * 0.84, 0.36, 0.07, (0, 0, 1))  # наклонён: грани не совпадают

    # ── тело: круглый пушистый клубок Ø ≈ 2 (ширина : высота ≈ 1 : 1.05). Ядро — ступенчатый шар, поверх — четыре
    #    яруса больших долек меха по кругу шара (широкий живот посередине), долька свисает над ярусом ниже
    C = V((0, 0.08, t + 1.48))
    R = 0.95
    part(a, "Body", "Stand", tuple(C))
    A.body(a, "fur", (C.x, C.y, C.z - 0.9), 0.8, 0.8, 1.84, "ball", n=5, floor=0.42, corner=0.42, bevel=0)
    for phi, n, key, w, h, off, hx in ((-54, 5, "furS", 0.76, 0.6, 0.5, True), (-20, 9, "fur", 0.66, 0.62, 0.0, False),
                                       (14, 10, "fur", 0.62, 0.62, 0.5, False), (46, 6, "furS", 0.74, 0.6, 0.0, True)):
        fur_ring(a, key, C, R, phi, n, w, h, off, hexa=hx)
    # пышный воротник на шее: кольцо долек под головой — голова отделена от тела, как грудка пуделя
    fur_ring(a, "furS", V((0, -0.02, t + 2.12)), 0.56, -6, 8, 0.5, 0.36, 0.5, depth=0.3, lift=0.08, tilt=-20,
             hexa=True)

    # ── шесть бритых лапок: из-под живота наружу коленом и вниз; на конце — большой сиреневый помпон, висит над
    #    подставкой рядом с бутоном (не на розовом)
    for s in S2:
        part(a, "Leg" + ("L" if s > 0 else "R"), "Body", (s * 0.42, 0.08, t + 0.88))
        for k, deg in enumerate((52, 96, 140)):
            r = math.radians(deg)
            d = V((s * math.sin(r), -math.cos(r), 0))
            hip = V((0, 0.08, t + 0.92)) + d * 0.48
            knee = V((0, 0.08, t + 0.74 + 0.012 * k)) + d * 0.92
            foot = V((0, 0.08, t + 0.46 + 0.01 * k)) + d * 1.0
            side = V((-d.y, d.x, 0))  # бруски-голени: бедро и голень заходят друг в друга в колене на 0.06
            seg(a, "furS", hip, knee + (knee - hip).normalized() * 0.06, 0.15, 0.15 - 0.004 * k, side)
            seg(a, "furS", knee - (foot - knee).normalized() * 0.06, foot, 0.14, 0.14 - 0.004 * k, side)
            knob(a, "pom", tuple(foot + V((0, 0, -0.06))), 0.19, n=3 if k < 2 else 2)  # задний почти не виден

    # ── брюшко назад-вниз из клубка, на кончике — помпон-хвостик пуделя (заходит в брюшко на 0.12)
    part(a, "Abdomen", "Body", (0, 0.6, t + 1.12))
    da = V((0, 0.85, -0.53)).normalized()
    ma = Matrix.Translation((0, 0.58, t + 1.14)) @ da.to_track_quat("Z", "Y").to_matrix().to_4x4()
    A.body(a, "furS", (0, 0, 0), 0.34, 0.32, 0.74, "egg", n=3, floor=0.5, bevel=0, matrix=ma)
    knob(a, "pom", tuple(ma @ V((0, 0, 0.8))), 0.18, n=3)

    # ── крылья: две пары раскрыты в стороны за клубком (видны спереди и в 3/4), передние выше и больше
    fore = [(0.0, -0.1), (0.6, -0.22), (1.25, 0.25), (1.46, 0.9), (1.38, 1.48), (1.04, 1.8), (0.6, 1.76),
            (0.02, 0.65)]
    fore_v = [((0.15, 0.15), (0.98, 1.42)), ((0.2, 0.05), (1.22, 0.9)), ((0.25, -0.03), (1.0, 0.24))]
    hind = [(0.0, 0.15), (0.6, 0.32), (1.15, 0.22), (1.34, -0.15), (1.15, -0.58), (0.65, -0.72), (0.12, -0.35)]
    hind_v = [((0.15, 0.06), (1.05, 0.0)), ((0.15, -0.05), (0.76, -0.5)), ((0.1, 0.02), (0.6, 0.24))]
    for s in S2:
        sd = "L" if s > 0 else "R"
        root = (s * 0.3, 0.55, t + 1.82)
        part(a, "Wing" + sd, "Body", root)
        wing(a, s, root, 4, 14, fore, fore_v)
        root = (s * 0.28, 0.62, t + 1.3)
        part(a, "Hind" + sd, "Body", root)
        wing(a, s, root, 12, 0, hind, hind_v)

    # ── голова: отдельный круглый шар (≈ 1/3 роста) на воротнике; мордочка бритая, как у пуделя
    part(a, "Head", "Body", (0, -0.08, t + 2.3))
    ht = A.body(a, "face", (0, -0.105, t + 2.1), 0.56, 0.5, 1.06, "ball", n=5, floor=0.45, corner=0.42, bevel=0)
    # огромные чёрные глаза мотылька: купол из двух ступеней-восьмиугольников, большой и малый блик утоплены в купол
    for s in S2:
        ex, ez = s * 0.27, t + 2.76
        nrm = V((s * 0.4, -1, 0.04)).normalized()
        ey = min(front_y(ht, ex, ez + dz) for dz in (-0.2, 0.0, 0.2))  # самый выпуклый ярус: купол перед ним
        me = Matrix.Translation((ex, ey + 0.02, ez)) @ A.facing(nrm)
        a.prism("eye", S.octagon(-0.225, 0.225, -0.25, 0.25, 0.11), -0.05, 0.24, axis="y", bevel=0, matrix=me)
        a.prism("eye", S.octagon(-0.165, 0.165, -0.19, 0.19, 0.08), -0.1, -0.02, axis="y", bevel=0, matrix=me)
        a.prism("glint", S.octagon(-0.13, 0.02, 0.0, 0.15, 0.04), -0.12, -0.08, axis="y", bevel=0, matrix=me)
        a.box("glint", 0.04, 0.11, -0.115, -0.08, -0.13, -0.06, bevel=0, matrix=me)
        # бровь — светлая сиреневая дуга над глазом, поднята (восторг)
        arc = []
        for i, (u, dz) in enumerate(((-0.2, 0.3), (0.0, 0.37), (0.2, 0.3))):
            x = ex + s * u
            arc.append((x, front_y(ht, x, ez + dz) - 0.01 - 0.004 * i, ez + dz))
        kchain(a, "brow", arc, [0.085] * 3, [0.08] * 3, up=(0, -1, 0), cut=0.2, overlap=0.3)
    # рот до ушей: дуга-улыбка, посередине открыт — тёмный рот и розовый язык
    mz = t + 2.4
    arc = []
    for i, (x, dz) in enumerate(((-0.32, 0.09), (-0.21, 0.03), (-0.08, 0.0), (0.08, 0.0), (0.21, 0.03),
                                 (0.32, 0.09))):
        arc.append((x, front_y(ht, x, mz + dz) - 0.004 - 0.005 * (i % 2), mz + dz))
    kchain(a, "mouth", arc, [0.075] * len(arc), [0.08] * len(arc), up=(0, -1, 0), cut=0.2, overlap=0.3)
    fy = front_y(ht, 0.0, mz - 0.06)
    a.prism("mouth", S.octagon(-0.17, 0.17, mz - 0.15, mz + 0.02, 0.05), fy - 0.02, fy + 0.12, axis="y", bevel=0)
    a.prism("tongue", S.octagon(-0.1, 0.1, mz - 0.14, mz - 0.07, 0.03), fy - 0.035, fy + 0.08, axis="y", bevel=0)
    # большой кудрявый чубчик-помпон на макушке: широкая приплюснутая кудряшка и две поменьше по бокам,
    #    сиреневато-белый (отделяется от головы); шире, чем выше — не «цилиндр»
    #    — маленький клубок, как тело: ядро и кольцо круглых долек
    A.body(a, "top", (0, -0.02, t + 3.0), 0.24, 0.24, 0.5, "ball", n=3, floor=0.55, corner=0.45, bevel=0)
    fur_ring(a, "top", V((0, -0.02, t + 3.22)), 0.27, 12, 7, 0.3, 0.3, 0.5, depth=0.2, lift=0.06, tilt=-14)
    # висячие пушистые «уши» по бокам головы, как у стриженого пуделя: обрамляют мордочку спереди
    for s in S2:
        A.body(a, "top", (s * 0.64, -0.1, t + 2.28), 0.21, 0.2, 0.64, "egg", n=3, floor=0.5, corner=0.45, bevel=0)
    # перистые усики-ёлочки из лба, вверх-наружу мимо чубчика
    for s in S2:
        feather(a, (s * 0.28, -0.24, t + 3.0), (s * 0.88, -0.5, t + 3.66), (0, -1, 0.2))  # по бокам чубчика

    face_point(a, (0, -0.62, t + 2.66))
    closeup(a, (0.35, -0.85, t + 1.45))
    a.pose = {"WingL": ((0, -20, 0), (0, 0, 0)), "WingR": ((0, 20, 0), (0, 0, 0)),
              "HindL": ((0, 14, 0), (0, 0, 0)), "HindR": ((0, -14, 0), (0, 0, 0)),
              "Head": ((0, -10, 0), (0, 0, 0)), "LegL": ((0, -14, 0), (0, 0, 0)), "LegR": ((0, 14, 0), (0, 0, 0)),
              "Abdomen": ((14, 0, 0), (0, 0, 0))}
    return a


ITEM = ("PoodleMoth", poodle_moth, "Мотылёк-пудель", "Rare")
