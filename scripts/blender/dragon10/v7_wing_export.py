"""Король-дракон v7: проверка перепонок крыльев перед Roblox (вариант A — перепонки деформируются на костях).

1. Веса: у каждой вершины перепонки не больше 4 костей (предел Roblox для skinned mesh), сумма весов 1.
2. Деформация во всех клипах (каждый второй кадр): растяжение треугольников относительно покоя и вывернутые
   треугольники — перепонка не рвётся, не схлопывается и не выворачивается.
3. Экспорт FBX (арматура + только перепонки, действие «взмах крыльями») → обратный импорт → расхождение вершин
   с исходной деформацией на каждом третьем кадре (импорт сдвигает действие на кадр 1 — сравнение с учётом сдвига);
   и что ключи действия (положение и поворот костей) дают ту же форму, что решатель рига. Так проверяется, что веса и кости переживают FBX, через который модель
   пойдёт в Roblox.
Пишет <папка>/wing_check.json и <папка>/wing_membrane_test.fbx. Позы — из v7_anim4.py (те же клипы и доводка).

  blender --background --factory-startup --python scripts/blender/dragon10/v7_wing_export.py -- <репо> <папка> wing
"""

import json
import os
import sys

import bmesh
import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v7_anim4 as A  # noqa: E402

OUT = A.OUT
EVERY = int(os.environ.get("EVERY", "2"))


def membrane_polys(rig):
    art = rig["art"]
    return {x: [i for i, b in enumerate(art.face_groups) if b == "Membrane." + x] for x in "LR"}


def tri_areas(co, tris):
    a, b, c = co[tris[:, 0]], co[tris[:, 1]], co[tris[:, 2]]
    cr = np.cross(b - a, c - a)
    return 0.5 * np.linalg.norm(cr, axis=1), cr


def weights_report(obj, verts):
    names = {g.index: g.name for g in obj.vertex_groups}
    worst, bad_sum, bones = 0, 0, set()
    for vi in verts:
        gs = [(names[g.group], g.weight) for g in obj.data.vertices[vi].groups if g.weight > 1e-6]
        worst = max(worst, len(gs))
        bones.update(n for n, _ in gs)
        if abs(sum(w for _, w in gs) - 1.0) > 1e-3:
            bad_sum += 1
    return {"max_influences": worst, "weight_sum_not_1": bad_sum, "bones": sorted(bones)}


def main():
    col, rig = A.setup()
    rg = A.Rig(rig["arm"])
    rg.samples = A.leg_samples(rig)
    rg.rig = rig
    obj, arm = rig["dragon"], rig["arm"]
    me = obj.data
    mp = membrane_polys(rig)
    report = {"weights": {}, "deform": {}, "fbx": {}}
    tris, verts = {}, {}
    rest = np.array([v.co[:] for v in me.vertices])
    for x in "LR":
        vs = sorted({v for i in mp[x] for v in me.polygons[i].vertices})
        verts[x] = vs
        t = []
        for i in mp[x]:
            pv = list(me.polygons[i].vertices)
            for k in range(1, len(pv) - 1):
                t.append((pv[0], pv[k], pv[k + 1]))
        tris[x] = np.array(t)
        report["weights"][x] = dict(weights_report(obj, vs), verts=len(vs), tris=len(t))
    rest_area = {x: tri_areas(rest, tris[x])[0] for x in "LR"}
    rest_n = {x: tri_areas(rest, tris[x])[1] for x in "LR"}

    # 2. деформация во всех клипах (ONLY_FBX=1 — взять из прошлого wing_check.json)
    prev = os.path.join(OUT, "wing_check.json")
    if os.environ.get("ONLY_FBX") and os.path.exists(prev):
        report["deform"] = json.load(open(prev, encoding="utf-8"))["deform"]
    for make in ([] if os.environ.get("ONLY_FBX") and report["deform"] else A.CLIPS):
        clip = make()
        times, poses = A.clip_frames(rg, clip)
        worst = {"min_ratio": 9.0, "max_ratio": 0.0, "collapsed": 0, "flipped_frames": 0, "flipped_max": 0}
        for f in range(0, len(times), EVERY):
            A.show(rg, rig, *poses[f])
            co = A.eval_points(obj)
            for x in "LR":
                area, cr = tri_areas(co, tris[x])
                ratio = area / np.maximum(rest_area[x], 1e-9)
                worst["min_ratio"] = min(worst["min_ratio"], float(ratio.min()))
                worst["max_ratio"] = max(worst["max_ratio"], float(ratio.max()))
                worst["collapsed"] = max(worst["collapsed"], int((ratio < 0.15).sum()))
                # вывернутый треугольник: его нормаль смотрит против средней нормали своего крыла в этом кадре
                avg = cr.sum(axis=0)
                flipped = int(((cr @ avg) < 0).sum())
                if flipped:
                    worst["flipped_frames"] += 1
                    worst["flipped_max"] = max(worst["flipped_max"], flipped)
        report["deform"][clip.name] = {k: round(v, 3) if isinstance(v, float) else v for k, v in worst.items()}
        print("WING", clip.name, json.dumps(report["deform"][clip.name]), flush=True)

    # 3. FBX туда и обратно: перепонки + арматура, действие «взмах крыльями»
    clip = next(c() for c in A.CLIPS if c().name == "wing_buffet")
    times, poses = A.clip_frames(rg, clip)
    arm.animation_data_create()
    act = bpy.data.actions.new("WingTest")
    arm.animation_data.action = act
    for f, (p, lag) in enumerate(poses):
        rg.apply(rg.solve(dict(p), lag))
        for pb in arm.pose.bones:
            pb.keyframe_insert("location", frame=f, group=pb.name)
            pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 0, len(poses) - 1
    # опора для сравнения: форма перепонок прямо из решателя рига (без ключей и FBX) и масштаб костей
    direct, scale_dev = {}, 0.0
    arm.animation_data.action = None
    for f in range(0, len(poses), 3):
        p, lag = poses[f]
        rg.apply(rg.solve(dict(p), lag))
        bpy.context.view_layer.update()
        direct[f] = A.eval_points(obj)
        for pb in arm.pose.bones:
            scale_dev = max(scale_dev, max(abs(c - 1.0) for c in pb.scale))
    arm.animation_data.action = act
    report["fbx_scale_dev"] = round(scale_dev, 5)
    # объект «только перепонки»: копия дракона без остальных граней, те же группы и модификатор арматуры
    mem = obj.copy()
    mem.data = obj.data.copy()
    mem.name = mem.data.name = "WingMembranes"
    col.objects.link(mem)
    keep = set(mp["L"]) | set(mp["R"])
    bm = bmesh.new()
    bm.from_mesh(mem.data)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(mem.data)
    bm.free()
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    mem.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    path = os.path.join(OUT, "wing_membrane_test.fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"ARMATURE", "MESH"},
                             add_leaf_bones=False, bake_anim=True, bake_anim_use_all_actions=False,
                             bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                             bake_anim_step=1.0, bake_anim_simplify_factor=0.0,  # без упрощения кривых
                             use_armature_deform_only=False)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    imem = next(o for o in new if o.type == "MESH")
    iarm = next(o for o in new if o.type == "ARMATURE")
    # одинаковые вершины: по положению в первом кадре
    scene.frame_set(0)
    a0 = A.eval_points(mem)
    b0 = A.eval_points(imem)
    order = [int(np.argmin(np.linalg.norm(b0 - p, axis=1))) for p in a0]
    dev, keyed, dev_modes = [], [], []
    moved = 0.0
    memv = sorted({v for i in (mp["L"] + mp["R"]) for v in me.polygons[i].vertices})
    # импорт FBX ставит первый ключ на кадр 1 (исходное действие — с кадра 0): сравнение — со сдвигом на это число
    iact = iarm.animation_data.action if iarm.animation_data else None
    offset = int(round(iact.frame_range[0] - act.frame_range[0])) if iact else 0
    report["fbx_import_frame_offset"] = offset
    for f in range(0, len(poses), 3):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        a = A.eval_points(mem)
        full = A.eval_points(obj)
        scene.frame_set(f + offset)
        bpy.context.view_layer.update()
        bi = A.eval_points(imem)
        b = bi[order]
        d_nn = float(np.linalg.norm(a - b, axis=1).max())
        d_ix = float(np.linalg.norm(a - bi, axis=1).max()) if len(bi) == len(a) else 9e9
        dev.append((f, min(d_nn, d_ix)))
        dev_modes.append((round(d_nn * A.STUDS, 3), round(d_ix * A.STUDS, 3)))
        moved = max(moved, float(np.linalg.norm(a - a0, axis=1).max()))
        keyed.append((f, float(np.linalg.norm(full[memv] - direct[f][memv], axis=1).max())))
    report["keyed_vs_direct_studs"] = round(max(d for _, d in keyed) * A.STUDS, 4)
    print("KEYED", report["keyed_vs_direct_studs"], "scale_dev", report["fbx_scale_dev"], flush=True)
    report["fbx"] = {"file": os.path.basename(path), "mesh_verts": len(mem.data.vertices),
                     "imported_verts": len(imem.data.vertices), "imported_bones": len(iarm.data.bones),
                     "imported_groups": len(imem.vertex_groups),
                     "max_deviation_studs": round(max(d for _, d in dev) * A.STUDS, 4),
                     "frames_compared": len(dev), "wing_tip_travel_studs": round(moved * A.STUDS, 2),
                     "per_frame": [(f, round(d * A.STUDS, 4)) for f, d in dev]}
    print("FBX", json.dumps(report["fbx"]), flush=True)

    # 4. Вся модель: дракон (жёсткие детали — вес 1 своей кости, перепонки — веса по углам) + скипетр + арматура
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in (obj, rig["scepter"], arm):
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    path2 = os.path.join(OUT, "dragon_full_test.fbx")
    bpy.ops.export_scene.fbx(filepath=path2, use_selection=True, object_types={"ARMATURE", "MESH"},
                             add_leaf_bones=False, bake_anim=True, bake_anim_use_all_actions=False,
                             bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                             bake_anim_step=1.0, bake_anim_simplify_factor=0.0, use_armature_deform_only=False)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path2)
    new = [o for o in bpy.data.objects if o not in before]
    iarm2 = next(o for o in new if o.type == "ARMATURE")
    meshes = [o for o in new if o.type == "MESH"]
    idr = max(meshes, key=lambda o: len(o.data.vertices))
    # веса: у каждой вершины тот же набор костей и весов (по именам групп)
    def wmap(o):
        names = {g.index: g.name for g in o.vertex_groups}
        return [tuple(sorted((names[g.group], round(g.weight, 4)) for g in v.groups if g.weight > 1e-6)) for v in o.data.vertices]
    w0, w1 = wmap(obj), wmap(idr)
    same_w = sum(1 for a, b in zip(w0, w1) if a == b)
    rigid = sum(1 for a in w0 if len(a) == 1)
    iact2 = iarm2.animation_data.action if iarm2.animation_data else None
    off2 = int(round(iact2.frame_range[0] - act.frame_range[0])) if iact2 else 0
    dev2 = 0.0
    compared = len(obj.data.vertices) == len(idr.data.vertices)
    for f in range(0, len(poses), 6 if compared else 10 ** 6):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        a = A.eval_points(obj)
        scene.frame_set(f + off2)
        bpy.context.view_layer.update()
        b = A.eval_points(idr)
        if len(a) == len(b):
            dev2 = max(dev2, float(np.linalg.norm(a - b, axis=1).max()))
    report["fbx_full"] = {"file": os.path.basename(path2), "verts": len(obj.data.vertices),
                          "imported_verts": len(idr.data.vertices), "bones": len(arm.data.bones),
                          "imported_bones": len(iarm2.data.bones), "groups": len(obj.vertex_groups),
                          "imported_groups": len(idr.vertex_groups), "weights_identical_verts": same_w,
                          "rigid_verts_single_bone": rigid, "max_deviation_studs": round(dev2 * A.STUDS, 4) if compared else None,
                          "deviation_compared": compared, "imported_meshes": len(meshes)}
    print("FBXFULL", json.dumps(report["fbx_full"]), flush=True)
    with open(os.path.join(OUT, "wing_check.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print("WEIGHTS", json.dumps(report["weights"]), flush=True)


main()
