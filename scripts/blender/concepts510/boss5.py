"""Концепт босса 5 «Полярный медведь» (Ледник): огромный сонный белый медведь, вязаный шарф, ледяная корона.

Черновая блочная модель для концепт-листа (не финальная, в игру не идёт). Формы — пухлые эллипсоиды ступенями D39.
Позы: idle — боевая стойка на задних лапах (виды спереди/сбоку/сзади), sleep — сидит, глаза закрыты (на арене),
attack1 — «Ледяная оплеуха» (лапа над головой, ледяные осколки), attack2 — «Снежный ком» (ком над головой).
Высота модели ≈ 7 (в игре ×3 ≈ 21 стад; Сфинкс стоя — 16.8).
"""

import math

import ck as C
from mathutils import Vector

PALETTE = {
    "fur": ("D2DDEA", "мех: белый с голубой тенью"),
    "furS": ("A9BDD4", "брови, тень меха"),
    "belly": ("EFE2C8", "живот, морда, подушечки"),
    "nose": ("262A3E", "нос, когти"),
    "scarf": ("D63B4C", "шарф: клюквенный"),
    "scarfB": ("F3E3C6", "полосы шарфа: кремовые"),
    "ice": ("8EDDFA", "лёд короны и браслетов"),
    "iceD": ("3F8FD6", "ободок и камень короны"),
    "iris": ("2B4A9C", "глаза: тёмно-синие"),
}
EXPOSURE = -0.45  # белый мех: без пересвета
ARMS = {"idle": [(20, 18), (20, 18)], "sleep": [(55, -5), (55, -5)],
        "attack1": [(168, 12), (25, 22)], "attack2": [(166, 34), (166, 34)]}


def build(collection, pose="idle"):
    a = C.new_art("Boss5", ring_z0=3.0)
    for k, (code, _) in PALETTE.items():
        a.paint(k, code, rings=k in ("fur", "belly", "scarf"))
    for k, code in (("white", "FFFFFF"), ("dark", "141726"), ("glint", "FFFFFF"), ("pink", "E9B7C2")):
        a.paint(k, code)
    sit = pose == "sleep"
    dz = -0.75 if sit else 0.0

    # ноги: стоя — тумбы со ступнями; сидя — ступни вперёд подушечками к зрителю
    for s in (1, -1):
        x = s * 1.2
        if sit:
            C.blob(a, "fur", (x, -1.0, 0.7), 0.75, 1.1, 0.7, n=4)
            C.blob(a, "belly", (x, -2.0, 0.75), 0.55, 0.12, 0.55, n=3)
            for k in (-0.3, 0.0, 0.3):
                C.disc(a, "belly", x + k, 1.35, 0.13, -2.18, -2.06, axis="y")
        else:
            C.blob(a, "fur", (x, 0.15, 0.95), 0.75, 0.78, 0.7, n=4)
            C.blob(a, "fur", (x, -0.35, 0.3), 0.85, 1.0, 0.32, n=3, z0=0.0)
            for k in (-0.38, 0.0, 0.38):
                a.frustum("nose", (x + k - 0.1, x + k + 0.1, -1.33, -1.13), (x + k, x + k, -1.48, -1.48), 0.32, 0.05,
                          bevel=0)

    # туловище и живот
    C.blob(a, "fur", (0, 0.3, 2.85 + dz), 2.05, 1.65, 1.85, n=8)
    C.blob(a, "belly", (0, -0.62, 2.55 + dz), 1.45, 1.0, 1.35, n=6)
    C.blob(a, "fur", (0, 1.85, 1.7 + dz), 0.36, 0.3, 0.33, n=3)  # хвостик

    # голова
    hz = 5.45 + dz
    head = C.tilt((0, 0, hz - 1.0), "X", 16 if sit else 0)
    a.transform = head
    C.blob(a, "fur", (0, -0.25, hz), 1.5, 1.3, 1.2, n=6)
    for s in (1, -1):
        C.blob(a, "fur", (s * 1.02, -1.0, hz - 0.3), 0.52, 0.45, 0.42, n=3)  # щёки
        C.blob(a, "fur", (s * 1.12, -0.1, hz + 1.08), 0.42, 0.3, 0.36, n=3)  # уши
        a.box("pink", s * 1.12 - 0.2, s * 1.12 + 0.2, -0.43, -0.38, hz + 0.95, hz + 1.25, bevel=0.01)
    C.blob(a, "belly", (0, -1.42, hz - 0.42), 0.8, 0.55, 0.52, n=4)  # морда
    for s in (1, -1):
        a.box("pink", s * 0.95 - 0.22, s * 0.95 + 0.22, -1.47, -1.4, hz - 0.32, hz - 0.12, bevel=0.01)  # румянец
    C.disc(a, "nose", 0, hz - 0.12, 0.33, -2.12, -1.86, axis="y", sy=0.75)
    a.box("glint", -0.2, -0.06, -2.15, -2.11, hz - 0.03, hz + 0.05, bevel=0)
    C.bar(a, "nose", (-0.42, -1.96, hz - 0.62), (0.0, -1.98, hz - 0.52), 0.07, 0.06, bevel=0)
    C.bar(a, "nose", (0.0, -1.98, hz - 0.52), (0.42, -1.96, hz - 0.64), 0.07, 0.06, bevel=0)
    for s in (1, -1):
        if sit:
            C.closed_eye(a, (s * 0.62, -1.5, hz + 0.22), 0.48, happy=False)
            C.bar(a, "furS", (s * 0.3, -1.52, hz + 0.47), (s * 0.95, -1.52, hz + 0.43), 0.17, 0.13)
        else:
            C.eye(a, (s * 0.66, -1.47, hz + 0.24), 0.72, 0.6, look=(-s * 0.15, -0.1), lid=0.45, lid_key="fur",
                  iris="iris")
            C.bar(a, "furS", (s * 0.26, -1.55, hz + 0.5), (s * 0.98, -1.55, hz + 0.66), 0.18, 0.14)
    # ледяная корона набекрень: ободок, пять сосулек спереди, камень
    a.transform = head @ C.tilt((0, -0.25, hz + 1.1), "Y", -10)
    a.frame("iceD", C.ngon(0, -0.25, 1.12, 8, sy=0.95), 0.2, hz + 0.98, hz + 1.3, axis="z")
    for i, (ang, h) in enumerate(((-150, 0.55), (-120, 0.85), (-90, 1.35), (-60, 0.85), (-30, 0.55),
                                  (30, 0.5), (90, 0.6), (150, 0.5))):
        t = math.radians(ang)
        x, y = 1.0 * math.cos(t), -0.25 + 0.95 * math.sin(t)
        a.frustum("ice", (x - 0.2, x + 0.2, y - 0.17, y + 0.17), (x, x, y, y), hz + 1.28, hz + 1.28 + h, bevel=0.004)
    C.gem(a, "iceD", (0, -1.22, hz + 1.13), 0.34)
    a.transform = None

    # шарф: три полосы вокруг шеи, концы на груди, узел сзади
    sz = 4.1 + dz
    for k, key in enumerate(("scarf", "scarfB", "scarf")):
        a.frame(key, C.ngon(0, 0.05, 1.62, 8, sy=0.98), 0.62, sz + k * 0.19, sz + (k + 1) * 0.19 + 0.005, axis="z")
    for k in range(6):
        key = "scarf" if k % 2 == 0 else "scarfB"
        zz = sz - k * 0.33
        a.box(key, 0.55, 1.2, -1.95 + k * 0.03, -1.62 + k * 0.03, zz - 0.33, zz + 0.002)
    for k in range(4):
        a.box("scarfB", 0.6 + k * 0.17, 0.7 + k * 0.17, -1.86, -1.62, sz - 2.3, sz - 1.98, bevel=0.005)
    a.box("scarf", -0.5, 0.5, 1.45, 1.85, sz, sz + 0.55)
    for k in range(3):
        key = "scarf" if k % 2 == 0 else "scarfB"
        a.box(key, -0.45 + k * 0.08, 0.05 + k * 0.08, 1.6, 1.92, sz - 0.4 - k * 0.36, sz - 0.04 - k * 0.36)

    # руки: плечо → локоть → запястье → лапа с когтями и ледяным браслетом
    for i, s in enumerate((1, -1)):
        pitch, out = ARMS[pose][i]
        root = Vector((s * 1.85, 0.05, 3.95 + dz))
        a.transform = C.tilt(root, "Y", -s * out) @ C.tilt(root, "X", -pitch)
        elbow, wrist = root - Vector((0, 0, 1.3)), root - Vector((0, 0, 2.35))
        C.tube(a, ["fur"], [root + Vector((0, 0, 0.35)), elbow, wrist], [0.62, 0.55], n=8)
        a.frame("ice", C.ngon(wrist.x, wrist.y, 0.66, 8), 0.16, wrist.z - 0.05, wrist.z + 0.22, axis="z")
        C.blob(a, "fur", (wrist.x, wrist.y - 0.08, wrist.z - 0.45), 0.66, 0.62, 0.48, n=4)
        for k in (-0.34, 0.0, 0.34):
            a.frustum("nose", (wrist.x + k - 0.09, wrist.x + k + 0.09, wrist.y - 0.72, wrist.y - 0.52),
                      (wrist.x + k, wrist.x + k, wrist.y - 0.78, wrist.y - 0.78), wrist.z - 0.62, wrist.z - 0.98, bevel=0)
        a.transform = None
    obj = C.finish(a, collection)

    fx = []
    if pose == "attack1":
        f = C.new_art("Boss5fx")
        f.paint("neonIce", "8BEFFF")
        f.paint("ice", "C9F5FF")
        for i in range(10):
            ang = i * 36
            c = Vector((1.75 + 1.5 * math.cos(math.radians(ang)), -0.9, 8.4 + 1.3 * math.sin(math.radians(ang))))
            C.gem(f, "ice" if i % 2 else "neonIce", c, 0.32 + 0.12 * (i % 3), turn=ang)
        fx.append(C.finish(f, collection, glow=2.5))
    if pose == "attack2":
        f = C.new_art("Boss5fx")
        f.paint("snow", "F7FBFF", rings=True)
        f.paint("snowS", "D2E3F2", rings=True)
        C.blob(f, "snow", (0, -0.3, 8.55), 1.65, 1.5, 1.5, n=7)
        for i in range(5):
            ang = i * 72 + 20
            C.blob(f, "snowS", (1.75 * math.cos(math.radians(ang)), -0.4 + 0.5 * math.sin(math.radians(ang)),
                                8.55 + 1.3 * math.sin(math.radians(ang))), 0.4, 0.4, 0.38, n=3)
        fx.append(C.finish(f, collection))
    return [obj] + fx
