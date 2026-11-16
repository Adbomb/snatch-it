"""Концепты арен боссов 5–10: зона 184 × 95 стадов с ракурса игрока и сверху (черновые блочные сцены).

Общий каркас взят из MapLayout: ширина коридора ±92, длина зоны 95 (вход y = −47.5, выход y = +47.5), босс в
(0, −5), площадка r 31, круг боя r 34 свободен от декора выше 2, места 4 существ как у зоны 4 (D59). Пути: вход →
площадка по центру, от площадки к выходу двумя дорожками по бокам задника (x ±40) — видно, куда идти дальше; во
входе зоны — те же две дорожки сходятся к центру (цепочка зон без тупиков). 1 единица = 1 стад. Босс — поза сна ×3.
Числа деталей в *_stats.json — примитивы черновой сцены, а не детали игры (оценка игры — в OVERVIEW.md).
"""

import importlib
import json
import math
import os

import bpy
import ck as C

HW, HL = 92.0, 47.5  # половина ширины коридора, половина длины зоны
BOSS = (0.0, -5.0)
PLAT_R, FIGHT_R = 31.0, 34.0
SLOTS = [(-22, -18), (23, -16), (-22, 12), (21, 13)]
EXIT_PATHS = [((26.0, 14.0), (40.0, HL)), ((-26.0, 14.0), (-40.0, HL))]
ENTRY_PATHS = [((40.0, -HL), (9.0, -38.0)), ((-40.0, -HL), (-9.0, -38.0))]
ARTS = []


def art(name, pal, rings=()):
    a = C.new_art(name, ring=C.RING_ARENA)
    for k, v in pal.items():
        a.paint(k, v, rings=k in rings)
    ARTS.append(a)
    return a


def rnd(seed):
    """Детерминированные псевдослучайные числа 0…1 (одинаковые кадры при каждом запуске)."""
    x = seed * 2654435761 % 4294967296
    while True:
        x = (1103515245 * x + 12345) % 2147483648
        yield x / 2147483648


def side_spots(n, seed, x0=50.0, x1=86.0, y0=-44.0, y1=44.0):
    """Точки декора в боковых полосах (обе стороны), вне путей и круга боя."""
    g = rnd(seed)
    pts = []
    while len(pts) < n:
        s = 1 if len(pts) % 2 == 0 else -1
        x, y = s * (x0 + (x1 - x0) * next(g)), y0 + (y1 - y0) * next(g)
        if math.hypot(x - BOSS[0], y - BOSS[1]) < FIGHT_R + 6:
            continue
        if any(abs(x - (p0[0] + (p1[0] - p0[0]) * t)) < 9 and abs(y - (p0[1] + (p1[1] - p0[1]) * t)) < 9
               for p0, p1 in EXIT_PATHS + ENTRY_PATHS for t in (0.0, 0.25, 0.5, 0.75, 1.0)):
            continue
        pts.append((x, y, next(g)))
    return pts


def frame_zone(T, col):
    """Пол, обрывы с уступами, пути, площадка с местами существ."""
    p = T["pal"]
    g = art("Ground", p, T.get("rings", ()))
    g.box(T["floor"], -HW, HW, -HL - 6, HL + 6, -1.0, 0.3)
    for s in (1, -1):
        g.box(T["cliff"], s * HW, s * (HW + 14), -HL - 6, HL + 6, 0.0, 16.0)
        g.box(T["cliffTop"], s * (HW - 0.6), s * (HW + 14), -HL - 6, HL + 6, 16.0, 17.2)
        g.box(T["cliff"], s * (HW + 9), s * (HW + 40), -HL - 6, HL + 6, 17.2, 30.0)
        g.box(T["cliffTop"], s * (HW + 8.4), s * (HW + 40), -HL - 6, HL + 6, 30.0, 31.2)
    w = T.get("path_w", 12.0)
    g.box(T["path"], -w / 2, w / 2, -HL - 6, BOSS[1] - PLAT_R + 1, 0.3, 0.42)
    for p0, p1 in EXIT_PATHS + ENTRY_PATHS:
        C.bar(g, T["path"], (p0[0], p0[1], 0.36), (p1[0], p1[1], 0.36), w, 0.12, bevel=0)
    if "path_fn" in T:
        T["path_fn"](g)
    q = art("Platform", p, T.get("rings", ()))
    q.prism(T["plat"], C.ngon(BOSS[0], BOSS[1], PLAT_R, 32), 0.3, 0.58)
    q.frame(T["platEdge"], C.ngon(BOSS[0], BOSS[1], PLAT_R + 0.8, 32), 1.6, 0.3, 0.8, axis="z")
    if "plat_fn" in T:
        T["plat_fn"](q)
    for x, y in SLOTS:
        q.prism(T["slot"], C.ngon(x, y, 2.6, 8), 0.58, 0.9)
        q.frame(T["platEdge"], C.ngon(x, y, 2.75, 8), 0.3, 0.58, 0.98, axis="z")


def overlay():
    """Схема для вида сверху: круг боя r 34, места существ, стрелки путей (только на виде сверху)."""
    o = C.new_art("Overlay")
    o.paint("neonW", "FFFFFF")
    o.paint("neonR", "FF3048")
    o.paint("neonG", "3DFF7A")
    for i in range(36):
        if i % 2 == 0:
            t0, t1 = math.radians(i * 10), math.radians(i * 10 + 10)
            C.bar(o, "neonW", (BOSS[0] + FIGHT_R * math.cos(t0), BOSS[1] + FIGHT_R * math.sin(t0), 3.0),
                  (BOSS[0] + FIGHT_R * math.cos(t1), BOSS[1] + FIGHT_R * math.sin(t1), 3.0), 0.7, 0.1, bevel=0)
    for x, y in SLOTS:
        o.frame("neonR", C.ngon(x, y, 3.6, 12), 0.6, 3.0, 3.1, axis="z")
    for p0, p1 in EXIT_PATHS + ENTRY_PATHS + [((0, -HL), (0, BOSS[1] - PLAT_R))]:
        C.bar(o, "neonG", (p0[0], p0[1], 3.0), (p1[0], p1[1], 3.0), 0.8, 0.1, bevel=0)
    return o


def place_boss(n, col):
    mod = importlib.import_module(f"boss{n}")
    objs = mod.build(col, "sleep")
    for ob in objs:
        ob.scale = (3, 3, 3)
        ob.location = (BOSS[0], BOSS[1], 0.58)
    return objs


def place_creatures(n, col, picks=(0, 4, 6, 8)):
    mod = importlib.import_module(f"creatures{n}")
    for (x, y), i in zip(SLOTS, picks):
        for ob in mod.CREATURES[i][3](col):
            ob.scale = (1.4, 1.4, 1.4)
            ob.location = (x, y, 0.9)
            ob.rotation_euler = (0, 0, math.radians(-20 if x > 0 else 20))  # чуть к центральному пути


def top_view(cam, path):
    """Вид сверху: вход внизу кадра, выход вверху (камера без поворота смотрит вниз, верх кадра — +y)."""
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = 1600, 900
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 212
    cam.data.clip_end = 2000
    cam.location = (0, 0, 300)
    cam.rotation_euler = (0, 0, 0)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def render(n, out):
    from themes import THEMES  # noqa: E402

    ARTS.clear()
    T = THEMES[n]
    col = C.reset_scene()
    cam = C.outdoor(T["sky_top"], T["sky_bot"], T.get("sun_color", (1, 0.96, 0.9)), T.get("sun", 3.2),
                    T.get("sun_dir", (-50, 0, 35)), T.get("ambient", 0.9))
    bpy.context.scene.view_settings.exposure = T.get("exposure", 0.0)
    frame_zone(T, col)
    T["decor"](lambda name, rings=(): art(name, T["pal"], rings))
    objs = [C.finish(a, col, glow=T.get("glow", 3.0)) for a in ARTS]
    place_boss(n, col)
    place_creatures(n, col)
    ov = C.finish(overlay(), col, glow=4.0)
    ov.hide_render = True
    C.shot(cam, os.path.join(out, f"arena{n}_player.png"), (0, -66, 14), (0, -2, 8), 22, (1600, 900))
    C.shot(cam, os.path.join(out, f"arena{n}_approach.png"), (-34, -40, 22), (0, 8, 6), 24, (1600, 900))
    ov.hide_render = False
    top_view(cam, os.path.join(out, f"arena{n}_top.png"))
    stats = {"primitives": {a.name: len(a.parts) for a in ARTS}, "total": sum(len(a.parts) for a in ARTS)}
    with open(os.path.join(out, f"arena{n}_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    del objs
