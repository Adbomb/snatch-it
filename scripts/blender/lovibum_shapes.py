"""Геометрия Ловибумов v5 «кристалл в когтях» (D55) — одна для концептов, игровых моделей и Part-версии.

Утверждено владельцем 2026-11-08 (концепт v5): четыре когтя-пластины держат кристалл-ромб и раскрываются при поимке;
прогрессия читается по кристаллу (маленький → вытянутый → огромный):
- Бум (×1): простой и цельный — большое ядро-шар, короткие толстые когти с заклёпками, крупные защёлки;
- Турбо (×1.5): высокое ядро, хищные когти с широкой световой полосой, стреловидные стабилизаторы, сопло-кольцо;
- Мега (×2): ядро — огромный гранёный кристалл в золотой оправе-короне, золотые зубцы с камнями.
Без глаз, ртов и лиц.

Подвижные части (a.group): Base (корень: ножка, база, защёлки, стабилизаторы, корона), Core (энергетическое ядро —
в игре Neon), Claw1…Claw4 (коготь целиком; точка вращения — основание, ось раскрытия — касательная), Crystal
(кристалл — Neon; при раскрытии поднимается). После lovibum() у объекта есть a.rig (часть → (родитель, точка
вращения)), a.axes (коготь → ось раскрытия), a.lift (подъём кристалла при раскрытии) и a.light (точка света ядра).

Деталь — вызовы a.box / a.prism / a.frustum / a.extrude (art_style.Art или любой класс с тем же набором, например
запись Part-версии в lovibum_models.py). 1 единица = 1 стад, z вверх, лицом в −y.
Зависит от art_style.py (Blender: bmesh, mathutils).
"""

import math

from mathutils import Matrix, Vector

import art_style as S

GLOW = {"core": 1.4, "crystal": 1.6, "crystal2": 1.4, "glow": 2.4, "net": 2.0, "spark": 2.6}  # светящиеся ключи и сила свечения
NEON = ("core", "crystal", "crystal2", "glow")  # в игре — материал Neon (решение владельца 2026-11-08)

TYPES = {
    "Boom": {"claw": "FF8A1F", "knuckle": "FFC21A", "tip": "FFC21A", "base": "FFC21A", "foot": "2A3344",
             "trim": "E8641A", "core": "2EE6D6", "crystal": "22D8C8", "glow": "8AFFF2", "light_z": 0.5,
             "scale": (1.0, 1.0, 1.0)},
    "Turbo": {"claw": "2F6BFF", "knuckle": "1E2B4F", "tip": "E6F3FF", "base": "E6F3FF", "foot": "1E2B4F",
              "trim": "1E2B4F", "core": "3FD8FF", "crystal": "2CB8FF", "glow": "5CE8FF", "light_z": 0.6,
              "scale": (1.0, 1.0, 1.0)},
    "Mega": {"claw": "7A2FE0", "knuckle": "F2C230", "tip": "F2C230", "base": "F2C230", "foot": "6A1FC0",
             "trim": "C98E12", "core": "E57BFF", "crystal": "D45CFF", "glow": "FFD1FF", "light_z": 0.8,
             "scale": (1.0, 1.0, 1.0)},
}
OPEN_DEG = 52  # раскрытие когтей при поимке
CLAWS = ("Claw1", "Claw2", "Claw3", "Claw4")


# ── Помощники ────────────────────────────────────────────────────────────────────────────────────────────────


def sq(h, cut):
    return S.octagon(-h, h, -h, h, cut)


def bar(a, key, p0, p1, w, h=None, bevel=S.BEVEL):
    """Брусок от p0 до p1 с сечением w × h (поворот сечения — как получится; для сетей и следов)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    up = "Y" if abs(d.normalized().z) > 0.95 else "Z"
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("X", up).to_matrix().to_4x4()
    h = h or w
    a.box(key, -d.length / 2, d.length / 2, -w / 2, w / 2, -h / 2, h / 2, bevel=bevel, matrix=m)


def bar_side(a, key, p0, p1, w, h, side, bevel=S.BEVEL, extend=0.0):
    """Брусок от p0 до p1: ширина w вдоль side (поперёк плоскости когтя), толщина h — в плоскости когтя."""
    p0, p1 = Vector(p0), Vector(p1)
    x = (p1 - p0).normalized()
    y = (side - x * side.dot(x)).normalized()
    z = x.cross(y)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = (p0 + p1) / 2
    half = (p1 - p0).length / 2 + extend
    a.box(key, -half, half, -w / 2, w / 2, -h / 2, h / 2, bevel=bevel, matrix=m)


def paint(a, spec):
    for key, code, rings in (("claw", spec["claw"], True), ("knuckle", spec["knuckle"], False),
                             ("tip", spec["tip"], False), ("base", spec["base"], False), ("foot", spec["foot"], False),
                             ("trim", spec["trim"], False), ("core", spec["core"], False),
                             ("crystal", spec["crystal"], False), ("crystal2", "FFC8FF", False),
                             ("glow", spec["glow"], False), ("gemp", "FF3B7F", False), ("gemc", "3FE0FF", False),
                             ("white", "FFFDF4", False)):
        a.paint(key, code, rings)


def claw(a, theta, prof, widths, thick, open_deg=0.0, cap=None, cap_at=1, strip=None, tip_scale=1.0):
    """Коготь-пластина в вертикальной плоскости под углом theta: сегменты сужаются к кончику (ширина поперёк плоскости
    когтя, толщина — по радиусу), чередование толщины — без совпадающих граней; cap — крупная заклёпка-колпачок на
    сгибе cap_at; strip — одна широкая полоса по наружной стороне средних сегментов; кончик — коготь-крючок к кристаллу.
    open_deg — раскрытие наружу вокруг основания. Возвращает (точки, ось раскрытия)."""
    u = Vector((math.cos(theta), math.sin(theta), 0))
    t = Vector((-math.sin(theta), math.cos(theta), 0))
    pts = [u * r + Vector((0, 0, z)) for r, z in prof]
    if open_deg:
        rot = Matrix.Rotation(math.radians(open_deg), 4, t)
        pts = [pts[0] + (rot @ (p - pts[0])) for p in pts]
    n = len(pts) - 1

    def outward(i):
        d = (pts[min(i + 1, n)] - pts[max(i - 1, 0)]).normalized()
        o = t.cross(d).normalized()
        return o if o.dot(u) >= 0 or open_deg else -o

    for i in range(n):
        bar_side(a, "claw", pts[i], pts[i + 1], widths[i], thick * (1 if i % 2 == 0 else 0.9), t, extend=0.03)
    if cap:
        o = outward(cap_at)
        m = Matrix.Translation(pts[cap_at] + o * (thick * 0.4)) @ o.to_track_quat("Z", "Y").to_matrix().to_4x4()
        a.prism(cap, sq(0.085, 0.028), 0.0, 0.08, matrix=m)
    if strip:
        for i in range(1, n - 1):
            o = outward(i) if not open_deg else (t.cross((pts[i + 1] - pts[i]).normalized())).normalized()
            if o.dot(u) < 0 and not open_deg:
                o = -o
            off = o * (thick / 2 + 0.006)
            bar_side(a, strip, pts[i] + off, pts[i + 1] + off, 0.1 + 0.006 * (i % 2), 0.03, t, bevel=0)
    tip = pts[-1]
    inward = Vector((-u.x, -u.y, 0))
    hook = inward * 0.1 * tip_scale + Vector((0, 0, 0.06 * tip_scale))
    bar_side(a, "tip", tip, tip + hook, widths[-1] * 0.85, thick * 1.15, t, extend=0.035)
    return pts, t


def crystal(a, lo, mid, hi, half, key="crystal", lift=0.0, turn=45.0):
    """Кристалл-ромб (бипирамида; поворот turn: при 45° грани смотрят на когти)."""
    rot = Matrix.Translation((0, 0, lift)) @ Matrix.Rotation(math.radians(turn), 4, "Z")
    a.frustum(key, (-0.02, 0.02, -0.02, 0.02), (-half, half, -half, half), lo, mid + 0.005, matrix=rot)
    a.frustum(key, (-half, half, -half, half), (-0.02, 0.02, -0.02, 0.02), mid - 0.005, hi, matrix=rot)


def _rig(a, group, parent, pivot):
    if not hasattr(a, "rig"):
        a.rig, a.axes = {}, {}
    a.rig[group] = (parent, tuple(pivot))
    a.group = group


def claws(a, prof, widths, thick, opened, **kw):
    for k in range(4):
        theta = math.pi / 4 + k * math.pi / 2
        u = Vector((math.cos(theta), math.sin(theta), 0))
        _rig(a, CLAWS[k], "Base", u * prof[0][0] + Vector((0, 0, prof[0][1])))
        _, axis = claw(a, theta, prof, widths, thick, OPEN_DEG if opened else 0.0, **kw)
        a.axes[CLAWS[k]] = tuple(axis)


def _crystal_part(a, lo, mid, hi, half, lift, opened, extra=None):
    """Часть Crystal: кристалл (и второй ряд граней у Меги); точка вращения — центр ромба, подъём при раскрытии."""
    _rig(a, "Crystal", "Base", (0, 0, mid))
    a.lift = lift
    up = lift if opened else 0.0
    crystal(a, lo, mid, hi, half, lift=up)
    if extra:
        crystal(a, *extra, key="crystal2", lift=up, turn=0.0)  # второй ряд граней — «огранка»


# ── Ловибумы: общая конструкция «кристалл в когтях» ─────────────────────────────────────────────────────────


def boom(a, opened):
    """Бум — простой и цельный: большое ядро-шар, четыре коротких толстых когтя-пластины с заклёпками, крупные
    защёлки, небольшой кристалл на макушке ядра."""
    _rig(a, "Base", None, (0, 0, 0))
    a.prism("foot", sq(0.3, 0.09), 0.0, 0.08)
    a.prism("base", sq(0.48, 0.15), 0.06, 0.22)
    for s in (-1, 1):
        a.box("base", s * 0.44, s * 0.63, -0.15, 0.15, 0.3, 0.62)
        a.box("trim", s * 0.6, s * 0.69, -0.11, 0.11, 0.52, 0.68)
        a.box("trim", s * 0.615, s * 0.65, -0.08, 0.08, 0.36, 0.43)
    _rig(a, "Core", "Base", (0, 0, 0.517))
    for h, z0, z1 in ((0.27, 0.18, 0.29), (0.39, 0.27, 0.41), (0.45, 0.39, 0.627), (0.39, 0.607, 0.75),
                      (0.27, 0.73, 0.85)):
        a.prism("core", sq(h, h * 0.32), z0, z1)
    claws(a, [(0.42, 0.16), (0.56, 0.36), (0.56, 0.6), (0.43, 0.79), (0.29, 0.88)], (0.46, 0.44, 0.38, 0.3), 0.16,
          opened, cap="knuckle", cap_at=2, tip_scale=1.1)
    _crystal_part(a, 0.8, 1.0, 1.28, 0.18, 0.16, opened)
    a.light = (0, 0, 0.5)


def turbo(a, opened):
    """Турбо — быстрый и чистый: высокое ядро, хищные когти с одной широкой световой полосой, крупные стреловидные
    стабилизаторы с яркой кромкой, сопло-кольцо, вытянутый кристалл."""
    _rig(a, "Base", None, (0, 0, 0))
    a.prism("glow", sq(0.2, 0.06), -0.05, 0.015)
    a.prism("foot", sq(0.28, 0.08), 0.0, 0.07)
    a.prism("base", sq(0.41, 0.125), 0.05, 0.2)
    fin = [(0.38, 0.18), (0.38, 0.84), (0.58, 0.75), (0.98, 0.22), (1.0, 0.03), (0.76, 0.1)]
    for s in (-1, 1):
        a.extrude("trim", [(s * x, z) for x, z in fin], -0.045, 0.045, axis="y")
        bar_side(a, "glow", Vector((s * 0.58, 0, 0.78)), Vector((s * 1.0, 0, 0.21)), 0.11, 0.07, Vector((0, 1, 0)),
                 bevel=0)
    _rig(a, "Core", "Base", (0, 0, 0.595))
    for h, z0, z1 in ((0.19, 0.17, 0.3), (0.29, 0.28, 0.45), (0.35, 0.43, 0.72), (0.29, 0.7, 0.9), (0.18, 0.88, 1.02)):
        a.prism("core", sq(h, h * 0.32), z0, z1)
    claws(a, [(0.34, 0.14), (0.45, 0.38), (0.45, 0.64), (0.35, 0.88), (0.2, 1.04)], (0.32, 0.3, 0.25, 0.19), 0.12,
          opened, strip="glow")
    _crystal_part(a, 0.92, 1.15, 1.58, 0.15, 0.16, opened)
    a.light = (0, 0, 0.6)


def mega(a, opened):
    """Мега — самый ценный: ядро — огромный гранёный кристалл в золотой оправе-короне: короткие фиолетовые когти с
    крупными золотыми когтями-кончиками и заклёпками, золотые зубцы-короны с камнями между когтями, золотая база."""
    _rig(a, "Base", None, (0, 0, 0))
    a.prism("foot", sq(0.36, 0.11), 0.0, 0.08)
    a.prism("base", sq(0.5, 0.155), 0.06, 0.22)
    a.prism("trim", sq(0.44, 0.135), 0.2, 0.26)
    for k in range(4):  # золотые зубцы-короны с камнями между когтями
        ang = k * math.pi / 2
        turn = Matrix.Rotation(ang, 4, "Z")
        for r, w, z0, z1 in ((0.5, 0.2, 0.2, 0.46), (0.55, 0.14, 0.44, 0.62), (0.6, 0.075, 0.6, 0.78)):
            a.box("knuckle", r - 0.06, r + 0.06, -w / 2, w / 2, z0, z1, matrix=turn)
        a.box("gemp" if k % 2 else "gemc", 0.555, 0.6, -0.065, 0.065, 0.26, 0.4, matrix=turn)
    _crystal_part(a, 0.22, 0.86, 1.5, 0.32, 0.2, opened, extra=(0.34, 0.86, 1.36, 0.25))
    claws(a, [(0.44, 0.18), (0.56, 0.38), (0.52, 0.62), (0.38, 0.8)], (0.4, 0.37, 0.3), 0.15, opened,
          cap="knuckle", cap_at=1, tip_scale=1.7)
    a.light = (0, 0, 0.8)


BUILD = {"Boom": boom, "Turbo": turbo, "Mega": mega}


def lovibum(name, opened=False, art_cls=None):
    """Ловибум name (закрыт или с раскрытыми когтями) — объект art_cls (по умолчанию art_style.Art)."""
    spec = TYPES[name]
    a = (art_cls or S.Art)("Lovibum_" + name + ("_open" if opened else ""), ring_z0=0.6)
    paint(a, spec)
    BUILD[name](a, opened)
    return a
