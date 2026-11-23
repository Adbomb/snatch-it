"""Общие вещи для этажей-мешей четвёртой партии (2026-11-22): пальма, факел, бочка, ящик, фонарь, растение.
Каждая функция строит тела в переданной детали (FS/IS — гладкая, вещи сами уходят в Props по габаритам) и
светящиеся части в детали Glass. Только геометрия и цвета; всё техническое — floorbase / floorkit.
Зависит от floorkit, floorbase (Blender: bpy, bmesh, mathutils).
"""

import math

import floorkit as K
from floorbase import beam, rng, taper, tube


def palm(p, base, lean, h, trunk="8A5A30", leaf="3FA64A", leaf2="2E8A3C", nut="6A4422"):
    """Пальма: изогнутый ствол, веер листьев-шипов, гроздь орехов."""
    bx, by, bz = base
    lx, lz = lean
    pts = [(bx + lx * (t ** 1.6), by + h * t, bz + lz * (t ** 1.6)) for t in (0.0, 0.33, 0.66, 1.0)]
    tube(p, pts, [0.9, 0.78, 0.68, 0.6], 0.75, (1, 0, 0) if abs(lz) > abs(lx) else (0, 0, 1), trunk)
    top = pts[-1]
    for k in range(6):
        t = 2 * math.pi * (k + rng(k, h) * 0.3) / 6
        L = 3.2 + rng(k, 7) * 0.8
        mid = (top[0] + math.cos(t) * L * 0.55, top[1] + 0.7, top[2] + math.sin(t) * L * 0.55)
        tip = (top[0] + math.cos(t) * L, top[1] - 1.1, top[2] + math.sin(t) * L)
        taper(p, top, mid, 0.9, 0.7, leaf if k % 2 else leaf2)
        taper(p, mid, tip, 0.7, 0.08, leaf if k % 2 else leaf2)
    for k in range(3):
        t = 2 * math.pi * k / 3 + 0.4
        p.prism_xz(K.octa(top[0] + 0.45 * math.cos(t), top[2] + 0.45 * math.sin(t), 0.3, 0.3, 0.12), top[1] - 0.7,
                   top[1] - 0.15, nut)


def torch(p, g, x, y, z, h=3.0, pole="6A4A2A", bowl="3A2E24", flame="FFB030", flame2="FFE070"):
    """Факел на шесте: шест, чаша, двухъярусное пламя (светится)."""
    p.prism_xz(K.octa(x, z, 0.16, 0.16, 0.06), y, y + h, pole)
    p.prism_xz(K.octa(x, z, 0.45, 0.45, 0.18), y + h, y + h + 0.4, bowl)
    g.prism_xz(K.octa(x, z, 0.34, 0.34, 0.14), y + h + 0.4, y + h + 1.0, flame)
    g.prism_xz(K.octa(x, z, 0.16, 0.16, 0.07), y + h + 1.0, y + h + 1.5, flame2)


def barrel(p, x, z, y=0.0, r=0.8, h=1.7, wood="8A5A30", hoop="3A3A40"):
    """Бочка: брюшко из трёх ярусов, два обруча."""
    p.prism_xz(K.ngon(x, z, r * 0.86, 10), y, y + h * 0.25, wood)
    p.prism_xz(K.ngon(x, z, r, 10), y + h * 0.25, y + h * 0.75, wood)
    p.prism_xz(K.ngon(x, z, r * 0.86, 10), y + h * 0.75, y + h, wood)
    for yy in (y + h * 0.22, y + h * 0.78):
        p.prism_xz(K.ngon(x, z, r * 0.93 + 0.04, 10), yy - 0.06, yy + 0.06, hoop)


def crate(p, x, z, y=0.0, s=1.2, wood="B08048", board="8A6234"):
    """Ящик с рейками по рёбрам."""
    h = s / 2
    p.box(x - h, x + h, y, y + s, z - h, z + h, wood)
    for e in (-1, 1):
        p.box(x - h - 0.04, x + h + 0.04, y + s * 0.5 + e * s * 0.38 - 0.08, y + s * 0.5 + e * s * 0.38 + 0.08,
              z - h - 0.04, z + h + 0.04, board)


def lantern(p, g, x, y, z, s=1.0, cap="3A2E24", light="FFD070"):
    """Подвесной фонарь: крышка, светящийся корпус, донце."""
    p.prism_xz(K.octa(x, z, 0.5 * s, 0.5 * s, 0.2 * s), y + 0.7 * s, y + 0.9 * s, cap)
    g.prism_xz(K.octa(x, z, 0.38 * s, 0.38 * s, 0.15 * s), y, y + 0.7 * s, light)
    p.prism_xz(K.octa(x, z, 0.44 * s, 0.44 * s, 0.17 * s), y - 0.15 * s, y, cap)


def bush(p, x, z, y=0.0, r=1.0, c1="3FA64A", c2="2E8A3C"):
    """Куст: три гранёных кома."""
    for k in range(3):
        t = 2 * math.pi * k / 3 + rng(x, z) * 2
        cx, cz = x + 0.45 * r * math.cos(t), z + 0.45 * r * math.sin(t)
        rr = r * (0.7 + 0.25 * rng(k, x))
        p.prism_xz(K.octa(cx, cz, rr, rr, rr * 0.4), y, y + rr * 1.3, c1 if k % 2 else c2)


def flower(p, x, z, y=0.0, h=0.9, stem="3FA64A", petal="FF6A9A"):
    """Цветок: стебель и венчик."""
    p.box(x - 0.06, x + 0.06, y, y + h, z - 0.06, z + 0.06, stem)
    p.prism_xz(K.octa(x, z, 0.28, 0.28, 0.11), y + h, y + h + 0.16, petal)


def chain(p, a, b, n, w, color, sag=0.6):
    """Провисающая гирлянда/цепь/канат из n отрезков между точками a и b."""
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t - sag * 4 * t * (1 - t), a[2] + (b[2] - a[2]) * t))
    for q0, q1 in zip(pts, pts[1:]):
        beam(p, q0, q1, w, w, color)
    return pts
