"""Коллекция босса 3 «Крысиный король» (D54, каталог владельца 2026-11-08), стиль D39.

Новое направление: живые предметы, смешные существа, необычные артефакты и яркие мини-скульптуры — крупные объёмные
формы, выразительные морды, необычный силуэт, узнаваемый без подписи; никаких обычных предметов, просто украшенных
золотом. Большие объекты — миниатюрами: всё помещается на площадку 3.7 × 3.7 стада и в музейную витрину.
30 предметов (12 Common, 10 Rare, 8 Epic, docs/CATALOG.md); сейчас четыре контрольные модели по указанию владельца:
живой сыр-монстр, пицца-крыса, автомат-пожиратель, крысиный трон. Прежний список (обычные вещи метро) —
art_subway.py, его модели сохранены. Общие инструменты (блоки, кольца D39, запекание, рендеры) — art_style.py.

Пишет assets/models/art/<id>.fbx (меш Art_<id>), assets/textures/art/<id>_{color,normal}.png, а в папку превью —
повороты, крупные кадры, общий кадр с манекеном Roblox (5.2 стада) на площадках 3.7 × 3.7, <id>.json для Studio и
report.json. Запуск: blender --background --factory-startup --python scripts/blender/art_rats.py -- <репо> <превью>
[check|quick] [id…]
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, PREVIEWS = os.path.abspath(argv[0]), os.path.abspath(argv[1])
CHECK = "check" in argv[2:]
QUICK = "quick" in argv[2:]  # рендеры без запекания и экспорта (материалы сборки) — для быстрых правок
ONLY = [x for x in argv[2:] if x not in ("check", "quick")]
TEXDIR = os.path.join(REPO, "assets", "textures", "art")
PAD = 3.7  # площадка предмета у босса (подушка 3.7 × 3.7)
PAD_H = 0.12  # толщина площадки в общем кадре (над полом сцены; предметы подняты на неё)
os.makedirs(PREVIEWS, exist_ok=True)
os.makedirs(os.path.join(REPO, "assets", "models", "art"), exist_ok=True)
os.makedirs(TEXDIR, exist_ok=True)


# ── Общие детали ─────────────────────────────────────────────────────────────────────────────────────────────


def tilt(c, axis, deg):
    """Поворот детали вокруг точки c."""
    c = Vector(c)
    return Matrix.Translation(c) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-c)


def ngon(cx, cy, r, n=8, phase=None):
    """Правильный многоугольник (точки в плоскости, поперечной оси призмы)."""
    phase = math.pi / n if phase is None else phase
    return [(cx + r * math.cos(phase + 2 * math.pi * i / n), cy + r * math.sin(phase + 2 * math.pi * i / n))
            for i in range(n)]


def disc(a, key, cx, cy, r, a0, a1, n=8, axis="z", bevel=S.BEVEL, matrix=None):
    """Многогранный «цилиндр» вдоль оси: в плоскости xy для z, xz для y, zy для x."""
    a.prism(key, ngon(cx, cy, r, n), a0, a1, axis=axis, bevel=bevel, matrix=matrix)


def bar(a, key, p0, p1, w, h=None, bevel=S.BEVEL):
    """Брусок от точки p0 до p1 с сечением w × h."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    up = "Y" if abs(d.normalized().z) > 0.95 else "Z"
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("X", up).to_matrix().to_4x4()
    h = h or w
    a.box(key, -d.length / 2, d.length / 2, -w / 2, w / 2, -h / 2, h / 2, bevel=bevel, matrix=m)


def chain(a, key, pts, w0, w1):
    """Ломаная из брусков, толщина плавно от w0 к w1 (хвосты, щупальца); соседние бруски разной толщины."""
    n = len(pts) - 1
    for i in range(n):
        w = w0 + (w1 - w0) * i / max(1, n - 1)
        bar(a, key, pts[i], pts[i + 1], w, w * 0.9)


def gem(a, key, c, size, turn=0.0):
    """Самоцвет: куб на вершине (ромб со всех сторон)."""
    m = Matrix.Translation(c) @ Matrix.Rotation(math.radians(turn), 4, "Z") @ Matrix.Rotation(
        math.radians(45), 4, "X") @ Matrix.Rotation(math.radians(35), 4, "Y")
    h = size / 2
    a.box(key, -h, h, -h, h, -h, h, bevel=0, matrix=m)


def sparkle(a, key, c, size, depth=0.04):
    """Искра-блик: три тонких бруска крестом по x, z и y — «плюс» с любой стороны; у бруска по y сечение тоньше."""
    x, y, z = c
    t = size * 0.18
    a.box(key, x - size / 2, x + size / 2, y - depth / 2, y + depth / 2, z - t / 2, z + t / 2, bevel=0)
    a.box(key, x - t / 2, x + t / 2, y - depth / 2 - 0.005, y + depth / 2 + 0.005, z - size / 2, z + size / 2, bevel=0)
    a.box(key, x - t * 0.42, x + t * 0.42, y - size / 2, y + size / 2, z - t * 0.42, z + t * 0.42, bevel=0)


def pixel_boxes(a, key, rows, cell, x0, ztop, y0, y1, matrix=None):
    """Пиксельный знак на плоской грани (в плоскости x–z, толщина y0…y1) прямоугольниками без общих граней.
    Поворот matrix — только вокруг оси X (иначе проверка граней видит ложные совпадения соседних пикселей)."""
    for c, r, cw, rh in S.greedy_rects([[ch == "#" for ch in row] for row in rows]):
        a.box(key, x0 + c * cell, x0 + (c + cw) * cell, y0, y1, ztop - (r + rh) * cell, ztop - r * cell, bevel=0,
              matrix=matrix)


def eye(a, c, w, h=None, look=(0.0, 0.0), depth=0.3, lid=0.0, lid_key=None, white="white"):
    """Глаз лицом к −y: белок w × h выступает от грани y = c[1] на depth вперёд, зрачок смещён look (−1…1 по x и z),
    блик; lid — веко сверху (доля высоты белка, цветом lid_key) — прищур, самодовольство."""
    x, y, z = c
    h = h or w
    a.box(white, x - w / 2, x + w / 2, y - depth, y + 0.02, z - h / 2, z + h / 2)
    pw = min(w, h) * 0.46
    px, pz = x + look[0] * (w - pw) / 2 * 0.8, z + look[1] * (h - pw) / 2 * 0.8
    a.box("dark", px - pw / 2, px + pw / 2, y - depth - 0.03, y - depth + 0.01, pz - pw / 2, pz + pw / 2, bevel=0)
    g = pw * 0.32
    a.box("glint", px - pw / 2 + 0.02, px - pw / 2 + 0.02 + g, y - depth - 0.045, y - depth - 0.025,
          pz + pw / 2 - 0.02 - g, pz + pw / 2 - 0.02, bevel=0)
    if lid > 0:
        a.box(lid_key, x - w / 2 - 0.03, x + w / 2 + 0.03, y - depth - 0.06, y + 0.02, z + h / 2 - lid * h,
              z + h / 2 + 0.04)


def stand(a, rarity, r=1.45):
    """Круглая подставка-витрина: цвет подсказывает редкость (Common — бирюзовая со светлой каймой, Rare — фиолетовая
    с золотой). Возвращает высоту верха."""
    body, rim = {"common": ("standC", "standCL"), "rare": ("standR", "gold")}[rarity]
    a.paint("standC", "23606B", rings=True)  # бирюза: контраст и с серыми крысами, и с жёлтым сыром
    a.paint("standCL", "5CC2CC")
    a.paint("standR", "6B3FB8", rings=True)
    a.paint("gold", "F2C230", rings=True)
    disc(a, body, 0, 0, r, 0.0, 0.22, n=12)
    a.frame(rim, ngon(0, 0, r + 0.05, 12), 0.1, 0.15, 0.28, axis="z")
    return 0.22


CROWN = ["#..#..#",
         "##.#.##",
         "#######",
         "#######"]


# ══ COMMON ═══════════════════════════════════════════════════════════════════════════════════════════════════

# ── 1. Живой сыр-монстр: огромный клин сыра на крошечных лапках; на высокой грани — морда: выпученные разные глаза,
#       рот с квадратными зубами и языком, рыжие брови; из дырок на боках и на скате выглядывают маленькие глазки ──


def peek_hole(a, axis, c, r, eyes, s=-1):
    """Дырка в сыре (тёмная) на грани с нормалью вдоль оси axis в сторону s; eyes — два крошечных глазка внутри."""
    u, v, w = c  # для axis "x": w — координата x грани, (u, v) = (z, y); для "y": w — y, (u, v) = (x, z)
    a0, a1 = sorted((w + s * 0.012, w - s * 0.02))
    if axis == "x":
        disc(a, "hole", u, v, r, a0, a1, n=8, axis="x", bevel=0)
    else:
        disc(a, "hole", u, v, r, a0, a1, n=8, axis="y", bevel=0)
    if not eyes:
        return
    e = r * 0.34
    for k in (-1, 1):
        if axis == "x":
            z, y = u + r * 0.12, v + k * r * 0.38
            x0, x1 = sorted((w + s * 0.025, w + s * 0.045))
            a.box("white", x0, x1, y - e / 2, y + e / 2, z - e / 2, z + e / 2, bevel=0)
            q0, q1 = sorted((w + s * 0.045, w + s * 0.06))
            a.box("dark", q0, q1, y - e * 0.22, y + e * 0.22, z - e * 0.3, z + e * 0.14, bevel=0)
        else:
            x, z = u + k * r * 0.38, v + r * 0.12
            y0, y1 = sorted((w + s * 0.025, w + s * 0.045))
            a.box("white", x - e / 2, x + e / 2, y0, y1, z - e / 2, z + e / 2, bevel=0)
            q0, q1 = sorted((w + s * 0.045, w + s * 0.06))
            a.box("dark", x - e * 0.22, x + e * 0.22, q0, q1, z - e * 0.3, z + e * 0.14, bevel=0)


def live_cheese_monster():
    a = S.Art("Art_LiveCheeseMonster", ring_z0=0.11)
    for key, code in (("cheese", "F9C93A"), ("rind", "E89A22"), ("hole", "B8700E"), ("mouth", "5A1020"),
                      ("white", "FFFDF4"), ("dark", "1E1E24"), ("tongue", "F06A86"), ("glint", "FFFFFF")):
        a.paint(key, code)
    top = stand(a, "common", 1.42)
    # Лапки: короткие жёлтые ножки с рыжими ступнями, коготки-пальцы спереди.
    zb = 0.66  # низ сыра
    for x in (-0.62, 0.62):
        for y, front in ((-0.25, True), (0.55, False)):
            a.box("cheese", x - 0.13, x + 0.13, y - 0.13, y + 0.13, top + 0.08, zb + 0.02)
            a.box("rind", x - 0.17, x + 0.17, y - 0.2 - (0.1 if front else 0), y + 0.17, top, top + 0.14)
            if front:
                for dx in (-0.09, 0.0, 0.09):
                    a.box("white", x + dx - 0.03, x + dx + 0.03, y - 0.36, y - 0.3, top + 0.02, top + 0.08, bevel=0)
    # Клин: высокая грань — лицо (−y), скат уходит назад; корка снизу.
    yf, yb, zt = -0.55, 0.95, 2.42
    a.box("rind", -1.13, 1.13, yf - 0.05, yb + 0.05, zb - 0.08, zb + 0.04)
    a.prism("cheese", [(zb, yf), (zb, yb), (zt, yf)], -1.1, 1.1, axis="x")
    # Морда: выпученные глаза разного размера (косят), брови-корка, рот с квадратными зубами и языком.
    eye(a, (-0.46, yf, 1.9), 0.74, 0.7, look=(0.5, -0.4), depth=0.36)
    eye(a, (0.5, yf, 1.98), 0.58, 0.6, look=(-0.6, 0.3), depth=0.3)
    bar(a, "rind", (-0.86, yf - 0.2, 2.34), (-0.14, yf - 0.2, 2.24), 0.14, 0.12)
    bar(a, "rind", (0.2, yf - 0.18, 2.36), (0.82, yf - 0.18, 2.4), 0.13, 0.11)
    a.box("mouth", -0.78, 0.78, yf - 0.05, yf + 0.02, 0.92, 1.42, bevel=0)
    for i, x in enumerate((-0.6, -0.3, 0.0, 0.3, 0.6)):
        a.box("white", x - 0.12, x + 0.12, yf - 0.1, yf - 0.03, 1.26 - (0.04 if i % 2 else 0), 1.44, bevel=0)
    for x in (-0.45, -0.15, 0.15, 0.45):
        a.box("white", x - 0.12, x + 0.12, yf - 0.1, yf - 0.03, 0.9, 1.04 + (0.03 if x > 0 else 0), bevel=0)
    a.box("tongue", -0.22, 0.22, yf - 0.32, yf - 0.02, 0.84, 0.98)
    # Ручки-лапки по бокам машут.
    for s in (-1, 1):
        bar(a, "cheese", (s * 1.05, -0.15, 1.25), (s * 1.42, -0.35, 1.62), 0.16, 0.15)
        a.box("rind", s * 1.42 - 0.12, s * 1.42 + 0.12, -0.47, -0.23, 1.6, 1.8)
    # Дырки: на боках (часть с глазками), на скате и на лице.
    for s in (-1, 1):
        x = s * 1.1
        for y, z, r, eyes in ((-0.1, 1.2, 0.22, True), (0.42, 0.88, 0.15, False), (-0.33, 1.86, 0.14, s < 0)):
            peek_hole(a, "x", (z, y, x), r, eyes, s)
    n = Vector((0, zt - zb, yb - yf)).normalized()  # нормаль ската
    for x, t, r, eyes in ((-0.5, 0.42, 0.2, True), (0.45, 0.62, 0.16, False), (0.15, 0.3, 0.11, False),
                          (-0.2, 0.78, 0.13, True)):
        p = Vector((x, yf + (yb - yf) * t, zt - (zt - zb) * t))
        m = Matrix.Translation(p) @ n.to_track_quat("Z", "Y").to_matrix().to_4x4()
        disc(a, "hole", 0, 0, r, -0.012, 0.02, n=8, bevel=0, matrix=m)
        if eyes:
            e = r * 0.34
            for k in (-1, 1):
                a.box("white", k * r * 0.38 - e / 2, k * r * 0.38 + e / 2, -e / 2, e / 2, 0.02, 0.04, bevel=0,
                      matrix=m)
                a.box("dark", k * r * 0.38 - e * 0.22, k * r * 0.38 + e * 0.22, -e * 0.3, e * 0.14, 0.04, 0.055,
                      bevel=0, matrix=m)
    peek_hole(a, "y", (0.88, 0.8, yf), 0.1, False)
    sparkle(a, "glint", (-1.25, -0.6, 2.55), 0.28)
    return a


# ── 2. Пицца-крыса: крыса застряла под сыром гигантского куска пиццы — горб под сыром, спереди торчит мордочка с
#       лапками (на голове капля сыра), сзади — длинный розовый хвост завитком; пепперони, оливки, базилик ─────────


def pizza_rat():
    a = S.Art("Art_PizzaRat", ring_z0=0.3)
    a.paint("cheese", "FFC93C", rings=True)
    for key, code in (("dough", "E8B86A"), ("crust", "C77A2E"), ("crustL", "E09A48"), ("pep", "D7262E"),
                      ("pepD", "A11E24"), ("olive", "2B2B33"), ("basil", "3DBA4E"), ("fur", "8790B0"),
                      ("furL", "A8AFCB"), ("pink", "F49AB0"), ("pinkD", "E07A94"), ("white", "FFFDF4"),
                      ("dark", "1E1E24"), ("glint", "FFFFFF")):
        a.paint(key, code)
    top = stand(a, "common", 1.6)
    z0 = top + 0.02
    # Кусок крупнее (×1.12, остриё за краем подставки) и наклонён задним краем вверх — начинка смотрит на зрителя.
    slice_m = (tilt((0, -0.7, z0), "X", 10) @ Matrix.Translation((0, 0, z0)) @ Matrix.Scale(1.12, 4)
               @ Matrix.Translation((0, 0, -z0)))
    a.transform = slice_m
    # Кусок: остриё влево, бортик справа; тесто, сыр, горб под сыром — там крыса.
    tip, c0, c1 = (-1.62, 0.0), (1.22, -1.18), (1.22, 1.18)
    a.prism("dough", [tip, c0, c1], z0, z0 + 0.2)
    a.prism("cheese", [(tip[0] + 0.2, 0.0), (c0[0] - 0.05, c0[1] + 0.12), (c1[0] - 0.05, c1[1] - 0.12)], z0 + 0.18,
            z0 + 0.3)
    a.box("crust", 1.0, 1.42, -1.22, 1.22, z0 - 0.01, z0 + 0.42)
    a.box("crustL", 1.06, 1.36, -1.14, 1.14, z0 + 0.4, z0 + 0.5)
    hz = z0 + 0.27  # низ горба внутри сыра, не в плоскости пепперони
    a.frustum("cheese", (-0.5, 0.8, -0.5, 0.48), (-0.3, 0.56, -0.32, 0.32), hz, hz + 0.5)
    a.frustum("cheese", (-0.3, 0.56, -0.32, 0.32), (-0.12, 0.34, -0.18, 0.16), hz + 0.48, hz + 0.72)
    # Начинка.
    zt = z0 + 0.28
    for x, y in ((-0.98, 0.05), (0.8, -0.6), (0.7, 0.55), (0.0, 0.62)):
        disc(a, "pep", x, y, 0.2, zt, zt + 0.07, n=8, bevel=0)
        disc(a, "pepD", x + 0.04, y + 0.04, 0.07, zt + 0.06, zt + 0.09, n=8, bevel=0)
    disc(a, "pep", 0.11, -0.01, 0.14, hz + 0.7, hz + 0.77, n=8, bevel=0)
    for x, y in ((0.25, -0.75), (-0.6, 0.25), (0.88, 0.1)):
        a.frame("olive", ngon(x, y, 0.1, 8), 0.04, zt + 0.01, zt + 0.08, axis="z")
    for x, y, ang in ((0.4, 0.75, 30), (-1.15, -0.0, 0)):
        a.box("basil", x - 0.14, x + 0.14, y - 0.06, y + 0.06, zt + 0.005, zt + 0.055, bevel=0,
              matrix=tilt((x, y, 0), "Z", ang))
    # Мордочка крысы торчит из-под сыра у переднего края (−y), крупно (масштаб 1.4 от центра головы): голова, морда-
    # клин, розовый нос, уши, удивлённые глаза, резцы, усы, сыр на макушке и капля; лапки держатся за край теста.
    a.transform = None
    hx, hy, hzc = -0.15, -0.92, z0 + 0.46
    a.transform = Matrix.Translation((hx, hy, hzc)) @ Matrix.Scale(1.3, 4)
    a.box("fur", -0.34, 0.34, -0.2, 0.36, -0.26, 0.3)
    a.frustum("furL", (-0.24, 0.24, -0.22, 0.06), (-0.08, 0.08, -0.14, -0.02), -0.2, -0.6, axis="y")
    a.box("pink", -0.08, 0.08, -0.68, -0.56, -0.14, -0.02)
    for s_ in (-1, 1):
        disc(a, "fur", s_ * 0.34, 0.36, 0.22, -0.02, 0.08, n=8, axis="y")
        disc(a, "pink", s_ * 0.34, 0.36, 0.14, -0.05, -0.01, n=8, axis="y", bevel=0)
        eye(a, (s_ * 0.16, -0.2, 0.16), 0.2, 0.24, look=(-s_ * 0.1, 0.6), depth=0.1)
        bar(a, "dark", (s_ * 0.12, -0.48, -0.08), (s_ * 0.5, -0.6, -0.03), 0.022)
        bar(a, "dark", (s_ * 0.12, -0.48, -0.12), (s_ * 0.48, -0.58, -0.19), 0.02)
    a.box("white", -0.07, 0.07, -0.6, -0.54, -0.26, -0.14, bevel=0)
    a.box("cheese", -0.3, 0.26, -0.08, 0.3, 0.28, 0.36)
    a.box("cheese", 0.27, 0.33, -0.24, -0.16, -0.05, 0.32, bevel=0)
    a.transform = None
    for s_ in (-1, 1):  # лапки на краю теста
        a.box("pink", hx + s_ * 0.56 - 0.12, hx + s_ * 0.56 + 0.12, hy - 0.36, hy - 0.02, z0 + 0.14, z0 + 0.28)
        for dx in (-0.07, 0.0, 0.07):
            a.box("white", hx + s_ * 0.56 + dx - 0.02, hx + s_ * 0.56 + dx + 0.02, hy - 0.42, hy - 0.36, z0 + 0.15,
                  z0 + 0.2, bevel=0)
    # Хвост: из-под заднего края, длинный, завитком вверх (наклонён вместе с куском).
    a.transform = slice_m
    chain(a, "pink", [(0.25, 0.62, z0 + 0.22), (0.35, 1.2, z0 + 0.28), (0.25, 1.52, z0 + 0.62), (0.0, 1.52, 1.12),
                      (-0.25, 1.32, 1.3), (-0.38, 1.12, 1.18)], 0.16, 0.08)
    a.transform = None
    sparkle(a, "glint", (-1.5, -0.8, 1.45), 0.26)
    return a


# ══ RARE ═════════════════════════════════════════════════════════════════════════════════════════════════════

# ── 13. Автомат-пожиратель: красный торговый автомат на ножках с огромной зубастой пастью и языком с монетами;
#        за стеклом вместо товаров — его злые глаза, сыр, глазик и стопки украденных монет; вывеска «НЯМ!» ─────────

FONT5 = {"Н": ["#..#", "#..#", "####", "#..#", "#..#"],
         "Я": [".###", "#..#", ".###", ".#.#", "#..#"],
         "М": ["#...#", "##.##", "#.#.#", "#...#", "#...#"],
         "!": ["#", "#", "#", ".", "#"]}


def word5(word):
    rows = [""] * 5
    for i, ch in enumerate(word):
        for r in range(5):
            rows[r] += ("." if i else "") + FONT5[ch][r]
    return rows


def devourer_vending():
    a = S.Art("Art_DevourerVending", ring_z0=1.6)
    a.paint("red", "D62D3A", rings=True)
    for key, code in (("redD", "A11E2B"), ("sign", "FFD23F"), ("glass", "2A1F4D"), ("chrome", "C3CAD4"),
                      ("panel", "3A3F4B"), ("mouth", "4A0E18"), ("tongue", "E94F6F"), ("white", "FFFDF4"),
                      ("dark", "1E1E24"), ("goldL", "FFE07A"), ("gold2", "C9921A"), ("cheese", "F9C93A"),
                      ("hole", "B8700E"), ("green", "2ECC71"), ("glint", "FFFFFF")):
        a.paint(key, code)
    top = stand(a, "rare", 1.55)
    # Ножки, корпус, крышка, золотые уголки спереди.
    for x in (-0.7, 0.7):
        for y in (-0.4, 0.4):
            a.box("dark", x - 0.16, x + 0.16, y - 0.16, y + 0.16, top - 0.02, 0.44)
    a.box("red", -0.95, 0.95, -0.6, 0.6, 0.42, 3.75)
    a.box("redD", -1.0, 1.0, -0.66, 0.66, 3.7, 3.9)
    for s in (-1, 1):
        x0, x1 = sorted((s * 0.9, s * 1.0))
        a.box("gold", x0, x1, -0.65, -0.55, 0.44, 3.72)
    # Вывеска «НЯМ!».
    a.box("sign", -0.9, 0.9, -0.7, -0.62, 3.36, 3.7)
    pixel_boxes(a, "red", word5("НЯМ!"), 0.055, -0.4675, 3.67, -0.73, -0.69)
    # Окно: хромовая рамка, тёмное стекло, золотые полки.
    a.frame("chrome", S.octagon(-0.88, 0.48, 1.89, 3.31, 0.14), 0.08, -0.69, -0.6, axis="y")
    a.box("glass", -0.82, 0.42, -0.64, -0.58, 1.95, 3.25, bevel=0)
    for z in (2.36, 2.8):
        a.box("gold", -0.8, 0.4, -0.8, -0.62, z - 0.035, z + 0.02)
    # Верхняя полка — его глаза, злые брови над окном.
    eye(a, (-0.46, -0.64, 3.03), 0.44, 0.38, look=(0.5, -0.4), depth=0.24)
    eye(a, (0.1, -0.64, 3.03), 0.44, 0.38, look=(-0.4, -0.4), depth=0.24)
    bar(a, "dark", (-0.78, -0.76, 3.34), (-0.22, -0.76, 3.22), 0.1, 0.11)
    bar(a, "dark", (0.42, -0.76, 3.34), (-0.14, -0.76, 3.22), 0.11, 0.1)
    # Средняя полка — сыр (треугольники с дырками) и маленький глаз.
    for x0 in (-0.78, -0.36):
        a.prism("cheese", [(x0, 2.39), (x0 + 0.34, 2.39), (x0, 2.71)], -0.76, -0.64, axis="y")
        a.box("hole", x0 + 0.06, x0 + 0.12, -0.775, -0.755, 2.45, 2.51, bevel=0)
    eye(a, (0.22, -0.64, 2.56), 0.24, 0.26, look=(-0.6, 0.1), depth=0.14)
    # Нижняя полка — стопки украденных монет.
    for x, n in ((-0.6, 3), (-0.3, 5), (0.0, 2), (0.27, 4)):
        for i in range(n):
            disc(a, "goldL" if i % 2 else "gold", x, -0.71, 0.12, 2.0 + i * 0.065, 2.06 + i * 0.065, n=8,
                 bevel=0)
    # Пульт справа: щель для монет, кнопки, красная кнопка, зелёный экранчик.
    a.box("panel", 0.52, 0.88, -0.64, -0.58, 1.95, 3.25, bevel=0)
    a.box("gold", 0.62, 0.78, -0.67, -0.63, 2.95, 3.12, bevel=0)
    a.box("dark", 0.68, 0.72, -0.69, -0.66, 2.98, 3.09, bevel=0)
    a.box("green", 0.58, 0.82, -0.67, -0.63, 2.72, 2.86, bevel=0)
    for i in range(3):
        for j in range(3):
            x, z = 0.6 + j * 0.1, 2.36 + i * 0.1
            a.box("white", x - 0.035, x + 0.035, -0.67, -0.63, z - 0.035, z + 0.035, bevel=0)
    a.box("red", 0.62, 0.78, -0.69, -0.63, 2.04, 2.2)
    # Пасть: тёмная, острые зубы сверху и снизу (один золотой), язык свисает вперёд, на нём монеты.
    a.box("mouth", -0.85, 0.85, -0.64, -0.58, 0.72, 1.78, bevel=0)
    for i, x in enumerate((-0.72, -0.48, -0.24, 0.0, 0.24, 0.48, 0.72)):
        a.frustum("gold" if i == 5 else "white", (x - 0.11, x + 0.11, -0.72, -0.6), (x, x, -0.66, -0.66), 1.76,
                  1.42 - 0.04 * (i % 2), bevel=0)
    for x in (-0.6, -0.36, 0.36, 0.6):
        a.frustum("white", (x - 0.11, x + 0.11, -0.72, -0.6), (x, x, -0.66, -0.66), 0.74, 1.04, bevel=0)
    tm = tilt((0, -0.6, 0.86), "X", 14)
    a.box("tongue", -0.36, 0.36, -1.3, -0.56, 0.8, 0.94, matrix=tm)
    for x, y in ((-0.12, -1.0), (0.14, -1.18)):
        disc(a, "goldL", x, y, 0.1, 0.93, 0.97, n=8, bevel=0, matrix=tm)
    # Рассыпанные монеты на подставке.
    for x, y, i in ((-1.1, -0.8, 0), (-0.95, -1.05, 1), (1.05, -0.95, 2)):
        disc(a, "gold" if i % 2 else "goldL", x, y, 0.13, top, top + 0.05, n=8, bevel=0)
    sparkle(a, "glint", (-1.35, -0.5, 3.6), 0.3)
    return a


# ══ EPIC ═════════════════════════════════════════════════════════════════════════════════════════════════════

# ── 23. Крысиный трон: толстый самодовольный король (прищур, ухмылка, корона набекрень, кубок в лапе) на огромном
#        золотом троне из украденных монет (столбики монет, гора монет), скипетров (боковые стойки) и сыра
#        (подлокотники-клинья); бархатные подушки, гребень с рубином ────────────────────────────────────────────


def rat_throne():
    a = S.Art("Art_RatThrone", ring_z0=1.7)
    a.paint("gold", "F2C230", rings=True)
    a.paint("fur", "8790B0", rings=True)
    a.paint("velvet", "C2263A", rings=True)
    for key, code in (("gold2", "C9921A"), ("goldL", "FFE07A"), ("cheese", "F9C93A"), ("hole", "B8700E"),
                      ("furL", "A8AFCB"), ("cream", "C9B9A0"), ("pink", "F49AB0"), ("cape", "D8352A"),
                      ("ermine", "F7F4EE"), ("purple", "6B3FB8"), ("ruby", "E53935"), ("sapph", "2F7DE1"),
                      ("emer", "2E9E4F"), ("white", "FFFDF4"), ("dark", "1E1E24"), ("glint", "FFFFFF")):
        a.paint(key, code)
    # Гора монет ступенями, монеты и кусочек сыра по краям.
    a.prism("gold2", S.octagon(-1.78, 1.78, -1.78, 1.78, 0.52), 0.0, 0.16)
    a.prism("gold", S.octagon(-1.6, 1.6, -1.6, 1.6, 0.46), 0.14, 0.34)
    for x, y, ang, key in ((-1.45, -1.0, 20, "goldL"), (1.35, -1.15, -30, "gold2"), (0.95, -1.42, 45, "goldL")):
        disc(a, key, x, y, 0.15, 0.3, 0.37, n=6, bevel=0, matrix=tilt((x, y, 0.33), "Y", ang * 0.3))
    a.prism("cheese", [(-1.62, -1.25), (-1.05, -1.38), (-1.3, -1.0)], 0.32, 0.6)
    # Сиденье: золотой блок, спереди столбики монет, красная подушка; подножка-подушка для лап.
    a.box("gold", -0.95, 0.95, -0.55, 0.75, 0.32, 1.0)
    for x in (-0.66, -0.22, 0.22, 0.66):  # столбики по три толстые монеты (бюджет треугольников)
        for i in range(3):
            disc(a, "goldL" if i % 2 else "gold", x, -0.62, 0.16, 0.34 + i * 0.213, 0.54 + i * 0.213, n=6, bevel=0)
    a.box("velvet", -0.86, 0.86, -0.5, 0.7, 0.98, 1.14)
    a.box("velvet", -0.62, 0.62, -1.08, -0.6, 0.32, 0.5, bevel=0)
    # Подлокотники — клинья сыра с дырками на столбиках монет.
    for s in (-1, 1):
        x0, x1 = sorted((s * 0.95, s * 1.42))
        a.prism("cheese", [(1.0, -0.6), (1.0, 0.75), (1.62, 0.75)], x0, x1, axis="x")
        for y in (-0.4, 0.55):
            for i in range(3):
                disc(a, "goldL" if i % 2 else "gold", s * 1.18, y, 0.15, 0.34 + i * 0.217, 0.54 + i * 0.217, n=6,
                     bevel=0)
        hx0, hx1 = sorted((s * 1.42, s * 1.45))
        for y, z, r in ((0.2, 1.18, 0.1), (0.5, 1.38, 0.08)):
            disc(a, "hole", z, y, r, hx0, hx1, n=8, axis="x", bevel=0)
    # Спинка ниже короны короля: золотая плита, красная стёганая подушка с золотыми пуговицами, зубцы гребня
    # только по краям — посередине корона короля видна на фоне неба.
    a.box("gold", -0.95, 0.95, 0.62, 0.92, 1.0, 2.62)
    a.box("velvet", -0.76, 0.76, 0.54, 0.64, 1.16, 2.46)
    for x in (-0.4, 0.0, 0.4):
        for z in (1.7, 2.25):
            a.box("goldL", x - 0.05, x + 0.05, 0.51, 0.55, z - 0.05, z + 0.05, bevel=0)
    for x, tip in ((-0.78, 3.05), (-0.48, 2.9), (0.48, 2.9), (0.78, 3.05)):
        a.frustum("gold", (x - 0.15, x + 0.15, 0.66, 0.88), (x, x, 0.77, 0.77), 2.6, tip, bevel=0)
        a.box("goldL", x - 0.06, x + 0.06, 0.71, 0.83, tip - 0.06, tip + 0.06, bevel=0)
    # Боковые стойки — скипетры с камнями на навершиях; сзади два скипетра крест-накрест.
    for s, key in ((-1, "sapph"), (1, "emer")):
        x = s * 1.03
        a.box("gold2", x - 0.07, x + 0.07, 0.7, 0.84, 0.36, 3.3, bevel=0)
        disc(a, "goldL", x, 0.77, 0.15, 3.26, 3.42, n=8, bevel=0)
        gem(a, key, (x, 0.77, 3.56), 0.24)
    for s in (-1, 1):
        bar(a, "gold2", (s * 0.85, 1.0, 1.2), (-s * 0.85, 1.0, 2.8), 0.1 + 0.01 * (s > 0))
        gem(a, "ruby", (-s * 0.9, 1.0, 2.9), 0.18)
    # Король: ноги на подушке, толстое тело, брюшко, пояс, плащ с горностаем.
    for s in (-1, 1):
        x0, x1 = sorted((s * 0.12, s * 0.48))
        a.box("fur", x0, x1, -0.55, 0.2, 1.1, 1.44)
        a.box("fur", s * 0.3 - 0.15, s * 0.3 + 0.15, -0.72, -0.44, 0.6, 1.2, bevel=0)
        a.box("pink", s * 0.3 - 0.19, s * 0.3 + 0.19, -0.98, -0.48, 0.48, 0.64, bevel=0)
    disc(a, "fur", 0, 0.05, 0.64, 1.12, 1.78, n=8)
    disc(a, "fur", 0, 0.05, 0.55, 1.74, 2.28, n=8)
    disc(a, "cream", 0, 1.52, 0.44, -0.62, -0.5, n=8, axis="y", bevel=0)  # брюшко светлее шерсти
    a.frame("gold", ngon(0, 0.05, 0.7, 8), 0.08, 1.46, 1.56, axis="z", bevel=0)
    a.box("cape", -0.74, 0.74, 0.32, 0.56, 1.2, 2.36)
    a.frame("ermine", ngon(0, 0.05, 0.62, 8), 0.2, 2.22, 2.4, axis="z", bevel=0)
    for ang in range(0, 360, 60):
        r = math.radians(ang + 30)
        x, y = 0.52 * math.cos(r), 0.05 + 0.52 * math.sin(r)
        a.box("dark", x - 0.03, x + 0.03, y - 0.03, y + 0.03, 2.39, 2.42, bevel=0)
    # Лапы: левая на подлокотнике, правая держит золотой кубок.
    bar(a, "fur", (-0.55, 0.0, 2.12), (-1.0, -0.1, 1.72), 0.2, 0.22)
    bar(a, "fur", (-1.0, -0.1, 1.72), (-1.02, -0.45, 1.68), 0.18, 0.2)
    a.box("pink", -1.14, -0.9, -0.62, -0.38, 1.6, 1.76, bevel=0)
    bar(a, "fur", (0.55, 0.0, 2.12), (0.92, -0.2, 1.82), 0.2, 0.22)
    bar(a, "fur", (0.92, -0.2, 1.82), (0.86, -0.52, 2.12), 0.18, 0.2)
    a.box("pink", 0.76, 0.98, -0.64, -0.42, 2.04, 2.22, bevel=0)
    a.frustum("gold", (0.8, 1.04, -0.66, -0.42), (0.74, 1.1, -0.72, -0.36), 2.22, 2.5)
    a.box("purple", 0.79, 1.05, -0.67, -0.41, 2.46, 2.5, bevel=0)
    disc(a, "gold2", 0.92, -0.54, 0.06, 2.12, 2.24, n=8, bevel=0)
    # Голова: череп, пухлые щёки, морда, нос, резцы, ухмылка, усы, прищур с тяжёлыми веками, уши, корона набекрень.
    a.box("fur", -0.42, 0.42, -0.42, 0.32, 2.3, 2.92)
    a.box("furL", -0.47, 0.47, -0.4, 0.0, 2.28, 2.56)
    a.frustum("cream", (-0.28, 0.28, 2.3, 2.6), (-0.1, 0.1, 2.36, 2.48), -0.42, -0.88, axis="y")
    a.box("pink", -0.08, 0.08, -0.96, -0.84, 2.36, 2.5, bevel=0)
    a.box("white", -0.07, 0.07, -0.8, -0.74, 2.2, 2.33, bevel=0)
    bar(a, "dark", (-0.22, -0.72, 2.31), (0.2, -0.69, 2.37), 0.04, bevel=0)
    for s in (-1, 1):
        for dz, dy in ((0.0, 0.0), (-0.06, 0.02)):
            bar(a, "dark", (s * 0.18, -0.76 + dy, 2.42 + dz), (s * 0.62, -0.86 + dy, 2.48 + dz * 2), 0.022, bevel=0)
        eye(a, (s * 0.2, -0.42, 2.72), 0.26, 0.2, look=(-0.4, -0.3), depth=0.08, lid=0.52, lid_key="fur")
        disc(a, "fur", s * 0.42, 3.02, 0.28, -0.06, 0.04, n=8, axis="y", bevel=0)
        disc(a, "pink", s * 0.42, 3.02, 0.18, -0.09, -0.05, n=8, axis="y", bevel=0)
    cm = tilt((0, -0.05, 2.9), "Y", 10)
    a.frame("gold", ngon(0, -0.05, 0.34, 8), 0.08, 2.88, 3.1, axis="z", bevel=0, matrix=cm)
    a.prism("purple", ngon(0, -0.05, 0.27, 8), 2.9, 3.16, bevel=0, matrix=cm)
    for i in range(0, 8, 2):
        ang = math.pi / 8 + i * math.pi / 4
        px, py = 0.3 * math.cos(ang), -0.05 + 0.3 * math.sin(ang)
        a.frustum("gold", (px - 0.06, px + 0.06, py - 0.06, py + 0.06), (px, px, py, py), 3.08, 3.32, bevel=0,
                  matrix=cm)
        a.box("goldL", px - 0.045, px + 0.045, py - 0.045, py + 0.045, 3.28, 3.37, bevel=0, matrix=cm)
    gem(a, "ruby", tuple(cm @ Vector((0, -0.4, 2.99))), 0.13)
    # Хвост: из-за трона вправо и вниз на монеты.
    chain(a, "pink", [(0.6, 0.72, 1.1), (1.1, 1.0, 0.85), (1.52, 0.72, 0.6), (1.58, 0.2, 0.45), (1.38, -0.2, 0.42),
                      (1.12, -0.28, 0.46)], 0.15, 0.08)
    sparkle(a, "glint", (-1.45, -0.6, 3.3), 0.3)
    sparkle(a, "glint", (1.4, -0.5, 2.9), 0.22)
    return a


# ══ Сборка, запекание, экспорт, проверочные рендеры ════════════════════════════════════════════════════════

COMMON = [("LiveCheeseMonster", live_cheese_monster), ("PizzaRat", pizza_rat)]
RARE = [("DevourerVending", devourer_vending)]
EPIC = [("RatThrone", rat_throne)]
GROUPS = {"common": COMMON, "rare": RARE, "epic": EPIC}
ITEMS = [(i, f, g) for g, items in GROUPS.items() for i, f in items if not ONLY or i in ONLY]


def pad(collection, x):
    """Площадка 3.7 × 3.7 под предметом в общем кадре (тёмно-красная, как подушка у босса), над полом сцены."""
    mat = bpy.data.materials.get("PadMat")
    if mat is None:
        mat = bpy.data.materials.new("PadMat")
        mat.use_nodes = True
        next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (
            *S.lin("8E1F2C"), 1)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(PAD, PAD, PAD_H), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(x, 0, PAD_H / 2), verts=bm.verts)
    me = bpy.data.meshes.new("Pad")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    collection.objects.link(bpy.data.objects.new("Pad", me))


bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new("Rats")
bpy.context.scene.collection.children.link(collection)

if CHECK:
    for item_id, make, _ in ITEMS:
        art = make()
        art.build(collection)
        print("CHECK", item_id, json.dumps(art.stats, ensure_ascii=False))
    sys.exit(0)

report, objs = {}, []
for item_id, make, group in ITEMS:
    art = make()
    obj = art.build(collection)
    uv = {} if QUICK else S.bake(obj, art, TEXDIR, item_id)
    lo, hi = S.bounds(obj)
    report[item_id] = {**art.stats, **{k: round(v, 3) for k, v in uv.items()},
                       "size": [round(hi[i] - lo[i], 2) for i in range(3)]}
    if not QUICK:
        S.studio_json(obj, os.path.join(PREVIEWS, f"{item_id}.json"))
        S.export_fbx([obj], os.path.join(REPO, "assets", "models", "art", f"{item_id}.fbx"))
    objs.append((obj, group))
    print("ITEM_OK", item_id, report[item_id]["tris"], flush=True)

prev = S.Preview(collection)
heroes = [S.render_item(prev, obj, PREVIEWS) for obj, _ in objs]
S.strip(heroes, os.path.join(PREVIEWS, "sheet.png"), gap=12)

# Общий кадр: предметы в ряд, каждый на площадке 3.7 × 3.7, и манекен Roblox (5.2 стада) — масштаб.
x = PAD / 2
for obj, _ in objs:
    lo, hi = S.bounds(obj)
    obj.location.x = x - (lo.x + hi.x) / 2
    obj.location.z = PAD_H
    pad(collection, x)
    x += PAD + 0.6
S.mannequin(collection, x)
right = x + 2.0  # правый край манекена (руки ±2)
center = Vector((right / 2, 0, 2.4))
prev.aim_lights(center)
dist = (right + 1.6) / 2 / 0.36  # объектив 50 мм на кадре 36 мм: половина ширины кадра = 0.36 расстояния
prev.shot(os.path.join(PREVIEWS, "group_scale.png"), (center.x, -dist, 5.5), (center.x, 0, 2.3), 50, (2000, 900))
for obj, _ in objs:
    obj.location.x = obj.location.z = 0

with open(os.path.join(PREVIEWS, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("RATS_OK " + json.dumps({k: v["tris"] for k, v in report.items()}, ensure_ascii=False))
