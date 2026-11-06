"""D48-C, фаза 2 — финальные Blender-модули музея (архитектура, ниши, постаменты, галереи, павильон с решёткой
хранилища, лестница, хранилище) в формате пачек проекта (lego.py): каждая модель — набор мешей-ролей по цветам,
FBX «<Модель>_<Роль>», раскладка assets/models/Pack3_d48.layout.json (центр, размер, цвет, материал, треугольники).
В игре роль = MeshPart с Color и Plastic — квадратные пупырышки даёт MaterialVariant LegoSquaresSoft (D36, 8 стадов
на плитку), неон — Neon, стекло — Glass. Новых текстур загружать не нужно.

Повторяющиеся детали — один меш на все копии (постамент ×20, урна, створка решётки, стеллаж, ячейки): Roblox
рисует одинаковые MeshId дешевле. Стены зала вместе с пилястрами и нишами — один модуль на сторону.
Где что стоит на каждом уровне — assets/concepts/d48/c2/mesh_placement.json (источник — d48c_layout.py).
UV: проекция на грань (1 UV = 8 стадов, как StudsPerTile материала музея) — для MaterialVariant и будущих запеканий.

Запуск: blender --background --factory-startup --python scripts/blender/d48_final.py -- <репо> [--no-render]
        [--fast] [виды]
Пишет assets/models/Pack3_d48.fbx, Pack3_d48.layout.json, assets/concepts/d48/c2/{mesh_placement.json,
d48_final.blend, renders/*.png}.
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import d48_kit as K  # noqa: E402
import d48c_layout as L  # noqa: E402
import lego  # noqa: E402
from lego import Model  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
REPO = os.path.abspath(argv[0]) if argv else os.getcwd()
NO_RENDER = "--no-render" in argv
FAST = "--fast" in argv
ONLY = [a for a in argv[1:] if not a.startswith("--")]
C2 = os.path.join(REPO, "assets", "concepts", "d48", "c2")
RENDERS = os.path.join(C2, "renders")
os.makedirs(RENDERS, exist_ok=True)
PACK = "Pack3_d48"

lego.PALETTE.update({
    "d48wall": "F4EFE4", "d48pil": "FBF8F1", "d48gold": "E9B43C", "d48golddeep": "C98E1E", "d48navy": "26345E",
    "d48navydark": "1A2440", "d48floor": "EFE6D3", "d48runner": "B8283A", "d48ceiling": "D3E3F2", "d48beam": "F7F2E8",
    "d48backdrop": "2E4377", "d48steel": "3A5A8C", "d48steellight": "A7B6C8", "d48steeldark": "5E7186",
    "d48roof": "D9705A", "d48step": "93A7C7", "d48disk": "AEBCD0", "d48vwall": "1F3A63", "d48vpanel": "2C5283",
    "d48vfloor": "17223D", "d48vceil": "131D33", "d48locker": "8EA2BD", "d48plant": "4FB45A", "d48plantdark": "3C8F47",
    "d48stone": "D8D2C4", "d48chest": "3E7BE0", "d48chestlight": "5A93F0", "d48red": "F0473C", "d48cyan": "39E1FF",
    "d48warm": "FFD88A", "d48screen": "1D6FE0", "d48sky": "EAF7FF", "d48glass": "BDEBFF", "d48white": "FFFFFF",
    "d48rare": "4FA6EA", "d48epic": "B266F5", "d48legend": "F7B731",
})

HW, FZ, BZ, T = L.HW, L.FZ, L.BZ, L.T
IX, IZ0, IZ1 = L.IX, L.IZ0, L.IZ1
CEIL, DOOR, DOORH = L.CEIL, L.DOOR, L.DOORH
G, VF, SLAB, VCEIL = -1.3, -13.0, 1.4, -1.8
ST0, STW = L.ST0, L.STW
WELL_X, WELL_Z1 = 2.8, 11.0
PV_X, PV_Z0, PV_Z1, PV_H = L.PV_X, L.PV_Z0, L.PV_Z1, 9.0
PORTICO_Z = -23.0
B1 = 0.12  # фаска крупных деталей
B2 = 0.06  # фаска мелких деталей


def bx(m, color, x0, x1, y0, y1, z0, z1, bevel=B1, role="Body", rotation=None):
    if min(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)) < 0.45:
        bevel = 0  # мелочь: фаску всё равно не видно, а треугольников вчетверо больше
    m.box(role, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), color,
          bevel=bevel, rotation=rotation)


def glow(m, color, x0, x1, y0, y1, z0, z1):
    bx(m, color, x0, x1, y0, y1, z0, z1, bevel=0, role="Glow")


def glass(m, color, x0, x1, y0, y1, z0, z1):
    bx(m, color, x0, x1, y0, y1, z0, z1, bevel=0, role="Glass")


def side_x(sx, a, b):
    """Полоса a…b от боковой стены зала (sx −1 / +1) → x0, x1."""
    x0, x1 = sx * (IX - a), sx * (IX - b)
    return min(x0, x1), max(x0, x1)


MODELS = {}  # имя → Model


def model(name):
    m = Model(name)
    MODELS[name] = m
    return m


# ── 1. Зал: пол с проёмом, фасад и задняя стена, потолок с кессонами, крыша, задняя стена, дорожка ────────────────
def build_hall():
    m = model("D48_Hall")
    for x0, x1, z0, z1 in ((-HW, HW, FZ, ST0), (-HW, -WELL_X, ST0, BZ), (WELL_X, HW, ST0, BZ),
                           (-WELL_X, WELL_X, WELL_Z1, BZ)):
        bx(m, "d48floor", x0, x1, -SLAB, 0, z0, z1, bevel=0.04)
    top = CEIL + 1.4
    for x0, x1, y0, y1 in ((-IX, -DOOR, 0, top), (DOOR, IX, 0, top), (-DOOR, DOOR, DOORH, top)):
        bx(m, "d48wall", x0, x1, y0, y1, FZ, IZ0, bevel=0.08)
    bx(m, "d48wall", -IX, IX, 0, top, IZ1, BZ, bevel=0.08)
    for x0, x1 in ((-IX, -DOOR - 1.0), (DOOR + 1.0, IX)):  # плинтус и пояс фасада изнутри
        bx(m, "d48navy", x0, x1, 0, 1.0, IZ0, IZ0 + 0.2, bevel=B2)
        bx(m, "d48gold", x0, x1, 12.4, 12.7, IZ0, IZ0 + 0.2, bevel=B2)
    bx(m, "d48navy", -IX, IX, 0, 1.0, IZ1 - 0.2, IZ1, bevel=B2)
    bx(m, "d48gold", -IX, IX, 12.4, 12.7, IZ1 - 0.2, IZ1, bevel=B2)
    bx(m, "d48pil", -IX, IX, 15.2, 16.0, IZ1 - 0.5, IZ1, bevel=B2)
    bx(m, "d48pil", -IX, IX, 15.2, 16.0, IZ0, IZ0 + 0.5, bevel=B2)
    m = model("D48_Roof")  # потолок с кессонами и световым фонарём, ступенчатая крыша
    bx(m, "d48ceiling", -HW, HW, CEIL + 1.4, CEIL + 2.4, FZ, BZ, bevel=0.04)
    bx(m, "d48ceiling", -IX, IX, CEIL + 0.4, CEIL + 1.4, IZ0, IZ1, bevel=0)
    for x in (-11.0, -5.5, 5.5, 11.0):
        bx(m, "d48beam", x - 0.5, x + 0.5, CEIL - 0.4, CEIL + 0.4, IZ0, IZ1, bevel=B2)
    for z in L.PIL_Z:
        bx(m, "d48beam", -IX, IX, CEIL - 0.35, CEIL + 0.35, z - 0.5, z + 0.5, bevel=B2)
    glow(m, "d48sky", -5.0, 5.0, CEIL + 0.39, CEIL + 0.4, -10.5, 10.0)
    for x0, x1, z0, z1 in ((-5.5, 5.5, -11.0, -10.5), (-5.5, 5.5, 10.0, 10.5), (-5.5, -5.0, -10.5, 10.0),
                           (5.0, 5.5, -10.5, 10.0)):
        bx(m, "d48gold", x0, x1, CEIL - 0.6, CEIL - 0.3, z0, z1, bevel=B2)
    for k, w in enumerate((19.5, 16.0, 12.5, 9.0, 5.5, 2.0)):  # крыша ступенями (силуэт D39)
        bx(m, "d48roof", -w, w, CEIL + 2.4 + k * 1.1, CEIL + 3.5 + k * 1.1, FZ - 0.4, BZ + 0.6, bevel=0.1)
    glass(m, "d48glass", -4.5, 4.5, CEIL + 9.0, CEIL + 10.4, -9.5, 9.0)
    m = MODELS["D48_Hall"]
    # задняя стена: эмблема и знамёна
    m.cylinder("Body", (0, 12.3, IZ1 - 0.25), 2.1, 0.5, "d48gold", axis="z", segments=24, bevel=0.08)
    m.cylinder("Body", (0, 12.3, IZ1 - 0.55), 1.5, 0.2, "d48navy", axis="z", segments=24, bevel=0.04)
    m.torus("Body", (0, 12.3, IZ1 - 0.62), 1.15, 0.1, "d48gold", axis="z", segments=24, minor_segments=6)
    for sx in (-1, 1):
        bx(m, "d48gold", sx * 8.0 - 1.9, sx * 8.0 + 1.9, 12.8, 13.1, IZ1 - 0.5, IZ1 - 0.2, bevel=B2)
        bx(m, "d48backdrop", sx * 8.0 - 1.6, sx * 8.0 + 1.6, 6.0, 12.8, IZ1 - 0.35, IZ1 - 0.2, bevel=B2)
        m.wedge("Body", (sx * 8.0, 5.6, IZ1 - 0.28), (3.2, 0.8, 0.14), "d48backdrop", down="-z", bevel=0)
    # дорожка, медальон, гнёзда лазеров
    bx(m, "d48runner", -3.2, 3.2, 0, 0.08, IZ0, PV_Z0 - 0.3, bevel=0.02)
    for sx in (-1, 1):
        bx(m, "d48gold", sx * 3.2 - 0.18, sx * 3.2 + 0.18, 0, 0.1, IZ0, PV_Z0 - 0.3, bevel=0.02)
    m.cylinder("Body", (0, 0.11, -1.4), 3.3, 0.06, "d48gold", segments=24, bevel=0.01)
    m.cylinder("Body", (0, 0.16, -1.4), 2.7, 0.04, "d48navy", segments=24, bevel=0)
    m.cylinder("Body", (0, 0.2, -1.4), 1.0, 0.04, "d48gold", segments=24, bevel=0)
    for name, las in L.LASERS.items():
        half = las["length"] / 2
        for sx in (-1, 1):
            m.cylinder("Body", (sx * half, 0.03, las["z"]), 0.45, 0.06, "d48steeldark", segments=16, bevel=0.01)
        bx(m, "d48red", -half + 0.45, half - 0.45, 0.0, 0.04, las["z"] - 0.04, las["z"] + 0.04, bevel=0)
    # портик и фасад снаружи (база уровней 1–4, D36)
    for i in range(3):
        bx(m, "d48floor", -16, 16, G, G + (i + 1) * (-G / 3), PORTICO_Z + i * 0.7, PORTICO_Z + 2.1, bevel=0.05)
    bx(m, "d48floor", -16, 16, G, 0, PORTICO_Z + 2.1, FZ, bevel=0.05)
    bx(m, "d48wall", -HW - 1, HW + 1, G, -0.02, BZ, BZ + 1, bevel=0.08)
    for cx in (-14.0, -8.0, 8.0, 14.0):
        bx(m, "d48pil", cx - 1.3, cx + 1.3, 0, 0.6, -20.7, -18.1, bevel=0.1)
        m.cylinder("Body", (cx, 6.8, -19.4), 0.95, 12.4, "d48wall", segments=12, bevel=0.0)  # 12 граней = каннелюры
        bx(m, "d48gold", cx - 1.25, cx + 1.25, 13.0, 13.6, -20.65, -18.15, bevel=0.08)
        bx(m, "d48pil", cx - 1.45, cx + 1.45, 13.6, 14.0, -20.85, -17.95, bevel=0.08)
    bx(m, "d48pil", -16.5, 16.5, 14.0, 16.0, -22.6, FZ, bevel=0.1)
    bx(m, "d48gold", -16.6, 16.6, 14.5, 15.3, -22.75, -22.5, bevel=B2)
    for k, (w, y0) in enumerate(((16.5, 16.0), (13.5, 17.2), (10.5, 18.4), (7.5, 19.6), (4.5, 20.8))):
        bx(m, "d48pil", -w, w, y0, y0 + 1.2, -22.6 + 0.2 * k, -21.0, bevel=0.1)
    m.cylinder("Body", (0, 18.3, -22.85), 2.0, 0.5, "d48gold", axis="z", segments=24, bevel=0.08)
    m.cylinder("Glow", (0, 18.3, -23.2), 1.4, 0.3, "d48warm", axis="z", segments=24, bevel=0)
    for x0, x1, y0, y1 in ((-DOOR - 1.0, -DOOR, 0, DOORH + 1.0), (DOOR, DOOR + 1.0, 0, DOORH + 1.0),
                           (-DOOR - 1.0, DOOR + 1.0, DOORH, DOORH + 1.0)):
        bx(m, "d48gold", x0, x1, y0, y1, FZ - 0.5, FZ + 0.3, bevel=0.08)
    for sx in (-1, 1):
        glow(m, "d48warm", sx * 9.2 - 0.5, sx * 9.2 + 0.5, 4.0, 7.0, FZ - 0.8, FZ - 0.2)
        bx(m, "d48gold", sx * 9.2 - 0.7, sx * 9.2 + 0.7, 7.0, 7.4, FZ - 1.0, FZ - 0.1, bevel=B2)
        bx(m, "d48gold", sx * 9.2 - 0.6, sx * 9.2 + 0.6, 3.6, 4.0, FZ - 0.9, FZ - 0.1, bevel=B2)


# ── 2. Боковая стена зала со всем, что на ней: пилястры, 4 ниши, светильники, пояс, карниз, подсветка ───────────
def build_side(sx, arch):
    m = model(f"D48_Side{'Arch' if arch else 'Closed'}_{'R' if sx > 0 else 'L'}")
    x0, x1 = sorted((sx * IX, sx * HW))
    top = CEIL + 1.4
    if arch:
        bx(m, "d48wall", x0, x1, 0, top, FZ, L.ARCH_Z0, bevel=0.08)
        bx(m, "d48wall", x0, x1, 0, top, L.ARCH_Z1, BZ, bevel=0.08)
        bx(m, "d48wall", x0, x1, L.ARCH_H, top, L.ARCH_Z0, L.ARCH_Z1, bevel=0.08)
        ax = sx * IX
        for z0, z1, y0, y1 in ((L.ARCH_Z0 - 0.5, L.ARCH_Z0, 0, L.ARCH_H + 0.5),
                               (L.ARCH_Z1, L.ARCH_Z1 + 0.5, 0, L.ARCH_H + 0.5),
                               (L.ARCH_Z0 - 0.5, L.ARCH_Z1 + 0.5, L.ARCH_H, L.ARCH_H + 0.5)):
            bx(m, "d48gold", *sorted((ax, ax - sx * 0.25)), y0, y1, z0, z1, bevel=B2)
        cz = (L.ARCH_Z0 + L.ARCH_Z1) / 2
        m.cylinder("Body", (ax - sx * 0.2, L.ARCH_H + 0.5, cz), 0.6, 0.3, "d48gold", axis="x", segments=20, bevel=0.04)
        bx(m, "d48navydark", *sorted((ax - sx * 0.25, ax - sx * 0.4)), L.ARCH_H + 1.1, L.ARCH_H + 2.1, L.ARCH_Z0,
           L.ARCH_Z1, bevel=B2)
        base = ((IZ0, L.ARCH_Z0), (L.ARCH_Z1, IZ1))
    else:
        bx(m, "d48wall", x0, x1, 0, top, FZ, BZ, bevel=0.08)
        bx(m, "d48wall", *sorted((sx * HW, sx * (HW + 1))), G, -0.02, FZ, BZ + 1, bevel=0.08)  # подиум
        base = ((IZ0, IZ1),)
    for z0, z1 in base:
        bx(m, "d48navy", *side_x(sx, 0, 0.2), 0, 1.0, z0, z1, bevel=B2)
    bx(m, "d48gold", *side_x(sx, 0, 0.2), 12.4, 12.7, IZ0, IZ1, bevel=B2)
    bx(m, "d48pil", *side_x(sx, 0, 0.5), 15.2, 16.0, IZ0, IZ1, bevel=B2)
    glow(m, "d48warm", *side_x(sx, 0.2, 0.45), 12.7, 12.9, IZ0 + 0.2, IZ1 - 0.2)
    for z in L.PIL_Z:  # пилястры: база, ствол с гранями, капитель ступенями
        bx(m, "d48navy", *side_x(sx, 0, 1.55), 0, 0.9, z - 0.55, z + 0.55, bevel=0.08)
        bx(m, "d48pil", *side_x(sx, 0, 1.3), 0.9, 11.6, z - 0.4, z + 0.4, bevel=0.08)
        bx(m, "d48gold", *side_x(sx, 0, 1.55), 11.6, 12.4, z - 0.55, z + 0.55, bevel=0.08)
    for i, cz in enumerate(L.NICHE_Z):  # ниши: фон, арочная перемычка, золотая ступень, светильник
        z0 = L.PIL_Z[i] + 0.4
        z1 = L.PIL_Z[i + 1] - 0.4 if i + 1 < len(L.PIL_Z) else IZ1
        bx(m, "d48backdrop", *side_x(sx, 0, 0.3), 0.9, 9.2, z0 + 0.05, z1 - 0.05, bevel=0.04)
        bx(m, "d48pil", *side_x(sx, 0, 1.1), 9.2, 10.4, z0, z1, bevel=0.08)
        bx(m, "d48gold", *side_x(sx, 0.3, 0.75), 8.6, 9.2, z0 + 0.05, z1 - 0.05, bevel=B2)
        bx(m, "d48gold", *side_x(sx, 1.1, L.NICHE_D + 0.2), 9.75, 10.0, cz - 0.15, cz + 0.15, bevel=0.03)
        m.cylinder("Body", (sx * (IX - L.NICHE_D), 9.5, cz), 0.45, 0.6, "d48navydark", segments=6, radius2=0.3,
                   bevel=0)
        m.cylinder("Glow", (sx * (IX - L.NICHE_D), 9.18, cz), 0.3, 0.06, "d48warm", segments=6, bevel=0)


# ── 3. Постамент (один меш на все 20 мест), урна, табличка — части в коде (SurfaceGui, состояние) ─────────────────
def build_plinth():
    m = model("D48_Plinth")
    hb, hd, hc, ht = L.BASE / 2, 2.3, 2.55, L.TOP / 2
    bx(m, "d48navy", -hb, hb, 0, 0.5, -hb, hb, bevel=0.1)
    bx(m, "d48pil", -hd, hd, 0.5, 2.6, -hd, hd, bevel=0.08)
    bx(m, "d48gold", -hc, hc, 2.6, 2.85, -hc, hc, bevel=0.06)
    bx(m, "d48pil", -ht, ht, 2.85, 3.0, -ht, ht, bevel=0.04)


def build_urn():
    m = model("D48_Urn")
    bx(m, "d48navy", -1.6, 1.6, 0, 1.2, -1.6, 1.6, bevel=0.1)
    m.cylinder("Body", (0, 1.45, 0), 0.7, 0.5, "d48gold", segments=20, radius2=0.5, bevel=0.04)
    m.sphere("Body", (0, 2.9, 0), 1.3, "d48gold", segments=12, rings=8, scale=(1, 0.95, 1))
    m.cylinder("Body", (0, 4.3, 0), 0.5, 0.8, "d48golddeep", segments=20, radius2=0.65, bevel=0.03)
    m.torus("Body", (0, 3.0, 0), 1.25, 0.12, "d48golddeep", axis="y", segments=28, minor_segments=6)


# ── 4. Павильон хранилища: портал, круглая дверь (открыта, декор), решётка доступа (створки), сканер ─────────────
def build_pavilion():
    m = model("D48_Pavilion")
    for x0, x1, y0, y1 in ((-PV_X, -STW, 0, 7.2), (STW, PV_X, 0, 7.2), (-PV_X, PV_X, 7.2, PV_H)):
        bx(m, "d48steel", x0, x1, y0, y1, PV_Z0, PV_Z0 + 0.6, bevel=0.08)
    for x0, x1, y0, y1 in ((-STW - 0.3, -STW, 0, 7.5), (STW, STW + 0.3, 0, 7.5), (-STW - 0.3, STW + 0.3, 7.2, 7.5)):
        bx(m, "d48gold", x0, x1, y0, y1, PV_Z0 - 0.15, PV_Z0 + 0.1, bevel=B2)
    for sx in (-1, 1):
        glow(m, "d48cyan", sx * 3.3 - 0.1, sx * 3.3 + 0.1, 0.5, 6.8, PV_Z0 - 0.1, PV_Z0)
    bx(m, "d48navydark", -3.3, 3.3, 7.75, 8.75, PV_Z0 - 0.15, PV_Z0, bevel=B2)
    bx(m, "d48steel", -PV_X, -PV_X + 0.6, 0, PV_H, PV_Z0 + 0.6, PV_Z1 - 0.6, bevel=0.08)
    bx(m, "d48steel", PV_X - 0.6, PV_X, 0, PV_H, PV_Z0 + 0.6, PV_Z1 - 0.6, bevel=0.08)
    bx(m, "d48steel", -PV_X, PV_X, 0, PV_H, PV_Z1 - 0.6, PV_Z1, bevel=0.08)
    for sx in (-1, 1):
        bx(m, "d48navy", *sorted((sx * WELL_X, sx * (PV_X - 0.6))), 0, 0.06, PV_Z0 + 0.6, PV_Z1 - 0.6, bevel=0)
        bx(m, "d48navy", *sorted((sx * PV_X, sx * (PV_X + 0.2))), 0, 0.8, PV_Z0 + 0.6, PV_Z1, bevel=0.04)
        bx(m, "d48gold", *sorted((sx * (PV_X - 0.05), sx * (PV_X + 0.25))), 0.8, PV_H, PV_Z1 - 0.5, PV_Z1 + 0.1,
           bevel=0.04)
    bx(m, "d48pil", -PV_X - 0.4, PV_X + 0.4, PV_H, PV_H + 0.6, PV_Z0 - 0.4, PV_Z1 + 0.4, bevel=0.08)
    bx(m, "d48gold", -PV_X - 0.6, PV_X + 0.6, PV_H + 0.6, PV_H + 0.9, PV_Z0 - 0.6, PV_Z1 + 0.6, bevel=0.06)
    bx(m, "d48navy", -3.4, 3.4, PV_H + 0.9, PV_H + 1.7, PV_Z0 + 0.6, PV_Z1 - 0.6, bevel=0.08)
    # круглая сейфовая дверь, распахнута на 90° (как в утверждённом v2): кольцо-тор, диск, штурвал, ригели
    HX, HZ, DR = PV_X, PV_Z0, 3.5
    dcx, dcz, dcy = HX + 0.45, HZ - DR - 0.1, 0.35 + DR
    m.torus("Body", (dcx + 0.1, dcy, dcz), DR - 0.05, 0.38, "d48gold", axis="x", segments=24, minor_segments=6)
    m.cylinder("Body", (dcx - 0.1, dcy, dcz), DR - 0.2, 0.6, "d48disk", axis="x", segments=24, bevel=0.1)
    m.torus("Glow", (dcx - 0.42, dcy, dcz), DR - 0.95, 0.06, "d48cyan", axis="x", segments=24, minor_segments=3)
    m.cylinder("Body", (dcx - 0.55, dcy, dcz), 1.3, 0.3, "d48gold", axis="x", segments=28, bevel=0.06)
    m.cylinder("Body", (dcx - 0.8, dcy, dcz), 0.5, 0.3, "d48steeldark", axis="x", segments=20, bevel=0.05)
    for k in range(3):
        m.box("Body", (dcx - 0.95, dcy, dcz), (0.24, 3.6, 0.28), "d48golddeep", bevel=0.04,
              rotation=Matrix.Rotation(math.radians(60 * k), 4, "X"))
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        m.cylinder("Body", (dcx - 0.5, dcy + math.sin(a) * 2.75, dcz + math.cos(a) * 2.75), 0.22, 0.2, "d48gold",
                   axis="x", segments=6, bevel=0)
    for hy in (1.8, 6.0):
        m.cylinder("Body", (HX + 0.25, hy, HZ - 0.25), 0.3, 1.0, "d48steeldark", segments=16, bevel=0.05)


def build_gate_leaf():
    """Створка дневной решётки хранилища (одна на обе стороны, вторая повёрнута на 180°): рама, прутья, эмблема.
    Начало — нижний внутренний угол у середины проёма; закрыта — стоит в проёме, открыта — уезжает в стену."""
    m = model("D48_GateLeaf")
    w, h = STW - 0.05, 7.1
    bx(m, "d48steeldark", 0, w, 0, 0.3, -0.1, 0.1, bevel=0.04)
    bx(m, "d48steeldark", 0, w, h - 0.3, h, -0.1, 0.1, bevel=0.04)
    bx(m, "d48steeldark", 0, 0.25, 0, h, -0.1, 0.1, bevel=0.04)
    bx(m, "d48steeldark", w - 0.25, w, 0, h, -0.1, 0.1, bevel=0.04)
    for k in range(5):
        x = 0.45 + k * (w - 0.9) / 4
        m.cylinder("Body", (x, h / 2, 0), 0.07, h - 0.6, "d48gold", segments=6, bevel=0.0)
    for y in (2.3, 4.8):
        bx(m, "d48gold", 0.25, w - 0.25, y - 0.08, y + 0.08, -0.08, 0.08, bevel=0.02)
    m.cylinder("Body", (w - 0.3, h * 0.55, -0.12), 0.45, 0.12, "d48gold", axis="z", segments=20, bevel=0.03)


def build_scanner():
    m = model("D48_Scanner")
    bx(m, "d48navydark", -0.5, 0.5, 0, 1.4, -0.12, 0.12, bevel=0.06)
    bx(m, "d48gold", -0.56, 0.56, -0.06, 0.06, -0.15, 0.15, bevel=0.03)
    m.box("Glow", (0, 0.85, -0.13), (0.7, 0.7, 0.04), "d48cyan", bevel=0)  # экран: цвет состояния ставит игра


# ── 5. Лестница: ступенчатый хребет одним мешем, стеклянные перила, золотые поручни ──────────────────────────────
def build_stair():
    m = model("D48_Stair")
    for k in range(1, 13):
        bx(m, "d48step", -STW, STW, VF, -k, ST0 + k - 1, ST0 + k, bevel=0.04)
        bx(m, "d48gold", -STW + 0.1, STW - 0.1, -k - 0.02, -k + 0.03, ST0 + k - 1.0, ST0 + k - 0.85, bevel=0)
    rot = Matrix.Rotation(math.radians(45), 4, "X")  # Blender X = Roblox x: спуск к +z
    mid_y, mid_z = -6.5 + 1.2, ST0 + 5.5
    length = 11.0 * math.sqrt(2) + 1.5
    for sx in (-1, 1):
        m.box("Glass", (sx * (STW + 0.1), mid_y, mid_z), (0.12, 2.1, length), "d48glass", bevel=0, rotation=rot)
        m.box("Body", (sx * (STW + 0.1), mid_y + 1.15, mid_z), (0.3, 0.25, length), "d48gold", bevel=0.05,
              rotation=rot)


# ── 6. Сундук и стенд у входа ──────────────────────────────────────────────────────────────────────────────────
def build_chest():
    m = model("D48_Chest")  # начало — центр основания; замок смотрит в +z (в зал)
    bx(m, "d48chest", -2.0, 2.0, 0, 1.9, -1.5, 1.5, bevel=0.12)
    bx(m, "d48chestlight", -2.1, 2.1, 1.9, 2.5, -1.6, 1.6, bevel=0.1)
    m.cylinder("Body", (0, 2.5, 0), 1.25, 3.7, "d48chest", axis="x", segments=12, bevel=0.06)
    for bxx in (-1.2, 1.2):
        bx(m, "d48gold", bxx - 0.18, bxx + 0.18, 0, 2.6, -1.62, 1.62, bevel=0.04)
    bx(m, "d48gold", -0.45, 0.45, 1.2, 2.2, 1.5, 1.7, bevel=0.05)
    glow(m, "d48cyan", -1.2, 1.2, 2.3, 2.4, 1.6, 1.66)
    for cxx in (-1.9, 1.9):
        for czz in (-1.4, 1.4):
            bx(m, "d48gold", cxx - 0.18, cxx + 0.18, 0, 0.5, czz - 0.18, czz + 0.18, bevel=0.04)


def build_stand():
    m = model("D48_Stand")
    bx(m, "d48navy", -0.9, 0.9, 0, 0.6, -0.7, 0.7, bevel=0.08)
    m.cylinder("Body", (0, 1.8, 0), 0.3, 2.4, "d48gold", segments=16, bevel=0.04)
    rot = Matrix.Rotation(math.radians(-20), 4, "X")
    m.box("Body", (0, 3.8, 0.1), (3.2, 2.0, 0.25), "d48navydark", bevel=0.06, rotation=rot)
    m.box("Glow", (0, 3.85, 0.27), (2.9, 1.7, 0.05), "d48screen", bevel=0, rotation=rot)


# ── 7. Галереи (с уровня 5): оболочка, 6 ниш у наружной стены, клумба снаружи ──────────────────────────────────
def build_gallery(sx):
    m = model(f"D48_Gallery_{'R' if sx > 0 else 'L'}")
    gx = lambda a, b: tuple(sorted((sx * a, sx * b)))  # noqa: E731
    bx(m, "d48floor", *gx(L.GAL_IN, L.GAL_OUT), G, 0, L.GAL_Z0, L.GAL_Z1, bevel=0.04)
    top = L.GAL_H + 1.0
    bx(m, "d48wall", *gx(L.GAL_IX, L.GAL_OUT), 0, top, L.GAL_Z0, L.GAL_Z1, bevel=0.08)
    bx(m, "d48wall", *gx(L.GAL_IN, L.GAL_IX), 0, top, L.GAL_Z0, L.GAL_IZ0, bevel=0.08)
    bx(m, "d48wall", *gx(L.GAL_IN, L.GAL_IX), 0, top, L.GAL_IZ1, L.GAL_Z1, bevel=0.08)
    bx(m, "d48wall", *gx(IX, L.GAL_IN), 0, top, L.GAL_Z0, FZ, bevel=0.08)  # вдоль портика
    bx(m, "d48navy", *gx(L.GAL_IX - 0.2, L.GAL_IX), 0, 1.0, L.GAL_IZ0, L.GAL_IZ1, bevel=B2)
    bx(m, "d48gold", *gx(L.GAL_IX - 0.25, L.GAL_IX), 9.6, 9.9, L.GAL_IZ0, L.GAL_IZ1, bevel=B2)
    bx(m, "d48navy", *gx(L.GAL_IN + 0.5, L.GAL_IN + 3.4), 0, 0.08, L.GAL_IZ0 + 0.6, L.GAL_IZ1 - 0.6, bevel=0.02)
    floor_model = m
    m = model(f"D48_GalleryRoof_{'R' if sx > 0 else 'L'}")
    bx(m, "d48pil", *gx(IX + 1.4, L.GAL_EAVE - 0.2), L.GAL_H + 1.0, L.GAL_H + 1.8, L.GAL_Z0 - 0.4, L.GAL_Z1 + 0.4,
       bevel=0.08)
    bx(m, "d48gold", *gx(IX + 1.4, L.GAL_EAVE), L.GAL_H + 1.8, L.GAL_H + 2.1, L.GAL_Z0 - 0.6, L.GAL_Z1 + 0.6,
       bevel=0.05)
    glow(m, "d48sky", *gx(L.GAL_IN + 0.6, L.GAL_IN + 3.6), L.GAL_H + 0.98, L.GAL_H + 1.0, L.GAL_IZ0 + 1,
         L.GAL_IZ1 - 1)
    m = floor_model
    # фасад галереи у портика: фриз, пилястры, медальон
    bx(m, "d48gold", *gx(L.GAL_IN, L.GAL_EAVE), L.GAL_H - 0.2, L.GAL_H + 0.6, L.GAL_Z0 - 0.3, L.GAL_Z0, bevel=0.05)
    for px in (L.GAL_IN + 0.8, L.GAL_OUT - 0.8):
        bx(m, "d48pil", *gx(px - 0.7, px + 0.7), 0, L.GAL_H - 0.2, L.GAL_Z0 - 0.4, L.GAL_Z0, bevel=0.08)
        bx(m, "d48gold", *gx(px - 0.85, px + 0.85), L.GAL_H - 1.2, L.GAL_H - 0.6, L.GAL_Z0 - 0.5, L.GAL_Z0,
           bevel=0.05)
    mid = (L.GAL_IN + L.GAL_OUT) / 2
    bx(m, "d48gold", *gx(mid - 2.6, mid + 2.6), 0.0, 7.8, L.GAL_Z0 - 0.35, L.GAL_Z0, bevel=0.06)  # глухая арка
    bx(m, "d48backdrop", *gx(mid - 2.1, mid + 2.1), 0.4, 7.3, L.GAL_Z0 - 0.45, L.GAL_Z0 - 0.3, bevel=0.04)
    m.cylinder("Body", (sx * mid, 5.4, L.GAL_Z0 - 0.5), 1.0, 0.12, "d48gold", axis="z", segments=20, bevel=0)
    bx(m, "d48pil", *gx(L.GAL_IN + 0.4, L.GAL_EAVE - 0.4), L.GAL_H + 2.1, L.GAL_H + 3.0, L.GAL_Z0 - 0.3,
       L.GAL_Z0 + 1.2, bevel=0.08)  # ступенчатый аттик над фасадом
    bx(m, "d48pil", *gx(mid - 2.4, mid + 2.4), L.GAL_H + 3.0, L.GAL_H + 3.7, L.GAL_Z0 - 0.2, L.GAL_Z0 + 1.0,
       bevel=0.08)
    for z in [(L.GAL_Z[i] + L.GAL_Z[j]) / 2 for i, j in ((2, 0), (0, 1), (1, 3), (3, 4), (4, 5))]:
        bx(m, "d48pil", *gx(L.GAL_OUT, L.GAL_OUT + 0.35), 0, L.GAL_H + 0.6, z - 0.45, z + 0.45, bevel=0.06)
        bx(m, "d48gold", *gx(L.GAL_OUT, L.GAL_OUT + 0.4), L.GAL_H - 0.6, L.GAL_H, z - 0.55, z + 0.55, bevel=0)
    # ниши у наружной стены
    for z in L.GAL_Z:
        px = sx * (L.GAL_IX - L.GAL_D)
        bx(m, "d48backdrop", *gx(L.GAL_IX - 0.3, L.GAL_IX), 0.9, 8.6, z - 2.75, z + 2.75, bevel=0.04)
        bx(m, "d48pil", *gx(L.GAL_IX - 0.8, L.GAL_IX), 8.6, 9.6, z - 3.0, z + 3.0, bevel=0.08)
        bx(m, "d48gold", *gx(L.GAL_IX - 0.55, L.GAL_IX - 0.3), 8.2, 8.6, z - 2.75, z + 2.75, bevel=0.03)
        m.cylinder("Body", (px, 9.55, z), 0.45, 0.5, "d48navydark", segments=6, radius2=0.3, bevel=0)
        m.cylinder("Glow", (px, 9.27, z), 0.3, 0.06, "d48warm", segments=6, bevel=0)
    # клумба снаружи: каменный бортик, земля, кусты шарами (у крайних участков закрывает щель до обрыва)
    p0, p1, ph = L.PLANTER
    bx(m, "d48stone", *gx(p0, p1), G, G + ph * 0.55, L.GAL_Z0, L.GAL_Z1, bevel=0.1)
    bx(m, "d48plantdark", *gx(p0 + 0.25, p1 - 0.25), G + ph * 0.55, G + ph * 0.62, L.GAL_Z0 + 0.25, L.GAL_Z1 - 0.25,
       bevel=0)
    z = L.GAL_Z0 + 2.0
    k = 0
    while z < L.GAL_Z1 - 1.5:
        y0 = G + ph * 0.62
        col = "d48plant" if k % 3 else "d48plantdark"
        bx(m, col, *gx((p0 + p1) / 2 - 0.95, (p0 + p1) / 2 + 0.95), y0, y0 + 1.3, z - 1.3, z + 1.3, bevel=0.2)
        bx(m, col, *gx((p0 + p1) / 2 - 0.6, (p0 + p1) / 2 + 0.6), y0 + 1.3, y0 + 2.0, z - 0.8, z + 0.8, bevel=0.15)
        z += 6.5
        k += 1


# ── 8. Хранилище: оболочка, сейф, терминал, стеллаж (×2), центр безопасности, ячейки (×2) ─────────────────────
def build_vault():
    m = model("D48_VaultShell")
    bx(m, "d48vfloor", -HW, HW, VF - 1.4, VF, FZ, BZ, bevel=0.04)
    bx(m, "d48vwall", -HW, -IX, VF, -SLAB, FZ, BZ, bevel=0.06)
    bx(m, "d48vwall", IX, HW, VF, -SLAB, FZ, BZ, bevel=0.06)
    bx(m, "d48vwall", -IX, IX, VF, -SLAB, FZ, IZ0, bevel=0.06)
    bx(m, "d48vwall", -IX, IX, VF, -SLAB, IZ1, BZ, bevel=0.06)
    for x0, x1, z0, z1 in ((-IX, -IX + 0.25, IZ0, IZ1), (IX - 0.25, IX, IZ0, IZ1), (-IX, IX, IZ0, IZ0 + 0.25)):
        bx(m, "d48gold", x0, x1, VF, VF + 0.5, z0, z1, bevel=0.04)
    for x in (-6.0, 6.0):
        bx(m, "d48gold", x - 0.12, x + 0.12, VF, VF + 0.04, IZ0 + 0.3, ST0 - 0.5, bevel=0)
    for x0, x1, z0, z1 in ((-IX, IX, IZ0, ST0), (-IX, -WELL_X, ST0, IZ1), (WELL_X, IX, ST0, IZ1),
                           (-WELL_X, WELL_X, WELL_Z1, IZ1)):
        bx(m, "d48vceil", x0, x1, VCEIL, -SLAB, z0, z1, bevel=0)
    for x in (-10.0, 10.0):
        glow(m, "d48cyan", x - 0.15, x + 0.15, VCEIL - 0.12, VCEIL, IZ0 + 0.5, IZ1 - 0.5)
    glow(m, "d48cyan", -IX + 0.5, IX - 0.5, VCEIL - 0.12, VCEIL, -4.0, -3.7)
    m.cylinder("Body", (0, VF + 7.8, IZ0 + 0.3), 1.8, 0.3, "d48gold", axis="z", segments=24, bevel=0.05)
    m.cylinder("Body", (0, VF + 7.8, IZ0 + 0.5), 1.3, 0.2, "d48navy", axis="z", segments=24, bevel=0.03)

    s = model("D48_Safe")  # начало — центр двери на задней стене хранилища (z = IZ1), ось двери — z
    SY = 5.0
    bx(s, "d48navydark", -5.2, 5.2, -SY, -SY + 10.2, -0.4, 0, bevel=0.06)
    s.torus("Body", (0, 0, -0.6), 3.95, 0.35, "d48gold", axis="z", segments=20, minor_segments=5)
    s.torus("Glow", (0, 0, -0.85), 3.55, 0.08, "d48cyan", axis="z", segments=28, minor_segments=4)
    s.cylinder("Body", (0, 0, -1.1), 3.6, 0.6, "d48disk", axis="z", segments=28, bevel=0.12)
    s.cylinder("Body", (0, 0, -1.55), 1.3, 0.3, "d48gold", axis="z", segments=24, bevel=0.06)
    s.cylinder("Body", (0, 0, -1.85), 0.5, 0.3, "d48steeldark", axis="z", segments=20, bevel=0.05)
    s.torus("Body", (0, 0, -1.95), 1.8, 0.13, "d48golddeep", axis="z", segments=24, minor_segments=6)
    for k in range(3):
        s.box("Body", (0, 0, -1.95), (3.8, 0.28, 0.25), "d48golddeep", bevel=0.04,
              rotation=Matrix.Rotation(math.radians(60 * k), 4, "Y"))
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        s.cylinder("Body", (math.cos(a) * 3.1, math.sin(a) * 3.1, -1.45), 0.25, 0.2, "d48gold", axis="z", segments=6,
                   bevel=0)
    for sxx in (-1, 1):
        glow(s, "d48warm", sxx * 5.6 - 0.2, sxx * 5.6 + 0.2, -SY, -SY + 9.6, -0.3, 0)
    bx(s, "d48navy", -3.6, 3.6, -SY + 9.3, -SY + 10.0, -0.55, -0.4, bevel=0.04)

    t = model("D48_Terminal")  # начало — середина торца лестницы на полу хранилища (z = ST0), экран смотрит в −z
    bx(t, "d48navydark", -2.45, 2.45, 3.6, 9.6, -0.3, 0, bevel=0.08)
    glow(t, "d48screen", -2.15, 2.15, 3.9, 9.3, -0.36, -0.3)
    for x0, x1, y0, y1 in ((-1.0, 1.0, 5.3, 6.9), (-0.45, 0.45, 6.9, 7.3)):
        glow(t, "d48white", x0, x1, y0, y1, -0.42, -0.36)
    bx(t, "d48navy", -2.2, 2.2, 0, 2.5, -2.4, -1.0, bevel=0.08)
    t.box("Body", (0, 2.75, -1.7), (4.6, 0.25, 1.8), "d48gold", bevel=0.05,
          rotation=Matrix.Rotation(math.radians(-15), 4, "X"))
    t.box("Glow", (0, 2.92, -1.72), (4.0, 0.06, 1.4), "d48cyan", bevel=0,
          rotation=Matrix.Rotation(math.radians(-15), 4, "X"))

    a = model("D48_Archive")  # стеллаж у стены: начало — у стены на полу, полки смотрят в +x
    bx(a, "d48steeldark", 0, 0.3, 0, 8.6, -3.4, 3.4, bevel=0.04)
    for zz in (-3.4, 3.1):
        bx(a, "d48gold", 0, 2.35, 0, 8.6, zz, zz + 0.3, bevel=0.05)
    for lvl in range(3):
        y = 0.6 + lvl * 2.75
        bx(a, "d48steellight", 0, 2.35, y - 0.2, y, -3.1, 3.1, bevel=0.04)
        for n, oz in enumerate((-1.5, 1.5)):
            col = ("d48rare", "d48epic", "d48legend")[(lvl + n) % 3]
            a.cylinder("Glass", (1.2, y + 0.95, oz), 0.75, 1.9, col, segments=12, bevel=0)
            a.cylinder("Body", (1.2, y + 0.06, oz), 0.82, 0.12, "d48gold", segments=12, bevel=0)

    c = model("D48_Security")  # начало — центр хранилища на полу (как VaultShell, поднято на VF)
    bx(c, "d48navy", 12.8, 15.6, 2.5, 2.8, -8.0, 0.0, bevel=0.06)
    bx(c, "d48gold", 12.7, 15.7, 2.35, 2.55, -8.1, 0.1, bevel=0.04)
    bx(c, "d48navydark", 13.4, 15.6, 0, 2.35, -7.8, -0.2, bevel=0.06)
    for k, mz in enumerate((-6.2, -4.0, -1.8)):
        bx(c, "d48navydark", 13.6, 13.9, 3.2, 5.2, mz - 1.0, mz + 1.0, bevel=0.05)
        glow(c, ("d48screen", "d48cyan", "d48screen")[k], 13.5, 13.6, 3.35, 5.05, mz - 0.85, mz + 0.85)
        c.cylinder("Body", (13.75, 2.95, mz), 0.15, 0.35, "d48steeldark", segments=10, bevel=0)
    bx(c, "d48navydark", IX - 0.3, IX, 5.4, 10.2, -9.0, 1.0, bevel=0.05)
    glow(c, "d48screen", IX - 0.36, IX - 0.3, 5.7, 9.9, -8.7, 0.7)
    for y0, y1, z0, z1 in ((9.1, 9.25, -7.6, -0.4), (6.4, 6.55, -7.6, -0.4)):
        glow(c, "d48cyan", IX - 0.42, IX - 0.36, y0, y1, z0, z1)
    glow(c, "d48red", IX - 0.42, IX - 0.36, 7.5, 8.0, -3.0, -2.5)
    bx(c, "d48red", 10.4, 11.8, 0, 1.0, -4.8, -3.2, bevel=0.15)
    bx(c, "d48red", 10.4, 10.7, 1.0, 3.6, -4.8, -3.2, bevel=0.12)
    c.cylinder("Body", (11.1, 0.5, -4.0), 0.25, 1.0, "d48steeldark", segments=10, bevel=0)
    c.cylinder("Body", (8.0, 1.3, -9.4), 0.7, 2.6, "d48navy", segments=20, bevel=0.06)
    c.cylinder("Body", (8.0, 3.3, -9.4), 1.1, 0.2, "d48gold", axis="z", segments=24, bevel=0.04)
    c.cylinder("Glow", (8.0, 3.3, -9.52), 0.8, 0.06, "d48cyan", axis="z", segments=24, bevel=0)

    k = model("D48_Lockers")  # стенка банковских ячеек: начало — левый нижний угол у стены, дверцы смотрят в +z
    bx(k, "d48gold", 0, 7.9, 0, 6.5, 0, 0.35, bevel=0.05)
    for col in range(3):
        for row in range(2):
            lx, ly = 0.2 + col * 2.53, 0.35 + row * 3.05
            bx(k, "d48locker" if (col + row) % 2 == 0 else "d48vpanel", lx, lx + 2.4, ly, ly + 2.85, 0.35, 0.6,
               bevel=0.06)
            bx(k, "d48gold", lx + 1.75, lx + 2.05, ly + 1.2, ly + 1.6, 0.6, 0.75, bevel=0)


# ── Постройка всех модулей ─────────────────────────────────────────────────────────────────────────────────────
K.reset("WORKBENCH" if FAST else "EEVEE", 64)
build_hall()
for sx in (-1, 1):
    build_side(sx, False)
    build_side(sx, True)
    build_gallery(sx)
build_plinth()
build_urn()
build_pavilion()
build_gate_leaf()
build_scanner()
build_stair()
build_chest()
build_stand()
build_vault()

lib = K.coll("Library")
LAYOUT, OBJECTS = {}, {}
spread = 0.0
for name, m in MODELS.items():
    layout = m.build(lib, offset=(spread, 0, 400))  # в FBX модули разнесены, чтобы не наслаивались при импорте
    LAYOUT[name] = {"roles": layout, "triangles": sum(r["triangles"] for r in layout.values())}
    OBJECTS[name] = [o for o in lib.objects if o.name.startswith(name + "_")]
    spread += 80.0


# UV: проекция на грань в стадах (1 UV = 8 стадов, StudsPerTile LegoSquaresSoft)
def uv_box(obj, studs=8.0):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for loop in f.loops:
            co = loop.vert.co
            u, v = [(co.y, co.z), (co.x, co.z), (co.x, co.y)][ax]
            loop[uv].uv = (u / studs, v / studs)
    bm.to_mesh(obj.data)
    bm.free()


for objs in OBJECTS.values():
    for o in objs:
        uv_box(o)

all_objs = [o for objs in OBJECTS.values() for o in objs]
lego.export_fbx(os.path.join(REPO, "assets", "models", f"{PACK}.fbx"), all_objs)
lego.write_json(os.path.join(REPO, "assets", "models", f"{PACK}.layout.json"), {"d48": LAYOUT})
for o in all_objs:
    o.location = (0, 0, 0)  # для сборки сцен — модули в своих осях
print("MODULES", {n: v["triangles"] for n, v in LAYOUT.items()}, flush=True)


# ── Расстановка модулей по уровням (контракт для MeshVisual, фаза 3) ───────────────────────────────────────────
def placements(level):
    galleries = level >= L.GALLERY_LEVEL
    out = [("D48_Hall", (0, 0, 0), 0), ("D48_Roof", (0, 0, 0), 0), ("D48_Pavilion", (0, 0, 0), 0), ("D48_Stair", (0, 0, 0), 0),
           ("D48_VaultShell", (0, 0, 0), 0), ("D48_Safe", (0, VF + 5.0, IZ1), 0),
           ("D48_Terminal", (0, VF, ST0), 0), ("D48_Security", (0, VF, 0), 0),
           ("D48_Archive", (-IX + 0.25, VF, -6.0), 0), ("D48_Archive", (-IX + 0.25, VF, 9.0), 0),
           ("D48_Lockers", (-11.9, VF, IZ0), 0), ("D48_Lockers", (4.0, VF, IZ0), 0),
           ("D48_Chest", (L.CHEST["center"][0], 0, L.CHEST["center"][1]), 0),
           ("D48_Stand", (L.STAND["center"][0], 0, L.STAND["center"][1]), 0),
           ("D48_GateLeaf", (-STW + 0.02, 0, PV_Z0 + 0.3), 0), ("D48_GateLeaf", (STW - 0.02, 0, PV_Z0 + 0.3), 180),
           ("D48_Scanner", (-PV_X + 0.95, 2.6, PV_Z0 - 0.15), 0)]
    for sx, tag in ((-1, "L"), (1, "R")):
        out.append((f"D48_Side{'Arch' if galleries else 'Closed'}_{tag}", (0, 0, 0), 0))
        if galleries:
            out.append((f"D48_Gallery_{tag}", (0, 0, 0), 0))
            out.append((f"D48_GalleryRoof_{tag}", (0, 0, 0), 0))
    for p in L.places():
        x, _, z = p["center"]
        if p["zone"] == "gallery" and not galleries:
            continue
        if p["slot"] in (7, 8) and level < p["unlock_compat"]:
            out.append(("D48_Urn", (x, 0, z), 0))
            continue
        out.append(("D48_Plinth", (x, 0, z), 0))
    return out


placement_json = {}
for level in range(1, 11):
    items = placements(level)
    tris = sum(LAYOUT[n]["triangles"] for n, _, _ in items)
    meshparts = sum(len(LAYOUT[n]["roles"]) for n, _, _ in items)
    placement_json[str(level)] = {"open": L.slots_compat(level), "triangles": tris, "meshparts": meshparts,
                                  "items": [{"model": n, "position": list(p), "yaw": y} for n, p, y in items]}
with open(os.path.join(C2, "mesh_placement.json"), "w", encoding="utf-8") as f:
    json.dump({"pack": PACK, "note": "позиции — оси участка (центр на полу зала, вход −Z); yaw — градусы вокруг y; "
                                     "решётка: створки уезжают в стену на 2.6 по x", "levels": placement_json}, f,
              ensure_ascii=False, indent=1)
print("LEVELS", {k: (v["triangles"], v["meshparts"]) for k, v in placement_json.items()}, flush=True)

if NO_RENDER:
    sys.exit(0)

# ── Сцена для рендеров: модули по местам, материал пупырышков как в игре ───────────────────────────────────────
SOFT_COLOR = os.path.join(REPO, "assets", "textures", "lego_squares_soft_color.png")
SOFT_NORMAL = os.path.join(REPO, "assets", "textures", "lego_squares_soft_normal.png")
_mat_cache = {}


def preview_material(code, kind):
    key = (code, kind)
    if key in _mat_cache:
        return _mat_cache[key]
    mat = bpy.data.materials.new(f"PV_{kind}_{code}")
    mat.use_nodes = True
    nt = mat.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    rgb = [int(code[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    if kind == "Neon":
        b.inputs["Base Color"].default_value = (*lin, 1)
        b.inputs["Emission Color"].default_value = (*lin, 1)
        b.inputs["Emission Strength"].default_value = 3.0
    elif kind == "Glass":
        b.inputs["Base Color"].default_value = (*lin, 1)
        b.inputs["Alpha"].default_value = 0.6
        b.inputs["Roughness"].default_value = 0.08
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
    else:
        b.inputs["Roughness"].default_value = 0.55
        uvn = nt.nodes.new("ShaderNodeUVMap")
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(SOFT_COLOR, check_existing=True)
        nt.links.new(uvn.outputs["UV"], tex.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        mix.inputs["Fac"].default_value = 1.0
        mix.inputs["Color2"].default_value = (*lin, 1)
        nt.links.new(tex.outputs["Color"], mix.inputs["Color1"])
        nt.links.new(mix.outputs["Color"], b.inputs["Base Color"])
        ntex = nt.nodes.new("ShaderNodeTexImage")
        ntex.image = bpy.data.images.load(SOFT_NORMAL, check_existing=True)
        ntex.image.colorspace_settings.name = "Non-Color"
        nt.links.new(uvn.outputs["UV"], ntex.inputs["Vector"])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = 0.8
        nt.links.new(ntex.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    _mat_cache[key] = mat
    return mat


for name, objs in OBJECTS.items():
    for o in objs:
        role = o.name[len(name) + 1:]
        info = LAYOUT[name]["roles"][role]
        o.data.materials.clear()
        o.data.materials.append(preview_material(info["color"], info["material"]))
lib.hide_render = True
lib.hide_viewport = True

GROUP_OF = {"D48_VaultShell": "Vault", "D48_Safe": "Vault", "D48_Terminal": "Vault", "D48_Security": "VaultNear",
            "D48_Archive": "Vault", "D48_Lockers": "VaultFront", "D48_Stair": "Stair", "D48_Hall": "Hall",
            "D48_Pavilion": "Pavilion", "D48_GateLeaf": "Gate", "D48_Scanner": "Pavilion", "D48_Roof": "Roof",
            "D48_GalleryRoof_L": "Roof", "D48_GalleryRoof_R": "Roof",
            "D48_Chest": "Hall", "D48_Stand": "Hall"}


def place_scene(level):
    """Ставит копии модулей уровня level (общие меши) в коллекции «L<level>_<группа>»."""
    made = []
    for name, pos, yaw in placements(level):
        grp = GROUP_OF.get(name)
        if grp is None:
            grp = ("SideR" if name.endswith("_R") else "SideL") if name.startswith(("D48_Side", "D48_Gallery")) else \
                ("PlacesR" if pos[0] > 0 else "PlacesL")
        col = K.coll(f"L{level}_{grp}")
        for src in OBJECTS[name]:
            o = bpy.data.objects.new(src.name + "_i", src.data)
            o.matrix_world = Matrix.Translation(K.R(*pos)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")
            col.objects.link(o)
            made.append(o)
    return made


# Состояния мест (части в коде игры): табличка, полоса редкости, стекло / голограмма / покрывало, надписи
RARITY = {"Common": "C4C0CE", "Rare": "4FA6EA", "Epic": "B266F5", "Legendary": "F7B731"}
ITEMS = {1: ("Moai", "ГОЛОВА МОАИ", "Common", 16), 4: ("TutMask", "МАСКА ТУТАНХАМОНА", "Epic", 150),
         5: ("Vase", "ВАЗА", "Rare", 25), 7: ("StatueOfLiberty", "СТАТУЯ СВОБОДЫ", "Epic", 165),
         9: ("GreatSphinx", "БОЛЬШОЙ СФИНКС", "Rare", 45), 10: ("NefertitiBust", "БЮСТ НЕФЕРТИТИ", "Rare", 48),
         12: ("Colosseum", "КОЛИЗЕЙ", "Rare", 55), 13: ("AnubisStatue", "СТАТУЯ АНУБИСА", "Common", 13),
         15: ("TerracottaWarrior", "ТЕРРАКОТОВЫЙ ВОИН", "Common", 12), 18: ("EgyptianCat", "ЕГИПЕТСКАЯ КОШКА", "Common", 10)}


def state_parts(level, collection_prefix):
    open_n = L.slots_compat(level)
    shown = {k: v for k, v in ITEMS.items() if k <= open_n and (level >= 5 or k in (1, 4, 5))}
    filled = []
    for p in L.places():
        if p["zone"] == "gallery" and level < L.GALLERY_LEVEL:
            continue
        if p["slot"] in (7, 8) and level < p["unlock_compat"]:
            continue
        x, _, cz = p["center"]
        sx = 1 if x > 0 else -1
        K.group(f"{collection_prefix}_{'PlacesR' if sx > 0 else 'PlacesL'}")
        item = shown.get(p["slot"])
        state = "filled" if (p["slot"] <= open_n and item) else ("free" if p["slot"] <= open_n else "locked")
        face = x - sx * 2.3
        fx0, fx1 = (face - 0.12, face) if sx > 0 else (face, face + 0.12)
        K.box("Plaque", fx0, fx1, 1.0, 2.2, cz - 1.5, cz + 1.5, "1A2440", record=False, bevel=0.04)
        strip = {"filled": RARITY[item[2]] if item else "39E1FF", "free": "39E1FF", "locked": "FFB347"}[state]
        K.box("Strip", fx0 - (0.03 if sx > 0 else 0), fx1 + (0 if sx > 0 else 0.03), 2.2, 2.32, cz - 1.5, cz + 1.5,
              strip, "Neon", glow=2.5, record=False, bevel=0)
        tf, tx = ("-x" if sx > 0 else "+x"), face - sx * 0.14
        if state == "filled":
            K.box("Glow", x - 1.9, x + 1.9, 3.0, 3.05, cz - 1.9, cz + 1.9, "E9B43C", "Glass", alpha=0.55, bevel=0,
                  record=False)
            K.text("Name", item[1], (tx, 1.85, cz), 0.26 if len(item[1]) > 14 else 0.32, "FFFFFF", tf)
            K.text("Income", f"+{item[3]} $/сек", (tx, 1.38, cz), 0.3, "7CFF6B", tf)
            filled.append((p, item, sx))
        elif state == "free":
            K.box("Glow", x - 1.9, x + 1.9, 3.0, 3.05, cz - 1.9, cz + 1.9, "39E1FF", "Glass", alpha=0.45, bevel=0,
                  record=False)
            K.part("Holo", "Block", (0.9, 0.9, 0.9), (x, 4.3, cz), "39E1FF", "Glass", alpha=0.5,
                   rot=K.rot_y(45) @ K.rot_x(35.26) @ K.rot_z(45), bevel=0.04, record=False)
            K.text("Free", "СВОБОДНО", (tx, 1.82, cz), 0.3, "39E1FF", tf, glow=1.2)
            K.text("Slot", f"место {p['slot']}", (tx, 1.38, cz), 0.22, "C9D6F2", tf, weight="Bold")
        else:
            K.box("Cover", x - 2.2, x + 2.2, 3.0, 3.25, cz - 2.2, cz + 2.2, "2E4377", record=False, bevel=0.08)
            K.text("Lock", "ЗАКРЫТО", (tx, 1.82, cz), 0.3, "FFB347", tf, glow=1.0)
            K.text("Lvl", f"уровень {p['unlock_compat']}", (tx, 1.38, cz), 0.24, "F2D7A8", tf, weight="Bold")
    return filled


TEX = os.path.join(REPO, "assets", "textures", "art")
FBX_B1 = os.path.join(REPO, "assets", "models", "Art_Boss1_MuseumOfWonders.fbx")


def item_material(name, color_png, normal_png):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Roughness"].default_value = 0.5
    col = nt.nodes.new("ShaderNodeTexImage")
    col.image = bpy.data.images.load(color_png, check_existing=True)
    nt.links.new(col.outputs["Color"], b.inputs["Base Color"])
    if os.path.exists(normal_png):
        nrm = nt.nodes.new("ShaderNodeTexImage")
        nrm.image = bpy.data.images.load(normal_png, check_existing=True)
        nrm.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


def fbx_objects(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.type == "MESH":
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    return [o for o in new if o.name in bpy.data.objects]


def put_item(objs, px, cz, sx, collection, height=None):
    def bounds():
        bpy.context.view_layer.update()
        lo = Vector([min(min((o.matrix_world @ v.co)[i] for v in o.data.vertices) for o in objs) for i in range(3)])
        hi = Vector([max(max((o.matrix_world @ v.co)[i] for v in o.data.vertices) for o in objs) for i in range(3)])
        return lo, hi
    lo, hi = bounds()
    if height:
        for o in objs:
            o.scale = o.scale * (height / (hi.z - lo.z))
    for o in objs:
        o.rotation_euler.z += math.radians(-90 if sx > 0 else 90)
    lo, hi = bounds()
    target = K.R(px, 3.0, cz)
    shift = Vector((target.x - (lo.x + hi.x) / 2, target.y - (lo.y + hi.y) / 2, target.z - lo.z))
    for o in objs:
        o.location += shift
        for c in list(o.users_collection):
            c.objects.unlink(o)
        collection.objects.link(o)


def items_for(level, filled):
    library = {o.name: o for o in fbx_objects(FBX_B1)}
    used = set()
    for p, item, sx in filled:
        x, _, cz = p["center"]
        col = K.coll(f"L{level}_{'PlacesR' if sx > 0 else 'PlacesL'}")
        if item[0] == "Vase":
            objs = fbx_objects(os.path.join(REPO, "assets", "models", "ArtV13_Vase.fbx"))
            m = item_material("Item_Vase", os.path.join(TEX, "v13_vase_color.png"),
                              os.path.join(TEX, "v13_vase_normal.png"))
            for o in objs:
                o.data.materials.clear()
                o.data.materials.append(m)
            put_item(objs, x, cz, sx, col, 3.2)
            continue
        src = library.get(f"Art_{item[0]}")
        if src is None:
            continue
        used.add(src.name)
        src.data.materials.clear()
        src.data.materials.append(item_material(f"Item_{item[0]}", os.path.join(TEX, f"{item[0]}_color.png"),
                                                os.path.join(TEX, f"{item[0]}_normal.png")))
        put_item([src], x, cz, sx, col)
    for name, o in library.items():
        if name not in used and name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)


# окружение: трава с вырезом под хранилище, участок, дорожка
K.group("Ground")
GRASS = K.rings("7FC75A", 4.0, 0.12)
for nm, x0, x1, z0, z1 in (("GrassF", -90, 90, -90, FZ), ("GrassB", -90, 90, BZ, 60), ("GrassL", -90, -HW, FZ, BZ),
                           ("GrassR", HW, 90, FZ, BZ)):
    K.box(nm, x0, x1, G - 2, G, z0, z1, "7FC75A", look=GRASS, record=False, bevel=0,
          cname="GroundNear" if nm == "GrassR" else "Ground")
K.box("Path", -4, 4, G, G + 0.08, -80, PORTICO_Z, "E9E2D2", record=False, bevel=0.02, cname="Ground")
K.sky()
K.sun()
for x in (-8.0, 8.0):
    for z in (-6.0, 6.0):
        K.light("HallFill", "AREA", (x, CEIL - 0.2, z), 900, "FFF4E2", 7.0, (x, 0, z), shadow=False)
K.light("SkyFill", "AREA", (0, CEIL - 0.7, 0.0), 1800, "EAF7FF", 9.0, (0, 0, 0.0))
K.light("Entry", "AREA", (0, 9.0, FZ - 3.0), 600, "FFF4E2", 6.0, (0, 4, 0), shadow=False)
for sx in (-1, 1):
    for z in (-12.0, 0.0, 13.0):
        K.light("GalFill", "AREA", (sx * 21.5, L.GAL_H - 0.3, z), 520, "FFF4E2", 6.0, (sx * 21.5, 0, z), shadow=False,
                cname="LightsGal")
K.light("PvInside", "AREA", (0, PV_H - 0.3, 6.5), 500, "FFE7B8", 4.0, (0, -6, 9), shadow=False)
K.light("StairMid", "AREA", (0, -3.0, 12.0), 650, "FFE7B8", 5.0, (0, -12, 12.0), shadow=False)
for x, z in ((-9.0, -6.0), (9.0, -6.0), (-9.0, 9.0), (9.0, 9.0), (0.0, -1.0)):
    K.light("VaultFill", "AREA", (x, VCEIL - 0.3, z), 750, "E6F4FF", 6.0, (x, VF, z), shadow=False)
K.light("SafeKey", "SPOT", (0, -3.0, 13.0), 2600, "FFD88A", target=(0, VF + 5.0, IZ1), spot=55)
K.light("TermKey", "SPOT", (0, -3.2, -4.0), 900, "E6F4FF", target=(0, VF + 6, ST0), spot=60)
for p in L.places():
    x, _, cz = p["center"]
    K.light("Spot", "SPOT", (x, 8.6 if p["zone"] == "gallery" else 9.3, cz), 700, "FFE7C2", target=(x, 3.0, cz),
            spot=46, cname="LightsGal" if p["zone"] == "gallery" else "Lights")
K.mannequin(-1.6, -6.0, math.radians(20))
K.mannequin(7.4, 6.0, math.radians(-90), shirt="E0533E")
K.mannequin(20.0, -2.0, math.radians(-90), shirt="F2B33D", cname="PeopleGal")
K.mannequin(3.5, -6.0, math.radians(200), y=VF, shirt="4CB860")
K.camera()

SCENES = {}
for level in (1, 10):
    place_scene(level)
    SCENES[level] = state_parts(level, f"L{level}")
    items_for(level, SCENES[level])

PCT = 50 if FAST else 100


def shot(level, name, eye, at, fov=70, res=(1600, 900), hidden=(), ortho=None, top=False):
    tag = f"L{level}_{name}"
    if ONLY and tag not in ONLY and name not in ONLY:
        return
    other = 10 if level == 1 else 1
    hide = {n for n in K.S["coll"] if n.startswith(f"L{other}_")} | {"Library"}
    hide |= {f"L{level}_{h}" for h in hidden} | {h for h in hidden}
    if level < L.GALLERY_LEVEL:
        hide |= {"PeopleGal", "LightsGal"}
    K.show_only(hide)
    lib.hide_render = True
    K.shot(os.path.join(RENDERS, tag + ".png"), eye, at, fov, res, ortho, PCT, top_down=top)


for level in (1, 10):
    shot(level, "exterior", (-38, 12, -64), (2, 7, -12), 52)
    shot(level, "hall_from_entrance", (0, 6.2, -16.0), (0, 4.2, 8), 76)
    shot(level, "hall_inside", (0, 9.0, -10.4), (0, 2.6, 13.0), 80)
    shot(level, "overview", (44, 58, -50), (1.5, -1, 1.5), 46, hidden=("Roof",))
shot(10, "gallery", (20.4, 6.2, -14.4), (24.6, 3.0, 14.0), 72)
shot(10, "gallery_arch", (-2.0, 6.0, -8.0), (-20.0, 4.0, -8.4), 70)
shot(10, "vault_gate", (-5.5, 6.0, -9.0), (1.0, 4.0, 2.6), 60)
shot(10, "stair_down", (0, 5.6, 2.0), (0, -8.0, 17.5), 70, hidden=("Gate",))
shot(10, "vault_safe", (5.0, -7.0, 11.5), (0, -8.2, 19.3), 70, hidden=("Gate",))
shot(10, "vault_main", (10.0, -6.5, 15.5), (-3.0, -8.8, -7.0), 76, hidden=("Gate",))
shot(10, "vault_overview", (26, 30, -30), (0, -14, 3), 44,
     hidden=("Roof", "Hall", "SideL", "SideR", "Pavilion", "Gate", "PlacesL", "PlacesR", "Ground", "GroundNear",
             "VaultNear", "VaultFront", "Lights", "LightsGal", "People", "PeopleGal"))
shot(10, "plinth_states", (20.4, 5.4, -1.0), (24.7, 3.2, -13.0), 46, (1100, 1100))
shot(10, "plan", (0, 140, -0.6), (0, 0, -0.599), 0, (1300, 1300), ("Roof", "People", "PeopleGal"), 66, True)
shot(1, "plan", (0, 140, -0.6), (0, 0, -0.599), 0, (1300, 1300), ("Roof", "People"), 66, True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C2, "d48_final.blend"))
