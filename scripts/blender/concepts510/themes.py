"""Темы зон 5–10 для arenas.py: палитры, узор пола и площадки, задник и боковой декор (черновые концепты).

Ключи палитры, нужные каркасу: floor, cliff, cliffTop, path, plat, platEdge, slot. Декор выше 2 — только вне круга
боя r 34; задник — в полосе y 31…47 и |x| < 30 (пути к выходу идут по бокам, x ±40).
"""

import math

import ck as C
from arenas import BOSS, HL, PLAT_R, side_spots


def radial(a, key, n, r0, r1, z=0.6, w=0.5, phase=0.0):
    for i in range(n):
        t = phase + 2 * math.pi * i / n
        C.bar(a, key, (BOSS[0] + r0 * math.cos(t), BOSS[1] + r0 * math.sin(t), z),
              (BOSS[0] + r1 * math.cos(t), BOSS[1] + r1 * math.sin(t), z), w, 0.08, bevel=0)


def ring(a, key, r, w, z0=0.58, z1=0.66):
    a.frame(key, C.ngon(BOSS[0], BOSS[1], r, 32), w, z0, z1, axis="z")


def pine(a, x, y, h):
    a.prism("trunk", C.ngon(x, y, 0.7, 6), 0.3, h * 0.3)
    for i in range(3):
        z0 = h * 0.22 + i * h * 0.22
        r = h * 0.3 * (1 - i * 0.26)
        a.frustum("pine", (x - r, x + r, y - r, y + r), (x - r * 0.3, x + r * 0.3, y - r * 0.3, y + r * 0.3), z0,
                  z0 + h * 0.3)
    a.frustum("snow", (x - h * 0.08, x + h * 0.08, y - h * 0.08, y + h * 0.08), (x, x, y, y), h * 0.88, h * 1.05)


def rock(a, key, x, y, w, h, turn=0.0):
    a.prism(key, *C.octa((x, y), w, w * 0.8, 0.2, h, cut=w * 0.25), matrix=C.tilt((x, y, 0), "Z", turn))


# ── 5. Ледник ─────────────────────────────────────────────────────────────────────────────────────────────────
def ice_decor(mk):
    b = mk("Palace", ("palace",))
    C.blob(b, "palace", (0, 41, 0.3), 24, 6.5, 18, n=6, z0=0.3)
    for x, h in ((-20, 30), (0, 40), (20, 30)):
        b.prism("palaceD", C.ngon(x, 38.5, 3.4, 8), 0.3, h)
        b.frame("ice", C.ngon(x, 38.5, 3.7, 8), 0.5, h - 2, h - 1, axis="z")
        b.frustum("ice", (x - 3.6, x + 3.6, 34.9, 42.1), (x, x, 38.5, 38.5), h, h + 11)
    b.box("iceD", -5, 5, 34.0, 35.0, 0.3, 12)
    for x, z in ((-12, 22), (10, 26), (-4, 30), (14, 14), (-16, 12)):
        C.gem(b, "ice", (x, 34.6, z), 2.4, turn=x * 10)
    au = mk("Aurora")
    for k in range(12):
        x0 = -110 + k * 20
        C.bar(au, "neonG" if k % 2 else "neonP", (x0, 95, 55 + 8 * math.sin(k)), (x0 + 22, 95, 60 + 8 * math.cos(k)),
              5.0, 0.4, bevel=0)
    f = mk("Forest", ("pine",))
    for x, y, r in side_spots(22, 5):
        pine(f, x, y, 9 + 9 * r)
    d = mk("Drifts", ("snow", "ice"))
    for x, y, r in side_spots(14, 15, 40, 88):
        C.blob(d, "snow", (x, y, 0.3), 3 + 3 * r, 2.5 + 2 * r, 1.2 + r, n=3, z0=0.3)
    for x, y, r in side_spots(9, 25, 46, 84):
        for k in range(3):
            C.gem(d, "ice", (x + (k - 1) * 1.6, y, 1.5 + k * 0.4), 2.0 + r, turn=k * 40)
    for x in (-30, -18, 18, 30):
        C.blob(d, "snow", (x, -44, 0.3), 3.5, 2.2, 1.3, n=3, z0=0.3)


def ice_plat(a):
    radial(a, "iceD", 12, 6, PLAT_R - 2, w=0.35, phase=0.2)
    ring(a, "iceD", 14, 0.4)
    ring(a, "iceD", 22, 0.4)


def ice_path(a):
    for k in range(5):
        y = -46 + k * 3.2
        a.box("pathTile", -2, 2, y, y + 2, 0.42, 0.5)


# ── 6. Джунгли ────────────────────────────────────────────────────────────────────────────────────────────────
def jungle_decor(mk):
    t = mk("Temple", ("temple",))
    for k, (w, z0) in enumerate(((28, 0.3), (23, 7), (18, 13), (12, 19))):
        t.box("temple" if k % 2 == 0 else "templeD", -w, w, 32 + k * 1.6, 47, z0, z0 + 6.7)
    t.box("templeD", -5, 5, 30.5, 34, 0.3, 12)
    t.box("dark", -3.5, 3.5, 30.4, 31, 0.3, 9)
    C.gem(t, "jade", (0, 39, 28.5), 5)
    for x in (-24, -14, 14, 24):
        C.bar(t, "vine", (x, 31.8, 13), (x + 1, 31.6, 2), 0.6, 0.3)
    w = mk("Water")
    for s in (1, -1):
        w.box("water", s * 91.6, s * 92.4, 14, 24, 0.3, 30)
        w.prism("water", C.ngon(s * 82, 19, 8, 12), 0.3, 0.55)
        w.frame("stone", C.ngon(s * 82, 19, 8.6, 12), 1.0, 0.3, 1.0, axis="z")
    p = mk("Plants", ("leaf", "trunk"))
    for i, (x, y, r) in enumerate(side_spots(18, 6)):
        if i % 3 == 0:  # гигантский цветок
            C.tube(p, ["leaf"], [(x, y, 0.3), (x + 1, y, 6 + 4 * r)], 0.6)
            for k in range(5):
                tt = math.radians(k * 72)
                C.blob(p, "flower", (x + 1 + 2.4 * math.cos(tt), y + 2.4 * math.sin(tt), 7 + 4 * r), 2.0, 2.0, 0.7, n=2)
            C.blob(p, "petal", (x + 1, y, 7.3 + 4 * r), 1.3, 1.3, 0.8, n=2)
        elif i % 3 == 1:  # гриб
            p.prism("mushS", C.ngon(x, y, 1.0, 8), 0.3, 4 + 3 * r)
            C.blob(p, "mush", (x, y, 4 + 3 * r), 4, 4, 2, n=3, z0=4 + 3 * r)
        else:  # пальма
            C.tube(p, ["trunk"], [(x, y, 0.3), (x + 1.5, y, 9 + 5 * r), (x + 2, y, 14 + 5 * r)], 0.8)
            for k in range(6):
                tt = math.radians(k * 60)
                C.bar(p, "leaf", (x + 2, y, 14 + 5 * r), (x + 2 + 6 * math.cos(tt), y + 6 * math.sin(tt), 11 + 5 * r),
                      2.2, 0.3)
    for x in (-30, -20, 20, 30):
        C.blob(p, "leaf", (x, -44, 0.3), 3, 2.4, 2.2, n=3, z0=0.3)


def jungle_plat(a):
    for k in range(10):
        tt = k * 0.63
        r = 8 + 2.1 * k
        a.box("moss", BOSS[0] + r * math.cos(tt) - 1.5, BOSS[0] + r * math.cos(tt) + 1.5,
              BOSS[1] + r * math.sin(tt) - 1.2, BOSS[1] + r * math.sin(tt) + 1.2, 0.58, 0.68)
    ring(a, "stoneD", 18, 0.6)


def jungle_path(a):
    for k in range(4):
        y = -46 + k * 2.4
        a.box("pathD", -6, 6, y, y + 0.35, 0.42, 0.48)


# ── 7. Банк ───────────────────────────────────────────────────────────────────────────────────────────────────
def bank_decor(mk):
    v = mk("Vault", ("wall", "vault"))
    v.box("wall", -30, 30, 41, 47, 0.3, 36)
    v.box("gold", -31, 31, 40.4, 47, 34.5, 36.5)
    cz, cy, r = 18.0, 40.4, 15.0
    C.disc(v, "vault", 0, cz, r, cy - 1.6, cy, n=24, axis="y")
    v.frame("vaultD", C.ngon(0, cz, r + 1.2, 24), 2.2, cy - 2.0, cy, axis="y")
    for i in range(12):
        tt = math.radians(i * 30 + 15)
        C.disc(v, "gold", (r - 2) * math.cos(tt), cz + (r - 2) * math.sin(tt), 0.8, cy - 2.4, cy - 1.5, n=6, axis="y")
    for i in range(3):
        tt = math.radians(i * 60 + 15)
        C.bar(v, "gold", (-7 * math.cos(tt), cy - 2.6, cz - 7 * math.sin(tt)), (7 * math.cos(tt), cy - 2.6,
                                                                               cz + 7 * math.sin(tt)), 1.2, 1.2)
    C.disc(v, "gold", 0, cz, 2.2, cy - 3.6, cy - 1.6, axis="y")
    for s in (1, -1):
        for x in (22, 27):
            v.prism("wall", C.ngon(s * x, 38.5, 1.6, 8), 0.3, 34.5)
    g = mk("Gold", ("gold",))
    for i, (x, y, r) in enumerate(side_spots(14, 7)):
        if i % 2 == 0:  # пирамида слитков
            for row in range(3):
                for k in range(3 - row):
                    bx = x + (k - (2 - row) / 2) * 2.4
                    g.frustum("gold", (bx - 1.1, bx + 1.1, y - 0.6, y + 0.6), (bx - 0.8, bx + 0.8, y - 0.4, y + 0.4),
                              0.3 + row * 1.0, 1.3 + row * 1.0)
        else:  # колонна
            g.prism("wall", C.ngon(x, y, 2.0, 8), 0.3, 18)
            g.prism("gold", *C.octa((x, y), 5.0, 5.0, 18, 19.5, cut=1.2))
            g.prism("gold", *C.octa((x, y), 5.0, 5.0, 0.3, 1.5, cut=1.2))
    lz = mk("Lasers")
    for s in (1, -1):
        for k in range(4):
            y = -30 + k * 18
            C.bar(lz, "neonR", (s * 46, y, 1.2), (s * 88, y + 6, 1.2), 0.18, 0.18, bevel=0)
    for s in (1, -1):
        for k in range(5):
            y = -46 + k * 3
            lz.prism("gold", C.ngon(s * 7.5, y, 0.25, 6), 0.4, 3.2)
        C.bar(lz, "carpetD", (s * 7.5, -46, 2.9), (s * 7.5, -34, 2.9), 0.15, 0.15)


def bank_floor(a):
    for i in range(-5, 6):
        for j in range(-3, 3):
            if (i + j) % 2 == 0:
                a.box("marbleD", i * 16 - 8, i * 16 + 8, j * 16, j * 16 + 16, 0.3, 0.34)


def bank_plat(a):
    ring(a, "gold", 9, 0.6)
    ring(a, "gold", 20, 0.4)
    for i in range(8):
        tt = math.radians(i * 45)
        L = 18 if i % 2 == 0 else 11
        a.prism("gold", [(BOSS[0] + 1.6 * math.cos(tt + 1.57), BOSS[1] + 1.6 * math.sin(tt + 1.57)),
                         (BOSS[0] + L * math.cos(tt), BOSS[1] + L * math.sin(tt)),
                         (BOSS[0] + 1.6 * math.cos(tt - 1.57), BOSS[1] + 1.6 * math.sin(tt - 1.57))], 0.58, 0.64,
                bevel=0)


# ── 8. Вулкан ─────────────────────────────────────────────────────────────────────────────────────────────────
def volcano_decor(mk):
    v = mk("Volcano", ("basalt", "basaltL"))
    v.frustum("basalt", (-30, 30, 33, 47.5), (-8, 8, 40, 46), 0.3, 40)
    v.prism("neonLava", C.ngon(0, 43, 5.5, 8), 39.5, 40.2, bevel=0)
    for x0, x1 in ((-3, -14), (2, 9), (5, 18)):
        C.bar(v, "neonLava", (x0, 39.5, 39.5), (x1, 33.5, 0.8), 1.4, 0.5, bevel=0)
    sm = mk("Smoke", ("ash",))
    for k in range(5):
        C.blob(sm, "ash", (-2 + 3 * math.sin(k), 44, 46 + 6 * k), 6 + k, 5 + k, 3.5, n=3)
    c = mk("Columns", ("basaltL",))
    for i, (x, y, r) in enumerate(side_spots(16, 8)):
        for k in range(4):
            dx, dy = (k % 2) * 2.6 - 1.3, (k // 2) * 2.4 - 1.2
            h = 5 + 9 * r * (1 - 0.2 * k)
            c.prism("basaltL" if k % 2 else "basalt", C.ngon(x + dx, y + dy, 1.35, 6, phase=0), 0.3, h)
            c.prism("neonLavaY", C.ngon(x + dx, y + dy, 1.0, 6, phase=0), h, h + 0.15, bevel=0)
    pools = mk("Lava")
    for s in (1, -1):
        for y in (-30, 5, 30):
            pools.prism("neonLava", C.ngon(s * 64, y, 9, 10), 0.3, 0.4, bevel=0)
            for k in range(3):
                rock(pools, "crust", s * 64 + (-3, 2.5, 4.5)[k], y + (2.5, -2.0, 3.5)[k], 2.6 - k * 0.5, 0.7, turn=k * 30)
    for x in (-30, -20, 20, 30):
        rock(pools, "basalt", x, -44, 4, 2.2, turn=x)


def volcano_plat(a):
    for i in range(9):
        tt = 0.7 * i
        pts = [(BOSS[0] + (5 + 3 * k) * math.cos(tt + 0.25 * math.sin(k * 2)),
                BOSS[1] + (5 + 3 * k) * math.sin(tt + 0.25 * math.sin(k * 2)), 0.62) for k in range(8)]
        for p0, p1 in zip(pts, pts[1:]):
            C.bar(a, "neonLava", p0, p1, 0.4, 0.06, bevel=0)


def volcano_path(a):
    for s in (1, -1):
        a.box("neonLava", s * 6.0, s * 6.4, -HL - 6, BOSS[1] - PLAT_R + 1, 0.42, 0.46)


# ── 9. Космопорт ──────────────────────────────────────────────────────────────────────────────────────────────
def rocket(a, x, y, h):
    a.prism("rocket", C.ngon(x, y, 2.6, 8), 0.3, h)
    a.frustum("rocketR", (x - 2.6, x + 2.6, y - 2.6, y + 2.6), (x, x, y, y), h, h + 6)
    for k in range(4):
        tt = math.radians(k * 90 + 45)
        a.extrude("rocketR", [(0, 0.3), (3.6, 0.3), (2.6, 4.6), (0, 7)], -0.25, 0.25, axis="y",
                  matrix=C.tilt((x, y, 0), "Z", k * 90 + 45) @ C.Matrix.Translation((x + 2.0, y, 0)))
    C.disc(a, "glass", x, h * 0.7, 1.1, y - 2.8, y - 2.4, axis="y")
    a.prism("neonC", C.ngon(x, y, 2.0, 8), -0.2, 0.3, bevel=0)


def space_decor(mk):
    h = mk("Hangar", ("hangar",))
    h.box("hangar", -28, 28, 33, 47.5, 0.3, 24)
    h.frustum("hangarD", (-29, 29, 32.5, 47.5), (-20, 20, 36, 46), 24, 30)
    h.box("dark", -14, 14, 32.6, 33.2, 0.3, 17)
    h.frame("neonC", [(-14.6, 0.3), (14.6, 0.3), (14.6, 17.6), (-14.6, 17.6)], 0.6, 32.3, 32.6, axis="y")
    for k in range(5):
        h.box("neonY", -12 + k * 6, -9 + k * 6, 32.2, 32.6, 19.5, 20.5, bevel=0)
    r = mk("Rockets", ("rocket",))
    for s in (1, -1):
        rocket(r, s * 66, 22, 26)
        rocket(r, s * 78, -18, 20)
        C.bar(r, "metal", (s * 56, -34, 0.3), (s * 56, -34, 16), 0.7)
        r.frustum("panel", (s * 56 - 0.8, s * 56 + 0.8, -34.8, -33.2), (s * 56 - 4, s * 56 + 4, -38, -30), 16, 18.5)
    cr = mk("Cargo", ("panel",))
    for i, (x, y, q) in enumerate(side_spots(12, 9, 46, 60)):
        cr.box("panel" if i % 2 else "metalD", x - 2, x + 2, y - 2, y + 2, 0.3, 3.5 + 2 * q)
    st = mk("Stars")
    for i, (x, y, q) in enumerate(side_spots(40, 19, 0, 120, -20, 80)):
        C.gem(st, "neonW", (x * 1.4, 130 + y, 40 + 60 * q), 1.2 + q)


def space_floor(a):
    for i in range(-9, 10):
        a.box("metalD", i * 10 - 0.15, i * 10 + 0.15, -HL - 6, HL + 6, 0.3, 0.33, bevel=0)
    for j in range(-5, 6):
        a.box("metalD", -92, 92, j * 10 - 0.15, j * 10 + 0.15, 0.3, 0.33, bevel=0)


def space_plat(a):
    ring(a, "neonC", 12, 0.5, 0.58, 0.63)
    ring(a, "neonC", 24, 0.5, 0.58, 0.63)
    for k in range(4):
        tt = math.radians(k * 90 + 45)
        C.bar(a, "neonY", (BOSS[0] + 14 * math.cos(tt), BOSS[1] + 14 * math.sin(tt), 0.6),
              (BOSS[0] + 22 * math.cos(tt), BOSS[1] + 22 * math.sin(tt), 0.6), 1.2, 0.06, bevel=0)


def space_path(a):
    for k in range(4):
        y = -46 + k * 3
        a.prism("neonC", [(-2.5, y), (2.5, y), (0, y + 1.8)], 0.42, 0.46, bevel=0)


# ── 10. Замок ─────────────────────────────────────────────────────────────────────────────────────────────────
def tower(a, x, y, r, h, roof_h):
    a.prism("stone", C.ngon(x, y, r, 10), 0.3, h)
    for k in range(10):
        if k % 2 == 0:
            tt = 2 * math.pi * k / 10
            a.box("stoneD", x + r * math.cos(tt) - 0.9, x + r * math.cos(tt) + 0.9, y + r * math.sin(tt) - 0.9,
                  y + r * math.sin(tt) + 0.9, h, h + 1.6)
    a.frustum("roof", (x - r - 0.6, x + r + 0.6, y - r - 0.6, y + r + 0.6), (x, x, y, y), h + 1.6, h + 1.6 + roof_h)
    C.bar(a, "gold", (x, y, h + 1.6 + roof_h), (x, y, h + 4 + roof_h), 0.3)
    a.box("banner", x, x + 2.6, y - 0.1, y + 0.1, h + 2.4 + roof_h, h + 3.8 + roof_h, bevel=0)


def castle_decor(mk):
    k = mk("Keep", ("stone", "roof"))
    k.box("stone", -14, 14, 34, 47.5, 0.3, 40)
    for i in range(8):
        x = -13 + i * 3.7
        k.box("stoneD", x, x + 1.8, 33.4, 35.2, 40, 42)
    k.box("dark", -4, 4, 33.6, 34.2, 0.3, 10)
    k.frame("gold", [(-4.6, 0.3), (4.6, 0.3), (4.6, 10.6), (-4.6, 10.6)], 0.6, 33.3, 33.7, axis="y")
    for s in (1, -1):
        tower(k, s * 21, 40, 6, 32, 12)
        k.box("banner", s * 9 - 2.4, s * 9 + 2.4, 33.6, 33.9, 18, 32, bevel=0)
        C.gem(k, "gold", (s * 9, 33.4, 26), 2.2)
    w = mk("Walls", ("stone",))
    for s in (1, -1):
        w.box("stone", s * 91, s * 98, -HL - 6, HL + 6, 0.3, 20)
        for i in range(-12, 13, 2):
            w.box("stoneD", s * 90.6, s * 92.4, i * 4, i * 4 + 2, 20, 22)
        w.box("water", s * 82, s * 90.8, -HL - 6, HL + 6, 0.05, 0.25, bevel=0)
    w.box("wood", -90.8, -80, -4, 6, 0.25, 0.9)  # подъёмный мост сбоку, через ров, не поперёк коридора
    for s in (1, -1):
        tower(w, s * 70, -30, 5, 22, 9)
        tower(w, s * 72, 24, 5.5, 26, 10)
    t = mk("Treasure", ("gold",))
    for i, (x, y, q) in enumerate(side_spots(10, 10, 46, 64)):
        C.blob(t, "gold", (x, y, 0.3), 3 + 2 * q, 2.5 + 2 * q, 1.5 + q, n=3, z0=0.3)
        for kk in range(4):
            C.disc(t, "gold", x + 3 * math.cos(kk * 1.7), y + 3 * math.sin(kk * 1.7), 0.8, 0.3, 0.5)
        C.gem(t, ("ruby", "sapphire", "emerald")[i % 3], (x, y, 2.4 + q), 1.4, turn=i * 30)
    for s in (1, -1):
        for kk in range(4):
            y = -44 + kk * 3
            t.prism("gold", C.ngon(s * 7.5, y, 0.3, 6), 0.4, 3.0)


def castle_floor(a):
    for i in range(-5, 6):
        for j in range(-3, 3):
            if (i * 3 + j) % 4 == 0:
                a.box("cobbleD", i * 16 - 7, i * 16 + 7, j * 16 + 1, j * 16 + 15, 0.3, 0.34)


def castle_plat(a):
    for i in range(8):
        t0, t1 = math.radians(i * 45), math.radians(i * 45 + 45)
        a.prism(("red", "gold")[i % 2], [(BOSS[0], BOSS[1]), (BOSS[0] + 24 * math.cos(t0), BOSS[1] + 24 * math.sin(t0)),
                                         (BOSS[0] + 24 * math.cos(t1), BOSS[1] + 24 * math.sin(t1))], 0.58, 0.62,
                bevel=0)
    ring(a, "gold", 25, 1.0)


THEMES = {
    5: dict(
        pal={"snow": "F2F7FF", "cliff": "A9C4E0", "cliffTop": "F2F7FF", "path": "DCE8F4", "pathTile": "7FCBF0",
             "plat": "BDEFFF", "platEdge": "4FA8E0", "slot": "7FCBF0", "ice": "9EE3FA", "iceD": "4FA8E0",
             "palace": "C9F0FF", "palaceD": "7FC4EE", "pine": "2F7A5A", "trunk": "8F5A31", "neonG": "3DFFB0",
             "neonP": "B57CFF"},
        rings=("snow", "cliff", "plat", "palace", "pine"), floor="snow", cliff="cliff", cliffTop="cliffTop",
        path="path", plat="plat", platEdge="platEdge", slot="slot", decor=ice_decor, plat_fn=ice_plat,
        path_fn=ice_path, sky_top="2A3E7A", sky_bot="BFE6FF", exposure=-0.35, sun=2.6, glow=2.5),
    6: dict(
        pal={"grass": "5DBB4A", "cliff": "7A8B6A", "cliffTop": "4FA03E", "path": "B5793A", "pathD": "8F5A31",
             "plat": "A3AE9C", "platEdge": "4FA03E", "slot": "6E7B6E", "moss": "4FA03E", "stone": "9AA79A",
             "stoneD": "6E7B6E", "temple": "B4BBA0", "templeD": "8C957C", "jade": "2FD3A9", "vine": "2B8B47",
             "water": "7FD8FF", "leaf": "2E9E4E", "flower": "FF6FAE", "petal": "FFD23F", "mush": "E8384F",
             "mushS": "F4F1E6", "trunk": "8F5A31", "dark": "1E2418"},
        rings=("grass", "cliff", "plat", "temple", "templeD", "leaf", "trunk"), floor="grass", cliff="cliff",
        cliffTop="cliffTop", path="path", plat="plat", platEdge="platEdge", slot="slot", decor=jungle_decor,
        plat_fn=jungle_plat, path_fn=jungle_path, sky_top="3FA0E8", sky_bot="D8F2FF", exposure=0.0, sun=3.2),
    7: dict(
        pal={"marble": "F2F0EA", "marbleD": "C9CCD4", "cliff": "E6E1D6", "cliffTop": "F2C230", "path": "C8283A",
             "carpetD": "8A1626", "plat": "F2F0EA", "platEdge": "F2C230", "slot": "8A1626", "gold": "F2C230",
             "wall": "E6E1D6", "vault": "BFC8D6", "vaultD": "6F7F99", "neonR": "FF3048"},
        rings=("marble", "cliff", "wall", "vault", "gold"), floor="marble", cliff="cliff", cliffTop="cliffTop",
        path="path", plat="plat", platEdge="platEdge", slot="slot", decor=bank_decor, plat_fn=bank_plat,
        path_fn=bank_floor, sky_top="5A4A8E", sky_bot="FFD9A0", exposure=-0.25, sun=2.8,
        sun_color=(1.0, 0.9, 0.75)),
    8: dict(
        pal={"basalt": "3A3342", "basaltL": "5A5266", "ash": "8D8496", "cliff": "4A4352", "cliffTop": "5A5266",
             "path": "2A2530", "plat": "2E2938", "platEdge": "6E6577", "slot": "5A5266", "neonLava": "FF5A1F",
             "neonLavaY": "FFB33A", "crust": "2A2530"},
        rings=("basalt", "basaltL", "cliff", "plat", "ash"), floor="basalt", cliff="cliff", cliffTop="cliffTop",
        path="path", plat="plat", platEdge="platEdge", slot="slot", decor=volcano_decor, plat_fn=volcano_plat,
        path_fn=volcano_path, sky_top="2A0F14", sky_bot="C2502A", exposure=0.35, sun=2.4,
        sun_color=(1.0, 0.75, 0.55), glow=2.2),
    9: dict(
        pal={"metal": "8A97AA", "metalD": "4E5A70", "panel": "C9D2E3", "cliff": "3A3F55", "cliffTop": "5B6478",
             "path": "6F7F99", "plat": "4E5A70", "platEdge": "C9D2E3", "slot": "333A4A", "hangar": "8C96AA",
             "hangarD": "5B6478", "rocket": "F4F4F4", "rocketR": "E8384F", "glass": "9EE8FF", "neonC": "3FF0FF",
             "neonY": "FFE23F", "neonW": "FFFFFF", "dark": "141826"},
        rings=("metal", "cliff", "hangar", "rocket", "panel"), floor="metal", cliff="cliff", cliffTop="cliffTop",
        path="path", plat="plat", platEdge="platEdge", slot="slot", decor=space_decor, plat_fn=space_plat,
        path_fn=lambda a: (space_floor(a), space_path(a)), sky_top="0B1030", sky_bot="3A2F7A", exposure=0.25,
        sun=2.2, sun_color=(0.8, 0.85, 1.0), glow=2.5),
    10: dict(
        pal={"cobble": "9A9AA6", "cobbleD": "7C7C88", "cliff": "8A857A", "cliffTop": "5DBB4A", "path": "C8283A",
             "plat": "B8B3A8", "platEdge": "F2C230", "slot": "8A857A", "stone": "B8B3A8", "stoneD": "8A857A",
             "roof": "3B4FA0", "red": "C8283A", "gold": "F2C230", "banner": "C8283A", "water": "3F8FD6",
             "wood": "8F5A31", "ruby": "E0204A", "sapphire": "2F6BFF", "emerald": "22C77A", "dark": "1A1420"},
        rings=("cobble", "cliff", "stone", "roof", "plat"), floor="cobble", cliff="cliff", cliffTop="cliffTop",
        path="path", plat="plat", platEdge="platEdge", slot="slot", decor=castle_decor, plat_fn=castle_plat,
        path_fn=castle_floor, sky_top="4B3A8E", sky_bot="FFB27A", exposure=-0.1, sun=3.0,
        sun_color=(1.0, 0.85, 0.7)),
}
