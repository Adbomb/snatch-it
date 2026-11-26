"""Непентес-обжора (GreedyPitcher, Epic, №27 каталога docs/BOSS6_CATALOG.md) — хищный кувшинчик наелся до отвала:
ловчая чаша-пузо раздулась урной, крышечка поднята и не закрывается, из горлышка выскочил пузырь — икнул; бредёт
на четырёх усиках-корнях, а листьями-ручками поглаживает пузо.
Признаки вида: пузатая ловчая чаша (одна урна: узкое горло → раздутое пузо → суженное круглое дно); гладкая губа-
перистом у входа (жёлтое кольцо, наклонено вперёд-вверх, по нему широкие косые рёбра); крышечка над входом на петле
сзади; крапчатая окраска (жёлтые крапины и тёмные капли запечены в цвет, гуще на пузе); усик-лиана из-под дна,
поднятая сбоку выше плеча и закрученная пружинкой (на ней кувшин держится в природе).
Эмоция — сытое довольство: глаза прикрыты тяжёлыми веками (без бровей), мягкая улыбка, румянец, пузырь-«ик».
Цвета: низ пуза бордовый (7A1035) → верх малиновый (D8245A), пузо спереди светлее (мягкий блик в цвете), перистом
жёлтый, крышечка фиолетовая (изнанка сиреневая с железками), корни тёмно-охристые; зелёное — только усик и листья;
пузырь светло-голубой с бликом.
Цвет кувшина — процедурный (градиент, блик, крапины) в материалах ключей pitch / pitchH: запекается в карту цвета
так же, как кольца D39; координаты модели восстановлены и в быстром просмотре (части от точек вращения),
и при запекании (части разнесены по x).
Зависит от jungle_kit.py (creature_kit, anatomy_kit, v4_kit, art_style).
"""

import math
import os
import sys

from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jungle_kit import *  # noqa: E402,F401,F403
import creature_kit as CK  # noqa: E402

RIM_N = 16  # граней кольца-перистома
RIBS = 11  # широких косых рёбер на губе
# профиль урны (доля наибольшего радиуса) по ярусам снизу вверх: суженное круглое дно → пузо → горло;
# соседние ярусы отличаются не больше чем на 0.12 стада
URN = (0.79, 0.88, 0.96, 1.0, 0.955, 0.87, 0.77, 0.67, 0.57, 0.48)
CUP = (0.6, 0.66, 0.72)  # верхняя чашечка (голова): от горла чуть расширяется к перистому, радиус в стадах


# ── процедурная окраска кувшина: запекается в карту цвета ─────────────────────────────────────────────────────


def _mix(nt, fac, c1, c2):
    m = nt.nodes.new("ShaderNodeMixRGB")
    m.blend_type = "MIX"
    for sock, v in ((m.inputs["Fac"], fac), (m.inputs["Color1"], c1), (m.inputs["Color2"], c2)):
        if isinstance(v, str):
            sock.default_value = (*S.lin(v), 1)
        elif isinstance(v, (int, float)):
            sock.default_value = v
        else:
            nt.links.new(v, sock)
    return m.outputs["Color"]


def _smooth(nt, x, lo, hi, out_lo=0.0, out_hi=1.0):
    r = nt.nodes.new("ShaderNodeMapRange")
    r.interpolation_type = "SMOOTHSTEP"
    nt.links.new(x, r.inputs["Value"])
    r.inputs["From Min"].default_value, r.inputs["From Max"].default_value = lo, hi
    r.inputs["To Min"].default_value, r.inputs["To Max"].default_value = out_lo, out_hi
    return r.outputs["Result"]


def _dots(nt, p, scale, rmin, rmax, dens, shift=(0.0, 0.0, 0.0)):
    """Маска крапин: ячейки Вороного (3D, по координатам модели p); крапина — круг радиуса rmin…rmax (стада) вокруг
    точки ячейки, только у доли ячеек dens (число или сокет): размер и место у каждой свои."""
    vm = nt.nodes.new("ShaderNodeVectorMath")
    vm.operation = "ADD"
    nt.links.new(p, vm.inputs[0])
    vm.inputs[1].default_value = shift
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.voronoi_dimensions, vo.feature, vo.distance = "3D", "F1", "EUCLIDEAN"
    vo.inputs["Scale"].default_value = scale
    vo.inputs["Randomness"].default_value = 1.0
    nt.links.new(vm.outputs["Vector"], vo.inputs["Vector"])
    sc = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(vo.outputs["Color"], sc.inputs["Color"])
    thr = S._math(nt, "MULTIPLY", S._math(nt, "ADD", rmin, S._math(nt, "MULTIPLY", sc.outputs["Red"], rmax - rmin)),
                  scale)  # расстояние Вороного — в единицах ячейки
    inside = S._math(nt, "LESS_THAN", vo.outputs["Distance"], thr)
    return S._math(nt, "MULTIPLY", inside, S._math(nt, "LESS_THAN", sc.outputs["Green"], dens))


def _skin(a, key, group, z_lo, z_hi, belly=None, zd=None):
    """Окраска ключа key (часть group): градиент бордовый → малиновый по высоте модели z_lo…z_hi, мягкий блик
    на пузе спереди (belly = точка перед пузом), жёлтые крапины (гуще на пузе: zd = (z пуза, z горла)) и тёмно-
    бордовые капли. Цвет идёт в кольца D39 (RingShade) — значит, и в запекание."""
    mat = a.materials[list(a.colors).index(key)]
    nt = mat.node_tree
    if CK.QUICK:  # быстрый просмотр: координаты части — от её точки вращения
        off = V(a.rig[group][1])
    else:  # запекание: части разнесены по x (creature_kit.explode)
        order = list(dict.fromkeys(a.face_groups)).index(group)
        off = V((-order * 10 * S.RING["step"], 0.0, 0.0))
    vm = nt.nodes.new("ShaderNodeVectorMath")
    vm.operation = "ADD"
    nt.links.new(nt.nodes.new("ShaderNodeTexCoord").outputs["Object"], vm.inputs[0])
    vm.inputs[1].default_value = tuple(off)
    p = vm.outputs["Vector"]
    xyz = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(p, xyz.inputs["Vector"])
    pz = xyz.outputs["Z"]
    col = _mix(nt, _smooth(nt, pz, z_lo, z_hi), "7A1035", "D8245A")  # низ бордовый, верх малиновый
    if belly is not None:  # налитое пузо: светлее к середине спереди, без контура
        d = nt.nodes.new("ShaderNodeVectorMath")
        d.operation = "SUBTRACT"
        nt.links.new(p, d.inputs[0])
        d.inputs[1].default_value = tuple(belly)
        sc = nt.nodes.new("ShaderNodeVectorMath")
        sc.operation = "MULTIPLY"
        nt.links.new(d.outputs["Vector"], sc.inputs[0])
        sc.inputs[1].default_value = (0.85, 1.0, 0.7)
        ln = nt.nodes.new("ShaderNodeVectorMath")
        ln.operation = "LENGTH"
        nt.links.new(sc.outputs["Vector"], ln.inputs[0])
        col = _mix(nt, _smooth(nt, ln.outputs["Value"], 0.35, 1.05, 0.55, 0.0), col, "F2638F")
    dens = _smooth(nt, pz, zd[0], zd[1], 0.5, 0.14) if zd else 0.18  # крапин больше на пузе, к горлу реже
    col = _mix(nt, _dots(nt, p, 3.1, 0.035, 0.07, 0.3, (3.7, 1.9, 0.6)), col, "4E0820")  # тёмно-бордовые капли
    col = _mix(nt, _dots(nt, p, 4.2, 0.04, 0.1, dens), col, "FFD23A")  # жёлтые крапины 0.08–0.2
    shade = nt.nodes.get("RingShade")
    if shade is not None:
        nt.links.new(col, shade.inputs["Color1"])
    else:
        b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        nt.links.new(col, b.inputs["Base Color"])
        nt.links.new(col, b.inputs["Emission Color"])


# ── формы ───────────────────────────────────────────────────────────────────────────────────────────────────────


def _surf(tiers, ang, z, off=0.0):
    """Точка на поверхности ярусов A.body по направлению ang (градусы, в плоскости xy) на высоте z, вынесенная
    наружу на off (лист-ручка лежит на пузе, а не тонет в нём)."""
    tr = min(tiers, key=lambda q: abs((q[0] + q[1]) / 2 - z))
    za, zb, bx, by, wx, wy, cut = tr
    d = V((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
    lim = [(wx + wy - cut) / (abs(d.x) + abs(d.y))]
    if abs(d.x) > 1e-6:
        lim.append(wx / abs(d.x))
    if abs(d.y) > 1e-6:
        lim.append(wy / abs(d.y))
    s = min(lim) + off
    return V((bx + d.x * s, by + d.y * s, z))


def _ellipse(rx, ry, n=RIM_N, k=1.0):
    return [(k * rx * math.cos(2 * math.pi * (i + 0.5) / n), k * ry * math.sin(2 * math.pi * (i + 0.5) / n))
            for i in range(n)]


def _leg(a, nm, sx, sy, zb, t, toes):
    """Нога-корень: усик выходит из-под дна вбок, изгибается коленцем (без шара-сустава) и уходит в землю;
    внизу — 2–3 тупых корешка, расходящихся по земле (толщина ≥ 0.12, длина 0.3–0.4)."""
    hip = V((sx * 0.42, sy * 0.36, zb + 0.16))
    bend = V((sx * 0.8, sy * 0.66, zb - 0.06))  # коленце: корень выгнут наружу дугой
    foot = V((sx * 0.86, sy * 0.74, t + 0.13))
    part(a, nm, "Body", tuple(hip))
    kchain(a, "root", [tuple(hip), tuple(bend), tuple(foot)], [0.25, 0.21, 0.19], up=(0, 0, 1), overlap=0.6)
    out = V((sx * 0.86, sy * 0.74, 0)).normalized()
    angs = (-0.75, 0.05, 0.8) if toes == 3 else (-0.5, 0.55)
    for i, ang in enumerate(angs):  # корешки: тупые клинья по земле, веером наружу
        d = Matrix.Rotation(ang, 3, "Z") @ out
        ln = (0.4, 0.34, 0.3)[i % 3]
        tip = foot + d * ln
        z0 = t + 0.075 + 0.006 * i  # у корешков разная высота — нижние грани не совпадают
        blunt(a, "rootD", (foot.x - d.x * 0.05, foot.y - d.y * 0.05, z0 + 0.03), (tip.x, tip.y, z0), 0.17, 0.12)


def _ball(a, key, c, r, n, bevel=0):
    """Пузырь: шар D39 из правильных восьмиугольных ярусов."""
    A.body(a, key, (c.x, c.y, c.z - r), r, r, 2 * r, "ball", n=n, floor=0.35, corner=0.58, bevel=bevel)


def greedy_pitcher():
    a = new("GreedyPitcher", {"pitch": ("D8245A", True), "pitchH": ("D8245A", True), "pitchL": ("F06A95", False),
                              "peri": ("FFCB2E", True), "periD": ("F59A1E", False), "maw": ("3E0B26", False),
                              "lid": ("8A43E0", True), "lidL": ("C9A2FF", False), "lidD": ("5C2AA6", False),
                              "bubble": ("BFEAFF", False), "root": ("8E6526", True), "rootD": ("6E4A1C", False),
                              "leaf": ("7CCB3A", True), "leafV": ("4E8F2E", False), "vine": ("9BD94A", True)})
    t = epic_stand(a, 1.7)
    zb = t + 0.5  # низ урны: под ним ноги-корни
    hb = 1.6  # высота пуза до горла
    zn = zb + hb  # горло
    zr = zn + 0.85  # губа-перистом

    # ── пузо: одна урна — суженное круглое дно, раздутое пузо, сужение к горлу (ступени только по профилю) ──
    part(a, "Body", "Stand", (0, 0.0, zb + 0.8))
    tb = A.body(a, "pitch", (0, 0.0, zb), 1.2, 1.08, hb, lambda u: URN[min(int(u * len(URN)), len(URN) - 1)],
                n=len(URN), floor=0.3)
    for s, nm, toes in ((1, "LegFL", 3), (-1, "LegFR", 3), (1, "LegBL", 2), (-1, "LegBR", 2)):
        _leg(a, nm, s, -1 if "F" in nm else 1, zb, t, toes)

    # ── листья-ручки (зелёный акцент): черешок от горла, лист лежит на пузе и гладит его ──
    for s, nm, angs, zs in ((1, "ArmL", (-30, -48, -62), (1.22, 0.92, 0.62)),
                            (-1, "ArmR", (210, 226, 238), (1.2, 0.9, 0.6))):
        sh = V((s * 0.52, -0.08, zn - 0.08))
        part(a, nm, "Body", tuple(sh))
        pts = [sh] + [_surf(tb, ang, zb + z, 0.05) for ang, z in zip(angs, zs)]
        nrm = (pts[2] - V((0, 0, pts[2].z))).normalized()
        leaf_blade(a, "leaf", "leafV", pts, [0.12, 0.3, 0.46, 0.14], 0.08, up=tuple(nrm))

    # ── усик-лиана: из-под дна назад-вбок, поднимается сбоку за плечом, наверху — пружинка на уровне губы ──
    p0 = V((-0.25, 0.42, zb + 0.1))
    part(a, "Tail", "Body", tuple(p0))
    tp = [p0, V((-0.35, 1.02, zb - 0.02)), V((-0.92, 1.2, zb + 0.22)), V((-1.36, 0.92, zb + 0.78)),
          V((-1.56, 0.62, zb + 1.4)), V((-1.56, 0.42, zr - 0.3))]
    cc = V((-1.32, 0.38, zr + 0.06))  # центр пружинки (в плоскости xz — видна спереди и в 3/4)
    for k, (ang, r) in enumerate(((180, 0.24), (120, 0.23), (55, 0.21), (0, 0.18), (-60, 0.15), (-125, 0.12))):
        q = math.radians(ang)
        tp.append(cc + V((r * math.cos(q), -0.02 * k, r * math.sin(q))))
    ws = [0.18, 0.17, 0.16, 0.15, 0.145, 0.14, 0.135, 0.13, 0.125, 0.12, 0.11, 0.1]
    kchain(a, "vine", [tuple(q) for q in tp], ws, up=(0, 1, 0), overlap=0.4)

    # ── голова: верхняя чашечка кувшина (от горла чуть расширяется к губе), лицо спереди ──
    part(a, "Head", "Body", (0, 0.0, zn + 0.05))
    th = A.body(a, "pitchH", (0, 0.0, zn - 0.03), 1.0, 0.92, zr - zn + 0.03,
                lambda u: CUP[min(int(u * len(CUP)), len(CUP) - 1)], n=len(CUP), floor=0.3)
    # лицо: глаза прикрыты тяжёлыми веками (бровей нет — веки и есть «сытое» выражение), улыбка, румянец
    ez = zr - 0.5
    for s in S2:
        ex = s * 0.22
        ec = (ex, front_y(th, ex, ez) + 0.02, ez)
        eye2(a, ec, 0.15, (s * 0.2, -1, 0.05), "sleepy", s, "pitchL", "dark", lid=0.55, lid_tilt=-6,
             look=(s * 0.15, -0.7), show_brow=False)
        bx_ = ex + s * 0.12
        bz = zr - 0.67
        by_ = front_y(th, bx_, bz)
        a.box("blush", bx_ - 0.08, bx_ + 0.08, by_ - 0.025, by_ + 0.06, bz - 0.03, bz + 0.03, bevel=0)
    mz = zr - 0.71
    grin(a, (0.0, front_y(th, 0.0, mz) + 0.005, mz), 0.26, h=0.055, key="dark")

    # ── перистом: гладкое жёлтое кольцо-губа, наклонено вперёд-вверх (сзади выше), широкие косые рёбра лёжа ──
    rm = Matrix.Translation((0, 0.04, zr + 0.03)) @ Matrix.Rotation(math.radians(12), 4, "X")
    RX, RY = 0.86, 0.8
    a.frame("peri", _ellipse(RX, RY), 0.22, -0.13, 0.1, axis="z", bevel=0, matrix=rm)
    a.prism("maw", _ellipse(RX, RY, k=0.76), -0.2, 0.03, axis="z", bevel=0, matrix=rm)  # тёмное нутро
    for i in range(RIBS):  # рёбра: широкие пластины поверх губы, наискось (как витой валик), выступ 0.025
        q = 2 * math.pi * (i + 0.25) / RIBS
        d = V((math.cos(q), math.sin(q), 0))
        ro = 1.0 / math.sqrt((d.x / RX) ** 2 + (d.y / RY) ** 2) - 0.11
        mr = rm @ Matrix.Rotation(q, 4, "Z") @ Matrix.Translation((ro, 0, 0)) @ Matrix.Rotation(math.radians(28), 4, "Z")
        e = 0.004 * (i % 2)
        a.box("periD", -0.11, 0.11, -0.08, 0.08, 0.07 + e, 0.125 + e, bevel=0, matrix=mr)

    # ── крышечка: на петле сзади, поднята и не закрывается; изнанка (к игроку) сиреневая с железками ──
    hinge = rm @ V((0, RY - 0.1, 0.06))
    part(a, "Lid", "Head", tuple(hinge))
    lm = rm @ Matrix.Translation((0, RY - 0.1, 0.06)) @ Matrix.Rotation(math.radians(-122), 4, "X")
    lp = [(-0.18, 0.08), (0.18, 0.08), (0.5, -0.15), (0.62, -0.44), (0.48, -0.74), (0.16, -0.96), (0.0, -1.03),
          (-0.16, -0.96), (-0.48, -0.74), (-0.62, -0.44), (-0.5, -0.15)]
    a.prism("lid", lp, -0.05, 0.06, axis="z", matrix=lm)
    a.prism("lidL", [(x * 0.78, y * 0.78 - 0.08) for x, y in lp], -0.08, -0.02, axis="z", bevel=0, matrix=lm)
    for gx, gy in ((-0.26, -0.3), (0.04, -0.5), (0.28, -0.72)):  # медовые железки изнанки вразброс
        a.box("lidD", gx - 0.06, gx + 0.06, gy - 0.06, gy + 0.06, -0.1 - 0.004 * (gy < -0.45), -0.06, bevel=0, matrix=lm)
    a.box("lid", -0.15, 0.15, -0.08, 0.1, -0.1, 0.1, bevel=0, matrix=lm)  # петля

    # ── пузырь-«ик»: вылетел из горлышка вбок (+x) — висит на фоне неба, крышку не закрывает; цепочка из трёх ──
    q = math.radians(-28)
    lip = rm @ V((RX * 0.9 * math.cos(q), RY * 0.9 * math.sin(q), 0.1))  # край губы спереди справа
    c1 = lip + V((0.05, -0.02, 0.05))
    c3 = lip + V((0.5, -0.04, 0.42))
    r1, r3 = 0.09, 0.26
    dv = (c3 - c1).normalized()
    r2 = 0.14
    c2 = c1 + dv * (r1 + r2 - 0.03)
    c3 = c2 + dv * (r2 + r3 - 0.03)
    part(a, "Bubble", "Head", tuple(c1))
    _ball(a, "bubble", c1, r1, 2)
    _ball(a, "bubble", c2, r2, 3)
    _ball(a, "bubble", c3, r3, 4)
    a.box("white", c3.x - 0.15, c3.x - 0.05, c3.y - r3 - 0.02, c3.y - r3 + 0.06, c3.z + 0.04, c3.z + 0.14,
          bevel=0)  # блик

    # процедурная окраска кувшина — после сборки материалов
    build0 = a.build

    def build(collection):
        obj = build0(collection)
        _skin(a, "pitch", "Body", zb + 0.1, zb + 1.1, belly=(0.0, -1.55, zb + 0.75), zd=(zb + 0.7, zn + 0.1))
        _skin(a, "pitchH", "Head", zb + 0.1, zb + 1.1, zd=(zb + 0.7, zn + 0.1))
        return obj

    a.build = build

    face_point(a, (0.0, front_y(th, 0.0, ez), ez - 0.05))
    closeup(a, (0.0, -0.2, zb + 0.8), eye_off=(-1.3, -2.2, 0.9))
    a.pose = {"Lid": ((-14, 0, 6), (0, 0, 0)), "Head": ((0, 6, -8), (0, 0, 0)), "LegFL": ((-20, 0, 0), (0, 0, 0.05)),
              "LegBR": ((12, 0, 0), (0, 0, 0)), "ArmR": ((0, 0, -12), (0, 0, 0)), "ArmL": ((0, 0, 8), (0, 0, 0)),
              "Tail": ((0, 0, 14), (0, 0, 0)), "Bubble": ((0, 0, 0), (0.04, 0, 0.14))}
    return a


ITEM = ("GreedyPitcher", greedy_pitcher, "Непентес-обжора", "Epic")
