"""Босс 10 «Король-дракон», этап C: привязка импорта к игре (по образцу boss4_bind_after_import.py).

Вход:
- <импорт.json> — вывод сборщика в Studio (Edit, по вставленным моделям Open Cloud):
  {"parts": {имя: {"meshId": n, "size": [x, y, z]}}, "wings": {"name": имя, "meshId": n, "size": [...],
   "bones": {кость: {"parent": имя | null, "cframe": [12 чисел — CFrame кости от MeshPart перепонок в покое]}}}};
- assets/textures/art/boss10/Boss10_maps.json — {группа: {"color": n, "normal": n}} (ID загруженных карт);
- assets/models/Boss10_Dragon_game.json — что экспортировал Blender (v7_game_export.py).
Проверки: все 55 мешей и перепонки на месте, MeshId — числа без повторов и не из запрещённых, размеры мешей
совпадают с Blender (±3 %), у перепонок есть все кости с весами, карты всех 6 групп. Ошибка — ничего не пишется.
Пишет:
- src/shared/Config/BossModels.luau — DRAGON_MESHES (части, добавочные меши, перепонки) и карты [10];
- assets/models/Boss10_meshids.json — то же для справки;
- assets/models/Boss10_wings_bones.json — кости перепонок в покое (читает scripts/boss10_to_luau.py).
Затем: python scripts/make_looks.py, python scripts/boss10_to_luau.py.
Запуск: python scripts/boss10_bind_after_import.py <импорт.json> [--dry-run]
"""

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOSSES = os.path.join(ROOT, "src", "shared", "Config", "BossModels.luau")
GAME = os.path.join(ROOT, "assets", "models", "Boss10_Dragon_game.json")
MAPS = os.path.join(ROOT, "assets", "textures", "art", "boss10", "Boss10_maps.json")
# запрещённые ассеты — из check_project.FORBIDDEN_IDS, чтобы список был один (как в boss4_bind_after_import.py)
FORBIDDEN = {int(x) for x in re.findall(r'"(\d+)":', re.search(r"FORBIDDEN_IDS = \{(.*?)\}", open(
    os.path.join(ROOT, "scripts", "check_project.py"), encoding="utf-8").read(), re.S).group(1))}
assert FORBIDDEN, "не найден список запрещённых ID в check_project.py"
WING_BONES = {"Body", "WingArmL", "WingForeL", "Finger1L", "Finger2L", "Finger3L", "Finger4L",
              "WingArmR", "WingForeR", "Finger1R", "Finger2R", "Finger3R", "Finger4R"}


def table(entries):
    lines = ["{"] + [f"\t{k} = {v}," for k, v in sorted(entries.items())] + ["}"]
    return "\n".join(lines)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("imported")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    imp = json.load(open(args.imported, encoding="utf-8"))
    game = json.load(open(GAME, encoding="utf-8"))
    maps = json.load(open(MAPS, encoding="utf-8"))
    errors = []
    expected = {**game["parts"], **game["extras"]}
    got = imp["parts"]
    for name in expected:
        if name not in got:
            errors.append(f"нет меша {name}")
    for name in got:
        if name not in expected:
            errors.append(f"лишний меш {name}")
    ids = {}
    for name, rec in list(got.items()) + [(imp["wings"]["name"], imp["wings"])]:
        mid = int(rec["meshId"])
        if mid in FORBIDDEN:
            errors.append(f"{name}: запрещённый ID {mid}")
        if mid in ids.values():
            errors.append(f"{name}: повтор MeshId {mid}")
        ids[name] = mid
    worst = 0.0
    for name, rec in got.items():
        if name not in expected:
            continue
        for a, b in zip(rec["size"], expected[name]["size"]):
            r = abs(a - b) / max(b, 0.05)
            worst = max(worst, r)
            if r > 0.03 and abs(a - b) > 0.02:
                errors.append(f"{name}: размер {rec['size']} против Blender {expected[name]['size']}")
                break
    wings = imp["wings"]
    for a, b in zip(wings["size"], game["membranes"]["size"]):
        if abs(a - b) > max(0.03 * b, 0.02):
            errors.append(f"перепонки: размер {wings['size']} против Blender {game['membranes']['size']}")
            break
    missing = WING_BONES - set(wings["bones"])
    if missing:
        errors.append(f"перепонки: нет костей {sorted(missing)}")
    for r in game["regions"]:
        m = maps.get(r)
        if not m or not str(m.get("color", "")).isdigit() or not str(m.get("normal", "")).isdigit():
            errors.append(f"нет карт группы {r}")
        else:
            for k in ("color", "normal"):
                if int(m[k]) in FORBIDDEN:
                    errors.append(f"карта {r}.{k}: запрещённый ID")
    print(f"мешей {len(got)} + перепонки; наибольшее расхождение размера {worst * 100:.2f} %; костей перепонок "
          f"{len(wings['bones'])}; карт {len(maps)}")
    if errors:
        for e in errors:
            print("ОШИБКА", e)
        raise SystemExit(1)
    if args.dry_run:
        print("проверки прошли (--dry-run: ничего не записано)")
        return

    text = open(BOSSES, encoding="utf-8").read()
    block = ("-- Король-дракон (босс 10, этап C): MeshId частей, добавочных мешей (Body_2 — правая половина корпуса, EyeL/R —\n"
             "-- глаза) и перепонок WingMembranes (skinned) из Open Cloud; вписывает scripts/boss10_bind_after_import.py.\n"
             "local DRAGON_MESHES: { [string]: number } = " + table(ids) + "\n")
    if "local DRAGON_MESHES" in text:
        text = re.sub(r"-- Король-дракон \(босс 10, этап C\).*?\nlocal DRAGON_MESHES: \{ \[string\]: number \} = \{.*?\n\}\n",
                      block.replace("\\", "\\\\"), text, flags=re.S)
    else:
        text = text.replace("\nlocal function ids(", "\n" + block + "\nlocal function ids(")
    lines = ",\n".join(f'\t\t\t{r} = {{ color = "rbxassetid://{maps[r]["color"]}", normal = "rbxassetid://{maps[r]["normal"]}" }}'
                       for r in game["regions"])
    entry = re.search(r"\t\[10\] = \{.*?\n\t\} :: BossModel,", text, re.S)
    if not entry:
        raise SystemExit("не найдена запись [10] в BossModels")
    new = ("\t[10] = {\n\t\tname = \"Король-дракон\",\n\t\tmaps = {\n" + lines + ",\n\t\t},\n"
           "\t\tmeshes = ids(DRAGON_MESHES),\n\t\tturn = 180,\n\t} :: BossModel,")
    text = text[:entry.start()] + new + text[entry.end():]
    with open(BOSSES, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    with open(os.path.join(ROOT, "assets", "models", "Boss10_meshids.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(ids, f, ensure_ascii=False, indent=1, sort_keys=True)
    with open(os.path.join(ROOT, "assets", "models", "Boss10_wings_bones.json"), "w", encoding="utf-8",
              newline="\n") as f:
        json.dump({"mesh": wings["name"], "size": wings["size"], "bones": wings["bones"]}, f, ensure_ascii=False,
                  indent=1)
    print("записано: BossModels [10] (мешей", len(ids), ", карт", len(game["regions"]), "), Boss10_meshids.json,",
          "Boss10_wings_bones.json")


if __name__ == "__main__":
    main()
