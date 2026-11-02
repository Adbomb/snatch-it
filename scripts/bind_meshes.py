"""Вписывает MeshId после импорта FBX в Studio (D40): предметы — Config/ItemModels (MESHES), части пса —
Config/BossModels (DOG_MESHES). Вход — JSON {имя объекта импорта: MeshId}, который собирает сценарий в Studio по
импортированным MeshPart: Art_<id> → предмет <id>, Boss1_Dog<Часть> → часть пса. turn — поворот после импорта
(градусы вокруг Y), если меши повёрнуты относительно Blender.
Запуск: python scripts/bind_meshes.py <meshids.json> [--item-turn 180] [--dog-turn 180]
"""

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS = os.path.join(ROOT, "src", "shared", "Config", "ItemModels.luau")
BOSSES = os.path.join(ROOT, "src", "shared", "Config", "BossModels.luau")


def table(entries):
    lines = ["{"] + [f"\t{k} = {v}," for k, v in sorted(entries.items())] + ["}"]
    return "\n".join(lines)


def replace_block(text, name, entries):
    pattern = re.compile(r"(local %s: \{ \[string\]: number \} = )\{.*?\n?\}" % name, re.S)
    if not pattern.search(text):
        raise SystemExit(f"не найден блок {name}")
    return pattern.sub(lambda m: m.group(1) + table(entries), text, count=1)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--item-turn", type=float, default=None)
    ap.add_argument("--dog-turn", type=float, default=None)
    args = ap.parse_args()
    ids = json.load(open(args.json, encoding="utf-8"))
    items, dog = {}, {}
    for name, mesh in ids.items():
        mesh = int(str(mesh).replace("rbxassetid://", ""))
        if name.startswith("Art_"):
            items[name[4:]] = mesh
        elif name.startswith("Boss1_Dog"):
            dog[name[len("Boss1_Dog"):]] = mesh
    text = open(ITEMS, encoding="utf-8").read()
    text = replace_block(text, "MESHES", items)
    if args.item_turn is not None:
        text = text.replace("\t\tturn = 0,\n", "\t\tturn = %g,\n" % args.item_turn)
    open(ITEMS, "w", encoding="utf-8", newline="\n").write(text)
    text = open(BOSSES, encoding="utf-8").read()
    text = replace_block(text, "DOG_MESHES", dog)
    if args.dog_turn is not None:
        text = text.replace("\t\tturn = 0,\n", "\t\tturn = %g,\n" % args.dog_turn)
    open(BOSSES, "w", encoding="utf-8", newline="\n").write(text)
    print(f"предметов: {len(items)}, частей пса: {len(dog)}")


if __name__ == "__main__":
    main()
