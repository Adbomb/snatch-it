"""Этаж «Королевская утка» музея-небоскрёба (третья партия, 2026-11-21; общий конвейер — floorbase.py).

Замысел: этаж — королевская купальня. Снаружи — белые стены с поясами голубых изразцов, синий изразцовый низ с белыми
швами, арочные окна в золочёных рамах с запотевшим стеклом, по углам — белые башенки с голубыми поясами под золотыми
луковичными куполами; спереди — огромный золотой кран (вентиль сбоку — один) льёт воду в круглую раковину-фонтан, в
ней плавают утята и пена, над краном — золотая корона, внизу — арочные двери; бока — балкончики с полосатыми
полотенцами и круглые окошки; сзади — медный котёл с трубами и паром. Внутри — купальня: белый пол с голубой каймой,
восьмиугольный бассейн с бликами, утятами и пеной, мостик от лифта к острову-постаменту, золотой кран на стене за
островом льёт струю в бассейн, золотая корона над ним, колонны с золотыми капителями, синие изразцы и арочные ниши
с полотенцами, мылом и губками.
Запуск: blender --background --factory-startup --python scripts/blender/floor_bathhouse.py -- <репо> <превью>
        [render] [export] [shot=<имя>]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorbase as B  # noqa: E402
import floorkit as K  # noqa: E402
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, beam, rng, slab, tube  # noqa: E402

TILEW, TILEW2, TILEB, TILEB2, GOLD, GOLD2 = "F2F4F8", "E2E6EE", "2E6AD8", "5A8AE8", "F2C230", "D9A21A"
WATER, WATER2, FOAM, DUCK, BEAK, COPPER = "5AB8E8", "8AD8F4", "FFFFFF", "FFD12E", "FF8A2A", "C87A4A"
TOWEL, TOWEL2, STEAMG, VELVET, SOAP = "E04A6A", "4AB0E0", "D8F0FF", "2E4AA8", "F4B8D8"

F = B.Floor("RY", "RoyalDuck", quiet=(TILEW, TILEW2, WATER), bevel_min=1.0)
FR, FS, FQ, FG, IR, IS, IQ, IG, SL = F.FR, F.FS, F.FQ, F.FG, F.IR, F.IS, F.IQ, F.IG, F.SL


def onion(p, cx, cz, r, y0):
    """Луковичный купол: профиль-луковица из колец и шпиль."""
    prof = [(1.0, 0.0), (1.18, 0.6), (1.1, 1.3), (0.8, 2.0), (0.4, 2.7), (0.12, 3.3)]
    rings = [[(cx + r * f * math.cos(2 * math.pi * k / 12), y0 + h, cz + r * f * math.sin(2 * math.pi * k / 12))
              for k in range(12)] for f, h in prof]
    for k, (a, b) in enumerate(zip(rings, rings[1:])):
        p.loft(a, b, GOLD if k % 2 == 0 else GOLD2)
    p.cone(rings[-1], (cx, min(y0 + 4.6, 18.95), cz), GOLD)


def duck(p, x, y, z, s, facing=1):
    """Утёнок-игрушка в профиль вдоль x (глаз не делаем — простая форма)."""
    p.prism_xz(K.octa(x, z, 1.0 * s, 0.7 * s, 0.35 * s), y, y + 0.8 * s, DUCK)
    p.box(x + facing * 0.35 * s - 0.4 * s, x + facing * 0.35 * s + 0.4 * s, y + 0.8 * s, y + 1.5 * s, z - 0.38 * s, z + 0.38 * s,
          DUCK)
    bx = x + facing * 0.75 * s
    p.box(min(bx, bx + facing * 0.45 * s), max(bx, bx + facing * 0.45 * s), y + 1.0 * s, y + 1.22 * s, z - 0.18 * s, z + 0.18 * s,
          BEAK)


def foam(p, x, y, z, r, seed):
    for k in range(4):
        t = 2 * math.pi * k / 4 + seed
        dx, dz = r * 0.6 * math.cos(t), r * 0.6 * math.sin(t)
        rr = r * (0.45 + 0.25 * rng(seed, k))
        p.prism_xz(K.octa(x + dx, z + dz, rr, rr, rr * 0.4), y, y + rr * 1.1, FOAM)


def arch_pts(cx, y0, w, h, n=8):
    return [(cx - w, y0)] + [(cx - w * math.cos(math.pi * k / n), y0 + h - w + w * math.sin(math.pi * k / n)) for k in range(n + 1)] + \
        [(cx + w, y0)]


# ══ ФАСАД: королевская купальня ═══════════════════════════════════════════════════════════════════════════════
B.shell_planes(F, TILEW2, TILEW2, TILEW)
for fi, (axis, fixed, out, half) in enumerate(B.FACES):
    slab(FQ, axis, fixed, out, 2.88, -half - 2.88, half + 2.88, -1.0, -0.2, TILEW2)
    slab(FR, axis, fixed, out, 1.88, -half - 1.88, half + 1.88, -0.2, 1.6, TILEB)  # синий изразцовый низ
    for k in range(int((2 * half + 3.6) // 1.0)):
        a = -half - 1.8 + 1.0 * k
        slab(FS, axis, fixed, out, 1.93, a, a + 0.06, -0.2, 1.6, TILEW)
    slab(FR, axis, fixed, out, 0.88, -half, half, 1.6, 15.6, TILEW)
    slab(FS, axis, fixed, out, 1.05, -half, half, 5.0, 5.8, TILEB)  # нижний пояс — ровная синяя полоса
    for y0 in (12.6,):  # верхний пояс изразцов ромбами
        slab(FS, axis, fixed, out, 1.05, -half, half, y0, y0 + 1.4, TILEB2)
        for k in range(int(2 * half // 1.4)):
            a = -half + 0.7 + 1.4 * k
            d0, d1 = sorted((fixed + out * 1.05, fixed + out * 1.15))
            (FS.prism_xy if axis == "z" else FS.prism_zy)([(a, y0 + 0.15), (a + 0.55, y0 + 0.7), (a, y0 + 1.25), (a - 0.55, y0 + 0.7)],
                                                          d0, d1, TILEB if k % 2 else GOLD2)
    slab(FS, axis, fixed, out, 1.8, -half - 0.4, half + 0.4, 15.6, 16.2, GOLD)  # карниз
    slab(FR, axis, fixed, out, 0.88, -half, half, 16.2, 19.0, TILEW2)
    for k in range(int(2 * half // 2.0)):  # зубчики-волны парапета
        a = -half + 1.0 + 2.0 * k
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 1.3))
        (FS.prism_xy if axis == "z" else FS.prism_zy)(arch_pts(a, 16.2, 0.9, 2.4, 4), d0, d1, TILEB2 if k % 2 else TILEW)
    for k in range(4 if axis == "z" else 4):  # арочные окна с запотевшим стеклом
        a = -half + (k + 0.5) * 2 * half / 4
        if fi == 0 and abs(a) < 10.0:
            continue
        prism = FS.prism_xy if axis == "z" else FS.prism_zy
        d0, d1 = sorted((fixed + out * 0.88, fixed + out * 1.25))
        prism(arch_pts(a, 6.8, 1.7, 5.4), d0, d1, GOLD2)
        g0, g1 = sorted((fixed + out * 1.25, fixed + out * 1.3))
        (FG.prism_xy if axis == "z" else FG.prism_zy)(arch_pts(a, 7.1, 1.35, 4.9), g0, g1, STEAMG)
        t0, t1 = sorted((fixed + out * 1.3, fixed + out * 1.38))
        prism([(a - 0.07, 7.1), (a + 0.07, 7.1), (a + 0.07, 11.8), (a - 0.07, 11.8)], t0, t1, GOLD2)
B.anchor(FR, (-21, -1, -20), (21, 19, 20))
B.anchor(FQ, (-21, -1, -20), (21, 19, 20))
# башенки по углам под луковичными куполами
for sx in (-1, 1):
    for sz in (-1, 1):
        cx, cz = sx * (FX + 1.2), sz * (FZ + 1.2)
        FR.prism_xz(K.ngon(cx, cz, 3.0, 12), -0.2, 14.0, TILEW)
        for y in (1.0, 5.0, 12.6):
            FS.prism_xz(K.ngon(cx, cz, 3.1, 12), y, y + 1.0, TILEB if y < 12 else TILEB2)
        FS.prism_xz(K.ngon(cx, cz, 3.3, 12), 13.6, 14.3, GOLD2)
        onion(FS, cx, cz, 2.4, 14.3)
# перед: золотой кран льёт воду в раковину-фонтан, корона, двери
tube(FS, [(0.0, 14.0, -FZ - 0.2), (0.0, 14.4, -FZ - 2.6), (0.0, 13.6, -FZ - 4.4), (0.0, 12.0, -FZ - 5.0)],
     [1.4, 1.3, 1.2, 1.1], 1.3, (1, 0, 0), GOLD)
FS.prism_xz(K.ngon(0.0, -FZ - 5.0, 0.9, 8), 11.4, 12.0, GOLD2)
FS.prism_zy(K.ngon(-FZ - 0.8, 14.0, 1.4, 8), -1.0, 1.0, GOLD2)  # основание крана
FS.box(1.0, 1.4, 13.6, 14.4, -FZ - 1.2, -FZ - 0.4, GOLD2)  # вентиль — один, сбоку
FS.box(1.4, 4.2, 13.8, 14.2, -FZ - 1.0, -FZ - 0.6, GOLD)
FS.prism_xz(K.octa(4.4, -FZ - 0.8, 0.45, 0.45, 0.18), 13.6, 14.4, "E04A4A")
for k in range(5):  # струя
    y0, y1 = 11.4 - 2.0 * (k + 1), 11.4 - 2.0 * k
    w = 0.7 + 0.08 * k
    FG.prism_xz(K.octa(0.0, -FZ - 5.0, w, w, w * 0.4), max(y0, 2.6), y1, WATER2 if k % 2 else STEAMG)
FS.frame_xz(K.ngon(0.0, -FZ - 5.0, 4.6, 16), K.ngon(0.0, -FZ - 5.0, 4.0, 16), -1.0, 2.6, TILEW)  # раковина (стоит на нижней кромке)
FS.prism_xz(K.ngon(0.0, -FZ - 5.0, 4.8, 16), 2.2, 2.6, GOLD2)
FS.prism_xz(K.ngon(0.0, -FZ - 5.0, 4.0, 16), -1.0, 2.2, WATER)
for k, (x, z, f) in enumerate(((-2.4, -FZ - 4.0, 1), (2.2, -FZ - 6.4, -1), (-1.0, -FZ - 7.4, 1))):
    duck(FS, x, 2.2, z, 0.8, f)
for k, (x, z) in enumerate(((1.6, -FZ - 3.6), (-2.6, -FZ - 6.6), (0.6, -FZ - 7.6))):
    foam(FS, x, 2.2, z, 0.7, k)
CROWN = [(-3.0, 15.4), (3.0, 15.4), (3.4, 18.2), (2.0, 16.8), (1.0, 18.6), (0.0, 17.0), (-1.0, 18.6), (-2.0, 16.8),
         (-3.4, 18.2)]
FS.prism_xy(CROWN, -FZ - 1.8, -FZ - 1.2, GOLD)
for x, y in ((-3.4, 18.2), (0.0, 17.4), (3.4, 18.2), (-1.0, 18.6), (1.0, 18.6)):
    FS.prism_xy(K.octa(x, y, 0.3, 0.3, 0.12), -FZ - 1.9, -FZ - 1.75, "E04A6A" if x else TILEB)
FS.prism_xy(arch_pts(-10.0, 1.6, 2.4, 7.0), -FZ - 1.5, -FZ, GOLD2)  # двери купальни — слева
FS.prism_xy(arch_pts(-10.0, 1.6, 2.0, 6.6), -FZ - 1.65, -FZ - 1.5, TILEB)
FS.box(-10.08, -9.92, 1.6, 8.6, -FZ - 1.75, -FZ - 1.6, GOLD)
FS.prism_xy(arch_pts(10.0, 6.8, 1.7, 5.4), -FZ - 1.25, -FZ, GOLD2)  # справа — окно
FG.prism_xy(arch_pts(10.0, 7.1, 1.35, 4.9), -FZ - 1.3, -FZ - 1.25, STEAMG)
# бока: балкончики с полосатыми полотенцами, круглые окошки
for s in (-1, 1):
    fx = s * FX
    for k, z in enumerate((-7.0, 7.0)):
        FS.box(fx + s * 0.9, fx + s * 3.0, 9.0, 9.4, z - 3.0, z + 3.0, TILEW2)
        for m in range(7):
            FS.box(fx + s * 2.8, fx + s * 3.0, 9.4, 10.8, z - 2.9 + 0.95 * m, z - 2.75 + 0.95 * m, GOLD2)
        FS.box(fx + s * 2.8, fx + s * 3.0, 10.8, 11.0, z - 3.0, z + 3.0, GOLD)
        for m in range(3):  # полотенца в полоску на перилах
            zz = z - 2.0 + 2.0 * m
            for q in range(3):
                FS.box(fx + s * 3.0, fx + s * 3.15, 8.0 + 0.9 * q, 8.9 + 0.9 * q, zz - 0.7, zz + 0.7,
                       (TOWEL, TILEW, TOWEL2)[(q + m) % 3])
    for z in (-14.0, 0.0, 14.0):
        FS.frame_zy(K.ngon(z, 3.4, 1.0, 10), K.ngon(z, 3.4, 0.7, 10), fx + s * 0.9, fx + s * 1.3, GOLD2)
        FG.prism_zy(K.ngon(z, 3.4, 0.72, 10), fx + s * 0.88, fx + s * 1.0, STEAMG)
# тыл: медный котёл с трубами и паром
FS.prism_xz(K.ngon(0.0, FZ + 3.0, 3.2, 12), -0.2, 9.0, COPPER)
for y in (2.0, 5.0, 8.0):
    FS.prism_xz(K.ngon(0.0, FZ + 3.0, 3.3, 12), y, y + 0.3, GOLD2)
FS.cone([(x, 9.0, z) for x, z in K.ngon(0.0, FZ + 3.0, 3.2, 12)], (0.0, 11.0, FZ + 3.0), COPPER)
for s in (-1, 1):
    tube(FS, [(s * 2.8, 6.0, FZ + 2.6), (s * 6.0, 6.0, FZ + 1.2), (s * 9.0, 10.0, FZ + 1.2)], [0.6] * 3, 0.6, (0, 0, 1), COPPER)
for k, (dx, y, r) in enumerate(((0.0, 11.8, 1.2), (0.8, 13.2, 1.0), (-0.6, 14.4, 0.8))):
    FS.prism_xz(K.octa(dx, FZ + 3.0, r, r, r * 0.4), y, y + r, TILEW)

# ══ ИНТЕРЬЕР: королевская купальня ════════════════════════════════════════════════════════════════════════════
PED = (0.0, -3.0)
TOP = 1.4
px, pz = PED
IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), TILEW)
for x0, x1, z0, z1 in ((-W, W, ZF, ZF + 0.6), (-W, W, ZB - 0.6, ZB), (-W, -W + 0.6, ZF, ZB), (W - 0.6, W, ZF, ZB)):
    IS.box(x0, x1, 0.02, 0.05, z0, z1, TILEB)  # голубая кайма
for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
    gap = idx == 3
    spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
    slab(IQ, axis, fixed, out, 0.7, -half, half, 0.0, C, TILEW)
    for a0, a1 in spans:
        slab(IR, axis, fixed, out, 0.88, a0, a1, 0.0, 5.0, TILEB)  # синие изразцы до пояса
        for k in range(int((a1 - a0) // 1.0)):
            slab(IS, axis, fixed, out, 0.93, a0 + 1.0 * k, a0 + 1.0 * k + 0.06, 0.0, 5.0, TILEW)
        for y in (1.0, 2.0, 3.0, 4.0):
            slab(IS, axis, fixed, out, 0.93, a0, a1, y - 0.03, y + 0.03, TILEW)
        slab(IS, axis, fixed, out, 1.05, a0, a1, 5.0, 5.4, GOLD2)
    if gap:
        slab(IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, 12.0, TILEB2)
    slab(IS, axis, fixed, out, 1.0, -half, half, 12.0, 12.6, GOLD)
    slab(IR, axis, fixed, out, 0.88, -half, half, 12.6, C, TILEW2)
    for k, a in enumerate((-11.0, 11.0) if not gap else (-11.0, 11.0)):  # арочные ниши с полотенцами и мылом
        if idx == 2:
            continue
        prism = IS.prism_xy if axis == "z" else IS.prism_zy
        d0, d1 = sorted((fixed + out * 0.7, fixed + out * 0.9))
        prism(arch_pts(a, 5.4, 1.8, 5.6), d0, d1, GOLD2)
        e0, e1 = sorted((fixed + out * 0.9, fixed + out * 0.95))
        prism(arch_pts(a, 5.6, 1.5, 5.2), e0, e1, TILEB2)
        nx, nz = (fixed + out * 1.4, a) if axis == "x" else (a, fixed + out * 1.4)
        for q in range(3):
            if axis == "x":
                IS.box(nx - 0.5, nx + 0.5, 5.6 + 0.5 * q, 6.05 + 0.5 * q, nz - 1.1, nz + 1.1, (TOWEL, TILEW, TOWEL2)[q])
            else:
                IS.box(nx - 1.1, nx + 1.1, 5.6 + 0.5 * q, 6.05 + 0.5 * q, nz - 0.5, nz + 0.5, (TOWEL, TILEW, TOWEL2)[q])
        IS.prism_xz(K.octa(nx, nz, 0.4, 0.28, 0.12), 7.15, 7.45, SOAP)
# бассейн: восьмиугольник с бортиком, вода с бликами, утята и пена; мостик от лифта; остров
POOL = K.octa(px, pz, 10.0, 8.0, 3.5)
IS.prism_xz(POOL, 0.02, 0.12, WATER)
for k in range(6):  # блики
    x, z = px + (rng(k, 11) - 0.5) * 14, pz + (rng(k, 12) - 0.5) * 11
    if abs(x - px) < 4.5 and abs(z - pz) < 4.5:
        continue
    IS.box(x - 1.2, x + 1.2, 0.12, 0.14, z - 0.1, z + 0.1, WATER2)
IS.frame_xz(K.octa(px, pz, 10.7, 8.7, 3.8), POOL, 0.0, 0.5, TILEW2)
IS.frame_xz(K.octa(px, pz, 10.8, 8.8, 3.85), K.octa(px, pz, 10.6, 8.6, 3.75), 0.5, 0.6, GOLD2)
for k, (x, z, f) in enumerate(((-7.0, -6.0, 1), (6.4, -8.4, -1), (-5.0, 2.0, -1), (7.2, 1.4, 1), (-2.0, -9.6, 1))):
    duck(IS, x, 0.12, z, 0.9, f)
for k, (x, z) in enumerate(((-8.0, -1.0), (8.0, -4.0), (4.6, -9.6), (-6.4, -9.2))):
    foam(IS, x, 0.12, z, 0.9, k + 3)
IS.box(-2.2, 2.2, 0.0, 0.55, pz + 3.0, pz + 8.9, TILEW2)  # мостик
for s in (-1, 1):
    for k in range(4):
        z = pz + 3.4 + 1.6 * k
        IS.box(s * 2.2 - 0.12, s * 2.2 + 0.12, 0.55, 1.8, z - 0.12, z + 0.12, GOLD2)
    IS.box(s * 2.2 - 0.12, s * 2.2 + 0.12, 1.8, 1.95, pz + 3.2, pz + 8.6, GOLD)
IR.prism_xz(K.ngon(px, pz, 4.0, 16), 0.0, 0.7, TILEW2)  # остров-постамент
IR.prism_xz(K.ngon(px, pz, 3.3, 16), 0.7, TOP, TILEW)
IS.frame_xz(K.ngon(px, pz, 4.1, 16), K.ngon(px, pz, 4.0, 16), 0.5, 0.7, GOLD)
IQ.prism_xz(K.ngon(px, pz, 3.0, 16), TOP - 0.1, TOP + 0.02, VELVET)
# золотой кран на стене за островом, струя в бассейн, корона над краном
tube(IS, [(0.0, 9.0, ZF + 0.9), (0.0, 9.4, ZF + 2.6), (0.0, 8.6, ZF + 3.8), (0.0, 7.4, ZF + 4.2)], [1.1, 1.0, 0.95, 0.9], 1.0,
     (1, 0, 0), GOLD)
IS.prism_zy(K.ngon(ZF + 1.2, 9.0, 1.1, 12), -0.8, 0.8, GOLD2)
for k in range(4):
    y0, y1 = 7.4 - 1.8 * (k + 1), 7.4 - 1.8 * k
    IG.prism_xz(K.octa(0.0, ZF + 4.2, 0.5, 0.5, 0.2), max(y0, 0.12), y1, WATER2 if k % 2 else STEAMG)
foam(IS, 0.0, 0.12, ZF + 4.4, 1.0, 9)
IS.prism_xy(CROWN, ZF + 0.9, ZF + 1.3, GOLD)
for x, y in ((-3.4, 18.2), (0.0, 17.4), (3.4, 18.2)):
    IS.prism_xy(K.octa(x, y - 0.6, 0.32, 0.32, 0.13), ZF + 1.3, ZF + 1.42, "E04A6A")
# колонны с золотыми капителями у бассейна
for x, z in ((-12.4, -12.4), (12.4, -12.4), (-12.4, 6.4), (12.4, 6.4)):
    IS.prism_xz(K.ngon(x, z, 1.1, 12), 0.0, 0.8, GOLD2)
    IR.prism_xz(K.ngon(x, z, 0.8, 12), 0.8, 11.0, TILEW)
    for y in (3.0, 7.0):
        IS.prism_xz(K.ngon(x, z, 0.86, 12), y, y + 0.5, TILEB)
    IS.prism_xz(K.ngon(x, z, 1.3, 12), 11.0, 12.0, GOLD)
# губки и подставка с мылом у лифта
for x, z, col in ((-7.0, 11.0, "FFE060"), (7.4, 10.6, "FF9AC8")):
    IS.box(x - 0.9, x + 0.9, 0.0, 0.8, z - 0.6, z + 0.6, col)
IS.box(9.6, 12.4, 0.0, 2.4, 12.6, 14.6, GOLD2)
for k in range(3):
    IS.box(9.9 + 0.9 * k, 10.6 + 0.9 * k, 2.4, 2.8, 13.0, 14.2, (SOAP, "A8E8C8", "F8E0A0")[k])
B.lift_leaves(IS, TILEB, GOLD)
B.anchor(IR, (-17, 0, -16), (17, 18, 16))
B.anchor(IQ, (-17, 0, -16), (17, 18, 16))

# ══ СИЛУЭТ ════════════════════════════════════════════════════════════════════════════════════════════════════
SL.box(-FX, FX, -1, 19, -FZ, FZ, TILEW)
SL.box(-FX - 1.9, FX + 1.9, -1.0, 1.6, -FZ - 1.9, FZ + 1.9, TILEB)
SL.box(-FX - 0.4, FX + 0.4, 15.6, 16.2, -FZ - 1.8, FZ + 1.8, GOLD)
for sx in (-1, 1):
    for sz in (-1, 1):
        cx, cz = sx * (FX + 1.2), sz * (FZ + 1.2)
        SL.prism_xz(K.octa(cx, cz, 3.0, 3.0, 1.2), -0.2, 14.3, TILEW)
        SL.prism_xz(K.octa(cx, cz, 2.6, 2.6, 1.0), 14.3, 17.6, GOLD)
SL.box(-1.2, 1.2, 11.4, 15.0, -FZ - 5.6, -FZ, GOLD)
SL.prism_xz(K.octa(0.0, -FZ - 5.0, 4.8, 4.8, 2.0), -0.2, 2.6, TILEW)
SL.box(-3.4, 3.4, 15.4, 18.6, -FZ - 1.8, -FZ - 1.2, GOLD)

F.build(mlf=1, tol=0.16, exhibit=(PED[0], TOP, PED[1], 2.8), lamps=[("Hall", (0, 14, 6), 3000, (0.92, 0.96, 1.0)),
                                                   ("Spot", (0, 13, -3), 3200, (1.0, 0.98, 0.92))])
