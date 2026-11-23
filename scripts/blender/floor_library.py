"""Этаж «Зеркало-портал» музея-небоскрёба (четвёртая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — библиотека академии магии. Снаружи — тёмно-синий камень с золотыми поясами и пилястрами-
книжными шкафами, высокие стрельчатые окна со звёздным витражом, посередине фасада — огромная резная рама-зеркало,
в которой закручен светящийся портал (кольца фиолетового и бирюзового), вокруг рамы парят раскрытые книги и
звёзды; по углам — башенки-шпили с хрустальными шарами; парапет с полумесяцами; бока — круглые окна-розы и парящие
книги; сзади — балкон с телескопом-глобусом. Внутри — читальный зал: высокие книжные шкафы по стенам с
лестницами на колёсах, парящие книги и свечи, большой глобус на подставке, столы для чтения с лампами, на стенах —
малые зеркала-порталы, на полу — магический круг из рун; экспонат — на ступенчатом золотом помосте внутри круга.
Запуск: blender --background --factory-startup --python scripts/blender/floor_library.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, ring_y, rng, slab, taper  # noqa: E402

BLUE, BLUE2, BLUE3, NIGHT, GOLD, GOLD2 = "2E3A8A", "1E2866", "4A5AB0", "14183A", "F2C230", "C8901A"
WOOD, WOOD2, WOOD3, PAPER, PAPER2, CANDLE = "7A4A2A", "5A3418", "9A6238", "F8F0DA", "E8D8B4", "FFF4D8"
PORT1, PORT2, PORT3, STARC, CRYSTAL = "9A4AFF", "3AE8E0", "E07AFF", "FFF2B0", "B8E8FF"
CARPET, CARPET2, BOOKS = "5A1E4A", "3A123A", ("C83A3A", "2E7A5A", "2E4AAA", "C8902A", "7A3A9A", "E8E0C8", "3A3A4A")

F = B.Floor("PR", "PortalMirror", quiet=(CARPET, CARPET2, NIGHT), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def portal(p, g, axis, fixed, out, a, y, r, depth):
    """Зеркало-портал на стене: резная рама (овал из сегментов с зубцами), светящиеся кольца, спираль."""
    pr = p.prism_xy if axis == "z" else p.prism_zy
    gr = g.prism_xy if axis == "z" else g.prism_zy
    fr = p.frame_xy if axis == "z" else p.frame_zy

    def oval(rx, ry, n=20):
        return [(a + rx * math.cos(2 * math.pi * k / n), y + ry * math.sin(2 * math.pi * k / n)) for k in range(n)]

    fr(oval(r * 0.82, r * 1.12), oval(r * 0.66, r * 0.96), *sorted((fixed + out * 0.6, fixed + out * depth)), GOLD)
    fr(oval(r * 0.9, r * 1.2, 20), oval(r * 0.82, r * 1.12, 20), *sorted((fixed + out * 0.6, fixed + out * (depth - 0.3))), GOLD2)
    for k in range(10):  # резные зубцы рамы
        t = 2 * math.pi * k / 10
        cx, cy = a + r * 0.95 * math.cos(t), y + r * 1.26 * math.sin(t)
        pr(K.octa(cx, cy, r * 0.12, r * 0.12, r * 0.05), *sorted((fixed + out * 0.6, fixed + out * (depth - 0.1))), GOLD)
    pr([(a - r * 0.3, y + r * 1.2), (a + r * 0.3, y + r * 1.2), (a, y + r * 1.62)], *sorted((fixed + out * 0.6, fixed + out * depth)), GOLD)
    for k, (s, col) in enumerate(((0.66, NIGHT), (0.56, PORT1), (0.42, PORT3), (0.28, PORT2), (0.14, "FFFFFF"))):
        gr(oval(r * s, r * s * 1.45), *sorted((fixed + out * (0.7 + 0.12 * k), fixed + out * (0.8 + 0.12 * k))), col)
    for k in range(6):  # завиток спирали
        t0 = 2 * math.pi * k / 6
        rr = r * (0.2 + 0.07 * k)
        gr([(a + rr * math.cos(t0), y + rr * 1.45 * math.sin(t0)), (a + (rr + 0.12 * r) * math.cos(t0 + 0.6),
            y + (rr + 0.12 * r) * 1.45 * math.sin(t0 + 0.6)), (a + rr * math.cos(t0 + 0.9), y + rr * 1.45 * math.sin(t0 + 0.9))],
           *sorted((fixed + out * 1.32, fixed + out * 1.38)), PORT2 if k % 2 else STARC)


def book(p, x, y, z, s, col, open_=True, yaw=0.0):
    """Парящая книга: раскрытая — две страницы домиком и обложка; закрытая — брусок."""
    c, sn = math.cos(yaw), math.sin(yaw)

    def rot(dx, dz):
        return (x + dx * c - dz * sn, z + dx * sn + dz * c)

    if open_:
        for e in (-1, 1):
            q0, q1 = rot(0.0, -0.5 * s), rot(0.0, 0.5 * s)
            q2, q3 = rot(e * 0.9 * s, 0.5 * s), rot(e * 0.9 * s, -0.5 * s)
            p.loft([(q0[0], y, q0[1]), (q1[0], y, q1[1]), (q2[0], y + 0.3 * s, q2[1]), (q3[0], y + 0.3 * s, q3[1])],
                   [(q0[0], y + 0.1, q0[1]), (q1[0], y + 0.1, q1[1]), (q2[0], y + 0.42 * s, q2[1]), (q3[0], y + 0.42 * s, q3[1])],
                   PAPER)
            p.loft([(q0[0], y - 0.08, q0[1]), (q1[0], y - 0.08, q1[1]), (q2[0], y + 0.22 * s, q2[1]), (q3[0], y + 0.22 * s, q3[1])],
                   [(q0[0], y, q0[1]), (q1[0], y, q1[1]), (q2[0], y + 0.3 * s, q2[1]), (q3[0], y + 0.3 * s, q3[1])], col)
    else:
        p.box(x - 0.7 * s, x + 0.7 * s, y, y + 0.3 * s, z - 0.5 * s, z + 0.5 * s, col)
        p.box(x - 0.64 * s, x + 0.7 * s, y + 0.04, y + 0.26 * s, z - 0.44 * s, z + 0.44 * s, PAPER2)


def bookcase(p, axis, fixed, out, a0, a1, y0, y1, depth, rows, seed):
    """Книжный шкаф на стене: корпус, полки, корешки (крупные группы)."""
    slab(p, axis, fixed, out, 0.6, a0, a1, y0, y1, WOOD2)  # задняя стенка
    for e in (a0, a1 - 0.3):  # боковины
        slab(p, axis, fixed, out, depth, e, e + 0.3, y0, y1, WOOD2)
    slab(p, axis, fixed, out, depth, a0, a1, y1 - 0.4, y1, WOOD3)
    h = (y1 - y0 - 0.6) / rows
    for r in range(rows):
        yb = y0 + 0.3 + h * r
        slab(p, axis, fixed, out, depth + 0.1, a0, a1, yb - 0.15, yb, WOOD3)
        n = max(1, int((a1 - a0 - 0.4) / 1.0))
        p.noroute = getattr(p, "noroute", 0) + 1  # корешки — гладкие накладки, не здание и не вещь
        for k in range(n):
            if rng(seed, r, k) < 0.1:
                continue
            b0 = a0 + 0.2 + (a1 - a0 - 0.4) * k / n
            lo, hi = sorted((fixed + out * 0.6, fixed + out * (depth - 0.1)))
            b1 = b0 + (a1 - a0 - 0.4) / n - 0.06
            yt = yb + h * (0.62 + 0.3 * rng(k, r, seed))
            col = BOOKS[int(rng(k, r, seed, 2) * len(BOOKS))]
            if axis == "z":
                p.box(b0 + 0.06, b1, yb, yt, lo, hi, col)
            else:
                p.box(lo, hi, yb, yt, b0 + 0.06, b1, col)
        p.noroute -= 1


def candle(p, g, x, y, z, h=0.8):
    p.prism_xz(K.ngon(x, z, 0.16, 6), y, y + h, CANDLE)
    g.prism_xz(K.octa(x, z, 0.1, 0.1, 0.04), y + h, y + h + 0.3, "FFC050")


def star_shape(g, axis, fixed, out, a, y, r, d0, d1, color):
    pts = [(a + (r if k % 2 == 0 else r * 0.42) * math.cos(math.pi / 2 + math.pi * k / 5),
            y + (r if k % 2 == 0 else r * 0.42) * math.sin(math.pi / 2 + math.pi * k / 5)) for k in range(10)]
    (g.prism_xy if axis == "z" else g.prism_zy)(pts, *sorted((fixed + out * d0, fixed + out * d1)), color)


# ══ ФАСАД: библиотека академии ════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, BLUE, BLUE, NIGHT)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FR, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, 0.0, BLUE2)
    slab(FR, axis, fixed, out, 1.88, -half - 0.6, half + 0.6, 0.0, 1.4, BLUE3)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.4, 16.0, BLUE)
    slab(FS, axis, fixed, out, 1.95, -half - 0.6, half + 0.6, 1.2, 1.5, GOLD)
    slab(FR, axis, fixed, out, 1.88, -half - 0.8, half + 0.8, 16.0, 17.2, BLUE3)
    slab(FS, axis, fixed, out, 2.0, -half - 0.8, half + 0.8, 16.0, 16.3, GOLD)
    slab(FR, axis, fixed, out, 0.88, -half, half, 17.2, 18.9, BLUE2)
    lo, hi = sorted((fixed + out * 0.88, fixed + out * 1.4))
    for k in range(int(2 * half // 4.0) + 1):  # парапет: полумесяцы
        a = -half + 2.0 + 4.0 * k
        if a > half - 1.0:
            break
        moon = [(a + 0.9 * math.cos(math.radians(t)), 18.0 + 0.9 * math.sin(math.radians(t))) for t in range(60, 301, 40)]
        moon += [(a + 0.35 + 0.7 * math.cos(math.radians(t)), 18.0 + 0.7 * math.sin(math.radians(t))) for t in range(250, 109, -35)]
        (FS.prism_xy if axis == "z" else FS.prism_zy)(moon, lo, hi, GOLD)
    if fi == 0:
        continue
    for k in range(int(2 * half // 8.0)):  # высокие стрельчатые окна со звёздным витражом
        a = -half + 4.0 + 8.0 * k
        if axis == "x" and abs(a) < 3.0:
            continue
        pts = [(a - 1.6, 3.0), (a + 1.6, 3.0), (a + 1.6, 11.0), (a + 0.8, 12.8), (a, 13.6), (a - 0.8, 12.8), (a - 1.6, 11.0)]
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 1.5))
        fr = FS.frame_xy if axis == "z" else FS.frame_zy
        fr([(px_ + (0.4 if px_ > a else -0.4 if px_ < a else 0.0), py + (0.5 if py > 3.0 else -0.4)) for px_, py in pts], pts, d0, d1, GOLD2)
        (FG.prism_xy if axis == "z" else FG.prism_zy)(pts, *sorted((fixed + out * 0.9, fixed + out * 0.94)), "3A4AC8")
        for m in range(3):
            star_shape(FG, axis, fixed, out, a + (m - 1) * 0.8, 5.0 + 2.6 * m, 0.5, 0.94, 0.98, STARC)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))

# перед: шкафы-пилястры по сторонам, огромная рама-портал посередине, парящие книги и звёзды, двери
for s in (-1, 1):
    for a0, a1 in ((s * 8.6, s * 12.6), (s * 13.6, s * 17.6)):
        bookcase(FR, "z", -FZ, -1, min(a0, a1), max(a0, a1), 1.4, 15.0, 1.88, 5, int(a0))
        slab(FS, "z", -FZ, -1, 2.1, min(a0, a1) - 0.2, max(a0, a1) + 0.2, 15.0, 15.6, GOLD2)
portal(FS, FG, "z", -FZ, -1, 0.0, 9.2, 5.4, 2.0)
FS.box(-2.4, 2.4, 1.4, 4.0, -FZ - 2.4, -FZ - 0.88, WOOD2)  # пьедестал-ступени перед рамой
FS.box(-3.2, 3.2, 1.4, 2.4, -FZ - 3.2, -FZ - 0.88, BLUE3)
FS.box(-1.6, 1.6, 1.4, 3.8, -FZ - 2.46, -FZ - 2.4, GOLD)
for x, y, z, yaw, col in ((-6.4, 13.0, -FZ - 3.0, 0.3, BOOKS[0]), (6.6, 12.0, -FZ - 3.4, -0.4, BOOKS[2]), (-7.0, 6.0, -FZ - 3.6, -0.2, BOOKS[4]),
                          (7.2, 5.4, -FZ - 3.0, 0.5, BOOKS[1])):
    book(FS, x, y, z, 1.3, col, True, yaw)
for x, y in ((-5.0, 16.2), (5.4, 15.6), (-7.6, 9.6), (7.8, 9.0)):
    star_shape(FG, "z", -FZ, -1, x, y, 0.7, 2.4, 2.5, STARC)
# башенки-шпили с хрустальными шарами по углам
for sx in (-1, 1):
    for sz in (-1, 1):
        x, z = sx * (FX + 1.6), sz * (FZ + 1.6)
        FS.prism_xz(K.ngon(x, z, 1.4, 8), -0.2, 15.0, BLUE3)
        for y in (5.0, 10.0):
            FS.prism_xz(K.ngon(x, z, 1.55, 8), y, y + 0.4, GOLD)
        FS.cone([(x + 1.6 * math.cos(t), 15.0, z + 1.6 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]], (x, 17.6, z), BLUE2)
        FG.prism_xz(K.ngon(x, z, 0.6, 8), 17.6, 18.8, CRYSTAL)
# бока: парящие книги
for s in (-1, 1):
    for k, z in enumerate((-12.0, 0.0, 12.0)):
        book(FS, s * (FX + 2.0), 14.0 - 1.2 * k, z, 1.0, BOOKS[k + 2], True, math.pi / 2)
# сзади: балкон с глобусом
FS.box(-5.0, 5.0, 8.0, 8.6, FZ + 0.88, FZ + 3.6, WOOD2)
for k in range(9):
    FS.box(-4.6 + 1.15 * k, -4.4 + 1.15 * k, 8.6, 10.0, FZ + 3.3, FZ + 3.5, GOLD2)
FS.prism_xz(K.ngon(0.0, FZ + 2.0, 0.3, 6), 8.6, 10.2, GOLD)
ring_y(FS, 0.0, FZ + 2.0, 1.3, 1.5, 11.2, 11.4, GOLD, n=12)
FS.prism_xz(K.ngon(0.0, FZ + 2.0, 1.2, 10), 10.2, 12.4, "3A8ACA")

# ══ ИНТЕРЬЕР: читальный зал ═══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.5
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), CARPET)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    slab(IR, axis, fixed, out, 0.88, -half, half, 0.0, C, BLUE2)
    if gap:
        for s in (-1, 1):
            bookcase(IS, axis, fixed, out, min(s * (DOOR[0] + 0.8), s * (half - 0.2)), max(s * (DOOR[0] + 0.8), s * (half - 0.2)),
                     0.0, 12.0, 2.0, 5, 50 + s)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.8, GOLD2)
    elif idx < 2:
        for k, (a0, a1) in enumerate(((-half + 0.2, -5.0), (-4.0, 4.0), (5.0, half - 0.2))):
            bookcase(IS, axis, fixed, out, a0, a1, 0.0, 13.0, 2.0, 4, idx * 10 + k)
    slab(IS, axis, fixed, out, 2.4, -half, half, 13.0, 13.6, GOLD2)
    slab(IR, axis, fixed, out, 0.88, -half, half, 13.6, C, BLUE)
# передняя стена: большое зеркало-портал за экспонатом и шкафы по бокам
for s in (-1, 1):
    bookcase(IS, "z", ZF, 1, min(s * 8.0, s * 16.6), max(s * 8.0, s * 16.6), 0.0, 13.0, 2.0, 5, 70 + s)
portal(IS, IG, "z", ZF, 1, 0.0, 8.6, 4.2, 1.6)
# лестницы на колёсах у шкафов
for s, z in ((-1, -9.0), (1, 6.0)):
    x = s * (W - 2.6)
    for e in (-0.7, 0.7):
        beam(IS, (x - s * 1.6, 0.0, z + e), (x, 12.0, z + e), 0.2, 0.2, WOOD3)
    for k in range(9):
        t = (k + 0.5) / 9
        IS.box(min(x - s * 1.6 * (1 - t), x - s * 1.6 * (1 - t) + 0.01) - 0.1, max(x - s * 1.6 * (1 - t), x - s * 1.6 * (1 - t)) + 0.1,
               12.0 * t - 0.08, 12.0 * t + 0.08, z - 0.7, z + 0.7, WOOD3)
# большой глобус, столы для чтения с лампами, парящие книги и свечи
gx, gz = 10.5, -9.5
for k in range(3):
    t = 2 * math.pi * k / 3
    beam(IS, (gx, 2.0, gz), (gx + 1.2 * math.cos(t), 0.0, gz + 1.2 * math.sin(t)), 0.2, 0.2, WOOD2)
IS.prism_xz(K.ngon(gx, gz, 0.3, 6), 2.0, 3.0, GOLD)
ring_y(IS, gx, gz, 1.9, 2.1, 4.4, 4.6, GOLD, n=12)
IS.prism_xz(K.ngon(gx, gz, 1.3, 10), 3.0, 3.6, "3A8ACA")
IS.prism_xz(K.ngon(gx, gz, 1.8, 10), 3.6, 5.2, "3A8ACA")
IS.prism_xz(K.ngon(gx, gz, 1.3, 10), 5.2, 5.8, "3A8ACA")
for x, z in ((-10.0, 3.0), (10.0, 3.0)):
    IS.box(x - 2.4, x + 2.4, 2.4, 2.8, z - 1.2, z + 1.2, WOOD)
    for e in (-1, 1):
        for f in (-1, 1):
            IS.box(x + e * 2.1 - 0.15, x + e * 2.1 + 0.15, 0.0, 2.4, z + f * 0.9 - 0.15, z + f * 0.9 + 0.15, WOOD2)
    IS.box(x - 1.6, x - 0.4, 2.8, 3.0, z - 0.6, z + 0.4, BOOKS[1])
    IS.prism_xz(K.ngon(x + 1.2, z, 0.2, 6), 2.8, 4.0, GOLD)
    IG.prism_xz(K.ngon(x + 1.2, z, 0.6, 8), 4.0, 4.6, "7AF0A0")
for k, (x, y, z, yaw, col) in enumerate(((-6.0, 9.0, -6.0, 0.4, BOOKS[0]), (9.0, 11.5, 4.5, -0.5, BOOKS[2]), (-7.6, 11.0, 1.0, 0.9, BOOKS[3]),
                                         (-8.5, 9.5, -3.0, -0.2, BOOKS[4]), (0.0, 12.6, 4.0, 0.1, BOOKS[1]))):
    book(IS, x, y, z, 1.1, col, k % 2 == 0, yaw)
for k in range(10):
    x = -11.0 + 22.0 * rng(k, 61)
    z = -12.0 + 20.0 * rng(k, 62)
    if abs(x) < 5.0 and -8.0 < z < 2.0:
        continue
    candle(IS, IG, x, 9.0 + 4.0 * rng(k, 63), z)
# магический круг из рун на полу и ступенчатый золотой помост
px, pz = PED
ring_y(IG, px, pz, 6.0, 6.3, 0.02, 0.06, PORT1, n=24)
ring_y(IG, px, pz, 7.2, 7.4, 0.02, 0.06, PORT2, n=24)
for k in range(8):
    t = 2 * math.pi * k / 8 + 0.2
    IG.prism_xz(K.octa(px + 6.75 * math.cos(t), pz + 6.75 * math.sin(t), 0.35, 0.35, 0.14), 0.02, 0.07, STARC)
IR.prism_xz(K.ngon(px, pz, 4.6, 8), 0.0, 0.5, BLUE3)
IR.prism_xz(K.ngon(px, pz, 3.8, 8), 0.5, 1.0, BLUE)
IR.prism_xz(K.ngon(px, pz, 3.0, 8), 1.0, TOP, BLUE3)
for r, y in ((4.6, 0.5), (3.8, 1.0), (3.0, TOP)):
    ring_y(IS, px, pz, r - 0.1, r + 0.08, y - 0.12, y + 0.02, GOLD, n=8)
B.lift_leaves(IS, WOOD2, GOLD)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, BLUE)
SL.box(-FX - 2.9, FX + 2.9, -1.0, 0.0, -FZ - 2.9, FZ + 2.9, BLUE2)
SL.box(-FX - 1.9, FX + 1.9, 16.0, 17.2, -FZ - 1.9, FZ + 1.9, BLUE3)
SL.prism_xy([(5.4 * 0.82 * math.cos(2 * math.pi * k / 10), 9.2 + 5.4 * 1.12 * math.sin(2 * math.pi * k / 10)) for k in range(10)],
            -FZ - 2.0, -FZ, GOLD)
SL.prism_xy([(5.4 * 0.56 * math.cos(2 * math.pi * k / 10), 9.2 + 5.4 * 0.8 * math.sin(2 * math.pi * k / 10)) for k in range(10)],
            -FZ - 2.06, -FZ - 2.0, PORT1)

F.build(ml=2, exhibit=(PED[0], TOP, PED[1], 2.0), lamps=[("Hall", (0, 14, 6), 2600, (0.9, 0.85, 1.0)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.96, 0.9)),
                                                   ("Portal", (0, 8, -13), 1200, (0.7, 0.5, 1.0))])
