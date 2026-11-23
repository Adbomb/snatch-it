"""Этаж «Кристальный хот-дог» музея-небоскрёба (четвёртая партия, 2026-11-22; общий конвейер — floorbase.py).

Замысел: этаж — ночной рынок уличной еды. Снаружи — кирпичная стена с гирляндами лампочек, на крыше — огромная
вывеска-хот-дог: булка, сосиска, зигзаг горчицы и кетчупа, вокруг неё сверкают кристаллы; внизу — киоск-прилавок
с полосатым красно-жёлтым навесом, окошком выдачи и меню-досками, по бокам — гигантские бутылки кетчупа и
горчицы-колонны; у прилавка — высокие столики и табуреты; бок — фургон с едой; другой бок — ящики с булками и
бочки; сзади — граффити-полосы и пожарная лестница. Внутри — рыночная улица под звёздным небом: прилавки с
навесами вдоль стен, гирлянды лампочек крест-накрест, столы для пикника с зонтиками, кристаллы-друзы как
украшения, ящики с булками; экспонат — на круглом постаменте, усыпанном кристаллами.
Запуск: blender --background --factory-startup --python scripts/blender/floor_hotdog.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floordecor as D  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, ring_y, rng, slab, taper, tube  # noqa: E402

BRICK, BRICK2, BRICK3, MORTAR, ASPH, ASPH2 = "B0503A", "8E3E2E", "C86A4E", "6A4A40", "3A3A44", "4E4E5A"
BUN, BUN2, SAUS, SAUS2, MUST, KETCH = "F4C070", "D89A48", "E0603E", "B8482E", "FFD42A", "E8302A"
STRIPE_R, STRIPE_Y, WOOD, WOOD2, STEEL, STEEL2 = "E8402E", "FFD84A", "B8844A", "8A6234", "B8BCC4", "8A8E98"
CRYS, CRYS2, CRYS3, BULB, NIGHT, NIGHT2 = "FF6AB8", "7AE8FF", "C89AFF", "FFE8A0", "1A1E40", "2A3060"
TRUCK, TRUCK2, BOARD, WHITE, GREEN = "4AB8D8", "2E8AA8", "2E3A2E", "F4F4F4", "4AA84A"

F = B.Floor("HD", "CrystalHotDog", quiet=(ASPH, ASPH2, NIGHT, NIGHT2), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def crystal(p, g, x, y, z, h, color, lean=(0.0, 0.0)):
    r = h * 0.2
    top = (x + lean[0], y + h * 0.7, z + lean[1])
    p.loft([(x + r * math.cos(t), y, z + r * math.sin(t)) for t in [2 * math.pi * k / 6 for k in range(6)]],
           [(top[0] + r * math.cos(t), top[1], top[2] + r * math.sin(t)) for t in [2 * math.pi * k / 6 for k in range(6)]], color)
    g.cone([(top[0] + r * math.cos(t), top[1], top[2] + r * math.sin(t)) for t in [2 * math.pi * k / 6 for k in range(6)]],
           (top[0] + lean[0] * 0.3, y + h, top[2] + lean[1] * 0.3), color)


def hotdog(p, cx, cy, cz, L, s):
    """Хот-дог вдоль x: булка (две половинки), сосиска с закруглёнными концами, зигзаги горчицы и кетчупа."""
    for e in (-1, 1):
        p.box(cx - L / 2, cx + L / 2, cy - 0.8 * s, cy + 0.5 * s, cz + e * 0.55 * s - 0.55 * s, cz + e * 0.55 * s + 0.55 * s, BUN)
        p.box(cx - L / 2 + 0.4 * s, cx + L / 2 - 0.4 * s, cy + 0.5 * s, cy + 0.8 * s, cz + e * 0.55 * s - 0.45 * s,
              cz + e * 0.55 * s + 0.45 * s, BUN)
    p.box(cx - L / 2 - 0.1, cx + L / 2 + 0.1, cy - 0.9 * s, cy - 0.7 * s, cz - 1.1 * s, cz + 1.1 * s, BUN2)
    p.box(cx - L / 2 - 0.9 * s, cx + L / 2 + 0.9 * s, cy + 0.2 * s, cy + 1.1 * s, cz - 0.5 * s, cz + 0.5 * s, SAUS)
    for e in (-1, 1):
        p.prism_zy(K.octa(cz, cy + 0.65 * s, 0.5 * s, 0.45 * s, 0.2 * s), *sorted((cx + e * (L / 2 + 0.9 * s), cx + e * (L / 2 + 1.3 * s))),
                   SAUS2)
    n = int(L / (1.2 * s))
    for k, col in ((0, MUST), (1, KETCH)):
        for m in range(n):
            x0 = cx - L / 2 + L * m / n + k * 0.3 * s
            x1 = x0 + L / n
            dz = 0.25 * s if m % 2 else -0.25 * s
            beam(p, (x0, cy + 1.15 * s + 0.06 * k, cz - dz), (x1, cy + 1.15 * s + 0.06 * k, cz + dz), 0.22 * s, 0.14 * s, col)


def bottle(p, x, z, y, h, body, cap):
    """Мягкая бутылка соуса: корпус, плечики, носик-конус."""
    r = h * 0.17
    p.prism_xz(K.ngon(x, z, r, 10), y, y + h * 0.72, body)
    p.loft([(x + r * math.cos(t), y + h * 0.72, z + r * math.sin(t)) for t in [2 * math.pi * k / 10 for k in range(10)]],
           [(x + r * 0.5 * math.cos(t), y + h * 0.82, z + r * 0.5 * math.sin(t)) for t in [2 * math.pi * k / 10 for k in range(10)]], body)
    p.prism_xz(K.ngon(x, z, r * 0.55, 10), y + h * 0.82, y + h * 0.88, cap)
    p.cone([(x + r * 0.3 * math.cos(t), y + h * 0.88, z + r * 0.3 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]],
           (x, y + h, z), cap)
    p.prism_xz(K.ngon(x, z, r * 1.02, 10), y + h * 0.3, y + h * 0.5, WHITE)


def stall(p, g, axis, fixed, out, a0, a1, colors, seed):
    """Прилавок у стены: стойка, полосатый навес, лампочки, товары на прилавке."""
    lo0, hi0 = sorted((fixed + out * 0.88, fixed + out * 3.2))
    if axis == "x":
        p.box(lo0, hi0, 0.0, 3.0, a0, a1, WOOD2)
        p.box(*sorted((fixed + out * 0.88, fixed + out * 3.4)), 3.0, 3.3, a0 - 0.1, a1 + 0.1, WOOD)
    else:
        p.box(a0, a1, 0.0, 3.0, lo0, hi0, WOOD2)
        p.box(a0 - 0.1, a1 + 0.1, 3.0, 3.3, *sorted((fixed + out * 0.88, fixed + out * 3.4)), WOOD)
    n = int((a1 - a0) / 1.4)
    for k in range(n):  # навес полосами
        b0 = a0 + (a1 - a0) * k / n
        b1 = a0 + (a1 - a0) * (k + 1) / n
        if axis == "x":
            p.loft(
                [(fixed + out * 0.88, 8.6, b0), (fixed + out * 0.88, 8.6, b1), (fixed + out * 4.4, 7.0, b1), (fixed + out * 4.4, 7.0, b0)],
                [(fixed + out * 0.88, 8.9, b0), (fixed + out * 0.88, 8.9, b1), (fixed + out * 4.4, 7.3, b1), (fixed + out * 4.4, 7.3, b0)],
                colors[k % 2])
        else:
            p.loft([(b0, 8.6, fixed + out * 0.88), (b1, 8.6, fixed + out * 0.88), (b1, 7.0, fixed + out * 4.4), (b0, 7.0, fixed + out * 4.4)],
                   [(b0, 8.9, fixed + out * 0.88), (b1, 8.9, fixed + out * 0.88), (b1, 7.3, fixed + out * 4.4), (b0, 7.3, fixed + out * 4.4)],
                   colors[k % 2])
    for k in range(n + 1):
        b = a0 + (a1 - a0) * k / n
        if axis == "x":
            g.prism_xz(K.octa(fixed + out * 4.4, b, 0.16, 0.16, 0.06), 6.7, 7.0, BULB)
        else:
            g.prism_xz(K.octa(b, fixed + out * 4.4, 0.16, 0.16, 0.06), 6.7, 7.0, BULB)
    for e in (a0 + 0.2, a1 - 0.2):  # стойки навеса
        if axis == "x":
            p.box(*sorted((fixed + out * 4.2, fixed + out * 4.5)), 0.0, 7.0, e - 0.15, e + 0.15, WOOD)
        else:
            p.box(e - 0.15, e + 0.15, 0.0, 7.0, *sorted((fixed + out * 4.2, fixed + out * 4.5)), WOOD)
    for k in range(int((a1 - a0) / 2.4)):  # хот-доги на прилавке
        b = a0 + 1.2 + 2.4 * k
        if axis == "x":
            p.box(*sorted((fixed + out * 1.6, fixed + out * 2.6)), 3.3, 3.8, b - 0.4, b + 0.4, (BUN, SAUS, CRYS2)[int(rng(seed, k) * 3)])
        else:
            p.box(b - 0.4, b + 0.4, 3.3, 3.8, *sorted((fixed + out * 1.6, fixed + out * 2.6)), (BUN, SAUS, CRYS2)[int(rng(seed, k) * 3)])


def picnic(p, x, z, umb_col):
    """Стол для пикника с лавками и зонтом."""
    p.box(x - 2.0, x + 2.0, 2.4, 2.7, z - 1.0, z + 1.0, WOOD)
    for e in (-1, 1):
        p.box(x - 2.0, x + 2.0, 1.3, 1.6, z + e * 1.8 - 0.4, z + e * 1.8 + 0.4, WOOD)
        for f in (-1, 1):
            beam(p, (x + f * 1.6, 0.0, z + e * 2.0), (x + f * 1.6, 2.4, z - e * 0.3), 0.2, 0.2, WOOD2)
    p.prism_xz(K.ngon(x, z, 0.1, 6), 2.7, 7.4, STEEL)
    p.cone([(x + 3.0 * math.cos(t), 7.0, z + 3.0 * math.sin(t)) for t in [2 * math.pi * k / 8 for k in range(8)]], (x, 8.4, z), umb_col)


# ══ ФАСАД: киоск хот-догов на рынке ═══════════════════════════════════════════════════════════════════════════
B.shell_planes(F, BRICK, BRICK, NIGHT)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.2, ASPH)
    slab(FR, axis, fixed, out, 1.88, -half - 0.4, half + 0.4, -0.2, 1.0, ASPH2)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.0, 15.0, BRICK)
    for r in range(7):  # кирпичная кладка поясами
        y = 1.0 + 2.0 * r
        off = 1.0 if r % 2 else 0.0
        n = int(2 * half // 2.0)
        for k in range(n):
            a = -half + off + 2.0 * k
            if a + 1.9 > half or rng(fi, r, k) < 0.55:
                continue
            if fi == 0 and a + 1.92 > -8.2 and a + 0.08 < 8.2 and y + 0.92 > 4.4 and y + 0.08 < 9.6:
                continue  # не закрывать окошко выдачи
            slab(FR, axis, fixed, out, 1.08, a + 0.08, a + 1.92, y + 0.08, y + 0.92, (BRICK2, BRICK3)[(k + r) % 2])
    slab(FR, axis, fixed, out, 1.88, -half - 0.6, half + 0.6, 15.0, 16.0, MORTAR)
    slab(FR, axis, fixed, out, 0.88, -half, half, 16.0, 18.9, BRICK2)
    if fi != 0:  # гирлянды лампочек на остальных стенах
        lo = fixed + out * 1.3
        for row in (12.0,):
            pts = D.chain(FS, *(((lo, row, -half + 1.0), (lo, row, half - 1.0)) if axis == "x" else ((-half + 1.0, row, lo), (half - 1.0, row, lo))),
                          8, 0.08, "2A2A30", 1.0)
            for q in pts[1:-1]:
                FG.prism_xz(K.octa(q[0], q[2], 0.2, 0.2, 0.08), q[1] - 0.45, q[1] - 0.05, BULB)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# перед: киоск — прилавок с окошком, полосатый навес, меню-доски
FS.box(-10.0, 10.0, 1.0, 4.2, -FZ - 2.6, -FZ, STEEL2)
FS.box(-10.3, 10.3, 4.2, 4.6, -FZ - 3.0, -FZ, STEEL)
FS.box(-8.0, 8.0, 4.6, 9.4, -FZ - 0.95, -FZ - 0.88, "2A2018")
FG.box(-7.6, 7.6, 5.0, 9.0, -FZ - 1.0, -FZ - 0.95, "FFE8B8")
for k in range(3):  # меню-доски
    x = -5.0 + 5.0 * k
    FS.box(x - 2.0, x + 2.0, 10.0, 12.6, -FZ - 1.1, -FZ - 0.88, BOARD)
    for m in range(3):
        FS.box(x - 1.6, x + 1.6 * (0.4 + 0.5 * rng(k, m)), 10.4 + 0.7 * m, 10.6 + 0.7 * m, -FZ - 1.16, -FZ - 1.1, (WHITE, MUST, CRYS2)[m])
for k in range(14):  # полосатый навес
    x0 = -10.5 + 1.5 * k
    FS.loft([(x0, 9.6, -FZ - 0.9), (x0 + 1.5, 9.6, -FZ - 0.9), (x0 + 1.5, 8.0, -FZ - 4.6), (x0, 8.0, -FZ - 4.6)],
            [(x0, 9.9, -FZ - 0.9), (x0 + 1.5, 9.9, -FZ - 0.9), (x0 + 1.5, 8.3, -FZ - 4.6), (x0, 8.3, -FZ - 4.6)], (STRIPE_R, STRIPE_Y)[k % 2])
    FS.prism_xy([(x0, 8.0), (x0 + 1.5, 8.0), (x0 + 0.75, 7.2)], -FZ - 4.7, -FZ - 4.6, (STRIPE_R, STRIPE_Y)[k % 2])
# огромная вывеска-хот-дог на крыше и кристаллы вокруг
def sign_hotdog(p, cx, cy, z0, L, s):
    """Вывеска-хот-дог в профиль, лицом к −Z: задняя половина булки, сосиска с закруглёнными концами, передняя
    половина булки, зигзаг горчицы и кетчупа по сосиске."""
    def capsule(x0, x1, y0, y1, n=6):
        r = (y1 - y0) / 2
        pts = [(x1 - r + r * math.cos(t), y0 + r + r * math.sin(t)) for t in [-math.pi / 2 + math.pi * k / n for k in range(n + 1)]]
        pts += [(x0 + r + r * math.cos(t), y0 + r + r * math.sin(t)) for t in [math.pi / 2 + math.pi * k / n for k in range(n + 1)]]
        return pts
    p.prism_xy(capsule(cx - L / 2, cx + L / 2, cy - 1.2 * s, cy + 1.0 * s), z0 - 0.6 * s, z0, BUN2)       # задняя булка
    p.prism_xy(capsule(cx - L / 2 - 1.2 * s, cx + L / 2 + 1.2 * s, cy - 0.2 * s, cy + 1.3 * s), z0 - 1.4 * s, z0 - 0.6 * s, SAUS)
    p.prism_xy(capsule(cx - L / 2 + 0.2, cx + L / 2 - 0.2, cy - 1.3 * s, cy + 0.05 * s), z0 - 2.0 * s, z0 - 1.0 * s, BUN)  # передняя
    n = int(L / (0.9 * s))
    for k, (col, dy) in enumerate(((MUST, 0.85), (KETCH, 0.6))):
        pts = [(cx - L / 2 + L * m / n, cy + dy * s + (0.22 * s if (m + k) % 2 else -0.22 * s)) for m in range(n + 1)]
        for q0, q1 in zip(pts, pts[1:]):
            beam(p, (q0[0], q0[1], z0 - 1.48 * s - 0.06 * k), (q1[0], q1[1], z0 - 1.48 * s - 0.06 * k), 0.26 * s, 0.14 * s, col,
                 up=(0, 0, 1))


sign_hotdog(FS, 0.0, 15.6, -FZ - 0.9, 13.0, 2.0)
for k, (x, y, col) in enumerate(((-11.0, 15.2, CRYS), (11.2, 15.6, CRYS2), (-13.4, 14.4, CRYS3), (13.6, 14.0, CRYS))):
    crystal(FS, FG, x, y, -FZ - 1.8, 2.4 + 0.6 * (k % 2), col, (0.3 * (1 if x > 0 else -1), 0.0))
for k in range(8):  # искры
    x = -12.0 + 24.0 * rng(k, 91)
    y = 12.6 + 6.0 * rng(k, 92)
    s = 0.2 + 0.2 * rng(k, 93)
    FG.prism_xy([(x, y + s * 2), (x + s * 0.4, y + s * 0.4), (x + s * 2, y), (x + s * 0.4, y - s * 0.4), (x, y - s * 2),
                 (x - s * 0.4, y - s * 0.4), (x - s * 2, y), (x - s * 0.4, y + s * 0.4)], -FZ - 3.2, -FZ - 3.1, (WHITE, CRYS2)[k % 2])
# гигантские бутылки кетчупа и горчицы по бокам киоска
bottle(FS, -13.4, -FZ - 2.4, -0.2, 12.0, KETCH, WHITE)
bottle(FS, 13.4, -FZ - 2.4, -0.2, 12.0, MUST, KETCH)
# высокие столики и табуреты перед киоском
for x in (-6.0, 6.0):
    FS.prism_xz(K.ngon(x, -FZ - 6.0, 0.15, 6), -0.2, 3.0, STEEL2)
    FS.prism_xz(K.ngon(x, -FZ - 6.0, 1.0, 10), 3.0, 3.25, WOOD)
    for e in (-1.6, 1.6):
        FS.prism_xz(K.ngon(x + e, -FZ - 6.0, 0.1, 6), -0.2, 1.9, STEEL2)
        FS.prism_xz(K.ngon(x + e, -FZ - 6.0, 0.55, 8), 1.9, 2.2, STRIPE_R)
# бок: фургон с едой (справа), ящики с булками и бочки (слева)
tx = FX + 2.2
FS.box(tx - 1.2, tx + 1.2, 1.2, 7.4, -10.0, 2.0, TRUCK)
FS.box(tx - 1.2, tx + 1.2, 7.4, 7.8, -10.2, 2.2, TRUCK2)
FG.box(tx + 1.2, tx + 1.26, 3.4, 6.4, -7.6, -1.0, "FFE8B8")
FS.loft([(tx + 1.2, 6.8, -8.0), (tx + 1.2, 6.8, -0.6), (tx + 3.0, 6.0, -0.6), (tx + 3.0, 6.0, -8.0)],
        [(tx + 1.2, 7.1, -8.0), (tx + 1.2, 7.1, -0.6), (tx + 3.0, 6.3, -0.6), (tx + 3.0, 6.3, -8.0)], STRIPE_Y)
for z in (-8.0, 0.0):
    FS.prism_zy(K.ngon(z, 1.2, 1.0, 10), tx - 1.3, tx + 1.3, "26262E")
for k, z in enumerate((6.0, 8.0, 7.0)):
    D.crate(FS, tx, z, -0.2 + (1.2 if k == 2 else 0.0), 1.2, WOOD, WOOD2)
for z in (11.0, 12.6):
    D.barrel(FS, tx, z, -0.2, 0.7, 1.6, WOOD, "3A3A40")
for k, z in enumerate((-8.0, 0.0, 8.0)):
    D.crate(FS, -tx, z, -0.2, 1.4, BUN, BUN2)
# сзади: пожарная лестница
for k in range(4):
    y = 3.0 + 3.8 * k
    FS.box(-6.0, 0.0, y, y + 0.2, FZ + 0.88, FZ + 2.4, STEEL2)
    for m in range(7):
        FS.box(-6.0 + m, -5.9 + m, y + 0.2, y + 1.4, FZ + 2.3, FZ + 2.4, STEEL)
    FS.box(-6.0, 0.0, y + 1.3, y + 1.4, FZ + 2.3, FZ + 2.4, STEEL)

# ══ ИНТЕРЬЕР: рыночная улица под звёздами ═════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.4
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), ASPH)
for k in range(-3, 4):  # разметка-плиты
    IQ.box(-1.6, 1.6, 0.0, 0.08, 4.0 * k - 1.6, 4.0 * k + 1.6, ASPH2)
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 9.0 if not gap else DOOR[1] + 0.1, BRICK)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 9.0, BRICK)
        slab(IG, axis, fixed, out, 1.0, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.3, DOOR[1] + 0.6, CRYS2)
    slab(IR, axis, fixed, out, 1.2, -half, half, 9.0, 9.4, MORTAR)
    slab(IQ, axis, fixed, out, 0.88, -half, half, 9.4, 13.0, NIGHT2)
    slab(IQ, axis, fixed, out, 0.88, -half, half, 13.0, C, NIGHT)
for k in range(36):  # звёзды
    x = -W + 1.0 + (2 * W - 2.0) * rng(k, 101)
    z = ZF + 1.0 + (ZB - ZF - 2.0) * rng(k, 102)
    s = 0.1 + 0.12 * rng(k, 103)
    IG.box(x - s, x + s, C - 0.05, C - 0.01, z - s, z + s, BULB)
# прилавки вдоль боковых стен и передней
for s in (-1, 1):
    stall(IS, IG, "x", s * W, -s, -14.0, -6.0, (STRIPE_R, WHITE) if s < 0 else (CRYS3, WHITE), 1 + s)
    stall(IS, IG, "x", s * W, -s, 0.0, 8.0, (GREEN, WHITE) if s < 0 else (STRIPE_Y, STRIPE_R), 5 + s)
for a0, a1, cols in ((-15.0, -6.0, (TRUCK, WHITE)), (6.0, 15.0, (STRIPE_R, STRIPE_Y))):
    stall(IS, IG, "z", ZF, 1, a0, a1, cols, int(a0))
# гирлянды лампочек крест-накрест
for a, b in (((-W + 1.0, 14.0, ZF + 1.0), (W - 1.0, 14.0, ZB - 4.0)), ((W - 1.0, 14.0, ZF + 1.0), (-W + 1.0, 14.0, ZB - 4.0)),
             ((-W + 1.0, 12.6, -2.0), (W - 1.0, 12.6, -2.0))):
    pts = D.chain(IS, a, b, 12, 0.07, "2A2A30", 1.4)
    for q in pts[1:-1]:
        IG.prism_xz(K.octa(q[0], q[2], 0.2, 0.2, 0.08), q[1] - 0.45, q[1] - 0.05, BULB)
# столы для пикника с зонтами у лифта, ящики с булками, кристаллы-друзы
picnic(IS, -9.0, 8.0, STRIPE_R)
picnic(IS, 9.5, 8.0, CRYS3)
for k, (x, z) in enumerate(((-14.0, 12.4), (-12.6, 12.4), (13.6, 12.6))):
    D.crate(IS, x, z, 0.0, 1.3, BUN, BUN2)
for x, z, cols in ((-5.6, -12.6, (CRYS, CRYS3)), (5.8, -12.8, (CRYS2, CRYS)), (-13.8, -3.0, (CRYS3, CRYS2)), (13.6, -2.6, (CRYS, CRYS2))):
    for k in range(3):
        t = 2 * math.pi * k / 3
        crystal(IS, IG, x + 0.6 * math.cos(t), 0.0, z + 0.6 * math.sin(t), 1.6 + 0.8 * rng(x, k), cols[k % 2],
                (0.4 * math.cos(t), 0.4 * math.sin(t)))
# круглый постамент, усыпанный кристаллами
px, pz = PED
IR.prism_xz(K.ngon(px, pz, 4.0, 12), 0.0, 0.6, NIGHT2)
IR.prism_xz(K.ngon(px, pz, 3.3, 12), 0.6, TOP, "3A3E7A")
ring_y(IS, px, pz, 3.3, 3.5, 0.6, TOP + 0.08, STEEL, n=12)
for k in range(10):
    t = 2 * math.pi * k / 10
    crystal(IS, IG, px + 3.7 * math.cos(t), 0.6, pz + 3.7 * math.sin(t), 0.9 + 0.5 * (k % 2), (CRYS, CRYS2, CRYS3)[k % 3],
            (0.3 * math.cos(t), 0.3 * math.sin(t)))
B.lift_leaves(IS, STEEL2, STRIPE_R)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, BRICK)
SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.2, -FZ - 2.9, FZ + 2.9, ASPH)
SL.box(-FX - 1.9, FX + 1.9, 15.0, 16.0, -FZ - 1.9, FZ + 1.9, MORTAR)
SL.box(-7.6, 7.6, 15.2, 18.2, -FZ - 3.7, -FZ - 2.1, SAUS)
SL.box(-7.0, 7.0, 13.0, 16.3, -FZ - 4.9, -FZ - 2.9, BUN)
SL.box(-10.5, 10.5, 8.0, 9.9, -FZ - 4.6, -FZ - 0.9, STRIPE_R)

F.build(exhibit=(PED[0], TOP, PED[1], 2.4), lamps=[("Hall", (0, 14, 6), 2600, (1.0, 0.9, 0.8)),
                                                   ("Spot", (0, 13, -3), 3400, (1.0, 0.96, 0.9)),
                                                   ("Bulbs", (0, 11, 4), 900, (1.0, 0.85, 0.5))])
