"""Общая библиотека моделей из LEGO-кирпичей для Blender (без интерфейса).

Координаты в функциях — как в Roblox: x вправо, y вверх, z назад (лицевая сторона модели смотрит в -z),
1 единица = 1 стад. При записи в Blender: (x, y, z) → (x, -z, y); экспорт FBX (-Z вперёд, Y вверх) возвращает
оси Roblox. Геометрия собирается через bmesh — по одному bmesh на «роль» (часть модели, которую игра красит
или освещает отдельно), потом каждая роль становится объектом «<Модель>_<Роль>».

Цвета — клетки общей палитры MODEL_PALETTE (8×8). Палитра пишется в assets/textures/model_palette.png
и встраивается в FBX.
"""

import json
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

GRID = 8
CELL = 16  # пикселей на клетку палитры

# Клетки палитры: имя → hex. Порядок = номер клетки.
PALETTE = [
    ("white", "FFFFFF"), ("cream", "FFF1D2"), ("lightgray", "C9CED6"), ("gray", "9AA0AA"),
    ("darkgray", "5A6170"), ("black", "1B1530"), ("wood", "A0682F"), ("darkwood", "5E3A1A"),
    ("lightwood", "C8945A"), ("stone", "A7ADB8"), ("darkstone", "6E7380"), ("iron", "7D8794"),
    ("steel", "3E4652"), ("bronze", "CD7F32"), ("darkbronze", "8C5320"), ("silver", "D5DCE4"),
    ("gold", "FFC21A"), ("darkgold", "C98E0A"), ("emerald", "2ECC71"), ("darkemerald", "128A4A"),
    ("diamond", "B9F2FF"), ("diamonddeep", "5CE1FF"), ("neonpink", "FF2BD6"), ("neoncyan", "00F0FF"),
    ("cosmic", "6A45F5"), ("cosmicdark", "1A1238"), ("star", "FFF59D"), ("red", "E53935"),
    ("darkred", "B71C1C"), ("blue", "1E88E5"), ("glass", "BFE6FF"), ("green", "43A047"),
    ("orange", "FB8C00"), ("marble", "F5F5F5"), ("marblevein", "B0BEC5"), ("terracotta", "C1502E"),
    ("moss", "3E7D2E"), ("rust", "9C4A1A"), ("lightblue", "81D4FA"), ("velvet", "8E1B1B"),
    ("pink", "F48FB1"), ("yellow", "FFD60A"), ("darkgreen", "2E7D32"), ("purple", "8E24AA"),
]
COLOR = {name: i for i, (name, _) in enumerate(PALETTE)}

# Пропорции кирпичей в стадах Roblox: шаг пупырышка 2, кирпич 2.4, пластина 0.8.
PITCH = 2.0
BRICK = 2.4
PLATE = 0.8
STUD_R, STUD_H, STUD_SEGMENTS = 0.6, 0.4, 12
BEVEL = 0.08


def to_blender(v):
    x, y, z = v
    return Vector((x, -z, y))


def hex_to_rgb(code):
    return tuple(int(code[i : i + 2], 16) / 255 for i in (0, 2, 4))


def make_palette(path):
    """Пишет PNG палитры и возвращает материал, который на неё ссылается."""
    size = GRID * CELL
    image = bpy.data.images.new("ModelPalette", width=size, height=size, alpha=False)
    pixels = [0.0] * (size * size * 4)
    for index, (_, code) in enumerate(PALETTE):
        r, g, b = hex_to_rgb(code)
        cx, cy = index % GRID, index // GRID
        for py in range(cy * CELL, (cy + 1) * CELL):
            for px in range(cx * CELL, (cx + 1) * CELL):
                i = (py * size + px) * 4
                pixels[i : i + 4] = [r, g, b, 1.0]
    image.pixels = pixels
    image.filepath_raw = path
    image.file_format = "PNG"
    image.save(filepath=path)

    material = bpy.data.materials.new("ModelPalette")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.35
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Closest"
    material.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return material


def cell_uv(color):
    index = COLOR[color] if isinstance(color, str) else color
    # В PNG строка 0 — внизу, как и v = 0 в UV.
    return ((index % GRID + 0.5) / GRID, (index // GRID + 0.5) / GRID)


class Model:
    """Модель из ролей. Каждая роль — свой bmesh; add_* кладут детали в роль."""

    def __init__(self, name):
        self.name = name
        self.roles = {}

    def bm(self, role):
        if role not in self.roles:
            bm = bmesh.new()
            bm.loops.layers.uv.verify()
            self.roles[role] = bm
        return self.roles[role]

    # --- служебное ---
    # Каждая деталь строится во временном bmesh, красится целиком и добавляется в роль. Так цвет не
    # теряется: после удаления граней bmesh кладёт новые грани на освободившиеся места, не в конец.
    def _begin(self, role):
        bm = bmesh.new()
        bm.loops.layers.uv.verify()
        return bm, role

    def _finish(self, bm, role, color):
        uv_layer = bm.loops.layers.uv.verify()
        u, v = cell_uv(color)
        for face in bm.faces:
            for loop in face.loops:
                loop[uv_layer].uv = (u, v)
        scratch = bpy.data.meshes.get("__scratch") or bpy.data.meshes.new("__scratch")
        bm.to_mesh(scratch)
        bm.free()
        self.bm(role).from_mesh(scratch)

    @staticmethod
    def _matrix(center, rotation=None):
        m = Matrix.Translation(to_blender(center))
        if rotation is not None:
            m = m @ rotation
        return m

    # --- детали ---
    def box(self, role, center, size, color, bevel=BEVEL, rotation=None, studs=False):
        """Кирпич: center и size в координатах Roblox. studs=True — пупырышки сверху (шаг PITCH)."""
        bm, start = self._begin(role)
        sx, sy, sz = size
        scale = Matrix.Diagonal((sx, sz, sy, 1.0))
        geom = bmesh.ops.create_cube(bm, size=1.0, matrix=self._matrix(center, rotation) @ scale)
        if bevel > 0:
            verts = geom["verts"]
            edges = list({e for v in verts for e in v.link_edges})
            width = min(bevel, min(size) * 0.25)
            bmesh.ops.bevel(bm, geom=edges, offset=width, segments=1, affect="EDGES", profile=0.5)
        self._finish(bm, start, color)
        if studs:
            self.studs_on(role, center, size, color, rotation)

    def studs_on(self, role, center, size, color, rotation=None, up="y"):
        """Пупырышки на верхней грани кирпича (или на грани up = '+x', '-x', '+z', '-z')."""
        sx, sy, sz = size
        if up == "y":
            nx, nz = max(1, int(round(sx / PITCH))), max(1, int(round(sz / PITCH)))
            for i in range(nx):
                for k in range(nz):
                    local = Vector((-sx / 2 + (i + 0.5) * sx / nx, sy / 2, -sz / 2 + (k + 0.5) * sz / nz))
                    self.stud(role, local, color, center, rotation, "y")
        elif up in ("+x", "-x"):
            sign = 1 if up == "+x" else -1
            ny, nz = max(1, int(round(sy / PITCH))), max(1, int(round(sz / PITCH)))
            for j in range(ny):
                for k in range(nz):
                    local = Vector((sign * sx / 2, -sy / 2 + (j + 0.5) * sy / ny, -sz / 2 + (k + 0.5) * sz / nz))
                    self.stud(role, local, color, center, rotation, up)

    def stud(self, role, local, color, center=(0, 0, 0), rotation=None, up="y"):
        """Один пупырышек: local — точка на грани относительно center (Roblox), up — куда смотрит."""
        bm, start = self._begin(role)
        orient = {
            "y": Matrix.Identity(4),
            "+x": Matrix.Rotation(math.radians(90), 4, "Y"),
            "-x": Matrix.Rotation(math.radians(-90), 4, "Y"),
            "+z": Matrix.Rotation(math.radians(90), 4, "X"),  # +Z Blender → -Y Blender = +z Roblox
            "-z": Matrix.Rotation(math.radians(-90), 4, "X"),
        }[up]
        base = self._matrix(center, rotation) @ Matrix.Translation(to_blender(local)) @ orient
        geom = bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=STUD_SEGMENTS,
            radius1=STUD_R,
            radius2=STUD_R,
            depth=STUD_H,
            matrix=base @ Matrix.Translation((0, 0, STUD_H / 2)),
        )
        # Нижняя крышка (у самой грани кирпича) не видна — убираем.
        anchor = base @ Vector((0, 0, 0))
        caps = [f for f in {f for v in geom["verts"] for f in v.link_faces} if len(f.verts) == STUD_SEGMENTS]
        if caps:
            bottom = min(caps, key=lambda f: (f.calc_center_median() - anchor).length)
            bmesh.ops.delete(bm, geom=[bottom], context="FACES_ONLY")
        self._finish(bm, start, color)

    def cylinder(self, role, center, radius, length, color, axis="y", segments=16, radius2=None, rotation=None):
        """Цилиндр (или усечённый конус, radius2) вдоль оси Roblox axis. segments=6 — шестигранник."""
        bm, start = self._begin(role)
        orient = {
            "y": Matrix.Identity(4),
            "x": Matrix.Rotation(math.radians(90), 4, "Y"),
            "z": Matrix.Rotation(math.radians(90), 4, "X"),
        }[axis]
        r2 = radius if radius2 is None else radius2
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=r2 == 0,
            segments=segments,
            radius1=radius,
            radius2=r2,
            depth=length,
            matrix=self._matrix(center, rotation) @ orient,
        )
        self._finish(bm, start, color)

    def sphere(self, role, center, radius, color, segments=12, rings=8, half=False, scale=(1, 1, 1)):
        """Шар (half=True — верхняя половина, купол)."""
        bm, start = self._begin(role)
        sx, sy, sz = scale
        m = self._matrix(center) @ Matrix.Diagonal((sx, sz, sy, 1.0))
        geom = bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius, matrix=m)
        if half:
            cz = to_blender(center).z
            below = [v for v in geom["verts"] if v.co.z < cz - 1e-4]
            bmesh.ops.delete(bm, geom=below, context="VERTS")
        self._finish(bm, start, color)

    def gem(self, role, center, radius, height_top, height_bottom, color, segments=8, axis="x", table=0.6):
        """Гранёный камень: площадка-«стол», пояс и низ-конус (как бриллиант). Стол смотрит вдоль axis
        ('x' — стол в +x, острие в -x; '-x' — наоборот)."""
        bm, start = self._begin(role)
        orient = {
            "y": Matrix.Identity(4),
            "x": Matrix.Rotation(math.radians(90), 4, "Y"),
            "-x": Matrix.Rotation(math.radians(-90), 4, "Y"),
            "z": Matrix.Rotation(math.radians(90), 4, "X"),
        }[axis]
        m = self._matrix(center) @ orient
        bmesh.ops.create_cone(
            bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius, radius2=radius * table,
            depth=height_top, matrix=m @ Matrix.Translation((0, 0, height_top / 2)),
        )
        bmesh.ops.create_cone(
            bm, cap_ends=True, cap_tris=True, segments=segments, radius1=0.001, radius2=radius,
            depth=height_bottom, matrix=m @ Matrix.Translation((0, 0, -height_bottom / 2)),
        )
        self._finish(bm, start, color)

    def torus(self, role, center, major, minor, color, axis="x", segments=20, minor_segments=8):
        """Кольцо вокруг оси Roblox axis."""
        bm, start = self._begin(role)
        orient = {
            "y": Matrix.Identity(4),
            "x": Matrix.Rotation(math.radians(90), 4, "Y"),
            "z": Matrix.Rotation(math.radians(90), 4, "X"),
        }[axis]
        m = self._matrix(center) @ orient
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
        self._finish(bm, start, color)

    def wedge(self, role, center, size, color, down="-z"):
        """Скат крыши: брусок size, у которого верх срезан наклонно; низкая сторона — down ('-z' или '+z',
        '-x', '+x')."""
        bm, start = self._begin(role)
        sx, sy, sz = size
        hx, hy, hz = sx / 2, sy / 2, sz / 2
        # Нижние 4 точки и 2 верхние у высокой стороны (Roblox, относительно центра).
        if down in ("-z", "+z"):
            high = hz if down == "-z" else -hz
            pts = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz), (-hx, hy, high), (hx, hy, high)]
        else:
            high = hx if down == "-x" else -hx
            pts = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz), (high, hy, -hz), (high, hy, hz)]
        c = Vector(center)
        verts = [bm.verts.new(to_blender(c + Vector(p))) for p in pts]
        # Грани по выпуклой оболочке — надёжнее, чем перечислять вручную.
        bmesh.ops.convex_hull(bm, input=verts)
        bm.normal_update()
        self._finish(bm, start, color)

    def gable(self, role, center, width, depth, height, color, along="z", pieces=6):
        """Двускатная крыша: конёк вдоль along, ширина поперёк, скаты из сегментов-кирпичей (швы)."""
        length = depth if along == "z" else width
        span = width if along == "z" else depth
        seg = length / pieces
        for i in range(pieces):
            t = -length / 2 + (i + 0.5) * seg
            for side in (-1, 1):
                if along == "z":
                    c = (center[0] + side * span / 4, center[1] + height / 2, center[2] + t)
                    self.wedge(role, c, (span / 2, height, seg - 0.05), color, down="-x" if side < 0 else "+x")
                else:
                    c = (center[0] + t, center[1] + height / 2, center[2] + side * span / 4)
                    self.wedge(role, c, (seg - 0.05, height, span / 2), color, down="-z" if side < 0 else "+z")

    def triangle_wall(self, role, center, width, height, thickness, color):
        """Фронтон: треугольная стена в плоскости x–y, основание width, вершина вверху."""
        bm, start = self._begin(role)
        c = Vector(center)
        pts = []
        for zz in (-thickness / 2, thickness / 2):
            pts += [(-width / 2, 0, zz), (width / 2, 0, zz), (0, height, zz)]
        verts = [bm.verts.new(to_blender(c + Vector(p))) for p in pts]
        bmesh.ops.convex_hull(bm, input=verts)
        self._finish(bm, start, color)

    def brick_wall(self, role, start, end, height, thickness, colors, y0=0.0, brick_len=8.0, studs_top=False,
                   holes=(), tops=None, seed=0):
        """Стена из кирпичей с перевязкой от start до end (в плоскости x–z, вдоль одной оси).
        colors — список цветов или пар (роль, цвет), чередуются псевдослучайно; holes — прямоугольники
        (t0, t1, y0, y1) вдоль стены, где кирпичей нет, tops — функция t → высота верха (для руин)."""
        sx, sz = start
        ex, ez = end
        along_x = abs(ex - sx) > abs(ez - sz)
        length = abs(ex - sx) if along_x else abs(ez - sz)
        sign = 1 if (ex - sx if along_x else ez - sz) > 0 else -1
        rows = int(math.ceil(height / BRICK - 1e-6))
        state = seed
        for row in range(rows):
            y_lo = y0 + row * BRICK
            y_hi = min(y0 + height, y_lo + BRICK)
            t = -(brick_len / 2 if row % 2 else 0.0)
            while t < length - 1e-6:
                a, b = max(t, 0.0), min(t + brick_len, length)
                t += brick_len
                if b - a < 0.3:
                    continue
                mid = (a + b) / 2
                if tops is not None and y_lo >= y0 + tops(mid) - 1e-6:
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
                            if h0 - p0 > 0.3:
                                nxt.append((p0, h0))
                            if p1 - h1 > 0.3:
                                nxt.append((h1, p1))
                    pieces = nxt
                for p0, p1 in pieces:
                    state = (state * 1103515245 + 12345) % 2147483648
                    pick = colors[(state >> 8) % len(colors)]
                    brick_role, color = pick if isinstance(pick, tuple) else (role, pick)
                    pm = (p0 + p1) / 2
                    if along_x:
                        cx, cz = sx + sign * pm, sz
                        size = (p1 - p0, y_hi - y_lo, thickness)
                    else:
                        cx, cz = sx, sz + sign * pm
                        size = (thickness, y_hi - y_lo, p1 - p0)
                    top_row = row == rows - 1 or (tops is not None and y_hi >= y0 + tops(pm) - 1e-6)
                    self.box(brick_role, (cx, (y_lo + y_hi) / 2, cz), size, color, studs=studs_top and top_row)

    # --- вывод ---
    def build(self, material, collection, offset=(0, 0, 0)):
        """Создаёт объекты ролей. offset — куда сдвинуть модель в файле (Roblox). Возвращает раскладку
        роли → {center, size} в координатах модели (центр габаритов = точка опоры MeshPart в Roblox)."""
        layout = {}
        for role, bm in self.roles.items():
            mesh = bpy.data.meshes.new(f"{self.name}_{role}")
            bm.normal_update()
            bm.to_mesh(mesh)
            bm.free()
            mesh.materials.append(material)
            obj = bpy.data.objects.new(f"{self.name}_{role}", mesh)
            collection.objects.link(obj)
            corners = [Vector(c) for c in obj.bound_box]
            lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
            hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
            mid = (lo + hi) / 2
            dims = hi - lo
            # Обратно в Roblox: blender (x, y, z) → (x, z, -y).
            layout[role] = {
                "center": [round(mid.x, 3), round(mid.z, 3), round(-mid.y, 3)],
                "size": [round(dims.x, 3), round(dims.z, 3), round(dims.y, 3)],
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
        path_mode="COPY",
        embed_textures=True,
    )


def setup_render(resolution=900):
    scene = bpy.context.scene
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 50))
    sun = bpy.context.active_object
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(35))
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.75, 0.95, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
    scene.world = world
    scene.view_settings.view_transform = "Standard"
    engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution


def render(path, eye, target, visible, lens=35):
    """Снимок: eye и target в координатах Roblox, visible — объекты, которые видны."""
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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
