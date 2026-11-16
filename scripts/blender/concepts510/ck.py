"""Набор для концептов боссов 5–10 (этап концептов 2026-11-14, ТЗ владельца «Все шесть боссов №5–10 — единый цикл»).

Черновые блочные модели в стиле D39 только для картинок-концептов: детали и кольца D39 — из art_style.py (материалы
сборки, без запекания, без экспорта); в игру и в Roblox ничего не идёт. Здесь — общие детали (глаза, бруски, шары,
трубы, самоцветы), светящиеся материалы, студия и уличная сцена для арен, кадры.
Координаты как в art_style: z вверх, лицо смотрит в −y, 1 единица = 1 стад модели (босс в игре — ×3, как Сфинкс).
Зависит от Blender (bpy, bmesh) и scripts/blender/art_style.py.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import art_style as S  # noqa: E402

# Кольца D39 как у эталона v2 (профиль «полка»); у арен — крупнее (там пупырышки Roblox 1–2 стада).
RING_V2 = dict(S.RING, core=0.55)
RING_ARENA = {"step": 2.0, "size": 1.5, "rad": 0.32, "width": 0.09, "dark": 0.16, "core": 0.5}
GLOW = 6.0  # сила свечения неона


# ── Простые детали ────────────────────────────────────────────────────────────────────────────────────────────


def ngon(cx, cy, r, n=8, phase=None, sy=1.0):
    phase = math.pi / n if phase is None else phase
    return [(cx + r * math.cos(phase + 2 * math.pi * i / n), cy + sy * r * math.sin(phase + 2 * math.pi * i / n))
            for i in range(n)]


def disc(a, key, cx, cy, r, a0, a1, n=8, axis="z", bevel=S.BEVEL, matrix=None, sy=1.0):
    a.prism(key, ngon(cx, cy, r, n, sy=sy), a0, a1, axis=axis, bevel=bevel, matrix=matrix)


def bar(a, key, p0, p1, w, h=None, bevel=S.BEVEL):
    """Брусок от p0 до p1 сечением w × h."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    up = "Y" if abs(d.normalized().z) > 0.95 else "Z"
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("X", up).to_matrix().to_4x4()
    h = h or w
    a.box(key, -d.length / 2, d.length / 2, -w / 2, w / 2, -h / 2, h / 2, bevel=bevel, matrix=m)


def gem(a, key, c, size, turn=0.0):
    m = Matrix.Translation(c) @ Matrix.Rotation(math.radians(turn), 4, "Z") @ Matrix.Rotation(
        math.radians(45), 4, "X") @ Matrix.Rotation(math.radians(35), 4, "Y")
    h = size / 2
    a.box(key, -h, h, -h, h, -h, h, bevel=0, matrix=m)


def ball(a, key, c, r, n=5, flat=0.3, sy=1.0):
    """«Шар» D39 — стопка восьмигранников."""
    for k in range(n):
        z0 = -r + 2 * r * k / n
        z1 = -r + 2 * r * (k + 1) / n
        zm = (z0 + z1) / 2
        rr = max(math.sqrt(max(r * r - zm * zm, 0.0)), r * 0.35)
        a.prism(key, S.octagon(c[0] - rr, c[0] + rr, c[1] - rr * sy, c[1] + rr * sy, rr * flat),
                c[2] + z0 - (0.01 if k else 0), c[2] + z1 + 0.01)


def blob(a, key, c, rx, ry, rz, n=6, cut=0.38, z0=None, z1=None, matrix=None):
    """Эллипсоид ступенями D39: n ярусов-восьмигранников (полуоси rx, ry, rz) вокруг c; z0/z1 — обрезать снизу/сверху.
    Пухлые формы (живот, голова, лапы) без гладких примитивов."""
    lo = -rz if z0 is None else max(-rz, z0 - c[2])
    hi = rz if z1 is None else min(rz, z1 - c[2])
    for k in range(n):
        a0 = lo + (hi - lo) * k / n
        a1 = lo + (hi - lo) * (k + 1) / n
        zm = (a0 + a1) / 2
        f = math.sqrt(max(1 - (zm / rz) ** 2, 0.0))
        f = max(f, 0.42)
        wx, wy = rx * f, ry * f
        a.prism(key, S.octagon(c[0] - wx, c[0] + wx, c[1] - wy, c[1] + wy, min(wx, wy) * cut),
                c[2] + a0 - (0.008 if k else 0), c[2] + a1 + 0.008, matrix=matrix)


def tube(a, keys, pts, r, n=8, joints=True):
    """Труба из восьмигранных отрезков; в изгибах — короткие шарниры."""
    if isinstance(keys, str):
        keys = [keys]
    for i in range(len(pts) - 1):
        p0, p1 = Vector(pts[i]), Vector(pts[i + 1])
        d = p1 - p0
        m = Matrix.Translation(p0) @ d.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
        rr = r[i] if isinstance(r, (list, tuple)) else r
        a.prism(keys[i % len(keys)], ngon(0, 0, rr, n), 0.0, d.length, matrix=m)
        if joints and i > 0:
            a.prism(keys[i % len(keys)], ngon(0, 0, rr * 0.97, n), -rr * 0.55, rr * 0.55, bevel=0, matrix=m)


def eye(a, c, w, h=None, look=(0.0, 0.0), depth=0.12, lid=0.0, lid_key=None, white="white", iris=None):
    """Глаз лицом к −y: белок, зрачок (или радужка iris + зрачок), блик; lid — верхнее веко (доля высоты)."""
    x, y, z = c
    h = h or w
    a.box(white, x - w / 2, x + w / 2, y - depth, y + 0.02, z - h / 2, z + h / 2)
    pw = min(w, h) * 0.56
    px, pz = x + look[0] * (w - pw) / 2 * 0.8, z + look[1] * (h - pw) / 2 * 0.8
    if iris:
        a.box(iris, px - pw / 2, px + pw / 2, y - depth - 0.02, y - depth + 0.01, pz - pw / 2, pz + pw / 2, bevel=0)
        q = pw * 0.5
        a.box("dark", px - q / 2, px + q / 2, y - depth - 0.035, y - depth - 0.01, pz - q / 2, pz + q / 2, bevel=0)
    else:
        a.box("dark", px - pw / 2, px + pw / 2, y - depth - 0.03, y - depth + 0.01, pz - pw / 2, pz + pw / 2, bevel=0)
    g = pw * 0.3
    a.box("glint", px - pw / 2 + 0.02, px - pw / 2 + 0.02 + g, y - depth - 0.05, y - depth - 0.03,
          pz + pw / 2 - 0.02 - g, pz + pw / 2 - 0.02, bevel=0)
    if lid > 0:
        a.box(lid_key, x - w / 2 - 0.03, x + w / 2 + 0.03, y - depth - 0.07, y + 0.01, z + h / 2 - lid * h,
              z + h / 2 + 0.04, bevel=0.006)


def round_eye(a, c, r, look=(0.0, 0.0), pupil=0.6, depth=0.05, lid=0.0, lid_key=None, n=8, iris=None):
    x, y, z = c
    disc(a, "white", x, z, r, y - depth, y + 0.02, n=n, axis="y")
    pr = r * pupil
    px, pz = x + look[0] * (r - pr) * 0.85, z + look[1] * (r - pr) * 0.85
    if iris:
        disc(a, iris, px, pz, pr, y - depth - 0.02, y - depth + 0.01, n=n, axis="y", bevel=0)
        disc(a, "dark", px, pz, pr * 0.5, y - depth - 0.035, y - depth - 0.01, n=n, axis="y", bevel=0)
    else:
        disc(a, "dark", px, pz, pr, y - depth - 0.025, y - depth + 0.01, n=n, axis="y", bevel=0)
    g = pr * 0.38
    a.box("glint", px - pr * 0.55, px - pr * 0.55 + g, y - depth - 0.05, y - depth - 0.03, pz + pr * 0.15,
          pz + pr * 0.15 + g, bevel=0)
    if lid > 0:
        a.box(lid_key, x - r - 0.03, x + r + 0.03, y - depth - 0.06, y + 0.01, z + r - 2 * r * lid, z + r + 0.04,
              bevel=0.006)


def closed_eye(a, c, w, key="dark", happy=True):
    x, y, z = c
    if happy:
        bar(a, key, (x - w / 2, y - 0.02, z - w * 0.18), (x, y - 0.02, z + w * 0.16), 0.06, 0.05, bevel=0)
        bar(a, key, (x, y - 0.025, z + w * 0.16), (x + w / 2, y - 0.025, z - w * 0.18), 0.06, 0.05, bevel=0)
    else:
        a.box(key, x - w / 2, x + w / 2, y - 0.04, y + 0.01, z - 0.03, z + 0.03, bevel=0)


def tilt(c, axis, deg):
    c = Vector(c)
    return Matrix.Translation(c) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-c)


def mirror(fn):
    """Вызвать fn(s) для s = +1 и −1 (левая и правая стороны)."""
    for s in (1, -1):
        fn(s)


def octa(c, w, d, h0, h1, cut=0.3):
    """Восьмигранник по прямоугольнику w × d вокруг c (x, y) — для a.prism."""
    return S.octagon(c[0] - w / 2, c[0] + w / 2, c[1] - d / 2, c[1] + d / 2, cut), h0, h1


# ── Сборка, неон, сцены ───────────────────────────────────────────────────────────────────────────────────────


def new_art(name, ring=None, ring_z0=0.0):
    a = S.Art(name, ring_z0=ring_z0)
    a.ring = ring or RING_V2
    return a


def finish(a, collection, glow=GLOW):
    """Собрать меш; материалы с ключами neon* светятся."""
    obj = a.build(collection)
    for mat in a.materials:
        key = mat.name.split("_", 1)[-1]
        bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            continue
        if key.startswith("neon"):
            bsdf.inputs["Emission Strength"].default_value = glow
        elif key.startswith("glass"):
            bsdf.inputs["Transmission Weight"].default_value = 0.0
            bsdf.inputs["Roughness"].default_value = 0.15
        if key.startswith("metal"):
            bsdf.inputs["Metallic"].default_value = 0.35
            bsdf.inputs["Roughness"].default_value = 0.35
    return obj


def place(obj, loc=(0, 0, 0), rot_z=0.0, scale=1.0):
    obj.location = loc
    obj.rotation_euler = (0, 0, math.radians(rot_z))
    obj.scale = (scale, scale, scale)
    return obj


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    col = bpy.data.collections.new("Concept")
    bpy.context.scene.collection.children.link(col)
    return col


def engine(scene, samples=48):
    engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    try:
        scene.eevee.use_raytracing = True
        scene.eevee.taa_render_samples = samples
        scene.eevee.use_shadows = True
    except AttributeError:
        pass


def studio(collection, size=1.0, bg=(0.75, 0.78, 0.85), floor=(0.018, 0.022, 0.04)):
    """Тёмная студия как у эталонов (циклорама, три источника); size — масштаб сцены под высоту модели."""
    scene = bpy.context.scene
    engine(scene)
    world = bpy.data.worlds.new("Studio")
    world.use_nodes = True
    b = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    b.inputs["Color"].default_value = (*bg, 1)
    b.inputs["Strength"].default_value = 0.55
    scene.world = world
    me = bpy.data.meshes.new("Floor")
    k = size
    sweep = [(-80.0 * k, 0.0), (6.0 * k, 0.0)] + [(6.0 * k + 9 * k * math.sin(math.pi / 2 * i / 12),
                                                    9 * k - 9 * k * math.cos(math.pi / 2 * i / 12)) for i in range(1, 13)]
    sweep.append((15.0 * k, 60.0 * k))
    me.from_pydata([(x, y, z) for (y, z) in sweep for x in (-90.0 * k, 90.0 * k)], [],
                   [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(len(sweep) - 1)])
    for p in me.polygons:
        p.use_smooth = True
    fm = bpy.data.materials.new("FloorM")
    fm.use_nodes = True
    fb = next(n for n in fm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    fb.inputs["Base Color"].default_value = (*floor, 1)
    fb.inputs["Roughness"].default_value = 0.6
    me.materials.append(fm)
    collection.objects.link(bpy.data.objects.new("Floor", me))
    for name, loc, energy, sz in (("Key", (-5, -9, 9), 1900, 7), ("Fill", (7, -6, 4), 900, 8),
                                  ("Rim", (2, 8, 7), 1600, 6)):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.size = energy * k * k, sz * k
        light = bpy.data.objects.new(name, data)
        light.location = Vector(loc) * k
        light.rotation_euler = (light.location - Vector((0, 0, 1.5 * k))).to_track_quat("Z", "Y").to_euler()
        scene.collection.objects.link(light)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    return cam


def outdoor(sky_top, sky_bottom, sun_color=(1, 0.97, 0.9), sun_energy=3.5, sun_dir=(-35, 0, 40), ambient=0.9):
    """Уличная сцена для арен: небо-градиент (по высоте взгляда), солнце; камера."""
    scene = bpy.context.scene
    engine(scene, samples=32)
    world = bpy.data.worlds.new("Sky")
    world.use_nodes = True
    nt = world.node_tree
    bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.45, 0.75
    ramp.color_ramp.elements[0].color = (*[c for c in S.lin(sky_bottom)], 1)
    ramp.color_ramp.elements[1].color = (*[c for c in S.lin(sky_top)], 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = ambient
    scene.world = world
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy, sun.data.color, sun.data.angle = sun_energy, sun_color, math.radians(8)
    sun.rotation_euler = [math.radians(v) for v in sun_dir]
    scene.collection.objects.link(sun)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    return cam


def shot(cam, path, eye, target, lens=50, res=(1200, 900), ortho=None):
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho
    else:
        cam.data.type = "PERSP"
        cam.data.lens = lens
    cam.data.clip_end = 2000
    cam.location = eye
    cam.rotation_euler = (Vector(eye) - Vector(target)).to_track_quat("Z", "Y").to_euler()
    scene.render.filepath = path
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    return path


def bounds(objs):
    co = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    lo = Vector([min(c[i] for c in co) for i in range(3)])
    hi = Vector([max(c[i] for c in co) for i in range(3)])
    return lo, hi


def turn_shots(cam, objs, out_dir, prefix, res=(800, 1000), lens=60):
    """Спереди, сбоку, сзади и 3/4 — поворотом модели (камера и свет стоят)."""
    lo, hi = bounds(objs)
    size = max(hi - lo)
    cz = (lo.z + hi.z) / 2
    dist = 1.95 * size + 1.0
    paths = {}
    for label, angle in (("front", 0), ("side", -90), ("back", 180), ("34", -35)):
        for o in objs:
            o.rotation_euler = (0, 0, math.radians(angle))
        p = os.path.join(out_dir, f"{prefix}_{label}.png")
        paths[label] = shot(cam, p, (0, -dist, cz + 0.22 * size), (0, 0, cz), lens, res)
    for o in objs:
        o.rotation_euler = (0, 0, 0)
    return paths
