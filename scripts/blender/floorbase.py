"""Общий конвейер этажей-мешей музея-небоскрёба (по эталонам GoldenThrone v6, TRexSkeleton v1, SpaceHelmet v1,
утверждены владельцем 2026-11-21): детали и материалы, помощники геометрии, затенение, бюджет, экспорт, проверочные
рендеры. Скрипт этажа отвечает только за художественный замысел (геометрию и цвета); всё техническое — здесь.

  F = Floor("CO", "Colosseum", quiet=(...))   — 9 MeshPart: <prefix>_F_* (фасад), _I_* (зал), _S_All (силуэт)
  ... геометрия через F.FR / F.FS / F.FQ / F.FG / F.IR / F.IS / F.IQ / F.IG / F.SL и помощники модуля ...
  F.build(exhibit=(x, y, z, масштаб), lamps=[...])   — затенение, бюджет, экспорт (флаг export), рендеры (render)

Детали: Rings — Plastic + LegoSquaresFar (крупные квадраты по одному на стад), Quiet — LegoSquaresQuiet (ткань, песок,
трава — цвета из quiet переносятся туда сами), Smooth — SmoothPlastic, Glass — светится сам (без затенения).
Сетка: грани брусков с рисунком — на целых координатах (стены снаружи: глубина 0.88 / 1.88 от FX/FZ; внутри — от W/ZB),
центр габаритов деталей с рисунком — целый (anchor). Бюджет: фасад ≤ 14 000, зал ≤ 12 000, силуэт ≤ 400 треугольников —
печатается в конце (TIER), превышение — ошибка сборки.
Запуск: blender --background --factory-startup --python scripts/blender/floor_<тема>.py -- <репо> <превью>
        [render] [export] [shot=<имя>] [tol=…] [ml=…] [mlf=…]
Зависит от floorkit (Blender: bpy, bmesh, mathutils).
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorkit as K  # noqa: E402

HX, HZ, YB, YT = 18.0, 17.0, -1.0, 19.0
SK = 0.12
FX, FZ = HX + SK, HZ + SK  # наружные плоскости стен
W, ZB, ZF, C = 16.88, 15.88, -15.88, 18.0  # стены и потолок изнутри (лифт — у +Z)
DOOR = (3.5, 10.5)  # двери лифта: полуширина, высота
LANDING = (0.0, 12.0, 4.0)  # площадка лифта: x, z, полуразмер — пустая до высоты 8
NARROW = 0.9
PROP_NARROW = 0.5  # узкие грани объектов — гладкие, как мелкие накладки у предметов
ARCH_IN = 0.9  # накладка на стену шире этого в обе стороны — на квадраты этажа
EDGE = 0.1
SHADE = (0.52, 0.52, 0.52)
BUDGET = {"facade": 14000, "interior": 12000, "silhouette": 400}
FORM_IN = {"up": 1.0, "pz": 0.96, "px": 0.88, "nx": 0.88, "nz": 0.84, "down": 0.74, "edge": 1.14}
FORM_OUT = {"up": 1.0, "pz": 0.95, "px": 0.86, "nx": 0.86, "nz": 0.97, "down": 0.70, "edge": 1.12}


class Floor:
    """Этаж-тема: детали, флаги запуска, сборка."""

    def __init__(self, prefix, theme, quiet=(), bevel_min=1.0, keep_arch=False):
        """bevel_min — с какой толщины бруски с рисунком получают фаску рёбер (камень с острыми рёбрами — больше);
        keep_arch — утверждённый этаж: гладкая архитектура остаётся гладкой, на кольца уходят только вещи."""
        bpy.ops.wm.read_factory_settings(use_empty=True)
        argv = sys.argv[sys.argv.index("--") + 1 :]
        self.repo, self.out = os.path.abspath(argv[0]), os.path.abspath(argv[1])
        self.flags = set(argv[2:])
        os.makedirs(self.out, exist_ok=True)
        self.prefix, self.theme, self.quiet = prefix, theme, tuple(quiet)
        self.parts = []
        p = self._part
        self.FS = p("F_Smooth", "facade", "smooth", adapt=True)
        self.FR = p("F_Rings", "facade", "tile", adapt=True, partner=self.FS, narrow=NARROW, bevel=EDGE, bevel_min=bevel_min)
        self.FQ = p("F_Quiet", "facade", "tile", adapt=True, partner=self.FS, narrow=NARROW)
        self.FG = p("F_Glass", "facade", "glass", occlude=False)
        self.IS = p("I_Smooth", "interior", "smooth", adapt=True)
        self.IR = p("I_Rings", "interior", "tile", adapt=True, partner=self.IS, narrow=NARROW, bevel=EDGE, bevel_min=bevel_min)
        self.IQ = p("I_Quiet", "interior", "tile", adapt=True, partner=self.IS, narrow=NARROW)
        self.IG = p("I_Glass", "interior", "glass", occlude=False)
        self.SL = p("S_All", "silhouette", "smooth", limit=99)
        # Объекты этажа (статуи, звери, мебель, машины, растения) — в стиле предметов и боссов D39: Plastic +
        # LegoRingsD39Boss (квадраты-контуры с шагом 1.8 стада, как у боссов ×3); узкие грани — гладкие.
        self.FP = p("F_Props", "facade", "props", adapt=True, partner=self.FS, narrow=PROP_NARROW)
        self.IP = p("I_Props", "interior", "props", adapt=True, partner=self.IS, narrow=PROP_NARROW)
        self.FS.route_props, self.FS.route_arch = self.FP, self.FR
        self.IS.route_props, self.IS.route_arch = self.IP, self.IR
        if keep_arch:  # утверждённый этаж: на кольца — только вещи, отмеченные F.objects(True) … F.objects(False)
            self.FS.route_arch = self.IS.route_arch = self.FS.route_props = self.IS.route_props = None
        self._objects = 0

    def objects(self, on=True):
        """Начало (True) / конец (False) участка с вещами: гладкие тела уходят в Props (кольца D39 боссов). Вложенные
        участки (функции-вещи внутри участка) считаются."""
        self._objects += 1 if on else -1
        f = self._objects > 0
        # гладкие тела и бруски с квадратами (FR/IR) этого участка — на кольца; ткань (Quiet) и стекло — как были
        self.FS.force, self.IS.force = (self.FP, self.IP) if f else (None, None)
        self.FR.force, self.IR.force = (self.FP, self.IP) if f else (None, None)

    def _part(self, suffix, tier, material, **kw):
        part = K.Part(self.prefix + "_" + suffix, tier, material, "FFFFFF", SHADE, **kw)
        self.parts.append(part)
        return part

    def flag(self, name, default, cast=float):
        return cast(next((f[len(name) + 1 :] for f in self.flags if f.startswith(name + "=")), default))

    def _art_path(self, kind, name):
        """Файл предмета для превью: assets/<kind>/art/<name> или подпапка босса (art/boss4/… у существ)."""
        base = os.path.join(self.repo, "assets", kind, "art")
        for sub in ("",) + tuple(sorted(d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)))):
            path = os.path.join(base, sub, name)
            if os.path.exists(path):
                return path
        return os.path.join(base, name)

    def auto_yard(self, edge=2.88):
        """Земля под вещами за краем площадки: если у земли (y −0.35…0.6) стоят детали фасада дальше полосы земли
        этажа (2.88 от стены), сторона получает двор того же цвета до них + 0.6 — вещи не висят в воздухе (проверка
        всех этажей, 2026-11-22). Свой двор этажа (земля FQ дальше 2.88) учитывается."""
        sides = (("-z", lambda x, z: -z - FZ, lambda x, z: abs(x)), ("+z", lambda x, z: z - FZ, lambda x, z: abs(x)),
                 ("-x", lambda x, z: -x - FX, lambda x, z: abs(z)), ("+x", lambda x, z: x - FX, lambda x, z: abs(z)))
        need, have, col = {}, {}, {}
        for p in self.parts:
            if p.tier != "facade":
                continue
            for v in p.bm.verts:
                x, y, z = -v.co.x, v.co.z, v.co.y
                for key, out, along in sides:
                    d = out(x, z)
                    lim = (FX if key[1] == "z" else FZ) + edge + 0.3
                    if d < 0 or along(x, z) > lim:
                        continue
                    if p is self.FQ and y < -0.9:  # своя земля — плита до низа полосы (плитки-накладки не в счёт)
                        have[key] = max(have.get(key, edge), d)
                    elif p is not self.FQ and -0.35 < y < 0.6 and d > edge + 0.3:
                        need[key] = max(need.get(key, 0.0), d)
        tone_l = self.FQ.bm.loops.layers.float_color["tone"]
        for f in self.FQ.bm.faces:  # цвет и высота земли — с верхней грани полосы земли у стены
            c = f.calc_center_median()
            x, y, z = -c.x, c.z, c.y
            if f.normal.z < 0.9 or not -0.3 < y < 0.02:
                continue
            for key, out, along in sides:
                if 1.0 < out(x, z) < edge and along(x, z) < (FX if key[1] == "z" else FZ) and key not in col:
                    col[key] = (tuple(f.loops[0][tone_l])[:3], y)
        for key, out, along in sides:
            if key not in need or need[key] <= have.get(key, edge) + 0.3 or key not in col:
                continue
            h0, h1 = have.get(key, edge), need[key] + 0.6
            c, top = col[key]
            s = 1 if key[0] == "+" else -1
            self.FQ.noroute += 1
            if key[1] == "z":
                self.FQ.box(-FX - edge, FX + edge, -1.0, top, s * (FZ + h0), s * (FZ + h1), c)
            else:
                self.FQ.box(s * (FX + h0), s * (FX + h1), -1.0, top, -FZ - edge, FZ + edge, c)
            self.FQ.noroute -= 1
            print("YARD", key, round(h0, 2), "->", round(h1, 2), flush=True)

    def build(self, exhibit, yaw=180.0, lamps=(), shots=None, tol=0.11, ml=3, mlf=2):
        """exhibit — (x, y, z, масштаб показа) как в теме Luau; lamps — [(имя, (x, y, z), энергия, (r, g, b))] для
        рендеров (в игре свет задаёт тема); shots — дополнительные кадры {имя: (глаз, цель, угол)}."""
        parts = self.parts
        if "noyard" not in self.flags:
            self.auto_yard()
        collection = bpy.data.collections.new(self.theme + "Floor")
        bpy.context.scene.collection.children.link(collection)

        def proxy(name, y0, y1):
            me = bpy.data.meshes.new(name)
            pts = [K.P(sx * HX, y, sz * HZ) for y in (y0, y1) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            me.from_pydata(pts, [], [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
            obj = bpy.data.objects.new(name, me)
            collection.objects.link(obj)
            return obj

        above, below = proxy("TowerAbove", 19.0, 39.0), proxy("TowerBelow", -21.0, -1.0)
        bpy.context.view_layer.update()
        facade = [p for p in parts if p.tier == "facade" and p.material != "glass"]
        interior = [p for p in parts if p.tier == "interior" and p.material != "glass"]
        glow = [p for p in parts if p.material == "glass"]
        silhouette = [p for p in parts if p.tier == "silhouette"]
        tol, ml, mlf = self.flag("tol", tol), self.flag("ml", ml, int), self.flag("mlf", mlf, int)
        for p in parts:  # центр габаритов деталей с рисунком — целый: квадраты не сдвигаются от выступов фасада
            if p.material in ("tile", "props"):
                if p.tier == "facade":
                    anchor(p, (-30, -1, -30), (30, 19, 30))
                elif p.tier == "interior":
                    anchor(p, (-17, 0, -16), (17, 18, 16))
        if self.quiet:
            print("QUIET facade", self.FR.give_tones(self.FQ, self.quiet), "interior", self.IR.give_tones(self.IQ, self.quiet),
                  flush=True)
        if "nocoplanar" not in self.flags:
            print("COPLANAR", K.resolve_coplanar([p for p in parts if p.tier != "silhouette"]), flush=True)
        print("LINES facade", K.adaptive_cut(facade, [above, below], radius=5.0, tol=tol, fine=1.0, min_size=2.0,
                                             max_lines=mlf), flush=True)
        print("LINES interior", K.adaptive_cut(interior, radius=3.5, tol=tol, fine=1.2, min_size=2.4, max_lines=ml),
              flush=True)
        for p in sorted(parts, key=lambda q: q.partner is None):
            p.finish(collection)
        bpy.context.view_layer.update()
        K.shade_parts(facade, extra=[above, below], radius=5.0, rays=32, form=FORM_OUT, floor_lo=0.34)
        K.shade_parts(interior, radius=3.5, rays=32, form=FORM_IN, floor_lo=0.30)
        K.flat_parts(silhouette + glow)
        info = K.manifest(parts)
        over = []
        for name, d in info.items():
            print("PART", name, d["tier"], d["material"], d["tris"], d["size"], flush=True)
            y0, y1 = d["center"][1] - d["size"][1] / 2, d["center"][1] + d["size"][1] / 2
            if y0 < YB - 1e-3 or y1 > YT + 1e-3:
                over.append("%s вне полосы этажа (%.3f…%.3f)" % (name, y0, y1))
        for tier, limit in BUDGET.items():
            total = sum(d["tris"] for d in info.values() if d["tier"] == tier)
            print("TIER", tier, total, "/", limit, flush=True)
            if total > limit:
                over.append("%s: %d > %d" % (tier, total, limit))
        for line in over:
            print("BUDGET_ERROR", line, flush=True)
        if "export" in self.flags:
            if over:
                raise SystemExit("экспорт отменён: " + "; ".join(over))
            path = os.path.join(self.repo, "assets", "models", "floors", self.theme + "Floor.fbx")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            K.export_fbx([p.obj for p in parts], path)
            K.write_json(os.path.splitext(path)[0] + ".json", info)
            print("EXPORTED", path, flush=True)
        if "render" in self.flags:
            self._render(above, below, exhibit, yaw, lamps, shots or {})
        print("DONE", flush=True)

    def _render(self, above, below, exhibit, yaw, lamps, extra):
        scene = bpy.context.scene
        engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
        scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
        scene.view_settings.view_transform = "Standard"
        world = bpy.data.worlds.new("Sky")
        world.use_nodes = True
        bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
        bg.inputs["Color"].default_value = (0.55, 0.72, 1.0, 1)
        scene.world = world
        sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
        sun.data.energy = 2.6
        sun.rotation_euler = (math.radians(52), 0, math.radians(-150))
        scene.collection.objects.link(sun)
        for p in self.parts:
            K.preview_material(p)
        grey = bpy.data.materials.new("Tower")
        grey.use_nodes = True
        next(n for n in grey.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.8, 0.8, 0.82, 1)
        above.data.materials.append(grey)
        below.data.materials.append(grey)
        names = []
        for name, at, energy, color in lamps:
            lamp = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT"))
            lamp.data.energy, lamp.data.color, lamp.data.shadow_soft_size = energy, color, 2.0
            lamp.data.use_shadow = False
            lamp.location = K.P(*at)
            scene.collection.objects.link(lamp)
            names.append(name)
        # оригинал предмета на месте показа (масштаб показа, лицом к лифту)
        before = set(bpy.data.objects)
        try:
            bpy.ops.import_scene.fbx(filepath=self._art_path("models", self.theme + ".fbx"))
        except Exception as err:  # noqa: BLE001
            print("ITEM_IMPORT_FAILED", err)
        item = [o for o in bpy.data.objects if o not in before]
        if item:
            img = bpy.data.images.load(self._art_path("textures", self.theme + "_color.png"))
            mat = bpy.data.materials.new("Item")
            mat.use_nodes = True
            tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
            tex.image = img
            bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
            root = bpy.data.objects.new("ItemRoot", None)
            scene.collection.objects.link(root)
            for o in item:
                if o.type == "MESH":
                    o.data.materials.clear()
                    o.data.materials.append(mat)
                if o.parent is None:
                    o.parent = root
            root.scale = (exhibit[3],) * 3
            root.rotation_euler = (0, 0, math.radians(yaw))
            root.location = K.P(exhibit[0], exhibit[1] + 0.07, exhibit[2])
        cam_data = bpy.data.cameras.new("Cam")
        cam = bpy.data.objects.new("Cam", cam_data)
        scene.collection.objects.link(cam)
        scene.camera = cam
        cam_data.sensor_fit = "VERTICAL"
        cam_data.clip_start, cam_data.clip_end = 0.2, 800
        pre = self.prefix + "_"
        inside = (pre + "S_",)
        outside = (pre + "S_", "Item") + tuple(names)
        ex, ey, ez = exhibit[0], exhibit[1], exhibit[2]
        shots = {
            "f1_front": ((0, 9, -84), (0, 9, -17), 32, outside),
            "f2_side": ((84, 10, -4), (18, 9, -4), 32, outside),
            "f3_three_quarter": ((-50, 16, -60), (0, 8.5, -12), 36, outside),
            "f5_back": ((32, 14, 74), (0, 9, 17), 32, outside),
            "i1_lift": ((0, 5.5, 14.6), (0, 7.0, -8), 70, inside),
            "i2_exhibit": ((ex + 7.5, ey + 5.0, ez + 8.5), (ex, ey + 3.5, ez), 55, inside),
            "i3_side": ((-12, 6.5, 10), (2.0, 6.0, -10), 70, inside),
            "i4_back": ((0, 6.5, 2.0), (0, 6.0, 16), 70, inside),
            "s1_silhouette": ((-50, 16, -60), (0, 8.5, -12), 36, (pre + "F_", pre + "I_", "Item") + tuple(names)),
        }
        for k, (eye, target, fov) in extra.items():
            shots[k] = (eye, target, fov, inside)
        only = [f[5:] for f in self.flags if f.startswith("shot=")]
        for key, (eye, target, fov, hide) in shots.items():
            if only and key not in only:
                continue
            for o in bpy.data.objects:
                o.hide_render = any(o.name.startswith(h) for h in hide)
            scene.render.resolution_x, scene.render.resolution_y = 1280, 720
            cam_data.angle_y = math.radians(fov)
            e, t = K.P(*eye), K.P(*target)
            cam.location = e
            cam.rotation_euler = (e - t).to_track_quat("Z", "Y").to_euler()
            scene.render.filepath = os.path.join(self.out, key + ".png")
            bpy.ops.render.render(write_still=True)
            print("SHOT", key, flush=True)


# ── Помощники геометрии (оси этажа: X вправо, Y вверх, фасад — −Z, лифт — +Z) ─────────────────────────────────

def slab(p, axis, fixed, out, depth, a0, a1, y0, y1, color, back=0.05):
    """Накладка на стену: axis 'x' — стена x = fixed (вдоль z от a0 до a1), 'z' — стена z = fixed; out — куда выступает.
    Гладкая накладка шире ARCH_IN в обе стороны — часть здания: уходит на квадраты этажа (route_arch)."""
    a0, a1 = sorted((a0, a1))
    if axis == "z" and abs(abs(fixed) - FZ) < 1e-6 and out * fixed > 0 and depth > 0:
        # пояс переда/тыла во всю ширину огибает угол на свою глубину: без пустого столба на углу здания
        if -FX - depth < a0 <= -FX + 1e-6:
            a0 = -FX - depth
        if FX - 1e-6 <= a1 < FX + depth:
            a1 = FX + depth
    lo, hi = sorted((fixed - out * back, fixed + out * depth))
    arch = getattr(p, "route_arch", None)
    if arch is not None and min(a1 - a0, abs(y1 - y0)) >= ARCH_IN:
        p = arch
    p.noroute = getattr(p, "noroute", 0) + 1
    try:
        if axis == "x":
            p.box(lo, hi, y0, y1, a0, a1, color)
        else:
            p.box(a0, a1, y0, y1, lo, hi, color)
    finally:
        p.noroute -= 1


def quad(p, axis, fixed, out, a0, a1, y0, y1, color):
    """Плоский прямоугольник на стене, лицом в сторону out."""
    if axis == "x":
        p.plane([(fixed, y0, a0), (fixed, y0, a1), (fixed, y1, a1), (fixed, y1, a0)], [], (out, 0, 0), color)
    else:
        p.plane([(a0, y0, fixed), (a1, y0, fixed), (a1, y1, fixed), (a0, y1, fixed)], [], (0, 0, out), color)


def _frame(n, up):
    u = Vector(up).cross(n)
    if u.length < 1e-4:
        u = Vector((1, 0, 0)).cross(n)
    u.normalize()
    return u, n.cross(u).normalized()


def beam(p, a, b, w, d, color, up=(0, 1, 0)):
    """Брус между точками a и b, сечение w × d; d — вдоль up (перпендикулярно брусу)."""
    a, b = Vector(a), Vector(b)
    u, v = _frame((b - a).normalized(), up)

    def ring(c):
        return [tuple(c + u * su * w / 2 + v * sv * d / 2) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]

    p.loft(ring(a), ring(b), color)


def taper(p, a, b, w0, w1, color):
    """Сужающийся квадратный брус от a (сечение w0) к b (w1): лист, шип, луч."""
    a, b = Vector(a), Vector(b)
    u, v = _frame((b - a).normalized(), (0, 1, 0))

    def ring(c, w):
        return [tuple(c + u * su * w / 2 + v * sv * w / 2) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]

    p.loft(ring(a, w0), ring(b, w1), color)


def tube(p, pts, widths, thick, normal, color):
    """Изогнутое тело по точкам: ширина widths[i] поперёк, толщина thick вдоль normal; кольца общие — без ступенек."""
    n = Vector(normal).normalized()
    pp = [Vector(q) for q in pts]
    rings = []
    for i, c in enumerate(pp):
        t = (pp[min(i + 1, len(pp) - 1)] - pp[max(i - 1, 0)]).normalized()
        u = t.cross(n).normalized()
        w = widths[i]
        rings.append([tuple(c + u * su * w / 2 + n * sv * thick / 2) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for a, b in zip(rings, rings[1:]):
        p.loft(a, b, color)


def ring_y(p, cx, cz, r0, r1, y0, y1, color, n=16, a0=0.0, a1=360.0):
    """Кольцо (или дуга) в плане: внутренний r0, внешний r1, по высоте y0…y1 — сегментами-призмами."""
    steps = max(1, int(round(n * (a1 - a0) / 360.0)))
    for k in range(steps):
        t0 = math.radians(a0 + (a1 - a0) * k / steps)
        t1 = math.radians(a0 + (a1 - a0) * (k + 1) / steps)
        pts = [(cx + r0 * math.cos(t0), cz + r0 * math.sin(t0)), (cx + r1 * math.cos(t0), cz + r1 * math.sin(t0)),
               (cx + r1 * math.cos(t1), cz + r1 * math.sin(t1)), (cx + r0 * math.cos(t1), cz + r0 * math.sin(t1))]
        p.prism_xz(pts, y0, y1, color)


def rng(*k):
    """Детерминированное «случайное» 0…1 по ключу."""
    h = 2166136261
    for v in k:
        h = ((h ^ (int(v * 1000) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (h % 10007) / 10007.0


def rects(cells):
    """Жадное слияние клеток (c, r) в прямоугольники (c0, c1, r0, r1)."""
    left = set(cells)
    out = []
    for r, c in sorted((r, c) for c, r in cells):
        if (c, r) not in left:
            continue
        c1 = c
        while (c1 + 1, r) in left:
            c1 += 1
        r1 = r
        while all((k, r1 + 1) in left for k in range(c, c1 + 1)):
            r1 += 1
        for rr in range(r, r1 + 1):
            for k in range(c, c1 + 1):
                left.discard((k, rr))
        out.append((c, c1 + 1, r, r1 + 1))
    return out


def anchor(p, lo, hi, color="222222"):
    """Две крошечные скрытые грани в углах (lo, hi): габариты детали — ровно этот брус, его центр целый (рисунок
    материала привязан к центру детали — клетки рисунка совпадают с сеткой блоков)."""
    layer = p.bm.loops.layers.float_color["tone"]
    for (x, y, z), d in ((lo, 0.01), (hi, -0.01)):
        f = p.bm.faces.new([p.bm.verts.new(K.P(*q)) for q in ((x, y, z), (x + d, y, z), (x, y + d, z))])
        for loop in f.loops:
            loop[layer] = (*K.rgb(color), 1.0)


def chamfer(p, axis, fixed, out, a0, a1, prof, color):
    """Профильная полоса вдоль стены: prof — [(глубина наружу, y)], вытянута вдоль стены от a0 до a1."""
    pts = [(fixed + out * d, y) for d, y in prof]
    arch = getattr(p, "route_arch", None)
    if arch is not None and abs(a1 - a0) >= ARCH_IN:
        p = arch  # профильный карниз, скат, откос — часть здания
    p.noroute = getattr(p, "noroute", 0) + 1
    try:
        if axis == "z":
            p.prism_zy(pts, a0, a1, color)
        else:
            p.prism_xy(pts, a0, a1, color)
    finally:
        p.noroute -= 1


FACES = (("z", -FZ, -1, FX), ("z", FZ, 1, FX), ("x", -FX, -1, FZ), ("x", FX, 1, FZ))  # перед, тыл, лево, право
WALLS = (("x", -W, 1, ZB), ("x", W, -1, ZB), ("z", ZF, 1, W), ("z", ZB, -1, W))  # стены зала изнутри


def shell_planes(F, color_out, color_in, color_ceiling):
    """Плоскости стен снаружи (за убранством, F.FR) и внутри (F.IR, с проёмом дверей лифта), потолок зала."""
    for axis, fixed, out, half in FACES:
        quad(F.FR, axis, fixed, out, -half, half, YB, YT, color_out)
    I = F.IR
    I.plane([(-W, C, ZF), (W, C, ZF), (W, C, ZB), (-W, C, ZB)], [], (0, -1, 0), color_ceiling)
    for s in (-1, 1):
        I.plane([(s * W, 0, ZF), (s * W, 0, ZB), (s * W, C, ZB), (s * W, C, ZF)], [], (-s, 0, 0), color_in)
    I.plane([(-W, 0, ZF), (W, 0, ZF), (W, C, ZF), (-W, C, ZF)], [], (0, 0, 1), color_in)
    I.plane([(x, y, ZB) for x, y in [(-W, 0), (-DOOR[0], 0), (-DOOR[0], DOOR[1]), (DOOR[0], DOOR[1]), (DOOR[0], 0),
                                      (W, 0), (W, C), (-W, C)]], [], (0, 0, -1), color_in)


def lift_leaves(p, color, stripe, stripe_y=(5.0, 5.6)):
    """Створки дверей лифта в проёме стены каркаса (утоплены за плоскостью зала)."""
    for s in (-1, 1):
        p.box(s * 0.06, s * DOOR[0], 0, DOOR[1], 16.15, 16.45, color)
        p.box(s * 0.4, s * (DOOR[0] - 0.3), stripe_y[0], stripe_y[1], 16.0, 16.17, stripe)
