"""Босс 10 «Король-дракон»: скелет и клипы из Blender → модули Luau для игры (этап A, boss10_v7_anim4/REPORT.md §6).

Читает assets/models/Boss10_Dragon.rig.json (52 сустава, точки вращения, габариты, средние цвета, позы stand / combat
/ sleep, контур тела, центр магического круга) и assets/models/Boss10_Dragon.anim.json (13 клипов и шаг на месте
влево и вправо: Transform каждого сустава от покоя в осях Roblox, [x, y, z, qx, qy, qz, qw]; оба файла пишет
scripts/blender/dragon10/v7_export.py). Пишет:
  src/shared/Config/Boss10DragonRig.luau — скелет и позы (формат как у Config/Boss4SphinxRig) + клипы выпадов, шаг
  на месте, части головы для реакции на удар, кости перепонок;
  src/shared/Config/Boss10DragonClips/init.luau и <Клип>.luau — по модулю на клип; клип больше 190 000 знаков делится
  на части <Клип>_2, <Клип>_3 (загрузчик склеивает кадры).
Этап C (если файлы есть): assets/models/Boss10_Dragon_game.json (scripts/blender/dragon10/v7_game_export.py) —
группы карт и габариты мешей частей, добавочные меши Extras (Body_2 — правая половина корпуса, EyeL/R — глаза),
перепонки MembraneMesh; assets/models/Boss10_wings_bones.json (scripts/boss10_bind_after_import.py, из Studio) —
кости перепонок в покое от их MeshPart; assets/models/Boss10_Dragon.eyes.json — канал глаз клипов (eyes в модуле
клипа: время, значение, … — 0 закрыты, 1 открыты; нет — открыты).
Медленные циклы (сон и боевая стойка) — через кадр (15 в секунду), как у Сфинкса; остальные — все 30 кадров. Поворот —
кватернион (4 знака), сдвиг — только у суставов, которые сдвигаются (3 знака). Руками модули не править.
Запуск из корня репозитория: python scripts/boss10_to_luau.py
"""

import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
CONFIG = os.path.join(ROOT, "src", "shared", "Config")
CLIP_DIR = os.path.join(CONFIG, "Boss10DragonClips")
HALF_RATE = {"sleep_idle", "combat_idle"}
MODULE = {"sleep_idle": "SleepIdle", "wake": "Wake", "combat_idle": "CombatIdle", "walk": "Walk",
          "claw_swipe": "ClawSwipe", "bite": "Bite", "tail_strike": "TailStrike", "wing_buffet": "WingBuffet",
          "magic_volley": "MagicVolley", "hit": "Hit", "victory": "Victory", "defeat": "Defeat",
          "fall_asleep": "FallAsleep", "turn_step_left": "TurnStepLeft", "turn_step_right": "TurnStepRight"}
LIMIT = 190_000
# Этап C.2 — переходы (Shared/PoseFade, BossClips): время входа выпада без плана (= Battle.HitDelay) и сглаживание
# разрыва позы при смене источника.
CATCH_UP_IN = 0.25
FADE_TIME, FADE_JUMP = 0.25, 12

# Вид выпада на сервере → клип (Shared/BossClips, rig.AttackClips). Урон и интервал у всех одинаковые.
ATTACK_CLIPS = {"claw": "claw_swipe", "bite": "bite", "tail": "tail_strike", "wings": "wing_buffet",
                "volley": "magic_volley"}
HEAD = ["Head", "Jaw", "Neck4"]


def num(v, digits):
    s = f"{v:.{digits}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def vec(v):
    return "Vector3.new({}, {}, {})".format(*(num(c, 4) for c in v))


def quat_canon(q):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    s = (1.0 if w >= 0 else -1.0) / n
    return x * s, y * s, z * s, w * s


def lua_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def load_opt(name):
    path = os.path.join(MODELS, name)
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def clip_text(header, fields, rows, part_of=None):
    return "\n".join(header + ["", "return {", *fields, "\tdata = {", *rows, "\t},", "}", ""])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rig = json.load(open(os.path.join(MODELS, "Boss10_Dragon.rig.json"), encoding="utf-8"))
    anim = json.load(open(os.path.join(MODELS, "Boss10_Dragon.anim.json"), encoding="utf-8"))
    order = rig["order"]
    game = load_opt("Boss10_Dragon_game.json")
    bones = load_opt("Boss10_wings_bones.json")
    eyes = load_opt("Boss10_Dragon.eyes.json")
    if game:
        for name in order:
            g = game["parts"][name]
            rig["parts"][name].update(center=g["center"], size=g["size"], map=g["map"])
    assert anim["order"] == order, "порядок суставов в anim.json и rig.json разный"
    assert set(anim["clips"]) == set(MODULE), f"клипы: {sorted(anim['clips'])}"
    for name in order:
        par = rig["parts"][name]["parent"]
        assert par is None or order.index(par) < order.index(name), f"{name}: родитель {par} позже в порядке"

    # — скелет —
    lines = [
        "-- Скелет босса 10 «Король-дракон» для Motor6D (модель v7, риг 53 кости, анимации итерации 4): суставы, точки",
        "-- вращения, габариты, позы, клипы. Сгенерировано scripts/boss10_to_luau.py — руками не править. Оси Roblox, стады;",
        "-- лицо смотрит в +Z модели; кость Root — корень модели (её поворот делает сама модель). pivot — точка вращения",
        "-- сустава в покое (земля — y = 0), center и size — габариты меша от точки вращения, color — средний цвет части",
        "-- (заготовка до импорта мешей), bone — имя кости в Blender. Позы: сустав → {x, y, z, r00…r22} — Transform от покоя.",
        "-- AttackClips — вид выпада → клип (Shared/BossClips); TurnClips — шаг на месте при повороте модели (Turn.Rate °/с,",
        "-- клип — 90° за цикл); HeadParts — что вздрагивает при ударе поверх выпада; Membranes — кости перепонок крыльев",
        "-- (skinned mesh после импорта, этап C: те же имена суставов). Body — контур тела сверху (X, Z) для дальности",
        "-- ближнего боя; VolleyOrigin — центр магического круга залпа от корня модели. Этап C: Extras — добавочные меши",
        "-- (Body_2 — правая половина корпуса, EyeL/R — глаза) от точки вращения своего сустава; MembraneMesh — перепонки",
        "-- (skinned): центр меша в покое и кости (cframe — от MeshPart перепонок, из импорта); Eyes — части глаз и цвета",
        "-- закрытого и открытого глаза (канал eyes в клипах).",
        "-- Зависит только от Config/Boss10DragonClips.",
        "",
        "return {",
        f"\tScale = {num(rig['scale'], 3)},",
        "\tOrder = { " + ", ".join(lua_str(p) for p in order) + " },",
        "\tParts = {",
    ]
    for name in order:
        p = rig["parts"][name]
        parent = lua_str(p["parent"]) if p["parent"] else "nil"
        lines.append(f"\t\t{name} = {{ parent = {parent}, pivot = {vec(p['pivot'])}, center = {vec(p['center'])}, "
                     f"size = {vec(p['size'])}, map = {lua_str(p['map'])}, color = {lua_str(p['color'])}, "
                     f"bone = {lua_str(p['bone'])} }},")
    lines.append("\t},")
    lines.append("\tPoses = {")
    for pose, parts in rig["poses"].items():
        lines.append(f"\t\t{pose} = {{")
        for name in order:
            lines.append(f"\t\t\t{name} = {{ " + ", ".join(num(c, 4) for c in parts[name]) + " },")
        lines.append("\t\t},")
    lines.append("\t},")
    lines.append("\tAttackClips = { " + ", ".join(f"{k} = {lua_str(v)}" for k, v in ATTACK_CLIPS.items()) + " },")
    lines.append(f"\tTurn = {{ Rate = {num(rig['turn_rate'], 2)}, Left = \"turn_step_left\", Right = \"turn_step_right\", Degrees = 90 }},")
    lines.append("\tHeadParts = { " + ", ".join(lua_str(p) for p in HEAD) + " },")
    # этап C.2: выпад без плана (сервер бьёт сразу) входит в силу за всё время до попадания (Battle.HitDelay), а не
    # за 0.12 с; разрыв позы при смене источника (план → залп в одном шаге сервера, пауза вне кадра) — Shared/PoseFade
    lines.append(f"\tCatchUpIn = {CATCH_UP_IN}, -- с: выпад без плана набирает силу до момента попадания")
    lines.append(f"\tFade = {{ Time = {FADE_TIME}, Jump = {FADE_JUMP} }}, -- Shared/PoseFade: с и градусов")
    lines.append("\tMembranes = {")
    for x, m in rig["membranes"].items():
        lines.append(f"\t\t{x} = {{ " + ", ".join(lua_str(b.replace('.', '')) for b in m["bones"]) + " },")
    lines.append("\t},")
    lines.append("\tBody = { " + ", ".join(f"Vector2.new({num(x, 2)}, {num(z, 2)})" for x, z in rig["body"]) + " },")
    lines.append(f"\tVolleyOrigin = {vec(rig['volley_origin'])},")
    if game:
        lines.append("\tExtras = {")
        for name, e in game["extras"].items():
            extra = f"map = {lua_str(e['map'])}" if e.get("map") else "eye = true"
            lines.append(f"\t\t{name} = {{ joint = {lua_str(e['joint'])}, center = {vec(e['center'])}, "
                         f"size = {vec(e['size'])}, {extra} }},")
        lines.append("\t},")
    if game and bones:
        m = game["membranes"]
        lines.append("\tMembraneMesh = {")
        lines.append(f"\t\tname = {lua_str(m['mesh'])}, center = {vec(m['center'])}, size = {vec(m['size'])}, "
                     f"map = {lua_str(m['map'])},")
        lines.append("\t\tbones = {")
        for b, rec in bones["bones"].items():
            cf = ", ".join(num(c, 5) for c in rec["cframe"])
            par = lua_str(rec["parent"]) if rec.get("parent") else "nil"
            lines.append(f"\t\t\t{b} = {{ parent = {par}, cframe = CFrame.new({cf}) }},")
        lines.append("\t\t},")
        lines.append("\t},")
    if eyes:
        lines.append(f"\tEyes = {{ Parts = {{ \"EyeL\", \"EyeR\" }}, Open = {lua_str(eyes['open'])}, "
                     f"Closed = {lua_str(eyes['closed'])} }},")
    lines.append("\tClips = require(script.Parent.Boss10DragonClips),")
    lines.append("}")
    write(os.path.join(CONFIG, "Boss10DragonRig.luau"), "\n".join(lines) + "\n")

    # — клипы —
    os.makedirs(CLIP_DIR, exist_ok=True)
    for old in os.listdir(CLIP_DIR):
        if old.endswith(".luau"):
            os.remove(os.path.join(CLIP_DIR, old))
    sizes, chunks = {}, {}
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
        rows = []
        for f in kept:
            data = []
            for i, part in enumerate(order):
                x, y, z, qx, qy, qz, qw = f[i]
                data += [num(c, 4) for c in quat_canon((qx, qy, qz, qw))]
                if part in moved:
                    data += [num(x, 3), num(y, 3), num(z, 3)]
            rows.append("\t\t" + ", ".join(data) + ",")
        events = ", ".join(f"[{lua_str(k)}] = {num(v, 4)}" for k, v in clip["events"].items())
        head = [f"-- Клип «{clip['title']}» босса 10 (Config/Boss10DragonRig). Сгенерировано scripts/boss10_to_luau.py из",
                "-- assets/models/Boss10_Dragon.anim.json — руками не править. data: по кадрам, в каждом — суставы по Order:",
                "-- кватернион qx, qy, qz, qw, а у суставов из moved ещё сдвиг x, y, z — Transform сустава. Ни от чего не зависит."]
        fields = [f"\tname = {lua_str(name)},", f"\ttitle = {lua_str(clip['title'])},",
                  f"\tduration = {num(clip['duration'], 4)},", f"\tloop = {'true' if clip['loop'] else 'false'},",
                  f"\tfps = {num(fps, 3)},", f"\tframes = {len(kept)},",
                  f"\tstartPose = {lua_str(clip['start_pose']) if clip['start_pose'] else 'nil'},",
                  f"\tendPose = {lua_str(clip['end_pose']) if clip['end_pose'] else 'nil'},",
                  f"\tevents = {{ {events} }},", "\tmoved = { " + ", ".join(lua_str(p) for p in moved) + " },"]
        if eyes and name in eyes["clips"]:
            keys = ", ".join(f"{num(t, 4)}, {num(v, 3)}" for t, v in eyes["clips"][name])
            fields.append(f"\teyes = {{ {keys} }},")
        # части по пределу модуля
        groups, cur, size = [], [], 0
        for r in rows:
            if cur and size + len(r) > LIMIT - 4000:
                groups.append(cur)
                cur, size = [], 0
            cur.append(r)
            size += len(r) + 1
        groups.append(cur)
        mod = MODULE[name]
        total = 0
        for k, g in enumerate(groups):
            if k == 0:
                text = clip_text(head, fields + ([f"\tparts = {len(groups)},"] if len(groups) > 1 else []), g)
                path = os.path.join(CLIP_DIR, mod + ".luau")
            else:
                text = clip_text([f"-- Часть {k + 1} клипа «{clip['title']}» босса 10 (кадры дальше части {k}). "
                                  "Сгенерировано scripts/boss10_to_luau.py — руками не править."], [], g)
                path = os.path.join(CLIP_DIR, f"{mod}_{k + 1}.luau")
            assert len(text) < 200_000, f"{name} часть {k + 1}: {len(text)} знаков"
            write(path, text)
            total += len(text)
        sizes[name] = total
        chunks[name] = len(groups)
        print(f"клип {name:16s} кадров {len(kept):4d} ({fps:.0f}/с), со сдвигом {len(moved):2d} суставов, "
              f"{total:7d} знаков, модулей {len(groups)}")

    loaders = []
    for name, mod in MODULE.items():
        if chunks[name] == 1:
            loaders.append(f"\t{name} = function()\n\t\treturn require(script.{mod})\n\tend,")
        else:
            rest = ", ".join(f"script.{mod}_{k}" for k in range(2, chunks[name] + 1))
            loaders.append(f"\t{name} = function()\n\t\treturn joined(require(script.{mod}), {{ {rest} }})\n\tend,")
    # склейка частей — только если какой-то клип разбит (иначе selene: неиспользуемая функция)
    joiner = [
        "-- Кадры частей 2…n — в конец данных первой части (каждая часть — целые кадры).",
        "local function joined(first: any, rest: { ModuleScript }): any",
        "\tif first.parts == nil then",
        "\t\treturn first",
        "\tend",
        "\tlocal data = table.clone(first.data)",
        "\tfirst.data = nil -- числа уже в общем массиве: в кэше модулей их не держать",
        "\tfor _, module in rest do",
        "\t\tlocal part = require(module) :: any",
        "\t\tfor _, v in part.data do",
        "\t\t\ttable.insert(data, v)",
        "\t\tend",
        "\t\tpart.data = nil",
        "\tend",
        "\tlocal out = table.clone(first)",
        "\tout.data = data",
        "\tout.parts = nil",
        "\treturn out",
        "end",
        "",
    ] if any(n > 1 for n in chunks.values()) else []
    index = "\n".join([
        "-- Клипы босса 10 «Король-дракон»: имя → данные клипа (модуль загружается при первом обращении; клип из нескольких",
        "-- частей склеивается по кадрам). Сгенерировано scripts/boss10_to_luau.py — руками не править. Проигрыватель —",
        "-- Shared/BossClips. Ни от чего не зависит.",
        "",
        *joiner,
        "local loaders = {",
        *loaders,
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
    print(f"всего {sum(sizes.values())} знаков в {sum(chunks.values())} модулях клипов")


if __name__ == "__main__":
    main()
