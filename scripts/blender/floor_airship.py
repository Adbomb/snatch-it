"""Этаж «Верблюд-туча» музея-небоскрёба (седьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — небесный причал дирижаблей в духе ар-деко. Снаружи — кремовый терминал со ступенчатыми бирюзовыми
пилонами, широкими лентами окон и латунными полосами; у правого переднего угла — решётчатая причальная мачта,
к которой носом пришвартован серебристый дирижабль с красной полосой, гондолой с окошками, хвостовым оперением и
винтами — он висит вдоль верхнего яруса фасада; по углам крыши и у основания — пухлые облака, на мачте — красно-
белый ветроуказатель, у входа — латунные фонари, чемоданы и указатель-пропеллер. Внутри — зал ожидания в облаках:
стены цвета неба с облаками, большие панорамные окна, палуба из досок, латунные поручни, кресла с багажом, под
потолком — модели дирижаблей и облака, глобус на подставке, табло с рейсами; экспонат — на белом облаке-постаменте
с латунной каймой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_airship.py -- <репо> <превью>
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

CREAM, CREAM2, TEAL, TEAL2, SKY, SKY2 = "F0E6D0", "DCCFB4", "2E8A9A", "246E7A", "8AC8F0", "B8DEF6"
CLOUD, CLOUD2, HULL, HULL2, STRIPE, BRASS = "F6F8FC", "DCE4EE", "C8CED8", "A8B0BC", "D84A3A", "C8982E"
WOOD, WOOD2, LEATHER, GLASS = "A87A48", "8A6236", "8A3A2A", "CFE8F8"

F = B.Floor("ZP", "CloudCamel", quiet=(SKY, "B0A890", WOOD), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def cloud(p, x, y, z, s=1.0, seed=0):
    """Пухлое облако из гранёных комков (низ плоский)."""
    for k in range(5):
        dx = (k - 2) * 0.9 * s
        r = (1.0 + 0.5 * (1 - abs(k - 2) / 2) + 0.25 * rng(seed, k)) * s
        p.prism_xz(K.octa(x + dx, z + 0.2 * s * (k % 2), r, r * 0.8, r * 0.38), y, y + r * 1.1, CLOUD if k % 2 else CLOUD2)
    p.prism_xz(K.octa(x - 0.3 * s, z, 1.2 * s, 0.9 * s, 0.4 * s), y + 1.0 * s, y + 2.0 * s, CLOUD)


def airship(p, g, x0, x1, yc, zc, r):
    """Дирижабль вдоль x носом к x0: корпус из колец (сечения-восьмиугольники), полоса, гондола, оперение у x1, винты."""
    q = r / 1.9
    n = 9
    rings = []
    for k in range(n + 1):
        t = k / n
        rr = r * math.sqrt(max(0.02, 1 - (2 * t - 1) ** 2)) ** 0.8
        x = x0 + (x1 - x0) * t
        rings.append([(x, yc + rr * math.sin(a), zc + rr * math.cos(a)) for a in [2 * math.pi * (i + 0.5) / 8 for i in range(8)]])
    for k, (a, b) in enumerate(zip(rings, rings[1:])):
        p.loft(a, b, HULL if k % 2 else HULL2)
    p.box(x0 + 1.4 * q, x1 - 1.4 * q, yc - 0.18 * q, yc + 0.18 * q, zc - r * 0.98 - 0.05, zc + r * 0.98 + 0.05, STRIPE)
    gx = x0 + (x1 - x0) * 0.42  # гондола ближе к носу
    p.box(gx - 2.4 * q, gx + 2.4 * q, yc - r - 1.1 * q, yc - r + 0.1, zc - 0.7 * q, zc + 0.7 * q, CREAM)
    p.box(gx - 2.5 * q, gx + 2.5 * q, yc - r - 1.2 * q, yc - r - 1.0 * q, zc - 0.75 * q, zc + 0.75 * q, TEAL2)
    for k in range(5):
        g.box(gx + (-2.0 + 0.85 * k) * q, gx + (-1.5 + 0.85 * k) * q, yc - r - 0.75 * q, yc - r - 0.3 * q, zc - 0.74 * q, zc - 0.7 * q, "FFE8B0")
    for e in (-1, 1):  # оперение у хвоста (x1)
        p.prism_xy([(x1 - 0.4 * q, yc), (x1 - 2.6 * q, yc), (x1 - 0.2 * q, yc + e * (r + 1.2 * q))], zc - 0.08, zc + 0.08, STRIPE)
        p.prism_xz([(x1 - 0.4 * q, zc), (x1 - 2.6 * q, zc), (x1 - 0.2 * q, zc + e * (r + 1.2 * q))], yc - 0.08, yc + 0.08, STRIPE)
    for e in (-1, 1):  # винты на штангах за гондолой
        bx, bz = gx + 3.0 * q, zc + e * (r * 0.6 + 0.6 * q)
        beam(p, (gx + 2.2 * q, yc - r - 0.3 * q, zc + e * 0.6 * q), (bx, yc - r - 0.3 * q, bz), 0.15 * q, 0.15 * q, HULL2)
        p.prism_zy(K.ngon(bz, yc - r - 0.3 * q, 0.3 * q, 8), bx - 0.5 * q, bx + 0.3 * q, HULL2)
        for a in (0.3, 0.3 + math.pi):
            p.prism_zy([(bz, yc - r - 0.3 * q), (bz + 0.9 * q * math.cos(a) - 0.1 * q, yc - r - 0.3 * q + 0.9 * q * math.sin(a)),
                        (bz + 0.9 * q * math.cos(a) + 0.1 * q, yc - r - 0.3 * q + 0.9 * q * math.sin(a))], bx + 0.3 * q, bx + 0.38 * q, WOOD2)


def suitcase(p, x, z, y, w, h, col):
    """Чемодан с ручкой и ремнём."""
    p.box(x - w / 2, x + w / 2, y, y + h, z - 0.35, z + 0.35, col)
    p.box(x - w / 2 - 0.02, x + w / 2 + 0.02, y + h * 0.45, y + h * 0.55, z - 0.37, z + 0.37, WOOD2)
    p.box(x - 0.25, x + 0.25, y + h, y + h + 0.2, z - 0.06, z + 0.06, WOOD2)


# ══ ФАСАД: терминал ═══════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, CREAM, SKY2, "2A4A6A")
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "B0A890")
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.2, TEAL2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.2, 17.4, CREAM)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, 17.4, 18.9, CREAM2)
    slab(FS, axis, fixed, out, 1.42, -half - 0.3, half + 0.3, 17.4, 17.6, BRASS)
    for y0, y1 in ((3.2, 6.8), (9.6, 12.2)):  # ленты окон
        slab(FG, axis, fixed, out, 0.92, -half + 1.6, half - 1.6, y0, y1, GLASS)
        slab(FS, axis, fixed, out, 1.2, -half + 1.4, half - 1.4, y0 - 0.3, y0, TEAL)
        slab(FS, axis, fixed, out, 1.1, -half + 1.4, half - 1.4, y1, y1 + 0.2, BRASS)
        for k in range(int((2 * half - 3.2) // 2.4) + 1):
            a = -half + 1.6 + 2.4 * k
            slab(FS, axis, fixed, out, 1.0, a - 0.07, a + 0.07, y0, y1, TEAL2)
    for a in (-half, half - 1.6):  # ступенчатые пилоны по углам
        slab(FR, axis, fixed, out, 1.38, a, a + 1.6, 1.2, 17.4, TEAL)
        slab(FR, axis, fixed, out, 1.88, a + 0.3, a + 1.3, 1.2, 15.0, TEAL2)
        slab(FR, axis, fixed, out, 2.28, a + 0.5, a + 1.1, 1.2, 12.0, TEAL)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# вход: ступенчатый портал ар-деко
for k, (w, d) in enumerate(((4.6, 1.2), (4.0, 1.6), (3.4, 2.0))):
    FR.box(-w, w, 1.2, 9.0 + 0.8 * k, -FZ - d, -FZ - 0.88, (TEAL, CREAM2, TEAL2)[k])
FG.box(-2.6, 2.6, 1.2, 7.6, -FZ - 2.04, -FZ - 2.0, "FFE8B0")
FS.frame_xy(K.rect(-3.0, 3.0, 1.2, 8.0), K.rect(-2.6, 2.6, 1.2, 7.6), -FZ - 2.2, -FZ - 2.0, BRASS)
for k in range(5):  # солнечные лучи над дверью
    t = math.pi * (0.15 + 0.7 * k / 4)
    FS.prism_xy([(0.0, 8.2), (2.4 * math.cos(t - 0.08), 8.2 + 2.4 * math.sin(t - 0.08)), (2.4 * math.cos(t + 0.08), 8.2 + 2.4 * math.sin(t + 0.08))],
                -FZ - 1.3, -FZ - 1.2, BRASS)
for k in range(3):
    FS.box(-4.0 + 0.4 * k, 4.0 - 0.4 * k, -0.1, 0.2 + 0.3 * k, -FZ - 2.88 + 0.3 * k, -FZ - 0.88, CREAM2)
# причальная мачта у правого (по фасаду −x) угла и дирижабль
MX, MZ = -15.4, -FZ - 1.8
for e in (-1, 1):
    for f in (-1, 1):
        beam(FS, (MX + e * 1.0, -0.1, MZ + f * 0.8), (MX + e * 0.35, 18.4, MZ + f * 0.3), 0.18, 0.18, HULL2)
for k in range(7):
    y = 1.5 + 2.4 * k
    w = 1.0 - 0.65 * y / 18.5
    FS.box(MX - w, MX + w, y, y + 0.14, MZ - 0.1, MZ + 0.1, HULL2)
    beam(FS, (MX - w, y, MZ), (MX + w * 0.95, y + 2.3, MZ), 0.1, 0.1, HULL2)
FS.prism_xz(K.ngon(MX, MZ, 0.6, 8), 18.2, 18.6, STRIPE)
for k in range(4):  # ветроуказатель
    t0, t1 = k / 4, (k + 1) / 4
    taper(FS, (MX + 0.4 + 2.4 * t0, 18.3 - 0.4 * t0, MZ), (MX + 0.4 + 2.4 * t1, 18.3 - 0.4 * t1, MZ), 0.7 - 0.35 * t0, 0.7 - 0.35 * t1,
          STRIPE if k % 2 == 0 else "F4F4F4")
F.objects(True)
airship(FS, FG, -12.6, 13.2, 14.6, -FZ - 2.3, 1.9)
beam(FS, (-12.6, 14.6, -FZ - 2.3), (MX + 0.4, 15.6, MZ), 0.12, 0.12, WOOD2)
F.objects(False)
# облака по углам и у основания
F.objects(True)
cloud(FS, 15.6, -0.1, -FZ - 1.9, s=0.9, seed=1)
cloud(FS, 6.6, -0.1, -FZ - 2.0, s=0.7, seed=2)
cloud(FS, -FX - 0.6, 15.4, -4.0, s=0.6, seed=3)
cloud(FS, FX + 0.6, 15.4, 6.0, s=0.6, seed=4)
cloud(FS, 6.0, 15.4, FZ + 0.6, s=0.6, seed=5)
F.objects(False)
# фонари и багаж у входа, указатель-пропеллер
F.objects(True)
for e in (-1, 1):
    FS.prism_xz(K.ngon(e * 5.6, -FZ - 2.2, 0.15, 6), -0.1, 3.6, BRASS)
    D.lantern(FS, FG, e * 5.6, 3.6, -FZ - 2.2, s=0.9, cap=BRASS, light="FFE8B0")
for k, (x, w, h, col) in enumerate(((8.6, 1.4, 1.0, LEATHER), (8.7, 1.1, 0.8, TEAL2), (10.4, 1.2, 1.4, "C8A050"))):
    suitcase(FS, x, -FZ - 2.2, -0.1 + (1.0 if k == 1 else 0.0), w, h, col)
PX = 12.6
FS.prism_xz(K.ngon(PX, -FZ - 2.2, 0.12, 6), -0.1, 4.0, WOOD2)
for k in range(3):
    t = 2 * math.pi * k / 3 + 0.4
    FS.prism_zy([(-FZ - 2.3, 4.0), (-FZ - 2.3 + 1.2 * math.cos(t - 0.15), 4.0 + 1.2 * math.sin(t - 0.15)),
                 (-FZ - 2.3 + 1.2 * math.cos(t + 0.15), 4.0 + 1.2 * math.sin(t + 0.15))], PX - 0.06, PX + 0.06, WOOD)
FS.prism_zy(K.ngon(-FZ - 2.3, 4.0, 0.25, 8), PX - 0.15, PX + 0.15, BRASS)
F.objects(False)

# ══ ИНТЕРЬЕР: зал ожидания в облаках ══════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), WOOD)
for k in range(-13, 14):  # доски палубы
    if k % 2:
        IQ.box(1.2 * k, 1.2 * k + 1.2, 0.02, 0.04, ZF + 0.9, ZB - 0.9, WOOD2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, SKY)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 2.4, CREAM)
        slab(IS, axis, fixed, out, 1.05, a0, a1, 2.4, 2.6, BRASS)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, SKY)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, TEAL)
    slab(IR, axis, fixed, out, 1.4, -half, half, 16.4, 17.2, CREAM)
    slab(IS, axis, fixed, out, 1.45, -half, half, 16.2, 16.4, BRASS)
    if idx < 2:  # панорамные окна
        for a in (-9.0, 1.0):
            d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
            IG.prism_zy(K.rect(a - 3.4, a + 3.4, 4.0, 12.6), d0, d1, SKY2)
            IS.frame_zy(K.rect(a - 3.8, a + 3.8, 3.6, 13.0), K.rect(a - 3.4, a + 3.4, 4.0, 12.6), *sorted((fixed + out * 0.88, fixed + out * 1.2)), TEAL)
            for i in (-1.15, 1.15):
                IS.box(*sorted((fixed + out * 0.9, fixed + out * 1.0)), 4.0, 12.6, a + i - 0.08, a + i + 0.08, TEAL)
            IS.box(*sorted((fixed + out * 0.9, fixed + out * 1.0)), 8.2, 8.36, a - 3.4, a + 3.4, TEAL)
            for k in range(2):  # облака за стеклом
                IS.prism_zy(K.octa(a - 1.6 + 3.0 * k, 6.0 + 3.0 * k, 1.2, 0.6, 0.3), *sorted((fixed + out * 0.92, fixed + out * 0.95)), CLOUD)
for k in range(-3, 4):
    IS.box(-W, W, C - 0.6, C - 0.2, 4.4 * k - 0.2, 4.4 * k + 0.2, CREAM2)
# дальняя стена: табло рейсов и большое облако
IS.box(-6.0, 6.0, 10.0, 14.0, ZF + 0.88, ZF + 1.2, "1E2A3A")
IS.frame_xy(K.rect(-6.3, 6.3, 9.7, 14.3), K.rect(-6.0, 6.0, 10.0, 14.0), ZF + 0.88, ZF + 1.4, BRASS)
for k in range(4):
    IG.box(-5.4, -0.6, 10.5 + 0.9 * k, 11.0 + 0.9 * k, ZF + 1.2, ZF + 1.24, "F0C020")
    IG.box(0.2, 2.6, 10.5 + 0.9 * k, 11.0 + 0.9 * k, ZF + 1.2, ZF + 1.24, "F4F4F4")
    IG.box(3.2, 5.4, 10.5 + 0.9 * k, 11.0 + 0.9 * k, ZF + 1.2, ZF + 1.24, "5AE07A" if k % 2 else "F0C020")
for k, (x, y) in enumerate(((-11.0, 6.0), (10.4, 5.0), (-4.0, 4.4), (5.0, 7.4))):
    IS.prism_xy(K.octa(x, y, 2.2, 0.9, 0.5), ZF + 0.88, ZF + 1.1, CLOUD)
    IS.prism_xy(K.octa(x - 0.6, y + 0.8, 1.2, 0.7, 0.3), ZF + 0.88, ZF + 1.1, CLOUD)
# латунные поручни вокруг постамента (со стороны лифта открыто), кресла с багажом, глобус
px, pz = PED
F.objects(True)
for k in range(9):
    t = math.pi * (1.15 + 0.7 * k / 8)
    x, z = px + 5.6 * math.cos(t), pz + 5.6 * math.sin(t)
    IS.prism_xz(K.ngon(x, z, 0.1, 6), 0.0, 2.2, BRASS)
for k in range(8):
    t0, t1 = math.pi * (1.15 + 0.7 * k / 8), math.pi * (1.15 + 0.7 * (k + 1) / 8)
    beam(IS, (px + 5.6 * math.cos(t0), 2.2, pz + 5.6 * math.sin(t0)), (px + 5.6 * math.cos(t1), 2.2, pz + 5.6 * math.sin(t1)), 0.14, 0.14, BRASS)
for s in (-1, 1):
    for z in (-9.0, -4.0, 1.0):
        x = s * (W - 3.8)
        IS.box(x - 0.9, x + 0.9, 0.0, 1.1, z - 0.9, z + 0.9, LEATHER)
        IS.box(*sorted((x + s * 0.6, x + s * 0.9)), 1.1, 2.6, z - 0.9, z + 0.9, LEATHER)
        for e in (-1, 1):
            IS.box(x - 0.9, x + 0.9, 1.1, 1.6, z + e * 0.9 - 0.2, z + e * 0.9 + 0.2, LEATHER)
    suitcase(IS, s * (W - 6.4), 3.0, 0.0, 1.3, 1.0, (TEAL2, "C8A050")[(s + 1) // 2])
    suitcase(IS, s * (W - 6.4), 3.0, 1.0, 1.0, 0.7, LEATHER)
GX, GZ = 10.0, -12.0
IS.prism_xz(K.ngon(GX, GZ, 0.9, 8), 0.0, 0.3, WOOD2)
IS.prism_xz(K.ngon(GX, GZ, 0.15, 6), 0.3, 2.4, BRASS)
for k in range(6):  # глобус: шар из ярусов, материк, латунный меридиан
    a0, a1 = math.pi * (-0.5 + k / 6), math.pi * (-0.5 + (k + 1) / 6)
    IS.prism_xz(K.ngon(GX, GZ, 1.15 * math.cos((a0 + a1) / 2), 12), 3.6 + 1.15 * math.sin(a0), 3.6 + 1.15 * math.sin(a1), "3A7AC8")
IS.prism_xz(K.octa(GX + 0.5, GZ - 0.6, 0.45, 0.4, 0.15), 3.2, 4.2, "5AB04A")
IS.frame_xy(K.ngon(GX, 3.6, 1.35, 12), K.ngon(GX, 3.6, 1.22, 12), GZ - 0.06, GZ + 0.06, BRASS)
F.objects(False)
# модели дирижаблей и облака под потолком
F.objects(True)
for x, z, s_ in ((-7.0, -10.0, 1.0), (7.0, -6.0, 0.8)):
    airship(IS, IG, x - 3.0 * s_, x + 3.0 * s_, 13.4, z, 0.9 * s_)
    IS.box(x - 0.03, x + 0.03, 14.3, C - 0.6, z - 0.03, z + 0.03, BRASS)
for x, z in ((8.0, -10.0), (-8.0, 4.0), (0.0, 9.0)):
    cloud(IS, x, 13.6, z, s=0.8, seed=int(x + z))
F.objects(False)
# белое облако-постамент с латунной каймой
IR.prism_xz(K.ngon(px, pz, 3.9, 16), 0.0, 0.5, CLOUD2)
IS.prism_xz(K.ngon(px, pz, 4.0, 16), 0.5, 0.62, BRASS)
IS.prism_xz(K.ngon(px, pz, 3.7, 16), 0.62, TOP - 0.1, CLOUD)
IS.prism_xz(K.ngon(px, pz, 3.8, 16), TOP - 0.1, TOP, CLOUD2)
for k in range(8):
    t = 2 * math.pi * (k + 0.5) / 8
    IS.prism_xz(K.octa(px + 3.9 * math.cos(t), pz + 3.9 * math.sin(t), 0.9, 0.9, 0.35), 0.0, 0.9, CLOUD)
B.lift_leaves(IS, TEAL2, BRASS)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, CREAM)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "B0A890")
SL.box(-FX - 0.3, FX + 0.3, 17.4, 18.9, -FZ - 0.3, FZ + 0.3, CREAM2)
SL.box(-12.6, 13.2, 12.9, 16.3, -FZ - 4.0, -FZ - 0.6, HULL)
SL.box(MX - 1.0, MX + 1.0, -0.1, 18.6, MZ - 0.8, MZ + 0.8, HULL2)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 1900, (1.0, 0.98, 0.95)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Sky", (0, 9, ZF + 5), 700, (0.85, 0.92, 1.0))])
