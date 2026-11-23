"""Этаж «Магический гриб» музея-небоскрёба (первая партия новых этажей, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — сказочный дом-гриб. Снаружи — стены-ножка гриба (кремовые продольные бороздки) с круглыми окнами в
деревянных рамах, светящимися янтарём; наверху — огромная фиолетовая шляпка в белых пятнах, нависает над стенами,
снизу видны пластинки; из стен растут маленькие светящиеся грибы (розовые, голубые, жёлтые), внизу — мох, корни и
цветы, с края шляпки свисают лианы, вокруг — светлячки. Издалека — фиолетовая шляпка на светлой ножке.
Внутри — волшебная поляна под шляпкой: потолок — пластинки гриба лучами от центра, стены — кора и корни со мхом,
моховой пол, дорожка из камней от лифта, ручей, большие светящиеся грибы по углам, у лифта — корни аркой.
Главный экспонат — гриб на старом пне; вокруг — ведьмин круг из маленьких светящихся грибов и парящие споры.
Запуск: blender --background --factory-startup --python scripts/blender/floor_mushroom.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, chamfer, rng, slab, taper, tube  # noqa: E402

CAP, CAP2, SPOT, GILL, GILL2 = "8E44D9", "6A2FB0", "F6F0FF", "D9C2F0", "B79AD8"
STEM, STEM2, STEM3 = "F2E8D5", "E2D3B8", "CDBB98"
MOSS, MOSS2, BARK, BARK2, ROOT = "4E9A3A", "3A7A2C", "6B4A2E", "4E3520", "5A3D24"
PINK, CYAN, YEL, WIN, WATER = "FF6FD0", "4FE0F0", "FFE07A", "FFC85A", "3FB6D8"
STONE, STONE2, FLOWER1, FLOWER2, LEAF = "8E9098", "6E7078", "FF8AD8", "FFD84A", "5DA83E"
FOREST, DEEP, GILL_IN = "2A4A34", "1C3326", "5C3F84"

F = B.Floor("MM", "MagicMushroom", quiet=(MOSS, MOSS2, GILL, GILL2, GILL_IN), keep_arch=True)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def mushroom(S, G, base, direction, length, cap_r, cap_color, glow, stem=STEM, tilt_up=0.35):
    """Гриб: изогнутая ножка от base по направлению (с подъёмом), шляпка ступенями, светящаяся кайма снизу."""
    bx, by, bz = base
    dx, dz = direction
    tip = (bx + dx * length, by + length * tilt_up + 0.4, bz + dz * length)
    mid = (bx + dx * length * 0.55, by + length * tilt_up * 0.3, bz + dz * length * 0.55)
    tube(S, [base, mid, tip], [0.9 * cap_r * 0.6, 0.75 * cap_r * 0.6, 0.6 * cap_r * 0.6], 0.6 * cap_r * 0.6,
         (-dz, 0, dx) if (dx or dz) else (1, 0, 0), stem)
    x, y, z = tip
    G.prism_xz(K.octa(x, z, cap_r * 0.92, cap_r * 0.92, cap_r * 0.38), y - 0.12, y + 0.02, glow)  # кайма снизу
    S.prism_xz(K.octa(x, z, cap_r, cap_r, cap_r * 0.4), y, y + cap_r * 0.35, cap_color)
    S.prism_xz(K.octa(x, z, cap_r * 0.7, cap_r * 0.7, cap_r * 0.28), y + cap_r * 0.35, y + cap_r * 0.6, cap_color)
    S.prism_xz(K.octa(x, z, cap_r * 0.35, cap_r * 0.35, cap_r * 0.14), y + cap_r * 0.6, y + cap_r * 0.72, cap_color)
    S.box(x + cap_r * 0.3, x + cap_r * 0.55, y + cap_r * 0.3, y + cap_r * 0.42, z - 0.15, z + 0.15, SPOT)


def upright(S, G, x, z, y0, h, r, cap_color, glow, stem=STEM):
    """Прямой гриб: ножка восьмигранником, шляпка ступенями, светящаяся кайма."""
    S.prism_xz(K.octa(x, z, r * 0.32, r * 0.32, r * 0.13), y0, y0 + h, stem)
    G.prism_xz(K.octa(x, z, r * 0.9, r * 0.9, r * 0.36), y0 + h - 0.12, y0 + h + 0.02, glow)
    S.prism_xz(K.octa(x, z, r, r, r * 0.4), y0 + h, y0 + h + r * 0.32, cap_color)
    S.prism_xz(K.octa(x, z, r * 0.66, r * 0.66, r * 0.26), y0 + h + r * 0.32, y0 + h + r * 0.55, cap_color)


# ══ ФАСАД: дом-гриб ═══════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, STEM3, BARK2, GILL_IN)
CAP_PROF = [(0.0, 13.4), (4.2, 13.4), (4.2, 15.0), (3.6, 16.6), (2.4, 18.0), (1.0, 18.9), (0.0, 19.0)]
WINDOWS = {0: (-9.0, 0.0, 9.0), 1: (-8.0, 8.0), 2: (-7.0, 7.0), 3: (-7.0, 7.0)}
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    # мох и камни понизу
    slab(FQ, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, -1.0, 1.6, MOSS)
    k = -half + 1.5
    while k < half - 1.0:
        w = 1.4 + 1.2 * rng(fi, k)
        slab(FR, axis, fixed, out, 2.88, k, k + w, -1.0, 0.4 + 0.8 * rng(k, fi), STONE if rng(fi, k, 2) > 0.5 else STONE2)
        k += w + 1.6 + 2.0 * rng(k, 3)
    # ножка: продольные бороздки через стад
    n = int(2 * half // 2)
    for i in range(n):
        a0 = -half + 2 * half * i / n
        a1 = -half + 2 * half * (i + 1) / n
        slab(FR, axis, fixed, out, 0.88, a0 + 0.06, a1 - 0.06, 1.6, 13.4, STEM if i % 2 == 0 else STEM2)
    slab(FS, axis, fixed, out, 1.1, -half - 1.1, half + 1.1, 1.6, 2.0, STEM3)
    # круглые окна в деревянных рамах, светятся янтарём; переплёт крестом
    for a in WINDOWS[fi]:
        y = 8.0
        o, i_ = K.octa(a, y, 2.1, 2.1, 0.87), K.octa(a, y, 1.55, 1.55, 0.64)
        lo, hi = sorted((fixed - out * 0.05, fixed + out * 1.5))
        if axis == "z":
            FS.frame_xy(o, i_, lo, hi, BARK)
            FG.prism_xy(i_, fixed + out * 0.95, fixed + out * 1.05, WIN)
        else:
            FS.frame_zy(o, i_, lo, hi, BARK)
            FG.prism_zy(i_, fixed + out * 0.95, fixed + out * 1.05, WIN)
        slab(FS, axis, fixed, out, 1.2, a - 0.12, a + 0.12, y - 1.6, y + 1.6, BARK2)
        slab(FS, axis, fixed, out, 1.2, a - 1.6, a + 1.6, y - 0.12, y + 0.12, BARK2)
        slab(FS, axis, fixed, out, 1.6, a - 1.6, a + 1.6, y - 2.4, y - 2.0, BARK)  # подоконник
        slab(FQ, axis, fixed, out, 1.7, a - 1.4, a + 1.4, y - 2.0, y - 1.75, MOSS2)
    # шляпка: нависающий край, пластинки снизу, белые пятна
    chamfer(FR, axis, fixed, out, -half - 4.2, half + 4.2, CAP_PROF, CAP)
    k = -half - 3.0
    while k < half + 3.0:
        slab(FS, axis, fixed, out, 3.5, k - 0.12, k + 0.12, 12.9, 13.42, GILL)
        k += 1.3
    for j in range(8):  # пятна на вертикальном крае шляпки (вразбежку по высоте)
        a = -half + 2.5 + (2 * half - 5.0) * j / 7 + (rng(fi, j) - 0.5) * 1.4
        w = 0.6 + 0.45 * rng(fi, j, 2)
        y = 13.65 if j % 2 == 0 else 14.05
        slab(FS, axis, fixed, out, 4.32, a - w, a + w, y, min(y + w * 1.3, 14.9), SPOT, back=-3.9)
    # лианы с края шляпки
    for j in range(5):
        a = -half + 3.5 + (2 * half - 7.0) * j / 4 + rng(fi, j, 5) * 1.2
        if fi == 0 and abs(a) < 3.0:
            continue
        ln = 2.5 + 3.5 * rng(fi, j, 6)
        slab(FS, axis, fixed, out, 2.6, a - 0.14, a + 0.14, 13.4 - ln, 13.4, LEAF)
        for m in range(int(ln // 1.4)):
            yy = 13.0 - 1.4 * m
            s = 1 if m % 2 else -1
            slab(FS, axis, fixed, out, 2.75, a + s * 0.1, a + s * 0.55, yy - 0.25, yy, MOSS)
    # цветы во мху
    for j in range(6):
        a = -half + 2.0 + (2 * half - 4.0) * rng(fi, j, 7)
        slab(FS, axis, fixed, out, 2.1, a - 0.25, a + 0.25, 1.6, 2.2, FLOWER1 if j % 2 else FLOWER2)
B.anchor(FR, (-23, -1, -22), (23, 19, 22))
B.anchor(FQ, (-23, -1, -22), (23, 19, 22))

F.objects(True)
# светящиеся грибы на стенах (из щелей между бороздками)
for (x, y, z), d, L, r, cap, glow in (
        ((-FX, 4.0, -12.0), (-1, 0), 2.6, 1.3, "FF4FB8", PINK), ((-FX, 10.6, 3.0), (-1, 0), 2.0, 1.0, "35C6E0", CYAN),
        ((FX, 5.5, 12.5), (1, 0), 2.4, 1.2, "F2B630", YEL), ((FX, 3.2, -4.0), (1, 0), 2.0, 1.1, "FF4FB8", PINK),
        ((-13.5, 3.2, -FZ), (0, -1), 2.4, 1.2, "35C6E0", CYAN), ((13.0, 11.0, -FZ), (0, -1), 2.0, 1.0, "FF4FB8", PINK),
        ((12.0, 4.0, FZ), (0, 1), 2.2, 1.1, "35C6E0", CYAN)):
    mushroom(FS, FG, (x, y, z), d, L, r, cap, glow)
# светлячки
for j in range(14):
    fi = j % 4
    axis, fixed, out, half = B.FACES[fi]
    a = -half + 2 * half * rng(j, 11)
    y = 2.5 + 9.0 * rng(j, 12)
    slab(FG, axis, fixed, out, 3.2 + 1.5 * rng(j, 13), a - 0.12, a + 0.12, y - 0.12, y + 0.12, YEL, back=-2.9)

F.objects(False)
# ══ ИНТЕРЬЕР: поляна под шляпкой ═══════════════════════════════════════════════════════════════════════════════
STUMP = (0.0, -3.0)  # пень с главным грибом
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), MOSS)

# стены: кора с корнями, мох понизу, окна изнутри
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    n = int(2 * half // 2)
    for i in range(n):
        a0 = -half + 2 * half * i / n
        a1 = -half + 2 * half * (i + 1) / n
        if idx == 3 and abs((a0 + a1) / 2) < DOOR[0] + 1.5:
            slab(IR, axis, fixed, out, 0.88, a0 + 0.05, a1 - 0.05, DOOR[1] + 1.2, C, BARK if i % 2 else BARK2)
            continue
        slab(IR, axis, fixed, out, 0.88, a0 + 0.05, a1 - 0.05, 0.0, C, BARK if i % 2 else BARK2)
    if idx != 3:  # мох понизу (кроме стены лифта)
        slab(IQ, axis, fixed, out, 1.3, -half, half, 0.0, 1.4, MOSS2)
    for j in range(5):  # корни: изогнутые жгуты по стене от потолка к полу
        a = -half + 3.0 + (2 * half - 6.0) * j / 4
        if idx == 3 and abs(a) < DOOR[0] + 2.0:
            continue
        sgn = 1 if j % 2 else -1
        if axis == "x":
            pts = [(fixed + out * 1.2, 17.5, a), (fixed + out * 1.8, 11.0, a + sgn * 1.2), (fixed + out * 1.5, 5.0, a - sgn * 0.6),
                   (fixed + out * 2.4, 0.4, a + sgn * 1.0)]
        else:
            pts = [(a, 17.5, fixed + out * 1.2), (a + sgn * 1.2, 11.0, fixed + out * 1.8), (a - sgn * 0.6, 5.0, fixed + out * 1.5),
                   (a + sgn * 1.0, 0.4, fixed + out * 2.4)]
        tube(IS, pts, [1.2, 1.0, 0.9, 1.1], 0.9, (out, 0, 0) if axis == "x" else (0, 0, out), ROOT)
for s in (-1, 1):  # окна изнутри
    for z in (-7.0, 7.0):
        IG.prism_zy(K.octa(z, 8.0, 1.5, 1.5, 0.62), s * (W - 0.9), s * (W - 0.95), WIN)
        IS.frame_zy(K.octa(z, 8.0, 2.0, 2.0, 0.83), K.octa(z, 8.0, 1.5, 1.5, 0.62), s * (W - 0.85), s * (W - 1.4), BARK2)
for x in (-9.0, 0.0, 9.0):
    IG.prism_xy(K.octa(x, 8.0, 1.5, 1.5, 0.62), ZF + 0.9, ZF + 0.95, WIN)
    IS.frame_xy(K.octa(x, 8.0, 2.0, 2.0, 0.83), K.octa(x, 8.0, 1.5, 1.5, 0.62), ZF + 0.85, ZF + 1.4, BARK2)

# потолок — пластинки шляпки лучами от центра над пнём
cx, cz = STUMP
for k in range(28):
    t = 2 * math.pi * k / 28
    c, sn = math.cos(t), math.sin(t)  # луч до стены зала, не сквозь неё
    r1 = min((W - 0.3 - cx * (1 if c > 0 else -1)) / max(abs(c), 1e-6), ((ZB if sn > 0 else -ZF) - 0.3 - cz * (1 if sn > 0 else -1)) / max(abs(sn), 1e-6))
    a = (cx + 2.2 * math.cos(t), C - 0.02, cz + 2.2 * math.sin(t))
    b = (cx + r1 * math.cos(t), C - 0.02, cz + r1 * math.sin(t))
    beam(IS, (a[0], a[1] - 0.6, a[2]), (b[0], b[1] - 0.6, b[2]), 0.22, 1.2, GILL2 if k % 2 else GILL)
IS.prism_xz(K.octa(cx, cz, 2.4, 2.4, 1.0), C - 1.4, C - 0.01, CAP2)
IG.prism_xz(K.octa(cx, cz, 1.4, 1.4, 0.58), C - 1.5, C - 1.38, "E8C8FF")

# моховой пол: камни-дорожка от лифта, ручей с мостиком, цветы
for k in range(7):
    z = 13.0 - 2.1 * k
    x = 0.6 * math.sin(k * 1.3)
    IR.prism_xz(K.octa(x, z, 0.95, 0.75, 0.35), 0.02, 0.22, STONE if k % 2 else STONE2)
for k in range(10):  # ручей поперёк зала у передней стены
    x0 = -W + k * (2 * W / 10)
    x1 = x0 + 2 * W / 10
    z0 = -11.5 + 0.8 * math.sin(k * 0.9)
    IG.box(x0, x1, 0.03, 0.08, z0, z0 + 1.6, WATER)
for j in range(22):
    x, z = (rng(j, 21) - 0.5) * 28.0, (rng(j, 22) - 0.5) * 24.0
    if abs(x) < 6 and -9 < z < 3 or abs(x) < 3 and z > 3:
        continue
    IS.box(x - 0.18, x + 0.18, 0.0, 0.7, z - 0.18, z + 0.18, LEAF)
    IS.box(x - 0.32, x + 0.32, 0.7, 0.95, z - 0.32, z + 0.32, FLOWER1 if j % 3 == 0 else FLOWER2 if j % 3 == 1 else "8FD8FF")

F.objects(True)
# большие светящиеся грибы по углам и у стен
for x, z, h, r, cap, glow in ((-13.0, -12.0, 7.0, 2.6, "E04AA8", PINK), (12.6, -12.4, 8.0, 2.9, "2FB0CC", CYAN),
                              (-13.6, 6.5, 4.6, 2.0, "E0A82A", YEL), (13.6, 2.5, 5.6, 2.2, "E04AA8", PINK),
                              (-8.5, -13.4, 3.4, 1.5, "2FB0CC", CYAN)):
    upright(IS, IG, x, z, 0.0, h, r, cap, glow, stem=STEM2)

# пень с главным грибом, корни, ведьмин круг, парящие споры
IS.prism_xz(K.octa(cx, cz, 4.6, 4.6, 1.85), 0.0, 0.6, ROOT)
IR.prism_xz(K.octa(cx, cz, 4.2, 4.2, 1.7), 0.0, 1.7, BARK)
IS.prism_xz(K.octa(cx, cz, 4.0, 4.0, 1.62), 1.7, 1.8, STEM2)
for rr, color in ((3.0, STEM3), (1.8, STEM2)):
    IS.frame_xz(K.octa(cx, cz, rr + 0.15, rr + 0.15, (rr + 0.15) * 0.4), K.octa(cx, cz, rr, rr, rr * 0.4), 1.8, 1.84,
                color)
IQ.prism_xz(K.octa(cx, cz + 3.6, 1.2, 0.6, 0.3), 1.8, 1.95, MOSS)
for k in range(6):
    t = 2 * math.pi * k / 6 + 0.3
    a = (cx + 3.6 * math.cos(t), 0.8, cz + 3.6 * math.sin(t))
    b = (cx + 6.2 * math.cos(t), 0.15, cz + 6.2 * math.sin(t))
    tube(IS, [a, b], [1.0, 0.5], 0.7, (0, 1, 0), ROOT)
for k in range(12):
    t = 2 * math.pi * k / 12
    x, z = cx + 7.2 * math.cos(t), cz + 6.4 * math.sin(t)
    if z > cz + 5.0 and abs(x - cx) < 2.5:
        continue  # проход к пню со стороны лифта
    upright(IS, IG, x, z, 0.0, 0.8 + 0.5 * (k % 3), 0.55 + 0.15 * (k % 2), "FF4FB8" if k % 2 else "35C6E0",
            PINK if k % 2 else CYAN)
for k in range(16):
    t = 2 * math.pi * rng(k, 31)
    r = 3.5 + 4.0 * rng(k, 32)
    x, z, y = cx + r * math.cos(t), cz + r * math.sin(t), 3.0 + 9.0 * rng(k, 33)
    IG.box(x - 0.15, x + 0.15, y - 0.15, y + 0.15, z - 0.15, z + 0.15, "F8E0FF" if k % 2 else YEL)

F.objects(False)
# корни аркой над дверями лифта
for s in (-1, 1):
    tube(IS, [(s * (DOOR[0] + 1.4), 0.0, ZB - 0.9), (s * (DOOR[0] + 1.2), 7.0, ZB - 1.1),
              (s * (DOOR[0] - 0.2), 11.4, ZB - 1.2), (0.0, 12.4, ZB - 1.2)], [1.6, 1.3, 1.1, 0.9], 1.0, (0, 0, -1), ROOT)
    IQ.prism_xz(K.octa(s * (DOOR[0] + 1.6), ZB - 1.2, 1.2, 0.9, 0.4), 0.0, 0.5, MOSS2)
IG.prism_xz(K.octa(0.0, ZB - 1.3, 0.45, 0.45, 0.18), 11.0, 11.9, YEL)
B.lift_leaves(IS, BARK, "C9A05A")
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, STEM)
SL.box(-FX - 1.9, FX + 1.9, -1, 1.6, -FZ - 1.9, FZ + 1.9, MOSS)
SL.box(-FX - 4.2, FX + 4.2, 13.4, 15.6, -FZ - 4.2, FZ + 4.2, CAP)
SL.box(-FX - 3.0, FX + 3.0, 15.6, 17.8, -FZ - 3.0, FZ + 3.0, CAP)
SL.box(-FX - 1.4, FX + 1.4, 17.8, 19.0, -FZ - 1.4, FZ + 1.4, CAP2)
SL.box(-FX - 3.6, FX + 3.6, 12.9, 13.4, -FZ - 3.6, FZ + 3.6, GILL)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    for a in WINDOWS[fi]:
        slab(SL, axis, fixed, out, 0.3, a - 1.6, a + 1.6, 6.4, 9.6, WIN)
    for j in range(3):
        a = -half + 6 + (2 * half - 12) * j / 2
        slab(SL, axis, fixed, out, 4.4, a - 0.8, a + 0.8, 14.6, 15.6, SPOT, back=-3.9)

F.build(exhibit=(STUMP[0], 1.84, STUMP[1], 3.4), lamps=[("Hall", (0, 14, 4), 4000, (0.8, 0.75, 1.0)),
                                                       ("Spot", (0, 13, -3), 2500, (1.0, 0.95, 1.0))])
