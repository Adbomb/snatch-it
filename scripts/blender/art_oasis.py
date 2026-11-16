"""Коллекция босса 4 «Сфинкс-лежебока» — «Живой оазис» + «Загадки Сфинкса» (каталог владельца 2026-11-11), стиль D39.

Сейчас — одна эталонная модель по указанию владельца (2026-11-12): №20 «Фенек-загадочник» (Rare). Остальные 29 — только
после утверждения эталона. Устройство — как у существ босса 3 (art_rats.py): детали D39 из art_style.py, подвижные
части (Art.group) с точками вращения для Motor6D (D18, D55), корень — подставка Stand (у живого существа в игре
скрыта), запекание цвета, окклюзии и нормалей в карты 1024², FBX из частей и скелет rig.json в осях Roblox.

Пишет assets/models/art/boss4/<id>.{fbx,rig.json,blend}, assets/textures/art/boss4/<id>_{color,normal}.png, а в папку
кадров — повороты, крупные планы, масштаб с манекеном Roblox (5.2 стада) и площадкой 3.7 × 3.7, кадр как в игре,
сравнение с эталоном D39 (ваза v13) и report.json.
Запуск: blender --background --factory-startup --python scripts/blender/art_oasis.py -- <репо> <кадры> [quick] [study] [id…]
quick — без запекания и экспорта (материалы сборки), для быстрых правок формы; study — FBX и карты не в assets, а в
<кадры>/study (сравнительные варианты).
FennecRiddler — исходная модель (v1). FennecRiddler_v2 — точечная полировка 2026-11-12 (та же геометрия, скелет и
точки вращения): тёмные отметины у глаз только рисунком в карте, чёткий профиль контура D39 и запекание с запасом
×4, веки, «?» медальона, кубик и мелкое золото — цветом. FennecRiddler_v2_nomarks — то же без отметин (для A/B).
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

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, SHOTS = os.path.abspath(argv[0]), os.path.abspath(argv[1])
QUICK = "quick" in argv[2:]
STUDY = "study" in argv[2:]
ONLY = [x for x in argv[2:] if x not in ("quick", "study")]
MODELS = os.path.join(REPO, "assets", "models", "art", "boss4")
TEXDIR = os.path.join(REPO, "assets", "textures", "art", "boss4")
if STUDY:
    MODELS = TEXDIR = os.path.join(SHOTS, "study")
PAD, PAD_H = 3.7, 0.12  # площадка существа у босса и её толщина в кадре масштаба
for d in (SHOTS, MODELS, TEXDIR):
    os.makedirs(d, exist_ok=True)


# ── Общие детали (как у существ босса 3) ─────────────────────────────────────────────────────────────────────


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
    """Круглая подставка-витрина цвета редкости (как у существ босса 3). Возвращает высоту верха."""
    part(a, "Stand", None, (0, 0, 0))
    body, rim = {"common": ("standC", "standCL"), "rare": ("standR", "standGold")}[rarity]
    a.paint("standC", "23606B", rings=True)
    a.paint("standCL", "5CC2CC")
    a.paint("standR", "6B3FB8", rings=True)
    a.paint("standGold", "F2C230", rings=True)
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
    """Подставка Common (бирюзовая со светлой каймой, как у босса 3); мелкое золото существа — гладкое."""
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


def cactus_boxer():
    a = S.Art("Art_CactusBoxer", ring_z0=1.3)
    d39v2(a)
    a.paint("green", "43B54C", rings=True)
    for key, code in (("rib", "2A8A3B"), ("spine", "FFF0C8"), ("glove", "E53935"), ("gloveD", "B3261E"),
                      ("white", "FFFDF4"), ("dark", "231816"), ("glint", "FFFFFF"), ("mouth", "5A1A20"),
                      ("petal", "FF6FAE"), ("petalD", "E0458C"), ("yellow", "FFD23F"), ("teal", "16B3A3"),
                      ("lace", "E53935"), ("lid", "2F9A3E")):
        a.paint(key, code)
    t = common_stand(a, 1.45)
    # бочонок: четыре яруса-восьмигранника (широкое брюшко)
    part(a, "Body", "Stand", (0, 0, t + 0.4))
    secs = [(S.octagon(-0.6, 0.6, -0.52, 0.52, 0.2), t + 0.36, t + 0.6),
            (S.octagon(-0.8, 0.8, -0.68, 0.68, 0.27), t + 0.58, t + 1.52),
            (S.octagon(-0.7, 0.7, -0.6, 0.6, 0.23), t + 1.5, t + 1.96),
            (S.octagon(-0.5, 0.5, -0.42, 0.42, 0.16), t + 1.94, t + 2.12)]
    for pts, z0, z1 in secs:
        a.prism("green", pts, z0, z1)
    # рёбра — тёмные брусья по углам ярусов (на брюшке прерываются поясом), на рёбрах кремовые колючки
    for (pts, z0, z1), spans, spines in ((secs[1], ((t + 0.62, t + 0.86), (t + 1.06, t + 1.48)), (t + 0.74, t + 1.27)),
                                         (secs[2], ((t + 1.54, t + 1.92),), (t + 1.73,))):
        for x, y in pts:
            ang = math.degrees(math.atan2(y, x))
            for s0, s1 in spans:
                a.box("rib", x - 0.05, x + 0.05, y - 0.05, y + 0.05, s0, s1, matrix=tilt((x, y, 0), "Z", ang))
            d = Vector((x, y, 0)).normalized()
            for z in spines:
                q = Vector((x, y, z)) + d * 0.07
                a.box("spine", q.x - 0.035, q.x + 0.035, q.y - 0.035, q.y + 0.035, z - 0.035, z + 0.035, bevel=0,
                      matrix=tilt((q.x, q.y, 0), "Z", ang))
    # пояс чемпиона: золотое кольцо, табличка, бирюзовый камень
    a.frame("gold", S.octagon(-0.84, 0.84, -0.72, 0.72, 0.285), 0.07, t + 0.86, t + 1.06, axis="z", bevel=0)
    a.box("gold", -0.24, 0.24, -0.8, -0.7, t + 0.8, t + 1.12)
    gem(a, "teal", (0, -0.82, t + 0.96), 0.17)
    # лицо: глаза на верхнем ярусе, решительные брови, ухмылка с белой капой на брюшке
    yf = -0.6
    for s in (-1, 1):
        round_eye(a, (s * 0.24, yf, t + 1.66), 0.16, look=(-0.15 * s, -0.1), pupil=0.58, lid=0.24, lid_key="lid")
        bar(a, "rib", (s * 0.44, yf - 0.06, t + 1.92), (s * 0.08, yf - 0.06, t + 1.82), 0.11, 0.08)
    a.box("mouth", -0.2, 0.3, -0.71, -0.66, t + 1.24, t + 1.37, bevel=0)  # кривая ухмылка: правый уголок вверх
    a.box("white", -0.16, 0.26, -0.725, -0.7, t + 1.305, t + 1.36, bevel=0)  # белая капа
    bar(a, "mouth", (0.27, -0.69, t + 1.32), (0.45, -0.69, t + 1.5), 0.08, 0.05, bevel=0)
    # ножки в белых боксёрках с красной шнуровкой
    for s, name in ((-1, "LegL"), (1, "LegR")):
        part(a, name, "Body", (s * 0.32, 0, t + 0.4))
        a.box("green", s * 0.18, s * 0.46, -0.14, 0.14, t + 0.18, t + 0.42)
        a.box("white", s * 0.13, s * 0.51, -0.36, 0.2, t, t + 0.22)
        a.box("lace", s * 0.24, s * 0.4, -0.38, -0.34, t + 0.05, t + 0.18, bevel=0)
    # левая рука — выпад вперёд
    part(a, "ArmL", "Body", (-0.74, -0.1, t + 1.25))
    bar(a, "green", (-0.7, -0.1, t + 1.25), (-0.98, -0.5, t + 1.38), 0.22, 0.2)
    gx, gz = -1.02, t + 1.42
    a.box("white", gx - 0.22, gx + 0.22, -0.62, -0.48, gz - 0.21, gz + 0.21)
    a.prism("glove", S.octagon(gx - 0.31, gx + 0.31, gz - 0.29, gz + 0.29, 0.11), -1.16, -0.6, axis="y")
    a.box("glove", gx + 0.22, gx + 0.38, -1.0, -0.74, gz - 0.06, gz + 0.16)
    a.box("gloveD", gx - 0.26, gx + 0.26, -1.19, -1.14, gz + 0.03, gz + 0.12, bevel=0)
    # правая рука — защита у подбородка
    part(a, "ArmR", "Body", (0.74, -0.1, t + 1.25))
    bar(a, "green", (0.7, -0.1, t + 1.25), (0.88, -0.58, t + 1.42), 0.22, 0.2)
    gx, gy, gz = 0.86, -0.8, t + 1.72
    a.box("white", gx - 0.21, gx + 0.21, gy - 0.2, gy + 0.2, gz - 0.42, gz - 0.28)
    a.prism("glove", S.octagon(gx - 0.29, gx + 0.29, gy - 0.27, gy + 0.27, 0.1), gz - 0.3, gz + 0.3)
    a.box("glove", gx - 0.38, gx - 0.2, gy - 0.26, gy, gz - 0.12, gz + 0.1)
    a.box("gloveD", gx - 0.25, gx + 0.25, gy - 0.3, gy - 0.25, gz + 0.06, gz + 0.14, bevel=0)
    # цветок на макушке
    part(a, "Flower", "Body", (0, 0, t + 2.1))
    a.box("rib", -0.05, 0.05, -0.05, 0.05, t + 2.08, t + 2.24, bevel=0)
    petals(a, (0, 0, t + 2.24), 6, 0.3, 0.2, ("petal", "petalD"), "yellow", 0.14, spin=15)
    a.face = (0, yf, t + 1.55)
    a.closeup = ((-1.7, -2.3, t + 0.95), (-0.62, -0.5, t + 0.75))
    a.pose = {"ArmL": ((0, 0, -18), (0, -0.12, 0)), "ArmR": ((20, 0, 0), (0, 0, 0)), "Flower": ((0, 18, 0), (0, 0, 0.1)),
              "Body": ((0, 0, 8), (0, 0, 0)), "LegL": ((-14, 0, 0), (0, 0, 0))}
    return a


# ── 2. Фенек-лопоух: крошечный лисёнок-малыш сидит, стесняется; уши больше головы, правое торчит, левое завалилось
#       набок; огромные круглые глаза смотрят вниз, бровки домиком, румянец; бледно-песочный мех, коралловые уши
#       изнутри; хвост обвит вокруг лапок. Не фенек №20 (рыжий, взрослый, хитрый прищур, кубик) и не Fennekin (без
#       рыжих пучков в ушах) ──────────────────────────────────────────────────────────────────────────────────────────


def floppy_fennec():
    a = S.Art("Art_FloppyFennec", ring_z0=1.2)
    d39v2(a)
    a.paint("fur", "E9BE6C", rings=True)
    for key, code in (("cream", "FFF2D6"), ("earIn", "FF7A66"), ("brow", "C98A3C"), ("nose", "3A2626"),
                      ("cheek", "FFA0A0"), ("white", "FFFDF4"), ("dark", "2A1E1E"), ("glint", "FFFFFF"),
                      ("mouth", "6B2A2A")):
        a.paint(key, code)
    t = common_stand(a, 1.3)
    # туловище-грушка: бёдра, грудка с манишкой, передние лапки вместе, задние в стороны
    part(a, "Body", "Stand", (0, 0.05, t + 0.15))
    a.prism("fur", S.octagon(-0.52, 0.52, -0.4, 0.5, 0.2), t + 0.12, t + 0.6)
    a.prism("fur", S.octagon(-0.4, 0.4, -0.32, 0.38, 0.15), t + 0.58, t + 1.02)
    a.box("cream", -0.24, 0.24, -0.36, -0.26, t + 0.6, t + 0.98)
    for s in (-1, 1):
        bar(a, "fur", (s * 0.13, -0.3, t + 0.8), (s * 0.12, -0.44, t + 0.24), 0.14, 0.13)
        a.box("cream", s * 0.03, s * 0.21, -0.56, -0.32, t + 0.1, t + 0.26)
        a.box("cream", s * 0.3, s * 0.54, -0.52, -0.24, t + 0.1, t + 0.22)
    # голова-малыш: крупнее туловища, пушистые щёчки, светлая маска, короткая мордочка с носиком
    part(a, "Head", "Body", (0, -0.02, t + 1.0))
    a.prism("fur", S.octagon(-0.56, 0.56, -0.5, 0.42, 0.2), t + 0.98, t + 1.76)
    a.prism("fur", S.octagon(-0.42, 0.42, -0.38, 0.3, 0.14), t + 1.74, t + 1.86)
    for s in (-1, 1):
        a.box("cream", s * 0.5, s * 0.63, -0.4, -0.04, t + 1.0, t + 1.24)
    a.box("cream", -0.34, 0.34, -0.55, -0.48, t + 1.0, t + 1.3)
    a.frustum("cream", (-0.19, 0.19, t + 1.06, t + 1.3), (-0.09, 0.09, t + 1.12, t + 1.24), -0.54, -0.74, axis="y")
    a.box("nose", -0.07, 0.07, -0.79, -0.72, t + 1.17, t + 1.27)
    a.box("glint", -0.045, -0.005, -0.8, -0.785, t + 1.22, t + 1.255, bevel=0)
    a.box("mouth", -0.07, 0.07, -0.58, -0.54, t + 1.04, t + 1.07, bevel=0)
    for s in (-1, 1):
        round_eye(a, (s * 0.27, -0.5, t + 1.49), 0.17, look=(-0.35, -0.6), pupil=0.66)
        bar(a, "brow", (s * 0.42, -0.53, t + 1.72), (s * 0.14, -0.53, t + 1.78), 0.06, 0.05)
        a.box("cheek", s * 0.22, s * 0.32, -0.58, -0.54, t + 1.12, t + 1.2, bevel=0)
    # уши: правое торчит чуть наружу; левое у основания отклонено, выше сгиба завалилось вниз-наружу
    base = Vector((0.3, -0.02, t + 1.78))
    part(a, "EarR", "Head", tuple(base))
    with_matrix(a, Matrix.Translation(base) @ Matrix.Rotation(math.radians(14), 4, "Y"))
    a.frustum("fur", (-0.32, 0.32, -0.09, 0.09), (-0.04, 0.04, -0.09, 0.03), -0.04, 1.36)
    a.frustum("earIn", (-0.23, 0.23, -0.12, -0.07), (-0.025, 0.025, -0.12, -0.07), 0.08, 1.18)
    with_matrix(a, None)
    base = Vector((-0.3, -0.02, t + 1.78))
    part(a, "EarL", "Head", tuple(base))
    lower = Matrix.Translation(base) @ Matrix.Rotation(math.radians(-24), 4, "Y")
    with_matrix(a, lower)
    a.frustum("fur", (-0.32, 0.32, -0.09, 0.09), (-0.21, 0.21, -0.09, 0.07), -0.04, 0.6)
    a.frustum("earIn", (-0.23, 0.23, -0.12, -0.07), (-0.14, 0.14, -0.12, -0.07), 0.08, 0.58)
    fold = lower @ Matrix.Translation((0, 0, 0.54)) @ Matrix.Rotation(math.radians(-118), 4, "Y")
    with_matrix(a, fold)
    a.box("fur", -0.205, 0.205, -0.08, 0.06, -0.11, 0.09, bevel=0)  # сгиб (чуть утоплен: без общих граней)
    a.frustum("fur", (-0.21, 0.21, -0.1, 0.07), (-0.03, 0.03, -0.1, 0.0), 0.06, 0.78)
    a.frustum("earIn", (-0.14, 0.14, -0.13, -0.08), (-0.02, 0.02, -0.13, -0.08), 0.06, 0.66)
    with_matrix(a, None)
    # хвост: пушистый, обвит вокруг правой задней лапки к передним, кончик светлый
    part(a, "Tail", "Body", (0.38, 0.3, t + 0.2))
    chain(a, "fur", [(0.38, 0.3, t + 0.19), (0.74, -0.05, t + 0.18), (0.62, -0.52, t + 0.18), (0.18, -0.74, t + 0.18)],
          [0.3, 0.34, 0.3], tip_key="cream")
    a.face = (0, -0.5, t + 1.4)
    a.closeup = ((-1.5, -2.0, t + 1.1), (-0.4, -0.3, t + 0.5))
    a.pose = {"EarL": ((0, 20, 0), (0, 0, 0)), "EarR": ((0, -12, 0), (0, 0, 0)), "Head": ((0, -12, 10), (0, 0, 0)),
              "Tail": ((0, 0, -14), (0, 0, 0))}
    return a


# ── 3. Перекати-поле-бегун: шар из толстых соломенных прутьев (кольца в разные стороны и торчащие веточки), внутри
#       тёмное ядро с испуганными глазами — косятся назад; длинные ножки-прутики бегут в красных кедах; фиолетовый
#       цветок застрял в прутьях, капля пота. Шар крутится отдельно от ядра (глаза неподвижны). Не Bramblin — ноги ─────


def tumbleweed_runner():
    a = S.Art("Art_TumbleweedRunner", ring_z0=1.7)
    d39v2(a)
    a.paint("core", "5A3E2A", rings=True)
    for key, code in (("straw", "E2B65A"), ("strawD", "B8893A"), ("twig", "C9963F"), ("boot", "E53935"),
                      ("white", "FFFDF4"), ("dark", "1E1612"), ("glint", "FFFFFF"), ("mouth", "2A0E0E"),
                      ("petal", "9B5CE0"), ("petalD", "7B3FC4"), ("yellow", "FFD23F"), ("sweat", "7FD3FF")):
        a.paint(key, code)
    t = common_stand(a, 1.4)
    c = Vector((0, 0, t + 1.5))
    # ядро: ярусы-восьмигранники с широкой передней гранью; лицо — испуганные глаза-плошки, бровки домиком, рот «о»
    part(a, "Body", "Stand", tuple(c))
    for h, z0, z1 in ((0.24, -0.5, -0.38), (0.38, -0.4, -0.26), (0.47, -0.28, -0.12), (0.5, -0.14, 0.14),
                      (0.47, 0.12, 0.28), (0.38, 0.26, 0.4), (0.24, 0.38, 0.5)):
        a.prism("core", S.octagon(-h, h, -h, h, h * 0.3), c.z + z0, c.z + z1)
    for s in (-1, 1):
        round_eye(a, (s * 0.2, -0.49, c.z + 0.02), 0.15, look=(0.75, 0.25), pupil=0.38, depth=0.04)
        bar(a, "straw", (s * 0.34, -0.51, c.z + 0.21), (s * 0.08, -0.51, c.z + 0.25), 0.06, 0.05)
    disc(a, "mouth", 0, c.z - 0.2, 0.07, -0.52, -0.46, n=8, axis="y", bevel=0)
    a.box("sweat", 0.44, 0.52, -0.46, -0.38, c.z + 0.3, c.z + 0.42, bevel=0)
    a.box("sweat", 0.455, 0.505, -0.445, -0.395, c.z + 0.42, c.z + 0.48, bevel=0)
    # ноги-прутики: левая шагнула вперёд, правая отброшена назад; красные кеды с белой подошвой
    part(a, "LegR", "Body", (0.22, 0.0, c.z - 0.45))
    knee = Vector((0.42, -0.36, t + 0.72))
    bar(a, "twig", (0.22, 0.0, c.z - 0.45), tuple(knee), 0.19, 0.18)
    bar(a, "twig", tuple(knee), (0.46, -0.52, t + 0.26), 0.18, 0.17)
    a.box("twig", knee.x - 0.11, knee.x + 0.11, knee.y - 0.11, knee.y + 0.11, knee.z - 0.11, knee.z + 0.11, bevel=0)
    a.box("boot", 0.27, 0.65, -0.96, -0.34, t + 0.06, t + 0.38)
    a.box("white", 0.25, 0.67, -1.0, -0.31, t, t + 0.08)
    a.box("white", 0.38, 0.54, -0.68, -0.42, t + 0.37, t + 0.41, bevel=0)
    part(a, "LegL", "Body", (-0.22, 0.0, c.z - 0.45))
    knee = Vector((-0.44, 0.24, t + 0.82))
    ankle = Vector((-0.56, 0.64, t + 0.96))
    bar(a, "twig", (-0.22, 0.0, c.z - 0.45), tuple(knee), 0.19, 0.18)
    bar(a, "twig", tuple(knee), tuple(ankle), 0.18, 0.17)
    a.box("twig", knee.x - 0.11, knee.x + 0.11, knee.y - 0.11, knee.y + 0.11, knee.z - 0.11, knee.z + 0.11, bevel=0)
    m = Matrix.Translation(ankle) @ Matrix.Rotation(math.radians(70), 4, "X")
    a.box("boot", -0.19, 0.19, -0.6, 0.04, -0.32, 0.0, matrix=m)
    a.box("white", -0.21, 0.21, -0.64, 0.07, -0.38, -0.3, matrix=m)
    # шар из прутьев (v2, правка владельца 2026-11-13: прутья не закрывают лицо ни спереди, ни под углом): кольцо по
    # контуру шара (вокруг оси взгляда) и малые кольца сбоку, сверху, снизу и сзади — ни одно не заходит в окно лица
    # (конус ~45° от взгляда); торчащие веточки — только по краям и сзади; цветок у края окна
    part(a, "Ball", "Body", tuple(c))
    rad = 0.84
    for n, off, spin, key in (((0.08, 1, 0.12), 0.0, 10, "straw"), ((1, 0.12, 0.1), 0.6, 20, "strawD"),
                              ((-1, 0.08, -0.12), 0.6, 35, "straw"), ((0.1, 0.18, 1), 0.55, 5, "strawD"),
                              ((-0.12, 0.1, -1), 0.55, 25, "straw"), ((0.55, 0.75, 0.45), 0.42, 15, "strawD"),
                              ((-0.6, 0.72, -0.4), 0.42, 40, "straw")):
        rot = Vector(n).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
        m = Matrix.Translation(c) @ rot @ Matrix.Translation((0, 0, off)) @ Matrix.Rotation(math.radians(spin), 4, "Z")
        a.frame(key, ngon(0, 0, math.sqrt(rad * rad - off * off), 8), 0.15, -0.075, 0.075, axis="z", bevel=0, matrix=m)
    for d in ((0.95, 0.25, 0.35), (-0.9, 0.35, 0.45), (0.35, 0.65, 0.75), (-0.45, 0.55, -0.75), (0.75, 0.5, -0.5),
              (0.1, 0.95, 0.35), (-0.95, 0.2, -0.35), (0.72, -0.4, 0.57), (-0.7, -0.42, -0.58)):
        d = Vector(d).normalized()
        bar(a, "twig", tuple(c + d * 0.72), tuple(c + d * 1.04), 0.14, 0.13)
    # по прутику поперёк окна — над бровями и под ртом: ядро «внутри шара», лицо открыто
    bar(a, "straw", tuple(c + Vector((-0.5, -0.56, 0.47))), tuple(c + Vector((0.46, -0.58, 0.53))), 0.14, 0.13)
    bar(a, "strawD", tuple(c + Vector((-0.44, -0.6, -0.5))), tuple(c + Vector((0.5, -0.56, -0.44))), 0.14, 0.13)
    fd = Vector((0.45, -0.35, 0.82)).normalized()
    bar(a, "strawD", tuple(c + fd * 0.7), tuple(c + fd * 0.92), 0.08, 0.08)
    petals(a, tuple(c + fd * 0.94), 5, 0.17, 0.13, ("petal", "petalD"), "yellow", 0.09, normal=tuple(fd), lift=12)
    a.face = (0, -0.5, c.z)
    a.closeup = ((-1.4, -2.2, c.z + 0.5), (-0.1, -0.5, c.z))
    a.pose = {"Ball": ((35, 0, 20), (0, 0, 0)), "LegR": ((-28, 0, 0), (0, 0, 0)), "LegL": ((24, 0, 0), (0, 0, 0)),
              "Body": ((-10, 0, 0), (0, 0, 0))}
    return a


# ── 4. Верблюжонок-фляга: малыш на длинных ножках с узловатыми коленками; вместо горба — круглая походная фляга
#       (бирюзовая, красный ремешок по ободу, знак капли) с пробкой; большая голова повёрнута к игроку, сонные веки
#       с ресничками, жуёт, на губе капелька; хохолок, хвостик с кисточкой. Походная фляга с водой, не карманная ────


DROP = ["..#..",
        ".###.",
        ".###.",
        "#####",
        "#####",
        ".###."]


def canteen_camel():
    a = S.Art("Art_CanteenCamel", ring_z0=1.4)
    d39v2(a)
    a.paint("fur", "D9A35E", rings=True)
    for key, code in (("furD", "B9823F"), ("cream", "FFE6BF"), ("creamD", "F2CFA0"), ("hoof", "6B4630"), ("tuft", "8E5A2E"),
                      ("canteen", "1FB3A6"), ("canteenD", "128578"), ("drop", "D8FBFF"), ("cork", "9A6534"),
                      ("strap", "D63A3A"), ("white", "FFFDF4"), ("dark", "231816"), ("glint", "FFFFFF"),
                      ("mouth", "6B2A2A"), ("water", "6FD6FF"), ("cheek", "FFA0A0")):
        a.paint(key, code)
    t = common_stand(a, 1.45)
    zb = t + 0.92  # низ туловища; верблюжонок смотрит в −x, голова повёрнута к игроку (−y)
    part(a, "Body", "Stand", (0, 0, zb))
    a.prism("fur", S.octagon(zb - 0.04, zb + 0.56, -0.34, 0.34, 0.15), -0.62, 0.6, axis="x")
    a.frame("strap", S.octagon(zb - 0.08, zb + 0.6, -0.38, 0.38, 0.17), 0.06, -0.06, 0.08, axis="x", bevel=0)
    a.box("gold", -0.07, 0.09, -0.42, -0.36, zb + 0.12, zb + 0.3)
    bar(a, "fur", (-0.5, 0, zb + 0.3), (-0.74, -0.06, zb + 0.95), 0.3, 0.28)  # шея
    for x, y, name in ((-0.42, -0.2, "LegFL"), (-0.42, 0.2, "LegFR"), (0.42, -0.2, "LegBL"), (0.42, 0.2, "LegBR")):
        part(a, name, "Body", (x, y, zb))
        a.box("fur", x - 0.095, x + 0.095, y - 0.095, y + 0.095, t + 0.56, zb + 0.06)
        a.box("furD", x - 0.115, x + 0.115, y - 0.115, y + 0.115, t + 0.44, t + 0.6)
        a.box("fur", x - 0.08, x + 0.08, y - 0.08, y + 0.08, t + 0.1, t + 0.48)
        a.box("hoof", x - 0.12, x + 0.12, y - 0.13, y + 0.11, t, t + 0.12)
    # фляга вместо горба: бирюзовый диск, ремешок по ободу, знак капли, горлышко; пробка — своя часть
    cz = zb + 0.92
    part(a, "Canteen", "Body", (0.04, 0, zb + 0.52))
    disc(a, "canteen", 0.04, cz, 0.4, -0.2, 0.2, n=12, axis="y")
    a.frame("strap", ngon(0.04, cz, 0.43, 12), 0.07, -0.13, 0.13, axis="y", bevel=0)
    pixel_boxes(a, "drop", DROP, 0.055, 0.04 - 0.1375, cz + 0.165, -0.23, -0.19)
    a.box("canteenD", -0.06, 0.14, -0.1, 0.1, cz + 0.36, cz + 0.5)
    part(a, "Cork", "Canteen", (0.04, 0, cz + 0.5))
    a.frustum("cork", (-0.06, 0.14, -0.09, 0.09), (-0.09, 0.17, -0.12, 0.12), cz + 0.48, cz + 0.66)
    # голова верблюжья: длинная морда с отвисшей верхней губой и ноздрями-щёлками; повёрнута на 35° к игроку; сонные
    # глаза с тяжёлыми веками и ресничками на лбу над мордой; жующая нижняя челюсть с капелькой; ушки висят; хохолок
    head = Vector((-0.86, -0.08, zb + 1.12))
    m_head = Matrix.Translation(head) @ Matrix.Rotation(math.radians(35), 4, "Z")  # в осях головы морда смотрит в −x
    part(a, "Head", "Body", (-0.76, -0.06, zb + 0.92))
    with_matrix(a, m_head)
    a.prism("fur", S.octagon(-0.22, 0.34, -0.26, 0.26, 0.07), -0.3, 0.26, axis="x")
    a.prism("cream", S.octagon(-0.26, 0.06, -0.19, 0.19, 0.07), -0.66, -0.22, axis="x")
    a.box("creamD", -0.7, -0.42, -0.205, 0.205, -0.29, -0.16)
    for s in (-1, 1):  # ноздри — тонкие светло-коричневые щёлки (тёмные читались вторыми глазами)
        a.box("furD", -0.675, -0.645, s * 0.06, s * 0.15, 0.015, 0.04, bevel=0,
              matrix=tilt((-0.66, s * 0.1, 0.03), "X", -s * 20))
        a.box("fur", 0.02, 0.2, s * 0.22, s * 0.4, 0.2, 0.3, matrix=tilt((0.1, s * 0.24, 0.25), "X", -s * 28))
        a.box("cream", 0.05, 0.17, s * 0.3, s * 0.38, 0.185, 0.205, bevel=0,
              matrix=tilt((0.1, s * 0.24, 0.25), "X", -s * 28))
    for x0, x1, y0, y1, z1 in ((-0.12, 0.0, -0.06, 0.04, 0.48), (-0.04, 0.08, -0.03, 0.07, 0.54),
                               (0.04, 0.14, -0.08, 0.02, 0.46)):
        a.box("tuft", x0, x1, y0, y1, 0.31, z1)
    a.box("cheek", -0.2, -0.08, -0.28, -0.25, -0.07, 0.01, bevel=0)
    with_matrix(a, m_head @ Matrix.Rotation(math.radians(-90), 4, "Z"))  # оси глаза: −y глаза = −x головы
    for s in (-1, 1):
        eye(a, (s * 0.12, -0.3, 0.15 + 0.006 * (s > 0)), 0.18, 0.17, look=(0, -0.55), depth=0.05, lid=0.46,
            lid_key="furD")
        bar(a, "dark", (s * 0.19, -0.415, 0.16), (s * 0.245, -0.415, 0.11), 0.025, 0.02, bevel=0)
        bar(a, "dark", (s * 0.14, -0.425, 0.16), (s * 0.16, -0.425, 0.1), 0.025, 0.02, bevel=0)
    with_matrix(a, None)
    part(a, "Jaw", "Head", tuple(m_head @ Vector((-0.32, 0, -0.28))))
    with_matrix(a, m_head)
    a.box("cream", -0.62, -0.32, -0.12, 0.18, -0.38, -0.28)
    a.box("water", -0.52, -0.46, -0.23, -0.18, -0.37, -0.27, bevel=0)
    with_matrix(a, None)
    # хвостик с кисточкой
    part(a, "Tail", "Body", (0.6, 0, zb + 0.42))
    bar(a, "fur", (0.6, 0, zb + 0.42), (0.74, 0.02, zb + 0.1), 0.08, 0.08)
    a.box("tuft", 0.66, 0.84, -0.07, 0.11, zb - 0.1, zb + 0.13)
    a.face = tuple(m_head @ Vector((-0.45, 0, 0.0)))
    a.closeup = ((-0.4, -2.4, zb + 0.6), (0.2, -0.34, zb + 0.3))
    a.pose = {"Head": ((0, 0, -14), (0, 0, 0)), "Jaw": ((0, 0, 0), (0.05, 0, -0.03)), "Cork": ((0, 20, 0), (0, 0, 0.22)),
              "Tail": ((0, 30, 0), (0, 0, 0)), "LegFL": ((0, -14, 0), (0, 0, 0))}
    return a


# ── 5. Черепаха-бархан: низкая широкая черепашка-тихоня; панцирь — бархан-полумесяц из ступенчатых слоёв красного
#       песка (рога вперёд, крутой склон у головы, пологий сзади, слои — полосы ряби); из-под бархана выглядывает
#       сине-зелёная голова с большими робкими глазами и румянцем. Без деревьев и камней на панцире (не Torterra),
#       не №23 «Черепаха-остров» (там пальмы и лагуна) ───────────────────────────────────────────────────────────────


def _horn_tips(rx, ry, cy, ci, r):
    """Где эллипс (rx, ry) с центром (0, cy) выходит из круга с центром (0, ci) и радиусом r: параметры правого и левого
    рога и сама функция точки эллипса. Круг должен накрывать переднюю точку эллипса и не накрывать заднюю."""
    def ell(th):
        return Vector((rx * math.cos(th), cy + ry * math.sin(th)))

    def outside(th):
        return (ell(th) - Vector((0, ci))).length - r

    def cross(lo, hi):
        for _ in range(48):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if outside(mid) > 0 else (lo, mid)
        return lo

    return cross(math.pi / 2, -math.pi / 2), cross(math.pi / 2, 3 * math.pi / 2), ell


def _arc(ci, r, p_from, p_to, n):
    """Дуга окружности (центр (0, ci), радиус r) от точки p_from к p_to через верх (+y), n отрезков."""
    b0, b1 = math.atan2(p_from.y - ci, p_from.x), math.atan2(p_to.y - ci, p_to.x)
    return [Vector((r * math.cos(b0 + (b1 - b0) * k / n), ci + r * math.sin(b0 + (b1 - b0) * k / n)))
            for k in range(n + 1)]


def crescent(rx, ry, cy, ci, ri, n_out=16, n_in=8):
    """Бархан сверху: эллипс (rx, ry) с центром (0, cy) без круга с центром (0, ci) и радиусом ri — полумесяц рогами
    к −y (вогнутый крутой склон спереди)."""
    tr, tl, ell = _horn_tips(rx, ry, cy, ci, ri)
    outer = [ell(tr + (tl - tr) * k / n_out) for k in range(n_out + 1)]
    inner = _arc(ci, ri, outer[-1], outer[0], n_in)[1:-1]
    return [(p.x, p.y) for p in outer + inner]


def slip_band(rx, ry, cy, ci, r0, r1, n=8):
    """Крутой склон бархана — полоса между окружностями r0 < r1 (центр (0, ci)) внутри эллипса, от рога до рога."""
    tr0, tl0, ell = _horn_tips(rx, ry, cy, ci, r0)
    tr1, tl1, _ = _horn_tips(rx, ry, cy, ci, r1)
    front = _arc(ci, r0, ell(tl0), ell(tr0), n)
    back = _arc(ci, r1, ell(tl1), ell(tr1), n)
    return [(p.x, p.y) for p in front + list(reversed(back))]


def dune_turtle():
    a = S.Art("Art_DuneTurtle", ring_z0=0.6)
    d39v2(a)
    a.paint("duneA", "E07B48", rings=True)
    a.paint("duneB", "F2A766", rings=True)
    for key, code in (("skin", "3FA796"), ("skinD", "2C7F72"), ("rim", "B85C34"), ("nail", "FFF1D6"),
                      ("white", "FFFDF4"), ("dark", "1F2420"), ("glint", "FFFFFF"), ("cheek", "FF9EA6"),
                      ("mouth", "5A1A20")):
        a.paint(key, code)
    t = common_stand(a, 1.5)
    # край панциря и бархан-полумесяц (v2, правка владельца 2026-11-13: спереди был ступенчатой пирамидой). Как у
    # настоящего бархана: пологий светлый склон к хвосту тонкими слоями-рябью, острый гребень, тёмный вогнутый крутой
    # склон сразу за головой; рога длинные и низкие — тянутся вперёд по бокам головы; слои почти не сужаются по
    # бокам (купол, а не пирамида)
    part(a, "Body", "Stand", (0, 0.1, t + 0.3))
    a.prism("rim", S.octagon(-0.96, 0.96, -0.86, 0.92, 0.34), t + 0.24, t + 0.42)
    for k in range(7):
        front, back, rx = -1.05 + 0.09 * k, 1.05 - 0.16 * k, 1.06 - 0.012 * k * k
        cy, ry = (front + back) / 2, (back - front) / 2
        r0 = 0.85 + 0.012 * k  # крутой склон чуть отклоняется назад кверху
        z0, z1 = t + 0.38 + 0.14 * k, t + 0.54 + 0.14 * k
        a.extrude("duneB", crescent(rx, ry, cy, -1.15, r0 + 0.09), z0, z1, axis="z")
        # тёмная полоса крутого склона чуть выше слоя — острая кромка гребня (и без общих граней со слоем)
        a.extrude("duneA", slip_band(rx, ry, cy, -1.15, r0, r0 + 0.1), z0 + 0.005, z1 + 0.012, axis="z")
    # рога бархана: низкие сужающиеся «руки» от углов вперёд вокруг головы, ступенями вниз к кончику
    for s in (-1, 1):
        line = [Vector((s * 0.8, -0.56)), Vector((s * 0.79, -0.84)), Vector((s * 0.69, -1.06)), Vector((s * 0.52, -1.2))]
        half = (0.17, 0.14, 0.1, 0.05)
        for i, top in enumerate((0.58, 0.47, 0.37)):
            p0, p1 = line[i], line[i + 1]
            d = (p1 - p0).normalized()
            p1 = p1 + d * 0.03  # заходит в следующий отрезок: без щели и без общих торцов
            n = Vector((-d.y, d.x))
            pts = [p0 + n * half[i], p1 + n * half[i + 1], p1 - n * half[i + 1], p0 - n * half[i]]
            a.extrude("duneB", [(q.x, q.y) for q in pts], t + 0.26 + 0.004 * i, t + top, axis="z")
            # внутренняя сторона рога (к голове) — продолжение тёмного крутого склона, чуть выше и снаружи рога
            inner = n * -s
            w0, w1 = min(0.06, half[i] * 0.7), min(0.06, half[i + 1] * 0.7)
            b0, b1 = p0 + d * 0.006, p1 - d * 0.006  # торцы полосы не в плоскости торцов рога
            band = [b0 + inner * (half[i] + 0.01), b1 + inner * (half[i + 1] + 0.01), b1 + inner * (half[i + 1] - w1),
                    b0 + inner * (half[i] - w0)]
            a.extrude("duneA", [(q.x, q.y) for q in band], t + 0.265 + 0.004 * i, t + top + 0.012, axis="z")
    # ножки-тумбы с коготками
    for x, y, name in ((-0.9, -0.42, "LegFL"), (0.9, -0.42, "LegFR"), (-0.86, 0.6, "LegBL"), (0.86, 0.6, "LegBR")):
        part(a, name, "Body", (x * 0.85, y, t + 0.3))
        a.box("skin", x - 0.16, x + 0.16, y - 0.16, y + 0.16, t, t + 0.32)
        if y < 0:
            for dx in (-0.09, 0.0, 0.09):
                a.box("nail", x + dx - 0.035, x + dx + 0.035, y - 0.2, y - 0.14, t + 0.01, t + 0.07, bevel=0)
    part(a, "Tail", "Body", (0, 0.9, t + 0.3))
    a.frustum("skin", (-0.1, 0.1, 0.88, 1.0), (-0.03, 0.03, 1.1, 1.14), t + 0.2, t + 0.34)
    # голова выглядывает из-под крутого склона: большие робкие глаза вверх, румянец, улыбка
    part(a, "Head", "Body", (0, -0.5, t + 0.42))
    a.box("skin", -0.17, 0.17, -0.74, -0.3, t + 0.3, t + 0.62)
    hz = t + 0.8
    a.prism("skin", S.octagon(-0.36, 0.36, hz - 0.26, hz + 0.28, 0.12), -1.02, -0.56, axis="y")
    for s in (-1, 1):
        round_eye(a, (s * 0.17, -1.02, hz + 0.06), 0.14, look=(0.15 * s, 0.6), pupil=0.62, lid=0.22, lid_key="skinD")
        a.box("cheek", s * 0.21, s * 0.31, -1.05, -1.01, hz - 0.14, hz - 0.07, bevel=0)
    a.box("mouth", -0.09, 0.09, -1.05, -1.01, hz - 0.17, hz - 0.14, bevel=0)
    a.face = (0, -1.02, hz)
    a.closeup = ((1.3, -1.7, t + 1.7), (0.3, -0.1, t + 0.9))
    a.pose = {"Head": ((-12, 0, 10), (0, 0.15, -0.04)), "LegFL": ((-20, 0, 0), (0, 0, 0)), "LegBR": ((18, 0, 0), (0, 0, 0)),
              "Tail": ((0, 0, 25), (0, 0, 0))}
    return a


COMMON = [("CactusBoxer", cactus_boxer, "Кактус-боксёр", "Common"),
          ("FloppyFennec", floppy_fennec, "Фенек-лопоух", "Common"),
          ("TumbleweedRunner", tumbleweed_runner, "Перекати-поле-бегун", "Common"),
          ("CanteenCamel", canteen_camel, "Верблюжонок-фляга", "Common"),
          ("DuneTurtle", dune_turtle, "Черепаха-бархан", "Common")]


# ══ КОЛЛЕКЦИЯ №6–30 (кроме №20) — по каталогу владельца 2026-11-11 и эталону №20 v2 (D39V2), 2026-11-13 ══════════
# Владелец утвердил №1–5 и велел сделать остальные 25 сразу, без промежуточных утверждений. У каждого свой силуэт,
# морда и характер (спецификации — разбор каталога 2026-11-11); Neon, свечения и прозрачности нет (вода и стекло —
# непрозрачные блоки с бликами); детали не тоньше 0.12–0.16 стада.


def rare_stand(a, r):
    """Подставка Rare (фиолетовая с золотым ободом, как у №20); мелкое золото существа — гладкое."""
    t = stand(a, "rare", r)
    a.paint("gold", "F2C230")
    return t


def epic_stand(a, r=1.6):
    """Подставка Epic — гора золота ступенями с монетами по краю (как у Epic босса 3). Возвращает высоту верха."""
    part(a, "Stand", None, (0, 0, 0))
    a.paint("gold", "F2C230")
    a.paint("goldS", "F2C230", rings=True)
    a.paint("gold2", "C9921A")
    a.paint("goldL", "FFE07A")
    for key in ("gold2", "goldS", "goldL"):  # в игре подставку живого существа прячут — в карте ей меньше места
        a.uv_boost[key] = 0.4
    a.prism("gold2", S.octagon(-r, r, -r, r, r * 0.29), 0.0, 0.16)
    a.prism("goldS", S.octagon(-r + 0.18, r - 0.18, -r + 0.18, r - 0.18, r * 0.26), 0.14, 0.34)
    for x, y, ang in ((-r * 0.8, -r * 0.58, 20), (r * 0.78, -r * 0.62, -30), (r * 0.55, -r * 0.84, 45)):
        disc(a, "goldL", x, y, 0.15, 0.3, 0.37, n=6, bevel=0, matrix=tilt((x, y, 0.33), "Y", ang * 0.3))
    return 0.34


def legendary_stand(a, r=1.6):
    """Подставка Legendary (новая для коллекции, 2026-11-13): лазуритовый восьмигранник в золотой кайме, на нём
    золотой ярус; по углам — бирюзовые камни. Возвращает высоту верха."""
    part(a, "Stand", None, (0, 0, 0))
    a.paint("gold", "F2C230")
    a.paint("lapis", "2B4FC2", rings=True)
    a.paint("goldS", "F2C230", rings=True)
    a.paint("goldD", "C9921A")
    a.paint("goldSD", "C9921A")
    a.paint("gemT", "2ED1C0")
    for key in ("lapis", "goldS", "goldSD", "gemT"):  # в игре подставку прячут — в карте ей меньше места
        a.uv_boost[key] = 0.4
    a.prism("goldSD", S.octagon(-r, r, -r, r, r * 0.29), 0.0, 0.1)
    a.prism("lapis", S.octagon(-r + 0.06, r - 0.06, -r + 0.06, r - 0.06, r * 0.27), 0.08, 0.24)
    a.frame("goldSD", S.octagon(-r + 0.02, r - 0.02, -r + 0.02, r - 0.02, r * 0.28), 0.08, 0.2, 0.28, axis="z", bevel=0)
    a.prism("goldS", S.octagon(-r + 0.32, r - 0.32, -r + 0.32, r - 0.32, r * 0.22), 0.22, 0.36)
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


def umbrella_lizard():
    a = S.Art("Art_UmbrellaLizard", ring_z0=1.0)
    d39v2(a)
    a.paint("skin", "FF7A5C", rings=True)
    for key, code in (("skinD", "E85A3E"), ("belly", "FFE2C6"), ("red", "E53935"), ("white", "FFFDF4"),
                      ("dark", "2A1612"), ("glint", "FFFFFF"), ("tongue", "FF6FAE"), ("cheek", "FFB0A0"),
                      ("mouth", "5A1A20")):
        a.paint(key, code)
    t = common_stand(a, 1.4)
    part(a, "Body", "Stand", (0, 0.04, t + 0.6))
    a.prism("skin", S.octagon(-0.4, 0.4, -0.3, 0.34, 0.14), t + 0.44, t + 0.76)
    a.prism("skin", S.octagon(-0.33, 0.33, -0.26, 0.3, 0.12), t + 0.74, t + 1.36)
    a.box("belly", -0.2, 0.2, -0.315, -0.24, t + 0.52, t + 1.26)
    for s, name in ((-1, "LegL"), (1, "LegR")):  # бег: левая нога вперёд, правая назад
        part(a, name, "Body", (s * 0.22, 0.02, t + 0.56))
        fy = -0.16 if s < 0 else 0.2
        a.box("skin", s * 0.1, s * 0.34, fy - 0.12, fy + 0.12, t + 0.12, t + 0.58)
        a.box("skinD", s * 0.06, s * 0.38, fy - 0.36, fy + 0.12, t, t + 0.13)
        for dx in (0.1, 0.22, 0.34):
            a.box("belly", s * dx - 0.035, s * dx + 0.035, fy - 0.44, fy - 0.35, t, t + 0.08, bevel=0)
    for s, name in ((-1, "ArmL"), (1, "ArmR")):  # левая лапка машет, правая на поясе
        part(a, name, "Body", (s * 0.32, -0.04, t + 1.22))
        end = (s * 0.66, -0.14, t + 1.62) if s < 0 else (s * 0.58, -0.1, t + 0.98)
        bar(a, "skin", (s * 0.3, -0.04, t + 1.22), end, 0.14, 0.13)
        a.box("skinD", end[0] - 0.08, end[0] + 0.08, end[1] - 0.08, end[1] + 0.08, end[2] - 0.08, end[2] + 0.08)
    part(a, "Tail", "Body", (0, 0.3, t + 0.6))
    stripe_chain(a, ("skin", "skinD"), [(0, 0.3, t + 0.58), (0.32, 0.78, t + 0.32), (0.86, 0.92, t + 0.42),
                                        (1.08, 0.7, t + 0.8), (0.9, 0.5, t + 0.98)], 0.22, 0.2)
    # голова: глаза-бусины сверху по бокам с ресничками, мордочка, улыбка с высунутым языком, румянец
    part(a, "Head", "Body", (0, -0.02, t + 1.36))
    a.prism("skin", S.octagon(-0.34, 0.34, -0.36, 0.28, 0.12), t + 1.34, t + 1.84)
    a.frustum("skin", (-0.25, 0.25, t + 1.38, t + 1.62), (-0.17, 0.17, t + 1.42, t + 1.57), -0.35, -0.64, axis="y")
    for s in (-1, 1):
        round_eye(a, (s * 0.17, -0.36, t + 1.7), 0.13, look=(0.1 * s, 0.1), pupil=0.6)
        bar(a, "dark", (s * 0.27, -0.42, t + 1.79), (s * 0.33, -0.42, t + 1.82), 0.025, 0.02, bevel=0)
        bar(a, "dark", (s * 0.29, -0.425, t + 1.75), (s * 0.35, -0.425, t + 1.76), 0.025, 0.02, bevel=0)
        a.box("cheek", s * 0.2, s * 0.3, -0.395, -0.345, t + 1.44, t + 1.51, bevel=0)
        a.box("dark", s * 0.05, s * 0.1, -0.655, -0.63, t + 1.53, t + 1.56, bevel=0)
    a.box("mouth", -0.15, 0.15, -0.66, -0.62, t + 1.43, t + 1.47, bevel=0)
    a.box("tongue", 0.03, 0.13, -0.7, -0.62, t + 1.32, t + 1.45, bevel=0)
    # воротник-зонт за головой: восемь клиньев, наклон назад 25°, золотые наконечники и навершие
    part(a, "Frill", "Head", (0, 0.32, t + 1.56))
    m0 = Matrix.Translation((0, 0.36, t + 1.58)) @ Vector((0, -0.906, 0.423)).to_track_quat("Z", "Y").to_matrix().to_4x4()
    for i in range(8):
        a0, a1 = math.radians(i * 45 - 22.5 + 1), math.radians(i * 45 + 22.5 - 1)
        pts = [(0.16 * math.cos(a0), 0.16 * math.sin(a0)), (0.98 * math.cos(a0), 0.98 * math.sin(a0)),
               (1.02 * math.cos((a0 + a1) / 2), 1.02 * math.sin((a0 + a1) / 2)),
               (0.98 * math.cos(a1), 0.98 * math.sin(a1)), (0.16 * math.cos(a1), 0.16 * math.sin(a1))]
        a.prism("red" if i % 2 == 0 else "white", pts, -0.035 + 0.004 * (i % 2), 0.035 + 0.004 * (i % 2), matrix=m0)
        ang = math.radians(i * 45 - 22.5)
        q = Vector((0.99 * math.cos(ang), 0.99 * math.sin(ang), 0))
        a.box("gold", q.x - 0.045, q.x + 0.045, q.y - 0.045, q.y + 0.045, -0.06, 0.06, bevel=0,
              matrix=m0 @ Matrix.Translation(q) @ Matrix.Rotation(ang, 4, "Z") @ Matrix.Translation(-q))
    a.prism("gold", ngon(0, 0, 0.12, 8), 0.03, 0.12, matrix=m0 @ Matrix.Rotation(math.pi, 4, "X"))
    a.face = (0, -0.36, t + 1.6)
    a.closeup = ((-1.5, -2.0, t + 1.3), (-0.3, -0.3, t + 0.9))
    a.pose = {"Frill": ((15, 0, 0), (0, 0, 0)), "ArmL": ((0, 30, 0), (0, 0, 0)), "LegL": ((25, 0, 0), (0, 0, 0)),
              "LegR": ((-20, 0, 0), (0, 0, 0)), "Tail": ((0, 0, 20), (0, 0, 0)), "Head": ((0, 0, -10), (0, 0, 0))}
    return a


# ── 7. Арбуз-броненосец: полусвёрнутый броненосец, панцирь — полосы арбуза (тёмно- и светло-зелёные пояса), спереди
#       торец — красный срез арбуза с белой коркой и семечками, из-под него выглядывает розовая мордочка с ушками;
#       пугливый: глаза вверх, ушки торчком ─────────────────────────────────────────────────────────────────────────


def melon_armadillo():
    a = S.Art("Art_MelonArmadillo", ring_z0=0.8)
    d39v2(a)
    a.paint("melon", "2F8F3A", rings=True)
    a.paint("melonL", "7FCF55", rings=True)
    for key, code in (("rind", "F1F6DC"), ("flesh", "EE3B4A"), ("seed", "1E1414"), ("skin", "E9A98A"), ("nose", "B04A62"),
                      ("skinD", "C98468"), ("pink", "FF8FA6"), ("white", "FFFDF4"), ("dark", "2A1A16"),
                      ("glint", "FFFFFF"), ("claw", "FFF1D6")):
        a.paint(key, code)
    t = common_stand(a, 1.45)
    zb = t + 0.3
    part(a, "Body", "Stand", (0, 0.1, zb))
    bands = ((0.74, 0.86), (0.84, 1.0), (0.88, 1.06), (0.84, 0.98), (0.72, 0.82))
    for k, (w, h) in enumerate(bands):
        y0 = -0.62 + 0.3 * k
        a.prism("melon" if k % 2 == 0 else "melonL", half_oct(w, h, zb), y0, y0 + 0.32, axis="y")
    # спереди — срез арбуза: белая корка, красная мякоть, чёрные семечки
    w0, h0 = bands[0]
    a.prism("rind", half_oct(w0 - 0.05, h0 - 0.05, zb), -0.66, -0.6, axis="y")
    a.prism("flesh", half_oct(w0 - 0.15, h0 - 0.15, zb), -0.69, -0.64, axis="y")
    for x, z in ((-0.32, 0.42), (0.32, 0.42), (-0.12, 0.58), (0.14, 0.6), (-0.4, 0.2), (0.42, 0.22), (0.0, 0.42)):
        a.box("seed", x - 0.04, x + 0.04, -0.72, -0.68, zb + z - 0.055, zb + z + 0.055, bevel=0)
    # хвост
    part(a, "Tail", "Body", (0, 0.86, zb + 0.15))
    a.frustum("skinD", (-0.12, 0.12, zb + 0.06, zb + 0.28), (-0.04, 0.04, zb + 0.08, zb + 0.16), 0.86, 1.26, axis="y")
    # ножки с коготками
    for x, y, name in ((-0.5, -0.36, "LegFL"), (0.5, -0.36, "LegFR"), (-0.5, 0.46, "LegBL"), (0.5, 0.46, "LegBR")):
        part(a, name, "Body", (x, y, zb))
        a.box("skin", x - 0.13, x + 0.13, y - 0.13, y + 0.13, t, zb + 0.04)
        for dx in (-0.07, 0.07):
            a.box("claw", x + dx - 0.03, x + dx + 0.03, y - 0.19, y - 0.12, t + 0.01, t + 0.06, bevel=0)
    # мордочка выглядывает из-под среза: длинный розовый нос, ушки торчком, глаза вверх
    part(a, "Head", "Body", (0, -0.62, zb + 0.12))
    a.prism("skin", S.octagon(-0.3, 0.3, zb - 0.08, zb + 0.36, 0.1), -0.98, -0.6, axis="y")
    a.frustum("pink", (-0.13, 0.13, zb - 0.06, zb + 0.14), (-0.06, 0.06, zb - 0.03, zb + 0.06), -0.98, -1.36, axis="y")
    a.box("nose", -0.055, 0.055, -1.4, -1.34, zb - 0.02, zb + 0.06)
    for s in (-1, 1):
        round_eye(a, (s * 0.15, -0.98, zb + 0.22), 0.1, look=(0, 0.7), pupil=0.6)
        m = tilt((s * 0.22, -0.8, zb + 0.34), "Y", s * 38)
        a.box("skin", s * 0.15, s * 0.29, -0.84, -0.76, zb + 0.3, zb + 0.5, matrix=m)
        a.box("pink", s * 0.18, s * 0.26, -0.86, -0.835, zb + 0.34, zb + 0.46, bevel=0, matrix=m)
    a.face = (0, -0.98, zb + 0.18)
    a.closeup = ((-1.9, -1.6, zb + 1.4), (-0.6, 0.0, zb + 0.6))
    a.pose = {"Head": ((10, 0, 0), (0, 0.14, -0.02)), "Tail": ((0, 0, 25), (0, 0, 0)), "LegFL": ((-20, 0, 0), (0, 0, 0)),
              "LegBR": ((20, 0, 0), (0, 0, 0))}
    return a


# ── 8. Змейка-соломинка: змейка-трубочка в красно-белую полоску свернулась кольцом на подставке, поднялась, на сгибе —
#       «гармошка» как у коктейльной трубочки, и опустила жёлтую голову в половинку кокоса с бирюзовой водой; глаза
#       зажмурены от удовольствия, пузырьки. Кокос, не коктейль ─────────────────────────────────────────────────────


def straw_snake():
    a = S.Art("Art_StrawSnake", ring_z0=0.8)
    d39v2(a)
    a.paint("nut", "7A4A28", rings=True)
    for key, code in (("red", "E53935"), ("white", "FFFDF4"), ("yellow", "FFD23F"), ("yellowD", "F2B21E"),
                      ("flesh", "FFF6E6"), ("water", "3FD2D6"), ("waterL", "A6F0F2"), ("nutD", "5A3418"),
                      ("dark", "2A1A12"), ("cheek", "FF9EA6"), ("tongue", "FF6FAE"), ("glint", "FFFFFF")):
        a.paint(key, code)
    t = common_stand(a, 1.45)
    # половинка кокоса с водой и пузырьками
    cx, cy = 0.62, -0.18
    part(a, "Coconut", "Stand", (cx, cy, t))
    a.prism("nutD", ngon(cx, cy, 0.4, 8), t, t + 0.14)
    a.prism("nut", ngon(cx, cy, 0.58, 8), t + 0.12, t + 0.5)
    a.frame("flesh", ngon(cx, cy, 0.585, 8), 0.1, t + 0.48, t + 0.54, axis="z", bevel=0)
    a.prism("water", ngon(cx, cy, 0.49, 8), t + 0.44, t + 0.52, bevel=0)
    for dx, dy, dz, r in ((-0.2, 0.14, 0.07, 0.05), (0.16, 0.22, 0.17, 0.04), (0.2, -0.14, 0.29, 0.035)):
        disc(a, "waterL", cx + dx, cy + dy, r, t + 0.52 + dz, t + 0.52 + dz + 0.06, n=6, bevel=0)
    # тело-трубочка: кольцо на подставке и подъём; полоски — чередование отрезков
    keys = ("red", "white")
    part(a, "Body", "Stand", (-0.45, 0.1, t + 0.12))
    coil = [(-0.45 + 0.42 * math.cos(math.radians(a_)), 0.12 + 0.42 * math.sin(math.radians(a_)), t + 0.12 + 0.013 * k)
            for k, a_ in enumerate(range(200, 471, 30))]
    up = [(-0.6, 0.5, t + 0.3), (-0.55, 0.42, t + 0.72), (-0.48, 0.32, t + 1.15), (-0.42, 0.22, t + 1.45)]
    stripe_chain(a, keys, coil + up, 0.22, 0.2)
    part(a, "TailTip", "Body", coil[0])
    p = Vector(coil[0])
    q = p + Vector((-0.08, -0.26, 0.12))
    bar(a, "red", tuple(p), tuple(q), 0.18, 0.17)
    # сгиб-«гармошка» и шея вниз к кокосу
    part(a, "Neck", "Body", (-0.42, 0.22, t + 1.45))
    bend = [(-0.42, 0.22, t + 1.45), (-0.3, 0.15, t + 1.62), (-0.1, 0.06, t + 1.7), (0.1, -0.02, t + 1.66)]
    for i in range(len(bend) - 1):
        bar(a, "white", bend[i], bend[i + 1], 0.26, 0.24)
        x, y, z = bend[i + 1]
        a.box("red", x - 0.14, x + 0.14, y - 0.14, y + 0.14, z - 0.035, z + 0.035, bevel=0,
              matrix=tilt((x, y, z), "Y", 30 + 30 * i))
    down = [(0.1, -0.02, t + 1.66), (0.3, -0.1, t + 1.48), (0.44, -0.15, t + 1.22), (0.5, -0.18, t + 0.98)]
    stripe_chain(a, keys, down, 0.22, 0.2)
    # голова в кокосе: жмурится от удовольствия, язычок пьёт
    part(a, "Head", "Neck", (0.5, -0.18, t + 0.96))
    hz = t + 0.8
    a.box("yellow", 0.26, 0.78, -0.42, 0.06, hz - 0.16, hz + 0.13)
    a.box("yellowD", 0.32, 0.72, -0.36, 0.0, hz + 0.11, hz + 0.19)
    for s in (-1, 1):
        closed_eye(a, (0.52 + s * 0.11, -0.42, hz + 0.06), 0.12)
        a.box("cheek", 0.52 + s * 0.15 - 0.04, 0.52 + s * 0.15 + 0.04, -0.45, -0.41, hz - 0.08, hz - 0.03, bevel=0)
    a.box("tongue", 0.48, 0.56, -0.2, -0.12, hz - 0.36, hz - 0.17, bevel=0)
    a.face = (0.52, -0.42, hz + 0.02)
    a.closeup = ((-1.8, -1.8, t + 1.0), (-0.45, -0.1, t + 0.4))
    a.pose = {"Head": ((0, 0, 0), (0, 0, 0.08)), "Neck": ((0, -12, 0), (0, 0, 0)), "TailTip": ((0, 0, 30), (0, 0, 0)),
              "Coconut": ((0, 0, 0), (0, 0, 0))}
    return a


# ── 9. Жук-капелька: круглый синий жук-трудяга несёт на спине каплю воды больше себя, придерживает её передними
#       лапками; оранжевые усики, глаза с натугой смотрят вверх на каплю, капля пота; блики на капле ────────────────────


def drop_beetle():
    a = S.Art("Art_DropBeetle", ring_z0=0.7)
    d39v2(a)
    a.paint("shell", "2F6FD6", rings=True)
    a.paint("drop", "45CFE0")
    for key, code in (("shellD", "1F4BA0"), ("under", "1C2440"), ("orange", "FF9A2E"), ("dropL", "B8F3FA"),
                      ("white", "FFFDF4"), ("dark", "141824"), ("glint", "FFFFFF"), ("mouth", "3A1414"),
                      ("sweat", "8FDDFF")):
        a.paint(key, code)
    t = common_stand(a, 1.3)
    part(a, "Body", "Stand", (0, 0.15, t + 0.35))
    a.prism("under", S.octagon(-0.46, 0.46, -0.24, 0.6, 0.16), t + 0.18, t + 0.3)
    a.prism("shell", S.octagon(-0.52, 0.52, -0.3, 0.66, 0.19), t + 0.28, t + 0.56)
    a.prism("shell", S.octagon(-0.43, 0.43, -0.22, 0.58, 0.15), t + 0.54, t + 0.74)
    a.prism("shell", S.octagon(-0.28, 0.28, -0.1, 0.46, 0.1), t + 0.72, t + 0.84)
    a.box("shellD", -0.03, 0.03, -0.12, 0.62, t + 0.56, t + 0.86, bevel=0)
    for s, name in ((-1, "LegsL"), (1, "LegsR")):
        part(a, name, "Body", (s * 0.42, 0.18, t + 0.26))
        for y in (-0.12, 0.2, 0.5):
            bar(a, "under", (s * 0.4, y, t + 0.26), (s * 0.66, y - 0.06, t + 0.14), 0.09, 0.09)
            bar(a, "under", (s * 0.66, y - 0.06, t + 0.14), (s * 0.72, y - 0.1, t), 0.08, 0.08)
    # голова: тёмная, большие глаза с натугой вверх, сжатый рот, капля пота; усики — свои части
    part(a, "Head", "Body", (0, -0.28, t + 0.42))
    a.prism("shellD", S.octagon(-0.3, 0.3, t + 0.2, t + 0.62, 0.1), -0.64, -0.24, axis="y")
    for s in (-1, 1):
        round_eye(a, (s * 0.14, -0.64, t + 0.47), 0.11, look=(0, 0.8), pupil=0.6)
    a.box("mouth", -0.08, 0.08, -0.67, -0.63, t + 0.29, t + 0.32, bevel=0)
    a.box("sweat", 0.3, 0.37, -0.6, -0.54, t + 0.6, t + 0.7, bevel=0)
    for s, name in ((-1, "AntennaL"), (1, "AntennaR")):
        part(a, name, "Head", (s * 0.14, -0.5, t + 0.62))
        bar(a, "orange", (s * 0.14, -0.5, t + 0.6), (s * 0.34, -0.74, t + 0.98), 0.06, 0.06)
        a.box("orange", s * 0.34 - 0.07, s * 0.34 + 0.07, -0.81, -0.67, t + 0.92, t + 1.06)
    # капля на спине: восьмигранники сужаются к острию, блики слева сверху; передние лапки придерживают
    part(a, "Drop", "Body", (0, 0.14, t + 0.84))
    c = (0, 0.16)
    for r, z0, z1 in ((0.4, 0.82, 0.94), (0.52, 0.92, 1.12), (0.56, 1.1, 1.36), (0.52, 1.34, 1.52), (0.42, 1.5, 1.64),
                      (0.3, 1.62, 1.76), (0.18, 1.74, 1.88)):
        a.prism("drop", S.octagon(c[0] - r, c[0] + r, c[1] - r, c[1] + r, r * 0.34), t + z0, t + z1)
    a.frustum("drop", (-0.1, 0.1, 0.06, 0.26), (0, 0, 0.16, 0.16), t + 1.86, t + 2.06)
    a.box("dropL", -0.36, -0.2, -0.44, -0.38, t + 1.14, t + 1.34, bevel=0)
    a.box("glint", -0.3, -0.18, -0.4, -0.34, t + 1.38, t + 1.5, bevel=0)
    a.box("dropL", -0.22, -0.12, -0.18, -0.12, t + 1.64, t + 1.74, bevel=0)
    for s in (-1, 1):
        bar(a, "under", (s * 0.34, -0.2, t + 0.5), (s * 0.5, -0.1, t + 1.0), 0.08, 0.08)
    a.face = (0, -0.64, t + 0.42)
    a.closeup = ((-1.7, -1.4, t + 1.9), (-0.25, 0.1, t + 1.3))
    a.pose = {"Drop": ((0, 10, 0), (0.05, 0, 0.04)), "AntennaL": ((20, 0, 0), (0, 0, 0)),
              "AntennaR": ((-15, 0, 0), (0, 0, 0)), "LegsL": ((15, 0, 0), (0, 0, 0)), "Head": ((0, 0, 8), (0, 0, 0))}
    return a


# ── 10. Сурикат-часовой: высокий тонкий сурикат на страже, упёрся хвостом в землю; правой лапой держит у глаза латунную
#        подзорную трубу (смотрит вбок), левой прикрыл глаза от солнца; тёмные «очки» вокруг глаз, полоски на спине,
#        красный платок на шее. Без оружия и формы; не Тимон ──────────────────────────────────────────────────────────


def meerkat_lookout():
    a = S.Art("Art_MeerkatLookout", ring_z0=1.3)
    d39v2(a)
    a.paint("fur", "D8A65C", rings=True)
    for key, code in (("furD", "8A5E30"), ("cream", "FBE6BC"), ("mask", "3A2A20"), ("brass", "D4A93E"),
                      ("brassD", "8E6A22"), ("lens", "8FD8F0"), ("red", "E0352B"), ("white", "FFFDF4"),
                      ("dark", "1E1612"), ("glint", "FFFFFF"), ("nose", "2A1C16"), ("mouth", "5A1A20")):
        a.paint(key, code)
    t = common_stand(a, 1.3)
    part(a, "Body", "Stand", (0, 0.05, t + 0.2))
    for s in (-1, 1):
        a.box("fur", s * 0.06, s * 0.3, -0.42, 0.1, t, t + 0.12)
        a.box("fur", s * 0.08, s * 0.28, -0.1, 0.18, t + 0.1, t + 0.42)
    a.prism("fur", S.octagon(-0.33, 0.33, -0.26, 0.3, 0.12), t + 0.36, t + 1.0)
    a.prism("fur", S.octagon(-0.29, 0.29, -0.23, 0.26, 0.1), t + 0.98, t + 1.52)
    a.box("cream", -0.2, 0.2, -0.3, -0.21, t + 0.42, t + 1.44)
    for z in (0.62, 0.86, 1.1, 1.34):  # полоски на спине
        a.box("furD", -0.22, 0.22, 0.25 if z < 1 else 0.22, 0.32 if z < 1 else 0.29, t + z, t + z + 0.06, bevel=0)
    a.frame("red", S.octagon(-0.3, 0.3, -0.25, 0.28, 0.1), 0.06, t + 1.46, t + 1.56, axis="z", bevel=0)
    a.frustum("red", (-0.16, 0.16, -0.32, -0.25), (0, 0, -0.29, -0.29), t + 1.5, t + 1.26, bevel=0)
    part(a, "Tail", "Body", (0, 0.24, t + 0.4))
    stripe_chain(a, ("fur", "fur", "furD"), [(0, 0.24, t + 0.4), (0.1, 0.62, t + 0.12), (0.2, 1.0, t + 0.08),
                                             (0.26, 1.24, t + 0.08)], 0.16, 0.14)
    # голова: маленькая, тёмные «очки», мордочка с носом, ушки
    part(a, "Head", "Body", (0, -0.02, t + 1.54))
    hz = t + 1.82
    a.prism("fur", S.octagon(-0.27, 0.27, -0.28, 0.2, 0.1), t + 1.56, t + 2.06)
    a.frustum("cream", (-0.15, 0.15, hz - 0.22, hz - 0.02), (-0.08, 0.08, hz - 0.17, hz - 0.07), -0.27, -0.52, axis="y")
    a.box("nose", -0.06, 0.06, -0.55, -0.5, hz - 0.15, hz - 0.08)
    a.box("mouth", -0.06, 0.06, -0.32, -0.29, hz - 0.25, hz - 0.22, bevel=0)
    for s in (-1, 1):
        a.box("mask", s * 0.04, s * 0.27, -0.31, -0.27, hz - 0.08, hz + 0.12, bevel=0)
        a.box("furD", s * 0.26, s * 0.36, -0.06, 0.06, hz + 0.08, hz + 0.18)
    round_eye(a, (-0.15, -0.31, hz + 0.02), 0.08, look=(0.2, 0), pupil=0.62, depth=0.03)
    closed_eye(a, (0.15, -0.31, hz + 0.02), 0.14, happy=False)
    # правая лапа — подзорная труба у правого глаза, смотрит вбок-вперёд
    part(a, "ArmR", "Body", (0.26, -0.04, t + 1.36))
    bar(a, "fur", (0.26, -0.04, t + 1.36), (0.34, -0.26, t + 1.62), 0.13, 0.12)
    a.box("fur", 0.26, 0.42, -0.36, -0.2, t + 1.58, t + 1.74)
    part(a, "Spyglass", "ArmR", (0.2, -0.36, hz + 0.02))
    d = Vector((0.85, -0.53, 0.03)).normalized()
    base = Vector((0.2, -0.36, hz + 0.02))
    m = Matrix.Translation(base) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    for z0, z1, r, key in ((0.0, 0.32, 0.08, "brass"), (0.3, 0.58, 0.1, "brassD"), (0.56, 0.86, 0.12, "brass"),
                           (0.84, 0.9, 0.135, "brassD")):
        a.prism(key, ngon(0, 0, r, 8), z0, z1, matrix=m)
    a.prism("lens", ngon(0, 0, 0.1, 8), 0.89, 0.92, bevel=0, matrix=m)
    # левая лапа — козырьком над глазами
    part(a, "ArmL", "Body", (-0.26, -0.04, t + 1.36))
    bar(a, "fur", (-0.26, -0.04, t + 1.36), (-0.38, -0.22, t + 1.74), 0.13, 0.12)
    bar(a, "fur", (-0.38, -0.22, t + 1.74), (-0.12, -0.36, hz + 0.2), 0.12, 0.1)
    a.face = (0, -0.3, hz)
    a.closeup = ((-1.4, -1.9, t + 1.2), (-0.2, -0.1, t + 0.85))
    a.pose = {"Head": ((0, 0, 20), (0, 0, 0)), "ArmR": ((0, 0, 15), (0, 0, 0)), "Spyglass": ((0, 0, 0), (0, 0, 0)),
              "Tail": ((0, 0, -20), (0, 0, 0)), "Body": ((0, 0, 0), (0, 0, 0.12))}
    return a


# ── 11. Скорпион-лейка: пухлый оранжевый скорпион-садовник; хвост дугой над спиной кончается бирюзовой лейкой с носиком
#        и капли падают в горшок с розовым цветком, который он держит в левой клешне; правая клешня щёлкает; морда
#        добрая — большие глаза, улыбка. Ноги группами ──────────────────────────────────────────────────────────────


def can_scorpion():
    a = S.Art("Art_CanScorpion", ring_z0=0.6)
    d39v2(a)
    a.paint("body", "FF8C2E", rings=True)
    for key, code in (("bodyD", "E06A1A"), ("can", "1FB3A6"), ("canD", "128578"), ("pot", "C8643A"),
                      ("potD", "A04E2C"), ("soil", "5A3A26"), ("leaf", "3DBE4A"), ("petal", "FF6FAE"),
                      ("petalD", "E0458C"), ("yellow", "FFD23F"), ("water", "6FD6FF"), ("white", "FFFDF4"),
                      ("dark", "231816"), ("glint", "FFFFFF"), ("mouth", "5A1A20"), ("cheek", "FFB08A")):
        a.paint(key, code)
    t = common_stand(a, 1.5)
    part(a, "Body", "Stand", (0, 0.12, t + 0.3))
    a.prism("bodyD", S.octagon(-0.48, 0.48, -0.36, 0.56, 0.17), t + 0.16, t + 0.3)
    a.prism("body", S.octagon(-0.56, 0.56, -0.44, 0.62, 0.2), t + 0.28, t + 0.62)
    a.prism("body", S.octagon(-0.42, 0.42, -0.32, 0.5, 0.15), t + 0.6, t + 0.78)
    for y in (0.12, 0.36):
        a.box("bodyD", -0.43, 0.43, y, y + 0.06, t + 0.76, t + 0.8, bevel=0)
    for s in (-1, 1):
        round_eye(a, (s * 0.21, -0.44, t + 0.5), 0.13, look=(-0.3, 0.2), pupil=0.6)
        a.box("cheek", s * 0.33 - 0.05, s * 0.33 + 0.05, -0.47, -0.43, t + 0.33, t + 0.4, bevel=0)
    a.box("mouth", -0.1, 0.1, -0.47, -0.43, t + 0.34, t + 0.38, bevel=0)
    bar(a, "mouth", (0.08, -0.457, t + 0.36), (0.15, -0.457, t + 0.41), 0.04, 0.035, bevel=0)
    bar(a, "mouth", (-0.08, -0.462, t + 0.36), (-0.15, -0.462, t + 0.41), 0.04, 0.035, bevel=0)
    for s, name in ((-1, "LegsL"), (1, "LegsR")):
        part(a, name, "Body", (s * 0.5, 0.15, t + 0.3))
        for y in (-0.15, 0.08, 0.31, 0.52):
            bar(a, "bodyD", (s * 0.5, y, t + 0.3), (s * 0.78, y + 0.03, t + 0.2), 0.09, 0.09)
            bar(a, "bodyD", (s * 0.78, y + 0.03, t + 0.2), (s * 0.86, y + 0.05, t), 0.08, 0.08)
    # левая клешня держит горшок с цветком
    part(a, "ClawL", "Body", (-0.42, -0.34, t + 0.42))
    bar(a, "body", (-0.42, -0.34, t + 0.42), (-0.7, -0.66, t + 0.5), 0.16, 0.15)
    px, py, pz = -0.78, -0.86, t + 0.4
    a.box("body", px - 0.26, px + 0.26, py + 0.16, py + 0.3, pz + 0.02, pz + 0.24)
    a.frustum("pot", (px - 0.14, px + 0.14, py - 0.14, py + 0.14), (px - 0.19, px + 0.19, py - 0.19, py + 0.19), pz, pz + 0.3)
    a.frame("potD", S.octagon(px - 0.21, px + 0.21, py - 0.21, py + 0.21, 0.05), 0.05, pz + 0.27, pz + 0.34, axis="z",
            bevel=0)
    a.box("soil", px - 0.16, px + 0.16, py - 0.16, py + 0.16, pz + 0.26, pz + 0.3, bevel=0)
    a.box("leaf", px - 0.025, px + 0.025, py - 0.025, py + 0.025, pz + 0.28, pz + 0.62, bevel=0)
    for s in (-1, 1):
        a.box("leaf", px + s * 0.03, px + s * 0.16, py - 0.03, py + 0.03, pz + 0.4, pz + 0.46, bevel=0)
    petals(a, (px, py, pz + 0.66), 5, 0.14, 0.11, ("petal", "petalD"), "yellow", 0.08, normal=(0, -0.5, 1), lift=10)
    # правая клешня поднята и раскрыта
    part(a, "ClawR", "Body", (0.42, -0.34, t + 0.42))
    bar(a, "body", (0.42, -0.34, t + 0.42), (0.74, -0.6, t + 0.72), 0.16, 0.15)
    cx_, cy_, cz_ = 0.8, -0.68, t + 0.84
    a.box("body", cx_ - 0.16, cx_ + 0.16, cy_ - 0.14, cy_ + 0.14, cz_ - 0.16, cz_ + 0.06)
    a.box("bodyD", cx_ - 0.14, cx_ + 0.14, cy_ - 0.4, cy_ - 0.12, cz_ + 0.02, cz_ + 0.14, matrix=tilt((cx_, cy_ - 0.12, cz_ + 0.06), "X", 25))
    a.box("bodyD", cx_ - 0.13, cx_ + 0.13, cy_ - 0.36, cy_ - 0.12, cz_ - 0.16, cz_ - 0.05, matrix=tilt((cx_, cy_ - 0.12, cz_ - 0.1), "X", -15))
    # хвост дугой над спиной, на конце — лейка с носиком, капли падают в горшок
    part(a, "Tail", "Body", (0, 0.58, t + 0.6))
    stripe_chain(a, ("body", "bodyD"), [(0, 0.58, t + 0.6), (0, 0.92, t + 0.98), (-0.04, 0.84, t + 1.44),
                                        (-0.1, 0.5, t + 1.72)], 0.3, 0.28)
    part(a, "Can", "Tail", (-0.1, 0.5, t + 1.72))
    cc = Vector((-0.14, 0.36, t + 1.84))
    a.prism("can", ngon(cc.z, cc.y, 0.24, 8), cc.x - 0.22, cc.x + 0.22, axis="x")
    a.frame("canD", ngon(cc.z, cc.y, 0.255, 8), 0.05, cc.x - 0.06, cc.x + 0.06, axis="x", bevel=0)
    a.box("canD", cc.x - 0.05, cc.x + 0.05, cc.y - 0.06, cc.y + 0.24, cc.z + 0.22, cc.z + 0.3)
    tip = Vector((-0.66, -0.56, t + 1.5))
    bar(a, "can", tuple(cc + Vector((-0.08, -0.18, -0.04))), tuple(tip), 0.08, 0.08)
    disc(a, "canD", 0, 0, 0.1, -0.04, 0.04, n=8, matrix=Matrix.Translation(tip) @ (tip - cc).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4())
    for k, (dx, dz) in enumerate(((0.0, -0.16), (-0.06, -0.3), (0.05, -0.42))):
        a.box("water", tip.x + dx - 0.035, tip.x + dx + 0.035, tip.y - 0.035 - 0.05 * k, tip.y + 0.035 - 0.05 * k,
              tip.z + dz - 0.06, tip.z + dz + 0.03, bevel=0)
    a.face = (0, -0.44, t + 0.45)
    a.closeup = ((1.8, -1.2, t + 1.3), (0.4, 0.3, t + 0.5))
    a.pose = {"Tail": ((-10, 0, 0), (0, 0, 0)), "Can": ((0, -20, 0), (0, 0, 0)), "ClawR": ((0, 0, -20), (0, 0, 0)),
              "ClawL": ((0, 0, 8), (0, 0, 0)), "LegsL": ((10, 0, 0), (0, 0, 0))}
    return a


# ── 12. Страусёнок-песочник: пушистый жёлтый шар на длинных ногах, полосатая пушистая шея; только что вытащил голову
#        из песка — на голове куча песка, из неё торчат клюв и испуганные глаза; крылышки-пушинки. Шея в перьях, не
#        голая (≥ 0.16) ──────────────────────────────────────────────────────────────────────────────────────────────


def sand_chick():
    a = S.Art("Art_SandChick", ring_z0=1.2)
    d39v2(a)
    a.paint("fluff", "FFD45A", rings=True)
    a.paint("sand", "D29A50", rings=True)
    for key, code in (("fluffL", "FFE89A"), ("stripe", "B9852E"), ("leg", "E89A5A"), ("legD", "C27A40"),
                      ("beak", "FF9A2E"), ("sandD", "A87436"), ("sandL", "EBC07C"), ("white", "FFFDF4"), ("dark", "231816"),
                      ("glint", "FFFFFF")):
        a.paint(key, code)
    t = common_stand(a, 1.3)
    for s, name in ((-1, "LegL"), (1, "LegR")):
        part(a, name, "Body", (s * 0.2, 0.06, t + 1.0))
        knee = (s * 0.26, 0.2, t + 0.56)
        bar(a, "leg", (s * 0.2, 0.06, t + 1.0), knee, 0.15, 0.14)
        bar(a, "leg", knee, (s * 0.24, -0.02, t + 0.1), 0.13, 0.12)
        a.box("legD", s * 0.16, s * 0.32, -0.38, 0.06, t, t + 0.1)
        a.box("legD", s * 0.22, s * 0.36, -0.46, -0.3, t + 0.005, t + 0.08, bevel=0)
    part(a, "Body", "Stand", (0, 0.05, t + 1.0))
    ball(a, "fluff", (0, 0.08, t + 1.22), 0.52, n=5)
    for x, y, z in ((-0.5, 0.22, 1.3), (0.52, 0.0, 1.18), (-0.2, 0.55, 1.5), (0.25, 0.52, 1.0), (0.0, 0.6, 1.32),
                    (-0.35, -0.38, 1.0)):
        a.box("fluffL", x - 0.08, x + 0.08, y - 0.08, y + 0.08, t + z - 0.08, t + z + 0.08)
    for s, name in ((-1, "WingL"), (1, "WingR")):
        part(a, name, "Body", (s * 0.48, 0.05, t + 1.3))
        a.box("fluffL", s * 0.44, s * 0.66, -0.2, 0.28, t + 1.1, t + 1.38, matrix=tilt((s * 0.48, 0, t + 1.3), "Y", -s * 20))
    # шея полосатая, вверх и чуть вперёд
    part(a, "Neck", "Body", (0, -0.2, t + 1.6))
    stripe_chain(a, ("fluffL", "stripe"), [(0, -0.2, t + 1.6), (0, -0.26, t + 1.82), (0, -0.3, t + 2.04),
                                           (0, -0.32, t + 2.24), (0, -0.34, t + 2.42)], 0.19, 0.19)
    # голова под кучей песка: ступенчатая горка, из неё клюв и глаза-плошки
    part(a, "Head", "Neck", (0, -0.34, t + 2.42))
    hz = t + 2.56
    a.prism("fluff", S.octagon(-0.22, 0.22, -0.52, -0.14, 0.08), hz - 0.18, hz + 0.06)
    for r, dx, z0, z1, key in ((0.44, 0.0, 0.0, 0.14, "sandD"), (0.37, 0.05, 0.12, 0.28, "sand"),
                               (0.27, 0.11, 0.26, 0.42, "sand"), (0.16, 0.17, 0.4, 0.54, "sandL")):
        a.prism(key, S.octagon(dx - r, dx + r, -0.34 - r, -0.34 + r, r * 0.3), hz + z0, hz + z1)
    for x, y, z in ((-0.2, -0.6, 0.3), (0.3, -0.58, 0.22), (0.05, -0.5, 0.45), (-0.3, -0.42, 0.18), (0.36, -0.2, 0.36)):
        a.box("sandD", x - 0.03, x + 0.03, y - 0.03, y + 0.03, hz + z - 0.03, hz + z + 0.03, bevel=0)
    for x, y, z in ((-0.5, -0.56, -0.12), (0.5, -0.3, -0.3), (0.34, -0.78, -0.22)):  # песок сыплется
        a.box("sandD", x - 0.045, x + 0.045, y - 0.045, y + 0.045, hz + z - 0.045, hz + z + 0.045)
    a.frustum("beak", (-0.1, 0.1, hz - 0.12, hz + 0.02), (-0.04, 0.04, hz - 0.08, hz - 0.02), -0.7, -0.98, axis="y")
    for s in (-1, 1):
        round_eye(a, (s * 0.15, -0.7, hz + 0.2), 0.1, look=(0.3 * s, 0.2), pupil=0.42, depth=0.04)
    a.face = (0, -0.72, hz + 0.08)
    a.closeup = ((-1.6, -1.9, t + 1.7), (-0.25, -0.1, t + 1.2))
    a.pose = {"LegL": ((30, 0, 0), (0, 0, 0)), "LegR": ((-25, 0, 0), (0, 0, 0)), "WingL": ((0, 30, 0), (0, 0, 0)),
              "WingR": ((0, -30, 0), (0, 0, 0)), "Neck": ((-12, 0, 0), (0, 0, 0)), "Head": ((0, 0, 15), (0, 0, 0))}
    return a


COMMON2 = [("UmbrellaLizard", umbrella_lizard, "Ящерка-зонтик", "Common"),
           ("MelonArmadillo", melon_armadillo, "Арбуз-броненосец", "Common"),
           ("StrawSnake", straw_snake, "Змейка-соломинка", "Common"),
           ("DropBeetle", drop_beetle, "Жук-капелька", "Common"),
           ("MeerkatLookout", meerkat_lookout, "Сурикат-часовой", "Common"),
           ("CanScorpion", can_scorpion, "Скорпион-лейка", "Common"),
           ("SandChick", sand_chick, "Страусёнок-песочник", "Common")]


# ══ RARE ═════════════════════════════════════════════════════════════════════════════════════════════════════

# ── 20. Фенек-загадочник: взрослый фенек сидит столбиком, хитро прищурился; огромные уши лазурные изнутри; правая
#       лапа у подбородка («хм…»), левая показывает кубик-загадку с выдуманными знаками; хвост — большой знак вопроса,
#       под ним парит золотая точка; бирюзово-золотой ошейник с медальоном «?». Без платка фараона и без настоящих
#       иероглифов или букв (каталог владельца, спецификация 2026-11-11) ─────────────────────────────────────────────

FUR = (("fur", "F2A23A"), ("furD", "D9822B"), ("cream", "FFE7B8"), ("creamD", "F6CF92"), ("earIn", "45B8F0"),
       ("earInD", "2C8FD0"), ("teal", "16B3A3"), ("brow", "9C4A1A"), ("tip", "3A2A26"), ("pad", "C46A4A"),
       ("white", "FFFDF4"), ("dark", "231816"), ("glint", "FFFFFF"), ("cube", "2E7FD6"), ("cubeD", "1F5FB0"),
       ("glyph", "FFE45C"), ("mouth", "5A1A20"))
QUESTION = [".###.",
            "#...#",
            "...#.",
            "..#..",
            ".....",
            "..#.."]
SPIRAL = ["#####",
          "....#",
          "###.#",
          "#...#",
          "#####"]
STEPS = ["#....",
         "##...",
         "###..",
         "####.",
         "#####"]
DOTS = ["#...#",
        ".....",
        "..#..",
        ".....",
        "#...#"]


#   Полировка v2 (2026-11-12, задание владельца): только цвет, рисунок в карте и запекание — форма, части, точки вращения
#   и подставка как в v1. Контур D39 тех же размеров (шаг 0.6, квадрат 0.42, контур 0.03, глубина 0.22), но профиль —
#   «полка»: полная глубина на 55 % ширины, короткий скат (у v1 — плавный холмик, видимая часть линии вдвое уже).
POLISH = {
    "ring": dict(S.RING, core=0.55),
    # запекание ×4 со сглаживанием; проекция развёртки до 66° (при 50° крупные грани сжимались по одной оси, как у
    # проекции под 45°); острова по сетке текселей (прямые стороны квадратов — ровные строки карты); зазор 3 px
    # вместо 4. Плотность карты выше при том же 1024²
    "bake": {"ss": 4, "pack_margin": 0.003, "align": True, "project_angle": 66},
    "lid": ("lid", "D9822B"),  # веки темнее лба (цвет furD): прищур читается издалека; гладкие, как мелкие накладки
    "quest": ("tealD", "0A6A62"),  # «?» на золоте: тёмная бирюза вместо светлой — контраст яркости
    "gold": "F2C230",  # мелкое золото без контуров D39 (монета, заклёпки, медальон, уголки кубика — меньше квадрата)
    "cube": "2870CC",  # кубик чуть глубже по синему: золотые знаки контрастнее
    "marks": {"key": "furFace", "group": "Head", "code": "5C2A16", "soft": 0.004},
}


def fennec_riddler(v2=False, marks=True):
    a = S.Art("Art_FennecRiddler", ring_z0=1.0)
    a.paint("fur", "F2A23A", rings=True)
    for key, code in FUR[1:]:
        a.paint(key, code)
    lid_key, quest_key, head_key = "fur", "teal", "fur"
    if v2:
        a.ring = POLISH["ring"]
        a.bake_opts = POLISH["bake"]
        lid_key, quest_key = POLISH["lid"][0], POLISH["quest"][0]
        a.paint(*POLISH["lid"])
        a.paint(*POLISH["quest"])
        a.paint("cube", POLISH["cube"])
        if marks:
            head_key = POLISH["marks"]["key"]
            a.paint(head_key, "F2A23A", rings=True)  # тот же мех; на нём рисуются отметины
    t = stand(a, "rare", 1.5)
    if v2:
        a.paint("gold", POLISH["gold"])
    # золотая точка знака вопроса — парит на подставке под началом хвоста. Своя часть Dot (решение владельца
    # 2026-11-13: при скрытой подставке точка остаётся видимой); не качается с хвостом. Геометрия прежняя
    part(a, "Dot", "Stand", (1.04, 0.67, t + 0.42))
    disc(a, "gold", 1.04, t + 0.42, 0.19, 0.6, 0.74, n=8, axis="y")
    disc(a, "glyph", 0.99, t + 0.48, 0.06, 0.585, 0.605, n=6, axis="y", bevel=0)  # блик

    # — туловище: сидит столбиком на задних лапах; большие ступни вперёд, бёдра по бокам, светлое брюшко —
    part(a, "Body", "Stand", (0, 0.05, t + 0.1))
    for s in (-1, 1):
        a.box("creamD", s * 0.2, s * 0.6, -0.8, -0.1, t, t + 0.2)  # ступня
        for i, dx in enumerate((0.07, 0.2, 0.33)):  # пальцы
            x = s * 0.2 + s * dx
            a.box("cream", x - 0.055, x + 0.055, -0.89, -0.8, t, t + 0.13, bevel=0)
        a.box("fur", s * 0.36, s * 0.76, -0.42, 0.44, t + 0.04, t + 0.8)  # бедро
        a.box("fur", s * 0.42, s * 0.7, -0.34, 0.36, t + 0.8, t + 0.92)  # ступень бедра
    a.box("fur", -0.56, 0.56, -0.36, 0.48, t + 0.12, t + 1.06)  # низ туловища
    a.box("cream", -0.34, 0.34, -0.44, -0.3, t + 0.2, t + 0.98)  # брюшко
    a.box("fur", -0.47, 0.47, -0.3, 0.4, t + 1.04, t + 1.58)  # грудь
    a.box("cream", -0.3, 0.3, -0.39, -0.24, t + 1.0, t + 1.5)  # манишка
    a.box("cream", -0.17, 0.17, -0.38, -0.25, t + 0.9, t + 1.02, bevel=0.01)
    # ошейник: бирюзовая рамка, золотые заклёпки, медальон с «?»
    a.frame("teal", S.octagon(-0.52, 0.52, -0.42, 0.5, 0.14), 0.13, t + 1.49, t + 1.63, axis="z", bevel=0)
    for x in (-0.36, 0.36):
        a.box("gold", x - 0.05, x + 0.05, -0.47, -0.4, t + 1.52, t + 1.6, bevel=0)
    disc(a, "gold", 0, t + 1.37, 0.2, -0.5, -0.4, n=8, axis="y")
    pixel_boxes(a, quest_key, QUESTION, 0.042, -0.105, t + 1.5, -0.53, -0.49)

    # — голова: широкая, светлые щёки уступами, маска морды, острая мордочка с носом, хитрая полуулыбка —
    part(a, "Head", "Body", (0, 0.0, t + 1.56))
    a.box(head_key, -0.66, 0.66, -0.5, 0.46, t + 1.6, t + 2.7)
    if v2 and marks:
        # v2: две тёмные отметины от внешних нижних уголков глаз к носу (к краю мордочки) — только рисунок на лицевой
        # грани головы, симметрично; сужаются к концу. Отрезок (x, z, радиус) → (x, z, радиус)
        a.marks = dict(POLISH["marks"], strokes=[((0.5, t + 2.04, 0.032), (0.33, t + 1.9, 0.016))])
    a.box("fur", -0.52, 0.52, -0.38, 0.36, t + 2.7, t + 2.82)  # темя ступенью
    for s_ in (-1, 1):
        a.box("cream", s_ * 0.62, s_ * 0.86, -0.44, 0.02, t + 1.64, t + 2.0)  # щека
        a.box("cream", s_ * 0.84, s_ * 0.96, -0.36, -0.06, t + 1.7, t + 1.9)  # кончик щеки
    a.box("cream", -0.46, 0.46, -0.55, -0.46, t + 1.62, t + 1.88)  # маска под мордочкой
    a.frustum("cream", (-0.3, 0.3, t + 1.8, t + 2.12), (-0.14, 0.14, t + 1.87, t + 2.06), -0.49, -0.95, axis="y")
    a.box("dark", -0.12, 0.12, -1.02, -0.92, t + 1.93, t + 2.08)  # нос
    a.box("glint", -0.08, -0.02, -1.035, -1.015, t + 2.02, t + 2.06, bevel=0)
    # полуулыбка: прямая слева, уголок справа поднят
    a.box("mouth", -0.17, 0.11, -0.59, -0.54, t + 1.7, t + 1.75, bevel=0)
    bar(a, "mouth", (0.1, -0.57, t + 1.725), (0.24, -0.57, t + 1.82), 0.06, 0.05, bevel=0)
    # брови: левая (над прищуром) прямая и ниже, правая высоко поднята — «а ну-ка отгадай»
    bar(a, "brow", (-0.5, -0.52, t + 2.53), (-0.15, -0.52, t + 2.5), 0.09, 0.07)
    bar(a, "brow", (0.15, -0.52, t + 2.6), (0.5, -0.52, t + 2.67), 0.09, 0.07)
    # глаза: большие, хитро прищуренные, смотрят на кубик
    part(a, "EyeL", "Head", (-0.31, -0.42, t + 2.24))
    eye(a, (-0.31, -0.5, t + 2.24), 0.4, 0.38, look=(-0.55, -0.1), depth=0.07, lid=0.46, lid_key=lid_key)
    part(a, "EyeR", "Head", (0.31, -0.42, t + 2.24))
    eye(a, (0.31, -0.5, t + 2.24), 0.4, 0.38, look=(-0.55, -0.1), depth=0.07, lid=0.3, lid_key=lid_key)
    # уши: огромные, широкие, тремя крупными ступенями и кончиком, наружу и назад; изнутри лазурные
    for s_, name in ((-1, "EarL"), (1, "EarR")):
        base = Vector((s_ * 0.44, 0.02, t + 2.74))
        part(a, name, "Head", tuple(base))
        with_matrix(a, Matrix.Translation(base) @ Matrix.Rotation(math.radians(s_ * 17), 4, "Y")
                    @ Matrix.Rotation(math.radians(-8), 4, "X"))
        z = -0.06
        for i, (w, h) in enumerate(((0.8, 0.4), (0.58, 0.36), (0.36, 0.3), (0.16, 0.18))):
            a.box("fur", -w / 2, w / 2, -0.13, 0.13, z, z + h + (0.004 if i < 3 else 0))
            if i < 3:
                iw = w - 0.24
                a.box("earIn" if i < 2 else "earInD", -iw / 2, iw / 2, -0.17, -0.11, z + 0.08 if i == 0 else z,
                      z + h + 0.004, bevel=0)
            z += h
        with_matrix(a, None)

    # — лапы: левая показывает кубик-загадку, правая у подбородка —
    part(a, "ArmL", "Body", (-0.46, -0.04, t + 1.4))
    bar(a, "fur", (-0.46, -0.04, t + 1.4), (-0.86, -0.26, t + 1.26), 0.22, 0.2)
    a.box("fur", -0.97, -0.75, -0.37, -0.15, t + 1.15, t + 1.37)  # локоть
    bar(a, "fur", (-0.86, -0.26, t + 1.26), (-1.07, -0.53, t + 1.8), 0.2, 0.19)
    a.box("cream", -1.19, -0.95, -0.65, -0.41, t + 1.77, t + 2.0)  # ладонь
    part(a, "Cube", "ArmL", (-1.07, -0.53, t + 2.0))
    c = Vector((-1.07, -0.53, t + 2.25))
    h = 0.25
    a.box("cube", c.x - h, c.x + h, c.y - h, c.y + h, c.z - h, c.z + h)
    for dx in (-1, 1):
        for dy in (-1, 1):
            for dz in (-1, 1):
                q = c + Vector((dx, dy, dz)) * (h - 0.045)
                a.box("gold", q.x - 0.065, q.x + 0.065, q.y - 0.065, q.y + 0.065, q.z - 0.065, q.z + 0.065, bevel=0)
    pixel_boxes(a, "glyph", SPIRAL, 0.052, c.x - 0.13, c.z + 0.13, c.y - h - 0.025, c.y - h + 0.01)  # спереди
    side = Matrix.Translation((c.x - h, c.y, c.z)) @ Matrix.Rotation(math.radians(90), 4, "Z")  # бок к −x
    pixel_boxes(a, "glyph", STEPS, 0.052, -0.13, 0.13, -0.01, 0.025, matrix=side)
    top = Matrix.Translation((c.x, c.y, c.z + h)) @ Matrix.Rotation(math.radians(-90), 4, "X")  # верх
    pixel_boxes(a, "glyph", DOTS, 0.052, -0.13, 0.13, -0.025, 0.01, matrix=top)
    part(a, "ArmR", "Body", (0.46, -0.04, t + 1.4))
    bar(a, "fur", (0.46, -0.04, t + 1.4), (0.68, -0.42, t + 1.2), 0.22, 0.2)
    a.box("fur", 0.58, 0.8, -0.53, -0.31, t + 1.09, t + 1.31)  # локоть
    bar(a, "fur", (0.68, -0.42, t + 1.2), (0.33, -0.7, t + 1.52), 0.2, 0.19)
    a.box("cream", 0.2, 0.44, -0.82, -0.58, t + 1.46, t + 1.66)  # кулачок под подбородком
    a.box("pad", 0.25, 0.39, -0.835, -0.815, t + 1.5, t + 1.6, bevel=0)

    # — хвост-«?»: из-за бедра вбок и вверх, крюк сверху загибается к голове, кончик тёмный —
    part(a, "Tail", "Body", (0.45, 0.58, t + 0.78))
    chain(a, "fur", [(0.45, 0.58, t + 0.78), (1.0, 0.66, t + 1.02), (1.12, 0.66, t + 1.52), (1.4, 0.62, t + 1.98)],
          [0.5, 0.54, 0.52])
    part(a, "TailTip", "Tail", (1.4, 0.62, t + 1.98))
    chain(a, "fur", [(1.4, 0.62, t + 1.98), (1.33, 0.58, t + 2.5), (1.02, 0.56, t + 2.68), (0.9, 0.56, t + 2.36)],
          [0.5, 0.46, 0.42], tip_key="tip")
    a.pose = {"Head": ((0, -8, -10), (0, 0, 0)), "EarL": ((0, 12, 0), (0, 0, 0)), "EarR": ((0, -6, 0), (0, 0, 0)),
              "ArmL": ((0, 18, 0), (0, 0, 0)), "Cube": ((0, 0, 35), (0, 0, 0.12)), "Tail": ((0, 0, -12), (0, 0, 0)),
              "TailTip": ((0, -15, 0), (0, 0, 0))}
    return a


RARE = [("FennecRiddler", fennec_riddler, "Фенек-загадочник", "Rare"),
        ("FennecRiddler_v2", lambda: fennec_riddler(v2=True), "Фенек-загадочник (полировка v2)", "Rare"),
        ("FennecRiddler_v2_nomarks", lambda: fennec_riddler(v2=True, marks=False),
         "Фенек-загадочник (v2 без отметин, для сравнения)", "Rare")]

def tube(a, keys, pts, r, n=8, joints=True):
    """Толстая труба из восьмигранных отрезков между точками (цвета по очереди из keys), в изгибах — короткие
    восьмигранные «шарниры» (без щелей)."""
    for i in range(len(pts) - 1):
        p0, p1 = Vector(pts[i]), Vector(pts[i + 1])
        d = p1 - p0
        m = Matrix.Translation(p0) @ d.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
        rr = r * (1.0 + 0.03 * (i % 2))
        a.prism(keys[i % len(keys)], ngon(0, 0, rr, n), 0.0, d.length, matrix=m)
        if joints and i > 0:
            a.prism(keys[i % len(keys)], ngon(0, 0, rr * 0.97, n), -rr * 0.55, rr * 0.55, bevel=0, matrix=m)


def fish_pixels(a, key, keyT, x0, z0, cell, y0, y1, flip=False, matrix=None):
    """Рыбка из пикселей (5 × 3 тело + хвост) в плоскости x–z на грани y0…y1."""
    body = [".###.", "#####", ".###."]
    s = -1 if flip else 1
    for r, row in enumerate(body):
        for c, ch in enumerate(row):
            if ch == "#":
                xa = x0 + s * c * cell
                a.box(key, min(xa, xa + s * cell), max(xa, xa + s * cell), y0, y1, z0 - (r + 1) * cell, z0 - r * cell,
                      bevel=0, matrix=matrix)
    for r in (0, 2):
        xa = x0 + s * 5 * cell
        a.box(keyT, min(xa, xa + s * cell), max(xa, xa + s * cell), y0, y1, z0 - (r + 1) * cell, z0 - r * cell, bevel=0,
              matrix=matrix)


# ══ RARE №13–19, 21 ══════════════════════════════════════════════════════════════════════════════════════════

# ── 13. Верблюд-аквариум: важный взрослый верблюд-водовоз; вместо двух горбов — два кубических аквариума в золотых
#        рамах с рыбками и пузырьками; между ними фиолетовая попона с золотой бахромой; голова высоко, веки
#        полуопущены (важничает), на лбу — уздечка с золотым медальоном. Прозрачности нет: вода — бирюзовые блоки ──────


def aquarium_camel():
    a = S.Art("Art_AquariumCamel", ring_z0=1.6)
    d39v2(a)
    a.paint("fur", "E8A956", rings=True)
    for key, code in (("furD", "C0843A"), ("cream", "FBE3BC"), ("hoof", "5A3A26"), ("tuft", "8A5A2E"),
                      ("water", "35C6D6"), ("waterL", "A6EEF5"), ("fish", "FF8A2E"), ("fishY", "FFD23F"),
                      ("blanket", "7A3FC4"), ("blanketD", "5A2A9A"), ("white", "FFFDF4"), ("dark", "231816"),
                      ("glint", "FFFFFF"), ("bridle", "7A3FC4")):
        a.paint(key, code)
    t = rare_stand(a, 1.6)
    zb = t + 1.02
    part(a, "Body", "Stand", (0, 0, zb))
    a.prism("fur", S.octagon(zb - 0.04, zb + 0.62, -0.38, 0.38, 0.16), -0.86, 0.82, axis="x")
    a.prism("blanket", S.octagon(zb + 0.16, zb + 0.68, -0.42, 0.42, 0.14), -0.26, 0.26, axis="x")
    for s in (-1, 1):
        a.box("blanketD", -0.24, 0.24, s * 0.4, s * 0.44, zb + 0.14, zb + 0.5, bevel=0)
        for x in (-0.2, -0.07, 0.07, 0.2):
            a.box("gold", x - 0.035, x + 0.035, s * 0.42, s * 0.46, zb + 0.06, zb + 0.16, bevel=0)
    bar(a, "fur", (-0.78, 0, zb + 0.4), (-1.0, -0.06, zb + 1.08), 0.32, 0.3)
    bar(a, "fur", (-1.0, -0.06, zb + 1.08), (-1.06, -0.1, zb + 1.36), 0.28, 0.27)
    for x, y, name in ((-0.58, -0.22, "LegFL"), (-0.58, 0.22, "LegFR"), (0.56, -0.22, "LegBL"), (0.56, 0.22, "LegBR")):
        part(a, name, "Body", (x, y, zb))
        a.box("fur", x - 0.1, x + 0.1, y - 0.1, y + 0.1, t + 0.6, zb + 0.06)
        a.box("furD", x - 0.12, x + 0.12, y - 0.12, y + 0.12, t + 0.48, t + 0.64)
        a.box("fur", x - 0.085, x + 0.085, y - 0.085, y + 0.085, t + 0.1, t + 0.52)
        a.box("hoof", x - 0.13, x + 0.13, y - 0.14, y + 0.12, t, t + 0.12)
    # аквариумы-горбы: вода, золотые рёбра, рыбки на передних гранях, пузырьки
    for k, (x, name) in enumerate(((-0.46, "TankA"), (0.48, "TankB"))):
        z0 = zb + 0.6
        part(a, name, "Body", (x, 0, z0))
        a.box("water", x - 0.27, x + 0.27, -0.27, 0.27, z0, z0 + 0.56)
        a.box("waterL", x - 0.25, x + 0.25, -0.25, 0.25, z0 + 0.52, z0 + 0.58, bevel=0)
        for dz in (0.0, 0.52):
            a.frame("gold", S.octagon(x - 0.3, x + 0.3, -0.3, 0.3, 0.04), 0.06, z0 + dz - 0.01, z0 + dz + 0.07, axis="z",
                    bevel=0)
        for sx in (-1, 1):
            for sy in (-1, 1):
                xa, ya = x + sx * 0.29, sy * 0.29
                a.box("gold", min(xa, xa - sx * 0.05), max(xa, xa - sx * 0.05), min(ya, ya - sy * 0.05),
                      max(ya, ya - sy * 0.05), z0 + 0.06, z0 + 0.52, bevel=0)
        a.box("waterL", x - 0.2, x - 0.12, -0.285, -0.27, z0 + 0.34, z0 + 0.44, bevel=0)
        a.box("glint", x + 0.12, x + 0.18, -0.29, -0.275, z0 + 0.4, z0 + 0.46, bevel=0)
        part(a, "FishA" if k == 0 else "FishB", name, (x, -0.28, z0 + 0.25))
        fish_pixels(a, "fish" if k == 0 else "fishY", "fishY" if k == 0 else "fish", x - 0.15, z0 + 0.3, 0.05,
                    -0.31, -0.27, flip=k == 1)
        a.box("white", x + 0.14 * (1 if k == 0 else -1) - 0.025, x + 0.14 * (1 if k == 0 else -1) + 0.025, -0.3, -0.27,
              z0 + 0.36, z0 + 0.41, bevel=0)
    # голова: высоко поднята, повёрнута к игроку; полуопущенные веки, уздечка с медальоном
    head = Vector((-1.12, -0.16, zb + 1.5))
    m_head = Matrix.Translation(head) @ Matrix.Rotation(math.radians(38), 4, "Z") @ Matrix.Rotation(math.radians(12), 4, "Y")
    part(a, "Head", "Body", (-1.06, -0.1, zb + 1.3))
    with_matrix(a, m_head)
    a.prism("fur", S.octagon(-0.2, 0.3, -0.24, 0.24, 0.07), -0.26, 0.24, axis="x")
    a.prism("cream", S.octagon(-0.24, 0.06, -0.18, 0.18, 0.06), -0.66, -0.2, axis="x")
    a.box("furD", -0.72, -0.44, -0.19, 0.19, -0.27, -0.16)
    for s in (-1, 1):
        a.box("furD", -0.68, -0.645, s * 0.05, s * 0.14, 0.0, 0.03, bevel=0)
        a.box("fur", 0.02, 0.2, s * 0.2, s * 0.36, 0.2, 0.3, matrix=tilt((0.1, s * 0.22, 0.25), "X", -s * 22))
    a.frame("bridle", S.octagon(-0.25, 0.25, -0.25, 0.25, 0.07), 0.04, -0.2, -0.14, axis="x", bevel=0)
    a.prism("gold", ngon(-0.17, 0.0, 0.07, 8), -0.3, -0.25, axis="y")
    with_matrix(a, m_head @ Matrix.Rotation(math.radians(-90), 4, "Z"))
    for s in (-1, 1):
        eye(a, (s * 0.11, -0.26, 0.17 + 0.006 * (s > 0)), 0.15, 0.14, look=(0, -0.3), depth=0.05, lid=0.55, lid_key="furD")
        bar(a, "dark", (s * 0.17, -0.375, 0.19), (s * 0.22, -0.375, 0.15), 0.022, 0.02, bevel=0)
    with_matrix(a, None)
    part(a, "Tail", "Body", (0.8, 0, zb + 0.44))
    bar(a, "fur", (0.8, 0, zb + 0.44), (0.94, 0.02, zb + 0.1), 0.08, 0.08)
    a.box("tuft", 0.86, 1.04, -0.08, 0.12, zb - 0.12, zb + 0.12)
    a.face = tuple(m_head @ Vector((-0.4, 0, 0.0)))
    a.closeup = ((-0.2, -2.6, zb + 1.2), (0.0, -0.3, zb + 0.9))
    a.pose = {"Head": ((0, 0, -10), (0, 0, 0)), "FishA": ((0, 0, 0), (0.08, 0, 0.05)), "FishB": ((0, 0, 0), (-0.08, 0, -0.04)),
              "LegFL": ((0, -14, 0), (0, 0, 0)), "Tail": ((0, 25, 0), (0, 0, 0))}
    return a


# ── 14. Кактусы-акробаты: цирковая башня из трёх разных кактусов — внизу пузатый бочонок держит на голове опунцию,
#        опунция (плоские лопасти, одна «рукой» вбок) держит на кромке маленький столбик, который стоит на одной руке
#        и машет флажком; у каждого свой зелёный и свой цветок. Не два симметричных круга ─────────────────────────────


def cactus_acrobats():
    a = S.Art("Art_CactusAcrobats", ring_z0=1.2)
    d39v2(a)
    a.paint("green1", "3FAE46", rings=True)
    a.paint("green2", "8CCF4A", rings=True)
    a.paint("green3", "2E9C7A", rings=True)
    for key, code in (("rib", "2A7F34"), ("spine", "FFF0C8"), ("red", "E53935"), ("yellow", "FFD23F"),
                      ("pink", "FF6FAE"), ("pinkD", "E0458C"), ("white", "FFFDF4"), ("dark", "231816"),
                      ("glint", "FFFFFF"), ("mouth", "5A1A20"), ("orange", "FF9A2E"), ("cheek", "FFB0A0")):
        a.paint(key, code)
    t = rare_stand(a, 1.5)
    # низ — пузатый бочонок, напрягся, держит лапками опунцию
    part(a, "Base", "Stand", (0, 0, t))
    for h, z0, z1 in ((0.46, 0.0, 0.16), (0.6, 0.14, 0.62), (0.52, 0.6, 0.86), (0.36, 0.84, 0.96)):
        a.prism("green1", S.octagon(-h, h, -h, h, h * 0.3), t + z0, t + z1)
    for x, y in S.octagon(-0.6, 0.6, -0.6, 0.6, 0.18):
        ang = math.degrees(math.atan2(y, x))
        a.box("rib", x - 0.04, x + 0.04, y - 0.04, y + 0.04, t + 0.18, t + 0.6, matrix=tilt((x, y, 0), "Z", ang))
    for s in (-1, 1):
        round_eye(a, (s * 0.2, -0.6, t + 0.46), 0.12, look=(0, 0.6), pupil=0.55)
        bar(a, "rib", (s * 0.34, -0.63, t + 0.66), (s * 0.08, -0.63, t + 0.6), 0.07, 0.05)
    a.box("white", -0.16, 0.16, -0.63, -0.6, t + 0.25, t + 0.31, bevel=0)
    a.box("mouth", -0.18, 0.18, -0.62, -0.595, t + 0.23, t + 0.33, bevel=0)
    petals(a, (0.5, -0.2, t + 0.74), 5, 0.13, 0.11, ("red",), "yellow", 0.07, normal=(0.6, -0.4, 0.7), lift=10)
    for s, name in ((-1, "BaseArmL"), (1, "BaseArmR")):
        part(a, name, "Base", (s * 0.56, 0, t + 0.5))
        bar(a, "green1", (s * 0.56, 0, t + 0.5), (s * 0.66, -0.05, t + 0.86), 0.16, 0.15)
        bar(a, "green1", (s * 0.66, -0.05, t + 0.86), (s * 0.34, -0.04, t + 1.06), 0.14, 0.13)
    # середина — опунция: большая лопасть с лицом (кружится голова), маленькая лопасть-рука вбок, жёлтый цветок
    part(a, "Mid", "Base", (0, 0, t + 0.96))
    pad = S.octagon(-0.42, 0.42, t + 0.94, t + 1.98, 0.2)
    a.prism("green2", pad, -0.13, 0.13, axis="y")
    for x, z in ((-0.3, 1.2), (0.28, 1.36), (-0.22, 1.78), (0.3, 1.82), (0.0, 1.06)):
        a.box("spine", x - 0.03, x + 0.03, -0.17, -0.12, t + z - 0.03, t + z + 0.03, bevel=0)
    closed_eye(a, (-0.15, -0.13, t + 1.56), 0.12, key="dark", happy=False)  # один глаз зажмурен — закружилась голова
    round_eye(a, (0.15, -0.13, t + 1.56), 0.1, look=(-0.4, 0.3), pupil=0.55, depth=0.04)
    a.box("mouth", -0.1, 0.12, -0.16, -0.12, t + 1.36, t + 1.4, bevel=0)
    a.box("cheek", -0.3, -0.2, -0.16, -0.12, t + 1.42, t + 1.48, bevel=0)
    part(a, "MidArm", "Mid", (0.36, 0, t + 1.5))
    arm = tilt((0.36, 0, t + 1.5), "Y", -55)
    a.prism("green2", S.octagon(0.3, 0.86, t + 1.36, t + 1.68, 0.1), -0.11, 0.11, axis="y", matrix=arm)
    petals(a, (-0.46, -0.02, t + 1.62), 5, 0.12, 0.1, ("yellow",), "orange", 0.06, normal=(-1, -0.3, 0.3), lift=8)
    # верх — маленький столбик стоит на одной руке на кромке опунции и машет флажком, розовый цветок
    part(a, "Top", "Mid", (-0.12, 0, t + 1.98))
    lean = tilt((-0.12, 0, t + 1.98), "Y", 18)
    bar(a, "green3", (-0.12, 0, t + 1.97), (-0.1, -0.02, t + 2.22), 0.1, 0.1)
    with_matrix(a, lean)
    a.prism("green3", S.octagon(-0.4, -0.06, -0.17, 0.17, 0.08), t + 2.2, t + 2.86)
    a.prism("green3", S.octagon(-0.36, -0.1, -0.13, 0.13, 0.06), t + 2.84, t + 2.94)
    for s in (-1, 1):
        round_eye(a, (-0.23 + s * 0.075, -0.17, t + 2.62), 0.06, look=(0, 0), pupil=0.6, depth=0.03)
    a.box("mouth", -0.28, -0.18, -0.2, -0.165, t + 2.46, t + 2.49, bevel=0)
    petals(a, (-0.23, 0, t + 2.96), 5, 0.11, 0.09, ("pink", "pinkD"), "yellow", 0.06, lift=14)
    with_matrix(a, None)
    part(a, "TopArm", "Top", (0.0, 0, t + 2.6))
    bar(a, "green3", (0.0, 0, t + 2.6), (0.34, -0.04, t + 2.9), 0.09, 0.09)
    bar(a, "dark", (0.34, -0.04, t + 2.86), (0.36, -0.04, t + 3.3), 0.035, 0.035, bevel=0)
    a.prism("red", [(0.38, t + 3.28), (0.7, t + 3.18), (0.38, t + 3.06)], -0.06, -0.02, axis="y")
    a.prism("white", [(0.4, t + 3.2), (0.56, t + 3.16), (0.4, t + 3.12)], -0.075, -0.055, axis="y", bevel=0)
    a.face = (0, -0.13, t + 1.5)
    a.closeup = ((-1.8, -1.7, t + 1.1), (-0.4, -0.3, t + 0.4))
    a.pose = {"Mid": ((0, 8, 0), (0, 0, 0)), "Top": ((0, -14, 0), (0, 0, 0)), "TopArm": ((0, -25, 0), (0, 0, 0)),
              "MidArm": ((0, 15, 0), (0, 0, 0)), "BaseArmL": ((0, -10, 0), (0, 0, 0))}
    return a


# ── 15. Песчаный червь-бурильщик: толстый весёлый червь дугой выходит из песчаной ямки, на голове шахтёрские очки,
#        вместо носа — стальной бур со спиралью; терракотовый с жёлтыми полосами; кончик хвоста машет из второй ямки
#        позади. Толстый, дугой, с большой мордой и не телесного цвета; не червь «Дюны» (нет круглой пасти) ───────────


def drill_worm():
    a = S.Art("Art_DrillWorm", ring_z0=1.0)
    d39v2(a)
    a.paint("worm", "D9663A", rings=True)
    a.paint("sand", "E8B460", rings=True)
    for key, code in (("stripe", "F2C230"), ("hole", "6A4220"), ("steel", "B9C3CF"), ("steelD", "7D8794"),
                      ("goggle", "6B4A2E"), ("lens", "8FD8F0"), ("white", "FFFDF4"), ("dark", "231816"),
                      ("glint", "FFFFFF"), ("mouth", "5A1A20"), ("tongue", "FF6F86"), ("cheek", "FF9E7A"),
                      ("sandD", "C89040")):
        a.paint(key, code)
    t = rare_stand(a, 1.55)
    # песчаные бугры с ямками — своя часть (подставку в игре прячут, бугры остаются: червь выходит из земли)
    part(a, "Mound", "Stand", (-0.3, 0.12, t))
    for k, (cx, cy, r) in enumerate(((-0.3, 0.12, 0.58), (0.72, 0.52, 0.4))):
        a.prism("sand", S.octagon(cx - r, cx + r, cy - r, cy + r, r * 0.3), t, t + 0.14 + 0.012 * k)
        a.prism("sandD", S.octagon(cx - r * 0.7, cx + r * 0.7, cy - r * 0.7, cy + r * 0.7, r * 0.2), t + 0.12,
                t + 0.22 + 0.012 * k)
        a.prism("hole", ngon(cx, cy, r * 0.55, 8), t + 0.2 + 0.012 * k, t + 0.235 + 0.012 * k, bevel=0)
    part(a, "Body", "Mound", (-0.3, -0.12, t + 0.2))
    low = [(-0.3, 0.12, t + 0.1), (-0.36, 0.14, t + 0.62), (-0.3, 0.08, t + 1.08), (-0.1, -0.02, t + 1.38),
           (0.14, -0.14, t + 1.42), (0.28, -0.24, t + 1.22)]
    tube(a, ("worm", "stripe"), low, 0.3)
    part(a, "Head", "Body", (0.28, -0.24, t + 1.22))
    hz = t + 1.12
    with_matrix(a, Matrix.Translation((0.28, 0.06, 0)))
    for h, z0, z1 in ((0.36, -0.36, -0.14), (0.42, -0.16, 0.22), (0.36, 0.2, 0.36)):
        a.prism("worm", S.octagon(-h, h, -0.3 - h, -0.3 + h, h * 0.3), hz + z0, hz + z1)
    # очки на лбу-глазах: оправа и голубые стёкла, за ними глаза
    for s in (-1, 1):
        a.prism("goggle", ngon(s * 0.17, hz + 0.08, 0.15, 8), -0.78, -0.7, axis="y")
        a.prism("lens", ngon(s * 0.17, hz + 0.08, 0.11, 8), -0.8, -0.77, axis="y", bevel=0)
        a.box("white", s * 0.17 - 0.07, s * 0.17 + 0.07, -0.81, -0.795, hz + 0.02, hz + 0.14, bevel=0)
        a.box("dark", s * 0.17 - 0.035, s * 0.17 + 0.035, -0.82, -0.805, hz + 0.04, hz + 0.11, bevel=0)
        a.box("cheek", s * 0.28 - 0.05, s * 0.28 + 0.05, -0.75, -0.71, hz - 0.18, hz - 0.11, bevel=0)
    a.box("goggle", -0.435, 0.435, -0.6, 0.0, hz + 0.1, hz + 0.16, bevel=0)
    a.box("goggle", -0.04, 0.04, -0.79, -0.73, hz + 0.05, hz + 0.11, bevel=0)
    a.box("mouth", -0.2, 0.2, -0.75, -0.71, hz - 0.28, hz - 0.18, bevel=0)
    a.box("white", -0.16, 0.16, -0.76, -0.735, hz - 0.21, hz - 0.185, bevel=0)
    a.box("tongue", -0.06, 0.08, -0.76, -0.72, hz - 0.3, hz - 0.24, bevel=0)
    with_matrix(a, None)
    # бур вместо носа: стальной ступенчатый конус со спиралью, смотрит вперёд-вверх
    part(a, "Drill", "Head", (0.28, -0.6, hz - 0.02))
    m = Matrix.Translation((0.28, -0.6, hz - 0.04)) @ Vector((0.0, -0.75, 0.66)).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    for r, z0, z1, key in ((0.17, 0.0, 0.12, "steelD"), (0.15, 0.1, 0.26, "steel"), (0.11, 0.24, 0.4, "steel"),
                           (0.07, 0.38, 0.52, "steel")):
        a.prism(key, ngon(0, 0, r, 8), z0, z1, matrix=m)
    a.frustum("steel", (-0.05, 0.05, -0.05, 0.05), (0, 0, 0, 0), 0.5, 0.66, matrix=m)
    for k in range(7):
        ang = math.radians(k * 75)
        z = 0.06 + k * 0.065
        r = 0.17 - k * 0.018
        q = Vector((r * math.cos(ang), r * math.sin(ang), z))
        a.box("steelD", q.x - 0.035, q.x + 0.035, q.y - 0.035, q.y + 0.035, q.z - 0.03, q.z + 0.03, bevel=0,
              matrix=m @ Matrix.Translation(q) @ Matrix.Rotation(ang, 4, "Z") @ Matrix.Translation(-q))
    # кончик хвоста машет из второй ямки
    part(a, "TailTip", "Mound", (0.72, 0.52, t + 0.2))
    tube(a, ("worm", "stripe", "worm"), [(0.72, 0.52, t + 0.1), (0.76, 0.5, t + 0.38), (0.88, 0.46, t + 0.58),
                                         (1.04, 0.4, t + 0.62)], 0.17)
    a.face = (0.28, -0.69, hz)
    a.closeup = ((-1.7, -1.8, t + 1.2), (-0.3, -0.15, t + 0.7))
    a.pose = {"Head": ((10, 0, -12), (0, 0, 0)), "Drill": ((0, 0, 0), (0, 0, 0)), "TailTip": ((0, 0, 30), (0, 0, 0)),
              "Body": ((0, -8, 0), (0, 0, 0))}
    return a


# ── 16. Гриф-вентилятор: упитанный фиолетовый гриф, вместо крыльев — два вентилятора в решётках (лопасти — свои
#        части), белый пушистый воротник, оранжевая голова с крючковатым клювом; ему вечно жарко — язык набок,
#        капли пота, веки полуопущены. Лопасти толстые, без костей ───────────────────────────────────────────────


def fan_vulture():
    a = S.Art("Art_FanVulture", ring_z0=1.2)
    d39v2(a)
    a.paint("plum", "8E4FC9", rings=True)
    for key, code in (("plumD", "6A35A0"), ("ruff", "FFFDF4"), ("ruffD", "E6E2F0"), ("head", "FF8A4C"),
                      ("headD", "E06A30"), ("beak", "FFE3A0"), ("beakD", "D9B060"), ("metal", "C3CAD4"),
                      ("metalD", "8A93A0"), ("blade", "2ED1C0"), ("bladeD", "1FA396"), ("leg", "FFB04A"),
                      ("white", "FFFDF4"), ("dark", "231816"), ("glint", "FFFFFF"), ("tongue", "FF6F86"),
                      ("sweat", "8FDDFF")):
        a.paint(key, code)
    t = rare_stand(a, 1.5)
    for s, name in ((-1, "LegL"), (1, "LegR")):
        part(a, name, "Body", (s * 0.22, 0, t + 0.5))
        a.box("leg", s * 0.15, s * 0.29, -0.07, 0.07, t + 0.08, t + 0.52)
        for dx, dy in ((-0.08, -0.22), (0.06, -0.24), (0.0, 0.12)):
            a.box("leg", s * 0.22 + dx - 0.04, s * 0.22 + dx + 0.04, min(0, dy), max(0, dy), t, t + 0.08, bevel=0)
    part(a, "Body", "Stand", (0, 0.05, t + 0.5))
    ball(a, "plum", (0, 0.05, t + 1.0), 0.58, n=5)
    a.box("plumD", -0.28, 0.28, -0.6, -0.5, t + 0.74, t + 1.12)
    # воротник: пушистое белое кольцо из брусков
    for k in range(10):
        ang = math.radians(k * 36 + 18)
        q = (0.5 * math.cos(ang), 0.05 + 0.48 * math.sin(ang), t + 1.5 + 0.014 * (k % 2))
        a.box("ruff" if k % 2 else "ruffD", q[0] - 0.15, q[0] + 0.15, q[1] - 0.15, q[1] + 0.15, q[2] - 0.12,
              q[2] + 0.12, matrix=tilt(q, "Z", math.degrees(ang)))
    part(a, "Tail", "Body", (0, 0.55, t + 0.8))
    for k, dx in enumerate((-0.18, 0.0, 0.18)):
        a.box("plumD", dx - 0.08, dx + 0.08, 0.5, 0.95, t + 0.62 + 0.02 * k, t + 0.72 + 0.02 * k,
              matrix=tilt((dx, 0.55, t + 0.7), "Z", dx * 80))
    # голова: оранжевая, крючковатый клюв, полуопущенные веки, язык набок, пот
    part(a, "Head", "Body", (0, 0, t + 1.56))
    hz = t + 1.86
    a.prism("head", S.octagon(-0.26, 0.26, -0.3, 0.2, 0.09), t + 1.56, t + 2.16)
    a.prism("headD", S.octagon(-0.2, 0.2, -0.24, 0.14, 0.07), t + 2.14, t + 2.24)
    a.frustum("beak", (-0.13, 0.13, hz - 0.1, hz + 0.08), (-0.07, 0.07, hz - 0.08, hz + 0.02), -0.3, -0.62, axis="y")
    a.box("beakD", -0.07, 0.07, -0.66, -0.56, hz - 0.2, hz - 0.04)
    for s in (-1, 1):
        round_eye(a, (s * 0.14, -0.3, hz + 0.14), 0.09, look=(0, -0.3), pupil=0.6, lid=0.5, lid_key="headD")
    a.box("tongue", 0.04, 0.12, -0.46, -0.38, hz - 0.32, hz - 0.1, matrix=tilt((0.08, -0.42, hz - 0.1), "Y", 25))
    a.box("sweat", 0.28, 0.34, -0.26, -0.2, hz + 0.18, hz + 0.28, bevel=0)
    a.box("sweat", -0.36, -0.31, -0.24, -0.19, hz + 0.02, hz + 0.1, bevel=0)
    # вентиляторы вместо крыльев: решётка (два кольца и ось), лопасти — своя часть
    for s, name in ((-1, "FanL"), (1, "FanR")):
        c = Vector((s * 0.95, -0.12, t + 1.1))
        n = Vector((s * 0.45, -1.0, 0.1)).normalized()
        mr = Matrix.Translation(c) @ n.to_track_quat("Z", "Y").to_matrix().to_4x4()
        part(a, name, "Body", (s * 0.55, 0.0, t + 1.05))
        bar(a, "metalD", (s * 0.5, 0.02, t + 1.05), tuple(c + n * 0.12), 0.12, 0.12)
        a.frame("metal", ngon(0, 0, 0.52, 10), 0.06, -0.06, 0.06, axis="z", bevel=0, matrix=mr)
        a.frame("metalD", ngon(0, 0, 0.3, 10), 0.04, -0.035, 0.035, axis="z", bevel=0, matrix=mr)
        for k in range(4):
            a.box("metal", -0.02, 0.02, 0.06, 0.5, -0.025, 0.025, bevel=0,
                  matrix=mr @ Matrix.Rotation(math.radians(45 + 90 * k), 4, "Z"))
        part(a, "BladesL" if s < 0 else "BladesR", name, tuple(c))
        a.prism("metalD", ngon(0, 0, 0.09, 8), -0.1, 0.1, matrix=mr)
        for k in range(3):
            rot = mr @ Matrix.Rotation(math.radians(120 * k + 15 * s), 4, "Z") @ Matrix.Rotation(math.radians(18), 4, "X")
            a.prism("blade" if k % 2 == 0 else "bladeD", [(0.06, -0.08), (0.44, -0.15), (0.46, 0.12), (0.08, 0.07)],
                    -0.025, 0.025, matrix=rot)
    a.face = (0, -0.32, hz)
    a.closeup = ((1.6, -1.8, t + 1.0), (0.2, -0.1, t + 0.9))
    a.pose = {"BladesL": ((0, 0, 40), (0, 0, 0)), "BladesR": ((0, 0, -40), (0, 0, 0)), "Head": ((0, 0, 12), (0, 0, 0)),
              "FanL": ((0, 0, 10), (0, 0, 0)), "Tail": ((0, 0, 15), (0, 0, 0))}
    return a


# ── 17. Кобра-фонтан: изумрудная кобра-позёр в каменной чаше фонтана, капюшон раздут, на нём золотой узор из
#        квадратов (не похож на лицо), изо рта дугой бьёт струя воды в чашу. Чаша фонтана, не корзина заклинателя;
#        без яда. Чаша — своя часть (в игре остаётся) ──────────────────────────────────────────────────────────────


def cobra_fountain():
    a = S.Art("Art_CobraFountain", ring_z0=1.2)
    d39v2(a)
    a.paint("snake", "1FA35A", rings=True)
    a.paint("stone", "EAD2A2", rings=True)
    for key, code in (("snakeL", "7FDB8A"), ("snakeD", "157A42"), ("stoneD", "C8AE7C"), ("water", "3AA6E8"),
                      ("waterL", "A8DEFA"), ("white", "FFFDF4"), ("dark", "1E2418"), ("glint", "FFFFFF"),
                      ("mouth", "3A1414"), ("tongue", "FF6F86")):
        a.paint(key, code)
    t = rare_stand(a, 1.55)
    part(a, "Bowl", "Stand", (0, 0, t))
    a.prism("stoneD", S.octagon(-0.42, 0.42, -0.42, 0.42, 0.12), t, t + 0.22)
    a.prism("stone", S.octagon(-1.0, 1.0, -1.0, 1.0, 0.3), t + 0.2, t + 0.62)
    a.frame("stoneD", S.octagon(-1.04, 1.04, -1.04, 1.04, 0.31), 0.1, t + 0.6, t + 0.68, axis="z", bevel=0)
    a.prism("water", S.octagon(-0.92, 0.92, -0.92, 0.92, 0.27), t + 0.58, t + 0.64, bevel=0)
    for x, y in ((-0.5, -0.4), (0.3, 0.5), (0.62, -0.1)):
        a.box("waterL", x - 0.1, x + 0.1, y - 0.03, y + 0.03, t + 0.635, t + 0.655, bevel=0)
    # тело кольцом в воде и столбом вверх
    part(a, "Body", "Bowl", (0, 0.15, t + 0.64))
    ring = [(0.55 * math.cos(math.radians(a_)), 0.15 + 0.5 * math.sin(math.radians(a_)), t + 0.66 + 0.012 * k)
            for k, a_ in enumerate(range(-80, 250, 40))]
    tube(a, ("snake", "snakeD"), ring + [(0.05, 0.1, t + 0.9), (0.0, 0.0, t + 1.3), (0.0, -0.04, t + 1.66)], 0.2)
    a.box("snakeL", -0.1, 0.1, -0.24, -0.16, t + 0.86, t + 1.6, bevel=0)
    # капюшон: широкий, плоский, золотой узор из квадратов
    part(a, "Hood", "Body", (0, 0.02, t + 1.6))
    hood = [(-0.22, t + 1.3), (-0.56, t + 1.62), (-0.62, t + 1.98), (-0.44, t + 2.3), (0.0, t + 2.42), (0.44, t + 2.3),
            (0.62, t + 1.98), (0.56, t + 1.62), (0.22, t + 1.3)]
    a.prism("snake", hood, 0.0, 0.14, axis="y")
    a.prism("snakeL", [(x * 0.82, z - (z - t - 1.9) * 0.18) for x, z in hood], -0.03, 0.01, axis="y")
    for x, z in ((-0.4, 1.66), (0.4, 1.66), (-0.46, 1.96), (0.46, 1.96), (-0.3, 2.2), (0.3, 2.2), (0.0, 2.3)):
        a.box("gold", x - 0.05, x + 0.05, -0.055, -0.025, t + z - 0.05, t + z + 0.05, bevel=0)
    # голова: самодовольная, полуопущенные веки, рот открыт — из него струя
    part(a, "Head", "Hood", (0, -0.1, t + 1.7))
    hz = t + 1.98
    a.prism("snake", S.octagon(-0.24, 0.24, -0.36, -0.02, 0.1), hz - 0.2, hz + 0.18)
    a.prism("snakeL", S.octagon(-0.18, 0.18, -0.42, -0.3, 0.03), hz - 0.21, hz - 0.04)
    for s in (-1, 1):
        round_eye(a, (s * 0.12, -0.36, hz + 0.06), 0.08, look=(0.2 * s, 0), pupil=0.6, lid=0.45, lid_key="snakeD")
    a.box("mouth", -0.08, 0.08, -0.44, -0.4, hz - 0.17, hz - 0.08, bevel=0)
    # струя дугой в чашу и брызги
    part(a, "Stream", "Head", (0, -0.42, hz - 0.12))
    arc = [(0.04, -0.42, hz - 0.12), (0.22, -0.56, hz - 0.06), (0.42, -0.72, hz + 0.08), (0.58, -0.84, hz - 0.08),
           (0.66, -0.86, hz - 0.56), (0.66, -0.82, t + 0.66)]
    for i in range(len(arc) - 1):
        w = 0.12 - 0.012 * i
        bar(a, "water" if i % 2 == 0 else "waterL", arc[i], arc[i + 1], w * (1 + 0.04 * (i % 2)), w)
    for x, y, z in ((0.5, -0.92, 0.78), (0.82, -0.7, 0.74), (0.74, -0.96, 0.86)):
        a.box("waterL", x - 0.04, x + 0.04, y - 0.04, y + 0.04, t + z - 0.04, t + z + 0.04, bevel=0)
    a.face = (0, -0.38, hz)
    a.closeup = ((-1.8, -1.6, t + 2.2), (-0.3, 0.05, t + 1.9))
    a.pose = {"Hood": ((0, 0, 0), (0, 0, 0)), "Head": ((8, 0, -10), (0, 0, 0)), "Stream": ((10, 0, 0), (0, 0, 0)),
              "Body": ((0, 0, 6), (0, 0, 0))}
    return a


# ── 18. Смерч-озорник: перевёрнутый ступенчатый конус из песка (кремовый, песочный, оранжевый) со спиральными
#        полосами; нахальная рожица на неподвижном ярусе — подмигивает, язык; вокруг кружат украденные вещи: соломенная
#        шляпа, полосатый носок, горшок с кактусом. Ярусы крутятся в разные стороны. Без рук и торса ─────────────────


def dust_devil():
    a = S.Art("Art_DustDevil", ring_z0=1.4)
    d39v2(a)
    a.paint("sand", "F0C070", rings=True)
    a.paint("orange", "E8903A", rings=True)
    a.paint("cream", "FFE5B8", rings=True)
    for key, code in (("swirl", "C87A32"), ("straw", "F2D27A"), ("strawD", "C9A04A"), ("red", "E53935"),
                      ("white", "FFFDF4"), ("pot", "C8643A"), ("green", "3FAE46"), ("dark", "231816"),
                      ("glint", "FFFFFF"), ("mouth", "5A1A20"), ("tongue", "FF6F86"), ("dust", "E8D2A6")):
        a.paint(key, code)
    t = rare_stand(a, 1.5)
    for x, y, r in ((0.0, 0.0, 0.2), (-0.26, 0.08, 0.12), (0.24, -0.06, 0.13), (0.06, 0.26, 0.1)):
        a.prism("dust", S.octagon(x - r, x + r, y - r, y + r, r * 0.3), t, t + 0.1 + r * 0.4)
    tiers = []
    for k in range(7):
        r = 0.16 + 0.105 * k
        dx = 0.09 * math.cos(math.radians(k * 65))
        z0 = t + 0.08 + 0.3 * k
        tiers.append((r, dx, z0))
    keys = ("sand", "orange", "cream")
    groups = (("TierLow", (0, 1, 2)), ("Body", (3, 4)), ("TierHigh", (5, 6)))
    for name, idx in groups:
        r0, dx0, z00 = tiers[idx[0]]
        part(a, name, "Stand" if name == "TierLow" else ("TierLow" if name == "Body" else "Body"), (dx0, 0, z00))
        for k in idx:
            r, dx, z0 = tiers[k]
            a.prism(keys[k % 3], S.octagon(dx - r, dx + r, -r, r, r * 0.3), z0, z0 + 0.32)
            ang = 30 + 50 * k
            q = (dx + r * 0.95 * math.cos(math.radians(ang)), r * 0.95 * math.sin(math.radians(ang)), z0 + 0.16)
            a.box("swirl", q[0] - 0.24, q[0] + 0.24, q[1] - 0.05, q[1] + 0.05, z0 + 0.1, z0 + 0.22, bevel=0,
                  matrix=tilt(q, "Z", ang + 90) @ tilt(q, "X", 12))
    # рожица на ярусе 4: подмигивает, язык
    r, dx, z0 = tiers[4]
    fy = -r
    fz = z0 + 0.16
    round_eye(a, (dx - 0.18, fy, fz + 0.04), 0.12, look=(0.4, 0.2), pupil=0.55)
    closed_eye(a, (dx + 0.2, fy, fz + 0.06), 0.18)
    r3, dx3, z03 = tiers[3]
    a.box("mouth", dx3 - 0.16, dx3 + 0.2, -r3 - 0.04, -r3 + 0.01, z03 + 0.2, z03 + 0.27, bevel=0)
    a.box("tongue", dx3 + 0.04, dx3 + 0.16, -r3 - 0.05, -r3 - 0.01, z03 + 0.1, z03 + 0.22, bevel=0)
    # украденные вещи кружат вокруг
    part(a, "Loot", "Body", (0, 0, t + 1.3))
    hx, hy, hz = -1.05, -0.2, t + 1.5
    a.prism("straw", ngon(hx, hy, 0.3, 10), hz, hz + 0.05, matrix=tilt((hx, hy, hz), "Y", 20))
    a.prism("straw", ngon(hx, hy, 0.16, 8), hz + 0.04, hz + 0.22, matrix=tilt((hx, hy, hz), "Y", 20))
    a.frame("red", ngon(hx, hy, 0.165, 8), 0.03, hz + 0.06, hz + 0.1, axis="z", bevel=0, matrix=tilt((hx, hy, hz), "Y", 20))
    sx, sy, sz = 1.0, -0.35, t + 1.1
    sock = tilt((sx, sy, sz), "Y", -30)
    for k in range(4):
        w = 0.09 - 0.004 * k
        a.box("red" if k % 2 == 0 else "white", sx - w, sx + w, sy - w + 0.01, sy + w - 0.01, sz + 0.12 * k,
              sz + 0.12 * k + 0.12, bevel=0, matrix=sock)
    a.box("red", sx - 0.09, sx + 0.26, sy - 0.075, sy + 0.075, sz - 0.14, sz + 0.0, matrix=sock)
    px, py, pz = 0.45, 0.95, t + 1.9
    a.frustum("pot", (px - 0.11, px + 0.11, py - 0.11, py + 0.11), (px - 0.15, px + 0.15, py - 0.15, py + 0.15), pz, pz + 0.22)
    a.prism("green", S.octagon(px - 0.08, px + 0.08, py - 0.08, py + 0.08, 0.03), pz + 0.2, pz + 0.48)
    # кольца ветра ниже рта и выше бровей — не пересекают лицо
    for k, (z, r, tilt_x, key) in enumerate(((0.62, 0.58, 10, "cream"), (2.0, 1.02, -6, "swirl"), (2.3, 1.1, 5, "cream"))):
        m = tilt((0, 0, t + z), "X", tilt_x) @ tilt((0, 0, t + z), "Y", 5 - 5 * k)
        a.frame(key, ngon(0, 0.02 * k, r, 10), 0.05, t + z - 0.025, t + z + 0.025, axis="z", bevel=0, matrix=m)
    a.face = (0, -0.6, t + 1.4)
    a.closeup = ((-2.0, -1.5, t + 1.6), (-0.4, 0.0, t + 1.5))
    a.pose = {"TierLow": ((0, 0, 30), (0, 0, 0)), "TierHigh": ((0, 0, -35), (0, 0, 0)), "Loot": ((0, 0, 60), (0, 0, 0)),
              "Body": ((0, 0, -10), (0, 0, 0))}
    return a


# ── 19. Хамелеон-калейдоскоп: хамелеон-зазнайка в профиль на ветке; тело из пяти разноцветных долек (бирюза, оранжевый,
#        пурпур, жёлтый, лайм — не порядок радуги), синий шлем-гребень, глаз-турель — трубка калейдоскопа со звездой на
#        торце; хвост квадратной спиралью; цепкие лапки. Цвет в игре не меняется ─────────────────────────────────────


def kaleido_chameleon():
    a = S.Art("Art_KaleidoChameleon", ring_z0=1.2)
    d39v2(a)
    for key, code in (("c1", "2EC4B6"), ("c2", "FF8A2E"), ("c3", "9B4DE0"), ("c4", "FFD23F"), ("c5", "8ED63F")):
        a.paint(key, code, rings=True)
    for key, code in (("casque", "3A7BE0"), ("casqueD", "2A5AB0"), ("wood", "8A5A34"), ("woodD", "6A4226"),
                      ("leaf", "3FAE46"), ("white", "FFFDF4"), ("dark", "231816"), ("glint", "FFFFFF"),
                      ("mouth", "3A1414"), ("tongue", "FF6F86"), ("pink", "FF6FAE")):
        a.paint(key, code)
    t = rare_stand(a, 1.55)
    part(a, "Branch", "Stand", (0.9, 0.1, t))
    stripe_chain(a, ("wood", "woodD"), [(1.0, 0.15, t), (0.95, 0.1, t + 0.5), (0.6, 0.05, t + 0.86), (0.0, 0.0, t + 0.98),
                                        (-0.7, 0.0, t + 0.92), (-1.15, 0.05, t + 1.1)], 0.16, 0.15)
    for x, z in ((-1.2, 1.18), (1.05, 0.06)):
        a.box("leaf", x - 0.12, x + 0.12, -0.04, 0.12, t + z - 0.05, t + z + 0.05, matrix=tilt((x, 0.04, t + z), "Y", 30))
    zb = t + 1.06
    part(a, "Body", "Branch", (0, 0, zb + 0.1))
    slices = (("c1", -0.62, -0.36, 0.42), ("c2", -0.36, -0.1, 0.5), ("c3", -0.1, 0.16, 0.52), ("c4", 0.16, 0.42, 0.46),
              ("c5", 0.42, 0.66, 0.36))
    for k, (key, x0, x1, h) in enumerate(slices):
        a.prism(key, S.octagon(zb + 0.06, zb + 0.06 + h, -0.22, 0.22, 0.08), x0 - 0.005 * (k % 2), x1 + 0.005 * (k % 2),
                axis="x")
        a.box(key, x0 + 0.04, x1 - 0.04, -0.06, 0.06, zb + 0.04 + h, zb + 0.14 + h, bevel=0)
    for name, xs in (("LegsF", (-0.5, -0.3)), ("LegsB", (0.3, 0.52))):
        part(a, name, "Body", (sum(xs) / 2, 0, zb + 0.1))
        for x in xs:
            for s in (-1, 1):
                bar(a, "c1" if name == "LegsF" else "c5", (x, s * 0.18, zb + 0.12), (x + 0.04, s * 0.14, zb - 0.06), 0.08, 0.08)
                a.box("casqueD", x - 0.04, x + 0.12, s * 0.06, s * 0.16, zb - 0.1, zb - 0.02, bevel=0)
    # голова: синий шлем-гребень, глаз-турель с калейдоскопом к игроку, рот, язык
    part(a, "Head", "Body", (-0.64, 0, zb + 0.32))
    a.prism("casque", [(-0.62, zb + 0.08), (-0.62, zb + 0.52), (-0.82, zb + 0.86), (-1.12, zb + 0.4), (-1.06, zb + 0.14)],
            -0.2, 0.2, axis="y")
    a.box("mouth", -1.1, -0.82, -0.205, -0.17, zb + 0.18, zb + 0.22, bevel=0)
    a.box("pink", -1.0, -0.9, -0.21, -0.18, zb + 0.24, zb + 0.29, bevel=0)
    part(a, "Eye", "Head", (-0.86, -0.18, zb + 0.4))
    me = Matrix.Translation((-0.86, -0.18, zb + 0.4)) @ Matrix.Rotation(math.radians(90), 4, "X")
    a.prism("c3", ngon(0, 0, 0.14, 8), 0.0, 0.2, matrix=me)
    a.prism("c4", ngon(0, 0, 0.16, 8), 0.18, 0.24, matrix=me)
    star = ["..#..", ".###.", "#####", ".###.", "..#.."]
    cell = 0.04
    for r_, row in enumerate(star):
        for c_, ch in enumerate(row):
            if ch == "#":
                key = ("c1", "c2", "c3", "c5", "c1")[(r_ + c_) % 5]
                x = -0.86 - 0.1 + c_ * cell
                z = zb + 0.4 + 0.1 - r_ * cell
                a.box(key, x, x + cell, -0.465, -0.43, z - cell, z, bevel=0)
    a.box("dark", -0.885, -0.835, -0.48, -0.46, zb + 0.375, zb + 0.425, bevel=0)
    part(a, "EyeB", "Head", (-0.86, 0.18, zb + 0.4))
    a.prism("c3", ngon(0, 0, 0.13, 8), 0.0, 0.16, matrix=Matrix.Translation((-0.86, 0.18, zb + 0.4)) @ Matrix.Rotation(math.radians(-90), 4, "X"))
    part(a, "Tongue", "Head", (-1.1, 0, zb + 0.2))
    bar(a, "tongue", (-1.1, -0.02, zb + 0.2), (-1.42, -0.06, zb + 0.32), 0.05, 0.05)
    a.box("tongue", -1.5, -1.38, -0.12, 0.0, zb + 0.28, zb + 0.4)
    # хвост квадратной спиралью
    part(a, "Tail", "Body", (0.66, 0, zb + 0.3))
    spiral = [(0.66, 0.0, zb + 0.3), (0.98, 0.0, zb + 0.3), (0.98, 0.0, zb - 0.22), (0.7, 0.0, zb - 0.22),
              (0.7, 0.0, zb + 0.02), (0.86, 0.0, zb + 0.02), (0.86, 0.0, zb - 0.1)]
    stripe_chain(a, ("c5", "c4", "c3", "c2", "c1", "c5"), spiral, 0.14, 0.14)
    a.face = (-0.86, -0.3, zb + 0.4)
    a.closeup = ((-0.2, -2.4, zb + 0.8), (-0.1, -0.2, zb + 0.35))
    a.pose = {"Eye": ((0, 30, 0), (0, 0, 0)), "Tongue": ((0, 0, 0), (-0.25, 0, 0.05)), "Tail": ((0, 20, 0), (0, 0, 0)),
              "Head": ((0, -10, 0), (0, 0, 0)), "EyeB": ((0, -20, 0), (0, 0, 0))}
    return a


# ── 21. Рыба-мираж: мечтательная рыбка в парящем кубе воды — голова торчит из левой грани, хвост из правой, плавник
#        спереди; под кубом песчаный бугорок и волны марева; пузырьки над кубом. Розово-оранжевая, не рыба-клоун (без
#        белых и чёрных полос) ───────────────────────────────────────────────────────────────────────────────────────


def mirage_fish():
    a = S.Art("Art_MirageFish", ring_z0=1.4)
    d39v2(a)
    a.paint("water", "39C9D4", rings=True)
    a.paint("fish", "FF8A6A", rings=True)
    for key, code in (("waterL", "A6EEF5"), ("waterD", "1FA3B0"), ("fishD", "F0645A"), ("fin", "FFB060"),
                      ("lips", "FF5C8A"), ("sand", "E8B460"), ("haze", "FFE9C2"), ("white", "FFFDF4"),
                      ("dark", "231816"), ("glint", "FFFFFF"), ("lid", "F0645A")):
        a.paint(key, code)
    t = rare_stand(a, 1.45)
    # марево над песчаным холмиком — своя часть Haze (решение владельца 2026-11-13: при скрытой подставке марево
    # остаётся видимым; холмик — его основание, без него полосы легли бы на пол). Геометрия прежняя
    part(a, "Haze", "Stand", (0, 0, t))
    a.prism("sand", S.octagon(-0.7, 0.7, -0.5, 0.5, 0.2), t, t + 0.16)
    a.prism("sand", S.octagon(-0.42, 0.42, -0.3, 0.3, 0.12), t + 0.14, t + 0.26)
    for k, (w, z) in enumerate(((0.62, 0.42), (0.5, 0.6))):
        for s in (-1, 1):
            yb = -0.1 - 0.012 * k - 0.006 * (s > 0)
            bar(a, "haze", (s * w, yb, t + z), (s * w * 0.4, yb, t + z + 0.06), 0.05, 0.04, bevel=0)
            bar(a, "haze", (s * w * 0.4, yb - 0.003, t + z + 0.06), (0.0, yb - 0.003, t + z - 0.01 * k), 0.05, 0.034,
                bevel=0)
    cz = t + 1.55
    part(a, "Cube", "Stand", (0, 0, cz))
    a.box("water", -0.5, 0.5, -0.46, 0.46, cz - 0.46, cz + 0.46)
    for sx in (-1, 1):
        for sy in (-1, 1):
            a.box("waterL", sx * 0.5 - 0.05 * (sx > 0), sx * 0.5 + 0.05 * (sx < 0), sy * 0.46 - 0.05 * (sy > 0),
                  sy * 0.46 + 0.05 * (sy < 0), cz - 0.4, cz + 0.4, bevel=0)
    a.box("waterL", -0.44, 0.44, -0.4, 0.4, cz + 0.455, cz + 0.49, bevel=0)
    for x, z, w in ((-0.3, 0.26, 0.1), (0.18, -0.2, 0.06), (0.3, 0.3, 0.05)):
        a.box("white", x - w / 2, x + w / 2, -0.49, -0.455, cz + z - w / 2, cz + z + w / 2, bevel=0)
    a.box("glint", -0.42, -0.32, -0.495, -0.46, cz + 0.3, cz + 0.4, bevel=0)
    # голова из левой грани: большие мечтательные глаза с веками, губки бантиком
    part(a, "Head", "Cube", (-0.5, 0, cz))
    a.prism("fish", S.octagon(cz - 0.3, cz + 0.32, -0.3, 0.3, 0.1), -0.86, -0.46, axis="x")
    a.prism("fish", S.octagon(cz - 0.2, cz + 0.2, -0.22, 0.22, 0.07), -0.98, -0.84, axis="x")
    a.box("lips", -1.04, -0.96, -0.1, 0.1, cz - 0.1, cz - 0.01)
    for s in (-1, 1):
        round_eye(a, (-0.68 + s * 0.13, -0.3, cz + 0.12), 0.1, look=(0, 0.5), pupil=0.6, lid=0.42, lid_key="lid")
        bar(a, "dark", (-0.68 + s * 0.13 + s * 0.08, -0.385, cz + 0.2), (-0.68 + s * 0.13 + s * 0.13, -0.385, cz + 0.25),
            0.022, 0.02, bevel=0)
    a.box("fishD", -0.98, -0.6, -0.31, -0.29, cz - 0.24, cz - 0.18, bevel=0)
    # хвост из правой грани
    part(a, "Tail", "Cube", (0.5, 0, cz))
    a.prism("fishD", S.octagon(cz - 0.16, cz + 0.16, -0.14, 0.14, 0.05), 0.46, 0.7, axis="x")
    a.extrude("fin", [(0.66, cz), (1.02, cz + 0.44), (1.1, cz + 0.36), (0.86, cz + 0.06), (0.86, cz - 0.06),
                      (1.1, cz - 0.36), (1.02, cz - 0.44)], -0.06, 0.06, axis="y")
    for z in (0.18, -0.18):
        a.box("fishD", 0.84, 0.98, -0.08, -0.06, cz + z - 0.03, cz + z + 0.03, bevel=0)
    part(a, "Fin", "Cube", (-0.1, -0.46, cz - 0.15))
    a.prism("fin", [(-0.22, cz - 0.1), (0.1, cz - 0.1), (0.2, cz - 0.4), (-0.12, cz - 0.3)], -0.62, -0.44, axis="y")
    part(a, "Bubbles", "Cube", (-0.7, -0.1, cz + 0.4))
    for x, z, r in ((-0.74, 0.5, 0.07), (-0.62, 0.74, 0.055), (-0.76, 0.96, 0.045)):
        a.prism("waterL", ngon(x, cz + z, r, 8), -0.14, -0.06, axis="y")
    a.face = (-0.7, -0.3, cz + 0.05)
    a.closeup = ((1.2, -2.2, cz + 0.6), (0.1, -0.46, cz))
    a.pose = {"Cube": ((0, 0, 0), (0, 0, 0.12)), "Tail": ((0, 0, 25), (0, 0, 0)), "Head": ((0, 0, -8), (0, 0, 0)),
              "Fin": ((20, 0, 0), (0, 0, 0)), "Bubbles": ((0, 0, 0), (0, 0, 0.15))}
    return a


RARE2 = [("AquariumCamel", aquarium_camel, "Верблюд-аквариум", "Rare"),
         ("CactusAcrobats", cactus_acrobats, "Кактусы-акробаты", "Rare"),
         ("DrillWorm", drill_worm, "Песчаный червь-бурильщик", "Rare"),
         ("FanVulture", fan_vulture, "Гриф-вентилятор", "Rare"),
         ("CobraFountain", cobra_fountain, "Кобра-фонтан", "Rare"),
         ("DustDevil", dust_devil, "Смерч-озорник", "Rare"),
         ("KaleidoChameleon", kaleido_chameleon, "Хамелеон-калейдоскоп", "Rare"),
         ("MirageFish", mirage_fish, "Рыба-мираж", "Rare")]



# ══ EPIC №22–27 (подставка — золотая горка, как у Epic босса 3) ═══════════════════════════════════════════════

# ── 22. Кит-бархан: добрый песчаный кит выныривает из дюны — передняя половина поднята наискось к игроку, спина
#        песочная в тёмных полосах, кремовое брюхо с бороздками, большой добрый глаз и улыбка; из дыхала бьёт фонтан
#        песка; позади из дюны торчит хвост-фонтан. Дюна — своя часть (в игре остаётся) ───────────────────────────────


def ripples(a, key, pts, w=0.07):
    """Песчаная рябь: волнистый валик сечением w по точкам pts, без фаски (мелкая деталь — мало треугольников);
    звенья заходят друг в друга на w/2 (без щелей в изгибах), соседние — на 4 % разной толщины (без совпадающих граней)."""
    for i in range(len(pts) - 1):
        p0, p1 = Vector(pts[i]), Vector(pts[i + 1])
        d = (p1 - p0).normalized() * w * 0.5
        k = 1.0 + 0.04 * (i % 2)
        bar(a, key, tuple(p0 - d * (i > 0)), tuple(p1 + d * (i < len(pts) - 2)), w * k, w * k, bevel=0)


def dune_whale():
    a = S.Art("Art_DuneWhale", ring_z0=1.0)
    d39v2(a)
    a.paint("back", "E59A48", rings=True)
    a.paint("sand", "F3D99E", rings=True)
    for key, code in (("stripe", "B9702E"), ("belly", "FFE4C0"), ("groove", "D9B98A"), ("sandL", "FBE8C0"),
                      ("sandD", "D6AE6C"), ("white", "FFFDF4"), ("dark", "231816"), ("glint", "FFFFFF"),
                      ("mouth", "5A1A20"), ("cheek", "FFB08A"), ("ripple", "C9803C")):
        a.paint(key, code)
    a.paint("duneL", "F7C67C", rings=True)  # наветренный склон гребня
    a.paint("slip", "B8692C", rings=True)  # крутой подветренный склон
    t = epic_stand(a, 1.72)
    # v2: у тела-бархана поверхностей больше — карте существа нужно больше места (плотность не ниже эталона №20):
    # скрытой в игре подставке меньше
    for key in ("gold2", "goldS", "goldL"):
        a.uv_boost[key] = 0.2
    part(a, "Dune", "Stand", (0, 0, t))
    # низ дюны до пола (v2, проверка импорта 2026-11-13): зарытая часть кита уходит ниже верха подставки; в игре
    # подставку прячут — без этого слоя дюна висела бы над полом на торчащем куске тела. При подставке слой в ней
    a.paint("sandBase", "F3D99E", rings=True)
    a.uv_boost["sandBase"] = 0.3  # ровный бок песка, виден только без подставки — места в карте меньше
    a.prism("sandBase", S.octagon(-1.3, 1.3, -1.18, 1.24, 0.38), 0.004, t + 0.02)
    for (x0, x1, y0, y1, c, z0, z1, key) in ((-1.42, 1.42, -1.3, 1.36, 0.42, 0.0, 0.24, "sand"),
                                             (-1.15, 1.12, -1.02, 1.12, 0.36, 0.22, 0.46, "sandL"),
                                             (-0.86, 0.86, -0.72, 0.9, 0.28, 0.44, 0.62, "sand")):
        a.prism(key, S.octagon(x0, x1, y0, y1, c), t + z0, t + z1)
    for x, y, z in ((-0.52, -0.3, 0.66), (0.42, -0.48, 0.66), (0.62, 0.3, 0.68), (-0.2, 0.62, 0.68)):
        a.box("sandD", x - 0.07, x + 0.07, y - 0.07, y + 0.07, t + z - 0.06, t + z + 0.06)
    # кит: передняя половина наискось вверх к игроку (ось x — к голове)
    p0 = Vector((0.24, 0.26, t + 0.42))
    d = Vector((-0.74, -0.46, 0.5)).normalized()
    M = Matrix.Translation(p0) @ d.to_track_quat("X", "Z").to_matrix().to_4x4()
    part(a, "Whale", "Dune", tuple(p0 + d * 0.3))
    with_matrix(a, M)
    for (x0, x1, zl, zh, w, c, key) in ((-0.5, 0.42, -0.56, 0.6, 0.56, 0.18, "back"), (0.4, 1.1, -0.52, 0.62, 0.53, 0.17, "back"),
                                        (1.08, 1.55, -0.44, 0.56, 0.47, 0.15, "back"), (1.53, 1.72, -0.32, 0.42, 0.37, 0.11, "back")):
        a.prism(key, S.octagon(zl, zh, -w, w, c), x0, x1, axis="x")
    a.prism("belly", S.octagon(-0.6, -0.36, -0.42, 0.42, 0.08), 0.1, 1.6, axis="x")
    for z in (-0.5, -0.44):
        a.box("groove", 0.3, 1.5, -0.43, 0.43, z - 0.012, z + 0.012, bevel=0)
    # тело — бархан (правка владельца 2026-11-13: «подчеркни сходство тела с дюной»; вместо прямых полос-рёбер).
    # За головой кит — дюна: острый гребень; к игроку (+y) пологий светлый наветренный склон, он же песчаный покров
    # бока с волнистым нижним краем; назад (−y) тёмный крутой подветренный склон с языками осыпи; с гребня ветер
    # сдувает песчинки. Рябь — две-три крупные волны (мелкая на телефоне — шум). Голова, хвост и ласт — оранжевая кожа
    crest = ((-0.48, 0.44, 0.44, -0.15, 0.92, 0.54, 0.5, -0.55), (0.42, 1.04, 0.46, -0.1, 0.86, 0.51, 0.54, -0.5))
    for x0, x1, zb_, yc, zc, yo, zo, ys in crest:  # тёмная кромка чуть выше светлой — острый гребень
        a.prism("duneL", [(zb_, yo), (zo, yo), (zc, yc), (zb_, yc)], x0, x1, axis="x")
        a.prism("slip", [(zb_, yc + 0.02), (zc + 0.02, yc + 0.02), (zb_, ys)], x0 - 0.01, x1 + 0.01, axis="x")

    def on_slope(x, u, dy=0.0):
        x0, x1, zb_, yc, zc, yo, zo, ys = crest[0] if x < 0.43 else crest[1]
        y = yc + u * (yo - yc) + dy
        return (x, y, zc + (y - yc) * (zo - zc) / (yo - yc))

    for k, u in enumerate((0.36, 0.74)):  # крупная рябь вдоль гребня
        xs = (-0.36 + 0.1 * k, -0.02, 0.32, 0.66, 0.96 - 0.1 * k)
        ripples(a, "ripple", [on_slope(x, u, 0.05 * (-1) ** (i + k)) for i, x in enumerate(xs)])
    for (x0, x1, y0, y1, top, edge) in ((-0.47, 0.43, 0.53, 0.59, 0.5, ((0.43, -0.1), (0.28, -0.24), (0.1, -0.13),
                                                                         (-0.08, -0.3), (-0.26, -0.19), (-0.47, -0.32))),
                                        (0.41, 0.98, 0.5, 0.56, 0.54, ((0.98, 0.1), (0.84, -0.04), (0.68, 0.04),
                                                                       (0.52, -0.12), (0.41, -0.06)))):
        a.extrude("duneL", [(x0, top), (x1, top)] + list(edge), y0, y1, axis="y")  # песчаный покров бока
    for k, (z, xs) in enumerate(((0.3, (-0.4, -0.06, 0.28, 0.62, 0.92)), (0.02, (-0.36, -0.06, 0.24, 0.5)))):
        ripples(a, "ripple", [(x, 0.59 if x < 0.42 else 0.56, z + 0.05 * (-1) ** (i + k)) for i, x in enumerate(xs)])
    for x, w in ((-0.2, 0.2), (0.62, 0.17)):  # языки осыпи по крутому склону: ступенями, шире книзу
        _, _, zb_, yc, zc, _, _, ys = crest[0] if x < 0.43 else crest[1]
        s0, s1 = Vector((x, yc + 0.02, zc + 0.02)), Vector((x, ys, zb_))
        nrm = Vector((0.0, -(s1 - s0).z, (s1 - s0).y)).normalized()
        nrm = nrm if nrm.y < 0 else -nrm  # наружу от крутого склона
        top, bot = s0.lerp(s1, 0.08) + nrm * 0.012, s0.lerp(s1, 0.86) + nrm * 0.012
        for i, (f0, f1, k) in enumerate(((0.0, 0.4, 0.45), (0.36, 0.72, 0.72), (0.68, 1.0, 1.0))):
            bar(a, "ripple", tuple(top.lerp(bot, f0)), tuple(top.lerp(bot, f1)), w * k, 0.04 + 0.006 * i, bevel=0)
    for x, dy, dz, r in ((-0.3, -0.16, 0.08, 0.05), (-0.22, -0.3, 0.16, 0.04), (0.56, -0.15, 0.08, 0.05),
                         (0.66, -0.29, 0.15, 0.04), (0.74, -0.42, 0.2, 0.03)):  # песок с гребня по ветру
        _, _, _, yc, zc, _, _, _ = crest[0] if x < 0.43 else crest[1]
        a.box("sandL", x - r, x + r, yc + dy - r, yc + dy + r, zc + dz - r, zc + dz + r, bevel=0)
    a.box("mouth", 1.0, 1.73, 0.44, 0.5, -0.22, -0.16, bevel=0)
    a.box("cheek", 1.18, 1.32, 0.46, 0.5, -0.06, 0.04, bevel=0)
    with_matrix(a, M @ Matrix.Rotation(math.pi, 4, "Z"))
    round_eye(a, (-1.32, -0.48, 0.16), 0.13, look=(-0.3, 0.2), pupil=0.62)
    with_matrix(a, None)
    part(a, "Flipper", "Whale", tuple(M @ Vector((0.62, 0.5, -0.3))))
    with_matrix(a, M)
    a.box("back", 0.48, 0.92, 0.52, 0.62, -0.5, -0.24, matrix=tilt((0.62, 0.56, -0.3), "X", 25))
    with_matrix(a, None)
    # фонтан песка из дыхала: столбик кубиков, наверху рассыпается
    top = M @ Vector((1.22, 0.0, 0.62))
    part(a, "Spout", "Whale", tuple(top))
    for k in range(5):
        r = 0.09 + 0.012 * k
        q = top + Vector((0.0, 0.0, 0.08 + 0.17 * k))
        a.box("sandL" if k % 2 else "sand", q.x - r, q.x + r, q.y - r, q.y + r, q.z - 0.09, q.z + 0.09)
    for ang in range(0, 360, 72):
        q = top + Vector((0.26 * math.cos(math.radians(ang)), 0.26 * math.sin(math.radians(ang)), 0.84 - 0.1 * (ang % 144 == 0)))
        a.box("sandL", q.x - 0.07, q.x + 0.07, q.y - 0.07, q.y + 0.07, q.z - 0.07, q.z + 0.07)
    # хвост торчит из дюны позади
    part(a, "Tail", "Dune", (0.82, 0.74, t + 0.5))
    stripe_chain(a, ("back", "stripe"), [(0.82, 0.74, t + 0.5), (0.9, 0.82, t + 0.86), (0.98, 0.9, t + 1.12)], 0.26, 0.22)
    mt = Matrix.Translation((0.98, 0.9, t + 1.12)) @ Matrix.Rotation(math.radians(-45), 4, "Z")
    a.prism("back", [(0.0, -0.05), (0.5, 0.18), (0.58, 0.34), (0.12, 0.16)], -0.05, 0.05, axis="y", matrix=mt)
    a.prism("back", [(0.0, -0.05), (-0.12, 0.16), (-0.58, 0.34), (-0.5, 0.18)], -0.045, 0.045, axis="y", matrix=mt)
    a.face = tuple(M @ Vector((1.3, 0.5, 0.05)))
    a.closeup = ((1.8, -1.6, t + 1.3), (0.4, 0.1, t + 0.8))
    a.pose = {"Whale": ((0, -12, 0), (0, 0, 0)), "Tail": ((0, 0, 20), (0, 0, 0)), "Spout": ((0, 0, 0), (0, 0, 0.15)),
              "Flipper": ((25, 0, 0), (0, 0, 0))}
    return a


# ── 23. Черепаха-остров: старая мудрая черепаха несёт в панцире-чаше оазис — песчаный островок с озером, две пальмы,
#        красно-белый шатёр, лодочка, водопад через край панциря; лазурный панцирь с золотой каймой; седые брови,
#        бородка, сонные глаза, добрая улыбка; ноги-тумбы. Не №5 и не Torterra (оазис с шатром, а не деревья и камни) ──


def island_turtle():
    a = S.Art("Art_IslandTurtle", ring_z0=0.8)
    d39v2(a)
    a.paint("shell", "3AA6E8", rings=True)
    a.paint("skin", "C86B4E", rings=True)
    for key, code in (("shellD", "2A7FC0"), ("skinD", "A65438"), ("sand", "F2C46D"), ("water", "35C6D6"),
                      ("waterL", "A6EEF5"), ("trunk", "9A6534"), ("trunkD", "7A4A28"), ("leaf", "3FAE46"),
                      ("leafD", "2E8B3A"), ("red", "E53935"), ("white", "FFFDF4"), ("wood", "8A5A34"),
                      ("brow", "F4F4F4"), ("dark", "231816"), ("glint", "FFFFFF"), ("mouth", "5A1A20"),
                      ("nail", "FFF1D6"), ("cheek", "FF9E8A")):
        a.paint(key, code)
    t = epic_stand(a, 1.76)
    for x, y, name in ((-0.86, -0.52, "LegFL"), (0.86, -0.52, "LegFR"), (-0.82, 0.62, "LegBL"), (0.82, 0.62, "LegBR")):
        part(a, name, "Body", (x * 0.9, y, t + 0.42))
        a.box("skin", x - 0.22, x + 0.22, y - 0.22, y + 0.22, t, t + 0.48)
        if y < 0:
            for dx in (-0.12, 0.0, 0.12):
                a.box("nail", x + dx - 0.045, x + dx + 0.045, y - 0.27, y - 0.2, t + 0.005, t + 0.08, bevel=0)
    part(a, "Body", "Stand", (0, 0.05, t + 0.4))
    a.prism("shellD", S.octagon(-1.02, 1.02, -0.88, 0.98, 0.32), t + 0.34, t + 0.52)
    a.prism("shell", S.octagon(-1.14, 1.14, -0.98, 1.08, 0.36), t + 0.5, t + 0.9)
    a.frame("gold", S.octagon(-1.18, 1.18, -1.02, 1.12, 0.37), 0.12, t + 0.88, t + 0.98, axis="z", bevel=0)
    for x in (-0.6, 0.0, 0.6):
        a.box("gold", x - 0.06, x + 0.06, -1.0, -0.96, t + 0.56, t + 0.84, bevel=0)
    a.prism("water", S.octagon(-1.02, 1.02, -0.86, 0.96, 0.32), t + 0.86, t + 0.93, bevel=0)
    a.prism("sand", S.octagon(-0.2, 0.86, -0.3, 0.86, 0.22), t + 0.9, t + 1.04)
    a.prism("sand", S.octagon(-0.05, 0.7, -0.15, 0.7, 0.16), t + 1.02, t + 1.12)
    # водопад через передний левый край
    for k, (y, z) in enumerate(((-1.06, 0.84), (-1.1, 0.68), (-1.12, 0.52), (-1.1, 0.38))):
        a.box("waterL" if k % 2 else "water", -0.74 - 0.01 * k, -0.42 + 0.01 * k, y - 0.06, y + 0.04, t + z - 0.14,
              t + z + 0.04, bevel=0)
    # шатёр: красная пирамида с белыми полосами
    tx, ty = 0.42, 0.42
    a.frustum("red", (tx - 0.24, tx + 0.24, ty - 0.24, ty + 0.24), (tx, tx, ty, ty), t + 1.1, t + 1.56)
    for s in (-1, 1):
        a.box("white", tx + s * 0.08 - 0.04, tx + s * 0.08 + 0.04, ty - 0.27, ty - 0.2, t + 1.12, t + 1.3, bevel=0)
    a.box("dark", tx - 0.06, tx + 0.06, ty - 0.265, ty - 0.22, t + 1.1, t + 1.26, bevel=0)
    # две пальмы — свои части (качаются)
    for name, (px, py), lean in (("PalmA", (0.05, 0.62), -12), ("PalmB", (0.72, 0.05), 14)):
        part(a, name, "Body", (px, py, t + 1.08))
        top = Vector((px + lean * 0.012, py, t + 2.05))
        stripe_chain(a, ("trunk", "trunkD"), [(px, py, t + 1.06), (px + lean * 0.004, py, t + 1.42),
                                              (px + lean * 0.009, py, t + 1.76), tuple(top)], 0.12, 0.12)
        for k in range(5):
            ang = math.radians(k * 72 + 15)
            m = Matrix.Translation(top) @ Matrix.Rotation(ang, 4, "Z") @ Matrix.Rotation(math.radians(22), 4, "Y")
            a.prism("leaf" if k % 2 else "leafD", [(0.0, -0.05), (0.42, -0.12), (0.62, 0.0), (0.42, 0.12), (0.0, 0.05)],
                    -0.025, 0.025, matrix=m)
        a.box("trunkD", top.x - 0.07, top.x + 0.07, top.y - 0.07, top.y + 0.07, top.z - 0.1, top.z + 0.02, bevel=0)
    # лодочка на озере
    part(a, "Boat", "Body", (-0.55, 0.3, t + 0.93))
    a.frustum("wood", (-0.68, -0.42, 0.24, 0.36), (-0.74, -0.36, 0.2, 0.4), t + 0.9, t + 1.0)
    a.box("trunkD", -0.565, -0.545, 0.29, 0.31, t + 0.98, t + 1.3, bevel=0)
    a.prism("white", [(-0.55, t + 1.04), (-0.55, t + 1.28), (-0.38, t + 1.06)], 0.28, 0.32, axis="y", bevel=0)
    # голова: старая, седые брови, бородка, сонные глаза, добрая улыбка
    part(a, "Head", "Body", (0, -0.86, t + 0.62))
    a.box("skin", -0.22, 0.22, -1.12, -0.82, t + 0.48, t + 0.76)
    hz = t + 0.92
    a.prism("skin", S.octagon(-0.36, 0.36, hz - 0.28, hz + 0.26, 0.12), -1.5, -1.06, axis="y")
    for s in (-1, 1):
        round_eye(a, (s * 0.16, -1.5, hz + 0.06), 0.11, look=(0, -0.2), pupil=0.6, lid=0.55, lid_key="skinD")
        a.box("brow", s * 0.04, s * 0.38, -1.64, -1.5, hz + 0.21, hz + 0.31, matrix=tilt((s * 0.2, -1.56, hz + 0.26), "Y", s * 12))
        a.box("cheek", s * 0.23, s * 0.32, -1.53, -1.49, hz - 0.12, hz - 0.05, bevel=0)
    bar(a, "mouth", (-0.14, -1.52, hz - 0.13), (0.0, -1.52, hz - 0.17), 0.04, 0.035, bevel=0)
    bar(a, "mouth", (0.0, -1.525, hz - 0.17), (0.14, -1.525, hz - 0.13), 0.04, 0.035, bevel=0)
    a.frustum("brow", (-0.12, 0.12, -1.52, -1.32), (-0.03, 0.03, -1.46, -1.38), hz - 0.26, hz - 0.5)
    part(a, "Tail", "Body", (0, 1.06, t + 0.44))
    a.frustum("skin", (-0.12, 0.12, 1.0, 1.14), (-0.03, 0.03, 1.3, 1.34), t + 0.34, t + 0.46)
    a.face = (0, -1.5, hz)
    a.closeup = ((-1.9, -1.8, t + 1.4), (-0.6, -0.4, t + 0.7))
    a.pose = {"Head": ((-10, 0, 8), (0, 0, -0.04)), "PalmA": ((0, 10, 0), (0, 0, 0)), "PalmB": ((0, -8, 0), (0, 0, 0)),
              "Boat": ((0, 0, 40), (0.1, -0.05, 0)), "LegFL": ((-15, 0, 0), (0, 0, 0)), "Tail": ((0, 0, 20), (0, 0, 0))}
    return a


# ── 24. Жар-страус: высокий страус-артист чеканит шаг; позади раскрыт огненный хвост — два яруса объёмных языков
#        пламени чашей вокруг тела (v2, правка владельца 2026-11-13; в v1 — плоский веер лучей); тёмно-фиолетовое
#        тело, золотые ноги, длинные ресницы, клюв ─────────────────────────────────────────────────────────────────────


def blaze_ostrich():
    a = S.Art("Art_BlazeOstrich", ring_z0=1.6)
    d39v2(a)
    a.paint("plum", "4A2F86", rings=True)
    for key, code in (("plumL", "6E4FB0"), ("legG", "F2C230"), ("legD", "C9921A"), ("beak", "FF9A2E"),
                      ("r1", "FFE14A"), ("r2", "FFC83A"), ("r3", "FFA632"), ("r4", "FF842C"), ("r5", "FF5E2C"),
                      ("r6", "F23F2C"), ("r7", "D92B3A"), ("white", "FFFDF4"), ("dark", "231816"), ("glint", "FFFFFF"),
                      ("cheek", "FF8FB0"), ("core", "FFF4B8")):
        a.paint(key, code)
    t = epic_stand(a, 1.6)
    for s, name, lift in ((-1, "LegL", 0.0), (1, "LegR", 0.32)):
        part(a, name, "Body", (s * 0.22, 0.05, t + 1.42))
        knee = (s * 0.26, 0.28, t + 0.82 + lift * 0.6)
        foot = (s * 0.24, -0.06 - lift * 0.5, t + 0.12 + lift)
        bar(a, "legG", (s * 0.22, 0.05, t + 1.42), knee, 0.15, 0.14)
        bar(a, "legG", knee, foot, 0.13, 0.12)
        a.box("legD", knee[0] - 0.09, knee[0] + 0.09, knee[1] - 0.09, knee[1] + 0.09, knee[2] - 0.09, knee[2] + 0.09, bevel=0)
        a.box("legD", foot[0] - 0.1, foot[0] + 0.1, foot[1] - 0.32, foot[1] + 0.06, foot[2] - 0.12, foot[2] - 0.02)
    part(a, "Body", "Stand", (0, 0.05, t + 1.42))
    for h, z0, z1, y0, y1 in ((0.42, 1.3, 1.46, -0.38, 0.5), (0.52, 1.44, 1.86, -0.44, 0.62), (0.44, 1.84, 2.02, -0.36, 0.52)):
        a.prism("plum", S.octagon(-h, h, y0, y1, h * 0.3), t + z0, t + z1)
    a.box("plumL", -0.3, 0.3, -0.48, -0.42, t + 1.5, t + 1.84, bevel=0)
    for s, name in ((-1, "WingL"), (1, "WingR")):
        part(a, name, "Body", (s * 0.5, 0.05, t + 1.75))
        m = tilt((s * 0.5, 0.05, t + 1.75), "Y", -s * 25)
        a.box("plumL", s * 0.46, s * 0.62, -0.3, 0.42, t + 1.5, t + 1.86, matrix=m)
        a.box("legG", s * 0.47, s * 0.63, -0.32, 0.44, t + 1.47, t + 1.52, bevel=0, matrix=m)
    # хвост — объёмное пламя (правка владельца 2026-11-13: «огненный хвост объёмнее и выразительнее»; было — плоский
    # веер лучей толщиной 0.06, сбоку почти не виден). Два яруса языков огня: задний — семь длинных, от оранжевого в
    # центре к тёмно-красному по краям, передний (ближе к телу) — шесть коротких оранжево-жёлтых. У каждого языка
    # светлая сердцевина — выступает с обеих сторон; языки повёрнуты вокруг своей оси, а к краям загибаются вперёд
    # чашей — пламя читается толщей сбоку и сзади. Над кончиками искры, позади — золотое «солнце», откуда бьёт огонь
    part(a, "Fan", "Body", (0, 0.58, t + 1.7))
    hub = Vector((0, 0.66, t + 1.66))

    def flame(w, ln, flip):
        """Язык огня в плоскости x–z от основания z = 0 к кончику z = ln: боковой язычок и чуть смещённый кончик."""
        pts = [(-0.7 * w, 0.0), (0.7 * w, 0.0), (w, 0.3 * ln), (0.75 * w, 0.55 * ln), (1.05 * w, 0.74 * ln),
               (0.45 * w, 0.66 * ln), (0.15 * w, ln), (-0.55 * w, 0.62 * ln), (-w, 0.32 * ln)]
        return [(-x, z) for x, z in reversed(pts)] if flip else pts

    # ярусы: сдвиг по y, углы веера, длины и цвета по удалению от центра, полуширина, толщина, наклон (основа и шаг к
    # краю: «+» — вперёд, к телу, чашей; «−» — назад). Третий, самый дальний ярус отклонён назад — сбоку хвост — куст огня
    layers = ((0.0, [-78 + 26 * i for i in range(7)], (1.36, 1.3, 1.22, 1.12), 0.2, 0.14,
               ("r4", "r5", "r6", "r7"), ("r1", "r2", "r3", "r3"), 0, 4),
              (-0.15, [-65 + 26 * i for i in range(6)], (0.9, 0.86, 0.8), 0.15, 0.1,
               ("r2", "r3", "r3"), ("core", "r1", "r1"), 4, 5),
              (0.14, [-56 + 28 * i for i in range(5)], (1.02, 0.96, 0.88), 0.17, 0.12,
               ("r6", "r6", "r7"), ("r4", "r4", "r5"), -30, -4))
    for li, (dy, angs, lens, w, th, keys, cores, lean0, lean_k) in enumerate(layers):
        for i, deg in enumerate(angs):
            dist = int(abs(deg) // 26)
            ln = lens[dist]
            lean = lean0 + lean_k * dist
            m = (Matrix.Translation(hub + Vector((0, dy, 0))) @ Matrix.Rotation(math.radians(deg), 4, "Y")
                 @ Matrix.Rotation(math.radians(-14 + lean), 4, "X")
                 @ Matrix.Rotation(math.radians(14 if (i + li) % 2 else -14), 4, "Z") @ Matrix.Translation((0, 0, 0.1)))
            shape = flame(w, ln, (i + li) % 2 == 1)
            a.extrude(keys[dist], shape, -th / 2, th / 2, axis="y", matrix=m)
            a.extrude(cores[dist], [(0.55 * x, 0.12 * ln + 0.6 * z) for x, z in shape], -th / 2 - 0.02, th / 2 + 0.02,
                      axis="y", matrix=m)
    for deg, r, key, h in ((-50, 1.42, "r2", 0.06), (-10, 1.6, "r1", 0.065), (28, 1.48, "r3", 0.055),
                           (62, 1.26, "r2", 0.05), (10, 1.78, "r4", 0.045)):  # искры
        m = (Matrix.Translation(hub) @ Matrix.Rotation(math.radians(deg), 4, "Y") @ Matrix.Rotation(math.radians(-14), 4, "X")
             @ Matrix.Translation((0, 0, r)) @ Matrix.Rotation(math.radians(45), 4, "Y"))
        a.box(key, -h, h, -h, h, -h, h, bevel=0, matrix=m)
    a.prism("legG", ngon(0, 0, 0.18, 8), 0.24, 0.32, axis="y", matrix=Matrix.Translation(hub))
    # шея и голова
    part(a, "Neck", "Body", (0, -0.28, t + 1.98))
    stripe_chain(a, ("plum", "plumL"), [(0, -0.28, t + 1.96), (0, -0.36, t + 2.3), (0, -0.4, t + 2.64), (0, -0.38, t + 2.92)],
                 0.18, 0.18)
    part(a, "Head", "Neck", (0, -0.38, t + 2.92))
    hz = t + 3.06
    a.prism("plum", S.octagon(-0.2, 0.2, -0.6, -0.18, 0.08), hz - 0.16, hz + 0.18)
    a.frustum("beak", (-0.13, 0.13, hz - 0.12, hz + 0.02), (-0.06, 0.06, hz - 0.09, hz - 0.03), -0.6, -0.86, axis="y")
    for s in (-1, 1):
        round_eye(a, (s * 0.1, -0.6, hz + 0.08), 0.07, look=(0, 0.1), pupil=0.62, depth=0.03)
        bar(a, "dark", (s * 0.15, -0.64, hz + 0.15), (s * 0.21, -0.64, hz + 0.2), 0.022, 0.02, bevel=0)
        bar(a, "dark", (s * 0.17, -0.645, hz + 0.11), (s * 0.23, -0.645, hz + 0.14), 0.022, 0.02, bevel=0)
    a.box("cheek", 0.13, 0.19, -0.62, -0.595, hz - 0.06, hz, bevel=0)
    a.box("cheek", -0.19, -0.13, -0.62, -0.595, hz - 0.06, hz, bevel=0)
    for k, dx in enumerate((-0.06, 0.04)):
        a.box("r3" if k else "r5", dx - 0.035, dx + 0.035, -0.42 - 0.06 * k, -0.34 - 0.06 * k, hz + 0.16, hz + 0.34 - 0.06 * k)
    a.face = (0, -0.6, hz)
    a.closeup = ((1.6, -1.8, t + 2.2), (0.3, 0.6, t + 2.0))
    a.pose = {"Fan": ((0, 0, 0), (0, 0, 0)), "LegR": ((-30, 0, 0), (0, 0, 0)), "LegL": ((15, 0, 0), (0, 0, 0)),
              "Neck": ((-10, 0, 0), (0, 0, 0)), "WingL": ((0, 20, 0), (0, 0, 0)), "WingR": ((0, -20, 0), (0, 0, 0))}
    return a


# ── 25. Верблюд-туча: единственный мокрый в пустыне — взрослый верблюд в жёлтой зюйдвестке и четырёх красных
#        резиновых сапогах, над ним его собственная сине-фиолетовая туча с мордой, из тучи по кругу идёт дождь, под
#        ногами лужа; верблюд смирился — грустные мокрые глаза, капли на носу. Капли крупные ─────────────────────────


def cloud_camel():
    a = S.Art("Art_CloudCamel", ring_z0=1.6)
    d39v2(a)
    a.paint("fur", "E3A456", rings=True)
    a.paint("cloud", "7A86D8", rings=True)
    for key, code in (("furD", "B9823F"), ("cream", "FBE3BC"), ("hat", "FFD23F"), ("hatD", "E6B21E"),
                      ("boot", "E53935"), ("bootD", "B3261E"), ("cloudL", "A6B0F0"), ("cloudD", "5A64B8"),
                      ("rain", "5FC8FF"), ("puddle", "4FA8E8"), ("puddleL", "A6DAFA"), ("white", "FFFDF4"),
                      ("dark", "231816"), ("glint", "FFFFFF"), ("tuft", "8A5A2E")):
        a.paint(key, code)
    t = epic_stand(a, 1.7)
    part(a, "Puddle", "Stand", (0, 0, t))
    a.prism("puddle", S.octagon(-1.25, 1.2, -0.8, 0.9, 0.3), t, t + 0.03, bevel=0)
    a.frame("puddleL", ngon(-0.6, -0.4, 0.26, 10), 0.04, t + 0.02, t + 0.05, axis="z", bevel=0)
    a.frame("puddleL", ngon(0.7, 0.4, 0.2, 10), 0.04, t + 0.025, t + 0.055, axis="z", bevel=0)
    zb = t + 1.0
    part(a, "Body", "Stand", (0, 0, zb))
    a.prism("fur", S.octagon(zb - 0.04, zb + 0.6, -0.38, 0.38, 0.16), -0.82, 0.8, axis="x")
    a.prism("fur", S.octagon(zb + 0.56, zb + 0.98, -0.3, 0.3, 0.14), -0.4, 0.42, axis="x")
    a.prism("fur", S.octagon(zb + 0.96, zb + 1.12, -0.18, 0.18, 0.05), -0.2, 0.22, axis="x")
    bar(a, "fur", (-0.74, 0, zb + 0.4), (-0.98, -0.06, zb + 1.02), 0.3, 0.28)
    for x, y, name in ((-0.56, -0.22, "LegFL"), (-0.56, 0.22, "LegFR"), (0.54, -0.22, "LegBL"), (0.54, 0.22, "LegBR")):
        part(a, name, "Body", (x, y, zb))
        a.box("fur", x - 0.1, x + 0.1, y - 0.1, y + 0.1, t + 0.6, zb + 0.06)
        a.box("furD", x - 0.12, x + 0.12, y - 0.12, y + 0.12, t + 0.5, t + 0.64)
        a.box("boot", x - 0.13, x + 0.13, y - 0.13, y + 0.13, t + 0.1, t + 0.52)
        a.box("bootD", x - 0.15, x + 0.15, y - 0.2, y + 0.14, t + 0.02, t + 0.12)
    part(a, "Tail", "Body", (0.78, 0, zb + 0.44))
    bar(a, "fur", (0.78, 0, zb + 0.44), (0.92, 0.02, zb + 0.1), 0.08, 0.08)
    a.box("tuft", 0.84, 1.02, -0.08, 0.12, zb - 0.12, zb + 0.12)
    # голова: грустные мокрые глаза, капли на носу, жёлтая зюйдвестка
    head = Vector((-1.04, -0.12, zb + 1.2))
    m_head = Matrix.Translation(head) @ Matrix.Rotation(math.radians(40), 4, "Z") @ Matrix.Rotation(math.radians(-6), 4, "Y")
    part(a, "Head", "Body", (-0.98, -0.06, zb + 1.02))
    with_matrix(a, m_head)
    a.prism("fur", S.octagon(-0.22, 0.32, -0.25, 0.25, 0.07), -0.28, 0.24, axis="x")
    a.prism("cream", S.octagon(-0.26, 0.06, -0.18, 0.18, 0.06), -0.68, -0.22, axis="x")
    a.box("furD", -0.72, -0.44, -0.19, 0.19, -0.28, -0.16)
    a.box("rain", -0.73, -0.68, -0.03, 0.03, -0.1, -0.02, bevel=0)
    a.prism("hat", S.octagon(-0.46, 0.4, -0.42, 0.42, 0.12), 0.3, 0.36)
    a.prism("hat", S.octagon(-0.26, 0.24, -0.28, 0.28, 0.08), 0.34, 0.58)
    a.prism("hatD", S.octagon(-0.27, 0.25, -0.29, 0.29, 0.08), 0.36, 0.42, bevel=0)
    with_matrix(a, m_head @ Matrix.Rotation(math.radians(-90), 4, "Z"))
    for s in (-1, 1):
        eye(a, (s * 0.12, -0.28, 0.17 + 0.006 * (s > 0)), 0.15, 0.15, look=(0, -0.5), depth=0.05, lid=0.38, lid_key="furD")
        a.box("rain", s * 0.12 - 0.03, s * 0.12 + 0.03, -0.35, -0.33, 0.02, 0.08, bevel=0)
    with_matrix(a, None)
    # туча с мордой над верблюдом и дождь по кругу
    part(a, "Cloud", "Body", (0, 0, zb + 1.9))
    cz = zb + 2.1
    for x, y, z, r in ((-0.2, 0.0, 0.0, 0.42), (0.36, 0.05, 0.05, 0.36), (-0.62, 0.02, -0.05, 0.3), (0.05, 0.0, 0.26, 0.32),
                       (0.62, 0.0, -0.08, 0.24)):
        a.prism("cloud" if r > 0.3 else "cloudL", S.octagon(x - r, x + r, y - r * 0.8, y + r * 0.8, r * 0.3), cz + z - r * 0.55,
                cz + z + r * 0.55)
    a.prism("cloudD", S.octagon(-0.78, 0.78, -0.3, 0.3, 0.12), cz - 0.36, cz - 0.24)
    for s in (-1, 1):
        closed_eye(a, (-0.2 + s * 0.14, -0.34, cz + 0.06), 0.12, key="cloudD", happy=False)
    bar(a, "cloudD", (-0.3, -0.35, cz - 0.08), (-0.2, -0.35, cz - 0.04), 0.04, 0.035, bevel=0)
    bar(a, "cloudD", (-0.2, -0.355, cz - 0.04), (-0.1, -0.355, cz - 0.08), 0.04, 0.035, bevel=0)
    part(a, "Rain", "Cloud", (0, 0, cz - 0.4))
    for k in range(10):
        ang = math.radians(k * 36 + 10)
        r = 0.55 + 0.15 * (k % 2)
        x, y = r * math.cos(ang) * 1.3, r * math.sin(ang) * 0.6
        z = cz - 0.55 - 0.32 * (k % 3)
        a.box("rain", x - 0.04, x + 0.04, y - 0.04, y + 0.04, z - 0.12, z + 0.02, bevel=0)
        a.box("rain", x - 0.025, x + 0.025, y - 0.025, y + 0.025, z + 0.02, z + 0.07, bevel=0)
    a.face = tuple(m_head @ Vector((-0.4, 0, 0.05)))
    a.closeup = ((0.6, -2.4, cz), (0.0, -0.3, cz - 0.1))
    a.pose = {"Cloud": ((0, 0, 0), (0.1, 0, 0.1)), "Rain": ((0, 0, 0), (0, 0, -0.15)), "Head": ((0, 0, -12), (0, 0, 0)),
              "LegFL": ((0, -14, 0), (0, 0, 0)), "Tail": ((0, 25, 0), (0, 0, 0))}
    return a


# ── 26. Кристальный скорпион: гордый страж — янтарный бронированный скорпион, клешни высоко подняты, хвост дугой
#        несёт огромный гранёный бирюзовый камень (без жала), на спине гроздь бирюзовых кристаллов; морда гордая.
#        Блики на гранях вместо прозрачности. Не №11 (тот — пухлый оранжевый садовник) ─────────────────────────────────


def crystal_scorpion():
    a = S.Art("Art_CrystalScorpion", ring_z0=0.8)
    d39v2(a)
    a.paint("amber", "F2B33A", rings=True)
    for key, code in (("amberD", "C8862A"), ("amberL", "FFD77A"), ("gemA", "2ED1C0"), ("gemB", "8FF2E6"),
                      ("gemC", "1FA396"), ("white", "FFFDF4"), ("dark", "231816"), ("glint", "FFFFFF"),
                      ("mouth", "5A1A20"), ("brow", "8A5A1A")):
        a.paint(key, code)
    t = epic_stand(a, 1.66)
    part(a, "Body", "Stand", (0, 0.15, t + 0.35))
    a.prism("amberD", S.octagon(-0.5, 0.5, -0.4, 0.66, 0.16), t + 0.22, t + 0.36)
    for k, (h, z0, z1) in enumerate(((0.58, 0.34, 0.62), (0.5, 0.6, 0.76))):
        a.prism("amber", S.octagon(-h, h, -0.48 + 0.04 * k, 0.72 - 0.04 * k, h * 0.3), t + z0, t + z1)
    for y in (0.0, 0.24, 0.48):
        a.box("amberD", -0.49, 0.49, y, y + 0.05, t + 0.74, t + 0.79, bevel=0)
    # гроздь кристаллов на спине
    for x, y, h, r, key in ((0.0, 0.3, 0.62, 0.13, "gemA"), (-0.22, 0.2, 0.42, 0.1, "gemB"), (0.22, 0.42, 0.46, 0.1, "gemC"),
                            (0.12, 0.12, 0.32, 0.08, "gemB"), (-0.14, 0.48, 0.36, 0.08, "gemA")):
        lean = tilt((x, y, t + 0.76), "Y", x * 60) @ tilt((x, y, t + 0.76), "X", (y - 0.3) * -60)
        a.prism(key, ngon(x, y, r, 6), t + 0.74, t + 0.76 + h * 0.75, matrix=lean)
        a.frustum(key, (x - r * 0.86, x + r * 0.86, y - r * 0.86, y + r * 0.86), (x, x, y, y), t + 0.76 + h * 0.75 - 0.01,
                  t + 0.76 + h, matrix=lean)
    for s in (-1, 1):
        round_eye(a, (s * 0.2, -0.44, t + 0.52), 0.1, look=(0, 0.2), pupil=0.6, lid=0.3, lid_key="amberD")
        bar(a, "brow", (s * 0.34, -0.47, t + 0.66), (s * 0.08, -0.47, t + 0.6), 0.06, 0.04)
    a.box("mouth", -0.12, 0.12, -0.47, -0.43, t + 0.34, t + 0.37, bevel=0)
    bar(a, "mouth", (0.1, -0.455, t + 0.355), (0.18, -0.455, t + 0.4), 0.035, 0.03, bevel=0)
    for s, name in ((-1, "LegsL"), (1, "LegsR")):
        part(a, name, "Body", (s * 0.52, 0.15, t + 0.3))
        for y in (-0.16, 0.08, 0.32, 0.54):
            bar(a, "amberD", (s * 0.52, y, t + 0.3), (s * 0.8, y + 0.03, t + 0.22), 0.09, 0.09)
            bar(a, "amberD", (s * 0.8, y + 0.03, t + 0.22), (s * 0.9, y + 0.05, t), 0.08, 0.08)
    # клешни подняты высоко
    for s, name in ((-1, "ClawL"), (1, "ClawR")):
        part(a, name, "Body", (s * 0.42, -0.36, t + 0.48))
        el = (s * 0.78, -0.62, t + 0.9)
        bar(a, "amber", (s * 0.42, -0.36, t + 0.48), el, 0.17, 0.16)
        bar(a, "amber", el, (s * 0.84, -0.72, t + 1.32), 0.16, 0.15)
        c = Vector((s * 0.86, -0.76, t + 1.42))
        a.box("amber", c.x - 0.2, c.x + 0.2, c.y - 0.16, c.y + 0.16, c.z - 0.16, c.z + 0.16)
        fu = tilt((c.x - s * 0.06, c.y, c.z + 0.1), "Y", s * 18)
        a.box("amberL", c.x - s * 0.16 - 0.08, c.x - s * 0.16 + 0.08, c.y - 0.12, c.y + 0.12, c.z + 0.1, c.z + 0.56, matrix=fu)
        a.frustum("amberL", (c.x - s * 0.16 - 0.08, c.x - s * 0.16 + 0.08, c.y - 0.12, c.y + 0.12),
                  (c.x - s * 0.13, c.x - s * 0.13, c.y, c.y), c.z + 0.56, c.z + 0.7, bevel=0, matrix=fu)
        fl = tilt((c.x + s * 0.1, c.y, c.z + 0.1), "Y", -s * 22)
        a.box("amberD", c.x + s * 0.13 - 0.07, c.x + s * 0.13 + 0.07, c.y - 0.1, c.y + 0.1, c.z + 0.1, c.z + 0.42, matrix=fl)
    # хвост дугой, на конце — огромный гранёный камень
    part(a, "Tail", "Body", (0, 0.68, t + 0.6))
    stripe_chain(a, ("amber", "amberD"), [(0, 0.68, t + 0.6), (0, 1.0, t + 1.0), (0, 0.98, t + 1.5), (0, 0.7, t + 1.92),
                                          (0, 0.36, t + 2.06)], 0.26, 0.24)
    part(a, "Gem", "Tail", (0, 0.36, t + 2.06))
    g = Vector((0, 0.2, t + 2.22))
    a.prism("gemA", ngon(g.x, g.y, 0.3, 8), g.z - 0.1, g.z + 0.1, matrix=tilt(tuple(g), "X", 20))
    a.frustum("gemB", (g.x - 0.26, g.x + 0.26, g.y - 0.26, g.y + 0.26), (g.x - 0.1, g.x + 0.1, g.y - 0.1, g.y + 0.1), g.z + 0.09,
              g.z + 0.3, matrix=tilt(tuple(g), "X", 20))
    a.frustum("gemC", (g.x - 0.26, g.x + 0.26, g.y - 0.26, g.y + 0.26), (g.x, g.x, g.y, g.y), g.z - 0.09, g.z - 0.36,
              matrix=tilt(tuple(g), "X", 20))
    a.box("glint", g.x - 0.12, g.x - 0.04, g.y - 0.31, g.y - 0.27, g.z, g.z + 0.08, bevel=0, matrix=tilt(tuple(g), "X", 20))
    a.face = (0, -0.46, t + 0.5)
    a.closeup = ((1.9, -1.4, t + 1.4), (0.3, 0.2, t + 0.9))
    a.pose = {"ClawL": ((0, 0, 15), (0, 0, 0)), "ClawR": ((0, 0, -15), (0, 0, 0)), "Tail": ((-12, 0, 0), (0, 0, 0)),
              "Gem": ((0, 30, 0), (0, 0, 0)), "LegsL": ((10, 0, 0), (0, 0, 0))}
    return a


# ── 27. Кактус-великан: добрый сагуаро-дом с тремя руками на разной высоте (асимметрично), сонное лицо зевает, на
#        макушке венок бело-розовых цветов, в двух дуплах выглядывают совята. Ствол один, без двух круглых форм у
#        основания ────────────────────────────────────────────────────────────────────────────────────────────────


def giant_cactus():
    a = S.Art("Art_GiantCactus", ring_z0=1.6)
    d39v2(a)
    a.paint("green", "2E8B3A", rings=True)
    for key, code in (("rib", "1F6B2C"), ("spine", "FFF0C8"), ("hole", "3A2416"), ("owl", "B9844E"),
                      ("owlL", "F2D9B0"), ("beak", "FFB04A"), ("petal", "FFFDF4"), ("petalP", "FF9EC4"),
                      ("yellow", "FFD23F"), ("sand", "E8B460"), ("white", "FFFDF4"), ("dark", "231816"),
                      ("glint", "FFFFFF"), ("mouth", "3A1414"), ("tongue", "FF6F86")):
        a.paint(key, code)
    t = epic_stand(a, 1.6)
    a.prism("sand", S.octagon(-0.66, 0.66, -0.6, 0.66, 0.2), t, t + 0.12)
    part(a, "Trunk", "Stand", (0, 0, t + 0.1))
    a.prism("green", S.octagon(-0.44, 0.44, -0.4, 0.44, 0.14), t + 0.08, t + 3.1)
    a.prism("green", S.octagon(-0.36, 0.36, -0.32, 0.36, 0.12), t + 3.08, t + 3.3)
    for x, y in S.octagon(-0.44, 0.44, -0.4, 0.44, 0.14):
        ang = math.degrees(math.atan2(y - 0.02, x))
        a.box("rib", x - 0.035, x + 0.035, y - 0.035, y + 0.035, t + 0.2, t + 3.0, bevel=0, matrix=tilt((x, y, 0), "Z", ang))
    for x, y, z in ((-0.46, -0.1, 0.8), (0.46, 0.15, 1.2), (-0.46, 0.2, 2.2), (0.46, -0.1, 2.7), (0.2, -0.42, 0.6)):
        a.box("spine", x - 0.03, x + 0.03, y - 0.03, y + 0.03, t + z - 0.03, t + z + 0.03, bevel=0)
    # сонное лицо: веки полуопущены, рот «зевок», румянец
    fz = t + 2.5
    for s in (-1, 1):
        round_eye(a, (s * 0.16, -0.4, fz), 0.11, look=(0, -0.3), pupil=0.6, lid=0.6, lid_key="rib")
    a.prism("mouth", ngon(0, fz - 0.32, 0.12, 8), -0.44, -0.38, axis="y")
    a.box("tongue", -0.07, 0.07, -0.445, -0.42, fz - 0.42, fz - 0.34, bevel=0)
    # дупла с совятами
    for k, (x, z, name) in enumerate(((0.16, 1.2, "OwlA"), (-0.2, 1.85, "OwlB"))):
        a.prism("hole", ngon(x, t + z, 0.17, 8), -0.43, -0.38, axis="y")
        part(a, name, "Trunk", (x, -0.44, t + z))
        a.prism("owl", ngon(x, t + z - 0.02, 0.13, 8), -0.47, -0.41, axis="y")
        for s in (-1, 1):
            a.prism("owlL", ngon(x + s * 0.055, t + z + 0.02, 0.05, 8), -0.49, -0.46, axis="y", bevel=0)
            a.box("dark", x + s * 0.055 - 0.02, x + s * 0.055 + 0.02, -0.5, -0.485, t + z, t + z + 0.04, bevel=0)
        a.frustum("beak", (x - 0.03, x + 0.03, t + z - 0.07, t + z - 0.02), (x, x, t + z - 0.045, t + z - 0.045), -0.47,
                  -0.53, axis="y", bevel=0)
        for s in (-1, 1):
            a.box("owl", x + s * 0.07 - 0.025, x + s * 0.07 + 0.025, -0.45, -0.42, t + z + 0.1, t + z + 0.17, bevel=0)
    # три руки на разной высоте
    for name, s, z, out, up, w in (("ArmA", -1, 1.1, 0.5, 0.9, 0.24), ("ArmB", 1, 1.75, 0.52, 0.8, 0.22),
                                   ("ArmC", -1, 2.55, 0.38, 0.45, 0.17)):
        part(a, name, "Trunk", (s * 0.4, 0, t + z))
        elbow = (s * (0.4 + out), 0.02, t + z)
        stripe_chain(a, ("green", "green"), [(s * 0.38, 0.0, t + z), elbow, (s * (0.4 + out), 0.02, t + z + up)], w, w)
        a.prism("green", S.octagon(s * (0.4 + out) - w / 2 - 0.01, s * (0.4 + out) + w / 2 + 0.01, -w / 2 - 0.01,
                                   w / 2 + 0.01, w * 0.2), t + z + up - 0.02, t + z + up + 0.08)
    # венок цветов на макушке
    part(a, "Crown", "Trunk", (0, 0.02, t + 3.3))
    for k in range(4):
        ang = math.radians(k * 90 + 30)
        c = (0.28 * math.cos(ang), 0.02 + 0.28 * math.sin(ang), t + 3.32)
        petals(a, c, 5, 0.13, 0.1, ("petal", "petalP"), "yellow", 0.06, normal=(math.cos(ang) * 0.5, math.sin(ang) * 0.5, 1),
               lift=10, spin=k * 20, bevel=0)
    a.face = (0, -0.4, fz - 0.1)
    a.closeup = ((-1.6, -1.8, t + 1.6), (-0.3, -0.2, t + 1.3))
    a.pose = {"ArmA": ((0, 10, 0), (0, 0, 0)), "ArmB": ((0, -12, 0), (0, 0, 0)), "OwlA": ((0, 0, 0), (0, -0.08, 0)),
              "OwlB": ((0, 0, 20), (0, 0, 0)), "Crown": ((0, 0, 20), (0, 0, 0.05))}
    return a


EPIC = [("DuneWhale", dune_whale, "Кит-бархан", "Epic"),
        ("IslandTurtle", island_turtle, "Черепаха-остров", "Epic"),
        ("BlazeOstrich", blaze_ostrich, "Жар-страус", "Epic"),
        ("CloudCamel", cloud_camel, "Верблюд-туча", "Epic"),
        ("CrystalScorpion", crystal_scorpion, "Кристальный скорпион", "Epic"),
        ("GiantCactus", giant_cactus, "Кактус-великан", "Epic")]



# ══ LEGENDARY №28–30 (подставка — лазурит в золоте с бирюзовыми камнями, новая) ════════════════════════════

# ── 28. Антилопа-родник: дух оазиса — белая антилопа с прямыми золотыми рогами, грива и хвост — струи воды (бирюза и
#        лазурь), лазурная «маска» у глаз, золотые копытца; под копытами родник с лотосом. Ноги не тоньше 0.16; не
#        Suicune (нет ленты и кристального гребня) ──────────────────────────────────────────────────────────────────


def spring_antelope():
    a = S.Art("Art_SpringAntelope", ring_z0=1.6)
    d39v2(a)
    a.paint("coat", "F7F4EE", rings=True)
    for key, code in (("coatD", "E3DCCF"), ("azure", "3AA6E8"), ("azureD", "2A7FC0"), ("water", "2ED1C0"),
                      ("waterL", "A6F0EA"), ("pool", "35B6D6"), ("lotus", "FF9EC4"), ("lotusL", "FFE3EF"),
                      ("yellow", "FFD23F"), ("leaf", "3FAE46"), ("white", "FFFDF4"), ("dark", "231816"),
                      ("glint", "FFFFFF"), ("goldD", "C9921A"), ("nose", "C8B8A8")):
        a.paint(key, code)
    a.paint("cloth", "2B4FC2", rings=True)  # попона — лазурит, как подставка Legendary
    t = legendary_stand(a, 1.66)
    part(a, "Spring", "Stand", (0, 0, t))
    a.prism("pool", S.octagon(-1.0, 1.0, -0.86, 0.86, 0.3), t, t + 0.05, bevel=0)
    for r, dz in ((0.32, 0.0), (0.56, 0.006)):
        a.frame("waterL", ngon(-0.45, -0.32, r, 10), 0.04, t + 0.045 + dz, t + 0.07 + dz, axis="z", bevel=0)
    for k, (x, y, z) in enumerate(((-0.45, -0.32, 0.08), (-0.4, -0.28, 0.2), (-0.5, -0.36, 0.3))):
        r = 0.07 - 0.015 * k
        a.box("waterL" if k % 2 else "water", x - r, x + r, y - r, y + r, t + z - r, t + z + r, bevel=0)
    for cx, cy, r, z1 in ((-0.52, 0.18, 0.22, 0.08), (-0.72, -0.18, 0.17, 0.074)):  # круги на воде у копыт
        a.frame("waterL", ngon(cx, cy, r, 6), 0.035, t + 0.04, t + z1, axis="z", bevel=0)  # (под поднятым — от капель)
    lx, ly = 0.62, -0.52
    a.prism("leaf", ngon(lx, ly, 0.24, 8), t + 0.04, t + 0.08)
    petals(a, (lx, ly, t + 0.1), 6, 0.16, 0.1, ("lotus", "lotusL"), "yellow", 0.07, lift=35, bevel=0)
    zb = t + 1.06
    part(a, "Body", "Spring", (0, 0, zb))
    a.prism("coat", S.octagon(zb - 0.02, zb + 0.5, -0.3, 0.3, 0.13), -0.74, 0.7, axis="x")
    a.prism("coatD", S.octagon(zb - 0.06, zb + 0.1, -0.24, 0.24, 0.06), -0.6, 0.56, axis="x")
    # убранство Legendary (правка владельца 2026-11-13: «слегка усили оформление корпуса»; вместо волны на боку):
    # лазуритовая попона в цвет подставки, золотая кайма по низу и полоса по хребту, по бокам бирюзовые самоцветы в
    # золотой оправе-ромбе; на шее золотой ошейник с бирюзовой подвеской
    a.prism("cloth", [(zb + 0.16, -0.33), (zb + 0.395, -0.33), (zb + 0.545, -0.18), (zb + 0.545, 0.18), (zb + 0.395, 0.33),
                      (zb + 0.16, 0.33)], -0.3, 0.28, axis="x")  # свисает по бокам до каймы
    a.box("gold", -0.31, 0.29, -0.05, 0.05, zb + 0.53, zb + 0.565, bevel=0)
    for s in (-1, 1):
        a.box("gold", -0.31, 0.29, s * 0.325, s * 0.35, zb + 0.14, zb + 0.19, bevel=0)
        a.box("gold", -0.09, 0.09, s * 0.32, s * 0.352, zb + 0.25, zb + 0.43, bevel=0, matrix=tilt((0, 0, zb + 0.34), "Y", 45))
        gem(a, "water", (0, s * 0.37, zb + 0.34), 0.11)
    n0, n1 = Vector((-0.64, 0, zb + 0.36)), Vector((-0.9, -0.08, zb + 0.98))
    bar(a, "coat", tuple(n0), tuple(n1), 0.25, 0.24)
    bar(a, "gold", tuple(n0.lerp(n1, 0.13)), tuple(n0.lerp(n1, 0.25)), 0.31, 0.3)
    gem(a, "water", tuple(n0.lerp(n1, 0.17) + Vector((-0.19, -0.03, -0.07))), 0.1)
    for x, y, name, lift in ((-0.52, -0.18, "LegFL", 0.28), (-0.52, 0.18, "LegFR", 0.0), (0.52, -0.18, "LegBL", 0.0),
                             (0.52, 0.18, "LegBR", 0.0)):
        part(a, name, "Body", (x, y, zb))
        kx = x - 0.12 if lift else x
        bar(a, "coat", (x, y, zb + 0.05), (kx, y, t + 0.58 + lift * 0.5), 0.17, 0.17)
        bar(a, "coat", (kx, y, t + 0.58 + lift * 0.5), (x - (0.2 if lift else 0.0), y, t + 0.12 + lift), 0.16, 0.16)
        fx = x - (0.2 if lift else 0.0)
        a.box("azure", fx - 0.095, fx + 0.095, y - 0.095, y + 0.095, t + 0.14 + lift, t + 0.22 + lift, bevel=0)
        a.box("gold", fx - 0.1, fx + 0.1, y - 0.11, y + 0.1, t + 0.02 + lift, t + 0.14 + lift)
        if lift:  # с поднятого копыта капает вода
            for k, (dx, dz, r) in enumerate(((0.0, -0.05, 0.045), (0.03, -0.17, 0.035))):
                a.box("water" if k else "waterL", fx + dx - r, fx + dx + r, y - r, y + r, t + lift + dz - r,
                      t + lift + dz + r, bevel=0)
        else:  # всплеск-корона из воды вокруг копыта: языки наклонены наружу
            for k in range(4):
                ang = math.radians(45 + 90 * k + (20 if y > 0 else -10))
                m = (Matrix.Translation((fx + 0.17 * math.cos(ang), y + 0.17 * math.sin(ang), t + 0.1))
                     @ Matrix.Rotation(ang, 4, "Z") @ Matrix.Rotation(math.radians(32), 4, "Y"))
                a.box("waterL" if k % 2 else "water", -0.05, 0.05, -0.065, 0.065, -0.08, 0.17 + 0.06 * (k % 2), bevel=0,
                      matrix=m)
    # голова: благородная, повёрнута к игроку, лазурная маска у глаз, прямые золотые рога
    head = Vector((-0.96, -0.12, zb + 1.16))
    m_head = Matrix.Translation(head) @ Matrix.Rotation(math.radians(36), 4, "Z") @ Matrix.Rotation(math.radians(-8), 4, "Y")
    part(a, "Head", "Body", (-0.9, -0.08, zb + 0.98))
    with_matrix(a, m_head)
    a.prism("coat", S.octagon(-0.2, 0.24, -0.22, 0.22, 0.07), -0.24, 0.22, axis="x")
    a.prism("coat", S.octagon(-0.2, 0.06, -0.15, 0.15, 0.05), -0.64, -0.2, axis="x")
    a.box("nose", -0.68, -0.6, -0.08, 0.08, -0.06, 0.04)
    for s in (-1, 1):
        a.box("azure", -0.56, -0.22, s * 0.15, s * 0.168, -0.05, 0.03, bevel=0, matrix=tilt((-0.4, 0, 0), "Y", -10))
    for s in (-1, 1):
        hb = Vector((0.04, s * 0.1, 0.22))
        tip = Vector((0.5, s * 0.2, 1.12))
        stripe_chain(a, ("gold", "goldD"), [tuple(hb), tuple(hb.lerp(tip, 0.5)), tuple(tip)], 0.075, 0.075)
        a.box("coat", 0.0, 0.16, s * 0.2, s * 0.36, 0.12, 0.2, matrix=tilt((0.08, s * 0.22, 0.16), "X", -s * 30))
    with_matrix(a, m_head @ Matrix.Rotation(math.radians(-90), 4, "Z"))
    for s in (-1, 1):
        eye(a, (s * 0.11, -0.24, 0.08 + 0.006 * (s > 0)), 0.13, 0.12, look=(0, -0.2), depth=0.04, lid=0.4, lid_key="coatD")
        bar(a, "dark", (s * 0.16, -0.33, 0.13), (s * 0.21, -0.33, 0.17), 0.02, 0.02, bevel=0)
    with_matrix(a, None)
    # грива — струи воды каскадом от темени по шее; хвост — струя в родник
    part(a, "Mane", "Body", (-0.86, 0.06, zb + 1.1))
    mane = [(-0.92, 0.06, zb + 1.22), (-0.86, 0.12, zb + 1.0), (-0.74, 0.14, zb + 0.8), (-0.6, 0.12, zb + 0.6),
            (-0.44, 0.14, zb + 0.5)]
    stripe_chain(a, ("water", "waterL", "pool"), mane, 0.24, 0.16)
    for x, y, z, r in ((-1.0, 0.22, 0.94, 0.07), (-0.86, 0.3, 0.7, 0.08), (-0.7, 0.3, 0.48, 0.07), (-0.5, 0.26, 0.4, 0.06)):
        a.box("waterL" if r < 0.07 else "water", x - r, x + r, y - r, y + r, zb + z - r, zb + z + r, bevel=0)
    part(a, "Tail", "Body", (0.7, 0, zb + 0.4))
    stripe_chain(a, ("water", "waterL"), [(0.7, 0.0, zb + 0.4), (0.88, 0.02, zb + 0.24), (0.96, 0.04, zb - 0.1),
                                          (0.98, 0.06, t + 0.3)], 0.13, 0.11)
    for x, y in ((0.86, 0.14), (1.08, -0.02), (0.94, -0.12)):
        a.box("waterL", x - 0.045, x + 0.045, y - 0.045, y + 0.045, t + 0.1, t + 0.19, bevel=0)
    a.face = tuple(m_head @ Vector((-0.36, 0, 0.04)))
    a.closeup = ((0.4, -2.6, zb + 0.4), (0.1, -0.3, zb + 0.25))
    a.pose = {"Head": ((0, 14, 0), (0, 0, -0.06)), "LegFL": ((0, -20, 0), (0, 0, 0.04)), "Mane": ((0, 0, 0), (0.02, 0, -0.02)),
              "Tail": ((0, -15, 0), (0, 0, 0))}
    return a


# ── 29. Феникс-головоломка: птица из крупных деталей пазла (красные, оранжевые, жёлтые, бирюзовые, лазурные — с
#        выступами-«ушками» и тёмными швами), крылья раскрыты вверх, хвост из трёх длинных деталей; рядом парит
#        золотая деталь с «?» — птица собирает сама себя. Без пламени; не Ho-Oh ────────────────────────────────────


def puzzle_tile(a, key, x0, x1, z0, z1, y0, y1, tabs=(), seam="seam", matrix=None):
    """Деталь пазла в плоскости x–z: плитка, «ушки» (стороны 'l','r','t','b') и тёмная кромка-шов сзади."""
    a.box(key, x0, x1, y0, y1, z0, z1, matrix=matrix)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    r = min(x1 - x0, z1 - z0) * 0.16
    for side in tabs:
        if side == "l":
            c = (x0 - r * 0.7, cz)
        elif side == "r":
            c = (x1 + r * 0.7, cz)
        elif side == "t":
            c = (cx, z1 + r * 0.7)
        else:
            c = (cx, z0 - r * 0.7)
        a.prism(key, ngon(c[0], c[1], r, 8), y0 + 0.01, y1 - 0.01, axis="y", bevel=S.BEVEL if r > 0.05 else 0,
                matrix=matrix)
    a.box(seam, x0 - 0.01, x1 + 0.01, y1 - 0.005, y1 + 0.02, z0 - 0.01, z1 + 0.01, bevel=0, matrix=matrix)


QMARK = [".##.",
         "#..#",
         "..#.",
         "....",
         "..#."]


def puzzle_phoenix():
    a = S.Art("Art_PuzzlePhoenix", ring_z0=1.6)
    d39v2(a)
    for key, code in (("red", "E53935"), ("orange", "FF8A2E"), ("yellow", "FFD23F"), ("teal", "2ED1C0"), ("azure", "3AA6E8")):
        a.paint(key, code, rings=True)
    for key, code in (("seam", "3A2A40"), ("beak", "FFB04A"), ("legG", "F2C230"), ("legD", "C9921A"), ("white", "FFFDF4"),
                      ("dark", "231816"), ("glint", "FFFFFF"), ("goldP", "F2C230"), ("qmark", "6A3A10")):
        a.paint(key, code)
    t = legendary_stand(a, 1.66)
    for s, name in ((-1, "LegL"), (1, "LegR")):
        part(a, name, "Body", (s * 0.2, 0, t + 0.62))
        bar(a, "legG", (s * 0.2, 0, t + 0.64), (s * 0.24, -0.04, t + 0.12), 0.12, 0.12)
        for dx, dy in ((-0.1, -0.24), (0.06, -0.26), (0.0, 0.14)):
            a.box("legD", s * 0.24 + dx - 0.04, s * 0.24 + dx + 0.04, min(-0.04, -0.04 + dy), max(-0.04, -0.04 + dy), t,
                  t + 0.08, bevel=0)
    # туловище: две большие детали (грудь спереди, спина сзади) и верхняя
    part(a, "Body", "Stand", (0, 0, t + 0.64))
    puzzle_tile(a, "red", -0.42, 0.42, t + 0.6, t + 1.32, -0.36, 0.0, tabs=("t",))
    a.box("seam", -0.42, 0.42, -0.375, -0.355, t + 0.95, t + 0.97, bevel=0)
    a.prism("red", ngon(0.0, t + 0.94, 0.07, 8), -0.39, -0.35, axis="y", bevel=0)
    puzzle_tile(a, "orange", -0.38, 0.38, t + 0.62, t + 1.28, 0.0, 0.34, tabs=("b",))
    puzzle_tile(a, "yellow", -0.32, 0.32, t + 1.3, t + 1.62, -0.3, 0.26, tabs=("l", "r"))
    # голова: жёлтая деталь, клюв, решительный глаз, гребень из трёх маленьких деталей
    part(a, "Head", "Body", (0, -0.04, t + 1.62))
    hz = t + 1.9
    a.box("orange", -0.27, 0.27, -0.36, 0.2, hz - 0.26, hz + 0.24)
    a.box("seam", -0.28, 0.28, 0.2, 0.22, hz - 0.27, hz + 0.25, bevel=0)
    a.frustum("legG", (-0.12, 0.12, hz - 0.12, hz + 0.04), (-0.03, 0.03, hz - 0.1, hz - 0.06), -0.36, -0.66, axis="y")
    for s in (-1, 1):
        round_eye(a, (s * 0.13, -0.36, hz + 0.1), 0.08, look=(0.1 * s, 0.1), pupil=0.62, depth=0.03)
        bar(a, "seam", (s * 0.22, -0.39, hz + 0.24), (s * 0.06, -0.39, hz + 0.2), 0.05, 0.04)
    for k, (dx, h, key) in enumerate(((-0.17, 0.36, "red"), (0.0, 0.54, "yellow"), (0.17, 0.32, "red"))):
        puzzle_tile(a, key, dx - 0.085, dx + 0.085, hz + 0.24, hz + 0.24 + h, -0.12 + 0.01 * k, 0.04 + 0.01 * k)
    # крылья: по три детали ступенчатым веером вверх-наружу
    for s, name in ((-1, "WingL"), (1, "WingR")):
        part(a, name, "Body", (s * 0.42, 0.0, t + 1.2))
        for k, (key, ang, ln, w) in enumerate((("teal", 28, 0.98, 0.38), ("azure", 50, 1.18, 0.34), ("teal", 72, 1.04, 0.3))):
            m = Matrix.Translation((s * 0.42, 0.04 + 0.02 * k, t + 1.18)) @ Matrix.Rotation(math.radians(s * (90 - ang)), 4, "Y")
            puzzle_tile(a, key if s < 0 else ("azure" if key == "teal" else "teal"), -w / 2, w / 2, 0.0, ln, -0.07 - 0.005 * k,
                        0.07 + 0.005 * k, tabs=("t",) if k == 1 else (), matrix=m)
    # хвост: три длинные детали веером вниз-назад
    part(a, "Tail", "Body", (0, 0.32, t + 0.8))
    for k, (key, ang) in enumerate((("orange", -34), ("red", 0), ("yellow", 34))):
        m = Matrix.Translation((0, 0.36, t + 0.86)) @ Matrix.Rotation(math.radians(ang), 4, "Y") @ Matrix.Rotation(math.radians(58), 4, "X")
        puzzle_tile(a, key, -0.13, 0.13, -1.2, 0.0, -0.06 - 0.004 * k, 0.06 + 0.004 * k, tabs=("b",), matrix=m)
    # парящая золотая деталь с «?»
    part(a, "Piece", "Stand", (1.0, -0.3, t + 1.7))
    mp = tilt((1.0, -0.3, t + 1.7), "Y", -18)
    puzzle_tile(a, "goldP", 0.78, 1.22, t + 1.48, t + 1.92, -0.36, -0.24, tabs=("l", "t"), matrix=mp)
    for r_, row in enumerate(QMARK):
        for c_, ch in enumerate(row):
            if ch == "#":
                x = 0.9 + c_ * 0.05
                z = t + 1.84 - r_ * 0.065
                d_ = 0.004 * ((r_ + c_) % 2)
                a.box("qmark", x, x + 0.05, -0.385 - d_, -0.355, z - 0.065, z, bevel=0, matrix=mp)
    a.face = (0, -0.36, hz)
    a.closeup = ((-1.7, -1.9, t + 1.4), (-0.2, -0.2, t + 1.0))
    a.pose = {"WingL": ((0, 20, 0), (0, 0, 0)), "WingR": ((0, -20, 0), (0, 0, 0)), "Piece": ((0, 25, 0), (-0.2, 0, -0.1)),
              "Head": ((0, 0, -12), (0, 0, 0)), "Tail": ((10, 0, 0), (0, 0, 0))}
    return a


# ── 30. Царь-смерч: грозный повелитель бурь — башня из шести ярусов вихря (от песочно-золотого внизу к индиго наверху)
#        с наклонными кольцами ветра, наверху голова-туча с бирюзовыми глазами и хмурыми бровями, корона из золотых
#        молний, два вихря-руки по бокам. Лицо на неподвижной туче; без торса (не джинн) ──────────────────────────────


def tornado_king():
    a = S.Art("Art_TornadoKing", ring_z0=1.6)
    d39v2(a)
    tones = ("E8C060", "D9A048", "B98A6A", "8A6AA8", "6A58B0", "4A44A0")
    for k, code in enumerate(tones):
        a.paint(f"tier{k}", code, rings=True)
    a.paint("cloud", "5A50B8", rings=True)
    for key, code in (("cloudL", "8A84D8"), ("cloudD", "3A3488"), ("swirl", "FFE7B0"), ("swirlD", "F2C230"),
                      ("eyeT", "2ED1C0"), ("white", "FFFDF4"), ("dark", "1A1640"), ("glint", "FFFFFF"),
                      ("brow", "2A2468"), ("mouth", "2A1430"), ("goldD", "C9921A")):
        a.paint(key, code)
    t = legendary_stand(a, 1.66)
    tiers = []
    for k in range(6):
        r = 0.26 + 0.11 * k
        dx, dy = 0.08 * math.cos(math.radians(k * 70)), 0.06 * math.sin(math.radians(k * 70))
        tiers.append((r, dx, dy, t + 0.12 + 0.42 * k))
    names = (("TierA", (0, 1)), ("TierB", (2, 3)), ("TierC", (4, 5)))
    for g, (name, idx) in enumerate(names):
        r0, dx0, dy0, z00 = tiers[idx[0]]
        part(a, name, "Stand" if g == 0 else names[g - 1][0], (dx0, dy0, z00))
        for k in idx:
            r, dx, dy, z0 = tiers[k]
            a.prism(f"tier{k}", S.octagon(dx - r, dx + r, dy - r, dy + r, r * 0.3), z0, z0 + 0.44)
            ang = 40 + 70 * k
            q = (dx + r * 0.96 * math.cos(math.radians(ang)), dy + r * 0.96 * math.sin(math.radians(ang)), z0 + 0.22)
            a.box("swirl", q[0] - 0.3, q[0] + 0.3, q[1] - 0.05, q[1] + 0.05, z0 + 0.14, z0 + 0.28, bevel=0,
                  matrix=tilt(q, "Z", ang + 90) @ tilt(q, "X", 14))
    for k, (z, r, tx, key) in enumerate(((0.95, 0.72, 10, "swirl"), (1.75, 0.98, -9, "swirlD"), (2.45, 1.16, 7, "swirl"))):
        m = tilt((0, 0, t + z), "X", tx) @ tilt((0, 0, t + z), "Y", 6 - 6 * k)
        a.frame(key, ngon(0, 0.02 * k, r, 12), 0.055, t + z - 0.03, t + z + 0.03, axis="z", bevel=0, matrix=m)
    # вихри-руки по бокам верхних ярусов
    for s, name in ((-1, "ArmL"), (1, "ArmR")):
        part(a, name, "TierC", (s * 0.8, 0, t + 2.1))
        base = Vector((s * 0.78, 0.0, t + 2.08))
        d = Vector((s * 1.0, -0.15, 0.5)).normalized()
        m = Matrix.Translation(base) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        for k, (r, z0, z1) in enumerate(((0.32, 0.0, 0.22), (0.26, 0.2, 0.42), (0.19, 0.4, 0.62), (0.12, 0.6, 0.8))):
            a.prism(f"tier{3 + k % 3}", ngon(0.03 * k, 0, r, 8), z0, z1, matrix=m)
    # голова-туча с хмурым лицом
    part(a, "Head", "TierC", (0, 0, t + 2.64))
    cz = t + 2.98
    for x, y, z, r, key in ((0.0, 0.0, 0.0, 0.62, "cloud"), (-0.62, 0.05, -0.08, 0.34, "cloudL"), (0.62, 0.05, -0.06, 0.36, "cloudL"),
                            (0.02, 0.06, 0.4, 0.38, "cloudL"), (-0.34, 0.1, 0.3, 0.26, "cloud"), (0.38, 0.1, 0.3, 0.26, "cloud")):
        a.prism(key, S.octagon(x - r, x + r, y - r * 0.8, y + r * 0.8, r * 0.3), cz + z - r * 0.5, cz + z + r * 0.5)
    fy = -0.62 * 0.8
    for s in (-1, 1):
        a.prism("eyeT", ngon(s * 0.2, cz + 0.04, 0.11, 8), fy - 0.04, fy + 0.02, axis="y")
        a.box("white", s * 0.2 - 0.06, s * 0.2 - 0.02, fy - 0.055, fy - 0.035, cz + 0.07, cz + 0.11, bevel=0)
        bar(a, "brow", (s * 0.38, fy - 0.05, cz + 0.24), (s * 0.06, fy - 0.05, cz + 0.12), 0.09, 0.06)
    a.box("mouth", -0.16, 0.16, fy - 0.04, fy + 0.01, cz - 0.2, cz - 0.15, bevel=0)
    bar(a, "mouth", (0.14, fy - 0.035, cz - 0.175), (0.22, fy - 0.035, cz - 0.24), 0.045, 0.04, bevel=0)
    bar(a, "mouth", (-0.14, fy - 0.04, cz - 0.175), (-0.22, fy - 0.04, cz - 0.24), 0.045, 0.04, bevel=0)
    # корона из золотых молний на ободе
    part(a, "Crown", "Head", (0, 0.06, cz + 0.62))
    a.frame("gold", ngon(0.0, 0.06, 0.36, 10), 0.08, cz + 0.6, cz + 0.72, axis="z", bevel=0)
    bolt = [(-0.06, 0.0), (0.06, 0.0), (0.02, 0.14), (0.1, 0.14), (-0.04, 0.38), (0.0, 0.2), (-0.08, 0.2)]
    for k in range(5):
        ang = math.radians(-90 + (k - 2) * 34)
        x, y = 0.33 * math.cos(ang), 0.06 + 0.33 * math.sin(ang)
        m = Matrix.Translation((x, y, cz + 0.7 + 0.006 * k)) @ Matrix.Rotation(ang + math.pi / 2, 4, "Z")
        a.extrude("gold" if k % 2 == 0 else "goldD", [(px * 1.4, pz * 1.2) for px, pz in bolt], -0.03, 0.03, axis="y", matrix=m)
    a.face = (0, fy, cz + 0.05)
    a.closeup = ((-2.2, -2.0, t + 1.6), (-0.4, -0.2, t + 1.3))
    a.pose = {"TierA": ((0, 0, 35), (0, 0, 0)), "TierB": ((0, 0, -40), (0, 0, 0)), "TierC": ((0, 0, 25), (0, 0, 0)),
              "Crown": ((0, 0, 0), (0, 0, 0.12)), "ArmL": ((0, 15, 0), (0, 0, 0)), "Head": ((0, 0, -15), (0, 0, 0))}
    return a


LEGENDARY = [("SpringAntelope", spring_antelope, "Антилопа-родник", "Legendary"),
             ("PuzzlePhoenix", puzzle_phoenix, "Феникс-головоломка", "Legendary"),
             ("TornadoKing", tornado_king, "Царь-смерч", "Legendary")]


ALL = COMMON + COMMON2 + RARE + globals().get("RARE2", []) + globals().get("EPIC", []) + globals().get("LEGENDARY", [])
ITEMS = [x for x in ALL if (not ONLY and x[0] == "FennecRiddler") or x[0] in ONLY]
TO_RBX = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))  # оси Blender → оси Roblox


# ── Сборка, проверки, кадры ──────────────────────────────────────────────────────────────────────────────────


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
    out = {"id": item_id, "order": list(art.rig), "parts": {}, "demo_pose": {}}
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

ids = [x[0] for x in ITEMS]
rep_name = "report.json" if ids == ["FennecRiddler"] else "report_" + "+".join(ids) + ".json"  # v1 не затирается
with open(os.path.join(SHOTS, rep_name), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("OASIS_OK " + json.dumps({k: v["tris"] for k, v in report.items()}, ensure_ascii=False))
