"""D48-C, фаза 2 — финальные Blender-модели пяти устройств защиты (по утверждённому концепту D48 v2) с отдельными
подвижными частями. Формат пачек проекта (lego.py): модель = меши-роли по цветам, FBX «<Модель>_<Роль>»,
assets/models/Pack4_d48_defense.layout.json. Роль «Glow_d48state» — огонёк состояния: цвет ставит игра (State).

Начало каждой подвижной части — её точка вращения (шарнир, плечо, шея, ось турели); где она стоит в устройстве и
какие позы и цвета у каждого состояния — assets/concepts/d48/c2/defense_rigs.json (для кода, фаза 3). Игровые числа
(урон, время, радиусы, цены) не меняются — их держит GameConfig.Defense.

Запуск: blender --background --factory-startup --python scripts/blender/d48_final_devices.py -- <репо> [--no-render]
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import d48_kit as K  # noqa: E402
import lego  # noqa: E402
from lego import Model  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
REPO = os.path.abspath(argv[0]) if argv else os.getcwd()
NO_RENDER = "--no-render" in argv
ONLY = [a for a in argv[1:] if not a.startswith("--")]
C2 = os.path.join(REPO, "assets", "concepts", "d48", "c2")
OUTDIR = os.path.join(C2, "devices")
os.makedirs(OUTDIR, exist_ok=True)
PACK = "Pack4_d48_defense"

lego.PALETTE.update({
    "d48navy": "26345E", "d48navydark": "1A2440", "d48white": "F4F7FB", "d48steel": "A7B6C8", "d48steeldark": "5E7186",
    "d48gold": "E9B43C", "d48golddeep": "C98E1E", "d48hazard": "FFC93C", "d48ink": "2A2A33", "d48lens": "FF3B3B",
    "d48state": "39E1FF", "d48zap": "BDEBFF", "d48spark": "FF9A2E", "d48red": "FF3B3B",
})
STATE = {"idle": "39E1FF", "detect": "FFB020", "active": "FF3B3B", "attack": "FF3B3B", "hit": "F4F7FB",
         "broken": "3A3D46", "hack": "FF7A1A", "open": "4CE07A"}
MODELS = {}


def model(name):
    m = Model(name)
    MODELS[name] = m
    return m


def bx(m, color, x0, x1, y0, y1, z0, z1, bevel=0.06, role="Body", rotation=None):
    if min(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)) < 0.3:
        bevel = 0
    m.box(role, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), color,
          bevel=bevel, rotation=rotation)


def RX(deg):
    return Matrix.Rotation(math.radians(deg), 4, "X")  # = поворот вокруг x Roblox


def RZb(deg):
    return Matrix.Rotation(math.radians(deg), 4, "Y")  # Blender Y = −z Roblox: поворот в плоскости фасада


# ── Ловушка «Пружинная плита» ──────────────────────────────────────────────────────────────────────────────────
def trap():
    b = model("D48T_TrapBase")
    bx(b, "d48navydark", -2.1, 2.1, 0, 0.3, -2.1, 2.1, bevel=0.1)
    for x0, x1, z0, z1 in ((-2.1, 2.1, -2.1, -1.7), (-2.1, 2.1, 1.7, 2.1), (-2.1, -1.7, -1.7, 1.7), (1.7, 2.1, -1.7, 1.7)):
        bx(b, "d48hazard", x0, x1, 0.3, 0.42, z0, z1)
    for sx, sz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        bx(b, "d48ink", sx * 2.15 - 0.45, sx * 2.15 + 0.45, 0.3, 0.46, sz * 2.15 - 0.45, sz * 2.15 + 0.45, bevel=0)
    bx(b, "d48steel", -1.55, 1.55, 0.3, 0.45, -1.55, 1.55, bevel=0.05)
    for sx, sz in ((0, 0), (-0.85, -0.85), (0.85, -0.85), (-0.85, 0.85), (0.85, 0.85)):
        b.cylinder("Body", (sx, 0.455, sz), 0.33, 0.02, "d48navydark", segments=8, bevel=0)
    b.cylinder("Glow", (0, 0.48, -1.9), 0.21, 0.12, "d48state", segments=10, bevel=0)
    s = model("D48T_TrapSpikes")  # поднимаются на 1.35 при срабатывании; в покое — под плитой
    for sx, sz in ((0, 0), (-0.85, -0.85), (0.85, -0.85), (-0.85, 0.85), (0.85, 0.85)):
        s.cylinder("Body", (sx, 0.7, sz), 0.3, 0.5, "d48gold", segments=8, bevel=0.03)
        s.cylinder("Body", (sx, 1.3, sz), 0.24, 0.7, "d48white", segments=8, radius2=0.0, bevel=0)
    f = model("D48T_TrapFlash")
    for x0, x1, z0, z1 in ((-2.35, 2.35, -2.35, -2.2), (-2.35, 2.35, 2.2, 2.35), (-2.35, -2.2, -2.2, 2.2),
                           (2.2, 2.35, -2.2, 2.2)):
        bx(f, "d48red", x0, x1, 0.05, 0.14, z0, z1, role="Glow")


# ── Капкан «Захват» ────────────────────────────────────────────────────────────────────────────────────────────
def snare():
    b = model("D48T_SnareBase")
    b.cylinder("Body", (0, 0.08, 0), 1.7, 0.16, "d48hazard", segments=20, bevel=0)
    b.cylinder("Body", (0, 0.28, 0), 1.5, 0.24, "d48navydark", segments=20, bevel=0.05)
    b.cylinder("Glow", (0, 0.45, 0), 0.55, 0.12, "d48state", segments=14, bevel=0)  # нажимная кнопка
    for sx in (-1, 1):
        b.cylinder("Body", (sx * 1.38, 0.55, 0), 0.25, 0.42, "d48gold", axis="x", segments=10, bevel=0.03)
        b.torus("Body", (sx * 1.38, 0.55, 0), 0.25, 0.05, "d48golddeep", axis="x", segments=10, minor_segments=4)
    j = model("D48T_SnareJaw")  # начало — ось шарнира; сомкнутое положение: дуга вверх; зубцы — к центру дуги
    r = 1.3
    for a0, a1 in ((180, 120), (120, 60), (60, 0)):
        mid = math.radians((a0 + a1) / 2)
        cx, cy = math.cos(mid) * r * 0.93, math.sin(mid) * r * 0.93
        j.box("Body", (cx, cy, -0.13), (r * 1.06, 0.28, 0.26), "d48steeldark", bevel=0.05,
              rotation=RZb(90 - (a0 + a1) / 2))
    for ang in (150, 90, 30):
        a = math.radians(ang)
        tip_dir = (-math.cos(a), -math.sin(a), 0)
        j.cylinder("Body", (math.cos(a) * r * 0.66, math.sin(a) * r * 0.66, -0.13), 0.13, 0.42, "d48white", segments=6,
                   radius2=0.0, rotation=lego.align(tip_dir), bevel=0)
    g = model("D48T_SnareGlow")
    g.cylinder("Glow", (0, 0.02, 0), 2.0, 0.04, "d48red", segments=24, bevel=0)


# ── Лазерная стойка (две на лазер, вторая повёрнута на 180°); луч — Neon-деталь в коде (длина по месту) ──────────
def laser():
    p = model("D48T_LaserPost")  # начало — центр основания; линза смотрит в +x
    y = 2.4
    p.cylinder("Body", (0, 0.15, 0), 0.65, 0.3, "d48navydark", segments=14, bevel=0.05)
    p.cylinder("Body", (0, 0.4, 0), 0.5, 0.2, "d48gold", segments=14, bevel=0)
    bx(p, "d48navy", -0.35, 0.35, 0.5, y + 1.3, -0.35, 0.35, bevel=0.06)
    for by in (1.0, y + 0.95):
        bx(p, "d48gold", -0.42, 0.42, by, by + 0.14, -0.42, 0.42)
    bx(p, "d48white", -0.45, 0.45, y - 0.35, y + 0.35, -0.45, 0.45, bevel=0.08)
    p.cylinder("Glow", (0.5, y, 0), 0.21, 0.16, "d48lens", axis="x", segments=10, bevel=0)
    bx(p, "d48gold", -0.45, 0.45, y + 1.3, y + 1.45, -0.45, 0.45)
    p.sphere("Glow", (0, y + 1.68, 0), 0.23, "d48state", segments=10, rings=6)


# ── Бронедверь 12 × 10: две створки (L, R), замок-штурвал, лампа, взломщик ────────────────────────────────────
def door():
    hw, height = 5.9, 9.9
    for side, tag in ((-1, "L"), (1, "R")):
        m = model(f"D48T_DoorLeaf{tag}")
        x0, x1 = (-hw, -0.05) if side < 0 else (0.05, hw)
        bx(m, "d48navy", x0, x1, 0.05, height, -0.4, 0.4, bevel=0.08)
        bx(m, "d48steel", x0 + 0.5, x1 - 0.5, 2.0, height - 0.8, -0.52, -0.38, bevel=0.05)
        for by in (3.2, height - 2.3):
            bx(m, "d48gold", x0 + 0.3, x1 - 0.3, by, by + 0.5, -0.62, -0.5)
        bx(m, "d48hazard", x0 + 0.1, x1 - 0.1, 0.25, 1.65, -0.5, -0.38)
        for k in range(3):
            cx = x0 + 0.9 + k * (x1 - x0 - 1.8) / 2
            m.box("Body", (cx, 0.95, -0.52), (0.44, 1.3, 0.08), "d48ink", bevel=0, rotation=RZb(35))
        for rx in (x0 + 0.55, x1 - 0.55):
            for ry in (2.2, height - 1.0):
                m.cylinder("Body", (rx, ry, -0.5), 0.16, 0.14, "d48golddeep", axis="z", segments=6, bevel=0)
    lock = model("D48T_DoorLock")  # начало — центр штурвала; вращается при взломе, уезжает со створкой L
    lock.torus("Body", (0, 0, 0.0), 1.55, 0.18, "d48gold", axis="z", segments=24, minor_segments=5)
    lock.cylinder("Body", (0, 0, -0.18), 1.4, 0.25, "d48steel", axis="z", segments=24, bevel=0.06)
    lock.cylinder("Glow", (0, 0, -0.34), 0.75, 0.12, "d48state", axis="z", segments=18, bevel=0)
    lock.cylinder("Body", (0, 0, -0.46), 0.45, 0.2, "d48gold", axis="z", segments=14, bevel=0.04)
    for k in range(2):
        lock.box("Body", (0, 0, -0.43), (2.5, 0.24, 0.14), "d48golddeep", bevel=0, rotation=RZb(45 + 90 * k))
    lamp = model("D48T_DoorLamp")  # над проёмом
    bx(lamp, "d48navydark", -0.9, 0.9, 0, 0.4, -0.6, 0.0, bevel=0.05)
    bx(lamp, "d48state", -0.65, 0.65, 0.4, 0.8, -0.5, -0.1, role="Glow", bevel=0)
    hack = model("D48T_HackDevice")  # взломщик: крепится под штурвалом
    bx(hack, "d48ink", -0.8, 0.8, -0.4, 0.4, -0.3, 0.3, bevel=0.06)
    bx(hack, "d48navydark", -0.6, 0.6, -0.25, 0.25, -0.36, -0.3, bevel=0)
    bx(hack, "d48state", -0.55, 0.15, -0.1, 0.1, -0.39, -0.35, role="Glow", bevel=0)
    hack.cylinder("Body", (0.55, 0.55, 0), 0.06, 0.6, "d48steeldark", segments=6, bevel=0)


# ── Робот-охранник: основание, турель с корпусом, голова, руки (правая с дубинкой), разряд, тревога, искры ──────
def robot():
    b = model("D48T_RobotBase")
    b.cylinder("Body", (0, 0.25, 0), 1.45, 0.5, "d48navydark", segments=20, bevel=0.08)
    b.cylinder("Body", (0, 0.58, 0), 1.55, 0.16, "d48gold", segments=20, bevel=0)
    t = model("D48T_RobotBody")  # начало — ось турели на верху основания (y 0.66 от пола)
    t.cylinder("Body", (0, 0.2, 0), 1.1, 0.4, "d48steel", segments=18, bevel=0.05)
    t.cylinder("Body", (0, 0.69, 0), 0.7, 0.6, "d48steeldark", segments=14, bevel=0.04)
    bx(t, "d48white", -1.2, 1.2, 0.99, 3.19, -0.9, 0.9, bevel=0.22)
    bx(t, "d48navy", -0.85, 0.85, 1.39, 2.79, -1.02, -0.8, bevel=0.06)
    t.cylinder("Body", (0, 2.29, -1.1), 0.35, 0.16, "d48gold", axis="z", segments=14, bevel=0.03)
    bx(t, "d48state", -0.55, 0.55, 1.64, 1.79, -1.1, -0.98, role="Glow", bevel=0)
    for sx in (-1, 1):
        t.sphere("Body", (sx * 1.5, 2.79, 0), 0.5, "d48navy", segments=12, rings=8)
    h = model("D48T_RobotHead")  # начало — шея (y 3.85 от пола)
    bx(h, "d48steeldark", -0.4, 0.4, 0, 0.25, -0.4, 0.4, bevel=0)
    bx(h, "d48white", -0.95, 0.95, 0.25, 1.5, -0.8, 0.8, bevel=0.25)
    bx(h, "d48state", -0.75, 0.75, 0.65, 1.1, -0.9, -0.76, role="Glow", bevel=0)
    for sx in (-1, 1):
        h.cylinder("Body", (sx * 1.05, 0.9, 0), 0.38, 0.3, "d48navy", axis="x", segments=12, bevel=0.04)
    h.cylinder("Body", (0, 1.9, 0), 0.07, 0.8, "d48steeldark", segments=6, bevel=0)
    h.sphere("Glow", (0, 2.4, 0), 0.19, "d48state", segments=10, rings=6)
    for tag, sx in (("L", -1), ("R", 1)):
        a = model(f"D48T_RobotArm{tag}")  # начало — плечо (x ±1.5, y 3.45 от пола); рука висит вниз
        bx(a, "d48white", -0.35, 0.35, -1.15, -0.25, -0.35, 0.35, bevel=0.1)
        bx(a, "d48navy", -0.42, 0.42, -2.25, -1.15, -0.42, 0.42, bevel=0.1)
        bx(a, "d48steeldark", -0.4, 0.4, -2.7, -2.2, -0.42, 0.42, bevel=0.08)
        if sx > 0:  # дубинка вперёд из кулака
            a.cylinder("Body", (0, -2.45, -1.2), 0.17, 1.9, "d48ink", axis="z", segments=8, bevel=0)
            a.cylinder("Glow", (0, -2.45, -2.4), 0.25, 0.55, "d48state", axis="z", segments=8, bevel=0)
    z = model("D48T_RobotZap")  # разряд у конца дубинки (начало — конец дубинки)
    for k, (dx, dy, ang) in enumerate(((-0.35, 0.1, 35), (0.35, 0.25, -30), (0.0, 0.55, 15))):
        z.box("Glow", (dx, dy, 0), (0.12, 0.6, 0.12), "d48zap", bevel=0, rotation=RZb(ang))
    al = model("D48T_RobotAlarm")
    al.cylinder("Glow", (0, 0.03, 0), 2.2, 0.05, "d48red", segments=24, bevel=0)
    sp = model("D48T_RobotSparks")  # поломка: искры у головы и плеча
    for k, (x, y, zz) in enumerate(((0.9, 4.6, -0.6), (-0.7, 4.2, -0.8), (1.4, 3.3, 0.3), (-1.2, 3.0, -0.2))):
        sp.box("Glow", (x, y, zz), (0.14, 0.14, 0.14), "d48spark", bevel=0, rotation=RZb(30 * k))


trap()
snare()
laser()
door()
robot()

# ── Позы и цвета состояний (для кода, фаза 3) ──────────────────────────────────────────────────────────────────
RIGS = {
    "Trap": {"parts": {"D48T_TrapBase": {"at": [0, 0, 0]}, "D48T_TrapSpikes": {"at": [0, -1.35, 0]},
                       "D48T_TrapFlash": {"at": [0, 0, 0]}},
             "states": {"idle": {"glow": STATE["idle"], "D48T_TrapSpikes": {"at": [0, -1.35, 0]},
                                 "hide": ["D48T_TrapFlash"]},
                        "active": {"glow": STATE["active"], "D48T_TrapSpikes": {"at": [0, 0, 0], "tween": 0.12}}}},
    "Snare": {"parts": {"D48T_SnareBase": {"at": [0, 0, 0]},
                        "D48T_SnareJaw#front": {"model": "D48T_SnareJaw", "at": [0, 0.55, 0], "yaw": 0},
                        "D48T_SnareJaw#back": {"model": "D48T_SnareJaw", "at": [0, 0.55, 0], "yaw": 180},
                        "D48T_SnareGlow": {"at": [0, 0, 0]}},
              "states": {"idle": {"glow": STATE["idle"], "D48T_SnareJaw#front": {"rotX": -84},
                                  "D48T_SnareJaw#back": {"rotX": -84}, "hide": ["D48T_SnareGlow"]},
                         "active": {"glow": STATE["active"], "D48T_SnareJaw#front": {"rotX": 0, "tween": 0.08},
                                    "D48T_SnareJaw#back": {"rotX": 0, "tween": 0.08}}}},
    "Laser": {"parts": {"D48T_LaserPost#a": {"model": "D48T_LaserPost", "at": ["-half", 0, 0], "yaw": 0},
                        "D48T_LaserPost#b": {"model": "D48T_LaserPost", "at": ["half", 0, 0], "yaw": 180},
                        "Beam": {"code": "Neon FF3B3B, y 2.4, толщина 0.1 (тревога 0.2 + ореол Glass 0.44)"}},
              "states": {"idle": {"glow": STATE["idle"], "beam": 0.1}, "active": {"glow": STATE["active"], "beam": 0.2}}},
    "Door": {"parts": {"D48T_DoorLeafL": {"at": [0, 0, 0]}, "D48T_DoorLeafR": {"at": [0, 0, 0]},
                       "D48T_DoorLock": {"at": [0, 5.15, -0.5], "follows": "D48T_DoorLeafL"},
                       "D48T_DoorLamp": {"at": [0, 10.05, 0]}, "D48T_HackDevice": {"at": [0, 3.8, -1.0]}},
             "states": {"idle": {"glow": STATE["idle"], "hide": ["D48T_HackDevice"]},
                        "hack": {"glow": STATE["hack"], "D48T_DoorLock": {"spin": 90, "time": 5}},
                        "open": {"glow": STATE["open"], "D48T_DoorLeafL": {"at": [-6.05, 0, 0], "tween": 0.8},
                                 "D48T_DoorLeafR": {"at": [6.05, 0, 0], "tween": 0.8},
                                 "hide": ["D48T_HackDevice", "D48T_DoorLock"]}}},
    "Robot": {"parts": {"D48T_RobotBase": {"at": [0, 0, 0]}, "D48T_RobotBody": {"at": [0, 0.66, 0]},
                        "D48T_RobotHead": {"at": [0, 3.85, 0], "follows": "D48T_RobotBody"},
                        "D48T_RobotArmL": {"at": [-1.5, 3.45, 0], "follows": "D48T_RobotBody"},
                        "D48T_RobotArmR": {"at": [1.5, 3.45, 0], "follows": "D48T_RobotBody"},
                        "D48T_RobotZap": {"at": [1.5, 1.0, -2.75], "follows": "D48T_RobotArmR"},
                        "D48T_RobotAlarm": {"at": [0, 0, 0]}, "D48T_RobotSparks": {"at": [0, 0, 0]}},
              "states": {"idle": {"glow": STATE["idle"], "hide": ["D48T_RobotZap", "D48T_RobotAlarm", "D48T_RobotSparks"]},
                         "detect": {"glow": STATE["detect"], "D48T_RobotBody": {"yaw": 25}, "alarm": STATE["detect"],
                                    "hide": ["D48T_RobotZap", "D48T_RobotSparks"]},
                         "attack": {"glow": STATE["attack"], "D48T_RobotArmR": {"rotX": 75}, "alarm": STATE["attack"],
                                    "hide": ["D48T_RobotSparks"]},
                         "hit": {"glow": STATE["hit"], "D48T_RobotBody": {"rotX": -10},
                                 "hide": ["D48T_RobotZap", "D48T_RobotAlarm", "D48T_RobotSparks"]},
                         "broken": {"glow": STATE["broken"], "D48T_RobotHead": {"rotZ": 18, "rotX": -15},
                                    "D48T_RobotArmL": {"rotX": 12}, "D48T_RobotArmR": {"rotX": 12},
                                    "hide": ["D48T_RobotZap", "D48T_RobotAlarm"]}}},
}

# ── Постройка, UV, выгрузка ────────────────────────────────────────────────────────────────────────────────────
K.reset("EEVEE", 48)
lib = K.coll("Library")
LAYOUT, OBJECTS = {}, {}
x = 0.0
import bmesh  # noqa: E402


def uv_box(obj, studs=4.0):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for loop in f.loops:
            co = loop.vert.co
            u, v = [(co.y, co.z), (co.x, co.z), (co.x, co.y)][ax]
            loop[uv].uv = (u / studs, v / studs)
    bm.to_mesh(obj.data)
    bm.free()


for name, m in MODELS.items():
    roles = m.build(lib, offset=(x, 0, 300))
    for role, info in roles.items():
        if "d48state" in role:
            info["color"] = "State"
    LAYOUT[name] = {"roles": roles, "triangles": sum(r["triangles"] for r in roles.values())}
    OBJECTS[name] = [o for o in lib.objects if o.name.startswith(name + "_")]
    x += 20.0
for objs in OBJECTS.values():
    for o in objs:
        uv_box(o)
all_objs = [o for objs in OBJECTS.values() for o in objs]
lego.export_fbx(os.path.join(REPO, "assets", "models", f"{PACK}.fbx"), all_objs)
lego.write_json(os.path.join(REPO, "assets", "models", f"{PACK}.layout.json"), {"d48_defense": LAYOUT})
totals = {}
for dev, rig in RIGS.items():
    totals[dev] = sum(LAYOUT[p.get("model", n)]["triangles"] for n, p in rig["parts"].items() if "code" not in p)
with open(os.path.join(C2, "defense_rigs.json"), "w", encoding="utf-8") as f:
    json.dump({"pack": PACK, "units": "studs; at — от начала устройства (центр на полу, лицо −Z); rotX/rotZ/yaw — "
                                      "градусы вокруг x / z / y; follows — часть едет вместе с другой", "rigs": RIGS,
               "triangles": totals}, f, ensure_ascii=False, indent=1)
for o in all_objs:
    o.location = (0, 0, 0)
print("DEVICES", totals, {n: v["triangles"] for n, v in LAYOUT.items()}, flush=True)
if NO_RENDER:
    sys.exit(0)

# ── Рендер состояний ───────────────────────────────────────────────────────────────────────────────────────────
SQ = os.path.join(REPO, "assets", "textures", "lego_squares_color.png")
SQN = os.path.join(REPO, "assets", "textures", "lego_squares_normal.png")
cache = {}


def mat_for(code, kind):
    key = (code, kind)
    if key in cache:
        return cache[key]
    m = bpy.data.materials.new(f"PV_{kind}_{code}")
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    lin = K.lin(code)
    if kind == "Neon":
        b.inputs["Base Color"].default_value = (*lin, 1)
        b.inputs["Emission Color"].default_value = (*lin, 1)
        b.inputs["Emission Strength"].default_value = 3.0
    else:
        b.inputs["Roughness"].default_value = 0.5
        uvn = nt.nodes.new("ShaderNodeUVMap")
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(SQ, check_existing=True)
        nt.links.new(uvn.outputs["UV"], tex.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        mix.inputs["Fac"].default_value = 1.0
        mix.inputs["Color2"].default_value = (*lin, 1)
        nt.links.new(tex.outputs["Color"], mix.inputs["Color1"])
        nt.links.new(mix.outputs["Color"], b.inputs["Base Color"])
        ntex = nt.nodes.new("ShaderNodeTexImage")
        ntex.image = bpy.data.images.load(SQN, check_existing=True)
        ntex.image.colorspace_settings.name = "Non-Color"
        nt.links.new(uvn.outputs["UV"], ntex.inputs["Vector"])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = 0.6
        nt.links.new(ntex.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    cache[key] = m
    return m


A3 = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))


def rbx_rot(rot_x=0.0, rot_z=0.0, yaw=0.0):
    """Поворот в осях Roblox (yaw вокруг y, затем x, затем z) → матрица Blender 4 × 4."""
    r = K.rot_y(yaw) @ K.rot_x(rot_x) @ K.rot_z(rot_z)
    return (A3 @ r @ A3.transposed()).to_4x4()


def pose(device, state, origin, coll_name):
    """Ставит устройство в состоянии state. Положения частей — в осях устройства; часть с follows едет вместе с
    родителем: F(часть) = F(родитель) · T(−покой родителя) · T(место части) · R(поворот части)."""
    rig = RIGS[device]
    st = rig["states"][state]
    glow_col = st.get("glow", STATE["idle"])
    col = K.coll(coll_name)

    def at_of(part):
        info = rig["parts"][part]
        at = [(-2.0 if v == "-half" else 2.0 if v == "half" else v) for v in info["at"]]
        return st.get(part, {}).get("at", at)

    def rest_of(part):
        return [(-2.0 if v == "-half" else 2.0 if v == "half" else v) for v in rig["parts"][part]["at"]]

    frames = {}

    def frame(part):
        if part in frames:
            return frames[part]
        info, ov = rig["parts"][part], st.get(part, {})
        own = Matrix.Translation(K.R(*at_of(part))) @ rbx_rot(ov.get("rotX", 0), ov.get("rotZ", 0),
                                                             info.get("yaw", 0) + ov.get("yaw", 0))
        if "follows" in info:
            parent = info["follows"]
            own = frame(parent) @ Matrix.Translation(-K.R(*rest_of(parent))) @ own
        frames[part] = own
        return own

    for part, info in rig["parts"].items():
        if "code" in info or part in st.get("hide", []):
            continue
        name = info.get("model", part)
        world = Matrix.Translation(K.R(*origin)) @ frame(part)
        for src in OBJECTS[name]:
            o = bpy.data.objects.new(src.name + "_p", src.data)
            role = src.name[len(name) + 1:]
            info_role = LAYOUT[name]["roles"][role]
            code = glow_col if info_role["color"] == "State" else info_role["color"]
            if name == "D48T_RobotAlarm" and st.get("alarm"):
                code = st["alarm"]
            o.material_slots  # noqa: B018
            o.data = src.data.copy()
            o.data.materials.clear()
            o.data.materials.append(mat_for(code, info_role["material"]))
            o.matrix_world = world
            col.objects.link(o)
    if device == "Laser":  # луч — деталь в коде
        thick = st.get("beam", 0.1)
        K.group(coll_name)
        K.box("Beam", origin[0] - 1.4, origin[0] + 1.4, 2.4 - thick / 2, 2.4 + thick / 2, origin[2] - thick / 2,
              origin[2] + thick / 2, "FF3B3B", "Neon", glow=6 if state == "active" else 4, record=False, bevel=0)


lib.hide_render = True
K.sky("DCE6F2", "B9C8DC", 0.35)
K.camera()


def studio(extent):
    K.group("Studio")
    K.box("Floor", -90, 90, -0.6, 0, -90, 90, "AEBCD0", record=False, look=K.rings("AEBCD0", 2.0, 0.07, 0.6), bevel=0)
    K.box("Wall", -90, 90, 0, 80, 40, 41, "8FA3BF", record=False, bevel=0)
    e2 = extent * extent
    K.light("Key", "AREA", (extent * 1.2, extent * 2.0, -extent * 1.8), 34 * e2, "FFF4E6", extent * 1.4,
            (0, extent * 0.3, 0))
    K.light("Fill", "AREA", (-extent * 2.0, extent * 1.1, -extent * 1.2), 12 * e2, "E6F0FF", extent * 1.8,
            (0, extent * 0.3, 0), shadow=False)
    K.light("Rim", "AREA", (-extent * 0.5, extent * 1.8, extent * 2.0), 22 * e2, "FFFFFF", extent * 1.4,
            (0, extent * 0.4, 0), shadow=False)


SHEETS = [("trap", "Trap", ("idle", "active"), 6.0, ((-0.5, 7.5, -11.0), (-3.0, 0.5, 0)), 30, 3.5),
          ("snare", "Snare", ("idle", "active"), 4.8, ((-0.8, 5.6, -8.6), (-2.4, 0.8, 0)), 30, 3.5),
          ("laser", "Laser", ("idle", "active"), 5.6, ((-2.8, 6.0, -12.5), (-2.8, 2.0, 0)), 34, 4.5),
          ("robot", "Robot", ("idle", "detect", "attack", "hit", "broken"), 5.4, ((-10.8, 6.8, -21.5), (-10.8, 3.0, 0)),
           36, 5.0),
          ("door", "Door", ("idle", "hack", "open"), 26.0, ((-26.0, 8.0, -62.0), (-26.0, 5.2, 0)), 30, 9.0)]
for key, dev, states, dx, (eye, at), fov, extent in SHEETS:
    if ONLY and key not in ONLY:
        continue
    for name in list(K.S["coll"]):
        if name not in ("Library",):
            c = K.S["coll"].pop(name)
            for o in list(c.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.collections.remove(c)
    studio(extent)
    for k, st in enumerate(states):
        origin = (-k * dx, 0, 0)
        if dev == "Laser":  # стойки поближе: луч 4 стада
            pass
        pose(dev, st, origin, f"{dev}_{st}")
        if dev == "Door":  # проём фасада вокруг двери
            K.group("Studio")
            wall = K.rings("F4EFE4", 2.0, 0.06, 0.5)
            ox = origin[0]
            for x0, x1 in ((ox - 13, ox - 6), (ox + 6, ox + 13)):
                K.box("Wall", x0, x1, 0, 13, -0.7, 0.7, "F4EFE4", record=False, look=wall, bevel=0.03)
            K.box("WallTop", ox - 6, ox + 6, 10, 13, -0.7, 0.7, "F4EFE4", record=False, look=wall, bevel=0.03)
            for x0, x1, y0, y1 in ((ox - 7, ox - 6, 0, 11), (ox + 6, ox + 7, 0, 11), (ox - 7, ox + 7, 11, 11.6)):
                K.box("Frame", x0, x1, y0, y1, -1.2, -0.6, "E9B43C", record=False, bevel=0.04)
    lib.hide_render = True
    K.shot(os.path.join(OUTDIR, f"{key}.png"), eye, at, fov, (2000, 900) if len(states) > 2 else (1600, 900))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C2, "d48_final_devices.blend"))
