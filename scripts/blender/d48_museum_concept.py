"""D48, этап A — концепт двухэтажного музея (только рендеры для утверждения владельцем; в игру ничего не попадает).

Верх — выставочный зал с шестью пустыми постаментами (столько мест сейчас, GameConfig.Museum.SlotsByLevel), центральным
проходом, кессонным потолком со световым фонарём, входом с портиком и лестничным проёмом у задней стены. Низ —
подземное хранилище: большой сейф, терминал инвентаря, центр безопасности, стеллажи, световые линии.
Стиль D39 для архитектуры: блоки с острыми рёбрами и тонкой фаской, ступенчатые силуэты, чистые яркие цвета; кольца-
квадраты D39 — только на крупных панелях (крупный шаг), остальное гладкое, чтобы музей не был покрыт одним узором.

Координаты сцены — как у участка в игре (Roblox, y вверх): центр участка на уровне пола зала, вход в −Z, трава на
y = −1.3 (MuseumHall.Ground). В Blender (x, y, z) Roblox → (x, −z, y). Внешние размеры зала — как у нынешнего
(36 × 33.4, MuseumHall: HW 18, фасад −12.7, задняя стена 20.7), участок 44 × 44.

Запуск: blender --background --factory-startup --python scripts/blender/d48_museum_concept.py -- <репо> [--fast] [виды]
Пишет assets/concepts/d48/museum_concept.blend и assets/concepts/d48/renders/*.png.
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
FAST = "--fast" in argv
ONLY = [a for a in argv[1:] if not a.startswith("--")]
OUT = os.path.join(REPO, "assets", "concepts", "d48")
RENDERS = os.path.join(OUT, "renders")
os.makedirs(RENDERS, exist_ok=True)
VASE = os.path.join(REPO, "assets", "models", "ArtV13_Vase.fbx")

# ── Размеры (стады, координаты участка) ─────────────────────────────────────────────────────────────────────────
G = -1.3  # трава
HW, FZ, BZ, T = 18.0, -12.7, 20.7, 1.4  # полуширина, фасад, задняя стена, толщина стен
IX, IZ0, IZ1 = HW - T, FZ + T, BZ - T  # внутренний зал: x ±16.6, z −11.3…19.3
CEIL = 16.0  # низ потолка зала
DOOR, DOORH = 6.0, 10.0
VF = -13.0  # пол хранилища (верх)
SLAB = 1.4  # перекрытие между этажами
WELL_X, WELL_Z0 = 5.5, 8.0  # лестничный проём: x ±5.5, z 8…19.3
RISE, RUN = 1.0, 1.25
PED_X, PED_Z = 11.0, (-4.0, 4.5, 13.0)  # шесть постаментов: две колонны по три
PORTICO_Z = -23.0

# ── Палитра ─────────────────────────────────────────────────────────────────────────────────────────────────────
C = {
    "wall": "F4EFE4", "panel": "E6DDC9", "pilaster": "FBF8F1", "gold": "E9B43C", "goldDeep": "C98E1E",
    "navy": "26345E", "navyDark": "1A2440", "floor": "EFE6D3", "floorAlt": "E3D5B9", "runner": "B8283A",
    "ceiling": "CFE2F3", "beam": "F7F2E8", "glassBlue": "BDEBFF", "cyan": "39E1FF", "warm": "FFD88A",
    "roof": "D9705A", "grass": "7FC75A", "path": "E9E2D2",
    "vWall": "1F4770", "vPanel": "3A6C96", "vFloor": "18233F", "vCeil": "152038", "steel": "A7B6C8",
    "steelDark": "5E7186", "red": "F0473C", "crateBlue": "3E7BE0", "crateRed": "E0533E", "crateGreen": "4CB860",
    "screen": "0E2A4A", "white": "FFFFFF", "mannequin": "4F86F7", "skin": "F5C99B", "pants": "2E3B55",
}


def lin(code):
    rgb = [int(code[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]


def R(x, y, z):
    return Vector((x, -z, y))


# ── Сцена ───────────────────────────────────────────────────────────────────────────────────────────────────────
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
if FAST:
    scene.render.engine = "BLENDER_WORKBENCH"
else:
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    try:
        scene.eevee.use_raytracing = True
        scene.eevee.taa_render_samples = 64
        scene.eevee.use_shadows = True
    except AttributeError:
        pass
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

COLL = {}


def coll(name):
    if name not in COLL:
        c = bpy.data.collections.new(name)
        scene.collection.children.link(c)
        COLL[name] = c
    return COLL[name]


# ── Материалы ───────────────────────────────────────────────────────────────────────────────────────────────────
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


def flat(code, rough=0.55, metal=0.0, name=None):
    key = name or f"flat_{code}_{rough}_{metal}"
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*lin(code), 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    MATS[key] = m
    return m


def rings(code, step, size, rad, width, dark=0.2, rough=0.55):
    """Сплошной цвет + отдельные скруглённые квадраты-контуры D39 (сетка в мировых осях; крупный шаг для архитектуры)."""
    key = f"rings_{code}_{step}"
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Roughness"].default_value = rough
    p = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(nt.nodes.new("ShaderNodeTexCoord").outputs["Object"], p.inputs["Vector"])
    n = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(nt.nodes.new("ShaderNodeNewGeometry").outputs["True Normal"], n.inputs["Vector"])
    px, py, pz = p.outputs["X"], p.outputs["Y"], p.outputs["Z"]
    nx, ny, nz = n.outputs["X"], n.outputs["Y"], n.outputs["Z"]
    top = _math(nt, "GREATER_THAN", _math(nt, "ABSOLUTE", nz), 0.7)
    fl = _math(nt, "MAXIMUM", _math(nt, "SQRT", _math(nt, "ADD", _math(nt, "MULTIPLY", nx, nx),
                                                    _math(nt, "MULTIPLY", ny, ny))), 0.01)
    along = _math(nt, "DIVIDE", _math(nt, "SUBTRACT", _math(nt, "MULTIPLY", py, nx), _math(nt, "MULTIPLY", px, ny)), fl)
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
    nt.links.new(_math(nt, "SUBTRACT", 1.0, _math(nt, "MULTIPLY", g.outputs["Result"], dark)), shade.inputs["Color2"])
    nt.links.new(shade.outputs["Color"], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value, bump.inputs["Distance"].default_value = 0.7, 0.03
    nt.links.new(_math(nt, "SUBTRACT", 1.0, g.outputs["Result"]), bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    MATS[key] = m
    return m


def neon(code, strength=6.0):
    key = f"neon_{code}_{strength}"
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*lin(code), 1)
    b.inputs["Emission Color"].default_value = (*lin(code), 1)
    b.inputs["Emission Strength"].default_value = strength
    MATS[key] = m
    return m


def glass(code, alpha=0.35):
    key = f"glass_{code}_{alpha}"
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*lin(code), 1)
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Alpha"].default_value = alpha
    try:
        m.surface_render_method = "BLENDED"
    except AttributeError:
        m.blend_method = "BLEND"
    MATS[key] = m
    return m


# ── Геометрия ───────────────────────────────────────────────────────────────────────────────────────────────────
TRIS = {"count": 0}


def _finish(bm, name, mat, cname):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    obj = bpy.data.objects.new(name, me)
    coll(cname).objects.link(obj)
    TRIS["count"] += sum(len(p.vertices) - 2 for p in me.polygons)
    return obj


def box(name, x0, x1, y0, y1, z0, z1, mat, cname="Hall", bevel=0.05):
    """Брусок по границам в координатах участка (Roblox): острые рёбра с тонкой фаской."""
    sx, sy, sz = abs(x1 - x0), abs(z1 - z0), abs(y1 - y0)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    b = min(bevel, sx / 3, sy / 3, sz / 3)
    if b > 0.004:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=b, segments=1, affect="EDGES")
    bmesh.ops.translate(bm, vec=R((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    return _finish(bm, name, mat, cname)


def prism(name, cx, cy, cz, radius, height, mat, cname="Hall", segments=16, axis="Z", bevel=0.04):
    """Многогранная призма (диск сейфа, медальон): axis Z — ось вдоль глубины участка (смотрит на вход), Y — вверх."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius, radius2=radius,
                          depth=height)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=[e for e in bm.edges if len(e.link_faces) == 2 and
                                  abs(e.link_faces[0].normal.dot(e.link_faces[1].normal)) < 0.5],
                        offset=bevel, segments=1, affect="EDGES")
    half = Matrix.Rotation(math.radians(180 / segments), 3, "Z")  # плоская грань снизу, а не ребро
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=half)
    if axis == "Z":  # ось диска — вдоль Roblox z (Blender −y)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"))
    bmesh.ops.translate(bm, vec=R(cx, cy, cz), verts=bm.verts)
    return _finish(bm, name, mat, cname)


def text(name, body, x, y, z, size, mat, face="-z", cname="Hall", align="CENTER"):
    """Надпись (Montserrat Black из Roblox Studio, как у Stud-UI), лицом к −z или к ±x участка."""
    font_path = None
    for p in sorted(glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Roblox\Versions\*\content\fonts\Montserrat-Black.ttf"))):
        font_path = p
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = 0.02
    cu.align_x = align
    cu.align_y = "CENTER"
    if font_path:
        cu.font = bpy.data.fonts.load(font_path, check_existing=True)
    obj = bpy.data.objects.new(name, cu)
    obj.data.materials.append(mat)
    obj.location = R(x, y, z)
    rot = {"+z": (math.radians(90), 0, 0), "-z": (math.radians(90), 0, math.radians(180)),
           "+x": (math.radians(90), 0, math.radians(90)), "-x": (math.radians(90), 0, math.radians(-90))}[face]
    obj.rotation_euler = rot
    coll(cname).objects.link(obj)
    return obj


def light(name, kind, x, y, z, energy, color="FFFFFF", size=2.0, target=None, cname="Lights", spot=60,
          shadow=True):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    data.use_shadow = shadow
    data.color = lin(color)
    if kind == "AREA":
        data.size = size
    if kind == "SPOT":
        data.spot_size = math.radians(spot)
        data.spot_blend = 0.5
        data.shadow_soft_size = 0.3
    if kind == "POINT":
        data.shadow_soft_size = size
    obj = bpy.data.objects.new(name, data)
    obj.location = R(x, y, z)
    aim = R(*(target or (x, y - 10, z)))
    obj.rotation_euler = (obj.location - aim).to_track_quat("Z", "Y").to_euler()
    coll(cname).objects.link(obj)
    return obj


def mannequin(x, z, face=0.0, cname="People", y=0.0):
    """Блочный игрок Roblox (рост ≈ 5.2) для масштаба: голова, торс, руки, ноги; face — поворот вокруг y."""
    parts = [((0, 4.6, 0), (1.15, 1.15, 1.15), "skin"), ((0, 3.15, 0), (2.0, 1.75, 1.0), "mannequin"),
             ((-1.5, 3.15, 0), (0.95, 1.75, 0.95), "skin"), ((1.5, 3.15, 0), (0.95, 1.75, 0.95), "skin"),
             ((-0.5, 1.15, 0), (0.95, 2.3, 0.95), "pants"), ((0.5, 1.15, 0), (0.95, 2.3, 0.95), "pants")]
    ca, sa = math.cos(face), math.sin(face)
    for (px, py, pz), (sx, sy, sz), col in parts:
        rx, rz = px * ca - pz * sa, px * sa + pz * ca
        cx, cy, cz = x + rx, y + py, z + rz
        o = box("Mannequin", cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2,
                flat(C[col], 0.5), cname, 0.06)
        o.rotation_euler = (0, 0, 0)


# ── Земля, участок, дорожка ─────────────────────────────────────────────────────────────────────────────────────
GRASS = rings(C["grass"], 4.0, 3.2, 0.6, 0.12, 0.12)
for name, x0, x1, z0, z1 in (("GrassF", -70, 70, -70, FZ), ("GrassB", -70, 70, BZ + 1, 45),
                             ("GrassL", -70, -HW - 1, FZ, BZ + 1), ("GrassR", HW + 1, 70, FZ, BZ + 1)):
    box(name, x0, x1, G - 2, G, z0, z1, GRASS, "Ground", 0)  # трава вокруг здания: под ним — хранилище
for name, x0, x1, z0, z1 in (("PlotN", -22, 22, -22.15, -21.85), ("PlotS", -22, 22, 21.85, 22.15),
                             ("PlotW", -22.15, -21.85, -22, 22), ("PlotE", 21.85, 22.15, -22, 22)):
    box(name, x0, x1, G, G + 0.06, z0, z1, flat("FFFFFF", 0.4), "PlotLines", 0)
box("Path", -4, 4, G, G + 0.08, -60, PORTICO_Z, flat(C["path"], 0.6), "Ground", 0.02)

# ── Подиум, портик, вход ────────────────────────────────────────────────────────────────────────────────────────
WALLM = flat(C["wall"], 0.5)
PANEL = rings(C["panel"], 2.0, 1.55, 0.3, 0.07, 0.16)
GOLD = flat(C["gold"], 0.32, 0.65, "gold")
NAVY = flat(C["navy"], 0.5)
WHITE = flat(C["pilaster"], 0.45)

for name, x0, x1, z0, z1 in (("PodiumL", -HW - 1, -HW, FZ, BZ + 1), ("PodiumR", HW, HW + 1, FZ, BZ + 1),
                             ("PodiumB", -HW - 1, HW + 1, BZ, BZ + 1)):
    box(name, x0, x1, G, -0.02, z0, z1, WALLM, "Exterior")
box("PorticoFloor", -16, 16, G, 0, PORTICO_Z + 2.1, FZ, flat(C["floor"], 0.5), "Exterior")
for i in range(3):  # три ступени к порталу
    h = G + (i + 1) * (-G / 3)
    box(f"PorticoStep{i}", -16 + i * 0.0, 16, G, h, PORTICO_Z + i * 0.7, PORTICO_Z + 2.1, flat(C["floor"], 0.5), "Exterior")
for cx in (-14.0, -8.0, 8.0, 14.0):  # колонны: квадратные, ступенчатые база и капитель
    box("ColBase", cx - 1.3, cx + 1.3, 0, 0.6, -20.7, -18.1, WHITE, "Exterior")
    box("ColShaft", cx - 0.95, cx + 0.95, 0.6, 13.0, -20.35, -18.45, WALLM, "Exterior")
    box("ColCap", cx - 1.25, cx + 1.25, 13.0, 13.6, -20.65, -18.15, GOLD, "Exterior")
    box("ColCap2", cx - 1.45, cx + 1.45, 13.6, 14.0, -20.85, -17.95, WHITE, "Exterior")
box("Entablature", -16.5, 16.5, 14.0, 16.0, -22.6, FZ, WHITE, "Exterior")
box("Frieze", -16.6, 16.6, 14.5, 15.3, -22.75, -22.5, GOLD, "Exterior")
for k, (w, y0) in enumerate(((16.5, 16.0), (13.5, 17.2), (10.5, 18.4), (7.5, 19.6), (4.5, 20.8))):  # фронтон ступенями
    box(f"Pediment{k}", -w, w, y0, y0 + 1.2, -22.6 + 0.2 * k, -21.0, WHITE, "Exterior")
prism("Emblem", 0, 18.3, -22.7, 2.0, 0.5, GOLD, "Exterior", 16)
prism("EmblemIn", 0, 18.3, -23.0, 1.4, 0.3, neon(C["warm"], 2.5), "Exterior", 16)
# дверной портал: золотая рама и световые пилоны у входа
box("DoorFrameL", -DOOR - 1.0, -DOOR, 0, DOORH + 1.0, FZ - 0.5, FZ + 0.3, GOLD, "Exterior")
box("DoorFrameR", DOOR, DOOR + 1.0, 0, DOORH + 1.0, FZ - 0.5, FZ + 0.3, GOLD, "Exterior")
box("DoorFrameT", -DOOR - 1.0, DOOR + 1.0, DOORH, DOORH + 1.0, FZ - 0.5, FZ + 0.3, GOLD, "Exterior")
for sx in (-1, 1):
    box("Lantern", sx * 9.2 - 0.5, sx * 9.2 + 0.5, 4.0, 7.0, FZ - 0.8, FZ - 0.2, neon(C["warm"], 4.0), "Exterior")
    box("LanternCap", sx * 9.2 - 0.7, sx * 9.2 + 0.7, 7.0, 7.4, FZ - 1.0, FZ - 0.1, GOLD, "Exterior")

# ── Верхний этаж: стены, пол с лестничным проёмом, потолок, крыша ──────────────────────────────────────────────
FLOORM = rings(C["floor"], 4.0, 3.5, 0.5, 0.06, 0.08, 0.35)
for name, x0, x1, z0, z1 in (("FloorFront", -HW, HW, FZ, WELL_Z0), ("FloorL", -HW, -WELL_X, WELL_Z0, BZ),
                             ("FloorR", WELL_X, HW, WELL_Z0, BZ), ("FloorBack", -WELL_X, WELL_X, IZ1, BZ)):
    box(name, x0, x1, -SLAB, 0, z0, z1, FLOORM, "Hall", 0.02)
box("WallL", -HW, -IX, 0, CEIL + 1.4, FZ, BZ, WALLM)
box("WallR", IX, HW, 0, CEIL + 1.4, FZ, BZ, WALLM, "WallsNear")
box("WallBack", -IX, IX, 0, CEIL + 1.4, IZ1, BZ, WALLM)
box("WallFrontL", -IX, -DOOR, 0, CEIL + 1.4, FZ, IZ0, WALLM, "WallsNear")
box("WallFrontR", DOOR, IX, 0, CEIL + 1.4, FZ, IZ0, WALLM, "WallsNear")
box("WallFrontTop", -DOOR, DOOR, DOORH, CEIL + 1.4, FZ, IZ0, WALLM, "WallsNear")
# тёмно-синий плинтус, золотой пояс и карниз по периметру зала
for name, x0, x1, z0, z1 in (("L", -IX, -IX + 0.2, IZ0, IZ1), ("R", IX - 0.2, IX, IZ0, IZ1),
                             ("B", -IX, IX, IZ1 - 0.2, IZ1)):
    box("Base" + name, x0, x1, 0, 1.2, z0, z1, NAVY)
    box("Belt" + name, x0, x1, 12.4, 12.8, z0, z1, GOLD)
    box("Cornice" + name, x0 - (0.3 if name == "R" else 0), x1 + (0.3 if name == "L" else 0), 15.2, 16.0,
        z0 - (0.3 if name == "B" else 0), z1, WHITE)
for x0, x1 in ((-IX, -DOOR - 1.0), (DOOR + 1.0, IX)):
    box("BaseF", x0, x1, 0, 1.2, IZ0, IZ0 + 0.2, NAVY)
    box("BeltF", x0, x1, 12.4, 12.8, IZ0, IZ0 + 0.2, GOLD)
# пилястры и панели с кольцами между ними (боковые стены)
for side in (-1, 1):
    wx = side * IX
    for pz in (-7.0, 0.25, 8.75, 17.0):
        box("Pilaster", wx - side * 0.9 if side > 0 else wx, wx if side > 0 else wx + 0.9, 0, 15.2,
            pz - 0.8, pz + 0.8, WHITE)
        box("PilCap", wx - side * 1.15 if side > 0 else wx, wx if side > 0 else wx + 1.15, 13.6, 14.4,
            pz - 1.0, pz + 1.0, GOLD)
        box("Sconce", wx - side * 1.3 if side > 0 else wx + 0.9, wx - side * 0.9 if side > 0 else wx + 1.3, 8.6, 9.8,
            pz - 0.45, pz + 0.45, GOLD)
        box("SconceGlow", wx - side * 1.5 if side > 0 else wx + 1.3, wx - side * 1.3 if side > 0 else wx + 1.5, 8.8,
            9.6, pz - 0.3, pz + 0.3, neon(C["warm"], 5.0), "Hall", 0)
    for z0, z1 in ((-6.0, -0.75), (1.25, 7.75), (9.75, 16.0)):
        box("Panel", wx - side * 0.15 if side > 0 else wx, wx if side > 0 else wx + 0.15, 2.0, 11.6,
            z0 + 0.2, z1 - 0.2, PANEL)
        box("PanelLight", wx - side * 0.25 if side > 0 else wx, wx if side > 0 else wx + 0.25, 11.6, 11.8,
            z0 + 0.4, z1 - 0.4, neon(C["warm"], 3.0))
# задняя стена: арка над лестницей с медальоном
box("BackArchL", -7.2, -5.8, 0, 13.5, IZ1 - 0.6, IZ1, WHITE)
box("BackArchR", 5.8, 7.2, 0, 13.5, IZ1 - 0.6, IZ1, WHITE)
box("BackArchT", -7.2, 7.2, 12.2, 13.5, IZ1 - 0.6, IZ1, WHITE)
prism("BackMedal", 0, 10.0, IZ1 - 0.35, 1.5, 0.4, GOLD, "Hall", 16)
# потолок: кессоны и световой фонарь
box("CeilingSlab", -HW, HW, CEIL + 1.4, CEIL + 2.4, FZ, BZ, flat(C["ceiling"], 0.6), "Ceiling")
box("CeilingBase", -IX, IX, CEIL + 0.4, CEIL + 1.4, IZ0, IZ1, flat(C["ceiling"], 0.6), "Ceiling", 0)
for x in (-11.0, -5.5, 5.5, 11.0):
    box("BeamZ", x - 0.5, x + 0.5, CEIL - 0.4, CEIL + 0.4, IZ0, IZ1, flat(C["beam"], 0.5), "Ceiling")
for z in (-5.5, 0.5, 6.5, 12.5):
    box("BeamX", -IX, IX, CEIL - 0.35, CEIL + 0.35, z - 0.5, z + 0.5, flat(C["beam"], 0.5), "Ceiling")
box("Skylight", -5.0, 5.0, CEIL + 0.39, CEIL + 0.4, -4.5, 12.0, neon("EAF7FF", 2.2), "Ceiling", 0)
for x0, x1, z0, z1 in ((-5.5, 5.5, -5.0, -4.5), (-5.5, 5.5, 12.0, 12.5), (-5.5, -5.0, -4.5, 12.0),
                       (5.0, 5.5, -4.5, 12.0)):
    box("SkylightRim", x0, x1, CEIL - 0.6, CEIL - 0.3, z0, z1, GOLD, "Ceiling")
ROOF = rings(C["roof"], 2.0, 1.55, 0.3, 0.07, 0.12)
for k, w in enumerate((19.5, 16.0, 12.5, 9.0, 5.5, 2.0)):  # крыша ступенями (силуэт D39)
    box(f"Roof{k}", -w, w, CEIL + 2.4 + k * 1.1, CEIL + 3.5 + k * 1.1, FZ - 0.4, BZ + 0.6, ROOF, "Roof")
box("Lantern", -4.5, 4.5, CEIL + 9.0, CEIL + 10.4, -3.5, 11.0, glass(C["glassBlue"], 0.55), "Roof")

# ── Постаменты (эталон): ступенчатый силуэт, кольца на теле, световое место под экспонат, табличка ───────────────
PEDS = []


def pedestal(cx, cz, face, cname="Pedestals", ring_coll="Pedestals"):
    objs = [
        box("PedBase", cx - 2.5, cx + 2.5, 0, 0.55, cz - 2.5, cz + 2.5, NAVY, cname),
        box("PedTrim", cx - 2.25, cx + 2.25, 0.55, 0.75, cz - 2.25, cz + 2.25, GOLD, cname),
        box("PedBody", cx - 2.05, cx + 2.05, 0.75, 2.75, cz - 2.05, cz + 2.05,
            rings(C["pilaster"], 0.6, 0.42, 0.1, 0.03, 0.18, 0.45), cname),
        box("PedCap", cx - 2.4, cx + 2.4, 2.75, 3.15, cz - 2.4, cz + 2.4, NAVY, cname),
        box("PedTop", cx - 2.2, cx + 2.2, 3.15, 3.27, cz - 2.2, cz + 2.2, GOLD, cname),
        box("PedSpotN", cx - 1.55, cx + 1.55, 3.27, 3.33, cz - 1.55, cz - 1.35, neon(C["cyan"], 5), ring_coll, 0),
        box("PedSpotS", cx - 1.55, cx + 1.55, 3.27, 3.33, cz + 1.35, cz + 1.55, neon(C["cyan"], 5), ring_coll, 0),
        box("PedSpotW", cx - 1.55, cx - 1.35, 3.27, 3.33, cz - 1.35, cz + 1.35, neon(C["cyan"], 5), ring_coll, 0),
        box("PedSpotE", cx + 1.35, cx + 1.55, 3.27, 3.33, cz - 1.35, cz + 1.35, neon(C["cyan"], 5), ring_coll, 0),
    ]
    # табличка на стороне к проходу
    px = cx - face * 2.18
    objs.append(box("PedPlate", px - 0.12 if face > 0 else px, px if face > 0 else px + 0.12, 1.2, 2.25,
                    cz - 1.4, cz + 1.4, flat(C["navyDark"], 0.4), cname, 0.03))
    PEDS.append((cx, cz, face))
    return objs


for side in (-1, 1):
    for pz in PED_Z:
        target = side > 0 and pz == PED_Z[0]  # здесь в кадре «занято» стоит ваза
        pedestal(side * PED_X, pz, side, ring_coll="EmptyP" if target else "Pedestals")
        text("PedLabel", "СВОБОДНО", side * (PED_X - 2.33), 1.72, pz, 0.42, flat(C["cyan"], 0.3),
             "+x" if side < 0 else "-x", "EmptyP" if target else "Pedestals")
        if target:
            cx = side * PED_X
            for x0, x1, z0, z1 in ((cx - 1.55, cx + 1.55, pz - 1.55, pz - 1.35),
                                   (cx - 1.55, cx + 1.55, pz + 1.35, pz + 1.55),
                                   (cx - 1.55, cx - 1.35, pz - 1.35, pz + 1.35),
                                   (cx + 1.35, cx + 1.55, pz - 1.35, pz + 1.35)):
                box("PedSpotBusy", x0, x1, 3.27, 3.33, z0, z1, neon(C["gold"], 5), "Exhibit", 0)
            text("PedLabelBusy", "ВАЗА", side * (PED_X - 2.33), 1.95, pz, 0.38, flat("FFFFFF", 0.3), "-x", "Exhibit")
            text("PedLabelIncome", "+25 $/сек", side * (PED_X - 2.33), 1.45, pz, 0.32, flat("7CFF6B", 0.3), "-x",
                 "Exhibit")
        light("PedSpot", "SPOT", side * PED_X * 0.82, CEIL - 0.6, pz, 900, C["warm"], target=(side * PED_X, 3.3, pz),
              spot=34)

# ── Пол: проход-дорожка, места защиты, лазерные отметки ────────────────────────────────────────────────────────
box("Runner", -3.2, 3.2, 0, 0.08, IZ0, WELL_Z0 - 0.8, flat(C["runner"], 0.7), "Hall", 0.01)
for sx in (-1, 1):
    box("RunnerEdge", sx * 3.2 - 0.18, sx * 3.2 + 0.18, 0, 0.1, IZ0, WELL_Z0 - 0.8, GOLD, "Hall", 0.01)
DEF = neon("7FD8FF", 1.4)
for (dx, dz) in ((-6.8, -8.0), (6.8, -8.0), (0.0, 0.25), (-6.8, 8.6), (6.8, 8.6)):  # места защиты на полу
    for x0, x1, z0, z1 in ((dx - 1.6, dx + 1.6, dz - 1.6, dz - 1.4), (dx - 1.6, dx + 1.6, dz + 1.4, dz + 1.6),
                           (dx - 1.6, dx - 1.4, dz - 1.4, dz + 1.4), (dx + 1.4, dx + 1.6, dz - 1.4, dz + 1.4)):
        box("DefSpot", x0, x1, 0.08, 0.13, z0, z1, DEF, "Hall", 0)
    box("DefCore", dx - 0.35, dx + 0.35, 0.08, 0.12, dz - 0.35, dz + 0.35, DEF, "Hall", 0)
for lz in (-6.0, 6.2):  # отметки лазера поперёк прохода и гнёзда излучателей
    box("LaserMark", -5.4, 5.4, 0.08, 0.12, lz - 0.1, lz + 0.1, neon(C["red"], 1.2), "Hall", 0)
    for sx in (-1, 1):
        box("LaserSocket", sx * 5.6 - 0.35, sx * 5.6 + 0.35, 0, 3.2, lz - 0.35, lz + 0.35, flat(C["steel"], 0.35, 0.5),
            "Hall")
        box("LaserEye", sx * 5.6 - 0.4, sx * 5.6 + 0.4, 2.2, 2.6, lz - 0.2, lz + 0.2, neon(C["red"], 4), "Hall", 0)
# сундук (сдача добычи) — у входа слева, как сейчас
box("Chest", -14.0, -10.0, 0, 2.0, -10.6, -8.0, flat(C["crateBlue"], 0.45), "Hall")
box("ChestLid", -14.2, -9.8, 2.0, 2.6, -10.8, -7.8, GOLD, "Hall")
box("ChestLock", -12.4, -11.6, 1.0, 1.8, -7.95, -7.8, flat(C["navyDark"], 0.4), "Hall")

# ── Лестница вниз (без телепорта): два марша с площадкой, ширина марша 5.2 ─────────────────────────────────────
STEP = rings("E6D9BF", 4.0, 3.5, 0.5, 0.06, 0.10, 0.4)
NOSE = neon(C["warm"], 3.5)
x0a, x1a, x0b, x1b = -WELL_X, -0.3, 0.3, WELL_X
for i in range(1, 7):  # марш 1: вниз к задней стене
    top = -i * RISE
    z0, z1 = WELL_Z0 + (i - 1) * RUN, WELL_Z0 + i * RUN
    box(f"StepA{i}", x0a, x1a, -7.0, top, z0, z1, STEP, "Stair", 0.03)
    box(f"NoseA{i}", x0a + 0.2, x1a - 0.2, top, top + 0.06, z0 + 0.02, z0 + 0.14, NOSE, "Stair", 0)
LZ0 = WELL_Z0 + 6 * RUN
box("Landing", -WELL_X, WELL_X, -7.0, -6.0, LZ0, IZ1, STEP, "Stair", 0.03)
box("UnderLanding", x0b, x1b, VF, -7.0, LZ0, IZ1, flat(C["vWall"], 0.5), "Stair", 0.02)
for j in range(1, 8):  # марш 2: вниз ко входу хранилища
    top = -6.0 - j * RISE
    z1, z0 = LZ0 - (j - 1) * RUN, LZ0 - j * RUN
    box(f"StepB{j}", x0b, x1b, VF, top, z0, z1, STEP, "Stair", 0.03)
    box(f"NoseB{j}", x0b + 0.2, x1b - 0.2, top, top + 0.06, z1 - 0.14, z1 - 0.02, NOSE, "Stair", 0)
box("UnderFlightA", x0a, x1a, VF, -7.0, WELL_Z0, LZ0, flat(C["vWall"], 0.5), "Stair", 0.02)
box("Divider", -0.3, 0.3, VF, 1.1, WELL_Z0, LZ0 - 0.4, rings(C["vPanel"], 2.0, 1.55, 0.3, 0.07, 0.16), "Stair")
box("DividerCap", -0.45, 0.45, 1.1, 1.35, WELL_Z0 - 0.15, LZ0 - 0.25, GOLD, "Stair")
box("DividerGlow", -0.32, 0.32, -0.4, -0.2, WELL_Z0, LZ0 - 0.4, neon(C["cyan"], 3), "Stair", 0)
for sx in (-1, 1):  # стены колодца и балюстрады вокруг проёма
    wx0, wx1 = (WELL_X, WELL_X + 0.25) if sx > 0 else (-WELL_X - 0.25, -WELL_X)
    box("WellWall", wx0, wx1, VF, -SLAB, WELL_Z0, IZ1, rings("4A7DBA", 2.0, 1.55, 0.3, 0.07, 0.16), "Stair", 0.02)
    gx0, gx1 = (wx0 - 0.08, wx0) if sx > 0 else (wx1, wx1 + 0.08)
    box("WellGlow", gx0, gx1, -4.2, -4.0, WELL_Z0, IZ1, neon(C["warm"], 3.5), "Stair", 0)
    box("WellGlow2", gx0, gx1, -10.2, -10.0, WELL_Z0, IZ1, neon(C["cyan"], 3.5), "Stair", 0)
    xr = sx * (WELL_X + 0.2)
    for k in range(7):
        pz = WELL_Z0 + 0.3 + k * 1.8
        box("RailPost", xr - 0.2, xr + 0.2, 0, 3.0, pz - 0.2, pz + 0.2, GOLD, "Stair")
    box("RailTop", xr - 0.3, xr + 0.3, 3.0, 3.3, WELL_Z0 + 0.1, IZ1, GOLD, "Stair")
    box("RailGlass", xr - 0.06, xr + 0.06, 0.4, 2.9, WELL_Z0 + 0.3, IZ1, glass(C["glassBlue"], 0.28), "Stair", 0)
    box("RailLight", xr - 0.32, xr + 0.32, 2.95, 3.0, WELL_Z0 + 0.1, IZ1, neon(C["warm"], 2.5), "Stair", 0)
for k in range(4):  # перила над вторым маршем (передний край проёма справа)
    px = 0.6 + k * 1.6
    box("RailPostF", px - 0.2, px + 0.2, 0, 3.0, WELL_Z0 - 0.1, WELL_Z0 + 0.3, GOLD, "Stair")
box("RailTopF", 0.3, WELL_X + 0.4, 3.0, 3.3, WELL_Z0 - 0.15, WELL_Z0 + 0.35, GOLD, "Stair")
box("RailGlassF", 0.4, WELL_X + 0.2, 0.4, 2.9, WELL_Z0 + 0.05, WELL_Z0 + 0.15, glass(C["glassBlue"], 0.28), "Stair", 0)
box("StairSign", -4.2, 4.2, 13.7, 15.0, IZ1 - 0.9, IZ1 - 0.6, flat(C["navyDark"], 0.4), "Stair", 0.03)
text("StairSignText", "ХРАНИЛИЩЕ", 0, 14.35, IZ1 - 0.95, 0.75, neon(C["gold"], 1.5), "-z", "Stair")

# ── Подземное хранилище ─────────────────────────────────────────────────────────────────────────────────────────
VW = flat(C["vWall"], 0.5)
VP = rings(C["vPanel"], 2.0, 1.55, 0.3, 0.07, 0.18, 0.45)
box("VFloor", -HW, HW, VF - 1.4, VF, FZ, BZ, rings(C["vFloor"], 3.0, 2.6, 0.45, 0.06, 0.18, 0.4), "Vault", 0.02)
box("VWallL", -HW, -IX, VF, -SLAB, FZ, BZ, VW, "Vault")
box("VWallR", IX, HW, VF, -SLAB, FZ, BZ, VW, "Vault")
box("VWallF", -IX, IX, VF, -SLAB, FZ, IZ0, VW, "Vault")
box("VWallB", -IX, IX, VF, -SLAB, IZ1, BZ, VW, "Vault")
for name, x0, x1, z0, z1 in (("VCeilF", -IX, IX, IZ0, WELL_Z0), ("VCeilL", -IX, -WELL_X - 0.25, WELL_Z0, IZ1),
                             ("VCeilR", WELL_X + 0.25, IX, WELL_Z0, IZ1)):
    box(name, x0, x1, -SLAB - 0.4, -SLAB, z0, z1, flat(C["vCeil"], 0.6), "VaultCeiling", 0)
for x in (-11.0, 11.0):
    box("VCeilLine", x - 0.15, x + 0.15, -SLAB - 0.55, -SLAB - 0.4, IZ0, IZ1, neon(C["cyan"], 4), "VaultCeiling", 0)
for z in (-6.0, 2.0):
    box("VCeilLineX", -IX, IX, -SLAB - 0.55, -SLAB - 0.4, z - 0.15, z + 0.15, neon(C["cyan"], 4), "VaultCeiling", 0)
for side in (-1, 1):  # золотые пилястры и световые полосы у пола
    wx = side * IX
    for pz in (-7.0, 0.0, 7.0, 14.0):
        box("VPil", wx - side * 0.8 if side > 0 else wx, wx if side > 0 else wx + 0.8, VF, -SLAB - 0.4,
            pz - 0.6, pz + 0.6, GOLD, "Vault")
    for z0, z1 in ((-6.2, -0.8), (0.8, 6.2), (7.8, 13.2)):
        box("VPanel", wx - side * 0.15 if side > 0 else wx, wx if side > 0 else wx + 0.15, VF + 1.2, VF + 9.4,
            z0, z1, VP, "Vault")
    box("VFloorGlow", wx - side * 0.25 if side > 0 else wx, wx if side > 0 else wx + 0.25, VF, VF + 0.15,
        IZ0, IZ1, neon(C["cyan"], 3), "Vault", 0)
for x in (-8.0, 8.0):  # золотые линии пола
    box("VInlay", x - 0.12, x + 0.12, VF, VF + 0.05, IZ0, WELL_Z0 - 1, GOLD, "Vault", 0)
# сейф: ступенчатая рама, диск-дверь, штурвал, ригели
box("SafeFrame", -7.0, 7.0, VF, VF + 11.0, IZ0, IZ0 + 0.8, flat(C["steelDark"], 0.4, 0.4), "Vault")
box("SafeFrame2", -6.2, 6.2, VF + 0.6, VF + 10.4, IZ0 + 0.8, IZ0 + 1.2, GOLD, "Vault")
prism("SafeRing", 0, VF + 5.5, IZ0 + 1.6, 4.6, 0.8, flat(C["steel"], 0.3, 0.6), "Vault", 16)
prism("SafeDoor", 0, VF + 5.5, IZ0 + 2.2, 3.9, 0.8, flat("C9D3DE", 0.28, 0.6), "Vault", 16)
prism("SafeCore", 0, VF + 5.5, IZ0 + 2.7, 1.6, 0.6, GOLD, "Vault", 16)
prism("SafeHub", 0, VF + 5.5, IZ0 + 3.1, 0.7, 0.6, flat(C["steelDark"], 0.3, 0.5), "Vault", 8)
for k in range(4):  # штурвал: четыре спицы
    a = math.radians(45 * k)
    hx, hy = math.cos(a) * 1.5, math.sin(a) * 1.5
    o = box("SafeSpoke", -1.8, 1.8, -0.18, 0.18, -0.18, 0.18, GOLD, "Vault")
    o.rotation_euler = (0, -a, 0)
    o.location = R(0, VF + 5.5, IZ0 + 3.3)
for k in range(8):  # ригели по кругу
    a = math.radians(22.5 + 45 * k)
    prism("SafeBolt", math.cos(a) * 4.25, VF + 5.5 + math.sin(a) * 4.25, IZ0 + 2.0, 0.35, 0.6, GOLD, "Vault", 8, "Z", 0.02)
for sx in (-1, 1):
    box("SafeGlow", sx * 7.4 - 0.25, sx * 7.4 + 0.25, VF, VF + 10.0, IZ0, IZ0 + 0.5, neon(C["warm"], 4), "Vault", 0)
box("SafeArc", -7.0, 7.0, VF, VF + 0.1, IZ0 + 1.2, IZ0 + 5.0, GOLD, "Vault", 0)
# терминал инвентаря — по центру, лицом к лестнице
TX = -4.5
box("TermBase", TX - 1.4, TX + 1.4, VF, VF + 3.0, 0.4, 2.0, flat(C["navy"], 0.45), "Vault")
box("TermTrim", TX - 1.55, TX + 1.55, VF + 3.0, VF + 3.25, 0.25, 2.15, GOLD, "Vault")
# экран терминала смотрит на лестницу (+z участка), наклонён назад на 35°: плиты строятся плашмя у начала координат,
# толщина — вдоль нормали (y участка), потом поворот и перенос
TILT = (math.radians(55), 0, 0)
for name, x0, x1, y0, y1, z0, z1, mat in (
        ("TermBezel", -1.8, 1.8, -0.3, -0.05, -1.25, 1.25, flat(C["navyDark"], 0.4)),
        ("TermScreen", -1.6, 1.6, -0.05, 0.05, -1.05, 1.05, neon("2A86FF", 1.6)),
        ("TermIcon", -0.6, 0.6, 0.05, 0.09, -0.45, 0.65, neon("FFFFFF", 3.0)),  # значок рюкзака: корпус
        ("TermIcon", -0.35, 0.35, 0.05, 0.09, -0.75, -0.45, neon("FFFFFF", 3.0)),  # ручка
        ("TermIcon", -0.4, 0.4, 0.09, 0.12, 0.05, 0.35, neon("2A86FF", 2.0))):  # карман
    o = box(name, x0, x1, y0, y1, z0, z1, mat, "Vault", 0)
    o.rotation_euler = TILT
    o.location = R(TX, VF + 4.1, 1.3)
text("TermText", "ИНВЕНТАРЬ", TX, VF + 2.0, 2.07, 0.36, neon(C["gold"], 1.2), "+z", "Vault")
# стеллажи слева
for k, cz in enumerate((-7.5, -1.0, 5.5)):
    x0, x1 = -IX + 0.2, -IX + 2.6
    box("ShelfBack", x0, x0 + 0.3, VF, VF + 8.0, cz - 2.8, cz + 2.8, flat(C["steelDark"], 0.4, 0.3), "Vault")
    for sz in (cz - 2.8, cz + 2.5):
        box("ShelfPost", x0, x1, VF, VF + 8.0, sz, sz + 0.3, GOLD, "Vault")
    for lvl in range(4):
        y = VF + 0.6 + lvl * 2.0
        box("ShelfBoard", x0, x1, y - 0.15, y, cz - 2.8, cz + 2.8, flat(C["steel"], 0.35, 0.4), "Vault")
        for n in range(3):
            colr = (C["crateBlue"], C["crateRed"], C["crateGreen"], C["gold"])[(k + lvl + n) % 4]
            z0 = cz - 2.3 + n * 1.65
            box("Crate", x0 + 0.5, x1 - 0.2, y, y + 1.2, z0, z0 + 1.35,
                flat(colr, 0.4, 0.6 if colr == C["gold"] else 0.0), "Vault", 0.06)
            box("CrateBand", x0 + 0.45, x1 - 0.15, y + 0.5, y + 0.7, z0 - 0.02, z0 + 1.37, GOLD, "Vault", 0.02)
    box("ShelfGlow", x1 - 0.1, x1, VF + 7.6, VF + 7.8, cz - 2.6, cz + 2.6, neon(C["cyan"], 3), "Vault", 0)
# центр безопасности справа: стол, мониторы, большой экран с планом зала, маяки тревоги
box("DeskTop", 8.5, 14.8, VF + 2.6, VF + 2.9, -5.5, 3.5, flat(C["navy"], 0.4), "Vault")
box("DeskEdge", 8.4, 14.9, VF + 2.45, VF + 2.65, -5.6, 3.6, GOLD, "Vault")
box("DeskBody", 12.6, 14.8, VF, VF + 2.6, -5.3, 3.3, flat(C["navyDark"], 0.45), "Vault")
for k, mz in enumerate((-3.6, -0.5, 2.6)):
    box("MonStand", 13.6, 13.9, VF + 2.9, VF + 3.8, mz - 0.2, mz + 0.2, flat(C["steelDark"], 0.3, 0.5), "Vault")
    box("MonFrame", 13.3, 13.6, VF + 3.6, VF + 5.6, mz - 1.4, mz + 1.4, flat(C["navyDark"], 0.4), "Vault", 0.04)
    box("MonScreen", 13.2, 13.3, VF + 3.75, VF + 5.45, mz - 1.25, mz + 1.25, neon(C["screen"], 1.0), "Vault", 0)
    for (a0, a1, b0, b1) in ((3.95, 4.05, -1.0, 1.0), (5.15, 5.25, -1.0, 1.0), (3.95, 5.25, -1.0, -0.9),
                             (3.95, 5.25, 0.9, 1.0), (4.4, 4.8, -0.3 + k * 0.2, 0.1 + k * 0.2)):
        box("MonLine", 13.15, 13.2, VF + a0, VF + a1, mz + b0, mz + b1,
            neon(C["red"] if a1 - a0 > 0.3 and b1 - b0 < 0.6 else C["cyan"], 3.5), "Vault", 0)
box("WallScreen", IX - 0.25, IX - 0.05, VF + 4.5, VF + 10.0, -8.5, 5.5, flat(C["navyDark"], 0.4), "Vault", 0.04)
box("WallScreenIn", IX - 0.3, IX - 0.25, VF + 4.8, VF + 9.7, -8.2, 5.2, neon(C["screen"], 1.0), "Vault", 0)
for (zz0, zz1, yy0, yy1) in ((-7.6, 4.6, 5.3, 5.4), (-7.6, 4.6, 9.1, 9.2), (-7.6, -7.5, 5.3, 9.2), (4.5, 4.6, 5.3, 9.2)):
    box("PlanLine", IX - 0.35, IX - 0.3, VF + yy0, VF + yy1, zz0, zz1, neon(C["cyan"], 3.5), "Vault", 0)
for pz in (-5.0, -1.2, 2.6):
    for py in (6.2, 8.2):
        box("PlanPed", IX - 0.35, IX - 0.3, VF + py - 0.35, VF + py + 0.35, pz - 0.35, pz + 0.35,
            neon(C["gold"], 3.0), "Vault", 0)
box("PlanAlert", IX - 0.36, IX - 0.3, VF + 7.0, VF + 7.4, -6.4, -6.0, neon(C["red"], 6.0), "Vault", 0)
for pz in (-9.0, 6.0):
    box("Beacon", IX - 0.6, IX - 0.05, VF + 10.3, VF + 11.0, pz - 0.3, pz + 0.3, neon(C["red"], 5.0), "Vault", 0.05)
box("Chair", 10.4, 11.8, VF, VF + 1.8, -1.4, 0.2, flat(C["crateRed"], 0.5), "Vault", 0.08)
box("ChairBack", 10.2, 10.5, VF + 1.8, VF + 3.6, -1.4, 0.2, flat(C["crateRed"], 0.5), "Vault", 0.08)
text("SecText", "БЕЗОПАСНОСТЬ", IX - 0.4, VF + 10.6, -1.5, 0.55, neon(C["gold"], 1.2), "-x", "Vault")

# ── Свет ────────────────────────────────────────────────────────────────────────────────────────────────────────
world = bpy.data.worlds.new("Sky")
world.use_nodes = True
wt = world.node_tree
bg = next(n for n in wt.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (*lin("C9E4FF"), 1)
bg.inputs["Strength"].default_value = 0.7
sky = wt.nodes.new("ShaderNodeBackground")
sky.inputs["Color"].default_value = (*lin("57AEFF"), 1)
sky.inputs["Strength"].default_value = 1.0
mix = wt.nodes.new("ShaderNodeMixShader")
path = wt.nodes.new("ShaderNodeLightPath")
out = next(n for n in wt.nodes if n.type == "OUTPUT_WORLD")
wt.links.new(path.outputs["Is Camera Ray"], mix.inputs["Fac"])
wt.links.new(bg.outputs["Background"], mix.inputs[1])
wt.links.new(sky.outputs["Background"], mix.inputs[2])
wt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
scene.world = world
sun = bpy.data.lights.new("Sun", "SUN")
sun.energy = 3.6
sun.angle = math.radians(4)
sun_obj = bpy.data.objects.new("Sun", sun)
sun_obj.rotation_euler = (math.radians(52), 0, math.radians(-35))
coll("Lights").objects.link(sun_obj)
for x in (-8.0, 8.0):  # заполняющий свет зала из кессонов
    for z in (-3.0, 9.5):
        light("HallFill", "AREA", x, CEIL - 0.2, z, 950, "FFF4E2", 7.0, (x, 0, z), shadow=False)
light("Skylight", "AREA", 0, CEIL - 0.7, 3.75, 2000, "EAF7FF", 9.0, (0, 0, 3.75))
light("Entry", "AREA", 0, 9.0, FZ - 3.0, 600, "FFF4E2", 6.0, (0, 4, 0), shadow=False)
light("WellLight", "AREA", 0, -0.8, 13.6, 650, "FFE7B8", 6.0, (0, -12, 13.6), shadow=False)
light("WellA", "POINT", -2.9, -2.0, 12.0, 280, "FFE7B8", 1.0, shadow=False)
light("WellB", "POINT", 2.9, -8.5, 11.0, 380, "E6F4FF", 1.0, shadow=False)
for x, z in ((-8.0, -5.0), (8.0, -5.0), (-8.0, 7.0), (8.0, 7.0), (0.0, 1.0)):  # хранилище
    light("VaultFill", "AREA", x, -2.2, z, 700, "E6F4FF", 6.0, (x, VF, z), shadow=False)
light("SafeKey", "SPOT", 0, -3.0, -1.0, 2200, C["warm"], target=(0, VF + 5.5, IZ0), spot=55)
light("ShelfKey", "SPOT", -6.0, -3.5, -1.0, 900, "E6F4FF", target=(-IX, VF + 4, -1.0), spot=80)
light("SecKey", "SPOT", 6.0, -3.5, -1.0, 900, "E6F4FF", target=(IX, VF + 5, -1.5), spot=80)

# ── Масштаб: фигуры игроков ─────────────────────────────────────────────────────────────────────────────────────
mannequin(-1.5, -4.0, math.radians(15))
mannequin(4.2, 2.0, math.radians(200))
mannequin(2.9, -16.5, math.radians(0), "People", 0.0)
mannequin(-2.9, 15.0, math.radians(0), "People", -5.0)
mannequin(3.0, -3.0, math.radians(180), "People", VF)
mannequin(10.0, 2.0, math.radians(90), "People", VF)


# ── Камера и виды ───────────────────────────────────────────────────────────────────────────────────────────────
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam_data.clip_end = 600


def show(names_hidden):
    for name, c in COLL.items():
        hide = name in names_hidden
        c.hide_render = hide
        c.hide_viewport = hide


def shot(name, eye, at, fov=70, res=(1600, 900), hidden=(), ortho=None):
    if ONLY and name not in ONLY:
        return None
    show(set(hidden))
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 50 if FAST else 100
    if ortho:
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = ortho
    else:
        cam_data.type = "PERSP"
        cam_data.sensor_fit = "VERTICAL"
        cam_data.angle = math.radians(fov)
    cam.location = R(*eye)
    if ortho:
        cam.rotation_euler = (0, 0, math.pi)  # строго сверху, вход участка (−z) внизу кадра
    else:
        cam.rotation_euler = (R(*eye) - R(*at)).to_track_quat("Z", "Y").to_euler()
    path = os.path.join(RENDERS, name + ".png")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("render", path)
    return path


VASE_OBJS = []


def place_vase(cx, cz):
    """Одобренная ваза v13 (D39) на постамент — для кадра «занятое место»."""
    if not os.path.exists(VASE):
        return
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=VASE)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll("Exhibit").objects.link(o)
    meshes = [o for o in new if o.type == "MESH"]
    if not meshes:
        return
    tex = os.path.join(REPO, "assets", "textures", "art")
    m = bpy.data.materials.new("VaseV13")
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Roughness"].default_value = 0.5
    col = nt.nodes.new("ShaderNodeTexImage")
    col.image = bpy.data.images.load(os.path.join(tex, "v13_vase_color.png"))
    nt.links.new(col.outputs["Color"], b.inputs["Base Color"])
    nrm = nt.nodes.new("ShaderNodeTexImage")
    nrm.image = bpy.data.images.load(os.path.join(tex, "v13_vase_normal.png"))
    nrm.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    for o in meshes:
        o.data.materials.clear()
        o.data.materials.append(m)
    lo = Vector((min(min((o.matrix_world @ v.co)[i] for v in o.data.vertices) for o in meshes) for i in range(3)))
    hi = Vector((max(max((o.matrix_world @ v.co)[i] for v in o.data.vertices) for o in meshes) for i in range(3)))
    height = hi.z - lo.z
    scale = 3.2 / height if height > 0 else 1
    root = [o for o in new if o.parent is None]
    for o in root:
        o.scale = o.scale * scale
    bpy.context.view_layer.update()
    lo = Vector((min(min((o.matrix_world @ v.co)[i] for v in o.data.vertices) for o in meshes) for i in range(3)))
    hi = Vector((max(max((o.matrix_world @ v.co)[i] for v in o.data.vertices) for o in meshes) for i in range(3)))
    target = R(cx, 3.33, cz)
    shift = Vector((target.x - (lo.x + hi.x) / 2, target.y - (lo.y + hi.y) / 2, target.z - lo.z))
    for o in root:
        o.location += shift
    VASE_OBJS.extend(new)


place_vase(PED_X, -4.0)

ALL_UP = ("Ceiling", "Roof")
shot("01_exterior_entrance", (-17, 6.0, -44), (0, 9.5, -14), 58, hidden=("Vault", "Exhibit"))
shot("02_from_entrance", (0, 6.5, -16.5), (0, 4.5, 8), 74, hidden=("Exhibit",))
shot("03_toward_entrance", (-3.5, 7.5, 7.0), (2, 4.5, -12), 74, hidden=("Exhibit",))
shot("04_hall_overview", (27, 40, -30), (0, -1, 5), 44, hidden=ALL_UP + ("Exhibit", "WallsNear", "Exterior"))
shot("05_stair_from_hall", (-8.5, 10.5, 4.0), (0.0, -6.0, 14.5), 66, hidden=("Exhibit",))
shot("06_stair_down", (2.8, -0.8, 19.0), (2.8, -11.5, 5.0), 76, hidden=("Exhibit",))
shot("07_vault", (2.6, -7.0, 7.0), (-1.5, -8.0, -9.5), 78, hidden=("Exhibit",))
shot("08_vault_security", (-1.0, -6.6, 0.8), (14.0, -8.4, -1.5), 72, hidden=("Exhibit",))
shot("09_pedestal_empty", (-4.2, 5.6, -10.0), (-PED_X, 2.6, -4.0), 46, (1100, 1100), ("Exhibit",))
shot("10_pedestal_item", (3.6, 7.2, -12.6), (PED_X, 3.8, -4.0), 46, (1100, 1100), ("EmptyP",))
shot("11_plan_upper", (0, 120, 4), (0, 0, 4.001), 0, (1100, 1100), ALL_UP + ("Exhibit", "People"), 58)
shot("12_plan_vault", (0, 120, 4), (0, 0, 4.001), 0, (1100, 1100),
     ALL_UP + ("Exhibit", "People", "Hall", "Pedestals", "Exterior", "WallsNear", "VaultCeiling"), 58)

print("TRIS", TRIS["count"])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "museum_concept.blend"))
