"""Концепт босса 6 «Горилла» (Джунгли): мощная горилла с серебристой спиной, короной из листьев и огромным барабаном.

Черновая блочная модель для концепт-листа (не финальная). Барабан-колода висит за спиной на лианах (силуэт сзади),
в особой атаке — перед ней. Позы: idle — стойка на костяшках (огромные плечи, длинные руки), sleep — сидит, обняв
барабан, attack1 — «Кулак-молот» (кулаки сцеплены над головой), attack2 — «Барабанная дробь» (бьёт в барабан,
зелёные кольца-волны). Высота ≈ 7.3, ширина плеч ≈ 6 (в игре ×3).
"""

import math

import ck as C
from mathutils import Vector

EXPOSURE = 0.35  # тёмная шерсть
PALETTE = {
    "fur": ("40465A", "шерсть: тёмный сланец"),
    "furS": ("2C3140", "шерсть в тени, гребень"),
    "silver": ("C2CBD8", "серебристая спина"),
    "skin": ("7C6C66", "лицо, грудь, ладони"),
    "leaf": ("45C45F", "листья короны"),
    "leafD": ("2B8B47", "тёмные листья, лианы"),
    "flower": ("FF6FAE", "цветок короны"),
    "nut": ("6B4226", "бусы-орехи"),
    "wood": ("7E4524", "барабан: колода"),
    "woodD": ("4E2A14", "обручи барабана"),
    "hide": ("EFD9AE", "кожа барабана"),
    "jade": ("2FD3A9", "нефритовые вставки"),
    "iris": ("FFB12B", "глаза: янтарь"),
}
ARMS = {"idle": [(18, 22, 0), (18, 22, 0)], "sleep": [(60, -12, 0), (60, -12, 0)],
        "attack1": [(172, -8, 0), (172, -8, 0)], "attack2": [(70, 5, 0), (95, 5, 0)]}


def drum(a, c, upright=True):
    """Барабан-колода: стоя — кожей вверх; на спине — лёжа поперёк (сзади виден бочонок с обручами)."""
    x, y, z = c
    r, h = (1.25, 2.4) if upright else (1.5, 3.0)
    m = None if upright else C.tilt((x, y, z), "Y", 90)
    a.transform = m
    C.disc(a, "wood", x, y, r, z - h / 2, z + h / 2)
    for k in (-0.75, 0.0, 0.75):
        a.frame("woodD", C.ngon(x, y, r + 0.08, 8), 0.14, z + k - 0.12, z + k + 0.12, axis="z")
    C.disc(a, "hide", x, y, r - 0.1, z + h / 2 - 0.02, z + h / 2 + 0.12)
    C.disc(a, "jade", x, y, 0.35, z + h / 2 + 0.1, z + h / 2 + 0.16, bevel=0)
    a.transform = None


def build(collection, pose="idle"):
    a = C.new_art("Boss6", ring_z0=3.0)
    for k, (code, _) in PALETTE.items():
        a.paint(k, code, rings=k in ("fur", "silver", "wood", "skin"))
    for k, code in (("white", "FFFFFF"), ("dark", "121420"), ("glint", "FFFFFF"), ("teeth", "F4F1E6")):
        a.paint(k, code)
    sit = pose == "sleep"
    dz = -0.6 if sit else 0.0

    # ноги и ступни
    for s in (1, -1):
        x = s * 1.25
        C.blob(a, "fur", (x, 0.55 + (-0.8 if sit else 0), 0.85), 0.8, 0.85, 0.8, n=4)
        C.blob(a, "skin", (x, -0.15 + (-1.1 if sit else 0), 0.25), 0.75, 0.85, 0.28, n=3, z0=0.0)
    # туловище: бочка груди, серебристая спина, гребень
    C.blob(a, "fur", (0, 0.25, 3.3 + dz), 2.35, 1.7, 1.9, n=8)
    C.blob(a, "skin", (0, -1.15, 3.55 + dz), 1.45, 0.55, 1.15, n=5)  # грудь
    C.blob(a, "silver", (0, 1.25, 3.7 + dz), 1.85, 0.75, 1.45, n=6)
    for s in (1, -1):
        C.blob(a, "fur", (s * 2.3, 0.1, 4.55 + dz), 1.05, 1.05, 0.95, n=5)  # плечи-горы
    # бусы из орехов дугой на груди
    for i in range(9):
        t = math.radians(-60 + i * 15)
        C.blob(a, "nut", (1.35 * math.sin(t), -1.7, 4.3 + dz - 0.9 * (1 - math.cos(t))), 0.2, 0.16, 0.2, n=2)
    C.gem(a, "jade", (0, -1.78, 3.35 + dz), 0.45)

    # голова — небольшая и низко посаженная, тяжёлые надбровья, гребень
    hz = 5.6 + dz
    head = C.tilt((0, -0.4, hz - 0.8), "X", 18 if sit else 0)
    a.transform = head
    C.blob(a, "fur", (0, -0.55, hz), 1.2, 1.05, 1.05, n=6)
    a.box("furS", -0.35, 0.35, -0.6, 0.6, hz + 0.75, hz + 1.25)  # сагиттальный гребень
    C.blob(a, "skin", (0, -1.42, hz - 0.15), 0.88, 0.4, 0.75, n=4)  # лицо-маска
    a.box("furS", -0.95, 0.95, -1.95, -1.45, hz + 0.32, hz + 0.62)  # надбровный валик
    C.blob(a, "skin", (0, -1.95, hz - 0.45), 0.55, 0.3, 0.32, n=3)  # морда
    for s in (1, -1):
        C.disc(a, "dark", s * 0.2, hz - 0.3, 0.1, -2.27, -2.2, axis="y", bevel=0)  # ноздри
        if sit:
            C.closed_eye(a, (s * 0.45, -1.85, hz + 0.12), 0.34, happy=False)
        else:
            C.eye(a, (s * 0.45, -1.84, hz + 0.12), 0.38, 0.28, look=(-s * 0.1, 0.0), lid=0.25, lid_key="furS",
                  iris="iris")
        C.blob(a, "skin", (s * 1.12, -0.6, hz + 0.05), 0.2, 0.18, 0.28, n=2)  # уши
    if sit:
        C.bar(a, "dark", (-0.4, -2.26, hz - 0.68), (0.4, -2.26, hz - 0.68), 0.07, 0.05, bevel=0)
    else:
        a.box("dark", -0.42, 0.42, -2.27, -2.2, hz - 0.82, hz - 0.62, bevel=0)  # рот рыком
        for k in range(5):
            a.box("teeth", -0.36 + k * 0.16, -0.26 + k * 0.16, -2.3, -2.24, hz - 0.7, hz - 0.62, bevel=0)
    # корона из листьев: веер листьев вокруг макушки и розовый цветок
    for i in range(9):
        ang = -80 + i * 20
        t = math.radians(ang)
        base = Vector((0.95 * math.sin(t), -0.55 - 0.85 * math.cos(t) * 0.6, hz + 0.75))
        m = C.tilt(base, "Y", ang * 0.6) @ C.tilt(base, "X", -12)
        a.transform = head @ m
        key = "leaf" if i % 2 == 0 else "leafD"
        a.frustum(key, (base.x - 0.2, base.x + 0.2, base.y - 0.06, base.y + 0.06), (base.x, base.x, base.y, base.y),
                  base.z, base.z + 0.95 + 0.25 * (i % 2), bevel=0.003)
    a.transform = head
    for i in range(5):
        t = math.radians(i * 72)
        C.blob(a, "flower", (0.85 + 0.22 * math.cos(t), -1.35, hz + 0.95 + 0.22 * math.sin(t)), 0.16, 0.08, 0.16, n=2)
    C.gem(a, "jade", (0.85, -1.45, hz + 0.95), 0.18)
    a.transform = None

    # руки: длинные, кулаки-гири, браслеты из лиан
    for i, s in enumerate((1, -1)):
        pitch, out, _ = ARMS[pose][i]
        root = Vector((s * 2.55, 0.0, 4.6 + dz))
        a.transform = C.tilt(root, "Y", -s * out) @ C.tilt(root, "X", -pitch)
        elbow, wrist = root - Vector((0, 0, 1.75)), root - Vector((0, 0, 3.3))
        C.tube(a, ["fur"], [root + Vector((0, 0, 0.3)), elbow, wrist], [0.78, 0.66], n=8)
        a.frame("leafD", C.ngon(wrist.x, wrist.y, 0.75, 8), 0.16, wrist.z + 0.05, wrist.z + 0.35, axis="z")
        C.blob(a, "skin", (wrist.x, wrist.y - 0.1, wrist.z - 0.45), 0.78, 0.7, 0.6, n=4)  # кулак
        for k in (-0.4, -0.13, 0.13, 0.4):
            a.box("furS", wrist.x + k - 0.1, wrist.x + k + 0.1, wrist.y - 0.85, wrist.y - 0.65, wrist.z - 0.95,
                  wrist.z - 0.55)  # костяшки
        a.transform = None

    # барабан: за спиной (стойка, сон — рядом), перед грудью в «барабанной дроби»
    if pose == "attack2":
        drum(a, (0, -2.6, 2.2), upright=True)
    elif sit:
        drum(a, (2.9, -1.2, 1.25), upright=True)
    else:
        drum(a, (0, 2.75, 3.7), upright=False)
        for s in (1, -1):  # лианы-лямки
            C.bar(a, "leafD", (s * 1.1, -1.3, 5.0), (s * 0.9, 2.5, 5.2), 0.2, 0.12)
    obj = C.finish(a, collection)

    fx = []
    if pose == "attack2":
        f = C.new_art("Boss6fx")
        f.paint("neonLeaf", "5CFF7A")
        for k, r in enumerate((2.6, 3.6, 4.6)):
            f.frame("neonLeaf", C.ngon(0, -2.6, r, 16), 0.12, 0.05 + k * 0.02, 0.14 + k * 0.02, axis="z")
        fx.append(C.finish(f, collection, glow=2.0))
    if pose == "attack1":
        f = C.new_art("Boss6fx")
        f.paint("rock", "8D7A66", rings=True)
        for i in range(7):
            ang = i * 51
            C.blob(f, "rock", (2.4 * math.cos(math.radians(ang)), -2.2 + 1.2 * math.sin(math.radians(ang)), 0.3 + 0.25 * (i % 3)),
                   0.35, 0.3, 0.3, n=3)
        fx.append(C.finish(f, collection))
    return [obj] + fx
