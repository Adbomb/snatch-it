"""Образец архитектуры этажа «Золотой трон» в утверждённом стиле D39 (2026-11-19, на проверку владельцу): небольшой
внутренний угол золотой стены — пол-ковёр, цоколь, бархатный пояс с пуговицами, угловая стойка с камнем, карниз с
зубцами. Сделан тем же конвейером, что ваза v13 и предмет GoldenThrone (art_style.py): блоки с острыми рёбрами
(фаска 0.012), чистые цвета предмета, на крупных деталях — отдельные скруглённые квадраты-контуры D39 (шаг 0.6,
квадрат 0.42, скругление 0.1, контур 0.03) одной сеткой, мелкие накладки гладкие; цвет, окклюзия и нормали запечены
в карты 1024². Ничего не загружается в Roblox и не идёт в игру.
Рядом для сравнения ставятся настоящие утверждённые модели с их картами: ваза v13 (assets/models/ArtV13_Vase.fbx) и
предмет «Золотой трон» (assets/models/art/GoldenThrone.fbx) — одна студия, один свет, одна камера.
Пишет в папку <out>: карты образца, кадры сравнения и metrics.json (плотность текселей).
Запуск: blender --background --factory-startup --python scripts/blender/floor_sample_d39.py -- <репо> <out>
"""

import json
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new("SampleD39")
bpy.context.scene.collection.children.link(collection)

# ── Образец: цвета — как у предмета GoldenThrone (art_flea.golden_throne) ────────────────────────────────────
a = S.Art("Sample_GoldWall", ring_z0=2.0)
a.paint("gold", "F2C230", rings=True)
a.paint("velvet", "C62828", rings=True)
a.paint("carpet", "6B3FB8", rings=True)
for key, code in (("gold2", "C9921A"), ("button", "F2C230"), ("ruby", "E53935"), ("ruby2", "FF8A8A"), ("emerald", "2E9E4F"),
                  ("sapphire", "2E5BD8"), ("glint", "FFFFFF")):
    a.paint(key, code)

W, T = 3.6, 0.6  # ширина стен от угла и их толщина; стена A смотрит в −y, стена B — в −x
X0, Y0 = -0.2, -3.8  # свободные края стен
# пол — ковёр
a.box("carpet", X0, W + T, Y0, T, 0.0, 0.3)
# стены
a.box("gold", X0, W + T, 0.0, T, 0.28, 4.4)
a.box("gold", W, W + T, Y0, 0.0, 0.28, 4.4)
# цоколь ступенью и его гладкая кромка
a.box("gold", X0, W, -0.25, 0.0, 0.28, 0.95)
a.box("gold", W - 0.25, W, Y0, -0.25, 0.28, 0.95)
a.box("gold2", X0, W, -0.32, 0.0, 0.93, 1.05)
a.box("gold2", W - 0.32, W, Y0, -0.32, 0.93, 1.05)
# пояс: бархат между двумя гладкими валиками, пуговицы
for z0, z1 in ((2.5, 2.62), (3.38, 3.5)):
    a.box("gold2", X0, W, -0.14, 0.0, z0, z1)
    a.box("gold2", W - 0.14, W, Y0, -0.14, z0, z1)
a.box("velvet", X0, W, -0.08, 0.0, 2.6, 3.4)
a.box("velvet", W - 0.08, W, Y0, -0.08, 2.6, 3.4)
for x in (0.35, 1.25, 2.15):
    a.box("button", x - 0.08, x + 0.08, -0.13, -0.07, 2.92, 3.08, bevel=0)
for y in (-1.45, -2.35, -3.25):
    a.box("button", W - 0.13, W - 0.07, y - 0.08, y + 0.08, 2.92, 3.08, bevel=0)
# угловая стойка ступенями: база, ствол, капитель
a.box("gold", W - 0.85, W, -0.85, 0.0, 0.28, 1.2)
a.box("gold", W - 0.7, W, -0.7, 0.0, 1.18, 3.92)
a.box("gold2", W - 0.85, W, -0.85, 0.0, 3.9, 4.15)
a.box("gold", W - 1.0, W, -1.0, 0.0, 4.13, 4.42)
# камни на стойке: восьмигранный рубин в оправе (как на гребне трона) и изумруд сбоку
a.prism("gold2", S.octagon(W - 0.62, W - 0.08, 2.64, 3.36, 0.16), -0.78, -0.68, axis="y")
a.prism("ruby", S.octagon(W - 0.54, W - 0.16, 2.74, 3.26, 0.12), -0.85, -0.76, axis="y")
a.box("ruby2", W - 0.46, W - 0.36, -0.87, -0.84, 3.06, 3.16, bevel=0)
a.box("glint", W - 0.48, W - 0.43, -0.89, -0.86, 3.12, 3.18, bevel=0)
a.box("gold2", W - 0.78, W - 0.68, -0.6, -0.1, 2.72, 3.28)
a.box("emerald", W - 0.84, W - 0.76, -0.52, -0.18, 2.82, 3.18, bevel=0)
# карниз в две ступени и зубцы с камнями (как гребень трона)
a.box("gold2", X0, W + T, -0.18, T, 4.38, 4.6)
a.box("gold2", W - 0.18, W + T, Y0, -0.18, 4.38, 4.6)
a.box("gold", X0, W + T, -0.36, T, 4.58, 5.0)
a.box("gold", W - 0.36, W + T, Y0, -0.36, 4.58, 5.0)
for i, x in enumerate((0.45, 1.6, 2.75)):
    a.frustum("gold", (x - 0.26, x + 0.26, 0.0, 0.52), (x, x, 0.26, 0.26), 4.98, 5.62, bevel=0)
    a.box("sapphire" if i % 2 == 0 else "emerald", x - 0.1, x + 0.1, -0.41, -0.35, 4.69, 4.89, bevel=0)
for i, y in enumerate((-1.0, -2.15, -3.3)):
    a.frustum("gold", (W + 0.04, W + 0.56, y - 0.26, y + 0.26), (W + 0.3, W + 0.3, y, y), 4.98, 5.62, bevel=0)
    a.box("emerald" if i % 2 == 0 else "sapphire", W - 0.41, W - 0.35, y - 0.1, y + 0.1, 4.69, 4.89, bevel=0)

sample = a.build(collection)
S.TEX = 2048  # the sample is larger than the vase: 2048 px gives the same texel density as the vase's 1024 px map
uv = S.bake(sample, a, OUT, "Sample_GoldWall")
print("SAMPLE", json.dumps(a.stats, ensure_ascii=False), {k: round(v, 3) for k, v in uv.items()}, flush=True)


# ── Настоящие утверждённые модели с их картами ───────────────────────────────────────────────────────────────
DENSITY = {}


def reference(tag, fbx, prefix, at):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=fbx)
    objs = [o for o in bpy.data.objects if o not in before]
    mat = bpy.data.materials.new(f"M_{tag}")
    mat.use_nodes = True
    mat.use_backface_culling = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.5
    col = nt.nodes.new("ShaderNodeTexImage")
    col.image = bpy.data.images.load(prefix + "_color.png")
    nt.links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    nrm = nt.nodes.new("ShaderNodeTexImage")
    nrm.image = bpy.data.images.load(prefix + "_normal.png")
    nrm.image.colorspace_settings.name = "Non-Color"
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(nrm.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    root = bpy.data.objects.new(f"Root_{tag}", None)
    collection.objects.link(root)
    for o in objs:
        if o.type == "MESH":
            o.data.materials.clear()
            o.data.materials.append(mat)
        if o.parent is None:
            o.parent = root
    root.location = at
    area = surf = 0.0
    for o in objs:
        if o.type == "MESH":
            me = o.data
            me.calc_loop_triangles()
            data = me.uv_layers.active.data
            for lt in me.loop_triangles:
                p0, p1, p2 = (Vector(data[i].uv) for i in lt.loops)
                area += abs((p1 - p0).cross(p2 - p0)) / 2
                surf += lt.area
    DENSITY[tag] = round(col.image.size[0] * (area / surf) ** 0.5, 1) if surf else 0
    return root


vase = reference("VaseV13", os.path.join(REPO, "assets", "models", "ArtV13_Vase.fbx"),
                 os.path.join(REPO, "assets", "textures", "art", "v13_vase"), (-2.7, -3.0, 0.0))
throne = reference("GoldenThrone", os.path.join(REPO, "assets", "models", "art", "GoldenThrone.fbx"),
                   os.path.join(REPO, "assets", "textures", "art", "GoldenThrone"), (6.7, -3.6, 0.0))

# ── Кадры: одна студия (art_style.Preview — та же, что у утверждённых рендеров), один свет, одна камера ──────
prev = S.Preview(collection)
prev.aim_lights(Vector((2.0, 0, 0)))
shots = [
    ("01_all", (-3.0, -22.0, 7.2), (2.0, -2.0, 2.6), 50, (1920, 1080)),
    ("02_vase_and_wall", (-3.2, -11.5, 3.0), (-1.1, -1.8, 1.9), 55, (1920, 1080)),
    ("03_wall_and_throne", (5.8, -13.5, 3.8), (5.2, -2.4, 2.5), 55, (1920, 1080)),
    ("04_belt_close", (0.6, -5.0, 3.4), (2.5, -0.4, 3.0), 70, (1920, 1080)),
]
for name, eye, target, lens, res in shots:
    prev.shot(os.path.join(OUT, name + ".png"), eye, target, lens, res)
    print("SHOT", name, flush=True)
with open(os.path.join(OUT, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump({"sample": {**a.stats, **{k: round(v, 3) for k, v in uv.items()}}, "reference_texels_per_stud": DENSITY},
              f, ensure_ascii=False, indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "sample_d39.blend"))
print("DONE", flush=True)
