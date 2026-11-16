"""Риг Короля-дракона v7 (утверждённая модель, внешний вид не меняется) — модуль для v7_anim.py.

Модель собирается тем же кодом v7_dragon.py. Каждая деталь жёстко привязана к одной кости: блоки D39 не гнутся, как
Motor6D-части Сфинкса в игре. Исключение — перепонки крыльев: их углы привязаны к костям руки и пальцев с весами,
поэтому перепонка тянется при взмахе и складывании. В игре это будет skinned mesh.

Кости (имена — как будут называться суставы в игре). Root — земля под центром.
- Тело: Body.
- Шея и голова: Neck1–4, Head (с короной и рогами), Jaw.
- Броня и мантия: Pauldron.L/R — наплечник частично следует за плечом; Mantle.L1–3/R1–3 — полосы мантии.
- Передние лапы: UpperArm, Forearm, Paw.
- Задние лапы: Thigh, Shin, Meta (плюсна), HindPaw.
- Крылья: WingArm, WingFore, Finger1–4.
- Хвост: Tail1–7.
- Скипетр — отдельный объект на своих костях: ScepterCircle (круг на земле), Scepter, ScepterShards (осколки вокруг).

Кольца D39 рисуются по координатам покоя (атрибуты rest_co, rest_no): в движении рисунок не плывёт по детали, как
и запечённая текстура в игре.
Зависит от Blender, v7_dragon.py, v4_kit.py, art_style.py и concepts510/ck.py.
"""

import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "concepts510"))
import ck  # noqa: E402
import v7_dragon as D  # noqa: E402

V = Vector
S2 = (1, -1)
SIDE = {1: "L", -1: "R"}
SCALE = 2.795  # стадов в единице модели (масштаб экспорта v6/v7: без короны 35 стадов)
GLOW = 5.0

# ── суставы (числа из v7_dragon.py: анатомия v6) ──────────────────────────────────────────────────────────────
NECK = [V((0, -2.6, 5.95)), V((0, -3.75, 6.95)), V((0, -3.95, 8.1)), V((0, -3.5, 9.0)), V((0, -3.8, 9.8)),
        V((0, -4.35, 10.2))]
HEAD_ORIGIN = V((0, -4.15, 9.75))
HL, HH, HW = 3.8, 1.85, 1.58
HEAD_M = Matrix.Translation(HEAD_ORIGIN) @ Matrix.Rotation(math.radians(-7), 4, "Z") @ \
    Matrix.Rotation(math.radians(-10), 4, "X")
JAW_HINGE = HEAD_M @ V((0, -0.12 * HL, 0))
JAW_AXIS = (HEAD_M.to_3x3() @ V((1, 0, 0))).normalized()  # раскрытие челюсти — вокруг этой оси, плюс — шире
TAIL = [V(p) for p in ((0, 3.4, 4.5), (0, 4.8, 4.65), (0.6, 6.2, 3.85), (1.8, 7.2, 2.45), (3.0, 7.5, 1.15),
                       (4.3, 7.0, 0.58), (5.3, 5.9, 0.48), (5.6, 4.6, 0.45))]
BODY_C = V((0, 0.2, 4.4))


def fore(s):
    step = s > 0
    sh = V((s * 2.05, -2.35, 5.25))
    el = V((s * 2.5, -2.25, 3.45)) if step else V((s * 2.5, -1.9, 3.25))
    wr = V((s * 2.4, -3.35, 1.55)) if step else V((s * 2.38, -2.45, 1.3))
    front_y = -3.95 if step else -3.1
    return sh, el, wr, V((wr.x, front_y - 0.25, 0.25))


def hind(s):
    dy = 0.0 if s > 0 else 0.35
    hip = V((s * 1.92, 2.2, 4.6))
    knee, hock = V((s * 2.06, 1.55, 2.0)), V((s * 2.1, 3.5 + dy, 1.15))
    ankle = V((s * 2.1, 2.8 + dy, 0.42))
    return hip, knee, hock, ankle, V((ankle.x, 1.75 + dy - 0.25, 0.25))


WING_ARGS = {1: dict(sweep=20, lean=12, tilt=6), -1: dict(sweep=26, lean=12, tilt=-3)}
WING_LOCAL = {"E": (2.05, 2.25), "W": (3.95, 3.9), "F": [(6.6, 3.05), (6.95, 0.78), (5.9, -1.2), (4.05, -2.15)]}


def wing_frame(s):
    """Плоскость крыла как в v7_dragon.wing(): матрица M, точки в мире (корень, E, W, F1–4, вырезы, T у бока)."""
    g = WING_ARGS[s]
    root = V((s * 1.55, -1.1, 7.0))
    M = (Matrix.Translation(root) @ Matrix.Rotation(math.radians(s * g["sweep"]), 4, "Z")
         @ Matrix.Rotation(math.radians(-s * g["tilt"]), 4, "Y") @ Matrix.Rotation(math.radians(g["lean"]), 4, "X")
         @ Matrix.Scale(s, 4, V((1, 0, 0))))
    t = M.inverted() @ V((s * 1.75, 1.0, 5.2))
    E, W, T = V(WING_LOCAL["E"]), V(WING_LOCAL["W"]), V((t.x, t.z))
    F = [V(f) for f in WING_LOCAL["F"]]

    def P(v):
        return M @ V((v.x, 0.0, v.y))

    def notch(p, q, k=0.3):
        mid = (p + q) / 2
        return mid + (W - mid) * k

    pts = {"root": P(V((0, 0))), "E": P(E), "W": P(W), "T": P(T)}
    for i, f in enumerate(F):
        pts[f"F{i + 1}"] = P(f)
    for i in range(3):
        pts[f"N{i + 1}"] = P(notch(F[i], F[i + 1]))
    pts["N4"] = P(notch(F[-1], T, 0.22))
    return M, pts


def bones():
    """[(имя, голова, хвост, родитель)] — порядок задаёт иерархию."""
    out = [("Root", V((0, 0, 0)), V((0, -1.5, 0)), None), ("Body", BODY_C, BODY_C + V((0, -1.8, 0)), "Root")]
    parent = "Body"
    for i in range(4):
        out.append((f"Neck{i + 1}", NECK[i], NECK[i + 1], parent))
        parent = f"Neck{i + 1}"
    out.append(("Head", NECK[4], HEAD_M @ V((0, -1.08 * HL, 0.28 * HH)), "Neck4"))
    out.append(("Collar", V((0, -3.92, 7.72)), V((0, -3.92, 8.9)), "Body"))  # воротник: следует за шеей (COLLAR_FOLLOW)
    out.append(("Jaw", JAW_HINGE, HEAD_M @ V((0, -1.0 * HL, -0.35 * HH)), "Head"))
    for s in S2:
        x = SIDE[s]
        sh, el, wr, toe = fore(s)
        out += [(f"Pauldron.{x}", sh, sh + V((s * 0.6, 0, 1.2)), "Body"), (f"UpperArm.{x}", sh, el, "Body"),
                (f"Forearm.{x}", el, wr, f"UpperArm.{x}"), (f"Paw.{x}", wr, toe, f"Forearm.{x}")]
        hip, knee, hock, ankle, htoe = hind(s)
        out += [(f"Thigh.{x}", hip, knee, "Body"), (f"Shin.{x}", knee, hock, f"Thigh.{x}"),
                (f"Meta.{x}", hock, ankle, f"Shin.{x}"), (f"HindPaw.{x}", ankle, htoe, f"Meta.{x}")]
        _, p = wing_frame(s)
        out += [(f"WingArm.{x}", p["root"], p["E"], "Body"), (f"WingFore.{x}", p["E"], p["W"], f"WingArm.{x}")]
        out += [(f"Finger{i}.{x}", p["W"], p[f"F{i}"], f"WingFore.{x}") for i in range(1, 5)]
        for k, (y0, y1, zh, _) in enumerate(D.STRIPS):
            yc = (y0 + y1) / 2
            out.append((f"Mantle.{x}{k + 1}", V((s * 2.05, yc, D.YOKE["z0"] + 0.05)),
                        V((s * (2.05 + D.FLARE), yc, zh)), "Body"))
    parent = "Body"
    for i in range(7):
        out.append((f"Tail{i + 1}", TAIL[i], TAIL[i + 1], parent))
        parent = f"Tail{i + 1}"
    sx, sy = D.SCEPTER_AT
    out += [("ScepterCircle", V((sx, sy, 0.05)), V((sx, sy - 1.0, 0.05)), "Root"),
            ("Scepter", V((sx, sy, 3.2)), V((sx, sy, 6.2)), "Root"),
            ("ScepterShards", V((sx, sy, 2.1)), V((sx, sy, 2.8)), "Scepter")]
    return out


# ── детали → кости ───────────────────────────────────────────────────────────────────────────────────────────
ORDER = {  # детали метки по порядку их постройки в v7_dragon.py (последнее имя — для остальных)
    "neck": ["Neck1", "Neck2", "Neck3", "Neck4", "Head"],
    "spines": ["Neck3", "Neck4", "Head", "Body"],
    "fore": ["UpperArm", "Forearm", "Forearm", "Paw"],
    "hind": ["Thigh", "Thigh", "Thigh", "Shin", "Shin", "Meta", "Meta", "HindPaw"],
    "greave": ["Meta", "Thigh"],
    "wing": ["Membrane"] * 4 + ["WingArm", "WingFore"] + [f"Finger{i}" for i in range(1, 5) for _ in (0, 1)] +
            ["WingFore", "WingArm"],
    "tail": [f"Tail{i}" for i in range(1, 8)] + [f"Tail{i}" for i in range(2, 8)] + ["Tail7"],
    "tailarmor": ["Tail1", "Tail1", "Tail2", "Tail2", "Tail1"],
}
HEAD_TAGS = ("skull", "brows", "eyes", "browspikes", "horns", "crown")


def assign(a):
    """Каждой детали — кость (a.parts[i][3]); возвращает {метка: [номера деталей]} для проверок."""
    bone = [None] * len(a.parts)

    def put(tag, names, suffix=""):
        for k, i in enumerate(a.tags[tag]):
            n = names if isinstance(names, str) else names[min(k, len(names) - 1)]
            bone[i] = n + suffix if n not in ("Membrane",) else n + suffix

    for i, part in enumerate(a.parts):
        bone[i] = {"Head": "Head", "Jaw": "Jaw", "Torso": "Body", "Neck": "Body"}.get(part[3])
    for t in HEAD_TAGS:
        put(t, "Head")
    put("jaw", "Jaw")
    put("neck", ORDER["neck"])
    put("spines", ORDER["spines"])
    put("tail", ORDER["tail"])
    put("tailarmor", ORDER["tailarmor"])
    put("collar", "Collar")
    for s in S2:
        x = SIDE[s]
        put("fore" + "leg" + x, ORDER["fore"], "." + x)
        put("bracer" + x, "Forearm", "." + x)
        put("hindleg" + x, ORDER["hind"], "." + x)
        put("greave" + x, ORDER["greave"], "." + x)
        put("pauldron" + x, "Pauldron", "." + x)
        put("wing" + x, ORDER["wing"], "." + x)
        for i in a.tags["mantle" + x]:
            bone[i] = "Mantle." + x + a.parts[i][3][-1]  # группа v7 «MantleL2» → кость Mantle.L2
    for want, tag in ((5, "neck"), (8, "spines"), (11, "foreleg" + "L"), (15, "hindleg" + "L"), (16, "wingL"),
                      (14, "tail"), (6, "tailarmor"), (4, "greaveL")):
        assert len(a.tags[tag]) == want, (tag, len(a.tags[tag]), want)
    missing = [i for i, b in enumerate(bone) if b is None]
    assert not missing, missing
    for i, b in enumerate(bone):
        bm, key, solid, _ = a.parts[i]
        a.parts[i] = (bm, key, solid, b)
    return bone


def scepter_art():
    """Скипетр отдельным произведением: круг на земле, древко с кристаллом, осколки вокруг."""
    a = D.new_art("ScepterV7")
    D.scepter(a)
    n = len(a.parts)
    for i, (bm, key, solid, _) in enumerate(a.parts):
        b = "ScepterShards" if i >= n - 6 else "ScepterCircle" if i >= n - 8 else "Scepter"
        a.parts[i] = (bm, key, solid, b)
    return a


# ── сборка ───────────────────────────────────────────────────────────────────────────────────────────────────
def tag_parts(a):
    """Номер детали в слой граней: после сборки атрибут pid у каждой грани меша."""
    for i, (bm, _, _, _) in enumerate(a.parts):
        layer = bm.faces.layers.int.get("pid") or bm.faces.layers.int.new("pid")
        for f in bm.faces:
            f[layer] = i


def rest_attributes(obj):
    """Координаты и нормали покоя для колец D39; материалы колец читают их вместо текущих (рисунок не плывёт)."""
    me = obj.data
    co = np.empty(len(me.vertices) * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co)
    me.attributes.new("rest_co", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", co)
    no = np.empty(len(me.polygons) * 3, dtype=np.float32)
    me.polygons.foreach_get("normal", no)
    me.attributes.new("rest_no", "FLOAT_VECTOR", "FACE").data.foreach_set("vector", no)
    for mat in me.materials:
        nt = mat.node_tree
        for node in list(nt.nodes):
            if node.type == "TEX_COORD":
                out = node.outputs["Object"]
                name = "rest_co"
            elif node.type == "NEW_GEOMETRY":
                out = node.outputs["True Normal"]
                name = "rest_no"
            else:
                continue
            links = [ln.to_socket for ln in out.links]
            if not links:
                continue
            attr = nt.nodes.new("ShaderNodeAttribute")
            attr.attribute_name = name
            attr.attribute_type = "GEOMETRY"
            for sock in links:
                nt.links.new(attr.outputs["Vector"], sock)


def skin(obj, art, arm, membrane=None):
    """Группы вершин: жёсткие детали — вес 1 своей кости; перепонки — веса по углам (рука, пальцы, бок)."""
    me = obj.data
    groups = {}
    for poly, b in zip(me.polygons, art.face_groups):
        if b is None or b.startswith("Membrane"):
            continue
        g = groups.get(b) or obj.vertex_groups.new(name=b)
        groups[b] = g
        g.add(list(poly.vertices), 1.0, "REPLACE")
    if membrane is not None:
        weights = {"root": {"WingArm": 1.0}, "E": {"WingArm": 1.0}, "W": {"WingFore": 1.0}, "T": {"Body": 1.0},
                   "N4": {"Finger4": 0.5, "Body": 0.5}}
        for i in range(1, 5):
            weights[f"F{i}"] = {f"Finger{i}": 1.0}
        for i in range(1, 4):
            weights[f"N{i}"] = {f"Finger{i}": 0.5, f"Finger{i + 1}": 0.5}
        for s in S2:
            x = SIDE[s]
            _, pts = wing_frame(s)
            verts = {v for poly, b in zip(me.polygons, art.face_groups) if b == "Membrane." + x for v in poly.vertices}
            worst = 0.0
            for vi in verts:
                co = me.vertices[vi].co
                name, d = min(((n, (co - p).length) for n, p in pts.items()), key=lambda t: t[1])
                worst = max(worst, d)
                for b, w in weights[name].items():
                    bn = b if b == "Body" else f"{b}.{x}"
                    g = groups.get(bn) or obj.vertex_groups.new(name=bn)
                    groups[bn] = g
                    g.add([vi], w, "ADD")
            membrane[x] = {"verts": len(verts), "worst_corner_distance": round(worst, 3)}
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    obj.parent = arm
    return groups


def make_armature(col):
    data = bpy.data.armatures.new("KingDragonRig")
    arm = bpy.data.objects.new("KingDragonRig", data)
    col.objects.link(arm)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for name, head, tail, parent in bones():
        b = data.edit_bones.new(name)
        b.head, b.tail = head, tail
        if parent:
            b.parent = eb[parent]
        b.use_deform = name != "Root"
        eb[name] = b
    bpy.ops.object.mode_set(mode="OBJECT")
    data.display_type = "OCTAHEDRAL"
    arm.show_in_front = True
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return arm


def eye_driver(mat, arm, prop, closed_code, glow):
    """Свечение материала по свойству рига (0 — погасло/закрыто, 1 — горит): цвет и сила свечения."""
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    open_col = tuple(bsdf.inputs["Base Color"].default_value)
    val = nt.nodes.new("ShaderNodeValue")
    val.name = prop
    val.outputs[0].default_value = 1.0
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.inputs["Color1"].default_value = (*D.K.S.lin(closed_code), 1) if closed_code else open_col
    mix.inputs["Color2"].default_value = open_col
    nt.links.new(val.outputs[0], mix.inputs["Fac"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Emission Color"])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = glow
    nt.links.new(val.outputs[0], mul.inputs[0])
    nt.links.new(mul.outputs[0], bsdf.inputs["Emission Strength"])
    fc = val.outputs[0].driver_add("default_value")
    fc.driver.type = "AVERAGE"
    var = fc.driver.variables.new()
    var.type = "SINGLE_PROP"
    var.targets[0].id_type = "OBJECT"
    var.targets[0].id = arm
    var.targets[0].data_path = f'["{prop}"]'
    return val


def build(col):
    """Риг целиком: арматура, дракон, скипетр. Возвращает словарь с объектами и сведениями для проверок."""
    arm = make_armature(col)
    arm["eyes"] = 1.0  # 1 — глаза открыты (горят), 0 — закрыты: в игре это смена материала глаз, не кость
    arm["glow"] = 1.0  # свечение кристалла скипетра (1 — обычное, до 3 — магическая атака)
    art = D.dragon(royal=True, with_scepter=False)
    bone_of_part = assign(art)
    tags = dict(art.tags)
    tag_parts(art)
    obj = ck.finish(art, col, glow=GLOW)
    obj.name = "KingDragon_v7"
    membrane = {}
    skin(obj, art, arm, membrane)
    sart = scepter_art()
    tag_parts(sart)
    sobj = ck.finish(sart, col, glow=GLOW)
    sobj.name = "Scepter_v7"
    skin(sobj, sart, arm)
    for o, a in ((obj, art), (sobj, sart)):
        for mat in a.materials:
            k = mat.name.split("_", 1)[-1]
            b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if b is not None and k.startswith("gold"):
                b.inputs["Metallic"].default_value = 0.45
                b.inputs["Roughness"].default_value = 0.32
        rest_attributes(o)
    eye = next(m for m in art.materials if m.name.endswith("_neonEye"))
    eye_driver(eye, arm, "eyes", D.PALETTE["scaleD"][0], GLOW)
    crystal = next(m for m in sart.materials if m.name.endswith("_neonCrystal"))
    eye_driver(crystal, arm, "glow", None, GLOW)
    pid = np.zeros(len(obj.data.polygons), dtype=np.int32)
    obj.data.attributes["pid"].data.foreach_get("value", pid)
    polys_of_tag = {t: np.nonzero(np.isin(pid, idx))[0] for t, idx in tags.items()}
    # двойная привязка вершин (если бы сборка склеила детали разных костей) — недопустима
    mem = {v for poly, b in zip(obj.data.polygons, art.face_groups) if b.startswith("Membrane") for v in poly.vertices}
    shared = sum(1 for v in obj.data.vertices if len(v.groups) > 1 and v.index not in mem)
    info = {"tris": art.stats["tris"], "tris_scepter": sart.stats["tris"], "hidden_faces": art.stats["hidden_faces"],
            "coplanar": art.stats["coplanar"], "membrane": membrane, "shared_vertices": shared,
            "bones": [b[0] for b in bones()], "parts_per_bone": {}}
    for b in bone_of_part:
        info["parts_per_bone"][b] = info["parts_per_bone"].get(b, 0) + 1
    return {"arm": arm, "dragon": obj, "scepter": sobj, "art": art, "sart": sart, "tags": polys_of_tag, "info": info}
