"""Босс 5 «Ледник» — Йети-коллекционер (концепт, D64): одна модель в позах стойка / сон / бой / поражение.

Образ: огромный сутулый йети-коллекционер. Короткие кривые ноги, могучие предплечья (костяшки почти у земли), голова
утоплена в плечи. Мех — ступенчатые пряди D39 (рваный воротник на груди, пряди на плечах и локтях, «юбка» над бёдрами,
хохолок на макушке). Лицо — тёмная индиговая маска: тяжёлое надбровье, светящиеся ледяные глаза, неправильный прикус с
двумя бивнями, золотой монокль на правом глазу — знаток. Коллекционер: кожаная портупея крест-накрест с золотым
знаком-снежинкой, пояс с музейными бирками, связкой ключей и лупой. На спине — ледяная глыба-витрина в золотых
уголках: в ней вморожены экспонаты (кубок, самоцвет, Ловибум, маленькое существо). Глыба выше головы — силуэт
читается спереди. При поражении глыба трескается: осколки и экспонаты падают на землю (только оформление: правила боя,
добычи и краж не меняются — D64).

Построение как у дракона v7 (стиль D39, art_style): слоёные боковые профили (средняя пластина — полный профиль,
внешние — уменьшенные копии), сужающиеся восьмигранные звенья (руки, ноги, пальцы), половины головы под углом (лицо
не прямоугольник), острые пирамиды (пряди меха, когти, бивни). Поза — «скелет» матриц: таз → торс → голова / плечи →
локти → кисти, бёдра → колени → стопы. Координаты: z вверх, лицо в −y, 1 единица ≈ 2.6 стада в игре (рост ≈ 24 стада).
Зависит от scripts/blender/art_style.py и scripts/blender/dragon10/v4_kit.py.
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
    "fur": ("EEF4FF", True), "furS": ("CBDAF3", True), "furD": ("A3B7E0", False),
    "skin": ("4B3C93", True), "skinD": ("33286E", False), "nose": ("1C1640", False),
    "mouth": ("2A1640", False), "tongue": ("E8507A", False), "ivory": ("F3E9D2", False),
    "neonEye": ("7FF4FF", False), "pupil": ("1A2A55", False), "dark": ("161824", False),
    "leather": ("A9582C", True), "leatherD": ("6E3519", False),
    "gold": ("F5B21C", True), "goldS": ("F5B21C", False), "goldD": ("C27E0E", False),
    "iceBlock": ("7FD6FF", False), "iceD": ("4FC3EA", False), "iceE": ("E2FAFF", False),
    "lens": ("B4F8FF", False), "tag": ("E8384F", False), "tagW": ("FFF3DC", False),
    "neonGem": ("FF4FA3", False), "neonCrystal": ("2FE6D8", False), "crystalD": ("1596A8", False),
    "white": ("FFFFFF", False), "critter": ("FF9F1C", False), "steel": ("8C97B5", False),
}


def key(k):
    K.KEY = k


def new_art(name):
    a = S.Art(name, ring_z0=3.0)
    a.ring = dict(S.RING, core=0.55)  # профиль контура «полка», как у дракона v7
    for k, (code, rings) in PALETTE.items():
        a.paint(k, code, rings=rings)
    return a


def R(axis, deg):
    return Matrix.Rotation(math.radians(deg), 4, axis)


def T(v):
    return Matrix.Translation(V(v))


def slab(a, prof, x0, x1, matrix=None):
    K.slab(a, prof, x0, x1, matrix=matrix)


def half(a, prof, w, s, ang, pz, x0=-0.1, extra=None):
    """Половина слоя головы под углом ang вокруг вертикали — лицо не прямоугольник спереди (как у дракона v6)."""
    c = V((0, 0, pz))
    m = T(c) @ R("Y", ang * s) @ T(-c)
    slab(a, prof, s * x0, s * w, matrix=m if extra is None else extra @ m)


def tufts(a, pts, size, out, down=0.75, k="fur"):
    """Пряди меха — острые пирамиды из точек pts по направлению out (вектор) с наклоном вниз."""
    key(k)
    for i, p in enumerate(pts):
        p = V(p)
        d = (V(out(p)) if callable(out) else V(out)).normalized()
        s = size * (1.0 if i % 2 == 0 else 0.78)
        tip = p + d * s * (1 - down) + V((0, 0, -s * down))
        K.spike(a, p, tip, s * 0.62)


# ── Позы ──────────────────────────────────────────────────────────────────────────────────────────────────────
# swing — мах руки вперёд (градусы), abd — отвод в сторону, elbow — сгиб в локте, wrist — сгиб кисти;
# hip — сгиб бедра вперёд, knee — сгиб колена, ankle — стопа; face — выражение; jaw — открытие пасти.
POSES = {
    "stand": dict(pelvis=(0, 0, 2.3), pitch=0, torso=16, head=(-14, 0, 0), face="smug", jaw=0,
                  arm={1: (34, 12, 26, 10), -1: (28, 14, 22, 8)}, leg={1: (12, 26, 0), -1: (12, 26, 0)}),
    "sleep": dict(pelvis=(0, 0.1, 1.15), pitch=0, torso=-8, head=(16, 0, 14), face="sleep", jaw=0,
                  arm={1: (18, 22, 42, 35), -1: (16, 24, 46, 35)}, leg={1: (80, 30, -20), -1: (76, 26, -18)}),
    "combat": dict(pelvis=(0, 0, 2.2), pitch=0, torso=10, head=(-20, 0, 0), face="roar", jaw=26,
                   arm={1: (40, 34, 64, 15), -1: (10, 160, 25, 0)}, leg={1: (18, 34, 0), -1: (4, 18, 0)}),
    "defeat": dict(pelvis=(0, 0.2, 1.1), pitch=0, torso=-14, head=(-4, 14, 18), face="dizzy", jaw=12,
                   arm={1: (-8, 52, 14, -10), -1: (-14, 56, 20, -6)}, leg={1: (78, 34, 30), -1: (70, 24, 30)}),
}

# опорные точки скелета (покой): в системе таза (начало — центр таза)
SHOULDER = V((2.35, -0.2, 3.55))
NECK = V((0.0, -0.55, 3.95))
HIP = V((1.2, 0.15, 0.0))
UPPER, FORE, THIGH, SHIN = 2.05, 2.3, 1.15, 1.0

TORSO = [(-1.05, 0.25), (-1.45, 1.2), (-1.58, 2.35), (-1.42, 3.3), (-0.95, 4.05), (0.4, 4.25), (1.15, 3.6),
         (1.35, 2.4), (1.2, 1.2), (0.95, 0.35), (0.55, -0.3), (-0.55, -0.32)]


def front_y(z, prof=TORSO):
    """y передней поверхности торса на высоте z (по профилю TORSO, его передней части)."""
    front = sorted([p for p in prof if p[0] < 0], key=lambda p: p[1])
    for (y0, z0), (y1, z1) in zip(front, front[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0) if z1 > z0 else 0.0
            return y0 + (y1 - y0) * t
    return front[0][0] if z < front[0][1] else front[-1][0]


def skeleton(pose):
    P = POSES[pose]
    M = {}
    M["pelvis"] = T(P["pelvis"]) @ R("X", P["pitch"])  # +: наклон вперёд (лицо в −y)
    M["torso"] = M["pelvis"] @ R("X", P["torso"])
    hp, hy, hr = P["head"]
    M["head"] = M["torso"] @ T(NECK) @ R("Z", hy) @ R("X", hp) @ R("Y", hr)  # hp > 0 — смотрит вниз
    for s in S2:
        sw, ab, el, wr = P["arm"][s]
        M[("sh", s)] = M["torso"] @ T(V((s * SHOULDER.x, SHOULDER.y, SHOULDER.z))) @ R("Y", -s * ab) @ R("X", -sw)
        M[("el", s)] = M[("sh", s)] @ T((0, 0, -UPPER)) @ R("X", -el)
        M[("wr", s)] = M[("el", s)] @ T((0, 0, -FORE)) @ R("X", -wr)
        hf, kn, an = P["leg"][s]
        M[("hip", s)] = M["pelvis"] @ T(V((s * HIP.x, HIP.y, HIP.z))) @ R("X", -hf)
        M[("kn", s)] = M[("hip", s)] @ T((0, 0, -THIGH)) @ R("X", kn)
        M[("an", s)] = M[("kn", s)] @ T((0, 0, -SHIN)) @ R("X", hf - kn - P["pitch"] + an)  # стопа ровно + an
    return M


# ── Части ─────────────────────────────────────────────────────────────────────────────────────────────────────
def torso(a, M):
    a.transform, a.group = M, "Torso"
    key("fur")
    K.layered(a, TORSO, [(1.3, 1.0, 1.0), (1.7, 0.94, 0.95), (1.935, 0.85, 0.88)], (0.05, 2.0))  # 1.935 / 1.92 / 1.435:
    # грани слоёв не совпадают между собой и с глыбой (±1.95) и её спинкой (±1.45)
    # грудь шире талии (V-силуэт) и горб трапеций — голова утоплена в плечи
    chest = [(-1.52, 2.1), (-1.62, 2.6), (-1.47, 3.4), (-0.97, 4.12), (0.4, 4.32), (1.2, 3.62), (1.32, 2.4),
             (0.8, 1.9), (-1.2, 1.9)]
    K.layered(a, chest, [(2.3, 1.0, 1.0), (2.6, 0.88, 0.84)], (0.0, 3.1))
    trap = [(-0.7, 3.8), (-0.45, 4.75), (0.5, 4.95), (1.2, 4.25), (0.6, 3.7)]
    K.layered(a, trap, [(1.435, 1.0, 1.0), (1.92, 0.85, 0.82)], (0.2, 4.2))
    key("furS")  # живот: светлее, с кольцами D39
    belly = [(-1.12, 0.35), (-1.53, 1.25), (-1.66, 2.35), (-1.5, 3.05), (-1.0, 3.05), (-1.0, 0.35)]
    slab(a, belly, -1.1, 1.1)
    # рваный воротник под подбородком и пряди на груди по бокам
    collar = [(s * x, front_y(3.75) - 0.05, 3.85) for x in (0.0, 0.62, 1.22, 1.75) for s in S2 if not (x == 0 and s < 0)]
    tufts(a, collar, 0.85, (0, -0.35, -1), down=0.85)
    side = [(s * 2.05, -0.55 + dy, z) for s in S2 for dy, z in ((0.0, 3.2), (0.55, 2.2))]
    tufts(a, side, 0.7, lambda p: (math.copysign(1, p.x), -0.2, -0.6), down=0.6)
    # «юбка» меха над бёдрами — под поясом по кругу
    skirt = []
    for i in range(14):
        t = 2 * math.pi * i / 14
        skirt.append((2.05 * math.sin(t), -0.1 - 1.15 * math.cos(t), 0.35))
    tufts(a, skirt, 0.8, lambda p: (p.x, p.y + 0.1, -1.2), down=0.8)


def harness(a, M):
    """Портупея крест-накрест, золотой знак-снежинка, пояс, бирки, ключи и лупа."""
    a.transform, a.group = M, "Torso"
    off = 0.13
    for s in S2:
        pts = [(s * 1.55, -0.2, 4.15), (s * 1.12, front_y(3.4) - off, 3.4), (s * 0.45, front_y(2.6) - off - 0.05, 2.6),
               (-s * 0.35, front_y(1.75) - off - 0.06, 1.75), (-s * 1.05, front_y(1.0) - off - 0.02, 1.0),
               (-s * 1.55, front_y(0.6) - off, 0.6)]
        key("leather")
        K.chain(a, pts, [0.42] * len(pts), [0.12] * len(pts), up=(0, -1, 0), cut=0.15, overlap=0.1)
        key("goldS")  # заклёпки
        for p in pts[1:-1]:
            a.box("goldS", p[0] - 0.07, p[0] + 0.07, p[1] - 0.1, p[1] - 0.04, p[2] - 0.07, p[2] + 0.07, bevel=0.01)
    # знак-снежинка на перекрестье
    c = V((0.0, front_y(2.2) - 0.25, 2.2))
    m = T(c) @ R("X", 90)
    a.prism("gold", S.octagon(-0.48, 0.48, -0.48, 0.48, 0.16), -0.06, 0.1, axis="z", matrix=m)
    a.prism("goldD", S.octagon(-0.36, 0.36, -0.36, 0.36, 0.12), 0.1, 0.13, axis="z", matrix=m)
    for ang in (0, 60, 120):
        mm = m @ R("Z", ang)
        a.box("neonCrystal", -0.07, 0.07, -0.42, 0.42, 0.12, 0.2, bevel=0, matrix=mm)
    # пояс
    a.frame("leather", S.octagon(-2.22, 2.22, -1.42, 1.15, 0.6), 0.2, 0.38, 0.72, axis="z", bevel=0.008)
    a.box("gold", -0.38, 0.38, -1.52, -1.32, 0.33, 0.78, bevel=0.02)
    a.box("goldD", -0.2, 0.2, -1.56, -1.5, 0.45, 0.66, bevel=0)
    # музейные бирки на шнурках (номера — точками, без текста)
    for x, z, ang, kk in ((-1.35, 0.2, -8, "tag"), (-0.95, 0.05, 6, "tagW"), (1.05, 0.12, -5, "tag")):
        y = -1.33 if abs(x) < 1.2 else -1.15
        mt = T((x, y, z)) @ R("Y", ang)
        a.box(kk, -0.2, 0.2, -0.05, 0.05, -0.32, 0.0, bevel=0.01, matrix=mt)
        a.box("dark", -0.1, -0.02, -0.075, -0.045, -0.12, -0.04, bevel=0, matrix=mt)
        a.box("dark", 0.02, 0.1, -0.075, -0.045, -0.12, -0.04, bevel=0, matrix=mt)
        a.box("leatherD", -0.025, 0.025, -0.03, 0.03, 0.0, 0.42, bevel=0, matrix=mt)
    # связка ключей у правого бедра
    kc = V((1.8, -0.95, 0.15))
    mk = T(kc) @ R("Z", 25)
    a.frame("goldS", S.octagon(-0.28, 0.28, -0.28, 0.28, 0.09), 0.07, -0.04, 0.04, axis="y", matrix=mk)
    for i, ang in enumerate((-22, 0, 24)):
        mm = mk @ R("Y", ang) @ T((0, 0, -0.28))
        a.box("gold", -0.045, 0.045, -0.03, 0.03, -0.62, 0.0, bevel=0, matrix=mm)
        a.box("gold", 0.0, 0.16, -0.03, 0.03, -0.6, -0.5, bevel=0, matrix=mm)
        a.box("gold", 0.0, 0.11, -0.03, 0.03, -0.44, -0.36, bevel=0, matrix=mm)
    # лупа у левого бедра
    lc = V((-1.95, -0.8, 0.0))
    ml = T(lc) @ R("Z", -30) @ R("Y", 12)
    a.frame("goldS", S.octagon(-0.36, 0.36, -0.36, 0.36, 0.12), 0.08, -0.05, 0.05, axis="y", matrix=ml)
    a.prism("lens", S.octagon(-0.29, 0.29, -0.29, 0.29, 0.1), -0.02, 0.02, axis="y", matrix=ml)
    a.box("leatherD", -0.06, 0.06, -0.05, 0.05, 0.36, 0.95, bevel=0.01, matrix=ml)


def ice_block(a, M, broken=False, lean=0.0):
    """Глыба-витрина на спине: высокий гранёный кристалл выше головы, кожаные обвязки, золотые уголки, сосульки снизу,
    экспонаты внутри (лёд полупрозрачный). broken — после поражения: от глыбы остался нижний обломок с зубцами."""
    piv = V((0, 1.05, 1.6))  # глыба стоит ровнее торса: наклон торса компенсирован наполовину
    a.transform, a.group = M @ T(piv) @ R("X", -lean * 0.5) @ T(-piv), "Block"
    x0, x1, y0, y1 = -1.95, 1.95, 0.85, 3.05
    z0, z1 = 1.6, (7.2 if not broken else 3.6)
    # extrude, а не prism: невыпуклая деталь не прячет грани экспонатов внутри (лёд прозрачный)
    a.extrude("iceBlock", S.octagon(x0, x1, y0, y1, 0.55), z0, z1, axis="z")
    if not broken:  # гранёная верхушка со сколом и кристаллы
        a.frustum("iceBlock", (x0 + 0.2, x1 - 0.2, y0 + 0.15, y1 - 0.15), (-1.3, 0.9, 1.55, 2.85), z1, z1 + 0.85, bevel=0)
        a.frustum("iceE", (-1.3, 0.9, 1.55, 2.85), (-0.7, -0.1, 2.0, 2.4), z1 + 0.85, z1 + 1.45, bevel=0)
        for x, y, h, lean, w in ((1.3, 1.8, 1.6, 0.5, 0.6), (-1.45, 2.55, 1.2, -0.45, 0.5), (0.35, 2.9, 0.9, 0.2, 0.42),
                                 (-0.4, 1.5, 0.75, -0.1, 0.36)):
            key("iceD")
            K.spike(a, (x, y, z1 + 0.25), (x + lean, y + 0.1, z1 + 0.25 + h), w)
    else:  # сломанный край — зубцы
        for i in range(9):
            x = x0 + 0.3 + i * (x1 - x0 - 0.6) / 8
            key("iceBlock" if i % 2 else "iceE")
            K.spike(a, (x, (y0 + y1) / 2 + (0.3 if i % 2 else -0.3), z1 - 0.05),
                    (x + 0.1, (y0 + y1) / 2, z1 + 0.55 + 0.35 * (i % 3)), 0.6)
    if broken:
        cracks(a, y0 - 0.02, z0 + 0.3, z1 - 0.1)
        cracks(a, y1 + 0.02, z0 + 0.3, z1 - 0.1, flip=True)
    if not broken:  # рама-носилка между спиной и глыбой (как у заплечного короба): глыба не висит в воздухе
        a.box("leatherD", -1.45, 1.45, y0 - 0.85, y0 + 0.05, 2.3, 6.3, bevel=0.03)
        for x in (-1.1, 1.1):
            for z in (2.7, 4.3, 5.9):
                a.box("goldS", x - 0.12, x + 0.12, y0 - 0.92, y0 - 0.8, z - 0.12, z + 0.12, bevel=0.02)
    # блики на рёбрах
    for x in (x0 + 0.02, x1 - 0.02):
        a.box("iceE", x - 0.04, x + 0.04, y0 + 0.35, y0 + 0.85, z0 + 0.3, z1 - 0.3, bevel=0)
    # сосульки по нижнему краю
    for i, x in enumerate((-1.55, -0.9, -0.2, 0.55, 1.2, 1.7)):
        key("iceD" if i % 2 else "iceE")
        K.spike(a, (x, y1 - 0.25, z0 + 0.02), (x, y1 - 0.2, z0 - 0.45 - 0.25 * (i % 3)), 0.32)
    # кожаные обвязки вокруг глыбы и лямки к плечам
    for zb in ((2.3, 6.3) if not broken else (2.3,)):
        a.frame("leather", S.octagon(x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, 0.6), 0.16, zb, zb + 0.38, axis="z",
                bevel=0.008)
        for x in (x0 - 0.14, x1 + 0.14):
            a.box("gold", x - 0.06, x + 0.06, 1.95, 2.45, zb - 0.06, zb + 0.44, bevel=0.015)
    if not broken:
        for s in S2:
            key("leather")
            K.chain(a, [(s * 1.25, 1.1, 6.45), (s * 1.55, 0.3, 4.75), (s * 1.55, -0.2, 4.2)], [0.42] * 3, [0.13] * 3,
                    up=(1, 0, 0), cut=0.15, overlap=0.15)
    # золотые уголки витрины
    for x in (x0, x1):
        sx = 1 if x > 0 else -1
        for y in (y0 + 0.3, y1 - 0.3):
            for z, sz in ((z0, 1), (z1, -1)):
                a.box("gold", x - sx * 0.05, x + sx * 0.12, y - 0.35, y + 0.35, z - sz * 0.06, z + sz * 0.55,
                      bevel=0.015)
    # табличка сзади
    a.box("gold", -0.75, 0.75, y1 + 0.02, y1 + 0.1, z0 + 0.95, z0 + 1.45 if not broken else z0 + 1.45, bevel=0.02)
    a.box("goldD", -0.55, 0.55, y1 + 0.1, y1 + 0.13, z0 + 1.08, z0 + 1.32, bevel=0)
    if not broken:
        exhibits(a, inside=True)


def trophy(a, c, sc=1.0):
    x, y, z = c
    a.prism("gold", S.octagon(x - 0.42 * sc, x + 0.42 * sc, y - 0.42 * sc, y + 0.42 * sc, 0.12 * sc), z, z + 0.16 * sc)
    a.prism("goldD", S.octagon(x - 0.12 * sc, x + 0.12 * sc, y - 0.12 * sc, y + 0.12 * sc, 0.04 * sc), z + 0.16 * sc, z + 0.55 * sc)
    a.frustum("gold", (x - 0.25 * sc, x + 0.25 * sc, y - 0.25 * sc, y + 0.25 * sc),
              (x - 0.55 * sc, x + 0.55 * sc, y - 0.55 * sc, y + 0.55 * sc), z + 0.55 * sc, z + 1.25 * sc)
    for s in S2:
        a.frame("goldS", S.octagon(-0.22 * sc, 0.22 * sc, -0.24 * sc, 0.24 * sc, 0.07 * sc), 0.08 * sc, -0.05 * sc, 0.05 * sc,
                axis="y", matrix=T((x + s * 0.62 * sc, y, z + 0.95 * sc)))


def lovibum(a, c, sc=1.0):
    """Мини-Ловибум (кристалл в когтях, D55) — экспонат коллекции."""
    x, y, z = c
    a.prism("steel", S.octagon(x - 0.32 * sc, x + 0.32 * sc, y - 0.32 * sc, y + 0.32 * sc, 0.1 * sc), z, z + 0.22 * sc)
    a.frustum("neonCrystal", (x - 0.24 * sc, x + 0.24 * sc, y - 0.24 * sc, y + 0.24 * sc), (x, x, y, y),
              z + 0.45 * sc, z + 0.9 * sc, bevel=0)
    a.frustum("crystalD", (x - 0.24 * sc, x + 0.24 * sc, y - 0.24 * sc, y + 0.24 * sc), (x, x, y, y),
              z + 0.45 * sc, z + 0.2 * sc, bevel=0)
    for ang in (45, 135, 225, 315):
        d = V((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
        p0 = V(c) + d * 0.28 * sc + V((0, 0, 0.2 * sc))
        key("gold")
        K.spike(a, p0, p0 + d * 0.12 * sc + V((0, 0, 0.6 * sc)), 0.13 * sc)


def critter(a, c, sc=1.0, dazed=False):
    """Маленькое существо-экспонат: рыжий снежный зверёк."""
    x, y, z = c
    key("critter")
    K.layered(a, [(-0.4 * sc, z), (-0.45 * sc, z + 0.5 * sc), (-0.2 * sc, z + 0.85 * sc), (0.3 * sc, z + 0.8 * sc),
                  (0.42 * sc, z + 0.35 * sc), (0.3 * sc, z)], [(0.32 * sc, 1, 1), (0.42 * sc, 0.85, 0.85)],
              (0, z + 0.4 * sc), xc=x, matrix=T((0, y, 0)))
    for s in S2:
        K.spike(a, (x + s * 0.22 * sc, y, z + 0.78 * sc), (x + s * 0.32 * sc, y + 0.05, z + 1.12 * sc), 0.16 * sc)
        if dazed:
            a.box("dark", x + s * 0.15 * sc - 0.05 * sc, x + s * 0.15 * sc + 0.05 * sc, y - 0.47 * sc, y - 0.42 * sc,
                  z + 0.5 * sc, z + 0.62 * sc, bevel=0)
        else:
            a.box("dark", x + s * 0.15 * sc - 0.06 * sc, x + s * 0.15 * sc + 0.06 * sc, y - 0.47 * sc, y - 0.42 * sc,
                  z + 0.48 * sc, z + 0.62 * sc, bevel=0)
    a.box("white", x - 0.22 * sc, x + 0.22 * sc, y - 0.46 * sc, y - 0.4 * sc, z + 0.12 * sc, z + 0.4 * sc, bevel=0)


def exhibits(a, inside=True, spill=None):
    """Экспонаты в глыбе (inside) или рассыпанные по земле (spill — матрица сцены поражения)."""
    if inside:
        base = a.transform
        trophy(a, (-0.72, 2.15, 5.55), 1.15)
        a.transform = base @ T((0.85, 2.1, 6.35)) @ R("X", 35) @ R("Y", 45)
        a.box("neonGem", -0.36, 0.36, -0.36, 0.36, -0.36, 0.36, bevel=0)
        a.transform = base
        lovibum(a, (0.75, 2.2, 3.55), 1.25)
        critter(a, (-0.6, 2.25, 2.25), 1.3)
    else:
        base = spill
        a.transform = base @ T((-3.4, -2.6, 0.0)) @ R("Y", 70) @ R("Z", 30)
        trophy(a, (0, 0, -0.55), 1.0)
        a.transform = base @ T((3.0, -3.4, 0.33)) @ R("X", 35) @ R("Y", 45)
        a.box("neonGem", -0.32, 0.32, -0.32, 0.32, -0.32, 0.32, bevel=0)
        a.transform = base @ T((2.2, -1.6, 0.0)) @ R("Z", 20) @ R("Y", -15)
        lovibum(a, (0, 0, 0), 1.15)
        a.transform = base @ T((-1.7, -3.9, 0.0)) @ R("Z", 15)
        critter(a, (0, 0, 0), 1.2, dazed=True)


def block_top(a, Mt):
    """Верхняя половина треснувшей глыбы в полёте: гранёная верхушка, золотые уголки, рваный низ, трещины."""
    a.transform, a.group = Mt, "BlockTop"
    x0, x1, y0, y1 = -1.95, 1.95, 1.02, 3.2
    z0, z1 = 3.7, 7.2
    a.extrude("iceBlock", S.octagon(x0, x1, y0, y1, 0.55), z0, z1, axis="z")
    a.frustum("iceBlock", (x0 + 0.2, x1 - 0.2, y0 + 0.15, y1 - 0.15), (-1.3, 0.9, 1.55, 2.85), z1, z1 + 0.85, bevel=0)
    a.frustum("iceE", (-1.3, 0.9, 1.55, 2.85), (-0.7, -0.1, 2.0, 2.4), z1 + 0.85, z1 + 1.45, bevel=0)
    for i in range(8):  # рваный низ — зубцы вниз
        x = x0 + 0.35 + i * (x1 - x0 - 0.7) / 7
        key("iceE" if i % 2 else "iceBlock")
        K.spike(a, (x, (y0 + y1) / 2, z0 + 0.05), (x - 0.1, (y0 + y1) / 2 + 0.2, z0 - 0.45 - 0.3 * (i % 3)), 0.62)
    a.frame("leather", S.octagon(x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, 0.6), 0.16, 6.3, 6.68, axis="z", bevel=0.008)
    for x in (x0, x1):
        sx = 1 if x > 0 else -1
        for y in (y0 + 0.3, y1 - 0.3):
            a.box("gold", x - sx * 0.05, x + sx * 0.12, y - 0.35, y + 0.35, z1 + 0.06, z1 - 0.55, bevel=0.015)
    cracks(a, y0 - 0.02, z0 + 0.3, z1 - 0.2)
    cracks(a, y1 + 0.02, z0 + 0.4, z1 - 0.4, flip=True)


def cracks(a, y, za, zb, flip=False):
    """Трещины на грани льда: ломаные тёмно-голубые полосы (видны и сквозь блик)."""
    k = -1 if flip else 1
    for x0, pts in ((-0.9, ((0, 0.0), (0.35, 0.3), (0.1, 0.62), (0.5, 1.0))), (0.7, ((0, 0.0), (-0.3, 0.4), (0.05, 0.7),
                                                                                   (-0.35, 1.0)))):
        for (u0, t0), (u1, t1) in zip(pts, pts[1:]):
            p0 = V((k * (x0 + u0), y, za + (zb - za) * t0))
            p1 = V((k * (x0 + u1), y, za + (zb - za) * t1))
            d = p1 - p0
            m = T((p0 + p1) / 2) @ R("Y", -math.degrees(math.atan2(d.x, d.z)))
            a.box("iceD", -0.05, 0.05, -0.03, 0.03, -d.length / 2 - 0.04, d.length / 2 + 0.04, bevel=0, matrix=m)


def shards(a, base):
    """Осколки глыбы вокруг сидящего йети."""
    chunks = [(-3.0, 1.2, 0.9, 30, 1.0), (2.9, 1.6, 0.8, -25, 0.9), (-2.2, 3.4, 0.7, 60, 0.8), (1.6, 3.8, 1.0, -40, 1.1),
              (0.2, 4.6, 0.6, 15, 0.7), (-3.9, -0.6, 0.5, 80, 0.6), (3.8, -0.9, 0.55, -70, 0.65)]
    for x, y, z, ang, sc in ((-1.6, 2.9, 4.6, 25, 0.55), (-2.4, 1.6, 5.3, -40, 0.42), (-0.8, 3.4, 3.6, 60, 0.38),
                             (1.0, 2.8, 4.9, -20, 0.36)):  # осколки в воздухе между спиной и слетающей верхушкой
        a.transform = base @ T((x, y, z)) @ R("Z", ang) @ R("X", ang)
        a.frustum("iceE" if sc < 0.4 else "iceBlock", (-0.5 * sc, 0.5 * sc, -0.4 * sc, 0.4 * sc), (0, 0, 0, 0), -0.4 * sc,
                  0.9 * sc, bevel=0)
    for x, y, h, ang, sc in chunks:
        a.transform = base @ T((x, y, 0)) @ R("Z", ang) @ R("Y", ang * 0.3)
        a.prism("iceBlock", S.octagon(-0.7 * sc, 0.6 * sc, -0.5 * sc, 0.55 * sc, 0.25 * sc), 0.0, h, bevel=0)
        a.frustum("iceE", (-0.6 * sc, 0.5 * sc, -0.42 * sc, 0.45 * sc), (-0.1, 0.05, -0.05, 0.1), h, h + 0.6 * sc, bevel=0)


def arm(a, M, s, fist=False):
    a.transform, a.group = M[("sh", s)], f"UpperArm{'L' if s > 0 else 'R'}"
    key("furS")
    K.taper(a, (0, 0, 0.55), (0, 0, -0.65), 1.75, 1.45, 1.6, 1.35, up=(0, -1, 0), cut=0.32)
    key("fur")
    K.chain(a, [(0, 0, 0.1), (0, 0.05, -1.05), (0, 0, -UPPER)], [1.25, 1.18, 1.0], up=(0, -1, 0), cut=0.3)
    tufts(a, [(s * 0.55, -0.1, 0.75), (s * 0.85, 0.15, 0.4), (s * 0.4, 0.45, 0.65)], 0.75,
          lambda p: (s * 0.6, 0.1, 1.0), down=-0.3)
    a.transform, a.group = M[("el", s)], f"ForeArm{'L' if s > 0 else 'R'}"
    key("fur")
    K.chain(a, [(0, 0, 0.15), (0, -0.1, -1.25), (0, 0, -FORE)], [1.1, 1.95, 1.15], [1.1, 1.75, 1.05], up=(0, -1, 0),
            cut=0.3)
    tufts(a, [(0, 0.45, 0.05), (s * 0.3, 0.4, -0.25)], 0.6, (0, 1, -0.2), down=0.2)  # локоть
    cuff = [(0.62 * math.cos(t), 0.55 * math.sin(t), -FORE + 0.35) for t in [i * math.pi / 3 for i in range(6)]]
    tufts(a, cuff, 0.55, lambda p: (p.x, p.y, -0.3), down=0.75)
    a.transform, a.group = M[("wr", s)], f"Hand{'L' if s > 0 else 'R'}"
    key("skin")
    K.taper(a, (0, 0, 0.1), (0, -0.05, -0.75), 1.15, 1.3, 0.8, 0.82, up=(0, -1, 0), cut=0.28)
    key("skinD")
    for i, dx in enumerate((-0.38, 0.0, 0.38)):
        if fist:
            pts = [(dx, -0.1, -0.7), (dx, -0.45, -0.85), (dx, -0.5, -0.45)]
        else:
            pts = [(dx, -0.05, -0.7), (dx, -0.3, -1.15), (dx, -0.62, -1.3)]
        key("skin")
        K.chain(a, pts, [0.36, 0.33, 0.28], up=(0, -1, 0), cut=0.3)
        key("ivory")
        tip = V(pts[-1])
        K.spike(a, tip + V((0, -0.08, 0)), tip + V((0, -0.32, -0.12 if not fist else 0.1)), 0.18)
    key("skin")
    th = -s * 0.62
    K.chain(a, [(th, -0.2, -0.25), (th * 1.05, -0.55, -0.45), (th * 0.8, -0.78, -0.55)], [0.34, 0.3, 0.26],
            up=(0, -1, 0), cut=0.3)


def leg(a, M, s):
    a.transform, a.group = M[("hip", s)], f"Thigh{'L' if s > 0 else 'R'}"
    key("fur")
    K.chain(a, [(0, 0, 0.35), (0, -0.05, -0.6), (0, 0, -THIGH)], [1.6, 1.7, 1.35], up=(0, -1, 0), cut=0.32)
    a.transform, a.group = M[("kn", s)], f"Shin{'L' if s > 0 else 'R'}"
    K.chain(a, [(0, 0, 0.2), (0, 0.05, -0.5), (0, 0, -SHIN)], [1.25, 1.3, 1.08], up=(0, -1, 0), cut=0.32)
    cuff = [(0.62 * math.cos(t), 0.6 * math.sin(t), -SHIN + 0.25) for t in [i * math.pi / 3.5 for i in range(7)]]
    tufts(a, cuff, 0.5, lambda p: (p.x, p.y, -0.2), down=0.8)
    a.transform, a.group = M[("an", s)], f"Foot{'L' if s > 0 else 'R'}"
    key("skin")
    sole = [(0.5, 0.0), (0.42, -0.42), (-1.2, -0.42), (-1.38, -0.18), (-1.05, 0.12), (-0.2, 0.3), (0.35, 0.25)]
    slab(a, sole, -0.62, 0.62)
    key("skinD")
    slab(a, [(0.45, -0.42), (-1.2, -0.42), (-1.2, -0.36), (0.45, -0.36)], -0.64, 0.64)
    key("ivory")
    for dx in (-0.36, 0.0, 0.36):
        K.spike(a, (dx, -1.25, -0.3), (dx, -1.6, -0.4), 0.2)


HEAD_SCALE = 1.32


def head(a, M, face, jaw):
    a.transform, a.group = M["head"] @ Matrix.Scale(HEAD_SCALE, 4), "Head"
    # меховой капюшон головы — слоёный купол
    dome = [(1.05, 0.2), (1.15, 1.4), (0.8, 2.25), (0.0, 2.55), (-0.8, 2.4), (-1.1, 1.95), (-1.12, 0.3),
            (-0.6, -0.15), (0.6, -0.15)]
    key("fur")
    K.layered(a, dome, [(1.05, 1.0, 1.0), (1.32, 0.88, 0.9)], (0.0, 1.1))
    # хохолок на макушке
    for p in ((0, 0.25, 2.45), (0.5, 0.5, 2.3), (-0.5, 0.5, 2.3), (0.0, 0.85, 2.15)):
        p = V(p)
        K.spike(a, p, p + V((p.x * 0.6, 0.5, 1.0 - abs(p.x) * 0.3)), 0.66)
    # грива вокруг лица: пряди по овалу, наружу и чуть вперёд — силуэт «йети в капюшоне»
    for i, t in enumerate(range(-140, 141, 28)):
        r = math.radians(t)
        p = V((1.22 * math.sin(r), -0.9, 1.05 + 1.02 * math.cos(r)))
        d = V((math.sin(r), -0.35, math.cos(r))).normalized()
        sz = 0.78 if i % 2 == 0 else 0.6
        K.spike(a, p, p + d * sz, sz * 0.75)
    # маска лица
    key("skin")
    mask = [(-0.9, 1.95), (-1.25, 1.86), (-1.33, 0.85), (-1.22, 0.45), (-0.9, 0.45)]
    for s in S2:
        half(a, mask, 1.0, s, -12, 1.0)
    # надбровья — тяжёлый козырёк, наклон по выражению
    brow = {"smug": (10, -16), "sleep": (-4, -4), "roar": (-24, -24), "dizzy": (16, 12)}[face]
    for s in S2:
        ang = brow[0] if s < 0 else brow[1]  # s < 0 — правый глаз персонажа (с моноклем), бровь выше
        lift = 0.12 if (face == "smug" and s < 0) else 0.0
        c = V((s * 0.55, -1.3, 1.78 + lift))
        key("skinD")
        slab(a, [(-0.98, 2.04 + lift), (-1.58, 1.94 + lift), (-1.52, 1.7 + lift), (-1.05, 1.72 + lift)], s * 0.04,
             s * 1.06, matrix=T(c) @ R("Y", s * ang) @ T(-c))
    # глаза: крупные, светятся
    for s in S2:
        ex = s * 0.52
        if face in ("smug", "roar"):
            key("neonEye")
            slab(a, [(-1.26, 1.66), (-1.36, 1.6), (-1.36, 1.24), (-1.26, 1.2)], ex - 0.31, ex + 0.31)
            key("pupil")
            px = ex + (0.0 if face == "roar" else -s * 0.06)
            slab(a, [(-1.36, 1.56), (-1.39, 1.54), (-1.39, 1.3), (-1.36, 1.28)], px - 0.09, px + 0.09)
            key("white")
            slab(a, [(-1.36, 1.6), (-1.385, 1.6), (-1.385, 1.54), (-1.36, 1.54)], ex + 0.12, ex + 0.22)
        elif face == "sleep":
            key("skinD")
            slab(a, [(-1.26, 1.6), (-1.35, 1.55), (-1.35, 1.36), (-1.26, 1.36)], ex - 0.32, ex + 0.32)
            key("dark")
            slab(a, [(-1.35, 1.42), (-1.38, 1.42), (-1.38, 1.35), (-1.35, 1.35)], ex - 0.28, ex + 0.28)
        else:  # dizzy — глаза-крестики
            key("neonEye")
            slab(a, [(-1.26, 1.66), (-1.36, 1.6), (-1.36, 1.24), (-1.26, 1.2)], ex - 0.31, ex + 0.31)
            for ang in (45, -45):
                a.box("dark", -0.05, 0.05, -0.02, 0.02, -0.26, 0.26, bevel=0,
                      matrix=T((ex, -1.39, 1.43)) @ R("Y", ang))
    # монокль на правом глазу персонажа (x < 0); при поражении слетел и висит на цепочке
    mc = V((-0.52, -1.46, 1.43 + (0.06 if face == "smug" else 0.0)))
    mm = T((-0.95, -1.5, 0.15)) @ R("X", 70) @ R("Z", 30) if face == "dizzy" else T(mc) @ R("X", 90)
    a.frame("gold", S.octagon(-0.42, 0.42, -0.42, 0.42, 0.13), 0.1, -0.05, 0.05, axis="z", matrix=mm)
    a.prism("lens", S.octagon(-0.33, 0.33, -0.33, 0.33, 0.1), -0.015, 0.015, axis="z", matrix=mm)
    if face != "dizzy":
        for i in range(4):  # цепочка к щеке
            p = mc + V((-0.36 - i * 0.06, 0.06 + i * 0.03, -0.42 - i * 0.26))
            a.box("goldS", p.x - 0.05, p.x + 0.05, p.y - 0.05, p.y + 0.05, p.z - 0.1, p.z + 0.1, bevel=0.01)
    # морда и нос
    key("skin")
    for s in S2:
        half(a, [(-1.2, 1.22), (-1.62, 1.12), (-1.7, 0.66), (-1.42, 0.52), (-1.15, 0.6)], 0.74, s, -10, 0.8)
    key("nose")  # нос — широкая «кнопка» с двумя ноздрями (не сплошная прорезь)
    slab(a, [(-1.6, 1.3), (-1.8, 1.2), (-1.84, 1.0), (-1.7, 0.9), (-1.6, 0.9)], -0.32, 0.32)
    for s in S2:
        a.box("dark", s * 0.16 - 0.08, s * 0.16 + 0.08, -1.88, -1.83, 0.96, 1.06, bevel=0)
    key("skinD")
    slab(a, [(-1.6, 0.66), (-1.72, 0.66), (-1.72, 0.58), (-1.6, 0.58)], -0.5, 0.5)  # верхняя губа
    # нижняя челюсть — неправильный прикус: выступает вперёд, нижние зубы поверх губы, два бивня вверх
    hinge = V((0, -0.6, 0.45))
    mj = T(hinge) @ R("X", jaw) @ T(-hinge)
    if jaw > 0:
        key("mouth")
        slab(a, [(-0.85, 0.62), (-1.58, 0.6), (-1.6, 0.05), (-0.85, 0.05)], -0.62, 0.62)
        key("tongue")
        slab(a, [(-0.9, 0.34), (-1.6, 0.36), (-1.62, 0.22), (-0.9, 0.2)], -0.36, 0.36, matrix=mj)
        if face == "dizzy":  # язык набок
            slab(a, [(-1.55, 0.36), (-1.95, 0.2), (-1.9, -0.15), (-1.6, 0.18)], 0.1, 0.42, matrix=mj)
        key("ivory")
        for s in S2:  # верхние клыки
            K.spike(a, (s * 0.38, -1.58, 0.62), (s * 0.38, -1.62, 0.32), 0.17)
    key("skin")
    jawp = [(-0.75, 0.6), (-1.86, 0.66), (-1.9, 0.2), (-1.5, -0.18), (-0.75, -0.12)]
    for s in S2:
        half(a, jawp, 0.68, s, -8, 0.25, extra=mj)
    if jaw == 0:  # линия рта между мордой и нижними зубами
        key("mouth")
        slab(a, [(-1.6, 0.6), (-1.74, 0.6), (-1.74, 0.53), (-1.6, 0.53)], -0.58, 0.58)
    key("ivory")
    for dx in (-0.42, -0.14, 0.14, 0.42):  # нижние зубы
        a.box("ivory", dx - 0.1, dx + 0.1, -1.86, -1.74, 0.62, 0.8, bevel=0.01, matrix=mj)
    a.transform = M["head"] @ Matrix.Scale(HEAD_SCALE, 4)
    for s in S2:  # бивни из углов челюсти — изогнуты вверх и наружу
        p0 = mj @ V((s * 0.62, -1.72, 0.5))
        p1 = mj @ V((s * 0.74, -1.84, 0.98))
        p2 = mj @ V((s * 0.92, -1.86, 1.38))
        K.chain(a, [p0, p1], [0.3, 0.24], up=(0, -1, 0), cut=0.3, overlap=0.2)
        K.spike(a, p1, p2, 0.24)
    if face == "sleep":  # морозный пузырь из носа
        b = V((0.5, -2.02, 0.92))
        a.prism("lens", S.octagon(b.x - 0.26, b.x + 0.26, b.y - 0.26, b.y + 0.26, 0.09), b.z - 0.26, b.z + 0.26,
                bevel=0.02)


def zzz(a, M):
    """Сон: ледяные «Z» над головой (плоские фигуры, не текст)."""
    zp = [(0, 0), (0.7, 0), (0.12, -0.62), (0.72, -0.62), (0.72, -0.78), (-0.05, -0.78), (0.52, -0.16), (0, -0.16)]
    for i, (dx, dz, sc) in enumerate(((0.8, 0.9, 1.0), (1.55, 1.8, 0.8), (2.2, 2.55, 0.62))):
        a.transform, a.group = M["head"] @ T((dx, -0.6, 2.4 + dz)) @ R("Y", -12 * i) @ Matrix.Scale(sc, 4), "Fx"
        a.extrude("iceE" if i % 2 else "lens", zp, -0.07, 0.07, axis="y")


def yeti(pose="stand"):
    a = new_art("Yeti" + pose.capitalize())  # без «_»: ключ материала — после последнего «_»
    M = skeleton(pose)
    torso(a, M["torso"])
    harness(a, M["torso"])
    for s in S2:
        arm(a, M, s, fist=(pose == "combat"))
        leg(a, M, s)
    head(a, M, POSES[pose]["face"], POSES[pose]["jaw"])
    if pose == "defeat":  # глыба треснула: остаток на спине, верхняя половина слетает, осколки и экспонаты на земле
        ice_block(a, M["torso"], broken=True, lean=POSES[pose]["torso"])
        block_top(a, T((3.7, 1.2, 2.5)) @ R("Z", -30) @ R("Y", 52) @ T((0, -2.1, -5.45)))
        base = T((0, 0, 0))
        shards(a, base)
        exhibits(a, inside=False, spill=base)
    elif pose == "sleep":  # спит сидя, привалившись спиной к снятой глыбе
        ice_block(a, T((0, 0.75, -1.6)) @ R("X", -6))
    else:
        ice_block(a, M["torso"], lean=POSES[pose]["torso"])
    if pose == "sleep":
        zzz(a, M)
    a.transform, a.group = None, None
    return a
