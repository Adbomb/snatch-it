"""Вписывает MeshId после импорта FBX в Studio (D40, D42): предметы — Config/ItemModels (MESHES), части боссов —
Config/BossModels (DOG_MESHES — пёс, TRADER_MESHES — торговец). Вход — JSON {имя объекта импорта: MeshId}, который
собирает сценарий в Studio по импортированным MeshPart: Art_<id> → предмет <id>, Boss1_Dog{Head,Body}_<Часть> → часть
пса, Boss2_Trader{Head,Body,Limbs}_<Часть> → часть торговца. Новые ID добавляются к уже вписанным (прежние не
теряются). Меш предмета вписывается, только если у предмета уже есть запись с картами (scripts/bind_maps.py), иначе
он пропускается с предупреждением. turn — поворот после импорта (градусы вокруг Y), если меши повёрнуты
относительно Blender.
Запуск: python scripts/bind_meshes.py <meshids.json> [--item-turn 180] [--boss-turn 2=180]
"""

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS = os.path.join(ROOT, "src", "shared", "Config", "ItemModels.luau")
BOSSES = os.path.join(ROOT, "src", "shared", "Config", "BossModels.luau")
BOSS_PARTS = {"Boss1_Dog": "DOG_MESHES", "Boss2_Trader": "TRADER_MESHES"}  # префикс объекта импорта → блок


def table(entries):
    if not entries:
        return "{}"
    lines = ["{"] + [f"\t{k} = {v}," for k, v in sorted(entries.items())] + ["}"]
    return "\n".join(lines)


def merge_block(text, name, entries):
    """Добавляет entries к блоку local <name>: { [string]: number } = {…} (совпавшие ключи — заменяет)."""
    pattern = re.compile(r"(local %s: \{ \[string\]: number \} = )\{(.*?)\n?\}" % name, re.S)
    m = pattern.search(text)
    if not m:
        raise SystemExit(f"не найден блок {name}")
    merged = {k: int(v) for k, v in re.findall(r"(\w+) = (\d+),", m.group(2))}
    merged.update(entries)
    return text[:m.start()] + m.group(1) + table(merged) + text[m.end():], len(merged)


def set_boss_turn(text, boss, turn):
    pattern = re.compile(r"(\t\[%d\] = \{.*?\n\t\tturn = )[-\d.]+(,)" % boss, re.S)
    if not pattern.search(text):
        raise SystemExit(f"не найден turn у BossModels[{boss}]")
    return pattern.sub(lambda m: m.group(1) + ("%g" % turn) + m.group(2), text, count=1)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--item-turn", type=float, default=None)
    ap.add_argument("--boss-turn", action="append", default=[], help="номер=градусы, например 2=180")
    args = ap.parse_args()
    ids = json.load(open(args.json, encoding="utf-8"))
    items, parts = {}, {block: {} for block in BOSS_PARTS.values()}
    unknown = []
    for name, mesh in ids.items():
        mesh = int(str(mesh).replace("rbxassetid://", ""))
        if name.startswith("Art_"):
            items[name[4:]] = mesh
            continue
        prefix = next((p for p in BOSS_PARTS if name.startswith(p)), None)
        if prefix:
            parts[BOSS_PARTS[prefix]][name.rsplit("_", 1)[-1]] = mesh  # Boss2_TraderHead_Jaw → Jaw
        else:
            unknown.append(name)

    text = open(ITEMS, encoding="utf-8").read()
    with_maps = set(re.findall(r"^\t(\w+) = model\(", text, re.M))
    skipped = sorted(i for i in items if i not in with_maps)
    items = {i: m for i, m in items.items() if i in with_maps}
    text, item_total = merge_block(text, "MESHES", items)
    if args.item_turn is not None:
        text = text.replace("\t\tturn = 0,\n", "\t\tturn = %g,\n" % args.item_turn)
    open(ITEMS, "w", encoding="utf-8", newline="\n").write(text)

    text = open(BOSSES, encoding="utf-8").read()
    totals = {}
    for block, entries in parts.items():
        text, totals[block] = merge_block(text, block, entries)
    for spec in args.boss_turn:
        boss, turn = spec.split("=")
        text = set_boss_turn(text, int(boss), float(turn))
    open(BOSSES, "w", encoding="utf-8", newline="\n").write(text)

    print(f"предметов: +{len(items)} (всего {item_total}); частей пса: всего {totals['DOG_MESHES']}; "
          f"частей торговца: всего {totals['TRADER_MESHES']}")
    if skipped:
        print("пропущены (нет карт в ItemModels — сначала scripts/bind_maps.py): " + ", ".join(skipped))
    if unknown:
        print("не распознаны: " + ", ".join(sorted(unknown)))


if __name__ == "__main__":
    main()
