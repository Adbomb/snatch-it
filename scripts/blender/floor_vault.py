"""Этаж «Карманный сейф» музея-небоскрёба (третья партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — банк в стиле ар-деко с огромным хранилищем. Снаружи — светлый известняк с каннелированными
пилястрами, бронзовые пояса и «ёлочки» ар-деко, ступенчатый парапет-зиккурат; в центре фасада — огромная круглая
дверь сейфа: стальная рама, кольцо болтов, дверь с кольцевыми ступенями, ступица со штурвалом из четырёх спиц и
петли справа; у подножия — штабеля золотых слитков за латунными стойками с бархатным канатом; слева — бронзовая
вращающаяся дверь под козырьком, справа — ящик ночного депозита; по углам — камеры наблюдения; бока — высокие окна
с бронзовыми решётками; сзади — инкассаторский фургон. Внутри — хранилище: пол в чёрно-белую клетку, стены из
стальных ячеек с ручками, выше — клёпаные листы, открытая круглая дверь у лифта, поддоны с пирамидами слитков,
мешки с монетами, красные лучи сигнализации вокруг золота, лампы-решётки; экспонат — на стальном постаменте с
золотым кантом и бархатным верхом.
Запуск: blender --background --factory-startup --python scripts/blender/floor_vault.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab  # noqa: E402

LIME, LIME2, LIME3, BRONZE, BRONZE2 = "E6DCC4", "D2C6AA", "F2EAD6", "B08040", "8A6230"
STEEL, STEEL2, STEEL3, DARKS, GOLD, GOLD2 = "A8B0BC", "8A929E", "C8CED8", "4A505A", "F2C230", "D9A21A"
MARBLE, MARBLE2, GREEN, RED, WARM, VELVET = "F0F0F0", "2A2A32", "2E6A4A", "FF2A3A", "FFE2A0", "8A1E2A"

F = B.Floor("PS", "PocketSafe", quiet=(LIME2, MARBLE, VELVET), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def bars(p, x, z, nx, nz, layers, along_x=True):
    """Пирамида золотых слитков: слои уменьшаются кверху."""
    for L in range(layers):
        for i in range(nx - L):
            for j in range(nz - L):
                bx = x + (i + L * 0.5) * 1.1 - (nx - 1) * 0.55
                bz = z + (j + L * 0.5) * 0.6 - (nz - 1) * 0.3
                p.loft([(bx - 0.5, 0.45 * L, bz - 0.26), (bx + 0.5, 0.45 * L, bz - 0.26), (bx + 0.5, 0.45 * L, bz + 0.26),
                        (bx - 0.5, 0.45 * L, bz + 0.26)],
                       [(bx - 0.4, 0.45 * L + 0.42, bz - 0.18), (bx + 0.4, 0.45 * L + 0.42, bz - 0.18),
                        (bx + 0.4, 0.45 * L + 0.42, bz + 0.18), (bx - 0.4, 0.45 * L + 0.42, bz + 0.18)],
                       GOLD if (i + j + L) % 2 else GOLD2)


def vault_door(prism, frame, box_, cx, cy, r, z_wall, out):
    """Круглая дверь сейфа на стене z = z_wall, выступает в сторону out (по z)."""
    def zz(d):
        return sorted((z_wall + out * d[0], z_wall + out * d[1]))
    frame(K.ngon(cx, cy, r + 1.1, 24), K.ngon(cx, cy, r, 24), *zz((-0.05, 1.6)), DARKS)
    prism(K.ngon(cx, cy, r, 24), *zz((-0.05, 1.2)), STEEL)
    frame(K.ngon(cx, cy, r * 0.8, 24), K.ngon(cx, cy, r * 0.7, 24), *zz((1.2, 1.5)), STEEL3)
    frame(K.ngon(cx, cy, r * 0.5, 16), K.ngon(cx, cy, r * 0.42, 16), *zz((1.2, 1.7)), STEEL2)
    for k in range(20):  # болты
        t = 2 * math.pi * k / 20
        x, y = cx + (r + 0.55) * math.cos(t), cy + (r + 0.55) * math.sin(t)
        prism(K.octa(x, y, 0.28, 0.28, 0.11), *zz((1.6, 1.85)), STEEL3)
    prism(K.ngon(cx, cy, 1.0, 12), *zz((1.2, 2.1)), GOLD2)
    for k in range(4):  # штурвал
        t = math.pi / 4 + math.pi / 2 * k
        c, s = math.cos(t), math.sin(t)
        w = 0.22
        L = r * 0.62
        prism([(cx - s * w, cy + c * w), (cx + c * L - s * w, cy + s * L + c * w), (cx + c * L + s * w, cy + s * L - c * w),
               (cx + s * w, cy - c * w)], *zz((1.9, 2.2)), STEEL3)
        prism(K.octa(cx + c * L, cy + s * L, 0.38, 0.38, 0.15), *zz((1.9, 2.5)), GOLD)
    for y in (cy - r * 0.55, cy + r * 0.55):  # петли справа
        box_(cx + r + 0.5, cx + r + 1.6, y - 0.8, y + 0.8, *zz((1.4, 2.2)), DARKS)


# ══ ФАСАД: банк ар-деко с дверью сейфа ════════════════════════════════════════════════════════════════════════
B.shell_planes(F, LIME2, LIME2, STEEL2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.2, LIME2)
    for k in range(3):  # ступени цоколя
        d = 2.88 - k
        slab(FR, axis, fixed, out, d - 0.1, -half - d + 0.1, half + d - 0.1, -0.2 + 0.6 * k, 0.4 + 0.6 * k, (LIME2, LIME, LIME3)[k])
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.6, 15.0, LIME)
    for k in range(int(2 * half // 4.0) + 1):  # каннелированные пилястры
        a = -half + 4.0 * k
        if fi == 0 and abs(a) < 9.6:
            continue
        slab(FR, axis, fixed, out, 1.88, max(a - 0.9, -half), min(a + 0.9, half), 1.6, 15.0, LIME3)
        for e in (-0.45, 0.0, 0.45):
            slab(FS, axis, fixed, out, 1.95, a + e - 0.08, a + e + 0.08, 2.4, 14.2, LIME2)
    slab(FS, axis, fixed, out, 2.0, -half - 0.4, half + 0.4, 15.0, 15.6, BRONZE)  # бронзовый пояс
    for k in range(int(2 * half // 1.2)):  # «ёлочка» ар-деко
        a = -half + 0.6 + 1.2 * k
        d0, d1 = sorted((fixed + out * 2.0, fixed + out * 2.1))
        (FS.prism_xy if axis == "z" else FS.prism_zy)([(a - 0.5, 15.1), (a, 15.5), (a + 0.5, 15.1), (a, 15.3)], d0, d1, GOLD2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 15.6, 17.0, LIME3)
    for k, (w, y0, y1) in enumerate(((half, 15.6, 17.0), (half * 0.62, 17.0, 18.0), (half * 0.3, 18.0, 18.9))):
        slab(FR, axis, fixed, out, 1.88 - 0.5 * k, -w, w, y0, y1, (LIME, LIME3, LIME)[k])  # зиккурат
    if axis == "x":  # бока: высокие окна с бронзовыми решётками
        for k in range(3):
            a = -half + 2.0 + 4.0 * (2 * k + 1) - 1.0 + 1.0
            a = -8.0 + 8.0 * k
            slab(FS, axis, fixed, out, 1.3, a - 1.5, a + 1.5, 3.6, 13.0, BRONZE2)
            slab(FG, axis, fixed, out, 1.35, a - 1.2, a + 1.2, 3.9, 12.7, WARM)
            for m in range(4):
                slab(FS, axis, fixed, out, 1.45, a - 1.2 + 0.8 * m - 0.06, a - 1.2 + 0.8 * m + 0.06, 3.9, 12.7, BRONZE)
            for y in (6.0, 9.0):
                slab(FS, axis, fixed, out, 1.45, a - 1.2, a + 1.2, y - 0.06, y + 0.06, BRONZE)
            d0, d1 = sorted((fixed + out * 1.3, fixed + out * 1.5))
            FS.prism_zy([(a - 1.5, 13.0), (a + 1.5, 13.0), (a, 14.4)], d0, d1, BRONZE)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
FR.box(-17.0, 9.0, -0.2, 1.6, -FZ - 6.0, -FZ, LIME3)  # терраса перед банком: на ней слитки, стойки, вращающаяся дверь
FS.box(-17.2, 9.2, -0.2, 0.4, -FZ - 6.3, -FZ - 5.9, LIME2)
# центр: огромная дверь сейфа
vault_door(FS.prism_xy, FS.frame_xy, FS.box, 0.0, 8.4, 5.8, -FZ, -1)
# у подножия: штабеля слитков за стойками с бархатным канатом
for x in (-5.2, 5.2):
    FS.box(x - 2.0, x + 2.0, 1.6, 1.9, -FZ - 4.2, -FZ - 2.6, BRONZE2)
    for k, (bx, bz) in enumerate(((x - 1.1, -FZ - 3.0), (x, -FZ - 3.0), (x + 1.1, -FZ - 3.0), (x - 0.55, -FZ - 3.0),
                                  (x + 0.55, -FZ - 3.0), (x, -FZ - 3.0))):
        L = 0 if k < 3 else (1 if k < 5 else 2)
        y = 1.9 + 0.45 * L
        FS.loft([(bx - 0.5, y, bz - 0.4), (bx + 0.5, y, bz - 0.4), (bx + 0.5, y, bz + 0.4), (bx - 0.5, y, bz + 0.4)],
                [(bx - 0.4, y + 0.42, bz - 0.3), (bx + 0.4, y + 0.42, bz - 0.3), (bx + 0.4, y + 0.42, bz + 0.3),
                 (bx - 0.4, y + 0.42, bz + 0.3)], GOLD if k % 2 else GOLD2)
for x in (-8.0, -2.4, 2.4, 8.0):
    FS.prism_xz(K.octa(x, -FZ - 5.0, 0.18, 0.18, 0.07), 1.6, 3.6, BRONZE)
    FS.prism_xz(K.octa(x, -FZ - 5.0, 0.3, 0.3, 0.12), 3.6, 3.9, GOLD)
for a, b in ((-8.0, -2.4), (2.4, 8.0)):
    pts = [(a + (b - a) * t, 3.3 - 0.5 * 4 * t * (1 - t), -FZ - 5.0) for t in (0.0, 0.5, 1.0)]
    for q0, q1 in zip(pts, pts[1:]):
        beam(FS, q0, q1, 0.18, 0.18, VELVET)
# слева: бронзовая вращающаяся дверь под козырьком; справа: ящик ночного депозита
FS.box(-16.0, -11.0, 1.6, 7.6, -FZ - 1.4, -FZ, BRONZE2)
FS.prism_xz(K.ngon(-13.5, -FZ - 1.6, 2.0, 12), 1.6, 7.0, "3A3020")
for k in range(4):
    t = math.pi / 4 + math.pi / 2 * k
    FS.box(-13.5 + 1.9 * math.cos(t) - 0.08, -13.5 + 1.9 * math.cos(t) + 0.08, 1.6, 7.0, -FZ - 1.6 + 1.9 * math.sin(t) - 0.08,
           -FZ - 1.6 + 1.9 * math.sin(t) + 0.08, GOLD)
FG.prism_xz(K.ngon(-13.5, -FZ - 1.6, 1.9, 12), 2.0, 6.6, "C8B890")
FS.box(-16.6, -10.4, 7.6, 8.2, -FZ - 4.0, -FZ, BRONZE)
for k in range(5):
    FG.box(-15.6 + 1.2 * k, -15.0 + 1.2 * k, 7.55, 7.6, -FZ - 3.6, -FZ - 2.8, WARM)
FS.box(11.0, 16.0, 1.6, 6.6, -FZ - 1.2, -FZ, STEEL2)
FS.box(11.6, 15.4, 4.0, 4.6, -FZ - 1.4, -FZ - 1.2, DARKS)
FS.box(12.6, 14.4, 2.4, 3.2, -FZ - 1.4, -FZ - 1.2, BRONZE)
FG.box(13.2, 13.8, 5.4, 5.9, -FZ - 1.3, -FZ - 1.2, "6AE06A")
# камеры наблюдения по углам
for sx in (-1, 1):
    for sz in (-1, 1):
        x, z = sx * (FX + 0.3), sz * (FZ + 0.3)
        beam(FS, (x, 14.0, z), (x + sx * 1.2, 13.4, z + sz * 1.2), 0.25, 0.25, DARKS)
        FS.box(x + sx * 0.9 - 0.4, x + sx * 0.9 + 0.4, 12.6, 13.4, z + sz * 1.6 - 0.6, z + sz * 1.6 + 0.6, STEEL3)
        FG.box(x + sx * 0.9 - 0.15, x + sx * 0.9 + 0.15, 12.8, 13.1, z + sz * 2.2 - 0.05, z + sz * 2.2 + 0.05, RED)
# тыл: инкассаторский фургон
FS.box(-7.0, 5.0, 0.8, 6.6, FZ + 1.0, FZ + 5.0, GREEN)
FS.box(5.0, 8.6, 0.8, 4.6, FZ + 1.2, FZ + 4.8, GREEN)
FG.box(5.6, 8.4, 2.8, 4.2, FZ + 1.15, FZ + 1.2, "9CC8E0")
FS.box(-6.6, 4.6, 6.6, 6.8, FZ + 1.4, FZ + 4.6, STEEL2)
for x in (-4.8, 2.6, 6.8):
    FS.frame_xy(K.ngon(x, 0.8, 1.0, 12), K.ngon(x, 0.8, 0.5, 12), FZ + 5.0, FZ + 5.4, "26262E")
    FS.prism_xy(K.ngon(x, 0.8, 0.5, 12), FZ + 5.0, FZ + 5.3, STEEL3)

# ══ ИНТЕРЬЕР: хранилище ═══════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.4
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), MARBLE)
for i in range(-8, 8):  # чёрно-белая клетка
    for j in range(-8, 8):
        if (i + j) % 2:
            x0, z0 = 2.11 * i, 1.985 * j
            IS.box(x0 + 0.02, x0 + 2.09, 0.02, 0.05, z0 + 0.02, z0 + 1.965, MARBLE2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    slab(IQ, axis, fixed, out, 0.7, -half, half, 0.0, C, DARKS)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.0, DARKS)
        if not gap:  # стальные ячейки
            n = int((a1 - a0) // 2.8)
            for k in range(n):
                b0 = a0 + (a1 - a0) * k / n
                b1 = a0 + (a1 - a0) * (k + 1) / n
                for r in range(4):
                    y0 = 1.0 + 2.3 * r
                    slab(IR, axis, fixed, out, 0.88, b0 + 0.08, b1 - 0.08, y0 + 0.08, y0 + 2.22, STEEL if (k + r) % 2 else STEEL3)
                    m = (b0 + b1) / 2
                    slab(IS, axis, fixed, out, 1.05, m - 0.22, m + 0.22, y0 + 1.0, y0 + 1.3, GOLD2)
        else:
            slab(IR, axis, fixed, out, 0.88, a0, a1, 1.0, 10.2, STEEL2)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 10.2, STEEL2)
    slab(IS, axis, fixed, out, 1.0, -half, half, 10.2, 10.6, GOLD2)
    slab(IR, axis, fixed, out, 0.88, -half, half, 10.6, C, STEEL2)
    for k in range(int(2 * half // 2.0)):  # заклёпки
        a = -half + 1.0 + 2.0 * k
        for y in (11.4, 16.8):
            slab(IS, axis, fixed, out, 0.98, a - 0.12, a + 0.12, y - 0.12, y + 0.12, STEEL3)
for k in range(-2, 3):  # лампы-решётки на потолке
    for x in (-8.0, 0.0, 8.0):
        IG.box(x - 1.6, x + 1.6, C - 0.1, C - 0.04, 5.0 * k - 0.4, 5.0 * k + 0.4, "F4F8FF")
# открытая круглая дверь у лифта (повёрнута вдоль стены)
odx, odz = 9.0, 11.6
IS.prism_zy(K.ngon(odz, 4.4, 3.8, 20), odx - 0.8, odx + 0.8, STEEL)
IS.frame_zy(K.ngon(odz, 4.4, 3.0, 20), K.ngon(odz, 4.4, 2.6, 20), odx - 1.0, odx - 0.8, STEEL3)
IS.prism_zy(K.ngon(odz, 4.4, 0.8, 12), odx - 1.4, odx - 0.8, GOLD2)
for k in range(4):
    t = math.pi / 4 + math.pi / 2 * k
    IS.prism_zy([(odz - 0.15, 4.4), (odz + 2.2 * math.cos(t) - 0.15, 4.4 + 2.2 * math.sin(t)),
                 (odz + 2.2 * math.cos(t) + 0.15, 4.4 + 2.2 * math.sin(t)), (odz + 0.15, 4.4)], odx - 1.3, odx - 1.0, STEEL3)
for k in range(10):
    t = 2 * math.pi * k / 10 + 0.3
    IS.box(odx + 0.8, odx + 1.6, 4.4 + 3.4 * math.sin(t) - 0.25, 4.4 + 3.4 * math.sin(t) + 0.25,
           odz + 3.4 * math.cos(t) - 0.25, odz + 3.4 * math.cos(t) + 0.25, STEEL3)
# поддоны с пирамидами слитков, мешки, лучи сигнализации
for x, z in ((-11.5, -10.5), (11.5, -10.5), (-12.0, 1.0)):
    IS.box(x - 2.6, x + 2.6, 0.0, 0.4, z - 1.8, z + 1.8, "A87A40")
    bars(IS, x, z, 4, 4, 3)
    for k in range(4):
        y = 0.6 + 0.7 * k
        IG.box(x - 3.2, x + 3.2, y, y + 0.05, z + 2.4, z + 2.45, RED)
    for e in (-1, 1):
        IS.box(x + e * 3.3 - 0.15, x + e * 3.3 + 0.15, 0.0, 3.4, z + 2.3, z + 2.6, DARKS)
for k, (x, z) in enumerate(((12.0, 1.0), (13.4, 3.0), (11.0, 3.4), (-12.6, 6.6))):  # мешки с монетами
    IS.prism_xz(K.octa(x, z, 0.9, 0.9, 0.36), 0.0, 1.4, "7A8A5A")
    IS.prism_xz(K.octa(x, z, 0.5, 0.5, 0.2), 1.4, 1.8, "6A7A4A")
    IS.prism_xz(K.octa(x, z, 0.55, 0.55, 0.22), 1.55, 1.7, GOLD2)
    for m in range(3):
        IS.prism_xz(K.octa(x + 0.9 + 0.3 * m, z + 0.4, 0.25, 0.25, 0.1), 0.0, 0.08 + 0.08 * m, GOLD)
# стальной постамент с золотым кантом и бархатным верхом
px, pz = PED
IR.box(px - 4.0, px + 4.0, 0.0, 0.6, pz - 3.6, pz + 3.6, STEEL2)
IR.box(px - 3.3, px + 3.3, 0.6, TOP, pz - 2.9, pz + 2.9, STEEL)
IS.frame_xz(K.rect(px - 4.08, px + 4.08, pz - 3.68, pz + 3.68), K.rect(px - 3.9, px + 3.9, pz - 3.5, pz + 3.5), 0.45, 0.62, GOLD)
IQ.box(px - 3.0, px + 3.0, TOP - 0.1, TOP + 0.02, pz - 2.6, pz + 2.6, VELVET)
for sx in (-1, 1):
    for sz in (-1, 1):
        IS.prism_xz(K.octa(px + sx * 3.3, pz + sz * 2.9, 0.3, 0.3, 0.12), TOP, TOP + 0.4, GOLD)
B.lift_leaves(IS, STEEL2, GOLD)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, LIME)
SL.box(-FX - 2.9, FX + 2.9, -1.0, 1.6, -FZ - 2.9, FZ + 2.9, LIME2)
SL.box(-FX - 1.9, FX + 1.9, 15.0, 17.0, -FZ - 1.9, FZ + 1.9, LIME3)
SL.box(-FX * 0.62, FX * 0.62, 17.0, 18.0, -FZ - 1.4, FZ + 1.4, LIME)
SL.prism_xy(K.ngon(0.0, 8.4, 6.9, 12), -FZ - 1.6, -FZ, DARKS)
SL.prism_xy(K.ngon(0.0, 8.4, 5.8, 12), -FZ - 2.2, -FZ - 1.6, STEEL)

F.build(exhibit=(PED[0], TOP, PED[1], 3.2), lamps=[("Hall", (0, 14, 6), 3000, (0.95, 0.97, 1.0)),
                                                   ("Spot", (0, 13, -3), 3200, (1.0, 0.98, 0.94))])
