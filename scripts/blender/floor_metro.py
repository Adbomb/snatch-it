"""Этаж «Улитка-метро» музея-небоскрёба (пятая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — старая станция метро. Снаружи — вестибюль в белой «метро»-плитке с синим и жёлтым поясами,
большие арочные окна в зелёных чугунных рамах, вход в подземку — лестница вниз под стеклянным козырьком на
чугунных опорах, у входа — столб-указатель с цветным диском, круглые часы, карта линий, скамья, автомат с
жетонами; бока — вагоны метро вдоль стен (синие, с окнами, дверями и полосой); сзади — пути и светофор. Внутри —
подземная платформа: плиточные стены с поясами, колонны, у дальней стены — вагон с открытыми дверями на путях,
жёлтая линия края, скамьи, табло, часы над путями, карта линий, турникеты у лифта, лампы-шары; экспонат —
на круглом плиточном островке с жёлтой кромкой и кольцом рельсов.
Запуск: blender --background --factory-startup --python scripts/blender/floor_metro.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, ring_y, rng, slab  # noqa: E402

TILE, TILE2, BLUE, BLUE2, YEL, GREEN, GREEN2 = "F2F0E8", "DCD8CC", "2A5AB0", "1E3E80", "FFC82A", "2E7A5A", "1E5A40"
STEEL, STEEL2, RAIL, DARK, CAR, CAR2, GLASS = "C8CCD4", "7A808C", "6A6A72", "22242C", "3A7AD8", "2A5AB0", "BFE4FF"
LINES = ("E83A3A", "3AB04A", "2A6AE0", "FFB02A", "A04AE0")

F = B.Floor("SW", "SubwaySnail", quiet=(TILE2, DARK, "5A5A60"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def car_side(p, g, axis, fixed, out, a0, a1, y0, h, doors=(), open_=False):
    """Бок вагона на стене или у стены: корпус, крыша, полоса, окна, двери, колёсные тележки."""
    pr = p.prism_xy if axis == "z" else p.prism_zy
    gp = g.prism_xy if axis == "z" else g.prism_zy

    def d(k):
        return fixed + out * k

    slab(p, axis, fixed, out, 1.4, a0, a1, y0 + 0.8, y0 + h, CAR)
    slab(p, axis, fixed, out, 1.5, a0 + 0.3, a1 - 0.3, y0 + h, y0 + h + 0.5, STEEL)
    slab(p, axis, fixed, out, 1.48, a0, a1, y0 + 1.6, y0 + 2.0, "F4F4F4")
    for a in (a0 + 2.0, a1 - 2.0):  # тележки с колёсами
        slab(p, axis, fixed, out, 1.2, a - 1.6, a + 1.6, y0, y0 + 0.8, DARK)
        for e in (-1, 1):
            pr(K.ngon(a + e * 0.9, y0 + 0.45, 0.45, 8), *sorted((d(1.2), d(1.3))), RAIL)
    n = int((a1 - a0) // 2.6)
    for k in range(n):
        a = a0 + 1.3 + (a1 - a0 - 2.6) * k / max(1, n - 1)
        if any(abs(a - dd) < 1.6 for dd in doors):
            continue
        gp(K.rect(a - 0.8, a + 0.8, y0 + 2.4, y0 + h - 0.6), *sorted((d(1.4), d(1.44))), GLASS)
    for dd in doors:
        if open_:
            gp(K.rect(dd - 1.0, dd + 1.0, y0 + 0.8, y0 + h - 0.4), *sorted((d(1.4), d(1.44))), "FFF0C8")
        else:
            slab(p, axis, fixed, out, 1.5, dd - 1.0, dd + 1.0, y0 + 0.8, y0 + h - 0.4, CAR2)
            gp(K.rect(dd - 0.8, dd - 0.1, y0 + 2.6, y0 + h - 0.8), *sorted((d(1.5), d(1.54))), GLASS)
            gp(K.rect(dd + 0.1, dd + 0.8, y0 + 2.6, y0 + h - 0.8), *sorted((d(1.5), d(1.54))), GLASS)


def clock(p, g, x, y, z, r, axis="z"):
    """Станционные часы: обод, циферблат, стрелки (один круг — не «лицо»)."""
    pr = p.prism_xy if axis == "z" else p.prism_zy
    gr = g.prism_xy if axis == "z" else g.prism_zy
    a = x if axis == "z" else z
    d = z if axis == "z" else x
    pr(K.ngon(a, y, r, 16), d - 0.3, d + 0.3, DARK)
    gr(K.ngon(a, y, r * 0.86, 16), d - 0.34, d - 0.3, "FFFBEA")
    pr([(a - 0.06, y), (a + 0.06, y), (a + 0.06, y + r * 0.7), (a - 0.06, y + r * 0.7)], d - 0.4, d - 0.34, DARK)
    pr([(a, y - 0.06), (a + r * 0.5, y - 0.06), (a + r * 0.5, y + 0.06), (a, y + 0.06)], d - 0.4, d - 0.34, DARK)
    for k in range(12):
        t = 2 * math.pi * k / 12
        pr(K.rect(a + r * 0.72 * math.cos(t) - 0.05, a + r * 0.72 * math.cos(t) + 0.05, y + r * 0.72 * math.sin(t) - 0.05,
                  y + r * 0.72 * math.sin(t) + 0.05), d - 0.38, d - 0.34, DARK)


def route_map(p, g, axis, fixed, out, a, y, w, h):
    """Карта линий: тёмная доска, цветные ломаные линии, белые станции."""
    slab(p, axis, fixed, out, 1.1, a - w / 2, a + w / 2, y - h / 2, y + h / 2, DARK)
    for k in range(4):
        yy = y - h * 0.3 + h * 0.2 * k
        x0 = a - w * 0.42
        pts = [(x0, yy), (a - w * 0.1, yy), (a + w * 0.05, yy + h * 0.12 * (1 if k % 2 else -1)), (a + w * 0.42, yy + h * 0.12 * (1 if k % 2 else -1))]
        for q0, q1 in zip(pts, pts[1:]):
            if axis == "z":
                beam(p, (q0[0], q0[1], fixed + out * 1.15), (q1[0], q1[1], fixed + out * 1.15), 0.14, 0.06, LINES[k])
            else:
                beam(p, (fixed + out * 1.15, q0[1], q0[0]), (fixed + out * 1.15, q1[1], q1[0]), 0.14, 0.06, LINES[k])
        for q in pts:
            if axis == "z":
                p.box(q[0] - 0.14, q[0] + 0.14, q[1] - 0.14, q[1] + 0.14, *sorted((fixed + out * 1.15, fixed + out * 1.22)), "FFFFFF")
            else:
                p.box(*sorted((fixed + out * 1.15, fixed + out * 1.22)), q[1] - 0.14, q[1] + 0.14, q[0] - 0.14, q[0] + 0.14, "FFFFFF")


def bench(p, x, z, along_x=True):
    """Скамья: деревянное сиденье и спинка на стальных ножках."""
    if along_x:
        p.box(x - 1.8, x + 1.8, 1.0, 1.25, z - 0.5, z + 0.5, "B07A44")
        p.box(x - 1.8, x + 1.8, 1.25, 2.4, z + 0.4, z + 0.55, "B07A44")
        for e in (-1, 1):
            p.box(x + e * 1.5 - 0.1, x + e * 1.5 + 0.1, 0.0, 1.0, z - 0.4, z + 0.4, STEEL2)
    else:
        p.box(x - 0.5, x + 0.5, 1.0, 1.25, z - 1.8, z + 1.8, "B07A44")
        for e in (-1, 1):
            p.box(x - 0.4, x + 0.4, 0.0, 1.0, z + e * 1.5 - 0.1, z + e * 1.5 + 0.1, STEEL2)


# ══ ФАСАД: вестибюль метро ════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, TILE, TILE, DARK)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "5A5A60")
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.2, GREEN2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.2, 15.0, TILE)
    for k in range(int(2 * half // 2.0)):  # плитка «кабанчик» рядами (выступ через ряд)
        for r in range(3):
            a = -half + 2.0 * k + (1.0 if r % 2 else 0.0)
            y = 12.0 + 1.0 * r
            if a + 1.9 > half:
                continue
            slab(FR, axis, fixed, out, 0.96, a + 0.06, a + 1.94, y + 0.06, y + 0.94, (TILE, TILE2)[(k + r) % 2])
    slab(FR, axis, fixed, out, 1.0, -half, half, 11.2, 12.0, BLUE)
    slab(FR, axis, fixed, out, 1.0, -half, half, 2.0, 2.5, YEL)
    slab(FR, axis, fixed, out, 1.88, -half - 0.6, half + 0.6, 15.0, 15.9, GREEN)
    slab(FR, axis, fixed, out, 0.88, -half, half, 15.9, 18.9, TILE2)
    slab(FS, axis, fixed, out, 1.0, -half, half, 17.0, 17.5, BLUE)
    if axis == "x":  # бока: вагоны вдоль стен
        car_side(FS, FG, axis, fixed, out, -15.6, -0.6, -0.1, 5.2, doors=(-8.1,))
        car_side(FS, FG, axis, fixed, out, 0.6, 15.6, -0.1, 5.2, doors=(8.1,))
        for z in (-8.0, 8.0):  # арочные окна над вагонами
            FG.prism_zy(K.rect(z - 3.0, z + 3.0, 6.6, 10.4), *sorted((fixed + out * 0.9, fixed + out * 0.94)), GLASS)
            FS.frame_zy(K.rect(z - 3.3, z + 3.3, 6.3, 10.7), K.rect(z - 3.0, z + 3.0, 6.6, 10.4), *sorted((fixed + out * 0.88, fixed + out * 1.2)),
                        GREEN)
            for m in (-1, 1):
                slab(FS, axis, fixed, out, 1.1, z + m * 1.0 - 0.08, z + m * 1.0 + 0.08, 6.6, 10.4, GREEN)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# перед: большие арочные окна в чугунных рамах
for ax in (-13.2, -8.0, 8.0, 13.2):  # четыре узких арочных окна ритмом (пара широких окон у двери читалась бы «лицом»)
    arch = [(ax - 2.2, 3.0), (ax + 2.2, 3.0)] + [(ax + 2.2 * math.cos(math.pi * k / 6), 9.4 + 1.4 * math.sin(math.pi * k / 6)) for k in range(7)]
    inner = [(ax - 1.85, 3.4), (ax + 1.85, 3.4)] + [(ax + 1.85 * math.cos(math.pi * k / 6), 9.4 + 1.15 * math.sin(math.pi * k / 6))
                                                   for k in range(7)]
    FG.prism_xy(inner, -FZ - 0.94, -FZ - 0.9, GLASS)
    FS.frame_xy(arch, inner, -FZ - 1.4, -FZ - 0.88, GREEN)
    FS.box(ax - 0.1, ax + 0.1, 3.4, 10.5, -FZ - 1.2, -FZ - 0.88, GREEN)
    FS.box(ax - 1.85, ax + 1.85, 7.0, 7.2, -FZ - 1.2, -FZ - 0.88, GREEN)
# вход в подземку: проём, лестница вниз, стеклянный козырёк на чугунных опорах, ограждение
FS.box(-4.4, 4.4, 1.2, 10.2, -FZ - 1.0, -FZ - 0.88, DARK)
for k in range(5):  # ступени вниз (утоплены в тротуар перед входом)
    FS.box(-3.6, 3.6, -0.1 - 0.15 * k, 0.0 - 0.15 * k, -FZ - 1.0 - 1.0 * k, -FZ - 2.0 - 1.0 * k, (STEEL2, RAIL)[k % 2])
FG.box(-4.0, 4.0, 1.2, 9.0, -FZ - 1.06, -FZ - 1.0, "FFE6A0")
for s in (-1, 1):
    for z in (-FZ - 1.2, -FZ - 6.2):
        FS.prism_xz(K.ngon(s * 4.4, z, 0.2, 6), 0.0, 8.6, GREEN2)
    beam(FS, (s * 4.4, 1.2, -FZ - 6.2), (s * 4.4, 1.2, -FZ - 1.2), 0.14, 0.14, GREEN2)
    for k in range(5):
        z = -FZ - 1.8 - 1.0 * k
        beam(FS, (s * 4.4, 0.0, z), (s * 4.4, 1.2, z), 0.08, 0.08, GREEN2)
FS.box(-5.0, 5.0, 8.6, 8.8, -FZ - 6.8, -FZ - 0.88, GREEN)
FG.box(-4.8, 4.8, 8.8, 8.9, -FZ - 6.6, -FZ - 1.0, "CFF0E6")
for k in range(6):
    z = -FZ - 1.4 - 1.0 * k
    FS.box(-4.8, 4.8, 8.9, 9.1, z - 0.08, z + 0.08, GREEN)
# указатель с цветным диском, часы, карта линий, скамья, автомат с жетонами
FS.prism_xz(K.ngon(-7.0, -FZ - 6.0, 0.16, 6), 0.0, 8.0, GREEN2)
FS.prism_xy(K.ngon(-7.0, 8.6, 1.2, 16), -FZ - 6.2, -FZ - 5.8, LINES[0])
FS.prism_xy(K.ngon(-7.0, 8.6, 0.8, 16), -FZ - 6.26, -FZ - 6.2, "FFFFFF")
FS.box(-7.5, -6.5, 8.2, 9.0, -FZ - 6.3, -FZ - 6.26, LINES[2])
clock(FS, FG, 0.0, 12.6, -FZ - 1.3, 1.6)
route_map(FS, FG, "z", -FZ - 5.2, -1, -14.6, 4.6, 3.6, 3.6)  # отдельностоящий стенд со схемой
for x in (-16.0, -13.2):
    FS.box(x - 0.12, x + 0.12, 0.0, 2.8, -FZ - 5.4, -FZ - 5.2, GREEN2)
bench(FS, 11.0, -FZ - 3.2)
FS.box(14.6, 16.6, 0.0, 4.8, -FZ - 2.8, -FZ - 1.4, BLUE)
FG.box(15.0, 16.2, 3.0, 4.2, -FZ - 2.84, -FZ - 2.8, "6AE0FF")
FS.box(15.2, 16.0, 1.6, 2.2, -FZ - 2.9, -FZ - 2.8, YEL)
# тыл: рельсы со шпалами и светофор
for k in range(16):
    x = -FX + 2.3 * k
    FS.box(x, x + 0.8, -0.1, 0.1, FZ + 1.4, FZ + 4.4, "6A4A30")
for z in (FZ + 2.0, FZ + 3.8):
    FS.box(-FX, FX, 0.1, 0.35, z - 0.1, z + 0.1, RAIL)
FS.prism_xz(K.ngon(12.0, FZ + 5.4, 0.2, 6), 0.0, 6.0, DARK)
FS.box(11.5, 12.5, 6.0, 8.6, FZ + 5.2, FZ + 5.7, DARK)
for k, col in enumerate(("E83A3A", "FFB02A", "3AE05A")):
    FG.prism_xy(K.ngon(12.0, 8.1 - 0.8 * k, 0.28, 8), FZ + 5.1, FZ + 5.2, col)

# ══ ИНТЕРЬЕР: подземная платформа ═════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.4
IQ.plane([(-W, 0.02, ZF + 5.4), (W, 0.02, ZF + 5.4), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "8A8A90")
for i in range(-8, 8):  # плитка платформы
    for j in range(-4, 8):
        if (i + j) % 2:
            IQ.box(2.1 * i + 0.05, 2.1 * i + 2.05, 0.02, 0.04, 2.1 * j + 0.05, 2.1 * j + 2.05, "9A9AA0")
IQ.box(-W, W, 0.04, 0.07, ZF + 5.4, ZF + 6.0, YEL)
IR.box(-W, W, -0.6, 0.0, ZF, ZF + 5.4, DARK)  # путевая яма у дальней стены
for z in (ZF + 1.6, ZF + 3.6):
    IS.box(-W, W, 0.0, 0.25, z - 0.1, z + 0.1, RAIL)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.0, BLUE2)
        slab(IR, axis, fixed, out, 0.88, a0, a1, 1.0, C if not gap else DOOR[1] + 0.1, TILE)
        for r in range(8):  # плитка рядами: четыре ряда под синим поясом, четыре над ним
            y = 1.2 + 1.0 * r if r < 4 else 6.5 + 1.0 * (r - 4)
            if gap and y + 1.0 > DOOR[1]:
                continue
            for k in range(int((a1 - a0) // 2.0)):
                a = a0 + 2.0 * k + (1.0 if r % 2 else 0.0)
                if a + 1.9 > a1:
                    continue
                slab(IR, axis, fixed, out, 0.96, a + 0.06, a + 1.94, y + 0.06, y + 0.94, (TILE, TILE2)[(k + r) % 2])
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, TILE)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, YEL)
    slab(IR, axis, fixed, out, 1.0, -half, half, 5.2, 6.0, BLUE)
    slab(IR, axis, fixed, out, 1.0, -half, half, 6.0, 6.3, YEL)
    slab(IR, axis, fixed, out, 1.6, -half, half, 14.8, 15.6, GREEN)
# вагон у дальней стены с открытыми дверями
car_side(IS, IG, "z", ZF + 3.2, 1, -15.0, 15.0, 0.0, 6.0, doors=(-7.0, 7.0), open_=True)
IS.box(-15.0, 15.0, 0.0, 6.5, ZF + 0.4, ZF + 3.2, CAR2)
# колонны в плитке, скамьи, табло, часы, карта, турникеты у лифта, лампы-шары
for x in (-10.0, 10.0):
    for z in (-6.0, 4.0):
        IR.box(x - 0.9, x + 0.9, 0.0, C, z - 0.9, z + 0.9, TILE)
        IS.box(x - 1.0, x + 1.0, 5.2, 6.0, z - 1.0, z + 1.0, BLUE)
        IS.box(x - 1.0, x + 1.0, 0.0, 1.0, z - 1.0, z + 1.0, BLUE2)
for s in (-1, 1):
    bench(IS, s * 13.6, -1.0, along_x=False)
    route_map(IS, IG, "x", s * W, -s, 4.0, 9.6, 6.0, 4.2)
    for x in (s * 4.6, s * 6.8):  # турникеты: стойки со стеклянными створками
        IS.box(x - 0.35, x + 0.35, 0.0, 2.2, 8.4, 9.6, STEEL)
        IG.box(x - 0.2, x + 0.2, 2.2, 2.26, 8.6, 9.4, "3AE05A")
    IG.box(*sorted((s * 5.0, s * 6.4)), 0.9, 2.0, 8.98, 9.02, "BFE8FF")
IS.box(-4.0, 4.0, 9.0, 10.6, ZF + 5.6, ZF + 6.0, DARK)
for k in range(5):
    IG.box(-3.6 + 1.5 * k, -2.6 + 1.5 * k, 9.4, 10.2, ZF + 6.0, ZF + 6.04, LINES[k])
for x in (-6.0, 6.0):
    IS.prism_xz(K.ngon(x, ZF + 5.8, 0.08, 4), 10.6, C, DARK)
clock(IS, IG, 0.0, 12.4, ZF + 5.8, 1.3)
IS.prism_xz(K.ngon(0.0, ZF + 5.8, 0.08, 4), 13.7, C, DARK)
for x in (-8.0, 0.0, 8.0):
    for z in (-10.0, 0.0, 8.0):
        if x == 0.0 and z == 0.0:
            continue
        IS.prism_xz(K.ngon(x, z, 0.05, 4), C - 1.8, C, DARK)
        IG.prism_xz(K.octa(x, z, 0.6, 0.6, 0.24), C - 2.6, C - 1.8, "FFF4D0")
# островок-постамент: плитка, жёлтая кромка, кольцо рельсов со шпалами
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, TOP - 0.2, TILE)
IS.prism_xz(K.ngon(px, pz, 4.1, 16), TOP - 0.2, TOP, YEL)
IQ.prism_xz(K.ngon(px, pz, 3.6, 16), TOP - 0.02, TOP + 0.02, TILE2)
for k in range(16):
    t = 2 * math.pi * k / 16
    IS.box(px + 5.0 * math.cos(t) - 0.5, px + 5.0 * math.cos(t) + 0.5, 0.0, 0.14, pz + 5.0 * math.sin(t) - 0.5, pz + 5.0 * math.sin(t) + 0.5,
           "6A4A30")
ring_y(IS, px, pz, 4.6, 4.75, 0.14, 0.34, RAIL, n=16)
ring_y(IS, px, pz, 5.25, 5.4, 0.14, 0.34, RAIL, n=16)
B.lift_leaves(IS, BLUE2, YEL)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, TILE)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "5A5A60")
SL.box(-FX - 1.9, FX + 1.9, 15.0, 15.9, -FZ - 1.9, FZ + 1.9, GREEN)
SL.box(-FX - 0.3, FX + 0.3, 11.2, 12.0, -FZ - 0.3, FZ + 0.3, BLUE)
for s in (-1, 1):
    SL.box(s * FX - 0.6, s * FX + 0.6, 0.0, 5.6, -15.6, 15.6, CAR)
SL.box(-5.0, 5.0, 8.6, 8.9, -FZ - 6.8, -FZ, GREEN)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 2800, (1.0, 0.97, 0.9)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.97, 0.9)),
                                                   ("Train", (0, 4, -12), 800, (1.0, 0.9, 0.6))])
