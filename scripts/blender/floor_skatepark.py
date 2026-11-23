"""Этаж «Сырный скейтер» музея-небоскрёба (пятая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — городской скейтпарк. Снаружи — бетонная стена из плит со швами, яркие граффити-пятна, стрелки и
зигзаги (без лиц и букв), рулонные ворота-гараж с неоновой рамкой, над ними — огромная вывеска-скейтборд из «сыра»
с дырками и рыжими колёсами; слева к фасаду пристроена рампа-«четвертинка» с металлическим копингом и площадкой,
справа — лестница с перилами для слайда, фонарь, сетка-рабица, бумбокс на ящике, конусы; бока — граффити, водостоки,
рабица; сзади — морской контейнер и бочки. Внутри — крытый скейтпарк: бетонный пол с разметкой, рампы-четвертинки
вдоль боковых стен, большой хафпайп у дальней стены с площадкой и ограждением, промышленные окна и фермы под
потолком, стойка с досками, скамьи, сырные круги-табуреты, граффити; экспонат — на фанбоксе с сырной крышкой и
стальными кромками, перед ним — перила для слайда.
Запуск: blender --background --factory-startup --python scripts/blender/floor_skatepark.py -- <репо> <превью>
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

CON, CON2, CON3, ASPH, ASPH2 = "B4B4B0", "9A9A98", "C8C8C2", "3A3A40", "4A4A52"
STEEL, STEEL2, RUST, CHEESE, CHEESE2, HOLE = "C8CCD4", "8A909C", "B0603A", "FFC83A", "F0A820", "D08A18"
NEONP, NEONC, NEONY = "FF3AA8", "3AE8FF", "FFE83A"
GR = ("FF4A7A", "3AB0FF", "7AE04A", "FF9A2A", "B06AF0", "FFE04A")  # граффити
WOOD, WOOD2, BOARD, BOARD2, TIRE = "C8925A", "9A6A3A", "2A2A30", "E83A3A", "2A2A2E"

F = B.Floor("SK", "CheeseSkater", quiet=(ASPH, ASPH2, CON2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def qpipe_zy(p, x0, x1, z_wall, out, h, r, top_d, col, cope=STEEL):
    """Рампа-четвертинка у стены z = z_wall, выступает в сторону out (±1), профиль в плоскости (z, y)."""
    pts = [(z_wall + out * (r + 0.2), 0.0)]
    for k in range(1, 7):  # вогнутая дуга: центр кривизны над началом рампы
        t = math.pi / 2 * k / 6
        pts.append((z_wall + out * (r - r * math.sin(t) + 0.2), h - h * math.cos(t)))
    pts += [(z_wall - out * top_d, h), (z_wall - out * top_d, 0.0)]
    p.prism_zy(pts, x0, x1, col)
    p.prism_zy(K.ngon(z_wall + out * 0.2, h, 0.22, 6), x0, x1, cope)


def qpipe_xy(p, z0, z1, x_wall, out, h, r, top_d, col, cope=STEEL):
    """Та же рампа у стены x = x_wall (профиль в плоскости (x, y), вытянута вдоль z)."""
    pts = [(x_wall + out * (r + 0.2), 0.0)]
    for k in range(1, 7):
        t = math.pi / 2 * k / 6
        pts.append((x_wall + out * (r - r * math.sin(t) + 0.2), h - h * math.cos(t)))
    pts += [(x_wall - out * top_d, h), (x_wall - out * top_d, 0.0)]
    p.prism_xy(pts, z0, z1, col)
    p.prism_xy(K.ngon(x_wall + out * 0.2, h, 0.22, 6), z0, z1, cope)


def skateboard(p, x, y, z, L, col=BOARD, grip=BOARD2, wheel="FF8A2A", along_x=True, up=0.0):
    """Скейтборд: дека с загнутыми носом и хвостом, подвески, четыре колеса (вдоль x или z)."""
    w, t = L * 0.26, L * 0.05
    if along_x:
        p.prism_xy([(x - L / 2, y + up + t * 2.4), (x - L * 0.38, y + up), (x + L * 0.38, y + up), (x + L / 2, y + up + t * 2.4),
                    (x + L / 2, y + up + t * 3.4), (x + L * 0.38, y + up + t), (x - L * 0.38, y + up + t), (x - L / 2, y + up + t * 3.4)],
                   z - w / 2, z + w / 2, col)
        p.box(x - L * 0.36, x + L * 0.36, y + up + t, y + up + t * 1.3, z - w * 0.42, z + w * 0.42, grip)
        for e in (-1, 1):
            p.box(x + e * L * 0.27 - L * 0.04, x + e * L * 0.27 + L * 0.04, y + up - t * 1.4, y + up, z - w * 0.4, z + w * 0.4, STEEL2)
            for f in (-1, 1):
                p.prism_xy(K.ngon(x + e * L * 0.27, y + up - t * 2.0, t * 1.4, 8), z + f * w * 0.45 - t * 0.9,
                           z + f * w * 0.45 + t * 0.9, wheel)
    else:
        p.prism_zy([(z - L / 2, y + up + t * 2.4), (z - L * 0.38, y + up), (z + L * 0.38, y + up), (z + L / 2, y + up + t * 2.4),
                    (z + L / 2, y + up + t * 3.4), (z + L * 0.38, y + up + t), (z - L * 0.38, y + up + t), (z - L / 2, y + up + t * 3.4)],
                   x - w / 2, x + w / 2, col)
        for e in (-1, 1):
            for f in (-1, 1):
                p.prism_zy(K.ngon(z + e * L * 0.27, y + up - t * 2.0, t * 1.4, 8), x + f * w * 0.45 - t * 0.9, x + f * w * 0.45 + t * 0.9,
                           wheel)


def graffiti(p, g, axis, fixed, out, a, y, s, seed):
    """Граффити-пятно: облако из рубленых комков, полосы-стрелка и зигзаг, капли; без лиц и букв."""
    pr = p.prism_xy if axis == "z" else p.prism_zy
    d0 = fixed + out * 0.9
    lay = lambda k: sorted((d0 + out * 0.04 * k, d0 + out * 0.04 * (k + 1)))  # noqa: E731
    c0, c1, c2 = GR[seed % 6], GR[(seed + 2) % 6], GR[(seed + 4) % 6]
    for k in range(4):
        cx = a + (k - 1.5) * s * 0.55
        cy = y + s * 0.18 * math.sin(k * 1.7 + seed)
        pr(K.octa(cx, cy, s * 0.42, s * 0.36, s * 0.14), *lay(0), c0)
    pr([(a - s * 1.0, y - s * 0.12), (a + s * 0.6, y - s * 0.12), (a + s * 0.6, y - s * 0.32), (a + s * 1.15, y),
         (a + s * 0.6, y + s * 0.32), (a + s * 0.6, y + s * 0.12), (a - s * 1.0, y + s * 0.12)], *lay(1), c1)
    for k in range(5):
        x0 = a - s * 1.1 + k * s * 0.45
        pr([(x0, y - s * 0.62), (x0 + s * 0.22, y - s * 0.42), (x0 + s * 0.45, y - s * 0.62), (x0 + s * 0.45, y - s * 0.5),
            (x0 + s * 0.22, y - s * 0.3), (x0, y - s * 0.5)], *lay(1), c2)
    for k in range(3):
        x0 = a - s * 0.9 + k * s * 0.8 + rng(seed, k) * s * 0.3
        pr(K.rect(x0, x0 + s * 0.1, y - s * 0.55 - s * 0.4 * rng(k, seed), y - s * 0.3), *lay(0), c0)


def fence(p, axis, fixed, out, a0, a1, h, col=STEEL2):
    """Рабица: столбы, верхняя и нижняя трубы, ромбическая сетка из тонких прутьев."""
    pb = (lambda q0, q1: beam(p, q0, q1, 0.08, 0.08, col))
    for a in (a0, (a0 + a1) / 2, a1):
        if axis == "z":
            p.prism_xz(K.ngon(a, fixed + out * 0.3, 0.14, 6), 0.0, h, col)
        else:
            p.prism_xz(K.ngon(fixed + out * 0.3, a, 0.14, 6), 0.0, h, col)
    n = int((a1 - a0) // 0.9)
    for k in range(n + 1):
        u = a0 + (a1 - a0) * k / n
        if axis == "z":
            pb((u, 0.2, fixed + out * 0.3), (min(u + h * 0.5, a1), h - 0.2, fixed + out * 0.3))
        else:
            pb((fixed + out * 0.3, 0.2, u), (fixed + out * 0.3, h - 0.2, min(u + h * 0.5, a1)))
    for y in (0.2, h):
        if axis == "z":
            beam(p, (a0, y, fixed + out * 0.3), (a1, y, fixed + out * 0.3), 0.14, 0.14, col)
        else:
            beam(p, (fixed + out * 0.3, y, a0), (fixed + out * 0.3, y, a1), 0.14, 0.14, col)


def cone(p, x, z, y=0.0, h=1.4):
    """Дорожный конус: основание, конус, светоотражающая полоса."""
    p.box(x - 0.55, x + 0.55, y, y + 0.14, z - 0.55, z + 0.55, "FF6A1A")
    p.cone([(x + 0.4 * math.cos(t), y + 0.14, z + 0.4 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]],
           (x, y + h, z), "FF6A1A")
    p.prism_xz(K.ngon(x, z, 0.26, 8), y + h * 0.45, y + h * 0.6, "F4F4F4")


def cheese_wheel(p, x, z, y=0.0, r=1.0, h=0.8):
    """Сырный круг-табурет: корка, срез с дырками."""
    p.prism_xz(K.ngon(x, z, r, 12), y, y + h, CHEESE2)
    p.prism_xz(K.ngon(x, z, r * 0.92, 12), y + h, y + h + 0.06, CHEESE)
    for k in range(3):
        t = 2 * math.pi * (k + rng(x, z, k) * 0.5) / 3
        rr = r * (0.12 + 0.08 * rng(k, x))
        p.prism_xz(K.ngon(x + r * 0.5 * math.cos(t), z + r * 0.5 * math.sin(t), rr, 6), y + h + 0.06, y + h + 0.1, HOLE)


# ══ ФАСАД: бетонная стена скейтпарка ══════════════════════════════════════════════════════════════════════════
B.shell_planes(F, CON, CON, ASPH)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.1, ASPH)
    slab(FR, axis, fixed, out, 1.38, -half - 0.4, half + 0.4, -0.1, 1.0, CON2)
    for k in range(int(2 * half // 4.0)):  # бетонные плиты со швами
        a = -half + 4.0 * k
        for r in range(3):
            y = 1.0 + 4.6 * r
            slab(FR, axis, fixed, out, 0.88 + 0.08 * ((k + r) % 2), a + 0.08, a + 3.92, y + 0.08, y + 4.52, (CON, CON3)[(k + r) % 2])
    slab(FR, axis, fixed, out, 1.88, -half - 0.6, half + 0.6, 14.8, 15.8, CON2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 15.8, 18.9, CON)
    for k in range(int(2 * half // 3.0)):  # граффити-пояс наверху: косые полосы
        a = -half + 3.0 * k + 0.3
        pr = FS.prism_xy if axis == "z" else FS.prism_zy
        pr([(a, 16.2), (a + 1.2, 16.2), (a + 2.2, 18.5), (a + 1.0, 18.5)], *sorted((fixed + out * 0.88, fixed + out * 1.0)), GR[k % 6])
    if axis == "x":  # бока: граффити, водосток, рабица
        for k, z in enumerate((-9.0, 2.0, 11.0)):
            graffiti(FS, FG, axis, fixed, out, z, 8.0 + 2.0 * (k % 2), 2.8, k + 3 * (fixed > 0))
        fence(FS, axis, fixed + out * 1.4, out, -14.0, -4.0, 3.6)
        FS.prism_xz(K.ngon(fixed + out * 1.2, 14.6, 0.3, 6), 0.0, 15.8, STEEL2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# перед: рулонные ворота с неоновой рамкой
FS.box(-5.6, 5.6, 0.0, 9.0, -FZ - 1.1, -FZ - 0.88, STEEL2)
for k in range(17):
    y = 0.3 + 0.5 * k
    FS.box(-5.2, 5.2, y, y + 0.3, -FZ - 1.25, -FZ - 1.1, (STEEL, STEEL2)[k % 2])
FS.box(-5.6, 5.6, 8.6, 9.6, -FZ - 1.9, -FZ - 0.88, CON2)
FG.frame_xy(K.rect(-6.2, 6.2, 0.0, 10.0), K.rect(-5.8, 5.8, 0.0, 9.6), -FZ - 1.32, -FZ - 1.12, NEONP)
for k, (a, y, sz) in enumerate(((-12.0, 6.0, 3.0), (12.0, 7.5, 3.0), (2.6, 12.8, 2.2), (12.6, 12.8, 2.4))):
    graffiti(FS, FG, "z", -FZ, -1, a, y, sz, k)
for k in range(16):  # полосатый цоколь «осторожно» вдоль фасада
    x = -FX + 2.3 * k
    if -6.2 < x + 1.1 < 6.2:
        continue
    FS.prism_xy([(x, 1.0), (x + 1.1, 1.0), (x + 1.8, 2.0), (x + 0.7, 2.0)], -FZ - 1.0, -FZ - 0.88, ("FFD02A", "2A2A30")[k % 2])
# вывеска-скейтборд из сыра над рампой: доска в наклоне «в прыжке» — колёса на разной высоте (ровная пара колёс под
# дугой деки читалась «лицом»)
SX, SY, SZ, SLEN = -9.6, 12.6, -FZ - 2.0, 13.0
SA = math.radians(-16)


def srot(u, v):
    """Точка вывески: смещение (u, v) от центра, повёрнутое на SA."""
    return (SX + u * math.cos(SA) - v * math.sin(SA), SY + u * math.sin(SA) + v * math.cos(SA))


FS.prism_xy([srot(u, v) for u, v in ((-SLEN / 2, 1.6), (-SLEN * 0.38, 0.0), (SLEN * 0.38, 0.0), (SLEN / 2, 1.6), (SLEN / 2, 2.6),
                                     (SLEN * 0.38, 1.0), (-SLEN * 0.38, 1.0), (-SLEN / 2, 2.6))], SZ - 0.9, SZ + 0.9, CHEESE)
FS.prism_xy([srot(u, v) for u, v in ((-SLEN * 0.37, 1.0), (SLEN * 0.37, 1.0), (SLEN * 0.37, 1.25), (-SLEN * 0.37, 1.25))], SZ - 0.8,
            SZ + 0.8, BOARD)  # шкурка-грип сверху
for k, (hx, hy, hr) in enumerate(((-4.0, 0.5, 0.4), (-1.6, 0.62, 0.28), (0.8, 0.45, 0.44), (3.0, 0.6, 0.3))):
    cx, cy = srot(hx, hy)
    FS.prism_xy(K.ngon(cx, cy, hr, 8), SZ - 0.96, SZ - 0.9, HOLE)
for e in (-1, 1):
    FS.prism_xy([srot(u, v) for u, v in ((e * 3.8 - 1.0, -0.9), (e * 3.8 + 1.0, -0.9), (e * 3.8 + 1.0, 0.0), (e * 3.8 - 1.0, 0.0))],
                SZ - 0.6, SZ + 0.6, STEEL2)
    wx, wy = srot(e * 3.8, -1.5)
    for f in (-1, 1):
        FS.prism_xy(K.ngon(wx, wy, 0.9, 10), SZ + f * 1.2 - 0.4, SZ + f * 1.2 + 0.4, "FF8A2A")
        FS.prism_xy(K.ngon(wx, wy, 0.35, 8), SZ + f * 1.2 - 0.46, SZ + f * 1.2 + 0.46, STEEL)
    FS.box(wx - 0.15, wx + 0.15, wy - 0.4, wy + 0.4, SZ + 0.4, -FZ - 0.88, STEEL2)
# слева: рампа-четвертинка с площадкой и копингом, граффити на боку
qpipe_zy(FS, -FX - 0.4, -8.0, -FZ - 0.9, -1, 6.0, 5.0, 0.0, CON3)
FS.box(-FX - 0.4, -8.0, 6.0, 6.3, -FZ - 1.3, -FZ - 0.9, STEEL2)
for x in (-FX - 0.2, -8.2):
    beam(FS, (x, 6.3, -FZ - 1.1), (x, 7.6, -FZ - 1.1), 0.14, 0.14, STEEL2)
beam(FS, (-FX - 0.2, 7.6, -FZ - 1.1), (-8.2, 7.6, -FZ - 1.1), 0.14, 0.14, STEEL2)
FS.box(-8.0, -7.9, 0.0, 6.0, -FZ - 6.0, -FZ - 0.9, CON2)
skateboard(FS, -12.5, 0.0, -FZ - 7.6, 3.6, BOARD, BOARD2, "FFD03A", along_x=True, up=0.5)
# справа: лестница с перилами, фонарь, бумбокс на ящике, конусы
for k in range(5):
    FS.box(7.0, 15.5, 0.0, 0.45 * (5 - k), -FZ - 1.0 - 0.9 * (k + 1), -FZ - 1.0 - 0.9 * k, (CON2, CON3)[k % 2])
beam(FS, (11.2, 3.2, -FZ - 1.2), (11.2, 1.0, -FZ - 5.6), 0.16, 0.16, STEEL)
for z, y in ((-FZ - 1.2, 2.25), (-FZ - 5.6, 0.0)):
    beam(FS, (11.2, y, z), (11.2, y + 1.0, z), 0.16, 0.16, STEEL2)
FS.prism_xz(K.ngon(16.4, -FZ - 3.6, 0.2, 6), 0.0, 9.0, STEEL2)
beam(FS, (16.4, 9.0, -FZ - 3.6), (15.0, 9.4, -FZ - 3.6), 0.2, 0.2, STEEL2)
FG.box(14.2, 15.4, 8.8, 9.2, -FZ - 4.0, -FZ - 3.2, NEONY)
D.crate(FS, 5.0, -FZ - 2.2, 0.0, 1.4)
FS.box(4.1, 5.9, 1.4, 2.4, -FZ - 2.6, -FZ - 1.8, BOARD)
for e in (-1, 1):
    FS.prism_xy(K.ngon(5.0 + e * 0.5, 1.9, 0.36, 8), -FZ - 2.66, -FZ - 2.6, STEEL)
FG.box(4.6, 5.4, 2.0, 2.2, -FZ - 2.68, -FZ - 2.62, NEONC)
for x, z in ((-6.0, -FZ - 3.0), (-6.8, -FZ - 4.6), (6.6, -FZ - 6.2)):
    cone(FS, x, z)
fence(FS, "z", -FZ - 6.2, -1, 7.0, 15.5, 2.4)
# тыл: морской контейнер и бочки
FS.box(-9.0, 5.0, 0.0, 5.6, FZ + 1.2, FZ + 5.0, RUST)
for k in range(15):
    x = -8.6 + 0.9 * k
    FS.box(x, x + 0.3, 0.3, 5.3, FZ + 5.0, FZ + 5.2, "8A4A2A")
for x in (7.0, 8.8):
    D.barrel(FS, x, FZ + 2.6, 0.0, 0.8, 1.7, "3A7ACF", STEEL2)

# ══ ИНТЕРЬЕР: крытый скейтпарк ════════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.4
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), CON2)
for x in (-6.0, 6.0):  # разметка
    IQ.box(x - 0.15, x + 0.15, 0.02, 0.05, -12.0, 6.0, NEONY)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 2.4, CON2)
        slab(IR, axis, fixed, out, 0.88, a0, a1, 2.4, C if not gap else DOOR[1] + 0.1, CON)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, CON)
        slab(IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, NEONP)
    else:  # промышленные окна в сетку под потолком
        gp = IG.prism_xy if axis == "z" else IG.prism_zy
        fr = IS.frame_xy if axis == "z" else IS.frame_zy
        for a in ((-10.0, 0.0, 10.0) if axis == "z" else (-9.0, 1.0)):
            lo, hi = sorted((fixed + out * 0.9, fixed + out * 0.94))
            gp(K.rect(a - 3.6, a + 3.6, 11.0, 15.4), lo, hi, "9ED8FF")
            fr(K.rect(a - 3.9, a + 3.9, 10.7, 15.7), K.rect(a - 3.6, a + 3.6, 11.0, 15.4), *sorted((fixed + out * 0.88, fixed + out * 1.2)),
               STEEL2)
            for m in (-1, 0, 1):
                slab(IS, axis, fixed, out, 1.1, a + 1.2 * m * 2 - 0.08, a + 1.2 * m * 2 + 0.08, 11.0, 15.4, STEEL2)
            slab(IS, axis, fixed, out, 1.1, a - 3.6, a + 3.6, 13.12, 13.28, STEEL2)
    for k, a in enumerate((-10.0, 0.0, 10.0) if not gap else (-11.5, 11.5)):  # граффити на стенах
        if idx == 2 and abs(a) < 1.0:
            continue
        graffiti(IS, IG, axis, fixed, out, a, 6.6, 2.4, idx * 3 + k)
for k in range(3):  # гирлянды флажков через зал
    x = -8.0 + 8.0 * k
    pts = D.chain(IS, (x, 15.0, ZF + 1.0), (x, 15.0, ZB - 2.0), 10, 0.06, STEEL2, 1.4)
    for m, q in enumerate(pts[1:-1]):
        IS.prism_zy([(q[2] - 0.6, q[1]), (q[2] + 0.6, q[1]), (q[2], q[1] - 1.2)], q[0] - 0.04, q[0] + 0.04, GR[(m + k) % 6])
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):  # цветной цоколь стен
    if idx == 3:
        continue
    n = int(2 * half // 2.4)
    for k in range(n):
        a = -half + 2.4 * k
        slab(IS, axis, fixed, out, 0.96, a + 0.05, a + 2.35, 2.4, 3.0, GR[(k + idx) % 6])
for k in range(-3, 4):  # фермы под потолком
    z = 4.4 * k
    IS.box(-W, W, C - 0.8, C - 0.5, z - 0.2, z + 0.2, STEEL2)
    for m in range(8):
        x0 = -W + 4.2 * m
        beam(IS, (x0, C - 0.65, z), (x0 + 2.1, C - 2.2, z), 0.18, 0.18, STEEL2)
        beam(IS, (x0 + 2.1, C - 2.2, z), (x0 + 4.2, C - 0.65, z), 0.18, 0.18, STEEL2)
    IS.box(-W, W, C - 2.35, C - 2.1, z - 0.15, z + 0.15, STEEL2)
# хафпайп у дальней стены с площадкой и ограждением
qpipe_zy(IS, -14.0, 14.0, ZF + 3.0, 1, 4.4, 4.2, 3.0, CON3)
IS.box(-14.0, 14.0, 4.4, 4.7, ZF, ZF + 3.0, WOOD2)
for x in range(-13, 14, 3):
    beam(IS, (x, 4.7, ZF + 0.6), (x, 6.2, ZF + 0.6), 0.14, 0.14, STEEL2)
beam(IS, (-13.0, 6.2, ZF + 0.6), (13.0, 6.2, ZF + 0.6), 0.16, 0.16, STEEL2)
# рампы-четвертинки вдоль боковых стен
for s in (-1, 1):
    qpipe_xy(IS, -9.0, 4.0, s * W, -s, 3.4, 3.2, 0.0, CON3)
# стойка с досками у лифта, скамьи, сырные табуреты, конусы, бумбокс
for s in (-1, 1):
    IS.box(s * 12.0 - 2.2, s * 12.0 + 2.2, 0.0, 0.3, 11.6, 12.4, WOOD2)
    for k in range(4):
        x = s * 12.0 - 1.5 + 1.0 * k
        skateboard(IS, x, 0.3, 12.0, 3.2, (BOARD, GR[k], GR[k + 1], BOARD2)[k], BOARD, ("FFD03A", "FF8A2A", "3AE8FF", "FFFFFF")[k],
                   along_x=False, up=1.6)
    IS.box(s * 9.0 - 2.4, s * 9.0 + 2.4, 1.2, 1.5, 7.0, 8.0, WOOD)
    for e in (-1, 1):
        IS.box(s * 9.0 + e * 2.0 - 0.15, s * 9.0 + e * 2.0 + 0.15, 0.0, 1.2, 7.2, 7.8, STEEL2)
cheese_wheel(IS, -6.0, 3.0, 0.0, 0.9, 0.9)
cheese_wheel(IS, 6.4, 2.6, 0.0, 1.0, 0.8)
cheese_wheel(IS, -12.5, -11.0, 0.0, 1.3, 1.0)
for x, z in ((4.0, 5.0), (-4.2, 5.4), (11.0, -11.6)):
    cone(IS, x, z)
skateboard(IS, -7.6, 0.0, -0.4, 3.2, BOARD2, BOARD, "FFD03A", along_x=True, up=0.32)
# фанбокс-постамент: сырная крышка, стальные кромки, пологие скаты; перила для слайда перед ним
px, pz = PED
IR.box(px - 4.0, px + 4.0, 0.0, TOP - 0.1, pz - 3.2, pz + 3.2, CON3)
for s in (-1, 1):
    IR.prism_xy([(px + s * 4.0, 0.0), (px + s * 7.0, 0.0), (px + s * 4.0, TOP - 0.1)], pz - 3.2, pz + 3.2, CON3)
IS.box(px - 3.9, px + 3.9, TOP - 0.1, TOP, pz - 3.1, pz + 3.1, ASPH2)  # тёмная крышка-«шкурка»: экспонат светлее подставки
for k, (hx, hz, hr) in enumerate(((-2.6, -1.6, 0.4), (2.4, 1.8, 0.32), (-2.8, 2.2, 0.26), (2.9, -2.0, 0.3))):
    IS.prism_xz(K.ngon(px + hx, pz + hz, hr, 8), TOP, TOP + 0.03, CHEESE)
for s in (-1, 1):
    IS.prism_zy(K.ngon(pz + s * 3.2, TOP - 0.1, 0.16, 6), px - 4.0, px + 4.0, STEEL)
    IS.prism_xy(K.ngon(px + s * 4.0, TOP - 0.1, 0.16, 6), pz - 3.2, pz + 3.2, STEEL)
beam(IS, (px - 3.0, 0.9, pz + 5.2), (px + 3.0, 0.9, pz + 5.2), 0.18, 0.18, STEEL)
for x in (-2.6, 2.6):
    beam(IS, (px + x, 0.0, pz + 5.2), (px + x, 0.9, pz + 5.2), 0.16, 0.16, STEEL2)
B.lift_leaves(IS, STEEL2, NEONC)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, CON)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, ASPH)
SL.box(-5.6, 5.6, 0.0, 9.0, -FZ - 0.4, -FZ + 0.1, STEEL2)
SL.prism_xy([srot(-SLEN / 2, 0.0), srot(SLEN / 2, 0.0), srot(SLEN / 2, 1.6), srot(-SLEN / 2, 1.6)], SZ - 0.6, SZ + 0.6, CHEESE)
SL.prism_zy([(-FZ - 6.0, 0.0), (-FZ - 0.9, 6.0), (-FZ - 0.9, 0.0)], -FX, -8.0, CON3)
for k in range(5):
    SL.box(-FX + 7.2 * k + 0.4, -FX + 7.2 * k + 3.4, 16.2, 18.5, -FZ - 0.3, -FZ + 0.1, GR[k])

F.build(exhibit=(PED[0], TOP, PED[1], 3.0), lamps=[("Hall", (0, 14, 6), 2800, (1.0, 0.97, 0.92)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.96, 0.88)),
                                                   ("Neon", (-12, 6, 0), 800, (1.0, 0.4, 0.8))])
