"""Коллекция босса 5 «Морозный двор» — 10 примеров (черновые концепты, не финальные модели)."""

import ck as C
import cr

EXPOSURE = -0.2


def penguin(col):
    a = cr.new("Pengu", {"navy": "26355E", "belly": "F4F6FA", "beak": "FF9F1C", "board": "2EC4F1", "stripe": "FF4F8B",
                         "goggle": "FFD23F", "lens": "6FD6FF"}, rings=("navy", "board"))
    cr.turn(a, (0, 0, 0), 25)
    a.prism("board", *C.octa((0, 0), 3.0, 1.0, 0.0, 0.16, cut=0.45))
    a.box("stripe", -1.2, 1.2, -0.12, 0.12, 0.16, 0.2, bevel=0)
    a.transform = None
    C.blob(a, "navy", (0, 0.1, 1.3), 0.85, 0.75, 1.05, n=6, z0=0.2)
    C.blob(a, "belly", (0, -0.25, 1.15), 0.62, 0.5, 0.8, n=5)
    C.blob(a, "navy", (0, 0.0, 2.45), 0.62, 0.58, 0.55, n=5)
    C.blob(a, "belly", (0, -0.35, 2.35), 0.45, 0.25, 0.35, n=3)
    cr.face(a, (0, -0.6, 2.45), 0.48, 0.22, "big", mouth=None)
    cr.spike(a, "beak", (0, -0.52, 2.25), 0.28, 0.42, tilt_x=95)
    a.frame("goggle", C.ngon(0, 0, 0.63, 8), 0.1, 2.68, 2.82, axis="z")
    for s in (1, -1):
        a.box("lens", s * 0.24 - 0.17, s * 0.24 + 0.17, -0.7, -0.58, 2.66, 2.88, bevel=0.01)
    cr.wings(a, "navy", (0, 0.05, 1.75), 0.95, 0.9, spread=5)
    for s in (1, -1):
        a.box("beak", s * 0.35 - 0.2, s * 0.35 + 0.2, -0.55, 0.1, 0.16, 0.32)
    return cr.done(a, col)


def yeti(col):
    a = cr.new("Yeti", {"fur": "E9F1FA", "face": "8FB8E8", "horn": "F3E9D2", "thermos": "E8384F", "cap": "B9C3D1",
                        "steam": "FFFFFF"}, rings=("fur",))
    C.blob(a, "fur", (0, 0, 1.25), 1.0, 0.85, 1.15, n=6, z0=0.05)
    for s in (1, -1):
        C.blob(a, "fur", (s * 0.5, -0.35, 0.18), 0.4, 0.55, 0.18, n=3, z0=0.0)
        cr.spike(a, "horn", (s * 0.55, 0, 2.2), 0.22, 0.45, tilt_y=s * 25)
        C.tube(a, ["fur"], [(s * 0.85, -0.1, 1.5), (s * 0.75, -0.75, 1.05)], 0.24)
    cr.spike(a, "fur", (0, 0, 2.3), 0.3, 0.35)
    C.blob(a, "face", (0, -0.7, 1.6), 0.6, 0.18, 0.48, n=3)
    cr.face(a, (0, -0.86, 1.72), 0.5, 0.24, "round", mouth="open")
    a.prism("thermos", C.ngon(0.75, -0.95, 0.22), 0.7, 1.45)
    a.prism("cap", C.ngon(0.75, -0.95, 0.24), 1.45, 1.6)
    for k in range(3):
        C.blob(a, "steam", (0.75 + 0.08 * k, -0.95, 1.8 + 0.25 * k), 0.12 + 0.03 * k, 0.12, 0.1, n=2)
    return cr.done(a, col)


def fox(col):
    a = cr.new("Fox", {"orange": "FF8A3D", "cream": "FFF1DC", "helmet": "2F6BFF", "stick": "C68B4E", "tape": "1D1D1D",
                       "iris": "8A4B16"}, rings=("orange", "helmet"))
    C.blob(a, "orange", (0, 0.1, 1.0), 0.65, 0.6, 0.85, n=5, z0=0.1)
    C.blob(a, "cream", (0, -0.28, 1.05), 0.42, 0.35, 0.55, n=4)
    C.blob(a, "orange", (0, -0.05, 2.05), 0.55, 0.5, 0.45, n=4)
    cr.spike(a, "orange", (0, -0.42, 1.92), 0.4, 0.5, tilt_x=95)
    a.box("tape", -0.07, 0.07, -0.98, -0.88, 1.84, 1.94, bevel=0)
    for s in (1, -1):
        cr.spike(a, "orange", (s * 0.32, 0.0, 2.3), 0.3, 0.55, tilt_y=s * 15)
        C.blob(a, "orange", (s * 0.35, -0.45, 0.25), 0.25, 0.4, 0.22, n=3, z0=0.0)
    C.blob(a, "helmet", (0, 0.02, 2.28), 0.6, 0.56, 0.34, n=3, z0=2.22)
    cr.face(a, (0, -0.52, 2.1), 0.42, 0.18, "big", iris="iris", mouth=None)
    C.blob(a, "orange", (0.75, 0.65, 0.75), 0.42, 0.42, 0.75, n=4, matrix=C.tilt((0.75, 0.65, 0.75), "Y", -35))
    C.blob(a, "cream", (1.18, 0.65, 1.32), 0.24, 0.24, 0.24, n=3)
    C.bar(a, "stick", (-0.55, -0.55, 1.35), (-0.95, -0.95, 0.1), 0.1)
    a.box("stick", -1.4, -0.9, -1.05, -0.88, 0.0, 0.16)
    a.box("tape", -1.3, -1.05, -1.08, -0.86, 0.02, 0.17, bevel=0)
    C.disc(a, "tape", -0.3, -1.35, 0.22, 0.0, 0.12)
    return cr.done(a, col)


def snowman(col):
    a = cr.new("Snowman", {"snow": "F4F8FF", "carrot": "FF8C1A", "scarf": "2EC4B6", "wood": "B5793A", "box": "C9A06B",
                           "tape": "E8384F", "cap": "E8384F"}, rings=("snow", "wood", "box"))
    for s in (1, -1):
        C.bar(a, "wood", (s * 0.55, -1.0, 0.08), (s * 0.55, 1.0, 0.08), 0.12)
        C.bar(a, "wood", (s * 0.55, -1.0, 0.08), (s * 0.55, -1.3, 0.45), 0.12)
        for y in (-0.6, 0.6):
            C.bar(a, "wood", (s * 0.55, y, 0.1), (s * 0.55, y, 0.32), 0.1)
    a.box("wood", -0.75, 0.75, -0.95, 0.95, 0.32, 0.45)
    C.blob(a, "snow", (0, 0.25, 0.98), 0.62, 0.6, 0.55, n=5)
    C.blob(a, "snow", (0, 0.25, 1.82), 0.42, 0.4, 0.4, n=4)
    cr.spike(a, "carrot", (0, -0.12, 1.82), 0.13, 0.45, tilt_x=95)
    cr.face(a, (0, -0.14, 1.95), 0.3, 0.1, "round", mouth="smile", look=(0, 0))
    for z in (0.8, 1.05):
        a.box("dark", -0.06, 0.06, -0.38, -0.32, z, z + 0.1, bevel=0)
    a.frame("scarf", C.ngon(0, 0.25, 0.44, 8), 0.14, 1.42, 1.56, axis="z")
    a.box("scarf", 0.15, 0.32, -0.25, -0.14, 0.95, 1.45)
    C.blob(a, "cap", (0, 0.25, 2.15), 0.4, 0.4, 0.22, n=2, z0=2.08)
    C.blob(a, "white", (0, 0.25, 2.42), 0.12, 0.12, 0.12, n=2)
    a.box("box", 0.15, 0.7, -0.88, -0.32, 0.45, 0.95)
    a.box("tape", 0.36, 0.48, -0.9, -0.3, 0.45, 0.97, bevel=0)
    for s in (1, -1):
        C.bar(a, "wood", (s * 0.55, 0.25, 1.1), (s * 0.95, -0.2, 1.35), 0.06)
    return cr.done(a, col)


def seal(col):
    a = cr.new("SealDJ", {"gray": "9AA8B8", "belly": "D6DEE8", "phones": "FF4F8B", "deck": "2A2D3A", "ice": "8EDDFA",
                          "neonC": "3FF0FF"}, rings=("gray",))
    C.blob(a, "gray", (0, 0.45, 0.6), 0.75, 1.15, 0.6, n=5, z0=0.0)
    C.blob(a, "gray", (0, -0.35, 1.25), 0.55, 0.5, 0.5, n=4)
    C.blob(a, "belly", (0, -0.78, 1.08), 0.3, 0.12, 0.18, n=2)
    a.box("dark", -0.08, 0.08, -0.93, -0.85, 1.18, 1.28, bevel=0)
    cr.face(a, (0, -0.84, 1.35), 0.38, 0.2, "cool", mouth="smile", blush=False)
    for s in (1, -1):
        a.box("phones", s * 0.52, s * 0.66, -0.55, -0.15, 1.1, 1.5, bevel=0.02)
        C.blob(a, "gray", (s * 0.7, -0.35, 0.3), 0.3, 0.4, 0.12, n=2)
    C.bar(a, "phones", (-0.6, -0.35, 1.5), (0, -0.35, 1.82), 0.1)
    C.bar(a, "phones", (0, -0.35, 1.82), (0.6, -0.35, 1.5), 0.1)
    a.prism("gray", [(-0.6, 1.6), (0.0, 1.45), (0.6, 1.6), (0.0, 1.95)], 0.05, 0.18)
    a.box("deck", -0.75, 0.75, -1.65, -1.0, 0.0, 0.38)
    for s in (1, -1):
        C.disc(a, "ice", s * 0.35, -1.32, 0.24, 0.38, 0.44)
        C.disc(a, "neonC", s * 0.35, -1.32, 0.07, 0.44, 0.47, bevel=0)
    return cr.done(a, col)


def owl(col):
    a = cr.new("Owl", {"white": "EEF2F8", "spots": "8D9AAE", "beak": "FFB347", "glasses": "3A3F55", "snow": "DDE8F5",
                       "iris": "FFC83A"}, rings=("white", "snow"))
    C.blob(a, "snow", (0, 0, 0.15), 1.1, 1.0, 0.3, n=2, z0=0.0)
    C.blob(a, "white", (0, 0, 1.25), 0.85, 0.75, 1.1, n=6, z0=0.2)
    for x, z in ((-0.35, 0.9), (0.2, 0.7), (0.45, 1.1), (-0.1, 1.15), (0.0, 0.55)):
        a.box("spots", x - 0.08, x + 0.08, -0.76, -0.68, z, z + 0.08, bevel=0)
    for s in (1, -1):
        cr.spike(a, "white", (s * 0.45, 0.0, 2.1), 0.25, 0.45, tilt_y=s * 20)
        C.round_eye(a, (s * 0.32, -0.72, 1.62), 0.26, look=(0, -0.1), iris="iris")
        a.frame("glasses", C.ngon(s * 0.32, 1.62, 0.33, 8), 0.07, -0.86, -0.8, axis="y")
        C.blob(a, "white", (s * 0.82, 0.1, 1.1), 0.18, 0.55, 0.65, n=3)
        a.box("beak", s * 0.25 - 0.12, s * 0.25 + 0.12, -0.6, -0.3, 0.3, 0.42)
    a.box("glasses", -0.06, 0.06, -0.86, -0.8, 1.62, 1.7, bevel=0)
    cr.spike(a, "beak", (0, -0.72, 1.4), 0.18, 0.28, tilt_x=160)
    return cr.done(a, col)


def narwhal(col):
    a = cr.new("Narwhal", {"body": "5F7FB8", "belly": "DCE6F5", "tusk": "F3E9D2", "brass": "F2B630", "spot": "3E5A8C"},
               rings=("body",))
    C.blob(a, "body", (0, 0.3, 1.0), 0.72, 1.4, 0.75, n=6, z0=0.2)
    C.blob(a, "belly", (0, 0.1, 0.65), 0.55, 1.1, 0.4, n=3, z0=0.25)
    C.tube(a, ["body"], [(0, 1.5, 1.1), (0, 2.15, 1.45)], [0.3])
    a.prism("body", [(-0.75, 2.35), (0, 2.05), (0.75, 2.35), (0, 2.65)], 1.38, 1.52)
    for x, y in ((-0.3, 0.6), (0.25, 0.9), (0.0, 0.2)):
        a.box("spot", x - 0.1, x + 0.1, y - 0.1, y + 0.1, 1.72, 1.76, bevel=0)
    cr.spike(a, "tusk", (0, -1.0, 1.35), 0.18, 1.5, tilt_x=72)
    cr.face(a, (0, -1.04, 1.12), 0.6, 0.2, "happy", mouth=None)
    for s in (1, -1):
        a.prism("body", [(s * 0.65, -0.2), (s * 1.15, 0.1), (s * 0.65, 0.45)], 0.45, 0.58)
    C.bar(a, "brass", (0, -1.12, 0.9), (0, -1.75, 0.85), 0.1)
    C.bar(a, "brass", (0.2, -1.12, 1.0), (0.2, -1.75, 0.95), 0.1)
    C.bar(a, "brass", (0, -1.75, 0.85), (0.2, -1.75, 0.95), 0.1)
    C.bar(a, "brass", (0.2, -1.12, 1.0), (0.5, -0.8, 1.7), 0.09)
    a.frustum("brass", (0.4, 0.6, -0.9, -0.7), (0.15, 0.85, -1.15, -0.45), 1.7, 2.25,
              matrix=C.tilt((0.5, -0.8, 1.7), "X", 25))
    return cr.done(a, col)


def mammoth(col):
    a = cr.new("Mammoth", {"fur": "8A5A3C", "furL": "B07A52", "jacket": "E8384F", "jacketB": "FFD23F", "tusk": "F3E9D2",
                           "iris": "3A2A1A"}, rings=("fur", "jacket"))
    cr.legs(a, "fur", [(0.55, -0.4), (-0.55, -0.4), (0.55, 0.9), (-0.55, 0.9)], 0.3, 0.7)
    C.blob(a, "fur", (0, 0.3, 1.2), 0.95, 1.15, 0.8, n=5)
    for k, key in enumerate(("jacket", "jacketB", "jacket")):
        a.prism(key, *C.octa((0, 0.3), 2.05, 2.4, 0.85 + k * 0.32, 1.13 + k * 0.32, cut=0.65))
    C.blob(a, "fur", (0, -0.85, 1.65), 0.65, 0.55, 0.6, n=4)
    for s in (1, -1):
        cr.plate(a, "furL", [(s * 0.55, 1.4), (s * 1.2, 1.95), (s * 1.3, 1.3), (s * 0.8, 0.95)], -0.5, -0.38)
        cr.spike(a, "tusk", (s * 0.3, -1.25, 1.2), 0.13, 0.6, tilt_x=125, tilt_y=s * 10)
    C.tube(a, ["fur"], [(0, -1.3, 1.45), (0, -1.65, 0.95), (0, -1.55, 0.5), (0, -1.25, 0.45)], [0.22, 0.18, 0.14])
    cr.face(a, (0, -1.36, 1.82), 0.55, 0.18, "big", iris="iris", mouth=None)
    for x in (-0.15, 0.0, 0.15):
        cr.spike(a, "furL", (x, -0.85, 2.15), 0.12, 0.3, tilt_y=x * 120)
    return cr.done(a, col)


def jelly(col):
    a = cr.new("AuroraJelly", {"bell": "8F7CFF", "bellL": "C9B8FF", "neonG": "3DFFB0", "neonP": "FF5FD8",
                               "neonB": "4FC3FF"}, rings=("bell",))
    C.blob(a, "bell", (0, 0, 2.55), 0.95, 0.95, 0.8, n=5, z0=2.2)
    a.frame("bellL", C.ngon(0, 0, 0.98, 8), 0.16, 2.12, 2.3, axis="z")
    keys = ("neonG", "neonP", "neonB")
    for i in range(7):
        t = i * 2 * 3.14159 / 7
        x, y = 0.62 * C.math.cos(t), 0.62 * C.math.sin(t)
        pts = [(x, y, 2.15), (x * 1.15 + 0.1, y * 1.15, 1.5), (x * 0.9 - 0.1, y * 0.9, 0.95), (x * 1.1, y * 1.1, 0.4)]
        C.tube(a, [keys[i % 3]], pts, 0.07, n=6)
    for i in range(5):
        t = i * 2 * 3.14159 / 5
        C.gem(a, keys[i % 3], (0.45 * C.math.cos(t), 0.45 * C.math.sin(t), 3.3), 0.18)
    cr.face(a, (0, -0.86, 2.62), 0.45, 0.22, "happy", mouth="smile")
    return cr.done(a, col, glow=2.0)


def ice_dragon(col):
    a = cr.new("IceDragon", {"ice": "8EDDFA", "iceD": "3F8FD6", "belly": "E6F7FF", "blade": "D6DEE8", "crystal": "B9F3FF",
                             "iris": "2B4A9C"}, rings=("ice",))
    C.blob(a, "ice", (0, 0, 1.6), 0.6, 0.55, 0.75, n=5, matrix=C.tilt((0, 0, 1.6), "X", 15))
    C.blob(a, "belly", (0, -0.35, 1.55), 0.38, 0.28, 0.5, n=3)
    C.blob(a, "ice", (0, -0.4, 2.45), 0.5, 0.5, 0.45, n=4)
    cr.spike(a, "ice", (0, -0.8, 2.35), 0.38, 0.45, tilt_x=95)
    cr.face(a, (0, -0.86, 2.55), 0.4, 0.17, "big", iris="iris", mouth=None)
    for s in (1, -1):
        cr.spike(a, "crystal", (s * 0.25, -0.2, 2.8), 0.16, 0.5, tilt_x=-30, tilt_y=s * 15)
        C.tube(a, ["ice"], [(s * 0.5, -0.1, 1.95), (s * 1.15, -0.1, 2.2)], 0.12)
    cr.wings(a, "iceD", (0, 0.35, 1.9), 1.0, 0.9, spread=25)
    C.tube(a, ["ice"], [(0, 0.45, 1.25), (0, 1.0, 1.4), (0, 1.3, 1.9)], [0.2, 0.13])
    for k in range(3):
        cr.spike(a, "crystal", (0, 0.45 + k * 0.05, 1.7 + k * 0.35), 0.14, 0.32, tilt_x=-35)
    C.tube(a, ["ice"], [(0.18, 0.0, 1.05), (0.2, -0.05, 0.3)], 0.17)
    a.box("iceD", 0.0, 0.4, -0.3, 0.2, 0.08, 0.32)
    a.box("blade", 0.17, 0.23, -0.45, 0.35, 0.0, 0.08, bevel=0)
    C.tube(a, ["ice"], [(-0.2, 0.2, 1.1), (-0.25, 0.95, 1.45)], 0.15)
    a.box("iceD", -0.45, -0.05, 0.9, 1.35, 1.35, 1.6)
    a.box("blade", -0.28, -0.22, 0.8, 1.55, 1.3, 1.36, bevel=0)
    return cr.done(a, col)


CREATURES = [
    ("penguin", "Пингвин-сноубордист", "Common", penguin),
    ("yeti", "Йети-малыш с термосом", "Common", yeti),
    ("fox", "Лиса-хоккеистка", "Common", fox),
    ("snowman", "Снеговик-курьер", "Common", snowman),
    ("seal", "Тюлень-диджей", "Rare", seal),
    ("owl", "Сова-снежок в очках", "Rare", owl),
    ("narwhal", "Нарвал-тромбонист", "Epic", narwhal),
    ("mammoth", "Мамонтёнок в пуховике", "Epic", mammoth),
    ("jelly", "Медуза-сияние", "Legendary", jelly),
    ("ice_dragon", "Ледяной дракончик-фигурист", "Legendary", ice_dragon),
]
