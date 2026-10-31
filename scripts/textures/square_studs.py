"""Текстура «квадратные пупырышки» для MaterialVariant (референс заказчика 2026-10-31): плотная сетка мелких
вдавленных квадратиков со скруглёнными углами — один на стад, без линий между ними; клетки 4 × 4 стада
шахматкой светлее и темнее (цвет детали красит текстуру, получаются два оттенка одного цвета).

Плитка — 8 × 8 стадов (2 × 2 клетки), поэтому в MaterialVariant StudsPerTile = 8.
Пишет в assets/textures: lego_squares_color.png (светлая основа, шахматка, затемнение стенок),
lego_squares_normal.png (рельеф, OpenGL: Y вверх) и lego_squares_roughness.png (ровная шероховатость пластика).

Запуск из корня репозитория (нужен numpy — он есть в Blender):
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup \\
    --python scripts/textures/square_studs.py -- .
"""

import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1 :]
OUT = os.path.join(os.path.abspath(argv[0]), "assets", "textures")

SIZE = 1024  # пикселей на плитку
STUDS = 8  # стадов на плитку
CELL = 4  # стадов в клетке шахматки
HALF = 0.30  # полуширина квадратика, доля стада (квадратик 0.6 стада)
RADIUS = 0.10  # скругление углов, доля стада
SLOPE = 0.065  # ширина скоса стенки, доля стада
DEPTH = 9.0  # глубина вдавливания для карты нормалей, пикселей
DARK_CELL = 0.80  # тёмная клетка шахматки
WALL_SHADE = 0.42  # затемнение стенок квадратика: контур тёмный и чёткий, как на референсе
FLOOR_SHADE = 0.05  # дно чуть темнее
ROUGHNESS = 0.55


def save(name, rgb):
    """rgb — массив (SIZE, SIZE, 3) в 0..1, строки сверху вниз; пишет PNG без цветовых преобразований."""
    h, w, _ = rgb.shape
    image = bpy.data.images.new(name, w, h, alpha=False)
    image.colorspace_settings.name = "Non-Color"
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[..., :3] = rgb
    image.pixels.foreach_set(rgba[::-1].ravel())  # Blender хранит строки снизу вверх
    image.filepath_raw = os.path.join(OUT, name)
    image.file_format = "PNG"
    image.save()
    print("TEXTURE", name, w, h)


px = SIZE // STUDS
y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32) + 0.5
u = (x % px) / px - 0.5
v = (y % px) / px - 0.5

# Скруглённый квадрат: знаковое расстояние (доли стада), меньше нуля — внутри.
qx = np.abs(u) - (HALF - RADIUS)
qy = np.abs(v) - (HALF - RADIUS)
outside = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0))
sd = outside + np.minimum(np.maximum(qx, qy), 0) - RADIUS

t = np.clip(-sd / SLOPE, 0, 1)
t = t * t * (3 - 2 * t)  # 0 снаружи → 1 на дне, плавный скос
wall = 4 * t * (1 - t)  # 1 посередине стенки

cells = (x // (px * CELL)).astype(int) + (y // (px * CELL)).astype(int)
checker = np.where(cells % 2 == 0, 1.0, DARK_CELL)
shade = checker * (1 - WALL_SHADE * wall) * (1 - FLOOR_SHADE * t)
save("lego_squares_color.png", np.repeat(shade[..., None], 3, axis=2))

height = -t * DEPTH
dh_row, dh_col = np.gradient(height)
normal = np.stack([-dh_col, dh_row, np.ones_like(height)], axis=-1)  # строки картинки идут вниз, Y — вверх
normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
save("lego_squares_normal.png", normal * 0.5 + 0.5)

save("lego_squares_roughness.png", np.full((64, 64, 3), ROUGHNESS, dtype=np.float32))
print("SQUARES_OK")
