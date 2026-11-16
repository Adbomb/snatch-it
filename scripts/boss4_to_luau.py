"""Босс 4 «Сфинкс-лежебока»: скелет и десять клипов из Blender → модули Luau для игры.

Читает assets/models/Boss4_Sphinx.rig.json (части, точки вращения, габариты, 13 поз), assets/models/Boss4_Sphinx.anim.json
(клипы по кадрам: Transform каждого сустава в осях Roblox, [x, y, z, qx, qy, qz, qw]) и
assets/models/Boss4_Sphinx.colors.json (средний цвет каждой части по карте — заготовка до импорта мешей; пишет
scripts/blender/boss4_sphinx_fixture.py). Пишет:
  src/shared/Config/Boss4SphinxRig.luau — скелет и позы (формат как у Config/Boss3RatKingRig) + ссылка на клипы;
  src/shared/Config/Boss4SphinxClips/init.luau и <Клип>.luau — по модулю на клип (каждый < 200 000 знаков).
Медленные циклы (сон и боевая стойка) хранятся через кадр (15 в секунду) — ошибка носка лапы 0 (отчёт анимаций),
остальные — все 30 кадров. Поворот — кватернион (4 знака после запятой), сдвиг — только у частей, у которых он есть
(3 знака). Руками модули не править. Запуск из корня репозитория: python scripts/boss4_to_luau.py
"""

import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
CONFIG = os.path.join(ROOT, "src", "shared", "Config")
CLIP_DIR = os.path.join(CONFIG, "Boss4SphinxClips")
HALF_RATE = {"sleep_idle", "combat_idle"}  # циклы без перестановки лап: через кадр без потерь
MODULE = {"sleep_idle": "SleepIdle", "wake": "Wake", "combat_idle": "CombatIdle", "walk": "Walk",
          "heavy_paw": "HeavyPaw", "tail_strike": "TailStrike", "hit": "Hit", "victory": "Victory",
          "defeat": "Defeat", "fall_asleep": "FallAsleep"}
LIMIT = 200_000


def num(v, digits):
    s = f"{v:.{digits}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def vec(v):
    return "Vector3.new({}, {}, {})".format(*(num(c, 4) for c in v))


def quat_canon(q):
    """Кватернион с w ≥ 0 и единичной длиной (знак не меняет поворот)."""
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    s = (1.0 if w >= 0 else -1.0) / n
    return x * s, y * s, z * s, w * s


def lua_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rig = json.load(open(os.path.join(MODELS, "Boss4_Sphinx.rig.json"), encoding="utf-8"))
    anim = json.load(open(os.path.join(MODELS, "Boss4_Sphinx.anim.json"), encoding="utf-8"))
    colors_path = os.path.join(MODELS, "Boss4_Sphinx.colors.json")
    colors = json.load(open(colors_path, encoding="utf-8")) if os.path.exists(colors_path) else {}
    order = rig["order"]
    assert anim["order"] == order, "порядок частей в anim.json и rig.json разный"
    assert set(anim["clips"]) == set(MODULE), f"клипы: {sorted(anim['clips'])}"

    # — скелет —
    lines = [
        "-- Скелет босса 4 «Сфинкс-лежебока» для Motor6D (D18; модель v2, стиль D39): части, точки вращения, габариты,",
        "-- 13 ключевых поз и клипы анимаций. Сгенерировано scripts/boss4_to_luau.py — руками не править. Оси Roblox,",
        "-- стады; лицо смотрит в +Z модели. pivot — точка вращения части в покое (низ лап на y = 0), center и size —",
        "-- габариты меша относительно точки вращения, color — средний цвет части по карте (заготовка до импорта мешей).",
        "-- Позы: часть → {x, y, z, r00…r22} — Transform сустава относительно покоя (у Torso — вместе с подъёмом к земле);",
        "-- имена как у пса (Shared/BossAnim): bite — «Тяжёлая лапа», swipe — «Хвост-кистень», bark и bark2 — победа.",
        "-- Clips — клипы по кадрам (Config/Boss4SphinxClips): у скелета с клипами BossAnim играет их, а не позы.",
        "-- Зависит только от Config/Boss4SphinxClips.",
        "",
        "return {",
        f"\tScale = {num(rig['scale'], 3)},",
        "\tOrder = { " + ", ".join(lua_str(p) for p in order) + " },",
        "\tParts = {",
    ]
    for name in order:
        p = rig["parts"][name]
        parent = lua_str(p["parent"]) if p["parent"] else "nil"
        color = colors.get(name, "C9A05A")
        lines.append(f"\t\t{name} = {{ parent = {parent}, pivot = {vec(p['pivot'])}, center = {vec(p['center'])}, "
                     f"size = {vec(p['size'])}, map = {lua_str(p['map'])}, color = {lua_str(color)} }},")
    lines.append("\t},")
    lines.append("\tPoses = {")
    for pose, parts in rig["poses"].items():
        lines.append(f"\t\t{pose} = {{")
        for name in order:
            lines.append(f"\t\t\t{name} = {{ " + ", ".join(num(c, 4) for c in parts[name]) + " },")
        lines.append("\t\t},")
    lines.append("\t},")
    lines.append("\tClips = require(script.Parent.Boss4SphinxClips),")
    lines.append("}")
    write(os.path.join(CONFIG, "Boss4SphinxRig.luau"), "\n".join(lines) + "\n")

    # — клипы —
    os.makedirs(CLIP_DIR, exist_ok=True)
    sizes = {}
    for name, clip in anim["clips"].items():
        frames = clip["frames"]
        step = 2 if name in HALF_RATE else 1
        if clip["loop"]:
            assert len(frames) % step == 0, f"{name}: цикл из нечётного числа кадров"
            kept = frames[::step]
        else:
            kept = frames[::step]
            assert (len(frames) - 1) % step == 0, f"{name}: последний кадр выпадает"
        fps = anim["fps"] / step
        moved = [p for i, p in enumerate(order) if any(max(abs(c) for c in f[i][:3]) > 5e-4 for f in frames)]
        data = []
        for f in kept:
            for i, part in enumerate(order):
                x, y, z, qx, qy, qz, qw = f[i]
                q = quat_canon((qx, qy, qz, qw))
                data += [num(c, 4) for c in q]
                if part in moved:
                    data += [num(x, 3), num(y, 3), num(z, 3)]
        events = ", ".join(f"[{lua_str(k)}] = {num(v, 4)}" for k, v in clip["events"].items())
        rows = []
        per = len(order) * 4 + len(moved) * 3
        for i in range(0, len(data), per):
            rows.append("\t\t" + ", ".join(data[i:i + per]) + ",")
        text = "\n".join([
            f"-- Клип «{clip['title']}» босса 4 (Config/Boss4SphinxRig). Сгенерировано scripts/boss4_to_luau.py из",
            "-- assets/models/Boss4_Sphinx.anim.json — руками не править. data: по кадрам, в каждом — части по Order: кватернион",
            "-- qx, qy, qz, qw, а у частей из moved ещё сдвиг x, y, z — Transform сустава. Ни от чего не зависит.",
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
            "\tmoved = { " + ", ".join(lua_str(p) for p in moved) + " },",
            "\tdata = {",
            *rows,
            "\t},",
            "}",
            "",
        ])
        path = os.path.join(CLIP_DIR, MODULE[name] + ".luau")
        write(path, text)
        sizes[name] = len(text)
        assert len(text) < LIMIT, f"{name}: {len(text)} знаков — больше предела модуля"
        print(f"клип {name:12s} кадров {len(kept):4d} ({fps:.0f}/с), со сдвигом {len(moved):2d} частей, {len(text):7d} знаков")

    loaders = "\n".join(f"\t{name} = function()\n\t\treturn require(script.{mod})\n\tend," for name, mod in MODULE.items())
    index = "\n".join([
        "-- Клипы босса 4 «Сфинкс-лежебока»: имя → данные клипа (модуль загружается при первом обращении). Сгенерировано",
        "-- scripts/boss4_to_luau.py — руками не править. Проигрыватель — Shared/BossClips. Ни от чего не зависит.",
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
    ])
    write(os.path.join(CLIP_DIR, "init.luau"), index)
    print(f"всего {sum(sizes.values())} знаков в {len(sizes)} модулях; самый большой — {max(sizes.values())}")
    print("цвета частей:", "из " + os.path.basename(colors_path) if colors else "нет файла — общий цвет C9A05A")


if __name__ == "__main__":
    main()
