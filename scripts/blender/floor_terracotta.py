"""Этаж «Терракотовый воин» музея-небоскрёба (вторая партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — императорский павильон над раскопом. Снаружи — белая каменная терраса с балюстрадой, красные
лакированные колонны, между ними — решётчатые окна, пояс кронштейнов-доугунов в зелени и золоте, двухъярусная
крыша из глазурованной черепицы (жёлто-зелёной) с загнутыми вверх углами-драконами; спереди — красные врата
с рядами золотых гвоздей и пустой табличкой в раме, под карнизом — красные фонари.
Внутри — раскоп: пол из утоптанной земли, траншеи с земляными перегородками под деревянными балками, в траншеях —
ряды терракотовых воинов (без лиц), стены — слои глины, выше — красная галерея с перилами, потолок — кессоны
с росписью; воин-экспонат на белом постаменте с драконьими ступенями, вокруг — бронзовые треножники, фонари.
Запуск: blender --background --factory-startup --python scripts/blender/floor_terracotta.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab, taper  # noqa: E402

RED, RED2, GOLD, GOLD2, JADE, JADE2 = "B8282A", "8E1E22", "E8B84A", "B8892E", "2E8B57", "1F6A40"
TILE, TILE2, MARBLE, MARBLE2, WOOD, WOOD2 = "E8B030", "C98A1A", "EAE4D6", "CFC6B4", "5A3A24", "3E2818"
CLAY, CLAY2, EARTH, EARTH2, EARTH3, BRONZE = "C2845A", "A86E4A", "8A6A4A", "9E7C58", "765A3E", "6E7A5A"
BLUE, LANTERN, LANTERN2 = "2E5A9A", "FF4A3A", "FFB040"

F = B.Floor("TW", "TerracottaWarrior", quiet=(EARTH, EARTH2, EARTH3, MARBLE2), bevel_min=1.0, keep_arch=True)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def lantern(p, g, x, y, z, s=1.0):
    """Красный фонарь: золотые крышки, светящийся корпус, кисть."""
    F.objects(True)
    p.box(x - 0.04, x + 0.04, y + 0.9 * s, y + 1.6 * s, z - 0.04, z + 0.04, GOLD2)
    p.prism_xz(K.octa(x, z, 0.45 * s, 0.45 * s, 0.18 * s), y + 0.75 * s, y + 0.9 * s, GOLD)
    g.prism_xz(K.octa(x, z, 0.7 * s, 0.7 * s, 0.29 * s), y - 0.55 * s, y + 0.75 * s, LANTERN)
    p.prism_xz(K.octa(x, z, 0.45 * s, 0.45 * s, 0.18 * s), y - 0.7 * s, y - 0.55 * s, GOLD)
    p.box(x - 0.08, x + 0.08, y - 1.3 * s, y - 0.7 * s, z - 0.08, z + 0.08, LANTERN2)
    F.objects(False)


def warrior(p, x, z, facing=-1):
    """Терракотовый воин без лица: ноги, полы халата, панцирь, руки, голова с пучком."""
    F.objects(True)
    f = facing
    for s in (-1, 1):
        p.box(x + s * 0.12, x + s * 0.42, 0.0, 1.3, z - 0.22, z + 0.22, CLAY2)
    p.prism_xz(K.octa(x, z, 0.62, 0.42, 0.15), 1.3, 2.4, CLAY)
    p.prism_xz(K.octa(x, z, 0.58, 0.4, 0.14), 2.4, 3.4, CLAY2)
    for k in range(3):  # пластины панциря
        p.box(x - 0.6, x + 0.6, 2.5 + 0.3 * k, 2.62 + 0.3 * k, z + f * 0.4, z + f * 0.44, CLAY)
    for s in (-1, 1):
        p.box(x + s * 0.58, x + s * 0.82, 2.2, 3.35, z - 0.2, z + 0.2, CLAY)
    p.box(x - 0.2, x + 0.2, 3.4, 3.6, z - 0.18, z + 0.18, CLAY2)
    p.box(x - 0.3, x + 0.3, 3.6, 4.25, z - 0.3, z + 0.3, CLAY)
    p.box(x - 0.14, x + 0.14, 4.25, 4.5, z - 0.05, z + 0.25, CLAY2)
    F.objects(False)


# ══ ФАСАД: императорский павильон ════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, WOOD2, WOOD2, RED2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    # терраса: белый камень, балюстрада со столбиками
    slab(FR, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, 0.6, MARBLE2)
    slab(FS, axis, fixed, out, 2.95, -half - 2.95, half + 2.95, 0.6, 0.85, MARBLE)
    n = int(2 * half // 3.4)
    for k in range(n + 1):
        a = -half - 1.4 + (2 * half + 2.8) * k / n
        if fi == 0 and abs(a) < 6.0:
            continue
        slab(FS, axis, fixed, out, 2.7, a - 0.22, a + 0.22, 0.85, 2.3, MARBLE)
    for a0, a1 in (((-half - 2.6, -6.0), (6.0, half + 2.6)) if fi == 0 else ((-half - 2.6, half + 2.6),)):
        slab(FS, axis, fixed, out, 2.6, a0, a1, 1.9, 2.1, MARBLE)
    # стена: тёмное дерево, красные колонны, решётчатые окна, нижние доски
    slab(FR, axis, fixed, out, 0.88, -half, half, 0.85, 3.0, RED2)
    nb = 6 if axis == "z" else 5
    bw = 2 * half / nb
    for i in range(nb + 1):
        a = -half + bw * i
        slab(FS, axis, fixed, out, 1.5, a - 0.6, a + 0.6, 0.85, 12.6, RED)
        slab(FS, axis, fixed, out, 1.6, a - 0.75, a + 0.75, 0.85, 1.3, MARBLE2)
    for i in range(nb):
        a0, a1 = -half + bw * i + 0.6, -half + bw * (i + 1) - 0.6
        if fi == 0 and abs((a0 + a1) / 2) < 4.0:
            continue
        slab(FS, axis, fixed, out, 1.0, a0, a1, 3.0, 11.0, GOLD2)
        slab(FS, axis, fixed, out, 1.05, a0 + 0.25, a1 - 0.25, 3.25, 10.75, "2A1A12")
        for k in range(1, 5):  # решётка: вертикали и горизонтали
            a = a0 + (a1 - a0) * k / 5
            slab(FS, axis, fixed, out, 1.12, a - 0.07, a + 0.07, 3.25, 10.75, GOLD)
        for k in range(1, 5):
            y = 3.25 + 7.5 * k / 5
            slab(FS, axis, fixed, out, 1.12, a0 + 0.25, a1 - 0.25, y - 0.07, y + 0.07, GOLD)
        slab(FS, axis, fixed, out, 1.0, a0, a1, 11.0, 12.6, JADE)
    # пояс доугунов: ступенчатые кронштейны (зелень, синь, золото)
    slab(FS, axis, fixed, out, 1.7, -half - 1.7, half + 1.7, 12.6, 13.1, BLUE)
    for k in range(int(2 * half // 2.6) + 1):
        a = -half + 2.6 * k
        slab(FS, axis, fixed, out, 2.0, a - 0.35, a + 0.35, 13.1, 13.6, JADE)
        slab(FS, axis, fixed, out, 2.4, a - 0.6, a + 0.6, 13.6, 14.0, GOLD)
    # нижний ярус крыши: скат черепицы с выносом, рёбра, загнутые углы
    prof = [(0.0, 16.0), (0.0, 14.0), (3.0, 13.4), (3.2, 13.9), (2.6, 14.0)]
    B.chamfer(FS, axis, fixed, out, -half - 3.0, half + 3.0, prof, TILE)
    for k in range(int((2 * half + 4) // 2.2)):
        a = -half - 2.0 + 2.2 * k
        beam(FS, (fixed + out * 0.2, 15.9, a) if axis == "x" else (a, 15.9, fixed + out * 0.2),
             (fixed + out * 3.1, 13.95, a) if axis == "x" else (a, 13.95, fixed + out * 3.1), 0.3, 0.2, TILE2)
    # верхний ярус крыши: малый скат и конёк
    prof2 = [(0.0, 18.6), (0.0, 16.0), (1.4, 15.8), (1.5, 16.3), (0.3, 18.6)]
    B.chamfer(FS, axis, fixed, out, -half - 1.5, half + 1.5, prof2, JADE)
    for k in range(int((2 * half + 2) // 2.2)):
        a = -half - 1.0 + 2.2 * k
        beam(FS, (fixed + out * 0.3, 18.55, a) if axis == "x" else (a, 18.55, fixed + out * 0.3),
             (fixed + out * 1.45, 16.25, a) if axis == "x" else (a, 16.25, fixed + out * 1.45), 0.26, 0.16, JADE2)
    slab(FS, axis, fixed, out, 0.6, -half - 0.6, half + 0.6, 18.6, 19.0, GOLD2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
# загнутые углы крыши — драконьи «хвосты» золотом
for sx in (-1, 1):
    for sz in (-1, 1):
        c = (sx * (FX + 2.8), 13.7, sz * (FZ + 2.8))
        taper(FS, c, (sx * (FX + 4.0), 15.4, sz * (FZ + 4.0)), 0.9, 0.2, GOLD)
        taper(FS, (sx * (FX + 1.3), 16.0, sz * (FZ + 1.3)), (sx * (FX + 2.2), 17.4, sz * (FZ + 2.2)), 0.6, 0.15, GOLD)
# перед: красные врата с золотыми гвоздями, табличка, ступени, фонари
FS.box(-4.0, 4.0, 0.85, 11.0, -FZ - 1.3, -FZ, RED)
FS.box(-0.05, 0.05, 0.85, 11.0, -FZ - 1.4, -FZ - 1.3, GOLD2)
for s in (-1, 1):
    for i in range(4):
        for j in range(6):
            x, y = s * (0.6 + 0.85 * i), 2.0 + 1.5 * j
            FS.prism_xy(K.octa(x, y, 0.2, 0.2, 0.08), -FZ - 1.45, -FZ - 1.3, GOLD)
    FS.prism_xy(K.octa(s * 0.45, 6.0, 0.4, 0.4, 0.16), -FZ - 1.55, -FZ - 1.3, GOLD)  # кольца-ручки
FS.box(-2.6, 2.6, 11.2, 12.4, -FZ - 1.7, -FZ - 1.4, GOLD)
FS.box(-2.3, 2.3, 11.4, 12.2, -FZ - 1.8, -FZ - 1.7, BLUE)
for k in range(3):
    FS.box(-5.0 - k * 0.6, 5.0 + k * 0.6, -1.0, 0.85 - 0.6 * k, -FZ - 2.9 - 0.0, -FZ - 1.0 - 0.6 * k, MARBLE)
for x in (-12.0, -6.0, 6.0, 12.0):
    lantern(FS, FG, x, 11.3, -FZ - 2.3, 1.0)
for s in (-1, 1):
    for z in (-8.0, 8.0):
        lantern(FS, FG, s * (FX + 2.3), 11.3, z, 1.0)

# ══ ИНТЕРЬЕР: раскоп с армией ═════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -2.0)
TOP = 1.4
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), EARTH)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        for r, (y0, y1, color) in enumerate(((0.0, 2.0, EARTH3), (2.0, 3.6, EARTH2), (3.6, 5.6, EARTH),
                                              (5.6, 7.0, EARTH2), (7.0, 9.0, EARTH3), (9.0, 10.6, EARTH2))):
            slab(IQ, axis, fixed, out, 0.88, a0, a1, y0, y1, color)
    if gap:
        slab(IQ, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 10.6, EARTH2)
    # красная галерея с перилами
    slab(IS, axis, fixed, out, 1.6, -half, half, 10.6, 11.0, WOOD)
    slab(IR, axis, fixed, out, 0.88, -half, half, 11.0, 15.2, RED2)
    for k in range(int(2 * half // 2.0) + 1):
        a = -half + 2.0 * k
        slab(IS, axis, fixed, out, 1.4, a - 0.12, a + 0.12, 11.0, 12.4, RED)
        slab(IS, axis, fixed, out, 1.0, a - 0.3, a + 0.3, 11.0, 15.2, RED)
    slab(IS, axis, fixed, out, 1.45, -half, half, 12.3, 12.5, GOLD)
    slab(IS, axis, fixed, out, 1.3, -half, half, 15.2, 15.8, JADE)
    slab(IS, axis, fixed, out, 1.6, -half, half, 15.8, 16.2, GOLD2)
    slab(IR, axis, fixed, out, 0.88, -half, half, 16.2, C, WOOD2)
# кессонный потолок: балки и расписные кессоны
for k in range(-4, 5):
    beam(IS, (-W, C - 0.3, 3.4 * k), (W, C - 0.3, 3.4 * k), 0.4, 0.5, WOOD)
    beam(IS, (3.6 * k, C - 0.3, ZF), (3.6 * k, C - 0.3, ZB), 0.4, 0.5, WOOD)
for i in range(-4, 4):
    for j in range(-4, 4):
        x, z = 3.6 * i + 1.8, 3.4 * j + 1.7
        if abs(x) > 15 or abs(z) > 14:
            continue
        IS.box(x - 1.25, x + 1.25, C - 0.12, C - 0.04, z - 1.2, z + 1.2, (JADE, BLUE)[(i + j) % 2])
        IS.box(x - 0.55, x + 0.55, C - 0.16, C - 0.12, z - 0.55, z + 0.55, GOLD)
# траншеи: земляные перегородки с балками, ряды воинов
for x0 in (-15.5, -10.5, 10.5, 15.5):
    IR.box(x0 - 0.7, x0 + 0.7, 0.0, 1.8, ZF + 1.0, 4.0, EARTH2)
    IS.box(x0 - 0.8, x0 + 0.8, 1.8, 2.1, ZF + 1.0, 4.0, WOOD)
for x in (-13.0, 13.0):
    for z in (-13.0, -9.5, -6.0, -2.5, 1.0):
        warrior(IS, x + (rng(x, z) - 0.5) * 0.3, z, -1)
IR.box(-W, W, 0.0, 1.6, ZF, ZF + 2.4, EARTH2)  # передний вал раскопа
IS.box(-W, W, 1.6, 1.9, ZF, ZF + 2.4, WOOD)
for x in (-7.5, -4.5, 4.5, 7.5):
    warrior(IS, x, ZF + 4.0, -1)
# на валу за экспонатом — чёрная лаковая ширма в золотой раме: терракотовый воин читается на тёмном, а не на рядах
# таких же терракотовых фигур; воины остаются по бокам
LQ = "241A1A"
IR.box(-6.0, 6.0, 1.9, 10.0, ZF + 2.0, ZF + 2.3, LQ)
IS.frame_xy(K.rect(-6.3, 6.3, 1.9, 10.3), K.rect(-6.0, 6.0, 2.2, 10.0), ZF + 1.95, ZF + 2.4, GOLD2)
for x in (-2.0, 2.0):  # створки ширмы
    IS.box(x - 0.1, x + 0.1, 2.2, 10.0, ZF + 2.3, ZF + 2.36, GOLD2)
IS.prism_xy(K.ngon(0.0, 8.6, 0.9, 12), ZF + 2.3, ZF + 2.36, RED)
IS.prism_xy(K.ngon(0.0, 8.6, 0.5, 12), ZF + 2.36, ZF + 2.4, GOLD)
F.objects(True)
# постамент: белый мрамор, ступени-«драконьи пути», бронзовые треножники
px, pz = PED
IR.box(px - 4.8, px + 4.8, 0.0, 0.7, pz - 4.2, pz + 4.2, MARBLE2)
IR.box(px - 4.0, px + 4.0, 0.7, TOP, pz - 3.4, pz + 3.4, MARBLE)
IS.box(px - 4.9, px + 4.9, 0.6, 0.78, pz - 4.3, pz + 4.3, GOLD2)
IS.box(px - 1.4, px + 1.4, 0.0, 1.0, pz + 4.2, pz + 6.2, MARBLE2)
IS.prism_zy([(pz + 4.2, 0.7), (pz + 6.2, 0.0), (pz + 6.2, 0.2), (pz + 4.2, 1.0)], px - 0.8, px + 0.8, JADE)
for x, z in ((-6.5, pz - 3.5), (6.5, pz - 3.5), (-6.5, pz + 3.5), (6.5, pz + 3.5)):
    for e in ((-0.4, -0.3), (0.4, -0.3), (0.0, 0.45)):
        IS.box(x + e[0] - 0.1, x + e[0] + 0.1, 0.0, 1.0, z + e[1] - 0.1, z + e[1] + 0.1, BRONZE)
    IS.prism_xz(K.octa(x, z, 0.75, 0.75, 0.3), 1.0, 2.2, BRONZE)
    IS.prism_xz(K.octa(x, z, 0.85, 0.85, 0.35), 2.2, 2.4, "8A9A70")
    IG.prism_xz(K.octa(x, z, 0.5, 0.5, 0.2), 2.4, 2.55, LANTERN2)
F.objects(False)
# фонари под потолком над постаментом и у лифта
for x, z in ((-4.5, -7.0), (4.5, -7.0), (-4.5, 3.0), (4.5, 3.0), (-7.0, 10.0), (7.0, 10.0)):
    lantern(IS, IG, x, 14.5, z, 1.3)
    IS.box(x - 0.03, x + 0.03, 16.4, C - 0.3, z - 0.03, z + 0.03, GOLD2)
B.lift_leaves(IS, RED, GOLD)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, RED2)
SL.box(-FX - 2.9, FX + 2.9, -1, 0.85, -FZ - 2.9, FZ + 2.9, MARBLE)
SL.box(-FX - 1.5, FX + 1.5, 0.85, 12.6, -FZ - 1.5, FZ + 1.5, RED)
SL.box(-FX - 2.4, FX + 2.4, 12.6, 14.0, -FZ - 2.4, FZ + 2.4, JADE)
SL.box(-FX - 3.2, FX + 3.2, 13.4, 16.0, -FZ - 3.2, FZ + 3.2, TILE)
SL.box(-FX + 1.0, FX - 1.0, 16.0, 19.0, -FZ + 1.0, FZ - 1.0, JADE)
SL.box(-4.0, 4.0, 0.85, 11.0, -FZ - 1.6, -FZ, RED)
for sx in (-1, 1):
    for sz in (-1, 1):
        SL.box(sx * (FX + 2.6), sx * (FX + 4.0), 13.6, 15.4, sz * (FZ + 2.6), sz * (FZ + 4.0), GOLD)

F.build(exhibit=(PED[0], TOP, PED[1], 3.4), lamps=[("Hall", (0, 14, 6), 3000, (1.0, 0.85, 0.75)),
                                                   ("Spot", (0, 13, -2), 3200, (1.0, 0.95, 0.85))])
