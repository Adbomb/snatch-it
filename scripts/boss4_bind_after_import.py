"""Босс 4: привязка мешей после ручного импорта двух FBX в Studio (File → Import 3D).

Порядок:
1. Владелец импортирует assets/models/Boss4Creatures_all.fbx (30 существ, 218 частей Art_<id>_<Часть>) и
   assets/models/Boss4_Sphinx_game.fbx (27 частей Boss4_Sphinx{Body,Head,Limbs}_<Часть>).
2. Claude запускает в Studio (Edit) scripts/studio/collect_boss4_meshes.luau через MCP execute_luau и сохраняет
   вывод (блок BOSS4_IMPORT … END) в текстовый файл.
3. python scripts/boss4_bind_after_import.py <вывод.txt> — проверка и привязка; --dry-run — то же на копиях
   конфигов во временной папке (файлы проекта не меняются); --synthetic вместо файла — самопроверка на
   выдуманных ID с размерами из скелетов (всегда вместе с --dry-run).

Проверки (любая ошибка — ничего не пишется, код выхода 1):
- имена: все 218 видимых частей 30 существ (Config/CreatureRigs, сверено с Boss4Creatures.index.json) и 27 частей
  Сфинкса (Config/Boss4SphinxRig: группа Body/Head/Limbs в имени = карта части); нет пропусков и лишних; повтор
  имени (импорт дважды) — предупреждение, берётся первый;
- MeshId: число, не запрещённый ассет, не ID карты (перепутан с текстурой), разные у разных частей;
- размеры: импорт против габарита части в скелете — общий масштаб k (игра всё равно ставит размер сама) и
  каждая часть в пределах допуска от k × габарит (иначе меш, скорее всего, от другой части);
- карты: у каждого существа ItemModels и Server/Looks совпадают с assets/textures/art/boss4/Boss4_maps.json; у
  Сфинкса шаблоны Looks/Boss4_{Body,Head,Limbs} совпадают с BossModels[4].maps; свои карты меша из импорта
  (метки S/T) игра не использует — сведения;
- скелеты и анимации: суставы и клипы собираются кодом (Motor6D, CreatureRigs, Boss4SphinxClips), из FBX они не
  нужны — кости и анимации в импорте отмечаются сведением; после привязки у каждой части скелета есть меш.
Потом scripts/bind_meshes.py вписывает ID (ItemModels.CREATURE_MESHES, BossModels.SPHINX_MESHES), сверка
результата (прочие блоки не тронуты) и проверки проекта (check_project.py, Lune check_creatures).
Зависит от scripts/bind_meshes.py, Config/CreatureRigs, Config/Boss4SphinxRig, Config/ItemModels, Config/BossModels.
"""

import argparse
import importlib
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "src", "shared", "Config")
LOOKS = os.path.join(ROOT, "src", "server", "Looks")
INDEX = os.path.join(ROOT, "assets", "models", "art", "boss4", "Boss4Creatures.index.json")
MAPS = os.path.join(ROOT, "assets", "textures", "art", "boss4", "Boss4_maps.json")
OUT_JSON = os.path.join(ROOT, "assets", "models", "Boss4_meshids.json")
# запрещённые ассеты (бан 2026-11-02) — из check_project.FORBIDDEN_IDS, чтобы список был один
FORBIDDEN = set(re.findall(r'"(\d+)":', re.search(r"FORBIDDEN_IDS = \{(.*?)\}", open(
    os.path.join(ROOT, "scripts", "check_project.py"), encoding="utf-8").read()).group(1)))
NUM = r"(-?[\d.]+)"
VEC = r"(?:V|Vector3\.new)\(" + NUM + r", " + NUM + r", " + NUM + r"\)"


def read(path):
    return open(path, encoding="utf-8").read()


def creature_expectations():
    """{id: {часть: (x, y, z)}} — видимые части существ босса 4 с габаритами из CreatureRigs."""
    index = json.load(open(INDEX, encoding="utf-8"))
    ids = [item["id"] for item in index["items"]]
    text = read(os.path.join(CONFIG, "CreatureRigs.luau"))
    out, problems = {}, []
    for item in index["items"]:
        m = re.search(r"^\t%s = \{\n(.*?)\n\t\},?$" % item["id"], text, re.S | re.M)
        if not m:
            problems.append(f"{item['id']}: нет в Config/CreatureRigs")
            continue
        parts = {}
        rig_names = set()
        for name, rest in re.findall(r"^\t\t\t(\w+) = \{ (.*)$", m.group(1), re.M):
            rig_names.add(name)
            if "hidden = true" in rest:
                continue
            size = re.search(r"size = " + VEC, rest)
            parts[name] = tuple(float(v) for v in size.groups())
        index_names = {p["name"] for p in item["parts"]}
        if index_names != rig_names:
            problems.append(f"{item['id']}: части индекса и скелета расходятся: {sorted(index_names ^ rig_names)}")
        out[item["id"]] = parts
    return ids, out, problems


def sphinx_expectations():
    """{часть: (группа карты, (x, y, z))} из Config/Boss4SphinxRig и порядок частей."""
    text = read(os.path.join(CONFIG, "Boss4SphinxRig.luau"))
    order = re.findall(r'"(\w+)"', re.search(r"Order = \{(.*?)\}", text).group(1))
    parts = {}
    for name in order:
        line = re.search(r"^\t\t%s = \{ (.*)$" % name, text, re.M).group(1)
        size = re.search(r"size = " + VEC, line)
        group = re.search(r'map = "(\w+)"', line).group(1)
        parts[name] = (group, tuple(float(v) for v in size.groups()))
    return order, parts


def texture_ids():
    """Все ID карт босса 4 (существа и Сфинкс) и проблемы согласованности карт."""
    maps = json.load(open(MAPS, encoding="utf-8"))
    items = read(os.path.join(CONFIG, "ItemModels.luau"))
    bosses = read(os.path.join(CONFIG, "BossModels.luau"))
    ids, problems = set(), []
    for item_id, m in maps.items():
        color, normal = (m[k].replace("rbxassetid://", "") for k in ("color", "normal"))
        ids |= {color, normal}
        row = re.search(r"^\t%s = model\((\d+), (\d+), " % item_id, items, re.M)
        if not row or row.groups() != (color, normal):
            problems.append(f"{item_id}: карты в Config/ItemModels не те, что в Boss4_maps.json")
        look = os.path.join(LOOKS, f"{item_id}.model.json")
        if not os.path.exists(look) or color not in read(look) or normal not in read(look):
            problems.append(f"{item_id}: шаблон Server/Looks/{item_id}.model.json не с теми картами")
    block = re.search(r"\t\[4\] = \{(.*?)\n\t\} :: BossModel", bosses, re.S)
    for group in ("Body", "Head", "Limbs"):
        m = block and re.search(group + r' = \{ color = "rbxassetid://(\d+)", normal = "rbxassetid://(\d+)" \}',
                                block.group(1))
        if not m:
            problems.append(f"Сфинкс: нет карт {group} в BossModels[4].maps")
            continue
        ids |= set(m.groups())
        look = os.path.join(LOOKS, f"Boss4_{group}.model.json")
        if not os.path.exists(look) or any(i not in read(look) for i in m.groups()):
            problems.append(f"Сфинкс: шаблон Server/Looks/Boss4_{group}.model.json не с картами BossModels[4]")
    return ids, problems


def parse_collector(text):
    """Строки «имя|MeshId|x,y,z|метки» между BEGIN и END; заголовок — сведения."""
    if "BOSS4_IMPORT v1" not in text or "\nBEGIN" not in text or "\nEND" not in text:
        raise SystemExit("это не вывод scripts/studio/collect_boss4_meshes.luau (нет BOSS4_IMPORT v1 / BEGIN / END)")
    head, body = text.split("\nBEGIN", 1)
    body = body.split("\nEND", 1)[0]
    rows = []
    for line in body.strip().splitlines():
        name, mesh, size, flags = (line.strip().split("|") + [""])[:4]
        rows.append((name, mesh, tuple(float(v) for v in size.split(",")), flags))
    return head.strip(), rows


def synthetic(ids, creatures, order, sphinx):
    """Выдуманный вывод сборщика: все части, ID 9…, размеры из скелетов (как импорт без масштаба)."""
    lines, n = ["BOSS4_IMPORT v1", "синтетика для самопроверки", "BEGIN"], 0
    for item_id in ids:
        for part, size in sorted(creatures[item_id].items()):
            n += 1
            lines.append(f"Art_{item_id}_{part}|{9000000000000 + n}|{size[0]},{size[1]},{size[2]}|")
    for part in order:
        n += 1
        group, size = sphinx[part]
        lines.append(f"Boss4_Sphinx{group}_{part}|{9000000000000 + n}|{size[0]},{size[1]},{size[2]}|")
    lines.append("END")
    return "\n".join(lines)


def check(rows, ids, creatures, order, sphinx, textures, tolerance):
    errors, warnings, notes = [], [], []
    expected = {}
    for item_id in ids:
        for part, size in creatures[item_id].items():
            expected[f"Art_{item_id}_{part}"] = size
    for part in order:
        group, size = sphinx[part]
        expected[f"Boss4_Sphinx{group}_{part}"] = size
    chosen, seen_ids = {}, {}
    for name, mesh, size, flags in rows:
        if name not in expected:
            errors.append(f"{name}: такой части нет в скелетах босса 4")
            continue
        if name in chosen:
            warnings.append(f"{name}: имя повторяется (импорт дважды?) — беру первый ID {chosen[name][0]}")
            continue
        if not re.fullmatch(r"\d{6,20}", mesh):
            errors.append(f"{name}: MeshId «{mesh}» не число (импорт ещё грузится?)")
            continue
        if mesh in FORBIDDEN:
            errors.append(f"{name}: запрещённый ассет {mesh}")
            continue
        if mesh in textures:
            errors.append(f"{name}: MeshId {mesh} — это ID карты, а не меша")
            continue
        if mesh in seen_ids:
            errors.append(f"{name}: тот же MeshId {mesh}, что у {seen_ids[mesh]}")
        seen_ids[mesh] = name
        chosen[name] = (mesh, size)
        if "S" in flags or "T" in flags:
            notes.append(name)
    missing = sorted(set(expected) - set(chosen))
    if missing:
        errors.append(f"нет {len(missing)} частей: " + ", ".join(missing[:12]) + (" …" if len(missing) > 12 else ""))
    ratios = [chosen[n][1][a] / expected[n][a] for n in chosen for a in range(3) if expected[n][a] > 1e-6]
    k = statistics.median(ratios) if ratios else 1.0
    if abs(k - 1) > 0.01:
        warnings.append(f"импорт с общим масштабом ×{k:.4f} — игра ставит размер частей сама, это не мешает")
    for name, (_, size) in chosen.items():
        want = expected[name]
        bad = [a for a in range(3)
               if abs(size[a] - k * want[a]) > max(tolerance * k * want[a], 0.02 * k)]
        if bad:
            errors.append(f"{name}: размер {size} против {tuple(round(k * v, 4) for v in want)} — меш другой части?")
    if notes:
        warnings.append(f"у {len(notes)} мешей импорт добавил свои карты — игра их не берёт (карты из Server/Looks)")
    return chosen, errors, warnings, k


def blocks(text, name):
    m = re.search(r"local %s: \{ \[string\]: number \} = \{(.*?)\n?\}" % name, text, re.S)
    return dict(re.findall(r"(\w+) = (\d+),", m.group(1))) if m else None


def bind(meshids, workdir):
    """bind_meshes.py над конфигами в workdir (копии или сам проект); вывод скрипта."""
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    bm = importlib.import_module("bind_meshes")
    bm.ITEMS = os.path.join(workdir, "ItemModels.luau")
    bm.BOSSES = os.path.join(workdir, "BossModels.luau")
    bm.RIGS = os.path.join(CONFIG, "CreatureRigs.luau")
    saved = sys.argv
    sys.argv = ["bind_meshes.py", meshids]
    try:
        bm.main()
    finally:
        sys.argv = saved


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("collector", nargs="?", help="файл с выводом collect_boss4_meshes.luau")
    ap.add_argument("--synthetic", action="store_true", help="самопроверка на выдуманных ID (только с --dry-run)")
    ap.add_argument("--dry-run", action="store_true", help="привязать в копии конфигов, проект не трогать")
    ap.add_argument("--tolerance", type=float, default=0.03, help="допуск размера части (доля), по умолчанию 3 %%")
    args = ap.parse_args()
    if args.synthetic and not args.dry_run:
        raise SystemExit("--synthetic только вместе с --dry-run")
    if not args.synthetic and not args.collector:
        raise SystemExit("нужен файл с выводом collect_boss4_meshes.luau (или --synthetic --dry-run)")

    ids, creatures, rig_problems = creature_expectations()
    order, sphinx = sphinx_expectations()
    textures, map_problems = texture_ids()
    print(f"ожидается: {len(ids)} существ, {sum(len(p) for p in creatures.values())} частей; Сфинкс {len(order)} частей")
    text = synthetic(ids, creatures, order, sphinx) if args.synthetic else read(args.collector)
    head, rows = parse_collector(text)
    print("сборщик: " + head.replace("\n", " | "))
    chosen, errors, warnings, k = check(rows, ids, creatures, order, sphinx, textures, args.tolerance)
    errors = rig_problems + map_problems + errors
    for w in warnings:
        print("предупреждение: " + w)
    if errors:
        print(f"ОШИБКИ ({len(errors)}) — ничего не записано:")
        for e in errors:
            print("  " + e)
        sys.exit(1)
    print(f"проверки прошли: {len(chosen)} мешей, масштаб ×{k:.4f}, карты 30 существ и 3 группы Сфинкса совпадают")

    meshids = {name: int(mesh) for name, (mesh, _) in sorted(chosen.items())}
    if args.dry_run:
        work = tempfile.mkdtemp(prefix="boss4_bind_")
        for name in ("ItemModels.luau", "BossModels.luau"):
            shutil.copy(os.path.join(CONFIG, name), work)
        out_json = os.path.join(work, "Boss4_meshids.json")
    else:
        work, out_json = CONFIG, OUT_JSON
    before = {name: read(os.path.join(work, name)) for name in ("ItemModels.luau", "BossModels.luau")}
    json.dump(meshids, open(out_json, "w", encoding="utf-8"), indent=0)
    bind(out_json, work)

    # сверка результата: вписаны все части, остальное не тронуто
    after = {name: read(os.path.join(work, name)) for name in before}
    problems = []
    got_c, old_c = blocks(after["ItemModels.luau"], "CREATURE_MESHES"), blocks(before["ItemModels.luau"], "CREATURE_MESHES")
    got_s = blocks(after["BossModels.luau"], "SPHINX_MESHES")
    for item_id in ids:
        for part in creatures[item_id]:
            if got_c.get(f"{item_id}_{part}") != str(meshids[f"Art_{item_id}_{part}"]):
                problems.append(f"{item_id}_{part} не вписан")
    for part in order:
        if got_s.get(part) != str(meshids[f"Boss4_Sphinx{sphinx[part][0]}_{part}"]):
            problems.append(f"Сфинкс {part} не вписан")
    for key, value in old_c.items():
        if got_c.get(key) != value and not any(key.startswith(i + "_") for i in ids):
            problems.append(f"чужая запись {key} изменилась")
    for name, block in (("ItemModels.luau", "MESHES"), ("BossModels.luau", "DOG_MESHES"),
                        ("BossModels.luau", "TRADER_MESHES")):
        if blocks(after[name], block) != blocks(before[name], block):
            problems.append(f"блок {block} изменился")
    if problems:
        print("ОШИБКА сверки после bind_meshes: " + "; ".join(problems[:10]))
        sys.exit(1)
    print(f"вписано: частей существ {sum(len(p) for p in creatures.values())}, частей Сфинкса {len(order)}; "
          "прочие блоки не тронуты" + (f" (копии в {work})" if args.dry_run else ""))
    if args.dry_run:
        shutil.rmtree(work, ignore_errors=True)
        return
    for cmd in (["python", os.path.join(ROOT, "scripts", "check_project.py")],
                ["lune", "run", os.path.join(ROOT, "scripts", "lune", "check_creatures.luau")]):
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        tail = (result.stdout + result.stderr).strip().splitlines()[-3:]
        print(f"{' '.join(cmd[:2])}: код {result.returncode}: " + " | ".join(tail))
    print("дальше: Rojo синхронизирует конфиги → Play → серверные тесты «Босс 4» (меши вместо Part-версии)")


if __name__ == "__main__":
    main()
