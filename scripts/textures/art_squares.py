"""Текстура предметов искусства (референсы владельца 2026-10-31 — блочные Roblox-персонажи): на ровной грани —
крупные слегка выпуклые квадраты со скруглёнными углами и тонкие мягкие швы между ними, один цвет, без шахматки.
Цвет детали красит текстуру. Плитка — ART_SQUARES × ART_SQUARES квадратов; размер квадрата в игре задаёт
StudsPerTile варианта LegoSquaresArt (Config/Textures).

Пишет assets/textures/lego_art_color.png, lego_art_normal.png (OpenGL: Y вверх), lego_art_roughness.png.
Запуск: blender --background --factory-startup --python scripts/textures/art_squares.py -- <репо>
"""

import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1 :]
OUT = os.path.join(os.path.abspath(argv[0]), "assets", "textures")

SIZE = 1024  # пикселей на плитку
ART_SQUARES = 4  # квадратов на плитку по стороне
HALF = 0.455  # полуширина квадрата (доля клетки): швы тонкие
RADIUS = 0.16  # скругление углов
SLOPE = 0.06  # ширина мягкого скоса края
DEPTH = 10.0  # высота для карты нормалей (пикселей)
SEAM_SHADE = 0.16  # затемнение шва в цвете
ROUGHNESS = 0.5


def save(name, rgb):
    """rgb — массив (h, w, 3) в 0..1, строки сверху вниз; PNG без цветовых преобразований (как square_studs.py)."""
    h, w, _ = rgb.shape
    image = bpy.data.images.new(name, w, h, alpha=False)
    image.colorspace_settings.name = "Non-Color"
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[..., :3] = rgb
    image.pixels.foreach_set(rgba[::-1].ravel())  # Blender хранит строки снизу вверх
    image.filepath_raw = os.path.join(OUT, name)
    image.file_format = "PNG"
    image.save()


px = SIZE // ART_SQUARES
y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32) + 0.5
u = (x % px) / px - 0.5
v = (y % px) / px - 0.5
qx = np.abs(u) - (HALF - RADIUS)
qy = np.abs(v) - (HALF - RADIUS)
sd = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - RADIUS
t = np.clip(-sd / SLOPE, 0, 1)
t = t * t * (3 - 2 * t)  # 0 в шве → 1 на квадрате
shade = 1 - SEAM_SHADE * (1 - t)
save("lego_art_color.png", np.repeat(shade[..., None], 3, axis=2).astype(np.float32))
height = t * DEPTH  # квадраты чуть выпуклые
dh_row, dh_col = np.gradient(height)
normal = np.stack([-dh_col, dh_row, np.ones_like(height)], axis=-1)
normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
save("lego_art_normal.png", (normal * 0.5 + 0.5).astype(np.float32))
save("lego_art_roughness.png", np.full((64, 64, 3), ROUGHNESS, dtype=np.float32))
print("ART_SQUARES_OK")
