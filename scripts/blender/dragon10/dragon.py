"""Король-дракон (босс 10), эталон v2: новая геометрия с нуля (не доработка блок-аута v1).

Анатомия: мощная грудная клетка и широкие плечи (сечения тела — суперэллипсы, талия уже груди), толстая изогнутая
шея, крупная морда (череп и отдельная нижняя челюсть для клипов), тяжёлые надбровья, ноздри, клыки, рога с золотыми
кольцами, корона-реликвия (ступенчатый обод, зубцы-лилии с камнями, бархатная шапка, дуги, держава). Броня — отдельные
оболочки по поверхности тела: нагрудник с килем, пояс с пряжкой, набедренники, ступенчатые наплечники и наколенники,
наручи. Ноги пальцеходящие, хвост ступенчатыми сегментами с золотыми шипами и наконечником-лезвием, крылья — кости и
перепонки с прогибом, мантия со складками и горностаевым воротником, скипетр с державой.

Части (будущие MeshPart на Motor6D): см. PARTS. Единица — модель; в игре ×3 (как у Сфинкса). Лицом к −y.
"""

import math

import bmesh
import dk
from dk import V, Mesh, superellipse
from mathutils import Matrix

S = (1, -1)  # +x — левая сторона дракона (справа в кадре спереди)
# Детализация: HERO — концепт-рендер, GAME — игровая копия ≤ 8 000 треугольников (те же формы, меньше граней).
HERO = dict(body=12, limb=10, crown=20, cape=17, cage=4, horn=9, gem=8, orb=10, rows=5, steps=1.0, trim=6, cape_rows=8,
            band_steps=True, brow=6, dome=12, grips=4, head=12, side_gems=True, ballr=4, cuffs=2, ermine=13, collar=10)
GAME = dict(body=10, limb=8, crown=12, cape=11, cage=2, horn=7, gem=6, orb=8, rows=3, steps=0.65, trim=4, cape_rows=6,
            band_steps=False, brow=4, dome=10, grips=2, head=10, side_gems=False, ballr=3, cuffs=1, ermine=9, collar=8)
Q = dict(HERO)

# Тело: (z, полуширина, перед, зад, центр y, квадратность)
TORSO = [(2.45, 0.98, 0.85, 0.95, 0.42, 2.4), (2.85, 1.2, 1.0, 1.1, 0.4, 2.5), (3.3, 1.22, 1.0, 1.1, 0.36, 2.5),
         (3.75, 1.08, 1.0, 1.02, 0.3, 2.5), (4.25, 1.3, 1.1, 1.02, 0.24, 2.5), (4.8, 1.66, 1.24, 1.04, 0.16, 2.6),
         (5.35, 2.02, 1.24, 1.06, 0.1, 2.6), (5.85, 2.08, 1.08, 1.02, 0.12, 2.6), (6.25, 1.6, 0.84, 0.88, 0.18, 2.5),
         (6.5, 0.98, 0.72, 0.76, 0.16, 2.4)]
# Череп вдоль −y: (y, полуширина, верх, низ, центр z, квадратность)
SKULL = [(0.12, 0.72, 0.5, 0.48, 8.48, 2.6), (-0.25, 0.95, 0.74, 0.55, 8.46, 2.8), (-0.72, 0.92, 0.7, 0.52, 8.42, 2.8),
         (-1.2, 0.74, 0.52, 0.42, 8.3, 2.8), (-1.75, 0.63, 0.43, 0.34, 8.2, 3.0), (-2.25, 0.6, 0.41, 0.31, 8.16, 3.0),
         (-2.55, 0.5, 0.34, 0.26, 8.14, 3.0), (-2.68, 0.36, 0.24, 0.18, 8.13, 3.0)]
JAW = [(-0.05, 0.7, 7.98, 7.6), (-0.7, 0.68, 7.92, 7.5), (-1.4, 0.56, 7.88, 7.55), (-2.05, 0.47, 7.86, 7.62),
       (-2.38, 0.36, 7.85, 7.7)]
CROWN = V((0, -0.42, 9.08))
CROWN_R = (0.6, 0.56)


def lerp(a, b, t):
    return a + (b - a) * t


def sec_at(z):
    for a, b in zip(TORSO, TORSO[1:]):
        if a[0] <= z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0])
            return [lerp(x, y, t) for x, y in zip(a, b)]
    return list(TORSO[0] if z < TORSO[0][0] else TORSO[-1])


def surf(z, ang, off=0.0):
    """Точка поверхности тела на высоте z; ang — градусы от центра груди (+90 — левый бок, +x)."""
    _, w, fr, bk, cy, p = sec_at(z)
    t = math.radians(90 - ang)
    c, s = math.cos(t), math.sin(t)
    x = (w + off) * math.copysign(abs(c) ** (2 / p), c)
    d = ((fr if s > 0 else bk) + off) * math.copysign(abs(s) ** (2 / p), s)
    return V((x, cy - d, z))


def body_ring(z, n=None):
    n = n or Q["body"]
    return [surf(z, 90 - math.degrees(math.pi / n + 2 * math.pi * i / n)) for i in range(n)]


def plate(m, key, a0, a1, z_of, off, th, steps, rows):
    """Пластина по поверхности тела: дуга a0…a1, края z_of(a) → (низ, верх); rows рядов по высоте — пластина
    гнётся вместе с телом (иначе выпуклая грудь проходит сквозь плоскую грань). Возвращает наружные грани."""
    rows = min(rows, Q["rows"])
    steps = max(3, round(steps * Q["steps"]))
    rings = []
    for k in range(steps):
        a = lerp(a0, a1, k / (steps - 1))
        z0, z1 = z_of(a)
        zs = [lerp(z0, z1, i / (rows - 1)) for i in range(rows)]
        rings.append([surf(z, a, off) for z in zs] + [surf(z, a, off - th) for z in reversed(zs)])
    faces = m.rings(key, rings)
    L = 2 * rows
    return [faces[k * L + j] for k in range(steps - 1) for j in range(rows - 1)]


def band(m, key, z0, z1, a0, a1, off, th, steps=8, gap=0.025):
    """Пояс-пластина постоянной высоты z0…z1 по дуге a0…a1; возвращает наружные грани."""
    rows = max(2, int((z1 - z0) / 0.22) + 1)
    return plate(m, key, a0, a1, lambda a: (z0 + gap, z1 - gap), off, th, steps, rows)


def shell(m, key, a0, a1, zlo, zhi, off, th, steps=10, rows=5):
    """Пластина по телу с переменными краями: zlo(a), zhi(a) — нижний и верхний край на угле a."""
    return plate(m, key, a0, a1, lambda a: (zlo(a), zhi(a)), off, th, steps, rows)


def head_ring(sec, n=None):
    n = n or Q["head"]
    y, w, ht, hb, cz, p = sec
    return [V((x, y, cz + z)) for x, z in superellipse(n, w, 1.0, p, top=ht, bottom=hb)]


def skull_top(y):
    for a, b in zip(SKULL, SKULL[1:]):
        if b[0] <= y <= a[0]:
            t = (y - a[0]) / (b[0] - a[0])
            return lerp(a[4] + a[2], b[4] + b[2], t)
    return SKULL[0][4] + SKULL[0][2]


def cone(m, key, p0, p1, r0, r1=0.004, n=6, up=(0, 0, 1)):
    m.tube(key, [p0, p1], lambda t: superellipse(n, lerp(r0, r1, t), lerp(r0, r1, t), 2.2), up=up)


def blade(m, key, origin, side, up, length, height, lean=0.9, th=0.05):
    """Плоский шип-лезвие: основание вдоль своей оси X, вершина смещена на lean (наклон к концу)."""
    mat = dk.basis(origin, side, up)
    m.flat(key, [(-length * 0.5, 0.0), (length, 0.0), (length * lean, height)], th, mat, back=th)


# ── голова ──────────────────────────────────────────────────────────────────────────────────────────
def head(m):
    m.rings("scale", [head_ring(s) for s in SKULL])
    # тяжёлые надбровья: от переносицы к основанию рогов, внутренний край ниже — строгий взгляд
    for s in S:
        m.tube("scaleD", [(s * 0.16, -1.34, 8.78), (s * 0.55, -1.1, 8.98), (s * 0.9, -0.58, 9.03), (s * 1.0, -0.12, 8.95)],
               lambda t: superellipse(6, 0.17 * (1 - 0.35 * t), 0.12, 2.2), samples=Q["brow"])
        # глаз: миндалина (свечение), вертикальный зрачок, блик; веко снизу
        n = V((s * 0.62, -0.78, 0.08))
        e = dk.basis((s * 0.75, -1.06, 8.62), n)
        k = 1.28  # глаз крупнее — читается с игровой камеры
        eye = [(-0.22, -0.02), (-0.1, 0.1), (0.12, 0.12), (0.25, 0.06), (0.17, -0.07), (-0.06, -0.1)]
        m.flat("eye", [(u * s * k, v * k) for u, v in eye], 0.05, e, back=0.06)
        m.flat("dark", [(0.02 * s * k, 0.1 * k), (0.07 * s * k, 0.0), (0.02 * s * k, -0.09 * k), (-0.03 * s * k, 0.0)],
               0.075, e, back=0.0)
        m.flat("white", [(-0.1 * s, 0.04), (-0.05 * s, 0.04), (-0.05 * s, 0.09), (-0.1 * s, 0.09)], 0.085, e, back=0.0)
        m.tube("dark", [e @ V((-0.26 * s, -0.04, 0.0)), e @ V((-0.12 * s, -0.04, 0.14)), e @ V((0.16 * s, -0.04, 0.16)),
                        e @ V((0.33 * s, -0.04, 0.08))], lambda t: superellipse(4, 0.025, 0.025, 2))
        m.tube("scaleD", [(s * 0.55, -1.2, 8.46), (s * 0.85, -0.95, 8.48)], lambda t: superellipse(4, 0.06, 0.05, 2))
        # ноздри: бугор и тёмное отверстие
        m.ball("scale", (s * 0.25, -2.45, 8.5), 0.13, n=8, rows=4, sz=0.8)
        nm = dk.basis((s * 0.27, -2.57, 8.53), (s * 0.3, -1, 0.5))
        m.flat("dark", [(-0.06, -0.035), (0.06, -0.035), (0.06, 0.035), (-0.06, 0.035)], 0.03, nm, back=0.02)
        # клыки сверху — свисают снаружи узкой нижней челюсти
        cone(m, "ivory", (s * 0.5, -2.12, 7.95), (s * 0.5, -2.14, 7.6), 0.085)
        cone(m, "ivory", (s * 0.56, -1.62, 7.95), (s * 0.56, -1.63, 7.72), 0.06)
        # гребни-плавники за челюстью
        for tip, r in (((s * 1.48, 0.38, 8.66), 0.13), ((s * 1.6, 0.52, 8.2), 0.12), ((s * 1.4, 0.42, 7.8), 0.1)):
            cone(m, "scaleD", (s * 0.78, -0.12, 8.22), tip, r, n=4)
        # рога: изгиб назад и вверх, сужение к кончику, два золотых кольца
        horn = [(s * 0.78, -0.3, 8.86), (s * 0.98, 0.15, 9.28), (s * 1.22, 0.75, 9.55), (s * 1.36, 1.35, 9.95),
                (s * 1.36, 1.62, 10.45)]
        m.tube("ivory", horn, lambda t: superellipse(6, 0.25 * (1 - t) ** 0.8 + 0.015, 0.25 * (1 - t) ** 0.8 + 0.015, 2.2),
               samples=Q["horn"])
        hp = dk.spline(horn, Q["horn"])
        for i0, i1 in ((1, 2), (3, 4))[: Q["cuffs"]]:
            r = 0.25 * (1 - i0 / (Q["horn"] - 1)) ** 0.8 + 0.06
            m.tube("gold", [hp[i0], hp[i0] + (hp[i1] - hp[i0]) * 0.45],
                   lambda t, r=r: superellipse(6, r, r, 2.2))
        cone(m, "ivory", (s * 0.92, -0.08, 8.52), (s * 1.38, 0.52, 8.72), 0.12)
    # спинка носа — три ступенчатые пластины
    for y in (-1.38, -1.78, -2.14):
        z = skull_top(y)
        pm = dk.basis((0, y, z), (0, -0.23, 1), up=(0, -1, 0))
        m.flat("scaleD", [(-0.17, -0.13), (0.17, -0.13), (0.13, 0.13), (-0.13, 0.13)], 0.06, pm, back=0.03)
    # пасть: тёмная щель между челюстями
    m.flat("mouth", [(-0.42, -0.04), (0.42, -0.04), (0.42, 0.04), (-0.42, 0.04)], 2.05,
           dk.basis((0, -0.28, 7.88), (0, -1, 0)), back=0.0)


def crown(m):
    cx, cy, cz = CROWN
    rx, ry = CROWN_R

    def ell(k, z, n=None):
        n = n or Q["crown"]
        return [V((cx + rx * k * math.sin(2 * math.pi * i / n), cy - ry * k * math.cos(2 * math.pi * i / n), z))
                for i in range(n)]

    # обод: ступенчатый профиль (нижний кант, лента, верхний кант), замкнутое кольцо
    prof = [(0.9, 0.0), (1.07, 0.0), (1.07, 0.08), (1.02, 0.08), (1.02, 0.3), (1.08, 0.3), (1.08, 0.38), (0.9, 0.38)]
    if not Q["band_steps"]:
        prof = [(0.9, 0.0), (1.07, 0.0), (1.04, 0.19), (1.08, 0.38), (0.9, 0.38)]
    rings = [ell(k, cz + dz) for k, dz in prof]
    m.rings("gold", rings, closed=True)
    # бархатная шапка, две дуги, держава с камнем
    m.rings("velvet", [ell(0.92, cz + 0.36), ell(0.86, cz + 0.52), ell(0.7, cz + 0.68), ell(0.42, cz + 0.8),
                       ell(0.12, cz + 0.85)])
    for ax in ((0, 1), (1, 0)):
        pts = []
        for i in range(7):
            a = math.pi * i / 6
            pts.append(V((cx + ax[0] * rx * 0.98 * math.cos(a), cy + ax[1] * ry * 0.98 * math.cos(a),
                          cz + 0.38 + 0.62 * math.sin(a))))
        m.tube("gold", pts, lambda t: superellipse(Q["trim"], 0.055, 0.055, 2.2), up=(1 - ax[0], 1 - ax[1], 0))
    m.ball("gold", (cx, cy, cz + 1.08), 0.12, n=8, rows=Q["ballr"] + 1)
    m.gem("ruby", (cx, cy, cz + 1.19), (0, 0, 1), 0.07, up=(0, -1, 0))
    # зубцы-лилии с камнями: спереди выше, назад ниже
    gems = ("ruby", "sapphire", "emerald")
    for k, (phi, h) in enumerate(((0, 0.66), (40, 0.5), (-40, 0.5), (82, 0.4), (-82, 0.4), (130, 0.34), (-130, 0.34),
                                  (180, 0.34))):
        a = math.radians(phi)
        out = V((math.sin(a), -math.cos(a) * ry / rx, 0)).normalized()
        base = V((cx + rx * 1.04 * math.sin(a), cy - ry * 1.04 * math.cos(a), cz + 0.36))
        mat = dk.basis(base, out + V((0, 0, 0.12)))
        w = 0.17 if phi == 0 else 0.14
        m.flat("gold", [(-w, 0), (w, 0), (w * 0.85, h * 0.45), (w * 0.4, h * 0.56), (0, h), (-w * 0.4, h * 0.56),
                        (-w * 0.85, h * 0.45)], 0.05, mat, back=0.02)
        if abs(phi) <= (90 if Q["side_gems"] else 45):
            m.gem(gems[0] if phi == 0 else gems[1 + k % 2], mat @ V((0, -0.06, h * 0.3)), out,
                  0.11 if phi == 0 else 0.065)
    m.gem("ruby", V((cx, cy - ry * 1.08 - 0.03, cz + 0.2)), (0, -1, 0), 0.1, bezel="gold")


def jaw(m):
    rings = []
    for y, w, top, bot in JAW:
        cz, h = (top + bot) / 2, (top - bot) / 2
        rings.append([V((x, y, cz + z)) for x, z in superellipse(Q["limb"], w, h, 2.8)])
    m.rings("scale", rings)
    for k, y in enumerate((-0.85, -1.35, -1.85)):  # кремовые пластины подбородка
        pm = dk.basis((0, y, 7.5 + k * 0.03), (0, -0.1, -1), up=(0, -1, 0))
        m.flat("belly", [(-0.3, -0.18), (0.3, -0.18), (0.26, 0.18), (-0.26, 0.18)], 0.04, pm, back=0.03)


# ── шея и тело ──────────────────────────────────────────────────────────────────────────────────────
NECK = [(0, 0.15, 6.15), (0, -0.05, 6.85), (0, -0.4, 7.45), (0, -0.55, 7.98)]


def neck(m):
    m.tube("scale", NECK, lambda t: superellipse(Q["limb"], 0.84 - 0.22 * t, 1.0, 2.5, top=0.74 - 0.16 * t,
                                                 bottom=0.8 - 0.2 * t), up=(0, -1, 0), samples=6)
    P = dk.spline(NECK, 6)
    fr = dk.frames(P, (0, -1, 0))
    for i in (1, 2, 3, 4):  # кремовые пластины горла и шипы по загривку
        c, r, u = fr[i]
        t = i / 5
        front = c + u * (0.74 - 0.16 * t + 0.02)
        m.flat("belly", [(-0.34, -0.12), (0.34, -0.12), (0.3, 0.12), (-0.3, 0.12)], 0.05,
               dk.basis(front, u, up=(P[i + 1] - P[i - 1])), back=0.04)
        back = c - u * (0.8 - 0.2 * t - 0.05)
        blade(m, "scaleD", back, r, (-u + V((0, 0, 0.6))).normalized(), 0.28, 0.42 - 0.04 * i)


def torso(m, pelvis):
    lo = [s for s in TORSO if s[0] <= 3.75]
    hi = [s for s in TORSO if s[0] >= 3.75]
    pelvis.rings("scale", [body_ring(s[0]) for s in lo])
    m.rings("scale", [body_ring(s[0]) for s in hi])
    # живот: колонна кремовых щитков, книзу уже, с контуром D39
    for z0, z1, a, mm in ((2.66, 2.92, 28, pelvis), (2.95, 3.25, 32, pelvis), (3.62, 3.98, 38, m), (4.0, 4.38, 42, m),
                          (4.4, 4.8, 46, m)):
        outer = band(mm, "belly", z0, z1, -a, a, 0.05, 0.1, steps=7)
        mm.contour(outer, "bellyD", 0.04, 0.012)
    # нагрудник: две грудные пластины (нижний край поднимается к бокам, как мышцы груди), киль, рубин
    for sgn in (1, -1):
        a0, a1 = (6, 84) if sgn > 0 else (-84, -6)
        outer = shell(m, "gold", a0, a1, lambda a: 4.84 + 0.5 * (abs(a) / 84) ** 1.4,
                      lambda a: 5.98 - 0.08 * (abs(a) / 84), 0.1, 0.14, steps=11)
        m.contour(outer, "goldD", 0.07, 0.03)
    y0, y1 = surf(4.78, 0, 0.13).y, surf(5.98, 0, 0.13).y
    m.tube("goldD", [(0, y0 - 0.03, 4.78), (0, y1 - 0.03, 5.98)], lambda t: superellipse(4, 0.09, 0.08, 2),
           up=(0, -1, 0))
    m.gem("ruby", surf(5.6, 0, 0.16) + V((0, -0.06, 0)), (0, -1, 0.15), 0.15, bezel="gold")
    # ворот (горжет) в два яруса
    band(m, "gold", 6.12, 6.42, -180, 180, 0.12, 0.16, steps=17, gap=0.0)
    band(m, "goldD", 6.4, 6.58, -180, 180, 0.06, 0.12, steps=17, gap=0.0)
    # пояс с пряжкой и набедренники
    band(pelvis, "gold", 3.28, 3.56, -180, 180, 0.08, 0.12, steps=17, gap=0.0)
    f = surf(3.42, 0, 0.12)
    bm = dk.basis(f, (0, -1, 0))
    buckle = pelvis.flat("gold", [(-0.38, -0.2), (-0.28, -0.3), (0.28, -0.3), (0.38, -0.2), (0.38, 0.2), (0.28, 0.3),
                                  (-0.28, 0.3), (-0.38, 0.2)], 0.1, bm, back=0.05)
    pelvis.contour([buckle[1]], "goldD", 0.05, 0.015)
    pelvis.gem("ruby", f + V((0, -0.11, 0)), (0, -1, 0), 0.12)
    for a0, a1, z0 in ((-74, -36, 2.62), (36, 74, 2.62), (-22, 22, 2.72)):
        outer = band(pelvis, "gold", z0, 3.3, a0, a1, 0.16, 0.08, steps=5, gap=0.0)
        pelvis.contour(outer, "goldD", 0.045, 0.012)


# ── руки ────────────────────────────────────────────────────────────────────────────────────────────
ARMS = {1: ((2.02, 0.12, 5.85), (2.85, 0.5, 4.8), (2.0, -0.3, 3.86)),
        -1: ((-2.02, 0.12, 5.85), (-2.66, 0.05, 4.66), (-2.68, -0.6, 3.98))}


def arm(upper, fore, hand, s):
    Sh, E, W = (V(p) for p in ARMS[s])
    mid = (Sh + E) / 2 + V((s * 0.08, 0, 0))
    upper.tube("scale", [Sh + V((0, 0, 0.2)), mid, E], lambda t: superellipse(Q["limb"], 0.5 - 0.08 * t + 0.05 * math.sin(math.pi * t),
                                                                            0.47 - 0.1 * t, 2.5), up=(0, -1, 0), samples=5)
    axis = V((s * 0.85, 0.0, 0.55)).normalized()
    upper.dome("gold", Sh + V((s * 0.1, 0, 0.1)), axis, [0.98, 0.8, 0.6, 0.38], 0.15, n=Q["dome"], p=2.5,
               keys=["gold", "goldD"])
    top = Sh + V((s * 0.1, 0, 0.1)) + axis * 0.6
    for dy in (-0.25, 0.25):
        cone(upper, "gold", top + V((0, dy, 0)), top + V((s * 0.35, dy * 1.4, 0.55)), 0.11)
    upper.gem("ruby", top + axis * 0.02 + V((0, -0.32, 0.0)), (s * 0.3, -1, 0.3), 0.1)
    fore.tube("scale", [E, W], lambda t: superellipse(Q["limb"], 0.44 - 0.1 * t, 0.4 - 0.08 * t, 2.5), up=(0, -1, 0), samples=4)
    for t0, t1, key in ((0.5, 0.66, "goldD"), (0.68, 0.94, "gold")):
        a, b = E.lerp(W, t0), E.lerp(W, t1)
        fore.tube(key, [a, b], lambda t, t0=t0, t1=t1: superellipse(Q["limb"], 0.44 - 0.1 * lerp(t0, t1, t) + 0.06,
                                                                   0.4 - 0.08 * lerp(t0, t1, t) + 0.06, 2.6), up=(0, -1, 0))
    cone(fore, "ivory", E + V((s * 0.1, 0.3, 0.05)), E + V((s * 0.3, 0.75, 0.2)), 0.12)
    # кулак: ступенчатый блок, костяшки, когти к ладони
    d = (W - E).normalized()
    F = W + d * 0.3
    hand.tube("scale", [W, F, F + d * 0.28], lambda t: superellipse(Q["limb"], 0.32 + 0.06 * math.sin(math.pi * t), 0.28, 3.0),
              up=(0, -1, 0))
    side = d.cross(V((0, 0, 1))).normalized()
    for k in (-1, 0, 1):
        kp = F + d * 0.2 + side * (0.14 * k) + V((0, -0.22, 0))
        hand.ball("scaleD", kp, 0.1, n=6, rows=Q["ballr"])
        cone(hand, "ivory", kp + V((0, -0.05, -0.05)), kp + V((0, 0.05, -0.28)), 0.06, n=4)


# ── ноги ────────────────────────────────────────────────────────────────────────────────────────────
def leg(thigh, shin, foot, s):
    dy = -0.22 if s > 0 else 0.28  # левая нога чуть вперёд, правая назад — живая стойка
    H, K = V((s * 1.0, 0.35, 3.0)), V((s * 1.3, -0.5 + dy, 1.95))
    A, B = V((s * 1.3, 0.3 + dy, 0.85)), V((s * 1.3, -0.3 + dy, 0.24))
    thigh.tube("scale", [H, H + V((s * 0.18, -0.55, -0.45)), K], lambda t: superellipse(
        10, 0.84 - 0.26 * t, 1.0, 2.5, top=0.86 - 0.26 * t, bottom=0.76 - 0.3 * t), up=(0, -1, 0), samples=5)
    thigh.dome("gold", K + V((0, -0.3, 0.06)), (0, -1, 0.3), [0.5, 0.38, 0.24], 0.12, n=10, p=2.5,
               keys=["gold", "goldD"])
    shin.tube("scale", [K, A], lambda t: superellipse(Q["limb"], 0.48 - 0.16 * t, 0.46 - 0.14 * t, 2.5), up=(0, -1, 0),
              samples=4)
    cone(shin, "ivory", A + V((0, 0.2, 0.05)), A + V((0, 0.6, 0.15)), 0.12, n=5)
    shin.tube("scale", [A, B], lambda t: superellipse(Q["limb"], 0.31 - 0.03 * t, 0.29, 2.5), up=(0, -1, 0))
    x = s * 1.3
    foot.tube("scale", [(x, 0.18 + dy, 0.2), (x, -0.32 + dy, 0.2), (x, -0.74 + dy, 0.17)],
              lambda t: superellipse(Q["limb"], 0.44 - 0.04 * t, 0.2, 3.0, top=1.15, bottom=1.0), up=(0, 0, 1))
    for k, dx in enumerate((-0.27, 0.0, 0.27)):
        p0, p1 = V((x + dx, -0.62 + dy, 0.16)), V((x + dx * 1.25, -1.05 + dy, 0.13))
        foot.tube("scale", [p0, p1], lambda t: superellipse(8, 0.13 - 0.02 * t, 0.12 - 0.02 * t, 2.4))
        cone(foot, "ivory", p1 + V((0, -0.02, 0.0)), p1 + V((dx * 0.1, -0.32, -0.1)), 0.09, n=5)
    cone(foot, "ivory", V((x, 0.3 + dy, 0.2)), V((x, 0.62 + dy, 0.06)), 0.1, n=5)


# ── хвост ───────────────────────────────────────────────────────────────────────────────────────────
TAIL = [(0, 1.05, 2.8), (0, 1.7, 1.7), (0.45, 2.55, 0.72), (1.5, 3.3, 0.4), (2.85, 3.2, 0.35), (3.7, 2.25, 0.34),
        (3.92, 1.05, 0.33)]
TAIL_SPLIT = (0, 5, 9, 13, 16)


def tail(parts):
    P = dk.spline(TAIL, 17)
    fr = dk.frames(P, (0, 0, 1))
    radii = []
    rings = []
    for i, (c, r, u) in enumerate(fr):
        t = i / 16
        rad = (0.74 * (1 - t) ** 0.85 + 0.07) * (1.08 if i % 2 else 1.0)
        radii.append(rad)
        rings.append([c + r * x + u * z for x, z in superellipse(Q["limb"], rad, rad, 2.5, top=1.0, bottom=0.8)])
    for k, m in enumerate(parts):
        m.rings("scale", rings[TAIL_SPLIT[k]: TAIL_SPLIT[k + 1] + 1])
    for i in range(2, 15, 2):
        c, r, u = fr[i]
        k = next(j for j in range(4) if TAIL_SPLIT[j] <= i < TAIL_SPLIT[j + 1])
        blade(parts[k], "gold", c + u * radii[i] * 0.9, r, u, 0.32 * radii[i] + 0.08, 0.5 * radii[i] + 0.1, lean=1.0)
    c, r, u = fr[-1]
    f = (P[-1] - P[-2]).normalized()
    side = f.cross(V((0, 0, 1))).normalized()  # лезвие строго вертикально, вдоль хвоста
    u = V((0, 0, 1))
    r = side
    parts[-1].tube("gold", [c - f * 0.12, c + f * 0.06],
                   lambda t: superellipse(Q["trim"] + 2, radii[-1] + 0.07, radii[-1] + 0.07, 2.2), up=(0, 0, 1))
    mat = dk.basis(c + f * 0.05, side, u)
    # наконечник-лезвие: широкие «плечи», острие, золотой киль по центру, рубины
    parts[-1].flat("gold", [(0.0, 0.24), (0.4, 0.52), (1.2, 0.0), (0.4, -0.52), (0.0, -0.24), (-0.14, 0.0)], 0.07, mat,
                   back=0.07)
    parts[-1].tube("goldD", [mat @ V((-0.08, 0, 0)), mat @ V((1.05, 0, 0))],
                   lambda t: superellipse(4, 0.1 * (1 - 0.7 * t), 0.12 * (1 - 0.7 * t), 2.0), up=u)
    for side in ((1, -1) if Q["side_gems"] else (1,)):
        parts[-1].gem("ruby", mat @ V((0.42, -0.1 * side, 0.0)), r * side, 0.1)


# ── крылья ──────────────────────────────────────────────────────────────────────────────────────────
def wing(arm_m, hand_m, s):
    R, E, W = V((s * 0.75, 1.62, 6.4)), V((s * 2.1, 2.45, 7.85)), V((s * 3.45, 3.05, 9.25))
    F = [V((s * 6.1, 4.1, 8.7)), V((s * 6.35, 4.5, 6.4)), V((s * 5.35, 4.15, 4.5)), V((s * 3.75, 3.35, 3.75))]
    T = V((s * 1.3, 1.95, 4.6))
    nrm = (F[1] - W).cross(F[0] - W).normalized()
    if nrm.y < 0:
        nrm = -nrm

    def sc(a, b):
        mid = (a + b) / 2
        return mid + (W - mid) * 0.3

    for a, b in zip(F, F[1:]):
        hand_m.membrane("wing", [W, a, sc(a, b), b], 0.42, 0.05, nrm)
    arm_m.membrane("wing", [W, F[-1], sc(F[-1], T), T, R, E], 0.4, 0.05, nrm)
    arm_m.tube("scaleD", [R, (R + E) / 2 + V((0, 0, 0.1)), E], lambda t: superellipse(8, 0.22 - 0.05 * t, 0.2 - 0.04 * t, 2.4),
               samples=4)
    arm_m.tube("scaleD", [E, W], lambda t: superellipse(8, 0.17 - 0.04 * t, 0.16 - 0.04 * t, 2.4))
    arm_m.ball("gold", E, 0.2, n=8, rows=Q["ballr"])
    hand_m.ball("gold", W, 0.19, n=8, rows=Q["ballr"])
    cone(hand_m, "gold", W + V((0, -0.05, 0.12)), W + V((s * 0.15, -0.25, 0.65)), 0.11)
    for f in F:
        hand_m.tube("scaleD", [W, f], lambda t: superellipse(6, 0.12 - 0.085 * t, 0.11 - 0.08 * t, 2.2))
        cone(hand_m, "ivory", f, f + (f - W).normalized() * 0.3, 0.05, n=4)


# ── мантия, воротник, цепь ──────────────────────────────────────────────────────────────────────────
def cape(m):
    rows, cols = Q["cape_rows"], Q["cape"]
    outer, inner = [], []
    for i in range(rows):
        t = i / (rows - 1)
        z = lerp(6.12, 1.95, t)
        rx, ry, amp = 1.82 + 0.5 * t, 1.18 + 0.9 * t, 0.05 + 0.3 * t ** 0.8
        ro, ri = [], []
        for j in range(cols):
            th = math.radians(lerp(-78, 78, j / (cols - 1)))
            fold = amp * math.cos(th * 5.0)
            ro.append(V(((rx + fold) * math.sin(th), 0.32 + (ry + fold) * math.cos(th), z)))
            ri.append(V(((rx + fold - 0.07) * math.sin(th), 0.32 + (ry + fold - 0.07) * math.cos(th), z)))
        outer.append(ro)
        inner.append(ri)
    bm = m.bm
    vo = [[bm.verts.new(p) for p in r] for r in outer]
    vi = [[bm.verts.new(p) for p in r] for r in inner]
    faces = []
    for i in range(rows - 1):
        for j in range(cols - 1):
            faces.append(bm.faces.new((vo[i][j], vo[i][j + 1], vo[i + 1][j + 1], vo[i + 1][j])))
            faces.append(bm.faces.new((vi[i][j], vi[i + 1][j], vi[i + 1][j + 1], vi[i][j + 1])))
    for j in range(cols - 1):
        for i in (0, rows - 1):
            faces.append(bm.faces.new((vo[i][j], vi[i][j], vi[i][j + 1], vo[i][j + 1])))
    for i in range(rows - 1):
        for j in (0, cols - 1):
            faces.append(bm.faces.new((vo[i][j], vo[i + 1][j], vi[i + 1][j], vi[i][j])))
    idx = m.mi("mantle")
    for f in faces:
        f.material_index = idx
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    hem = [p + (p - V((0, 0.32, p.z))).normalized() * 0.02 for p in outer[-1]]
    m.tube("gold", hem, lambda t: superellipse(Q["trim"], 0.08, 0.08, 2.2), up=(0, 0, 1))
    for j in (0, cols - 1):
        m.tube("gold", [r[j] for r in outer], lambda t: superellipse(Q["trim"], 0.07, 0.07, 2.2), up=(1, 0, 0))
    # горностаевый воротник по плечам и спине, пятна, цепь с застёжками
    col = []
    N = Q["ermine"]
    for k in range(N):
        th = math.radians(lerp(-122, 122, k / (N - 1)))
        col.append(V((1.55 * math.sin(th), 0.35 + 1.15 * math.cos(th), 6.2 + 0.08 * math.cos(th))))
    m.tube("ermine", col, lambda t: superellipse(Q["trim"] + 2, 0.3, 0.27, 2.2), up=(0, 0, 1))
    for k in range(1, N - 1, 2):
        th = math.radians(lerp(-122, 122, k / (N - 1)))
        out = V((math.sin(th), math.cos(th) * 1.15 / 1.55, 0)).normalized()
        p = col[k] + out * 0.29 + V((0, 0, 0.05))
        m.flat("dark", [(0, -0.07), (0.035, 0.0), (0, 0.09), (-0.035, 0.0)], 0.03, dk.basis(p, out + V((0, 0, 0.6))),
               back=0.02)
    a, b = col[0], col[-1]
    m.tube("gold", [a, V((0, -1.05, 5.82)), b], lambda t: superellipse(Q["trim"], 0.06, 0.06, 2.2), samples=7, up=(0, 0, 1))
    for p in (a, b):
        m.ball("gold", p + V((0, -0.22, 0)), 0.14, n=8, rows=Q["ballr"])
        m.gem("ruby", p + V((0, -0.36, 0)), (0, -1, 0), 0.07)


def crest(m):
    """Герб на спине мантии: золотой щит с алым полем и короной из трёх зубцов."""
    z, y = 4.7, 0.32 + 1.18 + 0.9 * ((6.12 - 4.7) / (6.12 - 1.95)) + 0.05 + 0.3 * 0.4
    mat = dk.basis((0, y + 0.05, z), (0, 1, 0))
    shield = [(-0.62, 0.55), (0.62, 0.55), (0.62, -0.05), (0.3, -0.5), (0.0, -0.68), (-0.3, -0.5), (-0.62, -0.05)]
    m.flat("gold", shield, 0.08, mat, back=0.05)
    m.flat("velvet", [(u * 0.8, v * 0.8 + 0.02) for u, v in shield], 0.11, mat, back=0.0)
    m.flat("gold", [(-0.3, -0.12), (0.3, -0.12), (0.34, 0.2), (0.17, 0.06), (0.0, 0.3), (-0.17, 0.06), (-0.34, 0.2)],
           0.14, mat, back=0.0)


def scepter(m):
    x, y = -2.68, -0.88
    m.tube("gold", [(x, y, 0.1), (x, y, 5.5)], lambda t: superellipse(8, 0.075, 0.075, 2.2))
    for z in (0.9, 1.9, 2.9, 4.6)[: Q["grips"]]:
        m.tube("goldD", [(x, y, z), (x, y, z + 0.1)], lambda t: superellipse(Q["trim"] + 2, 0.11, 0.11, 2.2))
    nc = Q["collar"]
    m.rings("gold", [[V((x + r * math.cos(2 * math.pi * i / nc), y + r * math.sin(2 * math.pi * i / nc), z))
                      for i in range(nc)] for r, z in ((0.075, 5.45), (0.18, 5.5), (0.18, 5.6), (0.12, 5.68))])
    m.ball("ruby", (x, y, 5.95), 0.27, n=Q["orb"], rows=Q["orb"] - 4)
    for k in range(Q["cage"]):
        a = math.pi * k / Q["cage"]
        pts = [V((x + 0.31 * math.cos(a) * math.sin(math.pi * i / 6), y + 0.31 * math.sin(a) * math.sin(math.pi * i / 6),
                  5.95 - 0.31 * math.cos(math.pi * i / 6))) for i in range(7)]
        m.tube("gold", pts, lambda t: superellipse(Q["trim"], 0.035, 0.035, 2.2), up=(math.sin(a), -math.cos(a), 0))
    m.ball("gold", (x, y, 6.3), 0.08, n=8, rows=Q["ballr"])
    m.gem("sapphire", (x, y, 6.37), (0, 0, 1), 0.07, up=(0, -1, 0))
    m.ball("gold", (x, y, 0.12), 0.12, n=8, rows=Q["ballr"])


PARTS = ["Head", "Jaw", "Neck", "Torso", "Pelvis", "Cape", "UpperArmL", "UpperArmR", "ForearmL", "ForearmR", "HandL",
         "HandR", "Scepter", "ThighL", "ThighR", "ShinL", "ShinR", "FootL", "FootR", "Tail1", "Tail2", "Tail3", "Tail4",
         "WingArmL", "WingArmR", "WingHandL", "WingHandR"]


def build(quality=None):
    """Все части дракона (Mesh по имени PARTS); quality — HERO (по умолчанию) или GAME."""
    Q.clear()
    Q.update(quality or HERO)
    Mesh.gem_n = Q["gem"]
    P = {n: Mesh(n) for n in PARTS}
    head(P["Head"])
    crown(P["Head"])
    jaw(P["Jaw"])
    big = Matrix.Translation((0, -0.45, 7.75)) @ Matrix.Scale(1.14, 4) @ Matrix.Translation((0, 0.45, -7.75))
    for n in ("Head", "Jaw"):  # крупнее голова — сильнее характер (стилизация Roblox)
        bmesh.ops.transform(P[n].bm, matrix=big, verts=P[n].bm.verts)
    neck(P["Neck"])
    torso(P["Torso"], P["Pelvis"])
    cape(P["Cape"])
    crest(P["Cape"])
    for s, sfx in ((1, "L"), (-1, "R")):
        arm(P["UpperArm" + sfx], P["Forearm" + sfx], P["Hand" + sfx], s)
        leg(P["Thigh" + sfx], P["Shin" + sfx], P["Foot" + sfx], s)
        wing(P["WingArm" + sfx], P["WingHand" + sfx], s)
    scepter(P["Scepter"])
    tail([P["Tail1"], P["Tail2"], P["Tail3"], P["Tail4"]])
    return P
