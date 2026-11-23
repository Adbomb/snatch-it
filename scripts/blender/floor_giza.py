"""Этаж «Пирамиды Гизы» музея-небоскрёба (четвёртая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — пустыня Гизы. Снаружи весь фасад — огромная ступенчатая пирамида из известняка с белой облицовкой
наверху и золотым пирамидионом, у её подножия — тёмный вход под каменной притолокой с голубым поясом; стены вокруг —
кладка крупными блоками, карниз-выкружка с синими и золотыми полосами, по углам — обелиски с золотыми вершинами,
у подножия — песчаные дюны; бока — пальмовая роща у колодца и караван верблюдов; сзади — шатёр торговцев. Внутри —
ночь в пустыне: небо полосами от лилового заката к тёмно-синей ночи, звёзды и месяц, на горизонте — силуэты
далёких пирамид и барханы, песчаный пол с дюнами, оазис с пальмами, шатёр бедуинов с коврами и фонарями, лежащие
верблюды, дорожка из плит к ступенчатому постаменту-зиккурату под прожектором.
Запуск: blender --background --factory-startup --python scripts/blender/floor_giza.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab, taper  # noqa: E402

SAND, SAND2, SAND3, DUNE = "E8C27A", "D9AE62", "F2D69A", "C89A58"
STONE, STONE2, STONE3, CASING = "D8B878", "C4A062", "ECD2A0", "F8E4B4"
GOLD, GOLD2, LAPIS, LAPIS2, RED = "F2C230", "D9A21A", "2A5AA8", "3FA0C8", "C0442A"
NIGHT, NIGHT2, NIGHT3, DUSK, DUSK2 = "141C48", "1E2A66", "2E3A88", "5A4AA0", "8A5A9A"
FAR, FAR2, WATER, CAMEL, CAMEL2 = "3A2E5A", "4E3E6E", "2EA8C0", "C8904A", "A87038"
TENT, TENT2, RUG, RUG2, DOORWAY = "E8D4B0", "B8402E", "9A2A3A", "2A4A9A", "2A2018"
SKY0, SKY1, SKY2, SKY3 = "F4DCA0", "C6E4F2", "92CCF0", "62AEE8"

F = B.Floor("GZ", "GizaPyramids", quiet=(SAND, SAND2, SAND3, DUNE, TENT, TENT2, RUG, RUG2, SKY0, SKY1, SKY2, SKY3), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def camel(p, x, z, facing, y=0.0, lying=False):
    """Верблюд в профиль (смотрит по оси x: facing = ±1): туловище, горб, шея, голова, ноги, седло с попоной."""
    f = facing
    by = y + (0.6 if lying else 2.4)
    p.box(x - 1.5, x + 1.5, by, by + 1.4, z - 0.6, z + 0.6, CAMEL)
    p.loft([(x - 0.9, by + 1.4, z - 0.5), (x + 0.9, by + 1.4, z - 0.5), (x + 0.9, by + 1.4, z + 0.5), (x - 0.9, by + 1.4, z + 0.5)],
           [(x - 0.3, by + 2.2, z - 0.3), (x + 0.3, by + 2.2, z - 0.3), (x + 0.3, by + 2.2, z + 0.3), (x - 0.3, by + 2.2, z + 0.3)],
           CAMEL2)
    beam(p, (x + f * 1.3, by + 1.0, z), (x + f * 2.2, by + 2.6, z), 0.55, 0.55, CAMEL)
    p.box(min(x + f * 1.9, x + f * 3.1), max(x + f * 1.9, x + f * 3.1), by + 2.4, by + 3.0, z - 0.3, z + 0.3, CAMEL)
    p.box(x - 0.7, x + 0.7, by + 1.3, by + 1.55, z - 0.7, z + 0.7, RUG)  # попона
    if lying:
        for e in (-1, 1):
            p.box(x + e * 1.0 - 0.5, x + e * 1.0 + 0.5, y, by, z - 0.75, z + 0.75, CAMEL2)
    else:
        for e in (-1, 1):
            for s in (-1, 1):
                p.box(x + e * 1.1 - 0.2, x + e * 1.1 + 0.2, y, by, z + s * 0.35 - 0.2, z + s * 0.35 + 0.2, CAMEL2)


def stepped(p, cx, y0, cz, half, steps, rise, depth_axis, colors, base_d, dd, out=-1):
    """Ступенчатая пирамида-рельеф на стене z (depth_axis='z') или в плане: ступени по высоте, сужаются к верху."""
    for k in range(steps):
        w = half * (1 - k / steps)
        d = base_d - dd * k
        p.box(cx - w, cx + w, y0 + rise * k, y0 + rise * (k + 1), cz + out * d if out < 0 else cz, cz if out < 0 else cz + d,
              colors[k % len(colors)])


# ══ ФАСАД: пирамида ═══════════════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, STONE2, STONE2, NIGHT)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.2, SAND)
    slab(FR, axis, fixed, out, 0.88, -half, half, -0.2, 16.0, STONE)
    if fi == 0:  # перед: между пилонами — небо над дюнами, на нём пирамида
        for y0, y1, col in ((-0.2, 2.0, SKY0), (2.0, 5.0, SKY1), (5.0, 9.0, SKY2), (9.0, 16.0, SKY3)):
            slab(FR, axis, fixed, out, 0.88, -13.0, 13.0, y0, y1, col)
        FG.prism_xy(K.ngon(9.0, 12.6, 1.6, 12), -FZ - 1.0, -FZ - 0.9, "FFF4C0")
        for s in (-1, 1):  # пилоны по краям с карнизом и картушем
            slab(FR, axis, fixed, out, 2.88, s * 13.0, s * (half + 0.6), -0.2, 16.0, STONE)
            for r in range(8):
                slab(FS, axis, fixed, out, 2.98, s * 13.1, s * (half + 0.5), -0.2 + 2.0 * r + 1.9, -0.2 + 2.0 * r + 2.0, STONE2)
            d0, d1 = sorted((fixed + out * 2.88, fixed + out * 3.1))
            FS.frame_xy(K.octa(s * 16.0, 9.0, 1.2, 3.0, 0.5), K.octa(s * 16.0, 9.0, 0.9, 2.7, 0.4), d0, d1, GOLD)
            FS.prism_xy(K.octa(s * 16.0, 9.0, 0.9, 2.7, 0.4), d0 + 0.05, d1 - 0.05, LAPIS)
            for m in range(3):
                FS.box(s * 16.0 - 0.4, s * 16.0 + 0.4, 7.2 + 1.2 * m, 7.8 + 1.2 * m, d0 - 0.12, d0, (GOLD, RED, GOLD2)[m])
    for r in range(8):  # кладка крупными блоками со сдвигом швов
        y0 = -0.2 + 2.0 * r
        off = 2.0 if r % 2 else 0.0
        k = 0
        a = -half - off
        while a < half:
            a1 = min(a + 4.0, half)
            if a1 - max(a, -half) >= 1.0 and rng(fi, r, k) > 0.55 and fi != 0:
                slab(FR, axis, fixed, out, 1.08, max(a, -half) + 0.1, a1 - 0.1, y0 + 0.1, y0 + 1.9, (STONE3, STONE2)[k % 2])
            a, k = a1, k + 1
    # карниз-выкружка: синие и золотые полосы, золотой пояс
    B.chamfer(FR, axis, fixed, out, -half - 1.0, half + 1.0, [(0.0, 16.0), (1.0, 16.0), (1.0, 16.4), (1.9, 17.6),
                                                             (1.9, 18.0), (0.0, 18.0)], STONE3)
    slab(FS, axis, fixed, out, 1.15, -half - 0.6, half + 0.6, 16.0, 16.4, GOLD2)
    for k in range(int(2 * half // 1.4)):
        a = -half + 0.7 + 1.4 * k
        slab(FS, axis, fixed, out, 1.5, a - 0.32, a + 0.32, 16.6, 17.4, (LAPIS, GOLD, LAPIS2)[k % 3])
    slab(FR, axis, fixed, out, 0.88, -half, half, 18.0, 18.9, STONE)
    for k in range(5):  # дюны у подножия
        a = -half + 2.0 + (2 * half - 4.0) * k / 4 + (rng(fi, k) - 0.5) * 2.0
        w = 2.4 + 1.4 * rng(k, fi)
        h = 0.9 + 1.2 * rng(fi, k, 3)
        d0, d1 = sorted((fixed + out * 0.9, fixed + out * 2.88))
        if axis == "z":
            if fi == 0 and abs(a) < 15.0:
                continue
            FQ.prism_xy([(a - w, -0.2), (a + w, -0.2), (a + w * 0.3, -0.2 + h), (a - w * 0.4, -0.2 + h * 0.9)], d0, d1, DUNE)
        else:
            FQ.prism_zy([(a - w, -0.2), (a + w, -0.2), (a + w * 0.3, -0.2 + h), (a - w * 0.4, -0.2 + h * 0.9)], d0, d1, DUNE)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))

# перед: огромная ступенчатая пирамида (облицовка наверху, золотой пирамидион)
STEPS = 8
for k in range(STEPS):
    w = 14.5 - 1.75 * k
    y0, y1 = -0.2 + 2.0 * k, 1.8 + 2.0 * k
    d = 4.88 - 0.4 * k
    col = (STONE3, CASING)[k >= 5]
    FR.box(-w, w, y0, y1, -FZ - d, -FZ - 0.88, col)
    FS.box(-w + 0.1, w - 0.1, y0, y0 + 0.35, -FZ - d - 0.06, -FZ - d + 0.3, STONE2)  # тень-подступёнок
FS.prism_xy([(-2.0, 15.8), (2.0, 15.8), (0.0, 18.6)], -FZ - 2.3, -FZ - 1.4, GOLD)
FS.prism_zy([(-FZ - 2.3, 15.8), (-FZ - 0.5, 15.8), (-FZ - 1.4, 18.6)], -2.0, 2.0, GOLD2)
FG.prism_xy([(-0.6, 17.4), (0.6, 17.4), (0.0, 18.4)], -FZ - 2.36, -FZ - 2.3, "FFF2B0")
# вход у подножия: тёмный проём, косяки, притолока с голубым поясом и золотым солнечным диском с крыльями
FS.box(-2.4, 2.4, 0.4, 5.6, -FZ - 4.95, -FZ - 4.6, DOORWAY)
for s in (-1, 1):
    FS.box(s * 2.4, s * 3.4, 0.4, 6.0, -FZ - 5.3, -FZ - 4.6, STONE3)
FS.box(-3.8, 3.8, 6.0, 7.2, -FZ - 5.4, -FZ - 4.6, STONE3)
FS.box(-3.6, 3.6, 6.3, 6.9, -FZ - 5.5, -FZ - 5.4, LAPIS)
FS.prism_xy(K.octa(0.0, 6.6, 0.5, 0.5, 0.2), -FZ - 5.65, -FZ - 5.5, GOLD)
for s in (-1, 1):
    FS.prism_xy([(s * 0.5, 6.75), (s * 2.6, 6.95), (s * 2.4, 6.45), (s * 0.5, 6.45)], -FZ - 5.62, -FZ - 5.5, GOLD2)
for s in (-1, 1):  # факелы у входа
    D.torch(FS, FG, s * 5.0, -0.2, -FZ - 5.6, 3.2)
# обелиски по углам
for sx in (-1, 1):
    ox, oz = sx * (FX + 1.6), -FZ - 1.6
    FS.box(ox - 1.3, ox + 1.3, -0.2, 0.8, oz - 1.3, oz + 1.3, STONE2)
    FS.loft([(ox - 0.8, 0.8, oz - 0.8), (ox + 0.8, 0.8, oz - 0.8), (ox + 0.8, 0.8, oz + 0.8), (ox - 0.8, 0.8, oz + 0.8)],
            [(ox - 0.5, 15.4, oz - 0.5), (ox + 0.5, 15.4, oz - 0.5), (ox + 0.5, 15.4, oz + 0.5), (ox - 0.5, 15.4, oz + 0.5)], RED)
    FS.cone([(ox - 0.5, 15.4, oz - 0.5), (ox + 0.5, 15.4, oz - 0.5), (ox + 0.5, 15.4, oz + 0.5), (ox - 0.5, 15.4, oz + 0.5)],
            (ox, 16.8, oz), GOLD)
    for m in range(4):  # иероглифы-насечки
        y = 4.0 + 2.4 * m
        FS.box(ox - 0.35, ox + 0.35, y, y + 0.9, oz - 0.75, oz - 0.68, GOLD2)
# бока: пальмовая роща у колодца (слева) и караван (справа)
for s in (-1, 1):
    fx = s * FX
    for k, (z, h) in enumerate(((-10.0, 11.0), (-2.0, 13.0), (9.0, 10.5))):
        D.palm(FS, (fx + s * 2.2, -0.2, z), (s * 1.4, 0.4 * (k - 1)), h)
    if s < 0:
        FS.prism_xz(K.ngon(fx - 2.6, 4.0, 1.6, 10), -0.2, 1.2, STONE3)  # колодец
        FS.prism_xz(K.ngon(fx - 2.6, 4.0, 1.1, 10), 1.15, 1.25, WATER)
        for e in (-1, 1):
            FS.box(fx - 2.75, fx - 2.45, 1.2, 4.2, 4.0 + e * 1.3 - 0.15, 4.0 + e * 1.3 + 0.15, "6A4A2A")
        FS.box(fx - 2.8, fx - 2.4, 4.0, 4.3, 2.5, 5.5, "6A4A2A")
    else:
        for k, z in enumerate((-12.0, -4.5)):
            camel(FS, fx + 2.6, z, -1 if k else -1, y=-0.2)
# тыл: шатёр торговцев с полосатым пологом и ящиками
FQ.prism_zy([(FZ + 0.2, 7.0), (FZ + 5.0, 3.0), (FZ + 5.0, 3.4), (FZ + 0.2, 7.4)], -9.0, 9.0, TENT)
for k in range(6):
    FQ.prism_zy([(FZ + 0.25, 7.05), (FZ + 5.05, 3.05), (FZ + 5.05, 3.45), (FZ + 0.25, 7.45)], -8.5 + 3.0 * k,
                -7.5 + 3.0 * k, TENT2)
for x in (-8.6, 8.6):
    FS.box(x - 0.15, x + 0.15, -0.2, 3.0, FZ + 4.8, FZ + 5.1, "6A4A2A")
for k, x in enumerate((-6.0, -3.6, 2.0, 5.0)):
    D.crate(FS, x, FZ + 2.4, -0.2, 1.2 + 0.2 * (k % 2))
for x in (-1.0, 0.4):
    D.barrel(FS, x, FZ + 3.0, -0.2, 0.6, 1.3)

# ══ ИНТЕРЬЕР: ночь в пустыне ══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.2  # широкий низкий помост: макет пирамид стоит на своём столе 10.9 × 9 (масштаб 3.4) — ножки на верхней ступени
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), SAND)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:  # небо полосами: закат у горизонта → ночь
        for y0, y1, col in ((0.0, 2.0, DUSK2), (2.0, 4.0, DUSK), (4.0, 7.0, NIGHT3), (7.0, 11.0, NIGHT2), (11.0, C, NIGHT)):
            if gap and y0 < DOOR[1] + 0.1:
                continue
            slab(IR, axis, fixed, out, 0.88, a0, a1, y0, y1, col)
    if gap:
        for y0, y1, col in ((DOOR[1] + 0.1, 11.0, NIGHT2), (11.0, C, NIGHT)):
            slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, y0, y1, col)
        for s in (-1, 1):  # каменный портал вокруг лифта
            slab(IR, axis, fixed, out, 1.88, s * (DOOR[0] + 0.6), s * (DOOR[0] + 1.8), 0.0, DOOR[1] + 1.2, STONE)
        slab(IR, axis, fixed, out, 1.88, -DOOR[0] - 1.8, DOOR[0] + 1.8, DOOR[1] + 0.1, DOOR[1] + 1.4, STONE3)
        slab(IS, axis, fixed, out, 2.0, -DOOR[0] - 1.6, DOOR[0] + 1.6, DOOR[1] + 0.5, DOOR[1] + 1.0, LAPIS)
    if not gap:  # барханы у горизонта
        for k in range(4):
            a = -half + 2.0 + (2 * half - 4.0) * k / 3
            w = 3.0 + 1.6 * rng(idx, k)
            h = 1.2 + 1.4 * rng(k, idx)
            d0, d1 = sorted((fixed + out * 0.9, fixed + out * 1.6))
            lim = half - 0.1  # бархан не уходит в соседнюю стену
            pts = [(max(-lim, min(lim, u)), v) for u, v in ((a - w, 0.0), (a + w, 0.0), (a + 0.3 * w, h), (a - 0.5 * w, h * 0.8))]
            (IQ.prism_xy if axis == "z" else IQ.prism_zy)(pts, d0, d1, DUNE)
# далёкие пирамиды на горизонте (по бокам от экспоната; центр — месяц и звёзды)
for x, w, h in ((-12.0, 4.0, 5.6), (-6.8, 2.6, 3.6), (7.4, 2.6, 3.8), (12.6, 4.2, 6.0)):
    IR.prism_xy([(x - w, 1.0), (x + w, 1.0), (x, 1.0 + h)], ZF + 0.3, ZF + 1.0, FAR)
    IS.prism_xy([(x, 1.0 + h), (x + w, 1.0), (x + w * 0.62, 1.0)], ZF + 1.0, ZF + 1.1, FAR2)
for z, w, h in ((-8.0, 3.6, 5.0), (4.0, 2.4, 3.2)):
    for s in (-1, 1):
        IR.prism_zy([(z - w, 1.0), (z + w, 1.0), (z, 1.0 + h)], *sorted((s * (W - 0.3), s * (W - 1.0))), FAR)
MOON = [(-7.0 + 1.8 * math.cos(math.radians(a)), 14.0 + 1.8 * math.sin(math.radians(a))) for a in range(60, 301, 30)]
MOON += [(-6.2 + 1.45 * math.cos(math.radians(a)), 14.0 + 1.45 * math.sin(math.radians(a))) for a in range(250, 109, -35)]
IG.prism_xy(MOON, ZF + 0.9, ZF + 1.0, "FFF2C0")
for k in range(46):  # звёзды на стенах и потолке
    x = -W + 1.0 + (2 * W - 2.0) * rng(k, 1)
    z = ZF + 1.0 + (ZB - ZF - 2.0) * rng(k, 2)
    s = 0.12 + 0.12 * rng(k, 3)
    if k < 22:
        IG.box(x - s, x + s, C - 0.05, C - 0.01, z - s, z + s, "FFF8D8")
    elif k < 34:
        y = 8.0 + 9.0 * rng(k, 4)
        IG.box(x - s, x + s, y - s, y + s, ZF + 0.88, ZF + 0.92, "FFF8D8")
    else:
        y = 8.0 + 9.0 * rng(k, 4)
        sx = -1 if k % 2 else 1
        x0, x1 = sorted((sx * (W - 0.88), sx * (W - 0.92)))
        IG.box(x0, x1, y - s, y + s, z - s, z + s, "FFF8D8")
# дюны на полу и дорожка из плит от лифта к постаменту
for k, (x, z, w, h) in enumerate(((-11.0, -11.0, 4.0, 1.4), (11.5, -12.0, 4.4, 1.6), (-13.5, 9.5, 3.0, 1.0), (13.0, 9.0, 3.0, 1.1))):
    IQ.prism_xz([(x - w, z - 1.6), (x + w, z - 1.4), (x + w * 0.8, z + 1.8), (x - w * 0.6, z + 2.0)], 0.0, h * 0.5, SAND2)
    IQ.prism_xz([(x - w * 0.6, z - 0.8), (x + w * 0.5, z - 0.7), (x + w * 0.4, z + 1.0), (x - w * 0.4, z + 1.1)], h * 0.5, h, DUNE)
for k in range(3):  # дорожка кончается у помоста
    z = 9.5 - 2.4 * k
    IR.box(-1.5, 1.5, 0.0, 0.12, z - 1.0, z + 1.0, (STONE3, STONE)[k % 2])
# оазис слева: пруд, камыши, пальмы
IS.prism_xz(K.ngon(-11.0, 2.0, 3.6, 12), 0.0, 0.3, STONE2)
IS.prism_xz(K.ngon(-11.0, 2.0, 3.1, 12), 0.28, 0.34, WATER)
for k in range(5):
    t = 2 * math.pi * k / 5
    D.bush(IS, -11.0 + 3.6 * math.cos(t), 2.0 + 3.6 * math.sin(t), 0.0, 0.7)
for (x, z), (lx, lz), h in (((-14.2, -1.0), (1.0, 0.8), 11.5), ((-8.0, 5.6), (-0.8, -0.6), 9.0), ((-14.0, 5.0), (1.2, -0.4), 10.0)):
    D.palm(IS, (x, 0.0, z), (lx, lz), h)
# шатёр бедуинов справа: полосатый скат, столбы, ковры, подушки, фонари, верблюды
FX0, FX1, TZ0, TZ1 = 8.4, 16.0, -9.0, -1.0
IQ.prism_zy([(TZ0, 7.0), (TZ1, 7.0), (TZ1, 7.3), (TZ0, 7.3)], FX0 + 3.0, FX1, TENT)
IQ.prism_xy([(FX0, 4.6), (FX0 + 3.0, 7.0), (FX0 + 3.0, 7.3), (FX0, 4.9)], TZ0, TZ1, TENT)
for k in range(4):
    z = TZ0 + 0.4 + 2.0 * k
    IQ.prism_xy([(FX0 - 0.02, 4.62), (FX0 + 3.0, 7.03), (FX0 + 3.0, 7.33), (FX0 - 0.02, 4.92)], z, z + 0.8, TENT2)
for z in (TZ0 + 0.2, TZ1 - 0.2):
    IS.box(FX0 - 0.1, FX0 + 0.2, 0.0, 4.8, z - 0.15, z + 0.15, "6A4A2A")
IQ.box(FX0 + 0.6, FX1 - 0.2, 0.0, 0.12, TZ0 + 0.5, TZ1 - 0.5, RUG)
IQ.box(FX0 + 1.6, FX1 - 1.2, 0.12, 0.16, TZ0 + 1.5, TZ1 - 1.5, RUG2)
for k, z in enumerate((TZ0 + 1.6, TZ0 + 4.0, TZ0 + 6.4)):
    IS.box(14.2, 15.8, 0.0, 0.9, z - 0.8, z + 0.8, (RUG2, TENT2, RUG)[k])
for z in (TZ0 + 2.0, TZ1 - 2.0):
    IS.box(FX0 + 0.8 - 0.03, FX0 + 0.8 + 0.03, 4.8, 6.4, z - 0.03, z + 0.03, "3A2E24")
    D.lantern(IS, IG, FX0 + 0.8, 4.0, z, 1.0)
camel(IS, 11.0, 4.0, -1, lying=True)
camel(IS, 4.0, -12.0, 1, lying=True)
# ступенчатый постамент-зиккурат с золотым кантом, факелы
px, pz = PED
# верхняя ступень — лазурит: песочные пирамиды не сливаются с песчаником
for k, (hw, hd, y0, y1, col) in enumerate(((6.4, 5.4, 0.0, 0.4, STONE2), (6.0, 5.0, 0.4, 0.8, STONE), (5.8, 4.85, 0.8, TOP, LAPIS))):
    IR.box(px - hw, px + hw, y0, y1, pz - hd, pz + hd, col)
    IS.frame_xz(K.rect(px - hw - 0.06, px + hw + 0.06, pz - hd - 0.06, pz + hd + 0.06), K.rect(px - hw + 0.12, px + hw - 0.12,
                pz - hd + 0.12, pz + hd - 0.12), y1 - 0.14, y1 + 0.02, GOLD2)
for s in (-1, 1):
    D.torch(IS, IG, px + s * 7.4, 0.0, pz + 2.6, 2.6)
B.lift_leaves(IS, STONE2, GOLD)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, STONE)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.2, -FZ - 2.9, FZ + 2.9, SAND)
SL.box(-FX - 1.9, FX + 1.9, 16.0, 18.0, -FZ - 1.9, FZ + 1.9, STONE3)
for k in range(4):
    w = 14.5 - 3.5 * k
    SL.box(-w, w, -0.2 + 4.0 * k, 3.8 + 4.0 * k, -FZ - 4.88 + 0.8 * k, -FZ, (STONE, STONE3, STONE, CASING)[k])
SL.prism_xy([(-2.0, 15.8), (2.0, 15.8), (0.0, 18.6)], -FZ - 2.3, -FZ - 1.4, GOLD)
for sx in (-1, 1):
    SL.loft([(sx * (FX + 1.6) - 0.8, -0.2, -FZ - 2.4), (sx * (FX + 1.6) + 0.8, -0.2, -FZ - 2.4),
             (sx * (FX + 1.6) + 0.8, -0.2, -FZ - 0.8), (sx * (FX + 1.6) - 0.8, -0.2, -FZ - 0.8)],
            [(sx * (FX + 1.6) - 0.4, 16.8, -FZ - 2.0), (sx * (FX + 1.6) + 0.4, 16.8, -FZ - 2.0),
             (sx * (FX + 1.6) + 0.4, 16.8, -FZ - 1.2), (sx * (FX + 1.6) - 0.4, 16.8, -FZ - 1.2)], RED)

F.build(exhibit=(PED[0], TOP, PED[1], 3.4), lamps=[("Hall", (0, 14, 6), 2600, (0.8, 0.82, 1.0)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.94, 0.82)),
                                                   ("Torch", (-11, 4, 2), 900, (1.0, 0.7, 0.4))])
