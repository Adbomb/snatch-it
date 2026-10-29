"""Собирает src/server/World/MeshModels.luau из пачек моделей Blender.

Для каждой пачки нужны assets/models/<пачка>.layout.json (пишет скрипт Blender) и
assets/models/<пачка>.meshids.json (ID мешей после импорта в Studio: {"<Пачка>": {"<Модель>_<роль>": "rbxassetid://…"}}).
У музеев из pack1_museums.py берутся ещё глубина зала (BACK), проём входа (DOOR_W, DOOR_H) и толщина стен (WALL_T).

Запуск из корня репозитория: python scripts/models_to_luau.py
"""

import json
import os
import re

PACKS = ["Pack1", "Pack1_dumbbells"]
OUT = os.path.join("src", "server", "World", "MeshModels.luau")


def num(value):
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def vec(values):
    return "Vector3.new(" + ", ".join(num(v) for v in values) + ")"


def museum_constants():
    source = open(os.path.join("scripts", "blender", "pack1_museums.py"), encoding="utf-8").read()

    def grab(pattern):
        return [float(x) for x in re.search(pattern, source, re.M).groups()]

    (back,) = grab(r"^BACK = ([\d.]+)")
    door_w, door_h = grab(r"^DOOR_W, DOOR_H = ([\d.]+), ([\d.]+)")
    (wall_t,) = grab(r"^WALL_T = ([\d.]+)")
    return {"back": back, "doorWidth": door_w, "doorHeight": door_h, "wallThickness": wall_t}


def main():
    lines = [
        "-- СГЕНЕРИРОВАНО scripts/models_to_luau.py из assets/models/*.layout.json и *.meshids.json — руками не править.",
        "-- Модели из Blender (D33, D34): детали-роли с ID меша, центром и размером в координатах модели (x вправо,",
        "-- y вверх, вход или лицо — в -z, начало — центр у пола), цвет (hex или Accent / AccentDark / DecorAccent —",
        "-- цвет участка), материал, декор чётных уровней. У музеев — размеры зала для стен и вывески, у гантелей —",
        "-- лампы (PointLight без теней). Собирает их World/MeshBuilder. Ни от чего не зависит.",
        "",
        "export type Part = {",
        "\trole: string,",
        "\tmesh: string,",
        "\tcenter: Vector3,",
        "\tsize: Vector3,",
        "\tcolor: string,",
        "\tmaterial: string,",
        "\tdecor: boolean,",
        "}",
        "export type Light = { position: Vector3, color: string, range: number, brightness: number }",
        "export type MeshModel = {",
        "\ttitle: string?,",
        "\ttriangles: number,",
        "\tparts: { Part },",
        "\tlights: { Light }?,",
        "\twallHeight: number?,",
        "\tsignY: number?,",
        "\tlampHeight: number?,",
        "\tfacadeZ: number?,",
        "\thalfWidth: number?,",
        "\tback: number?,",
        "\tdoorWidth: number?,",
        "\tdoorHeight: number?,",
        "\twallThickness: number?,",
        "}",
        "",
        "return {",
    ]
    museum_extra = museum_constants()
    for pack in PACKS:
        layout = json.load(open(os.path.join("assets", "models", pack + ".layout.json"), encoding="utf-8"))
        ids = json.load(open(os.path.join("assets", "models", pack + ".meshids.json"), encoding="utf-8"))[pack]
        models = layout["museums"] if "museums" in layout else layout
        for name, data in models.items():
            lines.append(f"\t{name} = {{")
            if "title" in data:
                lines.append(f'\t\ttitle = "{data["title"]}",')
            lines.append(f"\t\ttriangles = {data['triangles']},")
            if name.startswith("Museum"):
                for key in ("wallHeight", "signY", "lampHeight", "facadeZ", "halfWidth"):
                    lines.append(f"\t\t{key} = {num(data[key])},")
                for key, value in museum_extra.items():
                    lines.append(f"\t\t{key} = {num(value)},")
            lines.append("\t\tparts = {")
            for role, part in data["roles"].items():
                mesh = ids[f"{name}_{role}"]
                decor = "true" if part["decor"] else "false"
                lines.append(f'\t\t\t{{ role = "{role}", mesh = "{mesh}",')
                lines.append(f'\t\t\t\tcenter = {vec(part["center"])}, size = {vec(part["size"])},')
                lines.append(f'\t\t\t\tcolor = "{part["color"]}", material = "{part["material"]}", decor = {decor} }},')
            lines.append("\t\t},")
            if data.get("lights"):
                lines.append("\t\tlights = {")
                for light in data["lights"]:
                    lines.append(
                        f'\t\t\t{{ position = {vec(light["position"])}, color = "{light["color"]}", '
                        f'range = {num(light["range"])}, brightness = {num(light["brightness"])} }},'
                    )
                lines.append("\t\t},")
            lines.append("\t},")
    lines.append("}")
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("written", OUT)


if __name__ == "__main__":
    main()
