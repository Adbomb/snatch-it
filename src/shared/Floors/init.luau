--!strict
-- Темы этажей музея-небоскрёба (этапы B–C): ItemID → модуль темы с одной таблицей функций (shell — серверный каркас,
-- exhibit — место и масштаб показа экспоната, decor — убранство клиента по уровням детализации). Эталоны этапа C —
-- GoldenThrone, TRexSkeleton, SpaceHelmet; первая партия новых — Colosseum, MagicMushroom, GoldenMic (Floors/MeshTheme),
-- вторая — ещё десять тем (Moai … WorldInBottle) на том же конвейере;
-- у остальных предметов — временный этаж Placeholder. Новые темы
-- добавляются в THEMES без изменения сервисов. Общие детали тем — Floors/Kit.
-- Здесь же холл (нулевой этаж: вход, сундук участка, лифт) и крыша — общие для всех башен.
-- Координаты — оси этажа: центр башни на уровне пола, вход в −Z (GameConfig.Tower).
-- Зависит от Floors/FloorBuilder, Floors/Kit, Floors/Placeholder, Floors/<темы>.

local FloorBuilder = require(script.FloorBuilder)
local Placeholder = require(script.Placeholder)

local Brick = FloorBuilder.Brick

local Floors = {}

Floors.FloorBuilder = FloorBuilder
Floors.Placeholder = Placeholder

Floors.Kit = require(script.Kit)

local THEMES: { [string]: any } = {
	GoldenThrone = require(script.GoldenThrone),
	TRexSkeleton = require(script.TRexSkeleton),
	SpaceHelmet = require(script.SpaceHelmet),
	-- первая партия новых этажей (2026-11-21): общий конвейер Floors/MeshTheme
	Colosseum = require(script.Colosseum),
	MagicMushroom = require(script.MagicMushroom),
	GoldenMic = require(script.GoldenMic),
	-- вторая партия (2026-11-21): тот же конвейер
	Moai = require(script.Moai),
	TutMask = require(script.TutMask),
	TerracottaWarrior = require(script.TerracottaWarrior),
	StatueOfLiberty = require(script.StatueOfLiberty),
	GoldenGamepad = require(script.GoldenGamepad),
	UfoJar = require(script.UfoJar),
	GoldenBanana = require(script.GoldenBanana),
	CrystalDino = require(script.CrystalDino),
	TrophyBurger = require(script.TrophyBurger),
	WorldInBottle = require(script.WorldInBottle),
	-- третья партия (2026-11-21): тот же конвейер
	MiniStonehenge = require(script.MiniStonehenge),
	PocketDragon = require(script.PocketDragon),
	CursedTV = require(script.CursedTV),
	NeonHeart = require(script.NeonHeart),
	RoboDuck = require(script.RoboDuck),
	PrizeMachine = require(script.PrizeMachine),
	ChaosCrown = require(script.ChaosCrown),
	PocketSafe = require(script.PocketSafe),
	RoyalDuck = require(script.RoyalDuck),
	MonsterFlower = require(script.MonsterFlower),
	-- четвёртая партия (2026-11-22): тот же конвейер
	GizaPyramids = require(script.GizaPyramids),
	AstroCat = require(script.AstroCat),
	LivingCassette = require(script.LivingCassette),
	MagicSoda = require(script.MagicSoda),
	MonsterRadio = require(script.MonsterRadio),
	MimicChest = require(script.MimicChest),
	PortalMirror = require(script.PortalMirror),
	BlackCatIdol = require(script.BlackCatIdol),
	CrystalHotDog = require(script.CrystalHotDog),
	Sunflowers = require(script.Sunflowers),
	-- пятая партия (2026-11-22): тот же конвейер
	CheeseSkater = require(script.CheeseSkater),
	BuffRat = require(script.BuffRat),
	SneakerTenant = require(script.SneakerTenant),
	SubwaySnail = require(script.SubwaySnail),
	AngryAlarmClock = require(script.AngryAlarmClock),
	PanicCone = require(script.PanicCone),
	SubwayOctopus = require(script.SubwayOctopus),
	CactusBoxer = require(script.CactusBoxer),
	IslandTurtle = require(script.IslandTurtle),
	LiveCheeseMonster = require(script.LiveCheeseMonster),
	-- шестая партия (2026-11-22): тот же конвейер
	PizzaRat = require(script.PizzaRat),
	RunawayTicket = require(script.RunawayTicket),
	RatKnight = require(script.RatKnight),
	MutantSoda = require(script.MutantSoda),
	WalkingSuitcase = require(script.WalkingSuitcase),
	DevourerVending = require(script.DevourerVending),
	TrashGobbler = require(script.TrashGobbler),
	RoyalRatTrain = require(script.RoyalRatTrain),
	GoldenRatMech = require(script.GoldenRatMech),
	RubyThief = require(script.RubyThief),
	-- седьмая партия (2026-11-22): тот же конвейер
	DuckInspector = require(script.DuckInspector),
	RatWizard = require(script.RatWizard),
	ThreeHeadedRat = require(script.ThreeHeadedRat),
	TurnstileTerminator = require(script.TurnstileTerminator),
	ThreeTailEmperor = require(script.ThreeTailEmperor),
	CobraFountain = require(script.CobraFountain),
	BlazeOstrich = require(script.BlazeOstrich),
	CloudCamel = require(script.CloudCamel),
	DrillWorm = require(script.DrillWorm),
	DustDevil = require(script.DustDevil),
	-- восьмая партия (2026-11-22): тот же конвейер
	FanVulture = require(script.FanVulture),
	MeerkatLookout = require(script.MeerkatLookout),
	FennecRiddler = require(script.FennecRiddler),
	SpringAntelope = require(script.SpringAntelope),
	KaleidoChameleon = require(script.KaleidoChameleon),
	PuzzlePhoenix = require(script.PuzzlePhoenix),
	StrawSnake = require(script.StrawSnake),
	SandChick = require(script.SandChick),
	MonsterTrain = require(script.MonsterTrain),
	RatMimic = require(script.RatMimic),
	-- девятая партия (2026-11-22): тот же конвейер, общий каркас scripts/blender/floorshell.py
	FloppyFennec = require(script.FloppyFennec),
	TumbleweedRunner = require(script.TumbleweedRunner),
	CanteenCamel = require(script.CanteenCamel),
	DuneTurtle = require(script.DuneTurtle),
	UmbrellaLizard = require(script.UmbrellaLizard),
	MelonArmadillo = require(script.MelonArmadillo),
	DropBeetle = require(script.DropBeetle),
	CanScorpion = require(script.CanScorpion),
	AquariumCamel = require(script.AquariumCamel),
	CactusAcrobats = require(script.CactusAcrobats),
	-- десятая партия (2026-11-22): тот же конвейер и каркас floorshell.py
	MirageFish = require(script.MirageFish),
	DuneWhale = require(script.DuneWhale),
	CrystalScorpion = require(script.CrystalScorpion),
	GiantCactus = require(script.GiantCactus),
	TornadoKing = require(script.TornadoKing),
	PizzaUfo = require(script.PizzaUfo),
	RatThrone = require(script.RatThrone),
	CheeseDragon = require(script.CheeseDragon),
	ClockGolem = require(script.ClockGolem),
	CheeseVaultHeart = require(script.CheeseVaultHeart),
	-- одиннадцатая партия (2026-11-22): тот же конвейер и каркас floorshell.py
	EgyptianCat = require(script.EgyptianCat),
	AnubisStatue = require(script.AnubisStatue),
	TriceratopsSkull = require(script.TriceratopsSkull),
	EgyptianSarcophagus = require(script.EgyptianSarcophagus),
	GladiatorHelmet = require(script.GladiatorHelmet),
	GreatSphinx = require(script.GreatSphinx),
	NefertitiBust = require(script.NefertitiBust),
	AllSeeingEye = require(script.AllSeeingEye),
}

-- Все темы (проверки Lune, замеры).
function Floors.Themes(): { [string]: any }
	return THEMES
end

-- Тема этажа предмета itemId (нет своей — временный этаж).
function Floors.Get(itemId: string?): any
	return if itemId and THEMES[itemId] then THEMES[itemId] else Placeholder
end

function Floors.HasTheme(itemId: string): boolean
	return THEMES[itemId] ~= nil
end

-- Место главного экспоната темы в осях этажа: центр верха его подставки и поворот лица (−Z модели) на yaw градусов;
-- scale — масштаб показа (только вид и хитбокс этажа: сам предмет и его размер в игре не меняются).
-- У темы — exhibit(cfg) → { at: Vector3, yaw: number, scale: number? }; у временного этажа — тумба cfg.Exhibit.
-- Хитбокс сервера и копия модели у клиента стоят на этом месте (низ предмета — на верхе подставки).
function Floors.ExhibitAt(theme: any, cfg: any): (CFrame, number)
	local spec = if theme and theme.exhibit then theme.exhibit(cfg) else nil
	if not spec then
		local c = cfg.Exhibit.Center
		spec = { at = Vector3.new(c.X, cfg.Exhibit.Plinth.Y, c.Z), yaw = cfg.Exhibit.Yaw or 0 }
	end
	return CFrame.new(spec.at) * CFrame.Angles(0, math.rad(spec.yaw or 0), 0), spec.scale or 1
end

local WALL = Color3.fromHex("F3EFE6")
local TRIM = Color3.fromHex("E0D9CA")
local DARK = Color3.fromHex("3B3F47")
local WORK = Color3.fromHex("F2C230")

-- Холл: вход шириной Door.X и высотой Door.Y в передней стене, ступень с травы на пол музея.
local function lobbyDims(cfg: any)
	return cfg.Half.X, cfg.Half.Y, cfg.Wall, cfg.FloorHeight - cfg.Slab, cfg.Lobby.Door, cfg.Lobby.Step
end

Floors.Lobby = {}

function Floors.Lobby.shell(cfg: any): { FloorBuilder.Brick }
	local hx, hz, t, h, door, step = lobbyDims(cfg)
	local slab = cfg.Slab
	local side = hx - door.X / 2
	local any = DARK
	return {
		Brick(Vector3.new(hx * 2, slab, hz * 2), Vector3.new(0, -slab / 2, 0), any, { name = "Slab" }),
		Brick(Vector3.new(hx * 2, h, t), Vector3.new(0, h / 2, hz - t / 2), any, { name = "WallBack" }),
		Brick(Vector3.new(t, h, hz * 2 - t * 2), Vector3.new(-hx + t / 2, h / 2, 0), any, { name = "WallLeft" }),
		Brick(Vector3.new(t, h, hz * 2 - t * 2), Vector3.new(hx - t / 2, h / 2, 0), any, { name = "WallRight" }),
		Brick(Vector3.new(side, h, t), Vector3.new(-hx + side / 2, h / 2, -hz + t / 2), any, { name = "FrontLeft" }),
		Brick(Vector3.new(side, h, t), Vector3.new(hx - side / 2, h / 2, -hz + t / 2), any, { name = "FrontRight" }),
		Brick(
			Vector3.new(door.X, h - door.Y, t),
			Vector3.new(0, (door.Y + h) / 2, -hz + t / 2),
			any,
			{ name = "Lintel" }
		),
		Brick(
			Vector3.new(door.X + 2, step.Y, step.X),
			Vector3.new(0, -step.Y / 2 - (cfg.Lobby.Rise - step.Y), -hz - step.X / 2),
			any,
			{ name = "Step" }
		),
	}
end

-- tier: "facade" (стены, вход, ступень), "interior" (только то, что внутри — добавляется к фасаду, как у этажей),
-- "silhouette".
function Floors.Lobby.decor(cfg: any, ctx: any, tier: string): { FloorBuilder.Brick }
	local hx, hz, t, h, door, step = lobbyDims(cfg)
	local slab = cfg.Slab
	local side = hx - door.X / 2
	local accent = if ctx and ctx.accent then ctx.accent else WORK
	local bricks: { FloorBuilder.Brick } = {}
	if tier == "silhouette" then
		table.insert(bricks, Brick(Vector3.new(hx * 2, h + slab, hz * 2), Vector3.new(0, (h - slab) / 2, 0), WALL))
		table.insert(bricks, Brick(Vector3.new(door.X, door.Y, 0.2), Vector3.new(0, door.Y / 2, -hz - 0.1), DARK))
		return bricks
	end
	if tier == "interior" then
		return Floors.Lobby.inside(cfg)
	end
	table.insert(bricks, Brick(Vector3.new(hx * 2 + 0.4, slab, hz * 2 + 0.4), Vector3.new(0, -slab / 2, 0), TRIM))
	Placeholder.WindowWall(bricks, cfg, Vector3.new(0, 0, hz - t / 2), hx * 2, true)
	Placeholder.WindowWall(bricks, cfg, Vector3.new(-hx + t / 2, 0, 0), hz * 2 - t * 2, false)
	Placeholder.WindowWall(bricks, cfg, Vector3.new(hx - t / 2, 0, 0), hz * 2 - t * 2, false)
	local solid = { occlude = true } -- на месте стен каркаса: камера упирается в них у клиента
	table.insert(bricks, Brick(Vector3.new(side, h, t), Vector3.new(-hx + side / 2, h / 2, -hz + t / 2), WALL, solid))
	table.insert(bricks, Brick(Vector3.new(side, h, t), Vector3.new(hx - side / 2, h / 2, -hz + t / 2), WALL, solid))
	table.insert(
		bricks,
		Brick(Vector3.new(door.X, h - door.Y, t), Vector3.new(0, (door.Y + h) / 2, -hz + t / 2), WALL, solid)
	)
	-- наличник входа (выступает на 0.2) и табличка над ним
	table.insert(
		bricks,
		Brick(Vector3.new(0.8, door.Y, 0.2), Vector3.new(-door.X / 2 - 0.4, door.Y / 2, -hz - 0.1), accent)
	)
	table.insert(
		bricks,
		Brick(Vector3.new(0.8, door.Y, 0.2), Vector3.new(door.X / 2 + 0.4, door.Y / 2, -hz - 0.1), accent)
	)
	table.insert(bricks, Brick(Vector3.new(door.X + 1.6, 0.8, 0.2), Vector3.new(0, door.Y + 0.4, -hz - 0.1), accent))
	table.insert(
		bricks,
		Brick(Vector3.new(14, 2.6, 0.2), Vector3.new(0, door.Y + 2.8, -hz - 0.1), DARK, {
			text = { text = "МУЗЕЙ-НЕБОСКРЁБ · DEV", color = WORK },
			name = "LobbySign",
		})
	)
	table.insert(
		bricks,
		Brick(
			Vector3.new(door.X + 2, step.Y, step.X),
			Vector3.new(0, -step.Y / 2 - (cfg.Lobby.Rise - step.Y), -hz - step.X / 2),
			TRIM
		)
	)
	return bricks
end

-- Внутри холла (уровень «интерьер», к фасаду): потолок со светом, площадка лифта, дорожка от входа.
function Floors.Lobby.inside(cfg: any): { FloorBuilder.Brick }
	local hx, hz, t, h = lobbyDims(cfg)
	local land = cfg.Landing
	local lc, lh = land.Center, land.Half
	local bricks: { FloorBuilder.Brick } = {}
	table.insert(
		bricks,
		Brick(Vector3.new(hx * 2 - t * 2 - 0.2, 0.2, hz * 2 - t * 2 - 0.2), Vector3.new(0, h - 0.2, 0), WALL)
	)
	table.insert(
		bricks,
		Brick(Vector3.new(2, 0.3, 2), Vector3.new(0, h - 0.45, 0), WALL, {
			light = { range = 36, brightness = 1.1, color = Color3.fromHex("FFF1D6") },
			material = Enum.Material.Neon,
			name = "Lamp",
		})
	)
	table.insert(bricks, Brick(Vector3.new(lh.X * 2, 0.1, lh.Y * 2), Vector3.new(lc.X, 0.05, lc.Z), DARK))
	local frameZ = hz - t - 0.3
	table.insert(bricks, Brick(Vector3.new(0.6, 10, 0.6), Vector3.new(lc.X - lh.X - 0.3, 5, frameZ), WORK))
	table.insert(bricks, Brick(Vector3.new(0.6, 10, 0.6), Vector3.new(lc.X + lh.X + 0.3, 5, frameZ), WORK))
	table.insert(bricks, Brick(Vector3.new(lh.X * 2 + 1.2, 0.8, 0.6), Vector3.new(lc.X, 10.4, frameZ), WORK))
	table.insert(
		bricks,
		Brick(Vector3.new(5, 1.4, 0.2), Vector3.new(lc.X, 12, hz - t - 0.1), DARK, {
			text = { text = "ЛИФТ", color = WORK },
			name = "LiftSign",
		})
	)
	-- дорожка от входа к лифту
	local from, to = -hz + t, lc.Z - lh.Y
	table.insert(bricks, Brick(Vector3.new(4, 0.1, to - from), Vector3.new(0, 0.05, (from + to) / 2), TRIM))
	return bricks
end

-- Крыша над верхним этажом: плита (сервер) и парапет с будкой лифта (клиент). Оси — как у этажа над верхним.
Floors.Roof = {}

function Floors.Roof.shell(cfg: any): { FloorBuilder.Brick }
	local hx, hz = cfg.Half.X, cfg.Half.Y
	return {
		Brick(Vector3.new(hx * 2, cfg.Slab, hz * 2), Vector3.new(0, -cfg.Slab / 2, 0), DARK, { name = "Roof" }),
	}
end

function Floors.Roof.decor(cfg: any, ctx: any, tier: string): { FloorBuilder.Brick }
	local hx, hz, t = cfg.Half.X, cfg.Half.Y, cfg.Wall
	local slab = cfg.Slab
	local accent = if ctx and ctx.accent then ctx.accent else WORK
	local bricks: { FloorBuilder.Brick } = {
		Brick(Vector3.new(hx * 2 + 0.4, slab, hz * 2 + 0.4), Vector3.new(0, -slab / 2, 0), TRIM),
	}
	if tier == "silhouette" then
		return bricks
	end
	local p = 1.2
	table.insert(bricks, Brick(Vector3.new(hx * 2, p, t), Vector3.new(0, p / 2, -hz + t / 2), WALL))
	table.insert(bricks, Brick(Vector3.new(hx * 2, p, t), Vector3.new(0, p / 2, hz - t / 2), WALL))
	table.insert(bricks, Brick(Vector3.new(t, p, hz * 2 - t * 2), Vector3.new(-hx + t / 2, p / 2, 0), WALL))
	table.insert(bricks, Brick(Vector3.new(t, p, hz * 2 - t * 2), Vector3.new(hx - t / 2, p / 2, 0), WALL))
	local land = cfg.Landing
	table.insert(
		bricks,
		Brick(
			Vector3.new(land.Half.X * 2 + 2, 5, land.Half.Y * 2),
			Vector3.new(land.Center.X, 2.5, land.Center.Z),
			DARK
		)
	)
	table.insert(
		bricks,
		Brick(
			Vector3.new(land.Half.X * 2 + 2.4, 0.6, land.Half.Y * 2 + 0.4),
			Vector3.new(land.Center.X, 5.3, land.Center.Z),
			accent
		)
	)
	return bricks
end

return Floors
