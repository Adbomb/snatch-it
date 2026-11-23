"""Этаж «Живой сыр-монстр» музея-небоскрёба (пятая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — альпийская сыроварня. Снаружи — шале: белёный каменный низ, верх из тёмных брёвен, резной
деревянный балкон с ящиками красной герани, широкий свес крыши с резными кронштейнами и снежной кромкой,
арочная каменная дверь в погреб, у входа — башня из сырных голов, огромный сырный клин-вывеска с дырками,
колокольчик, бидоны молока, альпийский рог; бока — поленницы и ставни с ромбическими прорезями; сзади —
тележка с бидонами. Внутри — сырный погреб: каменные стены со сводчатыми нишами, деревянные стеллажи с
головками сыра, медный котёл над огнём, стол с фондю, клинья сыра, фонари, бочки; экспонат — на огромной сырной
голове в красном воске под дубовой доской.
Запуск: blender --background --factory-startup --python scripts/blender/floor_cheese.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, ring_y, rng, slab  # noqa: E402

STUCCO, STUCCO2, STONE, STONE2, LOG, LOG2, LOG3 = "F2EBDD", "DED4C0", "B8AE9C", "9A9080", "8A5432", "6A3E24", "A86A40"
CHEESE, CHEESE2, RIND, HOLE, SNOW, RED, RED2 = "FFCC4A", "F4B436", "E09A2A", "D88E1E", "F8FBFF", "E0302E", "B0201E"
LEAF, COPPER, COPPER2, STEEL, FIRE, FIRE2, DARK = "3E8E3A", "D07A3E", "A85A2A", "C8CCD4", "FF8A2A", "FFD060", "2A2220"

F = B.Floor("CH", "LiveCheeseMonster", quiet=(STONE2, LOG2, STUCCO2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def wheel_small(p, x, z, y, r, h):
    """Лёгкая сырная голова для стеллажей: бок и светлый верх (восьмигранник)."""
    p.prism_xz(K.ngon(x, z, r, 8), y, y + h * 0.82, CHEESE2)
    p.prism_xz(K.ngon(x, z, r * 0.96, 8), y + h * 0.82, y + h, CHEESE)


def wheel(p, x, z, y, r, h, rind=RIND, top=CHEESE, holes=True, seed=0):
    """Сырная голова: корка, светлый срез сверху, неровные дырки (три, разного размера — не «лицо»)."""
    p.prism_xz(K.ngon(x, z, r, 12), y, y + h * 0.15, rind)
    p.prism_xz(K.ngon(x, z, r * 1.03, 12), y + h * 0.15, y + h * 0.85, CHEESE2)
    p.prism_xz(K.ngon(x, z, r, 12), y + h * 0.85, y + h, top)
    if holes:
        for k in range(3):
            t = 2 * math.pi * (k + rng(seed, k) * 0.6) / 3
            rr = r * (0.1 + 0.1 * rng(k, seed))
            p.prism_xz(K.ngon(x + r * 0.55 * math.cos(t), z + r * 0.55 * math.sin(t), rr, 6), y + h, y + h + 0.03, HOLE)


def wedge(p, x, z, y, r, h, yaw=0.0):
    """Сырный клин: треугольная призма с коркой по дуге и дырками на срезе."""
    c, s = math.cos(yaw), math.sin(yaw)
    pts = [(0.0, 0.0), (r, -r * 0.45), (r * 1.05, 0.0), (r, r * 0.45)]
    p.prism_xz([(x + u * c - v * s, z + u * s + v * c) for u, v in pts], y, y + h, CHEESE)
    p.prism_xz([(x + u * c - v * s, z + u * s + v * c) for u, v in ((r * 0.92, -r * 0.42), (r * 1.08, -r * 0.42), (r * 1.12, 0.0),
                                                                     (r * 1.08, r * 0.42), (r * 0.92, r * 0.42), (r * 0.96, 0.0))],
               y, y + h, RIND)


def geranium_box(p, axis, fixed, out, a0, a1, y):
    """Ящик с геранью: деревянный ящик, листва, красные цветки."""
    slab(p, axis, fixed, out, 1.6, a0, a1, y, y + 0.7, LOG3)
    n = int((a1 - a0) // 0.8)
    for k in range(n):
        a = a0 + 0.4 + (a1 - a0 - 0.8) * k / max(1, n - 1)
        if axis == "z":
            p.prism_xz(K.octa(a, fixed + out * 1.2, 0.45, 0.4, 0.15), y + 0.7, y + 1.2, LEAF)
            p.prism_xz(K.octa(a + 0.1, fixed + out * 1.3, 0.22, 0.22, 0.08), y + 1.2, y + 1.45, (RED, RED2)[k % 2])
        else:
            p.prism_xz(K.octa(fixed + out * 1.2, a, 0.4, 0.45, 0.15), y + 0.7, y + 1.2, LEAF)
            p.prism_xz(K.octa(fixed + out * 1.3, a + 0.1, 0.22, 0.22, 0.08), y + 1.2, y + 1.45, (RED, RED2)[k % 2])


def milk_can(p, x, z, y=0.0, s=1.0):
    """Бидон: корпус, плечики, горлышко, крышка."""
    p.prism_xz(K.ngon(x, z, 0.55 * s, 10), y, y + 1.4 * s, STEEL)
    p.loft([(x + 0.55 * s * math.cos(t), y + 1.4 * s, z + 0.55 * s * math.sin(t)) for t in [2 * math.pi * k / 10 for k in range(10)]],
           [(x + 0.32 * s * math.cos(t), y + 1.8 * s, z + 0.32 * s * math.sin(t)) for t in [2 * math.pi * k / 10 for k in range(10)]], STEEL)
    p.prism_xz(K.ngon(x, z, 0.38 * s, 10), y + 1.8 * s, y + 2.0 * s, "9AA0AA")


def lantern(p, g, x, y, z):
    """Фонарь на кронштейне."""
    p.prism_xz(K.ngon(x, z, 0.4, 6), y + 0.8, y + 1.0, DARK)
    g.prism_xz(K.ngon(x, z, 0.3, 6), y + 0.15, y + 0.8, FIRE2)
    p.prism_xz(K.ngon(x, z, 0.36, 6), y, y + 0.15, DARK)


# ══ ФАСАД: альпийское шале-сыроварня ══════════════════════════════════════════════════════════════════════════
B.shell_planes(F, STUCCO, STUCCO, LOG2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "8AAA6A")
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.2, STONE)
    for k in range(int(2 * half // 2.4)):  # каменный цоколь
        a = -half + 2.4 * k
        slab(FR, axis, fixed, out, 1.48, a + 0.1, a + 2.3, 0.1, 1.1, (STONE, STONE2)[k % 2])
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.2, 7.6, STUCCO)
    slab(FR, axis, fixed, out, 1.2, -half, half, 7.6, 8.2, LOG2)
    for r in range(9):  # бревенчатый верх
        y = 8.2 + 0.8 * r
        slab(FR, axis, fixed, out, 1.0 + 0.06 * (r % 2), -half - 0.2, half + 0.2, y + 0.04, y + 0.76, (LOG, LOG3)[r % 2])
    slab(FR, axis, fixed, out, 2.88, -half - 2.0, half + 2.0, 15.4, 16.2, LOG2)
    slab(FR, axis, fixed, out, 3.0, -half - 2.1, half + 2.1, 16.2, 16.6, SNOW)
    slab(FR, axis, fixed, out, 0.88, -half, half, 16.6, 18.9, LOG2)
    B.chamfer(FR, axis, fixed, out, -half - 1.8, half + 1.8, [(0.0, 16.6), (1.9, 16.6), (1.9, 16.9), (0.0, 18.9)], LOG)  # скат кровли
    for k in range(int(2 * half // 3.0) + 1):  # резные кронштейны под свесом
        a = -half + 3.0 * k
        if axis == "z":
            FS.prism_zy([(fixed + out * 0.9, 13.6), (fixed + out * 0.9, 15.4), (fixed + out * 2.6, 15.4), (fixed + out * 2.4, 14.9),
                         (fixed + out * 1.6, 14.6)], a - 0.2, a + 0.2, LOG3)
        else:
            FS.prism_xy([(fixed + out * 0.9, 13.6), (fixed + out * 0.9, 15.4), (fixed + out * 2.6, 15.4), (fixed + out * 2.4, 14.9),
                         (fixed + out * 1.6, 14.6)], a - 0.2, a + 0.2, LOG3)
    if axis == "x":  # бока: поленница и окна с ромбическими ставнями
        for z in (-8.0, 6.0):
            FG.prism_zy(K.rect(z - 1.6, z + 1.6, 3.0, 6.4), *sorted((fixed + out * 0.9, fixed + out * 0.94)), "FFE6A0")
            for e in (-1, 1):
                slab(FS, axis, fixed, out, 1.1, z + e * 1.6, z + e * 3.0, 3.0, 6.4, RED2)
                FS.prism_zy([(z + e * 2.3, 4.2), (z + e * 2.6, 4.7), (z + e * 2.3, 5.2), (z + e * 2.0, 4.7)], *sorted((fixed + out * 1.1, fixed + out * 1.16)),
                   STUCCO)
            geranium_box(FS, axis, fixed, out, z - 1.8, z + 1.8, 2.3)
        for k in range(3):
            for m in range(5):
                FS.prism_zy(K.ngon(-14.0 + 0.0 + 0.85 * m + 0.4 * (k % 2), 0.45 + 0.8 * k, 0.4, 6),
                            *sorted((fixed + out * 1.0, fixed + out * 2.6)), (LOG3, LOG)[(k + m) % 2])
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# перед: арочная каменная дверь в погреб
arch_o = [(-3.4, 1.2), (3.4, 1.2)] + [(3.4 * math.cos(math.pi * k / 8), 5.4 + 2.0 * math.sin(math.pi * k / 8)) for k in range(9)]
arch_i = [(-2.6, 1.2), (2.6, 1.2)] + [(2.6 * math.cos(math.pi * k / 8), 5.4 + 1.5 * math.sin(math.pi * k / 8)) for k in range(9)]
FS.frame_xy(arch_o, arch_i, -FZ - 1.6, -FZ - 0.88, STONE)
FS.prism_xy(arch_i, -FZ - 1.0, -FZ - 0.88, LOG2)
for k in range(5):
    FS.box(-2.4 + 1.0 * k, -2.4 + 1.0 * k + 0.08, 1.2, 6.4, -FZ - 1.06, -FZ - 1.0, DARK)
for e in (-1, 1):
    FS.box(e * 1.2 - 0.6, e * 1.2 + 0.6, 3.2, 3.4, -FZ - 1.1, -FZ - 1.0, DARK)
# окна низа со ставнями и геранью
for x in (-14.4, -8.0, 8.0, 14.4):  # четыре окна ритмом (пара окон у двери читалась бы «лицом»)
    FG.box(x - 1.3, x + 1.3, 3.0, 6.6, -FZ - 0.94, -FZ - 0.9, "FFE6A0")
    FS.frame_xy(K.rect(x - 1.5, x + 1.5, 2.8, 6.8), K.rect(x - 1.3, x + 1.3, 3.0, 6.6), -FZ - 1.2, -FZ - 0.88, LOG2)
    for e in (-1, 1):
        FS.box(*sorted((x + e * 1.5, x + e * 2.6)), 2.8, 6.8, -FZ - 1.1, -FZ - 0.88, RED2)
        FS.prism_xy([(x + e * 2.05, 4.3), (x + e * 2.3, 4.8), (x + e * 2.05, 5.3), (x + e * 1.8, 4.8)], -FZ - 1.16, -FZ - 1.1, STUCCO)
    geranium_box(FS, "z", -FZ, -1, x - 1.6, x + 1.6, 2.0)
# резной балкон на бревенчатом этаже
FS.box(-14.0, 14.0, 8.6, 9.0, -FZ - 3.0, -FZ - 0.9, LOG2)
for k in range(29):
    x = -14.0 + 1.0 * k
    FS.prism_xy([(x - 0.3, 9.0), (x + 0.3, 9.0), (x + 0.3, 10.2), (x + 0.15, 10.5), (x + 0.3, 10.8), (x + 0.3, 11.6), (x - 0.3, 11.6),
                 (x - 0.3, 10.8), (x - 0.15, 10.5), (x - 0.3, 10.2)], -FZ - 3.0, -FZ - 2.84, LOG3)
FS.box(-14.2, 14.2, 11.6, 11.9, -FZ - 3.1, -FZ - 2.7, LOG2)
for x in (-8.0, 0.0, 8.0):
    geranium_box(FS, "z", -FZ - 2.0, -1, x - 2.2, x + 2.2, 11.9)
FG.box(-4.0, 4.0, 9.0, 13.6, -FZ - 0.96, -FZ - 0.92, "FFE6A0")
FS.frame_xy(K.rect(-4.3, 4.3, 9.0, 13.9), K.rect(-4.0, 4.0, 9.0, 13.6), -FZ - 1.3, -FZ - 0.88, LOG2)
FS.box(-0.1, 0.1, 9.0, 13.6, -FZ - 1.2, -FZ - 0.92, LOG2)
# сырный клин-вывеска на кронштейне, башня сырных голов, бидоны, колокол, альпийский рог
FS.box(-0.2, 0.2, 13.8, 14.2, -FZ - 6.0, -FZ - 0.9, DARK)
FS.prism_xy([(-3.2, 13.6), (3.2, 13.6), (2.8, 13.0), (0.0, 10.4), (-2.8, 13.0)], -FZ - 6.3, -FZ - 5.1, CHEESE)
FS.prism_xy([(-3.2, 13.6), (3.2, 13.6), (3.2, 14.0), (-3.2, 14.0)], -FZ - 6.3, -FZ - 5.1, RIND)
for k, (hx, hy, hr) in enumerate(((-1.4, 12.8, 0.4), (0.8, 13.0, 0.3), (0.1, 11.7, 0.28))):
    FS.prism_xy(K.ngon(hx, hy, hr, 8), -FZ - 6.36, -FZ - 6.3, HOLE)
for k in range(5):
    wheel(FS, -6.4 + 0.15 * (k % 2), -FZ - 3.0, 0.8 * k, 1.3 - 0.08 * k, 0.8, seed=k)
for k in range(3):
    wheel(FS, 6.2, -FZ - 3.2 - 1.8 * (k % 2), 0.0 if k < 2 else 0.8, 1.0, 0.8, seed=k + 5)
for x, z in ((14.0, -FZ - 3.0), (15.4, -FZ - 4.2), (13.4, -FZ - 4.6)):
    milk_can(FS, x, z, 0.0, 1.1)
FS.cone([(-15.0 + 0.6 * math.cos(t), 0.0, -FZ - 4.0 + 0.6 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]],
        (-11.0, 0.3, -FZ - 4.0), LOG3)
FS.prism_xz(K.ngon(-15.0, -FZ - 4.0, 0.7, 8), 0.0, 1.2, LOG3)
FS.box(-12.0 - 0.06, -12.0 + 0.06, 3.8, 5.0, -FZ - 1.4, -FZ - 0.9, DARK)
FS.cone([(-12.0 + 0.6 * math.cos(t), 2.6, -FZ - 1.6 + 0.6 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]],
        (-12.0, 3.8, -FZ - 1.6), COPPER)
# тыл: тележка с бидонами
FS.box(-6.0, 0.0, 0.8, 1.2, FZ + 1.6, FZ + 4.6, LOG3)
for x in (-5.2, -0.8):
    FS.prism_xy(K.ngon(x, 0.8, 0.8, 10), FZ + 1.3, FZ + 1.6, LOG2)
for k in range(3):
    milk_can(FS, -4.6 + 1.6 * k, FZ + 3.1, 1.2, 0.9)

# ══ ИНТЕРЬЕР: сырный погреб ═══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), STONE2)
for i in range(-5, 5):  # плитняк
    for j in range(-5, 5):
        if (i + j) % 2:
            IQ.box(3.3 * i + 0.1, 3.3 * i + 3.2, 0.02, 0.05, 3.2 * j + 0.1, 3.2 * j + 3.1, STONE)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, STONE)
        for r in range(6):  # бутовая кладка
            y = 0.2 + 1.6 * r
            if gap and y + 1.4 > DOOR[1]:
                break
            for k in range(int((a1 - a0) // 2.2)):
                a = a0 + 2.2 * k + (1.1 if r % 2 else 0.0)
                if a + 2.0 > a1 or rng(idx, r, k) < 0.66:
                    continue
                slab(IR, axis, fixed, out, 1.0, a + 0.1, a + 2.1, y + 0.1, y + 1.5, (STONE, STONE2, STUCCO2)[(k + r) % 3])
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, STONE)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, LOG3)
for k in range(-2, 3):  # своды-арки поперёк зала
    z = 5.6 * k
    IS.box(-W, -W + 1.2, 0.0, 12.0, z - 0.6, z + 0.6, STONE2)
    IS.box(W - 1.2, W, 0.0, 12.0, z - 0.6, z + 0.6, STONE2)
    for m in range(8):
        x0, x1 = -W + 2 * W * m / 8, -W + 2 * W * (m + 1) / 8
        y0, y1 = 12.0 + 4.6 * math.sin(math.pi * m / 8), 12.0 + 4.6 * math.sin(math.pi * (m + 1) / 8)
        IS.loft([(x0, y0, z - 0.6), (x1, y1, z - 0.6), (x1, y1, z + 0.6), (x0, y0, z + 0.6)],
                [(x0, y0 + 0.8, z - 0.6), (x1, y1 + 0.8, z - 0.6), (x1, y1 + 0.8, z + 0.6), (x0, y0 + 0.8, z + 0.6)], STONE2)
# стеллажи с сырными головами вдоль боковых стен
for s in (-1, 1):
    for z0, z1 in ((-14.6, -6.4), (-4.6, 3.6)):
        x = s * (W - 1.6)
        for e in (z0, z1):
            IS.box(x - 1.0, x + 1.0, 0.0, 10.0, e - 0.15, e + 0.15, LOG2)
        for r in range(3):
            y = 1.2 + 3.0 * r
            IS.box(x - 1.0, x + 1.0, y - 0.15, y, z0, z1, LOG3)
            for k in range(3):
                zz = z0 + 1.4 + (z1 - z0 - 2.8) * k / 2
                wheel_small(IS, x, zz, y, 0.9, 0.8)
# медный котёл над огнём у дальней стены, стол с фондю, клинья, фонари, бочки
KX, KZ = 8.0, ZF + 3.6
for k in range(5):
    t = 2 * math.pi * k / 5
    beam(IS, (KX + 1.0 * math.cos(t), 0.0, KZ + 1.0 * math.sin(t)), (KX + 1.4 * math.cos(t + 0.5), 0.5, KZ + 1.4 * math.sin(t + 0.5)), 0.3,
         0.3, LOG2)
IG.cone([(KX + 0.9 * math.cos(t), 0.2, KZ + 0.9 * math.sin(t)) for t in [2 * math.pi * k / 6 for k in range(6)]], (KX, 1.6, KZ), FIRE)
IG.cone([(KX + 0.5 * math.cos(t), 0.2, KZ + 0.5 * math.sin(t)) for t in [2 * math.pi * k / 6 for k in range(6)]], (KX + 0.2, 2.0, KZ), FIRE2)
IS.loft([(KX + 1.4 * math.cos(t), 1.8, KZ + 1.4 * math.sin(t)) for t in [2 * math.pi * k / 12 for k in range(12)]],
        [(KX + 2.0 * math.cos(t), 4.0, KZ + 2.0 * math.sin(t)) for t in [2 * math.pi * k / 12 for k in range(12)]], COPPER)
IS.prism_xz(K.ngon(KX, KZ, 1.85, 12), 3.9, 3.95, CHEESE2)
for e in (-1, 1):
    IS.box(KX + e * 2.8 - 0.15, KX + e * 2.8 + 0.15, 0.0, 6.4, KZ - 0.15, KZ + 0.15, DARK)
IS.box(KX - 2.95, KX + 2.95, 6.2, 6.5, KZ - 0.15, KZ + 0.15, DARK)
IR.box(-12.0, -6.0, 0.0, 2.8, ZF + 2.0, ZF + 4.6, LOG2)
IS.box(-12.3, -5.7, 2.8, 3.1, ZF + 1.8, ZF + 4.8, LOG3)
IS.prism_xz(K.ngon(-9.0, ZF + 3.3, 0.7, 10), 3.1, 3.9, RED)
IS.prism_xz(K.ngon(-9.0, ZF + 3.3, 0.6, 10), 3.9, 3.95, CHEESE)
wedge(IS, -11.0, ZF + 3.0, 3.1, 1.0, 0.7, 0.6)
wedge(IS, -7.0, ZF + 3.6, 3.1, 0.9, 0.6, 2.4)
for x, z in ((-11.0, 9.6), (11.2, 9.0)):
    D.barrel(IS, x, z, 0.0, 0.9, 1.9, LOG3, DARK)
for x, z in ((-9.0, -10.0), (9.0, -10.0), (-9.0, 4.0), (9.0, 4.0)):
    lantern(IS, IG, x, 8.4, z)
    IS.box(x - 0.03, x + 0.03, 9.4, 14.0, z - 0.03, z + 0.03, DARK)
wheel(IS, 5.6, 6.0, 0.0, 1.2, 0.9, seed=11)
wedge(IS, -5.8, 5.6, 0.0, 1.3, 0.9, 1.0)
# постамент — огромная сырная голова на деревянной доске
px, pz = PED
IR.box(px - 4.6, px + 4.6, 0.0, 0.35, pz - 4.2, pz + 4.2, LOG3)
for k in range(5):
    IS.box(px - 4.6 + 1.84 * k, px - 4.6 + 1.84 * k + 0.05, 0.35, 0.37, pz - 4.2, pz + 4.2, LOG2)
IR.prism_xz(K.ngon(px, pz, 3.8, 14), 0.35, 0.5, RED2)  # голова в красном воске под дубовой доской: жёлтый экспонат ярче подставки
IR.prism_xz(K.ngon(px, pz, 3.9, 14), 0.5, TOP - 0.12, RED)
IS.prism_xz(K.ngon(px, pz, 3.7, 14), TOP - 0.12, TOP, LOG2)
for k in range(4):
    IS.box(px - 3.3 + 1.65 * k, px - 3.3 + 1.65 * k + 0.06, TOP, TOP + 0.02, pz - 3.2, pz + 3.2, LOG)
B.lift_leaves(IS, LOG2, CHEESE)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 7.6, -FZ, FZ, STUCCO)
SL.box(-FX, FX, 7.6, 18.9, -FZ, FZ, LOG)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "8AAA6A")
SL.box(-FX - 2.1, FX + 2.1, 15.4, 16.6, -FZ - 2.1, FZ + 2.1, SNOW)
SL.box(-14.0, 14.0, 8.6, 11.9, -FZ - 3.0, -FZ, LOG3)
SL.prism_xy([(-3.2, 13.6), (3.2, 13.6), (0.0, 10.4)], -FZ - 6.3, -FZ - 5.1, CHEESE)

F.build(exhibit=(PED[0], TOP, PED[1], 2.5), lamps=[("Hall", (0, 14, 6), 2600, (1.0, 0.88, 0.72)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.95, 0.85)),
                                                   ("Fire", (8, 3, -12), 1000, (1.0, 0.6, 0.3))])
