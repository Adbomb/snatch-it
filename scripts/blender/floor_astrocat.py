"""Этаж «Кот в шлеме» музея-небоскрёба (четвёртая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — кошачья обсерватория. Снаружи — тёплый дом из персиковых блоков с фиолетовыми поясами и крышей-
парапетом с «кошачьими ушками»; посередине фасада — огромный белый ступенчатый купол обсерватории с открытой щелью,
из щели наклонно торчит латунный телескоп; по углам — кошачьи деревья: столбы в канате с полками-лежанками; на стене
следы лап, круглые окна-иллюминаторы, огромный клубок ниток с размотанной нитью, Сатурн с кольцом над входом,
ракета на боку, миски и рыбка-флюгер сзади. Внутри — планетарий для котов: тёмно-фиолетовый звёздный зал, висящие
планеты, кошачьи полки-лесенки вдоль стен, когтеточки, клубки, большой латунный телескоп на треноге, модель
ракеты, мягкие лежанки; экспонат — на круглой стартовой площадке в оранжево-белых полосах под прожектором.
Запуск: blender --background --factory-startup --python scripts/blender/floor_astrocat.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, ring_y, rng, slab, taper, tube  # noqa: E402

PEACH, PEACH2, PEACH3, VIOLET, VIOLET2 = "F2B48A", "E09A70", "F8CCA8", "6A4AC8", "4A2E9A"
DOME, DOME2, SLIT, BRASS, BRASS2 = "F4F4FA", "D8DCE8", "1E1A3A", "E0A840", "B07A24"
ROPE, ROPE2, WOOD, WOOD2, CUSHION, CUSHION2 = "D8B880", "C09A60", "B07A48", "8A5A34", "FF7A9A", "6AC8F0"
NIGHT, NIGHT2, NIGHT3, STAR = "1A1440", "2A2060", "3A2E80", "FFF6D0"
SATURN, SATURN2, MARS, EARTH, EARTH2, MOONC = "F2C070", "D89A50", "E0603A", "3A8AE0", "4AC06A", "D8D8E0"
YARN, YARN2, ROCKET, ROCKET2, ORANGE, WHITE = "FF5A8A", "8A6AF0", "F4F4F8", "E83A3A", "FF8A2A", "FFFFFF"

F = B.Floor("AC", "AstroCat", quiet=(CUSHION, CUSHION2, NIGHT, NIGHT2, NIGHT3), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def cat_tree(p, x, z, h, levels):
    """Кошачье дерево: столб в канате (кольца двух тонов), полки-лежанки с подушками на разной высоте."""
    for k in range(int(h / 0.5)):
        p.prism_xz(K.ngon(x, z, 0.5, 8), 0.5 * k, 0.5 * k + 0.5, ROPE if k % 2 else ROPE2)
    for k, (y, dx, dz) in enumerate(levels):
        p.box(x + dx - 1.4, x + dx + 1.4, y, y + 0.4, z + dz - 1.2, z + dz + 1.2, WOOD)
        p.box(x + dx - 1.1, x + dx + 1.1, y + 0.4, y + 0.75, z + dz - 0.9, z + dz + 0.9, CUSHION if k % 2 else CUSHION2)


def planet(p, x, y, z, r, c1, c2=None, ring=None):
    """Планета: гранёный шар из трёх ярусов, полоса, кольцо (Сатурн)."""
    p.prism_xz(K.ngon(x, z, r * 0.72, 10), y - r, y - r * 0.55, c1)
    p.prism_xz(K.ngon(x, z, r, 10), y - r * 0.55, y + r * 0.55, c2 or c1)
    p.prism_xz(K.ngon(x, z, r * 0.72, 10), y + r * 0.55, y + r, c1)
    if ring:
        ring_y(p, x, z, r * 1.25, r * 1.8, y - 0.06, y + 0.06, ring, n=14)


def yarn(p, x, z, y, r, c1, c2):
    """Клубок: шар и несколько ниток-полос по нему."""
    planet(p, x, y + r, z, r, c1, c1)
    for k in range(3):
        t = math.pi * k / 3
        p.box(x - r * 1.02 * abs(math.cos(t)) - 0.05, x + r * 1.02 * abs(math.cos(t)) + 0.05, y + r * 0.2 + 0.5 * k * r * 0.6,
              y + r * 0.2 + 0.5 * k * r * 0.6 + 0.14, z - r * 1.02, z + r * 1.02, c2)


def paw(p, axis, fixed, out, a, y, d0=0.9, d1=1.0, color=VIOLET2):
    """След лапы на стене: подушечка и четыре пальчика."""
    lo, hi = sorted((fixed + out * d0, fixed + out * d1))
    pr = p.prism_xy if axis == "z" else p.prism_zy
    pr(K.octa(a, y, 0.45, 0.38, 0.16), lo, hi, color)
    for e, dy in ((-0.5, 0.45), (-0.18, 0.7), (0.18, 0.7), (0.5, 0.45)):
        pr(K.octa(a + e, y + dy, 0.15, 0.15, 0.06), lo, hi, color)


def rocket(p, g, x, y, z, s, axis_up=True):
    """Ракета: корпус, полоса, обтекатель-конус, иллюминатор, три стабилизатора, пламя."""
    p.prism_xz(K.ngon(x, z, 0.8 * s, 10), y, y + 3.6 * s, ROCKET)
    p.prism_xz(K.ngon(x, z, 0.82 * s, 10), y + 1.0 * s, y + 1.5 * s, ROCKET2)
    p.cone([(x + 0.8 * s * math.cos(t), y + 3.6 * s, z + 0.8 * s * math.sin(t)) for t in
            [2 * math.pi * k / 10 for k in range(10)]], (x, y + 5.2 * s, z), ROCKET2)
    for k in range(3):
        t = 2 * math.pi * k / 3
        c, sn = math.cos(t), math.sin(t)
        p.prism_xz([(x + 0.6 * s * c - 0.08 * sn, z + 0.6 * s * sn + 0.08 * c), (x + 1.5 * s * c - 0.08 * sn, z + 1.5 * s * sn + 0.08 * c),
                    (x + 1.5 * s * c + 0.08 * sn, z + 1.5 * s * sn - 0.08 * c), (x + 0.6 * s * c + 0.08 * sn, z + 0.6 * s * sn - 0.08 * c)],
                   y, y + 1.2 * s, ROCKET2)
    g.prism_xz(K.ngon(x, z, 0.5 * s, 8), y - 0.6 * s, y, "FFB030")


# ══ ФАСАД: дом-обсерватория ═══════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, PEACH2, PEACH2, NIGHT)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FR, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, 0.4, VIOLET2)  # цоколь-подиум
    slab(FR, axis, fixed, out, 0.88, -half, half, 0.4, 15.6, PEACH)
    for r in range(7):  # пояса блоков двух тонов
        y0 = 0.4 + 2.2 * r
        if r % 2:
            slab(FR, axis, fixed, out, 1.08, -half + 0.2, half - 0.2, y0 + 0.1, y0 + 2.1, PEACH3)
    slab(FS, axis, fixed, out, 1.3, -half - 0.4, half + 0.4, 15.6, 16.2, VIOLET)
    slab(FR, axis, fixed, out, 1.88, -half - 0.8, half + 0.8, 16.2, 17.2, VIOLET2)
    for k in range(int(2 * half // 6.0) + 1):  # парапет с «кошачьими ушками»
        a = -half + 1.5 + 6.0 * k
        if a > half - 1.0:
            break
        d0, d1 = sorted((fixed + out * 0.3, fixed + out * 1.6))
        pr = FS.prism_xy if axis == "z" else FS.prism_zy
        pr([(a - 1.4, 17.2), (a + 1.4, 17.2), (a + 0.9, 18.9), (a - 1.1, 18.4)], d0, d1, VIOLET)
        pr([(a - 0.8, 17.2), (a + 0.7, 17.2), (a + 0.5, 18.2), (a - 0.6, 17.9)], *sorted((fixed + out * 1.6, fixed + out * 1.7)),
           CUSHION)
    if axis == "x":  # бока: иллюминаторы и следы лап
        for z in (-9.0, 0.0, 9.0):
            d0, d1 = sorted((fixed + out * 0.88, fixed + out * 1.4))
            FS.frame_zy(K.ngon(z, 9.0, 2.0, 12), K.ngon(z, 9.0, 1.5, 12), d0, d1, BRASS)
            FG.prism_zy(K.ngon(z, 9.0, 1.5, 12), *sorted((fixed + out * 0.9, fixed + out * 0.95)), "8ACBFF")
        for k in range(5):
            paw(FS, axis, fixed, out, -14.0 + 7.0 * k, 3.0 + 1.6 * (k % 2), color=VIOLET2)
    if fi == 1:  # тыл: окна и следы лап
        for k in range(6):
            paw(FS, axis, fixed, out, -15.0 + 6.0 * k, 4.0 + 2.0 * (k % 2), color=VIOLET2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))

# перед: ступенчатый купол обсерватории (передняя половина), щель, телескоп
DX, DY, DZ, DR = 0.0, 5.0, -FZ - 0.4, 8.0
LAYERS = 7
for k in range(LAYERS):
    t0 = math.pi / 2 * k / LAYERS
    y0 = DY + DR * math.sin(t0)
    y1 = DY + DR * math.sin(math.pi / 2 * (k + 1) / LAYERS)
    r = DR * math.cos(t0)
    pts = [(DX + r * math.cos(a), DZ + r * math.sin(a)) for a in [math.pi + math.pi * m / 10 for m in range(11)]]
    FS.prism_xz(pts, y0, min(y1, 18.9), (DOME, DOME2)[k % 2])
for k in range(LAYERS):  # открытая щель по ступеням купола и латунные рельсы
    t0 = math.pi / 2 * k / LAYERS
    y0, y1 = DY + DR * math.sin(t0), min(DY + DR * math.sin(math.pi / 2 * (k + 1) / LAYERS), 18.9)
    r = DR * math.cos(t0) * math.cos(math.pi / 10)
    FS.box(-1.0, 1.0, y0, y1, DZ - r - 0.06, DZ - r + 0.6, SLIT)
    for e in (-1, 1):
        FS.box(e * 1.0 - 0.15, e * 1.0 + 0.15, y0, y1, DZ - r - 0.18, DZ - r + 0.6, BRASS2)
FR.box(-9.0, 9.0, 0.4, DY, -FZ - 3.0, -FZ, VIOLET2)  # барабан под куполом с дверью
FS.box(-2.2, 2.2, 0.4, 4.4, -FZ - 3.1, -FZ - 2.95, SLIT)
FS.frame_xy(K.octa(0.0, 2.7, 2.6, 2.6, 1.0), K.octa(0.0, 2.7, 2.2, 2.2, 0.8), -FZ - 3.2, -FZ - 2.95, BRASS)
for x in (-6.5, -4.5, 4.5, 6.5):  # узкие высокие окна барабана рядами (не пара «глаз» у двери)
    FS.frame_xy(K.rect(x - 0.75, x + 0.75, 0.9, 4.3), K.rect(x - 0.5, x + 0.5, 1.15, 4.05), -FZ - 3.2, -FZ - 2.95, BRASS)
    FG.prism_xy(K.rect(x - 0.5, x + 0.5, 1.15, 4.05), -FZ - 3.0, -FZ - 2.95, "8ACBFF")
TB0, TB1 = (0.0, 10.6, DZ - 4.5), (3.6, 16.4, DZ - 9.6)  # телескоп
beam(FS, TB0, TB1, 1.5, 1.5, BRASS)
beam(FS, TB0, ((TB0[0] + TB1[0]) / 2, (TB0[1] + TB1[1]) / 2, (TB0[2] + TB1[2]) / 2), 1.7, 1.7, BRASS2)
beam(FS, (TB1[0] - 0.2, TB1[1] - 0.2, TB1[2] + 0.4), (TB1[0] + 0.4, TB1[1] + 0.4, TB1[2] - 0.5), 2.3, 2.3, BRASS2)
FG.prism_xy(K.ngon(TB1[0] + 0.5, TB1[1] + 0.5, 0.8, 8), TB1[2] - 0.62, TB1[2] - 0.55, "BFE8FF")
FR.box(-FX - 0.2, -9.0, 12.0, 15.4, -FZ - 1.08, -FZ, NIGHT2)  # звёздный фриз по бокам от купола
FR.box(9.0, FX + 0.2, 12.0, 15.4, -FZ - 1.08, -FZ, NIGHT2)
for k in range(14):
    x = (-FX + 0.6 + 8.0 * rng(k, 5)) if k % 2 else (9.6 + 8.0 * rng(k, 5))
    y = 12.5 + 2.4 * rng(k, 6)
    sz = 0.14 + 0.12 * rng(k, 7)
    FG.box(x - sz, x + sz, y - sz, y + sz, -FZ - 1.14, -FZ - 1.08, STAR)
# Сатурн над входом слева, следы лап по фасаду, огромный клубок у правого угла
planet(FS, -12.5, 9.0, -FZ - 2.6, 2.0, SATURN, SATURN2, ring=BRASS)
planet(FS, 12.0, 9.6, -FZ - 2.0, 1.3, MARS)
planet(FS, 15.0, 7.0, -FZ - 1.6, 0.7, EARTH, EARTH2)
for k, (a, y) in enumerate(((-15.0, 2.0), (-12.6, 3.4), (12.0, 3.0), (14.4, 4.4), (10.8, 6.6))):
    paw(FS, "z", -FZ, -1, a, y, 0.88, 1.0)
yarn(FS, 13.0, -FZ - 4.0, 0.4, 1.8, YARN, "FF9AB8")
tube(FS, [(11.4, 0.6, -FZ - 4.6), (6.0, 0.48, -FZ - 5.4), (1.0, 0.48, -FZ - 4.8)], [0.18, 0.18, 0.18], 0.1, (0, 1, 0), YARN)
yarn(FS, -13.4, -FZ - 4.6, 0.4, 1.1, YARN2, "B8A8FF")
# кошачьи деревья по углам
for sx in (-1, 1):
    for sz in (-1, 1):
        x, z = sx * (FX + 1.6), sz * (FZ + 1.6)
        cat_tree(FS, x, z, 14.0, [(4.0, sx * 0.6, sz * 0.4), (8.6, -sx * 0.2, sz * 0.8), (13.0, sx * 0.4, 0.0)])
# бок: ракета у правой стены; сзади: миски
rocket(FS, FG, FX + 2.4, 0.4, 4.0, 2.0)
for k, (x, col) in enumerate(((-4.0, CUSHION2), (-1.0, CUSHION), (2.0, VIOLET))):
    FS.prism_xz(K.ngon(x, FZ + 2.0, 1.0, 10), 0.4, 0.9, col)
    FS.prism_xz(K.ngon(x, FZ + 2.0, 0.7, 10), 0.85, 0.92, "F4E6C8" if k else "6ACB8A")

# ══ ИНТЕРЬЕР: планетарий для котов ════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), NIGHT3)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.0, VIOLET2)
        slab(IQ, axis, fixed, out, 0.88, a0, a1, 1.0, 6.0 if not gap else DOOR[1] + 0.1, NIGHT3)
        if not gap:
            slab(IQ, axis, fixed, out, 0.88, a0, a1, 6.0, 11.0, NIGHT2)
    slab(IQ, axis, fixed, out, 0.88, -half, half, 11.0, C, NIGHT)
    if gap:
        slab(IQ, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 11.0, NIGHT2)
        slab(IR, axis, fixed, out, 1.88, -DOOR[0] - 1.4, DOOR[0] + 1.4, DOOR[1] + 0.1, DOOR[1] + 1.0, BRASS2)
        for s in (-1, 1):
            slab(IR, axis, fixed, out, 1.88, s * (DOOR[0] + 0.6), s * (DOOR[0] + 1.4), 0.0, DOOR[1] + 0.1, BRASS2)
    slab(IS, axis, fixed, out, 1.0, -half, half, 1.0, 1.3, BRASS)
for k in range(56):  # звёзды
    x = -W + 1.0 + (2 * W - 2.0) * rng(k, 11)
    z = ZF + 1.0 + (ZB - ZF - 2.0) * rng(k, 12)
    s = 0.1 + 0.14 * rng(k, 13)
    if k < 30:
        IG.box(x - s, x + s, C - 0.05, C - 0.01, z - s, z + s, STAR)
    elif k < 42:
        y = 7.0 + 10.0 * rng(k, 14)
        IG.box(x - s, x + s, y - s, y + s, ZF + 0.88, ZF + 0.92, STAR)
    else:
        sx = -1 if k % 2 else 1
        y = 7.0 + 10.0 * rng(k, 14)
        IG.box(*sorted((sx * (W - 0.88), sx * (W - 0.92))), y - s, y + s, z - s, z + s, STAR)
# висящие планеты (на нитях), Сатурн за экспонатом
for x, y, z, r, c1, c2, ring in ((-9.0, 13.0, -9.0, 2.2, SATURN, SATURN2, BRASS), (9.5, 14.0, -10.0, 1.4, MARS, MARS, None),
                                 (-10.5, 12.5, 4.0, 1.6, EARTH, EARTH2, None), (10.0, 12.0, 5.0, 1.0, MOONC, "B8B8C8", None),
                                 (0.0, 14.5, -12.0, 2.6, "B07AE0", "8A5AC8", "D8C8FF")):
    IS.box(x - 0.03, x + 0.03, y + r, C, z - 0.03, z + 0.03, "C8C8D8")
    planet(IS, x, y, z, r, c1, c2, ring=ring)
# кошачьи полки-лесенки вдоль боковых стен, когтеточки
for s in (-1, 1):
    wx = s * W
    for k in range(5):
        z = -12.0 + 4.6 * k
        y = 2.4 + 1.8 * k
        IS.box(*sorted((wx, wx - s * 2.4)), y, y + 0.35, z - 1.4, z + 1.4, WOOD)
        IS.box(*sorted((wx - s * 0.3, wx - s * 2.2)), y + 0.35, y + 0.65, z - 1.1, z + 1.1, (CUSHION, CUSHION2)[k % 2])
        IS.box(*sorted((wx - s * 2.2, wx - s * 2.35)), y - 1.6, y, z - 0.12, z + 0.12, WOOD2)
cat_tree(IS, -12.0, -11.0, 9.0, [(3.0, 0.6, 0.4), (6.0, -0.4, 0.6), (8.8, 0.2, 0.0)])
cat_tree(IS, 12.5, 8.5, 7.0, [(2.6, -0.6, 0.2), (6.8, 0.2, -0.4)])
# большой латунный телескоп на треноге (левее), модель ракеты (правее), клубки, лежанки
tx, tz = -9.5, 2.0
for k in range(3):
    t = 2 * math.pi * k / 3 + 0.3
    beam(IS, (tx, 4.0, tz), (tx + 1.8 * math.cos(t), 0.0, tz + 1.8 * math.sin(t)), 0.2, 0.2, WOOD2)
beam(IS, (tx - 1.6, 3.6, tz + 1.8), (tx + 1.8, 6.0, tz - 2.2), 1.0, 1.0, BRASS)
beam(IS, (tx + 1.2, 5.6, tz - 1.5), (tx + 2.0, 6.15, tz - 2.45), 1.3, 1.3, BRASS2)
beam(IS, (tx - 1.6, 3.6, tz + 1.8), (tx - 2.0, 3.3, tz + 2.3), 0.5, 0.5, BRASS2)
rocket(IS, IG, 10.5, 0.0, -2.0, 1.5)
for x, z, r, c1, c2 in ((-5.0, 6.0, 0.9, YARN, "FF9AB8"), (6.2, 7.0, 0.7, YARN2, "B8A8FF"), (5.0, -12.0, 0.8, CUSHION2, WHITE)):
    yarn(IS, x, z, 0.0, r, c1, c2)
for x, z, col in ((-13.0, 12.5, CUSHION), (13.0, -12.5, CUSHION2)):
    IS.prism_xz(K.ngon(x, z, 1.8, 10), 0.0, 0.5, VIOLET)
    IQ.prism_xz(K.ngon(x, z, 1.4, 10), 0.5, 0.8, col)
for k in range(4):  # дорожка следов лап к постаменту
    z = 9.5 - 2.2 * k
    IS.prism_xz(K.octa(0.9 * (1 if k % 2 else -1), z, 0.42, 0.36, 0.15), 0.0, 0.06, VIOLET)
# стартовая площадка: круглая, оранжево-белые полосы, латунный кант, огни
px, pz = PED
IR.box(px - 4.0, px + 4.0, 0.0, 0.5, pz - 4.0, pz + 4.0, NIGHT2)
for k in range(12):
    a0, a1 = 30 * k, 30 * (k + 1)
    ring_y(IS, px, pz, 0.0, 3.6, 0.5, TOP, (ORANGE, WHITE)[k % 2], n=12, a0=a0, a1=a1)
ring_y(IS, px, pz, 3.6, 3.9, 0.5, TOP + 0.1, BRASS, n=16)
for k in range(8):
    t = 2 * math.pi * k / 8
    IG.prism_xz(K.octa(px + 3.75 * math.cos(t), pz + 3.75 * math.sin(t), 0.16, 0.16, 0.06), TOP + 0.1, TOP + 0.25, "FFE070")
B.lift_leaves(IS, VIOLET2, BRASS)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, PEACH)
SL.box(-FX - 2.9, FX + 2.9, -1.0, 0.4, -FZ - 2.9, FZ + 2.9, VIOLET2)
SL.box(-FX - 1.9, FX + 1.9, 15.6, 17.2, -FZ - 1.9, FZ + 1.9, VIOLET)
for k in range(3):
    t0 = math.pi / 2 * k / 3
    r = DR * math.cos(t0)
    SL.prism_xz([(DX + r * math.cos(a), DZ + r * math.sin(a)) for a in [math.pi + math.pi * m / 6 for m in range(7)]],
                DY + DR * math.sin(t0), DY + DR * math.sin(math.pi / 2 * (k + 1) / 3), DOME)
beam(SL, TB0, TB1, 1.6, 1.6, BRASS)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 2600, (0.85, 0.8, 1.0)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.96, 0.9)),
                                                   ("Glow", (-9, 6, 2), 700, (1.0, 0.8, 0.5))])
