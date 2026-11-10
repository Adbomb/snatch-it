"""Part-версия Крысиного короля (босс 3, D54) по утверждённой модели — пока меши и карты не загружены (вместо 21
блока-заготовки по габаритам частей).

Модель короля в scripts/blender/boss3_ratking.py собрана из простых фигур art_style.Art: бруски, восьмигранные и
другие призмы, усечённые пирамиды, рамки. Этот скрипт выполняет ту же сборку (без запекания и рендеров) и записывает
каждую фигуру — вид, размеры, поворот, цвет и часть скелета, — а затем переводит её в детали Roblox:
- брусок (в том числе наклонный: усы, хвост, цепь) — одна деталь того же размера и поворота;
- призма — полосами поперёк её многоугольника: восьмигранник — три ступени (D39: силуэт ступенями), прямоугольник —
  одна деталь, сужающийся многоугольник — до трёх полос;
- усечённая пирамида (клыки, зубцы короны) — две-три ступени;
- рамка (обод уха, медальона) — бруски вдоль сторон.
Скругления фасок не переносятся (блоки с острыми рёбрами). Цвет — цвет детали в модели (palette art.paint).
Совпадающих граней у разных деталей нет: у пересекающихся деталей (и одного цвета) одинаково смотрящие грани ближе
OVERLAY (в том числе наклонённые — ухо, корона) разводятся на OVERLAY (CLAUDE.md: ≥ 0.1) сдвигом грани меньшей
детали не больше чем на OVERLAY — см. separate().

Пишет assets/models/Boss3_RatKing.parts.json: часть → [{c, s, col, r?, shape?}] — центр от точки вращения части и
размер в стадах (оси Roblox, лицо +Z), поворот r — 9 чисел по строкам (если не единичный), shape "Cylinder" — круг.
Кадры <рендеры>/king_<ракурс>_{fbx,blocks}.png: FBX с картами D54 и детали с одного ракурса (лист сравнения —
assets/concepts/d55/boss3_visual_qa/11_king_d54_fbx_vs_parts.jpg).
Запуск: blender --background --factory-startup --python scripts/blender/boss_parts.py -- <репо> <рендеры>
Зависит от art_style.py и boss3_ratking.py (сборка фигур).
"""

import inspect
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import art_style as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
os.makedirs(OUT, exist_ok=True)
DST = os.path.join(REPO, "assets", "models", "Boss3_RatKing.parts.json")

SMALL_CUT = 0.12  # восьмигранник со срезом меньше этой доли стороны — одна деталь (срез не заметен)

# ── 1. Запись фигур при сборке модели ─────────────────────────────────────────────────────────────────────────
records = []
for kind in ("box", "prism", "frustum", "extrude", "frame"):
    original = getattr(S.Art, kind)
    signature = inspect.signature(original)

    def wrapper(self, *args, _original=original, _kind=kind, _sig=signature, **kwargs):
        bound = _sig.bind(self, *args, **kwargs)
        bound.apply_defaults()
        params = dict(bound.arguments)
        params.pop("self")
        records.append({"kind": _kind, "group": self.group, "color": self.colors[params["key"]][0],
                        "transform": None if self.transform is None else self.transform.copy(), "p": params})
        return _original(self, *args, **kwargs)

    setattr(S.Art, kind, wrapper)

source_path = os.path.join(HERE, "boss3_ratking.py")
source = open(source_path, encoding="utf-8").read()
source = source[: source.index('report = {"scale": SCALE}')]  # до сборки мешей: только фигуры, RIG и SCALE
sys.argv = [sys.argv[0], "--", REPO, os.path.join(OUT, "_unused"), "record"]
model = {"__name__": "__boss3_record__", "__file__": source_path}
exec(compile(source, source_path, "exec"), model)
RIG, SCALE = model["RIG"], model["SCALE"]
AX = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))  # оси Roblox: (x, y, z) Blender → (x, z, −y) Roblox


# ── 2. Фигура → прямоугольные куски в своих осях ──────────────────────────────────────────────────────────────
def spans(pts, w):
    """Отрезки по u, где горизонталь w пересекает многоугольник pts (может быть невыпуклым)."""
    xs = []
    n = len(pts)
    for i in range(n):
        (u0, w0), (u1, w1) = pts[i], pts[(i + 1) % n]
        if (w0 <= w < w1) or (w1 <= w < w0):
            xs.append(u0 + (w - w0) * (u1 - u0) / (w1 - w0))
    xs.sort()
    return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


def polygon_rects(pts, convex=True):
    """Многоугольник → прямоугольники (u0, u1, w0, w1): полосы между соседними высотами вершин, ширина — на середине
    полосы; сужающаяся полоса (клин) делится ещё надвое. Восьмигранник с маленьким срезом — его габарит."""
    us, ws = [p[0] for p in pts], [p[1] for p in pts]
    u0, u1, w0, w1 = min(us), max(us), min(ws), max(ws)
    if convex and len(pts) == 8:
        bottom = [p[0] - u0 for p in pts if abs(p[1] - w0) < 1e-6]  # срез — отступ нижнего ребра от угла
        cut = min(bottom) if bottom else 0
        if cut < SMALL_CUT * min(u1 - u0, w1 - w0):
            return [(u0, u1, w0, w1)]
    levels = sorted({round(w, 6) for w in ws})
    rects = []
    for a, b in zip(levels, levels[1:]):
        top, bottom = spans(pts, b - 1e-6 * (b - a)), spans(pts, a + 1e-6 * (b - a))
        width_top = sum(x1 - x0 for x0, x1 in top)
        width_bottom = sum(x1 - x0 for x0, x1 in bottom)
        taper = abs(width_top - width_bottom) > 0.35 * max(width_top, width_bottom, 1e-6)
        cuts = [a, (a + b) / 2, b] if taper and (b - a) > 0.06 else [a, b]
        for c0, c1 in zip(cuts, cuts[1:]):
            for x0, x1 in spans(pts, (c0 + c1) / 2):
                if x1 - x0 > 1e-4:
                    rects.append((x0, x1, c0, c1))
    return rects


def pieces(rec):
    """Куски фигуры: (матрица осей фигуры 4×4, центр, размер, поворот 3×3 в осях фигуры, форма)."""
    p, kind = rec["p"], rec["kind"]
    base = p.get("matrix")
    m = Matrix.Identity(4) if base is None else base.copy()
    if rec["transform"] is not None:
        m = rec["transform"] @ m
    eye = Matrix.Identity(3)
    out = []
    if kind == "box":
        lo = Vector((min(p["x0"], p["x1"]), min(p["y0"], p["y1"]), min(p["z0"], p["z1"])))
        hi = Vector((max(p["x0"], p["x1"]), max(p["y0"], p["y1"]), max(p["z0"], p["z1"])))
        out.append((m, (lo + hi) / 2, hi - lo, eye, "Block"))
    elif kind in ("prism", "extrude"):
        a = m @ S.AXES[p["axis"]]
        a0, a1 = sorted((p["a0"], p["a1"]))
        for u0, u1, w0, w1 in polygon_rects(p["pts"], convex=kind == "prism"):
            out.append((a, Vector(((u0 + u1) / 2, (w0 + w1) / 2, (a0 + a1) / 2)),
                        Vector((u1 - u0, w1 - w0, a1 - a0)), eye, "Block"))
    elif kind == "frustum":
        a = m @ S.AXES[p["axis"]]
        bottom, top, z0, z1 = p["bottom"], p["top"], p["z0"], p["z1"]
        apex = top[1] - top[0] < 1e-6 and top[3] - top[2] < 1e-6
        ts = (1 / 6, 1 / 2, 5 / 6) if apex else (1 / 4, 3 / 4)
        n = len(ts)
        for i, t in enumerate(ts):
            r = [bottom[k] + (top[k] - bottom[k]) * t for k in range(4)]
            za, zb = z0 + (z1 - z0) * i / n, z0 + (z1 - z0) * (i + 1) / n
            out.append((a, Vector(((r[0] + r[1]) / 2, (r[2] + r[3]) / 2, (za + zb) / 2)),
                        Vector((abs(r[1] - r[0]), abs(r[3] - r[2]), abs(zb - za))), eye, "Block"))
    elif kind == "frame":
        a = m @ S.AXES[p["axis"]]
        outer = p["pts"]
        inner = S._inset(outer, p["inset"])
        a0, a1 = sorted((p["a0"], p["a1"]))
        for i in range(len(outer)):
            j = (i + 1) % len(outer)
            po, qo = Vector((*outer[i], 0)), Vector((*outer[j], 0))
            pi, qi = Vector((*inner[i], 0)), Vector((*inner[j], 0))
            d = qo - po
            ang = math.atan2(d.y, d.x)
            length = ((qo - po).length + (qi - pi).length) / 2
            depth = a1 - a0  # бруски одной рамки одного цвета: их общие грани не видны
            center = (po + qo + pi + qi) / 4
            center.z = (a0 + a1) / 2
            out.append((a, center, Vector((length, p["inset"], depth)), Matrix.Rotation(ang, 3, "Z"), "Block"))
    return out


# ── 3. Куски → детали Roblox от точки вращения части ──────────────────────────────────────────────────────────
def proper(r):
    """Поворот без отражения (оси фигур Art бывают зеркальными): брусок симметричен — отражаем его третью ось."""
    if r.determinant() < 0:
        r = r.copy()
        for k in range(3):
            r[k][2] = -r[k][2]
    return r


def aligned(rr, size):
    """Поворот на 90° вокруг осей (призмы по y и x, зеркальные оси Art) — не наклон: деталь без поворота, размер
    по осям мира. Возвращает (поворот или None, размер)."""
    world = [None, None, None]
    for i in range(3):
        col = [rr[0][i], rr[1][i], rr[2][i]]
        j = max(range(3), key=lambda k: abs(col[k]))
        if abs(abs(col[j]) - 1) > 1e-4 or world[j] is not None:
            return rr, size
        world[j] = size[i]
    return None, Vector(world)


parts = {name: [] for name in RIG}
for rec in records:
    group = rec["group"]
    pivot = Vector(RIG[group][1]) * SCALE
    for frame, center, size, rot, shape in pieces(rec):
        r3 = frame.to_3x3()
        world = (frame @ center) * SCALE  # модель короля в масштабе предметов → стады
        r = proper(r3 @ rot)
        for k in range(3):  # без масштаба (на всякий случай нормируем столбцы)
            col = Vector((r[0][k], r[1][k], r[2][k])).normalized()
            for row in range(3):
                r[row][k] = col[row]
        c = AX @ (world - pivot)
        # поворот детали: её оси (оси фигуры) → оси Roblox; размер — по её осям (порядок фигуры)
        rr, s = aligned(AX @ r, size * SCALE)
        entry = {"c": [round(v, 4) for v in c], "s": [round(v, 4) for v in s], "col": rec["color"]}
        if rr is not None and any(abs(rr[i][j] - (1 if i == j else 0)) > 1e-4 for i in range(3) for j in range(3)):
            entry["r"] = [round(rr[i][j], 5) for i in range(3) for j in range(3)]
        if shape != "Block":
            entry["shape"] = shape
        parts[group].append(entry)


OVERLAY = 0.1  # стадов (CLAUDE.md): накладка другого цвета выступает не меньше этого — иначе грани мерцают
FACE_MIN = 0.05  # стадов: перекрытие граней меньше этого по одной из осей не считается (как в World/FaceCheck)
PASSES = 3  # проходов разведения граней


def separate(parts):
    """Одинаково смотрящие совпадающие или почти совпадающие (ближе OVERLAY) грани пересекающихся деталей с одним
    поворотом разводятся на OVERLAY: двигается грань меньшей детали — накладки (зрачок, пряжка, камень). Детали — от
    больших к меньшим (грани больших уже на местах, цепочек нет); новое место грани — ближайшее к исходному, где она
    не ближе OVERLAY ни к одной такой грани больших деталей, не дальше OVERLAY от исходного (у разных частей —
    2 × OVERLAY); при равенстве — наружу (накладка выступает). У разных частей грань уходит только внутрь: части
    двигаются друг относительно друга, выступ прошёл бы сквозь соседа (блик глаза сквозь закрытое веко). Детали
    одного цвета тоже разводятся (пупырышки LegoSquares на совпадающих гранях мерцают и при одном цвете), но только
    наружу: внутрь — вырез или щель, если большая деталь закрывает меньшую не целиком. Перекрытие граней меньше
    FACE_MIN по одной из осей не считается (как в World/FaceCheck). Сравнение — в осях поворота деталей (у
    наклонённого уха все его детали повёрнуты одинаково)."""
    by_part = {id(e): name for name, lst in parts.items() for e in lst}
    pivots = {name: AX @ (Vector(RIG[name][1]) * SCALE) for name in RIG}
    groups = {}
    for lst in parts.values():
        for e in lst:
            key = tuple(round(v, 3) for v in e.get("r", (1, 0, 0, 0, 1, 0, 0, 0, 1)))
            groups.setdefault(key, []).append(e)
    moved = kept = 0
    for key, boxes in groups.items():
        rot = Matrix((key[0:3], key[3:6], key[6:9]))
        inv = rot.transposed()
        local = {}
        for e in boxes:
            c = inv @ (Vector(e["c"]) + pivots[by_part[id(e)]])
            s = Vector(e["s"])
            local[id(e)] = [[c[k] - s[k] / 2 for k in range(3)], [c[k] + s[k] / 2 for k in range(3)]]

        def volume(e):
            box = local[id(e)]
            return math.prod(box[1][k] - box[0][k] for k in range(3))

        order = sorted(boxes, key=volume, reverse=True)
        start = {id(e): [list(local[id(e)][0]), list(local[id(e)][1])] for e in boxes}
        for rnd in range(PASSES):  # ещё проход: сдвиг одной грани меняет перекрытие других (верх бруска → его бок)
            for idx, e in enumerate(order):
                box = local[id(e)]
                for ax in range(3):
                    others = [k for k in range(3) if k != ax]
                    for side in (0, 1):  # грани смотрят в одну сторону: обе нижние или обе верхние
                        faces = []  # (плоскость грани большей детали, та же часть, тот же цвет)
                        for other in order[:idx]:
                            b = local[id(other)]
                            # с запасом 1e-3: в Roblox 0.05 превращается в 0.0500001, и FaceCheck пару видит
                            if all(min(box[1][k], b[1][k]) - max(box[0][k], b[0][k]) > FACE_MIN - 1e-3
                                   for k in others):
                                own_part = by_part[id(other)] == by_part[id(e)]
                                faces.append((b[side][ax], own_part, other["col"] == e["col"]))
                        cur = box[side][ax]
                        near = [(own, same) for f, own, same in faces if abs(cur - f) < OVERLAY - 1e-4]
                        if not near:
                            continue
                        orig = start[id(e)][side][ax]  # сдвиг — от исходного места грани
                        own = all(o for o, _ in near)
                        same = all(c for _, c in near)  # только того же цвета: только наружу
                        out = -1 if side == 0 else 1
                        limit = OVERLAY if own else 2 * OVERLAY
                        cands = {f + d * OVERLAY for f, _, _ in faces for d in (-1, 1)}
                        best = None
                        def rank(p):  # ближе к исходному; при равенстве — наружу
                            return round(abs(p - orig), 6), 0 if (p - orig) * out > 0 else 1

                        for p in sorted(cands, key=rank):
                            if abs(p - orig) > limit + 1e-4:
                                break
                            if not own and (p - orig) * out > 1e-4:
                                continue  # разные части: только внутрь
                            if own and same and (p - orig) * out < -1e-4:
                                continue  # один цвет: только наружу
                            if (box[1][ax] - p if side == 0 else p - box[0][ax]) < 0.02:
                                continue
                            if all(abs(p - f) >= OVERLAY - 1e-4 for f, _, _ in faces):
                                best = p
                                break
                        if best is None and min(abs(cur - f) for f, _, _ in faces) < FACE_MIN:
                            # вровень, а места на OVERLAY нет (грань между двумя соседними): хотя бы FACE_MIN — так
                            # World/FaceCheck пару не видит; в любую сторону (и у одного цвета), до 2 × OVERLAY
                            cands = {f + d for f, _, _ in faces for d in (-OVERLAY, OVERLAY, -FACE_MIN, FACE_MIN)}
                            for p in sorted(cands, key=lambda p: round(abs(p - orig), 6)):
                                if abs(p - orig) > 2 * OVERLAY + 1e-4:
                                    break
                                if (box[1][ax] - p if side == 0 else p - box[0][ax]) < 0.02:
                                    continue
                                if all(abs(p - f) >= FACE_MIN - 1e-4 for f, _, _ in faces):
                                    best = p
                                    break
                        if best is None:
                            if rnd == PASSES - 1:
                                kept += 1  # зажата между соседними (не ближе FACE_MIN) — оставлена
                            continue
                        box[side][ax] = best
        for e in boxes:
            box, first = local[id(e)], start[id(e)]
            n = sum(1 for side in (0, 1) for k in range(3) if abs(box[side][k] - first[side][k]) > 1e-6)
            if n:
                moved += n
                c = rot @ Vector([(box[0][k] + box[1][k]) / 2 for k in range(3)])
                e["c"] = [round(v, 4) for v in c - pivots[by_part[id(e)]]]
                e["s"] = [round(box[1][k] - box[0][k], 4) for k in range(3)]
    return moved, kept


moved, kept = separate(parts)
total = sum(len(v) for v in parts.values())
with open(DST, "w", encoding="utf-8", newline="\n") as f:
    json.dump({"source": "scripts/blender/boss3_ratking.py", "figures": len(records), "blocks": total,
               "parts": parts}, f, ensure_ascii=False, indent=1)
print(f"KING_PARTS фигур {len(records)} → деталей {total}, отступов граней {moved}, зажатых (≥ FACE_MIN) {kept}",
      flush=True)
for name in RIG:
    print(f"KING_PART {name}: {len(parts[name])}", flush=True)

# ── 4. Кадры: FBX с картами D54 и детали с одного ракурса ─────────────────────────────────────────────────────
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
studio = bpy.data.collections.new("Studio")
scene.collection.children.link(studio)
holder = bpy.data.objects.new("Holder", None)
studio.objects.link(holder)
DOWN = 1 / 3.0  # студия рассчитана на предметы ~4 стада: король ×1/3
holder.matrix_world = Matrix.Scale(DOWN, 4)
bpy.ops.import_scene.fbx(filepath=os.path.join(REPO, "assets", "models", "Boss3_RatKing.fbx"))
fbx = [o for o in scene.objects if o.type == "MESH" and o.name.startswith("Boss3_RatKing")]
tex = {}
for o in fbx:
    group = o.name[len("Boss3_RatKing"):].split("_", 1)[0]
    if group not in tex:
        m = bpy.data.materials.new(f"Tex{group}")
        m.use_nodes = True
        nt = m.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        t = nt.nodes.new("ShaderNodeTexImage")
        color = os.path.join(REPO, "assets", "textures", "art", f"Boss3_RatKing{group}_color.png")
        t.image = bpy.data.images.load(color)
        nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.55
        tex[group] = m
    o.data.materials.clear()
    o.data.materials.append(tex[group])
    o.parent = holder
mats, blocks = {}, []
TO_B = AX.transposed()
for name, lst in parts.items():
    pivot = Vector(RIG[name][1]) * SCALE
    for e in lst:
        bm = bmesh.new()
        if e.get("shape") == "Cylinder":
            bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.5, radius2=0.5, depth=1.0)
            bmesh.ops.rotate(bm, verts=bm.verts, matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
        else:
            bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=e["s"], verts=bm.verts)
        r = Matrix(((e["r"][0:3]), (e["r"][3:6]), (e["r"][6:9]))) if "r" in e else Matrix.Identity(3)
        m = (TO_B @ r).to_4x4()  # оси детали → оси Roblox → оси Blender; размер — по осям детали
        m.translation = pivot + TO_B @ Vector(e["c"])
        bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
        me = bpy.data.meshes.new("Blk")
        bm.to_mesh(me)
        bm.free()
        key = e["col"]
        if key not in mats:
            mt = bpy.data.materials.new(key)
            mt.use_nodes = True
            b = next(n for n in mt.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            b.inputs["Base Color"].default_value = (*S.lin(key), 1)
            b.inputs["Roughness"].default_value = 0.55
            mats[key] = mt
        me.materials.append(mats[key])
        ob = bpy.data.objects.new("Blk", me)
        studio.objects.link(ob)
        ob.parent = holder
        blocks.append(ob)
prev = S.Preview(scene.collection)
for which, models in (("fbx", fbx), ("blocks", blocks)):
    for o in fbx + blocks:
        o.hide_render = o not in models
    center = Vector((0, 0, 15 * DOWN / 2))
    prev.aim_lights(center)
    for tag, eye, target, lens in (("front", (0, -11, 4.1), center, 50),
                                   ("three_quarter", (-6.5, -9, 4.7), center, 50),
                                   ("side", (-11, -0.5, 4.1), center, 50),
                                   ("face", (-1.2, -6.5, 3.8), Vector((0, 0, 3.45)), 70)):
        prev.shot(os.path.join(OUT, f"king_{tag}_{which}.png"), tuple(Vector(eye)), target, lens, (800, 900))
print("KING_RENDER_OK", OUT, flush=True)
