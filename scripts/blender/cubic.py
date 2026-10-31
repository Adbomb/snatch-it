"""Кубический Roblox-стиль предметов (референс владельца, 2026-10-31): крупные блоки с мягко скруглёнными рёбрами,
на больших гранях — рельеф из «стёганых» квадратов со скруглёнными углами и мягкими канавками; яркие чистые цвета,
матовый материал. Не круглые пупырышки и не картинка: квадраты — настоящая геометрия.

Модель — набор деталей по цветам (как у гантелей): каждая роль-цвет станет MeshPart, игра ставит Color и
материал SmoothPlastic (без квадратной текстуры карты поверх своего рельефа).
Координаты — как в Roblox: x вправо, y вверх, z назад (лицевая сторона смотрит в -z), 1 = 1 стад.
"""

import math

import bmesh
import bpy
from mathutils import Matrix, Vector


def to_bl(v):
    x, y, z = v
    return Vector((x, -z, y))


def hex_rgb(code):
    return tuple((int(code[i : i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4))


# Грани блока: внешняя нормаль и оси (u, v) с u × v = нормаль (тогда лицо плитки смотрит наружу).
FACES = {
    "+x": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "-x": ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
    "+y": ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
    "-y": ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
    "+z": ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
    "-z": ((0, 0, -1), (0, 1, 0), (1, 0, 0)),
}


def _extent(size, axis):
    return abs(axis[0]) * size[0] + abs(axis[1]) * size[1] + abs(axis[2]) * size[2]


def rounded_rect(w, h, r, seg):
    """Контур прямоугольника w × h со скруглёнными углами радиуса r (против часовой в осях u, v)."""
    r = min(r, w / 2 - 1e-4, h / 2 - 1e-4)
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
                       (w / 2 - r, -h / 2 + r, 270)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


class Kit:
    """Детали по цветам. cell — размер квадрата рельефа, depth — высота плитки, gap — ширина канавки."""

    def __init__(self, name, cell=0.4, depth=0.026, gap=0.024, radius=0.09):
        self.name = name
        self.cell, self.depth, self.gap, self.radius = cell, depth, gap, radius
        self.parts = {}

    def _bm(self, color):
        if color not in self.parts:
            self.parts[color] = bmesh.new()
        return self.parts[color]

    def rounded_box(self, color, center, size, radius=None, segments=None, rotation=None):
        """Брусок с мягко скруглёнными рёбрами (без рельефа). У мелких деталей фаска в один шаг."""
        segments = segments or (1 if min(size) < 0.07 else 2)
        bm = bmesh.new()
        sx, sy, sz = size
        m = Matrix.Translation(to_bl(center))
        if rotation is not None:
            m = m @ rotation
        bmesh.ops.create_cube(bm, size=1.0, matrix=m @ Matrix.Diagonal((sx, sz, sy, 1.0)))
        r = min(radius if radius is not None else self.radius, min(size) * 0.45)
        bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=r, segments=segments, profile=0.5,
                        affect="EDGES", clamp_overlap=True)
        self._merge(color, bm)

    def tile(self, color, origin, frame, w, h, depth=None, corner=None, chamfer=None, rotation=None):
        """Плитка — скруглённый квадрат w × h, поднятый на depth над гранью (низ утоплен, его не видно)."""
        n, u, v = (Vector(a) for a in frame)
        depth = depth if depth is not None else self.depth
        corner = corner if corner is not None else min(w, h) * 0.26
        chamfer = chamfer if chamfer is not None else min(w, h) * 0.1
        o = Vector(origin)
        bm = bmesh.new()
        rot = rotation or Matrix.Identity(4)

        # Мягкий «подушечный» профиль: низ, средний пояс (60 % высоты, 40 % скоса) и верх.
        def ring(inset, height):
            pts = rounded_rect(w - 2 * inset, h - 2 * inset, max(corner - inset, 0.01), 2)
            return [bm.verts.new(rot @ to_bl(o + u * x + v * y + n * height)) for x, y in pts]

        rings = [ring(0, -0.02), ring(chamfer * 0.4, depth * 0.62), ring(chamfer, depth)]
        count = len(rings[0])
        for a, b in zip(rings, rings[1:]):
            for i in range(count):
                j = (i + 1) % count
                bm.faces.new((a[i], a[j], b[j], b[i]))
        bm.faces.new(rings[-1])
        self._merge(color, bm)

    def block(self, color, center, size, faces="+x -x +y +z -z", cell=None, tile_color=None, rotation=None,
              radius=None):
        """Блок с рельефом: скруглённое основание и сетка плиток на указанных гранях (по умолчанию все, кроме низа)."""
        cell = cell or self.cell
        depth = self.depth
        cx, cy, cz = center
        sx, sy, sz = size
        inner = (sx - 2 * depth, sy - 2 * depth, sz - 2 * depth)
        r = radius if radius is not None else self.radius
        self.rounded_box(color, center, inner, r, rotation=rotation)
        for key in faces.split():
            n, u, v = FACES[key]
            eu, ev = _extent(size, u), _extent(size, v)
            margin = r * 0.3 + depth
            ru, rv = eu - 2 * margin, ev - 2 * margin
            nu, nv = max(1, round(ru / cell)), max(1, round(rv / cell))
            step_u, step_v = ru / nu, rv / nv
            half = _extent(inner, n) / 2
            for i in range(nu):
                for j in range(nv):
                    du = -ru / 2 + step_u * (i + 0.5)
                    dv = -rv / 2 + step_v * (j + 0.5)
                    p = Vector((cx, cy, cz)) + Vector(n) * half + Vector(u) * du + Vector(v) * dv
                    if rotation is not None:
                        p = Vector((cx, cy, cz)) + (rotation_roblox(rotation) @ (p - Vector((cx, cy, cz))))
                    frame = (n, u, v) if rotation is None else tuple(tuple(rotation_roblox(rotation) @ Vector(a))
                                                                     for a in (n, u, v))
                    self.tile(tile_color or color, p, frame, step_u - self.gap, step_v - self.gap)

    def _merge(self, color, bm):
        scratch = bpy.data.meshes.get("__cubic") or bpy.data.meshes.new("__cubic")
        bm.to_mesh(scratch)
        bm.free()
        self._bm(color).from_mesh(scratch)

    def build(self, collection, smooth_angle=48):
        """Объекты «<имя>_<цвет>» со сглаживанием по углу (скругления мягкие, плитки и грани — чёткие)."""
        objects = []
        for color, bm in self.parts.items():
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
            bm.normal_update()
            mesh = bpy.data.meshes.new(f"{self.name}_{color}")
            bm.to_mesh(mesh)
            bm.free()
            for poly in mesh.polygons:
                poly.use_smooth = True
            obj = bpy.data.objects.new(f"{self.name}_{color}", mesh)
            collection.objects.link(obj)
            objects.append(obj)
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth_angle))
        self.parts = {}
        return objects


def rotation_roblox(rotation):
    """Поворот Blender (4×4) → поворот 3×3 в осях Roblox (для плиток повёрнутого блока)."""
    to = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
    return to.transposed() @ rotation.to_3x3() @ to


def rot(x=0.0, y=0.0, z=0.0):
    """Поворот в градусах вокруг осей Roblox (как lego.rot)."""
    return (Matrix.Rotation(math.radians(y), 4, "Z") @ Matrix.Rotation(math.radians(x), 4, "X")
            @ Matrix.Rotation(math.radians(-z), 4, "Y"))


def triangles(objects):
    total = 0
    for obj in objects:
        obj.data.calc_loop_triangles()
        total += len(obj.data.loop_triangles)
    return total
