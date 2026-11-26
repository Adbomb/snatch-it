"""Быстрый просмотр эскизов существ босса 7: каждое — отдельный кадр 3/4 (как hero) без конвейера и отчётов.

Запуск: blender --background --factory-startup --python scripts/blender/boss7/preview.py -- <репо> <папка> [id…]
Кадры <папка>/<id>.png (600²) — только для правки форм; в лист идут кадры creature_kit (creatures.py).
"""

import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "concepts510"))
import ck  # noqa: E402
import creatures  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
out = os.path.abspath(argv[1])
only = argv[2:]
os.makedirs(out, exist_ok=True)
for item_id, make, title, rarity in creatures.CREATURES:
    if only and item_id not in only:
        continue
    col = ck.reset_scene()
    art = make()
    obj = art.build(col)
    cam = ck.studio(col, size=0.5, bg=(0.7, 0.76, 0.86))
    lo, hi = ck.bounds([obj])
    size = max(hi - lo)
    c = (lo + hi) / 2
    d = 2.7 * size + 1.0
    bpy.context.scene.eevee.taa_render_samples = 16
    ck.shot(cam, os.path.join(out, f"{item_id}.png"), (c.x - 0.6 * d, c.y - 0.86 * d, c.z + 0.5 * size),
            (c.x, c.y, c.z - 0.04 * size), 75, (600, 600))
    print("PREVIEW", item_id, art.stats["tris"], art.stats["flipped"], len(art.stats["coplanar"]), flush=True)
