"""Этаж «Кактусы-акробаты» музея-небоскрёба (девятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — цирк шапито. Снаружи — стены в красно-белую полоску, под карнизом — фестоны жёлто-синих
треугольников, красная скатная крыша с белыми полосами, на углах — мачты с вымпелами, вход-арка с лампочками,
по бокам — тумбы-барабаны со звёздами, билетная будка с круглой крышей, пушка для акробатов, афиши со звёздами
и кактусом, флажки. Внутри — манеж: шатёр-купол из полосатых клиньев под потолком, красный барьер манежа,
опилки, трибуны-ступени вдоль стен, трапеция на канатах, канат между двумя мачтами, прожекторы, гирлянды
звёзд; экспонат — на цирковой тумбе-барабане в полоску со звёздами.
Запуск: blender --background --factory-startup --python scripts/blender/floor_circus.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
import floorshell as S  # noqa: E402
from floorbase import C, FX, FZ, W, ZB, ZF, beam, rng, slab  # noqa: E402

RED, RED2, WHITE, YEL, BLUE, BLUE2 = "E0343A", "B0242A", "F6F2EA", "F6C836", "2E5ED8", "1E40A0"
GOLD, SAW, WOOD, DARK, GREEN, BULB = "E8B030", "D8B070", "8A5A32", "2A2A34", "3E9A4A", "FFF0A0"

F = B.Floor("CI", "CactusAcrobats", quiet=(SAW, "C8A070", "8A6A4A"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def star(p, x, y, z0, z1, r, col, axis="z"):
    pts = [(x + r * (1 if k % 2 == 0 else 0.45) * math.cos(math.pi / 2 + k * math.pi / 5),
            y + r * (1 if k % 2 == 0 else 0.45) * math.sin(math.pi / 2 + k * math.pi / 5)) for k in range(10)]
    if axis == "z":
        p.prism_xy(pts, z0, z1, col)
    else:
        p.prism_zy(pts, z0, z1, col)


def drum(p, x, z, y, r, h, c1, c2, n=12):
    """Тумба-барабан: полосатый цилиндр сегментами, обручи сверху и снизу."""
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        p.prism_xz([(x, z), (x + r * math.cos(a0), z + r * math.sin(a0)), (x + r * math.cos(a1), z + r * math.sin(a1))],
                   y + 0.25, y + h - 0.25, c1 if k % 2 else c2)
    p.prism_xz(K.ngon(x, z, r + 0.12, n), y, y + 0.25, GOLD)
    p.prism_xz(K.ngon(x, z, r + 0.12, n), y + h - 0.25, y + h, GOLD)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, WHITE, RED2, GOLD, SAW, "2A1E3A", roof="hip", roof_col=RED, top=15.6, side=None)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # красные полосы и фестоны по всем сторонам
    n = int(2 * half // 1.6)
    for k in range(n):
        a = -half + 1.6 * k
        if k % 2 == 0:
            slab(FS, axis, fixed, out, 0.93, a, a + 1.6, 1.0, 15.6, RED)
        tri = [(a, 15.6), (a + 1.6, 15.6), (a + 0.8, 14.4)]
        d0, d1 = sorted((fixed + out * 1.0, fixed + out * 1.12))
        if axis == "z":
            FS.prism_xy(tri, d0, d1, YEL if k % 2 else BLUE)
        else:
            FS.prism_zy(tri, d0, d1, YEL if k % 2 else BLUE)
for k in range(9):  # белые полосы по скату крыши спереди
    x = -FX - 1.0 + (2 * FX + 2.0) * (k + 0.5) / 9
    FS.loft([(x - 0.5, 16.32, -FZ - 2.22), (x + 0.5, 16.32, -FZ - 2.22), (x + 0.5, 16.5, -FZ - 2.22), (x - 0.5, 16.5, -FZ - 2.22)],
            [(x - 0.4, 18.92, -FZ - 0.86), (x + 0.4, 18.92, -FZ - 0.86), (x + 0.4, 18.96, -FZ - 0.86), (x - 0.4, 18.96, -FZ - 0.86)], WHITE)
# мачты с вымпелами на углах
for x in (-FX - 1.6, FX + 1.6):
    FS.prism_xz(K.ngon(x, -FZ - 1.6, 0.18, 8), -0.1, 18.6, GOLD)
    FS.prism_xz(K.ngon(x, -FZ - 1.6, 0.3, 8), 18.4, 18.8, GOLD)
    FS.prism_xy([(x, 18.2), (x + (2.6 if x < 0 else -2.6), 17.5), (x, 16.8)], -FZ - 1.64, -FZ - 1.56, BLUE if x < 0 else RED)
# вход-арка с лампочками
AW, AH = 4.0, 9.0
FS.box(-AW, AW, 1.0, AH - AW, -FZ - 0.92, -FZ - 0.88, "1A1430")
FS.prism_xy([(-AW, AH - AW)] + [(AW * math.cos(math.pi * k / 10), AH - AW + AW * math.sin(math.pi * k / 10)) for k in range(11)],
            -FZ - 0.92, -FZ - 0.88, "1A1430")
for k in range(10):
    a0, a1 = math.pi * k / 10, math.pi * (k + 1) / 10
    beam(FS, ((AW + 0.5) * math.cos(a0), AH - AW + (AW + 0.5) * math.sin(a0), -FZ - 1.2), ((AW + 0.5) * math.cos(a1), AH - AW + (AW + 0.5) * math.sin(a1),
                                                                                         -FZ - 1.2), 1.0, 0.6, GOLD, up=(0, 0, 1))
for k in range(15):
    a = math.pi * k / 14
    FG.prism_xy(K.ngon((AW + 0.5) * math.cos(a), AH - AW + (AW + 0.5) * math.sin(a), 0.2, 6), -FZ - 1.6, -FZ - 1.5, BULB)
for e in (-1, 1):
    FS.box(e * (AW + 0.5) - 0.5, e * (AW + 0.5) + 0.5, 1.0, AH - AW, -FZ - 1.5, -FZ - 0.9, GOLD)
    for k in range(5):
        FG.prism_xy(K.ngon(e * (AW + 0.5), 1.8 + 0.9 * k, 0.2, 6), -FZ - 1.6, -FZ - 1.5, BULB)
for e in (-1, 1):  # занавес
    FS.prism_xy([(e * 0.2, 1.0), (e * AW, 1.0), (e * AW, AH - 1.0), (e * 1.4, AH - 2.0)], -FZ - 1.0, -FZ - 0.94, RED2)
# афиши со звёздами и кактусом
for x, kind in ((-12.0, 0), (11.0, 1)):
    FS.box(x - 2.4, x + 2.4, 5.4, 11.8, -FZ - 1.1, -FZ - 0.88, BLUE2 if kind else YEL)
    FS.frame_xy(K.rect(x - 2.6, x + 2.6, 5.2, 12.0), K.rect(x - 2.4, x + 2.4, 5.4, 11.8), -FZ - 1.2, -FZ - 0.88, GOLD)
    if kind:
        FS.box(x - 0.4, x + 0.4, 6.0, 10.6, -FZ - 1.25, -FZ - 1.1, GREEN)
        FS.box(x - 1.6, x - 0.4, 8.0, 8.6, -FZ - 1.25, -FZ - 1.1, GREEN)
        FS.box(x - 1.6, x - 1.0, 8.6, 9.8, -FZ - 1.25, -FZ - 1.1, GREEN)
        FS.box(x + 0.4, x + 1.4, 7.2, 7.8, -FZ - 1.25, -FZ - 1.1, GREEN)
        FS.box(x + 0.8, x + 1.4, 7.8, 9.0, -FZ - 1.25, -FZ - 1.1, GREEN)
        star(FS, x, 11.0, -FZ - 1.25, -FZ - 1.1, 0.5, YEL)
    else:
        for j, (dx, dy, r) in enumerate(((0, 9.6, 1.6), (-1.3, 6.6, 0.7), (1.3, 6.8, 0.8))):
            star(FS, x + dx, dy, -FZ - 1.25, -FZ - 1.1, r, (RED, BLUE, RED)[j])
F.objects(True)
# тумбы-барабаны по бокам входа и билетная будка с круглой крышей
for x in (-7.2, 7.2):
    drum(FS, x, -FZ - 2.0, -0.1, 1.1, 1.8, RED, WHITE)
    star(FS, x, 2.6, -FZ - 2.06, -FZ - 1.94, 0.7, YEL)
KX = -16.0
FS.box(KX - 1.6, KX + 1.6, -0.1, 4.8, -FZ - 2.8, -FZ - 1.0, RED)
FG.box(KX - 1.2, KX + 1.2, 2.4, 4.2, -FZ - 2.84, -FZ - 2.8, BULB)
FS.box(KX - 1.7, KX + 1.7, 2.0, 2.3, -FZ - 3.0, -FZ - 0.9, GOLD)
FS.cone([(x, 4.8, z) for x, z in K.ngon(KX, -FZ - 1.9, 2.2, 10)], (KX, 6.8, -FZ - 1.9), WHITE)
FS.prism_xz(K.ngon(KX, -FZ - 1.9, 2.3, 10), 4.7, 4.9, BLUE)
star(FS, KX, 7.4, -FZ - 1.95, -FZ - 1.85, 0.5, YEL)
# пушка для акробатов
CX = 13.0
beam(FS, (CX - 1.2, 1.2, -FZ - 2.0), (CX + 1.6, 3.6, -FZ - 2.0), 1.2, 1.2, BLUE)
beam(FS, (CX + 1.5, 3.5, -FZ - 2.0), (CX + 1.9, 3.85, -FZ - 2.0), 1.5, 1.5, GOLD)
S.disc(FS, (CX - 0.6, 0.9, -FZ - 2.9), (0, 0, -1), 1.0, 0.3, RED, seg=12)
S.disc(FS, (CX - 0.6, 0.9, -FZ - 3.05), (0, 0, -1), 0.3, 0.2, GOLD, seg=8)
F.objects(False)

# ══ ИНТЕРЬЕР: манеж под куполом ═══════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.8
S.interior(F, "3A2A5A", SAW, "2A1E3A", GOLD, wain=(2.0, RED2), beams=None)
for k in range(16):  # шатёр-купол из полосатых клиньев
    a0, a1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
    r = 21.0
    IS.cone([(max(-W + 0.9, min(W - 0.9, r * math.cos(a0))), 13.6, max(ZF + 0.9, min(ZB - 0.9, -3.0 + r * math.sin(a0)))),
             (max(-W + 0.9, min(W - 0.9, r * math.cos(a1))), 13.6, max(ZF + 0.9, min(ZB - 0.9, -3.0 + r * math.sin(a1)))),
             (0.0, 13.6, -3.0)], (0.0, C - 0.3, -3.0), RED if k % 2 else WHITE)
F.objects(True)
for s in (-1, 1):  # трибуны-ступени вдоль боковых стен
    for j in range(4):
        x0 = s * (W - 0.88)
        x1 = x0 - s * (4.4 - 1.1 * j)
        IS.box(*sorted((x0, x1)), 0.0, 1.0 + 1.0 * j, -13.0, 6.0, (RED, BLUE, RED, BLUE)[j])
        IS.box(*sorted((x1, x1 + s * 0.3)), 1.0 + 1.0 * j - 0.15, 1.0 + 1.0 * j + 0.05, -13.0, 6.0, GOLD)
# барьер манежа вокруг постамента
for k in range(20):
    if k in (4, 5):  # проход к лифту
        continue
    a0, a1 = 2 * math.pi * k / 20, 2 * math.pi * (k + 1) / 20
    r0, r1 = 6.4, 7.0
    IS.prism_xz([(r0 * math.cos(a0), -3.0 + r0 * math.sin(a0)), (r1 * math.cos(a0), -3.0 + r1 * math.sin(a0)),
                 (r1 * math.cos(a1), -3.0 + r1 * math.sin(a1)), (r0 * math.cos(a1), -3.0 + r0 * math.sin(a1))], 0.0, 1.0,
                RED if k % 2 else GOLD)
# трапеция на канатах и канат между мачтами
for x in (-10.0, 10.0):
    IS.prism_xz(K.ngon(x, ZF + 3.0, 0.2, 8), 0.0, 13.6, GOLD)
    IS.box(x - 1.0, x + 1.0, 10.0, 10.3, ZF + 2.0, ZF + 4.0, WOOD)
IS.box(-10.0, 10.0, 10.6, 10.7, ZF + 2.96, ZF + 3.04, "E8E0D0")
for e in (-1.2, 1.2):
    IS.box(-4.0 + e - 0.03, -4.0 + e + 0.03, 8.6, 13.6, -9.0 - 0.03, -9.0 + 0.03, "E8E0D0")
IS.box(-5.4, -2.6, 8.4, 8.6, -9.1, -8.9, GOLD)
# пушка для «человека-ядра», тумбы-барабаны, стойка с булавами и мячами — у лифта, по бокам от прохода
CX, CZ = -10.6, 10.4
for e in (-1, 1):
    S.disc(IS, (CX + e * 1.3, 1.0, CZ), (1, 0, 0), 1.0, 0.3, RED2, seg=12)
    S.annulus(IS, (CX + e * 1.32, 1.0, CZ), (1, 0, 0), 0.75, 1.0, 0.34, GOLD, seg=12)
beam(IS, (CX, 1.2, CZ + 2.2), (CX, 4.6, CZ - 1.8), 1.5, 1.5, BLUE, up=(1, 0, 0))
beam(IS, (CX, 4.5, CZ - 1.7), (CX, 4.9, CZ - 2.1), 1.8, 1.8, GOLD, up=(1, 0, 0))
for k, (x, z, h) in enumerate(((9.0, 9.4, 1.6), (11.2, 10.6, 1.2), (10.2, 12.4, 2.0))):
    drum(IS, x, z, 0.0, 0.9, h, (RED, BLUE, YEL)[k], WHITE, n=12)
IS.box(13.0, 14.6, 0.0, 2.6, 13.4, 14.4, WOOD)
for k in range(4):
    x = 13.2 + 0.4 * k
    IS.prism_xz(K.ngon(x, 13.9, 0.13, 6), 2.6, 3.6, (WHITE, RED, YEL, BLUE)[k])
    IS.prism_xz(K.ngon(x, 13.9, 0.2, 6), 3.2, 3.5, (WHITE, RED, YEL, BLUE)[k])
F.objects(False)
# флажки-вымпелы над трибунами и опилки манежа с красным кругом
for s in (-1, 1):
    pts = D.chain(IS, (s * (W - 1.0), 7.2, -13.0), (s * (W - 1.0), 7.2, 6.0), 12, 0.05, "E8E0D0", sag=0.8)
    for m, q in enumerate(pts[1:-1]):
        IS.prism_zy([(q[2] - 0.4, q[1]), (q[2] + 0.4, q[1]), (q[2], q[1] - 0.9)], q[0] - 0.03, q[0] + 0.03, (RED, YEL, BLUE, WHITE)[m % 4])
IQ.prism_xz(K.ngon(0.0, -3.0, 6.3, 20), 0.02, 0.05, "E8C890")
S.annulus(IQ, (0.0, 0.05, -3.0), (0, 1, 0), 5.8, 6.1, 0.02, RED, seg=20)
for k in range(6):  # прожекторы под куполом
    a = 2 * math.pi * k / 6
    x, z = 9.0 * math.cos(a), -3.0 + 8.0 * math.sin(a)
    IS.box(x - 0.6, x + 0.6, 12.2, 13.4, z - 0.6, z + 0.6, DARK)
    IG.box(x - 0.45, x + 0.45, 12.1, 12.2, z - 0.45, z + 0.45, BULB)
for k in range(14):  # гирлянда звёзд по дальней стене
    x = -13.0 + 2.0 * k
    star(IS, x, 11.6 + 0.4 * math.sin(k), ZF + 0.9, ZF + 1.0, 0.45, (YEL, GOLD, WHITE)[k % 3])
# постамент: цирковая тумба-барабан
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 3.4, 16), 0.0, 0.3, BLUE2)
drum(IS, px, pz, 0.3, 3.0, TOP - 0.3, RED, WHITE, n=16)
star(IS, px, 1.05, pz - 3.14, pz - 3.0, 0.5, YEL)
B.lift_leaves(IS, RED2, GOLD)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, RED, SAW, RED, top=15.6, roof="hip")
for x in (-FX - 1.6, FX + 1.6):
    SL.prism_xz(K.ngon(x, -FZ - 1.6, 0.2, 4), -0.1, 18.6, GOLD)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 1500, (1.0, 0.9, 0.85)),
                                                   ("Spot", (0, 13, -3), 4200, (1.0, 0.97, 0.9)),
                                                   ("Ring", (0, 6, -3), 800, (1.0, 0.8, 0.5))])
