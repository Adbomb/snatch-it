"""D48, этап A — пять эталонных иконок HUD (рюкзак, щит, рука силы, монета, доход) в стиле D39.

Только PNG для утверждения: в Roblox ничего не загружается. Одна камера (вид 3/4 сверху, узкий объектив), один свет
(ключ слева сверху, заполняющий справа, контровой сзади), прозрачный фон; модели — блоки с острыми рёбрами и тонкой
фаской, силуэт ступенями, чистые яркие цвета, крупные грани — с редкими кольцами-квадратами D39. Контур и тень
добавляет scripts/d48_icon_sheet.py (одинаковая толщина для всех иконок).

Запуск: blender --background --factory-startup --python scripts/blender/d48_icons.py -- <репо>
Пишет assets/concepts/d48/icons/raw_<имя>.png (1024², прозрачный фон) и icons.blend.
"""

import glob
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
REPO = os.path.abspath(argv[0]) if argv else os.getcwd()
OUT = os.path.join(REPO, "assets", "concepts", "d48", "icons")
os.makedirs(OUT, exist_ok=True)
RES = 1024
BEVEL = 0.025


def lin(code):
    rgb = [int(code[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
try:
    scene.eevee.use_raytracing = True
    scene.eevee.taa_render_samples = 64
except AttributeError:
    pass
scene.view_settings.view_transform = "Standard"
scene.render.film_transparent = True
scene.render.resolution_x = scene.render.resolution_y = RES
world = bpy.data.worlds.new("Icons")
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (*lin("DCE9FF"), 1)
bg.inputs["Strength"].default_value = 0.35
scene.world = world

MATS = {}


def _math(nt, op, a, b=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            nt.links.new(x, n.inputs[i])
    return n.outputs[0]


def mat(code, rough=0.45, metal=0.0, emit=0.0, rings=None):
    """Цвет; rings = шаг колец D39 (в единицах иконки) — только для крупных граней."""
    key = f"{code}_{rough}_{metal}_{emit}_{rings}"
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*lin(code), 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*lin(code), 1)
        b.inputs["Emission Strength"].default_value = emit
    if rings:
        step, size, rad, width = rings, rings * 0.7, rings * 0.17, rings * 0.06
        p = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(nt.nodes.new("ShaderNodeTexCoord").outputs["Object"], p.inputs["Vector"])
        n = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(nt.nodes.new("ShaderNodeNewGeometry").outputs["True Normal"], n.inputs["Vector"])
        px, py, pz = p.outputs["X"], p.outputs["Y"], p.outputs["Z"]
        nx, ny, nz = n.outputs["X"], n.outputs["Y"], n.outputs["Z"]
        top = _math(nt, "GREATER_THAN", _math(nt, "ABSOLUTE", nz), 0.7)
        fl = _math(nt, "MAXIMUM", _math(nt, "SQRT", _math(nt, "ADD", _math(nt, "MULTIPLY", nx, nx),
                                                        _math(nt, "MULTIPLY", ny, ny))), 0.01)
        along = _math(nt, "DIVIDE", _math(nt, "SUBTRACT", _math(nt, "MULTIPLY", py, nx),
                                          _math(nt, "MULTIPLY", px, ny)), fl)
        u = _math(nt, "ADD", along, _math(nt, "MULTIPLY", top, _math(nt, "SUBTRACT", px, along)))
        v = _math(nt, "ADD", pz, _math(nt, "MULTIPLY", top, _math(nt, "SUBTRACT", py, pz)))
        inner = size / 2 - rad
        d2 = None
        for coord in (u, v):
            frac = _math(nt, "FRACT", _math(nt, "DIVIDE", _math(nt, "ADD", coord, step / 2), step))
            q = _math(nt, "ABSOLUTE", _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", frac, 0.5), step))
            a = _math(nt, "MAXIMUM", _math(nt, "SUBTRACT", q, inner), 0.0)
            sq = _math(nt, "MULTIPLY", a, a)
            d2 = sq if d2 is None else _math(nt, "ADD", d2, sq)
        dist = _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", _math(nt, "SQRT", d2), rad))
        g = nt.nodes.new("ShaderNodeMapRange")
        g.interpolation_type = "SMOOTHSTEP"
        nt.links.new(dist, g.inputs["Value"])
        g.inputs["From Min"].default_value, g.inputs["From Max"].default_value = width / 2, 0.0
        shade = nt.nodes.new("ShaderNodeMixRGB")
        shade.blend_type = "MULTIPLY"
        shade.inputs["Fac"].default_value = 1.0
        shade.inputs["Color1"].default_value = (*lin(code), 1)
        nt.links.new(_math(nt, "SUBTRACT", 1.0, _math(nt, "MULTIPLY", g.outputs["Result"], 0.18)),
                     shade.inputs["Color2"])
        nt.links.new(shade.outputs["Color"], b.inputs["Base Color"])
    MATS[key] = m
    return m


ICONS = {}


def coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        scene.collection.children.link(c)
        ICONS[name] = c
    return c


def box(icon, x0, x1, y0, y1, z0, z1, m, bevel=BEVEL, rot=None, pivot=(0, 0, 0)):
    """Брусок в осях иконки: x — вправо, y — вглубь (лицо к −y), z — вверх."""
    sx, sy, sz = abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    b = min(bevel, sx / 3, sy / 3, sz / 3)
    if b > 0.002:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=b, segments=1, affect="EDGES")
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    if rot:
        bmesh.ops.rotate(bm, verts=bm.verts, cent=pivot, matrix=rot)
    me = bpy.data.meshes.new(icon)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    obj = bpy.data.objects.new(icon, me)
    coll(icon).objects.link(obj)
    return obj


def disc(icon, cx, cy, cz, radius, depth, m, segments=16, axis="Y", bevel=BEVEL):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius, radius2=radius,
                          depth=depth)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(180 / segments), 3, "Z"))
    bmesh.ops.bevel(bm, geom=[e for e in bm.edges if len(e.link_faces) == 2 and
                              abs(e.link_faces[0].normal.dot(e.link_faces[1].normal)) < 0.5],
                    offset=bevel, segments=1, affect="EDGES")
    if axis == "Y":  # лицом к камере (−y)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"))
    bmesh.ops.translate(bm, vec=(cx, cy, cz), verts=bm.verts)
    me = bpy.data.meshes.new(icon)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    obj = bpy.data.objects.new(icon, me)
    coll(icon).objects.link(obj)
    return obj


def glyph(icon, body, cx, cy, cz, size, depth, m):
    font = None
    for p in sorted(glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Roblox\Versions\*\content\fonts\Montserrat-Black.ttf"))):
        font = p
    cu = bpy.data.curves.new(icon + "_t", "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = depth
    cu.bevel_depth = 0.01
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    if font:
        cu.font = bpy.data.fonts.load(font, check_existing=True)
    obj = bpy.data.objects.new(icon + "_t", cu)
    obj.data.materials.append(m)
    obj.location = (cx, cy, cz)
    obj.rotation_euler = (math.radians(90), 0, 0)
    coll(icon).objects.link(obj)
    return obj


# ── 1. Рюкзак (инвентарь): оранжевый корпус, тёмный клапан, карман, золотые пряжки, ручка ──────────────────────────
ORANGE, ORANGE_D, ORANGE_L = "F38B22", "C8611A", "FFAE45"
GOLD, GOLD_D = "F2C230", "C9921B"
box("backpack", -0.72, 0.72, -0.42, 0.42, -0.9, 0.62, mat(ORANGE, 0.5, rings=0.36))
box("backpack", -0.6, 0.6, -0.36, 0.36, 0.62, 0.78, mat(ORANGE, 0.5))  # плечо крышки ступенью
box("backpack", -0.76, 0.76, -0.47, 0.1, 0.18, 0.86, mat(ORANGE_D, 0.5))  # клапан
box("backpack", -0.58, 0.58, -0.56, -0.38, -0.78, -0.08, mat(ORANGE_L, 0.5))  # передний карман
box("backpack", -0.48, 0.48, -0.6, -0.5, -0.22, -0.14, mat(ORANGE_D, 0.5))  # шов кармана
for sx in (-0.38, 0.38):  # ремешки клапана с пряжками
    box("backpack", sx - 0.09, sx + 0.09, -0.52, -0.44, -0.1, 0.62, mat(ORANGE_D, 0.5))
    box("backpack", sx - 0.13, sx + 0.13, -0.58, -0.48, 0.0, 0.18, mat(GOLD, 0.3, 0.55))
box("backpack", -0.3, 0.3, -0.12, 0.12, 0.78, 0.92, mat(ORANGE_D, 0.5))  # ручка: опоры и перекладина
box("backpack", -0.3, -0.16, -0.12, 0.12, 0.92, 1.12, mat(ORANGE_D, 0.5))
box("backpack", 0.16, 0.3, -0.12, 0.12, 0.92, 1.12, mat(ORANGE_D, 0.5))
box("backpack", -0.3, 0.3, -0.12, 0.12, 1.06, 1.18, mat(ORANGE_D, 0.5))
for sx in (-1, 1):  # боковые карманы
    box("backpack", sx * 0.72 - (0.0 if sx > 0 else 0.16), sx * 0.72 + (0.16 if sx > 0 else 0.0), -0.3, 0.3, -0.7, -0.05,
        mat(ORANGE_L, 0.5))

# ── 2. Щит (защита): синее поле ступенчатым «гербом», золотой обод, белая звезда-ромб ────────────────────────────
BLUE, BLUE_D, WHITE = "2F7BFF", "1D4FC2", "F4F8FF"
rows = [(0.86, 0.95, 0.55), (0.86, 0.55, 0.15), (0.78, 0.15, -0.2), (0.66, -0.2, -0.5), (0.5, -0.5, -0.75),
        (0.32, -0.75, -0.93), (0.14, -0.93, -1.05)]
for w, z1, z0 in rows:  # обод — внешний ступенчатый силуэт позади, поле — сплошное спереди
    box("shield", -w - 0.12, w + 0.12, -0.05, 0.14, z0 - 0.1, z1 + 0.06, mat(GOLD, 0.3, 0.55), 0.01)
    box("shield", -w + 0.02, w - 0.02, -0.2, 0.0, z0, z1, mat(BLUE, 0.45, rings=0.34), 0.01)
box("shield", -0.96, 0.96, -0.14, 0.14, 0.95, 1.08, mat(GOLD, 0.3, 0.55))  # верхний край ступенью
box("shield", -0.7, 0.7, -0.14, 0.14, 1.08, 1.16, mat(GOLD_D, 0.3, 0.55))
box("shield", -0.07, 0.07, -0.24, -0.18, -0.75, 0.86, mat(BLUE_D, 0.45))  # продольная полоса
star = [(0.0, 0.46), (0.14, 0.14), (0.46, 0.0), (0.14, -0.14), (0.0, -0.46), (-0.14, -0.14), (-0.46, 0.0), (-0.14, 0.14)]
bm = bmesh.new()
verts_f = [bm.verts.new((x, -0.27, z + 0.1)) for x, z in star]
verts_b = [bm.verts.new((x, -0.17, z + 0.1)) for x, z in star]
bm.faces.new(verts_f[::-1])
bm.faces.new(verts_b)
for i in range(len(star)):
    j = (i + 1) % len(star)
    bm.faces.new((verts_f[i], verts_f[j], verts_b[j], verts_b[i]))
me = bpy.data.meshes.new("shield_star")
bm.to_mesh(me)
bm.free()
me.materials.append(mat(WHITE, 0.35))
coll("shield").objects.link(bpy.data.objects.new("shield_star", me))

# ── 3. Рука силы: согнутая рука «💪» — плечо, купол бицепса тонкими слоями, предплечье с наклоном к бицепсу ─
SKIN, SKIN_D, SKIN_L, RED, RED_D = "EC9A58", "C9733A", "F7B677", "F0473C", "B82E28"
AB = 0.05
box("arm", -1.0, 0.25, -0.36, 0.36, -0.74, -0.14, mat(SKIN, 0.5), AB)  # плечо
for k in range(6):  # купол бицепса: полукруг из тонких слоёв
    t0, t1 = k / 6, (k + 1) / 6
    half = 0.5 * math.sqrt(max(0.0, 1 - t1 * t1)) + 0.04
    z0, z1 = -0.14 + t0 * 0.78, -0.14 + t1 * 0.78
    box("arm", -0.42 - half, -0.42 + half, -0.4, 0.4, z0, z1, mat(SKIN if k < 5 else SKIN_L, 0.5), 0.03)
box("arm", -0.62, -0.36, -0.43, -0.39, 0.12, 0.44, mat(SKIN_L, 0.45), 0.02)  # блик
TILT = Matrix.Rotation(math.radians(18), 3, "Y")  # предплечье к бицепсу; ось — локоть
ELBOW = (0.36, 0, -0.44)
box("arm", 0.08, 0.64, -0.36, 0.36, -0.74, 0.5, mat(SKIN, 0.5), AB, TILT, ELBOW)
box("arm", 0.04, 0.68, -0.39, 0.39, 0.32, 0.54, mat(RED, 0.45), 0.04, TILT, ELBOW)  # повязка
box("arm", -0.2, 0.7, -0.4, 0.4, 0.54, 1.06, mat(SKIN, 0.5), AB, TILT, ELBOW)  # кулак
for k in range(4):  # костяшки
    xx = -0.04 + k * 0.2
    box("arm", xx, xx + 0.03, -0.44, -0.38, 0.6, 1.0, mat(SKIN_D, 0.5), 0.005, TILT, ELBOW)
box("arm", -0.32, -0.1, -0.36, 0.36, 0.62, 0.96, mat(SKIN, 0.5), AB, TILT, ELBOW)  # большой палец
box("arm", -1.12, -0.92, -0.4, 0.4, -0.8, -0.08, mat(RED, 0.45), 0.04)  # рукав у плеча

# ── 4. Монета: толстый 16-гранный диск, ступенчатый обод, «$» ──────────────────────────────────────────────────
disc("coin", 0, 0, 0, 1.0, 0.34, mat(GOLD_D, 0.3, 0.6))
disc("coin", 0, -0.04, 0, 0.86, 0.36, mat(GOLD, 0.28, 0.6))
disc("coin", 0, -0.1, 0, 0.68, 0.3, mat("F8D85A", 0.3, 0.55))
glyph("coin", "$", 0.0, -0.27, -0.04, 1.05, 0.04, mat(GOLD_D, 0.3, 0.6))

# ── 5. Доход: две монеты стопкой и зелёная стрелка вверх ступенями ─────────────────────────────────────────────
for k, (cx, cz) in enumerate(((-0.46, -0.78), (-0.46, -0.56), (-0.46, -0.34))):
    disc("income", cx, 0.1, cz, 0.62, 0.2, mat(GOLD_D if k % 2 == 0 else GOLD, 0.3, 0.6), 16, "Z")
disc("income", -0.46, 0.1, -0.22, 0.46, 0.06, mat("F8D85A", 0.3, 0.55), 16, "Z")
GREEN, GREEN_D, GREEN_L = "2FC94A", "1E8F33", "6CEB72"
box("income", 0.2, 0.6, -0.22, 0.12, -0.9, 0.3, mat(GREEN, 0.45))  # стержень стрелки
for k, (w, z0) in enumerate(((0.7, 0.3), (0.52, 0.5), (0.34, 0.7), (0.16, 0.9))):  # наконечник ступенями
    box("income", 0.4 - w, 0.4 + w, -0.22, 0.12, z0, z0 + 0.2, mat(GREEN if k % 2 == 0 else GREEN_L, 0.45))
box("income", 0.27, 0.53, -0.28, -0.2, -0.8, 0.26, mat(GREEN_L, 0.45))  # блик на стержне

# ── Свет и камера ──────────────────────────────────────────────────────────────────────────────────────────────
for name, loc, energy, size in (("Key", (-3.0, -4.0, 4.5), 520, 3.5), ("Fill", (4.0, -3.5, 1.0), 190, 4.0),
                                ("Rim", (2.0, 4.0, 3.5), 420, 3.0)):
    d = bpy.data.lights.new(name, "AREA")
    d.energy, d.size = energy, size
    o = bpy.data.objects.new(name, d)
    o.location = loc
    o.rotation_euler = (Vector(loc)).to_track_quat("Z", "Y").to_euler()
    scene.collection.objects.link(o)
cam_d = bpy.data.cameras.new("Cam")
cam_d.type = "ORTHO"
cam = bpy.data.objects.new("Cam", cam_d)
scene.collection.objects.link(cam)
scene.camera = cam
eye = Vector((-1.6, -6.0, 2.6))  # вид 3/4 спереди-слева, чуть сверху — одинаковый для всех
cam.location = eye
cam.rotation_euler = eye.to_track_quat("Z", "Y").to_euler()

# одинаковый «вес»: каждая иконка вписывается в кадр по своей проекции с одним запасом
bpy.context.view_layer.update()
inv = cam.matrix_world.inverted()
for name in ("backpack", "shield", "arm", "coin", "income"):
    for other, c in ICONS.items():
        c.hide_render = other != name
    pts = []
    bpy.context.view_layer.update()
    for o in ICONS[name].objects:
        if o.type == "MESH":
            pts += [inv @ (o.matrix_world @ v.co) for v in o.data.vertices]
        else:
            pts += [inv @ (o.matrix_world @ Vector(corner)) for corner in o.bound_box]
    xs, ys = [p.x for p in pts], [p.y for p in pts]
    span = max(max(xs) - min(xs), max(ys) - min(ys))
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    cam_d.ortho_scale = span * 1.24
    cam_d.shift_x, cam_d.shift_y = cx / cam_d.ortho_scale, cy / cam_d.ortho_scale
    scene.render.filepath = os.path.join(OUT, f"raw_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("icon", name)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "icons.blend"))
