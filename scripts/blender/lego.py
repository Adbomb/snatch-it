"""Общая библиотека моделей из LEGO-кирпичей для Blender (без интерфейса).

Стиль (референс заказчика): крупные простые формы из кирпичей с мягкой фаской; рисунок LEGO (пупырышки)
даёт не геометрия, а материал игры: MaterialVariant «LegoStuds» ложится на MeshPart сам, с той же
плотностью, что на земле и стенах (проверено в Studio). Поэтому цвет не запекается в текстуру: каждая
модель — набор деталей по цветам («ролям»), игра ставит MeshPart цвет Color и материал Plastic.

Роли: имя цвета из PALETTE (Body), «Decor_<цвет>» (декор), Accent / AccentDark (цвет участка и его тёмный
оттенок — красит игра), DecorAccent (декор цвета участка), «Glass_<цвет>» (стекло), «Glow_<цвет>» (неон).
Объект в FBX — «<Модель>_<Роль>».

Координаты в функциях — как в Roblox: x вправо, y вверх, z назад (лицевая сторона модели смотрит в -z),
1 единица = 1 стад. В Blender: (x, y, z) → (x, -z, y); экспорт FBX (-Z вперёд, Y вверх) возвращает оси Roblox.
"""

import json
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

# Цвета деталей (hex без #). Игра берёт их из layout.json.
PALETTE = {
    "white": "F4F4F0", "cream": "EFE4CC", "sand": "D9C7A0", "stone": "B9B3A6", "darkstone": "8C877C",
    "slate": "4E5866", "darkslate": "333B46", "gold": "F2B51E", "darkgold": "B8860B", "wood": "A0682F",
    "darkwood": "6B4423", "lightwood": "C8945A", "iron": "7D8794", "steel": "4A525E", "black": "23252B",
    "bronze": "C67A35", "darkbronze": "8C5320", "silver": "D7DDE4", "emerald": "2ECC71",
    "darkemerald": "138A4C", "diamond": "BFF3FF", "red": "D93B30", "velvet": "9E1B1B", "glass": "A9DDF5",
    "cosmic": "6A45F5", "cosmicdark": "241A4D", "star": "FFF2A6", "green": "43A047", "leaf": "5BC24A",
    "pink": "F28DB2", "yellow": "FFD23F", "orange": "F28C28", "rock": "8F8A84", "darkrock": "5F5B57",
    "neongreen": "39FF6A", "neoncyan": "2CF6FF", "ruby": "E0115F",
}
SPECIAL = {"Accent", "AccentDark", "DecorAccent"}
PREFIXED = {"Decor", "Glass", "Glow"}  # роль «<Префикс>_<цвет>»
PREVIEW_SPECIAL = {"Accent": "2F6FD6", "AccentDark": "1F3F7A", "DecorAccent": "2F6FD6"}

BRICK = 2.4  # высота кирпича, стадов
BEVEL = 0.22


def to_blender(v):
    x, y, z = v
    return Vector((x, -z, y))


def hex_to_rgb(code):
    return tuple((int(code[i : i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4))  # sRGB → линейный


def role_of(role, color):
    if role in SPECIAL:
        return role
    if role in PREFIXED:
        return f"{role}_{color}"
    return color


def rot(x=0.0, y=0.0, z=0.0):
    """Поворот в градусах вокруг осей Roblox (y — рыскание, x — тангаж, z — крен)."""
    return (
        Matrix.Rotation(math.radians(y), 4, "Z")
        @ Matrix.Rotation(math.radians(x), 4, "X")
        @ Matrix.Rotation(math.radians(-z), 4, "Y")
    )


def role_color(role):
    """Имя цвета роли: «Decor_gold» → gold, «Accent» → Accent."""
    prefix, _, rest = role.partition("_")
    return rest if prefix in PREFIXED and rest else role


def _bevel(bm, width, segments=None):
    """Фаска на острых рёбрах (между гранями больше ~30°): мягкие края, как у кирпичей на референсе.
    Мелкая фаска — один сегмент (дешевле), крупная — два (мягче)."""
    if width <= 0:
        return
    if segments is None:
        segments = 2 if width >= 0.3 else 1
    bm.normal_update()
    edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > 0.5]
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=width, segments=segments, affect="EDGES", profile=0.5,
                        clamp_overlap=True)


class Model:
    """Модель из ролей-цветов. Каждая деталь строится во временном bmesh и добавляется в роль."""

    def __init__(self, name):
        self.name = name
        self.roles = {}

    def _add(self, role, color, build, bevel):
        bm = bmesh.new()
        build(bm)
        _bevel(bm, bevel)
        scratch = bpy.data.meshes.get("__scratch") or bpy.data.meshes.new("__scratch")
        bm.to_mesh(scratch)
        bm.free()
        key = role_of(role, color)
        if key not in self.roles:
            self.roles[key] = bmesh.new()
        self.roles[key].from_mesh(scratch)

    @staticmethod
    def _matrix(center, rotation=None):
        m = Matrix.Translation(to_blender(center))
        if rotation is not None:
            m = m @ rotation
        return m

    @staticmethod
    def _axis(axis):
        return {
            "y": Matrix.Identity(4),
            "x": Matrix.Rotation(math.radians(90), 4, "Y"),
            "-x": Matrix.Rotation(math.radians(-90), 4, "Y"),
            "z": Matrix.Rotation(math.radians(90), 4, "X"),
        }[axis]

    # --- детали ---
    def box(self, role, center, size, color, bevel=BEVEL, rotation=None):
        sx, sy, sz = size
        bevel = min(bevel, min(size) * 0.3)

        def build(bm):
            bmesh.ops.create_cube(bm, size=1.0, matrix=self._matrix(center, rotation) @ Matrix.Diagonal((sx, sz, sy, 1.0)))

        self._add(role, color, build, bevel)

    def cylinder(self, role, center, radius, length, color, axis="y", segments=20, radius2=None, rotation=None,
                 bevel=BEVEL):
        r2 = radius if radius2 is None else radius2
        bevel = min(bevel, length * 0.3, radius * 0.3)

        def build(bm):
            bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=r2 == 0, segments=segments, radius1=radius, radius2=r2,
                                  depth=length, matrix=self._matrix(center, rotation) @ self._axis(axis))

        self._add(role, color, build, bevel if r2 > 0 else 0)

    def sphere(self, role, center, radius, color, segments=20, rings=12, half=False, scale=(1, 1, 1)):
        sx, sy, sz = scale

        def build(bm):
            m = self._matrix(center) @ Matrix.Diagonal((sx, sz, sy, 1.0))
            geom = bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius, matrix=m)
            if half:
                cz = to_blender(center).z
                below = [v for v in geom["verts"] if v.co.z < cz - 1e-4]
                bmesh.ops.delete(bm, geom=below, context="VERTS")
                # Закрыть низ купола.
                edges = [e for e in bm.edges if e.is_boundary]
                if edges:
                    bmesh.ops.holes_fill(bm, edges=edges, sides=0)

        self._add(role, color, build, 0)

    def gem(self, role, center, radius, height_top, height_bottom, color, segments=8, axis="x", table=0.6):
        """Гранёный камень: стол смотрит вдоль axis, остриё — в обратную сторону."""

        def build(bm):
            m = self._matrix(center) @ self._axis(axis)
            bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius,
                                  radius2=radius * table, depth=height_top,
                                  matrix=m @ Matrix.Translation((0, 0, height_top / 2)))
            bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=segments, radius1=0.001, radius2=radius,
                                  depth=height_bottom, matrix=m @ Matrix.Translation((0, 0, -height_bottom / 2)))
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)

        self._add(role, color, build, 0)

    def torus(self, role, center, major, minor, color, axis="x", segments=24, minor_segments=8):
        def build(bm):
            m = self._matrix(center) @ self._axis(axis)
            rings = []
            for i in range(segments):
                a = 2 * math.pi * i / segments
                ring = []
                for j in range(minor_segments):
                    b = 2 * math.pi * j / minor_segments
                    r = major + minor * math.cos(b)
                    ring.append(bm.verts.new(m @ Vector((r * math.cos(a), r * math.sin(a), minor * math.sin(b)))))
                rings.append(ring)
            for i in range(segments):
                a, b = rings[i], rings[(i + 1) % segments]
                for j in range(minor_segments):
                    k = (j + 1) % minor_segments
                    bm.faces.new((a[j], b[j], b[k], a[k]))

        self._add(role, color, build, 0)

    def wedge(self, role, center, size, color, down="-z", bevel=0.12):
        """Скат: брусок size со срезанным верхом; низкая сторона — down ('-z', '+z', '-x', '+x')."""
        sx, sy, sz = size
        hx, hy, hz = sx / 2, sy / 2, sz / 2

        def build(bm):
            if down in ("-z", "+z"):
                high = hz if down == "-z" else -hz
                pts = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz), (-hx, hy, high), (hx, hy, high)]
            else:
                high = hx if down == "-x" else -hx
                pts = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz), (high, hy, -hz), (high, hy, hz)]
            c = Vector(center)
            verts = [bm.verts.new(to_blender(c + Vector(p))) for p in pts]
            bmesh.ops.convex_hull(bm, input=verts)

        self._add(role, color, build, bevel)

    def gable(self, role, center, width, depth, height, color, along="z", pieces=6):
        """Двускатная крыша: конёк вдоль along; каждый скат — ряд сегментов (швы как у кирпичей).
        center — середина основания крыши."""
        length = depth if along == "z" else width
        span = width if along == "z" else depth
        seg = length / pieces
        for i in range(pieces):
            t = -length / 2 + (i + 0.5) * seg
            for side in (-1, 1):
                if along == "z":
                    c = (center[0] + side * span / 4, center[1] + height / 2, center[2] + t)
                    self.wedge(role, c, (span / 2, height, seg - 0.06), color, down="-x" if side < 0 else "+x")
                else:
                    c = (center[0] + t, center[1] + height / 2, center[2] + side * span / 4)
                    self.wedge(role, c, (seg - 0.06, height, span / 2), color, down="-z" if side < 0 else "+z")

    def brick_wall(self, role, start, end, height, thickness, color, y0=0.0, brick_len=6.0, holes=(), seed=0,
                   alt_color=None, alt_every=0):
        """Стена из кирпичей с перевязкой (швы видны по фаске) от start до end в плоскости x–z.
        holes — (t0, t1, y0, y1) вдоль стены без кирпичей. alt_color — изредка другой оттенок (каждый
        alt_every-й кирпич по псевдослучайному закону)."""
        sx, sz = start
        ex, ez = end
        along_x = abs(ex - sx) > abs(ez - sz)
        length = abs(ex - sx) if along_x else abs(ez - sz)
        sign = 1 if (ex - sx if along_x else ez - sz) > 0 else -1
        rows = int(math.ceil(height / BRICK - 1e-6))
        state = seed + 1
        for row in range(rows):
            y_lo = y0 + row * BRICK
            y_hi = min(y0 + height, y_lo + BRICK)
            t = -(brick_len / 2 if row % 2 else 0.0)
            while t < length - 1e-6:
                a, b = max(t, 0.0), min(t + brick_len, length)
                t += brick_len
                if b - a < 0.4:
                    continue
                pieces = [(a, b)]
                for h0, h1, hy0, hy1 in holes:
                    if y_hi <= y0 + hy0 + 1e-6 or y_lo >= y0 + hy1 - 1e-6:
                        continue
                    nxt = []
                    for p0, p1 in pieces:
                        if p1 <= h0 or p0 >= h1:
                            nxt.append((p0, p1))
                        else:
                            if h0 - p0 > 0.4:
                                nxt.append((p0, h0))
                            if p1 - h1 > 0.4:
                                nxt.append((h1, p1))
                    pieces = nxt
                for p0, p1 in pieces:
                    state = (state * 1103515245 + 12345) % 2147483648
                    c = alt_color if alt_color and alt_every and (state >> 10) % alt_every == 0 else color
                    pm = (p0 + p1) / 2
                    if along_x:
                        center, size = (sx + sign * pm, (y_lo + y_hi) / 2, sz), (p1 - p0, y_hi - y_lo, thickness)
                    else:
                        center, size = (sx, (y_lo + y_hi) / 2, sz + sign * pm), (thickness, y_hi - y_lo, p1 - p0)
                    self.box(role, center, size, c, bevel=0.14)

    def prism_triangle(self, role, center, width, height, depth, color, bevel=0.2):
        """Треугольная призма (фронтон): основание width по x на высоте center.y, вершина вверху, толщина по z."""
        x, y, z = center

        def build(bm):
            pts = []
            for dz in (-depth / 2, depth / 2):
                pts += [(x - width / 2, y, z + dz), (x + width / 2, y, z + dz), (x, y + height, z + dz)]
            verts = [bm.verts.new(to_blender(p)) for p in pts]
            bmesh.ops.convex_hull(bm, input=verts)

        self._add(role, color, build, bevel)

    def vase(self, role, center, height, color):
        """Классическая ваза-урна на ножке."""
        x, y, z = center
        k = height / 3.0
        self.box(role, (x, y + 0.2 * k, z), (1.4 * k, 0.4 * k, 1.4 * k), color, bevel=0.1 * k)
        self.cylinder(role, (x, y + 0.65 * k, z), 0.35 * k, 0.5 * k, color, segments=12, bevel=0.05 * k)
        self.cylinder(role, (x, y + 1.35 * k, z), 0.6 * k, 0.9 * k, color, segments=14, radius2=0.95 * k, bevel=0.08 * k)
        self.cylinder(role, (x, y + 2.15 * k, z), 0.95 * k, 0.7 * k, color, segments=14, radius2=0.7 * k, bevel=0.08 * k)
        self.cylinder(role, (x, y + 2.7 * k, z), 0.8 * k, 0.4 * k, color, segments=14, bevel=0.06 * k)

    def stepped_triangle(self, role, center, width, height, depth, color, step=1.2, inset=0.0):
        """Фронтон лесенкой из кирпичей (как LEGO): ряды шириной от width до ~2*step, в плоскости x–y."""
        x, y, z = center
        rows = max(1, int(round(height / step)))
        for i in range(rows):
            w = width * (1 - i / rows) - inset
            if w < step:
                break
            self.box(role, (x, y + (i + 0.5) * step, z), (w, step, depth), color, bevel=0.14)

    def voxel_disc(self, role, center, radius, thickness, color, axis="x", cell=1.2, bevel=0.18):
        """Круг из горизонтальных брусков-рядов (LEGO-«пиксельный» диск), плоскость поперёк axis ('x' или 'y')."""
        x, y, z = center
        rows = int(radius / cell)
        for i in range(-rows, rows):
            v = (i + 0.5) * cell
            half = math.sqrt(max(radius * radius - v * v, 0))
            w = max(cell, round(2 * half / cell) * cell)
            if axis == "x":
                self.box(role, (x, y + v, z), (thickness, cell, w), color, bevel=bevel)
            else:
                self.box(role, (x + v, y, z), (w, thickness, cell), color, bevel=bevel)

    def voxel_ball(self, role, center, radius, color, cell=1.2, bevel=0.18):
        """Шар из слоёв-дисков (как собранный из кирпичей)."""
        x, y, z = center
        layers = int(radius / cell)
        for i in range(-layers, layers):
            v = (i + 0.5) * cell
            r = math.sqrt(max(radius * radius - v * v, 0))
            if r >= cell * 0.6:
                self.voxel_disc(role, (x + v, y, z), r, cell, color, axis="x", cell=cell, bevel=bevel)

    # --- вывод ---
    def build(self, collection, offset=(0, 0, 0)):
        """Создаёт объекты ролей (без материала — для FBX). Возвращает раскладку роль → центр, размер, цвет."""
        layout = {}
        for role, bm in self.roles.items():
            mesh = bpy.data.meshes.new(f"{self.name}_{role}")
            bm.normal_update()
            bm.to_mesh(mesh)
            bm.free()
            obj = bpy.data.objects.new(f"{self.name}_{role}", mesh)
            collection.objects.link(obj)
            corners = [Vector(c) for c in obj.bound_box]
            lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
            hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
            mid, dims = (lo + hi) / 2, hi - lo
            color = role_color(role)
            layout[role] = {
                "center": [round(mid.x, 3), round(mid.z, 3), round(-mid.y, 3)],
                "size": [round(dims.x, 3), round(dims.z, 3), round(dims.y, 3)],
                "color": PALETTE.get(color, color),
                "decor": role.startswith("Decor_") or role == "DecorAccent",
                "material": "Glass" if role.startswith("Glass_") else "Neon" if role.startswith("Glow_") else "Plastic",
                "triangles": sum(len(p.vertices) - 2 for p in mesh.polygons),
            }
            obj.location = to_blender(offset)
        self.roles = {}
        return layout


def export_fbx(path, objects):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
        mesh_smooth_type="FACE",
        path_mode="STRIP",  # без материалов и текстур: цвет и материал ставит игра
    )


def preview_materials(objects, studs_texture):
    """Материалы только для превью: цвет роли × текстура пупырышков (4 стада на плитку), как в игре."""
    image = bpy.data.images.load(studs_texture)
    cache = {}
    for obj in objects:
        role = obj.name.split("_", 1)[1]
        color = role_color(role)
        glow = role.startswith("Glow_")
        code = PREVIEW_SPECIAL.get(color) or PALETTE.get(color, "FF00FF")
        key = code + ("g" if glow else "")
        if key not in cache:
            mat = bpy.data.materials.new("P_" + code)
            mat.use_nodes = True
            nt = mat.node_tree
            bsdf = nt.nodes["Principled BSDF"]
            bsdf.inputs["Roughness"].default_value = 0.45
            coord = nt.nodes.new("ShaderNodeTexCoord")
            mapping = nt.nodes.new("ShaderNodeMapping")
            mapping.inputs["Scale"].default_value = (0.25, 0.25, 0.25)
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = image
            tex.projection = "BOX"
            tex.projection_blend = 0.2
            mix = nt.nodes.new("ShaderNodeMixRGB")
            mix.blend_type = "MULTIPLY"
            mix.inputs["Fac"].default_value = 1.0
            mix.inputs["Color2"].default_value = (*hex_to_rgb(code), 1)
            nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
            nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
            nt.links.new(tex.outputs["Color"], mix.inputs["Color1"])
            nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
            if glow:
                bsdf.inputs["Emission Color"].default_value = (*hex_to_rgb(code), 1)
                bsdf.inputs["Emission Strength"].default_value = 2.5
            cache[key] = mat
        obj.data.materials.clear()
        obj.data.materials.append(cache[key])


def setup_render(resolution=900):
    scene = bpy.context.scene
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 50))
    sun = bpy.context.active_object
    sun.data.energy = 3.2
    sun.rotation_euler = (math.radians(50), math.radians(8), math.radians(-35))
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.45, 0.68, 0.95, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    scene.world = world
    scene.view_settings.view_transform = "Standard"
    engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution


def render(path, eye, target, visible, lens=35):
    scene = bpy.context.scene
    for obj in scene.objects:
        if obj.type == "MESH":
            obj.hide_render = obj not in visible
    cam = scene.camera
    if cam is None:
        bpy.ops.object.camera_add()
        cam = bpy.context.active_object
        scene.camera = cam
    cam.data.lens = lens
    cam.location = to_blender(eye)
    cam.rotation_euler = (cam.location - to_blender(target)).to_track_quat("Z", "Y").to_euler()
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def write_json(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
