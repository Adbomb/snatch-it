"""Вписывает загруженные карты предметов в Config/ItemModels (D39, D42): для каждого предмета — строка
<id> = model(color, normal, V(размер)), размер берётся из Config/Items (размер модели из Blender). Вход — JSON
{"<id>": {"color": ColorMap, "normal": NormalMap}} с ID, которые выдал Roblox при загрузке PNG из
assets/textures/art/<id>_{color,normal}.png. Новые предметы добавляются в конец таблицы ItemModels (записи с теми же
id заменяются). Запрещённые ID (scripts/check_project.py) не принимаются никогда.

Загружать карты — только аккаунтом владельца, когда Roblox снимет ограничение, и только после того, как владелец сам
посмотрел каждую картинку (docs/RECOVERY_STATUS.md). Этот скрипт ничего не загружает.
Запуск: python scripts/bind_maps.py <maps.json>, затем python scripts/make_looks.py и scripts/bind_meshes.py.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS = os.path.join(ROOT, "src", "shared", "Config", "Items.luau")
MODELS = os.path.join(ROOT, "src", "shared", "Config", "ItemModels.luau")
FORBIDDEN_IDS = {"115188607358965", "91016959329136"}


def asset(value):
    text = str(value).replace("rbxassetid://", "").strip()
    if not text.isdigit():
        raise SystemExit(f"не ID ассета: {value}")
    if text in FORBIDDEN_IDS:
        raise SystemExit(f"запрещённый ассет {text} — не используется никогда")
    return text


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    maps = json.load(open(sys.argv[1], encoding="utf-8"))
    items = open(ITEMS, encoding="utf-8").read()
    sizes = {}
    for item_id, size in re.findall(r'^\w+\(\s*"(\w+)",[^\n]*?V\(([^)]*)\)', items, re.M):
        sizes[item_id] = ", ".join(x.strip() for x in size.split(","))
    text = open(MODELS, encoding="utf-8").read()
    start = text.index("local ItemModels: { [string]: ItemModel } = {")
    end = text.index("\n}\n", start)
    body = text[start:end]
    added, replaced = [], []
    for item_id, pair in sorted(maps.items()):
        if item_id not in sizes:
            raise SystemExit(f"нет предмета {item_id} с размером в Config/Items")
        line = f"\t{item_id} = model({asset(pair['color'])}, {asset(pair['normal'])}, V({sizes[item_id]})),"
        pattern = re.compile(r"^\t%s = model\([^\n]*$" % re.escape(item_id), re.M)
        if pattern.search(body):
            body = pattern.sub(line, body, count=1)
            replaced.append(item_id)
        else:
            body += "\n" + line
            added.append(item_id)
    text = text[:start] + body + text[end:]
    open(MODELS, "w", encoding="utf-8", newline="\n").write(text)
    print(f"добавлено: {len(added)}, заменено: {len(replaced)}")


if __name__ == "__main__":
    main()
