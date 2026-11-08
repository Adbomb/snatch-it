"""Скелеты и Part-версия Ловибумов (D55) → src/shared/Config/LovibumRigs.luau.

Берёт assets/models/lovibums/parts.json (пишет scripts/blender/lovibum_models.py): части Base, Core, Claw1…4, Crystal
(точки вращения, оси раскрытия когтей, подъём кристалла), точку света, детали Part-версии (форма, размер, CFrame в
координатах модели, цвет, Neon). Оси Roblox, стады, лицо в +Z, низ на y = 0.
Запуск: python scripts/lovibum_rig_to_luau.py
"""

import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "assets", "models", "lovibums", "parts.json")
DST = os.path.join(REPO, "src", "shared", "Config", "LovibumRigs.luau")
ORDER = ("Boom", "Turbo", "Mega")


def num(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def v3(v):
    return f"Vector3.new({', '.join(num(c) for c in v)})"


def bbox(parts):
    """Габариты модели по углам всех деталей (закрытый вид)."""
    lo, hi = [1e9] * 3, [-1e9] * 3
    for p in parts:
        cf, (sx, sy, sz) = p["cf"], p["size"]
        c, r = cf[:3], cf[3:]
        for dx in (-sx / 2, sx / 2):
            for dy in (-sy / 2, sy / 2):
                for dz in (-sz / 2, sz / 2):
                    w = [c[i] + r[3 * i] * dx + r[3 * i + 1] * dy + r[3 * i + 2] * dz for i in range(3)]
                    lo = [min(lo[i], w[i]) for i in range(3)]
                    hi = [max(hi[i], w[i]) for i in range(3)]
    return lo, hi


def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    rig0 = data[ORDER[0]]["rig"]
    out = [
        "-- Ловибумы v5 «кристалл в когтях» (D55): подвижные части и запасная Part-версия.",
        "-- Сгенерировано scripts/lovibum_rig_to_luau.py из assets/models/lovibums/parts.json (scripts/blender/"
        "lovibum_models.py) —",
        "-- руками не править. Оси Roblox, стады, лицо в +Z, низ на y = 0, закрытый вид. Groups: часть → родитель, точка",
        "-- вращения (pivot, координаты модели), у когтей — ось раскрытия (axis: поворот на +OpenDeg вокруг неё — наружу),",
        "-- у кристалла — подъём при раскрытии (lift). Parts — детали Part-версии: часть, форма, размер, CFrame в",
        "-- координатах модели, цвет, Neon (кристалл и ядро — решение владельца 2026-11-08). Меши (FBX) лежат локально,",
        "-- импорт и загрузка пока запрещены — в игре Part-версия. Ни от чего не зависит.",
        "",
        "return {",
        f"\tOpenDeg = {num(rig0['open_deg'])},",
        f"\tOrder = {{ {', '.join(repr(n).replace(chr(39), chr(34)) for n in ORDER)} }},",
        "\tTypes = {",
    ]
    for name in ORDER:
        entry = data[name]
        rig, parts = entry["rig"], entry["parts"]
        lo, hi = bbox(parts)
        out.append(f"\t\t{name} = {{")
        out.append(f"\t\t\tSize = {v3([hi[i] - lo[i] for i in range(3)])},")
        out.append(f"\t\t\tCenter = {v3([(hi[i] + lo[i]) / 2 for i in range(3)])},")
        out.append(f"\t\t\tLight = {v3(rig['light'])},")
        out.append(f"\t\t\tGlow = \"{entry['glow']}\",")
        out.append(f"\t\t\tCrystalLift = {num(rig['crystal_lift'])},")
        out.append(f"\t\t\tGroupOrder = {{ {', '.join(chr(34) + g + chr(34) for g in rig['order'])} }},")
        out.append("\t\t\tGroups = {")
        for g in rig["order"]:
            p = rig["parts"][g]
            fields = [f"parent = {chr(34) + p['parent'] + chr(34) if p['parent'] else 'nil'}", f"pivot = {v3(p['pivot'])}"]
            if "axis" in p:
                fields.append(f"axis = {v3(p['axis'])}")
            fields.append("neon = true" if g in rig["neon"] else "neon = false")
            out.append(f"\t\t\t\t{g} = {{ {', '.join(fields)} }},")
        out.append("\t\t\t},")
        out.append("\t\t\tParts = {")
        for p in parts:
            cf = ", ".join(num(c) for c in p["cf"])
            out.append(
                f"\t\t\t\t{{ g = \"{p['group']}\", shape = \"{p['shape']}\", size = {v3(p['size'])}, "
                f"cf = CFrame.new({cf}), color = \"{p['color']}\", neon = {'true' if p['neon'] else 'false'} }},"
            )
        out.append("\t\t\t},")
        out.append("\t\t},")
    out += ["\t},", "}", ""]
    with open(DST, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    print("LovibumRigs:", {n: len(data[n]["parts"]) for n in ORDER})


main()
