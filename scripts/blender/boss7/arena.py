"""Арена 7 «Банк» (концепт D64): хранилище банка вокруг Копилки-громилы, зона 184 × 95 стадов.

Задумка: несколько крупных узнаваемых элементов, а не сотни мелких.
- Задник — огромная круглая дверь сейфа из тёмной стали (ø 32) с золотым ободом, засовами по кругу и штурвалом;
  за ней — тёмная стальная стена хранилища с клёпаными панелями. Розовая свинья стоит на фоне тёмной стали —
  главное пятно кадра.
- Мраморные колонны (тёмно-зелёный мрамор, золотые база и капитель): пара у двери, пара в рамке входа, колоннада
  по бокам за полосами.
- Золото: штабеля слитков (пирамидами) и горы монет с огромными монетами на ребре — у двери и по бокам, крупно.
- Пол — тёмно-зелёный мрамор крупной шахматкой; площадка — тёмный сине-зелёный мрамор с золотыми кольцами-инкрустацией
  (как монета); центральный путь — тёмно-синяя мраморная дорожка с золотой каймой.
- Плиты существ (D71): тёмный круг, золотой обод, кольцо-подсветка снизу цветом редкости существа на плите.
Свободный бег (D66, как «Джунгли»): две прямые полосы |x| 48–66 насквозь от входа до выхода и дальше (до y 76),
перемычки площадка ↔ полосы, центральный путь; в прямоугольниках путей ничего на высоте 1.1–7 над полом (пол и
инкрустация ниже, перемычки ворот на выходе — выше 9). Декор — у стен (|x| > 66) или в середине вне круга боя r 34.
Твёрдое у стен (|x| > 76) — верх не выше 24. Без людей, статуй, картин, текста, логотипов банков, купюр, оружия и
охранников; ничего похожего на виселицу или петлю (ворота — две массивные опоры и толстая балка, ничего не свисает).
Каркас (пол, обрывы, площадка, места существ, вид сверху) — concepts510/arenas.py; босс — piggy.py (поза сна),
существа — creatures.py.

Запуск: blender --background --factory-startup --python scripts/blender/boss7/arena.py -- <репо> [quick] [player,approach,lane,top]
Кадры: assets/concepts/bosses_5_10/boss7/raw/arena7_{player,approach,lane,top}.png и arena7_stats.json (вне git).
"""

import json
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "concepts510"))
import arenas as A  # noqa: E402
import ck as C  # noqa: E402
import stand_colors as SC  # noqa: E402

BOSS, HL, HW = A.BOSS, A.HL, A.HW
LANE_X, LANE_W = 57.0, 18.0  # полосы |x| 48–66 (D66, MapLayout.Lane)
LANE_IN, LANE_OUT = LANE_X - LANE_W / 2, LANE_X + LANE_W / 2
LINK_W = 10.0
FLOOR = 0.3  # верх пола зоны
FIGHT_R = 34.0
LANE_Z = (FLOOR + 1.1, FLOOR + 7.0)
WALL_X, WALL_TOP = 76.0, 24.0
Y0, Y1 = -HL - 6, HL + 6
EXIT_Y = 76.0
DOOR_C = (0.0, 41.0, 17.5)  # центр двери сейфа
DOOR_R = 16.0
SLOT_RARITY = ("Common", "Rare", "Epic", "Legendary")  # по местам A.SLOTS: что лежит — тем цветом и светится плита

PAL = {
    "marble": "1F4A3D", "marbleD": "173A30", "marbleL": "2F6B57", "vein": "5E9C86",  # тёмно-зелёный мрамор
    "marbleB": "1C3049", "marbleBD": "142338",  # тёмный сине-зелёный мрамор: площадка, дорожки
    "steel": "2C3344", "steelD": "1E2330", "steelL": "4A5670", "rivet": "8792AA",  # сталь хранилища
    "gold": "F5B21C", "goldD": "C9820E", "goldL": "FFD866",  # золото: обод, капители, слитки
    "coin": "FFC93A", "coinL": "FFE27A",
    "slotP": "151926",  # плита места существа — тёмный круг
    "cliffTop": "3A4357", "white": "FFFFFF",
}
RINGS = ("marble", "marbleL", "marbleB", "steel", "steelL", "gold")
FREE, EXIT_FREE = [], []
GAME = {}  # части игры по категориям (крупное — меши)


def mk(name):
    return A.art(name, PAL, RINGS)


def part(cat, n=1):
    GAME[cat] = GAME.get(cat, 0) + n


def near_fight(x, y, r=0.0):
    return math.hypot(x - BOSS[0], y - BOSS[1]) < FIGHT_R + r


# ── Пол, полосы, площадка ─────────────────────────────────────────────────────────────────────────────────────
def theme():
    return dict(pal=PAL, rings=RINGS, floor="marble", cliff="steel", cliffTop="cliffTop", path="marbleB",
                plat="marbleB", platEdge="gold", slot="slotP", plat_fn=plat_inlay, path_w=12.0)


def floor_checker():
    """Шахматка тёмного мрамора крупными плитами 12 × 12 (тёмные плиты — накладки 0.02) и золотая кайма путей."""
    f = mk("Floor")
    step = 12.0
    for i in range(-8, 8):
        for j in range(-5, 5):
            if (i + j) % 2:
                continue
            x0, y0 = i * step, j * step
            x1, y1 = x0 + step, y0 + step
            if x1 <= -HW or x0 >= HW:
                continue
            f.box("marbleD", max(x0, -HW) + 0.05, min(x1, HW) - 0.05, max(y0, Y0) + 0.05, min(y1, Y1) - 0.05,
                  FLOOR - 0.05, FLOOR + 0.02, bevel=0)
    # полосы бега: тёмная мраморная дорожка с золотой каймой (низко, пробегается) — насквозь и за выход
    for s in (1, -1):
        xa, xb = sorted((s * LANE_IN, s * LANE_OUT))
        FREE.append((xa, xb, Y0, Y1, FLOOR))
        EXIT_FREE.append((xa, xb, Y1, EXIT_Y, FLOOR))
        f.box("marbleBD", xa + 0.6, xb - 0.6, Y0, EXIT_Y, FLOOR - 0.04, FLOOR + 0.05, bevel=0)
        for x in (xa, xb):
            f.box("gold", x - 0.3, x + 0.3, Y0, EXIT_Y, FLOOR - 0.04, FLOOR + 0.09, bevel=0)
    f.box("marble", -HW, HW, Y1, EXIT_Y, -1.0, FLOOR - 0.06)  # пол за выходом (коридор к следующей зоне)
    # перемычки площадка ↔ полосы и центральный путь — та же дорожка
    for s in (1, -1):
        xa, xb = sorted((s * (A.PLAT_R - 1.0), s * (LANE_IN + 0.3)))
        y0, y1 = BOSS[1] - LINK_W / 2, BOSS[1] + LINK_W / 2
        FREE.append((xa, xb, y0, y1, FLOOR))
        f.box("marbleBD", xa, xb, y0 + 0.6, y1 - 0.6, FLOOR - 0.03, FLOOR + 0.06, bevel=0)
        for y in (y0, y1):
            f.box("gold", xa, xb, y - 0.3, y + 0.3, FLOOR - 0.03, FLOOR + 0.08, bevel=0)
    yt = BOSS[1] - A.PLAT_R + 1
    FREE.append((-6.0, 6.0, Y0, yt, FLOOR))
    for x in (-6.0, 6.0):
        f.box("gold", x - 0.3, x + 0.3, Y0, yt, FLOOR + 0.1, FLOOR + 0.2, bevel=0)
    part("пол и обрывы (текстурой)", 8)


def plat_inlay(q):
    """Площадка-«монета»: золотые кольца-инкрустация и лучи (низко, ≤ 0.1 над площадкой)."""
    bx, by = BOSS
    for r, w in ((28.5, 0.7), (24.0, 0.45), (14.0, 0.45)):
        q.frame("gold", C.ngon(bx, by, r, 40), w, 0.58, 0.66, axis="z")
    for i in range(16):
        t = math.radians(11.25 + 22.5 * i)
        C.bar(q, "goldD", (bx + 15.0 * math.cos(t), by + 15.0 * math.sin(t), 0.62),
              (bx + 23.2 * math.cos(t), by + 23.2 * math.sin(t), 0.62), 0.35, 0.06, bevel=0)
    part("площадка", 6)


def slot_glow(col):
    """Плиты существ (D71): тёмный круг и золотой обод уже из каркаса; кольцо-подсветка цветом редкости и свет снизу."""
    g = C.new_art("SlotGlow")
    for k in SLOT_RARITY:
        g.paint("neon" + k, SC.RARITY[k][0])
    for (x, y), rar in zip(A.SLOTS, SLOT_RARITY):
        g.frame("neon" + rar, C.ngon(x, y, 3.25, 16), 0.32, 0.52, 0.62, axis="z")
    ob = C.finish(g, col, glow=5.0)
    for (x, y), rar in zip(A.SLOTS, SLOT_RARITY):
        ld = bpy.data.lights.new(f"Slot{rar}", "POINT")
        ld.color = tuple(c / 255 for c in SC.rgb(SC.RARITY[rar][1]))
        ld.energy, ld.shadow_soft_size = 900, 1.5
        lo = bpy.data.objects.new(f"Slot{rar}", ld)
        lo.location = (x, y, 1.6)
        bpy.context.scene.collection.objects.link(lo)
    part("площадка", 8)  # 4 кольца + 4 SurfaceLight / PointLight
    return ob


# ── Задник: дверь сейфа, стена хранилища ──────────────────────────────────────────────────────────────────────
def vault():
    v = mk("Vault")
    cx, cy, cz = DOOR_C
    # стена хранилища: тёмная сталь с клёпаными панелями, |x| < 46 (полосы и их обочина свободны)
    v.box("steelD", -46, 46, cy + 2.5, Y1, FLOOR, 38.0)
    for i in range(-3, 4):
        x = i * 13.0
        v.box("steel", x - 6.0, x + 6.0, cy + 2.0, cy + 2.6, FLOOR + 1.0, 37.0)
        for z in (3.0, 35.0):
            for dx in (-4.5, 4.5):
                v.box("rivet", x + dx - 0.35, x + dx + 0.35, cy + 1.75, cy + 2.05, z - 0.35, z + 0.35, bevel=0)
    v.box("steelL", -46.5, 46.5, cy + 1.6, Y1, 37.5, 39.5)  # карниз
    # рама двери: толстое стальное кольцо с золотым внутренним ободом
    v.frame("steel", C.ngon(cx, cz, DOOR_R + 3.2, 24), 3.6, cy - 0.8, cy + 2.2, axis="y")
    v.frame("gold", C.ngon(cx, cz, DOOR_R + 0.5, 24), 0.9, cy - 1.2, cy - 0.6, axis="y")
    # дверь: тёмный стальной диск, кольца-ступени, засовы по кругу, штурвал
    v.prism("steelD", C.ngon(cx, cz, DOOR_R, 24), cy - 1.6, cy + 1.0, axis="y")
    v.prism("steel", C.ngon(cx, cz, DOOR_R - 2.5, 24), cy - 2.4, cy - 1.5, axis="y")
    v.frame("steelL", C.ngon(cx, cz, DOOR_R - 2.6, 24), 0.6, cy - 2.6, cy - 2.3, axis="y")
    v.prism("steelD", C.ngon(cx, cz, 6.6, 16), cy - 3.0, cy - 2.3, axis="y")
    for i in range(12):  # засовы — короткие цилиндры поперёк обода
        t = math.radians(15 + 30 * i)
        x, z = cx + (DOOR_R - 1.0) * math.cos(t), cz + (DOOR_R - 1.0) * math.sin(t)
        v.prism("gold", C.ngon(x, z, 0.9, 8), cy - 2.0, cy - 1.5, axis="y")
        v.prism("goldD", C.ngon(x, z, 0.5, 8), cy - 2.3, cy - 1.95, axis="y")
    # штурвал: золотое кольцо, шесть спиц, ступица
    v.frame("gold", C.ngon(cx, cz, 5.4, 24), 0.8, cy - 3.9, cy - 3.1, axis="y")
    for i in range(6):
        t = math.radians(30 * (2 * i) + 15)
        C.bar(v, "goldD", (cx + 1.0 * math.cos(t), cy - 3.5, cz + 1.0 * math.sin(t)),
              (cx + 5.1 * math.cos(t), cy - 3.5, cz + 5.1 * math.sin(t)), 0.6, 0.6, bevel=0)
        C.bar(v, "gold", (cx + 5.2 * math.cos(t), cy - 3.5, cz + 5.2 * math.sin(t)),
              (cx + 6.4 * math.cos(t), cy - 3.5, cz + 6.4 * math.sin(t)), 0.8, 0.8, bevel=0)  # рукояти
    v.prism("gold", C.ngon(cx, cz, 1.6, 12), cy - 4.1, cy - 2.9, axis="y")
    # петли двери справа
    for z in (cz - 9.0, cz + 9.0):
        v.box("steelL", cx + DOOR_R + 0.5, cx + DOOR_R + 3.2, cy - 2.2, cy - 0.4, z - 2.0, z + 2.0)
    part("задник (меши)", 4)
    return v


# ── Колонны, золото ───────────────────────────────────────────────────────────────────────────────────────────
def column(c, x, y, h, r=2.4):
    """Мраморная колонна: золотая ступенчатая база, восьмигранный ствол с прожилками, золотая капитель."""
    c.prism("gold", C.ngon(x, y, r + 1.0, 8), FLOOR, FLOOR + 0.8)
    c.prism("goldD", C.ngon(x, y, r + 0.55, 8), FLOOR + 0.75, FLOOR + 1.6)
    c.prism("marbleL", C.ngon(x, y, r, 8), FLOOR + 1.55, h - 1.6)
    for k in range(3):  # прожилки мрамора: косые светлые полосы на стволе
        t = math.radians(45 * k + 20)
        z0 = FLOOR + 3.0 + k * (h - 6) / 3
        C.bar(c, "vein", (x + (r + 0.02) * math.cos(t), y - (r + 0.02) * abs(math.sin(t)) * 0 - r * 0.4, z0),
              (x + (r + 0.02) * math.cos(t + 0.6), y - r * 0.4, z0 + 2.4), 0.22, 0.12, bevel=0)
    c.prism("goldD", C.ngon(x, y, r + 0.55, 8), h - 1.65, h - 0.8)
    c.prism("gold", C.ngon(x, y, r + 1.1, 8), h - 0.85, h)


def columns():
    c = mk("Columns")
    spots = [(-24.0, 36.0, 30.0), (24.0, 36.0, 30.0),  # у двери
             (-26.0, -44.0, 26.0), (26.0, -44.0, 26.0),  # рамка входа
             (-40.0, -26.0, 22.0), (40.0, -26.0, 22.0), (-40.0, 24.0, 22.0), (40.0, 24.0, 22.0)]  # середина
    for s in (1, -1):  # колоннада за полосами (|x| 72): твёрдое ≤ 24 там не требуется, но держим 22
        for y in (-36.0, -12.0, 12.0, 36.0):
            spots.append((s * 72.0, y, 22.0))
    for x, y, h in spots:
        assert not near_fight(x, y, 3.5), (x, y)
        column(c, x, y, h)
    part("колонны (меши)", len(spots))
    return c


def bars_pile(b, x, y, n=4, turn=0.0, bar=(4.4, 2.2, 1.2)):
    """Штабель золотых слитков пирамидой (n в нижнем ряду): каждый слиток — усечённая пирамида."""
    L, W, H = bar
    m = C.tilt((x, y, 0), "Z", turn)
    for row in range(n):
        k = n - row
        for i in range(k):
            bx = x + (i - (k - 1) / 2) * (W + 0.12)
            z0 = FLOOR + row * H
            b.frustum("gold" if (i + row) % 2 else "goldL", (bx - W / 2, bx + W / 2, y - L / 2, y + L / 2),
                      (bx - W * 0.36, bx + W * 0.36, y - L * 0.4, y + L * 0.4), z0, z0 + H - 0.01, matrix=m)


def coin_mound(b, x, y, r, h, big=()):
    """Гора монет: ступенчатый золотой холм и огромные монеты на ребре (big = [(угол, наклон)])."""
    for k, (rr, z0, z1) in enumerate(((r, FLOOR, FLOOR + h * 0.4), (r * 0.72, FLOOR + h * 0.36, FLOOR + h * 0.72),
                                      (r * 0.42, FLOOR + h * 0.68, FLOOR + h))):
        b.prism("coin" if k % 2 == 0 else "coinL", C.ngon(x, y, rr, 10), z0, z1)
    for ang, lean in big:
        t = math.radians(ang)
        cx, cy = x + r * 0.55 * math.cos(t), y + r * 0.55 * math.sin(t)
        m = C.tilt((cx, cy, FLOOR + h * 0.5), "Z", ang + 90) @ C.tilt((cx, cy, FLOOR + h * 0.5), "X", lean)
        b.prism("gold", C.ngon(cx, FLOOR + h * 0.5 + 1.6, 2.2, 10), cy - 0.3, cy + 0.3, axis="y", matrix=m)
        b.prism("goldL", C.ngon(cx, FLOOR + h * 0.5 + 1.6, 1.5, 10), cy - 0.42, cy - 0.25, axis="y", matrix=m)


def treasure():
    b = mk("Treasure")
    piles = [(-33.0, 31.0, 4, 20), (33.0, 31.0, 4, -20), (-82.0, -30.0, 5, 8), (82.0, 8.0, 5, -12),
             (-82.0, 28.0, 4, 0), (82.0, -34.0, 4, 15)]
    for x, y, n, t in piles:
        assert not near_fight(x, y, 4), (x, y)
        bars_pile(b, x, y, n, t)
    mounds = [(-34.0, 42.0, 6.0, 5.0, [(200, 12)]), (34.0, 42.0, 6.0, 5.0, [(-20, -12)]),
              (-84.0, 0.0, 6.5, 6.0, [(160, 10), (20, -8)]), (84.0, -14.0, 6.5, 6.0, [(200, 10)]),
              (84.0, 36.0, 5.5, 5.0, [(160, -10)])]
    for x, y, r, h, big in mounds:
        assert not near_fight(x, y, r), (x, y)
        coin_mound(b, x, y, r, h, big)
    part("золото (меши)", len(piles) + len(mounds))
    return b


def side_walls():
    """Стальные стены-обрывы: вертикальные клёпаные рёбра и золотая полоса по верху уступа (≤ 24 у стен)."""
    w = mk("SideWalls")
    for s in (1, -1):
        y = Y0 + 4
        while y < Y1:
            w.box("steelL", s * (HW - 0.6), s * HW, y - 0.9, y + 0.9, FLOOR, 15.5)
            for z in (3.0, 9.0, 14.0):
                w.box("rivet", s * (HW - 0.9), s * (HW - 0.55), y - 0.3, y + 0.3, z - 0.3, z + 0.3, bevel=0)
            y += 10.0
        w.box("gold", s * (HW - 0.8), s * (HW + 0.2), Y0, Y1, 15.6, 16.3)
    part("стены (меши)", 2)
    return w


def exit_gates():
    """Ворота хранилища над полосами на выходе: две массивные опоры вне полосы и толстая балка выше 9 — проём
    полосы свободен по всей высоте 1.1–7 (ничего не свисает)."""
    g = mk("Gates")
    for s in (1, -1):
        xa, xb = sorted((s * LANE_IN, s * LANE_OUT))
        for x0, x1 in ((xa - 4.0, xa - 0.4), (xb + 0.4, xb + 4.0)):
            g.box("steel", x0, x1, Y1 - 3.0, Y1 + 1.0, FLOOR, 13.0)
            g.box("gold", x0 - 0.3, x1 + 0.3, Y1 - 3.3, Y1 + 1.3, FLOOR, FLOOR + 1.0)
        g.box("steel", xa - 4.0, xb + 4.0, Y1 - 3.0, Y1 + 1.0, 10.0, 13.5)
        g.box("gold", xa - 4.3, xb + 4.3, Y1 - 3.3, Y1 + 1.3, 13.5, 14.3)
        for x in (xa + 3.0, (xa + xb) / 2, xb - 3.0):
            g.box("rivet", x - 0.4, x + 0.4, Y1 - 3.3, Y1 - 3.0, 11.3, 12.1, bevel=0)
    part("ворота (меши)", 2)
    return g


# ── Проверки (как у арены 6) ──────────────────────────────────────────────────────────────────────────────────
SKIP_CHECK = ("Ground", "Platform", "Floor")  # пол, обрывы, площадка и инкрустация — ниже 1.1
TOL = 0.2


def check_free(arts):
    bad, wall, fight, ext = [], [], [], []
    for a in arts:
        if a.name in SKIP_CHECK:
            continue
        for bm, _key, _solid, _grp in a.parts:
            xs = [v.co.x for v in bm.verts]
            ys = [v.co.y for v in bm.verts]
            zs = [v.co.z for v in bm.verts]
            lo, hi = min(zs), max(zs)
            box = (a.name, round(min(xs), 1), round(max(xs), 1), round(min(ys), 1), round(max(ys), 1), round(lo, 1),
                   round(hi, 1))
            for rects, out in ((FREE, bad), (EXIT_FREE, ext)):
                for x0, x1, y0, y1, _fl in rects:
                    if min(xs) < x1 - TOL and max(xs) > x0 + TOL and min(ys) < y1 - TOL and max(ys) > y0 + TOL:
                        if lo < LANE_Z[1] and hi > LANE_Z[0]:
                            out.append(box)
                            break
            in_zone = min(ys) < Y1 and max(ys) > Y0
            if in_zone and max(abs(min(xs)), abs(max(xs))) > WALL_X and hi > WALL_TOP:
                wall.append(box)
            if hi > FLOOR + 2.0:
                nx = min(max(BOSS[0], min(xs)), max(xs))
                ny = min(max(BOSS[1], min(ys)), max(ys))
                if math.hypot(nx - BOSS[0], ny - BOSS[1]) < FIGHT_R - 0.3:
                    fight.append(box)
    return bad, wall, fight, ext


def overlay():
    """Схема сверху: круг боя (белый пунктир), места существ (красные), свободные пути (зелёные контуры), граница
    «у стен» |x| 76 (жёлтый пунктир)."""
    o = C.new_art("Overlay")
    for k, v in (("neonW", "FFFFFF"), ("neonR", "FF3048"), ("neonG", "3DFF7A"), ("neonY", "FFD400")):
        o.paint(k, v)
    for s_ in (1, -1):
        y = -HL
        while y < HL:
            C.bar(o, "neonY", (s_ * WALL_X, y, 45.0), (s_ * WALL_X, min(y + 4.0, HL), 45.0), 0.7, 0.1, bevel=0)
            y += 8.0
    for i in range(0, 36, 2):
        t0, t1 = math.radians(i * 10), math.radians(i * 10 + 10)
        C.bar(o, "neonW", (BOSS[0] + FIGHT_R * math.cos(t0), BOSS[1] + FIGHT_R * math.sin(t0), 45.0),
              (BOSS[0] + FIGHT_R * math.cos(t1), BOSS[1] + FIGHT_R * math.sin(t1), 45.0), 0.7, 0.1, bevel=0)
    for x, y in A.SLOTS:
        o.frame("neonR", C.ngon(x, y, 3.6, 12), 0.6, 45.0, 45.1, axis="z")
    for x0, x1, y0, y1, _ in FREE + EXIT_FREE:
        o.frame("neonG", [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 0.6, 45.0, 45.1, axis="z")
    return o


def sky(top, mid, bottom):
    nt = bpy.context.scene.world.node_tree
    ramp = next(n for n in nt.nodes if n.type == "VALTORGB")
    els = ramp.color_ramp.elements
    els[0].position, els[1].position = 0.0, 0.42
    els[0].color, els[1].color = (*C.S.lin(bottom), 1), (*C.S.lin(top), 1)
    e = els.new(0.12)
    e.color = (*C.S.lin(mid), 1)


def boss_scale(out):
    try:
        with open(os.path.join(out, "stats.json"), encoding="utf-8") as f:
            return float(json.load(f).get("export_scale", 1.9))
    except (OSError, ValueError):
        return 1.9


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    repo = os.path.abspath(argv[0])
    quick = "quick" in argv[1:]
    views = next((a.split(",") for a in argv[1:] if a != "quick" and "=" not in a),
                 ["player", "approach", "lane", "top"])
    out = os.path.join(repo, "assets", "concepts", "bosses_5_10", "boss7", "raw")
    os.makedirs(out, exist_ok=True)
    A.ARTS.clear()
    A.EXIT_PATHS[:] = []
    A.ENTRY_PATHS[:] = []
    FREE.clear()
    EXIT_FREE.clear()
    GAME.clear()
    col = C.reset_scene()
    cam = C.outdoor("1B2440", "3A4A62", (1.0, 0.9, 0.72), 3.4, (52, 0, -28), 0.55)
    bpy.context.scene.view_settings.exposure = 0.05
    sky("121a30", "2a3550", "56607a")
    if quick:
        bpy.context.scene.eevee.taa_render_samples = 12
    A.frame_zone(theme(), col)
    part("пол и обрывы (текстурой)", 6)
    floor_checker()
    vault()
    columns()
    treasure()
    side_walls()
    exit_gates()
    bad, wall, fight, ext = check_free(A.ARTS)
    print("FREE_LANES", "ok" if not bad else f"FAIL {len(bad)}: {bad[:20]}", flush=True)
    print("FREE_LANES exit", "ok" if not ext else f"FAIL {len(ext)}: {ext[:20]}", flush=True)
    print("FREE_LANES walls_24", "ok" if not wall else f"FAIL {len(wall)}: {wall[:20]}", flush=True)
    print("FREE_LANES fight_r34", "ok" if not fight else f"FAIL {len(fight)}: {fight[:12]}", flush=True)
    tris, prims = {}, {}
    for a in A.ARTS:
        prims[a.name] = len(a.parts)
        ob = C.finish(a, col, glow=3.0)
        tris[a.name] = a.stats["tris"]
        for mat in a.materials:
            k = mat.name.rsplit("_", 1)[-1]
            bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if bsdf is not None and k.startswith(("gold", "coin")):
                bsdf.inputs["Metallic"].default_value = 0.55
                bsdf.inputs["Roughness"].default_value = 0.28
            elif bsdf is not None and k.startswith("marble"):
                bsdf.inputs["Roughness"].default_value = 0.22  # полированный мрамор
            elif bsdf is not None and k.startswith("steel"):
                bsdf.inputs["Metallic"].default_value = 0.4
                bsdf.inputs["Roughness"].default_value = 0.4
        del ob
    slot_glow(col)
    # тёплый свет хранилища: заливка от двери и сверху (в игре — свет зоны D67)
    for name, loc, energy, color in (("VaultFill", (0, 20, 30), 90000, (1.0, 0.85, 0.6)),
                                     ("EntryFill", (0, -40, 24), 22000, (0.8, 0.86, 1.0))):
        ld = bpy.data.lights.new(name, "POINT")
        ld.energy, ld.color, ld.shadow_soft_size = energy, color, 6.0
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        bpy.context.scene.collection.objects.link(lo)
    boss = {}
    try:
        import piggy  # noqa: E402

        pa = piggy.piggy("sleep")
        po = C.finish(pa, col, glow=4.0)
        k = boss_scale(out)
        po.scale = (k,) * 3
        po.location = (BOSS[0], BOSS[1] + 2.0, 0.58)
        boss = {"tris": pa.stats["tris"], "scale": k}
    except Exception as e:  # noqa: BLE001
        print("BUILD boss failed:", repr(e)[:300], flush=True)
    picked = []
    try:
        import creatures  # noqa: E402

        names = [c[0] for c in creatures.CREATURES]
        for (x, y), rar in zip(A.SLOTS, SLOT_RARITY):
            i = next(j for j, c in enumerate(creatures.CREATURES) if c[3] == rar)
            for ob in creatures.build(i, col):
                ob.scale = (1.5, 1.5, 1.5)
                ob.location = (x, y, 0.95)
                ob.rotation_euler = (0, 0, math.radians(-20 if x > 0 else 20))
            picked.append(names[i])
    except Exception as e:  # noqa: BLE001
        print("BUILD creatures failed:", repr(e)[:300], flush=True)
    ov = C.finish(overlay(), col, glow=4.0)
    ov.hide_render = True
    res = (800, 450) if quick else (1600, 900)
    shots = {
        "player": ((0, -70, 11.5), (0, 6, 12.5), 24),
        "approach": ((-30, -42, 18), (2, 10, 9), 24),
        "lane": ((-LANE_X, -62, 7.5), (-LANE_X, 30, 6.0), 24),
    }
    for v in views:
        if v in shots:
            eye, tgt, lens = shots[v]
            C.shot(cam, os.path.join(out, f"arena7_{v}.png"), eye, tgt, lens, res)
    if "top" in views:
        ov.hide_render = False
        for ob in bpy.data.objects:
            if ob.name.startswith("Vault") or ob.name.startswith("Gates"):
                ob.hide_render = True  # сверху: задник и балки ворот не закрывают схему
        A.top_view(cam, os.path.join(out, "arena7_top.png"))
    total = sum(GAME.values())
    stats = {
        "scene_primitives": prims, "scene_primitives_total": sum(prims.values()),
        "scene_tris": tris, "scene_tris_total": sum(tris.values()), "boss": boss, "creatures_on_slots": picked,
        "game_parts_estimate": GAME, "game_parts_total": total, "game_parts_budget": 800,
        "game_parts_ok": total <= 800,
        "free_lanes": "ok" if not bad else [list(b) for b in bad[:30]],
        "exit_lanes": "ok" if not ext else [list(b) for b in ext[:30]],
        "walls_solid_le_24": "ok" if not wall else [list(b) for b in wall[:30]],
        "fight_circle_r34": "ok" if not fight else [list(b) for b in fight[:30]],
        "free_rects": [[round(v, 1) for v in r] for r in FREE],
    }
    with open(os.path.join(out, "arena7_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    print("STATS", json.dumps({k: stats[k] for k in ("scene_primitives_total", "scene_tris_total", "game_parts_total",
                                                     "free_lanes", "exit_lanes", "walls_solid_le_24",
                                                     "fight_circle_r34", "creatures_on_slots")},
                              ensure_ascii=False)[:1500], flush=True)
    print("DONE", flush=True)


main()
