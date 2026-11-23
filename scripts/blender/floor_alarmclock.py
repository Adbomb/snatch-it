"""Этаж «Злой будильник» музея-небоскрёба (пятая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — часовая башня-мастерская. Снаружи — тёмный кирпич и песчаник с карнизами, в центре фасада —
огромный циферблат в латунной раме с римскими метками и стрелками, вокруг — открытые «окна» в механизм с
латунными шестернями, сцепленными друг с другом, над циферблатом на крыше — два огромных звонка будильника с
молоточком, внизу — дверь мастерской под козырьком-часами, маятник в стеклянном шкафу; бока — ряды разных часов
(круглые, квадратные, домики), шестерни; сзади — трубы и колокол. Внутри — мастерская часовщика: деревянный
пол, стены, увешанные часами, огромные шестерни на дальней стене, напольные часы с маятниками, верстак с
инструментами и лупой-лампой, полки с будильниками, свисающие цепи с гирями; экспонат — на огромной лежачей
латунной шестерне.
Запуск: blender --background --factory-startup --python scripts/blender/floor_clockwork.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab  # noqa: E402

BRICK, BRICK2, STONE, STONE2, DARK, WOOD, WOOD2, WOOD3 = "6A3A30", "5A2E26", "D8C49A", "BFA880", "2A2228", "A06A3A", "7A4E2A", "C8905A"
BRASS, BRASS2, COPPER, STEEL, FACE, RED, RED2, TEAL = "E0B048", "B08830", "C87A4A", "B8BCC4", "FFF6DC", "D83A2E", "A82A22", "3AA8A0"

F = B.Floor("AL", "AngryAlarmClock", quiet=(WOOD2, DARK, STONE2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def teeth_pts(cx, cy, r, n, depth=0.16):
    """Контур шестерни: n зубцов (по 4 точки на зуб)."""
    pts = []
    for k in range(n):
        t0 = 2 * math.pi * k / n
        dt = 2 * math.pi / n
        rr = r * (1 - depth)
        for f, rad in ((0.0, rr), (0.15, r), (0.5, r), (0.65, rr)):
            t = t0 + dt * f
            pts.append((cx + rad * math.cos(t), cy + rad * math.sin(t)))
    return pts


def gear(p, plane, cx, cy, d0, d1, r, n, col, hub=BRASS2, spokes=4):
    """Шестерня: зубчатый диск, утопленное поле, выпуклые спицы и ступица. plane: 'xy' (ось z), 'zy' (ось x), 'xz' (лежит)."""
    pr = {"xy": p.prism_xy, "zy": p.prism_zy, "xz": p.prism_xz}[plane]
    sg = 1 if d1 > d0 else -1
    pr(teeth_pts(cx, cy, r, n), d0, d1, col)
    pr(K.ngon(cx, cy, r * 0.66, 12), d1 - sg * 0.02, d1 + sg * 0.02, DARK)  # тёмное поле между спицами
    d0, d1 = d1, d1 + sg * 0.12
    for k in range(spokes):
        t = math.pi * k / spokes
        c, s = math.cos(t), math.sin(t)
        w = r * 0.09
        pr([(cx - c * r * 0.64 - s * w, cy - s * r * 0.64 + c * w), (cx + c * r * 0.64 - s * w, cy + s * r * 0.64 + c * w),
            (cx + c * r * 0.64 + s * w, cy + s * r * 0.64 - c * w), (cx - c * r * 0.64 + s * w, cy - s * r * 0.64 - c * w)],
           d0 + (d1 - d0) * 0.2, d1 - (d1 - d0) * 0.2, col)
    pr(K.ngon(cx, cy, r * 0.2, 8), d0 - 0.05 * (1 if d1 > d0 else -1), d1 + 0.05 * (1 if d1 > d0 else -1), hub)


def clock_face(p, g, plane, cx, cy, d, r, out, frame=BRASS, hands=DARK, hh=10.0, mm=2.0):
    """Циферблат: рама, светлое поле, метки (12), часовая и минутная стрелки — один круг, без «лица»."""
    pr = {"xy": p.prism_xy, "zy": p.prism_zy}[plane]
    gp = {"xy": g.prism_xy, "zy": g.prism_zy}[plane]
    a, b = sorted((d, d + out * 0.5))
    seg = 24 if r >= 2.0 else 12
    pr(K.ngon(cx, cy, r, seg), a, b, frame)
    c0, c1 = sorted((d + out * 0.5, d + out * 0.56))
    gp(K.ngon(cx, cy, r * 0.88, seg), c0, c1, FACE)
    m0, m1 = sorted((d + out * 0.56, d + out * 0.66))
    for k in range(12):
        if r < 2.0 and k % 3:
            continue  # на маленьких циферблатах — только четыре главные метки
        t = 2 * math.pi * k / 12
        L = r * (0.14 if k % 3 == 0 else 0.08)
        x, y = cx + r * 0.76 * math.cos(t), cy + r * 0.76 * math.sin(t)
        w = r * (0.035 if k % 3 == 0 else 0.022)
        pr([(x - math.sin(t) * w - math.cos(t) * L / 2, y + math.cos(t) * w - math.sin(t) * L / 2),
            (x - math.sin(t) * w + math.cos(t) * L / 2, y + math.cos(t) * w + math.sin(t) * L / 2),
            (x + math.sin(t) * w + math.cos(t) * L / 2, y - math.cos(t) * w + math.sin(t) * L / 2),
            (x + math.sin(t) * w - math.cos(t) * L / 2, y - math.cos(t) * w - math.sin(t) * L / 2)], m0, m1, hands)
    for ang, L, w in ((math.pi / 2 - 2 * math.pi * hh / 12, r * 0.5, r * 0.05), (math.pi / 2 - 2 * math.pi * mm / 12, r * 0.72, r * 0.035)):
        c, s = math.cos(ang), math.sin(ang)
        pr([(cx - s * w, cy + c * w), (cx + c * L - s * w * 0.4, cy + s * L + c * w * 0.4), (cx + c * L + s * w * 0.4, cy + s * L - c * w * 0.4),
            (cx + s * w, cy - c * w)], *sorted((d + out * 0.66, d + out * 0.76)), hands)
    pr(K.ngon(cx, cy, r * 0.07, 8), *sorted((d + out * 0.66, d + out * 0.8)), frame)


def bell(p, x, y, z, r, col=BRASS):
    """Звонок будильника: купол из ярусов, ножка."""
    for k, (rr, y0, y1) in enumerate(((1.0, 0.0, 0.25), (0.92, 0.25, 0.6), (0.74, 0.6, 0.9), (0.42, 0.9, 1.05))):
        p.prism_xz(K.ngon(x, z, r * rr, 12), y + r * y0, y + r * y1, col)
    p.prism_xz(K.ngon(x, z, r * 0.12, 6), y + r * 1.05, y + r * 1.4, BRASS2)


def wall_clock(p, g, axis, fixed, out, a, y, kind, s):
    """Настенные часы разных форм: круглые, квадратные, домик-ходики (по одному кругу на часы)."""
    pr = p.prism_xy if axis == "z" else p.prism_zy
    d0, d1 = sorted((fixed + out * 0.88, fixed + out * 1.2))
    if kind == 0:
        clock_face(p, g, "xy" if axis == "z" else "zy", a, y, fixed + out * 0.88, s, out, frame=(BRASS, COPPER, WOOD)[int(a) % 3],
                   hh=rng(a, y) * 12, mm=rng(y, a) * 12)
    elif kind == 1:
        pr(K.rect(a - s, a + s, y - s, y + s), d0, d1, (WOOD, TEAL, RED2)[int(abs(a)) % 3])
        clock_face(p, g, "xy" if axis == "z" else "zy", a, y, fixed + out * 1.2, s * 0.8, out, frame=BRASS2,
                   hh=rng(a, 1) * 12, mm=rng(2, a) * 12)
    else:
        pr([(a - s, y - s * 1.4), (a + s, y - s * 1.4), (a + s, y + s * 0.6), (a, y + s * 1.5), (a - s, y + s * 0.6)], d0, d1, WOOD2)
        pr([(a - s * 1.2, y + s * 0.5), (a, y + s * 1.7), (a + s * 1.2, y + s * 0.5), (a + s * 1.2, y + s * 0.8), (a, y + s * 2.0),
            (a - s * 1.2, y + s * 0.8)], *sorted((fixed + out * 0.88, fixed + out * 1.4)), RED2)
        clock_face(p, g, "xy" if axis == "z" else "zy", a, y - s * 0.2, fixed + out * 1.2, s * 0.6, out, frame=BRASS, hh=3, mm=9)
        if axis == "z":
            p.box(a - 0.06, a + 0.06, y - s * 3.2, y - s * 1.4, *sorted((fixed + out * 1.0, fixed + out * 1.06)), BRASS2)
            p.prism_xz(K.ngon(a, fixed + out * 1.03, s * 0.25, 6), y - s * 3.8, y - s * 3.2, BRASS)


def grandfather(p, g, x, z, face_out, h=9.0):
    """Напольные часы: корпус, капитель, циферблат, стеклянная дверца с маятником (лицом к +x/−x)."""
    p.box(x - 0.9, x + 0.9, 0.0, h, z - 1.0, z + 1.0, WOOD2)
    p.box(x - 1.05, x + 1.05, h, h + 0.5, z - 1.15, z + 1.15, WOOD)
    p.prism_zy([(z - 1.1, h + 0.5), (z + 1.1, h + 0.5), (z, h + 1.4)], x - 1.0, x + 1.0, WOOD)
    clock_face(p, g, "zy", z, h - 1.4, x + face_out * 0.9, 0.85, face_out, frame=BRASS, hh=7, mm=11)
    g.box(*sorted((x + face_out * 0.9, x + face_out * 0.95)), 1.2, h - 2.8, z - 0.6, z + 0.6, "BFE0E8")
    p.box(*sorted((x + face_out * 0.75, x + face_out * 0.85)), 2.2, h - 3.0, z - 0.04, z + 0.04, BRASS2)
    p.prism_zy(K.ngon(z, 2.4, 0.42, 10), *sorted((x + face_out * 0.7, x + face_out * 0.86)), BRASS)


# ══ ФАСАД: часовая башня-мастерская ═══════════════════════════════════════════════════════════════════════════
B.shell_planes(F, BRICK, BRICK, DARK)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, STONE2)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.4, STONE)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.4, 15.2, BRICK)
    for r in range(6):  # кладка
        y = 1.6 + 2.2 * r
        for k in range(int(2 * half // 2.4)):
            a = -half + 2.4 * k + (1.2 if r % 2 else 0.0)
            if a + 2.2 > half or rng(fi, r, k) < 0.6:
                continue
            if fi == 0 and -9.6 < a + 1.1 < 9.6 and y > 3.0:
                continue
            slab(FR, axis, fixed, out, 1.0, a + 0.1, a + 2.2, y + 0.1, y + 1.0, BRICK2)
    for e in (-1, 1):  # песчаниковые углы
        for k in range(6):
            y = 1.4 + 2.3 * k
            w = 2.2 if k % 2 else 1.4
            slab(FR, axis, fixed, out, 1.08, *sorted((e * half, e * (half - w))), y + 0.1, y + 2.2, STONE)
    slab(FR, axis, fixed, out, 1.88, -half - 0.6, half + 0.6, 15.2, 16.2, STONE)
    slab(FR, axis, fixed, out, 0.88, -half, half, 16.2, 18.9, BRICK2)
    for k in range(int(2 * half // 1.6)):  # зубчатый фриз-«шестерёнка»
        a = -half + 1.6 * k + 0.4
        slab(FS, axis, fixed, out, 1.2, a, a + 0.8, 16.2, 16.8, BRASS2)
    if axis == "x":  # бока: ряды разных часов
        for k, (z, y) in enumerate(((-12.0, 10.0), (-6.0, 7.0), (0.0, 10.4), (6.0, 7.2), (12.0, 10.0))):
            wall_clock(FS, FG, axis, fixed, out, z, y, k % 3, 1.5)
        gear(FS, "zy", -12.0, 4.0, fixed + out * 0.88, fixed + out * 1.4, 2.2, 12, BRASS)  # d1 — наружная сторона (спицы видны)
        gear(FS, "zy", 12.0, 4.2, fixed + out * 0.88, fixed + out * 1.4, 1.8, 10, COPPER)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# перед: песчаниковое поле с огромным циферблатом, окна в механизм с шестернями
FR.box(-9.6, 9.6, 1.4, 15.2, -FZ - 1.08, -FZ, STONE)
clock_face(FS, FG, "xy", 0.0, 9.6, -FZ - 1.08, 5.0, -1, frame=BRASS, hh=10.0, mm=2.0)
for s in (-1, 1):
    FS.frame_xy(K.rect(s * 13.6 - 3.2, s * 13.6 + 3.2, 3.6, 13.6), K.rect(s * 13.6 - 2.8, s * 13.6 + 2.8, 4.0, 13.2), -FZ - 1.5, -FZ - 0.88,
                STONE)
    FS.box(s * 13.6 - 2.8, s * 13.6 + 2.8, 4.0, 13.2, -FZ - 0.6, -FZ - 0.4, DARK)
    gear(FS, "xy", s * 13.0, 10.6, -FZ - 0.8, -FZ - 1.2, 2.4, 14, BRASS)  # d1 — сторона улицы (−z)
    gear(FS, "xy", s * 14.6, 6.6, -FZ - 0.6, -FZ - 1.0, 1.7, 10, COPPER)
    gear(FS, "xy", s * 11.6, 5.2, -FZ - 0.9, -FZ - 1.3, 1.1, 8, BRASS2)
# два звонка будильника с молоточком на крыше
for s in (-1, 1):
    bell(FS, s * 4.6, 15.2, -FZ - 2.0, 2.6)
FS.box(-0.25, 0.25, 15.2, 17.6, -FZ - 2.25, -FZ - 1.75, BRASS2)
FS.prism_zy(K.ngon(-FZ - 2.0, 17.8, 0.5, 8), -1.6, 1.6, RED)
# дверь мастерской под козырьком, маятник в стеклянном шкафу, вывеска-шестерня
FS.box(-2.6, 2.6, 1.4, 4.4, -FZ - 1.3, -FZ - 1.08, WOOD2)
FG.box(-2.2, 2.2, 1.4, 4.0, -FZ - 1.36, -FZ - 1.3, "FFE2A0")
FS.box(-3.4, 3.4, 4.4, 4.8, -FZ - 3.0, -FZ - 1.08, DARK)
for s in (-1, 1):
    FS.box(s * 7.2 - 1.0, s * 7.2 + 1.0, 1.4, 4.4, -FZ - 2.6, -FZ - 1.08, WOOD)
    FG.box(s * 7.2 - 0.75, s * 7.2 + 0.75, 1.6, 4.2, -FZ - 2.64, -FZ - 2.6, "BFE0E8")
    FS.box(s * 7.2 - 0.04, s * 7.2 + 0.04, 2.4, 4.2, -FZ - 2.2, -FZ - 2.12, BRASS2)
    FS.prism_xy(K.ngon(s * 7.2, 2.3, 0.4, 10), -FZ - 2.3, -FZ - 2.06, BRASS)
# тыл: трубы и колокол на балке
for x in (-10.0, -7.0):
    FS.prism_xz(K.ngon(x, FZ + 2.0, 0.7, 8), 0.0, 17.0, COPPER)
FS.box(4.0, 10.0, 12.0, 12.6, FZ + 2.4, FZ + 3.0, WOOD2)
bell(FS, 7.0, 9.6, FZ + 2.7, 2.2, BRASS2)

# ══ ИНТЕРЬЕР: мастерская часовщика ════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.3
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), WOOD2)
for k in range(-8, 8):
    if k % 2:
        IQ.box(2.1 * k + 0.04, 2.1 * k + 2.06, 0.02, 0.04, ZF, ZB, WOOD)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 4.0, WOOD2)
        for k in range(int((a1 - a0) // 1.6)):  # вагонка
            a = a0 + 1.6 * k
            slab(IR, axis, fixed, out, 0.96, a + 0.05, a + 1.55, 0.3, 3.7, WOOD)
        slab(IR, axis, fixed, out, 1.2, a0, a1, 4.0, 4.4, WOOD3)
        slab(IR, axis, fixed, out, 0.88, a0, a1, 4.4, C if not gap else DOOR[1] + 0.1, "8A5A44")
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, "8A5A44")
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, BRASS2)
    slab(IR, axis, fixed, out, 1.6, -half, half, 15.2, 16.0, WOOD)
# стены, увешанные часами
for idx, (axis, fixed, out, half) in enumerate(B.WALLS[:2]):
    for k, (a, y) in enumerate(((-12.6, 12.0), (-6.2, 11.0), (-1.6, 12.6), (4.4, 11.0), (10.0, 12.2))):
        wall_clock(IS, IG, axis, fixed, out, a, y, (k + idx) % 3, 1.3 + 0.2 * ((k + idx) % 2))
# огромные шестерни на дальней стене
for (x, y, r, n, col) in ((-8.0, 10.0, 4.0, 14, BRASS), (-1.6, 13.6, 2.6, 10, COPPER), (4.2, 10.4, 3.4, 12, BRASS),
                          (10.4, 12.0, 2.6, 10, BRASS2), (11.0, 6.4, 1.8, 8, COPPER)):
    gear(IS, "xy", x, y, ZF + 0.9, ZF + 1.4, r, n, col)
# напольные часы вдоль боковых стен, верстак с лупой-лампой, полки с будильниками, цепи с гирями
for s in (-1, 1):
    grandfather(IS, IG, s * (W - 1.8), -10.0, -s)
    grandfather(IS, IG, s * (W - 1.8), 0.0, -s, 8.0)
IR.box(-14.0, -8.0, 0.0, 3.0, ZF + 1.6, ZF + 4.0, WOOD2)
IS.box(-14.2, -7.8, 3.0, 3.3, ZF + 1.4, ZF + 4.2, WOOD3)
for k in range(4):
    IS.box(-13.4 + 1.4 * k, -13.0 + 1.4 * k, 3.3, 3.5, ZF + 2.6, ZF + 3.6, STEEL)
beam(IS, (-9.0, 3.3, ZF + 2.0), (-9.6, 5.6, ZF + 2.8), 0.14, 0.14, STEEL)
beam(IS, (-9.6, 5.6, ZF + 2.8), (-10.6, 5.2, ZF + 3.2), 0.14, 0.14, STEEL)
IS.prism_xz(K.ngon(-10.6, ZF + 3.2, 0.6, 10), 4.6, 5.2, BRASS2)
IG.prism_xz(K.ngon(-10.6, ZF + 3.2, 0.45, 10), 4.5, 4.6, "FFE8A0")
for r in range(2):
    y = 6.6 + 2.4 * r
    IS.box(7.0, 14.0, y - 0.2, y, ZF + 0.88, ZF + 2.2, WOOD)
    for k in range(3):
        x = 8.2 + 2.3 * k
        IS.prism_xy(K.ngon(x, y + 0.75, 0.7, 12), ZF + 1.3, ZF + 1.9, (RED, TEAL, BRASS, RED2)[(k + r) % 4])
        IG.prism_xy(K.ngon(x, y + 0.75, 0.52, 12), ZF + 1.9, ZF + 1.94, FACE)
        for e in (-1, 1):
            IS.prism_xz(K.ngon(x + e * 0.5, ZF + 1.6, 0.26, 8), y + 1.25, y + 1.55, BRASS)
for x in (-4.0, 4.0):
    for e in (-0.3, 0.3):
        IS.prism_xz(K.ngon(x + e, ZF + 6.0, 0.05, 4), 8.0 + e * 3, C, STEEL)
        IS.prism_xz(K.ngon(x + e, ZF + 6.0, 0.35, 8), 7.0 + e * 3, 8.0 + e * 3, BRASS2)
# потолочные лампы-колпаки
for x in (-8.0, 8.0):
    for z in (-6.0, 4.0):
        IS.prism_xz(K.ngon(x, z, 0.05, 4), C - 2.0, C, DARK)
        IS.cone([(x + 1.0 * math.cos(t), C - 2.4, z + 1.0 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]], (x, C - 1.9, z),
                BRASS2)
        IG.prism_xz(K.ngon(x, z, 0.55, 8), C - 2.48, C - 2.4, "FFF0C8")
# постамент — огромная лежачая шестерня
px, pz = PED
IR.prism_xz(teeth_pts(px, pz, 4.4, 16, 0.12), 0.0, TOP - 0.4, "7A5A30")  # тёмная бронза: золотой будильник светлее подставки
IS.prism_xz(K.ngon(px, pz, 3.6, 16), TOP - 0.4, TOP, "8A4E2A")
IS.prism_xz(K.ngon(px, pz, 1.2, 8), TOP, TOP + 0.05, COPPER)
for k in range(8):
    t = 2 * math.pi * k / 8
    IS.prism_xz(K.ngon(px + 2.6 * math.cos(t), pz + 2.6 * math.sin(t), 0.22, 6), TOP, TOP + 0.06, BRASS2)
gear(IS, "xz", px + 6.0, pz - 2.6, 0.0, 0.5, 1.8, 10, COPPER)
gear(IS, "xz", px - 5.8, pz - 1.4, 0.0, 0.4, 1.4, 9, BRASS)
B.lift_leaves(IS, WOOD2, BRASS)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, BRICK)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, STONE2)
SL.box(-FX - 1.9, FX + 1.9, 15.2, 16.2, -FZ - 1.9, FZ + 1.9, STONE)
SL.prism_xy(K.ngon(0.0, 9.6, 5.0, 12), -FZ - 1.3, -FZ + 0.1, BRASS)
SL.prism_xy(K.ngon(0.0, 9.6, 4.2, 12), -FZ - 1.4, -FZ - 1.3, FACE)
for s in (-1, 1):
    SL.prism_xy(K.ngon(s * 13.0, 10.6, 2.4, 8), -FZ - 1.2, -FZ + 0.1, BRASS)
    SL.box(s * 4.6 - 2.4, s * 4.6 + 2.4, 15.2, 17.6, -FZ - 4.4, -FZ + 0.4, BRASS)

F.build(exhibit=(PED[0], TOP, PED[1], 2.8), lamps=[("Hall", (0, 14, 6), 2600, (1.0, 0.9, 0.75)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.95, 0.85)),
                                                   ("Warm", (-10, 5, -12), 900, (1.0, 0.75, 0.4))])
