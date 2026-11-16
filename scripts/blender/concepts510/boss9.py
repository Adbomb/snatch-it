"""Концепт босса 9 «Пришелец-генерал» (Космопорт): трёхглазый генерал в космической броне на парящем командном троне.

Черновая блочная модель для концепт-листа (не финальная). Большая голова-купол, три глаза в ряд (средний крупнее),
генеральская фуражка с золотой кокардой, белые угловатые наплечники, медали; трон с высокой спинкой-плавником,
пультами на подлокотниках, антигравитационным кольцом и соплами. Позы: idle — парит, указывает вперёд;
sleep — трон опустился, фуражка съехала на глаза; attack1 — «Орбитальный удар» (рука вверх, прицел на земле и луч
с неба); attack2 — «Тройной луч» (лучи из трёх глаз сходятся впереди). Высота ≈ 9 (трон парит на 1.1).
"""

import math

import ck as C
from mathutils import Matrix, Vector

EXPOSURE = 0.2
PALETTE = {
    "skin": ("8EE06B", "кожа: салатовая"),
    "skinS": ("5DB35A", "тень кожи, плавники"),
    "armor": ("5B3FA0", "броня: фиолетовая"),
    "armorL": ("E8EAF4", "белые пластины"),
    "cap": ("2A2350", "фуражка, сиденье"),
    "gold": ("F2C230", "кокарда, канты, медали"),
    "throne": ("C9D2E3", "трон: серебро"),
    "throneD": ("4A5470", "низ трона, сопла"),
    "iris": ("7A2BD8", "глаза: фиолетовые"),
    "medal": ("E8384F", "медаль"),
}
ARMS = {"idle": [(35, 6), (88, -12)], "sleep": [(30, 6), (30, 6)],
        "attack1": [(35, 6), (172, -8)], "attack2": [(35, 6), (35, 6)]}


def throne(a, b, sit):
    """Командный трон: летающая платформа, сиденье, спинка-плавник, подлокотники с пультами."""
    a.prism("throneD", *C.octa((0, 0.3), 3.3, 2.9, b + 0.3, b + 1.0, cut=0.9))
    a.frustum("throneD", (-1.2, 1.2, -0.75, 1.35), (-0.7, 0.7, -0.25, 0.85), b + 0.3, b - 0.05 if sit else b + 0.0)
    a.frame("neonCyan", C.ngon(0, 0.3, 2.05, 12), 0.16, b + 0.5, b + 0.66, axis="z")
    if not sit:
        for x, y in ((-1.0, -0.4), (1.0, -0.4), (-1.0, 1.0), (1.0, 1.0)):
            a.frustum("neonCyan", (x - 0.22, x + 0.22, y - 0.22, y + 0.22), (x, x, y, y), b + 0.0, b - 0.75, bevel=0)
    a.prism("throne", *C.octa((0, 0.3), 3.9, 3.0, b + 1.0, b + 1.5, cut=0.9))
    a.prism("cap", *C.octa((0, 0.15), 2.7, 2.3, b + 1.5, b + 1.72, cut=0.6))
    back = [(-1.65, b + 1.5), (1.65, b + 1.5), (1.85, b + 4.4), (0.95, b + 6.1), (0.0, b + 6.9), (-0.95, b + 6.1),
            (-1.85, b + 4.4)]
    a.extrude("throne", back, 1.45, 1.85, axis="y")
    inner = [(u * 0.78, b + 1.75 + (w - b - 1.5) * 0.8) for u, w in back]
    a.extrude("armor", inner, 1.33, 1.45, axis="y")
    a.extrude("armor", inner, 1.85, 1.97, axis="y")  # спинка сзади: фиолетовая вставка, эмблема, двигатели
    a.prism("neonCyan", C.ngon(0, b + 4.6, 0.55, 3, phase=math.pi / 2), 1.97, 2.03, axis="y", bevel=0)
    for s in (1, -1):
        C.tube(a, ["throneD"], [(s * 1.05, 1.6, b + 1.25), (s * 1.05, 2.7, b + 1.25)], 0.42, n=8)
        a.prism("neonCyan", C.ngon(s * 1.05, b + 1.25, 0.3, 8), 2.7, 2.78, axis="y", bevel=0)
    a.prism("neonPink", C.ngon(0, b + 5.4, 0.42, 6, phase=0), 1.27, 1.34, axis="y", bevel=0)
    for s in (1, -1):
        C.bar(a, "neonCyan", (s * 1.7, 1.4, b + 1.8), (s * 1.88, 1.4, b + 4.35), 0.08, 0.08, bevel=0)
        C.bar(a, "neonCyan", (s * 1.88, 1.4, b + 4.45), (s * 1.0, 1.4, b + 6.1), 0.08, 0.08, bevel=0)
        # подлокотник с пультом
        a.box("throne", s * 1.55, s * 2.15, -1.1, 1.3, b + 1.5, b + 2.25)
        a.box("cap", s * 1.6, s * 2.1, -1.05, -0.1, b + 2.25, b + 2.35, bevel=0.005)
        for k, key in enumerate(("neonCyan", "neonPink", "neonCyan")):
            a.box(key, s * 1.7 + k * s * 0.12 - 0.04, s * 1.7 + k * s * 0.12 + 0.04, -0.9, -0.82, b + 2.35, b + 2.4,
                  bevel=0)
        # боковой плавник
        a.extrude("armor", [(s * 2.15, b + 1.0), (s * 2.9, b + 0.6), (s * 2.6, b + 2.0), (s * 2.15, b + 2.25)],
                  -0.3, 0.6, axis="y")
    a.box("throneD", -1.1, 1.1, -2.35, -1.25, b + 0.62, b + 0.88)  # подножка


def build(collection, pose="idle"):
    a = C.new_art("Boss9", ring_z0=3.0)
    for k, (code, _) in PALETTE.items():
        a.paint(k, code, rings=k in ("skin", "armor", "throne"))
    for k, code in (("white", "FFFFFF"), ("dark", "120E1E"), ("glint", "FFFFFF")):
        a.paint(k, code)
    a.paint("neonCyan", "3FF0FF")
    a.paint("neonPink", "FF4FD8")
    sit = pose == "sleep"
    b = 0.15 if sit else 1.1
    throne(a, b, sit)

    # ноги: бёдра вперёд, голени вниз, белые сапоги на подножке
    for s in (1, -1):
        x = s * 0.65
        C.tube(a, ["armor"], [(x, 0.3, b + 2.05), (x, -1.35, b + 2.05)], 0.42, n=8)
        C.tube(a, ["armor"], [(x, -1.4, b + 2.05), (x, -1.65, b + 1.15)], 0.36, n=8)
        a.box("armorL", x - 0.38, x + 0.38, -2.15, -1.3, b + 0.88, b + 1.3)
        a.box("gold", x - 0.4, x + 0.4, -1.75, -1.55, b + 1.3, b + 1.45, bevel=0.005)
    # туловище: броня, белая кираса, медали, золотой пояс, высокий ворот
    C.blob(a, "armor", (0, 0.35, b + 3.15), 1.25, 0.95, 1.3, n=6)
    a.prism("armorL", *C.octa((0, -0.45), 1.9, 0.35, b + 2.65, b + 4.05, cut=0.5))
    a.prism("gold", *C.octa((0, 0.3), 2.5, 2.0, b + 2.15, b + 2.4, cut=0.6))
    for k, key in enumerate(("gold", "medal", "neonCyan", "gold")):
        x = 0.85 - (k % 2) * 0.32
        z = b + 3.7 - (k // 2) * 0.38
        a.box("gold", x - 0.12, x + 0.12, -0.7, -0.62, z, z + 0.08, bevel=0)
        C.disc(a, key, x, z - 0.15, 0.13, -0.72, -0.62, n=6, axis="y", bevel=0.003)
    a.frame("armorL", C.ngon(0, 0.25, 0.75, 8), 0.3, b + 4.1, b + 4.65, axis="z")
    for s in (1, -1):  # угловатые наплечники с плавниками
        a.prism("armorL", *C.octa((s * 1.4, 0.3), 1.35, 1.45, b + 3.75, b + 4.35, cut=0.25))
        a.box("gold", s * 0.85, s * 1.95, -0.48, -0.38, b + 3.72, b + 3.84, bevel=0.005)
        a.extrude("armor", [(s * 1.4, b + 4.35), (s * 2.25, b + 4.35), (s * 2.0, b + 5.0)], 0.0, 0.5, axis="y")
        a.box("neonCyan", s * 1.75 - 0.08, s * 1.75 + 0.08, -0.47, -0.4, b + 4.0, b + 4.16, bevel=0)
    C.tube(a, ["skin"], [(0, 0.2, b + 4.3), (0, 0.0, b + 5.05)], 0.34, n=8)

    # голова: купол, узкий подбородок, три глаза, плавники-уши, фуражка
    hz = b + 5.95
    head = C.tilt((0, -0.1, hz - 0.9), "X", 22 if sit else 0)
    a.transform = head
    C.blob(a, "skin", (0, -0.1, hz + 0.1), 1.4, 1.2, 1.15, n=7)
    C.blob(a, "skin", (0, -0.35, hz - 0.8), 0.78, 0.68, 0.45, n=3)
    for s in (1, -1):
        a.frustum("skinS", (-0.28, 0.28, -0.12, 0.12), (0, 0, 0, 0), 0.0, 0.8,
                  matrix=Matrix.Translation((s * 1.25, -0.1, hz - 0.05)) @ Matrix.Rotation(math.radians(-s * 70), 4, "Y"))
    eyes = ((0.0, -1.33, hz + 0.08, 0.56, 0.52), (0.72, -1.15, hz - 0.02, 0.42, 0.4), (-0.72, -1.15, hz - 0.02, 0.42, 0.4))
    for x, y, z, w, h in eyes:
        if sit:
            C.closed_eye(a, (x, y - 0.02, z), w * 0.9, happy=False)
        else:
            C.eye(a, (x, y, z), w, h, look=(0, -0.15), lid=0.3, lid_key="skinS", iris="iris")
    if not sit:
        for x, y, z, w, _ in eyes:
            C.bar(a, "dark", (x - w * 0.55, y - 0.1, z + 0.38 - 0.06 * (x > 0) + 0.06 * (x < 0)),
                  (x + w * 0.55, y - 0.1, z + 0.38 + 0.06 * (x > 0) - 0.06 * (x < 0)), 0.08, 0.06, bevel=0)
    a.box("dark", -0.3, 0.3, -1.02, -0.95, hz - 0.72, hz - 0.64, bevel=0)  # рот
    cap_tilt = C.tilt((0, -0.15, hz + 0.9), "X", 14 if sit else -4)
    a.transform = head @ cap_tilt
    a.prism("cap", *C.octa((0, -0.15), 2.3, 2.15, hz + 0.88, hz + 1.38, cut=0.6))
    a.prism("cap", *C.octa((0, -0.22), 2.75, 2.55, hz + 1.38, hz + 1.68, cut=0.7))
    a.box("dark", -1.0, 1.0, -1.95, -0.95, hz + 0.84, hz + 0.96)
    a.box("gold", -1.05, 1.05, -1.33, -1.25, hz + 0.98, hz + 1.12, bevel=0.005)
    C.disc(a, "gold", 0, hz + 1.3, 0.38, -1.5, -1.3, n=6, axis="y")
    a.prism("neonCyan", C.ngon(0, hz + 1.3, 0.2, 3, phase=math.pi / 2), -1.56, -1.48, axis="y", bevel=0)
    a.transform = None

    # руки: броня до локтя, салатовые предплечья, золотые манжеты, три пальца
    for i, s in enumerate((1, -1)):
        pitch, out = ARMS[pose][i]
        root = Vector((s * 1.5, 0.3, b + 3.95))
        a.transform = C.tilt(root, "Y", -s * out) @ C.tilt(root, "X", -pitch)
        elbow, wrist = root - Vector((0, 0, 1.15)), root - Vector((0, 0, 2.1))
        C.tube(a, ["armor", "skin"], [root, elbow, wrist], [0.36, 0.28], n=8)
        a.frame("gold", C.ngon(wrist.x, wrist.y, 0.34, 8), 0.1, wrist.z, wrist.z + 0.18, axis="z")
        C.blob(a, "skin", (wrist.x, wrist.y, wrist.z - 0.25), 0.3, 0.26, 0.26, n=3)
        for k in (-0.15, 0.0, 0.15):
            C.bar(a, "skin", (wrist.x + k, wrist.y - 0.05, wrist.z - 0.4), (wrist.x + k * 1.3, wrist.y - 0.05,
                                                                          wrist.z - 0.85), 0.1)
        a.transform = None
    obj = C.finish(a, collection, glow=4.0)

    fx = []
    if pose == "attack1":
        f = C.new_art("Boss9fx")
        f.paint("neonRed", "FF3048")
        f.paint("neonCyan", "3FF0FF")
        for r in (1.1, 2.0):
            f.frame("neonRed", C.ngon(2.6, -4.2, r, 16), 0.12, 0.02, 0.1, axis="z")
        C.bar(f, "neonRed", (0.2, -4.2, 0.06), (5.0, -4.2, 0.06), 0.1, 0.06, bevel=0)
        C.bar(f, "neonRed", (2.6, -6.6, 0.06), (2.6, -1.8, 0.06), 0.1, 0.06, bevel=0)
        f.prism("neonCyan", C.ngon(2.6, -4.2, 0.35, 8), 0.1, 9.5, bevel=0)
        fx.append(C.finish(f, collection, glow=3.5))
    if pose == "attack2":
        f = C.new_art("Boss9fx")
        f.paint("neonPink", "FF4FD8")
        target = Vector((0, -5.5, 0.8))
        for x, y, z, w, h in eyes:
            C.bar(f, "neonPink", (x, y - 0.2, z), target, 0.14, 0.14, bevel=0)
        C.ball(f, "neonPink", target, 0.55)
        fx.append(C.finish(f, collection, glow=4.0))
    return [obj] + fx
