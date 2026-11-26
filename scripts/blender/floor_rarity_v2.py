"""Лист Б v2 (D74): редкость этажа — модуль небоскрёба, а не стиль. Названия Деревянный … Космический — только ярлыки.

Правила (владелец 2026-11-26):
  1. Этаж — модуль башни: след точно по сетке (FX × FZ), плита снизу и плита сверху; выше верхней плиты — ничего
     (проверка CHECK_TOP ниже: ни одна деталь этажа не выше Y его верхней плиты).
  2. Рост по редкости — внутри своей высоты: ×1 / 1.35 / 1.6 / 1.9 / 2.3 / 3 от FloorHeight 20 (ярус, двусветный зал,
     галереи).
  3. Вынос за контур — только вбок и в своей полосе высоты (балконы, террасы-консоли, навесы, вывески); предел — OUT.
  4. Купола, шпили, короны — только у общей кровли башни («колпак»): CAP_A / CAP_B / CAP_C, богатство — по лучшему
     этажу.
  5. Тема одна на все 6 редкостей; редкость — насколько этаж больше и богаче: ярусы, галереи, балконы по периметру,
     свет в окнах, большое остекление, крупнее знак темы, на высших — «геройский» объект темы.
  6. Маркер редкости — цветной кант по торцам плит перекрытия (KANT), одинаковый для любой темы.
  7. Без религиозной архитектуры и замков.
Только концепт на утверждение: в игру не экспортируется, файлы этажей не меняет.

Запуск (две темы, вторая собирает башню):
  blender -b --factory-startup --python scripts/blender/floor_rarity_v2.py -- <репо> <папка> aquarium
  blender -b --factory-startup --python scripts/blender/floor_rarity_v2.py -- <репо> <папка> saloon tower
"""

import math
import os
import runpy
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import floorkit as K  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT, THEME = os.path.abspath(argv[0]), os.path.abspath(argv[1]), argv[2]
TOWER = "tower" in argv[3:]
TIER_SHOTS = "notiers" not in argv[3:]
THEMES = {
    "saloon": {
        "script": "floor_cactusboxer.py", "prefix": "CB", "title": "Кактус-боксёр (салун)",
        "wall": "9A6A3E", "wall2": "835632", "trim": "5A3A20", "accent": "C0392B", "accent2": "F2E6D0",
        "glass": "FFD98A", "sign": "glove", "style": "planks",
    },
    "aquarium": {
        "script": "floor_aquarium.py", "prefix": "AQ", "title": "Верблюд-аквариум (океанариум)",
        "wall": "1E3A6E", "wall2": "264A86", "trim": "2FC4B2", "accent": "F2E6C8", "accent2": "FF8A3D",
        "glass": "9FE6F2", "sign": "fish", "style": "portholes",
    },
}
TH = THEMES[THEME]
os.makedirs(OUT, exist_ok=True)

# базовый этаж темы: сборка без двора (след точно по сетке) и сцена показа без кадров; для башни — готовые файлы
# прогонов тем (<тема>_base.blend), чтобы не собирать этажи заново
if TOWER:
    bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, THEME + "_base.blend"))
else:
    sys.argv = [sys.argv[0], "--", REPO, OUT, "render", "shot=__none__", "noyard"]
    runpy.run_path(os.path.join(HERE, TH["script"]), run_name="__main__")
scene = bpy.context.scene
for name in ("TowerAbove", "TowerBelow"):
    if name in bpy.data.objects:
        bpy.data.objects[name].hide_render = True
BASE = [o for o in bpy.data.objects if o.name.startswith(TH["prefix"] + "_F_") or o.name.startswith(TH["prefix"] + "_I_")]
for o in bpy.data.objects:  # силуэт, оригинал предмета и лампы зала в кадрах снаружи не нужны
    if o.name.startswith(TH["prefix"] + "_S_") or o.name == "ItemRoot" or (o.parent and o.parent.name == "ItemRoot"):
        o.hide_render = True

# ── числа системы ─────────────────────────────────────────────────────────────────────────────────────────────
NAMES = ["Деревянный", "Каменный", "Мраморный", "Золотой", "Мифический", "Космический"]
HEIGHT_K = [1, 1.35, 1.6, 1.9, 2.3, 3]
H = [round(20 * k) for k in HEIGHT_K]  # 20 27 32 38 46 60
OUT_SIDE = [0, 2, 3, 4, 5, 6]  # предел выноса вбок, стадов (сверх выноса базового этажа)
KANT = ["F2F0EA", "3FB54A", "1FC7B8", "E5392F", "FF5FA8", "rainbow"]  # 6 — радужный: сегменты 1…5 по кругу
X, Z, BASE_TOP = 18.12, 17.12, 19.0  # наружные плоскости стен, верх базового этажа (полоса −1 … 19)
SLAB = 2.0

PAL = dict(TH)
PAL.update({"slab": "3E3F45", "rail": "3B3B3B", "white": "F4F2EC", "black": "222222", "green": "4E9A3A",
            "gold": "E9B43A", "crystal": "38D6E0", "yellow": "F5C531", "red": "D63A2F", "metal": "8C949C",
            "glove": "C9302C", "cuff": "F2EFE6", "fish": "FF8A3D", "fin": "FFB347", "eye": "FFFFFF"})
for i, k in enumerate(KANT):
    if k != "rainbow":
        PAL["kant%d" % (i + 1)] = k
_mats = {}


def mat(key):
    if key in _mats:
        return _mats[key]
    hexs = PAL[key]
    m = bpy.data.materials.new("R_" + key)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    rgb = [int(hexs[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c**2.2 for c in rgb]
    bsdf.inputs["Base Color"].default_value = (*lin, 1)
    bsdf.inputs["Roughness"].default_value = 0.6
    if key in ("gold",):
        bsdf.inputs["Metallic"].default_value = 0.55
        bsdf.inputs["Roughness"].default_value = 0.32
    if key == "glass":  # свет в окнах — тёплое свечение, не неон
        bsdf.inputs["Emission Color"].default_value = (*lin, 1)
        bsdf.inputs["Emission Strength"].default_value = 0.7
    _mats[key] = m
    return m


class Build:
    """Собирает детали надстроек в коллекцию со сдвигом (ox, oy) в координатах игры (y — вверх)."""

    def __init__(self, coll_name, ox=0.0, oy=0.0, top=None):
        self.coll = bpy.data.collections.new(coll_name)
        scene.collection.children.link(self.coll)
        self.ox, self.oy, self.top = ox, oy, top
        self.objs = []

    def _put(self, o, key):
        for c in o.users_collection:
            c.objects.unlink(o)
        self.coll.objects.link(o)
        o.data.materials.clear()
        o.data.materials.append(mat(key))
        self.objs.append(o)
        return o

    def P(self, x, y, z):
        return K.P(x + self.ox, y + self.oy, z)

    def box(self, key, x0, x1, y0, y1, z0, z1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=self.P((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        o = bpy.context.active_object
        o.scale = (abs(x1 - x0), abs(z1 - z0), abs(y1 - y0))
        return self._put(o, key)

    def cyl(self, key, x, z, r, y0, y1, n=16, r2=None):
        if r2 is None:
            bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=r, depth=y1 - y0, location=self.P(x, (y0 + y1) / 2, z))
        else:
            bpy.ops.mesh.primitive_cone_add(vertices=n, radius1=r, radius2=r2, depth=y1 - y0,
                                            location=self.P(x, (y0 + y1) / 2, z))
        return self._put(bpy.context.active_object, key)

    def blob(self, key, x, y, z, sx, sy, sz, seg=16):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=max(6, seg // 2), radius=1, location=self.P(x, y, z))
        o = bpy.context.active_object
        o.scale = (sx, sz, sy)
        return self._put(o, key)

    def disc(self, key, x, y, z, r, depth, axis, n=16):
        """Круг (иллюминатор): ось по нормали стены — 'z' (перед, зад) или 'x' (бока)."""
        bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=r, depth=depth, location=self.P(x, y, z))
        o = bpy.context.active_object
        o.rotation_euler = (math.radians(90), 0, 0) if axis == "z" else (0, math.radians(90), 0)
        return self._put(o, key)

    def torus(self, key, x, y, z, big, small, tilt=0.0):
        bpy.ops.mesh.primitive_torus_add(major_radius=big, minor_radius=small, major_segments=32, minor_segments=8,
                                         location=self.P(x, y, z))
        o = bpy.context.active_object
        o.rotation_euler = (math.radians(tilt), 0, 0)
        return self._put(o, key)


# ── этаж: плиты с кантом, ярусы, галереи, балконы, знак темы ───────────────────────────────────────────────────
def slab_with_kant(b, tier, y0, y1):
    """Плита перекрытия точно по следу и кант по её торцам (выступ 0.15 — в полосе плиты)."""
    b.box("slab", -X, X, y0, y1, -Z, Z)
    e = 0.5
    sides = ((-X - e, X + e, -Z - e, -Z), (-X - e, X + e, Z, Z + e), (-X - e, -X, -Z, Z), (X, X + e, -Z, Z))
    if KANT[tier - 1] != "rainbow":
        for x0, x1, z0, z1 in sides:
            b.box("kant%d" % tier, x0, x1, y0, y1, z0, z1)
        return
    seg = 3.0  # радужный: сегменты цветов 1…5 по кругу
    for x0, x1, z0, z1 in sides:
        along_x = (x1 - x0) > (z1 - z0)
        a0, a1 = (x0, x1) if along_x else (z0, z1)
        n = max(1, round((a1 - a0) / seg))
        for k in range(n):
            s0, s1 = a0 + (a1 - a0) * k / n, a0 + (a1 - a0) * (k + 1) / n
            key = "kant%d" % (1 + k % 5)
            if along_x:
                b.box(key, s0, s1, y0, y1, z0, z1)
            else:
                b.box(key, x0, x1, y0, y1, s0, s1)


def railing(b, x0, x1, z0, z1, y, posts=3.0):
    """Сплошной парапет по отрезку (вдоль x или вдоль z) на высоте пола y: панель цвета темы и поручень."""
    along_x = abs(x1 - x0) > abs(z1 - z0)
    if along_x:
        b.box("wall2", min(x0, x1), max(x0, x1), y, y + 1.3, z0 - 0.2, z0 + 0.2)
        b.box("trim", min(x0, x1) - 0.15, max(x0, x1) + 0.15, y + 1.3, y + 1.6, z0 - 0.3, z0 + 0.3)
    else:
        b.box("wall2", x0 - 0.2, x0 + 0.2, y, y + 1.3, min(z0, z1), max(z0, z1))
        b.box("trim", x0 - 0.3, x0 + 0.3, y + 1.3, y + 1.6, min(z0, z1) - 0.15, max(z0, z1) + 0.15)


def balcony(b, side, y, depth, span):
    """Балкон-консоль на стороне side ('front' | 'back' | 'left' | 'right') на уровне пола y."""
    if side in ("front", "back"):
        s = -1 if side == "front" else 1
        z0, z1 = sorted((s * Z, s * (Z + depth)))
        b.box("slab", -span, span, y - 0.5, y, z0, z1)
        zr = s * (Z + depth - 0.3)
        railing(b, -span + 0.3, span - 0.3, zr, zr, y)
    else:
        s = -1 if side == "left" else 1
        x0, x1 = sorted((s * X, s * (X + depth)))
        b.box("slab", x0, x1, y - 0.5, y, -span, span)
        xr = s * (X + depth - 0.3)
        railing(b, xr, xr, -span + 0.3, span - 0.3, y)


def windows(b, face, y0, y1, glass_full=False):
    """Окна по стене face на ярусе y0…y1 в стиле темы: салун — доски и окна со ставнями, океанариум — иллюминаторы;
    glass_full — витраж в средней части фасада во весь ярус (виден жилец)."""
    h = y1 - y0
    front = face in ("front", "back")
    s = (-1 if face in ("front", "left") else 1)
    half = X if front else Z
    plane = s * ((Z if front else X) + 0.08)

    def at(a, y, d=0.0):  # точка на плоскости стены: a — вдоль стены, d — наружу
        return (a, y, plane + s * d) if front else (plane + s * d, y, a)

    def rect(key, a0, a1, yy0, yy1, d0, d1):
        if front:
            z0, z1 = sorted((plane + s * d0, plane + s * d1))
            b.box(key, a0, a1, yy0, yy1, z0, z1)
        else:
            x0, x1 = sorted((plane + s * d0, plane + s * d1))
            b.box(key, x0, x1, yy0, yy1, a0, a1)

    style = TH["style"]
    g0 = -half * 0.45 if glass_full else None
    if glass_full:  # витраж в середине фасада
        rect("glass", g0, -g0, y0 + 0.4, y1 - 0.2, -0.1, 0.05)
        for k in range(7):
            a = g0 + (-2 * g0) * k / 6
            rect("trim", a - 0.2, a + 0.2, y0 + 0.4, y1 - 0.2, -0.1, 0.25)
    n = 6 if front else 5
    for k in range(n):
        a = -half + 3.0 + (2 * half - 6.0) * (k + 0.5) / n
        if glass_full and abs(a) < -g0 + 1.5:
            continue
        if style == "portholes":
            r = min(1.6, h * 0.22)
            cy = y0 + h * 0.52
            ax = "z" if front else "x"
            px, py, pz = at(a, cy, 0.15)
            b.disc("accent", px, py, pz, r + 0.45, 0.3, ax)
            px, py, pz = at(a, cy, 0.25)
            b.disc("glass", px, py, pz, r, 0.3, ax)
        else:
            w = 2.2
            wy0, wy1 = y0 + h * 0.22, y0 + h * 0.8
            rect("trim", a - w / 2 - 0.3, a + w / 2 + 0.3, wy0 - 0.3, wy1 + 0.3, 0.0, 0.2)
            rect("glass", a - w / 2, a + w / 2, wy0, wy1, 0.2, 0.28)
            rect("accent", a - w / 2 - 1.1, a - w / 2 - 0.35, wy0, wy1, 0.2, 0.35)  # ставни
            rect("accent", a + w / 2 + 0.35, a + w / 2 + 1.1, wy0, wy1, 0.2, 0.35)
    if style == "planks":  # вертикальные доски между окнами
        m = 14 if front else 13
        for k in range(m):
            a = -half + 0.8 + (2 * half - 1.6) * (k + 0.5) / m
            if glass_full and abs(a) < -g0 + 0.5:
                continue
            rect("wall2", a - 0.5, a + 0.5, y0 + 0.6, y1 - 0.1, 0.0, 0.1)
    else:  # волна-пояс океанариума
        rect("trim", -half + 0.6, half - 0.6, y0 + h * 0.12, y0 + h * 0.12 + 0.4, 0.0, 0.15)


def sign(b, kind, x, y, z, s):
    """Знак темы масштаба s (вывеска на фасаде; на высших редкостях — «геройский» объект)."""
    if kind == "glove":  # боксёрская перчатка: кулак, большой палец, манжета со шнуровкой
        b.blob("glove", x, y, z, 1.6 * s, 1.35 * s, 1.15 * s)
        b.blob("glove", x - 1.25 * s, y - 0.2 * s, z - 0.35 * s, 0.6 * s, 0.75 * s, 0.6 * s, seg=12)
        b.cyl("cuff", x + 0.0, z, 1.05 * s, y - 2.2 * s, y - 1.05 * s, n=16)
        b.box("trim", x - 0.12 * s, x + 0.12 * s, y - 2.1 * s, y - 1.1 * s, z - 1.1 * s, z - 0.95 * s)
    else:  # рыба: тело, хвост, плавники, глаз
        b.blob("fish", x, y, z, 2.3 * s, 1.25 * s, 0.75 * s)
        b.box("fin", x + 2.1 * s, x + 3.4 * s, y - 1.2 * s, y + 1.2 * s, z - 0.2 * s, z + 0.2 * s)
        b.box("fin", x - 0.4 * s, x + 0.6 * s, y + 1.0 * s, y + 1.7 * s, z - 0.12 * s, z + 0.12 * s)
        b.blob("eye", x - 1.4 * s, y + 0.3 * s, z - 0.6 * s, 0.32 * s, 0.32 * s, 0.2 * s, seg=10)
        b.blob("black", x - 1.5 * s, y + 0.3 * s, z - 0.75 * s, 0.15 * s, 0.15 * s, 0.1 * s, seg=8)


def floor_overlay(b, tier):
    """Надстройки этажа редкости tier в полосе −1 … −1 + H (координаты этажа)."""
    top = -1 + H[tier - 1]
    slab_with_kant(b, tier, -1.0, -1.0 + 1.2)  # плита снизу
    slab_with_kant(b, tier, top - SLAB, top)  # плита сверху
    if tier == 1:
        return top
    u0, u1 = BASE_TOP, top - SLAB  # верхний ярус(ы) над базовым этажом
    levels = {2: 1, 3: 1, 4: 2, 5: 3, 6: 5}[tier]
    hs = (u1 - u0) / levels
    out = OUT_SIDE[tier - 1]
    # стены ярусов в цветах темы, пояса между ярусами
    for k in range(levels):
        y0, y1 = u0 + k * hs, u0 + (k + 1) * hs
        wall = "wall" if k % 2 == 0 else "wall2"
        b.box(wall, -X, X, y0, y1, -Z, -Z + 0.6)
        b.box(wall, -X, X, y0, y1, Z - 0.6, Z)
        b.box(wall, -X, -X + 0.6, y0, y1, -Z, Z)
        b.box(wall, X - 0.6, X, y0, y1, -Z, Z)
        b.box("trim", -X - 0.3, X + 0.3, y0, y0 + 0.6, -Z - 0.3, -Z + 0.6)
        glass_front = tier >= 5 and k < levels - 1  # витраж во всю высоту — виден жилец
        windows(b, "front", y0, y1, glass_full=glass_front)
        for face in ("left", "right") if tier >= 3 else ():
            windows(b, face, y0, y1, glass_full=tier >= 6)
        if tier >= 4:
            windows(b, "back", y0, y1)
    # балконы и террасы: на уровнях пола ярусов (на высших — через ярус, иначе фасад как леса)
    for k in range(levels):
        if levels >= 3 and k % 2 == 1:
            continue
        y = u0 + k * hs + 0.5
        sides = ["front"]
        if tier >= 3:
            sides += ["left", "right"]
        if tier >= 5:
            sides += ["back"]
        for side in sides:
            span = (X - 1.0) if side in ("front", "back") else (Z - 1.0)
            balcony(b, side, y, out if side != "front" or tier < 5 else min(out, 3), span)
    # навесы над окнами нижнего яруса (тема: акцентный цвет)
    if tier >= 2:
        y = u0 + hs * 0.85
        b.box("accent", -X + 2.0, X - 2.0, y, y + 0.35, -Z - min(out, 2.5), -Z)
        for k in range(8):
            x0 = -X + 2.0 + k * (2 * X - 4.0) / 8
            b.box("accent2", x0, x0 + (2 * X - 4.0) / 16, y + 0.35, y + 0.45, -Z - min(out, 2.5), -Z)
    # знак темы: средний на 3–4, «геройский» на 5–6 (вынос — в пределах out)
    if tier in (3, 4):
        s = 1.4 if tier == 3 else 1.8
        sign(b, TH["sign"], 0, u0 + hs * 0.6, -Z - 1.6 * s, s)
    elif tier >= 5:  # «геройский» объект темы — на передней террасе-консоли (вынос out), стоит на ней
        s = 2.3 if tier == 5 else 3.0
        ty = u0 + hs * (1 if levels >= 3 else 0) + 0.5
        b.box("slab", -X * 0.55, X * 0.55, ty - 0.6, ty, -Z - out, -Z)
        railing(b, -X * 0.55, X * 0.55, -Z - out + 0.3, -Z - out + 0.3, ty)
        sign(b, TH["sign"], 0, ty + 2.3 * s, -Z - out / 2, s)
    return top


# ── проверки: ничего выше верхней плиты; вынос вбок ───────────────────────────────────────────────────────────
def bounds(objs):
    """Габариты по вершинам (служебные якоря floorbase на ±30 не считаются)."""
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        if o.type != "MESH":
            continue
        mw = o.matrix_world
        base = Vector((o.matrix_world.translation))
        for v in o.data.vertices:
            w = mw @ v.co
            local = w - base if o.name.startswith(("CB_", "AQ_")) else None
            if local is not None and (abs(local.x) > 29.5 or abs(local.y) > 29.5):
                continue
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def check(label, objs, ox, oy, top):
    """Blender: x = −x игры, y = z игры, z = y игры."""
    lo, hi = bounds(objs)
    top_w = oy + top
    ok = hi.z <= top_w + 1e-3
    side = max(-lo.x - ox, hi.x + ox) - X  # |x игры| за плоскостью стены
    front, back = -lo.y - Z, hi.y - Z
    print("CHECK_TOP %s %s: верх деталей %.2f, верх плиты %.2f; вынос вбок %.1f, вперёд %.1f, назад %.1f"
          % ("OK" if ok else "FAIL", label, hi.z - oy, top, side, front, back), flush=True)
    return ok, side, front, back


# ── 6 редкостей у начала координат ───────────────────────────────────────────────────────────────────────────
tier_builds = {}
for t in range(1, 7) if not TOWER else ():
    b = Build("T%d" % t)
    top = floor_overlay(b, t)
    tier_builds[t] = (b, top)
    check("%s %d %s" % (THEME, t, NAMES[t - 1]), BASE + b.objs, 0, 0, top)

cam = scene.camera
scene.render.resolution_x, scene.render.resolution_y = 900, 1100


def aim(eye, target, fov):
    cam.data.angle_y = math.radians(fov)
    e, t = K.P(*eye), K.P(*target)
    cam.location = e
    cam.rotation_euler = (e - t).to_track_quat("Z", "Y").to_euler()


def show(visible):
    for c in scene.collection.children:
        if c.name.startswith("T") or c.name.startswith("Tower") or c.name.startswith("Cap"):
            c.hide_render = c.name not in visible


def render(name):
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("SHOT", name, flush=True)


base_coll = BASE[0].users_collection[0]
aim((-104, 40, -118), (0, 27, -2), 36)
for t in range(1, 7) if (TIER_SHOTS and not TOWER) else ():
    show({"T%d" % t})
    render("%s_tier_%d" % (THEME, t))

if not TOWER:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, THEME + "_base.blend"))
    print("DONE_THEME", flush=True)
    sys.exit(0)

# ── башня: 6 этажей в порядке 1, 6, 3, 5, 2, 4 (темы чередуются), колпак сверху ─────────────────────────────────
base_coll.hide_render = True
for c in scene.collection.children:  # образцы редкостей из файла темы — не в кадр башни
    if c.name.startswith("T") and not c.name.startswith("Tower"):
        c.hide_render = True
aq_path = os.path.join(OUT, "aquarium_base.blend")
with bpy.data.libraries.load(aq_path) as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith("AQ_F_") or n.startswith("AQ_I_")]
AQ_BASE = [o for o in dst.objects if o is not None]
TX = 400.0  # башня — в стороне от образцов
ORDER = [1, 6, 3, 5, 2, 4]
tower_ok = True
y = 0.0
floors = []
for i, t in enumerate(ORDER):
    theme = "saloon" if i % 2 == 0 else "aquarium"
    TH = THEMES[theme]
    PAL.update({k: v for k, v in TH.items() if isinstance(v, str) and len(v) == 6})
    for k in list(_mats):  # цвета темы — свои материалы
        if k in ("wall", "wall2", "trim", "accent", "accent2", "glass"):
            del _mats[k]
    oy = y + 1.0  # низ полосы этажа (−1) — на y
    b = Build("Tower%d" % i, ox=TX, oy=oy)
    src_objs = BASE if theme == "saloon" else AQ_BASE
    for o in src_objs:
        c = o.copy()
        b.coll.objects.link(c)
        c.location = o.location + Vector((-TX, 0, oy))
        b.objs.append(c)
    top = floor_overlay(b, t)
    over = [o for o in b.objs if not o.name.startswith(("CB_", "AQ_"))]  # база проверена в прогонах тем (верх 19)
    ok, side, front, back = check("башня этаж %d: %s %s" % (i + 1, theme, NAMES[t - 1]), over, TX, oy, top)
    tower_ok = tower_ok and ok
    floors.append((t, oy, top))
    y += H[t - 1]
print("TOWER_HEIGHT", y, "TOWER_TOP_OK", tower_ok, flush=True)

# колпаки — общая кровля башни (отдельный объект башни; переставляется при добавлении и краже этажа);
# богатство — по лучшему этажу: кант лучшего этажа, на лучшем ≥ 5 — больше элементов
best = max(ORDER)
kant = "kant%d" % (best if best < 6 else 4)
ry = y  # верх башни


def cap_a(b):
    """A «Мачта-антенна»: уступ-надстройка, решётчатая мачта, вращающееся кольцо с кристаллом-логотипом."""
    b.box("slab", -X + 3, X - 3, ry, ry + 7, -Z + 3, Z - 3)
    b.box(kant, -X + 2.6, X - 2.6, ry + 6.0, ry + 7.0, -Z + 2.6, Z - 2.6)
    for sx in (-1, 1):
        for sz in (-1, 1):
            b.box("metal", sx * 3.2 - 0.45, sx * 3.2 + 0.45, ry + 7, ry + 58, sz * 3.2 - 0.45, sz * 3.2 + 0.45)
    for k in range(16):
        yy = ry + 9 + k * 3.1
        b.box("metal", -3.6, 3.6, yy, yy + 0.4, -3.6, 3.6)
    b.torus("gold", 0, ry + 42, 0, 10.5, 0.9, tilt=90)
    b.cyl("crystal", 0, 0, 0.01, ry + 38, ry + 42, n=4, r2=3.6)
    b.cyl("crystal", 0, 0, 3.6, ry + 42, ry + 46, n=4, r2=0.01)
    b.blob("red", 0, ry + 59.2, 0, 1.3, 1.3, 1.3, seg=10)


def cap_b(b):
    """B «Вертолётная площадка с маяком»: круглая площадка на опорах, разметка, будка, мачта-маяк."""
    for sx in (-1, 1):
        for sz in (-1, 1):
            b.box("metal", sx * 10 - 0.8, sx * 10 + 0.8, ry, ry + 6, sz * 10 - 0.8, sz * 10 + 0.8)
    b.box("wall", -8, 8, ry, ry + 6, -8, 8)
    b.cyl("slab", 0, 0, 16.5, ry + 6, ry + 7.4, n=32)
    b.torus(kant, 0, ry + 7.45, 0, 16.0, 0.6)
    b.torus("yellow", 0, ry + 7.45, 0, 10.0, 0.55)
    b.box("white", -4.4, -3.0, ry + 7.4, ry + 7.7, -5.5, 5.5)
    b.box("white", 3.0, 4.4, ry + 7.4, ry + 7.7, -5.5, 5.5)
    b.box("white", -3.0, 3.0, ry + 7.4, ry + 7.7, -0.7, 0.7)
    b.cyl("metal", -13, 11, 0.8, ry + 7.4, ry + 34, n=8)
    b.blob("yellow", -13, ry + 35.4, 11, 1.8, 1.8, 1.8, seg=12)


def cap_c(b):
    """C «Ловибум-кристалл»: сад на крыше, четыре когтя-пластины держат огромный кристалл (фирменный знак игры)."""
    b.box("green", -X + 1, X - 1, ry, ry + 1.5, -Z + 1, Z - 1)
    for k in range(12):
        a = 2 * math.pi * k / 12
        b.blob("green", math.cos(a) * 14.5, ry + 2.8, math.sin(a) * 13.5, 2.2, 1.8, 2.2, seg=10)
    b.cyl("gold", 0, 0, 9.5, ry + 1.5, ry + 4.5, n=8)
    b.cyl(kant, 0, 0, 10.0, ry + 4.5, ry + 5.5, n=8)
    b.cyl("crystal", 0, 0, 0.01, ry + 5.5, ry + 19.0, n=4, r2=8.5)
    b.cyl("crystal", 0, 0, 8.5, ry + 19.0, ry + 35.0, n=4, r2=0.01)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        cx, cz = math.cos(a) * 9.2, math.sin(a) * 9.2
        b.box("gold", cx - 1.6, cx + 1.6, ry + 4.5, ry + 23.0, cz - 1.6, cz + 1.6)
        b.box(kant, cx - 1.75, cx + 1.75, ry + 12.0, ry + 13.6, cz - 1.75, cz + 1.75)


caps = {}
for key, fn in (("A", cap_a), ("B", cap_b), ("C", cap_c)):
    b = Build("Cap" + key, ox=TX, oy=0)
    fn(b)
    caps[key] = b

tower_colls = {"Tower%d" % i for i in range(6)}
scene.render.resolution_x, scene.render.resolution_y = 900, 1600
mid = y / 2 + 10
for key in ("A", "B", "C"):
    show(tower_colls | {"Cap" + key})
    aim((TX - 230, mid + 70, -270), (TX, mid + 14, 0), 52)
    render("tower_cap_%s" % key)
show(tower_colls | {"CapC"})
aim((TX + 330, mid + 25, 0), (TX, mid + 14, 0), 54)  # вид сбоку: игра +x → кадр сбоку
render("tower_side")
print("DONE_TOWER", flush=True)
