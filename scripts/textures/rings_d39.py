"""Плитка контурных квадратов D39 для крупной архитектуры (этажи музея-небоскрёба): тот же рисунок, что запекает
scripts/blender/art_style.py (_ring_material) на вазе v13, предметах и боссах, — отдельные скруглённые квадраты-контуры:
шаг 0.6 стада, квадрат 0.42, скругление 0.1, контур 0.03, затемнение 22 %, глубина рельефа 0.012. Цвет плитки белый
(цвет даёт деталь), контур — тонкое вдавленное кольцо. Плитка 4 × 4 квадрата = 2.4 стада (StudsPerTile = 2.4), 512 px
(213 px на стад). Предмет запекает рисунок в свою карту; этажу такой карты не хватит по размеру, поэтому тот же
рисунок идёт плиткой (MaterialVariant LegoRingsD39, Config/Textures.RingsD39).
Пишет assets/textures/rings_d39_color.png и rings_d39_normal.png. Запуск: python scripts/textures/rings_d39.py
"""

import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STEP, SIZE, RAD, WIDTH, DARK, DEPTH, STRENGTH = 0.6, 0.42, 0.1, 0.03, 0.22, 0.012, 0.8  # art_style.RING и Bump
CELLS, PX, SS = 4, 512, 4  # сглаживание: считаем в SS раз крупнее и усредняем


def main():
    n = PX * SS
    tile = STEP * CELLS
    c = (np.arange(n) + 0.5) / n * tile
    x, y = np.meshgrid(c, c)
    inner = SIZE / 2 - RAD
    d2 = 0
    for coord in (x, y):
        q = np.abs(((coord + STEP / 2) / STEP) % 1.0 - 0.5) * STEP
        a = np.maximum(q - inner, 0.0)
        d2 = d2 + a * a
    dist = np.abs(np.sqrt(d2) - RAD)
    t = np.clip(1.0 - dist / (WIDTH / 2), 0, 1)
    g = t * t * (3 - 2 * t)  # плавный профиль контура (SMOOTHSTEP)
    color = 1.0 - g * DARK
    height = (1.0 - g) * DEPTH * STRENGTH
    px = n / tile
    gx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5 * px
    gy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5 * px
    nx, ny, nz = -gx, gy, np.ones_like(height)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    normal = np.stack([nx / ln, ny / ln, nz / ln], -1) * 0.5 + 0.5

    def down(a):
        return a.reshape(PX, SS, PX, SS, -1).mean(axis=(1, 3))

    col = np.repeat(down(color[..., None]), 3, axis=-1)
    Image.fromarray((col * 255 + 0.5).astype(np.uint8), "RGB").save(os.path.join(ROOT, "assets", "textures", "rings_d39_color.png"))
    Image.fromarray((down(normal) * 255 + 0.5).astype(np.uint8), "RGB").save(
        os.path.join(ROOT, "assets", "textures", "rings_d39_normal.png"))
    print("OK")


if __name__ == "__main__":
    main()
