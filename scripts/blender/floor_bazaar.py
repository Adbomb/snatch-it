"""Этаж «Большой Сфинкс» музея-небоскрёба (одиннадцатая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — каирский базар у плато Гизы. Снаружи — охристые стены с деревянными решётчатыми эркерами-
машрабия на кронштейнах, стрельчатые арки лавок с полосатыми навесами, гирлянды цветных фонарей, ковры на
перилах, горки специй в мешках (конусы красного, жёлтого, зелёного), медные кувшины и подносы, корзины с
финиками, ослик-тележка (только телега с колёсами и грузом), на крыше — силуэт пирамиды-вывески. Внутри — крытый
рынок: ряды прилавков со специями и фонарями, свисающие ковры, гирлянды фонарей под потолком, медная посуда на
стенах, пуфы и низкие столики; экспонат — на круглом ковровом помосте с медной каймой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_bazaar.py -- <репо> <превью>
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

OCHRE, OCHRE2, CREAM, WOOD, WOOD2, COPPER = "D8A060", "B8844A", "F0E0C0", "8A5A30", "5E3C20", "C8743A"
RED, SAFFRON, GREEN, TEAL, PURPLE, NIGHT = "C83A2E", "F2B830", "4A9A3A", "2A9A9A", "7A3A9A", "2A2A4A"
RUG = (RED, TEAL, PURPLE, SAFFRON)
LAMPS = ("FF7040", "40E0A0", "F0C040", "C060FF", "40A0FF")

F = B.Floor("BZ", "GreatSphinx", quiet=(OCHRE2, "C8A878", "7A5A40"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def mashrabiya(p, x0, x1, y0, y1, z, depth):
    """Эркер-машрабия: короб на кронштейнах, решётка из брусков, козырёк."""
    p.box(x0, x1, y0, y0 + 0.3, z - depth, z, WOOD2)
    p.box(x0, x1, y1, y1 + 0.3, z - depth - 0.2, z, WOOD2)
    for x in (x0, x1):
        p.box(x - 0.12, x + 0.12, y0, y1, z - depth, z - depth + 0.24, WOOD2)
    n = int((x1 - x0) / 0.45)
    for k in range(1, n):
        x = x0 + (x1 - x0) * k / n
        p.box(x - 0.05, x + 0.05, y0 + 0.3, y1, z - depth + 0.02, z - depth + 0.12, WOOD)
    for j in range(1, int((y1 - y0) / 0.45)):
        y = y0 + 0.3 + j * 0.45
        p.box(x0, x1, y - 0.05, y + 0.05, z - depth + 0.02, z - depth + 0.12, WOOD)
    for x in (x0 + 0.3, x1 - 0.3):
        beam(p, (x, y0 - 1.0, z), (x, y0, z - depth + 0.2), 0.2, 0.2, WOOD2)


def spice(p, x, z, y, r, col):
    """Мешок со специей: открытый мешок и конус-горка."""
    p.prism_xz(K.ngon(x, z, r, 8), y, y + r * 1.2, CREAM)
    p.prism_xz(K.ngon(x, z, r * 1.08, 8), y + r * 1.2, y + r * 1.4, "C8B080")
    p.cone([(x + r * math.cos(a), y + r * 1.4, z + r * math.sin(a)) for a in [2 * math.pi * k / 8 for k in range(8)]],
           (x, y + r * 2.4, z), col)


def lantern_c(p, g, x, y, z, s, col):
    """Цветной ажурный фонарь: верх-купол, цветное стекло, низ."""
    p.cone([(x + 0.3 * s * math.cos(a), y + 0.9 * s, z + 0.3 * s * math.sin(a)) for a in [2 * math.pi * k / 6 for k in range(6)]],
           (x, y + 1.3 * s, z), COPPER)
    g.prism_xz(K.ngon(x, z, 0.32 * s, 6), y + 0.2 * s, y + 0.9 * s, col)
    p.cone([(x + 0.3 * s * math.cos(a), y + 0.2 * s, z + 0.3 * s * math.sin(a)) for a in [2 * math.pi * k / 6 for k in range(6)]],
           (x, y - 0.1 * s, z), COPPER)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, OCHRE, OCHRE2, CREAM, "C8A878", "3A2A22", roof="crenel", roof_col=OCHRE, top=16.0, band=(8.8, 9.2, CREAM),
         side=S.side_windows(F, WOOD2, "2A2020", kind="arch", y0=10.4, y1=13.6, w=1.8, xs=(-12.90, -6.90, -0.90, 5.10, 11.10)))
# лавки под стрельчатыми арками с полосатыми навесами
for k, x in enumerate((-12.0, -4.0, 4.0, 12.0)):
    FS.prism_xy([(x - 2.6, 1.0), (x + 2.6, 1.0), (x + 2.6, 5.6), (x, 8.0), (x - 2.6, 5.6)], -FZ - 0.92, -FZ - 0.88, "2A1E18")
    FR.prism_xy([(x - 3.0, 5.6), (x - 2.6, 5.6), (x, 8.0), (x + 2.6, 5.6), (x + 3.0, 5.6), (x, 8.6)], -FZ - 1.3, -FZ - 0.88, CREAM)
    for j in range(5):
        xa = x - 2.8 + 5.6 * j / 5
        FS.loft([(xa, 5.4, -FZ - 0.9), (xa + 1.12, 5.4, -FZ - 0.9), (xa + 1.12, 5.55, -FZ - 0.9), (xa, 5.55, -FZ - 0.9)],
                [(xa, 4.6, -FZ - 2.6), (xa + 1.12, 4.6, -FZ - 2.6), (xa + 1.12, 4.75, -FZ - 2.6), (xa, 4.75, -FZ - 2.6)],
                (RUG[k], CREAM)[j % 2])
# эркеры-машрабия на втором ярусе
for x0, x1 in ((-15.0, -9.0), (-3.0, 3.0), (9.0, 15.0)):
    mashrabiya(FS, x0, x1, 10.4, 14.4, -FZ - 0.88, 1.6)
# гирлянды фонарей и ковры на перилах
F.objects(True)
for k in range(12):
    x = -16.5 + 3.0 * k
    lantern_c(FS, FG, x, 8.6 - 0.5 * math.sin(math.pi * ((k % 4) + 0.5) / 4), -FZ - 2.8, 0.8, LAMPS[k % 5])
F.objects(False)
D.chain(FS, (-FX, 9.8, -FZ - 2.8), (FX, 9.8, -FZ - 2.8), 16, 0.05, "3A3A40", sag=0.6)
for k, x in enumerate((-12.0, 0.0, 12.0)):
    FS.box(x - 1.8, x + 1.8, 13.6, 14.4, -FZ - 2.62, -FZ - 2.48, WOOD2)
    FS.box(x - 1.6, x + 1.6, 11.4, 13.6, -FZ - 2.6, -FZ - 2.52, RUG[k])
    FS.box(x - 1.2, x + 1.2, 11.8, 13.2, -FZ - 2.64, -FZ - 2.6, RUG[(k + 2) % 4])
    for j in range(5):
        FS.box(x - 1.5 + 0.7 * j, x - 1.4 + 0.7 * j, 11.0, 11.4, -FZ - 2.58, -FZ - 2.54, CREAM)
# горки специй, медные кувшины и подносы, корзины с финиками, телега
F.objects(True)
for k, (x, col) in enumerate(((-14.0, RED), (-12.6, SAFFRON), (-11.2, GREEN), (-13.3, "8A4A2A"), (-11.9, SAFFRON))):
    spice(FS, x, -FZ - 2.0 - (0.9 if k > 2 else 0.0), -0.1, 0.55, col)
for k, x in enumerate((-5.6, -4.6, -3.6)):
    FS.prism_xz(K.ngon(x, -FZ - 1.6, 0.3, 8), -0.1, 0.4, COPPER)
    FS.prism_xz(K.ngon(x, -FZ - 1.6, 0.45, 8), 0.4, 1.0, COPPER)
    FS.prism_xz(K.ngon(x, -FZ - 1.6, 0.15, 6), 1.0, 1.6, COPPER)
    beam(FS, (x, 1.5, -FZ - 1.6), (x + 0.5, 0.8, -FZ - 1.6), 0.1, 0.1, COPPER)
S.disc(FS, (-2.4, 2.4, -FZ - 1.0), (0, 0, -1), 1.0, 0.1, COPPER, seg=14)
for x in (2.6, 3.8):
    FS.prism_xz(K.ngon(x, -FZ - 1.6, 0.6, 8), -0.1, 0.8, "C8A050")
    for j in range(4):
        FS.prism_xz(K.octa(x - 0.2 + 0.4 * (j % 2), -FZ - 1.6 + 0.3 * (j // 2) - 0.15, 0.2, 0.12, 0.05), 0.8, 1.0, "6A2A1A")
CX = 12.0
FS.box(CX - 2.0, CX + 2.0, 1.0, 1.5, -FZ - 3.0, -FZ - 1.6, WOOD)
for e in (-1, 1):
    S.disc(FS, (CX, 0.9, -FZ - 2.3 + e * 0.75), (0, 0, e), 0.9, 0.15, WOOD2, seg=10)
beam(FS, (CX - 2.0, 1.2, -FZ - 2.3), (CX - 3.6, 0.8, -FZ - 2.3), 0.15, 0.15, WOOD2)
for k in range(3):
    spice(FS, CX - 1.2 + 1.2 * k, -FZ - 2.3, 1.5, 0.45, (RED, GREEN, SAFFRON)[k])
F.objects(False)
# силуэт пирамиды-вывески на крыше
FS.prism_xy([(-3.0, 18.0), (3.0, 18.0), (0.0, 18.9)], -FZ - 1.3, -FZ - 1.1, SAFFRON)
FS.box(-3.2, 3.2, 17.6, 18.0, -FZ - 1.35, -FZ - 0.88, WOOD2)

# ══ ИНТЕРЬЕР: крытый рынок ════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.0
S.interior(F, CREAM, "B89A72", WOOD2, COPPER, wain=(2.8, OCHRE2), beams=(6, WOOD), beam_dir="x")
F.objects(True)
for s in (-1, 1):  # ряды прилавков со специями
    for k in range(3):
        z = -11.0 + 5.4 * k
        x = s * (W - 3.2)
        IS.box(x - 1.8, x + 1.8, 0.0, 1.6, z - 2.2, z + 2.2, WOOD)
        for j in range(3):
            spice(IS, x - 0.9 + 1.8 * (j % 2), z - 1.4 + 1.4 * j, 1.6, 0.5, (RED, SAFFRON, GREEN, "8A4A2A", PURPLE)[(j + k) % 5])
        IS.box(x - 0.08, x + 0.08, 1.6, 6.0, z + 2.1, z + 2.2, WOOD2)
        IS.box(*sorted((x, s * (W - 0.88))), 5.8, 6.0, z + 2.05, z + 2.25, WOOD2)
# свисающие ковры у дальней стены и медная посуда на стенах
for k, x in enumerate((-12.0, -6.0, 6.0, 12.0)):
    IS.box(x - 2.0, x + 2.0, 4.0, 11.0, ZF + 0.9, ZF + 1.0, RUG[k])
    IS.box(x - 1.5, x + 1.5, 4.6, 10.4, ZF + 1.0, ZF + 1.04, RUG[(k + 2) % 4])
    IS.prism_xy(K.ngon(x, 7.5, 0.9, 4, turn=0.0), ZF + 1.04, ZF + 1.08, CREAM)
# большой тёмный ковёр прямо за экспонатом: светлый песочный сфинкс читается на ночной сини, а не на бежевой стене
IS.box(-3.2, 3.2, 2.0, 11.6, ZF + 0.9, ZF + 1.0, RED)
IS.box(-2.7, 2.7, 2.5, 11.1, ZF + 1.0, ZF + 1.04, NIGHT)
IS.prism_xy(K.ngon(0.0, 6.8, 1.2, 4, turn=0.0), ZF + 1.04, ZF + 1.08, SAFFRON)
for s in (-1, 1):
    for k, (z, y, r) in enumerate(((-10.4, 10.6, 0.95), (-6.6, 9.0, 0.55), (-3.0, 11.0, 1.1), (1.2, 9.6, 0.7))):
        z = z if s < 0 else -4.6 - z  # подносы разного размера и высоты, справа — в обратном порядке
        S.disc(IS, (s * (W - 0.9), y, z), (-s, 0, 0), r, 0.08, COPPER, seg=12)
        S.annulus(IS, (s * (W - 0.98), y, z), (-s, 0, 0), r * 0.62, r * 0.72, 0.06, "8A4A20", seg=12)
        IS.box(*sorted((s * (W - 0.88), s * (W - 1.0))), y + r - 0.05, y + r + 0.35, z - 0.04, z + 0.04, "3A3A40")  # крючок
# пуфы и низкие столики у лифта
for (x, z) in ((-6.0, 6.0), (6.0, 6.0)):
    IS.prism_xz(K.ngon(x, z, 1.2, 10), 0.0, 1.0, COPPER)
    S.disc(IS, (x, 1.0, z), (0, 1, 0), 1.3, 0.1, "E09A50", seg=12)
    for k in range(3):
        a = 2 * math.pi * k / 3 + x
        IS.prism_xz(K.ngon(x + 2.2 * math.cos(a), z + 2.2 * math.sin(a), 0.6, 8), 0.0, 0.8, RUG[k])
F.objects(False)
for k in range(5):  # гирлянды фонарей под потолком
    z = -12.0 + 4.5 * k
    for j in range(6):
        x = -10.0 + 4.0 * j
        IS.box(x - 0.02, x + 0.02, C - 3.2 - 0.6 * ((j + k) % 2), C - 0.8, z - 0.02, z + 0.02, "3A3A40")
        lantern_c(IS, IG, x, C - 4.2 - 0.6 * ((j + k) % 2), z, 0.8, LAMPS[(j + k) % 5])
# постамент: круглый ковровый помост с медной каймой
px, pz = PED
# вытянутый по длине сфинкса (модель 1.9 × 3.2 при масштабе 3.2 — 6.1 × 10.1): цоколь модели не свисает
IR.prism_xz(K.octa(px, pz, 3.8, 5.6, 1.4), 0.0, TOP - 0.15, WOOD2)
IS.prism_xz(K.octa(px, pz, 3.95, 5.75, 1.45), TOP - 0.15, TOP, COPPER)
for k, (r, col) in enumerate(((3.6, RED), (2.6, NIGHT), (1.6, "4A2420"))):  # тёмный ковёр: светлый сфинкс читается
    IS.prism_xz(K.octa(px, pz, r, r + 1.8, r * 0.36), TOP, TOP + 0.03 + 0.01 * k, col)
B.lift_leaves(IS, WOOD2, COPPER)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, OCHRE, "C8A878", OCHRE, top=16.0)
SL.prism_xy([(-3.0, 18.0), (3.0, 18.0), (0.0, 18.8)], -FZ - 1.3, -FZ - 1.1, SAFFRON)

F.build(exhibit=(PED[0], TOP, PED[1], 3.2), lamps=[("Hall", (0, 14, 6), 1700, (1.0, 0.9, 0.78)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.96, 0.88)),
                                                   ("Lamps", (0, 12, -8), 900, (1.0, 0.65, 0.4))])
