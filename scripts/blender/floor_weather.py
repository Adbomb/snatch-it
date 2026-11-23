"""Этаж «Смерч-озорник» музея-небоскрёба (седьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — штормовая метеостанция. Снаружи — белые панели с красными поясами и угловыми стойками; на правом
переднем углу — радарный купол на решётчатой опоре, на левом — мачта с чашечным анемометром, флюгером-стрелкой и
красно-белым ветроуказателем; посередине — двойная дверь под козырьком и широкое окно диспетчерской с экранами;
перед станцией — белая метеобудка с жалюзи на ножках, дождемеры, спутниковая тарелка, шар-зонд на тросе и
перекати-поле; на боках — солнечные панели и окна-ленты. Внутри — центр наблюдения за смерчами: пульты с
мониторами, на дальней стене — большая карта погоды с вихрями и мигающими отметками, по стенам — барометры и
термометры, глобус, под потолком — кольцевой вентилятор-«генератор смерча» с лопастями прямо над постаментом,
вокруг постамента на полу — разметка вихря; экспонат — на круглой решётке-вентиляции в три кольца с подсветкой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_weather.py -- <репо> <превью>
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

WHITE, WHITE2, RED, RED2, GREY, GREY2 = "F2F2EE", "DCDCD6", "D83A34", "B02A26", "8A9098", "6A7078"
NAVY, SCREEN, GREENS, YEL, SOLAR, GLASS = "243246", "3AD0F0", "5AE07A", "F0C020", "2A3A6A", "BFD8EA"
GROUND, TUMBLE = "C8B890", "A8884A"

F = B.Floor("WX", "DustDevil", quiet=(GROUND, GREY2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def dome(p, x, y, z, r, col, n=3):
    """Купол из ярусов-многоугольников (сфера ступенями) с нижним кольцом."""
    for k in range(n * 2):  # ярусы от экватора к макушке: радиус по середине яруса — купол круглится
        a0, a1 = math.pi / 2 * k / (n * 2), math.pi / 2 * (k + 1) / (n * 2)
        rr = r * math.cos((a0 + a1) / 2)
        p.prism_xz(K.ngon(x, z, rr, 12), y + r * math.sin(a0), y + r * math.sin(a1), col)
    p.prism_xz(K.ngon(x, z, r * 1.02, 12), y - 0.5, y, col)


def anemometer(p, x, y, z):
    """Чашечный анемометр: ось, три спицы с чашками."""
    p.prism_xz(K.ngon(x, z, 0.12, 6), y, y + 0.8, GREY2)
    for k in range(3):
        t = 2 * math.pi * k / 3
        ex, ez = x + 1.0 * math.cos(t), z + 1.0 * math.sin(t)
        beam(p, (x, y + 0.7, z), (ex, y + 0.7, ez), 0.08, 0.08, GREY2)
        p.prism_xz(K.octa(ex, ez, 0.3, 0.3, 0.1), y + 0.45, y + 0.95, RED)


def windsock(p, x, y, z, length=3.0, dz=1.0):
    """Красно-белый ветроуказатель из сужающихся колец."""
    for k in range(4):
        t0, t1 = k / 4, (k + 1) / 4
        taper(p, (x + length * t0, y - 0.35 * t0, z + dz * t0), (x + length * t1, y - 0.35 * t1, z + dz * t1),
              0.9 - 0.4 * t0, 0.9 - 0.4 * t1, RED if k % 2 == 0 else WHITE)


def stevenson(p, x, z, y=0.0):
    """Метеобудка: белый ящик с жалюзи на четырёх ножках, крыша-скат."""
    for e in (-1, 1):
        for f in (-1, 1):
            p.box(x + e * 0.8 - 0.08, x + e * 0.8 + 0.08, y, y + 2.0, z + f * 0.6 - 0.08, z + f * 0.6 + 0.08, WHITE2)
    p.box(x - 1.0, x + 1.0, y + 2.0, y + 3.6, z - 0.8, z + 0.8, WHITE)
    for k in range(5):
        yy = y + 2.2 + 0.28 * k
        p.box(x - 0.9, x + 0.9, yy, yy + 0.08, z - 0.84, z - 0.8, GREY)
    p.prism_xy([(x - 1.2, y + 3.6), (x + 1.2, y + 3.6), (x + 1.2, y + 3.8), (x, y + 4.2), (x - 1.2, y + 3.8)], z - 1.0, z + 1.0, WHITE2)


def tumbleweed(p, x, z, y, r):
    """Перекати-поле: три пересечённых гранёных кольца."""
    ring_y(p, x, z, r * 0.8, r, y + r - 0.1, y + r + 0.1, TUMBLE, n=8)
    p.frame_xy(K.ngon(x, y + r, r, 8), K.ngon(x, y + r, r * 0.8, 8), z - 0.1, z + 0.1, TUMBLE)
    p.frame_zy(K.ngon(z, y + r, r, 8), K.ngon(z, y + r, r * 0.8, 8), x - 0.1, x + 0.1, TUMBLE)


def vortex(p, cx, cz, y, r0, r1, arms=3, col="9AD8F0", turns=0.6):
    """Разметка вихря на полу: спиральные рукава из коротких брусков."""
    for a in range(arms):
        pts = []
        for k in range(10):
            t = k / 9
            ang = 2 * math.pi * (a / arms + turns * t)
            rr = r0 + (r1 - r0) * t
            pts.append((cx + rr * math.cos(ang), y, cz + rr * math.sin(ang)))
        for q0, q1 in zip(pts, pts[1:]):
            p.prism_xz([(q0[0] - 0.12, q0[2] - 0.12), (q1[0] - 0.12, q1[2] - 0.12), (q1[0] + 0.12, q1[2] + 0.12),
                        (q0[0] + 0.12, q0[2] + 0.12)], y, y + 0.03, col)


# ══ ФАСАД: метеостанция ═══════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, WHITE, WHITE, NAVY)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, GROUND)
    slab(FR, axis, fixed, out, 1.18, -half - 0.2, half + 0.2, -0.1, 1.0, GREY2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.0, 17.6, WHITE)
    for y0 in (8.6, 16.2):
        slab(FR, axis, fixed, out, 1.28, -half - 0.2, half + 0.2, y0, y0 + 0.9, RED)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, 17.6, 18.9, GREY)
    for a in (-half, half - 1.2):
        slab(FR, axis, fixed, out, 1.18, a, a + 1.2, 1.0, 17.6, GREY)
    for k in range(int(2 * half // 3.0)):  # швы панелей
        a = -half + 1.2 + 3.0 * k
        slab(FS, axis, fixed, out, 0.94, a - 0.06, a + 0.06, 1.0, 16.2, WHITE2)
    if fi > 0:  # бока и тыл: окна-ленты и солнечные панели
        slab(FG, axis, fixed, out, 0.92, -half + 2.0, half - 2.0, 11.2, 13.6, GLASS)
        slab(FS, axis, fixed, out, 1.15, -half + 1.8, half - 1.8, 10.9, 11.2, GREY2)
        for k in range(4):
            a = -half + 3.0 + (2 * half - 6.0) * k / 3
            prof = [(fixed + out * 0.9, 3.0), (fixed + out * 2.2, 3.0), (fixed + out * 0.9, 7.4)]
            if axis == "x":
                FS.prism_xy(prof, a - 2.6, a + 2.6, SOLAR)
            else:
                FS.prism_zy(prof, a - 2.6, a + 2.6, SOLAR)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# двойная дверь под козырьком, окно диспетчерской с экранами
FS.box(-2.4, 2.4, 1.0, 7.2, -FZ - 0.96, -FZ - 0.88, NAVY)
for e in (-1, 1):
    FS.box(e * 0.08, e * 2.2, 1.0, 7.0, -FZ - 1.04, -FZ - 0.96, GREY)
    FG.box(e * 0.5, e * 1.8, 4.0, 6.4, -FZ - 1.08, -FZ - 1.04, GLASS)
FS.box(-3.6, 3.6, 7.6, 8.0, -FZ - 3.0, -FZ - 0.88, RED2)
for e in (-1, 1):
    beam(FS, (e * 3.2, 8.0, -FZ - 2.9), (e * 3.2, 10.4, -FZ - 0.9), 0.14, 0.14, GREY2)
FG.box(-9.0, 9.0, 10.4, 15.4, -FZ - 0.94, -FZ - 0.9, "2A4A6A")
FS.frame_xy(K.rect(-9.4, 9.4, 10.0, 15.8), K.rect(-9.0, 9.0, 10.4, 15.4), -FZ - 1.3, -FZ - 0.88, GREY)
for x in (-3.0, 3.0):
    FS.box(x - 0.1, x + 0.1, 10.4, 15.4, -FZ - 1.0, -FZ - 0.94, GREY)
for k, (x0, col) in enumerate(((-8.4, SCREEN), (-2.4, GREENS), (3.6, SCREEN))):  # экраны за стеклом: графики-полосы
    for j in range(4):
        ln = 1.4 + 3.0 * rng(k, j)
        FG.box(x0 + 0.3, x0 + 0.3 + ln, 11.2 + 0.7 * j, 11.6 + 0.7 * j, -FZ - 0.96, -FZ - 0.94, col)
# радарный купол на решётчатой опоре (правый угол по фасаду −x)
RX, RZ = -14.2, -FZ - 1.8
F.objects(True)
for e in (-1, 1):
    for f in (-1, 1):
        beam(FS, (RX + e * 1.6, -0.1, RZ + f * 0.9), (RX + e * 1.0, 13.4, RZ + f * 0.6), 0.2, 0.2, GREY2)
for k in range(5):
    y = 1.6 + 2.4 * k
    FS.box(RX - 1.5 + 0.1 * k, RX + 1.5 - 0.1 * k, y, y + 0.14, RZ - 0.1, RZ + 0.1, GREY2)
FS.box(RX - 2.2, RX + 2.2, 13.4, 13.8, RZ - 1.0, RZ + 1.0, GREY)
dome(FS, RX, 14.3, RZ, 2.6, WHITE, n=3)
FS.prism_xz(K.ngon(RX, RZ, 0.3, 8), 16.85, 17.35, RED)
F.objects(False)
# мачта: анемометр, флюгер-стрелка, ветроуказатель (левый угол по фасаду +x)
MX, MZ = 15.0, -FZ - 1.9
F.objects(True)
FS.prism_xz(K.ngon(MX, MZ, 0.2, 8), -0.1, 17.2, GREY2)
for k in range(3):
    beam(FS, (MX, 6.0 + 4.0 * k, MZ), (MX - 1.2, 6.0 + 4.0 * k - 1.6, MZ + 0.9), 0.1, 0.1, GREY2)
anemometer(FS, MX, 17.2, MZ)
FS.box(MX - 1.6, MX + 1.6, 15.0, 15.12, MZ - 0.06, MZ + 0.06, NAVY)
FS.prism_xy([(MX + 1.6, 14.7), (MX + 2.3, 15.06), (MX + 1.6, 15.4)], MZ - 0.06, MZ + 0.06, RED)
FS.prism_xy([(MX - 1.6, 14.7), (MX - 2.1, 14.7), (MX - 1.8, 15.06), (MX - 2.1, 15.4), (MX - 1.6, 15.4)], MZ - 0.06, MZ + 0.06, NAVY)
windsock(FS, MX - 0.2, 12.4, MZ, length=-3.2, dz=-0.6)
F.objects(False)
# перед станцией: метеобудка, дождемеры, тарелка, шар-зонд, перекати-поле
F.objects(True)
stevenson(FS, -18.4, -FZ - 1.9, y=-0.1)
for x in (-3.2, -3.8):
    FS.prism_xz(K.ngon(x, -FZ - 2.3, 0.25, 8), -0.1, 1.2, GREY)
    FS.prism_xz(K.ngon(x, -FZ - 2.3, 0.3, 8), 1.2, 1.3, NAVY)
DX, DZ = -8.6, -FZ - 1.9
FS.prism_xz(K.ngon(DX, DZ, 0.6, 8), -0.1, 0.4, GREY2)
FS.prism_xz(K.ngon(DX, DZ, 0.18, 6), 0.4, 2.4, GREY2)
FS.cone([(x, 3.4, z) for x, z in K.ngon(DX, DZ - 0.3, 1.4, 12)], (DX, 2.4, DZ + 0.2), WHITE)  # тарелка чашей вверх
beam(FS, (DX, 2.6, DZ + 0.1), (DX, 3.8, DZ - 0.8), 0.08, 0.08, GREY2)
BX, BZ = -4.6, -FZ - 2.4
FS.box(BX - 0.03, BX + 0.03, -0.1, 10.0, BZ - 0.03, BZ + 0.03, GREY2)
FS.prism_xz(K.octa(BX, BZ, 0.9, 0.9, 0.35), 10.0, 11.8, WHITE)
FS.prism_xz(K.octa(BX, BZ, 0.5, 0.5, 0.2), 11.8, 12.3, WHITE)
FS.box(BX - 0.25, BX + 0.25, 9.4, 10.0, BZ - 0.25, BZ + 0.25, RED)
for k in range(7):  # маленький пылевой вихрь: кольца песка расширяются кверху, в нём кружится перекати-поле
    r0 = 0.3 + 0.22 * k
    ring_y(FS, 12.2 + 0.15 * math.sin(k * 1.3), -FZ - 1.9 + 0.12 * math.cos(k * 1.3), r0, r0 + 0.22, 0.1 + 0.75 * k, 0.4 + 0.75 * k,
           ("E8D4A0", "D8BC80")[k % 2], n=10, a0=40.0 * k, a1=40.0 * k + 250.0)
tumbleweed(FS, 12.6, -FZ - 2.0, 2.4, 0.55)
F.objects(False)
# гараж и фургон охотников за смерчами (боком), сирена оповещения над окном
FS.box(3.6, 11.6, 1.0, 6.6, -FZ - 0.96, -FZ - 0.88, GREY2)
for k in range(6):
    FS.box(3.8, 11.4, 1.2 + 0.9 * k, 1.9 + 0.9 * k, -FZ - 1.02, -FZ - 0.96, GREY)
FS.frame_xy(K.rect(3.4, 11.8, 1.0, 6.9), K.rect(3.6, 11.6, 1.0, 6.6), -FZ - 1.2, -FZ - 0.88, RED2)
F.objects(True)
VX0, VX1, VZ = 4.2, 11.0, -FZ - 2.0
FS.box(VX0, VX1, 0.7, 3.4, VZ - 0.85, VZ + 0.85, WHITE)
FS.box(VX0, VX1, 1.6, 1.9, VZ - 0.88, VZ + 0.88, RED)
FG.box(VX0 + 0.2, VX0 + 1.6, 2.3, 3.1, VZ - 0.89, VZ - 0.86, GLASS)
FG.box(VX0 + 2.4, VX1 - 0.6, 2.3, 3.1, VZ - 0.89, VZ - 0.86, "2A4A6A")
for wx in (VX0 + 1.3, VX1 - 1.3):
    FS.prism_xy(K.ngon(wx, 0.7, 0.65, 10), VZ - 0.95, VZ - 0.6, NAVY)
    FS.prism_xy(K.ngon(wx, 0.7, 0.65, 10), VZ + 0.6, VZ + 0.95, NAVY)
FS.box(VX0 + 3.0, VX0 + 5.4, 3.4, 3.6, VZ - 0.6, VZ + 0.6, GREY2)
dome(FS, VX0 + 4.2, 3.8, VZ, 0.8, WHITE, n=2)
FG.box(VX0 + 0.6, VX0 + 1.8, 3.4, 3.7, VZ - 0.5, VZ + 0.5, "FF8A20")
FS.box(-0.12, 0.12, 15.6, 18.6, -FZ - 1.6, -FZ - 1.36, GREY2)
for i in range(3):  # сирена: решётка из шести квадратных раструбов
    for j in range(2):
        x, y = -0.9 + 0.9 * i, 17.2 + 0.8 * j
        FS.box(x - 0.38, x + 0.38, y - 0.34, y + 0.34, -FZ - 1.9, -FZ - 1.5, YEL)
        FS.box(x - 0.22, x + 0.22, y - 0.18, y + 0.18, -FZ - 1.94, -FZ - 1.9, NAVY)
tumbleweed(FS, -11.6, -FZ - 2.2, -0.1, 0.55)
F.objects(False)

# ══ ИНТЕРЬЕР: центр наблюдения за смерчами ════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.1
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), GREY2)
for i in range(-6, 7):
    for j in range(-6, 7):
        if (i + j) % 2 == 0:
            x, z = 2.4 * i, 2.4 * j
            if abs(x) < W - 1.4 and ZF + 1.4 < z < ZB - 1.4 and math.hypot(x, z + 3.0) > 5.0:
                IQ.box(x - 1.2, x + 1.2, 0.02, 0.04, z - 1.2, z + 1.2, "7A8088")
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, WHITE)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 1.2, GREY)
        slab(IS, axis, fixed, out, 1.05, a0, a1, 1.2, 1.4, RED)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, WHITE)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, RED)
    slab(IR, axis, fixed, out, 1.4, -half, half, 15.8, 16.6, GREY)
    if idx < 2:  # окна-ленты
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
        IG.prism_zy(K.rect(-13.0, 9.0, 11.2, 13.6), d0, d1, GLASS)
        IS.frame_zy(K.rect(-13.3, 9.3, 10.9, 13.9), K.rect(-13.0, 9.0, 11.2, 13.6), *sorted((fixed + out * 0.88, fixed + out * 1.1)), GREY)
for k in range(-3, 4):
    IS.box(-W, W, C - 0.7, C - 0.2, 4.4 * k - 0.2, 4.4 * k + 0.2, GREY2)
# дальняя стена: большая карта погоды с вихрями
IS.box(-11.0, 11.0, 5.0, 14.6, ZF + 0.88, ZF + 1.1, NAVY)
IS.frame_xy(K.rect(-11.3, 11.3, 4.7, 14.9), K.rect(-11.0, 11.0, 5.0, 14.6), ZF + 0.88, ZF + 1.3, GREY)
SX, SY = -5.0, 10.0  # один большой ураган на карте: глаз и три спиральных рукава
IG.prism_xy(K.ngon(SX, SY, 0.45, 8), ZF + 1.1, ZF + 1.16, RED)
for a in range(3):
    pts = []
    for k in range(9):
        t = k / 8
        ang = 2 * math.pi * (a / 3 + 0.55 * t)
        rr = 0.6 + 3.0 * t
        pts.append((SX + rr * math.cos(ang), SY + rr * math.sin(ang) * 0.8))
    for k, ((ax, ay), (bx, by)) in enumerate(zip(pts, pts[1:])):
        w = 0.32 - 0.025 * k
        IG.prism_xy([(ax, ay - w), (bx, by - w), (bx, by + w), (ax, ay + w)], ZF + 1.1, ZF + 1.14, (RED, YEL, GREENS)[min(2, k // 3)])
IG.prism_xy([(-11.0, 5.0), (-4.0, 5.0), (-2.0, 7.0), (-6.0, 8.0), (-11.0, 7.4)], ZF + 1.1, ZF + 1.12, "2A6A4A")
IG.prism_xy([(3.0, 11.0), (11.0, 11.4), (11.0, 14.6), (6.0, 14.6), (4.0, 13.0)], ZF + 1.1, ZF + 1.12, "2A6A4A")
for k in range(6):
    IG.prism_xy(K.ngon(-9.0 + 3.2 * k, 6.0 + 1.3 * (k % 3), 0.22, 6), ZF + 1.14, ZF + 1.18, RED if k % 2 else YEL)
# пульты с мониторами по бокам
F.objects(True)
for s in (-1, 1):
    x = s * (W - 3.0)
    for z0 in (-13.4, -6.4):
        IS.box(x - 1.2, x + 1.2, 0.0, 2.6, z0, z0 + 5.6, GREY)
        IS.prism_zy([(z0, 2.6), (z0 + 5.6, 2.6), (z0 + 5.6, 3.0), (z0, 3.0)], x - 1.2, x + 1.2, NAVY)
        for k in range(2):
            zz = z0 + 0.4 + 2.6 * k
            IS.box(*sorted((x + s * 0.4, x + s * 0.7)), 3.0, 5.6, zz, zz + 2.4, NAVY)
            IG.box(*sorted((x + s * 0.4, x + s * 0.36)), 3.3, 5.3, zz + 0.2, zz + 2.2, (SCREEN, GREENS)[(k + int(z0)) % 2])
        for k in range(6):
            IG.box(*sorted((x - s * 0.8, x - s * 0.6)), 3.0, 3.06, z0 + 0.5 + 0.8 * k, z0 + 0.9 + 0.8 * k, (RED, YEL, GREENS)[k % 3])
GX, GZ = -11.0, 4.2
IS.prism_xz(K.ngon(GX, GZ, 0.9, 8), 0.0, 0.3, NAVY)
IS.prism_xz(K.ngon(GX, GZ, 0.15, 6), 0.3, 2.2, GREY2)
dome(IS, GX, 3.2, GZ, 1.1, "3A7AC8", n=2)  # глобус: шар из ярусов, материк, латунный меридиан
for k in range(4):
    a0, a1 = math.pi / 2 * k / 4, math.pi / 2 * (k + 1) / 4
    IS.prism_xz(K.ngon(GX, GZ, 1.1 * math.cos((a0 + a1) / 2), 12), 3.2 - 1.1 * math.sin(a1), 3.2 - 1.1 * math.sin(a0), "3A7AC8")
IS.prism_xz(K.octa(GX - 0.5, GZ + 0.6, 0.45, 0.4, 0.15), 2.9, 3.9, "5AB04A")
IS.frame_xy(K.ngon(GX, 3.2, 1.3, 12), K.ngon(GX, 3.2, 1.18, 12), GZ - 0.06, GZ + 0.06, "C8982E")
F.objects(False)
for s in (-1, 1):  # барометры и термометры
    x = s * (W - 0.88)
    d0, d1 = sorted((x, x - s * 0.3))
    IS.prism_zy(K.ngon(5.6, 8.2, 1.0, 12), d0, d1, "C8982E")
    IS.prism_zy(K.ngon(5.6, 8.2, 0.8, 12), *sorted((x - s * 0.3, x - s * 0.34)), WHITE)
    IS.box(*sorted((x - s * 0.34, x - s * 0.38)), 8.15, 8.25, 5.0, 5.6, NAVY)
    IS.box(*sorted((x, x - s * 0.25)), 3.0, 9.6, 8.6, 9.2, WHITE)
    IG.box(*sorted((x - s * 0.25, x - s * 0.3)), 3.4, 6.0 + 1.4 * (s > 0), 8.8, 9.0, RED)
# кольцевой вентилятор-«генератор смерча» над постаментом
px, pz = PED
F.objects(True)
ring_y(IS, px, pz, 3.4, 4.0, C - 3.6, C - 2.8, GREY, n=16)
for k in range(8):
    t = 2 * math.pi * k / 8
    IS.prism_xz([(px + 0.4 * math.cos(t), pz + 0.4 * math.sin(t)), (px + 3.4 * math.cos(t + 0.25), pz + 3.4 * math.sin(t + 0.25)),
                 (px + 3.4 * math.cos(t + 0.6), pz + 3.4 * math.sin(t + 0.6))], C - 3.3, C - 3.1, WHITE2)
IS.prism_xz(K.ngon(px, pz, 0.6, 8), C - 3.6, C - 2.6, RED)
for k in range(4):
    t = math.pi / 2 * k + math.pi / 4
    IS.box(px + 3.7 * math.cos(t) - 0.08, px + 3.7 * math.cos(t) + 0.08, C - 2.8, C - 0.7, pz + 3.7 * math.sin(t) - 0.08,
           pz + 3.7 * math.sin(t) + 0.08, GREY2)
F.objects(False)
ring_y(IG, px, pz, 3.6, 3.7, C - 3.7, C - 3.6, SCREEN, n=16)
vortex(IS, px, pz, 0.02, 4.6, 7.0, arms=3)
# постамент: круглая решётка-вентиляция в три кольца с подсветкой
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, 0.5, NAVY)
IG.prism_xz(K.ngon(px, pz, 4.05, 16), 0.3, 0.42, SCREEN)
IS.prism_xz(K.ngon(px, pz, 3.8, 16), 0.5, TOP - 0.08, GREY)
for r in (1.2, 2.2, 3.2):
    ring_y(IS, px, pz, r, r + 0.3, TOP - 0.08, TOP, WHITE2, n=16)
IS.prism_xz(K.ngon(px, pz, 0.9, 8), TOP - 0.08, TOP, WHITE2)
B.lift_leaves(IS, GREY, RED)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, WHITE)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, GROUND)
for y0 in (8.6, 16.2):
    SL.box(-FX - 0.3, FX + 0.3, y0, y0 + 0.9, -FZ - 0.3, FZ + 0.3, RED)
SL.prism_xz(K.ngon(RX, RZ, 2.5, 8), 13.4, 16.9, WHITE)
SL.box(RX - 1.6, RX + 1.6, -0.1, 13.4, RZ - 0.9, RZ + 0.9, GREY2)

F.build(exhibit=(PED[0], TOP, PED[1], 2.8), lamps=[("Hall", (0, 14, 6), 1800, (0.95, 0.97, 1.0)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Map", (0, 8, ZF + 5), 600, (0.6, 0.9, 1.0))])
