"""Предпросмотр зоны без Roblox Studio: строит детали из JSON (scripts/lune/export_zone.luau) и рендерит виды в PNG.

Только для глаз разработчика и заказчика — в игру ничего не попадает. Детали: Block — куб, Wedge — клин (высокая
сторона на +Z детали, как в Roblox), Cylinder — цилиндр по оси X, Ball — шар. Рендер EEVEE, близкий к дню в игре
(Lighting: солнце ClockTime 13.5, голубое небо): Plastic — цвет детали × карта «квадратных пупырышков»
(assets/textures/lego_squares_color.png, 8 стадов на плитку, проекция по трём осям мира, как MaterialVariant D36),
SmoothPlastic — без карты, Neon — свечение, Glass — полупрозрачное; PointLight/SpotLight деталей — лампы того же
радиуса; надписи вывесок — как World/Signs (белый текст с тёмной обводкой цвета вывески, Arial Black вместо
Montserrat). Для масштаба на виды ставятся фигурки игрока (5 стадов, как R15). Оси Roblox (Y вверх) → Blender
(Z вверх): (x, y, z) → (x, −z, y).

Запуск:
  blender --background --factory-startup --python scripts/blender/preview_zone.py -- <zone.json> <папка> [виды.json]
Виды задаются в координатах зоны (x — поперёк коридора, y — вверх от пола, z — вдоль, вход на z = −47.5):
{"имя": {"eye": [x, y, z], "at": [x, y, z], "fov": 70, "ortho": 200}} — fov по вертикали (как FieldOfView в Roblox),
ortho — вид сверху без перспективы. Без файла — общие виды: entrance (камера игрока у входа), overview, top, boss,
back (от босса ко входу), lane_l / lane_r (камера игрока в проходах). Ключ --fast — Workbench вместо EEVEE.
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FAST = "--fast" in argv
argv = [a for a in argv if a != "--fast"]
SOURCE = argv[0] if argv else "zone.json"
OUT = argv[1] if len(argv) > 1 else "."
VIEWS = argv[2] if len(argv) > 2 else None
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STUDS = os.path.join(ROOT, "assets", "textures", "lego_squares_color.png")

P = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))  # Roblox → Blender

DEFAULT_VIEWS = {
    "entrance": {"eye": [0, 9, -60], "at": [0, 6, -5], "fov": 70},
    "overview": {"eye": [0, 42, -88], "at": [0, 0, 2], "fov": 60},
    "top": {"eye": [0, 300, 0.01], "at": [0, 0, 0], "ortho": 200},
    "boss": {"eye": [10, 9, -30], "at": [0, 8, -5], "fov": 70},
    "back": {"eye": [0, 14, 46], "at": [0, 4, -30], "fov": 70},
    "lane_l": {"eye": [-30, 9, -52], "at": [-38, 6, 10], "fov": 70},
    "lane_r": {"eye": [30, 9, -52], "at": [38, 6, 10], "fov": 70},
}
PLAYERS = [(6, -40), (-34, -30), (36, 6)]  # фигурки игрока для масштаба (x, z зоны)
SUN, AMBIENT, EXPOSURE = 6.5, 2.0, 0.7  # солнце, рассеянный свет, экспозиция: по снимку Studio (PREVIEW_* — свои)


def linear(c):
    """Цвет Roblox (sRGB) → линейный, как ждёт шейдер Blender."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def to_blender(v):
    return P @ Vector(v)


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def base_mesh(shape, cache={}):
    if shape in cache:
        return cache[shape]
    if shape == "Cylinder":
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.5, depth=1.0)
        obj = bpy.context.active_object
        obj.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))  # ось цилиндра — X, как в Roblox
        mesh = obj.data
        bpy.data.objects.remove(obj)
    elif shape == "Ball":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=14, radius=0.5)
        obj = bpy.context.active_object
        mesh = obj.data
        bpy.data.objects.remove(obj)
    elif shape == "Wedge":
        # Вершины в осях Roblox: низ целиком, задняя грань (+Z) целиком, скат от верха сзади к низу спереди.
        verts_r = [(-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (-0.5, -0.5, 0.5),
                   (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5)]
        verts = verts_r
        faces = [(0, 1, 2, 3), (3, 2, 5, 4), (0, 4, 5, 1), (0, 3, 4), (1, 5, 2)]
        mesh = bpy.data.meshes.new("Wedge")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        # Нормали наружу независимо от порядка обхода.
        import bmesh

        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        cache[shape] = mesh
        return mesh
    else:
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        obj = bpy.context.active_object
        mesh = obj.data
        bpy.data.objects.remove(obj)
    # Меши куба, цилиндра и шара создаются в осях Blender; переводим в оси Roblox (матрица детали задаётся в них).
    mesh.transform(P.transposed().to_4x4())
    cache[shape] = mesh
    return mesh


def node(tree, kind, **props):
    n = tree.nodes.new(kind)
    for k, v in props.items():
        setattr(n, k, v)
    return n


def plastic_material(studs_image):
    """Цвет детали × карта пупырышков по трём осям мира + рельеф из той же карты."""
    mat = bpy.data.materials.new("Plastic")
    mat.use_nodes = True
    t = mat.node_tree
    t.nodes.clear()
    out = node(t, "ShaderNodeOutputMaterial")
    bsdf = node(t, "ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.55
    info = node(t, "ShaderNodeObjectInfo")
    geo = node(t, "ShaderNodeNewGeometry")
    scale = node(t, "ShaderNodeVectorMath", operation="SCALE")
    scale.inputs[3].default_value = 1 / 8  # 8 стадов на плитку (Config/Textures)
    t.links.new(geo.outputs["Position"], scale.inputs[0])
    sep = node(t, "ShaderNodeSeparateXYZ")
    t.links.new(scale.outputs[0], sep.inputs[0])
    absn = node(t, "ShaderNodeVectorMath", operation="ABSOLUTE")
    t.links.new(geo.outputs["Normal"], absn.inputs[0])
    nsep = node(t, "ShaderNodeSeparateXYZ")
    t.links.new(absn.outputs[0], nsep.inputs[0])
    axes = {"X": ("Y", "Z"), "Y": ("X", "Z"), "Z": ("X", "Y")}
    weighted = []
    weights = []
    for axis, (u, v) in axes.items():
        comb = node(t, "ShaderNodeCombineXYZ")
        t.links.new(sep.outputs[u], comb.inputs[0])
        t.links.new(sep.outputs[v], comb.inputs[1])
        tex = node(t, "ShaderNodeTexImage", image=studs_image, interpolation="Linear")
        t.links.new(comb.outputs[0], tex.inputs[0])
        pw = node(t, "ShaderNodeMath", operation="POWER")
        pw.inputs[1].default_value = 8
        t.links.new(nsep.outputs[axis], pw.inputs[0])
        weights.append(pw)
        weighted.append((tex, pw))
    total = node(t, "ShaderNodeMath", operation="ADD")
    t.links.new(weights[0].outputs[0], total.inputs[0])
    t.links.new(weights[1].outputs[0], total.inputs[1])
    total2 = node(t, "ShaderNodeMath", operation="ADD")
    t.links.new(total.outputs[0], total2.inputs[0])
    t.links.new(weights[2].outputs[0], total2.inputs[1])
    acc = None
    for tex, pw in weighted:
        w = node(t, "ShaderNodeMath", operation="DIVIDE")
        t.links.new(pw.outputs[0], w.inputs[0])
        t.links.new(total2.outputs[0], w.inputs[1])
        sc = node(t, "ShaderNodeVectorMath", operation="SCALE")
        t.links.new(tex.outputs["Color"], sc.inputs[0])
        t.links.new(w.outputs[0], sc.inputs[3])
        if acc is None:
            acc = sc
        else:
            add = node(t, "ShaderNodeVectorMath", operation="ADD")
            t.links.new(acc.outputs[0], add.inputs[0])
            t.links.new(sc.outputs[0], add.inputs[1])
            acc = add
    mul = node(t, "ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY")
    mul.inputs["Factor"].default_value = 1.0
    t.links.new(info.outputs["Color"], mul.inputs[6])
    t.links.new(acc.outputs[0], mul.inputs[7])
    t.links.new(mul.outputs[2], bsdf.inputs["Base Color"])
    bump = node(t, "ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.03
    gray = node(t, "ShaderNodeRGBToBW")
    t.links.new(acc.outputs[0], gray.inputs[0])
    t.links.new(gray.outputs[0], bump.inputs["Height"])
    t.links.new(bump.outputs[0], bsdf.inputs["Normal"])
    t.links.new(bsdf.outputs[0], out.inputs[0])
    return mat


def simple_material(name, roughness=0.5, emission=0.0, alpha=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    t = mat.node_tree
    bsdf = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    info = node(t, "ShaderNodeObjectInfo")
    t.links.new(info.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = roughness
    if emission > 0:
        t.links.new(info.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = emission
    if alpha < 1:
        # Непрозрачность — из альфы цвета объекта (1 − Transparency детали), alpha — если её нет.
        bsdf.inputs["Alpha"].default_value = alpha
        t.links.new(info.outputs["Alpha"], bsdf.inputs["Alpha"])
        for attr, value in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
            try:
                setattr(mat, attr, value)
            except (AttributeError, TypeError):
                pass
    return mat


def set_material(obj, mat):
    """Материал на объект, а не на общий меш (у деталей одной формы меш один)."""
    if len(obj.data.materials) == 0:
        obj.data.materials.append(None)
    obj.material_slots[0].link = "OBJECT"
    obj.material_slots[0].material = mat


def build(data):
    mats = {}
    if not FAST:
        studs = bpy.data.images.load(STUDS)
        studs.colorspace_settings.name = "sRGB"
        mats["Plastic"] = plastic_material(studs)
        mats["SmoothPlastic"] = simple_material("Smooth", 0.45)
        mats["Neon"] = simple_material("Neon", 0.4, emission=2.2)
        mats["Glass"] = simple_material("Glass", 0.05, alpha=0.3)
    for i, b in enumerate(data["bricks"]):
        glass = b["mat"] == "Glass" or b["t"] > 0.4
        if FAST and glass:
            continue
        shape = b["shape"] if b["shape"] in ("Cylinder", "Ball", "Wedge") else "Block"
        obj = bpy.data.objects.new(f"b{i}", base_mesh(shape))
        bpy.context.scene.collection.objects.link(obj)
        cf = b["cf"]
        rot = Matrix(((cf[3], cf[4], cf[5]), (cf[6], cf[7], cf[8]), (cf[9], cf[10], cf[11])))
        # Меш в осях Roblox: масштаб и поворот детали, затем перевод в оси Blender.
        basis = P @ rot @ Matrix.Diagonal(Vector(b["s"]))
        obj.matrix_world = Matrix.Translation(to_blender(cf[0:3])) @ basis.to_4x4()
        bright = 1.25 if (FAST and b["mat"] == "Neon") else 1.0
        color = [linear(min(1.0, ch * bright)) for ch in b["c"]]
        obj.color = (color[0], color[1], color[2], 1.0 - b["t"] if glass else 1.0)
        if not FAST:
            kind = "Glass" if glass else (b["mat"] if b["mat"] in mats else "Plastic")
            set_material(obj, mats[kind])
            light = b.get("light")
            if light:
                add_light(light, cf, rot)
    add_signs(data)


# Грань детали → (нормаль, направление «вправо» для читающего) в осях Roblox, как у SurfaceGui.
FACES = {
    "Front": ((0, 0, -1), (-1, 0, 0)),
    "Back": ((0, 0, 1), (1, 0, 0)),
    "Left": ((-1, 0, 0), (0, 0, 1)),
    "Right": ((1, 0, 0), (0, 0, -1)),
}
FONTS = ["C:/Windows/Fonts/ariblk.ttf", "C:/Windows/Fonts/arialbd.ttf"]


def add_signs(data):
    """Надписи вывесок (World/Signs): белый текст с тёмной обводкой цвета вывески, 94 % ширины и 80 % высоты грани."""
    signs = data.get("signs") or []
    if not signs:
        return
    bricks = {b["name"]: b for b in data["bricks"] if b.get("name")}
    font = None
    for path in FONTS:
        if os.path.exists(path):
            font = bpy.data.fonts.load(path)
            break
    white = simple_material("SignText", 0.5, emission=1.0) if not FAST else None
    dark = simple_material("SignStroke", 0.6) if not FAST else None
    for sign in signs:
        b = bricks.get(sign["name"])
        if not b:
            continue
        cf, size = b["cf"], Vector(b["s"])
        rot = Matrix(((cf[3], cf[4], cf[5]), (cf[6], cf[7], cf[8]), (cf[9], cf[10], cf[11])))
        tint = [c * 0.35 for c in b["c"]]
        for face in sign["faces"]:
            if face not in FACES:
                continue
            normal, right = Vector(FACES[face][0]), Vector(FACES[face][1])
            depth = abs(normal.dot(size)) / 2
            width, height = abs(right.dot(size)), size[1]
            n, r, up = rot @ normal, rot @ right, rot @ Vector((0, 1, 0))
            center = Vector(cf[0:3]) + n * depth
            scale = None
            for color, offset, push, mat in ((tint, 0.07, 0.015, dark), ((1, 1, 1), 0, 0.03, white)):
                curve = bpy.data.curves.new("sign", "FONT")
                curve.body = sign["text"]
                if font:
                    curve.font = font
                curve.align_x = "CENTER"
                curve.align_y = "CENTER"
                curve.offset = offset
                obj = bpy.data.objects.new("sign", curve)
                bpy.context.scene.collection.objects.link(obj)
                if scale is None:
                    bpy.context.view_layer.update()
                    dims = obj.dimensions
                    scale = min(0.94 * width / max(dims.x, 1e-3), 0.8 * height / max(dims.y, 1e-3))
                basis = Matrix((r, up, n)).transposed() * scale
                obj.matrix_world = Matrix.Translation(to_blender(center + n * push)) @ (P @ basis).to_4x4()
                obj.color = (*[linear(c) for c in color], 1.0)
                if mat:
                    obj.data.materials.append(mat)


def add_light(light, cf, rot):
    radius = light["range"]
    color = light["color"]
    if light.get("angle"):
        data = bpy.data.lights.new("spot", "SPOT")
        data.spot_size = math.radians(light["angle"])
        data.spot_blend = 0.4
        data.energy = 6 * light["brightness"] * radius * radius
    else:
        data = bpy.data.lights.new("point", "POINT")
        data.energy = 3 * light["brightness"] * radius * radius
    data.color = color
    data.shadow_soft_size = 0.5
    for attr, value in (("use_custom_distance", True), ("cutoff_distance", radius)):
        try:
            setattr(data, attr, value)
        except AttributeError:
            pass
    obj = bpy.data.objects.new("light", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = to_blender(cf[0:3])
    look = P @ (rot @ Vector((0, 0, -1)))  # Front детали (−Z) — туда светит SpotLight
    obj.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()


def add_players(local):
    """Фигурки игрока 5 стадов (ноги, тело, руки, голова) для масштаба."""
    mat = simple_material("Player", 0.5) if not FAST else None
    parts = [
        ((0.9, 2, 0.9), (-0.5, 1, 0), (0.25, 0.35, 0.7)),
        ((0.9, 2, 0.9), (0.5, 1, 0), (0.25, 0.35, 0.7)),
        ((2, 2, 1), (0, 3, 0), (0.95, 0.75, 0.2)),
        ((0.9, 2, 0.9), (-1.45, 3, 0), (0.98, 0.84, 0.66)),
        ((0.9, 2, 0.9), (1.45, 3, 0), (0.98, 0.84, 0.66)),
        ((1.2, 1.2, 1.2), (0, 4.6, 0), (0.98, 0.84, 0.66)),
    ]
    for x, z in PLAYERS:
        for size, offset, color in parts:
            obj = bpy.data.objects.new("player", base_mesh("Block"))
            bpy.context.scene.collection.objects.link(obj)
            world = local(x + offset[0], offset[1], z + offset[2])
            obj.matrix_world = Matrix.Translation(to_blender(world)) @ (P @ Matrix.Diagonal(Vector(size))).to_4x4()
            obj.color = (*[linear(c) for c in color], 1.0)
            if mat:
                set_material(obj, mat)


def setup_render(scene):
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new("sky")
    scene.view_settings.view_transform = "Standard"
    if FAST:
        scene.render.engine = "BLENDER_WORKBENCH"
        shading = scene.display.shading
        shading.light = "STUDIO"
        shading.color_type = "OBJECT"
        shading.show_shadows = True
        shading.shadow_intensity = 0.35
        shading.show_cavity = True
        shading.cavity_type = "WORLD"
        shading.show_object_outline = True
        shading.object_outline_color = (0.08, 0.08, 0.1)
        scene.display.light_direction = (0.35, -0.45, 0.82)
        scene.world.color = (0.62, 0.8, 0.95)
        return
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    eevee = scene.eevee
    for attr, value in (("taa_render_samples", 48), ("use_shadows", True), ("use_raytracing", True),
                        ("use_gtao", True), ("gtao_distance", 1.5)):
        try:
            setattr(eevee, attr, value)
        except AttributeError:
            pass
    # Свет подогнан по снимку Studio 2026-11-04 (Lighting: Brightness 3, ClockTime 13.5): плита D9C8A5 там почти белая.
    # Камера видит голубое небо, освещает же нейтральный рассеянный свет (как OutdoorAmbient) — без синевы на полу.
    scene.view_settings.exposure = float(os.environ.get("PREVIEW_EXPOSURE", EXPOSURE))
    scene.world.use_nodes = True
    tree = scene.world.node_tree
    bg = next(n for n in tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.42, 0.62, 0.92, 1)
    bg.inputs["Strength"].default_value = 0.9
    ambient = tree.nodes.new("ShaderNodeBackground")
    ambient.inputs["Color"].default_value = (0.62, 0.62, 0.66, 1)
    ambient.inputs["Strength"].default_value = float(os.environ.get("PREVIEW_AMBIENT", AMBIENT))
    path = tree.nodes.new("ShaderNodeLightPath")
    mix = tree.nodes.new("ShaderNodeMixShader")
    out = next(n for n in tree.nodes if n.type == "OUTPUT_WORLD")
    tree.links.new(path.outputs["Is Camera Ray"], mix.inputs[0])
    tree.links.new(ambient.outputs[0], mix.inputs[1])
    tree.links.new(bg.outputs[0], mix.inputs[2])
    tree.links.new(mix.outputs[0], out.inputs["Surface"])
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = float(os.environ.get("PREVIEW_SUN", SUN))
    sun.angle = math.radians(6)
    sun.color = (1.0, 0.97, 0.9)
    obj = bpy.data.objects.new("sun", sun)
    scene.collection.objects.link(obj)
    obj.rotation_euler = Vector((0.35, -0.55, -0.9)).to_track_quat("Z", "Y").to_euler()


def camera(scene, name, eye, at, fov=70, ortho=None):
    cam = bpy.data.cameras.new(name)
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    else:
        cam.sensor_fit = "VERTICAL"
        cam.angle_y = math.radians(fov)
    cam.clip_start = 0.3
    cam.clip_end = 2000
    obj = bpy.data.objects.new(name, cam)
    scene.collection.objects.link(obj)
    obj.location = to_blender(eye)
    direction = to_blender(at) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = obj
    return obj


def main():
    with open(SOURCE, encoding="utf-8") as f:
        data = json.load(f)
    views = DEFAULT_VIEWS
    if VIEWS:
        with open(VIEWS, encoding="utf-8") as f:
            views = json.load(f)
    clear()
    scene = bpy.context.scene
    build(data)
    cx, cy, cz = data["center"]

    # Координаты зоны → мир Roblox: +X зоны = −X мира, +Z зоны = −Z мира (вход зоны — на +Z мира).
    def local(x, y, z):
        return (cx - x, cy + y, cz - z)

    add_players(local)
    setup_render(scene)
    os.makedirs(OUT, exist_ok=True)
    for name, view in views.items():
        cam = camera(scene, name, local(*view["eye"]), local(*view["at"]), view.get("fov", 70), view.get("ortho"))
        overlay = draw_labels(scene, cam, data.get("labels") or [], view.get("labels"))
        scene.render.filepath = os.path.join(OUT, f"zone{data['zone']}_{name}.png")
        bpy.ops.render.render(write_still=True)
        print("written", scene.render.filepath)
        for obj in overlay:
            bpy.data.objects.remove(obj)


# Подписи над предметами (BillboardGui): постоянный размер на экране. mode "old" — прежние 200 × 36 px с одним
# названием, без раскладки; "new" — D45 (UITokens.ItemLabel): ширина по названию, две строки, масштаб по высоте
# экрана и подъём дальних над ближними. Числа и расчёт — как в UITokens.ItemLabel и Shared/LabelLayout.
LABEL = {"height": 46, "gap": 4, "stack": 4, "screen": 720, "scale": (0.6, 1.1), "share": 0.62, "distance": 60}


def label_layout(entries, gap, max_lift):
    """Тот же расчёт, что Shared/LabelLayout.Place: подъём каждой подписи (px вверх)."""
    order = sorted(range(len(entries)), key=lambda i: entries[i]["depth"])
    placed, lifts = [], [0.0] * len(entries)
    for i in order:
        e = entries[i]
        lift = 0.0
        for _ in range(len(placed) + 1):
            moved = False
            for p in placed:
                top, bottom = e["y"] - e["h"] / 2 - lift, e["y"] + e["h"] / 2 - lift
                apart = abs(e["x"] - p["x"]) >= (e["w"] + p["w"]) / 2 + gap
                if not apart and bottom > p["top"] - gap and top < p["bottom"] + gap:
                    lift = e["y"] + e["h"] / 2 - (p["top"] - gap)
                    moved = True
            if not moved:
                break
        lift = min(lift, max_lift)
        lifts[i] = lift
        placed.append({"x": e["x"], "w": e["w"], "top": e["y"] - e["h"] / 2 - lift, "bottom": e["y"] + e["h"] / 2 - lift})
    return lifts


LABEL_MATS = {}


def overlay_text(cam, text, color, x, y, w, h, objects):
    """Текст с тёмной обводкой, вписанный в прямоугольник экрана (центр x, y, размер w × h, px), перед камерой."""
    scene = bpy.context.scene
    width_px, height_px = scene.render.resolution_x, scene.render.resolution_y
    depth = 1.0
    visible = 2 * depth * math.tan(cam.data.angle_y / 2)
    per_px = visible / height_px
    if not LABEL_MATS:
        LABEL_MATS["fill"] = simple_material("LabelFill", 0.5, emission=1.0)
        LABEL_MATS["stroke"] = simple_material("LabelStroke", 0.6)
    mats = LABEL_MATS
    scale = None
    for kind, offset, push, tint in (("stroke", 0.09, 0.0, (0.1, 0.08, 0.19)), ("fill", 0, 0.001, color)):
        curve = bpy.data.curves.new("label", "FONT")
        curve.body = text
        for path in FONTS:
            if os.path.exists(path):
                curve.font = bpy.data.fonts.load(path, check_existing=True)
                break
        curve.align_x = "CENTER"
        curve.align_y = "CENTER"
        curve.offset = offset
        obj = bpy.data.objects.new("label", curve)
        bpy.context.scene.collection.objects.link(obj)
        if scale is None:
            bpy.context.view_layer.update()
            dims = obj.dimensions
            scale = min(0.94 * w * per_px / max(dims.x, 1e-4), 0.8 * h * per_px / max(dims.y, 1e-4))
        obj.parent = cam
        obj.location = ((x - width_px / 2) * per_px, -(y - height_px / 2) * per_px, -depth + push)
        obj.scale = (scale, scale, scale)
        obj.color = (*[linear(c) for c in tint], 1.0)
        obj.data.materials.append(mats[kind])
        objects.append(obj)


def draw_labels(scene, cam, labels, mode):
    if not mode or not labels:
        return []
    from bpy_extras.object_utils import world_to_camera_view

    bpy.context.view_layer.update()
    width_px, height_px = scene.render.resolution_x, scene.render.resolution_y
    scale = min(max(height_px / LABEL["screen"], LABEL["scale"][0]), LABEL["scale"][1])
    entries = []
    for lab in labels:
        co = world_to_camera_view(scene, cam, to_blender(lab["anchor"]))
        if co.z <= 0 or co.z > LABEL["distance"] or not (0 < co.x < 1 and 0 < co.y < 1):
            continue
        if mode == "old":
            w, h = 200, 36
        else:
            w, h = lab["width"] * scale, LABEL["height"] * scale
        entries.append({"x": co.x * width_px, "y": (1 - co.y) * height_px, "w": w, "h": h, "depth": co.z, "lab": lab})
    if mode == "new":
        lifts = label_layout(entries, LABEL["gap"] * scale, LABEL["stack"] * LABEL["height"] * scale)
    else:
        lifts = [0] * len(entries)
    objects = []
    for e, lift in zip(entries, lifts):
        y = e["y"] - lift
        if mode == "old":
            overlay_text(cam, e["lab"]["name"], e["lab"]["color"], e["x"], y, e["w"], e["h"], objects)
        else:
            share = LABEL["share"]
            name_h, info_h = e["h"] * share, e["h"] * (1 - share)
            top = y - e["h"] / 2
            overlay_text(cam, e["lab"]["name"], e["lab"]["color"], e["x"], top + name_h / 2, e["w"], name_h, objects)
            info_y = top + name_h + info_h / 2
            overlay_text(cam, e["lab"]["info"], (1, 1, 1), e["x"], info_y, e["w"], info_h, objects)
    return objects


main()
