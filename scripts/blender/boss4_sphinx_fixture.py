"""Босс 4 «Сфинкс-лежебока»: данные для игры и для предпросмотра в Studio без загрузки мешей.

Открывает игровую копию assets/models/Boss4_Sphinx_game.blend (7 916 треугольников, утверждённая v2 не меняется) и пишет:
  assets/models/Boss4_Sphinx.colors.json — средний цвет каждой части по её карте цвета (по площади граней): цвет
    блоков-заготовок в игре, пока меши не загружены (scripts/boss4_to_luau.py кладёт его в Config/Boss4SphinxRig);
  src/server/Tests/MeshFixture/Boss4_<Часть>.luau — геометрия части для EditableMesh (Tests/BossMeshPreview; папка в
    .gitignore — в репозиторий не идёт): вершины в осях Roblox от точки вращения части, вершина — общая у граней с той же
    позицией, нормалью и UV (модель с острыми рёбрами), 13 байт на вершину — позиция int16 ×3 / 1000, нормаль int8 ×3 / 127, UV uint16 ×2 /
    65535 (v перевёрнут, как при импорте FBX); треугольник — uint16 ×3. Всё в base64.
Запуск: blender --background assets/models/Boss4_Sphinx_game.blend --python scripts/blender/boss4_sphinx_fixture.py -- <репо>
"""

import base64
import json
import os
import struct
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO = os.path.abspath(argv[0])
OUT = os.path.join(REPO, "src", "server", "Tests", "MeshFixture")
POS = 1000
os.makedirs(OUT, exist_ok=True)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def image_of(obj):
    """Картинка карты цвета у материала части (узел Image Texture, подключённый к цвету)."""
    for slot in obj.material_slots:
        mat = slot.material
        if mat and mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image and "color" in node.image.name.lower():
                    return node.image
            for node in mat.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image:
                    return node.image
    return None


cache = {}


def pixels(img):
    if img.name not in cache:
        w, h = img.size
        cache[img.name] = (w, h, list(img.pixels[:]))
    return cache[img.name]


def sample(img, u, v):
    w, h, px = pixels(img)
    x = clamp(int(u * w), 0, w - 1)
    y = clamp(int(v * h), 0, h - 1)
    i = (y * w + x) * 4
    return px[i], px[i + 1], px[i + 2]


def to_srgb(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


colors, total = {}, 0
for obj in sorted((o for o in bpy.context.scene.objects if o.name.startswith("Boss4_Sphinx")), key=lambda o: o.name):
    part = obj.name.rsplit("_", 1)[1]
    me = obj.data
    me.calc_loop_triangles()
    uv = me.uv_layers.active.data
    img = image_of(obj)
    acc, area = [0.0, 0.0, 0.0], 0.0
    vb, tb = bytearray(), bytearray()
    n = 0
    seen = {}  # одинаковые вершины (позиция, нормаль, UV) — одна: бюджет EditableMesh в Studio невелик
    for tri in me.loop_triangles:
        ids = []
        for li in tri.loops:
            co = me.vertices[me.loops[li].vertex_index].co
            x, y, z = co.x, co.z, -co.y  # Blender → Roblox
            if max(abs(x), abs(y), abs(z)) * POS > 32767:
                raise SystemExit(f"{part}: вершина вне диапазона int16")
            nx, ny, nz = tri.normal.x, tri.normal.z, -tri.normal.y
            u, v = uv[li].uv
            packed = struct.pack("<hhhbbbHH", round(x * POS), round(y * POS), round(z * POS),
                                 clamp(round(nx * 127), -127, 127), clamp(round(ny * 127), -127, 127),
                                 clamp(round(nz * 127), -127, 127), clamp(round(u * 65535), 0, 65535),
                                 clamp(round((1 - v) * 65535), 0, 65535))
            if packed not in seen:
                seen[packed] = n
                vb += packed
                n += 1
            ids.append(seen[packed])
        tb += struct.pack("<HHH", *ids)
        if img:
            cu = sum(uv[li].uv[0] for li in tri.loops) / 3
            cv = sum(uv[li].uv[1] for li in tri.loops) / 3
            r, g, b = sample(img, cu, cv)
            acc = [acc[0] + r * tri.area, acc[1] + g * tri.area, acc[2] + b * tri.area]
            area += tri.area
    assert n < 65536, f"{part}: вершин {n}"
    if area > 0:
        rgb = [clamp(round(to_srgb(c / area) * 255), 0, 255) for c in acc]
        colors[part] = "{:02X}{:02X}{:02X}".format(*rgb)
    total += len(me.loop_triangles)
    text = "\n".join([
        f"-- Геометрия части {part} босса 4 для предпросмотра без загрузки (scripts/blender/boss4_sphinx_fixture.py).",
        "-- Только локально (.gitignore). Читает Tests/BossMeshPreview.",
        "return {",
        f'\tpart = "{part}",',
        f'\tmap = "{obj.name.split("_")[1].replace("Sphinx", "")}",',
        f"\tpos = {POS},",
        f"\tnv = {n},",
        f"\tnt = {len(me.loop_triangles)},",
        f'\tv = "{base64.b64encode(bytes(vb)).decode()}",',
        f'\tt = "{base64.b64encode(bytes(tb)).decode()}",',
        "}",
        "",
    ])
    with open(os.path.join(OUT, f"Boss4_{part}.luau"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"FIX {part:9s} треугольников {len(me.loop_triangles):5d} вершин {n:5d} цвет {colors.get(part)} {len(text)} знаков")
with open(os.path.join(REPO, "assets", "models", "Boss4_Sphinx.colors.json"), "w", encoding="utf-8") as f:
    json.dump(colors, f, ensure_ascii=False, indent=1)
print("FIX_OK треугольников", total, "частей", len(colors))
