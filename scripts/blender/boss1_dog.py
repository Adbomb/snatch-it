"""Босс 1 «Сторожевой пёс» (D40), стиль D39: подвижная модель из частей для процедурных анимаций (D18).

Пёс в манере референса владельца (собака из TikTok): голова почти шириной с тело, белая морда-короб с чёрным носом,
чёрные глаза-квадраты с бликом, брови-полоски, ошейник, белые лапы; квадраты-контуры D39 на крупных гранях.
Сторожевой и «немного опасный», но не страшный: нахмуренные брови, нижние клыки, ошейник с шипами, фуражка
охранника с жетоном.

Части (Motor6D): Torso (корень) → Head → Jaw, EyelidL/R, EarL/R; Torso → Tail; лапы из двух частей
(FUpper → FLower, BUpper → BLower), L — левый бок пса (+x). Собрано в масштабе предметов — квадраты D39 того же вида
относительно тела, — затем увеличено в SCALE раз. Две карты 1024² (голова и тело); окклюзия запекается с разнесёнными
частями, чтобы в любой позе не было чужих теней. Веки в модели закрыты (сон), в бодрых позах уходят под бровь.

Пишет assets/models/Boss1_Dog.fbx (части Boss1_Dog<Часть>, начало координат — точка вращения),
assets/textures/art/Boss1_Dog{Head,Body}_{color,normal}.png, а в папку превью — ракурсы, позы, кадр с манекеном,
<часть>.json и rig.json (точки вращения и позы в осях Roblox) для Studio.
Запуск: blender --background --factory-startup --python scripts/blender/boss1_dog.py -- <репо> <превью> [check]
"""

import json
import math
import os
import sys

import bpy
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, PREVIEWS = os.path.abspath(argv[0]), os.path.abspath(argv[1])
CHECK = len(argv) > 2 and argv[2] == "check"
TEXDIR = os.path.join(REPO, "assets", "textures", "art")
os.makedirs(PREVIEWS, exist_ok=True)

SCALE = 3.0  # в игре пёс в SCALE раз больше модели: голова на высоте ≈ 9 стадов
LIFT = 0.255  # насколько веки поднимаются под бровь, когда глаза открыты
HEAD_UP = 0.18  # голова поднята над грудью: видно шею и ошейник

# Часть → (родитель, точка вращения в координатах модели).
RIG = {
    "Torso": (None, (0.0, 0.15, 1.3)),
    "Head": ("Torso", (0.0, -1.05, 1.95 + HEAD_UP)),
    "Jaw": ("Head", (0.0, -1.3, 1.86 + HEAD_UP)),
    "EyelidL": ("Head", (0.245, -1.84, 2.315 + HEAD_UP)),
    "EyelidR": ("Head", (-0.245, -1.84, 2.315 + HEAD_UP)),
    "EarL": ("Head", (0.5, -1.25, 2.66 + HEAD_UP)),
    "EarR": ("Head", (-0.5, -1.25, 2.66 + HEAD_UP)),
    "Tail": ("Torso", (0.0, 1.15, 1.58)),
}
for side, s in (("L", 1), ("R", -1)):
    RIG["FUpper" + side] = ("Torso", (s * 0.57, -0.7, 1.38))
    RIG["FLower" + side] = ("FUpper" + side, (s * 0.57, -0.7, 0.78))
    RIG["BUpper" + side] = ("Torso", (s * 0.6, 0.88, 1.42))
    RIG["BLower" + side] = ("BUpper" + side, (s * 0.6, 0.9, 0.76))
HEAD_PARTS = ("Head", "Jaw", "EyelidL", "EyelidR", "EarL", "EarR")


def colors(a):
    a.paint("fur", "D98C3A", rings=True)  # тёплый рыже-коричневый
    a.paint("saddle", "8A4E2B", rings=True)  # тёмная «попона» на спине, уши, кончик хвоста
    a.paint("cream", "F2E2C4", rings=True)  # морда, грудь, лапы — кремовые: на них видны белые клыки
    a.paint("collar", "D8352A", rings=True)
    a.paint("cap", "2C4A9E", rings=True)  # фуражка охранника
    for key, code in (("dark", "1C1B22"), ("glint", "FFFFFF"), ("brow", "5A3320"), ("spike", "D6DCE6"),
                      ("gold", "F2C230"), ("rim", "B87A12"), ("star", "2C4A9E"), ("band", "1E2230"),
                      ("mouth", "8E2433"), ("tongue", "F07A8C"), ("tooth", "FFFFFF")):
        a.paint(key, code)


def tilt(c, axis, deg):
    """Поворот детали вокруг её центра c (для бровей и ушей)."""
    c = Vector(c)
    return Matrix.Translation(c) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-c)


STAR = ["..#..", ".###.", "#####", ".###.", "#.#.#"]
TAG_STAR = ["..#..", ".###.", "#####", ".###.", ".#.#."]  # на жетоне — без угловых точек, читается издалека


# ── Голова: череп, морда, глаза, брови, фуражка, челюсть, веки, уши ──────────────────────────────────────────


def dog_head():
    a = S.Art("Boss1_DogHead", ring_z0=2.3)
    colors(a)
    a.transform = Matrix.Translation((0, 0, HEAD_UP))
    a.group = "Head"
    a.box("fur", -0.58, 0.58, -1.8, -0.98, 1.86, 2.72)  # череп
    a.box("fur", -0.62, 0.62, -1.74, -1.34, 1.84, 2.16)  # щёки шире черепа — бульдожий силуэт спереди
    a.box("fur", -0.51, 0.51, -1.9, -1.5, 2.435, 2.71)  # тяжёлый надбровный выступ
    a.box("cream", -0.355, 0.355, -2.15, -1.76, 1.8, 2.19)  # морда-короб под глазами, как у референса
    a.box("cream", -0.1, 0.1, -1.98, -1.79, 2.17, 2.3)  # переносица между глаз
    a.box("dark", -0.16, 0.16, -2.21, -2.11, 2.0, 2.21)  # нос
    a.box("mouth", -0.3, 0.3, -2.09, -1.5, 1.775, 1.83, bevel=0)  # нёбо — видно, когда пасть открыта
    a.box("mouth", -0.365, 0.365, -2.16, -2.14, 1.795, 1.835, bevel=0)  # тёмная губа: на ней видны клыки
    for s in (1, -1):
        x0, x1 = sorted((s * 0.17, s * 0.27))
        t0, t1 = sorted((s * 0.2, s * 0.24))
        a.frustum("tooth", (x0, x1, -2.11, -2.01), (t0, t1, -2.08, -2.04), 1.82, 1.62, bevel=0)  # верхние клыки
        # глаз: чёрный квадрат, блик сверху справа (как у референса — у обоих глаз с одной стороны)
        e0, e1 = sorted((s * 0.12, s * 0.37))
        a.box("dark", e0, e1, -1.83, -1.78, 2.2, 2.435, bevel=0)
        g0 = 0.26 if s > 0 else -0.22
        a.box("glint", g0, g0 + 0.07, -1.86, -1.82, 2.33, 2.4, bevel=0)
        # нахмуренная бровь: внутренний конец ниже
        b0, b1 = sorted((s * 0.08, s * 0.44))
        a.box("brow", b0, b1, -1.94, -1.88, 2.48, 2.57, bevel=0, matrix=tilt((s * 0.26, -1.91, 2.525), "Y", -s * 20))
    # фуражка: околыш, расширенная тулья, козырёк, жетон со звездой
    a.box("band", -0.5, 0.5, -1.68, -1.0, 2.66, 2.86)
    a.box("cap", -0.55, 0.55, -1.78, -0.92, 2.86, 3.04)
    a.box("cap", -0.45, 0.45, -1.7, -1.0, 3.03, 3.1)
    a.box("band", -0.42, 0.42, -2.04, -1.62, 2.645, 2.725)
    a.prism("gold", S.octagon(-0.11, 0.11, 2.68, 2.9, 0.045), -1.72, -1.66, axis="y")
    a.pixels(STAR, {"#": ("star", 0.02)}, 0.032, -0.08, 2.87, "xz", 1.72)

    a.group = "Jaw"
    a.box("cream", -0.34, 0.34, -2.19, -1.38, 1.61, 1.845)  # нижняя челюсть чуть впереди — бульдожий прикус
    a.box("tongue", -0.18, 0.18, -1.95, -1.5, 1.83, 1.865, bevel=0)
    for s in (1, -1):
        x0, x1 = sorted((s * 0.16, s * 0.29))
        t0, t1 = sorted((s * 0.195, s * 0.255))
        a.frustum("tooth", (x0, x1, -2.27, -2.12), (t0, t1, -2.24, -2.17), 1.83, 2.09, bevel=0)  # нижние клыки

    for side, s in (("L", 1), ("R", -1)):
        a.group = "Eyelid" + side  # закрытое веко со «спящей» чертой ресниц
        x0, x1 = sorted((s * 0.11, s * 0.38))
        a.box("fur", x0, x1, -1.885, -1.795, 2.19, 2.44, bevel=0)
        a.box("brow", x0 - 0.005, x1 + 0.005, -1.895, -1.875, 2.185, 2.235, bevel=0)

        a.group = "Ear" + side  # ухо торчит из-под фуражки и свисает наружу
        x0, x1 = sorted((s * 0.46, s * 0.72))
        a.box("saddle", x0, x1, -1.42, -1.08, 2.6, 2.89)
        x0, x1 = sorted((s * 0.58, s * 0.78))
        a.box("saddle", x0, x1, -1.46, -1.12, 2.36, 2.64, matrix=tilt((s * 0.68, -1.29, 2.5), "Y", -s * 12))
    return a


# ── Тело: грудь, живот, круп, шея, ошейник, жетон, хвост, лапы ───────────────────────────────────────────────


def dog_body():
    a = S.Art("Boss1_DogBody", ring_z0=1.3)
    colors(a)
    a.group = "Torso"
    a.box("fur", -0.62, 0.62, -1.05, -0.25, 0.82, 1.86)  # широкая грудь
    a.box("fur", -0.52, 0.52, -0.27, 0.64, 0.95, 1.72)  # живот уже — ступенька в силуэте
    a.box("fur", -0.57, 0.57, 0.62, 1.18, 0.92, 1.74)  # круп
    a.box("saddle", -0.46, 0.46, -0.4, 1.02, 1.68, 1.82)  # тёмная спина
    a.box("cream", -0.44, 0.44, -1.11, -1.03, 1.12, 1.66)  # белая грудь двумя ступенями
    a.box("cream", -0.26, 0.26, -1.11, -1.03, 0.9, 1.12)
    a.box("fur", -0.42, 0.42, -1.28, -0.8, 1.45, 2.2)  # шея
    a.box("collar", -0.48, 0.48, -1.34, -0.74, 1.5, 1.74)  # ошейник — между челюстью и грудью
    for x in (-0.33, 0.33):  # крупные шипы: по одному по сторонам жетона и по бокам
        a.frustum("spike", (x - 0.07, x + 0.07, 1.55, 1.69), (x, x, 1.62, 1.62), -1.33, -1.52, axis="y", bevel=0)
    for s in (1, -1):
        a.frustum("spike", (1.55, 1.69, -1.11, -0.97), (1.62, 1.62, -1.04, -1.04), s * 0.47, s * 0.66, axis="x",
                  bevel=0)
    # жетон «охрана»: крупный, с тёмным ободком и простой звездой — читается издалека
    a.prism("rim", S.octagon(-0.18, 0.18, 1.18, 1.54, 0.065), -1.38, -1.33, axis="y")
    a.prism("gold", S.octagon(-0.14, 0.14, 1.22, 1.5, 0.05), -1.4, -1.37, axis="y")
    a.pixels(TAG_STAR, {"#": ("star", 0.02)}, 0.045, -0.1125, 1.4725, "xz", 1.4)

    a.group = "Tail"  # хвост торчком, дугой назад; широкая тёмная кисточка — силуэт читается и сзади
    tail = [(1.02, 1.42), (1.34, 1.42), (1.34, 1.58), (1.48, 1.58), (1.48, 1.8), (1.58, 1.8), (1.58, 2.04),
            (1.66, 2.04), (1.66, 2.3), (1.34, 2.3), (1.34, 2.04), (1.24, 2.04), (1.24, 1.8), (1.12, 1.8),
            (1.12, 1.58), (1.02, 1.58)]  # (y, z)
    a.extrude("fur", [(z, y) for y, z in tail], -0.16, 0.16, axis="x")
    a.box("saddle", -0.23, 0.23, 1.3, 1.72, 2.0, 2.44)
    a.box("saddle", -0.15, 0.15, 1.37, 1.65, 2.42, 2.53)

    for side, s in (("L", 1), ("R", -1)):
        def sx(u, v):
            return sorted((s * u, s * v))

        a.group = "FUpper" + side  # плечо выступает из груди
        a.box("fur", *sx(0.4, 0.75), -0.93, -0.47, 0.72, 1.5)
        a.group = "FLower" + side
        a.box("fur", *sx(0.42, 0.72), -0.9, -0.5, 0.17, 0.8)
        a.box("cream", *sx(0.39, 0.76), -1.0, -0.47, 0.0, 0.2)  # белая лапа
        for x in (0.51, 0.63):
            a.box("brow", *sx(x - 0.012, x + 0.012), -1.02, -0.98, 0.02, 0.17, bevel=0)  # пальцы
        a.group = "BUpper" + side  # мощное бедро шире крупа, мышца ступенькой наружу
        a.box("fur", *sx(0.42, 0.82), 0.52, 1.24, 0.66, 1.6)
        a.box("fur", *sx(0.46, 0.87), 0.6, 1.15, 0.86, 1.44)
        a.group = "BLower" + side
        a.box("fur", *sx(0.43, 0.79), 0.68, 1.14, 0.17, 0.8)
        a.box("cream", *sx(0.4, 0.82), 0.58, 1.18, 0.0, 0.21)
        for x in (0.53, 0.69):
            a.box("brow", *sx(x - 0.012, x + 0.012), 0.56, 0.6, 0.02, 0.18, bevel=0)
    return a


# ── Позы: часть → (поворот XYZ в градусах относительно родителя, сдвиг в единицах модели) ─────────────────────

OPEN_EYES = {"EyelidL": ((0, 0, 0), (0, 0, LIFT)), "EyelidR": ((0, 0, 0), (0, 0, LIFT))}
POSES = {
    "stand": {**OPEN_EYES},
    "sleep": {
        "Torso": ((0, 0, 0), (0, 0, -0.8)),
        "Head": ((-6, 0, 0), (0, -0.16, -0.46)),  # подбородок на лапах, морда видна
        "EarL": ((0, -25, 0), (0, 0, 0)), "EarR": ((0, 25, 0), (0, 0, 0)),
        "Tail": ((-80, 0, 0), (0, 0, 0)),
        "FUpperL": ((-60, 0, 0), (0, 0, 0)), "FLowerL": ((-30, 0, 0), (0, 0, 0)),
        "FUpperR": ((-60, 0, 0), (0, 0, 0)), "FLowerR": ((-30, 0, 0), (0, 0, 0)),
        "BUpperL": ((-90, 0, 0), (0, 0, -0.25)), "BLowerL": ((180, 0, 0), (0, 0, 0)),  # бедро вдоль бока
        "BUpperR": ((-90, 0, 0), (0, 0, -0.25)), "BLowerR": ((180, 0, 0), (0, 0, 0)),
    },
    "combat": {
        **OPEN_EYES,
        "Torso": ((0, 0, 0), (0, 0, -0.1)),
        "Head": ((12, 0, 0), (0, -0.06, -0.06)),
        "Jaw": ((24, 0, 0), (0, 0, 0)),
        "EarL": ((-30, 0, 0), (0, 0, 0)), "EarR": ((-30, 0, 0), (0, 0, 0)),
        "Tail": ((20, 0, 0), (0, 0, 0)),
        "FUpperL": ((16, -7, 0), (0, 0, 0)), "FLowerL": ((-16, 0, 0), (0, 0, 0)),
        "FUpperR": ((16, 7, 0), (0, 0, 0)), "FLowerR": ((-16, 0, 0), (0, 0, 0)),
        "BUpperL": ((-20, -6, 0), (0, 0, 0)), "BLowerL": ((20, 0, 0), (0, 0, 0)),
        "BUpperR": ((-20, 6, 0), (0, 0, 0)), "BLowerR": ((20, 0, 0), (0, 0, 0)),
    },
}


def pose_matrices(pose):
    """Мировые матрицы частей в позе (в стадах), низ пса — на z = 0."""
    out = {}

    def world(name):
        if name in out:
            return out[name]
        parent, pivot = RIG[name]
        rot, off = pose.get(name, ((0, 0, 0), (0, 0, 0)))
        r = Euler([math.radians(d) for d in rot], "XYZ").to_matrix().to_4x4()
        local = Vector(pivot) - (Vector(RIG[parent][1]) if parent else Vector())
        m = Matrix.Translation((local + Vector(off)) * SCALE) @ r
        out[name] = (world(parent) @ m) if parent else m
        return out[name]

    for name in RIG:
        world(name)
    return out


def apply_pose(parts, pose, place=Matrix.Identity(4)):
    mats = pose_matrices(POSES[pose])
    low = min((mats[n] @ v.co).z for n, o in parts.items() for v in o.data.vertices)
    ground = Matrix.Translation((0, 0, -low))
    for n, o in parts.items():
        o.matrix_world = place @ ground @ mats[n]
    return {n: ground @ mats[n] for n in parts}


# ── Сборка ───────────────────────────────────────────────────────────────────────────────────────────────────

bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new("Boss1")
bpy.context.scene.collection.children.link(collection)

arts = [dog_head(), dog_body()]
report = {"scale": SCALE}
if CHECK:
    for art in arts:
        art.build(collection)
        print("CHECK", art.name, json.dumps(art.stats, ensure_ascii=False))
    sys.exit(0)


def explode(obj, art, sign):
    """Разнести части по x на 10 шагов квадратов D39 (рисунок не сдвигается), чтобы окклюзия была только своя."""
    order = {g: i for i, g in enumerate(dict.fromkeys(art.face_groups))}
    me = obj.data
    done = set()
    for poly in me.polygons:
        dx = order[art.face_groups[poly.index]] * 10 * S.RING["step"] * sign
        for v in poly.vertices:
            if v not in done:
                me.vertices[v].co.x += dx
                done.add(v)


parts = {}
for art in arts:
    obj = art.build(collection)
    explode(obj, art, 1)
    uv = S.bake(obj, art, TEXDIR, art.name)
    explode(obj, art, -1)
    report[art.name] = {**art.stats, "uv_fill": round(uv["uv_fill"], 3),
                        "texels_per_stud": round(uv["texels_per_stud"] / SCALE, 1)}
    groups = dict.fromkeys(art.face_groups)
    split = S.split_groups(obj, art, {g: RIG[g][1] for g in groups}, collection)
    for g, o in split.items():
        o.data.transform(Matrix.Scale(SCALE, 4))
        o.location = Vector(RIG[g][1]) * SCALE
        o.data.calc_loop_triangles()
        report.setdefault("tris", {})[g] = len(o.data.loop_triangles)
        parts[g] = o
report["tris_total"] = sum(report["tris"].values())

S.export_fbx([parts[n] for n in RIG], os.path.join(REPO, "assets", "models", "Boss1_Dog.fbx"))

# Studio: меш каждой части (вершины относительно точки вращения) и позы в осях Roblox.
TO_RBX = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
rig = {"parents": {n: RIG[n][0] for n in RIG}, "poses": {}}
for n, o in parts.items():
    S.studio_json(o, os.path.join(PREVIEWS, f"Dog_{n}.json"))
for pose in POSES:
    mats = apply_pose(parts, pose)
    rig["poses"][pose] = {}
    for n, m in mats.items():
        r = TO_RBX @ m @ TO_RBX.inverted()
        rig["poses"][pose][n] = [round(r[0][3], 4), round(r[1][3], 4), round(r[2][3], 4)] + [
            round(r[i][j], 5) for i in range(3) for j in range(3)]
with open(os.path.join(PREVIEWS, "rig.json"), "w", encoding="utf-8") as f:
    json.dump(rig, f)

# ── Проверочные рендеры ──────────────────────────────────────────────────────────────────────────────────────

prev = S.Preview(collection)
floor = bpy.data.objects["Floor"]
floor.scale = (1, 2.2, 2.2)  # циклорама под пса: дальше и выше
floor.location.y = 6
for i, (light, loc) in enumerate(prev.lights):
    light.data.energy *= 7
    light.data.size *= 2.5
    prev.lights[i] = (light, loc * 2.6)
prev.aim_lights(Vector((0, 0, 0)))


def turn(deg):
    return Matrix.Rotation(math.radians(deg), 4, "Z")


tiles = []
for label, deg in (("front", 0), ("34", -40), ("side", -90), ("back", 180), ("34back", 140)):
    apply_pose(parts, "combat", turn(deg))
    tiles.append(prev.shot(os.path.join(PREVIEWS, f"dog_combat_{label}.png"), (0, -30, 8.5), (0, 0, 4.0), 50,
                           (800, 800)))
S.strip(tiles, os.path.join(PREVIEWS, "dog_turns_combat.png"))
tiles = []
for label, deg in (("34", -40), ("side", -90), ("front", 0)):
    apply_pose(parts, "sleep", turn(deg))
    tiles.append(prev.shot(os.path.join(PREVIEWS, f"dog_sleep_{label}.png"), (0, -30, 8.5), (0, 0, 2.5), 50,
                           (800, 800)))
S.strip(tiles, os.path.join(PREVIEWS, "dog_turns_sleep.png"))
apply_pose(parts, "stand", turn(-35))
prev.shot(os.path.join(PREVIEWS, "dog_stand_34.png"), (0, -30, 8.5), (0, 0, 4.0), 50, (1000, 1000))
apply_pose(parts, "stand", turn(90))
prev.shot(os.path.join(PREVIEWS, "dog_top.png"), (0, -0.01, 34), (0, 0, 0), 50, (1000, 1000))
apply_pose(parts, "combat", turn(-28))
prev.shot(os.path.join(PREVIEWS, "dog_head_close.png"), (-7.0, -17.0, 9.0), (-2.0, -3.8, 6.6), 50, (1100, 1100))

# Масштаб: спящий и в стойке рядом с манекеном Roblox (5.2 стада).
apply_pose(parts, "combat", Matrix.Translation((-10.5, 0, 0)) @ turn(-90))
sleeper = {n: o.copy() for n, o in parts.items()}
for o in sleeper.values():
    collection.objects.link(o)
apply_pose(sleeper, "sleep", Matrix.Translation((11.0, 0, 0)) @ turn(-90))
S.mannequin(collection, 0.0, y=-1.0)
prev.aim_lights(Vector((0, 0, 0)))
prev.shot(os.path.join(PREVIEWS, "dog_scale.png"), (0, -54, 9.0), (0, 0, 4.0), 50, (1800, 800))

with open(os.path.join(PREVIEWS, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("DOG_OK " + json.dumps(report, ensure_ascii=False))
