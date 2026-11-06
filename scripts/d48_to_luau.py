"""D48-C, фаза 3 — раскладка музея для игры: scripts/blender/d48c_layout.py (числа и места) и
assets/concepts/d48/c2/mesh_placement.json (какой модуль Blender где стоит на уровнях 1–10) →
src/shared/Config/MuseumLayout.luau. Один источник правды для Blender-моделей, листов и игры.

Запуск из корня репозитория: python scripts/d48_to_luau.py
Проверка без записи (код 1, если файл устарел): python scripts/d48_to_luau.py --check
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "blender"))
import d48c_layout as L  # noqa: E402

PLACEMENT = os.path.join(ROOT, "assets", "concepts", "d48", "c2", "mesh_placement.json")
OUT = os.path.join(ROOT, "src", "shared", "Config", "MuseumLayout.luau")


def num(value):
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def vec(values):
    return "Vector3.new(" + ", ".join(num(v) for v in values) + ")"


def nums(values):
    return "{ " + ", ".join(num(v) for v in values) + " }"


def rects(items):
    return "{\n" + "".join(f"\t\t{nums(r)},\n" for r in items) + "\t}"


def modules():
    """Модули по уровням: одинаковые (модель, место, поворот) на соседних уровнях — одна запись from…to."""
    data = json.load(open(PLACEMENT, encoding="utf-8"))["levels"]
    seen = {}
    order = []
    for level in range(1, 11):
        for item in data[str(level)]["items"]:
            key = (item["model"], tuple(round(v, 3) for v in item["position"]), item["yaw"])
            if key not in seen:
                seen[key] = []
                order.append(key)
            seen[key].append(level)
    out = []
    for key in order:
        levels = seen[key]
        assert levels == list(range(levels[0], levels[-1] + 1)), key  # уровни подряд
        out.append((key, levels[0], levels[-1]))
    return out


def build():
    lay = L.layout()
    hall, gal, vault, stair, pav = lay["hall"], lay["gallery"], lay["vault"], lay["stair"], lay["pavilion"]
    zones_low, zones_high = L.defense_zones(1), L.defense_zones(L.GALLERY_LEVEL)
    gallery_only = [r for r in zones_high["forbidden"] if r not in zones_low["forbidden"]]
    lines = [
        "-- СГЕНЕРИРОВАНО scripts/d48_to_luau.py из scripts/blender/d48c_layout.py и",
        "-- assets/concepts/d48/c2/mesh_placement.json — руками не править.",
        "-- Раскладка музея D48-C (утверждена владельцем 2026-11-06): главный зал с 8 нишами, две галереи по 6 мест (с",
        "-- уровня Gallery.Level), павильон и лестница в хранилище, сундук, лазеры, зоны защиты, модули Blender по уровням.",
        "-- Оси участка: начало — центр участка на уровне пола зала, вход в −Z, x+ — левая рука входящего. Ни от чего не",
        "-- зависит.",
        "",
        "export type Place = { slot: number, zone: string, center: Vector3, face: Vector3, unlock: number }",
        "export type Module = { model: string, position: Vector3, yaw: number, from: number, to: number }",
        "",
        "local MuseumLayout = {}",
        "",
        "-- Главный зал: полуширина, фасад и задняя грань, толщина стен, потолок, проём входа (полуширина, высота), трава",
        "-- и плита пола (от пола зала), передний край портика.",
        "MuseumLayout.Hall = {",
        f"\tHalfWidth = {num(hall['half_width'])},",
        f"\tFront = {num(hall['front'])},",
        f"\tBack = {num(hall['back'])},",
        f"\tWall = {num(hall['wall'])},",
        f"\tInnerX = {num(L.IX)},",
        f"\tInnerZ0 = {num(L.IZ0)},",
        f"\tInnerZ1 = {num(L.IZ1)},",
        f"\tCeiling = {num(hall['ceiling'])},",
        f"\tDoorHalf = {num(L.DOOR)},",
        f"\tDoorHeight = {num(L.DOORH)},",
        f"\tGround = {num(hall['ground'])},",
        f"\tSlab = {num(hall['slab'])},",
        f"\tPortico = {num(hall['portico'])},",
        "}",
        "",
        "-- Павильон над лестницей (портал спереди, z0) и лестница: верх у TopZ, ступени 1 × 1 вниз к +z, проём в полу.",
        "MuseumLayout.Pavilion = {",
        f"\tHalfX = {num(pav['half_x'])},",
        f"\tZ0 = {num(pav['z0'])},",
        f"\tZ1 = {num(pav['z1'])},",
        f"\tHeight = {num(pav['height'])},",
        "}",
        "MuseumLayout.Stair = {",
        f"\tTopZ = {num(stair['top_z'])},",
        f"\tHalfWidth = {num(stair['half_width'])},",
        f"\tSteps = {stair['steps']},",
        f"\tWellX = {num(stair['well_x'])},",
        f"\tWellZ1 = {num(stair['well_z1'])},",
        "}",
        "-- Хранилище под главным залом: пол и низ потолка (от пола зала), по плану — контур зала.",
        "MuseumLayout.Vault = {",
        f"\tFloor = {num(vault['floor'])},",
        f"\tCeiling = {num(vault['ceiling'])},",
        "}",
        "",
        "-- Галереи (места 9–20) с уровня Level: от стены зала (In) до наружной стены (Out), фасад Z0, арка из входного",
        "-- зала, клумба снаружи (x0, x1, высота).",
        "MuseumLayout.Gallery = {",
        f"\tIn = {num(gal['x_in'])},",
        f"\tOut = {num(gal['x_out'])},",
        f"\tZ0 = {num(gal['z0'])},",
        f"\tZ1 = {num(gal['z1'])},",
        f"\tHeight = {num(gal['height'])},",
        f"\tInnerX = {num(L.GAL_IX)},",
        f"\tInnerZ0 = {num(L.GAL_IZ0)},",
        f"\tInnerZ1 = {num(L.GAL_IZ1)},",
        f"\tEave = {num(gal['eave'])},",
        f"\tPlanter = {nums(gal['planter'])},",
        f"\tArch = {{ Z0 = {num(L.ARCH_Z0)}, Z1 = {num(L.ARCH_Z1)}, Height = {num(L.ARCH_H)} }},",
        f"\tLevel = {gal['level']},",
        f"\tZ = {nums(L.GAL_Z)},",
        f"\tInset = {num(L.GAL_D)},",
        "}",
        "",
        "-- Ниши главного зала (по 4 у боковой стены) и пилястры между ними.",
        "MuseumLayout.Niche = {",
        f"\tZ = {nums(L.NICHE_Z)},",
        f"\tPilasters = {nums(L.PIL_Z)},",
        f"\tInset = {num(L.NICHE_D)},",
        "}",
        "",
        "-- Постамент: верх Top × Top на высоте Height (GameConfig.Museum.ShowcaseSize), основание Base.",
        f"MuseumLayout.Showcase = {{ Top = {num(L.TOP)}, Base = {num(L.BASE)}, Height = 3 }}",
        "",
        "-- Места 1–20: центр постамента на полу, куда смотрит его лицо (в проход), уровень открытия max(6, 2 × уровень).",
        "MuseumLayout.Places = {",
    ]
    for p in lay["places"]:
        x, _, z = p["center"]
        zone = "Hall" if p["zone"] == "hall" else "Gallery"
        lines.append(f'\t{{ slot = {p["slot"]}, zone = "{zone}", center = {vec((x, 0, z))}, face = {vec(p["face"])}, '
                     f'unlock = {p["unlock_compat"]} }},')
    chest, stand = lay["chest"], lay["stand"]
    lines += [
        "} :: { Place }",
        "",
        "-- Сундук (центр на полу, замок смотрит в Face) и стенд музея у входа.",
        f"MuseumLayout.Chest = {{ Center = {vec((chest['center'][0], 0, chest['center'][1]))}, "
        f"Face = {vec(chest['face'])} }}",
        f"MuseumLayout.Stand = {{ Center = {vec((stand['center'][0], 0, stand['center'][1]))} }}",
        "",
        "-- Лазеры поперёк прохода: z, длина луча, высота.",
        "MuseumLayout.Lasers = {",
    ]
    for name, las in L.LASERS.items():
        lines.append(f"\t{name} = {{ z = {num(las['z'])}, length = {num(las['length'])}, y = {num(las['y'])} }},")
    lines += [
        "}",
        "",
        "-- Зоны защиты на полу (x0, x1, z0, z1): ловушка, робот и капкан — только в Allowed и не в Forbidden;",
        "-- GalleryForbidden добавляется с уровня Gallery.Level (подходы к аркам и сами галереи).",
        "MuseumLayout.Defense = {",
        f"\tAllowed = {rects(zones_low['allowed'])},",
        f"\tForbidden = {rects(zones_low['forbidden'])},",
        f"\tGalleryForbidden = {rects(gallery_only)},",
        "}",
        "",
        "-- Модули Blender (пачка Pack3_d48) по уровням музея: модель, место, поворот (градусы вокруг y), уровни from…to.",
        "MuseumLayout.Modules = {",
    ]
    for (model, position, yaw), first, last in modules():
        lines.append(f'\t{{ model = "{model}", position = {vec(position)}, yaw = {num(yaw)}, from = {first}, '
                     f'to = {last} }},')
    lines += ["} :: { Module }", "", "return MuseumLayout", ""]
    return "\n".join(lines)


def main():
    text = build()
    if "--check" in sys.argv:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if current != text:
            print("MuseumLayout.luau устарел: python scripts/d48_to_luau.py")
            sys.exit(1)
        print("MuseumLayout.luau совпадает с раскладкой")
        return
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("written", OUT)


if __name__ == "__main__":
    main()
