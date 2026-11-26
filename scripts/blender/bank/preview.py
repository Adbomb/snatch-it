"""Быстрый просмотр существ коллекции «Банк»: кадр 3/4 (как hero) на каждое, без конвейера; числа — треугольники
без подставки, перевёрнутые и совпадающие грани.

Запуск: blender --background --factory-startup --python scripts/blender/bank/preview.py -- <папка> <модуль> [id…]
модуль — common / rare / epic / legendary. Кадры <папка>/<id>.png (600²) — только для правки форм.
"""

import importlib
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "concepts510"))
import ck  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
out = os.path.abspath(argv[0])
mod = importlib.import_module(argv[1])
only = argv[2:]
os.makedirs(out, exist_ok=True)
for item_id, make, title, rarity in mod.ITEMS:
    if only and item_id not in only:
        continue
    col = ck.reset_scene()
    art = make()
    obj = art.build(col)
    stand = sum(1 for p, g in zip(obj.data.polygons, art.face_groups) if g == "Stand" for _ in range(len(p.vertices) - 2))
    cam = ck.studio(col, size=0.5, bg=(0.7, 0.76, 0.86))
    lo, hi = ck.bounds([obj])
    size = max(hi - lo)
    c = (lo + hi) / 2
    d = 2.7 * size + 1.0
    bpy.context.scene.eevee.taa_render_samples = 16
    ck.shot(cam, os.path.join(out, f"{item_id}.png"), (c.x - 0.6 * d, c.y - 0.86 * d, c.z + 0.5 * size),
            (c.x, c.y, c.z - 0.04 * size), 75, (600, 600))
    print("PREVIEW", item_id, "tris_no_stand", art.stats["tris"] - stand, "flipped", art.stats["flipped"], "coplanar",
          len(art.stats["coplanar"]), flush=True)
