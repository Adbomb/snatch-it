"""Король-дракон №10, этап C: запечённые карты D39 и FBX для загрузки в Roblox (модель v7, клипы anim5 — те же
суставы, что в Boss10_Dragon.rig.json этапа A).

Геометрия, палитра и кольца D39 — из утверждённой сборки (v7_rig.py → v7_dragon.py), ничего не меняется: здесь только
развёртка, запекание и раскладка по файлам.

Карты — 6 атласов 1024² (цвет с окклюзией и нормали, как art_style.bake с настройками эталона D39V2: запекание
крупнее в 4 раза и сжатие, острова по сетке текселей, угол проекции 66°). Одна MeshPart в Roblox — одна карта, а
корпус (часть Body) по площади больше трети дракона, поэтому он делится на две меши: Body (левая половина, x ≥ 0)
и Body_2 (правая), Body_2 приварена к суставу Body. Группы карт:
- BodyA, BodyB — половины корпуса;
- Head — голова и челюсть;
- Front — шея, воротник, плечи, передние лапы, наплечники, полосы мантии;
- Hind — задние лапы и скипетр;
- Tail — хвост, кости крыльев, перепонки.
Окклюзия — только своя у каждой части (части разнесены на целое число шагов колец, рисунок не сдвигается).

Глаза в Blender меняют материал (канал eyes: 0 — закрыты, цвет чешуи 43258F; 1 — горят янтарём FFB020), поэтому
грани глаз — отдельные меши EyeL / EyeR без карты (в игре Neon, цвет по каналу клипа), приварены к суставу Head.

Пишет:
- assets/textures/art/boss10/Boss10_<группа>_color.png, _normal.png;
- assets/models/Boss10_Dragon_game.fbx — 52 части суставов + Body_2 + EyeL + EyeR (меш от точки вращения сустава,
  стады, развёртка, без картинок);
- assets/models/Boss10_Dragon_wings_game.fbx — две перепонки одной мешью со скелетом крыльев (Root, Body, WingArm,
  WingFore, Finger1–4 обеих сторон; имена костей = имена суставов игры), веса ≤ 2 кости на вершину, стады;
- assets/models/Boss10_Dragon_game.json — группы карт частей, габариты мешей от точки вращения (оси Roblox),
  добавочные меши, кости перепонок в покое, плотность текселей;
- <папка>/preview_*.png — запечённая модель в позе боевой стойки рядом с исходными материалами (та же камера).

  blender --background --factory-startup --python scripts/blender/dragon10/v7_game_export.py -- <репо> <папка> bake
  … -- <репо> <папка> eyes — только канал глаз по клипам (assets/models/Boss10_Dragon.eyes.json)
"""

import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import art_style as S  # noqa: E402
import v7_anim5 as A  # noqa: E402

ck = A.ck

AX = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))  # Blender → Roblox
SC = A.STUDS
MODELS = os.path.join(A.REPO, "assets", "models")
TEXDIR = os.path.join(A.REPO, "assets", "textures", "art", "boss10")
SS = int(os.environ.get("BAKE_SS", "4"))
ANGLE = 66.0
MARGIN = 0.003
REGIONS = ["BodyA", "BodyB", "Head", "Front", "Hind", "Tail"]
WING_BONES = ["Root", "Body", "WingArm.L", "WingFore.L", "Finger1.L", "Finger2.L", "Finger3.L", "Finger4.L",
              "WingArm.R", "WingFore.R", "Finger1.R", "Finger2.R", "Finger3.R", "Finger4.R"]
EYE_OPEN, EYE_CLOSED = "FFB020", "43258F"


def rname(n):
    return n.replace(".", "")


def region_of(bone):
    if bone in ("Head", "Jaw"):
        return "Head"
    if bone.startswith(("Neck", "Collar", "UpperArm", "Forearm", "Paw.", "Pauldron", "Mantle")):
        return "Front"
    if bone.startswith(("Thigh", "Shin", "Meta", "HindPaw", "Scepter")):
        return "Hind"  # и скипетр: кольца круга — крупные пустые острова, в атласе крыльев места мало
    if bone.startswith(("Tail", "WingArm", "WingFore", "Finger", "Membrane")):
        return "Tail"
    raise KeyError(bone)


def mat_key(mat):
    return mat.name.split("_", 1)[-1] if mat else ""


# ── сборка в одну меш для запекания ───────────────────────────────────────────────────────────────────────────
def combined(rig):
    """Дракон + скипетр одной мешью (поза покоя). Возвращает объект и группу (кость) каждой грани."""
    arm = rig["arm"]
    arm.data.pose_position = "REST"
    dragon, scep = rig["dragon"], rig["scepter"]
    groups = list(rig["art"].face_groups)
    names = {g.index: g.name for g in scep.vertex_groups}
    for poly in scep.data.polygons:
        gs = [g for g in scep.data.vertices[poly.vertices[0]].groups if g.weight > 0.5]
        groups.append(names[gs[0].group])
    n0 = len(dragon.data.polygons)
    bpy.ops.object.select_all(action="DESELECT")
    scep.select_set(True)
    dragon.select_set(True)
    bpy.context.view_layer.objects.active = dragon
    bpy.ops.object.join()
    assert len(dragon.data.polygons) == len(groups), (len(dragon.data.polygons), len(groups), n0)
    return dragon, groups


def unlink_drivers(mats):
    """Свечение глаз и кристалла скипетра в сборке идёт через драйвер (×GLOW): для запекания цвета — сила 1."""
    for m in mats:
        nt = m.node_tree
        b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b is None:
            continue
        for link in list(nt.links):
            if link.to_socket == b.inputs["Emission Strength"]:
                nt.links.remove(link)
        b.inputs["Emission Strength"].default_value = 1.0


def explode(obj, groups, sign):
    """Части врозь по x на 10 шагов колец (рисунок колец не сдвигается): окклюзия — только своя."""
    order = {g: i for i, g in enumerate(dict.fromkeys(groups))}
    me = obj.data
    done = set()
    for poly in me.polygons:
        dx = order[groups[poly.index]] * 10 * S.RING["step"] * sign
        for v in poly.vertices:
            if v not in done:
                me.vertices[v].co.x += dx
                done.add(v)


def unwrap(obj, region):
    """Развёртка по группам: у каждой группы свой атлас 0…1 (Smart UV 66°, острова по сетке, упаковка 90°)."""
    S._select_only(obj)
    scene = bpy.context.scene
    scene.tool_settings.use_uv_select_sync = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_mode(type="FACE")
    me = obj.data

    def select(r):
        bm = bmesh.from_edit_mesh(me)
        bm.faces.ensure_lookup_table()
        for seq in (bm.verts, bm.edges, bm.faces):
            for e in seq:
                e.select = False
        for f in bm.faces:
            if region[f.index] == r:
                f.select_set(True)
        bmesh.update_edit_mesh(me)

    for r in REGIONS:
        select(r)
        bpy.ops.uv.smart_project(angle_limit=math.radians(ANGLE), island_margin=0.0, area_weight=0.0,
                                 scale_to_bounds=False)
    S._align_islands(obj)
    for r in REGIONS:
        select(r)
        bpy.ops.uv.pack_islands(rotate=True, rotate_method="CARDINAL", margin_method="FRACTION", margin=MARGIN,
                                shape_method="CONCAVE")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.object.mode_set(mode="OBJECT")


def region_materials(obj, region):
    """Копия материала на каждую пару (материал, группа карт): у копии своя цель запекания."""
    me = obj.data
    copies = {}
    idx = np.zeros(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get("material_index", idx)
    base = list(me.materials)
    for poly in me.polygons:
        r = region[poly.index]
        if r is None:
            continue
        key = (poly.material_index, r)
        if key not in copies:
            m = base[poly.material_index].copy()
            m.name = f"{base[poly.material_index].name}@{r}"
            me.materials.append(m)
            copies[key] = len(me.materials) - 1
        idx[poly.index] = copies[key]
    me.polygons.foreach_set("material_index", idx)
    me.update()
    return {k: me.materials[i] for k, i in copies.items()}


def bake(obj, copies):
    """Цвет (эмиссия) и нормали — в карту SS×, окклюзия — 1×; итог как art_style.bake. Пишет PNG по группам."""
    scene = bpy.context.scene
    S._select_only(obj)
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.world = scene.world or bpy.data.worlds.new("Bake")
    scene.world.light_settings.distance = 0.5
    scene.render.bake.use_clear = True
    by_region = {}
    for (_, r), m in copies.items():
        by_region.setdefault(r, []).append(m)
    # материалы без атласа (глаза, исходные до копий): цель — пустышка, иначе Cycles не запекает
    dummy = bpy.data.images.new("BakeDummy", 64, 64, alpha=False, float_buffer=True)
    used = {m.name for ms in by_region.values() for m in ms}
    for m in obj.data.materials:
        if m.name not in used and "BakeTarget" in m.node_tree.nodes:
            m.node_tree.nodes["BakeTarget"].image = dummy
            m.node_tree.nodes.active = m.node_tree.nodes["BakeTarget"]

    def run(kind):
        k = 1 if kind == "ao" else SS
        size = S.TEX * k
        scene.render.bake.margin = 8 * k
        imgs = {r: bpy.data.images.new(f"{r}_{kind}", size, size, alpha=False, float_buffer=True) for r in REGIONS}
        for r, mats in by_region.items():
            for m in mats:
                t = m.node_tree.nodes["BakeTarget"]
                t.image = imgs[r]
                m.node_tree.nodes.active = t
                b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
                b.inputs["Emission Strength"].default_value = 1.0 if kind == "color" else 0.0
        scene.cycles.samples = {"color": 4, "ao": 64, "normal": 8}[kind]
        if kind == "normal":
            bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
        else:
            bpy.ops.object.bake(type="EMIT" if kind == "color" else "AO")
        out = {}
        for r, img in imgs.items():
            arr = np.empty(size * size * 4, np.float32)
            img.pixels.foreach_get(arr)
            bpy.data.images.remove(img)
            out[r] = S._downsample(arr.reshape(size, size, 4)[::-1, :, :3], k, unit=kind == "normal")
        print("BAKED", kind, flush=True)
        return out

    color, ao, normal = run("color"), run("ao"), run("normal")
    os.makedirs(TEXDIR, exist_ok=True)
    paths = {}
    for r in REGIONS:
        c = S.to_srgb(color[r] * (S.AO_MIX + (1 - S.AO_MIX) * ao[r][..., :1]))
        paths[r] = {"color": os.path.join(TEXDIR, f"Boss10_{r}_color.png"),
                    "normal": os.path.join(TEXDIR, f"Boss10_{r}_normal.png")}
        S._save_png(paths[r]["color"], c)
        S._save_png(paths[r]["normal"], normal[r])
    return paths


def final_materials(obj, region, paths, eye_mats):
    """Материал на группу карт (цвет + нормали, как увидит Roblox); глаза — свой светящийся материал."""
    me = obj.data
    finals = {}
    for r in REGIONS:
        m = bpy.data.materials.new(f"Final_{r}")
        m.use_nodes = True
        nt = m.node_tree
        b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Roughness"].default_value = 0.5
        for kind, path in paths[r].items():
            t = nt.nodes.new("ShaderNodeTexImage")
            t.image = bpy.data.images.load(path)
            t.image.colorspace_settings.name = "sRGB" if kind == "color" else "Non-Color"
            if kind == "normal":
                nm = nt.nodes.new("ShaderNodeNormalMap")
                nt.links.new(t.outputs["Color"], nm.inputs["Color"])
                nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
            else:
                nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
        finals[r] = m
    old = list(me.materials)
    old_idx = np.zeros(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get("material_index", old_idx)  # clear() сбрасывает номера материалов граней
    me.materials.clear()
    for r in REGIONS:
        me.materials.append(finals[r])
    eye_index = {}
    for m in eye_mats:
        me.materials.append(m)
        eye_index[m.name] = len(me.materials) - 1
    idx = []
    for poly in me.polygons:
        r = region[poly.index]
        if r is None:
            idx.append(eye_index[old[old_idx[poly.index]].name])
        else:
            idx.append(REGIONS.index(r))
    me.polygons.foreach_set("material_index", idx)
    me.update()


def texel_stats(obj, region):
    me = obj.data
    me.calc_loop_triangles()
    uv = me.uv_layers.active.data
    acc = {r: [0.0, 0.0] for r in REGIONS}
    for lt in me.loop_triangles:
        r = region[lt.polygon_index]
        if r is None:
            continue
        a, b, c = (Vector(uv[i].uv) for i in lt.loops)
        acc[r][0] += abs((b - a).cross(c - a)) / 2
        acc[r][1] += lt.area
    out = {}
    for r, (uva, surf) in acc.items():
        tpu = S.TEX * math.sqrt(uva / surf) if surf else 0
        out[r] = {"uv_fill": round(uva, 3), "area_units": round(surf, 1), "texels_per_unit": round(tpu, 1),
                  "texels_per_stud": round(tpu / SC, 1), "ring_line_texels": round(tpu * S.RING["width"], 2)}
    return out


# ── части для FBX ────────────────────────────────────────────────────────────────────────────────────────────
def piece(src, polys, name, pivot):
    """Новый объект из граней polys меши src: начало координат — pivot (точка вращения), стады."""
    bm = bmesh.new()
    bm.from_mesh(src.data)
    bm.faces.ensure_lookup_table()
    keep = set(polys)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    dl = bm.verts.layers.deform.active
    if dl is not None:
        bm.verts.layers.deform.remove(dl)  # веса исходной меши (её номера групп) — не переносить
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in src.data.materials:
        me.materials.append(m)
    me.transform(Matrix.Translation(-pivot))
    me.transform(Matrix.Scale(SC, 4))
    o = bpy.data.objects.new(name, me)
    o.location = pivot * SC
    bpy.context.scene.collection.objects.link(o)
    return o


def bounds_rbx(o):
    """Габарит меша от точки вращения в осях Roblox (стады): центр и размер."""
    co = [AX @ v.co for v in o.data.vertices]
    lo = Vector([min(c[i] for c in co) for i in range(3)])
    hi = Vector([max(c[i] for c in co) for i in range(3)])
    return [round(x, 4) for x in (lo + hi) / 2], [round(x, 4) for x in hi - lo]


def tris(o):
    o.data.calc_loop_triangles()
    return len(o.data.loop_triangles)


def export(objs, path, armature=False):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    kw = dict(filepath=path, use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
              axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP")
    if armature:
        kw.update(object_types={"ARMATURE", "MESH"}, add_leaf_bones=False, bake_anim=False,
                  use_armature_deform_only=False)
    else:
        kw.update(object_types={"MESH"})
    bpy.ops.export_scene.fbx(**kw)


def wing_rig(src, groups, arm):
    """Перепонки одной мешью и укороченный скелет крыльев (стады, имена костей = суставы игры)."""
    polys = [i for i, g in enumerate(groups) if g and g.startswith("Membrane")]
    mem = piece(src, polys, "WingMembranes", Vector((0, 0, 0)))
    mem.location = (0, 0, 0)
    # группы вершин (веса) — с исходной меши: piece() их не переносит, переносим по совпадению координат
    src_me = src.data
    vg_names = {g.index: g.name for g in src.vertex_groups}
    index = {}
    for poly in polys:
        for vi in src_me.polygons[poly].vertices:
            co = (src_me.vertices[vi].co * SC).freeze()
            index[(round(co.x, 4), round(co.y, 4), round(co.z, 4))] = vi
    groups_out = {}
    for v in mem.data.vertices:
        vi = index[(round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4))]
        ws = [(vg_names[g.group], g.weight) for g in src_me.vertices[vi].groups if g.weight > 1e-4]
        total = sum(w for _, w in ws)
        for n, w in ws:
            assert n in WING_BONES, n
            g = groups_out.get(n) or mem.vertex_groups.new(name=rname(n))
            groups_out[n] = g
            g.add([v.index], w / total, "REPLACE")
    # скелет: копия арматуры, лишние кости удалены, масштаб в стады
    a2 = arm.copy()
    a2.data = arm.data.copy()
    a2.name = a2.data.name = "WingRig"
    bpy.context.scene.collection.objects.link(a2)
    a2.animation_data_clear()
    for o in list(a2.children):
        o.parent = None
    S._select_only(a2)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = a2.data.edit_bones
    for b in list(eb):
        if b.name not in WING_BONES:
            eb.remove(b)
    for b in eb:
        b.name = rname(b.name)
    bpy.ops.object.mode_set(mode="OBJECT")
    a2.data.pose_position = "REST"
    a2.scale = (SC, SC, SC)
    a2.location = (0, 0, 0)
    a2.rotation_euler = (0, 0, 0)
    S._select_only(a2)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    mod = mem.modifiers.new("Armature", "ARMATURE")
    mod.object = a2
    mem.parent = a2
    bones = {}
    for b in a2.data.bones:
        m = b.matrix_local  # кость в покое, стады, оси Blender (Y кости — вдоль кости)
        R3 = AX @ m.to_3x3() @ AX.transposed()
        bones[b.name] = {"parent": b.parent.name if b.parent else None,
                         "head": [round(x, 4) for x in AX @ m.translation],
                         "rot": [round(R3[i][j], 6) for i in range(3) for j in range(3)]}
    per_vertex = [sum(1 for g in v.groups if g.weight > 1e-4) for v in mem.data.vertices]
    gname = {g.index: g.name for g in mem.vertex_groups}
    for v in mem.data.vertices:
        if per_vertex[v.index] > 2:
            print("INFL", v.index, [(gname[g.group], round(g.weight, 3)) for g in v.groups], flush=True)
    return mem, a2, bones, max(per_vertex)


def main():
    col, rig = A.setup()
    rg = A.Rig(rig["arm"])
    rg.samples = A.leg_samples(rig)
    rg.rig = rig
    arm = rig["arm"]
    # поза для контрольного рендера — до склейки (доводка касаний меряет меши дракона и скипетра)
    clip = next(c for c in A.CLIPS if c().name == "combat_idle")()
    pose0 = A.clip_frames(rg, clip)[1][0]
    eye_mats = [m for m in rig["art"].materials if mat_key(m) == "neonEye"]
    unlink_drivers([m for m in list(rig["art"].materials) + list(rig["sart"].materials)
                    if mat_key(m) in ("neonEye", "neonCrystal")])
    obj, groups = combined(rig)
    me = obj.data
    region = []
    middle = []  # грани корпуса на средней линии — в ту половину, где площадь меньше (по длине тела)
    area = {"BodyA": 0.0, "BodyB": 0.0}
    for poly, g in zip(me.polygons, groups):
        key = mat_key(me.materials[poly.material_index])
        if key == "neonEye":
            region.append(None)
        elif g == "Body":
            x = poly.center.x
            if abs(x) < 1e-3:
                middle.append(poly.index)
                region.append("BodyA")
            else:
                r = "BodyA" if x > 0 else "BodyB"
                area[r] += poly.area
                region.append(r)
        else:
            region.append(region_of(g))
    for i in sorted(middle, key=lambda i: me.polygons[i].center.y):
        r = min(area, key=area.get)
        region[i] = r
        area[r] += me.polygons[i].area
    print("REGIONS", {r: region.count(r) for r in REGIONS + [None]}, flush=True)
    copies = region_materials(obj, region)
    explode(obj, groups, 1)
    unwrap(obj, region)
    paths = bake(obj, copies)
    explode(obj, groups, -1)
    stats = texel_stats(obj, region)
    print("TEXELS", json.dumps(stats), flush=True)
    final_materials(obj, region, paths, eye_mats)

    # контрольный рендер: запечённая модель в боевой стойке — та же камера, что в роликах anim4/anim5
    cam = A.stage(col)
    arm.data.pose_position = "POSE"
    for view in ("34", "front", "back", "sideL"):
        A.show(rg, rig, *pose0)
        eye, target, lens = A.VIEWS[view]
        ck.shot(cam, os.path.join(A.OUT, f"preview_baked_{view}.png"), eye, target, lens, (1280, 720))
    arm.data.pose_position = "REST"

    # части по суставам (+ половина корпуса и глаза)
    by = {}
    for i, (g, r) in enumerate(zip(groups, region)):
        if g.startswith("Membrane"):
            continue
        if r is None:
            name = "EyeL" if me.polygons[i].center.x >= 0 else "EyeR"
        elif r == "BodyB":
            name = "Body_2"
        else:
            name = rname(g)
        by.setdefault(name, []).append(i)
    bone_of = {rname(b.name): b.name for b in arm.data.bones}
    extras_joint = {"Body_2": "Body", "EyeL": "Head", "EyeR": "Head"}
    parts, info, extras = [], {}, {}
    for name, polys in by.items():
        joint = extras_joint.get(name, name)
        pivot = arm.data.bones[bone_of[joint]].head_local
        o = piece(obj, polys, name, pivot)
        center, size = bounds_rbx(o)
        rec = {"center": center, "size": size, "tris": tris(o)}
        if name in extras_joint:
            rec.update(joint=joint, map=("BodyB" if name == "Body_2" else None),
                       eye=(name.startswith("Eye") and {"open": EYE_OPEN, "closed": EYE_CLOSED} or None))
            extras[name] = rec
        else:
            rec["map"] = region[polys[0]]
            info[name] = rec
        parts.append(o)
    export(parts, os.path.join(MODELS, "Boss10_Dragon_game.fbx"))
    print("FBX_PARTS", len(parts), sum(tris(o) for o in parts), flush=True)

    mem, wing_arm, bones, max_infl = wing_rig(obj, groups, arm)
    mc, ms = bounds_rbx(mem)
    export([wing_arm, mem], os.path.join(MODELS, "Boss10_Dragon_wings_game.fbx"), armature=True)
    print("FBX_WINGS", len(mem.data.vertices), tris(mem), "infl", max_infl, flush=True)

    out = {
        "scale": SC, "regions": REGIONS, "texels": stats, "maps": {r: {k: os.path.relpath(p, A.REPO).replace("\\", "/")
                                                                        for k, p in paths[r].items()} for r in REGIONS},
        "parts": info, "extras": extras,
        "membranes": {"mesh": "WingMembranes", "center": mc, "size": ms, "tris": tris(mem), "verts": len(mem.data.vertices),
                      "max_influences": max_infl, "map": "Tail", "bones": bones},
        "tris_total": sum(tris(o) for o in parts) + tris(mem),
    }
    with open(os.path.join(MODELS, "Boss10_Dragon_game.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("GAME_EXPORT_OK", out["tris_total"], flush=True)


def export_eyes():
    """Канал глаз по клипам игры (anim5, без «Разворота» — в игре шаг на месте, глаза открыты): точки изменения
    [t, значение] по кадрам 30/с → assets/models/Boss10_Dragon.eyes.json. Суставы клипов не пересчитываются."""
    col, rig = A.setup()
    rg = A.Rig(rig["arm"])
    rg.samples = A.leg_samples(rig)
    rg.rig = rig
    out = {}
    for make in A.CLIPS:
        clip = make()
        if clip.name == "turn_left":
            continue
        times, frames = A.clip_frames(rg, clip)
        vals = [round(float(p.get("eyes", 1.0)), 3) for p, _ in frames]
        if all(v == 1.0 for v in vals):
            continue
        keys = []
        for i, v in enumerate(vals):
            prev = vals[i - 1] if i else None
            nxt = vals[i + 1] if i + 1 < len(vals) else None
            if i == 0 or i == len(vals) - 1 or v != prev or v != nxt:
                keys.append([round(times[i], 4), v])
        out[clip.name] = keys
        print("EYES", clip.name, len(keys), flush=True)
    with open(os.path.join(MODELS, "Boss10_Dragon.eyes.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"open": EYE_OPEN, "closed": EYE_CLOSED, "clips": out}, f, ensure_ascii=False, indent=1)
    print("EYES_OK", len(out), flush=True)


if __name__ == "__main__":
    if A.MODE == "eyes":
        export_eyes()
    else:
        main()
