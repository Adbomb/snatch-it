"""Этаж «Сундук-мимик» музея-небоскрёба (восьмая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — пиратская таверна в порту. Снаружи — кремовая штукатурка с тёмным фахверком и каменным цоколем,
в левый угол фасада «врезался» нос корабля: обшитый досками корпус с бушпритом, канатами и кусочком паруса;
у входа — висячая вывеска с двумя скрещёнными саблями, фонари, пушка на лафете, пирамида ядер, бочки, бухта каната,
сундук с золотом, пальма; на крыше — чёрный флаг со скрещёнными костями; на боках — круглые окна-иллюминаторы
по одному в каждом пролёте. Внутри — таверна: дощатый пол и балки, стойка с бочками-кранами, столы с кружками и
лавками, люстра-штурвал со свечами, карта сокровищ на стене, сети, пушка у окна, вокруг постамента — горки
золотых монет и самоцветы; экспонат — на горе золотых монет на дощатом помосте.
Запуск: blender --background --factory-startup --python scripts/blender/floor_pirate.py -- <репо> <превью>
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

PLASTER, PLASTER2, WOOD, WOOD2, WOOD3, STONE = "E8DCC0", "D4C4A4", "7A5232", "4E3420", "9A6A3A", "8A8478"
GOLD, GOLD2, RED, BLACK, ROPE, SAIL = "F0C030", "C8962A", "B83A2A", "2A2A2E", "D8C090", "EEE6D0"
GLASS, SEA = "FFD890", "3A8AB0"
GEMS = ("E8343A", "3A8AE8", "3AC86A", "B06AE0")

F = B.Floor("PI", "RatMimic", quiet=(STONE, "8A7A60"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def coin_pile(p, x, z, y, r, seed=0):
    """Горка монет: три гранёных яруса золота и несколько самоцветов."""
    p.prism_xz(K.octa(x, z, r, r * 0.85, r * 0.35), y, y + r * 0.35, GOLD2)
    p.prism_xz(K.octa(x, z, r * 0.7, r * 0.6, r * 0.25), y + r * 0.35, y + r * 0.65, GOLD)
    p.prism_xz(K.octa(x, z, r * 0.4, r * 0.35, r * 0.15), y + r * 0.65, y + r * 0.85, GOLD)
    for k in range(3):
        a = 2 * math.pi * (k + rng(seed, k)) / 3
        p.prism_xz(K.octa(x + r * 0.55 * math.cos(a), z + r * 0.5 * math.sin(a), 0.16, 0.16, 0.06), y + r * 0.4, y + r * 0.6,
                   GEMS[(k + seed) % 4])


def cannon(p, x, z, y, face=-1):
    """Пушка на лафете вдоль z (дуло к face)."""
    p.box(x - 0.8, x + 0.8, y, y + 0.7, z - 1.2, z + 1.0, WOOD)
    for e in (-1, 1):
        p.prism_zy(K.ngon(z + e * 0.8, y + 0.35, 0.45, 8), x - 0.95, x - 0.8, WOOD2)
        p.prism_zy(K.ngon(z + e * 0.8, y + 0.35, 0.45, 8), x + 0.8, x + 0.95, WOOD2)
    p.loft([(x + 0.45 * math.cos(a), y + 1.1 + 0.45 * math.sin(a), z - face * 1.0) for a in [2 * math.pi * k / 8 for k in range(8)]],
           [(x + 0.32 * math.cos(a), y + 1.3 + 0.32 * math.sin(a), z + face * 1.6) for a in [2 * math.pi * k / 8 for k in range(8)]], BLACK)
    p.prism_xy(K.ngon(x, y + 1.3, 0.4, 8), *sorted((z + face * 1.6, z + face * 1.75)), BLACK)


def mug(p, x, z, y):
    p.prism_xz(K.ngon(x, z, 0.22, 6), y, y + 0.45, WOOD3)
    p.prism_xz(K.ngon(x, z, 0.2, 6), y + 0.45, y + 0.52, "F4ECD8")


def sabers(p, cx, cy, z0, z1, s=1.0):
    """Две скрещённые сабли (вид спереди)."""
    for e in (-1, 1):
        a = math.radians(45 if e > 0 else 135)
        dx, dy = math.cos(a), math.sin(a)
        nx, ny = -dy * 0.12 * s, dx * 0.12 * s
        tip = (cx + dx * 1.6 * s, cy + dy * 1.6 * s)
        hilt = (cx - dx * 1.2 * s, cy - dy * 1.2 * s)
        p.prism_xy([(hilt[0] + nx, hilt[1] + ny), (tip[0], tip[1]), (hilt[0] - nx, hilt[1] - ny)], z0, z1, "D8DCE4")
        p.prism_xy(K.rect(hilt[0] - 0.3 * s, hilt[0] + 0.3 * s, hilt[1] - 0.1 * s, hilt[1] + 0.1 * s), z0, z1 + 0.04, GOLD)


# ══ ФАСАД: таверна ════════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, PLASTER, PLASTER, WOOD2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "8A7A60")
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 2.4, STONE)
    slab(FR, axis, fixed, out, 0.88, -half, half, 2.4, 16.2, PLASTER)
    for y in (2.4, 9.0, 15.6):
        slab(FR, axis, fixed, out, 1.18, -half - 0.1, half + 0.1, y, y + 0.6, WOOD2)
    for k in range(int(2 * half // 3.6) + 1):  # фахверк
        a = -half + 0.2 + 3.6 * k
        if a + 0.5 > half:
            continue
        slab(FS, axis, fixed, out, 1.05, a, a + 0.5, 3.0, 15.6, WOOD2)
    B.chamfer(FR, axis, fixed, out, -half - 1.6, half + 1.6, [(0.88, 18.9), (2.4, 16.2), (2.4, 15.9), (0.88, 15.9)], "6A3A2A")
    if fi > 0:  # бока и тыл: по одному круглому окну в пролёте
        for k in range(int(2 * half // 7.2)):
            a = -half + 2.0 + 7.2 * k
            if a + 1.2 > half:
                continue
            y = 6.0 if k % 2 == 0 else 12.2
            d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
            pr, fr = (FG.prism_zy, FS.frame_zy) if axis == "x" else (FG.prism_xy, FS.frame_xy)
            pr(K.ngon(a, y, 0.9, 10), d0, d1, GLASS)
            fr(K.ngon(a, y, 1.2, 10), K.ngon(a, y, 0.9, 10), *sorted((fixed + out * 0.88, fixed + out * 1.15)), GOLD2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# нос корабля, «врезавшийся» в левый (по фасаду +x) угол
F.objects(True)
NX, NZ = 13.4, -FZ - 1.0
hull = [(NX - 4.4, 1.0), (NX + 3.6, 1.0), (NX + 5.2, 4.2), (NX + 5.4, 8.6), (NX - 4.4, 8.6)]
FS.prism_xy(hull, NZ - 1.6, NZ + 0.2, WOOD)
for y in (2.6, 4.2, 5.8, 7.4):
    FS.box(NX - 4.4, NX + 3.6 + (y - 1.0) / 7.6 * 1.6, y - 0.08, y + 0.08, NZ - 1.66, NZ - 1.6, WOOD2)
FS.box(NX - 4.6, NX + 5.6, 8.6, 9.0, NZ - 1.8, NZ + 0.2, RED)
for k in range(3):  # пушечные порты
    FS.box(NX - 3.6 + 2.4 * k, NX - 2.6 + 2.4 * k, 5.0, 6.0, NZ - 1.7, NZ - 1.6, BLACK)
beam(FS, (NX + 5.0, 8.4, NZ - 0.7), (NX + 7.4, 11.4, NZ - 0.7), 0.35, 0.35, WOOD2)  # бушприт
D.chain(FS, (NX + 7.2, 11.2, NZ - 0.7), (NX - 2.0, 15.0, NZ - 0.8), 6, 0.08, ROPE, sag=0.8)
FS.prism_xy([(NX + 6.4, 10.6), (NX + 2.6, 14.0), (NX + 2.6, 10.6)], NZ - 0.76, NZ - 0.64, SAIL)
F.objects(False)
# вход, вывеска с саблями, фонари
FS.box(-2.6, 1.8, 2.4, 9.0, -FZ - 0.96, -FZ - 0.88, WOOD2)
FS.box(-2.2, 1.4, 2.4, 8.6, -FZ - 1.06, -FZ - 0.96, WOOD3)
FS.box(-0.45, -0.35, 2.4, 8.6, -FZ - 1.1, -FZ - 1.06, WOOD2)
FG.prism_xy(K.ngon(-0.4, 7.4, 0.6, 8), -FZ - 1.1, -FZ - 1.06, GLASS)
FS.box(-3.8, 1.6, 10.0, 10.2, -FZ - 2.6, -FZ - 0.88, WOOD2)
for x in (-3.4, -1.0):
    FS.box(x - 0.03, x + 0.03, 9.0, 10.0, -FZ - 2.3, -FZ - 2.24, BLACK)
FS.box(-4.4, 0.0, 6.8, 9.0, -FZ - 2.34, -FZ - 2.2, WOOD3)
sabers(FS, -2.2, 7.9, -FZ - 2.42, -FZ - 2.34, s=0.75)
for x in (-4.2, 3.4):
    FS.box(x - 0.05, x + 0.05, 7.2, 8.2, -FZ - 1.6, -FZ - 0.88, BLACK)
    D.lantern(FS, FG, x, 6.4, -FZ - 1.6, s=0.8, cap=BLACK, light=GLASS)
# широкое окно таверны справа
FG.box(-15.4, -7.4, 4.0, 7.6, -FZ - 0.94, -FZ - 0.9, GLASS)
FS.frame_xy(K.rect(-15.8, -7.0, 3.6, 8.0), K.rect(-15.4, -7.4, 4.0, 7.6), -FZ - 1.2, -FZ - 0.88, WOOD2)
for x in (-12.7, -10.1):
    FS.box(x - 0.06, x + 0.06, 4.0, 7.6, -FZ - 1.0, -FZ - 0.94, WOOD2)
# второй этаж: окна со ставнями, балкончик с перилами, грузовая балка с бочонком на канате
for x in (-14.2, 2.4):  # окна не парами: над широким окном — только одно
    FG.box(x - 1.0, x + 1.0, 11.0, 13.6, -FZ - 0.94, -FZ - 0.9, GLASS)
    FS.frame_xy(K.rect(x - 1.25, x + 1.25, 10.75, 13.85), K.rect(x - 1.0, x + 1.0, 11.0, 13.6), -FZ - 1.15, -FZ - 0.88, WOOD2)
    for e in (-1, 1):
        FS.box(x + e * 1.3 - (0.0 if e > 0 else 1.0), x + e * 1.3 + (1.0 if e > 0 else 0.0), 11.0, 13.6, -FZ - 1.05, -FZ - 0.95, "2E5A6A")
FS.box(-16.0, -6.8, 10.2, 10.5, -FZ - 2.2, -FZ - 0.88, WOOD)
FS.box(-16.0, -6.8, 11.5, 11.65, -FZ - 2.2, -FZ - 2.05, WOOD2)
for k in range(10):
    x = -16.0 + 1.02 * k
    FS.box(x - 0.05, x + 0.05, 10.5, 11.5, -FZ - 2.15, -FZ - 2.07, WOOD2)
FS.box(6.4, 6.8, 14.4, 14.8, -FZ - 3.0, -FZ - 0.88, WOOD2)
FS.box(6.57, 6.63, 10.6, 14.4, -FZ - 2.83, -FZ - 2.77, ROPE)
F.objects(True)
D.barrel(FS, 6.6, -FZ - 2.8, y=9.4, r=0.5, h=1.2, wood=WOOD3, hoop=BLACK)
F.objects(False)
# пушка, ядра, бочки, канат, сундук с золотом, пальма
F.objects(True)
cannon(FS, -5.6, -FZ - 2.0, -0.1, face=-1)
for k, (dx, dz, dy) in enumerate(((0, 0, 0), (0.5, 0, 0), (0.25, 0.42, 0), (0.25, 0.14, 0.42))):
    FS.prism_xz(K.octa(-7.8 + dx, -FZ - 1.6 + dz, 0.25, 0.25, 0.1), -0.1 + dy, 0.35 + dy, BLACK)
for k, (x, z, y) in enumerate(((-14.4, -FZ - 1.6, -0.1), (-12.8, -FZ - 1.6, -0.1), (-13.6, -FZ - 1.6, 1.6))):
    D.barrel(FS, x, z, y=y, r=0.75, h=1.6, wood=WOOD3, hoop=BLACK)
ring_y(FS, -16.6, -FZ - 1.4, 0.3, 1.0, -0.1, 0.4, ROPE, n=10)
CX = 4.4  # сундук с золотом
FS.box(CX - 1.0, CX + 1.0, -0.1, 1.0, -FZ - 2.2, -FZ - 1.2, WOOD)
FS.box(CX - 1.05, CX + 1.05, 0.2, 0.35, -FZ - 2.25, -FZ - 1.15, GOLD2)
FS.prism_zy([(-FZ - 1.2, 1.0), (-FZ - 1.2, 2.2), (-FZ - 0.95, 2.2), (-FZ - 0.95, 1.0)], CX - 1.0, CX + 1.0, WOOD)
coin_pile(FS, CX, -FZ - 1.7, 1.0, 0.9, seed=3)
D.palm(FS, (8.2, -0.1, -FZ - 2.0), (-0.8, -0.3), 7.0)
F.objects(False)
# чёрный флаг со скрещёнными костями на крыше-скате
FS.box(-10.0 - 0.07, -10.0 + 0.07, 15.9, 18.9, -FZ - 1.9, -FZ - 1.76, WOOD2)
FS.box(-12.8, -10.07, 16.4, 18.4, -FZ - 1.86, -FZ - 1.8, BLACK)
for e in (-1, 1):
    a = math.radians(30 if e > 0 else 150)
    cx, cy = -11.4, 17.4
    FS.prism_xy([(cx - 0.9 * math.cos(a) - 0.08 * math.sin(a), cy - 0.9 * math.sin(a) + 0.08 * math.cos(a)),
                 (cx + 0.9 * math.cos(a) - 0.08 * math.sin(a), cy + 0.9 * math.sin(a) + 0.08 * math.cos(a)),
                 (cx + 0.9 * math.cos(a) + 0.08 * math.sin(a), cy + 0.9 * math.sin(a) - 0.08 * math.cos(a)),
                 (cx - 0.9 * math.cos(a) + 0.08 * math.sin(a), cy - 0.9 * math.sin(a) - 0.08 * math.cos(a))], -FZ - 1.9, -FZ - 1.86, "F4ECD8")

# ══ ИНТЕРЬЕР: таверна ═════════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.5
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), WOOD3)
for k in range(-13, 14):
    if k % 2:
        IQ.box(1.2 * k, 1.2 * k + 1.2, 0.02, 0.04, ZF + 0.9, ZB - 0.9, WOOD)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, PLASTER2)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 3.0, WOOD)
        slab(IS, axis, fixed, out, 1.05, a0, a1, 3.0, 3.3, WOOD2)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, PLASTER2)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, WOOD2)
    for k in range(int(2 * half // 3.6) + 1):
        a = -half + 0.2 + 3.6 * k
        if a + 0.5 <= half and not (gap and abs(a + 0.25) < DOOR[0] + 1.0):
            slab(IS, axis, fixed, out, 1.05, a, a + 0.5, 3.3, C, WOOD2)
for k in range(-3, 4):
    IS.box(-W, W, C - 0.8, C - 0.2, 4.4 * k - 0.3, 4.4 * k + 0.3, WOOD2)
# стойка с бочками-кранами у дальней стены, карта сокровищ
F.objects(True)
IS.box(-9.0, 9.0, 0.0, 3.0, ZF + 3.0, ZF + 4.4, WOOD)
IS.box(-9.2, 9.2, 3.0, 3.25, ZF + 2.9, ZF + 4.6, WOOD3)
for k in range(5):
    x = -8.0 + 4.0 * k
    IS.prism_xy(K.ngon(x, 5.4, 1.0, 10), ZF + 1.0, ZF + 2.8, WOOD3)
    for zz in (ZF + 1.3, ZF + 2.5):
        IS.prism_xy(K.ngon(x, 5.4, 1.04, 10), zz - 0.08, zz + 0.08, BLACK)
    IS.box(x - 0.08, x + 0.08, 4.6, 5.0, ZF + 2.8, ZF + 3.3, GOLD2)
    IS.box(x - 1.2, x + 1.2, 4.0, 4.4, ZF + 0.9, ZF + 2.9, WOOD2)
    mug(IS, x - 0.5, ZF + 3.6, 3.25)
F.objects(False)
IS.box(-4.0, 4.0, 8.0, 13.0, ZF + 0.88, ZF + 0.96, "E8D0A0")  # карта
IS.frame_xy(K.rect(-4.3, 4.3, 7.7, 13.3), K.rect(-4.0, 4.0, 8.0, 13.0), ZF + 0.88, ZF + 1.05, WOOD2)
for k in range(6):
    IS.box(-3.0 + 1.0 * k, -2.6 + 1.0 * k, 9.2 + 0.5 * (k % 3), 9.3 + 0.5 * (k % 3), ZF + 0.96, ZF + 1.0, RED)
IS.prism_xy([(2.0, 11.0), (2.6, 11.6), (2.0, 12.2), (1.4, 11.6)], ZF + 0.96, ZF + 1.0, RED)
IS.prism_xy([(-3.4, 9.2), (-2.8, 12.4), (-2.2, 9.6)], ZF + 0.96, ZF + 1.0, "3A8A4A")
# столы с кружками и лавками
F.objects(True)
for s in (-1, 1):
    for z in (-10.0, -2.0, 5.0):
        x = s * (W - 4.6)
        IS.box(x - 1.4, x + 1.4, 2.4, 2.7, z - 2.0, z + 2.0, WOOD3)
        for e in (-1, 1):
            IS.box(x + e * 1.1 - 0.15, x + e * 1.1 + 0.15, 0.0, 2.4, z - 1.6, z + 1.6, WOOD2)
            IS.box(x + e * 2.4 - 0.5, x + e * 2.4 + 0.5, 1.3, 1.55, z - 1.8, z + 1.8, WOOD)
            IS.box(x + e * 2.4 - 0.1, x + e * 2.4 + 0.1, 0.0, 1.3, z - 1.4, z + 1.4, WOOD2)
        for k in range(3):
            mug(IS, x - 0.6 + 0.6 * k, z - 0.8 + 0.8 * k, 2.7)
cannon(IS, -W + 2.6, -13.8, 0.0, face=1)  # пушка в углу зала
F.objects(False)
# люстра-штурвал со свечами над постаментом
px, pz = PED
IS.frame_xz(K.ngon(px, pz, 3.0, 12), K.ngon(px, pz, 2.6, 12), C - 4.2, C - 3.9, WOOD)
for k in range(8):
    a = 2 * math.pi * k / 8
    beam(IS, (px, C - 4.05, pz), (px + 3.5 * math.cos(a), C - 4.05, pz + 3.5 * math.sin(a)), 0.18, 0.18, WOOD2)
    IS.prism_xz(K.ngon(px + 2.8 * math.cos(a + 0.4), pz + 2.8 * math.sin(a + 0.4), 0.12, 6), C - 3.9, C - 3.4, "F4ECD8")
    IG.prism_xz(K.ngon(px + 2.8 * math.cos(a + 0.4), pz + 2.8 * math.sin(a + 0.4), 0.07, 4), C - 3.4, C - 3.2, "FFD070")
for k in range(4):
    a = math.pi / 2 * k + math.pi / 4
    IS.box(px + 2.8 * math.cos(a) - 0.03, px + 2.8 * math.cos(a) + 0.03, C - 3.9, C - 0.8, pz + 2.8 * math.sin(a) - 0.03,
           pz + 2.8 * math.sin(a) + 0.03, BLACK)
# горки монет вокруг и сам постамент — гора золота на дощатом помосте
F.objects(True)
for k, (x, z, r) in enumerate(((-6.0, -8.6, 1.2), (6.2, -8.0, 1.0), (-6.4, 1.6, 0.9), (6.0, 2.4, 1.1))):
    coin_pile(IS, x, z, 0.0, r, seed=k)
F.objects(False)
IR.box(px - 4.0, px + 4.0, 0.0, 0.5, pz - 4.0, pz + 4.0, WOOD2)
IS.prism_xz(K.octa(px, pz, 3.7, 3.7, 1.4), 0.5, 1.0, GOLD2)
IS.prism_xz(K.octa(px, pz, 3.2, 3.2, 1.2), 1.0, TOP, GOLD)
for k in range(10):
    a = 2 * math.pi * k / 10 + 0.2
    x, z = px + 3.45 * math.cos(a), pz + 3.45 * math.sin(a)
    IS.prism_xz(K.ngon(x, z, 0.22, 8), 0.8 + 0.1 * (k % 3), 1.1 + 0.1 * (k % 3), GOLD)
for k in range(5):
    a = 2 * math.pi * k / 5 + 0.7
    IS.prism_xz(K.octa(px + 2.9 * math.cos(a), pz + 2.9 * math.sin(a), 0.2, 0.2, 0.07), TOP - 0.05, TOP + 0.25, GEMS[k % 4])
B.lift_leaves(IS, WOOD2, GOLD2)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 16.2, -FZ, FZ, PLASTER)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "8A7A60")
SL.prism_zy([(-FZ - 2.4, 16.2), (FZ + 2.4, 16.2), (FZ + 0.88, 18.9), (-FZ - 0.88, 18.9)], -FX - 2.4, FX + 2.4, "6A3A2A")
SL.prism_xy(hull, NZ - 1.6, NZ + 0.2, WOOD)

F.build(exhibit=(PED[0], TOP, PED[1], 2.8), lamps=[("Hall", (0, 14, 6), 1600, (1.0, 0.88, 0.7)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.97, 0.92)),
                                                   ("Bar", (0, 6, ZF + 5), 600, (1.0, 0.8, 0.5))])
