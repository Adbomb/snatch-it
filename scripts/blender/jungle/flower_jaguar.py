"""Ягуар-клумба (FlowerJaguar, Epic, №22 каталога docs/BOSS6_CATALOG.md) — коренастый золотисто-рыжий ягуар, у
которого вместо пятен по всему телу распустились крупные цветы-розетки шести цветов (розовые, фиолетовые, жёлтые,
белые, красные, синие — с контрастными серединками): на спине, боках, плечах, груди, лапах, бёдрах, голове и хвосте,
а кончик хвоста зацвёл бутоном. Признаки вида: мощное тело с широкой грудью и плечами на коротких толстых лапах,
крупные круглые уши на углах головы, длинный хвост крючком, розетки по всей шкуре, светлая морда с розовым носом
и толстыми усами. Эмоция — хитрое довольство: веки прикрыты, взгляд вбок, одна бровь поднята, ухмылка одним уголком.
Стоит наискось на подставке (тело повёрнуто на YAW, голова — к игроку): спереди видны и морда, и цветущий бок.
Зелёный — только листики-воротничок у бутона. Правка владельца 2026-11-25: розетки по всему телу, крупные и разные.
Зависит от jungle_kit (creature_kit, anatomy_kit, art_style, v4_kit).
"""

import math
import os
import sys

from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jungle_kit import *  # noqa: E402,F401,F403

YAW = 25  # поворот тела на подставке (°): голова к +x, левый (−x) бок с цветами смотрит в камеру игрока
# цвет розетки → цвет серединки (контраст)
ROSES = {"petP": "coreY", "petV": "coreY", "petY": "petR", "petW": "coreO", "petR": "coreY", "petB": "petW"}


def rosette_pts(r, n, spin=0.0):
    """Контур плоского цветка: n квадратных лепестков (по две точки на конце) и выемки между ними."""
    pts = []
    for i in range(n):
        th = math.radians(spin) + i * 2 * math.pi / n
        half = math.pi / n
        pts.append((r * 0.45 * math.cos(th - half), r * 0.45 * math.sin(th - half)))
        for k in (-0.62, 0.62):
            pts.append((r * math.cos(th + k * half), r * math.sin(th + k * half)))
    return pts


def rosette(a, key, c, normal, r, spin=0.0, sink=0.035, up=0.06, n=5):
    """Цветок-розетка на шкуре: плоская пластина-контур (утоплена в тело на sink, наружу на up) и выпуклая серединка.
    Низкополигонально: ~55 видимых треугольников, без фаски."""
    m = Matrix.Translation(V(c)) @ V(normal).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    a.extrude(key, rosette_pts(r, n, spin), -sink, up, axis="z", bevel=0, matrix=m)
    core = [(r * 0.34 * math.cos(math.radians(spin) + i * 2 * math.pi / n),
             r * 0.34 * math.sin(math.radians(spin) + i * 2 * math.pi / n)) for i in range(n)]
    a.prism(ROSES[key], core, up - 0.02, up + 0.045, bevel=0, matrix=m)  # серединка — многоугольник по лепесткам


def paw(a, x, y, t):
    """Лапа-подушка: брусок стопы и три пальца-бруска светлого цвета (дешевле A.foot: пальцы — простые бруски)."""
    taper(a, "jag", (x, y + 0.1, t + 0.075), (x, y - 0.2, t + 0.075), 0.36, 0.36, 0.15, 0.14, cut=0.22)
    for o in (-0.115, 0.0, 0.115):
        a.box("jagL", x + o - 0.048, x + o + 0.048, y - 0.29, y - 0.14, t + 0.004, t + 0.105 - 0.012 * (o == 0),
              bevel=0)


def flower_jaguar():
    """Ягуар-клумба: шкура-клумба из крупных розеток шести цветов, короткие мощные лапы, длинный хвост с бутоном."""
    a = new("FlowerJaguar", {"jag": ("F4A93A", True), "jagL": ("FFE8C0", False), "jagD": ("9A4E1E", False),
                             "petP": ("FF4FA3", False), "petV": ("A55CFF", False), "petY": ("FFD23F", False),
                             "petW": ("FFFFFF", False), "petR": ("F0303C", False), "petB": ("3D8BFF", False),
                             "coreY": ("FFE14D", False), "coreO": ("FF8A3D", False), "leaf": ("3FAE4A", False)})
    t = epic_stand(a, 1.7)
    G = Matrix.Rotation(math.radians(YAW), 4, "Z")  # всё существо — наискось на подставке

    def P(p):
        return tuple(G @ V(p))

    with_matrix(a, G)
    zb = t + 0.4  # низ тела: лапы короткие
    zt = zb + 0.8  # спина
    zc = (zb + zt) / 2
    # ── лапы: короткие и толстые, под центром масс; передние под широкими плечами ──
    legs = (("LegFL", 0.38, -0.58, 0.34), ("LegFR", -0.38, -0.58, 0.34), ("LegBL", 0.36, 0.56, 0.38),
            ("LegBR", -0.36, 0.56, 0.38))
    for nm, x, y, w in legs:
        part(a, nm, "Stand", P((x, y, zb + 0.1)))
        taper(a, "jag", (x, y, zb + 0.3), (x, y, t + 0.08), w, 0.3, w * 0.95, 0.3, up=(0, -1, 0))
        paw(a, x, y, t)
        s = 1 if x > 0 else -1
        if y < 0:  # спереди на передних лапах — розетка (не фиолетовая: сливалась бы с подставкой)
            rosette(a, "petW" if s > 0 else "petP", (x, y - 0.21, t + 0.27), (0, -1, 0.1), 0.15, 18 * s, sink=0.06)
        else:  # сзади на бёдрах — крупная розетка (видна со спины)
            rosette(a, "petY" if s > 0 else "petP", (s * 0.27, 0.84, zc - 0.04), (s * 0.3, 1, 0.1), 0.2, 10 * s,
                    sink=0.06)
    # ── тело: бочка, плечи шире и выше бёдер (мощная грудь), снизу — светлое брюхо ──
    part(a, "Body", "Stand", P((0, 0, zc)))
    body = [(-0.86, zb + 0.14), (-0.86, zt - 0.24), (-0.7, zt - 0.08), (0.7, zt - 0.08), (0.86, zt - 0.26),
            (0.86, zb + 0.16), (0.62, zb), (-0.64, zb)]
    layered(a, "jag", body, [(0.42, 1, 1)], (0.0, zc))
    a.prism("jag", S.octagon(zb + 0.02, zt + 0.07, -0.84, -0.24, 0.13), -0.62, 0.62, axis="x")  # широкие плечи
    a.prism("jag", S.octagon(zb + 0.06, zt + 0.02, 0.28, 0.84, 0.1), -0.52, 0.52, axis="x")  # бёдра
    a.prism("jag", S.octagon(zb + 0.08, zt - 0.12, -0.42, 0.42, 0.1), -0.48, 0.48, axis="x")  # бока
    a.box("jagL", -0.36, 0.36, -0.62, 0.6, zb - 0.1, zb + 0.12)  # брюхо: толстая светлая плита между лапами
    # ── розетки по всему телу ──
    for s in S2:
        k1, k2, k3 = ("petP", "petB", "petY") if s > 0 else ("petV", "petR", "petW")  # бока — разная раскладка
        # на плече — наискось вперёд-наружу: лепестки выходят за бок и видны спереди
        rosette(a, k1, (s * 0.6, -0.68, zc + 0.06), (s * 1.0, -0.8, 0.12), 0.29, 8 * s, sink=0.08)
        rosette(a, k2, (s * 0.48, 0.0, zc - 0.04), (s, 0, 0), 0.27, 20 + 18 * s)  # середина бока
        rosette(a, k3, (s * 0.52, 0.5, zc + 0.05), (s, 0.2, 0), 0.26, 10)  # бедро
    for y, z, r, k, sp, tx in ((-0.54, zt + 0.07, 0.26, "petY", 8, -0.45), (0.0, zt - 0.08, 0.26, "petB", 30, 0.45),
                               (0.56, zt + 0.02, 0.25, "petV", 0, -0.45)):  # спина: наклонены к бокам — не щепки
        rosette(a, k, (0.0, y, z + 0.03), (tx, 0, 1), r, sp, sink=0.06)
    rosette(a, "petR", (0.0, -0.86, zb + 0.2), (0, -1, -0.05), 0.3, 0)  # большая на груди
    # ── голова ≈ треть тела: один круглый блок, крупные круглые уши на углах, светлая морда ──
    neck = V((0, -0.76, zt - 0.05))
    part(a, "Head", "Body", P(neck))
    HG = G @ tilt(neck, "Z", -YAW)  # голова повёрнута к игроку (−y)
    with_matrix(a, HG)
    hc = V((0, -1.08, zt + 0.12))
    A.body(a, "jag", (0, hc.y, hc.z - 0.4), 0.47, 0.42, 0.8, "ball", n=4, t0=0.1, t1=0.86, floor=0.5, corner=0.42)
    A.snout(a, "jagL", tuple(hc + V((0, -0.3, -0.14))), (0, -1, -0.04), 0.21, 0.42, 0.34, 0.3, 0.26, nose_key="pink",
            nose=0.4, mouth=0)
    fy = hc.y - 0.51  # перёд морды
    for s in S2:
        # веки прикрыты (довольство), взгляд вбок (хитрость); левая (+x) бровь высоко поднята, правая — ровно
        eye2(a, tuple(hc + V((s * 0.18, -0.39, 0.08))), 0.12, (s * 0.25, -1, 0.05), "sly", s, "jag", "jagD",
             look=(0.45, -0.1), lid=0.44, lid_tilt=-6, brow_tilt=-10 if s > 0 else 0,
             brow_lift=0.75 if s > 0 else 0.2)
        em = Matrix.Translation(hc + V((s * 0.3, 0.06, 0.47))) @ Matrix.Rotation(math.radians(-14 * s), 4, "Y")
        a.prism("jag", S.octagon(-0.18, 0.18, -0.18, 0.18, 0.09), -0.05, 0.05, axis="y", matrix=em)  # круглое ухо
        a.prism("jagD", S.octagon(-0.11, 0.11, -0.1, 0.1, 0.05), -0.07, -0.04, axis="y", bevel=0, matrix=em)
        for k in range(2):  # усы: короткие толстые бруски по бокам морды (тонкие мерцают)
            zz = hc.z - 0.2 + 0.09 * k
            a.box("white", s * 0.19, s * 0.39, fy + 0.05, fy + 0.12, zz - 0.035, zz + 0.035, bevel=0,
                  matrix=tilt((s * 0.19, fy + 0.08, zz), "Y", s * (10 - 22 * k)))
    # ухмылка одним уголком: короткая ровная черта под носом, левый (+x) уголок задран на 0.09; рот закрыт
    mz = hc.z - 0.235
    a.box("mouth", -0.025, 0.025, fy - 0.022, fy + 0.02, mz, hc.z - 0.16, bevel=0)  # черта от носа
    a.box("mouth", -0.1, 0.05, fy - 0.022, fy + 0.02, mz - 0.03, mz + 0.03, bevel=0)
    a.box("mouth", 0.0, 0.13, fy - 0.026, fy + 0.016, -0.03, 0.03, bevel=0,
          matrix=Matrix.Translation((0.04, 0, mz)) @ Matrix.Rotation(math.radians(-36), 4, "Y"))
    rosette(a, "petP", tuple(hc + V((0.26, -0.18, 0.38))), (0.35, -0.6, 0.75), 0.27, 12, sink=0.06)  # венок у уха
    rosette(a, "petY", tuple(hc + V((-0.45, -0.12, -0.12))), (-1, -0.45, 0), 0.27, 0, sink=0.06)  # на щеке
    face = tuple(HG @ (hc + V((0, -0.45, 0.02))))
    with_matrix(a, G)
    # ── длинный хвост крючком, по нему розетки на оси, кончик зацвёл бутоном ──
    part(a, "Tail", "Body", P((0, 0.8, zt - 0.16)))
    tp = [(0, 0.68, zt - 0.2), (0, 1.36, zt - 0.06), (0.08, 1.64, zt + 0.36), (0.04, 1.56, zt + 0.84)]
    kchain(a, "jag", tp, [0.22, 0.19, 0.17, 0.15], up=(1, 0, 0))
    rosette(a, "petW", (0.0, 1.04, zt + 0.0), (-0.3, -0.12, 1), 0.17, 0, sink=0.05)  # сверху на хвосте
    for s, k in ((1, "petB"), (-1, "petR")):  # пара по бокам вертикальной части, на её оси
        rosette(a, k, (0.065 + s * 0.08, 1.6, zt + 0.6), (s, 0, 0), 0.15, 18, sink=0.05)
    tip = V(tp[-1])
    for i in range(4):  # зелёный воротничок — единственный зелёный акцент
        ang = math.radians(45 + i * 90)
        d = V((math.cos(ang), math.sin(ang), 0.35)).normalized()
        a.box("leaf", -0.05, 0.05, -0.035, 0.035, 0.0, 0.17, bevel=0,
              matrix=Matrix.Translation(tip + V((0, 0, 0.02))) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4())
    petals(a, tuple(tip + V((0, 0, 0.1))), 5, 0.28, 0.19, ("petV", "petP"), "coreY", 0.1, normal=(0, -0.2, 1),
           lift=30, bevel=0)  # бутон на кончике хвоста
    with_matrix(a, None)
    face_point(a, face)
    closeup(a, P((-0.5, 0.0, zc + 0.1)), eye_off=(-2.3, -1.2, 0.9))
    lift = Matrix.Rotation(math.radians(-28), 3, G.to_3x3() @ V((1, 0, 0))).to_euler()  # шаг передней лапой
    a.pose = {"Head": ((0, 0, 16), (0, 0, 0)), "Tail": ((0, 0, -22), (0, 0, 0)),
              "LegFL": (tuple(math.degrees(v) for v in lift), (0, 0, 0.06))}
    return a


ITEM = ("FlowerJaguar", flower_jaguar, "Ягуар-клумба", "Epic")
