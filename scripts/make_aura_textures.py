"""Король-дракон №10, этап C.1: свои текстуры частиц фиолетовой ауры (рисуются кодом, без сторонних ресурсов).

Все текстуры — белые с альфой (цвет задаёт ParticleEmitter.Color), фон прозрачный:
- aura_wisp.png — 4×4 кадра (FlipbookLayout Grid4x4) магических языков: узкие изогнутые ленты с рваными краями и
  светлой серединой, тянутся вверх, рвутся на клочья и сворачиваются (не обычный огонь: нет округлого «пламени свечи»
  и раскалённого низа);
- aura_streak.png — вертикальный энергетический штрих: яркая нить, мягкое свечение, концы гаснут;
- aura_spark.png — искра: яркая точка с четырьмя короткими лучами;
- aura_smoke.png — 2×2 кадра мягких рваных клубов дыма (полупрозрачные);
- aura_glow.png — мягкое круглое свечение (внутренняя оболочка).
Пишет assets/textures/vfx/boss10_aura/ и лист-превью <папка>/aura_textures_preview.png (на тёмном и светлом фоне).

  python scripts/make_aura_textures.py <папка превью>
"""

import math
import os
import sys

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(REPO, "assets", "textures", "vfx", "boss10_aura")
RNG = np.random.default_rng(1010)


def value_noise(h, w, cells, rng, octaves=4):
    """Плавный шум 0…1 (сумма октав билинейной сетки)."""
    out = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        c = cells * 2**o
        grid = rng.random((c + 1, c + 1)).astype(np.float32)
        y = np.linspace(0, c, h, endpoint=False)
        x = np.linspace(0, c, w, endpoint=False)
        yi, xi = np.floor(y).astype(int), np.floor(x).astype(int)
        fy, fx = (y - yi)[:, None], (x - xi)[None, :]
        fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
        a = grid[yi][:, xi]
        b = grid[yi][:, xi + 1]
        cc = grid[yi + 1][:, xi]
        d = grid[yi + 1][:, xi + 1]
        out += amp * ((a * (1 - fx) + b * fx) * (1 - fy) + (cc * (1 - fx) + d * fx) * fy)
        total += amp
        amp *= 0.5
    return out / total


def rgba(alpha):
    a = np.clip(alpha, 0, 1)
    img = np.zeros(a.shape + (4,), np.uint8)
    img[..., :3] = 255
    img[..., 3] = (a * 255 + 0.5).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


def wisp_frame(size, phase, seed):
    """Один кадр языка: лента вдоль изогнутой оси снизу вверх, ширина сужается, края рваные, середина ярче."""
    rng = np.random.default_rng(seed)
    h = w = size
    y = np.linspace(1, 0, h)[:, None]  # 0 — низ, 1 — верх кадра
    x = np.linspace(-1, 1, w)[None, :]
    # ось языка: волна, которая поднимается со временем (phase 0…1)
    k1, k2 = rng.uniform(1.5, 2.5), rng.uniform(3.0, 5.0)
    axis = 0.22 * np.sin(2 * math.pi * (k1 * y - phase) + rng.uniform(0, 6)) * y + 0.08 * np.sin(
        2 * math.pi * (k2 * y - 1.7 * phase)) * y
    # ширина: узкая у основания, расширение в нижней трети, к верху сходит на нет; к концу кадра язык «рвётся»
    top = 0.95 - 0.35 * phase
    width = 0.26 * np.sin(np.clip(y / top, 0, 1) * math.pi) ** 0.8 * (1 - 0.3 * phase) + 0.015
    d = np.abs(x - axis) / width
    n = value_noise(h, w, 4, rng, 4)
    n2 = value_noise(h, w, 9, rng, 3)
    # рваные края: порог по шуму, растёт к верху и к концу жизни
    erode = 0.35 + 0.45 * y + 0.35 * phase
    body = np.clip(1.25 - d, 0, 1) * np.clip((n * 0.7 + n2 * 0.5) - erode * 0.55 + 0.45, 0, 1) * 1.6
    core = np.exp(-(d / 0.35) ** 2) * (1 - y * 0.5) * 0.9
    alpha = np.clip(body * 0.8 + core * body, 0, 1)
    # оторванные клочья над языком
    above = (y > top) & (y < top + 0.25)
    blob = np.clip(1.0 - np.abs(x - axis) / 0.12, 0, 1) * np.clip(n2 * 2.2 - 1.3, 0, 1) * above
    alpha = np.maximum(alpha, blob * 0.8)
    alpha *= np.clip(y * 6, 0, 1)  # основание мягкое
    fade = 1 - max(0.0, phase - 0.7) / 0.3 * 0.6
    return alpha * fade


def flipbook(frames, grid):
    s = frames[0].shape[0]
    sheet = np.zeros((s * grid, s * grid), np.float32)
    for i, f in enumerate(frames):
        r, c = divmod(i, grid)
        sheet[r * s:(r + 1) * s, c * s:(c + 1) * s] = f
    return sheet


def wisp():
    frames = [wisp_frame(128, i / 15, 500 + i // 4) for i in range(16)]
    return rgba(flipbook(frames, 4))


def streak():
    h, w = 256, 64
    y = np.linspace(-1, 1, h)[:, None]
    x = np.linspace(-1, 1, w)[None, :]
    along = np.clip(1 - np.abs(y) ** 2.2, 0, 1)
    line = np.exp(-(x / 0.08) ** 2)
    glow = np.exp(-(x / 0.35) ** 2) * 0.35
    return rgba((line + glow) * along)


def spark():
    s = 64
    y, x = np.mgrid[-1:1:s * 1j, -1:1:s * 1j]
    r = np.sqrt(x * x + y * y)
    dot = np.exp(-(r / 0.16) ** 2)
    rays = (np.exp(-(np.abs(x) / 0.05) ** 2) * np.exp(-(np.abs(y) / 0.7) ** 2)
            + np.exp(-(np.abs(y) / 0.05) ** 2) * np.exp(-(np.abs(x) / 0.7) ** 2)) * 0.7
    halo = np.exp(-(r / 0.5) ** 2) * 0.25
    return rgba(dot + rays + halo)


def smoke():
    s = 128
    frames = []
    for i in range(4):
        rng = np.random.default_rng(900 + i)
        y, x = np.mgrid[-1:1:s * 1j, -1:1:s * 1j]
        r = np.sqrt(x * x + y * y)
        n = value_noise(s, s, 3, rng, 4)
        a = np.clip(1 - r / (0.65 + 0.35 * n), 0, 1) ** 1.6 * (0.35 + 0.65 * n)
        frames.append(a * 0.85)
    return rgba(flipbook(frames, 2))


def glow():
    s = 128
    y, x = np.mgrid[-1:1:s * 1j, -1:1:s * 1j]
    r = np.sqrt(x * x + y * y)
    return rgba(np.clip(1 - r, 0, 1) ** 2.2)


def preview(images, path):
    tiles = []
    for bg in ((14, 10, 24), (200, 205, 215)):
        row = Image.new("RGB", (sum(256 for _ in images), 256), bg)
        for i, im in enumerate(images):
            t = im.copy()
            t.thumbnail((256, 256))
            tint = Image.new("RGBA", t.size, (190, 90, 255, 255))
            tint.putalpha(t.getchannel("A"))
            row.paste(tint, (i * 256, (256 - t.size[1]) // 2), tint)
        tiles.append(row)
    sheet = Image.new("RGB", (tiles[0].width, 512))
    sheet.paste(tiles[0], (0, 0))
    sheet.paste(tiles[1], (0, 256))
    sheet.save(path)


def main():
    os.makedirs(DST, exist_ok=True)
    out = {"aura_wisp": wisp(), "aura_streak": streak(), "aura_spark": spark(), "aura_smoke": smoke(),
           "aura_glow": glow()}
    for name, im in out.items():
        im.save(os.path.join(DST, name + ".png"))
        print("AURA_TEX", name, im.size, flush=True)
    if len(sys.argv) > 1:
        os.makedirs(sys.argv[1], exist_ok=True)
        preview(list(out.values()), os.path.join(sys.argv[1], "aura_textures_preview.png"))


if __name__ == "__main__":
    main()
