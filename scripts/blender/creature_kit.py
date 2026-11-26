"""Общий набор существ (D54, D55, стиль D39 v2): детали, подставки по редкостям, глаза, подвижные части и весь цикл
«сборка → запекание → части с точками вращения → FBX → скелет rig.json → кадры → отчёт».

Перенесено без изменений поведения из scripts/blender/art_oasis.py (коллекция босса 4, эталон №20 «Фенек-загадочник»
v2), чтобы коллекции боссов 5–10 строились одним кодом; art_oasis.py не меняется. Отличия: run() вместо кода на уровне
модуля; размер карты — по редкости существа (D64: Common 512², Rare и выше 1024²), tex_size().
Подключается модулем коллекции (art_glacier.py): from creature_kit import *; … run(ITEMS, …). Зависит от art_style.py.
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style as S  # noqa: E402
import stand_colors as SC  # noqa: E402  (D71: цвет подставки = UITokens.Rarity)

PAD, PAD_H = 3.7, 0.12  # площадка существа у босса и её толщина в кадре масштаба
REPO = SHOTS = MODELS = TEXDIR = ""
QUICK = False
TO_RBX = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))  # оси Blender → оси Roblox
TEX_BY_RARITY = {"Common": 512}  # D64: Common 512², остальные 1024²
D39V2_RING = dict(S.RING, core=0.55)


def tex_size(rarity):
    return TEX_BY_RARITY.get(rarity, 1024)


def ngon(cx, cy, r, n=8, phase=None):
    phase = math.pi / n if phase is None else phase
    return [(cx + r * math.cos(phase + 2 * math.pi * i / n), cy + r * math.sin(phase + 2 * math.pi * i / n))
            for i in range(n)]


def disc(a, key, cx, cy, r, a0, a1, n=8, axis="z", bevel=S.BEVEL, matrix=None):
    a.prism(key, ngon(cx, cy, r, n), a0, a1, axis=axis, bevel=bevel, matrix=matrix)


def bar(a, key, p0, p1, w, h=None, bevel=S.BEVEL):
    """Брусок от точки p0 до p1 с сечением w × h."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    up = "Y" if abs(d.normalized().z) > 0.95 else "Z"
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("X", up).to_matrix().to_4x4()
    h = h or w
    a.box(key, -d.length / 2, d.length / 2, -w / 2, w / 2, -h / 2, h / 2, bevel=bevel, matrix=m)


def gem(a, key, c, size, turn=0.0):
    """Самоцвет: куб на вершине (ромб со всех сторон)."""
    m = Matrix.Translation(c) @ Matrix.Rotation(math.radians(turn), 4, "Z") @ Matrix.Rotation(
        math.radians(45), 4, "X") @ Matrix.Rotation(math.radians(35), 4, "Y")
    h = size / 2
    a.box(key, -h, h, -h, h, -h, h, bevel=0, matrix=m)


def pixel_boxes(a, key, rows, cell, x0, ztop, y0, y1, matrix=None):
    """Пиксельный знак в плоскости x–z (толщина y0…y1) прямоугольниками без общих граней."""
    for c, r, cw, rh in S.greedy_rects([[ch == "#" for ch in row] for row in rows]):
        a.box(key, x0 + c * cell, x0 + (c + cw) * cell, y0, y1, ztop - (r + rh) * cell, ztop - r * cell, bevel=0,
              matrix=matrix)


def eye(a, c, w, h=None, look=(0.0, 0.0), depth=0.3, lid=0.0, lid_key=None, white="white"):
    """Глаз лицом к −y: белок w × h выступает от грани y = c[1] на depth, зрачок смещён look, блик; lid — веко
    сверху (доля высоты белка) цветом lid_key."""
    x, y, z = c
    h = h or w
    a.box(white, x - w / 2, x + w / 2, y - depth, y + 0.02, z - h / 2, z + h / 2)
    pw = min(w, h) * 0.5
    px, pz = x + look[0] * (w - pw) / 2 * 0.8, z + look[1] * (h - pw) / 2 * 0.8
    a.box("dark", px - pw / 2, px + pw / 2, y - depth - 0.03, y - depth + 0.01, pz - pw / 2, pz + pw / 2, bevel=0)
    g = pw * 0.32
    a.box("glint", px - pw / 2 + 0.02, px - pw / 2 + 0.02 + g, y - depth - 0.045, y - depth - 0.025,
          pz + pw / 2 - 0.02 - g, pz + pw / 2 - 0.02, bevel=0)
    if lid > 0:
        a.box(lid_key, x - w / 2 - 0.03, x + w / 2 + 0.03, y - depth - 0.06, y + 0.01, z + h / 2 - lid * h,
              z + h / 2 + 0.04, bevel=0.006)


def part(a, name, parent, pivot):
    """Следующие детали — подвижная часть name (родитель parent, точка вращения pivot в координатах модели)."""
    if not hasattr(a, "rig"):
        a.rig, a.pose = {}, {}
    a.rig[name] = (parent, tuple(pivot))
    a.group = name


def stand(a, rarity, r=1.5):
    """Круглая подставка-витрина цвета редкости (D71: тело — насыщенный цвет UITokens.Rarity, кайма — светлый;
    золота у Common и Rare нет). Возвращает высоту верха."""
    part(a, "Stand", None, (0, 0, 0))
    c = SC.stand({"common": "Common", "rare": "Rare"}[rarity])
    body, rim = {"common": ("standC", "standCL"), "rare": ("standR", "standRL")}[rarity]
    a.paint(body, c["body"], rings=True)
    a.paint(rim, c["rim"])
    a.paint("gold", "F2C230", rings=True)
    # в игре подставку живого существа прячут (как у босса 3) — в карте ей меньше места, существу больше
    for key in (body, rim):
        a.uv_boost[key] = 0.4
    disc(a, body, 0, 0, r, 0.0, 0.22, n=12)
    a.frame(rim, ngon(0, 0, r + 0.05, 12), 0.1, 0.15, 0.28, axis="z")
    return 0.22


def chain(a, key, pts, widths, tip_key=None):
    """Толстая ломаная (пушистый хвост): бруски между точками и кубы в изгибах (без щелей на внешней стороне)."""
    for i in range(len(pts) - 1):
        k = tip_key if tip_key and i == len(pts) - 2 else key
        bar(a, k, pts[i], pts[i + 1], widths[i], widths[i] * 0.92)
    for i in range(1, len(pts) - 1):
        w = min(widths[i - 1], widths[i]) * 0.98
        x, y, z = pts[i]
        a.box(key, x - w / 2, x + w / 2, y - w * 0.46, y + w * 0.46, z - w / 2, z + w / 2, bevel=0)


def with_matrix(a, m):
    """Следующие детали — в осях m (поворот уха вокруг его основания, не переписывая координаты)."""
    a.transform = m


def tilt(c, axis, deg):
    """Поворот детали вокруг точки c."""
    c = Vector(c)
    return Matrix.Translation(c) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-c)


# Качество D39 эталона — фенек №20 v2 (утверждён владельцем 2026-11-13): профиль контура «полка» и запекание ×4 с
# выравниванием островов, проекцией до 66° и зазором 3 px; мелкое золото гладкое. Все новые существа — так же.
D39V2 = {"ring": dict(S.RING, core=0.55),
         "bake": {"ss": 4, "pack_margin": 0.003, "align": True, "project_angle": 66}}


def d39v2(a):
    a.ring = D39V2["ring"]
    a.bake_opts = D39V2["bake"]


def common_stand(a, r):
    """Подставка Common (D71: серая ADA6B4 с каймой D9D7E3); мелкое золото существа — гладкое."""
    t = stand(a, "common", r)
    a.paint("gold", "F2C230")
    return t


def round_eye(a, c, r, look=(0.0, 0.0), pupil=0.6, depth=0.05, lid=0.0, lid_key=None, n=8):
    """Круглый глаз лицом к −y: белок-восьмигранник радиуса r выступает от грани y = c[1] на depth; зрачок (доля pupil
    от r) смещён look (−1…1), два блика; lid — верхнее веко (доля высоты белка) цветом lid_key."""
    x, y, z = c
    disc(a, "white", x, z, r, y - depth, y + 0.02, n=n, axis="y")
    pr = r * pupil
    px, pz = x + look[0] * (r - pr) * 0.85, z + look[1] * (r - pr) * 0.85
    disc(a, "dark", px, pz, pr, y - depth - 0.025, y - depth + 0.01, n=n, axis="y", bevel=0)
    g = pr * 0.38
    a.box("glint", px - pr * 0.55, px - pr * 0.55 + g, y - depth - 0.04, y - depth - 0.02, pz + pr * 0.15,
          pz + pr * 0.15 + g, bevel=0)
    g2 = pr * 0.18
    a.box("glint", px + pr * 0.28, px + pr * 0.28 + g2, y - depth - 0.04, y - depth - 0.02, pz - pr * 0.5,
          pz - pr * 0.5 + g2, bevel=0)
    if lid > 0:
        a.box(lid_key, x - r - 0.03, x + r + 0.03, y - depth - 0.06, y + 0.01, z + r - 2 * r * lid, z + r + 0.04,
              bevel=0.006)


def petals(a, c, n, length, width, keys, center_key, center_r, normal=(0, 0, 1), lift=18, spin=0.0, bevel=S.BEVEL):
    """Цветок: n лепестков-брусков вокруг центра c в плоскости, поперечной normal, концы приподняты на lift°;
    серединка — восьмигранник."""
    m0 = Matrix.Translation(c) @ Vector(normal).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    for i in range(n):
        m = m0 @ Matrix.Rotation(math.radians(spin + i * 360 / n), 4, "Z") @ Matrix.Rotation(math.radians(-lift), 4, "Y")
        a.box(keys[i % len(keys)], center_r * 0.5, center_r * 0.5 + length, -width / 2, width / 2, -0.035, 0.035, bevel=bevel,
              matrix=m)
    a.prism(center_key, ngon(0, 0, center_r, 8), -0.02, 0.07, bevel=bevel, matrix=m0)


# ══ COMMON ═══════════════════════════════════════════════════════════════════════════════════════════════════
# Каталог владельца 2026-11-11, №1–5 (его же короткие спецификации); у каждого свой силуэт, лицо и характер — не
# повторы фенека №20 (утверждено: «не копируй дизайн фенека», 2026-11-13).

# ── 1. Кактус-боксёр: пузатый бочонок-кактус с рёбрами и колючками на коротких ножках в боксёрках; огромные красные
#       перчатки — левая в выпаде, правая в защите у подбородка; решительные брови и дерзкая ухмылка с капой; пояс
#       чемпиона с бирюзовым камнем; розовый цветок на макушке. Не Кактуар: бочонок, большое лицо, без «трёх точек» ────



def rare_stand(a, r):
    """Подставка Rare (D71: синяя 3D8EE0 с каймой 84CAE8, без золотого обода); мелкое золото существа — гладкое."""
    t = stand(a, "rare", r)
    a.paint("gold", "F2C230")
    return t


def epic_stand(a, r=1.6):
    """Подставка Epic (D71): фиолетовый ступенчатый холм 9A3EF0 на тёмном цоколе со светлой каймой E2B0FF, по краю —
    друзы аметистов (вместо прежней горы золота: золото — только Legendary и Secret). Возвращает высоту верха."""
    part(a, "Stand", None, (0, 0, 0))
    c = SC.stand("Epic")
    a.paint("gold", "F2C230")
    a.paint("epicS", c["body"], rings=True)
    a.paint("epicB", c["base"])
    a.paint("epicL", c["rim"])
    for key in ("epicB", "epicS", "epicL"):  # в игре подставку живого существа прячут — в карте ей меньше места
        a.uv_boost[key] = 0.4
    a.prism("epicB", S.octagon(-r, r, -r, r, r * 0.29), 0.0, 0.16)
    a.prism("epicS", S.octagon(-r + 0.18, r - 0.18, -r + 0.18, r - 0.18, r * 0.26), 0.14, 0.34)
    for x, y, h, ang in ((-r * 0.74, -r * 0.6, 0.62, 20), (r * 0.72, -r * 0.64, 0.5, -30), (r * 0.5, r * 0.74, 0.44, 45),
                         (-r * 0.55, r * 0.7, 0.4, -15)):
        m = tilt((x, y, 0.3), "Y", ang * 0.4)  # друза: высокий острый кристалл и низкий рядом
        a.frustum("epicL", (x - 0.16, x + 0.16, y - 0.13, y + 0.13), (x, x, y, y), 0.3, 0.3 + h, bevel=0, matrix=m)
        a.frustum("epicS", (x + 0.1, x + 0.3, y - 0.09, y + 0.1), (x + 0.2, x + 0.2, y, y), 0.28, 0.28 + h * 0.6,
                  bevel=0, matrix=m)
    return 0.34


def legendary_stand(a, r=1.6):
    """Подставка Legendary (D71): золото F5A215 в светлой кайме FFE27A, на нём светлый золотой ярус; по углам —
    бирюзовые камни. Форма прежняя (2026-11-13), лазурит заменён золотом редкости. Возвращает высоту верха."""
    part(a, "Stand", None, (0, 0, 0))
    c = SC.stand("Legendary")
    a.paint("gold", "F2C230")
    a.paint("legBody", c["body"], rings=True)  # свои ключи подставки: золото существа (gold*) не перекрашивается
    a.paint("legS", c["rim"], rings=True)
    a.paint("goldD", "C9921A")
    a.paint("legB", c["base"])
    a.paint("gemT", "2ED1C0")
    for key in ("legBody", "legS", "legB", "gemT"):  # в игре подставку прячут — в карте ей меньше места
        a.uv_boost[key] = 0.4
    a.prism("legB", S.octagon(-r, r, -r, r, r * 0.29), 0.0, 0.1)
    a.prism("legBody", S.octagon(-r + 0.06, r - 0.06, -r + 0.06, r - 0.06, r * 0.27), 0.08, 0.24)
    a.frame("legB", S.octagon(-r + 0.02, r - 0.02, -r + 0.02, r - 0.02, r * 0.28), 0.08, 0.2, 0.28, axis="z", bevel=0)
    a.prism("legS", S.octagon(-r + 0.32, r - 0.32, -r + 0.32, r - 0.32, r * 0.22), 0.22, 0.36)
    for k in range(4):
        ang = math.radians(45 + 90 * k)
        gem(a, "gemT", (math.cos(ang) * (r - 0.22), math.sin(ang) * (r - 0.22), 0.3), 0.16, turn=45 + 90 * k)
    return 0.36


def stripe_chain(a, keys, pts, w, h=None, joints=True):
    """Ломаная из брусков сечением w × h, цвета по очереди из keys (полоски); в изгибах — кубики цвета отрезка."""
    h = h or w
    for i in range(len(pts) - 1):  # соседние отрезки на 4 % разной толщины — боковые грани не совпадают
        k = 1.0 + 0.04 * (i % 2)
        bar(a, keys[i % len(keys)], pts[i], pts[i + 1], w * k, h * k)
        if joints and 0 < i:
            x, y, z = pts[i]
            m = min(w, h) * 0.98 / 2
            a.box(keys[i % len(keys)], x - m, x + m, y - m, y + m, z - m, z + m, bevel=0)


def half_oct(w, h, z0, cut=0.42):
    """Арка: верхняя половина восьмигранника шириной 2w и высотой h над z0 (точки (x, z) для призмы по оси y)."""
    c = min(w, h) * cut
    return [(-w, z0), (-w, z0 + h - c), (-w + c, z0 + h), (w - c, z0 + h), (w, z0 + h - c), (w, z0)]


def ball(a, key, c, r, n=5, flat=0.3):
    """«Шар» D39 — стопка восьмигранников (n ярусов) радиуса r вокруг c."""
    for k in range(n):
        z0 = -r + 2 * r * k / n
        z1 = -r + 2 * r * (k + 1) / n
        zm = (z0 + z1) / 2
        rr = max(math.sqrt(max(r * r - zm * zm, 0.0)), r * 0.35)
        a.prism(key, S.octagon(c[0] - rr, c[0] + rr, c[1] - rr, c[1] + rr, rr * flat), c[2] + z0 - (0.01 if k else 0),
                c[2] + z1 + 0.01)


def closed_eye(a, c, w, key="dark", happy=True):
    """Закрытый глаз «^» (довольный) или «—» (сонный) на грани −y."""
    x, y, z = c
    if happy:
        bar(a, key, (x - w / 2, y - 0.02, z - w * 0.18), (x, y - 0.02, z + w * 0.16), 0.05, 0.04, bevel=0)
        bar(a, key, (x, y - 0.025, z + w * 0.16), (x + w / 2, y - 0.025, z - w * 0.18), 0.05, 0.04, bevel=0)
    else:
        a.box(key, x - w / 2, x + w / 2, y - 0.04, y + 0.01, z - 0.025, z + 0.025, bevel=0)


# ── 6. Ящерка-зонтик: коралловая ящерка бежит на задних лапах, воротник раскрыт пляжным зонтом из восьми красно-белых
#       клиньев с золотыми наконечниками; модница — реснички, язык розовый, хвост завитком. Не Heliolisk (жёлто-чёрная) ──




def tube(a, keys, pts, r, n=8, joints=True):
    """Толстая труба из восьмигранных отрезков между точками (цвета по очереди из keys), в изгибах — короткие
    восьмигранные «шарниры» (без щелей)."""
    for i in range(len(pts) - 1):
        p0, p1 = Vector(pts[i]), Vector(pts[i + 1])
        d = p1 - p0
        m = Matrix.Translation(p0) @ d.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
        rr = r * (1.0 + 0.03 * (i % 3))  # три соседних звена разной толщины: боковые грани не совпадают
        a.prism(keys[i % len(keys)], ngon(0, 0, rr, n), 0.0, d.length, matrix=m)
        if joints and i > 0:
            a.prism(keys[i % len(keys)], ngon(0, 0, rr * 0.94, n), -rr * 0.55, rr * 0.55, bevel=0, matrix=m)



def face_marks(art, off):
    """Рисунок отметин (art.marks) в материале ключа marks["key"]: отрезки-капли на гранях, смотрящих вперёд (−y),
    симметрично по x; поверх меха и контуров D39, до запекания. off = (x, z) — сдвиг координат объекта от координат
    модели: при запекании часть разнесена по x (explode), в быстром просмотре начало части — её точка вращения.
    Геометрия не меняется."""
    m = art.marks
    mat = art.materials[list(art.colors).index(m["key"])]
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    shade = nt.nodes["RingShade"]
    p = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(nt.nodes.new("ShaderNodeTexCoord").outputs["Object"], p.inputs["Vector"])
    n = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(nt.nodes.new("ShaderNodeNewGeometry").outputs["True Normal"], n.inputs["Vector"])
    px = S._math(nt, "ABSOLUTE", S._math(nt, "SUBTRACT", p.outputs["X"], off[0]))
    pz = S._math(nt, "SUBTRACT", p.outputs["Z"], off[1])
    mask = None
    for (x0, z0, r0), (x1, z1, r1) in m["strokes"]:
        dx, dz = x1 - x0, z1 - z0
        ax, az = S._math(nt, "SUBTRACT", px, x0), S._math(nt, "SUBTRACT", pz, z0)
        h = S._math(nt, "DIVIDE", S._math(nt, "ADD", S._math(nt, "MULTIPLY", ax, dx), S._math(nt, "MULTIPLY", az, dz)),
                    dx * dx + dz * dz)
        h = S._math(nt, "MAXIMUM", S._math(nt, "MINIMUM", h, 1.0), 0.0)
        ex = S._math(nt, "SUBTRACT", ax, S._math(nt, "MULTIPLY", h, dx))
        ez = S._math(nt, "SUBTRACT", az, S._math(nt, "MULTIPLY", h, dz))
        d = S._math(nt, "SQRT", S._math(nt, "ADD", S._math(nt, "MULTIPLY", ex, ex), S._math(nt, "MULTIPLY", ez, ez)))
        edge = S._math(nt, "SUBTRACT", d, S._math(nt, "ADD", r0, S._math(nt, "MULTIPLY", h, r1 - r0)))
        ramp = nt.nodes.new("ShaderNodeMapRange")
        ramp.interpolation_type = "SMOOTHSTEP"
        nt.links.new(edge, ramp.inputs["Value"])
        ramp.inputs["From Min"].default_value, ramp.inputs["From Max"].default_value = m["soft"], -m["soft"]
        g = ramp.outputs["Result"]
        mask = g if mask is None else S._math(nt, "MAXIMUM", mask, g)
    front = S._math(nt, "LESS_THAN", n.outputs["Y"], -0.7)
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    nt.links.new(S._math(nt, "MULTIPLY", mask, front), mix.inputs["Fac"])
    nt.links.new(shade.outputs["Color"], mix.inputs["Color1"])
    mix.inputs["Color2"].default_value = (*S.lin(m["code"]), 1)
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Emission Color"])


def rig_check(art):
    groups = list(dict.fromkeys(art.face_groups))
    rig = art.rig
    return {"parts": len(groups), "missing": [g for g in groups if g not in rig],
            "unused": [g for g in rig if g not in groups],
            "bad_parent": [g for g, (par, _) in rig.items() if par is not None and par not in rig],
            "roots": [g for g, (par, _) in rig.items() if par is None]}


def explode(obj, art, sign):
    """Части разнесены по x на 10 шагов квадратов D39 (рисунок не сдвигается): окклюзия при запекании только своя."""
    order = {g: i for i, g in enumerate(dict.fromkeys(art.face_groups))}
    me = obj.data
    done = set()
    for poly in me.polygons:
        dx = order[art.face_groups[poly.index]] * 10 * S.RING["step"] * sign
        for v in poly.vertices:
            if v not in done:
                me.vertices[v].co.x += dx
                done.add(v)


def split_keep(obj, art, collection):
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
        mesh = bpy.data.meshes.new(f"{obj.name}_{group}")
        bm.to_mesh(mesh)
        bm.free()
        for m in me.materials:
            mesh.materials.append(m)
        o = bpy.data.objects.new(f"{obj.name}_{group}", mesh)
        o.location = pivot
        collection.objects.link(o)
        out[group] = o
    bpy.data.objects.remove(obj)
    return out


def rig_json(item_id, art, parts, path):
    """Скелет для анимаций (D55): части, родители, точки вращения и габариты в осях Roblox."""
    out = {"id": item_id, "order": list(art.rig), "parts": {}, "demo_pose": {},
           "transparent": list(getattr(art, "transparent_parts", ()))}
    for g, (parent, pivot) in art.rig.items():
        co = [TO_RBX @ (parts[g].matrix_world @ v.co) for v in parts[g].data.vertices]
        lo = Vector([min(c[i] for c in co) for i in range(3)])
        hi = Vector([max(c[i] for c in co) for i in range(3)])
        p = TO_RBX @ Vector(pivot)
        out["parts"][g] = {"parent": parent, "pivot": [round(c, 4) for c in p],
                           "center": [round(c, 4) for c in (lo + hi) / 2 - p], "size": [round(c, 4) for c in hi - lo]}
    for g, (rot, off) in art.pose.items():
        out["demo_pose"][g] = {"rot_xyz_blender_deg": list(rot), "offset_blender": list(off)}
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


def sphere_dirs(n):
    out = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(1 - z * z, 0.0))
        ang = math.pi * (3 - math.sqrt(5)) * i
        out.append(Vector((r * math.cos(ang), r * math.sin(ang), z)))
    return out


def face_samples(f):
    """Точки по всей грани: середина, вдоль рёбер у края и ближе к середине, у вершин."""
    c = f.calc_center_median()
    pts = [c]
    vs = [v.co for v in f.verts]
    for i in range(len(vs)):
        a_, b_ = vs[i], vs[(i + 1) % len(vs)]
        for k in (0.05, 0.3, 0.5, 0.7, 0.95):
            q = a_.lerp(b_, k)
            pts += [q.lerp(c, 0.03), q.lerp(c, 0.3)]
        pts.append(a_.lerp(c, 0.04))
    return pts


def drop_enclosed(parts):
    """Удалить грани, которых не видно ни в одной позе: из каждой их точки (чуть над гранью и глубже) луч в любую из
    600 сторон упирается в ту же часть. Часть — твёрдое тело, поэтому от позы это не зависит."""
    dirs = sphere_dirs(600)
    removed = 0
    for o in parts.values():
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.normal_update()
        tree = BVHTree.FromBMesh(bm, epsilon=0.0)

        def shut(p):
            return all(tree.ray_cast(p, d)[0] is not None for d in dirs)

        dead = []
        for f in bm.faces:
            n = f.normal
            if not shut(f.calc_center_median() + n * 0.004):
                continue
            if all(shut(p + n * 0.004) and shut(p + n * 0.012) for p in face_samples(f)):
                dead.append(f)
        if dead:
            removed += len(dead)
            bmesh.ops.delete(bm, geom=dead, context="FACES")
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
            bm.to_mesh(o.data)
            o.data.update()
        bm.free()
    return removed


def enclosed_faces(parts):
    """Сколько осталось граней, которых не видно ни с одной стороны (то же правило, что drop_enclosed)."""
    dirs = sphere_dirs(600)
    total = 0
    for o in parts.values():
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.normal_update()
        tree = BVHTree.FromBMesh(bm, epsilon=0.0)
        for f in bm.faces:
            n = f.normal
            if all(all(tree.ray_cast(p + n * 0.004, d)[0] is not None for d in dirs) for p in face_samples(f)):
                total += 1
        bm.free()
    return total


def pose_parts(parts, art, on):
    """Пробная поза: части связаны иерархией скелета и повёрнуты вокруг точек вращения (on = False — покой)."""
    bpy.context.view_layer.update()
    for g, (parent, _) in art.rig.items():
        if parent and parts[g].parent is None:
            parts[g].parent = parts[parent]
            parts[g].matrix_parent_inverse = parts[parent].matrix_world.inverted()
    for g, (rot, off) in art.pose.items():
        parts[g].rotation_euler = [math.radians(d) for d in rot] if on else (0, 0, 0)
        base = parts[g].get("rest", None)
        if base is None:
            parts[g]["rest"] = list(parts[g].location)
            base = parts[g]["rest"]
        parts[g].location = Vector(base) + (Vector(off) if on else Vector())
    bpy.context.view_layer.update()


def world_bounds(objs):
    co = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    return Vector([min(c[i] for c in co) for i in range(3)]), Vector([max(c[i] for c in co) for i in range(3)])


def only_visible(keep):
    hidden = [o for o in bpy.context.scene.objects if o.type == "MESH" and o not in keep and o.name != "Floor"]
    for o in hidden:
        o.hide_render = True
    return hidden


def show_all(hidden):
    for o in hidden:
        o.hide_render = False


def import_vase():
    """Эталон D39 — ваза v13 (assets/models/ArtV13_Vase.fbx и её карты), только для кадра сравнения."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(REPO, "assets", "models", "ArtV13_Vase.fbx"))
    objs = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    mat = bpy.data.materials.new("V13")
    mat.use_nodes = True
    mat.use_backface_culling = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.5
    tex = os.path.join(REPO, "assets", "textures", "art")
    col = nt.nodes.new("ShaderNodeTexImage")
    col.image = bpy.data.images.load(os.path.join(tex, "v13_vase_color.png"))
    nt.links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    nrm = nt.nodes.new("ShaderNodeTexImage")
    nrm.image = bpy.data.images.load(os.path.join(tex, "v13_vase_normal.png"))
    nrm.image.colorspace_settings.name = "Non-Color"
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(nrm.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(mat)
    return objs


def pad(collection, x, y=0.0):
    mat = bpy.data.materials.get("PadMat") or bpy.data.materials.new("PadMat")
    mat.use_nodes = True
    next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (
        *S.lin("C9A15A"), 1)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(PAD, PAD, PAD_H), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(x, y, PAD_H / 2), verts=bm.verts)
    me = bpy.data.meshes.new("Pad")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new("Pad", me)
    collection.objects.link(o)
    return o


def clear_studio():
    """Убрать студию прошлого кадра (S.Preview): свет, камеру и пол — у каждого существа своя студия."""
    for o in list(bpy.context.scene.objects):
        if o.type in ("LIGHT", "CAMERA") or o.name.startswith("Floor"):
            bpy.data.objects.remove(o, do_unlink=True)


def run(items, repo, shots, models, texdir, quick=False, report_name="report.json"):
    """Собрать существа items = [(id, функция, название, редкость)]: запекание (кроме quick), FBX, rig.json, кадры."""
    global REPO, SHOTS, MODELS, TEXDIR, QUICK
    REPO, SHOTS, MODELS, TEXDIR, QUICK = repo, shots, models, texdir, quick
    for d in (SHOTS, MODELS, TEXDIR):
        os.makedirs(d, exist_ok=True)
    ITEMS = items
    bpy.ops.wm.read_factory_settings(use_empty=True)
    collection = bpy.data.collections.new("Oasis")
    bpy.context.scene.collection.children.link(collection)
    report = {}
    for item_id, make, title, rarity in ITEMS:
        art = make()
        obj = art.build(collection)
        rc = rig_check(art)
        if rc["missing"] or rc["bad_parent"] or len(rc["roots"]) != 1:
            raise ValueError(f"{item_id}: скелет {rc}")
        if getattr(art, "marks", None):
            order = list(dict.fromkeys(art.face_groups)).index(art.marks["group"])
            pivot = art.rig[art.marks["group"]][1]
            face_marks(art, (-pivot[0], -pivot[2]) if QUICK else (order * 10 * S.RING["step"], 0.0))
        uv = {}
        if not QUICK:
            explode(obj, art, 1)
            S.TEX = tex_size(rarity)
            uv = S.bake(obj, art, TEXDIR, item_id, **getattr(art, "bake_opts", {}))
            explode(obj, art, -1)
        lo, hi = S.bounds(obj)
        rep = {"title": title, "rarity": rarity, **art.stats, **{k: round(v, 3) for k, v in uv.items()},
               "size_blender_xyz": [round(hi[i] - lo[i], 2) for i in range(3)], "rig_parts": rc["parts"],
               "materials": len(obj.data.materials)}
        print("BUILD", item_id, json.dumps(rep, ensure_ascii=False), flush=True)

        # части с точками вращения
        if QUICK:
            parts = split_keep(obj, art, collection)
        else:
            parts = S.split_groups(obj, art, {g: Vector(art.rig[g][1]) for g in art.rig}, collection)
        rep["dropped_enclosed_faces"] = drop_enclosed(parts)
        for g in getattr(art, "transparent_parts", ()):  # полупрозрачные части (в игре — прозрачность MeshPart)
            me = parts[g].data
            for i, m in enumerate(me.materials):
                mm = m.copy()
                b = next((x for x in mm.node_tree.nodes if x.type == "BSDF_PRINCIPLED"), None)
                if b is not None:
                    b.inputs["Alpha"].default_value = 0.35
                mm.surface_render_method = "BLENDED"
                mm.use_backface_culling = True
                me.materials[i] = mm
        rep["transparent_parts"] = list(getattr(art, "transparent_parts", ()))
        bpy.context.view_layer.update()
        from joint_check import check_bends, check_joints  # правила анатомии D64: щели в суставах > 0.05 стада — ошибка
        rep["joint_issues"] = check_joints(parts, art.rig, gap=0.05) + check_bends(parts, art.rig)
        rep["meshes"] = len(parts)
        rep["tris_by_part"] = {g: len(o.data.polygons) and sum(len(p.vertices) - 2 for p in o.data.polygons)
                               for g, o in parts.items()}
        rep["tris_without_stand"] = sum(v for g, v in rep["tris_by_part"].items() if g != "Stand")
        rep["enclosed_faces"] = enclosed_faces(parts)
        if not QUICK:
            uvs = [l.uv for o in parts.values() for l in o.data.uv_layers.active.data]
            rep["uv_layers"] = sorted({len(o.data.uv_layers) for o in parts.values()})
            rep["uv_in_0_1"] = all(-1e-4 <= c <= 1 + 1e-4 for u in uvs for c in u)
            rep["texture"] = f"{S.TEX}×{S.TEX}, color + normal (шероховатость общая 0.5)"
            S.export_fbx([parts[g] for g in art.rig], os.path.join(MODELS, f"{item_id}.fbx"))
            rig_json(item_id, art, parts, os.path.join(MODELS, f"{item_id}.rig.json"))

        # — кадры: части связаны скелетом, повороты — вращением подставки (камера всегда спереди, к студии) —
        clear_studio()  # свет, камера и пол прошлого существа (иначе свет копится и кадры пересвечены)
        prev = S.Preview(collection)
        whole = list(parts.values())
        pose_parts(parts, art, False)
        root = parts["Stand"]
        hidden = only_visible(set(whole))
        lo, hi = world_bounds(whole)
        size = max(hi - lo)
        cz = (lo.z + hi.z) / 2
        cx, cy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
        dist = 2.6 * size + 1.0
        shots = {}

        def shot(name, eye, target, lens, res):
            shots[name] = prev.shot(os.path.join(SHOTS, f"{item_id}_{name}.png"), eye, target, lens, res)

        def turn(deg):
            root.rotation_euler = (0, 0, math.radians(deg))
            bpy.context.view_layer.update()

        shot("hero", (cx - 0.6 * dist, cy - 0.86 * dist, cz + 0.5 * size), (cx, cy, cz - 0.04 * size), 75, (1600, 1600))
        for name, deg in (("front", 0), ("side", -90), ("side_r", 90), ("back", 180)):
            turn(deg)
            shot(name, (0, -dist, cz + 0.12 * size), (0, 0, cz), 75, (1000, 1200))
        turn(0)
        shot("top", (cx, cy - 0.01, cz + 0.95 * dist), (cx, cy, cz), 75, (1200, 1200))
        if hasattr(art, "face"):  # новые существа: лицо спереди чуть сверху; точка лица задаётся в модели
            f = Vector(art.face)
            shot("face", (f.x - 0.8, f.y - 3.0, f.z + 0.55), (f.x - 0.1, f.y, f.z + 0.05), 85, (1400, 1100))
        else:
            head = parts["Head"].matrix_world.translation
            shot("face", (head.x - 0.9, head.y - 3.6, head.z + 0.9), (head.x - 0.15, head.y - 0.5, head.z + 0.7), 85,
                 (1400, 1100))
        if hasattr(art, "closeup"):  # крупно контуры D39: камера и точка на крупной поверхности с квадратами
            shot("texture", art.closeup[0], art.closeup[1], 105, (1400, 1100))
        else:
            body = parts["Body"].matrix_world.translation
            shot("texture", (body.x - 1.2, body.y - 2.2, body.z + 1.0), (body.x - 0.5, body.y - 0.4, body.z + 0.5), 105,
                 (1400, 1100))
        pose_parts(parts, art, True)
        shot("pose", (cx - 0.6 * dist, cy - 0.86 * dist, cz + 0.5 * size), (cx, cy, cz - 0.04 * size), 75, (1400, 1400))
        pose_parts(parts, art, False)
        show_all(hidden)

        # масштаб: на площадке 3.7 × 3.7 рядом с манекеном Roblox (5.2 стада) и эталоном D39 — вазой v13
        root.location.z += PAD_H
        pads = [pad(collection, 0.0)]
        vase = import_vase()
        vlo, vhi = world_bounds(vase)
        for o in vase:
            o.location += Vector((-4.3 - (vlo.x + vhi.x) / 2, -(vlo.y + vhi.y) / 2, PAD_H - vlo.z))
        bpy.context.view_layer.update()
        vase_pad = pad(collection, -4.3)
        S.mannequin(collection, 4.0)
        men = [o for o in bpy.context.scene.objects if o.name.startswith("Mannequin")]
        hidden = only_visible(set(whole) | set(vase) | set(pads) | {vase_pad} | set(men))
        prev.aim_lights(Vector((0, 0, 0)))
        shot("scale", (0.4, -17.5, 6.5), (-0.2, 0, 2.4), 50, (2000, 1000))
        # сравнение с вазой v13 крупно: одинаковый объектив и расстояние до поверхности (2.6 стада)
        vmid = (vlo + vhi) / 2 + Vector((-4.3 - (vlo.x + vhi.x) / 2, -(vlo.y + vhi.y) / 2, PAD_H - vlo.z))
        vfront = vmid.y - (vhi.y - vlo.y) / 2
        for o in whole:
            o.hide_render = True
        shot("vase_close", (vmid.x - 1.0, vfront - 2.4, vmid.z + 0.7), (vmid.x - 0.3, vfront, vmid.z + 0.3), 105, (1400, 1100))
        for o in whole:
            o.hide_render = False
        # как в игре: игрок (манекен) перед существом, камера Roblox за его спиной, кадр телефона 844 × 390
        for o in vase + [vase_pad]:
            o.hide_render = True
        for o in men:
            o.location += Vector((-6.2, -6.0, 0))  # игрок слева впереди, в 6 стадах от существа
        shot("ingame_phone", (0.2, -18.5, 9.0), (-0.6, -1.0, 2.0), 32, (844, 390))
        for o in men:
            o.location -= Vector((-6.2, -6.0, 0))
        show_all(hidden)
        for o in vase + pads + [vase_pad] + men:
            o.hide_render = True
        root.location.z -= PAD_H

        if not QUICK:
            bpy.ops.wm.save_as_mainfile(filepath=os.path.join(MODELS, f"{item_id}.blend"), copy=True)
        rep["shots"] = {k: os.path.relpath(v, REPO) for k, v in shots.items()}
        report[item_id] = rep

    with open(os.path.join(SHOTS, report_name), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("CREATURES_OK " + json.dumps({k: v["tris"] for k, v in report.items()}, ensure_ascii=False), flush=True)
    return report
