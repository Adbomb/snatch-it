"""D48 v2 — концепт музея игрока: галерея с нишами-экспозициями наверху, павильон с круглой сейфовой дверью
и прямая лестница вниз, подземное хранилище (сейф коллекции, терминал инвентаря, центр безопасности, архив).
Только концепт: в игру ничего не попадает, в Roblox ничего не загружается.

Всё собрано из деталей Roblox (d48_kit: Block / Cylinder / Ball / Wedge) — в игре музей строится тем же списком
кодом (World/ModelBuilder), без мешей. Выгрузка: assets/concepts/d48/v2/bricks/museum.json (+ учёт деталей).
Координаты — как у участка (центр участка на уровне пола зала, вход −Z, трава y = −1.3); внешний контур — как
у нынешнего здания (36 × 33.4, MuseumHall: HW 18, фасад −12.7, задняя стена 20.7), участок 44 × 44.

Запуск: blender --background --factory-startup --python scripts/blender/d48_museum.py -- <репо> [--fast] [виды]
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import d48_devices as D  # noqa: E402
import d48_kit as K  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
REPO = os.path.abspath(argv[0]) if argv else os.getcwd()
FAST = "--fast" in argv
ONLY = [a for a in argv[1:] if not a.startswith("--")]
OUT = os.path.join(REPO, "assets", "concepts", "d48", "v2")
RENDERS = os.path.join(OUT, "renders")
os.makedirs(RENDERS, exist_ok=True)

# ── Размеры (стады) ─────────────────────────────────────────────────────────────────────────────────────────────
G = -1.3
HW, FZ, BZ, T = 18.0, -12.7, 20.7, 1.4
IX, IZ0, IZ1 = HW - T, FZ + T, BZ - T  # внутри: x ±16.6, z −11.3…19.3
CEIL = 16.0
DOOR, DOORH = 6.0, 10.0
VF, SLAB = -13.0, 1.4  # пол хранилища; перекрытие y −1.4…0
VCEIL = -1.8  # низ потолочных панелей хранилища
ST0, STW = 3.0, 2.6  # лестница: верхний край z = 3, полуширина 2.6; 12 ступеней 1 × 1 вниз к задней стене
WELL_X, WELL_Z1 = 2.8, 11.0  # проём в полу зала над лестницей: x ±2.8, z 3…11 (над головой ≥ 6.6)
PV_X, PV_Z0, PV_Z1, PV_H = 4.4, 2.4, 11.6, 9.0  # павильон над проёмом
BAY_Z = (-1.6, 6.2, 14.0)  # центры ниш вдоль боковых стен
PIL_Z = (-5.5, 2.3, 10.1, 17.9)  # пилястры между нишами
PED_D = 3.4  # центр постамента — в 3.4 от стены (x ±13.2)
LASERS = {"Entrance": (-8.6, 12.0), "Gallery": (-6.4, 9.2)}  # размеченные места лазера: z и длина поперёк прохода
PORTICO_Z = -23.0

C = {
    "wall": "F4EFE4", "pilaster": "FBF8F1", "gold": "E9B43C", "goldDeep": "C98E1E", "navy": "26345E",
    "navyDark": "1A2440", "floor": "EFE6D3", "runner": "B8283A", "ceiling": "D3E3F2", "beam": "F7F2E8",
    "backdrop": "2E4377", "steelBlue": "3A5A8C", "steel": "A7B6C8", "steelDark": "5E7186", "cyan": "39E1FF",
    "warm": "FFD88A", "roof": "D9705A", "grass": "7FC75A", "path": "E9E2D2", "step": "E8DCC2",
    "vWall": "1F3A63", "vPanel": "2C5283", "vFloor": "17223D", "vCeil": "131D33", "screen": "1D6FE0",
    "white": "FFFFFF", "green": "6BF27A", "red": "F0473C", "plant": "4FB45A", "plantDark": "3C8F47",
    "stepCool": "93A7C7", "disk": "AEBCD0", "locker": "8EA2BD",
}
RARITY = {"Common": "C4C0CE", "Rare": "4FA6EA", "Epic": "B266F5", "Legendary": "F7B731", "Secret": "8B6CF7"}


def W(side, a, b):
    """Полоса на расстоянии a…b от боковой стены (side −1 — стена x = −16.6, +1 — x = +16.6) → (x0, x1)."""
    x0, x1 = side * (IX - a), side * (IX - b)
    return (min(x0, x1), max(x0, x1))


def soft(code, step=2.0, dark=0.08):
    return K.rings(code, step, dark, 0.5)


scene = K.reset("WORKBENCH" if FAST else "EEVEE", 64)

# ── Земля, участок, дорожка (в бюджет музея не входят) ─────────────────────────────────────────────────────────
K.group("Ground")
GRASS = K.rings(C["grass"], 4.0, 0.12)
for name, x0, x1, z0, z1 in (("GrassF", -80, 80, -80, FZ), ("GrassB", -80, 80, BZ + 1, 50),
                             ("GrassL", -80, -HW - 1, FZ, BZ + 1), ("GrassR", HW + 1, 80, FZ, BZ + 1)):
    K.box(name, x0, x1, G - 2, G, z0, z1, C["grass"], look=GRASS, record=False, bevel=0,
          cname="GroundNear" if name == "GrassR" else "Ground")
K.group("PlotLines")
for name, x0, x1, z0, z1 in (("PlotN", -22, 22, -22.15, -21.85), ("PlotS", -22, 22, 21.85, 22.15),
                             ("PlotW", -22.15, -21.85, -22, 22), ("PlotE", 21.85, 22.15, -22, 22)):
    K.box(name, x0, x1, G, G + 0.06, z0, z1, "FFFFFF", record=False, bevel=0)
K.group("Ground")
K.box("Path", -4, 4, G, G + 0.08, -70, PORTICO_Z, C["path"], record=False, bevel=0.02)
K.group("SectionEarth")  # только для разреза: земля за хранилищем
K.box("EarthBack", -60, -HW - 0.6, VF - 4, G - 2, -40, 50, "8A6A4A", record=False, bevel=0,
      look=K.rings("8A6A4A", 3.0, 0.1))
K.box("EarthUnder", -60, 60, VF - 6, VF - 1.6, -40, 50, "7A5C3F", record=False, bevel=0)

# ── Снаружи: подиум, портик, фронтон, вход (как сейчас, D36) ───────────────────────────────────────────────────
K.group("Exterior")
WALL = soft(C["wall"])
for name, x0, x1, z0, z1 in (("PodiumL", -HW - 1, -HW, FZ, BZ + 1), ("PodiumR", HW, HW + 1, FZ, BZ + 1),
                             ("PodiumB", -HW - 1, HW + 1, BZ, BZ + 1)):
    K.box(name, x0, x1, G, -0.02, z0, z1, C["wall"], look=WALL)
K.box("PorticoFloor", -16, 16, G, 0, PORTICO_Z + 2.1, FZ, C["floor"], look=soft(C["floor"], 4.0))
for i in range(3):
    K.box(f"PorticoStep{i}", -16, 16, G, G + (i + 1) * (-G / 3), PORTICO_Z + i * 0.7, PORTICO_Z + 2.1, C["floor"])
for cx in (-14.0, -8.0, 8.0, 14.0):
    K.box("ColBase", cx - 1.3, cx + 1.3, 0, 0.6, -20.7, -18.1, C["pilaster"])
    K.box("ColShaft", cx - 0.95, cx + 0.95, 0.6, 13.0, -20.35, -18.45, C["wall"], look=WALL)
    K.box("ColCap", cx - 1.25, cx + 1.25, 13.0, 13.6, -20.65, -18.15, C["gold"])
    K.box("ColCap2", cx - 1.45, cx + 1.45, 13.6, 14.0, -20.85, -17.95, C["pilaster"])
K.box("Entablature", -16.5, 16.5, 14.0, 16.0, -22.6, FZ, C["pilaster"])
K.box("Frieze", -16.6, 16.6, 14.5, 15.3, -22.75, -22.5, C["gold"])
for k, (w, y0) in enumerate(((16.5, 16.0), (13.5, 17.2), (10.5, 18.4), (7.5, 19.6), (4.5, 20.8))):
    K.box(f"Pediment{k}", -w, w, y0, y0 + 1.2, -22.6 + 0.2 * k, -21.0, C["pilaster"])
K.cyl("Emblem", (0, 18.3, -22.85), 0.5, 4.0, C["gold"], "z")
K.cyl("EmblemIn", (0, 18.3, -23.2), 0.3, 2.8, C["warm"], "z", "Neon", glow=2.5)
for x0, x1, y0, y1 in ((-DOOR - 1.0, -DOOR, 0, DOORH + 1.0), (DOOR, DOOR + 1.0, 0, DOORH + 1.0),
                       (-DOOR - 1.0, DOOR + 1.0, DOORH, DOORH + 1.0)):
    K.box("DoorFrame", x0, x1, y0, y1, FZ - 0.5, FZ + 0.3, C["gold"])
for sx in (-1, 1):
    K.box("Lantern", sx * 9.2 - 0.5, sx * 9.2 + 0.5, 4.0, 7.0, FZ - 0.8, FZ - 0.2, C["warm"], "Neon", glow=3)
    K.box("LanternCap", sx * 9.2 - 0.7, sx * 9.2 + 0.7, 7.0, 7.4, FZ - 1.0, FZ - 0.1, C["gold"])

# ── Оболочка зала: пол с проёмом, стены, пояса, потолок, крыша ─────────────────────────────────────────────────
K.group("Shell")
FLOOR = soft(C["floor"], 4.0, 0.07)
for name, x0, x1, z0, z1 in (("FloorFront", -HW, HW, FZ, ST0), ("FloorL", -HW, -WELL_X, ST0, BZ),
                             ("FloorR", WELL_X, HW, ST0, BZ), ("FloorBack", -WELL_X, WELL_X, WELL_Z1, BZ)):
    K.box(name, x0, x1, -SLAB, 0, z0, z1, C["floor"], look=FLOOR, bevel=0.02)
K.box("WallL", -HW, -IX, 0, CEIL + 1.4, FZ, BZ, C["wall"], look=WALL)
K.box("WallBack", -IX, IX, 0, CEIL + 1.4, IZ1, BZ, C["wall"], look=WALL)
K.group("WallsNear")
K.box("WallR", IX, HW, 0, CEIL + 1.4, FZ, BZ, C["wall"], look=WALL)
K.box("WallFrontL", -IX, -DOOR, 0, CEIL + 1.4, FZ, IZ0, C["wall"], look=WALL)
K.box("WallFrontR", DOOR, IX, 0, CEIL + 1.4, FZ, IZ0, C["wall"], look=WALL)
K.box("WallFrontTop", -DOOR, DOOR, DOORH, CEIL + 1.4, FZ, IZ0, C["wall"], look=WALL)
K.group("Shell")
for name, x0, x1, z0, z1 in (("L", -IX, -IX + 0.2, IZ0, IZ1), ("R", IX - 0.2, IX, IZ0, IZ1),
                             ("B", -IX, IX, IZ1 - 0.2, IZ1)):
    K.group("WallsNear" if name == "R" else "Shell")
    K.box("Base" + name, x0, x1, 0, 1.0, z0, z1, C["navy"])
    K.box("Belt" + name, x0, x1, 12.4, 12.7, z0, z1, C["gold"])
    K.box("Cornice" + name, x0 - (0.3 if name == "R" else 0), x1 + (0.3 if name == "L" else 0), 15.2, 16.0,
          z0 - (0.3 if name == "B" else 0), z1, C["pilaster"])
for x0, x1 in ((-IX, -DOOR - 1.0), (DOOR + 1.0, IX)):
    K.group("WallsNear" if x0 > 0 else "Shell")
    K.box("BaseF", x0, x1, 0, 1.0, IZ0, IZ0 + 0.2, C["navy"])
    K.box("BeltF", x0, x1, 12.4, 12.7, IZ0, IZ0 + 0.2, C["gold"])
for sx in (-1, 1):  # тёплая подсветка карниза
    K.group("WallsNear" if sx > 0 else "Shell")
    x0, x1 = W(sx, 0.2, 0.45)
    K.box("Cove", x0, x1, 12.7, 12.9, IZ0 + 0.2, IZ1 - 0.2, C["warm"], "Neon", glow=2.5, bevel=0)
K.group("Ceiling")
K.box("CeilingSlab", -HW, HW, CEIL + 1.4, CEIL + 2.4, FZ, BZ, C["ceiling"])
K.box("CeilingBase", -IX, IX, CEIL + 0.4, CEIL + 1.4, IZ0, IZ1, C["ceiling"], bevel=0)
for x in (-11.0, -5.5, 5.5, 11.0):
    K.box("BeamZ", x - 0.5, x + 0.5, CEIL - 0.4, CEIL + 0.4, IZ0, IZ1, C["beam"])
for z in PIL_Z[:3]:
    K.box("BeamX", -IX, IX, CEIL - 0.35, CEIL + 0.35, z - 0.5, z + 0.5, C["beam"])
K.box("Skylight", -5.0, 5.0, CEIL + 0.39, CEIL + 0.4, -10.5, 10.0, "EAF7FF", "Neon", glow=2.0, bevel=0)
for x0, x1, z0, z1 in ((-5.5, 5.5, -11.0, -10.5), (-5.5, 5.5, 10.0, 10.5), (-5.5, -5.0, -10.5, 10.0),
                       (5.0, 5.5, -10.5, 10.0)):
    K.box("SkylightRim", x0, x1, CEIL - 0.6, CEIL - 0.3, z0, z1, C["gold"])
K.group("Roof")
ROOF = K.rings(C["roof"], 2.0, 0.12)
for k, w in enumerate((19.5, 16.0, 12.5, 9.0, 5.5, 2.0)):
    K.box(f"Roof{k}", -w, w, CEIL + 2.4 + k * 1.1, CEIL + 3.5 + k * 1.1, FZ - 0.4, BZ + 0.6, C["roof"], look=ROOF)
K.box("RoofLantern", -4.5, 4.5, CEIL + 9.0, CEIL + 10.4, -9.5, 9.0, "BDEBFF", "Glass", alpha=0.55)

# ── Ниши-экспозиции: 6 официальных мест (столько витрин сейчас, GameConfig.Museum.SlotsByLevel) ──────────────────
for sx in (-1, 1):
    K.group("BaysNear" if sx > 0 else "Bays")
    for z in PIL_Z:  # пилястры между нишами: база, ствол, капитель
        K.box("PilBase", *W(sx, 0, 1.55), 0, 0.9, z - 0.95, z + 0.95, C["navy"])
        K.box("Pilaster", *W(sx, 0, 1.3), 0.9, 11.6, z - 0.8, z + 0.8, C["pilaster"])
        K.box("PilCap", *W(sx, 0, 1.55), 11.6, 12.4, z - 0.95, z + 0.95, C["gold"])

PLACES = []


def bay(sx, i, item=None):
    """Ниша: фон, арка-перемычка, постамент, табличка, светильник. item — (ключ, имя, редкость, доход) или None."""
    K.group("BaysNear" if sx > 0 else "Bays")
    cz = BAY_Z[i]
    z0, z1 = PIL_Z[i] + 0.8, PIL_Z[i + 1] - 0.8
    K.box("Backdrop", *W(sx, 0, 0.3), 0.9, 9.2, z0 + 0.1, z1 - 0.1, C["backdrop"], look=K.rings(C["backdrop"], 1.0,
                                                                                                    0.1, 0.75))
    K.box("Header", *W(sx, 0, 1.1), 9.2, 10.4, z0, z1, C["pilaster"])
    K.box("HeaderStep", *W(sx, 0.3, 0.75), 8.6, 9.2, z0 + 0.1, z1 - 0.1, C["gold"])
    # светильник: кронштейн из перемычки и плафон над постаментом
    K.box("LampArm", *W(sx, 1.1, PED_D + 0.2), 9.75, 10.0, cz - 0.15, cz + 0.15, C["gold"])
    K.cyl("LampHead", (sx * (IX - PED_D), 9.55, cz), 0.6, 0.8, C["navyDark"], "y")
    # постамент: ступенчатый силуэт, верх — на высоте 3 (как ShowcaseSize)
    px = sx * (IX - PED_D)
    K.box("PedBase", px - 2.8, px + 2.8, 0, 0.5, cz - 2.8, cz + 2.8, C["navy"])
    K.box("PedBody", px - 2.4, px + 2.4, 0.5, 2.6, cz - 2.4, cz + 2.4, C["pilaster"], look=soft(C["pilaster"], 0.8, 0.1))
    K.box("PedCap", px - 2.65, px + 2.65, 2.6, 2.85, cz - 2.65, cz + 2.65, C["gold"])
    K.box("PedTop", px - 2.5, px + 2.5, 2.85, 3.0, cz - 2.5, cz + 2.5, C["pilaster"])
    # табличка на стороне к проходу и полоса редкости
    face = px - sx * 2.4
    fx0, fx1 = (face - 0.12, face) if sx > 0 else (face, face + 0.12)
    K.box("Plaque", fx0, fx1, 1.0, 2.2, cz - 1.5, cz + 1.5, C["navyDark"], bevel=0.03)
    strip = RARITY[item[2]] if item else C["cyan"]
    K.box("PlaqueStrip", fx0 - (0.03 if sx > 0 else 0), fx1 + (0 if sx > 0 else 0.03), 2.2, 2.32, cz - 1.5, cz + 1.5,
          strip, "Neon", glow=2.5, bevel=0)
    tf = "-x" if sx > 0 else "+x"
    tx = face - sx * 0.14
    if item:
        ex = "ExhibitNear" if sx > 0 else "Exhibit"
        K.box("PlaceGlow", px - 1.9, px + 1.9, 3.0, 3.05, cz - 1.9, cz + 1.9, C["gold"], "Glass", alpha=0.55, bevel=0,
              cname=ex)
        K.text("PlaqueName", item[1], (tx, 1.85, cz), 0.32, "FFFFFF", tf, cname=ex)
        K.text("PlaqueIncome", f"+{item[3]} $/сек", (tx, 1.38, cz), 0.3, "7CFF6B", tf, cname=ex)
    else:
        K.box("PlaceGlow", px - 1.9, px + 1.9, 3.0, 3.05, cz - 1.9, cz + 1.9, C["cyan"], "Glass", alpha=0.45,
              bevel=0)
        K.part("PlaceHolo", "Block", (0.9, 0.9, 0.9), (px, 4.3, cz), C["cyan"], "Glass", alpha=0.5,
               rot=K.rot_y(45) @ K.rot_x(35.26) @ K.rot_z(45), bevel=0.04, collide=False)
        K.text("PlaqueFree", "СВОБОДНО", (tx, 1.82, cz), 0.3, C["cyan"], tf, glow=1.2)
        K.text("PlaqueHint", "место для экспоната", (tx, 1.38, cz), 0.2, "C9D6F2", tf, weight="Bold")
    K.game_light("SpotLight", (px, 9.3, cz), 14, 1.6 if item else 0.6, C["warm"], 55)
    PLACES.append((sx, i, px, cz, item))


ITEMS = {(1, 0): ("Moai", "ГОЛОВА МОАИ", "Common", 16), (-1, 1): ("TutMask", "МАСКА ТУТАНХАМОНА", "Epic", 150),
         (1, 2): ("Vase", "ВАЗА", "Rare", 25)}
for sx in (-1, 1):
    for i in range(3):
        bay(sx, i, ITEMS.get((sx, i)))

# ── Проход: дорожка, медальон, разметка лазеров ────────────────────────────────────────────────────────────────
K.group("Aisle")
K.box("Runner", -3.2, 3.2, 0, 0.08, IZ0, PV_Z0 - 0.3, C["runner"], bevel=0.01)
for sx in (-1, 1):
    K.box("RunnerEdge", sx * 3.2 - 0.18, sx * 3.2 + 0.18, 0, 0.1, IZ0, PV_Z0 - 0.3, C["gold"], bevel=0.01)
K.cyl("MedalRing", (0, 0.11, -1.4), 0.06, 6.6, C["gold"], "y", bevel=0.01)
K.cyl("MedalCore", (0, 0.16, -1.4), 0.04, 5.4, C["navy"], "y", bevel=0)
K.cyl("MedalStar", (0, 0.2, -1.4), 0.04, 2.0, C["gold"], "y", bevel=0)
for name, (lz, length) in LASERS.items():
    D.laser_sockets((0, 0, lz), 0, length, prefix=f"LaserMark{name}")

# ── Входной зал: сундук слева, стенд музея справа, растения у двери ───────────────────────────────────────────
K.group("Foyer")
cxz = (-12.0, -9.7)  # сундук — на месте нынешнего (PartBuilder: x −12, у фасада), замком в зал
cx, cz = cxz
K.box("Chest", cx - 2.0, cx + 2.0, 0, 1.9, cz - 1.5, cz + 1.5, "3E7BE0")
K.box("ChestLid", cx - 2.1, cx + 2.1, 1.9, 2.5, cz - 1.6, cz + 1.6, "5A93F0")
K.box("ChestTop", cx - 1.8, cx + 1.8, 2.5, 2.85, cz - 1.3, cz + 1.3, "3E7BE0")
for bx in (-1.2, 1.2):
    K.box("ChestBand", cx + bx - 0.18, cx + bx + 0.18, 0, 2.9, cz - 1.62, cz + 1.62, C["gold"])
K.box("ChestLock", cx - 0.45, cx + 0.45, 1.2, 2.2, cz + 1.5, cz + 1.7, C["gold"])
K.box("ChestSlot", cx - 1.2, cx + 1.2, 2.3, 2.4, cz + 1.6, cz + 1.66, C["cyan"], "Neon", glow=2.5, bevel=0)
sx_, sz_ = 12.0, -9.6
K.box("StandBase", sx_ - 0.9, sx_ + 0.9, 0, 0.6, sz_ - 0.7, sz_ + 0.7, C["navy"])
K.box("StandPost", sx_ - 0.3, sx_ + 0.3, 0.6, 3.0, sz_ - 0.3, sz_ + 0.3, C["gold"])
board = K.rot_x(-20)
K.part("StandBoard", "Block", (3.2, 2.0, 0.25), (sx_, 3.8, sz_ + 0.1), C["navyDark"], rot=board, bevel=0.05)
K.part("StandScreen", "Block", (2.9, 1.7, 0.05), (sx_, 3.8 + 0.05, sz_ + 0.27), C["screen"], "Neon", rot=board,
       glow=1.2, bevel=0)
K.text("StandText", "МУЗЕЙ · УР. 3", (sx_, 4.15, sz_ + 0.36), 0.3, "FFFFFF", "+z")
K.text("StandText2", "6 мест · +191 $/сек", (sx_, 3.62, sz_ + 0.18), 0.22, "7CFF6B", "+z", weight="Bold")
for px_ in (-8.4, 8.4):
    K.cyl("Pot", (px_, 0.7, -9.9), 1.4, 1.6, C["pilaster"], "y")
    K.cyl("PotRim", (px_, 1.5, -9.9), 0.25, 1.9, C["gold"], "y")
    K.ball("Topiary", (px_, 2.75, -9.9), 2.3, C["plant"])
    K.ball("TopiaryTop", (px_, 4.15, -9.9), 1.3, C["plantDark"])

# ── Павильон «Хранилище» над лестницей и открытая круглая сейфовая дверь ───────────────────────────────────────
K.group("Pavilion")
VAULTM = K.rings(C["steelBlue"], 1.0, 0.1)
K.box("PvJambL", -PV_X, -STW, 0, 7.2, PV_Z0, PV_Z0 + 0.6, C["steelBlue"], look=VAULTM)
K.box("PvJambR", STW, PV_X, 0, 7.2, PV_Z0, PV_Z0 + 0.6, C["steelBlue"], look=VAULTM)
K.box("PvLintel", -PV_X, PV_X, 7.2, PV_H, PV_Z0, PV_Z0 + 0.6, C["steelBlue"], look=VAULTM)
for x0, x1, y0, y1 in ((-STW - 0.3, -STW, 0, 7.5), (STW, STW + 0.3, 0, 7.5), (-STW - 0.3, STW + 0.3, 7.2, 7.5)):
    K.box("PvFrame", x0, x1, y0, y1, PV_Z0 - 0.15, PV_Z0 + 0.1, C["gold"])
for sx in (-1, 1):
    K.box("PvGlow", sx * 3.3 - 0.1, sx * 3.3 + 0.1, 0.5, 6.8, PV_Z0 - 0.1, PV_Z0, C["cyan"], "Neon", glow=2.5, bevel=0)
K.box("PvSign", -3.3, 3.3, 7.75, 8.75, PV_Z0 - 0.15, PV_Z0, C["navyDark"])
K.text("PvSignText", "ХРАНИЛИЩЕ", (0, 8.25, PV_Z0 - 0.17), 0.62, C["gold"], "-z", glow=1.4)
K.box("PvSideL", -PV_X, -PV_X + 0.6, 0, PV_H, PV_Z0 + 0.6, PV_Z1 - 0.6, C["steelBlue"], look=VAULTM)
for sx in (-1, 1):
    K.box("PvFloor", *sorted((sx * WELL_X, sx * (PV_X - 0.6))), 0, 0.06, PV_Z0 + 0.6, PV_Z1 - 0.6, C["navy"], bevel=0)
K.box("PvBack", -PV_X, PV_X, 0, PV_H, PV_Z1 - 0.6, PV_Z1, C["steelBlue"], look=VAULTM)
K.group("PavilionNear")
K.box("PvSideR", PV_X - 0.6, PV_X, 0, PV_H, PV_Z0 + 0.6, PV_Z1 - 0.6, C["steelBlue"], look=VAULTM)
K.group("Pavilion")
K.box("PvRoof", -PV_X - 0.4, PV_X + 0.4, PV_H, PV_H + 0.6, PV_Z0 - 0.4, PV_Z1 + 0.4, C["pilaster"])
K.box("PvCornice", -PV_X - 0.6, PV_X + 0.6, PV_H + 0.6, PV_H + 0.9, PV_Z0 - 0.6, PV_Z1 + 0.6, C["gold"])
K.box("PvCrown", -3.4, 3.4, PV_H + 0.9, PV_H + 1.7, PV_Z0 + 0.6, PV_Z1 - 0.6, C["navy"])
for sx in (-1, 1):
    K.group("PavilionNear" if sx > 0 else "Pavilion")
    K.box("PvBase", sx * PV_X - (0 if sx > 0 else 0.2), sx * PV_X + (0.2 if sx > 0 else 0), 0, 0.8, PV_Z0 + 0.6,
          PV_Z1, C["navy"])
    K.box("PvEdge", sx * PV_X - (0.05 if sx > 0 else 0.25), sx * PV_X + (0.25 if sx > 0 else 0.05), 0.8, PV_H,
          PV_Z1 - 0.5, PV_Z1 + 0.1, C["gold"])
K.group("VaultDoor")
# дверь открыта на 90°: шарнир — правый передний угол павильона, лицо двери смотрит в проход
HX, HZ, DR = PV_X, PV_Z0, 3.5
dcx, dcz, dcy = HX + 0.45, HZ - DR - 0.1, 0.35 + DR
K.cyl("DoorRing", (dcx + 0.1, dcy, dcz), 0.7, 2 * DR + 0.5, C["gold"], "x")
K.cyl("DoorDisk", (dcx - 0.2, dcy, dcz), 0.6, 2 * DR - 0.3, C["disk"], "x")
K.cyl("DoorGlow", (dcx - 0.45, dcy, dcz), 0.1, 2 * DR - 1.2, C["cyan"], "x", "Neon", glow=2.0, bevel=0)
K.cyl("DoorCore", (dcx - 0.6, dcy, dcz), 0.3, 2.6, C["gold"], "x")
K.cyl("DoorHub", (dcx - 0.85, dcy, dcz), 0.3, 1.0, C["steelDark"], "x")
for k in range(3):
    K.part("DoorSpoke", "Block", (0.25, 3.6, 0.3), (dcx - 0.95, dcy, dcz), C["goldDeep"], rot=K.rot_x(60 * k))
for k in range(8):
    a = math.radians(22.5 + 45 * k)
    K.cyl("DoorBolt", (dcx - 0.55, dcy + math.sin(a) * 2.75, dcz + math.cos(a) * 2.75), 0.2, 0.45, C["gold"], "x")
K.cyl("DoorHinge", (HX + 0.25, 1.8, HZ - 0.25), 1.0, 0.6, C["steelDark"], "y")
K.cyl("DoorHinge2", (HX + 0.25, 6.0, HZ - 0.25), 1.0, 0.6, C["steelDark"], "y")

# ── Задняя стена: эмблема и знамёна ────────────────────────────────────────────────────────────────────────────
K.group("BackWall")
K.cyl("BackEmblem", (0, 12.3, IZ1 - 0.25), 0.5, 4.2, C["gold"], "z")
K.cyl("BackEmblemIn", (0, 12.3, IZ1 - 0.55), 0.2, 3.0, C["navy"], "z")
for sx in (-1, 1):
    K.box("BannerRod", sx * 8.0 - 1.9, sx * 8.0 + 1.9, 12.8, 13.1, IZ1 - 0.5, IZ1 - 0.2, C["gold"])
    K.box("Banner", sx * 8.0 - 1.6, sx * 8.0 + 1.6, 6.0, 12.8, IZ1 - 0.35, IZ1 - 0.2, C["backdrop"])

# ── Лестница вниз: 12 ступеней 1 × 1 к задней стене, стеклянные перила, подсветка ─────────────────────────────
K.group("Stair")
STEP = soft(C["stepCool"], 2.0, 0.07)
for k in range(1, 13):
    K.box(f"Step{k}", -STW, STW, VF, -k, ST0 + k - 1, ST0 + k, C["stepCool"], look=STEP, bevel=0.03)
slope = 45.0  # линия носков ступеней: (z 3, y −1) → (z 14, y −12)
mid = Vector((0, -6.5 + 1.2, ST0 + 5.5))
length = 11.0 * math.sqrt(2) + 1.5
for sx in (-1, 1):
    rot = K.rot_x(slope)
    K.part("RailGlass", "Block", (0.12, 2.1, length), (sx * (STW + 0.1), mid.y, mid.z), "BDEBFF", "Glass",
           alpha=0.3, rot=rot, bevel=0)
    K.part("RailTop", "Block", (0.3, 0.25, length), (sx * (STW + 0.1), mid.y + 1.15, mid.z), C["gold"], rot=rot,
           bevel=0.03)

# ── Подземное хранилище ────────────────────────────────────────────────────────────────────────────────────────
K.group("Vault")
VW = K.rings(C["vWall"], 1.0, 0.08)
K.box("VFloor", -HW, HW, VF - 1.4, VF, FZ, BZ, C["vFloor"], look=K.rings(C["vFloor"], 3.0, 0.16), bevel=0.02)
K.box("VWallL", -HW, -IX, VF, -SLAB, FZ, BZ, C["vWall"], look=VW)
K.group("VaultFront")
K.box("VWallF", -IX, IX, VF, -SLAB, FZ, IZ0, C["vWall"], look=VW)
K.group("Vault")
K.box("VWallB", -IX, IX, VF, -SLAB, IZ1, BZ, C["vWall"], look=VW)
K.group("VaultNear")
K.box("VWallR", IX, HW, VF, -SLAB, FZ, BZ, C["vWall"], look=VW)
K.group("Vault")
for name, x0, x1, z0, z1 in (("L", -IX, -IX + 0.25, IZ0, IZ1), ("R", IX - 0.25, IX, IZ0, IZ1),
                             ("F", -IX, IX, IZ0, IZ0 + 0.25)):
    K.box("VBase" + name, x0, x1, VF, VF + 0.5, z0, z1, C["gold"],
          cname={"R": "VaultNear", "F": "VaultFront"}.get(name, "Vault"))
for x in (-6.0, 6.0):  # золотые линии пола
    K.box("VInlay", x - 0.12, x + 0.12, VF, VF + 0.04, IZ0 + 0.3, ST0 - 0.5, C["gold"], bevel=0)
K.group("VaultCeiling")
for name, x0, x1, z0, z1 in (("VCeilF", -IX, IX, IZ0, ST0), ("VCeilL", -IX, -WELL_X, ST0, IZ1),
                             ("VCeilR", WELL_X, IX, ST0, IZ1), ("VCeilB", -WELL_X, WELL_X, WELL_Z1, IZ1)):
    K.box(name, x0, x1, VCEIL, -SLAB, z0, z1, C["vCeil"], bevel=0)
for x in (-10.0, 10.0):
    K.box("VLine", x - 0.15, x + 0.15, VCEIL - 0.12, VCEIL, IZ0 + 0.5, IZ1 - 0.5, C["cyan"], "Neon", glow=3, bevel=0)
K.box("VLineX", -IX + 0.5, IX - 0.5, VCEIL - 0.12, VCEIL, -4.0, -3.7, C["cyan"], "Neon", glow=3, bevel=0)

# сейф коллекции на задней стене: виден сразу, как спускаешься
K.group("Safe")
SY = VF + 5.0
K.box("SafePlate", -5.2, 5.2, VF, VF + 10.2, IZ1 - 0.4, IZ1, C["navyDark"], bevel=0.05)
K.cyl("SafeRing", (0, SY, IZ1 - 0.6), 0.4, 8.4, C["gold"], "z")
K.cyl("SafeGlow", (0, SY, IZ1 - 0.85), 0.1, 7.9, C["cyan"], "z", "Neon", glow=2.5, bevel=0)
K.cyl("SafeDisk", (0, SY, IZ1 - 1.1), 0.6, 7.4, C["disk"], "z")
K.cyl("SafeCore", (0, SY, IZ1 - 1.55), 0.3, 2.6, C["gold"], "z")
K.cyl("SafeHub", (0, SY, IZ1 - 1.85), 0.3, 1.0, C["steelDark"], "z")
for k in range(3):
    K.part("SafeSpoke", "Block", (3.8, 0.28, 0.25), (0, SY, IZ1 - 1.95), C["goldDeep"], rot=K.rot_z(60 * k))
for k in range(8):
    a = math.radians(22.5 + 45 * k)
    K.cyl("SafeBolt", (math.cos(a) * 3.1, SY + math.sin(a) * 3.1, IZ1 - 1.45), 0.2, 0.5, C["gold"], "z")
for sx in (-1, 1):
    K.box("SafeLight", sx * 5.6 - 0.2, sx * 5.6 + 0.2, VF, VF + 9.6, IZ1 - 0.3, IZ1, C["warm"], "Neon", glow=3,
          bevel=0)
K.box("SafeSign", -3.6, 3.6, VF + 9.3, VF + 10.0, IZ1 - 0.55, IZ1 - 0.4, C["navy"])
K.text("SafeSignText", "СЕЙФ КОЛЛЕКЦИИ", (0, VF + 9.65, IZ1 - 0.57), 0.4, C["gold"], "-z", glow=1.3)

# терминал инвентаря — на торце лестницы, лицом к главному залу хранилища
K.group("Terminal")
K.box("TermFrame", -2.45, 2.45, VF + 3.6, VF + 9.6, ST0 - 0.3, ST0, C["navyDark"])
K.box("TermScreen", -2.15, 2.15, VF + 3.9, VF + 9.3, ST0 - 0.36, ST0 - 0.3, C["screen"], "Neon", glow=1.1, bevel=0)
for name, x0, x1, y0, y1 in (("IconBody", -1.0, 1.0, 5.3, 6.9), ("IconHandle", -0.45, 0.45, 6.9, 7.3),
                             ("IconBand", -1.0, 1.0, 6.05, 6.2)):
    K.box(name, x0, x1, VF + y0, VF + y1, ST0 - 0.42, ST0 - 0.36, "FFFFFF" if name != "IconBand" else C["screen"],
          "Neon", glow=2.0, bevel=0)
K.text("TermText", "ИНВЕНТАРЬ", (0, VF + 4.55, ST0 - 0.43), 0.5, "FFFFFF", "-z", glow=1.2)
K.box("TermDesk", -2.2, 2.2, VF, VF + 2.5, ST0 - 2.4, ST0 - 1.0, C["navy"])
K.part("TermPanel", "Block", (4.6, 0.25, 1.8), (0, VF + 2.75, ST0 - 1.7), C["gold"], rot=K.rot_x(-15))
K.part("TermPad", "Block", (4.0, 0.06, 1.4), (0, VF + 2.92, ST0 - 1.72), C["cyan"], "Neon", rot=K.rot_x(-15),
       glow=1.2, bevel=0)

# архив: два стеллажа с капсулами (предметы инвентаря в хранилище — образно, не модели)
K.group("Archive")
CAPS = [RARITY[r] for r in ("Common", "Rare", "Epic", "Legendary", "Rare", "Common")]
for u, cz in enumerate((-6.0, 9.0)):
    x0, x1 = W(-1, 0.25, 2.6)
    K.box("ShelfBack", *W(-1, 0.25, 0.55), VF, VF + 8.6, cz - 3.4, cz + 3.4, C["steelDark"])
    for zz in (cz - 3.4, cz + 3.1):
        K.box("ShelfPost", x0, x1, VF, VF + 8.6, zz, zz + 0.3, C["gold"])
    for lvl in range(3):
        y = VF + 0.6 + lvl * 2.75
        K.box("ShelfBoard", x0, x1, y - 0.2, y, cz - 3.1, cz + 3.1, C["steel"])
        for n, oz in enumerate((-1.5, 1.5)):
            col = CAPS[(u * 3 + lvl + n) % len(CAPS)]
            K.cyl("Capsule", (-IX + 1.45, y + 0.95, cz + oz), 1.9, 1.5, col, "y", "Glass", alpha=0.78)
K.text("ArchiveText", "АРХИВ", (-IX + 0.6, VF + 9.6, 1.5), 0.6, C["gold"], "+x", glow=1.2)

# центр безопасности: стол, мониторы, план музея на стене, пульт защиты
K.group("Security")
K.box("DeskTop", 12.8, 15.6, VF + 2.5, VF + 2.8, -8.0, 0.0, C["navy"])
K.box("DeskEdge", 12.7, 15.7, VF + 2.35, VF + 2.55, -8.1, 0.1, C["gold"])
K.box("DeskBody", 13.4, 15.6, VF, VF + 2.35, -7.8, -0.2, C["navyDark"])
for k, mz in enumerate((-6.2, -4.0, -1.8)):
    K.box("MonFrame", 13.6, 13.9, VF + 3.2, VF + 5.2, mz - 1.0, mz + 1.0, C["navyDark"])
    K.box("MonScreen", 13.5, 13.6, VF + 3.35, VF + 5.05, mz - 0.85, mz + 0.85, ("1D6FE0", "0E7F7A", "1D6FE0")[k],
          "Neon", glow=1.1, bevel=0)
K.box("WallScreen", IX - 0.3, IX, VF + 5.4, VF + 10.2, -9.0, 1.0, C["navyDark"])
K.box("WallScreenIn", IX - 0.36, IX - 0.3, VF + 5.7, VF + 9.9, -8.7, 0.7, "0F2C55", "Neon", glow=1.0, bevel=0)
for name, y0, y1, z0, z1, col in (("PlanTop", 9.1, 9.25, -7.6, -0.4, C["cyan"]), ("PlanBot", 6.4, 6.55, -7.6, -0.4,
                                                                                    C["cyan"]),
                                  ("PlanAlert", 7.5, 8.0, -3.0, -2.5, C["red"])):
    K.box(name, IX - 0.42, IX - 0.36, VF + y0, VF + y1, z0, z1, col, "Neon", glow=3, bevel=0)
K.text("SecText", "БЕЗОПАСНОСТЬ", (IX - 0.45, VF + 10.75, -4.0), 0.55, C["gold"], "-x", glow=1.2)
K.box("Chair", 10.4, 11.8, VF, VF + 1.8, -4.8, -3.2, C["red"])
K.box("ChairBack", 10.4, 10.7, VF + 1.8, VF + 3.6, -4.8, -3.2, C["red"])
K.cyl("ShieldStand", (8.0, VF + 1.3, -9.4), 2.6, 1.4, C["navy"], "y")
K.cyl("ShieldDisk", (8.0, VF + 3.3, -9.4), 0.2, 2.2, C["gold"], "z")
K.cyl("ShieldHolo", (8.0, VF + 3.3, -9.52), 0.06, 1.6, C["cyan"], "z", "Neon", glow=2, bevel=0)

# эмблема на передней стене хранилища
K.group("Lockers")
for sx in (-1, 1):
    x0 = sx * 4.0 if sx > 0 else -11.9
    K.box("LockerFrame", x0, x0 + 7.9, VF, VF + 6.5, IZ0, IZ0 + 0.35, C["gold"])
    for col in range(3):
        for row in range(2):
            lx = x0 + 0.2 + col * 2.53
            ly = VF + 0.35 + row * 3.05
            K.box("LockerDoor", lx, lx + 2.4, ly, ly + 2.85, IZ0 + 0.35, IZ0 + 0.6,
                  C["locker"] if (col + row) % 2 == 0 else C["vPanel"])
K.group("Vault")
K.cyl("VEmblem", (0, VF + 7.8, IZ0 + 0.3), 0.3, 3.6, C["gold"], "z")
K.cyl("VEmblemIn", (0, VF + 7.8, IZ0 + 0.5), 0.2, 2.6, C["navy"], "z")

# ── Свет для игры (бюджет) и для рендера ───────────────────────────────────────────────────────────────────────
K.group("GameLights")
for x, z in ((0.0, -4.0), (0.0, 8.0)):
    K.game_light("PointLight", (x, 12.0, z), 26, 1.0, "FFE8B0")
K.game_light("PointLight", (0, VF + 9.5, -4.0), 24, 0.9, "CFE6FF")
K.game_light("SpotLight", (0, VF + 10.0, 14.0), 14, 1.4, C["warm"], 60)
K.game_light("PointLight", (11.0, VF + 6.0, -4.0), 14, 0.6, "BFE4FF")

K.sky()
K.sun()
for x in (-8.0, 8.0):
    for z in (-6.0, 6.0):
        K.light("HallFill", "AREA", (x, CEIL - 0.2, z), 900, "FFF4E2", 7.0, (x, 0, z), shadow=False)
K.light("SkyFill", "AREA", (0, CEIL - 0.7, 0.0), 1800, "EAF7FF", 9.0, (0, 0, 0.0))
K.light("Entry", "AREA", (0, 9.0, FZ - 3.0), 600, "FFF4E2", 6.0, (0, 4, 0), shadow=False)
for sx, i, px, cz, item in PLACES:
    K.light("BaySpot", "SPOT", (px, 9.3, cz), 900 if item else 380, C["warm"] if item else "E6F4FF",
            target=(px, 3.0, cz), spot=46)
K.light("PvInside", "AREA", (0, PV_H - 0.3, 6.5), 500, "FFE7B8", 4.0, (0, -6, 9), shadow=False)
K.light("StairMid", "AREA", (0, -3.0, 12.0), 650, "FFE7B8", 5.0, (0, -12, 12.0), shadow=False)
for x, z in ((-9.0, -6.0), (9.0, -6.0), (-9.0, 9.0), (9.0, 9.0), (0.0, -1.0)):
    K.light("VaultFill", "AREA", (x, VCEIL - 0.3, z), 750, "E6F4FF", 6.0, (x, VF, z), shadow=False)
K.light("SafeKey", "SPOT", (0, -3.0, 13.0), 2600, C["warm"], target=(0, SY, IZ1), spot=55)
K.light("TermKey", "SPOT", (0, -3.2, -4.0), 900, "E6F4FF", target=(0, VF + 6, ST0), spot=60)
K.light("ArchKey", "SPOT", (-7.0, -3.5, 1.5), 900, "E6F4FF", target=(-IX, VF + 4, 1.5), spot=80)
K.light("SecKey", "SPOT", (6.5, -3.5, -4.0), 1000, "E6F4FF", target=(IX, VF + 5, -4.0), spot=80)

# ── Люди для масштаба ──────────────────────────────────────────────────────────────────────────────────────────
K.mannequin(-1.6, -6.0, math.radians(20))
K.mannequin(7.4, 6.0, math.radians(-90), shirt="E0533E")
K.mannequin(1.2, 7.5, math.radians(0), y=-5.0)
K.mannequin(3.5, -6.0, math.radians(200), y=VF, shirt="4CB860")
K.mannequin(9.4, -1.4, math.radians(-90), y=VF)

# ── Экспонаты (одобренные модели D39 и коллекция босса 1, без картин) ───────────────────────────────────────────
TEX = os.path.join(REPO, "assets", "textures", "art")


def material_for(name, color_png, normal_png):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Roughness"].default_value = 0.5
    col = nt.nodes.new("ShaderNodeTexImage")
    col.image = bpy.data.images.load(color_png)
    nt.links.new(col.outputs["Color"], b.inputs["Base Color"])
    if os.path.exists(normal_png):
        nrm = nt.nodes.new("ShaderNodeTexImage")
        nrm.image = bpy.data.images.load(normal_png)
        nrm.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


def import_item(fbx, keep, color_png, normal_png, px, cz, sx, height=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=fbx)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH" and (keep is None or o.name == keep)]
    for o in new:
        if o not in meshes and o.type == "MESH" or (o.type != "MESH" and o not in meshes and o.parent is None and
                                                    not o.children):
            bpy.data.objects.remove(o, do_unlink=True)
    m = material_for(f"Item_{keep}", color_png, normal_png)
    for o in meshes:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        K.coll("ExhibitNear" if sx > 0 else "Exhibit").objects.link(o)
        o.data.materials.clear()
        o.data.materials.append(m)
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    bpy.context.view_layer.update()

    def bounds():
        lo = Vector([min(min((o.matrix_world @ v.co)[i] for v in o.data.vertices) for o in meshes) for i in range(3)])
        hi = Vector([max(max((o.matrix_world @ v.co)[i] for v in o.data.vertices) for o in meshes) for i in range(3)])
        return lo, hi

    lo, hi = bounds()
    if height:
        for o in meshes:
            o.scale = o.scale * (height / (hi.z - lo.z))
    for o in meshes:  # лицом к проходу
        o.rotation_euler.z += math.radians(-90 if sx > 0 else 90)
    bpy.context.view_layer.update()
    lo, hi = bounds()
    target = K.R(px, 3.0, cz)
    shift = Vector((target.x - (lo.x + hi.x) / 2, target.y - (lo.y + hi.y) / 2, target.z - lo.z))
    for o in meshes:
        o.location += shift


B1 = os.path.join(REPO, "assets", "models", "Art_Boss1_MuseumOfWonders.fbx")
for sx, i, px, cz, item in PLACES:
    if not item:
        continue
    key = item[0]
    if key == "Vase":
        import_item(os.path.join(REPO, "assets", "models", "ArtV13_Vase.fbx"), None,
                    os.path.join(TEX, "v13_vase_color.png"), os.path.join(TEX, "v13_vase_normal.png"), px, cz, sx, 3.2)
    else:
        import_item(B1, f"Art_{key}", os.path.join(TEX, f"{key}_color.png"), os.path.join(TEX, f"{key}_normal.png"),
                    px, cz, sx)

# ── Устройства защиты (только для кадра «защита в музее»; в бюджет зала не входят) ─────────────────────────────
K.group("Devices")
D.door((0, 0, -12.0), 0, "idle", prefix="DefDoor")
D.laser((0, 0, LASERS["Gallery"][0]), 0, "idle", length=LASERS["Gallery"][1], prefix="DefLaser")
D.robot((-6.6, 0, 0.6), 0, "idle", prefix="DefRobot")
D.trap((7.4, 0, 5.6), 0, "idle", prefix="DefTrap")
D.snare((-7.6, 0, 10.4), 0, "idle", prefix="DefSnare")

# ── Учёт деталей и выгрузка ────────────────────────────────────────────────────────────────────────────────────
NOT_MUSEUM = {"Devices", "Ground", "PlotLines", "SectionEarth", "People", "Exhibit", "Studio", "GameLights"}
museum = [b for b in K.S["bricks"] if b["group"] not in NOT_MUSEUM]
K.S["bricks"][:] = museum
counts = K.counts()
upper = sum(v for g, v in counts.items() if g not in ("Stair", "Vault", "VaultNear", "VaultFront", "VaultCeiling",
                                                      "Safe",
                                                      "Terminal", "Archive", "Security", "Lockers"))
print("PARTS", counts, "total", len(museum), "upper", upper, "lower", len(museum) - upper, flush=True)
print("TRIS", K.S["tris"], flush=True)
K.export(os.path.join(OUT, "bricks", "museum.json"),
         {"upper": upper, "lower": len(museum) - upper,
          "places": [{"slot": n + 1, "side": sx, "center": [px, 3.0, cz], "face": [-sx, 0, 0]}
                     for n, (sx, i, px, cz, item) in enumerate(sorted(PLACES, key=lambda p: (p[3], -p[0])))],
          "lasers": {k: {"z": z, "length": L, "y": 2.4} for k, (z, L) in LASERS.items()},
          "stair": {"top_z": ST0, "half_width": STW, "steps": 12, "rise": 1, "run": 1},
          "well": {"half_x": WELL_X, "z0": ST0, "z1": WELL_Z1}, "vault_floor": VF})

# ── Камера и кадры ─────────────────────────────────────────────────────────────────────────────────────────────
K.camera()
PCT = 50 if FAST else 100
UP = ("Ceiling", "Roof")
EXTRA = ("Devices", "SectionEarth", "GameLights")


def shot(name, eye, at, fov=70, res=(1600, 900), hidden=(), ortho=None, top=False):
    if ONLY and name not in ONLY:
        return
    K.show_only(set(hidden) | set(EXTRA) - ({"Devices"} if name == "14_defense_in_museum" else set())
                - ({"SectionEarth"} if name == "13_section" else set()))
    K.shot(os.path.join(RENDERS, name + ".png"), eye, at, fov, res, ortho, PCT, top_down=top)


shot("01_exterior", (-17, 6.0, -44), (0, 9.5, -14), 58)
shot("02_hall_from_entrance", (0, 6.2, -16.0), (0, 4.2, 8), 76)
shot("03_hall_toward_entrance", (-13.0, 11.5, 17.6), (5.0, 2.5, -11.0), 74)
shot("04_hall_overview", (26, 42, -30), (0, -1, 3), 44, hidden=UP + ("WallsNear", "Exterior"))
shot("05_place_empty", (-5.2, 5.4, -8.6), (-13.2, 3.0, -1.6), 44, (1100, 1100))
shot("06_place_filled", (5.4, 5.6, -8.4), (13.2, 3.4, -1.6), 44, (1100, 1100))
shot("07_vault_entrance", (-5.5, 6.2, -9.5), (1.8, 4.2, 2.4), 62)
shot("08_stair_down", (0, 5.6, 2.0), (0, -8.0, 17.5), 70)
shot("09_vault_safe", (5.0, -7.0, 11.5), (0, -8.2, 19.3), 70)
shot("10_vault_main", (10.0, -6.5, 15.5), (-3.0, -8.8, -7.0), 76)
shot("11_vault_security", (-3.0, -6.6, -2.0), (14.0, -8.6, -5.0), 70)
shot("12_vault_overview", (26, 30, -30), (0, -14, 3), 44,
     hidden=UP + ("WallsNear", "Exterior", "Shell", "Bays", "BaysNear", "Aisle", "Foyer", "Pavilion", "BackWall",
                  "PavilionNear", "VaultDoor", "VaultNear", "VaultFront", "VaultCeiling", "Ground", "GroundNear",
                  "Exhibit",
                  "ExhibitNear", "People", "PlotLines"))
shot("13_section", (80, -1.0, 4.0), (0, -1.0, 4.0), 0, (1600, 900), ortho=52,
     hidden=("WallsNear", "BaysNear", "ExhibitNear", "VaultNear", "GroundNear", "PlotLines", "PavilionNear",
             "VaultDoor", "Security"))
shot("14_defense_in_museum", (22, 30, -26), (0, 0, 0), 42, hidden=UP + ("WallsNear", "Exterior"))
shot("15_plan_upper", (0, 120, 4), (0, 0, 4.001), 0, (1100, 1100), UP + ("People", "Exhibit", "ExhibitNear"), 58,
     True)
shot("16_plan_vault", (0, 120, 4), (0, 0, 4.001), 0, (1100, 1100),
     UP + ("People", "Exhibit", "ExhibitNear", "Shell", "WallsNear", "Bays", "BaysNear", "Aisle", "Foyer",
           "Pavilion", "PavilionNear", "VaultDoor", "BackWall", "Exterior", "VaultCeiling", "Ground", "GroundNear",
           "PlotLines"), 58, True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "museum_v2.blend"))
