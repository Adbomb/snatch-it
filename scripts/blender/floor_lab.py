"""Этаж «Газировка-мутант» музея-небоскрёба (шестая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — секретная лаборатория мутаций. Снаружи — металлические панели со швами, внизу — полоса жёлто-чёрных
«зебр», шлюзовая дверь со скошенными углами и штурвалом, лента окон с частыми переплётами, перед фасадом — три
огромные стеклянные колбы со светящейся зелёной жидкостью и пузырями на стальных подставках, от колб в стену идут
трубы с красными вентилями; на крыше — тарелка антенны, вентилятор в коробе, оранжевая мигалка, трубы-вытяжки;
на боку — вентиляционные решётки, бочки с зелёными подтёками и светящаяся лужа. Внутри — лаборатория: тёмный
плиточный пол с жёлтой разметкой, белые панели, у дальней стены — пульт с экранами-графиками, по бокам от него —
колбы с жидкостью, на стенах — полки с цветными склянками, верстак с микроскопом, роборука над залом, трубы и
лампы-полосы под потолком; экспонат — на стальной платформе с жёлто-чёрной каймой и фиолетовым светящимся кольцом.
Запуск: blender --background --factory-startup --python scripts/blender/floor_lab.py -- <репо> <превью>
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

PANEL, PANEL2, DARK, DARK2, STEEL, STEEL2 = "D4DAE0", "B4BEC8", "2C3238", "3E464E", "8A929C", "6A727C"
HAZ, BLACK, TOX, TOX2, PIPE, RED = "F2C230", "26262A", "7CF050", "3AB83A", "E07A30", "D83A2E"
VIOLET, SCREEN, WHITE, TEAL = "B070FF", "4AA8E8", "F2F4F6", "2A9A9A"

F = B.Floor("LB", "MutantSoda", quiet=("9A9EA4", DARK2, "5A626A"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def tank(p, g, x, z, r, y0, h, liquid=TOX, seed=0):
    """Колба: стальная подставка, стекло с жидкостью, крышка, пузыри (в детали стекла светятся)."""
    p.prism_xz(K.ngon(x, z, r + 0.35, 12), y0, y0 + 0.9, STEEL2)
    p.prism_xz(K.ngon(x, z, r + 0.2, 12), y0 + 0.9, y0 + 1.1, HAZ)
    g.prism_xz(K.ngon(x, z, r, 12), y0 + 1.1, y0 + 1.1 + h, liquid)
    for k in range(4):
        t = 2 * math.pi * (k + 0.5) / 4
        p.box(x + r * math.cos(t) - 0.09, x + r * math.cos(t) + 0.09, y0 + 1.1, y0 + 1.1 + h, z + r * math.sin(t) - 0.09,
              z + r * math.sin(t) + 0.09, STEEL)
    p.prism_xz(K.ngon(x, z, r + 0.3, 12), y0 + 1.1 + h, y0 + 1.5 + h, STEEL2)
    p.prism_xz(K.ngon(x, z, r * 0.5, 8), y0 + 1.5 + h, y0 + 1.8 + h, DARK2)
    for k in range(5):
        a = 2 * math.pi * rng(seed, k)
        rr = r * (0.3 + 0.6 * rng(k, seed))
        bx, bz = x + rr * 0.7 * math.cos(a), z + rr * 0.7 * math.sin(a)
        yy = y0 + 1.6 + h * 0.8 * rng(seed + 3, k)
        g.prism_xz(K.ngon(bx + (r - 0.05 - rr * 0.7) * math.cos(a) * 0.0, bz, 0.16, 6), yy, yy + 0.3, "E8FFD8")


def valve(pr, a, y, d0, d1, r=0.5):
    """Красный вентиль-штурвал на трубе (pr — prism_xy / prism_zy)."""
    pr(K.ngon(a, y, r, 10), d0, d1, RED)
    pr(K.ngon(a, y, r * 0.6, 10), d0 - 0.02, d1 + 0.02, DARK)
    pr(K.ngon(a, y, r * 0.2, 6), d0 - 0.04, d1 + 0.04, RED)


def hazard(p, axis, fixed, out, a0, a1, y0, y1, depth):
    """Полоса жёлто-чёрной «зебры» (наклонные полосы) на стене."""
    slab(p, axis, fixed, out, depth, a0, a1, y0, y1, HAZ)
    d0, d1 = sorted((fixed + out * depth, fixed + out * (depth + 0.04)))
    pr = p.prism_xy if axis == "z" else p.prism_zy
    a = a0
    while a < a1 - 0.6:
        pr([(a, y0), (min(a + 0.6, a1), y0), (min(a + 0.6 + (y1 - y0), a1), y1), (min(a + (y1 - y0), a1), y1)], d0, d1, BLACK)
        a += 1.2


# ══ ФАСАД: лаборатория ═══════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, PANEL, PANEL, DARK)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, "9A9EA4")
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 1.0, DARK2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.0, 15.6, PANEL)
    hazard(FS, axis, fixed, out, -half, half, 1.0, 2.0, 0.92)
    for k in range(int(2 * half // 3.0) + 1):  # швы панелей
        a = -half + 3.0 * k
        if fi == 0 and -8.6 < a < -3.0:
            continue
        slab(FS, axis, fixed, out, 0.96, a - 0.08, a + 0.08, 2.0, 15.6, PANEL2)
    for y in (6.0, 10.6):
        slab(FS, axis, fixed, out, 0.96, -half, half, y - 0.08, y + 0.08, PANEL2)
    slab(FR, axis, fixed, out, 1.88, -half - 0.5, half + 0.5, 15.6, 16.4, DARK2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 16.4, 18.9, PANEL2)
    slab(FR, axis, fixed, out, 1.3, -half - 0.2, half + 0.2, 18.4, 18.9, DARK2)
    if axis == "x":  # бока: вентрешётки, лента окон
        for z in (-9.0, 3.0):
            slab(FR, axis, fixed, out, 1.0, z - 3.0, z + 3.0, 3.0, 8.0, DARK2)
            for k in range(8):
                y = 3.3 + 0.6 * k
                slab(FS, axis, fixed, out, 1.15, z - 2.8, z + 2.8, y, y + 0.2, STEEL)
        slab(FG, axis, fixed, out, 0.92, -14.0, 14.0, 11.2, 13.6, "9AD8F0")
        for k in range(15):
            z = -14.0 + 2.0 * k
            slab(FS, axis, fixed, out, 1.1, z - 0.1, z + 0.1, 11.0, 13.8, DARK2)
        slab(FS, axis, fixed, out, 1.2, -14.2, 14.2, 10.8, 11.2, DARK2)
        slab(FS, axis, fixed, out, 1.2, -14.2, 14.2, 13.6, 13.9, DARK2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# лента окон на фасаде (частые переплёты)
FG.box(-15.0, 15.0, 11.2, 13.6, -FZ - 0.94, -FZ - 0.9, "9AD8F0")
for k in range(16):
    x = -15.0 + 2.0 * k
    FS.box(x - 0.1, x + 0.1, 11.0, 13.8, -FZ - 1.15, -FZ - 0.88, DARK2)
FS.box(-15.2, 15.2, 10.8, 11.2, -FZ - 1.4, -FZ - 0.88, DARK2)
FS.box(-15.2, 15.2, 13.6, 13.9, -FZ - 1.25, -FZ - 0.88, DARK2)
# шлюзовая дверь со скошенными углами и штурвалом
dx = -5.8
door_o = [(dx - 2.8, 1.0), (dx + 2.8, 1.0), (dx + 2.8, 7.0), (dx + 1.8, 8.0), (dx - 1.8, 8.0), (dx - 2.8, 7.0)]
door_i = [(dx - 2.2, 1.0), (dx + 2.2, 1.0), (dx + 2.2, 6.7), (dx + 1.5, 7.4), (dx - 1.5, 7.4), (dx - 2.2, 6.7)]
FS.frame_xy(door_o, door_i, -FZ - 1.5, -FZ - 0.88, HAZ)
FS.prism_xy(door_i, -FZ - 1.1, -FZ - 0.9, STEEL)
FS.box(dx - 0.06, dx + 0.06, 1.0, 7.4, -FZ - 1.16, -FZ - 1.1, DARK)
valve(FS.prism_xy, dx, 4.4, -FZ - 1.4, -FZ - 1.25, 0.9)
FS.box(dx - 2.6, dx + 2.6, 8.4, 9.0, -FZ - 1.3, -FZ - 0.88, DARK2)
FG.box(dx - 0.5, dx + 0.5, 8.5, 8.9, -FZ - 1.36, -FZ - 1.3, "FF8A30")
# три огромные колбы перед фасадом, трубы в стену с вентилями
for k, x in enumerate((1.6, 7.4, 13.2)):
    tz = -FZ - 3.6
    tank(FS, FG, x, tz, 1.7, 0.0, 6.4 - 0.8 * (k % 2), seed=k)
    top = 7.5 + 1.1 - 0.8 * (k % 2) + 0.0
    beam(FS, (x, top + 0.3, tz), (x, 9.6 + 0.4 * k, tz), 0.5, 0.5, STEEL2)
    beam(FS, (x, 9.6 + 0.4 * k, tz - 0.25), (x, 9.6 + 0.4 * k, -FZ - 0.88), 0.5, 0.5, STEEL2)
    FS.prism_xz(K.ngon(x, -FZ - 2.2, 0.55, 10), 9.6 + 0.4 * k + 0.25, 9.6 + 0.4 * k + 0.4, RED)
FS.box(-1.0, 15.8, 0.0, 0.3, -FZ - 6.0, -FZ - 1.2, DARK2)
hazard(FS, "z", -FZ - 6.0, -1, -1.0, 15.8, 0.0, 0.3, 0.0)
# бочки с подтёками и светящаяся лужа
for k, (x, z) in enumerate(((-13.6, -FZ - 4.6), (-15.6, -FZ - 5.6), (-15.0, -FZ - 3.6))):
    FS.prism_xz(K.ngon(x, z, 0.85, 10), 0.0, 2.0, HAZ)
    for yy in (0.5, 1.5):
        FS.prism_xz(K.ngon(x, z, 0.9, 10), yy - 0.06, yy + 0.06, BLACK)
    FS.prism_xz(K.ngon(x, z, 0.6, 10), 2.0, 2.06, TOX2)
    FS.box(x - 0.2, x + 0.2, 1.0, 2.0, z - 0.9, z - 0.84, TOX2)
FG.prism_xz(K.octa(-11.6, -FZ - 5.6, 1.4, 0.9, 0.4), -0.1, -0.04, TOX)
FS.box(-10.6, -8.6, 0.0, 1.6, -FZ - 6.6, -FZ - 4.6, PANEL2)  # ящик с зеброй
hazard(FS, "z", -FZ - 6.6, -1, -10.6, -8.6, 0.6, 1.0, 0.0)
# крыша: тарелка антенны, вентилятор, мигалка, вытяжки
FS.box(-14.0, -10.0, 16.4, 18.6, -FZ - 1.2, -FZ + 2.0, DARK2)
FS.prism_xy(K.ngon(-12.0, 17.5, 1.0, 12), -FZ - 1.3, -FZ - 1.2, STEEL)
for k in range(4):
    t = math.pi / 2 * k + 0.4
    FS.prism_xy([(-12.0, 17.5), (-12.0 + 0.95 * math.cos(t), 17.5 + 0.95 * math.sin(t)),
                 (-12.0 + 0.95 * math.cos(t + 0.7), 17.5 + 0.95 * math.sin(t + 0.7))], -FZ - 1.36, -FZ - 1.3, DARK)
FS.cone([(12.0 + 1.6 * math.cos(t), 18.6, -FZ - 1.6 + 0.9 * math.sin(t)) for t in [2 * math.pi * k / 10 for k in range(10)]],
        (12.0, 17.6, -FZ - 1.4), WHITE)
FS.box(11.9, 12.1, 16.4, 17.8, -FZ - 1.5, -FZ - 1.3, STEEL)
FS.prism_xz(K.ngon(4.0, -FZ - 1.4, 0.4, 8), 16.4, 17.6, DARK2)
FG.prism_xz(K.ngon(4.0, -FZ - 1.4, 0.32, 8), 17.6, 18.4, "FF8A30")
for x in (-4.0, -2.4):
    FS.prism_xz(K.ngon(x, -FZ - 1.4, 0.35, 8), 16.4, 18.6, STEEL)
# угловые трубы
for x in (-FX - 0.6, FX + 0.6):
    FS.prism_xz(K.ngon(x, -FZ - 0.6, 0.35, 8), 1.0, 15.6, STEEL2)
    for y in (4.0, 8.0, 12.0):
        FS.prism_xz(K.ngon(x, -FZ - 0.6, 0.45, 8), y, y + 0.3, DARK2)
# тыл: генератор и петля трубы
FS.box(-10.0, -2.0, 0.0, 4.0, FZ + 0.88, FZ + 4.0, STEEL2)
for k in range(6):
    FS.box(-9.6 + 1.3 * k, -9.0 + 1.3 * k, 1.0, 3.6, FZ + 4.0, FZ + 4.1, DARK2)
beam(FS, (4.0, 0.0, FZ + 2.0), (4.0, 10.0, FZ + 2.0), 0.6, 0.6, PIPE)
beam(FS, (4.0, 10.0, FZ + 2.0), (10.0, 10.0, FZ + 2.0), 0.6, 0.6, PIPE)
beam(FS, (10.0, 10.0, FZ + 2.0), (10.0, 0.0, FZ + 2.0), 0.6, 0.6, PIPE)

# ══ ИНТЕРЬЕР: лаборатория ════════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.1
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), DARK2)
for i in range(-7, 7):
    for j in range(-7, 7):
        if (i + j) % 2 == 0:
            IQ.box(2.4 * i + 0.04, 2.4 * i + 2.36, 0.02, 0.04, 2.27 * j + 0.04, 2.27 * j + 2.23, "4A525A")
for k in range(24):  # жёлтая разметка вокруг постамента
    t0, t1 = 2 * math.pi * k / 24, 2 * math.pi * (k + 0.55) / 24
    IQ.prism_xz([(5.4 * math.cos(t0), -3.0 + 5.4 * math.sin(t0)), (5.9 * math.cos(t0), -3.0 + 5.9 * math.sin(t0)),
                 (5.9 * math.cos(t1), -3.0 + 5.9 * math.sin(t1)), (5.4 * math.cos(t1), -3.0 + 5.4 * math.sin(t1))], 0.04, 0.06, HAZ)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, PANEL)
        slab(IR, axis, fixed, out, 1.0, a0, a1, 0.0, 1.4, DARK2)
        if not gap:
            slab(IR, axis, fixed, out, 0.96, a0, a1, 11.0, C, PANEL2)
        for k in range(int((a1 - a0) // 3.0) + 1):
            a = a0 + 3.0 * k
            slab(IS, axis, fixed, out, 0.96, a - 0.06, a + 0.06, 1.4, 11.0, PANEL2)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, PANEL2)
        hazard(IS, axis, fixed, out, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.9, 1.0)
    slab(IR, axis, fixed, out, 1.3, -half, half, 15.4, 16.0, DARK2)
# пульт с экранами у дальней стены
IR.box(-8.0, 8.0, 0.0, 3.2, ZF + 0.88, ZF + 3.0, DARK2)
IS.loft([(-8.2, 3.2, ZF + 0.88), (8.2, 3.2, ZF + 0.88), (8.2, 3.2, ZF + 3.2), (-8.2, 3.2, ZF + 3.2)],
        [(-8.2, 3.8, ZF + 0.88), (8.2, 3.8, ZF + 0.88), (8.2, 3.5, ZF + 3.2), (-8.2, 3.5, ZF + 3.2)], STEEL2)
for k in range(8):
    x = -7.2 + 2.05 * k
    IG.box(x - 0.3, x + 0.3, 3.62, 3.7, ZF + 2.0, ZF + 2.6, ("FF5A5A", "5AE85A", "FFD03A", "5AB8FF")[k % 4])
for k, x in enumerate((-6.0, -2.0, 2.0, 6.0)):
    IS.box(x - 1.8, x + 1.8, 5.0, 9.4, ZF + 0.88, ZF + 1.2, DARK)
    IG.box(x - 1.6, x + 1.6, 5.2, 9.2, ZF + 1.2, ZF + 1.26, ("1E3A5A", "1E4A3A", "1E3A5A", "3A1E4A")[k])
    for i in range(5):  # графики-столбики
        h = 0.6 + 2.6 * rng(k, i)
        IG.box(x - 1.3 + 0.55 * i, x - 0.95 + 0.55 * i, 5.6, 5.6 + h, ZF + 1.26, ZF + 1.3, ("5AE85A", "5AB8FF", "FFD03A", "FF8AC0")[(k + i) % 4])
IS.box(-8.0, 8.0, 9.6, 10.2, ZF + 0.88, ZF + 1.6, STEEL2)
# колбы по бокам от пульта
for x in (-12.4, 12.4):
    tank(IS, IG, x, ZF + 3.2, 1.6, 0.0, 9.0, seed=int(x))
    beam(IS, (x, 11.9, ZF + 3.2), (x, C - 0.4, ZF + 3.2), 0.5, 0.5, STEEL2)
# полки с цветными склянками и верстак с микроскопом
for s in (-1, 1):
    for r in range(3):
        y = 5.0 + 2.2 * r
        IS.box(*sorted((s * (W - 1.9), s * (W - 0.88))), y - 0.2, y, -12.0, -2.0, STEEL2)
        for k in range(8):
            z = -11.4 + 1.25 * k
            col = ("FF5AB0", "5AB8FF", "FFD03A", "7CF050", "B070FF")[(k + r + s) % 5]
            if (k + r) % 2:
                IS.prism_xz(K.ngon(s * (W - 1.4), z, 0.38, 8), y, y + 0.7, col)
                IS.prism_xz(K.ngon(s * (W - 1.4), z, 0.12, 6), y + 0.7, y + 1.2, WHITE)
            else:
                IS.prism_xz(K.ngon(s * (W - 1.4), z, 0.22, 6), y, y + 1.3, col)
    IR.box(*sorted((s * (W - 3.0), s * (W - 0.88))), 0.0, 3.2, 1.0, 6.0, PANEL2)
    IS.box(*sorted((s * (W - 3.2), s * (W - 0.88))), 3.2, 3.45, 0.8, 6.2, DARK2)
mx, mz = -(W - 2.0), 3.0
IS.box(mx - 0.6, mx + 0.6, 3.45, 3.7, mz - 0.6, mz + 0.6, BLACK)
beam(IS, (mx - 0.3, 3.7, mz), (mx - 0.2, 5.4, mz), 0.25, 0.4, WHITE)
beam(IS, (mx - 0.1, 5.2, mz), (mx + 0.5, 4.4, mz), 0.35, 0.35, BLACK)
IS.box(mx - 0.4, mx + 0.4, 3.9, 4.0, mz - 0.4, mz + 0.4, WHITE)
for k in range(4):
    IS.prism_xz(K.ngon(W - 2.2, 1.6 + 1.2 * k, 0.3, 8), 3.45, 4.2, ("FF5AB0", "5AB8FF", "FFD03A", "7CF050")[k])
# роборука над залом
rx, rz = 10.0, 6.0
IS.prism_xz(K.ngon(rx, rz, 0.9, 10), C - 0.6, C, STEEL2)
beam(IS, (rx, C - 0.6, rz), (rx - 1.0, 13.0, rz - 2.0), 0.6, 0.6, HAZ)
IS.prism_zy(K.ngon(rz - 2.0, 13.0, 0.5, 10), rx - 1.3, rx - 0.7, DARK)
beam(IS, (rx - 1.0, 13.0, rz - 2.0), (rx - 4.0, 10.6, rz - 4.4), 0.5, 0.5, HAZ)
for e in (-1, 1):
    taper(IS, (rx - 4.0, 10.6, rz - 4.4), (rx - 4.4 + e * 0.4, 9.6, rz - 4.8), 0.3, 0.1, DARK)
# трубы и лампы-полосы под потолком
for z in (-10.0, 0.0, 10.0):
    IS.box(-10.0, 10.0, C - 0.6, C - 0.4, z - 0.6, z + 0.6, STEEL2)
    IG.box(-9.6, 9.6, C - 0.66, C - 0.6, z - 0.4, z + 0.4, "F0F8FF")
for x in (-14.0, 14.0):
    beam(IS, (x, C - 1.2, -14.0), (x, C - 1.2, 14.0), 0.6, 0.6, PIPE)
    beam(IS, (x - 1.0 * (x > 0) + 0.0, C - 2.0, -14.0), (x - 1.0 * (x > 0), C - 2.0, 14.0), 0.4, 0.4, TEAL)
# стальная платформа-постамент: зебра, фиолетовое кольцо, зажимы
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.2, 16), 0.0, 0.45, DARK2)
for k in range(16):
    t0, t1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
    IS.prism_xz([(px + 3.95 * math.cos(t0), pz + 3.95 * math.sin(t0)), (px + 4.05 * math.cos(t0), pz + 4.05 * math.sin(t0)),
                 (px + 4.05 * math.cos(t1), pz + 4.05 * math.sin(t1)), (px + 3.95 * math.cos(t1), pz + 3.95 * math.sin(t1))],
                0.45, 0.8, (HAZ, BLACK)[k % 2])
IS.prism_xz(K.ngon(px, pz, 3.95, 16), 0.45, 0.8, DARK2)
IS.prism_xz(K.ngon(px, pz, 3.8, 16), 0.8, TOP, "3A4048")
ring_y(IG, px, pz, 3.3, 3.55, TOP, TOP + 0.04, VIOLET, n=16)
for k in range(4):
    t = math.pi / 2 * k + math.pi / 4
    cx, cz = px + 3.9 * math.cos(t), pz + 3.9 * math.sin(t)
    IS.box(cx - 0.4, cx + 0.4, 0.8, 1.5, cz - 0.4, cz + 0.4, STEEL)
B.lift_leaves(IS, DARK2, HAZ)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 18.9, -FZ, FZ, PANEL)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, "9A9EA4")
SL.box(-FX - 0.4, FX + 0.4, 1.0, 2.0, -FZ - 0.4, FZ + 0.4, HAZ)
SL.box(-15.0, 15.0, 11.0, 13.8, -FZ - 0.6, -FZ, SCREEN)
for x in (1.6, 7.4, 13.2):
    SL.prism_xz(K.ngon(x, -FZ - 3.6, 1.8, 8), 0.0, 8.0, TOX2)

F.build(exhibit=(PED[0], TOP, PED[1], 2.6), lamps=[("Hall", (0, 14, 6), 2400, (0.9, 0.95, 1.0)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.98, 0.95)),
                                                   ("Tox", (0, 6, ZF + 6), 900, (0.5, 1.0, 0.4))])
