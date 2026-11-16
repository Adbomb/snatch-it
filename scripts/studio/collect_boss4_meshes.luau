-- Сборщик MeshId босса 4 после ручного импорта двух FBX (File → Import 3D): Boss4Creatures_all.fbx — 30 существ,
-- части Art_<id>_<Часть>; Boss4_Sphinx_game.fbx — 27 частей Boss4_Sphinx{Body,Head,Limbs}_<Часть>.
-- Запуск: Studio в Edit, MCP execute_luau с текстом этого файла (или Command Bar). Ищет MeshPart в Workspace,
-- ServerStorage и ReplicatedStorage, сверяет имена со скелетами и печатает блок для
-- scripts/boss4_bind_after_import.py: строки «имя|MeshId|размер X,Y,Z|метки». Метки: S — у меша свой
-- SurfaceAppearance, T — задан TextureID (игра их не берёт: карты D39 — из Server/Looks), D — имя встретилось
-- не один раз (импорт повторён). Отдельно — что ещё пришло с импортом (кости, анимации, Humanoid): скелеты и клипы
-- босса 4 собираются кодом (Motor6D, Config/CreatureRigs, Config/Boss4SphinxClips), из FBX они не нужны.
-- ONLY = "creatures" | "sphinx" — печатать только эту половину (если вывод MCP обрезается). Место не меняет.
-- Зависит от Config/Items, Config/CreatureRigs, Config/Boss4SphinxRig.

local ONLY: string? = nil

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Config = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config")
local Items = require(Config.Items) :: any
local CreatureRigs = require(Config.CreatureRigs) :: any
local SphinxRig = require(Config.Boss4SphinxRig) :: any

-- ожидаемые имена объектов импорта → «c» (существо) или «s» (Сфинкс)
local expected: { [string]: string } = {}
local nCreatures, nSphinx, nKinds = 0, 0, 0
for id, def in Items do
	if def.boss == 4 and not def.legacy and CreatureRigs[id] then
		nKinds += 1
		for part, spec in CreatureRigs[id].Parts do
			if not spec.hidden then
				expected[("Art_%s_%s"):format(id, part)] = "c"
				nCreatures += 1
			end
		end
	end
end
for _, part in SphinxRig.Order do
	expected[("Boss4_Sphinx%s_%s"):format(SphinxRig.Parts[part].map, part)] = "s"
	nSphinx += 1
end

local found: { [string]: { MeshPart } } = {}
local roots: { [Instance]: boolean } = {}
local extra: { string } = {}
for _, service in { workspace, ServerStorage, ReplicatedStorage } do
	for _, d in service:GetDescendants() do
		if d:IsA("MeshPart") then
			if expected[d.Name] then
				found[d.Name] = found[d.Name] or {}
				table.insert(found[d.Name], d)
				local root = d:FindFirstAncestorOfClass("Model") or d.Parent
				if root then
					roots[root] = true
				end
			elseif
				d.Name:match("^Boss4_Sphinx") or (d.Name:match("^Art_%w+_%w+$") and not d.Name:match("^Art_Boss"))
			then
				local id = d.Name:match("^Art_(%w+)_")
				if not id or (Items[id] and Items[id].boss == 4) then
					table.insert(extra, d:GetFullName())
				end
			end
		end
	end
end

local missing: { string } = {}
local lines: { string } = {}
local dup = 0
for name, kind in expected do
	local list = found[name]
	if not list then
		table.insert(missing, name)
		continue
	end
	if ONLY == "creatures" and kind ~= "c" or ONLY == "sphinx" and kind ~= "s" then
		continue
	end
	dup += if #list > 1 then 1 else 0
	for _, m in list do
		local flags = (if m:FindFirstChildOfClass("SurfaceAppearance") then "S" else "")
			.. (if m.TextureID ~= "" then "T" else "")
			.. (if #list > 1 then "D" else "")
		local s = m.Size
		table.insert(
			lines,
			("%s|%s|%.4f,%.4f,%.4f|%s"):format(name, string.match(m.MeshId, "%d+$") or "", s.X, s.Y, s.Z, flags)
		)
	end
end
table.sort(lines)
table.sort(missing)

-- что ещё пришло с импортом: кости, анимации, гуманоиды и прочие не-MeshPart
local others: { [string]: number } = {}
local rootNames: { string } = {}
for root in roots do
	table.insert(rootNames, root:GetFullName())
	for _, d in root:GetDescendants() do
		if not d:IsA("MeshPart") then
			others[d.ClassName] = (others[d.ClassName] or 0) + 1
		end
	end
end
local otherList: { string } = {}
for class, n in others do
	table.insert(otherList, ("%s=%d"):format(class, n))
end
table.sort(otherList)
table.sort(rootNames)

local out = {
	"BOSS4_IMPORT v1",
	("ожидается: существ %d (частей %d), Сфинкс %d частей"):format(
		nKinds,
		nCreatures,
		nSphinx
	),
	("найдено имён: %d из %d; повторов: %d"):format(
		nCreatures + nSphinx - #missing,
		nCreatures + nSphinx,
		dup
	),
	"корни импорта: " .. (if #rootNames > 0 then table.concat(rootNames, ", ") else "нет"),
	"кроме MeshPart в импорте: "
		.. (if #otherList > 0 then table.concat(otherList, ", ") else "ничего"),
	"нет: " .. (if #missing > 0 then table.concat(missing, ", ") else "—"),
	"лишние (имя похоже, но не из скелета): "
		.. (if #extra > 0 then table.concat(extra, ", ") else "—"),
	"BEGIN",
}
for _, line in lines do
	table.insert(out, line)
end
table.insert(out, "END")
print(table.concat(out, "\n"))
