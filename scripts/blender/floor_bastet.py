"""Этаж «Египетская кошка» музея-небоскрёба (одиннадцатая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — храм богини-кошки Бастет на берегу Нила. Снаружи — белёные стены с голубыми и золотыми поясами,
вход между двумя колоннами-папирусами с лотосовыми капителями, над входом — крылатый солнечный диск, по сторонам —
статуи сидящих кошек на постаментах (силуэты без лиц), деревянная пристань с папирусной лодкой, полоса воды,
заросли папируса, лотосы, корзины с рыбой, амфоры. Внутри — внутренний двор храма: бассейн с лотосами, ряды
корзин-лежанок с подушками, курильницы, роспись с кошками и рыбками по стенам, пальмовые балки; экспонат —
на круглом голубом постаменте с золотым кольцом-ошейником.
Запуск: blender --background --factory-startup --python scripts/blender/floor_bastet.py -- <репо> <превью>
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

WHITE, WHITE2, BLUE, BLUE2, GOLD, SAND = "F4EEDC", "DCD2B8", "2A6AC0", "1E4A8A", "E8B840", "E2C890"
BLACK, PAPY, PAPY2, LOTUS, WATER, WOOD = "2A2A30", "5AA84A", "3E8A3A", "F2A0C0", "4AA8D8", "A87A48"
CLAY, CUSH, TEAL, GLASS = "C86A3A", "D84A4A", "2AB0A8", "F8E8C0"

F = B.Floor("BS", "EgyptianCat", quiet=(WHITE2, SAND, "8AA0B8"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def papyrus_col(p, x, z, y0, y1, r):
    """Колонна-папирус: связка стеблей, кольца-обвязки, раскрытая капитель-лотос."""
    p.prism_xz(K.ngon(x, z, r, 10), y0, y1 - 1.6, WHITE)
    for y in (y0 + 0.6, y1 - 2.4):
        p.prism_xz(K.ngon(x, z, r + 0.08, 10), y, y + 0.3, BLUE)
    p.loft([(x + r * math.cos(a), y1 - 1.6, z + r * math.sin(a)) for a in [2 * math.pi * k / 10 for k in range(10)]],
           [(x + r * 1.7 * math.cos(a), y1 - 0.3, z + r * 1.7 * math.sin(a)) for a in [2 * math.pi * k / 10 for k in range(10)]], PAPY)
    p.prism_xz(K.ngon(x, z, r * 1.75, 10), y1 - 0.3, y1, GOLD)


def cat_statue(p, x, z, y, s, col=BLACK):
    """Сидящая кошка-силуэт: постамент, тело-конус, голова, уши, хвост (без глаз)."""
    p.box(x - 0.9 * s, x + 0.9 * s, y, y + 0.6 * s, z - 0.9 * s, z + 0.9 * s, GOLD)
    p.loft([(x - 0.6 * s, y + 0.6 * s, z - 0.7 * s), (x + 0.6 * s, y + 0.6 * s, z - 0.7 * s), (x + 0.6 * s, y + 0.6 * s, z + 0.7 * s),
            (x - 0.6 * s, y + 0.6 * s, z + 0.7 * s)],
           [(x - 0.35 * s, y + 2.6 * s, z - 0.3 * s), (x + 0.35 * s, y + 2.6 * s, z - 0.3 * s), (x + 0.35 * s, y + 2.6 * s, z + 0.3 * s),
            (x - 0.35 * s, y + 2.6 * s, z + 0.3 * s)], col)
    p.box(x - 0.38 * s, x + 0.38 * s, y + 2.6 * s, y + 3.3 * s, z - 0.4 * s, z + 0.3 * s, col)
    for e in (-1, 1):
        p.prism_xy([(x + e * 0.38 * s, y + 3.3 * s), (x + e * 0.05 * s, y + 3.3 * s), (x + e * 0.3 * s, y + 3.85 * s)], z - 0.1 * s, z + 0.1 * s, col)
    p.box(x - 0.3 * s, x + 0.3 * s, y + 2.3 * s, y + 2.45 * s, z - 0.42 * s, z - 0.3 * s, GOLD)
    beam(p, (x + 0.5 * s, y + 0.7 * s, z + 0.5 * s), (x + 1.1 * s, y + 1.4 * s, z - 0.2 * s), 0.18 * s, 0.18 * s, col)


def reeds(p, x, z, y, n, h, seed):
    for k in range(n):
        dx, dz = 0.9 * (rng(k, seed) - 0.5), 0.6 * (rng(k, seed, 2) - 0.5)
        hh = h * (0.7 + 0.5 * rng(k, seed, 3))
        beam(p, (x + dx, y, z + dz), (x + dx * 1.6, y + hh, z + dz * 1.4), 0.08, 0.08, PAPY2)
        p.cone([(x + dx * 1.6 + 0.35 * math.cos(a), y + hh, z + dz * 1.4 + 0.35 * math.sin(a)) for a in [2 * math.pi * j / 5 for j in range(5)]],
               (x + dx * 1.6, y + hh - 0.5, z + dz * 1.4), PAPY)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, WHITE, SAND, BLUE, SAND, "1E3A6A", roof="flat", roof_col=WHITE, top=16.0, band=(12.8, 13.4, BLUE),
         side=S.side_windows(F, BLUE, "2A3A5A", kind="slit", y0=8.0, y1=12.0, w=1.2, xs=(-10.0, -4.0, 2.0, 8.0)))
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # золотой пояс шашкой под карнизом
    for k in range(int(2 * half // 1.0)):
        a = -half + 1.0 * k
        if k % 2 == 0:
            slab(FS, axis, fixed, out, 1.0, a, a + 1.0, 14.0, 14.6, GOLD)
# вход: тёмный проём, колонны-папирусы, крылатый солнечный диск
FS.box(-3.0, 3.0, 1.0, 9.6, -FZ - 0.92, -FZ - 0.88, "2A1E18")
FR.box(-3.6, 3.6, 9.6, 10.6, -FZ - 1.4, -FZ - 0.88, WHITE2)
for x in (-4.8, 4.8):
    papyrus_col(FS, x, -FZ - 1.8, 1.0, 11.6, 0.6)
FR.box(-6.2, 6.2, 11.6, 12.4, -FZ - 2.6, -FZ - 0.88, WHITE)
S.disc(FS, (0.0, 14.4, -FZ - 1.0), (0, 0, -1), 0.9, 0.25, GOLD, seg=14)
for e in (-1, 1):
    for k in range(4):
        FS.prism_xy([(e * 1.0, 14.0 + 0.2 * k), (e * (4.6 - 0.6 * k), 14.2 + 0.25 * k), (e * (4.4 - 0.6 * k), 14.5 + 0.25 * k),
                     (e * 1.0, 14.3 + 0.2 * k)], -FZ - 1.1 - 0.02 * k, -FZ - 0.95, (BLUE, GOLD, TEAL, BLUE2)[k])
# росписи-панели с кошками и рыбками на стене
for x0, kind in ((-15.6, 0), (9.4, 1)):
    FS.box(x0, x0 + 6.2, 4.0, 10.4, -FZ - 0.96, -FZ - 0.88, SAND)
    FS.frame_xy(K.rect(x0 - 0.2, x0 + 6.4, 3.8, 10.6), K.rect(x0, x0 + 6.2, 4.0, 10.4), -FZ - 1.05, -FZ - 0.88, BLUE)
    for k in range(3):
        cx = x0 + 1.1 + 2.0 * k
        if kind == 0:
            FS.prism_xy([(cx - 0.5, 5.0), (cx + 0.5, 5.0), (cx + 0.3, 7.0), (cx + 0.45, 7.8), (cx + 0.15, 7.4), (cx - 0.15, 7.4),
                         (cx - 0.45, 7.8), (cx - 0.3, 7.0)], -FZ - 1.0, -FZ - 0.96, BLACK)
        else:
            FS.prism_xy(K.octa(cx, 6.0 + 1.6 * (k % 2), 0.7, 0.35, 0.2), -FZ - 1.0, -FZ - 0.96, (BLUE, TEAL, GOLD)[k])
            FS.prism_xy([(cx - 0.6, 6.0 + 1.6 * (k % 2)), (cx - 1.0, 6.35 + 1.6 * (k % 2)), (cx - 1.0, 5.65 + 1.6 * (k % 2))],
                        -FZ - 1.0, -FZ - 0.96, (BLUE, TEAL, GOLD)[k])
    FS.box(x0 + 0.3, x0 + 5.9, 8.8, 9.0, -FZ - 1.0, -FZ - 0.96, GOLD)
# статуи сидящих кошек, пристань, лодка, папирус, лотосы, корзины, амфоры
F.objects(True)
for x in (-7.6, 7.6):
    cat_statue(FS, x, -FZ - 2.0, -0.1, 1.2)
F.objects(False)
FG.box(-FX - 2.9, FX + 2.9, -0.12, -0.06, -FZ - 2.9, -FZ - 2.2, WATER)
FR.box(10.6, 17.6, -0.1, 0.4, -FZ - 2.9, -FZ - 1.0, WOOD)
for k in range(6):
    FS.box(10.8 + 1.2 * k, 11.0 + 1.2 * k, -0.6, 0.4, -FZ - 2.95, -FZ - 2.75, "6A4A2A")
F.objects(True)
FS.loft([(-16.6, 0.2, -FZ - 2.7), (-10.6, 0.2, -FZ - 2.7), (-10.6, 0.2, -FZ - 2.3), (-16.6, 0.2, -FZ - 2.3)],
        [(-17.4, 1.0, -FZ - 2.9), (-9.8, 1.0, -FZ - 2.9), (-9.8, 1.0, -FZ - 2.1), (-17.4, 1.0, -FZ - 2.1)], "C8A050")
for e in (-1, 1):
    beam(FS, (-13.6 + e * 3.8, 1.0, -FZ - 2.5), (-13.6 + e * 4.6, 2.0, -FZ - 2.5), 0.5, 0.5, "B08A40")
FS.box(-13.7, -13.5, 1.0, 5.6, -FZ - 2.6, -FZ - 2.4, WOOD)
FS.prism_xy([(-13.5, 5.4), (-13.5, 1.8), (-10.6, 2.0)], -FZ - 2.52, -FZ - 2.48, WHITE)
for (x, n, h, sd) in ((-FX - 1.6, 6, 4.0, 1), (-2.6, 4, 2.6, 2), (3.2, 4, 2.8, 3), (FX + 1.4, 6, 3.6, 4)):
    reeds(FS, x, -FZ - 2.5, -0.1, n, h, sd)
for x in (-1.0, 1.4):
    FS.prism_xz(K.ngon(x, -FZ - 2.6, 0.4, 6), -0.05, 0.05, PAPY)
    FS.prism_xz(K.ngon(x, -FZ - 2.6, 0.2, 5), 0.05, 0.3, LOTUS)
for x in (12.0, 13.4):
    FS.prism_xz(K.ngon(x, -FZ - 1.6, 0.55, 8), 0.4, 1.1, "C8A050")
    FS.prism_xz(K.octa(x, -FZ - 1.6, 0.35, 0.2, 0.1), 1.1, 1.3, "8AB0C8")
for x in (15.2, 16.4):
    FS.prism_xz(K.ngon(x, -FZ - 1.5, 0.3, 8), 0.4, 0.7, CLAY)
    FS.prism_xz(K.ngon(x, -FZ - 1.5, 0.5, 8), 0.7, 1.7, CLAY)
    FS.prism_xz(K.ngon(x, -FZ - 1.5, 0.22, 8), 1.7, 2.2, CLAY)
F.objects(False)

# ══ ИНТЕРЬЕР: двор храма Бастет ═══════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.4
S.interior(F, WHITE, SAND, "6A4A2A", BLUE, wain=(2.0, BLUE2), beams=None)
for k in range(14):  # пальмовые балки потолка
    x = -W + 1.2 + (2 * W - 2.4) * k / 13
    IS.prism_zy([(ZF, C - 0.7), (ZB, C - 0.7), (ZB, C - 0.1), (ZF, C - 0.1)], x - 0.3, x + 0.3, WOOD if k % 2 else "8A5A30")
for idx, (axis, fixed, out, half) in enumerate(B.WALLS[:3]):  # роспись: фриз из кошек и рыбок
    for k in range(int(2 * half // 2.4)):
        a = -half + 1.2 + 2.4 * k
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.94))
        pts = ([(a - 0.5, 9.0), (a + 0.5, 9.0), (a + 0.3, 11.0), (a + 0.45, 11.8), (a + 0.15, 11.4), (a - 0.15, 11.4), (a - 0.45, 11.8),
                (a - 0.3, 11.0)] if k % 2 == 0 else [(a - 0.8, 10.2), (a, 10.7), (a + 0.6, 10.2), (a + 1.0, 10.6), (a + 1.0, 9.8),
                                                     (a + 0.6, 10.2), (a, 9.7)])
        col = BLACK if k % 2 == 0 else (BLUE, TEAL, GOLD)[k % 3]
        if axis == "x":
            IS.prism_zy(pts, d0, d1, col)
        else:
            IS.prism_xy(pts, d0, d1, col)
    slab(IS, axis, fixed, out, 0.94, -half, half, 8.3, 8.6, GOLD)
    slab(IS, axis, fixed, out, 0.94, -half, half, 12.4, 12.7, GOLD)
# бассейн с лотосами у дальней стены
IR.frame_xz(K.rect(-8.0, 8.0, ZF + 1.4, ZF + 7.0), K.rect(-7.4, 7.4, ZF + 2.0, ZF + 6.4), 0.0, 0.7, WHITE2)  # бортик
IG.box(-7.4, 7.4, 0.0, 0.56, ZF + 2.0, ZF + 6.4, WATER)  # вода ниже бортика, белой плиты под ней нет
F.objects(True)
for k in range(7):
    x, z = -6.4 + 2.1 * k, ZF + 3.0 + 2.4 * rng(k, 5)
    IS.prism_xz(K.ngon(x, z, 0.6, 8), 0.56, 0.62, PAPY)
    if k % 2 == 0:
        IS.cone([(x + 0.35 * math.cos(a), 0.62, z + 0.35 * math.sin(a)) for a in [2 * math.pi * j / 6 for j in range(6)]], (x, 1.3, z), LOTUS)
# корзины-лежанки с подушками и статуи кошек вдоль боковых стен
for s in (-1, 1):
    for k in range(3):
        z = -11.0 + 5.0 * k
        x = s * (W - 2.6)
        IS.prism_xz(K.ngon(x, z, 1.4, 10), 0.0, 0.8, "C8A050")
        IS.prism_xz(K.ngon(x, z, 1.15, 10), 0.6, 0.95, (CUSH, TEAL, GOLD)[k])
    cat_statue(IS, s * (W - 2.2), 6.0, 0.0, 1.0, col=BLACK if s < 0 else GOLD)
# курильницы
for x in (-6.0, 6.0):
    IS.prism_xz(K.ngon(x, 4.0, 0.5, 8), 0.0, 2.6, GOLD)
    IS.prism_xz(K.ngon(x, 4.0, 0.8, 8), 2.6, 3.0, GOLD)
    IG.prism_xz(K.ngon(x, 4.0, 0.4, 6), 3.0, 3.4, "FFB050")
F.objects(False)
for x, z in ((-5.0, -8.0), (5.0, -8.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.0, C - 0.7, z - 0.03, z + 0.03, "4A3A2A")
    D.lantern(IS, IG, x, C - 4.0, z, s=1.0, cap=GOLD, light="FFE0A0")
# постамент: голубой барабан с золотым кольцом-ошейником
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 3.8, 16), 0.0, TOP - 0.2, BLUE)
S.annulus(IS, (px, 0.5, pz), (0, 1, 0), 3.75, 3.95, 0.35, GOLD, seg=16)
IS.prism_xz(K.ngon(px, pz, 3.9, 16), TOP - 0.2, TOP, GOLD)
IS.prism_xz(K.octa(px, pz - 3.9, 0.35, 0.3, 0.1), 0.35, 0.95, GOLD)
B.lift_leaves(IS, BLUE2, GOLD)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, WHITE, SAND, WHITE, top=16.0)
SL.box(-6.2, 6.2, 11.6, 12.4, -FZ - 2.6, -FZ, WHITE)

F.build(exhibit=(PED[0], TOP, PED[1], 3.2), lamps=[("Hall", (0, 14, 6), 2000, (1.0, 0.95, 0.85)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.9)),
                                                   ("Pool", (0, 3, -12), 600, (0.6, 0.85, 1.0))])
