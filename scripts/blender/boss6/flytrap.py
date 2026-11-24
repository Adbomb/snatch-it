"""Босс 6 «Джунгли» — Королева-мухоловка (концепт, D64 шаг 3): одна модель в позах стойка / сон / бой / поражение.

Образ: огромное хищное растение-королева, вросшее в землю (не ходит — поворачивается на месте, D64 п. 5).
Силуэт «королева в бальном платье»: внизу — пышная юбка из двух ярусов огромных листьев и корни, расползшиеся по
земле; тонкая «талия» — стебель с узлами-кольцами; на «шее» — королевский воротник-раф из листочков; руки — две
лианы с ладонями из трёх листьев; голова — ловушка мухоловки: две створки-челюсти (снаружи зелёные, внутри малиновые)
с частоколом белых ресничек-зубов. Лицо — на верхней створке: два больших глаза-бруска с тяжёлыми веками и брови-бруски
(высокомерная королева), сверху — золотая корона с розовыми самоцветами. Сзади — мантия из трёх длинных тёмных
листьев с золотой застёжкой, на груди — золотой медальон с самоцветом. У подножия — два бутона-фрейлины (маленькие
мухоловки на лианах). Анатомия растения (D64 п. 1): створки-ловушка с ресничками, стебель с узлами, листья с
центральной жилкой, корни; без людей, текста и узнаваемых чужих персонажей.

Позы: стойка — створки приоткрыты, «ну и кто тут?»; сон — створки сомкнуты (реснички переплетены), голова склонилась
на воротник, лианы опущены, веки закрыты, бутоны спят; бой — пасть распахнута, голова подалась вперёд, лианы
вскинуты, брови-домиком вниз; поражение — увяла: стебель согнулся набок, голова поникла, пасть повисла, глаза-
крестики, корона упала на землю, листья опали.

Построение — как у Йети (стиль D39, art_style): слоёные боковые профили (створки, корона), сужающиеся восьмигранные
звенья (стебель, лианы, листья, корни), острые пирамиды (реснички, зубцы короны). Координаты: z вверх, лицо в −y,
1 единица ≈ 2.3 стада в игре (рост ≈ 24 стада, как у Йети). Зависит от art_style.py и dragon10/v4_kit.py.
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
    "leaf": ("43B649", True), "leafD": ("23803A", True), "leafL": ("9BE15D", True), "leafY": ("D7F06A", False),
    "stem": ("3E9A45", True), "stemD": ("256B34", False), "rib": ("C9F07A", False),
    "maw": ("E2385A", True), "mawD": ("A51E45", False), "tongue": ("FF7FA6", False), "teeth": ("FFF4DA", False),
    "root": ("8F5A31", True), "rootD": ("5E3A1E", False), "moss": ("6FC24A", False),
    "eyeW": ("FFFFFF", False), "pupil": ("1B1B2A", False), "lid": ("2F8F44", False), "brow": ("1E5E2E", False),
    "gold": ("F5B21C", True), "goldS": ("F5B21C", False), "goldD": ("C27E0E", False),
    "neonGem": ("FF4FA3", False), "gemD": ("B8306E", False), "petal": ("FF8FC0", True), "petalD": ("E0569A", False),
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


def slab(a, prof, x0, x1, matrix=None):
    K.slab(a, prof, x0, x1, matrix=matrix)


def leaf(a, k, root, tip, w, thick=0.16, normal=(0, 0, 1), rib=None, curl=0.0):
    """Лист: звенья вдоль от корня к кончику (узко — широко — остро), толщина по нормали normal; rib — жилка
    поверх листа другим цветом; curl — изгиб кончика вдоль нормали (доля длины)."""
    r0, r1, n = V(root), V(tip), V(normal).normalized()
    d = r1 - r0
    pts = [r0, r0 + d * 0.28 + n * curl * 0.2 * d.length, r0 + d * 0.62 + n * curl * 0.5 * d.length,
           r1 + n * curl * d.length]
    key(k)
    K.chain(a, pts, [w * 0.32, w, w * 0.78, w * 0.1], [thick, thick, thick * 0.9, thick * 0.5], up=n, cut=0.22,
            overlap=0.25)
    if rib:
        key(rib)
        off = n * thick * 0.5
        K.chain(a, [p + off for p in pts[:3]] + [pts[3] * 0.85 + pts[2] * 0.15 + off],
                [w * 0.12, w * 0.1, w * 0.08, w * 0.03], [0.06] * 4, up=n, cut=0.2, overlap=0.2)


# ── Позы ──────────────────────────────────────────────────────────────────────────────────────────────────────
# lean — наклон стебля вперёд (градусы, + вперёд к −y), side — набок; head — (наклон вниз, поворот, крен);
# jaw — раскрытие створок (градусы); face — выражение; arm — (отвод от «вниз» наружу: 0 — висит, 90 — в сторону,
# 150 — вверх; мах вперёд; сгиб «локтя»; поворот ладони); droop — увядание листьев 0…1.
POSES = {
    "stand": dict(lean=4, side=0, head=(-8, 0, 0), jaw=30, face="smug",
                  arm={1: (38, 28, 62, 20), -1: (30, 12, 24, -10)}, droop=0.0, buds="awake"),
    "sleep": dict(lean=14, side=4, head=(46, 8, 10), jaw=0, face="sleep",
                  arm={1: (14, 12, 22, 0), -1: (16, 10, 26, 0)}, droop=0.25, buds="sleep"),
    "combat": dict(lean=12, side=0, head=(4, 0, 0), jaw=58, face="roar",
                   arm={1: (96, 42, 48, 30), -1: (108, 30, 36, -20)}, droop=0.0, buds="angry"),
    "defeat": dict(lean=20, side=-20, head=(18, -12, -34), jaw=40, face="dizzy",
                   arm={1: (8, -6, 6, 0), -1: (12, -4, 8, 0)}, droop=1.0, buds="dizzy"),
}

STEM_BASE = V((0, 0, 2.2))
STEM_LEN = [1.55, 1.5, 1.45, 1.2]  # звенья стебля снизу вверх
STEM_W = [1.95, 1.62, 1.4, 1.28, 1.3]


def skeleton(pose):
    """Матрицы: узлы стебля (n0…n4), шея (head), плечи лиан."""
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
    M["neck"] = nodes[-1]
    M["head"] = nodes[-1] @ T((0, 0, 0.85)) @ R("Z", hy) @ R("X", hp) @ R("Y", hr)  # hp > 0 — смотрит вниз
    for s in S2:  # лиана растёт по локальной −z (висит вниз), отводится наружу и вперёд
        out, fwd, el, wr = P["arm"][s]
        M[("sh", s)] = nodes[2] @ T((s * 0.55, -0.05, 0.75)) @ R("Y", -s * out) @ R("X", -fwd)
        M[("el", s)] = M[("sh", s)] @ T((0, 0, -1.6)) @ R("X", -el)
        M[("wr", s)] = M[("el", s)] @ T((0, 0, -1.45)) @ R("Z", wr)
    return M


# ── Подножие: корни, клубень, юбка из листьев, мантия ─────────────────────────────────────────────────────────
def base(a, P):
    a.transform, a.group = Matrix(), "Base"
    key("root")
    # клубень — ступенчатый купол корня (как «шар» Сфинкса), вросший в землю
    for i, (r, z0, z1) in enumerate(((2.45, 0.0, 0.55), (2.3, 0.5, 1.1), (2.0, 1.05, 1.6), (1.6, 1.55, 2.05),
                                     (1.15, 2.0, 2.45))):
        a.prism("root" if i % 2 == 0 else "rootD", S.octagon(-r, r, -r * 0.92, r * 0.92, r * 0.36), z0, z1)
    a.prism("moss", S.octagon(-1.25, 1.25, -1.18, 1.18, 0.42), 2.42, 2.6)  # мох на макушке клубня
    # корни расползаются по земле (8 штук, разной длины) — опора, «шлейф» платья
    for i in range(8):
        t = math.radians(22.5 + 45 * i)
        d = V((math.cos(t), math.sin(t), 0))
        ln = 4.6 + 1.1 * ((i * 7) % 3) / 2
        p0 = d * 1.7 + V((0, 0, 0.55))
        p1 = d * (1.7 + ln * 0.45) + V((0, 0, 0.32))
        p2 = d * (1.7 + ln * 0.8) + d.cross(V((0, 0, 1))) * 0.45 * (1 if i % 2 else -1) + V((0, 0, 0.18))
        p3 = d * (1.7 + ln) + d.cross(V((0, 0, 1))) * 0.2 * (1 if i % 2 else -1) + V((0, 0, 0.08))
        key("root" if i % 2 else "rootD")
        K.chain(a, [p0, p1, p2, p3], [0.85, 0.6, 0.38, 0.12], [0.6, 0.42, 0.28, 0.1], up=(0, 0, 1), cut=0.3,
                overlap=0.3)
    # юбка: два яруса огромных листьев от клубня вниз-наружу (кончики загнуты кверху), между ними — светлые
    droop = P["droop"]
    for tier, (n, r0, z0, ln, w, kk, phase) in enumerate(((9, 1.35, 2.35, 4.4, 1.9, "leaf", 0.0),
                                                          (9, 1.1, 2.9, 3.3, 1.45, "leafL", 20.0))):
        for i in range(n):
            t = math.radians(phase + 360 * i / n)
            if tier == 0 and abs(math.degrees(t) % 360 - 270) < 1:
                continue  # спереди по центру — без листа: корни и клубень видны, юбка «распахнута»
            d = V((math.cos(t), math.sin(t), 0))
            fall = 0.55 + 0.25 * droop + 0.1 * tier
            tip = d * (r0 + ln * math.cos(fall)) + V((0, 0, z0 - ln * math.sin(fall) + 0.35 - 0.3 * droop))
            root = d * r0 + V((0, 0, z0))
            nrm = (V((0, 0, 1)) - d * 0.6).normalized()
            leaf(a, kk, root, tip, w, 0.17, nrm, rib="rib" if tier == 0 else None, curl=0.12 - 0.1 * droop)
    # мантия: три длинных тёмных листа от воротника за спиной до земли
    return


def mantle(a, M, P):
    top = M["nodes"][-1]
    a.transform, a.group = Matrix(), "Mantle"
    droop = P["droop"]
    for i, (dx, ln, w) in enumerate(((-1.9, 7.6, 2.3), (0.0, 8.2, 2.7), (1.9, 7.6, 2.3))):
        root = top @ V((dx * 0.35, 0.6, -0.2))
        tip = V((dx * 1.9 + dx * droop * 0.6, 2.5 + 0.5 * abs(dx) + droop * 0.8, 0.25))
        mid = (root + tip) / 2 + V((0, 0.55, 0.0))
        key("leafD")
        pts = [root, root * 0.6 + mid * 0.4, mid, mid * 0.4 + tip * 0.6, tip]
        K.chain(a, pts, [w * 0.35, w * 0.8, w, w * 0.75, w * 0.12], [0.16, 0.18, 0.18, 0.16, 0.08], up=(0, 1, 0.2),
                cut=0.22, overlap=0.25)
        key("rib")
        K.chain(a, [p + V((0, 0.1, 0)) for p in pts[:4]], [0.16, 0.14, 0.12, 0.08], [0.06] * 4, up=(0, 1, 0.2),
                cut=0.2, overlap=0.2)
    # золотая застёжка мантии на затылке стебля
    a.transform = top @ T((0, 0.6, -0.05)) @ R("X", -80)
    a.prism("gold", S.octagon(-0.42, 0.42, -0.42, 0.42, 0.14), -0.06, 0.1)
    a.prism("neonGem", S.octagon(-0.2, 0.2, -0.2, 0.2, 0.07), 0.1, 0.2)


# ── Стебель, воротник, медальон ───────────────────────────────────────────────────────────────────────────────
def stem(a, M, P):
    a.transform, a.group = Matrix(), "Stem"
    nodes = M["nodes"]
    pts = [n @ V((0, 0, 0)) for n in nodes]
    key("stem")
    K.chain(a, pts, STEM_W, up=(0, -1, 0), cut=0.3, overlap=0.35)
    # узлы-кольца стебля (как у бамбука) — тёмные пояски
    for i, n in enumerate(nodes[1:-1]):
        a.transform = n
        w = STEM_W[i + 1] / 2 + 0.1
        a.prism("stemD", S.octagon(-w, w, -w, w, w * 0.3), -0.14, 0.14)
        # маленькие листочки из узлов (живое растение, не столб)
        s = 1 if i % 2 == 0 else -1
        leaf(a, "leafL", (s * w * 0.8, 0.05, 0.1), (s * (w + 1.0), -0.2, 0.75), 0.6, 0.1, (s * -0.4, -0.3, 1))
    a.transform = Matrix()
    # корсаж: два широких листа обвивают стебель крест-накрест спереди (силуэт «талии» платья)
    for s in S2:
        p0 = nodes[1] @ V((s * 0.95, -0.55, 0.0))
        p1 = nodes[3] @ V((-s * 0.85, -0.6, 0.2))
        leaf(a, "leafD" if s > 0 else "leaf", p0, p1, 1.15, 0.14, (0, -1, 0.15), rib="rib")


def collar(a, M, P):
    """Королевский воротник-раф из листочков вокруг «шеи» и медальон с самоцветом спереди."""
    top = M["nodes"][-1]
    a.transform, a.group = top, "Collar"
    closed = P["face"] == "sleep"
    n = 14
    for i in range(n):
        t = 2 * math.pi * i / n
        d = V((math.cos(t), math.sin(t), 0))
        up = 0.75 if closed else 0.38
        root = d * 0.55 + V((0, 0, -0.05))
        tip = d * (2.25 - (0.55 if closed else 0)) + V((0, 0, up + 0.15))
        leaf(a, "leafY" if i % 2 else "leafL", root, tip, 1.05, 0.12, (V((0, 0, 1)) - d * 0.5).normalized())
    a.prism("stem", S.octagon(-0.62, 0.62, -0.62, 0.62, 0.2), -0.25, 0.32)
    # медальон: золотой обод, самоцвет, блик (приём Сфинкса)
    a.transform = top @ T((0, -0.68, -0.55)) @ R("X", 90 + 12)
    a.prism("gold", S.octagon(-0.44, 0.44, -0.44, 0.44, 0.15), -0.05, 0.1)
    a.prism("goldD", S.octagon(-0.33, 0.33, -0.33, 0.33, 0.11), 0.1, 0.13)
    a.prism("neonGem", S.octagon(-0.24, 0.24, -0.24, 0.24, 0.08), 0.13, 0.25)
    a.box("white", 0.04, 0.12, 0.06, 0.14, 0.25, 0.27, bevel=0)
    a.transform = Matrix()


# ── Лианы-руки ────────────────────────────────────────────────────────────────────────────────────────────────
def arm(a, M, s, P):
    side = "L" if s > 0 else "R"
    a.transform, a.group = Matrix(), f"Vine{side}"
    p0 = M[("sh", s)] @ V((0, 0, 0))
    p1 = M[("sh", s)] @ V((0, -0.1, -0.8))
    p2 = M[("el", s)] @ V((0, 0, 0))
    p3 = M[("el", s)] @ V((0, -0.1, -0.75))
    p4 = M[("wr", s)] @ V((0, 0, 0))
    key("stem")
    K.chain(a, [p0, p1, p2, p3, p4], [0.74, 0.66, 0.6, 0.54, 0.5], up=(0, -1, 0), cut=0.3, overlap=0.35)
    key("stemD")
    for p in (p2,):  # «локоть» — узел
        a.prism("stemD", S.octagon(p.x - 0.33, p.x + 0.33, p.y - 0.33, p.y + 0.33, 0.1), p.z - 0.18, p.z + 0.18)
    # усики, закрученные спиралью (растение-лиана)
    for j in range(5):
        t = j * 1.25
        q0 = M[("el", s)] @ V((s * (0.5 + 0.18 * math.cos(t)), 0.18 * math.sin(t), -0.5 - 0.12 * j))
        q1 = M[("el", s)] @ V((s * (0.5 + 0.18 * math.cos(t + 1.25)), 0.18 * math.sin(t + 1.25), -0.62 - 0.12 * j))
        key("leafL")
        K.chain(a, [q0, q1], [0.09, 0.08], up=(0, -1, 0), cut=0.3, overlap=0.3)
    # ладонь: три листа-пальца веером
    a.transform, a.group = M[("wr", s)], f"Hand{side}"
    a.prism("stemD", S.octagon(-0.32, 0.32, -0.32, 0.32, 0.1), -0.3, 0.1)
    for j, ang in enumerate((-38, 0, 38)):
        d = V((math.sin(math.radians(ang)), -0.15, -math.cos(math.radians(ang)))).normalized()
        leaf(a, "leaf" if j != 1 else "leafL", d * 0.15 + V((0, 0, -0.2)), d * 1.95 + V((0, 0, -0.2)), 0.85, 0.13,
             (0, -1, 0.1), rib="rib")
    a.transform = Matrix()


# ── Голова: бутон с лицом, пасть-ловушка, венчик, корона ─────────────────────────────────────────────────────
# Голова — круглый бутон (ярусы D39) с плоской «маской» лица (приём Сфинкса): глаза-бруски, веки, ресницы, брови.
# Пасть — ловушка мухоловки под лицом: верхняя створка неподвижна (как морда), нижняя опускается на jaw градусов;
# снаружи зелёные, внутри малиновые, по краю — реснички-зубы (переплетаются, когда пасть закрыта).
POD_C, POD_RX, POD_RY, POD_H = V((0, -0.1, 0.0)), 1.85, 1.6, 3.1
FACE_Y = -1.72  # передняя плоскость маски лица
HINGE = V((0, -1.15, 0.55))  # шарнир пасти — у нижнего края лица
JL, JW = 2.75, 4.3  # длина створки вперёд и её ширина (шире бутона — «пасть-ловушка»)
UPPER = [(0.25, 0.0), (0.25, 0.42), (-0.55, 0.6), (-1.55, 0.6), (-2.35, 0.42), (-2.7, 0.16), (-2.75, 0.0)]
JAW_LAYERS = [(0.8, 1.0, 1.0), (1.3, 0.95, 0.95), (1.72, 0.86, 0.86), (1.98, 0.7, 0.72), (2.14, 0.5, 0.55)]


def pod(a):
    """Бутон головы: ступенчатое «яйцо» из 7 ярусов (сечение — восьмигранник со скосами) и маска лица."""
    n = 7
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        tm = (t0 + t1) / 2
        f = max(math.sqrt(max(1 - ((tm - 0.45) / (0.55 if tm > 0.45 else 0.45)) ** 2, 0.0)), 0.38)
        wx, wy = POD_RX * f - 0.01 * i, POD_RY * f - 0.01 * i
        a.prism("leaf" if i % 2 == 0 else "leafD",
                S.octagon(POD_C.x - wx, POD_C.x + wx, POD_C.y - wy, POD_C.y + wy, min(wx, wy) * 0.36),
                POD_H * t0 - (0.01 if i else 0), POD_H * t1 + 0.01)
    # маска лица — светлая пластина спереди (как маска Сфинкса и Йети)
    a.prism("leafL", S.octagon(-1.38, 1.38, 0.78, 3.0, 0.48), FACE_Y, FACE_Y + 0.5, axis="y")


def face(a, mood):
    """Глаза, веки, ресницы и брови на маске. mood: smug / roar / sleep / dizzy."""
    y = FACE_Y
    for s in S2:
        ex, ez = s * 0.68, 1.95
        if mood == "sleep":
            a.box("lid", ex - 0.42, ex + 0.42, y - 0.1, y + 0.02, ez - 0.42, ez + 0.42, bevel=0.02)
            a.box("dark", ex - 0.4, ex + 0.4, y - 0.13, y - 0.1, ez - 0.22, ez - 0.12, bevel=0)
            for dx in (-0.28, 0.0, 0.28):  # ресницы вниз — спит
                key("dark")
                K.spike(a, (ex + dx, y - 0.12, ez - 0.17), (ex + dx * 1.3, y - 0.2, ez - 0.45), 0.08)
        else:
            a.box("eyeW", ex - 0.4, ex + 0.4, y - 0.1, y + 0.02, ez - 0.48, ez + 0.48, bevel=0.02)
            if mood == "dizzy":
                for ang in (45, -45):
                    a.box("dark", -0.06, 0.06, -0.02, 0.02, -0.38, 0.38, bevel=0,
                          matrix=T((ex, y - 0.12, ez)) @ R("Y", ang))
            else:
                px, pz = {"smug": (-s * 0.05, -0.12), "roar": (-s * 0.08, -0.02)}[mood]
                a.box("pupil", ex + px - 0.19, ex + px + 0.19, y - 0.13, y - 0.1, ez + pz - 0.24, ez + pz + 0.24,
                      bevel=0)
                a.box("white", ex + px + 0.03, ex + px + 0.13, y - 0.15, y - 0.13, ez + pz + 0.06, ez + pz + 0.17,
                      bevel=0)
                lid = {"smug": 0.08, "roar": 0.3}[mood]  # тяжёлое веко: высокомерный прищур / распахнуты в гневе
                a.box("lid", ex - 0.44, ex + 0.44, y - 0.14, y + 0.0, ez + lid, ez + 0.52, bevel=0.02)
            for j, dx in enumerate((-0.3, 0.0, 0.3)):  # ресницы вверх-наружу — королева
                key("dark")
                tip = (ex + dx + s * 0.22 + dx * 0.4, y - 0.2, ez + 0.76 + (0.06 if j == 1 else 0.0))
                K.spike(a, (ex + dx, y - 0.13, ez + 0.5), tip, 0.1)
        ang, lift = {"smug": ((-8 if s > 0 else 12), (0.0 if s > 0 else 0.2)), "roar": (-s * 22, -0.08),
                     "sleep": (s * 8, -0.05), "dizzy": (-s * 16, 0.15)}[mood]
        a.box("brow", -0.52, 0.52, -0.1, 0.1, -0.11, 0.11, bevel=0.03,
              matrix=T((ex, y - 0.16, ez + 0.8 + lift)) @ R("Y", ang))
    if mood != "sleep":  # румянец на щеках (розовые бруски)
        for s in S2:
            a.box("petal", s * 1.05 - 0.2, s * 1.05 + 0.2, y - 0.08, y + 0.02, 1.25, 1.42, bevel=0.02)


def rim_points(n, u0, u1, shrink=0.0):
    """Точки края створки по эллипсу (x, y) от шарнира вперёд."""
    pts = []
    for i in range(n):
        u = math.radians(u0 + (u1 - u0) * i / (n - 1))
        x = (JW / 2 - 0.15 - shrink) * math.sin(u)
        y = -JL / 2 - (JL / 2 - 0.12 - shrink) * math.cos(u)
        pts.append((x, y))
    return pts


def jaw_lobe(a, upper, jaw):
    """Створка пасти относительно шарнира HINGE: верхняя неподвижна, нижняя опущена на jaw градусов."""
    sgn = 1 if upper else -1
    m = T(HINGE) @ R("X", -jaw * 0.18 if upper else jaw * 0.85) @ Matrix.Scale(1.0 if upper else 0.98, 4)
    prof = [(y, z * sgn * (1.0 if upper else 1.08)) for y, z in UPPER]
    if not upper:
        prof = list(reversed(prof))
    key("leaf")
    K.layered(a, prof, JAW_LAYERS, (-1.35, 0.0), matrix=m)
    # кайма по краю снаружи — тёмная (контур створки в силуэте)
    rim = [(y, z * sgn) for y, z in ((-2.3, 0.47), (-2.75, 0.2), (-2.82, 0.0), (-2.64, 0.0), (-2.56, 0.18),
                                     (-2.15, 0.44))]
    if not upper:
        rim = list(reversed(rim))
    key("mawD")  # край ловушки снаружи — малиновая кайма, как у настоящей мухоловки
    K.layered(a, rim, [(0.82, 1.0, 1.0), (1.32, 0.95, 0.95), (1.74, 0.86, 0.86)], (-1.35, 0.0), matrix=m)
    # малиновая выстилка у плоскости смыкания
    inner = [(y, -z * sgn) for y, z in ((0.15, 0.0), (0.15, 0.12), (-2.4, 0.12), (-2.55, 0.0))]
    if upper:
        inner = list(reversed(inner))
    key("maw")
    K.layered(a, inner, [(0.78, 1.0, 1.0), (1.26, 0.95, 1.0), (1.66, 0.86, 1.0), (1.9, 0.7, 1.0)], (-1.3, 0.0),
              matrix=m @ T((0, 0, -0.01 * sgn)))
    for x in (-0.7, 0.0, 0.7):  # прожилки внутри
        a.box("mawD", x - 0.05, x + 0.05, -2.25, -0.3, -sgn * 0.14, -sgn * 0.1, bevel=0, matrix=m)
    key("teeth")
    pts = rim_points(15, -124, 124) if upper else rim_points(16, -130, 130, shrink=0.05)
    for i, (x, y) in enumerate(pts):  # реснички длинные и тонкие, через одну короче
        out = V((x, y + JL / 2, 0)).normalized() * 0.32
        ln = 1.05 if i % 2 == 0 else 0.8
        b = m @ V((x, y, -0.02 * sgn))
        tip = m @ (V((x, y, 0)) + out + V((0, 0, -ln * sgn)))
        K.spike(a, b, tip, 0.2)
    return m


def halo(a, mood):
    """Венчик из розовых лепестков за головой — «королева цветов»; во сне лепестки сложены вперёд-кверху."""
    c = V((0, 0.55, 1.55))
    n = 9
    for i in range(n):
        ang = -90 + 360 * (i + 0.5) / n
        if -130 < ang < -50:
            continue  # снизу — шея, без лепестков
        t = math.radians(ang)
        d = V((math.cos(t), 0.0, math.sin(t)))
        fold = 0.55 if mood == "sleep" else (0.25 if mood == "dizzy" else 0.0)
        tip = c + d * (3.6 - fold * 0.8) + V((0, 0.4 + fold * 1.6, 0))
        leaf(a, "petal" if i % 2 else "petalD", c + d * 1.2, tip, 1.25, 0.14, (0, -1, 0.0))


def crown(a, mc):
    """Золотая корона: обод-восьмигранник, пять зубцов с самоцветами, цветок-навершие."""
    a.prism("gold", S.octagon(-0.95, 0.95, -0.8, 0.8, 0.3), 0.0, 0.42, matrix=mc)
    a.frame("goldD", S.octagon(-0.97, 0.97, -0.82, 0.82, 0.3), 0.08, 0.0, 0.12, axis="z", matrix=mc)
    for i in range(5):
        t = 2 * math.pi * i / 5 - math.pi / 2
        px, py = 0.82 * math.cos(t), 0.68 * math.sin(t)
        a.frustum("gold", (px - 0.26, px + 0.26, py - 0.2, py + 0.2), (px, px, py, py), 0.4, 1.15, bevel=0, matrix=mc)
        a.prism("neonGem", S.octagon(px * 1.06 - 0.13, px * 1.06 + 0.13, py * 1.06 - 0.13, py * 1.06 + 0.13, 0.04),
                0.14, 0.3, matrix=mc)
    a.prism("petal", S.octagon(-0.38, 0.38, -0.38, 0.38, 0.12), 0.42, 0.62, matrix=mc)
    a.prism("petalD", S.octagon(-0.18, 0.18, -0.18, 0.18, 0.06), 0.62, 0.78, matrix=mc)


def trap_head(a, mood, jaw, royal=True):
    """Голова целиком в осях a.transform: бутон, лицо, пасть; у королевы — венчик и корона."""
    pod(a)
    face(a, mood)
    jaw_lobe(a, upper=True, jaw=jaw)
    jaw_lobe(a, upper=False, jaw=jaw)
    if royal:
        halo(a, mood)
        if mood != "dizzy":
            crown(a, T((0.1, -0.15, POD_H - 0.12)) @ R("Y", -8) @ R("X", -6))


def head(a, M, P):
    a.transform, a.group = M["head"], "Head"
    mood, jaw = P["face"], P["jaw"]
    a.prism("stem", S.octagon(-0.72, 0.72, -0.75, 0.65, 0.22), -0.95, 0.35)  # шея входит в бутон
    trap_head(a, mood, jaw)
    if mood == "dizzy":  # язык набок из открытой пасти
        key("tongue")
        mj = T(HINGE) @ R("X", jaw * 0.85)
        K.chain(a, [mj @ V((0.0, -0.6, -0.2)), mj @ V((0.25, -1.7, -0.15)), mj @ V((0.8, -2.6, -0.45)),
                    mj @ V((1.1, -3.0, -1.1))], [0.85, 0.8, 0.66, 0.42], [0.18] * 4, up=(0, 0, 1), cut=0.3,
                overlap=0.3)
    if mood == "sleep":  # капля росы на кончике створки
        a.prism("dew", S.octagon(-0.18, 0.18, HINGE.y - 2.62, HINGE.y - 2.27, 0.08), HINGE.z - 0.55, HINGE.z - 0.2)
    a.transform = Matrix()


# ── Бутоны-фрейлины ───────────────────────────────────────────────────────────────────────────────────────────
def bud(a, at, turn, mood):
    """Маленькая мухоловка на лиане у подножия: бутон с глазами и пастью-ловушкой, без короны."""
    x, y = at
    m = T((x, y, 0)) @ R("Z", turn)
    a.transform, a.group = m, "Buds"
    key("stem")
    K.chain(a, [(0, 0, 0.1), (0.15, -0.1, 0.9), (0.0, -0.15, 1.7)], [0.46, 0.4, 0.36], up=(0, -1, 0), cut=0.3,
            overlap=0.3)
    leaf(a, "leaf", (0.15, 0, 0.35), (1.0, -0.2, 0.7), 0.6, 0.1, (0, -0.3, 1))
    leaf(a, "leafL", (-0.12, 0, 0.6), (-0.9, -0.1, 1.0), 0.5, 0.1, (0, -0.3, 1))
    a.transform = m @ T((0, -0.1, 1.55)) @ Matrix.Scale(0.42, 4)
    mood_ = {"awake": "smug", "sleep": "sleep", "angry": "roar", "dizzy": "dizzy"}[mood]
    trap_head(a, mood_, {"awake": 24, "sleep": 0, "angry": 45, "dizzy": 30}[mood], royal=False)
    a.transform = Matrix()


def fallen_leaves(a):
    """Поражение: опавшие листья и лепестки на земле вокруг."""
    a.transform, a.group = Matrix(), "Fx"
    for i, (x, y, ang, kk) in enumerate(((-4.6, -3.5, 30, "leafL"), (3.8, -4.4, -50, "leaf"), (5.2, -1.2, 80, "leafY"),
                                         (-2.6, -5.6, -20, "leafL"), (1.4, -6.0, 10, "petal"),
                                         (-5.4, 0.8, 60, "leaf"))):
        d = V((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
        p = V((x, y, 0.1))
        leaf(a, kk, p - d * 0.7, p + d * 0.7, 0.7, 0.08, (0, 0, 1))


def zzz(a, M):
    """Сон: розовые «Z» над головой (плоские фигуры, не текст)."""
    zp = [(0, 0), (0.7, 0), (0.12, -0.62), (0.72, -0.62), (0.72, -0.78), (-0.05, -0.78), (0.52, -0.16), (0, -0.16)]
    base = T(M["head"] @ V((0, -1.0, 3.4)))
    for i, (dx, dz, sc) in enumerate(((1.6, 0.6, 1.0), (2.4, 1.6, 0.8), (3.1, 2.4, 0.62))):
        a.transform, a.group = base @ T((dx, 0, dz)) @ R("Y", -12 * i) @ Matrix.Scale(sc, 4), "Fx"
        a.extrude("petal" if i % 2 else "leafY", zp, -0.07, 0.07, axis="y")
    a.transform = Matrix()


def flytrap(pose="stand"):
    a = new_art("Flytrap" + pose.capitalize())  # без «_»: ключ материала — после последнего «_»
    P = POSES[pose]
    M = skeleton(pose)
    base(a, P)
    mantle(a, M, P)
    stem(a, M, P)
    collar(a, M, P)
    for s in S2:
        arm(a, M, s, P)
    head(a, M, P)
    for (x, y), turn in (((-5.6, -3.8), 30), ((5.6, -3.8), -30)):
        bud(a, (x, y), turn, P["buds"])
    if pose == "defeat":
        a.transform, a.group = Matrix(), "Fx"
        crown(a, T((3.2, -5.6, 0.9)) @ R("Z", 30) @ R("Y", 74))
        fallen_leaves(a)
    if pose == "sleep":
        zzz(a, M)
    a.transform, a.group = None, None
    return a
