"""Общий каркас этажей партий 9–11 (2026-11-22): стены, цоколь, карниз, крыша, окна боков, стены и потолок зала,
силуэт. Своё у каждого этажа — передний фасад, убранство зала, постамент: их пишет скрипт этажа.
Зависит от floorbase (оси, slab, chamfer, FACES, WALLS) и floorkit (контуры)."""

import math

import floorbase as B
import floorkit as K
from floorbase import C, DOOR, FX, FZ, W, ZB, ZF, slab

TOP = 16.6  # верх стены до карниза


def window(F, axis, fixed, out, a, y0, y1, w, frame, glass, kind="rect", mull=True):
    """Окно на стене: стекло на плоскости, рама наружу; kind — rect | arch | slit | tall."""
    d0, d1 = sorted((fixed + out * 0.88, fixed + out * 0.92))
    f0, f1 = sorted((fixed + out * 0.88, fixed + out * 1.1))
    pr, fr = (F.FG.prism_zy, F.FS.frame_zy) if axis == "x" else (F.FG.prism_xy, F.FS.frame_xy)
    if kind == "arch":
        r = w / 2
        n = 6
        inner = [(a, y0), (a + w, y0)] + [(a + r + r * math.cos(math.pi * k / n), y1 - r + r * math.sin(math.pi * k / n))
                                          for k in range(n + 1)]
        outer = [(a - 0.3, y0 - 0.3), (a + w + 0.3, y0 - 0.3)] + [
            (a + r + (r + 0.3) * math.cos(math.pi * k / n), y1 - r + (r + 0.3) * math.sin(math.pi * k / n)) for k in range(n + 1)]
        pr(inner, d0, d1, glass)
        fr(outer, inner, f0, f1, frame)
    else:
        pr(K.rect(a, a + w, y0, y1), d0, d1, glass)
        fr(K.rect(a - 0.3, a + w + 0.3, y0 - 0.3, y1 + 0.3), K.rect(a, a + w, y0, y1), f0, f1, frame)
        if mull and kind != "slit":
            slab(F.FS, axis, fixed, out, 1.0, a + w / 2 - 0.06, a + w / 2 + 0.06, y0, y1, frame)
            if kind == "rect":
                slab(F.FS, axis, fixed, out, 1.0, a, a + w, (y0 + y1) / 2 - 0.06, (y0 + y1) / 2 + 0.06, frame)


def _span(axis, half, depth, a0=None, a1=None):
    """Пояс вокруг здания без зазоров и наложений на углах: передняя и задняя стороны (z) выходят на глубину пояса
    за углы, боковые (x) кончаются у задней кромки соседних — грани углов встык, совпадающих граней нет."""
    if axis == "z":
        return -half - depth, half + depth
    return -half + 0.05, half - 0.05


def facade(F, wall, base, cornice, ground, ceil, roof="flat", roof_col=None, pilaster=None, band=None,
           side=None, top=TOP, boards=None):
    """Стены снаружи на всех четырёх сторонах. roof — flat (парапет), hip (скат к центру), crenel (зубцы),
    none (только карниз). side(axis, fixed, out, half) — убранство боков и тыла. boards — (шаг, цвет) вертикальных
    досок/рустов. Возвращает верх стен (для силуэта)."""
    B.shell_planes(F, wall, wall, ceil)
    rc = roof_col or cornice
    for fi, (axis, fixed, out, half) in enumerate(B.FACES):
        slab(F.FQ, axis, fixed, out, 2.88, *_span(axis, half, 2.88), -1.0, -0.1, ground)
        slab(F.FR, axis, fixed, out, 1.18, *_span(axis, half, 1.18), -0.1, 1.0, base)
        slab(F.FR, axis, fixed, out, 0.88, *_span(axis, half, 0.88), 1.0, top, wall)
        if boards:
            step, col = boards
            for k in range(int(2 * half // step)):
                a = -half + step / 2 + step * k
                slab(F.FS, axis, fixed, out, 0.94, a - 0.05, a + 0.05, 1.0, top, col)
        if pilaster:
            e = 1.18 if axis == "z" else -0.05  # угловые лопатки охватывают угол
            for a0, a1 in ((-half - e, -half + 1.0), (half - 1.0, half + e)):
                slab(F.FR, axis, fixed, out, 1.18, a0, a1, 1.0, top, pilaster)
        if band:
            y0, y1, col = band
            slab(F.FR, axis, fixed, out, 1.02, *_span(axis, half, 1.02), y0, y1, col)
        slab(F.FR, axis, fixed, out, 1.38, *_span(axis, half, 1.38), top, top + 0.7, cornice)
        if roof == "flat":
            slab(F.FR, axis, fixed, out, 1.0, *_span(axis, half, 1.0), top + 0.7, 18.3, rc)
            slab(F.FR, axis, fixed, out, 1.2, *_span(axis, half, 1.2), 18.3, 18.9, cornice)
        elif roof == "hip":
            B.chamfer(F.FR, axis, fixed, out, -half - 1.4, half + 1.4,
                      [(0.88, 18.9), (2.2, top + 0.7), (2.2, top + 0.5), (0.88, top + 0.5)], rc)
        elif roof == "crenel":
            slab(F.FR, axis, fixed, out, 1.0, *_span(axis, half, 1.0), top + 0.7, 17.6, rc)
            n = int(2 * half // 2.4)
            for k in range(n):
                a = -half + 0.3 + 2.4 * k
                slab(F.FR, axis, fixed, out, 1.0, a, a + 1.4, 17.6, 18.9, rc)
        if fi > 0 and side:
            side(axis, fixed, out, half)
    B.anchor(F.FR, (-21, -1, -20), (21, 19, 20))
    B.anchor(F.FQ, (-21, -1, -20), (21, 19, 20))
    return top


def side_windows(F, frame, glass, kind="rect", y0=8.6, y1=12.6, w=2.4, xs=(-10.0, -2.0, 6.0)):
    """Готовый side() для facade: ряд одинаковых окон на боках и тыле."""
    def side(axis, fixed, out, half):
        for a in xs:
            window(F, axis, fixed, out, a, y0, y1, w, frame, glass, kind)
    return side


def interior(F, wall, floor, ceil, trim, wain=None, beams=None, beam_dir="x", cornice=None, floor_q=True):
    """Стены зала изнутри с проёмом лифта, панель понизу (wain=(высота, цвет)), карниз, балки потолка
    (beams=(число, цвет)), пол — тихие квадраты (floor_q) цвета floor."""
    if floor_q:
        F.IQ.plane([(-W, 0.02, ZF), (W, 0.02, ZF), (W, 0.02, ZB), (-W, 0.02, ZB)], [], (0, 1, 0), floor)
    for idx, (axis, fixed, out, half) in enumerate(B.WALLS):
        gap = idx == 3
        spans = ((-half, -DOOR[0] - 0.6), (DOOR[0] + 0.6, half)) if gap else ((-half, half),)
        for a0, a1 in spans:
            slab(F.IR, axis, fixed, out, 0.88, a0, a1, 0.0, C if not gap else DOOR[1] + 0.1, wall)
            if wain:
                slab(F.IR, axis, fixed, out, 1.1, a0, a1, 0.0, wain[0], wain[1])
                slab(F.IS, axis, fixed, out, 1.2, a0, a1, wain[0], wain[0] + 0.25, trim)
        if gap:
            slab(F.IR, axis, fixed, out, 0.88, -DOOR[0] - 0.6, DOOR[0] + 0.6, DOOR[1] + 0.1, C, wall)
            slab(F.IS, axis, fixed, out, 1.2, -DOOR[0] - 0.8, DOOR[0] + 0.8, DOOR[1] + 0.1, DOOR[1] + 0.6, trim)
            for s in (-1, 1):
                slab(F.IS, axis, fixed, out, 1.2, s * (DOOR[0] + 0.1), s * (DOOR[0] + 0.8), 0.0, DOOR[1] + 0.1, trim)
        slab(F.IR, axis, fixed, out, 1.3, -half, half, C - 2.6, C - 2.0, cornice or trim)
    if beams:
        n, col = beams
        for k in range(n):
            t = -1 + 2 * (k + 0.5) / n
            if beam_dir == "x":
                z = t * (ZB - 1.0)
                F.IS.box(-W, W, C - 0.8, C - 0.1, z - 0.3, z + 0.3, col)
            else:
                x = t * (W - 1.0)
                F.IS.box(x - 0.3, x + 0.3, C - 0.8, C - 0.1, ZF, ZB, col)
    B.anchor(F.IR, (-17, 0, -16), (17, 18, 16))
    B.anchor(F.IQ, (-17, 0, -16), (17, 18, 16))


def silhouette(F, wall, ground, roof_col, top=TOP, roof="flat"):
    """Силуэт для дальнего LOD: коробка стен, площадка, крыша; особые объёмы добавляет скрипт."""
    F.SL.box(-FX, FX, -1, top + 0.7, -FZ, FZ, wall)
    F.SL.box(-FX - 2.9, FX + 2.9, -1.0, -0.1, -FZ - 2.9, FZ + 2.9, ground)
    if roof == "hip":
        F.SL.prism_zy([(-FZ - 2.2, top + 0.7), (FZ + 2.2, top + 0.7), (FZ + 0.88, 18.9), (-FZ - 0.88, 18.9)],
                      -FX - 2.2, FX + 2.2, roof_col)
    else:
        F.SL.box(-FX - 0.3, FX + 0.3, top + 0.7, 18.9, -FZ - 0.3, FZ + 0.3, roof_col)


def ped_round(F, px, pz, r, top, col, rim, base=None, n=16):
    """Круглый постамент: цоколь, тумба, обод."""
    if base:
        F.IR.prism_xz(K.ngon(px, pz, r + 0.5, n), 0.0, 0.3, base)
    F.IR.prism_xz(K.ngon(px, pz, r, n), 0.3 if base else 0.0, top - 0.2, col)
    F.IS.prism_xz(K.ngon(px, pz, r + 0.15, n), top - 0.2, top, rim)


def disc(p, c, n, r, t, col, seg=16):
    """Диск радиуса r толщиной t в любой плоскости: центр c, нормаль n (тарелки антенн, циферблаты, колёса)."""
    from mathutils import Vector

    n = Vector(n).normalized()
    u = Vector((0, 1, 0)).cross(n)
    if u.length < 1e-4:
        u = Vector((1, 0, 0)).cross(n)
    u.normalize()
    v = n.cross(u).normalized()
    c = Vector(c)
    ring = [c + (u * math.cos(2 * math.pi * k / seg) + v * math.sin(2 * math.pi * k / seg)) * r for k in range(seg)]
    p.loft([tuple(q) for q in ring], [tuple(q + n * t) for q in ring], col)


def _basis(n):
    from mathutils import Vector

    n = Vector(n).normalized()
    u = Vector((0, 1, 0)).cross(n)
    if u.length < 1e-4:
        u = Vector((1, 0, 0)).cross(n)
    u.normalize()
    return n, u, n.cross(u).normalized()


def annulus(p, c, n, r0, r1, t, col, seg=16):
    """Плоское кольцо r0…r1 толщиной t в плоскости с нормалью n (сегменты-призмы)."""
    from mathutils import Vector

    n, u, v = _basis(n)
    c = Vector(c)
    for k in range(seg):
        a0, a1 = 2 * math.pi * k / seg, 2 * math.pi * (k + 1) / seg
        d0 = u * math.cos(a0) + v * math.sin(a0)
        d1 = u * math.cos(a1) + v * math.sin(a1)
        q = [c + d0 * r0, c + d0 * r1, c + d1 * r1, c + d1 * r0]
        p.loft([tuple(x) for x in q], [tuple(x + n * t) for x in q], col)


def dish(p, c, n, r, depth, col, rim, steps=3, seg=14):
    """Вогнутая ступенчатая тарелка (антенна, раковина, чаша): дно-диск позади, кольца шире и ближе к n."""
    from mathutils import Vector

    nn = Vector(n).normalized()
    c = Vector(c)
    r_in = r / (steps + 1)
    disc(p, c - nn * depth, nn, r_in, 0.2, col, seg)
    for k in range(steps):
        a, b = r_in + (r - r_in) * k / steps, r_in + (r - r_in) * (k + 1) / steps
        off = depth * (1 - (k + 1) / steps)
        annulus(p, c - nn * off, nn, a - 0.05, b, 0.2, rim if k == steps - 1 else col, seg)
