"""Предпросмотр мешей D54 в Studio без загрузки (D55): данные scripts/blender/check_creature_import.py --fixture →
модули src/server/Tests/MeshFixture/<id>.luau (папка в .gitignore — в репозиторий не идёт, после проверки удалить:
сначала файлы, потом папку). Модуль: { id, texSize, tex = base64 RGB, parts = { [часть] = { size, nv, nt, v, t } } };
вершина — 13 байт (позиция int16 ×3 / 10000, нормаль int8 ×3 / 127, UV uint16 ×2 / 65535), треугольник — uint16 ×3.
Читает и собирает EditableMesh — src/server/Tests/CreatureMeshPreview.luau.
Запуск: python scripts/creature_mesh_fixture.py <папка с <id>.json> [id…]
"""

import base64
import json
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "src", "server", "Tests", "MeshFixture")
POS = 10000


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def part_blob(p):
    vb = bytearray()
    for (x, y, z), (nx, ny, nz), (u, v) in zip(p["v"], p["n"], p["uv"]):
        if max(abs(x), abs(y), abs(z)) * POS > 32767:
            raise SystemExit("вершина вне диапазона int16")
        vb += struct.pack("<hhhbbbHH", round(x * POS), round(y * POS), round(z * POS),
                          clamp(round(nx * 127), -127, 127), clamp(round(ny * 127), -127, 127),
                          clamp(round(nz * 127), -127, 127), clamp(round(u * 65535), 0, 65535),
                          clamp(round(v * 65535), 0, 65535))
    tb = bytearray()
    for a, b, c in p["t"]:
        tb += struct.pack("<HHH", a, b, c)
    return base64.b64encode(bytes(vb)).decode(), base64.b64encode(bytes(tb)).decode()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    src = os.path.abspath(sys.argv[1])
    ids = sys.argv[2:] or sorted(f[:-5] for f in os.listdir(src) if f.endswith(".json"))
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for item_id in ids:
        data = json.load(open(os.path.join(src, f"{item_id}.json"), encoding="utf-8"))
        lines = ["-- Предпросмотр меша D54 (scripts/creature_mesh_fixture.py) — не в репозитории, удалить после проверки.",
                 "return {", f'\tid = "{item_id}",', f"\ttexSize = {data['texSize']},", f'\ttex = "{data["tex"]}",',
                 "\tparts = {"]
        for name, p in data["parts"].items():
            v, t = part_blob(p)
            size = ", ".join(f"{c:g}" for c in p["size"])
            lines.append(f'\t\t{name} = {{ size = {{ {size} }}, nv = {len(p["v"])}, nt = {len(p["t"])}, '
                         f'v = "{v}", t = "{t}" }},')
        lines += ["\t},", "}", ""]
        path = os.path.join(OUT, f"{item_id}.luau")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines))
        total += os.path.getsize(path)
    print(f"модулей {len(ids)}, {total / 1e6:.1f} МБ → {OUT}")


if __name__ == "__main__":
    main()
