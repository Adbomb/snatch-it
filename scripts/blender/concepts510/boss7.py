"""Концепт босса 7 «Бронированный охранник» (Банк): массивный броненосец-инкассатор в тяжёлой броне со щитом-сейфом.

Черновая блочная модель для концепт-листа (не финальная). Стоит на задних лапах: спину и бока закрывает панцирь из
поясов-пластин с золотыми заклёпками, спереди — стальная кираса с жетоном, фуражка охранника с мигалкой, длинная
морда, высокие уши, бронированный хвост. Левая лапа держит круглую дверь сейфа как щит, правая — ключ-дубинку.
Позы: idle, sleep (сидит, опираясь на дверь), attack1 — «Удар дверцей сейфа», attack2 — «Тревога!» (сворачивается
в бронированный шар, мигалка горит). Шире и тяжелее 5 и 6: высота ≈ 7.9, ширина со щитом ≈ 7.5.
"""

import math

import ck as C
from mathutils import Matrix, Vector

EXPOSURE = 0.1
PALETTE = {
    "plate": ("6F7F99", "броня: сталь"),
    "plateL": ("A3B1C7", "светлые пояса, наплечники"),
    "skin": ("E3A58C", "кожа: морда, лапы"),
    "cap": ("22305C", "мундир, фуражка"),
    "gold": ("F2C230", "заклёпки, кокарда, штурвал"),
    "vault": ("B4BFCF", "дверь сейфа"),
    "vaultD": ("56637A", "кромка двери"),
    "red": ("E8384F", "мигалка, жетон"),
    "key": ("D9A520", "ключи"),
    "iris": ("3A2A1A", "глаза"),
}
# (наклон вперёд, отвод в сторону) для левой (+x, щит) и правой (−x, ключ) лап
ARMS = {"idle": [(40, 8), (20, 15)], "sleep": [(60, -10), (60, -10)],
        "attack1": [(95, -25), (150, 10)], "attack2": [(0, 0), (0, 0)]}
DOOR = {"idle": ((2.75, -2.2, 2.55), 1.9), "sleep": ((2.75, -1.9, 1.75), 1.8), "attack1": ((2.0, -3.25, 4.6), 2.0)}


def vault_door(a, c, r):
    """Дверь сейфа лицом к −y: диск, кромка, болты-засовы, штурвал из трёх спиц, наборный диск."""
    x, y, z = c
    C.disc(a, "vault", x, z, r, y - 0.2, y + 0.2, n=16, axis="y")
    a.frame("vaultD", C.ngon(x, z, r + 0.14, 16), 0.26, y - 0.26, y + 0.22, axis="y")
    for i in range(8):
        t = math.radians(i * 45 + 22.5)
        bx, bz = x + (r - 0.32) * math.cos(t), z + (r - 0.32) * math.sin(t)
        C.disc(a, "gold", bx, bz, 0.12, y - 0.32, y - 0.18, n=6, axis="y", bevel=0.005)
    for i in range(3):
        t = math.radians(i * 60 + 15)
        C.bar(a, "gold", (x - 0.85 * r / 1.9 * math.cos(t), y - 0.36, z - 0.85 * r / 1.9 * math.sin(t)),
              (x + 0.85 * r / 1.9 * math.cos(t), y - 0.36, z + 0.85 * r / 1.9 * math.sin(t)), 0.15, 0.15)
    C.disc(a, "gold", x, z, 0.3, y - 0.5, y - 0.22, axis="y")
    C.disc(a, "vaultD", x - 0.95 * r / 1.9, z + 0.95 * r / 1.9, 0.3, y - 0.4, y - 0.2, axis="y")
    C.disc(a, "white", x - 0.95 * r / 1.9, z + 0.95 * r / 1.9, 0.12, y - 0.45, y - 0.38, n=6, axis="y", bevel=0)


def armor_ball(a, collection):
    """«Тревога!»: свернулся в шар — пояса панциря дугой, уши и фуражка сверху, мигалка горит."""
    cz = 3.3
    C.blob(a, "plate", (0, 0, cz), 2.7, 2.6, 2.7, n=7)
    for k in range(9):
        a.transform = C.tilt((0, 0, cz), "X", -100 + k * 25)
        key = "plate" if k % 2 else "plateL"
        a.prism(key, *C.octa((0, 0), 5.3, 1.05, cz + 2.55, cz + 3.0, cut=0.6))
        for x in (-2.0, -1.0, 0.0, 1.0, 2.0):
            C.gem(a, "gold", (x, 0, cz + 3.02), 0.22)
    a.transform = None
    for s in (1, -1):  # уши и лапы торчат из шара
        a.frustum("skin", (s * 0.7 - 0.22, s * 0.7 + 0.22, -1.6, -1.35), (s * 0.85, s * 0.85, -1.5, -1.5), cz + 2.6,
                  cz + 3.7, bevel=0.004)
        C.blob(a, "skin", (s * 1.3, -2.55, 0.55), 0.5, 0.45, 0.4, n=3)
    a.prism("cap", *C.octa((0, -1.0), 2.1, 1.8, cz + 2.9, cz + 3.4, cut=0.6))
    a.box("dark", -0.9, 0.9, -2.25, -1.4, cz + 2.88, cz + 2.98)
    C.gem(a, "gold", (0, -1.95, cz + 3.2), 0.35)
    C.disc(a, "neonRed", 0, -1.0, 0.42, cz + 3.4, cz + 4.0)
    obj = C.finish(a, collection, glow=4.0)
    f = C.new_art("Boss7fx")
    f.paint("neonRed", "FF3048")
    f.paint("neonGold", "FFD54A")
    for k in range(3):
        f.frame("neonRed", C.ngon(0, 0, 3.4 + k * 0.9, 16), 0.1, 0.02, 0.1, axis="z")
    for k in range(4):  # искры качения
        C.bar(f, "neonGold", (-1.5 + k, 2.8, 0.3 + 0.2 * k), (-1.8 + k, 3.9, 0.15 + 0.2 * k), 0.08, 0.08)
    return [obj, C.finish(f, collection, glow=2.5)]


def build(collection, pose="idle"):
    a = C.new_art("Boss7", ring_z0=3.0)
    for k, (code, _) in PALETTE.items():
        a.paint(k, code, rings=k in ("plate", "plateL", "vault", "cap"))
    for k, code in (("white", "FFFFFF"), ("dark", "14161F"), ("glint", "FFFFFF"), ("pink", "E98B8B")):
        a.paint(k, code)
    a.paint("neonRed", "FF3048")
    if pose == "attack2":
        return armor_ball(a, collection)
    sit = pose == "sleep"
    dz = -0.7 if sit else 0.0

    # ноги в стальных сапогах; сидя — подошвами к зрителю
    for s in (1, -1):
        x = s * 1.25
        if sit:
            C.blob(a, "skin", (x, -1.0, 0.65), 0.7, 1.0, 0.6, n=4)
            a.box("plate", x - 0.75, x + 0.75, -2.35, -1.75, 0.0, 1.15)
            a.box("dark", x - 0.55, x + 0.55, -2.4, -2.3, 0.15, 0.95, bevel=0.01)
        else:
            C.blob(a, "skin", (x, 0.0, 1.05), 0.72, 0.75, 0.8, n=4)
            a.box("plate", x - 0.85, x + 0.85, -1.05, 0.75, 0.0, 0.5)
            a.box("plateL", x - 0.9, x + 0.9, -1.1, 0.8, 0.5, 0.72)
            for k in (-0.35, 0.35):
                a.box("dark", x + k - 0.12, x + k + 0.12, -1.15, -1.0, 0.05, 0.3, bevel=0.01)
    # бронированный хвост
    C.tube(a, ["plate", "plateL"], [(0, 1.4, 1.9 + dz), (0, 2.5, 1.0 + dz), (0.5, 3.2, 0.35), (1.3, 3.5, 0.3)],
           [0.55, 0.45, 0.32], n=8)

    # туловище: мундир, панцирь поясами сзади и с боков, кираса спереди
    C.blob(a, "cap", (0, 0.1, 3.15 + dz), 2.05, 1.55, 1.95, n=7)
    for k in range(6):
        z0 = 1.75 + k * 0.66 + dz
        key = "plate" if k % 2 == 0 else "plateL"
        a.prism(key, *C.octa((0, 0.75), 4.7 - abs(k - 2.5) * 0.35, 2.3, z0, z0 + 0.64, cut=0.9))
        for x in (-1.6, -0.55, 0.55, 1.6):
            C.gem(a, "gold", (x, 1.92, z0 + 0.32), 0.2)
    a.prism("plate", *C.octa((0, -1.35), 3.1, 0.5, 2.45 + dz, 4.75 + dz, cut=0.6))
    a.prism("plateL", *C.octa((0, -1.55), 2.5, 0.2, 2.7 + dz, 4.5 + dz, cut=0.5))
    for x in (-1.3, 1.3):
        for z in (2.7, 4.5):
            C.gem(a, "gold", (x, -1.62, z + dz), 0.24)
    C.disc(a, "gold", -0.7, 4.0 + dz, 0.42, -1.8, -1.62, n=6, axis="y")  # жетон
    C.disc(a, "red", -0.7, 4.0 + dz, 0.2, -1.86, -1.78, n=6, axis="y", bevel=0)
    a.prism("gold", *C.octa((0, -0.1), 4.4, 3.3, 2.0 + dz, 2.35 + dz, cut=0.8))  # ремень
    a.box("gold", -0.4, 0.4, -1.85, -1.7, 1.9 + dz, 2.45 + dz)
    a.frame("key", C.ngon(1.65, 1.85 + dz, 0.28, 8), 0.07, -1.84, -1.74, axis="y")  # связка ключей
    for i in range(3):
        C.bar(a, "key", (1.5 + i * 0.15, -1.8, 1.6 + dz), (1.45 + i * 0.17, -1.82, 1.0 + dz - (i % 2) * 0.2), 0.12, 0.06)
    # наплечники с золотой бахромой, стальной ворот
    for s in (1, -1):
        C.blob(a, "plateL", (s * 2.35, 0.25, 5.25 + dz), 1.15, 1.1, 0.7, n=4)
        for k in range(6):
            fx = s * (1.55 + k * 0.3)
            a.box("gold", fx - 0.07, fx + 0.07, -0.85, -0.7, 4.35 + dz, 4.75 + dz, bevel=0.005)
        C.gem(a, "gold", (s * 2.35, -0.6, 5.55 + dz), 0.3)
    a.frame("plate", C.ngon(0, -0.1, 1.3, 8), 0.42, 5.05 + dz, 5.55 + dz, axis="z")

    # голова броненосца: длинная морда вниз-вперёд, высокие уши, фуражка с мигалкой
    hz = 6.3 + dz
    head = C.tilt((0, -0.2, hz - 0.7), "X", 18 if sit else 0)
    a.transform = head
    C.blob(a, "skin", (0, -0.2, hz), 1.0, 0.95, 0.9, n=5)
    a.frustum("skin", (-0.55, 0.55, -0.45, 0.45), (-0.2, 0.2, -0.17, 0.17), 0.0, 1.5,
              matrix=Matrix.Translation((0, -0.85, hz - 0.3)) @ Matrix.Rotation(math.radians(100), 4, "X"))
    a.box("plate", -0.4, 0.4, -1.75, -0.95, hz - 0.03, hz + 0.1, bevel=0.01)  # щиток на морде
    C.disc(a, "dark", 0, hz - 0.56, 0.2, -2.38, -2.25, axis="y")
    for s in (1, -1):
        a.frustum("skin", (-0.27, 0.27, -0.13, 0.13), (-0.1, 0.1, -0.06, 0.06), 0.0, 1.35,
                  matrix=Matrix.Translation((s * 0.82, -0.05, hz + 0.45)) @ Matrix.Rotation(math.radians(-s * 22), 4, "Y"))
        a.box("pink", -0.13, 0.13, -0.17, -0.12, 0.15, 1.0, bevel=0,
              matrix=Matrix.Translation((s * 0.82, -0.05, hz + 0.45)) @ Matrix.Rotation(math.radians(-s * 22), 4, "Y"))
        if sit:
            C.closed_eye(a, (s * 0.55, -1.02, hz + 0.18), 0.32, happy=False)
        else:
            C.eye(a, (s * 0.55, -1.0, hz + 0.18), 0.36, 0.36, look=(-s * 0.2, -0.1), lid=0.35, lid_key="skin",
                  iris="iris")
            C.bar(a, "dark", (s * 0.25, -1.12, hz + 0.48), (s * 0.85, -1.12, hz + 0.4), 0.1, 0.08, bevel=0)
    a.prism("cap", *C.octa((0, -0.3), 2.15, 2.05, hz + 0.62, hz + 1.12, cut=0.6))
    a.prism("cap", *C.octa((0, -0.35), 2.55, 2.4, hz + 1.12, hz + 1.42, cut=0.7))
    a.box("dark", -1.0, 1.0, -1.85, -0.9, hz + 0.6, hz + 0.72)  # козырёк
    a.box("gold", -1.0, 1.0, -1.37, -1.3, hz + 0.75, hz + 0.9, bevel=0.005)  # шнур
    C.gem(a, "gold", (0, -1.55, hz + 1.12), 0.42)
    C.disc(a, "red", 0, -0.35, 0.3, hz + 1.42, hz + 1.75)  # мигалка (выключена)
    a.transform = None

    # лапы: левая (+x) держит дверь сейфа, правая (−x) — ключ-дубинку
    for i, s in enumerate((1, -1)):
        pitch, out = ARMS[pose][i]
        root = Vector((s * 2.35, 0.0, 4.85 + dz))
        a.transform = C.tilt(root, "Y", -s * out) @ C.tilt(root, "X", -pitch)
        elbow, wrist = root - Vector((0, 0, 1.4)), root - Vector((0, 0, 2.5))
        C.tube(a, ["plate", "plateL"], [root, elbow, wrist], [0.58, 0.52], n=8)
        a.frame("gold", C.ngon(wrist.x, wrist.y, 0.6, 8), 0.14, wrist.z, wrist.z + 0.22, axis="z")
        C.blob(a, "skin", (wrist.x, wrist.y, wrist.z - 0.35), 0.55, 0.55, 0.42, n=3)
        if s == -1:
            C.bar(a, "key", (wrist.x, wrist.y - 0.25, wrist.z - 0.1), (wrist.x, wrist.y - 0.25, wrist.z - 2.4), 0.26)
            for k in (0, 1):  # бородка ключа
                a.box("key", wrist.x - 0.13, wrist.x + 0.13, wrist.y - 0.38, wrist.y - 0.12, wrist.z - 2.2 + k * 0.45,
                      wrist.z - 1.95 + k * 0.45, bevel=0.01, matrix=Matrix.Translation((-0.35, 0, 0)))
            a.frame("key", C.ngon(wrist.x, wrist.z + 0.45, 0.5, 8), 0.15, wrist.y - 0.4, wrist.y - 0.1, axis="y")
        a.transform = None
    c, r = DOOR[pose]
    vault_door(a, c, r)
    obj = C.finish(a, collection)
    fx = []
    if pose == "attack1":
        f = C.new_art("Boss7fx")
        f.paint("neonGold", "FFD54A")
        for k in range(3):
            f.frame("neonGold", C.ngon(2.0, 4.6, 2.5 + k * 0.6, 16), 0.1, -3.9 - k * 0.6, -3.8 - k * 0.6, axis="y")
        fx.append(C.finish(f, collection, glow=3.0))
    return [obj] + fx
