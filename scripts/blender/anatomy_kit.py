"""Набор анатомии существ (D64 «Анатомия», 2026-11-24): объёмные тела и конечности вместо ящиков и плоских досок.

- body — тело-яйцо, бочка, капля, груша, шар в стиле D39 (как «шар» Сфинкса и ярусы дракона): стопка ярусов
  с прямыми стенками и срезанными углами (сечение — прямоугольник со скосами, не круг), каждый ярус своей ширины,
  поэтому силуэт ступенчатый, а крупные плоские грани несут кольца D39; профиль задаёт только ширину ступеней.
  Не гладкий многогранник: «лофтовая органика» отклонена (дракон v2; набор v1 2026-11-24 — «отошёл от стиля»).
- limb — конечность из сужающихся звеньев с шарами-суставами в изгибах (части заходят друг в друга);
  flipper — ласт или лапа-лопасть с изгибом и толщиной; foot — стопа с пальцами; folded_wing — сложенное крыло
  с перьями ступенями.
- eye — глаз как у существ и Сфинкса: брусок белка, квадратный зрачок, квадратный блик; по нормали поверхности,
  утоплен в голову на sink (≥ 0.05); closed=True — закрытый глаз для сна (веко и полоска ресниц); snout — морда-брусок
  вперёд ступенью, с носом-бруском и ртом; beak — тупой клюв-клин из двух половин; facial_disc — лицевой диск совы.
- Сечения звеньев — восьмигранник с малыми скосами (CUT): читаются брусками, а не круглыми трубами.
Все детали — выпуклые куски Art (art_style.py): грани внутри других деталей убирает конвейер (drop_enclosed).
Подключается из коллекций: import anatomy_kit as A; A.body(a, "navy", (0, 0, z), 1.2, 1.0, 2.4, "egg").
Зависит от art_style.py (Art, фаска), dragon10/v4_kit.py (звенья-цепи).
"""

import math
import os
import sys

from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "dragon10"))
import art_style as S  # noqa: E402
import v4_kit as K  # noqa: E402

V = Vector
TIER_BEVEL = S.BEVEL  # фаска яруса — как у всех деталей D39 (0.012)
CORNER = 0.34  # скос угла яруса — доля меньшего радиуса (прямоугольник со срезанными углами, как «шар» Сфинкса)
CUT = 0.26  # скос сечения звеньев (дракон v4–v7: 0.3) — брусок, не труба
SINK = 0.06  # глаза и морды заходят в голову не меньше чем на 0.05 (правило D64)


# ---------------------------------------------------------------- профили тел (t — 0 низ … 1 верх → доля радиуса)
def _bulge(t, mid, half):
    u = (t - mid) / half
    return math.sqrt(max(1.0 - u * u, 0.0))


PROFILES = {
    "ball": lambda t: _bulge(t, 0.5, 0.5),
    "egg": lambda t: _bulge(t, 0.42, 0.42 if t < 0.42 else 0.58),  # шире внизу, сужение к плечам
    "barrel": lambda t: 0.72 + 0.28 * math.sin(math.pi * t),  # бока выпуклые, верх и низ широкие
    "drop": lambda t: _bulge(t, 0.3, 0.3) if t < 0.3 else ((1.0 - t) / 0.7) ** 0.85,  # капля, кончик вверху
    "pear": lambda t: max(_bulge(t, 0.32, 0.34), 0.62 * _bulge(t, 0.76, 0.26)),  # груша: низ большой, верх малый
    "dome": lambda t: math.sqrt(max(1.0 - t * t, 0.0)),  # купол: широкое основание, кругло кверху
}


_N = [0]


def _count():
    _N[0] += 1
    return _N[0]


def body(a, key, base, rx, ry, h, shape="egg", n=6, t0=0.0, t1=1.0, lean=0.0, sides=8, floor=0.25, bevel=TIER_BEVEL,
         matrix=None, keys=None, corner=CORNER, front=None):
    """Тело D39: n ярусов с прямыми стенками вдоль оси z от base (середина низа) высотой h; ширина яруса — rx, ry ×
    профиль shape в середине яруса (ступени, не гладкий лофт). t0/t1 — срез профиля снизу/сверху; lean — сдвиг
    ярусов по y к верху (грудь вперёд < 0); floor — наименьшая доля радиуса; keys — свои цвета по ярусам снизу вверх;
    corner — скос углов (доля меньшего радиуса); matrix — поворот всего тела. sides оставлен для совместимости.
    front = (цвет, w, z0, z1[, глубина]) — живот или грудка, вписанные в ярусы: на ярусах между z0 и z1 передняя
    часть яруса (ширина w × плоская грань, овалом) — другого цвета, вровень с ярусом; ступени живота = ступени тела.
    Возвращает ярусы (za, zb, x, y, wx, wy, скос) для belly и проверок."""
    prof = PROFILES[shape] if isinstance(shape, str) else shape
    bx, by, bz = base
    tiers, prev = [], None
    for k in range(n):
        ta, tb = t0 + (t1 - t0) * k / n, t0 + (t1 - t0) * (k + 1) / n
        r = max(prof((ta + tb) / 2), floor)
        if prev is not None and abs(r - prev) < 0.04:
            r = prev * 0.96  # соседний ярус почти той же ширины (середина яйца) — ступень внутрь: видна, грани не
            # совпадают; заметно разные ярусы не трогаем (бока без лишних зубцов)
        prev = r
        wx, wy = rx * r, ry * r
        za, zb = bz + h * k / n, bz + h * (k + 1) / n
        y = by + lean * ((ta + tb) / 2 - t0) / (t1 - t0)
        ov = 0.01 if k else -(0.004 + 0.0017 * (_count() % 12))  # ярусы заходят друг в друга; низ над опорой (у разных
        # тел на разной высоте — нижние грани не совпадают)
        bv = min(bevel, h / n / 3, min(wx, wy) * 0.3) if min(rx, ry) >= 0.12 else 0.0
        pts = S.octagon(bx - wx, bx + wx, y - wy, y + wy, min(wx, wy) * corner)
        tk = keys[k % len(keys)] if keys else key
        cut = min(wx, wy) * corner
        lo, hi = (max(za, front[2]), min(zb, front[3])) if front else (0, 0)
        if front and hi - lo >= 0.05:
            fkey, fw, fz0, fz1 = front[:4]
            depth = front[4] if len(front) > 4 else 0.3
            u = ((za + zb) / 2 - (fz0 + fz1) / 2) / ((fz1 - fz0) / 2)
            hw = min((wx - cut) * fw * math.sqrt(max(1.0 - u * u * 0.85, 0.2)), wx - cut - 0.05)  # зазор > 2 фасок
            yd = y - wy + min(depth, wy)
            for piece in (_clip(pts, (1, 0), bx - hw), _clip(pts, (-1, 0), -(bx + hw)),
                          _clip(_clip(_clip(pts, (-1, 0), -(bx - hw)), (1, 0), bx + hw), (0, -1), -yd)):
                if len(piece) >= 3:  # тёмные бока и спина яруса
                    a.prism(tk, piece, za - ov, zb + 0.01, axis="z", bevel=bv, matrix=matrix)
            a.prism(fkey, [(bx - hw - 0.005, y - wy - 0.006), (bx + hw + 0.005, y - wy - 0.006),
                           (bx + hw + 0.005, yd + 0.005), (bx - hw - 0.005, yd + 0.005)],
                    za - ov + 0.002, zb + 0.008, axis="z", bevel=bv, matrix=matrix)  # перёд яруса — живот вровень
        else:
            a.prism(tk, pts, za - ov, zb + 0.01, axis="z", bevel=bv, matrix=matrix)
        tiers.append((za, zb, bx, y, wx, wy, min(wx, wy) * corner))
    return tiers


def _clip(pts, n, d):
    """Выпуклый многоугольник pts, обрезанный полуплоскостью n·p <= d (Сазерленд — Ходжман)."""
    out = []
    for i in range(len(pts)):
        p, q = pts[i], pts[(i + 1) % len(pts)]
        fp, fq = n[0] * p[0] + n[1] * p[1] - d, n[0] * q[0] + n[1] * q[1] - d
        if fp <= 0:
            out.append(p)
        if fp * fq < 0:
            t = fp / (fp - fq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    clean = []
    for p in out:  # точка на самой линии среза попадает дважды — вырожденная грань
        if not clean or abs(p[0] - clean[-1][0]) + abs(p[1] - clean[-1][1]) > 1e-5:
            clean.append(p)
    if len(clean) > 1 and abs(clean[0][0] - clean[-1][0]) + abs(clean[0][1] - clean[-1][1]) <= 1e-5:
        clean.pop()
    return clean


def belly(a, key, tiers, z0, z1, w=0.7, lift=0.025, reach=0.16, flat=False, depth=0.3, matrix=None, back=False):
    """Живот, грудка спереди тела между z0 и z1, ширина w × ширина яруса, контур — ступенчатый овал по ярусам тела
    (tiers из body). По умолчанию — накладка на каждый ярус: ступени живота совпадают со ступенями тела (живот вписан
    в форму, как полосы Сфинкса), выступ lift. flat=True — одна плоская накладка без швов (передняя грань — одна
    плоскость; ярусы, утопленные глубже reach, пропускает). back=True — полоса по спине (+y), ширина без овала."""
    if not flat:
        for za, zb, bx, y, wx, wy, cut in tiers:
            lo, hi = max(za, z0), min(zb, z1)
            if hi - lo < 0.05:
                continue
            u = 0.0 if back else ((lo + hi) / 2 - (z0 + z1) / 2) / ((z1 - z0) / 2)
            hw = min(wx * w * math.sqrt(max(1.0 - u * u * 0.85, 0.15)), wx - cut - 0.03)
            if back:
                a.box(key, bx - hw, bx + hw, y + wy - depth, y + wy + lift, lo + 0.004, hi + 0.006, matrix=matrix)
            else:
                a.box(key, bx - hw, bx + hw, y - wy - lift, y - wy + depth, lo + 0.004, hi + 0.006, matrix=matrix)
        return
    rows = []
    front = min(y - wy for za, zb, bx, y, wx, wy, cut in tiers if min(zb, z1) - max(za, z0) >= 0.05)
    for za, zb, bx, y, wx, wy, cut in tiers:
        lo, hi = max(za, z0), min(zb, z1)
        if hi - lo < 0.05 or (y - wy) - front > reach:
            continue
        u = ((lo + hi) / 2 - (z0 + z1) / 2) / ((z1 - z0) / 2)
        hw = min(wx * w * math.sqrt(max(1.0 - u * u * 0.85, 0.15)), wx - cut - 0.03)  # овал, не шире плоской грани
        rows.append((lo, hi, bx, hw, y - wy))
    if not rows:
        return
    bx = rows[0][2]
    right = []
    for lo, hi, _, hw, _ in rows:
        right += [(bx + hw, lo + 0.004), (bx + hw, hi + 0.004)]
    pts = right + [(2 * bx - x, z) for x, z in reversed(right)]
    clean = [pts[0]]
    for q in pts[1:]:  # соседние ярусы одной ширины — без лишних точек на прямой
        if abs(q[0] - clean[-1][0]) > 1e-4 or abs(q[1] - clean[-1][1]) > 1e-4:
            clean.append(q)
    back = max(r[4] for r in rows) + 0.08  # уходит в каждый ярус
    a.extrude(key, clean, front - lift, back, axis="y", matrix=matrix)


def ball(a, key, c, r, n=4, ry=None, rz=None, matrix=None):
    """Шар-сустав или голова: body формы ball вокруг центра c."""
    rz = rz or r
    body(a, key, (c[0], c[1], c[2] - rz), r, ry or r, 2 * rz, "ball", n=n, floor=0.35, matrix=matrix)


# ---------------------------------------------------------------- конечности
def limb(a, key, pts, ws, hs=None, up=(0, -1, 0), joint_key=None, joints=True):
    """Конечность по точкам pts (плечо → локоть → запястье …) сужающимися звеньями; в каждом изгибе шар-сустав
    чуть толще звеньев — части заходят друг в друга, сгиб не раскрывается."""
    hs = hs or ws
    K.KEY = key
    K.chain(a, pts, ws, hs, up=up, cut=CUT, overlap=0.5)
    if joints:
        for i in range(1, len(pts) - 1):
            r = max(ws[i], hs[i]) * 0.56
            ball(a, joint_key or key, pts[i], r, n=3)


def flipper(a, key, root, tip, w0, w1, thick=0.16, bend=(0, 0, 0), up=(0, 0, 1), segments=3):
    """Ласт или лапа-лопасть: от root к tip сужается w0 → w1, толщина thick → thick·0.5, изгиб bend (смещение
    середины); плоскость лопасти поперёк up. Корень заходит в тело на половину ширины."""
    p0, p1, b = V(root), V(tip), V(bend)
    pts, ws, hs = [], [], []
    for k in range(segments + 1):
        t = k / segments
        pts.append(tuple(p0.lerp(p1, t) + b * (4 * t * (1 - t))))
        ws.append(w0 + (w1 - w0) * t ** 0.8)
        hs.append(thick * (1.0 - 0.5 * t))
    K.KEY = key
    K.chain(a, pts, ws, hs, up=up, cut=CUT, overlap=0.5)


def foot(a, key, ankle, forward, length, width, toes=3, toe_key=None, h=0.14, z=None):
    """Стопа-брусок: подушка от пятки (под щиколоткой) вперёд на length и тупые пальцы-бруски (как лапы Сфинкса);
    forward — направление в плоскости."""
    f = V(forward).normalized()
    side = V((-f.y, f.x, 0))
    an = V(ankle)
    gz = an.z if z is None else z
    heel = V((an.x, an.y, gz + h / 2)) - f * width * 0.2
    toe = heel + f * length * 0.72
    K.KEY = key
    K.taper(a, heel, toe, width * 0.86, width, h, h * 0.92, up=(0, 0, 1), cut=0.2)
    K.KEY = toe_key or key
    tw = width / toes * 0.86
    for i in range(toes):
        o = (i - (toes - 1) / 2) * width / toes
        b = toe + side * o - f * 0.05 - V((0, 0, h * 0.04 * (i % 2)))
        ln = length * (0.26 if i in (0, toes - 1) else 0.32)
        K.taper(a, b, b + f * ln, tw, tw * 0.8, h * 0.82 - 0.01 * (i % 2), h * 0.66, up=(0, 0, 1), cut=0.22)


def folded_wing(a, key, tip_key, shoulder, side, length, width, rows=3, down=(0, 0.35, -1), thick=0.12):
    """Сложенное крыло вдоль бока: rows рядов перьев ступенями (верхний — короткий кроющий, нижний — длинные
    маховые), каждый ряд чуть дальше от тела; концы перьев — tip_key. side = ±1 (x)."""
    sh = V(shoulder)
    d = V(down).normalized()
    out = V((side, 0, 0))
    for r in range(rows):
        t = (r + 1) / rows
        ln = length * (0.45 + 0.55 * t)
        w = width * (1.0 - 0.18 * r)
        p0 = sh + out * (0.03 + 0.045 * r) + d * (length * 0.12 * r)
        p1 = p0 + d * ln * 0.72
        p2 = p0 + d * ln + out * 0.02
        K.KEY = key if r < rows - 1 else tip_key
        K.chain(a, [p0, p1, p2], [w, w * 0.8, w * 0.36], [thick, thick * 0.9, thick * 0.6], up=out, cut=CUT,
                overlap=0.4)


# ---------------------------------------------------------------- лицо
def facing(normal, up=(0, 0, 1)):
    """Поворот: ось −y детали смотрит по normal, z — как можно ближе к up."""
    n = V(normal).normalized()
    m = (-n).to_track_quat("Y", "Z").to_matrix().to_4x4()
    return m


def _at(c, normal):
    return Matrix.Translation(V(c)) @ facing(normal)


MOODS = {  # эмоция лица (как у Верблюда-тучи и Сфинкса): веко (доля белка сверху), наклон века и брови (градусы,
    # «+» — внутренний конец ниже), подъём брови (доля радиуса), зрачок
    "calm": dict(lid=0.15, lid_tilt=0, brow_tilt=0, brow_lift=0.25, pupil=0.55),
    "surprised": dict(lid=0.0, lid_tilt=0, brow_tilt=-12, brow_lift=0.75, pupil=0.42),
    "sly": dict(lid=0.45, lid_tilt=-14, brow_tilt=18, brow_lift=0.15, pupil=0.5),
    "sleepy": dict(lid=0.58, lid_tilt=8, brow_tilt=-6, brow_lift=0.05, pupil=0.5),
    "angry": dict(lid=0.3, lid_tilt=22, brow_tilt=28, brow_lift=0.0, pupil=0.5),
    "worried": dict(lid=0.12, lid_tilt=-18, brow_tilt=-26, brow_lift=0.4, pupil=0.48),
    "proud": dict(lid=0.4, lid_tilt=0, brow_tilt=-8, brow_lift=0.45, pupil=0.5),
    "goofy": dict(lid=0.0, lid_tilt=0, brow_tilt=-14, brow_lift=0.55, pupil=0.36),
}


def eye(a, c, r, normal=(0, -1, 0), look=(0.0, 0.0), pupil=None, sink=SINK, lift=0.04, closed=False,
        lid_key="dark", skin_key=None, sides=8, h=1.1, mood=None, side=1, brow_key=None, lid=None, lid_tilt=None,
        brow_tilt=None, brow_lift=None, brow=True):
    """Глаз D39 (как у существ и Сфинкса) в точке c головы, смотрит по normal: брусок белка 2r × 2r·h выступает на
    lift и уходит внутрь на sink, квадратный зрачок со смещением look, квадратный блик. closed — закрытый глаз:
    веко-брусок цвета skin_key и тёмная полоса ресниц. sides оставлен для совместимости.
    Эмоция (лицо — половина шутки коллекции): mood из MOODS или свои lid / lid_tilt / brow_tilt / brow_lift; веко —
    брусок цвета skin_key сверху белка с наклоном, бровь — брусок brow_key над глазом с наклоном; side — знак x
    глаза (+1 / −1), зеркалит наклоны: «+» опускает внутренний конец (к середине лица)."""
    m = _at(c, normal)
    w, hh = r, r * h
    bk = brow_key or lid_key
    if closed:
        a.box(skin_key or lid_key, -w * 1.02, w * 1.02, -lift * 0.7, sink, -hh * 0.95, hh * 0.95,
              bevel=0.01 if r >= 0.1 else 0.0, matrix=m)
        a.box(lid_key, -w * 0.95, w * 0.95, -lift * 0.7 - 0.03, -lift * 0.7 + 0.01, -hh * 0.18, hh * 0.02, bevel=0,
              matrix=m)
        if mood and brow:
            _brow(a, bk, m, w, hh, MOODS[mood]["brow_tilt"] * -side, MOODS[mood]["brow_lift"] * r, lift)
        return
    mv = dict(MOODS.get(mood or "calm"))
    for k, v in (("lid", lid), ("lid_tilt", lid_tilt), ("brow_tilt", brow_tilt), ("brow_lift", brow_lift),
                 ("pupil", pupil)):
        if v is not None:
            mv[k] = v
    if mood is None and lid is None:
        mv["lid"] = 0.0  # без эмоции — как раньше, глаз открыт и без брови
    a.box("white", -w, w, -lift, sink, -hh, hh, bevel=0.01 if r >= 0.1 else 0.0, matrix=m)
    pr = min(w, hh) * mv["pupil"]
    open_top = hh - 2 * hh * mv["lid"]  # зрачок под веком не прячется целиком
    px = look[0] * (w - pr) * 0.8
    pz = min(look[1] * (hh - pr) * 0.8, open_top - pr * 0.9)
    a.box("dark", px - pr, px + pr, -lift - 0.025, -lift + 0.01, pz - pr, pz + pr, bevel=0, matrix=m)
    g = pr * 0.62
    a.box("glint", px - pr + 0.02, px - pr + 0.02 + g, -lift - 0.045, -lift - 0.02, pz + pr - 0.02 - g, pz + pr - 0.02,
          bevel=0, matrix=m)
    if mv["lid"] > 0.02:  # веко с наклоном: хитрость, сонливость, злость
        lt = math.radians(mv["lid_tilt"] * -side)
        lh = 2 * hh * mv["lid"]
        mm = m @ Matrix.Translation((0, 0, hh - lh / 2)) @ Matrix.Rotation(lt, 4, "Y")
        a.box(skin_key or lid_key, -w * 1.12, w * 1.12, -lift - 0.06, sink * 0.5, -lh / 2, lh / 2 + hh * 0.3,
              bevel=0, matrix=mm)
    if brow and (mood is not None or brow_tilt is not None):
        _brow(a, bk, m, w, hh, mv["brow_tilt"] * -side, mv["brow_lift"] * r, lift)


def _brow(a, key, m, w, hh, tilt, raise_, lift):
    """Бровь-брусок над глазом (как у Сфинкса и Верблюда): длина 2.5w, наклон tilt (° , «+» — внутренний конец
    ниже), подъём raise_ над верхом белка."""
    bh = max(hh * 0.32, 0.03)
    mm = m @ Matrix.Translation((0, 0, hh + bh * 0.9 + raise_)) @ Matrix.Rotation(math.radians(tilt), 4, "Y")
    a.box(key, -w * 1.25, w * 1.25, -lift - 0.05, SINK * 2.2, -bh / 2, bh / 2, bevel=0, matrix=mm)  # глубоко: на
    # круглой голове бровь не отходит от поверхности


def snout(a, key, base, direction, length, w0, w1, h0=None, h1=None, nose_key="dark", nose=0.3, mouth_key="mouth",
          mouth=0.7):
    """Морда-брусок: от base (внутри головы на SINK) по direction на length двумя ступенями (корень шире, конец уже),
    на конце нос-брусок (доля nose от ширины конца), снизу полоса рта (доля mouth от длины, 0 — без рта)."""
    b, d = V(base), V(direction).normalized()
    h0, h1 = h0 or w0 * 0.85, h1 or w1 * 0.85
    tip = b + d * length
    mid = b + d * length * 0.55
    K.KEY = key
    K.taper(a, b - d * SINK, mid, w0, w0 * 0.94, h0, h0 * 0.94, up=(0, 0, 1), cut=0.22)  # корень морды
    K.taper(a, mid - d * 0.04, tip, w1 * 1.04, w1, h1 * 1.04, h1, up=(0, 0, 1), cut=0.22)  # ступень к носу
    if nose:
        nw = w1 * nose + 0.03
        nc = tip + V((0, 0, h1 * 0.3))
        K.KEY = nose_key
        K.taper(a, nc - d * 0.05, nc + d * 0.035, nw, nw * 0.92, nw * 0.7, nw * 0.62, up=(0, 0, 1), cut=0.2)
    if mouth:
        side = d.cross(V((0, 0, 1))).normalized()
        m0 = tip - d * length * mouth - V((0, 0, h1 * 0.42))
        m1 = tip - d * 0.03 - V((0, 0, h1 * 0.42))
        for s in (1, -1):
            K.KEY = mouth_key
            K.taper(a, m0 + side * s * w0 * 0.36, m1 + side * s * w1 * 0.1, 0.05, 0.045, 0.05, 0.045, cut=0.2)


def beak(a, key, base, direction, length, w, h=None, key_low=None, gape=0.0):
    """Клюв-клин D39: верхняя половина сужается к тупому концу и чуть вниз, нижняя — короче; gape — щель (открыт)."""
    b, d = V(base), V(direction).normalized()
    h = h or w * 0.8
    up = V((0, 0, 1))
    K.KEY = key
    K.taper(a, b - d * SINK + up * h * 0.18, b + d * length - up * h * 0.2, w, w * 0.34, h * 0.6, h * 0.24, cut=0.2)
    K.KEY = key_low or key
    K.taper(a, b - d * SINK - up * (h * 0.22 + gape), b + d * length * 0.66 - up * (h * 0.3 + gape), w * 0.86,
            w * 0.36, h * 0.42, h * 0.2, cut=0.2)


def facial_disc(a, key, rim_key, c, r, normal=(0, -1, 0), gap=0.55):
    """Лицевой диск совы: два круга вокруг глаз (сердце), светлее перьев; тёмная кайма позади. c — середина лица."""
    m = _at(c, normal)
    for s in (1, -1):
        x0 = s * r * gap
        a.prism(rim_key, S.octagon(x0 - r * 1.08, x0 + r * 1.08, -r * 1.12, r * 1.12, r * 0.4), 0.0, SINK + 0.02,
                axis="y", bevel=0.01, matrix=m)
        a.prism(key, S.octagon(x0 - r, x0 + r, 0.04 - r * 1.02, 0.04 + r * 1.02, r * 0.36), -0.04, SINK, axis="y",
                bevel=0.01, matrix=m)


def eye_points(c, r, normal, spread, up=0.0):
    """Точки двух глаз на сфере головы (центр c, радиус r), смотрящих по normal: разведены на spread градусов."""
    n = V(normal).normalized()
    out = []
    for s in (1, -1):
        q = Matrix.Rotation(math.radians(s * spread), 3, "Z") @ n
        q = (q + V((0, 0, up))).normalized()
        out.append((tuple(V(c) + q * r), tuple(q)))
    return out
