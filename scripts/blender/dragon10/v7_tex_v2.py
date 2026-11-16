"""Король-дракон №10, этап C.1: запекание вспомогательных карт для текстур версии 2 (объём и тени).

Берёт ровно те меши, что загружены в Roblox (assets/models/Boss10_Dragon_game.fbx и _wings_game.fbx: та же
развёртка, что у карт версии 1), собирает дракона в позе покоя и запекает в каждый из 6 атласов 1024²:
- ao_near — окклюзия всех частей вместе на 1.4 стада (щели между пластинами, под золотыми накладками, у суставов;
  в версии 1 окклюзия была только своя у каждой части);
- ao_far — та же окклюзия на 6 стадов (крупные формы: под брюхом, между лапами, под крыльями);
- geo — R: вертикальная составляющая нормали грани (0 — вниз, 1 — вверх), G: высота над полом, B: положение вдоль
  тела (0 — морда, 1 — кончик хвоста);
- nrm — нормаль грани целиком (xyz → 0…1, оси Blender: лицо дракона −Y) — для мягкого света сверху-спереди;
- ao_tight (этап C.2, текстуры v3) — окклюзия на 0.5 стада: щели между пластинами чешуи и края накладок;
- part (этап C.2) — номер части (меша сустава) в каждом пикселе: R = номер / 100; список — <папка>/parts.json.
Пишет <папка>/<группа>_<карта>.npy (float32, строки сверху вниз, как в PNG). Цвет версии 2 собирает
scripts/boss10_tex_v2.py; карты версии 1 и меши не меняются.

  blender --background --factory-startup --python scripts/blender/dragon10/v7_tex_v2.py -- <репо> <папка>
"""

import json
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
REPO, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
REGIONS = ["BodyA", "BodyB", "Head", "Front", "Hind", "Tail"]
TEX = 1024
AO_NEAR, AO_FAR, AO_TIGHT = 1.4, 6.0, 0.5  # стадов
SAMPLES = int(os.environ.get("TEX2_SAMPLES", "128"))


def region_of(mat):
    name = mat.name.split(".")[0] if mat else ""
    return name[len("Final_"):] if name.startswith("Final_") else None


def load():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for f in ("Boss10_Dragon_game.fbx", "Boss10_Dragon_wings_game.fbx"):
        bpy.ops.import_scene.fbx(filepath=os.path.join(REPO, "assets", "models", f))
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    names = sorted(o.name for o in meshes)
    for o in meshes:
        for m in list(o.modifiers):
            o.modifiers.remove(m)  # перепонки: поза покоя = поза привязки
        o.parent = None
        # номер части на каждой грани (для bake «part»): после склейки атрибут остаётся у граней
        attr = o.data.attributes.new("part", "FLOAT", "FACE")
        attr.data.foreach_set("value", [float(names.index(o.name))] * len(o.data.polygons))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "parts.json"), "w", encoding="utf-8") as f:
        json.dump(names, f)
    for o in [o for o in bpy.data.objects if o.type != "MESH"]:
        bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = next(o for o in meshes if o.name == "Body")
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def bake_materials(obj):
    """Материал на группу карт: цель запекания + свечение из геометрии (для geo); глаза — пустышка."""
    me = obj.data
    co = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    ymin, ymax = float(co[:, 1].min()), float(co[:, 1].max())
    zmax = float(co[:, 2].max())
    targets, mats = {}, {}
    for r in REGIONS + ["_dummy"]:
        m = bpy.data.materials.new("Bake_" + r)
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        emit = nt.nodes.new("ShaderNodeEmission")
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep_n = nt.nodes.new("ShaderNodeSeparateXYZ")
        sep_p = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(geo.outputs["Normal"], sep_n.inputs[0])
        nt.links.new(geo.outputs["Position"], sep_p.inputs[0])
        comb = nt.nodes.new("ShaderNodeCombineXYZ")

        def remap(sock, lo, hi):
            mr = nt.nodes.new("ShaderNodeMapRange")
            mr.inputs["From Min"].default_value = lo
            mr.inputs["From Max"].default_value = hi
            nt.links.new(sock, mr.inputs["Value"])
            return mr.outputs["Result"]

        nt.links.new(remap(sep_n.outputs["Z"], -1.0, 1.0), comb.inputs["X"])
        nt.links.new(remap(sep_p.outputs["Z"], 0.0, zmax), comb.inputs["Y"])
        nt.links.new(remap(sep_p.outputs["Y"], ymin, ymax), comb.inputs["Z"])
        nrm = nt.nodes.new("ShaderNodeCombineXYZ")
        nrm.name = "Nrm"
        for axis in "XYZ":
            nt.links.new(remap(sep_n.outputs[axis], -1.0, 1.0), nrm.inputs[axis])
        comb.name = "Geo"
        part = nt.nodes.new("ShaderNodeAttribute")
        part.attribute_name = "part"
        div = nt.nodes.new("ShaderNodeMath")
        div.operation = "DIVIDE"
        div.inputs[1].default_value = 100.0
        nt.links.new(part.outputs["Fac"], div.inputs[0])
        pid = nt.nodes.new("ShaderNodeCombineXYZ")
        pid.name = "Part"
        nt.links.new(div.outputs[0], pid.inputs["X"])
        nt.links.new(comb.outputs[0], emit.inputs["Color"])
        emit.inputs["Strength"].default_value = 1.0
        nt.links.new(emit.outputs[0], out.inputs["Surface"])
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.name = "BakeTarget"
        nt.nodes.active = tex
        targets[r] = tex
        mats[r] = m
    slot_region = [region_of(m) for m in me.materials]
    idx = np.zeros(len(me.polygons), np.int32)
    me.polygons.foreach_get("material_index", idx)
    me.materials.clear()
    for r in REGIONS + ["_dummy"]:
        me.materials.append(mats[r])
    order = REGIONS + ["_dummy"]
    new = [order.index(slot_region[i] or "_dummy") for i in idx]
    me.polygons.foreach_set("material_index", np.array(new, np.int32))
    me.update()
    print("FACES", {r: new.count(order.index(r)) for r in order}, flush=True)
    return targets


def bake(obj, targets, kind):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.world = scene.world or bpy.data.worlds.new("Bake")
    scene.render.bake.use_clear = True
    scene.render.bake.margin = 8
    imgs = {}
    for r in REGIONS:
        imgs[r] = bpy.data.images.new(f"{r}_{kind}", TEX, TEX, alpha=False, float_buffer=True)
        targets[r].image = imgs[r]
    targets["_dummy"].image = bpy.data.images.new("dummy", 32, 32, alpha=False, float_buffer=True)
    if kind in ("geo", "nrm", "part"):
        for m in bpy.data.materials:
            if m.name.startswith("Bake_"):
                nt = m.node_tree
                emit = next(n for n in nt.nodes if n.type == "EMISSION")
                node = {"geo": "Geo", "nrm": "Nrm", "part": "Part"}[kind]
                nt.links.new(nt.nodes[node].outputs[0], emit.inputs["Color"])
        scene.cycles.samples = 4
        bpy.ops.object.bake(type="EMIT")
    else:
        scene.world.light_settings.distance = {"ao_near": AO_NEAR, "ao_far": AO_FAR, "ao_tight": AO_TIGHT}[kind]
        scene.cycles.samples = SAMPLES
        bpy.ops.object.bake(type="AO")
    os.makedirs(OUT, exist_ok=True)
    for r, img in imgs.items():
        arr = np.empty(TEX * TEX * 4, np.float32)
        img.pixels.foreach_get(arr)
        arr = arr.reshape(TEX, TEX, 4)[::-1, :, :3]
        np.save(os.path.join(OUT, f"{r}_{kind}.npy"), arr if kind in ("geo", "nrm", "part") else arr[..., :1])
    print("BAKED", kind, flush=True)


def main():
    obj = load()
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    targets = bake_materials(obj)
    kinds = os.environ.get("TEX2_KINDS", "geo,nrm,ao_near,ao_far").split(",")
    for kind in kinds:
        bake(obj, targets, kind)
    print("TEX2_BAKE_OK", flush=True)


main()
