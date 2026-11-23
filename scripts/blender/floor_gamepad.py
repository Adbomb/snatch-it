"""Этаж «Золотой геймпад» музея-небоскрёба (вторая партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — дневной ретро-игровой зал в пастельных цветах. Снаружи — светлые стены с белыми рамами,
спереди — три огромных игровых автомата (светящаяся вывеска, экран с пиксельными картинками — монета, сердце,
звезда, наклонный пульт с джойстиком и кнопками, дверца для монет), над ними — неоновая лента из пикселей;
бока — пиксельные фрески: падающие фигуры-тетрамино и большое сердце; на верхних углах — гигантские джойстики;
сзади — розетка с толстыми кабелями.
Внутри — игровой зал: тёмно-синий ковёр с неоновыми искрами, вдоль стен — ряды автоматов, автомат с клешнёй
и шарами-призами, потолок — сетка неоновых трубок; геймпад на пьедестале-монете с сияющим кольцом, вокруг парят
пиксельные сердца и звёзды, у лифта — горка из фигур-тетрамино.
Запуск: blender --background --factory-startup --python scripts/blender/floor_gamepad.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab  # noqa: E402

WALL, WALL2, TRIM, LAV = "F4EEFA", "E2D8F2", "FFFFFF", "B8A4E8"
MINT, PINK, SKY, LEMON, PEACH = "7FE0C8", "FF8AC0", "7CC8FF", "FFE066", "FFB088"
PURP, PURP2, NAVY, NAVY2, SCREEN = "6A4AC8", "4A2E9A", "1E1E4A", "2A2A60", "141432"
GOLD, GOLD2, RED, GREEN, WHITE = "F2C230", "C9921A", "FF4A5A", "4AE070", "FFFFFF"

F = B.Floor("GG", "GoldenGamepad", quiet=(WALL2, NAVY, LAV), bevel_min=1.0, keep_arch=True)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL

SPRITES = {
    "heart": [".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."],
    "star": ["...X...", "..XXX..", "XXXXXXX", ".XXXXX.", ".XX.XX.", "X.....X"],
    "coin": [".XXXX.", "XXX.XX", "XXX.XX", "XXX.XX", "XXX.XX", ".XXXX."],
}


def pixels(p, axis, fixed, out, a0, y0, px, name, color, d0, d1):
    """Пиксельная картинка на стене: a0, y0 — левый верхний угол, px — размер пикселя."""
    rows = SPRITES[name]
    cells = [(c, r) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == "X"]
    lo, hi = sorted((fixed + out * d0, fixed + out * d1))
    for c0, c1, r0, r1 in B.rects(cells):
        a_lo, a_hi = a0 + c0 * px, a0 + c1 * px
        y_hi, y_lo = y0 - r0 * px, y0 - r1 * px
        if axis == "z":
            p.box(a_lo, a_hi, y_lo, y_hi, lo, hi, color)
        else:
            p.box(lo, hi, y_lo, y_hi, a_lo, a_hi, color)


def cabinet(S, G, x, z, d, w, body, accent, sprite, sprite_color, facing=-1):
    """Игровой автомат лицом к −Z (facing −1) или +Z: корпус, вывеска, экран, пульт, дверца."""
    F.objects(True)
    f = facing
    zb, zf = z, z + f * d
    lo, hi = sorted((zb, zf))
    S.box(x - w, x + w, 0.0, 9.6, lo, hi, body)
    S.box(x - w - 0.12, x + w + 0.12, 0.0, 9.6, *sorted((zf, zf + f * 0.1)), accent)
    G.box(x - w + 0.25, x + w - 0.25, 8.0, 9.4, *sorted((zf + f * 0.1, zf + f * 0.25)), accent)  # вывеска
    S.box(x - w + 0.2, x + w - 0.2, 4.6, 7.8, *sorted((zf + f * 0.1, zf + f * 0.2)), "2A2A40")
    G.box(x - w + 0.45, x + w - 0.45, 4.85, 7.55, *sorted((zf + f * 0.2, zf + f * 0.26)), SCREEN)
    px = min((2 * w - 1.4) / 7.0, 2.4 / 6.0)
    pixels(G, "z", zf + f * 0.26, f, x - 3.5 * px, 7.4, px, sprite, sprite_color, 0.0, 0.06)
    # пульт: наклонная полка, джойстик, кнопки
    S.prism_zy([(zf + f * 0.1, 3.4), (zf + f * 1.4, 3.6), (zf + f * 1.4, 4.0), (zf + f * 0.1, 4.6)], x - w, x + w, accent)
    S.box(x - w * 0.55 - 0.08, x - w * 0.55 + 0.08, 4.0, 4.8, *sorted((zf + f * 0.7, zf + f * 0.86)), "2A2A40")
    S.prism_xz(K.octa(x - w * 0.55, zf + f * 0.78, 0.28, 0.28, 0.11), 4.8, 5.2, RED)
    for k, c in enumerate((PINK, LEMON, SKY)):
        S.prism_xz(K.octa(x + w * 0.2 + 0.55 * k, zf + f * 0.8, 0.2, 0.2, 0.08), 4.0, 4.25, c)
    S.box(x - 0.8, x + 0.8, 1.0, 2.6, *sorted((zf + f * 0.1, zf + f * 0.18)), "2A2A40")  # дверца монет
    G.box(x - 0.12, x + 0.12, 1.9, 2.3, *sorted((zf + f * 0.18, zf + f * 0.22)), RED)
    F.objects(False)


# ══ ФАСАД: ретро-игровой зал ══════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, LAV, NAVY, NAVY)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FR, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, -1.0, 0.6, PURP2)  # цоколь
    for k in range(int((2 * half + 3.6) // 1.8)):  # «шашечки» неонового цоколя
        a = -half - 1.8 + 1.8 * k
        slab(FS, axis, fixed, out, 1.95, a + 0.1, a + 0.8, -0.6, 0.2, (MINT, PINK, LEMON, SKY)[k % 4])
    slab(FR, axis, fixed, out, 0.88, -half, half, 0.6, 15.0, WALL)
    slab(FS, axis, fixed, out, 1.2, -half - 1.2, half + 1.2, 15.0, 15.5, TRIM)
    # неоновая лента из пикселей
    slab(FR, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, 15.5, 19.0, PURP)
    for k in range(int((2 * half + 2) // 1.0)):
        a = -half - 1.0 + 1.0 * k
        h = 1 + int(rng(fi, k) * 3)
        for m in range(h):
            slab(FG, axis, fixed, out, 1.96, a + 0.08, a + 0.92, 16.0 + 0.85 * m, 16.75 + 0.85 * m,
                 (MINT, SKY, PINK, LEMON)[(k + m) % 4], back=-1.9)
    for e in (-1, 1):  # белые угловые рамы
        slab(FS, axis, fixed, out, 1.0, e * (half - 0.6), e * (half + 1.0), 0.6, 15.0, TRIM)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
# перед: три автомата
for k, (x, body, accent, sprite, sc) in enumerate(((-10.6, MINT, PINK, "coin", GOLD), (0.0, PINK, LEMON, "heart", RED),
                                                   (10.6, SKY, MINT, "star", LEMON))):
    FS.box(x - 4.6, x + 4.6, 0.6, 0.9, -FZ - 1.8, -FZ, TRIM)
    cabinet(FS, FG, x, -FZ, 0.9, 4.2, body, accent, sprite, sc, -1)
    FS.box(x - 4.4, x + 4.4, 9.6, 14.2, -FZ - 0.9, -FZ, body)
    slab(FS, "z", -FZ, -1, 1.0, x - 4.4, x + 4.4, 13.6, 14.2, accent)
    for m in range(4):  # огоньки над автоматом
        FG.prism_xy(K.octa(x - 2.7 + 1.8 * m, 11.9, 0.35, 0.35, 0.14), -FZ - 1.05, -FZ - 0.9,
                    (LEMON, PINK, SKY, MINT)[(m + k) % 4])
# бока: пиксельные фрески — тетрамино и сердце
TETRO = [((0, 0), (1, 0), (2, 0), (3, 0)), ((0, 0), (1, 0), (0, 1), (1, 1)), ((0, 0), (1, 0), (2, 0), (1, 1)),
         ((0, 0), (0, 1), (1, 1), (2, 1)), ((1, 0), (2, 0), (0, 1), (1, 1))]
for s in (-1, 1):
    fx = s * FX
    slab(FS, "x", fx, s, 0.95, -15.4, 15.4, 1.4, 14.2, NAVY)
    slab(FS, "x", fx, s, 1.0, -15.6, 15.6, 1.2, 1.4, TRIM)
    slab(FS, "x", fx, s, 1.0, -15.6, 15.6, 14.2, 14.4, TRIM)
    stack = [(0, 0, 0, MINT), (4, 0, 1, PINK), (6, 0, 2, LEMON), (9, 0, 3, SKY), (0, 2, 4, PEACH), (3, 1, 2, PURP),
             (7, 2, 0, MINT), (2, 3, 1, LEMON), (10, 2, 4, PINK)]
    cs = 1.15
    for cx0, cy0, t, color in stack:
        for cx, cy in TETRO[t]:
            z0 = -14.6 + (cx0 + cx) * cs
            y0 = 1.6 + (cy0 + cy) * cs
            if z0 + cs > 15.0:
                continue
            slab(FS, "x", fx, s, 1.2, z0 + 0.06, z0 + cs - 0.06, y0 + 0.06, y0 + cs - 0.06, color)
    pixels(FG, "x", fx, s, 3.0, 13.2, 1.3, "heart", RED, 1.0, 1.15)
    # гигантский джойстик на углу крыши
    for sz in (-1, 1):
        jx, jz = s * (FX + 0.8), sz * (FZ + 0.8)
        FS.box(jx - 1.4, jx + 1.4, 15.5, 16.4, jz - 1.4, jz + 1.4, "2A2A40")
        FS.box(jx - 0.2, jx + 0.2, 16.4, 17.8, jz - 0.2, jz + 0.2, "BFC4D0")
        FS.prism_xz(K.octa(jx, jz, 0.75, 0.75, 0.31), 17.8, 18.9, RED if sz < 0 else SKY)
# тыл: розетка и кабели
FS.box(-3.0, 3.0, 4.0, 9.0, FZ, FZ + 0.6, WALL2)
for s in (-1, 1):
    FS.box(s * 1.1 - 0.35, s * 1.1 + 0.35, 6.0, 7.6, FZ + 0.6, FZ + 0.7, "2A2A40")
    beam(FS, (s * 1.1, 6.8, FZ + 0.7), (s * 6.0, 2.0, FZ + 1.6), 0.5, 0.5, "2A2A40")
    beam(FS, (s * 6.0, 2.0, FZ + 1.6), (s * 12.0, 0.9, FZ + 1.6), 0.5, 0.5, "2A2A40")

# ══ ИНТЕРЬЕР: игровой зал ═════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.4
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), NAVY)
for k in range(46):  # неоновые искры на ковре
    x, z = (rng(k, 91) - 0.5) * 31, (rng(k, 92) - 0.5) * 29
    if abs(x) < 5.5 and -8.5 < z < 2.5:
        continue
    IG.box(x - 0.18, x + 0.18, 0.02, 0.05, z - 0.18, z + 0.18, (MINT, PINK, LEMON, SKY)[k % 4])
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.0, PURP2)
    slab(IQ, axis, fixed, out, 0.7, -half, half, 1.0, C, NAVY2)
    if gap:
        slab(IQ, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, NAVY2)
    for y in (11.2, 15.6):  # неоновые трубки по стенам
        slab(IG, axis, fixed, out, 0.95, -half, half, y, y + 0.2, PINK if y < 12 else SKY)
    for k in range(int(2 * half // 5.0)):  # пиксельные картинки на стенах
        a = -half + 2.5 + 5.0 * k
        if gap and abs(a) < DOOR[0] + 2:
            continue
        pixels(IG, axis, fixed, out, a - 1.4, 14.6, 0.4, ("heart", "star", "coin")[(k + idx) % 3],
               (RED, LEMON, GOLD)[(k + idx) % 3], 0.9, 1.0)
# ряды автоматов вдоль боковых стен и передней стены
for s in (-1, 1):
    for k, z in enumerate((-12.5, -7.5, -2.5, 2.5)):
        body, accent = ((MINT, PINK), (PINK, LEMON), (SKY, MINT), (PEACH, SKY))[(k + (s > 0)) % 4]
        # автомат лицом к центру (поворот через ось x): строим вдоль x
        x0 = s * W
        IS.box(min(x0, x0 - s * 2.4), max(x0, x0 - s * 2.4), 0.0, 8.6, z - 1.9, z + 1.9, body)
        IG.box(min(x0 - s * 2.4, x0 - s * 2.55), max(x0 - s * 2.4, x0 - s * 2.55), 7.2, 8.4, z - 1.6, z + 1.6, accent)
        IS.box(min(x0 - s * 2.4, x0 - s * 2.5), max(x0 - s * 2.4, x0 - s * 2.5), 4.0, 6.9, z - 1.6, z + 1.6, "2A2A40")
        IG.box(min(x0 - s * 2.5, x0 - s * 2.56), max(x0 - s * 2.5, x0 - s * 2.56), 4.2, 6.7, z - 1.4, z + 1.4,
               (SKY, PINK, MINT, LEMON)[k % 4])
        IS.prism_xy([(x0 - s * 2.4, 3.2), (x0 - s * 3.5, 3.4), (x0 - s * 3.5, 3.8), (x0 - s * 2.4, 4.0)], z - 1.9, z + 1.9, accent)
        IS.prism_xz(K.octa(x0 - s * 3.0, z - 0.6, 0.22, 0.22, 0.09), 3.8, 4.3, RED)
for x, body, accent, sprite, sc in ((-6.0, LEMON, PURP, "star", PINK), (6.0, MINT, PINK, "coin", GOLD)):
    cabinet(IS, IG, x, ZF, 2.2, 2.0, body, accent, sprite, sc, 1)
F.objects(True)
# автомат с клешнёй
cx, cz = 11.5, 8.5
IS.box(cx - 2.0, cx + 2.0, 0.0, 3.4, cz - 2.0, cz + 2.0, PINK)
IG.box(cx - 1.9, cx + 1.9, 3.4, 7.6, cz - 1.9, cz + 1.9, "D8F4FF")
IS.box(cx - 2.0, cx + 2.0, 7.6, 8.6, cz - 2.0, cz + 2.0, PINK)
IG.box(cx - 1.8, cx + 1.8, 8.6, 9.2, cz - 1.8, cz + 1.8, LEMON)
for k in range(9):
    bx, bz = cx - 1.3 + 0.9 * (k % 3) + (rng(k, 3) - 0.5) * 0.3, cz - 1.3 + 0.9 * (k // 3)
    IS.prism_xz(K.octa(bx, bz, 0.42, 0.42, 0.17), 3.4, 3.4 + 0.8, (MINT, SKY, LEMON, PEACH)[k % 4])
IS.box(cx - 0.05, cx + 0.05, 5.8, 7.6, cz - 0.05, cz + 0.05, "BFC4D0")
for e in (-1, 1):
    beam(IS, (cx, 5.8, cz), (cx + e * 0.45, 5.0, cz), 0.1, 0.1, "BFC4D0")
# пьедестал-монета с сияющим кольцом
px, pz = PED
IR.prism_xz(K.octa(px, pz, 4.4, 4.4, 1.8), 0.0, 0.7, GOLD2)
IR.prism_xz(K.octa(px, pz, 3.8, 3.8, 1.57), 0.7, TOP, GOLD)
IG.frame_xz(K.octa(px, pz, 4.9, 4.9, 2.0), K.octa(px, pz, 4.45, 4.45, 1.82), 0.0, 0.25, MINT)
IS.frame_xz(K.octa(px, pz, 3.2, 3.2, 1.3), K.octa(px, pz, 2.8, 2.8, 1.15), TOP, TOP + 0.05, GOLD2)
# парящие пиксельные сердца и звёзды вокруг
for k, (a, y, name, color) in enumerate(((-6.5, 11.0, "heart", RED), (5.0, 12.0, "star", LEMON),
                                         (-3.5, 14.0, "coin", GOLD), (7.0, 9.0, "heart", PINK))):
    pixels(IG, "z", pz - 1.0 - k * 0.3, -1, a, y, 0.32, name, color, 0.0, 0.25)
# горка тетрамино у лифта
blocks = [(-9.0, 0, 0, MINT), (-6.6, 0, 1, PINK), (-8.4, 1, 2, LEMON), (6.0, 0, 3, SKY), (8.4, 0, 0, PEACH),
          (7.0, 1, 4, PURP)]
for bx, by, t, color in blocks:
    for cx_, cy_ in TETRO[t]:
        x0 = bx + cx_ * 0.9
        y0 = by * 0.9 + cy_ * 0.9
        IS.box(x0 + 0.04, x0 + 0.86, y0, y0 + 0.86, 11.0, 11.86, color)
F.objects(False)
# потолок: сетка неоновых трубок
for k in range(-3, 4):
    IG.box(-W, W, C - 0.3, C - 0.18, 4.2 * k - 0.06, 4.2 * k + 0.06, (PINK, SKY, MINT)[k % 3])
for k in range(-3, 4):
    IS.box(4.6 * k - 0.06, 4.6 * k + 0.06, C - 0.32, C - 0.2, ZF, ZB, "BFC4D0")
B.lift_leaves(IS, PURP, LEMON)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, WALL)
SL.box(-FX - 1.9, FX + 1.9, -1.0, 0.6, -FZ - 1.9, FZ + 1.9, PURP2)
SL.box(-FX - 1.9, FX + 1.9, 15.5, 19.0, -FZ - 1.9, FZ + 1.9, PURP)
for x, body in ((-10.6, MINT), (0.0, PINK), (10.6, SKY)):
    SL.box(x - 4.4, x + 4.4, 0.6, 14.2, -FZ - 1.0, -FZ, body)
    SL.box(x - 3.6, x + 3.6, 4.8, 7.6, -FZ - 1.2, -FZ - 1.0, SCREEN)
for s in (-1, 1):
    SL.box(s * FX, s * (FX + 1.2), 1.4, 14.2, -15.4, 15.4, NAVY)
    for sz in (-1, 1):
        SL.box(s * (FX + 0.1), s * (FX + 1.5), 17.8, 18.9, sz * (FZ + 0.1), sz * (FZ + 1.5), RED)

F.build(exhibit=(PED[0], TOP, PED[1], 3.2), lamps=[("Hall", (0, 14, 6), 3000, (0.95, 0.9, 1.0)),
                                                   ("Spot", (0, 13, -3), 3200, (1.0, 0.97, 0.9))])
