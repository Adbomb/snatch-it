"""Этаж «Проклятый телевизор» музея-небоскрёба (третья партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — дом с привидениями из 80-х, ночь. Снаружи — сайдинг из сиреневых досок на каменном цоколе, белая
обводка углов, мансарда из тёмной черепицы с карнизом, на крыше — несколько телеантенн; окна нарочно несимметричны
(никакого «лица дома»): слева — большое эркерное окно, в котором мерцает голубой «снег» экрана, справа — крыльцо с
навесом, столбиками и дверью, наверху — заколоченное окно и круглое чердачное окошко; перед домом — покосившийся
штакетник с калиткой, почтовый ящик, тыквы без лиц, сухое дерево, паутина по углам; бок — кирпичная труба и окна со
ставнями, тыл — гора старых телевизоров. Внутри — гостиная 80-х: ковёр, деревянные панели и обои в полоску,
диван цвета авокадо, горчичное кресло, торшер, полка с видеокассетами, проигрыватель, телефон с диском, пустые
перекошенные рамы, паутина; парящие стул и книги; голубое свечение от экспоната на тумбе под телевизор.
Запуск: blender --background --factory-startup --python scripts/blender/floor_cursedtv.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab, taper, tube  # noqa: E402

SIDING, SIDING2, TRIM, ROOF, ROOF2, FOUND = "6E6A8A", "5E5A78", "D8D4E6", "3A3448", "2E2A3A", "5A5A60"
BRICK, BRICK2, DWOOD, STATIC, STATIC2, LAMP = "8A4A3A", "6E3A2E", "4A3A30", "8FB8FF", "C8DCFF", "FFD27A"
PUMPKIN, PUMPKIN2, NGRASS, BOARD, WEB, NIGHT = "FF8A2A", "D86A1A", "3E5A3A", "8A7A68", "E8E8F0", "1E2448"
CARPET, CARPET2, PANEL, PANEL2, PAPER, PAPER2 = "B86A3A", "8A3A5A", "8A5A3A", "7A4E30", "C8A878", "B08E60"
AVOCADO, AVOCADO2, MUSTARD, CEIL, TAPE, PHONE = "6A8A4A", "5A7A3E", "D8A03A", "D8D0C0", "26262E", "D8352A"

F = B.Floor("CT", "CursedTV", quiet=(CARPET, CARPET2, PAPER, NGRASS), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def window(p, g, axis, fixed, out, a0, a1, y0, y1, lit, boards=False):
    """Окно на стене: белая рама, стекло (светится голубым «снегом» или тёмное), перекрестье или доски."""
    slab(p, axis, fixed, out, 1.35, a0 - 0.3, a1 + 0.3, y0 - 0.3, y1 + 0.3, TRIM)
    if lit:
        slab(g, axis, fixed, out, 1.4, a0, a1, y0, y1, STATIC)
        for k in range(5):  # полосы помех
            y = y0 + (y1 - y0) * (0.12 + 0.19 * k)
            slab(g, axis, fixed, out, 1.42, a0 + (a1 - a0) * rng(k, a0) * 0.4, a1 - (a1 - a0) * rng(a0, k) * 0.3, y, y + 0.14,
                 STATIC2)
    else:
        slab(p, axis, fixed, out, 1.4, a0, a1, y0, y1, NIGHT)
    if boards:
        for k in range(3):
            y = y0 + (y1 - y0) * (0.2 + 0.3 * k)
            slab(p, axis, fixed, out, 1.55, a0 - 0.4, a1 + 0.4, y - 0.25 + 0.1 * k, y + 0.25, BOARD)
    else:
        slab(p, axis, fixed, out, 1.48, (a0 + a1) / 2 - 0.08, (a0 + a1) / 2 + 0.08, y0, y1, TRIM)
        slab(p, axis, fixed, out, 1.48, a0, a1, (y0 + y1) / 2 - 0.08, (y0 + y1) / 2 + 0.08, TRIM)


def antenna(p, x, z, h, ang):
    p.box(x - 0.07, x + 0.07, 17.0, 17.0 + h, z - 0.07, z + 0.07, "8A8A94")
    c, s = math.cos(ang), math.sin(ang)
    for k in range(4):
        L = 1.6 - 0.3 * k
        y = 17.0 + h - 0.25 - 0.45 * k
        beam(p, (x - c * L, y, z - s * L), (x + c * L, y, z + s * L), 0.07, 0.07, "8A8A94")


# ══ ФАСАД: дом с привидениями ═════════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, SIDING2, SIDING2, CEIL)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 8.88 if fi == 0 else 3.88, -half - 3.88, half + 3.88, -1.0, -0.2, NGRASS)  # ночная трава (спереди — двор)
    slab(FR, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, -0.2, 1.4, FOUND)  # каменный цоколь
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.4, 15.4, SIDING2)
    for k in range(14):  # доски сайдинга внахлёст (≥ 0.9 высотой — на квадратах этажа)
        y = 1.45 + 1.0 * k
        slab(FS, axis, fixed, out, 1.0 + 0.06 * (k % 2), -half, half, y, y + 0.96, SIDING if k % 2 else SIDING2)
    for e in (-1, 1):  # белые угловые доски
        slab(FS, axis, fixed, out, 1.2, e * (half - 0.7), e * (half + 1.2), 1.4, 15.4, TRIM)
    slab(FS, axis, fixed, out, 2.3, -half - 2.3, half + 2.3, 15.4, 15.9, TRIM)  # карниз
    B.chamfer(FR, axis, fixed, out, -half - 1.6, half + 1.6, [(0.0, 15.9), (2.2, 15.9), (0.9, 19.0), (0.0, 19.0)], ROOF)
    for k in range(4):  # ряды черепицы
        y = 16.4 + 0.7 * k
        d = 2.2 - 1.3 * (y - 15.9) / 3.1
        slab(FS, axis, fixed, out, d + 0.12, -half - 1.6, half + 1.6, y - 0.12, y, ROOF2)
B.anchor(FR, (-22, -1, -21), (22, 19, 21))
B.anchor(FQ, (-22, -1, -21), (22, 19, 21))
# перед: несимметрично — эркер с «снегом» слева, крыльцо и дверь справа, наверху заколоченное и круглое окно
FS.box(-14.0, -4.0, 1.4, 9.2, -FZ - 2.4, -FZ, SIDING)  # эркер
FS.box(-14.4, -3.6, 9.2, 9.8, -FZ - 2.8, -FZ, TRIM)
FS.loft([(-14.4, 9.8, -FZ - 2.8), (-3.6, 9.8, -FZ - 2.8), (-3.6, 9.8, -FZ), (-14.4, 9.8, -FZ)],
        [(-14.0, 11.0, -FZ - 0.8), (-4.0, 11.0, -FZ - 0.8), (-4.0, 11.0, -FZ), (-14.0, 11.0, -FZ)], ROOF)
window(FS, FG, "z", -FZ - 1.15, -1, -13.0, -5.0, 3.0, 8.4, True)
window(FS, FG, "z", -FZ, -1, -11.0, -7.0, 11.4, 14.4, False, boards=True)  # заколоченное
FS.frame_xy(K.octa(6.0, 12.8, 1.5, 1.5, 0.62), K.octa(6.0, 12.8, 1.1, 1.1, 0.45), -FZ - 1.4, -FZ, TRIM)  # чердачное окно
FS.prism_xy(K.octa(6.0, 12.8, 1.1, 1.1, 0.45), -FZ - 1.2, -FZ, NIGHT)
FS.box(5.94, 6.06, 11.7, 13.9, -FZ - 1.3, -FZ - 1.2, TRIM)
FS.box(2.0, 14.0, -0.2, 1.9, -FZ - 4.6, -FZ, DWOOD)  # крыльцо
for k in range(3):
    FS.box(5.0, 9.0, 0.5 * k - 0.2, 0.5 * k + 0.3, -FZ - 5.8 + 0.4 * k, -FZ - 4.6, DWOOD)
for x in (2.4, 13.6):  # столбики навеса
    FS.box(x - 0.22, x + 0.22, 1.9, 7.6, -FZ - 4.4, -FZ - 3.96, TRIM)
FS.loft([(1.6, 7.6, -FZ - 4.8), (14.4, 7.6, -FZ - 4.8), (14.4, 7.6, -FZ), (1.6, 7.6, -FZ)],
        [(1.6, 9.0, -FZ - 1.0), (14.4, 9.0, -FZ - 1.0), (14.4, 9.0, -FZ), (1.6, 9.0, -FZ)], ROOF2)
FS.box(5.0, 9.0, 1.9, 7.0, -FZ - 1.3, -FZ, TRIM)  # дверь
FS.box(5.4, 8.6, 1.9, 6.6, -FZ - 1.45, -FZ - 1.3, "5A2E3A")
FS.box(5.6, 8.4, 4.6, 6.4, -FZ - 1.5, -FZ - 1.45, "3A1E28")
FS.prism_xz(K.octa(8.1, -FZ - 1.55, 0.12, 0.12, 0.05), 3.9, 4.1, LAMP)
FS.box(10.6, 11.4, 5.8, 6.6, -FZ - 1.5, -FZ - 1.2, DWOOD)  # фонарь у двери
FG.box(10.7, 11.3, 5.9, 6.5, -FZ - 1.6, -FZ - 1.5, LAMP)
window(FS, FG, "z", -FZ, -1, 10.6, 13.4, 2.8, 5.2, False)
# штакетник с калиткой, почтовый ящик, тыквы без лиц, сухое дерево
for k in range(27):
    x = -17.0 + 1.3 * k
    if 4.4 < x < 9.6 or rng(k, 31) < 0.12:
        continue
    lean = (rng(k, 32) - 0.5) * 0.8
    FS.loft([(x - 0.25, -0.2, -FZ - 6.6), (x + 0.25, -0.2, -FZ - 6.6), (x + 0.25, -0.2, -FZ - 6.4), (x - 0.25, -0.2, -FZ - 6.4)],
            [(x - 0.25 + lean, 2.6, -FZ - 6.6), (x + 0.25 + lean, 2.6, -FZ - 6.6), (x + 0.25 + lean, 2.6, -FZ - 6.4),
             (x - 0.25 + lean, 2.6, -FZ - 6.4)], TRIM)
for y in (0.8, 2.0):
    FS.box(-17.2, 4.4, y, y + 0.22, -FZ - 6.7, -FZ - 6.62, TRIM)
    FS.box(9.6, 17.2, y, y + 0.22, -FZ - 6.7, -FZ - 6.62, TRIM)
FS.box(15.6, 15.8, -0.2, 2.6, -FZ - 7.4, -FZ - 7.2, DWOOD)  # почтовый ящик
FS.box(15.1, 16.3, 2.6, 3.4, -FZ - 7.9, -FZ - 6.7, "3060A0")
FS.box(16.3, 16.4, 2.9, 3.8, -FZ - 7.5, -FZ - 7.3, PHONE)
for x, z, r in ((4.6, -FZ - 5.4, 0.7), (9.6, -FZ - 5.6, 0.55), (13.0, -FZ - 4.2, 0.6)):
    FS.prism_xz(K.octa(x, z, r, r, r * 0.4), 1.9 if z > -FZ - 4.6 else 0.0, (1.9 if z > -FZ - 4.6 else 0.0) + r * 1.2,
                PUMPKIN)
    FS.box(x - 0.08, x + 0.08, (1.9 if z > -FZ - 4.6 else 0.0) + r * 1.2, (1.9 if z > -FZ - 4.6 else 0.0) + r * 1.2 + 0.3,
           z - 0.08, z + 0.08, "4A6A2A")
tree = [(-17.0, -0.2, -FZ - 5.0), (-16.6, 5.0, -FZ - 5.2), (-15.6, 10.0, -FZ - 5.0), (-14.6, 14.0, -FZ - 4.6)]
tube(FS, tree, [1.2, 0.95, 0.7, 0.4], 1.0, (0, 0, 1), "2E2622")
for a, b in (((-16.6, 6.0, -FZ - 5.2), (-19.6, 9.0, -FZ - 5.4)), ((-15.8, 9.5, -FZ - 5.0), (-12.4, 12.6, -FZ - 5.6)),
             ((-15.0, 12.6, -FZ - 4.8), (-17.4, 15.8, -FZ - 4.4)), ((-12.4, 12.6, -FZ - 5.6), (-11.2, 14.6, -FZ - 5.8))):
    taper(FS, a, b, 0.45, 0.1, "2E2622")
for a, b in (((-FX - 1.2, 15.4, -FZ - 1.2), (-FX + 1.4, 12.6, -FZ - 1.2)), ((FX + 1.2, 15.4, -FZ - 1.2),
                                                                           (FX - 1.6, 13.0, -FZ - 1.2))):
    beam(FS, a, b, 0.05, 0.05, WEB)  # паутина в углах
# крыша: телеантенны
for x, z, h, ang in ((-10.0, -FZ + 0.6, 1.7, 0.3), (-2.0, -FZ + 0.6, 1.5, -0.15), (7.0, -FZ + 0.6, 1.8, 0.15), (14.0, -FZ + 0.6, 1.4, -0.15)):
    antenna(FS, x, z, h, ang)
# бока: кирпичная труба слева, окна со ставнями (одно со «снегом»), мусорные баки
FS.box(-FX - 2.6, -FX, -0.2, 18.9, -4.0, 0.0, BRICK)
for k in range(12):
    FS.box(-FX - 2.7, -FX - 2.6, 1.0 + 1.5 * k, 1.15 + 1.5 * k, -4.0, 0.0, BRICK2)
FS.box(-FX - 2.9, -FX - 0.2, 18.0, 18.9, -4.3, 0.3, BRICK2)
for s in (-1, 1):
    fx = s * FX
    for k, z in enumerate((-10.0, 7.0)):
        lit = s > 0 and k == 0
        window(FS, FG, "x", fx, s, z - 1.6, z + 1.6, 4.0 + 6.0 * k, 7.6 + 6.0 * k, lit)
        for e in (-1, 1):  # перекошенные ставни
            lean = 0.4 if (s + k + e) % 2 else -0.25
            FS.loft([(fx + s * 1.4, 4.0 + 6.0 * k, z + e * 2.2 - 0.6), (fx + s * 1.4, 4.0 + 6.0 * k, z + e * 2.2 + 0.6),
                     (fx + s * 1.55, 4.0 + 6.0 * k, z + e * 2.2 + 0.6), (fx + s * 1.55, 4.0 + 6.0 * k, z + e * 2.2 - 0.6)],
                    [(fx + s * 1.4, 7.6 + 6.0 * k, z + e * 2.2 - 0.6 + lean), (fx + s * 1.4, 7.6 + 6.0 * k, z + e * 2.2 + 0.6 + lean),
                     (fx + s * 1.55, 7.6 + 6.0 * k, z + e * 2.2 + 0.6 + lean),
                     (fx + s * 1.55, 7.6 + 6.0 * k, z + e * 2.2 - 0.6 + lean)], "3A4A5A")
    for k in range(2):
        z = 11.0 + 2.0 * k
        FS.prism_xz(K.octa(fx + s * 3.0, z, 0.8, 0.8, 0.32), -0.2, 2.0, "6A6E74")
        FS.prism_xz(K.octa(fx + s * 3.0, z, 0.9, 0.9, 0.36), 2.0, 2.3, "7A7E84")
# тыл: гора старых телевизоров
for k, (x, y, w) in enumerate(((-6.0, -0.2, 2.2), (-2.0, -0.2, 2.6), (2.4, -0.2, 2.2), (-4.0, 2.2, 2.0), (0.4, 2.4, 2.2),
                               (-1.6, 4.6, 1.8))):
    FS.box(x - w / 2, x + w / 2, y, y + w * 0.85 + 0.2, FZ + 0.2, FZ + 2.8, ("7A5A3A", "5A5A60", "8A7A6A")[k % 3])
    FG.box(x - w / 2 + 0.3, x + w / 2 - 0.3, y + 0.35, y + w * 0.85 - 0.15, FZ + 2.8, FZ + 2.85,
           STATIC if k % 2 else "6A8AB0")

# ══ ИНТЕРЬЕР: гостиная 80-х ═══════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -4.0)
TOP = 1.4
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), CARPET)
IQ.box(-9.0, 9.0, 0.02, 0.08, -10.0, 4.0, CARPET2)  # ковёр
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        n = max(1, int((a1 - a0) // 1.5))
        for k in range(n):  # деревянные панели до пояса
            b0, b1 = a0 + (a1 - a0) * k / n, a0 + (a1 - a0) * (k + 1) / n
            slab(IR, axis, fixed, out, 0.88, b0 + 0.04, b1 - 0.04, 0.0, 5.0, PANEL if k % 2 else PANEL2)
        slab(IS, axis, fixed, out, 1.05, a0, a1, 5.0, 5.4, PANEL2)
    slab(IQ, axis, fixed, out, 0.7, -half, half, 0.0, C, PAPER)
    for k in range(int(2 * half // 1.6)):  # полоски обоев
        a = -half + 0.8 + 1.6 * k
        if gap and abs(a) < DOOR[0] + 0.6:
            continue
        slab(IS, axis, fixed, out, 0.75, a - 0.25, a + 0.25, 5.4, C - 0.6, PAPER2)
    slab(IS, axis, fixed, out, 0.95, -half, half, C - 0.6, C, TRIM)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 12.0, PANEL2)
# окна на передней стене: ночь, луна, шторы
for k, x in enumerate((-10.0, 10.0)):
    IS.box(x - 3.0, x + 3.0, 6.0, 13.0, ZF + 0.8, ZF + 1.2, TRIM)
    IS.box(x - 2.6, x + 2.6, 6.4, 12.6, ZF + 1.2, ZF + 1.25, NIGHT)
    IS.box(x - 0.08, x + 0.08, 6.4, 12.6, ZF + 1.25, ZF + 1.35, TRIM)
    for e in (-1, 1):
        IS.box(x + e * 3.0 - 0.9, x + e * 3.0 + 0.9, 5.4, 14.0, ZF + 1.3, ZF + 1.8, CARPET2)
IG.prism_xy(K.octa(11.2, 11.0, 0.8, 0.8, 0.33), ZF + 1.25, ZF + 1.28, "F4F0D8")  # луна (одна, в правом окне)
# мебель: диван, кресло, столик, торшер, полка с кассетами, проигрыватель, телефон
IS.box(-14.6, -10.6, 0.0, 1.6, -9.0, 1.0, AVOCADO)  # диван лицом к экспонату
IS.box(-16.2, -14.6, 0.0, 3.6, -9.0, 1.0, AVOCADO2)
for z0, z1 in ((-9.0, -8.0), (0.0, 1.0)):
    IS.box(-16.2, -10.6, 1.6, 2.6, z0, z1, AVOCADO2)
for k in range(3):
    IS.box(-14.4, -11.0, 1.6, 2.2, -7.8 + 2.7 * k, -5.4 + 2.7 * k, AVOCADO)
IS.box(10.6, 14.2, 0.0, 1.8, 2.0, 5.6, MUSTARD)  # кресло
IS.box(14.2, 15.4, 0.0, 4.0, 2.0, 5.6, "B8862A")
for z0, z1 in ((2.0, 2.8), (4.8, 5.6)):
    IS.box(10.6, 15.4, 1.8, 2.8, z0, z1, "B8862A")
IS.box(-9.0, -6.6, 1.2, 1.4, -6.0, -2.0, PANEL)  # столик
for x in (-8.8, -6.8):
    for z in (-5.8, -2.2):
        IS.box(x - 0.1, x + 0.1, 0.0, 1.2, z - 0.1, z + 0.1, PANEL2)
IS.box(-8.4, -7.4, 1.4, 1.6, -4.6, -3.4, PHONE)
IS.box(13.6, 13.8, 0.0, 6.4, 8.6, 8.8, "B8A070")  # торшер
IS.prism_xz(K.octa(13.7, 8.7, 0.9, 0.9, 0.36), 6.4, 7.6, "F0E0B0")
IG.prism_xz(K.octa(13.7, 8.7, 0.6, 0.6, 0.25), 6.2, 6.4, LAMP)
IS.box(W - 1.4, W, 0.0, 9.0, -12.0, -6.0, PANEL2)  # полка с кассетами
for r in range(4):
    IS.box(W - 1.4, W, 1.9 + 2.2 * r, 2.1 + 2.2 * r, -12.0, -6.0, PANEL)
    for k in range(8):
        IS.box(W - 1.3, W - 0.3, 2.1 + 2.2 * r, 3.5 + 2.2 * r, -11.8 + 0.7 * k, -11.3 + 0.7 * k, TAPE)
        IS.box(W - 1.35, W - 1.3, 2.4 + 2.2 * r, 3.0 + 2.2 * r, -11.7 + 0.7 * k, -11.4 + 0.7 * k,
               ("E04A6A", "4AB0E0", "E0C84A", "6ACB5A")[(k + r) % 4])
IS.box(-W, -W + 1.6, 0.0, 2.6, 6.0, 10.0, PANEL2)  # проигрыватель-тумба
IS.box(-W + 0.2, -W + 1.4, 2.6, 2.7, 6.4, 9.6, "3A3A40")
IS.prism_xz(K.octa(-W + 0.8, 8.0, 0.6, 0.6, 0.25), 2.7, 2.8, TAPE)
# пустые перекошенные рамы, паутина
for x, y, w, h, t in ((-5.0, 8.6, 1.6, 2.2, 0.12), (4.6, 9.2, 2.0, 1.6, -0.15)):
    c, s_ = math.cos(t), math.sin(t)
    outer = [(x + u * c - v * s_, y + u * s_ + v * c) for u, v in ((-w, -h), (w, -h), (w, h), (-w, h))]
    inner = [(x + u * c - v * s_, y + u * s_ + v * c) for u, v in ((-w + 0.35, -h + 0.35), (w - 0.35, -h + 0.35),
                                                                     (w - 0.35, h - 0.35), (-w + 0.35, h - 0.35))]
    IS.frame_xy(outer, inner, ZF + 0.8, ZF + 1.0, MUSTARD)
for a, b in (((-W, C - 0.8, ZF + 2.4), (-W + 2.4, C - 0.6, ZF)), ((W, C - 0.8, ZF + 2.0), (W - 2.0, C - 0.6, ZF)),
             ((-W + 1.2, C - 0.7, ZF + 1.2), (-W + 0.2, C - 2.2, ZF + 0.2))):
    beam(IS, a, b, 0.05, 0.05, WEB)
# парящие предметы: стул и книги
IS.loft([(5.0, 4.2, -9.6), (6.6, 4.5, -9.6), (6.6, 4.5, -8.0), (5.0, 4.2, -8.0)],
        [(5.0, 4.5, -9.6), (6.6, 4.8, -9.6), (6.6, 4.8, -8.0), (5.0, 4.5, -8.0)], PANEL)
for x, z in ((5.1, -9.5), (6.5, -9.5), (5.1, -8.1), (6.5, -8.1)):
    IS.box(x - 0.08, x + 0.08, 2.6, 4.2, z - 0.08, z + 0.08, PANEL2)
IS.box(5.0, 6.6, 4.5, 6.8, -9.6, -9.4, PANEL)
for k in range(4):
    x, y, z = -4.0 + 1.6 * k, 6.0 + 0.8 * math.sin(k), -10.0 + 0.6 * k
    IS.box(x - 0.6, x + 0.6, y, y + 0.25, z - 0.45, z + 0.45, ("C2463A", "3A6AB0", "E8B84A", "5A8A4A")[k])
# тумба под телевизор и голубое свечение
px, pz = PED
IR.box(px - 4.0, px + 4.0, 0.0, 0.7, pz - 3.4, pz + 3.4, PANEL2)
IR.box(px - 3.4, px + 3.4, 0.7, TOP, pz - 2.8, pz + 2.8, PANEL)
IS.box(px - 3.0, px + 3.0, 0.15, 0.55, pz + 3.4, pz + 3.45, TAPE)
for k, r in enumerate((4.6, 5.6)):  # голубое свечение по ковру вокруг тумбы
    IG.frame_xz(K.octa(px, pz, r + 0.25, r - 0.2, 1.6), K.octa(px, pz, r, r - 0.45, 1.5), 0.08 + 0.01 * k, 0.11 + 0.01 * k,
                "7AA0E0" if k == 0 else "5A78B8")
IG.box(-0.8, 0.8, C - 0.12, C - 0.06, -0.8, 0.8, "F4F0E0")  # плафон
B.lift_leaves(IS, PANEL2, MUSTARD)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, SIDING)
SL.box(-FX - 1.9, FX + 1.9, -1.0, 1.4, -FZ - 1.9, FZ + 1.9, FOUND)
SL.box(-FX - 1.9, FX + 1.9, 15.4, 17.4, -FZ - 1.9, FZ + 1.9, ROOF)
SL.box(-14.0, -4.0, 1.4, 9.8, -FZ - 2.6, -FZ, STATIC)
SL.box(2.0, 14.0, 1.4, 9.0, -FZ - 4.6, -FZ, ROOF2)
SL.box(-FX - 2.6, -FX, -0.2, 18.9, -4.0, 0.0, BRICK)
SL.box(-17.5, -14.0, -0.2, 14.0, -FZ - 5.6, -FZ - 4.4, "2E2622")

F.build(exhibit=(PED[0], TOP, PED[1], 2.8), lamps=[("Hall", (0, 14, 6), 2200, (0.85, 0.85, 1.0)),
                                                   ("Spot", (0, 13, -4), 3000, (0.85, 0.92, 1.0))])
