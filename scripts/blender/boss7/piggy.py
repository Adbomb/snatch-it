"""Босс 7 «Банк» — Копилка-громила, концепт (D64 шаг 1 для босса 7): одна модель в позах стойка / сон / бой /
особая атака / поражение.

Образ: огромная бронированная свинья-копилка на четырёх коротких толстых ногах. Тело — бочка ярусами D39 (ярко-розовая),
поперёк бочки — два стальных обруча с золотыми заклёпками, между ними на спине — стальное «седло» с прорезью для монет
в золотой рамке, из прорези торчит монета. Голова — широкая, с большим светлым пятачком (две ноздри), уши-треугольники
загнуты вперёд, на лбу — стальной щиток с заклёпками, тяжёлые брови, маленькие злые глаза, рот-ухмылка с двумя тупыми
клычками. Ноги — розовые, с копытами и стальными наголенниками; хвост — пружинка-завиток. Розовое — главное пятно
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
    a.prism("coin", S.octagon(-r, r, -r, r, r * 0.29), -th / 2, th / 2, bevel=0, matrix=m)
    q = r * 0.66
    a.prism("coinL", S.octagon(-q, q, -q, q, q * 0.29), th / 2 - 0.02, th / 2 + 0.035, bevel=0, matrix=m)


# ── Пропорции ─────────────────────────────────────────────────────────────────────────────────────────────────
BODY_Y = (-3.1, 3.9)  # бочка от груди до крупа
BODY_Z = 3.95  # ось бочки
BODY_R = (3.05, 2.9)  # полуширина, полувысота
BODY_N = 9
CORNER = 0.52  # скос ярусов бочки — почти правильный восьмиугольник (круглее, чем у ящика)
HIP = V((0, 2.35, 2.3))  # тазобедренная ось — вокруг неё встаёт на дыбы
SHOULDER_Y, HIP_Y, LEG_X = -1.75, 2.35, 1.95
NECK = V((0, -2.7, 4.3))
BANDS = (-0.95, 1.8)  # обручи
LEG_TOP = 2.3  # верх ноги (внутри тела)


BODY_TIERS = ((-3.1, -2.6, 0.56), (-2.6, -1.95, 0.83), (-1.95, -1.3, 0.96), (-1.3, 2.3, 1.0), (2.3, 2.95, 0.94),
              (2.95, 3.45, 0.8), (3.45, 3.9, 0.56))  # (от y, до y, доля радиуса): торцы ступенями, середина — ровная


def slice_at(y):
    """Полуширина, полувысота и скос яруса бочки в точке y (вдоль оси)."""
    r = next((r for y0, y1, r in BODY_TIERS if y0 - 1e-6 <= y <= y1 + 1e-6), BODY_TIERS[-1][2])
    wx, wz = BODY_R[0] * r, BODY_R[1] * r
    return wx, wz, min(wx, wz) * CORNER


# ── Позы ──────────────────────────────────────────────────────────────────────────────────────────────────────
# lift — подъём тела (− опустить), pitch — наклон тела вокруг таза (+ перёд вниз, − на дыбы), roll — крен;
# head — (наклон вниз +, поворот, крен); front/back — ноги: (мах вперёд −/назад +, развод в стороны); face — лицо;
# mouth — "grin" / "roar" / "tongue"; coins — "slot" / "burst" / "fountain" / "spill"; ears — 0 торчат … 1 повисли.
POSES = {
    "stand": dict(lift=0.0, pitch=0, roll=0, head=(-4, 0, 0), front=(0, 4), back=(0, 4), face="angry", mouth="grin",
                  coins="slot", ears=0.0),
    "sleep": dict(lift=-1.55, pitch=3, roll=0, head=(16, 8, 4), front=(-82, 8), back=(84, 8), face="sleep",
                  mouth="sleep", coins="slot", ears=0.6),
    "combat": dict(lift=-0.15, pitch=7, roll=0, head=(16, 0, 0), front=(-14, 16), back=(14, 6), face="angry",
                   mouth="roar", coins="burst", ears=0.0),
    "special": dict(lift=0.0, pitch=-38, roll=0, head=(-12, 0, 0), front=(-48, 12), back=(0, 8), face="angry",
                    mouth="roar", coins="fountain", ears=0.0),
    "defeat": dict(lift=-1.45, pitch=5, roll=7, head=(26, -14, -10), front=(-30, 58), back=(30, 58), face="dizzy",
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
        M[("F", s)] = M["body"] @ about((s * LEG_X, SHOULDER_Y, LEG_TOP), R("X", fs) @ R("Y", -s * fo))
        # задние ноги: тело встаёт на дыбы вокруг таза, ноги остаются вертикально на земле
        M[("B", s)] = M["body"] @ about((s * LEG_X, HIP_Y, LEG_TOP),
                                        R("Y", -P["roll"]) @ R("X", -P["pitch"]) @ R("X", bs) @ R("Y", -s * bo))
    return M


# ── Тело ──────────────────────────────────────────────────────────────────────────────────────────────────────
def body(a, M, P):
    a.transform, a.group = M["body"], "Body"
    y0, y1 = BODY_Y
    for i, (ya, yb, r) in enumerate(BODY_TIERS):  # ярусы вдоль оси y (бочка лёжа), заходят друг в друга на 0.01
        wx, wz = BODY_R[0] * r, BODY_R[1] * r
        a.prism("pig", S.octagon(-wx, wx, BODY_Z - wz, BODY_Z + wz, min(wx, wz) * CORNER), ya - (0.01 if i else 0),
                yb + 0.01, axis="y", bevel=0.02)
    # обручи: восьмигранная рамка чуть шире яруса, золотые заклёпки по верхней половине
    for yb in BANDS:
        wx, wz, c = slice_at(yb)
        wx, wz = wx + 0.2, wz + 0.2
        pts = S.octagon(-wx, wx, BODY_Z - wz, BODY_Z + wz, c + 0.08)
        a.frame("steel", pts, 0.55, yb - 0.42, yb + 0.42, axis="y", bevel=0.02)
        a.frame("steelL", S.octagon(-wx - 0.06, wx + 0.06, BODY_Z - wz - 0.06, BODY_Z + wz + 0.06, c + 0.1), 0.2,
                yb - 0.5, yb - 0.3, axis="y", bevel=0)  # светлая кромка спереди обруча
        for ang in (10, 38, 66, 90, 114, 142, 170):
            t = math.radians(ang)
            d = V((math.cos(t), 0, math.sin(t)))
            p = hull_point(wx, wz, c + 0.08, d) + V((0, yb + 0.02, BODY_Z))
            stud(a, "gold", p, d, s=0.13, h=0.1)
    # наплечники «громилы»: стальные щиты на боках у плеч, золотой обод и заклёпка
    wx, wz, c = slice_at(-1.6)
    for sx in S2:
        m = T((sx * (wx - 0.08), -1.75, BODY_Z + 0.55)) @ R("Y", sx * 90)
        a.prism("steel", S.octagon(-1.2, 1.2, -1.2, 1.2, 0.5), 0.0, 0.32, bevel=0.03, matrix=m)
        a.frame("gold", S.octagon(-1.28, 1.28, -1.28, 1.28, 0.53), 0.16, 0.12, 0.38, axis="z", bevel=0, matrix=m)
        stud(a, "gold", m @ V((0, 0, 0.32)), (sx, 0, 0), s=0.2, h=0.12)
    # седло со щелью-прорезью на спине (между обручами)
    _, wz_top, _ = slice_at(0.5)
    top = BODY_Z + wz_top
    a.box("steel", -1.6, 1.6, BANDS[0] + 0.35, BANDS[1] - 0.35, top - 0.25, top + 0.15, bevel=0.03)
    yc = (BANDS[0] + BANDS[1]) / 2  # прорезь поперёк спины: монета в ней смотрит на игрока
    a.frame("gold", [(-1.12, yc - 0.42), (1.12, yc - 0.42), (1.12, yc + 0.42), (-1.12, yc + 0.42)], 0.24,
            top + 0.18, top + 0.42, axis="z", bevel=0)
    a.box("slot", -0.9, 0.9, yc - 0.19, yc + 0.19, top + 0.1, top + 0.34, bevel=0)
    for x, y in ((-1.35, BANDS[0] + 0.55), (1.35, BANDS[0] + 0.55), (-1.35, BANDS[1] - 0.55),
                 (1.35, BANDS[1] - 0.55)):
        stud(a, "gold", (x, y, top + 0.18), (0, 0, 1), s=0.13, h=0.1)
    # хвост-завиток на крупе
    pts = []
    for i in range(9):
        t = math.radians(-30 + i * 52)
        r = 0.55 - 0.03 * i
        pts.append((r * math.cos(t), BODY_Y[1] + 0.25 + 0.06 * i, BODY_Z + 1.2 + r * math.sin(t)))
    pts[0] = (0.2, BODY_Y[1] - 0.35, BODY_Z + 0.95)
    a.group = "Tail"
    chain(a, "pig", pts, [0.42] + [0.32] * 7 + [0.24], up=(0, 1, 0), overlap=0.5)
    a.group = "Body"
    return top


def hull_point(wx, wz, c, d):
    """Точка на восьмиграннике (полуоси wx, wz, скос c) в направлении d (в плоскости xz, вокруг начала)."""
    best = None
    pts = S.octagon(-wx, wx, -wz, wz, c)
    for i in range(len(pts)):
        (x0, z0), (x1, z1) = pts[i], pts[(i + 1) % len(pts)]
        ex, ez = x1 - x0, z1 - z0
        den = d.x * ez - d.z * ex
        if abs(den) < 1e-9:
            continue
        t = (x0 * ez - z0 * ex) / den
        u = (x0 * d.z - z0 * d.x) / den if abs(den) > 1e-9 else -1
        if t > 0 and -1e-6 <= u <= 1 + 1e-6 and (best is None or t < best):
            best = t
    return V((d.x * best, 0, d.z * best))


# ── Голова ────────────────────────────────────────────────────────────────────────────────────────────────────
HEAD_C = V((0, -3.75, 2.45))  # низ головы
HEAD_R = (2.3, 2.0, 3.7)


def front_y(tiers, x, z):
    for za, zb, bx, y, wx, wy, c in tiers:
        if za - 1e-6 <= z <= zb + 1e-6:
            flat = wx - c
            dx = abs(x - bx)
            return y - wy + max(0.0, dx - flat)
    za, zb, bx, y, wx, wy, c = tiers[-1]
    return y - wy


def head(a, M, P):
    a.transform, a.group = M["head"], "Head"
    tiers = A.body(a, "pig", tuple(HEAD_C), HEAD_R[0], HEAD_R[1], HEAD_R[2], "egg", n=6, floor=0.45, corner=0.46)
    # пятачок: светлый восьмигранный «пятак» вперёд, на нём две ноздри
    sz = HEAD_C.z + 1.5
    fy = front_y(tiers, 0, sz)
    sm = T((0, 0, sz))
    a.prism("snout", S.octagon(-1.2, 1.2, -0.9, 0.9, 0.5), fy - 0.85, fy + 0.35, axis="y", bevel=0.02,
            matrix=sm)  # ось y: от fy−0.72 (наружу) до fy+0.35 (в голове)
    for s in S2:
        a.prism("nostril", S.octagon(s * 0.45 - 0.18, s * 0.45 + 0.18, -0.28, 0.28, 0.09), fy - 0.89, fy - 0.83,
                axis="y", bevel=0, matrix=sm)
    a.prism("pigD", S.octagon(-1.27, 1.27, -0.97, 0.97, 0.52), fy - 0.1, fy + 0.2, axis="y", bevel=0,
            matrix=sm)  # тёмная «шея» пятачка у головы
    # глаза — маленькие, злые; брови тяжёлые
    ez = HEAD_C.z + 2.7
    for s in S2:
        x = s * 0.88
        p = V((x, front_y(tiers, x, ez) + 0.02, ez))
        if P["face"] == "sleep":
            A.eye(a, p, 0.27, normal=(s * 0.25, -1, 0.05), closed=True, lid_key="dark", skin_key="pig",
                  mood="calm", side=s, brow_key="brow")
        elif P["face"] == "dizzy":
            m = T(p) @ A.facing((s * 0.25, -1, 0.05))
            a.box("white", -0.3, 0.3, -0.03, 0.08, -0.3, 0.3, bevel=0, matrix=m)
            for ang in (45, -45):
                a.box("dark", -0.36, 0.36, -0.08, -0.02, -0.07, 0.07, bevel=0, matrix=m @ R("Y", ang))
        else:
            A.eye(a, p, 0.33, normal=(s * 0.25, -1, 0.05), mood="angry", side=s, skin_key="pig", brow_key="brow",
                  look=(0.0, -0.2), lid=0.32, brow_tilt=30, brow_lift=0.05, h=1.15)
    # стальной щиток на лбу с тремя заклёпками
    fz = HEAD_C.z + 3.3
    fyy = front_y(tiers, 0, fz)
    mf = T((0, fyy + 0.1, fz)) @ R("X", 32)
    a.box("steel", -1.15, 1.15, -0.2, 0.25, -0.42, 0.42, bevel=0.03, matrix=mf)
    a.box("steelL", -1.2, 1.2, -0.24, 0.0, -0.48, -0.3, bevel=0, matrix=mf)
    for x in (-0.75, 0.0, 0.75):
        stud(a, "gold", (mf @ V((x, -0.2, 0.08))), mf.to_3x3() @ V((0, -1, 0)), s=0.11, h=0.08)
    # нижняя челюсть «громилы» чуть выступает вперёд; рот — щель над ней, клычки из челюсти вверх по бокам пятачка
    mouth = P["mouth"]
    jz = HEAD_C.z + 0.22
    jy = front_y(tiers, 0, jz)
    pivot = V((0, jy + 1.3, jz + 0.3))
    a.transform = M["head"] @ about(pivot, R("X", {"roar": 26, "tongue": 14}.get(mouth, 0)))
    a.group = "Jaw"
    a.prism("pig", S.octagon(-1.45, 1.45, -0.42, 0.36, 0.3), jy - 0.32, jy + 1.4, axis="y", bevel=0.02,
            matrix=T((0, 0, jz)))
    a.box("mouth", -1.25, 1.25, jy - 0.24, jy + 0.9, jz + 0.3, jz + 0.4, bevel=0)  # нёбо-щель на челюсти
    if mouth in ("roar", "tongue"):
        a.box("tongue", -0.6, 0.6, jy - 0.05, jy + 0.8, jz + 0.34, jz + 0.46, bevel=0)
    if mouth == "tongue":  # язык набок через губу
        taper(a, "tongue", (0.55, jy + 0.1, jz + 0.42), (0.95, jy - 0.55, jz - 0.35), 0.5, 0.42, 0.13, 0.11)
    if mouth != "sleep":
        for sx in S2:
            K.KEY = "tusk"
            b = V((sx * 1.38, jy - 0.1, jz + 0.2))
            K.taper(a, b, b + V((sx * 0.1, -0.1, 0.72)), 0.26, 0.13, 0.24, 0.12, up=(0, -1, 0), cut=0.2)
    a.transform, a.group = M["head"], "Head"
    if mouth in ("roar", "tongue"):  # тёмная глотка за открытой челюстью
        a.box("mouth", -1.2, 1.2, jy - 0.05, jy + 0.9, jz + 0.25, jz + 0.85, bevel=0)
    else:  # уголки рта приподняты — ухмылка (во сне ровно)
        up = 0.22 if mouth == "grin" else 0.0
        for sx in S2:
            x0, x1 = sx * 1.2, sx * 1.55
            taper(a, "mouth", (x0, front_y(tiers, x0, jz + 0.4) - 0.02, jz + 0.38),
                  (x1, front_y(tiers, x1, jz + 0.4 + up) - 0.02, jz + 0.4 + up), 0.09, 0.08, 0.09, 0.08,
                  up=(0, -1, 0))
    # уши: треугольные, загнуты вперёд; в поражении повисли
    droop = P["ears"]
    for s in S2:
        base = V((s * 1.35, HEAD_C.y + 0.45, HEAD_C.z + 3.45))
        mid = base + V((s * (0.75 + 0.35 * droop), -0.35 - 0.2 * droop, 1.0 - 1.4 * droop))
        tip = mid + V((s * (0.35 + 0.3 * droop), -1.0 + 0.4 * droop, -0.15 - 0.9 * droop))
        chain(a, "pig", [base, mid, tip], [1.75, 1.3, 0.3], [0.34, 0.3, 0.16], up=(0, -1, 0.5), overlap=0.4)
        inner = [base + V((0, -0.17, 0.05)), mid + V((0, -0.17, 0.0)), tip + V((0, -0.1, 0.0))]
        chain(a, "pigD", inner, [1.15, 0.85, 0.15], [0.08, 0.08, 0.06], up=(0, -1, 0.5), overlap=0.3)
    return tiers


# ── Ноги ──────────────────────────────────────────────────────────────────────────────────────────────────────
def leg(a, M, s, front):
    m = M[("F" if front else "B", s)]
    a.transform, a.group = m, ("Leg" + ("F" if front else "B") + ("L" if s > 0 else "R"))
    y = SHOULDER_Y if front else HIP_Y
    x = s * LEG_X
    top = V((x, y, LEG_TOP))
    knee = V((x, y - 0.05, 1.1))
    ank = V((x, y - 0.1, 0.62))
    chain(a, "pig", [top, knee, ank], [1.55, 1.3, 1.15], up=(0, -1, 0), overlap=0.5)
    # копыто — тёмный восьмигранник с раздвоенным носком
    a.prism("hoof", S.octagon(x - 0.66, x + 0.66, y - 0.78, y + 0.52, 0.3), 0.0, 0.66, bevel=0.02)
    a.box("pig", x - 0.06, x + 0.06, y - 0.83, y - 0.3, 0.02, 0.6, bevel=0)  # щель между пальцами копыта
    # стальной наголенник спереди с двумя заклёпками
    a.box("steel", x - 0.6, x + 0.6, y - 0.82, y - 0.45, 0.78, 1.75, bevel=0.02)
    for zz in (1.0, 1.5):
        stud(a, "gold", (x, y - 0.82, zz), (0, -1, 0), s=0.1, h=0.08)


# ── Эффекты позы: монеты, трещины, «Z» ────────────────────────────────────────────────────────────────────────
def coins_fx(a, M, P, top):
    kind = P["coins"]
    mb = M["body"]
    slot_c = V((0, (BANDS[0] + BANDS[1]) / 2, top + 0.2))
    a.group = "Fx"
    if kind in ("slot", "burst", "fountain"):
        a.transform = mb  # монета в прорези: наполовину торчит
        coin(a, slot_c + V((0, 0, 0.5)), (0, -1, 0), r=0.78, th=0.16)
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
    base_m = T(M["head"] @ V((2.6, -3.0, 6.6)))
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
