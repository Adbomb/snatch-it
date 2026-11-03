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

Запуск: python scripts/check_project.py (код выхода 1 — есть ошибки). Ни от чего не зависит, кроме стандартной
библиотеки Python.
"""

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
for item, (color, normal) in models.items():
    look = os.path.join(ROOT, "src/server/Looks", f"{item}.model.json")
    if not os.path.isfile(look):
        errors.append(f"нет шаблона Looks/{item}.model.json")
    else:
        t = open(look, encoding="utf-8").read()
        if color not in t or normal not in t:
            errors.append(f"Looks/{item}: карты не совпадают с ItemModels")
    if item not in meshes:
        errors.append(f"{item}: нет MeshId в ItemModels")
    if not os.path.isfile(os.path.join(ROOT, "assets/models/art", f"{item}.fbx")):
        errors.append(f"{item}: нет исходника assets/models/art/{item}.fbx")

bm = open(os.path.join(ROOT, "src/shared/Config/BossModels.luau"), encoding="utf-8").read()
for boss, body in re.findall(r"^\t\[(\d+)\] = \{(.*?)^\t\} :: BossModel", bm, re.M | re.S):
    for group, color, normal in re.findall(r'(\w+) = \{ color = "rbxassetid://(\d+)", normal = "rbxassetid://(\d+)" \}', body):
        look = os.path.join(ROOT, "src/server/Looks", f"Boss{boss}_{group}.model.json")
        if not os.path.isfile(look):
            errors.append(f"нет шаблона Looks/Boss{boss}_{group}.model.json")
        elif color not in open(look, encoding="utf-8").read() or normal not in open(look, encoding="utf-8").read():
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
if not re.search(r"Arenas = \{\s*\[2\] = \{", src("src/server/World/MapLayout.luau")):
    errors.append("нет площадки босса 2 (MapLayout.Arenas[2])")
if "FleaMarket.Zone()" not in src("src/server/World/WorldBuilder.luau"):
    errors.append("декор «Барахолки» (FleaMarket) не подключён в WorldBuilder")

print(f"require проверено: {checked}; предметов с моделями (ItemModels): {len(models)}; коллекция босса 2: "
      f"{len(boss2_ids)} в игре, исключено из каталога {len(excluded)}")
for n in notes:
    print("· " + n)
for e in errors:
    print("ОШИБКА: " + e)
print("ИТОГ: " + ("ошибок нет" if not errors else f"ошибок {len(errors)}"))
sys.exit(1 if errors else 0)
