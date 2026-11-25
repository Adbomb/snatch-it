"""Босс 6 «Джунгли» — Королева-мухоловка, концепт v2 (D64 шаг 3): одна модель в позах стойка / сон / бой / поражение.

Образ (правки владельца к v1): огромное хищное растение-королева, вросшее в землю (не ходит — поворачивается на месте,
D64 п. 5). Анатомия настоящей мухоловки, без силуэта «платья»: внизу — бурый приплюснутый клубень-купол (скошенные
ярусы, бугры, корни в землю) и розетка огромных светлых листьев из-под него, веером на земле; из клубня — толстый тёмный стебель-ствол с узлами;
на стебле — золотой обруч-амулет с розовым самоцветом. Руки — светлые лозы (читаются на тёмном стебле) с ладонями
из трёх крупных листьев, отведены в стороны (на фоне тёмных стебля и мантии). Сзади — тёмная мантия из трёх
коротких изогнутых листов-плащей с прожилками и золотой застёжкой, разведённых в стороны (стебель сзади виден). Три уровня светлоты: лицо и бутон головы светлые, створки,
стебель и мантия тёмные, розетка светлая.
Голова — бутон со светлой маской лица (глаза-бруски, веки, ресницы, брови с эмоцией), над ним золотая корона с
розовыми самоцветами и венчик крупных розовых лепестков. Пасть под лицом — ловушка мухоловки: две короткие округлые
створки на петле (сбоку — полукруг), снаружи тёмно-зелёные с малиновым кантом по краю, внутри ярко-малиновые,
по самому краю — короткие тупые реснички к другой створке; внутри — розовый язык. Венчик — чаша из двух рядов
толстых лепестков, наклонённых вперёд. У подножия — два закрытых бутона-фрейлины без лиц (в бою раскрываются в маленькие
ловушки, тоже без лиц). Без людей, текста и узнаваемых чужих персонажей.

Позы: стойка — пасть приоткрыта, высокомерный прищур; сон — створки сомкнуты (реснички переплетены), голова
склонилась, лепестки сложены, глаза закрыты, роса, «Z»; бой — пасть распахнута, язык наружу, лозы вскинуты, злые
брови, бутоны раскрылись; поражение — увяла: стебель согнулся набок, голова поникла, глаза-крестики, язык набок,
корона на земле, листья опали.

Построение — стиль D39 (art_style): слоёные боковые профили (створки), ступенчатые ярусы со скосами (клубень, бутон),
сужающиеся восьмигранные звенья (стебель, лозы), листья — плоские пластины из звеньев с изломом (изгиб) и сгибом по
жилке, тупые пирамиды (реснички, зубцы короны). Игровая копия ≤ 8 000 треугольников: мелочь без фаски.
Координаты: z вверх, лицо в −y. Зависит от art_style.py и dragon10/v4_kit.py.
"""

import math
import os
import sys

from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "dragon10"))
import art_style as S  # noqa: E402
import v4_kit as K  # noqa: E402

V = Vector
S2 = (1, -1)

PALETTE = {  # ключ: (цвет, кольца D39 на крупных поверхностях)
    "leafL": ("8FD957", True),  # розетка листьев на земле — светлая
    "leaf": ("43B649", True),  # внутренние листья розетки, стебельки бутонов, чашелистики
    "leafD": ("2F9442", True),  # мантия — тёмная: светлые лозы и голова читаются на ней
    "pod": ("6FCB55", True), "podD": ("62BD4B", True),  # бутон головы — между лицом и листом по светлоте
    "trap": ("1F6634", True),  # створки ловушки снаружи — тёмно-зелёные
    "rim": ("E8285A", False),  # малиновый кант по краю створок (как у настоящей мухоловки)
    "stem": ("3B5A2B", True),  # стебель-ствол — тёмный
    "stemD": ("243D1E", False),  # узлы стебля
    "vine": ("BDEB6E", True),  # лозы-руки — светлые на тёмном стебле
    "rib": ("D9F58C", False),  # жилки листьев
    "face": ("A8E86A", False),  # маска лица — светлая
    "maw": ("FF4F80", True),  # нутро ловушки — яркий светлый малиновый
    "mawD": ("C8285E", False),  # прожилки нутра
    "tongue": ("FFA0C0", False),
    "teeth": ("FFF4DA", False),  # реснички
    "root": ("8F5A31", True), "rootD": ("6B4224", False),  # клубень
    "eyeW": ("FFFFFF", False), "pupil": ("1B1B2A", False), "lid": ("3F9A45", False), "brow": ("1E4A26", False),
    "gold": ("F5B21C", True), "goldD": ("C27E0E", False),
    "neonGem": ("FF4FA3", False), "petal": ("FF8FC0", True), "petalD": ("E0569A", False),
    "dark": ("161824", False), "white": ("FFFFFF", False), "dew": ("BFF6FF", False),
}


def key(k):
    K.KEY = k


def new_art(name):
    a = S.Art(name, ring_z0=0.5)
    a.ring = dict(S.RING, core=0.55)  # профиль контура «полка», как у Йети и дракона v7
    for k, (code, rings) in PALETTE.items():
        a.paint(k, code, rings=rings)
    return a


def R(axis, deg):
    return Matrix.Rotation(math.radians(deg), 4, axis)


def T(v):
    return Matrix.Translation(V(v))


def frame(root, d, n):
    """Оси листа: y — вдоль листа (d), z — нормаль лицевой стороны (n), начало — root."""
    y = V(d).normalized()
    z = V(n) - y * V(n).dot(y)
    z.normalize()
    x = y.cross(z)
    r = V(root)
    return Matrix(((x.x, y.x, z.x, r.x), (x.y, y.y, z.y, r.y), (x.z, y.z, z.z, r.z), (0, 0, 0, 1)))


def blunt(a, k, base, tip, w0, w1):
    """Тупая пирамида (ресничка, зубец): квадрат w0 у основания, площадка w1 на конце."""
    base, tip = V(base), V(tip)
    m = T(base) @ (tip - base).to_track_quat("Z", "Y").to_matrix().to_4x4()
    a.frustum(k, (-w0 / 2, w0 / 2, -w0 / 2, w0 / 2), (-w1 / 2, w1 / 2, -w1 / 2, w1 / 2), 0.0, (tip - base).length,
              bevel=0, matrix=m)


# ── Лист: пластина из звеньев с изломами (изгиб по длине) и сгибом по жилке ───────────────────────────────────
def leaf(a, k, M, L, W, thick=0.16, bends=(0.0, 0.0, 0.0), ts=(0.38, 0.72), fold=0.0, rib=None, veins=False,
         tier=None, root_w=0.22, tip_w=0.0, rib_w=0.07):
    """Лист в осях M (y — вдоль, z — лицевая сторона): звенья между долями ts, на стыках излом bends (градусы,
    + к лицевой стороне); fold — сгиб половинок по жилке (+ края вниз, «плащ»; − края вверх, «лодочка»);
    rib — жилка поверх, veins — боковые прожилки, tier — второй ярус (ступень D39) меньшей пластиной."""
    br = [0.0] + list(ts) + [1.0]
    hw = lambda t: W / 2 * max(root_w, math.sin(math.pi * min(max(t, 0.0), 1.0)) ** 0.7) if t < 0.999 else W / 2 * tip_w
    m = M
    for i in range(len(br) - 1):
        t0, t1 = br[i], br[i + 1]
        m = m @ T((0, (t0 - br[i - 1]) * L if i else 0, 0)) @ R("X", bends[i] if i < len(bends) else 0.0)
        last = i == len(br) - 2
        ext = 0.0 if last else min(0.1, thick * 0.6)
        samples = [t0, (t0 + t1) / 2, t1]
        us = [(t - t0) * L for t in samples]
        us[-1] += ext
        ws = [hw(t) for t in samples]
        halves = [(1, R("Y", fold)), (-1, R("Y", -fold))] if fold else [(0, Matrix())]
        for s, mh in halves:
            if s == 0:
                pts = [(w, u) for w, u in zip(ws, us)]
                pts += [(-w, u) for w, u in reversed(list(zip(ws, us)))]
            else:
                pts = [(0.0, us[0])] + [(s * w, u) for w, u in zip(ws, us)] + [(0.0, us[-1])]
            pts = _dedup(pts)
            if len(pts) >= 3:
                a.extrude(k, pts, 0.0, thick, axis="z", matrix=m @ mh)
            if tier and not last:
                tp = [(x * 0.55, us[0] + (u - us[0]) * 0.9 + 0.05) for x, u in pts]
                a.extrude(tier, _dedup(tp), thick * 0.5, thick * 1.45, axis="z", matrix=m @ mh)
            if veins and i > 0 and s != 0:
                um = us[1]
                wv = ws[1] * 0.62
                a.box(rib or "rib", -0.045, 0.045, 0.0, wv, thick * 0.7, thick + 0.05, bevel=0,
                      matrix=m @ mh @ T((s * 0.08, um - wv * 0.3, 0)) @ R("Z", -s * 58))
        if rib:
            u1 = us[-1] - (0.35 * (us[-1] - us[0]) if last else 0.03)  # торец жилки не в плоскости торца звена
            top = thick * (1.45 if tier else 1.0) + 0.07
            rw = rib_w + 0.015 * (i % 2)  # соседние звенья жилки разной ширины — без совпадающих граней
            a.box(rib, -rw, rw, us[0], u1, thick * 0.6, top + 0.01 * (i % 2), bevel=0, matrix=m)


def _dedup(pts):
    out = []
    for p in pts:
        if not out or abs(out[-1][0] - p[0]) + abs(out[-1][1] - p[1]) > 1e-4:
            out.append(p)
    if len(out) > 2 and abs(out[0][0] - out[-1][0]) + abs(out[0][1] - out[-1][1]) < 1e-4:
        out.pop()
    return out


# ── Позы ──────────────────────────────────────────────────────────────────────────────────────────────────────
# lean — наклон стебля вперёд (градусы, + вперёд к −y), side — набок; head — (наклон вниз (+), поворот, крен);
# jaw — (раскрытие верхней створки вверх, нижней вниз); face — выражение; arm — (отвод наружу: 0 — висит, 90 — в
# сторону, 150 — вверх; мах вперёд; сгиб «локтя»; поворот ладони); droop — увядание 0…1; buds — бутоны.
POSES = {
    "stand": dict(lean=4, side=0, head=(-6, 0, 0), jaw=(15, 28), face="smug", tongue="in",
                  arm={1: (80, 24, 34, 0), -1: (84, 22, 38, 15)}, droop=0.0, buds="closed"),
    "sleep": dict(lean=12, side=4, head=(24, 6, 8), jaw=(0, 0), face="sleep", tongue=None,
                  arm={1: (12, 12, 22, 0), -1: (14, 10, 26, 0)}, droop=0.25, buds="sleep"),
    "combat": dict(lean=12, side=0, head=(2, 0, 0), jaw=(28, 46), face="roar", tongue="out",
                   arm={1: (128, 22, 30, 30), -1: (132, 18, 26, -20)}, droop=0.0, buds="open"),
    "defeat": dict(lean=16, side=-18, head=(26, -12, -28), jaw=(8, 38), face="dizzy", tongue="side",
                   arm={1: (8, -6, 6, 0), -1: (12, -4, 8, 0)}, droop=1.0, buds="wilt"),
}

STEM_BASE = V((0, 0, 0.9))
STEM_LEN = [1.55, 1.5, 1.4, 1.1]  # звенья стебля снизу вверх
STEM_W = [2.75, 2.45, 2.2, 2.0, 1.85]  # толстый ствол без «талии»
BUDS = (((-3.75, -4.4), 22), ((3.75, -4.4), -22))  # бутоны-фрейлины: (x, y), поворот — шире, амулет открыт
AMULET_Z = 1.15  # обруч амулета над узлом 1


def skeleton(pose):
    """Матрицы: узлы стебля (n0…n4), голова, плечи лиан."""
    P = POSES[pose]
    M = {}
    m = T(STEM_BASE)
    nodes = [m]
    k = len(STEM_LEN)
    for i, ln in enumerate(STEM_LEN):
        f = (i + 1) / k  # изгиб растёт к верху — стебель гнётся дугой, а не ломается в одном месте
        m = m @ R("X", P["lean"] / k * (0.5 + f)) @ R("Y", P["side"] / k * (0.5 + f)) @ T((0, 0, ln))
        nodes.append(m)
    M["nodes"] = nodes
    hp, hy, hr = P["head"]
    M["head"] = nodes[-1] @ T((0, 0, 0.7)) @ R("Z", hy) @ R("X", hp) @ R("Y", hr)  # hp > 0 — смотрит вниз
    for s in S2:  # лиана растёт по локальной −z (висит вниз), отводится наружу и вперёд
        out, fwd, el, wr = P["arm"][s]
        M[("sh", s)] = nodes[2] @ T((s * 0.95, -0.1, 0.65)) @ R("Y", -s * out) @ R("X", -fwd)
        M[("el", s)] = M[("sh", s)] @ T((0, 0, -1.55)) @ R("X", -el)
        M[("wr", s)] = M[("el", s)] @ T((0, 0, -1.4)) @ R("Z", wr)
    return M


# ── Подножие: клубень и розетка листьев на земле ──────────────────────────────────────────────────────────────
def base(a, P):
    a.transform, a.group = Matrix(), "Base"
    # клубень — широкий приплюснутый бурый купол с выпуклостью, вросший в землю (отдельная масса между листьями):
    # ярусы — скошенные восьмигранники (бока наклонены, а не отвесные — не «торт» и не постамент), центры чуть
    # смещены (комковатый), каждый следующий поуже — ступень D39; на боках — бугры-наросты, в землю уходят корни
    for i, (r0, r1, z0, z1, ox, oy) in enumerate(((2.75, 3.1, 0.0, 0.45, 0.0, 0.0), (3.05, 2.85, 0.4, 0.9, 0.08, -0.05),
                                                  (2.75, 2.35, 0.85, 1.3, 0.12, 0.04), (2.2, 1.75, 1.25, 1.6, 0.05, 0.1),
                                                  (1.65, 1.35, 1.55, 1.85, 0.0, 0.05))):
        key("root" if i % 2 == 0 else "rootD")
        t = math.radians(22.5 * (i % 2))
        K.taper(a, (ox, oy, z0), (ox, oy, z1), 2 * r0, 2 * r1, up=(math.sin(t), -math.cos(t), 0), cut=0.3)
    for ang, h, rr in ((0, 0.95, 0.62), (128, 0.75, 0.55), (236, 0.8, 0.6)):  # бугры между листьями розетки
        d = V((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
        key("rootD" if ang else "root")
        K.taper(a, d * 2.45 + V((0, 0, h)), d * 3.15 + V((0, 0, h + 0.12)), 2 * rr, 1.2 * rr, up=(0, 0, 1), cut=0.3)
    for ang in (62, 180, 300):  # корни уходят в землю
        d = V((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
        key("root")
        K.chain(a, [d * 2.7 + V((0, 0, 0.35)), d * 3.6 + V((0, 0, 0.12)), d * 4.2 + V((0, 0, -0.12))],
                [0.5, 0.34, 0.16], up=(0, 0, 1), cut=0.3, overlap=0.3)
    droop = P["droop"]
    # розетка: 6 огромных светлых листьев веером на земле (спереди один — «ковёр» к игроку); растут из-под клубня
    for i in range(6):
        t = math.radians(30 + 60 * i)
        d = V((math.cos(t), math.sin(t), 0))
        root = d * 2.4 + V((0, 0, 0.7))
        M = frame(root, d + V((0, 0, -0.42)), V((0, 0, 1)))
        ln = 5.3 if i != 4 else 4.7  # корни отодвинуты наружу на 0.95 — общий охват розетки как в v2
        leaf(a, "leafL", M, ln, 2.7, 0.2, bends=(0, 22, 16 - 12 * droop), ts=(0.3, 0.74), rib="rib", veins=False,
             root_w=0.3)
    # внутренних листьев нет: бурый купол клубня виден спереди между листьями розетки


# ── Мантия: три изогнутых листа-плаща за спиной ───────────────────────────────────────────────────────────────
def mantle(a, M, P):
    top = M["nodes"][-1]
    a.transform, a.group = Matrix(), "Mantle"
    droop = P["droop"]
    for dx, ln, w in ((-1, 4.2, 2.45), (0, 4.6, 2.6), (1, 4.2, 2.45)):
        # веер из трёх коротких листов-плащей: разведены в стороны и подняты, кончики загнуты кверху и кончаются выше
        # амулета — сзади между листами и под ними виден тёмный стебель (без силуэта «платья со шлейфом»)
        root = top @ V((dx * 0.75, 0.6, -0.3))
        d = V((dx * 1.8, 0.8 if dx else 1.0, -0.45))
        n = V((dx * 0.9, 1.0, 0.45))
        Mf = frame(root, d, n)
        leaf(a, "leafD", Mf, ln, w, 0.17, bends=(0, -10 - 6 * droop, 50 - 20 * droop), ts=(0.3, 0.66), fold=26,
             rib="rib", veins=True, root_w=0.3, rib_w=0.1)
    # золотая застёжка мантии на затылке стебля
    a.transform = top @ T((0, 0.8, -0.2)) @ R("X", -80)
    a.prism("gold", S.octagon(-0.45, 0.45, -0.45, 0.45, 0.15), -0.06, 0.12)
    a.prism("neonGem", S.octagon(-0.22, 0.22, -0.22, 0.22, 0.07), 0.12, 0.24, bevel=0)
    a.transform = Matrix()


# ── Стебель и амулет ──────────────────────────────────────────────────────────────────────────────────────────
def stem(a, M, P):
    a.transform, a.group = Matrix(), "Stem"
    nodes = M["nodes"]
    pts = [n @ V((0, 0, 0)) for n in nodes]
    key("stem")
    K.chain(a, pts, STEM_W, up=(0, -1, 0), cut=0.3, overlap=0.45)  # нахлёст — без щели под амулетом
    for i in (2, 3):  # узлы-кольца ствола — тёмные пояски (на узле 1 — амулет)
        a.transform = nodes[i]
        w = STEM_W[i] / 2 + 0.14  # выступает над нахлёстом звеньев
        a.prism("stemD", S.octagon(-w, w, -w, w, w * 0.6), -0.14, 0.14)
    # два листочка из узлов — живой стебель, а не колонна
    for i, s in ((2, -1), (3, 1)):
        a.transform = nodes[i]
        w = STEM_W[i] / 2
        leaf(a, "leafL", frame((s * w * 0.8, 0.1, 0.05), (s, -0.25, 0.75), (-s * 0.5, -0.3, 1)), 1.7, 0.85, 0.12,
             bends=(0, 18), ts=(0.5,), rib="rib", root_w=0.3)
    a.transform = Matrix()
    # амулет: золотой обруч на стебле и медальон с самоцветом спереди
    a.group = "Amulet"
    a.transform = nodes[1] @ T((0, 0, AMULET_Z))
    w = (STEM_W[1] + STEM_W[2]) / 4 + 0.1
    a.prism("gold", S.octagon(-w, w, -w, w, w * 0.6), -0.2, 0.2)
    a.prism("goldD", S.octagon(-w - 0.04, w + 0.04, -w - 0.04, w + 0.04, (w + 0.04) * 0.6), -0.06, 0.06, bevel=0)
    a.box("gold", -0.14, 0.14, -w - 0.2, -w + 0.1, -0.55, -0.05, bevel=0)  # ушко
    a.transform = nodes[1] @ T((0, -w - 0.12, AMULET_Z - 0.75)) @ R("X", 90 + 6)
    a.prism("gold", S.octagon(-0.62, 0.62, -0.62, 0.62, 0.22), -0.04, 0.16)
    a.prism("goldD", S.octagon(-0.48, 0.48, -0.48, 0.48, 0.17), 0.16, 0.2, bevel=0)
    a.prism("neonGem", S.octagon(-0.36, 0.36, -0.36, 0.36, 0.13), 0.2, 0.36, bevel=0)
    a.box("white", 0.06, 0.18, 0.1, 0.22, 0.36, 0.38, bevel=0)
    a.transform = Matrix()


# ── Лозы-руки ─────────────────────────────────────────────────────────────────────────────────────────────────
def arm(a, M, s, P):
    side = "L" if s > 0 else "R"
    a.transform, a.group = Matrix(), f"Vine{side}"
    p0 = M[("sh", s)] @ V((0, 0, 0.1))
    p1 = M[("sh", s)] @ V((0, -0.1, -0.8))
    p2 = M[("el", s)] @ V((0, 0, 0))
    p3 = M[("el", s)] @ V((0, -0.1, -0.72))
    p4 = M[("wr", s)] @ V((0, 0, 0))
    key("vine")
    K.chain(a, [p0, p1, p2, p3, p4], [0.91, 0.81, 0.73, 0.65, 0.6], up=(0, -1, 0), cut=0.3, overlap=0.3)
    # усики, закрученные завитком (растение-лиана)
    for j in range(2):
        q = [M[("el", s)] @ V((s * (0.3 + 0.3 * math.cos(t)), 0.3 * math.sin(t), -0.3 - 0.5 * j - 0.1 * t))
             for t in (0.0, 1.6, 3.2)]
        key("vine")
        K.chain(a, [M[("el", s)] @ V((0, 0, -0.3 - 0.5 * j))] + q, [0.2, 0.17, 0.14, 0.1], up=(0, -1, 0),
                cut=0.3, overlap=0.3)
    # ладонь: три светлых листа-пальца веером (крупные — читаются на тёмной мантии), жилки тёмные
    a.transform, a.group = M[("wr", s)], f"Hand{side}"
    a.prism("vine", S.octagon(-0.42, 0.42, -0.42, 0.42, 0.14), -0.42, 0.14, bevel=0)
    for j, ang in enumerate((-50, 0, 50)):  # короткие и разведены — трёхпалая кисть, а не лишний лист
        d = V((math.sin(math.radians(ang)), -0.12, -math.cos(math.radians(ang))))
        leaf(a, "vine", frame(d * 0.14 + V((0, 0, -0.21)), d, (0, -1, 0.1)), 2.0, 1.25,
             0.16, bends=(0, 12), ts=(0.5,), rib="leaf", root_w=0.3)
    a.transform = Matrix()


# ── Голова: бутон с лицом, ловушка, венчик, корона ───────────────────────────────────────────────────────────
POD_C, POD_RX, POD_RY, POD_H = V((0, -0.05, 0.0)), 1.85, 1.6, 3.3
FACE_Y = -1.66  # передняя плоскость маски лица
EYE_Z = 2.2
HINGE = V((0, -0.85, 0.32))  # петля ловушки — под лицом
TRAP_L, TRAP_H, TRAP_W = 2.15, 1.1, 3.0  # створка: вылет вперёд, высота полукруга, ширина


def pod(a):
    """Бутон головы: ступенчатое «яйцо» из 6 ярусов (восьмигранник со скосами) и светлая маска лица."""
    n = 6
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        tm = (t0 + t1) / 2
        f = max(math.sqrt(max(1 - ((tm - 0.45) / (0.55 if tm > 0.45 else 0.45)) ** 2, 0.0)), 0.42)
        wx, wy = POD_RX * f - 0.01 * i, POD_RY * f - 0.01 * i
        a.prism("pod" if i % 2 == 0 else "podD",
                S.octagon(POD_C.x - wx, POD_C.x + wx, POD_C.y - wy, POD_C.y + wy, min(wx, wy) * 0.36),
                POD_H * t0 - (0.01 if i else 0), POD_H * t1 + 0.01)
    a.prism("face", S.octagon(-1.42, 1.42, 1.05, 3.12, 0.5), FACE_Y, FACE_Y + 0.5, axis="y")


def face(a, mood):
    """Глаза, веки, ресницы и брови на маске. mood: smug / roar / sleep / dizzy."""
    y = FACE_Y
    for s in S2:
        ex, ez = s * 0.68, EYE_Z
        if mood == "sleep":
            a.box("lid", ex - 0.42, ex + 0.42, y - 0.1, y + 0.02, ez - 0.42, ez + 0.42, bevel=0.02)
            a.box("dark", ex - 0.4, ex + 0.4, y - 0.13, y - 0.1, ez - 0.2, ez - 0.1, bevel=0)
            for dx in (-0.26, 0.0, 0.26):  # ресницы вниз — спит
                key("dark")
                K.spike(a, (ex + dx, y - 0.12, ez - 0.15), (ex + dx * 1.3, y - 0.2, ez - 0.42), 0.08)
        else:
            a.box("eyeW", ex - 0.4, ex + 0.4, y - 0.1, y + 0.02, ez - 0.46, ez + 0.46, bevel=0.02)
            if mood == "dizzy":
                for ang in (45, -45):
                    a.box("dark", -0.06, 0.06, -0.02, 0.02, -0.36, 0.36, bevel=0,
                          matrix=T((ex, y - 0.12, ez)) @ R("Y", ang))
            else:
                px, pz = {"smug": (-s * 0.1, -0.12), "roar": (-s * 0.1, -0.04)}[mood]
                a.box("pupil", ex + px - 0.19, ex + px + 0.19, y - 0.13, y - 0.1, ez + pz - 0.23, ez + pz + 0.23,
                      bevel=0)
                a.box("white", ex + px + 0.03, ex + px + 0.13, y - 0.15, y - 0.13, ez + pz + 0.06, ez + pz + 0.17,
                      bevel=0)
                lid = {"smug": 0.16, "roar": 0.3}[mood]  # веко: вредный прищур (зрачок открыт) / распахнуты в гневе
                tilt = {"smug": (-12 if s > 0 else 12), "roar": -s * 10}[mood]  # к переносице ниже — вредный взгляд
                a.box("lid", -0.44, 0.44, -0.14, 0.0, lid - 0.33, 0.17, bevel=0.02,
                      matrix=T((ex, y, ez + 0.33)) @ R("Y", tilt))
            for j, dx in enumerate((-0.3, 0.0, 0.3)):  # ресницы вверх-наружу — королева
                key("dark")
                tip = (ex + dx + s * 0.22 + dx * 0.4, y - 0.2, ez + 0.72 + (0.06 if j == 1 else 0.0))
                K.spike(a, (ex + dx, y - 0.13, ez + 0.48), tip, 0.1)
        ang, lift = {"smug": ((-20 if s > 0 else 22), (0.2 if s > 0 else -0.05)), "roar": (-s * 24, -0.1),
                     "sleep": (s * 8, -0.05), "dizzy": (-s * 16, 0.15)}[mood]
        a.box("brow", -0.52, 0.52, -0.1, 0.1, -0.11, 0.11, bevel=0.03,
              matrix=T((ex, y - 0.16, ez + 0.78 + lift)) @ R("Y", ang))
    if mood != "sleep":  # румянец на щеках (розовые бруски)
        for s in S2:
            a.box("petal", s * 1.08 - 0.2, s * 1.08 + 0.2, y - 0.08, y + 0.02, 1.5, 1.66, bevel=0)


def lobe(a, m, upper, L=TRAP_L, H=TRAP_H, W=TRAP_W, n_cil=8, cil=0.38, cil_w=0.17, out_key="trap", rim=0.2):
    """Створка ловушки в осях m (петля в начале, вылет к −y): сбоку — полукруг, сверху — ступенчатый полуэллипс;
    снаружи out_key с малиновым кантом по краю (rim — ширина канта), внутри малиновая выстилка с прожилками,
    по самому краю — короткие тупые реснички к другой створке (сомкнутая ловушка — «застёжка» из ресничек)."""
    sgn = 1 if upper else -1
    y0, y1 = 0.25, -L
    yc, half = (y0 + y1) / 2, (y0 - y1) / 2
    prof = [(yc + half * math.cos(math.pi * i / 8), sgn * H * math.sin(math.pi * i / 8)) for i in range(9)]
    key(out_key)
    hw = W / 2 * (1.0 if upper else 0.975)  # нижняя чуть уже — боковины створок не в одной плоскости
    layers = [(hw * 0.3, 1.0, 1.0), (hw * 0.55, 0.96, 0.94), (hw * 0.75, 0.86, 0.8), (hw * 0.9, 0.7, 0.62), (hw, 0.5, 0.4)]
    K.layered(a, prof, layers, (yc, 0.0), matrix=m)
    if rim:  # кант: полоса у шва, выступает за створку на e; к краям ниже (по слоям — спад), спереди край идёт дугой
        key("rim")
        e = 0.06 * W / TRAP_W
        for i, (w, sy, sz) in enumerate(layers):
            hy = half * sy + e
            z0, z1 = sgn * (0.05 + 0.006 * i), sgn * (0.05 + rim * (0.35 + 0.65 * sz) - 0.012 * i)
            K.slab(a, [(yc + hy, z0), (yc + hy, z1), (yc - hy, z1), (yc - hy, z0)], -w - e, w + e, m)
    inner = [(y0 - 0.02, sgn * 0.03), (y1 + 0.14, sgn * 0.03), (y1 + 0.14, -sgn * 0.09), (y0 - 0.02, -sgn * 0.09)]
    key("maw")
    K.layered(a, inner, [(hw * 0.58, 0.97, 1.0), (hw * 0.8, 0.84, 1.0), (hw * 0.95, 0.62, 1.0)], (yc, 0.0),
              matrix=m)
    for x in (-hw * 0.4, hw * 0.4):  # прожилки нутра
        a.box("mawD", x - 0.05, x + 0.05, y1 + 0.5, y0 - 0.4, -sgn * 0.08, -sgn * 0.13, bevel=0, matrix=m)
    # реснички по краю: короткие, тупые, наружу и к другой створке (у нижней — со сдвигом, чтобы переплетались)
    for i in range(n_cil):
        u = math.radians(-80 + 160 * (i + (0.0 if upper else 0.5)) / (n_cil - (1 if upper else 0)))
        if abs(math.degrees(u)) > 80.5:  # у петли ресничек нет — створки не сталкиваются ими
            continue
        x = hw * 0.95 * math.sin(u)  # на самом краю: у сомкнутой ловушки ложатся поверх другой створки
        y = yc - half * 0.96 * math.cos(u)
        out = V((math.sin(u), -math.cos(u), 0))
        b = m @ V((x, y, -sgn * 0.02))
        tip = m @ (V((x, y, 0)) + out * cil * 0.19 + V((0, 0, -sgn * cil * 0.92)))
        blunt(a, "teeth", b, tip, cil_w, cil_w * 0.7)


def halo(a, mood, droop):
    """Венчик-чаша вокруг головы — «королева цветов»: 6 крупных розовых лепестков (наклонены вперёд на ~25°,
    толстые, со ступенью) и внутренний ряд из 5 тёмно-розовых, наклонённых сильнее; сбоку — венец, а не линия.
    Во сне лепестки сложены вперёд."""
    c = V((0, 0.55, 1.75))
    fold = {"sleep": 40, "dizzy": 22}.get(mood, 18)
    for n, off, ln, w, th, k, tier, fwd, r0 in ((7, 0.0, 2.75, 1.95, 0.24, "petal", "petalD", 0.45, 1.15),
                                                (7, 0.5, 1.95, 1.4, 0.2, "petalD", None, 0.95, 1.0)):
        for i in range(n):
            ang = -90 + 360 * (i + off) / n
            if abs((ang + 90 + 180) % 360 - 180) < 40:
                continue  # снизу — шея и ловушка, без лепестков
            t = math.radians(ang)
            d = V((math.cos(t), 0.0, math.sin(t)))
            dd = d + V((0, -fwd, 0)) + V((0, 0, -0.5 * droop))
            leaf(a, k, frame(c + d * r0 + V((0, 0.12 if tier else 0.0, 0)), dd, V((0, -1, 0))), ln, w, th,
                 bends=(0, fold), ts=(0.5,), tier=tier, root_w=0.35)


def crown(a, mc):
    """Золотая корона: обод-восьмигранник, пять тупых зубцов с самоцветами, цветок-навершие."""
    a.prism("gold", S.octagon(-0.98, 0.98, -0.82, 0.82, 0.3), 0.0, 0.45, matrix=mc)
    for i in range(5):
        t = 2 * math.pi * i / 5 - math.pi / 2
        px, py = 0.84 * math.cos(t), 0.7 * math.sin(t)
        a.frustum("gold", (px - 0.27, px + 0.27, py - 0.2, py + 0.2), (px - 0.04, px + 0.04, py - 0.03, py + 0.03),
                  0.42, 1.2, bevel=0, matrix=mc)
        a.box("neonGem", px * 1.08 - 0.13, px * 1.08 + 0.13, py * 1.08 - 0.13, py * 1.08 + 0.13, 0.12, 0.34,
              bevel=0, matrix=mc)
    a.prism("petal", S.octagon(-0.4, 0.4, -0.4, 0.4, 0.13), 0.45, 0.66, matrix=mc, bevel=0)
    a.prism("petalD", S.octagon(-0.2, 0.2, -0.2, 0.2, 0.07), 0.66, 0.82, matrix=mc, bevel=0)


def head(a, M, P):
    a.transform, a.group = M["head"], "Head"
    mood = P["face"]
    up, down = P["jaw"]
    a.prism("stem", S.octagon(-0.85, 0.85, -0.85, 0.75, 0.26), -0.9, 0.4, bevel=0)  # шея входит в бутон
    pod(a)
    face(a, mood)
    mu = T(HINGE) @ R("X", -up)
    ml = T(HINGE) @ R("X", down)
    cil = (0.48, 0.2) if mood == "sleep" else (0.38, 0.17)  # во сне «застёжка» крупнее
    lobe(a, mu, True, cil=cil[0], cil_w=cil[1])
    lobe(a, ml, False, cil=cil[0], cil_w=cil[1])
    tg = P["tongue"]
    if tg:  # язык лежит в нижней створке; в бою — наружу, в поражении — набок
        key("tongue")
        pts = {"in": [(0, 0.0, 0.05), (0, -0.8, 0.14), (0, -1.45, 0.16)],
               "out": [(0, 0.0, 0.05), (0, -1.0, 0.18), (0, -1.9, 0.3), (0.1, -2.55, 0.62)],
               "side": [(0, 0.0, 0.05), (0.3, -1.0, 0.16), (0.95, -1.75, 0.0), (1.25, -2.0, -0.75)]}[tg]
        ws = [0.95, 0.9, 0.72, 0.55][:len(pts)]
        K.chain(a, [ml @ V(p) for p in pts], ws, [0.22] * len(pts), up=(0, 0, 1), cut=0.35, overlap=0.3)
    halo(a, mood, P["droop"])
    if mood != "dizzy":
        crown(a, T((0.1, -0.15, POD_H - 0.12)) @ R("Y", -8) @ R("X", -6))
    if mood == "sleep":  # капля росы на кончике створки
        a.prism("dew", S.octagon(-0.18, 0.18, HINGE.y - TRAP_L - 0.25, HINGE.y - TRAP_L + 0.1, 0.08),
                HINGE.z - 0.25, HINGE.z + 0.12, bevel=0)
    a.transform = Matrix()


# ── Бутоны-фрейлины (без лиц) ─────────────────────────────────────────────────────────────────────────────────
def bud(a, at, turn, state):
    """Бутон на стебельке у подножия: закрыт (розовое «яйцо» в тёмно-зелёных чашелистиках); в бою
    раскрыт в маленькую ловушку — две створки с малиновым нутром и ресничками, без лица."""
    x, y = at
    tilt = {"closed": 0, "sleep": 34, "open": -6, "wilt": 68}[state]
    m = T((x, y, 0)) @ R("Z", turn)
    a.transform, a.group = m, "Buds"
    top = V((0.0, -0.15 - 1.4 * math.sin(math.radians(tilt)), 0.25 + 1.6 * math.cos(math.radians(tilt))))
    key("leaf")
    K.chain(a, [(0, 0, 0.05), (0.08, -0.05, 0.8), top], [0.42, 0.36, 0.32], up=(0, -1, 0), cut=0.3, overlap=0.3)
    for s, ln in ((1, 1.3), (-1, 1.1)):
        leaf(a, "leafL", frame((s * 0.15, 0, 0.3), (s * 1, -0.25, 0.25), (0, 0, 1)), ln, 0.7, 0.1, bends=(0,),
             ts=(), root_w=0.3)
    mb = m @ T(top) @ R("X", tilt)
    a.transform = mb
    if state == "open":
        # маленькая ловушка смотрит вперёд-вверх, на игрока: малиновое нутро и реснички видны спереди
        a.prism("trap", S.octagon(-0.42, 0.42, -0.3, 0.5, 0.15), -0.2, 0.45, bevel=0)
        sc = Matrix.Scale(0.55, 4)
        h = V((0, -0.1, 0.4))
        lobe(a, T(h) @ R("X", -28) @ R("X", -34) @ sc, True, n_cil=6, cil=0.32, cil_w=0.15, rim=0.25)
        lobe(a, T(h) @ R("X", -28) @ R("X", 30) @ sc, False, n_cil=6, cil=0.32, cil_w=0.15, rim=0.25)
        for s in S2:  # розовые лепестки-«ушки» прижаты к основанию створок
            leaf(a, "petal", frame((s * 0.3, 0.0, 0.3), (s, 0.15, 0.6), (0, -1, 0)), 0.7, 0.62, 0.1, ts=(),
                 bends=(0,))
    else:
        # розовое «яйцо» бутона: широкое посередине, круглая макушка
        for i, (r, z0, z1) in enumerate(((0.34, -0.05, 0.3), (0.5, 0.25, 0.8), (0.44, 0.75, 1.15), (0.3, 1.1, 1.42))):
            a.prism("petal" if i % 2 else "petalD", S.octagon(-r, r, -r, r, r * 0.4), z0, z1, bevel=0)
        a.frustum("petal", (-0.2, 0.2, -0.2, 0.2), (-0.05, 0.05, -0.05, 0.05), 1.4, 1.72, bevel=0)
        a.prism("trap", S.octagon(-0.4, 0.4, -0.4, 0.4, 0.15), -0.18, 0.16, bevel=0)  # донце чаши
        for i in range(4):  # чашелистики — низкая чаша под бутоном, отогнуты наружу; по диагоналям к игроку
            t = math.radians(45 + 90 * i - turn)
            d = V((math.cos(t), math.sin(t), 0))
            leaf(a, "trap" if i % 2 else "leaf", frame(d * 0.3 + V((0, 0, -0.02)), d * 0.5 + V((0, 0, 1)), d),
                 0.85, 0.74, 0.14, bends=(0,), ts=(), root_w=0.8)  # одним звеном: без щели на изломе
    a.transform = Matrix()


def fallen_leaves(a):
    """Поражение: опавшие листья и лепестки на земле вокруг."""
    a.transform, a.group = Matrix(), "Fx"
    for x, y, ang, kk in ((-4.4, -5.6, 30, "leaf"), (4.8, -3.0, -50, "leafL"), (1.6, -6.6, 10, "petal"),
                          (-5.8, -1.6, 70, "petal")):
        d = V((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
        leaf(a, kk, frame(V((x, y, 0.02)) - d * 0.8, d, (0, 0, 1)), 1.6, 0.9, 0.08, ts=(), bends=(0,), root_w=0.3)


def zzz(a, M):
    """Сон: «Z» над головой (плоские фигуры, не текст)."""
    zp = [(0, 0), (0.7, 0), (0.12, -0.62), (0.72, -0.62), (0.72, -0.78), (-0.05, -0.78), (0.52, -0.16), (0, -0.16)]
    base_m = T(M["head"] @ V((0, -1.0, 3.6)))
    for i, (dx, dz, sc) in enumerate(((1.7, 0.7, 1.0), (2.5, 1.7, 0.8), (3.2, 2.5, 0.62))):
        a.transform, a.group = base_m @ T((dx, 0, dz)) @ R("Y", -12 * i) @ Matrix.Scale(sc, 4), "Fx"
        a.extrude("petal" if i % 2 else "rib", zp, -0.07, 0.07, axis="y")
    a.transform = Matrix()


def flytrap(pose="stand"):
    a = new_art("Flytrap" + pose.capitalize())  # без «_»: ключ материала — после последнего «_»
    P = POSES[pose]
    M = skeleton(pose)
    base(a, P)
    mantle(a, M, P)
    stem(a, M, P)
    for s in S2:
        arm(a, M, s, P)
    head(a, M, P)
    for at, turn in BUDS:
        bud(a, at, turn, P["buds"])
    if pose == "defeat":
        a.transform, a.group = Matrix(), "Fx"
        crown(a, T((3.6, -5.8, 0.95)) @ R("Z", 30) @ R("Y", 74))
        fallen_leaves(a)
    if pose == "sleep":
        zzz(a, M)
    a.transform, a.group = None, None
    return a
