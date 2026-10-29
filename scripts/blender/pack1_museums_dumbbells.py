"""Пачка 1 (D28, D30, D31): 5 моделей музея и 10 гантелей из LEGO-кирпичей → assets/models/Pack1.fbx.

Музей: начало координат — центр участка на уровне пола, вход в -z (как World/Models/Museum). Все пять
вписаны в участок 44×44: фасад на z = -19, проём входа 12×10 по центру, над ним место под вывеску
(y ≈ 11.5), внутри свободно для витрин. Роли: Accent (стены — игра красит в цвет участка),
AccentDark (крыша — тёмный оттенок), Body и Trim (палитра), Decor (палитра; ставится на чётных уровнях).
Гантели: центр рукояти в начале координат, ось вдоль x, «огромный» размер (~16 стадов); роли Body,
Crystal (стекло в игре), Glow (неон в игре).

Запуск из корня репозитория:
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup \\
    --python scripts/blender/pack1_museums_dumbbells.py -- . <папка превью>
Пишет assets/models/Pack1.fbx, assets/models/Pack1.layout.json, assets/textures/model_palette.png и превью.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lego  # noqa: E402
from lego import Model  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, PREVIEWS = os.path.abspath(argv[0]), os.path.abspath(argv[1])
os.makedirs(PREVIEWS, exist_ok=True)

HALF = 22.0
FACADE = -19.0
DOOR_W, DOOR_H = 12.0, 10.0
WALL_T = 1.0
SIGN_Y = 11.5

ACC = ("Accent", "red")  # цвет в превью; в игре — цвет участка
ACC_DARK = ("AccentDark", "darkred")


def noise(t, seed):
    """Детерминированный «шум» 0..1 по координате вдоль стены."""
    x = math.sin(t * 12.9898 + seed * 78.233) * 43758.5453
    return x - math.floor(x)


def door_hole():
    # Проём входа вдоль фасада (t от левого края x = -HALF).
    return (HALF - DOOR_W / 2, HALF + DOOR_W / 2, 0.0, DOOR_H)


def shell(m, height, colors, seed, studs_top=True, side_windows=(), tops=None, facade_tops=None, back_windows=()):
    """Три стены и фасад с проёмом. side_windows — (z0, z1, y0, y1) на боковых, back_windows — (x0, x1, y0, y1)."""
    side_len = HALF - FACADE
    holes_side = [(z0 - FACADE, z1 - FACADE, y0, y1) for z0, z1, y0, y1 in side_windows]
    for sx in (-HALF + WALL_T / 2, HALF - WALL_T / 2):
        m.brick_wall("Accent", (sx, FACADE), (sx, HALF), height, WALL_T, colors, studs_top=studs_top,
                     holes=holes_side, tops=tops, seed=seed + int(sx))
    holes_back = [(x0 + HALF, x1 + HALF, y0, y1) for x0, x1, y0, y1 in back_windows]
    m.brick_wall("Accent", (-HALF, HALF - WALL_T / 2), (HALF, HALF - WALL_T / 2), height, WALL_T, colors,
                 studs_top=studs_top, holes=holes_back, tops=tops, seed=seed + 7)
    m.brick_wall("Accent", (-HALF, FACADE), (HALF, FACADE), height, WALL_T, colors, studs_top=studs_top,
                 holes=[door_hole()], tops=facade_tops or tops, seed=seed + 3)
    return side_len


def window(m, center, width, height, along, color_frame="white", arch=False):
    """Окно в проёме стены: стекло и рамка. along — ось стены ('x' или 'z')."""
    x, y, z = center
    if along == "z":
        m.box("Body", (x, y, z), (0.3, height, width), "glass", bevel=0)
        for dz in (-width / 2, width / 2):
            m.box("Body", (x, y, z + dz), (1.4, height + 0.6, 0.6), color_frame)
        m.box("Body", (x, y - height / 2, z), (1.6, 0.6, width + 1.2), color_frame, studs=False)
        m.box("Body", (x, y + height / 2, z), (1.4, 0.6, width + 0.6), color_frame)
        if arch:
            m.cylinder("Body", (x, y + height / 2, z), width / 2 + 0.3, 1.4, color_frame, axis="x", segments=12)
    else:
        m.box("Body", (x, y, z), (width, height, 0.3), "glass", bevel=0)
        for dx in (-width / 2, width / 2):
            m.box("Body", (x + dx, y, z), (0.6, height + 0.6, 1.4), color_frame)
        m.box("Body", (x, y - height / 2, z), (width + 1.2, 0.6, 1.6), color_frame)
        m.box("Body", (x, y + height / 2, z), (width + 0.6, 0.6, 1.4), color_frame)


def door_frame(m, color="white"):
    for x in (-DOOR_W / 2 - 0.4, DOOR_W / 2 + 0.4):
        m.box("Body", (x, DOOR_H / 2, FACADE), (0.8, DOOR_H, 1.6), color)
    m.box("Body", (0, DOOR_H + 0.4, FACADE), (DOOR_W + 1.6, 0.8, 1.6), color, studs=False)


def column(m, x, z, height, color="white", radius=0.9, base=2.4):
    m.box("Body", (x, 0.4, z), (base, 0.8, base), color, studs=True)
    m.cylinder("Body", (x, height / 2, z), radius, height - 1.6, color, segments=12)
    m.box("Body", (x, height - 0.4, z), (base, 0.8, base), color)


def lamp_post(m, x, z, role="Decor"):
    m.box(role, (x, 0.4, z), (1.6, 0.8, 1.6), "darkgray")
    m.cylinder(role, (x, 3.2, z), 0.3, 5.6, "black", segments=8)
    m.box(role, (x, 6.6, z), (1.4, 1.6, 1.4), "yellow")
    m.box(role, (x, 7.6, z), (1.8, 0.4, 1.8), "black", studs=True)


def flag(m, x, y, z, color="red", height=6.0, role="Decor"):
    m.cylinder(role, (x, y + height / 2, z), 0.2, height, "lightgray", segments=6)
    m.box(role, (x, y + height - 1.2, z + 1.6), (0.2, 2.0, 3.0), color, bevel=0)
    m.sphere(role, (x, y + height + 0.3, z), 0.35, "gold", segments=8, rings=5)


def statue(m, x, z, color, pedestal="marble", role="Decor", kind="figure"):
    """Статуя на постаменте: человечек или лев из кирпичей."""
    m.box(role, (x, 1.0, z), (3.2, 2.0, 3.2), pedestal, studs=False)
    m.box(role, (x, 2.2, z), (3.6, 0.4, 3.6), "gold" if pedestal != "gold" else "darkgold")
    y = 2.4
    if kind == "lion":
        m.box(role, (x, y + 1.2, z + 0.4), (2.0, 2.4, 3.2), color)  # тело
        m.box(role, (x, y + 2.8, z - 1.2), (2.4, 2.4, 1.6), color)  # грива
        m.box(role, (x, y + 2.6, z - 2.1), (1.2, 1.2, 0.6), color)  # морда
        m.box(role, (x, y + 3.0, z + 2.2), (0.4, 0.4, 1.2), color)  # хвост
    else:
        m.box(role, (x, y + 1.2, z), (2.0, 2.4, 1.2), color)  # ноги
        m.box(role, (x, y + 3.4, z), (2.4, 2.0, 1.2), color)  # тело
        for side in (-1, 1):
            m.box(role, (x + side * 1.5, y + 3.4, z), (0.6, 2.0, 0.8), color)
        m.cylinder(role, (x, y + 5.1, z), 0.7, 1.4, color, segments=10)
        m.cylinder(role, (x, y + 6.0, z), 0.35, 0.4, color, segments=8)


# ---------------------------------------------------------------- музеи
def museum_ruins():
    m = Model("Museum1")
    colors = [ACC, ACC, ACC, ("Body", "stone"), ("Body", "darkstone")]

    def tops(t):
        return 4.8 + 2.4 * math.floor(noise(math.floor(t / 4), 1) * 3)

    def facade_tops(t):
        # Над входом держится кусок стены под вывеску.
        if HALF - 10 <= t <= HALF + 10:
            return 14.4
        return tops(t)

    shell(m, 14.4, colors, seed=11, tops=tops, facade_tops=facade_tops,
          side_windows=[(-6, 0, 2.4, 4.8)], back_windows=[(6, 14, 2.4, 4.8)])
    door_frame(m, "lightwood")
    # Доски, прибитые крест-накрест на проломах боковых стен.
    for sx in (-HALF - 0.2, HALF + 0.2):
        for angle in (25, -25):
            rot = Matrix.Rotation(math.radians(angle), 4, "Y")
            m.box("Body", (sx, 3.6, -3), (0.4, 0.6, 7.5), "lightwood", rotation=rot)
    for angle in (20, -20):
        m.box("Body", (10, 3.6, HALF + 0.2), (9.5, 0.6, 0.4), "lightwood", rotation=Matrix.Rotation(math.radians(angle), 4, "Y"))
    # Остатки крыши: балки над рядами витрин (на них висят лампы) и обломок кровли.
    for z in (-2, 12, 19):
        m.box("Body", (0, 13.9, z), (HALF * 2 - 0.2, 1.0, 1.0), "darkwood")
    m.box("Body", (0, 14.6, (FACADE + HALF) / 2), (1.0, 0.6, HALF - FACADE), "darkwood")
    # Уцелевший кусок кровли над задним правым углом.
    m.box("AccentDark", (12, 13.2, 20), (16, 0.6, 3.0), "darkred", rotation=Matrix.Rotation(math.radians(-18), 4, "X"))
    for i in range(5):
        m.box("Body", (8 + i * 3.2, 12.3 - i * 0.25, 16.5), (3.0, 0.5, 9.0), "wood" if i % 2 else "darkwood",
              rotation=Matrix.Rotation(math.radians(-14), 4, "X"))
    # Груды кирпичей в углах.
    for cx, cz, seed in ((-18.5, -15.5, 3), (18.5, -14.5, 5), (-18.5, 18.5, 9), (17.5, 4.5, 13)):
        for i in range(6):
            r1, r2, r3 = noise(i, seed), noise(i + 9, seed), noise(i + 17, seed)
            color = ACC if r3 > 0.5 else ("Body", "stone")
            rot = Matrix.Rotation(r1 * 3.0, 4, "Z")
            m.box(color[0], (cx + (r1 - 0.5) * 3, 0.6 + (i // 3) * 1.2, cz + (r2 - 0.5) * 3), (2.0, 1.2, 4.0),
                  color[1], rotation=rot, studs=i >= 3)
    # Декор (уровень 2): фонари у входа, флажок на стене, ящики с цветами.
    for x in (-9.5, 9.5):
        lamp_post(m, x, -21)
    flag(m, 0, 14.4, FACADE, "orange", height=4.0)
    for x in (-14, 14):
        m.box("Decor", (x, 0.6, -20.6), (4.0, 1.2, 1.6), "wood")
        for k in range(3):
            m.sphere("Decor", (x - 1.2 + k * 1.2, 1.6, -20.6), 0.55, "pink" if k % 2 else "yellow", segments=8, rings=5)
    return m, {"wallHeight": 14.4, "signY": SIGN_Y, "lampHeight": 13.4}


def museum_house():
    m = Model("Museum2")
    h = 14.4
    colors = [ACC, ACC, ACC, ACC, ("Body", "cream")]
    windows = [(-12, -5, 4.0, 9.6), (5, 12, 4.0, 9.6)]
    shell(m, h, colors, seed=21, side_windows=windows, back_windows=[(-4, 4, 4.0, 9.6)], studs_top=False)
    door_frame(m, "white")
    for sx in (-HALF + 0.5, HALF - 0.5):
        for z0, z1, y0, y1 in windows:
            window(m, (sx, (y0 + y1) / 2, (z0 + z1) / 2), z1 - z0, y1 - y0, "z")
    window(m, (0, 6.8, HALF - 0.5), 8, 5.6, "x")
    # Белые угловые камни.
    for x in (-HALF + 0.5, HALF - 0.5):
        for z in (FACADE, HALF - 0.5):
            for k in range(6):
                m.box("Body", (x, 1.2 + k * 2.4, z), (1.6, 2.4, 1.6), "white" if k % 2 == 0 else "cream")
    # Карниз и двускатная крыша, фронтоны.
    m.box("Body", (0, h + 0.4, (FACADE + HALF) / 2), (2 * HALF + 1.6, 0.8, HALF - FACADE + 1.6), "white")
    m.gable("AccentDark", (0, h + 0.8, (FACADE + HALF) / 2), 2 * HALF + 2.4, HALF - FACADE + 2.4, 9.6, "darkred",
            along="z", pieces=7)
    for z in (FACADE, HALF - 0.5):
        m.triangle_wall("Accent", (0, h + 0.8, z), 2 * HALF - 1, 9.0, 1.0, "red")
        m.cylinder("Body", (0, h + 4.4, z - 0.6 if z < 0 else z + 0.6), 1.6, 0.4, "white", axis="z", segments=12)
    # Труба.
    for k in range(4):
        m.box("Body", (13, h + 5 + k * 2.4, 10), (3.2, 2.4, 3.2), "darkred" if k % 2 else "terracotta", studs=k == 3)
    # Козырёк над дверью — ниже вывески нельзя, поэтому у дверей фонари.
    for x in (-DOOR_W / 2 - 1.6, DOOR_W / 2 + 1.6):
        m.box("Body", (x, 8.0, FACADE - 0.9), (0.8, 0.8, 1.2), "black")
        m.box("Body", (x, 7.0, FACADE - 1.3), (1.0, 1.4, 1.0), "yellow")
    # Декор (уровень 4): ящики с цветами под окнами, фонари у входа, флаг на коньке.
    for sx in (-HALF - 0.8, HALF + 0.8):
        for z0, z1, _, _ in windows:
            m.box("Decor", (sx, 3.4, (z0 + z1) / 2), (1.4, 1.0, z1 - z0), "wood")
            for k in range(3):
                m.sphere("Decor", (sx, 4.2, z0 + 1.2 + k * (z1 - z0 - 2.4) / 2), 0.7, "red" if k % 2 else "pink",
                         segments=8, rings=5)
    for x in (-10, 10):
        lamp_post(m, x, -21)
    flag(m, 0, h + 10.2, (FACADE + HALF) / 2, "blue")
    return m, {"wallHeight": h, "signY": SIGN_Y, "lampHeight": h - 2.5}


def portico(m, xs, z, height, pediment_w, pediment_h, color="white"):
    for x in xs:
        column(m, x, z, height, color)
    m.box("Body", (0, height + 0.6, z), (pediment_w, 1.2, 3.2), "cream")
    m.box("Body", (0, height + 1.6, z), (pediment_w + 1, 0.8, 3.6), color)
    m.triangle_wall("Body", (0, height + 2.0, z), pediment_w, pediment_h, 3.0, color)
    m.triangle_wall("Accent", (0, height + 2.6, z - 1.6), pediment_w - 6, pediment_h - 2.2, 0.4, "red")


def museum_gallery():
    m = Model("Museum3")
    h = 14.4
    colors = [ACC, ACC, ACC, ACC, ACC, ("Body", "cream")]
    windows = [(-13, -7, 3.0, 10.0), (-1, 5, 3.0, 10.0), (11, 17, 3.0, 10.0)]
    shell(m, h, colors, seed=31, side_windows=windows, studs_top=False)
    door_frame(m, "cream")
    for sx in (-HALF + 0.5, HALF - 0.5):
        for z0, z1, y0, y1 in windows:
            window(m, (sx, (y0 + y1) / 2, (z0 + z1) / 2), z1 - z0, y1 - y0, "z", arch=True)
    # Цоколь, карниз с пупырышками и плоская крыша с парапетом.
    for x in (-HALF - 0.3, HALF + 0.3):
        m.box("Body", (x, 0.8, (FACADE + HALF) / 2), (0.8, 1.6, HALF - FACADE), "stone")
    m.box("Body", (0, 0.8, HALF + 0.3), (2 * HALF + 1.4, 1.6, 0.8), "stone")
    m.box("Body", (0, h + 0.4, (FACADE + HALF) / 2), (2 * HALF + 1.2, 0.8, HALF - FACADE + 1.2), "white")
    m.box("AccentDark", (0, h + 1.2, (FACADE + HALF) / 2), (2 * HALF - 1, 0.8, HALF - FACADE - 1), "darkred", bevel=0)
    for x in (-HALF, HALF):
        m.box("Body", (x, h + 1.6, (FACADE + HALF) / 2), (1.2, 1.6, HALF - FACADE), "white", studs=True)
    m.box("Body", (0, h + 1.6, HALF), (2 * HALF, 1.6, 1.2), "white", studs=True)
    portico(m, (-17, -9, 9, 17), -21.0, h, 40, 7)
    # Ступени перед входом (ниже уровня пола — к аллее).
    m.box("Body", (0, -0.35, -22.8), (20, 0.7, 1.6), "stone", studs=True)
    m.box("Body", (0, -1.05, -23.8), (22, 0.7, 1.6), "darkstone", studs=True)
    # Декор (уровень 6): знамёна между колоннами и львы у входа.
    for x in (-13, 13):
        m.box("Decor", (x, 10, -21.4), (3.2, 6.0, 0.2), "velvet", bevel=0)
        m.box("Decor", (x, 13.2, -21.4), (3.8, 0.4, 0.4), "gold")
        m.box("Decor", (x, 7.0, -21.5), (3.2, 0.6, 0.2), "gold", bevel=0)
    statue(m, -9.5, -25.5, "gold", kind="lion")
    statue(m, 9.5, -25.5, "gold", kind="lion")
    return m, {"wallHeight": h, "signY": SIGN_Y, "lampHeight": h - 2.5}


def museum_dome():
    m = Model("Museum4")
    h = 16.8
    colors = [ACC, ACC, ACC, ACC, ACC, ACC, ("Body", "cream")]
    windows = [(-12, -7, 3.0, 11.0), (-1, 4, 3.0, 11.0), (10, 15, 3.0, 11.0)]
    shell(m, h, colors, seed=41, side_windows=windows, studs_top=False,
          back_windows=[(-10, -5, 3.0, 11.0), (5, 10, 3.0, 11.0)])
    door_frame(m, "cream")
    for sx in (-HALF + 0.5, HALF - 0.5):
        for z0, z1, y0, y1 in windows:
            window(m, (sx, (y0 + y1) / 2, (z0 + z1) / 2), z1 - z0, y1 - y0, "z", arch=True)
            # Пилястры между окнами.
        for z in (-16, -4.5, 7, 18):
            m.box("Body", (sx + (0.9 if sx > 0 else -0.9), h / 2, z), (0.8, h, 1.8), "white")
    for x0, x1 in ((-10, -5), (5, 10)):
        window(m, ((x0 + x1) / 2, 7.0, HALF - 0.5), x1 - x0, 8.0, "x")
    m.box("Body", (0, h + 0.4, (FACADE + HALF) / 2), (2 * HALF + 1.6, 0.8, HALF - FACADE + 1.6), "white")
    m.box("AccentDark", (0, h + 1.2, (FACADE + HALF) / 2), (2 * HALF - 1, 0.8, HALF - FACADE - 1), "darkred", bevel=0)
    for x in (-HALF, HALF):
        m.box("Body", (x, h + 1.6, (FACADE + HALF) / 2), (1.2, 1.6, HALF - FACADE), "white", studs=True)
    m.box("Body", (0, h + 1.6, HALF), (2 * HALF, 1.6, 1.2), "white", studs=True)
    portico(m, (-19, -13.5, -8, 8, 13.5, 19), -21.0, h, 42, 8)
    # Барабан с окнами и купол с фонариком.
    cz = 4.0
    m.cylinder("Body", (0, h + 3.6, cz), 9.0, 4.4, "cream", segments=20)
    for k in range(10):
        a = 2 * math.pi * k / 10
        m.box("Body", (9.1 * math.cos(a), h + 3.6, cz + 9.1 * math.sin(a)), (1.0, 2.6, 1.0), "glass", bevel=0)
    m.cylinder("Body", (0, h + 6.0, cz), 9.6, 0.6, "white", segments=20)
    m.sphere("AccentDark", (0, h + 6.2, cz), 9.0, "darkred", segments=20, rings=12, half=True)
    m.cylinder("Body", (0, h + 16.2, cz), 1.2, 2.4, "white", segments=10)
    m.sphere("Body", (0, h + 18.0, cz), 1.0, "gold", segments=10, rings=6)
    m.box("Body", (0, -0.35, -23.2), (24, 0.7, 1.6), "stone", studs=True)
    m.box("Body", (0, -1.05, -24.2), (26, 0.7, 1.6), "darkstone", studs=True)
    # Декор (уровень 8): статуи у входа, флаги по углам крыши, прожекторы.
    statue(m, -10.5, -25.5, "marble", pedestal="darkstone")
    statue(m, 10.5, -25.5, "marble", pedestal="darkstone")
    for x in (-HALF + 1, HALF - 1):
        for z in (FACADE + 1, HALF - 1):
            flag(m, x, h + 2.4, z, "velvet", height=5.0)
    for x in (-16, 16):
        m.box("Decor", (x, 0.5, -23.5), (1.4, 1.0, 1.4), "darkgray")
        m.box("Decor", (x, 1.3, -23.5), (1.0, 0.6, 1.0), "star")
    return m, {"wallHeight": h, "signY": SIGN_Y, "lampHeight": h - 3.0}


def museum_palace():
    m = Model("Museum5")
    h = 19.2
    colors = [ACC, ACC, ACC, ACC, ("Body", "cream"), ACC]
    windows = [(-12, -7, 3.0, 12.0), (-1, 4, 3.0, 12.0), (8, 13, 3.0, 12.0)]
    shell(m, h, colors, seed=51, side_windows=windows, studs_top=False)
    door_frame(m, "gold")
    for sx in (-HALF + 0.5, HALF - 0.5):
        for z0, z1, y0, y1 in windows:
            window(m, (sx, (y0 + y1) / 2, (z0 + z1) / 2), z1 - z0, y1 - y0, "z", color_frame="gold", arch=True)
    # Золотой пояс и зубцы по верху.
    for x in (-HALF - 0.3, HALF + 0.3):
        m.box("Body", (x, 7.6, (FACADE + HALF) / 2), (0.6, 0.8, HALF - FACADE), "gold")
    m.box("Body", (0, 7.6, HALF + 0.3), (2 * HALF, 0.8, 0.6), "gold")
    m.box("Body", (0, h + 0.4, (FACADE + HALF) / 2), (2 * HALF + 1.2, 0.8, HALF - FACADE + 1.2), "cream")
    m.box("AccentDark", (0, h + 1.0, (FACADE + HALF) / 2), (2 * HALF - 1, 0.4, HALF - FACADE - 1), "darkred", bevel=0)
    for x in range(-20, 21, 4):
        for z in (FACADE, HALF - 0.5):
            m.box("Trim", (x, h + 1.8, z), (2.0, 2.0, 1.4), "stone", studs=True)
    for z in range(-16, 21, 4):
        for x in (-HALF + 0.5, HALF - 0.5):
            m.box("Trim", (x, h + 1.8, z), (1.4, 2.0, 2.0), "stone", studs=True)
    # Четыре башни: тело в цвет участка, кольцо зубцов, шатёр, золотой шар.
    for tx in (-19.5, 19.5):
        for tz in (FACADE - 0.5, 19.5):
            for k in range(11):
                role, color = (ACC if k % 3 else ("Body", "cream"))
                m.cylinder(role, (tx, 1.2 + k * 2.4, tz), 3.6, 2.35, color, segments=14)
            top = 26.4
            for j in range(8):
                a = 2 * math.pi * j / 8
                m.box("Trim", (tx + 3.6 * math.cos(a), top + 1.0, tz + 3.6 * math.sin(a)), (1.4, 2.0, 1.4), "stone",
                      studs=True, rotation=Matrix.Rotation(-a, 4, "Z"))
            m.cylinder("AccentDark", (tx, top + 2.0 + 4.5, tz), 4.4, 9.0, "darkred", segments=14, radius2=0.0)
            m.sphere("Body", (tx, top + 11.4, tz), 0.8, "gold", segments=10, rings=6)
    # Ворота: золотая арка и балкон над вывеской.
    for k in range(11):
        a = math.pi * k / 10  # полуокружность над проёмом
        m.box("Body", ((DOOR_W / 2 + 0.6) * math.cos(a), DOOR_H - 1.0 + (DOOR_W / 2 + 0.6) * 0.45 * math.sin(a),
                       FACADE - 0.9), (1.4, 1.4, 0.8), "gold")
    m.box("Body", (0, 14.6, FACADE - 1.6), (16, 0.8, 3.2), "cream", studs=False)
    for x in range(-7, 8, 2):
        m.cylinder("Body", (x, 15.8, FACADE - 2.9), 0.25, 1.6, "gold", segments=6)
    m.box("Body", (0, 16.8, FACADE - 2.9), (16, 0.4, 0.4), "gold")
    # Золотой купол на барабане.
    cz = 3.0
    m.cylinder("Body", (0, h + 3.4, cz), 8.0, 4.0, "cream", segments=20)
    for k in range(12):
        a = 2 * math.pi * k / 12
        m.box("Body", (8.1 * math.cos(a), h + 3.4, cz + 8.1 * math.sin(a)), (0.8, 2.4, 0.8), "gold", bevel=0)
    m.sphere("Body", (0, h + 5.4, cz), 8.0, "gold", segments=20, rings=12, half=True)
    m.cylinder("Body", (0, h + 14.4, cz), 0.6, 3.0, "gold", segments=8, radius2=0.1)
    # Парадная лестница.
    for k in range(3):
        m.box("Body", (0, -0.35 - k * 0.7, -22.6 - k * 1.2), (22 + k * 3, 0.7, 1.6), "marble", studs=True)
    # Декор (уровень 10): золотые статуи, флаги на башнях, светильники.
    statue(m, -10.5, -26.0, "gold", pedestal="marble")
    statue(m, 10.5, -26.0, "gold", pedestal="marble")
    for tx in (-19.5, 19.5):
        for tz in (FACADE - 0.5, 19.5):
            flag(m, tx, 38.2, tz, "velvet", height=4.0)
    for x in (-16, -8.5, 8.5, 16):
        m.box("Decor", (x, 0.6, -24.6), (1.2, 1.2, 1.2), "gold")
        m.sphere("Decor", (x, 1.8, -24.6), 0.7, "star", segments=8, rings=5)
    return m, {"wallHeight": h, "signY": SIGN_Y, "lampHeight": h - 3.0}


# ---------------------------------------------------------------- гантели
def plate_studs(m, x, radius, color, outward, count=6, ring=0.55):
    """Пупырышки по кругу на торце диска (outward = '+x' или '-x')."""
    for k in range(count):
        a = 2 * math.pi * k / count
        m.stud("Body", (x, radius * ring * math.cos(a), radius * ring * math.sin(a)), color, up=outward)


def dumbbell(index):
    m = Model(f"Dumbbell{index:02d}")
    if index == 1:  # Деревянная: брёвнышко и круглые чурбаки
        m.cylinder("Body", (0, 0, 0), 1.2, 16, "darkwood", axis="x", segments=8)
        for s in (-1, 1):
            m.cylinder("Body", (s * 5.4, 0, 0), 4.4, 2.0, "wood", axis="x", segments=14)
            m.cylinder("Body", (s * 7.0, 0, 0), 3.8, 1.2, "lightwood", axis="x", segments=14)
            plate_studs(m, s * 7.6, 3.8, "lightwood", "+x" if s > 0 else "-x")
    elif index == 2:  # Каменная: грубые каменные кубы
        m.cylinder("Body", (0, 0, 0), 1.1, 15, "darkstone", axis="x", segments=8)
        for s in (-1, 1):
            m.box("Body", (s * 5.8, 0, 0), (4.8, 6.4, 6.4), "stone", rotation=Matrix.Rotation(math.radians(8 * s), 4, "X"))
            m.box("Body", (s * 5.6, 3.6, 0.6), (3.6, 1.2, 4.0), "darkstone", studs=True)
            m.box("Body", (s * 6.4, -0.8, -3.6), (2.4, 2.4, 1.2), "darkstone")
    elif index == 3:  # Железная: стопка блинов
        m.cylinder("Body", (0, 0, 0), 0.8, 17, "steel", axis="x", segments=10)
        for s in (-1, 1):
            for k, (r, w) in enumerate(((4.6, 0.9), (4.0, 0.9), (3.2, 0.9), (2.4, 0.9))):
                m.cylinder("Body", (s * (4.6 + k * 1.0), 0, 0), r, w, "iron" if k % 2 == 0 else "darkgray", axis="x",
                           segments=18)
            m.cylinder("Body", (s * 3.6, 0, 0), 1.3, 0.8, "steel", axis="x", segments=10)
            plate_studs(m, s * 8.05, 2.4, "iron", "+x" if s > 0 else "-x", count=4, ring=0.5)
    elif index == 4:  # Бронзовая: шестигранные головы
        m.cylinder("Body", (0, 0, 0), 0.9, 14, "steel", axis="x", segments=8)
        for k in range(-3, 4):
            m.cylinder("Body", (k * 0.9, 0, 0), 1.05, 0.3, "darkgray", axis="x", segments=8)
        for s in (-1, 1):
            m.cylinder("Body", (s * 6.0, 0, 0), 4.2, 4.4, "bronze", axis="x", segments=6)
            m.cylinder("Body", (s * 8.4, 0, 0), 3.2, 0.5, "darkbronze", axis="x", segments=6)
            m.cylinder("Body", (s * 3.6, 0, 0), 3.4, 0.5, "darkbronze", axis="x", segments=6)
    elif index == 5:  # Серебряная: шары
        m.cylinder("Body", (0, 0, 0), 0.9, 12, "steel", axis="x", segments=10)
        for k in (-1.6, 0, 1.6):
            m.cylinder("Body", (k, 0, 0), 1.1, 0.5, "silver", axis="x", segments=10)
        for s in (-1, 1):
            m.sphere("Body", (s * 6.4, 0, 0), 4.2, "silver", segments=16, rings=10)
            m.cylinder("Body", (s * 3.0, 0, 0), 1.6, 1.0, "lightgray", axis="x", segments=12)
            m.stud("Body", (s * 10.6, 0, 0), "silver", up="+x" if s > 0 else "-x")
    elif index == 6:  # Золотая: диски с зубцами-короной и рубин в центре
        m.cylinder("Body", (0, 0, 0), 1.0, 15, "darkgold", axis="x", segments=10)
        m.sphere("Body", (0, 0, 0), 1.6, "red", segments=10, rings=6)
        for s in (-1, 1):
            m.cylinder("Body", (s * 5.6, 0, 0), 4.6, 2.2, "gold", axis="x", segments=20)
            m.cylinder("Body", (s * 7.0, 0, 0), 3.4, 0.8, "darkgold", axis="x", segments=20)
            for k in range(8):
                a = 2 * math.pi * k / 8
                rot = Matrix.Rotation(a, 4, "X")  # остриё по радиусу
                m.cylinder("Body", (s * 5.6, 5.4 * math.cos(a), 5.4 * math.sin(a)), 0.7, 1.8, "gold",
                           segments=4, radius2=0.0, rotation=rot)
            m.sphere("Body", (s * 7.6, 0, 0), 1.0, "red", segments=10, rings=6)
    elif index == 7:  # Изумрудная: восьмигранные кристаллы
        m.cylinder("Body", (0, 0, 0), 0.9, 13, "darkemerald", axis="x", segments=8)
        for s in (-1, 1):
            # Остриём наружу: у левого камня низ-конус в -x, у правого — в +x.
            m.gem("Crystal", (s * 5.6, 0, 0), 4.0, 1.4, 4.4, "emerald", segments=8, axis="x" if s < 0 else "-x",
                  table=0.55)
            m.cylinder("Body", (s * 3.4, 0, 0), 2.0, 0.8, "darkemerald", axis="x", segments=8)
            for k in range(3):
                a = 2 * math.pi * k / 3 + 0.5
                m.cylinder("Crystal", (s * 4.6, 3.6 * math.cos(a), 3.6 * math.sin(a)), 0.8, 2.6, "emerald", segments=6,
                           radius2=0.0, rotation=Matrix.Rotation(a, 4, "X"))
    elif index == 8:  # Алмазная: два бриллианта остриём наружу
        m.cylinder("Body", (0, 0, 0), 0.8, 12, "silver", axis="x", segments=10)
        for s in (-1, 1):
            m.gem("Crystal", (s * 5.0, 0, 0), 4.6, 1.6, 4.8, "diamond", segments=12, axis="x" if s < 0 else "-x",
                  table=0.55)
            m.cylinder("Body", (s * 3.2, 0, 0), 1.6, 0.8, "silver", axis="x", segments=12)
    elif index == 9:  # Неоновая: светящиеся кольца на тёмном ядре
        m.cylinder("Body", (0, 0, 0), 0.9, 15, "black", axis="x", segments=10)
        for k in (-2.4, 0, 2.4):
            m.torus("Glow", (k, 0, 0), 1.1, 0.25, "neonpink", axis="x", segments=12, minor_segments=6)
        for s in (-1, 1):
            m.cylinder("Body", (s * 5.8, 0, 0), 3.4, 4.0, "black", axis="x", segments=16)
            for k, x in enumerate((4.4, 5.8, 7.2)):
                m.torus("Glow", (s * x, 0, 0), 3.6 + (0.3 if k == 1 else 0), 0.35, "neonpink", axis="x")
            m.cylinder("Body", (s * 8.0, 0, 0), 2.0, 0.5, "neoncyan", axis="x", segments=16)
    elif index == 10:  # Космическая: планеты с кольцами, луны и звёзды
        m.cylinder("Body", (0, 0, 0), 0.9, 14, "cosmicdark", axis="x", segments=10)
        for k in (-2, 0, 2):
            m.gem("Body", (k, 1.0, 0), 0.6, 0.3, 0.3, "star", segments=4, axis="y")
        for s in (-1, 1):
            m.sphere("Body", (s * 6.4, 0, 0), 4.2, "cosmic", segments=16, rings=10)
            m.sphere("Body", (s * 6.4, 0, 0), 4.25, "cosmicdark", segments=16, rings=10,
                     scale=(1.0, 0.25, 1.0))
            m.torus("Glow", (s * 6.4, 0, 0), 6.2, 0.35, "neoncyan", axis="y", segments=24)
            m.sphere("Body", (s * 6.4, 4.6, 4.0), 0.9, "star", segments=8, rings=5)
    return m


# ---------------------------------------------------------------- сборка
bpy.ops.wm.read_factory_settings(use_empty=True)
palette_path = os.path.join(REPO, "assets", "textures", "model_palette.png")
material = lego.make_palette(palette_path)
collection = bpy.context.scene.collection

layout = {"museums": {}, "dumbbells": {}}
objects = []
museums = [museum_ruins, museum_house, museum_gallery, museum_dome, museum_palace]
for i, build in enumerate(museums):
    model, anchors = build()
    offset = (i * 70, 0, 0)
    roles = model.build(material, collection, offset)
    layout["museums"][model.name] = {"roles": roles, **anchors}
    objects += [o for o in collection.objects if o.name.startswith(model.name + "_")]
for index in range(1, 11):
    model = dumbbell(index)
    offset = ((index - 1) % 5 * 24, 0, 120 + (index - 1) // 5 * 18)
    roles = model.build(material, collection, offset)
    layout["dumbbells"][model.name] = {"roles": roles}
    objects += [o for o in collection.objects if o.name.startswith(model.name + "_")]

models_dir = os.path.join(REPO, "assets", "models")
os.makedirs(models_dir, exist_ok=True)
lego.export_fbx(os.path.join(models_dir, "Pack1.fbx"), objects)
lego.write_json(os.path.join(models_dir, "Pack1.layout.json"), layout)

# Превью: каждый музей спереди-сбоку и все гантели.
lego.setup_render(900)
for i in range(5):
    name = f"Museum{i + 1}"
    vis = [o for o in objects if o.name.startswith(name + "_")]
    ox = i * 70
    lego.render(os.path.join(PREVIEWS, f"{name}.png"), (ox + 46, 34, -58), (ox, 9, 0), vis)
    lego.render(os.path.join(PREVIEWS, f"{name}_front.png"), (ox, 9, -70), (ox, 9, 0), vis)
vis = [o for o in objects if o.name.startswith("Dumbbell")]
lego.render(os.path.join(PREVIEWS, "Dumbbells.png"), (48, 70, 185), (48, 0, 129), vis, lens=32)

for group, items in layout.items():
    for name, data in items.items():
        tris = {role: info["triangles"] for role, info in data["roles"].items()}
        print(f"PACK1 {name} triangles={tris}")
print("PACK1_OK")
