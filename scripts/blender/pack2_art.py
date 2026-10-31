"""Произведения искусства, пачка 1 (D37, D38): объёмные предметы коллекций боссов 1–3 → assets/models/Pack2_art.fbx.

Стиль: stylized Roblox — крупные чистые формы с мягкой фаской, яркие гармоничные цвета, читаемый силуэт; без
фотореализма. Модель — набор деталей по цветам («ролям», как у гантелей): игра ставит MeshPart цвет и материал.
Масштаб — игровой (1 = 1 стад), низ модели на y = 0, лицевая сторона смотрит в -z, размеры — как у заготовок в
Config/Items. Картины (Epic) — отдельной пачкой, мозаикой с изображений в общественном достоянии.

Запуск из корня репозитория (или через Blender MCP — execute_blender_code с exec этого файла):
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup \\
    --python scripts/blender/pack2_art.py -- . <папка превью>
Пишет assets/models/Pack2_art.fbx, .layout.json и превью: <id>.png и Pack2_sheet.png.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lego  # noqa: E402
from lego import Model, rot  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [".", "previews"]
REPO, PREVIEWS = os.path.abspath(argv[0]), os.path.abspath(argv[1])
os.makedirs(PREVIEWS, exist_ok=True)

BUDGET = 3000  # треугольников на предмет (D33)
B = 0.06  # фаска мелких деталей
B2 = 0.1  # фаска крупных

lego.PALETTE.update({
    "folkblue": "2F6FD6", "plum": "6B2E5F", "porcelain": "F7F3EA", "cobalt": "1F3F9A", "marble": "ECE8DF",
    "plaster": "EFEDE6", "straw": "E8C96A", "crate": "C49A68", "horsewhite": "F5EFE2", "brass2": "E0B04A",
})


# 1. Глиняная свистулька (дымковская птица): белый корпус, красный хвост-веер, роспись кружками.
def folk_whistle(m):
    m.cylinder("Body", (0, 0.1, 0.05), 0.48, 0.2, "red", bevel=B)
    m.sphere("Body", (0, 0.72, 0.12), 0.5, "porcelain", segments=16, rings=10, scale=(0.85, 0.9, 1.15))
    m.hull("Body", [(-0.32, 0.55, 0.45), (0.32, 0.55, 0.45), (-0.5, 1.55, 0.95), (0.5, 1.55, 0.95),
                    (0, 1.7, 0.85), (0, 0.9, 0.7)], "red", bevel=0.04)
    for i, x in enumerate((-0.3, 0, 0.3)):
        m.box("Body", (x, 1.35 + (0.08 if i == 1 else 0), 0.92), (0.14, 0.42, 0.06), "yellow", bevel=0.02)
    m.sphere("Body", (0, 1.25, -0.34), 0.27, "porcelain", segments=14, rings=8)
    m.cylinder("Body", (0, 1.22, -0.64), 0.07, 0.2, "yellow", axis="z", radius2=0.02, bevel=0)
    for k, y in enumerate((1.53, 1.6, 1.53)):
        m.box("Body", (0, y, -0.42 + k * 0.12), (0.06, 0.18, 0.12), "red", bevel=0.02)
    for x in (-0.14, 0.14):
        m.sphere("Body", (x, 1.3, -0.56), 0.04, "black", segments=8, rings=5)
    for (x, y, z), c in (((-0.42, 0.75, -0.05), "folkblue"), ((0.42, 0.75, -0.05), "folkblue"),
                         ((-0.36, 0.95, 0.3), "red"), ((0.36, 0.95, 0.3), "red"), ((0, 0.62, -0.5), "yellow"),
                         ((-0.25, 0.5, -0.35), "red"), ((0.25, 0.5, -0.35), "red")):
        m.sphere("Body", (x, y, z), 0.09, c, segments=10, rings=6)


# 2. Расписной поднос (жостовский): чёрный овал с золотой каймой и букетом, на деревянной подставке.
def painted_tray(m):
    m.box("Body", (0, 0.1, 0.05), (1.7, 0.2, 0.6), "darkwood", bevel=B)
    m.box("Body", (0, 0.24, 0.05), (1.4, 0.1, 0.28), "wood", bevel=0.03)
    m.cylinder("Body", (0, 1.35, 0.05), 1.15, 0.12, "black", axis="z", segments=28, bevel=0.03)
    m.torus("Body", (0, 1.35, 0.05), 1.12, 0.07, "gold", axis="z", segments=28, minor_segments=6)
    m.torus("Body", (0, 1.35, -0.02), 0.9, 0.025, "gold", axis="z", segments=28, minor_segments=4)
    for (x, y), r, c in (((-0.3, 1.45), 0.24, "red"), ((0.28, 1.3), 0.2, "pink"), ((0.02, 1.78), 0.15, "yellow"),
                         ((-0.05, 1.05), 0.16, "orange"), ((0.45, 1.68), 0.11, "white")):
        m.sphere("Body", (x, y, -0.07), r, c, segments=12, rings=8, scale=(1, 1, 0.45))
        m.sphere("Body", (x, y, -0.13), r * 0.35, "yellow" if c != "yellow" else "orange", segments=8, rings=5,
                 scale=(1, 1, 0.5))
    for (x, y, a) in ((-0.6, 1.2, 30), (0.62, 1.42, -35), (-0.45, 1.75, -20), (0.3, 0.95, 50), (-0.2, 0.85, -60)):
        m.box("Body", (x, y, -0.06), (0.36, 0.13, 0.05), "leaf", bevel=0.02, rotation=rot(z=a))


# 3. Матрёшка-великан и маленькая рядом.
def doll(m, x, s):
    m.cylinder("Body", (x, 0.62 * s, 0), 0.78 * s, 1.2 * s, "red", radius2=0.6 * s, segments=22, bevel=0.05 * s)
    m.sphere("Body", (x, 1.62 * s, 0), 0.58 * s, "red", segments=18, rings=10)
    m.cylinder("Body", (x, 1.6 * s, -0.5 * s), 0.36 * s, 0.12 * s, "porcelain", axis="z", segments=18, bevel=0.02)
    m.box("Body", (x, 1.86 * s, -0.48 * s), (0.5 * s, 0.1 * s, 0.1 * s), "yellow", bevel=0.02)
    for dx in (-0.12, 0.12):
        m.sphere("Body", (x + dx * s, 1.64 * s, -0.6 * s), 0.035 * s, "black", segments=8, rings=4)
        m.sphere("Body", (x + dx * 1.6 * s, 1.5 * s, -0.58 * s), 0.06 * s, "pink", segments=8, rings=4)
    m.box("Body", (x, 1.45 * s, -0.6 * s), (0.08 * s, 0.04 * s, 0.03 * s), "red", bevel=0.01)
    m.box("Body", (x, 0.62 * s, -0.66 * s), (0.86 * s, 0.9 * s, 0.1 * s), "yellow", bevel=0.04 * s)
    m.sphere("Body", (x, 0.72 * s, -0.74 * s), 0.2 * s, "red", segments=12, rings=8, scale=(1, 1, 0.5))
    m.sphere("Body", (x, 0.72 * s, -0.79 * s), 0.08 * s, "yellow", segments=8, rings=5, scale=(1, 1, 0.5))
    for dx, dy, a in ((-0.22, 0.45, 35), (0.22, 0.45, -35), (0, 0.98, 0)):
        m.box("Body", (x + dx * s, dy * s, -0.74 * s), (0.22 * s, 0.09 * s, 0.04 * s), "leaf", bevel=0.01,
              rotation=rot(z=a))


def nesting_doll(m):
    doll(m, -0.25, 1.0)
    doll(m, 0.82, 0.45)


# 4. Лошадка-качалка: белая в яблоках, красная грива и седло, полозья дугой.
def rocking_horse(m):
    for x in (-0.36, 0.36):
        for k in range(-3, 4):
            a = math.radians(k * 11)
            z, y = 2.3 * math.sin(a), 2.3 * (1 - math.cos(a)) + 0.1
            m.box("Body", (x, y, z), (0.14, 0.14, 0.62), "darkwood", bevel=0.03, rotation=rot(x=-k * 11))
    m.box("Body", (0, 0.35, 0), (0.86, 0.1, 0.12), "darkwood", bevel=0.02)
    for x in (-0.24, 0.24):
        for z in (-0.6, 0.6):
            m.box("Body", (x, 0.68, z), (0.16, 0.7, 0.16), "horsewhite", bevel=0.04, rotation=rot(x=-z * 18))
    m.box("Body", (0, 1.2, 0), (0.62, 0.55, 1.5), "horsewhite", bevel=0.14)
    m.box("Body", (0, 1.62, -0.72), (0.42, 0.8, 0.42), "horsewhite", bevel=0.1, rotation=rot(x=-28))
    m.box("Body", (0, 2.0, -1.0), (0.4, 0.42, 0.7), "horsewhite", bevel=0.1)
    m.box("Body", (0, 1.92, -1.35), (0.34, 0.3, 0.12), "pink", bevel=0.04)
    for x in (-0.13, 0.13):
        m.box("Body", (x, 2.28, -0.86), (0.08, 0.2, 0.08), "horsewhite", bevel=0.02)
        m.sphere("Body", (x * 1.6, 2.08, -1.18), 0.045, "black", segments=8, rings=4)
    for k in range(5):
        m.box("Body", (0, 2.18 - k * 0.2, -0.78 + k * 0.17), (0.12, 0.2, 0.22), "red", bevel=0.03)
    m.box("Body", (0, 1.52, 0.1), (0.7, 0.12, 0.62), "red", bevel=0.04)
    m.box("Body", (0, 1.25, 0.1), (0.74, 0.5, 0.08), "gold", bevel=0.02)
    m.box("Body", (0, 1.15, 0.86), (0.14, 0.55, 0.14), "red", bevel=0.03, rotation=rot(x=30))
    for (x, y, z) in ((0.32, 1.2, -0.35), (-0.32, 1.1, 0.3), (0.32, 1.05, 0.45), (-0.32, 1.3, -0.4)):
        m.sphere("Body", (x, y, z), 0.09, "stone", segments=8, rings=5, scale=(0.4, 1, 1))


# 5. Фарфоровая собачка (стаффордширский спаниель): белая, рыжие пятна, кобальтовый ошейник, золото.
def porcelain_dog(m):
    m.cylinder("Body", (0, 0.08, 0), 0.72, 0.16, "porcelain", segments=24, bevel=0.04)
    m.torus("Body", (0, 0.16, 0), 0.7, 0.035, "gold", axis="y", segments=24, minor_segments=4)
    m.sphere("Body", (0, 0.62, 0.15), 0.5, "porcelain", segments=16, rings=10, scale=(0.85, 1, 1))
    m.sphere("Body", (0, 0.9, -0.15), 0.38, "porcelain", segments=16, rings=10, scale=(0.9, 1.2, 0.9))
    for x in (-0.2, 0.2):
        m.box("Body", (x, 0.42, -0.42), (0.16, 0.6, 0.18), "porcelain", bevel=0.06)
    m.sphere("Body", (0, 1.42, -0.18), 0.36, "porcelain", segments=16, rings=10)
    m.sphere("Body", (0, 1.32, -0.48), 0.17, "porcelain", segments=12, rings=8)
    m.sphere("Body", (0, 1.36, -0.64), 0.05, "black", segments=8, rings=4)
    for x in (-0.13, 0.13):
        m.sphere("Body", (x, 1.5, -0.47), 0.045, "black", segments=8, rings=4)
        m.sphere("Body", (x * 2.6, 1.25, -0.12), 0.17, "orange", segments=10, rings=6, scale=(0.5, 1.6, 0.9))
    m.torus("Body", (0, 1.12, -0.18), 0.3, 0.05, "cobalt", axis="y", segments=18, minor_segments=5)
    m.sphere("Body", (0, 1.08, -0.48), 0.07, "gold", segments=8, rings=5)
    for (x, y, z) in ((0.3, 0.75, 0.3), (-0.32, 0.55, 0.05), (0.18, 0.95, -0.38)):
        m.sphere("Body", (x, y, z), 0.12, "orange", segments=8, rings=5, scale=(0.5, 1, 1))


# 6. Каминные часы: тёмное дерево, арка, белый циферблат в золотом кольце, ножки-шары, маятник.
def mantel_clock(m):
    m.box("Body", (0, 0.72, 0), (1.8, 1.2, 0.8), "darkwood", bevel=B2)
    m.cylinder("Body", (0, 1.32, 0), 0.72, 0.8, "darkwood", axis="z", segments=24, bevel=0.06)
    m.box("Body", (0, 0.16, 0), (2.0, 0.14, 0.92), "wood", bevel=0.04)
    for x in (-0.82, 0.82):
        for z in (-0.32, 0.32):
            m.sphere("Body", (x, 0.07, z), 0.1, "gold", segments=10, rings=6)
    m.cylinder("Body", (0, 1.28, -0.42), 0.48, 0.06, "white", axis="z", segments=24, bevel=0.02)
    m.torus("Body", (0, 1.28, -0.45), 0.5, 0.05, "gold", axis="z", segments=24, minor_segments=5)
    for k in range(12):
        a = math.radians(k * 30)
        m.box("Body", (0.38 * math.sin(a), 1.28 + 0.38 * math.cos(a), -0.46), (0.04, 0.09, 0.02), "black",
              bevel=0.005, rotation=rot(z=-k * 30))
    m.box("Body", (0.08, 1.38, -0.48), (0.04, 0.26, 0.02), "black", bevel=0.005, rotation=rot(z=-35))
    m.box("Body", (-0.1, 1.24, -0.48), (0.035, 0.34, 0.02), "black", bevel=0.005, rotation=rot(z=-110))
    m.box("Body", (0, 0.6, -0.41), (0.5, 0.42, 0.04), "glass", bevel=0.01)
    m.cylinder("Body", (0, 0.52, -0.38), 0.12, 0.04, "gold", axis="z", segments=14, bevel=0.01)
    m.sphere("Body", (0, 2.1, 0), 0.12, "gold", segments=10, rings=6)
    m.cylinder("Body", (0, 2.0, 0), 0.05, 0.12, "gold", segments=8, bevel=0)


# 7. Граммофон: деревянный ящик, чёрная пластинка, латунная труба-раструб.
def gramophone(m):
    m.box("Body", (0, 0.32, 0.1), (1.5, 0.6, 1.5), "wood", bevel=B2)
    m.box("Body", (0, 0.04, 0.1), (1.6, 0.08, 1.6), "darkwood", bevel=0.03)
    m.box("Body", (0, 0.32, -0.66), (1.0, 0.24, 0.04), "gold", bevel=0.01)
    m.cylinder("Body", (0, 0.66, 0.1), 0.66, 0.06, "black", segments=26, bevel=0.01)
    m.cylinder("Body", (0, 0.7, 0.1), 0.2, 0.03, "red", segments=16, bevel=0)
    m.cylinder("Body", (0.55, 0.85, 0.65), 0.07, 0.4, "brass2", segments=10, bevel=0)
    m.cylinder("Body", (0.32, 1.0, 0.38), 0.05, 0.75, "brass2", segments=8, bevel=0, rotation=rot(y=45, x=90))
    m.cylinder("Body", (0.25, 1.35, -0.1), 0.12, 0.8, "brass2", segments=14, radius2=0.22, bevel=0,
               rotation=rot(x=-35, y=-10))
    m.cylinder("Body", (0.1, 1.85, -0.62), 0.22, 0.75, "brass2", segments=18, radius2=0.95, bevel=0.03,
               rotation=rot(x=-50, y=-10))
    m.torus("Body", (0.02, 2.13, -0.86), 0.93, 0.05, "gold", axis="y", segments=24, minor_segments=5,
            rotation=rot(x=-50, y=-10))
    m.cylinder("Body", (0.035, 2.1, -0.85), 0.88, 0.04, "darkgold", segments=22, bevel=0, rotation=rot(x=-50, y=-10))
    m.box("Body", (0.85, 0.35, 0.1), (0.1, 0.12, 0.12), "gold", bevel=0.02)
    m.box("Body", (0.98, 0.35, 0.1), (0.06, 0.06, 0.4), "gold", bevel=0.01)


# 8. Музыкальная шкатулка: сливовый ларец с золотом, открытая крышка с зеркалом, балерина.
def music_box(m):
    m.box("Body", (0, 0.38, 0), (1.8, 0.7, 1.2), "plum", bevel=B2)
    m.box("Body", (0, 0.05, 0), (1.9, 0.1, 1.3), "gold", bevel=0.03)
    m.box("Body", (0, 0.74, 0), (1.86, 0.06, 1.26), "gold", bevel=0.02)
    for x in (-0.86, 0.86):
        for z in (-0.56, 0.56):
            m.box("Body", (x, 0.4, z), (0.14, 0.72, 0.14), "gold", bevel=0.03)
    m.box("Body", (0, 1.28, 0.62), (1.8, 1.1, 0.1), "plum", bevel=0.05, rotation=rot(x=-12))
    m.box("Body", (0, 1.28, 0.55), (1.4, 0.8, 0.04), "glass", bevel=0.01, rotation=rot(x=-12))
    m.box("Body", (0, 0.76, 0), (1.5, 0.04, 0.9), "velvet", bevel=0)
    m.cylinder("Body", (0, 0.83, 0), 0.22, 0.08, "gold", segments=16, bevel=0.01)
    m.cylinder("Body", (0, 1.02, 0), 0.3, 0.06, "pink", segments=16, radius2=0.12, bevel=0)
    m.cylinder("Body", (0, 1.15, 0), 0.07, 0.3, "pink", segments=10, bevel=0)
    m.sphere("Body", (0, 1.38, 0), 0.1, "porcelain", segments=10, rings=6)
    m.box("Body", (0, 1.22, 0), (0.6, 0.04, 0.04), "porcelain", bevel=0.01, rotation=rot(z=20))
    m.cylinder("Body", (0.98, 0.4, 0), 0.05, 0.2, "gold", axis="x", segments=8, bevel=0)
    m.box("Body", (1.12, 0.4, 0), (0.06, 0.3, 0.12), "gold", bevel=0.02)


# 9. Ваза в ящике: деревянная обрешётка, солома, сине-белая ваза торчит сверху.
def crated_vase(m):
    for x in (-0.95, 0.95):
        for z in (-0.95, 0.95):
            m.box("Body", (x, 0.6, z), (0.2, 1.2, 0.2), "darkwood", bevel=0.03)
    for y in (0.15, 0.6, 1.05):
        for (cx, cz, sx, sz) in ((0, -0.97, 1.7, 0.1), (0, 0.97, 1.7, 0.1), (-0.97, 0, 0.1, 1.7), (0.97, 0, 0.1, 1.7)):
            m.box("Body", (cx, y, cz), (sx, 0.26, sz), "crate", bevel=0.03)
    m.box("Body", (0, 0.06, 0), (1.8, 0.12, 1.8), "crate", bevel=0.02)
    m.box("Body", (0, 1.08, 0), (1.76, 0.12, 1.76), "straw", bevel=0.03)
    for k in range(9):
        a = math.radians(k * 40)
        m.box("Body", (0.62 * math.cos(a), 1.2, 0.62 * math.sin(a)), (0.5, 0.05, 0.06), "straw", bevel=0.01,
              rotation=rot(y=k * 37, z=12 - k * 3))
    m.vase("Body", (0, 0.85, 0), 1.35, "white")
    m.torus("Body", (0, 1.58, 0), 0.43, 0.05, "folkblue", axis="y", segments=20, minor_segments=5)
    m.torus("Body", (0, 1.95, 0), 0.5, 0.05, "folkblue", axis="y", segments=20, minor_segments=5)
    for k in range(6):
        a = math.radians(k * 60 + 15)
        m.sphere("Body", (0.56 * math.cos(a), 1.78, 0.56 * math.sin(a)), 0.08, "folkblue", segments=8, rings=5)


# 10. Гипсовый бюст (классический, в тоге): плинт, скруглённый торс с драпировкой, лицо и шапка кудрей.
def plaster_bust(m):
    m.box("Body", (0, 0.2, 0), (1.2, 0.4, 1.0), "stone", bevel=B)
    m.box("Body", (0, 0.45, 0), (0.9, 0.1, 0.8), "marble", bevel=0.03)
    m.cylinder("Body", (0, 0.6, 0), 0.3, 0.2, "plaster", segments=16, radius2=0.2, bevel=0.02)
    m.hull("Body", [(sx * x, y, z) for sx in (-1, 1) for (x, y, z) in (
        (0.72, 1.2, 0.0), (0.66, 1.28, -0.2), (0.66, 1.28, 0.22), (0.5, 0.78, -0.24), (0.5, 0.78, 0.24),
        (0.22, 1.36, -0.32), (0.22, 1.36, 0.3), (0.12, 0.7, -0.3), (0.12, 0.7, 0.3))], "plaster", bevel=0.05)
    m.box("Body", (0.05, 1.08, -0.33), (0.95, 0.16, 0.08), "marble", bevel=0.04, rotation=rot(z=-28))
    m.box("Body", (-0.2, 0.92, -0.32), (0.5, 0.12, 0.07), "marble", bevel=0.03, rotation=rot(z=-28))
    m.cylinder("Body", (0, 1.5, -0.02), 0.2, 0.34, "plaster", segments=14, bevel=0.02)
    m.sphere("Body", (0, 1.98, -0.04), 0.42, "plaster", segments=18, rings=12, scale=(0.82, 1.08, 0.95))
    m.sphere("Body", (0, 2.08, 0.04), 0.44, "plaster", segments=18, rings=10, half=True, scale=(0.9, 0.9, 1.0))
    for k in range(11):
        a = math.radians(-100 + k * 20)
        m.sphere("Body", (0.36 * math.sin(a), 2.2 + 0.05 * (k % 2), -0.04 - 0.3 * math.cos(a)), 0.11, "plaster",
                 segments=10, rings=6)
    m.wedge("Body", (0, 1.96, -0.43), (0.12, 0.22, 0.14), "plaster", down="-z", bevel=0.02)
    m.box("Body", (0, 2.1, -0.38), (0.44, 0.05, 0.07), "plaster", bevel=0.02)
    for x in (-0.13, 0.13):
        m.sphere("Body", (x, 2.02, -0.37), 0.045, "stone", segments=8, rings=5, scale=(1.3, 0.8, 0.5))
        m.sphere("Body", (x * 2.9, 1.98, -0.02), 0.08, "plaster", segments=8, rings=5, scale=(0.5, 1, 0.8))
    m.box("Body", (0, 1.78, -0.39), (0.16, 0.035, 0.04), "stone", bevel=0.01)


# 11. Рыцарские доспехи на стойке: шлем с забралом и красным плюмажем, кираса, меч перед собой.
def knight_armor(m):
    m.box("Body", (0, 0.1, 0), (1.4, 0.2, 1.0), "darkwood", bevel=B)
    for x in (-0.24, 0.24):
        m.box("Body", (x, 0.3, -0.08), (0.28, 0.2, 0.46), "silver", bevel=0.06)
        m.cylinder("Body", (x, 0.82, 0), 0.15, 0.86, "silver", segments=12, bevel=0.03)
        m.sphere("Body", (x, 1.28, -0.04), 0.17, "silver", segments=12, rings=8)
    m.box("Body", (0, 1.42, 0), (0.78, 0.36, 0.5), "steel", bevel=0.08)
    m.box("Body", (0, 2.0, 0), (0.92, 0.9, 0.58), "silver", bevel=0.22)
    m.box("Body", (0, 2.05, -0.3), (0.08, 0.7, 0.06), "white", bevel=0.02)
    for x in (-0.6, 0.6):
        m.sphere("Body", (x, 2.38, 0), 0.3, "silver", segments=14, rings=8, half=True)
        m.cylinder("Body", (x * 1.08, 1.95, 0), 0.13, 0.7, "silver", segments=12, bevel=0.03)
        m.box("Body", (x * 1.05, 1.52, -0.12), (0.22, 0.22, 0.3), "steel", bevel=0.05)
    m.cylinder("Body", (0, 2.66, 0), 0.32, 0.5, "silver", segments=16, bevel=0.04)
    m.sphere("Body", (0, 2.9, 0), 0.32, "silver", segments=16, rings=10, half=True)
    m.box("Body", (0, 2.7, -0.31), (0.44, 0.06, 0.04), "black", bevel=0.01)
    for k in range(3):
        m.box("Body", (0, 2.52 - k * 0.05, -0.31), (0.04, 0.03, 0.03), "black", bevel=0)
    for k in range(4):
        m.box("Body", (0, 3.25 + k * 0.03, 0.1 + k * 0.15), (0.16, 0.2, 0.22), "red", bevel=0.05, rotation=rot(x=k * 12))
    m.box("Body", (0, 1.15, -0.55), (0.1, 1.6, 0.05), "steel", bevel=0.02)
    m.box("Body", (0, 1.98, -0.55), (0.5, 0.08, 0.1), "gold", bevel=0.02)
    m.cylinder("Body", (0, 2.18, -0.55), 0.05, 0.32, "darkwood", segments=8, bevel=0)
    m.sphere("Body", (0, 2.36, -0.55), 0.07, "gold", segments=8, rings=5)


# 12. Бронзовый конь на мраморном постаменте: идёт шагом, передняя нога поднята.
def bronze_horse(m):
    m.box("Body", (0, 0.25, 0), (1.1, 0.5, 2.5), "marble", bevel=B)
    m.box("Body", (0, 0.52, 0), (1.2, 0.06, 2.6), "darkstone", bevel=0.02)
    m.box("Body", (0, 0.04, 0), (1.2, 0.08, 2.6), "darkstone", bevel=0.02)
    m.sphere("Body", (0, 1.45, 0.05), 0.5, "bronze", segments=16, rings=10, scale=(0.75, 0.85, 1.9))
    legs = (((-0.18, -0.55), 0, 0), ((0.18, -0.6), -40, 0.12), ((-0.18, 0.6), 8, 0), ((0.18, 0.62), -6, 0))
    for (x, z), tilt, lift in legs:
        m.box("Body", (x, 0.93 + lift, z), (0.14, 0.8, 0.16), "bronze", bevel=0.04, rotation=rot(x=tilt))
        m.box("Body", (x, 0.6 + lift * 2.5, z - (0.12 if tilt < -20 else 0)), (0.16, 0.1, 0.18), "darkbronze", bevel=0.02)
    m.box("Body", (0, 1.95, -0.75), (0.34, 0.85, 0.42), "bronze", bevel=0.12, rotation=rot(x=-35))
    m.box("Body", (0, 2.3, -1.05), (0.3, 0.32, 0.6), "bronze", bevel=0.1, rotation=rot(x=15))
    for x in (-0.09, 0.09):
        m.box("Body", (x, 2.52, -0.88), (0.06, 0.18, 0.08), "bronze", bevel=0.02)
    for k in range(5):
        m.box("Body", (0, 2.32 - k * 0.15, -0.72 + k * 0.12), (0.08, 0.2, 0.16), "darkbronze", bevel=0.03)
    m.box("Body", (0, 1.35, 0.98), (0.12, 0.7, 0.14), "darkbronze", bevel=0.04, rotation=rot(x=25))


ITEMS = [
    ("FolkWhistle", folk_whistle), ("PaintedTray", painted_tray), ("NestingDoll", nesting_doll),
    ("RockingHorse", rocking_horse), ("PorcelainDog", porcelain_dog), ("MantelClock", mantel_clock),
    ("Gramophone", gramophone), ("MusicBox", music_box), ("CratedVase", crated_vase),
    ("PlasterBust", plaster_bust), ("KnightArmor", knight_armor), ("BronzeHorse", bronze_horse),
]
SPACING = 5.0

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
collection = bpy.data.collections.new("Pack2_art")
bpy.context.scene.collection.children.link(collection)

layout, objects, report = {}, [], []
for k, (item_id, build) in enumerate(ITEMS):
    m = Model("Art_" + item_id)
    build(m)
    offset = ((k % 6) * SPACING, 0, (k // 6) * SPACING)
    parts = m.build(collection, offset)
    tris = sum(p["triangles"] for p in parts.values())
    layout["Art_" + item_id] = {"parts": parts}
    objects += [o for o in collection.objects if o.name.startswith("Art_" + item_id + "_")]
    report.append(f"{item_id}: {tris} тр.")
    assert tris <= BUDGET, f"{item_id}: {tris} > {BUDGET} треугольников"

lego.export_fbx(os.path.join(REPO, "assets", "models", "Pack2_art.fbx"), objects)
lego.write_json(os.path.join(REPO, "assets", "models", "Pack2_art.layout.json"), layout)

# Превью: чистые цвета без пупырышков (на произведениях квадратная текстура не обязательна, D37).
for obj in objects:
    color = lego.role_color(obj.name.split("_", 2)[2])
    code = lego.PALETTE.get(color, "FF00FF")
    mat = bpy.data.materials.get("C_" + code) or bpy.data.materials.new("C_" + code)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*lego.hex_to_rgb(code), 1)
    bsdf.inputs["Roughness"].default_value = 0.4
    if color == "glass":
        bsdf.inputs["Alpha"].default_value = 0.55
    obj.data.materials.clear()
    obj.data.materials.append(mat)
ground = Model("Ground")
ground.box("Body", (12.5, -0.25, 2.5), (60, 0.5, 30), "grass", bevel=0)
ground.build(collection)
ground_obj = [o for o in collection.objects if o.name.startswith("Ground_")]
for obj in ground_obj:
    mat = bpy.data.materials.new("Ground")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*lego.hex_to_rgb("7FC75A"), 1)
    obj.data.materials.append(mat)
lego.setup_render(700)
for k, (item_id, _) in enumerate(ITEMS):
    ox, oz = (k % 6) * SPACING, (k // 6) * SPACING
    vis = [o for o in objects if o.name.startswith("Art_" + item_id + "_")] + ground_obj
    lego.render(os.path.join(PREVIEWS, item_id + ".png"), (ox - 3.2, 2.6, oz - 4.6), (ox, 1.15, oz), vis, lens=40)
scene = bpy.context.scene
scene.render.resolution_x, scene.render.resolution_y = 1800, 900
lego.render(os.path.join(PREVIEWS, "Pack2_sheet.png"), (12.5, 11, -19), (12.5, 1.1, 2.5), objects + ground_obj, lens=34)
print("PACK2_OK " + "; ".join(report))
