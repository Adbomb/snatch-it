"""Этаж «Царь-смерч» музея-небоскрёба (десятая партия, 2026-11-22; общий конвейер — floorbase.py, floorshell.py).

Замысел: этаж — персидский дворец ветров. Снаружи — песочная кирпичная стена с бирюзово-синими изразцовыми
поясами, высокий айван (стрельчатый портал) в изразцовой раме с «сталактитами»-мукарнами в своде и спиралью
вихря над дверью, по углам — две башни-ветроловки (бадгиры) с решётками продухов и зубцами, решётки-джали на
окнах, перед дворцом — длинный бассейн с фонтанчиками, кипарисы, изразцовые вазоны. Внутри — тронный зал ветров:
изразцовые стены с решётками-джали, потолок со спиральным узором вихря, колонны с бирюзовыми капителями,
ковры, музыка ветра (трубочки на нитях), фонари, боковые фонтаны-чаши; экспонат — на трёхъярусном круглом
помосте со спиральной инкрустацией.
Запуск: blender --background --factory-startup --python scripts/blender/floor_windpalace.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
import floorshell as S  # noqa: E402
from floorbase import C, FX, FZ, W, ZB, ZF, beam, rng, slab, taper  # noqa: E402

BRICK, BRICK2, TURQ, TURQ2, COBALT, WHITE = "D8B888", "B8966A", "3AC0C8", "2A98A8", "2A4AB0", "F2EEE4"
GOLD, CYPRESS, WATER, RUG, RUG2, PURPLE = "E8B840", "2E6A3A", "4AB8E8", "B83A3A", "2A3A8A", "6A4AB0"
GLASS = "F8E8C0"

F = B.Floor("TK", "TornadoKing", quiet=(BRICK2, "C8B490", "2A6A78"), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def pointed(cx, y0, w, h, n=6):
    """Контур стрельчатой арки шириной w и высотой h: две дуги радиуса w, сходящиеся в вершине."""
    r = w
    ys = y0 + h - r * math.sin(math.pi / 3)
    pts = [(cx - w / 2, y0)]
    for k in range(n + 1):  # левая дуга, центр справа
        a = math.pi - (math.pi / 3) * k / n
        pts.append((cx + w / 2 + r * math.cos(a), ys + r * math.sin(a)))
    for k in range(1, n + 1):  # правая дуга, центр слева
        a = math.pi / 3 - (math.pi / 3) * k / n
        pts.append((cx - w / 2 + r * math.cos(a), ys + r * math.sin(a)))
    pts.append((cx + w / 2, y0))
    return pts


def spiral(p, cx, cy, z, r, turns, col, w=0.22, axis="z"):
    """Спираль вихря брусками."""
    n = int(18 * turns)
    pts = []
    for k in range(n + 1):
        t = k / n
        a = 2 * math.pi * turns * t
        rr = r * t
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    for a, b in zip(pts, pts[1:]):
        if axis == "z":
            beam(p, (a[0], a[1], z), (b[0], b[1], z), w, 0.1, col, up=(0, 0, 1))
        else:
            beam(p, (a[0], z, a[1]), (b[0], z, b[1]), w, 0.08, col)


def cypress(p, x, z, y, h):
    p.prism_xz(K.ngon(x, z, 0.2, 6), y, y + 0.8, "6A4A2A")
    for k in range(3):
        y0 = y + 0.6 + h * k / 3 * 0.8
        p.cone([(a, y0, b) for a, b in K.ngon(x, z, 1.0 - 0.25 * k, 8)], (x, y0 + h * 0.45, z), CYPRESS)


# ══ ФАСАД ══════════════════════════════════════════════════════════════════════════════════════════════════════
S.facade(F, BRICK, BRICK2, TURQ, "C8B490", "1E3A6A", roof="crenel", roof_col=BRICK, top=16.0,
         band=(12.6, 13.4, TURQ2), side=S.side_windows(F, TURQ2, GLASS, kind="arch", y0=7.0, y1=11.6, w=2.0, xs=(-13.0, -7.0, -1.0, 5.0, 11.0)))
for fi, (axis, fixed, out, half) in enumerate(B.FACES):  # изразцовый пояс шашкой
    for k in range(int(2 * half // 1.0)):
        a = -half + 1.0 * k
        slab(FS, axis, fixed, out, 1.0, a, a + 1.0, 14.0, 15.0, COBALT if k % 2 else WHITE)
# айван: изразцовая рама, стрельчатый портал, мукарны, спираль вихря
FR.box(-6.4, 6.4, 1.0, 17.0, -FZ - 1.6, -FZ - 0.88, TURQ)
FR.box(-5.6, 5.6, 1.0, 16.2, -FZ - 1.7, -FZ - 1.6, COBALT)
arch = pointed(0.0, 1.0, 8.4, 13.4, n=6)
FS.prism_xy(arch, -FZ - 1.76, -FZ - 1.7, "1E2A5A")
for j in range(4):  # мукарны: ряды ступенчатых ниш в своде
    y = 10.6 + 0.9 * j
    n = 7 - j
    for k in range(n):
        x = -2.4 + 4.8 * (k + 0.5) / n
        FS.box(x - 0.28, x + 0.28, y, y + 0.7, -FZ - 1.76 - 0.2 * (4 - j), -FZ - 1.76, (TURQ, WHITE, GOLD)[(j + k) % 3])
FS.box(-2.8, 2.8, 1.0, 9.2, -FZ - 1.82, -FZ - 1.76, "6A3A1E")
FS.prism_xy(pointed(0.0, 1.0, 5.6, 8.8, n=4), -FZ - 1.86, -FZ - 1.82, "8A4A22")
for k in range(3):
    FS.box(-2.4 + 0.1, 2.4 - 0.1, 2.0 + 2.2 * k, 2.12 + 2.2 * k, -FZ - 1.9, -FZ - 1.86, GOLD)
spiral(FS, 0.0, 5.6, -FZ - 1.95, 1.3, 2.0, TURQ, w=0.16)
# окна с решётками-джали по бокам от айвана
for x in (-12.4, 9.0):
    FS.prism_xy(pointed(x + 1.7, 4.0, 3.4, 7.2, n=4), -FZ - 0.94, -FZ - 0.88, "2A3A6A")
    for j in range(5):
        for k in range(3):
            FS.prism_xy(K.ngon(x + 0.7 + 1.0 * k, 5.0 + 1.1 * j, 0.32, 6), -FZ - 1.0, -FZ - 0.94, (WHITE, TURQ)[(j + k) % 2])
# башни-ветроловки по углам
for x in (-FX - 0.6, FX + 0.6):
    TZ = -FZ - 1.3
    FR.box(x - 1.4, x + 1.4, -0.1, 17.6, TZ - 1.4, TZ + 1.2, BRICK)
    for k in range(4):
        FS.box(x - 1.0 + 0.55 * k, x - 0.7 + 0.55 * k, 12.4, 16.6, TZ - 1.46, TZ - 1.4, "2A2A3A")
    FS.box(x - 1.5, x + 1.5, 11.8, 12.2, TZ - 1.5, TZ + 1.3, TURQ)
    FS.box(x - 1.5, x + 1.5, 16.8, 17.2, TZ - 1.5, TZ + 1.3, TURQ)
    for e in (-1, 1):
        FS.box(x + e * 1.1 - 0.3, x + e * 1.1 + 0.3, 17.6, 18.6, TZ - 1.4, TZ - 0.8, BRICK2)
    for j in range(3):
        FS.box(x - 1.46, x + 1.46, 3.0 + 3.0 * j, 3.6 + 3.0 * j, TZ - 1.46, TZ - 1.4, COBALT)
# бассейн с фонтанчиками, кипарисы, вазоны
FR.box(-9.0, 9.0, -0.1, 0.4, -FZ - 2.9, -FZ - 1.9, TURQ2)
FG.box(-8.6, 8.6, 0.25, 0.42, -FZ - 2.7, -FZ - 2.1, WATER)
for k in range(5):
    x = -7.0 + 3.5 * k
    if abs(x) > 0.1:
        FS.prism_xz(K.ngon(x, -FZ - 2.4, 0.12, 6), 0.4, 0.6, GOLD)
        FG.prism_xz(K.ngon(x, -FZ - 2.4, 0.06, 6), 0.6, 1.8, "B8ECFF")
F.objects(True)
for x in (-14.0, -10.6, 10.6, 14.0):
    FS.prism_xz(K.ngon(x, -FZ - 2.2, 0.8, 8), -0.1, 0.9, COBALT)
    cypress(FS, x, -FZ - 2.2, 0.9, 7.0 if abs(x) > 12 else 5.4)
F.objects(False)

# ══ ИНТЕРЬЕР: тронный зал ветров ══════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.8
S.interior(F, "E8DCC4", "C8B490", "1E2A5A", TURQ2, wain=(3.4, TURQ), beams=None, cornice=GOLD)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS[:3]):  # изразцовая шашка под панелью и решётки-джали
    for k in range(int(2 * half // 1.2)):
        a = -half + 1.2 * k
        slab(IS, axis, fixed, out, 1.15, a, a + 1.2, 3.4, 4.0, COBALT if k % 2 else WHITE)
    for a in ((-10.0, -2.0, 6.0) if idx < 2 else (-10.0, 6.0)):
        for j in range(4):
            for k in range(3):
                d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.96))
                if axis == "x":
                    IS.prism_zy(K.ngon(a + 0.6 + 1.0 * k, 6.4 + 1.2 * j, 0.36, 6), d0, d1, (TURQ, WHITE)[(j + k) % 2])
                else:
                    IS.prism_xy(K.ngon(a + 0.6 + 1.0 * k, 6.4 + 1.2 * j, 0.36, 6), d0, d1, (TURQ, WHITE)[(j + k) % 2])
for k in range(3):  # потолок: спираль вихря
    spiral(IS, 0.0, -3.0, C - 0.1 - 0.05 * k, 11.0, 2.2, (TURQ, GOLD, WHITE)[k], w=0.5 - 0.1 * k, axis="y")
F.objects(True)
for x in (-10.0, 10.0):  # колонны с бирюзовыми капителями
    for z in (-11.0, 4.0):
        IR.prism_xz(K.ngon(x, z, 0.9, 10), 0.0, 0.6, BRICK2)
        IS.prism_xz(K.ngon(x, z, 0.6, 10), 0.6, 12.4, WHITE)
        IS.loft([(x + 0.6 * math.cos(a), 12.4, z + 0.6 * math.sin(a)) for a in [2 * math.pi * k / 10 for k in range(10)]],
                [(x + 1.3 * math.cos(a), 14.2, z + 1.3 * math.sin(a)) for a in [2 * math.pi * k / 10 for k in range(10)]], TURQ)
        IS.prism_xz(K.ngon(x, z, 1.4, 10), 14.2, 14.6, GOLD)
# ковры, боковые фонтаны-чаши, музыка ветра, фонари
for x in (-6.0, 6.0):
    IQ.box(x - 2.2, x + 2.2, 0.02, 0.06, -12.0, 6.0, RUG if x < 0 else RUG2)
    IQ.box(x - 1.8, x + 1.8, 0.06, 0.08, -11.6, 5.6, GOLD)
    IQ.box(x - 1.5, x + 1.5, 0.08, 0.1, -11.3, 5.3, RUG2 if x < 0 else RUG)
for s in (-1, 1):
    x = s * (W - 2.6)
    IR.prism_xz(K.ngon(x, -3.0, 1.8, 12), 0.0, 1.2, WHITE)
    IG.prism_xz(K.ngon(x, -3.0, 1.5, 12), 0.9, 1.15, WATER)
    IS.prism_xz(K.ngon(x, -3.0, 0.3, 8), 1.0, 2.6, GOLD)
for k, (x, z) in enumerate(((-4.0, -10.0), (4.0, -10.0), (-4.0, 4.0), (4.0, 4.0))):
    IS.box(x - 0.03, x + 0.03, 14.0, C - 0.4, z - 0.03, z + 0.03, "6A6A70")  # высоко: не заслоняет экспонат
    IS.prism_xz(K.ngon(x, z, 0.7, 8), 13.8, 14.0, GOLD)
    for j in range(6):
        a = 2 * math.pi * j / 6
        IS.prism_xz(K.ngon(x + 0.55 * math.cos(a), z + 0.55 * math.sin(a), 0.08, 6), 11.6 + 0.3 * (j % 3), 13.8, (WHITE, TURQ, GOLD)[j % 3])
F.objects(False)
for x, z in ((-8.0, -6.0), (8.0, -6.0), (0.0, -13.0)):
    IS.box(x - 0.03, x + 0.03, C - 3.0, C - 0.6, z - 0.03, z + 0.03, "6A6A70")
    D.lantern(IS, IG, x, C - 4.0, z, s=1.2, cap=GOLD, light="FFE0A0")
# постамент: трёхъярусный круглый помост со спиральной инкрустацией
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.4, 16), 0.0, 0.6, BRICK2)
IR.prism_xz(K.ngon(px, pz, 3.8, 16), 0.6, 1.2, TURQ)
IR.prism_xz(K.ngon(px, pz, 3.2, 16), 1.2, TOP, WHITE)
spiral(IS, px, pz, TOP + 0.02, 3.0, 1.6, COBALT, w=0.3, axis="y")
for k in range(16):
    a = 2 * math.pi * (k + 0.5) / 16
    IS.box(px + 3.82 * math.cos(a) - 0.12, px + 3.82 * math.cos(a) + 0.12, 0.7, 1.1, pz + 3.82 * math.sin(a) - 0.12,
           pz + 3.82 * math.sin(a) + 0.12, GOLD)
B.lift_leaves(IS, COBALT, GOLD)

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
S.silhouette(F, BRICK, "C8B490", BRICK, top=16.0)
for x in (-FX - 0.6, FX + 0.6):
    SL.box(x - 1.4, x + 1.4, -0.1, 18.6, -FZ - 2.7, -FZ - 0.1, BRICK)
SL.box(-6.4, 6.4, 1.0, 17.0, -FZ - 1.6, -FZ, TURQ)

F.build(mlf=1, tol=0.16, exhibit=(PED[0], TOP, PED[1], 2.3), lamps=[("Hall", (0, 14, 6), 1800, (1.0, 0.95, 0.88)),
                                                   ("Spot", (0, 13, -3), 3800, (1.0, 0.97, 0.92)),
                                                   ("Tile", (0, 8, -12), 700, (0.6, 0.85, 1.0))])
