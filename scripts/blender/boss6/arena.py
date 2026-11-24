"""Арена 6 «Джунгли» (концепт D64): заросшая терраса Королевы-мухоловки в рамке зоны 184 × 95 стадов.

Задумка: королева вросла в каменную террасу старого садового храма. Задник — ступенчатый храм-сад из зелёного камня
(вымышленные узоры: листья, спирали лиан, цветы — без религиозных символов и лиц), по уступам — висящие лианы и
цветы, в центре — арка-«трон» из корней с нефритовым самоцветом над головой королевы. Площадка — каменная терраса
с мхом и цветочной мозаикой; по краю — низкий бордюр из мха (ниже 0.6, перешагивается). По бокам: водопады со
скальных стен в пруды с кувшинками, гигантские цветы, грибы, папоротники, пальмы.

Свободный бег (замечание владельца 2026-11-24 по «Леднику»): игрок пробегает зону без обходов. Две прямые дорожки
шириной 14 (деревянный настил) по x = ±42 идут от входа до выхода насквозь; центральная — от входа к площадке;
перемычки шириной 10 соединяют площадку с боковыми дорожками. На дорожках и в полосе ±3 вокруг них нет ничего выше
0.6 — ни декора, ни табличек; пруды, деревья и цветы — только в боковых полосах |x| 54…88 и за храмом. Круг боя
r 34 свободен выше 2 (королева не ходит — поворот на месте, D64 п. 5).
Каркас (пол, обрывы, площадка, места существ, вид сверху) — scripts/blender/concepts510/arenas.py.

Запуск: blender --background --factory-startup --python scripts/blender/boss6/arena.py -- <репо>
Кадры: assets/concepts/bosses_5_10/boss6_v2/raw/arena6_{player,approach,top}.png и arena6_stats.json (вне git).
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

BOSS, HL, HW = A.BOSS, A.HL, A.HW
LANE_X, LANE_W = 42.0, 14.0  # боковые дорожки насквозь: вход → выход
LINK_W = 10.0  # перемычки площадка ↔ боковые дорожки
QUEEN_SCALE = 1.97  # 24 стада / рост модели в стойке (stats.json render.py: export_scale)

PAL = {
    "grass": "4FB548", "grassD": "3A9A3E", "cliff": "6F8F5E", "cliffTop": "4FB548", "path": "C08A4E", "pathD": "8F5A31",
    "plat": "B3BE9C", "platEdge": "5E8B4E", "slot": "7E9A72", "moss": "5BBF4A", "mossD": "3E9A3E",
    "stone": "9DAA94", "stoneD": "6E7B6E", "temple": "A8C29A", "templeD": "7E9C74", "templeL": "CFE3BF",
    "jade": "2FD3A9", "vine": "2B8B47", "vineL": "6FCF4A", "water": "5FD0FF", "waterL": "BFF3FF", "foam": "F2FBFF",
    "lily": "3FAE4A", "flower": "FF6FAE", "flowerD": "E0458C", "petal": "FFD23F", "petalD": "F2A81C", "petalW": "FFF6E0",
    "mush": "E8384F", "mushS": "F4F1E6", "trunk": "8F5A31", "trunkD": "6A4022", "leaf": "2E9E4E", "leafL": "7ED957",
    "root": "8F5A31", "gold": "F5B21C", "dark": "1E2418", "white": "FFFFFF", "neonJade": "3DFFC8",
}
RINGS = ("grass", "cliff", "plat", "temple", "templeD", "stone", "leaf", "trunk", "path", "lily", "root")
FREE = []  # прямоугольники дорожек (x0, x1, y0, y1) — проверка «ничего выше 0.6 на путях»


def mk(name):
    return A.art(name, PAL, RINGS)


def rnd(seed):
    g = A.rnd(seed)
    return lambda: next(g)


# ── Пути: настил насквозь, центральный путь, перемычки ────────────────────────────────────────────────────────
def lanes():
    """Деревянный настил: доски поперёк, тёмные зазоры; камни-ступени по центральному пути. Всё ниже 0.6."""
    p = mk("Lanes")
    for s in (1, -1):
        x0, x1 = s * LANE_X - LANE_W / 2, s * LANE_X + LANE_W / 2
        FREE.append((min(x0, x1), max(x0, x1), -HL - 6, HL + 6))
        p.box("pathD", x0, x1, -HL - 6, HL + 6, 0.28, 0.36, bevel=0)
        y = -HL - 6
        i = 0
        while y < HL + 6:
            p.box("path" if i % 3 else "pathD", x0 + 0.3, x1 - 0.3, y + 0.12, y + 2.3, 0.36, 0.46)
            y += 2.5
            i += 1
        for xr in (x0 + 0.15, x1 - 0.15):  # бортик-брус по краям (низкий, не мешает)
            p.box("trunk", xr - 0.25, xr + 0.25, -HL - 6, HL + 6, 0.3, 0.56)
    # перемычки от площадки к дорожкам — на уровне y босса
    for s in (1, -1):
        xa, xb = s * (A.PLAT_R - 1.0), s * (LANE_X - LANE_W / 2 + 0.5)
        FREE.append((min(xa, xb), max(xa, xb), BOSS[1] - LINK_W / 2, BOSS[1] + LINK_W / 2))
        y = BOSS[1] - LINK_W / 2
        x0, x1 = min(xa, xb), max(xa, xb)
        x = x0
        while x < x1:
            p.box("path", x + 0.1, min(x + 2.2, x1), y + 0.3, y + LINK_W - 0.3, 0.3, 0.44)
            x += 2.4
    FREE.append((-6.0, 6.0, -HL - 6, BOSS[1] - A.PLAT_R + 1))
    # центральный путь: каменные плиты-ступени в траве
    for k, y in enumerate(range(int(-HL - 4), int(BOSS[1] - A.PLAT_R), 4)):
        dx = 0.8 if k % 2 else -0.8
        p.box("stone", -4.4 + dx, 4.4 + dx, y + 0.3, y + 3.4, 0.36, 0.5)


def theme():
    return dict(pal=PAL, rings=RINGS, floor="grass", cliff="cliff", cliffTop="cliffTop", path="pathD", plat="plat",
                platEdge="platEdge", slot="slot", plat_fn=plat_mosaic, path_w=12.0)


def plat_mosaic(q):
    """Каменная терраса: мох пятнами, цветочная мозаика из плит, низкий бордюр из мха."""
    bx, by = BOSS
    q.frame("mossD", C.ngon(bx, by, 25.0, 32), 0.9, 0.58, 0.64, axis="z")
    q.frame("stoneD", C.ngon(bx, by, 13.0, 24), 0.7, 0.58, 0.64, axis="z")
    for i in range(8):  # лепестки-мозаика
        t = math.radians(22.5 + 45 * i)
        c, s_ = math.cos(t), math.sin(t)
        C.bar(q, "moss" if i % 2 else "mossD", (bx + 14.5 * c, by + 14.5 * s_, 0.61),
              (bx + 23.5 * c, by + 23.5 * s_, 0.61), 3.2, 0.06, bevel=0)
    g = rnd(61)
    for k in range(34):  # пятна мха
        t = g() * 2 * math.pi
        r = 6 + 24 * g()
        x, y = bx + r * math.cos(t), by + r * math.sin(t)
        q.box("moss" if k % 3 else "mossD", x - 1.0 - g(), x + 1.0 + g(), y - 0.8 - g(), y + 0.8 + g(), 0.58, 0.66)


def mossy_border():
    """Бордюр из мха и мелких цветов по краю площадки: высота ≤ 0.6 над полом, проходы к путям широкие."""
    b = mk("Border")
    R = A.PLAT_R + 1.4
    gaps = (-90, 0, 180)  # вход и обе перемычки
    for a in range(-180, 180, 6):
        if any(abs(((a - g + 180) % 360) - 180) < 14 for g in gaps):
            continue
        t = math.radians(a)
        x, y = BOSS[0] + R * math.cos(t), BOSS[1] + R * math.sin(t)
        b.prism("moss" if a % 12 else "mossD", C.ngon(x, y, 1.25, 6), 0.3, 0.88)
        if a % 18 == 0:
            b.prism("flower", C.ngon(x, y, 0.45, 5), 0.88, 1.08)


# ── Задник: храм-сад с аркой-троном ───────────────────────────────────────────────────────────────────────────
def temple():
    """Ступенчатый храм-сад: 4 уступа, на каждом — цветочные плиты и свисающие лианы; в центре — арка из корней
    с нефритовым самоцветом; по бокам — две башенки-вазы с цветами. Узоры — листья и спирали (вымышленные)."""
    t = mk("Temple")
    g = rnd(66)
    tiers = ((32, 0.3, 7.5, "temple"), (27, 7.4, 14.0, "templeD"), (21.5, 13.9, 20.0, "temple"),
             (15.5, 19.9, 25.5, "templeD"))
    for k, (w, z0, z1, key) in enumerate(tiers):
        y0 = 33.0 + k * 1.7
        t.box(key, -w, w, y0, HL + 0.5, z0, z1)
        t.box("templeL", -w - 0.15, w + 0.15, y0 - 0.25, y0 + 1.2, z1 - 0.55, z1 + 0.05)  # карниз уступа
        for x in range(int(-w) + 3, int(w) - 2, 6):  # узор: лист-ромб на фасаде
            if abs(x) < 7 and k < 3:
                continue
            zc = (z0 + z1) / 2
            m = C.tilt((x, y0 - 0.05, zc), "Y", 45)
            t.box("templeL", x - 0.9, x + 0.9, y0 - 0.2, y0 + 0.1, zc - 0.9, zc + 0.9, matrix=m)
            t.box("leaf", x - 0.35, x + 0.35, y0 - 0.32, y0 - 0.15, zc - 0.35, zc + 0.35, matrix=m, bevel=0)
        # мох шапкой по краю уступа (ступенчатые подушки), цветы в мху
        x = -w
        while x < w:
            ln = 2.5 + 2.5 * g()
            t.box("moss" if g() > 0.4 else "mossD", x, min(x + ln, w), y0 - 0.45, y0 + 2.2, z1 + 0.02, z1 + 0.5 + 0.4 * g())
            if g() > 0.55:
                t.prism("flower" if g() > 0.5 else "petal", C.ngon(x + ln / 2, y0 + 0.6, 0.5, 5), z1 + 0.5, z1 + 1.1)
            x += ln + 0.1
        for x in range(int(-w) + 2, int(w) - 1, 4):  # лианы с карниза, через одну длиннее, с листиками
            if abs(x) < 10 and k < 2:
                continue
            ln = 2.5 + 3.5 * g() + (2.0 if x % 8 == 0 else 0.0)
            C.bar(t, "vine", (x, y0 - 0.45, z1), (x + 0.3, y0 - 0.7, z1 - ln), 0.42, 0.32)
            for j in range(int(ln // 1.6)):
                zz = z1 - 1.0 - j * 1.6
                t.box("vineL", x - 0.6, x + 0.75, y0 - 0.85, y0 - 0.55, zz - 0.25, zz + 0.2, bevel=0,
                      matrix=C.tilt((x, y0 - 0.7, zz), "Y", 30 if j % 2 else -30))
    # арка-трон из корней за спиной королевы (над ней — нефрит)
    for s in (1, -1):
        C.bar(t, "root", (s * 9.5, 31.0, 0.3), (s * 8.5, 31.5, 13.0), 2.6, 2.6)
        C.bar(t, "root", (s * 8.5, 31.5, 12.6), (s * 2.0, 31.8, 17.2), 2.4, 2.4)
    t.box("templeD", -6.5, 6.5, 32.6, 33.2, 0.3, 13.0)  # ниша, задёрнутая завесой из лиан
    for i, x in enumerate([-5.4 + 1.2 * k for k in range(10)]):
        ln = 9.5 + 2.5 * ((i * 7) % 3) / 2
        C.bar(t, "vine" if i % 2 else "vineL", (x, 32.3, 12.8), (x + 0.2, 32.2, 12.8 - ln), 0.5, 0.35)
        t.prism("flower" if i % 3 == 0 else "petal", C.ngon(x + 0.2, 32.1, 0.45, 5), 12.8 - ln * 0.6 - 0.3,
                12.8 - ln * 0.6 + 0.3, axis="z")
    C.gem(t, "neonJade", (0, 31.6, 18.4), 3.6)
    t.frame("gold", C.ngon(0, 18.4, 2.4, 8), 0.5, 31.4, 32.2, axis="y")
    # навершие: каменная чаша с огромным цветком и нефритовым бутоном
    t.box("temple", -9, 9, 39.5, 46.5, 25.4, 27.0)
    t.box("templeL", -9.3, 9.3, 39.2, 46.8, 27.0, 27.5)
    flower(t, 0, 43.0, 27.5, 5.0, g)
    # башенки-вазы по краям храма с огромными цветами
    for s in (1, -1):
        x = s * 29.0
        t.prism("templeD", C.ngon(x, 37.5, 3.2, 8), 7.4, 10.6)
        t.prism("temple", C.ngon(x, 37.5, 3.8, 8), 10.6, 11.6)
        flower(t, x, 37.5, 11.6, 3.4, g)
    # ступени к арке
    for i in range(3):
        t.box("templeL", -8 + i, 8 - i, 29.0 + i * 1.0, 33.0, 0.3, 0.75 + i * 0.4)


def flower(a, x, y, z, r, g, key="flower", core="petal"):
    """Гигантский цветок: 6 лепестков-брусков веером, жёлтая серединка ступенькой."""
    for k in range(6):
        t = math.radians(k * 60 + 30 * g())
        px, py = x + r * 0.8 * math.cos(t), y + r * 0.8 * math.sin(t)
        m = C.tilt((px, py, z + 0.3), "Z", math.degrees(t))
        a.box(key if k % 2 else key + "D", px - r * 0.55, px + r * 0.55, py - r * 0.3, py + r * 0.3, z, z + 0.5,
              matrix=m @ C.tilt((px, py, z), "Y", -18))
    a.prism(core, C.ngon(x, y, r * 0.38, 8), z, z + 0.9)
    a.prism("gold", C.ngon(x, y, r * 0.2, 6), z + 0.9, z + 1.2)


# ── Бока: скалы, водопады, пруды, цветы, грибы, пальмы ────────────────────────────────────────────────────────
def waterfalls():
    """Водопад с уступа скалы в пруд с кувшинками: скальная рама из глыб с мхом, широкая струя, пена, брызги."""
    w = mk("Water")
    for s in (1, -1):
        y = 18.0
        x_face = s * 84.5
        # скальная рама: стопки глыб справа и слева от струи и сверху (уступы), мох на верхушках
        for yy, h in ((y - 9.0, 19.0), (y + 9.0, 18.0), (y - 13.0, 13.0), (y + 13.5, 12.0)):
            for k, (r, z0, z1) in enumerate(((5.2, 0.3, h * 0.45), (4.4, h * 0.45 - 0.2, h * 0.8), (3.2, h * 0.8 - 0.2, h))):
                w.prism("stone" if k % 2 == 0 else "stoneD", C.ngon(s * 88.0, yy, r, 7), z0, z1)
            w.prism("moss", C.ngon(s * 88.0, yy, 3.4, 7), h - 0.1, h + 0.6)
        w.box("stoneD", s * 86.0, s * HW, y - 6.5, y + 6.5, 0.3, 16.0)  # скала за струёй
        w.box("moss", s * 85.6, s * HW, y - 6.8, y + 6.8, 16.0, 16.8)
        w.box("water", x_face - s * 0.2, x_face + s * 1.3, y - 5.5, y + 5.5, 0.5, 16.4, bevel=0)  # струя
        for k in range(7):  # полосы пены по струе
            yy = y - 4.5 + 1.5 * k
            w.box("foam", x_face - s * 0.35, x_face - s * 0.2, yy - 0.25, yy + 0.25, 1.0 + (k % 3) * 1.4,
                  15.8 - (k % 2) * 2.0, bevel=0)
        for k in range(6):  # лианы с уступа поверх струи
            yy = y - 6 + 2.4 * k
            C.bar(w, "vine", (s * 85.8, yy, 16.4), (s * 85.4, yy + 0.3, 16.4 - (3 + (k % 3) * 2.5)), 0.4, 0.3)
        # пруд: каменный край ступенькой, вода, пена у падения, кувшинки с цветами
        cx, cy = s * 72.0, y
        w.prism("stoneD", C.ngon(cx, cy, 13.6, 16), 0.3, 0.7)
        w.prism("stone", C.ngon(cx, cy, 12.9, 16), 0.3, 1.0)
        w.prism("water", C.ngon(cx, cy, 12.1, 16), 0.3, 1.08)
        w.prism("waterL", C.ngon(cx + s * 9.8, cy, 3.4, 10), 1.08, 1.14)
        for k in range(5):
            t = 2 * math.pi * k / 5
            w.prism("foam", C.ngon(cx + s * 10.0 + 1.6 * math.cos(t), cy + 2.4 * math.sin(t), 0.7, 6), 1.1, 1.5)
        g = rnd(70 + (s > 0))
        for k in range(9):
            t = 2 * math.pi * k / 9 + g()
            r = 3 + 6 * g()
            lx, ly = cx - s * 1.5 + r * math.cos(t), cy + r * math.sin(t)
            w.prism("lily", C.ngon(lx, ly, 1.4 + 0.8 * g(), 9), 1.1, 1.22)
            if k % 2 == 0:
                for j in range(5):
                    tt = math.radians(j * 72)
                    w.prism("petalW" if k % 4 else "flower",
                            C.ngon(lx + 0.45 * math.cos(tt), ly + 0.45 * math.sin(tt), 0.35, 5), 1.22, 1.6)
                w.prism("petal", C.ngon(lx, ly, 0.3, 6), 1.22, 1.7)


def tree(d, x, y, h, g):
    """Дерево джунглей: ствол с корнями-досками, крона — три ступенчатых яруса, лианы с кроны."""
    for k in range(4):
        t = math.radians(45 + 90 * k + 20 * g())
        C.bar(d, "trunkD", (x + 2.2 * math.cos(t), y + 2.2 * math.sin(t), 0.3), (x, y, 2.6), 0.9, 1.4)
    C.bar(d, "trunk", (x, y, 0.3), (x + 0.6, y, h * 0.75), 1.8, 1.8)
    for k, (r, dz, key) in enumerate(((7.0, 0.0, "leaf"), (5.6, 1.5, "grassD"), (3.8, 2.8, "leafL"))):
        d.prism(key, C.ngon(x + 0.6, y, r, 9), h * 0.72 + dz, h * 0.72 + dz + 1.7)
    for k in range(3):
        t = math.radians(120 * k + 40)
        px, py = x + 0.6 + 5.6 * math.cos(t), y + 5.6 * math.sin(t)
        C.bar(d, "vine", (px, py, h * 0.72), (px + 0.3, py, h * 0.72 - 4 - 2 * g()), 0.35, 0.3)


def monstera(d, x, y, g):
    """Куст-монстера: 6 огромных листьев веером от земли, у каждого — светлая жилка."""
    for k in range(6):
        t = math.radians(k * 60 + 25 * g())
        tip = (x + 4.6 * math.cos(t), y + 4.6 * math.sin(t), 2.4 + 1.5 * g())
        C.bar(d, "leaf" if k % 2 else "grassD", (x, y, 0.5), tip, 2.4, 0.3)
        C.bar(d, "leafL", (x, y, 0.82), (tip[0] * 0.9 + x * 0.1, tip[1] * 0.9 + y * 0.1, tip[2] + 0.25), 0.3, 0.12,
              bevel=0)


def side_decor():
    """Джунгли по бокам — только в полосах |x| 54…90 и вокруг храма; дорожки и перемычки пусты (check_free)."""
    d = mk("Plants")
    g = rnd(9)
    spots = []
    for x, y, kk in A.side_spots(90, 11, x0=55, x1=84):
        if abs(abs(x) - 72) < 15.5 and abs(y - 18) < 15.5:
            continue  # пруд
        if any(math.hypot(x - px, y - py) < 7.5 for px, py in spots):
            continue
        spots.append((x, y))
        if kk < 0.2:  # гигантский цветок на стебле
            h = 7 + 5 * g()
            C.bar(d, "leaf", (x, y, 0.3), (x + 0.6, y, h), 1.0, 1.0)
            for s in (1, -1):
                C.bar(d, "leafL", (x + 0.3, y, h * 0.45), (x + s * 3.2, y - 0.6, h * 0.6), 1.6, 0.3)
            flower(d, x + 0.6, y, h, 3.0 + g(), g, key="flower" if g() > 0.5 else "petal", core="petalW")
        elif kk < 0.35:  # гриб-зонтик
            h = 4 + 3 * g()
            d.prism("mushS", C.ngon(x, y, 1.1, 8), 0.3, h)
            for k, (r, z0) in enumerate(((4.2, h), (3.4, h + 0.8), (2.2, h + 1.5))):
                d.prism("mush" if k != 1 else "white", C.ngon(x, y, r, 10), z0, z0 + 0.85)
            for k in range(4):
                t = math.radians(45 + 90 * k)
                d.prism("white", C.ngon(x + 2.6 * math.cos(t), y + 2.6 * math.sin(t), 0.5, 6), h + 0.8, h + 0.95)
        elif kk < 0.55:  # дерево с кроной
            tree(d, x, y, 13 + 6 * g(), g)
        elif kk < 0.7:  # пальма
            h = 11 + 5 * g()
            C.bar(d, "trunk", (x, y, 0.3), (x + 1.2, y, h * 0.55), 1.2, 1.2)
            C.bar(d, "trunkD", (x + 1.2, y, h * 0.55 - 0.3), (x + 1.8, y, h), 1.0, 1.0)
            for k in range(7):
                t = math.radians(k * 51 + 20)
                C.bar(d, "leaf" if k % 2 else "leafL", (x + 1.8, y, h),
                      (x + 1.8 + 6.5 * math.cos(t), y + 6.5 * math.sin(t), h - 2.8), 2.4, 0.3)
            for k in range(3):  # кокосы
                d.prism("trunkD", C.ngon(x + 1.8 + 0.7 * math.cos(k * 2.1), y + 0.7 * math.sin(k * 2.1), 0.45, 6),
                        h - 1.0, h - 0.3)
        else:  # монстера
            monstera(d, x, y, g)
    # заросли у скальных стен: стена кустов и деревьев ярусами (фон коридора, не дорожки)
    for s in (1, -1):
        y = -52.0
        i = 0
        while y < 52:
            r = 3 + 2 * g()
            if not (abs(y - 18) < 14):  # у водопада — скалы
                d.prism("leaf" if i % 2 else "grassD", C.ngon(s * 89.5, y, r, 8), 0.3, 3 + 3 * g())
                d.prism("leafL", C.ngon(s * 89.5, y, r * 0.6, 8), 3.0, 4.2 + 2 * g())
                if i % 3 == 0:
                    tree(d, s * 91.0, y, 16 + 6 * g(), g)
            y += r * 1.5
            i += 1
    # клумбы у входа и у храма — плоские (≤ 0.6), между путями, разнообразят траву
    gb = rnd(33)
    for x0, x1, y0, y1 in ((8, 33, -47, -38), (-33, -8, -47, -38), (28, 33, 26, 46), (-33, -28, 26, 46)):
        for k in range(10):
            x, y = x0 + (x1 - x0) * gb(), y0 + (y1 - y0) * gb()
            d.prism("grassD", C.ngon(x, y, 1.6 + gb(), 7), 0.3, 0.42)
            for j in range(3):
                d.prism("flower" if (k + j) % 3 else "petal", C.ngon(x + 0.8 * math.cos(j * 2.1),
                                                                    y + 0.8 * math.sin(j * 2.1), 0.35, 5), 0.42, 0.58)
    # пятна тёмной травы и плиты-камни по всему полу (текстура, плоско)
    gp = rnd(44)
    for k in range(70):
        x, y = (gp() * 2 - 1) * 88, (gp() * 2 - 1) * 46
        if math.hypot(x - BOSS[0], y - BOSS[1]) < A.PLAT_R + 3:
            continue
        if any(x0 - 1 < x < x1 + 1 and y0 - 1 < y < y1 + 1 for x0, x1, y0, y1 in FREE):
            continue
        d.prism("grassD", C.ngon(x, y, 2 + 3 * gp(), 7), 0.3, 0.36)


def signs():
    """Указатели «В БАНК» — на столбе у бровки, сбоку от дорожки (не на ней)."""
    s = mk("Signs")
    for sx in (1, -1):
        x = sx * (LANE_X + LANE_W / 2 + 2.5)
        s.box("trunk", x - 0.3, x + 0.3, 38.0, 38.6, 0.3, 4.0)
        s.box("path", x - 2.6, x + 2.6, 37.9, 38.2, 3.0, 4.4)  # табличка (текст — в игре, на концепте без надписи)


def check_free(objs_arts):
    """Проверка свободного бега: ни одной детали выше 0.6 над полом в прямоугольниках дорожек (кроме самих путей)."""
    bad = []
    for a in objs_arts:
        if a.name in ("Lanes", "Ground", "Platform"):
            continue
        for bm, _key, _solid, _grp in a.parts:
            xs = [v.co.x for v in bm.verts]
            ys = [v.co.y for v in bm.verts]
            zs = [v.co.z for v in bm.verts]
            if max(zs) <= 0.6 + 0.3:
                continue
            for x0, x1, y0, y1 in FREE:
                if min(xs) < x1 - 0.5 and max(xs) > x0 + 0.5 and min(ys) < y1 - 0.5 and max(ys) > y0 + 0.5:
                    bad.append((a.name, round(min(xs), 1), round(max(xs), 1), round(min(ys), 1), round(max(ys), 1),
                                round(max(zs), 1)))
                    break
    return bad


def overlay():
    """Схема сверху: круг боя r 34 (белый), места существ (красные), свободные дорожки (зелёные контуры)."""
    o = C.new_art("Overlay")
    o.paint("neonW", "FFFFFF")
    o.paint("neonR", "FF3048")
    o.paint("neonG", "3DFF7A")
    for i in range(36):
        if i % 2 == 0:
            t0, t1 = math.radians(i * 10), math.radians(i * 10 + 10)
            C.bar(o, "neonW", (BOSS[0] + A.FIGHT_R * math.cos(t0), BOSS[1] + A.FIGHT_R * math.sin(t0), 3.0),
                  (BOSS[0] + A.FIGHT_R * math.cos(t1), BOSS[1] + A.FIGHT_R * math.sin(t1), 3.0), 0.7, 0.1, bevel=0)
    for x, y in A.SLOTS:
        o.frame("neonR", C.ngon(x, y, 3.6, 12), 0.6, 3.0, 3.1, axis="z")
    for x0, x1, y0, y1 in FREE:
        y0, y1 = max(y0, -HL), min(y1, HL)
        o.frame("neonG", [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 0.6, 3.0, 3.1, axis="z")
    return o


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    repo = os.path.abspath(argv[0])
    out = os.path.join(repo, "assets", "concepts", "bosses_5_10", "boss6_v2", "raw")
    os.makedirs(out, exist_ok=True)
    import flytrap  # noqa: E402

    A.ARTS.clear()
    A.EXIT_PATHS[:] = []  # свои пути: боковые дорожки насквозь (lanes), без диагоналей каркаса
    A.ENTRY_PATHS[:] = []
    col = C.reset_scene()
    cam = C.outdoor("2F86D8", "9AD6F5", (1.0, 0.95, 0.85), 3.6, (-48, 0, 30), 0.9)
    bpy.context.scene.view_settings.exposure = -0.1
    A.frame_zone(theme(), col)
    lanes()
    mossy_border()
    temple()
    waterfalls()
    side_decor()
    signs()
    bad = check_free(A.ARTS)
    print("FREE_LANES", "ok" if not bad else bad[:12], flush=True)
    for a in A.ARTS:
        C.finish(a, col, glow=3.0)
    qa = flytrap.flytrap("sleep")
    qo = C.finish(qa, col, glow=4.0)
    qo.scale = (QUEEN_SCALE,) * 3
    qo.location = (BOSS[0], BOSS[1], 0.58)
    try:
        import creatures  # noqa: E402  (эскизы коллекции: по одному на место — C, R, E, L)

        for (x, y), idx in zip(A.SLOTS, (0, 4, 7, 9)):
            for ob in creatures.build(idx, col):
                ob.scale = (1.5, 1.5, 1.5)
                ob.location = (x, y, 0.95)
                ob.rotation_euler = (0, 0, math.radians(-20 if x > 0 else 20))
    except ImportError:
        pass
    ov = C.finish(overlay(), col, glow=4.0)
    ov.hide_render = True
    C.shot(cam, os.path.join(out, "arena6_player.png"), (0, -66, 14), (0, -2, 8), 22, (1600, 900))
    C.shot(cam, os.path.join(out, "arena6_approach.png"), (-34, -40, 22), (0, 8, 6), 24, (1600, 900))
    C.shot(cam, os.path.join(out, "arena6_lane.png"), (-42, -60, 9), (-42, 30, 2), 24, (1600, 900))
    ov.hide_render = False
    A.top_view(cam, os.path.join(out, "arena6_top.png"))
    stats = {"primitives": {a.name: len(a.parts) for a in A.ARTS}, "total": sum(len(a.parts) for a in A.ARTS),
             "free_lanes": "ok" if not bad else [list(b) for b in bad]}
    with open(os.path.join(out, "arena6_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    print("STATS", json.dumps(stats, ensure_ascii=False), flush=True)


main()
