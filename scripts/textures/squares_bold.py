"""Плитка «крупные вдавленные квадраты» для этажей музея-небоскрёба (референс владельца 2026-11-19 — забор из
брусков): на каждый стад — один вдавленный квадрат со скруглёнными углами и мягкой фаской; дно квадратов через один
чуть светлее и чуть темнее (шахматка в один стад); свет сверху-слева: верхняя и левая стенки ямки в мягкой тени,
нижняя и правая — светлая кромка; у дна вдоль стенок — лёгкая тень (глубина); едва заметное зерно пластика.
Цвет плитки светлый — цвет даёт деталь.

Версия 3 (2026-11-20, «чтобы глазу было приятно»; v1 — первая, v2 — слишком бледная): контраст ниже — шахматка
дна 0.99 / 0.86 вместо 0.96 / 0.75, тень фаски мягче (0.34 вместо 0.42) и только на верхней и левой стенке, на нижней
и правой — светлая кромка, у дна вдоль стенок — лёгкая тень, квадрат крупнее (меньше пёстрого фона между квадратами),
рельеф карты нормалей ниже — издалека стена не рябит, вблизи квадраты читаются объёмом, а не тёмными дырками.

Версия 4 (2026-11-20, «все 5 пунктов»): три плитки с одним рисунком и сеткой —
  lego_squares_bold (золото зала, LegoSquaresBold): квадраты чередуются оттенком (желтее / теплее), а не яркостью;
  lego_squares_quiet (бархат, ковёр, потолок, LegoSquaresQuiet): квадраты едва заметны — ткань не рябит, глаз
    отдыхает, золото и трон становятся акцентом;
  lego_squares_far (фасад, LegoSquaresFar): рисунок золота зала, но мягче и чуть размыт — фасад видят издалека.

Плитка 2 × 2 стада (StudsPerTile = 2), 512 px (256 px на стад); считаем в SS раз крупнее и усредняем.
Квадраты стоят по центрам клеток в один стад: блоки этажа выровнены по той же сетке, поэтому квадраты не режутся
краями (MaterialVariant LegoSquaresBold, Config/Textures.SquaresBold).
Пишет assets/textures/lego_squares_bold_color.png и lego_squares_bold_normal.png.
Запуск: python scripts/textures/squares_bold.py [--preview <папка>] — превью: плитка в цветах этажа вблизи и издалека.
"""

import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PX, SS, STUDS = 512, 2, 2

# half, radius, slope — полуширина квадрата, скругление и ширина фаски (доли стада);
# surface, light, dark — тон поверхности, светлого и тёмного дна; shadow — тень верхней и левой стенки,
# rim — светлая кромка нижней и правой; inner — тень у дна вдоль стенок; depth — рельеф карты нормалей
STYLE = {
    "v1": dict(half=0.29, radius=0.085, slope=0.09, surface=0.88, light=0.96, dark=0.75, shadow=0.42, rim=0.0,
               inner=0.0, depth=0.07, grain=0.012, legacy=True),
    "v2": dict(half=0.31, radius=0.10, slope=0.11, surface=0.93, light=0.99, dark=0.90, shadow=0.26, rim=0.10,
               inner=0.07, depth=0.045, grain=0.006, legacy=False),
    "v3": dict(half=0.31, radius=0.10, slope=0.10, surface=0.92, light=0.99, dark=0.86, shadow=0.34, rim=0.14,
               inner=0.08, depth=0.055, grain=0.006, legacy=False),
    # v4 — золото зала: квадраты чередуются оттенком, а не яркостью — светлые чуть желтее, тёмные чуть теплее
    "v4": dict(half=0.31, radius=0.10, slope=0.10, surface=0.92, light=0.99, dark=0.93, shadow=0.32, rim=0.14,
               inner=0.08, depth=0.055, grain=0.006, legacy=False,
               light_tint=(1.0, 1.0, 0.88), dark_tint=(1.0, 0.90, 0.78)),
    # тихая — бархат, ковёр, потолок: квадраты едва заметны, оттенки алый / малиновый (на пурпуре — синее / краснее)
    "quiet": dict(half=0.31, radius=0.10, slope=0.12, surface=0.95, light=0.98, dark=0.96, shadow=0.12, rim=0.05,
                  inner=0.03, depth=0.02, grain=0.004, legacy=False,
                  light_tint=(1.0, 0.97, 0.94), dark_tint=(0.96, 0.92, 1.0)),
    # фасад: тот же рисунок, что у золота зала, но мягче — фасад видят издалека, мелкий рисунок там рябит
    "far": dict(half=0.31, radius=0.10, slope=0.12, surface=0.93, light=0.99, dark=0.95, shadow=0.20, rim=0.08,
                inner=0.05, depth=0.035, grain=0.004, legacy=False, blur=2,
                light_tint=(1.0, 1.0, 0.92), dark_tint=(1.0, 0.93, 0.84)),
}
USE = "v3"
OUTPUTS = {"v4": "lego_squares_bold", "quiet": "lego_squares_quiet", "far": "lego_squares_far"}


def tile(s):
    n = PX * SS
    c = (np.arange(n) + 0.5) / n * STUDS
    x, y = np.meshgrid(c, c)  # y растёт вниз по картинке
    u, v = x % 1.0 - 0.5, y % 1.0 - 0.5
    qx, qy = np.abs(u) - (s["half"] - s["radius"]), np.abs(v) - (s["half"] - s["radius"])
    sd = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - s["radius"]
    t = np.clip(-sd / s["slope"], 0, 1)
    t = t * t * (3 - 2 * t)  # 0 на поверхности → 1 на дне
    height = -t * s["depth"]
    step = STUDS / n
    gy, gx = np.gradient(height, step)  # уклон по картинке: вниз и вправо
    checker = (np.floor(x) + np.floor(y)) % 2
    floor = np.where(checker == 0, s["light"], s["dark"])
    tone = s["surface"] + (floor - s["surface"]) * t
    wall = 4 * t * (1 - t)  # 1 посередине фаски
    if s["legacy"]:
        lit = np.clip(-(gx + gy) * 0.75, -1, 1)
        tone = tone * (1 - s["shadow"] * wall * (0.25 + 0.75 * lit))
    else:
        # направление стенки: к свету (сверху-слева) или от него; величина не зависит от глубины
        g = np.hypot(gx, gy) + 1e-9
        lit = np.clip(-(gx + gy) / (g * 1.4142), -1, 1)  # +1 — верхняя и левая стенки (в тени), −1 — нижняя и правая
        tone = tone * (1 - s["shadow"] * wall * np.maximum(lit, 0)) + s["rim"] * wall * np.maximum(-lit, 0)
        # тень у дна вдоль стенок: дно темнее у края и светлее к центру
        rim_dist = np.clip(-sd - s["slope"], 0, None)
        tone = tone * (1 - s["inner"] * t * np.exp(-rim_dist / 0.05))
    rng = np.random.default_rng(39)
    grain = rng.normal(0.0, 1.0, (n, n))
    for axis in (0, 1):  # лёгкое размытие зерна, плитка без шва
        grain = (grain + np.roll(grain, 1, axis) + np.roll(grain, -1, axis)) / 3
    tone = np.clip(tone * (1 + s["grain"] * grain), 0, 1)

    def down(a):
        return a.reshape(PX, SS, PX, SS, -1).mean(axis=(1, 3))

    rgb = np.repeat(tone[..., None], 3, axis=2)
    if "light_tint" in s:  # оттенок дна квадрата: светлые и тёмные через один
        tint = np.where(checker[..., None] == 0, np.array(s["light_tint"]), np.array(s["dark_tint"]))
        rgb = rgb * (1 + (tint - 1) * t[..., None])
    for _ in range(s.get("blur", 0)):  # мягче для дальнего вида: меньше мелкой ряби на уменьшенных копиях
        rgb = (rgb + np.roll(rgb, 1, 0) + np.roll(rgb, -1, 0) + np.roll(rgb, 1, 1) + np.roll(rgb, -1, 1)) / 5
    color = down(rgb)
    normal = np.stack([-gx, gy, np.ones_like(height)], axis=-1)  # OpenGL: Y вверх, строки картинки идут вниз
    normal = down(normal)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    return color, normal


def to8(a):
    return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)


def preview(folder):
    """Плитка в цветах этажа: вблизи (8 × 4 стада) и издалека (40 × 20 стадов, уменьшено) — для каждой версии."""
    os.makedirs(folder, exist_ok=True)
    colors = {"gold": (242, 194, 48), "velvet": (198, 40, 40), "carpet": (107, 63, 184)}
    rows = []
    for name, s in STYLE.items():
        if name in ("v1", "v2"):
            continue
        color, _ = tile(s)
        row = []
        for code in colors.values():
            tint = np.array(code) / 255.0
            near = np.tile(color, (2, 4, 1)) * tint  # 4 × 8 стадов
            far = np.tile(color, (10, 20, 1)) * tint  # 20 × 40 стадов
            near_im = Image.fromarray(to8(near)).resize((512, 256), Image.LANCZOS)
            far_im = Image.fromarray(to8(far)).resize((512, 256), Image.LANCZOS)
            row += [near_im, far_im]
        rows.append((name, row))
    sheet = Image.new("RGB", (6 * 516 + 4, len(rows) * 260 + 4), (24, 24, 28))
    for r, (_, row) in enumerate(rows):
        for c, im in enumerate(row):
            sheet.paste(im, (4 + c * 516, 4 + r * 260))
    path = os.path.join(folder, "squares_bold_versions.png")
    sheet.save(path)
    print("PREVIEW", path, [name for name, _ in rows])


def main():
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
        return
    out = os.path.join(ROOT, "assets", "textures")
    for style, name in OUTPUTS.items():
        color, normal = tile(STYLE[style])
        Image.fromarray(to8(color)).save(os.path.join(out, name + "_color.png"))
        Image.fromarray(to8(normal * 0.5 + 0.5)).save(os.path.join(out, name + "_normal.png"))
        print("SQUARES_OK", style, name, PX)


main()
