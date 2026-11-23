"""Этаж «Жар-страус» музея-небоскрёба (седьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — старинная пожарная часть. Снаружи — красный кирпич с белыми карнизами и перемычками, внизу —
два больших въезда с арочным верхом: правый закрыт секционными воротами с полосой окон, перед левым стоит пожарная
машина боком — кабина с мигалкой, лестница на крыше, катушка рукава, хромированные полосы; над въездами — золотой
мальтийский крест в круге, наверху — ряд арочных окон; на левом углу — кирпичная башня для сушки рукавов с колоколом
под аркой и флюгером; перед въездами — красно-белые шевроны на асфальте, гидрант, тележка с рукавом, конусы. Внутри —
гараж расчёта: бетонный пол с жёлтыми полосами и шевронами, у левой стены — пожарная машина с лестницей, у правой —
шкафчики с жёлтыми куртками, касками и сапогами, латунный шест из отверстия в потолке на резиновом мате, на дальней
стене — свёрнутые рукава на крюках, большой тревожный колокол и ряд огнетушителей, под потолком — красные маячки;
экспонат — на стальной тумбе с красно-белым поясом.
Запуск: blender --background --factory-startup --python scripts/blender/floor_firestation.py -- <репо> <превью>
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

BRICK, BRICK2, STONE, FRED, FRED2 = "B04A34", "8E3A2A", "EDE4D2", "D82A22", "A81E1A"
CHROME, YEL, DARK, CONC, BRASS, TILEW, GLASS = "CDD2DA", "F2C21E", "2A2A30", "8E9094", "D4A83A", "F0F0EA", "BFD8EA"

F = B.Floor("FH", "BlazeOstrich", quiet=(CONC, "6E7074"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def arch_top(a, y0, y1, w, n=8):
    """Контур проёма с полукруглым верхом (y1 — пята арки)."""
    return [(a - w, y0), (a + w, y0)] + [(a + w * math.cos(math.pi * k / n), y1 + w * math.sin(math.pi * k / n)) for k in range(n + 1)]


def truck(p, g, x0, x1, zc, y=0.0, face=-1):
    """Пожарная машина боком вдоль x (кабина у x1): кузов, кабина, колёса, лестница, мигалка, катушка, хром."""
    zw = 1.5
    p.box(x0, x1 - 3.2, y + 0.8, y + 3.6, zc - zw, zc + zw, FRED)
    p.box(x1 - 3.2, x1, y + 0.8, y + 3.0, zc - zw, zc + zw, FRED)
    p.prism_zy([(zc - zw, y + 3.0), (zc + zw, y + 3.0), (zc + zw, y + 4.4), (zc - zw, y + 4.4)], x1 - 3.2, x1 - 0.9, FRED)
    p.prism_xy([(x1 - 0.9, y + 3.0), (x1, y + 3.0), (x1 - 0.9, y + 4.4)], zc - zw, zc + zw, FRED)
    g.box(x1 - 2.9, x1 - 1.1, y + 3.2, y + 4.2, zc + face * zw - 0.02, zc + face * zw + 0.02, GLASS)
    p.box(x0, x1, y + 1.5, y + 1.75, zc + face * (zw + 0.02) - 0.03, zc + face * (zw + 0.02) + 0.03, CHROME)
    for k in range(3):  # ячейки отсеков
        xa = x0 + 0.4 + 2.2 * k
        p.box(xa, xa + 1.9, y + 1.9, y + 3.3, zc + face * zw - 0.04, zc + face * zw + 0.04, FRED2)
        p.box(xa + 0.8, xa + 1.1, y + 2.5, y + 2.6, zc + face * (zw + 0.08) - 0.03, zc + face * (zw + 0.08) + 0.03, CHROME)
    for wx in (x0 + 1.4, x1 - 4.6, x1 - 1.6):
        for zz in (zc - zw + 0.1, zc + zw - 0.1):
            lo, hi = sorted((zz, zz + (0.45 if zz > zc else -0.45)))
            ring = [(wx + 0.85 * math.cos(2 * math.pi * k / 10), y + 0.85 + 0.85 * math.sin(2 * math.pi * k / 10)) for k in range(10)]
            p.prism_xy(ring, lo, hi, DARK)
            p.prism_xy([(wx + 0.35 * math.cos(2 * math.pi * k / 6), y + 0.85 + 0.35 * math.sin(2 * math.pi * k / 6)) for k in range(6)],
                       *sorted((zz + (0.45 if zz > zc else -0.45), zz + (0.5 if zz > zc else -0.5))), CHROME)
    for e in (-1, 1):  # лестница на крыше
        p.box(x0 + 0.2, x1 - 2.6, y + 3.8, y + 4.0, zc + e * 0.7 - 0.08, zc + e * 0.7 + 0.08, CHROME)
    for k in range(10):
        xa = x0 + 0.5 + (x1 - x0 - 3.4) * k / 9
        p.box(xa - 0.05, xa + 0.05, y + 3.8, y + 3.95, zc - 0.7, zc + 0.7, CHROME)
    p.box(x0 + 0.2, x1 - 3.4, y + 3.6, y + 3.8, zc - 0.3, zc + 0.3, DARK)
    g.box(x1 - 2.6, x1 - 1.9, y + 4.4, y + 4.75, zc - 0.8, zc - 0.1, "FF3030")
    g.box(x1 - 2.6, x1 - 1.9, y + 4.4, y + 4.75, zc + 0.1, zc + 0.8, "3A6AFF")
    p.prism_xy([(x0 + 3.2 + 0.7 * math.cos(2 * math.pi * k / 10), y + 2.7 + 0.7 * math.sin(2 * math.pi * k / 10)) for k in range(10)],
               *sorted((zc + face * zw, zc + face * (zw + 0.5))), "E8D8A8")  # катушка рукава


def chevrons(p, x0, x1, z0, z1, y, step=1.2):
    """Красно-белые шевроны полосами вдоль x (параллелограммы)."""
    n = int((x1 - x0) / step)
    for k in range(n):
        xa = x0 + step * k
        p.prism_xz([(xa, z0), (xa + step * 0.5, z0), (xa + step * 0.5 + (z1 - z0) * 0.5, z1), (xa + (z1 - z0) * 0.5, z1)],
                   y, y + 0.03, FRED if k % 2 == 0 else TILEW)


def helmet(p, x, y, z, col):
    """Каска: купол-восьмигранник с полями и гребнем."""
    p.prism_xz(K.octa(x, z, 0.5, 0.55, 0.18), y, y + 0.1, col)
    p.prism_xz(K.octa(x, z, 0.36, 0.38, 0.14), y + 0.1, y + 0.45, col)
    p.box(x - 0.05, x + 0.05, y + 0.1, y + 0.55, z - 0.36, z + 0.36, BRASS)


# ══ ФАСАД: пожарная часть ═════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, BRICK, BRICK, DARK)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "6E7074")
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.0, STONE)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.0, 16.6, BRICK)
    slab(FR, axis, fixed, out, 1.28, -half - 0.2, half + 0.2, 9.4, 10.2, STONE)
    slab(FR, axis, fixed, out, 1.88, -half - 0.5, half + 0.5, 16.6, 17.4, STONE)
    slab(FR, axis, fixed, out, 0.88, -half, half, 17.4, 18.6, BRICK2)
    slab(FR, axis, fixed, out, 1.28, -half - 0.2, half + 0.2, 18.6, 18.9, STONE)
    for a in (-half, half - 1.4):  # угловые пилястры
        slab(FR, axis, fixed, out, 1.18, a, a + 1.4, 1.0, 16.6, BRICK2)
    nwin = 4 if fi == 0 else 5
    for k in range(nwin):  # арочные окна второго яруса
        a = -half + 4.0 + (2 * half - 8.0) * k / (nwin - 1)
        if fi == 0 and a > 9.0:
            continue
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
        f0, f1 = sorted((fixed + out * 0.88, fixed + out * 1.15))
        pr, fr = (FG.prism_zy, FS.frame_zy) if axis == "x" else (FG.prism_xy, FS.frame_xy)
        pr(arch_top(a, 11.0, 14.2, 1.2), d0, d1, GLASS)
        fr(arch_top(a, 11.0, 14.2, 1.5), arch_top(a, 11.0, 14.2, 1.2), f0, f1, STONE)
        slab(FS, axis, fixed, out, 1.3, a - 1.6, a + 1.6, 10.6, 11.0, STONE)
        if fi > 0:
            pr(arch_top(a, 3.0, 6.6, 1.2), d0, d1, GLASS)
            fr(arch_top(a, 3.0, 6.6, 1.5), arch_top(a, 3.0, 6.6, 1.2), f0, f1, STONE)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# два въезда: левый (по фасаду +x) открыт — машина перед ним, правый закрыт секционными воротами
for bx, open_ in ((6.2, True), (-6.2, False)):
    FS.frame_xy(arch_top(bx, 1.0, 6.8, 4.6), arch_top(bx, 1.0, 6.8, 4.0), -FZ - 1.4, -FZ - 0.88, STONE)
    if open_:
        FS.prism_xy(arch_top(bx, 1.0, 6.8, 4.0), -FZ - 0.96, -FZ - 0.9, "3A3436")
        FG.box(bx - 3.6, bx + 3.6, 7.6, 8.4, -FZ - 1.0, -FZ - 0.96, "FFE0A0")
    else:
        FS.prism_xy(arch_top(bx, 1.0, 6.8, 4.0), -FZ - 0.96, -FZ - 0.9, FRED)
        for k in range(6):
            y = 1.0 + 1.0 * k
            FS.box(bx - 4.0, bx + 4.0, y + 0.9, y + 1.0, -FZ - 1.02, -FZ - 0.96, FRED2)
        for k in range(5):
            FG.box(bx - 3.4 + 1.4 * k, bx - 2.4 + 1.4 * k, 4.2, 4.8, -FZ - 1.02, -FZ - 0.98, GLASS)
FS.frame_xy(K.ngon(0.0, 8.0, 1.6, 16), K.ngon(0.0, 8.0, 1.3, 16), -FZ - 1.3, -FZ - 0.88, STONE)  # мальтийский крест
FS.prism_xy(K.ngon(0.0, 8.0, 1.3, 16), -FZ - 1.0, -FZ - 0.88, FRED)
for k in range(4):
    t = math.pi / 2 * k
    c, s_ = math.cos(t), math.sin(t)
    pts = [(0.15, 0.0), (1.1, -0.6), (0.95, 0.0), (1.1, 0.6)]
    FS.prism_xy([(x * c - y * s_, 8.0 + x * s_ + y * c) for x, y in pts], -FZ - 1.12, -FZ - 1.0, BRASS)
FS.prism_xy(K.ngon(0.0, 8.0, 0.3, 8), -FZ - 1.14, -FZ - 1.0, BRASS)
# башня для сушки рукавов с колоколом на левом углу
TX, TZ = 13.6, -FZ - 1.4
FR.box(TX - 2.6, TX + 2.6, -0.1, 16.6, TZ - 1.6, -FZ - 0.5, BRICK2)
FR.box(TX - 2.9, TX + 2.9, 16.6, 17.2, TZ - 1.9, -FZ - 0.5, STONE)
FS.prism_xy(arch_top(TX, 12.0, 14.6, 1.4), TZ - 1.66, TZ - 1.6, "2A1E1E")
FS.frame_xy(arch_top(TX, 12.0, 14.6, 1.7), arch_top(TX, 12.0, 14.6, 1.4), TZ - 1.9, TZ - 1.6, STONE)
F.objects(True)
FS.cone([(x, 14.4, z) for x, z in K.ngon(TX, TZ - 1.9, 0.9, 10)], (TX, 15.6, TZ - 1.9), BRASS)  # колокол
FS.prism_xz(K.ngon(TX, TZ - 1.9, 1.0, 10), 13.2, 14.4, BRASS)
FS.prism_xz(K.ngon(TX, TZ - 1.9, 0.25, 8), 12.8, 13.2, "8A6A2A")
FS.box(TX - 0.06, TX + 0.06, 15.6, 16.6, TZ - 1.96, TZ - 1.84, DARK)
F.objects(False)
FS.prism_xy(K.rect(TX - 1.0, TX + 1.0, 4.0, 9.0), TZ - 1.66, TZ - 1.6, GLASS)
FS.frame_xy(K.rect(TX - 1.3, TX + 1.3, 3.7, 9.3), K.rect(TX - 1.0, TX + 1.0, 4.0, 9.0), TZ - 1.9, TZ - 1.6, STONE)
FS.box(TX - 0.08, TX + 0.08, 17.2, 18.9, TZ - 0.88, TZ - 0.72, DARK)  # флюгер
FS.prism_xy([(TX, 18.3), (TX + 1.4, 18.0), (TX, 17.7)], TZ - 0.84, TZ - 0.76, BRASS)
# пожарная машина перед открытым въездом, шевроны, гидрант, тележка с рукавом, конусы
chevrons(FS, -11.6, 2.2, -FZ - 2.8, -FZ - 1.0, -0.1)
F.objects(True)
truck(FS, FG, -0.4, 11.0, -FZ - 1.6 - 0.15, y=-0.1, face=-1)
HX, HZ = -13.6, -FZ - 2.0
FS.prism_xz(K.ngon(HX, HZ, 0.42, 8), -0.1, 1.6, FRED)
FS.prism_xz(K.ngon(HX, HZ, 0.5, 8), 1.6, 1.8, YEL)
FS.cone([(x, 1.8, z) for x, z in K.ngon(HX, HZ, 0.42, 8)], (HX, 2.3, HZ), FRED)
for e in (-1, 1):
    FS.box(HX + e * 0.42, HX + e * 0.7, 0.9, 1.2, HZ - 0.15, HZ + 0.15, YEL)
CX = -16.6
for e in (-1, 1):
    FS.prism_zy([(-FZ - 2.0 + 0.6 * math.cos(2 * math.pi * k / 10), 0.5 + 0.6 * math.sin(2 * math.pi * k / 10)) for k in range(10)],
                CX + e * 0.7 - 0.08, CX + e * 0.7 + 0.08, DARK)
FS.prism_zy([(-FZ - 2.0 + 0.5 * math.cos(2 * math.pi * k / 10), 1.6 + 0.5 * math.sin(2 * math.pi * k / 10)) for k in range(10)],
            CX - 0.6, CX + 0.6, "E8D8A8")
for x in (-9.0, -7.6):
    FS.prism_xz(K.ngon(x, -FZ - 2.5, 0.35, 6), -0.1, 0.0, DARK)
    FS.cone([(xx, 0.0, zz) for xx, zz in K.ngon(x, -FZ - 2.5, 0.3, 6)], (x, 0.9, -FZ - 2.5), "F07A20")
F.objects(False)

# ══ ИНТЕРЬЕР: гараж расчёта ═══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.1
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), CONC)
for x in (-7.6, 7.6):
    IS.box(x - 0.15, x + 0.15, 0.02, 0.05, ZF + 1.2, ZB - 1.2, YEL)
chevrons(IS, -6.0, 6.0, 4.4, 6.0, 0.02, step=1.0)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, BRICK)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 3.0, TILEW)
        slab(IS, axis, fixed, out, 1.05, a0, a1, 3.0, 3.25, FRED)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, BRICK)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, STONE)
    slab(IR, axis, fixed, out, 1.4, -half, half, 15.8, 16.6, STONE)
for k in range(-3, 4):
    IS.box(-W, W, C - 0.8, C - 0.2, 4.4 * k - 0.25, 4.4 * k + 0.25, DARK)
for x, z in ((-8.0, -8.0), (8.0, -8.0), (-8.0, 3.0), (8.0, 3.0)):  # красные маячки
    IS.box(x - 0.4, x + 0.4, C - 1.0, C - 0.8, z - 0.4, z + 0.4, DARK)
    IG.prism_xz(K.ngon(x, z, 0.3, 8), C - 1.6, C - 1.0, "FF3A2A")
# пожарная машина у левой стены (вдоль z, кабиной к лифту)
F.objects(True)
zx0, zx1, xc = -13.4, -1.0, -12.0
zw = 1.5
IS.box(xc - zw, xc + zw, 0.8, 3.6, zx0, zx1 - 3.2, FRED)
IS.box(xc - zw, xc + zw, 0.8, 3.0, zx1 - 3.2, zx1, FRED)
IS.box(xc - zw, xc + zw, 3.0, 4.4, zx1 - 3.2, zx1 - 0.9, FRED)
IS.prism_zy([(zx1 - 0.9, 3.0), (zx1, 3.0), (zx1 - 0.9, 4.4)], xc - zw, xc + zw, FRED)
IG.box(xc + zw - 0.02, xc + zw + 0.02, 3.2, 4.2, zx1 - 2.9, zx1 - 1.1, GLASS)
IS.box(xc + zw - 0.01, xc + zw + 0.05, 1.5, 1.75, zx0, zx1, CHROME)
for k in range(3):
    za = zx0 + 0.4 + 2.6 * k
    IS.box(xc + zw - 0.04, xc + zw + 0.04, 1.9, 3.3, za, za + 2.3, FRED2)
for wz in (zx0 + 1.5, zx1 - 4.6, zx1 - 1.6):
    ring = [(wz + 0.85 * math.cos(2 * math.pi * k / 10), 0.85 + 0.85 * math.sin(2 * math.pi * k / 10)) for k in range(10)]
    IS.prism_zy(ring, xc + zw - 0.1, xc + zw + 0.35, DARK)
    IS.prism_zy([(wz + 0.35 * math.cos(2 * math.pi * k / 6), 0.85 + 0.35 * math.sin(2 * math.pi * k / 6)) for k in range(6)],
                xc + zw + 0.35, xc + zw + 0.4, CHROME)
for e in (-1, 1):
    IS.box(xc + e * 0.7 - 0.08, xc + e * 0.7 + 0.08, 3.8, 4.0, zx0 + 0.2, zx1 - 2.6, CHROME)
for k in range(10):
    za = zx0 + 0.5 + (zx1 - zx0 - 3.4) * k / 9
    IS.box(xc - 0.7, xc + 0.7, 3.8, 3.95, za - 0.05, za + 0.05, CHROME)
IS.box(xc - 0.3, xc + 0.3, 3.6, 3.8, zx0 + 0.2, zx1 - 3.4, DARK)
IG.box(xc - 0.8, xc - 0.1, 4.4, 4.75, zx1 - 2.6, zx1 - 1.9, "FF3030")
IG.box(xc + 0.1, xc + 0.8, 4.4, 4.75, zx1 - 2.6, zx1 - 1.9, "3A6AFF")
F.objects(False)
# окна наверху боковых стен, красные трубы спринклеров, лестницы над машиной, щит с топорами
for s_ in (-1, 1):
    for z in (-10.0, -2.0, 6.0):
        d0, d1 = sorted((s_ * (W - 0.88), s_ * (W - 0.92)))
        IG.prism_zy(arch_top(z, 9.4, 12.6, 1.3), d0, d1, GLASS)
        IS.frame_zy(arch_top(z, 9.4, 12.6, 1.6), arch_top(z, 9.4, 12.6, 1.3), *sorted((s_ * (W - 0.88), s_ * (W - 1.15))), STONE)
for x in (-6.0, 6.0):
    IS.box(x - 0.15, x + 0.15, C - 1.65, C - 1.35, ZF + 0.9, ZB - 0.9, FRED)
    for z in (-12.0, -6.0, 0.0, 6.0, 12.0):
        IS.box(x - 0.08, x + 0.08, C - 2.0, C - 1.65, z - 0.08, z + 0.08, FRED)
        IS.prism_xz(K.ngon(x, z, 0.22, 6), C - 2.15, C - 2.0, CHROME)
F.objects(True)
for k, y in enumerate((7.0, 8.4)):  # деревянные лестницы на крюках над машиной
    IS.box(-W + 0.9, -W + 1.3, y, y + 0.2, -14.0, -2.0, "B08048")
    IS.box(-W + 0.9, -W + 1.3, y + 0.9, y + 1.1, -14.0, -2.0, "B08048")
    for j in range(12):
        z = -13.6 + 1.0 * j
        IS.box(-W + 0.95, -W + 1.25, y + 0.2, y + 0.9, z - 0.06, z + 0.06, "8A6234")
AX0 = 10.0
IS.box(AX0, AX0 + 5.0, 5.0, 8.4, ZF + 0.88, ZF + 1.0, "3A3436")
for k in range(3):
    x = AX0 + 0.9 + 1.6 * k
    IS.box(x - 0.08, x + 0.08, 5.4, 8.0, ZF + 1.0, ZF + 1.15, "B08048")
    IS.prism_xy([(x, 7.2), (x + 0.7, 7.6), (x + 0.7, 8.1), (x, 8.0)], ZF + 1.0, ZF + 1.2, FRED)
F.objects(False)
# шкафчики с куртками, касками и сапогами у правой стены
F.objects(True)
x = W - 0.88
for k in range(6):
    z = -13.4 + 2.4 * k
    IS.box(x - 1.4, x, 0.0, 6.6, z - 1.1, z - 0.95, CHROME)
    IS.box(x - 1.4, x, 6.4, 6.6, z - 1.1, z + 1.1, CHROME)
    IS.box(x - 1.2, x - 0.6, 2.2, 5.6, z - 0.7, z + 0.7, YEL)  # куртка
    IS.box(x - 1.24, x - 1.2, 3.0, 3.3, z - 0.7, z + 0.7, "D8E0E8")
    IS.box(x - 1.24, x - 1.2, 4.4, 4.7, z - 0.7, z + 0.7, "D8E0E8")
    helmet(IS, x - 0.8, 6.6, z, FRED if k % 2 else YEL)
    for e in (-1, 1):
        IS.box(x - 1.1, x - 0.5, 0.0, 1.4, z + e * 0.35 - 0.25, z + e * 0.35 + 0.25, DARK)
IS.box(x - 1.4, x, 0.0, 6.6, -13.4 + 2.4 * 6 - 1.1, -13.4 + 2.4 * 6 - 0.95, CHROME)
F.objects(False)
# латунный шест из потолка на мате
PX, PZ = 9.0, -10.0
IS.frame_xz(K.ngon(PX, PZ, 1.5, 12), K.ngon(PX, PZ, 1.1, 12), C - 0.9, C - 0.1, BRASS)
IG.prism_xz(K.ngon(PX, PZ, 1.1, 12), C - 0.06, C - 0.02, "3A3436")
IS.prism_xz(K.ngon(PX, PZ, 0.14, 8), 0.3, C - 0.1, BRASS)
IS.prism_xz(K.ngon(PX, PZ, 1.6, 12), 0.0, 0.3, DARK)
# дальняя стена: рукава на крюках, тревожный колокол, огнетушители
F.objects(True)
for k, x in enumerate((-8.0, -5.0, 5.0, 8.0)):
    IS.box(x - 0.1, x + 0.1, 8.6, 9.0, ZF + 0.88, ZF + 1.6, DARK)
    IS.frame_xy(K.ngon(x, 7.6, 1.2, 12), K.ngon(x, 7.6, 0.6, 12), ZF + 1.0, ZF + 1.6, "E8D8A8" if k % 2 else "C84030")
IS.cone([(xx, 12.0, zz) for xx, zz in K.ngon(0.0, ZF + 1.8, 1.4, 12)], (0.0, 14.0, ZF + 1.8), BRASS)
IS.prism_xz(K.ngon(0.0, ZF + 1.8, 1.55, 12), 11.0, 12.0, BRASS)
IS.box(-0.15, 0.15, 14.0, 15.0, ZF + 0.88, ZF + 1.9, DARK)
for k in range(6):
    x = -12.6 + 0.9 * k if k < 3 else 10.8 + 0.9 * (k - 3)
    IS.prism_xz(K.ngon(x, ZF + 1.4, 0.35, 8), 0.0, 1.8, FRED)
    IS.box(x - 0.1, x + 0.1, 1.8, 2.2, ZF + 1.3, ZF + 1.5, DARK)
F.objects(False)
IS.box(-4.0, 4.0, 3.6, 8.6, ZF + 0.88, ZF + 1.0, "3A5A3A")  # доска с картой района
for k in range(5):
    IS.box(-3.6 + 1.6 * k, -3.0 + 1.6 * k, 4.0 + 0.8 * (k % 3), 4.6 + 0.8 * (k % 3), ZF + 1.0, ZF + 1.06, (FRED, YEL, TILEW)[k % 3])
# стальная тумба с красно-белым поясом
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, 0.3, DARK)
for k in range(16):
    t0, t1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
    IS.prism_xz([(px + 3.7 * math.cos(t0), pz + 3.7 * math.sin(t0)), (px + 3.7 * math.cos(t1), pz + 3.7 * math.sin(t1)),
                 (px, pz)], 0.3, 0.75, FRED if k % 2 else TILEW)
IS.prism_xz(K.ngon(px, pz, 3.8, 16), 0.75, TOP - 0.1, CHROME)
IS.prism_xz(K.ngon(px, pz, 3.9, 16), TOP - 0.1, TOP, "A8AEB8")
B.lift_leaves(IS, CHROME, FRED)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, BRICK)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "6E7074")
SL.box(-FX - 0.5, FX + 0.5, 16.6, 17.4, -FZ - 0.5, FZ + 0.5, STONE)
SL.box(TX - 2.6, TX + 2.6, -0.1, 17.2, TZ - 1.6, -FZ, BRICK2)
SL.box(-0.4, 11.0, -0.1, 4.4, -FZ - 3.2, -FZ - 0.2, FRED)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.95, 0.9)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Beacon", (-8, 10, -8), 500, (1.0, 0.4, 0.3))])
