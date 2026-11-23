"""Этаж «Бюст Нефертити» музея-небоскрёба (одиннадцатая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — мастерская скульптора в солнечном городе Амарна. Снаружи — светлая вилла с белыми стенами и
голубыми колоннами-пальмами на веранде, над входом — большой солнечный диск Атона с расходящимися лучами,
заканчивающимися ладошками, синий пояс с жёлтыми ромбами, на веранде — заготовки из камня, лестница, корзины,
пальмы в кадках, колодец-шадуф с журавлём, грядки. Внутри — мастерская: подставки-станки с недоделанными
скульптурами (абстрактные головы и вазы без лиц), полки с банками красок и кистями, глыбы известняка, инструменты
на стене (резцы, молотки), эскизы на доске, лучи Атона на потолке; экспонат — на синем постаменте-кубе
с золотой каймой (как музейная тумба).
Запуск: blender --background --factory-startup --python scripts/blender/floor_amarna.py -- <репо> <превью>
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

WHITE, WHITE2, BLUE, BLUE2, GOLD, SAND = "F6F2E6", "DCD6C4", "3A7AC8", "245A9A", "F0C040", "E6CE9A"
LIME, LIME2, PALM, WOOD, WOOD2, CLAY = "E8E0CC", "C8C0A8", "4A9A3A", "A87A48", "6A4A2A", "C86A3A"
RED, TEAL = "C84A3A", "2AA8A0"
PAINTS = (RED, BLUE, GOLD, TEAL, "2A2A30", WHITE)

F = B.Floor("AM", "NefertitiBust", quiet=(WHITE2, SAND, "8AA0C0"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def palm_column(p, x, z, y0, y1, r):
    """Колонна-пальма: голубой ствол с кольцами, капитель из листьев."""
    p.prism_xz(K.ngon(x, z, r, 10), y0, y1 - 1.4, BLUE)
    for y in (y0 + 0.4, y1 - 2.0):
        p.prism_xz(K.ngon(x, z, r + 0.06, 10), y, y + 0.25, GOLD)
    for k in range(8):
        a = 2 * math.pi * k / 8
        taper(p, (x, y1 - 1.4, z), (x + 1.2 * r * 1.6 * math.cos(a), y1 - 0.2, z + 1.2 * r * 1.6 * math.sin(a)), 0.4, 0.12, PALM)
    p.box(x - r * 1.1, x + r * 1.1, y1 - 0.4, y1, z - r * 1.1, z + r * 1.1, GOLD)


def aten(p, x, y, z, r, rays, axis="z", col=GOLD):
    """Диск Атона с лучами-ладошками (в плоскости xy лицом к −z или в xz у потолка)."""
    if axis == "z":
        S.disc(p, (x, y, z), (0, 0, -1), r, 0.25, col, seg=16)
    else:
        S.disc(p, (x, y, z), (0, -1, 0), r, 0.2, col, seg=16)
    for k in range(rays):
        a = math.pi * (1.1 + 0.8 * k / (rays - 1)) if axis == "z" else 2 * math.pi * k / rays
        L = r * 2.6
        if axis == "z":
            beam(p, (x + r * math.cos(a), y + r * math.sin(a), z - 0.12), (x + L * math.cos(a), y + L * math.sin(a), z - 0.12), 0.1, 0.08, col, up=(0, 0, 1))
            p.prism_xy(K.octa(x + (L + 0.15) * math.cos(a), y + (L + 0.15) * math.sin(a), 0.2, 0.2, 0.06), z - 0.18, z - 0.06, col)
        else:
            beam(p, (x + r * math.cos(a), y - 0.05, z + r * math.sin(a)), (x + L * math.cos(a), y - 0.05, z + L * math.sin(a)), 0.18, 0.06, col)
            p.prism_xz(K.octa(x + (L + 0.2) * math.cos(a), z + (L + 0.2) * math.sin(a), 0.28, 0.28, 0.08), y - 0.12, y - 0.02, col)


def bust_blank(p, x, z, y, s, col):
    """Недоделанная абстрактная голова-заготовка: шея, яйцо головы, высокий головной убор (без лица)."""
    p.prism_xz(K.ngon(x, z, 0.35 * s, 8), y, y + 0.6 * s, col)
    p.prism_xz(K.octa(x, z, 0.5 * s, 0.55 * s, 0.18 * s), y + 0.6 * s, y + 1.4 * s, col)
    p.loft([(x - 0.45 * s, y + 1.4 * s, z - 0.5 * s), (x + 0.45 * s, y + 1.4 * s, z - 0.5 * s), (x + 0.45 * s, y + 1.4 * s, z + 0.4 * s),
            (x - 0.45 * s, y + 1.4 * s, z + 0.4 * s)],
           [(x - 0.6 * s, y + 2.3 * s, z - 0.3 * s), (x + 0.6 * s, y + 2.3 * s, z - 0.3 * s), (x + 0.6 * s, y + 2.3 * s, z + 0.9 * s),
            (x - 0.6 * s, y + 2.3 * s, z + 0.9 * s)], BLUE if col == LIME else col)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, WHITE, SAND, BLUE, SAND, "2A3A6A", roof="flat", roof_col=WHITE, top=16.0, band=(10.0, 10.6, BLUE),
         side=S.side_windows(F, BLUE, "3A3A50", kind="rect", y0=11.6, y1=14.2, w=2.0, xs=(-12.25, -4.75, 2.75, 10.25)))
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # жёлтые ромбы по синему поясу
    for k in range(int(2 * half // 1.6)):
        a = -half + 0.8 + 1.6 * k
        d0, d1 = sorted((fixed + out * 1.0, fixed + out * 1.05))
        (FS.prism_zy if axis == "x" else FS.prism_xy)(K.ngon(a, 10.3, 0.35, 4, turn=0.0), d0, d1, GOLD)
# веранда: колонны-пальмы, перекрытие, тень
FR.box(-FX - 0.2, FX + 0.2, 8.8, 9.6, -FZ - 3.0, -FZ - 0.88, WHITE2)
for x in (-15.0, -9.0, -3.0, 3.0, 9.0, 15.0):
    palm_column(FS, x, -FZ - 2.4, -0.1, 8.8, 0.4)
# вход и окна виллы
FS.box(-2.0, 2.0, 1.0, 7.4, -FZ - 0.92, -FZ - 0.88, "2A2A3A")
FS.frame_xy(K.rect(-2.4, 2.4, 1.0, 7.8), K.rect(-2.0, 2.0, 1.0, 7.4), -FZ - 1.1, -FZ - 0.88, BLUE)
for x in (-12.6, -6.6, 5.0, 11.0):
    S.window(F, "z", -FZ, -1, x, 3.6, 7.0, 1.8, BLUE, "3A3A50", kind="rect")
# диск Атона с лучами-ладошками над верандой
aten(FS, 0.0, 14.2, -FZ - 1.0, 1.4, 9)
# заготовки, лестница, корзины, пальмы в кадках, шадуф, грядки
F.objects(True)
for k, x in enumerate((-13.0, -11.2)):
    FS.box(x - 0.7, x + 0.7, -0.1, 1.2 + 0.4 * k, -FZ - 2.4, -FZ - 1.2, LIME2)
bust_blank(FS, -6.0, -FZ - 1.6, -0.1, 1.2, LIME)
for e in (-0.5, 0.5):
    beam(FS, (6.0 + e, -0.1, -FZ - 2.6), (6.0 + e * 0.7, 6.0, -FZ - 1.2), 0.12, 0.12, WOOD)
for k in range(7):
    t = (k + 0.5) / 7
    FS.box(5.5, 6.5, 6.1 * t - 0.06, 6.1 * t + 0.06, -FZ - 2.6 + 1.4 * t - 0.06, -FZ - 2.6 + 1.4 * t + 0.06, WOOD2)
for x in (-1.8, 1.8):
    FS.prism_xz(K.ngon(x, -FZ - 2.4, 0.6, 8), -0.1, 0.8, CLAY)
    D.palm(FS, (x, 0.7, -FZ - 2.4), (0.3 if x > 0 else -0.3, -0.3), 4.0)
SX = FX + 1.2  # шадуф: столб, коромысло, ведро и противовес
FS.box(SX - 0.2, SX + 0.2, -0.1, 5.0, -FZ - 1.8, -FZ - 1.4, WOOD2)
beam(FS, (SX, 5.6, -FZ + 1.2), (SX, 3.4, -FZ - 2.6), 0.2, 0.2, WOOD)
FS.box(SX - 0.03, SX + 0.03, 1.6, 3.4, -FZ - 2.63, -FZ - 2.57, "C8B890")
FS.prism_xz(K.ngon(SX, -FZ - 2.6, 0.35, 8), 1.0, 1.6, CLAY)
FS.prism_xz(K.ngon(SX, -FZ + 1.0, 0.4, 6), 5.2, 6.0, LIME2)
for k in range(3):
    FQ.box(10.4 + 2.2 * k, 12.2 + 2.2 * k, -0.1, 0.3, -FZ - 2.8, -FZ - 2.0, "6A4A2A")
    for j in range(3):
        FS.prism_xz(K.ngon(10.8 + 2.2 * k + 0.5 * j, -FZ - 2.4, 0.22, 5), 0.3, 0.8, PALM)
F.objects(False)

# ══ ИНТЕРЬЕР: мастерская скульптора ═══════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 2.0
S.interior(F, WHITE, SAND, "EEE4CC", BLUE, wain=(2.0, BLUE2), beams=None)
aten(IS, 0.0, C - 0.02, -3.0, 2.0, 12, axis="y")  # лучи Атона на потолке
F.objects(True)
for s in (-1, 1):  # подставки-станки с заготовками вдоль стен
    for k in range(3):
        z = -11.0 + 5.0 * k
        x = s * (W - 3.0)
        IS.box(x - 0.8, x + 0.8, 0.0, 2.6, z - 0.8, z + 0.8, WOOD)
        IS.box(x - 1.0, x + 1.0, 2.6, 2.8, z - 1.0, z + 1.0, WOOD2)
        if (k + (s > 0)) % 2:
            bust_blank(IS, x, z, 2.8, 1.2, (LIME, "C8A070", LIME2)[k])
        else:
            IS.prism_xz(K.ngon(x, z, 0.35, 8), 2.8, 3.2, CLAY)
            IS.prism_xz(K.ngon(x, z, 0.7, 8), 3.2, 4.4, CLAY)
            IS.prism_xz(K.ngon(x, z, 0.3, 8), 4.4, 5.0, CLAY)
# полки с банками красок и кистями у дальней стены
for x0 in (-14.0, 6.0):
    for y in (2.0, 4.6):
        IS.box(x0, x0 + 8.0, y - 0.2, y, ZF + 0.88, ZF + 2.0, WOOD2)
        for k in range(7):
            IS.prism_xz(K.ngon(x0 + 0.6 + 1.1 * k, ZF + 1.5, 0.35, 8), y, y + 0.7, PAINTS[(k + int(y)) % 6])
    for k in range(5):
        IS.box(x0 + 1.0 + 1.4 * k - 0.05, x0 + 1.0 + 1.4 * k + 0.05, 4.6, 5.8, ZF + 1.3, ZF + 1.4, WOOD)
# глыбы известняка
for (x, z, s) in ((-11.0, 6.0, 1.4), (11.0, 5.4, 1.0), (12.6, 7.2, 0.8)):  # у боковых стен — вид от лифта свободен
    IS.box(x - s, x + s, 0.0, 1.6 * s, z - s * 0.9, z + s * 0.9, LIME)
F.objects(False)
for k in range(6):  # инструменты на стене: резцы и молотки
    x = -5.0 + 2.0 * k
    IS.box(x - 0.06, x + 0.06, 6.4, 8.2, ZF + 0.9, ZF + 1.0, WOOD2)
    if k % 2:
        IS.box(x - 0.4, x + 0.4, 8.2, 8.6, ZF + 0.9, ZF + 1.05, "7A7A80")
    else:
        IS.prism_xy([(x - 0.06, 6.4), (x + 0.06, 6.4), (x, 5.9)], ZF + 0.9, ZF + 1.0, "9A9AA0")
IS.box(-4.4, 4.4, 9.4, 13.4, ZF + 0.9, ZF + 1.0, "F4ECD8")  # доска эскизов: контур вазы и солнца
IS.box(-4.6, 4.6, 9.2, 9.4, ZF + 0.9, ZF + 1.1, WOOD2)
IS.prism_xy([(-2.6, 10.0), (-1.4, 10.0), (-1.2, 11.0), (-1.6, 12.4), (-2.4, 12.4), (-2.8, 11.0)], ZF + 1.0, ZF + 1.04, CLAY)
aten(IS, 1.8, 11.6, ZF + 1.12, 0.6, 7, col=GOLD)
for x, z in ((-6.0, -6.0), (6.0, -6.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.0, C - 0.6, z - 0.03, z + 0.03, "6A6A60")
    D.lantern(IS, IG, x, C - 4.0, z, s=1.0, cap=GOLD, light="FFF0C8")
# постамент: синяя тумба-куб с золотой каймой
px, pz = PED
IR.box(px - 2.8, px + 2.8, 0.0, TOP - 0.15, pz - 2.8, pz + 2.8, BLUE)
IS.box(px - 3.0, px + 3.0, TOP - 0.15, TOP, pz - 3.0, pz + 3.0, GOLD)
IS.box(px - 3.0, px + 3.0, 0.0, 0.2, pz - 3.0, pz + 3.0, GOLD)
B.lift_leaves(IS, BLUE2, GOLD)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, WHITE, SAND, WHITE, top=16.0)
SL.box(-FX - 0.2, FX + 0.2, 8.8, 9.6, -FZ - 3.0, -FZ, WHITE2)

F.build(exhibit=(PED[0], TOP, PED[1], 3.0), lamps=[("Hall", (0, 14, 6), 2100, (1.0, 0.96, 0.88)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.98, 0.92)),
                                                   ("Sun", (0, 16, -3), 800, (1.0, 0.85, 0.5))])
