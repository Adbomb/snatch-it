"""Индекс существ босса 4 «Сфинкс-лежебока» (D57, D58): assets/models/art/boss4/Boss4Creatures.index.json из скелетов
<id>.rig.json и каталога (docs/CATALOG.md, раздел «Босс 4»). Формат — как у Boss3Creatures.index.json (его читают
scripts/blender/creature_parts.py, scripts/creature_rigs_to_luau.py и Lune check_creatures).

Для каждого из 30: название, редкость, доход и вес (D57, D58), файлы, габарит, части с родителем, точкой вращения и
ролью (текст роли — те же слова, что у босса 3: по ним генератор выбирает ключ анимации Shared/CreatureAnim), пробная
поза в осях Roblox, ось вращения у вращающихся частей, правило подставки (D58: прячется у всех; детали композиции №20,
№21 — свои части). Модели из art_oasis.py — корпус не повёрнут (yaw 0).
Запуск: python scripts/build_boss4_index.py (из корня репозитория).
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "assets", "models", "art", "boss4")
TEX = "assets/textures/art/boss4"
FILES = {"FennecRiddler": "FennecRiddler_v2"}  # id в игре → имя файлов (№20 — утверждённая v2)

# Роль по имени части (порядок важен: первое совпадение). Слова — из ролей D54 (ключи — creature_rigs_to_luau.ROLES).
STATIC = "неподвижная часть композиции (как подставка, без движения)"
ROLES = [
    (r"^Stand$", "подставка: корень, неподвижна"),
    (r"^(Mound|Bowl|Branch|Dune|Puddle|Spring|Coconut|Haze|Dot)$", STATIC),
    (r"^(Body|Whale|Trunk|Base|Mid|Top|TierA|TierB|TierC|TierLow|TierHigh)$", "туловище: покачивание, подпрыгивание, наклоны"),
    (r"^(Head|Neck)$", "голова: повороты, кивки"),
    (r"^Eye[LRB]?$", "глаз: поворот (взгляд), моргание — масштаб по высоте"),
    (r"^(Ear[LR]|Antenna[LR])$", "ухо: шевелится"),
    (r"^Jaw$", "челюсть: открывается поворотом вокруг шарнира"),
    (r"^Tongue$", "язык: болтается"),
    (r"^(Arm[LR]|Arm[ABC]|BaseArm[LR]|MidArm|TopArm|Claw[LR])$", "рука или лапа: машет"),
    (r"^Legs?[FB]?[LR]?$|^Leg[FB][LR]$|^Legs[LRFB]$", "нога: шаг"),
    (r"^(Tail|TailTip|Fan)$", "хвост: виляет"),
    (r"^(Wing[LR]|Fan[LR]|Flipper|Fin)$", "крыло: взмах"),
    (r"^(Blades[LR]|Drill)$", "вращается"),
    (r"^Piece$", "парит и вращается"),
    (r"^(Crown|Frill|Flower|Cork|Hood)$", "головной убор или деталь: подпрыгивает, качается"),
    (r"^(Fish[AB]|Owl[AB])$", "маленький жилец: выглядывает, двигается"),
    (r"^Bubbles$", "вылетают из пасти: смещение вперёд-вверх"),
    (r"^Spout$", "фонтан: вверх-вниз, как штанга"),
]
SPIN_LONG = {"Drill"}  # бур крутится вдоль своей длины; лопасти вентилятора — поперёк плоской стороны
# точные оси из построения (art_oasis.fan_vulture: нормаль вентилятора n = (±0.45, −1, 0.1) в осях Blender →
# Roblox (±0.45, 0.1, 1) / |n|)
EXACT_AXES = {"FanVulture": {"BladesL": [-0.409, 0.091, 0.908], "BladesR": [0.409, 0.091, 0.908]}}
ATTENTION = {
    "TornadoKing": "вращение корпуса и колец — позже (указание владельца 2026-11-13); пока покачивание",
    "FanVulture": "лопасти вентиляторов вращаются вокруг своей оси",
}


def role(name):
    for pat, text in ROLES:
        if re.search(pat, name):
            return text
    return "крупная часть: покачивание, парение"


def catalog():
    text = open(os.path.join(ROOT, "docs", "CATALOG.md"), encoding="utf-8").read()
    sec = text[text.index("## Босс 4"): text.index("## Боссы 5–10")]
    out = {}
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 7 and cells[0].isdigit():
            out[cells[3]] = {"n": int(cells[0]), "rarity": cells[1], "name": cells[2], "description": cells[4],
                             "income": float(cells[5].replace(" ", "")), "weight": cells[6]}
    assert len(out) == 30, f"в каталоге босса 4 {len(out)} строк вместо 30"
    return out


def to_rbx(v):
    bx, by, bz = v
    return [bx, bz, -by]  # Blender X → Roblox X, Blender Z → Roblox Y, Blender Y → −Roblox Z


def spin_axis(name, size):
    """Ось вращения по габариту части: самая длинная сторона (бур) или самая тонкая (плоский винт)."""
    pick = max if name in SPIN_LONG else min
    k = size.index(pick(size))
    return [1.0 if i == k else 0.0 for i in range(3)]


def main():
    cat = catalog()
    items = []
    for item_id, meta in sorted(cat.items(), key=lambda kv: kv[1]["n"]):
        f = FILES.get(item_id, item_id)
        rig = json.load(open(os.path.join(ART, f"{f}.rig.json"), encoding="utf-8"))
        lo, hi = [1e9] * 3, [-1e9] * 3
        parts = []
        for name in rig["order"]:
            d = rig["parts"][name]
            for i in range(3):
                lo[i] = min(lo[i], d["pivot"][i] + d["center"][i] - d["size"][i] / 2)
                hi[i] = max(hi[i], d["pivot"][i] + d["center"][i] + d["size"][i] / 2)
            demo = rig.get("demo_pose", {}).get(name)
            text = role(name)
            entry = {"name": name, "parent": d["parent"], "pivot": d["pivot"], "role": text,
                     "demo_rot_rbx_deg": to_rbx(demo["rot_xyz_blender_deg"]) if demo else None,
                     "demo_offset_rbx": to_rbx(demo["offset_blender"]) if demo else None}
            if text == "вращается":
                entry["axis"] = EXACT_AXES.get(item_id, {}).get(name) or spin_axis(name, d["size"])
            parts.append(entry)
        items.append({"id": item_id, **meta, "fbx": f"assets/models/art/boss4/{f}.fbx",
                      "rig": f"assets/models/art/boss4/{f}.rig.json",
                      "maps": [f"{TEX}/{f}_color.png", f"{TEX}/{f}_normal.png"],
                      "footprint": [round(hi[0] - lo[0], 2), round(hi[2] - lo[2], 2)], "height": round(hi[1] - lo[1], 2),
                      "yaw_deg": 0, "hide_with_stand": [], "keep_stand": None, "stand_policy": "hide",
                      "attention": item_id in ATTENTION, "attention_note": ATTENTION.get(item_id), "parts": parts})
    out = {"version": "D57-D58-2026-11-13", "accepted": "каталог, доходы (D57), веса и подставки (D58) утверждены владельцем 2026-11-13",
           "rules": ["Stand у всех 30 — декоративная подставка, в игре прячется (stand_policy hide)",
                     "детали композиции, которые остаются: №20 — Dot (точка «?»), №21 — Haze (марево с холмиком); "
                     "у №27 песчаный холмик в Stand и прячется с ней",
                     "вес — из каталога (D58), не пересчитывается",
                     "подвижные части анимируются без разрывов: вращение вокруг pivot, Motor6D по rig.json"],
           "axes": "Roblox: x вправо, y вверх, z к зрителю − (лицо смотрит в −z); стады", "root": "Stand",
           "roughness_map": "assets/textures/art/art_roughness.png", "items": items}
    path = os.path.join(ART, "Boss4Creatures.index.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("INDEX_OK", len(items), path)


if __name__ == "__main__":
    main()
