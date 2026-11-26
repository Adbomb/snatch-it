"""Коллекция босса 7 «Копилка-громила» (Банк) — 30 существ по каталогу docs/BOSS7_CATALOG.md (утверждён владельцем
2026-11-26 с заменами, D73), шаг 2 D64 (производство). Стиль D39 v2 и правила анатомии D64: 3–5 признаков вида,
лицо с эмоцией, голова ≈ 1/3 тела, ноги под центром масс, суставы внахлёст, ≤ 3 000 треугольников без подставки;
подвижные части с точками вращения (D54, D55), корень — подставка Stand цвета редкости (D71, в игре скрыта); запекание ×4,
карты Common 512², остальные 1024², без нормалей; FBX из частей и скелет rig.json — общий цикл creature_kit.run.
Существа — в пакете scripts/blender/bank/ (common, rare, epic, legendary; набор — bank_kit.py; 10 утверждённых эскизов
концепта — из boss7/creatures.py). Без людей, текста, логотипов, купюр, оружия, бытовых вещей и мемных персонажей.

Пишет assets/models/art/boss7/<id>.{fbx,rig.json,blend}, assets/textures/art/boss7/<id>_color.png; кадры —
в <кадры>/<id>_*.png и report_*.json.
Запуск: blender --background --factory-startup --python scripts/blender/art_bank.py -- <репо> [кадры] [quick] [id…]
кадры по умолчанию — assets/concepts/bosses_5_10/boss7_prod/creatures (вне git); quick — без запекания и экспорта
(до утверждения листа «аудит анатомии» карты не пекутся).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "bank"))
from creature_kit import run  # noqa: E402
import common  # noqa: E402
import rare  # noqa: E402
import epic  # noqa: E402
import legendary  # noqa: E402

ITEMS = common.ITEMS + rare.ITEMS + epic.ITEMS + legendary.ITEMS


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    repo = os.path.abspath(argv[0])
    rest = argv[1:]
    shots = os.path.join(repo, "assets", "concepts", "bosses_5_10", "boss7_prod", "creatures")
    if rest and (os.sep in rest[0] or "/" in rest[0]):
        shots = os.path.abspath(rest.pop(0))
    quick = "quick" in rest
    only = [x for x in rest if x != "quick"]
    items = [x for x in ITEMS if not only or x[0] in only]
    name = "report.json" if not only else "report_" + "+".join(only)[:120] + ".json"
    if quick:
        models = tex = os.path.join(shots, "_quick")
    else:
        models = os.path.join(repo, "assets", "models", "art", "boss7")
        tex = os.path.join(repo, "assets", "textures", "art", "boss7")
    for d in (shots, models, tex):
        os.makedirs(d, exist_ok=True)
    run(items, repo, shots, models, tex, quick=quick, report_name=name)


if __name__ == "__main__":
    main()
