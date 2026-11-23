"""Этаж «Монстр-радио» музея-небоскрёба (четвёртая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — радиостанция 50-х в корпусе гигантского лампового приёмника. Снаружи фасад — деревянный корпус радио
со скруглёнными ступенчатыми углами и латунной окантовкой: слева — огромная решётка динамика из ткани с
деревянными рейками, справа — круглая шкала настройки со светящимся циферблатом и красной стрелкой, под ней — ряд
крупных ручек и клавиш, сверху — латунная антенна-«усы»; от шкалы расходятся светящиеся дуги радиоволн, над
дверью — красная лампа «в эфире». Бока — ар-деко: кремовые рёбра, иллюминаторы, светящиеся радиолампы в
нишах; сзади — вышка-ферма с огнём на верхушке. Внутри — студия вещания: стены в деревянных панелях и акустических
квадратах двух тонов, микшерный пульт с ползунками и светящимися стрелочными индикаторами, винтажные микрофоны на
стойках, стеллажи с пластинками, катушечный магнитофон, стекло аппаратной, красная лампа «в эфире»; экспонат — на
круглом деревянном подиуме с латунным кантом.
Запуск: blender --background --factory-startup --python scripts/blender/floor_radio.py -- <репо> <превью>
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

WOOD, WOOD2, WOOD3, BRASS, BRASS2 = "A8683A", "84502A", "C8884E", "E8B848", "B8862A"
GRILLE, GRILLE2, CREAM, CREAM2, TEAL, TEAL2 = "D8C49A", "BFA878", "F4EAD2", "E0D2B4", "2E8A8A", "1E6A6E"
DIAL, NEEDLE, RED, AMBER, GLOW, DARK = "FFE8A8", "E83A2A", "E83A3A", "FFB040", "7AE8FF", "2A2420"
FOAM, FOAM2, VINYL, STEEL, STEEL2 = "6A3A5A", "4E2A46", "1A1A20", "B8BCC4", "8A8E98"

F = B.Floor("MR", "MonsterRadio", quiet=(GRILLE, GRILLE2, FOAM, FOAM2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def knob(p, x, y, z0, z1, r, col=DARK, cap=BRASS):
    """Ручка на передней стенке (лицом к −Z): рифлёное кольцо и латунная шляпка."""
    p.prism_xy([(x + r * math.cos(2 * math.pi * k / 16) * (1.0 if k % 2 else 0.88),
                 y + r * math.sin(2 * math.pi * k / 16) * (1.0 if k % 2 else 0.88)) for k in range(16)], z0, z1, col)
    p.prism_xy(K.ngon(x, y, r * 0.45, 8), z0 - 0.12, z0, cap)


def mic(p, x, z, h=5.0, face=-1):
    """Винтажный микрофон на стойке: тренога, штанга, капсула-«таблетка» в кольце."""
    for k in range(3):
        t = 2 * math.pi * k / 3 + 0.5
        beam(p, (x, 0.9, z), (x + 1.0 * math.cos(t), 0.0, z + 1.0 * math.sin(t)), 0.14, 0.14, STEEL2)
    p.prism_xz(K.ngon(x, z, 0.1, 6), 0.9, h, STEEL)
    p.box(x - 0.55, x + 0.55, h, h + 1.3, z - 0.22, z + 0.22, STEEL)
    p.box(x - 0.45, x + 0.45, h + 0.15, h + 1.15, *sorted((z + face * 0.22, z + face * 0.28)), "2A2A30")
    for k in range(4):
        p.box(x - 0.45, x + 0.45, h + 0.25 + 0.25 * k, h + 0.3 + 0.25 * k, *sorted((z + face * 0.28, z + face * 0.32)), STEEL2)


def tube_lamp(p, g, x, y, z, h=1.6):
    """Радиолампа: цоколь и светящаяся колба."""
    p.prism_xz(K.ngon(x, z, 0.35, 8), y, y + 0.4, DARK)
    g.prism_xz(K.ngon(x, z, 0.28, 8), y + 0.4, y + h, AMBER)
    g.prism_xz(K.ngon(x, z, 0.16, 8), y + h, y + h + 0.2, "FFE0A0")


# ══ ФАСАД: корпус лампового приёмника ═════════════════════════════════════════════════════════════════════════
B.shell_planes(F, CREAM, CREAM, DARK)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FR, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, 0.0, TEAL2)
    if fi == 0:
        continue
    slab(FR, axis, fixed, out, 1.88, -half - 0.4, half + 0.4, 0.0, 1.2, TEAL)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.2, 16.0, CREAM)
    for k in range(int(2 * half // 4.0) + 1):  # ар-деко рёбра
        a = -half + 2.0 + 4.0 * k
        if a > half - 1.0:
            break
        slab(FR, axis, fixed, out, 1.88, a - 0.6, a + 0.6, 1.2, 16.0, CREAM2)
        slab(FS, axis, fixed, out, 1.95, a - 0.2, a + 0.2, 1.2, 16.0, TEAL)
    slab(FR, axis, fixed, out, 1.88, -half - 0.4, half + 0.4, 16.0, 17.0, TEAL)
    slab(FR, axis, fixed, out, 1.0, -half, half, 17.0, 18.9, CREAM2)
    slab(FS, axis, fixed, out, 2.0, -half - 0.4, half + 0.4, 16.4, 16.7, BRASS)
    if axis == "x":  # бока: иллюминаторы и радиолампы в нишах
        for z in (-12.0, 12.0):
            d0, d1 = sorted((fixed + out * 0.88, fixed + out * 1.6))
            FS.frame_zy(K.ngon(z, 10.0, 2.0, 12), K.ngon(z, 10.0, 1.4, 12), d0, d1, BRASS)
            FG.prism_zy(K.ngon(z, 10.0, 1.4, 12), *sorted((fixed + out * 0.9, fixed + out * 0.95)), GLOW)
        for z in (-6.0, 0.0, 6.0):
            FS.box(*sorted((fixed + out * 0.88, fixed + out * 2.4)), 4.0, 4.4, z - 1.4, z + 1.4, DARK)
            FS.box(*sorted((fixed + out * 0.88, fixed + out * 2.4)), 10.0, 10.4, z - 1.4, z + 1.4, DARK)
            for e in (-0.7, 0.0, 0.7):
                tube_lamp(FS, FG, fixed + out * 1.6, 4.4, z + e, 3.0 + 1.0 * (e == 0.0))
# перед: деревянный корпус радио
FR.box(-FX - 0.6, FX + 0.6, 0.0, 18.9, -FZ - 0.88, -FZ, WOOD)
for k, (inset, y0, y1) in enumerate(((0.0, 0.0, 18.9), (1.0, 1.0, 17.9))):  # ступенчатые скругления по углам
    for sx in (-1, 1):
        FS.box(sx * (FX + 0.6) - sx * inset - sx * 1.0, sx * (FX + 0.6) - sx * inset, y0, y1, -FZ - 1.88 - 0.6 * k, -FZ - 0.88,
               (WOOD2, WOOD3)[k])
FS.box(-FX + 1.4, FX - 1.4, 0.0, 1.4, -FZ - 2.2, -FZ - 0.88, WOOD2)  # цоколь корпуса
FS.box(-FX + 1.4, FX - 1.4, 17.2, 18.9, -FZ - 2.2, -FZ - 0.88, WOOD2)  # верх корпуса
FS.frame_xy(K.rect(-FX + 1.4, FX - 1.4, 1.4, 17.2), K.rect(-FX + 1.8, FX - 1.8, 1.8, 16.8), -FZ - 2.3, -FZ - 0.88, BRASS)
# слева: огромная решётка динамика — ткань и деревянные рейки
GX0, GX1, GY0, GY1 = -15.6, -1.4, 3.8, 16.2
FQ.box(GX0, GX1, GY0, GY1, -FZ - 1.2, -FZ - 0.88, GRILLE)
GCX = (GX0 + GX1) / 2
for k in range(9):  # деревянные рейки веером (как у старых приёмников)
    t = math.radians(30 + 120 * k / 8)
    L = min((GY1 - GY0 - 0.3) / max(math.sin(t), 0.01), (GX1 - GX0) / 2 / max(abs(math.cos(t)), 0.01) - 0.2)
    beam(FS, (GCX, GY0 + 0.3, -FZ - 1.45), (GCX + L * math.cos(t), GY0 + 0.3 + L * math.sin(t), -FZ - 1.45), 0.5, 0.5, WOOD3)
FS.prism_xy(K.ngon(GCX, GY0 + 0.3, 1.6, 12)[:7], -FZ - 1.8, -FZ - 1.2, WOOD2)
FS.frame_xy(K.rect(GX0 - 0.5, GX1 + 0.5, GY0 - 0.5, GY1 + 0.5), K.rect(GX0, GX1, GY0, GY1), -FZ - 2.0, -FZ - 0.88, WOOD2)
# справа: круглая шкала настройки со светящимся циферблатом, стрелкой и делениями; радиоволны
DX, DY, DR = 8.6, 11.0, 4.6
FS.frame_xy(K.ngon(DX, DY, DR + 0.8, 24), K.ngon(DX, DY, DR, 24), -FZ - 2.2, -FZ - 0.88, BRASS)
FG.prism_xy(K.ngon(DX, DY, DR, 24), -FZ - 1.0, -FZ - 0.94, DIAL)
for k in range(13):
    t = math.pi * (0.1 + 0.8 * k / 12)
    FS.box(DX + (DR - 0.9) * math.cos(t) - 0.08, DX + (DR - 0.9) * math.cos(t) + 0.08, DY - 0.6 + (DR - 0.9) * math.sin(t) - 0.35,
           DY - 0.6 + (DR - 0.9) * math.sin(t) + 0.35, -FZ - 1.06, -FZ - 1.0, DARK)
t = math.radians(62)
FS.prism_xy([(DX - 0.15, DY - 1.4), (DX + 0.15, DY - 1.4), (DX + 3.6 * math.cos(t) + 0.08, DY - 1.4 + 3.6 * math.sin(t)),
             (DX + 3.6 * math.cos(t) - 0.08, DY - 1.4 + 3.6 * math.sin(t))], -FZ - 1.14, -FZ - 1.06, NEEDLE)
FS.prism_xy(K.ngon(DX, DY - 1.4, 0.4, 8), -FZ - 1.2, -FZ - 1.0, BRASS)
for k, r in enumerate((6.4, 7.6, 8.8)):  # дуги радиоволн справа от шкалы
    pts_o = [(DX + r * math.cos(a), DY + r * math.sin(a)) for a in [math.radians(-35 + 70 * m / 6) for m in range(7)]]
    pts_i = [(DX + (r - 0.35) * math.cos(a), DY + (r - 0.35) * math.sin(a)) for a in [math.radians(-35 + 70 * m / 6) for m in range(7)]]
    poly = [q for q in pts_o if q[0] < FX + 0.4] + [q for q in pts_i if q[0] < FX + 0.4][::-1]
    if len(poly) >= 4:
        FG.prism_xy(poly, -FZ - 0.98, -FZ - 0.9, (GLOW, "A8F4FF", GLOW)[k])
# под шкалой — ручки и клавиши, дверь между решёткой и шкалой
for k, x in enumerate((4.2, 8.6, 13.0)):
    knob(FS, x, 3.4, -FZ - 2.0, -FZ - 0.88, 1.2 if k != 1 else 1.5)
for k in range(5):
    x = 1.2 + 1.0 * k
    FS.box(x - 0.4, x + 0.4, 5.6, 6.6, -FZ - 1.3, -FZ - 0.88, (CREAM, CREAM2)[k % 2])
FS.box(-1.0, 1.0, 1.4, 6.2, -FZ - 1.0, -FZ - 0.88, DARK)  # узкая дверь
FG.box(-0.8, 0.8, 7.0, 7.8, -FZ - 1.3, -FZ - 1.0, RED)  # лампа «в эфире»
FS.frame_xy(K.rect(-1.0, 1.0, 6.8, 8.0), K.rect(-0.8, 0.8, 7.0, 7.8), -FZ - 1.4, -FZ - 0.88, BRASS2)
# латунная антенна-«усы» на крыше корпуса
for s in (-1, 1):
    beam(FS, (s * 1.2, 17.6, -FZ - 2.6), (s * 9.0, 18.6, -FZ - 3.4), 0.35, 0.35, BRASS)
    FS.prism_xz(K.ngon(s * 9.0, -FZ - 3.4, 0.4, 8), 18.4, 18.9, RED)
FS.box(-1.6, 1.6, 16.8, 17.8, -FZ - 2.9, -FZ - 0.9, BRASS2)
# сзади: вышка-ферма
for k in range(6):
    y = 1.0 + 2.9 * k
    w = 2.4 - 0.3 * k
    for e in (-1, 1):
        beam(FS, (e * w, y, FZ + 2.4), (e * (w - 0.3), y + 2.9, FZ + 2.4), 0.25, 0.25, RED if k % 2 else CREAM)
    beam(FS, (-w, y, FZ + 2.4), (w - 0.3, y + 2.9, FZ + 2.4), 0.18, 0.18, STEEL)
FG.prism_xz(K.ngon(0.0, FZ + 2.4, 0.4, 8), 18.4, 18.9, RED)
FS.box(-3.0, 3.0, 0.0, 1.0, FZ + 0.9, FZ + 3.9, STEEL2)

# ══ ИНТЕРЬЕР: студия вещания ══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), FOAM2)
for i in range(-4, 4):  # паркет «ёлочкой» крупно
    for j in range(-4, 4):
        x, z = 4.2 * i + 2.1, 4.0 * j + 2.0
        IR.box(x - 2.0, x + 2.0, 0.0, 0.1, z - 1.9, z + 1.9, (WOOD3, WOOD)[(i + j) % 2])
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 4.0, WOOD2)  # деревянные панели понизу
        if gap:
            slab(IR, axis, fixed, out, 0.88, a0, a1, 4.0, DOOR[1] + 0.1, WOOD)
            continue
        n = int((a1 - a0) // 2.0)
        for k in range(n):  # акустические квадраты двух тонов
            for r in range(5):
                b0 = a0 + (a1 - a0) * k / n
                y = 4.0 + 2.0 * r
                slab(IQ, axis, fixed, out, 0.88 + 0.2 * ((k + r) % 2), b0 + 0.06, b0 + (a1 - a0) / n - 0.06, y + 0.06, y + 1.94,
                     (FOAM, FOAM2)[(k + r) % 2])
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 14.0, WOOD)
        slab(IR, axis, fixed, out, 0.88, -half, half, DOOR[1] + 0.1, 14.0, WOOD)
    slab(IS, axis, fixed, out, 1.0, -half, half, 3.9, 4.2, BRASS)
    slab(IR, axis, fixed, out, 0.88, -half, half, 14.0, C, WOOD2)
# стекло аппаратной на передней стене: рама, светящиеся приборы за стеклом, лампа «в эфире»
IR.box(-8.0, 8.0, 6.0, 12.0, ZF + 0.88, ZF + 1.2, DARK)
IG.box(-7.6, 7.6, 6.4, 11.6, ZF + 1.2, ZF + 1.24, "2A4A5A")
for k in range(8):
    x = -6.8 + 1.9 * k
    IG.box(x - 0.6, x + 0.6, 7.0 + 1.4 * (k % 3), 7.6 + 1.4 * (k % 3), ZF + 1.24, ZF + 1.3, (AMBER, GLOW, "7AF07A")[k % 3])
IS.frame_xy(K.rect(-8.4, 8.4, 5.6, 12.4), K.rect(-8.0, 8.0, 6.0, 12.0), ZF + 0.88, ZF + 1.6, WOOD3)
IG.box(-1.6, 1.6, 13.0, 14.2, ZF + 0.88, ZF + 1.3, RED)
IS.frame_xy(K.rect(-1.9, 1.9, 12.7, 14.5), K.rect(-1.6, 1.6, 13.0, 14.2), ZF + 0.88, ZF + 1.4, BRASS)
# микшерный пульт: наклонная панель, ползунки, стрелочные индикаторы
IR.box(-7.0, 7.0, 0.0, 2.6, ZF + 2.6, ZF + 5.0, WOOD)
IS.prism_zy([(ZF + 2.4, 2.6), (ZF + 5.2, 2.6), (ZF + 5.2, 3.0), (ZF + 2.4, 3.8)], -7.2, 7.2, DARK)
for k in range(12):
    x = -6.0 + 1.1 * k
    IS.box(x - 0.08, x + 0.08, 3.0, 3.5, ZF + 3.6, ZF + 4.6, STEEL2)
    IS.box(x - 0.25, x + 0.25, 3.3, 3.6, ZF + 3.6 + 0.8 * rng(k, 2), ZF + 3.9 + 0.8 * rng(k, 2), (CREAM, RED, BRASS)[k % 3])
for x in (-4.0, 0.0, 4.0):
    IS.box(x - 1.2, x + 1.2, 3.6, 5.2, ZF + 2.4, ZF + 2.8, DARK)
    IG.box(x - 1.0, x + 1.0, 3.8, 5.0, ZF + 2.8, ZF + 2.84, DIAL)
    IS.box(x - 0.05, x + 0.05, 3.9, 4.9, ZF + 2.84, ZF + 2.9, NEEDLE)
# микрофоны на стойках, стеллажи с пластинками, катушечный магнитофон, кресла
for x, z in ((-8.6, -8.0), (8.6, -8.0), (-9.0, 3.0)):
    mic(IS, x, z, 4.4, face=1)
for s in (-1, 1):
    x0, x1 = sorted((s * W, s * (W - 2.0)))
    for r in range(4):
        y = 0.6 + 1.9 * r
        IS.box(x0, x1, y - 0.15, y, -12.0, 0.0, WOOD3)
        for k in range(16):
            z = -11.6 + 0.72 * k
            if rng(s, r, k) < 0.2:
                continue
            IS.box(*sorted((s * (W - 0.2), s * (W - 1.8))), y, y + 1.6, z, z + 0.12, (VINYL, RED, TEAL, BRASS, CREAM)[int(rng(k, r) * 5)])
    IS.box(x0, x1, 0.0, 7.8, -12.2, -12.0, WOOD2)
    IS.box(x0, x1, 0.0, 7.8, 0.0, 0.2, WOOD2)
rx, rz = 11.0, 7.0  # магнитофон
IS.box(rx - 1.6, rx + 1.6, 0.0, 4.6, rz - 1.0, rz + 1.0, STEEL2)
for e in (-0.8, 0.8):
    IS.prism_xy(K.ngon(rx + e, 3.6, 0.7, 12), rz - 1.2, rz - 1.0, VINYL)
    IS.prism_xy(K.ngon(rx + e, 3.6, 0.2, 6), rz - 1.3, rz - 1.2, STEEL)
IG.box(rx - 1.0, rx + 1.0, 1.4, 2.0, rz - 1.06, rz - 1.0, GLOW)
for x, z, col in ((-11.0, 7.0, RED), (-11.0, 10.4, TEAL)):  # кресла
    IS.box(x - 1.3, x + 1.3, 0.0, 1.4, z - 1.2, z + 1.2, col)
    IS.box(x - 1.3, x + 1.3, 1.4, 3.2, z + 0.8, z + 1.3, col)
# подвесные лампы-радиолампы над постаментом
for x in (-5.0, 5.0):
    IS.box(x - 0.04, x + 0.04, 13.0, C, -3.04, -2.96, DARK)
    tube_lamp(IS, IG, x, 11.0, -3.0, 2.0)
# круглый деревянный подиум с латунным кантом
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, 0.5, WOOD2)
IR.prism_xz(K.ngon(px, pz, 3.3, 16), 0.5, TOP, WOOD3)
ring_y(IS, px, pz, 3.3, 3.5, 0.5, TOP + 0.06, BRASS, n=16)
ring_y(IS, px, pz, 4.0, 4.15, 0.0, 0.56, BRASS, n=16)
B.lift_leaves(IS, WOOD2, BRASS)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ + 0.1, FZ, CREAM)
SL.box(-FX - 2.9, FX + 2.9, -1.0, 0.0, -FZ - 2.9, FZ + 2.9, TEAL2)
SL.box(-FX - 0.6, FX + 0.6, 0.0, 18.9, -FZ - 1.88, -FZ + 0.1, WOOD)
SL.box(GX0, GX1, GY0, GY1, -FZ - 1.9, -FZ - 1.88, GRILLE)
SL.prism_xy(K.ngon(DX, DY, DR, 10), -FZ - 1.94, -FZ - 1.88, DIAL)
SL.box(-FX - 1.9, FX + 1.9, 16.0, 17.0, -FZ + 0.1, FZ + 1.9, TEAL)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 2800, (1.0, 0.92, 0.82)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.96, 0.9)),
                                                   ("Glow", (0, 9, -12), 700, (1.0, 0.7, 0.4))])
