"""Этаж «Перекати-поле-бегун» музея-небоскрёба (девятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — салун городка Дикого Запада. Снаружи — дощатый дом с высоким ступенчатым фальш-фасадом, крытая
галерея на столбах над дощатым тротуаром с перилами, двери-«крылья» салуна, вывеска с подковой, окна второго
яруса с балкончиком, коновязь, корыто с водой, бочки, колесо фургона у стены, кактусы, катящиеся шары перекати-поля.
Внутри — салун: длинная стойка с латунной подножкой и полками бутылок перед зеркалом, пианино, круглые столы со
стульями, лестница на галерею вдоль дальней стены, звёзды-шерифские значки и подковы на стенах, лампы на цепях;
экспонат — на круглой деревянной сцене-бочке, окружённой кольцом перекати-поля.
Запуск: blender --background --factory-startup --python scripts/blender/floor_saloon.py -- <репо> <превью>
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
from floorbase import C, FX, FZ, W, ZB, ZF, beam, rng, slab  # noqa: E402

PLANK, PLANK2, DARKW, RED, CREAM, GOLD = "B07A48", "8A5A32", "5A3A22", "A83A2A", "EFE0C0", "E8B848"
BRASS, BOTTLE, BOTTLE2, GREEN, GLASS, STRAW = "D8A840", "3A8A4A", "7A3A2A", "4A8A3A", "F8E0A8", "C89A50"

F = B.Floor("SA", "TumbleweedRunner", quiet=(PLANK2, "C8A070", "8A5A32"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def tumbleweed(p, x, z, y, r):
    """Шар перекати-поля: перекрещённые ветки."""
    for k in range(5):
        a = math.pi * k / 5
        beam(p, (x - r * math.cos(a), y + r + r * 0.4 * math.sin(2 * a), z - r * math.sin(a)),
             (x + r * math.cos(a), y + r - r * 0.4 * math.sin(2 * a), z + r * math.sin(a)), 0.12, 0.12, STRAW)
        beam(p, (x, y + r - r * math.cos(a) * 0.95, z - r * math.sin(a) * 0.5), (x + 0.2, y + r + r * math.cos(a) * 0.95, z + r * math.sin(a) * 0.5),
             0.1, 0.1, STRAW)


def cactus(p, x, z, y, h):
    p.prism_xz(K.ngon(x, z, 0.35, 8), y, y + h, GREEN)
    p.box(x, x + 0.9, y + h * 0.45, y + h * 0.45 + 0.5, z - 0.25, z + 0.25, GREEN)
    p.prism_xz(K.ngon(x + 0.75, z, 0.25, 6), y + h * 0.45, y + h * 0.8, GREEN)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, PLANK, DARKW, DARKW, "C8A070", "4A3424", roof="none", boards=(1.2, PLANK2), top=15.2,
         side=S.side_windows(F, CREAM, GLASS, kind="tall", y0=6.0, y1=10.8, w=2.0, xs=(-12.25, -4.75, 2.75, 10.25)))
# ступенчатый фальш-фасад над крышей
FR.prism_xy([(-FX - 0.2, 15.2), (FX + 0.2, 15.2), (FX + 0.2, 16.6), (11.0, 16.6), (11.0, 17.6), (6.0, 17.6), (6.0, 18.8),
             (-6.0, 18.8), (-6.0, 17.6), (-11.0, 17.6), (-11.0, 16.6), (-FX - 0.2, 16.6)], -FZ - 1.3, -FZ - 0.88, PLANK)
FS.box(-6.3, 6.3, 18.6, 18.9, -FZ - 1.5, -FZ - 0.88, DARKW)
for e in (-1, 1):
    FS.box(e * 6.0 - 0.15, e * 6.0 + 0.15, 15.2, 18.6, -FZ - 1.45, -FZ - 1.3, DARKW)
    FS.box(*sorted((e * 11.0, e * (FX + 0.2))), 16.5, 16.8, -FZ - 1.45, -FZ - 0.88, DARKW)
    FS.box(*sorted((e * 6.0, e * 11.0)), 17.5, 17.8, -FZ - 1.45, -FZ - 0.88, DARKW)
# вывеска: доска с подковой и звёздами
FS.box(-5.0, 5.0, 15.6, 17.8, -FZ - 1.6, -FZ - 1.3, RED)
FS.frame_xy(K.rect(-5.3, 5.3, 15.3, 18.1), K.rect(-5.0, 5.0, 15.6, 17.8), -FZ - 1.7, -FZ - 1.3, GOLD)
for k in range(9):
    a0, a1 = math.radians(-40 + 260 * k / 9), math.radians(-40 + 260 * (k + 1) / 9)
    beam(FS, (0.75 * math.cos(a0), 16.7 + 0.75 * math.sin(a0), -FZ - 1.7), (0.75 * math.cos(a1), 16.7 + 0.75 * math.sin(a1), -FZ - 1.7),
         0.25, 0.1, GOLD, up=(0, 0, 1))
for x in (-3.4, 3.4):
    FS.prism_xy([(x + 0.55 * math.cos(math.pi / 2 + k * math.pi / 5) * (1 if k % 2 == 0 else 0.45),
                  16.7 + 0.55 * math.sin(math.pi / 2 + k * math.pi / 5) * (1 if k % 2 == 0 else 0.45)) for k in range(10)],
                -FZ - 1.75, -FZ - 1.6, CREAM)
# второй ярус: окна со ставнями и балкончик
for x in (-13.0, -7.4, 5.4, 11.0):
    S.window(F, "z", -FZ, -1, x, 9.6, 13.4, 2.0, CREAM, GLASS, kind="tall")
    for e in (-1, 1):
        FS.box(*sorted((x + (1.0 + e * 1.0) - e * 0.05, x + (1.0 + e * 1.0) + e * 1.0)), 9.4, 13.6, -FZ - 1.05, -FZ - 0.88, GREEN)
FS.box(-4.4, 4.4, 9.2, 9.5, -FZ - 2.4, -FZ - 0.88, PLANK2)
for k in range(12):
    x = -4.2 + 8.4 * k / 11
    FS.box(x - 0.08, x + 0.08, 9.5, 10.7, -FZ - 2.35, -FZ - 2.2, DARKW)
FS.box(-4.4, 4.4, 10.7, 10.9, -FZ - 2.4, -FZ - 2.1, DARKW)
FG.box(-2.0, 2.0, 9.6, 13.4, -FZ - 0.92, -FZ - 0.88, GLASS)
FS.frame_xy(K.rect(-2.3, 2.3, 9.5, 13.7), K.rect(-2.0, 2.0, 9.6, 13.4), -FZ - 1.1, -FZ - 0.88, CREAM)
# крытая галерея: навес на столбах над тротуаром
FS.loft([(-FX - 0.2, 8.8, -FZ - 0.88), (FX + 0.2, 8.8, -FZ - 0.88), (FX + 0.2, 9.1, -FZ - 0.88), (-FX - 0.2, 9.1, -FZ - 0.88)],
        [(-FX - 0.2, 8.0, -FZ - 2.8), (FX + 0.2, 8.0, -FZ - 2.8), (FX + 0.2, 8.3, -FZ - 2.8), (-FX - 0.2, 8.3, -FZ - 2.8)], DARKW)
for k in range(8):
    x = -FX + 0.4 + (2 * FX - 0.8) * k / 7
    FS.box(x - 0.2, x + 0.2, 0.5, 8.1, -FZ - 2.6, -FZ - 2.2, PLANK2)
    FS.box(x - 0.35, x + 0.35, 7.6, 7.9, -FZ - 2.75, -FZ - 2.05, DARKW)
FR.box(-FX - 0.2, FX + 0.2, -0.1, 0.5, -FZ - 2.8, -FZ - 0.88, PLANK)
for k in range(16):
    x = -FX + 1.1 * k + 0.5
    FS.box(x - 0.03, x + 0.03, 0.5, 0.52, -FZ - 2.8, -FZ - 0.88, DARKW)
for xs in ((-FX + 0.4, -5.0), (5.0, FX - 0.4)):
    FS.box(xs[0], xs[1], 3.0, 3.2, -FZ - 2.5, -FZ - 2.3, PLANK2)
# двери-крылья салуна и окна первого яруса
FS.box(-2.6, 2.6, 0.5, 7.0, -FZ - 0.92, -FZ - 0.88, "2A1A10")
for e in (-1, 1):
    FS.prism_xy([(e * 0.08, 2.0), (e * 2.2, 2.0), (e * 2.2, 5.4), (e * 1.2, 5.9), (e * 0.08, 5.6)], -FZ - 1.2, -FZ - 1.0, PLANK2)
    for k in range(4):
        FS.box(*sorted((e * (0.3 + 0.45 * k), e * (0.5 + 0.45 * k))), 2.4, 5.2, -FZ - 1.25, -FZ - 1.2, DARKW)
for x in (-14.0, -8.6, 4.8, 10.2):
    FG.box(x, x + 3.6, 2.0, 6.4, -FZ - 0.92, -FZ - 0.88, GLASS)
    FS.frame_xy(K.rect(x - 0.3, x + 3.9, 1.7, 6.7), K.rect(x, x + 3.6, 2.0, 6.4), -FZ - 1.1, -FZ - 0.88, CREAM)
    FS.box(x + 1.75, x + 1.85, 2.0, 6.4, -FZ - 1.0, -FZ - 0.9, CREAM)
# коновязь, корыто, бочки, колесо, кактусы, перекати-поле
F.objects(True)
for x in (-16.4, -12.0):
    FS.box(x - 0.15, x + 0.15, -0.1, 2.4, -FZ - 3.3, -FZ - 3.0, PLANK2)
FS.box(-16.6, -11.8, 2.0, 2.3, -FZ - 3.3, -FZ - 3.0, PLANK2)
FS.box(12.0, 15.6, 0.5, 1.6, -FZ - 2.0, -FZ - 1.2, PLANK2)
FG.box(12.2, 15.4, 1.4, 1.5, -FZ - 1.9, -FZ - 1.3, "6AB8E0")
D.barrel(FS, 7.6, -FZ - 1.6, y=0.5, r=0.7, h=1.6)
D.barrel(FS, 9.0, -FZ - 1.5, y=0.5, r=0.6, h=1.4)
S.annulus(FS, (-9.0, 2.0, -FZ - 1.1), (0, 0, -1), 1.3, 1.6, 0.15, DARKW, seg=14)
for k in range(6):
    a = math.pi * k / 6
    beam(FS, (-9.0 - 1.3 * math.cos(a), 2.0 - 1.3 * math.sin(a), -FZ - 1.17), (-9.0 + 1.3 * math.cos(a), 2.0 + 1.3 * math.sin(a), -FZ - 1.17),
         0.12, 0.1, PLANK2, up=(0, 0, 1))
cactus(FS, -FX - 1.6, -FZ - 1.6, -0.1, 3.4)
cactus(FS, FX + 1.4, -FZ - 2.0, -0.1, 2.6)
tumbleweed(FS, -3.6, -FZ - 3.6, -0.1, 0.8)
tumbleweed(FS, 3.0, -FZ - 3.4, -0.1, 0.6)
F.objects(False)

# ══ ИНТЕРЬЕР: салун ═══════════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.4
S.interior(F, "C89060", "8A5A32", DARKW, DARKW, wain=(3.6, PLANK2), beams=(6, DARKW), beam_dir="x")
for k in range(26):  # доски пола
    x = -W + 0.65 + 1.3 * k
    IS.box(x - 0.03, x + 0.03, 0.02, 0.05, ZF, ZB, DARKW)
F.objects(True)
# стойка вдоль правой (по входу) стены, подножка, полки бутылок и зеркало
BX = W - 0.88
IS.box(BX - 7.0, BX - 5.4, 0.0, 3.6, -12.0, 4.0, PLANK2)
IS.box(BX - 7.3, BX - 5.2, 3.6, 3.9, -12.3, 4.3, DARKW)
IS.box(BX - 7.4, BX - 7.2, 0.4, 0.6, -12.0, 4.0, BRASS)
IG.box(BX - 0.2, BX, 5.0, 10.0, -10.0, 2.0, "4E5E66")  # старое зеркало — тёмное, с бликами, а не белое пятно
for z0 in (-6.0, -2.0):  # три створки
    IS.box(BX - 0.28, BX - 0.2, 5.0, 10.0, z0 - 0.1, z0 + 0.1, GOLD)
for z, y, h in ((-9.2, 6.0, 2.6), (-5.0, 6.8, 2.0), (-0.8, 5.8, 2.4)):  # косые блики
    IG.prism_zy([(z, y), (z + 0.5, y), (z + 1.3, y + h), (z + 0.8, y + h)], BX - 0.24, BX - 0.2, "8A9CA4")
IS.frame_zy(K.rect(-10.4, 2.4, 4.6, 10.4), K.rect(-10.0, 2.0, 5.0, 10.0), BX - 0.3, BX, GOLD)
for y in (3.4, 4.6, 11.0):
    IS.box(BX - 1.2, BX, y - 0.15, y, -12.0, 4.0, PLANK2)
    for k in range(14):
        z = -11.4 + 1.1 * k
        col = (BOTTLE, BOTTLE2, GOLD, "4A6AA8")[int(rng(k, y) * 4)]
        IS.prism_xz(K.ngon(BX - 0.6, z, 0.22, 6), y, y + 0.6, col)
        IS.prism_xz(K.ngon(BX - 0.6, z, 0.09, 6), y + 0.6, y + 0.95, col)
for k in range(4):  # табуреты у стойки
    z = -10.0 + 4.0 * k
    IS.prism_xz(K.ngon(BX - 8.2, z, 0.6, 8), 2.4, 2.7, RED)
    IS.box(BX - 8.3, BX - 8.1, 0.0, 2.4, z - 0.1, z + 0.1, BRASS)
# пианино у левой стены
PX = -W + 0.88
IS.box(PX, PX + 2.0, 0.0, 5.6, 6.0, 12.0, DARKW)
IS.box(PX + 2.0, PX + 3.0, 2.6, 3.0, 6.2, 11.8, DARKW)
for k in range(20):
    IS.box(PX + 2.05, PX + 2.9, 3.0, 3.1, 6.3 + 0.27 * k, 6.4 + 0.27 * k - 0.04, CREAM if k % 3 else "1A1A1A")
IS.box(PX + 3.6, PX + 4.6, 0.0, 2.2, 8.2, 9.8, PLANK2)
# круглые столы со стульями
for (x, z) in ((-9.0, -1.0), (-9.0, -8.0), (9.0, 8.0)):
    IS.prism_xz(K.ngon(x, z, 1.5, 10), 2.6, 2.8, PLANK)
    IS.prism_xz(K.ngon(x, z, 0.2, 6), 0.0, 2.6, DARKW)
    for k in range(3):
        a = 2 * math.pi * k / 3 + x
        cx, cz = x + 2.1 * math.cos(a), z + 2.1 * math.sin(a)
        IS.box(cx - 0.55, cx + 0.55, 1.6, 1.8, cz - 0.55, cz + 0.55, PLANK2)
        for ex in (-0.4, 0.4):
            for ez in (-0.4, 0.4):
                IS.box(cx + ex - 0.07, cx + ex + 0.07, 0.0, 1.6, cz + ez - 0.07, cz + ez + 0.07, DARKW)
    IS.box(x - 0.3, x + 0.3, 2.8, 3.0, z - 0.4, z + 0.4, "E8E0D0")
F.objects(False)
# галерея-балкон вдоль дальней стены и лестница
GY = 8.6
IR.box(-W + 0.88, W - 0.88, GY, GY + 0.5, ZF + 0.88, ZF + 4.0, PLANK2)
for k in range(15):
    x = -W + 1.6 + (2 * W - 3.2) * k / 14
    IS.box(x - 0.1, x + 0.1, GY + 0.5, GY + 2.4, ZF + 3.8, ZF + 4.0, DARKW)
IS.box(-W + 0.88, W - 0.88, GY + 2.4, GY + 2.6, ZF + 3.7, ZF + 4.1, PLANK2)
for x in (-10.0, 10.0):
    IS.box(x - 0.3, x + 0.3, 0.0, GY, ZF + 3.4, ZF + 4.0, PLANK2)
for k in range(10):
    t = (k + 1) / 10
    IS.box(-W + 0.88, -W + 3.4, GY * t - 0.25, GY * t, ZF + 4.0 + 7.0 * (1 - t), ZF + 4.8 + 7.0 * (1 - t), PLANK)
for k in range(3):  # двери номеров на галерее
    x = -6.0 + 6.0 * k
    IS.box(x - 1.0, x + 1.0, GY + 0.5, GY + 4.6, ZF + 0.88, ZF + 1.0, RED)
    IS.box(x + 0.5, x + 0.7, GY + 2.4, GY + 2.6, ZF + 1.0, ZF + 1.1, BRASS)
# значки-звёзды и подковы на стенах
for k, z in enumerate((-8.0, 0.0, 8.0)):
    x = -W + 0.88
    IS.prism_zy([(z + 0.9 * math.cos(math.pi / 2 + j * math.pi / 5) * (1 if j % 2 == 0 else 0.45),
                  11.6 + 0.9 * math.sin(math.pi / 2 + j * math.pi / 5) * (1 if j % 2 == 0 else 0.45)) for j in range(10)],
                x, x + 0.12, GOLD)
# лампы на цепях
for x, z in ((-5.0, -6.0), (5.0, -6.0), (-5.0, 4.0), (5.0, 4.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.0, C - 0.8, z - 0.03, z + 0.03, "3A3A40")
    D.lantern(IS, IG, x, C - 4.0, z, s=1.1, cap=DARKW, light="FFD070")
# постамент: круглая сцена-бочка в кольце перекати-поля
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 3.9, 16), 0.0, TOP - 0.3, PLANK)
for k in range(16):
    a = 2 * math.pi * (k + 0.5) / 16
    IS.box(px + 3.88 * math.cos(a) - 0.06, px + 3.88 * math.cos(a) + 0.06, 0.0, TOP - 0.3, pz + 3.88 * math.sin(a) - 0.06,
           pz + 3.88 * math.sin(a) + 0.06, PLANK2)
for y in (0.15, TOP - 0.5):
    S.annulus(IS, (px, y, pz), (0, 1, 0), 3.85, 4.0, 0.12, "3A3A40", seg=16)
IS.prism_xz(K.ngon(px, pz, 3.6, 16), TOP - 0.3, TOP, RED)
F.objects(True)
for k in range(6):
    a = 2 * math.pi * k / 6 + 0.3
    tumbleweed(IS, px + 4.9 * math.cos(a), pz + 4.9 * math.sin(a), 0.0, 0.55)
F.objects(False)
B.lift_leaves(IS, PLANK2, GOLD)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, PLANK, "C8A070", DARKW, top=15.2, roof="none")
SL.prism_xy([(-FX - 0.2, 15.9), (FX + 0.2, 15.9), (FX + 0.2, 16.6), (6.0, 16.6), (6.0, 18.8), (-6.0, 18.8), (-6.0, 16.6),
             (-FX - 0.2, 16.6)], -FZ - 1.3, -FZ, PLANK)
SL.box(-FX - 0.2, FX + 0.2, 8.0, 8.6, -FZ - 2.8, -FZ, DARKW)

F.build(exhibit=(PED[0], TOP, PED[1], 3.0), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.9, 0.76)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.95, 0.86)),
                                                   ("Bar", (12, 8, -4), 700, (1.0, 0.8, 0.5))])
