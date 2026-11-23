"""Этаж «Мир в бутылке» музея-небоскрёба (вторая партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — корма старинного галеона, плывущего по волнам (фасад v2, 2026-11-21). Снаружи — корпус из тёмных
досок-поясов с выносом кверху, чёрный привальный брус и золотой пояс, по низу — волны с пеной; на корме — руль с
золотыми петлями, кормовой балкон на кницах с золочёными балясинами, два яруса окон в золочёных рамах (верхний — под
арочными фронтонами), резной гакаборт с розой ветров и тремя кормовыми фонарями на кронштейнах; на бортах у кормы —
кормовые галереи-башенки с окнами вкруговую и золочёными куполами; по бортам — пушечные порты с откинутыми красными
крышками и пушками, руслени с юферсами, ванты с выбленками, спасательные круги, якорь у носа; на носу (тыл) — шлюпки.
Откат v1 — assets/concepts/tower_batch2/backup_v1/.
Внутри — каюта капитана: дощатый пол, стены в деревянных панелях с балками, на передней стене — большие
кормовые окна с видом на море и закат, полки с бутылками-кораблями, штурвал на стене, стол с картой и
глобусом, сундук, бухты каната, подвесные фонари; экспонат — на латунной подставке на круглом столе-тумбе.
Запуск: blender --background --factory-startup --python scripts/blender/floor_bottle.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab, tube  # noqa: E402

HULL, HULL2, HULL3, PLANK, PLANK2 = "5A3A24", "4A2E1C", "6E4A30", "A8743A", "8A5A32"
GOLD, GOLD2, BRASS, NAVY, NAVY2 = "E8B84A", "B8892E", "D8A84A", "23344F", "2E4466"
SEA, SEA2, FOAM, SKY, SUNSET = "2FA5C8", "1F7FA8", "EEF8FA", "8CC8EE", "FFB070"
RED, WHITE, ROPE, LAMP, GLASS, CORK = "C2463A", "F4F0E6", "C8A46A", "FFD27A", "4FA888", "B8895A"

F = B.Floor("WB", "WorldInBottle", quiet=(SEA2, PLANK2, NAVY), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def porthole(p, g, axis, fixed, out, a, y, r):
    lo, hi = sorted((fixed + out * 0.88, fixed + out * 1.25))
    (p.frame_xy if axis == "z" else p.frame_zy)(K.octa(a, y, r, r, r * 0.41), K.octa(a, y, r * 0.72, r * 0.72, r * 0.3), lo, hi,
                                                 BRASS)
    glo, ghi = sorted((fixed + out * 0.88, fixed + out * 1.0))
    (g.prism_xy if axis == "z" else g.prism_zy)(K.octa(a, y, r * 0.72, r * 0.72, r * 0.3), glo, ghi, LAMP)


def lifebuoy(p, axis, fixed, out, a, y, r):
    lo, hi = sorted((fixed + out * 1.0, fixed + out * 1.5))
    for k in range(8):
        t0, t1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        pts = [(a + r * math.cos(t0), y + r * math.sin(t0)), (a + r * math.cos(t1), y + r * math.sin(t1)),
               (a + r * 0.55 * math.cos(t1), y + r * 0.55 * math.sin(t1)), (a + r * 0.55 * math.cos(t0), y + r * 0.55 * math.sin(t0))]
        (p.prism_xy if axis == "z" else p.prism_zy)(pts, lo, hi, RED if k % 2 else WHITE)


def ship_in_bottle(p, g, x, y, z, s):
    """Бутылка с корабликом на подставке (лежит вдоль x)."""
    p.box(x - 0.9 * s, x + 0.9 * s, y, y + 0.15 * s, z - 0.3 * s, z + 0.3 * s, PLANK2)
    g.prism_zy(K.octa(z, y + 0.6 * s, 0.45 * s, 0.45 * s, 0.18 * s), x - 0.8 * s, x + 0.5 * s, GLASS)
    g.prism_zy(K.octa(z, y + 0.6 * s, 0.2 * s, 0.2 * s, 0.08 * s), x + 0.5 * s, x + 0.95 * s, GLASS)
    p.prism_zy(K.octa(z, y + 0.6 * s, 0.16 * s, 0.16 * s, 0.06 * s), x + 0.95 * s, x + 1.15 * s, CORK)
    p.box(x - 0.45 * s, x + 0.25 * s, y + 0.3 * s, y + 0.45 * s, z - 0.1 * s, z + 0.1 * s, HULL3)
    p.box(x - 0.12 * s, x - 0.08 * s, y + 0.45 * s, y + 0.95 * s, z - 0.02 * s, z + 0.02 * s, HULL2)
    p.box(x - 0.3 * s, x + 0.1 * s, y + 0.55 * s, y + 0.85 * s, z - 0.03 * s, z + 0.03 * s, WHITE)


# ══ ФАСАД v2: корма галеона ═══════════════════════════════════════════════════════════════════════════════════
IRON, PORT = "2A2A30", "1A1410"
B.shell_planes(F, HULL2, HULL2, PLANK2)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    # волны: вода и гребни (спереди — пенный след за кормой)
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, 0.2, SEA2)
    step = 2.6 if fi == 0 else 3.4
    for k in range(int((2 * half + 5) // step)):
        a = -half - 2.5 + step * k
        h = 0.5 + rng(fi, k) * 0.9
        slab(FS, axis, fixed, out, 2.95, a, a + 1.9, 0.2, 0.2 + h, SEA if k % 2 else "4AB8D8")
        slab(FS, axis, fixed, out, 3.0, a + 0.3, a + 1.4, 0.2 + h, 0.45 + h, FOAM)
    # корпус: пояса досок с выносом (борт расширяется кверху), швы
    for r in range(7):
        y0 = 0.2 + 2.0 * r
        d = 0.88 + (1.0 if r >= 3 else 0.0)
        slab(FR, axis, fixed, out, d, -half - d + 0.88, half + d - 0.88, y0, y0 + 1.94, (HULL, HULL3)[r % 2])
        slab(FS, axis, fixed, out, d - 0.08, -half, half, y0 + 1.94, y0 + 2.0, HULL2)
    slab(FS, axis, fixed, out, 2.1, -half - 1.2, half + 1.2, 6.0, 6.4, GOLD2)  # золотой пояс
    slab(FS, axis, fixed, out, 1.05, -half, half, 1.9, 2.3, IRON)  # чёрный привальный брус
    if fi == 0:
        continue
    # фальшборт: перила и балясины (сзади и по бокам; на корме — резной гакаборт)
    slab(FR, axis, fixed, out, 1.88, -half - 1.0, half + 1.0, 14.2, 15.0, HULL3)
    slab(FS, axis, fixed, out, 2.0, -half - 1.1, half + 1.1, 18.4, 19.0, PLANK)
    for k in range(int(2 * half // 1.3)):
        a = -half + 0.65 + 1.3 * k
        slab(FS, axis, fixed, out, 1.7, a - 0.2, a + 0.2, 15.0, 18.4, PLANK if k % 2 else PLANK2)
    slab(FS, axis, fixed, out, 1.2, -half, half, 15.0, 18.4, HULL2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))

# корма: руль, кормовой балкон с балясинами, два яруса окон, резной гакаборт с розой ветров, три фонаря
FS.prism_xy([(-0.8, 6.2), (0.8, 6.2), (1.7, -0.6), (-1.7, -0.6)], -FZ - 2.3, -FZ - 1.3, HULL3)  # руль
for y in (1.2, 3.2, 5.0):
    FS.box(-1.1, 1.1, y, y + 0.35, -FZ - 2.45, -FZ - 1.2, GOLD2)
FS.box(-14.4, 14.4, 6.4, 6.9, -FZ - 3.6, -FZ, PLANK)  # палуба балкона
FS.box(-14.4, 14.4, 6.3, 6.4, -FZ - 3.7, -FZ - 3.4, GOLD)
for x in (-12.0, -6.0, 6.0, 12.0):  # кницы под балконом
    FS.prism_zy([(-FZ, 6.4), (-FZ - 3.2, 6.4), (-FZ, 3.6)], x - 0.3, x + 0.3, HULL2)
for k in range(25):  # балясины
    x = -14.0 + 28.0 * k / 24
    FS.box(x - 0.14, x + 0.14, 6.9, 7.9, -FZ - 3.45, -FZ - 3.2, GOLD2 if k % 2 else GOLD)
FS.box(-14.4, 14.4, 7.9, 8.15, -FZ - 3.6, -FZ - 3.05, HULL2)  # поручень
for k in range(5):  # нижний ярус окон
    x = -10.8 + 5.4 * k
    FS.box(x - 2.2, x + 2.2, 7.0, 11.0, -FZ - 2.3, -FZ - 1.6, GOLD2)
    FG.box(x - 1.8, x + 1.8, 7.4, 10.6, -FZ - 2.35, -FZ - 2.3, LAMP)
    FS.box(x - 0.08, x + 0.08, 7.4, 10.6, -FZ - 2.45, -FZ - 2.35, GOLD2)
    FS.box(x - 1.8, x + 1.8, 8.95, 9.1, -FZ - 2.45, -FZ - 2.35, GOLD2)
FS.box(-14.0, 14.0, 11.0, 11.6, -FZ - 2.6, -FZ - 1.6, GOLD)  # резной пояс между ярусами
for k in range(14):
    x = -13.0 + 2.0 * k
    FS.box(x - 0.35, x + 0.35, 11.15, 11.45, -FZ - 2.75, -FZ - 2.6, GOLD2)
for k in range(4):  # верхний ярус окон под арочными фронтонами
    x = -8.1 + 5.4 * k
    FS.box(x - 2.0, x + 2.0, 11.6, 14.2, -FZ - 2.2, -FZ - 1.6, GOLD2)
    FG.box(x - 1.6, x + 1.6, 12.0, 13.8, -FZ - 2.25, -FZ - 2.2, LAMP)
    FS.box(x - 0.07, x + 0.07, 12.0, 13.8, -FZ - 2.35, -FZ - 2.25, GOLD2)
    FS.prism_xy([(x - 2.2, 14.2), (x + 2.2, 14.2), (x + 1.4, 14.9), (x - 1.4, 14.9)], -FZ - 2.3, -FZ - 1.6, GOLD)
TAF = [(-13.0, 14.2), (13.0, 14.2), (13.0, 15.4), (9.0, 16.6), (4.5, 17.4), (0.0, 17.7), (-4.5, 17.4), (-9.0, 16.6),
       (-13.0, 15.4)]
FS.prism_xy(TAF, -FZ - 1.9, -FZ - 0.9, HULL3)  # гакаборт
FS.frame_xy([(-13.5, 13.9), (13.5, 13.9), (13.5, 15.6), (9.2, 16.95), (4.6, 17.8), (0.0, 18.15), (-4.6, 17.8),
             (-9.2, 16.95), (-13.5, 15.6)], TAF, -FZ - 2.1, -FZ - 0.9, GOLD)
ROSE = [(math.cos(math.pi * k / 4 + math.pi / 2) * (1.5 if k % 2 == 0 else 0.55),
         math.sin(math.pi * k / 4 + math.pi / 2) * (1.5 if k % 2 == 0 else 0.55)) for k in range(8)]
FS.prism_xy([(x, 15.9 + y) for x, y in ROSE], -FZ - 2.15, -FZ - 1.85, GOLD)  # роза ветров
FS.frame_xy(K.octa(0.0, 15.9, 1.0, 1.0, 0.41), K.octa(0.0, 15.9, 0.8, 0.8, 0.33), -FZ - 2.05, -FZ - 1.9, GOLD2)
for k in range(13):  # резной пояс по низу гакаборта
    x = -12.0 + 2.0 * k
    FS.box(x - 0.45, x + 0.45, 14.45, 14.75, -FZ - 2.05, -FZ - 1.85, GOLD2)
for x, y0, big in ((-9.0, 15.4, 0.0), (0.0, 16.0, 0.15), (9.0, 15.4, 0.0)):  # кормовые фонари на кронштейнах
    z = -FZ - 3.0
    beam(FS, (x, y0 - 0.6, -FZ - 1.9), (x, y0, z), 0.25, 0.25, HULL2)
    r = 0.6 + big
    FS.prism_xz(K.octa(x, z, r, r, r * 0.41), y0, y0 + 0.2, GOLD)
    FG.prism_xz(K.octa(x, z, r - 0.1, r - 0.1, (r - 0.1) * 0.41), y0 + 0.2, y0 + 1.8 + big * 2, LAMP)
    FS.prism_xz(K.octa(x, z, r, r, r * 0.41), y0 + 1.8 + big * 2, y0 + 2.1 + big * 2, GOLD)
    FS.cone([(u, y0 + 2.1 + big * 2, v) for u, v in K.octa(x, z, r, r, r * 0.41)], (x, y0 + 2.6 + big * 2, z), GOLD2)
# кормовые галереи-башенки на бортах у кормы: окна вкруговую, золочёный купол, подвеска снизу
for sx in (-1, 1):
    cx, cz = sx * (FX + 1.6), -FZ + 2.8
    G = lambda d, c=1.0: K.octa(cx, cz, 2.2 + d, 2.6 + d, c)  # noqa: E731
    FS.prism_xz(G(0.0, 0.95), 6.4, 14.4, HULL3)
    FG.prism_xz(G(0.06, 0.97), 8.2, 12.6, LAMP)
    for px_, pz_ in G(0.1, 1.0):
        FS.box(px_ - 0.16, px_ + 0.16, 8.2, 12.6, pz_ - 0.16, pz_ + 0.16, GOLD2)
    for y in (7.8, 12.6):
        FS.prism_xz(G(0.2, 1.03), y, y + 0.4, GOLD)
    FS.prism_xz(G(0.4, 1.1), 14.4, 15.0, GOLD)
    FS.cone([(u, 15.0, v) for u, v in G(0.2, 1.03)], (cx, 17.9, cz), GOLD2)
    FS.box(cx - 0.2, cx + 0.2, 17.6, 18.7, cz - 0.2, cz + 0.2, GOLD)
    FS.cone([(u, 6.4, v) for u, v in G(0.0, 0.95)], (cx, 3.8, cz), HULL3)
    FS.prism_xz(K.octa(cx, cz, 0.4, 0.4, 0.16), 3.2, 4.0, GOLD)

# борта: пушечные порты с откинутыми крышками и пушками, ванты с юферсами и выбленками, якорь, круг
for s in (-1, 1):
    fx = s * FX
    for z in (-9.0, -4.5, 0.0, 4.5, 9.0):
        FS.frame_zy(K.rect(z - 1.0, z + 1.0, 2.7, 4.7), K.rect(z - 0.8, z + 0.8, 2.9, 4.5), fx + s * 0.85, fx + s * 1.1, RED)
        FS.box(fx + s * 0.85, fx + s * 0.95, 2.9, 4.5, z - 0.8, z + 0.8, PORT)
        beam(FS, (fx + s * 1.05, 4.75, z), (fx + s * 2.2, 5.75, z), 1.9, 0.15, RED)  # крышка
        FS.prism_zy(K.octa(z, 3.6, 0.32, 0.32, 0.13), fx + s * 0.9, fx + s * 2.5, IRON)  # ствол
        FS.prism_zy(K.octa(z, 3.6, 0.42, 0.42, 0.17), fx + s * 2.2, fx + s * 2.5, IRON)
    FS.box(fx + s * 1.88, fx + s * 2.7, 13.6, 14.0, -5.5, 8.5, HULL3)  # руслень
    lines = []
    for k in range(5):
        z = -4.5 + 3.0 * k
        FS.prism_zy(K.octa(z, 14.3, 0.32, 0.32, 0.13), fx + s * 2.35, fx + s * 2.65, HULL2)  # юферс
        lines.append(((fx + s * 2.5, 14.5, z), (fx + s * 1.95, 18.85, 1.5 + (z - 1.5) * 0.3)))
        beam(FS, lines[-1][0], lines[-1][1], 0.13, 0.13, ROPE)
    for h in (0.25, 0.45, 0.65, 0.85):  # выбленки
        for a, b in zip(lines, lines[1:]):
            pa = tuple(a[0][i] + (a[1][i] - a[0][i]) * h for i in range(3))
            pb = tuple(b[0][i] + (b[1][i] - b[0][i]) * h for i in range(3))
            beam(FS, pa, pb, 0.08, 0.08, ROPE)
    lifebuoy(FS, "x", fx + s * 1.0, s, -7.6, 16.7, 1.2)
    # якорь у носа: шток, рога, кольцо, цепь
    az = 13.2
    ax_ = fx + s * 2.1
    FS.box(ax_ - 0.2, ax_ + 0.2, 4.0, 10.0, az - 0.25, az + 0.25, "3A3A42")
    FS.box(ax_ - 0.2, ax_ + 0.2, 9.0, 9.4, az - 1.4, az + 1.4, "3A3A42")
    FS.prism_zy([(az - 2.2, 5.6), (az - 1.6, 4.0), (az, 3.4), (az + 1.6, 4.0), (az + 2.2, 5.6), (az + 1.5, 4.8), (az, 4.2),
                 (az - 1.5, 4.8)], ax_ - 0.2, ax_ + 0.2, "3A3A42")
    FS.frame_zy(K.octa(az, 10.6, 0.6, 0.6, 0.25), K.octa(az, 10.6, 0.35, 0.35, 0.14), ax_ - 0.15, ax_ + 0.15, "3A3A42")
    for k in range(4):
        FS.frame_zy(K.octa(az, 11.6 + 0.8 * k, 0.3, 0.42, 0.12), K.octa(az, 11.6 + 0.8 * k, 0.15, 0.27, 0.06),
                    ax_ - 0.08, ax_ + 0.08, "5A5A64")
# тыл (нос): шлюпки на шлюпбалках, иллюминаторы
for s in (-1, 1):
    x = s * 9.0
    FS.prism_xz([(x - 3.2, FZ + 2.0), (x + 3.2, FZ + 2.0), (x + 2.6, FZ + 3.2), (x - 2.6, FZ + 3.2)], 11.6, 12.8, WHITE)
    FS.box(x - 2.8, x + 2.8, 12.8, 13.0, FZ + 2.1, FZ + 3.1, PLANK)
    for e in (-1, 1):
        beam(FS, (x + e * 2.4, 14.2, FZ + 2.0), (x + e * 2.4, 12.8, FZ + 2.6), 0.1, 0.1, ROPE)
    for k in range(3):
        porthole(FS, FG, "z", FZ, 1, x - 3.0 + 3.0 * k, 4.2, 0.8)

# ══ ИНТЕРЬЕР: каюта капитана ══════════════════════════════════════════════════════════════════════════════════
TABLE = (0.0, -3.0)
TOP = 1.4
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), PLANK2)
for k in range(17):  # швы палубы
    x = -W + 2.0 * k
    IS.box(x - 0.04, x + 0.04, 0.02, 0.05, ZF, ZB, HULL2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 1.0, HULL2)
        n = max(1, int((a1 - a0) // 2.4))
        for k in range(n):  # деревянные панели
            b0 = a0 + (a1 - a0) * k / n
            b1 = a0 + (a1 - a0) * (k + 1) / n
            slab(IR, axis, fixed, out, 0.88, b0 + 0.08, b1 - 0.08, 1.1, 5.4, PLANK if k % 2 else PLANK2)
        slab(IS, axis, fixed, out, 1.0, a0, a1, 5.4, 5.8, GOLD2)
    slab(IQ, axis, fixed, out, 0.7, -half, half, 0.0, C, HULL)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 14.0, HULL3)
    for k in range(int(2 * half // 4.0) + 1):  # шпангоуты
        a = -half + 4.0 * k
        slab(IS, axis, fixed, out, 1.3, a - 0.35, a + 0.35, 1.0, C, HULL2)
for k in range(-3, 4):  # бимсы потолка
    beam(IS, (-W, C - 0.35, 4.4 * k), (W, C - 0.35, 4.4 * k), 0.6, 0.7, HULL2)
# кормовые окна на передней стене: море и закат
for k in range(4):
    x = -10.5 + 7.0 * k
    IS.box(x - 3.1, x + 3.1, 6.0, 14.6, ZF + 0.85, ZF + 1.3, GOLD2)
    IQ.box(x - 2.7, x + 2.7, 6.4, 9.0, ZF + 1.3, ZF + 1.35, SEA2)
    IQ.box(x - 2.7, x + 2.7, 9.0, 14.2, ZF + 1.3, ZF + 1.35, SKY)
    IG.box(x - 2.7, x + 2.7, 9.0, 10.2, ZF + 1.35, ZF + 1.38, SUNSET)
    IS.box(x - 0.08, x + 0.08, 6.4, 14.2, ZF + 1.35, ZF + 1.45, GOLD2)
    IS.box(x - 2.7, x + 2.7, 10.3, 10.42, ZF + 1.35, ZF + 1.45, GOLD2)
IG.prism_xy(K.octa(3.5, 9.6, 1.0, 1.0, 0.41), ZF + 1.38, ZF + 1.4, "FFE08A")  # солнце у горизонта
# полки с бутылками-кораблями вдоль левой стены
for y in (6.6, 9.2, 11.8):
    IS.box(-W, -W + 1.6, y - 0.15, y, -12.5, -2.5, PLANK)
    for k in range(4):
        ship_in_bottle(IS, IG, -W + 0.8, y, -11.4 + 2.6 * k, 1.0)
# штурвал на правой стене
wz, wy = -6.0, 9.0
IS.frame_zy(K.octa(wz, wy, 2.2, 2.2, 0.9), K.octa(wz, wy, 1.8, 1.8, 0.75), W - 1.2, W - 0.9, PLANK)
IS.prism_zy(K.octa(wz, wy, 0.5, 0.5, 0.2), W - 1.3, W - 0.8, GOLD)
for k in range(8):
    t = 2 * math.pi * k / 8
    beam(IS, (W - 1.05, wy + 0.4 * math.sin(t), wz + 0.4 * math.cos(t)),
         (W - 1.05, wy + 2.8 * math.sin(t), wz + 2.8 * math.cos(t)), 0.18, 0.18, PLANK2)
# стол с картой и глобусом, сундук, бухты каната
IS.box(7.0, 13.0, 2.6, 2.9, 2.0, 6.0, PLANK)
for x in (7.3, 12.7):
    for z in (2.3, 5.7):
        IS.box(x - 0.15, x + 0.15, 0.0, 2.6, z - 0.15, z + 0.15, HULL3)
IS.box(7.6, 11.4, 2.9, 2.95, 2.5, 5.2, "EAD8A8")  # карта
IS.box(8.4, 9.6, 2.95, 2.98, 3.2, 4.0, SEA)
IS.prism_xz(K.octa(12.0, 4.0, 0.35, 0.35, 0.14), 2.9, 3.3, GOLD2)
IS.prism_xz(K.octa(12.0, 4.0, 0.75, 0.75, 0.31), 3.3, 4.7, SEA)  # глобус
IS.prism_xz(K.octa(12.0, 4.0, 0.78, 0.78, 0.32), 3.85, 4.15, "6AB83E")
IS.box(-13.5, -10.5, 0.0, 1.8, 9.0, 11.0, HULL3)  # сундук
IS.box(-13.6, -10.4, 1.8, 2.4, 8.9, 11.1, HULL)
for x in (-13.0, -11.0):
    IS.box(x - 0.15, x + 0.15, 0.0, 2.45, 8.85, 11.15, BRASS)
for x, z in ((-6.5, 12.5), (6.5, 12.0)):
    for k in range(3):
        IS.frame_xz(K.octa(x, z, 1.1 - 0.2 * k, 1.1 - 0.2 * k, 0.45), K.octa(x, z, 0.5 - 0.1 * k, 0.5 - 0.1 * k, 0.2),
                    0.3 * k, 0.3 * (k + 1), ROPE)
# подвесные фонари
for x, z in ((-6.0, -8.0), (6.0, -8.0), (0.0, 6.0)):
    IS.box(x - 0.04, x + 0.04, 14.5, C - 0.7, z - 0.04, z + 0.04, "3A3A42")
    IS.prism_xz(K.octa(x, z, 0.5, 0.5, 0.2), 14.3, 14.5, BRASS)
    IG.prism_xz(K.octa(x, z, 0.4, 0.4, 0.16), 13.1, 14.3, LAMP)
    IS.prism_xz(K.octa(x, z, 0.5, 0.5, 0.2), 12.9, 13.1, BRASS)
# стол-тумба с латунной подставкой
px, pz = TABLE
IR.prism_xz(K.octa(px, pz, 4.0, 4.0, 1.65), 0.0, 0.6, HULL3)
IR.prism_xz(K.octa(px, pz, 3.4, 3.4, 1.4), 0.6, TOP, PLANK)
IS.frame_xz(K.octa(px, pz, 3.55, 3.55, 1.47), K.octa(px, pz, 3.4, 3.4, 1.4), TOP - 0.25, TOP, BRASS)
for k in range(6):  # волны-гребни вокруг тумбы (резьба)
    t = 2 * math.pi * k / 6
    x, z = px + 4.05 * math.cos(t), pz + 4.05 * math.sin(t)
    IS.prism_xz(K.octa(x, z, 0.45, 0.45, 0.18), 0.0, 0.5, SEA)
B.lift_leaves(IS, HULL3, GOLD)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, HULL)
SL.box(-FX - 2.9, FX + 2.9, -1.0, 0.8, -FZ - 2.9, FZ + 2.9, SEA)
SL.box(-FX - 1.9, FX + 1.9, 6.2, 14.2, -FZ - 1.9, FZ + 1.9, HULL3)
SL.box(-FX - 1.9, FX + 1.9, 14.2, 19.0, -FZ + 0.1, FZ + 1.9, PLANK2)
SL.box(-14.4, 14.4, 6.4, 8.1, -FZ - 3.6, -FZ, GOLD2)
SL.box(-13.0, 13.0, 8.1, 14.2, -FZ - 2.4, -FZ, LAMP)
SL.box(-13.0, 13.0, 14.2, 17.0, -FZ - 2.0, -FZ, GOLD)
SL.box(-1.5, 1.5, -0.6, 6.2, -FZ - 2.3, -FZ, HULL3)
for s in (-1, 1):
    SL.box(s * FX, s * (FX + 3.8), 6.4, 15.0, -FZ + 0.2, -FZ + 5.4, HULL3)
    SL.box(s * FX, s * (FX + 3.4), 15.0, 17.6, -FZ + 0.6, -FZ + 5.0, GOLD2)

F.build(mlf=1, exhibit=(TABLE[0], TOP, TABLE[1], 3.2), lamps=[("Hall", (0, 14, 6), 2800, (1.0, 0.88, 0.7)),
                                                       ("Spot", (0, 13, -3), 3200, (1.0, 0.95, 0.85))])
