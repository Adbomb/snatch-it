"""Коллекция босса 9 «Звёздный зоопарк» — 10 примеров (черновые концепты, не финальные модели)."""

import math

import ck as C
import cr

EXPOSURE = 0.0


def space_cat(col):
    a = cr.new("SpaceCat", {"suit": "EEF2F8", "suitD": "9AA8B8", "fur": "FF9F5A", "furL": "FFE3C8", "rim": "6FD6FF",
                            "neonC": "3FF0FF", "pack": "2F6BFF"}, rings=("suit", "fur"))
    for s in (1, -1):
        a.box("suitD", s * 0.3 - 0.22, s * 0.3 + 0.22, -0.35, 0.2, 0.0, 0.35)
        C.tube(a, ["suit"], [(s * 0.45, -0.05, 1.15), (s * 0.75, -0.35, 0.8)], 0.15)
    C.blob(a, "suit", (0, 0, 0.85), 0.55, 0.48, 0.65, n=4, z0=0.2)
    a.box("pack", -0.4, 0.4, 0.35, 0.65, 0.6, 1.35)
    a.box("neonC", -0.15, 0.15, -0.5, -0.44, 0.9, 1.05, bevel=0)
    C.blob(a, "fur", (0, -0.05, 1.75), 0.5, 0.45, 0.42, n=4)
    C.blob(a, "furL", (0, -0.42, 1.65), 0.28, 0.1, 0.18, n=2)
    for s in (1, -1):
        cr.spike(a, "fur", (s * 0.28, -0.05, 2.05), 0.22, 0.32, tilt_y=s * 12)
    cr.face(a, (0, -0.48, 1.82), 0.36, 0.16, "big", mouth="smile")
    a.frame("rim", C.ngon(0, 1.8, 0.7, 12), 0.1, -0.55, -0.45, axis="y")
    a.frame("rim", C.ngon(0, 0.0, 0.7, 12), 0.1, 1.3, 1.42, axis="z")
    C.bar(a, "suitD", (0.35, 0.0, 2.45), (0.45, 0.0, 2.9), 0.05)
    C.blob(a, "neonC", (0.45, 0.0, 2.95), 0.08, 0.08, 0.08, n=2)
    C.tube(a, ["fur"], [(0, 0.45, 0.45), (0.25, 0.85, 0.7), (0.35, 0.9, 1.1)], [0.1, 0.08])
    return cr.done(a, col, glow=1.2)


def ufo_jelly(col):
    a = cr.new("UfoJelly", {"saucer": "C9D2E3", "saucerD": "6F7F99", "dome": "B9A6FF", "neonP": "FF5FD8",
                            "neonC": "3FF0FF"}, rings=("saucer", "dome"))
    a.prism("saucerD", *C.octa((0, 0), 1.6, 1.6, 1.3, 1.45, cut=0.5))
    a.prism("saucer", *C.octa((0, 0), 2.2, 2.2, 1.45, 1.65, cut=0.7))
    C.blob(a, "dome", (0, 0, 1.9), 0.75, 0.75, 0.6, n=4, z0=1.65)
    for k in range(8):
        t = math.radians(k * 45 + 22.5)
        a.box("neonC" if k % 2 else "neonP", 1.05 * math.cos(t) - 0.08, 1.05 * math.cos(t) + 0.08,
              1.05 * math.sin(t) - 0.08, 1.05 * math.sin(t) + 0.08, 1.5, 1.6, bevel=0)
    for k in range(6):
        t = math.radians(k * 60)
        x, y = 0.5 * math.cos(t), 0.5 * math.sin(t)
        C.tube(a, ["neonP"], [(x, y, 1.3), (x * 1.2 + 0.1, y * 1.2, 0.8), (x, y, 0.3)], 0.06, n=6)
    cr.face(a, (0, -0.68, 2.0), 0.4, 0.18, "round", mouth="open")
    return cr.done(a, col, glow=1.2)


def meteor_hamster(col):
    a = cr.new("MeteorHamster", {"rock": "6E6577", "rockD": "4A4352", "fur": "E3B07A", "cream": "FFF1DC",
                                 "neonO": "FF7A1A", "neonY": "FFC23D"}, rings=("rock", "fur"))
    C.blob(a, "rock", (0, 0.25, 0.85), 1.0, 0.85, 0.85, n=5, z0=0.0)
    for x, z, r in ((-0.6, 1.3, 0.2), (0.55, 0.6, 0.16), (0.4, 1.45, 0.12)):
        C.disc(a, "rockD", x, z, r, -0.62, -0.55, axis="y")
    C.blob(a, "fur", (0, -0.45, 0.9), 0.6, 0.45, 0.55, n=4)
    C.blob(a, "cream", (0, -0.78, 0.75), 0.32, 0.12, 0.25, n=2)
    for s in (1, -1):
        C.blob(a, "fur", (s * 0.38, -0.45, 1.4), 0.14, 0.1, 0.14, n=2)
        C.blob(a, "fur", (s * 0.42, -0.85, 0.65), 0.12, 0.12, 0.1, n=2)
    cr.face(a, (0, -0.86, 1.02), 0.38, 0.16, "big", mouth="open")
    for k, key in enumerate(("neonO", "neonY", "neonO", "neonY")):
        cr.spike(a, key, ((k - 1.5) * 0.35, 0.95, 0.9 + 0.2 * (k % 2)), 0.32, 1.1 - abs(k - 1.5) * 0.25,
                 tilt_x=-100)
    return cr.done(a, col, glow=1.2)


def vacuum_dog(col):
    a = cr.new("VacuumDog", {"shell": "F4F4F4", "bumper": "6F7F99", "fur": "C68B4E", "ear": "8A5A3C", "neonC": "3FF0FF",
                             "red": "E8384F"}, rings=("shell", "fur"))
    a.prism("bumper", C.ngon(0, 0.2, 0.95, 12), 0.08, 0.3)
    a.prism("shell", C.ngon(0, 0.2, 0.92, 12), 0.3, 0.52)
    a.frame("neonC", C.ngon(0, 0.2, 0.6, 12), 0.06, 0.52, 0.56, axis="z")
    for x in (-0.5, 0.0, 0.5):
        a.box("dark", x - 0.08, x + 0.08, -0.8, -0.7, 0.0, 0.1, bevel=0)
    C.blob(a, "fur", (0, -0.65, 0.95), 0.45, 0.42, 0.4, n=4)
    C.blob(a, "fur", (0, -1.05, 0.82), 0.22, 0.2, 0.17, n=2)
    a.box("dark", -0.09, 0.09, -1.27, -1.2, 0.85, 0.96, bevel=0)
    for s in (1, -1):
        cr.plate(a, "ear", [(s * 0.35, 1.25), (s * 0.6, 1.2), (s * 0.62, 0.65), (s * 0.45, 0.6)], -0.75, -0.6)
    cr.face(a, (0, -1.0, 1.08), 0.38, 0.16, "big", mouth=None)
    a.box("tongue", -0.08, 0.08, -1.2, -1.14, 0.58, 0.72, bevel=0.01)
    C.bar(a, "bumper", (0, 1.0, 0.5), (0.1, 1.15, 1.1), 0.05)
    C.blob(a, "red", (0.1, 1.15, 1.15), 0.1, 0.1, 0.1, n=2)
    return cr.done(a, col, glow=1.2)


def synth_squid(col):
    a = cr.new("SynthSquid", {"squid": "8F5BD8", "squidL": "C9A8FF", "keys": "F4F4F4", "keysD": "26262E",
                              "synth": "FF4F8B"}, rings=("squid",))
    for k in range(8):
        t = math.radians(k * 45 + 22.5)
        x, y = 0.35 * math.cos(t), 0.35 * math.sin(t)
        C.tube(a, ["squid"], [(x, y, 0.75), (x * 2.4, y * 2.4, 0.3), (x * 3.2, y * 3.2, 0.08)], [0.12, 0.08], n=6)
    C.blob(a, "squid", (0, 0, 1.0), 0.55, 0.5, 0.45, n=3)
    a.frustum("squid", (-0.55, 0.55, -0.5, 0.5), (-0.1, 0.1, -0.1, 0.1), 1.3, 2.7)
    for s in (1, -1):
        cr.plate(a, "squidL", [(s * 0.3, 2.0), (s * 0.85, 2.5), (s * 0.15, 2.7)], -0.05, 0.05)
    cr.face(a, (0, -0.48, 1.6), 0.42, 0.22, "big", mouth=None)
    cr.turn(a, (0, -0.85, 0.95), -15, "Y")
    a.box("synth", -0.85, 0.85, -0.95, -0.7, 0.85, 1.05)
    a.box("keys", -0.75, 0.75, -0.98, -0.72, 1.05, 1.1, bevel=0)
    for k in range(6):
        x = -0.6 + k * 0.24
        a.box("keysD", x - 0.04, x + 0.04, -0.9, -0.8, 1.1, 1.14, bevel=0)
    a.box("synth", 0.85, 1.25, -0.9, -0.75, 0.9, 1.0)
    a.transform = None
    return cr.done(a, col)


def asteroid_turtle(col):
    a = cr.new("AsteroidTurtle", {"rock": "7C7488", "rockD": "4E475A", "skin": "4FC3A1", "flag": "E8384F",
                                  "pole": "D6DEE8"}, rings=("rock", "skin"))
    for x, y in ((0.65, -0.5), (-0.65, -0.5), (0.65, 0.6), (-0.65, 0.6)):
        C.blob(a, "skin", (x, y, 0.22), 0.24, 0.26, 0.22, n=2, z0=0.0)
    C.blob(a, "rock", (0, 0.05, 0.75), 1.05, 1.0, 0.75, n=4, z0=0.3)
    for x, y, z, r in ((0.3, -0.45, 1.3, 0.22), (-0.45, 0.1, 1.35, 0.18), (0.2, 0.5, 1.4, 0.15), (-0.6, -0.5, 0.9, 0.14)):
        C.disc(a, "rockD", x, y, r, z, z + 0.08)
    C.bar(a, "pole", (0.1, 0.1, 1.45), (0.1, 0.1, 2.25), 0.05)
    a.box("flag", 0.12, 0.6, 0.07, 0.13, 1.9, 2.22, bevel=0)
    C.blob(a, "skin", (0, -1.05, 0.55), 0.35, 0.33, 0.3, n=3)
    cr.face(a, (0, -1.36, 0.62), 0.3, 0.13, "round", mouth="smile")
    C.tube(a, ["skin"], [(0, -0.7, 0.45), (0, -0.9, 0.5)], 0.22)
    return cr.done(a, col)


def sat_owl(col):
    a = cr.new("SatOwl", {"body": "8FA3C8", "bodyL": "C9D2E3", "panel": "2F4FB8", "grid": "9EC1FF", "dish": "D6DEE8",
                          "neonY": "FFE23F", "beak": "FFB347"}, rings=("body",))
    C.blob(a, "body", (0, 0, 1.0), 0.6, 0.55, 0.85, n=5, z0=0.1)
    C.blob(a, "bodyL", (0, -0.35, 0.9), 0.4, 0.25, 0.55, n=3)
    for s in (1, -1):
        C.round_eye(a, (s * 0.24, -0.52, 1.35), 0.2, look=(0, -0.1), iris="neonY")
        a.box("beak", s * 0.2 - 0.1, s * 0.2 + 0.1, -0.35, 0.05, 0.0, 0.12)
        C.bar(a, "dish", (s * 0.55, 0, 1.1), (s * 0.85, 0, 1.15), 0.08)
        a.box("panel", s * 0.85, s * 1.85, -0.04, 0.04, 0.75, 1.55)
        for k in range(3):
            x = s * (1.1 + k * 0.3)
            a.box("grid", x - 0.015, x + 0.015, -0.07, -0.04, 0.75, 1.55, bevel=0)
        a.box("grid", min(s * 0.85, s * 1.85), max(s * 0.85, s * 1.85), -0.07, -0.04, 1.14, 1.17, bevel=0)
    cr.spike(a, "beak", (0, -0.55, 1.15), 0.12, 0.2, tilt_x=160)
    a.frustum("dish", (-0.12, 0.12, -0.12, 0.12), (-0.45, 0.45, -0.45, 0.45), 1.85, 2.05,
              matrix=C.tilt((0, 0, 1.85), "X", -25))
    C.bar(a, "dish", (0, 0, 1.85), (0, -0.15, 2.3), 0.04)
    return cr.done(a, col, glow=1.2)


def slime_skater(col):
    a = cr.new("MarsSlime", {"slime": "7BE36A", "slimeD": "49B33A", "board": "D63BC8", "neonC": "3FF0FF"},
               rings=("slime", "board"))
    a.prism("board", *C.octa((0, 0), 1.1, 2.6, 0.45, 0.6, cut=0.45))
    for y in (-0.8, 0.8):
        C.disc(a, "neonC", 0, y, 0.3, 0.32, 0.45)
    C.blob(a, "slime", (0, 0, 1.15), 0.7, 0.75, 0.6, n=4, z0=0.6)
    C.blob(a, "slime", (0, 0, 1.65), 0.42, 0.42, 0.35, n=3)
    for s in (1, -1):
        C.bar(a, "slimeD", (s * 0.15, -0.1, 1.9), (s * 0.35, -0.25, 2.45), 0.07)
        C.round_eye(a, (s * 0.35, -0.38, 2.5), 0.14, look=(0, -0.2))
        C.blob(a, "slime", (s * 0.55, 0.2, 0.62), 0.18, 0.25, 0.08, n=2)
    cr.face(a, (0, -0.68, 1.15), 0.3, 0.1, "happy", mouth="open", blush=False)
    return cr.done(a, col, glow=1.3)


def comet_dragon(col):
    a = cr.new("CometDragon", {"crystal": "6FD6FF", "crystalP": "B07CFF", "belly": "E6F7FF", "neonC": "8BEFFF",
                               "neonP": "FF7BE5", "iris": "2B4A9C"}, rings=("crystal",))
    z = 1.3
    C.blob(a, "crystal", (0, 0, z), 0.5, 0.65, 0.45, n=4)
    C.blob(a, "belly", (0, -0.25, z - 0.1), 0.32, 0.35, 0.3, n=3)
    C.blob(a, "crystal", (0, -0.7, z + 0.55), 0.4, 0.42, 0.36, n=3)
    cr.spike(a, "crystal", (0, -1.0, z + 0.45), 0.3, 0.35, tilt_x=95)
    cr.face(a, (0, -1.0, z + 0.62), 0.34, 0.15, "big", iris="iris", mouth=None)
    for s in (1, -1):
        cr.spike(a, "crystalP", (s * 0.2, -0.6, z + 0.85), 0.16, 0.45, tilt_x=-35, tilt_y=s * 15)
        C.bar(a, "crystal", (s * 0.3, -0.2, z - 0.3), (s * 0.4, -0.35, z - 0.8), 0.12)
    cr.wings(a, "crystalP", (0, 0.1, z + 0.3), 1.1, 0.9, spread=20)
    for k in range(4):
        cr.spike(a, "crystalP", (0, -0.3 + k * 0.25, z + 0.38), 0.14, 0.3, tilt_x=-25)
    for k, key in enumerate(("neonC", "neonP", "neonC", "neonP", "neonC")):
        r = 0.32 - k * 0.05
        C.blob(a, key, (0.15 * math.sin(k), 0.7 + k * 0.42, z - 0.05 - k * 0.12), r, r * 1.3, r, n=2)
    return cr.done(a, col, glow=1.2)


def blackhole_kitten(col):
    a = cr.new("BlackHoleKitten", {"void": "241838", "voidL": "3E2C5E", "neonO": "FF8C1A", "neonP": "FF4FD8",
                                   "neonY": "FFE23F"}, rings=("void",))
    C.blob(a, "void", (0, 0.1, 0.65), 0.6, 0.55, 0.65, n=4, z0=0.0)
    C.blob(a, "void", (0, -0.05, 1.45), 0.5, 0.45, 0.42, n=4)
    for s in (1, -1):
        cr.spike(a, "void", (s * 0.28, -0.05, 1.75), 0.24, 0.38, tilt_y=s * 12)
        a.prism("neonY", C.ngon(s * 0.2, 1.48, 0.13, 4, phase=0), -0.52, -0.46, axis="y", bevel=0)  # глаза-звёздочки
        C.blob(a, "void", (s * 0.25, -0.4, 0.2), 0.14, 0.14, 0.12, n=2)
    a.box("voidL", -0.1, 0.1, -0.5, -0.46, 1.28, 1.34, bevel=0)
    C.tube(a, ["void"], [(0, 0.6, 0.3), (0.4, 0.9, 0.7), (0.3, 0.8, 1.2)], [0.1, 0.08])
    ring = C.tilt((0, 0.05, 1.0), "X", 18)
    a.frame("neonO", C.ngon(0, 0.05, 1.25, 16), 0.12, 0.96, 1.04, axis="z", matrix=ring)
    a.frame("neonP", C.ngon(0, 0.05, 1.08, 16), 0.08, 0.98, 1.02, axis="z", matrix=ring)
    for x, y, z in ((-1.1, -0.3, 1.9), (1.0, 0.2, 2.1), (0.7, -0.6, 0.4), (-0.8, 0.5, 0.3)):
        C.gem(a, "neonY", (x, y, z), 0.12)
    return cr.done(a, col, glow=1.5)


CREATURES = [
    ("space_cat", "Кот-скафандр", "Common", space_cat),
    ("ufo_jelly", "Медуза-НЛО", "Common", ufo_jelly),
    ("meteor_hamster", "Хомяк-метеорит", "Common", meteor_hamster),
    ("vacuum_dog", "Робот-пёс-пылесос", "Rare", vacuum_dog),
    ("synth_squid", "Кальмар-синтезаторщик", "Rare", synth_squid),
    ("asteroid_turtle", "Астероид-черепаха", "Rare", asteroid_turtle),
    ("sat_owl", "Спутник-сова", "Epic", sat_owl),
    ("slime_skater", "Марсианский слизень-скейтер", "Epic", slime_skater),
    ("comet_dragon", "Кристальный дракон-комета", "Legendary", comet_dragon),
    ("blackhole_kitten", "«Чёрная дыра»-котёнок", "Secret", blackhole_kitten),
]
