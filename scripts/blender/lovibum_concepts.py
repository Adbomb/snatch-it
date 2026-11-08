"""Концепты Ловибумов v3 (D55, этап 0): энергетические капсулы Бум, Турбо и Мега, стиль D39.

v3 — правки владельца к предварительно утверждённой v2 (2026-11-08): Бум круглее (мельче ступени торцов, шире срез
углов), боковые дуги Меги меньше на ~22 %, общий символ системы — светящийся ромб на тёмной плашке верхнего пояса со
всех сторон; проверка читаемости в руке и при броске в кадрах размера экрана телефона (844 × 390).

Первая версия (персонажи с глазами и зубами) владелец отклонил 2026-11-08: нужны устройства одной линейки, без лиц,
с понятной прогрессией. Эта версия — одна форма на всех: вертикальная капсула (квадрат со срезанными углами в сечении),
ступенчатые торцы, четыре угловые стойки держат светящееся энергетическое ядро, оно видно в четырёх окнах. Шва-экватора,
центральной кнопки и деления на половины нет. Прогрессия — от простого к премиальному:
- Бум (бонус ×1): оранжевые стойки, жёлтые торцы, бирюзовое ядро; без лишних деталей;
- Турбо (×1.5): синий корпус, светлые торцы с тёмными поясами, голубое ядро за решёткой, световые полосы на стойках,
  четыре небольших стабилизатора снизу, огоньки на верхнем торце;
- Мега (×2): фиолетовый корпус, золотые торцы и канты, кристаллическое ядро, две золотые дуги над капсулой с камнем.
Захват — энергетическая сеть: капсула зависает над существом, из окон уходят лучи, сеть из квадратных ячеек накрывает
существо, стягивается в куб света и уходит в ядро; при неудаче рассыпается на квадраты.

Только концепт на утверждение: рендеры EEVEE, без запекания, FBX и загрузок. Для свечения каждый главный кадр
рендерится второй раз (свет и небо выключены — видны только светящиеся детали): <кадр>_glow.png, листы
(scripts/d55_lovibum_sheets.py) размывают его и добавляют к кадру. 1 единица = 1 стад, z вверх, лицом в −y.
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
GLOW = {"core": 4.0, "glow": 3.0, "net": 3.0, "spark": 3.5, "crystal": 3.0, "dark": 1.2, "mark": 3.5}  # светящиеся ключи и сила свечения

TYPES = {
    "Boom": {"body": "FF8A1F", "cap": "FFC21A", "trim": "E8641A", "foot": "2A3344", "core": "2EE6D6",
             "glow": "8AFFF2", "scale": 1.0, "cut": 0.16, "round": True},
    "Turbo": {"body": "2F6BFF", "cap": "E6F3FF", "trim": "1E2B4F", "foot": "1E2B4F", "core": "3FD8FF",
              "glow": "5CE8FF", "scale": 1.05, "cut": 0.12, "round": False},
    "Mega": {"body": "7A2FE0", "cap": "F2C230", "trim": "C98E12", "foot": "C98E12", "core": "E57BFF",
             "glow": "FFD1FF", "scale": 1.1, "cut": 0.12, "round": False},
}


# ── Помощники ────────────────────────────────────────────────────────────────────────────────────────────────


def sq(h, cut):
    return S.octagon(-h, h, -h, h, cut)


def bar(a, key, p0, p1, w, h=None, bevel=S.BEVEL):
    """Брусок от точки p0 до p1 с сечением w × h."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    up = "Y" if abs(d.normalized().z) > 0.95 else "Z"
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("X", up).to_matrix().to_4x4()
    h = h or w
    a.box(key, -d.length / 2, d.length / 2, -w / 2, w / 2, -h / 2, h / 2, bevel=bevel, matrix=m)


def paint(a, spec):
    for key, code, rings in (("body", spec["body"], True), ("cap", spec["cap"], False), ("trim", spec["trim"], False),
                             ("foot", spec["foot"], False), ("core", spec["core"], False),
                             ("glow", spec["glow"], False), ("dark", "6A1FC0", False), ("gold", "F2C230", False),
                             ("golddark", "C98E12", False), ("crystal", spec["core"], False),
                             ("white", "FFFDF4", False), ("plate", "1C2030", False), ("mark", "FFF4C9", False)):
        a.paint(key, code, rings)


W, CUT, IN = 0.4, 0.12, 0.17  # полуширина стоек, срез углов, внутренний край стойки (окно — между ±IN)
ZB, ZT = 0.32, 1.12  # низ и верх стоек; торцы симметричны относительно середины (капсула-пилюля)


def column_pts(sx, sy, cut=CUT):
    """Угловая стойка: пятиугольник со срезанным внешним углом (как у торцов)."""
    base = [(IN, IN), (W, IN), (W, W - cut), (W - cut, W), (IN, W)]
    return [(sx * x, sy * y) for x, y in base]


def chamfer_strip(sx, sy, z0, z1, a, key, out=0.015):
    """Полоса на срезе угловой стойки (световая у Турбо, золотой кант у Меги)."""
    p, q = Vector((sx * (W - CUT), sy * W)), Vector((sx * W, sy * (W - CUT)))
    n = Vector((sx, sy)).normalized()
    p1, p2 = p + (q - p) * 0.28, p + (q - p) * 0.72
    pts = [tuple(p1 - n * 0.01), tuple(p2 - n * 0.01), tuple(p2 + n * out), tuple(p1 + n * out)]
    a.prism(key, pts, z0, z1, bevel=0)


STEP_ENDS = ((0.12, 0.035, 0.0, 0.07), (0.24, 0.07, 0.06, 0.15), (0.33, 0.1, 0.14, 0.24))
ROUND_ENDS = ((0.12, 0.045, 0.0, 0.06), (0.2, 0.075, 0.05, 0.11), (0.27, 0.1, 0.1, 0.16), (0.33, 0.125, 0.15, 0.21),
              (0.38, 0.145, 0.2, 0.26))  # Бум: ступени мельче, срез шире — торец ближе к куполу
TOP_BAND = (1.07, 1.21)  # верхний пояс выше нижнего (0.23…0.33): на нём символ-ромб


def ends(a, band, cap, emit, round_=False, band_cut=0.125):
    """Торцы-ступени сверху и снизу (зеркально): излучатель, ступени, пояс; верхний пояс выше — под символ."""
    steps = ROUND_ENDS if round_ else STEP_ENDS
    for flip in (False, True):
        for i, (h, cut, z0, z1) in enumerate(steps):
            if flip:
                z0, z1 = ZB + ZT - z1, ZB + ZT - z0
            a.prism(emit if i == 0 else cap, sq(h, cut), z0, z1)
    a.prism(band, sq(0.42, band_cut), 0.23 if not round_ else 0.25, 0.33)
    a.prism(band, sq(0.42, band_cut), *TOP_BAND)


def emblem(a, cut):
    """Символ системы Ловибумов — светящийся ромб на тёмной плашке, на верхнем поясе с четырёх сторон."""
    c = (TOP_BAND[0] + TOP_BAND[1]) / 2
    hz, hw = 0.062, 0.045  # полувысота и полуширина ромба (вытянут вверх — «кристалл»)
    for s in (-1, 1):
        a.box("plate", -0.09, 0.09, s * 0.415, s * 0.44, c - 0.068, c + 0.068)
        a.box("plate", s * 0.415, s * 0.44, -0.09, 0.09, c - 0.068, c + 0.068)
        a.prism("mark", [(0, c + hz), (hw, c), (0, c - hz), (-hw, c)], s * 0.435, s * 0.458, axis="y", bevel=0)
        a.prism("mark", [(c + hz, 0), (c, hw), (c - hz, 0), (c, -hw)], s * 0.435, s * 0.458, axis="x", bevel=0)


# ── Капсула: общая форма линейки ────────────────────────────────────────────────────────────────────────────


def capsule(name):
    spec = TYPES[name]
    a = S.Art("Lovibum_" + name, ring_z0=0.72)
    paint(a, spec)
    a.transform = Matrix.Scale(spec["scale"], 4)
    cut = spec["cut"]
    ends(a, "cap" if name == "Boom" else "trim", "cap", "glow" if name != "Mega" else "crystal", spec["round"],
         band_cut=0.155 if spec["round"] else 0.125)
    emblem(a, cut)
    # Ядро и четыре угловые стойки; окна — между стойками на каждой стороне.
    if name == "Mega":
        a.prism("dark", sq(0.22, 0.06), ZB + 0.01, ZT - 0.01)
        rot = Matrix.Rotation(math.radians(45), 4, "Z")
        a.frustum("crystal", (-0.03, 0.03, -0.03, 0.03), (-0.29, 0.29, -0.29, 0.29), 0.35, 0.73, matrix=rot)
        a.frustum("crystal", (-0.29, 0.29, -0.29, 0.29), (-0.03, 0.03, -0.03, 0.03), 0.72, 1.1, matrix=rot)
    else:
        a.prism("core", sq(0.3, 0.12 if spec["round"] else 0.09), ZB - 0.01, ZT + 0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            a.prism("body", column_pts(sx, sy, cut), ZB, ZT)
    if name == "Turbo":
        # Решётка в окнах: по две тёмные планки (вертикальные — без «экватора»).
        for k in (-0.07, 0.07):
            for s in (-1, 1):
                a.box("trim", k - 0.016, k + 0.016, s * 0.29, s * 0.37, ZB + 0.01, ZT - 0.01)
                a.box("trim", s * 0.29, s * 0.37, k - 0.016, k + 0.016, ZB + 0.01, ZT - 0.01)
        # Световые полосы на срезах стоек и огоньки на верхней ступени.
        for sx in (-1, 1):
            for sy in (-1, 1):
                chamfer_strip(sx, sy, 0.42, 1.02, a, "glow")
                a.box("glow", sx * 0.25 - 0.03, sx * 0.25 + 0.03, sy * 0.25 - 0.03, sy * 0.25 + 0.03, 1.29, 1.335)
        # Четыре стабилизатора снизу по диагоналям: тонкие пластины ступенькой, светящийся кончик.
        for sx in (-1, 1):
            for sy in (-1, 1):
                m = Matrix.Rotation(math.atan2(sy, sx), 4, "Z")
                a.box("trim", 0.3, 0.6, -0.025, 0.025, 0.01, 0.3, matrix=m)
                a.box("trim", 0.3, 0.5, -0.025, 0.025, 0.29, 0.44, matrix=m)
                a.box("glow", 0.58, 0.64, -0.03, 0.03, 0.02, 0.14, matrix=m)
    if name == "Mega":
        # Золотые канты на срезах стоек.
        for sx in (-1, 1):
            for sy in (-1, 1):
                chamfer_strip(sx, sy, 0.38, 1.06, a, "gold")
        # Золотые дуги по бокам: от нижнего пояса к верхнему, выгнуты наружу; накладки на концах, камень в середине.
        # v3: дуги меньше на ~22 % (выгиб 0.17 → 0.13, высота 0.6 → 0.47, толщина и кристалл тоньше).
        n = 6
        for s in (-1, 1):
            pts = [Vector((s * (0.43 + 0.13 * math.sin(math.pi * i / n)), 0, 0.485 + (0.955 - 0.485) * i / n))
                   for i in range(n + 1)]
            for i in range(n):
                w = 0.056 if i % 2 else 0.066  # соседние бруски разной толщины: без совпадающих граней
                bar(a, "gold", pts[i], pts[i + 1], w, w + 0.024)
            for z in (0.485, 0.955):
                a.box("golddark", s * 0.38, s * 0.46, -0.06, 0.06, z - 0.04, z + 0.04)
            a.frustum("crystal", (-0.04, 0.04, -0.04, 0.04), (0, 0, 0, 0), 0.0, 0.1,
                      matrix=Matrix.Translation((s * 0.585, 0, 0.72)) @ Matrix.Rotation(s * math.pi / 2, 4, "Y"))
    a.transform = None
    return a


# ── Эффекты захвата: сеть, куб, искры, осколки, след ────────────────────────────────────────────────────────


def fx_art(name, color):
    a = S.Art(name)
    a.paint("net", color)
    a.paint("spark", color)
    a.paint("white", "FFFFFF")
    return a


def net_tent(a, base, top, z0, z1, rings=5, lines=5, w=0.04):
    """Сеть-шатёр: квадратные кольца от основания base (полусторона на z0) до верха top (на z1) и линии по граням."""
    def ring(h, z):
        c = [Vector((-h, -h, z)), Vector((h, -h, z)), Vector((h, h, z)), Vector((-h, h, z))]
        for i in range(4):
            bar(a, "net", c[i], c[(i + 1) % 4], w, w, bevel=0)
    for i in range(rings + 1):
        t = i / rings
        ring(base + (top - base) * t, z0 + (z1 - z0) * t)
    for side in range(4):
        for j in range(lines + 1):
            s = -1 + 2 * j / lines
            def at(h, z):
                p = [(s * h, -h), (h, s * h), (-s * h, h), (-h, -s * h)][side]
                return Vector((p[0], p[1], z))
            bar(a, "net", at(base, z0), at(top, z1), w, w, bevel=0)


def net_dome(a, base, top, z0, z1, rings=6, lines=6, w=0.04):
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


def net_cube(a, h, z0, cells=4, w=0.045):
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


def core_light(obj, color, z, energy=12.0):
    """Свет ядра изнутри капсулы — подсвечивает стойки цветом ядра; следует за капсулой."""
    data = bpy.data.lights.new(obj.name + "_Core", "POINT")
    data.energy, data.color, data.shadow_soft_size = energy, S.rgb(color), 0.1
    light = bpy.data.objects.new(obj.name + "_Core", data)
    collection.objects.link(light)
    light.parent = obj
    light.location = (0, 0, z)
    return light


def creature():
    """Существо босса 3 из FBX с картой цвета (без подставки) — для кадров захвата; пустой список, если не вышло."""
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
        if o.name.endswith("_Stand") or "Stand" in o.name:
            o.hide_render = True
            o.name = "CreatureStand"
        else:
            o.name = "Creature_" + o.name
    return [o for o in objs if not o.name.startswith("CreatureStand")]


# ── Сцена ───────────────────────────────────────────────────────────────────────────────────────────────────

bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new("Lovibums")
bpy.context.scene.collection.children.link(collection)

report, caps = {}, {}
for name in TYPES:
    art = capsule(name)
    obj = build(art)
    lo, hi = S.bounds(obj)
    report[name] = {**art.stats, "size": [round(hi[i] - lo[i], 2) for i in range(3)]}
    caps[name] = obj
    core_light(obj, TYPES[name]["core"], 0.62 * TYPES[name]["scale"])
print("REPORT " + json.dumps(report, ensure_ascii=False), flush=True)

prev = S.Preview(collection)
world_bg = next(n for n in bpy.context.scene.world.node_tree.nodes if n.type == "BACKGROUND")


def only(objs):
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and o.name != "Floor":
            o.hide_render = o not in objs and not o.name.startswith("CreatureStand")
            if o.name.startswith("CreatureStand"):
                o.hide_render = True
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
    """Капсула верхом по направлению полёта (и поворот вокруг своей оси)."""
    q = Vector(direction).normalized().to_track_quat("Z", "Y")
    obj.rotation_mode = "QUATERNION"
    obj.location = loc
    obj.rotation_quaternion = q @ Matrix.Rotation(spin, 4, "Z").to_quaternion()


# 1. Повороты и крупный кадр каждой капсулы.
for name, obj in caps.items():
    only([obj])
    S.render_item(prev, obj, OUT)
    only([obj])
    lo, hi = S.bounds(obj)
    size, cz = max(hi - lo), (lo.z + hi.z) / 2
    dist = 2.7 * size + 1.0
    shot(os.path.join(OUT, f"{obj.name}_hero.png"), (-0.62 * dist, -0.85 * dist, cz + 0.55 * size),
         (0, 0, cz - 0.05 * size), 75, (1100, 1100))

# 2. Линейка: три рядом, слева направо по старшинству.
for name, x in (("Boom", -1.45), ("Turbo", 0.0), ("Mega", 1.55)):
    place(caps[name], (x, 0, 0), (0, 0, math.radians(-25)))
only(list(caps.values()))
bpy.context.view_layer.update()
shot(os.path.join(OUT, "lineup.png"), (-1.2, -6.4, 2.3), (0.05, 0, 0.72), 50, (2000, 1000))

# 3. В полёте: капсулы летят вправо-вниз верхом вперёд, за ними след из квадратных искр цвета ядра.
fly = []
for i, (name, x, z) in enumerate((("Boom", -3.3, 3.5), ("Turbo", 0.1, 2.25), ("Mega", 3.5, 1.0))):
    d = Vector((1, 0, -0.12)).normalized()
    aim(caps[name], Vector((x, 0, z)), d, spin=0.5 + 0.4 * i)
    t = fx_art(f"Trail_{name}", TYPES[name]["core"])
    path = [Vector((x, 0, z)) - d * (0.95 + 0.2 * k) + Vector((0, 0, 0.01 * k * k)) for k in range(7)]
    trail(t, path, [0.085 * (1 - k / 8) for k in range(7)])
    fly.append(build(t))
only(list(caps.values()) + fly)
bpy.context.view_layer.update()
shot(os.path.join(OUT, "flight.png"), (0.0, -14.5, 3.4), (0.0, 0, 2.25), 50, (2000, 1000))
for o in fly:
    o.hide_render = True

# 4. Захват энергетической сетью (Бум): бросок → сеть → сжатие → поймано; и «вырвалось».
cre = creature()
boom = caps["Boom"]
boom_core = TYPES["Boom"]["core"]
if cre:
    bpy.context.view_layer.update()
    lo = Vector((min(S.bounds(o)[0].x for o in cre), min(S.bounds(o)[0].y for o in cre),
                 min(S.bounds(o)[0].z for o in cre)))
    hi = Vector((max(S.bounds(o)[1].x for o in cre), max(S.bounds(o)[1].y for o in cre),
                 max(S.bounds(o)[1].z for o in cre)))
    for o in cre:
        if o.parent is None:
            o.location += Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
    cre_h = hi.z - lo.z
    print("CREATURE", len(cre), [round(v, 2) for v in (hi - lo)], flush=True)
else:
    cre_h = 2.6
cam = ((-5.2, -8.2, 3.9), (0, 0, 1.6), 50, (1100, 1100))
base_tf = {o: (o.location.copy(), o.scale.copy()) for o in cre if o.parent is None}


def set_creature(scale=1.0, z=0.0, hide=False):
    """Существо целиком: части FBX — верхние объекты (их и двигаем), масштаб относительно начала координат."""
    for o in cre:
        o.hide_render = hide
    for o, (loc, sc) in base_tf.items():
        o.location = loc * scale + Vector((0, 0, z))
        o.scale = sc * scale


# 4.1 Бросок: капсула летит к существу, след искр.
place(boom, (-1.6, -2.6, 2.4), (math.radians(20), math.radians(50), math.radians(-40)))
t1 = fx_art("Fx_Throw", boom_core)
trail(t1, [Vector((-2.2 - 0.36 * k, -3.3 - 0.42 * k, 2.25 - 0.08 * k)) for k in range(9)],
      [0.1 * (1 - k / 10) for k in range(9)])
fx1 = build(t1)
only([boom, fx1] + cre)
bpy.context.view_layer.update()
shot(os.path.join(OUT, "capture_1_throw.png"), *cam)
fx1.hide_render = True

# 4.2 Сеть: капсула зависла над существом, из окон — сеть-шатёр из квадратных ячеек до земли.
top_z = cre_h + 0.9
place(boom, (0, 0, top_z), (0, 0, math.radians(-20)))
t2 = fx_art("Fx_Net", boom_core)
net_dome(t2, 1.9, 0.36, 0.02, top_z + 0.05, rings=7, lines=6)
sparks(t2, (0, 0, top_z + 0.6), 10, 0.3, 0.9, 0.05, 3)
fx2 = build(t2)
only([boom, fx2] + cre)
bpy.context.view_layer.update()
shot(os.path.join(OUT, "capture_2_net.png"), *cam)
fx2.hide_render = True

# 4.3 Сжатие: сеть стянулась в куб света вокруг уменьшенного существа, луч в ядро капсулы.
set_creature(0.42, 0.25)
t3 = fx_art("Fx_Cube", boom_core)
net_cube(t3, 0.66, 0.12, cells=3, w=0.035)
for k in range(5):
    s = 0.16 - 0.02 * k
    a_z = 1.62 + 0.32 * k
    t3.box("net", -s, s, -s, s, a_z, a_z + 0.22, bevel=0)
fx3 = build(t3)
place(boom, (0, 0, 3.35), (0, 0, math.radians(-20)))
only([boom, fx3] + cre)
bpy.context.view_layer.update()
shot(os.path.join(OUT, "capture_3_squeeze.png"), *cam)
fx3.hide_render = True

# 4.4 Поймано: капсула на земле, ядро сияет, вокруг квадратные искры.
set_creature(1.0, 0.0, hide=True)
place(boom, (0, 0, 0), (0, 0, math.radians(-20)))
t4 = fx_art("Fx_Caught", boom_core)
sparks(t4, (0, 0, 0.8), 26, 0.6, 1.8, 0.07, 7, up=0.4)
fx4 = build(t4)
only([boom, fx4])
bpy.context.view_layer.update()
light = bpy.context.scene.objects[boom.name + "_Core"]
energy = light.data.energy
light.data.energy = energy * 3
shot(os.path.join(OUT, "capture_4_caught.png"), (-3.4, -5.4, 2.6), (0, 0, 0.8), 50, (1100, 1100))
light.data.energy = energy

# 4.5 Вырвалось: сеть рассыпалась на квадратные осколки, существо снова на месте, капсула упала рядом.
set_creature(1.0, 0.0)
place(boom, (1.8, -1.3, 0.42), (0, math.radians(90), math.radians(30)))
t5 = fx_art("Fx_Break", boom_core)
rnd = random.Random(11)
for _ in range(60):
    d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0, 1))).normalized()
    p = Vector((0, 0, 1.3)) + d * rnd.uniform(1.4, 2.6)
    s = rnd.uniform(0.06, 0.14)
    m = Matrix.Translation(p) @ Matrix.Rotation(rnd.uniform(0, 3), 4, Vector((rnd.random(), rnd.random(), 1)))
    t5.box("net", -s, s, -0.012, 0.012, -s, s, bevel=0, matrix=m)
fx5 = build(t5)
only([boom, fx5] + cre)
bpy.context.view_layer.update()
shot(os.path.join(OUT, "capture_5_escape.png"), *cam)
fx5.hide_render = True
set_creature(1.0, 0.0, hide=True)
for o in caps.values():
    place(o, (0, 0, 0))
bpy.context.view_layer.update()


# 5. Масштаб: три манекена Roblox (5.2 стада) с капсулой на ладони вытянутой в сторону руки и крупные планы.
def holder(x, turn):
    grey = bpy.data.materials.get("Mannequin") or bpy.data.materials.new("Mannequin")
    grey.use_nodes = True
    next(n for n in grey.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (
        *S.lin("8E98AC"), 1)
    root = bpy.data.objects.new("MannequinRoot", None)
    collection.objects.link(root)
    root.location = (x, 0, 0)
    root.rotation_euler = (0, 0, math.radians(turn))
    blocks = (((0, 0, 4.65), (1.15, 1.15, 1.15)), ((0, 0, 3.2), (2.0, 1.0, 1.75)),
              ((1.5, 0, 3.2), (0.95, 0.95, 1.75)), ((-2.15, 0, 3.6), (2.3, 0.95, 0.95)),
              ((-0.5, 0, 1.15), (0.95, 0.95, 2.3)), ((0.5, 0, 1.15), (0.95, 0.95, 2.3)))
    for center, size in blocks:
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=size, verts=bm.verts)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.05, segments=2, affect="EDGES")
        bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
        me = bpy.data.meshes.new("Mannequin")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(grey)
        o = bpy.data.objects.new("Mannequin", me)
        collection.objects.link(o)
        o.parent = root
    return root, Vector((-2.85, 0, 4.075))


roots = {}
for name, x in (("Boom", -5.6), ("Turbo", 1.0), ("Mega", 7.6)):
    root, palm = holder(x, -12)
    obj = caps[name]
    lo, hi = S.bounds(obj)
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



# 6. Телефон: кадры 844 × 390 (логический размер экрана телефона в ландшафте) — проверка читаемости.
def phone_man():
    """Манекен Roblox с правой рукой вперёд (как с инструментом); возвращает точку перед кулаком."""
    grey = bpy.data.materials.get("Mannequin")
    blocks = (((0, 0, 4.65), (1.15, 1.15, 1.15)), ((0, 0, 3.2), (2.0, 1.0, 1.75)),
              ((1.5, 0, 3.2), (0.95, 0.95, 1.75)), ((-1.5, -0.66, 3.6), (0.95, 2.3, 0.95)),
              ((-0.5, 0, 1.15), (0.95, 0.95, 2.3)), ((0.5, 0, 1.15), (0.95, 0.95, 2.3)))
    for center, size in blocks:
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=size, verts=bm.verts)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.05, segments=2, affect="EDGES")
        bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
        me = bpy.data.meshes.new("PhoneMan")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(grey)
        collection.objects.link(bpy.data.objects.new("PhoneMan", me))
    return Vector((-1.5, -1.55, 4.075))  # на ладони у кулака, поверх руки — не закрыта ею


hand = phone_man()
man = [o for o in bpy.context.scene.objects if o.name.startswith("PhoneMan")]
for obj in caps.values():
    obj.parent = None
    place(obj, (0, 0, 0))
bpy.context.view_layer.update()
dims = {n: S.bounds(o) for n, o in caps.items()}
PHONE = (844, 390)
for name, obj in caps.items():
    lo, hi = dims[name]
    place(obj, hand - Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)), (0, 0, math.radians(-30)))
    only([obj] + man)
    bpy.context.view_layer.update()
    shot(os.path.join(OUT, f"phone_hand_{name}.png"), (-5.4, 9.4, 7.2), (-1.1, -1.6, 3.1), 12, PHONE)

# Бросок: камера мини-игры за игроком, существо впереди, капсула на полпути со следом.
offset = Vector((0, -8, 0))
turn = Matrix.Rotation(math.pi, 4, "Z")  # существо лицом к игроку
for o, (loc, sc) in base_tf.items():
    o.location, o.scale = turn @ loc + offset, sc
    o.rotation_euler.z += math.pi
for o in cre:
    o.hide_render = False
target = Vector((0, -8, 1.2))
for name, obj in caps.items():
    pos = Vector((1.35, -1.7, 3.35))
    d = (target - pos).normalized()
    aim(obj, pos, d, spin=0.6)
    tr = fx_art(f"PhoneTrail_{name}", TYPES[name]["core"])
    trail(tr, [pos - d * (0.95 + 0.26 * k) for k in range(5)], [0.075 * (1 - k / 6) for k in range(5)])
    fx = build(tr)
    only([obj, fx] + cre)
    bpy.context.view_layer.update()
    shot(os.path.join(OUT, f"phone_throw_{name}.png"), (0.9, 3.4, 4.6), (0, -8, 1.4), 17.8, PHONE)
    fx.hide_render = True
for obj in caps.values():
    place(obj, (0, 0, 0))

with open(os.path.join(OUT, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("LOVIBUMS_OK", flush=True)
