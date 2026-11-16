"""Коллекция босса 7 «Сокровищница» — 10 примеров (черновые концепты, не финальные модели)."""

import math

import ck as C
import cr
from mathutils import Matrix


def piggy(col):
    a = cr.new("PiggyBot", {"pink": "FF9EC1", "pinkD": "E9709B", "metal": "9AA8B8", "red": "E8384F", "gold": "F2C230"},
               rings=("pink",))
    cr.legs(a, "metal", [(0.45, -0.3), (-0.45, -0.3), (0.45, 0.45), (-0.45, 0.45)], 0.18, 0.55)
    for x, y in ((0.45, -0.3), (-0.45, -0.3)):
        a.box("metal", x - 0.22, x + 0.22, y - 0.32, y + 0.15, 0.0, 0.14)
    C.blob(a, "pink", (0, 0.05, 1.15), 0.85, 0.8, 0.7, n=5)
    a.box("dark", -0.3, 0.3, -0.06, 0.06, 1.8, 1.86, bevel=0)
    C.disc(a, "pinkD", 0, 1.05, 0.3, -0.92, -0.72, axis="y", sy=0.7)
    for s in (1, -1):
        a.box("dark", s * 0.12 - 0.05, s * 0.12 + 0.05, -0.95, -0.9, 1.0, 1.1, bevel=0)
        cr.spike(a, "pinkD", (s * 0.5, -0.05, 1.7), 0.25, 0.35, tilt_y=s * 30)
        for z in (0.95, 1.35):
            a.box("metal", s * 0.84, s * 0.92, -0.3, -0.18, z, z + 0.08, bevel=0)  # заклёпки
    cr.face(a, (0, -0.76, 1.4), 0.5, 0.18, "big", mouth=None)
    C.bar(a, "metal", (0, 0.3, 1.82), (0, 0.3, 2.35), 0.06)
    C.blob(a, "red", (0, 0.3, 2.42), 0.12, 0.12, 0.12, n=2)
    cr.coin(a, "gold", (0.0, 0.0, 1.95), 0.22, 0.06, tilt=80)
    return cr.done(a, col)


def coin_slug(col):
    a = cr.new("CoinSlug", {"slug": "7FE0C1", "slugD": "48B894", "gold": "F2C230", "goldD": "C8901C"},
               rings=("slug", "gold"))
    C.blob(a, "slug", (0, 0.3, 0.3), 0.45, 1.1, 0.3, n=3, z0=0.0)
    C.tube(a, ["slug"], [(0, -0.55, 0.3), (0, -0.75, 0.85)], 0.3)
    C.blob(a, "slug", (0, -0.75, 0.95), 0.32, 0.3, 0.25, n=3)
    for s in (1, -1):
        C.bar(a, "slugD", (s * 0.12, -0.75, 1.1), (s * 0.25, -0.8, 1.55), 0.07)
        C.round_eye(a, (s * 0.25, -0.88, 1.6), 0.12, look=(0, -0.2))
    a.box("dark", -0.12, 0.12, -1.06, -1.0, 0.8, 0.86, bevel=0)
    C.disc(a, "gold", 1.05, 0.45, 0.78, -0.12, 0.12, n=12, axis="x")
    a.frame("goldD", C.ngon(1.05, 0.45, 0.66, 12), 0.08, 0.12, 0.16, axis="x")
    a.frame("goldD", C.ngon(1.05, 0.45, 0.66, 12), 0.08, -0.16, -0.12, axis="x")
    C.disc(a, "goldD", 1.05, 0.45, 0.25, 0.12, 0.18, n=5, axis="x")
    return cr.done(a, col)


def wallet_croc(col):
    a = cr.new("WalletCroc", {"leather": "7A4A2A", "stitch": "E3C16F", "croc": "4FAF5A", "crocD": "2E7D3E",
                              "card1": "2F6BFF", "card2": "FF4F8B"}, rings=("leather", "croc"))
    a.box("leather", -0.65, 0.65, -0.35, 1.15, 0.15, 0.75)
    a.box("stitch", -0.6, 0.6, -0.37, -0.34, 0.44, 0.47, bevel=0)
    for x, key in ((-0.3, "card1"), (0.1, "card2")):
        a.box(key, x - 0.2, x + 0.2, 0.0, 0.08, 0.75, 1.1, bevel=0.01)
    a.box("croc", -0.5, 0.5, -1.25, -0.3, 0.15, 0.45)
    a.box("croc", -0.5, 0.5, -1.2, -0.3, 0.55, 0.78)
    a.box("dark", -0.45, 0.45, -1.2, -0.35, 0.45, 0.55, bevel=0)
    for k in range(7):
        x = -0.4 + k * 0.133
        a.frustum("white", (x - 0.05, x + 0.05, -1.24, -1.16), (x, x, -1.2, -1.2), 0.55, 0.47, bevel=0)
        a.frustum("white", (x - 0.05, x + 0.05, -1.24, -1.16), (x + 0.066, x + 0.066, -1.2, -1.2), 0.45, 0.53, bevel=0)
    for s in (1, -1):
        C.blob(a, "croc", (s * 0.3, -0.5, 0.88), 0.17, 0.17, 0.15, n=2)
        C.round_eye(a, (s * 0.3, -0.66, 0.92), 0.1, look=(0, -0.2))
        for y in (-0.2, 0.95):
            C.blob(a, "crocD", (s * 0.7, y, 0.15), 0.18, 0.22, 0.15, n=2, z0=0.0)
    C.tube(a, ["croc", "crocD"], [(0, 1.15, 0.4), (0.2, 1.7, 0.3), (0.55, 2.0, 0.2)], [0.25, 0.15])
    return cr.done(a, col)


def safe_turtle(col):
    a = cr.new("SafeTurtle", {"steel": "8A97AA", "steelD": "56637A", "skin": "6CC36B", "gold": "F2C230"},
               rings=("steel", "skin"))
    for x, y in ((0.65, -0.55), (-0.65, -0.55), (0.65, 0.65), (-0.65, 0.65)):
        C.blob(a, "skin", (x, y, 0.22), 0.25, 0.28, 0.22, n=2, z0=0.0)
    a.prism("steel", *C.octa((0, 0.05), 1.7, 1.8, 0.3, 1.25, cut=0.3))
    a.prism("steelD", *C.octa((0, 0.05), 1.78, 1.88, 0.3, 0.45, cut=0.3))
    a.box("steelD", -0.7, 0.7, -0.88, -0.84, 0.5, 1.15, bevel=0)
    C.disc(a, "gold", 0.2, 0.85, 0.22, -0.95, -0.86, axis="y")
    C.disc(a, "steelD", 0.2, 0.85, 0.1, -1.0, -0.95, axis="y", bevel=0)
    a.box("gold", -0.45, -0.3, -0.98, -0.86, 0.65, 1.0)
    C.blob(a, "skin", (0, -1.15, 0.6), 0.38, 0.35, 0.32, n=3)
    cr.face(a, (0, -1.47, 0.68), 0.32, 0.13, "sleepy", lid_key="skin", mouth="smile")
    C.tube(a, ["skin"], [(0, -0.85, 0.5), (0, -1.0, 0.55)], 0.22)
    return cr.done(a, col)


def atm(col):
    a = cr.new("ATM", {"body": "2F6BFF", "bodyD": "1D47B8", "screen": "141A2E", "neonC": "3FF0FF", "key": "D6DEE8",
                       "bill": "7FD87A", "gold": "F2C230"}, rings=("body",))
    cr.legs(a, "bodyD", [(0.35, 0), (-0.35, 0)], 0.15, 0.35)
    a.box("body", -0.7, 0.7, -0.45, 0.5, 0.35, 2.4)
    a.box("bodyD", -0.75, 0.75, -0.5, 0.55, 2.4, 2.6)
    a.box("screen", -0.5, 0.5, -0.5, -0.4, 1.55, 2.2, bevel=0.01)
    for s in (1, -1):
        a.box("neonC", s * 0.22 - 0.1, s * 0.22 + 0.1, -0.53, -0.5, 1.8, 2.0, bevel=0)
    a.box("neonC", -0.18, 0.18, -0.53, -0.5, 1.65, 1.7, bevel=0)
    for i in range(3):
        for j in range(3):
            a.box("key", -0.3 + i * 0.2 - 0.07, -0.3 + i * 0.2 + 0.07, -0.55, -0.45, 0.8 + j * 0.17, 0.92 + j * 0.17,
                  bevel=0.01)
    a.box("dark", -0.4, 0.4, -0.52, -0.44, 1.32, 1.42, bevel=0)
    C.bar(a, "bill", (0, -0.5, 1.37), (0.05, -0.95, 1.05), 0.45, 0.04)
    for s in (1, -1):
        C.tube(a, ["body"], [(s * 0.7, 0, 1.5), (s * 1.0, -0.4, 1.1)], 0.12)
        cr.coin(a, "gold", (s * 1.05, -0.5, 0.95), 0.18, 0.06, tilt=70)
    return cr.done(a, col)


def card_squirrel(col):
    a = cr.new("CardSquirrel", {"fur": "B08A6A", "cream": "F1DEC8", "card": "7A2BD8", "chip": "F2C230",
                                "stripe": "26262E"}, rings=("fur", "card"))
    z = 1.1
    a.box("card", -1.4, 1.4, -0.05, 0.05, z - 0.85, z + 0.85, bevel=0.02, matrix=C.tilt((0, 0, z), "X", 90))
    a.box("chip", -1.15, -0.75, -0.08, -0.04, z + 0.3, z + 0.6, bevel=0, matrix=C.tilt((0, 0, z), "X", 90))
    a.box("stripe", -1.35, 1.35, -0.08, -0.05, z - 0.6, z - 0.45, bevel=0, matrix=C.tilt((0, 0, z), "X", 90))
    C.blob(a, "fur", (0, 0.0, z + 0.25), 0.45, 0.7, 0.3, n=3)
    C.blob(a, "fur", (0, -0.75, z + 0.45), 0.38, 0.35, 0.34, n=3)
    C.blob(a, "cream", (0, -1.05, z + 0.35), 0.22, 0.1, 0.15, n=2)
    for s in (1, -1):
        cr.spike(a, "fur", (s * 0.22, -0.7, z + 0.75), 0.16, 0.25, tilt_y=s * 15)
        for y in (-0.5, 0.5):
            C.bar(a, "fur", (s * 0.3, y, z + 0.2), (s * 1.15, y * 0.9, z + 0.1), 0.12)
    cr.face(a, (0, -1.08, z + 0.55), 0.32, 0.15, "big", mouth="open")
    C.blob(a, "fur", (0, 1.05, z + 0.65), 0.3, 0.45, 0.6, n=3, matrix=C.tilt((0, 1.05, z + 0.65), "X", -35))
    return cr.done(a, col)


def goose(col):
    a = cr.new("GoldGoose", {"white": "F4F4F4", "beak": "FF9F1C", "straw": "E3C16F", "gold": "F2C230",
                             "goldL": "FFE27A"}, rings=("white", "straw", "gold"))
    a.frame("straw", C.ngon(0.1, 0.1, 1.05, 10), 0.35, 0.0, 0.32, axis="z")
    C.blob(a, "white", (0, 0.25, 0.75), 0.6, 0.85, 0.5, n=4)
    C.blob(a, "white", (0, 0.95, 0.95), 0.3, 0.35, 0.3, n=2)
    for s in (1, -1):
        C.blob(a, "white", (s * 0.55, 0.35, 0.85), 0.12, 0.6, 0.32, n=2)
    C.tube(a, ["white"], [(0, -0.35, 0.95), (0, -0.55, 1.5), (0, -0.4, 1.95)], [0.2, 0.17])
    C.blob(a, "white", (0, -0.5, 2.1), 0.26, 0.3, 0.24, n=3)
    cr.spike(a, "beak", (0, -0.75, 2.05), 0.2, 0.35, tilt_x=95)
    cr.face(a, (0, -0.78, 2.2), 0.28, 0.1, "round", mouth=None)
    C.blob(a, "gold", (0.95, -0.55, 0.45), 0.36, 0.36, 0.45, n=4, z0=0.0)
    a.box("goldL", 0.75, 0.88, -0.86, -0.82, 0.55, 0.72, bevel=0)
    return cr.done(a, col)


def gem_hedgehog(col):
    a = cr.new("GemHedgehog", {"fur": "8A5A3C", "cream": "F1DEC8", "gem": "8EEBFF", "gemP": "FF7BE5", "gemG": "6BFFB0"},
               rings=("fur",))
    C.blob(a, "fur", (0, 0.2, 0.75), 0.85, 0.85, 0.7, n=5, z0=0.0)
    C.blob(a, "cream", (0, -0.55, 0.62), 0.5, 0.25, 0.5, n=3)
    cr.spike(a, "cream", (0, -0.75, 0.62), 0.32, 0.4, tilt_x=95)
    a.box("dark", -0.08, 0.08, -1.18, -1.1, 0.58, 0.68, bevel=0)
    cr.face(a, (0, -0.78, 0.9), 0.38, 0.15, "big", mouth=None)
    keys = ("gem", "gemP", "gemG")
    k = 0
    for row, (z, r, tilt) in enumerate(((1.35, 0.4, -20), (1.1, 0.75, -50), (0.7, 0.88, -75))):
        for i in range(7):
            t = math.radians(20 + i * 23.3)
            x, y = r * math.cos(t) * 1.0, 0.2 + r * math.sin(t)
            cr.spike(a, keys[k % 3], (x, y, z), 0.3, 0.7, tilt_x=tilt * math.sin(t), tilt_y=-tilt * math.cos(t))
            k += 1
    C.gem(a, "gemP", (0.55, -0.85, 0.35), 0.38, turn=20)
    return cr.done(a, col, glow=1.5)


def gold_golem(col):
    a = cr.new("GoldGolem", {"gold": "F2C230", "goldD": "C8901C", "ruby": "E0204A", "neonC": "FFF27A"},
               rings=("gold",))

    def bar_(c, w, d, h):
        x, y, z = c
        a.frustum("gold", (x - w / 2, x + w / 2, y - d / 2, y + d / 2), (x - w / 2 + 0.08, x + w / 2 - 0.08,
                                                                          y - d / 2 + 0.08, y + d / 2 - 0.08), z, z + h)

    for s in (1, -1):
        bar_((s * 0.38, 0.0, 0.0), 0.45, 0.75, 0.4)
        bar_((s * 0.38, 0.0, 0.4), 0.42, 0.7, 0.4)
    for i in range(3):
        for j in range(2):
            bar_((-0.32 + j * 0.64, 0.0, 0.85 + i * 0.38), 0.6, 0.85, 0.36)
    for s in (1, -1):
        bar_((s * 0.95, 0.0, 1.55), 0.5, 0.6, 0.32)
        bar_((s * 1.05, -0.1, 1.15), 0.4, 0.5, 0.36)
        bar_((s * 1.1, -0.2, 0.75), 0.42, 0.5, 0.36)
    bar_((0, -0.05, 2.0), 0.95, 0.8, 0.6)
    C.gem(a, "ruby", (0, -0.48, 1.35), 0.38)
    for s in (1, -1):
        a.box("neonC", s * 0.2 - 0.1, s * 0.2 + 0.1, -0.47, -0.44, 2.3, 2.42, bevel=0)
    a.box("goldD", -0.2, 0.2, -0.47, -0.44, 2.12, 2.17, bevel=0)
    return cr.done(a, col, glow=2.0)


def mimic(col):
    a = cr.new("SafeMimic", {"steel": "3E4656", "steelL": "6F7F99", "gold": "F2C230", "crystal": "E04CFF",
                             "neonY": "FFE23F"}, rings=("steel",))
    cr.legs(a, "steelL", [(0.5, -0.3), (-0.5, -0.3), (0.5, 0.45), (-0.5, 0.45)], 0.15, 0.3)
    a.box("steel", -0.8, 0.8, -0.6, 0.6, 0.3, 1.05)
    a.box("dark", -0.7, 0.7, -0.55, 0.5, 1.05, 1.1, bevel=0)
    a.box("tongue", -0.35, 0.35, -0.75, 0.1, 1.02, 1.12, bevel=0.02)
    a.box("steel", -0.8, 0.8, -0.6, 0.6, 0.0, 0.5, bevel=0.03, matrix=C.tilt((0, 0.6, 1.1), "X", -35) @
          Matrix.Translation((0, 0, 1.1)))
    lid = C.tilt((0, 0.6, 1.1), "X", -35) @ Matrix.Translation((0, 0, 1.1))
    for k in range(6):
        x = -0.6 + k * 0.24
        a.frustum("white", (x - 0.07, x + 0.07, -0.58, -0.48), (x, x, -0.53, -0.53), 1.05, 1.25, bevel=0)
        a.frustum("white", (x - 0.07, x + 0.07, -0.58, -0.48), (x, x, -0.53, -0.53), 0.0, -0.2, bevel=0, matrix=lid)
    a.frame("gold", C.ngon(0, 0.0, 0.85, 8, sy=0.75), 0.1, 0.55, 0.65, axis="z")
    C.disc(a, "gold", 0, 0.68, 0.18, -0.68, -0.6, axis="y")
    for s in (1, -1):  # глаза светятся в глубине пасти
        a.box("neonY", s * 0.3 - 0.1, s * 0.3 + 0.1, 0.25, 0.4, 1.1, 1.3, bevel=0)
    a.frustum("crystal", (-0.35, 0.35, -0.3, 0.3), (0, 0, 0, 0), 0.5, 1.5, bevel=0, matrix=lid)
    return cr.done(a, col, glow=2.0)


CREATURES = [
    ("piggy", "Копилка-робот", "Common", piggy),
    ("coin_slug", "Слизень-монетка", "Common", coin_slug),
    ("wallet_croc", "Кошелёк-крокодил", "Common", wallet_croc),
    ("safe_turtle", "Сейф-черепаха", "Common", safe_turtle),
    ("atm", "Банкомат-обжора", "Rare", atm),
    ("card_squirrel", "Кредитка-летяга", "Rare", card_squirrel),
    ("goose", "Гусь с золотым яйцом", "Epic", goose),
    ("gem_hedgehog", "Алмаз-ёжик", "Epic", gem_hedgehog),
    ("gold_golem", "Золотой слиток-голем", "Legendary", gold_golem),
    ("mimic", "Сейф-мимик с кристаллом", "Legendary", mimic),
]
