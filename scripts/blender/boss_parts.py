"""Part-версия Крысиного короля (босс 3, D54) по утверждённой модели — пока меши и карты не загружены (вместо 21
блока-заготовки по габаритам частей).

Модель короля в scripts/blender/boss3_ratking.py собрана из простых фигур art_style.Art: бруски, восьмигранные и
другие призмы, усечённые пирамиды, рамки. Этот скрипт выполняет ту же сборку (без запекания и рендеров) и записывает
каждую фигуру — вид, размеры, поворот, цвет и часть скелета, — а затем переводит её в детали Roblox:
- брусок (в том числе наклонный: усы, хвост, цепь) — одна деталь того же размера и поворота;
- призма — полосами поперёк её многоугольника: восьмигранник — три ступени (D39: силуэт ступенями), прямоугольник —
  одна деталь, сужающийся многоугольник — до трёх полос;
- усечённая пирамида (клыки, зубцы короны) — две-три ступени;
- рамка (обод уха, медальона) — бруски вдоль сторон.
Скругления фасок не переносятся (блоки с острыми рёбрами). Цвет — цвет детали в модели (palette art.paint).
Совпадающих граней у разных деталей нет: у пересекающихся деталей (и одного цвета) одинаково смотрящие грани ближе
OVERLAY (в том числе наклонённые — ухо, корона) разводятся сдвигом грани меньшей детали — см. separate(): внутри
части — на OVERLAY (CLAUDE.md: ≥ 0.1), между частями — на FALLBACK_GAP в покое и во всех позах, что держатся
(assets/models/Boss3_RatKing.poses.json — scripts/lune/export_king_poses.luau по Shared/BossAnim; при смене поз
или скелета — выгрузить заново). flush_pairs() после разведения считает видимые пары вровень (должно быть 0).

Пишет assets/models/Boss3_RatKing.parts.json: часть → [{c, s, col, r?, shape?}] — центр от точки вращения части и
размер в стадах (оси Roblox, лицо +Z), поворот r — 9 чисел по строкам (если не единичный), shape "Cylinder" — круг.
Кадры <рендеры>/king_<ракурс>_{fbx,blocks}.png: FBX с картами D54 и детали с одного ракурса (лист сравнения —
assets/concepts/d55/boss3_visual_qa/11_king_d54_fbx_vs_parts.jpg).
Запуск: blender --background --factory-startup --python scripts/blender/boss_parts.py -- <репо> <рендеры>
Зависит от art_style.py и boss3_ratking.py (сборка фигур), Boss3_RatKing.poses.json (позы; без него — запасной
путь POSE_MARGIN).
"""

import inspect
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import art_style as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
os.makedirs(OUT, exist_ok=True)
DST = os.path.join(REPO, "assets", "models", "Boss3_RatKing.parts.json")

SMALL_CUT = 0.12  # восьмигранник со срезом меньше этой доли стороны — одна деталь (срез не заметен)

# ── 1. Запись фигур при сборке модели ─────────────────────────────────────────────────────────────────────────
records = []
for kind in ("box", "prism", "frustum", "extrude", "frame"):
    original = getattr(S.Art, kind)
    signature = inspect.signature(original)

    def wrapper(self, *args, _original=original, _kind=kind, _sig=signature, **kwargs):
        bound = _sig.bind(self, *args, **kwargs)
        bound.apply_defaults()
        params = dict(bound.arguments)
        params.pop("self")
        records.append({"kind": _kind, "group": self.group, "color": self.colors[params["key"]][0],
                        "transform": None if self.transform is None else self.transform.copy(), "p": params})
        return _original(self, *args, **kwargs)

    setattr(S.Art, kind, wrapper)

source_path = os.path.join(HERE, "boss3_ratking.py")
source = open(source_path, encoding="utf-8").read()
source = source[: source.index('report = {"scale": SCALE}')]  # до сборки мешей: только фигуры, RIG и SCALE
sys.argv = [sys.argv[0], "--", REPO, os.path.join(OUT, "_unused"), "record"]
model = {"__name__": "__boss3_record__", "__file__": source_path}
exec(compile(source, source_path, "exec"), model)
RIG, SCALE = model["RIG"], model["SCALE"]
AX = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))  # оси Roblox: (x, y, z) Blender → (x, z, −y) Roblox


# ── 2. Фигура → прямоугольные куски в своих осях ──────────────────────────────────────────────────────────────
def spans(pts, w):
    """Отрезки по u, где горизонталь w пересекает многоугольник pts (может быть невыпуклым)."""
    xs = []
    n = len(pts)
    for i in range(n):
        (u0, w0), (u1, w1) = pts[i], pts[(i + 1) % n]
        if (w0 <= w < w1) or (w1 <= w < w0):
            xs.append(u0 + (w - w0) * (u1 - u0) / (w1 - w0))
    xs.sort()
    return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


def polygon_rects(pts, convex=True):
    """Многоугольник → прямоугольники (u0, u1, w0, w1): полосы между соседними высотами вершин, ширина — на середине
    полосы; сужающаяся полоса (клин) делится ещё надвое. Восьмигранник с маленьким срезом — его габарит."""
    us, ws = [p[0] for p in pts], [p[1] for p in pts]
    u0, u1, w0, w1 = min(us), max(us), min(ws), max(ws)
    if convex and len(pts) == 8:
        bottom = [p[0] - u0 for p in pts if abs(p[1] - w0) < 1e-6]  # срез — отступ нижнего ребра от угла
        cut = min(bottom) if bottom else 0
        if cut < SMALL_CUT * min(u1 - u0, w1 - w0):
            return [(u0, u1, w0, w1)]
    levels = sorted({round(w, 6) for w in ws})
    rects = []
    for a, b in zip(levels, levels[1:]):
        top, bottom = spans(pts, b - 1e-6 * (b - a)), spans(pts, a + 1e-6 * (b - a))
        width_top = sum(x1 - x0 for x0, x1 in top)
        width_bottom = sum(x1 - x0 for x0, x1 in bottom)
        taper = abs(width_top - width_bottom) > 0.35 * max(width_top, width_bottom, 1e-6)
        cuts = [a, (a + b) / 2, b] if taper and (b - a) > 0.06 else [a, b]
        for c0, c1 in zip(cuts, cuts[1:]):
            for x0, x1 in spans(pts, (c0 + c1) / 2):
                if x1 - x0 > 1e-4:
                    rects.append((x0, x1, c0, c1))
    return rects


def pieces(rec):
    """Куски фигуры: (матрица осей фигуры 4×4, центр, размер, поворот 3×3 в осях фигуры, форма)."""
    p, kind = rec["p"], rec["kind"]
    base = p.get("matrix")
    m = Matrix.Identity(4) if base is None else base.copy()
    if rec["transform"] is not None:
        m = rec["transform"] @ m
    eye = Matrix.Identity(3)
    out = []
    if kind == "box":
        lo = Vector((min(p["x0"], p["x1"]), min(p["y0"], p["y1"]), min(p["z0"], p["z1"])))
        hi = Vector((max(p["x0"], p["x1"]), max(p["y0"], p["y1"]), max(p["z0"], p["z1"])))
        out.append((m, (lo + hi) / 2, hi - lo, eye, "Block"))
    elif kind in ("prism", "extrude"):
        a = m @ S.AXES[p["axis"]]
        a0, a1 = sorted((p["a0"], p["a1"]))
        for u0, u1, w0, w1 in polygon_rects(p["pts"], convex=kind == "prism"):
            out.append((a, Vector(((u0 + u1) / 2, (w0 + w1) / 2, (a0 + a1) / 2)),
                        Vector((u1 - u0, w1 - w0, a1 - a0)), eye, "Block"))
    elif kind == "frustum":
        a = m @ S.AXES[p["axis"]]
        bottom, top, z0, z1 = p["bottom"], p["top"], p["z0"], p["z1"]
        apex = top[1] - top[0] < 1e-6 and top[3] - top[2] < 1e-6
        ts = (1 / 6, 1 / 2, 5 / 6) if apex else (1 / 4, 3 / 4)
        n = len(ts)
        for i, t in enumerate(ts):
            r = [bottom[k] + (top[k] - bottom[k]) * t for k in range(4)]
            za, zb = z0 + (z1 - z0) * i / n, z0 + (z1 - z0) * (i + 1) / n
            out.append((a, Vector(((r[0] + r[1]) / 2, (r[2] + r[3]) / 2, (za + zb) / 2)),
                        Vector((abs(r[1] - r[0]), abs(r[3] - r[2]), abs(zb - za))), eye, "Block"))
    elif kind == "frame":
        a = m @ S.AXES[p["axis"]]
        outer = p["pts"]
        inner = S._inset(outer, p["inset"])
        a0, a1 = sorted((p["a0"], p["a1"]))
        for i in range(len(outer)):
            j = (i + 1) % len(outer)
            po, qo = Vector((*outer[i], 0)), Vector((*outer[j], 0))
            pi, qi = Vector((*inner[i], 0)), Vector((*inner[j], 0))
            d = qo - po
            ang = math.atan2(d.y, d.x)
            length = ((qo - po).length + (qi - pi).length) / 2
            depth = a1 - a0  # бруски одной рамки одного цвета: их общие грани не видны
            center = (po + qo + pi + qi) / 4
            center.z = (a0 + a1) / 2
            out.append((a, center, Vector((length, p["inset"], depth)), Matrix.Rotation(ang, 3, "Z"), "Block"))
    return out


# ── 3. Куски → детали Roblox от точки вращения части ──────────────────────────────────────────────────────────
def proper(r):
    """Поворот без отражения (оси фигур Art бывают зеркальными): брусок симметричен — отражаем его третью ось."""
    if r.determinant() < 0:
        r = r.copy()
        for k in range(3):
            r[k][2] = -r[k][2]
    return r


def aligned(rr, size):
    """Поворот на 90° вокруг осей (призмы по y и x, зеркальные оси Art) — не наклон: деталь без поворота, размер
    по осям мира. Возвращает (поворот или None, размер)."""
    world = [None, None, None]
    for i in range(3):
        col = [rr[0][i], rr[1][i], rr[2][i]]
        j = max(range(3), key=lambda k: abs(col[k]))
        if abs(abs(col[j]) - 1) > 1e-4 or world[j] is not None:
            return rr, size
        world[j] = size[i]
    return None, Vector(world)


parts = {name: [] for name in RIG}
for rec in records:
    group = rec["group"]
    pivot = Vector(RIG[group][1]) * SCALE
    for frame, center, size, rot, shape in pieces(rec):
        r3 = frame.to_3x3()
        world = (frame @ center) * SCALE  # модель короля в масштабе предметов → стады
        r = proper(r3 @ rot)
        for k in range(3):  # без масштаба (на всякий случай нормируем столбцы)
            col = Vector((r[0][k], r[1][k], r[2][k])).normalized()
            for row in range(3):
                r[row][k] = col[row]
        c = AX @ (world - pivot)
        # поворот детали: её оси (оси фигуры) → оси Roblox; размер — по её осям (порядок фигуры)
        rr, s = aligned(AX @ r, size * SCALE)
        entry = {"c": [round(v, 4) for v in c], "s": [round(v, 4) for v in s], "col": rec["color"]}
        if rr is not None and any(abs(rr[i][j] - (1 if i == j else 0)) > 1e-4 for i in range(3) for j in range(3)):
            entry["r"] = [round(rr[i][j], 5) for i in range(3) for j in range(3)]
        if shape != "Block":
            entry["shape"] = shape
        parts[group].append(entry)


OVERLAY = 0.1  # стадов (CLAUDE.md): накладка другого цвета выступает не меньше этого — иначе грани мерцают
FACE_MIN = 0.05  # стадов: перекрытие граней меньше этого по одной из осей не считается (как в World/FaceCheck)
PASSES = 6  # проходов разведения граней (сдвиг одной грани меняет перекрытия других)
PARALLEL = 1 - 1e-4  # |cos| осей: грани параллельны (наклонённые детали уха, короны, хвоста — тоже)
# Разведение — с запасом к проверке: перекрытие от SEP_OVERLAP и почти параллельные до SEP_PARALLEL (≈ 1°) — иначе
# пары на самом пороге (полоска перекрытия ровно 0.05 у обода уха) одна проверка видит, другая — нет (округления);
# полоски уже 0.04 (дырка сыра на 0.03 в сыре) не мерцают заметно и не стоят искажения детали
SEP_OVERLAP = 0.04  # разведение: чуть ниже FACE_MIN — пары на самом пороге (обод уха 0.0499…0.0501)
CHECK_OVERLAP = 0.045  # проверка «с запасом» — между разведением и FaceCheck, чтобы пара на пороге не мигала
KEEP = 0.5  # деталь вдоль оси не сужается больше чем вдвое (дырки сыра медальона не превращаются в щели)
FALLBACK_GAP = FACE_MIN + 0.005  # запасной зазор: с округлением центров и размеров до 4 знаков — не ниже FACE_MIN
# Детали разных частей двигаются друг относительно друга: грани, лежащие в одной плоскости, но рядом (до POSE_MARGIN),
# в позе могут перекрыться — плоскость грани, параллельной оси поворота сустава, при повороте не меняется (мантия во
# сне поворачивается вокруг x — её грани по x сходятся с гранями сумки; бровь опускается на блики глаз в победе)
POSE_MARGIN = 0.5  # запасной путь — если нет выгрузки поз (scripts/lune/export_king_poses.luau)
SEP_PARALLEL = 1 - 1.5e-4
POSES_PATH = os.path.join(REPO, "assets", "models", "Boss3_RatKing.poses.json")
POSE_REACH = 4.0  # стадов: дальше этого в покое детали разных частей в позах не сходятся — не проверяем


def _load_poses():
    """Позы из игры (Shared/BossAnim → export_king_poses.luau), только те, что держатся (held): поза → часть → 4×4 в
    осях модели (деталь x в позе — D · x). None — выгрузки нет."""
    if not os.path.exists(POSES_PATH):
        return None
    raw = json.load(open(POSES_PATH, encoding="utf-8"))
    held = set(raw.get("held") or raw["poses"].keys())
    data = {name: v for name, v in raw["poses"].items() if name in held}
    out = {}
    for name, parts_ in data.items():
        out[name] = {}
        for part, c in parts_.items():
            out[name][part] = Matrix(((c[3], c[4], c[5], c[0]), (c[6], c[7], c[8], c[1]),
                                      (c[9], c[10], c[11], c[2]), (0, 0, 0, 1)))
    return out


POSES = _load_poses()
_RELATIVE = {}


def _relative(p, q):
    """Положение части q в осях части p: в покое и в каждой позе (D_p⁻¹ · D_q)."""
    key = (p, q)
    if key not in _RELATIVE:
        mats = [Matrix.Identity(4)]
        for pose in POSES.values():
            mats.append(pose[p].inverted() @ pose[q])
        _RELATIVE[key] = mats
    return _RELATIVE[key]


def _boxes(parts):
    """Детали как коробки в осях модели: оси (ортонормированные столбцы поворота), отрезки вдоль своих осей."""
    pivots = {name: AX @ (Vector(RIG[name][1]) * SCALE) for name in RIG}
    out = []
    for name, lst in parts.items():
        for e in lst:
            r = e.get("r", (1, 0, 0, 0, 1, 0, 0, 0, 1))
            cols = [Vector((r[k], r[3 + k], r[6 + k])) for k in range(3)]
            a0 = cols[0].normalized()
            a1 = (cols[1] - a0 * cols[1].dot(a0)).normalized()
            a2 = a0.cross(a1)
            if a2.dot(cols[2]) < 0:
                a2 = -a2
            c = Vector(e["c"]) + pivots[name]
            h = Vector(e["s"]) / 2
            axes = [a0, a1, a2]
            ext = [[c.dot(a) - h[k], c.dot(a) + h[k]] for k, a in enumerate(axes)]
            out.append({"e": e, "part": name, "col": e["col"], "axes": axes, "ext": ext,
                        "start": [list(x) for x in ext], "radius": h.length})
    return out


def _center(b):
    c = Vector((0, 0, 0))
    for k in range(3):
        c += b["axes"][k] * ((b["ext"][k][0] + b["ext"][k][1]) / 2)
    return c


def _along(b, a, parallel=PARALLEL):
    """Отрезок коробки вдоль оси a (центр — проекция её центра на a, ± полуразмер по её оси, параллельной a) и номер
    этой оси (None — такой оси нет). Проекция центра, а не координата по своей оси: у почти параллельных (кольцо хвоста
    наклонено на 0.6°) координаты по разным осям расходятся на |центр| × угол."""
    for j, axis in enumerate(b["axes"]):
        if abs(axis.dot(a)) > parallel:
            mid = _center(b).dot(a)
            half = (b["ext"][j][1] - b["ext"][j][0]) / 2
            return [mid - half, mid + half], j
    return None, None


def _overlap_in_plane(b, k, o, j, least=FACE_MIN - 1e-3):
    """Перекрываются ли грани b (нормаль — ось k) и o (ось j) в своей плоскости больше чем на FACE_MIN по каждой из
    разделяющих осей (прямоугольники в плоскости могут быть повёрнуты друг к другу)."""
    cb, co = _center(b), _center(o)
    ub = [(b["axes"][i], (b["ext"][i][1] - b["ext"][i][0]) / 2) for i in range(3) if i != k]
    uo = [(o["axes"][i], (o["ext"][i][1] - o["ext"][i][0]) / 2) for i in range(3) if i != j]
    for w, _ in ub + uo:
        rb = sum(abs(u.dot(w)) * hu for u, hu in ub)
        ro = sum(abs(u.dot(w)) * hu for u, hu in uo)
        lo = max(cb.dot(w) - rb, co.dot(w) - ro)
        hi = min(cb.dot(w) + rb, co.dot(w) + ro)
        # с запасом 1e-3: в Roblox 0.05 превращается в 0.0500001, и FaceCheck пару видит
        if hi - lo <= least:
            return False
    return True


def _moved(o, m):
    """Коробка o, перенесённая матрицей m (поза): оси и отрезки вдоль новых осей."""
    r = m.to_3x3()
    c = m @ _center(o)
    axes = [(r @ a).normalized() for a in o["axes"]]
    ext = []
    for k, a in enumerate(axes):
        half = (o["ext"][k][1] - o["ext"][k][0]) / 2
        mid = c.dot(a)
        ext.append([mid - half, mid + half])
    return {"axes": axes, "ext": ext, "radius": o["radius"], "part": o["part"], "col": o["col"]}


def _scene(boxes):
    """Для каждой части P и каждой позы (0 — покой, дальше — POSES): все коробки в осях части P — пары (коробка в позе,
    исходная). Своя часть и покой — как есть, другие части в позе — перенесены (части двигаются друг относительно
    друга: мантия во сне, веко под надбровьем в бою). Пересчитывается каждый проход: грани сдвигаются."""
    count = 1 + (len(POSES) if POSES else 0)
    scene = {}
    for p in sorted({b["part"] for b in boxes}):
        per = []
        for i in range(count):
            lst = []
            for o in boxes:
                if i == 0 or o["part"] == p:
                    lst.append((o, o))
                else:
                    lst.append((_moved(o, _relative(p, o["part"])[i]), o))
            per.append(lst)
        scene[p] = per
    return scene


def _near(b, scene):
    """Коробки рядом с b в каждой позе: для пар и укрытие при проверке видимости (своя часть — тоже)."""
    cb = _center(b)
    out = []
    for i, lst in enumerate(scene[b["part"]]):
        near = []
        for v, src in lst:
            if src is b:
                continue
            if (_center(v) - cb).length <= b["radius"] + v["radius"] + 5 * OVERLAY:
                near.append((v, src))
        out.append(near)
    return out


def _inside(p, w):
    cw = _center(w)
    for q in range(3):
        if abs((p - cw).dot(w["axes"][q])) >= (w["ext"][q][1] - w["ext"][q][0]) / 2 - 1e-3:
            return False
    return True


def _visible(b, k, side, v, j, cover):
    """Видна ли пара граней (как World/FaceCheck): точки общей части граней — сетка 5 × 5 по меньшей из них внутри
    большей — чуть наружу (0.03, обе смотрят в одну сторону) не внутри третьих коробок cover (в той же позе).
    Симметрично: не зависит от того, какая деталь первая."""
    n = b["axes"][k] * (-1 if side == 0 else 1)

    def face(box, axis):
        c = _center(box)
        half = [(box["ext"][q][1] - box["ext"][q][0]) / 2 for q in range(3)]
        sign = 1 if box["axes"][axis].dot(n) > 0 else -1
        fc = c + box["axes"][axis] * (sign * half[axis])
        inplane = [(box["axes"][q], half[q]) for q in range(3) if q != axis]
        return fc, inplane

    fb, ib = face(b, k)
    fv, iv = face(v, j)
    small, big = ((fb, ib), (fv, iv)) if ib[0][1] * ib[1][1] <= iv[0][1] * iv[1][1] else ((fv, iv), (fb, ib))
    (fs, ((u1, h1), (u2, h2))), (fl, il) = small, big
    for fu in (-0.8, -0.4, 0, 0.4, 0.8):
        for fw in (-0.8, -0.4, 0, 0.4, 0.8):
            p = fs + u1 * (h1 * fu) + u2 * (h2 * fw)
            if any(abs((p - fl).dot(u)) > h for u, h in il):
                continue
            probe = p + n * 0.03
            if not any(_inside(probe, c) for c, _ in cover if c is not v and c is not b):
                return True
    return False


def _faces(b, k, side, near, mode="sep", deferred=None):
    """Параллельные грани той же стороны у деталей рядом (near из _near — в покое и в позах), перекрытые с гранью b
    и видимые: (координата вдоль оси k детали b, та же часть, тот же цвет, одна из деталей — веко, (часть и цвет
    другой детали)). deferred — id деталей, с которыми сравнивать (большие при разведении). Пары дальше 0.35 от
    грани ни на что не влияют (сдвиг ≤ 0.2, зазор 0.1) — видимость для них не считается."""
    a = b["axes"][k]
    cur = b["ext"][k][side]
    least = {"strict": FACE_MIN - 1e-3, "check": CHECK_OVERLAP, "sep": SEP_OVERLAP}[mode]
    parallel = PARALLEL if mode == "strict" else SEP_PARALLEL
    out = []
    for i, lst in enumerate(near):
        for v, src in lst:
            if deferred is not None and id(src) not in deferred:
                continue
            if i > 0 and src["part"] == b["part"]:
                continue  # своя часть в позе стоит так же, как в покое: пары — только в покое
            seg, j = _along(v, a, parallel)
            if seg is None or abs(seg[side] - cur) > 0.35:
                continue
            gap = least
            if mode == "sep" and src["part"] != b["part"] and POSES is None:
                gap = -POSE_MARGIN  # без выгрузки поз: разные части рядом в плоскости — тоже пара (сойдутся в позе)
            if not _overlap_in_plane(b, k, v, j, gap):
                continue
            # видимость — только у пар разных частей в позах (веко ездит сквозь голову: закрытые совпадения не мешают);
            # в покое и внутри части разводятся все пары, и закрытые тоже — так надёжнее эвристики видимости
            if i > 0 and src["part"] != b["part"] and not _visible(b, k, side, v, j, lst):
                continue
            lid = src["part"].startswith("Eyelid") or b["part"].startswith("Eyelid")
            out.append((seg[side], src["part"] == b["part"], src["col"] == b["col"], lid, (src["part"], src["col"])))
    return out


def separate(parts):
    """Одинаково смотрящие совпадающие или почти совпадающие (ближе OVERLAY) параллельные грани пересекающихся
    деталей при любом их повороте (по нормалям; перекрытие в плоскости грани — по разделяющим осям) разводятся на
    OVERLAY: двигается грань меньшей детали — накладки (зрачок, пряжка, камень). Детали — от больших к меньшим (грани
    больших уже на местах), PASSES проходов; новое место грани — ближайшее к исходному, где она не ближе OVERLAY ни к
    одной такой грани больших деталей, не дальше OVERLAY от исходного (у разных частей — 2 × OVERLAY); при равенстве —
    наружу (накладка выступает). У разных частей грань уходит только внутрь: части двигаются друг относительно друга,
    выступ прошёл бы сквозь соседа (блик глаза сквозь закрытое веко). Детали одного цвета тоже разводятся (пупырышки
    LegoSquares на совпадающих гранях мерцают и при одном цвете), но только наружу: внутрь — вырез или щель, если
    большая деталь закрывает меньшую не целиком. Веки — последними и в любую сторону (накладка поверх головы).
    Между разными частями хватает FALLBACK_GAP (они двигаются, совпадение случайное), внутри части — OVERLAY.
    Если места на OVERLAY нет, а грань вровень (ближе FACE_MIN), — хотя бы на FALLBACK_GAP в любую сторону (пара с
    веком — только внутрь). Перекрытие граней меньше FACE_MIN по одной из
    осей не считается (как в World/FaceCheck).
    Возвращает (сдвинуто граней, осталось ближе OVERLAY, осталось вровень)."""
    boxes = _boxes(parts)

    def rank_box(b):
        # веки — последними: накладка поверх глаза и головы (бровь в победе ложится на блик), двигаются они
        lid = 1 if b["part"].startswith("Eyelid") else 0
        return lid, -math.prod(x[1] - x[0] for x in b["start"])

    order = sorted(boxes, key=rank_box)
    near_left = flush_left = 0
    for rnd in range(PASSES):  # ещё проход: сдвиг одной грани меняет перекрытие других (верх бруска → его бок)
        scene = _scene(order)  # все детали в осях каждой части — в покое и в позах
        for idx, b in enumerate(order):
            around = _near(b, scene)
            deferred = {id(o) for o in order[:idx]}  # грани больших уже на местах
            for k in range(3):
                for side in (0, 1):  # грани смотрят в одну сторону: обе «нижние» или обе «верхние» вдоль оси
                    faces = _faces(b, k, side, around, "sep", deferred)
                    cur = b["ext"][k][side]
                    # зазор: внутри части — OVERLAY (накладка выступает, CLAUDE.md), между частями — FALLBACK_GAP
                    # (они двигаются друг относительно друга, совпадение случайное: лишь бы не вровень)
                    near = [(own, same, lid) for f, own, same, lid, _ in faces
                            if abs(cur - f) < (OVERLAY if own else FALLBACK_GAP) - 1e-4]
                    if not near:
                        continue
                    orig = b["start"][k][side]  # сдвиг — от исходного места грани
                    own = all(o for o, _, _ in near)
                    same = all(c for _, c, _ in near)
                    lid = any(v for _, _, v in near)
                    own_lid = b["part"].startswith("Eyelid")  # грань самого века: в любую сторону
                    out = -1 if side == 0 else 1
                    other = b["ext"][k][1 - side]
                    least = max(0.02, KEEP * (b["start"][k][1] - b["start"][k][0]))

                    def fits(p, gap, inward_only, outward_only, limit):
                        if abs(p - orig) > limit + 1e-4:
                            return False
                        if inward_only and (p - orig) * out > 1e-4:
                            return False
                        if outward_only and (p - orig) * out < -1e-4:
                            return False
                        if (other - p if side == 0 else p - other) < least:
                            return False
                        return all(abs(p - f) >= (gap if own_f else min(gap, FALLBACK_GAP)) - 1e-4
                                   for f, own_f, _, _, _ in faces)

                    def rank(p):  # ближе к исходному; при равенстве — наружу; дальше — по месту (однозначно)
                        return round(abs(p - orig), 6), 0 if (p - orig) * out > 0 else 1, round(p, 6)

                    best = None
                    cands = {f + d * (OVERLAY if own_f else FALLBACK_GAP)
                             for f, own_f, _, _, _ in faces for d in (-1, 1)}
                    for p in sorted(cands, key=rank):
                        if fits(p, OVERLAY, not own and not own_lid, own and same, OVERLAY if own else 2 * OVERLAY):
                            best = p
                            break
                    flush = min(abs(cur - f) for f, _, _, _, _ in faces) < FACE_MIN - 1e-4
                    if best is None and flush:
                        # места на OVERLAY нет (грань между двумя соседними): хотя бы FACE_MIN — так World/FaceCheck
                        # пару не видит; в любую сторону, до 2 × OVERLAY, кроме пары с веком — только внутрь (блик
                        # глаза сквозь закрытое веко); у остальных разных частей выступ ≤ FACE_MIN ничего не пробивает
                        steps = (-OVERLAY, OVERLAY, -FALLBACK_GAP, FALLBACK_GAP)
                        cands = {f + d for f, _, _, _, _ in faces for d in steps}
                        for p in sorted(cands, key=rank):
                            if fits(p, FALLBACK_GAP, lid and not own and not own_lid, False, 2 * OVERLAY):
                                best = p
                                break
                    if best is None:
                        if rnd == PASSES - 1:
                            if flush:
                                flush_left += 1
                            else:
                                near_left += 1
                        continue
                    b["ext"][k][side] = best
    moved = 0
    for b in boxes:
        n = sum(1 for k in range(3) for side in (0, 1) if abs(b["ext"][k][side] - b["start"][k][side]) > 1e-6)
        if not n:
            continue
        moved += n
        shift = Vector((0, 0, 0))
        for k in range(3):
            mid = (b["ext"][k][0] + b["ext"][k][1]) / 2 - (b["start"][k][0] + b["start"][k][1]) / 2
            shift += b["axes"][k] * mid
        e = b["e"]
        # центр — прежний плюс сдвиг по осям детали (без пересчёта через округлённый поворот)
        e["c"] = [round(e["c"][i] + shift[i], 4) for i in range(3)]
        e["s"] = [round(b["ext"][k][1] - b["ext"][k][0], 4) for k in range(3)]
    return moved, near_left, flush_left


def flush_pairs(parts, strict=False):
    """Проверка: видимые пары параллельных граней (любой поворот; в покое и в позах, что держатся) ближе FACE_MIN с
    перекрытием в плоскости (и примеры); strict — пороги World/FaceCheck, иначе — с запасом, как при разведении."""
    boxes = _boxes(parts)
    scene = _scene(boxes)
    count = 0
    examples = {}  # пара граней → в скольких позах вровень
    for i, b in enumerate(boxes):
        around = _near(b, scene)
        deferred = {id(o) for o in boxes[i + 1:]}
        for k in range(3):
            for side in (0, 1):
                cur = b["ext"][k][side]
                for f, _, _, _, who in _faces(b, k, side, around, "strict" if strict else "check", deferred):
                    if abs(cur - f) < FACE_MIN - 1e-4:
                        count += 1
                        key = (b["part"], b["col"], k, side, round(cur, 3)) + who
                        examples[key] = examples.get(key, 0) + 1
    return count, examples


flush_before, _ = flush_pairs(parts)
moved, near_left, flush_left = separate(parts)
flush_after, flush_examples = flush_pairs(parts)
flush_strict, _ = flush_pairs(parts, strict=True)
total = sum(len(v) for v in parts.values())
with open(DST, "w", encoding="utf-8", newline="\n") as f:
    json.dump({"source": "scripts/blender/boss3_ratking.py", "figures": len(records), "blocks": total,
               "parts": parts}, f, ensure_ascii=False, indent=1)
print(f"KING_PARTS фигур {len(records)} → деталей {total}, отступов граней {moved}; граней ближе OVERLAY осталось "
      f"{near_left}, вровень (< FACE_MIN) — {flush_left}; пар вровень (с запасом): было {flush_before}, стало "
      f"{flush_after}; по порогам FaceCheck — {flush_strict}",
      flush=True)
for ex, n in sorted(flush_examples.items(), key=lambda x: -x[1]):
    print("KING_FLUSH", ex, "поз:", n, flush=True)
for name in RIG:
    print(f"KING_PART {name}: {len(parts[name])}", flush=True)

# ── 4. Кадры: FBX с картами D54 и детали с одного ракурса ─────────────────────────────────────────────────────
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
studio = bpy.data.collections.new("Studio")
scene.collection.children.link(studio)
holder = bpy.data.objects.new("Holder", None)
studio.objects.link(holder)
DOWN = 1 / 3.0  # студия рассчитана на предметы ~4 стада: король ×1/3
holder.matrix_world = Matrix.Scale(DOWN, 4)
bpy.ops.import_scene.fbx(filepath=os.path.join(REPO, "assets", "models", "Boss3_RatKing.fbx"))
fbx = [o for o in scene.objects if o.type == "MESH" and o.name.startswith("Boss3_RatKing")]
tex = {}
for o in fbx:
    group = o.name[len("Boss3_RatKing"):].split("_", 1)[0]
    if group not in tex:
        m = bpy.data.materials.new(f"Tex{group}")
        m.use_nodes = True
        nt = m.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        t = nt.nodes.new("ShaderNodeTexImage")
        color = os.path.join(REPO, "assets", "textures", "art", f"Boss3_RatKing{group}_color.png")
        t.image = bpy.data.images.load(color)
        nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.55
        tex[group] = m
    o.data.materials.clear()
    o.data.materials.append(tex[group])
    o.parent = holder
mats, blocks = {}, []
TO_B = AX.transposed()
for name, lst in parts.items():
    pivot = Vector(RIG[name][1]) * SCALE
    for e in lst:
        bm = bmesh.new()
        if e.get("shape") == "Cylinder":
            bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.5, radius2=0.5, depth=1.0)
            bmesh.ops.rotate(bm, verts=bm.verts, matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
        else:
            bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=e["s"], verts=bm.verts)
        r = Matrix(((e["r"][0:3]), (e["r"][3:6]), (e["r"][6:9]))) if "r" in e else Matrix.Identity(3)
        m = (TO_B @ r).to_4x4()  # оси детали → оси Roblox → оси Blender; размер — по осям детали
        m.translation = pivot + TO_B @ Vector(e["c"])
        bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
        me = bpy.data.meshes.new("Blk")
        bm.to_mesh(me)
        bm.free()
        key = e["col"]
        if key not in mats:
            mt = bpy.data.materials.new(key)
            mt.use_nodes = True
            b = next(n for n in mt.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            b.inputs["Base Color"].default_value = (*S.lin(key), 1)
            b.inputs["Roughness"].default_value = 0.55
            mats[key] = mt
        me.materials.append(mats[key])
        ob = bpy.data.objects.new("Blk", me)
        studio.objects.link(ob)
        ob.parent = holder
        blocks.append(ob)
prev = S.Preview(scene.collection)
for which, models in (("fbx", fbx), ("blocks", blocks)):
    for o in fbx + blocks:
        o.hide_render = o not in models
    center = Vector((0, 0, 15 * DOWN / 2))
    prev.aim_lights(center)
    for tag, eye, target, lens in (("front", (0, -11, 4.1), center, 50),
                                   ("three_quarter", (-6.5, -9, 4.7), center, 50),
                                   ("side", (-11, -0.5, 4.1), center, 50),
                                   ("face", (-1.2, -6.5, 3.8), Vector((0, 0, 3.45)), 70)):
        prev.shot(os.path.join(OUT, f"king_{tag}_{which}.png"), tuple(Vector(eye)), target, lens, (800, 900))
print("KING_RENDER_OK", OUT, flush=True)
