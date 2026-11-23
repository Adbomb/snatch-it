"""Кадр одного существа ледяной коллекции (отдельный запуск Blender на каждое — свет студии не копится).

Запуск: blender --background --factory-startup --python scripts/blender/boss5/creature_render.py -- <репо> <номер>
Кадры: assets/concepts/bosses_5_10/boss5_v2/raw/creature{i}_{34,front}.png и creature{i}.json (вне git).
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import creatures  # noqa: E402

C = creatures.C
argv = sys.argv[sys.argv.index("--") + 1:]
REPO, I = os.path.abspath(argv[0]), int(argv[1])
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss5_v2", "raw")
os.makedirs(OUT, exist_ok=True)

col = C.reset_scene()
obj = creatures.build(I, col)[0]
cam = C.studio(col, size=0.5, bg=(0.7, 0.76, 0.86))
bpy.context.scene.view_settings.exposure = -0.3
lo, hi = C.bounds([obj])
obj.location = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
size = hi - lo
span = max(size.x, size.y * 0.8, size.z)
cz = size.z / 2
dist = 1.55 * span / (2 * 18 / 55)
for label, ang in (("34", -35), ("front", 0)):
    obj.rotation_euler = (0, 0, math.radians(ang))
    bpy.context.view_layer.update()
    C.shot(cam, os.path.join(OUT, f"creature{I}_{label}.png"), (0, -dist, cz + span * 0.28), (0, 0, cz * 0.95), 55,
           (900, 900))
name, rarity = creatures.CREATURES[I][:2]
with open(os.path.join(OUT, f"creature{I}.json"), "w", encoding="utf-8") as f:
    json.dump({"name": name, "rarity": rarity, "tris": obj["tris"], "size": [round(v, 2) for v in size]}, f,
              ensure_ascii=False)
print("DONE", I, obj["tris"], flush=True)
