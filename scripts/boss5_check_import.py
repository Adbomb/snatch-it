"""Босс 5: сверка загруженных мешей (Open Cloud → Studio) со скелетами и запись MeshId.

Вход — вывод сборщика в Studio (Edit, ServerStorage.Boss5Import): строки «имя|MeshId|X,Y,Z» (размер MeshPart = габарит
меша). Сверяет с assets/models/art/boss5/<id>.rig.json (части существ без Stand: имя Art_<id>_<Часть>) и
assets/models/Boss5_Yeti.rig.json (Boss5Yeti<Карта>_<Часть>): все части на месте, лишних нет, MeshId — числа и разные
у разных мешей (одинаковые меши Roblox может склеить в один ID — сведение), размер импорта = габарит части в rig.json
(допуск 2 % + 0.01). Пишет assets/models/Boss5_meshids.json {"creatures": {id: {часть: MeshId}}, "yeti": {часть: MeshId}}.
Запуск: python scripts/boss5_check_import.py <вывод.txt>
"""

import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "assets", "models", "art", "boss5")
YETI = os.path.join(ROOT, "assets", "models", "Boss5_Yeti.rig.json")
OUT = os.path.join(ROOT, "assets", "models", "Boss5_meshids.json")


def main(path):
    got = {}
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^(\S+)\|(\d+)\|([\d.]+),([\d.]+),([\d.]+)", line.strip())
        if m:
            got[m.group(1)] = (m.group(2), [float(m.group(k)) for k in (3, 4, 5)])
    want = {}
    for f in sorted(glob.glob(os.path.join(ART, "*.rig.json"))):
        r = json.load(open(f, encoding="utf-8"))
        for part, spec in r["parts"].items():
            if part != "Stand":
                want[f"Art_{r['id']}_{part}"] = ("c", r["id"], part, spec["size"])
    y = json.load(open(YETI, encoding="utf-8"))
    for part, spec in y["parts"].items():
        want[f"Boss5Yeti{spec['map']}_{part}"] = ("y", None, part, spec["size"])
    errors = []
    missing = sorted(set(want) - set(got))
    extra = sorted(set(got) - set(want))
    if missing:
        errors.append(f"нет в импорте: {missing}")
    if extra:
        errors.append(f"лишние в импорте: {extra}")
    out = {"creatures": {}, "yeti": {}}
    for name, (kind, cid, part, size) in sorted(want.items()):
        if name not in got:
            continue
        mid, isz = got[name]
        if any(abs(a - b) > 0.02 * max(b, 0.1) + 0.01 for a, b in zip(sorted(isz), sorted(size))):
            errors.append(f"размер {name}: импорт {isz} против rig {size}")
        if kind == "c":
            out["creatures"].setdefault(cid, {})[part] = mid
        else:
            out["yeti"][part] = mid
    ids = [v[0] for v in got.values()]
    shared = len(ids) - len(set(ids))
    print(f"частей: существа {sum(len(v) for v in out['creatures'].values())} ({len(out['creatures'])} существ), "
          f"Йети {len(out['yeti'])}; общих MeshId {shared}")
    if errors:
        print("ОШИБКИ:\n  " + "\n  ".join(errors))
        return 1
    json.dump(out, open(OUT, "w", encoding="utf-8", newline="\n"), indent=1)
    print("CHECK_OK", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
