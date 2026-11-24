"""Босс 5 «Йети-коллекционер»: скелет и десять клипов из Blender → модули Luau для игры.

Читает assets/models/Boss5_Yeti.rig.json (31 часть, точки вращения, габариты, 13 поз, выпады, части головы, лёд глыбы)
и assets/models/Boss5_Yeti.anim.json (клипы по кадрам: Transform каждого сустава в осях Roblox, [x, y, z, qx, qy, qz,
qw]; lens — яркость линзы монокля по кадрам). Пишет:
  src/shared/Config/Boss5YetiRig.luau — скелет и позы (формат Config/Boss4SphinxRig) и свои таблицы, как у дракона:
    AttackClips — вид выпада → клип, HeadParts — что вздрагивает при ударе, Eyes — линза (Neon открытого цвета,
    гаснет по каналу клипа), Body — контур тела сверху (X, Z) для дальности ближнего боя BodyRange, Transparent — лёд;
  src/shared/Config/Boss5YetiClips/init.luau и <Клип>.luau — по модулю на клип (каждый < 200 000 знаков).
Контур тела: выпуклая оболочка габаритов туловища, головы, ног и глыбы в покое (вид сверху), без рук — их выпад и так
идёт вперёд. Медленные циклы (сон и стойка) — через кадр. Руками модули не править.
Запуск из корня: python scripts/boss5_to_luau.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from boss4_to_luau import LIMIT, lua_str, num, quat_canon, vec, write  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
CONFIG = os.path.join(ROOT, "src", "shared", "Config")
CLIP_DIR = os.path.join(CONFIG, "Boss5YetiClips")
HALF_RATE = {"sleep_idle", "combat_idle"}
MODULE = {"sleep_idle": "SleepIdle", "wake": "Wake", "combat_idle": "CombatIdle", "walk": "Walk", "smash": "Smash",
          "ice_clap": "IceClap", "hit": "Hit", "victory": "Victory", "defeat": "Defeat", "fall_asleep": "FallAsleep"}
BODY_PARTS = ("Torso", "Head", "Jaw", "ThighL", "ThighR", "ShinL", "ShinR", "FootL", "FootR", "Block", "BlockFrame")
LENS = {"Open": "B4F8FF", "Closed": "2E3A4A"}  # линза: светится (Neon) — погасла
ICE_TRANSPARENCY = 0.45  # лёд глыбы: экспонаты видны (Glass в игре непрозрачен, BUGS.md)


def hull(points):
    """Выпуклая оболочка точек (x, z) — против часовой стрелки (монотонная цепь Эндрю)."""
    pts = sorted(set(points))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def body_outline(rig):
    pts = []
    for name in BODY_PARTS:
        p = rig["parts"][name]
        cx, cz = p["pivot"][0] + p["center"][0], p["pivot"][2] + p["center"][2]
        hx, hz = p["size"][0] / 2, p["size"][2] / 2
        pts += [(cx - hx, cz - hz), (cx + hx, cz - hz), (cx + hx, cz + hz), (cx - hx, cz + hz)]
    return hull([(round(x, 2), round(z, 2)) for x, z in pts])


def lens_keys(values, fps, duration):
    """Канал линзы: пары время, значение — только изломы (постоянный 1 — нет канала: светится весь клип)."""
    if all(abs(v - 1) < 1e-3 for v in values):
        return None
    keys = []
    for i, v in enumerate(values):
        t = min(i / fps, duration)
        if 0 < i < len(values) - 1 and abs((values[i - 1] + values[i + 1]) / 2 - v) < 2e-3:
            continue  # на прямой между соседями
        keys += [t, v]
    return keys


def frame_matrix(v):
    """Кадр клипа (x, y, z, qx, qy, qz, qw) → 12 чисел позы (позиция и матрица поворота по строкам, как CFrame.new)."""
    x, y, z, qx, qy, qz, qw = v
    return [x, y, z,
            1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw),
            2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw),
            2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rig = json.load(open(os.path.join(MODELS, "Boss5_Yeti.rig.json"), encoding="utf-8"))
    anim = json.load(open(os.path.join(MODELS, "Boss5_Yeti.anim.json"), encoding="utf-8"))
    colors = json.load(open(os.path.join(MODELS, "Boss5_Yeti.colors.json"), encoding="utf-8"))
    order = rig["order"]
    assert anim["order"] == order, "порядок частей в anim.json и rig.json разный"
    assert set(anim["clips"]) == set(MODULE), f"клипы: {sorted(anim['clips'])}"
    assert set(rig["attack_clips"].values()) <= set(MODULE)

    body = body_outline(rig)
    lines = [
        "-- Скелет босса 5 «Йети-коллекционер» для Motor6D (D18, D64; стиль D39): части, точки вращения, габариты,",
        "-- 13 ключевых поз и клипы. Сгенерировано scripts/boss5_to_luau.py — руками не править. Оси Roblox, стады; лицо",
        "-- смотрит в +Z модели. pivot — точка вращения в покое (подошвы на y = 0), center и size — габарит меша от неё.",
        "-- Свои таблицы (как у дракона, Shared/BossClips): AttackClips — вид выпада → клип (bite — «Удар кулаком сверху»,",
        "-- swipe — «Ледяной хлопок», только анимация D64); HeadParts — вздрагивают при ударе поверх выпада; Eyes — линза",
        "-- монокля (Neon открытого цвета, гаснет по каналу клипа: во сне погасла); Body — контур тела сверху (X, Z) для",
        "-- дальности ближнего боя (Battle.Bosses[5].BodyRange); Transparent — лёд глыбы (экспонаты видны).",
        "-- Зависит только от Config/Boss5YetiClips.",
        "",
        "return {",
        f"\tScale = {num(rig['scale'], 3)},",
        "\tOrder = { " + ", ".join(lua_str(p) for p in order) + " },",
        "\tParts = {",
    ]
    for name in order:
        p = rig["parts"][name]
        parent = lua_str(p["parent"]) if p["parent"] else "nil"
        extra = ", eye = true" if name == "Lens" else ""
        lines.append(f"\t\t{name} = {{ parent = {parent}, pivot = {vec(p['pivot'])}, center = {vec(p['center'])}, "
                     f"size = {vec(p['size'])}, map = {lua_str(p['map'])}, color = {lua_str(colors.get(name, 'EEF4FF'))}"
                     f"{extra} }},")
    lines.append("\t},")
    # Поза sleep — первый кадр клипа sleep_idle: в rig.json у неё нет опускания корня (во сне Йети сидит на 1.8 ниже —
    # это сдвиг объекта в boss5_yeti.py; в клипы он запечён и проверен по вершинам). Иначе стык «поза → клип» прыгал бы.
    poses = dict(rig["poses"])
    poses["sleep"] = {name: frame_matrix(anim["clips"]["sleep_idle"]["frames"][0][i]) for i, name in enumerate(order)}
    lines.append("\tPoses = {")
    for pose, parts in poses.items():
        lines.append(f"\t\t{pose} = {{")
        for name in order:
            lines.append(f"\t\t\t{name} = {{ " + ", ".join(num(c, 4) for c in parts[name]) + " },")
        lines.append("\t\t},")
    lines.append("\t},")
    lines.append("\tClips = require(script.Parent.Boss5YetiClips),")
    lines.append("\tAttackClips = { " + ", ".join(f"{k} = {lua_str(v)}" for k, v in rig["attack_clips"].items()) + " },")
    lines.append("\tAttackDefault = " + lua_str(rig["attack_clips"]["bite"]) + ",")
    lines.append("\tHeadParts = { " + ", ".join(lua_str(p) for p in rig["head_parts"]) + " },")
    lines.append(f"\tEyes = {{ Parts = {{ \"Lens\" }}, Open = {lua_str(LENS['Open'])}, Closed = {lua_str(LENS['Closed'])} }},")
    lines.append("\tBody = { " + ", ".join(f"Vector2.new({num(x, 2)}, {num(z, 2)})" for x, z in body) + " },")
    lines.append("\tTransparent = { " + ", ".join(f"{p} = {num(ICE_TRANSPARENCY, 2)}" for p in rig["ice_parts"]) + " },")
    lines.append("}")
    write(os.path.join(CONFIG, "Boss5YetiRig.luau"), "\n".join(lines) + "\n")

    os.makedirs(CLIP_DIR, exist_ok=True)
    sizes = {}
    for name, clip in anim["clips"].items():
        frames = clip["frames"]
        step = 2 if name in HALF_RATE else 1
        if clip["loop"]:
            assert len(frames) % step == 0, f"{name}: цикл из нечётного числа кадров"
        else:
            assert (len(frames) - 1) % step == 0, f"{name}: последний кадр выпадает"
        kept = frames[::step]
        fps = anim["fps"] / step
        moved = [p for i, p in enumerate(order) if any(max(abs(c) for c in f[i][:3]) > 5e-4 for f in frames)]
        data = []
        for f in kept:
            for i, part in enumerate(order):
                x, y, z, qx, qy, qz, qw = f[i]
                data += [num(c, 4) for c in quat_canon((qx, qy, qz, qw))]
                if part in moved:
                    data += [num(x, 3), num(y, 3), num(z, 3)]
        events = ", ".join(f"[{lua_str(k)}] = {num(v, 4)}" for k, v in clip["events"].items())
        per = len(order) * 4 + len(moved) * 3
        rows = ["\t\t" + ", ".join(data[i:i + per]) + "," for i in range(0, len(data), per)]
        keys = lens_keys(clip["lens"], anim["fps"], clip["duration"])
        eyes = [f"\teyes = {{ {', '.join(num(v, 4) for v in keys)} }},"] if keys else []
        text = "\n".join([
            f"-- Клип «{clip['title']}» босса 5 (Config/Boss5YetiRig). Сгенерировано scripts/boss5_to_luau.py из",
            "-- assets/models/Boss5_Yeti.anim.json — руками не править. data: по кадрам, в каждом — части по Order: кватернион",
            "-- qx, qy, qz, qw, а у частей из moved ещё сдвиг x, y, z — Transform сустава; eyes — яркость линзы (время,",
            "-- значение…; нет — светится весь клип). Ни от чего не зависит.",
            "",
            "return {",
            f"\tname = {lua_str(name)},",
            f"\ttitle = {lua_str(clip['title'])},",
            f"\tduration = {num(clip['duration'], 4)},",
            f"\tloop = {'true' if clip['loop'] else 'false'},",
            f"\tfps = {num(fps, 3)},",
            f"\tframes = {len(kept)},",
            f"\tstartPose = {lua_str(clip['start_pose']) if clip['start_pose'] else 'nil'},",
            f"\tendPose = {lua_str(clip['end_pose']) if clip['end_pose'] else 'nil'},",
            f"\tevents = {{ {events} }},",
            *eyes,
            "\tmoved = { " + ", ".join(lua_str(p) for p in moved) + " },",
            "\tdata = {",
            *rows,
            "\t},",
            "}",
            "",
        ])
        write(os.path.join(CLIP_DIR, MODULE[name] + ".luau"), text)
        sizes[name] = len(text)
        assert len(text) < LIMIT, f"{name}: {len(text)} знаков — больше предела модуля"
        print(f"клип {name:12s} кадров {len(kept):4d} ({fps:.0f}/с), со сдвигом {len(moved):2d}, линза "
              f"{'—' if not keys else len(keys) // 2}, {len(text):7d} знаков")

    loaders = "\n".join(f"\t{name} = function()\n\t\treturn require(script.{mod})\n\tend," for name, mod in MODULE.items())
    write(os.path.join(CLIP_DIR, "init.luau"), "\n".join([
        "-- Клипы босса 5 «Йети-коллекционер»: имя → данные клипа (модуль загружается при первом обращении). Сгенерировано",
        "-- scripts/boss5_to_luau.py — руками не править. Проигрыватель — Shared/BossClips. Ни от чего не зависит.",
        "",
        "local loaders = {",
        loaders,
        "}",
        "",
        "local Clips = {}",
        "",
        "Clips.Names = { " + ", ".join(lua_str(n) for n in MODULE) + " }",
        "",
        "-- Данные клипа name (nil — такого клипа нет).",
        "function Clips.Load(name: string): any",
        "\tlocal load = loaders[name]",
        "\treturn if load then load() else nil",
        "end",
        "",
        "return Clips",
        "",
    ]))
    print(f"контур тела: {len(body)} точек, x {min(p[0] for p in body)}…{max(p[0] for p in body)}, "
          f"z {min(p[1] for p in body)}…{max(p[1] for p in body)}")
    print(f"всего {sum(sizes.values())} знаков в {len(sizes)} модулях; самый большой — {max(sizes.values())}")


if __name__ == "__main__":
    main()
