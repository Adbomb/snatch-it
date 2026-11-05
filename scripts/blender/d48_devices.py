"""D48 v2 — устройства защиты музея в Blender из деталей Roblox (Block, Cylinder, Ball, Wedge): ловушка, капкан,
лазерные стойки, бронедверь, робот-охранник, метка установки. Каждое — в обычном и активном состоянии.

Единый язык устройств: тёмно-синий корпус, белые панели, золотые кольца и кромки, сталь; дежурный огонёк —
бирюзовый, срабатывание — красный; жёлто-чёрная разметка опасности — только у напольных устройств и двери.
Начало координат устройства — центр на полу, «лицо» — к −Z (как Defense.luau). Деталей: 15–35 на устройство.

Как модуль: import d48_devices as D; D.trap(K, (x, 0, z), yaw, "idle"). Сам по себе — рендер листов:
blender --background --factory-startup --python scripts/blender/d48_devices.py -- <репо> [--fast]
→ assets/concepts/d48/v2/devices/*.png и bricks/devices.json.
"""

import math
import os
import sys

from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import d48_kit as K  # noqa: E402

P = {
    "navy": "26345E", "navyDark": "1A2440", "white": "F4F7FB", "steel": "A7B6C8", "steelDark": "5E7186",
    "gold": "E9B43C", "goldDeep": "C98E1E", "hazard": "FFC93C", "ink": "2A2A33", "cyan": "39E1FF",
    "red": "FF3B3B", "orange": "FF7A1A", "green": "4CE07A", "glow": "BDEBFF",
}


def state_color(state):
    return {"idle": P["cyan"], "active": P["red"], "hack": P["orange"], "open": P["green"]}[state]


class Frame:
    """Локальные оси устройства: точка на полу и поворот вокруг вертикали (градусы, как CFrame.Angles(0, a, 0))."""

    def __init__(self, origin, yaw=0.0, prefix="Dev"):
        self.o = Vector(origin)
        self.r = K.rot_y(yaw)
        self.prefix = prefix

    def at(self, p):
        return tuple(self.o + self.r @ Vector(p))

    def box(self, name, x0, x1, y0, y1, z0, z1, color, mat="Plastic", rot=None, pivot=None, local_pivot=None,
            local_rot=None, **kw):
        c = Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        size = (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
        lr = rot or K.ID
        if pivot is not None and rot is not None:
            outer = rot @ local_rot.inverted() if local_rot is not None else rot
            c = Vector(pivot) + outer @ (c - Vector(pivot))
        return K.part(f"{self.prefix}_{name}", "Block", size, self.at(c), color, mat, rot=self.r @ lr, **kw)

    def cyl(self, name, c, length, dia, color, axis="y", mat="Plastic", rot=None, pivot=None, **kw):
        c = Vector(c)
        lr = rot or K.ID
        if pivot is not None and rot is not None:
            c = Vector(pivot) + rot @ (c - Vector(pivot))
        return K.part(f"{self.prefix}_{name}", "Cylinder", (length, dia, dia), self.at(c), color, mat,
                      rot=self.r @ lr @ K.AXIS[axis], **kw)

    def ball(self, name, c, dia, color, mat="Plastic", **kw):
        return K.part(f"{self.prefix}_{name}", "Ball", (dia, dia, dia), self.at(c), color, mat, rot=self.r, **kw)

    def wedge(self, name, size, c, color, rot=None, mat="Plastic", pivot=None, local_pivot=None, local_rot=None,
              **kw):
        c = Vector(c)
        lr = rot or K.ID
        if pivot is not None and rot is not None:
            outer = rot @ local_rot.inverted() if local_rot is not None else rot
            c = Vector(pivot) + outer @ (c - Vector(pivot))
        return K.part(f"{self.prefix}_{name}", "Wedge", size, self.at(c), color, mat, rot=self.r @ lr, **kw)


# ── 1. Ловушка «Пружинная плита» (радиус 2): плита с разметкой, в активном — шипы и красная вспышка ─────────────
def trap(origin, yaw=0.0, state="idle", prefix="Trap"):
    f = Frame(origin, yaw, prefix)
    s = state_color(state)
    f.box("Base", -2.1, 2.1, 0, 0.3, -2.1, 2.1, P["navyDark"], bevel=0.08)
    for name, x0, x1, z0, z1 in (("RimN", -2.1, 2.1, -2.1, -1.7), ("RimS", -2.1, 2.1, 1.7, 2.1),
                                 ("RimW", -2.1, -1.7, -1.7, 1.7), ("RimE", 1.7, 2.1, -1.7, 1.7)):
        f.box(name, x0, x1, 0.3, 0.42, z0, z1, P["hazard"], bevel=0.03)
    for sx, sz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):  # чёрные уголки разметки
        f.box("Corner", sx * 2.15 - 0.45, sx * 2.15 + 0.45, 0.3, 0.46, sz * 2.15 - 0.45, sz * 2.15 + 0.45,
              P["ink"], bevel=0.03)
    f.box("Pad", -1.55, 1.55, 0.3, 0.45, -1.55, 1.55, P["steel"], bevel=0.05)
    spots = ((0, 0), (-0.85, -0.85), (0.85, -0.85), (-0.85, 0.85), (0.85, 0.85))
    for k, (sx, sz) in enumerate(spots):
        if state == "active":
            f.box(f"Spike{k}", sx - 0.34, sx + 0.34, 0.45, 0.95, sz - 0.34, sz + 0.34, P["gold"], bevel=0.04)
            f.box(f"Mid{k}", sx - 0.22, sx + 0.22, 0.95, 1.4, sz - 0.22, sz + 0.22, P["steel"], bevel=0.03)
            f.box(f"Tip{k}", sx - 0.1, sx + 0.1, 1.4, 1.8, sz - 0.1, sz + 0.1, P["white"], bevel=0.02)
        else:
            f.box(f"Hole{k}", sx - 0.3, sx + 0.3, 0.45, 0.47, sz - 0.3, sz + 0.3, P["navyDark"], bevel=0.0)
    f.cyl("Status", (0, 0.42, -1.9), 0.12, 0.42, s, "y", "Neon", glow=4)
    if state == "active":
        f.box("Flash", -2.35, 2.35, 0.05, 0.12, -2.35, 2.35, P["red"], "Neon", glow=2, bevel=0, collide=False)


# ── 2. Капкан «Захват» (10 с): круглое основание, две челюсти-дуги с зубцами, пружины; активный — сомкнуты ────
def snare(origin, yaw=0.0, state="idle", prefix="Snare"):
    f = Frame(origin, yaw, prefix)
    s = state_color(state)
    f.cyl("Rim", (0, 0.08, 0), 0.16, 3.4, P["hazard"], "y", bevel=0.03)
    f.cyl("Base", (0, 0.28, 0), 0.24, 3.0, P["navyDark"], "y", bevel=0.05)
    f.cyl("Pad", (0, 0.45, 0), 0.12, 1.1, P["red"] if state == "active" else P["steel"], "y", bevel=0.03)
    for sx in (-1, 1):
        f.cyl("Spring", (sx * 1.38, 0.55, 0), 0.42, 0.5, P["gold"], "x", bevel=0.04)
    r, hy = 1.3, 0.55  # радиус дуги и высота шарнира
    for side in (-1, 1):  # −1 — передняя челюсть, +1 — задняя
        hinge = Vector((0, hy, 0))
        lay = 0 if state == "active" else side * 84  # раскрыта: почти плашмя наружу
        rot = K.rot_x(lay)
        dz = side * 0.13
        for k, (a0, a1) in enumerate(((180, 120), (120, 60), (60, 0))):  # полуокружность тремя хордами
            m = math.radians((a0 + a1) / 2)
            cx, cy = math.cos(m) * r * 0.93, hy + math.sin(m) * r * 0.93
            seg = K.rot_z((a0 + a1) / 2 - 90)  # хорда по касательной к дуге
            f.box(f"Jaw{side}{k}", cx - r * 0.53, cx + r * 0.53, cy - 0.14, cy + 0.14, dz - 0.13, dz + 0.13,
                  P["steelDark"], rot=rot @ seg, pivot=hinge, bevel=0.04, local_pivot=(cx, cy, dz), local_rot=seg)
        for k, ang in enumerate((150, 90, 30) if side < 0 else (120, 60)):
            m = math.radians(ang)
            tx, ty = math.cos(m) * r * 0.62, hy + math.sin(m) * r * 0.62
            tooth = K.rot_z(ang + 90)  # остриё — к центру дуги
            f.wedge(f"Tooth{side}{k}", (0.24, 0.42, 0.2), (tx, ty, dz), P["white"], rot=rot @ tooth, pivot=hinge,
                    bevel=0.02, local_pivot=(tx, ty, dz), local_rot=tooth)
    f.box("Status", -0.2, 0.2, 0.4, 0.52, -1.5, -1.3, s, "Neon", glow=4, bevel=0.02)
    if state == "active":
        f.cyl("Glow", (0, 0.02, 0), 0.04, 4.0, P["red"], "y", "Neon", glow=2, collide=False, bevel=0)


# ── 3. Лазерные стойки: две колонны и луч на высоте y (вдоль X), активный — луч толще, маяки красные ───────────
def laser(origin, yaw=0.0, state="idle", length=10.8, y=2.4, prefix="Laser"):
    f = Frame(origin, yaw, prefix)
    s = state_color(state)
    half = length / 2
    for sx in (-1, 1):
        x = sx * half
        f.cyl(f"Foot{sx}", (x, 0.15, 0), 0.3, 1.3, P["navyDark"], "y", bevel=0.05)
        f.cyl(f"Collar{sx}", (x, 0.4, 0), 0.2, 1.0, P["gold"], "y", bevel=0.03)
        f.box(f"Column{sx}", x - 0.35, x + 0.35, 0.5, y + 1.3, -0.35, 0.35, P["navy"], bevel=0.05)
        for by in (1.0, y + 0.95):
            f.box(f"Band{sx}", x - 0.42, x + 0.42, by, by + 0.14, -0.42, 0.42, P["gold"], bevel=0.02)
        f.box(f"Head{sx}", x - 0.45, x + 0.45, y - 0.35, y + 0.35, -0.45, 0.45, P["white"], bevel=0.06)
        f.cyl(f"Lens{sx}", (x - sx * 0.5, y, 0), 0.16, 0.42, P["red"], "x", "Neon", glow=5, bevel=0.01)
        f.box(f"Cap{sx}", x - 0.45, x + 0.45, y + 1.3, y + 1.45, -0.45, 0.45, P["gold"], bevel=0.03)
        f.ball(f"Beacon{sx}", (x, y + 1.68, 0), 0.46, s, "Neon", glow=4)
    thick = 0.2 if state == "active" else 0.1
    f.box("Beam", -half + 0.6, half - 0.6, y - thick / 2, y + thick / 2, -thick / 2, thick / 2, P["red"], "Neon",
          glow=7 if state == "active" else 9, bevel=0, collide=False)
    if state == "active":
        f.box("BeamGlow", -half + 0.6, half - 0.6, y - 0.22, y + 0.22, -0.22, 0.22, "FF7A7A", "Glass", alpha=0.25,
              bevel=0, collide=False)


def laser_sockets(origin, yaw=0.0, length=10.8, prefix="LaserMark"):
    """Размеченное место лазера в проходе (без устройства): два латунных гнезда и тонкая линия в полу."""
    f = Frame(origin, yaw, prefix)
    for sx in (-1, 1):
        f.cyl(f"Socket{sx}", (sx * length / 2, 0.03, 0), 0.06, 0.9, P["steelDark"], "y", bevel=0.01)
    f.box("Line", -length / 2 + 0.45, length / 2 - 0.45, 0.0, 0.04, -0.04, 0.04, "D2453F", bevel=0)


# ── 4. Бронедверь в проёме 12 × 10: две створки, круглый замок-штурвал, лампа; взлом — устройство на замке ──────
def door(origin, yaw=0.0, state="idle", width=12.0, height=10.0, prefix="Door"):
    f = Frame(origin, yaw, prefix)
    s = state_color(state)
    slide = 6.05 if state == "open" else 0.0
    hw = width / 2 - 0.1
    for side in (-1, 1):
        x0, x1 = (-hw - slide, -0.05 - slide) if side < 0 else (0.05 + slide, hw + slide)
        f.box(f"Leaf{side}", x0, x1, 0.05, height - 0.1, -0.4, 0.4, P["navy"], bevel=0.06)
        f.box(f"Panel{side}", x0 + 0.5, x1 - 0.5, 2.0, height - 0.9, -0.52, -0.38, P["steel"], bevel=0.05)
        for by in (3.2, height - 2.4):
            f.box(f"Bar{side}", x0 + 0.3, x1 - 0.3, by, by + 0.5, -0.62, -0.5, P["gold"], bevel=0.04)
        f.box(f"Hazard{side}", x0 + 0.1, x1 - 0.1, 0.25, 1.65, -0.5, -0.38, P["hazard"], bevel=0.03)
        for k in range(3):  # косые чёрные полосы разметки
            cx = x0 + 0.9 + k * (x1 - x0 - 1.8) / 2
            f.box(f"Stripe{side}{k}", cx - 0.22, cx + 0.22, 0.3, 1.6, -0.56, -0.48, P["ink"], rot=K.rot_z(35),
                  pivot=(cx, 0.95, -0.52), bevel=0.01)
        for rx in (x0 + 0.55, x1 - 0.55):  # заклёпки по краям
            for ry in (2.2, height - 1.0):
                f.cyl(f"Rivet{side}", (rx, ry, -0.5), 0.14, 0.32, P["goldDeep"], "z", bevel=0.02)
    lx = -slide  # замок — на левой створке (в открытом виде уезжает с ней в стену)
    cy = height * 0.52
    if state == "open":
        f.box("LampBase", -0.9, 0.9, height + 0.05, height + 0.45, -0.6, 0.0, P["navyDark"], bevel=0.04)
        f.box("Lamp", -0.65, 0.65, height + 0.45, height + 0.85, -0.5, -0.1, s, "Neon", glow=4, bevel=0.04)
        return
    f.cyl("LockRing", (lx, cy, -0.5), 0.3, 3.4, P["gold"], "z", bevel=0.06)
    f.cyl("LockDisk", (lx, cy, -0.68), 0.25, 2.8, P["steel"], "z", bevel=0.06)
    f.cyl("LockGlow", (lx, cy, -0.84), 0.12, 1.5, s, "z", "Neon", glow=3, bevel=0.01)
    f.cyl("LockHub", (lx, cy, -0.96), 0.2, 0.9, P["gold"], "z", bevel=0.04)
    for k in range(2):
        f.box(f"Spoke{k}", lx - 1.25, lx + 1.25, cy - 0.12, cy + 0.12, -1.0, -0.86, P["goldDeep"], rot=K.rot_z(45 + 90 * k),
              pivot=(lx, cy, -0.93), bevel=0.03)
    f.box("LampBase", -0.9, 0.9, height + 0.05, height + 0.45, -0.6, 0.0, P["navyDark"], bevel=0.04)
    f.box("Lamp", -0.65, 0.65, height + 0.45, height + 0.85, -0.5, -0.1, s, "Neon", glow=4, bevel=0.04)
    if state == "hack":  # взломщик на замке: корпус, экран с полосой прогресса
        f.box("HackBody", lx - 0.8, lx + 0.8, cy - 1.75, cy - 0.95, -1.35, -0.75, P["ink"], bevel=0.05)
        f.box("HackScreen", lx - 0.6, lx + 0.6, cy - 1.6, cy - 1.1, -1.4, -1.34, P["navyDark"], bevel=0)
        f.box("HackBar", lx - 0.55, lx + 0.15, cy - 1.45, cy - 1.25, -1.43, -1.39, P["orange"], "Neon", glow=3, bevel=0)


# ── 5. Робот-охранник: стоит на месте, лицо −Z; активный — красный визор, дубинка вперёд, разряд ───────────────
def robot(origin, yaw=0.0, state="idle", prefix="Robot"):
    f = Frame(origin, yaw, prefix)
    s = state_color(state)
    f.cyl("Base", (0, 0.25, 0), 0.5, 2.9, P["navyDark"], "y", bevel=0.06)
    f.cyl("BaseRing", (0, 0.58, 0), 0.16, 3.1, P["gold"], "y", bevel=0.03)
    f.cyl("Turret", (0, 0.86, 0), 0.4, 2.2, P["steel"], "y", bevel=0.05)
    f.cyl("Waist", (0, 1.35, 0), 0.6, 1.4, P["steelDark"], "y", bevel=0.04)
    f.box("Body", -1.2, 1.2, 1.65, 3.85, -0.9, 0.9, P["white"], bevel=0.12)
    f.box("Chest", -0.85, 0.85, 2.05, 3.45, -1.02, -0.8, P["navy"], bevel=0.06)
    f.cyl("Badge", (0, 2.95, -1.1), 0.16, 0.7, P["gold"], "z", bevel=0.03)
    f.box("ChestLight", -0.55, 0.55, 2.3, 2.45, -1.1, -0.98, s, "Neon", glow=3.5, bevel=0.01)
    swing = 75 if state == "active" else 0  # правая рука: опущена с дубинкой вперёд / поднята для удара
    for sx in (-1, 1):
        sh = Vector((sx * 1.5, 3.45, 0))
        f.ball(f"Shoulder{sx}", (sx * 1.5, 3.45, 0), 1.0, P["navy"])
        rot = K.rot_x(swing if sx > 0 else 0)
        f.box(f"Upper{sx}", sx * 1.5 - 0.35, sx * 1.5 + 0.35, 2.3, 3.2, -0.35, 0.35, P["white"], rot=rot, pivot=sh,
              bevel=0.06)
        f.box(f"Fore{sx}", sx * 1.5 - 0.42, sx * 1.5 + 0.42, 1.2, 2.3, -0.42, 0.42, P["navy"], rot=rot, pivot=sh,
              bevel=0.06)
        if sx > 0:  # дубинка в кулаке, смотрит вперёд
            f.box("Fist", 1.5 - 0.4, 1.5 + 0.4, 0.75, 1.25, -0.42, 0.42, P["steelDark"], rot=rot, pivot=sh, bevel=0.06)
            f.cyl("Baton", (1.5, 1.0, -1.2), 1.9, 0.34, P["ink"], "z", rot=rot, pivot=sh, bevel=0.03)
            f.cyl("BatonTip", (1.5, 1.0, -2.4), 0.55, 0.5, s, "z", "Neon", rot=rot, pivot=sh, glow=4, bevel=0.02)
    f.box("Neck", -0.4, 0.4, 3.85, 4.1, -0.4, 0.4, P["steelDark"], bevel=0.04)
    f.box("Head", -0.95, 0.95, 4.1, 5.35, -0.8, 0.8, P["white"], bevel=0.14)
    f.box("Visor", -0.75, 0.75, 4.5, 4.95, -0.9, -0.76, s, "Neon", glow=4.5, bevel=0.04)
    for sx in (-1, 1):
        f.cyl(f"Ear{sx}", (sx * 1.05, 4.75, 0), 0.3, 0.75, P["navy"], "x", bevel=0.04)
    f.cyl("Antenna", (0, 5.75, 0), 0.8, 0.14, P["steelDark"], "y", bevel=0.01)
    f.ball("AntennaTip", (0, 6.25, 0), 0.38, s, "Neon", glow=4.5)
    if state == "active":  # разряд у дубинки: три искры зигзагом
        arm = K.rot_x(swing)
        tip = Vector((0, 3.45, 0)) + arm @ (Vector((1.5, 1.0, -2.75)) - Vector((0, 3.45, 0)))
        for k, (dx, dy, a) in enumerate(((-0.35, 0.1, 35), (0.35, 0.25, -30), (0.0, 0.55, 15))):
            c = tip + Vector((dx, dy, 0))
            f.box(f"Zap{k}", c.x - 0.06, c.x + 0.06, c.y - 0.3, c.y + 0.3, c.z - 0.06, c.z + 0.06, P["glow"], "Neon",
                  rot=K.rot_z(a), pivot=tuple(c), glow=6, bevel=0, collide=False)
        f.cyl("Alarm", (0, 0.04, 0), 0.06, 4.4, P["red"], "y", "Neon", glow=2, collide=False, bevel=0)


# ── 6. Метка установки (подготовка): голографическая плита и уголки — где встанет устройство ───────────────────
def placement(origin, size=4.2, yaw=0.0, ok=True, prefix="Place"):
    f = Frame(origin, yaw, prefix)
    c = P["cyan"] if ok else P["red"]
    h = size / 2
    f.box("Holo", -h, h, 0.02, 0.06, -h, h, c, "Glass", alpha=0.3, bevel=0, collide=False)
    for sx, sz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        f.box("CornerA", sx * h - (0.9 if sx > 0 else 0), sx * h + (0 if sx > 0 else 0.9), 0.06, 0.16,
              sz * h - 0.12, sz * h + 0.12, c, "Neon", glow=3, bevel=0, collide=False)
        f.box("CornerB", sx * h - 0.12, sx * h + 0.12, 0.06, 0.16, sz * h - (0.9 if sz > 0 else 0),
              sz * h + (0 if sz > 0 else 0.9), c, "Neon", glow=3, bevel=0, collide=False)


DEVICES = {"trap": trap, "snare": snare, "laser": laser, "door": door, "robot": robot}


# ── Рендер листов устройств (когда скрипт запущен сам) ─────────────────────────────────────────────────────────
def _studio(extent):
    """Студия: светлый пол-подиум и мягкий свет со всех сторон — одинаково для всех устройств."""
    K.group("Studio")
    K.box("Floor", -90, 90, -0.6, 0, -90, 90, "AEBCD0", record=False, look=K.rings("AEBCD0", 2.0, 0.07, 0.6),
          bevel=0)
    K.box("Wall", -90, 90, 0, 80, 40, 41, "8FA3BF", record=False, bevel=0)
    e2 = extent * extent
    K.light("Key", "AREA", (extent * 1.2, extent * 2.0, -extent * 1.8), 34 * e2, "FFF4E6", extent * 1.4,
            (0, extent * 0.3, 0))
    K.light("Fill", "AREA", (-extent * 2.0, extent * 1.1, -extent * 1.2), 12 * e2, "E6F0FF", extent * 1.8,
            (0, extent * 0.3, 0), shadow=False)
    K.light("Rim", "AREA", (-extent * 0.5, extent * 1.8, extent * 2.0), 22 * e2, "FFFFFF", extent * 1.4,
            (0, extent * 0.4, 0), shadow=False)


def _doorway(width=12.0, height=10.0):
    """Кусок фасада музея с проёмом 12 × 10 и золотой рамой — чтобы дверь была видна в стене."""
    K.group("Studio")
    hw = width / 2
    wall = K.rings("F4EFE4", 2.0, 0.06, 0.5)
    for x0, x1 in ((-hw - 9, -hw), (hw, hw + 9)):
        K.box("DoorwayWall", x0, x1, 0, height + 3.0, -0.7, 0.7, "F4EFE4", record=False, look=wall, bevel=0.03)
    K.box("DoorwayTop", -hw, hw, height, height + 3.0, -0.7, 0.7, "F4EFE4", record=False, look=wall, bevel=0.03)
    for x0, x1, y0, y1 in ((-hw - 1.0, -hw, 0, height + 1.0), (hw, hw + 1.0, 0, height + 1.0),
                           (-hw - 1.0, hw + 1.0, height + 1.0, height + 1.6)):
        K.box("DoorwayFrame", x0, x1, y0, y1, -1.2, -0.6, "E9B43C", record=False, bevel=0.04)
    K.box("Threshold", -hw - 1.0, hw + 1.0, 0, 0.12, -1.6, 0.7, "E9B43C", record=False, bevel=0.02)


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    repo = os.path.abspath(argv[0]) if argv else os.getcwd()
    fast = "--fast" in argv
    only = [a for a in argv[1:] if not a.startswith("--")]
    out = os.path.join(repo, "assets", "concepts", "d48", "v2", "devices")
    os.makedirs(out, exist_ok=True)
    pct = 50 if fast else 100
    sheets = [  # имя, функция, состояния, смещение копий по X, камера (глаз, цель), поле зрения
        ("trap", trap, ("idle", "active"), 6.0, ((-0.5, 7.5, -11.0), (-3.0, 0.5, 0)), 30),
        ("snare", snare, ("idle", "active"), 4.8, ((-0.8, 5.6, -8.6), (-2.4, 0.8, 0)), 30),
        ("laser", laser, ("idle", "active"), 0.0, ((0.0, 7.5, -21.5), (0, 2.0, 0)), 36),
        ("door", door, ("idle", "hack", "open"), 0.0, ((-5.0, 6.5, -26.0), (0, 5.4, 0)), 34),
        ("robot", robot, ("idle", "active"), 5.6, ((-0.5, 5.4, -13.0), (-2.8, 3.0, 0)), 32),
    ]
    stats = {}
    for name, fn, states, dx, (eye, at), fov in sheets:
        if only and name not in only:
            continue
        K.reset("WORKBENCH" if fast else "EEVEE", 48)
        K.sky("DCE6F2", "B9C8DC", 0.35)
        K.camera()
        extent = {"door": 9.0, "laser": 5.5}.get(name, 3.5)
        _studio(extent)
        if name == "door":  # каждое состояние — свой кадр в проёме фасада
            for st in states:
                K.reset("WORKBENCH" if fast else "EEVEE", 48)
                K.sky("DCE6F2", "B9C8DC", 0.35)
                K.camera()
                _studio(extent)
                _doorway()
                K.group(f"door_{st}")
                door((0, 0, 0), 0, st, prefix=f"door_{st}")
                stats[f"door_{st}"] = K.counts()
                K.shot(os.path.join(out, f"door_{st}.png"), eye, at, fov, (1100, 900), percent=pct)
                K.export(os.path.join(out, "..", "bricks", f"device_door_{st}.json"))
            continue
        if name == "laser":  # два состояния — рядом, вдоль X
            K.group("laser_idle")
            laser((5.6, 0, 0), 0, "idle", length=8.0, prefix="LaserIdle")
            K.group("laser_active")
            laser((-5.6, 0, 0), 0, "active", length=8.0, prefix="LaserActive")
        else:
            for k, st in enumerate(states):
                K.group(f"{name}_{st}")
                fn((-k * dx, 0, 0), 0, st, prefix=f"{name}_{st}")
        stats[name] = K.counts()
        K.shot(os.path.join(out, f"{name}.png"), eye, at, fov, (1600, 900), percent=pct)
        K.export(os.path.join(out, "..", "bricks", f"device_{name}.json"))
    # метка установки и гнёзда лазера — отдельный маленький кадр
    if not only or "placement" in only:
        K.reset("WORKBENCH" if fast else "EEVEE", 48)
        K.sky("DCE6F2", "B9C8DC", 0.35)
        K.camera()
        _studio(4.5)
        K.group("placement")
        placement((3.2, 0, 0), 4.2, 0, True)
        placement((-3.2, 0, 0), 4.2, 0, False, "PlaceBad")
        trap((3.2, 0, 0), 0, "idle", prefix="PlaceTrap")
        K.group("laser_marks")
        laser_sockets((0, 0, -5.0), 0, 10.8)
        K.shot(os.path.join(out, "placement.png"), (1.5, 11.0, -15.0), (0, 0, -1.5), 34, (1600, 900), percent=pct)
    print("DEVICE_COUNTS", stats, flush=True)


if __name__ == "__main__":
    main()
