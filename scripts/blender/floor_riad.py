"""Этаж «Кобра-фонтан» музея-небоскрёба (седьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — марокканский риад. Снаружи — охристая штукатурка, внизу пояс мозаики-зеллиж из сине-зелёно-белых
квадратиков, наверху — ступенчатые зубцы парапета над мозаичным поясом; в центре — подковообразная арка входа в
синей мозаичной раме под прямоугольным порталом с восьмиконечной звездой, резная кедровая дверь; слева наверху —
кедровый эркер-машрабия с решёткой на резных консолях, справа — балкон с перилами и свисающими полосатыми коврами;
по сторонам двери — латунные фонари-звёзды и апельсиновые деревца в синих кадках; внизу справа — лавка специй под
полосатым навесом с конусами красного, жёлтого и зелёного порошка, кувшины и тажины. Внутри — двор риада: пол из
ромбов зеллиж, по бокам — аркады на тонких колоннах с подковообразными арками, у стен — пояса мозаики, на полу —
ковры, низкий латунный столик с подушками, апельсиновые деревца в кадках, под кедровым потолком со световым фонарём
— латунные фонари на цепях; у дальней стены — большая резная ниша-михраб в мозаичной раме; экспонат — на
восьмиугольной мозаичной тумбе с белой кромкой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_riad.py -- <репо> <превью>
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

OCHRE, OCHRE2, PLAST, TILEB, TILEG, TILEW = "D8A066", "C48A52", "EACB94", "2A6AB0", "2E9A6A", "F2EAD8"
CEDAR, CEDAR2, BRASS, TERRA, RUG1, RUG2, ORANGE, LEAF = "7A4A28", "5A3418", "C8982E", "B8583A", "B83A3A", "2A4A8A", "F08A20", "3A8A3A"
TILES = (TILEB, TILEW, TILEG, TILEW)

F = B.Floor("MQ", "CobraFountain", quiet=(OCHRE2, "D8B890", RUG1, RUG2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def horseshoe(a, y0, yc, r, n=14):
    """Контур подковообразной арки: прямые бока до yc, дуга 250° с сужением у пят."""
    t0, t1 = -0.39, math.pi + 0.39
    arc = [(a + r * math.cos(t0 + (t1 - t0) * k / n), yc + r * math.sin(t0 + (t1 - t0) * k / n)) for k in range(n + 1)]
    ax, ay = arc[0]
    bx, by = arc[-1]
    return [(a - r * 0.92, y0), (a + r * 0.92, y0), (a + r * 0.92, ay)] + arc[1:-1] + [(a - r * 0.92, by)]


def band(p, plane, outer, inner, d0, d1, col):
    """Рама-арка без нижней перемычки: четырёхугольники между соседними точками внешнего и внутреннего контуров
    (контуры одной длины, первый отрезок — низ проёма — пропускается); plane — 'xy' (стена z) или 'zy' (стена x)."""
    n = len(outer)
    for i in range(1, n):
        j = (i + 1) % n
        quad = [outer[i], outer[j], inner[j], inner[i]]
        (p.prism_xy if plane == "xy" else p.prism_zy)(quad, d0, d1, col)


def star8(cx, cy, r):
    """Восьмиконечная звезда из двух квадратов (контур)."""
    pts = []
    for i in range(16):
        t = math.pi / 8 * i
        rr = r if i % 2 == 0 else r * 0.72
        pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
    return pts


def tile_band(p, axis, fixed, out, a0, a1, y0, y1, step=0.8, depth=0.12, seed=0):
    """Пояс мозаики: квадратики трёх цветов в шахматном ритме (выступают на depth)."""
    n = int((a1 - a0) / step)
    rows = max(1, int(round((y1 - y0) / step)))
    for r in range(rows):
        for k in range(n):
            a = a0 + step * k
            y = y0 + (y1 - y0) * r / rows
            col = TILES[(k + 2 * r + seed) % 4]
            lo, hi = sorted((fixed, fixed + out * depth))
            if axis == "z":
                p.box(a + 0.04, a + step - 0.04, y + 0.04, y + (y1 - y0) / rows - 0.04, lo, hi, col)
            else:
                p.box(lo, hi, y + 0.04, y + (y1 - y0) / rows - 0.04, a + 0.04, a + step - 0.04, col)


def star_lantern(p, g, x, y, z, s=1.0):
    """Латунный фонарь-звезда: крышка-купол, светящийся гранёный корпус, навершие."""
    p.prism_xz(K.ngon(x, z, 0.12 * s, 6), y + 1.2 * s, y + 1.6 * s, BRASS)
    p.cone([(xx, y + 0.9 * s, zz) for xx, zz in K.ngon(x, z, 0.55 * s, 8)], (x, y + 1.25 * s, z), BRASS)
    g.prism_xz(star8(x, z, 0.55 * s), y + 0.25 * s, y + 0.9 * s, "FFC860")
    p.prism_xz(K.ngon(x, z, 0.45 * s, 8), y, y + 0.25 * s, BRASS)


def orange_tree(p, x, z, y=0.0, s=1.0):
    """Апельсиновое деревце в синей кадке."""
    p.prism_xz(K.ngon(x, z, 0.75 * s, 8), y, y + 1.2 * s, TILEB)
    p.prism_xz(K.ngon(x, z, 0.85 * s, 8), y + 1.2 * s, y + 1.4 * s, TILEW)
    p.prism_xz(K.ngon(x, z, 0.15 * s, 6), y + 1.4 * s, y + 2.6 * s, CEDAR)
    p.prism_xz(K.octa(x, z, 1.1 * s, 1.1 * s, 0.4 * s), y + 2.4 * s, y + 3.6 * s, LEAF)
    p.prism_xz(K.octa(x, z, 0.7 * s, 0.7 * s, 0.25 * s), y + 3.6 * s, y + 4.1 * s, "2E7A30")
    for k in range(5):
        t = 2 * math.pi * k / 5 + 0.3
        p.prism_xz(K.octa(x + 1.05 * s * math.cos(t), z + 1.05 * s * math.sin(t), 0.2 * s, 0.2 * s, 0.07 * s),
                   y + (2.7 + 0.4 * (k % 2)) * s, y + (3.0 + 0.4 * (k % 2)) * s, ORANGE)


def spice_cone(p, x, z, y, r, col):
    """Миска с конусом специи."""
    p.prism_xz(K.ngon(x, z, r, 8), y, y + 0.3, TERRA)
    p.cone([(xx, y + 0.3, zz) for xx, zz in K.ngon(x, z, r * 0.9, 8)], (x, y + 0.3 + r * 1.4, z), col)


# ══ ФАСАД: риад ═══════════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, OCHRE, PLAST, CEDAR2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "D8B890")
    slab(FR, axis, fixed, out, 1.18, -half - 0.2, half + 0.2, -0.1, 0.6, OCHRE2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 0.6, 16.0, OCHRE)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, 15.4, 16.2, OCHRE2)
    slab(FS, axis, fixed, out, 1.42, -half - 0.3, half + 0.3, 16.2, 16.4, TILEB)
    slab(FR, axis, fixed, out, 0.88, -half, half, 16.4, 17.2, OCHRE)
    for k in range(int(2 * half // 2.4) + 1):  # ступенчатые зубцы
        a = -half + 0.3 + 2.4 * k
        if a + 1.6 > half:
            continue
        slab(FR, axis, fixed, out, 1.18, a, a + 1.6, 17.2, 18.1, OCHRE)
        slab(FR, axis, fixed, out, 1.18, a + 0.4, a + 1.2, 18.1, 18.9, OCHRE)
    if fi == 0:
        for a0, a1 in ((-half + 0.4, -4.6), (4.6, half - 0.4)):
            tile_band(FS, axis, fixed + out * 0.88, out, a0, a1, 0.6, 2.2, seed=fi)
    else:
        tile_band(FS, axis, fixed + out * 0.88, out, -half + 0.4, half - 0.4, 0.6, 1.8, step=1.2, seed=fi)
        for a in (-10.0, -3.5, 3.0, 9.5):  # окна с кованой решёткой
            d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
            pr = FG.prism_zy if axis == "x" else FG.prism_xy
            for y0 in (4.4, 11.4):
                pr(horseshoe(a, y0, y0 + 1.8, 1.0, n=6), d0, d1, "3A2A1E")
                band(FS, "zy" if axis == "x" else "xy", horseshoe(a, y0, y0 + 1.8, 1.3, n=6), horseshoe(a, y0, y0 + 1.8, 1.0, n=6),
                     *sorted((fixed + out * 0.88, fixed + out * 1.1)), TILEB)
                for i in (-0.45, 0.0, 0.45):
                    lo, hi = sorted((fixed + out * 0.92, fixed + out * 1.0))
                    if axis == "x":
                        FS.box(lo, hi, y0, y0 + 2.6, a + i - 0.04, a + i + 0.04, "2A2A2A")
                    else:
                        FS.box(a + i - 0.04, a + i + 0.04, y0, y0 + 2.6, lo, hi, "2A2A2A")
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# вход: подковообразная арка в мозаичной раме, портал-альфиз со звездой, кедровая дверь
FS.box(-5.2, 5.2, 0.6, 12.6, -FZ - 1.3, -FZ - 0.88, PLAST)
FS.frame_xy(K.rect(-5.2, 5.2, 0.6, 12.6), K.rect(-4.6, 4.6, 0.6, 12.0), -FZ - 1.5, -FZ - 0.88, TILEB)
band(FS, "xy", horseshoe(0.0, 0.6, 6.8, 3.6), horseshoe(0.0, 0.6, 6.8, 3.0), -FZ - 1.6, -FZ - 1.3, TILEG)
FS.prism_xy(horseshoe(0.0, 0.6, 6.8, 3.0), -FZ - 1.34, -FZ - 1.3, CEDAR2)
FS.box(-2.6, 2.6, 0.6, 7.4, -FZ - 1.5, -FZ - 1.34, CEDAR)
FS.box(-0.05, 0.05, 0.6, 7.4, -FZ - 1.54, -FZ - 1.5, CEDAR2)
for e in (-1, 1):
    for j in range(3):
        FS.prism_xy(star8(e * 1.3, 2.4 + 2.0 * j, 0.45), -FZ - 1.6, -FZ - 1.5, BRASS)
for e in (-1, 1):  # звёзды в углах портала
    FS.prism_xy(star8(e * 3.9, 11.2, 0.5), -FZ - 1.4, -FZ - 1.3, TILEB)
FS.prism_xy(star8(0.0, 11.4, 0.7), -FZ - 1.4, -FZ - 1.3, TILEG)
for k in range(3):  # ступеньки
    FS.box(-3.6 + 0.3 * k, 3.6 - 0.3 * k, -0.1, 0.2 + 0.25 * k, -FZ - 2.4 + 0.45 * k, -FZ - 0.88, TERRA)
# слева (по фасаду +x): кедровый эркер-машрабия на консолях
MX = 10.4
FS.box(MX - 3.6, MX + 3.6, 9.0, 15.0, -FZ - 2.8, -FZ - 0.88, CEDAR)
FS.box(MX - 3.9, MX + 3.9, 15.0, 15.4, -FZ - 3.0, -FZ - 0.88, CEDAR2)
FS.box(MX - 3.9, MX + 3.9, 8.6, 9.0, -FZ - 3.0, -FZ - 0.88, CEDAR2)
FG.box(MX - 3.2, MX + 3.2, 9.6, 14.4, -FZ - 2.84, -FZ - 2.8, "FFC860")
for i in range(9):
    x = MX - 3.2 + 0.8 * i
    FS.box(x - 0.08, x + 0.08, 9.6, 14.4, -FZ - 2.95, -FZ - 2.84, CEDAR2)
for j in range(7):
    y = 9.6 + 0.8 * j
    FS.box(MX - 3.2, MX + 3.2, y - 0.08, y + 0.08, -FZ - 2.95, -FZ - 2.84, CEDAR2)
for x in (MX - 2.8, MX, MX + 2.8):
    FS.prism_zy([(-FZ - 0.88, 8.6), (-FZ - 2.6, 8.6), (-FZ - 2.0, 7.6), (-FZ - 0.88, 6.4)], x - 0.3, x + 0.3, CEDAR2)
# справа: балкон с перилами и полосатыми коврами
BX = -10.4
FS.box(BX - 4.0, BX + 4.0, 9.0, 9.5, -FZ - 2.4, -FZ - 0.88, OCHRE2)
FS.box(BX - 4.0, BX + 4.0, 11.4, 11.6, -FZ - 2.35, -FZ - 2.2, "2A2A2A")
for k in range(9):
    x = BX - 4.0 + 1.0 * k
    FS.box(x - 0.05, x + 0.05, 9.5, 11.4, -FZ - 2.32, -FZ - 2.24, "2A2A2A")
FG.prism_xy(horseshoe(BX, 9.5, 12.6, 1.4), -FZ - 0.94, -FZ - 0.9, "3A2A1E")
band(FS, "xy", horseshoe(BX, 9.5, 12.6, 1.7), horseshoe(BX, 9.5, 12.6, 1.4), -FZ - 1.1, -FZ - 0.88, TILEB)
for k, (x0, cols) in enumerate(((BX - 3.6, (RUG1, "F0C040", RUG1, TILEB)), (BX + 0.8, (RUG2, TILEW, RUG2, ORANGE)))):
    for i, col in enumerate(cols * 2):
        FS.box(x0, x0 + 2.8, 11.6 - 0.75 * (i + 1), 11.6 - 0.75 * i, -FZ - 2.48, -FZ - 2.36, col)
# латунные фонари у двери и апельсиновые деревца
F.objects(True)
for e in (-1, 1):
    FS.box(e * 6.0 - 0.06, e * 6.0 + 0.06, 9.6, 10.6, -FZ - 1.9, -FZ - 0.88, BRASS)
    star_lantern(FS, FG, e * 6.0, 8.2, -FZ - 1.9, s=0.9)
    orange_tree(FS, e * 6.4, -FZ - 1.9, y=-0.1, s=0.9)
F.objects(False)
# лавка специй под полосатым навесом (справа внизу), кувшины и тажины
F.objects(True)
SX = -12.4
FS.box(SX - 3.6, SX + 3.6, -0.1, 1.6, -FZ - 2.7, -FZ - 1.2, CEDAR)
for k, col in enumerate(("D83A2A", "F0C020", "E87A20", "6AA83A", "A04A2A", "F0C020")):
    spice_cone(FS, SX - 3.0 + 1.2 * k, -FZ - 1.95, 1.6, 0.5, col)
for x in (SX - 3.5, SX + 3.5):
    FS.box(x - 0.1, x + 0.1, -0.1, 6.6, -FZ - 2.8, -FZ - 2.6, CEDAR2)
for k in range(8):
    x0 = SX - 3.8 + 0.95 * k
    FS.loft([(x0, 7.2, -FZ - 0.9), (x0 + 0.95, 7.2, -FZ - 0.9), (x0 + 0.95, 7.35, -FZ - 0.9), (x0, 7.35, -FZ - 0.9)],
            [(x0, 6.4, -FZ - 2.9), (x0 + 0.95, 6.4, -FZ - 2.9), (x0 + 0.95, 6.55, -FZ - 2.9), (x0, 6.55, -FZ - 2.9)],
            RUG1 if k % 2 else TILEW)
for x, h in ((-16.8, 1.6), (-8.0, 1.2)):  # кувшины
    FS.prism_xz(K.ngon(x, -FZ - 2.1, 0.35, 8), -0.1, 0.2, TERRA)
    FS.prism_xz(K.ngon(x, -FZ - 2.1, 0.6, 8), 0.2, h, TERRA)
    FS.prism_xz(K.ngon(x, -FZ - 2.1, 0.25, 8), h, h + 0.5, TERRA)
FS.prism_xz(K.ngon(-8.0, -FZ - 1.2, 0.55, 8), -0.1, 0.2, TILEG)  # тажин
FS.cone([(xx, 0.2, zz) for xx, zz in K.ngon(-8.0, -FZ - 1.2, 0.5, 8)], (-8.0, 1.0, -FZ - 1.2), TILEG)
F.objects(False)
# тыл и бока: пальма у угла
F.objects(True)
D.palm(FS, (FX + 1.6, -0.1, FZ + 1.6), (0.8, 0.4), 9.0)
F.objects(False)

# ══ ИНТЕРЬЕР: двор риада ══════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.0
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), TILEW)
for i in range(-5, 6):
    for j in range(-5, 6):
        if (i + j) % 2 == 0:
            x, z = 2.4 * i, -3.0 + 2.4 * j
            if abs(x) < 11.0 and ZF + 1.4 < z < ZB - 1.4:
                IQ.prism_xz([(x, z - 1.2), (x + 1.2, z), (x, z + 1.2), (x - 1.2, z)], 0.02, 0.04, TILEB if (i // 2 + j // 2) % 2 else TILEG)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, PLAST)
        tile_band(IS, axis, fixed + out * 0.88, out, a0 + 0.1, a1 - 0.1, 0.0, 2.4, step=1.2, seed=idx)
        slab(IS, axis, fixed, out, 1.1, a0, a1, 2.4, 2.6, TILEB)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, PLAST)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, CEDAR)
    slab(IR, axis, fixed, out, 1.4, -half, half, 15.6, 16.4, OCHRE2)
    slab(IS, axis, fixed, out, 1.45, -half, half, 16.4, 16.6, TILEG)
# кедровый потолок со световым фонарём
for k in range(-3, 4):
    IS.box(-W, W, C - 0.7, C - 0.2, 4.4 * k - 0.25, 4.4 * k + 0.25, CEDAR2)
IS.frame_xz(K.rect(-5.0, 5.0, -8.0, 2.0), K.rect(-4.2, 4.2, -7.2, 1.2), C - 1.2, C - 0.1, CEDAR)
IG.prism_xz(K.rect(-4.2, 4.2, -7.2, 1.2), C - 0.08, C - 0.04, "F4F0E0")
# аркады на тонких колоннах вдоль боковых стен
for s in (-1, 1):
    x = s * (W - 3.4)
    zs = (-13.4, -7.4, -1.4, 4.6, 10.6)
    for z in zs:
        IS.prism_xz(K.ngon(x, z, 0.45, 8), 0.0, 2.4, TILEB)
        IS.prism_xz(K.ngon(x, z, 0.35, 8), 2.4, 9.0, TILEW)
        IS.box(x - 0.6, x + 0.6, 9.0, 9.5, z - 0.6, z + 0.6, OCHRE2)
    for z0, z1 in zip(zs, zs[1:]):
        zc = (z0 + z1) / 2
        band(IS, "zy", horseshoe(zc, 9.5, 11.4, 2.85), horseshoe(zc, 9.5, 11.4, 2.4), x - 0.4, x + 0.4, PLAST)
        band(IS, "zy", horseshoe(zc, 9.5, 11.4, 2.55), horseshoe(zc, 9.5, 11.4, 2.4), x - 0.46, x + 0.46, TILEG)
    IS.box(x - 0.5, x + 0.5, 14.2, 15.6, ZF + 0.88, 11.2, OCHRE2)
    IS.box(*sorted((x, s * W)), 14.2, 14.6, ZF + 0.88, 11.2, CEDAR)
# дальняя стена: ниша-михраб в мозаичной раме
IS.frame_xy(K.rect(-6.0, 6.0, 0.0, 14.0), K.rect(-5.2, 5.2, 0.0, 13.2), ZF + 0.88, ZF + 1.5, TILEB)
IS.prism_xy(K.rect(-5.2, 5.2, 0.0, 13.2), ZF + 0.88, ZF + 1.0, TILEW)
band(IS, "xy", horseshoe(0.0, 0.0, 7.6, 4.2), horseshoe(0.0, 0.0, 7.6, 3.5), ZF + 1.0, ZF + 1.6, TILEG)
IS.prism_xy(horseshoe(0.0, 0.0, 7.6, 3.5), ZF + 1.0, ZF + 1.04, "1E4A80")
IG.prism_xy(star8(0.0, 8.0, 1.6), ZF + 1.04, ZF + 1.08, "FFC860")
for e in (-1, 1):
    IS.prism_xy(star8(e * 4.4, 12.2, 0.55), ZF + 1.0, ZF + 1.6, TILEB)
# ковры, столик с подушками, деревца, фонари на цепях
IQ.box(-12.0, -6.4, 0.04, 0.08, -11.0, -4.0, RUG1)
IQ.box(-11.6, -6.8, 0.08, 0.1, -10.6, -4.4, RUG2)
IQ.box(6.4, 12.0, 0.04, 0.08, -11.0, -4.0, RUG2)
IQ.box(6.8, 11.6, 0.08, 0.1, -10.6, -4.4, RUG1)
F.objects(True)
TX, TZ = 9.2, -7.5
IS.prism_xz(K.ngon(TX, TZ, 1.4, 12), 1.0, 1.15, BRASS)
for k in range(4):
    t = math.pi / 2 * k + math.pi / 4
    IS.box(TX + 0.8 * math.cos(t) - 0.08, TX + 0.8 * math.cos(t) + 0.08, 0.1, 1.0, TZ + 0.8 * math.sin(t) - 0.08,
           TZ + 0.8 * math.sin(t) + 0.08, CEDAR)
IS.prism_xz(K.ngon(TX, TZ, 0.3, 8), 1.15, 1.5, TILEB)  # чайник
for k, col in enumerate((RUG1, "F0C040", TILEG, RUG2)):
    t = math.pi / 2 * k
    IS.box(TX + 2.4 * math.cos(t) - 0.7, TX + 2.4 * math.cos(t) + 0.7, 0.1, 0.6, TZ + 2.4 * math.sin(t) - 0.7,
           TZ + 2.4 * math.sin(t) + 0.7, col)
for x, z in ((-W + 1.6, 7.0), (W - 1.6, 7.0), (-9.4, -13.6), (W - 1.6, -13.6)):
    orange_tree(IS, x, z, s=1.0)
F.objects(False)
for x, z, y in ((-6.0, -8.0, 11.0), (6.0, -8.0, 10.2), (-6.0, 2.0, 10.6), (6.0, 2.0, 11.4), (0.0, 5.0, 12.0)):
    IS.box(x - 0.03, x + 0.03, y + 1.6, C - 0.7, z - 0.03, z + 0.03, BRASS)
    star_lantern(IS, IG, x, y, z, s=1.0)
# мозаичная восьмигранная тумба с белой кромкой
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 8, 0.0), 0.0, 0.5, TERRA)
IS.prism_xz(K.ngon(px, pz, 3.6, 8, 0.0), 0.5, TOP - 0.1, TILEB)
IS.prism_xz(K.ngon(px, pz, 3.8, 8, 0.0), TOP - 0.1, TOP, TILEW)
for k in range(8):
    t = 2 * math.pi * (k + 0.5) / 8
    IS.box(px + 3.45 * math.cos(t) - 0.25, px + 3.45 * math.cos(t) + 0.25, 0.6, TOP - 0.2, pz + 3.45 * math.sin(t) - 0.25,
           pz + 3.45 * math.sin(t) + 0.25, TILEG)
B.lift_leaves(IS, CEDAR, BRASS)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 17.2, -FZ, FZ, OCHRE)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "D8B890")
SL.box(-FX - 0.3, FX + 0.3, 15.4, 16.4, -FZ - 0.3, FZ + 0.3, TILEB)
SL.box(-FX, FX, 17.2, 18.5, -FZ - 0.3, FZ + 0.3, OCHRE)
SL.box(MX - 3.9, MX + 3.9, 8.6, 15.4, -FZ - 3.0, -FZ, CEDAR)

F.build(exhibit=(PED[0], TOP, PED[1], 2.8), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.92, 0.8)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Sky", (0, 16, -3), 800, (0.95, 0.95, 1.0))])
