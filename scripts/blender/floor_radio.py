"""Этаж «Фенек-лопоух» музея-небоскрёба (девятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — радиостанция «Большое ухо» в пустыне. Снаружи — песочный саман с синими наличниками и голубой
полосой, длинное окно аппаратной с жалюзи, на правом углу — решётчатая мачта с красно-белыми поясами и красным
огнём, слева — большая тарелка антенны на решётчатой опоре, рупоры-громкоговорители на кронштейнах,
кабели по стене, у входа — генератор, ящики, бочка с водой и солнечные панели на стойках. Внутри — аппаратная:
пульты с ручками и тумблерами вдоль стен, ряды экранов с волнами, стойки с катушками, карта эфира, лотки кабелей
под потолком; экспонат — на круглой тумбе-тарелке с наушниками на стойке.
Запуск: blender --background --factory-startup --python scripts/blender/floor_radio.py -- <репо> <превью>
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
from floorbase import C, FX, FZ, W, ZB, ZF, beam, rng, slab, taper  # noqa: E402

SAND, SAND2, BLUE, BLUE2, SKY, RED = "E2C08A", "C8A06A", "2E5E9E", "1E4478", "7EC8E8", "D83A30"
WHITE, STEEL, DARK, PANEL, SCREEN, GLASS = "F2EEE4", "9AA4AE", "2A2E36", "3A4250", "5AE0B0", "C8E8F8"
CREAM, WOOD = "EFE2C4", "A87A48"

F = B.Floor("RA", "FloppyFennec", quiet=(SAND2, "C8B08A", "5A6270"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL

# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, SAND, SAND2, BLUE, "C8B08A", "4A5260", roof="flat", roof_col=SAND, band=(12.8, 13.4, SKY),
         side=S.side_windows(F, BLUE, GLASS, kind="rect", y0=7.0, y1=10.6, xs=(-12.45, -4.95, 2.55, 10.05)))
# длинное окно аппаратной с жалюзи и козырёк
FG.box(-13.0, 3.0, 6.2, 11.0, -FZ - 0.92, -FZ - 0.88, GLASS)
FS.frame_xy(K.rect(-13.4, 3.4, 5.8, 11.4), K.rect(-13.0, 3.0, 6.2, 11.0), -FZ - 1.15, -FZ - 0.88, BLUE)
for k in range(9):
    y = 6.6 + 0.48 * k
    FS.box(-12.9, 2.9, y, y + 0.14, -FZ - 1.0, -FZ - 0.94, WHITE)
for x in (-8.0, -2.6):
    FS.box(x - 0.1, x + 0.1, 6.2, 11.0, -FZ - 1.05, -FZ - 0.9, BLUE)
FS.loft([(-13.8, 11.8, -FZ - 0.9), (3.8, 11.8, -FZ - 0.9), (3.8, 12.0, -FZ - 0.9), (-13.8, 12.0, -FZ - 0.9)],
        [(-13.8, 11.2, -FZ - 2.6), (3.8, 11.2, -FZ - 2.6), (3.8, 11.4, -FZ - 2.6), (-13.8, 11.4, -FZ - 2.6)], BLUE2)
# эмблема над окном: решётчатая вышка и волны эфира вправо — стена над аппаратной не пустая; перед поясом фасада (1.02)
TXc, TYc = -9.0, 12.3
for e in (-1, 1):
    beam(FS, (TXc + e * 1.0, TYc, -FZ - 1.14), (TXc, TYc + 2.6, -FZ - 1.14), 0.16, 0.12, WHITE, up=(0, 0, 1))
for k in range(3):
    y = TYc + 0.6 + 0.65 * k
    w = 1.0 * (1 - (y - TYc) / 2.6)
    FS.box(TXc - w, TXc + w, y - 0.06, y + 0.06, -FZ - 1.18, -FZ - 1.03, WHITE)
FS.prism_xy(K.ngon(TXc, TYc + 2.7, 0.26, 8), -FZ - 1.2, -FZ - 1.03, "E04A3A")
for k, r in enumerate((0.8, 1.3, 1.8)):  # волны
    pts = [(TXc + r * math.cos(t), TYc + 2.7 + r * math.sin(t)) for t in [math.radians(-40 + 80 * j / 5) for j in range(6)]]
    for a0, a1 in zip(pts, pts[1:]):
        beam(FS, (a0[0], a0[1], -FZ - 1.14), (a1[0], a1[1], -FZ - 1.14), 0.2, 0.1, (WHITE, "F2C83A", WHITE)[k], up=(0, 0, 1))
# дверь с иллюминатором и ступенями
DX = 8.0
FS.box(DX - 1.8, DX + 1.8, 1.0, 7.6, -FZ - 1.0, -FZ - 0.88, BLUE)
FS.box(DX - 1.4, DX + 1.4, 1.0, 7.2, -FZ - 1.08, -FZ - 1.0, BLUE2)
FG.prism_xy(K.ngon(DX, 5.6, 0.6, 10), -FZ - 1.12, -FZ - 1.08, GLASS)
FS.box(DX + 0.8, DX + 1.1, 3.8, 4.2, -FZ - 1.25, -FZ - 1.08, STEEL)
for k in range(2):
    FR.box(DX - 2.2 - 0.3 * k, DX + 2.2 + 0.3 * k, 0.5 - 0.5 * k, 1.0 - 0.5 * k, -FZ - 1.6 - 0.6 * k, -FZ - 0.88, SAND2)
# контрфорсы самана и вывеска-эмблема над дверью: мачта и волны эфира
for x in (-16.2, 4.6, 11.2):
    FR.box(x - 0.6, x + 0.6, 1.0, 12.8, -FZ - 1.5, -FZ - 0.88, SAND2)
    FR.loft([(x - 0.6, 12.8, -FZ - 1.5), (x + 0.6, 12.8, -FZ - 1.5), (x + 0.6, 12.8, -FZ - 0.88), (x - 0.6, 12.8, -FZ - 0.88)],
            [(x - 0.6, 14.0, -FZ - 0.9), (x + 0.6, 14.0, -FZ - 0.9), (x + 0.6, 14.0, -FZ - 0.88), (x - 0.6, 14.0, -FZ - 0.88)], SAND2)
FS.prism_xy(K.ngon(DX, 9.6, 1.3, 16), -FZ - 1.1, -FZ - 0.88, WHITE)
FS.prism_xy(K.ngon(DX, 9.6, 1.1, 16), -FZ - 1.2, -FZ - 1.1, BLUE)
FS.prism_xy([(DX - 0.5, 8.7), (DX + 0.5, 8.7), (DX + 0.08, 10.3), (DX - 0.08, 10.3)], -FZ - 1.3, -FZ - 1.2, WHITE)
for k, r in enumerate((0.45, 0.8)):
    for e in (-1, 1):
        a0, a1 = (math.radians(30), math.radians(-30)) if e > 0 else (math.radians(150), math.radians(210))
        beam(FS, (DX + r * math.cos(a0), 10.3 + r * math.sin(a0), -FZ - 1.25), (DX + r * math.cos(a1), 10.3 + r * math.sin(a1), -FZ - 1.25),
             0.1, 0.08, "F2C230", up=(0, 0, 1))
# кабели по стене от мачты к окну
for k, y in enumerate((14.2, 14.6)):
    FS.box(-14.0, 15.6, y, y + 0.14, -FZ - 1.02, -FZ - 0.9, DARK if k else RED)
# мачта на правом углу (по фасаду −x): решётка с поясами и огнём
MX, MZ = -FX - 1.2, -FZ - 1.2
for sx in (-1, 1):
    for sz in (-1, 1):
        beam(FS, (MX + sx * 0.9, -0.1, MZ + sz * 0.9), (MX + sx * 0.35, 18.4, MZ + sz * 0.35), 0.16, 0.16, RED if sx > 0 else WHITE)
for k in range(9):
    y = 1.0 + 1.9 * k
    t = y / 18.4
    h = 0.9 - 0.55 * t
    col = RED if k % 2 == 0 else WHITE
    for a, b in (((-h, -h), (h, -h)), ((h, -h), (h, h)), ((h, h), (-h, h)), ((-h, h), (-h, -h))):
        beam(FS, (MX + a[0], y, MZ + a[1]), (MX + b[0], y + 0.9, MZ + b[1]), 0.1, 0.1, col)
FS.prism_xz(K.ngon(MX, MZ, 0.3, 8), 18.4, 18.8, DARK)
FG.prism_xz(K.ngon(MX, MZ, 0.25, 8), 18.0, 18.4, "FF5040")
# большая тарелка антенны на решётчатой опоре слева (по фасаду +x), смотрит вверх-вперёд
AX, AZ = 12.6, -FZ - 1.9
F.objects(True)
for sx in (-1, 1):
    beam(FS, (AX + sx * 1.2, -0.1, AZ + 0.3), (AX + sx * 0.3, 9.6, AZ + 0.3), 0.22, 0.22, STEEL)
    for k in range(4):
        y = 1.0 + 2.2 * k
        beam(FS, (AX - 1.1 + 0.2 * k, y, AZ + 0.3), (AX + 1.1 - 0.2 * k, y + 2.0, AZ + 0.3), 0.1, 0.1, STEEL)
FS.box(AX - 0.6, AX + 0.6, 9.4, 10.2, AZ - 0.3, AZ + 0.9, DARK)
S.dish(FS, (AX, 12.2, AZ - 0.4), (0, 0.6, -1), 3.0, 0.9, WHITE, STEEL, steps=3, seg=16)
for e in (-1, 1):
    beam(FS, (AX + e * 2.2, 12.2 + 0.6, AZ - 0.9), (AX, 13.0, AZ - 2.6), 0.08, 0.08, DARK)
FS.prism_xy(K.ngon(AX, 13.0, 0.3, 8), AZ - 2.9, AZ - 2.5, RED)
F.objects(False)
# рупоры-громкоговорители на кронштейнах
F.objects(True)
for x in (-16.0, 4.6):
    FS.box(x - 0.1, x + 0.1, 13.6, 14.0, -FZ - 2.0, -FZ - 0.88, STEEL)
    taper(FS, (x, 13.0, -FZ - 1.6), (x, 13.0, -FZ - 3.0), 0.4, 1.4, WHITE)
F.objects(False)
# генератор, ящики, бочка с водой, солнечные панели
F.objects(True)
FS.box(12.6, 16.4, -0.1, 2.0, -FZ - 2.6, -FZ - 1.1, "D8A030")
for k in range(6):
    FS.box(12.8 + 0.6 * k, 13.1 + 0.6 * k, 0.6, 1.6, -FZ - 2.66, -FZ - 2.6, DARK)
FS.prism_xz(K.ngon(16.0, -FZ - 1.6, 0.25, 8), 2.0, 3.2, DARK)
D.crate(FS, -10.0, -FZ - 1.8, y=-0.1, s=1.3)
D.crate(FS, -8.6, -FZ - 1.9, y=-0.1, s=1.1)
D.crate(FS, -9.4, -FZ - 1.8, y=1.2, s=1.0)
D.barrel(FS, -5.8, -FZ - 1.8, y=-0.1, r=0.7, h=1.6, wood=BLUE, hoop=DARK)
for k in range(3):
    x = -0.4 + 2.6 * k
    beam(FS, (x, -0.1, -FZ - 2.0), (x, 1.2, -FZ - 2.0), 0.15, 0.15, STEEL)
    beam(FS, (x - 1.2, 1.0, -FZ - 1.3), (x - 1.2, 2.0, -FZ - 2.7), 2.2, 0.1, BLUE2, up=(0, 0, 1))
F.objects(False)
for k in range(3):
    x = -0.4 + 2.6 * k
    FG.loft([(x - 2.2, 1.06, -FZ - 1.3), (x - 0.2, 1.06, -FZ - 1.3), (x - 0.2, 1.1, -FZ - 1.3), (x - 2.2, 1.1, -FZ - 1.3)],
            [(x - 2.2, 2.06, -FZ - 2.7), (x - 0.2, 2.06, -FZ - 2.7), (x - 0.2, 2.1, -FZ - 2.7), (x - 2.2, 2.1, -FZ - 2.7)], "3A6AB8")

# ══ ИНТЕРЬЕР: аппаратная ══════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
S.interior(F, CREAM, "8A94A0", "3A4250", BLUE, wain=(4.4, "5A6270"), beams=None)
for k in range(5):  # лотки кабелей под потолком
    x = -12.0 + 6.0 * k
    IS.box(x - 0.8, x + 0.8, C - 1.6, C - 1.4, ZF, ZB, STEEL)
    for e in (-0.5, 0.0, 0.5):
        IS.box(x + e - 0.08, x + e + 0.08, C - 1.4, C - 1.25, ZF, ZB, (RED, DARK, BLUE)[int(e * 2 + 1)])
F.objects(True)
for s in (-1, 1):  # пульты вдоль боковых стен
    x0 = s * (W - 0.88)
    xi = x0 - s * 3.0
    IS.box(*sorted((x0, xi)), 0.0, 2.6, -12.0, 6.0, PANEL)
    IS.loft([(xi, 2.6, -12.0), (x0 - s * 1.2, 3.4, -12.0), (x0 - s * 1.2, 3.4, 6.0), (xi, 2.6, 6.0)],
            [(xi, 2.4, -12.0), (x0 - s * 1.2, 3.2, -12.0), (x0 - s * 1.2, 3.2, 6.0), (xi, 2.4, 6.0)], DARK)
    for k in range(16):
        z = -11.4 + 1.1 * k
        col = (RED, "F2C230", SCREEN, WHITE)[int(rng(k, s) * 4)]
        IS.box(xi + s * 0.5 - 0.15, xi + s * 0.5 + 0.15, 2.75 + 0.1, 3.0 + 0.1, z - 0.15, z + 0.15, col)
        IS.box(xi + s * 1.3 - 0.08, xi + s * 1.3 + 0.08, 3.1, 3.3, z - 0.08, z + 0.08, WHITE)
    for k in range(4):  # экраны над пультами
        z = -10.5 + 4.2 * k
        IS.box(*sorted((x0, x0 - s * 0.5)), 4.8, 8.0, z - 1.8, z + 1.8, DARK)
        d0, d1 = sorted((x0 - s * 0.5, x0 - s * 0.54))
        IG.box(d0, d1, 5.1, 7.7, z - 1.5, z + 1.5, "1E4A40")
        for j in range(6):
            yy = 6.4 + 0.8 * math.sin(j * 1.3 + k)
            IS.box(*sorted((x0 - s * 0.55, x0 - s * 0.6)), yy - 0.08, yy + 0.08, z - 1.4 + 0.47 * j, z - 0.9 + 0.47 * j, SCREEN)
# стойки с катушками у дальней стены
for k, x in enumerate((-12.0, -7.6, 7.6, 12.0)):
    IS.box(x - 1.8, x + 1.8, 0.0, 8.6, ZF + 0.88, ZF + 2.6, PANEL)
    disc_y = 6.4 if k % 2 else 3.4
    S.disc(IS, (x, disc_y, ZF + 2.6), (0, 0, 1), 1.2, 0.15, STEEL, seg=12)
    S.disc(IS, (x, disc_y, ZF + 2.75), (0, 0, 1), 0.35, 0.1, DARK, seg=8)
    for j in range(5):
        IS.box(x - 1.4 + 0.6 * j, x - 1.1 + 0.6 * j, 9.0 - 2.2 * (k % 2) - (1.0 if k % 2 == 0 else 0.0), 9.3 - 2.2 * (k % 2) - (1.0 if k % 2 == 0 else 0.0),
               ZF + 2.6, ZF + 2.7, (RED, SCREEN, "F2C230", WHITE, SCREEN)[j])
F.objects(False)
# карта эфира на дальней стене: синяя доска, синусоиды-волны, точки станций
IS.box(-4.6, 4.6, 9.4, 14.4, ZF + 0.88, ZF + 1.0, "1E3050")
for j, col in enumerate((SCREEN, "F2C230", RED)):
    pts = [(-4.2 + 8.4 * t / 12, 11.9 + (0.8 - 0.25 * j) * math.sin(t * 1.1 + j * 1.7)) for t in range(13)]
    for a, b in zip(pts, pts[1:]):
        beam(IS, (a[0], a[1], ZF + 1.05), (b[0], b[1], ZF + 1.05), 0.1, 0.08, col, up=(0, 0, 1))
for k in range(5):
    IS.prism_xy(K.ngon(-3.6 + 1.8 * k, 10.0 + 3.6 * rng(k, 9), 0.18, 6), ZF + 1.0, ZF + 1.12, "F2C230")
# стулья у пультов и вешалка с наушниками
F.objects(True)
for s in (-1, 1):
    for z in (-6.0, 1.0):
        x = s * (W - 5.2)
        IS.prism_xz(K.ngon(x, z, 0.8, 8), 1.6, 1.9, BLUE)
        IS.box(x - s * 0.7 - 0.1, x - s * 0.7 + 0.1, 1.9, 3.6, z - 0.7, z + 0.7, BLUE)
        IS.box(x - 0.1, x + 0.1, 0.3, 1.6, z - 0.1, z + 0.1, STEEL)
        IS.prism_xz(K.ngon(x, z, 0.7, 5), 0.0, 0.3, DARK)
F.objects(False)
for x, z in ((-6.0, -8.0), (6.0, -8.0), (-6.0, 4.0), (6.0, 4.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.0, C - 1.6, z - 0.03, z + 0.03, DARK)
    D.lantern(IS, IG, x, C - 4.0, z, s=1.0, cap=BLUE2, light="FFF2C8")
# постамент: тумба-тарелка (вогнутая чаша) на синем барабане, рядом стойка с наушниками
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, 0.5, BLUE2)
IR.prism_xz(K.ngon(px, pz, 3.5, 16), 0.5, TOP - 0.2, BLUE)
S.annulus(IS, (px, TOP - 0.2, pz), (0, 1, 0), 2.8, 3.7, 0.2, WHITE, seg=16)
IS.prism_xz(K.ngon(px, pz, 2.85, 16), TOP - 0.2, TOP, STEEL)
F.objects(True)
HX = px + 4.6
IS.box(HX - 0.12, HX + 0.12, 0.0, 4.4, pz - 0.12, pz + 0.12, STEEL)
IS.prism_xz(K.ngon(HX, pz, 0.6, 8), 0.0, 0.2, DARK)
for k in range(7):
    a = math.pi * k / 6
    IS.box(HX - 0.12, HX + 0.12, 4.4 + 0.9 * math.sin(a) - 0.1, 4.4 + 0.9 * math.sin(a) + 0.1,
           pz + 0.9 * math.cos(a) - 0.12, pz + 0.9 * math.cos(a) + 0.12, DARK)
for e in (-1, 1):
    IS.box(HX - 0.3, HX + 0.3, 3.8, 4.6, pz + e * 0.95 - 0.25, pz + e * 0.95 + 0.25, RED)
F.objects(False)
B.lift_leaves(IS, BLUE, SAND)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, SAND, "C8B08A", SAND)
SL.cone([(MX - 0.9, -0.1, MZ - 0.9), (MX + 0.9, -0.1, MZ - 0.9), (MX + 0.9, -0.1, MZ + 0.9), (MX - 0.9, -0.1, MZ + 0.9)],
        (MX, 18.8, MZ), RED)
SL.prism_xy(K.ngon(AX, 12.2, 3.0, 8), AZ - 0.6, AZ - 0.2, WHITE)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.95, 0.88)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Screens", (0, 6, -10), 700, (0.5, 1.0, 0.8))])
