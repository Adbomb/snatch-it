"""Индекс существ босса 3 для D55: assets/models/art/Boss3Creatures.index.json из скелетов <id>.rig.json и каталога.

Для каждого из 30 предметов: название и редкость (docs/CATALOG.md), габарит и высота (из скелета, оси Roblox, стады),
части с родителем, точкой вращения и ролью, подсказки движения (пробная поза в осях Roblox), поворот модели к
зрителю (yaw — оси шарниров повёрнуты на него), что прятать вместе с подставкой и где подставку лучше оставить.
Запуск: python scripts/build_creature_index.py (из корня репозитория).
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "assets", "models", "art")

# Поворот модели вокруг вертикали (градусы, по часовой при взгляде сверху в осях Roblox): у этих предметов шарниры
# корпуса (челюсть, колёса, крышка) повёрнуты на этот угол относительно осей модели.
YAW = {"SubwaySnail": 28, "SneakerTenant": 20, "RoyalRatTrain": 24, "MonsterTrain": 26}
# Части-декор подставки: прятать вместе со Stand.
HIDE_WITH_STAND = {"RunawayTicket": ["Grabber"]}
# Подставка — часть образа: у живого существа лучше оставить (или заменить своим декором).
KEEP_STAND = {
    "RatThrone": "трон — сиденье короля: без него король висит в воздухе",
    "SubwayOctopus": "люк в подставке — осьминог вылезает из него",
    "ThreeTailEmperor": "статуэтка стоит на золотой горе (так в описании владельца)",
}
ATTENTION = {"MonsterTrain", "CheeseDragon", "ThreeHeadedRat", "CheeseVaultHeart", "ThreeTailEmperor"}

ROLES = [
    (r"^Stand$", "подставка: корень, неподвижна"),
    (r"^Body$", "туловище: покачивание, подпрыгивание, наклоны"),
    (r"^Head[LCR]?$", "голова: повороты, кивки"),
    (r"^Eye[LRS]$", "глаз: поворот (взгляд), моргание — масштаб по высоте"),
    (r"^Jaw$", "челюсть: открывается поворотом вокруг шарнира"),
    (r"^Lid$", "крышка-челюсть: откидывается назад"),
    (r"^Beak$", "нижний клюв: открывается"),
    (r"^Tongue$", "язык: болтается"),
    (r"^Arm[LR]$", "рука или лапа: машет"),
    (r"^(Leg|Foot)", "нога: шаг"),
    (r"^Tail\d?$", "хвост: виляет"),
    (r"^Ear[LR]$", "ухо: шевелится"),
    (r"^Wing[LR]$", "крыло: взмах"),
    (r"^Wheel", "колёса с осью: вращение"),
    (r"^Tentacle", "щупальце со своей ношей: изгиб, взмах"),
    (r"^Gear[LR]$", "плечо-шестерёнка: вращение"),
    (r"^Hands$", "стрелки часов: вращение"),
    (r"^Door[LR]$", "створка сейфа: закрывается и открывается вокруг петли"),
    (r"^(Propeller|Lamp)$", "вращается"),
    (r"^(Crown|Cap|Hat|HatTip|Plume|Visor|Dome)$", "головной убор или деталь: подпрыгивает, качается"),
    (r"^(Bubbles|Cubes)$", "вылетают из пасти: смещение вперёд-вверх"),
    (r"^Crystal$", "парит и вращается"),
    (r"^Grabber$", "«рогатка» турникета-ловца: вращается (декор подставки)"),
    (r"^Barbell$", "штанга: вверх-вниз вместе с руками"),
    (r"^(Pilot|Rat\d?|Mouse|Guard[LR])$", "маленький жилец: выглядывает, двигается"),
    (r"^Paw[LR]$", "лапка: шевелится"),
    (r"^Stalk[LR]$", "глаз на стебельке: качается"),
    (r"^(Bell[LR]|Hammer)$", "звонок или молоточек: дрожит, бьёт"),
    (r"^Mustache$", "стрелки-усы: подкручиваются"),
    (r"^Brows$", "брови: хмурятся (смещение вниз)"),
    (r"^Tab$", "язычок банки на макушке: качается"),
    (r"^Laces$", "бантик-усы: шевелится"),
    (r"^(Pizza|Board|Cart|Shell|Ufo|Beam|Ruby|Cape)$", "крупная часть: покачивание, парение"),
]


def role(name):
    for pat, text in ROLES:
        if re.search(pat, name):
            return text
    return "подвижная часть"


def catalog():
    text = open(os.path.join(ROOT, "docs", "CATALOG.md"), encoding="utf-8").read()
    sec = text[text.index("## Босс 3"): text.index("## Боссы 4–10")]
    out = {}
    for m in re.finditer(r"^\| (\d+) \| (Common|Rare|Epic) \| ([^|]+) \| (\w+) \| ([^|]+) \|", sec, re.M):
        out[m.group(4)] = {"n": int(m.group(1)), "rarity": m.group(2), "name": m.group(3).strip(),
                           "description": m.group(5).strip()}
    return out


def to_rbx_rot(rot):
    bx, by, bz = rot
    return [bx, bz, -by]  # Blender X → Roblox X, Blender Z → Roblox Y, Blender Y → −Roblox Z


def main():
    cat = catalog()
    items = []
    for item_id, meta in sorted(cat.items(), key=lambda kv: kv[1]["n"]):
        rig = json.load(open(os.path.join(ART, f"{item_id}.rig.json"), encoding="utf-8"))
        lo, hi = [1e9] * 3, [-1e9] * 3
        parts = []
        for name in rig["order"]:
            d = rig["parts"][name]
            for i in range(3):
                lo[i] = min(lo[i], d["pivot"][i] + d["center"][i] - d["size"][i] / 2)
                hi[i] = max(hi[i], d["pivot"][i] + d["center"][i] + d["size"][i] / 2)
            demo = rig["demo_pose"].get(name)
            parts.append({"name": name, "parent": d["parent"], "pivot": d["pivot"], "role": role(name),
                          "demo_rot_rbx_deg": to_rbx_rot(demo["rot_xyz_blender_deg"]) if demo else None,
                          "demo_offset_rbx": ([demo["offset_blender"][0], demo["offset_blender"][2],
                                               -demo["offset_blender"][1]] if demo else None)})
        items.append({"id": item_id, **meta, "fbx": f"assets/models/art/{item_id}.fbx",
                      "rig": f"assets/models/art/{item_id}.rig.json",
                      "maps": [f"assets/textures/art/{item_id}_color.png", f"assets/textures/art/{item_id}_normal.png"],
                      "footprint": [round(hi[0] - lo[0], 2), round(hi[2] - lo[2], 2)], "height": round(hi[1] - lo[1], 2),
                      "yaw_deg": YAW.get(item_id, 0), "hide_with_stand": HIDE_WITH_STAND.get(item_id, []),
                      "keep_stand": KEEP_STAND.get(item_id), "attention": item_id in ATTENTION, "parts": parts})
    out = {"version": "D54-final-2026-11-08", "axes": "Roblox: x вправо, y вверх, z к зрителю − (лицо смотрит в −z); стады",
           "root": "Stand", "roughness_map": "assets/textures/art/art_roughness.png", "items": items}
    path = os.path.join(ART, "Boss3Creatures.index.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("INDEX_OK", len(items), path)


if __name__ == "__main__":
    main()
