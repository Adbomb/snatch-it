"""Этаж «Череп трицератопса» музея-небоскрёба (одиннадцатая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — раскоп в красных бэдлендах. Снаружи весь фасад — полосатая столовая гора (слои красного,
охристого и кремового песчаника уступами), в скале — раскоп с сеткой из верёвок и торчащими костями (рёбра,
позвонки, рог), деревянный кран-укосина поднимает гипсовый «кокон» с костью, лестница-стремянка, палатка
экспедиции с флажком, ящики с инструментами, тачка, сито на козлах, кактус и перекати-поле. Внутри — полевая
лаборатория: длинные столы с гипсовыми коконами и кисточками, стеллажи с подписанными костями, карта слоёв на
стене, лампы-переноски, стенд с позвонками; экспонат — на «пласте» из трёх слоёв песчаника.
Запуск: blender --background --factory-startup --python scripts/blender/floor_badlands.py -- <репо> <превью>
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

RED, RED2, OCHRE, CREAM, BROWN, BONE = "C2562E", "A2442A", "D8964A", "EAD6B0", "7A4A2A", "EFE4C8"
PLASTER, WOOD, WOOD2, CANVAS, GREEN, ROPE = "F4F0E6", "B08A5A", "7A5A3A", "D8C8A0", "4A8A3A", "D8C090"
STEEL, FLAG = "8A929C", "E04A3A"
LAYERS = (RED, OCHRE, CREAM, RED2, OCHRE)

F = B.Floor("DG", "TriceratopsSkull", quiet=(RED2, "C89A6A", "8A5A3A"), bevel_min=1.2)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def bone(p, a, b, w, col=BONE):
    """Кость: стержень и утолщения-эпифизы на концах."""
    beam(p, a, b, w, w, col)
    for c in (a, b):
        p.prism_xz(K.ngon(c[0], c[2], w * 1.1, 6), c[1] - w * 0.6, c[1] + w * 0.6, col)


def jacket(p, x, z, y, L):
    """Гипсовый «кокон» с полевой костью."""
    p.prism_zy(K.octa(z, y + 0.6, 0.8, 0.6, 0.3), x - L / 2, x + L / 2, PLASTER)
    for e in (-0.3, 0.3):
        p.prism_zy(K.octa(z, y + 0.6, 0.85, 0.65, 0.3), x + e * L - 0.08, x + e * L + 0.08, ROPE)


# ══ ФАСАД: столовая гора с раскопом ═══════════════════════════════════════════════════════════════════════════
S.facade(F, RED, BROWN, RED2, "C89A6A", "3A2A22", roof="none", top=16.6,
         side=S.side_windows(F, WOOD2, "2A2A30", kind="slit", y0=8.0, y1=11.0, w=1.2, xs=(-9.0, 1.0)))
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # слои песчаника уступами
    for j in range(5):
        y0 = 1.0 + 3.1 * j
        n = 5
        for k in range(n):
            a0 = -half + 2 * half * k / n
            dy = 0.4 * math.sin(k * 1.3 + j * 0.7 + fi)
            slab(FR, axis, fixed, out, 1.0 + 0.2 * ((k + j) % 2), a0, a0 + 2 * half / n + 0.02, y0 + dy, y0 + 3.1 + dy, LAYERS[j])
    for k in range(8):  # рваный верх горы
        a0 = -half + 2 * half * k / 8
        slab(FR, axis, fixed, out, 1.25 - 0.25 * (k % 2), a0, a0 + 2 * half / 8 + 0.02, 16.6, 17.2 + 1.6 * rng(k, fi, 7), CREAM if k % 2 else OCHRE)
# раскоп: тёмная ниша, сетка из верёвок, кости рёбрами и позвонками, рог
FR.box(-9.0, 5.0, 4.0, 11.0, -FZ - 0.92, -FZ - 0.88, BROWN)
for k in range(8):
    FS.box(-9.0 + 2.0 * k - 0.04, -9.0 + 2.0 * k + 0.04, 4.0, 11.0, -FZ - 1.3, -FZ - 1.22, ROPE)
for y in (6.3, 8.6):
    FS.box(-9.0, 5.0, y - 0.04, y + 0.04, -FZ - 1.3, -FZ - 1.22, ROPE)
F.objects(True)
for k in range(6):  # рёбра
    x = -7.4 + 1.6 * k
    pts = [(x + 0.9 * math.sin(1.5 * t), 9.8 - 4.4 * t) for t in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)]  # плавная дуга ребра
    for j, (a, b) in enumerate(zip(pts, pts[1:])):
        th = 0.34 - 0.03 * j
        beam(FS, (a[0], a[1], -FZ - 1.0), (b[0], b[1], -FZ - 1.0), th, 0.25, BONE, up=(0, 0, 1))
FS.box(-8.2, 2.6, 9.6, 10.4, -FZ - 1.1, -FZ - 0.95, BONE)
for k in range(7):  # позвонки вдоль хребта
    x = -8.0 + 1.6 * k
    FS.box(x - 0.4, x + 0.4, 10.4, 11.0, -FZ - 1.15, -FZ - 0.95, BONE)
taper(FS, (3.6, 6.0, -FZ - 1.1), (5.6, 8.6, -FZ - 1.8), 0.7, 0.12, BONE)
F.objects(False)
# деревянный кран-укосина с блоком и гипсовым коконом
CX = 11.6
F.objects(True)
for e in (-1, 1):
    beam(FS, (CX + e * 1.2, -0.1, -FZ - 2.4), (CX, 12.0, -FZ - 2.0), 0.35, 0.35, WOOD)
beam(FS, (CX, 12.0, -FZ - 2.0), (CX - 6.4, 13.6, -FZ - 2.0), 0.4, 0.4, WOOD2)
FS.prism_xy(K.ngon(CX - 6.2, 13.2, 0.35, 8), -FZ - 2.15, -FZ - 1.85, STEEL)
FS.box(CX - 6.24, CX - 6.16, 9.6, 13.2, -FZ - 2.04, -FZ - 1.96, ROPE)
jacket(FS, CX - 6.2, -FZ - 2.0, 8.0, 2.4)
beam(FS, (CX, 12.0, -FZ - 2.0), (CX + 1.4, 2.0, -FZ - 2.2), 0.06, 0.06, ROPE)
S.annulus(FS, (CX + 0.6, 2.6, -FZ - 2.4), (0, 0, -1), 0.3, 0.6, 0.3, STEEL, seg=8)
# стремянка, палатка с флажком, ящики, тачка, сито, кактус
for e in (-0.5, 0.5):
    beam(FS, (-12.0 + e, -0.1, -FZ - 2.6), (-12.0 + e * 0.6, 6.0, -FZ - 1.2), 0.14, 0.14, WOOD2)
for k in range(7):
    t = (k + 0.5) / 7
    FS.box(-12.5, -11.5, 6.0 * t - 0.06, 6.0 * t + 0.06, -FZ - 2.6 + 1.4 * t - 0.06, -FZ - 2.6 + 1.4 * t + 0.06, WOOD)
TX = -16.0
FS.prism_xy([(TX - 1.8, -0.1), (TX + 1.8, -0.1), (TX, 3.2)], -FZ - 3.2, -FZ - 0.9, CANVAS)  # палатка торцом к улице
FS.prism_xy([(TX - 0.75, -0.05), (TX + 0.75, -0.05), (TX, 2.0)], -FZ - 3.24, -FZ - 3.2, "6A5A40")  # вход
for e in (-1, 1):  # растяжки
    beam(FS, (TX + e * 0.9, 1.6, -FZ - 3.2), (TX + e * 2.2, -0.1, -FZ - 3.8), 0.04, 0.04, ROPE)
FS.box(TX - 0.05, TX + 0.05, 3.0, 5.6, -FZ - 2.1, -FZ - 2.0, WOOD2)  # флажок на коньке
FS.prism_xy([(TX + 0.05, 5.6), (TX + 1.2, 5.2), (TX + 0.05, 4.8)], -FZ - 2.07, -FZ - 2.03, FLAG)
for k, x in enumerate((7.0, 8.4)):
    D.crate(FS, x, -FZ - 2.2, y=-0.1, s=1.2, wood=WOOD, board=WOOD2)
FS.box(-5.6, -3.4, 0.6, 1.4, -FZ - 3.0, -FZ - 2.2, STEEL)
FS.prism_xz(K.octa(-4.5, -FZ - 2.6, 0.9, 0.3, 0.15), 1.4, 1.7, RED)
S.disc(FS, (-5.9, 0.5, -FZ - 2.6), (1, 0, 0), 0.5, 0.2, "2A2A2A", seg=8)
for x in (-1.6, 0.6):
    beam(FS, (x, -0.1, -FZ - 2.8), (x - 0.4, 1.6, -FZ - 2.4), 0.12, 0.12, WOOD2)
FS.box(-1.8, 0.8, 1.5, 1.7, -FZ - 2.9, -FZ - 2.1, WOOD)
FS.box(-1.6, 0.6, 1.4, 1.5, -FZ - 2.8, -FZ - 2.2, STEEL)
FS.prism_xz(K.ngon(FX + 1.4, -FZ - 1.8, 0.35, 8), -0.1, 3.6, GREEN)
FS.box(FX + 1.4, FX + 2.3, 1.6, 2.1, -FZ - 2.05, -FZ - 1.55, GREEN)
FS.prism_xz(K.ngon(FX + 2.15, -FZ - 1.8, 0.25, 6), 2.1, 3.0, GREEN)
F.objects(False)

# ══ ИНТЕРЬЕР: полевая лаборатория ═════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.5
S.interior(F, CREAM, "B89A72", WOOD2, BROWN, wain=(2.6, OCHRE), beams=(5, WOOD2), beam_dir="z")
F.objects(True)
for s in (-1, 1):  # длинные столы с коконами и кисточками
    x = s * (W - 3.6)
    IS.box(x - 1.6, x + 1.6, 2.8, 3.1, -12.0, 2.0, WOOD)
    for e in (-1.4, 1.4):
        for z in (-11.6, -5.0, 1.6):
            IS.box(x + e - 0.12, x + e + 0.12, 0.0, 2.8, z - 0.12, z + 0.12, WOOD2)
    for k in range(3):
        jacket(IS, x, -10.0 + 4.6 * k, 3.1, 2.2)
        IS.box(x - 0.9, x - 0.8, 3.1, 3.2, -8.0 + 4.6 * k, -7.2 + 4.6 * k, WOOD2)
        IS.box(x - 0.92, x - 0.78, 3.1, 3.18, -7.2 + 4.6 * k, -6.9 + 4.6 * k, "2A2A2A")
# стеллажи с подписанными костями у дальней стены
for x0 in (-14.0, 6.0):
    for y in (1.0, 3.6, 6.2, 8.8):
        IS.box(x0, x0 + 8.0, y - 0.2, y, ZF + 0.88, ZF + 2.6, WOOD2)
        for k in range(3):
            xx = x0 + 1.2 + 2.6 * k
            if (k + int(y)) % 2:
                bone(IS, (xx - 0.8, y + 0.3, ZF + 1.8), (xx + 0.8, y + 0.3, ZF + 1.8), 0.22)
            else:
                IS.box(xx - 0.4, xx + 0.4, y, y + 0.7, ZF + 1.4, ZF + 2.2, BONE)
            IS.box(xx - 0.3, xx + 0.3, y - 0.18, y - 0.02, ZF + 2.6, ZF + 2.64, PLASTER)
    for x in (x0, x0 + 8.0):
        IS.box(x - 0.1, x + 0.1, 0.0, 9.4, ZF + 0.9, ZF + 2.6, WOOD2)
# стенд с позвонками и лампы-переноски
IS.box(-0.15, 0.15, 0.0, 7.2, ZF + 1.6, ZF + 1.9, STEEL)
for k in range(6):
    IS.box(-0.5, 0.5, 2.0 + 0.9 * k, 2.7 + 0.9 * k, ZF + 1.4, ZF + 2.1, BONE)
F.objects(False)
# за экспонатом — тёмная доска-план раскопа с меловой сеткой: кремовый череп читается на тёмном, а не на кремовой стене
IR.box(-5.4, 5.4, 2.2, 7.7, ZF + 0.88, ZF + 0.98, "3A4044")
for k in range(5):
    x = -3.6 + 1.8 * k
    IS.box(x - 0.05, x + 0.05, 2.4, 7.5, ZF + 0.98, ZF + 1.02, PLASTER)
for k in range(4):
    y = 3.3 + 1.2 * k
    IS.box(-5.2, 5.2, y - 0.05, y + 0.05, ZF + 1.02, ZF + 1.06, PLASTER)
IS.frame_xy(K.rect(-5.7, 5.7, 1.9, 7.9), K.rect(-5.4, 5.4, 2.2, 7.7), ZF + 0.88, ZF + 1.1, WOOD2)
for k in range(5):  # карта слоёв на стене над стендом
    IS.box(-3.6, 3.6, 8.0 + 0.9 * k, 8.9 + 0.9 * k, ZF + 0.88, ZF + 0.98, LAYERS[k])
IS.box(-3.8, 3.8, 12.5, 12.7, ZF + 0.88, ZF + 1.02, WOOD2)
for x, z in ((-6.0, -6.0), (6.0, -6.0), (0.0, 4.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.0, C - 0.8, z - 0.03, z + 0.03, "3A3A40")
    D.lantern(IS, IG, x, C - 4.0, z, s=1.0, cap=WOOD2, light="FFE8B0")
# постамент: «пласт» из трёх слоёв песчаника
px, pz = PED
# верхний пласт — тёмный аргиллит: кремовый череп не сливается с подставкой
for k, (r, y0, y1, col) in enumerate(((4.4, 0.0, 0.5, RED), (4.0, 0.5, 1.0, OCHRE), (3.6, 1.0, TOP, "3A2E28"))):
    IR.prism_xz(K.octa(px, pz, r, r * 0.92, r * 0.3), y0, y1, col)
F.objects(True)
for k in range(4):
    a = math.pi / 2 * k + 0.6
    bone(IS, (px + 4.3 * math.cos(a), 0.4, pz + 4.3 * math.sin(a)), (px + 4.6 * math.cos(a + 0.35), 0.4, pz + 4.6 * math.sin(a + 0.35)), 0.2)
F.objects(False)
B.lift_leaves(IS, WOOD2, OCHRE)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, RED, "C89A6A", OCHRE, top=16.6, roof="none")
SL.box(-FX - 0.3, FX + 0.3, 16.6, 18.4, -FZ - 1.25, FZ + 0.3, CREAM)
SL.prism_xy([(11.6 - 1.2, -0.1), (11.6 + 1.2, -0.1), (11.6, 12.0)], -FZ - 2.6, -FZ - 2.2, WOOD)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 1900, (1.0, 0.94, 0.84)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.96, 0.88)),
                                                   ("Warm", (0, 6, -12), 600, (1.0, 0.75, 0.5))])
