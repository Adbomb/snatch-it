"""Скелеты и Part-версия существ босса 3 (D55, этап D) → src/shared/Config/CreatureRigs.luau и строки коллекции для
src/shared/Config/Items.luau (между метками «-- D55: коллекция босса 3 (сгенерировано…)»).

Берёт assets/models/art/Boss3Creatures.index.json (части, роли, пробные позы, поворот yaw, правила подставки D54),
<id>.rig.json (родители и точки вращения), Boss3Creatures.parts.json (блоки, scripts/blender/creature_parts.py) и
docs/CATALOG.md (названия, редкости и доход, предварительный). Оси Roblox; модель собирается в осях скелета (лицо к +Z,
низ подставки на y = 0), игра поворачивает её на 180°, чтобы лицо смотрело вперёд (−Z). Lift — низ живого существа
(без скрытой подставки), Size — его габариты в покое.
Роль части (строка D54) → ключ анимации (Shared/CreatureAnim).
Запуск: python scripts/creature_rigs_to_luau.py
"""

import json
import math
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(REPO, "assets", "models", "art")
DST = os.path.join(REPO, "src", "shared", "Config", "CreatureRigs.luau")
ITEMS = os.path.join(REPO, "src", "shared", "Config", "Items.luau")
CATALOG = os.path.join(REPO, "docs", "CATALOG.md")
BEGIN = "-- D55: коллекция босса 3 (сгенерировано scripts/creature_rigs_to_luau.py — руками не править)"
END = "-- D55: конец коллекции босса 3"

ROLES = [  # подстрока роли D54 → ключ анимации
    ("подставка", "stand"), ("нога", "leg"), ("рука или лапа", "arm"), ("лапка", "paw"), ("туловище", "body"),
    ("голова", "head"), ("глаз на стебельке", "eyestalk"), ("глаз", "eye"), ("ухо", "ear"), ("хвост", "tail"),
    ("нижний клюв", "jaw"), ("крышка-челюсть", "lid"), ("челюсть", "jaw"), ("колёса", "wheel"),
    ("стрелки часов", "hands"), ("плечо-шестерёнка", "spin"), ("парит и вращается", "float"), ("«рогатка»", "spin"),
    ("вращается", "spin"), ("крыло", "wing"), ("щупальце", "tentacle"), ("маленький жилец", "tenant"),
    ("головной убор", "hat"), ("крупная часть", "sway"), ("язычок банки", "tab"), ("язык", "tongue"),
    ("звонок", "bell"), ("брови", "brow"), ("бантик-усы", "whisker"), ("стрелки-усы", "whisker"),
    ("вылетают из пасти", "spit"), ("створка сейфа", "door"), ("штанга", "lift"),
]


# Существа «особого внимания» (D54, правила владельца для анимации): своя роль у части вместо общей по строке D54.
SPECIAL_ROLES = {
    # три головы с разным характером: злая — резкие кивки «щёлк», сонная — «клюёт носом», глупая — болтается
    "ThreeHeadedRat": {"HeadL": "head_angry", "HeadC": "head_sleepy", "HeadR": "head_silly"},
    # тележки с рамой (не отдельные колёса): покачиваются вокруг оси, а не кувыркаются; челюсть — и вниз, и «кусь»
    "MonsterTrain": {"WheelF": "bogie", "WheelB": "bogie", "Jaw": "jaw_wide"},
    # створки на петлях захлопываются навстречу друг другу; стражи переминаются и поворачиваются к игроку
    "CheeseVaultHeart": {"DoorL": "vault_door", "DoorR": "vault_door", "GuardL": "guard", "GuardR": "guard"},
    # корона подпрыгивает с запаздыванием за головой
    "ThreeTailEmperor": {"Crown": "crown"},
}

# Ось вращения части (оси модели до поворота yaw), если её не задаёт пробная поза: пропеллер глупой головы наклонён
# вместе с ней на 26° (art_rats.py: tilt вокруг Y Blender → вокруг −Z Roblox), лопасть — поперёк этой оси.
SPECIAL_AXES = {
    "ThreeHeadedRat": {"Propeller": (math.sin(math.radians(26)), math.cos(math.radians(26)), 0.0)},
}


def role_key(text):
    for needle, key in ROLES:
        if needle in (text or ""):
            return key
    return "sway"


def spin_axes(item):
    """Оси вращения колёс: у колеса без пробной позы — как у парного с позой (колёса одной оси крутятся одинаково;
    без этого второе колесо вертелось вокруг оси роли x — поперёк своей оси)."""
    axes = dict(SPECIAL_AXES.get(item["id"], {}))
    wheels = [p for p in item["parts"] if role_key(p["role"]) == "wheel"]
    posed = [p for p in wheels if p.get("demo_rot_rbx_deg") and any(p["demo_rot_rbx_deg"])]
    if posed:
        d = posed[0]["demo_rot_rbx_deg"]
        length = math.sqrt(sum(c * c for c in d))
        for p in wheels:
            if p not in posed:
                axes[p["name"]] = tuple(c / length for c in d)
    return axes


def num(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def v3(v):
    return f"Vector3.new({', '.join(num(c) for c in v)})"


def catalog():
    text = open(CATALOG, encoding="utf-8").read()
    part = text[text.index("## Босс 3"):text.index("## Боссы 4–10")]
    out = {}
    for line in part.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 6 and cells[0].isdigit():
            out[cells[3]] = {"n": int(cells[0]), "rarity": cells[1], "name": cells[2],
                             "income": float(cells[5].replace(" ", ""))}
    return out


def main():
    index = json.load(open(os.path.join(ART, "Boss3Creatures.index.json"), encoding="utf-8"))
    blocks = json.load(open(os.path.join(ART, "Boss3Creatures.parts.json"), encoding="utf-8"))
    cat = catalog()
    lines = [
        "-- Живые существа босса 3 «Крысиный король» (D55, данные D54): скелет, роли частей и Part-версия до импорта",
        "-- мешей. Сгенерировано scripts/creature_rigs_to_luau.py — руками не править. Оси Roblox, стады; модель в осях",
        "-- скелета: лицо к +Z, низ подставки на y = 0 (игра поворачивает на 180°: лицо вперёд, −Z). Parts: родитель,",
        "-- точка вращения (pivot), роль (ключ Shared/CreatureAnim), пробная поза D54 (demo — градусы XYZ в осях модели,",
        "-- shift — смещение), axis — ось вращения, если её не задаёт пробная поза (второе колесо, пропеллер), hidden —",
        "-- скрыта в игре (подставка stand_policy hide, D54), center / size — габарит меша D54 части от pivot (импорт ставит",
        "-- MeshPart в его центр), blocks — блоки Part-версии (центр от pivot, размер, цвет; резерв, если меша нет). Роли",
        "-- «особого внимания» (головы трёхголовой крысы, створки сейфа, корона императора…) — SPECIAL_ROLES генератора.",
        "-- Yaw — поворот корпуса к зрителю (D54: суставы анимировать в осях, повёрнутых на него).",
        "-- Lift — низ живого существа над низом подставки, Size — его габариты. Ни от чего не зависит.",
        "",
        "local V = Vector3.new",
        "",
        "return {",
    ]
    item_lines = [BEGIN]
    for item in index["items"]:
        item_id = item["id"]
        rig = json.load(open(os.path.join(ART, f"{item_id}.rig.json"), encoding="utf-8"))
        parts_blocks = blocks[item_id]["parts"]
        hidden = set(item.get("hide_with_stand") or [])
        if item.get("stand_policy") != "keep":
            hidden.add("Stand")
        roles = {p["name"]: p for p in item["parts"]}
        special = SPECIAL_ROLES.get(item_id, {})
        axes = spin_axes(item)
        lo, hi = [1e9] * 3, [-1e9] * 3
        colors = {}
        for name, entries in parts_blocks.items():
            piv = rig["parts"][name]["pivot"]
            for e in entries:
                for i in range(3):
                    lo[i] = min(lo[i], piv[i] + e["c"][i] - e["s"][i] / 2)
                    hi[i] = max(hi[i], piv[i] + e["c"][i] + e["s"][i] / 2)
                vol = e["s"][0] * e["s"][1] * e["s"][2]
                colors[e["col"]] = colors.get(e["col"], 0) + vol
        main_color = max(colors, key=colors.get)
        size = [hi[i] - lo[i] for i in range(3)]
        lines.append(f"\t{item_id} = {{")
        lines.append(f"\t\tSize = {v3(size)},")
        lines.append(f"\t\tCenter = {v3([(lo[0] + hi[0]) / 2, 0, (lo[2] + hi[2]) / 2])},")
        lines.append(f"\t\tLift = {num(lo[1])},")
        lines.append(f"\t\tYaw = {num(item.get('yaw_deg') or 0)},")
        lines.append(f"\t\tStand = \"{item.get('stand_policy')}\",")
        lines.append(f"\t\tAttention = {'true' if item.get('attention') else 'false'},")
        lines.append(f"\t\tOrder = {{ {', '.join(chr(34) + n + chr(34) for n in rig['order'])} }},")
        lines.append("\t\tParts = {")
        for name in rig["order"]:
            r = rig["parts"][name]
            info = roles.get(name, {})
            fields = [f"parent = {chr(34) + r['parent'] + chr(34) if r['parent'] else 'nil'}",
                      f"pivot = V({', '.join(num(c) for c in r['pivot'])})",
                      f"role = \"{special.get(name) or role_key(info.get('role'))}\""]
            if info.get("demo_rot_rbx_deg"):
                fields.append(f"demo = V({', '.join(num(c) for c in info['demo_rot_rbx_deg'])})")
            if name in axes:
                fields.append(f"axis = V({', '.join(num(c) for c in axes[name])})")
            if info.get("demo_offset_rbx") and any(abs(c) > 1e-6 for c in info["demo_offset_rbx"]):
                fields.append(f"shift = V({', '.join(num(c) for c in info['demo_offset_rbx'])})")
            if name in hidden:
                fields.append("hidden = true")
            # габарит меша D54 части от её pivot (rig.json): меш после импорта встаёт на тот же сустав
            fields.append(f"center = V({', '.join(num(c) for c in r['center'])})")
            fields.append(f"size = V({', '.join(num(c) for c in r['size'])})")
            bl = ", ".join(
                f"{{ V({', '.join(num(c) for c in e['c'])}), V({', '.join(num(c) for c in e['s'])}), \"{e['col']}\" }}"
                for e in parts_blocks.get(name, []))
            fields.append(f"blocks = {{ {bl} }}" if bl else "blocks = {}")
            lines.append(f"\t\t\t{name} = {{ {', '.join(fields)} }},")
        lines.append("\t\t},")
        lines.append("\t},")
        c = cat[item_id]
        weight = "Heavy" if max(size) > 3.2 else "Medium" if max(size) > 2.2 else "Light"
        item_lines.append(
            f"creature(\"{item_id}\", \"{c['rarity']}\", \"{c['name']}\", \"{weight}\", {num(c['income'])}, "
            f"\"{main_color}\", V({', '.join(num(v) for v in size)}))")
    lines += ["}", ""]
    with open(DST, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    item_lines.append(END)
    text = open(ITEMS, encoding="utf-8").read()
    if BEGIN in text:
        text = text[:text.index(BEGIN)] + "\n".join(item_lines) + text[text.index(END) + len(END):]
    else:
        raise SystemExit("В Items.luau нет метки начала коллекции босса 3")
    with open(ITEMS, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("CreatureRigs:", len(index["items"]))


main()
