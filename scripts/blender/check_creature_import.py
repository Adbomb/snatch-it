"""Готовность 30 существ босса 3 (D54) к импорту в Studio вместо Part-версий (D55). Модели не меняет.

Для каждого assets/models/art/<id>.fbx (то, что владелец импортирует через File → Import 3D) проверяет то, чего не
проверяет check_rigs.py: у каждой части один материал (иначе импорт делит меш на несколько MeshPart и имя части
теряется), одна развёртка UV в [0, 1], треугольники ≤ 20 000 на часть (предел MeshPart) и ≤ 3 000 на предмет (D54),
вырожденных треугольников нет, в FBX нет арматуры и анимаций (суставы и движения — в игре: Config/CreatureRigs,
Shared/CreatureAnim), карты color/normal 1024² (normal — OpenGL, синий канал ≈ 1), имена частей уникальны во всей
коллекции. Сравнивает габарит видимых частей меша с Part-версией (Config/CreatureRigs: Size, Lift, Center — по ним
стоят хитбокс, поимка, постамент и подпись): расхождение > 0.25 стада — предупреждение.
С --fixture <папка> ещё пишет <id>.json для предпросмотра в Studio без загрузки (EditableMesh): вершины каждой части
от центра её габарита и повёрнутые на 180° вокруг вертикали — так кладёт меш импорт Studio (BUGS.md), UV, гранёные
нормали, треугольники и карту цвета 128² (RGB).
Запуск: blender --background --factory-startup --python scripts/blender/check_creature_import.py -- <репо>
        [--fixture <папка>] [id…]
Печатает IMPORT по предметам и IMPORT_OK / IMPORT_FAIL; сводка — <репо>/assets/models/art/Boss3Creatures.import.json.
"""

import base64
import json
import os
import re
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO = os.path.abspath(argv[0])
rest = argv[1:]
FIXTURE = None
if "--fixture" in rest:
    i = rest.index("--fixture")
    FIXTURE = os.path.abspath(rest[i + 1])
    rest = rest[:i] + rest[i + 2 :]
ART = os.path.join(REPO, "assets", "models", "art")
TEX = os.path.join(REPO, "assets", "textures", "art")
RIGS = os.path.join(REPO, "src", "shared", "Config", "CreatureRigs.luau")
index = json.load(open(os.path.join(ART, "Boss3Creatures.index.json"), encoding="utf-8"))
ids = rest or [item["id"] for item in index["items"]]
items = {item["id"]: item for item in index["items"]}
TEX_FIXTURE = 128
MAX_PART_TRIS, MAX_ITEM_TRIS, BOX_TOLERANCE = 20000, 3000, 0.25


def to_rbx(v):
    return Vector((v.x, v.z, -v.y))


def creature_rigs():
    """Size / Center / Lift Part-версии из сгенерированного Config/CreatureRigs (по ним стоит предмет в игре)."""
    text = open(RIGS, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"^\t(\w+) = \{\n\t\tSize = Vector3\.new\(([^)]*)\),\n\t\tCenter = Vector3\.new\(([^)]*)\),"
                         r"\n\t\tLift = ([-\d.]+),", text, re.M):
        out[m.group(1)] = {"size": [float(c) for c in m.group(2).split(",")],
                           "center": [float(c) for c in m.group(3).split(",")], "lift": float(m.group(4))}
    return out


def image_stats(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = list(img.pixels[:])
    n = w * h
    mean = [sum(px[c::4]) / n for c in range(3)]
    return img, {"size": [w, h], "channels": img.channels, "mean": [round(m, 3) for m in mean]}


def fixture_texture(img):
    small = img.copy()
    small.scale(TEX_FIXTURE, TEX_FIXTURE)
    px = small.pixels[:]
    data = bytearray()
    # строки сверху вниз (EditableImage), в Blender — снизу вверх
    for row in range(TEX_FIXTURE - 1, -1, -1):
        for col in range(TEX_FIXTURE):
            k = (row * TEX_FIXTURE + col) * 4
            for c in range(3):
                data.append(max(0, min(255, round(px[k + c] * 255))))
    bpy.data.images.remove(small)
    return base64.b64encode(bytes(data)).decode("ascii")


def part_fixture(o, center):
    """Вершины части от центра габарита, повёрнутые на 180° вокруг вертикали (как кладёт меш импорт Studio)."""
    me = o.data
    me.calc_loop_triangles()
    uvl = me.uv_layers.active.data
    verts, index_of, tris = [], {}, []
    for lt in me.loop_triangles:
        ids3 = []
        n = to_rbx(lt.normal)
        for li in lt.loops:
            p = to_rbx(me.vertices[me.loops[li].vertex_index].co) - center
            u = uvl[li].uv
            key = (round(-p.x, 4), round(p.y, 4), round(-p.z, 4), round(-n.x, 3), round(n.y, 3), round(-n.z, 3),
                   round(u[0], 5), round(1 - u[1], 5))
            if key not in index_of:
                index_of[key] = len(verts)
                verts.append(key)
            ids3.append(index_of[key])
        tris.append(ids3)
    return {"v": [k[0:3] for k in verts], "n": [k[3:6] for k in verts], "uv": [k[6:8] for k in verts], "t": tris}


rigs = creature_rigs()
fails, warns_total, report, seen_names = 0, 0, {}, {}
if FIXTURE:
    os.makedirs(FIXTURE, exist_ok=True)
for item_id in ids:
    rig = json.load(open(os.path.join(ART, f"{item_id}.rig.json"), encoding="utf-8"))
    item = items[item_id]
    hidden = set(item.get("hide_with_stand") or [])
    if item.get("stand_policy") != "keep":
        hidden.add("Stand")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(ART, f"{item_id}.fbx"))
    bpy.context.view_layer.update()
    errs, warns = [], []
    scene_objs = list(bpy.context.scene.objects)
    if any(o.type == "ARMATURE" for o in scene_objs):
        errs.append("в FBX есть арматура (суставы — в игре)")
    if bpy.data.actions:
        errs.append(f"в FBX есть анимации {[a.name for a in bpy.data.actions]}")
    prefix = f"Art_{item_id}_"
    parts = {o.name[len(prefix):]: o for o in scene_objs if o.type == "MESH" and o.name.startswith(prefix)}
    total, lo, hi, fixture_parts, mats = 0, Vector((1e9,) * 3), Vector((-1e9,) * 3), {}, set()
    for name in rig["order"]:
        o = parts.get(name)
        if not o:
            errs.append(f"{name}: нет в FBX")
            continue
        if o.name in seen_names:
            errs.append(f"{o.name}: имя уже у {seen_names[o.name]}")
        seen_names[o.name] = item_id
        me = o.data
        me.calc_loop_triangles()
        tris = len(me.loop_triangles)
        total += tris
        if tris == 0 or tris > MAX_PART_TRIS:
            errs.append(f"{name}: треугольников {tris}")
        degenerate = sum(1 for lt in me.loop_triangles if lt.area < 1e-7)
        if degenerate:
            warns.append(f"{name}: вырожденных треугольников {degenerate}")
        used = {me.materials[p.material_index].name for p in me.polygons if me.materials}
        mats |= used
        if len(used) > 1:
            errs.append(f"{name}: материалов {len(used)} — импорт разделит меш")
        if len(me.uv_layers) != 1:
            errs.append(f"{name}: развёрток UV {len(me.uv_layers)}")
        else:
            us = [d.uv for d in me.uv_layers[0].data]
            if any(u.x < -1e-3 or u.x > 1 + 1e-3 or u.y < -1e-3 or u.y > 1 + 1e-3 for u in us):
                errs.append(f"{name}: UV вне [0, 1]")
        co = [to_rbx(v.co) for v in me.vertices]
        plo = Vector([min(c[i] for c in co) for i in range(3)])
        phi = Vector([max(c[i] for c in co) for i in range(3)])
        center = (plo + phi) / 2
        d = rig["parts"][name]
        if (center - Vector(d["center"])).length > 0.01 or (phi - plo - Vector(d["size"])).length > 0.01:
            errs.append(f"{name}: габарит меша ≠ скелет")
        if name not in hidden:
            piv = Vector(d["pivot"])
            for i in range(3):
                lo[i] = min(lo[i], piv[i] + plo[i])
                hi[i] = max(hi[i], piv[i] + phi[i])
        if FIXTURE:
            fixture_parts[name] = {**part_fixture(o, center), "size": [round(c, 4) for c in phi - plo]}
    if total > MAX_ITEM_TRIS:
        errs.append(f"треугольников на предмет {total} > {MAX_ITEM_TRIS}")
    maps = {}
    color_img = None
    for kind in ("color", "normal"):
        path = os.path.join(TEX, f"{item_id}_{kind}.png")
        if not os.path.exists(path):
            errs.append(f"нет карты {kind}")
            continue
        img, st = image_stats(path)
        maps[kind] = st
        if st["size"] != [1024, 1024]:
            errs.append(f"карта {kind} {st['size']} (нужно 1024²)")
        if kind == "normal" and not (st["mean"][2] > 0.85 and abs(st["mean"][0] - 0.5) < 0.08 and abs(st["mean"][1] - 0.5) < 0.08):
            warns.append(f"карта normal: среднее {st['mean']} — не похожа на касательную (OpenGL)")
        if kind == "color":
            color_img = img
    # габарит меша против Part-версии (по ней стоят хитбокс, поимка, постамент и подпись)
    pr = rigs.get(item_id)
    box = {}
    if pr:
        mesh_size = [hi[i] - lo[i] for i in range(3)]
        mesh_center = [(lo[0] + hi[0]) / 2, 0, (lo[2] + hi[2]) / 2]
        box = {"mesh_size": [round(c, 3) for c in mesh_size], "parts_size": pr["size"],
               "mesh_lift": round(lo[1], 3), "parts_lift": pr["lift"],
               "mesh_center": [round(c, 3) for c in mesh_center], "parts_center": pr["center"]}
        worst = max([abs(mesh_size[i] - pr["size"][i]) for i in range(3)]
                    + [abs(lo[1] - pr["lift"]), abs(mesh_center[0] - pr["center"][0]), abs(mesh_center[2] - pr["center"][2])])
        box["worst"] = round(worst, 3)
        if worst > BOX_TOLERANCE:
            warns.append(f"габарит меша отличается от Part-версии на {worst:.2f} стада")
    else:
        errs.append("нет записи в Config/CreatureRigs")
    fbx_size = os.path.getsize(os.path.join(ART, f"{item_id}.fbx"))
    report[item_id] = {"tris": total, "parts": len(rig["order"]), "visible": len(rig["order"]) - len(hidden & set(rig["order"])),
                       "materials": len(mats), "maps": maps, "box": box, "fbx_kb": round(fbx_size / 1024),
                       "errors": errs, "warnings": warns}
    if FIXTURE:
        out = {"id": item_id, "parts": fixture_parts, "tex": fixture_texture(color_img) if color_img else None,
               "texSize": TEX_FIXTURE}
        with open(os.path.join(FIXTURE, f"{item_id}.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, separators=(",", ":"))
    fails += 1 if errs else 0
    warns_total += len(warns)
    print("IMPORT", item_id, json.dumps({"tris": total, "box": box.get("worst"), "errors": errs, "warnings": warns},
                                        ensure_ascii=False), flush=True)

with open(os.path.join(ART, "Boss3Creatures.import.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
    f.write("\n")
print(("IMPORT_OK" if fails == 0 else "IMPORT_FAIL"), f"предметов {len(ids)}, с ошибками {fails}, предупреждений {warns_total}")
