"""Привязка мешей этажей: assets/models/floors/<Тема>Floor.json (центры, размеры — scripts/blender/floor_*.py) и
<Тема>Floor.ids.json (MeshId после загрузки через Open Cloud) → src/shared/Floors/FloorMeshes.luau.

Пустые детали (не больше 2 треугольников — только якоря рисунка) пропускает. Проверяет: у каждой детали есть MeshId, идентификаторы не повторяются, имена деталей не повторяются между этажами
(шаблоны в ReplicatedStorage.FloorMeshes ищутся по имени — общий префикс двух этажей подменяет меши одного другим),
размеры в полосе этажа (−1…19).
Дальний силуэт <префикс>_S_All, если есть assets/models/floors_lod/<Тема>Sil.json (scripts/blender/lod_silhouette.py):
число треугольников берётся оттуда (≤ 400), габарит нового силуэта сверяется с габаритом детали — меш в ids.json
уже от Sil.fbx. Пересобрал этаж — заново прогони lod_silhouette.py и загрузи его Sil.fbx (BUGS.md).
Запуск: python scripts/floor_bind_meshes.py [--dry-run], затем stylua src/shared/Floors/FloorMeshes.luau
"""

import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "assets", "models", "floors")
OUT = os.path.join(REPO, "src", "shared", "Floors", "FloorMeshes.luau")
LOD = os.path.join(REPO, "assets", "models", "floors_lod")
SIL_TRIS = 400  # предел дальнего силуэта (как MESH_TRIS.silhouette в scripts/lune/check_tower.luau)


def silhouette(theme, name, d, errors):
    """Треугольники нового дальнего силуэта из floors_lod/<Тема>Sil.json; None — силуэт прежний."""
    path = os.path.join(LOD, theme + "Sil.json")
    if not name.endswith("_S_All") or not os.path.exists(path):
        return None
    sil = json.load(open(path, encoding="utf-8"))
    if sil.get("name") != name:
        errors.append("%s.%s: в %sSil.json деталь %s" % (theme, name, theme, sil.get("name")))
    if sil["tris"] > SIL_TRIS:
        errors.append("%s.%s: силуэт %d треугольников > %d" % (theme, name, sil["tris"], SIL_TRIS))
    lo, hi = sil["bbox_new"]
    for i in range(3):
        c, s = d["center"][i], d["size"][i]
        if abs(lo[i] - (c - s / 2)) > 0.01 or abs(hi[i] - (c + s / 2)) > 0.01:
            errors.append("%s.%s: габарит силуэта не совпадает с деталью по оси %d" % (theme, name, i))
            break
    return sil["tris"]


def num(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def vec(v):
    return "Vector3.new(%s)" % ", ".join(num(x) for x in v)


def main():
    lines = [
        "--!strict",
        "-- Меши этажей музея-небоскрёба: MeshId, уровень детализации, материал, центр и размер детали в осях этажа.",
        "-- Создаётся scripts/floor_bind_meshes.py из assets/models/floors/*.json — руками не править.",
        "-- Шаблоны MeshPart грузит сервер (World/FloorMeshLoader) в ReplicatedStorage.FloorMeshes, клиент их клонирует",
        "-- (Floors/FloorBuilder). Ни от чего не зависит.",
        "",
        "export type MeshInfo = { mesh: string, tier: string, material: string, center: Vector3, size: Vector3, tris: number }",
        "",
        "local FloorMeshes: { [string]: { asset: string, parts: { [string]: MeshInfo } } } = {",
    ]
    seen, errors, owner = {}, [], {}
    for path in sorted(glob.glob(os.path.join(SRC, "*Floor.json"))):
        theme = os.path.basename(path)[: -len("Floor.json")]
        ids_path = path[: -len(".json")] + ".ids.json"
        if not os.path.exists(ids_path):
            errors.append("%s: нет файла идентификаторов %s" % (theme, os.path.basename(ids_path)))
            continue
        info = json.load(open(path, encoding="utf-8"))
        ids = json.load(open(ids_path, encoding="utf-8"))
        lines.append("\t%s = {" % theme)
        lines.append('\t\tasset = "%s",' % ids["asset"])
        lines.append("\t\tparts = {")
        for name in sorted(info):
            d = info[name]
            if d["tris"] <= 4:  # пустая деталь (только якоря рисунка: 1–2 якоря, напр. Props без вещей) — без меша
                continue
            mesh = ids["meshes"].get(name)
            if not mesh or not mesh.startswith("rbxassetid://") or not mesh[len("rbxassetid://"):].isdigit():
                errors.append("%s.%s: нет MeshId" % (theme, name))
                continue
            if name in owner and owner[name] != theme:
                errors.append("%s.%s: имя детали уже у этажа %s (общий префикс)" % (theme, name, owner[name]))
            owner[name] = theme
            if mesh in seen:
                errors.append("%s.%s: MeshId повторяет %s" % (theme, name, seen[mesh]))
            seen[mesh] = "%s.%s" % (theme, name)
            y0, y1 = d["center"][1] - d["size"][1] / 2, d["center"][1] + d["size"][1] / 2
            if y0 < -1 - 1e-3 or y1 > 19 + 1e-3:
                errors.append("%s.%s: вне полосы этажа (%.3f…%.3f)" % (theme, name, y0, y1))
            tris = silhouette(theme, name, d, errors) or d["tris"]
            lines.append(
                '\t\t\t%s = { mesh = "%s", tier = "%s", material = "%s", center = %s, size = %s, tris = %d },'
                % (name, mesh, d["tier"], d["material"], vec(d["center"]), vec(d["size"]), tris)
            )
        lines.append("\t\t},")
        lines.append("\t},")
    lines += ["}", "", "return FloorMeshes", ""]
    if errors:
        print("ОШИБКИ:")
        for e in errors:
            print("  " + e)
        sys.exit(1)
    if "--dry-run" in sys.argv:
        print("\n".join(lines))
        return
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print("OK", OUT, len(seen), "мешей")


if __name__ == "__main__":
    main()
