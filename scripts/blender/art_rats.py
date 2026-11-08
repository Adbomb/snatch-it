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


def part(a, name, parent, pivot):
    """Следующие детали — подвижная часть name: родитель parent (None — корень), точка вращения pivot (координаты
    модели). Скелет нужен для будущих анимаций живых предметов (D55); у каждой модели один корень — подставка."""
    if not hasattr(a, "rig"):
        a.rig, a.pose = {}, {}
    a.rig[name] = (parent, tuple(pivot))
    a.group = name


def stand(a, rarity, r=1.45):
    """Круглая подставка-витрина: цвет подсказывает редкость (Common — бирюзовая со светлой каймой, Rare — фиолетовая
    с золотой). Возвращает высоту верха."""
    part(a, "Stand", None, (0, 0, 0))
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
    sparkle(a, "glint", (-1.25, -0.6, 2.55), 0.28)
    # Лапки: короткие жёлтые ножки с рыжими ступнями, коготки-пальцы спереди.
    zb = 0.66  # низ сыра
    for x in (-0.62, 0.62):
        for y, front in ((-0.25, True), (0.55, False)):
            part(a, "Leg" + ("F" if front else "B") + ("L" if x < 0 else "R"), "Body", (x, y, zb))
            a.box("cheese", x - 0.13, x + 0.13, y - 0.13, y + 0.13, top + 0.08, zb + 0.02)
            a.box("rind", x - 0.17, x + 0.17, y - 0.2 - (0.1 if front else 0), y + 0.17, top, top + 0.14)
            if front:
                for dx in (-0.09, 0.0, 0.09):
                    a.box("white", x + dx - 0.03, x + dx + 0.03, y - 0.36, y - 0.3, top + 0.02, top + 0.08, bevel=0)
    # Клин: высокая грань — лицо (−y), скат уходит назад; корка снизу.
    yf, yb, zt = -0.55, 0.95, 2.42
    part(a, "Body", "Stand", (0, 0.2, top))
    a.box("rind", -1.13, 1.13, yf - 0.05, yb + 0.05, zb - 0.08, zb + 0.04)
    a.prism("cheese", [(zb, yf), (zb, yb), (zt, yf)], -1.1, 1.1, axis="x")
    # Морда: выпученные глаза разного размера (косят), брови-корка, рот с квадратными зубами и языком.
    part(a, "EyeL", "Body", (-0.46, yf - 0.17, 1.9))
    eye(a, (-0.46, yf, 1.9), 0.74, 0.7, look=(0.5, -0.4), depth=0.36)
    part(a, "EyeR", "Body", (0.5, yf - 0.14, 1.98))
    eye(a, (0.5, yf, 1.98), 0.58, 0.6, look=(-0.6, 0.3), depth=0.3)
    part(a, "Body", "Stand", (0, 0.2, top))
    bar(a, "rind", (-0.86, yf - 0.2, 2.34), (-0.14, yf - 0.2, 2.24), 0.14, 0.12)
    bar(a, "rind", (0.2, yf - 0.18, 2.36), (0.82, yf - 0.18, 2.4), 0.13, 0.11)
    a.box("mouth", -0.78, 0.78, yf - 0.05, yf + 0.02, 0.92, 1.42, bevel=0)
    for i, x in enumerate((-0.6, -0.3, 0.0, 0.3, 0.6)):
        a.box("white", x - 0.12, x + 0.12, yf - 0.1, yf - 0.03, 1.26 - (0.04 if i % 2 else 0), 1.44, bevel=0)
    part(a, "Jaw", "Body", (0, yf + 0.5, 0.98))  # нижние зубы и язык; шарнир сзади на их высоте — рот открывается вниз
    for x in (-0.45, -0.15, 0.15, 0.45):
        a.box("white", x - 0.12, x + 0.12, yf - 0.1, yf - 0.03, 0.9, 1.04 + (0.03 if x > 0 else 0), bevel=0)
    a.box("tongue", -0.22, 0.22, yf - 0.32, yf - 0.02, 0.84, 0.98)
    # Ручки-лапки по бокам машут.
    for s in (-1, 1):
        part(a, "ArmL" if s < 0 else "ArmR", "Body", (s * 1.05, -0.15, 1.25))
        bar(a, "cheese", (s * 1.05, -0.15, 1.25), (s * 1.42, -0.35, 1.62), 0.16, 0.15)
        a.box("rind", s * 1.42 - 0.12, s * 1.42 + 0.12, -0.47, -0.23, 1.6, 1.8)
    # Дырки: на боках (часть с глазками), на скате и на лице.
    part(a, "Body", "Stand", (0, 0.2, top))
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
    a.pose = {"EyeL": ((0, 0, 18), (0, 0, 0)), "EyeR": ((0, 0, -22), (0, 0, 0)), "Jaw": ((24, 0, 0), (0, 0, 0)),
              "ArmL": ((0, 35, 0), (0, 0, 0)), "ArmR": ((0, -20, 0), (0, 0, 0)), "LegFL": ((-25, 0, 0), (0, 0, 0)),
              "LegBR": ((20, 0, 0), (0, 0, 0))}
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
    sparkle(a, "glint", (-1.5, -0.8, 1.45), 0.26)
    z0 = top + 0.02
    # Кусок крупнее (×1.12, остриё за краем подставки) и наклонён задним краем вверх — начинка смотрит на зрителя.
    slice_m = (tilt((0, -0.7, z0), "X", 10) @ Matrix.Translation((0, 0, z0)) @ Matrix.Scale(1.12, 4)
               @ Matrix.Translation((0, 0, -z0)))
    a.transform = slice_m
    part(a, "Pizza", "Stand", (0, 0, z0))
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
    k = 1.3
    a.transform = Matrix.Translation((hx, hy, hzc)) @ Matrix.Scale(k, 4)
    part(a, "Head", "Pizza", (hx, hy + 0.3 * k, hzc - 0.1 * k))  # шея — у края сыра, голова крутится и кивает
    a.box("fur", -0.34, 0.34, -0.2, 0.36, -0.26, 0.3)
    a.frustum("furL", (-0.24, 0.24, -0.22, 0.06), (-0.08, 0.08, -0.14, -0.02), -0.2, -0.6, axis="y")
    a.box("pink", -0.08, 0.08, -0.68, -0.56, -0.14, -0.02)
    for s_ in (-1, 1):
        eye(a, (s_ * 0.16, -0.2, 0.16), 0.2, 0.24, look=(-s_ * 0.1, 0.6), depth=0.1)
        bar(a, "dark", (s_ * 0.12, -0.48, -0.08), (s_ * 0.5, -0.6, -0.03), 0.022)
        bar(a, "dark", (s_ * 0.12, -0.48, -0.12), (s_ * 0.48, -0.58, -0.19), 0.02)
    a.box("white", -0.07, 0.07, -0.6, -0.54, -0.26, -0.14, bevel=0)
    a.box("cheese", -0.3, 0.26, -0.08, 0.3, 0.28, 0.36)
    a.box("cheese", 0.27, 0.33, -0.24, -0.16, -0.05, 0.32, bevel=0)
    for s_ in (-1, 1):  # уши — свои части, шевелятся
        part(a, "EarL" if s_ < 0 else "EarR", "Head", (hx + s_ * 0.3 * k, hy + 0.03 * k, hzc + 0.22 * k))
        disc(a, "fur", s_ * 0.34, 0.36, 0.22, -0.02, 0.08, n=8, axis="y")
        disc(a, "pink", s_ * 0.34, 0.36, 0.14, -0.05, -0.01, n=8, axis="y", bevel=0)
    a.transform = None
    for s_ in (-1, 1):  # лапки на краю теста
        part(a, "PawL" if s_ < 0 else "PawR", "Pizza", (hx + s_ * 0.56, hy - 0.02, z0 + 0.21))
        a.box("pink", hx + s_ * 0.56 - 0.12, hx + s_ * 0.56 + 0.12, hy - 0.36, hy - 0.02, z0 + 0.14, z0 + 0.28)
        for dx in (-0.07, 0.0, 0.07):
            a.box("white", hx + s_ * 0.56 + dx - 0.02, hx + s_ * 0.56 + dx + 0.02, hy - 0.42, hy - 0.36, z0 + 0.15,
                  z0 + 0.2, bevel=0)
    # Хвост: из-под заднего края, длинный, завитком вверх (наклонён вместе с куском).
    a.transform = slice_m
    part(a, "Tail", "Pizza", tuple(slice_m @ Vector((0.25, 0.62, z0 + 0.22))))
    chain(a, "pink", [(0.25, 0.62, z0 + 0.22), (0.35, 1.2, z0 + 0.28), (0.25, 1.52, z0 + 0.62), (0.0, 1.52, 1.12),
                      (-0.25, 1.32, 1.3), (-0.38, 1.12, 1.18)], 0.16, 0.08)
    a.transform = None
    a.pose = {"Head": ((0, 0, 16), (0, 0, 0)), "EarL": ((0, 25, 0), (0, 0, 0)), "EarR": ((0, -20, 0), (0, 0, 0)),
              "PawL": ((-35, 0, 0), (0, 0, 0)), "Tail": ((0, 0, 30), (0, 0, 0))}
    return a


def rat_head(a, c, k=1.0, look=(0.0, 0.6), eyes=True, teeth=True, snout_only=False):
    """Голова крысы лицом к −y (центр c, масштаб k): череп, морда-клин, розовый нос, глаза, усы, резцы.
    snout_only — только морда, нос и усы (голова под шлемом). Уши — rat_ear. Цвета fur, furL, pink, white, dark."""
    prev = a.transform
    a.transform = (prev if prev is not None else Matrix.Identity(4)) @ Matrix.Translation(c) @ Matrix.Scale(k, 4)
    if not snout_only:
        a.box("fur", -0.34, 0.34, -0.2, 0.36, -0.26, 0.3)
    a.frustum("furL", (-0.24, 0.24, -0.22, 0.06), (-0.08, 0.08, -0.14, -0.02), -0.2, -0.6, axis="y")
    a.box("pink", -0.08, 0.08, -0.68, -0.56, -0.14, -0.02)
    for s in (-1, 1):
        if eyes:
            eye(a, (s * 0.16, -0.2, 0.16), 0.2, 0.24, look=(look[0] - s * 0.1, look[1]), depth=0.1)
        bar(a, "dark", (s * 0.12, -0.48, -0.08), (s * 0.5, -0.6, -0.03), 0.022, bevel=0)
        bar(a, "dark", (s * 0.12, -0.48, -0.12), (s * 0.48, -0.58, -0.19), 0.02, bevel=0)
    if teeth:
        a.box("white", -0.07, 0.07, -0.6, -0.54, -0.26, -0.14, bevel=0)
    a.transform = prev


def rat_ear(a, c, k, s):
    """Ухо крысы на голове rat_head с тем же центром и масштабом (s = −1 левое, 1 правое)."""
    prev = a.transform
    a.transform = (prev if prev is not None else Matrix.Identity(4)) @ Matrix.Translation(c) @ Matrix.Scale(k, 4)
    disc(a, "fur", s * 0.34, 0.36, 0.22, -0.02, 0.08, n=8, axis="y")
    disc(a, "pink", s * 0.34, 0.36, 0.14, -0.05, -0.01, n=8, axis="y", bevel=0)
    a.transform = prev


def bubble(a, key, c, r):
    """Пузырь лицом к −y: восьмигранная «капля» с бликом."""
    x, y, z = c
    disc(a, key, x, z, r, y - r * 0.5, y + r * 0.5, n=8, axis="y", bevel=0)
    a.box("glint", x - r * 0.5, x - r * 0.2, y - r * 0.5 - 0.02, y - r * 0.5 - 0.005, z + r * 0.2, z + r * 0.5,
          bevel=0)


RUNNER_PAINT = (("white", "FFFDF4"), ("dark", "1E1E24"), ("glint", "FFFFFF"), ("pink", "F49AB0"),
                ("fur", "8790B0"), ("furL", "A8AFCB"))


# ── 3. Билетик-беглец: живой билет метро бежит со всех ног — огромные глаза, рот запыхался, ручки машут, ножки в
#       красных кроссовках на шаге, капли пота; сзади к нему тянется «рогатка» турникета-ловца ─────────────────────


def runaway_ticket():
    a = S.Art("Art_RunawayTicket", ring_z0=1.6)
    a.paint("ticket", "FFE27A", rings=True)
    for key, code in RUNNER_PAINT + (("red", "E53935"), ("shoe", "FF4F6D"), ("leg", "2B2B33"), ("chrome", "C3CAD4"),
                                     ("turn", "3A4A6B"), ("sweat", "7FD4FF"), ("mouth", "5A1020"), ("ticketD", "E8B84A"), ("sole", "FFFDF4"),
                                     ("tongue", "F06A86"), ("gold", "F2C230")):
        a.paint(key, code)
    top = stand(a, "common", 1.45)
    sparkle(a, "glint", (1.35, -0.6, 2.6), 0.26)
    # Турникет-ловец сзади слева: тумба, хромовая крышка, ступица.
    a.box("turn", -1.36, -1.0, 0.0, 0.5, top, top + 1.5)
    a.box("chrome", -1.4, -0.96, -0.04, 0.54, top + 1.46, top + 1.58)
    a.box("gold", -1.38, -0.98, -0.02, 0.52, top + 0.7, top + 0.78, bevel=0)
    disc(a, "chrome", top + 1.2, 0.25, 0.16, -1.0, -0.88, n=8, axis="x")
    hub = Vector((-0.88, 0.25, top + 1.2))
    part(a, "Grabber", "Stand", tuple(hub))  # «рогатка» турникета тянется к краю билета
    for tgt, w in (((-0.72, 0.3, 2.35), 0.08), ((-0.66, 0.36, 1.75), 0.085), ((-0.95, 0.32, 2.62), 0.09)):
        v = (Vector(tgt) - hub).normalized()
        bar(a, "chrome", tuple(hub), tgt, w)
        gem(a, "red", tuple(Vector(tgt) + 0.04 * v), 0.14)
    # Билет наклонён вперёд — бежит; ножки и ручки — свои части.
    zb = 0.95
    bm = tilt((0, 0, zb), "X", 8)
    part(a, "Body", "Stand", (0, 0, zb))
    a.transform = bm
    a.box("ticket", -0.95, 0.95, -0.08, 0.08, zb, zb + 1.42)
    a.box("red", -0.93, 0.93, -0.1, 0.1, zb + 1.16, zb + 1.34, bevel=0)
    for i in range(7):  # перфорация слева
        z = zb + 0.12 + i * 0.17
        a.box("ticketD", -0.97, -0.9, -0.11, 0.11, z, z + 0.07, bevel=0)
    disc(a, "dark", 0.68, zb + 0.9, 0.08, -0.12, -0.07, n=8, axis="y", bevel=0)  # дырочка компостера
    for i, w in enumerate((0.03, 0.06, 0.03, 0.03, 0.08, 0.03, 0.05, 0.03, 0.06)):  # штрихкод
        x = -0.55 + i * 0.12
        a.box("dark", x, x + w, -0.11, -0.08, zb + 0.08, zb + 0.28, bevel=0)
    a.box("mouth", -0.22, 0.22, -0.12, -0.07, zb + 0.32, zb + 0.56, bevel=0)
    a.box("tongue", -0.12, 0.12, -0.14, -0.1, zb + 0.32, zb + 0.42, bevel=0)
    for s in (-1, 1):  # брови домиком — испуг (на красной полосе)
        bar(a, "dark", (s * 0.12, -0.12, zb + 1.24), (s * 0.58, -0.12, zb + 1.16), 0.06, 0.05, bevel=0)
    for x, z, sz in ((-0.7, zb + 1.5, 0.12), (0.55, zb + 1.62, 0.1), (0.85, zb + 1.45, 0.08)):
        gem(a, "sweat", (x, 0.0, z), sz)
    a.transform = None
    for s in (-1, 1):
        pivot = bm @ Vector((s * 0.3, -0.14, zb + 0.86))
        part(a, "EyeL" if s < 0 else "EyeR", "Body", tuple(pivot))
        a.transform = bm
        eye(a, (s * 0.3, -0.08, zb + 0.86), 0.46, 0.5, look=(0.3, 0.2), depth=0.14)
        a.transform = None
    # Ручки машут, ножки на шаге (левая вперёд, правая отведена назад), красные кроссовки.
    part(a, "ArmL", "Body", tuple(bm @ Vector((-0.95, 0, zb + 0.75))))
    bar(a, "leg", tuple(bm @ Vector((-0.95, 0, zb + 0.75))), (-1.38, -0.2, zb + 1.2), 0.07)
    a.box("white", -1.48, -1.28, -0.3, -0.1, zb + 1.18, zb + 1.36)
    part(a, "ArmR", "Body", tuple(bm @ Vector((0.95, 0, zb + 0.75))))
    bar(a, "leg", tuple(bm @ Vector((0.95, 0, zb + 0.75))), (1.36, 0.25, zb + 0.4), 0.07)
    a.box("white", 1.28, 1.48, 0.16, 0.36, zb + 0.28, zb + 0.46)
    for s, foot in ((-1, (-0.38, -0.48, top + 0.1)), (1, (0.42, 0.42, top + 0.38))):
        hip = Vector((s * 0.32, 0.0, zb + 0.02))
        part(a, "LegL" if s < 0 else "LegR", "Body", tuple(hip))
        bar(a, "leg", tuple(hip), foot, 0.08 + 0.005 * (s > 0))
        fx, fy, fz = foot
        a.box("sole", fx - 0.14, fx + 0.14, fy - 0.3, fy + 0.12, fz - 0.1, fz - 0.03)
        a.box("shoe", fx - 0.13, fx + 0.13, fy - 0.27, fy + 0.1, fz - 0.04, fz + 0.12)
    a.pose = {"LegL": ((30, 0, 0), (0, 0, 0)), "LegR": ((-30, 0, 0), (0, 0, 0)), "ArmL": ((0, -30, 0), (0, 0, 0)),
              "ArmR": ((0, 30, 0), (0, 0, 0)), "EyeL": ((0, 0, -15), (0, 0, 0)), "Grabber": ((25, 0, 0), (0, 0, 0))}
    return a


# ── 4. Крыса-рыцарь: маленькая крыса в огромном рыцарском шлеме (забрало поднимается, из щели горят глаза, снизу
#       торчит морда с усами, уши — в дырках шлема, красный плюмаж), с сырным мечом и щитом из крышки от банки ───────


def rat_knight():
    a = S.Art("Art_RatKnight", ring_z0=1.6)
    a.paint("steel", "B8C0CC", rings=True)
    for key, code in RUNNER_PAINT + (("steelD", "7E8794"), ("gold", "F2C230"), ("goldL", "FFE07A"),
                                     ("plume", "E53935"), ("plumeD", "B71C2C"), ("cheese", "F9C93A"),
                                     ("hole", "B8700E"), ("lid", "D62D3A"), ("glow", "FFE45C"), ("pinkD", "E07A94")):
        a.paint(key, code)
    top = stand(a, "common", 1.4)
    sparkle(a, "glint", (1.3, -0.6, 2.9), 0.26)
    # Тело: ноги, туловище с нагрудником и сырной эмблемой, хвост.
    for s in (-1, 1):
        part(a, "LegL" if s < 0 else "LegR", "Body", (s * 0.18, -0.02, top + 0.42))
        a.box("fur", s * 0.18 - 0.11, s * 0.18 + 0.11, -0.12, 0.1, top + 0.08, top + 0.44)
        a.box("pink", s * 0.18 - 0.14, s * 0.18 + 0.14, -0.32, 0.12, top, top + 0.1)
    part(a, "Body", "Stand", (0, 0, top + 0.42))
    disc(a, "fur", 0, 0.0, 0.36, top + 0.4, top + 1.12, n=8)
    a.frustum("steel", (-0.34, 0.34, -0.44, -0.3), (-0.26, 0.26, -0.4, -0.3), top + 0.52, top + 1.08)
    a.prism("cheese", [(-0.12, top + 0.68), (0.14, top + 0.68), (-0.12, top + 0.92)], -0.47, -0.42, axis="y")
    a.frame("gold", ngon(0, 0, 0.4, 8), 0.06, top + 0.5, top + 0.58, axis="z", bevel=0)
    part(a, "Tail", "Body", (0, 0.32, top + 0.5))
    chain(a, "pink", [(0, 0.32, top + 0.5), (0.1, 0.8, top + 0.35), (0.45, 1.05, top + 0.6), (0.6, 0.95, top + 1.0)],
          0.1, 0.06)
    # Шлем-ведро больше тела: золотой обод, рёбра, заклёпки, щель с горящими глазами; морда торчит снизу.
    hz = top + 1.1
    part(a, "Head", "Body", (0, 0, hz))
    rat_head(a, (0, -0.2, hz + 0.12), 1.15, eyes=False, snout_only=True, teeth=True)
    a.box("steel", -0.52, 0.52, -0.5, 0.5, hz + 0.08, hz + 1.1)
    a.frustum("steel", (-0.52, 0.52, -0.5, 0.5), (-0.34, 0.34, -0.32, 0.32), hz + 1.08, hz + 1.3)
    a.frame("gold", S.octagon(-0.56, 0.56, -0.54, 0.54, 0.14), 0.08, hz + 0.04, hz + 0.18, axis="z")
    a.box("steelD", -0.06, 0.06, -0.54, 0.54, hz + 1.08, hz + 1.36)  # гребень
    for s in (-1, 1):
        for z in (hz + 0.35, hz + 0.75):
            a.box("goldL", s * 0.53 - 0.03, s * 0.53 + 0.03, -0.36, -0.28, z - 0.04, z + 0.04, bevel=0)
    a.box("dark", -0.4, 0.4, -0.53, -0.49, hz + 0.56, hz + 0.72, bevel=0)  # щель
    for s in (-1, 1):
        a.box("glow", s * 0.18 - 0.08, s * 0.18 + 0.08, -0.545, -0.525, hz + 0.58, hz + 0.7, bevel=0)
    # Плюмаж: красные перья ступенями назад.
    part(a, "Plume", "Head", (0, 0.1, hz + 1.3))
    for i, (y, z, w) in enumerate(((0.05, hz + 1.38, 0.2), (0.25, hz + 1.5, 0.22), (0.48, hz + 1.48, 0.2),
                                   (0.66, hz + 1.32, 0.16))):
        a.box("plume" if i % 2 == 0 else "plumeD", -w / 2, w / 2, y - 0.14, y + 0.14, z - 0.12, z + 0.12)
    # Уши торчат из дырок по бокам шлема.
    for s in (-1, 1):
        part(a, "EarL" if s < 0 else "EarR", "Head", (s * 0.52, 0.05, hz + 0.85))
        x0, x1 = sorted((s * 0.5, s * 0.6))
        disc(a, "fur", hz + 1.0, 0.05, 0.2, x0, x1, n=8, axis="x")
        p0, p1 = sorted((s * 0.6, s * 0.63))
        disc(a, "pink", hz + 1.0, 0.05, 0.12, p0, p1, n=8, axis="x", bevel=0)
    # Забрало: пластина с прорезями над щелью, поднимается на шарнире сверху.
    part(a, "Visor", "Head", (0, -0.52, hz + 0.98))
    a.box("steelD", -0.46, 0.46, -0.6, -0.52, hz + 0.76, hz + 1.0)
    for x in (-0.3, -0.1, 0.1, 0.3):
        a.box("dark", x - 0.03, x + 0.03, -0.615, -0.595, hz + 0.8, hz + 0.95, bevel=0)
    # Правая лапа поднимает сырный меч; левая держит щит-крышку в красно-белую клетку.
    part(a, "ArmR", "Body", (0.36, 0, top + 1.0))
    bar(a, "fur", (0.36, 0, top + 1.0), (0.78, -0.3, top + 1.2), 0.13)
    a.box("pink", 0.7, 0.9, -0.42, -0.2, top + 1.1, top + 1.3)
    a.box("gold", 0.56, 1.06, -0.37, -0.25, top + 1.3, top + 1.4)  # гарда
    a.prism("cheese", [(0.66, top + 1.4), (0.96, top + 1.4), (0.96, top + 2.7), (0.81, top + 2.92)], -0.39, -0.23,
            axis="y")
    for x, z in ((0.88, top + 1.65), (0.78, top + 2.0), (0.89, top + 2.35)):
        a.box("hole", x - 0.04, x + 0.04, -0.405, -0.385, z, z + 0.08, bevel=0)
    a.box("gold", 0.76, 0.86, -0.36, -0.26, top + 1.04, top + 1.12)
    part(a, "ArmL", "Body", (-0.36, 0, top + 1.0))
    sm = tilt((-0.9, -0.2, top + 0.8), "Z", -35)  # щит сбоку, развёрнут к главному ракурсу
    bar(a, "fur", (-0.36, 0, top + 1.0), (-0.78, -0.18, top + 0.82), 0.13)
    sy = -0.2
    a.transform = sm
    disc(a, "lid", -0.9, top + 0.8, 0.46, sy - 0.06, sy + 0.04, n=16, axis="y")
    a.frame("steel", ngon(-0.9, top + 0.8, 0.5, 16), 0.07, sy - 0.08, sy + 0.05, axis="y")
    for i in range(4):
        for j in range(4):
            if (i + j) % 2 == 0:
                x, z = -1.18 + j * 0.14, top + 1.0 - i * 0.14
                a.box("white", x, x + 0.14, sy - 0.075, sy - 0.055, z, z + 0.14, bevel=0)
    a.transform = None
    a.pose = {"Visor": ((-70, 0, 0), (0, 0, 0)), "ArmR": ((0, -25, 0), (0, 0, 0)), "Head": ((0, 0, 12), (0, 0, 0)),
              "Plume": ((15, 0, 0), (0, 0, 0)), "Tail": ((0, 0, 25), (0, 0, 0)), "LegL": ((-20, 0, 0), (0, 0, 0))}
    return a


# ── 5. Газировка-мутант: неоново-зелёная банка с фиолетовой полосой и молнией; огромная пасть, из которой
#       вырываются разноцветные пузырьки, бешеные глаза разного размера, язычок банки-«хохолок», ножки и ручки ──────


def mutant_soda():
    a = S.Art("Art_MutantSoda", ring_z0=1.5)
    a.paint("can", "35D46A", rings=True)
    for key, code in RUNNER_PAINT + (("band", "7B3FE4"), ("yellow", "FFD23F"), ("metal", "C3CAD4"),
                                     ("mouth", "3A0E2A"), ("lip", "FF6EC7"), ("shoe", "2F6BD8"), ("leg", "2B2B33"),
                                     ("b1", "FF4FD8"), ("b2", "4FC3FF"), ("b3", "FFE14F"), ("b4", "7CFF4F")):
        a.paint(key, code)
    top = stand(a, "common", 1.4)
    sparkle(a, "glint", (-1.25, -0.6, 2.9), 0.26)
    # Ножки в синих кроссовках.
    for s in (-1, 1):
        part(a, "LegL" if s < 0 else "LegR", "Body", (s * 0.28, 0, top + 0.5))
        a.box("leg", s * 0.28 - 0.06, s * 0.28 + 0.06, -0.06, 0.06, top + 0.12, top + 0.52)
        a.box("shoe", s * 0.28 - 0.14, s * 0.28 + 0.14, -0.36, 0.12, top, top + 0.16)
    # Банка: корпус, фиолетовая полоса с молнией, металлический верх и низ.
    part(a, "Body", "Stand", (0, 0, top + 0.5))
    zc0, zc1, r = top + 0.48, top + 2.5, 0.62
    ap = r * math.cos(math.pi / 12)
    disc(a, "can", 0, 0, r, zc0, zc1, n=12)
    disc(a, "metal", 0, 0, 0.58, zc0 - 0.06, zc0 + 0.02, n=12, bevel=0)
    a.frame("metal", ngon(0, 0, 0.64, 12), 0.1, zc1 - 0.04, zc1 + 0.08, axis="z", bevel=0)
    disc(a, "metal", 0, 0, 0.52, zc1 - 0.02, zc1 + 0.03, n=12, bevel=0)
    disc(a, "band", 0, 0, 0.645, zc0 + 0.28, zc0 + 0.5, n=12, bevel=0)
    for th in (90, 0, 180):  # молнии на боках и сзади (середины граней)
        m = tilt((0, 0, 0), "Z", th - 270)
        pixel_boxes(a, "yellow", ["..##", ".##.", "####", ".##.", "##.."], 0.07, -0.14, zc0 + 1.25, -ap - 0.03, -ap + 0.01,
                    matrix=m)
    # Пасть выступает трубой из банки: тёмная глубина, розовые губы сверху и по бокам, верхние зубы.
    a.box("mouth", -0.38, 0.38, -0.56, -0.3, zc0 + 0.6, zc0 + 1.22, bevel=0)
    a.box("lip", -0.47, 0.47, -0.84, -0.3, zc0 + 1.2, zc0 + 1.32)
    for s in (-1, 1):
        x0, x1 = sorted((s * 0.37, s * 0.47))
        a.box("lip", x0, x1, -0.83, -0.3, zc0 + 0.6, zc0 + 1.22)
    for x in (-0.24, -0.08, 0.08, 0.24):
        a.box("white", x - 0.065, x + 0.065, -0.8, -0.6, zc0 + 1.08, zc0 + 1.21, bevel=0)
    # Глаза разного размера (уходят вглубь банки — без щелей на изгибе), брови вразлёт.
    part(a, "EyeL", "Body", (-0.24, -ap - 0.15, zc0 + 1.62))
    eye(a, (-0.24, -ap + 0.22, zc0 + 1.62), 0.42, 0.46, look=(0.6, 0.5), depth=0.52)
    part(a, "EyeR", "Body", (0.3, -ap - 0.12, zc0 + 1.66))
    eye(a, (0.3, -ap + 0.22, zc0 + 1.66), 0.3, 0.3, look=(-0.7, -0.6), depth=0.46)
    part(a, "Body", "Stand", (0, 0, top + 0.5))
    bar(a, "dark", (-0.5, -ap - 0.12, zc0 + 1.98), (-0.06, -ap - 0.12, zc0 + 1.9), 0.06, 0.05, bevel=0)
    bar(a, "dark", (0.16, -ap - 0.12, zc0 + 1.88), (0.5, -ap - 0.12, zc0 + 2.0), 0.055, 0.05, bevel=0)
    # Нижняя губа — челюсть.
    part(a, "Jaw", "Body", (0, -0.2, zc0 + 0.56))
    a.box("lip", -0.48, 0.48, -0.86, -0.3, zc0 + 0.5, zc0 + 0.61)
    # Пузырьки вырываются из пасти и летят вверх.
    part(a, "Bubbles", "Body", (0, -ap - 0.3, zc0 + 0.9))
    for i, (x, y, z, rr) in enumerate(((-0.15, -ap - 0.25, zc0 + 0.9, 0.17), (0.2, -ap - 0.42, zc0 + 1.0, 0.14),
                                       (-0.05, -ap - 0.62, zc0 + 1.22, 0.12), (0.32, -ap - 0.7, zc0 + 0.72, 0.1),
                                       (-0.38, -ap - 0.55, zc0 + 0.78, 0.11), (0.12, -ap - 0.85, zc0 + 1.45, 0.09),
                                       (-0.3, -ap - 0.9, zc0 + 1.6, 0.08))):
        bubble(a, ("b1", "b2", "b3", "b4")[i % 4], (x, y, z), rr)
    # Язычок банки — «хохолок» на макушке.
    part(a, "Tab", "Body", (0.1, 0.05, zc1 + 0.06))
    a.frame("metal", S.octagon(0.02, 0.38, -0.02, 0.24, 0.06), 0.06, zc1 + 0.04, zc1 + 0.08, axis="z", bevel=0)
    a.box("metal", 0.06, 0.16, -0.0, 0.1, zc1 + 0.02, zc1 + 0.1, bevel=0)
    # Ручки вверх — бешеный восторг.
    for s in (-1, 1):
        part(a, "ArmL" if s < 0 else "ArmR", "Body", (s * 0.6, -0.05, zc0 + 1.0))
        bar(a, "leg", (s * 0.6, -0.05, zc0 + 1.0), (s * 1.0, -0.2, zc0 + 1.55), 0.07)
        a.box("white", s * 1.0 - 0.1, s * 1.0 + 0.1, -0.3, -0.1, zc0 + 1.5, zc0 + 1.7)
    a.pose = {"Jaw": ((20, 0, 0), (0, 0, 0)), "Bubbles": ((0, 0, 0), (0, -0.15, 0.3)), "Tab": ((-40, 0, 0), (0, 0, 0)),
              "ArmL": ((0, 25, 0), (0, 0, 0)), "EyeR": ((0, 0, 30), (0, 0, 0)), "LegR": ((-25, 0, 0), (0, 0, 0))}
    return a


# ── 6. Улитка-метро: толстая улитка ползёт по слизи; вместо раковины — маленький синий вагон метро с окнами,
#       фарами, дверями и токоприёмником; глаза на стебельках, улыбка, щёчки ────────────────────────────────────


def subway_snail():
    a = S.Art("Art_SubwaySnail", ring_z0=1.0)
    a.paint("skin", "B8E986", rings=True)
    a.paint("car", "2F6DB5", rings=True)
    for key, code in RUNNER_PAINT + (("skinD", "8CC860"), ("slime", "9FE3FF"), ("cream", "EFE3C2"),
                                     ("window", "FFD86B"), ("lamp", "FFF3B0"), ("red", "E53935"), ("metal", "C3CAD4"),
                                     ("mouth", "5A1020"), ("cheek", "FF8FB1")):
        a.paint(key, code)
    top = stand(a, "common", 1.55)
    sparkle(a, "glint", (1.3, -0.7, 2.2), 0.26)
    a.extrude("slime", [(0.3, 0.25), (1.2, 0.35), (1.42, 0.62), (1.2, 0.95), (0.3, 0.8)], top - 0.005, top + 0.05,
              axis="z")
    # Улитка ползёт влево-вперёд: всё тело повёрнуто лицом к главному ракурсу.
    turn = tilt((0, 0, 0), "Z", 28)
    part(a, "Body", "Stand", tuple(turn @ Vector((0, 0, top))))
    a.transform = turn
    a.box("skin", -1.05, 1.25, -0.46, 0.46, top, top + 0.32)
    a.box("skinD", -0.95, 1.3, -0.5, 0.5, top - 0.01, top + 0.1, bevel=0)
    a.frustum("skin", (-1.4, -0.7, -0.4, 0.4), (-1.38, -0.86, -0.32, 0.32), top + 0.28, top + 1.08)
    a.box("skin", -1.44, -0.66, -0.42, 0.42, top + 0.3, top + 0.7)
    for x, y in ((0.4, -0.47), (0.9, -0.47), (0.1, 0.47)):
        disc(a, "skinD", x, top + 0.18, 0.07, y - 0.02, y + 0.02, n=8, axis="y", bevel=0)
    # Лицо смотрит влево (−x): улыбка, щёчки.
    a.box("mouth", -1.47, -1.43, -0.2, 0.2, top + 0.5, top + 0.58, bevel=0)
    a.box("mouth", -1.47, -1.43, -0.26, -0.18, top + 0.56, top + 0.66, bevel=0)
    a.box("mouth", -1.47, -1.43, 0.18, 0.26, top + 0.56, top + 0.66, bevel=0)
    for y in (-0.3, 0.3):
        a.box("cheek", -1.47, -1.43, y - 0.08, y + 0.08, top + 0.66, top + 0.76, bevel=0)
    a.transform = None
    # Глаза на стебельках.
    for s in (-1, 1):
        base = Vector((-1.1, s * 0.16, top + 1.05))
        part(a, "StalkL" if s < 0 else "StalkR", "Body", tuple(turn @ base))
        a.transform = turn
        bar(a, "skin", tuple(base), (-1.28, s * 0.3, top + 1.62), 0.1 + 0.005 * (s > 0))
        disc(a, "white", top + 1.68, s * 0.32, 0.17, -1.42, -1.16, n=8, axis="x")
        disc(a, "dark", top + 1.7, s * 0.32 - 0.03, 0.08, -1.45, -1.41, n=8, axis="x", bevel=0)
        a.box("glint", -1.47, -1.45, s * 0.32 - 0.07, s * 0.32 - 0.03, top + 1.73, top + 1.77, bevel=0)
        a.transform = None
    # Раковина — вагон метро: кузов, кремовая полоса, окна, двери, фары, красные огни, крыша, токоприёмник.
    part(a, "Shell", "Body", tuple(turn @ Vector((0.2, 0, top + 0.32))))
    a.transform = turn
    zc = top + 0.31
    a.box("car", -0.62, 1.08, -0.44, 0.44, zc, zc + 1.0)
    a.box("cream", -0.64, 1.1, -0.46, 0.46, zc + 0.36, zc + 0.46, bevel=0)
    a.frustum("metal", (-0.62, 1.08, -0.44, 0.44), (-0.52, 0.98, -0.3, 0.3), zc + 0.98, zc + 1.14)
    for s in (-1, 1):
        y0, y1 = sorted((s * 0.44, s * 0.47))
        for x in (-0.38, 0.08, 0.54, 0.9):
            a.box("window", x - 0.14, x + 0.1, y0, y1, zc + 0.52, zc + 0.86, bevel=0)
        a.box("dark", 0.22, 0.38, y0, y1 + 0.005 * s, zc + 0.08, zc + 0.86, bevel=0)
    a.box("window", -0.65, -0.62, -0.3, 0.3, zc + 0.52, zc + 0.86, bevel=0)
    for y in (-0.26, 0.26):
        disc(a, "lamp", zc + 0.2, y, 0.09, -0.68, -0.6, n=8, axis="x", bevel=0)
        disc(a, "red", zc + 0.2, y, 0.07, 1.06, 1.12, n=8, axis="x", bevel=0)
    a.box("red", -0.67, -0.63, -0.12, 0.12, zc + 0.08, zc + 0.3, bevel=0)
    bar(a, "dark", (0.0, -0.25, zc + 1.14), (0.35, 0.0, zc + 1.46), 0.04, bevel=0)
    bar(a, "dark", (0.7, -0.25, zc + 1.14), (0.35, 0.0, zc + 1.46), 0.045, bevel=0)
    a.box("metal", 0.05, 0.65, -0.05, 0.05, zc + 1.44, zc + 1.5, bevel=0)
    a.transform = None
    a.pose = {"StalkL": ((15, 0, 0), (0, 0, 0)), "StalkR": ((-12, 0, 10), (0, 0, 0)),
              "Shell": ((0, -8, 0), (0, 0, 0.05))}
    return a


# ── 7. Чемодан на ножках: коралловый чемодан шагает на коротких ножках; верхняя половина — крышка-челюсть на шарнире
#       сзади, по шву — зубастая молния, из пасти свисает полосатый носок и торчит кусок сыра; глаза на крышке ──────


def walking_suitcase():
    a = S.Art("Art_WalkingSuitcase", ring_z0=1.3)
    a.paint("case", "E8504A", rings=True)
    for key, code in RUNNER_PAINT + (("caseD", "B83A36"), ("cream", "F4E2C0"), ("gold", "F2C230"),
                                     ("strap", "7A4A26"), ("mouth", "3A0E14"), ("metal", "D4DAE3"), ("shoe", "2F6BD8"),
                                     ("leg", "2B2B33"), ("red", "E53935"), ("cheese", "F9C93A"), ("hole", "B8700E"),
                                     ("blue", "4FC3FF"), ("purple", "8E44EC")):
        a.paint(key, code)
    top = stand(a, "common", 1.45)
    sparkle(a, "glint", (-1.3, -0.6, 2.4), 0.26)
    # Ножки на шаге.
    for s, dy in ((-1, -0.12), (1, 0.12)):
        part(a, "LegL" if s < 0 else "LegR", "Body", (s * 0.45, dy, 0.64))
        a.box("leg", s * 0.45 - 0.08, s * 0.45 + 0.08, dy - 0.08, dy + 0.08, top + 0.14, 0.66)
        a.box("shoe", s * 0.45 - 0.17, s * 0.45 + 0.17, dy - 0.36, dy + 0.14, top, top + 0.18)
    # Нижняя половина: корпус, кремовая полоса, золотые уголки, наклейки, тёмная глубина пасти, нижний ряд молнии.
    part(a, "Body", "Stand", (0, 0, 0.62))
    a.box("case", -1.0, 1.0, -0.45, 0.45, 0.62, 1.26)
    a.box("cream", -1.02, 1.02, -0.47, 0.47, 0.82, 0.9, bevel=0)
    for x in (-1.0, 1.0):
        for y in (-0.45, 0.45):
            a.box("gold", x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0.56, 0.76)
    a.box("blue", 0.45, 0.75, -0.475, -0.455, 0.94, 1.18, bevel=0)
    a.box("purple", -0.8, -0.56, -0.475, -0.455, 0.95, 1.15, bevel=0)
    a.box("mouth", -0.96, 0.96, -0.42, 0.42, 1.2, 1.345, bevel=0)
    for i in range(9):
        x = -0.8 + i * 0.2
        a.frustum("metal", (x - 0.07, x + 0.07, -0.5, -0.4), (x, x, -0.45, -0.45), 1.24, 1.4, bevel=0)
    # Носок свисает изо рта, кусок сыра торчит сбоку.
    a.box("white", -0.6, -0.36, -0.56, -0.44, 0.86, 1.32, bevel=0)
    for z in (0.97, 1.12):
        a.box("red", -0.61, -0.35, -0.57, -0.43, z, z + 0.06, bevel=0)
    a.box("red", -0.62, -0.34, -0.66, -0.44, 0.78, 0.89, bevel=0)
    a.prism("cheese", [(0.3, -0.44), (0.95, -0.44), (0.3, 0.05)], 1.27, 1.47)
    a.box("hole", 0.4, 0.48, -0.47, -0.44, 1.32, 1.4, bevel=0)
    # Крышка-челюсть: верхняя половина, верхний ряд молнии, полоса, уголки, ручка; глаза — свои части.
    part(a, "Lid", "Body", (0, 0.45, 1.32))
    a.box("case", -1.0, 1.0, -0.45, 0.45, 1.33, 1.98)
    a.box("cream", -1.02, 1.02, -0.47, 0.47, 1.72, 1.8, bevel=0)
    for x in (-1.0, 1.0):
        for y in (-0.45, 0.45):
            a.box("gold", x - 0.1, x + 0.1, y - 0.1, y + 0.1, 1.86, 2.04)
    for i in range(8):
        x = -0.7 + i * 0.2
        a.frustum("metal", (x - 0.07, x + 0.07, -0.5, -0.4), (x, x, -0.45, -0.45), 1.36, 1.2, bevel=0)
    for x in (-0.3, 0.3):
        a.box("strap", x - 0.06, x + 0.06, -0.07, 0.07, 1.96, 2.16)
    a.box("strap", -0.38, 0.38, -0.09, 0.09, 2.12, 2.24)
    for s in (-1, 1):
        bar(a, "dark", (s * 0.16, -0.5, 1.98), (s * 0.66, -0.5, 1.88), 0.07, 0.06, bevel=0)
    for s in (-1, 1):
        part(a, "EyeL" if s < 0 else "EyeR", "Lid", (s * 0.4, -0.55, 1.6))
        eye(a, (s * 0.4, -0.45, 1.6), 0.34, 0.36, look=(0.3, -0.5), depth=0.2)
    a.pose = {"Lid": ((-24, 0, 0), (0, 0, 0)), "LegL": ((-25, 0, 0), (0, 0, 0)), "LegR": ((20, 0, 0), (0, 0, 0)),
              "EyeL": ((0, 0, 15), (0, 0, 0))}
    return a


# ── 8. Злой будильник: красный круглый будильник со злой мордой — сердитые брови, оскал, стрелки вместо усов
#       (подкручиваются), два золотых звонка-уха и молоточек между ними, ножки ─────────────────────────────────────


def angry_alarm_clock():
    a = S.Art("Art_AngryAlarmClock", ring_z0=1.5)
    a.paint("red", "E2343F", rings=True)
    a.paint("gold", "F2C230", rings=True)
    for key, code in RUNNER_PAINT + (("redD", "A11E2B"), ("goldL", "FFE07A"), ("gold2", "C9921A"), ("face", "FFF8EC"),
                                     ("mouth", "3A0E14"), ("leg", "2B2B33")):
        a.paint(key, code)
    top = stand(a, "common", 1.35)
    sparkle(a, "glint", (1.25, -0.6, 2.9), 0.26)
    for s in (-1, 1):
        part(a, "LegL" if s < 0 else "LegR", "Body", (s * 0.45, 0, 0.72))
        bar(a, "gold2", (s * 0.4, 0, 0.74), (s * 0.62, -0.05, top + 0.12), 0.09 + 0.005 * (s > 0))
        a.box("gold", s * 0.62 - 0.14, s * 0.62 + 0.14, -0.22, 0.12, top, top + 0.14)
    # Корпус: красный 16-гранник, золотой обод, белый циферблат с метками, злая морда.
    part(a, "Body", "Stand", (0, 0, 0.62))
    cz, r = 1.58, 0.95
    disc(a, "red", 0, cz, r, -0.36, 0.36, n=16, axis="y")
    a.frame("gold", ngon(0, cz, 0.99, 16), 0.13, -0.42, -0.26, axis="y")  # золото только спереди
    a.frame("gold", ngon(0, cz, 0.98, 16), 0.08, 0.26, 0.4, axis="y")
    disc(a, "face", 0, cz, 0.84, -0.4, -0.35, n=16, axis="y", bevel=0)
    for k in range(12):
        t = math.radians(k * 30)
        mx, mz = 0.72 * math.sin(t), cz + 0.72 * math.cos(t)
        h = 0.07 if k % 3 else 0.1
        a.box("dark", mx - h / 2, mx + h / 2, -0.43, -0.39, mz - h / 2, mz + h / 2, bevel=0)
    for s in (-1, 1):  # сердитые брови
        bar(a, "dark", (s * 0.1, -0.46, cz + 0.42), (s * 0.55, -0.46, cz + 0.56), 0.1, 0.08, bevel=0)
    a.box("mouth", -0.36, 0.36, -0.45, -0.39, cz - 0.64, cz - 0.36, bevel=0)  # оскал
    for x in (-0.24, -0.08, 0.08, 0.24):
        a.frustum("white", (x - 0.07, x + 0.07, -0.48, -0.4), (x, x, -0.44, -0.44), cz - 0.38, cz - 0.52, bevel=0)
    for x in (-0.16, 0.0, 0.16):
        a.frustum("white", (x - 0.07, x + 0.07, -0.48, -0.4), (x, x, -0.44, -0.44), cz - 0.62, cz - 0.5, bevel=0)
    for s in (-1, 1):  # ключи завода сзади
        a.box("gold2", s * 0.3 - 0.05, s * 0.3 + 0.05, 0.34, 0.5, cz - 0.05, cz + 0.05)
        a.box("goldL", s * 0.3 - 0.16, s * 0.3 + 0.16, 0.48, 0.54, cz - 0.1, cz + 0.1)
    for s in (-1, 1):
        part(a, "EyeL" if s < 0 else "EyeR", "Body", (s * 0.3, -0.48, cz + 0.22))
        eye(a, (s * 0.3, -0.38, cz + 0.22), 0.3, 0.26, look=(-s * 0.4, -0.5), depth=0.16)
    # Стрелки — усы: от центра в стороны с завитком кверху; красная шпилька.
    part(a, "Mustache", "Body", (0, -0.45, cz))
    for s in (-1, 1):
        bar(a, "dark", (0, -0.45, cz - 0.02), (s * 0.48, -0.45, cz - 0.16), 0.08 + 0.006 * (s > 0), 0.06, bevel=0)
        bar(a, "dark", (s * 0.46, -0.45, cz - 0.16), (s * 0.66, -0.46, cz + 0.04), 0.07, 0.055, bevel=0)
    disc(a, "red", 0, cz, 0.08, -0.52, -0.43, n=8, axis="y", bevel=0)
    # Звонки-уши и молоточек.
    for s in (-1, 1):
        part(a, "BellL" if s < 0 else "BellR", "Body", (s * 0.42, 0, cz + 0.88))
        m = tilt((s * 0.42, 0, cz + 0.88), "Y", s * 28)
        a.transform = m
        a.box("gold2", s * 0.42 - 0.05, s * 0.42 + 0.05, -0.05, 0.05, cz + 0.84, cz + 1.02)
        disc(a, "gold", s * 0.42, 0, 0.36, cz + 1.0, cz + 1.18, n=12)
        disc(a, "gold", s * 0.42, 0, 0.27, cz + 1.16, cz + 1.34, n=12)
        disc(a, "goldL", s * 0.42, 0, 0.12, cz + 1.32, cz + 1.42, n=8)
        a.transform = None
    part(a, "Hammer", "Body", (0, 0, cz + 0.95))
    a.box("gold2", -0.04, 0.04, -0.04, 0.04, cz + 0.92, cz + 1.36)
    a.box("gold", -0.15, 0.15, -0.1, 0.1, cz + 1.3, cz + 1.46)
    a.pose = {"BellL": ((0, -15, 0), (0, 0, 0)), "BellR": ((0, 15, 0), (0, 0, 0)), "Hammer": ((0, 25, 0), (0, 0, 0)),
              "Mustache": ((0, 18, 0), (0, 0, 0)), "LegR": ((-20, 0, 0), (0, 0, 0)), "EyeL": ((0, 0, -12), (0, 0, 0))}
    return a


# ── 9. Кроссовок с жильцом: огромный красно-синий кроссовок на белой подошве; из него выглядывает крыса, держится
#       лапками за край, а бантик шнурков у неё под носом — пышные усы ──────────────────────────────────────────


def sneaker_tenant():
    a = S.Art("Art_SneakerTenant", ring_z0=1.0)
    a.paint("upper", "E2343F", rings=True)
    for key, code in RUNNER_PAINT + (("sole", "F7F4EE"), ("soleD", "3A3F4B"), ("navy", "24305E"), ("inner", "2A1A22"),
                                     ("lace", "FFFDF4"), ("star", "FFD23F"), ("mouth", "5A1020")):
        a.paint(key, code)
    top = stand(a, "common", 1.55)
    sparkle(a, "glint", (-1.4, -0.6, 2.4), 0.26)
    turn = tilt((0, 0, 0), "Z", 20)  # носок — вперёд-влево, к главному ракурсу
    part(a, "Body", "Stand", (0, 0, top))
    a.transform = turn
    z0 = top
    a.extrude("soleD", [(-1.45, z0), (1.3, z0), (1.32, z0 + 0.08), (-1.48, z0 + 0.08)], -0.56, 0.56, axis="y")
    a.extrude("sole", [(-1.5, z0 + 0.07), (1.32, z0 + 0.07), (1.36, z0 + 0.36), (-1.32, z0 + 0.36),
                       (-1.52, z0 + 0.24)], -0.58, 0.58, axis="y")
    a.extrude("upper", [(-1.3, z0 + 0.35), (1.28, z0 + 0.35), (1.28, z0 + 1.72), (0.55, z0 + 1.78), (0.32, z0 + 1.3),
                        (-0.3, z0 + 1.08), (-1.0, z0 + 0.86), (-1.34, z0 + 0.62)], -0.5, 0.5, axis="y")
    a.extrude("sole", [(-1.36, z0 + 0.34), (-0.72, z0 + 0.34), (-0.78, z0 + 0.92), (-1.0, z0 + 0.88),
                       (-1.38, z0 + 0.62)], -0.52, 0.52, axis="y")
    a.extrude("navy", [(0.7, z0 + 0.33), (1.3, z0 + 0.33), (1.3, z0 + 1.0), (0.85, z0 + 1.0)], -0.52, 0.52, axis="y")
    for s in (-1, 1):  # звезда-заплатка на боках (без логотипов)
        y0, y1 = sorted((s * 0.5, s * 0.53))
        pixel_boxes(a, "star", ["..#..", ".###.", "#####", ".###.", ".#.#."], 0.09, -0.15, z0 + 1.18,
                    y0, y1, matrix=None)
    a.box("inner", 0.56, 1.22, -0.36, 0.36, z0 + 1.7, z0 + 1.8, bevel=0)  # проём
    a.frame("lace", S.octagon(0.5, 1.3, -0.44, 0.44, 0.12), 0.08, z0 + 1.72, z0 + 1.86, axis="z")
    for i in range(3):  # шнуровка крест-накрест по подъёму
        x = -0.2 + i * 0.22
        z = z0 + 1.12 + i * 0.1
        bar(a, "lace", (x, -0.4, z), (x + 0.2, 0.4, z + 0.09), 0.05, bevel=0)
        bar(a, "lace", (x, 0.4, z), (x + 0.2, -0.4, z + 0.09), 0.055, bevel=0)
    a.transform = None
    # Язычок кроссовка — откидывается.
    part(a, "Tongue", "Body", tuple(turn @ Vector((0.42, 0, z0 + 1.4))))
    a.transform = turn
    a.box("navy", 0.3, 0.52, -0.3, 0.3, z0 + 1.4, z0 + 2.0, matrix=tilt((0.42, 0, z0 + 1.4), "Y", -20))
    a.transform = None
    # Крыса выглядывает из проёма: голова, уши, лапки на краю.
    hc = Vector((0.92, -0.08, z0 + 2.06))
    part(a, "Rat", "Body", tuple(turn @ (hc + Vector((0, 0.2, -0.3)))))
    a.transform = turn
    rat_head(a, tuple(hc), 1.0, look=(-0.3, 0.4))
    a.transform = None
    for s in (-1, 1):
        part(a, "EarL" if s < 0 else "EarR", "Rat", tuple(turn @ (hc + Vector((s * 0.34, 0.02, 0.24)))))
        a.transform = turn
        rat_ear(a, tuple(hc), 1.0, s)
        a.transform = None
        part(a, "PawL" if s < 0 else "PawR", "Rat", tuple(turn @ Vector((0.92 + s * 0.3, -0.3, z0 + 1.86))))
        a.transform = turn
        a.box("pink", 0.92 + s * 0.3 - 0.1, 0.92 + s * 0.3 + 0.1, -0.5, -0.26, z0 + 1.82, z0 + 1.94)
        a.transform = None
    # Бантик шнурков под носом крысы — пышные усы (свои части — шевелятся).
    part(a, "Laces", "Body", tuple(turn @ Vector((0.72, -0.48, z0 + 1.62))))
    a.transform = turn
    a.box("lace", 0.64, 0.8, -0.56, -0.42, z0 + 1.56, z0 + 1.7)
    for s in (-1, 1):
        bar(a, "lace", (0.72, -0.52, z0 + 1.64), (0.72 + s * 0.52, -0.62, z0 + 1.58), 0.1, 0.08, bevel=0)
        bar(a, "lace", (0.72 + s * 0.5, -0.62, z0 + 1.58), (0.72 + s * 0.7, -0.64, z0 + 1.86), 0.09, 0.075, bevel=0)
        bar(a, "lace", (0.72 + s * 0.06, -0.52, z0 + 1.58), (0.72 + s * 0.2, -0.56, z0 + 1.28), 0.05, bevel=0)
    a.transform = None
    a.pose = {"Rat": ((0, 0, -15), (0, 0, 0.12)), "EarL": ((0, 20, 0), (0, 0, 0)), "Laces": ((0, 12, 0), (0, 0, 0)),
              "Tongue": ((0, -15, 0), (0, 0, 0)), "PawR": ((-25, 0, 0), (0, 0, 0))}
    return a


# ── 10. Утка-контролёр: жёлтая резиновая утка в синей фуражке контролёра с золотой кокардой; в правом крыле —
#        гигантский компостер-щипцы с красными ручками и пробитым билетиком; клюв открывается, крылья, лапки, хвост ───


def duck_inspector():
    a = S.Art("Art_DuckInspector", ring_z0=1.0)
    a.paint("duck", "FFD23F", rings=True)
    for key, code in RUNNER_PAINT + (("orange", "FF8A1F"), ("cap", "24305E"), ("capD", "1A2347"), ("gold", "F2C230"),
                                     ("red", "E53935"), ("metal", "C3CAD4"), ("water", "6FD0FF"), ("ticket", "FFE27A"),
                                     ("cheek", "FF9EB1")):
        a.paint(key, code)
    top = stand(a, "common", 1.45)
    sparkle(a, "glint", (-1.3, -0.6, 2.7), 0.26)
    a.extrude("water", [(-1.15, -0.4), (-0.4, -1.1), (0.6, -1.0), (1.15, -0.3), (1.0, 0.7), (-0.2, 1.1), (-1.05, 0.6)],
              top - 0.005, top + 0.03, axis="z")
    for s in (-1, 1):  # лапки-ласты
        part(a, "FootL" if s < 0 else "FootR", "Body", (s * 0.32, -0.45, top + 0.14))
        a.box("orange", s * 0.32 - 0.07, s * 0.32 + 0.07, -0.52, -0.38, top + 0.06, top + 0.2)
        a.prism("orange", [(s * 0.32, -0.45), (s * 0.32 - 0.24, -0.9), (s * 0.32 + 0.24, -0.9)], top + 0.03, top + 0.09)
    # Тело утки: низ, грудка, верх; хвост — своя часть.
    part(a, "Body", "Stand", (0, 0, top + 0.2))
    a.prism("duck", S.octagon(-0.85, 0.85, -0.7, 0.72, 0.3), top + 0.18, top + 0.86)
    a.prism("duck", S.octagon(-0.62, 0.62, -0.86, -0.3, 0.16), top + 0.3, top + 0.96)
    a.prism("duck", S.octagon(-0.7, 0.7, -0.56, 0.62, 0.25), top + 0.84, top + 1.08)
    part(a, "Tail", "Body", (0, 0.65, top + 0.8))
    a.frustum("duck", (-0.32, 0.32, 0.5, 0.9), (-0.1, 0.1, 0.95, 1.1), top + 0.8, top + 1.35)
    # Голова: глаза, щёчки, верхний клюв; нижний клюв открывается; фуражка с кокардой и козырьком.
    part(a, "Head", "Body", (0, -0.2, top + 1.06))
    a.prism("duck", S.octagon(-0.5, 0.5, -0.66, 0.24, 0.18), top + 1.02, top + 1.86)
    for s in (-1, 1):
        a.box("dark", s * 0.24 - 0.08, s * 0.24 + 0.08, -0.7, -0.64, top + 1.5, top + 1.66, bevel=0)
        a.box("glint", s * 0.24 - 0.06, s * 0.24 - 0.02, -0.715, -0.695, top + 1.6, top + 1.64, bevel=0)
        a.box("cheek", s * 0.36 - 0.07, s * 0.36 + 0.07, -0.69, -0.64, top + 1.32, top + 1.42, bevel=0)
    a.frustum("orange", (-0.26, 0.26, top + 1.26, top + 1.44), (-0.14, 0.14, top + 1.3, top + 1.4), -0.64, -1.02,
              axis="y")
    part(a, "Beak", "Head", (0, -0.62, top + 1.25))
    a.box("orange", -0.22, 0.22, -0.98, -0.6, top + 1.13, top + 1.25)
    part(a, "Cap", "Head", (0, -0.2, top + 1.84))
    a.prism("cap", S.octagon(-0.53, 0.53, -0.69, 0.27, 0.18), top + 1.82, top + 2.0)
    a.prism("capD", S.octagon(-0.6, 0.6, -0.8, 0.38, 0.22), top + 1.98, top + 2.16)
    a.frame("red", S.octagon(-0.52, 0.52, -0.7, 0.28, 0.19), 0.04, top + 1.95, top + 1.99, axis="z", bevel=0)
    a.frustum("dark", (-0.42, 0.42, -0.98, -0.62), (-0.38, 0.38, -0.92, -0.62), top + 1.79, top + 1.85)
    pixel_boxes(a, "gold", CROWN, 0.045, -0.1575, top + 2.12, -0.84, -0.8)
    # Левое крыло; правое держит гигантский компостер-щипцы с пробитым билетиком.
    part(a, "WingL", "Body", (-0.72, -0.05, top + 0.9))
    a.box("duck", -0.92, -0.7, -0.4, 0.42, top + 0.42, top + 0.96, matrix=tilt((-0.72, 0, top + 0.9), "Y", -14))
    part(a, "WingR", "Body", (0.72, -0.05, top + 0.9))
    a.box("duck", 0.7, 0.92, -0.52, 0.3, top + 0.5, top + 0.98, matrix=tilt((0.72, 0, top + 0.9), "Y", 20))
    hinge = Vector((0.98, -0.62, top + 1.22))
    for dx, w in ((-0.14, 0.09), (0.14, 0.095)):  # ручки
        bar(a, "red", (hinge.x + dx * 0.4, hinge.y, hinge.z), (hinge.x + dx, -0.26, top + 0.56), w)
    disc(a, "metal", hinge.x, hinge.z, 0.11, hinge.y - 0.08, hinge.y + 0.08, n=8, axis="y")
    for dz, w in ((0.06, 0.1), (-0.06, 0.105)):  # губки щипцов вверх-вперёд
        bar(a, "metal", tuple(hinge), (hinge.x - 0.05, -1.05, hinge.z + 0.5 + dz), w, 0.08)
    a.box("ticket", 0.62, 1.22, -1.08, -0.98, top + 1.58, top + 1.92, bevel=0)
    disc(a, "dark", 0.84, top + 1.75, 0.06, -1.1, -1.07, n=8, axis="y", bevel=0)
    a.pose = {"Beak": ((-25, 0, 0), (0, 0, 0)), "Head": ((0, 0, 14), (0, 0, 0)), "Cap": ((0, 10, 0), (0, 0, 0.05)),
              "WingL": ((0, 30, 0), (0, 0, 0)), "WingR": ((0, -15, 0), (0, 0, 0)), "Tail": ((0, 0, 20), (0, 0, 0)),
              "FootL": ((20, 0, 0), (0, 0, 0))}
    return a


# ── 11. Конус-паникёр: оранжевый дорожный конус в белых полосах, испуганное лицо (глаза-плошки, рот «О», брови
#        домиком, капли пота), ручки в белых перчатках вскинуты в панике, на макушке мигает жёлтая лампа ────────────


def panic_cone():
    a = S.Art("Art_PanicCone", ring_z0=1.2)
    a.paint("cone", "FF7A1A", rings=True)
    for key, code in RUNNER_PAINT + (("base", "2B2B33"), ("mouth", "3A0E14"), ("lamp", "FFB21F"), ("lampL", "FFF3B0"),
                                     ("ray", "FFE45C"), ("sweat", "7FD4FF"), ("tongue", "F06A86")):
        a.paint(key, code)
    top = stand(a, "common", 1.35)
    sparkle(a, "glint", (1.25, -0.6, 2.9), 0.26)
    for s in (-1, 1):  # ножки-ботинки из-под основания
        part(a, "FootL" if s < 0 else "FootR", "Body", (s * 0.34, -0.5, top + 0.1))
        a.box("base", s * 0.34 - 0.16, s * 0.34 + 0.16, -1.0, -0.6, top, top + 0.18)
    part(a, "Body", "Stand", (0, 0, top + 0.1))
    a.box("base", -0.78, 0.78, -0.78, 0.78, top + 0.06, top + 0.24)
    z0, z1, w0, w1 = top + 0.24, top + 2.34, 0.6, 0.16

    def w(z):
        return w0 + (w1 - w0) * (z - z0) / (z1 - z0)

    a.frustum("cone", (-w0, w0, -w0, w0), (-w1, w1, -w1, w1), z0, z1)
    for za, zb in ((z0 + 0.22, z0 + 0.42), (z0 + 1.62, z0 + 1.78)):  # белые светоотражающие полосы
        a.frustum("white", (-w(za) - 0.02, w(za) + 0.02, -w(za) - 0.02, w(za) + 0.02),
                  (-w(zb) - 0.02, w(zb) + 0.02, -w(zb) - 0.02, w(zb) + 0.02), za, zb, bevel=0)
    # Лицо на наклонной передней грани: черты строятся на вертикальной плоскости и поворачиваются к грани.
    zr = top + 1.25
    yr = -w(zr)
    slope = math.degrees(math.atan((w0 - w1) / (z1 - z0)))
    fm = tilt((0, yr, zr), "X", -slope)
    a.transform = fm
    a.prism("mouth", ngon(0, zr - 0.3, 0.16, 8), yr - 0.04, yr + 0.02, axis="y", bevel=0)
    a.box("tongue", -0.08, 0.08, yr - 0.05, yr - 0.03, zr - 0.44, zr - 0.36, bevel=0)
    for s in (-1, 1):
        bar(a, "dark", (s * 0.08, yr - 0.06, zr + 0.42), (s * 0.4, yr - 0.06, zr + 0.34), 0.06, 0.05, bevel=0)
    for x, z, sz in ((-0.5, zr + 0.5, 0.12), (0.46, zr + 0.62, 0.1)):
        gem(a, "sweat", (x, yr - 0.1, z), sz)
    a.transform = None
    for s in (-1, 1):
        part(a, "EyeL" if s < 0 else "EyeR", "Body", tuple(fm @ Vector((s * 0.2, yr - 0.1, zr + 0.14))))
        a.transform = fm
        eye(a, (s * 0.2, yr + 0.02, zr + 0.14), 0.3, 0.34, look=(0.0, 0.0), depth=0.18)
        a.transform = None
    # Ручки вскинуты в панике, белые перчатки.
    for s in (-1, 1):
        sh = Vector((s * w(top + 1.15), -0.05, top + 1.15))
        part(a, "ArmL" if s < 0 else "ArmR", "Body", tuple(sh))
        bar(a, "base", tuple(sh), (s * 0.95, -0.25, top + 2.15), 0.07 + 0.005 * (s > 0))
        a.box("white", s * 0.95 - 0.12, s * 0.95 + 0.12, -0.37, -0.13, top + 2.1, top + 2.36)
    # Мигалка на макушке: жёлтый колпак, яркое сердце, лучи вспышки.
    part(a, "Lamp", "Body", (0, 0, z1))
    a.box("base", -0.2, 0.2, -0.2, 0.2, z1 - 0.04, z1 + 0.08)
    disc(a, "lamp", 0, 0, 0.2, z1 + 0.06, z1 + 0.32, n=8)
    disc(a, "lampL", 0, 0, 0.12, z1 + 0.3, z1 + 0.4, n=8, bevel=0)
    for ang in range(0, 360, 60):
        r = math.radians(ang)
        bar(a, "ray", (0.3 * math.cos(r), 0.3 * math.sin(r), z1 + 0.22), (0.48 * math.cos(r), 0.48 * math.sin(r),
                                                                          z1 + 0.28), 0.05, bevel=0)
    a.pose = {"ArmL": ((0, -20, 0), (0, 0, 0)), "ArmR": ((0, 25, 0), (0, 0, 0)), "Lamp": ((0, 0, 30), (0, 0, 0.06)),
              "EyeL": ((0, 0, 20), (0, 0, 0)), "EyeR": ((0, 0, 20), (0, 0, 0)), "FootL": ((-25, 0, 0), (0, 0, 0))}
    return a


# ── 12. Сырный скейтер: светлый мышонок в синем шлеме катится на скейтборде из сыра с колёсами-монетами — стойка
#        боком, ручки в стороны для равновесия, уши торчат из шлема, хвост вверх ──────────────────────────────────


def cheese_skater():
    a = S.Art("Art_CheeseSkater", ring_z0=0.55)
    a.paint("cheese", "F9C93A", rings=True)
    for key, code in RUNNER_PAINT + (("hole", "B8700E"), ("metal", "C3CAD4"), ("gold2", "C9921A"), ("goldL", "FFE07A"),
                                     ("helmet", "2F6BD8"), ("stripe", "FFD23F"), ("shirt", "FF6B35"), ("shoe", "E53935"),
                                     ("belly", "F4F1EA")):
        a.paint(key, code)
    a.paint("fur", "B9BFCC")
    a.paint("furL", "DADFE8")
    top = stand(a, "common", 1.55)
    a.paint("gold", "F2C230", rings=True)
    sparkle(a, "glint", (-1.35, -0.6, 2.5), 0.26)
    # Скейт: дека-сыр с загнутыми концами и дырками, подвески, колёса-монеты (передняя и задняя пары — свои части).
    part(a, "Board", "Stand", (0, 0, 0.5))
    a.extrude("cheese", [(-1.3, 0.62), (-1.1, 0.52), (1.1, 0.52), (1.3, 0.62), (1.28, 0.72), (1.08, 0.62),
                         (-1.08, 0.62), (-1.28, 0.72)], -0.36, 0.36, axis="y")
    for x, y, r in ((-0.62, 0.12, 0.08), (0.3, -0.14, 0.07), (0.78, 0.16, 0.06), (-0.2, -0.2, 0.05)):
        disc(a, "hole", x, y, r, 0.61, 0.635, n=8, bevel=0)
    for x in (-0.72, 0.72):
        a.box("metal", x - 0.12, x + 0.12, -0.3, 0.3, 0.4, 0.53)
    for x in (-0.72, 0.72):
        part(a, "WheelB" if x < 0 else "WheelF", "Board", (x, 0, 0.37))
        a.box("metal", x - 0.03, x + 0.03, -0.38, 0.38, 0.34, 0.4, bevel=0)
        for s in (-1, 1):
            y0, y1 = sorted((s * 0.26, s * 0.38))
            disc(a, "gold", x, 0.37, 0.15, y0, y1, n=8, axis="y")
            c0, c1 = sorted((s * 0.37, s * 0.4))
            disc(a, "goldL", x, 0.37, 0.07, c0, c1, n=8, axis="y", bevel=0)
    # Мышонок: ноги в стойке боком (кеды на деке), туловище в оранжевой майке, хвост.
    for s in (-1, 1):
        part(a, "LegL" if s < 0 else "LegR", "Body", (s * 0.16, 0, 0.98))
        bar(a, "fur", (s * 0.16, 0, 0.98), (s * 0.48, -0.04, 0.72), 0.12 + 0.005 * (s > 0))
        a.box("shoe", s * 0.48 - 0.13, s * 0.48 + 0.13, -0.24, 0.12, 0.62, 0.76)
        a.box("white", s * 0.48 - 0.14, s * 0.48 + 0.14, -0.25, 0.13, 0.62, 0.66, bevel=0)
    part(a, "Body", "Board", (0, 0, 0.96))
    a.box("shirt", -0.28, 0.28, -0.22, 0.22, 0.92, 1.48)
    a.box("belly", -0.16, 0.16, -0.25, -0.2, 1.0, 1.3, bevel=0)
    a.box("fur", -0.22, 0.22, -0.18, 0.18, 1.46, 1.56)
    part(a, "Tail", "Body", (0, 0.22, 1.0))
    chain(a, "pink", [(0, 0.22, 1.0), (0.05, 0.62, 0.95), (0.25, 0.92, 1.25), (0.35, 0.9, 1.7), (0.2, 0.75, 1.9)],
          0.09, 0.05)
    for s in (-1, 1):  # руки в стороны для равновесия
        part(a, "ArmL" if s < 0 else "ArmR", "Body", (s * 0.28, 0, 1.4))
        bar(a, "fur", (s * 0.28, 0, 1.4), (s * 0.82, -0.1, 1.56 - 0.12 * (s > 0)), 0.1 + 0.005 * (s > 0))
        a.box("pink", s * 0.82 - 0.09, s * 0.82 + 0.09, -0.19, -0.01, 1.47 - 0.12 * (s > 0), 1.65 - 0.12 * (s > 0))
    # Голова мышонка в шлеме: шлем — синий купол с жёлтой полосой и ремешком; уши торчат по бокам.
    hc = (0, -0.05, 1.86)
    part(a, "Head", "Body", (0, 0, 1.56))
    rat_head(a, hc, 0.8, look=(0.2, 0.3))
    a.prism("helmet", S.octagon(-0.33, 0.33, -0.27, 0.35, 0.1), 1.98, 2.16)
    a.prism("helmet", S.octagon(-0.26, 0.26, -0.2, 0.28, 0.08), 2.14, 2.26)
    a.box("stripe", -0.05, 0.05, -0.29, 0.37, 2.0, 2.27, bevel=0)
    for s in (-1, 1):
        a.box("dark", s * 0.3 - 0.02, s * 0.3 + 0.02, -0.12, -0.04, 1.66, 2.0, bevel=0)
    for s in (-1, 1):
        part(a, "EarL" if s < 0 else "EarR", "Head", (s * 0.27, -0.03, 2.02))
        rat_ear(a, hc, 0.95, s)
    a.pose = {"WheelF": ((0, 60, 0), (0, 0, 0)), "Board": ((0, -6, 8), (0, 0, 0)), "ArmL": ((0, 25, 0), (0, 0, 0)),
              "ArmR": ((0, 20, 0), (0, 0, 0)), "Head": ((0, 0, 15), (0, 0, 0)), "Tail": ((0, 0, -25), (0, 0, 0)),
              "LegR": ((15, 0, 0), (0, 0, 0))}
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
    sparkle(a, "glint", (-1.35, -0.5, 3.6), 0.3)
    for x, y, i in ((-1.1, -0.8, 0), (-0.95, -1.05, 1), (1.05, -0.95, 2)):  # рассыпанные монеты
        disc(a, "gold" if i % 2 else "goldL", x, y, 0.13, top, top + 0.05, n=8, bevel=0)
    # Ножки (каждая — своя часть: автомат может шагать), корпус, крышка, золотые уголки спереди.
    for x in (-0.7, 0.7):
        for y in (-0.4, 0.4):
            part(a, "Leg" + ("F" if y < 0 else "B") + ("L" if x < 0 else "R"), "Body", (x, y, 0.44))
            a.box("dark", x - 0.16, x + 0.16, y - 0.16, y + 0.16, top - 0.02, 0.44)
    part(a, "Body", "Stand", (0, 0, 0.42))
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
    part(a, "EyeL", "Body", (-0.46, -0.75, 3.03))
    eye(a, (-0.46, -0.64, 3.03), 0.44, 0.38, look=(0.5, -0.4), depth=0.24)
    part(a, "EyeR", "Body", (0.1, -0.75, 3.03))
    eye(a, (0.1, -0.64, 3.03), 0.44, 0.38, look=(-0.4, -0.4), depth=0.24)
    part(a, "Brows", "Body", (-0.18, -0.76, 3.28))
    bar(a, "dark", (-0.78, -0.76, 3.34), (-0.22, -0.76, 3.22), 0.1, 0.11)
    bar(a, "dark", (0.42, -0.76, 3.34), (-0.14, -0.76, 3.22), 0.11, 0.1)
    part(a, "Body", "Stand", (0, 0, 0.42))
    # Средняя полка — сыр (треугольники с дырками) и маленький глаз.
    for x0 in (-0.78, -0.36):
        a.prism("cheese", [(x0, 2.39), (x0 + 0.34, 2.39), (x0, 2.71)], -0.76, -0.64, axis="y")
        a.box("hole", x0 + 0.06, x0 + 0.12, -0.775, -0.755, 2.45, 2.51, bevel=0)
    part(a, "EyeS", "Body", (0.22, -0.71, 2.56))
    eye(a, (0.22, -0.64, 2.56), 0.24, 0.26, look=(-0.6, 0.1), depth=0.14)
    part(a, "Body", "Stand", (0, 0, 0.42))
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
    part(a, "Jaw", "Body", (0, -0.2, 0.86))  # нижние зубы и язык с монетами: пасть раскрывается вниз
    for x in (-0.6, -0.36, 0.36, 0.6):
        a.frustum("white", (x - 0.11, x + 0.11, -0.72, -0.6), (x, x, -0.66, -0.66), 0.74, 1.04, bevel=0)
    tm = tilt((0, -0.6, 0.86), "X", 14)
    a.box("tongue", -0.36, 0.36, -1.3, -0.56, 0.8, 0.94, matrix=tm)
    for x, y in ((-0.12, -1.0), (0.14, -1.18)):
        disc(a, "goldL", x, y, 0.1, 0.93, 0.97, n=8, bevel=0, matrix=tm)
    a.pose = {"Jaw": ((18, 0, 0), (0, 0, 0)), "EyeL": ((0, 0, 14), (0, 0, 0)), "EyeR": ((0, 0, 14), (0, 0, 0)),
              "Brows": ((0, 0, 0), (0, 0, -0.06)), "EyeS": ((0, 0, 40), (0, 0, 0)), "LegFL": ((-20, 0, 0), (0, 0, 0))}
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
    # Трон и гора монет — неподвижная часть Stand (корень скелета); король — подвижные части.
    part(a, "Stand", None, (0, 0, 0))
    sparkle(a, "glint", (-1.45, -0.6, 3.3), 0.3)
    sparkle(a, "glint", (1.4, -0.5, 2.9), 0.22)
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
    a.box("velvet", -0.76, 0.76, 0.555, 0.64, 1.16, 2.46)
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
    for s in (-1, 1):  # голени со ступнями — свои части (болтает ногами)
        part(a, "LegL" if s < 0 else "LegR", "Body", (s * 0.3, -0.58, 1.2))
        a.box("fur", s * 0.3 - 0.15, s * 0.3 + 0.15, -0.72, -0.44, 0.6, 1.2, bevel=0)
        a.box("pink", s * 0.3 - 0.19, s * 0.3 + 0.19, -0.98, -0.48, 0.48, 0.64, bevel=0)
    part(a, "Body", "Stand", (0, 0.05, 1.12))
    for s in (-1, 1):
        x0, x1 = sorted((s * 0.12, s * 0.48))
        a.box("fur", x0, x1, -0.55, 0.2, 1.1, 1.44)
    disc(a, "fur", 0, 0.05, 0.64, 1.12, 1.78, n=8)
    disc(a, "fur", 0, 0.05, 0.55, 1.74, 2.28, n=8)
    disc(a, "cream", 0, 1.52, 0.44, -0.62, -0.5, n=8, axis="y", bevel=0)  # брюшко светлее шерсти
    a.frame("gold", ngon(0, 0.05, 0.7, 8), 0.08, 1.46, 1.56, axis="z", bevel=0)
    a.box("cape", -0.74, 0.74, 0.3, 0.52, 1.2, 2.36)  # плащ не касается подушки спинки
    a.frame("ermine", ngon(0, 0.05, 0.62, 8), 0.2, 2.22, 2.4, axis="z", bevel=0)
    for ang in range(0, 360, 60):
        r = math.radians(ang + 30)
        x, y = 0.52 * math.cos(r), 0.05 + 0.52 * math.sin(r)
        a.box("dark", x - 0.03, x + 0.03, y - 0.03, y + 0.03, 2.39, 2.42, bevel=0)
    # Лапы: левая на подлокотнике, правая держит золотой кубок.
    part(a, "ArmL", "Body", (-0.55, 0.0, 2.12))
    bar(a, "fur", (-0.55, 0.0, 2.12), (-1.0, -0.1, 1.72), 0.2, 0.22)
    bar(a, "fur", (-1.0, -0.1, 1.72), (-1.02, -0.45, 1.68), 0.18, 0.2)
    a.box("pink", -1.14, -0.9, -0.62, -0.38, 1.6, 1.76, bevel=0)
    part(a, "ArmR", "Body", (0.55, 0.0, 2.12))
    bar(a, "fur", (0.55, 0.0, 2.12), (0.92, -0.2, 1.82), 0.2, 0.22)
    bar(a, "fur", (0.92, -0.2, 1.82), (0.86, -0.52, 2.12), 0.18, 0.2)
    a.box("pink", 0.76, 0.98, -0.64, -0.42, 2.04, 2.22, bevel=0)
    a.frustum("gold", (0.8, 1.04, -0.66, -0.42), (0.74, 1.1, -0.72, -0.36), 2.22, 2.5)
    a.box("purple", 0.79, 1.05, -0.67, -0.41, 2.46, 2.5, bevel=0)
    disc(a, "gold2", 0.92, -0.54, 0.06, 2.12, 2.24, n=8, bevel=0)
    # Голова: череп, пухлые щёки, морда, нос, резцы, ухмылка, усы, прищур с тяжёлыми веками, уши, корона набекрень.
    part(a, "Head", "Body", (0, -0.05, 2.3))
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
    for s in (-1, 1):
        part(a, "EarL" if s < 0 else "EarR", "Head", (s * 0.36, -0.01, 2.82))
        disc(a, "fur", s * 0.42, 3.02, 0.28, -0.06, 0.04, n=8, axis="y", bevel=0)
        disc(a, "pink", s * 0.42, 3.02, 0.18, -0.09, -0.05, n=8, axis="y", bevel=0)
    part(a, "Crown", "Head", (0, -0.05, 2.9))
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
    part(a, "Tail", "Body", (0.6, 0.72, 1.1))
    chain(a, "pink", [(0.6, 0.72, 1.1), (1.1, 1.0, 0.85), (1.52, 0.72, 0.6), (1.58, 0.2, 0.45), (1.38, -0.2, 0.42),
                      (1.12, -0.28, 0.46)], 0.15, 0.08)
    a.pose = {"Head": ((6, 0, -12), (0, 0, 0)), "ArmR": ((0, -22, 0), (0, 0, 0)), "ArmL": ((0, 14, 0), (0, 0, 0)),
              "Crown": ((0, -14, 0), (0, 0, 0.04)), "LegL": ((-28, 0, 0), (0, 0, 0)), "EarR": ((0, -18, 0), (0, 0, 0)),
              "Tail": ((0, 0, -18), (0, 0, 0))}
    return a


# ══ Сборка, запекание, экспорт, проверочные рендеры ════════════════════════════════════════════════════════

COMMON = [("LiveCheeseMonster", live_cheese_monster), ("PizzaRat", pizza_rat), ("RunawayTicket", runaway_ticket),
          ("RatKnight", rat_knight), ("MutantSoda", mutant_soda), ("SubwaySnail", subway_snail),
          ("WalkingSuitcase", walking_suitcase), ("AngryAlarmClock", angry_alarm_clock), ("SneakerTenant", sneaker_tenant),
          ("DuckInspector", duck_inspector), ("PanicCone", panic_cone), ("CheeseSkater", cheese_skater)]
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


TO_RBX = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))  # оси Blender → оси Roblox


def explode(obj, art, sign):
    """Разнести части по x на 10 шагов квадратов D39 (рисунок не сдвигается): окклюзия при запекании только своя,
    в любой позе на части нет чужих теней (как у босса)."""
    order = {g: i for i, g in enumerate(dict.fromkeys(art.face_groups))}
    me = obj.data
    done = set()
    for poly in me.polygons:
        dx = order[art.face_groups[poly.index]] * 10 * S.RING["step"] * sign
        for v in poly.vertices:
            if v not in done:
                me.vertices[v].co.x += dx
                done.add(v)


def rig_check(art):
    """Каждая группа граней — часть скелета; у каждой части есть родитель из скелета (кроме корня)."""
    groups = list(dict.fromkeys(art.face_groups))
    rig = art.rig
    return {"parts": len(groups), "missing": [g for g in groups if g not in rig],
            "unused": [g for g in rig if g not in groups],
            "bad_parent": [g for g, (par, _) in rig.items() if par is not None and par not in rig],
            "roots": [g for g, (par, _) in rig.items() if par is None]}


def split_keep(obj, art):
    """Как S.split_groups, но с материалами сборки (быстрый просмотр без запекания)."""
    out = {}
    me = obj.data
    for group in art.rig:
        pivot = Vector(art.rig[group][1])
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if art.face_groups[f.index] != group], context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        bmesh.ops.translate(bm, vec=-pivot, verts=bm.verts)
        part = bpy.data.meshes.new(f"{obj.name}_{group}")
        bm.to_mesh(part)
        bm.free()
        for m in me.materials:
            part.materials.append(m)
        o = bpy.data.objects.new(f"{obj.name}_{group}", part)
        o.location = pivot
        collection.objects.link(o)
        out[group] = o
    bpy.data.objects.remove(obj)
    return out


def rig_json(item_id, art, parts, path):
    """Скелет предмета для будущих анимаций (D55): части, родители, точки вращения и габариты в осях Roblox."""
    out = {"id": item_id, "order": list(art.rig), "parts": {}, "demo_pose": {}}
    for g, (parent, pivot) in art.rig.items():
        co = [TO_RBX @ v.co for v in parts[g].data.vertices]
        lo = Vector([min(c[i] for c in co) for i in range(3)])
        hi = Vector([max(c[i] for c in co) for i in range(3)])
        out["parts"][g] = {"parent": parent, "pivot": [round(c, 4) for c in TO_RBX @ Vector(pivot)],
                           "center": [round(c, 4) for c in (lo + hi) / 2], "size": [round(c, 4) for c in hi - lo]}
    for g, (rot, off) in art.pose.items():
        out["demo_pose"][g] = {"rot_xyz_blender_deg": list(rot), "offset_blender": list(off)}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


def render_pose(prev, parts, art, path):
    """Крупный кадр 3/4 в пробной позе: части связаны иерархией скелета и повёрнуты вокруг своих точек вращения."""
    bpy.context.view_layer.update()  # иначе matrix_world новых частей ещё единичная и дети уезжают
    for g, (parent, _) in art.rig.items():
        if parent:
            parts[g].parent = parts[parent]
            parts[g].matrix_parent_inverse = parts[parent].matrix_world.inverted()
    for g, (rot, off) in art.pose.items():
        parts[g].rotation_euler = [math.radians(d) for d in rot]
        parts[g].location += Vector(off)
    bpy.context.view_layer.update()
    keep = set(parts.values())
    hidden = [o for o in bpy.context.scene.objects if o.type == "MESH" and o not in keep and o.name != "Floor"]
    for o in hidden:
        o.hide_render = True
    co = [o.matrix_world @ v.co for o in parts.values() for v in o.data.vertices]
    lo = Vector([min(c[i] for c in co) for i in range(3)])
    hi = Vector([max(c[i] for c in co) for i in range(3)])
    size = max(hi - lo)
    cz = (lo.z + hi.z) / 2
    dist = 2.7 * size + 1.0
    prev.shot(path, (-0.62 * dist, -0.85 * dist, cz + 0.55 * size), (0, 0, cz - 0.05 * size), 75, (1100, 1100))
    for o in hidden:
        o.hide_render = False


bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new("Rats")
bpy.context.scene.collection.children.link(collection)

if CHECK:
    for item_id, make, _ in ITEMS:
        art = make()
        art.build(collection)
        print("CHECK", item_id, json.dumps({**art.stats, "rig": rig_check(art)}, ensure_ascii=False))
    sys.exit(0)

report, objs = {}, []
for item_id, make, group in ITEMS:
    art = make()
    obj = art.build(collection)
    rc = rig_check(art)
    if rc["missing"] or rc["bad_parent"] or len(rc["roots"]) != 1:
        raise ValueError(f"{item_id}: скелет {rc}")
    uv = {}
    if not QUICK:
        explode(obj, art, 1)
        uv = S.bake(obj, art, TEXDIR, item_id)
        explode(obj, art, -1)
    lo, hi = S.bounds(obj)
    report[item_id] = {**art.stats, **{k: round(v, 3) for k, v in uv.items()},
                       "size": [round(hi[i] - lo[i], 2) for i in range(3)], "rig_parts": rc["parts"]}
    if not QUICK:
        S.studio_json(obj, os.path.join(PREVIEWS, f"{item_id}.json"))
    objs.append((obj, group, art, item_id))
    print("ITEM_OK", item_id, report[item_id]["tris"], flush=True)

prev = S.Preview(collection)
heroes = [S.render_item(prev, obj, PREVIEWS) for obj, *_ in objs]
S.strip(heroes, os.path.join(PREVIEWS, "sheet.png"), gap=12)

# Общий кадр: предметы в ряд, каждый на площадке 3.7 × 3.7, и манекен Roblox (5.2 стада) — масштаб.
x = PAD / 2
for obj, *_ in objs:
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
for o in [o for o in bpy.context.scene.objects if o.name.startswith(("Pad", "Mannequin"))]:
    bpy.data.objects.remove(o)
prev.aim_lights(Vector((0, 0, 0)))
for obj, *_ in objs:
    obj.location.x = obj.location.z = 0

# Подвижные части: меш режется по группам (начало координат части — точка вращения), FBX из частей, скелет JSON,
# кадр в пробной позе — проверка, что части двигаются без дыр.
for obj, group, art, item_id in objs:
    if QUICK:
        parts = split_keep(obj, art)
    else:
        parts = S.split_groups(obj, art, {g: Vector(art.rig[g][1]) for g in art.rig}, collection)
        S.export_fbx([parts[g] for g in art.rig], os.path.join(REPO, "assets", "models", "art", f"{item_id}.fbx"))
        rig_json(item_id, art, parts, os.path.join(REPO, "assets", "models", "art", f"{item_id}.rig.json"))
    render_pose(prev, parts, art, os.path.join(PREVIEWS, f"Art_{item_id}_pose.png"))
    for o in parts.values():
        o.hide_render = True

with open(os.path.join(PREVIEWS, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("RATS_OK " + json.dumps({k: v["tris"] for k, v in report.items()}, ensure_ascii=False))
