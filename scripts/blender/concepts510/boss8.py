"""Концепт босса 8 «Лавовый голем» (Вулкан): огромный обсидиановый голем с раскалёнными трещинами и огненным ядром.

Черновая блочная модель для концепт-листа (не финальная). Без кухонных предметов. Глыбы обсидиана и базальта,
маленькая голова глубоко между плеч, на плечах — шестигранные базальтовые столбы, огромные кулаки, в груди — ядро
в обсидиановой оправе. Позы: idle — тяжёлая стойка, кулаки у земли; sleep — сидит, трещины остыли (тёмно-красные);
attack1 — «Обсидиановый молот» (кулаки над головой, лавовое кольцо на земле); attack2 — «Извержение» (ядро
раскрыто, над головой летят раскалённые камни). Высота ≈ 8.6, ширина с кулаками ≈ 8.
"""

import math

import ck as C
from mathutils import Matrix, Vector

EXPOSURE = 0.0
PALETTE = {
    "obs": ("26222F", "обсидиан: тело"),
    "basalt": ("4A4352", "базальт: глыбы, столбы"),
    "basaltL": ("6E6577", "светлые грани базальта"),
    "ash": ("8D8496", "пепел на верхушках"),
    "ember": ("9C3A1E", "остывшие трещины (сон)"),
    "neonLava": ("FF5A1F", "раскалённые трещины"),
    "neonCore": ("FFC23D", "ядро, глаза"),
}
ARMS = {"idle": [(12, 24), (12, 24)], "sleep": [(55, -8), (55, -8)],
        "attack1": [(172, -6), (172, -6)], "attack2": [(40, 48), (40, 48)]}


def rock(a, key, c, w, d, h, turn=0.0, cut=0.35):
    """Глыба: восьмигранная призма с поворотом вокруг z (рубленые формы)."""
    m = C.tilt(c, "Z", turn)
    a.prism(key, *C.octa((c[0], c[1]), w, d, c[2] - h / 2, c[2] + h / 2, cut=w * cut / 2), matrix=m)


def crack(a, key, pts, w=0.12):
    """Светящаяся трещина-зигзаг по точкам (чуть выступает над поверхностью)."""
    for p0, p1 in zip(pts, pts[1:]):
        C.bar(a, key, p0, p1, w, w, bevel=0)


def build(collection, pose="idle"):
    a = C.new_art("Boss8", ring_z0=3.0)
    for k, (code, _) in PALETTE.items():
        a.paint(k, code, rings=k in ("obs", "basalt", "basaltL"))
    a.paint("dark", "0E0B12")
    sit = pose == "sleep"
    hot = "ember" if sit else "neonLava"
    core = "ember" if sit else "neonCore"
    dz = -0.9 if sit else 0.0

    # ноги-тумбы
    for s in (1, -1):
        x = s * 1.6
        if sit:
            rock(a, "obs", (x, -1.3, 0.75), 1.6, 2.4, 1.5, turn=s * 6)
            rock(a, "basalt", (x, -2.55, 0.55), 1.7, 0.5, 1.1)
        else:
            rock(a, "obs", (x, 0.0, 1.25), 1.7, 1.7, 2.5, turn=s * 8)
            rock(a, "basalt", (x, -0.25, 0.3), 2.0, 2.3, 0.6)
            crack(a, hot, [(x - 0.4, -0.88, 2.2), (x - 0.1, -0.88, 1.7), (x - 0.3, -0.88, 1.2)])
    # туловище: таз, бочка груди, широкие плечи
    rock(a, "obs", (0, 0.0, 2.85 + dz), 3.6, 2.6, 1.3)
    rock(a, "obs", (0, 0.05, 4.4 + dz), 4.8, 3.1, 2.1, cut=0.45)
    rock(a, "basalt", (0, 0.15, 5.9 + dz), 5.8, 3.2, 1.3, cut=0.5)
    rock(a, "basaltL", (0, 1.3, 4.9 + dz), 4.0, 1.4, 2.6)  # спинная глыба
    for x, h in ((-1.0, 1.4), (-0.35, 2.1), (0.35, 1.7), (1.0, 1.1)):  # столбы на спине
        a.prism("basalt", C.ngon(x, 1.55, 0.34, 6, phase=0), 6.0 + dz, 6.0 + dz + h)
        a.prism(hot, C.ngon(x, 1.55, 0.27, 6, phase=0), 6.0 + dz + h, 6.08 + dz + h, bevel=0)
    for x0 in (-1.2, 0.4):  # трещины на спине
        crack(a, hot, [(x0, 2.02, 6.0 + dz), (x0 + 0.4, 2.02, 5.3 + dz), (x0 + 0.1, 2.02, 4.5 + dz),
                       (x0 + 0.6, 2.02, 3.8 + dz)], 0.12)
    for s in (1, -1):
        rock(a, "basalt", (s * 1.4, -1.5, 3.6 + dz), 1.5, 0.4, 1.2, turn=-s * 6)  # пластины живота
    # ядро в оправе: шестигранник в рамке, лучи-трещины от него
    cz = 4.75 + dz
    a.frame("basaltL", C.ngon(0, cz, 1.05, 6, phase=0), 0.32, -1.88, -1.4, axis="y")
    open_core = pose == "attack2"
    a.prism(core, C.ngon(0, cz, 0.85 if open_core else 0.72, 6, phase=0), -1.72, -1.45, axis="y", bevel=0)
    for ang in (20, 75, 140, 200, 260, 330):
        t = math.radians(ang)
        p0 = (1.05 * math.cos(t), -1.6, cz + 1.05 * math.sin(t))
        p1 = (1.8 * math.cos(t + 0.2), -1.62, cz + 1.6 * math.sin(t + 0.2))
        p2 = (2.2 * math.cos(t - 0.1), -1.5, cz + 1.9 * math.sin(t - 0.1))
        crack(a, hot, [p0, p1, p2], 0.13)
    # столбы базальта на плечах (силуэт) с раскалёнными верхушками
    for s in (1, -1):
        for j, (dx, dy, h) in enumerate(((0.0, 0.0, 1.9), (0.55, 0.45, 1.3), (-0.5, 0.5, 1.0), (0.35, -0.5, 0.8))):
            x, y = s * (2.35 + dx), 0.2 + dy
            z0 = 6.4 + dz
            a.prism("basalt" if j % 2 == 0 else "basaltL", C.ngon(x, y, 0.38, 6, phase=0), z0, z0 + h)
            a.prism(hot, C.ngon(x, y, 0.3, 6, phase=0), z0 + h, z0 + h + 0.08, bevel=0)
    # голова: глыба глубоко между плеч, лоб-козырёк, светящиеся злые глаза и трещина-рот
    hz = 7.05 + dz
    head = C.tilt((0, -0.6, hz - 0.6), "X", 20 if sit else 0)
    a.transform = head
    rock(a, "obs", (0, -0.6, hz), 1.9, 1.7, 1.4, cut=0.4)
    a.prism("basalt", *C.octa((0, -1.05), 2.3, 0.9, hz + 0.3, hz + 0.75, cut=0.25))  # надбровный козырёк
    for s, h in ((1, 1.25), (-1, 1.25), (0, 0.7)):  # рога-осколки
        bx, by, bz = s * 0.65, -0.55, hz + 0.6
        a.frustum("basaltL", (bx - 0.26, bx + 0.26, by - 0.26, by + 0.26), (bx, bx, by, by), bz, bz + h, bevel=0.004,
                  matrix=C.tilt((bx, by, bz), "Y", s * 32))
    for s in (1, -1):
        if sit:
            a.box("ember", s * 0.15, s * 0.7, -1.5, -1.44, hz + 0.08, hz + 0.16, bevel=0)
        else:
            a.prism("neonCore", [(s * 0.15, hz + 0.02), (s * 0.8, hz + 0.32), (s * 0.78, hz + 0.1),
                                 (s * 0.18, hz - 0.14)][:: s], -1.5, -1.42, axis="y", bevel=0)  # злой прищур
    a.box("dark", -0.62, 0.62, -1.49, -1.43, hz - 0.62, hz - 0.3, bevel=0)  # пасть-щель
    crack(a, hot, [(-0.55, -1.51, hz - 0.5), (-0.3, -1.51, hz - 0.38), (-0.1, -1.51, hz - 0.52), (0.1, -1.51, hz - 0.38),
                   (0.3, -1.51, hz - 0.52), (0.55, -1.51, hz - 0.4)], 0.09)
    a.transform = None

    # руки: тяжёлые глыбы, лавовые пояса, огромные кулаки с трещинами
    for i, s in enumerate((1, -1)):
        pitch, out = ARMS[pose][i]
        root = Vector((s * 3.0, 0.1, 5.9 + dz))
        a.transform = C.tilt(root, "Y", -s * out) @ C.tilt(root, "X", -pitch)
        rock(a, "basalt", (root.x, root.y, root.z + 0.1), 1.8, 1.8, 1.4)  # плечевая глыба
        elbow, wrist = root - Vector((0, 0, 1.7)), root - Vector((0, 0, 3.2))
        C.tube(a, ["obs"], [root, elbow], 0.72, n=6)
        C.tube(a, ["basalt"], [elbow, wrist], 0.95, n=6)
        a.prism(hot, C.ngon(elbow.x, elbow.y, 0.8, 6), elbow.z - 0.12, elbow.z + 0.12, bevel=0)
        a.prism(hot, C.ngon(wrist.x, wrist.y, 1.0, 6), wrist.z + 0.25, wrist.z + 0.4, bevel=0)
        rock(a, "obs", (wrist.x, wrist.y, wrist.z - 0.65), 1.75, 1.6, 1.3, cut=0.5)  # кулак
        for k in range(2):  # осколки на предплечье
            bx, by, bz = wrist.x + s * 0.8, wrist.y + 0.2, wrist.z + 0.7 + k * 0.65
            a.frustum("basaltL", (bx - 0.2, bx + 0.2, by - 0.2, by + 0.2), (bx, bx, by, by), bz, bz + 0.85 - k * 0.2,
                      bevel=0.004, matrix=C.tilt((bx, by, bz), "Y", s * 65))
        for k in (-0.55, 0.0, 0.55):
            rock(a, "basaltL", (wrist.x + k, wrist.y - 0.85, wrist.z - 0.95), 0.48, 0.3, 0.55)
        crack(a, hot, [(wrist.x - 0.6, wrist.y - 0.82, wrist.z - 0.2), (wrist.x - 0.2, wrist.y - 0.82, wrist.z - 0.5),
                       (wrist.x + 0.3, wrist.y - 0.82, wrist.z - 0.3)], 0.1)
        a.transform = None
    # потёки лавы под ядром
    if not sit:
        for x, h in ((-0.35, 0.6), (0.3, 0.9)):
            a.frustum("neonLava", (x - 0.12, x + 0.12, -1.75, -1.55), (x, x, -1.68, -1.68), cz - 0.85, cz - 0.85 - h,
                      bevel=0)
    obj = C.finish(a, collection, glow=2.0)

    fx = []
    if pose == "attack1":
        f = C.new_art("Boss8fx")
        f.paint("neonLava", "FF5A1F")
        f.paint("rock", "3A3342", rings=True)
        for k, r in enumerate((3.2, 4.4)):
            f.frame("neonLava", C.ngon(0, -2.4, r, 12), 0.18, 0.02 + k * 0.02, 0.12 + k * 0.02, axis="z")
        for i in range(8):
            t = math.radians(i * 45 + 10)
            rock(f, "rock", (3.8 * math.cos(t), -2.4 + 3.0 * math.sin(t), 0.35), 0.7, 0.6, 0.7, turn=i * 20)
        fx.append(C.finish(f, collection, glow=2.2))
    if pose == "attack2":
        f = C.new_art("Boss8fx")
        f.paint("neonLava", "FF5A1F")
        f.paint("rock", "3A3342", rings=True)
        for i in range(7):
            t = math.radians(i * 52)
            c = (2.8 * math.cos(t), -0.8 + 1.2 * math.sin(t), 9.6 + 1.2 * math.sin(t * 2))
            rock(f, "rock", c, 0.75, 0.7, 0.75, turn=i * 33)
            a2 = C.tilt(c, "Z", i * 33)
            f.prism("neonLava", C.ngon(c[0], c[1], 0.3, 6), c[2] + 0.37, c[2] + 0.45, bevel=0, matrix=a2)
            f.frustum("neonLava", (c[0] - 0.15, c[0] + 0.15, c[1] - 0.15, c[1] + 0.15), (c[0], c[0], c[1], c[1]),
                      c[2] - 0.4, c[2] - 1.4, bevel=0)  # огненный хвост
        fx.append(C.finish(f, collection, glow=2.2))
    return [obj] + fx
