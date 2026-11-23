"""Этаж «Император трёх хвостов» музея-небоскрёба (седьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — восточный императорский дворец. Внизу — белая мраморная терраса с балюстрадой и широкой лестницей,
посередине лестницы — наклонная плита с золотым драконом; красные стены, портик из красных колонн, красные ворота с
золотыми гвоздями и кольцами; над стенами — пояс сине-зелёных кронштейнов с золотом и широкий навес из жёлтой
глазурованной черепицы с загнутыми вверх углами; второй ярус — красная стена с золотыми решётчатыми окнами и вторая
черепичная крыша; на террасе — бронзовые треножники-курильницы и каменные фонари, под навесом — красные фонари с
кистями. Внутри — тронный зал: тёмный пол с жёлтой дорожкой к помосту, два ряда красных колонн, обвитых золотыми
драконами, кессонный потолок в сине-зелёных и золотых клетках, красные стены с золотыми решётками окон, за помостом —
золотая ширма из пяти створок, по сторонам — бронзовые журавли и курильницы, под потолком — красные фонари;
экспонат — на белом мраморном помосте в три ступени с золотой каймой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_palace.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, ring_y, rng, slab, taper, tube  # noqa: E402

VERM, VERM2, GLAZE, GLAZE2, MARB, MARB2 = "B82A2A", "962024", "EBB52A", "C8901C", "EEEAE0", "D6D0C2"
JADE, BLUEP, GOLD, BRONZE, DARKS, CARPET = "2E8A6A", "2A4A9A", "E8C040", "8A6A3A", "4A4440", "E2B23A"

F = B.Floor("EP", "ThreeTailEmperor", quiet=(MARB2, CARPET, "5A524C"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def red_lantern(p, x, y, z, s=1.0):
    """Красный фонарь: золотые крышки, пухлый корпус, кисть."""
    p.prism_xz(K.ngon(x, z, 0.3 * s, 8), y + 1.0 * s, y + 1.15 * s, GOLD)
    p.prism_xz(K.ngon(x, z, 0.55 * s, 8), y + 0.8 * s, y + 1.0 * s, VERM)
    p.prism_xz(K.ngon(x, z, 0.7 * s, 8), y + 0.3 * s, y + 0.8 * s, "D83A30")
    p.prism_xz(K.ngon(x, z, 0.55 * s, 8), y + 0.1 * s, y + 0.3 * s, VERM)
    p.prism_xz(K.ngon(x, z, 0.3 * s, 8), y - 0.05 * s, y + 0.1 * s, GOLD)
    p.box(x - 0.08 * s, x + 0.08 * s, y - 0.7 * s, y - 0.05 * s, z - 0.08 * s, z + 0.08 * s, GOLD)


def ding(p, g, x, z, y=0.0, s=1.0):
    """Бронзовая курильница-треножник с ручками и дымком-огоньком."""
    for k in range(3):
        t = 2 * math.pi * k / 3 + 0.5
        p.box(x + 0.6 * s * math.cos(t) - 0.12, x + 0.6 * s * math.cos(t) + 0.12, y, y + 0.7 * s,
              z + 0.6 * s * math.sin(t) - 0.12, z + 0.6 * s * math.sin(t) + 0.12, BRONZE)
    p.prism_xz(K.ngon(x, z, 0.85 * s, 8), y + 0.7 * s, y + 1.5 * s, BRONZE)
    p.prism_xz(K.ngon(x, z, 0.95 * s, 8), y + 1.5 * s, y + 1.65 * s, GOLD)
    for e in (-1, 1):
        p.frame_zy(K.rect(z - 0.3 * s, z + 0.3 * s, y + 1.65 * s, y + 2.2 * s), K.rect(z - 0.18 * s, z + 0.18 * s, y + 1.65 * s, y + 2.08 * s),
                   x + e * 0.7 * s - 0.06, x + e * 0.7 * s + 0.06, BRONZE)
    g.prism_xz(K.ngon(x, z, 0.3 * s, 6), y + 1.65 * s, y + 1.9 * s, "FFB050")


def stone_lantern(p, g, x, z, y=0.0):
    """Каменный фонарь: основание, столб, светящаяся камера, крыша-шатёр."""
    p.prism_xz(K.ngon(x, z, 0.7, 6), y, y + 0.4, MARB2)
    p.prism_xz(K.ngon(x, z, 0.3, 6), y + 0.4, y + 2.0, MARB)
    p.prism_xz(K.ngon(x, z, 0.6, 6), y + 2.0, y + 2.2, MARB2)
    g.prism_xz(K.ngon(x, z, 0.42, 6), y + 2.2, y + 2.9, "FFD890")
    p.cone([(xx, y + 2.9, zz) for xx, zz in K.ngon(x, z, 0.85, 6)], (x, y + 3.6, z), MARB2)


def dragon_flat(p, x0, x1, yc, z0, z1, amp=0.6, n=12):
    """Золотой дракон-волна на плоскости (вид спереди): тело змейкой, гребень, голова-клин."""
    pts = [(x0 + (x1 - x0) * k / n, yc + amp * math.sin(2 * math.pi * 1.5 * k / n)) for k in range(n + 1)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        p.prism_xy([(ax, ay - 0.28), (bx, by - 0.28), (bx, by + 0.28), (ax, ay + 0.28)], z0, z1, GOLD)
        p.prism_xy([(ax + 0.1, ay + 0.28), (bx - 0.1, by + 0.28), ((ax + bx) / 2, (ay + by) / 2 + 0.6)], z0, z1, GLAZE2)
    hx, hy = pts[-1]
    p.prism_xy([(hx, hy - 0.5), (hx + 1.1, hy - 0.2), (hx + 1.1, hy + 0.3), (hx, hy + 0.6)], z0, z1, GOLD)
    p.prism_xy([(hx + 0.2, hy + 0.6), (hx + 0.5, hy + 1.2), (hx + 0.6, hy + 0.5)], z0, z1, GOLD)


def eave(p, axis, fixed, out, a0, a1, y_wall, y_edge, depth, col):
    """Черепичный навес: скат от стены (y_wall) к краю (y_edge, вынос depth), нижняя кромка темнее."""
    B.chamfer(p, axis, fixed, out, a0, a1, [(0.88, y_wall), (depth, y_edge), (depth, y_edge - 0.35), (0.88, y_wall - 1.0)], col)


# ══ ФАСАД: дворец ═════════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, VERM, VERM, DARKS)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, MARB2)
    for a0, a1 in (((-half - 2.88, -6.0), (6.0, half + 2.88)) if fi == 0 else ((-half - 2.88, half + 2.88),)):
        slab(FR, axis, fixed, out, 2.88, a0, a1, -0.1, 1.4, MARB)  # терраса (спереди — разрыв под лестницу)
        slab(FS, axis, fixed, out, 2.95, a0 - (0.07 if a0 < -half else 0), a1 + (0.07 if a1 > half else 0), 1.25, 1.45, MARB2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.4, 10.6, VERM)
    slab(FR, axis, fixed, out, 1.18, -half, half, 1.4, 2.4, MARB2)
    slab(FR, axis, fixed, out, 1.28, -half - 0.2, half + 0.2, 10.6, 11.4, BLUEP)  # пояс кронштейнов
    for k in range(int(2 * half // 1.2)):
        a = -half + 0.1 + 1.2 * k
        slab(FS, axis, fixed, out, 1.7, a, a + 0.6, 11.0, 11.6, (JADE, GOLD)[k % 2])
    slab(FS, axis, fixed, out, 1.3, -half - 0.2, half + 0.2, 10.4, 10.6, GOLD)
    eave(FR, axis, fixed, out, -half - 3.2, half + 3.2, 13.6, 11.8, 3.4, GLAZE)
    slab(FR, axis, fixed, out, 0.88, -half + 1.6, half - 1.6, 13.6, 16.4, VERM2)
    slab(FR, axis, fixed, out, 1.18, -half + 1.4, half - 1.4, 15.8, 16.4, BLUEP)
    eave(FR, axis, fixed, out, -half - 2.2, half + 2.2, 18.9, 16.4, 2.6, GLAZE)
    for k in range(int(2 * half // 1.6) + 4):  # ребра черепицы нижнего навеса
        a = -half - 2.6 + 1.6 * k
        if a > half + 2.6:
            continue
        p0 = (fixed + out * 1.2, 13.45, a) if axis == "x" else (a, 13.45, fixed + out * 1.2)
        p1 = (fixed + out * 3.3, 11.95, a) if axis == "x" else (a, 11.95, fixed + out * 3.3)
        beam(FS, p0, p1, 0.18, 0.12, GLAZE2)
    for k in range(int(2 * half // 1.6) + 2):  # рёбра черепицы верхней крыши
        a = -half - 1.6 + 1.6 * k
        if a > half + 1.6:
            continue
        p0 = (fixed + out * 1.2, 18.75, a) if axis == "x" else (a, 18.75, fixed + out * 1.2)
        p1 = (fixed + out * 2.5, 16.55, a) if axis == "x" else (a, 16.55, fixed + out * 2.5)
        beam(FS, p0, p1, 0.18, 0.12, GLAZE2)
    for k in range(4):  # решётчатые окна второго яруса
        a = -half + 4.5 + (2 * half - 9.0) * k / 3
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
        f0, f1 = sorted((fixed + out * 0.88, fixed + out * 1.1))
        if axis == "z":
            FG.prism_xy(K.rect(a - 1.6, a + 1.6, 14.0, 15.6), d0, d1, "FFD890")
            FS.frame_xy(K.rect(a - 1.8, a + 1.8, 13.8, 15.7), K.rect(a - 1.6, a + 1.6, 14.0, 15.6), f0, f1, GOLD)
            for i in range(1, 4):
                FS.box(a - 1.6 + 0.8 * i - 0.05, a - 1.6 + 0.8 * i + 0.05, 14.0, 15.6, *sorted((fixed + out * 0.9, fixed + out * 1.0)), GOLD)
            FS.box(a - 1.6, a + 1.6, 14.75, 14.85, *sorted((fixed + out * 0.9, fixed + out * 1.0)), GOLD)
        else:
            FG.prism_zy(K.rect(a - 1.6, a + 1.6, 14.0, 15.6), d0, d1, "FFD890")
            FS.frame_zy(K.rect(a - 1.8, a + 1.8, 13.8, 15.7), K.rect(a - 1.6, a + 1.6, 14.0, 15.6), f0, f1, GOLD)
    if fi > 0:  # бока и тыл: решётчатые окна нижнего яруса
        for a in (-10.0, 0.0, 10.0):
            d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
            f0, f1 = sorted((fixed + out * 0.88, fixed + out * 1.15))
            pr, fr = (FG.prism_zy, FS.frame_zy) if axis == "x" else (FG.prism_xy, FS.frame_xy)
            pr(K.rect(a - 2.0, a + 2.0, 4.0, 8.4), d0, d1, "FFD890")
            fr(K.rect(a - 2.3, a + 2.3, 3.7, 8.7), K.rect(a - 2.0, a + 2.0, 4.0, 8.4), f0, f1, GOLD)
            for i in range(1, 5):
                bb = a - 2.0 + 0.8 * i
                lo, hi = sorted((fixed + out * 0.9, fixed + out * 1.0))
                if axis == "x":
                    FS.box(lo, hi, 4.0, 8.4, bb - 0.05, bb + 0.05, GOLD)
                else:
                    FS.box(bb - 0.05, bb + 0.05, 4.0, 8.4, lo, hi, GOLD)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# загнутые вверх углы крыш с золотыми навершиями
for sx in (-1, 1):
    for sz in (-1, 1):
        for y0, d in ((11.8, 3.3), (16.4, 2.5)):
            cx, cz = sx * (FX + d), sz * (FZ + d)
            taper(FS, (cx - sx * 0.6, y0 + 0.1, cz - sz * 0.6), (cx + sx * 0.3, y0 + 1.3, cz + sz * 0.3), 0.6, 0.15, GOLD)
# балюстрада террасы и лестница с плитой-драконом
for x0, x1 in ((-FX - 2.8, -6.0), (6.0, FX + 2.8)):
    FS.box(x0, x1, 2.4, 2.65, -FZ - 2.75, -FZ - 2.45, MARB)
    n = int((x1 - x0) // 1.6)
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n
        FS.box(x - 0.18, x + 0.18, 1.4, 2.8, -FZ - 2.78, -FZ - 2.42, MARB2)
for k in range(4):
    FR.box(-6.0, 6.0, -0.1, 0.275 + 0.375 * k, -FZ - 2.88 + 0.5 * k, -FZ - 0.88, MARB)
FS.loft([(-2.0, 0.0, -FZ - 2.88), (2.0, 0.0, -FZ - 2.88), (2.0, 0.2, -FZ - 2.88), (-2.0, 0.2, -FZ - 2.88)],
        [(-2.0, 1.45, -FZ - 0.88), (2.0, 1.45, -FZ - 0.88), (2.0, 1.65, -FZ - 0.88), (-2.0, 1.65, -FZ - 0.88)], MARB2)
F.objects(True)
for k in range(6):  # дракон на наклонной плите
    t0, t1 = k / 6, (k + 1) / 6
    x0, x1 = 1.2 * math.sin(t0 * 2 * math.pi), 1.2 * math.sin(t1 * 2 * math.pi)
    z0, z1 = -FZ - 2.7 + 1.7 * t0, -FZ - 2.7 + 1.7 * t1
    y0, y1 = 0.25 + 1.2 * t0, 0.25 + 1.2 * t1
    beam(FS, (x0, y0, z0), (x1, y1, z1), 0.55, 0.3, GOLD)
F.objects(False)
# портик из красных колонн, ворота с золотыми гвоздями
for x in (-16.0, -11.5, -7.0, 7.0, 11.5, 16.0):
    FS.prism_xz(K.ngon(x, -FZ - 1.9, 0.75, 8), 1.4, 1.9, MARB2)
    FS.prism_xz(K.ngon(x, -FZ - 1.9, 0.55, 10), 1.9, 10.6, VERM)
    FS.box(x - 0.7, x + 0.7, 10.0, 10.6, -FZ - 2.6, -FZ - 1.2, BLUEP)
    FS.box(x - 0.75, x + 0.75, 10.0, 10.15, -FZ - 2.65, -FZ - 1.15, GOLD)
FS.box(-FX, FX, 10.6, 11.0, -FZ - 2.6, -FZ - 0.88, VERM2)  # балка портика
FS.box(-FX, FX, 10.8, 11.0, -FZ - 2.66, -FZ - 2.6, GOLD)
FS.box(-4.4, 4.4, 1.4, 9.4, -FZ - 1.3, -FZ - 0.88, VERM2)
FS.frame_xy(K.rect(-4.6, 4.6, 1.4, 9.6), K.rect(-3.8, 3.8, 1.4, 8.8), -FZ - 1.6, -FZ - 1.3, GOLD)
FS.box(-3.8, 3.8, 1.4, 8.8, -FZ - 1.42, -FZ - 1.3, "C83A30")
FS.box(-0.05, 0.05, 1.4, 8.8, -FZ - 1.46, -FZ - 1.42, GLAZE2)
for e in (-1, 1):
    for i in range(3):
        for j in range(5):
            x = e * (0.8 + 1.0 * i)
            FS.prism_xy(K.ngon(x, 2.8 + 1.35 * j, 0.16, 6), -FZ - 1.52, -FZ - 1.42, GOLD)
FS.box(-0.5, 0.5, 4.2, 6.2, -FZ - 1.56, -FZ - 1.42, GLAZE2)  # одна золотая накладка-замок на шве створок
FS.frame_xy(K.ngon(0.0, 4.6, 0.42, 10), K.ngon(0.0, 4.6, 0.28, 10), -FZ - 1.66, -FZ - 1.56, GOLD)
dragon_flat(FS, -5.8, 4.6, 12.6, -FZ - 0.94, -FZ - 0.88, amp=0.4)  # дракон на втором ярусе над воротами
# курильницы, каменные фонари, красные фонари под навесом
F.objects(True)
for e in (-1, 1):
    ding(FS, FG, e * 9.2, -FZ - 1.9, y=1.4, s=1.0)
    stone_lantern(FS, FG, e * 13.6, -FZ - 1.9, y=1.4)
F.objects(False)
for x in (-9.2, -4.6, 4.6, 9.2):
    FS.box(x - 0.04, x + 0.04, 9.0, 10.6, -FZ - 2.0, -FZ - 1.92, GOLD)
    red_lantern(FS, x, 7.6, -FZ - 1.96, s=1.0)

# ══ ИНТЕРЬЕР: тронный зал ═════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.5
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "5A524C")
IQ.box(-2.4, 2.4, 0.02, 0.06, 1.2, ZB - 0.9, CARPET)
IS.box(-2.6, -2.4, 0.02, 0.07, 1.2, ZB - 0.9, VERM)
IS.box(2.4, 2.6, 0.02, 0.07, 1.2, ZB - 0.9, VERM)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, VERM)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 1.2, MARB2)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, VERM)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, GOLD)
    slab(IR, axis, fixed, out, 1.4, -half, half, 14.6, 15.6, BLUEP)
    slab(IS, axis, fixed, out, 1.45, -half, half, 15.6, 15.8, GOLD)
    for k in range(int(2 * half // 1.2)):
        a = -half + 0.1 + 1.2 * k
        slab(IS, axis, fixed, out, 1.8, a, a + 0.6, 15.8, 16.6, (JADE, GOLD)[k % 2])
    if idx < 2:  # решётки окон на боковых стенах
        for a in (-12.0, -1.0):
            d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
            f0, f1 = sorted((fixed + out * 0.88, fixed + out * 1.1))
            IG.prism_zy(K.rect(a - 2.0, a + 2.0, 6.0, 11.4), d0, d1, "FFD890")
            IS.frame_zy(K.rect(a - 2.3, a + 2.3, 5.7, 11.7), K.rect(a - 2.0, a + 2.0, 6.0, 11.4), f0, f1, GOLD)
            for i in range(1, 5):
                IS.box(*sorted((fixed + out * 0.9, fixed + out * 1.0)), 6.0, 11.4, a - 2.0 + 0.8 * i - 0.05, a - 2.0 + 0.8 * i + 0.05, GOLD)
            for i in range(1, 6):
                IS.box(*sorted((fixed + out * 0.9, fixed + out * 1.0)), 6.0 + 0.9 * i - 0.05, 6.0 + 0.9 * i + 0.05, a - 2.0, a + 2.0, GOLD)
# кессонный потолок
for k in range(-3, 4):
    IS.box(-W, W, C - 0.7, C - 0.2, 4.4 * k - 0.25, 4.4 * k + 0.25, JADE)
for k in range(-3, 4):
    IS.box(4.6 * k - 0.25, 4.6 * k + 0.25, C - 0.7, C - 0.2, ZF, ZB, BLUEP)
for i in range(-3, 3):
    for j in range(-3, 3):
        IS.prism_xz(K.ngon(4.6 * i + 2.3, 4.4 * j + 2.2, 0.6, 8), C - 0.12, C - 0.05, GOLD)
# два ряда красных колонн, обвитых золотыми драконами
for s in (-1, 1):
    for z in (-12.0, -5.0, 2.0):
        x = s * 9.6
        IR.prism_xz(K.ngon(x, z, 1.1, 8), 0.0, 0.8, MARB2)
        IS.prism_xz(K.ngon(x, z, 0.8, 12), 0.8, C - 0.7, VERM)
        IS.box(x - 1.0, x + 1.0, C - 1.6, C - 0.7, z - 1.0, z + 1.0, BLUEP)
        pts = [(x + 0.98 * math.cos(0.55 * t + s), 2.0 + 0.42 * t, z + 0.98 * math.sin(0.55 * t + s)) for t in range(26)]
        for a, b in zip(pts, pts[1:]):  # золотой дракон вьётся спиралью вокруг ствола
            beam(IS, a, b, 0.42, 0.42, GOLD)
        hx, hy, hz = pts[-1]
        IS.prism_xz(K.octa(hx, hz, 0.38, 0.38, 0.14), hy - 0.2, hy + 0.45, GOLD)
        IS.prism_xz(K.ngon(hx, hz, 0.12, 4), hy + 0.45, hy + 0.9, GLAZE2)
# золотая ширма из пяти створок за помостом
for k in range(5):
    x0 = -7.5 + 3.0 * k
    zz = ZF + 2.2 + (0.4 if k % 2 else 0.0)
    IS.box(x0, x0 + 3.0, 0.0, 9.4 - abs(k - 2) * 0.8, zz - 0.15, zz + 0.15, GOLD)
    IS.frame_xy(K.rect(x0, x0 + 3.0, 0.0, 9.4 - abs(k - 2) * 0.8), K.rect(x0 + 0.3, x0 + 2.7, 0.6, 9.0 - abs(k - 2) * 0.8),
                zz + 0.15, zz + 0.3, VERM2)
    for c in range(2):  # облака-завитки
        cy = 3.5 + 3.0 * c - 0.3 * abs(k - 2)
        IS.prism_xy(K.ngon(x0 + 1.5, cy, 0.6, 8), zz + 0.15, zz + 0.22, GLAZE2)
        IS.prism_xy(K.ngon(x0 + 1.0, cy - 0.35, 0.45, 8), zz + 0.15, zz + 0.22, GLAZE2)
        IS.prism_xy(K.ngon(x0 + 2.0, cy - 0.35, 0.45, 8), zz + 0.15, zz + 0.22, GLAZE2)
dragon_flat(IS, -4.8, 3.6, 10.6, ZF + 0.94, ZF + 1.0, amp=0.5)
# бронзовые журавли и курильницы
F.objects(True)
for e in (-1, 1):
    x, z = e * 6.0, -9.6
    IS.prism_xz(K.ngon(x, z, 0.7, 8), 0.0, 0.5, MARB2)
    IS.box(x - 0.08, x + 0.08, 0.5, 2.0, z - 0.25, z - 0.1, BRONZE)
    IS.box(x - 0.08, x + 0.08, 0.5, 2.0, z + 0.1, z + 0.25, BRONZE)
    IS.prism_xz(K.octa(x, z, 0.5, 0.9, 0.25), 2.0, 2.8, BRONZE)
    tube(IS, [(x, 2.6, z - 0.7), (x, 3.6, z - 0.9), (x, 4.6, z - 0.8), (x, 5.0, z - 1.1)], [0.25, 0.22, 0.2, 0.2], 0.25, (1, 0, 0), BRONZE)
    IS.prism_zy([(z - 1.1, 4.85), (z - 1.9, 4.9), (z - 1.1, 5.15)], x - 0.08, x + 0.08, GOLD)
    IS.prism_zy([(z + 0.4, 2.2), (z + 1.4, 2.0), (z + 0.6, 2.6)], x - 0.3, x + 0.3, BRONZE)
    ding(IS, IG, e * 12.6, -14.0, s=1.2)
    ding(IS, IG, e * 6.4, 5.0, s=0.9)
F.objects(False)
for x, z in ((-6.0, -1.0), (6.0, -1.0), (-6.0, 6.0), (6.0, 6.0)):
    IS.box(x - 0.04, x + 0.04, C - 4.0, C - 0.7, z - 0.04, z + 0.04, GOLD)
    red_lantern(IS, x, C - 5.6, z, s=1.2)
# белый мраморный помост в три ступени
px, pz = PED
for k, (r, y0, y1) in enumerate(((5.0, 0.0, 0.5), (4.3, 0.5, 1.0), (3.6, 1.0, TOP - 0.1))):
    (IR if k == 0 else IS).box(px - r, px + r, y0, y1, pz - r, pz + r, MARB if k != 1 else MARB2)
IS.box(px - 3.7, px + 3.7, TOP - 0.1, TOP, pz - 3.7, pz + 3.7, GOLD)
for s in (-1, 1):  # балюстрады по бокам помоста
    IS.box(px + s * 4.9 - 0.12, px + s * 4.9 + 0.12, 0.5, 1.8, pz - 4.9, pz + 2.0, MARB2)
    for k in range(4):
        z = pz - 4.6 + 2.0 * k
        IS.box(px + s * 4.9 - 0.18, px + s * 4.9 + 0.18, 0.5, 2.0, z - 0.18, z + 0.18, MARB)
B.lift_leaves(IS, VERM2, GOLD)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX - 2.9, FX + 2.9, -1.0, 1.4, -FZ - 2.9, FZ + 2.9, MARB)
SL.box(-FX, FX, 1.4, 11.4, -FZ, FZ, VERM)
SL.prism_zy([(-FZ - 3.4, 11.8), (FZ + 3.4, 11.8), (FZ + 0.88, 13.6), (-FZ - 0.88, 13.6)], -FX - 3.4, FX + 3.4, GLAZE)
SL.box(-FX + 1.6, FX - 1.6, 13.6, 16.4, -FZ + 1.6, FZ - 1.6, VERM2)
SL.prism_zy([(-FZ - 2.6, 16.4), (FZ + 2.6, 16.4), (FZ + 0.88, 18.9), (-FZ - 0.88, 18.9)], -FX - 2.6, FX + 2.6, GLAZE)

F.build(exhibit=(PED[0], TOP, PED[1], 2.0), lamps=[("Hall", (0, 14, 6), 1700, (1.0, 0.92, 0.82)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Screen", (0, 8, ZF + 6), 700, (1.0, 0.85, 0.6))])
