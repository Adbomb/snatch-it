"""D48-C, фаза 1 — музей до 20 мест на основе утверждённого D48 v2 (только концепт: в игру ничего не попадает,
в Roblox ничего не загружается).

Раскладка — scripts/blender/d48c_layout.py (единый источник: места 1–20, уровни открытия, галереи, арки, зоны).
Главный зал: 8 ниш (по 4 на стену); места 9–20 — две боковые галереи в объёме крыльев D36 (x 18…29), продлённые
вдоль портика до линии участка, вход — аркой из входного зала. Хранилище, павильон, лестница — D48 v2 без изменений.
Уровень музея задаёт, что построено и что открыто: --level N (1…10).

Это временная геометрия из деталей Roblox (d48_kit) для проверки размеров, проходов и логики — не финальная
Blender-графика (финальные Mesh-модули — фаза 2).

Запуск: blender --background --factory-startup --python scripts/blender/d48c_museum.py -- <репо> --level N [--fast]
        [виды]
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import d48_devices as D  # noqa: E402
import d48_kit as K  # noqa: E402
import d48c_layout as L  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
REPO = os.path.abspath(argv[0]) if argv else os.getcwd()
FAST = "--fast" in argv
LEVEL = int(argv[argv.index("--level") + 1]) if "--level" in argv else 10
ONLY = [a for i, a in enumerate(argv[1:], 1) if not a.startswith("--") and argv[i - 1] != "--level"]
OUT = os.path.join(REPO, "assets", "concepts", "d48", "c1")
GALLERIES = LEVEL >= L.GALLERY_LEVEL
OPEN = L.slots_compat(LEVEL)  # сколько мест открыто (совместимая схема; по D37 — 2 × уровень)
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
PIL_Z = L.PIL_Z
LASERS = {k: (v["z"], v["length"]) for k, v in L.LASERS.items()}
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
    if GALLERIES and name != "PodiumB":
        continue  # под галереями — их пол
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
def side_wall(name, sx):
    x0, x1 = sorted((sx * IX, sx * HW))
    if not GALLERIES:
        K.box(name, x0, x1, 0, CEIL + 1.4, FZ, BZ, C["wall"], look=WALL)
        return
    K.box(name + "Front", x0, x1, 0, CEIL + 1.4, FZ, L.ARCH_Z0, C["wall"], look=WALL)
    K.box(name + "Back", x0, x1, 0, CEIL + 1.4, L.ARCH_Z1, BZ, C["wall"], look=WALL)
    K.box(name + "Lintel", x0, x1, L.ARCH_H, CEIL + 1.4, L.ARCH_Z0, L.ARCH_Z1, C["wall"], look=WALL)


side_wall("WallL", -1)
K.box("WallBack", -IX, IX, 0, CEIL + 1.4, IZ1, BZ, C["wall"], look=WALL)
K.group("WallsNear")
side_wall("WallR", 1)
K.box("WallFrontL", -IX, -DOOR, 0, CEIL + 1.4, FZ, IZ0, C["wall"], look=WALL)
K.box("WallFrontR", DOOR, IX, 0, CEIL + 1.4, FZ, IZ0, C["wall"], look=WALL)
K.box("WallFrontTop", -DOOR, DOOR, DOORH, CEIL + 1.4, FZ, IZ0, C["wall"], look=WALL)
K.group("Shell")
for name, x0, x1, z0, z1 in (("L", -IX, -IX + 0.2, IZ0, IZ1), ("R", IX - 0.2, IX, IZ0, IZ1),
                             ("B", -IX, IX, IZ1 - 0.2, IZ1)):
    K.group("WallsNear" if name == "R" else "Shell")
    if GALLERIES and name in ("L", "R"):  # плинтус прерывается аркой
        K.box("Base" + name + "F", x0, x1, 0, 1.0, z0, L.ARCH_Z0, C["navy"])
        K.box("Base" + name, x0, x1, 0, 1.0, L.ARCH_Z1, z1, C["navy"])
    else:
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

# ── Места экспонатов: 8 ниш зала и 12 мест галерей (L.places), состояние — по уровню ─────────────────────────
ITEMS = {  # одобренные модели для кадров (без картин): слот → (ключ FBX, имя, редкость, доход)
    1: ("Moai", "ГОЛОВА МОАИ", "Common", 16), 4: ("TutMask", "МАСКА ТУТАНХАМОНА", "Epic", 150),
    5: ("Vase", "ВАЗА", "Rare", 25), 7: ("StatueOfLiberty", "СТАТУЯ СВОБОДЫ", "Epic", 165),
    9: ("GreatSphinx", "БОЛЬШОЙ СФИНКС", "Rare", 45), 10: ("NefertitiBust", "БЮСТ НЕФЕРТИТИ", "Rare", 48),
    12: ("Colosseum", "КОЛИЗЕЙ", "Rare", 55), 13: ("AnubisStatue", "СТАТУЯ АНУБИСА", "Common", 13),
    15: ("TerracottaWarrior", "ТЕРРАКОТОВЫЙ ВОИН", "Common", 12), 18: ("EgyptianCat", "ЕГИПЕТСКАЯ КОШКА", "Common", 10),
}
SHOWN = {k: v for k, v in ITEMS.items() if k <= OPEN and (LEVEL >= 5 or k <= 6)}
if LEVEL < 5:  # на первых уровнях в кадре — только стартовые экспонаты
    SHOWN = {k: v for k, v in SHOWN.items() if k in (1, 4, 5)}
AMBER = "FFB347"
PLACES = []


def place_module(p, wall_x, sx, group):
    """Постамент у стены wall_x (внутренняя грань), табличка к проходу; состояние: занято / свободно / закрыто."""
    K.group(group)
    px, _, cz = p["center"]
    slot = p["slot"]
    item = SHOWN.get(slot)
    opened = slot <= OPEN
    state = "filled" if (opened and item) else ("free" if opened else "locked")
    hb, hd, hc, ht = L.BASE / 2, 2.3, 2.55, L.TOP / 2
    K.box("PedBase", px - hb, px + hb, 0, 0.5, cz - hb, cz + hb, C["navy"])
    K.box("PedBody", px - hd, px + hd, 0.5, 2.6, cz - hd, cz + hd, C["pilaster"], look=soft(C["pilaster"], 0.8, 0.1))
    K.box("PedCap", px - hc, px + hc, 2.6, 2.85, cz - hc, cz + hc, C["gold"])
    K.box("PedTop", px - ht, px + ht, 2.85, 3.0, cz - ht, cz + ht, C["pilaster"])
    face = px - sx * hd
    fx0, fx1 = (face - 0.12, face) if sx > 0 else (face, face + 0.12)
    K.box("Plaque", fx0, fx1, 1.0, 2.2, cz - 1.5, cz + 1.5, C["navyDark"], bevel=0.03)
    strip = {"filled": RARITY[item[2]] if item else C["cyan"], "free": C["cyan"], "locked": AMBER}[state]
    K.box("PlaqueStrip", fx0 - (0.03 if sx > 0 else 0), fx1 + (0 if sx > 0 else 0.03), 2.2, 2.32, cz - 1.5,
          cz + 1.5, strip, "Neon", glow=2.5, bevel=0)
    tf, tx = ("-x" if sx > 0 else "+x"), face - sx * 0.14
    ex = ("ExhibitNear" if sx > 0 else "Exhibit")
    if state == "filled":
        K.box("PlaceGlow", px - 1.9, px + 1.9, 3.0, 3.05, cz - 1.9, cz + 1.9, C["gold"], "Glass", alpha=0.55, bevel=0,
              cname=ex)
        K.text("PlaqueName", item[1], (tx, 1.85, cz), 0.28 if len(item[1]) > 14 else 0.32, "FFFFFF", tf, cname=ex)
        K.text("PlaqueIncome", f"+{item[3]} $/сек", (tx, 1.38, cz), 0.3, "7CFF6B", tf, cname=ex)
    elif state == "free":
        K.box("PlaceGlow", px - 1.9, px + 1.9, 3.0, 3.05, cz - 1.9, cz + 1.9, C["cyan"], "Glass", alpha=0.45, bevel=0)
        K.part("PlaceHolo", "Block", (0.9, 0.9, 0.9), (px, 4.3, cz), C["cyan"], "Glass", alpha=0.5,
               rot=K.rot_y(45) @ K.rot_x(35.26) @ K.rot_z(45), bevel=0.04, collide=False)
        K.text("PlaqueFree", "СВОБОДНО", (tx, 1.82, cz), 0.3, C["cyan"], tf, glow=1.2)
        K.text("PlaqueHint", f"место {slot}", (tx, 1.38, cz), 0.22, "C9D6F2", tf, weight="Bold")
    else:  # закрыто до уровня
        K.box("PlaceCover", px - 2.2, px + 2.2, 3.0, 3.25, cz - 2.2, cz + 2.2, C["backdrop"], bevel=0.08)
        K.text("PlaqueLock", "ЗАКРЫТО", (tx, 1.82, cz), 0.3, AMBER, tf, glow=1.0)
        K.text("PlaqueLevel", f"уровень {p['unlock_compat']}", (tx, 1.38, cz), 0.24, "F2D7A8", tf, weight="Bold")
    if state != "locked":
        K.game_light("SpotLight", (px, 9.3, cz), 14, 1.6 if state == "filled" else 0.6, C["warm"], 55)
    PLACES.append((p, state, item, sx))


ALL = L.places()
HALL_PLACES = [p for p in ALL if p["zone"] == "hall"]
GAL_PLACES = [p for p in ALL if p["zone"] == "gallery"]

for sx in (-1, 1):  # ниши зала: пилястры, фон, перемычка, светильник
    grp = "BaysNear" if sx > 0 else "Bays"
    K.group(grp)
    for z in PIL_Z:
        K.box("PilBase", *W(sx, 0, 1.55), 0, 0.9, z - 0.55, z + 0.55, C["navy"])
        K.box("Pilaster", *W(sx, 0, 1.3), 0.9, 11.6, z - 0.4, z + 0.4, C["pilaster"])
        K.box("PilCap", *W(sx, 0, 1.55), 11.6, 12.4, z - 0.55, z + 0.55, C["gold"])
    for i, cz in enumerate(L.NICHE_Z):
        z0 = PIL_Z[i] + 0.4
        z1 = PIL_Z[i + 1] - 0.4 if i + 1 < len(PIL_Z) else IZ1
        K.box("Backdrop", *W(sx, 0, 0.3), 0.9, 9.2, z0 + 0.05, z1 - 0.05, C["backdrop"],
              look=K.rings(C["backdrop"], 1.0, 0.1, 0.75))
        K.box("Header", *W(sx, 0, 1.1), 9.2, 10.4, z0, z1, C["pilaster"])
        K.box("HeaderStep", *W(sx, 0.3, 0.75), 8.6, 9.2, z0 + 0.05, z1 - 0.05, C["gold"])
        K.box("LampArm", *W(sx, 1.1, L.NICHE_D + 0.2), 9.75, 10.0, cz - 0.15, cz + 0.15, C["gold"])
        K.cyl("LampHead", (sx * (IX - L.NICHE_D), 9.55, cz), 0.6, 0.8, C["navyDark"], "y")
for p in HALL_PLACES:
    sx = 1 if p["center"][0] > 0 else -1
    if p["slot"] > OPEN and p["unlock_compat"] <= 4 and LEVEL < p["unlock_compat"] and p["slot"] in (7, 8):
        # 4-я ниша до уровня 4 — декоративная урна (часть здания, не экспонат): зал не выглядит недостроенным
        K.group("BaysNear" if sx > 0 else "Bays")
        px, _, cz = p["center"]
        K.box("UrnBase", px - 1.6, px + 1.6, 0, 1.2, cz - 1.6, cz + 1.6, C["navy"])
        K.cyl("UrnFoot", (px, 1.45, cz), 0.5, 1.4, C["gold"], "y")
        K.ball("UrnBody", (px, 2.9, cz), 2.6, C["gold"])
        K.cyl("UrnNeck", (px, 4.4, cz), 0.8, 1.1, C["goldDeep"], "y")
        continue
    place_module(p, sx * IX, sx, "BaysNear" if sx > 0 else "Bays")

# ── Галереи (с уровня 5): в объёме крыльев D36, вдоль портика до линии участка; вход — арка из входного зала ─────
if GALLERIES:
    GW = soft(C["wall"])
    for sx in (-1, 1):
        near = sx > 0
        K.group("Gallery")  # пол — видно и в разрезе
        xi0, xi1 = sorted((sx * L.GAL_IN, sx * L.GAL_OUT))
        K.box("GalFloor", xi0, xi1, G, 0, L.GAL_Z0, L.GAL_Z1, C["floor"], look=FLOOR, bevel=0.02)
        K.group("GalleryNear" if near else "Gallery")
        K.box("GalOuter", *sorted((sx * L.GAL_IX, sx * L.GAL_OUT)), 0, L.GAL_H + 1.0, L.GAL_Z0, L.GAL_Z1, C["wall"],
              look=GW)
        K.box("GalFront", *sorted((sx * L.GAL_IN, sx * L.GAL_IX)), 0, L.GAL_H + 1.0, L.GAL_Z0, L.GAL_IZ0, C["wall"],
              look=GW)
        K.box("GalBack", *sorted((sx * L.GAL_IN, sx * L.GAL_IX)), 0, L.GAL_H + 1.0, L.GAL_IZ1, L.GAL_Z1, C["wall"],
              look=GW)
        K.box("GalInnerFront", *sorted((sx * IX, sx * L.GAL_IN)), 0, L.GAL_H + 1.0, L.GAL_Z0, FZ, C["wall"],
              look=GW)  # стена вдоль портика
        K.box("GalBase", *sorted((sx * (L.GAL_IX - 0.2), sx * L.GAL_IX)), 0, 1.0, L.GAL_IZ0, L.GAL_IZ1, C["navy"])
        K.box("GalBelt", *sorted((sx * (L.GAL_IX - 0.25), sx * L.GAL_IX)), 9.6, 9.9, L.GAL_IZ0, L.GAL_IZ1, C["gold"])
        K.box("GalRunner", *sorted((sx * (L.GAL_IN + 0.5), sx * (L.GAL_IN + 3.4))), 0, 0.08, L.GAL_IZ0 + 0.6,
              L.GAL_IZ1 - 0.6, C["navy"], bevel=0.01)
        K.box("GalFrieze", *sorted((sx * L.GAL_IN, sx * (L.GAL_OUT + 0.3))), L.GAL_H - 0.2, L.GAL_H + 0.6,
              L.GAL_Z0 - 0.3, L.GAL_Z0, C["gold"])
        K.text("GalName", "ГАЛЕРЕЯ", (sx * (L.GAL_IN + L.GAL_OUT) / 2, L.GAL_H - 1.6, L.GAL_Z0 - 0.05), 1.1,
               C["gold"], "-z", glow=1.2)
        K.group("GalleryRoof")
        K.box("GalRoof", *sorted((sx * (IX + 1.4), sx * (L.GAL_OUT + 0.4))), L.GAL_H + 1.0, L.GAL_H + 1.8,
              L.GAL_Z0 - 0.4, L.GAL_Z1 + 0.4, C["pilaster"])
        K.box("GalCornice", *sorted((sx * (IX + 1.4), sx * (L.GAL_OUT + 0.6))), L.GAL_H + 1.8, L.GAL_H + 2.1,
              L.GAL_Z0 - 0.6, L.GAL_Z1 + 0.6, C["gold"])
        K.box("GalSkylight", *sorted((sx * (L.GAL_IN + 0.6), sx * (L.GAL_IN + 3.6))), L.GAL_H + 0.98, L.GAL_H + 1.0,
              L.GAL_IZ0 + 1, L.GAL_IZ1 - 1, "EAF7FF", "Neon", glow=1.8, bevel=0)
        # арка из входного зала: золотая рама и вывеска со стороны зала
        K.group("WallsNear" if near else "Shell")
        ax = sx * IX
        for z0, z1, y0, y1 in ((L.ARCH_Z0 - 0.5, L.ARCH_Z0, 0, L.ARCH_H + 0.5),
                               (L.ARCH_Z1, L.ARCH_Z1 + 0.5, 0, L.ARCH_H + 0.5),
                               (L.ARCH_Z0 - 0.5, L.ARCH_Z1 + 0.5, L.ARCH_H, L.ARCH_H + 0.5)):
            K.box("ArchFrame", *sorted((ax, ax - sx * 0.25)), y0, y1, z0, z1, C["gold"])
        K.box("ArchSign", *sorted((ax - sx * 0.25, ax - sx * 0.4)), L.ARCH_H + 0.9, L.ARCH_H + 1.9, L.ARCH_Z0,
              L.ARCH_Z1, C["navyDark"])
        K.text("ArchSignText", "ГАЛЕРЕЯ", (ax - sx * 0.43, L.ARCH_H + 1.4, (L.ARCH_Z0 + L.ARCH_Z1) / 2), 0.55,
               C["gold"], "-x" if sx > 0 else "+x", glow=1.2)
    for p in GAL_PLACES:
        sx = p["side"]
        K.group("GalPlacesNear" if sx > 0 else "GalPlaces")
        px, _, cz = p["center"]
        K.box("GalBackdrop", *sorted((sx * L.GAL_IX, sx * (L.GAL_IX - 0.3))), 0.9, 8.6, cz - 2.75, cz + 2.75,
              C["backdrop"], look=K.rings(C["backdrop"], 1.0, 0.1, 0.75))
        K.box("GalHeader", *sorted((sx * L.GAL_IX, sx * (L.GAL_IX - 0.8))), 8.6, 9.6, cz - 3.0, cz + 3.0,
              C["pilaster"])
        K.cyl("GalLamp", (px, 9.85, cz), 0.3, 0.8, C["navyDark"], "y")
        place_module(p, sx * L.GAL_IX, sx, "GalPlacesNear" if sx > 0 else "GalPlaces")

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
cxz = L.CHEST["center"]  # сундук у входа: x −9 вместо −12 — освобождает подход к арке галереи
cx, cz = cxz
K.box("Chest", cx - 2.0, cx + 2.0, 0, 1.9, cz - 1.5, cz + 1.5, "3E7BE0")
K.box("ChestLid", cx - 2.1, cx + 2.1, 1.9, 2.5, cz - 1.6, cz + 1.6, "5A93F0")
K.box("ChestTop", cx - 1.8, cx + 1.8, 2.5, 2.85, cz - 1.3, cz + 1.3, "3E7BE0")
for bx in (-1.2, 1.2):
    K.box("ChestBand", cx + bx - 0.18, cx + bx + 0.18, 0, 2.9, cz - 1.62, cz + 1.62, C["gold"])
K.box("ChestLock", cx - 0.45, cx + 0.45, 1.2, 2.2, cz + 1.5, cz + 1.7, C["gold"])
K.box("ChestSlot", cx - 1.2, cx + 1.2, 2.3, 2.4, cz + 1.6, cz + 1.66, C["cyan"], "Neon", glow=2.5, bevel=0)
sx_, sz_ = L.STAND["center"]
K.box("StandBase", sx_ - 0.9, sx_ + 0.9, 0, 0.6, sz_ - 0.7, sz_ + 0.7, C["navy"])
K.box("StandPost", sx_ - 0.3, sx_ + 0.3, 0.6, 3.0, sz_ - 0.3, sz_ + 0.3, C["gold"])
board = K.rot_x(-20)
K.part("StandBoard", "Block", (3.2, 2.0, 0.25), (sx_, 3.8, sz_ + 0.1), C["navyDark"], rot=board, bevel=0.05)
K.part("StandScreen", "Block", (2.9, 1.7, 0.05), (sx_, 3.8 + 0.05, sz_ + 0.27), C["screen"], "Neon", rot=board,
       glow=1.2, bevel=0)
K.text("StandText", f"МУЗЕЙ · УР. {LEVEL}", (sx_, 4.15, sz_ + 0.36), 0.3, "FFFFFF", "+z")
K.text("StandText2", f"{OPEN} мест из 20", (sx_, 3.62, sz_ + 0.18), 0.24, "7CFF6B", "+z", weight="Bold")
if not GALLERIES:  # углы входного зала до галерей — растения; потом здесь подход к аркам
    for px_ in (-13.6, 13.6):
        K.cyl("Pot", (px_, 0.7, -8.6), 1.4, 1.6, C["pilaster"], "y")
        K.cyl("PotRim", (px_, 1.5, -8.6), 0.25, 1.9, C["gold"], "y")
        K.ball("Topiary", (px_, 2.75, -8.6), 2.3, C["plant"])
        K.ball("TopiaryTop", (px_, 4.15, -8.6), 1.3, C["plantDark"])

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
for p, state, item, sx in PLACES:
    px, _, cz = p["center"]
    if state == "locked":
        continue
    K.light("BaySpot", "SPOT", (px, 8.6 if p["zone"] == "gallery" else 9.3, cz), 900 if item else 380,
            C["warm"] if item else "E6F4FF", target=(px, 3.0, cz), spot=46)
if GALLERIES:
    for sx in (-1, 1):
        for z in (-14.0, 0.0, 13.0):
            K.light("GalFill", "AREA", (sx * 21.5, L.GAL_H - 0.3, z), 520, "FFF4E2", 6.0, (sx * 21.5, 0, z),
                    shadow=False)
        K.game_light("PointLight", (sx * 21.5, 9.0, 0), 22, 0.8, "FFE8B0")
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
K.mannequin(-7.0, 14.0, math.radians(90), shirt="4CB860")
if GALLERIES:
    K.mannequin(20.0, -2.0, math.radians(-90), shirt="F2B33D")
    K.mannequin(-19.8, 6.0, math.radians(90), shirt="8B6CF7")
K.mannequin(3.5, -6.0, math.radians(200), y=VF, shirt="4CB860")

# ── Экспонаты: одобренные модели (D39 и коллекция босса 1, без картин) ─────────────────────────────────────────
TEX = os.path.join(REPO, "assets", "textures", "art")
B1 = os.path.join(REPO, "assets", "models", "Art_Boss1_MuseumOfWonders.fbx")


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


def fbx_objects(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.type == "MESH":
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    return [o for o in new if o.name in bpy.data.objects]


def bounds(objs):
    bpy.context.view_layer.update()
    lo = Vector([min(min((o.matrix_world @ v.co)[i] for v in o.data.vertices) for o in objs) for i in range(3)])
    hi = Vector([max(max((o.matrix_world @ v.co)[i] for v in o.data.vertices) for o in objs) for i in range(3)])
    return lo, hi


def put(objs, px, cz, sx, height=None):
    lo, hi = bounds(objs)
    if height:
        for o in objs:
            o.scale = o.scale * (height / (hi.z - lo.z))
    for o in objs:
        o.rotation_euler.z += math.radians(-90 if sx > 0 else 90)
    lo, hi = bounds(objs)
    target = K.R(px, 3.0, cz)
    shift = Vector((target.x - (lo.x + hi.x) / 2, target.y - (lo.y + hi.y) / 2, target.z - lo.z))
    for o in objs:
        o.location += shift
        for c in list(o.users_collection):
            c.objects.unlink(o)
        K.coll("ExhibitNear" if sx > 0 else "Exhibit").objects.link(o)


wanted = {p["slot"]: (p, item, sx) for p, state, item, sx in PLACES if state == "filled"}
lib = {o.name: o for o in fbx_objects(B1)} if any(v[1][0] != "Vase" for v in wanted.values()) else {}
used = set()
for slot, (p, item, sx) in sorted(wanted.items()):
    key = item[0]
    px, _, cz = p["center"]
    if key == "Vase":
        objs = fbx_objects(os.path.join(REPO, "assets", "models", "ArtV13_Vase.fbx"))
        m = material_for("Item_Vase", os.path.join(TEX, "v13_vase_color.png"), os.path.join(TEX, "v13_vase_normal.png"))
        for o in objs:
            o.data.materials.clear()
            o.data.materials.append(m)
        put(objs, px, cz, sx, 3.2)
        continue
    src = lib.get(f"Art_{key}")
    if src is None:
        continue
    o = src if src.name not in used else src.copy()
    used.add(src.name)
    m = material_for(f"Item_{key}", os.path.join(TEX, f"{key}_color.png"), os.path.join(TEX, f"{key}_normal.png"))
    o.data.materials.clear()
    o.data.materials.append(m)
    put([o], px, cz, sx)
for name, o in lib.items():  # лишние предметы библиотеки — убрать
    if name not in used and name in bpy.data.objects:
        bpy.data.objects.remove(o, do_unlink=True)

# ── Учёт деталей (временная Part-версия) и выгрузка ─────────────────────────────────────────────────────────────
NOT_MUSEUM = {"Devices", "Ground", "GroundNear", "PlotLines", "SectionEarth", "People", "Exhibit", "ExhibitNear",
              "Studio", "GameLights"}
museum = [b for b in K.S["bricks"] if b["group"] not in NOT_MUSEUM]
K.S["bricks"][:] = museum
counts = K.counts()
LOWER = {"Stair", "Vault", "VaultNear", "VaultFront", "VaultCeiling", "Safe", "Terminal", "Archive", "Security",
         "Lockers"}
GALL = {"Gallery", "GalleryNear", "GalleryRoof", "GalPlaces", "GalPlacesNear"}
lower = sum(v for g, v in counts.items() if g in LOWER)
gall = sum(v for g, v in counts.items() if g in GALL)
places_parts = sum(1 for b in museum if b["name"].startswith(("Ped", "Plaque", "Place", "Urn", "Gal")) and
                   b["group"] in ("Bays", "BaysNear", "GalPlaces", "GalPlacesNear"))
print("LEVEL", LEVEL, "OPEN", OPEN, "PARTS", len(museum), "lower", lower, "galleries", gall, "places", places_parts,
      counts, flush=True)
print("LIGHTS", len([g for g in K.GAME_LIGHTS]), flush=True)
K.export(os.path.join(OUT, "bricks", f"museum_L{LEVEL}.json"),
         {"level": LEVEL, "open": OPEN, "lower": lower, "galleries": gall, "place_parts": places_parts,
          "layout": "scripts/blender/d48c_layout.py"})

# ── Кадры ──────────────────────────────────────────────────────────────────────────────────────────────────────
K.camera()
PCT = 50 if FAST else 100
UP = ("Ceiling", "Roof", "GalleryRoof")
EXTRA = ("Devices", "SectionEarth", "GameLights")
TAG = f"L{LEVEL}_"


def shot(name, eye, at, fov=70, res=(1600, 900), hidden=(), ortho=None, top=False):
    if ONLY and name not in ONLY:
        return
    K.show_only(set(hidden) | set(EXTRA))
    K.shot(os.path.join(RENDERS, TAG + name + ".png"), eye, at, fov, res, ortho, PCT, top_down=top)


shot("exterior", (-36, 11, -62), (2, 7, -12), 52)
shot("hall_from_entrance", (0, 6.2, -16.0), (0, 4.2, 8), 76)
shot("hall_inside", (0, 9.0, -10.4), (0, 2.6, 13.0), 80)
shot("hall_toward_entrance", (-13.0, 11.5, 17.6), (5.0, 2.5, -11.0), 74)
shot("overview", (44, 58, -50), (1.5, -1, 1.5), 46, hidden=UP + ("WallsNear", "GalleryNear", "Exterior"))
if GALLERIES:
    shot("gallery", (20.4, 6.2, -13.6), (24.6, 3.0, 13.0), 72)
    shot("gallery_arch", (-2.0, 6.0, -8.0), (-20.0, 4.0, -8.4), 70)
shot("plan", (0, 140, -0.6), (0, 0, -0.599), 0, (1300, 1300), UP + ("People", "Exhibit", "ExhibitNear"), 66, True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"museum_L{LEVEL}.blend"))
