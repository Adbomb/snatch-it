"""Этаж «Легендарный автомат с призами» музея-небоскрёба (третья партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — цирк-шапито на ярмарке. Снаружи — стены из полосатого красно-белого полотна над дощатым настилом,
по верху — фестон из треугольных флажков и полосатый скат шатра, по углам — мачты с вымпелами; спереди — парадная
арка входа с рамкой из лампочек и звездой, касса-будка, гирлянды флажков; на правом боку — колесо обозрения с
кабинками, на левом — «силомер» с колоколом и тир; сзади — цирковой фургон. Внутри — манеж: опилки, круглый
бортик в красно-белую полоску с проходом к лифту, на звёздном подиуме в центре — экспонат, над манежем — купол шатра
полосами с люстрой, две полосатые мачты, трапеция, трибуны вдоль боковых стен, бархатный занавес за манежем,
прожекторы на стойках, полки с призами у лифта, гирлянды флажков.
Запуск: blender --background --factory-startup --python scripts/blender/floor_circus.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab  # noqa: E402

RED, RED2, WHITE, GOLD, GOLD2, BLUE, BLUE2 = "D8352A", "B02A22", "F4F0E6", "F2C230", "D9A21A", "2E6AD8", "2450A8"
WOOD, WOOD2, SAW, SAW2, PURPLE, GREEN, BULB, DARK = "A8743A", "8A5A32", "D8B878", "C8A060", "8A4AD8", "3FBF5A", "FFF0C0", "3A2E2A"
VELVET, VELVET2 = "8A1E2A", "6E1820"

F = B.Floor("PM", "PrizeMachine", quiet=(SAW, SAW2, VELVET), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL
FLAGS = (RED, GOLD, BLUE, GREEN, PURPLE)


def star(cx, cy, r, r2):
    return [(cx + math.cos(math.pi / 2 + math.pi * k / 5) * (r if k % 2 == 0 else r2),
             cy + math.sin(math.pi / 2 + math.pi * k / 5) * (r if k % 2 == 0 else r2)) for k in range(10)]


def bunting(p, a, b, n, size, sag=1.0):
    """Гирлянда флажков между точками a и b (с провисом)."""
    pts = []
    for k in range(n + 1):
        t = k / n
        pts.append(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))
        pts[-1] = (pts[-1][0], pts[-1][1] - sag * 4 * t * (1 - t), pts[-1][2])
    for k, (q0, q1) in enumerate(zip(pts, pts[1:])):
        beam(p, q0, q1, 0.06, 0.06, DARK)
        mx, my, mz = ((q0[0] + q1[0]) / 2, (q0[1] + q1[1]) / 2, (q0[2] + q1[2]) / 2)
        dx, dz = (q1[0] - q0[0]) * 0.35, (q1[2] - q0[2]) * 0.35
        p.loft([(mx - dx, my, mz - dz), (mx + dx, my, mz + dz), (mx + dx, my - 0.02, mz + dz), (mx - dx, my - 0.02, mz - dz)],
               [(mx - 0.02, my - size, mz), (mx + 0.02, my - size, mz), (mx + 0.02, my - size - 0.02, mz),
                (mx - 0.02, my - size - 0.02, mz)], FLAGS[k % 5])


# ══ ФАСАД: цирк-шапито ════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, RED2, RED2, WHITE)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 6.88 if fi == 0 else 2.88, -half - 2.88, half + 2.88, -1.0, -0.2, SAW2)
    slab(FR, axis, fixed, out, 5.88 if fi == 0 else 1.88, -half - 1.88, half + 1.88, -0.2, 1.2, WOOD)  # дощатый настил (спереди шире — под кассой)
    for k in range(int((2 * half + 3.6) // 0.9)):
        a = -half - 1.8 + 0.9 * k
        slab(FS, axis, fixed, out, 5.93 if fi == 0 else 1.93, a, a + 0.06, -0.2, 1.2, WOOD2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.2, 16.0, WHITE)
    for k in range(int(2 * half // 2.0)):  # полосы полотна
        a = -half + 2.0 * k
        if k % 2 == 0:
            slab(FS, axis, fixed, out, 1.0, a, a + 2.0, 1.2, 15.4, RED)
    slab(FS, axis, fixed, out, 1.6, -half - 0.3, half + 0.3, 15.4, 16.0, GOLD2)
    for k in range(int(2 * half // 1.6)):  # фестон из флажков
        a = -half + 1.6 * k
        pts = [(a, 16.0), (a + 1.6, 16.0), (a + 0.8, 14.6)]
        d0, d1 = sorted((fixed + out * 1.62, fixed + out * 1.72))
        (FS.prism_xy if axis == "z" else FS.prism_zy)(pts, d0, d1, FLAGS[k % 5])
    B.chamfer(FS, axis, fixed, out, -half - 0.4, half + 0.4, [(0.0, 16.0), (2.4, 16.0), (1.0, 19.0), (0.0, 19.0)], WHITE)
    for k in range(int(2 * half // 2.0) + 1):  # полосы ската
        a = -half + 2.0 * k
        if k % 2 == 0:
            B.chamfer(FS, axis, fixed, out, a - 0.5, min(a + 0.5, half + 0.4),
                      [(0.0, 16.0), (2.5, 16.0), (1.1, 19.0), (0.0, 19.0)], RED)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# мачты по углам с вымпелами
for sx in (-1, 1):
    for sz in (-1, 1):
        cx, cz = sx * (FX + 1.3), sz * (FZ + 1.3)
        for k in range(6):
            FS.prism_xz(K.octa(cx, cz, 0.45, 0.45, 0.18), -0.2 + 3.1 * k, 2.9 + 3.1 * k, RED if k % 2 else WHITE)
        FS.prism_xz(K.octa(cx, cz, 0.55, 0.55, 0.22), 17.4, 17.8, GOLD)
        FS.prism_xy([(cx, 18.9), (cx + sx * 2.2, 18.4), (cx, 17.9)], cz - 0.05, cz + 0.05, FLAGS[(sx + sz + 2) % 5])
# перед: арка входа с лампочками и звездой, касса, гирлянды
ARCH_O = [(-5.6, 1.2)] + [(-5.6 + 5.6 * (1 - math.cos(math.pi * k / 10)), 8.4 + 4.0 * math.sin(math.pi * k / 10))
                          for k in range(11)] + [(5.6, 1.2)]
ARCH_I = [(-4.2, 1.2)] + [(-4.2 + 4.2 * (1 - math.cos(math.pi * k / 10)), 8.4 + 2.8 * math.sin(math.pi * k / 10))
                          for k in range(11)] + [(4.2, 1.2)]
FS.frame_xy(ARCH_O, ARCH_I, -FZ - 2.2, -FZ, RED)
FS.prism_xy(ARCH_I, -FZ - 0.4, -FZ, "2A1E2A")
for k in range(1, 11):  # лампочки по арке
    x, y = ARCH_O[k]
    xi, yi = ARCH_I[k]
    mx, my = (x + xi) / 2, (y + yi) / 2
    FG.box(mx - 0.2, mx + 0.2, my - 0.2, my + 0.2, -FZ - 2.35, -FZ - 2.2, BULB)
for y in (2.4, 4.0, 5.6, 7.2):
    for x in (-4.9, 4.9):
        FG.box(x - 0.2, x + 0.2, y - 0.2, y + 0.2, -FZ - 2.35, -FZ - 2.2, BULB)
FS.prism_xy(star(0.0, 14.6, 2.2, 0.95), -FZ - 2.4, -FZ - 1.8, GOLD)
FS.box(-0.3, 0.3, 12.2, 13.0, -FZ - 2.1, -FZ - 1.9, GOLD2)
FS.box(-4.0, -0.2, 1.2, 7.0, -FZ - 0.7, -FZ - 0.4, VELVET)  # занавес входа, приоткрыт
FS.box(0.2, 4.0, 1.2, 7.0, -FZ - 0.7, -FZ - 0.4, VELVET2)
FS.box(9.0, 13.6, 1.2, 6.6, -FZ - 4.6, -FZ - 1.8, WHITE)  # касса
for k in range(3):
    FS.box(9.0 + 1.6 * k, 9.8 + 1.6 * k, 1.2, 6.6, -FZ - 4.7, -FZ - 1.7, RED)
FS.box(9.6, 13.0, 3.6, 5.6, -FZ - 4.75, -FZ - 4.6, "2A1E2A")
FG.box(9.8, 12.8, 3.8, 5.4, -FZ - 4.8, -FZ - 4.75, BULB)
FS.loft([(8.6, 6.6, -FZ - 5.2), (14.0, 6.6, -FZ - 5.2), (14.0, 6.6, -FZ - 1.4), (8.6, 6.6, -FZ - 1.4)],
        [(10.6, 8.4, -FZ - 3.4), (12.0, 8.4, -FZ - 3.4), (12.0, 8.4, -FZ - 3.0), (10.6, 8.4, -FZ - 3.0)], RED)
FS.prism_xz(K.octa(11.3, -FZ - 3.2, 0.3, 0.3, 0.12), 8.4, 9.2, GOLD)
bunting(FS, (-FX - 1.3, 13.4, -FZ - 1.3), (-5.6, 12.0, -FZ - 2.3), 6, 0.8, 0.8)
bunting(FS, (5.6, 12.0, -FZ - 2.3), (FX + 1.3, 13.4, -FZ - 1.3), 6, 0.8, 0.8)
# правый бок: колесо обозрения; левый: силомер с колоколом и тир
wc, wy, wr = 0.0, 9.0, 6.4
fx = FX + 1.4
FS.frame_zy(K.ngon(wc, wy, wr, 16), K.ngon(wc, wy, wr - 0.35, 16), fx, fx + 0.3, WHITE)
FS.frame_zy(K.ngon(wc, wy, wr - 1.6, 16), K.ngon(wc, wy, wr - 1.9, 16), fx, fx + 0.3, RED)
for k in range(8):
    t = 2 * math.pi * k / 8
    beam(FS, (fx + 0.15, wy, wc), (fx + 0.15, wy + wr * math.sin(t), wc + wr * math.cos(t)), 0.16, 0.16, WHITE)
    z, y = wc + wr * math.cos(t), wy + wr * math.sin(t)
    FS.box(fx + 0.3, fx + 1.4, y - 1.4, y - 0.2, z - 0.7, z + 0.7, FLAGS[k % 5])
    FS.box(fx + 0.3, fx + 1.5, y - 0.3, y - 0.1, z - 0.8, z + 0.8, WHITE)
    FG.box(fx + 0.25, fx + 0.35, y - 0.2, y + 0.2, z - 0.2, z + 0.2, BULB)
FS.prism_zy(K.octa(wc, wy, 0.8, 0.8, 0.33), fx - 0.1, fx + 0.6, GOLD)
for e in (-1, 1):
    beam(FS, (fx + 0.2, 1.2, wc + e * 4.0), (fx + 0.2, wy, wc), 0.5, 0.5, RED2, up=(1, 0, 0))
fl = -FX - 1.0  # силомер
FS.box(fl - 0.6, fl - 0.1, 1.2, 15.0, -8.6, -7.4, WHITE)
for k in range(6):
    FS.box(fl - 0.7, fl - 0.55, 2.0 + 2.2 * k, 3.4 + 2.2 * k, -8.4, -7.6, FLAGS[k % 5])
FS.prism_xz(K.octa(fl - 0.35, -8.0, 0.9, 0.9, 0.36), 15.0, 15.8, GOLD)
FS.box(fl - 1.4, fl - 0.1, 1.2, 1.8, -9.0, -7.0, RED)
FS.box(fl - 0.2, fl, 1.2, 6.8, 3.0, 11.0, WOOD)  # тир: стойка с мишенями
FS.box(fl - 1.6, fl, 6.8, 7.4, 2.6, 11.4, RED)
for k in range(4):
    z = 4.2 + 2.0 * k
    FS.frame_zy(K.octa(z, 4.2, 0.7, 0.7, 0.29), K.octa(z, 4.2, 0.4, 0.4, 0.16), fl - 0.4, fl - 0.2, RED if k % 2 else WHITE)
    FS.prism_zy(K.octa(z, 4.2, 0.4, 0.4, 0.16), fl - 0.35, fl - 0.2, WHITE if k % 2 else RED)
# тыл: цирковой фургон
FS.box(-8.0, 2.0, 1.6, 7.6, FZ + 0.6, FZ + 4.0, RED)
FS.box(-8.2, 2.2, 7.6, 8.2, FZ + 0.4, FZ + 4.2, GOLD)
for k in range(5):
    FS.box(-7.2 + 2.0 * k, -6.9 + 2.0 * k, 2.4, 7.2, FZ + 4.0, FZ + 4.1, GOLD2)
for x in (-6.4, 0.4):
    FS.frame_xy(K.ngon(x, 1.6, 1.3, 12), K.ngon(x, 1.6, 1.0, 12), FZ + 4.1, FZ + 4.4, GOLD)
    for k in range(4):
        t = math.pi * k / 4
        FS.box(x - 1.1 * abs(math.cos(t)) - 0.08, x + 1.1 * abs(math.cos(t)) + 0.08, 1.52, 1.68, FZ + 4.15, FZ + 4.35, GOLD2)

# ══ ИНТЕРЬЕР: манеж под куполом ═══════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.0
px, pz = PED
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), SAW)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    slab(IQ, axis, fixed, out, 0.7, -half, half, 0.0, C, RED2)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.0, WOOD2)
        for k in range(int((a1 - a0) // 2.0) + 1):
            b0, b1 = a0 + 2.0 * k, min(a0 + 2.0 * (k + 1), a1)
            if b1 - b0 > 0.2:
                slab(IR, axis, fixed, out, 0.88, b0, b1, 1.0, 12.0, RED if k % 2 else WHITE)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 12.0, GOLD2)
    slab(IS, axis, fixed, out, 1.2, -half, half, 12.0, 12.6, GOLD2)
    for k in range(int(2 * half // 1.4)):
        a = -half + 1.4 * k
        pts = [(a, 12.0), (a + 1.4, 12.0), (a + 0.7, 10.9)]
        d0, d1 = sorted((fixed + out * 1.0, fixed + out * 1.08))
        (IS.prism_xy if axis == "z" else IS.prism_zy)(pts, d0, d1, FLAGS[k % 5])
# купол шатра: полосы к центру, люстра
cx_, cz_ = px, pz + 1.0
corners = [(-W, ZF), (W, ZF), (W, ZB), (-W, ZB)]
for k in range(4):
    (x0, z0), (x1, z1) = corners[k], corners[(k + 1) % 4]
    for m in range(8):
        t0, t1 = m / 8, (m + 1) / 8
        a = (x0 + (x1 - x0) * t0, C - 0.05, z0 + (z1 - z0) * t0)
        b = (x0 + (x1 - x0) * t1, C - 0.05, z0 + (z1 - z0) * t1)
        if m % 2 == 0:
            IS.loft([a, b, (b[0], b[1] - 0.05, b[2]), (a[0], a[1] - 0.05, a[2])],
                    [(cx_ + 0.6, C - 0.6, cz_), (cx_ + 0.6, C - 0.6, cz_), (cx_ + 0.6, C - 0.65, cz_), (cx_ + 0.6, C - 0.65, cz_)],
                    RED)
IS.prism_xz(K.ngon(cx_, cz_, 1.6, 12), C - 1.2, C - 0.4, GOLD)
IG.prism_xz(K.ngon(cx_, cz_, 1.2, 12), C - 1.6, C - 1.2, BULB)
# манеж: бортик в полоску с проходом к лифту, звёздный подиум
RR = 7.6
for k in range(24):
    t0, t1 = 2 * math.pi * k / 24, 2 * math.pi * (k + 1) / 24
    mid = (t0 + t1) / 2
    if math.sin(mid) > 0.86:  # проход к лифту
        continue
    pts = [(px + RR * math.cos(t0), pz + RR * math.sin(t0)), (px + (RR + 0.8) * math.cos(t0), pz + (RR + 0.8) * math.sin(t0)),
           (px + (RR + 0.8) * math.cos(t1), pz + (RR + 0.8) * math.sin(t1)), (px + RR * math.cos(t1), pz + RR * math.sin(t1))]
    if max(abs(x) for x, _ in pts) > W - 0.1 or min(z for _, z in pts) < ZF + 0.1:
        continue
    IS.prism_xz(pts, 0.0, 0.9, RED if k % 2 else WHITE)
    IS.prism_xz(pts, 0.9, 1.0, GOLD2)
IQ.prism_xz(K.ngon(px, pz, RR, 24), 0.02, 0.06, SAW2)
IR.prism_xz(star(px, pz, 4.6, 2.4), 0.0, 0.5, BLUE)
IR.prism_xz(K.ngon(px, pz, 2.9, 12), 0.5, TOP, GOLD2)
IS.frame_xz(K.ngon(px, pz, 3.0, 12), K.ngon(px, pz, 2.9, 12), TOP - 0.15, TOP + 0.02, WHITE)
for k in range(5):
    x, z = star(px, pz, 4.2, 2.4)[2 * k]
    IG.prism_xz(K.octa(x, z, 0.22, 0.22, 0.09), 0.5, 0.6, BULB)
# мачты, трапеция
for s in (-1, 1):
    x = px + s * 9.6
    for k in range(6):
        IS.prism_xz(K.octa(x, pz, 0.5, 0.5, 0.2), 3.0 * k, 3.0 * (k + 1), RED if k % 2 else WHITE)
    IS.prism_xz(K.octa(x, pz, 0.7, 0.7, 0.28), 0.0, 0.5, GOLD2)
    beam(IS, (x, 16.0, pz), (px + s * 2.0, C - 0.2, pz - 6.0), 0.06, 0.06, DARK)
for e in (-1.4, 1.4):
    IS.box(px + e - 0.04, px + e + 0.04, 12.0, C, pz - 7.0, pz - 6.92, "C8A46A")
IS.box(px - 1.6, px + 1.6, 11.85, 12.05, pz - 7.05, pz - 6.87, GOLD)
# трибуны вдоль боковых стен
for s in (-1, 1):
    for k in range(4):
        x0, x1 = s * (W - 2.2 * (k + 1)), s * (W - 2.2 * k)
        IS.box(x0, x1, 0.0, 0.9 * (4 - k), -14.0, 2.0, (BLUE, BLUE2)[k % 2])
        IS.box(x0, x1, 0.9 * (4 - k), 0.9 * (4 - k) + 0.12, -14.0, 2.0, WOOD)
# занавес за манежем
for k in range(12):
    x = -11.0 + 2.0 * k
    IS.box(x - 1.0, x + 1.0, 0.0, 11.0, ZF + 0.9 + 0.25 * (k % 2), ZF + 1.4 + 0.25 * (k % 2), VELVET if k % 2 else VELVET2)
IS.box(-12.2, 12.2, 10.4, 11.4, ZF + 0.9, ZF + 1.9, GOLD2)
IS.prism_xy(star(0.0, 8.0, 1.6, 0.7), ZF + 1.9, ZF + 2.1, GOLD)
# прожекторы на стойках, полки с призами у лифта
for x, z in ((-11.6, 5.0), (11.6, 5.0)):
    IS.box(x - 0.1, x + 0.1, 0.0, 6.0, z - 0.1, z + 0.1, DARK)
    IS.loft([(x - 0.5, 6.0, z - 0.5), (x + 0.5, 6.0, z - 0.5), (x + 0.5, 6.0, z + 0.5), (x - 0.5, 6.0, z + 0.5)],
            [(x - 0.8, 6.6, z - 1.6), (x + 0.8, 6.6, z - 1.6), (x + 0.8, 7.4, z - 1.6), (x - 0.8, 7.4, z - 1.6)], DARK)
    IG.box(x - 0.7, x + 0.7, 6.7, 7.3, z - 1.65, z - 1.6, BULB)
for s in (-1, 1):
    x0 = s * W
    IS.box(x0, x0 - s * 1.4, 0.0, 8.0, 8.0, 14.0, WOOD2)
    for r in range(3):
        y = 1.6 + 2.4 * r
        IS.box(x0, x0 - s * 1.5, y - 0.15, y, 8.0, 14.0, WOOD)
        for k in range(3):
            z = 9.0 + 2.0 * k
            col = FLAGS[(r * 3 + k + (s > 0)) % 5]
            if (r + k) % 2:
                IS.prism_xz(K.octa(x0 - s * 0.7, z, 0.55, 0.55, 0.22), y, y + 1.1, col)
                IS.prism_xz(K.octa(x0 - s * 0.7, z, 0.4, 0.4, 0.16), y + 1.1, y + 1.7, col)
            else:
                IS.prism_zy(star(z, y + 0.85, 0.85, 0.38), x0 - s * 0.9, x0 - s * 0.5, col)
bunting(IS, (-W, 14.0, -6.0), (W, 14.0, -6.0), 12, 0.7, 1.4)
bunting(IS, (-W, 14.4, 4.0), (W, 14.4, 4.0), 12, 0.7, 1.4)
B.lift_leaves(IS, RED2, GOLD)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, RED)
SL.box(-FX - 1.9, FX + 1.9, -1.0, 1.2, -FZ - 1.9, FZ + 1.9, WOOD)
SL.box(-FX - 2.4, FX + 2.4, 15.4, 17.0, -FZ - 2.4, FZ + 2.4, WHITE)
SL.box(-5.6, 5.6, 1.2, 12.4, -FZ - 2.2, -FZ, RED2)
SL.box(-2.2, 2.2, 12.4, 16.8, -FZ - 2.4, -FZ - 1.8, GOLD)
SL.box(FX + 1.4, FX + 2.8, 2.6, 15.4, -6.4, 6.4, WHITE)
SL.box(9.0, 13.6, 1.2, 8.4, -FZ - 4.6, -FZ - 1.8, RED)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 3000, (1.0, 0.92, 0.85)),
                                                   ("Spot", (0, 13, -3), 3200, (1.0, 0.97, 0.9))])
