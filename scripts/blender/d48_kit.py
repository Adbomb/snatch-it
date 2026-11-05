"""D48 v2 — общий набор Blender-концептов: детали ровно тех форм, что есть в Roblox (Block, Cylinder, Ball, Wedge),
материалы в стиле D39, свет, камера, учёт деталей и выгрузка списка деталей (JSON) для будущей сборки кодом
(World/ModelBuilder: size, cframe, color, material, shape) — без мешей и без загрузок в Roblox.

Координаты — как в Roblox (y вверх); в Blender (x, y, z) Roblox → (x, −z, y). Повороты деталей — матрица 3 × 3
в осях Roblox (как у CFrame). Цилиндр Roblox: ось — локальная X, диаметр — min(Y, Z). Клин Roblox: высокая сторона
сзади (+Z), скос смотрит вперёд (−Z) и вверх.
Подключение: sys.path.insert(0, папка скрипта); import d48_kit as K; K.reset().
"""

import glob
import json
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

A = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))  # Roblox → Blender
ID = Matrix.Identity(3)


def R(x, y, z):
    return Vector((x, -z, y))


def lin(code):
    rgb = [int(code[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]


def rot_y(deg):
    """Поворот вокруг вертикали Roblox (как CFrame.Angles(0, rad, 0))."""
    a = math.radians(deg)
    return Matrix(((math.cos(a), 0, math.sin(a)), (0, 1, 0), (-math.sin(a), 0, math.cos(a))))


def rot_x(deg):
    a = math.radians(deg)
    return Matrix(((1, 0, 0), (0, math.cos(a), -math.sin(a)), (0, math.sin(a), math.cos(a))))


def rot_z(deg):
    a = math.radians(deg)
    return Matrix(((math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0), (0, 0, 1)))


# ── Состояние сцены ─────────────────────────────────────────────────────────────────────────────────────────────
S = {"scene": None, "coll": {}, "mats": {}, "bricks": [], "tris": 0, "group": "Misc"}


def reset(engine="EEVEE", samples=64):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    S.update(scene=scene, coll={}, mats={}, bricks=[], tris=0)
    engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    if engine == "WORKBENCH":
        scene.render.engine = "BLENDER_WORKBENCH"
    else:
        scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
        try:
            scene.eevee.use_raytracing = True
            scene.eevee.taa_render_samples = samples
            scene.eevee.use_shadows = True
        except AttributeError:
            pass
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    return scene


def coll(name):
    c = S["coll"].get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        S["scene"].collection.children.link(c)
        S["coll"][name] = c
    return c


def group(name):
    """Группа деталей для учёта и выгрузки (зал, ниши, хранилище, устройство…); коллекция Blender — та же."""
    S["group"] = name


# ── Материалы ───────────────────────────────────────────────────────────────────────────────────────────────────
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


def _principled(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def flat(code, rough=0.5, metal=0.0):
    key = ("flat", code, rough, metal)
    if key not in S["mats"]:
        m = bpy.data.materials.new(f"flat_{code}")
        m.use_nodes = True
        b = _principled(m)
        b.inputs["Base Color"].default_value = (*lin(code), 1)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
        S["mats"][key] = m
    return S["mats"][key]


def rings(code, step=2.0, dark=0.12, rough=0.5):
    """Квадратный рельеф LegoSquaresSoft (D36) по мотиву колец D39: скруглённые квадраты-контуры с шагом step."""
    key = ("rings", code, step, dark, rough)
    if key in S["mats"]:
        return S["mats"][key]
    size, rad, width = step * 0.8, step * 0.16, step * 0.035
    m = bpy.data.materials.new(f"rings_{code}_{step}")
    m.use_nodes = True
    nt = m.node_tree
    b = _principled(m)
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
    bump.inputs["Strength"].default_value, bump.inputs["Distance"].default_value = 0.6, 0.03
    nt.links.new(_math(nt, "SUBTRACT", 1.0, g.outputs["Result"]), bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    S["mats"][key] = m
    return m


def neon(code, strength=5.0):
    key = ("neon", code, strength)
    if key not in S["mats"]:
        m = bpy.data.materials.new(f"neon_{code}")
        m.use_nodes = True
        b = _principled(m)
        b.inputs["Base Color"].default_value = (*lin(code), 1)
        b.inputs["Emission Color"].default_value = (*lin(code), 1)
        b.inputs["Emission Strength"].default_value = strength
        S["mats"][key] = m
    return S["mats"][key]


def glassm(code, alpha=0.35):
    key = ("glass", code, alpha)
    if key not in S["mats"]:
        m = bpy.data.materials.new(f"glass_{code}")
        m.use_nodes = True
        b = _principled(m)
        b.inputs["Base Color"].default_value = (*lin(code), 1)
        b.inputs["Roughness"].default_value = 0.05
        b.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except AttributeError:
            m.blend_method = "BLEND"
        S["mats"][key] = m
    return S["mats"][key]


# ── Детали (как в Roblox) ───────────────────────────────────────────────────────────────────────────────────────
def _bm_shape(shape, size, bevel):
    sx, sy, sz = size
    bm = bmesh.new()
    if shape == "Block":
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
        b = min(bevel, sx / 3, sy / 3, sz / 3)
        if b > 0.004:
            bmesh.ops.bevel(bm, geom=list(bm.edges), offset=b, segments=1, affect="EDGES")
    elif shape == "Cylinder":  # ось — локальная X
        r = min(sy, sz) / 2
        seg = 32 if r > 0.6 else 20
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r, depth=sx)
        b = min(bevel, r / 3, sx / 3)
        if b > 0.004:
            sharp = [e for e in bm.edges if len(e.link_faces) == 2 and
                     abs(e.link_faces[0].normal.dot(e.link_faces[1].normal)) < 0.5]
            bmesh.ops.bevel(bm, geom=sharp, offset=b, segments=1, affect="EDGES")
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    elif shape == "Ball":
        d = min(size)
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=d / 2)
    elif shape == "Wedge":  # высокая сторона +Z, скос к −Z
        hx, hy, hz = sx / 2, sy / 2, sz / 2
        v = [bm.verts.new(p) for p in ((-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz),
                                       (-hx, hy, hz), (hx, hy, hz))]
        for f in ((0, 3, 2, 1), (3, 4, 5, 2), (0, 1, 5, 4), (0, 4, 3), (1, 2, 5)):
            bm.faces.new([v[i] for i in f])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        b = min(bevel, sx / 3, sy / 3, sz / 3)
        if b > 0.004:
            bmesh.ops.bevel(bm, geom=list(bm.edges), offset=b, segments=1, affect="EDGES")
    else:
        raise ValueError(shape)
    return bm


def part(name, shape, size, pos, color, mat="Plastic", rot=None, look=None, bevel=0.05, alpha=0.35,
         glow=5.0, collide=True, record=True, cname=None, variant="LegoSquaresSoft"):
    """Деталь Roblox. size — (X, Y, Z) Roblox, pos — центр, rot — матрица 3 × 3 (оси Roblox). look — материал Blender
    вместо обычного (например, rings) — только для вида; в выгрузку идёт color/mat."""
    rot = rot or ID
    bm = _bm_shape(shape, size, bevel)
    m4 = (A.to_4x4() @ Matrix.Translation(Vector(pos)) @ rot.to_4x4())
    bmesh.ops.transform(bm, matrix=m4, verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if shape == "Ball":
        for p in me.polygons:
            p.use_smooth = True
    elif shape == "Cylinder":  # гладкая боковая поверхность, торцы и фаски — плоские
        axis = (A @ rot @ Vector((1, 0, 0))).normalized()
        for p in me.polygons:
            p.use_smooth = abs(p.normal.dot(axis)) < 0.2
    if look is not None:
        material = look
    elif mat == "Neon":
        material = neon(color, glow)
    elif mat == "Glass":
        material = glassm(color, alpha)
    else:
        material = flat(color)
    me.materials.append(material)
    obj = bpy.data.objects.new(name, me)
    coll(cname or S["group"]).objects.link(obj)
    S["tris"] += sum(len(p.vertices) - 2 for p in me.polygons)
    if record:
        r = rot
        S["bricks"].append({
            "group": S["group"], "name": name, "shape": shape, "size": [round(v, 3) for v in size],
            "cframe": [round(v, 3) for v in pos] + [round(r[i][j], 4) for i in range(3) for j in range(3)],
            "color": color, "material": mat, "variant": variant if mat == "Plastic" else None,
            "transparency": round(1 - alpha, 2) if mat == "Glass" else 0, "collide": collide,
        })
    return obj


def box(name, x0, x1, y0, y1, z0, z1, color, mat="Plastic", **kw):
    """Блок по границам (оси Roblox)."""
    return part(name, "Block", (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)),
                ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), color, mat, **kw)


AXIS = {"x": ID, "y": rot_z(90), "z": rot_y(-90)}


def cyl(name, center, length, diameter, color, axis="y", mat="Plastic", **kw):
    """Цилиндр Roblox с осью вдоль x / y / z участка."""
    rot = kw.pop("rot", None)
    r = AXIS[axis] if rot is None else rot @ AXIS[axis]
    return part(name, "Cylinder", (length, diameter, diameter), center, color, mat, rot=r, **kw)


def ball(name, center, diameter, color, mat="Plastic", **kw):
    return part(name, "Ball", (diameter, diameter, diameter), center, color, mat, **kw)


def wedge(name, size, center, color, rot=None, mat="Plastic", **kw):
    return part(name, "Wedge", size, center, color, mat, rot=rot, **kw)


# ── Надписи, свет, фигуры ──────────────────────────────────────────────────────────────────────────────────────
def font_path(weight="Black"):
    path = None
    for p in sorted(glob.glob(os.path.expandvars(rf"%LOCALAPPDATA%\Roblox\Versions\*\content\fonts\Montserrat-{weight}.ttf"))):
        path = p
    return path


def text(name, body, pos, size, color, face="-z", glow=None, weight="Black", align="CENTER", cname=None):
    """Надпись лицом к −z / +z / −x / +x / up (в игре — SurfaceGui на табличке, отдельной детали не нужно)."""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = 0.015
    cu.align_x = align
    cu.align_y = "CENTER"
    fp = font_path(weight)
    if fp:
        cu.font = bpy.data.fonts.load(fp, check_existing=True)
    obj = bpy.data.objects.new(name, cu)
    obj.data.materials.append(neon(color, glow) if glow else flat(color, 0.4))
    obj.location = R(*pos)
    obj.rotation_euler = {"+z": (math.radians(90), 0, 0), "-z": (math.radians(90), 0, math.radians(180)),
                          "+x": (math.radians(90), 0, math.radians(90)), "-x": (math.radians(90), 0, math.radians(-90)),
                          "up": (0, 0, math.radians(180))}[face]
    coll(cname or S["group"]).objects.link(obj)
    return obj


def light(name, kind, pos, energy, color="FFFFFF", size=2.0, target=None, spot=60, shadow=True, cname="Lights"):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    data.use_shadow = shadow
    data.color = lin(color)
    if kind == "AREA":
        data.size = size
    elif kind == "SPOT":
        data.spot_size = math.radians(spot)
        data.spot_blend = 0.55
        data.shadow_soft_size = 0.3
    elif kind == "POINT":
        data.shadow_soft_size = size
    obj = bpy.data.objects.new(name, data)
    obj.location = R(*pos)
    aim = R(*(target or (pos[0], pos[1] - 10, pos[2])))
    obj.rotation_euler = (obj.location - aim).to_track_quat("Z", "Y").to_euler()
    coll(cname).objects.link(obj)
    return obj


GAME_LIGHTS = []


def game_light(kind, pos, rng, brightness, color, angle=None):
    """Свет, который будет в игре (PointLight / SpotLight в детали) — для бюджета; рендер освещают light()."""
    GAME_LIGHTS.append({"group": S["group"], "kind": kind, "pos": [round(v, 2) for v in pos], "range": rng,
                        "brightness": brightness, "color": color, "angle": angle})


def mannequin(x, z, face=0.0, y=0.0, shirt="4F86F7", cname="People"):
    """Блочный игрок Roblox (рост ≈ 5.2) для масштаба; в выгрузку не идёт."""
    parts = [((0, 4.6, 0), (1.15, 1.15, 1.15), "F5C99B"), ((0, 3.15, 0), (2.0, 1.75, 1.0), shirt),
             ((-1.5, 3.15, 0), (0.95, 1.75, 0.95), "F5C99B"), ((1.5, 3.15, 0), (0.95, 1.75, 0.95), "F5C99B"),
             ((-0.5, 1.15, 0), (0.95, 2.3, 0.95), "2E3B55"), ((0.5, 1.15, 0), (0.95, 2.3, 0.95), "2E3B55")]
    rot = rot_y(math.degrees(face))
    for (px, py, pz), size, col in parts:
        p = rot @ Vector((px, py, pz))
        part("Mannequin", "Block", size, (x + p.x, y + p.y, z + p.z), col, rot=rot, bevel=0.06, record=False,
             cname=cname)


def sky(horizon="C9E4FF", top="57AEFF", strength=0.7):
    """Мир: камера видит яркое небо, освещение — мягкое светлое (как дневной свет Roblox)."""
    world = bpy.data.worlds.new("Sky")
    world.use_nodes = True
    wt = world.node_tree
    bg = next(n for n in wt.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (*lin(horizon), 1)
    bg.inputs["Strength"].default_value = strength
    sk = wt.nodes.new("ShaderNodeBackground")
    sk.inputs["Color"].default_value = (*lin(top), 1)
    sk.inputs["Strength"].default_value = 1.0
    mix = wt.nodes.new("ShaderNodeMixShader")
    path = wt.nodes.new("ShaderNodeLightPath")
    out = next(n for n in wt.nodes if n.type == "OUTPUT_WORLD")
    wt.links.new(path.outputs["Is Camera Ray"], mix.inputs["Fac"])
    wt.links.new(bg.outputs["Background"], mix.inputs[1])
    wt.links.new(sk.outputs["Background"], mix.inputs[2])
    wt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    S["scene"].world = world
    return world


def sun(energy=3.6, elev=52, azim=-35):
    s = bpy.data.lights.new("Sun", "SUN")
    s.energy = energy
    s.angle = math.radians(4)
    o = bpy.data.objects.new("Sun", s)
    o.rotation_euler = (math.radians(elev), 0, math.radians(azim))
    coll("Lights").objects.link(o)
    return o


# ── Камера ──────────────────────────────────────────────────────────────────────────────────────────────────────
def camera():
    data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", data)
    S["scene"].collection.objects.link(cam)
    S["scene"].camera = cam
    data.clip_end = 800
    data.clip_start = 0.05
    S["cam"] = cam
    return cam


def show_only(hidden=(), shown=None):
    for name, c in S["coll"].items():
        hide = name in hidden or (shown is not None and name not in shown and name != "Lights")
        c.hide_render = hide
        c.hide_viewport = hide


def shot(path, eye, at, fov=70, res=(1600, 900), ortho=None, percent=100, transparent=False, top_down=False):
    scene, cam = S["scene"], S["cam"]
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = percent
    scene.render.film_transparent = transparent
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho
    else:
        cam.data.type = "PERSP"
        cam.data.sensor_fit = "VERTICAL" if res[0] >= res[1] else "HORIZONTAL"
        cam.data.angle = math.radians(fov)
    cam.location = R(*eye)
    if top_down:
        cam.rotation_euler = (0, 0, math.pi)
    else:
        cam.rotation_euler = (R(*eye) - R(*at)).to_track_quat("Z", "Y").to_euler()
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("render", path, flush=True)
    return path


# ── Учёт и выгрузка ─────────────────────────────────────────────────────────────────────────────────────────────
def counts():
    out = {}
    for b in S["bricks"]:
        out[b["group"]] = out.get(b["group"], 0) + 1
    return out


def export(path, extra=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {"units": "studs, Roblox axes (y up, entrance −Z)", "counts": counts(), "total": len(S["bricks"]),
            "lights": GAME_LIGHTS, "bricks": S["bricks"]}
    if extra:
        data.update(extra)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("export", path, data["counts"], "total", data["total"], flush=True)
