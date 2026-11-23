"""Этаж «Рыба-мираж» музея-небоскрёба (десятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — придорожный мотель «Мираж» в пустыне. Снаружи — розово-бирюзовый мотель в стиле 50-х: длинная
галерея номеров с цветными дверями и номерными табличками-кружками, навес-«бумеранг» над ресепшеном, высокий
столб-вывеска с неоновой рыбой и стрелкой, звёздочки-«атомы», ретро-автомобиль у входа, кактусы в кадках,
автомат с газировкой, бассейн-«мираж» с переливающейся водой. Внутри — холл-лаунж: стойка ресепшена с доской
ключей, пол-«мираж» с волнистыми полосами воды, ретро-диваны и кресла, торшеры-«атомы», неоновая рыба
на стене, потолочный вентилятор; экспонат — на круглом островке-оазисе с кольцом ряби.
Запуск: blender --background --factory-startup --python scripts/blender/floor_motel.py -- <репо> <превью>
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
from floorbase import C, FX, FZ, W, ZB, ZF, beam, rng, taper  # noqa: E402

PINK, PINK2, TURQ, TURQ2, CREAM, NEON = "F2A0B4", "D87890", "3ACAC0", "2A9A92", "F6EEDC", "FF5AA8"
NEON2, YEL, CHROME, DARK, SAND, WATER = "5AF0FF", "F6D040", "C8D0D8", "2A2A34", "E8D2A0", "4AC8F0"
RED, GREEN, GLASS = "E04A4A", "4A9A4A", "C8F0F0"
DOORS = (TURQ, YEL, "F28A3A", "6A8AE0", RED, "8AD060")

F = B.Floor("MI", "MirageFish", quiet=(PINK2, SAND, "7AB8C0"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def atom(p, x, y, z, r, col):
    """Звёздочка-«атом» 50-х: три луча крест-накрест и шарик."""
    for k in range(3):
        a = math.pi * k / 3
        beam(p, (x - r * math.cos(a), y - r * math.sin(a), z), (x + r * math.cos(a), y + r * math.sin(a), z), 0.12, 0.08, col, up=(0, 0, 1))
    p.prism_xy(K.ngon(x, y, r * 0.22, 6), z - 0.08, z + 0.08, col)


def neon_fish(p, x, y, z, s, col, d=1):
    """Неоновая рыба контуром: тело-ромб и хвост из брусков."""
    pts = [(x + d * s, y), (x, y + s * 0.5), (x - d * s * 0.8, y), (x, y - s * 0.5), (x + d * s, y)]
    for a, b in zip(pts, pts[1:]):
        beam(p, (a[0], a[1], z), (b[0], b[1], z), 0.16, 0.12, col, up=(0, 0, 1))
    for e in (-1, 1):
        beam(p, (x - d * s * 0.8, y, z), (x - d * s * 1.4, y + e * s * 0.45, z), 0.16, 0.12, col, up=(0, 0, 1))
    beam(p, (x - d * s * 1.4, y - s * 0.45, z), (x - d * s * 1.4, y + s * 0.45, z), 0.16, 0.12, col, up=(0, 0, 1))
    p.prism_xy(K.ngon(x + d * s * 0.45, y + s * 0.08, 0.12, 6), z - 0.08, z + 0.08, col)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, PINK, TURQ2, TURQ, SAND, "2A4A5A", roof="flat", roof_col=PINK, top=16.0, band=(8.2, 8.6, TURQ),
         side=S.side_windows(F, TURQ2, GLASS, kind="rect", y0=10.0, y1=13.4, w=2.4, xs=(-12.45, -4.95, 2.55, 10.05)))
# галерея номеров: двери, кружки-номера, окна верхнего ряда
for k in range(6):
    x = -15.6 + 2.6 * k if k < 3 else 4.6 + 2.6 * (k - 3)
    FS.box(x, x + 1.8, 1.0, 6.8, -FZ - 1.0, -FZ - 0.88, DOORS[k])
    FS.prism_xy(K.ngon(x + 0.9, 5.6, 0.4, 10), -FZ - 1.1, -FZ - 1.0, CREAM)
    FS.box(x + 1.4, x + 1.6, 3.6, 4.0, -FZ - 1.12, -FZ - 1.0, CHROME)
for x in (-14.4, -8.4, 5.6, 11.6):
    S.window(F, "z", -FZ, -1, x, 10.0, 13.4, 3.6, CREAM, GLASS, kind="rect")
# галерея-козырёк на тонких столбах вдоль номеров
FS.box(-FX - 0.2, FX + 0.2, 7.6, 7.9, -FZ - 3.0, -FZ - 0.88, CREAM)
FS.box(-FX - 0.2, FX + 0.2, 7.9, 8.2, -FZ - 3.05, -FZ - 2.8, TURQ)
for x in (-16.8, -12.0, -7.2, 7.2, 12.0, 16.8):
    FS.box(x - 0.12, x + 0.12, -0.1, 7.6, -FZ - 2.8, -FZ - 2.56, CHROME)
# ресепшен со стеклянной стеной и навесом-«бумерангом»
FG.box(-4.4, 3.4, 1.0, 7.0, -FZ - 0.92, -FZ - 0.88, GLASS)
FS.frame_xy(K.rect(-4.7, 3.7, 0.7, 7.3), K.rect(-4.4, 3.4, 1.0, 7.0), -FZ - 1.1, -FZ - 0.88, TURQ2)
FS.box(-0.6, -0.4, 1.0, 7.0, -FZ - 1.0, -FZ - 0.9, TURQ2)
FS.prism_xz([(-6.6, -FZ - 0.9), (5.4, -FZ - 0.9), (6.2, -FZ - 4.0), (0.2, -FZ - 2.8), (-5.4, -FZ - 4.2)], 9.0, 9.4, CREAM)
FS.prism_xz([(-6.6, -FZ - 0.9), (5.4, -FZ - 0.9), (6.2, -FZ - 4.0), (0.2, -FZ - 2.8), (-5.4, -FZ - 4.2)], 8.8, 9.0, NEON)
# атомы-звёзды по фасаду
for (x, y) in ((-11.2, 15.0), (-2.0, 14.4), (7.6, 15.2), (15.2, 14.6)):
    atom(FS, x, y, -FZ - 1.0, 0.7, YEL if x < 0 else NEON2)
# столб-вывеска с неоновой рыбой и стрелкой (правый угол по фасаду −x)
PX = -FX - 1.6
FS.box(PX - 0.25, PX + 0.25, -0.1, 18.6, -FZ - 1.9, -FZ - 1.4, CHROME)
FS.box(PX - 3.0, PX + 3.0, 12.6, 17.8, -FZ - 1.9, -FZ - 1.6, TURQ2)
FS.frame_xy(K.rect(PX - 3.2, PX + 3.2, 12.4, 18.0), K.rect(PX - 3.0, PX + 3.0, 12.6, 17.8), -FZ - 2.0, -FZ - 1.6, CHROME)
neon_fish(FG, PX + 0.2, 15.2, -FZ - 2.0, 1.6, NEON2, d=1)
FG.prism_xy([(PX - 2.6, 11.4), (PX + 1.4, 11.4), (PX + 1.4, 10.6), (PX + 2.6, 11.8), (PX + 1.4, 13.0), (PX + 1.4, 12.2), (PX - 2.6, 12.2)],
            -FZ - 1.98, -FZ - 1.9, NEON)
for k in range(8):
    FG.prism_xy(K.ngon(PX - 2.4 + 0.6 * k, 10.0, 0.14, 6), -FZ - 1.98, -FZ - 1.9, YEL)
# ретро-автомобиль, кадки с кактусами, автомат газировки, бассейн-мираж
F.objects(True)
CX = 8.4
FS.loft([(CX - 3.4, 0.6, -FZ - 3.4), (CX + 3.4, 0.6, -FZ - 3.4), (CX + 3.4, 0.6, -FZ - 1.6), (CX - 3.4, 0.6, -FZ - 1.6)],
        [(CX - 3.6, 1.6, -FZ - 3.4), (CX + 3.6, 1.6, -FZ - 3.4), (CX + 3.6, 1.6, -FZ - 1.6), (CX - 3.6, 1.6, -FZ - 1.6)], TURQ)
FS.loft([(CX - 1.8, 1.6, -FZ - 3.3), (CX + 1.4, 1.6, -FZ - 3.3), (CX + 1.4, 1.6, -FZ - 1.7), (CX - 1.8, 1.6, -FZ - 1.7)],
        [(CX - 1.2, 2.6, -FZ - 3.2), (CX + 0.8, 2.6, -FZ - 3.2), (CX + 0.8, 2.6, -FZ - 1.8), (CX - 1.2, 2.6, -FZ - 1.8)], CREAM)
FS.box(CX - 3.7, CX + 3.7, 0.7, 0.95, -FZ - 3.5, -FZ - 1.5, CHROME)
for x in (CX - 2.2, CX + 2.2):
    S.disc(FS, (x, 0.5, -FZ - 3.5), (0, 0, -1), 0.6, 0.3, DARK, seg=10)
FS.prism_xy([(CX + 3.6, 1.1), (CX + 4.4, 1.9), (CX + 3.6, 1.6)], -FZ - 2.6, -FZ - 2.4, TURQ)
for x in (-17.2, -10.0):
    FS.prism_xz(K.ngon(x, -FZ - 2.2, 0.7, 8), -0.1, 0.9, "C86A3A")
    FS.prism_xz(K.ngon(x, -FZ - 2.2, 0.35, 8), 0.9, 3.4, GREEN)
    FS.box(x, x + 0.9, 1.8, 2.3, -FZ - 2.4, -FZ - 2.0, GREEN)
    FS.prism_xz(K.ngon(x + 0.75, -FZ - 2.2, 0.22, 6), 2.3, 3.0, GREEN)
FS.box(-7.6, -5.6, -0.1, 5.4, -FZ - 1.9, -FZ - 0.9, RED)
FG.box(-7.3, -5.9, 2.6, 4.8, -FZ - 1.94, -FZ - 1.9, "F8E8C8")
for k in range(3):
    FS.box(-7.2 + 0.5 * k, -6.9 + 0.5 * k, 3.0, 4.4, -FZ - 1.98, -FZ - 1.94, (YEL, NEON2, CREAM)[k])
F.objects(False)
FR.box(-4.4, 3.4, -0.1, 0.3, -FZ - 2.9, -FZ - 1.2, CREAM)
FG.box(-4.0, 3.0, 0.2, 0.32, -FZ - 2.6, -FZ - 1.5, WATER)
for k in range(4):
    FS.box(-3.6 + 1.7 * k, -2.6 + 1.7 * k, 0.32, 0.36, -FZ - 2.3 + 0.3 * (k % 2), -FZ - 2.2 + 0.3 * (k % 2), "A8F0FF")

# ══ ИНТЕРЬЕР: холл-лаунж ══════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.1
S.interior(F, "F4E4E0", SAND, "3A5A6A", TURQ, wain=(3.2, PINK2), beams=None)
for k in range(9):  # пол-«мираж»: волнистые полосы воды
    z = -13.0 + 3.0 * k
    pts = [(-W + 1.0 + (2 * W - 2.0) * j / 14, z + 0.5 * math.sin(j * 0.9 + k)) for j in range(15)]
    for a, b in zip(pts, pts[1:]):
        IQ.loft([(a[0], 0.03, a[1] - 0.35), (b[0], 0.03, b[1] - 0.35), (b[0], 0.03, b[1] + 0.35), (a[0], 0.03, a[1] + 0.35)],
                [(a[0], 0.06, a[1] - 0.35), (b[0], 0.06, b[1] - 0.35), (b[0], 0.06, b[1] + 0.35), (a[0], 0.06, a[1] + 0.35)],
                "8ACCE0" if k % 2 else "B8E4EE")
F.objects(True)
# стойка ресепшена и доска ключей у дальней стены
IS.box(-6.0, 6.0, 0.0, 3.4, ZF + 3.0, ZF + 4.6, TURQ)
IS.box(-6.3, 6.3, 3.4, 3.7, ZF + 2.8, ZF + 4.8, CREAM)
for k in range(7):
    IS.box(-5.6 + 1.6 * k, -5.2 + 1.6 * k, 0.4, 3.0, ZF + 4.6, ZF + 4.66, NEON if k % 2 else YEL)
IS.box(-4.0, 4.0, 5.6, 9.4, ZF + 0.88, ZF + 1.0, "8A5A3A")
for j in range(3):
    for k in range(8):
        IS.box(-3.6 + 1.0 * k - 0.06, -3.6 + 1.0 * k + 0.06, 8.4 - 1.2 * j, 8.6 - 1.2 * j, ZF + 1.0, ZF + 1.2, CHROME)
        IS.box(-3.6 + 1.0 * k - 0.15, -3.6 + 1.0 * k + 0.15, 7.6 - 1.2 * j, 8.4 - 1.2 * j, ZF + 1.1, ZF + 1.16, DOORS[(j + k) % 6])
# ретро-диваны и кресла вдоль боковых стен
for s in (-1, 1):
    x = s * (W - 2.2)
    IS.box(x - 1.3, x + 1.3, 0.6, 1.6, -11.0, -4.0, DOORS[(s + 3) % 6])
    IS.box(*sorted((x + s * 0.6, x + s * 1.3)), 1.6, 3.6, -11.0, -4.0, DOORS[(s + 3) % 6])
    for z in (-10.6, -4.4):
        IS.box(x - 1.1, x + 1.1, 0.0, 0.6, z - 0.2, z + 0.2, CHROME)
    for z in (1.0, 6.0):
        cx = x - s * 0.6  # ретро-кресло на хромированной ножке: сиденье, высокая спинка, подлокотники
        IS.prism_xz(K.ngon(cx, z, 0.25, 6), 0.0, 1.0, CHROME)
        IS.box(cx - 1.0, cx + 1.0, 1.0, 1.7, z - 1.0, z + 1.0, NEON if s > 0 else TURQ)
        IS.box(*sorted((cx + s * 0.7, cx + s * 1.0)), 1.7, 3.8, z - 1.0, z + 1.0, NEON if s > 0 else TURQ)
        for e in (-1, 1):
            IS.box(cx - 1.0, cx + 1.0, 1.7, 2.4, z + e * 0.85 - 0.15, z + e * 0.85 + 0.15, CREAM)
# торшеры-«атомы»
for x, z in ((-9.0, -12.0), (9.0, -12.0), (-9.0, 8.0), (9.0, 8.0)):
    IS.prism_xz(K.ngon(x, z, 0.5, 8), 0.0, 0.2, DARK)
    IS.box(x - 0.08, x + 0.08, 0.2, 6.2, z - 0.08, z + 0.08, CHROME)
    for k in range(3):
        a = 2 * math.pi * k / 3
        beam(IS, (x, 6.2, z), (x + 1.0 * math.cos(a), 7.0, z + 1.0 * math.sin(a)), 0.1, 0.1, CHROME)
        IG.prism_xz(K.ngon(x + 1.0 * math.cos(a), z + 1.0 * math.sin(a), 0.3, 6), 7.0, 7.4, "FFF0C8")
F.objects(False)
# неоновая рыба на дальней стене, неоновые полосы по бокам, потолочный вентилятор
neon_fish(IG, 0.0, 12.6, ZF + 1.0, 2.2, NEON2, d=-1)
for s in (-1, 1):
    x = s * (W - 0.9)
    for k in range(3):
        y = 11.0 + 1.0 * k
        IS.box(*sorted((x, x - s * 0.1)), y - 0.06, y + 0.06, -6.0, 2.0, (NEON, NEON2, YEL)[k])
IS.box(-0.08, 0.08, C - 2.0, C - 0.2, 4.0 - 0.08, 4.0 + 0.08, CHROME)
IS.prism_xz(K.ngon(0.0, 4.0, 0.5, 8), C - 2.4, C - 2.0, CHROME)
for k in range(4):
    a = math.pi / 2 * k
    IS.box(-0.3 + 1.6 * math.cos(a) - 0.0, 0.3 + 1.6 * math.cos(a), C - 2.3, C - 2.2, 4.0 + 1.6 * math.sin(a) - 0.3,
           4.0 + 1.6 * math.sin(a) + 0.3, "8A5A3A")
# постамент: островок-оазис с кольцом ряби
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.2, 18), 0.0, 0.35, SAND)
IG.prism_xz(K.ngon(px, pz, 3.8, 18), 0.35, 0.45, WATER)
S.annulus(IS, (px, 0.45, pz), (0, 1, 0), 3.3, 3.45, 0.06, "B8F0FF", seg=18)
IR.prism_xz(K.ngon(px, pz, 2.8, 14), 0.35, TOP, SAND)
F.objects(True)
for a in (-math.pi / 2, 0.15, math.pi - 0.15):  # сзади и по бокам — вид от лифта на экспонат свободен
    D.palm(IS, (px + 6.4 * math.cos(a), 0.0, pz + 6.4 * math.sin(a)), (0.6 * math.cos(a), 0.6 * math.sin(a)), 5.0)  # пальмы вокруг, не на постаменте
F.objects(False)
B.lift_leaves(IS, TURQ2, PINK)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, PINK, SAND, PINK, top=16.0)
SL.box(PX - 3.2, PX + 3.2, 12.4, 18.0, -FZ - 2.0, -FZ - 1.6, TURQ2)
SL.box(-FX - 0.2, FX + 0.2, 7.6, 8.2, -FZ - 3.0, -FZ, CREAM)

F.build(exhibit=(PED[0], TOP, PED[1], 3.2), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.93, 0.92)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.94)),
                                                   ("Neon", (0, 8, -12), 700, (1.0, 0.5, 0.8))])
