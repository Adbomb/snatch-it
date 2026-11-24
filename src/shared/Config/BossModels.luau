-- Модели боссов из Blender (D40): у каждой части свой меш (импорт FBX в Studio даёт MeshId), карты SurfaceAppearance
-- общие на группу частей (голова и тело, assets/textures/art/IDS.md). turn — поворот меша частей вокруг вертикали
-- после импорта, чтобы он совпал со скелетом. Нет меша у части — часть показывается заготовкой (блок цвета из
-- скелета) до импорта. Скелет и позы — Config/Boss<N>…Rig (1 — пёс, 2 — торговец, 3 — Крысиный король, 4 — Сфинкс,
-- 5 — Йети, 10 — дракон). Ни от чего
-- не зависит.

export type BossModel = {
	name: string,
	-- metal, rough, glow — только у части боссов (босс 10): металл, шероховатость, маска свечения (Looks через make_looks)
	maps: { [string]: { color: string, normal: string, metal: string?, rough: string?, glow: string? } },
	meshes: { [string]: string },
	turn: number,
}

local ROUGHNESS = "rbxassetid://120633114716941"

-- MeshId частей пса из импорта Boss1_Dog.fbx (владелец, 2026-11-02; assets/models/Boss1_meshids.json).
-- Импорт повернул меши на 180° вокруг вертикали — turn = 180.
local DOG_MESHES: { [string]: number } = {
	BLowerL = 137250136190249,
	BLowerR = 124331422196767,
	BUpperL = 104633290669632,
	BUpperR = 125922436330102,
	EarL = 106455314556039,
	EarR = 139039230448770,
	EyelidL = 90682315510664,
	EyelidR = 102060066850738,
	FLowerL = 119589483306303,
	FLowerR = 103144601510934,
	FUpperL = 89740211608879,
	FUpperR = 76645415165349,
	Head = 132977355807397,
	Jaw = 85791501528323,
	Tail = 106766032217885,
	Torso = 103252526545154,
}

-- MeshId частей торговца — из Boss2_Trader.fbx (загружен 2026-11-14 через Open Cloud, модель 134330107033271; привязан
-- scripts/bind_meshes.py). Часть без меша — заготовка цвета из скелета (Config/Boss2TraderRig).
local TRADER_MESHES: { [string]: number } = {
	ArmLowerL = 86415180042589,
	ArmLowerR = 120434606344060,
	ArmUpperL = 102432014766061,
	ArmUpperR = 139107500659146,
	Head = 105533304393094,
	Jaw = 138746933715630,
	LegLowerL = 103683259722894,
	LegLowerR = 109616170207781,
	LegUpperL = 100693482010533,
	LegUpperR = 119087892398115,
	Sack = 80408592501846,
	Torso = 93208582888005,
}

-- Крысиный король (D54): MeshId частей из Boss3_RatKing.fbx (загружен 2026-11-14 через Open Cloud, привязан
-- scripts/bind_meshes.py). Часть без меша — Part-версия по утверждённой модели (Config/Boss3RatKingParts, BossService).
local RATKING_MESHES: { [string]: number } = {
	ArmLowerL = 108524552729346,
	ArmLowerR = 137559848794758,
	ArmUpperL = 92072669138159,
	ArmUpperR = 112217731885409,
	Cape = 140049790516190,
	Crown = 111432056197919,
	EarL = 135238031138059,
	EarR = 117818467375364,
	EyelidL = 137802704365121,
	EyelidR = 136255820200481,
	Head = 79336837251371,
	Jaw = 140141247113542,
	LegLowerL = 93126552545582,
	LegLowerR = 140274471492526,
	LegUpperL = 81993658216949,
	LegUpperR = 124811778184299,
	Pouch = 90221963618593,
	Scepter = 90541314799039,
	Tail1 = 108645944659540,
	Tail2 = 101515201637640,
	Torso = 90029549678441,
}

-- Сфинкс-лежебока (босс 4): MeshId частей из импорта Boss4_Sphinx_game.fbx (вписывает
-- scripts/boss4_bind_after_import.py через bind_meshes.py). Часть без MeshId — заготовка цвета из скелета
-- (Config/Boss4SphinxRig).
local SPHINX_MESHES: { [string]: number } = {
	BLowerL = 136264078358695,
	BLowerR = 126567884344964,
	BPawL = 124898513096469,
	BPawR = 131242002217036,
	BUpperL = 120775202082723,
	BUpperR = 126676089715939,
	BrowL = 73163774260801,
	BrowR = 124577627512160,
	EarL = 98739411571232,
	EarR = 112245618017850,
	EyelidL = 88135963321120,
	EyelidR = 123651834859234,
	FLowerL = 119831363139709,
	FLowerR = 137833052195452,
	FPawL = 108122523500804,
	FPawR = 140127274993861,
	FUpperL = 101035420250003,
	FUpperR = 120957225116513,
	Head = 116433705091188,
	Jaw = 117035870634500,
	NemesL = 113971683732431,
	NemesR = 105354763479477,
	Tail1 = 71467404458675,
	Tail2 = 115105922182203,
	Tail3 = 127859571110775,
	Tassel = 127241642082178,
	Torso = 124012337691510,
}

-- Король-дракон (босс 10, этап C): MeshId частей, добавочных мешей (Body_2 — правая половина корпуса, EyeL/R —
-- глаза) и перепонок WingMembranes (skinned) из Open Cloud; вписывает scripts/boss10_bind_after_import.py.
local DRAGON_MESHES: { [string]: number } = {
	Body = 139220072749968,
	Body_2 = 127674892660899,
	Collar = 118892073217748,
	EyeL = 104602639068037,
	EyeR = 100423302782160,
	Finger1L = 93819254332704,
	Finger1R = 96811032850035,
	Finger2L = 102977905139313,
	Finger2R = 132854898651346,
	Finger3L = 113376045871634,
	Finger3R = 125190025050369,
	Finger4L = 114333529689983,
	Finger4R = 86455763022601,
	ForearmL = 132528750194414,
	ForearmR = 79634318501644,
	Head = 70958083264654,
	HindPawL = 104002470267805,
	HindPawR = 78186701159571,
	Jaw = 74107897491758,
	MantleL1 = 76462303862261,
	MantleL2 = 86590112524449,
	MantleL3 = 111334663267521,
	MantleR1 = 113366023536384,
	MantleR2 = 132410633825063,
	MantleR3 = 96671384764827,
	MetaL = 90531810135067,
	MetaR = 135816688226567,
	Neck1 = 85176900995463,
	Neck2 = 100121819908603,
	Neck3 = 112118708241973,
	Neck4 = 135238618103172,
	PauldronL = 92444798001251,
	PauldronR = 140688846045240,
	PawL = 102400730169067,
	PawR = 118943317268274,
	Scepter = 73460449645829,
	ScepterCircle = 90972963230008,
	ScepterShards = 95869115258290,
	ShinL = 81655608217461,
	ShinR = 136074974916163,
	Tail1 = 77231043627239,
	Tail2 = 98064806239587,
	Tail3 = 89929460133755,
	Tail4 = 117127218113255,
	Tail5 = 85753931734007,
	Tail6 = 140485815735764,
	Tail7 = 99082251196393,
	ThighL = 130907301746218,
	ThighR = 135102514272688,
	UpperArmL = 131001855179187,
	UpperArmR = 72533211317645,
	WingArmL = 138549759163619,
	WingArmR = 108254742001210,
	WingForeL = 129042891481881,
	WingForeR = 134132668550394,
	WingMembranes = 120947390133081,
}

-- MeshId частей Йети-коллекционера — модель Open Cloud 115856961352655 (Boss5_Yeti.fbx, загружена 2026-11-24;
-- assets/models/Boss5_meshids.json, вписывает scripts/bind_meshes.py).
local YETI_MESHES: { [string]: number } = {
	Block = 105977164972324,
	BlockFrame = 124643434705095,
	BlockTop = 78727668818006,
	BlockTopFrame = 127567874290074,
	BrowL = 127742719894488,
	BrowR = 98410730061618,
	ExCritter = 97258883847055,
	ExCup = 95657324508748,
	ExGem = 127020399904045,
	ExLovibum = 124527362780495,
	EyelidL = 135880482273931,
	EyelidR = 138408304256772,
	FingersL = 136742894629751,
	FingersR = 87615735179764,
	FootL = 77884554823168,
	FootR = 81914325446537,
	ForeArmL = 123784516181703,
	ForeArmR = 108304200525776,
	HandL = 92164908211429,
	HandR = 119655609769684,
	Head = 136352406131019,
	Jaw = 79352699759839,
	Lens = 133160884983976,
	Monocle = 121716652755827,
	ShinL = 76802776319321,
	ShinR = 107427268827355,
	ThighL = 114709404851630,
	ThighR = 136101499055448,
	Torso = 108716682221463,
	UpperArmL = 81337829205729,
	UpperArmR = 111124413752864,
}

local function ids(list: { [string]: number }): { [string]: string }
	local out = {}
	for part, id in list do
		out[part] = "rbxassetid://" .. id
	end
	return out
end

return table.freeze({
	Roughness = ROUGHNESS,
	[1] = {
		name = "Сторожевой пёс",
		maps = {
			Head = { color = "rbxassetid://114075578064919", normal = "rbxassetid://72281207474806" },
			Body = { color = "rbxassetid://94835517459826", normal = "rbxassetid://94675390063511" },
		},
		meshes = ids(DOG_MESHES),
		turn = 180,
	} :: BossModel,
	-- Карты торговца загружены до бана аккаунта (2026-11-02, assets/textures/art/IDS.md).
	[2] = {
		name = "Торговец-громила",
		maps = {
			Head = { color = "rbxassetid://111835541987471", normal = "rbxassetid://95234991557771" },
			Body = { color = "rbxassetid://88982407819751", normal = "rbxassetid://111891368383392" },
			Limbs = { color = "rbxassetid://126025887496516", normal = "rbxassetid://71574604601669" },
		},
		meshes = ids(TRADER_MESHES),
		turn = 180,
	} :: BossModel,
	-- D55: бой Крысиного короля на материалах D54. Меши и карты загружены 2026-11-14 по просьбе владельца
	-- (assets/models/Boss3_RatKing.fbx — модель 113666622053915; карты — assets/textures/art/Boss3_maps.json).
	[3] = {
		name = "Крысиный король",
		maps = {
			Head = { color = "rbxassetid://108766978169224", normal = "rbxassetid://75118020083926" },
			Body = { color = "rbxassetid://90018895426012", normal = "rbxassetid://84063571761459" },
			Limbs = { color = "rbxassetid://76021961664339", normal = "rbxassetid://94011461040911" },
		},
		meshes = ids(RATKING_MESHES),
		turn = 180,
	} :: BossModel,
	-- Сфинкс-лежебока (модель v2): карты загружены 2026-11-12 (assets/textures/art/IDS.md). Меши — после импорта
	-- assets/models/Boss4_Sphinx_game.fbx (scripts/bind_meshes.py); turn 180 — как у FBX пса с теми же настройками
	-- экспорта, проверить после импорта.
	[4] = {
		name = "Сфинкс-лежебока",
		maps = {
			Head = { color = "rbxassetid://70978354612891", normal = "rbxassetid://100113950885464" },
			Body = { color = "rbxassetid://137503317136619", normal = "rbxassetid://130409217850998" },
			Limbs = { color = "rbxassetid://79180327028035", normal = "rbxassetid://130003429663958" },
		},
		meshes = ids(SPHINX_MESHES),
		turn = 180,
	} :: BossModel,
	-- Йети-коллекционер (D64, шаг 2): меши — модель Open Cloud 115856961352655, карты 1024² загружены 2026-11-24
	-- (assets/textures/art/Boss5Yeti_maps.json). turn 180 — сверено в Studio по центрам 31 части (отклонение 0.004 ст.).
	[5] = {
		name = "Йети-коллекционер",
		maps = {
			Head = { color = "rbxassetid://102344471750384", normal = "rbxassetid://126413183189503" },
			Body = { color = "rbxassetid://93942245151760", normal = "rbxassetid://76219191547989" },
			Limbs = { color = "rbxassetid://110096942919118", normal = "rbxassetid://84860610722819" },
		},
		meshes = ids(YETI_MESHES),
		turn = 180,
	} :: BossModel,
	-- Король-дракон (модель v7, риг 53 кости, этап C 2026-11-15): меши — модели Open Cloud 139253334200457 (части)
	-- и 104012151110699 (перепонки со скелетом крыльев), карты — 6 групп по 1024². turn 180 проверен по костям
	-- перепонок: все 14 — в точках вращения суставов (±0.0001 ст.). Карты — версия 3.1 (утверждена владельцем
	-- 2026-11-16, этап C.2): цвет — assets/textures/art/boss10_v31 (Boss10v31_maps.json), нормали — v1 (Boss10_maps.json),
	-- металл, шероховатость и маска свечения кристаллов — v2 (Boss10v2_maps.json). Прежние v1 — Boss10_maps.json.
	[10] = {
		name = "Король-дракон",
		maps = {
			BodyA = {
				color = "rbxassetid://97824864734119",
				normal = "rbxassetid://97740415846196",
				metal = "rbxassetid://127965315052836",
				rough = "rbxassetid://75191317775917",
				glow = "rbxassetid://96235359390691",
			},
			BodyB = {
				color = "rbxassetid://118049841751082",
				normal = "rbxassetid://128434721194884",
				metal = "rbxassetid://121361927122142",
				rough = "rbxassetid://125732338054485",
				glow = "rbxassetid://138631968228834",
			},
			Head = {
				color = "rbxassetid://109255891740493",
				normal = "rbxassetid://125790867034344",
				metal = "rbxassetid://109310974878078",
				rough = "rbxassetid://124257029309690",
				glow = "rbxassetid://117202839310093",
			},
			Front = {
				color = "rbxassetid://127425167160086",
				normal = "rbxassetid://121558917166924",
				metal = "rbxassetid://136992338912413",
				rough = "rbxassetid://128600824623045",
				glow = "rbxassetid://103680150010354",
			},
			Hind = {
				color = "rbxassetid://112563599144014",
				normal = "rbxassetid://133886269615008",
				metal = "rbxassetid://109390347258859",
				rough = "rbxassetid://98911529472181",
				glow = "rbxassetid://97671711735950",
			},
			Tail = {
				color = "rbxassetid://135526331200356",
				normal = "rbxassetid://90440010286672",
				metal = "rbxassetid://119895837358586",
				rough = "rbxassetid://103015669978885",
				glow = "rbxassetid://108147856316601",
			},
		},
		meshes = ids(DRAGON_MESHES),
		turn = 180,
	} :: BossModel,
})
