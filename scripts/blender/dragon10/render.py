"""Кадры эталона Короля-дракона v2 (босс 10): без текстур, цветные, крупные планы, счёт треугольников.

Запуск: blender --background --factory-startup --python scripts/blender/dragon10/render.py -- <репо> <задача>
Задачи: clay — спереди / сбоку / сзади / 3/4 в однотонном материале; color — те же ракурсы в цвете; close — голова,
корона, крыло, броня, хвост; stats — треугольники по частям (JSON). Кадры — assets/concepts/bosses_5_10/boss10_v2/raw/.
Материалы — процедурные (чешуя — Voronoi с рельефом, золото, бархат); для игры их запекают в карты, как у Сфинкса.
Зависит от dragon.py, dk.py и concepts510/ck.py (студия, камера).
"""

import json
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "concepts510"))
import ck  # noqa: E402
import dragon  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
REPO, TASK = os.path.abspath(argv[0]), argv[1]
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss10_v2", "raw")
os.makedirs(OUT, exist_ok=True)

COLORS = {
    "scale": ("C8283A", 0.5), "scaleD": ("8A1626", 0.5), "belly": ("F3D9A0", 0.55), "bellyD": ("C9A066", 0.6),
    "gold": ("F2C230", 0.3), "goldD": ("B07A12", 0.45), "ivory": ("EFE6CF", 0.5), "eye": ("FFD23F", 0.4),
    "dark": ("1A0A10", 0.6), "white": ("FFFFFF", 0.3), "wing": ("7A1A33", 0.6), "mantle": ("4E1A63", 0.85),
    "ermine": ("F6F4EE", 0.8), "ruby": ("E0204A", 0.2), "sapphire": ("2F6BFF", 0.2), "emerald": ("22C77A", 0.2),
    "velvet": ("B3122E", 0.85), "mouth": ("4A0A14", 0.8),
}


def lin(hexcode):
    c = [int(hexcode[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def principled(name, hexcode, rough=0.5, metal=0.0, emit=0.0, sheen=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*lin(hexcode), 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*lin(hexcode), 1)
        b.inputs["Emission Strength"].default_value = emit
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    return m, b


def scaled(name, hexcode, dark, rough, density=3.4, bump=0.35):
    """Чешуя: ячейки Voronoi по объекту, тёмный шов и мягкий рельеф (запекается в цвет и нормали)."""
    m, b = principled(name, hexcode, rough)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = density
    vor.inputs["Randomness"].default_value = 0.35  # ровные ряды чешуи, а не «трещины»
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.0, 0.06
    ramp.color_ramp.elements[0].color = (*lin(dark), 1)
    ramp.color_ramp.elements[1].color = (*lin(hexcode), 1)
    bmp = nt.nodes.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = bump
    bmp.inputs["Distance"].default_value = 0.04
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    nt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(vor.outputs["Distance"], bmp.inputs["Height"])
    nt.links.new(bmp.outputs["Normal"], b.inputs["Normal"])
    return m


def materials(clay):
    if clay:
        m, _ = principled("Clay", "B9B2A8", 0.62)
        return {k: m for k in COLORS}
    mats = {}
    for k, (code, rough) in COLORS.items():
        if k == "scale":
            mats[k] = scaled(k, code, "A21C30", rough, density=7.0, bump=0.18)
        elif k in ("gold", "goldD"):
            mats[k], _ = principled(k, code, rough, metal=0.35)
        elif k == "eye":
            mats[k], _ = principled(k, code, rough, emit=1.4)
        elif k in ("ruby", "sapphire", "emerald"):
            mats[k], _ = principled(k, code, rough, emit=0.25)
        elif k in ("mantle", "velvet", "ermine"):
            mats[k], _ = principled(k, code, rough, sheen=0.6)
        else:
            mats[k], _ = principled(k, code, rough)
    return mats


def scene(clay, quality=None):
    col = ck.reset_scene()
    parts = dragon.build(quality)
    mats = materials(clay)
    objs = [m.build(col, mats) for m in parts.values()]
    cam = ck.studio(col, size=1.9, bg=(0.72, 0.74, 0.8))
    bpy.context.scene.view_settings.exposure = -0.55 if clay else -0.3
    return objs, parts, cam


def views(objs, cam, prefix):
    lo, hi = ck.bounds(objs)
    h = hi.z - lo.z
    cz = (lo.z + hi.z) / 2
    for label, ang in (("front", 0), ("side", -90), ("back", 180), ("34", -35)):
        for o in objs:
            o.rotation_euler = (0, 0, math.radians(ang))
        span = max(h, (hi.x - lo.x) if ang in (0, 180, -35) else (hi.y - lo.y) + 1.0)
        dist = 1.12 * span / (2 * math.tan(math.atan(18 / 55)))
        ck.shot(cam, os.path.join(OUT, f"{prefix}_{label}.png"), (0, -dist, cz + 0.12 * h), (0, 0, cz), 55, (1100, 1100))
    for o in objs:
        o.rotation_euler = (0, 0, 0)


CLOSE = {
    "head": ((-3.0, -6.4, 9.6), (0, -1.0, 8.6), 70),
    "crown": ((-1.6, -3.4, 11.0), (0, -0.42, 9.55), 70),
    "wing": ((6.0, 16.5, 8.8), (4.0, 3.4, 6.8), 45),
    "armor": ((-4.0, -8.5, 6.6), (0.6, -0.4, 4.8), 55),
    "tail": ((6.8, -2.6, 2.0), (3.3, 1.5, 0.6), 45),
}


def stats(parts, objs, name="stats"):
    per = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs}
    lo, hi = ck.bounds(objs)
    data = {"parts": len(objs), "triangles": sum(per.values()), "per_part": per,
            "size": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)]}
    with open(os.path.join(OUT, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("TRIS", data["triangles"], "PARTS", data["parts"], flush=True)


if TASK in ("clay", "all"):
    objs, parts, cam = scene(True)
    views(objs, cam, "clay")
    stats(parts, objs)
if TASK in ("color", "all"):
    objs, parts, cam = scene(False)
    views(objs, cam, "color")
if TASK in ("close", "all"):
    objs, parts, cam = scene(False)
    for name, (eye, target, lens) in CLOSE.items():
        ck.shot(cam, os.path.join(OUT, f"close_{name}.png"), eye, target, lens, (1100, 1100))
if TASK in ("game", "all"):  # игровая копия: те же формы, меньше граней — кадры для сравнения и счёт
    objs, parts, cam = scene(False, dragon.GAME)
    stats(parts, objs, "stats_game")
    for o in objs:
        o.rotation_euler = (0, 0, math.radians(-35))
    lo, hi = ck.bounds(objs)
    cz = (lo.z + hi.z) / 2
    ck.shot(cam, os.path.join(OUT, "game_34.png"), (0, -21.5, cz + 1.3), (0, 0, cz), 55, (1100, 1100))
    for o in objs:
        o.rotation_euler = (0, 0, 0)
    ck.shot(cam, os.path.join(OUT, "game_head.png"), CLOSE["head"][0], CLOSE["head"][1], 70, (1100, 1100))
if TASK == "stats":
    objs, parts, cam = scene(True)
    stats(parts, objs)
print("DONE", TASK, OUT, flush=True)
