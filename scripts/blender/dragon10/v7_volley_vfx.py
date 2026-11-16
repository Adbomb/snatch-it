"""Эффекты «Королевского магического залпа» для превью в Blender (не для игры): магический круг с вращающимися
золотыми рунами, три полосы-предупреждения на земле, три снаряда (бирюзовое ядро, золотое кольцо, фиолетовый след),
вспышка выстрела, распад при ударе, тестовая цель и колонна-препятствие.

Положения берутся из volley_sim (та же модель, что для сервера): что видно — то и считается попаданием. Ширина
полосы = диаметр снаряда для попадания, у цели виден круг её капсулы.
Бюджет как для слабых телефонов: на снаряд — 3 детали (ядро, кольцо, след), круг — 1 деталь с текстурой в игре
(здесь — меш), без источников света; вспышка и распад — по 6–8 мелких деталей на 0.3 с.
Зависит от Blender, volley_sim.py.
"""

import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import volley_sim as VS

V = Vector
STUDS = 2.795
U = 1.0 / STUDS  # стад → единица модели

GOLD, GOLD_D, TURQ, PURPLE, WHITE = (1.0, 0.72, 0.12), (0.8, 0.5, 0.06), (0.18, 0.92, 0.85), (0.6, 0.2, 0.75), (1, 1, 1)


def emat(name, col, strength=2.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Emission Color"].default_value = (*col, 1)
    b.inputs["Emission Strength"].default_value = strength
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Roughness"].default_value = 0.4
    try:
        m.surface_render_method = "BLENDED"
    except (AttributeError, TypeError):
        m.blend_method = "BLEND"
    return m


def set_mat(m, strength=None, alpha=None, col=None):
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    if strength is not None:
        b.inputs["Emission Strength"].default_value = strength
    if alpha is not None:
        b.inputs["Alpha"].default_value = alpha
    if col is not None:
        b.inputs["Base Color"].default_value = (*col, 1)
        b.inputs["Emission Color"].default_value = (*col, 1)


def mesh_obj(col, name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    return o


def ring(r0, r1, n=24, z=0.0):
    verts = [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), z) for r in (r0, r1) for i in range(n)]
    faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return verts, faces


def octa(r, stretch=1.0):
    verts = [(r, 0, 0), (-r, 0, 0), (0, r, 0), (0, -r, 0), (0, 0, r * stretch), (0, 0, -r * stretch)]
    faces = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
    return verts, faces


def box(x0, x1, y0, y1, z0, z1):
    v = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return v, f


def join(parts):
    verts, faces = [], []
    for v, f in parts:
        base = len(verts)
        verts += v
        faces += [tuple(i + base for i in face) for face in f]
    return verts, faces


class Volley:
    """Объекты эффектов и их обновление по кадру симуляции."""

    def __init__(self, col, prm=None, obstacles=()):
        self.prm = dict(VS.PARAMS, **(prm or {}))
        rp = self.prm["radius"] * U
        self.m = {
            "gold": emat("vfx_gold", GOLD, 3.0), "turq": emat("vfx_turq", TURQ, 4.0),
            "purple": emat("vfx_purple", PURPLE, 2.0, 0.55), "lane": [emat(f"vfx_lane{i}", GOLD, 1.0, 0.3) for i in range(3)],
            "line": [emat(f"vfx_line{i}", GOLD, 2.0, 0.7) for i in range(3)], "flash": emat("vfx_flash", WHITE, 8.0, 0.9),
            "burst": [emat(f"vfx_burst{i}", TURQ, 5.0, 0.9) for i in range(3)], "circle_glow": emat("vfx_cglow", TURQ, 3.0, 0.35),
            "target": emat("vfx_target", (0.92, 0.94, 1.0), 0.4, 1.0), "foot": emat("vfx_foot", (1, 1, 1), 0.6, 0.5),
            "pillar": emat("vfx_pillar", (0.42, 0.4, 0.46), 0.0, 1.0),
        }
        for k in ("target", "pillar"):
            b = next(n for n in self.m[k].node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            b.inputs["Roughness"].default_value = 0.8
            try:
                self.m[k].surface_render_method = "DITHERED"
            except (AttributeError, TypeError):
                pass
        # магический круг: золотое кольцо, бирюзовое внутреннее, 8 рун, фиолетовый диск
        R = 1.15
        runes = []
        for i in range(8):
            a = 2 * math.pi * i / 8
            c, s = math.cos(a), math.sin(a)
            cx, cy = 0.95 * c, 0.95 * s
            w = 0.09
            pts = [(cx + c * w * 1.6, cy + s * w * 1.6), (cx - s * w, cy + c * w), (cx - c * w * 1.6, cy - s * w * 1.6),
                   (cx + s * w, cy - c * w)]
            runes.append(([(x, y, 0.01) for x, y in pts], [(0, 1, 2, 3)]))
        self.circle = mesh_obj(col, "MagicCircle", *join([ring(R - 0.09, R), ring(0.62, 0.7)] + runes), self.m["gold"])
        inner = mesh_obj(col, "MagicCircleInner", *ring(0.0, 0.62, 24), self.m["circle_glow"])
        inner.parent = self.circle
        turq_ring = mesh_obj(col, "MagicCircleTurq", *ring(0.78, 0.84, 24, 0.005), self.m["turq"])
        turq_ring.parent = self.circle
        # полосы на земле (единичные по длине, тянутся масштабом)
        self.lanes, self.lines = [], []
        for i in range(3):
            lane = mesh_obj(col, f"Lane{i}", [(-1, 0, 0), (1, 0, 0), (1, 1, 0), (-1, 1, 0)], [(0, 1, 2, 3)],
                            self.m["lane"][i])
            line = mesh_obj(col, f"LaneLine{i}", [(-1, 0, 0), (1, 0, 0), (1, 1, 0), (-1, 1, 0)], [(0, 1, 2, 3)],
                            self.m["line"][i])
            self.lanes.append(lane)
            self.lines.append(line)
        # снаряды: ядро, кольцо, след
        self.proj = []
        for i in range(3):
            core = mesh_obj(col, f"Bolt{i}", *octa(rp, 1.25), self.m["turq"])
            rng = mesh_obj(col, f"BoltRing{i}", *ring(rp * 1.05, rp * 1.3, 12), self.m["gold"])
            trail = mesh_obj(col, f"BoltTrail{i}", [(0, 0, 0), (rp * 0.7, 0, 0), (-rp * 0.7, 0, 0), (0, rp * 0.7, 0),
                                                    (0, -rp * 0.7, 0), (0, 0, -rp * 4.0)],
                             [(1, 3, 5), (3, 2, 5), (2, 4, 5), (4, 1, 5), (1, 3, 0), (3, 2, 0), (2, 4, 0), (4, 1, 0)],
                             self.m["purple"])
            self.proj.append((core, rng, trail))
        self.flash = mesh_obj(col, "LaunchFlash", *octa(1.0), self.m["flash"])
        self.bursts = []
        for i in range(3):
            parts = [ring(0.7, 0.85, 16)]
            for k in range(6):
                a = 2 * math.pi * k / 6
                v, f = octa(0.12, 1.6)
                parts.append(([(x + math.cos(a), y + math.sin(a), z) for x, y, z in v], f))
            self.bursts.append(mesh_obj(col, f"Burst{i}", *join(parts), self.m["burst"][i]))
        # тестовая цель (≈ R15: 5 стадов ростом) и круг её капсулы на земле
        h, w = 5.0 * U, 2.0 * U
        body = join([box(-w / 2, w / 2, -0.25 * w, 0.25 * w, 2.2 * U, 4.0 * U),
                     box(-0.3 * w, 0.3 * w, -0.25 * w, 0.25 * w, 4.05 * U, h),
                     box(-w / 2, -0.06 * w, -0.2 * w, 0.2 * w, 0.0, 2.15 * U),
                     box(0.06 * w, w / 2, -0.2 * w, 0.2 * w, 0.0, 2.15 * U)])
        self.target = mesh_obj(col, "TestTarget", *body, self.m["target"])
        pr = self.prm["player_radius"] * U
        self.foot = mesh_obj(col, "TargetFoot", *ring(pr - 0.04, pr, 24, 0.02), self.m["foot"])
        self.col = col
        self.pillars = []
        self.set_obstacles(obstacles)
        self.hide_all()

    def set_obstacles(self, obstacles):
        for p in self.pillars:
            bpy.data.objects.remove(p)
        self.pillars = []
        for o in obstacles:
            p = mesh_obj(self.col, "Pillar", *box(-o.r * U, o.r * U, -o.r * U, o.r * U, 0.0, o.h * U), self.m["pillar"])
            p.location = (o.x * U, o.y * U, 0.0)
            self.pillars.append(p)

    def hide_all(self):
        for o in [self.circle, self.flash, self.target, self.foot] + self.lanes + self.lines + self.bursts + \
                [x for t in self.proj for x in t]:
            o.hide_render = True
        for c in self.circle.children:
            c.hide_render = True

    def update(self, t, frame, launch, show_target=True, ended_at=None):
        """Состояние эффектов в момент t (с от начала клипа) по кадру симуляции frame."""
        prm = self.prm
        L = V(launch) * U
        feet = V(frame["feet"]) * U
        aim = V(frame["aim"]) * U
        locked, canceled = frame["locked"], frame["canceled"]
        fire = prm["fire"]
        self.target.hide_render = self.foot.hide_render = not show_target
        self.target.location = feet
        self.foot.location = (feet.x, feet.y, 0.0)
        hit_now = any(p[4] == "попал в игрока" and p[3] is not None and 0 <= t - fire - p[3] < 0.35 for p in frame["proj"])
        set_mat(self.m["target"], strength=3.0 if hit_now else 0.0, col=(1.0, 0.25, 0.2) if hit_now else (0.82, 0.84, 0.9))
        # круг: появляется с track_from до +0.4, вращается, ярче при фиксации, гаснет после выстрела
        d = (aim - L).normalized()
        flat = V((d.x, d.y, 0)).normalized()
        q = flat.to_track_quat("Z", "Y")
        grow = min(max((t - prm["track_from"] + 0.3) / 0.4, 0.0), 1.0)
        fade = 1.0 - min(max((t - fire - 0.1) / 0.25, 0.0), 1.0)
        cut = 1.0 if not canceled else max(0.0, 1.0 - (t - (ended_at or t)) / 0.2)
        k = grow * fade * cut
        self.circle.hide_render = k <= 0.01
        for c in self.circle.children:
            c.hide_render = k <= 0.01
        self.circle.matrix_world = Matrix.Translation(L) @ q.to_matrix().to_4x4() @ \
            Matrix.Rotation(math.radians(140 * t), 4, "Z") @ Matrix.Scale(max(k, 0.01), 4)
        set_mat(self.m["gold"], strength=3.0 + (4.0 if locked and t < fire + 0.1 else 0.0))
        # полосы: от проекции круга до касания земли; золотые и бледные при слежении, бирюзовые после фиксации
        ln = VS.lanes(launch, frame["aim"], prm)
        for i, side in enumerate((-1, 0, 1)):
            (x0, y0), (x1, y1), width = ln[side]
            a, b = V((x0, y0, 0.02)) * U, V((x1, y1, 0.02)) * U
            a.z = b.z = 0.02 + 0.002 * i
            vis = t >= prm["track_from"] and not (canceled and t >= (ended_at or 0) + 0.2)
            pr = next((p for p in frame["proj"] if p[0] == side), None)
            after = 0.0
            if pr is not None:
                after = t - fire - (pr[3] if pr[3] is not None else 99)
            alpha_k = 1.0 if after < 0 else max(0.0, 1.0 - after / 0.25)
            for o, mat, wk in ((self.lanes[i], self.m["lane"][i], 1.0), (self.lines[i], self.m["line"][i], 0.12)):
                o.hide_render = not vis or alpha_k <= 0.01
                dirv = b - a
                m = Matrix.Translation(a) @ V((dirv.x, dirv.y, 0)).to_track_quat("Y", "Z").to_matrix().to_4x4() @ \
                    Matrix.Diagonal((width * U / 2 * wk, dirv.length, 1, 1))
                o.matrix_world = m
                pulse = 0.5 + 0.5 * math.sin(t * 18)
                if locked:
                    set_mat(mat, col=TURQ, strength=(2.2 + 1.2 * pulse) * (1 if wk == 1.0 else 1.8),
                            alpha=(0.42 if wk == 1.0 else 0.85) * alpha_k)
                else:
                    set_mat(mat, col=GOLD, strength=0.9 if wk == 1.0 else 1.6, alpha=(0.22 if wk == 1.0 else 0.55))
        # снаряды
        for i, side in enumerate((-1, 0, 1)):
            core, rng, trail = self.proj[i]
            pr = next((p for p in frame["proj"] if p[0] == side), None)
            alive = pr is not None and pr[2]
            for o in (core, rng, trail):
                o.hide_render = not alive
            if alive:
                pos = V(pr[1]) * U
                dirs, _ = VS.aim_dirs(launch, (frame["aim"][0], frame["aim"][1], frame["aim"][2] - prm["aim_height"]),
                                      prm)
                dv = V(dirs[side])
                rot = dv.to_track_quat("Z", "Y").to_matrix().to_4x4()
                core.matrix_world = Matrix.Translation(pos) @ rot @ Matrix.Rotation(math.radians(400 * t), 4, "Z")
                rng.matrix_world = Matrix.Translation(pos) @ rot @ Matrix.Rotation(math.radians(-300 * t), 4, "Z")
                trail.matrix_world = Matrix.Translation(pos) @ rot
            # распад: на месте исчезновения, 0.3 с
            burst = self.bursts[i]
            if pr is not None and pr[3] is not None and pr[4] != "бой окончен":
                age = t - fire - pr[3]
                burst.hide_render = not (0 <= age < 0.32)
                if not burst.hide_render:
                    pos = V(pr[1]) * U
                    sc = 0.4 + 2.2 * age
                    up = V((0, 0, 1)) if pr[4] in ("земля",) else (V(pr[1]) * U - L).normalized()
                    burst.matrix_world = Matrix.Translation(pos) @ up.to_track_quat("Z", "Y").to_matrix().to_4x4() @ \
                        Matrix.Scale(sc, 4)
                    set_mat(self.m["burst"][i], strength=6.0 * (1 - age / 0.32), alpha=0.9 * (1 - age / 0.32),
                            col=(1.0, 0.35, 0.3) if pr[4] == "попал в игрока" else TURQ)
            elif pr is not None and pr[4] == "бой окончен":
                age = t - fire - pr[3]
                burst.hide_render = not (0 <= age < 0.2)
                if not burst.hide_render:  # снаряд гаснет на месте (без взрыва)
                    burst.matrix_world = Matrix.Translation(V(pr[1]) * U) @ Matrix.Scale(0.3 + 1.0 * age, 4)
                    set_mat(self.m["burst"][i], strength=2.0 * (1 - age / 0.2), alpha=0.5 * (1 - age / 0.2), col=PURPLE)
            else:
                burst.hide_render = True
        # вспышка выстрела
        age = t - fire
        self.flash.hide_render = not (0 <= age < 0.16) or bool(canceled and frame["canceled"] == "до выстрела")
        if not self.flash.hide_render:
            self.flash.matrix_world = Matrix.Translation(L) @ Matrix.Scale(0.4 + 6.0 * age, 4)
            set_mat(self.m["flash"], strength=10.0 * (1 - age / 0.16), alpha=0.9 * (1 - age / 0.16))
