"""Король-дракон №10: экспорт для Roblox — этап A плана интеграции (boss10_v7_anim4/REPORT.md §6).

Из утверждённого рига (v7_rig.py, 53 кости) и клипов итерации 4 (v7_anim4.py: доводка рогов, пола, наручей, мантии)
пишет в assets/models/:
- Boss10_Dragon.rig.json — 52 сустава: 49 частей дракона и 3 части скипетра. Кость Root — корень модели в игре (её
  поворот делает сама модель), родители, точки вращения, габариты меша от точки вращения, средний цвет части
  (заготовка до импорта мешей), позы stand / combat / sleep — Transform сустава от покоя, контур тела для дальности
  ближнего боя (REPORT §5), центр магического круга залпа;
- Boss10_Dragon.anim.json — 13 клипов (все утверждённые, кроме «Разворота») и вместо «Разворота» — шаг на месте
  влево и вправо: корень поворачивается равномерно на 50°/с, как модель в игре, лапы переступают дважды за 90°, цикл
  1.8 с; кадр — Transform каждого сустава от покоя в осях Roblox [x, y, z, qx, qy, qz, qw], 30 кадров в секунду;
- Boss10_Dragon_parts.fbx — части по суставам (меш от точки вращения, стады) и Boss10_Dragon_membranes.fbx — две
  перепонки с арматурой (веса по Body, WingArm, WingFore, Finger1–4) — для этапа C; сюда только пишутся, в Roblox
  не загружаются.
Оси Roblox: (x, y, z) Blender → (x, z, −y), лицо модели +Z, стады (масштаб 2.795). Имена суставов — имена костей
без точки (UpperArm.L → UpperArmL); имя кости Blender — поле bone.

  blender --background --factory-startup --python scripts/blender/dragon10/v7_export.py -- <репо> <папка> [data|fbx|all]
"""

import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE)))
import v7_anim5 as A  # noqa: E402
import volley_sim as VS  # noqa: E402

R = A.R
AX = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))  # Blender → Roblox
SC = A.STUDS
TURN_RATE = 50.0  # °/с — поворот модели на месте в игре (утверждено для теста)
MODELS = os.path.join(A.REPO, "assets", "models")
WHAT = A.MODE if A.MODE in ("data", "fbx", "all") else "all"
HULL_TAGS = ["body", "chest", "forelegL", "forelegR", "hindlegL", "hindlegR", "bracerL", "bracerR", "greaveL", "greaveR"]


def rname(n):
    return n.replace(".", "")


# ── шаг на месте ─────────────────────────────────────────────────────────────────────────────────────────────
def turn_step(direction):
    """Шаг на месте для поворота модели в игре: корень — равномерно TURN_RATE °/с (90° за цикл 1.8 с), лапы
    переступают по разу за 45° (как «Разворот» итерации 4: дуга шага внутрь, передняя лапа выше полос мантии)."""
    sign = 1.0 if direction == "left" else -1.0
    base = A.TURN_STEPS
    steps = base if sign > 0 else {"FR": base["FL"], "HL": base["HR"], "FL": base["FR"], "HR": base["HL"]}
    period = 90.0 / TURN_RATE

    def layer(p, t, clip):
        # корень стоит (его поворот в игре делает модель): опорные лапы относительно тела уходят назад со скоростью
        # поворота, переступающие — вперёд; цикл замкнут (через 90° стойка та же), маятник мантии не видит скачка
        p["root_yaw"] = 0.0
        turned = TURN_RATE * t
        for leg, st in steps.items():
            x0, y0, z0 = A.COMBAT[f"{leg}_x"], A.COMBAT[f"{leg}_y"], A.COMBAT[f"{leg}_z"]
            ang, lift, pitch, arc = 0.0, 0.0, 0.0, 0.0
            side = 1.0 if leg[1] == "L" else -1.0
            for t0, t1 in st:
                u = min(max((t - t0) / (t1 - t0), 0.0), 1.0)
                ang += 45.0 * A.smooth(u)
                lift += (A.TURN_LIFT_F if leg[0] == "F" else A.TURN_LIFT_H) * math.sin(math.pi * u)
                pitch += 18 * math.sin(math.pi * u)
                arc += A.TURN_ARC * math.sin(math.pi * u)
            x, y = A.rot2(x0 + side * arc, y0, sign * (ang - turned))
            p[f"{leg}_x"], p[f"{leg}_y"], p[f"{leg}_z"] = x, y, z0 + lift
            p[f"{leg}_yaw"], p[f"{leg}_pitch"] = sign * (ang - turned), pitch

    pose = A.P(A.COMBAT, head_y=8.0 * sign, neck_y=4.0 * sign)
    title = "Шаг на месте влево" if sign > 0 else "Шаг на месте вправо"
    return A.Clip(f"turn_step_{direction}", title, period, [(0.0, pose), (period, pose)], loop=True,
                  layers=[layer, A.scepter_idle], start="combat", end="combat",
                  note=f"цикл: поворот модели на 90° за {period:.1f} с ({TURN_RATE:.0f}°/с), каждая лапа — два шага")


# ── суставы и Transform ──────────────────────────────────────────────────────────────────────────────────────
def joints(arm):
    """Суставы игры: все кости, кроме Root (её место — корень модели). [(имя кости, родитель или None)]."""
    out = []
    for b in arm.data.bones:
        if b.name == "Root":
            continue
        par = b.parent.name if b.parent and b.parent.name != "Root" else None
        out.append((b.name, par))
    return out


def transforms(arm, js, A0):
    """Transform каждого сустава от покоя (Blender, единицы модели) в текущей позе арматуры — без движения корня."""
    pb, bones = arm.pose.bones, arm.data.bones
    root = pb["Root"].matrix @ bones["Root"].matrix_local.inverted()
    inv = root.inverted()
    W = {n: inv @ pb[n].matrix @ bones[n].matrix_local.inverted() @ A0[n] for n, _ in js}
    out = {}
    for n, par in js:
        bw, ba = (W[par], A0[par]) if par else (Matrix.Identity(4), Matrix.Identity(4))
        out[n] = (A0[n].inverted() @ ba) @ bw.inverted() @ W[n]
    return out, root


def to_rbx(T):
    r = (AX @ T.to_3x3() @ AX.transposed()).to_quaternion().normalized()
    t = AX @ (T.translation * SC)
    return t, r


PIN = 6  # кадров на краю клипа, которые сводятся к общей позе


def pin_row(a, b, w):
    """Сустав a → b с силой w: сдвиг — линейно, поворот — slerp (по короткой дуге)."""
    qa = Quaternion((a[6], a[3], a[4], a[5]))
    qb = Quaternion((b[6], b[3], b[4], b[5]))
    if qa.dot(qb) < 0:
        qb = -qb
    q = qa.slerp(qb, w).normalized()
    t = [a[k] + (b[k] - a[k]) * w for k in range(3)]
    return [round(v, 4) for v in (t[0], t[1], t[2], q.x, q.y, q.z, q.w)]


def row7(T):
    t, r = to_rbx(T)
    return [round(v, 4) for v in (t.x, t.y, t.z, r.x, r.y, r.z, r.w)]


def row12(T):
    t, _ = to_rbx(T)
    m = AX @ T.to_3x3() @ AX.transposed()
    return [round(v, 4) for v in [t.x, t.y, t.z] + [m[i][j] for i in range(3) for j in range(3)]]


# ── геометрия частей ─────────────────────────────────────────────────────────────────────────────────────────
def part_vertices(rig):
    """Вершины каждой кости: жёсткие детали дракона (вес 1, без перепонок) и скипетра."""
    out = {}
    for obj in (rig["dragon"], rig["scepter"]):
        me = obj.data
        names = {g.index: g.name for g in obj.vertex_groups}
        skip = set()
        if obj is rig["dragon"]:
            for poly, b in zip(me.polygons, rig["art"].face_groups):
                if b and b.startswith("Membrane"):
                    skip.update(poly.vertices)
        for v in me.vertices:
            if v.index in skip:
                continue
            gs = [g for g in v.groups if g.weight > 0.5]
            if len(gs) == 1:
                out.setdefault(names[gs[0].group], []).append((obj, v.index))
    return out


def material_color(mat):
    """Цвет материала по палитре v7 (имя материала — «<работа>_<ключ палитры>»); узлы колец D39 цвет не меняют."""
    key = mat.name.split("_", 1)[-1].split(".")[0]
    if key in A.VD.PALETTE:
        h = A.VD.PALETTE[key][0]
        return np.array([srgb_lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)])
    c = mat.diffuse_color
    return np.array([c[0], c[1], c[2]])


def srgb_lin(x):
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def srgb_hex(c):
    def enc(x):
        x = max(0.0, min(1.0, float(x)))
        return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
    return "".join(f"{int(round(enc(v) * 255)):02X}" for v in c)


def part_colors(rig):
    """Средний цвет кости по площади граней её деталей."""
    acc = {}
    for obj in (rig["dragon"], rig["scepter"]):
        me = obj.data
        names = {g.index: g.name for g in obj.vertex_groups}
        groups = rig["art"].face_groups if obj is rig["dragon"] else [None] * len(me.polygons)
        for poly, fg in zip(me.polygons, groups):
            if fg and fg.startswith("Membrane"):
                continue
            v = me.vertices[poly.vertices[0]]
            gs = [g for g in v.groups if g.weight > 0.5]
            if len(gs) != 1:
                continue
            mat = obj.material_slots[poly.material_index].material if obj.material_slots else None
            if mat is None:
                continue
            n = names[gs[0].group]
            s = acc.setdefault(n, [np.zeros(3), 0.0])
            s[0] += material_color(mat) * poly.area
            s[1] += poly.area
    return {n: srgb_hex(c / w) for n, (c, w) in acc.items() if w > 0}


def hull_xz(rig, rg):
    """Контур тела сверху в боевой стойке (REPORT §5): выпуклая оболочка, упрощённая, оси Roblox (X, Z)."""
    A.show(rg, rig, dict(A.COMBAT))
    co = A.eval_points(rig["dragon"]) * SC
    polys = [list(p.vertices) for p in rig["dragon"].data.polygons]
    vs = np.unique([v for t in HULL_TAGS for i in rig["tags"][t] for v in polys[i]])
    pts = sorted(set(map(tuple, np.round(co[vs][:, :2], 3))))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    h = lo[:-1] + up[:-1]
    changed = True
    while changed and len(h) > 8:
        changed = False
        for i in range(len(h)):
            a, b, c = np.array(h[i - 1]), np.array(h[i]), np.array(h[(i + 1) % len(h)])
            if abs(np.cross(c - a, b - a)) / (np.linalg.norm(c - a) + 1e-9) < 0.25:
                h.pop(i)
                changed = True
                break
    # Roblox: X = x, Z = −y; порядок — против часовой стрелки в плоскости X–Z (для проверки «внутри»)
    out = [(round(x, 2), round(-y, 2)) for x, y in h]
    area = sum(out[i][0] * out[(i + 1) % len(out)][1] - out[(i + 1) % len(out)][0] * out[i][1] for i in range(len(out)))
    if area < 0:
        out.reverse()
    return out


# ── данные ───────────────────────────────────────────────────────────────────────────────────────────────────
def export_data(col, rig, rg):
    arm = rig["arm"]
    js = joints(arm)
    A0 = {b.name: Matrix.Translation(b.head_local) for b in arm.data.bones}
    verts = part_vertices(rig)
    colors = part_colors(rig)
    order = [rname(n) for n, _ in js]
    parts = {}
    for n, par in js:
        head = arm.data.bones[n].head_local
        pivot = AX @ (head * SC)
        pts = [AX @ ((o.data.vertices[i].co - head) * SC) for o, i in verts.get(n, [])]
        if pts:
            lo = Vector([min(p[k] for p in pts) for k in range(3)])
            hi = Vector([max(p[k] for p in pts) for k in range(3)])
        else:
            lo = hi = Vector((0, 0, 0))
        size = Vector([max(hi[k] - lo[k], 0.2) for k in range(3)])
        parts[rname(n)] = {"parent": rname(par) if par else None, "bone": n,
                           "pivot": [round(c, 4) for c in pivot], "center": [round(c, 4) for c in (lo + hi) / 2],
                           "size": [round(c, 4) for c in size], "map": "Dragon", "color": colors.get(n, "6A4BC9"),
                           "verts": len(pts)}
    poses = {}  # из кадров клипов (ниже): с теми же доводками, что играют клипы, — стыки без скачков
    hull = hull_xz(rig, rg)
    L = VS.LAUNCH
    rigjson = {"scale": SC, "order": order, "parts": parts, "poses": poses,
               "body": hull, "volley_origin": [L[0], L[2], -L[1]], "turn_rate": TURN_RATE,
               "membranes": {x: {"bones": ["Body", f"WingArm.{x}", f"WingFore.{x}"] + [f"Finger{i}.{x}" for i in range(1, 5)]}
                             for x in "LR"},
               "format": "pivot/center/size — стады, оси Roblox (лицо +Z); poses: сустав → [x, y, z, r00…r22]"}

    clips = [c for c in A.CLIPS if c().name != "turn_left"] + [lambda: turn_step("left"), lambda: turn_step("right")]
    out = {"fps": A.FPS, "order": order, "scale": SC, "turn_rate": TURN_RATE,
           "format": "frames[кадр][сустав по order] = [x, y, z, qx, qy, qz, qw] — Transform от покоя, оси Roblox",
           "clips": {}}
    root_motion = {}
    probe_at = {"wing_buffet": 24, "claw_swipe": 24, "turn_step_left": 20, "sleep_idle": 0, "magic_volley": 58}
    out["probe"] = {}
    for make in clips:
        clip = make()
        times, frames = A.clip_frames(rg, clip)
        rows, rm = [], 0.0
        for f, (p, lag) in enumerate(frames):
            A.show(rg, rig, p, lag)
            T, root = transforms(arm, js, A0)
            rows.append([row7(T[n]) for n, _ in js])
            rm = max(rm, (root.translation * SC).length, abs(root.to_euler().z))
            if probe_at.get(clip.name) == f:
                # контроль для Lune: точка каждой части — в покое от точки вращения и в позе (корень модели, оси Roblox)
                co = A.eval_points(rig["dragon"])
                cs = A.eval_points(rig["scepter"])
                inv = root.inverted()
                pts = {}
                for n, _ in js:
                    vv = verts.get(n)
                    if not vv:
                        continue
                    o, i = vv[len(vv) // 2]
                    head = arm.data.bones[n].head_local
                    rest = AX @ ((o.data.vertices[i].co - head) * SC)
                    posed = AX @ ((inv @ Vector((co if o is rig["dragon"] else cs)[i])) * SC)
                    pts[rname(n)] = [round(c, 4) for c in list(rest) + list(posed)]
                out["probe"][clip.name] = {"frame": f, "points": pts}
        root_motion[clip.name] = round(rm, 3)
        out["clips"][clip.name] = {"title": clip.title, "duration": round(clip.duration, 4), "loop": clip.loop,
                                   "start_pose": clip.start, "end_pose": clip.end,
                                   "events": {k: round(v, 4) for k, v in clip.events.items()}, "frames": rows}
        print("CLIP", clip.name, len(rows), "кадров; движение корня (стады или радианы)", root_motion[clip.name], flush=True)
    # края клипов — к общим позам: каждый клип доводится отдельно (маятник мантии, отвод локтя), поэтому их первые и
    # последние кадры немного разные; PIN кадров на краю плавно сводятся к позе combat / stand / sleep — стыки клипов
    # в игре без маха (как у Сфинкса), середина клипа и моменты удара не меняются
    canon = {"combat": out["clips"]["combat_idle"]["frames"][0], "stand": out["clips"]["victory"]["frames"][-1],
             "sleep": out["clips"]["sleep_idle"]["frames"][0]}
    for cname, c in out["clips"].items():
        if c["loop"]:
            continue
        rows = c["frames"]
        n = len(rows)
        for edge, pose in (("start", c["start_pose"]), ("end", c["end_pose"])):
            if not pose or pose not in canon or (cname == "victory" and edge == "end"):
                continue
            target = canon[pose]
            for i in range(min(PIN, n // 2)):
                w = 1.0 - A.smooth(i / PIN)
                f = i if edge == "start" else n - 1 - i
                rows[f] = [pin_row(a, b, w) for a, b in zip(rows[f], target)]
    # позы движка — кадры клипов: combat — начало боевой стойки, stand — конец «Победы», sleep — начало сна
    def pose12(row):
        res = {}
        for (n, _), v in zip(js, row):
            m = Quaternion((v[6], v[3], v[4], v[5])).to_matrix()
            res[rname(n)] = [v[0], v[1], v[2]] + [round(m[i][j], 4) for i in range(3) for j in range(3)]
        return res
    poses["combat"] = pose12(out["clips"]["combat_idle"]["frames"][0])
    poses["stand"] = pose12(out["clips"]["victory"]["frames"][-1])
    poses["sleep"] = pose12(out["clips"]["sleep_idle"]["frames"][0])
    with open(os.path.join(MODELS, "Boss10_Dragon.rig.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rigjson, fh, ensure_ascii=False, indent=1)
    print("RIG_OK суставов", len(order), "контур", len(hull), "точек", flush=True)
    path = os.path.join(MODELS, "Boss10_Dragon.anim.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print("ANIM_OK", path, round(os.path.getsize(path) / 1e6, 2), "МБ", json.dumps(root_motion), flush=True)


# ── FBX для этапа C ──────────────────────────────────────────────────────────────────────────────────────────
def export_fbx(col, rig):
    arm = rig["arm"]
    verts = part_vertices(rig)
    objs = []
    for obj in (rig["dragon"], rig["scepter"]):
        names = {g.index: g.name for g in obj.vertex_groups}
        groups = rig["art"].face_groups if obj is rig["dragon"] else [None] * len(obj.data.polygons)
        by = {}
        for poly, fg in zip(obj.data.polygons, groups):
            if fg and fg.startswith("Membrane"):
                continue
            gs = [g for g in obj.data.vertices[poly.vertices[0]].groups if g.weight > 0.5]
            if len(gs) == 1:
                by.setdefault(names[gs[0].group], []).append(poly.index)
        for n, faces in by.items():
            head = arm.data.bones[n].head_local
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.faces.ensure_lookup_table()
            keep = set(faces)
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context="FACES")
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
            me = bpy.data.meshes.new(rname(n))
            bm.to_mesh(me)
            bm.free()
            for m in obj.data.materials:
                me.materials.append(m)
            me.transform(Matrix.Translation(-head))
            me.transform(Matrix.Scale(SC, 4))
            o = bpy.data.objects.new(rname(n), me)
            o.location = head * SC
            col.objects.link(o)
            objs.append(o)
    path = os.path.join(MODELS, "Boss10_Dragon_parts.fbx")
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
                             mesh_smooth_type="FACE", path_mode="STRIP", object_types={"MESH"})
    print("FBX_PARTS_OK", path, len(objs), "частей", flush=True)
    # перепонки с арматурой (без анимации — поза привязки = покой)
    obj = rig["dragon"]
    mem = obj.copy()
    mem.data = obj.data.copy()
    mem.name = mem.data.name = "WingMembranes"
    col.objects.link(mem)
    keep = {i for i, b in enumerate(rig["art"].face_groups) if b and b.startswith("Membrane")}
    bm = bmesh.new()
    bm.from_mesh(mem.data)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(mem.data)
    bm.free()
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    mem.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    path = os.path.join(MODELS, "Boss10_Dragon_membranes.fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"ARMATURE", "MESH"},
                             add_leaf_bones=False, bake_anim=False, use_armature_deform_only=False,
                             apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
                             axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP")
    print("FBX_MEMBRANES_OK", path, len(mem.data.vertices), "вершин", flush=True)


def main():
    col, rig = A.setup()
    rg = A.Rig(rig["arm"])
    rg.samples = A.leg_samples(rig)
    rg.rig = rig
    os.makedirs(MODELS, exist_ok=True)
    if WHAT in ("data", "all"):
        export_data(col, rig, rg)
    if WHAT in ("fbx", "all"):
        export_fbx(col, rig)
    print("EXPORT_DONE", flush=True)


if __name__ == "__main__":
    main()
