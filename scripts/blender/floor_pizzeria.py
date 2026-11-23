"""Этаж «Пицца-крыса» музея-небоскрёба (шестая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — итальянская пиццерия. Снаружи — тёплая штукатурка с кирпичным цоколем и рустом по углам, наверху
ритм из четырёх окон с зелёными ставнями и цветочными ящиками, внизу — дверь сбоку и длинная витрина с пиццами,
над ними полосатая маркиза; на карнизе — огромный наклонный кусок пиццы с пепперони; сбоку — кирпичная труба печи
с дымом и поленница; перед входом — столики под зонтом, мотороллер, ящики томатов, оливы в кадках, грифельная доска.
Внутри — зал пиццерии: пол в шашку, зелёная плитка понизу, кирпич и балки, у дальней стены — куполообразная печь
с огнём, слева — прилавок с витриной пицц, справа — полки с маслом и банками, связки чеснока и перца, столики
в клетчатых скатертях, лампы над ними; экспонат — на круглом кирпичном очаге с тёмной разделочной доской.
Запуск: blender --background --factory-startup --python scripts/blender/floor_pizzeria.py -- <репо> <превью>
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

PLAST, PLAST2, BRICK, BRICK2, STONE, TERRA = "F2DCB4", "E6C89A", "B85A3A", "9A4630", "D8C8A8", "C8825A"
GREEN, GREEN2, WHITE, RED, RED2, DARK = "3A8A4A", "2A6A38", "F6F0E2", "D83A2E", "A82A22", "2E2622"
WOOD, WOOD2, CHEESE, CRUST, OLIVE, TILE = "8A5A34", "6A4226", "F6C83A", "E0A050", "6A8A3A", "4A9A7A"

F = B.Floor("PZ", "PizzaRat", quiet=(TERRA, WOOD2, "E8E0D0"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def pizza(p, x, y, z, r, seed=0, along="y", t=0.12):
    """Круглая пицца: корж, сыр, кружки пепперони и оливки (плоско, лицом вверх или к стене)."""
    if along == "y":
        p.prism_xz(K.ngon(x, z, r, 12), y, y + t, CRUST)
        p.prism_xz(K.ngon(x, z, r * 0.84, 12), y + t, y + t + 0.04, CHEESE)
        for k in range(5):
            a = 2 * math.pi * (k + rng(seed, k) * 0.4) / 5
            p.prism_xz(K.ngon(x + r * 0.5 * math.cos(a), z + r * 0.5 * math.sin(a), r * 0.17, 8), y + t + 0.04, y + t + 0.08, RED)
    else:
        p.prism_xy(K.ngon(x, y, r, 12), z - t, z, CRUST)
        p.prism_xy(K.ngon(x, y, r * 0.84, 12), z - t - 0.04, z - t, CHEESE)
        for k in range(5):
            a = 2 * math.pi * (k + rng(seed, k) * 0.4) / 5
            p.prism_xy(K.ngon(x + r * 0.5 * math.cos(a), y + r * 0.5 * math.sin(a), r * 0.17, 8), z - t - 0.08, z - t - 0.04, RED)


def shutter_window(p, g, axis, fixed, out, a, y0, w, h):
    """Окно со ставнями, наличником и цветочным ящиком (стена axis = fixed, лицом out)."""
    d = lambda v: fixed + out * v  # noqa: E731
    if axis == "z":
        g.box(a - w / 2, a + w / 2, y0, y0 + h, *sorted((d(0.9), d(0.94))), "FFE0A0")
        p.frame_xy(K.rect(a - w / 2 - 0.3, a + w / 2 + 0.3, y0 - 0.3, y0 + h + 0.3), K.rect(a - w / 2, a + w / 2, y0, y0 + h),
                   *sorted((d(0.88), d(1.2))), WHITE)
        p.box(a - 0.06, a + 0.06, y0, y0 + h, *sorted((d(0.9), d(1.05))), WHITE)
        for e in (-1, 1):
            x0 = a + e * (w / 2 + 0.3)
            p.box(*sorted((x0, x0 + e * w * 0.55)), y0, y0 + h, *sorted((d(1.0), d(1.15))), GREEN)
            for k in range(4):
                yy = y0 + 0.4 + k * h / 4.2
                p.box(*sorted((x0 + e * 0.1, x0 + e * w * 0.5)), yy, yy + 0.12, *sorted((d(1.15), d(1.2))), GREEN2)
        p.box(a - w / 2 - 0.4, a + w / 2 + 0.4, y0 - 0.9, y0 - 0.2, *sorted((d(0.88), d(1.8))), WOOD)
        for k in range(4):
            xx = a - w / 2 + 0.2 + k * w / 3.3
            D.flower(p, xx, d(1.35), y0 - 0.2, 0.5, petal=("FF5A7A", "FFD03A", "FF8AC0", "FFFFFF")[k % 4])
    else:
        g.box(*sorted((d(0.9), d(0.94))), y0, y0 + h, a - w / 2, a + w / 2, "FFE0A0")
        p.frame_zy(K.rect(a - w / 2 - 0.3, a + w / 2 + 0.3, y0 - 0.3, y0 + h + 0.3), K.rect(a - w / 2, a + w / 2, y0, y0 + h),
                   *sorted((d(0.88), d(1.2))), WHITE)
        for e in (-1, 1):
            z0 = a + e * (w / 2 + 0.3)
            p.box(*sorted((d(1.0), d(1.15))), y0, y0 + h, *sorted((z0, z0 + e * w * 0.55)), GREEN)
        p.box(*sorted((d(0.88), d(1.8))), y0 - 0.9, y0 - 0.2, a - w / 2 - 0.4, a + w / 2 + 0.4, WOOD)
        for k in range(3):
            D.flower(p, d(1.35), a - w / 2 + 0.3 + k * w / 2.4, y0 - 0.2, 0.5, petal=("FF5A7A", "FFD03A", "FF8AC0")[k % 3])


def olive_tree(p, x, z, s=1.0):
    """Олива в терракотовой кадке: кадка, кривой ствол, три кроны."""
    p.prism_xz(K.ngon(x, z, 0.9 * s, 8), 0.0, 1.3 * s, TERRA)
    p.prism_xz(K.ngon(x, z, 1.0 * s, 8), 1.1 * s, 1.35 * s, "B06A44")
    beam(p, (x, 1.3 * s, z), (x + 0.3 * s, 3.2 * s, z), 0.3 * s, 0.3 * s, WOOD2)
    D.bush(p, x + 0.3 * s, z, 3.0 * s, 1.1 * s, OLIVE, "557A30")


def chair(p, x, z, face, col=WOOD):
    """Венский стул: сиденье, ножки, спинка (face — куда смотрит сидящий, ±1 по x)."""
    p.box(x - 0.5, x + 0.5, 1.0, 1.15, z - 0.5, z + 0.5, col)
    for e in (-1, 1):
        for f in (-1, 1):
            p.box(x + e * 0.4 - 0.05, x + e * 0.4 + 0.05, 0.0, 1.0, z + f * 0.4 - 0.05, z + f * 0.4 + 0.05, col)
    xb = x - face * 0.45
    p.box(xb - 0.06, xb + 0.06, 1.15, 2.4, z - 0.45, z + 0.45, col)


def table(p, x, z, cloth=True):
    """Столик в клетчатой скатерти: столешница, скатерть в шашку, ножка, свеча-лампа."""
    p.prism_xz(K.ngon(x, z, 0.12, 6), 0.0, 1.6, DARK)
    p.box(x - 1.1, x + 1.1, 1.6, 1.72, z - 1.1, z + 1.1, WHITE)
    if cloth:
        for i in range(4):
            for j in range(4):
                if (i + j) % 2 == 0:
                    p.box(x - 1.1 + 0.55 * i, x - 0.55 + 0.55 * i, 1.72, 1.74, z - 1.1 + 0.55 * j, z - 0.55 + 0.55 * j, RED)
        p.box(x - 1.15, x + 1.15, 1.1, 1.72, z - 1.15, z - 1.1, RED)
        p.box(x - 1.15, x + 1.15, 1.1, 1.72, z + 1.1, z + 1.15, RED)


# ══ ФАСАД: пиццерия ══════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, PLAST, PLAST, WOOD2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, TERRA)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.0, STONE)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.0, 15.0, PLAST)
    slab(FR, axis, fixed, out, 0.94, -half, half, 1.0, 3.4, BRICK)
    if fi == 0:  # кирпичный цоколь рядами со сдвигом — на главном фасаде
        for r in range(4):
            y = 1.0 + 0.6 * r
            off = 0.9 if r % 2 else 0.0
            for k in range(int(2 * half // 1.8)):
                a = -half + off + 1.8 * k
                if a + 1.75 > half or k % 2:
                    continue
                slab(FS, axis, fixed, out, 0.98, a + 0.04, a + 1.76, y + 0.04, y + 0.56, BRICK2)
    for s in (-1, 1):  # руст по углам
        for r in range(6):
            y = 3.6 + 1.85 * r
            w = 1.8 if r % 2 else 1.2
            a = s * half
            slab(FR, axis, fixed, out, 1.1, *sorted((a, a - s * w)), y + 0.05, y + 1.75, STONE)
    slab(FR, axis, fixed, out, 1.88, -half - 0.5, half + 0.5, 15.0, 15.8, STONE)
    slab(FR, axis, fixed, out, 0.88, -half, half, 15.8, 18.9, PLAST2)
    slab(FR, axis, fixed, out, 1.3, -half - 0.2, half + 0.2, 18.4, 18.9, STONE)
    slab(FR, axis, fixed, out, 1.3, -half - 0.2, half + 0.2, 9.2, 9.6, STONE)
    if axis == "x":  # бока: окна со ставнями, виноград
        for z in (-9.0, 0.0, 9.0):
            shutter_window(FS, FG, axis, fixed, out, z, 11.0, 2.4, 3.2)
        for z in (-11.5, 5.0):
            shutter_window(FS, FG, axis, fixed, out, z, 4.2, 2.4, 3.2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
for k in range(13):  # кронштейны под карнизом
    x = -16.2 + 2.7 * k
    FS.prism_zy([(-FZ - 0.88, 14.2), (-FZ - 0.88, 15.0), (-FZ - 1.8, 15.0), (-FZ - 1.4, 14.6)], x - 0.25, x + 0.25, STONE)
# верх фасада: ритм из четырёх окон со ставнями
for x in (-13.0, -4.4, 4.4, 13.0):
    shutter_window(FS, FG, "z", -FZ, -1, x, 11.0, 2.6, 3.4)
# низ: дверь сбоку, длинная витрина с пиццами
FS.box(-12.6, -7.4, 1.0, 8.4, -FZ - 1.0, -FZ - 0.88, DARK)
FG.box(-12.2, -7.8, 1.4, 7.8, -FZ - 1.06, -FZ - 1.0, "FFD890")
FS.frame_xy(K.rect(-13.0, -7.0, 1.0, 8.8), K.rect(-12.2, -7.8, 1.4, 7.8), -FZ - 1.4, -FZ - 0.88, WOOD2)
FS.box(-10.06, -9.94, 1.4, 7.8, -FZ - 1.2, -FZ - 1.0, WOOD2)
FG.box(-4.6, 14.6, 2.6, 8.0, -FZ - 0.94, -FZ - 0.9, "FFE6B0")
FS.frame_xy(K.rect(-5.0, 15.0, 2.2, 8.4), K.rect(-4.6, 14.6, 2.6, 8.0), -FZ - 1.3, -FZ - 0.88, WOOD2)
for x in (1.8, 8.2):
    FS.box(x - 0.1, x + 0.1, 2.6, 8.0, -FZ - 1.2, -FZ - 0.9, WOOD2)
FS.box(-5.2, 15.2, 1.6, 2.2, -FZ - 2.0, -FZ - 0.88, WOOD)  # подоконник-прилавок с пиццами
for k, x in enumerate((-2.6, 0.6, 5.0, 10.4, 13.0)):
    pizza(FS, x, 2.2, -FZ - 1.45, 1.0 if k % 2 else 0.85, seed=k)
# полосатая маркиза над дверью и витриной
for k in range(14):
    x0 = -13.6 + 2.07 * k
    col = (GREEN, WHITE, RED)[k % 3]
    FS.loft([(x0, 9.4, -FZ - 0.9), (x0 + 2.07, 9.4, -FZ - 0.9), (x0 + 2.07, 9.5, -FZ - 0.9), (x0, 9.5, -FZ - 0.9)],
            [(x0, 8.1, -FZ - 3.6), (x0 + 2.07, 8.1, -FZ - 3.6), (x0 + 2.07, 8.2, -FZ - 3.6), (x0, 8.2, -FZ - 3.6)], col)
    FS.prism_xy([(x0, 8.15), (x0 + 2.07, 8.15), (x0 + 1.03, 7.5)], -FZ - 3.65, -FZ - 3.55, col)
for x in (-13.4, 15.2):
    beam(FS, (x, 9.3, -FZ - 0.9), (x, 8.2, -FZ - 3.5), 0.1, 0.1, DARK)
# огромный кусок пиццы на карнизе, наклонён
cx, cy = 0.0, 16.1
ang = math.radians(-12)


def rot(u, v):
    return (cx + u * math.cos(ang) - v * math.sin(ang), cy + u * math.sin(ang) + v * math.cos(ang))


FS.prism_xy([rot(-4.0, 1.4), rot(4.0, 1.4), rot(0.0, -2.2)], -FZ - 1.5, -FZ - 1.0, CHEESE)
FS.prism_xy([rot(-4.3, 1.2), rot(4.3, 1.2), rot(4.3, 1.9), rot(-4.3, 1.9)], -FZ - 1.7, -FZ - 0.9, CRUST)
for u, v in ((-1.8, 0.5), (1.6, 0.6), (0.0, -0.8), (-0.6, 1.0)):
    FS.prism_xy([rot(u + 0.55 * math.cos(t), v + 0.55 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]],
                -FZ - 1.6, -FZ - 1.5, RED)
for u in (-2.6, 2.4):  # капли сыра
    FS.prism_xy([rot(u - 0.3, 0.2), rot(u + 0.3, 0.2), rot(u + 0.15, -0.9), rot(u - 0.15, -0.9)], -FZ - 1.56, -FZ - 1.44, CHEESE)
FS.box(-0.3, 0.3, 15.8, 16.4, -FZ - 1.3, -FZ - 0.88, DARK)
# мотороллер у входа
vx, vz = 13.8, -FZ - 5.2
for e in (-1, 1):
    FS.prism_zy(K.ngon(vz + e * 1.5, 0.55, 0.55, 10), vx - 0.18, vx + 0.18, DARK)
FS.prism_zy([(vz - 1.9, 0.9), (vz + 1.2, 0.9), (vz + 1.9, 1.5), (vz + 1.7, 2.3), (vz + 0.2, 2.4), (vz - 0.6, 1.4), (vz - 1.6, 1.4)],
            vx - 0.55, vx + 0.55, "6AC8C0")
FS.box(vx - 0.4, vx + 0.4, 2.4, 2.65, vz + 0.1, vz + 1.6, DARK)
beam(FS, (vx, 1.4, vz - 1.4), (vx, 3.4, vz - 1.7), 0.18, 0.18, "6AC8C0")
FS.box(vx - 0.9, vx + 0.9, 3.3, 3.45, vz - 1.8, vz - 1.65, DARK)
FS.box(vx - 0.5, vx + 0.5, 1.6, 2.4, vz - 2.0, vz - 1.4, "6AC8C0")
# терраса: столики, зонт, оливы, ящики томатов, грифельная доска
for x, z in ((-6.0, -FZ - 5.6), (2.0, -FZ - 5.4)):
    table(FS, x, z, cloth=True)
    chair(FS, x - 1.8, z, 1)
    chair(FS, x + 1.8, z, -1, "3A8A4A")
FS.prism_xz(K.ngon(-2.0, -FZ - 5.5, 0.1, 6), 0.0, 6.0, DARK)
for k in range(8):
    t0, t1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
    FS.cone([(-2.0 + 3.6 * math.cos(t0), 5.2, -FZ - 5.5 + 3.6 * math.sin(t0)), (-2.0 + 3.6 * math.cos(t1), 5.2, -FZ - 5.5 + 3.6 * math.sin(t1)),
             (-2.0, 5.2, -FZ - 5.5)], (-2.0, 6.4, -FZ - 5.5), (RED, WHITE)[k % 2])
for x in (-16.4, 8.2):
    olive_tree(FS, x, -FZ - 4.2, 1.0)
for k, (x, z) in enumerate(((-15.6, -FZ - 7.0), (-14.2, -FZ - 7.0), (-14.9, -FZ - 7.0))):
    y = 0.0 if k < 2 else 1.0
    D.crate(FS, x if k < 2 else -14.9, z, y, 1.0, "B08048", "8A6234")
    for i in range(3):
        FS.prism_xz(K.ngon(x - 0.25 + 0.25 * i, z, 0.2, 6), y + 1.0, y + 1.3, RED)
FS.box(-9.4, -8.0, 0.0, 3.4, -FZ - 3.4, -FZ - 3.2, WOOD2)  # грифельная доска
FS.box(-9.3, -8.1, 1.2, 3.2, -FZ - 3.46, -FZ - 3.4, "2E3A34")
for k, col in enumerate(("F6F0E2", "FFD03A", "FF8A8A")):
    FS.box(-9.1, -8.4 + 0.1 * k, 2.7 - 0.5 * k, 2.82 - 0.5 * k, -FZ - 3.5, -FZ - 3.46, col)
# правый бок: кирпичная труба печи с дымом, поленница
tz = 6.0
FS.box(FX + 0.9, FX + 3.1, -1.0, 18.6, tz - 1.1, tz + 1.1, BRICK)
for r in range(14):
    y = 0.5 + 1.3 * r
    FS.box(FX + 0.85, FX + 3.15, y, y + 0.2, tz - 1.15, tz + 1.15, BRICK2)
FS.box(FX + 0.7, FX + 3.3, 18.6, 18.95, tz - 1.3, tz + 1.3, DARK)
FS.box(FX + 0.9, FX + 3.4, 0.0, 3.6, -14.0, -6.0, WOOD2)  # навес поленницы
FS.loft([(FX + 0.8, 3.6, -14.3), (FX + 3.7, 3.2, -14.3), (FX + 3.7, 3.4, -14.3), (FX + 0.8, 3.8, -14.3)],
        [(FX + 0.8, 3.6, -5.7), (FX + 3.7, 3.2, -5.7), (FX + 3.7, 3.4, -5.7), (FX + 0.8, 3.8, -5.7)], RED2)
for r in range(3):
    for k in range(6):
        z = -13.4 + 1.3 * k + 0.6 * (r % 2)
        if z > -6.4:
            continue
        FS.prism_zy(K.ngon(z, 0.5 + 0.95 * r, 0.45, 7), FX + 3.4, FX + 3.6, "C89A64")
# тыл: бочонки масла, корзина томатов
for k, x in enumerate((-10.0, -8.2)):
    D.barrel(FS, x, FZ + 2.0, 0.0, 0.75, 1.6, WOOD, DARK)

# ══ ИНТЕРЬЕР: зал пиццерии ═══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.1
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), "E8E0D0")
for i in range(-7, 7):  # шашечный пол
    for j in range(-7, 7):
        if (i + j) % 2 == 0:
            IQ.box(2.4 * i + 0.02, 2.4 * i + 2.38, 0.02, 0.04, 2.27 * j + 0.02, 2.27 * j + 2.25, "3A3A3E")
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, PLAST)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 3.4, TILE)
        slab(IR, axis, fixed, out, 1.15, a0, a1, 3.4, 3.7, WHITE)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, PLAST)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, GREEN)
    if idx < 2:  # кирпичные пятна под облупившейся штукатуркой
        for k, (a, y) in enumerate(((-11.0, 9.0), (2.0, 12.0), (10.0, 7.0))):
            for r in range(4):
                for c in range(3):
                    aa = a + 1.2 * c + 0.6 * (r % 2) - 1.8
                    slab(IS, axis, fixed, out, 0.95, aa + 0.04, aa + 1.16, y + 0.6 * r + 0.04, y + 0.6 * r + 0.56, (BRICK, BRICK2)[(r + c) % 2])
    slab(IR, axis, fixed, out, 1.6, -half, half, 14.6, 15.2, WOOD2)
for k in range(-3, 4):  # потолочные балки
    IS.box(-W, W, C - 0.9, C - 0.2, 4.4 * k - 0.35, 4.4 * k + 0.35, WOOD2)
# купольная печь у дальней стены, устье — к залу
ox, oz = 0.0, ZF + 4.4
IR.box(-4.8, 4.8, 0.0, 3.2, ZF + 0.88, ZF + 8.2, BRICK)
for r in range(7):
    y0, y1 = 3.2 + 3.6 * math.sin(math.pi / 2 * r / 7), 3.2 + 3.6 * math.sin(math.pi / 2 * (r + 1) / 7)
    rr = 3.7 * math.cos(math.pi / 2 * (r + 0.5) / 7)
    IR.prism_xz(K.ngon(ox, oz, rr, 14), y0, y1, (BRICK, BRICK2)[r % 2])
IS.box(-0.7, 0.7, 6.4, C, oz - 0.7, oz + 0.7, BRICK2)
IS.box(-0.9, 0.9, 10.0, 10.4, oz - 0.9, oz + 0.9, DARK)
IS.frame_xy([(-2.0, 3.2), (2.0, 3.2), (2.0, 4.6), (1.2, 5.6), (-1.2, 5.6), (-2.0, 4.6)],
            [(-1.5, 3.25), (1.5, 3.25), (1.5, 4.5), (0.9, 5.1), (-0.9, 5.1), (-1.5, 4.5)], ZF + 7.6, ZF + 8.4, STONE)
IG.prism_xy([(-1.5, 3.25), (1.5, 3.25), (1.5, 4.5), (0.9, 5.1), (-0.9, 5.1), (-1.5, 4.5)], ZF + 7.5, ZF + 7.6, "FF8A30")
IG.prism_xy(K.ngon(0.0, 3.9, 0.7, 8), ZF + 7.6, ZF + 7.7, "FFD060")
IS.box(-5.0, 5.0, 3.2, 3.5, ZF + 0.88, ZF + 8.5, STONE)
for k in range(5):  # поленница у печи
    IS.prism_zy(K.ngon(ZF + 3.0, 0.45 + 0.8 * (k // 3), 0.4, 7), 5.4 + 0.85 * (k % 3), 6.2 + 0.85 * (k % 3), "C89A64")
beam(IS, (-6.6, 0.0, ZF + 6.6), (-6.1, 6.0, ZF + 5.4), 0.15, 0.15, WOOD)  # лопата
IS.box(-6.8, -5.4, 5.8, 5.88, ZF + 4.9, ZF + 6.0, WOOD)
# прилавок с витриной пицц слева
IR.box(-W + 0.9, -11.0, 0.0, 3.4, -12.0, 2.0, GREEN2)
IS.box(-W + 0.7, -10.8, 3.4, 3.7, -12.2, 2.2, STONE)
IS.frame_zy(K.rect(-11.6, 1.6, 3.7, 5.2), K.rect(-11.4, 1.4, 3.8, 5.0), -11.5, -11.3, "C8C8C8")
IG.box(-11.46, -11.36, 3.8, 5.0, -11.4, 1.4, "9ABFC8")
for k, z in enumerate((-9.4, -5.2, -1.0)):
    pizza(IS, -13.6, 3.72, z, 1.3, seed=k + 10)
IS.box(-W + 0.9, -11.6, 3.7, 3.9, 4.0, 5.4, DARK)  # касса
IS.box(-W + 1.1, -12.0, 3.9, 4.8, 4.2, 5.2, "D8D0C0")
# полки справа: масло, банки, томаты; связки чеснока и перца
for r in range(3):
    y = 5.0 + 2.2 * r
    IS.box(W - 1.9, W - 0.88, y - 0.2, y, -13.0, -2.0, WOOD2)
    for k in range(7):
        z = -12.4 + 1.5 * k
        if (k + r) % 3 == 0:
            IS.prism_xz(K.ngon(W - 1.4, z, 0.3, 6), y, y + 1.3, "9AB04A")
            IS.prism_xz(K.ngon(W - 1.4, z, 0.12, 6), y + 1.3, y + 1.7, DARK)
        elif (k + r) % 3 == 1:
            IS.prism_xz(K.ngon(W - 1.4, z, 0.4, 8), y, y + 0.9, RED)
            IS.prism_xz(K.ngon(W - 1.4, z, 0.42, 8), y + 0.9, y + 1.0, "C8C8C8")
        else:
            IS.prism_xz(K.ngon(W - 1.4, z, 0.38, 8), y, y + 1.1, "E8E0C0")
            IS.prism_xz(K.ngon(W - 1.4, z, 0.4, 8), y + 1.1, y + 1.3, "D8A040")
for k, z in enumerate((-14.0, 1.0, 5.0)):  # связки чеснока / перца с балок
    for i in range(5):
        y = 15.2 - 0.6 * i
        col = ("F2EEDC", RED, "F2EEDC")[k]
        IS.prism_xz(K.octa(W - 1.6, z, 0.3, 0.3, 0.12), y - 0.45, y, col)
    IS.box(W - 1.63, W - 1.57, 15.2, C - 0.9, z - 0.03, z + 0.03, "C8A060")
# столики в клетчатых скатертях и лампы над ними
for x, z in ((-11.0, 9.0), (11.0, 9.0), (11.0, 4.0), (-10.5, -14.0)):
    table(IS, x, z)
    chair(IS, x - 1.8, z, 1)
    chair(IS, x + 1.8, z, -1, GREEN)
    IS.box(x - 0.03, x + 0.03, 7.0, C - 0.9, z - 0.03, z + 0.03, DARK)
    IS.cone([(x + 0.9 * math.cos(t), 6.4, z + 0.9 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]], (x, 7.2, z), GREEN2)
    IG.prism_xz(K.ngon(x, z, 0.35, 8), 6.1, 6.4, "FFE0A0")
# расписные тарелки над прилавком и гирлянда флажков под балками
for k in range(6):
    z, y = -12.0 + 2.6 * k, 9.0 + 1.2 * (k % 2)
    IS.prism_zy(K.ngon(z, y, 0.85, 12), -W + 0.88, -W + 1.0, WHITE)
    IS.prism_zy(K.ngon(z, y, 0.55, 12), -W + 1.0, -W + 1.04, (GREEN, RED, "3A6AC8")[k % 3])
for z0, z1 in ((-13.0, 9.0),):
    for e in (-9.0, 9.0):
        pts = D.chain(IS, (e, C - 1.0, z0), (e, C - 1.0, z1), 10, 0.05, DARK, sag=1.4)
        for i, (x, y, z) in enumerate(pts[1:-1]):
            IS.prism_zy([(z - 0.5, y), (z + 0.5, y), (z, y - 1.0)], x - 0.04, x + 0.04, (GREEN, WHITE, RED)[i % 3])
# меню-доски на дальней стене по бокам от печи
for x in (-11.0, 10.0):
    IS.box(x - 2.6, x + 2.6, 7.0, 11.0, ZF + 0.88, ZF + 1.05, WOOD2)
    IS.box(x - 2.3, x + 2.3, 7.3, 10.7, ZF + 1.05, ZF + 1.1, "2E3A34")
    for k in range(4):
        IS.box(x - 1.9, x + 0.6 + 0.4 * (k % 2), 10.0 - 0.75 * k, 10.12 - 0.75 * k, ZF + 1.1, ZF + 1.13, ("F6F0E2", "FFD03A")[k % 2])
        IS.prism_xy(K.ngon(x + 1.6, 10.06 - 0.75 * k, 0.18, 6), ZF + 1.1, ZF + 1.13, RED)
# очаг-постамент: кирпичный барабан и тёмная доска
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 3.9, 16), 0.0, 0.75, BRICK)
for k in range(16):
    t = 2 * math.pi * (k + 0.5) / 16
    IS.box(px + 3.86 * math.cos(t) - 0.04, px + 3.86 * math.cos(t) + 0.04, 0.05, 0.7, pz + 3.86 * math.sin(t) - 0.04,
           pz + 3.86 * math.sin(t) + 0.04, STONE)
IS.prism_xz(K.ngon(px, pz, 4.0, 16), 0.75, 0.85, STONE)
IS.prism_xz(K.ngon(px, pz, 3.6, 16), 0.85, TOP, "3A2A22")
for k in range(6):  # листики базилика по краю
    t = 2 * math.pi * k / 6 + 0.3
    IS.prism_xz(K.octa(px + 3.2 * math.cos(t), pz + 3.2 * math.sin(t), 0.25, 0.14, 0.06), TOP, TOP + 0.05, "3FA64A")
B.lift_leaves(IS, WOOD2, GREEN)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, PLAST)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, TERRA)
SL.box(-FX - 0.4, FX + 0.4, 1.0, 3.4, -FZ - 0.5, FZ + 0.5, BRICK)
SL.box(-14.0, 15.6, 7.6, 9.5, -FZ - 3.6, -FZ, GREEN)
SL.prism_xy([rot(-4.0, 1.4), rot(4.0, 1.4), rot(0.0, -2.2)], -FZ - 1.5, -FZ - 0.4, CHEESE)
SL.box(FX, FX + 3.1, -1.0, 18.6, tz - 1.1, tz + 1.1, BRICK)

F.build(exhibit=(PED[0], TOP, PED[1], 2.2), lamps=[("Hall", (0, 14, 6), 2600, (1.0, 0.9, 0.75)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.95, 0.85)),
                                                   ("Fire", (0, 4, ZF + 5), 1200, (1.0, 0.6, 0.3))])
