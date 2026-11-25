"""Проверки проекта без Roblox Studio (после бана аккаунта 2026-11-02, docs/RECOVERY_STATUS.md):

1. Запрещённого контента нет в активной сборке: ID ассетов, за которые Roblox заблокировал аккаунт, и файлы картин
   с обнажёнными фигурами (src, default.project.json, assets кроме *.md, scripts кроме этого файла).
2. Каждый require в src указывает на существующий модуль (пути Rojo из default.project.json, алиасы
   local X = game:GetService(…) / X:WaitForChild(…); динамические require — в списке «не проверено»).
3. Карты предметов: у каждого предмета Config/ItemModels есть шаблон Server/Looks с теми же ColorMap и NormalMap,
   есть MeshId и исходник assets/models/art/<id>.fbx. У босса — шаблоны Looks/Boss<N>_<группа> для карт BossModels.
4. Коллекция босса 2 (docs/CATALOG.md) подключена: каждый id — в Config/Items у босса 2 (find), id не повторяются,
   у каждого есть FBX и карты в assets. Предметы без записи в ItemModels показываются заготовкой до импорта — это
   перечисляется как «ожидает импорта», не ошибка.
5. Босс 2 подключён (D42, D43): Battle.Bosses[2] с силой Progression.Bosses[2], BossModels[2], скелет
   Boss2TraderRig в BossService и BossAnimController, площадка MapLayout.Arenas[2], декор FleaMarket в WorldBuilder.
6. Уровень 3 «Подземка» подключён (D54): зона Subway в GameConfig, площадка MapLayout.Arenas[3], декор
   SubwayStation в WorldBuilder.

Запуск: python scripts/check_project.py (код выхода 1 — есть ошибки). Ни от чего не зависит, кроме стандартной
библиотеки Python.
"""

import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORBIDDEN_IDS = {"115188607358965": "«Сотворение Адама»", "91016959329136": "«Рождение Венеры»"}
FORBIDDEN_FILES = ("CreationOfAdam", "BirthOfVenus", "Sistine", "Uffizi")
MOUNTS = {("ReplicatedStorage", "Shared"): "src/shared", ("ServerScriptService", "Server"): "src/server",
          ("StarterPlayer", "StarterPlayerScripts", "Client"): "src/client"}
errors, notes = [], []


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def walk(*dirs):
    for d in dirs:
        for dp, dn, fn in os.walk(os.path.join(ROOT, d)):
            dn[:] = [x for x in dn if x not in ("__pycache__", ".git")]
            for f in fn:
                yield os.path.join(dp, f)


# ── 1. Запрещённый контент ───────────────────────────────────────────────────────────────────────────────────

me = os.path.abspath(__file__)
scan = [os.path.join(ROOT, "default.project.json")] + list(walk("src", "assets", "scripts"))
for p in scan:
    if os.path.abspath(p) == me:
        continue
    name = os.path.basename(p)
    if any(k.lower() in name.lower() for k in FORBIDDEN_FILES):
        errors.append(f"запрещённый файл в активной сборке: {rel(p)}")
    if p.endswith(".md") or not p.endswith((".luau", ".json", ".py", ".txt", ".toml")):
        continue
    text = open(p, encoding="utf-8", errors="ignore").read()
    for fid, what in FORBIDDEN_IDS.items():
        if fid in text:
            errors.append(f"запрещённый ассет {fid} ({what}) в {rel(p)}")
    if "creation_of_adam" in text or "birth_of_venus" in text:
        errors.append(f"генерация исключённой картины в {rel(p)}")

# ── 2. require ───────────────────────────────────────────────────────────────────────────────────────────────


def vpath_of(path):
    r = rel(path)
    for mount, d in MOUNTS.items():
        if r.startswith(d + "/"):
            parts = r[len(d) + 1:].split("/")
            last = re.sub(r"(\.server|\.client)?\.luau$", "", parts[-1])
            return list(mount) + parts[:-1] + ([] if last == "init" else [last])
    return None


def exists(vp):
    for mount, d in MOUNTS.items():
        n = len(mount)
        if tuple(vp[:n]) == mount:
            base = os.path.join(ROOT, d, *vp[n:])
            return vp[n:] == [] or os.path.isdir(base) or any(
                os.path.isfile(base + ext) for ext in (".luau", ".server.luau", ".client.luau", ".model.json"))
    if vp and vp[0] in ("ReplicatedStorage", "ServerScriptService", "StarterPlayer") and len(vp) == 1:
        return True
    return None  # вне проекта Rojo — не проверяется


STEP = re.compile(r'\s*(?:\.(\w+)|:(?:WaitForChild|FindFirstChild)\(\s*"([^"]+)"[^)]*\)|:GetService\(\s*"(\w+)"\s*\))')


def resolve(expr, aliases, own):
    expr = expr.strip()
    m = re.match(r"(\w+)", expr)
    if not m:
        return None
    head, rest = m.group(1), expr[m.end():]
    if head == "script":
        vp = list(own)
    elif head == "game":
        vp = []
    elif head in aliases:
        vp = list(aliases[head])
    else:
        return None
    pos = 0
    while pos < len(rest):
        s = STEP.match(rest, pos)
        if not s:
            return None
        name = s.group(1) or s.group(2) or s.group(3)
        if name == "Parent" and s.group(1):
            if not vp:
                return None
            vp.pop()
        elif s.group(3):
            vp = [name]
        else:
            vp.append(name)
        pos = s.end()
    return vp


def balanced(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
    return None


checked = 0
for p in walk("src"):
    if not p.endswith(".luau"):
        continue
    own = vpath_of(p)
    text = open(p, encoding="utf-8").read()
    text = re.sub(r"--\[(=*)\[.*?\]\1\]", "", text, flags=re.S)  # блочные комментарии
    text = re.sub(r"--[^\n]*", "", text)  # строчные комментарии
    aliases = {}
    for m in re.finditer(r"^\s*local (\w+)\s*=\s*([^\n]+)$", text, re.M):
        vp = resolve(m.group(2).split("--")[0], aliases, own)
        if vp is not None and "require" not in m.group(2):
            aliases[m.group(1)] = vp
    for m in re.finditer(r"\brequire\(", text):
        arg = balanced(text, m.end() - 1)
        if arg is None:
            continue
        vp = resolve(arg, aliases, own)
        if vp is None:
            notes.append(f"require не проверен (динамический): {rel(p)}: {arg.strip()[:60]}")
            continue
        ok = exists(vp)
        checked += 1
        if ok is False:
            errors.append(f"require на несуществующий модуль: {rel(p)} → {'.'.join(vp)}")

# ── 3. Карты и меши предметов ────────────────────────────────────────────────────────────────────────────────

im = open(os.path.join(ROOT, "src/shared/Config/ItemModels.luau"), encoding="utf-8").read()
models = dict((k, (c, n)) for k, c, n in re.findall(r"^\s*(\w+) = model\((\d+), (\d+),", im, re.M))
meshes = dict(re.findall(r"^\s*(\w+) = (\d{9,}),", im.split("local MESHES")[1], re.M)) if "local MESHES" in im else {}
# живые существа (боссы 3–5, D55, D57, D64): FBX — по индексу коллекции, меши частей — CREATURE_MESHES (<id>_<Часть>)
creature_fbx = {}
for _idx in ("assets/models/art/Boss3Creatures.index.json", "assets/models/art/boss4/Boss4Creatures.index.json",
             "assets/models/art/boss5/Boss5Creatures.index.json"):
    if os.path.isfile(os.path.join(ROOT, _idx)):
        for _it in json.load(open(os.path.join(ROOT, _idx), encoding="utf-8"))["items"]:
            creature_fbx[_it["id"]] = _it["fbx"]
_cm = im.split("local CREATURE_MESHES")[1].split("\n}")[0] if "local CREATURE_MESHES" in im else ""
creature_meshed = {k.split("_")[0] for k, _id in re.findall(r"^\s*(\w+?_\w+) = (\d{9,}),", _cm, re.M)}
creatures_waiting = []
for item, (color, normal) in models.items():
    look = os.path.join(ROOT, "src/server/Looks", f"{item}.model.json")
    if not os.path.isfile(look):
        errors.append(f"нет шаблона Looks/{item}.model.json")
    else:
        t = open(look, encoding="utf-8").read()
        if color not in t or normal not in t:
            errors.append(f"Looks/{item}: карты не совпадают с ItemModels")
    if item in creature_fbx:  # существо: свой FBX частей; меши — после импорта (до него — Part-версия)
        if not os.path.isfile(os.path.join(ROOT, creature_fbx[item])):
            errors.append(f"{item}: нет исходника {creature_fbx[item]}")
        if item not in creature_meshed:
            creatures_waiting.append(item)
        continue
    if item not in meshes:
        errors.append(f"{item}: нет MeshId в ItemModels")
    if not os.path.isfile(os.path.join(ROOT, "assets/models/art", f"{item}.fbx")):
        errors.append(f"{item}: нет исходника assets/models/art/{item}.fbx")

bm = open(os.path.join(ROOT, "src/shared/Config/BossModels.luau"), encoding="utf-8").read()
for boss, body in re.findall(r"^\t\[(\d+)\] = \{(.*?)^\t\} :: BossModel", bm, re.M | re.S):
    # карта группы — в одну строку или в несколько; кроме color и normal бывают metal, rough, glow (босс 10)
    for group, entry in re.findall(r"(\w+) = \{([^{}]*\bcolor = [^{}]*)\}", body):
        fields = dict(re.findall(r'(\w+) = "rbxassetid://(\d+)"', entry))
        look = os.path.join(ROOT, "src/server/Looks", f"Boss{boss}_{group}.model.json")
        if not os.path.isfile(look):
            errors.append(f"нет шаблона Looks/Boss{boss}_{group}.model.json")
        elif any(v not in open(look, encoding="utf-8").read() for v in fields.values()):
            errors.append(f"Looks/Boss{boss}_{group}: карты не совпадают с BossModels")

# ── 4. Коллекция босса 2 ─────────────────────────────────────────────────────────────────────────────────────

items_src = open(os.path.join(ROOT, "src/shared/Config/Items.luau"), encoding="utf-8").read()
declared = re.findall(r'^\s*(\w+)\(\s*"([A-Z]\w+)",', items_src, re.M)  # (функция, id): art(…), wonder(…), find(…)
seen = {}
for fn, i in declared:
    if i in seen:
        errors.append(f"id «{i}» объявлен в Config/Items дважды")
    seen[i] = fn
catalog = open(os.path.join(ROOT, "docs/CATALOG.md"), encoding="utf-8").read()
boss2 = catalog.split("## Босс 2")[1].split("\n## ")[0] if "## Босс 2" in catalog else ""
rows = re.findall(r"^\| (\d+) \| (\w+) \| ([^|]+) \| ([^|]+) \|", boss2, re.M)
boss2_ids = [r[3].strip() for r in rows if r[3].strip() not in ("—", "id")]
excluded = [r[2].strip() for r in rows if r[3].strip() == "—"]
if len(boss2_ids) != 30:
    errors.append(f"в каталоге босса 2 {len(boss2_ids)} предметов, нужно 30")
waiting = []
for i in boss2_ids:
    if seen.get(i) != "find":
        errors.append(f"босс 2: «{i}» не подключён в Config/Items (find)")
    for path in (f"assets/models/art/{i}.fbx", f"assets/textures/art/{i}_color.png", f"assets/textures/art/{i}_normal.png"):
        if not os.path.isfile(os.path.join(ROOT, path)):
            errors.append(f"босс 2: нет {path}")
    if i not in models:
        waiting.append(i)
extra = sorted(i for i, fn in seen.items() if fn == "find" and i not in boss2_ids)
if extra:
    errors.append("в Config/Items у босса 2 лишние предметы: " + ", ".join(extra))
if waiting:
    notes.append(f"ожидают импорта мешей и карт (показываются заготовкой): {len(waiting)} предметов босса 2")
if creatures_waiting:
    notes.append(f"карты есть, меши частей ждут импорта (показываются Part-версией): {len(creatures_waiting)} существ")

# ── 5. Подключение босса 2 ───────────────────────────────────────────────────────────────────────────────────


def src(path):
    return open(os.path.join(ROOT, path), encoding="utf-8").read()


battle, progression = src("src/shared/Config/Battle.luau"), src("src/shared/Config/Progression.luau")
strength = re.search(r"\[2\] = \{[^}]*?Strength = (\d+)", battle)
bosses = re.search(r"Bosses = \{([^}]*)\}", progression)
want = bosses.group(1).split(",")[1].strip() if bosses else None
if not strength or strength.group(1) != want:
    errors.append(f"Battle.Bosses[2].Strength ({strength and strength.group(1)}) ≠ Progression.Bosses[2] ({want})")
if "[2] = {" not in bm or "Торговец-громила" not in bm:
    errors.append("нет BossModels[2] «Торговец-громила»")
for path in ("src/server/Services/BossService.luau", "src/client/Controllers/BossAnimController.luau"):
    if not re.search(r"\[2\] = Boss2TraderRig", src(path)):
        errors.append(f"{path}: скелет босса 2 не подключён")
if not re.search(r"\[2\] = \{\s*top = ", src("src/server/World/MapLayout.luau")):
    errors.append("нет площадки босса 2 (MapLayout.Arenas[2])")
if not re.search(r"\[1\] = \{\s*top = ", src("src/server/World/MapLayout.luau")):
    errors.append("нет площадки пса (MapLayout.Arenas[1], D68)")
if "decor, signs = Junkyard.Zone()" not in src("src/server/World/WorldBuilder.luau"):
    errors.append("декор и надписи «Свалки» (Junkyard) не подключены в WorldBuilder")
if "FleaMarket.Zone()" not in src("src/server/World/WorldBuilder.luau"):
    errors.append("декор «Барахолки» (FleaMarket) не подключён в WorldBuilder")
if not re.search(r'id = "Subway", name = "Подземка", boss = "Крысиный король"', src("src/shared/Config/GameConfig.luau")):
    errors.append("нет зоны 3 «Подземка» с боссом «Крысиный король» (GameConfig.Zones)")
if not re.search(r"\[3\] = \{\s*top = ", src("src/server/World/MapLayout.luau")):
    errors.append("нет площадки босса 3 (MapLayout.Arenas[3])")
if "SubwayStation.Zone()" not in src("src/server/World/WorldBuilder.luau"):
    errors.append("декор «Подземки» (SubwayStation) не подключён в WorldBuilder")
# Босс 4 «Сфинкс-лежебока» (интеграция 2026-11-12): скелет с клипами, сила D56; с коллекцией (D57–D59) открыт
strength4 = re.search(r"\[4\] = \{[^}]*?Strength = (\d+)", battle)
want4 = bosses.group(1).split(",")[3].strip() if bosses else None
if not strength4 or strength4.group(1) != want4:
    errors.append(f"Battle.Bosses[4].Strength ({strength4 and strength4.group(1)}) ≠ Progression.Bosses[4] ({want4})")
_boss4_items = len(re.findall(r'^creature4\("', src("src/shared/Config/Items.luau"), re.M))
_closed4 = re.search(r"\[4\] = \{[^}]*?Closed = true", battle) is not None
if _boss4_items == 30 and _closed4:
    errors.append("босс 4 закрыт, хотя коллекция из 30 существ есть (D59)")
if _boss4_items != 30 and not _closed4:
    errors.append(f"босс 4 открыт, а существ в коллекции {_boss4_items} (нужно 30, D57)")
for path in ("src/server/Services/BossService.luau", "src/client/Controllers/BossAnimController.luau"):
    if not re.search(r"\[4\] = Boss4SphinxRig", src(path)):
        errors.append(f"{path}: скелет босса 4 не подключён")
if "Clips = require(script.Parent.Boss4SphinxClips)" not in src("src/shared/Config/Boss4SphinxRig.luau"):
    errors.append("у скелета босса 4 нет клипов (Config/Boss4SphinxClips)")
for clip in ("SleepIdle", "Wake", "CombatIdle", "Walk", "HeavyPaw", "TailStrike", "Hit", "Victory", "Defeat", "FallAsleep"):
    path = f"src/shared/Config/Boss4SphinxClips/{clip}.luau"
    if not os.path.exists(os.path.join(ROOT, path)):
        errors.append(f"нет клипа {path}")
    elif os.path.getsize(os.path.join(ROOT, path)) > 200_000:
        errors.append(f"{path}: больше 200 000 знаков")
# Босс 5 «Йети-коллекционер» (подключение 2026-11-24, D64): коллекция из 30 существ, но закрыт до общего выпуска
# боссов 5–10 (D64 п. 7); сила D56; удар до контура тела; скелет и 10 клипов из Blender; арена «Ледник»
strength5 = re.search(r"\[5\] = \{[^}]*?Strength = (\d+)", battle)
want5 = bosses.group(1).split(",")[4].strip() if bosses else None
if not strength5 or strength5.group(1) != want5:
    errors.append(f"Battle.Bosses[5].Strength ({strength5 and strength5.group(1)}) ≠ Progression.Bosses[5] ({want5})")
_b5 = re.search(r"\[5\] = \{([^}]*)\}", battle)
for field in ("Closed = true", "BodyRange = true"):
    if not _b5 or field not in _b5.group(1):
        errors.append(f"Battle.Bosses[5]: нет {field} (D64)")
_boss5_items = len(re.findall(r'^creature5\("', src("src/shared/Config/Items.luau"), re.M))
if _boss5_items != 30:
    errors.append(f"в коллекции босса 5 {_boss5_items} существ (нужно 30, D64)")
for path in ("src/server/Services/BossService.luau", "src/client/Controllers/BossAnimController.luau"):
    if not re.search(r"\[5\] = Boss5YetiRig", src(path)):
        errors.append(f"{path}: скелет босса 5 не подключён")
if "Clips = require(script.Parent.Boss5YetiClips)" not in src("src/shared/Config/Boss5YetiRig.luau"):
    errors.append("у скелета босса 5 нет клипов (Config/Boss5YetiClips)")
for clip in ("SleepIdle", "Wake", "CombatIdle", "Walk", "Smash", "IceClap", "Hit", "Victory", "Defeat", "FallAsleep"):
    path = f"src/shared/Config/Boss5YetiClips/{clip}.luau"
    if not os.path.exists(os.path.join(ROOT, path)):
        errors.append(f"нет клипа {path}")
    elif os.path.getsize(os.path.join(ROOT, path)) > 200_000:
        errors.append(f"{path}: больше 200 000 знаков")
if "[5] = {" not in bm or "Йети-коллекционер" not in bm or "ids(YETI_MESHES)" not in bm:
    errors.append("нет BossModels[5] «Йети-коллекционер» с мешами частей")
_yeti = bm.split("local YETI_MESHES")[1].split("\n}")[0] if "local YETI_MESHES" in bm else ""
if len(re.findall(r"= \d{9,},", _yeti)) != 31:
    errors.append("BossModels: у Йети не 31 меш частей (YETI_MESHES)")
if not re.search(r"\[5\] = \{\s*floor = ", src("src/server/World/MapLayout.luau")):
    errors.append("нет площадки босса 5 (MapLayout.Arenas[5])")
if "GlacierHall.Zone()" not in src("src/server/World/WorldBuilder.luau"):
    errors.append("арена «Ледник» (GlacierHall) не подключена в WorldBuilder")
if not re.search(r'id = "Glacier", name = "Ледник", boss = "Йети-коллекционер"', src("src/shared/Config/GameConfig.luau")):
    errors.append("нет зоны 5 «Ледник» с боссом «Йети-коллекционер» (GameConfig.Zones)")
# Босс 10 «Король-дракон» (этап B интеграции, 2026-11-15): закрыт до коллекции и импорта модели; сила D56; свои
# правила боя только у него (дальность до тела, без погони, залп); скелет и 15 клипов из Blender
battle10 = re.search(r"\[10\] = \{(.*?)\n\t\t\},\n\t\},", battle, re.S)
b10 = battle10.group(1) if battle10 else ""
strength10 = re.search(r"Strength = (\d+)", b10)
want10 = bosses.group(1).split(",")[9].strip() if bosses else None
if not strength10 or strength10.group(1) != want10:
    errors.append(f"Battle.Bosses[10].Strength ({strength10 and strength10.group(1)}) ≠ Progression.Bosses[10] ({want10})")
for field, rx in (("Closed = true", r"Closed = true"), ("BodyRange = true", r"BodyRange = true"),
                  ("Leash = 0", r"Leash = 0,"), ("Volley", r"Volley = \{"), ("HP = 140", r"HP = 140,"),
                  ("Damage = 8", r"Damage = 8,"), ("AttackInterval = 1.4", r"AttackInterval = 1\.4,")):
    if not re.search(rx, b10):
        errors.append(f"Battle.Bosses[10]: нет {field}")
for path in ("src/server/Services/BossService.luau", "src/client/Controllers/BossAnimController.luau"):
    if not re.search(r"\[10\] = Boss10DragonRig", src(path)):
        errors.append(f"{path}: скелет босса 10 не подключён")
if "Clips = require(script.Parent.Boss10DragonClips)" not in src("src/shared/Config/Boss10DragonRig.luau"):
    errors.append("у скелета босса 10 нет клипов (Config/Boss10DragonClips)")
for clip in ("SleepIdle", "Wake", "CombatIdle", "Walk", "ClawSwipe", "Bite", "TailStrike", "WingBuffet", "MagicVolley",
             "Hit", "Victory", "Defeat", "FallAsleep", "TurnStepLeft", "TurnStepRight"):
    path = f"src/shared/Config/Boss10DragonClips/{clip}.luau"
    if not os.path.exists(os.path.join(ROOT, path)):
        errors.append(f"нет клипа {path}")
    elif os.path.getsize(os.path.join(ROOT, path)) > 200_000 * 2:  # кириллица в комментариях — 2 байта на знак
        errors.append(f"{path}: слишком большой модуль")
# этап C (2026-11-15): меши всех 52 частей, Body_2, глаз и перепонок; 6 групп карт с шаблонами Looks; кости перепонок
models_src = src("src/shared/Config/BossModels.luau")
dragon = re.search(r"local DRAGON_MESHES: \{ \[string\]: number \} = \{(.*?)\n\}", models_src, re.S)
rig10 = src("src/shared/Config/Boss10DragonRig.luau")
if dragon:
    have = set(re.findall(r"(\w+) = \d+,", dragon.group(1)))
    order10 = re.findall(r'"(\w+)"', re.search(r"Order = \{(.*?)\}", rig10).group(1))
    need = set(order10) | {"Body_2", "EyeL", "EyeR", "WingMembranes"}
    if need - have:
        errors.append(f"босс 10: нет мешей {sorted(need - have)}")
    entry10 = re.search(r"\t\[10\] = \{(.*?)\n\t\} :: BossModel,", models_src, re.S)
    groups10 = re.findall(r"(\w+) = \{\s*color = ", entry10.group(1)) if entry10 else []
    for g in ("BodyA", "BodyB", "Head", "Front", "Hind", "Tail"):
        if g not in groups10:
            errors.append(f"босс 10: нет карт группы {g}")
        elif not os.path.exists(os.path.join(ROOT, f"src/server/Looks/Boss10_{g}.model.json")):
            errors.append(f"босс 10: нет шаблона Looks/Boss10_{g} (python scripts/make_looks.py)")
    if "MembraneMesh = {" not in rig10 or "WingArmL = { parent" not in rig10:
        errors.append("босс 10: у скелета нет перепонок с костями (python scripts/boss10_to_luau.py)")
    notes.append(f"босс 10: мешей {len(have)} (части, Body_2, глаза, перепонки), групп карт {len(groups10)}")
elif re.search(r"\[10\] = \{[^}]*?meshes = \{\s*\w", models_src):
    notes.append("у босса 10 есть меши — этап C начат (нужно разрешение владельца)")
for ctl in ("BossVolleyController", "PlayerSwingController"):
    if f'WaitForChild("{ctl}")' not in src("src/client/Main.client.luau"):
        errors.append(f"контроллер {ctl} не запущен в Main.client.luau")

# ── Тестовый режим владельца (решение владельца 2026-11-16): изоляция ─────────────────────────────────────────
# Резервные серверы создаёт только OwnerTestService (по ним Util/OwnerTest узнаёт тестовый сервер), тестовый сервер
# пускает только владельца и грузит профиль в памяти, закрытые боссы — Studio или тестовый сервер.
for p in walk("src"):
    if not p.endswith(".luau"):
        continue
    text = open(p, encoding="utf-8", errors="ignore").read()
    if re.search(r"ReserveServer|ShouldReserveServer|ReservedServerAccessCode", text) and not p.endswith(
        "OwnerTestService.luau"
    ):
        errors.append(f"резервный сервер создаётся не тестовым режимом владельца: {rel(p)}")
main_src = src("src/server/Main.server.luau")
if not re.search(r"IsTestServer\(\) then\s+if not OwnerTest\.IsOwner\(player\) then\s+player:Kick", main_src):
    errors.append("Main: тестовый сервер владельца не выгоняет чужих игроков")
if "PlayerSession.Join(player, { mock = true, veteran = true })" not in main_src:
    errors.append("Main: на тестовом сервере владельца профиль не в памяти")
if "(RunService:IsStudio() and GameConfig.DevMode == true) or OwnerTest.IsTestServer()" not in src(
    "src/server/Services/BossService.luau"
):
    errors.append("BossService.ClosedAllowed: закрытые боссы не только в Studio и на тестовом сервере")
owner_cfg = re.search(r"GameConfig\.OwnerTest = \{(.*?)\n\}", src("src/shared/Config/GameConfig.luau"), re.S)
if not owner_cfg or "UniverseId = 10776417796" not in owner_cfg.group(1) or "PlaceId = 81392528393796" not in owner_cfg.group(1):
    errors.append("GameConfig.OwnerTest: не подтверждённое DEV-место (10776417796 / 81392528393796)")
else:
    on = re.search(r"Enabled = (true|false)", owner_cfg.group(1))
    notes.append(f"тестовый режим владельца: {'включён' if on and on.group(1) == 'true' else 'выключен'} (DEV-место)")

print(f"require проверено: {checked}; предметов с моделями (ItemModels): {len(models)}; коллекция босса 2: "
      f"{len(boss2_ids)} в игре, исключено из каталога {len(excluded)}")
for n in notes:
    print("· " + n)
for e in errors:
    print("ОШИБКА: " + e)
print("ИТОГ: " + ("ошибок нет" if not errors else f"ошибок {len(errors)}"))
sys.exit(1 if errors else 0)
