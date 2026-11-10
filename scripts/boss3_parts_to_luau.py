"""Детали Part-версии Крысиного короля → src/shared/Config/Boss3RatKingParts.luau.

Берёт assets/models/Boss3_RatKing.parts.json (scripts/blender/boss_parts.py: фигуры утверждённой модели D54 →
детали) и пишет модуль Luau: часть скелета → список деталей { центр, размер, цвет, поворот? } в осях Roblox от точки
вращения части (лицо модели +Z), стадов; поворот — 9 чисел по строкам (как в CFrame.new(x, y, z, R00…R22)).
Запуск: python scripts/boss3_parts_to_luau.py
"""

import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "assets", "models", "Boss3_RatKing.parts.json")
DST = os.path.join(REPO, "src", "shared", "Config", "Boss3RatKingParts.luau")


def num(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def main():
    data = json.load(open(SRC, encoding="utf-8"))
    lines = [
        "-- Part-версия Крысиного короля (босс 3, D54) по утверждённой модели — пока меши и карты не загружены: детали",
        "-- каждой части скелета (Config/Boss3RatKingRig) из тех же фигур, что модель D54 (бруски, ступени",
        "-- восьмигранников, пирамид и рамок). Сгенерировано scripts/boss3_parts_to_luau.py из",
        "-- assets/models/Boss3_RatKing.parts.json (scripts/blender/boss_parts.py) — руками не править. Деталь:",
        "-- { центр, размер, цвет, поворот? } — оси Roblox от точки вращения части (лицо модели +Z), стады; поворот —",
        "-- 9 чисел по строкам, как в CFrame.new(x, y, z, R00…R22). Ни от чего не зависит.",
        "",
        "local V = Vector3.new",
        "",
        "return {",
    ]
    for name, rows in data["parts"].items():
        lines.append(f"\t{name} = {{")
        for e in rows:
            fields = [f"V({', '.join(num(c) for c in e['c'])})", f"V({', '.join(num(c) for c in e['s'])})",
                      f"\"{e['col']}\""]
            if "r" in e:
                fields.append("{ " + ", ".join(num(c) for c in e["r"]) + " }")
            lines.append("\t\t{ " + ", ".join(fields) + " },")
        lines.append("\t},")
    lines += ["}", ""]
    with open(DST, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print("Boss3RatKingParts:", data["blocks"], "деталей")


main()
