"""Коллекция босса 6 «Джунгли-патруль» — 10 примеров (черновые концепты, не финальные модели)."""

import math

import ck as C
import cr
from mathutils import Matrix

EXPOSURE = 0.1


def chameleon(col):
    a = cr.new("Chameleon", {"green": "5BD15B", "greenD": "2E9E4E", "belly": "D6F28A", "camera": "2A2D3A",
                             "lens": "6FD6FF", "strap": "FF6FAE", "branch": "8F5A31", "leaf": "45C45F"},
               rings=("green", "branch"))
    C.bar(a, "branch", (-1.5, 0.1, 0.35), (1.5, 0.1, 0.3), 0.28)
    for x in (-1.2, 1.3):
        cr.plate(a, "leaf", [(x, 0.4), (x + 0.35, 0.75), (x + 0.1, 0.95), (x - 0.15, 0.6)], 0.05, 0.12)
    C.blob(a, "green", (0.1, 0.1, 0.95), 0.85, 0.45, 0.5, n=4)
    C.blob(a, "belly", (0.1, -0.2, 0.8), 0.6, 0.25, 0.3, n=3)
    for x in (-0.3, 0.2, 0.7):
        a.box("greenD", x - 0.1, x + 0.1, -0.1, 0.3, 1.38, 1.46, bevel=0)
    C.blob(a, "green", (-0.75, -0.15, 1.25), 0.45, 0.42, 0.42, n=4)
    cr.plate(a, "greenD", [(-1.1, 1.45), (-0.55, 1.95), (-0.35, 1.5)], -0.12, 0.08)
    for s in (1, -1):
        x = -0.75 + s * 0.28
        a.prism("greenD", C.ngon(x, 1.35, 0.2), -0.62, -0.42, axis="y")
        C.round_eye(a, (x, -0.63, 1.35), 0.13, look=(s * 0.4, 0))
        C.tube(a, ["green"], [(0.1 + s * 0.55, -0.1, 0.8), (0.1 + s * 0.6, -0.15, 0.38)], 0.1)
    C.tube(a, ["green"], [(0.9, 0.1, 0.95), (1.3, 0.1, 0.7), (1.4, 0.1, 0.35), (1.15, 0.1, 0.22), (1.05, 0.1, 0.45)],
           [0.18, 0.14, 0.1, 0.08])
    a.box("camera", -0.65, -0.05, -0.95, -0.55, 0.75, 1.12)
    C.disc(a, "camera", -0.35, 0.93, 0.17, -1.12, -0.95, axis="y")
    C.disc(a, "lens", -0.35, 0.93, 0.11, -1.16, -1.1, axis="y", bevel=0)
    a.box("white", -0.6, -0.48, -0.98, -0.94, 1.0, 1.08, bevel=0)
    C.bar(a, "strap", (-0.6, -0.75, 1.1), (-0.9, -0.2, 1.4), 0.06)
    return cr.done(a, col)


def parrot(col):
    a = cr.new("Parrot", {"red": "E8384F", "yellow": "FFD23F", "blue": "2F6BFF", "beak": "F4F1E6", "beakD": "3A3F55",
                          "hat": "1D1D24", "perch": "8F5A31"}, rings=("red", "perch"))
    C.disc(a, "perch", 0, 0.25, 0.45, 0.0, 0.12)
    C.bar(a, "perch", (0, 0.25, 0.1), (0, 0.25, 0.95), 0.14)
    C.bar(a, "perch", (-0.65, 0.1, 0.98), (0.65, 0.1, 0.98), 0.14)
    C.blob(a, "red", (0, 0.1, 1.65), 0.5, 0.45, 0.7, n=5)
    C.bar(a, "blue", (0, 0.45, 1.25), (0, 0.9, 0.35), 0.38, 0.08)
    C.bar(a, "yellow", (0, 0.5, 1.2), (0, 0.85, 0.5), 0.2, 0.1)
    for s in (1, -1):
        C.blob(a, "blue", (s * 0.45, 0.15, 1.6), 0.14, 0.4, 0.5, n=3)
        a.box("yellow", s * 0.2 - 0.1, s * 0.2 + 0.1, -0.05, 0.25, 0.98, 1.12)
    C.blob(a, "red", (0, -0.05, 2.4), 0.42, 0.42, 0.4, n=4)
    C.blob(a, "beak", (0, -0.48, 2.28), 0.17, 0.2, 0.22, n=3)
    cr.spike(a, "beakD", (0, -0.55, 2.12), 0.16, 0.25, tilt_x=165)
    C.round_eye(a, (0.2, -0.38, 2.45), 0.11, look=(0.3, 0))
    a.box("hat", -0.33, -0.08, -0.45, -0.36, 2.33, 2.58, bevel=0.01)
    C.bar(a, "hat", (-0.42, -0.35, 2.68), (0.42, -0.35, 2.4), 0.05)
    a.prism("hat", [(-0.7, 0.3), (0.7, 0.3), (0, -0.62)], 2.7, 2.82)
    C.blob(a, "hat", (0, -0.05, 2.9), 0.36, 0.36, 0.2, n=2)
    a.box("white", -0.1, 0.1, -0.42, -0.36, 2.86, 3.02, bevel=0)
    return cr.done(a, col)


def sloth(col):
    a = cr.new("Sloth", {"fur": "9C7A5B", "mask": "E8D6B8", "hammock": "FF9F1C", "stripe": "2EC4B6", "wood": "8F5A31",
                         "leaf": "45C45F", "claw": "3A2A1A"}, rings=("fur", "hammock", "wood"))
    for s in (1, -1):
        C.bar(a, "wood", (s * 1.45, 0, 0.0), (s * 1.45, 0, 1.75), 0.2)
        for k in range(3):
            cr.spike(a, "leaf", (s * 1.45, 0, 1.75), 0.2, 0.55, tilt_y=-50 + k * 50)
        C.bar(a, "wood", (s * 1.45, 0, 1.55), (s * 1.15, 0, 1.0), 0.05)
    for i in range(8):
        x0, x1 = -1.15 + i * 0.29, -1.15 + (i + 1) * 0.29
        z0 = 1.0 - 0.45 * math.sin(math.pi * i / 8)
        z1 = 1.0 - 0.45 * math.sin(math.pi * (i + 1) / 8)
        C.bar(a, "hammock" if i % 2 else "stripe", (x0, 0, z0), (x1, 0, z1), 0.9, 0.08)
    C.blob(a, "fur", (0.1, 0.0, 0.9), 0.75, 0.42, 0.35, n=3)
    C.blob(a, "fur", (-0.65, -0.15, 1.15), 0.4, 0.38, 0.36, n=3)
    C.blob(a, "mask", (-0.65, -0.42, 1.15), 0.3, 0.14, 0.24, n=2)
    for s in (1, -1):
        a.box("claw", -0.65 + s * 0.13 - 0.1, -0.65 + s * 0.13 + 0.1, -0.58, -0.52, 1.12, 1.24, bevel=0)
    cr.face(a, (-0.65, -0.58, 1.2), 0.26, 0.1, "happy", mouth="smile", blush=False)
    C.tube(a, ["fur"], [(0.25, -0.3, 0.95), (0.35, -0.55, 0.65), (0.4, -0.6, 0.3)], [0.11, 0.1])
    for k in (-0.06, 0.06):
        a.frustum("claw", (0.4 + k - 0.03, 0.4 + k + 0.03, -0.63, -0.57), (0.4 + k, 0.4 + k, -0.66, -0.66), 0.25, 0.08,
                  bevel=0)
    return cr.done(a, col)


def frog(col):
    a = cr.new("DrumFrog", {"green": "5ED16A", "belly": "F2F0A8", "wood": "B26E36", "hide": "EFD9AE", "band": "E8384F"},
               rings=("green", "wood"))
    C.blob(a, "green", (0, 0.15, 0.8), 0.9, 0.8, 0.78, n=5, z0=0.0)
    C.blob(a, "belly", (0, -0.3, 0.7), 0.6, 0.5, 0.55, n=4)
    for s in (1, -1):
        C.blob(a, "green", (s * 0.85, 0.25, 0.3), 0.35, 0.6, 0.3, n=3, z0=0.0)
        C.blob(a, "green", (s * 0.38, -0.15, 1.55), 0.3, 0.3, 0.28, n=3)
        C.round_eye(a, (s * 0.38, -0.44, 1.58), 0.17, look=(0, -0.2))
        C.tube(a, ["green"], [(s * 0.7, -0.3, 1.0), (s * 0.4, -0.85, 0.85)], 0.12)
    a.frame("band", C.ngon(0, 0.0, 0.62, 8), 0.12, 1.75, 1.88, axis="z")
    a.box("band", 0.5, 0.75, 0.45, 0.6, 1.5, 1.8)
    a.box("dark", -0.42, 0.42, -0.72, -0.62, 1.12, 1.2, bevel=0)
    for s, r, h in ((1, 0.32, 0.72), (-1, 0.26, 0.62)):
        x = s * 0.36
        a.prism("wood", C.ngon(x, -1.05, r), 0.0, h)
        a.frame("dark", C.ngon(x, -1.05, r + 0.02), 0.05, h * 0.5, h * 0.5 + 0.06, axis="z")
        a.prism("hide", C.ngon(x, -1.05, r - 0.03), h, h + 0.05)
    return cr.done(a, col)


def piranha_shoe(col):
    a = cr.new("PiranhaShoe", {"sole": "F4F4F4", "fish": "8FA3B8", "belly": "E8384F", "lace": "FFFFFF", "fin": "5D7590"},
               rings=("fish",))
    a.prism("sole", *C.octa((0, 0.1), 1.45, 2.9, 0.0, 0.3, cut=0.55))
    a.prism("belly", *C.octa((0, 0.1), 1.5, 2.95, 0.3, 0.42, cut=0.55))
    C.blob(a, "fish", (0, 0.35, 0.85), 0.68, 1.05, 0.5, n=4, z0=0.4)
    C.blob(a, "fish", (0, -0.55, 0.7), 0.62, 0.5, 0.32, n=3, z0=0.4)
    a.box("dark", -0.45, 0.45, -1.08, -0.95, 0.48, 0.78, bevel=0.01)
    for k in range(5):
        x = -0.36 + k * 0.18
        a.frustum("white", (x - 0.06, x + 0.06, -1.1, -1.0), (x, x, -1.05, -1.05), 0.78, 0.6, bevel=0)
        a.frustum("white", (x - 0.05, x + 0.05, -1.1, -1.0), (x + 0.09, x + 0.09, -1.05, -1.05), 0.48, 0.63, bevel=0)
    for s in (1, -1):
        C.round_eye(a, (s * 0.28, -0.78, 1.0), 0.15, look=(0, -0.3))
        C.bar(a, "dark", (s * 0.12, -0.86, 1.2), (s * 0.45, -0.86, 1.1), 0.06, 0.05, bevel=0)
    for k in range(3):
        y = -0.1 + k * 0.3
        C.bar(a, "lace", (-0.35, y, 1.33), (0.35, y + 0.08, 1.33), 0.08, 0.05)
    a.extrude("fin", [(1.25, 0.0), (1.85, 0.45), (1.25, 0.9)], -0.06, 0.06, axis="x")  # (z, y): спинной плавник
    a.extrude("fin", [(0.55, 1.2), (1.35, 1.75), (0.35, 1.8)], -0.05, 0.05, axis="x")  # хвост у пятки
    return cr.done(a, col)


def toucan(col):
    a = cr.new("Toucan", {"black": "26262E", "chest": "FFE9A8", "face": "FFD23F", "beak": "FF8C1A", "beakG": "45C45F",
                          "beakR": "E8384F", "phones": "2EC4F1", "box": "3A3F55", "neonC": "3FF0FF"},
               rings=("black", "box"))
    a.box("box", -0.85, 0.85, -0.45, 0.45, 0.0, 0.85)
    for s in (1, -1):
        C.disc(a, "black", s * 0.45, 0.42, 0.3, -0.52, -0.45, axis="y")
        C.disc(a, "neonC", s * 0.45, 0.42, 0.14, -0.55, -0.5, axis="y", bevel=0)
        a.box("beak", s * 0.25 - 0.1, s * 0.25 + 0.1, -0.15, 0.15, 0.85, 0.95)
    C.blob(a, "black", (0, 0.1, 1.55), 0.5, 0.45, 0.7, n=5, z0=0.85)
    C.blob(a, "chest", (0, -0.25, 1.55), 0.35, 0.25, 0.45, n=3)
    C.blob(a, "black", (0, 0.0, 2.3), 0.42, 0.42, 0.4, n=4)
    C.blob(a, "face", (0, -0.3, 2.3), 0.32, 0.15, 0.26, n=2)
    C.round_eye(a, (0, -0.44, 2.38), 0.12, look=(0, 0))
    for k, (key, w0, w1, ln) in enumerate((("beakG", 0.42, 0.38, 0.35), ("beak", 0.38, 0.26, 0.6), ("beakR", 0.26, 0.0, 0.4))):
        y0 = -0.38 - (0.0, 0.34, 0.92)[k]
        a.frustum(key, (-w0 / 2, w0 / 2, -w0 * 0.55, w0 * 0.55), (-w1 / 2, w1 / 2, -w1 * 0.55, w1 * 0.55), 0.0, ln,
                  bevel=0.004, matrix=Matrix.Translation((0, y0, 2.2 - 0.06 * k)) @ Matrix.Rotation(math.radians(100), 4, "X"))
    for s in (1, -1):
        a.box("phones", s * 0.4, s * 0.52, -0.2, 0.15, 2.15, 2.5, bevel=0.02)
        C.blob(a, "black", (s * 0.45, 0.15, 1.5), 0.12, 0.35, 0.45, n=2)
    C.bar(a, "phones", (-0.45, 0.0, 2.5), (0.0, 0.0, 2.78), 0.08)
    C.bar(a, "phones", (0.0, 0.0, 2.78), (0.45, 0.0, 2.5), 0.08)
    return cr.done(a, col)


def beetle(col):
    a = cr.new("RhinoBeetle", {"shell": "2B6E4F", "shellL": "46A374", "blade": "FFC300", "track": "26262E",
                               "horn": "3A2A1A", "hat": "FFC300"}, rings=("shell", "blade"))
    for s in (1, -1):
        a.box("track", s * 0.75, s * 1.05, -0.9, 1.1, 0.0, 0.45)
        for y in (-0.6, 0.1, 0.8):
            C.disc(a, "blade", 0.22, y, 0.16, min(s * 1.04, s * 1.12), max(s * 1.04, s * 1.12), axis="x")
        C.bar(a, "blade", (s * 0.6, -0.5, 0.45), (s * 0.7, -1.35, 0.35), 0.12)
    C.blob(a, "shell", (0, 0.3, 0.9), 0.85, 1.0, 0.55, n=4, z0=0.4)
    a.box("shellL", -0.04, 0.04, -0.4, 1.25, 1.2, 1.46, bevel=0)
    C.blob(a, "shell", (0, -0.75, 0.75), 0.45, 0.35, 0.35, n=3)
    cr.spike(a, "horn", (0, -0.98, 0.85), 0.3, 1.0, tilt_x=58)
    cr.spike(a, "horn", (0, -0.6, 1.05), 0.2, 0.45, tilt_x=20)
    C.blob(a, "hat", (0, -0.62, 1.08), 0.38, 0.32, 0.2, n=2, z0=1.0)
    cr.face(a, (0, -1.08, 0.72), 0.36, 0.15, "angry", mouth=None, blush=False)
    a.prism("blade", [(-1.2, 0.0), (1.2, 0.0), (1.2, 0.75), (-1.2, 0.75)], -1.6, -1.42, axis="y")
    a.box("track", -1.2, 1.2, -1.62, -1.4, 0.0, 0.1, bevel=0)
    return cr.done(a, col)


def jump_snake(col):
    a = cr.new("RopeSnake", {"snake": "7ED957", "stripe": "FFD23F", "handle": "E8384F", "handleB": "2F6BFF",
                             "iris": "3A2A1A"}, rings=("snake",))
    pts = [(-1.15, 0, 0.75), (-1.1, 0, 1.45), (-0.65, 0, 2.05), (0, 0, 2.25), (0.65, 0, 2.05), (1.1, 0, 1.45),
           (1.2, 0, 0.6)]
    C.tube(a, ["snake", "stripe"], pts, 0.17, n=8)
    a.prism("handle", C.ngon(-1.15, 0.0, 0.14), 0.0, 0.55)
    a.prism("handleB", C.ngon(1.2, 0.0, 0.14), 0.0, 0.55)
    C.blob(a, "snake", (-1.15, -0.15, 0.68), 0.32, 0.38, 0.25, n=3)
    cr.face(a, (-1.15, -0.5, 0.75), 0.28, 0.14, "big", iris="iris", mouth=None, blush=False)
    a.frustum("tongue", (-1.19, -1.11, -0.62, -0.52), (-1.15, -1.15, -0.85, -0.85), 0.55, 0.55, bevel=0)
    C.tube(a, ["snake"], [(1.2, 0, 0.6), (1.4, -0.2, 0.4), (1.25, -0.25, 0.2), (1.05, -0.05, 0.3)], [0.13, 0.1, 0.07])
    return cr.done(a, col)


def jaguar(col):
    a = cr.new("Jaguar", {"fur": "F5B638", "spot": "6B3E1F", "cream": "FFF1DC", "deck": "7A2BD8", "wheel": "3FF0FF",
                          "cap": "E8384F"}, rings=("fur", "deck"))
    a.prism("deck", *C.octa((0, 0), 1.0, 2.8, 0.25, 0.38, cut=0.45))
    for y in (-0.95, 0.95):
        for s in (1, -1):
            C.disc(a, "wheel", s * 0.38, 0.13, 0.13, y - 0.1, y + 0.1, axis="y")
    C.blob(a, "fur", (0, 0.25, 1.05), 0.55, 0.85, 0.5, n=4, matrix=C.tilt((0, 0.25, 1.05), "X", -12))
    C.blob(a, "cream", (0, -0.15, 0.9), 0.35, 0.45, 0.3, n=3)
    for x, y, z in ((0.45, 0.4, 1.25), (-0.45, 0.2, 1.3), (0.3, 0.8, 1.45), (-0.25, 0.65, 1.5), (0.0, 0.3, 1.55)):
        a.box("spot", x - 0.08, x + 0.08, y - 0.08, y + 0.08, z, z + 0.06, bevel=0)
    for s in (1, -1):
        C.tube(a, ["fur"], [(s * 0.32, -0.5, 0.95), (s * 0.35, -0.8, 0.4)], 0.13)
        C.tube(a, ["fur"], [(s * 0.32, 0.85, 0.95), (s * 0.35, 0.95, 0.4)], 0.15)
        cr.spike(a, "fur", (s * 0.32, -0.55, 2.0), 0.22, 0.3, tilt_y=s * 10)
    C.blob(a, "fur", (0, -0.6, 1.75), 0.45, 0.42, 0.4, n=4)
    C.blob(a, "cream", (0, -0.95, 1.62), 0.25, 0.12, 0.17, n=2)
    a.box("dark", -0.07, 0.07, -1.1, -1.05, 1.68, 1.76, bevel=0)
    cr.face(a, (0, -0.98, 1.85), 0.36, 0.15, "cool", mouth=None, blush=False)
    C.blob(a, "cap", (0, -0.55, 2.08), 0.42, 0.4, 0.18, n=2, z0=2.0)
    a.box("cap", -0.3, 0.3, -0.25, 0.25, 2.0, 2.08)
    C.tube(a, ["fur", "spot"], [(0, 1.05, 1.15), (0, 1.5, 1.6), (0.2, 1.4, 2.1)], [0.12, 0.1])
    return cr.done(a, col)


def flytrap(col):
    a = cr.new("Flytrap", {"pot": "D9734A", "potD": "A8502E", "stem": "3FAF55", "jaw": "6BD34E", "inner": "FF6FAE",
                           "guitar": "E8384F", "neck": "B5793A", "neonY": "FFE23F"}, rings=("pot", "jaw"))
    a.frustum("pot", (-0.55, 0.55, -0.55, 0.55), (-0.75, 0.75, -0.75, 0.75), 0.0, 0.85)
    a.prism("potD", *C.octa((0, 0), 1.6, 1.6, 0.85, 1.05, cut=0.4))
    a.extrude("neonY", [(-0.2, 0.65), (0.1, 0.65), (-0.05, 0.42), (0.2, 0.42), (-0.15, 0.1), (0.0, 0.35), (-0.25, 0.35)],
              -0.72, -0.66, axis="y")
    C.tube(a, ["stem"], [(0, 0, 1.0), (0.05, 0, 1.6), (0, 0, 2.0)], 0.13)
    cr.turn(a, (0, 0, 2.2), -25, "X")
    C.blob(a, "jaw", (0, -0.15, 2.45), 0.7, 0.55, 0.35, n=3, z0=2.2)
    a.box("inner", -0.55, 0.55, -0.62, 0.25, 2.18, 2.26, bevel=0)
    a.transform = C.tilt((0, 0, 2.2), "X", 20)
    C.blob(a, "jaw", (0, -0.15, 2.05), 0.65, 0.5, 0.3, n=3, z1=2.2)
    a.transform = None
    for k in range(6):
        x = -0.5 + k * 0.2
        cr.spike(a, "white", (x, -0.75, 2.3), 0.08, 0.25, tilt_x=200)
    C.round_eye(a, (-0.25, -0.62, 2.82), 0.14, look=(0.2, -0.2))
    C.round_eye(a, (0.25, -0.62, 2.82), 0.14, look=(-0.2, -0.2))
    for s in (1, -1):
        cr.plate(a, "stem", [(s * 0.1, 1.5), (s * 0.75, 1.25), (s * 0.85, 1.5), (s * 0.3, 1.7)], -0.08, 0.04)
    cr.turn(a, (0, -0.45, 1.45), 25, "Y")
    a.prism("guitar", *C.octa((0, -0.5), 0.8, 0.22, 1.05, 1.6, cut=0.25))
    a.box("dark", -0.12, 0.12, -0.63, -0.6, 1.2, 1.4, bevel=0)
    a.box("neck", -0.06, 0.06, -0.58, -0.45, 1.6, 2.15)
    a.box("guitar", -0.12, 0.12, -0.58, -0.45, 2.15, 2.35)
    a.transform = None
    return cr.done(a, col)


CREATURES = [
    ("chameleon", "Хамелеон-фотограф", "Common", chameleon),
    ("parrot", "Попугай-пират", "Common", parrot),
    ("sloth", "Ленивец в гамаке", "Common", sloth),
    ("frog", "Лягушка-барабанщица", "Common", frog),
    ("piranha_shoe", "Пиранья-кроссовок", "Rare", piranha_shoe),
    ("toucan", "Тукан-диджей", "Rare", toucan),
    ("beetle", "Жук-носорог-бульдозер", "Epic", beetle),
    ("jump_snake", "Змея-скакалка", "Epic", jump_snake),
    ("jaguar", "Ягуар-скейтер", "Legendary", jaguar),
    ("flytrap", "Цветок-хищник рок-звезда", "Legendary", flytrap),
]
