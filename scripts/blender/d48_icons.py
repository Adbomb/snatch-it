"""D48 v2 — иконки HUD в стиле D39: портфель (инвентарь), щит (защита), монета, доход и три варианта силы —
кулак (основной), рука с гантелью, бицепс.

Только PNG для утверждения: в Roblox ничего не загружается. Одна камера (вид 3/4 сверху, ортографическая), один
свет (ключ слева сверху, заполняющий справа, контровой сзади), прозрачный фон; модели — блоки с острыми рёбрами и
тонкой фаской, силуэт ступенями, чистые яркие цвета. Контур и тень одной толщины добавляет scripts/d48_hud_mockup.py.

HUD v3 (ТЗ владельца 2026-11-17, свои иконки вместо библиотечных): тем же набором приёмов добавлены магазин
(тележка), музей, фазы суток — солнце, луна, песочные часы (подготовка), череп (Судная ночь).

Запуск: blender --background --factory-startup --python scripts/blender/d48_icons.py -- <репо> [имя,имя…]
Пишет assets/concepts/d48/v2/icons/raw_<имя>.png (1024², прозрачный фон) и icons.blend; со списком имён — только их
(icons.blend тогда не перезаписывается). Контур, обрезку и размер 256 для игры делает scripts/hud_icons.py.
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
ONLY = [n for n in argv[1].split(",") if n] if len(argv) > 1 else None
OUT = os.path.join(REPO, "assets", "concepts", "d48", "v2", "icons")
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
    elif axis == "X":  # ось вдоль x (гриф гантели)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
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


# ── 1. Портфель (инвентарь): тёплый оранжевый корпус, крышка ступенью, ручка, золотые замки и уголки ───────────
ORANGE, ORANGE_D, ORANGE_L, BROWN = "EE8A2C", "C2621E", "FFAD52", "6E3414"
GOLD, GOLD_D = "F2C230", "C9921B"
box("briefcase", -1.0, 1.0, -0.34, 0.34, -0.78, 0.3, mat(ORANGE, 0.5, rings=0.42))  # корпус
box("briefcase", -1.06, 1.06, -0.4, 0.4, 0.22, 0.58, mat(ORANGE_D, 0.5))  # крышка
box("briefcase", -0.94, 0.94, -0.33, 0.33, 0.58, 0.68, mat(ORANGE_D, 0.5))  # верх крышки ступенью
box("briefcase", -0.98, 0.98, -0.41, -0.36, 0.14, 0.22, mat(BROWN, 0.5), 0.01)  # шов
for sx in (-0.56, 0.56):  # ремни с замками
    box("briefcase", sx - 0.1, sx + 0.1, -0.42, -0.34, -0.78, 0.22, mat(ORANGE_L, 0.5), 0.015)
    box("briefcase", sx - 0.16, sx + 0.16, -0.5, -0.38, 0.12, 0.42, mat(GOLD, 0.3, 0.55))
    box("briefcase", sx - 0.05, sx + 0.05, -0.53, -0.48, 0.2, 0.32, mat(BROWN, 0.5), 0.008)
for sx in (-1, 1):  # золотые уголки внизу
    box("briefcase", sx * 1.0 - (0.22 if sx > 0 else -0.0), sx * 1.0 + (0.0 if sx > 0 else 0.22), -0.4, 0.4, -0.84,
        -0.6, mat(GOLD, 0.3, 0.55), 0.02)
box("briefcase", -0.4, -0.24, -0.14, 0.14, 0.68, 0.98, mat(BROWN, 0.5))  # ручка
box("briefcase", 0.24, 0.4, -0.14, 0.14, 0.68, 0.98, mat(BROWN, 0.5))
box("briefcase", -0.44, 0.44, -0.16, 0.16, 0.94, 1.1, mat(BROWN, 0.5))
box("briefcase", -0.3, 0.3, -0.18, -0.12, 0.98, 1.06, mat("9A5428", 0.5), 0.01)

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

# ── 3. Сила — три варианта в одном стиле: кожа, красная повязка, ступенчатый силуэт ─────────────────────────
SKIN, SKIN_D, SKIN_L, RED, RED_D, WHITE2 = "F0A062", "C9733A", "FFC68E", "F0473C", "B82E28", "FFFFFF"
AB = 0.05

# 3а. Кулак ✊ (основной): кисть прямо к зрителю, четыре согнутых пальца ступенькой, большой палец поперёк,
# повязка на запястье — «удар».
box("fist", -0.46, 0.46, -0.32, 0.4, -1.2, -0.5, mat(SKIN, 0.5), AB)  # запястье
box("fist", -0.54, 0.54, -0.4, 0.48, -0.74, -0.42, mat(RED, 0.45), 0.04)  # повязка
box("fist", -0.55, 0.55, -0.41, 0.49, -0.62, -0.56, mat(WHITE2, 0.45), 0.01)  # полоса на повязке
box("fist", -0.66, 0.66, -0.12, 0.42, -0.44, 0.62, mat(SKIN, 0.5), AB)  # ладонь (тыльная часть)
for k, (fx, top) in enumerate(((-0.495, 0.74), (-0.165, 0.86), (0.165, 0.84), (0.495, 0.7))):
    box("fist", fx - 0.155, fx + 0.155, -0.36, 0.3, top - 0.34, top, mat(SKIN_L if k in (1, 2) else SKIN, 0.48), 0.05)
    box("fist", fx - 0.15, fx + 0.15, -0.52, -0.2, -0.02, top - 0.3, mat(SKIN, 0.5), 0.05)  # средние фаланги
    box("fist", fx - 0.14, fx + 0.14, -0.5, -0.24, -0.22, -0.02, mat(SKIN_D, 0.5), 0.04)  # кончики, поджатые
box("fist", -0.72, 0.16, -0.7, -0.42, -0.42, -0.14, mat(SKIN, 0.5), 0.06)  # большой палец поперёк
box("fist", 0.04, 0.24, -0.72, -0.44, -0.4, -0.16, mat(SKIN_L, 0.48), 0.05)  # подушечка
box("fist", -0.78, -0.56, -0.5, 0.3, -0.5, 0.16, mat(SKIN_D, 0.5), 0.05)  # основание большого пальца сбоку
for k, fx in enumerate((-0.495, -0.165, 0.165, 0.495)):  # блики на костяшках
    top = (0.74, 0.86, 0.84, 0.7)[k]
    box("fist", fx - 0.09, fx + 0.09, -0.38, -0.33, top - 0.14, top - 0.06, mat("FFE2C4", 0.4), 0.01)

# 3б. Рука с гантелью: согнутая рука, кулак сжимает гантель (гриф и ступенчатые диски)
box("dumbbell", -1.05, 0.15, -0.34, 0.34, -0.78, -0.2, mat(SKIN, 0.5), AB)  # плечо
box("dumbbell", -0.86, 0.06, -0.38, 0.38, -0.3, 0.12, mat(SKIN, 0.5), AB)  # бицепс: купол тремя ступенями
box("dumbbell", -0.74, -0.06, -0.4, 0.4, 0.12, 0.36, mat(SKIN, 0.5), AB)
box("dumbbell", -0.6, -0.2, -0.41, 0.41, 0.36, 0.5, mat(SKIN_L, 0.5), 0.04)
box("dumbbell", -1.12, -0.9, -0.38, 0.38, -0.84, -0.14, mat(RED, 0.45), 0.04)  # рукав
box("dumbbell", 0.1, 0.62, -0.34, 0.34, -0.78, 0.46, mat(SKIN, 0.5), AB)  # предплечье
box("dumbbell", 0.06, 0.66, -0.38, 0.38, 0.3, 0.5, mat(RED, 0.45), 0.04)  # повязка
box("dumbbell", 0.02, 0.7, -0.4, 0.38, 0.5, 0.98, mat(SKIN, 0.5), AB)  # кулак
for k in range(4):
    xx = 0.08 + k * 0.16
    box("dumbbell", xx, xx + 0.03, -0.44, -0.38, 0.56, 0.92, mat(SKIN_D, 0.5), 0.005)
DARK, DARK_L = "2C3350", "48527A"
disc("dumbbell", 0.36, -0.02, 0.74, 0.1, 2.3, mat("B9C3D6", 0.3, 0.7), 16, "X")  # гриф
for sx in (-1, 1):
    cx = 0.36 + sx * 0.82
    disc("dumbbell", cx, -0.02, 0.74, 0.4, 0.22, mat(DARK, 0.4), 16, "X")
    disc("dumbbell", cx + sx * 0.18, -0.02, 0.74, 0.3, 0.16, mat(DARK_L, 0.4), 16, "X")
    disc("dumbbell", cx - sx * 0.13, -0.02, 0.74, 0.43, 0.05, mat(GOLD, 0.3, 0.55), 16, "X")

# 3в. Бицепс 💪 (улучшенный): крупная «Г», чёткий купол бицепса тремя ступенями, кулак к зрителю, синий рукав
SLEEVE, SLEEVE_D = "3E7BE0", "2A58AE"
box("bicep", -1.15, -0.78, -0.42, 0.42, -0.92, -0.06, mat(SLEEVE, 0.5), 0.05)  # рукав футболки
box("bicep", -1.2, -0.72, -0.44, 0.44, -0.98, -0.86, mat(SLEEVE_D, 0.5), 0.02)
box("bicep", -0.8, 0.2, -0.38, 0.38, -0.9, -0.2, mat(SKIN, 0.5), AB)  # плечо
box("bicep", -0.86, 0.12, -0.42, 0.42, -0.24, 0.2, mat(SKIN, 0.5), AB)  # купол: крупный, три ступени
box("bicep", -0.76, 0.0, -0.44, 0.44, 0.2, 0.5, mat(SKIN, 0.5), AB)
box("bicep", -0.62, -0.14, -0.45, 0.45, 0.5, 0.7, mat(SKIN_L, 0.5), 0.05)
box("bicep", 0.12, 0.66, -0.36, 0.36, -0.86, 0.42, mat(SKIN, 0.5), AB)  # предплечье
box("bicep", 0.08, 0.7, -0.4, 0.4, 0.26, 0.48, mat(RED, 0.45), 0.04)  # повязка
box("bicep", 0.02, 0.74, -0.42, 0.42, 0.48, 1.0, mat(SKIN, 0.5), AB)  # кулак
for k in range(4):
    xx = 0.09 + k * 0.165
    box("bicep", xx, xx + 0.03, -0.46, -0.4, 0.54, 0.94, mat(SKIN_D, 0.5), 0.005)
box("bicep", -0.08, 0.14, -0.4, 0.36, 0.56, 0.9, mat(SKIN, 0.5), 0.05)  # большой палец

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

# ── HUD v3 ─────────────────────────────────────────────────────────────────────────────────────────────────────
def ry(deg):
    return Matrix.Rotation(math.radians(deg), 3, "Y")


def star4(icon, cx, cz, r, y0, y1, m):
    """Четырёхлучевая звезда-ромб лицом к камере (как на щите)."""
    k = 0.3
    pts = [(0, r), (r * k, r * k), (r, 0), (r * k, -r * k), (0, -r), (-r * k, -r * k), (-r, 0), (-r * k, r * k)]
    b = bmesh.new()
    front = [b.verts.new((cx + x, y0, cz + z)) for x, z in pts]
    back = [b.verts.new((cx + x, y1, cz + z)) for x, z in pts]
    b.faces.new(front[::-1])
    b.faces.new(back)
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        b.faces.new((front[i], front[j], back[j], back[i]))
    me_ = bpy.data.meshes.new(icon + "_star")
    b.to_mesh(me_)
    b.free()
    me_.materials.append(m)
    coll(icon).objects.link(bpy.data.objects.new(icon + "_star", me_))


# 6. Магазин: красная тележка — корзина ступенью, белый обод, рейки, ручка, колёса, покупки сверху
CART, CART_D, CART_L = "F0473C", "B82E28", "FF7A6E"
STEEL, STEEL_D = "B9C3D6", "2C3350"
box("shop", -0.82, 0.86, -0.42, 0.42, -0.28, 0.44, mat(CART, 0.45, rings=0.4))  # корзина
box("shop", -0.66, 0.7, -0.38, 0.38, -0.5, -0.28, mat(CART_D, 0.45))  # дно ступенью
box("shop", -0.9, 0.94, -0.48, 0.48, 0.44, 0.58, mat("F4F8FF", 0.35))  # белый обод
for sx in (-0.5, -0.06, 0.38):  # рейки на лицевой стенке
    box("shop", sx, sx + 0.14, -0.47, -0.41, -0.2, 0.4, mat(CART_L, 0.45), 0.012)
box("shop", -1.1, -0.92, -0.12, 0.12, 0.3, 0.98, mat(STEEL_D, 0.4))  # стойка ручки
box("shop", -1.28, -0.86, -0.3, 0.3, 0.94, 1.1, mat(STEEL_D, 0.4))  # ручка
box("shop", -1.3, -1.1, -0.31, 0.31, 0.92, 1.12, mat(CART, 0.45), 0.02)  # красная накладка ручки
box("shop", -0.74, 0.78, -0.3, 0.3, -0.66, -0.5, mat(STEEL, 0.3, 0.7))  # рама
for wx in (-0.5, 0.56):
    disc("shop", wx, -0.36, -0.86, 0.24, 0.2, mat(STEEL_D, 0.4))
    disc("shop", wx, -0.48, -0.86, 0.1, 0.08, mat(GOLD, 0.3, 0.55))
box("shop", -0.6, -0.16, -0.26, 0.26, 0.58, 0.98, mat(GOLD, 0.3, 0.55))  # покупки: золотая коробка
box("shop", -0.6, -0.16, -0.28, -0.24, 0.72, 0.8, mat("FFE873", 0.3), 0.008)
box("shop", -0.06, 0.34, -0.24, 0.24, 0.58, 0.82, mat("2FC94A", 0.45))  # зелёная
box("shop", 0.42, 0.74, -0.2, 0.2, 0.58, 1.06, mat("2F7BFF", 0.45))  # синяя высокая
box("shop", 0.42, 0.74, -0.22, -0.18, 0.9, 0.98, mat("F4F8FF", 0.35), 0.008)

# 7. Музей: ступени, четыре белые колонны, синяя стена с золотой дверью, фронтон ступенями со звездой
STONE, STONE_D = "F4F8FF", "C9D3E6"
box("museum", -1.08, 1.08, -0.56, 0.5, -1.0, -0.82, mat(STONE_D, 0.5))  # ступени
box("museum", -0.96, 0.96, -0.5, 0.46, -0.82, -0.66, mat(STONE, 0.45))
box("museum", -0.84, 0.84, -0.2, 0.42, -0.66, 0.3, mat(BLUE, 0.45, rings=0.36))  # стена
box("museum", -0.15, 0.15, -0.24, -0.18, -0.66, 0.02, mat(GOLD, 0.3, 0.55), 0.012)  # дверь
box("museum", -0.2, 0.2, -0.26, -0.18, 0.02, 0.1, mat(GOLD_D, 0.3, 0.55), 0.01)
for cx_ in (-0.69, -0.33, 0.33, 0.69):  # колонны с базой и капителью
    box("museum", cx_ - 0.1, cx_ + 0.1, -0.44, -0.24, -0.6, 0.24, mat(STONE, 0.4))
    box("museum", cx_ - 0.14, cx_ + 0.14, -0.48, -0.2, -0.66, -0.58, mat(STONE_D, 0.45), 0.015)
    box("museum", cx_ - 0.14, cx_ + 0.14, -0.48, -0.2, 0.22, 0.3, mat(STONE_D, 0.45), 0.015)
box("museum", -1.0, 1.0, -0.54, 0.48, 0.3, 0.46, mat(STONE, 0.4))  # антаблемент
for k, w in enumerate((0.92, 0.7, 0.48, 0.26)):  # фронтон ступенями
    box("museum", -w, w, -0.5, 0.44, 0.46 + k * 0.15, 0.61 + k * 0.15, mat(BLUE if k % 2 == 0 else BLUE_D, 0.45))
star4("museum", 0.0, 0.66, 0.2, -0.56, -0.5, mat(GOLD, 0.3, 0.55))

# 8. День: солнце — диск ступенью и восемь лучей-брусков
SUN, SUN_L, SUN_D = "FFD23F", "FFEB7A", "FF9F1C"
disc("sun", 0, 0, 0, 0.66, 0.34, mat(SUN_D, 0.4))
disc("sun", 0, -0.06, 0, 0.56, 0.34, mat(SUN, 0.35))
disc("sun", 0, -0.12, 0, 0.4, 0.3, mat(SUN_L, 0.35))
for k in range(8):
    long_ = k % 2 == 0
    box("sun", -0.11, 0.11, -0.12, 0.12, 0.8, 1.16 if long_ else 1.02, mat(SUN_D if long_ else SUN, 0.4),
        rot=ry(k * 45))

# 9. Ночь: месяц ступенями и две звезды
MOON, MOON_L = "CFC7FF", "EEEAFF"
R_OUT, R_IN, C_IN = 1.0, 0.86, (0.44, 0.22)
step_ = 0.125
z_ = -1.0
row_ = 0
while z_ < 1.0 - 1e-6:
    zm = z_ + step_ / 2
    xo = math.sqrt(max(R_OUT ** 2 - zm ** 2, 0.0))
    right = xo
    dz = zm - C_IN[1]
    if abs(dz) < R_IN:
        right = min(xo, C_IN[0] - math.sqrt(R_IN ** 2 - dz ** 2))
    if right - (-xo) > 0.12:
        box("moon", -xo, right, -0.2, 0.2, z_, z_ + step_, mat(MOON_L if zm > 0.45 else MOON, 0.4), 0.015)
    z_ += step_
    row_ += 1
star4("moon", 0.5, 0.42, 0.26, -0.16, -0.06, mat("FFEB7A", 0.35))
star4("moon", 0.72, -0.2, 0.15, -0.16, -0.06, mat("FFFFFF", 0.35))

# 10. Подготовка: песочные часы — золотые крышки, стекло ступенями, песок
GLASS, SAND, WOOD = "BFE6FF", "FFB020", "6E3414"
for sz in (1, -1):
    box("hourglass", -0.76, 0.76, -0.4, 0.4, sz * 0.86 - 0.11, sz * 0.86 + 0.11, mat(GOLD, 0.3, 0.55))
    box("hourglass", -0.62, 0.62, -0.34, 0.34, sz * 1.03 - 0.06, sz * 1.03 + 0.06, mat(GOLD_D, 0.3, 0.55))
    for k, w in enumerate((0.56, 0.44, 0.3, 0.14)):  # колба сужается к перемычке
        z0_ = 0.75 - (k + 1) * 0.185
        lo, hi = (z0_, z0_ + 0.185) if sz > 0 else (-z0_ - 0.185, -z0_)
        box("hourglass", -w, w, -0.26, 0.26, lo, hi, mat(GLASS, 0.2), 0.012)
for sx in (-0.68, 0.56):
    box("hourglass", sx, sx + 0.12, -0.36, -0.24, -0.76, 0.76, mat(WOOD, 0.5), 0.02)
box("hourglass", -0.3, 0.3, -0.3, -0.24, 0.24, 0.42, mat(SAND, 0.45), 0.01)  # песок сверху
box("hourglass", -0.16, 0.16, -0.3, -0.24, 0.06, 0.24, mat(SAND, 0.45), 0.01)
box("hourglass", -0.04, 0.04, -0.3, -0.24, -0.4, 0.06, mat(SAND, 0.45), 0.006)  # струйка
box("hourglass", -0.46, 0.46, -0.3, -0.24, -0.74, -0.56, mat(SAND, 0.45), 0.01)  # горка снизу
box("hourglass", -0.32, 0.32, -0.3, -0.24, -0.56, -0.44, mat("FFC65A", 0.45), 0.01)
box("hourglass", -0.16, 0.16, -0.3, -0.24, -0.44, -0.36, mat("FFC65A", 0.45), 0.01)

# 11. Судная ночь: череп — свод ступенью, скулы, зубы, тёмные глазницы с красными огнями
BONE, BONE_D, HOLE, EYE = "F4F8FF", "CBD3E4", "1E1428", "FF3B3B"
box("skull", -0.86, 0.86, -0.5, 0.5, -0.12, 0.84, mat(BONE, 0.45, rings=0.4))  # свод
box("skull", -0.66, 0.66, -0.46, 0.46, 0.84, 1.04, mat(BONE, 0.45))
box("skull", -0.94, -0.84, -0.3, 0.3, 0.1, 0.6, mat(BONE_D, 0.45), 0.02)  # виски
box("skull", 0.84, 0.94, -0.3, 0.3, 0.1, 0.6, mat(BONE_D, 0.45), 0.02)
box("skull", -0.56, 0.56, -0.46, 0.4, -0.58, -0.12, mat(BONE_D, 0.45))  # скулы и челюсть
for k, tx in enumerate((-0.42, -0.14, 0.14, 0.42)):  # зубы
    box("skull", tx - 0.11, tx + 0.11, -0.5, -0.3, -0.86, -0.56, mat(BONE, 0.4), 0.03)
for sx in (-1, 1):
    box("skull", sx * 0.36 - 0.24, sx * 0.36 + 0.24, -0.56, -0.46, 0.14, 0.6, mat(HOLE, 0.6), 0.02)  # глазницы
    box("skull", sx * 0.36 - 0.09, sx * 0.36 + 0.09, -0.6, -0.54, 0.26, 0.44, mat(EYE, 0.3, emit=2.5), 0.01)
box("skull", -0.09, 0.09, -0.56, -0.46, -0.1, 0.1, mat(HOLE, 0.6), 0.015)  # нос

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
ALL = ("briefcase", "shield", "coin", "income", "fist", "dumbbell", "bicep", "shop", "museum", "sun", "moon",
       "hourglass", "skull")
for name in ONLY or ALL:
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
if not ONLY:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "icons.blend"))
