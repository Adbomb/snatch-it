"""Концепты Ловибумов v4 (D55, этап 0): Бум, Турбо и Мега — игрушечные устройства поимки, стиль D39.

История: v1 (персонажи с лицами) отклонён; v2–v3 (энергетические капсулы) — направление верное, но владелец увидел в
них батарейки и картриджи (2026-11-08). v4 сохраняет идею компактной капсулы с энергетическим ядром, цвета и захват
сетью, а силуэт делает игрушечным. Фирменный элемент всей линейки — «кристалл в когтях»: четыре угловые стойки v3
стали сегментированными когтями-захватами, они выгибаются наружу и смыкаются над головой, держа кристалл-ромб; между
когтями светится ядро. При поимке когти раскрываются, кристалл выпускает сеть — символ стал и силуэтом, и механизмом.
Плоских торцов-«контактов» нет. Прогрессия:
- Бум (×1): широкий и приземистый, толстые оранжевые когти с жёлтыми суставами, боковые защёлки, бирюзовое ядро;
- Турбо (×1.5): вытянутый, хищные синие когти со световыми полосами, большие стреловидные стабилизаторы со светящейся
  кромкой, сопло-кольцо снизу, голубой вытянутый кристалл;
- Мега (×2): фиолетовые когти с золотыми суставами и кончиками, золотой обод-корона на кончиках, золотая база с
  камнями, самый крупный кристалл.
Без глаз, ртов и лиц; без центральной кнопки и деления на половины.

Только концепт на утверждение: рендеры EEVEE и проход свечения (<кадр>_glow.png — листы scripts/d55_lovibum_sheets.py
размывают его и добавляют к кадру), без запекания, FBX и загрузок. 1 единица = 1 стад, z вверх, лицом в −y.
Запуск: blender --background --factory-startup --python scripts/blender/lovibum_concepts.py -- <репо> <превью>
Зависит от art_style.py.
"""

import json
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
os.makedirs(OUT, exist_ok=True)
GLOW = {"core": 1.4, "crystal": 1.6, "glow": 2.4, "net": 2.0, "spark": 2.6}  # светящиеся ключи и сила свечения

TYPES = {
    "Boom": {"claw": "FF8A1F", "knuckle": "FFC21A", "tip": "FFC21A", "base": "FFC21A", "foot": "2A3344",
             "trim": "E8641A", "core": "2EE6D6", "crystal": "22D8C8", "glow": "8AFFF2",
             "widths": (0.36, 0.35, 0.32, 0.27, 0.2), "thick": 0.12, "scale": (1.12, 1.12, 0.92),
             "profile": [(0.34, 0.14), (0.46, 0.33), (0.5, 0.55), (0.46, 0.77), (0.34, 0.92), (0.2, 1.0)],
             "crystal_at": (0.95, 1.13, 1.38, 0.16),
             "orb": [(0.2, 0.17, 0.27), (0.31, 0.25, 0.39), (0.37, 0.37, 0.63), (0.31, 0.61, 0.79), (0.2, 0.77, 0.9)]},
    "Turbo": {"claw": "2F6BFF", "knuckle": "1E2B4F", "tip": "E6F3FF", "base": "E6F3FF", "foot": "1E2B4F",
              "trim": "1E2B4F", "core": "3FD8FF", "crystal": "2CB8FF", "glow": "5CE8FF",
              "widths": (0.28, 0.27, 0.23, 0.18, 0.13), "thick": 0.1, "scale": (0.98, 0.98, 1.06),
              "profile": [(0.33, 0.14), (0.43, 0.36), (0.45, 0.6), (0.38, 0.84), (0.25, 1.01), (0.14, 1.11)],
              "crystal_at": (1.04, 1.24, 1.56, 0.13),
              "orb": [(0.18, 0.17, 0.29), (0.27, 0.27, 0.43), (0.33, 0.41, 0.69), (0.27, 0.67, 0.87),
                      (0.17, 0.85, 1.0)]},
    "Mega": {"claw": "7A2FE0", "knuckle": "F2C230", "tip": "F2C230", "base": "F2C230", "foot": "C98E12",
             "trim": "C98E12", "core": "E57BFF", "crystal": "D45CFF", "glow": "FFD1FF",
             "widths": (0.34, 0.33, 0.3, 0.25, 0.19), "thick": 0.12, "scale": (1.05, 1.05, 1.05),
             "profile": [(0.35, 0.16), (0.47, 0.37), (0.51, 0.59), (0.46, 0.82), (0.33, 0.98), (0.21, 1.07)],
             "crystal_at": (0.98, 1.21, 1.53, 0.21),
             "orb": [(0.2, 0.18, 0.28), (0.32, 0.26, 0.41), (0.38, 0.39, 0.66), (0.32, 0.64, 0.83),
                     (0.21, 0.81, 0.95)]},
}
OPEN_DEG = 52  # раскрытие когтей при поимке


# ── Помощники ────────────────────────────────────────────────────────────────────────────────────────────────


def sq(h, cut):
    return S.octagon(-h, h, -h, h, cut)


def bar(a, key, p0, p1, w, h=None, bevel=S.BEVEL):
    """Брусок от p0 до p1 с сечением w × h (поворот сечения — как получится; для сетей и следов)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    up = "Y" if abs(d.normalized().z) > 0.95 else "Z"
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("X", up).to_matrix().to_4x4()
    h = h or w
    a.box(key, -d.length / 2, d.length / 2, -w / 2, w / 2, -h / 2, h / 2, bevel=bevel, matrix=m)


def bar_side(a, key, p0, p1, w, h, side, bevel=S.BEVEL, extend=0.0):
    """Брусок от p0 до p1: ширина w вдоль side (поперёк плоскости когтя), толщина h — в плоскости когтя."""
    p0, p1 = Vector(p0), Vector(p1)
    x = (p1 - p0).normalized()
    y = (side - x * side.dot(x)).normalized()
    z = x.cross(y)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = (p0 + p1) / 2
    half = (p1 - p0).length / 2 + extend
    a.box(key, -half, half, -w / 2, w / 2, -h / 2, h / 2, bevel=bevel, matrix=m)


def paint(a, spec):
    for key, code, rings in (("claw", spec["claw"], True), ("knuckle", spec["knuckle"], False),
                             ("tip", spec["tip"], False), ("base", spec["base"], False), ("foot", spec["foot"], False),
                             ("trim", spec["trim"], False), ("core", spec["core"], False),
                             ("crystal", spec["crystal"], False), ("glow", spec["glow"], False),
                             ("gemp", "FF3B7F", False), ("gemc", "3FE0FF", False), ("white", "FFFDF4", False)):
        a.paint(key, code, rings)


def claw(a, theta, prof, widths, thick, open_deg=0.0, strip=None, hinges=(1, 3)):
    """Коготь-лепесток в вертикальной плоскости под углом theta: пластины сужаются к кончику (ширина поперёк плоскости
    когтя, толщина — по радиусу), чередование толщины — без совпадающих граней; оси-шарниры поперёк когтя (видно, что
    он раскрывается); кончик — крючок к кристаллу; strip — полоса по наружной стороне (свет у Турбо, золото у Меги).
    open_deg — раскрытие наружу вокруг основания."""
    u = Vector((math.cos(theta), math.sin(theta), 0))
    t = Vector((-math.sin(theta), math.cos(theta), 0))
    pts = [u * r + Vector((0, 0, z)) for r, z in prof]
    if open_deg:
        rot = Matrix.Rotation(math.radians(open_deg), 4, t)
        pts = [pts[0] + (rot @ (p - pts[0])) for p in pts]
    n = len(pts) - 1
    for i in range(n):
        bar_side(a, "claw", pts[i], pts[i + 1], widths[i], thick * (1 if i % 2 == 0 else 0.9), t, extend=0.025)
    for i in hinges:
        half = widths[i] / 2 + 0.035
        bar_side(a, "knuckle", pts[i] - t * half, pts[i] + t * half, 0.085 + 0.006 * (i % 2), 0.085, u)
    tip = pts[-1]
    hook = Vector((-u.x, -u.y, 0)) * 0.09 + Vector((0, 0, 0.05))
    bar_side(a, "tip", tip, tip + hook, widths[-1] * 0.8, thick * 1.1, t, extend=0.03)
    bar_side(a, "tip", tip + hook, tip + hook * 1.7, widths[-1] * 0.45, thick * 0.8, t)
    if strip:
        for i in range(n - 1):
            d = (pts[i + 1] - pts[i]).normalized()
            out = t.cross(d).normalized()  # наружу от оси
            if out.dot(u) < 0:
                out = -out
            off = out * (thick / 2 + 0.006)
            bar_side(a, strip, pts[i] + off, pts[i + 1] + off, 0.06 + 0.004 * (i % 2), 0.024, t, bevel=0)
    return pts


def crystal(a, lo, mid, hi, half, key="crystal", lift=0.0):
    """Кристалл-ромб (бипирамида, повёрнута на 45°: грани смотрят на когти)."""
    rot = Matrix.Translation((0, 0, lift)) @ Matrix.Rotation(math.radians(45), 4, "Z")
    a.frustum(key, (-0.02, 0.02, -0.02, 0.02), (-half, half, -half, half), lo, mid + 0.005, matrix=rot)
    a.frustum(key, (-half, half, -half, half), (-0.02, 0.02, -0.02, 0.02), mid - 0.005, hi, matrix=rot)


# ── Ловибум: общая конструкция «кристалл в когтях» ──────────────────────────────────────────────────────────


def lovibum(name, opened=False):
    spec = TYPES[name]
    a = S.Art("Lovibum_" + name + ("_open" if opened else ""), ring_z0=0.6)
    paint(a, spec)
    sx, sy, sz = spec["scale"]
    a.transform = Matrix.Diagonal((sx, sy, sz, 1.0))
    # База: ножка и кольцо, из которого растут когти.
    a.prism("foot", sq(0.26, 0.07), 0.0, 0.07)
    a.prism("base", sq(0.42, 0.13), 0.05, 0.2)
    # Ядро-шар ступенями — светится между когтями.
    for h, z0, z1 in spec["orb"]:
        a.prism("core", sq(h, h * 0.32), z0, z1)
    strip = {"Turbo": "glow", "Mega": "knuckle"}.get(name)
    for k in range(4):
        claw(a, math.pi / 4 + k * math.pi / 2, spec["profile"], spec["widths"], spec["thick"],
             OPEN_DEG if opened else 0.0, strip=strip)
    lo, mid, hi, half = spec["crystal_at"]
    crystal(a, lo, mid, hi, half, lift=0.14 if opened else 0.0)
    if name == "Boom":
        # Боковые защёлки, как у игрушечного ланч-бокса.
        for s in (-1, 1):
            a.box("base", s * 0.4, s * 0.56, -0.13, 0.13, 0.34, 0.62)
            a.box("trim", s * 0.54, s * 0.62, -0.1, 0.1, 0.55, 0.69)
            a.box("trim", s * 0.555, s * 0.585, -0.07, 0.07, 0.39, 0.45)
    if name == "Turbo":
        # Стреловидные стабилизаторы со светящейся передней кромкой; сопло-кольцо снизу.
        fin = [(0.38, 0.2), (0.38, 0.8), (0.56, 0.72), (0.95, 0.25), (0.98, 0.05), (0.72, 0.11)]
        for s in (-1, 1):
            pts = [(s * x, z) for x, z in fin]
            a.extrude("trim", pts, -0.034, 0.034, axis="y")
            bar_side(a, "glow", Vector((s * 0.57, 0, 0.74)), Vector((s * 0.97, 0, 0.26)), 0.08, 0.05,
                     Vector((0, 1, 0)), bevel=0)
            a.box("white", s * 0.37, s * 0.46, -0.05, 0.05, 0.32, 0.7)
        a.prism("glow", sq(0.2, 0.06), -0.05, 0.015)
    if name == "Mega":
        # Камни на золотой базе, золотой обод-корона на кончиках когтей.
        for k in range(4):
            ang = k * math.pi / 2
            c = Vector((math.cos(ang) * 0.42, math.sin(ang) * 0.42, 0.125))
            a.box("gemp" if k % 2 else "gemc", -0.05, 0.05, -0.05, 0.05, -0.05, 0.05,
                  matrix=Matrix.Translation(c) @ Matrix.Rotation(ang, 4, "Z") @ Matrix.Rotation(math.radians(45), 4,
                                                                                                    "X"))
        if not opened:
            pts = [Vector((math.cos(math.pi / 4 + k * math.pi / 4) * 0.25, math.sin(math.pi / 4 + k * math.pi / 4) * 0.25,
                           1.06)) for k in range(8)]
            for k in range(8):
                bar(a, "knuckle", pts[k], pts[(k + 1) % 8], 0.06 if k % 2 else 0.068, 0.07 if k % 2 else 0.078)
    a.transform = None
    return a


# ── Эффекты захвата: сеть, куб, искры, след ─────────────────────────────────────────────────────────────────


def fx_art(name, color):
    a = S.Art(name)
    a.paint("net", color)
    a.paint("spark", color)
    a.paint("white", "FFFFFF")
    return a


def net_dome(a, base, top, z0, z1, rings=6, lines=6, w=0.03):
    """Сеть-купол: квадратные кольца, полусторона от base на z0 до top на z1 по выпуклому профилю, и линии по граням."""
    hs = [top + (base - top) * math.cos(math.pi / 2 * i / rings) ** 0.6 for i in range(rings + 1)]
    zs = [z0 + (z1 - z0) * (i / rings) ** 1.15 for i in range(rings + 1)]
    for h, z in zip(hs, zs):
        c = [Vector((-h, -h, z)), Vector((h, -h, z)), Vector((h, h, z)), Vector((-h, h, z))]
        for i in range(4):
            bar(a, "net", c[i], c[(i + 1) % 4], w, w, bevel=0)
    for side in range(4):
        for j in range(lines + 1):
            s = -1 + 2 * j / lines

            def at(h, z):
                p = [(s * h, -h), (h, s * h), (-s * h, h), (-h, -s * h)][side]
                return Vector((p[0], p[1], z))
            for i in range(rings):
                bar(a, "net", at(hs[i], zs[i]), at(hs[i + 1], zs[i + 1]), w, w, bevel=0)


def net_cube(a, h, z0, cells=3, w=0.035):
    """Сеть, стянутая в куб: решётка на всех гранях куба полустороны h, низ на z0."""
    for i in range(cells + 1):
        t = -h + 2 * h * i / cells
        for z in (z0, z0 + 2 * h):
            bar(a, "net", (t, -h, z), (t, h, z), w, w, bevel=0)
            bar(a, "net", (-h, t, z), (h, t, z), w, w, bevel=0)
        for s in (-1, 1):
            bar(a, "net", (t, s * h, z0), (t, s * h, z0 + 2 * h), w, w, bevel=0)
            bar(a, "net", (s * h, t, z0), (s * h, t, z0 + 2 * h), w, w, bevel=0)
            zz = z0 + 2 * h * i / cells
            bar(a, "net", (-h, s * h, zz), (h, s * h, zz), w, w, bevel=0)
            bar(a, "net", (s * h, -h, zz), (s * h, h, zz), w, w, bevel=0)


def sparks(a, center, count, r0, r1, size, seed, key="spark", up=0.0):
    rnd = random.Random(seed)
    for _ in range(count):
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.2, 1) + up)).normalized()
        p = Vector(center) + d * rnd.uniform(r0, r1)
        s = size * rnd.uniform(0.6, 1.2)
        m = Matrix.Translation(p) @ Matrix.Rotation(rnd.uniform(0, 3.14), 4, Vector((rnd.random(), rnd.random(), 1)))
        a.box(key if rnd.random() > 0.25 else "white", -s, s, -s, s, -s, s, bevel=0, matrix=m)


def trail(a, path, sizes):
    for p, s in zip(path, sizes):
        m = Matrix.Translation(p) @ Matrix.Rotation(0.6, 4, "Z") @ Matrix.Rotation(0.4, 4, "X")
        a.box("spark", -s, s, -s, s, -s, s, bevel=0, matrix=m)


def build(art, glow_keys=GLOW):
    obj = art.build(collection)
    for mat in obj.data.materials:
        key = mat.name.split("_")[-1]
        if key in glow_keys:
            b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            b.inputs["Emission Strength"].default_value = glow_keys[key]
    return obj


def core_light(obj, color, z, energy=6.0):
    """Свет ядра изнутри — подсвечивает когти цветом ядра; следует за Ловибумом."""
    data = bpy.data.lights.new(obj.name + "_Core", "POINT")
    data.energy, data.color, data.shadow_soft_size = energy, S.rgb(color), 0.1
    light = bpy.data.objects.new(obj.name + "_Core", data)
    collection.objects.link(light)
    light.parent = obj
    light.location = (0, 0, z)
    return light


def creature():
    """Существо босса 3 из FBX с картой цвета (без подставки) — для кадров поимки; пустой список, если не вышло."""
    fbx = os.path.join(REPO, "assets", "models", "art", "LiveCheeseMonster.fbx")
    tex = os.path.join(REPO, "assets", "textures", "art", "LiveCheeseMonster_color.png")
    if not (os.path.exists(fbx) and os.path.exists(tex)):
        return []
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.fbx(filepath=fbx)
    except Exception as e:  # noqa: BLE001
        print("CREATURE_FAIL", e)
        return []
    objs = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    mat = bpy.data.materials.new("Creature")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    img = nt.nodes.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(tex)
    nt.links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.5
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(mat)
        for c in list(o.users_collection):
            c.objects.unlink(o)
        collection.objects.link(o)
        if "Stand" in o.name:
            o.hide_render = True
            o.name = "CreatureStand"
        else:
            o.name = "Creature_" + o.name
    return [o for o in objs if not o.name.startswith("CreatureStand")]


# ── Сцена ───────────────────────────────────────────────────────────────────────────────────────────────────

bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new("Lovibums")
bpy.context.scene.collection.children.link(collection)

report, caps, opens = {}, {}, {}
for name in TYPES:
    for opened, store in ((False, caps), (True, opens)):
        art = lovibum(name, opened)
        obj = build(art)
        if not opened:
            lo, hi = S.bounds(obj)
            report[name] = {**art.stats, "size": [round(hi[i] - lo[i], 2) for i in range(3)]}
        store[name] = obj
        core_light(obj, TYPES[name]["core"], 0.55 * TYPES[name]["scale"][2])
print("REPORT " + json.dumps(report, ensure_ascii=False), flush=True)

prev = S.Preview(collection)
world_bg = next(n for n in bpy.context.scene.world.node_tree.nodes if n.type == "BACKGROUND")


def only(objs):
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and o.name != "Floor":
            o.hide_render = o not in objs or o.name.startswith("CreatureStand")
    for o in bpy.context.scene.objects:
        if o.type == "LIGHT" and o.parent is not None:
            o.hide_render = o.parent.hide_render


def shot(path, eye, target, lens, res):
    """Кадр и его проход свечения (свет и небо выключены — видно только светящееся)."""
    prev.shot(path, eye, target, lens, res)
    lights = [(o, o.data.energy) for o in bpy.context.scene.objects if o.type == "LIGHT"]
    strength = world_bg.inputs["Strength"].default_value
    floor = bpy.context.scene.objects["Floor"]
    for o, _ in lights:
        o.data.energy = 0
    world_bg.inputs["Strength"].default_value = 0
    floor.hide_render = True
    prev.shot(path.replace(".png", "_glow.png"), eye, target, lens, res)
    for o, e in lights:
        o.data.energy = e
    world_bg.inputs["Strength"].default_value = strength
    floor.hide_render = False


def place(obj, loc, rot=(0, 0, 0)):
    obj.rotation_mode = "XYZ"
    obj.location, obj.rotation_euler = loc, rot


def aim(obj, loc, direction, spin=0.0):
    """Ловибум кристаллом по направлению полёта (и поворот вокруг своей оси)."""
    q = Vector(direction).normalized().to_track_quat("Z", "Y")
    obj.rotation_mode = "QUATERNION"
    obj.location = loc
    obj.rotation_quaternion = q @ Matrix.Rotation(spin, 4, "Z").to_quaternion()


def hero(obj, path):
    lo, hi = S.bounds(obj)
    size, cz = max(hi - lo), (lo.z + hi.z) / 2
    dist = 2.7 * size + 1.0
    shot(path, (-0.62 * dist, -0.85 * dist, cz + 0.55 * size), (0, 0, cz - 0.05 * size), 75, (1100, 1100))


# 1. Повороты, крупный кадр и раскрытые когти каждого.
for name, obj in caps.items():
    only([obj])
    S.render_item(prev, obj, OUT)
    only([obj])
    hero(obj, os.path.join(OUT, f"{obj.name}_hero.png"))
    only([opens[name]])
    hero(opens[name], os.path.join(OUT, f"Lovibum_{name}_open_hero.png"))

# 2. Линейка: три рядом, слева направо по старшинству.
for name, x in (("Boom", -1.55), ("Turbo", 0.05), ("Mega", 1.7)):
    place(caps[name], (x, 0, 0), (0, 0, math.radians(-25)))
only(list(caps.values()))
bpy.context.view_layer.update()
shot(os.path.join(OUT, "lineup.png"), (-1.2, -6.9, 2.4), (0.1, 0, 0.72), 50, (2000, 1000))

# 3. В полёте: кристаллом вперёд, короткий след из квадратных искр цвета ядра.
fly = []
for i, (name, x, z) in enumerate((("Boom", -3.3, 3.5), ("Turbo", 0.1, 2.25), ("Mega", 3.5, 1.0))):
    d = Vector((1, 0, -0.12)).normalized()
    aim(caps[name], Vector((x, 0, z)), d, spin=0.5 + 0.4 * i)
    t = fx_art(f"Trail_{name}", TYPES[name]["core"])
    path = [Vector((x, 0, z)) - d * (0.9 + 0.2 * k) + Vector((0, 0, 0.01 * k * k)) for k in range(6)]
    trail(t, path, [0.075 * (1 - k / 7) for k in range(6)])
    fly.append(build(t))
only(list(caps.values()) + fly)
bpy.context.view_layer.update()
shot(os.path.join(OUT, "flight.png"), (0.0, -14.5, 3.4), (0.0, 0, 2.25), 50, (2000, 1000))
for o in fly:
    o.hide_render = True
for o in caps.values():
    place(o, (0, 0, 0))

# 4. Поимка энергетической сетью (Бум): бросок → когти раскрылись, сеть → сжатие → поймано; и «вырвалось».
cre = creature()
boom, boom_open = caps["Boom"], opens["Boom"]
boom_core = TYPES["Boom"]["core"]
cre_h = 2.6
if cre:
    bpy.context.view_layer.update()
    lo = Vector([min(S.bounds(o)[0][i] for o in cre) for i in range(3)])
    hi = Vector([max(S.bounds(o)[1][i] for o in cre) for i in range(3)])
    for o in cre:
        if o.parent is None:
            o.location += Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
    cre_h = hi.z - lo.z
    print("CREATURE", len(cre), [round(v, 2) for v in (hi - lo)], flush=True)
base_tf = {o: (o.location.copy(), o.scale.copy(), o.rotation_euler.copy()) for o in cre if o.parent is None}


def set_creature(scale=1.0, z=0.0, hide=False, offset=Vector((0, 0, 0)), face=False):
    """Существо целиком: части FBX — верхние объекты; масштаб от начала координат; face — лицом к +y (к игроку)."""
    turn = Matrix.Rotation(math.pi if face else 0.0, 4, "Z")
    for o in cre:
        o.hide_render = hide
    for o, (loc, sc, rot) in base_tf.items():
        o.location = turn @ (loc * scale) + Vector((0, 0, z)) + offset
        o.scale = sc * scale
        o.rotation_euler = rot.copy()
        o.rotation_euler.z += math.pi if face else 0.0


cam = ((-5.9, -9.3, 4.4), (0, 0, 1.85), 50, (1100, 1100))
set_creature()
pos1 = Vector((-2.7, -0.2, 3.2))  # на подлёте сбоку-сверху, не на линии камеры — морду не закрывает
aim(boom, pos1, Vector((0, 0, 1.3)) - pos1, spin=0.5)
d1 = (Vector((0, 0, 1.3)) - pos1).normalized()
t1 = fx_art("Fx_Throw", boom_core)
trail(t1, [pos1 - d1 * (0.9 + 0.22 * k) for k in range(6)], [0.075 * (1 - k / 7) for k in range(6)])
fx1 = build(t1)
only([boom, fx1] + cre)
bpy.context.view_layer.update()
shot(os.path.join(OUT, "capture_1_throw.png"), *cam)

top_z = cre_h + 0.75
place(boom_open, (0, 0, top_z), (0, 0, math.radians(-20)))
t2 = fx_art("Fx_Net", boom_core)
net_dome(t2, 1.9, 0.3, 0.02, top_z + 0.9, rings=7, lines=6)
fx2 = build(t2)
only([boom_open, fx2] + cre)
bpy.context.view_layer.update()
shot(os.path.join(OUT, "capture_2_net.png"), *cam)

set_creature(0.42, 0.22)
t3 = fx_art("Fx_Cube", boom_core)
net_cube(t3, 0.66, 0.12)
for k in range(5):
    s = 0.14 - 0.018 * k
    t3.box("net", -s, s, -s, s, 1.6 + 0.3 * k, 1.8 + 0.3 * k, bevel=0)
fx3 = build(t3)
place(boom_open, (0, 0, 3.25), (0, 0, math.radians(-20)))
only([boom_open, fx3] + cre)
bpy.context.view_layer.update()
shot(os.path.join(OUT, "capture_3_squeeze.png"), *cam)

set_creature(hide=True)
place(boom, (0, 0, 0), (0, 0, math.radians(-20)))
t4 = fx_art("Fx_Caught", boom_core)
sparks(t4, (0, 0, 0.8), 22, 0.6, 1.8, 0.06, 7, up=0.4)
fx4 = build(t4)
only([boom, fx4])
bpy.context.view_layer.update()
light = bpy.context.scene.objects[boom.name + "_Core"]
energy = light.data.energy
light.data.energy = energy * 3
shot(os.path.join(OUT, "capture_4_caught.png"), (-3.4, -5.4, 2.6), (0, 0, 0.8), 50, (1100, 1100))
light.data.energy = energy

set_creature()
place(boom, (1.8, -1.3, 0.5), (0, math.radians(90), math.radians(30)))
t5 = fx_art("Fx_Break", boom_core)
rnd = random.Random(11)
for _ in range(50):
    d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0, 1))).normalized()
    p = Vector((0, 0, 1.3)) + d * rnd.uniform(1.5, 2.7)
    s = rnd.uniform(0.05, 0.12)
    m = Matrix.Translation(p) @ Matrix.Rotation(rnd.uniform(0, 3), 4, Vector((rnd.random(), rnd.random(), 1)))
    t5.box("net", -s, s, -0.01, 0.01, -s, s, bevel=0, matrix=m)
fx5 = build(t5)
only([boom, fx5] + cre)
bpy.context.view_layer.update()
shot(os.path.join(OUT, "capture_5_escape.png"), *cam)
set_creature(hide=True)
for o in list(caps.values()) + list(opens.values()):
    place(o, (0, 0, 0))
for o in (fx1, fx2, fx3, fx4, fx5):
    o.hide_render = True
bpy.context.view_layer.update()


# 5. Масштаб: три манекена Roblox (5.2 стада), Ловибум на ладони вытянутой в сторону руки, и крупные планы.
def mannequin(name, x, turn, arm):
    """Блочный манекен Roblox; arm "side" — правая рука в сторону, "forward" — вперёд (как с инструментом)."""
    grey = bpy.data.materials.get("Mannequin") or bpy.data.materials.new("Mannequin")
    grey.use_nodes = True
    next(n for n in grey.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (
        *S.lin("8E98AC"), 1)
    root = bpy.data.objects.new(name + "Root", None)
    collection.objects.link(root)
    root.location = (x, 0, 0)
    root.rotation_euler = (0, 0, math.radians(turn))
    right = ((-2.15, 0, 3.6), (2.3, 0.95, 0.95)) if arm == "side" else ((-1.5, -0.66, 3.6), (0.95, 2.3, 0.95))
    blocks = (((0, 0, 4.65), (1.15, 1.15, 1.15)), ((0, 0, 3.2), (2.0, 1.0, 1.75)),
              ((1.5, 0, 3.2), (0.95, 0.95, 1.75)), right,
              ((-0.5, 0, 1.15), (0.95, 0.95, 2.3)), ((0.5, 0, 1.15), (0.95, 0.95, 2.3)))
    for center, size in blocks:
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=size, verts=bm.verts)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.05, segments=2, affect="EDGES")
        bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(grey)
        o = bpy.data.objects.new(name, me)
        collection.objects.link(o)
        o.parent = root
    palm = Vector((-2.85, 0, 4.075)) if arm == "side" else Vector((-1.5, -1.55, 4.075))
    return root, palm


dims = {n: S.bounds(o) for n, o in caps.items()}
roots = {}
for name, x in (("Boom", -5.6), ("Turbo", 1.0), ("Mega", 7.6)):
    root, palm = mannequin("Mannequin", x, -12, "side")
    obj = caps[name]
    lo, hi = dims[name]
    obj.parent = root
    obj.location = palm - Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    obj.rotation_euler = (0, 0, math.radians(-20))
    roots[name] = (root, palm)
bpy.context.view_layer.update()
only(list(caps.values()) + [o for o in bpy.context.scene.objects if o.name.startswith("Mannequin")])
shot(os.path.join(OUT, "hand_scale.png"), (-0.6, -27.0, 7.2), (0.4, 0, 2.9), 50, (2200, 1100))
for name, (root, palm) in roots.items():
    p = root.matrix_world @ palm
    shot(os.path.join(OUT, f"hand_{name}.png"), (p.x - 1.5, p.y - 5.4, p.z + 1.4), (p.x + 0.8, p.y, p.z + 0.35),
         50, (900, 900))
for obj in caps.values():
    obj.parent = None
    place(obj, (0, 0, 0))
bpy.context.view_layer.update()

# 6. Телефон: кадры 844 × 390 (логический размер экрана телефона в ландшафте), 1 : 1 — в руке, бросок, сеть.
PHONE = (844, 390)
_, hand = mannequin("PhoneMan", 0, 0, "forward")
man = [o for o in bpy.context.scene.objects if o.name.startswith("PhoneMan") and o.type == "MESH"]
for name, obj in caps.items():
    lo, hi = dims[name]
    place(obj, hand - Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)), (0, 0, math.radians(-30)))
    only([obj] + man)
    bpy.context.view_layer.update()
    shot(os.path.join(OUT, f"phone_hand_{name}.png"), (-5.4, 9.4, 7.2), (-1.1, -1.6, 3.1), 12, PHONE)
    place(obj, (0, 0, 0))

target = Vector((0, -8, 1.2))
phone_cam = ((0.9, 3.4, 4.6), (0, -8, 1.4), 17.8, PHONE)
set_creature(offset=Vector((0, -8, 0)), face=True)
for name, obj in caps.items():
    pos = Vector((1.35, -1.7, 3.35))
    d = (target - pos).normalized()
    aim(obj, pos, d, spin=0.6)
    tr = fx_art(f"PhoneTrail_{name}", TYPES[name]["core"])
    trail(tr, [pos - d * (0.95 + 0.26 * k) for k in range(5)], [0.065 * (1 - k / 6) for k in range(5)])
    fx = build(tr)
    only([obj, fx] + cre)
    bpy.context.view_layer.update()
    shot(os.path.join(OUT, f"phone_throw_{name}.png"), *phone_cam)
    fx.hide_render = True
    place(obj, (0, 0, 0))
for name, obj in opens.items():
    place(obj, (0, -8, cre_h + 0.75), (0, 0, math.radians(-20)))
    tn = fx_art(f"PhoneNet_{name}", TYPES[name]["core"])
    net_dome(tn, 1.9, 0.3, 0.02, cre_h + 1.65, rings=7, lines=6, w=0.028)
    fx = build(tn)
    fx.location = (0, -8, 0)
    only([obj, fx] + cre)
    bpy.context.view_layer.update()
    shot(os.path.join(OUT, f"phone_net_{name}.png"), *phone_cam)
    fx.hide_render = True
    place(obj, (0, 0, 0))

with open(os.path.join(OUT, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("LOVIBUMS_OK", flush=True)
