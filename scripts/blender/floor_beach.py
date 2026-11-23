"""Этаж «Ящерка-зонтик» музея-небоскрёба (девятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — пляжный отель на дюнах. Снаружи — белая штукатурка с округлыми углами, два яруса балконов с
бирюзовыми перилами и полосатыми маркизами, панорамные окна лобби, над входом — козырёк-волна, у входа — ряд
пляжных зонтов-грибков с шезлонгами, доски для сёрфинга у стены, сумка-холодильник, спасательный круг, пальма,
волейбольный мяч. Внутри — пляжный клуб: бассейн в полу с бортиком и лесенкой, шезлонги и столики под зонтами,
бар-хижина под соломенной крышей, полосатые кабинки для переодевания, полотенца на крючках, гирлянда флажков;
экспонат — на круглом островке в виде полосатого пляжного мяча.
Запуск: blender --background --factory-startup --python scripts/blender/floor_beach.py -- <репо> <превью>
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

WHITE, WHITE2, TURQ, TURQ2, CORAL, YELLOW = "F6F2EA", "DCD6C8", "2EC0C0", "1E9A9E", "F27A5A", "F8D040"
SAND, SAND2, STRAW, WOOD, POOL, GLASS = "F0DCA8", "D8C08A", "D8B060", "A87A48", "4AC8F0", "C8F0F8"
BLUE, PINK = "3A7AE0", "F06A9A"
STRIPES = (CORAL, WHITE, TURQ, WHITE, YELLOW, WHITE)

F = B.Floor("BE", "UmbrellaLizard", quiet=(SAND2, SAND, "C8E0E0"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def parasol(p, x, z, y, r, h, cols, seg=8):
    """Зонт-грибок: шест и полосатый конус-купол сегментами."""
    p.box(x - 0.08, x + 0.08, y, y + h, z - 0.08, z + 0.08, WHITE2)
    for k in range(seg):
        a0, a1 = 2 * math.pi * k / seg, 2 * math.pi * (k + 1) / seg
        p.cone([(x + r * math.cos(a0), y + h - 0.6, z + r * math.sin(a0)), (x + r * math.cos(a1), y + h - 0.6, z + r * math.sin(a1)),
                (x, y + h - 0.6, z)], (x, y + h + 0.3, z), cols[k % len(cols)])


def lounger(p, x, z, y, col, along_x=False):
    """Шезлонг: рама и полосатый лежак с поднятой спинкой."""
    if along_x:
        p.box(x - 1.6, x + 0.8, y + 0.5, y + 0.7, z - 0.6, z + 0.6, col)
        p.loft([(x + 0.8, y + 0.7, z - 0.6), (x + 0.8, y + 0.7, z + 0.6), (x + 0.8, y + 0.5, z + 0.6), (x + 0.8, y + 0.5, z - 0.6)],
               [(x + 1.6, y + 1.8, z - 0.6), (x + 1.6, y + 1.8, z + 0.6), (x + 1.4, y + 1.7, z + 0.6), (x + 1.4, y + 1.7, z - 0.6)], col)
        for e in (-1.4, 0.6):
            p.box(x + e - 0.08, x + e + 0.08, y, y + 0.5, z - 0.6, z + 0.6, WHITE2)
    else:
        p.box(x - 0.6, x + 0.6, y + 0.5, y + 0.7, z - 0.8, z + 1.6, col)
        p.loft([(x - 0.6, y + 0.7, z - 0.8), (x + 0.6, y + 0.7, z - 0.8), (x + 0.6, y + 0.5, z - 0.8), (x - 0.6, y + 0.5, z - 0.8)],
               [(x - 0.6, y + 1.8, z - 1.6), (x + 0.6, y + 1.8, z - 1.6), (x + 0.6, y + 1.7, z - 1.4), (x - 0.6, y + 1.7, z - 1.4)], col)
        for e in (-0.6, 1.4):
            p.box(x - 0.6, x + 0.6, y, y + 0.5, z + e - 0.08, z + e + 0.08, WHITE2)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, WHITE, WHITE2, TURQ, SAND, "D8EEF0", roof="flat", roof_col=WHITE, top=16.4,
         side=S.side_windows(F, TURQ, GLASS, kind="tall", y0=6.4, y1=10.4, w=2.2, xs=(-9.10, -1.10, 6.90)))
for x in (-FX - 0.2, FX + 0.2):  # округлые углы
    FR.prism_xz(K.ngon(x, -FZ, 1.4, 12), 1.0, 16.4, WHITE)
# панорамные окна лобби и вход с козырьком-волной
for x0, x1 in ((-15.4, -3.4), (3.4, 15.4)):
    FG.box(x0, x1, 1.6, 6.2, -FZ - 0.92, -FZ - 0.88, GLASS)
    FS.frame_xy(K.rect(x0 - 0.3, x1 + 0.3, 1.3, 6.5), K.rect(x0, x1, 1.6, 6.2), -FZ - 1.1, -FZ - 0.88, TURQ2)
    for k in range(1, 4):
        x = x0 + (x1 - x0) * k / 4
        FS.box(x - 0.08, x + 0.08, 1.6, 6.2, -FZ - 1.0, -FZ - 0.9, TURQ2)
FG.box(-2.4, 2.4, 1.0, 6.4, -FZ - 0.94, -FZ - 0.88, GLASS)
FS.frame_xy(K.rect(-2.7, 2.7, 1.0, 6.7), K.rect(-2.4, 2.4, 1.0, 6.4), -FZ - 1.1, -FZ - 0.88, TURQ2)
FS.box(-0.06, 0.06, 1.0, 6.4, -FZ - 1.0, -FZ - 0.9, TURQ2)
for k in range(8):
    x0 = -4.8 + 1.2 * k
    y = 7.2 + 0.4 * math.sin(k * 0.9)
    FS.loft([(x0, y, -FZ - 0.9), (x0 + 1.2, y, -FZ - 0.9), (x0 + 1.2, y + 0.3, -FZ - 0.9), (x0, y + 0.3, -FZ - 0.9)],
            [(x0, y - 0.6, -FZ - 3.0), (x0 + 1.2, y - 0.6, -FZ - 3.0), (x0 + 1.2, y - 0.3, -FZ - 3.0), (x0, y - 0.3, -FZ - 3.0)], TURQ)
# два яруса балконов с перилами и полосатыми маркизами
for y0 in (8.0, 12.4):
    for x0, x1 in ((-16.4, -10.6), (-8.4, -2.6), (2.6, 8.4), (10.6, 16.4)):
        FR.box(x0, x1, y0 - 0.4, y0, -FZ - 2.2, -FZ - 0.88, WHITE)
        FG.box(x0 + 0.6, x1 - 0.6, y0, y0 + 3.0, -FZ - 0.92, -FZ - 0.88, GLASS)
        FS.frame_xy(K.rect(x0 + 0.3, x1 - 0.3, y0, y0 + 3.3), K.rect(x0 + 0.6, x1 - 0.6, y0, y0 + 3.0), -FZ - 1.05, -FZ - 0.88, TURQ2)
        for k in range(8):
            x = x0 + 0.2 + (x1 - x0 - 0.4) * k / 7
            FS.box(x - 0.06, x + 0.06, y0, y0 + 1.4, -FZ - 2.15, -FZ - 2.05, TURQ)
        FS.box(x0, x1, y0 + 1.4, y0 + 1.55, -FZ - 2.2, -FZ - 2.0, TURQ2)
        for k in range(5):
            xa = x0 + (x1 - x0) * k / 5
            FS.loft([(xa, y0 + 3.9, -FZ - 0.9), (xa + (x1 - x0) / 5, y0 + 3.9, -FZ - 0.9), (xa + (x1 - x0) / 5, y0 + 4.05, -FZ - 0.9),
                     (xa, y0 + 4.05, -FZ - 0.9)],
                    [(xa, y0 + 3.0, -FZ - 2.2), (xa + (x1 - x0) / 5, y0 + 3.0, -FZ - 2.2), (xa + (x1 - x0) / 5, y0 + 3.15, -FZ - 2.2),
                     (xa, y0 + 3.15, -FZ - 2.2)], (CORAL, WHITE)[k % 2] if y0 < 10 else (TURQ, WHITE)[k % 2])
# зонты, шезлонги, доски, холодильник, круг, пальма, мяч
F.objects(True)
for k, x in enumerate((-13.0, -7.6, 7.6, 13.0)):
    parasol(FS, x, -FZ - 2.3, -0.1, 1.6, 4.0, STRIPES[k % 3 * 2:k % 3 * 2 + 2] + (WHITE,))
    lounger(FS, x + (1.6 if k < 2 else -1.6), -FZ - 2.0, -0.1, (CORAL, TURQ, YELLOW, PINK)[k], along_x=True)
for k, (x, col) in enumerate(((4.2, YELLOW), (5.0, CORAL), (5.8, TURQ))):
    FS.prism_xy(K.octa(x, 3.2, 0.35, 3.2, 0.3), -FZ - 1.2 - 0.1 * k, -FZ - 1.05 - 0.1 * k, col)
FS.box(-5.6, -4.0, -0.1, 1.0, -FZ - 1.9, -FZ - 1.1, BLUE)
FS.box(-5.7, -3.9, 1.0, 1.2, -FZ - 2.0, -FZ - 1.0, WHITE)
S.annulus(FS, (-FX - 1.1, 3.4, -FZ - 1.6), (1, 0, 0), 0.55, 1.0, 0.2, CORAL, seg=12)
D.palm(FS, (FX + 1.4, -0.1, -FZ - 1.6), (-0.6, -0.3), 10.5)
for k in range(6):  # волейбольный мяч: пояса разного цвета
    r = 0.6 * math.sin(math.pi * (k + 0.5) / 6)
    FS.prism_xz(K.ngon(1.0, -FZ - 2.4, r, 8), -0.1 + 0.2 * k, 0.1 + 0.2 * k, (WHITE, BLUE, YELLOW)[k % 3])
F.objects(False)

# ══ ИНТЕРЬЕР: пляжный клуб с бассейном ════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
S.interior(F, "F4ECDC", SAND, "DCEFF0", TURQ, wain=(2.2, "8AD8D8"), beams=None)
for k in range(8):  # гирлянда флажков под потолком
    z = ZF + 2.0 + 3.8 * k
    if k % 2 == 0:
        D.chain(IS, (-W + 1.0, C - 2.4, z), (W - 1.0, C - 2.4, z), 12, 0.06, "E8E0D0", sag=1.0)
        for j in range(10):
            x = -W + 2.6 + (2 * W - 5.2) * j / 9
            yy = C - 2.4 - 1.0 * (1 - ((x / (W - 1.0)) ** 2))
            IS.prism_xy([(x - 0.45, yy), (x + 0.45, yy), (x, yy - 0.9)], z - 0.04, z + 0.04, STRIPES[j % 6] if j % 2 else CORAL)
# бассейн в полу у дальней стены
for x0, x1, z0, z1 in ((-10.0, 10.0, ZF + 1.2, ZF + 1.8), (-10.0, 10.0, ZF + 7.3, ZF + 7.9), (-10.0, -9.4, ZF + 1.8, ZF + 7.3),
                       (9.4, 10.0, ZF + 1.8, ZF + 7.3)):  # бортик бассейна рамкой
    IR.box(x0, x1, 0.0, 0.6, z0, z1, WHITE)
IS.box(-9.4, 9.4, 0.0, 0.3, ZF + 1.8, ZF + 7.3, "3AA8D8")
IG.box(-9.4, 9.4, 0.4, 0.45, ZF + 1.8, ZF + 7.3, POOL)
for k in range(6):
    IS.box(-9.2 + 3.6 * k, -8.8 + 3.6 * k, 0.45, 0.47, ZF + 2.0, ZF + 7.1, "8AE0F8")
for e in (-0.6, 0.6):
    IS.loft([(7.0 + e, 0.6, ZF + 7.0), (7.1 + e, 0.6, ZF + 7.0), (7.1 + e, 0.6, ZF + 7.1), (7.0 + e, 0.6, ZF + 7.1)],
            [(7.0 + e, 2.0, ZF + 7.6), (7.1 + e, 2.0, ZF + 7.6), (7.1 + e, 2.0, ZF + 7.7), (7.0 + e, 2.0, ZF + 7.7)], "C8C8C8")
F.objects(True)
# бар-хижина под соломенной крышей у правой стены
HX = W - 0.88
IS.box(HX - 6.0, HX - 4.4, 0.0, 3.4, -2.0, 8.0, WOOD)
IS.box(HX - 6.3, HX - 4.2, 3.4, 3.7, -2.3, 8.3, "8A5A32")
for z in (-2.0, 8.0):
    IS.box(HX - 6.0, HX - 5.6, 0.0, 8.0, z - 0.2, z + 0.2, WOOD)
IS.loft([(HX, 9.6, -3.0), (HX, 9.6, 9.0), (HX, 9.9, 9.0), (HX, 9.9, -3.0)],
        [(HX - 7.2, 7.4, -3.0), (HX - 7.2, 7.4, 9.0), (HX - 7.2, 7.8, 9.0), (HX - 7.2, 7.8, -3.0)], STRAW)
for k in range(6):
    IS.prism_xz(K.ngon(HX - 1.0, -0.6 + 1.6 * k, 0.25, 6), 4.6, 5.6, (CORAL, YELLOW, TURQ, PINK, "6AE070", BLUE)[k])
# шезлонги и столики с зонтами у левой стены
for k, z in enumerate((-12.0, -6.0, 0.0)):
    lounger(IS, -W + 3.0, z, 0.0, (CORAL, TURQ, YELLOW)[k])
for z in (-9.0, -3.0):
    IS.prism_xz(K.ngon(-W + 6.6, z, 1.0, 10), 2.4, 2.6, WHITE)
    IS.box(-W + 6.5, -W + 6.7, 0.0, 2.4, z - 0.1, z + 0.1, WHITE2)
    parasol(IS, -W + 6.6, z, 2.6, 2.0, 4.6, (CORAL, WHITE, TURQ, WHITE))
# полосатые кабинки у левой стены у лифта
for k in range(2):
    z = 6.0 + 4.0 * k
    for j in range(6):
        IS.box(-W + 0.9, -W + 4.4, 0.0, 7.0, z + 0.6 * j - 1.8, z + 0.6 * j - 1.2, (TURQ, WHITE)[j % 2])
    IS.box(-W + 0.9, -W + 4.6, 7.0, 7.4, z - 2.0, z + 2.0, CORAL)
# вышка спасателя у бассейна, надувной круг, доски для сёрфинга, пальмы в кадках, пляжный мяч
for ex in (10.6, 12.4):
    for ez in (ZF + 3.0, ZF + 5.0):
        beam(IS, (ex, 0.0, ez), (11.5, 3.8, ZF + 4.0), 0.14, 0.14, WHITE)
IS.box(10.6, 12.4, 3.8, 4.1, ZF + 3.1, ZF + 4.9, WOOD)
IS.box(10.6, 12.4, 4.1, 5.6, ZF + 3.1, ZF + 3.3, WOOD)
IS.box(11.45, 11.55, 4.1, 8.0, ZF + 4.7, ZF + 4.8, WHITE2)
parasol(IS, 11.5, ZF + 4.75, 8.0, 1.4, 0.8, (CORAL, WHITE, CORAL, WHITE))
S.annulus(IS, (-4.6, 0.47, ZF + 4.4), (0, 1, 0), 0.55, 1.1, 0.28, CORAL, seg=12)
S.annulus(IS, (3.8, 0.47, ZF + 5.6), (0, 1, 0), 0.45, 0.9, 0.24, YELLOW, seg=12)
for k, (x, col) in enumerate(((-15.4, CORAL), (-14.0, TURQ), (-12.6, YELLOW))):  # доски у дальней стены
    beam(IS, (x, 0.0, ZF + 2.2), (x + 0.2 * (k - 1), 6.4 - 0.4 * k, ZF + 1.05), 1.0, 0.16, col, up=(0, 0, 1))
for x, z in ((-8.6, -9.4), (8.6, -9.4)):  # кадки с пальмами по бокам от постамента
    IS.prism_xz(K.ngon(x, z, 0.9, 10), 0.0, 1.0, WOOD)
    IS.prism_xz(K.ngon(x, z, 1.0, 10), 1.0, 1.2, "8A5A32")
    D.palm(IS, (x, 1.2, z), (0.5 if x > 0 else -0.5, -0.4), 6.0)
for k in range(6):  # пляжный мяч у шезлонгов
    a0 = 2 * math.pi * k / 6
    IS.prism_xz([(-W + 8.6, -6.0)] + [(-W + 8.6 + 0.6 * math.cos(a0 + math.pi / 3 * j / 2), -6.0 + 0.6 * math.sin(a0 + math.pi / 3 * j / 2))
                                       for j in range(3)], 0.0, 1.1, (CORAL, WHITE, TURQ, WHITE, YELLOW, WHITE)[k])
F.objects(False)
IQ.box(-11.0, 11.0, 0.02, 0.07, ZF + 0.9, ZF + 9.4, "D8B080")  # дощатый настил вокруг бассейна
for k in range(12):
    x = -10.5 + 1.9 * k
    IQ.box(x - 0.04, x + 0.04, 0.07, 0.08, ZF + 0.9, ZF + 9.4, "A87A48")
for k in range(5):  # полотенца на крючках на правой стене
    z = -14.0 + 2.0 * k
    IS.box(W - 0.98, W - 0.88, 6.6, 6.8, z - 0.1, z + 0.1, "C8C8C8")
    IS.box(W - 1.08, W - 0.98, 3.6, 6.7, z - 0.7, z + 0.7, (CORAL, TURQ, YELLOW, PINK, BLUE)[k])
# постамент: островок-пляжный мяч (полосатые дольки)
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.2, 18), 0.0, 0.3, SAND)
for k in range(6):
    a0, a1 = 2 * math.pi * k / 6, 2 * math.pi * (k + 1) / 6
    pts = [(px, pz)] + [(px + 3.7 * math.cos(a0 + (a1 - a0) * j / 3), pz + 3.7 * math.sin(a0 + (a1 - a0) * j / 3)) for j in range(4)]
    IS.prism_xz(pts, 0.3, TOP - 0.15, (CORAL, WHITE, TURQ, WHITE, YELLOW, WHITE)[k])
IS.prism_xz(K.ngon(px, pz, 3.5, 18), TOP - 0.15, TOP, WHITE)
B.lift_leaves(IS, TURQ2, WHITE)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, WHITE, SAND, WHITE, top=16.4)
for y0 in (8.0, 12.4):
    SL.box(-16.4, 16.4, y0 + 3.0, y0 + 4.0, -FZ - 2.2, -FZ, CORAL if y0 < 10 else TURQ)

F.build(exhibit=(PED[0], TOP, PED[1], 3.0), lamps=[("Hall", (0, 14, 6), 2000, (1.0, 0.97, 0.92)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.98, 0.94)),
                                                   ("Pool", (0, 3, -11), 700, (0.6, 0.9, 1.0))])
