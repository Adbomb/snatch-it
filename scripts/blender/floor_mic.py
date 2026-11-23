"""Этаж «Золотой микрофон» музея-небоскрёба (первая партия новых этажей, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — гигантский концертный усилитель. Снаружи — чёрные стены-кейсы аппаратуры: панели «под кожу» с
золотыми уголками и хромированными рёбрами, спереди — два огромных динамика (хромовый обод, тёмный диффузор,
золотой колпачок), между ними — светящийся эквалайзер, сверху — панель усилителя с ручками, разъёмами и лампой
питания; по бокам — динамики поменьше, ручки и защёлки кейсов, жгуты кабелей; сзади — решётка вентиляции и панель
разъёмов. Издалека — чёрный блок с золотом и двумя кругами динамиков.
Внутри — концертный клуб: сцена из тёмного дерева с золотой кромкой и рампой, на ней — золотой микрофон на круглом
подиуме с фиолетовым кольцом, над ним — ферма с прожекторами; по бокам сцены — стены колонок, за сценой — экран со
звуковой волной; на стенах — акустические панели, гитары и золотые пластинки; в зале — танцпол из светящихся плиток,
у лифта — стойки с бархатным канатом и большая золотая пластинка над дверями.
Запуск: blender --background --factory-startup --python scripts/blender/floor_mic.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab, tube  # noqa: E402

BLACK, BLACK2, BLACK3, GRILLE = "24242C", "2E2E38", "1A1A20", "33333E"
GOLD, GOLD2, CHROME, CHROME2 = "F2C230", "C9921A", "C3CAD6", "8E96A4"
PURPLE, PURPLE2, PINK, CYAN, AMBER = "8B5CF6", "5B3AB0", "FF4FA8", "38D6F0", "FFB24A"
WOOD, WOOD2, VELVET, CREAM, FOAM, FOAM2 = "6A4428", "4E3220", "B0263A", "F2E8D5", "2B2B36", "35354A"

F = B.Floor("GM", "GoldenMic", quiet=(GRILLE, FOAM, FOAM2), bevel_min=1.0, keep_arch=True)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def speaker(S, R, G, axis, fixed, out, a, y, r, depth):
    """Динамик на стене: хромовый обод, тёмный подвес, диффузор ступенями внутрь, золотой колпачок."""
    def frame(p, ro, ri, d0, d1, color):
        o, i = K.octa(a, y, ro, ro, ro * 0.41), K.octa(a, y, ri, ri, ri * 0.41)
        lo, hi = sorted((fixed + out * d0, fixed + out * d1))
        if axis == "z":
            p.frame_xy(o, i, lo, hi, color)
        else:
            p.frame_zy(o, i, lo, hi, color)

    def disc(p, ro, d0, d1, color):
        pts = K.octa(a, y, ro, ro, ro * 0.41)
        lo, hi = sorted((fixed + out * d0, fixed + out * d1))
        if axis == "z":
            p.prism_xy(pts, lo, hi, color)
        else:
            p.prism_zy(pts, lo, hi, color)

    frame(S, r, r * 0.86, -0.05, depth + 0.35, CHROME)
    frame(S, r * 0.86, r * 0.7, -0.05, depth + 0.1, BLACK3)
    frame(S, r * 0.7, r * 0.42, -0.05, depth - 0.25, BLACK2)
    disc(S, r * 0.42, -0.05, depth - 0.55, BLACK3)
    disc(S, r * 0.26, depth - 0.6, depth - 0.2, GOLD)
    for k in range(8):  # винты обода
        t = 2 * math.pi * (k + 0.5) / 8
        u, v = a + r * 0.93 * math.cos(t), y + r * 0.93 * math.sin(t)
        slab(S, axis, fixed, out, depth + 0.45, u - 0.14, u + 0.14, v - 0.14, v + 0.14, GOLD2, back=-(depth + 0.3))


def knob(S, axis, fixed, out, a, y, r, depth):
    pts, cap = K.octa(a, y, r, r, r * 0.41), K.octa(a, y, r * 0.7, r * 0.7, r * 0.29)
    if axis == "z":
        S.prism_xy(pts, fixed + out * depth, fixed + out * (depth + 0.35), CHROME)
        S.prism_xy(cap, fixed + out * (depth + 0.35), fixed + out * (depth + 0.6), BLACK)
    else:
        S.prism_zy(pts, fixed + out * depth, fixed + out * (depth + 0.35), CHROME)
        S.prism_zy(cap, fixed + out * (depth + 0.35), fixed + out * (depth + 0.6), BLACK)
    slab(S, axis, fixed, out, depth + 0.65, a - 0.06, a + 0.06, y, y + r * 0.65, CREAM, back=-(depth + 0.5))


# ══ ФАСАД: гигантский усилитель ═══════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, BLACK3, BLACK3, BLACK3)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    # корпус: панели «под кожу», хромовые рёбра-разделители, цоколь
    slab(FR, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, -1.0, 1.4, BLACK2)
    slab(FS, axis, fixed, out, 2.0, -half - 2.0, half + 2.0, 1.4, 1.7, CHROME)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.7, 14.6, BLACK)
    slab(FS, axis, fixed, out, 1.0, -half - 1.0, half + 1.0, 14.6, 14.9, CHROME)
    slab(FR, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, 14.9, 19.0, BLACK2)  # панель усилителя
    slab(FS, axis, fixed, out, 1.96, -half + 1.0, half - 1.0, 15.4, 18.5, GOLD2)
    slab(FS, axis, fixed, out, 2.02, -half + 1.2, half - 1.2, 15.6, 18.3, GOLD)
    # ручки, разъёмы, лампа питания на панели
    n = 9 if axis == "z" else 8
    for k in range(n):
        a = -half + 3.5 + (2 * half - 7.0) * k / (n - 1)
        knob(FS, axis, fixed, out, a, 17.0, 0.62, 2.02)
    slab(FG, axis, fixed, out, 2.3, half - 2.4, half - 1.7, 16.6, 17.4, "FF5A3A", back=-1.9)
    for k in range(3):
        a = -half + 1.9 + 0.0 * k
        slab(FS, axis, fixed, out, 2.12, a - 0.25, a + 0.25, 16.0 + 0.9 * k, 16.5 + 0.9 * k, BLACK3)
    # рёбра кейса: хромовые угловые профили, золотые уголки
    for e in (-1, 1):
        slab(FS, axis, fixed, out, 1.2, e * (half - 0.6), e * (half + 1.2), 1.7, 14.6, CHROME2)
        for y0, y1 in ((1.4, 3.4), (12.9, 14.9), (17.0, 19.0)):
            slab(FS, axis, fixed, out, 2.2, e * (half - 1.4), e * (half + 2.2), y0, y1, GOLD)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))

# перед: два огромных динамика в сетке, эквалайзер посередине
slab(FQ, "z", -FZ, -1, 1.0, -15.4, -3.4, 2.2, 14.0, GRILLE)
speaker(FS, FR, FG, "z", -FZ, -1, -9.4, 8.1, 5.6, 1.6)  # басовик
slab(FQ, "z", -FZ, -1, 1.0, 3.4, 15.4, 2.2, 14.0, GRILLE)
speaker(FS, FR, FG, "z", -FZ, -1, 9.4, 10.9, 2.9, 1.5)  # средний
speaker(FS, FR, FG, "z", -FZ, -1, 9.4, 4.9, 2.9, 1.5)
for k in range(5):  # щель фазоинвертора и шильдик-полоса между динамиками справа
    slab(FS, "z", -FZ, -1, 1.2, 5.0 + 1.8 * k, 5.9 + 1.8 * k, 7.75, 8.05, BLACK3)
EQ = (3, 5, 7, 9, 6, 8, 4)
for k, h in enumerate(EQ):
    x = -2.7 + 0.9 * k
    for m in range(h):
        y = 2.6 + 1.25 * m
        color = PURPLE if m < 4 else PINK if m < 7 else AMBER
        FG.box(x - 0.34, x + 0.34, y, y + 0.9, -FZ - 1.15, -FZ - 1.3, color)
slab(FS, "z", -FZ, -1, 1.05, -3.3, 3.3, 2.2, 14.0, BLACK3)
# бока: динамики поменьше, ручки кейса, защёлки, жгуты кабелей
for s in (-1, 1):
    fx = s * FX
    slab(FQ, "x", fx, s, 1.0, -11.6, 11.6, 3.2, 12.8, GRILLE)
    speaker(FS, FR, FG, "x", fx, s, -5.5, 8.0, 4.3, 1.5)
    for k, (w, h, d) in enumerate(((3.4, 2.4, 1.2), (2.4, 1.6, 1.7), (1.4, 0.8, 2.1))):  # рупор ступенями
        slab(FS, "x", fx, s, d, 6.5 - w, 6.5 + w, 8.0 - h, 8.0 + h, CHROME if k == 0 else BLACK3 if k == 1 else BLACK)
    for y in (3.0, 13.4):  # ручки кейса
        slab(FS, "x", fx, s, 1.4, -1.2, 1.2, y - 0.2, y + 0.2, CHROME)
        slab(FS, "x", fx, s, 1.0, -1.4, 1.4, y - 0.45, y + 0.45, BLACK3)
    for z in (-13.0, 13.0):  # защёлки
        slab(FS, "x", fx, s, 1.3, z - 0.7, z + 0.7, 7.4, 8.8, GOLD2)
        slab(FS, "x", fx, s, 1.45, z - 0.35, z + 0.35, 7.7, 8.5, CHROME)
    tube(FS, [(fx + s * 1.2, 15.0, 1.5), (fx + s * 1.6, 10.0, 2.4), (fx + s * 1.3, 5.0, 1.0), (fx + s * 1.9, 0.8, 2.6)],
         [0.6, 0.6, 0.6, 0.6], 0.6, (s, 0, 0), BLACK3)
    tube(FS, [(fx + s * 1.2, 15.0, 2.4), (fx + s * 1.8, 10.0, 3.4), (fx + s * 1.4, 5.0, 2.0), (fx + s * 2.0, 0.8, 3.6)],
         [0.45, 0.45, 0.45, 0.45], 0.45, (s, 0, 0), PURPLE2)
# тыл: решётка вентиляции и панель разъёмов
for k in range(11):
    y = 3.0 + 1.0 * k
    slab(FS, "z", FZ, 1, 1.2, -11.0, 11.0, y, y + 0.45, BLACK2)
slab(FS, "z", FZ, 1, 1.0, -11.6, 11.6, 2.6, 14.0, GRILLE)
for k in range(6):
    x = -12.5 + 5.0 * k
    slab(FS, "z", FZ, 1, 1.3, x - 0.5, x + 0.5, 1.9, 2.5, GOLD2)

# ══ ИНТЕРЬЕР: концертный клуб ═════════════════════════════════════════════════════════════════════════════════
STAGE = (-6.0, 1.2)  # передний край сцены (z) и высота
MIC = (0.0, -9.5)  # подиум с микрофоном
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), FOAM)
# стены: акустические панели (квадраты двух тонов), низ — чёрный, золотая полоса
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    n = int(2 * half // 2)
    for i in range(n):
        a0 = -half + 2 * half * i / n
        a1 = -half + 2 * half * (i + 1) / n
        for j, (y0, y1) in enumerate(((2.0, 4.0), (4.0, 6.0), (6.0, 8.0), (8.0, 10.0), (10.0, 12.0), (12.0, 14.0))):
            if idx == 3 and abs((a0 + a1) / 2) < DOOR[0] + 1.6 and y0 < DOOR[1] + 2.0:
                continue
            slab(IQ, axis, fixed, out, 0.88 if (i + j) % 2 else 0.6, a0 + 0.06, a1 - 0.06, y0 + 0.06, y1 - 0.06,
                 FOAM if (i + j) % 2 else FOAM2)
    if idx != 3:
        slab(IR, axis, fixed, out, 0.88, -half, half, 0.0, 2.0, BLACK2)
    slab(IS, axis, fixed, out, 1.0, -half, half, 14.0, 14.4, GOLD2)
    slab(IR, axis, fixed, out, 0.88, -half, half, 14.4, C, BLACK3)
for a0, a1 in ((-W, -DOOR[0] - 1.6), (DOOR[0] + 1.6, W)):
    slab(IR, "z", ZB, -1, 0.88, a0, a1, 0.0, 2.0, BLACK2)
# сцена: тёмное дерево, золотая кромка, рампа, ступени сбоку
sz, sh = STAGE
IR.box(-W, W, 0.0, sh, ZF, sz, WOOD)
IS.box(-W, W, sh - 0.18, sh + 0.02, sz - 0.05, sz + 0.15, GOLD)
for k in range(11):
    x = -12.5 + 2.5 * k
    IG.box(x - 0.35, x + 0.35, 0.35, 0.7, sz + 0.02, sz + 0.12, AMBER)
for k in range(3):
    IS.box(9.0, 12.0, 0.4 * k, 0.4 * (k + 1), sz + 1.2 - 0.4 * k, sz + 1.6 - 0.4 * k, WOOD2)
F.objects(True)
# подиум с микрофоном: золотой обод, фиолетовое светящееся кольцо
mx, mz = MIC
IS.prism_xz(K.octa(mx, mz, 3.2, 3.2, 1.3), sh, sh + 0.5, BLACK)
IG.frame_xz(K.octa(mx, mz, 3.45, 3.45, 1.4), K.octa(mx, mz, 3.2, 3.2, 1.3), sh, sh + 0.25, PURPLE)
IR.prism_xz(K.octa(mx, mz, 2.6, 2.6, 1.05), sh + 0.5, sh + 0.8, GOLD)
IS.prism_xz(K.octa(mx, mz, 2.3, 2.3, 0.95), sh + 0.8, sh + 0.84, BLACK3)
# за сценой — экран со звуковой волной; стены колонок по бокам
IS.box(-7.5, 7.5, 3.0, 13.5, ZF + 0.9, ZF + 1.3, BLACK3)
for k in range(25):
    x = -6.6 + 0.55 * k
    h = 1.2 + 3.8 * abs(math.sin(k * 0.55)) * (0.6 + 0.4 * math.cos(k * 0.21))
    IG.box(x - 0.18, x + 0.18, 8.25 - h / 2, 8.25 + h / 2, ZF + 1.3, ZF + 1.36, CYAN if k % 4 else PURPLE)
for s in (-1, 1):
    for i in range(2):
        for j in range(3):
            x = s * (12.2 + 2.5 * i)
            y = sh + 2.6 * j
            IR.box(x - 1.2, x + 1.2, y, y + 2.5, ZF + 0.9, ZF + 3.4, BLACK2)
            IS.prism_xy(K.octa(x, y + 1.25, 0.95, 0.95, 0.4), ZF + 3.4, ZF + 3.5, GRILLE)
            IS.prism_xy(K.octa(x, y + 1.25, 0.35, 0.35, 0.14), ZF + 3.5, ZF + 3.65, GOLD)
    IS.box(s * 10.0, s * 16.0, sh, sh + 7.8, ZF + 3.0, ZF + 3.12, CHROME2)
F.objects(False)
# ферма над сценой с прожекторами
for z in (-12.5, -8.0):
    beam(IS, (-13.0, 15.8, z), (13.0, 15.8, z), 0.22, 0.22, CHROME)
    beam(IS, (-13.0, 16.8, z), (13.0, 16.8, z), 0.22, 0.22, CHROME)
for k in range(14):
    x = -13.0 + 2.0 * k
    for z in (-12.5, -8.0):
        beam(IS, (x, 15.8, z), (x + 1.0, 16.8, z), 0.12, 0.12, CHROME2)
        beam(IS, (x + 1.0, 16.8, z), (x + 2.0, 15.8, z), 0.12, 0.12, CHROME2)
for s in (-1, 1):
    beam(IS, (s * 13.0, 15.8, -12.5), (s * 13.0, 15.8, -8.0), 0.22, 0.22, CHROME)
    beam(IS, (s * 13.0, 0.0 + sh, -12.5), (s * 13.0, 16.8, -12.5), 0.3, 0.3, CHROME)
for k, (x, color) in enumerate(((-9.0, PINK), (-5.0, AMBER), (-1.5, "FFFFFF"), (1.5, "FFFFFF"), (5.0, AMBER),
                                (9.0, PURPLE))):
    z = -8.0
    IS.box(x - 0.55, x + 0.55, 14.3, 15.6, z - 0.55, z + 0.55, BLACK3)
    IG.box(x - 0.4, x + 0.4, 14.2, 14.32, z - 0.4, z + 0.4, color)
# зал: танцпол из светящихся плиток (приглушены в теме), гитары и пластинки на стенах
for i in range(-3, 3):
    for j in range(4):
        x0, z0 = i * 2.0 + 0.08, -4.0 + j * 2.0 + 0.08
        k = (i * 7 + j * 3) % 4
        color = (PURPLE2, "1F4F8A", "6A2A6A", "2A2A5A")[k]
        IG.box(x0, x0 + 1.84, 0.02, 0.06, z0, z0 + 1.84, color)
VGUITAR = [(0.0, -1.6), (1.3, 1.4), (0.75, 1.4), (0.0, -0.2), (-0.75, 1.4), (-1.3, 1.4)]  # электро-«V»
ACOUSTIC = [(-0.95, -1.5), (0.95, -1.5), (1.25, -0.6), (0.9, 0.2), (0.75, 0.55), (0.95, 1.2), (0.6, 1.7), (-0.6, 1.7),
            (-0.95, 1.2), (-0.75, 0.55), (-0.9, 0.2), (-1.25, -0.6)]
F.objects(True)
for s in (-1, 1):  # гитары на стене: корпус, гриф, голова с колками
    for z, shape, color in ((-1.0, VGUITAR, "E0343A"), (5.0, ACOUSTIC, "D89A3A")):
        x = s * (W - 0.95)
        IS.prism_zy([(z + u, 4.6 + v) for u, v in shape], x, x - s * 0.35, color)
        if shape is ACOUSTIC:
            IS.prism_zy(K.octa(z, 5.0, 0.35, 0.35, 0.14), x - s * 0.35, x - s * 0.42, BLACK3)
        else:
            IS.box(x - s * 0.35, x - s * 0.42, 3.8, 4.4, z - 0.45, z + 0.45, BLACK3)
        IS.box(x - s * 0.35, x - s * 0.42, 3.4, 3.6, z - 0.35, z + 0.35, CHROME)  # бридж
        IS.box(x, x - s * 0.25, 5.9, 10.4, z - 0.15, z + 0.15, WOOD2)
        IS.box(x, x - s * 0.3, 10.4, 11.5, z - 0.28, z + 0.28, BLACK)
        for k in range(3):
            for e in (-1, 1):
                IS.box(x - s * 0.1, x - s * 0.4, 10.6 + 0.3 * k, 10.75 + 0.3 * k, z + e * 0.28, z + e * 0.42, CHROME)
    for z in (-12.0, 11.0):  # золотые пластинки
        x = s * (W - 0.95)
        IS.frame_zy(K.octa(z, 9.0, 1.6, 1.6, 0.66), K.octa(z, 9.0, 0.45, 0.45, 0.19), x, x - s * 0.2, GOLD)
        IS.prism_zy(K.octa(z, 9.0, 0.45, 0.45, 0.19), x, x - s * 0.15, BLACK)
        IS.frame_zy(K.octa(z, 9.0, 2.0, 2.0, 0.83), K.octa(z, 9.0, 1.7, 1.7, 0.7), x, x - s * 0.12, CHROME2)
# у лифта: большая пластинка над дверями, стойки с бархатным канатом
IS.frame_xy(K.octa(0, DOOR[1] + 3.3, 2.6, 2.6, 1.08), K.octa(0, DOOR[1] + 3.3, 0.7, 0.7, 0.29), ZB - 0.9, ZB - 1.15, GOLD)
IS.prism_xy(K.octa(0, DOOR[1] + 3.3, 0.7, 0.7, 0.29), ZB - 0.9, ZB - 1.05, VELVET)
for s in (-1, 1):
    for z in (7.0, 10.5, 14.0):
        x = s * 5.4
        IS.prism_xz(K.octa(x, z, 0.32, 0.32, 0.13), 0.0, 0.12, GOLD2)
        IS.box(x - 0.08, x + 0.08, 0.12, 2.6, z - 0.08, z + 0.08, GOLD)
        IS.prism_xz(K.octa(x, z, 0.2, 0.2, 0.08), 2.6, 2.85, GOLD)
    beam(IS, (s * 5.4, 2.4, 7.0), (s * 5.4, 2.0, 10.5), 0.14, 0.14, VELVET)
    beam(IS, (s * 5.4, 2.0, 10.5), (s * 5.4, 2.4, 14.0), 0.14, 0.14, VELVET)
F.objects(False)
B.lift_leaves(IS, BLACK2, GOLD)
# потолок: звёздное небо из огоньков
for k in range(30):
    x, z = (rng(k, 41) - 0.5) * 30.0, (rng(k, 42) - 0.5) * 28.0
    if -14 < z < -6:
        continue
    IG.box(x - 0.1, x + 0.1, C - 0.06, C - 0.02, z - 0.1, z + 0.1, "F4E8FF")
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, BLACK)
SL.box(-FX - 1.9, FX + 1.9, 14.9, 19.0, -FZ - 1.9, FZ + 1.9, BLACK2)
SL.box(-FX - 2.0, FX + 2.0, 15.6, 18.3, -FZ - 2.0, FZ + 2.0, GOLD)
SL.box(-FX - 2.0, FX + 2.0, 1.4, 1.7, -FZ - 2.0, FZ + 2.0, CHROME)
SL.box(-15.0, -3.8, 2.5, 13.7, -FZ - 1.95, -FZ, CHROME)
SL.box(-13.4, -5.4, 4.1, 12.1, -FZ - 2.05, -FZ - 1.95, BLACK3)
SL.box(-10.6, -8.2, 6.9, 9.3, -FZ - 2.15, -FZ - 2.05, GOLD)
for y in (4.9, 10.9):
    SL.box(6.5, 12.3, y - 2.9, y + 2.9, -FZ - 1.85, -FZ, CHROME)
    SL.box(8.6, 10.2, y - 0.8, y + 0.8, -FZ - 1.95, -FZ - 1.85, GOLD)
SL.box(-2.9, 2.9, 2.6, 12.0, -FZ - 1.3, -FZ, PURPLE)
for s in (-1, 1):
    SL.box(s * FX, s * (FX + 1.85), 3.7, 12.3, -9.8, -1.2, CHROME)
    SL.box(s * FX, s * (FX + 1.95), 7.2, 8.8, -6.3, -4.7, GOLD)
    SL.box(s * FX, s * (FX + 1.2), 5.6, 10.4, 3.1, 9.9, BLACK3)
    for e in (-1, 1):
        SL.box(s * FX - 2.2, s * FX + 2.2, 12.9, 19.0, e * FZ - 2.2, e * FZ + 2.2, GOLD)

F.build(exhibit=(MIC[0], STAGE[1] + 0.84, MIC[1], 3.6), lamps=[("Hall", (0, 14, 6), 3500, (0.85, 0.8, 1.0)),
                                                               ("Spot", (0, 13, -8), 3000, (1.0, 0.95, 0.9))])
