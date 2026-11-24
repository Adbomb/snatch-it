"""Индекс существ босса 5 «Йети-коллекционер» (D64): assets/models/art/boss5/Boss5Creatures.index.json из скелетов
<id>.rig.json (art_glacier.py), каталога docs/BOSS5_CATALOG.md (названия, редкости, доходы по ступени 3.2 — D64 вариант
А) и весов D58 (assets/concepts/boss5/sheets/weights.json — наибольший габарит без подставки, boss5_sheets.py; если
файла нет — тот же расчёт по rig.json). Формат — как у Boss4Creatures.index.json (его читают
scripts/blender/creature_parts.py, scripts/creature_rigs_to_luau.py и Lune check_creatures). Роли частей — слова D54
(build_boss4_index.ROLES) плюс имена частей босса 5; transparent — прозрачные части (желе, купол медузы).
Запуск: python scripts/build_boss5_index.py (из корня репозитория).
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_boss4_index as B4  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "assets", "models", "art", "boss5")
TEX = "assets/textures/art/boss5"
WEIGHTS = os.path.join(ROOT, "assets", "concepts", "boss5", "sheets", "weights.json")
CATALOG = os.path.join(ROOT, "docs", "BOSS5_CATALOG.md")
TRANSPARENCY = 0.45  # желе и купол: внутренности видны (как лёд глыбы Йети)

ROLES5 = [  # раньше общих: имена частей босса 5 → слова роли D54
    (r"^(Floe|Water|Branch)$", B4.STATIC),
    (r"^Ball$", "туловище: покачивание, подпрыгивание, наклоны"),  # нижний шар снежного червя — часть тела
    (r"^(Bell|Folds|Front|Rear|Bottom|Middle|OwlLow|OwlMid|OwlTop|Iceberg|Quills)$",
     "туловище: покачивание, подпрыгивание, наклоны"),
    (r"^(HeadL|HeadR|HeadMid|Face|Nose)$", "голова: повороты, кивки"),
    (r"^(Eye|Eyes)$", "глаз: поворот (взгляд), моргание — масштаб по высоте"),
    (r"^Eye[LR]$", "глаз на стебельке: качается"),
    (r"^(Legs[ABC]|Legs[LR]|Paw[FB][LR])$", "нога: шаг"),
    (r"^(Braid[LR]|Trunk)$", "хвост: виляет"),
    (r"^(Flipper[LR]|Fin[LR]?)$", "крыло: взмах"),
    (r"^(ClawBig|ClawSmall)$", "рука или лапа: машет"),
    (r"^(Pack|Loupe|Horn|Lighthouse|Antlers)$", "головной убор или деталь: подпрыгивает, качается"),
    (r"^(Bird[12]|Fish)$", "маленький жилец: выглядывает, двигается"),
]


# Части с ролью не по имени (существо, часть): ходули кита качаются и стоя — иначе в покое двигаются 2 части из 4.
OVERRIDE = {("StiltWhale", "LegL"): "крупная часть: покачивание на ходулях",
            ("StiltWhale", "LegR"): "крупная часть: покачивание на ходулях"}


def role(name, item_id=None):
    if (item_id, name) in OVERRIDE:
        return OVERRIDE[(item_id, name)]
    for pat, text in ROLES5:
        if re.search(pat, name):
            return text
    return B4.role(name)


def catalog():
    out = {}
    for line in open(CATALOG, encoding="utf-8"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 8 and cells[0].isdigit():
            out[cells[4]] = {"n": int(cells[0]), "rarity": cells[1], "name": cells[3], "description": cells[6],
                             "income": float(cells[7].replace(" ", "").replace(" ", ""))}
    assert len(out) == 30, f"в каталоге босса 5 {len(out)} строк вместо 30"
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cat = catalog()
    weights = json.load(open(WEIGHTS, encoding="utf-8")) if os.path.exists(WEIGHTS) else {}
    items = []
    for item_id, meta in sorted(cat.items(), key=lambda kv: kv[1]["n"]):
        rig = json.load(open(os.path.join(ART, f"{item_id}.rig.json"), encoding="utf-8"))
        lo, hi = [1e9] * 3, [-1e9] * 3
        parts = []
        for name in rig["order"]:
            d = rig["parts"][name]
            if name != "Stand":
                for i in range(3):
                    lo[i] = min(lo[i], d["pivot"][i] + d["center"][i] - d["size"][i] / 2)
                    hi[i] = max(hi[i], d["pivot"][i] + d["center"][i] + d["size"][i] / 2)
            demo = rig.get("demo_pose", {}).get(name)
            text = role(name, item_id)
            entry = {"name": name, "parent": d["parent"], "pivot": d["pivot"], "role": text,
                     "demo_rot_rbx_deg": B4.to_rbx(demo["rot_xyz_blender_deg"]) if demo else None,
                     "demo_offset_rbx": B4.to_rbx(demo["offset_blender"]) if demo else None}
            if name in rig.get("transparent", []):
                entry["transparency"] = TRANSPARENCY
            parts.append(entry)
        size = max(hi[i] - lo[i] for i in range(3))
        weight = (weights.get(item_id) or {}).get("class") or ("Heavy" if size > 3.2 else "Medium" if size > 2.2
                                                                else "Light")
        items.append({"id": item_id, **meta, "weight": weight, "fbx": f"assets/models/art/boss5/{item_id}.fbx",
                      "rig": f"assets/models/art/boss5/{item_id}.rig.json",
                      "maps": [f"{TEX}/{item_id}_color.png", f"{TEX}/{item_id}_normal.png"],
                      "footprint": [round(hi[0] - lo[0], 2), round(hi[2] - lo[2], 2)], "height": round(hi[1] - lo[1], 2),
                      "yaw_deg": 0, "hide_with_stand": [], "keep_stand": None, "stand_policy": "hide",
                      "attention": False, "attention_note": None, "parts": parts})
    out = {"version": "D64-2026-11-24", "accepted": "каталог (D64) утверждён владельцем 2026-11-24; доходы — ступень 3.2 "
                                                   "(D64, вариант А); модели и карты приняты, загружены 2026-11-24",
           "rules": ["Stand у всех 30 — декоративная подставка, в игре прячется (stand_policy hide)",
                     "вес — наибольший габарит без подставки (D58)",
                     "прозрачные части (transparency) — желе и купол: внутренности видны"],
           "axes": "Roblox: x вправо, y вверх, z к зрителю − (лицо смотрит в −z); стады", "root": "Stand",
           "roughness_map": "assets/textures/art/art_roughness.png", "items": items}
    path = os.path.join(ART, "Boss5Creatures.index.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    roles = {}
    for it in items:
        for p in it["parts"]:
            roles.setdefault(p["role"], []).append(f"{it['id']}.{p['name']}")
    sway = roles.get("крупная часть: покачивание, парение", [])
    print("INDEX_OK", len(items), path, "| без своей роли:", sway)


if __name__ == "__main__":
    main()
