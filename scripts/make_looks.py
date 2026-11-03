"""Шаблоны SurfaceAppearance для Rojo (D39, D40): src/server/Looks/<имя>.model.json.

Свойства карт SurfaceAppearance (ColorMap, NormalMap, RoughnessMap) игровой скрипт менять не может (нужны права
плагина), поэтому шаблоны создаёт Rojo, а игра только клонирует их на MeshPart. Источник ID — Config/ItemModels
(предметы) и Config/BossModels (карты частей каждого босса: Boss<N>_<группа>). Запуск после изменения карт:
python scripts/make_looks.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "src", "shared", "Config")
OUT = os.path.join(ROOT, "src", "server", "Looks")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    items = open(os.path.join(CONFIG, "ItemModels.luau"), encoding="utf-8").read()
    bosses = open(os.path.join(CONFIG, "BossModels.luau"), encoding="utf-8").read()
    rough = re.search(r'local ROUGHNESS = "(rbxassetid://\d+)"', items).group(1)
    looks = {}
    for name, color, normal in re.findall(r"^\t(\w+) = model\((\d+), (\d+),", items, re.M):
        looks[name] = (f"rbxassetid://{color}", f"rbxassetid://{normal}")
    for boss in re.finditer(r"\[(\d+)\] = \{.*?maps = \{(.*?)\n\t\t\},", bosses, re.S):
        for group, color, normal in re.findall(
                r'(\w+) = \{ color = "(rbxassetid://\d+)", normal = "(rbxassetid://\d+)" \}', boss.group(2)):
            looks[f"Boss{boss.group(1)}_{group}"] = (color, normal)
    os.makedirs(OUT, exist_ok=True)
    for name, (color, normal) in looks.items():
        data = {"ClassName": "SurfaceAppearance",
                "Properties": {"ColorMap": color, "NormalMap": normal, "RoughnessMap": rough}}
        with open(os.path.join(OUT, f"{name}.model.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, indent="\t")
            f.write("\n")
    print(f"шаблонов: {len(looks)} → {OUT}")


if __name__ == "__main__":
    main()
