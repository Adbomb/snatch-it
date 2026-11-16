"""Этап C.2: настоящие стеклянные стенки у предметов, которые по дизайну стеклянные (банка, шлем, бутылка, колпак).

По D42 стекло предметов было «без прозрачности»: у предмета одна меш и одна SurfaceAppearance, поэтому стекло нарисовано
голубыми рёбрами и кольцами (art_flea.glass_cage), стенок нет. Здесь к тем же рёбрам добавляются стенки — отдельные
тонкие детали Glass с прозрачностью (их строит ItemFactory по Config/ItemGlass). Меш, карты и форма предмета не
меняются: рёбра остаются светлыми гранями стекла, стенки встают между ними (концы уходят в рёбра и кольца).

Скрипт запускает настоящие построители art_flea в режиме проверки (без запекания), берёт габарит меша (центр меша
в игре — центр габарита) и детали «glass» — по ним сверяет числа стенок, затем пишет src/shared/Config/ItemGlass.luau:
стенки в осях меша в игре (у мешей предметов: −x, z, y Blender — лицо −Z; стады = единицы Blender).

  blender --background --factory-startup --python scripts/blender/glass_panes.py -- <репо> <папка>
"""

import math
import os
import runpy
import sys

argv = sys.argv[sys.argv.index("--") + 1:]
REPO, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
sys.path.insert(0, os.path.join(REPO, "scripts", "blender"))
import art_style as S  # noqa: E402

THICK = 0.04  # толщина стенки, стадов
INSET = 0.012  # стенка чуть внутрь от линии осей рёбер: рёбра выступают наружу светлой гранью

# Стеклянные части по построителям art_flea (числа — те же, что в вызовах glass_cage / рёбрах бутылки).
CAGES = {
    # предмет: (cx, cy, r, z0, z1, n, ring, phase) — glass_cage(a, "glass", cx, cy, r, z0, z1, n, post, ring, phase)
    "UfoJar": (0.0, 0.0, 0.88, 0.24, 2.6, 8, 0.1, None),
    "AstroCat": (0.0, -0.1, 0.84, 1.5, 2.62, 6, 0.08, 0.0),
    "PrizeMachine": (0.0, 0.0, 0.72, 1.74, 3.18, 8, 0.1, None),
}
BOTTLE = {"zc": 1.05, "r": 0.72, "x0": -1.18, "x1": 0.94, "neck_r": 0.3, "neck_x0": 1.06, "neck_x1": 1.5}

bounds, glass_pts = {}, {}
_build = S.Art.build


def build(self, collection):
    pts = []
    for bm, key, _, _ in self.parts:
        if key == "glass":
            pts += [tuple(v.co) for v in bm.verts]
    obj = _build(self, collection)
    lo, hi = S.bounds(obj)
    bounds[self.name] = (tuple(lo), tuple(hi))
    glass_pts[self.name] = pts
    return obj


S.Art.build = build
sys.argv = [sys.argv[0], "--", REPO, OUT, "check", "UfoJar", "AstroCat", "PrizeMachine", "WorldInBottle"]
try:
    runpy.run_path(os.path.join(REPO, "scripts", "blender", "art_flea.py"), run_name="__main__")
except SystemExit:
    pass


def ngon(cx, cy, r, n, phase):
    phase = math.pi / n if phase is None else phase
    return [(cx + r * math.cos(phase + 2 * math.pi * i / n), cy + r * math.sin(phase + 2 * math.pi * i / n))
            for i in range(n)]


def to_rbx(p, center):
    """Точка Blender → оси меша предмета в игре (центр — центр габарита). Меши предметов (импорт FBX в Studio)
    повёрнуты на 180° вокруг вертикали относительно осей дракона (Open Cloud): лицо −Z, оси (−x, z, y); проверено
    на снимке сверху (шлем кота смещён от центра — сдвиг виден, у симметричной банки — нет)."""
    x, y, z = p
    return (-x - center[0], z - center[1], y - center[2])


def sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def norm(a):
    length = math.sqrt(sum(c * c for c in a))
    return tuple(c / length for c in a), length


def quad_pane(p00, p10, p01, center):
    """Стенка-прямоугольник по углам (Blender): p00 → p10 — ширина, p00 → p01 — высота. Возвращает центр, оси, размер
    в осях меша в игре."""
    a, b, c = (to_rbx(p, center) for p in (p00, p10, p01))
    right, w = norm(sub(b, a))
    up, h = norm(sub(c, a))
    mid = tuple(a[i] + (b[i] - a[i]) / 2 + (c[i] - a[i]) / 2 for i in range(3))
    return {"center": mid, "right": right, "up": up, "size": (w, h, THICK)}


def cage_panes(spec, center):
    cx, cy, r, z0, z1, n, ring, phase = spec
    pts = ngon(cx, cy, r - INSET, n, phase)
    out = []
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % n]
        out.append(quad_pane((xa, ya, z0 + ring * 0.5), (xb, yb, z0 + ring * 0.5), (xa, ya, z1 - ring * 0.5), center))
    return out


def bottle_panes(center):
    b = BOTTLE
    out = []
    # тело вдоль x: восьмиугольник (z, y) радиуса r, стенки между кольцами
    body = ngon(b["zc"], 0, b["r"] - INSET, 8, None)
    for i in range(8):
        (za, ya), (zb, yb) = body[i], body[(i + 1) % 8]
        out.append(quad_pane((b["x0"], ya, za), (b["x0"], yb, zb), (b["x1"], ya, za), center))
    # горлышко
    neck = ngon(b["zc"], 0, b["neck_r"] - INSET, 8, None)
    for i in range(8):
        (za, ya), (zb, yb) = neck[i], neck[(i + 1) % 8]
        out.append(quad_pane((b["neck_x0"], ya, za), (b["neck_x0"], yb, zb), (b["neck_x1"], ya, za), center))
    # плечо: кольцо между телом и горлышком в плоскости x = 1.0 (трапеции → прямоугольник по средней ширине)
    for i in range(8):
        (za, ya), (zb, yb) = body[i], body[(i + 1) % 8]
        (zc_, yc), (zd, yd) = neck[i], neck[(i + 1) % 8]
        m_out = ((za + zb) / 2, (ya + yb) / 2)
        m_in = ((zc_ + zd) / 2, (yc + yd) / 2)
        half = ((math.dist((za, ya), (zb, yb)) + math.dist((zc_, yc), (zd, yd))) / 4)
        dz, dy = (zb - za), (yb - ya)
        length = math.hypot(dz, dy)
        tz, ty = dz / length * half, dy / length * half
        x = 1.0
        out.append(quad_pane((x, m_in[1] - ty, m_in[0] - tz), (x, m_in[1] + ty, m_in[0] + tz),
                             (x, m_out[1] - ty, m_out[0] - tz), center))
    return out


lines = ["-- Создано scripts/blender/glass_panes.py (этап C.2) — не править руками.",
         "-- Стеклянные стенки предметов, которые по дизайну стеклянные: банка, шлем, бутылка, колпак автомата.",
         "-- Стенка — тонкая деталь Glass между светлыми рёбрами меша (рёбра, кольца, блики остаются в меше и картах D39):",
         "-- center, right, up — в осях меша «Visual» (центр габарита меша), size — ширина × высота × толщина, стады.",
         "-- Строит ItemFactory; цвет и прозрачность — ItemGlass.Style. Ни от чего не зависит.",
         "",
         "local V = Vector3.new",
         "",
         "local ItemGlass = {}",
         "",
         "-- Вид стекла (подобран по снимкам Studio, этап C.2): SmoothPlastic, а не Glass — материал Glass в Roblox",
         "-- искажает то, что за ним (содержимое банки «рассыпается»); прозрачность — силуэт читается и на светлом фоне.",
         "ItemGlass.Style = { Material = \"SmoothPlastic\", Color = \"DDF7FF\", Transparency = 0.7, Reflectance = 0.15 }",
         "",
         "ItemGlass.Items = {"]
report = []
for item, spec in list(CAGES.items()) + [("WorldInBottle", None)]:
    name = "Art_" + item
    if name not in bounds:
        raise SystemExit(f"нет габарита {name}")
    lo, hi = bounds[name]
    c_b = tuple((lo[i] + hi[i]) / 2 for i in range(3))
    center = (-c_b[0], c_b[2], c_b[1])  # центр габарита в осях меша предмета
    size_r = (hi[0] - lo[0], hi[2] - lo[2], hi[1] - lo[1])
    panes = cage_panes(spec, center) if spec else bottle_panes(center)
    gp = glass_pts[name]
    report.append(f"{item}: габарит {tuple(round(v, 3) for v in size_r)}, стенок {len(panes)}, "
                  f"вершин стекла в построителе {len(gp)}")
    lines.append(f"\t{item} = {{ -- габарит меша {size_r[0]:.3f} × {size_r[1]:.3f} × {size_r[2]:.3f}")
    for p in panes:
        lines.append("\t\t{ center = V(%.4f, %.4f, %.4f), right = V(%.4f, %.4f, %.4f), up = V(%.4f, %.4f, %.4f), "
                     "size = V(%.4f, %.4f, %.4f) }," % (*p["center"], *p["right"], *p["up"], *p["size"]))
    lines.append("\t},")
lines += ["}", "", "return ItemGlass", ""]
path = os.path.join(REPO, "src", "shared", "Config", "ItemGlass.luau")
with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines))
for r in report:
    print("GLASS", r, flush=True)
print("GLASS_OK", path, flush=True)
