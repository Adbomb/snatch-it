"""D48-C, фаза 2 — проверка выгруженных пачек: FBX открывается, каждый меш есть в раскладке и наоборот, у каждого
меша есть UV, треугольников не больше лимита Roblox на один меш (20 000), счёт треугольников совпадает с раскладкой.
Запуск: blender --background --factory-startup --python scripts/blender/d48_check_fbx.py -- <репо>
Код возврата 1 — при ошибке.
"""

import json
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
REPO = os.path.abspath(argv[0]) if argv else os.getcwd()
LIMIT = 20000
failed = 0


def check(ok, text):
    global failed
    print(("  ок   " if ok else "  ОШИБКА ") + text, flush=True)
    if not ok:
        failed += 1


for pack, key in (("Pack3_d48", "d48"), ("Pack4_d48_defense", "d48_defense")):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    fbx = os.path.join(REPO, "assets", "models", f"{pack}.fbx")
    layout = json.load(open(os.path.join(REPO, "assets", "models", f"{pack}.layout.json"), encoding="utf-8"))[key]
    bpy.ops.import_scene.fbx(filepath=fbx)
    meshes = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    expected = {f"{model}_{role}": info for model, data in layout.items() for role, info in data["roles"].items()}
    print(f"{pack}: мешей в FBX {len(meshes)}, в раскладке {len(expected)}, моделей {len(layout)}")
    check(set(meshes) == set(expected), f"{pack}: имена мешей совпадают с раскладкой")
    no_uv = [n for n, o in meshes.items() if not o.data.uv_layers]
    check(not no_uv, f"{pack}: у всех мешей есть UV" + (f" (нет у {no_uv[:3]})" if no_uv else ""))
    worst = max(meshes.values(), key=lambda o: sum(len(p.vertices) - 2 for p in o.data.polygons))
    wt = sum(len(p.vertices) - 2 for p in worst.data.polygons)
    check(wt <= LIMIT, f"{pack}: самый тяжёлый меш {worst.name} — {wt} треугольников (лимит {LIMIT})")
    diff = [n for n, o in meshes.items() if n in expected and
            sum(len(p.vertices) - 2 for p in o.data.polygons) != expected[n]["triangles"]]
    check(not diff, f"{pack}: треугольники совпадают с раскладкой" + (f" (расходятся {diff[:3]})" if diff else ""))
    total = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes.values())
    print(f"{pack}: всего треугольников в пачке {total}")
print("ИТОГ:", "ошибок нет" if not failed else f"ошибок {failed}")
sys.exit(1 if failed else 0)
