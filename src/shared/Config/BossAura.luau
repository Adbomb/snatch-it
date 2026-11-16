-- Фиолетовая аура Короля-дракона (босс 10). Этап C.1: прототипы A (умеренная) и B (мощная). Этап C.2: вариант C2 —
-- B по всему телу (бока, шея, хвост, бёдра, голени, плечи, предплечья), тёмная дымка, длинные вертикальные всплески,
-- во сне — полная базовая сила (лёгкое «дыхание»), всплески при пробуждении, выпадах и залпе; после поражения гаснет,
-- во сне снова полная. C3 (замечания владельца к C2) — мощная всегда, в том числе во сне и днём: насыщенные языки,
-- тёмный плотный дым, длинные штрихи, ещё лапы, кости крыльев и весь хвост. Этап C.2.3: RoyalAura — основа «Вихрь» +
-- лёгкий «Покров»; утверждена владельцем 2026-11-16 и стоит у настоящего босса (Active). Атрибут
-- workspace.BossAuraPrototype = "A" | "B" | "C2" | "C3" | "Flow" | "Vortex" | "Veil" | "RoyalAura" | "off" —
-- сравнение в Studio (перекрывает Active). Только вид: урона и усилений нет. Числа внешнего вида — здесь, контроллер — BossAuraController.
-- Слои (по ТЗ): Shell — тёмно-фиолетовое свечение вокруг тела; Flame — магические языки (свои текстуры, вверх,
-- разной высоты); Streak — вертикальные энергетические штрихи; Smoke — полупрозрачный тёмный дым у тела и лап;
-- Spark — мелкие искры; Light — один умеренный источник у груди.
-- Зависит только от загруженных своих текстур (assets/textures/vfx/boss10_aura/IDS.md).

local BossAura = {}

BossAura.Zone = 10
BossAura.Attribute = "BossAuraPrototype"
BossAura.Active = "RoyalAura" -- вариант у настоящего босса без атрибута (nil — без ауры); утверждён 2026-11-16

BossAura.Textures = {
	Wisp = "rbxassetid://74136435227189", -- 4×4 кадра
	Streak = "rbxassetid://109734776877204",
	Spark = "rbxassetid://79866710951291",
	Smoke = "rbxassetid://88251907710058", -- 2×2 кадра
	Glow = "rbxassetid://95333945330440",
	-- энергетическое поле (этап C.2, 2026-11-16): свои, Blender (scripts/blender/boss10_aura_textures.py), уже в цвете
	Flow = "rbxassetid://84045383753216", -- лента потока, бесшовная по длине (Beam), толстые нити
	Bolt = "rbxassetid://94974639726852", -- разряд (Beam)
	Orb = "rbxassetid://126032410745866", -- мягкое объёмное свечение
	Swirl = "rbxassetid://91512567704737", -- вихрь, 4×4 кадра (OneShot)
	Veil = "rbxassetid://97763207757032", -- полупрозрачная пелена с прожилками, 2×2 вида (Random)
	Crackle = "rbxassetid://94469876304855", -- треск разрядов, 4×4 кадра (OneShot)
}

-- Сила по состоянию босса (1 — полная боевая). Сон — слабая медленная пульсация.
BossAura.State = {
	Sleep = 0.22,
	Wake = 0.45, -- нарастает до StandUp
	StandUp = 0.75,
	ToCombat = 0.95,
	Combat = 1,
	Victory = 1,
	Defeat = 0, -- гаснет за DefeatFade
	Return = 0.5,
	FallAsleep = 0.22,
}
BossAura.Blend = 0.6 -- с: переход силы между состояниями
BossAura.DefeatFade = 1.8 -- с
BossAura.SleepPulse = { period = 3.2, depth = 0.45 } -- во сне сила × (1 − depth … 1)
-- Слои во сне и при угасании: доля от общей силы (языки и штрихи во сне почти не видны, тлеют свечение и дым).
BossAura.SleepLayer = { Shell = 1.4, Flame = 0.35, Streak = 0, Smoke = 1.2, Spark = 0.5 }

-- Залп (время от начала клипа, как Battle.Volley): подготовка — рост, выстрел — короткий всплеск, потом обратно.
BossAura.Volley = { prepFrom = 0.3, prep = 1.35, fire = 1.95, peak = 1.75, hold = 0.25, back = 0.8 }

-- Дальность и качество: дальше Near — меньше частиц, дальше Far — аура выключена; качество графики игрока
-- (UserGameSettings.SavedQualityLevel 1…10) — доля частиц.
BossAura.Lod = { near = 60, far = 150, minShare = 0.25 }
BossAura.Quality = { low = 3, lowShare = 0.4, mid = 6, midShare = 0.7, auto = 0.8 }

-- Части дракона по слоям (MeshPart; эмиттер — по их габариту). Голова, челюсть и перепонки крыльев не горят:
-- морда, корона и крылья читаются.
local CORE =
	{ "Body", "Body_2", "Neck1", "Neck2", "Tail1", "Tail2", "Tail3", "ThighL", "ThighR", "UpperArmL", "UpperArmR" }
local FLAME = {
	"Body",
	"Body_2",
	"Neck1",
	"Neck2",
	"Neck3",
	"Tail1",
	"Tail2",
	"Tail3",
	"Tail4",
	"ThighL",
	"ThighR",
	"UpperArmL",
	"UpperArmR",
	"ForearmL",
	"ForearmR",
	"WingArmL",
	"WingArmR",
}
local STREAK = { "Body", "Body_2", "Neck1", "Tail2", "ThighL", "ThighR" }
local SMOKE = { "PawL", "PawR", "HindPawL", "HindPawR", "Tail5", "Tail6" }
local SPARK = { "Body", "Neck2", "Tail3", "ScepterShards" }

-- Цвета: ядро языков — светлый пурпур, края — фиолет, хвосты — тёмный индиго (не оранжевый огонь).
local FLAME_COLOR = { { 0, "D88EFF" }, { 0.3, "A63CFF" }, { 0.65, "6A1BC4" }, { 1, "2A0660" } }
local STREAK_COLOR = { { 0, "F6D2FF" }, { 0.5, "CF6BFF" }, { 1, "8A2BE2" } }
local SHELL_COLOR = { { 0, "6A22B8" }, { 1, "2A0850" } }
local SMOKE_COLOR = { { 0, "2E0E4D" }, { 1, "160626" } }
local SPARK_COLOR = { { 0, "FFFFFF" }, { 0.4, "F2A6FF" }, { 1, "B24DFF" } }

-- C3 (этап C.2, замечания владельца): мощнее днём — языки насыщеннее и меньше «выбелены» сложением со светом,
-- дым темнее и гуще, штрихи длиннее.
local FLAME_COLOR_C3 = { { 0, "F4B0FF" }, { 0.25, "E040FF" }, { 0.6, "8A1FD6" }, { 1, "34086E" } }
local SMOKE_COLOR_C3 = { { 0, "3A1266" }, { 1, "1A0733" } }

-- Поправить поля слоя name в списке слоёв (вариант на основе общего набора).
local function tweak(list: { any }, name: string, fields: { [string]: any }): { any }
	for _, layer in list do
		if layer.name == name then
			for key, value in fields do
				layer[key] = value
			end
		end
	end
	return list
end

local function layers(k: { [string]: number }, parts: { [string]: { string } }?)
	-- k — множители варианта: rate (частота), size (размер), bright (яркость), alpha (прозрачность меньше — гуще),
	-- long (длина штрихов); parts — свои части слоёв (C2), byArea — частота по площади части (большие — гуще)
	local P = parts or {}
	local byArea = parts ~= nil
	return {
		{
			name = "Shell",
			parts = P.Shell or CORE,
			byArea = byArea,
			texture = BossAura.Textures.Glow,
			rate = 2.5 * k.rate,
			lifetime = { 1.2, 1.9 },
			size = { { 0, 7 * k.size }, { 0.5, 11 * k.size }, { 1, 12 * k.size } },
			transparency = { { 0, 1 }, { 0.3, 0.76 - 0.1 * k.alpha }, { 1, 1 } },
			color = SHELL_COLOR,
			lightEmission = 0.2,
			lightInfluence = 0.15,
			brightness = 1,
			speed = { 0.3, 0.8 },
			spread = 180,
			acceleration = Vector3.new(0, 0.6, 0),
			zOffset = -2,
			shapeStyle = "Surface",
		},
		{
			name = "Flame",
			parts = P.Flame or FLAME,
			byArea = byArea,
			texture = BossAura.Textures.Wisp,
			flipbook = "Grid4x4",
			rate = 6 * k.rate,
			lifetime = { 0.55, 1.25 },
			size = { { 0, 2.6 * k.size }, { 0.35, 5.6 * k.size, 2 * k.size }, { 1, 3.6 * k.size } },
			squash = { { 0, 0.5 }, { 1, 0.9 } },
			transparency = { { 0, 1 }, { 0.12, 0.22 - 0.1 * k.alpha }, { 0.7, 0.42 }, { 1, 1 } },
			color = FLAME_COLOR,
			lightEmission = 0.4,
			lightInfluence = 0,
			brightness = 1.2 * k.bright,
			speed = { 1.5, 4.5 },
			spread = 18,
			acceleration = Vector3.new(0, 5, 0),
			drag = 0.8,
			rotation = { -12, 12 },
			rotSpeed = { -25, 25 },
			emitUp = true,
			shapeStyle = "Surface",
		},
		{
			name = "Streak",
			parts = P.Streak or STREAK,
			byArea = byArea,
			texture = BossAura.Textures.Streak,
			rate = 3 * k.rate,
			lifetime = { 0.35, 0.8 * (k.long or 1) },
			size = { { 0, 1.4 * k.size * (k.long or 1), 0.6 * k.size }, { 1, 2.2 * k.size * (k.long or 1) } },
			squash = { { 0, 2.6 * (k.long or 1) }, { 1, 3.2 * (k.long or 1) } },
			transparency = { { 0, 1 }, { 0.15, 0.2, 0.2 }, { 0.8, 0.55 }, { 1, 1 } },
			color = STREAK_COLOR,
			lightEmission = 0.8,
			lightInfluence = 0,
			brightness = 2.2 * k.bright,
			speed = { 0.5, 2 },
			spread = 6,
			acceleration = Vector3.new(0, 26, 0), -- вверх по миру: часть может быть повёрнута
			orientation = "FacingCameraWorldUp", -- штрих всегда вертикальный
			emitUp = true,
			shapeStyle = "Surface",
		},
		{
			name = "Smoke",
			parts = P.Smoke or SMOKE,
			byArea = byArea,
			texture = BossAura.Textures.Smoke,
			flipbook = "Grid2x2",
			flipbookMode = "Random",
			rate = 1.4 * k.rate,
			lifetime = { 2.4, 3.6 },
			size = { { 0, 4 * k.size }, { 1, 10 * k.size } },
			transparency = { { 0, 1 }, { 0.25, 0.68 - 0.1 * k.alpha }, { 1, 1 } },
			color = SMOKE_COLOR,
			lightEmission = 0,
			lightInfluence = 0.5,
			brightness = 1,
			speed = { 0.6, 1.6 },
			spread = 70,
			acceleration = Vector3.new(0, 0.9, 0),
			drag = 0.6,
			rotation = { 0, 360 },
			rotSpeed = { -15, 15 },
			emitUp = true,
			shapeStyle = "Volume",
		},
		{
			name = "Spark",
			parts = P.Spark or SPARK,
			texture = BossAura.Textures.Spark,
			rate = 5 * k.rate,
			lifetime = { 0.6, 1.4 },
			size = { { 0, 0.45 * k.size }, { 1, 0.1 } },
			transparency = { { 0, 0 }, { 0.8, 0.3 }, { 1, 1 } },
			color = SPARK_COLOR,
			lightEmission = 1,
			lightInfluence = 0,
			brightness = 3 * k.bright,
			speed = { 3, 8 },
			spread = 55,
			acceleration = Vector3.new(0, 3, 0),
			drag = 0.5,
			emitUp = true,
			shapeStyle = "Surface",
		},
	}
end

BossAura.Variants = {
	A = {
		title = "A — умеренная",
		layers = layers({ rate = 1, size = 1, bright = 1, alpha = 0 }),
		light = { part = "Body", color = "9B4DFF", range = 16, brightness = 1.2 },
		maxParticles = 260, -- оценка Σ частота × жизнь при полной силе (больше — частоты урезаются)
	},
	B = {
		title = "B — мощная (ближе к референсу)",
		layers = layers({ rate = 2, size = 1.3, bright = 1.3, alpha = 1 }),
		light = { part = "Body", color = "A35BFF", range = 22, brightness = 2 },
		maxParticles = 560,
	},
	C2 = {
		title = "C2 — мощная по всему телу (этап C.2)",
		layers = layers({ rate = 1.6, size = 1.3, bright = 1.3, alpha = 1, long = 1.35 }, {
			Shell = {
				"Body",
				"Body_2",
				"Neck1",
				"Neck2",
				"Tail1",
				"Tail2",
				"Tail3",
				"ThighL",
				"ThighR",
				"ShinL",
				"ShinR",
				"UpperArmL",
				"UpperArmR",
				"ForearmL",
				"ForearmR",
			},
			Flame = {
				"Body",
				"Body_2",
				"Neck1",
				"Neck2",
				"Neck3",
				"Tail1",
				"Tail2",
				"Tail3",
				"Tail4",
				"Tail5",
				"Tail6",
				"ThighL",
				"ThighR",
				"ShinL",
				"ShinR",
				"UpperArmL",
				"UpperArmR",
				"ForearmL",
				"ForearmR",
				"WingArmL",
				"WingArmR",
			},
			Streak = { "Body", "Body_2", "Neck1", "Tail2", "Tail3", "ThighL", "ThighR", "UpperArmL", "UpperArmR" },
			Smoke = { "Body", "PawL", "PawR", "HindPawL", "HindPawR", "Tail4", "Tail5", "Tail6" },
		}),
		light = { part = "Body", color = "A35BFF", range = 22, brightness = 2 },
		maxParticles = 600,
		-- сила по состоянию: во сне — полная база с лёгким дыханием, после поражения гаснет
		state = {
			Sleep = 0.9,
			Wake = 1,
			StandUp = 1,
			ToCombat = 1,
			Combat = 1,
			Victory = 1,
			Defeat = 0,
			Return = 0.9,
			FallAsleep = 0.9,
		},
		sleepPulse = { period = 4, depth = 0.15 },
		sleepLayer = { Shell = 1.1, Flame = 0.8, Streak = 0.6, Smoke = 1.15, Spark = 0.8 },
		-- кратковременные всплески: пробуждение (первые time с состояния Wake), начало выпада (AttackAt, не залп)
		bursts = { wake = { peak = 1.6, time = 1.2 }, attack = { peak = 1.3, time = 0.45 } },
	},
	C3 = {
		title = "C3 — мощная и днём, и во сне (этап C.2, замечания владельца)",
		layers = (function()
			local list = layers({ rate = 1.9, size = 1.35, bright = 1.7, alpha = 1.5, long = 1.7 }, {
				Shell = {
					"Body",
					"Body_2",
					"Neck1",
					"Neck2",
					"Tail1",
					"Tail2",
					"Tail3",
					"Tail4",
					"ThighL",
					"ThighR",
					"ShinL",
					"ShinR",
					"UpperArmL",
					"UpperArmR",
					"ForearmL",
					"ForearmR",
				},
				Flame = {
					"Body",
					"Body_2",
					"Neck1",
					"Neck2",
					"Neck3",
					"Tail1",
					"Tail2",
					"Tail3",
					"Tail4",
					"Tail5",
					"Tail6",
					"ThighL",
					"ThighR",
					"ShinL",
					"ShinR",
					"UpperArmL",
					"UpperArmR",
					"ForearmL",
					"ForearmR",
					"PawL",
					"PawR",
					"HindPawL",
					"HindPawR",
					"WingArmL",
					"WingArmR",
					"WingForeL",
					"WingForeR",
				},
				Streak = {
					"Body",
					"Body_2",
					"Neck1",
					"Tail2",
					"Tail3",
					"Tail5",
					"ThighL",
					"ThighR",
					"ShinL",
					"ShinR",
					"UpperArmL",
					"UpperArmR",
					"ForearmL",
					"ForearmR",
					"WingArmL",
					"WingArmR",
					"WingForeL",
					"WingForeR",
				},
				Smoke = { "Body", "Body_2", "PawL", "PawR", "HindPawL", "HindPawR", "Tail3", "Tail4", "Tail5", "Tail6" },
			})
			-- днём: языки насыщенные (меньше сложения со светом, ярче сами), дым тёмный и плотный, свет его не выбеливает
			tweak(list, "Flame", {
				color = FLAME_COLOR_C3,
				lightEmission = 0.25,
				transparency = { { 0, 1 }, { 0.12, 0.06 }, { 0.7, 0.36 }, { 1, 1 } },
			})
			tweak(list, "Streak", { lightEmission = 0.55 })
			tweak(list, "Smoke", {
				color = SMOKE_COLOR_C3,
				lightInfluence = 0.2,
				transparency = { { 0, 1 }, { 0.25, 0.48 }, { 1, 1 } },
			})
			return list
		end)(),
		light = { part = "Body", color = "B05CFF", range = 24, brightness = 2.4 },
		maxParticles = 760,
		-- во сне — та же сила, что в бою (ТЗ: «постоянно мощная»), лёгкое дыхание; после поражения гаснет
		state = {
			Sleep = 1,
			Wake = 1,
			StandUp = 1,
			ToCombat = 1,
			Combat = 1,
			Victory = 1,
			Defeat = 0,
			Return = 1,
			FallAsleep = 1,
		},
		sleepPulse = { period = 4, depth = 0.1 },
		sleepLayer = { Shell = 1.1, Flame = 0.95, Streak = 0.85, Smoke = 1.2, Spark = 0.9 },
		bursts = { wake = { peak = 1.5, time = 1.2 }, attack = { peak = 1.25, time = 0.45 } },
	},
}

-- ── Энергетическое поле (этап C.2, замечания владельца 2026-11-16: «не огонь, а мощное магическое поле») ──────────
-- Три разных варианта на выбор владельца: Flow — потоки (ленты Beam с бегущей текстурой обвивают тело, лапы, кости
-- крыльев и хвост, разряды между частями), Vortex — вихри (плетёные вихри на теле и кольца бегущей энергии вокруг
-- груди, шеи и хвоста), Veil — покров (полупрозрачная пелена с прожилками по всей поверхности и треск разрядов).
-- Всегда полная сила (во сне тоже), после поражения гаснет. Голова, челюсть, Neck4, скипетр, его круг и перепонки
-- крыльев свободны; кости крыльев (Finger*) — только тонкие ленты по краю перепонок. Ленты и разряды — в
-- ribbons / arcs варианта (BossAuraController), частицы — в layers.

local ENERGY_WHITE = { { 0, "FFFFFF" }, { 1, "F2DCFF" } } -- текстуры уже в цвете: оттенок почти белый
local ENERGY_PINK = { { 0, "FFE6FF" }, { 1, "E8B8FF" } }
local ALWAYS =
	{ -- сила по состоянию: всегда полная, после поражения гаснет
		Sleep = 1,
		Wake = 1,
		StandUp = 1,
		ToCombat = 1,
		Combat = 1,
		Victory = 1,
		Defeat = 0,
		Return = 1,
		FallAsleep = 1,
	}
local TORSO = { "Body", "Body_2", "Neck1", "Neck2", "Tail1", "Tail2", "Tail3", "ThighL", "ThighR" }
local SPINE = { "Neck3", "Neck2", "Neck1", "Body", "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "Tail7" }
local ARMS = { { "UpperArmL", "ForearmL", "PawL" }, { "UpperArmR", "ForearmR", "PawR" } }
local LEGS = { { "ThighL", "ShinL", "MetaL", "HindPawL" }, { "ThighR", "ShinR", "MetaR", "HindPawR" } }
local WING_BONES = {
	{ "WingArmL", "WingForeL", "Finger1L" },
	{ "WingForeL", "Finger3L" },
	{ "WingForeL", "Finger4L" },
	{ "WingArmR", "WingForeR", "Finger1R" },
	{ "WingForeR", "Finger3R" },
	{ "WingForeR", "Finger4R" },
}
local ARC_PARTS = {
	"Body",
	"Body_2",
	"Neck1",
	"Neck2",
	"Tail1",
	"Tail2",
	"Tail3",
	"Tail4",
	"Tail5",
	"ThighL",
	"ThighR",
	"UpperArmL",
	"UpperArmR",
	"WingArmL",
	"WingArmR",
	"WingForeL",
	"WingForeR",
}

-- мягкое объёмное свечение у тела (общий слой вариантов; k — гуще / крупнее)
local function orbLayer(k: number, parts: { string }): { [string]: any }
	return {
		name = "Glow",
		parts = parts,
		byArea = true,
		texture = BossAura.Textures.Orb,
		rate = 1.6 * k,
		lifetime = { 1.6, 2.4 },
		size = { { 0, 6 * k }, { 0.5, 10 * k }, { 1, 12 * k } },
		transparency = { { 0, 1 }, { 0.35, 0.7 }, { 1, 1 } },
		color = ENERGY_WHITE,
		lightEmission = 0.7,
		lightInfluence = 0,
		brightness = 1.3,
		speed = { 0.2, 0.5 },
		spread = 180,
		acceleration = Vector3.zero,
		zOffset = -2,
		shapeStyle = "Surface",
	}
end

-- энергетические искорки: медленно всплывают и гаснут
local function moteLayer(rate: number, parts: { string }): { [string]: any }
	return {
		name = "Mote",
		parts = parts,
		texture = BossAura.Textures.Spark,
		rate = rate,
		lifetime = { 0.9, 1.8 },
		size = { { 0, 0.45 }, { 1, 0.08 } },
		transparency = { { 0, 0 }, { 0.75, 0.3 }, { 1, 1 } },
		color = { { 0, "FFFFFF" }, { 0.5, "FF9CF4" }, { 1, "B24DFF" } },
		lightEmission = 1,
		lightInfluence = 0,
		brightness = 2.6,
		speed = { 1, 3 },
		spread = 70,
		acceleration = Vector3.new(0, 2.2, 0),
		drag = 0.8,
		emitUp = true,
		shapeStyle = "Surface",
	}
end

BossAura.Variants.Flow = {
	title = "Потоки энергии — ленты обвивают тело, лапы, крылья и хвост; разряды между частями",
	layers = { orbLayer(1.6, TORSO), moteLayer(9, { "Body", "Neck2", "Tail2", "Tail4", "WingForeL", "WingForeR" }) },
	ribbons = {
		{ -- три нити спиралью вдоль шеи, спины и хвоста до кончика
			name = "Stream",
			chains = { SPINE },
			strands = 5,
			angles = { -2.3, -1.15, 0, 1.15, 2.3 }, -- сверху, по бокам и снизу по бокам; у пола — над полом
			wobble = 0.5,
			radial = 1,
			margin = 3.2,
			bulge = 0.8,
			tip = true,
			width = { 9, 7 },
			texture = BossAura.Textures.Flow,
			textureLength = 12,
			textureSpeed = 1.6,
			color = ENERGY_WHITE,
			transparency = { { 0, 0 }, { 1, 0 } },
			lightEmission = 0.4,
			brightness = 3.4,
			segments = 10,
		},
		{ -- по две нити на лапах
			name = "Limb",
			chains = { ARMS[1], ARMS[2], LEGS[1], LEGS[2] },
			strands = 1,
			radial = 1,
			margin = 1.6,
			bulge = 0.6,
			tip = true,
			tipReach = 0.6,
			width = { 5, 3.6 },
			texture = BossAura.Textures.Flow,
			textureLength = 8,
			textureSpeed = 1.9,
			color = ENERGY_WHITE,
			transparency = { { 0, 0 }, { 1, 0 } },
			lightEmission = 0.4,
			brightness = 3.2,
			segments = 8,
		},
		{ -- по костям крыльев к концам пальцев (края перепонок), перепонки остаются чистыми
			name = "Wing",
			chains = WING_BONES,
			strands = 1,
			radial = 0.65,
			margin = 0.25,
			bulge = 0.15,
			tip = true,
			width = { 2.8, 1.6 },
			texture = BossAura.Textures.Flow,
			textureLength = 9,
			textureSpeed = 2.4,
			color = ENERGY_PINK,
			transparency = { { 0, 0.1 }, { 1, 0.1 } },
			lightEmission = 0.85,
			brightness = 2,
			segments = 8,
		},
	},
	arcs = {
		name = "Arc",
		parts = ARC_PARTS,
		pool = 5,
		every = { 0.15, 0.45 },
		life = { 0.08, 0.2 },
		maxLength = 18,
		width = { 1.4, 0.7 },
		texture = BossAura.Textures.Bolt,
		textureMode = "Stretch",
		textureLength = 1,
		textureSpeed = 0,
		color = { { 0, "FFFFFF" }, { 1, "FFC8FF" } },
		lightEmission = 1,
		brightness = 2.6,
		segments = 10,
	},
	light = { part = "Body", color = "B05CFF", range = 24, brightness = 2.2 },
	maxParticles = 320,
	state = ALWAYS,
	sleepPulse = { period = 4, depth = 0.12 },
	sleepLayer = { Glow = 1, Mote = 0.9, Stream = 1, Limb = 1, Wing = 1, Arc = 0.7 },
	bursts = { wake = { peak = 1.5, time = 1.2 }, attack = { peak = 1.3, time = 0.45 } },
}

BossAura.Variants.Vortex = {
	title = "Магический вихрь — плетёные вихри на теле и кольца бегущей энергии вокруг груди, шеи и хвоста",
	layers = {
		{
			name = "Swirl",
			parts = {
				"Body",
				"Body_2",
				"Neck1",
				"Neck2",
				"Tail1",
				"Tail2",
				"Tail3",
				"Tail4",
				"Tail5",
				"ThighL",
				"ThighR",
				"Tail6",
				"ShinL",
				"ShinR",
				"UpperArmL",
				"UpperArmR",
				"ForearmL",
				"ForearmR",
				"WingArmL",
				"WingArmR",
				"WingForeL",
				"WingForeR",
			},
			byArea = true,
			texture = BossAura.Textures.Swirl,
			flipbook = "Grid4x4",
			rate = 3.4,
			lifetime = { 1.1, 1.6 },
			size = { { 0, 5 }, { 1, 10 } },
			transparency = { { 0, 0 }, { 1, 0.15 } },
			color = ENERGY_WHITE,
			lightEmission = 0.5,
			lightInfluence = 0,
			brightness = 2.2,
			speed = { 0.2, 0.6 },
			spread = 180,
			acceleration = Vector3.new(0, 0.4, 0),
			rotation = { 0, 360 },
			rotSpeed = { -90, -45 },
			lockedToPart = true,
			shapeStyle = "Surface",
		},
		orbLayer(0.9, TORSO),
		moteLayer(6, { "Body", "Body_2", "Neck1", "Tail2", "Tail4", "WingArmL", "WingArmR" }),
	},
	ribbons = {
		{
			name = "Ring",
			rings = {
				{ part = "Body", toward = "Neck1", shift = 5, radiusK = 1.12, segments = 8 },
				{ part = "Body", toward = "Tail1", shift = 6, radiusK = 1.05, segments = 8, speed = -1 },
				{ part = "Neck2", toward = "Neck3", radiusK = 1.25, segments = 6, speed = 1.3 },
				{ part = "Tail2", toward = "Tail3", radiusK = 1.2, segments = 6, speed = -1.2 },
				{ part = "Tail4", toward = "Tail5", radiusK = 1.25, segments = 6, speed = 1.4 },
				{ part = "Tail6", toward = "Tail7", radiusK = 1.35, segments = 6, speed = -1.6 },
			},
			width = { 4, 4 },
			texture = BossAura.Textures.Flow,
			textureLength = 12,
			textureSpeed = 3.2,
			color = ENERGY_PINK,
			transparency = { { 0, 0 }, { 1, 0 } },
			lightEmission = 0.6,
			brightness = 2.8,
			segments = 8,
		},
		{ -- тонкие нити на крыльях — вихрь «тянется» к концам крыльев
			name = "Wing",
			chains = WING_BONES,
			strands = 1,
			radial = 0.65,
			margin = 0.25,
			bulge = 0.15,
			tip = true,
			width = { 1.8, 1 },
			texture = BossAura.Textures.Flow,
			textureLength = 9,
			textureSpeed = 2.4,
			color = ENERGY_PINK,
			transparency = { { 0, 0.2 }, { 1, 0.2 } },
			lightEmission = 0.85,
			brightness = 1.7,
			segments = 8,
		},
	},
	arcs = {
		name = "Arc",
		parts = ARC_PARTS,
		pool = 2,
		every = { 0.6, 1.4 },
		life = { 0.08, 0.18 },
		maxLength = 14,
		width = { 0.8, 0.45 },
		texture = BossAura.Textures.Bolt,
		textureMode = "Stretch",
		textureLength = 1,
		textureSpeed = 0,
		color = { { 0, "FFFFFF" }, { 1, "FFC8FF" } },
		lightEmission = 1,
		brightness = 2.4,
		segments = 10,
	},
	light = { part = "Body", color = "B05CFF", range = 24, brightness = 2.2 },
	maxParticles = 560,
	state = ALWAYS,
	sleepPulse = { period = 4, depth = 0.12 },
	sleepLayer = { Swirl = 1, Glow = 1, Mote = 0.9, Ring = 1, Wing = 1, Arc = 0.7 },
	bursts = { wake = { peak = 1.5, time = 1.2 }, attack = { peak = 1.3, time = 0.45 } },
}

local VEIL_PARTS = {
	"Body",
	"Body_2",
	"Neck1",
	"Tail1",
	"Tail2",
	"Tail3",
	"Tail4",
	"Tail5",
	"Tail6",
	"ThighL",
	"ThighR",
	"ShinL",
	"ShinR",
	"UpperArmL",
	"UpperArmR",
	"ForearmL",
	"ForearmR",
	"WingArmL",
	"WingArmR",
	"WingForeL",
	"WingForeR",
}

BossAura.Variants.Veil = {
	title = "Энергетический покров — полупрозрачная пелена с прожилками по всему телу и треск разрядов",
	layers = {
		{
			name = "Veil",
			parts = VEIL_PARTS,
			byArea = true,
			texture = BossAura.Textures.Veil,
			flipbook = "Grid2x2",
			flipbookMode = "Random",
			rate = 2,
			lifetime = { 2.2, 3.2 },
			size = { { 0, 6 }, { 0.5, 9.5 }, { 1, 11 } },
			transparency = { { 0, 1 }, { 0.25, 0.42 }, { 0.7, 0.58 }, { 1, 1 } },
			color = ENERGY_WHITE,
			lightEmission = 0.35,
			lightInfluence = 0.1,
			brightness = 1.6,
			speed = { 0.15, 0.45 },
			spread = 180,
			acceleration = Vector3.zero,
			rotation = { 0, 360 },
			rotSpeed = { -10, 10 },
			lockedToPart = true,
			zOffset = -1,
			shapeStyle = "Surface",
		},
		{ -- шея — пелена мельче: голова и корона открыты
			name = "VeilNeck",
			parts = { "Neck2", "Neck3" },
			texture = BossAura.Textures.Veil,
			flipbook = "Grid2x2",
			flipbookMode = "Random",
			rate = 2.2,
			lifetime = { 2, 2.8 },
			size = { { 0, 4 }, { 0.5, 6 }, { 1, 7 } },
			transparency = { { 0, 1 }, { 0.25, 0.42 }, { 0.7, 0.58 }, { 1, 1 } },
			color = ENERGY_WHITE,
			lightEmission = 0.45,
			lightInfluence = 0.1,
			brightness = 1.7,
			speed = { 0.1, 0.3 },
			spread = 180,
			acceleration = Vector3.zero,
			rotation = { 0, 360 },
			rotSpeed = { -10, 10 },
			lockedToPart = true,
			zOffset = -1,
			shapeStyle = "Surface",
		},
		{
			name = "Crackle",
			parts = VEIL_PARTS,
			byArea = true,
			texture = BossAura.Textures.Crackle,
			flipbook = "Grid4x4",
			rate = 4,
			lifetime = { 0.35, 0.6 },
			size = { { 0, 3.6 }, { 1, 5 } },
			transparency = { { 0, 0 }, { 1, 0 } },
			color = ENERGY_WHITE,
			lightEmission = 1,
			lightInfluence = 0,
			brightness = 2.4,
			speed = { 0, 0.2 },
			spread = 180,
			acceleration = Vector3.zero,
			rotation = { 0, 360 },
			lockedToPart = true,
			zOffset = 0.5,
			shapeStyle = "Surface",
		},
		orbLayer(0.9, TORSO),
		moteLayer(6, { "Body", "Body_2", "Neck1", "Tail2", "Tail4", "ThighL", "ThighR", "WingForeL", "WingForeR" }),
	},
	light = { part = "Body", color = "B05CFF", range = 24, brightness = 2.2 },
	maxParticles = 560,
	state = ALWAYS,
	sleepPulse = { period = 4, depth = 0.12 },
	sleepLayer = { Veil = 1, VeilNeck = 1, Crackle = 0.8, Glow = 1, Mote = 0.9 },
	bursts = { wake = { peak = 1.5, time = 1.2 }, attack = { peak = 1.3, time = 0.45 } },
}

-- ── RoyalAura (2026-11-16, направление владельца: основа «Вихрь» + лёгкий «Покров») ─────────────────────────────
-- Одна объединённая аура с общим бюджетом (не два прототипа сразу): вихри Vortex по телу и кольца бегущей энергии,
-- орбиты — вихри и искры летят по кругу вокруг груди, бёдер, шеи и хвоста (энергия идёт вокруг корпуса, со всех
-- сторон, а не только вверх), тонкая тёмно-пурпурная пелена только на корпусе и хвосте связывает вихри в одно поле
-- (броня, голова, крылья и скипетр не закрыты, тело не белеет), немного треска и разрядов. Сила то нарастает, то
-- спадает (vary), в залп вихри, орбиты и разряды усиливаются больше остального (volleyLayer). Утверждена владельцем
-- 2026-11-16 (Active). Правка владельца: прямо перед нагрудником розовое свечение слабее, чтобы броня читалась —
-- вихри корпуса рисуются чуть «за» поверхностью и прозрачнее, кольцо груди (brightness кольца) и орбита у груди
-- (ORBIT_LAYERS_CHEST) приглушены; остальная аура та же.
local ROYAL_SWIRL_PARTS =
	{ -- без корпуса: у корпуса вихри — отдельным слоем «Swirl» за поверхностью (RoyalAura.layers)
		"Neck1",
		"Neck2",
		"Tail1",
		"Tail2",
		"Tail3",
		"Tail4",
		"Tail5",
		"Tail6",
		"ThighL",
		"ThighR",
		"ShinL",
		"ShinR",
		"UpperArmL",
		"UpperArmR",
		"ForearmL",
		"ForearmR",
		"WingArmL",
		"WingArmR",
	}
local ROYAL_VEIL_PARTS = { "Body", "Body_2", "Neck1", "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "ThighL", "ThighR" }
local ROYAL_VEIL_COLOR = { { 0, "D9B8FF" }, { 1, "B488FF" } } -- темнее белого: пелена не выбеливает тело

-- частицы точки орбиты: вихрь, летящий по касательной (тормозит, вращается), и след искр
local ORBIT_LAYERS = {
	{
		name = "OrbitSwirl",
		texture = BossAura.Textures.Swirl,
		flipbook = "Grid4x4",
		rate = 4,
		lifetime = { 0.9, 1.3 },
		size = { { 0, 2.8 }, { 1, 6 } },
		transparency = { { 0, 0.05 }, { 1, 0.3 } },
		color = ENERGY_WHITE,
		lightEmission = 0.55,
		lightInfluence = 0,
		brightness = 2.2,
		speed = { 3, 6 },
		spread = 12,
		acceleration = Vector3.zero,
		drag = 1.6,
		rotation = { 0, 360 },
		rotSpeed = { -120, -60 },
		emitUp = true,
	},
	{
		name = "OrbitMote",
		texture = BossAura.Textures.Spark,
		rate = 5,
		lifetime = { 0.6, 1.1 },
		size = { { 0, 0.5 }, { 1, 0.08 } },
		transparency = { { 0, 0 }, { 0.7, 0.25 }, { 1, 1 } },
		color = { { 0, "FFFFFF" }, { 0.5, "FF9CF4" }, { 1, "B24DFF" } },
		lightEmission = 1,
		lightInfluence = 0,
		brightness = 2.6,
		speed = { 5, 9 },
		spread = 18,
		acceleration = Vector3.zero,
		drag = 1.2,
		emitUp = true,
	},
}

-- орбита прямо перед нагрудником: те же вихри и искры, но вихрь мельче, прозрачнее и тусклее — броня читается
local ORBIT_LAYERS_CHEST = {
	table.clone(ORBIT_LAYERS[1]),
	ORBIT_LAYERS[2],
}
ORBIT_LAYERS_CHEST[1].size = { { 0, 2.2 }, { 1, 4.6 } }
ORBIT_LAYERS_CHEST[1].transparency = { { 0, 0.35 }, { 1, 0.6 } }
ORBIT_LAYERS_CHEST[1].lightEmission = 0.3
ORBIT_LAYERS_CHEST[1].brightness = 1.2

BossAura.Variants.RoyalAura = {
	title = "RoyalAura — вихри и кольца энергии вокруг всего тела, энергия по орбитам, лёгкий покров, разряды",
	layers = {
		{
			name = "Swirl",
			parts = ROYAL_SWIRL_PARTS,
			byArea = true,
			texture = BossAura.Textures.Swirl,
			flipbook = "Grid4x4",
			rate = 3,
			lifetime = { 1.1, 1.6 },
			size = { { 0, 5 }, { 1, 10 } },
			transparency = { { 0, 0 }, { 1, 0.15 } },
			color = ENERGY_WHITE,
			lightEmission = 0.5,
			lightInfluence = 0,
			brightness = 2.1,
			speed = { 0.2, 0.6 },
			spread = 180,
			acceleration = Vector3.new(0, 0.4, 0),
			rotation = { 0, 360 },
			rotSpeed = { -90, -45 },
			lockedToPart = true,
			shapeStyle = "Surface",
		},
		{ -- те же вихри на корпусе (то же имя слоя: та же волна силы и усиление в залп), но рисуются чуть «за»
			-- поверхностью (zOffset) и прозрачнее: по контуру тела и с боков видны как раньше, а прямо перед
			-- нагрудником не заливают броню розовым (правка владельца 2026-11-16)
			name = "Swirl",
			parts = { "Body", "Body_2" },
			byArea = true,
			texture = BossAura.Textures.Swirl,
			flipbook = "Grid4x4",
			rate = 3,
			lifetime = { 1.1, 1.6 },
			size = { { 0, 5 }, { 1, 10 } },
			transparency = { { 0, 0.2 }, { 1, 0.4 } },
			color = ENERGY_WHITE,
			lightEmission = 0.35,
			lightInfluence = 0,
			brightness = 1.7,
			speed = { 0.2, 0.6 },
			spread = 180,
			acceleration = Vector3.new(0, 0.4, 0),
			rotation = { 0, 360 },
			rotSpeed = { -90, -45 },
			lockedToPart = true,
			zOffset = -2.5,
			shapeStyle = "Surface",
		},
		{ -- лёгкий покров: в 3 раза реже и вдвое прозрачнее самостоятельного «Покрова», под вихрями
			name = "VeilLight",
			parts = ROYAL_VEIL_PARTS,
			byArea = true,
			texture = BossAura.Textures.Veil,
			flipbook = "Grid2x2",
			flipbookMode = "Random",
			rate = 0.65,
			lifetime = { 2.4, 3.2 },
			size = { { 0, 6 }, { 0.5, 9 }, { 1, 10 } },
			transparency = { { 0, 1 }, { 0.3, 0.7 }, { 0.75, 0.8 }, { 1, 1 } },
			color = ROYAL_VEIL_COLOR,
			lightEmission = 0.25,
			lightInfluence = 0.15,
			brightness = 1.2,
			speed = { 0.1, 0.3 },
			spread = 180,
			acceleration = Vector3.zero,
			rotation = { 0, 360 },
			rotSpeed = { -8, 8 },
			lockedToPart = true,
			zOffset = -1.5,
			shapeStyle = "Surface",
		},
		{
			name = "Crackle",
			parts = { "Body", "Body_2", "Tail2", "ThighR" }, -- меньше эмиттеров (телефоны), частота выше — вид тот же
			byArea = true,
			texture = BossAura.Textures.Crackle,
			flipbook = "Grid4x4",
			rate = 1.8,
			lifetime = { 0.35, 0.6 },
			size = { { 0, 2.6 }, { 1, 3.6 } },
			transparency = { { 0, 0 }, { 1, 0 } },
			color = ENERGY_WHITE,
			lightEmission = 1,
			lightInfluence = 0,
			brightness = 2.3,
			speed = { 0, 0.2 },
			spread = 180,
			acceleration = Vector3.zero,
			rotation = { 0, 360 },
			lockedToPart = true,
			zOffset = 0.5,
			shapeStyle = "Surface",
		},
		orbLayer(1, { "Body", "Body_2", "Neck1", "Tail2" }),
		moteLayer(7, { "Body", "Body_2", "Tail2", "WingArmL" }),
	},
	orbits = {
		{
			part = "Body",
			toward = "Neck1",
			shift = 4,
			radiusK = 1.3,
			count = 2,
			speed = 1.5,
			layers = ORBIT_LAYERS_CHEST,
		},
		{ part = "Body", toward = "Tail1", shift = 5, radiusK = 1.2, count = 2, speed = -1.2, layers = ORBIT_LAYERS },
		{ part = "Neck1", toward = "Neck2", radiusK = 1.5, count = 1, speed = 2, layers = ORBIT_LAYERS },
		{ part = "Tail3", toward = "Tail4", radiusK = 1.6, count = 2, speed = -1.8, layers = ORBIT_LAYERS },
	},
	ribbons = {
		{
			name = "Ring",
			rings = {
				{ part = "Body", toward = "Neck1", shift = 5, radiusK = 1.12, segments = 8, brightness = 0.45 }, -- у нагрудника
				{ part = "Body", toward = "Tail1", shift = 6, radiusK = 1.05, segments = 8, speed = -1 },
				{ part = "Neck2", toward = "Neck3", radiusK = 1.25, segments = 6, speed = 1.3, minQuality = 0.6 },
				{ part = "Tail2", toward = "Tail3", radiusK = 1.2, segments = 6, speed = -1.2 },
				{ part = "Tail4", toward = "Tail5", radiusK = 1.25, segments = 6, speed = 1.4, minQuality = 0.6 },
				{ part = "Tail6", toward = "Tail7", radiusK = 1.35, segments = 6, speed = -1.6, minQuality = 0.6 },
			},
			width = { 3.6, 3.6 },
			texture = BossAura.Textures.Flow,
			textureLength = 12,
			textureSpeed = 3.2,
			color = ENERGY_PINK,
			transparency = { { 0, 0.05 }, { 1, 0.05 } },
			lightEmission = 0.6,
			brightness = 2.5,
			segments = 8,
		},
		{ -- тонкие нити по костям крыльев к концам пальцев (края перепонок); на низком качестве графики — нет
			name = "Wing",
			chains = WING_BONES,
			strands = 1,
			minQuality = 0.6,
			radial = 0.65,
			margin = 0.25,
			bulge = 0.15,
			tip = true,
			width = { 1.5, 0.8 },
			texture = BossAura.Textures.Flow,
			textureLength = 9,
			textureSpeed = 2.4,
			color = ENERGY_PINK,
			transparency = { { 0, 0.25 }, { 1, 0.25 } },
			lightEmission = 0.85,
			brightness = 1.6,
			segments = 8,
		},
	},
	arcs = {
		name = "Arc",
		parts = ARC_PARTS,
		pool = 3,
		every = { 0.4, 1 },
		life = { 0.08, 0.18 },
		maxLength = 15,
		width = { 0.9, 0.5 },
		texture = BossAura.Textures.Bolt,
		textureMode = "Stretch",
		textureLength = 1,
		textureSpeed = 0,
		color = { { 0, "FFFFFF" }, { 1, "FFC8FF" } },
		lightEmission = 1,
		brightness = 2.5,
		segments = 10,
	},
	light = { part = "Body", color = "B05CFF", range = 24, brightness = 2.2 },
	maxParticles = 420, -- общий бюджет: вихри, покров, треск, свечение, искры и орбиты
	state = ALWAYS,
	sleepPulse = { period = 4, depth = 0.12 },
	sleepLayer = {
		Swirl = 1,
		VeilLight = 1,
		Crackle = 0.8,
		Glow = 1,
		Mote = 0.9,
		OrbitSwirl = 1,
		OrbitMote = 1,
		Ring = 1,
		Wing = 1,
		Arc = 0.7,
	},
	-- плавные вариации силы слоёв (период, с; глубина ±): вихри и кольца «дышат» не в такт с орбитами
	vary = {
		Swirl = { period = 3.7, depth = 0.25 },
		OrbitSwirl = { period = 2.9, depth = 0.3 },
		Ring = { period = 4.3, depth = 0.2 },
		Wing = { period = 3.1, depth = 0.25 },
		VeilLight = { period = 6.1, depth = 0.15 },
	},
	-- залп: вихри, орбиты и разряды сверх общего усиления (доля надбавки), покров — меньше
	volleyLayer = { Swirl = 1.4, OrbitSwirl = 1.6, OrbitMote = 1.6, Arc = 2, Crackle = 1.5, VeilLight = 0.4 },
	bursts = { wake = { peak = 1.5, time = 1.2 }, attack = { peak = 1.3, time = 0.45 } },
}

return BossAura
