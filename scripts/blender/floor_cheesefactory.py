"""Этаж «Сердце сырного хранилища» музея-небоскрёба (десятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — сырный завод. Снаружи — цех из светло-жёлтого профлиста с рёбрами, пилообразный фронтон, большая
подъёмная дверь у погрузочной рампы с жёлто-чёрными полосами, конвейер выходит из стены и несёт сырные бруски
к кузову грузовичка, справа — два стальных молочных бака с трубой и лесенкой, труба-дымоход, вывеска-ломоть сыра
с дырками, поддоны с ящиками, погрузчик. Внутри — производственный цех: два стальных чана с мешалками и мостками,
трубы под потолком, конвейер вдоль стены с сырными головками и брусками, стеллажи созревания, пульт с лампочками,
полосы безопасности на полу; экспонат — на «сердце хранилища»: стальном барабане с жёлтым светящимся кольцом,
болтами и трубами.
Запуск: blender --background --factory-startup --python scripts/blender/floor_cheesefactory.py -- <репо> <превью>
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

PANEL, PANEL2, STEEL, STEEL2, DARK, YEL = "F2DC8A", "D8BE6A", "B8C0C8", "8A929C", "2A2E34", "F6C832"
CHEESE, CHEESE2, HOLE, BLUE, RED, WHITE = "F6CE4A", "E2A830", "C88A20", "3A6AC8", "D84A3A", "F4F2EA"
GREEN, WOOD, GLASS, GLOW = "4AA04A", "B08A5A", "D8ECF4", "FFE070"

F = B.Floor("VH", "CheeseVaultHeart", quiet=(PANEL2, "A8A498", "6A707A"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def block(p, x, z, y, w, h, d):
    """Сырный брусок с парой дырок на торце."""
    p.box(x - w / 2, x + w / 2, y, y + h, z - d / 2, z + d / 2, CHEESE)
    p.prism_xy(K.ngon(x - w * 0.2, y + h * 0.55, min(w, h) * 0.12, 6), z - d / 2 - 0.03, z - d / 2, HOLE)
    p.prism_xy(K.ngon(x + w * 0.25, y + h * 0.3, min(w, h) * 0.08, 6), z - d / 2 - 0.03, z - d / 2, HOLE)


def stripes(p, x0, x1, y, z0, z1, n):
    for k in range(n):
        xa = x0 + (x1 - x0) * k / n
        p.box(xa, xa + (x1 - x0) / n, y, y + 0.03, z0, z1, YEL if k % 2 else DARK)


# ══ ФАСАД: цех из профлиста ═══════════════════════════════════════════════════════════════════════════════════
S.facade(F, PANEL, DARK, STEEL2, "A8A498", "4A5058", roof="none", top=15.6, boards=(0.8, PANEL2),
         side=S.side_windows(F, STEEL2, GLASS, kind="rect", y0=9.4, y1=12.6, w=3.0, xs=(-9.50, -1.50, 6.50)))
for k in range(6):  # пилообразный фронтон с окнами
    x0 = -FX + 2 * FX * k / 6
    x1 = x0 + 2 * FX / 6
    FR.prism_xy([(x0, 15.6), (x1, 15.6), (x1, 18.8)], -FZ - 1.2, -FZ - 0.88, PANEL)
    FG.prism_xy([(x1 - 0.4, 16.0), (x1 - 0.4, 18.2), (x1 - 2.6, 16.0)], -FZ - 1.24, -FZ - 1.2, "34505C")  # тёмное стекло
    FS.box(x1 - 0.2, x1 + 0.1, 15.6, 18.9, -FZ - 1.3, -FZ - 0.88, STEEL2)
FS.box(-FX - 0.3, FX + 0.3, 15.5, 15.8, -FZ - 1.4, -FZ - 0.88, STEEL2)
# погрузочная рампа и подъёмная дверь с полосами
FR.box(-9.0, 1.0, -0.1, 1.6, -FZ - 3.0, -FZ - 0.88, "8A8A86")
stripes(FS, -9.0, 1.0, 1.6, -FZ - 3.0, -FZ - 2.6, 10)
FS.box(-8.0, 0.0, 1.6, 9.0, -FZ - 0.96, -FZ - 0.88, STEEL2)
for k in range(12):
    FS.box(-7.8, -0.2, 1.8 + 0.6 * k, 1.92 + 0.6 * k, -FZ - 1.02, -FZ - 0.96, STEEL)
for e in (-8.4, 0.4):
    FS.box(e - 0.35, e + 0.35, 1.6, 9.4, -FZ - 1.2, -FZ - 0.88, YEL)
    for k in range(8):
        FS.box(e - 0.36, e + 0.36, 2.0 + 0.9 * k, 2.4 + 0.9 * k, -FZ - 1.24, -FZ - 1.2, DARK)
# вывеска-ломоть сыра с дырками
FS.prism_xy([(-6.0, 10.6), (2.0, 10.6), (2.0, 13.4)], -FZ - 1.2, -FZ - 0.88, CHEESE)
FS.box(-6.0, 2.0, 10.0, 10.6, -FZ - 1.2, -FZ - 0.88, CHEESE2)
for (x, y, r) in ((0.6, 11.4, 0.35), (-1.4, 11.0, 0.22), (1.2, 12.5, 0.2)):
    FS.prism_xy(K.ngon(x, y, r, 8), -FZ - 1.24, -FZ - 1.2, HOLE)
# конвейер из стены к грузовичку
F.objects(True)
FS.loft([(3.0, 5.0, -FZ - 1.0), (5.0, 5.0, -FZ - 1.0), (5.0, 5.3, -FZ - 1.0), (3.0, 5.3, -FZ - 1.0)],
        [(3.0, 2.6, -FZ - 2.8), (5.0, 2.6, -FZ - 2.8), (5.0, 2.9, -FZ - 2.8), (3.0, 2.9, -FZ - 2.8)], DARK)
for t in (0.2, 0.5, 0.8):
    block(FS, 4.0, -FZ - 1.0 - 1.8 * t, 5.3 - 2.4 * t, 1.0, 0.6, 0.8)
FS.box(3.0, 3.2, -0.1, 4.6, -FZ - 1.6, -FZ - 1.4, STEEL2)
FS.box(4.8, 5.0, -0.1, 4.6, -FZ - 1.6, -FZ - 1.4, STEEL2)
TX = 9.0  # грузовичок
FS.box(TX - 2.6, TX + 2.6, 1.2, 4.6, -FZ - 3.2, -FZ - 1.6, WHITE)
FS.box(TX + 2.6, TX + 4.4, 1.2, 3.6, -FZ - 3.2, -FZ - 1.6, BLUE)
FG.box(TX + 3.2, TX + 4.3, 2.6, 3.4, -FZ - 3.24, -FZ - 3.2, GLASS)
for x in (TX - 1.6, TX + 3.4):
    S.disc(FS, (x, 0.75, -FZ - 3.3), (0, 0, -1), 0.65, 0.3, DARK, seg=10)
FS.prism_xy(K.ngon(TX, 3.0, 0.9, 8), -FZ - 3.24, -FZ - 3.2, CHEESE)
# поддоны с ящиками и погрузчик
for k, x in enumerate((-14.0, -11.4)):
    FS.box(x - 1.1, x + 1.1, -0.1, 0.3, -FZ - 2.6, -FZ - 1.2, WOOD)
    for j in range(2 - k):
        FS.box(x - 1.0, x + 1.0, 0.3 + 1.0 * j, 1.25 + 1.0 * j, -FZ - 2.5, -FZ - 1.3, (CHEESE2, WOOD)[j % 2])
FS.box(13.6, 16.4, 0.6, 2.4, -FZ - 2.8, -FZ - 1.6, YEL)
FS.box(14.6, 16.2, 2.4, 4.0, -FZ - 2.8, -FZ - 1.6, DARK)
FS.box(13.4, 13.6, 0.0, 4.4, -FZ - 2.7, -FZ - 1.7, STEEL2)
FS.box(12.0, 13.4, 0.2, 0.3, -FZ - 2.6, -FZ - 1.8, STEEL2)
for x in (14.2, 15.8):
    S.disc(FS, (x, 0.5, -FZ - 2.9), (0, 0, -1), 0.5, 0.2, DARK, seg=8)
F.objects(False)
# два стальных молочных бака с трубой и лесенкой (правый угол по фасаду −x)
for k, x in enumerate((-17.6, -15.2)):
    FR.prism_xz(K.ngon(x, -FZ - 1.9, 1.0, 12), -0.1, 14.0 - 1.4 * k, STEEL)
    FS.cone([(a, 14.0 - 1.4 * k, b) for a, b in K.ngon(x, -FZ - 1.9, 1.0, 12)], (x, 14.8 - 1.4 * k, -FZ - 1.9), STEEL2)
    for y in (3.0, 7.0, 11.0):
        if y < 13.0 - 1.4 * k:
            FS.prism_xz(K.ngon(x, -FZ - 1.9, 1.06, 12), y - 0.1, y + 0.1, STEEL2)
FS.prism_zy(K.ngon(-FZ - 1.9, 10.0, 0.22, 8), -17.6, -8.0, BLUE)
for k in range(10):
    FS.box(-16.8, -16.2, 1.0 + 1.2 * k, 1.1 + 1.2 * k, -FZ - 2.95, -FZ - 2.9, DARK)
FS.prism_xz(K.ngon(16.6, -FZ - 1.6, 0.7, 10), -0.1, 18.6, STEEL2)
for y in (6.0, 12.0, 17.6):
    FS.prism_xz(K.ngon(16.6, -FZ - 1.6, 0.8, 10), y - 0.15, y + 0.15, RED)

# ══ ИНТЕРЬЕР: производственный цех ════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.6
S.interior(F, "EAE6D8", "9A9A96", "4A5058", STEEL2, wain=(2.6, "6A9A6A"), beams=(5, STEEL2), beam_dir="x")
for x in (-6.0, 0.0, 6.0):  # трубы под потолком
    IS.prism_xy(K.ngon(x, C - 2.6, 0.4, 10), ZF + 0.02, ZB - 0.02, (BLUE, WHITE, YEL)[int(x / 6 + 1)])  # от стены до стены
    for z in (ZF + 0.12, ZB - 0.12):  # фланцы у стен
        IS.prism_xy(K.ngon(x, C - 2.6, 0.62, 10), z - 0.1, z + 0.1, STEEL2)
    for z in (-9.0, 0.0, 9.0):  # подвесы к потолку
        IS.box(x - 0.05, x + 0.05, C - 2.2, C - 0.01, z - 0.05, z + 0.05, STEEL2)
        IS.prism_xy(K.ngon(x, C - 2.6, 0.48, 10), z - 0.12, z + 0.12, STEEL2)
stripes(IQ, -4.4, 4.4, 0.02, 1.6, 2.0, 12)
F.objects(True)
for k, x in enumerate((-10.0, 10.0)):  # два стальных чана с мешалками и мостками
    VZ = -10.0
    IR.prism_xz(K.ngon(x, VZ, 3.0, 16), 0.0, 6.0, STEEL)
    IS.prism_xz(K.ngon(x, VZ, 3.1, 16), 5.8, 6.2, STEEL2)
    IS.prism_xz(K.ngon(x, VZ, 2.8, 16), 5.6, 5.8, "F8F0C8")
    IS.box(x - 0.15, x + 0.15, 5.6, 9.6, VZ - 0.15, VZ + 0.15, DARK)
    IS.box(x - 1.6, x + 1.6, 9.4, 9.8, VZ - 0.2, VZ + 0.2, DARK)
    for e in (-1, 1):
        IS.box(x + e * 2.6 - 0.2, x + e * 2.6 + 0.2, 0.0, 1.0, VZ - 2.0, VZ + 2.0, STEEL2)
IS.box(-W + 0.9, W - 0.9, 6.2, 6.5, -13.6, -12.4, DARK)
for k in range(18):
    x = -W + 1.4 + (2 * W - 2.8) * k / 17
    IS.box(x - 0.05, x + 0.05, 6.5, 7.8, -12.5, -12.4, YEL)
IS.box(-W + 0.9, W - 0.9, 7.8, 7.95, -12.55, -12.35, YEL)
# конвейер вдоль правой стены с головками и брусками
CXc = W - 2.4
IS.box(CXc - 1.0, CXc + 1.0, 2.4, 2.8, -6.0, 8.0, DARK)
for z in (-5.4, -1.0, 3.4, 7.4):
    IS.box(CXc - 0.8, CXc + 0.8, 0.0, 2.4, z - 0.15, z + 0.15, STEEL2)
for k in range(6):
    z = -5.0 + 2.4 * k
    if k % 2:
        block(IS, CXc, z, 2.8, 1.2, 0.7, 1.0)
    else:
        IS.prism_xz(K.ngon(CXc, z, 0.75, 12), 2.8, 3.4, CHEESE)
# стеллажи созревания у левой стены
x0 = -W + 0.88
for y in (0.4, 2.8, 5.2):
    IS.box(x0, x0 + 2.2, y - 0.15, y, -4.0, 8.0, WOOD)
    for k in range(5):
        IS.prism_xz(K.ngon(x0 + 1.1, -3.0 + 2.4 * k, 0.85, 10), y, y + 0.7, CHEESE if k % 2 else CHEESE2)
for z in (-4.0, 8.0):
    IS.box(x0, x0 + 2.2, 0.0, 6.0, z - 0.1, z + 0.1, WOOD)
F.objects(False)
# пульт с лампочками на дальней стене
IS.box(-4.0, 4.0, 0.0, 3.0, ZF + 0.88, ZF + 2.2, STEEL2)
IS.box(-4.0, 4.0, 3.0, 7.0, ZF + 0.88, ZF + 1.2, DARK)
for j in range(3):
    for k in range(7):
        IS.prism_xy(K.ngon(-3.0 + 1.0 * k, 4.0 + 1.0 * j, 0.22, 6), ZF + 1.2, ZF + 1.32, (RED, GREEN, YEL)[(j + k) % 3])
for x, z in ((-6.0, -4.0), (6.0, -4.0), (0.0, 5.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.6, C - 0.8, z - 0.03, z + 0.03, DARK)
    IS.cone([(a, C - 4.4, b) for a, b in K.ngon(x, z, 1.0, 8)], (x, C - 3.6, z), STEEL2)
    IG.prism_xz(K.ngon(x, z, 0.5, 8), C - 4.6, C - 4.4, "FFF4D8")
# постамент: «сердце хранилища» — стальной барабан с жёлтым светящимся кольцом и болтами
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, 0.4, DARK)
IR.prism_xz(K.ngon(px, pz, 3.6, 16), 0.4, TOP - 0.2, STEEL)
IG.prism_xz(K.ngon(px, pz, 3.68, 16), 0.8, 1.0, GLOW)
IS.prism_xz(K.ngon(px, pz, 3.3, 16), TOP - 0.2, TOP, YEL)
for k in range(12):
    a = 2 * math.pi * k / 12
    IS.prism_xz(K.ngon(px + 3.45 * math.cos(a), pz + 3.45 * math.sin(a), 0.1, 6), TOP, TOP + 0.08, STEEL2)
for s in (-1, 1):
    IS.prism_zy(K.ngon(pz, 0.9, 0.3, 8), *sorted((px + s * 3.6, px + s * 6.0)), BLUE)
B.lift_leaves(IS, STEEL2, YEL)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, PANEL, "A8A498", PANEL, top=15.6, roof="none")
SL.box(-FX - 0.3, FX + 0.3, 15.6, 18.0, -FZ - 1.2, FZ + 0.3, PANEL2)
for x in (-17.6, -15.2):
    SL.prism_xz(K.ngon(x, -FZ - 1.9, 1.0, 6), -0.1, 14.0, STEEL)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 1900, (1.0, 0.97, 0.9)),
                                                   ("Spot", (0, 13, -3), 3800, (1.0, 0.97, 0.9)),
                                                   ("Glow", (0, 2, -3), 600, (1.0, 0.85, 0.4))])
