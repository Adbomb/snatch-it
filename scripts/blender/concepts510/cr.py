"""Детали для черновых концептов существ боссов 5–10 (листы по 10 примеров, не финальные модели).

Зависит от ck (примитивы D39). Существо стоит в начале координат на z = 0, смотрит в −y; размер 2–4 (стада в игре).
"""

import math

import ck as C
from mathutils import Matrix, Vector

BASE = {"white": "FFFFFF", "dark": "161824", "glint": "FFFFFF", "blush": "FF8FA8", "tongue": "F2607A"}


def new(name, colors, rings=()):
    """Новое существо: colors — {ключ: hex}; ключи из rings получают кольца D39."""
    a = C.new_art(name, ring_z0=1.0)
    for k, code in colors.items():
        a.paint(k, code, rings=k in rings)
    for k, code in BASE.items():
        if k not in colors:
            a.paint(k, code)
    return a


def done(a, col, glow=2.5):
    return [C.finish(a, col, glow=glow)]


def face(a, c, sep, size, kind="round", iris=None, mouth="smile", blush=True, lid_key=None, look=(0.0, -0.1)):
    """Лицо на плоскости y = c.y (смотрит в −y): пара глаз через sep, размер size.
    kind: round — круглые, big — крупные с радужкой, happy — дуги, sleepy — с веком, angry — с бровями,
    cool — тёмные очки. mouth: smile, open, grin, flat, None."""
    x, y, z = c
    for s in (1, -1):
        ex = x + s * sep / 2
        if kind == "happy":
            C.closed_eye(a, (ex, y, z), size)
        elif kind == "round":
            C.round_eye(a, (ex, y, z), size / 2, look=look, iris=iris)
        elif kind in ("big", "sleepy", "angry"):
            C.eye(a, (ex, y, z), size, size * 1.1, look=look, lid=0.45 if kind == "sleepy" else 0.0,
                  lid_key=lid_key, iris=iris)
            if kind == "angry":
                C.bar(a, "dark", (ex - s * size * 0.55, y - 0.06, z + size * 0.75),
                      (ex + s * size * 0.55, y - 0.06, z + size * 0.55), size * 0.18, size * 0.14, bevel=0)
    if kind == "cool":
        a.box("dark", x - sep / 2 - size * 0.6, x + sep / 2 + size * 0.6, y - 0.08, y + 0.02, z - size * 0.35,
              z + size * 0.35, bevel=0.01)
        a.box("glint", x - sep / 2 - size * 0.4, x - sep / 2 - size * 0.15, y - 0.1, y - 0.07, z + size * 0.05,
              z + size * 0.22, bevel=0)
    mz = z - size * 0.95
    w = sep * 0.32
    if mouth == "smile":
        C.bar(a, "dark", (x - w, y - 0.02, mz + w * 0.35), (x, y - 0.02, mz), size * 0.14, size * 0.1, bevel=0)
        C.bar(a, "dark", (x, y - 0.02, mz), (x + w, y - 0.02, mz + w * 0.35), size * 0.14, size * 0.1, bevel=0)
    elif mouth == "open":
        a.box("dark", x - w * 0.8, x + w * 0.8, y - 0.04, y + 0.02, mz - w * 0.55, mz + w * 0.2, bevel=0.01)
        a.box("tongue", x - w * 0.5, x + w * 0.5, y - 0.05, y - 0.02, mz - w * 0.5, mz - w * 0.2, bevel=0)
    elif mouth == "grin":
        a.box("dark", x - w * 1.1, x + w * 1.1, y - 0.04, y + 0.02, mz - w * 0.3, mz + w * 0.15, bevel=0.01)
        a.box("white", x - w * 0.9, x + w * 0.9, y - 0.05, y - 0.03, mz - w * 0.05, mz + w * 0.12, bevel=0)
    elif mouth == "flat":
        a.box("dark", x - w * 0.6, x + w * 0.6, y - 0.03, y + 0.01, mz - 0.03, mz + 0.03, bevel=0)
    if blush:
        for s in (1, -1):
            a.box("blush", x + s * (sep / 2 + size * 0.25) - size * 0.22, x + s * (sep / 2 + size * 0.25) + size * 0.22,
                  y - 0.02, y + 0.02, mz + size * 0.1, mz + size * 0.3, bevel=0)


def legs(a, key, pts, r, h, z0=0.0, n=8):
    """Ножки-столбики от z0 вверх на h в точках pts (x, y)."""
    for x, y in pts:
        a.prism(key, C.ngon(x, y, r, n), z0, z0 + h)


def spike(a, key, base, w, h, tilt_x=0.0, tilt_y=0.0, bevel=0.004):
    """Конус-шип (уши, рога, рожки), наклон вокруг основания: tilt_x — вперёд (+) / назад, tilt_y — вбок."""
    bx, by, bz = base
    m = C.tilt(base, "Y", tilt_y) @ C.tilt(base, "X", tilt_x)
    a.frustum(key, (bx - w / 2, bx + w / 2, by - w / 2, by + w / 2), (bx, bx, by, by), bz, bz + h, bevel=bevel, matrix=m)


def plate(a, key, pts, y0, y1, matrix=None):
    """Плоская деталь по контуру pts (x, z) толщиной y0…y1: крылья, плавники, гребни."""
    a.extrude(key, pts, y0, y1, axis="y", matrix=matrix)


def wings(a, key, c, span, h, spread=20.0, thick=0.08):
    """Пара плоских крыльев от точки c: span — длина, h — высота, spread — отвод назад (градусы)."""
    for s in (1, -1):
        pts = [(0, 0), (s * span, h * 0.55), (s * span * 0.8, -h * 0.1), (s * span * 0.45, -h * 0.45)]
        m = Matrix.Translation(c) @ Matrix.Rotation(math.radians(s * spread), 4, "Z")
        plate(a, key, pts, -thick / 2, thick / 2, matrix=m)


def turn(a, c, deg, axis="Z"):
    """Повернуть следующие детали вокруг c (сбросить — a.transform = None)."""
    a.transform = C.tilt(c, axis, deg)


def coin(a, key, c, r=0.35, t=0.08, tilt=0.0):
    C.disc(a, key, c[0], c[1], r, c[2], c[2] + t, n=8, bevel=0.01, matrix=C.tilt(c, "X", tilt) if tilt else None)
