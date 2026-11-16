"""Шаблоны SurfaceAppearance для Rojo (D39, D40): src/server/Looks/<имя>.model.json.

Свойства карт SurfaceAppearance (ColorMap, NormalMap, RoughnessMap) игровой скрипт менять не может (нужны права
плагина), поэтому шаблоны создаёт Rojo, а игра только клонирует их на MeshPart. Источник ID — Config/ItemModels
(предметы) и Config/BossModels (карты частей каждого босса: Boss<N>_<группа>). У карты босса могут быть ещё metal
(MetalnessMap), rough (своя RoughnessMap вместо общей) и glow (маска свечения EmissiveMaskContent с силой
GLOW_STRENGTH) — у Короля-дракона, версия 3.1 (этап C.2). Запуск после изменения карт:
python scripts/make_looks.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "src", "shared", "Config")
OUT = os.path.join(ROOT, "src", "server", "Looks")
GLOW_STRENGTH = 3  # сила свечения по маске glow (кристаллы дракона; подобрано на снимках Studio, этап C.1)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    items = open(os.path.join(CONFIG, "ItemModels.luau"), encoding="utf-8").read()
    bosses = open(os.path.join(CONFIG, "BossModels.luau"), encoding="utf-8").read()
    rough = re.search(r'local ROUGHNESS = "(rbxassetid://\d+)"', items).group(1)
    looks = {}
    for name, color, normal in re.findall(r"^\t(\w+) = model\((\d+), (\d+),", items, re.M):
        looks[name] = {"color": f"rbxassetid://{color}", "normal": f"rbxassetid://{normal}"}
    # запись босса — от «[N] = {» до следующей; пустые maps = {} (у босса нет карт) пропускаются
    for boss in re.finditer(r"\n\t\[(\d+)\] = \{(.*?)(?=\n\t\[\d+\] = \{|\n\}\))", bosses, re.S):
        maps = re.search(r"maps = \{(.*?)\n\t\t\},", boss.group(2), re.S)
        if not maps:
            continue
        # группа = { color = "…", normal = "…"[, metal = "…", rough = "…", glow = "…"] } — в одну строку или в несколько
        for group, body in re.findall(r"(\w+) = \{([^{}]*)\}", maps.group(1)):
            fields = dict(re.findall(r'(\w+) = "(rbxassetid://\d+)"', body))
            if "color" in fields and "normal" in fields:
                looks[f"Boss{boss.group(1)}_{group}"] = fields
    os.makedirs(OUT, exist_ok=True)
    for name, f in looks.items():
        props = {"ColorMap": f["color"], "NormalMap": f["normal"]}
        if "metal" in f:
            props["MetalnessMap"] = f["metal"]
        props["RoughnessMap"] = f.get("rough", rough)
        if "glow" in f:
            props["EmissiveMaskContent"] = f["glow"]
            props["EmissiveStrength"] = GLOW_STRENGTH
        data = {"ClassName": "SurfaceAppearance", "Properties": props}
        with open(os.path.join(OUT, f"{name}.model.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, indent="\t")
            fh.write("\n")
    print(f"шаблонов: {len(looks)} → {OUT}")


if __name__ == "__main__":
    main()
