"""Этаж «Крысиный маг» музея-небоскрёба (седьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — башня мага-звездочёта. Снаружи — серый камень с рустом на углах и зубцами по парапету, по передним
углам — две восьмигранные башенки с фиолетовыми коническими крышами и золотыми звёздами на шпилях; в центре —
стрельчатая дверь из тёмного дерева с железными полосами под круглым витражом-звездой; слева наверху — эркер-балкон
с тремя узкими окнами и латунным телескопом, справа — длинное знамя с полумесяцем; у входа — котёл на огне с зелёным
варевом и хрустальный шар на каменной тумбе, метла у стены; на боках — контрфорсы и стрельчатые окна. Внутри —
кабинет мага: пол из плит с сияющим магическим кругом и рунами вокруг постамента, по бокам — книжные шкафы до потолка,
у дальней стены — круглое окно в звёздное небо и полки со светящимися зельями, слева — большой котёл на огне,
справа — стол алхимика с колбами и раскрытой книгой, под тёмно-синим потолком со звёздами — армиллярная сфера и
парящие свечи; экспонат — на серой каменной тумбе в две ступени с голубыми рунами.
Запуск: blender --background --factory-startup --python scripts/blender/floor_wizard.py -- <репо> <превью>
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

STONE, STONE2, DARK, SLATE, SLATE2 = "7A7E92", "62667A", "3A3C4A", "5A3E90", "432C70"
WOOD, WOOD2, GOLD, MAGIC, PURP, GREEN = "6A4A2A", "4E3420", "E8C040", "6AE0F8", "7A4AC0", "7CF050"
NIGHTB, PARCH, IRON, FIRE = "1E2A50", "E8D8A8", "3A3A44", "FF9A30"
BOOKS = ("A83A3A", "3A6AA8", "3A8A4A", "C89A3A", "7A3A8A", "5A3A2A", "2A5A6A")

F = B.Floor("WZ", "RatWizard", quiet=(STONE2, "565A6C"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def lancet(a, y0, y1, w):
    """Контур стрельчатого окна: прямые бока до y1, острый верх."""
    return [(a - w, y0), (a + w, y0), (a + w, y1), (a + w * 0.6, y1 + w * 0.9), (a, y1 + w * 1.5),
            (a - w * 0.6, y1 + w * 0.9), (a - w, y1)]


def star(cx, cy, r, n=5, k=0.45):
    """Звезда-многоугольник (контур)."""
    pts = []
    for i in range(2 * n):
        t = math.pi / 2 + math.pi * i / n
        rr = r if i % 2 == 0 else r * k
        pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
    return pts


def cauldron(p, g, x, z, y=0.0, r=1.4):
    """Котёл на трёх ножках над огнём, с бурлящим варевом."""
    for k in range(3):
        t = 2 * math.pi * k / 3 + 0.5
        beam(p, (x + r * 0.7 * math.cos(t), y + 0.9, z + r * 0.7 * math.sin(t)),
             (x + r * 1.05 * math.cos(t), y, z + r * 1.05 * math.sin(t)), 0.18, 0.18, IRON)
    for k in range(4):
        t = 2 * math.pi * k / 4 + 0.3
        beam(p, (x - 0.9 * math.cos(t), y + 0.15, z - 0.9 * math.sin(t)), (x + 0.9 * math.cos(t), y + 0.15, z + 0.9 * math.sin(t)),
             0.3, 0.3, WOOD2)
    g.prism_xz(K.ngon(x, z, 0.6, 6), y + 0.3, y + 0.9, FIRE)
    p.prism_xz(K.ngon(x, z, r * 0.75, 12), y + 0.7, y + 1.0, IRON)
    p.prism_xz(K.ngon(x, z, r, 12), y + 1.0, y + 2.0, IRON)
    p.prism_xz(K.ngon(x, z, r * 0.92, 12), y + 2.0, y + 2.3, IRON)
    p.prism_xz(K.ngon(x, z, r * 1.02, 12), y + 2.3, y + 2.45, IRON)
    g.prism_xz(K.ngon(x, z, r * 0.86, 12), y + 2.3, y + 2.4, GREEN)
    for k in range(4):  # пузыри варева
        t = 2 * math.pi * k / 4 + 0.7
        rr = 0.18 + 0.1 * (k % 2)
        g.prism_xz(K.octa(x + 0.5 * math.cos(t), z + 0.5 * math.sin(t), rr, rr, rr * 0.4), y + 2.4, y + 2.4 + rr * 1.6, "B8FF90")


def crystal_ball(p, g, x, z, y=0.0):
    """Хрустальный шар на каменной тумбе с золотыми лапками."""
    p.prism_xz(K.ngon(x, z, 0.7, 8), y, y + 0.3, STONE2)
    p.prism_xz(K.ngon(x, z, 0.4, 8), y + 0.3, y + 1.8, STONE)
    p.prism_xz(K.ngon(x, z, 0.65, 8), y + 1.8, y + 2.1, GOLD)
    g.prism_xz(K.octa(x, z, 0.55, 0.55, 0.22), y + 2.1, y + 3.1, "A8E8FF")
    g.prism_xz(K.octa(x, z, 0.38, 0.38, 0.15), y + 3.1, y + 3.3, "D8F8FF")


def bookcase_z(p, x, out, z0, z1, y0, y1, seed=0):
    """Книжный шкаф у боковой стены (x — плоскость стены, out — внутрь зала): корпус, полки, книги разной высоты."""
    d0, d1 = sorted((x, x + out * 1.2))
    p.box(d0, d1, y0, y0 + 0.4, z0, z1, WOOD2)
    p.box(d0, d1, y1 - 0.4, y1, z0 - 0.2, z1 + 0.2, WOOD2)
    for z in (z0, z1):
        p.box(d0, d1, y0, y1, z - 0.2, z + 0.2, WOOD2)
    shelves = 4
    step = (y1 - y0 - 0.8) / shelves
    for k in range(shelves):
        yb = y0 + 0.4 + step * k
        p.box(d0, d1, yb, yb + 0.12, z0, z1, WOOD)
        z = z0 + 0.25
        i = 0
        while z < z1 - 0.6:
            w = 0.3 + 0.2 * rng(seed, k, i)
            h = step * (0.55 + 0.3 * rng(i, k, seed + 3))
            b0, b1 = sorted((x + out * 0.15, x + out * 1.0))
            p.box(b0, b1, yb + 0.12, yb + 0.12 + h, z, z + w, BOOKS[(i + k * 3 + seed) % len(BOOKS)])
            z += w + 0.04
            i += 1


# ══ ФАСАД: башня мага ═════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, STONE, STONE, NIGHTB)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "565A6C")
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.6, STONE2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.6, 16.6, STONE)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, 9.2, 9.8, STONE2)
    slab(FS, axis, fixed, out, 1.42, -half - 0.3, half + 0.3, 9.8, 10.0, SLATE)
    slab(FR, axis, fixed, out, 1.88, -half - 0.5, half + 0.5, 16.6, 17.4, STONE2)
    slab(FR, axis, fixed, out, 1.38, -half - 0.2, half + 0.2, 17.4, 17.9, STONE)
    for k in range(int(2 * half // 2.4) + 1):  # зубцы парапета
        a = -half - 0.2 + 2.4 * k
        if a + 1.4 <= half + 0.2:
            slab(FR, axis, fixed, out, 1.38, a, a + 1.4, 17.9, 18.9, STONE)
    for e in (-1, 1):  # руст на углах: длинный / короткий камень через один
        for k in range(7):
            y = 1.6 + 2.1 * k
            ln = 2.4 if k % 2 == 0 else 1.4
            a0, a1 = (half - ln, half) if e > 0 else (-half, -half + ln)
            if y + 1.9 <= 16.6:
                slab(FR, axis, fixed, out, 1.18, a0, a1, y, y + 1.9, STONE2 if k % 2 else STONE)
    if fi > 0:  # бока и тыл: контрфорсы и стрельчатые окна
        for a in (-9.0, 0.0, 9.0):
            d = lambda v: fixed + out * v  # noqa: E731
            pr = FG.prism_zy if axis == "x" else FG.prism_xy
            fr = FS.frame_zy if axis == "x" else FS.frame_xy
            pr(lancet(a, 3.0, 6.8, 0.9), *sorted((d(0.88), d(0.92))), MAGIC)
            fr(lancet(a, 2.7, 6.8, 1.2), lancet(a, 3.0, 6.8, 0.9), *sorted((d(0.88), d(1.15))), STONE2)
            pr(lancet(a, 11.2, 14.4, 0.9), *sorted((d(0.88), d(0.92))), MAGIC)
            fr(lancet(a, 10.9, 14.4, 1.2), lancet(a, 11.2, 14.4, 0.9), *sorted((d(0.88), d(1.15))), STONE2)
        for a in (-13.2, -4.5, 4.5, 13.2):
            prof = [(0.88, 1.6), (2.2, 1.6), (2.2, 6.0), (1.6, 9.2), (1.6, 13.0), (0.88, 16.6)]
            if axis == "z":
                FR.prism_zy([(fixed + out * dd, y) for dd, y in prof], a - 0.6, a + 0.6, STONE2)
            else:
                FR.prism_xy([(fixed + out * dd, y) for dd, y in prof], a - 0.6, a + 0.6, STONE2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# башенки по передним углам
for e in (-1, 1):
    tx, tz = e * (FX - 0.6), -FZ - 0.9
    FR.prism_xz(K.ngon(tx, tz, 2.4, 8), -0.1, 13.4, STONE)
    FS.prism_xz(K.ngon(tx, tz, 2.55, 8), 9.2, 9.8, SLATE)
    FS.prism_xz(K.ngon(tx, tz, 2.8, 8), 13.0, 13.6, STONE2)
    FS.prism_xz(K.ngon(tx, tz, 2.95, 8), 13.6, 13.9, SLATE2)
    FS.cone([(x, 13.9, z) for x, z in K.ngon(tx, tz, 2.95, 8)], (tx, 18.4, tz), SLATE)
    for k in range(4):  # слуховые окошки на крыше
        t = 2 * math.pi * (k + 0.5) / 4 + math.pi / 4
        if math.sin(t) < 0.3:
            x, z = tx + 2.05 * math.cos(t), tz + 2.05 * math.sin(t)
            FG.prism_xz(K.ngon(x, z, 0.3, 4), 14.6, 15.4, "FFD070")
    FS.prism_xz(K.ngon(tx, tz, 0.12, 6), 18.2, 18.6, GOLD)
    FS.prism_xy(star(tx, 18.5, 0.4), tz - 0.06, tz + 0.06, GOLD)
    for y0 in (3.0, 9.9):  # узкие окна башенки
        FG.prism_xy(lancet(tx, y0, y0 + 2.4, 0.35), tz - 2.42, tz - 2.38, MAGIC)
        FS.frame_xy(lancet(tx, y0 - 0.2, y0 + 2.4, 0.55), lancet(tx, y0, y0 + 2.4, 0.35), tz - 2.5, tz - 2.3, STONE2)
# стрельчатая дверь под круглым витражом-звездой
DX = 0.0
FS.prism_xy(lancet(DX, 1.6, 6.4, 2.6), -FZ - 1.4, -FZ - 0.88, STONE2)
FS.prism_xy(lancet(DX, 1.6, 6.2, 2.0), -FZ - 1.46, -FZ - 1.4, WOOD)
FS.frame_xy(lancet(DX, 1.6, 6.4, 2.6), lancet(DX, 1.6, 6.2, 2.0), -FZ - 1.7, -FZ - 1.4, STONE)
FS.box(DX - 0.04, DX + 0.04, 1.6, 8.8, -FZ - 1.52, -FZ - 1.46, WOOD2)
for y in (2.6, 5.2):
    FS.box(DX - 1.9, DX + 1.9, y, y + 0.25, -FZ - 1.54, -FZ - 1.46, IRON)
for e in (-1, 1):
    FS.prism_xy(K.ngon(DX + e * 0.5, 4.0, 0.16, 8), -FZ - 1.6, -FZ - 1.46, GOLD)
for k in range(3):  # ступени
    FS.box(DX - 3.0 + 0.3 * k, DX + 3.0 - 0.3 * k, -0.1 + 0.4 * k, 0.3 + 0.4 * k, -FZ - 2.8 + 0.5 * k, -FZ - 0.88, STONE2)
RY = 13.2
FS.frame_xy(K.ngon(DX, RY, 2.6, 16), K.ngon(DX, RY, 2.2, 16), -FZ - 1.4, -FZ - 0.88, STONE2)
FG.prism_xy(K.ngon(DX, RY, 2.2, 16), -FZ - 0.94, -FZ - 0.9, NIGHTB)
FG.prism_xy(star(DX, RY, 1.9, 6, 0.5), -FZ - 0.98, -FZ - 0.94, MAGIC)
FG.prism_xy(star(DX, RY, 0.8, 6, 0.5), -FZ - 1.02, -FZ - 0.98, "F4F0FF")
# эркер-балкон слева с тремя узкими окнами и телескопом
OX = 8.4
FR.box(OX - 3.6, OX + 3.6, 10.0, 15.2, -FZ - 2.6, -FZ - 0.5, STONE)
FR.prism_xy([(OX - 3.6, 10.0), (OX + 3.6, 10.0), (OX + 2.4, 8.6), (OX - 2.4, 8.6)], -FZ - 2.6, -FZ - 0.5, STONE2)
FR.box(OX - 3.9, OX + 3.9, 15.2, 15.8, -FZ - 2.9, -FZ - 0.5, STONE2)
FS.cone([(OX - 3.9, 15.8, -FZ - 2.9), (OX + 3.9, 15.8, -FZ - 2.9), (OX + 3.9, 15.8, -FZ - 0.5), (OX - 3.9, 15.8, -FZ - 0.5)],
        (OX, 17.4, -FZ - 1.7), SLATE)
for a in (OX - 2.2, OX, OX + 2.2):
    FG.prism_xy(lancet(a, 11.0, 13.4, 0.55), -FZ - 2.64, -FZ - 2.6, MAGIC)
    FS.frame_xy(lancet(a, 10.8, 13.4, 0.75), lancet(a, 11.0, 13.4, 0.55), -FZ - 2.8, -FZ - 2.6, STONE2)
F.objects(True)
TS = (OX + 2.6, 15.0, -FZ - 2.4)  # латунный телескоп на крыше эркера, смотрит в небо
beam(FS, (OX + 1.4, 15.8, -FZ - 1.8), TS, 0.2, 0.2, IRON)
taper(FS, (OX + 1.6, 15.6, -FZ - 1.8), (OX + 4.2, 17.8, -FZ - 2.6), 0.55, 0.85, GOLD)
FS.prism_xz(K.ngon(OX + 4.25, -FZ - 2.62, 0.48, 8), 17.8, 18.1, "A07828")
F.objects(False)
# знамя справа с полумесяцем и звёздами
BX = -8.8
FS.box(BX - 2.4, BX + 2.4, 15.8, 16.1, -FZ - 1.6, -FZ - 0.88, GOLD)
FS.prism_xy([(BX - 2.0, 15.8), (BX + 2.0, 15.8), (BX + 2.0, 10.6), (BX, 9.4), (BX - 2.0, 10.6)], -FZ - 1.3, -FZ - 1.1, PURP)
FS.frame_xy([(BX - 2.0, 15.8), (BX + 2.0, 15.8), (BX + 2.0, 10.6), (BX, 9.4), (BX - 2.0, 10.6)],
            [(BX - 1.8, 15.6), (BX + 1.8, 15.6), (BX + 1.8, 10.7), (BX, 9.7), (BX - 1.8, 10.7)], -FZ - 1.36, -FZ - 1.1, GOLD)
moon_o = [(BX + 1.3 * math.cos(t), 13.2 + 1.3 * math.sin(t)) for t in [math.pi * (0.3 + 1.4 * k / 10) for k in range(11)]]
moon_i = [(BX + 0.45 + 1.0 * math.cos(t), 13.35 + 1.0 * math.sin(t)) for t in [math.pi * (1.65 - 1.25 * k / 10) for k in range(11)]]
FS.prism_xy(moon_o + moon_i, -FZ - 1.42, -FZ - 1.3, GOLD)
for sx, sy in ((BX + 1.0, 14.4), (BX + 1.1, 11.6), (BX - 0.6, 10.9)):
    FS.prism_xy(star(sx, sy, 0.35), -FZ - 1.42, -FZ - 1.3, GOLD)
# справа внизу — витрина лавки зелий (одно широкое окно), слева — плющ и фонарь
VX = -9.2
FS.prism_xy(lancet(VX, 2.6, 6.4, 2.6), -FZ - 1.2, -FZ - 0.88, STONE2)
FG.prism_xy(lancet(VX, 2.9, 6.4, 2.3), -FZ - 1.24, -FZ - 1.2, "3A2A60")
FS.box(VX - 2.3, VX + 2.3, 2.9, 3.1, -FZ - 1.9, -FZ - 1.2, WOOD)
FS.box(VX - 2.3, VX + 2.3, 4.7, 4.85, -FZ - 1.5, -FZ - 1.2, WOOD)
for k in range(7):
    x = VX - 1.8 + 0.6 * k
    col = ("B070F0", GREEN, MAGIC, "FF70B0", "FFB040", GREEN, "B070F0")[k]
    FG.prism_xz(K.ngon(x, -FZ - 1.45, 0.2, 6), 3.1, 3.7 + 0.25 * (k % 3), col)
    FG.prism_xz(K.ngon(x + 0.3, -FZ - 1.35, 0.17, 6), 4.85, 5.4, ("FF70B0", MAGIC, GREEN)[k % 3])
F.objects(True)
for k, (bx, by, w, h, col) in enumerate(((10.2, -0.1, 3.0, 0.8, "8A2A3A"), (10.0, 0.7, 2.6, 0.7, "2A4A8A"),
                                         (10.3, 1.4, 2.2, 0.6, "2A6A3A"))):  # стопка огромных старых книг
    FS.box(bx - w / 2, bx + w / 2, by, by + h, -FZ - 2.6, -FZ - 1.0, col)
    FS.box(bx - w / 2 + 0.15, bx + w / 2 - 0.02, by + 0.1, by + h - 0.1, -FZ - 2.64, -FZ - 1.1, PARCH)
    FS.box(bx - w / 2 - 0.02, bx - w / 2 + 0.2, by + 0.25, by + h - 0.25, -FZ - 2.62, -FZ - 0.98, GOLD)
FS.prism_xy([(12.0, -0.1), (12.7, -0.1), (13.9, 2.8), (13.2, 2.8)], -FZ - 2.5, -FZ - 1.1, "5A2A6A")  # прислонённая книга
FS.prism_xy([(12.1, 0.1), (12.6, 0.1), (13.7, 2.6), (13.2, 2.6)], -FZ - 2.54, -FZ - 2.5, PARCH)
F.objects(False)
FS.box(5.2, 5.4, 6.4, 7.6, -FZ - 1.9, -FZ - 0.88, IRON)
D.lantern(FS, FG, 5.3, 5.4, -FZ - 1.9, s=0.8, cap=IRON, light="FFD070")
# у входа: котёл, хрустальный шар, метла
F.objects(True)
cauldron(FS, FG, -6.0, -FZ - 1.9, y=-0.1, r=1.0)
crystal_ball(FS, FG, 6.2, -FZ - 1.9, y=-0.1)
beam(FS, (4.0, -0.1, -FZ - 2.0), (3.4, 4.6, -FZ - 1.0), 0.16, 0.16, WOOD)
taper(FS, (4.15, -0.1, -FZ - 2.1), (4.0, 1.4, -FZ - 1.85), 0.9, 0.35, "C8A050")
for x in (-12.6, -10.8):
    D.crate(FS, x, -FZ - 2.0, y=-0.1, s=1.3, wood="7A5A3A", board=WOOD2)
for k in range(5):  # склянки на ящиках
    FG.prism_xz(K.ngon(-12.9 + 0.55 * k, -FZ - 2.0, 0.16, 6), 1.2, 1.7, ("B070F0", GREEN, MAGIC, "FF70B0", GREEN)[k])
F.objects(False)

# ══ ИНТЕРЬЕР: кабинет мага ═══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.1
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "585C6E")
for i in range(-6, 7):
    for j in range(-6, 7):
        x, z = 2.6 * i, 2.6 * j
        if rng(i, j) < 0.35 and -W + 0.3 < x - 1.2 and x + 1.2 < W - 0.3 and ZF + 0.3 < z - 1.2 and z + 1.2 < ZB - 0.3:
            IQ.box(x - 1.2, x + 1.2, 0.02, 0.04, z - 1.2, z + 1.2, "4A4E60")
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, STONE)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 1.2, STONE2)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, STONE)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, WOOD2)
    slab(IR, axis, fixed, out, 1.5, -half, half, 15.6, 16.2, STONE2)
for k in range(-3, 4):  # тёмные балки потолка
    IS.box(-W, W, C - 0.6, C - 0.2, 4.4 * k - 0.25, 4.4 * k + 0.25, WOOD2)
for k in range(28):  # звёзды на потолке
    x, z = -W + 1.5 + (2 * W - 3) * rng(k, 1), ZF + 1.5 + (ZB - ZF - 3) * rng(k, 2)
    IG.prism_xz(K.ngon(x, z, 0.12 + 0.08 * rng(k, 3), 4), C - 0.04, C - 0.02, "F4F0FF")
# книжные шкафы по бокам
F.objects(True)
for s in (-1, 1):
    for z0, z1 in ((-13.6, -6.6), (-4.4, 2.6)):
        bookcase_z(IS, s * W, -s, z0, z1, 0.0, 12.0, seed=int(z0) + s)
F.objects(False)
# дальняя стена: круглое окно в звёздное небо, полки с зельями
IS.frame_xy(K.ngon(0, 11.0, 4.6, 16), K.ngon(0, 11.0, 4.0, 16), ZF + 0.88, ZF + 1.4, STONE2)
IG.prism_xy(K.ngon(0, 11.0, 4.0, 16), ZF + 0.9, ZF + 0.94, NIGHTB)
IG.prism_xy(star(-1.6, 12.4, 0.5, 4, 0.35), ZF + 0.94, ZF + 0.98, "F4F0FF")
IG.prism_xy(star(1.8, 10.0, 0.35, 4, 0.35), ZF + 0.94, ZF + 0.98, "F4F0FF")
IG.prism_xy(star(0.6, 13.6, 0.25, 4, 0.35), ZF + 0.94, ZF + 0.98, "F4F0FF")
moon = [(1.4 + 1.1 * math.cos(t), 12.6 + 1.1 * math.sin(t)) for t in [math.pi * (0.4 + 1.2 * k / 8) for k in range(9)]]
moon += [(1.85 + 0.85 * math.cos(t), 12.75 + 0.85 * math.sin(t)) for t in [math.pi * (1.55 - 1.0 * k / 8) for k in range(9)]]
IG.prism_xy(moon, ZF + 0.94, ZF + 0.98, "FFF0B0")
for k in range(8):
    t = 2 * math.pi * k / 8
    IS.box(4.3 * math.cos(t) - 0.12, 4.3 * math.cos(t) + 0.12, 11.0 + 4.3 * math.sin(t) - 0.12, 11.0 + 4.3 * math.sin(t) + 0.12,
           ZF + 1.4, ZF + 1.6, GOLD)
F.objects(True)
for s in (-1, 1):
    x0 = s * 8.0
    for y in (3.0, 5.6, 8.2):
        IS.box(x0 - 2.6, x0 + 2.6, y, y + 0.2, ZF + 0.88, ZF + 2.0, WOOD)
        for k in range(5):
            x = x0 - 2.0 + 1.0 * k
            col = ("B070F0", GREEN, MAGIC, "FF70B0", "FFB040")[(k + int(y) + s) % 5]
            IG.prism_xz(K.ngon(x, ZF + 1.45, 0.28, 6), y + 0.2, y + 0.9, col)
            IS.prism_xz(K.ngon(x, ZF + 1.45, 0.12, 6), y + 0.9, y + 1.3, WOOD2)
    IS.box(x0 - 2.6, x0 + 2.6, 0.0, 3.0, ZF + 0.88, ZF + 2.0, WOOD2)
F.objects(False)
# котёл слева, стол алхимика справа
F.objects(True)
cauldron(IS, IG, -10.4, -9.0, r=1.5)
TX, TZ = 10.6, -9.6
IS.box(TX - 1.5, TX + 1.5, 2.6, 2.9, TZ - 2.6, TZ + 2.6, WOOD)
for e in (-1, 1):
    for f in (-1, 1):
        IS.box(TX + e * 1.3 - 0.15, TX + e * 1.3 + 0.15, 0.0, 2.6, TZ + f * 2.4 - 0.15, TZ + f * 2.4 + 0.15, WOOD2)
IS.box(TX - 0.9, TX + 0.5, 2.9, 3.05, TZ - 1.0, TZ + 0.6, PARCH)  # раскрытая книга
IS.box(TX - 0.95, TX + 0.55, 2.9, 2.98, TZ - 0.24, TZ - 0.16, "8A2A2A")
for k, (dx, dz, col) in enumerate(((0.6, -1.8, GREEN), (-0.6, 1.4, "B070F0"), (0.7, 1.9, MAGIC), (-0.2, -2.0, "FF70B0"))):
    IG.prism_xz(K.ngon(TX + dx, TZ + dz, 0.3, 8), 2.9, 3.4, col)
    IS.prism_xz(K.ngon(TX + dx, TZ + dz, 0.1, 6), 3.4, 3.9, "C8E0F0")
for dz in (-0.6, 0.9):  # свечи на столе
    IS.prism_xz(K.ngon(TX + 1.0, TZ + dz, 0.12, 6), 2.9, 3.5, PARCH)
    IG.prism_xz(K.ngon(TX + 1.0, TZ + dz, 0.07, 4), 3.5, 3.7, "FFD070")
F.objects(False)
# армиллярная сфера над постаментом и парящие свечи
F.objects(True)
SY = 14.6
ring_y(IS, 0.0, -3.0, 2.2, 2.45, SY - 0.12, SY + 0.12, GOLD, n=16)
IS.frame_xy(K.ngon(0.0, SY, 2.45, 16), K.ngon(0.0, SY, 2.2, 16), -3.12, -2.88, GOLD)
IS.frame_zy(K.ngon(-3.0, SY, 2.1, 16), K.ngon(-3.0, SY, 1.88, 16), -0.11, 0.11, "C89A3A")
IG.prism_xz(K.octa(0.0, -3.0, 0.5, 0.5, 0.2), SY - 0.5, SY + 0.5, "FFD070")
IS.box(-0.05, 0.05, SY + 2.4, C - 0.6, -3.05, -2.95, IRON)
F.objects(False)
for k in range(10):
    t = 2 * math.pi * k / 10
    x, z = 7.0 * math.cos(t), -3.0 + 6.0 * math.sin(t)
    if z > 6.0:
        continue
    y = 9.5 + 1.2 * rng(k, 9)
    IS.prism_xz(K.ngon(x, z, 0.16, 6), y, y + 0.8, PARCH)
    IG.prism_xz(K.ngon(x, z, 0.09, 4), y + 0.8, y + 1.05, "FFD070")
# магический круг и руны вокруг постамента
px, pz = PED
ring_y(IG, px, pz, 5.4, 5.7, 0.02, 0.06, MAGIC, n=24)
ring_y(IG, px, pz, 6.6, 6.75, 0.02, 0.06, MAGIC, n=24)
for k in range(12):
    t = 2 * math.pi * (k + 0.5) / 12
    x, z = px + 6.15 * math.cos(t), pz + 6.15 * math.sin(t)
    IG.prism_xz(star(x, z, 0.3, 4, 0.4) if k % 3 else K.ngon(x, z, 0.22, 3), 0.02, 0.07, MAGIC)
# постамент: серая каменная тумба в две ступени с голубыми рунами
IR.prism_xz(K.ngon(px, pz, 4.1, 8), 0.0, 0.5, STONE2)
IS.prism_xz(K.ngon(px, pz, 3.5, 8), 0.5, TOP - 0.1, STONE)
IS.prism_xz(K.ngon(px, pz, 3.7, 8), TOP - 0.1, TOP, "8A8EA0")
for k in range(8):
    t = 2 * math.pi * k / 8
    x, z = px + 3.55 * math.cos(t), pz + 3.55 * math.sin(t)
    IG.prism_xz(K.ngon(x, z, 0.14, 4), 0.62, 0.92, MAGIC)
B.lift_leaves(IS, WOOD2, IRON)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, STONE)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "565A6C")
SL.box(-FX - 0.5, FX + 0.5, 16.6, 17.4, -FZ - 0.5, FZ + 0.5, STONE2)
for e in (-1, 1):
    tx, tz = e * (FX - 0.6), -FZ - 0.9
    SL.prism_xz(K.ngon(tx, tz, 2.5, 8), -0.1, 13.9, STONE)
    SL.cone([(x, 13.9, z) for x, z in K.ngon(tx, tz, 2.95, 8)], (tx, 18.4, tz), SLATE)
SL.box(OX - 3.6, OX + 3.6, 9.0, 15.8, -FZ - 2.6, -FZ, STONE)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 1500, (0.9, 0.9, 1.0)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Cauldron", (-10, 5, -9), 500, (0.5, 1.0, 0.4))])
