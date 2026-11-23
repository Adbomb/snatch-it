"""Этаж «Мини-Стоунхендж» музея-небоскрёба (третья партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — меловой холм равнины Солсбери на рассвете. Снаружи — спереди белый меловой обрыв с поясами
кремня, перед ним по дуге стоят трилиты из серых сарсенов с лишайником и одиночные камни, у подножия — дерновый
склон и клочья тумана; по верху — дерновый козырёк с полевыми цветами; бока — зелёный холм с белой меловой фигурой
коня (без глаза); тыл — кольцо деревянных столбов и курган. Внутри — рассвет в каменном круге: стены — панорама
неба (лаванда, розовый, золото у горизонта) над грядой холмов, в разрыве холмов встаёт солнце точно за экспонатом,
подковой стоят пять трилитов, снаружи — синие камни, туман по траве, меловая тропа от лифта, фонари друидов;
экспонат — на плоском камне-алтаре из двух плит.
Запуск: blender --background --factory-startup --python scripts/blender/floor_stonehenge.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, rng, slab, taper  # noqa: E402

GRASS, GRASS2, GRASS3, EARTH, CHALK, CHALK2 = "5FA83A", "4C9230", "3E7A28", "7A5A3A", "EDEAE0", "D6D0C0"
SARSEN, SARSEN2, SARSEN3, LICHEN, BLUE, FLINT = "9C9A8E", "8A877C", "B2AFA2", "C8C070", "7088A0", "4A4A50"
WOOD, WOOD2, FLOWER, FLOWER2, MIST = "6E4A2E", "52361F", "F2D24A", "E86AA0", "E4ECF2"
SKY, SKY2, LAV, PINK, DAWN, SUN, FIRE = "8FB0E0", "6E86C0", "B8A8D8", "F2A8B4", "FFC890", "FFE6A8", "FFB040"

F = B.Floor("MS", "MiniStonehenge", quiet=(GRASS, GRASS2, SKY, LAV, PINK, DAWN), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def rot_rect(cx, cz, hw, hd, ang):
    """Прямоугольник в плане, повёрнутый на ang (рад): hw — вдоль касательной, hd — поперёк."""
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + u * c - v * s, cz + u * s + v * c) for u, v in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd))]


def stone(p, cx, cz, hw, hd, y0, y1, ang, color, taper_k=0.82):
    """Сарсен: брус, к верху чуть уже, с наклонной макушкой."""
    lo = rot_rect(cx, cz, hw, hd, ang)
    hi = rot_rect(cx, cz, hw * taper_k, hd * taper_k, ang)
    tilt = (rng(cx, cz) - 0.5) * 0.5
    p.loft([(x, y0, z) for x, z in lo], [(x, y1 + tilt * (k - 1.5) * 0.3, z) for k, (x, z) in enumerate(hi)], color)


def trilithon(p, lich, cx, cz, ang, h, span=1.9, w=0.85, d=0.65, colors=(SARSEN, SARSEN2)):
    """Трилит: два столба и перемычка; пятна лишайника."""
    c, s = math.cos(ang), math.sin(ang)
    for e, col in zip((-1, 1), colors):
        ux, uz = cx + e * span * c, cz + e * span * s
        stone(p, ux, uz, w, d, 0.0, h, ang, col)
        lich.prism_xz(rot_rect(ux + 0.1 * e, uz, 0.32, d + 0.03, ang), h * 0.55, h * 0.55 + 0.6, LICHEN)
    p.prism_xz(rot_rect(cx, cz, span + w + 0.25, d + 0.05, ang), h - 0.05, h + 1.2, SARSEN3)


# ══ ФАСАД: меловой холм с каменным кругом ════════════════════════════════════════════════════════════════════
B.shell_planes(F, CHALK2, CHALK2, SKY2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    front = fi == 0
    gd = 6.88 if fi == 0 else 3.88  # спереди трава шире: на ней стоят камни круга
    slab(FQ, axis, fixed, out, gd, -half - 3.88, half + 3.88, -1.0, 0.4, GRASS2)  # трава у подножия
    B.chamfer(FQ, axis, fixed, out, -half - 3.0, half + 3.0,  # дерновый склон
              [(0.0, 0.4), (3.0, 0.4), (2.3, 2.0), (1.4, 3.6), (0.9, 5.0), (0.0, 5.0)], GRASS)
    if front:  # меловой обрыв: блоки двух тонов, пояса кремня
        for r, (y0, y1) in enumerate(((5, 8), (8, 11), (11, 13), (13, 16))):
            a, k = -half, 0
            while a < half:
                w = 3 + int(rng(fi, r, k) * 4)
                a1 = min(a + w, half)
                slab(FR, axis, fixed, out, 0.88 if rng(r, k, 3) < 0.7 else 1.88, a + 0.05, a1 - 0.05, y0 + 0.05, y1 - 0.05,
                     CHALK if (r + k) % 3 else CHALK2)
                a, k = a1, k + 1
        for y in (8.0, 13.0):
            for k in range(int(2 * half // 1.6)):
                a = -half + 0.8 + 1.6 * k + (rng(y, k) - 0.5) * 0.6
                slab(FS, axis, fixed, out, 1.0 + (0.9 if rng(k, y, 2) < 0.3 else 0.0), a - 0.3, a + 0.3, y - 0.22, y + 0.22,
                     FLINT)
        for k in range(15):  # дёрн свисает с козырька, меловые валуны у подножия обрыва
            a = -half + 1.2 + 2.4 * k + (rng(k, 17) - 0.5)
            L = 1.0 + rng(k, 18) * 2.6
            slab(FS, axis, fixed, out, 1.0 + rng(k, 19) * 0.6, a - 0.5, a + 0.5, 16.0 - L, 16.0, GRASS2 if k % 2 else GRASS3)
        for k in range(6):
            a = -15.0 + 6.0 * k + (rng(k, 27) - 0.5) * 2
            FS.prism_xz(K.octa(a, -FZ - 1.6, 0.9, 0.7, 0.3), 3.6, 4.6 + rng(k, 28) * 0.6, CHALK2)
    else:  # зелёный холм
        slab(FQ, axis, fixed, out, 0.88, -half, half, 5.0, 16.0, GRASS if fi != 1 else GRASS2)
    slab(FQ, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, 16.0, 17.2, GRASS)  # дерновый козырёк
    slab(FR, axis, fixed, out, 0.88, -half, half, 17.2, 19.0, EARTH)
    for k in range(int(2 * half // 1.3)):  # пучки травы и цветы по козырьку
        a = -half + 0.6 + 1.3 * k
        h = 0.5 + rng(fi, k, 9) * 0.6
        slab(FS, axis, fixed, out, 1.95, a - 0.25, a + 0.25, 17.2, 17.2 + h, GRASS3 if k % 2 else GRASS2)
        if rng(fi, k, 5) < 0.35:
            slab(FS, axis, fixed, out, 1.75, a + 0.3, a + 0.6, 17.2 + h * 0.6, 17.5 + h * 0.6, FLOWER if k % 3 else FLOWER2)
B.anchor(FR, (-22, -1, -21), (22, 19, 21))
B.anchor(FQ, (-22, -1, -21), (22, 19, 21))
# перед: дуга трилитов и одиночных камней на склоне, туман у подножия
for k, x in enumerate((-12.6, -4.3, 4.3, 12.6)):
    z = -FZ - 3.4 - 2.4 * (1 - (x / 15.0) ** 2)
    ang = math.atan2(-x * 0.08, 1.0)
    trilithon(FS, FS, x, z, ang, 9.6 if abs(x) < 6 else 8.4)
for x in (-8.4, 0.0, 8.4):  # одиночные камни между трилитами
    z = -FZ - 3.0 - 2.4 * (1 - (x / 15.0) ** 2)
    stone(FS, x, z, 0.8, 0.6, 0.0, 4.6 + rng(x, 3) * 1.4, 0.0, SARSEN2 if x else BLUE)
FS.prism_xz(rot_rect(-16.8, -FZ - 3.6, 2.6, 0.7, 0.3), -0.2, 0.9, SARSEN)  # упавший камень
for x in (-16.4, 16.4):  # костры-жаровни друидов по краям круга
    z = -FZ - 3.2
    FS.prism_xz(K.octa(x, z, 0.7, 0.7, 0.28), 0.0, 1.6, SARSEN2)
    FS.prism_xz(K.octa(x, z, 0.95, 0.95, 0.38), 1.6, 2.0, WOOD2)
    FG.prism_xz(K.octa(x, z, 0.6, 0.6, 0.24), 2.0, 2.8, FIRE)
    FG.prism_xz(K.octa(x, z, 0.3, 0.3, 0.12), 2.8, 3.4, "FFD870")
for k in range(7):  # клочья тумана
    x = -15.0 + 5.0 * k + (rng(k, 41) - 0.5) * 2
    FS.prism_xz(K.octa(x, -FZ - 4.6 - rng(k, 42) * 1.2, 2.0, 0.9, 0.6), 0.4, 0.9 + rng(k, 43) * 0.4, MIST)
# бока: меловая фигура коня на склоне холма (белые линии, без глаза)
HORSE = [((-7.0, 9.6), (5.0, 10.2), 0.7), ((5.0, 10.2), (8.2, 12.6), 0.55), ((8.2, 12.6), (9.8, 12.4), 0.5),
         ((-7.0, 9.6), (-9.4, 11.2), 0.45), ((-5.6, 9.4), (-7.4, 6.4), 0.4), ((-3.8, 9.5), (-2.8, 6.6), 0.4),
         ((3.0, 9.9), (2.0, 6.8), 0.4), ((4.4, 10.0), (6.6, 7.2), 0.4)]
for s in (-1, 1):
    fx = s * FX
    for (z0, y0), (z1, y1), w in HORSE:
        zz0, zz1 = z0 * s, z1 * s
        B.beam(FS, (fx + s * 0.95, y0, zz0), (fx + s * 0.95, y1, zz1), w, 0.14, CHALK, up=(1, 0, 0))
    for k in range(4):  # камни-голубчики у подножия
        z = -12.0 + 8.0 * k
        stone(FS, fx + s * 3.2, z, 0.5, 0.45, 0.0, 2.2 + rng(s, k) * 1.2, 0.2 * s, BLUE if k % 2 else SARSEN2)
# тыл: деревянное кольцо столбов и курган
for k in range(9):
    x = -14.0 + 3.5 * k
    FS.prism_xz(K.octa(x, FZ + 3.0, 0.45, 0.45, 0.18), 0.0, 5.5 + rng(k, 51) * 1.5, WOOD if k % 2 else WOOD2)
FQ.prism_zy([(FZ, 5.0), (FZ + 2.4, 5.0), (FZ + 1.6, 6.6), (FZ + 0.6, 7.2), (FZ, 7.2)], -9.0, 9.0, GRASS2)

# ══ ИНТЕРЬЕР: рассвет в каменном круге ════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), GRASS)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:  # полосы неба: золото у горизонта, розовый, лаванда, голубой
        for y0, y1, col in ((0.0, 4.0, DAWN), (4.0, 7.0, PINK), (7.0, 11.0, LAV)):
            slab(IQ, axis, fixed, out, 0.88, a0, a1, y0, y1, col)
    if gap:
        slab(IQ, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 11.0, LAV)
    slab(IQ, axis, fixed, out, 0.88, -half, half, 11.0, C, SKY)
    # гряда холмов по низу (на передней стене — разрыв для солнца)
    pts = []
    n = 14
    for k in range(n + 1):
        a = -half + 2 * half * k / n
        h = 2.2 + 1.4 * math.sin(a * 0.45 + idx) + 0.8 * math.sin(a * 1.1 + idx * 2)
        if idx == 2 and abs(a) < 4.0:
            h = min(h, 0.9 + abs(a) * 0.35)
        pts.append((a, max(h, 0.6)))
    poly = [(-half, 0.0)] + pts + [(half, 0.0)]
    if gap:
        poly = [(a, min(h, 0.6)) if abs(a) < DOOR[0] + 0.6 else (a, h) for a, h in poly]
    d0, d1 = sorted((fixed + out * 0.88, fixed + out * 1.05))
    far = [(-half, 0.0)] + [(a, h + 1.6 + 0.8 * math.sin(a * 0.3 + idx * 3)) for a, h in pts] + [(half, 0.0)]
    if gap:
        far = [(a, min(h, 0.6)) if abs(a) < DOOR[0] + 0.6 else (a, h) for a, h in far]
    if idx == 2:
        far = [(a, min(h, 0.9 + abs(a) * 0.5)) for a, h in far]
    e0, e1 = sorted((fixed + out * 0.88, fixed + out * 0.96))
    d0, d1 = sorted((fixed + out * 0.96, fixed + out * 1.05))
    prism = IS.prism_xy if axis == "z" else IS.prism_zy
    prism(far, e0, e1, "6FAF5A")
    prism(poly, d0, d1, GRASS3)
    for k in range(3):  # облака в розовом свете
        a = -half + (k + 0.5) * 2 * half / 3 + (rng(idx, k, 7) - 0.5) * 4
        y = 12.0 + rng(idx, k, 8) * 3.0
        c0, c1 = sorted((fixed + out * 0.88, fixed + out * 0.94))
        prism(K.octa(a, y, 3.2 + rng(idx, k) * 1.6, 0.55, 0.45), c0, c1, "FCE6EE")
        prism(K.octa(a + 0.8, y + 0.5, 1.8, 0.5, 0.4), c0, c1, "FFF4F6")
# солнце встаёт в разрыве холмов за экспонатом; лучи
IG.prism_xy(K.octa(0.0, 2.6, 2.4, 2.4, 1.0), ZF + 0.86, ZF + 0.9, SUN)
for k in range(9):
    t = math.radians(20 + 17.5 * k)
    a, b = (2.9 * math.cos(t), 2.6 + 2.9 * math.sin(t)), (6.4 * math.cos(t), 2.6 + 6.4 * math.sin(t))
    taper(IG, (a[0], a[1], ZF + 0.92), (b[0], b[1], ZF + 0.92), 0.45, 0.12, "FFD8A0")
for k in range(14):  # последние звёзды на потолке
    x, z = (rng(k, 61) - 0.5) * 30, (rng(k, 62) - 0.5) * 28
    IG.box(x - 0.12, x + 0.12, C - 0.05, C - 0.02, z - 0.12, z + 0.12, "FFFFFF")
# подкова из четырёх трилитов вокруг экспоната, снаружи — синие камни; середина открыта на рассвет:
# серый мини-Стоунхендж читается на светлом небе, а не на таком же сером трилите прямо за ним
px, pz = PED
for k, deg in enumerate((-105, -62, 62, 105)):
    a = math.radians(deg)
    cx, cz = px + 9.2 * math.sin(a), pz - 9.2 * math.cos(a)
    trilithon(IS, IS, cx, cz, a, 7.6,
              colors=((SARSEN, SARSEN2), (SARSEN2, SARSEN3))[k % 2])
for k in range(12):
    a = math.radians(-150 + 300 * k / 11)
    cx, cz = px + 12.6 * math.sin(a), pz - 12.6 * math.cos(a)
    if cz > 5.0 or abs(cx) > 15.5 or cz < -15.0:
        continue
    stone(IS, cx, cz, 0.5, 0.42, 0.0, 2.4 + rng(k, 71) * 1.4, a, BLUE if k % 2 else SARSEN2)
# меловая тропа от лифта к алтарю, туман по траве
for j in range(7):
    z = 15.0 - 2.0 * j
    w = 1.6 + (rng(j, 81) - 0.5) * 0.4
    IS.box(-w, w, 0.0, 0.06, z - 0.95, z + 0.95, CHALK2 if j % 2 else CHALK)
for k in range(9):
    x, z = (rng(k, 91) - 0.5) * 28, -13.0 + rng(k, 92) * 18
    if abs(x) < 5.0 and z > -9:
        continue
    IS.prism_xz(K.octa(x, z, 2.2, 1.0, 0.6), 0.0, 0.25 + rng(k, 93) * 0.25, MIST)
# кольцевой вал вокруг круга (у лифта — проход), трава и цветы
for k in range(20):
    a0, a1 = 2 * math.pi * k / 20, 2 * math.pi * (k + 1) / 20
    pts = [(px + r * math.sin(a), pz - r * math.cos(a)) for r, a in ((14.2, a0), (15.2, a0), (15.2, a1), (14.2, a1))]
    if all(abs(x) < W - 0.2 and ZF + 0.2 < z < 4.0 for x, z in pts):
        IQ.prism_xz(pts, 0.0, 0.45, GRASS2)
for k in range(22):
    x, z = (rng(k, 101) - 0.5) * 31, -14.5 + rng(k, 102) * 22
    if (abs(x) < 4.8 and z > 6.0) or (abs(x - px) < 4.6 and abs(z - pz) < 4.6):
        continue
    for m in range(3):
        t = 2 * math.pi * m / 3 + k
        taper(IS, (x, 0.0, z), (x + math.cos(t) * 0.5, 0.9 + rng(k, m) * 0.5, z + math.sin(t) * 0.5), 0.3, 0.06,
              GRASS2 if m % 2 else GRASS3)
    if k % 3 == 0:
        IS.prism_xz(K.octa(x + 0.3, z, 0.22, 0.22, 0.09), 0.7, 0.95, (FLOWER, FLOWER2, "FFFFFF")[k % 9 // 3])
# камень-алтарь и фонари друидов
# алтарь — тёмный кремень: серые камни экспоната не тонут в сером сарсене
IR.box(px - 4.0, px + 4.0, 0.0, 0.6, pz - 4.0, pz + 4.0, FLINT)
IR.box(px - 3.2, px + 3.2, 0.6, TOP, pz - 3.2, pz + 3.2, "3A3A42")
IS.box(px - 3.3, px + 3.3, TOP - 0.12, TOP + 0.03, pz - 3.3, pz + 3.3, "2E2E34")
for x, z in ((-5.2, 6.0), (5.2, 6.0), (-5.6, 1.6), (5.6, 1.6)):
    IS.box(x - 0.15, x + 0.15, 0.0, 3.6, z - 0.15, z + 0.15, WOOD2)
    IS.prism_xz(K.octa(x, z, 0.4, 0.4, 0.16), 3.6, 3.8, WOOD)
    IG.prism_xz(K.octa(x, z, 0.3, 0.3, 0.12), 3.8, 4.5, FIRE)
    IS.prism_xz(K.octa(x, z, 0.4, 0.4, 0.16), 4.5, 4.7, WOOD)
B.lift_leaves(IS, SARSEN2, CHALK)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, GRASS)
SL.box(-FX - 3.9, FX + 3.9, -1.0, 0.4, -FZ - 3.9, FZ + 3.9, GRASS2)
SL.box(-FX - 1.9, FX + 1.9, 16.0, 17.2, -FZ - 1.9, FZ + 1.9, GRASS)
SL.box(-FX + 0.2, FX - 0.2, 5.0, 16.0, -FZ - 0.9, -FZ, CHALK)
for x in (-12.6, -4.3, 4.3, 12.6):
    z = -FZ - 3.4 - 2.4 * (1 - (x / 15.0) ** 2)
    h = 9.6 if abs(x) < 6 else 8.4
    SL.box(x - 2.9, x - 1.1, 0.0, h, z - 0.6, z + 0.6, SARSEN)
    SL.box(x + 1.1, x + 2.9, 0.0, h, z - 0.6, z + 0.6, SARSEN2)
    SL.box(x - 3.0, x + 3.0, h, h + 1.2, z - 0.7, z + 0.7, SARSEN3)

F.build(exhibit=(PED[0], TOP, PED[1], 3.0), lamps=[("Hall", (0, 14, 6), 2800, (1.0, 0.9, 0.85)),
                                                   ("Spot", (0, 13, -3), 3200, (1.0, 0.95, 0.88))])
