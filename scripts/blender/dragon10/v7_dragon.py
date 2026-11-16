"""Король-дракон v7 — королевское оформление утверждённой формы v6 (стиль D39: цвета и квадраты-контуры art_style).

Анатомия — геометрия v6 без изменений: те же профили, звенья и точки. Добавлены только цвета частей и разметка
подвижных частей a.group для будущего рига. Метки a.tags (имя → номера деталей) нужны для проверки пересечений.

Королевские атрибуты — отдельные детали:
- корона-диадема поперёк лба перед основаниями рогов. Сидит на куполе черепа и бровях, ступенчатые зубцы,
  большой центральный бирюзовый кристалл, малые камни. Ниже глаз не опускается, рогов не касается;
- броня:
  - нагрудник со ступенью и королевским знаком (корона + кристалл);
  - наплечники над плечевым суставом;
  - наручи на передних лапах;
  - кольца и пластины на задних;
  - сегменты вдоль хребта между шипами;
  - кольца у основания хвоста;
- короткая церемониальная мантия:
  - горностаевый воротник у основания шеи;
  - ремни к наплечникам;
  - по бокам — золотая планка от лопатки и три полосы-полотнища, отдельные части для анимации;
  - полотнища висят ниже перепонки, между передними и задними лапами, со ступенчатым подолом и золотой каймой;
- скипетр парит рядом с драконом над магическим кругом: золотое древко, когти-держатели, большой кристалл.

Палитра — из ТЗ владельца:
- чешуя — королевский фиолетовый, живот и горло — тёмная слива;
- броня и корона — золото;
- перепонки — пурпурные;
- кристаллы — бирюзовые;
- глаза — светящиеся янтарные;
- когти и рога — слоновая кость.
Мантия — алая с горностаем: предложение, в ТЗ цвета мантии нет.
"""

import math
from contextlib import contextmanager

import bmesh

import v4_kit as K
from v4_kit import Matrix, V

S2 = (1, -1)
PALETTE = {  # ключ: (цвет, кольца D39 на крупных поверхностях)
    "scale": ("5E36C4", True), "scaleD": ("43258F", False), "belly": ("7E2C72", True), "wing": ("B03CB0", True),
    "bone": ("43258F", False), "ivory": ("F3E9D2", False), "gold": ("F5B21C", True), "goldS": ("F5B21C", False),
    "goldD": ("C27E0E", False), "goldL": ("FFD966", False), "neonCrystal": ("2FE6D8", False),
    "crystalD": ("1596A8", False), "neonEye": ("FFB020", False), "pupil": ("2A1036", False), "mouth": ("3A1440", False),
    "mantle": ("C42136", True), "mantleD": ("8E1426", False), "ermine": ("F7F5EF", False), "spot": ("1E1A24", False),
}


def key(k):
    K.KEY = k


def new_art(name, palette=None):
    a = K.S.Art(name, ring_z0=3.0)
    a.ring = dict(K.S.RING, core=0.55)  # профиль контура «полка», как у концептов боссов 5–10
    for k, (code, rings) in (palette or PALETTE).items():
        a.paint(k, code, rings=rings)
    a.tags = {}
    return a


@contextmanager
def tag(a, name):
    """Метка группы деталей (для проверки пересечений)."""
    i0 = len(a.parts)
    yield
    a.tags.setdefault(name, []).extend(range(i0, len(a.parts)))


def gem(a, c, w, h, top="neonCrystal", bottom="crystalD"):
    """Огранённый кристалл: светящаяся верхняя пирамида и тёмная нижняя."""
    x, y, z = c
    a.frustum(top, (x - w, x + w, y - w, y + w), (x, x, y, y), z, z + h, bevel=0)
    a.frustum(bottom, (x - w, x + w, y - w, y + w), (x, x, y, y), z, z - h * 0.8, bevel=0)


def gem_on(a, c, normal, size, top="neonCrystal", bottom="crystalD", turn=0.0):
    """Кристалл, вставленный в поверхность: ось — по нормали normal, низ утоплен; turn — поворот ромбом."""
    c, n = V(c), V(normal).normalized()
    m = Matrix.Translation(c) @ n.to_track_quat("Z", "Y").to_matrix().to_4x4() @ \
        Matrix.Rotation(math.radians(turn), 4, "Z")
    a.frustum(top, (-size, size, -size, size), (0, 0, 0, 0), 0.0, size * 1.3, bevel=0, matrix=m)
    a.frustum(bottom, (-size, size, -size, size), (0, 0, 0, 0), 0.0, -size * 0.6, bevel=0, matrix=m)


EMBLEM = [(-0.4, 0.0), (0.4, 0.0), (0.4, 0.22), (0.5, 0.52), (0.22, 0.32), (0.0, 0.62), (-0.22, 0.32), (-0.5, 0.52),
          (-0.4, 0.22)]  # королевский знак: корона из трёх зубцов (u — поперёк, v — вверх)


# ── анатомия v6 с цветами ────────────────────────────────────────────────────────────────────────────────────
def half(a, prof, w, s, ang, pz, x0=-0.12, extra=None):
    c = V((0, 0, pz))
    m = Matrix.Translation(c) @ Matrix.Rotation(math.radians(ang * s), 4, "Y") @ Matrix.Translation(-c)
    K.slab(a, prof, s * x0, s * w, matrix=m if extra is None else extra @ m)


def head(a, origin, L=3.8, H=1.85, W=1.58, pitch=10.0, yaw=-7.0, jaw_open=17.0, royal=True):
    a.group = "Head"
    M = Matrix.Translation(origin) @ Matrix.Rotation(math.radians(yaw), 4, "Z") @ \
        Matrix.Rotation(math.radians(-pitch), 4, "X")
    a.transform = M
    dome = [(0.15, 0.6 * H), (0.0, 1.0 * H), (-0.3 * L, 1.08 * H), (-0.46 * L, 0.98 * H), (-0.5 * L, 0.7 * H),
            (0.1, 0.55 * H)]
    skull = [(0.22, -0.05 * H), (0.28, 0.6 * H), (0.05, 0.92 * H), (-0.32 * L, 0.98 * H), (-0.52 * L, 0.82 * H),
             (-0.56 * L, 0.06 * H), (-0.12 * L, -0.18 * H)]
    cheek = [(0.08, 0.12 * H), (0.1, 0.52 * H), (-0.2 * L, 0.58 * H), (-0.44 * L, 0.54 * H), (-0.52 * L, 0.28 * H),
             (-0.34 * L, 0.04 * H), (-0.1 * L, 0.0)]
    sn1 = [(-0.5 * L, 0.78 * H), (-0.72 * L, 0.62 * H), (-0.72 * L, 0.06 * H), (-0.5 * L, 0.06 * H)]
    sn2 = [(-0.7 * L, 0.64 * H), (-0.9 * L, 0.5 * H), (-0.9 * L, 0.08 * H), (-0.7 * L, 0.08 * H)]
    tip = [(-0.88 * L, 0.52 * H), (-1.03 * L, 0.46 * H), (-1.08 * L, 0.28 * H), (-1.04 * L, 0.1 * H), (-0.88 * L, 0.1 * H)]
    lip = [(-0.25 * L, 0.12 * H), (-1.0 * L, 0.12 * H), (-1.02 * L, -0.02 * H), (-0.25 * L, -0.08 * H)]
    with tag(a, "skull"):
        for s in S2:
            key("scale")
            half(a, dome, 0.5 * W, s, -12, 0.6 * H)
            half(a, skull, 0.72 * W, s, -7, 0.35 * H)
            half(a, cheek, W, s, -14, 0.3 * H)
            half(a, sn1, 0.56 * W, s, -9, 0.06 * H)
            half(a, sn2, 0.45 * W, s, -9, 0.08 * H)
            half(a, tip, 0.34 * W, s, -9, 0.1 * H)
            key("belly")
            half(a, lip, 0.5 * W, s, -9, 0.0)
        key("scaleD")
        K.slab(a, [(-0.44 * L, 0.92 * H), (-0.97 * L, 0.6 * H), (-0.97 * L, 0.5 * H), (-0.44 * L, 0.76 * H)],
               -0.16 * W, 0.16 * W)
        key("mouth")
        K.slab(a, [(-0.2 * L, 0.08 * H), (-0.95 * L, 0.08 * H), (-0.95 * L, 0.0), (-0.2 * L, 0.0)], -0.34 * W, 0.34 * W)
    for s in S2:
        with tag(a, "brows"):
            key("scaleD")
            c = V((s * 0.62 * W, -0.4 * L, 0.86 * H))
            mb = Matrix.Translation(c) @ Matrix.Rotation(math.radians(-s * 17), 4, "Y") @ Matrix.Translation(-c)
            K.slab(a, [(-0.22 * L, 1.0 * H), (-0.55 * L - 0.32 * H, 0.9 * H), (-0.55 * L - 0.26 * H, 0.72 * H),
                       (-0.27 * L, 0.78 * H)], s * 0.2 * W, s * 1.02 * W, matrix=mb)
        with tag(a, "eyes"):
            key("neonEye")
            ce = V((s * 0.78 * W, -0.43 * L, 0.65 * H))
            me = Matrix.Translation(ce) @ Matrix.Rotation(math.radians(s * 24), 4, "Z") @ Matrix.Translation(-ce)
            K.slab(a, [(-0.34 * L, 0.58 * H), (-0.48 * L, 0.76 * H), (-0.52 * L, 0.62 * H), (-0.38 * L, 0.55 * H)],
                   s * 0.7 * W, s * 0.86 * W, matrix=me)
            if royal:  # вертикальный зрачок на светящемся глазу — взгляд читается
                key("pupil")
                K.slab(a, [(-0.43 * L, 0.735 * H), (-0.448 * L, 0.65 * H), (-0.43 * L, 0.575 * H),
                           (-0.412 * L, 0.65 * H)], s * 0.84 * W, s * 0.9 * W, matrix=me)
        with tag(a, "skull"):
            key("scaleD")
            cn = V((s * 0.2 * W, -1.0 * L, 0.45 * H))
            mn = Matrix.Translation(cn) @ Matrix.Rotation(math.radians(s * 18), 4, "Z") @ Matrix.Translation(-cn)
            K.slab(a, [(-0.94 * L, 0.44 * H), (-1.05 * L, 0.56 * H), (-1.09 * L, 0.38 * H), (-0.98 * L, 0.3 * H)],
                   s * 0.08 * W, s * 0.32 * W, matrix=mn)
            key("ivory")
            with tag(a, "browspikes"):
                K.spike(a, (s * 0.95 * W, -0.52 * L, 1.0 * H), (s * 1.25 * W, -0.36 * L, 1.36 * H), 0.24 * H)
            K.spike(a, (s * 1.02 * W, -0.14 * L, 0.3 * H), (s * (W + 0.85), 0.14 * L, 0.45 * H), 0.32 * H)
            for y, ln, w, x in ((-0.93, 0.46, 0.2, 0.4), (-0.72, 0.28, 0.14, 0.44)):
                K.spike(a, (s * x * W, y * L, 0.02 * H), (s * (x + 0.01) * W, y * L - 0.04, -ln * H), w * H)
        with tag(a, "horns"):
            key("ivory")
            K.chain(a, [(s * 0.56, -1.0, 1.72), (s * 0.95, -0.35, 2.2), (s * 1.42, 0.55, 2.45), (s * 1.82, 1.55, 2.35),
                        (s * 2.05, 2.45, 2.0), (s * 2.2, 3.05, 2.25)], [0.64, 0.53, 0.42, 0.31, 0.2, 0.1])
            K.spike(a, (s * 2.2, 3.05, 2.25), (s * 2.32, 3.3, 2.8), 0.1)
            K.chain(a, [(s * 1.0, 0.0, 0.95), (s * 1.5, 0.7, 1.12), (s * 1.78, 1.3, 0.95)], [0.32, 0.22, 0.08])
    if royal:
        with tag(a, "crown"):
            crown(a)
    a.group = "Jaw"
    hinge = V((0, -0.12 * L, 0.0))
    J = Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(jaw_open), 4, "X") @ Matrix.Translation(-hinge)
    a.transform = M @ J
    jaw = [(-0.12 * L, -0.1 * H), (-0.96 * L, -0.1 * H), (-1.0 * L, -0.2 * H), (-0.88 * L, -0.44 * H),
           (-0.42 * L, -0.58 * H), (-0.1 * L, -0.44 * H)]
    mus = [(-0.02 * L, -0.06 * H), (-0.42 * L, -0.06 * H), (-0.38 * L, -0.52 * H), (-0.08 * L, -0.46 * H)]
    chin = [(-0.86 * L, -0.18 * H), (-1.02 * L, -0.18 * H), (-1.0 * L, -0.42 * H), (-0.88 * L, -0.48 * H)]
    rim = [(-0.2 * L, 0.02 * H), (-0.98 * L, 0.02 * H), (-0.98 * L, -0.1 * H), (-0.2 * L, -0.1 * H)]
    with tag(a, "jaw"):
        for s in S2:
            key("belly")
            half(a, jaw, 0.5 * W, s, 13, -0.1 * H)
            key("scale")
            half(a, mus, 0.72 * W, s, 15, -0.06 * H)
            key("belly")
            half(a, chin, 0.36 * W, s, 13, -0.18 * H)
            key("scale")
            half(a, rim, 0.5 * W, s, 13, -0.1 * H, x0=0.34 * W)
            key("ivory")
            for y, ln, w, x in ((-0.89, 0.34, 0.16, 0.36), (-0.66, 0.2, 0.11, 0.38)):
                K.spike(a, (s * x * W, y * L, 0.0), (s * (x - 0.01) * W, y * L + 0.03, ln * H), w * H)
    a.transform = None


# ── корона ───────────────────────────────────────────────────────────────────────────────────────────────────
CROWN_TINES = ((0.5, 0.17, 2.98), (0.98, 0.15, 2.72))  # (x по брови, полуширина, верх) — зубцы над каждой бровью


def brow_frame(s, L=3.8, H=1.85, W=1.58):
    """Та же матрица, что у брови стороны s в head(): обод короны повторяет её наклон («V» бровей)."""
    c = V((s * 0.62 * W, -0.4 * L, 0.86 * H))
    return Matrix.Translation(c) @ Matrix.Rotation(math.radians(-s * 17), 4, "Y") @ Matrix.Translation(-c)


def tine(a, p, w, d, top):
    """Ступенчатый зубец короны: брусок до полки, острие выше; p — середина основания (утоплено в обод)."""
    x, y, z = p
    zs = z + (top - z) * 0.48
    a.box("goldS", x - w, x + w, y - d, y + d, z - 0.12, zs)
    a.box("goldD", x - w - 0.03, x + w + 0.03, y - d - 0.03, y + d + 0.03, zs - 0.07, zs + 0.03)
    a.frustum("goldS", (x - w * 0.7, x + w * 0.7, y - d * 0.7, y + d * 0.7), (x, x, y, y), zs, top, bevel=0)


def crown(a):
    """Корона в координатах головы — под голову дракона, а не обруч.

    Обод — две половины по верху бровей: повторяет их «V» и продолжает злой изгиб бровей вверх. Зубцы
    вертикальные, ступенчатые: прямоугольное основание, полка, острие. Средний зубец самый высокий, перед ним —
    большой бирюзовый кристалл в золотой оправе, по ободу — малые камни. Корона целиком перед основаниями рогов
    (рога от y −1.0) и выше глаз (глаза ниже z 1.41)."""
    y0, y1 = -1.95, -1.36
    for s in S2:
        mb = brow_frame(s)
        key("goldS")
        K.slab(a, [(y1, 1.74), (y1, 2.12), (y1 - 0.14, 2.26), (y0 + 0.13, 2.26), (y0, 2.12), (y0, 1.72)],
               s * 0.18, s * 1.2, matrix=mb)
        key("goldD")  # нижняя ступень обода спереди
        K.slab(a, [(y0 + 0.02, 1.7), (y0 + 0.02, 1.96), (y0 - 0.1, 1.93), (y0 - 0.1, 1.72)], s * 0.24, s * 1.14,
               matrix=mb)
        for xb, w, top in CROWN_TINES:
            tine(a, mb @ V((s * xb, (y0 + y1) / 2, 2.12)), w, 0.2, top)
        gem_on(a, mb @ V((s * 0.74, y0 - 0.1, 1.84)), mb.to_3x3() @ V((0, -1, 0.15)), 0.085)
    a.box("goldS", -0.36, 0.36, y0 - 0.02, y1, 1.86, 2.3)  # средняя часть над переносицей и самый высокий зубец
    tine(a, V((0.0, (y0 + y1) / 2, 2.2)), 0.24, 0.24, 3.2)
    a.box("goldD", -0.3, 0.3, y0 - 0.14, y0, 2.1, 2.82)  # оправа кристалла
    gem_on(a, (0.0, y0 - 0.12, 2.46), (0, -1, 0.25), 0.27, turn=45)


# ── броня ────────────────────────────────────────────────────────────────────────────────────────────────────
SHIELD = [(-1.05, 0.5), (1.05, 0.5), (1.02, -0.35), (0.6, -1.0), (0.0, -1.42), (-0.6, -1.0), (-1.02, -0.35)]
SPINE_PLATES = [(-0.85, 7.18), (0.35, 6.55), (1.6, 6.05), (2.7, 5.55)]  # (y, высота хребта) между спинными шипами


def inset(pts, k, c=(0.0, -0.3)):
    """Многоугольник, уменьшенный к точке c (ступень щита)."""
    return [(c[0] + (u - c[0]) * k, c[1] + (v - c[1]) * k) for u, v in pts]


def torso_armor(a):
    a.group = "Torso"
    with tag(a, "chest"):  # щит по наклону груди: низ уходит назад к животу, верх под горлом
        mc = Matrix.Translation((0.0, -3.78, 5.2)) @ Matrix.Rotation(math.radians(20), 4, "X")
        a.extrude("goldD", SHIELD, -0.04, 0.32, axis="y", matrix=mc)
        a.extrude("gold", inset(SHIELD, 0.86), -0.17, 0.0, axis="y", matrix=mc)
        a.extrude("gold", inset(SHIELD, 0.5, (0.0, -0.15)), -0.3, -0.1, axis="y", matrix=mc)
        a.extrude("goldL", [(u * 0.7, -0.05 + v * 0.7) for u, v in EMBLEM], -0.36, -0.26, axis="y", matrix=mc)
        gem_on(a, mc @ V((0.0, -0.3, -0.58)), mc.to_3x3() @ V((0, -1, 0)), 0.17)
    for s in S2:  # наплечники над плечевым суставом, ступенью, тёмный кант снизу, камень
        with tag(a, "pauldron" + ("L" if s > 0 else "R")):
            key("gold")
            K.slab(a, [(-3.0, 5.4), (-3.1, 6.15), (-2.55, 6.7), (-1.6, 6.55), (-1.45, 5.65), (-1.95, 5.35)],
                   s * 2.74, s * 2.98)
            K.slab(a, [(-2.75, 5.6), (-2.85, 6.1), (-2.45, 6.42), (-1.85, 6.32), (-1.75, 5.75), (-2.05, 5.55)],
                   s * 2.98, s * 3.1)
            key("goldD")
            K.slab(a, [(-3.04, 5.3), (-1.95, 5.25), (-1.4, 5.55), (-1.4, 5.7), (-1.95, 5.42), (-3.04, 5.47)],
                   s * 2.72, s * 3.02)
            gem_on(a, (s * 3.1, -2.3, 5.95), (s, 0, 0.1), 0.13)
    with tag(a, "spineplates"):
        for yc, z in SPINE_PLATES:
            key("gold")
            K.slab(a, [(yc - 0.3, z - 0.1), (yc - 0.22, z + 0.12), (yc + 0.22, z + 0.08), (yc + 0.3, z - 0.14)],
                   -0.72, 0.72)
            key("goldD")
            K.slab(a, [(yc - 0.32, z - 0.18), (yc - 0.3, z - 0.06), (yc + 0.3, z - 0.1), (yc + 0.32, z - 0.22)],
                   -0.78, 0.78)


def foreleg_armor(a, s, el, wr):
    a.group = "ForeLeg" + ("L" if s > 0 else "R")
    with tag(a, "bracer" + ("L" if s > 0 else "R")):
        key("gold")
        K.taper(a, el.lerp(wr, 0.32), el.lerp(wr, 0.78), 1.5, 1.32, 1.58, 1.34, up=(0, -1, 0))
        key("goldD")
        K.taper(a, el.lerp(wr, 0.28), el.lerp(wr, 0.34), 1.56, 1.52, 1.64, 1.6, up=(0, -1, 0))
        K.taper(a, el.lerp(wr, 0.76), el.lerp(wr, 0.82), 1.38, 1.34, 1.4, 1.36, up=(0, -1, 0))
        f = (wr - el).normalized()
        u = (V((0, -1, 0)) - f * f.dot(V((0, -1, 0)))).normalized()
        gem_on(a, el.lerp(wr, 0.55) + u * 0.7, u, 0.12)


def hindleg_armor(a, s, hock, ankle):
    a.group = "HindLeg" + ("L" if s > 0 else "R")
    with tag(a, "greave" + ("L" if s > 0 else "R")):
        key("gold")
        K.taper(a, hock.lerp(ankle, 0.3), hock.lerp(ankle, 0.66), 1.16, 1.1, up=(0, -1, 0))
        K.slab(a, [(1.8, 3.7), (2.3, 4.3), (2.8, 3.7), (2.3, 3.1)], s * 2.84, s * 2.98)  # ромб на бедре
        gem_on(a, (s * 2.98, 2.3, 3.7), (s, 0, 0), 0.11)


def tail_armor(a, tail, ws):
    a.group = "Tail"
    with tag(a, "tailarmor"):
        for i, t in ((0, 0.58), (1, 0.4)):
            p0, p1 = V(tail[i]), V(tail[i + 1])
            w = ws[i] + (ws[i + 1] - ws[i]) * t + 0.16
            key("gold")
            K.taper(a, p0.lerp(p1, t - 0.1), p0.lerp(p1, t + 0.1), w, w * 0.97)
            key("goldD")
            K.taper(a, p0.lerp(p1, t + 0.1), p0.lerp(p1, t + 0.14), w * 0.98, w * 0.96)
        c = V(tail[0]).lerp(V(tail[1]), 0.58)
        gem_on(a, c + V((0, 0, (ws[0] + (ws[1] - ws[0]) * 0.58) / 2 + 0.08)), (0, 0, 1), 0.15)


# ── мантия ───────────────────────────────────────────────────────────────────────────────────────────────────
COLLAR = dict(c=(0.0, -3.92, 7.72), rx=1.27, ry=1.27, arc=118, n=9, drop=0.14)
STRIPS = ((-1.05, -0.61, 2.3, 0.0), (-0.56, -0.12, 2.55, 0.07), (-0.07, 0.35, 2.8, 0.0))  # y0, y1, подол, сдвиг
YOKE = dict(y0=-1.15, y1=0.42, z0=4.4, z1=4.72, x0=1.98, x1=2.32)  # ниже угла перепонки (z 4.89)
FLARE = 0.5  # подол отходит от бока: ткань висит на планке, а не приклеена


def sheet(a, k, quad, thick, inward):
    """Пластина ткани по четырём точкам наружной поверхности; толщина — внутрь, к точке inward."""
    p = [V(q) for q in quad]
    n = (p[1] - p[0]).cross(p[3] - p[0]).normalized()
    if n.dot(sum(p, V()) / 4 - V(inward)) < 0:
        n = -n
    bm = bmesh.new()
    outer = [bm.verts.new(q) for q in p]
    inner = [bm.verts.new(q - n * thick) for q in p]
    bm.faces.new(outer)
    bm.faces.new(list(reversed(inner)))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((outer[i], outer[j], inner[j], inner[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    a._add(bm, k, None, None)


def collar(a):
    """Горностаевый воротник подковой вокруг основания шеи (открыт сзади — там шипы и корни крыльев)."""
    cx, cy, cz = COLLAR["c"]
    rx, ry, arc, n, drop = COLLAR["rx"], COLLAR["ry"], math.radians(COLLAR["arc"]), COLLAR["n"], COLLAR["drop"]

    def at(t, grow=0.0, dz=0.0):
        return V((cx + (rx + grow) * math.sin(t), cy - (ry + grow) * math.cos(t), cz - drop * math.cos(t) + dz))

    ts = [-arc + 2 * arc * i / n for i in range(n + 1)]
    for t0, t1 in zip(ts, ts[1:]):
        key("goldS")
        K.taper(a, at(t0, 0.06, -0.3), at(t1, 0.06, -0.3), 0.5, 0.5, 0.2, 0.2, up=(0, 0, 1), ext0=0.08, ext1=0.08)
        key("ermine")
        K.taper(a, at(t0), at(t1), 0.66, 0.66, 0.46, 0.46, up=(0, 0, 1), ext0=0.1, ext1=0.1)
        m = at((t0 + t1) / 2)
        out = V((m.x - cx, m.y - cy, 0)).normalized()
        key("spot")
        K.spike(a, m + out * 0.2 + V((0, 0, 0.04)), m + out * 0.43 + V((0, 0, -0.06)), 0.13)
    for s in S2:
        t = s * math.radians(38)
        gem_on(a, at(t, 0.33, 0.0), V((math.sin(t), -math.cos(t), 0.25)), 0.15)


SHOULDER = [(-3.42, 5.68), (-3.46, 6.45), (-2.95, 7.02), (-1.95, 6.95), (-1.32, 6.4), (-1.27, 5.68)]  # (y, z)


def drape(a, s):
    """Плечевая часть мантии буквой «Г»: верхнее полотно от конца воротника через плечо и боковое — по лопатке
    до плечевого сустава (низ выше плеча лапы). Наплечник прижимает её снаружи. Передний край — горностай
    (продолжение воротника), задний и нижний — золотая кайма."""
    x0, x1 = s * 2.6, s * 2.72
    q = [V((s * 1.0, -3.66, 7.58)), V((s * 1.2, -2.86, 7.42)), V((x1 - s * 0.04, -2.2, 6.98)),
         V((x1 - s * 0.04, -3.36, 6.82))]
    key("mantle")
    sheet(a, "mantle", q, 0.1, (s * 1.5, -2.9, 5.4))
    K.slab(a, SHOULDER, x0, x1)
    key("ermine")  # передний край — горностай, продолжение воротника, вниз до плеча
    ermine = [q[0] + V((0, -0.04, 0.03)), q[3] + V((s * 0.04, -0.06, 0.05)), V((x1 + s * 0.02, -3.46, 5.62))]
    K.chain(a, ermine, [0.27, 0.27, 0.27], [0.2, 0.2, 0.2], up=(0, -1, 0.3), overlap=0.3)
    key("spot")  # хвостики горностая, как на воротнике
    for p, out in ((ermine[0].lerp(ermine[1], 0.5), V((0, -0.3, 1))), (ermine[1].lerp(ermine[2], 0.45), V((s, -1, 0)))):
        out = out.normalized()
        K.spike(a, p + out * 0.04, p + out * 0.2 + V((0, 0, -0.06)), 0.11)
    key("goldS")  # задний край и низ — золотая кайма
    K.taper(a, q[1] + V((0, 0, 0.02)), q[2] + V((0, 0, 0.02)), 0.14, 0.14, 0.14, 0.14, up=(0, 0, 1))
    K.slab(a, [(-3.4, 5.6), (-1.25, 5.6), (-1.25, 5.74), (-3.4, 5.74)], x0 - s * 0.02, x1 + s * 0.04)
    # шнур от плечевой части к планке бокового полотнища: полотнища подвешены к плечевому поясу
    K.chain(a, [V((s * 2.68, -1.38, 5.62)), V((s * 2.48, -1.24, 5.12)), V((s * 2.3, -1.1, 4.7))], [0.13, 0.12, 0.12],
            up=(0, 0, 1))


def strip_pts(s, x_top, zt, zh, thick, fl):
    return [(s * x_top, zt), (s * (x_top + thick), zt), (s * (x_top + thick + fl), zh), (s * (x_top + fl), zh)]


def mantle_side(a, s):
    """Плечевая часть, золотая планка от лопатки назад и три полосы-полотнища (отдельные части для анимации)."""
    side = "L" if s > 0 else "R"
    a.group = "Torso"
    with tag(a, "drape" + side):
        drape(a, s)
    y = YOKE
    with tag(a, "yoke" + side):
        key("gold")
        a.extrude("gold", [(s * y["x0"], y["z0"]), (s * y["x1"], y["z0"]), (s * (y["x1"] + 0.04), y["z1"]),
                           (s * y["x0"], y["z1"] + 0.06)], y["y0"], y["y1"], axis="y")
        key("goldD")
        a.extrude("goldD", [(s * (y["x1"] - 0.02), y["z0"] + 0.06), (s * (y["x1"] + 0.06), y["z0"] + 0.06),
                            (s * (y["x1"] + 0.08), y["z1"] - 0.06), (s * (y["x1"] - 0.02), y["z1"] - 0.06)],
                  y["y0"] + 0.12, y["y1"] - 0.12, axis="y")
        gem_on(a, (s * (y["x1"] + 0.07), -0.34, (y["z0"] + y["z1"]) / 2), (s, 0, 0), 0.12)
    for k, (y0, y1, zh, dx) in enumerate(STRIPS):
        a.group = f"Mantle{side}{k + 1}"
        with tag(a, "mantle" + side):
            zt = YOKE["z0"] + 0.05
            x_top = 1.98 + dx
            fl = FLARE
            key("mantle")
            a.extrude("mantle", strip_pts(s, x_top, zt, zh + 0.22, 0.14, fl * (zt - zh - 0.22) / (zt - zh)), y0, y1,
                      axis="y")
            xh = x_top + fl * (zt - zh - 0.26) / (zt - zh)
            key("gold")  # кайма подола
            a.extrude("gold", [(s * (xh - 0.03), zh + 0.26), (s * (xh + 0.19), zh + 0.26),
                               (s * (x_top + fl + 0.19), zh), (s * (x_top + fl - 0.03), zh)], y0 - 0.02, y1 + 0.02,
                      axis="y")
            if k == 1:  # знак-корона на средней полосе, по наклону ткани
                zc = 3.55
                xo = x_top + 0.14 + fl * (zt - zc) / (zt - zh)
                ang = math.atan2(fl, zt - zh)
                m = Matrix.Translation((s * xo, (y0 + y1) / 2, zc)) @ Matrix.Rotation(s * ang, 4, "Y")
                a.extrude("goldL", [(v * 0.5, u * 0.5) for u, v in EMBLEM], *sorted((-s * 0.02, s * 0.05)), axis="x",
                          matrix=m)


# ── скипетр ──────────────────────────────────────────────────────────────────────────────────────────────────
SCEPTER_AT = (-5.0, -4.6)  # справа-спереди от дракона (слева на виде спереди), куда он смотрит


def scepter(a, base=None, z0=1.0, circle=True):
    """Парящий скипетр: древко со ступенчатыми кольцами, когти-держатели, большой кристалл; круг и осколки."""
    a.group = "Scepter"
    x, y = base if base is not None else SCEPTER_AT
    key("goldS")
    K.taper(a, (x, y, z0 + 0.35), (x, y, z0 + 4.2), 0.26, 0.22, up=(0, -1, 0), cut=0.2)
    a.frustum("goldS", (x - 0.17, x + 0.17, y - 0.17, y + 0.17), (x, x, y, y), z0 + 0.38, z0 - 0.3, bevel=0)
    key("goldD")
    for zz in (z0 + 0.95, z0 + 1.85, z0 + 2.75):
        K.taper(a, (x, y, zz), (x, y, zz + 0.16), 0.38, 0.38, up=(0, -1, 0))
    key("goldS")
    zc = z0 + 4.2
    K.taper(a, (x, y, zc - 0.05), (x, y, zc + 0.2), 0.46, 0.6, up=(0, -1, 0))
    K.taper(a, (x, y, zc + 0.2), (x, y, zc + 0.38), 0.66, 0.5, up=(0, -1, 0))
    for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):  # когти держат кристалл
        p0 = V((x + dx * 0.2, y + dy * 0.2, zc + 0.3))
        p1 = V((x + dx * 0.44, y + dy * 0.44, zc + 0.9))
        p2 = V((x + dx * 0.18, y + dy * 0.18, zc + 1.5))
        K.chain(a, [p0, p1, p2], [0.15, 0.12, 0.05], up=(0, 0, 1))
    gem(a, (x, y, zc + 1.0), 0.38, 0.78)
    for k in range(4):  # венец: четыре зубца по краю чаши между когтями
        t = math.pi / 2 * k
        tine(a, V((x + 0.42 * math.cos(t), y + 0.42 * math.sin(t), zc + 0.3)), 0.07, 0.07, zc + 0.75)
    if circle:  # магический круг и парящие осколки
        for r, zz in ((1.0, 0.05), (1.42, 0.07)):
            a.frame("neonCrystal", K.S.octagon(x - r, x + r, y - r, y + r, r * 0.42), 0.08, zz, zz + 0.04, axis="z",
                    bevel=0)
        for k in range(3):
            t = 2 * math.pi * k / 3 + 0.4
            gem(a, (x + 0.75 * math.cos(t), y + 0.75 * math.sin(t), z0 + 0.5 + 0.55 * k), 0.09, 0.17)


# ── сборка ───────────────────────────────────────────────────────────────────────────────────────────────────
def dragon(royal=True, palette=None, with_scepter=True):
    a = new_art("DragonV7" if royal else "DragonV6c", palette)
    a.group = "Torso"
    body = [(-2.3, 2.75), (-3.2, 3.7), (-3.5, 5.0), (-3.05, 6.2), (-1.8, 7.0), (-0.3, 6.65), (1.2, 5.9), (2.6, 5.45),
            (3.5, 4.7), (3.65, 3.7), (3.0, 2.8), (1.8, 2.35), (0.2, 2.2), (-1.3, 2.4)]
    with tag(a, "body"):
        for i, (w, sy, sz) in enumerate([(1.0, 1.0, 1.0), (1.6, 0.94, 0.93), (2.05, 0.8, 0.8)]):
            key("belly" if i == 0 else "scale")  # середина — сливовый живот и грудь, бока — фиолетовая чешуя
            K.slab(a, K.scaled(body, (0.2, 4.35), sy, sz), -w, w)
        for s in S2:
            key("belly")
            K.layered(a, [(-3.62, 4.25), (-3.78, 5.25), (-3.3, 6.05), (-2.6, 5.7), (-2.7, 4.4)],
                      [(0.48, 1.0, 1.0), (0.66, 0.9, 0.88)], anchor=(-3.0, 5.1), xc=s * 0.72)
            key("scale")
            K.layered(a, [(-3.2, 3.6), (-3.3, 5.3), (-2.55, 6.85), (-1.1, 6.6), (-1.25, 4.8), (-2.05, 3.5)],
                      [(0.42, 1.0, 1.0), (0.64, 0.86, 0.86)], anchor=(-2.2, 5.1), xc=s * 2.0)
        bridge = [(-3.25, 5.35), (-3.95, 6.3), (-4.3, 7.25), (-4.05, 8.0), (-3.35, 7.7), (-2.3, 7.3), (-1.3, 6.95),
                  (-1.75, 5.9)]
        for i, (w, sy, sz) in enumerate([(1.08, 1.0, 1.0), (1.5, 0.9, 0.88), (1.85, 0.78, 0.76)]):
            key("belly" if i == 0 else "scale")  # мост шеи: середина — сливовое горло
            K.slab(a, K.scaled(bridge, (-2.9, 6.6), sy, sz), -w, w)
        key("scale")
        K.layered(a, [(-3.45, 8.25), (-2.95, 8.7), (-1.6, 7.55), (-0.55, 7.05), (-1.85, 6.75)],
                  [(0.62, 1.0, 1.0), (0.9, 0.9, 0.86)], anchor=(-2.1, 7.5))
    with tag(a, "wingroots"):
        key("scale")
        for s in S2:
            K.chain(a, [(s * 1.75, -1.75, 6.3), (s * 1.6, -1.2, 7.05)], [1.15, 0.85], [1.25, 0.9])
    a.group = "Neck"
    neck = [(0, -2.6, 5.95), (0, -3.75, 6.95), (0, -3.95, 8.1), (0, -3.5, 9.0), (0, -3.8, 9.8), (0, -4.35, 10.2)]
    with tag(a, "neck"):
        key("scale")
        K.chain(a, neck, [2.6, 2.22, 1.88, 1.62, 1.46, 1.36], [2.7, 2.3, 1.92, 1.65, 1.48, 1.38], up=(0, -1, 0))
    head(a, (0, -4.15, 9.75), royal=royal)
    a.group = "Torso"
    with tag(a, "spines"):
        key("scaleD")
        K.spines(a, [V(p) + V((0, 0.8, 0.25)) for p in neck[2:-1]] +
                 [V((0, -1.4, 7.55)), V((0, -0.3, 7.1)), V((0, 1.0, 6.4)), V((0, 2.2, 5.95)), V((0, 3.15, 5.4))],
                 [0.5, 0.46, 0.42, 0.78, 0.72, 0.6, 0.5, 0.42], up=(0, 0.4, 1), lean=0.4)
    legs = {}
    for s in S2:
        sfx = "L" if s > 0 else "R"
        a.group = "ForeLeg" + sfx
        step = s > 0
        sh = V((s * 2.05, -2.35, 5.25))
        el = V((s * 2.5, -2.25, 3.45)) if step else V((s * 2.5, -1.9, 3.25))
        wr = V((s * 2.4, -3.35, 1.55)) if step else V((s * 2.38, -2.45, 1.3))
        with tag(a, "foreleg" + sfx):
            key("scale")
            K.chain(a, [sh, el, wr], [1.62, 1.35, 1.1], [1.8, 1.45, 1.12], up=(0, -1, 0))
            key("ivory")
            K.spike(a, el + V((s * 0.3, 0.3, 0.0)), el + V((s * 0.55, 1.1, 0.2)), 0.42)
            paw(a, s, wr, wr + V((0, 0.0, -0.25)), (-3.95 if step else -3.1))
        a.group = "HindLeg" + sfx
        with tag(a, "hindleg" + sfx):
            hock, ankle = hind_leg(a, s, 0.0 if s > 0 else 0.35)
        legs[s] = (el, wr, hock, ankle)
        a.group = "Wing" + sfx
        with tag(a, "wing" + sfx):
            wing(a, V((s * 1.55, -1.1, 7.0)), s,
                 {"E": (2.05, 2.25), "W": (3.95, 3.9), "F": [(6.6, 3.05), (6.95, 0.78), (5.9, -1.2), (4.05, -2.15)]},
                 sweep=20 if s > 0 else 26, lean=12, tilt=6 if s > 0 else -3, flank=(s * 1.75, 1.0, 5.2))
    a.group = "Tail"
    tail = [(0, 3.4, 4.5), (0, 4.8, 4.65), (0.6, 6.2, 3.85), (1.8, 7.2, 2.45), (3.0, 7.5, 1.15), (4.3, 7.0, 0.58),
            (5.3, 5.9, 0.48), (5.6, 4.6, 0.45)]
    ws = [2.05, 1.75, 1.45, 1.2, 0.97, 0.77, 0.6, 0.47]
    with tag(a, "tail"):
        key("scale")
        K.chain(a, tail, ws, up=(0, 0, 1))
        key("scaleD")
        K.spines(a, [V(p) + V((0, 0, w * 0.45)) for p, w in zip(tail[1:-1], ws[1:-1])],
                 [0.62, 0.56, 0.48, 0.4, 0.34, 0.28])
        end, prev = V(tail[-1]), V(tail[-2])
        d = (end - prev).normalized()
        m = Matrix.Translation(end) @ Matrix.Rotation(math.atan2(d.x, -d.y), 4, "Z")
        a.extrude("ivory", [(0.0, 0.25), (0.5, 0.5), (0.9, -0.15), (0.45, -1.25), (0.0, -0.2)], -0.08, 0.08, axis="x",
                  matrix=m)
    if royal:
        torso_armor(a)
        for s in S2:
            el, wr, hock, ankle = legs[s]
            foreleg_armor(a, s, el, wr)
            hindleg_armor(a, s, hock, ankle)
        tail_armor(a, tail, ws)
        a.group = "Torso"
        with tag(a, "collar"):
            collar(a)
        for s in S2:
            mantle_side(a, s)
        if with_scepter:
            with tag(a, "scepter"):
                scepter(a)
    a.group = None
    return a


def hind_leg(a, s, dy):
    key("scale")
    K.layered(a, [(0.6, 5.35), (2.9, 5.75), (3.95, 4.5), (3.8, 3.0), (3.0, 2.0), (1.5, 2.0), (0.45, 3.3)],
              [(0.64, 1.0, 1.0), (0.96, 0.87, 0.87)], anchor=(2.2, 3.8), xc=s * 1.92)
    key("belly")
    K.layered(a, [(1.0, 2.95), (1.65, 3.05), (1.8, 2.05), (1.3, 1.62), (0.85, 2.1)], [(0.6, 1.0, 1.0)],
              anchor=(1.3, 2.4), xc=s * 2.06)
    knee, hock = V((s * 2.06, 1.55, 2.0)), V((s * 2.1, 3.5 + dy, 1.15))
    key("scale")
    K.chain(a, [knee, hock], [1.42, 1.02], [1.55, 1.05], up=(0, -1, 0))
    K.layered(a, [(1.9, 2.8), (2.95, 2.62), (3.6 + dy * 0.6, 1.55), (3.4 + dy * 0.6, 1.08), (2.3, 1.55)],
              [(0.44, 1.0, 1.0)], anchor=(2.6, 1.9), xc=s * 2.1)
    key("ivory")
    K.spike(a, hock + V((0, 0.35, 0.05)), hock + V((0, 1.05, 0.2)), 0.38)
    ankle = V((s * 2.1, 2.8 + dy, 0.42))
    key("scale")
    K.chain(a, [hock, ankle], [1.02, 0.94], up=(0, -1, 0))
    paw(a, s, ankle, ankle, 1.75 + dy, width=1.42, claw=0.68)
    return hock, ankle


def paw(a, s, wrist, ankle, front_y, z=0.3, width=1.45, claw=0.72):
    """Лапа v5: ступня, три пальца с когтями, внутренний коготь (геометрия без изменений, с цветами)."""
    x = wrist.x
    key("scale")
    K.taper(a, ankle, V((x, front_y + 0.55, z)), 1.2, 1.25, 0.9, 0.62)
    for dx, ln in ((-0.42, 0.62), (0.0, 0.72), (0.42, 0.62)):
        b = V((x + dx * width / 1.45, front_y + 0.55, z))
        e = b + V((dx * 0.25, -ln, -0.08))
        key("scale")
        K.taper(a, b, e, 0.42, 0.34, 0.42, 0.3)
        key("ivory")
        K.spike(a, e + V((0, 0.05, 0.02)), e + V((dx * 0.1, -claw, -0.2)), 0.3)
    b = V((x - s * 0.62, front_y + 0.9, z + 0.1))
    K.spike(a, b, b + V((-s * 0.45, -0.25, -0.15)), 0.28)


def wing(a, root, s, local, sweep, lean, tilt, flank, bone=(0.55, 0.38, 0.2)):
    """Крыло v5 (геометрия без изменений): пурпурные перепонки, тёмные кости, когти слоновой кости."""
    M = (Matrix.Translation(root) @ Matrix.Rotation(math.radians(s * sweep), 4, "Z")
         @ Matrix.Rotation(math.radians(-s * tilt), 4, "Y") @ Matrix.Rotation(math.radians(lean), 4, "X")
         @ Matrix.Scale(s, 4, V((1, 0, 0))))
    t = M.inverted() @ V(flank)
    E, W, T = V(local["E"]), V(local["W"]), V((t.x, t.z))
    F = [V(f) for f in local["F"]]

    def P(v):
        return M @ V((v.x, 0.0, v.y))

    def notch(p, q, k=0.3):
        mid = (p + q) / 2
        return mid + (W - mid) * k

    for i, (p, q) in enumerate(zip(F, F[1:])):
        dy = 0.06 * (i % 2)
        a.extrude("wing", [tuple(W), tuple(p), tuple(notch(p, q)), tuple(q)], -0.05 + dy, 0.05 + dy, axis="y", matrix=M)
    a.extrude("wing", [tuple(W), tuple(F[-1]), tuple(notch(F[-1], T, 0.22)), tuple(T), (0.0, 0.0), tuple(E)], -0.05,
              0.05, axis="y", matrix=M)
    key("bone")
    K.chain(a, [P(V((0, 0))), P(E), P(W)], [bone[0], bone[0] * 0.8, bone[1]], up=(0, 0, 1))
    for f in F:
        key("bone")
        K.chain(a, [P(W), P(f)], [bone[1] * 0.85, bone[2] * 0.45], up=(0, 0, 1), overlap=0.2)
        key("ivory")
        K.spike(a, P(f), P(f) + (P(f) - P(W)).normalized() * 0.55, bone[2] * 0.6)
    key("ivory")
    K.spike(a, P(W), P(W) + (M.to_3x3() @ V((0.15, 0.0, 1.0))).normalized() * 0.85, bone[1] * 0.85)
    K.spike(a, P(E), P(E) + (M.to_3x3() @ V((-0.3, 0.0, 0.9))).normalized() * 0.5, bone[1] * 0.6)


def scepter_only():
    a = new_art("ScepterV7")
    scepter(a, base=(0.0, 0.0))
    return a
