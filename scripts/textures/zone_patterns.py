"""Узоры пола зон коридора (D41): белые фигуры на прозрачном фоне, PNG 256 × 256 (одна плитка). В игре — Texture на
верхней грани пола зоны: цвет и прозрачность задаёт зона (GameConfig.Zones.pattern), рельеф пупырышков (LegoSquares)
под узором остаётся виден. Четыре узора:
- tiles — шахматка крупных плит (2 × 2 клетки на плитку);
- grid — тонкая сетка швов (плиточный пол);
- waves — волнистые полосы (песок, лава);
- diamonds — ромбы (ковёр, лёд).
Пишет assets/textures/zone_<узор>.png. Только стандартная библиотека Python (zlib, struct).
Запуск из корня репозитория: python scripts/textures/zone_patterns.py
"""

import math
import os
import struct
import zlib

SIZE = 256
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "textures")


def save(name, alpha):
    """alpha(x, y) → 0…1 (доля непрозрачности белого) → RGBA PNG."""
    rows = []
    for y in range(SIZE):
        row = bytearray([0])
        for x in range(SIZE):
            a = max(0.0, min(1.0, alpha(x, y)))
            row += bytes((255, 255, 255, round(a * 255)))
        rows.append(bytes(row))
    raw = zlib.compress(b"".join(rows), 9)

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", raw) + chunk(b"IEND", b"")
    path = os.path.join(OUT, f"zone_{name}.png")
    with open(path, "wb") as f:
        f.write(png)
    print(path)


def smooth_edge(d, width=1.5):
    """Мягкий край: d — расстояние до границы фигуры в пикселях (внутри > 0)."""
    return max(0.0, min(1.0, 0.5 + d / width))


def tiles(x, y):
    half = SIZE / 2
    inside = (x < half) == (y < half)
    # фаска по краю плиты: светлее к середине
    dx = min(x % half, half - 1 - x % half)
    dy = min(y % half, half - 1 - y % half)
    edge = min(dx, dy)
    return (1.0 if inside else 0.0) * (0.75 + 0.25 * min(1.0, edge / 10))


def grid(x, y):
    line = 9.0  # толще: тонкие швы пропадают на расстоянии (mip-карты)
    d = min(x % SIZE, SIZE - x % SIZE, y % SIZE, SIZE - y % SIZE)
    return smooth_edge(line - d)


def waves(x, y):
    period = SIZE / 2
    phase = y + 18 * math.sin(2 * math.pi * x / SIZE)
    d = abs((phase % period) - period / 2) - period / 4
    return smooth_edge(-d, 2.5)


def diamonds(x, y):
    u, v = (x + 0.5) / SIZE, (y + 0.5) / SIZE
    d = abs(u - 0.5) + abs(v - 0.5)  # ромб в центре плитки
    return smooth_edge((0.36 - d) * SIZE, 2.0)


if __name__ == "__main__":
    for name, fn in (("tiles", tiles), ("grid", grid), ("waves", waves), ("diamonds", diamonds)):
        save(name, fn)
