"""Этаж «Поезд-монстр» музея-небоскрёба (восьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — паровозное депо. Снаружи — кирпичный корпус с белыми арками трёх въездов для паровозов, над ними —
круглые часы и пояс-карниз; перед фасадом по рельсам на шпалах стоит паровоз боком — чёрный котёл, труба,
сухопарник, будка машиниста, красные колёса с дышлами и путеочиститель; на правом углу — водонапорная башня-бак на
ножках с хоботом, рядом — семафор с поднятым крылом и куча угля. Внутри — цех депо: рельсы
через весь зал, поворотный круг-постамент, на домкратах — второй котёл в ремонте, колёсные пары у стены, верстаки
и стена с ключами, кран-балка с крюком, кучи угля, фонари; экспонат — на поворотном круге с рельсами.
Запуск: blender --background --factory-startup --python scripts/blender/floor_depot.py -- <репо> <превью>
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

BRICK, BRICK2, STONE, BLACK, RED, STEEL = "9A4A34", "7A3826", "D8D0C0", "26282E", "C8302A", "8A929C"
STEEL2, BRASS, COAL, WOOD, WOOD2, GLASS = "5A626C", "C8982E", "2A2A2E", "8A6440", "5A4028", "FFE0A0"
GREEN = "3A6A4A"
# закопчённый кирпич стен цеха (снаружи — прежний красный): ярко-красный поезд читается на тёмном, атмосфера депо та же
SOOT, SOOT2 = "5E3A30", "4A2C24"

F = B.Floor("DP", "MonsterTrain", quiet=("6A665E", COAL), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def arch(a, y0, y1, w, n=6):
    return [(a - w, y0), (a + w, y0)] + [(a + w * math.cos(math.pi * k / n), y1 + w * math.sin(math.pi * k / n)) for k in range(n + 1)]


def band(p, outer, inner, d0, d1, col):
    for i in range(1, len(outer)):
        j = (i + 1) % len(outer)
        p.prism_xy([outer[i], outer[j], inner[j], inner[i]], d0, d1, col)


def rails_x(p, x0, x1, z, y=0.0):
    """Путь вдоль x: шпалы и два рельса."""
    n = int((x1 - x0) // 1.2)
    for k in range(n + 1):
        x = x0 + 1.2 * k
        p.box(x - 0.3, x + 0.3, y, y + 0.2, z - 1.2, z + 1.2, WOOD2)
    for e in (-1, 1):
        p.box(x0, x1, y + 0.2, y + 0.4, z + e * 0.75 - 0.08, z + e * 0.75 + 0.08, STEEL)


def rails_z(p, z0, z1, x, y=0.0):
    n = int((z1 - z0) // 1.2)
    for k in range(n + 1):
        z = z0 + 1.2 * k
        p.box(x - 1.2, x + 1.2, y, y + 0.06, z - 0.3, z + 0.3, WOOD2)
    for e in (-1, 1):
        p.box(x + e * 0.75 - 0.08, x + e * 0.75 + 0.08, y + 0.06, y + 0.22, z0, z1, STEEL)


def wheel(p, x, y, z, r, z_out, col=RED):
    """Колесо вида сбоку (в плоскости xy) с ободом и ступицей."""
    lo, hi = sorted((z, z + z_out))
    p.prism_xy(K.ngon(x, y, r, 12), lo, hi, col)
    p.prism_xy(K.ngon(x, y, r * 0.35, 8), *sorted((z + z_out, z + z_out * 1.4)), BLACK)


def locomotive(p, g, x0, z, y, face=-1):
    """Паровоз боком вдоль x (дымовая труба у x0): котёл, труба, сухопарник, будка, колёса, дышла, путеочиститель."""
    L = 10.0
    p.prism_zy(K.ngon(z, y + 2.6, 1.2, 12), x0, x0 + L * 0.68, BLACK)
    p.prism_zy(K.ngon(z, y + 2.6, 1.3, 12), x0 + 0.2, x0 + 0.5, BRASS)
    p.prism_zy(K.ngon(z, y + 2.6, 1.3, 12), x0 + L * 0.66, x0 + L * 0.68, BRASS)
    p.prism_xz(K.ngon(x0 + 1.2, z, 0.45, 8), y + 3.6, y + 5.0, BLACK)  # труба
    p.prism_xz(K.ngon(x0 + 1.2, z, 0.65, 8), y + 5.0, y + 5.4, BLACK)
    p.prism_xz(K.ngon(x0 + 4.0, z, 0.5, 8), y + 3.6, y + 4.4, BRASS)  # сухопарник
    p.box(x0 + L * 0.68, x0 + L, y + 1.2, y + 5.2, z - 1.4, z + 1.4, RED)  # будка
    p.box(x0 + L * 0.66, x0 + L + 0.2, y + 5.2, y + 5.5, z - 1.6, z + 1.6, BLACK)
    g.box(x0 + L * 0.72, x0 + L * 0.92, y + 3.4, y + 4.6, z + face * 1.4 - 0.02, z + face * 1.4 + 0.02, GLASS)
    p.box(x0 - 0.2, x0 + L, y + 1.0, y + 1.4, z - 1.3, z + 1.3, BLACK)  # рама
    p.prism_xy([(x0 - 0.2, y + 1.0), (x0 - 1.4, y + 0.1), (x0 - 0.2, y + 0.1)], z - 1.1, z + 1.1, RED)  # путеочиститель
    for k, wx in enumerate((x0 + 2.4, x0 + 4.4, x0 + 6.4)):
        wheel(p, wx, y + 1.0, z + face * 1.15, 0.95, face * 0.25)
    wheel(p, x0 + 0.6, y + 0.6, z + face * 1.15, 0.55, face * 0.25)
    beam(p, (x0 + 2.4, y + 0.7, z + face * 1.55), (x0 + 6.4, y + 0.7, z + face * 1.55), 0.18, 0.12, STEEL)


# ══ ФАСАД: депо ═══════════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, BRICK, SOOT, "3A3430")
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "6A665E")
    slab(FR, axis, fixed, out, 1.18, -half - 0.2, half + 0.2, -0.1, 1.2, STONE)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.2, 16.6, BRICK)
    for k in range(int(2 * half // 4.0) + 1):  # лопатки
        a = -half + 0.2 + 4.0 * k
        if a + 1.0 <= half:
            slab(FR, axis, fixed, out, 1.18, a, a + 1.0, 1.2, 16.6, BRICK2)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, 11.6, 12.2, STONE)
    slab(FR, axis, fixed, out, 1.88, -half - 0.5, half + 0.5, 16.6, 17.4, STONE)
    slab(FR, axis, fixed, out, 1.18, -half - 0.2, half + 0.2, 17.4, 18.9, BRICK2)
    if fi > 0:  # бока и тыл: высокие окна цеха с переплётом
        for a in (-11.0, -3.0, 5.0, 13.0):
            if a + 1.6 > half:
                continue
            d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
            pr = FG.prism_zy if axis == "x" else FG.prism_xy
            pr(arch(a + 0.0, 4.0, 9.6, 1.4), d0, d1, GLASS)
            for i in (-0.5, 0.5):
                slab(FS, axis, fixed, out, 1.0, a + i - 0.05, a + i + 0.05, 4.0, 10.8, STEEL2)
            for y in (6.0, 8.0):
                slab(FS, axis, fixed, out, 1.0, a - 1.4, a + 1.4, y - 0.05, y + 0.05, STEEL2)
            slab(FR, axis, fixed, out, 1.1, a - 1.6, a + 1.6, 3.6, 4.0, STONE)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# три арочных въезда с белыми арками, часы над средним
for k, x in enumerate((-9.0, 0.0, 9.0)):
    FS.prism_xy(arch(x, 1.2, 8.2, 3.2), -FZ - 0.96, -FZ - 0.9, "2A2420" if k == 1 else GREEN)
    band(FS, arch(x, 1.2, 8.2, 3.8), arch(x, 1.2, 8.2, 3.2), -FZ - 1.3, -FZ - 0.88, STONE)
    if k != 1:
        for j in range(5):
            FS.box(x - 3.0 + 1.2 * j + 0.5, x - 3.0 + 1.2 * j + 0.6, 1.2, 8.2, -FZ - 1.0, -FZ - 0.96, "2E5A3E")
        FG.box(x - 2.6, x + 2.6, 6.0, 7.2, -FZ - 1.0, -FZ - 0.96, GLASS)
FS.prism_xy(K.ngon(0.0, 14.2, 1.6, 16), -FZ - 1.2, -FZ - 0.88, STONE)
FS.prism_xy(K.ngon(0.0, 14.2, 1.35, 16), -FZ - 1.26, -FZ - 1.2, "F4F0E4")
FS.box(-0.06, 0.06, 14.1, 15.2, -FZ - 1.3, -FZ - 1.26, BLACK)
FS.box(0.0, 0.8, 14.15, 14.27, -FZ - 1.3, -FZ - 1.26, BLACK)
# пути и паровоз боком перед фасадом
rails_x(FS, -FX - 2.4, 7.6, -FZ - 1.9, y=-0.1)
F.objects(True)
locomotive(FS, FG, -11.0, -FZ - 1.9, 0.3, face=-1)
F.objects(False)
# водонапорная башня, семафор, уголь с тачкой
F.objects(True)
TX, TZ = 15.0, -FZ - 1.6
for e in (-1, 1):
    for f in (-1, 1):
        beam(FS, (TX + e * 1.6, -0.1, TZ + f * 0.9), (TX + e * 1.1, 10.0, TZ + f * 0.6), 0.25, 0.25, WOOD2)
FS.prism_xz(K.ngon(TX, TZ, 2.2, 12), 10.0, 14.2, WOOD)
for y in (10.6, 12.0, 13.4):
    FS.prism_xz(K.ngon(TX, TZ, 2.26, 12), y, y + 0.15, BLACK)
FS.cone([(x, 14.2, z) for x, z in K.ngon(TX, TZ, 2.5, 12)], (TX, 15.8, TZ), BRICK2)
beam(FS, (TX - 1.8, 11.4, TZ), (TX - 4.0, 8.6, TZ - 0.4), 0.4, 0.4, BLACK)
SX = 9.6
FS.box(SX - 0.12, SX + 0.12, -0.1, 9.0, -FZ - 2.8, -FZ - 2.56, BLACK)
FS.prism_xy([(SX, 8.2), (SX + 2.4, 9.2), (SX + 2.4, 9.6), (SX, 8.6)], -FZ - 2.86, -FZ - 2.8, RED)
FG.prism_xy(K.ngon(SX - 0.3, 7.4, 0.22, 8), -FZ - 2.86, -FZ - 2.8, "5AE07A")
FS.prism_xz(K.octa(12.0, -FZ - 1.5, 1.3, 0.6, 0.4), -0.1, 0.9, COAL)  # куча угля
FS.prism_xz(K.octa(12.2, -FZ - 1.5, 0.8, 0.4, 0.25), 0.9, 1.5, COAL)
F.objects(False)

# ══ ИНТЕРЬЕР: цех депо ════════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 0.9
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "6A665E")
rails_z(IS, ZF + 0.9, -7.6, 0.0, y=0.02)
rails_z(IS, 1.6, 6.6, 0.0, y=0.02)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, SOOT)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 1.6, STONE)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, SOOT)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, STONE)
    for k in range(int(2 * half // 4.0) + 1):
        a = -half + 0.2 + 4.0 * k
        behind = idx == 2 and abs(a + 0.4) < 6.4  # за воротами и окном дальней стены пилястр нет: не режут их
        if a + 0.8 <= half and not (gap and abs(a + 0.4) < DOOR[0] + 1.0) and not behind:
            slab(IS, axis, fixed, out, 1.1, a, a + 0.8, 1.6, C, SOOT2)
for k in range(-3, 4):  # стальные фермы
    IS.box(-W, W, C - 0.8, C - 0.3, 4.4 * k - 0.15, 4.4 * k + 0.15, STEEL2)
# котёл на домкратах у левой стены, колёсные пары, верстак и стена ключей
F.objects(True)
BXc, BZc = -11.6, -8.0
IS.prism_xy(K.ngon(BXc, 3.4, 1.6, 12), BZc - 4.4, BZc + 3.4, BLACK)  # котёл лежит вдоль z
for z in (BZc - 3.6, BZc + 2.6):
    IS.box(BXc - 0.9, BXc + 0.9, 0.0, 1.8, z - 0.4, z + 0.4, RED)
IS.prism_xz(K.ngon(BXc, BZc - 3.4, 0.45, 8), 5.0, 6.6, BLACK)
for k, z in enumerate((-1.0, 1.4, 3.8)):
    x = W - 2.6
    for e in (-1, 1):
        IS.prism_zy(K.ngon(z, 1.1, 1.1, 12), x + e * 0.8 - 0.15, x + e * 0.8 + 0.15, BLACK)  # у лифта — не красное пятно
    IS.prism_zy(K.ngon(z, 1.1, 0.2, 8), x - 1.0, x + 1.0, STEEL)
IS.box(W - 3.0, W - 0.88, 2.4, 2.7, -14.0, -8.0, WOOD)
for z in (-13.6, -8.4):
    IS.box(W - 2.9, W - 1.0, 0.0, 2.4, z - 0.2, z + 0.2, WOOD2)
F.objects(False)
IS.box(W - 1.0, W - 0.88, 4.0, 8.0, -14.0, -8.0, "3A3A3A")
for k in range(7):
    z = -13.4 + 0.8 * k
    IS.box(W - 1.06, W - 1.0, 4.6, 7.2 - 0.3 * (k % 3), z - 0.08, z + 0.08, STEEL)
# за экспонатом под окном — стальные ворота депо: красный поезд читается на сером, а не на красном кирпиче
IR.box(-5.6, 5.6, 1.6, 5.9, ZF + 0.88, ZF + 1.0, STEEL)
for x in (-5.4, -0.1, 5.2):
    IS.box(x, x + 0.2, 1.6, 5.9, ZF + 1.0, ZF + 1.08, STEEL2)
for y in (1.9, 5.4):
    IS.box(-5.4, 5.4, y, y + 0.2, ZF + 1.0, ZF + 1.14, STEEL2)
# дальняя стена: большое арочное окно цеха; на дальнем пути — тендер с углём; паровые трубы под потолком
IG.prism_xy(arch(0.0, 6.0, 12.0, 5.0, n=8), ZF + 0.9, ZF + 0.94, GLASS)
band(IS, arch(0.0, 6.0, 12.0, 5.6, n=8), arch(0.0, 6.0, 12.0, 5.0, n=8), ZF + 0.88, ZF + 1.2, STONE)
for x in (-2.5, 0.0, 2.5):
    IS.box(x - 0.08, x + 0.08, 6.0, 12.0 + 5.0 * math.cos(math.asin(min(1.0, abs(x) / 5.0))), ZF + 0.94, ZF + 1.0, STEEL2)
for y in (8.0, 10.0, 12.0):
    IS.box(-5.0, 5.0, y - 0.08, y + 0.08, ZF + 0.94, ZF + 1.0, STEEL2)
F.objects(True)
TZc = -12.6
IS.box(-1.4, 1.4, 0.9, 3.4, TZc - 2.2, TZc + 2.2, BLACK)
IS.prism_xz(K.octa(0.0, TZc, 1.2, 2.0, 0.5), 3.4, 4.2, COAL)
for z in (TZc - 1.4, TZc + 1.4):
    for e in (-1, 1):
        IS.prism_zy(K.ngon(z, 0.7, 0.55, 10), e * 0.75 - 0.15, e * 0.75 + 0.15, RED)
F.objects(False)
for x in (-12.0, 12.0):
    IS.prism_xy(K.ngon(x, C - 1.6, 0.3, 8), ZF + 0.9, ZB - 0.9, STEEL2)
    IS.prism_xy(K.ngon(x, C - 1.6, 0.4, 8), -2.0, -1.4, BRASS)
# кран-балка с крюком, кучи угля
IS.box(-W, W, C - 2.4, C - 1.8, -10.2, -9.6, "F0C020")
IS.box(-5.0, -3.4, C - 3.0, C - 1.8, -10.6, -9.2, STEEL2)
IS.box(-4.24, -4.16, 9.0, C - 3.0, -9.94, -9.86, BLACK)
IS.box(-4.4, -4.0, 8.2, 9.0, -10.0, -9.8, "F0C020")
F.objects(True)
for x, z, r in ((10.6, 6.0, 1.6), (12.4, 5.2, 1.2)):
    IS.prism_xz(K.octa(x, z, r * 1.4, r, r * 0.5), 0.0, r * 0.9, COAL)
    IS.prism_xz(K.octa(x + 0.2, z, r * 0.8, r * 0.6, r * 0.3), r * 0.9, r * 1.5, COAL)
F.objects(False)
for x, z in ((-6.0, -6.0), (6.0, -6.0), (-6.0, 3.0), (6.0, 3.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.0, C - 0.8, z - 0.03, z + 0.03, BLACK)
    D.lantern(IS, IG, x, C - 4.0, z, s=1.0, cap=BLACK, light=GLASS)
# постамент: поворотный круг с рельсами
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.6, 20), 0.0, 0.4, STONE)
IS.prism_xz(K.ngon(px, pz, 4.2, 20), 0.4, TOP - 0.06, WOOD2)
ring_y(IS, px, pz, 4.2, 4.5, 0.4, TOP, STEEL, n=20)
for e in (-1, 1):
    IS.box(px + e * 0.75 - 0.1, px + e * 0.75 + 0.1, TOP - 0.06, TOP + 0.1, pz - 4.2, pz + 4.2, STEEL)
for k in range(7):
    z = pz - 3.6 + 1.2 * k
    IS.box(px - 1.4, px + 1.4, TOP - 0.06, TOP - 0.01, z - 0.3, z + 0.3, WOOD)
B.lift_leaves(IS, STEEL2, STONE)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, BRICK)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "6A665E")
SL.box(-FX - 0.5, FX + 0.5, 16.6, 17.4, -FZ - 0.5, FZ + 0.5, STONE)
SL.box(-11.0, -1.0, 0.3, 5.5, -FZ - 3.0, -FZ - 0.8, BLACK)
SL.prism_xz(K.ngon(TX, TZ, 2.3, 8), 10.0, 14.2, WOOD)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.92, 0.82)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Forge", (-11, 6, -8), 500, (1.0, 0.6, 0.35))])
