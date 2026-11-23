"""Этаж «Турникет-терминатор» музея-небоскрёба (седьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — футбольный стадион. Снаружи — бетонная чаша с частыми рёбрами-пилонами, синий пояс облицовки с
белыми полосами и консольный козырёк крыши на стальных подкосах; на передних углах — мачты прожекторов с панелями
ламп; внизу у входа — ряд турникетов с красными и зелёными огнями под стальным навесом, над входом — большой
мяч-эмблема, справа — зигзаг бетонных пандусов с перилами на верхние ярусы, слева — киоск касс; между рёбрами —
красные и синие знамёна болельщиков, на площади — стойки ограждения. Внутри — поле: газон полосами, белая разметка
(центральный круг вокруг постамента, линии, штрафная), у дальней стены — ворота с сеткой и табло со счётом,
по бокам — трибуны в четыре яруса с синими и жёлтыми креслами, скамейки запасных под прозрачными навесами, угловые
флажки, мячи; у лифта — арка выхода игроков; экспонат — на круглом постаменте с газоном и синей подсветкой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_stadium.py -- <репо> <превью>
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

CONC, CONC2, BLUE, BLUE2, RED = "C2C2BA", "A2A29A", "2A5AC8", "1E449A", "D83434"
STEEL, STEEL2, GRASS, GRASS2, WHITE, YEL, DARK = "8E98A6", "6A7482", "4FA83C", "438F33", "F4F4F0", "F2C230", "2A2E36"
LAMP = "F4F8FF"

F = B.Floor("SG", "TurnstileTerminator", quiet=(GRASS, GRASS2, "9C9C94"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def ball(p, x, y, z, r):
    """Футбольный мяч: белый гранёный ком с тёмными пятнами по бокам."""
    p.prism_xz(K.octa(x, z, r, r, r * 0.4), y - r * 0.55, y + r * 0.55, WHITE)
    p.prism_xz(K.octa(x, z, r * 0.7, r * 0.7, r * 0.28), y + r * 0.55, y + r * 0.85, WHITE)
    p.prism_xz(K.octa(x, z, r * 0.7, r * 0.7, r * 0.28), y - r * 0.85, y - r * 0.55, WHITE)
    p.prism_xz(K.ngon(x, z, r * 0.32, 5), y + r * 0.85, y + r * 0.88, DARK)
    for k in range(4):
        t = math.pi / 2 * k
        p.box(x + r * 1.0 * math.cos(t) - 0.04 - 0.16 * abs(math.sin(t)), x + r * 1.0 * math.cos(t) + 0.04 + 0.16 * abs(math.sin(t)),
              y - 0.18 * r, y + 0.18 * r,
              z + r * 1.0 * math.sin(t) - 0.04 - 0.16 * abs(math.cos(t)), z + r * 1.0 * math.sin(t) + 0.04 + 0.16 * abs(math.cos(t)), DARK)


def emblem(p, cx, cy, z0, z1, r):
    """Мяч-эмблема на стене (вид спереди): белый круг, чёрный пятиугольник в центре и пять долек по краю."""
    p.prism_xy(K.ngon(cx, cy, r, 20), z0 + 0.06, z1, WHITE)
    p.prism_xy(K.ngon(cx, cy, r * 0.3, 5, 0.25), z0, z0 + 0.06, DARK)
    for k in range(5):
        t = math.pi / 2 + 2 * math.pi * k / 5
        x, y = cx + r * 0.72 * math.cos(t), cy + r * 0.72 * math.sin(t)
        p.prism_xy(K.ngon(x, y, r * 0.2, 5, 0.25), z0, z0 + 0.06, DARK)
    p.frame_xy(K.ngon(cx, cy, r + 0.35, 20), K.ngon(cx, cy, r, 20), z0 - 0.1, z1, BLUE)


def turnstile(p, g, x, z, y=0.0, ok=True):
    """Турникет: стальная тумба, трипод, огонёк."""
    p.box(x - 0.35, x + 0.35, y, y + 1.6, z - 0.5, z + 0.5, STEEL)
    p.box(x - 0.4, x + 0.4, y + 1.6, y + 1.75, z - 0.55, z + 0.55, DARK)
    for k in range(3):
        t = 2 * math.pi * k / 3
        beam(p, (x + 0.35, y + 1.2, z), (x + 1.25, y + 1.2 + 0.4 * math.sin(t), z + 0.8 * math.cos(t)), 0.1, 0.1, STEEL)
    g.box(x - 0.15, x + 0.15, y + 1.75, y + 1.85, z - 0.15, z + 0.15, "5AE07A" if ok else "FF4040")


def floodlight(p, g, x, z, y0, y1, face):
    """Мачта прожекторов: стальная опора и наклонная панель ламп 4 × 3 (face — куда смотрит по z)."""
    p.prism_xz(K.ngon(x, z, 0.35, 8), y0, y1 - 2.4, STEEL2)
    p.box(x - 2.0, x + 2.0, y1 - 2.6, y1 - 2.4, z - 0.4, z + 0.4, STEEL2)
    p.box(x - 2.0, x + 2.0, y1 - 2.4, y1, z - 0.25, z + 0.25, DARK)
    for i in range(4):
        for j in range(3):
            g.box(x - 1.85 + 0.95 * i, x - 1.15 + 0.95 * i, y1 - 2.25 + 0.75 * j, y1 - 1.7 + 0.75 * j,
                  z + face * 0.25, z + face * 0.3, LAMP)


# ══ ФАСАД: стадион ════════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, CONC, CONC, "DDE8F0")
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "9C9C94")
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.2, CONC2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.2, 12.0, CONC)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, 12.0, 15.6, BLUE)
    for y in (12.8, 14.4):
        slab(FS, axis, fixed, out, 1.42, -half - 0.3, half + 0.3, y, y + 0.3, WHITE)
    slab(FR, axis, fixed, out, 0.88, -half, half, 15.6, 17.0, CONC2)
    # консольный козырёк крыши на подкосах
    chamfer_prof = [(0.88, 17.0), (3.4, 17.6), (3.4, 18.0), (0.88, 18.9)]
    B.chamfer(FS, axis, fixed, out, -half - 0.6, half + 0.6, chamfer_prof, WHITE)
    for k in range(int(2 * half // 6.0) + 1):
        a = -half + 1.5 + 6.0 * k
        if a > half - 1.0:
            continue
        p0 = (fixed + out * 1.4, 15.6, a) if axis == "x" else (a, 15.6, fixed + out * 1.4)
        p1 = (fixed + out * 3.2, 17.55, a) if axis == "x" else (a, 17.55, fixed + out * 3.2)
        beam(FS, p0, p1, 0.3, 0.3, STEEL2)
    # рёбра-пилоны чаши
    for k in range(int(2 * half // 3.0) + 1):
        a = -half + 0.6 + 3.0 * k
        if a + 0.8 > half:
            continue
        if fi == 0 and -9.6 < a < 9.6:
            continue
        slab(FR, axis, fixed, out, 1.48, a, a + 0.8, 1.2, 12.0, CONC2)
    if fi > 0:  # бока и тыл: светлая лента окон и знамёна
        slab(FG, axis, fixed, out, 0.92, -half + 1.0, half - 1.0, 9.6, 10.6, "DDEEFA")
        for k in range(int(2 * half // 6.0)):
            a = -half + 2.1 + 6.0 * k
            if a + 1.6 > half:
                continue
            col = RED if k % 2 else BLUE2
            if axis == "x":
                FS.prism_zy([(a, 8.8), (a + 1.6, 8.8), (a + 1.6, 4.2), (a + 0.8, 3.4), (a, 4.2)], *sorted((fixed + out * 0.9, fixed + out * 1.05)), col)
                FS.box(*sorted((fixed + out * 0.9, fixed + out * 1.1)), 4.6, 5.0, a, a + 1.6, WHITE)
            else:
                FS.prism_xy([(a, 8.8), (a + 1.6, 8.8), (a + 1.6, 4.2), (a + 0.8, 3.4), (a, 4.2)], *sorted((fixed + out * 0.9, fixed + out * 1.05)), col)
                FS.box(a, a + 1.6, 4.6, 5.0, *sorted((fixed + out * 0.9, fixed + out * 1.1)), WHITE)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# вход: тёмный проём, ряд турникетов под стальным навесом
FS.box(-9.4, 9.4, 1.2, 8.0, -FZ - 0.96, -FZ - 0.88, DARK)
FG.box(-9.0, 9.0, 4.4, 7.6, -FZ - 1.0, -FZ - 0.96, "C8E0F4")
for x in (-6.0, -3.0, 0.0, 3.0, 6.0):
    FS.box(x - 0.08, x + 0.08, 4.4, 7.6, -FZ - 1.06, -FZ - 1.0, STEEL2)
F.objects(True)
for k, x in enumerate((-7.6, -4.6, -1.6, 1.4, 4.4, 7.4)):
    turnstile(FS, FG, x, -FZ - 1.6, y=1.2 - 1.3, ok=k != 2)
FS.box(-9.6, 9.6, 3.8, 4.2, -FZ - 2.8, -FZ - 0.88, STEEL)  # навес
for x in (-9.2, 0.0, 9.2):
    FS.box(x - 0.15, x + 0.15, -0.1, 3.8, -FZ - 2.7, -FZ - 2.4, STEEL2)
F.objects(False)
emblem(FS, 0.0, 10.0, -FZ - 1.3, -FZ - 0.88, 1.6)
# справа (по фасаду +x): зигзаг пандусов с перилами
for k, (y0, y1, sx) in enumerate(((1.2, 5.0, 1), (5.0, 8.8, -1), (8.8, 11.8, 1))):
    xa, xb = (10.4, 17.2) if sx > 0 else (17.2, 10.4)
    FR.prism_xy([(xa, y0 - 0.5), (xb, y1 - 0.5), (xb, y1), (xa, y0)], -FZ - 2.6, -FZ - 0.88, CONC2)
    for i in range(7):
        t = i / 6
        x = xa + (xb - xa) * t
        y = y0 + (y1 - y0) * t
        FS.box(x - 0.05, x + 0.05, y, y + 1.0, -FZ - 2.58, -FZ - 2.48, STEEL)
    beam(FS, (xa, y0 + 1.0, -FZ - 2.53), (xb, y1 + 1.0, -FZ - 2.53), 0.12, 0.12, STEEL)
for x in (10.4, 17.2):
    FR.box(x - 0.4, x + 0.4, -0.1, 11.8, -FZ - 2.4, -FZ - 0.88, CONC2)
# слева: киоск касс
F.objects(True)
FS.box(-17.0, -11.6, -0.1, 5.4, -FZ - 2.6, -FZ - 0.88, BLUE2)
FS.box(-17.2, -11.4, 5.4, 5.9, -FZ - 2.8, -FZ - 0.88, WHITE)
for x in (-15.8, -13.0):
    FG.box(x - 0.9, x + 0.9, 2.4, 4.4, -FZ - 2.64, -FZ - 2.6, "FFE8B0")
    FS.box(x - 1.0, x + 1.0, 2.2, 2.4, -FZ - 3.0, -FZ - 2.6, STEEL)
F.objects(False)
# знамёна болельщиков над киоском
for k, a in enumerate((-16.4, -13.4)):
    col = (RED, BLUE2)[k]
    FS.prism_xy([(a, 11.8), (a + 1.6, 11.8), (a + 1.6, 7.2), (a + 0.8, 6.4), (a, 7.2)], -FZ - 1.05, -FZ - 0.9, col)
    FS.box(a, a + 1.6, 9.0, 9.4, -FZ - 1.1, -FZ - 0.9, WHITE)
    FS.box(a - 0.2, a + 1.8, 11.8, 12.0, -FZ - 1.2, -FZ - 0.9, STEEL2)
# мачты прожекторов на передних углах
for e in (-1, 1):
    floodlight(FS, FG, e * (FX + 0.9), -FZ - 1.6, -0.1, 18.8, -1)
# стойки ограждения на площади
for x in (-10.6, -9.2, 9.2):
    FS.box(x - 0.06, x + 0.06, -0.1, 1.1, -FZ - 2.7, -FZ - 2.6, STEEL)

# ══ ИНТЕРЬЕР: поле и трибуны ══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.0
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), GRASS)
for k in range(-5, 5):  # полосы газона
    if k % 2 == 0:
        IQ.box(-11.0, 11.0, 0.02, 0.04, 3.0 * k, 3.0 * k + 3.0, GRASS2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, CONC)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 1.0, BLUE2)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, CONC)
    slab(IR, axis, fixed, out, 1.3, -half, half, 15.6, 16.6, BLUE)
    slab(IS, axis, fixed, out, 1.35, -half, half, 16.0, 16.2, WHITE)
for k in range(-3, 4):  # фермы крыши
    IS.box(-W, W, C - 0.8, C - 0.3, 4.4 * k - 0.2, 4.4 * k + 0.2, STEEL2)
# разметка поля
LW = 0.18
for s in (-1, 1):
    IS.box(s * 11.0 - LW / 2, s * 11.0 + LW / 2, 0.02, 0.06, ZF + 1.2, ZB - 1.2, WHITE)
IS.box(-11.0, 11.0, 0.02, 0.06, ZF + 1.2 - LW / 2, ZF + 1.2 + LW / 2, WHITE)
IS.box(-11.0, -4.8, 0.02, 0.06, -3.0 - LW / 2, -3.0 + LW / 2, WHITE)
IS.box(4.8, 11.0, 0.02, 0.06, -3.0 - LW / 2, -3.0 + LW / 2, WHITE)
ring_y(IS, 0.0, -3.0, 5.8, 5.8 + LW, 0.02, 0.06, WHITE, n=28)
for s in (-1, 1):  # штрафная у дальних ворот
    IS.box(s * 7.0 - LW / 2, s * 7.0 + LW / 2, 0.02, 0.06, ZF + 1.2, ZF + 5.6, WHITE)
IS.box(-7.0, 7.0, 0.02, 0.06, ZF + 5.6 - LW / 2, ZF + 5.6 + LW / 2, WHITE)
# ворота с сеткой у дальней стены
F.objects(True)
GZ = ZF + 1.3
for s in (-1, 1):
    IS.box(s * 4.0 - 0.15, s * 4.0 + 0.15, 0.0, 3.4, GZ - 0.15, GZ + 0.15, WHITE)
IS.box(-4.15, 4.15, 3.4, 3.7, GZ - 0.15, GZ + 0.15, WHITE)
F.objects(False)
for k in range(9):  # сетка ворот
    x = -3.6 + 0.9 * k
    IS.box(x - 0.03, x + 0.03, 0.0, 3.4, ZF + 0.92, ZF + 0.98, "D8DCE0")
for k in range(4):
    y = 0.8 * (k + 1)
    IS.box(-4.0, 4.0, y - 0.03, y + 0.03, ZF + 0.92, ZF + 0.98, "D8DCE0")
for s in (-1, 1):
    IS.prism_zy([(ZF + 0.95, 0.0), (GZ, 0.0), (GZ, 3.4), (ZF + 0.95, 3.4)], s * 4.0 - 0.03, s * 4.0 + 0.03, "D8DCE0")
IS.box(-4.0, 4.0, 3.37, 3.43, ZF + 0.95, GZ, "D8DCE0")
# табло над воротами: «1 : 0» пикселями
IS.box(-7.0, 7.0, 10.0, 14.8, ZF + 0.88, ZF + 1.4, DARK)
IS.frame_xy(K.rect(-7.2, 7.2, 9.8, 15.0), K.rect(-7.0, 7.0, 10.0, 14.8), ZF + 0.88, ZF + 1.6, BLUE)
DIG = {"1": ["010", "110", "010", "010", "111"], "0": ["111", "101", "101", "101", "111"], ":": ["0", "1", "0", "1", "0"]}
x0 = -4.6
for ch in "1:0":
    rows = DIG[ch]
    for r, row in enumerate(rows):
        for c, v in enumerate(row):
            if v == "1":
                IG.box(x0 + 0.7 * c, x0 + 0.7 * c + 0.6, 13.6 - 0.7 * r, 14.2 - 0.7 * r, ZF + 1.4, ZF + 1.44, YEL)
    x0 += 0.7 * len(rows[0]) + 1.4
for x in (-6.4, 5.0):
    IG.box(x, x + 1.4, 10.4, 10.9, ZF + 1.4, ZF + 1.44, RED if x < 0 else BLUE)
# трибуны в четыре яруса по бокам
for s in (-1, 1):
    for t in range(4):
        x_in = s * (W - 4.6 + 1.15 * t)
        x0, x1 = sorted((x_in, s * W))
        IR.box(x0, x1, 0.0, 1.0 + 1.0 * t, ZF + 0.88, 8.6, CONC2 if t % 2 else CONC)
        F.objects(True)
        for k in range(8):
            z0 = ZF + 1.2 + 2.9 * k
            col = (BLUE, YEL)[(k + t) % 2]
            xs = x_in + s * 0.15
            IS.box(*sorted((xs, xs + s * 0.75)), 1.0 + 1.0 * t, 1.45 + 1.0 * t, z0, z0 + 2.6, col)
            IS.box(*sorted((xs + s * 0.75, xs + s * 0.95)), 1.45 + 1.0 * t, 2.1 + 1.0 * t, z0, z0 + 2.6, col)
        F.objects(False)
    xr = s * (W - 4.75)
    IS.box(xr - 0.05, xr + 0.05, 1.0, 2.1, ZF + 0.88, 8.6, STEEL)
    for k in range(9):
        z = ZF + 1.0 + 2.9 * k
        IS.box(xr - 0.05, xr + 0.05, 0.0, 2.1, z - 0.05, z + 0.05, STEEL)
    IR.box(*sorted((s * (W - 4.6), s * W)), 0.0, 5.0, 8.6, 9.2, CONC2)  # торец трибуны
# скамейки запасных под прозрачными навесами
F.objects(True)
for s in (-1, 1):
    x = s * 9.8
    IS.box(x - 0.9, x + 0.9, 0.0, 0.9, 2.0, 7.0, DARK)
    IS.box(*sorted((x + s * 0.7, x + s * 0.9)), 0.9, 3.4, 2.0, 7.0, STEEL)
    IS.box(*sorted((x - s * 1.1, x + s * 0.9)), 3.4, 3.55, 2.0, 7.0, "A8D0F0")
    IS.box(x - 0.8, x + 0.8, 0.9, 1.2, 2.2, 6.8, BLUE if s > 0 else RED)
F.objects(False)
# угловые флажки и мячи
for s in (-1, 1):
    x, z = s * 10.6, ZF + 1.6
    IS.box(x - 0.05, x + 0.05, 0.0, 2.6, z - 0.05, z + 0.05, YEL)
    IS.prism_xy([(x, 2.6), (x, 1.8), (x + s * 0.9, 2.2)], z - 0.03, z + 0.03, RED)
F.objects(True)
ball(IS, -2.0, 0.55, ZF + 6.4, 0.55)
ball(IS, 8.2, 0.5, 0.0, 0.5)
F.objects(False)
# арка выхода игроков вокруг двери лифта
IS.frame_xy([(-5.6, 0.0), (5.6, 0.0), (5.6, 11.0), (0.0, 13.2), (-5.6, 11.0)], [(-4.4, 0.0), (4.4, 0.0), (4.4, 10.6), (0.0, 12.4), (-4.4, 10.6)],
            ZB - 2.0, ZB - 0.88, BLUE2)
IG.box(-3.6, 3.6, 11.0, 11.5, ZB - 2.04, ZB - 2.0, "DDEEFA")
# прожекторы на потолке
for s in (-1, 1):
    for z in (-12.0, 4.0):
        IS.box(s * 9.0 - 1.6, s * 9.0 + 1.6, C - 1.6, C - 0.8, z - 0.5, z + 0.5, DARK)
        for i in range(3):
            IG.box(s * 9.0 - 1.4 + 1.0 * i, s * 9.0 - 0.6 + 1.0 * i, C - 1.64, C - 1.6, z - 0.35, z + 0.35, LAMP)
# постамент: газон, белое кольцо, синяя подсветка
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, 0.55, DARK)
IG.prism_xz(K.ngon(px, pz, 4.05, 16), 0.3, 0.4, "4A8AF0")
IS.prism_xz(K.ngon(px, pz, 3.9, 16), 0.55, TOP - 0.06, WHITE)
IS.prism_xz(K.ngon(px, pz, 3.6, 16), TOP - 0.06, TOP, GRASS2)
B.lift_leaves(IS, STEEL2, BLUE)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 12.0, -FZ, FZ, CONC)
SL.box(-FX - 0.5, FX + 0.5, 12.0, 15.6, -FZ - 0.5, FZ + 0.5, BLUE)
SL.box(-FX, FX, 15.6, 17.0, -FZ, FZ, CONC2)
SL.box(-FX - 3.4, FX + 3.4, 17.0, 18.6, -FZ - 3.4, FZ + 3.4, WHITE)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "9C9C94")
for e in (-1, 1):
    SL.box(e * (FX + 0.9) - 2.0, e * (FX + 0.9) + 2.0, 16.2, 18.8, -FZ - 1.9, -FZ - 1.3, DARK)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 1900, (1.0, 1.0, 1.0)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.98, 0.95)),
                                                   ("Board", (0, 8, ZF + 5), 600, (1.0, 0.95, 0.8))])
