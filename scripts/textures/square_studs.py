"""Текстуры «квадратные пупырышки» для MaterialVariant (референс заказчика 2026-10-31): плотная сетка мелких
вдавленных квадратиков со скруглёнными углами — один на стад, без линий между ними; клетки 4 × 4 стада
шахматкой светлее и темнее (цвет детали красит текстуру, получаются два оттенка одного цвета).

Два рельефа (настройки — VARIANTS):
- squares — трава, дорожки, постройки: мелкий рельеф, тёмный только контур квадратика;
- squares_deep — земляные обрывы: квадратики глубже, дно темнее (как ямки на стене референса), без резкого контраста;
- squares_soft — музеи (фасады и интерьер): тот же рельеф, шахматка едва заметна — чистые спокойные стены.

Плитка — 8 × 8 стадов (2 × 2 клетки), поэтому в MaterialVariant StudsPerTile = 8.
Пишет в assets/textures: lego_<вариант>_color.png (светлая основа, шахматка, тени), lego_<вариант>_normal.png
(рельеф, OpenGL: Y вверх) и lego_<вариант>_roughness.png (ровная шероховатость пластика).

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
RADIUS = 0.10  # скругление углов, доля стада
SLOPE = 0.065  # ширина скоса стенки, доля стада
ROUGHNESS = 0.55

# half — полуширина квадратика (доля стада), depth — глубина для карты нормалей (пикселей),
# dark_cell — тёмная клетка шахматки, wall_shade — затемнение стенок, floor_shade — затемнение дна.
VARIANTS = {
    "squares": {"half": 0.30, "depth": 9.0, "dark_cell": 0.80, "wall_shade": 0.42, "floor_shade": 0.05},
    "squares_deep": {"half": 0.29, "depth": 12.0, "dark_cell": 0.90, "wall_shade": 0.24, "floor_shade": 0.30},
    "squares_soft": {"half": 0.30, "depth": 7.0, "dark_cell": 0.95, "wall_shade": 0.26, "floor_shade": 0.03},
    # Предметы (референсы владельца 2026-10-31): редкие вдавленные квадраты с заметной фаской, без шахматки.
    "squares_item": {"half": 0.27, "depth": 12.0, "dark_cell": 1.0, "wall_shade": 0.42, "floor_shade": 0.02},
}


def save(name, rgb):
    """rgb — массив (h, w, 3) в 0..1, строки сверху вниз; пишет PNG без цветовых преобразований."""
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
cells = (x // (px * CELL)).astype(int) + (y // (px * CELL)).astype(int)

for variant, cfg in VARIANTS.items():
    # Скруглённый квадрат: знаковое расстояние (доли стада), меньше нуля — внутри.
    qx = np.abs(u) - (cfg["half"] - RADIUS)
    qy = np.abs(v) - (cfg["half"] - RADIUS)
    outside = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0))
    sd = outside + np.minimum(np.maximum(qx, qy), 0) - RADIUS

    t = np.clip(-sd / SLOPE, 0, 1)
    t = t * t * (3 - 2 * t)  # 0 снаружи → 1 на дне, плавный скос
    wall = 4 * t * (1 - t)  # 1 посередине стенки

    checker = np.where(cells % 2 == 0, 1.0, cfg["dark_cell"])
    shade = checker * (1 - cfg["wall_shade"] * wall) * (1 - cfg["floor_shade"] * t)
    save(f"lego_{variant}_color.png", np.repeat(shade[..., None], 3, axis=2))

    height = -t * cfg["depth"]
    dh_row, dh_col = np.gradient(height)
    normal = np.stack([-dh_col, dh_row, np.ones_like(height)], axis=-1)  # строки картинки идут вниз, Y — вверх
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    save(f"lego_{variant}_normal.png", normal * 0.5 + 0.5)

    save(f"lego_{variant}_roughness.png", np.full((64, 64, 3), ROUGHNESS, dtype=np.float32))
print("SQUARES_OK")
