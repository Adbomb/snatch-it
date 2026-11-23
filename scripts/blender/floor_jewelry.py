"""Этаж «Рубиновый воришка» музея-небоскрёба (шестая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — ювелирный дом ночью, в разгар ограбления. Внизу — чёрный мрамор в золотых рамах, широкая витрина
слева с колье на бархатных бюстах и кольцами на подставках (в стекле вырезан круглый лаз), вход с колоннами и
бордовым козырьком, справа — узкая витрина и над ней на золотом кронштейне огромный светящийся гранёный рубин;
наверху — кремовая стена с ритмом из четырёх арочных окон с золотыми балкончиками, на парапете — золотые вазы,
по углам — камеры наблюдения, с крыши свисает верёвка с крюком-кошкой, у двери — брошенный мешок и фонарик;
на боках — арочные окна и золотые пояса. Внутри — салон: пол «ромбами» из чёрного и белого мрамора, стены
в бордовом бархате с золотыми рамами и зеркалами, по бокам — стеклянные витрины с кольцами и колье, у дальней стены
— арочная ниша с прожектором и пустой подушкой под приподнятым стеклянным колпаком (рубин украден), над залом —
хрустальная люстра, у стен — красные лучи сигнализации; экспонат — на чёрном бархатном помосте с золотой каймой.
Запуск: blender --background --factory-startup --python scripts/blender/floor_jewelry.py -- <репо> <превью>
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

MARBLE, MARBLE2, GOLD, GOLD2, WINE, RUBY = "2A2830", "3A3742", "E0B040", "B88A28", "7A1A28", "E02840"
CREAM, CREAM2, VELVET, WHITE, SILVER, LASER = "F2E6D0", "E2D2B8", "5A1A3A", "F4F0EA", "C8CCD4", "FF2A3A"
NIGHT, ROPE, BLUEG = "1E2238", "C8A070", "3A6AB0"
GEMS = ("E02840", "3A8AE8", "3AC86A", "B06AE0", "F4F0EA")

F = B.Floor("JW", "RubyThief", quiet=(MARBLE2, VELVET, "4A2A3A"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def gem(p, g, cx, cy, z0, z1, r, col, glow=True):
    """Гранёный камень (вид спереди): корона-трапеция и павильон-клин; светится, если glow."""
    q = g if glow else p
    q.prism_xy([(cx - r * 0.6, cy + r * 0.5), (cx + r * 0.6, cy + r * 0.5), (cx + r, cy + r * 0.1), (cx - r, cy + r * 0.1)], z0, z1, col)
    q.prism_xy([(cx - r, cy + r * 0.1), (cx + r, cy + r * 0.1), (cx, cy - r)], z0, z1, col)
    p.prism_xy([(cx - r * 0.3, cy + r * 0.45), (cx, cy + r * 0.45), (cx - r * 0.15, cy + r * 0.2)], z0 - 0.04, z0, WHITE)


def bust(p, x, y, z, col=VELVET, necklace=True, seed=0):
    """Бархатный бюст с колье (лицом к −z): шея-подставка, плечи, нить с камнями."""
    p.box(x - 0.3, x + 0.3, y, y + 0.3, z - 0.3, z + 0.3, GOLD2)
    p.prism_xy([(x - 0.9, y + 0.3), (x + 0.9, y + 0.3), (x + 0.7, y + 1.3), (x + 0.25, y + 1.5), (x + 0.25, y + 2.1),
                (x - 0.25, y + 2.1), (x - 0.25, y + 1.5), (x - 0.7, y + 1.3)], z - 0.3, z + 0.3, col)
    if necklace:
        for k in range(5):
            t = math.pi * (0.15 + 0.7 * k / 4)
            xx, yy = x + 0.55 * math.cos(t), y + 1.55 - 0.45 * math.sin(t)
            p.prism_xy(K.ngon(xx, yy, 0.1 if k != 2 else 0.18, 6), z - 0.36, z - 0.3, GOLD if k != 2 else GEMS[seed % 5])


def ring_stand(p, x, y, z, col):
    """Кольцо на подставке-конусе."""
    p.cone([(x + 0.22 * math.cos(t), y, z + 0.22 * math.sin(t)) for t in [2 * math.pi * k / 6 for k in range(6)]], (x, y + 0.6, z), VELVET)
    p.frame_xy(K.ngon(x, y + 0.75, 0.22, 8), K.ngon(x, y + 0.75, 0.15, 8), z - 0.04, z + 0.04, GOLD)
    p.prism_xz(K.ngon(x, z, 0.07, 6), y + 0.94, y + 1.06, col)


def camera(p, g, x, y, z, ex, ez):
    """Камера наблюдения на кронштейне, повернута по (ex, ez)."""
    p.box(x - 0.15, x + 0.15, y - 0.15, y + 0.15, z - 0.15, z + 0.15, SILVER)
    beam(p, (x, y, z), (x + ex * 0.8, y - 0.2, z + ez * 0.8), 0.15, 0.15, SILVER)
    beam(p, (x + ex * 0.6, y - 0.1, z + ez * 0.6), (x + ex * 1.6, y - 0.5, z + ez * 1.6), 0.45, 0.45, WHITE)
    g.prism_xz(K.ngon(x + ex * 1.65, z + ez * 1.65, 0.08, 6), y - 0.3, y - 0.2, LASER)


# ══ ФАСАД: ювелирный дом ══════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, MARBLE, CREAM, NIGHT)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, MARBLE2)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.0, MARBLE2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.0, 9.6, MARBLE)
    for k in range(int(2 * half // 4.4) + 1):  # золотые рамы-панели по мрамору
        a = -half + 0.4 + 4.4 * k
        if a + 4.0 > half or (fi == 0 and -16.0 < a < 16.0):
            continue
        pr = FS.frame_xy if axis == "z" else FS.frame_zy
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 1.0))
        pr(K.rect(a, a + 4.0, 1.6, 8.8), K.rect(a + 0.15, a + 3.85, 1.75, 8.65), d0, d1, GOLD2)
    slab(FR, axis, fixed, out, 1.6, -half - 0.3, half + 0.3, 9.6, 10.4, GOLD2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 10.4, 16.4, CREAM)
    slab(FR, axis, fixed, out, 1.88, -half - 0.5, half + 0.5, 16.4, 17.0, CREAM2)
    slab(FS, axis, fixed, out, 1.95, -half - 0.5, half + 0.5, 16.95, 17.1, GOLD)
    slab(FR, axis, fixed, out, 0.88, -half, half, 17.0, 18.9, CREAM2)
    slab(FR, axis, fixed, out, 1.3, -half - 0.2, half + 0.2, 18.4, 18.9, GOLD2)
    if axis == "x":  # бока: арочные окна наверху
        for z in (-10.0, -2.0, 6.0):
            d = lambda v: fixed + out * v  # noqa: E731
            slab(FG, axis, fixed, out, 0.92, z - 1.3, z + 1.3, 11.2, 14.6, "FFD890")
            FS.frame_zy([(z - 1.6, 10.9), (z + 1.6, 10.9), (z + 1.6, 14.6), (z, 16.0), (z - 1.6, 14.6)],
                        [(z - 1.3, 11.2), (z + 1.3, 11.2), (z + 1.3, 14.5), (z, 15.6), (z - 1.3, 14.5)], *sorted((d(0.88), d(1.2))), GOLD2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# широкая витрина слева: колье на бюстах, кольца, круглый лаз в стекле
FS.box(-15.6, -3.4, 1.0, 2.4, -FZ - 1.6, -FZ - 0.88, MARBLE2)
FG.box(-15.0, -4.0, 2.4, 8.6, -FZ - 0.94, -FZ - 0.9, "2A1E3A")
FS.frame_xy(K.rect(-15.6, -3.4, 2.0, 9.2), K.rect(-15.0, -4.0, 2.4, 8.6), -FZ - 1.4, -FZ - 0.88, GOLD)
FS.box(-15.0, -4.0, 2.4, 2.6, -FZ - 2.0, -FZ - 0.88, VELVET)
for k, x in enumerate((-13.2, -9.5, -5.8)):
    bust(FS, x, 2.6, -FZ - 1.5, VELVET, seed=k)
for k, x in enumerate((-11.4, -7.6)):
    ring_stand(FS, x, 2.6, -FZ - 1.6, GEMS[k + 1])
FS.frame_xy(K.ngon(-6.2, 6.8, 0.9, 12), K.ngon(-6.2, 6.8, 0.78, 12), -FZ - 1.02, -FZ - 0.94, WHITE)  # круглый лаз
FS.prism_xz(K.ngon(-6.0, -FZ - 3.0, 0.9, 12), 0.0, 0.08, "A8C8E0")  # вырезанный круг стекла на тротуаре
# вход с колоннами и бордовым козырьком
FS.box(-1.2, 4.0, 1.0, 8.4, -FZ - 0.96, -FZ - 0.88, NIGHT)
FG.box(-0.8, 3.6, 1.2, 7.8, -FZ - 1.0, -FZ - 0.96, "FFD890")
FS.frame_xy(K.rect(-1.2, 4.0, 1.0, 8.4), K.rect(-0.8, 3.6, 1.0, 7.8), -FZ - 1.3, -FZ - 0.9, GOLD)
FS.box(1.36, 1.44, 1.0, 7.8, -FZ - 1.1, -FZ - 1.0, GOLD)
for x in (-2.2, 5.0):
    FS.prism_xz(K.ngon(x, -FZ - 1.8, 0.45, 10), 1.0, 8.8, MARBLE2)
    FS.box(x - 0.7, x + 0.7, 0.0, 1.0, -FZ - 2.5, -FZ - 1.1, GOLD2)
    FS.box(x - 0.7, x + 0.7, 8.8, 9.4, -FZ - 2.5, -FZ - 1.1, GOLD)
FS.loft([(-3.2, 9.4, -FZ - 0.9), (6.0, 9.4, -FZ - 0.9), (6.0, 9.7, -FZ - 0.9), (-3.2, 9.7, -FZ - 0.9)],
        [(-3.2, 9.0, -FZ - 3.4), (6.0, 9.0, -FZ - 3.4), (6.0, 9.3, -FZ - 3.4), (-3.2, 9.3, -FZ - 3.4)], WINE)
FS.box(-3.3, 6.1, 8.8, 9.05, -FZ - 3.5, -FZ - 3.3, GOLD)
# справа: узкая витрина и огромный рубин на кронштейне
FG.box(8.0, 14.6, 2.4, 8.2, -FZ - 0.94, -FZ - 0.9, "2A1E3A")
FS.frame_xy(K.rect(7.6, 15.0, 2.0, 8.6), K.rect(8.0, 14.6, 2.4, 8.2), -FZ - 1.4, -FZ - 0.88, GOLD)
for k in range(3):
    ring_stand(FS, 9.2 + 2.2 * k, 2.4, -FZ - 1.5, GEMS[(k + 2) % 5])
    FS.box(8.8 + 2.2 * k, 9.6 + 2.2 * k, 2.4, 2.4 + 0.02, -FZ - 1.9, -FZ - 1.1, VELVET)
RX = 8.7
FS.box(RX - 0.2, RX + 0.2, 10.4, 11.0, -FZ - 4.0, -FZ - 0.88, GOLD)
beam(FS, (RX, 10.7, -FZ - 1.0), (RX, 13.6, -FZ - 3.8), 0.25, 0.25, GOLD)
FS.box(RX - 0.05, RX + 0.05, 11.0, 12.0, -FZ - 3.95, -FZ - 3.85, GOLD2)
gem(FS, FG, RX, 13.2, -FZ - 4.2, -FZ - 3.6, 2.0, RUBY)
FS.frame_xy([(RX - 1.4, 14.4), (RX + 1.4, 14.4), (RX + 2.4, 13.6), (RX, 10.8), (RX - 2.4, 13.6)],
            [(RX - 1.2, 14.2), (RX + 1.2, 14.2), (RX + 2.1, 13.5), (RX, 11.2), (RX - 2.1, 13.5)], -FZ - 4.26, -FZ - 3.54, GOLD)
# наверху: четыре арочных окна с балкончиками
for x in (-13.0, -4.4, 4.4, 13.0):
    FG.box(x - 1.4, x + 1.4, 11.0, 14.6, -FZ - 0.94, -FZ - 0.9, "FFD890")
    FS.frame_xy([(x - 1.7, 10.7), (x + 1.7, 10.7), (x + 1.7, 14.6), (x, 16.1), (x - 1.7, 14.6)],
                [(x - 1.4, 11.0), (x + 1.4, 11.0), (x + 1.4, 14.5), (x, 15.7), (x - 1.4, 14.5)], -FZ - 1.2, -FZ - 0.88, GOLD2)
    FS.box(x - 0.05, x + 0.05, 11.0, 15.6, -FZ - 1.0, -FZ - 0.94, GOLD2)
    FS.box(x - 2.0, x + 2.0, 10.4, 10.7, -FZ - 2.2, -FZ - 0.88, MARBLE2)
    for i in range(9):
        FS.box(x - 1.9 + 0.475 * i - 0.04, x - 1.9 + 0.475 * i + 0.04, 10.7, 11.9, -FZ - 2.15, -FZ - 2.07, GOLD)
    FS.box(x - 2.0, x + 2.0, 11.9, 12.05, -FZ - 2.2, -FZ - 2.02, GOLD)
# золотые вазы на парапете, камеры, верёвка с крюком, мешок и фонарик
for x in (-16.0, -8.6, 8.6, 16.0):
    FS.prism_xz(K.ngon(x, -FZ - 1.4, 0.5, 8), 17.1, 17.5, GOLD2)
    FS.prism_xz(K.ngon(x, -FZ - 1.4, 0.38, 8), 17.5, 18.2, GOLD)
    FS.prism_xz(K.ngon(x, -FZ - 1.4, 0.55, 8), 18.2, 18.5, GOLD)
camera(FS, FG, -FX - 0.6, 9.2, -FZ - 0.6, 0.6, -0.8)
camera(FS, FG, FX + 0.6, 9.2, -FZ - 0.6, -0.6, -0.8)
for e in (-1, 1):  # крюк-кошка на парапете
    beam(FS, (-0.6, 18.4, -FZ - 1.0), (-0.6 + e * 0.6, 18.8, -FZ - 1.5), 0.12, 0.12, SILVER)
FS.box(-0.65, -0.55, 4.0, 18.4, -FZ - 1.45, -FZ - 1.35, ROPE)
for k in range(10):
    FS.box(-0.75, -0.45, 4.6 + 1.4 * k, 4.75 + 1.4 * k, -FZ - 1.5, -FZ - 1.3, ROPE)
FS.prism_xz(K.octa(-4.4, -FZ - 5.0, 0.9, 0.7, 0.3), 0.0, 1.3, "8A7A5A")
FS.prism_xz(K.ngon(-4.4, -FZ - 5.0, 0.25, 6), 1.3, 1.7, "6A5A3A")
FS.prism_zy(K.ngon(-FZ - 6.2, 0.25, 0.25, 8), -6.6, -5.6, NIGHT)
FG.prism_zy(K.ngon(-FZ - 6.2, 0.25, 0.18, 8), -5.6, -5.5, "FFF0B0")
# тыл: пожарная лестница
for k in range(8):
    FS.box(-8.6, -6.4, 2.0 + 2.0 * k, 2.1 + 2.0 * k, FZ + 1.0, FZ + 1.2, SILVER)
for x in (-8.6, -6.4):
    FS.box(x - 0.08, x + 0.08, 1.0, 17.0, FZ + 1.0, FZ + 1.2, SILVER)

# ══ ИНТЕРЬЕР: салон ═══════════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.1
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "E8E4DC")
for i in range(-7, 8):
    for j in range(-7, 8):
        if (i + j) % 2 == 0:
            x, z = 2.3 * i, -3.0 + 2.3 * j
            if abs(x) < W - 1.2 and ZF + 1.2 < z < ZB - 1.2:
                IQ.prism_xz([(x, z - 1.15), (x + 1.15, z), (x, z + 1.15), (x - 1.15, z)], 0.02, 0.04, MARBLE)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, WINE)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 1.4, MARBLE)
        slab(IS, axis, fixed, out, 1.1, a0, a1, 1.4, 1.6, GOLD2)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, WINE)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, GOLD)
    if idx < 2:  # бархатные панели в золотых рамах и зеркала
        for k, a in enumerate((-11.0, -3.0, 5.0, 12.4)):
            d0, d1 = sorted((fixed + out * 0.88, fixed + out * 1.05))
            IS.frame_zy(K.rect(a - 2.2, a + 2.2, 7.4, 14.2), K.rect(a - 1.95, a + 1.95, 7.65, 13.95), d0, d1, GOLD)
            if k == 1:
                IG.prism_zy(K.rect(a - 1.95, a + 1.95, 7.65, 13.95), *sorted((fixed + out * 0.9, fixed + out * 0.94)), "6A7A90")
            else:
                IS.prism_zy(K.rect(a - 1.95, a + 1.95, 7.65, 13.95), *sorted((fixed + out * 0.9, fixed + out * 0.96)), VELVET)
    slab(IR, axis, fixed, out, 1.5, -half, half, 15.0, 15.6, GOLD2)
for k in range(-3, 4):
    IS.box(-W, W, C - 0.5, C - 0.2, 4.4 * k - 0.2, 4.4 * k + 0.2, GOLD2)
# стеклянные витрины вдоль боковых стен
for s in (-1, 1):
    for z in (-11.0, -4.0, 3.0):
        x = s * (W - 2.4)
        IR.box(x - 1.3, x + 1.3, 0.0, 3.0, z - 2.6, z + 2.6, MARBLE2)
        IS.box(x - 1.35, x + 1.35, 3.0, 3.15, z - 2.65, z + 2.65, GOLD)
        IS.box(x - 1.1, x + 1.1, 3.15, 3.2, z - 2.4, z + 2.4, VELVET)
        for k in range(4):
            zz = z - 1.8 + 1.2 * k
            if k % 2:
                ring_stand(IS, x, 3.2, zz, GEMS[(k + int(z)) % 5])
            else:
                bust(IS, x, 3.2, zz, VELVET, seed=k + int(z))
        IG.box(x - 1.3, x + 1.3, 5.6, 5.66, z - 2.6, z + 2.6, "C8D8E8")
        for e in (-1, 1):
            for f in (-1, 1):
                IS.box(x + e * 1.25 - 0.06, x + e * 1.25 + 0.06, 3.15, 5.6, z + f * 2.55 - 0.06, z + f * 2.55 + 0.06, GOLD)
# арочная ниша с пустой подушкой и приподнятым колпаком (рубин украден)
IR.box(-4.2, 4.2, 0.0, 12.0, ZF + 0.88, ZF + 1.6, VELVET)
IS.frame_xy([(-4.6, 0.0), (4.6, 0.0), (4.6, 9.6), (0.0, 12.6), (-4.6, 9.6)], [(-3.8, 0.0), (3.8, 0.0), (3.8, 9.2), (0.0, 11.8), (-3.8, 9.2)],
            ZF + 1.6, ZF + 2.0, GOLD)
IR.prism_xz(K.ngon(0.0, ZF + 3.6, 1.3, 10), 0.0, 3.6, MARBLE2)
IS.prism_xz(K.ngon(0.0, ZF + 3.6, 1.45, 10), 3.6, 3.8, GOLD)
IS.prism_xz(K.octa(0.0, ZF + 3.6, 1.0, 1.0, 0.4), 3.8, 4.2, "C83040")
IS.prism_xz(K.octa(0.0, ZF + 3.6, 0.45, 0.45, 0.18), 4.2, 4.25, "8A1E2A")
IG.prism_xz(K.ngon(0.0, ZF + 3.6, 1.2, 10), 6.4, 8.4, "7A90A8")
IS.box(-0.04, 0.04, 8.4, 12.6, ZF + 3.56, ZF + 3.64, SILVER)
IG.prism_xy(K.ngon(0.0, 12.9, 0.4, 8), ZF + 2.0, ZF + 2.2, "FFF4D8")
# хрустальная люстра
ring_y(IS, 0.0, -3.0, 2.4, 2.8, C - 3.0, C - 2.7, GOLD, n=16)
ring_y(IS, 0.0, -3.0, 1.2, 1.5, C - 2.0, C - 1.8, GOLD, n=12)
for k in range(12):
    t = 2 * math.pi * k / 12
    IG.prism_xz(K.octa(2.6 * math.cos(t), -3.0 + 2.6 * math.sin(t), 0.18, 0.18, 0.07), C - 3.8, C - 3.0, "F0F8FF")
for k in range(4):
    t = math.pi / 2 * k + math.pi / 4
    IS.box(2.6 * math.cos(t) - 0.03, 2.6 * math.cos(t) + 0.03, C - 2.7, C - 0.5, -3.0 + 2.6 * math.sin(t) - 0.03, -3.0 + 2.6 * math.sin(t) + 0.03, GOLD)
# красные лучи сигнализации у стен (не поперёк прохода)
for s in (-1, 1):
    x = s * (W - 4.4)
    for k in range(3):
        y = 0.8 + 0.9 * k
        IG.box(x - 0.04, x + 0.04, y - 0.04, y + 0.04, -13.6, 6.0, LASER)
    IS.box(x - 0.25, x + 0.25, 0.0, 3.2, 6.0, 6.5, NIGHT)
    IS.box(x - 0.25, x + 0.25, 0.0, 3.2, -14.1, -13.6, NIGHT)
for k in range(2):
    y = 1.2 + 1.2 * k
    IG.box(-6.2, 6.2, y - 0.04, y + 0.04, -9.6 - 0.04, -9.6 + 0.04, LASER)
for x in (-6.4, 6.4):
    IS.box(x - 0.25, x + 0.25, 0.0, 3.0, -9.85, -9.35, NIGHT)
# чёрный бархатный помост с золотой каймой
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.1, 16), 0.0, 0.5, MARBLE)
IS.prism_xz(K.ngon(px, pz, 4.2, 16), 0.5, 0.62, GOLD)
IS.prism_xz(K.ngon(px, pz, 3.8, 16), 0.62, TOP - 0.1, "26202A")
IS.prism_xz(K.ngon(px, pz, 3.9, 16), TOP - 0.1, TOP, GOLD2)
for k in range(8):
    t = 2 * math.pi * (k + 0.5) / 8
    IS.prism_xz(K.ngon(px + 3.86 * math.cos(t), pz + 3.86 * math.sin(t), 0.12, 6), 0.62, TOP - 0.1, GOLD)
B.lift_leaves(IS, MARBLE2, GOLD)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 9.6, -FZ, FZ, MARBLE)
SL.box(-FX, FX, 9.6, 18.9, -FZ, FZ, CREAM)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, MARBLE2)
SL.box(-FX - 0.5, FX + 0.5, 9.6, 10.4, -FZ - 0.5, FZ + 0.5, GOLD)
SL.box(-3.2, 6.0, 8.8, 9.7, -FZ - 3.4, -FZ, WINE)
SL.prism_xy([(RX - 2.0, 14.4), (RX + 2.0, 14.4), (RX + 2.4, 13.4), (RX, 10.6), (RX - 2.4, 13.4)], -FZ - 4.2, -FZ - 3.6, RUBY)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.85, 0.75)),
                                                   ("Spot", (0, 13, -3), 3600, (1.0, 0.95, 0.9)),
                                                   ("Niche", (0, 9, ZF + 5), 800, (1.0, 0.9, 0.8))])
