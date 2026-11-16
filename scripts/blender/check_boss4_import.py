"""Готовность 30 существ босса 4 «Сфинкс-лежебока» к импорту в Studio (File → Import 3D). Модели не меняет.

Для каждого assets/models/art/boss4/<id>.fbx (то, что владелец импортирует) проверяет, как check_creature_import.py
у босса 3: в FBX нет арматуры и анимаций (суставы и движения — в игре), части = скелет rig.json (имена, порядок,
один корень Stand, родители существуют), у каждой части один материал (иначе импорт делит меш и имя части теряется),
одна развёртка UV в [0, 1], 1…20 000 треугольников (предел MeshPart), вырожденных нет, у объекта нет поворота,
масштаба и родителя, начало координат = точка вращения скелета, габарит меша = скелет; на предмет ≤ 3 000
треугольников и один материал; карты color/normal 1024² (normal — касательная OpenGL); имена объектов уникальны во
всей коллекции. Масштаб и подставка: низ модели на y = 0, площадка ≤ 3.7 × 3.7, высота ≤ 4.6; Stand — только
подставка (верх ≤ 0.45 стада; иначе — решение владельца, как у Stand-композиций босса 3), после её скрытия существо не уходит под верх подставки и ничего видимого не остаётся
в Stand; габарит живого существа без подставки (Size, Lift, Center — по ним в игре хитбокс, поимка, постамент).
Запуск: blender --background --factory-startup --python scripts/blender/check_boss4_import.py -- <репо> [id…]
Печатает IMPORT по предметам и IMPORT_OK / IMPORT_FAIL; сводка — assets/models/art/boss4/Boss4Creatures.import.json.
"""

import ast
import json
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO = os.path.abspath(argv[0])
ART = os.path.join(REPO, "assets", "models", "art", "boss4")
TEX = os.path.join(REPO, "assets", "textures", "art", "boss4")
# каталог коллекции (№, id, название, редкость) — из листа коллекции, без запуска его кода (там PIL)
_src = open(os.path.join(REPO, "scripts", "boss4_collection_sheet.py"), encoding="utf-8").read()
_node = next(n for n in ast.parse(_src).body if isinstance(n, ast.Assign) and n.targets[0].id == "CREATURES")
CREATURES = ast.literal_eval(_node.value)

ids = argv[1:] or [c[1] for c in CREATURES]
meta = {c[1]: c for c in CREATURES}
MAX_PART_TRIS, MAX_ITEM_TRIS, PAD, MAX_H, STAND_TOP = 20000, 3000, 3.7, 4.6, 0.45  # верх подставок: 0.28–0.44
# решения владельца по подставкам с деталями (D58): деталь остаётся в Stand и прячется вместе с ней
STAND_RESOLVED = {"GiantCactus": "D58: песчаный холмик прячется вместе с подставкой"}


def to_rbx(v):
    return Vector((v.x, v.z, -v.y))


def image_stats(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = img.pixels[:]
    n = w * h
    mean = [sum(px[c::4]) / n for c in range(3)]
    bpy.data.images.remove(img)
    return {"size": [w, h], "mean": [round(m, 3) for m in mean]}


fails, warns_total, decisions_total, report, seen_names = 0, 0, 0, {}, {}
for item_id in ids:
    rig = json.load(open(os.path.join(ART, f"{item_id}.rig.json"), encoding="utf-8"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(ART, f"{item_id}.fbx"))
    bpy.context.view_layer.update()
    errs, warns, decisions = [], [], []
    objs = list(bpy.context.scene.objects)
    if any(o.type == "ARMATURE" for o in objs):
        errs.append("в FBX есть арматура (суставы — в игре)")
    if bpy.data.actions:
        errs.append(f"в FBX есть анимации {[a.name for a in bpy.data.actions]}")
    meshes = [o for o in objs if o.type == "MESH"]
    order = rig["order"]
    by_part = {}
    for o in meshes:
        part = next((p for p in order if o.name.endswith("_" + p)), None)
        if part is None or part in by_part:
            errs.append(f"{o.name}: лишний объект или повтор части")
            continue
        by_part[part] = o
    roots = [p for p in order if rig["parts"][p]["parent"] is None]
    if roots != ["Stand"]:
        errs.append(f"корень скелета {roots} (нужен один Stand)")
    for k, p in enumerate(order):
        par = rig["parts"][p]["parent"]
        if par is not None and par not in rig["parts"]:
            errs.append(f"{p}: родитель {par} не в скелете")
        elif par is not None and par not in order[:k]:
            # ItemFactory.buildCreature идёт по Order: ребёнок раньше родителя прикрепится к корню, а не к родителю
            warns.append(f"порядок частей: {p} раньше родителя {par} — генератор CreatureRigs должен упорядочить")
    total, mats = 0, set()
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)  # живое существо (без подставки)
    alo, ahi = Vector((1e9,) * 3), Vector((-1e9,) * 3)  # вся модель
    stand_top = None
    for name in order:
        o = by_part.get(name)
        if not o:
            errs.append(f"{name}: нет в FBX")
            continue
        if o.name in seen_names:
            errs.append(f"{o.name}: имя уже у {seen_names[o.name]}")
        seen_names[o.name] = item_id
        if o.parent is not None:
            errs.append(f"{name}: у объекта есть родитель")
        if any(abs(c) > 1e-4 for c in o.rotation_euler) or any(abs(c - 1) > 1e-4 for c in o.scale):
            errs.append(f"{name}: поворот или масштаб объекта не нулевые")
        me = o.data
        me.calc_loop_triangles()
        tris = len(me.loop_triangles)
        total += tris
        if tris == 0 or tris > MAX_PART_TRIS:
            errs.append(f"{name}: треугольников {tris}")
        degenerate = sum(1 for lt in me.loop_triangles if lt.area < 1e-7)
        if degenerate:
            errs.append(f"{name}: вырожденных треугольников {degenerate}")
        used = {me.materials[p.material_index].name for p in me.polygons if me.materials}
        mats |= used
        if len(used) != 1:
            errs.append(f"{name}: материалов {len(used)} — импорт разделит меш")
        if len(me.uv_layers) != 1:
            errs.append(f"{name}: развёрток UV {len(me.uv_layers)}")
        elif any(u.uv.x < -1e-3 or u.uv.x > 1 + 1e-3 or u.uv.y < -1e-3 or u.uv.y > 1 + 1e-3 for u in me.uv_layers[0].data):
            errs.append(f"{name}: UV вне [0, 1]")
        d = rig["parts"][name]
        piv = Vector(d["pivot"])
        if (to_rbx(o.location) - piv).length > 0.01:
            errs.append(f"{name}: начало координат ≠ точка вращения ({(to_rbx(o.location) - piv).length:.3f})")
        co = [to_rbx(v.co) for v in me.vertices]
        plo = Vector([min(c[i] for c in co) for i in range(3)])
        phi = Vector([max(c[i] for c in co) for i in range(3)])
        if ((plo + phi) / 2 - Vector(d["center"])).length > 0.01 or (phi - plo - Vector(d["size"])).length > 0.01:
            errs.append(f"{name}: габарит меша ≠ скелет")
        gap = max(max(plo[i] - 0.0, 0.0 - phi[i], 0.0) for i in range(3))  # точка вращения вне габарита части
        if gap > 0.6:
            warns.append(f"{name}: точка вращения в {gap:.2f} стада от части")
        for i in range(3):
            alo[i], ahi[i] = min(alo[i], piv[i] + plo[i]), max(ahi[i], piv[i] + phi[i])
        if name == "Stand":
            stand_top = piv[1] + phi[1]
        else:
            for i in range(3):
                lo[i], hi[i] = min(lo[i], piv[i] + plo[i]), max(hi[i], piv[i] + phi[i])
    if total > MAX_ITEM_TRIS:
        errs.append(f"треугольников на предмет {total} > {MAX_ITEM_TRIS}")
    if len(mats) != 1:
        errs.append(f"материалов на предмет {len(mats)}")
    if abs(alo[1]) > 0.005:
        errs.append(f"низ модели на y = {alo[1]:.3f}")
    foot = [ahi[0] - alo[0], ahi[2] - alo[2]]
    if max(foot) > PAD + 1e-3 or ahi[1] - alo[1] > MAX_H:
        errs.append(f"габарит {foot[0]:.2f} × {foot[1]:.2f} × {ahi[1] - alo[1]:.2f} больше площадки")
    if stand_top is None:
        errs.append("нет части Stand")
    elif stand_top > STAND_TOP and item_id in STAND_RESOLVED:
        pass  # решено владельцем (D58)
    elif stand_top > STAND_TOP:
        decisions.append(f"в Stand кроме подставки есть детали (верх {stand_top:.2f} стада): при скрытой подставке "
                         "они пропадут — оставить подставку, скрывать вместе с ней или вынести их в свою часть")
    elif lo[1] < stand_top - 0.08:
        warns.append(f"низ существа на {stand_top - lo[1]:.2f} стада ниже верха подставки: без подставки "
                     "его низ — эта часть (проверить вид)")
    maps = {}
    for kind in ("color", "normal"):
        path = os.path.join(TEX, f"{item_id}_{kind}.png")
        if not os.path.exists(path):
            errs.append(f"нет карты {kind}")
            continue
        st = image_stats(path)
        maps[kind] = st
        if st["size"] != [1024, 1024]:
            errs.append(f"карта {kind} {st['size']} (нужно 1024²)")
        if kind == "normal" and not (st["mean"][2] > 0.85 and abs(st["mean"][0] - 0.5) < 0.08
                                     and abs(st["mean"][1] - 0.5) < 0.08):
            warns.append(f"карта normal: среднее {st['mean']} — не похожа на касательную (OpenGL)")
    living = {"size": [round(hi[i] - lo[i], 3) for i in range(3)], "lift": round(lo[1], 3),
              "center": [round((lo[0] + hi[0]) / 2, 3), round((lo[2] + hi[2]) / 2, 3)]}
    report[item_id] = {
        "n": meta[item_id][0], "name": meta[item_id][2], "rarity": meta[item_id][3], "tris": total,
        "parts": order, "visible_parts": [p for p in order if p != "Stand"],
        "stand_top": round(stand_top or 0, 3), "stand_policy": "decide" if decisions else "hide", "living": living,
        "model_size": [round(foot[0], 3), round(ahi[1] - alo[1], 3), round(foot[1], 3)],
        "objects": sorted(o.name for o in by_part.values()), "materials": len(mats), "maps": maps,
        "fbx_kb": round(os.path.getsize(os.path.join(ART, f"{item_id}.fbx")) / 1024), "errors": errs,
        "decisions": decisions, "warnings": warns}
    fails += 1 if errs else 0
    warns_total += len(warns)
    decisions_total += len(decisions)
    print("IMPORT", item_id, json.dumps({"tris": total, "lift": living["lift"], "stand_top": round(stand_top or 0, 3),
                                         "errors": errs, "decisions": decisions, "warnings": warns}, ensure_ascii=False),
          flush=True)

if len(ids) == len(CREATURES):
    with open(os.path.join(ART, "Boss4Creatures.import.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
        f.write("\n")
print(("IMPORT_OK" if fails == 0 else "IMPORT_FAIL"), f"предметов {len(ids)}, с ошибками {fails}, решений владельца "
      f"{decisions_total}, предупреждений {warns_total}")
