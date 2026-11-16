"""Коллекция босса 10 «Королевский зверинец» — 10 примеров (черновые концепты, не финальные модели)."""

import math

import ck as C
import cr
from mathutils import Matrix

EXPOSURE = 0.0


def snail_knight(col):
    a = cr.new("SnailKnight", {"body": "F2C98A", "steel": "A3B1C7", "steelD": "5D6A80", "plume": "E8384F",
                               "lance": "C68B4E", "gold": "F2C230"}, rings=("body", "steel"))
    C.blob(a, "body", (0, -0.1, 0.25), 0.45, 1.1, 0.25, n=2, z0=0.0)
    C.tube(a, ["body"], [(0, -0.8, 0.3), (0, -0.95, 1.05)], 0.28)
    C.blob(a, "steel", (0, 0.25, 1.0), 0.6, 0.75, 0.8, n=5, z0=0.25)
    for k in range(3):
        a.frame("steelD", C.ngon(0, 0.25, 0.62 - k * 0.12, 8), 0.06, 0.95 + k * 0.25, 1.0 + k * 0.25, axis="z")
    C.blob(a, "steel", (0, -0.95, 1.2), 0.32, 0.3, 0.3, n=3)
    a.box("dark", -0.25, 0.25, -1.27, -1.2, 1.2, 1.28, bevel=0)
    for s in (1, -1):
        C.round_eye(a, (s * 0.12, -1.27, 1.12), 0.06, look=(0, 0))
    cr.spike(a, "plume", (0, -0.85, 1.45), 0.18, 0.55, tilt_x=-30)
    C.bar(a, "lance", (0.4, -0.7, 0.55), (0.55, -2.2, 0.9), 0.08)
    cr.spike(a, "steel", (0.55, -2.15, 0.9), 0.12, 0.35, tilt_x=95)
    a.frustum("gold", (0.3, 0.6, -0.95, -0.65), (0.4, 0.5, -0.85, -0.75), 0.45, 0.7, bevel=0.01)
    return cr.done(a, col)


def jester_cat(col):
    a = cr.new("JesterCat", {"fur": "F4F1E6", "furD": "8D9AAE", "hatA": "7A2BD8", "hatB": "FFC300", "bell": "F2C230",
                             "ruff": "FF6FAE"}, rings=("fur",))
    for s in (1, -1):
        C.blob(a, "fur", (s * 0.3, -0.35, 0.18), 0.2, 0.28, 0.18, n=2, z0=0.0)
    C.blob(a, "fur", (0, 0.05, 0.75), 0.55, 0.5, 0.6, n=4, z0=0.05)
    for k in range(8):
        t = math.radians(k * 45)
        C.blob(a, "ruff" if k % 2 else "hatB", (0.45 * math.cos(t), 0.0 + 0.4 * math.sin(t), 1.3), 0.2, 0.2, 0.1, n=2)
    C.blob(a, "fur", (0, -0.05, 1.7), 0.5, 0.45, 0.42, n=4)
    for x, y, z in ((0.3, -0.4, 1.85), (-0.2, -0.42, 1.55)):
        a.box("furD", x - 0.1, x + 0.1, y - 0.04, y + 0.02, z, z + 0.1, bevel=0)
    cr.face(a, (0, -0.48, 1.75), 0.36, 0.16, "happy", mouth="grin")
    for s, key in ((1, "hatA"), (-1, "hatB")):
        C.tube(a, [key], [(s * 0.15, -0.05, 2.05), (s * 0.55, -0.05, 2.45), (s * 0.85, -0.1, 2.25)], [0.22, 0.14], n=6)
        C.blob(a, "bell", (s * 0.9, -0.1, 2.12), 0.12, 0.12, 0.12, n=2)
    C.blob(a, "hatA", (0, -0.05, 2.05), 0.48, 0.44, 0.15, n=2)
    C.tube(a, ["fur"], [(0, 0.5, 0.3), (0.4, 0.75, 0.6), (0.35, 0.7, 1.05)], [0.09, 0.07])
    return cr.done(a, col)


def griffin_chick(col):
    a = cr.new("GriffinChick", {"fluff": "FFD84A", "fluffD": "F2B630", "beak": "FF9F1C", "lion": "D99A4E",
                                "tuft": "8A5A3C", "white": "FFFFFF"}, rings=("fluff",))
    for s in (1, -1):
        a.box("beak", s * 0.25 - 0.15, s * 0.25 + 0.15, -0.5, 0.0, 0.0, 0.1)
        C.bar(a, "beak", (s * 0.25, -0.2, 0.05), (s * 0.25, -0.15, 0.4), 0.08)
    C.blob(a, "fluff", (0, 0.0, 0.95), 0.7, 0.65, 0.65, n=5)
    C.blob(a, "white", (0, -0.15, 1.85), 0.48, 0.45, 0.42, n=4)
    for k in range(3):
        cr.spike(a, "white", (-0.15 + k * 0.15, 0.05, 2.2), 0.12, 0.3, tilt_x=-20, tilt_y=(k - 1) * 20)
    a.frustum("beak", (-0.18, 0.18, -0.65, -0.45), (0, 0, -0.95, -0.95), 1.82, 1.62, bevel=0.004)
    a.box("beak", -0.18, 0.18, -0.65, -0.45, 1.82, 1.95, bevel=0.01)
    cr.face(a, (0, -0.58, 2.02), 0.42, 0.17, "big", mouth=None)
    cr.wings(a, "fluffD", (0, 0.1, 1.1), 0.75, 0.6, spread=10)
    C.tube(a, ["lion"], [(0, 0.6, 0.6), (0, 1.0, 0.75), (0.1, 1.2, 1.15)], [0.08, 0.06])
    C.blob(a, "tuft", (0.1, 1.2, 1.25), 0.15, 0.15, 0.17, n=2)
    return cr.done(a, col)


def frog_prince(col):
    a = cr.new("FrogPrince", {"green": "5ED16A", "belly": "F2F0A8", "cape": "C8283A", "ermine": "F6F4EE",
                              "gold": "F2C230", "ruby": "E0204A"}, rings=("green", "cape"))
    a.extrude("cape", [(-0.7, 1.3), (0.7, 1.3), (0.95, 0.0), (-0.95, 0.0)], 0.45, 0.6, axis="y")
    a.box("ermine", -0.95, 0.95, 0.42, 0.63, 0.0, 0.18)
    C.blob(a, "green", (0, 0.1, 0.7), 0.75, 0.6, 0.65, n=4, z0=0.0)
    C.blob(a, "belly", (0, -0.3, 0.6), 0.48, 0.35, 0.45, n=3)
    a.frame("ermine", C.ngon(0, 0.1, 0.62, 8), 0.2, 1.25, 1.45, axis="z")
    for s in (1, -1):
        C.blob(a, "green", (s * 0.7, -0.2, 0.18), 0.3, 0.45, 0.18, n=2, z0=0.0)
        C.blob(a, "green", (s * 0.32, -0.15, 1.7), 0.26, 0.26, 0.24, n=3)
        C.round_eye(a, (s * 0.32, -0.4, 1.72), 0.14, look=(0, -0.2))
    C.blob(a, "green", (0, 0.0, 1.5), 0.6, 0.5, 0.3, n=3)
    a.box("dark", -0.38, 0.38, -0.52, -0.46, 1.38, 1.44, bevel=0)
    a.frame("gold", C.ngon(0, -0.05, 0.38, 8), 0.08, 1.85, 2.0, axis="z")
    for k in range(5):
        t = math.radians(-160 + k * 35)
        cr.spike(a, "gold", (0.35 * math.cos(t), -0.05 + 0.35 * math.sin(t), 2.0), 0.12, 0.25)
    C.gem(a, "ruby", (0, -0.43, 1.92), 0.14)
    return cr.done(a, col)


def chest_dog(col):
    a = cr.new("ChestDog", {"wood": "9C5B2C", "woodD": "6B3E1F", "gold": "F2C230", "fur": "C68B4E", "ear": "8A5A3C",
                            "coin": "FFD84A"}, rings=("wood", "fur"))
    cr.legs(a, "fur", [(0.5, -0.35), (-0.5, -0.35), (0.5, 0.45), (-0.5, 0.45)], 0.15, 0.35)
    for x, y in ((0.5, -0.35), (-0.5, -0.35)):
        a.box("fur", x - 0.17, x + 0.17, y - 0.28, y + 0.12, 0.0, 0.12)
    a.box("wood", -0.75, 0.75, -0.55, 0.6, 0.35, 1.1)
    for x in (-0.55, 0.55):
        a.box("gold", x - 0.07, x + 0.07, -0.58, 0.63, 0.35, 1.1, bevel=0.005)
    lid = C.tilt((0, 0.6, 1.1), "X", -28)
    a.prism("wood", [(-0.75, 0.0), (0.75, 0.0), (0.75, 0.25), (0.5, 0.45), (-0.5, 0.45), (-0.75, 0.25)], -0.55, 0.6,
            axis="y", matrix=lid @ Matrix.Translation((0, 0, 1.1)))
    a.box("dark", -0.65, 0.65, -0.5, 0.5, 1.08, 1.12, bevel=0)
    for k in range(5):
        C.disc(a, "coin", -0.4 + k * 0.2, -0.1 + 0.1 * (k % 2), 0.13, 1.1 + 0.05 * k, 1.16 + 0.05 * k, bevel=0.005)
    a.box("tongue", -0.2, 0.2, -0.75, -0.45, 1.05, 1.12, bevel=0.02)
    for s in (1, -1):
        cr.plate(a, "ear", [(s * 0.55, 1.2), (s * 0.85, 1.15), (s * 0.9, 0.7), (s * 0.7, 0.65)], -0.62, -0.5)
    cr.face(a, (0, -0.56, 0.85), 0.45, 0.17, "big", mouth=None)
    a.box("gold", -0.12, 0.12, -0.6, -0.55, 0.5, 0.65, bevel=0)
    C.tube(a, ["fur"], [(0, 0.6, 0.6), (0.2, 0.9, 0.9), (0.15, 0.95, 1.3)], [0.07, 0.05])
    return cr.done(a, col)


def candle_ghost(col):
    a = cr.new("CandleGhost", {"wax": "F4E9D2", "waxD": "E3CFA6", "holder": "F2C230", "neonG": "BFF6FF",
                               "neonB": "6FD6FF"}, rings=("wax", "holder"))
    a.prism("holder", C.ngon(0, 0, 0.6, 10), 0.0, 0.12)
    C.bar(a, "holder", (0.6, 0, 0.1), (0.8, 0, 0.35), 0.08)
    a.prism("wax", C.ngon(0, 0, 0.38, 10), 0.12, 1.35)
    for x, h in ((-0.3, 0.45), (0.15, 0.7), (0.32, 0.3)):
        a.box("waxD", x - 0.07, x + 0.07, -0.4, -0.3, 1.35 - h, 1.36, bevel=0.01)
    C.bar(a, "dark", (0, 0, 1.35), (0, 0, 1.5), 0.04)
    C.blob(a, "neonB", (0, 0, 1.75), 0.35, 0.3, 0.3, n=3)
    C.blob(a, "neonG", (0, -0.02, 2.0), 0.25, 0.22, 0.28, n=3)
    cr.spike(a, "neonG", (0.05, 0, 2.2), 0.2, 0.45, tilt_y=-15)
    for s in (1, -1):
        a.box("dark", s * 0.12 - 0.05, s * 0.12 + 0.05, -0.34, -0.3, 1.78, 1.92, bevel=0)
        C.tube(a, ["neonB"], [(s * 0.3, 0, 1.7), (s * 0.6, -0.1, 1.85)], 0.07, n=6)
    a.box("dark", -0.06, 0.06, -0.33, -0.3, 1.62, 1.7, bevel=0)
    return cr.done(a, col, glow=1.2)


def rocker_unicorn(col):
    a = cr.new("RockerUnicorn", {"body": "F4F1FA", "mane": "FF4FD8", "mane2": "3FF0FF", "horn": "FFD23F",
                                 "hoof": "7A2BD8", "guitar": "26262E", "neck": "B5793A", "bolt": "FFE23F"},
               rings=("body",))
    for x, y in ((0.35, -0.5), (-0.35, -0.5), (0.35, 0.55), (-0.35, 0.55)):
        a.prism("body", C.ngon(x, y, 0.15), 0.15, 0.75)
        a.prism("hoof", C.ngon(x, y, 0.17), 0.0, 0.15)
    C.blob(a, "body", (0, 0.05, 1.0), 0.5, 0.85, 0.4, n=3)
    C.tube(a, ["body"], [(0, -0.6, 1.2), (0, -0.8, 1.65)], 0.25)
    C.blob(a, "body", (0, -0.9, 1.8), 0.32, 0.45, 0.3, n=3)
    cr.face(a, (0, -1.32, 1.85), 0.34, 0.14, "cool", mouth="grin", blush=False)
    cr.spike(a, "horn", (0, -1.05, 2.05), 0.13, 0.6, tilt_x=25)
    for k in range(5):
        cr.spike(a, "mane" if k % 2 else "mane2", (0, -0.75 + k * 0.18, 2.05 - k * 0.12), 0.14, 0.45 - k * 0.04,
                 tilt_x=-15)
    for s in (1, -1):
        cr.spike(a, "body", (s * 0.18, -0.75, 2.05), 0.12, 0.22, tilt_y=s * 15)
    for k in range(3):
        cr.spike(a, "mane2" if k % 2 else "mane", (0, 0.85, 1.2 - k * 0.1), 0.16, 0.6, tilt_x=-140 + k * 20)
    cr.turn(a, (0.55, -0.3, 1.0), -40, "X")
    a.prism("guitar", [(0.35, 0.8), (0.75, 0.8), (0.85, 1.05), (0.55, 1.2), (0.25, 1.05)], -0.62, -0.5, axis="y")
    a.box("neck", 0.5, 0.6, -0.62, -0.52, 1.2, 1.9)
    a.extrude("bolt", [(0.5, 1.12), (0.62, 1.12), (0.55, 0.98), (0.65, 0.98), (0.48, 0.82), (0.53, 0.95), (0.45, 0.95)],
              -0.66, -0.62, axis="y")  # молния на деке
    a.transform = None
    return cr.done(a, col)


def shield_turtle(col):
    a = cr.new("ShieldTurtle", {"skin": "6CC36B", "red": "C8283A", "blue": "2F4FB8", "gold": "F2C230",
                                "white": "F6F4EE"}, rings=("skin",))
    for x, y in ((0.6, -0.5), (-0.6, -0.5), (0.6, 0.55), (-0.6, 0.55)):
        C.blob(a, "skin", (x, y, 0.22), 0.22, 0.25, 0.22, n=2, z0=0.0)
    C.blob(a, "skin", (0, 0.05, 0.45), 0.85, 0.85, 0.25, n=2)
    shield = [(-0.95, 1.25), (0.95, 1.25), (0.95, 0.45), (0.0, -0.35), (-0.95, 0.45)]
    m = C.tilt((0, 0, 0.6), "X", -75)
    quads = ((-0.95, 0.0, 0.45, 1.25, "red"), (0.0, 0.95, 0.45, 1.25, "blue"), (-0.95, 0.0, -0.35, 0.45, "blue"),
             (0.0, 0.95, -0.35, 0.45, "red"))
    a.extrude("gold", shield, 0.0, 0.18, axis="y", matrix=m)
    for x0, x1, z0, z1, key in quads:
        pts = [(x, z) for x, z in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]
        clip = [(x, max(z, abs(x) * 0.84 - 0.35)) for x, z in pts]
        a.extrude(key, clip, -0.05, 0.0, axis="y", matrix=m)
    C.gem(a, "gold", (0, -0.9, 0.85), 0.3)
    C.blob(a, "skin", (0, -1.15, 0.55), 0.35, 0.33, 0.3, n=3)
    cr.face(a, (0, -1.46, 0.62), 0.3, 0.13, "round", mouth="smile")
    return cr.done(a, col)


def treasurer(col):
    a = cr.new("TreasurerDragon", {"scale": "45C45F", "belly": "F2F0A8", "wing": "2E9E4E", "bag": "B5793A",
                                   "gold": "F2C230", "glass": "B9F3FF", "book": "C8283A"}, rings=("scale", "bag"))
    for s in (1, -1):
        C.blob(a, "scale", (s * 0.3, -0.1, 0.25), 0.22, 0.3, 0.25, n=2, z0=0.0)
    C.blob(a, "scale", (0, 0.05, 0.95), 0.55, 0.5, 0.65, n=4)
    C.blob(a, "belly", (0, -0.3, 0.9), 0.35, 0.25, 0.45, n=3)
    C.blob(a, "scale", (0, -0.1, 1.8), 0.45, 0.42, 0.38, n=3)
    cr.spike(a, "scale", (0, -0.42, 1.72), 0.32, 0.35, tilt_x=95)
    for s in (1, -1):
        cr.spike(a, "gold", (s * 0.22, 0.05, 2.1), 0.12, 0.3, tilt_x=-30, tilt_y=s * 15)
        a.frame("dark", C.ngon(s * 0.17, 1.9, 0.14, 8), 0.035, -0.56, -0.52, axis="y")
    cr.face(a, (0, -0.5, 1.9), 0.34, 0.13, "round", mouth=None, blush=False)
    cr.wings(a, "wing", (0, 0.35, 1.25), 0.7, 0.6, spread=25)
    C.tube(a, ["scale"], [(0, 0.5, 0.5), (0.5, 0.9, 0.25), (0.9, 0.8, 0.2)], [0.15, 0.1])
    C.blob(a, "bag", (0.75, -0.55, 0.45), 0.4, 0.38, 0.45, n=3, z0=0.0)
    a.frame("gold", C.ngon(0.75, -0.55, 0.2, 8), 0.06, 0.82, 0.92, axis="z")
    cr.spike(a, "bag", (0.75, -0.55, 0.9), 0.3, 0.25)
    for k in range(3):
        cr.coin(a, "gold", (0.95 - k * 0.15, -1.0, 0.03 + k * 0.08), 0.15, 0.06)
    a.box("book", -0.85, -0.35, -0.65, -0.45, 0.8, 1.35, bevel=0.01, matrix=C.tilt((-0.6, -0.55, 1.05), "Z", 20))
    a.box("belly", -0.83, -0.37, -0.68, -0.64, 0.84, 1.31, bevel=0, matrix=C.tilt((-0.6, -0.55, 1.05), "Z", 20))
    return cr.done(a, col)


def crown_serpent(col):
    a = cr.new("CrownSerpent", {"gold": "F2C230", "goldD": "C8901C", "snake": "7A2BD8", "snakeL": "C9A8FF",
                                "ruby": "E0204A", "emerald": "22C77A", "sapphire": "2F6BFF", "neonY": "FFE23F"},
               rings=("gold", "snake"))
    a.frame("gold", C.ngon(0, 0, 0.85, 10), 0.18, 0.0, 0.55, axis="z")
    for k in range(5):
        t = math.radians(-162 + k * 72)
        x, y = 0.78 * math.cos(t), 0.78 * math.sin(t)
        cr.spike(a, "gold", (x, y, 0.55), 0.28, 0.65)
        C.gem(a, ("ruby", "emerald", "sapphire", "emerald", "ruby")[k], (x * 1.08, y * 1.08, 0.28), 0.2, turn=k * 72)
    pts = []
    for k in range(9):
        t = math.radians(k * 50)
        pts.append((1.0 * math.cos(t), 1.0 * math.sin(t), 0.25 + k * 0.12))
    pts.append((0.1, -0.2, 1.65))
    C.tube(a, ["snake", "snakeL"], pts, 0.16, n=8)
    C.blob(a, "snake", (0.05, -0.35, 1.85), 0.3, 0.38, 0.25, n=3)
    a.frame("gold", C.ngon(0.05, -0.35, 0.22, 8), 0.06, 2.08, 2.16, axis="z")
    for k in range(3):
        cr.spike(a, "gold", (-0.12 + k * 0.12, -0.35, 2.12), 0.08, 0.2)
    for s in (1, -1):
        a.box("neonY", 0.05 + s * 0.13 - 0.06, 0.05 + s * 0.13 + 0.06, -0.75, -0.7, 1.86, 1.98, bevel=0)
    a.frustum("tongue", (0.0, 0.1, -0.78, -0.7), (0.05, 0.05, -1.05, -1.05), 1.72, 1.72, bevel=0)
    return cr.done(a, col, glow=1.2)


CREATURES = [
    ("snail_knight", "Улитка-рыцарь", "Common", snail_knight),
    ("jester_cat", "Кот-шут", "Common", jester_cat),
    ("griffin_chick", "Грифон-птенец", "Common", griffin_chick),
    ("frog_prince", "Лягушка-принц", "Rare", frog_prince),
    ("chest_dog", "Сундук-пёс", "Rare", chest_dog),
    ("candle_ghost", "Свеча-призрак", "Rare", candle_ghost),
    ("rocker_unicorn", "Единорог-пони рокер", "Epic", rocker_unicorn),
    ("shield_turtle", "Щит-черепаха", "Epic", shield_turtle),
    ("treasurer", "Мини-дракон-казначей", "Legendary", treasurer),
    ("crown_serpent", "«Корона королей» — змей-корона", "Secret", crown_serpent),
]
