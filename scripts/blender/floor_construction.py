"""Этаж «Конус-паникёр» музея-небоскрёба (пятая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — стройка, которую охраняют конусы. Снаружи — недостроенный дом: бетонный каркас с рядами
кладки, по фасаду — леса из жёлтых труб с дощатыми настилами и оранжевой сеткой, на крыше — башенный кран-малыш
со стрелой и крюком, на крюке — поддон с конусами, у фасада — бетонные блоки-ограждения в красно-белую полосу,
мигалки, конусы, тачка, бетономешалка; бока — леса и штабеля кирпича; сзади — кучи песка и трубы. Внутри —
голый каркас: бетонный пол с меловой разметкой, жёлтые двутавровые колонны и балки, вышка-тура лесов, поддоны
кирпича, мешки цемента, каски, ящик с инструментами, прожекторы на треногах, лампы на проводах, лента «осторожно»;
экспонат — на стопке поддонов с жёлто-чёрной кромкой и конусами по углам.
Запуск: blender --background --factory-startup --python scripts/blender/floor_construction.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab  # noqa: E402

CON, CON2, CON3, BRICK, BRICK2, SAND, SAND2 = "B8B4AC", "9C988E", "CFCBC2", "C0603E", "A04E32", "E0C080", "C8A868"
YEL, YEL2, ORANGE, ORANGE2, RED, WHITE, BLACK = "FFC21A", "E0A010", "FF6A1A", "D8540E", "E0302A", "F4F4F0", "2A2A2E"
WOOD, WOOD2, STEEL, STEEL2, NET, BLUE = "C89A5A", "9E7440", "C0C4CC", "7A808A", "FF8A3A", "2A6AD8"

F = B.Floor("PC", "PanicCone", quiet=(CON2, SAND2, BLACK), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def cone(p, x, z, y=0.0, h=1.6):
    """Дорожный конус: основание, конус, две светоотражающие полосы."""
    p.box(x - 0.6, x + 0.6, y, y + 0.16, z - 0.6, z + 0.6, ORANGE2)
    p.cone([(x + 0.45 * math.cos(t), y + 0.16, z + 0.45 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]], (x, y + h, z),
           ORANGE)
    for f, rr in ((0.38, 0.3), (0.62, 0.2)):
        p.prism_xz(K.ngon(x, z, rr, 8), y + h * f, y + h * f + 0.14, WHITE)


def scaffold(p, axis, fixed, out, a0, a1, y_levels, depth=2.2):
    """Леса у стены: стойки, ригели, диагонали, дощатые настилы, бортовые доски."""
    def P(a, y, d):
        return (a, y, fixed + out * d) if axis == "z" else (fixed + out * d, y, a)

    n = int((a1 - a0) // 3.0)
    xs = [a0 + (a1 - a0) * k / n for k in range(n + 1)]
    top = y_levels[-1] + 1.4
    for a in xs:
        for d in (0.6, depth):
            beam(p, P(a, -0.1, d), P(a, top, d), 0.16, 0.16, YEL)
    for y in y_levels:
        for d in (0.6, depth):
            beam(p, P(a0, y + 1.0, d), P(a1, y + 1.0, d), 0.14, 0.14, YEL)
        slab(p, axis, fixed, out, depth + 0.15, a0, a1, y - 0.12, y, WOOD)
        slab(p, axis, fixed, out, depth + 0.2, a0, a1, y, y + 0.35, WOOD2, back=-(depth - 0.05))
    for k in range(n):  # диагонали ярусами
        j = k % len(y_levels)
        lo = y_levels[j - 1] if j else 0.0
        beam(p, P(xs[k], lo, depth), P(xs[k + 1], y_levels[j], depth), 0.1, 0.1, YEL2)


def barrier(p, x, z, along_x=True, L=3.0):
    """Бетонный блок-ограждение в красно-белую полосу (сечение «нью-джерси»)."""
    prof = [(-0.6, 0.0), (0.6, 0.0), (0.45, 0.3), (0.22, 0.6), (0.22, 1.1), (-0.22, 1.1), (-0.22, 0.6), (-0.45, 0.3)]
    n = 4
    for k in range(n):
        u0, u1 = -L / 2 + L * k / n, -L / 2 + L * (k + 1) / n
        col = (RED, WHITE)[k % 2]
        if along_x:
            p.prism_zy([(z + u, v) for u, v in prof], x + u0, x + u1, col)
        else:
            p.prism_xy([(x + u, v) for u, v in prof], z + u0, z + u1, col)


def pallet(p, x, z, y=0.0, a=2.4, b=2.4):
    """Поддон: три бруска и настил из досок."""
    for e in (-1, 0, 1):
        p.box(x - a / 2, x + a / 2, y, y + 0.25, z + e * (b / 2 - 0.2) - 0.18, z + e * (b / 2 - 0.2) + 0.18, WOOD2)
    for k in range(5):
        xx = x - a / 2 + a * (k + 0.5) / 5
        p.box(xx - a * 0.08, xx + a * 0.08, y + 0.25, y + 0.38, z - b / 2, z + b / 2, WOOD)


def brick_stack(p, x, z, y=0.0, layers=4):
    """Поддон с кирпичом, перевязанным лентой."""
    pallet(p, x, z, y)
    for k in range(layers):
        p.box(x - 1.1, x + 1.1, y + 0.38 + 0.4 * k, y + 0.78 + 0.4 * k, z - 1.1, z + 1.1, (BRICK, BRICK2)[k % 2])
    p.box(x - 1.14, x + 1.14, y + 0.38, y + 0.38 + 0.4 * layers, z - 0.08, z + 0.08, BLUE)


def hard_hat(p, x, z, y, col=YEL):
    """Каска: купол из ярусов, козырёк."""
    p.prism_xz(K.ngon(x, z, 0.62, 10), y, y + 0.1, col)
    p.prism_xz(K.ngon(x, z, 0.46, 10), y + 0.1, y + 0.45, col)
    p.prism_xz(K.ngon(x, z, 0.28, 8), y + 0.45, y + 0.6, col)


def floodlight(p, g, x, z, h, face):
    """Прожектор на треноге, светит в сторону face (угол по y)."""
    for k in range(3):
        t = 2 * math.pi * k / 3
        beam(p, (x + 0.9 * math.cos(t), 0.0, z + 0.9 * math.sin(t)), (x, h, z), 0.1, 0.1, BLACK)
    c, s = math.cos(face), math.sin(face)
    p.box(x - 0.6, x + 0.6, h, h + 1.0, z - 0.6, z + 0.6, BLACK)
    g.box(x + c * 0.62 - 0.45 * abs(s), x + c * 0.66 + 0.45 * abs(s), h + 0.15, h + 0.85, z + s * 0.62 - 0.45 * abs(c),
          z + s * 0.66 + 0.45 * abs(c), "FFF6C8")


# ══ ФАСАД: недостроенный дом в лесах ══════════════════════════════════════════════════════════════════════════
B.shell_planes(F, CON, CON, CON2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, SAND2)
    slab(FR, axis, fixed, out, 1.38, -half - 0.3, half + 0.3, -0.1, 0.8, CON2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 0.8, 18.9, CON)
    for k in range(int(2 * half // 6.0) + 1):  # бетонный каркас: колонны и плиты перекрытий
        a = -half + 6.0 * k
        slab(FR, axis, fixed, out, 1.2, max(a - 0.6, -half), min(a + 0.6, half), 0.8, 15.6, CON3)
    for y in (5.6, 10.6, 15.6):
        slab(FR, axis, fixed, out, 1.3, -half, half, y - 0.6, y, CON3)
    for r in range(4):  # кладка в нижних пролётах — недоложенные ряды
        y = 0.9 + 1.0 * r
        for k in range(int(2 * half // 2.0)):
            a = -half + 2.0 * k + (1.0 if r % 2 else 0.0)
            if a + 1.9 > half or rng(fi, r, k) < 0.25 + 0.12 * r:
                continue
            slab(FR, axis, fixed, out, 1.0, a + 0.06, a + 1.94, y + 0.06, y + 0.94, (BRICK, BRICK2)[(k + r) % 2])
    slab(FR, axis, fixed, out, 1.0, -half, half, 16.4, 18.9, CON2)
    if axis == "x":  # бока: леса и штабеля кирпича
        scaffold(FS, axis, fixed, out, -12.0, 6.0, (5.0, 10.0))
        for z in (9.0, 12.4):
            brick_stack(FS, fixed + out * 2.0, z, 0.0, 3 + int(z) % 2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# перед: леса с сеткой, проём-вход, ограждения, мигалки, конусы, тачка, бетономешалка
scaffold(FS, "z", -FZ, -1, -FX, FX, (5.0, 10.0, 15.0))
for k, (a0, a1, y0, y1) in enumerate(((-FX + 0.2, -10.0, 5.4, 9.8), (6.0, FX - 0.2, 10.4, 14.8), (-6.0, 2.0, 15.4, 16.4))):
    FS.box(a0, a1, y0, y1, -FZ - 2.32, -FZ - 2.26, NET)
    for m in range(int((a1 - a0) // 0.8)):
        x = a0 + 0.8 * m
        FS.box(x, x + 0.06, y0, y1, -FZ - 2.36, -FZ - 2.32, ORANGE2)
FS.box(-3.2, 3.2, 0.8, 5.0, -FZ - 1.0, -FZ - 0.88, BLACK)
FG.box(-2.8, 2.8, 0.8, 4.6, -FZ - 1.04, -FZ - 1.0, "FFE2A0")
for k, x in enumerate((-12.0, -8.6, 8.6, 12.0)):
    barrier(FS, x, -FZ - 4.6, along_x=True, L=3.2)
    FG.prism_xz(K.ngon(x, -FZ - 4.6, 0.28, 8), 1.1, 1.6, (ORANGE, YEL)[k % 2])
for x, z in ((-5.0, -FZ - 5.2), (-4.0, -FZ - 6.4), (5.0, -FZ - 5.4), (15.6, -FZ - 6.0), (-15.8, -FZ - 6.2)):
    cone(FS, x, z)
# тачка
FS.loft([(1.0, 1.0, -FZ - 6.6), (3.4, 1.0, -FZ - 6.6), (3.4, 1.0, -FZ - 5.4), (1.0, 1.0, -FZ - 5.4)],
        [(0.6, 2.0, -FZ - 6.9), (3.8, 2.0, -FZ - 6.9), (3.8, 2.0, -FZ - 5.1), (0.6, 2.0, -FZ - 5.1)], BLUE)
FS.prism_zy(K.ngon(-FZ - 6.0, 0.5, 0.5, 10), 0.4, 0.7, BLACK)
for e in (-1, 1):
    beam(FS, (3.4, 1.0, -FZ - 6.0 + e * 0.5), (5.2, 1.6, -FZ - 6.0 + e * 0.7), 0.12, 0.12, STEEL2)
# бетономешалка
FS.box(15.0, 17.6, 0.0, 0.6, -FZ - 3.6, -FZ - 1.6, YEL2)
FS.loft([(16.3 + 1.3 * math.cos(t), 1.0, -FZ - 2.6 + 1.3 * math.sin(t)) for t in [2 * math.pi * k / 10 for k in range(10)]],
        [(16.3 + 0.7 * math.cos(t), 3.6, -FZ - 2.6 + 0.7 * math.sin(t) - 0.6) for t in [2 * math.pi * k / 10 for k in range(10)]], ORANGE)
FS.prism_xz(K.ngon(16.3, -FZ - 2.6, 1.0, 10), 0.6, 1.0, ORANGE2)
# кран-малыш на крыше: мачта-ферма, стрела, противовес, трос с поддоном конусов
MX, MZ = -10.0, -FZ - 1.0
for e in (-1, 1):
    for f in (-1, 1):
        beam(FS, (MX + e * 0.5, 15.6, MZ + f * 0.5), (MX + e * 0.5, 18.6, MZ + f * 0.5), 0.14, 0.14, YEL)
for y in (16.4, 17.4, 18.4):
    FS.box(MX - 0.6, MX + 0.6, y - 0.08, y, MZ - 0.6, MZ + 0.6, YEL2)
FS.box(MX - 4.0, MX + 12.0, 18.4, 18.9, MZ - 0.4, MZ + 0.4, YEL)
for k in range(8):
    x = MX - 3.6 + 2.0 * k
    beam(FS, (x, 18.4, MZ), (x + 1.0, 18.9, MZ), 0.1, 0.1, YEL2)
FS.box(MX - 4.0, MX - 2.4, 17.2, 18.4, MZ - 0.7, MZ + 0.7, CON2)
FS.box(MX + 10.0 - 0.03, MX + 10.0 + 0.03, 13.6, 18.4, MZ - 0.03, MZ + 0.03, BLACK)
FS.prism_xz(K.octa(MX + 10.0, MZ, 0.3, 0.3, 0.1), 13.2, 13.6, RED)
for e in (-1, 1):
    beam(FS, (MX + 10.0, 13.2, MZ), (MX + 10.0 + e * 1.0, 12.2, MZ), 0.06, 0.06, BLACK)
pallet(FS, MX + 10.0, MZ, 11.8, 2.2, 1.6)
for e in (-0.5, 0.5):
    cone(FS, MX + 10.0 + e, MZ, 12.18, 1.1)
# тыл: кучи песка и трубы
for x, r, h in ((-8.0, 3.0, 2.6), (-3.4, 2.2, 1.8)):
    FS.cone([(x + r * math.cos(t), -0.1, FZ + 3.6 + r * 0.8 * math.sin(t)) for t in [2 * math.pi * k / 10 for k in range(10)]],
            (x, h, FZ + 3.6), SAND)
for k in range(3):
    FS.prism_xy(K.ngon(6.0 + 1.0 * k, 0.5, 0.5, 8), FZ + 1.4, FZ + 6.0, STEEL2)
FS.prism_xy(K.ngon(6.5, 1.35, 0.5, 8), FZ + 1.4, FZ + 6.0, STEEL)

# ══ ИНТЕРЬЕР: голый каркас стройки ════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.18  # верх третьего поддона
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), CON2)
for x0, z0, x1, z1 in ((-12.0, -12.0, 12.0, -12.0), (-12.0, -12.0, -12.0, 6.0), (12.0, -12.0, 12.0, 6.0)):  # меловая разметка
    IQ.box(min(x0, x1) - 0.06, max(x0, x1) + 0.06, 0.02, 0.04, min(z0, z1) - 0.06, max(z0, z1) + 0.06, WHITE)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, CON)
        for r in range(6):  # кладка до половины стены, выше — голый бетон
            y = 0.1 + 1.0 * r
            for k in range(int((a1 - a0) // 2.0)):
                a = a0 + 2.0 * k + (1.0 if r % 2 else 0.0)
                if a + 1.9 > a1 or rng(idx, r, k) < 0.08 * r:
                    continue
                slab(IR, axis, fixed, out, 1.0, a + 0.06, a + 1.94, y + 0.06, y + 0.94, (BRICK, BRICK2)[(k + r) % 2])
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, CON)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, YEL)
    for k in range(int(2 * half // 1.6)):  # лента «осторожно» вдоль стен
        a = -half + 1.6 * k
        slab(IS, axis, fixed, out, 1.1, a, a + 0.8, 7.0, 7.4, (YEL, BLACK)[k % 2])
# проёмы под окна, затянутые плёнкой, и щиты опалубки на верхней части стен
for idx, (axis, fixed, out, half) in enumerate(B.WALLS[:3]):
    for a in ((-12.0, -3.0, 6.0) if idx < 2 else (-9.0, 9.0)):
        gp = IG.prism_xy if axis == "z" else IG.prism_zy
        fr = IS.frame_xy if axis == "z" else IS.frame_zy
        gp(K.rect(a - 2.4, a + 2.4, 9.0, 13.0), *sorted((fixed + out * 0.9, fixed + out * 0.94)), "D8ECF4")
        fr(K.rect(a - 2.7, a + 2.7, 8.7, 13.3), K.rect(a - 2.4, a + 2.4, 9.0, 13.0), *sorted((fixed + out * 0.88, fixed + out * 1.2)), WOOD)
        slab(IS, axis, fixed, out, 1.1, a - 2.4, a + 2.4, 10.9, 11.1, WOOD2)
    for a in ((-7.5, 1.5, 10.5) if idx < 2 else (0.0,)):
        slab(IS, axis, fixed, out, 1.05, a - 1.6, a + 1.6, 14.0, 16.6, WOOD)
        for m in (-1, 1):
            slab(IS, axis, fixed, out, 1.15, a + m * 1.0 - 0.1, a + m * 1.0 + 0.1, 14.0, 16.6, WOOD2)
# жёлтые двутавровые колонны и балки
for x in (-10.0, 10.0):
    for z in (-10.0, 4.0):
        IS.box(x - 0.7, x + 0.7, 0.0, C, z - 0.12, z + 0.12, YEL)
        IS.box(x - 0.7, x + 0.7, 0.0, C, z - 0.6, z - 0.45, YEL)
        IS.box(x - 0.7, x + 0.7, 0.0, C, z + 0.45, z + 0.6, YEL)
    IS.box(x - 0.6, x + 0.6, C - 1.2, C - 0.2, ZF, ZB, YEL2)
for z in (-10.0, 4.0):
    IS.box(-W, W, C - 1.0, C - 0.4, z - 0.5, z + 0.5, YEL2)
# вышка-тура лесов у дальней стены
for e in (-1, 1):
    for f in (-1, 1):
        beam(IS, (-6.0 + e * 1.5, 0.0, ZF + 3.0 + f * 1.4), (-6.0 + e * 1.5, 9.0, ZF + 3.0 + f * 1.4), 0.14, 0.14, YEL)
for y in (3.0, 6.0, 9.0):
    IS.box(-7.6, -4.4, y - 0.15, y, ZF + 1.5, ZF + 4.5, WOOD)
    beam(IS, (-7.5, y - 3.0, ZF + 4.4), (-4.5, y, ZF + 4.4), 0.1, 0.1, YEL2)
# поддоны кирпича, мешки цемента, каски, ящик с инструментами, прожекторы, лампы на проводах
for x, z, n in ((6.0, ZF + 2.4, 4), (9.0, ZF + 2.4, 3), (13.2, -6.0, 4)):
    brick_stack(IS, x, z, 0.0, n)
for k in range(5):
    IS.box(-13.6 + 0.1 * (k % 2), -11.6 + 0.1 * (k % 2), 0.38 + 0.45 * (k // 2), 0.8 + 0.45 * (k // 2), -2.0 + 1.1 * (k % 2) - 0.5,
           -2.0 + 1.1 * (k % 2) + 0.5, "D8D0BE")
pallet(IS, -12.6, -1.4, 0.0, 2.6, 2.8)
for k, (x, z) in enumerate(((-13.0, 7.0), (-11.8, 7.6), (13.0, 8.0))):
    hard_hat(IS, x, z, 0.0, (YEL, ORANGE, WHITE)[k])
IS.box(11.0, 13.6, 0.0, 1.2, 10.4, 11.6, RED)
IS.box(11.0, 13.6, 1.2, 1.3, 10.4, 11.6, BLACK)
IS.box(11.8, 12.8, 1.3, 1.7, 10.9, 11.1, BLACK)
floodlight(IS, IG, -13.0, -11.0, 4.0, math.radians(45))
floodlight(IS, IG, 13.0, -12.0, 4.4, math.radians(135))
for x, z in ((-6.0, -6.0), (6.0, -6.0), (0.0, 4.0), (-6.0, 8.0), (6.0, 8.0)):
    IS.box(x - 0.03, x + 0.03, 12.6, C, z - 0.03, z + 0.03, BLACK)
    IG.prism_xz(K.octa(x, z, 0.35, 0.35, 0.14), 11.8, 12.6, "FFE9A8")
for x, z in ((-7.0, 2.0), (7.4, 1.6), (-4.0, 6.0), (4.4, 6.4)):
    cone(IS, x, z)
beam(IS, (-7.0, 1.0, 2.0), (-4.0, 1.0, 6.0), 0.06, 0.24, YEL)
beam(IS, (7.4, 1.0, 1.6), (4.4, 1.0, 6.4), 0.06, 0.24, YEL)
# постамент — стопка поддонов с жёлто-чёрной кромкой, конусы по углам
px, pz = PED
for k in range(3):
    pallet(IS, px, pz, 0.4 * k, 6.4, 5.6)
for k in range(13):  # жёлто-чёрная кромка верхнего поддона
    x = px - 3.25 + 0.5 * k
    IS.box(x, x + 0.5, 0.86, TOP, pz + 2.82, pz + 3.0, (YEL, BLACK)[k % 2])
    IS.box(x, x + 0.5, 0.86, TOP, pz - 3.0, pz - 2.82, (YEL, BLACK)[k % 2])
for e in (-1, 1):
    for f in (-1, 1):
        cone(IS, px + e * 4.2, pz + f * 3.6, 0.0, 1.3)
B.lift_leaves(IS, CON2, YEL)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, CON)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, SAND2)
for y in (5.0, 10.0, 15.0):
    SL.box(-FX, FX, y - 0.2, y + 0.4, -FZ - 2.4, -FZ, WOOD)
SL.box(-FX + 0.2, -10.0, 5.4, 9.8, -FZ - 2.4, -FZ - 2.2, NET)
SL.box(6.0, FX - 0.2, 10.4, 14.8, -FZ - 2.4, -FZ - 2.2, NET)
SL.box(MX - 4.0, MX + 12.0, 18.4, 18.9, MZ - 0.4, MZ + 0.4, YEL)
SL.box(MX - 0.6, MX + 0.6, 15.6, 18.4, MZ - 0.6, MZ + 0.6, YEL)

F.build(exhibit=(PED[0], TOP, PED[1], 2.8), lamps=[("Hall", (0, 14, 6), 2800, (1.0, 0.96, 0.88)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.95, 0.85)),
                                                   ("Flood", (-12, 5, -10), 900, (1.0, 0.9, 0.6))])
