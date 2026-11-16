"""Коллекция босса 8 «Огненная кухня» — 10 примеров (черновые концепты, не финальные модели).
Кухонный юмор — только у существ; у самого голема кухонных предметов нет."""

import math

import ck as C
import cr
from mathutils import Matrix

EXPOSURE = 0.1


def lava_slime(col):
    a = cr.new("LavaSlime", {"lava": "FF7A1A", "crust": "3A3342", "neonL": "FFB33A"}, rings=("lava", "crust"))
    C.blob(a, "lava", (0, 0, 0.75), 1.0, 0.95, 0.75, n=5, z0=0.0)
    for x, y, w in ((-0.4, 0.2, 0.55), (0.35, 0.35, 0.5), (0.0, -0.1, 0.4), (0.55, -0.35, 0.3)):
        a.prism("crust", *C.octa((x, y), w, w * 0.9, 1.3 - abs(x) * 0.35, 1.45 - abs(x) * 0.35, cut=w * 0.3))
    for x, y in ((-0.85, -0.5), (0.9, -0.4), (0.2, -0.95)):
        a.frustum("neonL", (x - 0.1, x + 0.1, y - 0.1, y + 0.1), (x, x, y, y), 0.25, 0.0, bevel=0)
    cr.face(a, (0, -0.9, 0.9), 0.5, 0.2, "happy", mouth="open")
    return cr.done(a, col, glow=1.0)


def salamander(col):
    a = cr.new("SalamanderChef", {"skin": "FF6A3D", "belly": "FFD08A", "hat": "FFFFFF", "apron": "F4F4F4",
                                  "spoon": "C68B4E", "spot": "FFD23F"}, rings=("skin",))
    for s in (1, -1):
        C.blob(a, "skin", (s * 0.35, -0.2, 0.2), 0.25, 0.4, 0.2, n=2, z0=0.0)
    C.tube(a, ["skin"], [(0, 0.3, 0.6), (0.3, 1.0, 0.35), (0.9, 1.3, 0.25), (1.3, 1.1, 0.2)], [0.3, 0.22, 0.12])
    C.blob(a, "skin", (0, 0, 1.0), 0.5, 0.42, 0.75, n=5)
    a.prism("apron", *C.octa((0, -0.32), 0.75, 0.15, 0.45, 1.35, cut=0.15))
    C.blob(a, "skin", (0, -0.15, 1.95), 0.55, 0.5, 0.35, n=3)
    for x, y in ((0.3, 0.2), (-0.35, 0.25), (0.1, 0.4)):
        a.box("spot", x - 0.08, x + 0.08, y - 0.08, y + 0.08, 2.24, 2.3, bevel=0)
    cr.face(a, (0, -0.62, 2.0), 0.48, 0.2, "big", mouth="smile")
    a.prism("hat", C.ngon(0, -0.1, 0.38), 2.2, 2.6)
    for k in range(5):
        t = math.radians(k * 72)
        C.blob(a, "hat", (0.22 * math.cos(t), -0.1 + 0.22 * math.sin(t), 2.75), 0.24, 0.24, 0.2, n=2)
    for s in (1, -1):
        C.tube(a, ["skin"], [(s * 0.45, -0.05, 1.35), (s * 0.7, -0.4, 1.1)], 0.11)
    C.bar(a, "spoon", (0.72, -0.45, 0.6), (0.72, -0.45, 1.9), 0.08)
    C.blob(a, "spoon", (0.72, -0.45, 2.0), 0.16, 0.06, 0.22, n=2)
    return cr.done(a, col)


def ember_hamster(col):
    a = cr.new("EmberHamster", {"coal": "3A3640", "coalL": "5A5464", "neonO": "FF7A1A", "neonY": "FFC23D"},
               rings=("coal",))
    C.blob(a, "coal", (0, 0, 0.8), 0.85, 0.75, 0.8, n=5, z0=0.0)
    C.blob(a, "coalL", (0, -0.4, 0.7), 0.5, 0.35, 0.45, n=3)
    for s in (1, -1):
        C.blob(a, "neonO", (s * 0.48, -0.55, 0.85), 0.2, 0.12, 0.17, n=2)
        C.blob(a, "coal", (s * 0.48, 0.0, 1.55), 0.18, 0.12, 0.18, n=2)
        a.box("neonY", s * 0.48 - 0.08, s * 0.48 + 0.08, -0.12, -0.08, 1.48, 1.62, bevel=0)
        C.blob(a, "coalL", (s * 0.3, -0.62, 0.3), 0.14, 0.14, 0.12, n=2)
    for x, y, z in ((0.5, 0.4, 1.3), (-0.4, 0.5, 1.2), (0.0, 0.6, 0.6), (-0.7, 0.1, 0.5)):
        a.box("neonO", x - 0.07, x + 0.07, y - 0.07, y + 0.07, z, z + 0.07, bevel=0)
    cr.face(a, (0, -0.72, 1.12), 0.42, 0.16, "round", mouth="open", blush=False)
    a.frustum("neonY", (-0.12, 0.12, -0.12, 0.12), (0, 0, 0, 0), 1.6, 2.05, bevel=0)
    return cr.done(a, col, glow=1.0)


def pepper_dragon(col):
    a = cr.new("PepperDragon", {"red": "E8263A", "redD": "A8162A", "stem": "45C45F", "wing": "FF8C1A"},
               rings=("red",))
    C.tube(a, ["red"], [(0, 0.2, 1.6), (0, 0.0, 1.0), (0.1, 0.3, 0.45), (0.5, 0.8, 0.25), (0.9, 1.0, 0.35)],
           [0.55, 0.5, 0.35, 0.18])
    C.blob(a, "red", (0, 0.15, 1.75), 0.58, 0.55, 0.5, n=4)
    for k in range(5):
        t = math.radians(k * 72 + 20)
        cr.spike(a, "stem", (0.25 * math.cos(t), 0.15 + 0.25 * math.sin(t), 2.15), 0.18, 0.35,
                 tilt_x=35 * math.sin(t), tilt_y=-35 * math.cos(t))
    C.bar(a, "stem", (0, 0.15, 2.2), (0.1, 0.25, 2.65), 0.12)
    cr.face(a, (0, -0.38, 1.75), 0.45, 0.18, "angry", mouth="grin", blush=False)
    cr.wings(a, "wing", (0, 0.45, 1.4), 0.8, 0.7, spread=30)
    for s in (1, -1):
        C.blob(a, "redD", (s * 0.3, -0.15, 0.2), 0.18, 0.25, 0.15, n=2, z0=0.0)
        C.blob(a, "white", (s * 0.15, -0.5, 2.15), 0.08, 0.06, 0.06, n=2)
    return cr.done(a, col)


def lava_lamp(col):
    a = cr.new("LavaLamp", {"metal": "8A97AA", "metalD": "56637A", "glass": "B9A6FF", "neonP": "FF5FD8",
                            "neonO": "FF8C1A"}, rings=("metal",))
    a.frustum("metal", (-0.6, 0.6, -0.6, 0.6), (-0.4, 0.4, -0.4, 0.4), 0.0, 0.6)
    a.frustum("glass", (-0.42, 0.42, -0.42, 0.42), (-0.62, 0.62, -0.62, 0.62), 0.6, 1.55)
    a.frustum("glass", (-0.62, 0.62, -0.62, 0.62), (-0.3, 0.3, -0.3, 0.3), 1.55, 2.35)
    a.frustum("metalD", (-0.3, 0.3, -0.3, 0.3), (-0.18, 0.18, -0.18, 0.18), 2.35, 2.6)
    for c, r, key in (((0.25, -0.3, 1.0), 0.18, "neonP"), ((-0.28, -0.25, 1.9), 0.16, "neonO"),
                      ((0.3, -0.2, 2.1), 0.1, "neonP"), ((-0.3, -0.3, 0.85), 0.12, "neonO")):
        C.blob(a, key, c, r, r, r, n=2)
    cr.face(a, (0, -0.56, 1.55), 0.45, 0.2, "happy", mouth="smile")
    for k in range(4):
        x = -0.45 + k * 0.3
        C.tube(a, ["neonP"], [(x, -0.45, 0.3), (x * 1.3, -0.75, 0.15), (x * 1.5, -0.8, 0.04)], 0.06, n=6)
    return cr.done(a, col, glow=1.0)


def volcano_cupcake(col):
    a = cr.new("VolcanoCupcake", {"wrap": "FF6FAE", "wrapD": "D9468A", "cake": "6B3E1F", "rock": "4A4352",
                                  "neonL": "FF7A1A", "sprinkle": "3FF0FF"}, rings=("wrap", "cake"))
    a.frustum("wrap", (-0.6, 0.6, -0.6, 0.6), (-0.8, 0.8, -0.8, 0.8), 0.0, 0.9)
    for k in range(6):
        x = -0.6 + k * 0.24
        a.box("wrapD", x - 0.05, x + 0.05, -0.75, -0.7, 0.05, 0.85, bevel=0)
    C.blob(a, "cake", (0, 0, 1.05), 0.85, 0.85, 0.35, n=3, z0=0.85)
    a.frustum("rock", (-0.6, 0.6, -0.6, 0.6), (-0.22, 0.22, -0.22, 0.22), 1.1, 1.95)
    a.prism("neonL", C.ngon(0, 0, 0.2), 1.95, 2.0, bevel=0)
    for k in range(4):
        t = math.radians(k * 90 + 30)
        x, y = 0.22 * math.cos(t), 0.22 * math.sin(t)
        C.bar(a, "neonL", (x, y, 1.95), (x * 2.6, y * 2.6, 1.25), 0.1, 0.06, bevel=0)
    for k in range(6):
        C.blob(a, "neonL", (0.1 * math.sin(k), 0.1 * math.cos(k), 2.15 + 0.18 * k), 0.12 - 0.012 * k, 0.12, 0.1, n=2)
    for x, y, z in ((0.5, -0.35, 1.25), (-0.45, -0.3, 1.3), (0.2, 0.55, 1.2), (-0.5, 0.4, 1.15)):
        a.box("sprinkle", x - 0.08, x + 0.08, y - 0.03, y + 0.03, z, z + 0.04, bevel=0)
    cr.face(a, (0, -0.72, 0.55), 0.5, 0.18, "big", mouth="open")
    return cr.done(a, col, glow=1.0)


def grill_hog(col):
    a = cr.new("GrillHog", {"fur": "B5653A", "cream": "F1DEC8", "grill": "26262E", "skewer": "B9C3D1",
                            "veg1": "E8384F", "veg2": "45C45F", "veg3": "FFD23F", "neonO": "FF7A1A"},
               rings=("fur",))
    C.blob(a, "fur", (0, 0.25, 0.7), 0.8, 0.85, 0.65, n=4, z0=0.0)
    C.blob(a, "cream", (0, -0.5, 0.6), 0.48, 0.3, 0.45, n=3)
    cr.spike(a, "cream", (0, -0.7, 0.6), 0.3, 0.35, tilt_x=95)
    a.box("dark", -0.07, 0.07, -1.08, -1.0, 0.57, 0.66, bevel=0)
    cr.face(a, (0, -0.72, 0.85), 0.36, 0.15, "big", mouth=None)
    for k in range(5):
        y = -0.1 + k * 0.17
        a.box("grill", -0.6, 0.6, y - 0.03, y + 0.03, 1.32 - abs(k - 2) * 0.05, 1.38 - abs(k - 2) * 0.05, bevel=0)
    for i, x in enumerate((-0.45, 0.0, 0.45)):
        C.bar(a, "skewer", (x, 0.6, 0.9), (x * 1.3, 0.5, 2.0), 0.05)
        for j, key in enumerate(("veg1", "veg2", "veg3")):
            c = (x * (1.0 + 0.1 * (j + 1)), 0.57 - 0.03 * j, 1.25 + 0.22 * j)
            a.box(key, c[0] - 0.11, c[0] + 0.11, c[1] - 0.11, c[1] + 0.11, c[2] - 0.08, c[2] + 0.08, bevel=0.01)
    for x in (-0.3, 0.3):
        cr.spike(a, "neonO", (x, 0.2, 1.38), 0.14, 0.3)
    return cr.done(a, col, glow=1.0)


def dragonfly(col):
    a = cr.new("SparkFly", {"body": "2EC4B6", "bodyD": "1D8A80", "neonW": "8BEFFF", "neonY": "FFE23F", "eye": "FF4F8B"},
               rings=("body",))
    z = 1.3
    for k in range(6):
        C.blob(a, "body" if k % 2 == 0 else "bodyD", (0, 0.25 + k * 0.3, z - k * 0.04), 0.22 - k * 0.018,
               0.18, 0.22 - k * 0.018, n=2)
    C.blob(a, "body", (0, -0.3, z), 0.3, 0.32, 0.3, n=3)
    for s in (1, -1):
        C.blob(a, "eye", (s * 0.22, -0.48, z + 0.12), 0.18, 0.18, 0.18, n=2)
        a.box("glint", s * 0.22 - 0.06, s * 0.22, -0.67, -0.64, z + 0.18, z + 0.25, bevel=0)
        for k, (dy, ang) in enumerate(((0.0, 10), (0.35, -12))):
            pts = [(0, 0), (s * 1.7, 0.35), (s * 1.8, -0.1), (s * 0.5, -0.3)]
            a.prism("neonW" if k == 0 else "neonY", pts, z + 0.06, z + 0.1, bevel=0,
                    matrix=C.tilt((0, 0.0, 0), "Z", ang * s) @ Matrix.Translation((0, 0.05 + dy, 0)))
        C.bar(a, "bodyD", (s * 0.12, -0.2, z - 0.2), (s * 0.35, -0.3, 0.3), 0.05)
    C.blob(a, "neonY", (0, 2.1, z - 0.25), 0.1, 0.1, 0.1, n=2)
    return cr.done(a, col, glow=1.0)


def phoenix(col):
    a = cr.new("Phoenix", {"red": "E8263A", "orange": "FF8C1A", "gold": "F2C230", "beak": "FFD23F", "guitar": "2F6BFF",
                           "neck": "B5793A", "neonO": "FF7A1A", "neonY": "FFC23D"}, rings=("red", "orange"))
    for s in (1, -1):
        C.bar(a, "gold", (s * 0.2, 0.0, 0.0), (s * 0.2, 0.0, 0.65), 0.08)
    C.blob(a, "red", (0, 0.05, 1.2), 0.5, 0.45, 0.65, n=4)
    C.blob(a, "orange", (0, -0.25, 1.15), 0.32, 0.25, 0.42, n=3)
    C.blob(a, "red", (0, -0.1, 2.05), 0.38, 0.38, 0.35, n=3)
    cr.spike(a, "beak", (0, -0.45, 1.98), 0.16, 0.3, tilt_x=110)
    cr.face(a, (0, -0.45, 2.12), 0.32, 0.14, "cool", mouth=None, blush=False)
    for k, key in enumerate(("neonO", "neonY", "neonO")):
        cr.spike(a, key, (-0.1 + k * 0.1, -0.05, 2.35), 0.14, 0.55 - abs(k - 1) * 0.15, tilt_x=-25, tilt_y=(k - 1) * 25)
    for k, key in enumerate(("neonO", "neonY", "neonO", "neonY", "neonO")):
        ang = -40 + k * 20
        cr.spike(a, key, (0, 0.45, 0.8), 0.22, 1.2 - abs(k - 2) * 0.15, tilt_x=-130, tilt_y=ang)
    cr.wings(a, "orange", (0, 0.15, 1.55), 1.0, 0.85, spread=-10)
    cr.turn(a, (0, -0.55, 1.15), 35, "Y")
    a.prism("guitar", [(-0.35, -0.6), (0.35, -0.6), (0.5, -0.5), (0, -0.48), (-0.5, -0.5)], 0.8, 1.15, axis="z")
    a.prism("guitar", *C.octa((0, -0.55), 0.55, 0.12, 0.85, 1.25, cut=0.15))
    a.box("neck", -0.05, 0.05, -0.6, -0.5, 1.25, 1.85)
    a.transform = None
    return cr.done(a, col, glow=1.0)


def heart_whale(col):
    a = cr.new("HeartWhale", {"stone": "4A4352", "stoneL": "6E6577", "belly": "8D8496", "neonL": "FF5A1F",
                              "neonC": "FFC23D"}, rings=("stone", "stoneL"))
    C.blob(a, "stone", (0, 0.2, 1.1), 1.15, 1.6, 0.95, n=5, z0=0.15)
    C.blob(a, "belly", (0, -0.2, 0.55), 0.85, 1.2, 0.45, n=3, z0=0.15)
    C.tube(a, ["stone"], [(0, 1.6, 1.0), (0, 2.25, 1.35)], [0.45])
    a.prism("stoneL", [(-1.0, 2.4), (0, 2.15), (1.0, 2.4), (0, 2.75)], 1.3, 1.45)
    for s in (1, -1):
        a.prism("stoneL", [(s * 1.0, -0.4), (s * 1.6, -0.05), (s * 1.0, 0.4)], 0.5, 0.65)
    for pts in (((-0.5, -0.5, 2.02), (-0.1, -0.1, 2.08), (0.3, 0.35, 2.02)), ((-1.18, -0.7, 1.25), (-1.2, -0.1, 1.5),
                (-1.18, 0.6, 1.15)), ((-1.0, -0.9, 0.75), (-0.6, -1.25, 0.95))):
        for p0, p1 in zip(pts, pts[1:]):
            C.bar(a, "neonL", p0, p1, 0.1, bevel=0)
    a.frustum("stoneL", (-0.35, 0.35, -0.35, 0.35), (-0.18, 0.18, -0.18, 0.18), 1.85, 2.25)
    for k in range(4):
        C.blob(a, "neonL" if k % 2 else "neonC", (0.06 * k, -0.05 * k, 2.4 + 0.25 * k), 0.16 - 0.02 * k, 0.16, 0.14,
               n=2)
    a.prism("neonC", C.ngon(1.15, -0.1, 0.36, 6, phase=0), -1.3, -1.12, axis="x", bevel=0)  # окно с магмой сбоку
    a.frame("stoneL", C.ngon(1.15, -0.1, 0.48, 6, phase=0), 0.12, -1.34, -1.1, axis="x")
    cr.face(a, (0, -1.4, 1.5), 0.75, 0.22, "sleepy", lid_key="stone", mouth="smile", blush=False)
    return cr.done(a, col, glow=1.2)


CREATURES = [
    ("lava_slime", "Лавовый слизень", "Common", lava_slime),
    ("salamander", "Саламандра-повар", "Common", salamander),
    ("ember_hamster", "Уголёк-хомяк", "Common", ember_hamster),
    ("pepper_dragon", "Перчик-дракон", "Rare", pepper_dragon),
    ("lava_lamp", "Лава-лампа-медуза", "Rare", lava_lamp),
    ("volcano_cupcake", "Вулкан-кекс", "Rare", volcano_cupcake),
    ("grill_hog", "Огненный ёж-гриль", "Epic", grill_hog),
    ("dragonfly", "Стрекоза-искра", "Epic", dragonfly),
    ("phoenix", "Феникс-гитарист", "Legendary", phoenix),
    ("heart_whale", "«Сердце вулкана» — каменный кит", "Secret", heart_whale),
]
