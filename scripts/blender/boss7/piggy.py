"""Босс 7 «Банк» — Копилка-громила, концепт (D64 шаг 1 для босса 7): одна модель в позах стойка / сон / бой /
особая атака / поражение.

Образ (v2 по замечаниям владельца 2026-11-26): огромная бронированная свинья-копилка на четырёх толстых ногах. Тело —
круглое яйцо из 16-гранных ярусов D39 (ярко-розовое): самое широкое место ближе к груди, массивные плечи и грудь,
зад меньше — тяжёлый перёд «бульдога»; голова опущена и выдвинута вперёд, передние ноги толще, стойка шире.
Поперёк тела — два стальных обруча с золотыми заклёпками, между ними на спине — изогнутое стальное седло с тёмной
щелью в золотой рамке, круглая монета вставлена в щель наполовину. Голова — круглая, с крупным светлым пятачком
(ноздри вырезаны: тёмные ямки в ободках), широкие уши с изгибом вперёд, на лбу — стальной щиток с заклёпками, тяжёлые
брови, маленькие злые глаза, челюсть «громилы» с двумя тупыми клычками. v1 (восьмигранная бочка) — в git-истории. Ноги — розовые, с копытами и стальными наголенниками; хвост — пружинка-завиток. Розовое — главное пятно
(≈ 2/3 видимой поверхности), сталь и золото — акценты; на тёмном мраморе и тёмной стали хранилища свинья читается.
Монеты сыплются из прорези только в позах и анимации (правила боя, добычи и краж не меняются, D64 п. 5).

Позы: стойка — ухмылка, брови насуплены, монета в прорези; сон — лежит на брюхе, ноги вытянуты вперёд и назад, голова
на земле, глаза закрыты (полоски век, ничего не светится), «Z»; бой (основная атака «Таран пятачком») — голова опущена
и выдвинута, передние ноги расставлены, рот открыт, из прорези выскакивают монеты; особая атака («Монетный град», только
анимация) — встаёт на дыбы на задних ногах, передние копыта вверх, фонтан монет из прорези; поражение — тело трескается
(тёмные трещины, отколотые розовые осколки на земле), из трещины на боку высыпается горка монет, глаза-крестики, язык
набок, уши повисли, ноги разъехались.

Построение — стиль D39 (art_style): ярусы со скосами (тело-бочка лёжа, голова, пятачок), сужающиеся восьмигранные звенья
(ноги, уши, хвост), рамки (обручи, рамка прорези). Мелочь (заклёпки, монеты, ноздри) без фаски. Игровая копия
≤ 8 000 треугольников. Координаты: z вверх, лицо в −y, 1 единица модели = export_scale стадов (render.py).
Зависит от art_style.py, anatomy_kit.py и dragon10/v4_kit.py.
"""

import math
import os
import sys

from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "dragon10"))
import anatomy_kit as A  # noqa: E402
import art_style as S  # noqa: E402
import v4_kit as K  # noqa: E402

V = Vector
S2 = (1, -1)

PALETTE = {  # ключ: (цвет, кольца D39 на крупных поверхностях)
    "pig": ("FF86B5", True),  # тело, голова, ноги — ярко-розовые (главное пятно кадра)
    "pigD": ("E25E95", False),  # внутренность ушей, складки
    "snout": ("FFB6CF", True),  # пятачок — светлее тела
    "nostril": ("9E2F60", False),
    "hoof": ("5E3B4E", False),  # копыта — тёмные
    "steel": ("4F5A72", True),  # броня — тёмная синеватая сталь
    "steelL": ("7C88A3", False),  # кромки брони
    "gold": ("F5B21C", True), "goldD": ("C9820E", False),  # рамка прорези, заклёпки
    "coin": ("FFC93A", False), "coinL": ("FFE27A", False),  # монеты: обод и середина
    "slot": ("1A1626", False),  # тёмная прорезь
    "snoutD": ("F28AB0", False),  # ободки ноздрей
    "brow": ("5A2142", False),
    "mouth": ("5A1E2E", False), "tongue": ("FF5F8A", False), "tusk": ("FFF4DA", False),
    "crack": ("3A1026", False),  # трещины (поражение)
    "white": ("FFFFFF", False), "dark": ("1B1B2A", False), "glint": ("FFFFFF", False),
    "zz": ("FFE27A", False),  # «Z» над спящим
}


def new_art(name):
    a = S.Art(name, ring_z0=0.5)
    a.ring = dict(S.RING, core=0.55)  # профиль контура «полка», как у Йети, дракона v7 и королевы
    for k, (code, rings) in PALETTE.items():
        a.paint(k, code, rings=rings)
    return a


def R(axis, deg):
    return Matrix.Rotation(math.radians(deg), 4, axis)


def T(v):
    return Matrix.Translation(V(v))


def about(p, m):
    """Поворот m вокруг точки p."""
    return T(p) @ m @ T(-V(p))


def chain(a, key, pts, ws, hs=None, up=(0, -1, 0), cut=0.26, overlap=0.45):
    K.KEY = key
    K.chain(a, pts, ws, hs, up=up, cut=cut, overlap=overlap)


def taper(a, key, p0, p1, w0, w1, h0=None, h1=None, up=(0, 0, 1), cut=0.26):
    K.KEY = key
    K.taper(a, p0, p1, w0, w1, h0, h1, up=up, cut=cut)


def stud(a, key, p, normal, s=0.13, h=0.1):
    """Заклёпка: низкий брусок на поверхности p по нормали normal (выступ h, уходит внутрь на 0.06)."""
    m = T(p) @ A.facing(normal)
    a.box(key, -s, s, -h, 0.06, -s, s, bevel=0, matrix=m)


def coin(a, c, normal, r=0.5, th=0.14, spin=0.0):
    """Монета: восьмигранный диск (обод) и выпуклая середина, плоскость поперёк normal."""
    m = T(c) @ V(normal).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4() @ R("Z", spin)
    n = 16 if r > 0.6 else 10  # крупная монета в прорези — круглая, россыпь — проще
    a.prism("coin", ring(0, 0, r, r, n), -th / 2, th / 2, bevel=0, matrix=m)
    q = r * 0.66
    a.prism("coinL", ring(0, 0, q, q, n + 2), th / 2 - 0.02, th / 2 + 0.035, bevel=0, matrix=m)
    a.prism("coinL", ring(0, 0, q, q, n + 2), -th / 2 - 0.035, -th / 2 + 0.02, bevel=0, matrix=m)


# ── Пропорции (v2: яйцо, тяжёлый перёд «бульдога») ──────────────────────────────────────────────────────────
ROUND = 16  # сечения тела и головы — 16-угольники: силуэт круглый, ступени ярусов D39 остаются
BODY_Y = (-3.4, 3.7)  # яйцо от груди до крупа
BODY_Z = 4.1  # ось тела
BODY_R = (3.25, 3.05)  # полуширина, полувысота в самом широком месте
BODY_N = 12
EGG_PEAK = 0.36  # самое широкое место — ближе к груди: перёд тяжёлый, зад меньше
HIP = V((0, 2.3, 2.6))  # тазобедренная ось — вокруг неё встаёт на дыбы
SHOULDER_Y, HIP_Y = -1.45, 2.3
LEG_XF, LEG_XB = 2.45, 2.0  # передние ноги шире — широкая стойка
LEG_X = LEG_XF
NECK = V((0, -3.2, 3.6))
BANDS = (-0.7, 1.9)  # обручи
LEG_TOP = 2.6  # верх ноги (внутри тела)


def ring(cx, cz, rx, rz, n=ROUND):
    """Многоугольник-«круг» (n углов) с плоской гранью сверху и снизу, точки (x, z) или (x, y)."""
    return [(cx + rx * math.cos(math.pi / n + 2 * math.pi * k / n), cz + rz * math.sin(math.pi / n + 2 * math.pi * k / n))
            for k in range(n)]


def egg_prof(t):
    u = (t - EGG_PEAK) / (EGG_PEAK + 0.04 if t < EGG_PEAK else 1.0 - EGG_PEAK + 0.04)
    return max(math.sqrt(max(1.0 - u * u, 0.0)), 0.3)


BODY_TIERS = []
for _k in range(BODY_N):
    _t = (_k + 0.5) / BODY_N
    _w = 1.0 + 0.08 * (EGG_PEAK - _t)  # перёд чуть шире
    BODY_TIERS.append((BODY_Y[0] + (BODY_Y[1] - BODY_Y[0]) * _k / BODY_N,
                       BODY_Y[0] + (BODY_Y[1] - BODY_Y[0]) * (_k + 1) / BODY_N, egg_prof(_t) * _w, egg_prof(_t)))


def slice_at(y):
    """Полуширина и полувысота яруса тела в точке y (третье значение — для совместимости)."""
    for y0, y1, fx, fz in BODY_TIERS:
        if y0 - 1e-6 <= y <= y1 + 1e-6:
            return BODY_R[0] * fx, BODY_R[1] * fz, 0.0
    y0, y1, fx, fz = BODY_TIERS[-1]
    return BODY_R[0] * fx, BODY_R[1] * fz, 0.0


def hull_point(wx, wz, c, d):
    """Точка на 16-угольном сечении (полуоси wx, wz) в направлении d (плоскость xz, вокруг оси тела)."""
    s = 1.0 / math.sqrt((d.x / wx) ** 2 + (d.z / wz) ** 2)
    return V((d.x * s, 0, d.z * s)) * math.cos(math.pi / ROUND)


# ── Позы ──────────────────────────────────────────────────────────────────────────────────────────────────────
# lift — подъём тела (− опустить), pitch — наклон тела вокруг таза (+ перёд вниз, − на дыбы), roll — крен;
# head — (наклон вниз +, поворот, крен); front/back — ноги: (мах вперёд −/назад +, развод в стороны); face — лицо;
# mouth — "grin" / "roar" / "tongue"; coins — "slot" / "burst" / "fountain" / "spill"; ears — 0 торчат … 1 повисли.
POSES = {
    "stand": dict(lift=0.0, pitch=2, roll=0, head=(4, 0, 0), front=(0, 6), back=(0, 5), face="angry", mouth="grin",
                  coins="slot", ears=0.0),
    "sleep": dict(lift=-1.75, pitch=3, roll=0, head=(14, 8, 4), front=(-82, 8), back=(84, 8), face="sleep",
                  mouth="sleep", coins="slot", ears=0.6),
    "combat": dict(lift=-0.2, pitch=8, roll=0, head=(14, 0, 0), front=(-14, 16), back=(14, 6), face="angry",
                   mouth="roar", coins="burst", ears=0.0),
    "special": dict(lift=0.0, pitch=-38, roll=0, head=(-14, 0, 0), front=(-48, 12), back=(0, 8), face="angry",
                    mouth="roar", coins="fountain", ears=0.0),
    "defeat": dict(lift=-1.6, pitch=5, roll=7, head=(22, -14, -10), front=(-30, 58), back=(30, 58), face="dizzy",
                   mouth="tongue", coins="spill", ears=1.0),
}


def skeleton(P):
    M = {}
    M["body"] = T((0, 0, P["lift"])) @ about(HIP, R("X", P["pitch"]) @ R("Y", P["roll"]))
    hp, hy, hr = P["head"]
    M["head"] = M["body"] @ about(NECK, R("Z", hy) @ R("X", hp) @ R("Y", hr))
    for s in S2:
        fs, fo = P["front"]
        bs, bo = P["back"]
        M[("F", s)] = M["body"] @ about((s * LEG_XF, SHOULDER_Y, LEG_TOP), R("X", fs) @ R("Y", -s * fo))
        # задние ноги: тело встаёт на дыбы вокруг таза, ноги остаются вертикально на земле
        M[("B", s)] = M["body"] @ about((s * LEG_XB, HIP_Y, LEG_TOP),
                                        R("Y", -P["roll"]) @ R("X", -P["pitch"]) @ R("X", bs) @ R("Y", -s * bo))
    return M


def egg_y(a, key, y0, y1, cx, cz, rx, rz, n, prof=egg_prof):
    """Яйцо лёжа: n ярусов-16-угольников вдоль y (ступени D39), ярусы заходят друг в друга на 0.01."""
    for k in range(n):
        f = prof((k + 0.5) / n)
        ya, yb = y0 + (y1 - y0) * k / n, y0 + (y1 - y0) * (k + 1) / n
        a.prism(key, ring(cx, cz, rx * f, rz * f), ya - (0.01 if k else 0), yb + 0.01, axis="y", bevel=0)


# ── Тело ──────────────────────────────────────────────────────────────────────────────────────────────────────
def body(a, M, P):
    a.transform, a.group = M["body"], "Body"
    for i, (ya, yb, fx, fz) in enumerate(BODY_TIERS):  # яйцо лёжа: перёд шире и выше, зад меньше
        a.prism("pig", ring(0, BODY_Z, BODY_R[0] * fx, BODY_R[1] * fz), ya - (0.01 if i else 0), yb + 0.01,
                axis="y", bevel=0)
    # мощная грудь внизу спереди и массивные плечи над передними ногами
    egg_y(a, "pig", -3.75, -1.0, 0, 3.15, 2.35, 2.0, 6)
    for sx in S2:
        egg_y(a, "pig", -2.75, -0.15, sx * 2.35, 4.0, 1.5, 1.8, 6)
    # обручи: 16-угольная рамка чуть шире яруса, золотые заклёпки по верхней половине
    for yb in BANDS:
        wx = max(slice_at(yb - 0.42)[0], slice_at(yb + 0.42)[0]) + 0.2
        wz = max(slice_at(yb - 0.42)[1], slice_at(yb + 0.42)[1]) + 0.2
        a.frame("steel", ring(0, BODY_Z, wx, wz), 0.6, yb - 0.42, yb + 0.42, axis="y", bevel=0)
        a.frame("steelL", ring(0, BODY_Z, wx + 0.06, wz + 0.06), 0.2, yb - 0.5, yb - 0.3, axis="y", bevel=0)
        for ang in (8, 34, 60, 90, 120, 146, 172):
            t = math.radians(ang)
            d = V((math.cos(t), 0, math.sin(t)))
            p = hull_point(wx, wz, 0, d) + V((0, yb + 0.02, BODY_Z))
            stud(a, "gold", p, d, s=0.13, h=0.1)
    # наплечники «громилы»: стальные щиты на плечах, золотой обод и заклёпка
    for sx in S2:
        m = T((sx * 3.05, -1.5, 5.15)) @ R("Y", sx * 52)  # лежит на верху плеча, смотрит вверх-наружу
        a.prism("steel", ring(0, 0, 1.25, 1.05), 0.0, 0.3, bevel=0, matrix=m)
        a.frame("gold", ring(0, 0, 1.32, 1.12), 0.16, 0.12, 0.38, axis="z", bevel=0, matrix=m)
        stud(a, "gold", m @ V((0, 0, 0.3)), m.to_3x3() @ V((0, 0, 1)), s=0.2, h=0.12)
    # седло на спине — изогнутая стальная пластина между обручами; поперёк — прорезь в золотой рамке
    yc = (BANDS[0] + BANDS[1]) / 2
    wx, wz, _ = slice_at(yc)
    arc = [((wx + 0.16) * math.cos(math.radians(g)), BODY_Z + (wz + 0.16) * math.sin(math.radians(g)))
           for g in range(54, 127, 8)]
    arc += [((wx - 0.3) * math.cos(math.radians(g)), BODY_Z + (wz - 0.3) * math.sin(math.radians(g)))
            for g in range(126, 53, -8)]
    a.extrude("steel", arc, BANDS[0] + 0.4, BANDS[1] - 0.4, axis="y")
    top = BODY_Z + (wz + 0.16) * math.sin(math.radians(86))
    a.frame("gold", [(-1.08, yc - 0.42), (1.08, yc - 0.42), (1.08, yc + 0.42), (-1.08, yc + 0.42)], 0.22,
            top - 0.06, top + 0.2, axis="z", bevel=0)
    a.box("slot", -0.86, 0.86, yc - 0.18, yc + 0.18, top - 0.3, top + 0.1, bevel=0)  # тёмная щель
    for x, y in ((-1.45, BANDS[0] + 0.6), (1.45, BANDS[0] + 0.6), (-1.45, BANDS[1] - 0.6), (1.45, BANDS[1] - 0.6)):
        stud(a, "gold", (x, y, BODY_Z + (wz + 0.16) * 0.93), (x / 3, 0, 1), s=0.13, h=0.1)
    # хвост-завиток на крупе
    pts = []
    for i in range(9):
        t = math.radians(-30 + i * 52)
        r = 0.55 - 0.03 * i
        pts.append((r * math.cos(t), BODY_Y[1] + 0.3 + 0.06 * i, BODY_Z + 0.9 + r * math.sin(t)))
    pts[0] = (0.2, BODY_Y[1] - 0.4, BODY_Z + 0.6)
    a.group = "Tail"
    chain(a, "pig", pts, [0.44] + [0.34] * 7 + [0.26], up=(0, 1, 0), overlap=0.5)
    a.group = "Body"
    return top


# ── Голова ────────────────────────────────────────────────────────────────────────────────────────────────────
HEAD_C = V((0, -4.45, 1.75))  # низ головы: опущена и выдвинута вперёд
HEAD_R = (2.35, 2.15, 3.5)


def round_z(a, key, base, rx, ry, h, prof, n):
    """Тело-«шар» вертикально: n ярусов-16-угольников; возвращает ярусы (za, zb, x, y, wx, wy)."""
    bx, by, bz = base
    tiers = []
    for k in range(n):
        f = max(prof((k + 0.5) / n), 0.45)
        za, zb = bz + h * k / n, bz + h * (k + 1) / n
        a.prism(key, ring(bx, by, rx * f, ry * f), za - (0.01 if k else 0), zb + 0.01, axis="z", bevel=0)
        tiers.append((za, zb, bx, by, rx * f, ry * f))
    return tiers


def front_y(tiers, x, z):
    """Передняя (−y) поверхность 16-угольных ярусов в точке (x, z)."""
    za, zb, bx, by, wx, wy = min(tiers, key=lambda tr: abs((tr[0] + tr[1]) / 2 - z))
    u = min(abs(x - bx) / wx, 0.99)
    return by - wy * math.sqrt(1 - u * u) * math.cos(math.pi / ROUND)


def head_prof(t):
    """Голова: широкие щёки-брыли внизу, круглый лоб."""
    return math.sqrt(max(1.0 - ((t - 0.42) / (0.5 if t < 0.42 else 0.6)) ** 2, 0.0))


def head(a, M, P):
    a.transform, a.group = M["head"], "Head"
    tiers = round_z(a, "pig", tuple(HEAD_C), HEAD_R[0], HEAD_R[1], HEAD_R[2], head_prof, 8)
    # пятачок: крупный светлый «пятак» вперёд, кайма, ноздри — тёмные ямки в розовых ободках (вырезаны)
    sz = HEAD_C.z + 1.3
    fy = front_y(tiers, 0, sz)
    sm = T((0, 0, sz))
    a.prism("pigD", ring(0, 0, 1.55, 1.18), fy - 0.15, fy + 0.4, axis="y", bevel=0, matrix=sm)
    a.prism("snout", ring(0, 0, 1.45, 1.1), fy - 1.0, fy + 0.3, axis="y", bevel=0, matrix=sm)
    a.frame("snout", ring(0, 0, 1.47, 1.12), 0.2, fy - 1.12, fy - 0.95, axis="y", bevel=0, matrix=sm)
    for s in S2:
        a.prism("nostril", ring(s * 0.52, 0.0, 0.25, 0.4, 12), fy - 1.02, fy - 0.9, axis="y", bevel=0, matrix=sm)
        a.frame("snoutD", ring(s * 0.52, 0.0, 0.36, 0.52, 12), 0.11, fy - 1.1, fy - 0.96, axis="y", bevel=0,
                matrix=sm)
    # глаза — маленькие, злые; брови тяжёлые
    ez = HEAD_C.z + 2.6
    for s in S2:
        x = s * 0.95
        n = V((s * 0.3, -1, 0.05))
        p = V((x, front_y(tiers, x, ez) + 0.03, ez))
        if P["face"] == "sleep":
            A.eye(a, p, 0.3, normal=n, closed=True, lid_key="dark", skin_key="pig", mood="calm", side=s,
                  brow_key="brow")
        elif P["face"] == "dizzy":
            m = T(p) @ A.facing(n)
            a.box("white", -0.32, 0.32, -0.03, 0.08, -0.32, 0.32, bevel=0, matrix=m)
            for ang in (45, -45):
                a.box("dark", -0.38, 0.38, -0.08, -0.02, -0.07, 0.07, bevel=0, matrix=m @ R("Y", ang))
        else:
            A.eye(a, p, 0.34, normal=n, mood="angry", side=s, skin_key="pig", brow_key="brow",
                  look=(0.0, -0.2), lid=0.32, brow_tilt=30, brow_lift=0.05, h=1.15)
    # стальной щиток на лбу с тремя заклёпками
    fz = HEAD_C.z + 3.1
    fyy = front_y(tiers, 0, fz)
    mf = T((0, fyy + 0.12, fz)) @ R("X", 34)
    a.box("steel", -1.2, 1.2, -0.2, 0.25, -0.42, 0.42, bevel=0.03, matrix=mf)
    a.box("steelL", -1.25, 1.25, -0.24, 0.0, -0.48, -0.3, bevel=0, matrix=mf)
    for x in (-0.8, 0.0, 0.8):
        stud(a, "gold", (mf @ V((x, -0.2, 0.08))), mf.to_3x3() @ V((0, -1, 0)), s=0.11, h=0.08)
    # нижняя челюсть «громилы» выступает вперёд; рот — щель над ней, клычки из челюсти вверх по бокам пятачка
    mouth = P["mouth"]
    jz = HEAD_C.z + 0.02
    jy = front_y(tiers, 0, jz + 0.3)
    pivot = V((0, jy + 1.3, jz + 0.3))
    a.transform = M["head"] @ about(pivot, R("X", {"roar": 26, "tongue": 14}.get(mouth, 0)))
    a.group = "Jaw"
    a.prism("pig", ring(0, 0, 1.6, 0.42), jy - 0.4, jy + 1.4, axis="y", bevel=0, matrix=T((0, 0, jz)))
    a.box("mouth", -1.35, 1.35, jy - 0.3, jy + 0.9, jz + 0.3, jz + 0.4, bevel=0)  # нёбо-щель на челюсти
    if mouth in ("roar", "tongue"):
        a.box("tongue", -0.65, 0.65, jy - 0.1, jy + 0.8, jz + 0.34, jz + 0.46, bevel=0)
    if mouth == "tongue":  # язык набок через губу
        taper(a, "tongue", (0.55, jy + 0.1, jz + 0.42), (0.95, jy - 0.6, jz - 0.35), 0.5, 0.42, 0.13, 0.11)
    if mouth != "sleep":
        for sx in S2:
            K.KEY = "tusk"
            b = V((sx * 1.52, jy - 0.15, jz + 0.2))
            K.taper(a, b, b + V((sx * 0.1, -0.1, 0.8)), 0.28, 0.14, 0.26, 0.13, up=(0, -1, 0), cut=0.2)
    a.transform, a.group = M["head"], "Head"
    if mouth in ("roar", "tongue"):  # тёмная глотка за открытой челюстью
        a.box("mouth", -1.25, 1.25, jy - 0.05, jy + 0.9, jz + 0.25, jz + 0.85, bevel=0)
    else:  # уголки рта приподняты — ухмылка (во сне ровно)
        up = 0.24 if mouth == "grin" else 0.0
        for sx in S2:
            x0, x1 = sx * 1.4, sx * 1.75
            taper(a, "mouth", (x0, front_y(tiers, x0, jz + 0.42) - 0.02, jz + 0.4),
                  (x1, front_y(tiers, x1, jz + 0.42 + up) - 0.02, jz + 0.42 + up), 0.1, 0.09, 0.1, 0.09,
                  up=(0, -1, 0))
    # уши: широкие, с изгибом — вверх-наружу, потом загнуты вперёд-вниз; в поражении повисли
    droop = P["ears"]
    for s in S2:
        base = V((s * 1.4, HEAD_C.y + 0.6, HEAD_C.z + 3.15))
        p1 = base + V((s * 0.6, -0.1, 0.9 - 1.2 * droop))
        p2 = p1 + V((s * 0.45, -0.6, 0.3 - 0.9 * droop))
        tip = p2 + V((s * 0.15, -0.55 + 0.3 * droop, -0.4 - 0.6 * droop))
        chain(a, "pig", [base, p1, p2, tip], [1.9, 1.6, 1.05, 0.26], [0.36, 0.32, 0.27, 0.15], up=(0, -1, 0.5),
              overlap=0.4)
        n = V((0, -0.16, 0.06))
        chain(a, "pigD", [base + n, p1 + n, p2 + n, tip + n * 0.6], [1.25, 1.05, 0.68, 0.12], [0.08] * 4,
              up=(0, -1, 0.5), overlap=0.3)
    return tiers


# ── Ноги ──────────────────────────────────────────────────────────────────────────────────────────────────────
def leg(a, M, s, front):
    m = M[("F" if front else "B", s)]
    a.transform, a.group = m, ("Leg" + ("F" if front else "B") + ("L" if s > 0 else "R"))
    y = SHOULDER_Y if front else HIP_Y
    x = s * (LEG_XF if front else LEG_XB)
    k = 1.0 if front else 0.82  # передние толще: тяжёлый перёд
    top = V((x, y, LEG_TOP))
    knee = V((x, y - 0.05, 1.2))
    ank = V((x, y - 0.1, 0.66))
    chain(a, "pig", [top, knee, ank], [2.05 * k, 1.8 * k, 1.55 * k], up=(0, -1, 0), overlap=0.5)
    # копыто — тёмное, широкое, с раздвоенным носком
    hw = 0.86 * k
    a.prism("hoof", ring(x, y - 0.15, hw, hw * 0.92, 12), 0.0, 0.7, bevel=0)
    a.box("pig", x - 0.07, x + 0.07, y - 0.15 - hw * 0.95, y - 0.15 - hw * 0.5, 0.02, 0.62, bevel=0)  # щель копыта
    # стальной наголенник спереди с двумя заклёпками
    a.box("steel", x - 0.72 * k, x + 0.72 * k, y - 0.98 * k, y - 0.55 * k, 0.82, 1.85, bevel=0.02)
    for zz in (1.05, 1.6):
        stud(a, "gold", (x, y - 0.98 * k, zz), (0, -1, 0), s=0.11, h=0.08)


# ── Эффекты позы: монеты, трещины, «Z» ────────────────────────────────────────────────────────────────────────
def coins_fx(a, M, P, top):
    kind = P["coins"]
    mb = M["body"]
    slot_c = V((0, (BANDS[0] + BANDS[1]) / 2, top + 0.08))
    a.group = "Fx"
    if kind in ("slot", "burst", "fountain"):
        a.transform = mb  # монета в прорези: наполовину торчит
        coin(a, slot_c, (0, -1, 0), r=0.72, th=0.16)  # наполовину в щели
    if kind == "burst":  # выскакивают дугой вверх-назад
        a.transform = mb
        for i, (dx, dy, dz, ang) in enumerate(((0.5, -0.4, 1.6, 20), (-0.7, 0.3, 2.4, -35), (0.3, 0.8, 3.2, 60),
                                                (-0.2, -0.2, 4.0, 10))):
            coin(a, slot_c + V((dx, dy, dz)), (math.sin(math.radians(ang)), 0.3, math.cos(math.radians(ang))),
                 r=0.42, th=0.12)
    if kind == "fountain":  # фонтан монет из прорези вверх (в мировых осях: тело на дыбах)
        sw = mb @ (slot_c + V((0, 0, 0.6)))
        a.transform = Matrix()
        for i in range(10):
            t = (i + 1) / 10
            ang = math.radians(i * 71)
            p = sw + V((1.9 * math.sin(ang) * t, 1.2 * t + 0.8 * math.cos(ang) * t, 1.2 + 4.2 * t - 1.3 * t * t))
            coin(a, p, (math.sin(ang), math.cos(ang), 0.7), r=0.44, th=0.12, spin=i * 17)
        for i, (x, y) in enumerate(((-2.6, -1.0), (2.2, -1.6), (3.4, 1.4), (-3.4, 2.2), (0.6, -2.6))):
            coin(a, V((x, y, 0.07)), (0.05 * (i % 2), 0.0, 1), r=0.42, th=0.12, spin=i * 25)
    if kind == "spill":
        spill(a, M)
    a.transform = Matrix()


def spill(a, M):
    """Поражение: трещины на боку и спине, отколотые осколки, горка монет из трещины на земле."""
    mb = M["body"]
    a.transform, a.group = mb, "Body"
    wx, wz, c = slice_at(0.4)
    # трещины: тёмные ломаные по левому (+x к игроку в 3/4 — правый бок модели −x) боку и по спине
    for s, pts in ((1, [(-1.2, 4.6, 1.5), (-0.6, 3.6, 1.0), (0.1, 4.0, 0.5), (0.8, 3.2, 0.0), (1.6, 3.7, -0.5)]),
                   (1, [(-0.9, 2.0, 0.4), (-0.3, 2.5, -0.1), (0.3, 1.9, -0.5)]),
                   (1, [(1.4, 4.2, 1.2), (1.9, 3.5, 0.8), (2.4, 4.0, 0.4)]),
                   (-1, [(-0.4, 4.4, 1.2), (0.4, 3.8, 0.6), (1.2, 4.2, 0.0)])):
        q = []
        for y, h, dz in pts:
            d = V((s * 1.0, 0, h / 4.6 * 0.9)).normalized()
            p = hull_point(wx, wz, c, d) + V((0, y, BODY_Z + dz))
            q.append(p + d * 0.02)
        chain(a, "crack", q, [0.16] * len(q), [0.12] * len(q), up=(s, 0, 0), overlap=0.3)
    # пролом на боку (тёмная дыра), из него — горка монет
    hole = hull_point(wx, wz, c, V((1, 0, -0.15)).normalized()) + V((0, 0.6, BODY_Z - 0.4))
    m = T(hole) @ A.facing((1, 0, -0.15))
    a.prism("slot", S.octagon(-0.7, 0.7, -0.55, 0.5, 0.25), -0.04, 0.3, axis="y", bevel=0, matrix=m)
    a.transform, a.group = Matrix(), "Fx"
    hw = mb @ hole
    base = V((hw.x + 1.5, hw.y - 0.6, 0.0))
    a.prism("coin", S.octagon(base.x - 1.5, base.x + 1.5, base.y - 1.3, base.y + 1.3, 0.6), 0.012, 0.3, bevel=0)
    a.prism("coinL", S.octagon(base.x - 0.95, base.x + 0.95, base.y - 0.8, base.y + 0.8, 0.4), 0.28, 0.55, bevel=0)
    for i, (dx, dy, dz, rr) in enumerate(((0, 0, 0.08, 0.5), (0.7, 0.4, 0.08, 0.45), (-0.6, 0.5, 0.08, 0.48),
                                          (0.2, -0.7, 0.08, 0.46), (-0.3, -0.1, 0.24, 0.45), (0.45, 0.15, 0.36, 0.42),
                                          (-0.1, 0.3, 0.5, 0.42), (0.9, -0.5, 0.08, 0.42), (-1.1, -0.4, 0.08, 0.44),
                                          (1.0, 1.1, 0.08, 0.4), (0.25, 0.35, 0.64, 0.38))):
        coin(a, base + V((dx, dy, dz)), (0.25 * math.sin(i * 1.7), 0.25 * math.cos(i * 2.3), 1), r=rr, th=0.12,
             spin=i * 31)
    for i, (dx, dy) in enumerate(((1.0, 1.6), (-2.2, 0.9), (2.0, -3.6))):  # монеты, укатившиеся вперёд
        coin(a, V((hw.x - dx + 1.6, hw.y - 3.4 + dy, 0.48)), (1, 0.3 * i, 0.2), r=0.42, th=0.12)
    for i, (x, y, ang) in enumerate(((4.9, -1.4, 20), (5.6, 1.6, -40), (3.6, 4.2, 65))):  # розовые осколки
        m = T((x, y, 0.0)) @ R("Z", ang)
        a.prism("pig", [(-0.5, -0.4), (0.55, -0.3), (0.3, 0.45), (-0.35, 0.35)], 0.0, 0.32 + 0.06 * i, axis="z",
                bevel=0.02, matrix=m)


def zzz(a, M):
    zp = [(0, 0), (0.7, 0), (0.12, -0.62), (0.72, -0.62), (0.72, -0.78), (-0.05, -0.78), (0.52, -0.16), (0, -0.16)]
    base_m = T(M["head"] @ V((2.8, -3.8, 5.8)))
    for i, (dx, dz, sc) in enumerate(((0.6, 0.4, 1.0), (1.4, 1.4, 0.8), (2.1, 2.2, 0.62))):
        a.transform, a.group = base_m @ T((dx, 0, dz)) @ R("Y", -12 * i) @ Matrix.Scale(sc, 4), "Fx"
        a.extrude("zz", zp, -0.07, 0.07, axis="y")
    a.transform = Matrix()


def piggy(pose="stand"):
    a = new_art("Piggy" + pose.capitalize())  # без «_»: ключ материала — после последнего «_»
    P = POSES[pose]
    M = skeleton(P)
    top = body(a, M, P)
    head(a, M, P)
    for s in S2:
        leg(a, M, s, True)
        leg(a, M, s, False)
    coins_fx(a, M, P, top)
    if pose == "sleep":
        zzz(a, M)
    a.transform, a.group = None, None
    return a
