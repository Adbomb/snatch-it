"""Коллекция босса 6 «Королева-мухоловка» (Джунгли) — 30 существ по каталогу docs/BOSS6_CATALOG.md (утверждён
владельцем 2026-11-25 с правками), шаг 2 D64 (производство). Стиль D39 v2 и правила анатомии D64: 3–5 признаков вида,
лицо с эмоцией, голова ≈ 1/3 тела, ноги под центром масс, суставы внахлёст, ≤ 3 000 треугольников без подставки;
подвижные части с точками вращения (D54, D55), корень — подставка Stand цвета редкости (D71, в игре скрыта); запекание ×4,
карты Common 512², остальные 1024²; FBX из частей и скелет rig.json в осях Roblox — общий цикл creature_kit.run.
Существа — в пакете scripts/blender/jungle/ (common, rare, epic, legendary; набор — jungle_kit.py).
Без людей, текста, логотипов, оружия, бытовых вещей и мемных или чужих персонажей; без «зелёного на зелёном».

Пишет assets/models/art/boss6/<id>.{fbx,rig.json,blend}, assets/textures/art/boss6/<id>_{color,normal}.png; кадры —
в <кадры>/<id>_*.png и report_*.json.
Запуск: blender --background --factory-startup --python scripts/blender/art_jungle.py -- <репо> [кадры] [quick] [id…]
кадры по умолчанию — assets/concepts/bosses_5_10/boss6_prod/creatures (вне git); quick — без запекания и экспорта
(до утверждения листа «аудит анатомии» карты не пекутся). JUNGLE_OUT — сборка вне assets (пробы).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "jungle"))
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
    shots = os.path.join(repo, "assets", "concepts", "bosses_5_10", "boss6_prod", "creatures")
    if rest and (os.sep in rest[0] or "/" in rest[0]):
        shots = os.path.abspath(rest.pop(0))
    quick = "quick" in rest
    only = [x for x in rest if x != "quick"]
    items = [x for x in ITEMS if not only or x[0] in only]
    name = "report.json" if not only else "report_" + "+".join(only)[:120] + ".json"
    out = os.environ.get("JUNGLE_OUT")
    if quick:
        models = tex = os.path.join(shots, "_quick")
    else:
        models = os.path.join(out, "models") if out else os.path.join(repo, "assets", "models", "art", "boss6")
        tex = os.path.join(out, "textures") if out else os.path.join(repo, "assets", "textures", "art", "boss6")
    for d in (shots, models, tex):
        os.makedirs(d, exist_ok=True)
    run(items, repo, shots, models, tex, quick=quick, report_name=name)


if __name__ == "__main__":
    main()
