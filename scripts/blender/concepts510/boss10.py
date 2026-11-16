"""Концепт босса 10 «Король-дракон» (Замок): финальный противник — красно-золотой дракон в короне и королевской мантии.

Черновая блочная модель для концепт-листа (не финальная). Стоит на задних лапах: кремовые пластины живота, золотые
наплечники и ворот с рубином, мантия с горностаевым воротником, огромные крылья (перепонка тёмно-красная, кости
золотые когти), рога цвета слоновой кости, корона с тремя камнями, скипетр с рубиновой державой, хвост с золотым
наконечником. Позы: idle — крылья полураскрыты; sleep — свернулся на горе золота, дым из ноздрей;
attack1 — «Королевское пламя» (огонь вперёд); attack2 — «Взмах крыльев» (крылья вверх, золотой вихрь монет).
Высота ≈ 10.5, размах крыльев ≈ 14 — самый крупный силуэт ряда.
"""

import math

import ck as C
from mathutils import Matrix, Vector

EXPOSURE = 0.15
PALETTE = {
    "scale": ("C8283A", "чешуя: королевский красный"),
    "scaleD": ("8A1626", "тень чешуи, кости крыльев"),
    "wing": ("6E1630", "перепонка крыльев"),
    "belly": ("F3D9A0", "пластины живота"),
    "gold": ("F2C230", "корона, броня, скипетр"),
    "goldD": ("C8901C", "тёмное золото"),
    "mantle": ("5A1E6E", "мантия: пурпур"),
    "ermine": ("F6F4EE", "горностай"),
    "ivory": ("EFE6CF", "рога, когти, клыки"),
    "eyeY": ("FFD23F", "глаза"),
    "ruby": ("E0204A", "рубины"),
    "sapphire": ("2F6BFF", "сапфир"),
    "emerald": ("22C77A", "изумруд"),
}
# крылья: (отвод назад, подъём) в градусах
WINGS = {"idle": (28, 2), "attack1": (38, 12), "attack2": (6, 26), "sleep": (78, -18)}
ARMS = {"idle": [(25, 14), (40, 8)], "attack1": [(55, 30), (40, 8)], "attack2": [(120, 40), (120, 40)],
        "sleep": [(50, -10), (50, -10)]}
# крыло в своей плоскости: (наружу от корня, высота от корня)
WING_PTS = [(0.0, 0.0), (2.2, 2.3), (4.1, 3.5), (6.7, 1.3), (5.1, 0.95), (6.1, -1.1), (4.3, -0.6), (4.5, -2.6),
            (2.7, -1.6), (0.7, -2.2)]
WING_BONES = [(0, 1), (1, 2), (2, 3), (2, 5), (2, 7)]


def wing(a, s, root, sweep, lift):
    m = Matrix.Translation(root) @ Matrix.Rotation(math.radians(s * sweep), 4, "Z") @ Matrix.Rotation(
        math.radians(-s * lift), 4, "Y")
    pts = [(s * u, w) for u, w in WING_PTS]
    a.extrude("wing", pts, -0.06, 0.06, axis="y", matrix=m)
    for i, j in WING_BONES:
        p0, p1 = Vector((pts[i][0], -0.14, pts[i][1])), Vector((pts[j][0], -0.14, pts[j][1]))
        a.transform = m
        C.bar(a, "scaleD", p0, p1, 0.32 if i == 0 or (i, j) == (1, 2) else 0.18, bevel=0.01)
        a.transform = None
    w = pts[2]
    a.frustum("gold", (w[0] - 0.18, w[0] + 0.18, -0.32, 0.04), (w[0], w[0], -0.14, -0.14), w[1], w[1] + 0.75,
              bevel=0.004, matrix=m)
    a.frustum("gold", (pts[1][0] - 0.14, pts[1][0] + 0.14, -0.28, 0.0), (pts[1][0], pts[1][0], -0.14, -0.14),
              pts[1][1], pts[1][1] + 0.5, bevel=0.004, matrix=m)


def hoard(a):
    """Гора золота под спящим драконом."""
    C.blob(a, "goldD", (0, 0.2, 0.0), 4.2, 3.6, 1.2, n=4, z0=0.0)
    for i in range(26):
        t = math.radians(i * 137.5)
        r = 1.0 + 2.9 * ((i * 37) % 26) / 26
        x, y = r * math.cos(t), 0.2 + 0.85 * r * math.sin(t)
        z = 1.15 * max(0.0, 1 - (r / 4.3) ** 2) + 0.05
        C.disc(a, "gold", x, y, 0.32, z, z + 0.1, n=8, bevel=0.01,
               matrix=C.tilt((x, y, z), "X", (i * 23) % 40 - 20))
    for x, y, key in ((-2.6, -1.6, "ruby"), (2.4, -1.2, "sapphire"), (-1.2, -2.6, "emerald"), (3.0, 0.8, "ruby")):
        C.gem(a, key, (x, y, 0.7), 0.5, turn=x * 20)


def build(collection, pose="idle"):
    a = C.new_art("Boss10", ring_z0=3.0)
    for k, (code, _) in PALETTE.items():
        a.paint(k, code, rings=k in ("scale", "belly", "mantle", "wing"))
    for k, code in (("white", "FFFFFF"), ("dark", "150A10"), ("glint", "FFFFFF"), ("smoke", "B9B4BE")):
        a.paint(k, code)
    sit = pose == "sleep"
    dz = -1.4 if sit else 0.0
    if sit:
        hoard(a)
    base = 1.0 if sit else 0.0  # сидя — на горе золота

    # ноги
    for s in (1, -1):
        x = s * 1.5
        if sit:
            C.blob(a, "scale", (x, -1.0, base + 0.8), 0.95, 1.4, 0.8, n=4)
            C.blob(a, "scale", (x, -2.2, base + 0.35), 0.7, 0.6, 0.35, n=3)
            for k in (-0.3, 0.0, 0.3):
                a.frustum("ivory", (x + k - 0.1, x + k + 0.1, -2.7, -2.5), (x + k, x + k, -2.95, -2.95), base + 0.3,
                          base + 0.05, bevel=0)
        else:
            C.blob(a, "scale", (x, 0.3, 1.95), 1.05, 1.15, 1.2, n=5)
            C.blob(a, "scale", (x, -0.1, 0.8), 0.72, 0.78, 0.8, n=4)
            C.blob(a, "scale", (x, -0.7, 0.28), 0.8, 1.05, 0.28, n=3, z0=0.0)
            for k in (-0.38, 0.0, 0.38):
                a.frustum("ivory", (x + k - 0.11, x + k + 0.11, -1.72, -1.5), (x + k, x + k, -1.95, -1.95), 0.35, 0.05,
                          bevel=0)
            a.frame("gold", C.ngon(x, -0.1, 0.82, 8), 0.16, 1.2, 1.45, axis="z")  # золотые наколенные кольца
    # хвост с шипами и золотым наконечником
    tail = [(0, 1.5, 2.0 + dz + base), (0, 3.1, 1.0 + base * 0.4), (1.3, 4.3, 0.6 + base * 0.3), (2.9, 4.6, 0.5 + base * 0.3)]
    if sit:
        tail = [(1.6, 1.4, base + 0.9), (3.2, 0.2, base + 0.5), (3.0, -2.0, base + 0.35), (1.4, -3.1, base + 0.3)]
    C.tube(a, ["scale"], tail, [0.85, 0.65, 0.45], n=8)
    for p0, p1 in zip(tail, tail[1:]):
        mid = (Vector(p0) + Vector(p1)) / 2
        a.frustum("gold", (mid.x - 0.16, mid.x + 0.16, mid.y - 0.16, mid.y + 0.16), (mid.x, mid.x, mid.y, mid.y),
                  mid.z + 0.4, mid.z + 1.0, bevel=0.004)
    end = Vector(tail[-1])
    a.prism("gold", [(end.x - 0.1, end.y - 0.6), (end.x + 0.8, end.y), (end.x - 0.1, end.y + 0.6), (end.x - 0.5, end.y)],
            end.z - 0.15, end.z + 0.15)

    # мантия за спиной: пурпур, горностаевая кайма, золотая застёжка
    mz = dz + base
    a.extrude("mantle", [(-1.9, mz + 6.1), (1.9, mz + 6.1), (2.9, mz + 0.35), (-2.9, mz + 0.35)], 2.0, 2.28, axis="y")
    a.box("ermine", -2.95, 2.95, 1.95, 2.34, mz + 0.25, mz + 0.75)
    for k in range(7):
        a.box("dark", -2.4 + k * 0.8 - 0.07, -2.4 + k * 0.8 + 0.07, 2.33, 2.37, mz + 0.4, mz + 0.62, bevel=0)
    # туловище: красная бочка, кремовый живот с поперечными пластинами
    C.blob(a, "scale", (0, 0.3, 4.3 + dz + base), 2.05, 1.7, 2.3, n=8)
    C.blob(a, "belly", (0, -0.45, 4.1 + dz + base), 1.4, 1.05, 1.75, n=6)
    for k in range(6):
        z = 2.75 + k * 0.5
        f = max(math.sqrt(max(1 - ((z - 4.1) / 1.75) ** 2, 0.0)), 0.42)
        y = -0.45 - 1.05 * f - 0.02
        C.bar(a, "goldD", (-1.25 * f, y, z + dz + base), (1.25 * f, y, z + dz + base), 0.07, 0.05, bevel=0)
    # горностаевый воротник, золотой ворот с рубином, наплечники с шипами
    cz = 6.05 + dz + base
    C.blob(a, "ermine", (0, 0.55, cz), 2.35, 1.55, 0.45, n=3)
    for i in range(9):
        t = math.radians(-160 + i * 40)
        a.box("dark", 2.1 * math.cos(t) - 0.07, 2.1 * math.cos(t) + 0.07, 0.55 + 1.35 * math.sin(t) - 0.07,
              0.55 + 1.35 * math.sin(t) + 0.07, cz + 0.3, cz + 0.48, bevel=0)
    a.frame("gold", C.ngon(0, -0.05, 1.0, 8), 0.28, cz + 0.2, cz + 0.65, axis="z")
    C.gem(a, "ruby", (0, -1.12, cz + 0.42), 0.5)
    for s in (1, -1):
        C.blob(a, "gold", (s * 2.3, 0.15, cz - 0.3), 1.0, 1.0, 0.6, n=4)
        for k, h in enumerate((0.9, 0.6, 0.45)):
            x = s * (2.0 + k * 0.45)
            a.frustum("gold", (x - 0.16, x + 0.16, 0.0, 0.32), (x, x, 0.16, 0.16), cz + 0.15, cz + 0.15 + h, bevel=0.004)

    # шея и голова
    hz = 8.4 + dz + base
    C.tube(a, ["scale"], [(0, 0.25, cz + 0.2), (0, -0.25, hz - 0.5)], 0.85, n=8)
    for k in range(3):
        z = cz + 0.75 + k * 0.6
        a.frustum("gold", (-0.13, 0.13, 0.75 - k * 0.15, 1.0 - k * 0.15), (0, 0, 1.25 - k * 0.15, 1.25 - k * 0.15),
                  z, z + 0.45, bevel=0.004)
    head = C.tilt((0, -0.3, hz - 0.8), "X", 24 if sit else 0)
    a.transform = head
    C.blob(a, "scale", (0, -0.35, hz), 1.15, 1.1, 0.95, n=5)
    a.frustum("scale", (-0.75, 0.75, -0.5, 0.42), (-0.48, 0.48, -0.28, 0.2), 0.0, 1.65,
              matrix=Matrix.Translation((0, -1.05, hz - 0.3)) @ Matrix.Rotation(math.radians(94), 4, "X"))
    a.box("belly", -0.62, 0.62, -2.6, -1.15, hz - 0.88, hz - 0.62)  # нижняя челюсть
    for s in (1, -1):
        C.disc(a, "dark", s * 0.25, hz - 0.28, 0.1, -2.78, -2.66, n=6, axis="y", bevel=0)  # ноздри
        a.frustum("ivory", (s * 0.48 - 0.08, s * 0.48 + 0.08, -2.4, -2.25), (s * 0.48, s * 0.48, -2.33, -2.33),
                  hz - 0.62, hz - 0.95, bevel=0)  # клыки
        if sit:
            C.closed_eye(a, (s * 0.55, -1.38, hz + 0.18), 0.4, happy=False)
        else:
            a.box("eyeY", s * 0.55 - 0.22, s * 0.55 + 0.22, -1.42, -1.32, hz + 0.06, hz + 0.32, bevel=0.01)
            a.box("dark", s * 0.55 - 0.04, s * 0.55 + 0.04, -1.46, -1.4, hz + 0.08, hz + 0.3, bevel=0)
            a.box("glint", s * 0.55 - 0.18, s * 0.55 - 0.1, -1.47, -1.44, hz + 0.22, hz + 0.29, bevel=0)
        C.bar(a, "scaleD", (s * 0.2, -1.45, hz + 0.42), (s * 0.95, -1.4, hz + 0.58), 0.16, 0.14)  # надбровья
        C.tube(a, ["ivory"], [(s * 0.7, 0.0, hz + 0.55), (s * 1.15, 0.85, hz + 1.35), (s * 1.3, 1.85, hz + 1.55)],
               [0.27, 0.18], n=6)
        a.frustum("ivory", (s * 1.3 - 0.12, s * 1.3 + 0.12, 1.75, 1.95), (s * 1.3, s * 1.3, 2.45, 2.45), hz + 1.45,
                  hz + 1.65, bevel=0)
        a.extrude("scaleD", [(s * 1.05, hz + 0.3), (s * 1.75, hz + 0.75), (s * 1.6, hz + 0.1), (s * 1.05, hz - 0.15)],
                  -0.45, -0.3, axis="y")  # плавники-уши
    # корона: обод, пять зубцов, камни
    a.frame("gold", C.ngon(0, -0.3, 0.88, 8), 0.2, hz + 0.72, hz + 1.1, axis="z")
    for i, (ang, h) in enumerate(((-150, 0.55), (-120, 0.8), (-90, 1.1), (-60, 0.8), (-30, 0.55), (90, 0.6))):
        t = math.radians(ang)
        x, y = 0.8 * math.cos(t), -0.3 + 0.8 * math.sin(t)
        a.frustum("gold", (x - 0.17, x + 0.17, y - 0.12, y + 0.12), (x, x, y, y), hz + 1.08, hz + 1.08 + h, bevel=0.004)
    for x, key in ((-0.55, "sapphire"), (0.0, "ruby"), (0.55, "emerald")):
        C.gem(a, key, (x, -1.12 + abs(x) * 0.25, hz + 0.92), 0.3 if x else 0.4)
    a.transform = None

    # руки: золотые браслеты, когти; в правой — скипетр с рубиновой державой
    for i, s in enumerate((1, -1)):
        pitch, out = ARMS[pose][i]
        root = Vector((s * 2.2, 0.1, 5.45 + dz + base))
        a.transform = C.tilt(root, "Y", -s * out) @ C.tilt(root, "X", -pitch)
        elbow, wrist = root - Vector((0, 0, 1.4)), root - Vector((0, 0, 2.6))
        C.tube(a, ["scale"], [root, elbow, wrist], [0.6, 0.52], n=8)
        a.frame("gold", C.ngon(wrist.x, wrist.y, 0.6, 8), 0.16, wrist.z + 0.05, wrist.z + 0.4, axis="z")
        C.blob(a, "scale", (wrist.x, wrist.y, wrist.z - 0.32), 0.55, 0.5, 0.42, n=3)
        for k in (-0.3, 0.0, 0.3):
            a.frustum("ivory", (wrist.x + k - 0.08, wrist.x + k + 0.08, wrist.y - 0.55, wrist.y - 0.38),
                      (wrist.x + k, wrist.x + k, wrist.y - 0.62, wrist.y - 0.62), wrist.z - 0.5, wrist.z - 0.85, bevel=0)
        if s == -1 and pose != "attack2":
            C.bar(a, "gold", (wrist.x, wrist.y - 0.2, wrist.z + 1.4), (wrist.x, wrist.y - 0.2, wrist.z - 2.2), 0.22)
            C.blob(a, "ruby", (wrist.x, wrist.y - 0.2, wrist.z + 1.85), 0.48, 0.48, 0.48, n=4)
            a.frame("gold", C.ngon(wrist.x, wrist.y - 0.2, 0.5, 8), 0.1, wrist.z + 1.78, wrist.z + 1.92, axis="z")
            a.frustum("gold", (wrist.x - 0.12, wrist.x + 0.12, wrist.y - 0.32, wrist.y - 0.08),
                      (wrist.x, wrist.x, wrist.y - 0.2, wrist.y - 0.2), wrist.z + 2.3, wrist.z + 2.75, bevel=0.004)
        a.transform = None
    # крылья
    sweep, lift = WINGS[pose]
    for s in (1, -1):
        wing(a, s, (s * 1.0, 2.15, 6.3 + dz + base), sweep, lift)
    obj = C.finish(a, collection)

    fx = []
    if pose == "attack1":
        f = C.new_art("Boss10fx")
        f.paint("neonFire", "FF4A12")
        f.paint("neonFireY", "FFA51F")
        for k in range(6):
            t = k / 5
            c = Vector((0, -2.9 - 1.15 * k, hz - 0.5 - 0.42 * k))
            r = 0.35 + 0.42 * k
            C.blob(f, "neonFire" if k % 2 else "neonFireY", c, r, r * 0.8, r * 0.8, n=4)
        fx.append(C.finish(f, collection, glow=1.6))
    if pose == "attack2":
        f = C.new_art("Boss10fx")
        f.paint("neonGold", "FFD54A")
        f.paint("gold", "F2C230")
        for k, r in enumerate((3.0, 4.2, 5.4)):
            f.frame("neonGold", C.ngon(0, -0.5, r, 16), 0.12, 0.03 + k * 0.03, 0.13 + k * 0.03, axis="z")
        for i in range(14):
            t = math.radians(i * 51)
            r = 2.2 + 0.25 * i
            c = (r * math.cos(t), -0.5 + r * math.sin(t) * 0.7, 1.0 + 0.45 * i)
            C.disc(f, "gold", c[0], c[1], 0.3, c[2], c[2] + 0.08, n=8, bevel=0.01, matrix=C.tilt(c, "X", 30 + i * 17))
        fx.append(C.finish(f, collection, glow=3.0))
    if sit:
        f = C.new_art("Boss10fx")
        f.paint("smoke", "C9C4CE", rings=True)
        for k, (dx, dy, dz2, r) in enumerate(((0.3, -3.0, 0.2, 0.28), (0.6, -3.4, 0.6, 0.38), (1.0, -3.7, 1.15, 0.5))):
            p = head @ Vector((dx, dy, hz - 0.3 + dz2))
            C.blob(f, "smoke", p, r, r, r, n=3)
        fx.append(C.finish(f, collection))
    return [obj] + fx
