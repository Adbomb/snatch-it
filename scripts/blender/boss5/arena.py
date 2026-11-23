"""Арена 5 «Ледник» (концепт D64): замёрзшая галерея Йети-коллекционера в рамке зоны 184 × 95 стадов.

Задумка: коллекционер устроил музей прямо во льду. Задник — ледниковая стена-хранилище: ступенчатый лёд с кристаллами,
арка-вход в золотой раме, ниши с вмороженными экспонатами, золотая снежинка-герб. Площадка — замёрзшее озеро со
снежинкой-мозаикой; по краю — музейные столбики с канатом (ниже 2 стадов, круг боя свободен). По бокам — ледяные витрины
на пьедесталах (кубок, самоцвет, ключ, будильник, корона, кристалл), гряды ледника, трещины с голубым светом, ели,
сугробы. Небо — северное сияние. Без ледяных дворцов и узнаваемых чужих образов.
Каркас (пол, обрывы, пути, площадка r 31, места существ, вид сверху) — scripts/blender/concepts510/arenas.py.
Босс — поза сна (yeti.py), рост в стойке 24 стада; существа — creatures.py.

Запуск: blender --background --factory-startup --python scripts/blender/boss5/arena.py -- <репо>
Кадры: assets/concepts/bosses_5_10/boss5_v2/raw/arena5_{player,approach,top}.png и arena5_stats.json (вне git).
"""

import json
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "concepts510"))
import arenas as A  # noqa: E402
import ck as C  # noqa: E402

BOSS, HL = A.BOSS, A.HL
YETI_SCALE = 2.03  # 24 стада / рост модели в стойке 11.8 (stats.json render.py: export_scale)

PAL = {
    "snow": "F2F7FF", "snowS": "DCE8F7", "cliff": "A9C4E0", "cliffTop": "F2F7FF", "path": "D2E2F2", "tile": "8FCDF0",
    "plat": "B7ECFF", "platEdge": "3F98D6", "slot": "7FCBF0", "mosaic": "5FB6E8", "mosaicL": "E2FAFF",
    "glacier": "A6E4FA", "glacierD": "62BDE6", "glacierE": "E6FBFF", "cave": "1F3A6E", "gold": "F5B21C",
    "goldD": "C27E0E", "rope": "D8344A", "stone": "4E5F8C", "stoneD": "35426A", "pine": "2F7A5A",
    "pineD": "23604A", "trunk": "8F5A31", "crev": "203A66", "neonIce": "6FF2FF", "neonAur": "3DFFB0",
    "neonAurP": "B57CFF", "neonGem": "FF4FA3", "red": "E8384F", "white": "FFFFFF", "dark": "161824",
    "iceCase": "9FE6FF",
}
RINGS = ("snow", "cliff", "plat", "glacier", "stone", "pine", "gold")


def mk(name):
    return A.art(name, PAL, RINGS)


def rnd(seed):
    g = A.rnd(seed)
    return lambda: next(g)


# ── Задник: ледниковая стена-хранилище ────────────────────────────────────────────────────────────────────────
def backdrop():
    """Ледниковая стена-хранилище: неровные гранёные глыбы, в центре — круглая дверь хранилища (золотое кольцо,
    снежинка-штурвал, голубое свечение по кругу), перед стеной на ледяном уступе — витрины с экспонатами."""
    b = mk("Vault")
    g = rnd(55)
    # ледник — единая стена (не башни): широкий гранёный массив, над ним острые пики со смещёнными вершинами,
    # снежный карниз с сосульками
    b.frustum("glacier", (-34, 34, 36.5, 47.5), (-29, 29, 39.0, 47.0), 0.0, 14.0)
    b.frustum("glacierD", (-36, -20, 37.5, 47.5), (-33, -24, 40.0, 47.0), 0.0, 9.0)
    b.frustum("glacierD", (20, 36, 37.5, 47.5), (24, 33, 40.0, 47.0), 0.0, 8.0)
    peaks = [(-24, 10, 11, -3), (-14, 12, 16, 2), (-4, 13, 21, -2), (6, 12, 18, 3), (16, 11, 14, -2), (25, 9, 9, 2)]
    for x, w, h, off in peaks:
        b.frustum("glacier" if x % 4 else "glacierE", (x - w / 2, x + w / 2, 39.5, 46.5),
                  (x + off, x + off, 42.0 + g() * 2, 42.0 + g() * 2), 13.9, 14.0 + h, bevel=0)
        b.frustum("glacierE", (x + off - 1.6, x + off + 1.6, 41.3, 44.4), (x + off, x + off, 42.8, 42.8),
                  14.0 + h * 0.72, 14.0 + h + 0.4, bevel=0)  # снег на вершине
    b.box("glacierE", -30.5, 30.5, 38.0, 47.5, 13.6, 14.6)  # снежный карниз
    for i in range(24):
        x = -29 + i * 2.5
        b.frustum("glacierE", (x - 0.6, x + 0.6, 37.6, 38.6), (x, x, 38.1, 38.1), 13.7, 12.0 - 1.4 * g(), bevel=0)
    # ледяной уступ перед стеной
    b.prism("glacierE", C.octa((0, 34.8), 62, 4.0, 0, 0, cut=1.6)[0], 0.0, 1.6)
    for i in range(3):  # ступени к двери
        b.box("glacierE", -6.5 + i * 0.8, 6.5 - i * 0.8, 31.5 + i * 0.9, 33.0, 0.3, 0.75 + i * 0.45)
    # круглая дверь хранилища
    cx, cy, cz = 0.0, 35.2, 8.6
    b.prism("cave", C.ngon(cx, cz, 7.2, 16), cy - 0.2, cy + 0.6, axis="y")
    b.frame("neonIce", C.ngon(cx, cz, 7.9, 16), 0.7, cy - 0.35, cy + 0.2, axis="y")
    b.frame("gold", C.ngon(cx, cz, 6.9, 16), 1.3, cy - 0.7, cy - 0.15, axis="y")
    b.frame("goldD", C.ngon(cx, cz, 5.4, 16), 0.45, cy - 0.5, cy - 0.2, axis="y")
    for ang in (0, 60, 120):  # снежинка-штурвал
        m = C.tilt((cx, cy, cz), "Y", ang)
        b.box("gold", cx - 0.45, cx + 0.45, cy - 0.95, cy - 0.45, cz - 5.0, cz + 5.0, bevel=0.05, matrix=m)
        for sz in (-1, 1):
            for side in (-1, 1):
                mm = m @ C.tilt((cx, cy, cz + sz * 3.2), "Y", side * 45)
                b.box("gold", cx - 0.3, cx + 0.3, cy - 0.9, cy - 0.5, cz + sz * 3.2, cz + sz * 4.6, bevel=0.04,
                      matrix=mm)
    b.prism("goldD", C.ngon(cx, cz, 1.5, 8), cy - 1.3, cy - 0.9, axis="y")
    b.prism("neonIce", C.ngon(cx, cz, 0.75, 8), cy - 1.45, cy - 1.25, axis="y")
    for ang in range(0, 360, 45):  # заклёпки по кольцу
        t = math.radians(ang + 22.5)
        px, pz = cx + 6.2 * math.cos(t), cz + 6.2 * math.sin(t)
        b.box("goldD", px - 0.3, px + 0.3, cy - 0.95, cy - 0.65, pz - 0.3, pz + 0.3, bevel=0.03)
    # витрины на уступе — объёмные (лёд, пьедестал, экспонат), не рамки на стене
    for x, kind in ((-22.0, "trophy"), (-13.0, "gem"), (13.0, "clock"), (22.0, "crown")):
        b.prism("stone", C.ngon(x, 34.4, 2.0, 8), 1.6, 3.2)
        b.frame("gold", C.ngon(x, 34.4, 2.1, 8), 0.3, 3.0, 3.35, axis="z")
        exhibit(b, kind, (x, 34.4, 3.35), 1.0)
        b.extrude("iceCase", C.ngon(x, 34.4, 1.7, 8), 3.35, 7.6, axis="z")
        b.frustum("glacierE", (x - 1.5, x + 1.5, 32.9, 35.9), (x - 0.3, x + 0.3, 34.1, 34.7), 7.6, 8.4, bevel=0)


def _T(v):
    from mathutils import Matrix

    return Matrix.Translation(v)


# ── Экспонаты (предметы, без людей и картин) ──────────────────────────────────────────────────────────────────
def exhibit(a, kind, c, s=1.0):
    x, y, z = c
    if kind == "trophy":
        a.prism("gold", C.ngon(x, y, 0.9 * s, 8), z, z + 0.35 * s)
        a.prism("goldD", C.ngon(x, y, 0.3 * s, 8), z + 0.35 * s, z + 1.2 * s)
        a.frustum("gold", (x - 0.55 * s, x + 0.55 * s, y - 0.55 * s, y + 0.55 * s),
                  (x - 1.2 * s, x + 1.2 * s, y - 1.2 * s, y + 1.2 * s), z + 1.2 * s, z + 2.7 * s)
        for sx in (-1, 1):
            a.frame("gold", [(-0.45 * s, -0.5 * s), (0.45 * s, -0.5 * s), (0.45 * s, 0.5 * s), (-0.45 * s, 0.5 * s)],
                    0.18 * s, -0.1 * s, 0.1 * s, axis="y", matrix=_T((x + sx * 1.35 * s, y, z + 2.0 * s)))
    elif kind == "gem":
        a.frustum("neonGem", (x - 1.1 * s, x + 1.1 * s, y - 1.1 * s, y + 1.1 * s), (x, x, y, y), z + 1.4 * s,
                  z + 3.0 * s, bevel=0)
        a.frustum("neonGem", (x - 1.1 * s, x + 1.1 * s, y - 1.1 * s, y + 1.1 * s), (x, x, y, y), z + 1.4 * s, z,
                  bevel=0)
    elif kind == "clock":  # будильник
        a.prism("red", C.ngon(x, z + 1.5 * s, 1.3 * s, 10), y - 0.45 * s, y + 0.45 * s, axis="y")
        a.prism("white", C.ngon(x, z + 1.5 * s, 1.0 * s, 10), y - 0.55 * s, y - 0.4 * s, axis="y")
        a.box("dark", x - 0.08 * s, x + 0.08 * s, y - 0.62 * s, y - 0.55 * s, z + 1.45 * s, z + 2.25 * s, bevel=0)
        a.box("dark", x - 0.08 * s, x + 0.6 * s, y - 0.62 * s, y - 0.55 * s, z + 1.42 * s, z + 1.58 * s, bevel=0)
        for sx in (-1, 1):
            a.prism("gold", C.ngon(x + sx * 0.8 * s, z + 2.9 * s, 0.45 * s, 8), y - 0.3 * s, y + 0.3 * s, axis="y")
            a.box("gold", x + sx * 0.7 * s - 0.15 * s, x + sx * 0.7 * s + 0.15 * s, y - 0.15 * s, y + 0.15 * s, z,
                  z + 0.4 * s)
    elif kind == "crown":
        a.prism("gold", C.ngon(x, y, 1.2 * s, 10), z + 0.4 * s, z + 1.3 * s)
        for i in range(5):
            t = 2 * math.pi * i / 5
            px, py = x + 1.0 * s * math.cos(t), y + 1.0 * s * math.sin(t)
            a.frustum("gold", (px - 0.3 * s, px + 0.3 * s, py - 0.3 * s, py + 0.3 * s), (px, px, py, py), z + 1.3 * s,
                      z + 2.3 * s, bevel=0)
            a.prism("neonGem", C.ngon(px, py, 0.18 * s, 6), z + 0.75 * s, z + 1.0 * s)
    elif kind == "key":
        a.frame("gold", C.ngon(x, z + 2.4 * s, 0.9 * s, 8), 0.35 * s, y - 0.2 * s, y + 0.2 * s, axis="y")
        a.box("gold", x - 0.22 * s, x + 0.22 * s, y - 0.2 * s, y + 0.2 * s, z + 0.2 * s, z + 1.6 * s)
        a.box("gold", x, x + 0.7 * s, y - 0.2 * s, y + 0.2 * s, z + 0.3 * s, z + 0.6 * s)
        a.box("gold", x, x + 0.5 * s, y - 0.2 * s, y + 0.2 * s, z + 0.85 * s, z + 1.1 * s)
    elif kind == "crystal":
        for dx, h in ((-0.5, 2.2), (0.0, 3.2), (0.55, 1.8)):
            a.frustum("neonIce", (x + dx * s - 0.4 * s, x + dx * s + 0.4 * s, y - 0.4 * s, y + 0.4 * s),
                      (x + dx * s, x + dx * s, y, y), z, z + h * s, bevel=0)


def vitrine(kind, x, y, turn=0.0):
    """Ледяная витрина на каменном пьедестале с золотой окантовкой и экспонатом внутри."""
    v = mk(f"Vitrine{kind.capitalize()}{int(abs(x))}")
    v.prism("stone", C.ngon(x, y, 3.0, 8), 0.3, 2.6)
    v.frame("gold", C.ngon(x, y, 3.15, 8), 0.4, 2.4, 2.8, axis="z")
    v.prism("stoneD", C.ngon(x, y, 3.4, 8), 0.3, 0.9)
    v.extrude("iceCase", C.ngon(x, y, 2.4, 8), 2.8, 8.6, axis="z")
    v.frustum("glacierE", (x - 2.1, x + 2.1, y - 2.1, y + 2.1), (x - 0.4, x + 0.4, y - 0.4, y + 0.4), 8.6, 9.8,
              bevel=0)
    for sx in (-1, 1):  # золотые уголки
        v.box("gold", x + sx * 2.2 - 0.25, x + sx * 2.2 + 0.25, y - 0.4, y + 0.4, 2.8, 4.0)
        v.box("gold", x + sx * 2.2 - 0.25, x + sx * 2.2 + 0.25, y - 0.4, y + 0.4, 7.6, 8.8)
    v.box("gold", x - 1.0, x + 1.0, y - 3.2, y - 3.0, 1.2, 1.9)  # табличка (без текста)
    exhibit(v, kind, (x, y, 3.0), 1.35)


# ── Края зоны: гряды ледника, трещины, ели, сугробы ───────────────────────────────────────────────────────────
def glacier_ridges():
    r = mk("Ridges")
    g = rnd(5)
    for s in (1, -1):
        y = -50.0
        while y < 50:
            w = 6 + 5 * g()
            h = 10 + 13 * g()
            x = s * (82 + 6 * g())
            r.prism("glacier" if g() > 0.35 else "glacierD", C.octa((x, y), 10 + 4 * g(), w, 0, 0, cut=2.2)[0], 0.0, h,
                    matrix=C.tilt((x, y, 0), "Z", 20 * (g() - 0.5)))
            r.frustum("glacierE", (x - 4.5, x + 4.5, y - w / 2 + 0.6, y + w / 2 - 0.6), (x - 1.5, x + 1.5, y - 0.8,
                      y + 0.8), h, h + 2.5 + 2 * g(), bevel=0)
            y += w * 0.85
    for x0, y0, x1, y1 in ((-74, -40, -58, -12), (62, -36, 76, -8), (-70, 6, -52, 28), (56, 20, 74, 40)):
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        ang = math.degrees(math.atan2(dy, dx))
        m = C.tilt(((x0 + x1) / 2, (y0 + y1) / 2, 0), "Z", ang)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        r.box("crev", cx - L / 2, cx + L / 2, cy - 1.4, cy + 1.4, 0.24, 0.33, bevel=0, matrix=m)
        r.box("neonIce", cx - L / 2 + 1, cx + L / 2 - 1, cy - 0.35, cy + 0.35, 0.3, 0.34, bevel=0, matrix=m)
        for t in (-0.3, 0.1, 0.4):  # ледяные края трещины
            for sy in (-1, 1):
                px = cx + t * L
                r.box("glacierE", px - 2.2, px + 2.2, cy + sy * 1.4, cy + sy * 2.4, 0.2, 0.75, matrix=m)


def side_decor():
    d = mk("Sides")
    for i, (x, y, kk) in enumerate(A.side_spots(22, 9, x0=54, x1=78)):
        if kk < 0.6:
            h = 9 + 7 * kk
            d.prism("trunk", C.ngon(x, y, 0.7, 6), 0.3, h * 0.25)
            for j in range(3):
                z0 = h * 0.2 + j * h * 0.22
                rr = h * 0.32 * (1 - j * 0.25)
                d.frustum("pine" if j % 2 == 0 else "pineD", (x - rr, x + rr, y - rr, y + rr),
                          (x - rr * 0.3, x + rr * 0.3, y - rr * 0.3, y + rr * 0.3), z0, z0 + h * 0.3)
                d.frustum("snow", (x - rr * 0.75, x + rr * 0.75, y - rr * 0.75, y + rr * 0.75),
                          (x - rr * 0.32, x + rr * 0.32, y - rr * 0.32, y + rr * 0.32), z0 + h * 0.26, z0 + h * 0.33)
        else:  # сугроб с кристаллами
            d.frustum("snowS", (x - 4, x + 4, y - 3, y + 3), (x - 2, x + 2, y - 1.2, y + 1.2), 0.2, 2.0)
            d.frustum("neonIce", (x - 0.6, x + 0.6, y - 0.6, y + 0.6), (x + 0.3, x + 0.3, y, y), 1.5, 4.5, bevel=0)


def stanchions():
    """Музейные столбики с красным канатом по краю площадки (ниже 2 стадов): проходы у входа и к выходу."""
    s = mk("Stanchions")
    R = A.PLAT_R + 1.6
    gaps = (-90, 30, 150)  # вход и две дорожки к выходу (градусы от +x)
    angs = [a for a in range(-180, 180, 15) if all(abs(((a - g + 180) % 360) - 180) > 12 for g in gaps)]
    pts = {}
    for a in angs:
        t = math.radians(a)
        x, y = BOSS[0] + R * math.cos(t), BOSS[1] + R * math.sin(t)
        s.prism("goldD", C.ngon(x, y, 0.55, 8), 0.58, 0.8)
        s.prism("gold", C.ngon(x, y, 0.22, 8), 0.8, 1.55)
        s.prism("gold", C.ngon(x, y, 0.32, 8), 1.55, 1.8)
        pts[a] = (x, y)
    for a in angs:
        b = a + 15
        if b in pts:
            (x0, y0), (x1, y1) = pts[a], pts[b]
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            C.bar(s, "rope", (x0, y0, 1.5), (mx, my, 1.15), 0.22, 0.22, bevel=0)
            C.bar(s, "rope", (mx, my, 1.15), (x1, y1, 1.5), 0.22, 0.22, bevel=0)


def plat_mosaic(q):
    """Замёрзшее озеро: снежинка-мозаика, кольца, места существ уже нарисованы каркасом."""
    bx, by = BOSS
    q.frame("mosaic", C.ngon(bx, by, 26.0, 32), 0.8, 0.58, 0.64, axis="z")
    q.frame("mosaicL", C.ngon(bx, by, 14.0, 24), 0.6, 0.58, 0.64, axis="z")
    for i in range(6):
        t = math.radians(30 + 60 * i)
        c, s_ = math.cos(t), math.sin(t)
        C.bar(q, "mosaic", (bx + 4 * c, by + 4 * s_, 0.61), (bx + 25 * c, by + 25 * s_, 0.61), 1.1, 0.06, bevel=0)
        for r0, ln in ((12.0, 5.0), (19.0, 4.0)):
            px, py = bx + r0 * c, by + r0 * s_
            for sg in (-1, 1):
                t2 = t + sg * math.radians(45)
                C.bar(q, "mosaicL", (px, py, 0.62), (px + ln * math.cos(t2), py + ln * math.sin(t2), 0.62), 0.8, 0.05,
                      bevel=0)


def aurora():
    """Северное сияние — «занавесь» из тонких вертикальных лучей разной высоты вдоль волнистой линии за ледником."""
    au = mk("Aurora")
    for k, (y0, z0, ph, key_, hgt, n) in enumerate(((210, 46, 0.0, "neonAur", 24, 46), (240, 62, 1.7, "neonAurP", 18, 34))):
        for i in range(n):
            x = -160 + i * 320 / n
            y = y0 + 22 * math.sin(i * 0.23 + ph)
            z = z0 + 12 * math.sin(i * 0.17 + ph)
            h = hgt * (0.55 + 0.45 * abs(math.sin(i * 0.9 + ph)))
            au.box(key_, x - 4.2, x + 4.2, y - 0.3 - 0.7 * k, y + 0.3 - 0.7 * k, z, z + h, bevel=0)


def theme():
    return dict(pal=PAL, rings=RINGS, floor="snow", cliff="cliff", cliffTop="cliffTop", path="path", plat="plat",
                platEdge="platEdge", slot="slot", plat_fn=plat_mosaic, path_w=12.0,
                path_fn=lambda g: [g.box("tile", -1.6, 1.6, y, y + 3.0, 0.42, 0.5) for y in range(-50, -38, 5)])


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    repo = os.path.abspath(argv[0])
    out = os.path.join(repo, "assets", "concepts", "bosses_5_10", "boss5_v2", "raw")
    os.makedirs(out, exist_ok=True)
    import creatures  # noqa: E402
    import yeti  # noqa: E402

    A.ARTS.clear()
    col = C.reset_scene()
    cam = C.outdoor("142453", "8FC8EA", (1.0, 0.94, 0.86), 3.4, (-42, 0, 32), 0.8)  # вечер: сияние читается
    bpy.context.scene.view_settings.exposure = -0.35
    A.frame_zone(theme(), col)
    backdrop()
    for kind, x, y in (("trophy", -46, -24), ("key", 46, -24), ("crystal", -54, 2), ("gem", 54, 2),
                       ("clock", -62, 28), ("crown", 62, 28)):
        vitrine(kind, x, y)
    glacier_ridges()
    side_decor()
    stanchions()
    aurora()
    objs = [C.finish(a, col, glow=3.0) for a in A.ARTS]
    for ob, a in zip(objs, A.ARTS):  # лёд витрин полупрозрачный — экспонаты видны
        for mat in a.materials:
            if mat.name.rsplit("_", 1)[-1] in ("neonAur", "neonAurP"):  # сияние — полупрозрачные полосы сливаются
                b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
                b.inputs["Alpha"].default_value = 0.4
                mat.surface_render_method = "BLENDED"
            if mat.name.rsplit("_", 1)[-1] == "iceCase":
                b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
                b.inputs["Alpha"].default_value = 0.3
                mat.surface_render_method = "BLENDED"
                mat.use_backface_culling = True
    ya = yeti.yeti("sleep")
    yo = C.finish(ya, col, glow=4.0)
    for mat in ya.materials:
        k = mat.name.rsplit("_", 1)[-1]
        b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b is not None and k in ("iceBlock", "iceE", "lens"):
            b.inputs["Alpha"].default_value = 0.35
            mat.surface_render_method = "BLENDED"
            mat.use_backface_culling = True
    yo.scale = (YETI_SCALE,) * 3
    yo.location = (BOSS[0], BOSS[1], 0.58)
    for (x, y), idx in zip(A.SLOTS, (0, 4, 7, 9)):  # Common, Rare, Epic, Legendary — по одному на место
        for ob in creatures.build(idx, col):
            ob.scale = (1.5, 1.5, 1.5)
            ob.location = (x, y, 0.9)
            ob.rotation_euler = (0, 0, math.radians(-20 if x > 0 else 20))
    ov = C.finish(A.overlay(), col, glow=4.0)
    ov.hide_render = True
    C.shot(cam, os.path.join(out, "arena5_player.png"), (0, -66, 14), (0, -2, 8), 22, (1600, 900))
    C.shot(cam, os.path.join(out, "arena5_approach.png"), (-34, -40, 22), (0, 8, 6), 24, (1600, 900))
    ov.hide_render = False
    A.top_view(cam, os.path.join(out, "arena5_top.png"))
    stats = {"primitives": {a.name: len(a.parts) for a in A.ARTS}, "total": sum(len(a.parts) for a in A.ARTS)}
    with open(os.path.join(out, "arena5_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    print("STATS", json.dumps(stats, ensure_ascii=False), flush=True)


main()
