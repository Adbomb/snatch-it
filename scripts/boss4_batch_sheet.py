"""Общий лист партии существ босса 4: ряд одной камерой (oasis_lineup.py), силуэты, лица крупно, контуры D39 крупно и
кадр телефона каждого — с подписями и числами из report_<id>.json. Только кадры настоящих моделей из Blender.
Запуск: python scripts/boss4_batch_sheet.py <папка ряда> <папка существ> "<заголовок>" <id>=<название> […]
Пишет <папка ряда>/batch_sheet.jpg.
"""

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
lineup_dir, creatures_dir, title = sys.argv[1], sys.argv[2], sys.argv[3]
items = [a.split("=", 1) for a in sys.argv[4:]]
BOLD = "C:/Windows/Fonts/arialbd.ttf"
F_T, F_L, F_S = ImageFont.truetype(BOLD, 44), ImageFont.truetype(BOLD, 26), ImageFont.truetype(BOLD, 21)
BG, GOLD, WHITE, GREY = (16, 18, 24), (255, 210, 63), (240, 242, 248), (170, 176, 190)
W, M = 2400, 16


def fit(im, w, h):
    k = min(w / im.width, h / im.height)
    small = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    cell = Image.new("RGB", (w, h), BG)
    cell.paste(small, ((w - small.width) // 2, (h - small.height) // 2))
    return cell


def label(d, xy, text, font=F_L, fill=WHITE):
    x, y = xy
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        d.text((x + dx, y + dy), text, font=font, fill=BG)
    d.text(xy, text, font=font, fill=fill)


def report(item):
    folder = os.path.join(creatures_dir, item)
    for name in os.listdir(folder):
        if name.startswith("report") and name.endswith(".json"):
            data = json.load(open(os.path.join(folder, name), encoding="utf-8"))
            if item in data:
                return data[item]
    return {}


page = Image.new("RGB", (W, 6000), BG)
d = ImageDraw.Draw(page)
d.text((M, 14), title, font=F_T, fill=GOLD)
d.text((M, 72), "Одна камера, свет и масштаб для всех; справа — эталон качества D39 (фенек №20 v2). Числа — игровой FBX.",
       font=F_S, fill=GREY)
y = 112
n = len(items)
color = Image.open(os.path.join(lineup_dir, "lineup_color.png")).convert("RGB")
cell = fit(color, W - 2 * M, round((W - 2 * M) * color.height / color.width))
page.paste(cell, (M, y))
cw = (W - 2 * M) / n
for k, (item, name) in enumerate(items):
    label(d, (M + round(k * cw) + 10, y + 8), name, F_S)
y += cell.height + M
sil = Image.open(os.path.join(lineup_dir, "lineup_silhouette.png")).convert("RGB")
cell = fit(sil, W - 2 * M, round((W - 2 * M) * sil.height / sil.width))
page.paste(cell, (M, y))
label(d, (M + 10, y + 8), "силуэты спереди, без подставок", F_S, GREY)
y += cell.height + M
# лица, контуры и кадр телефона — по столбцу на существо (без эталона)
own = [(i, nm) for i, nm in items if os.path.isdir(os.path.join(creatures_dir, i)) and not i.startswith("FennecRiddler")]
cw = (W - (len(own) + 1) * M) // len(own)
for row, (shot, h, text) in enumerate((("face", 380, "лицо"), ("texture", 330, "контуры D39 крупно"),
                                        ("ingame_phone", 300, "кадр телефона 844 × 390"))):
    for k, (item, name) in enumerate(own):
        im = Image.open(os.path.join(creatures_dir, item, f"{item}_{shot}.png")).convert("RGB")
        if shot == "ingame_phone":
            im = im.crop((390, 70, 630, 290))  # существо в кадре телефона, без лишнего манекена
        page.paste(fit(im, cw, h), (M + k * (cw + M), y))
        label(d, (M + k * (cw + M) + 8, y + 6), text if k == 0 else "", F_S, GREY)
    y += h + M
for k, (item, name) in enumerate(own):
    r = report(item)
    x = M + k * (cw + M)
    label(d, (x + 4, y), name, F_L, GOLD)
    stand = r.get("tris_by_part", {}).get("Stand", 0)
    tris = sum(r.get("tris_by_part", {}).values())
    lines = [f"{tris} треуг. (без подставки {tris - stand})", f"частей {r.get('meshes', '?')}, материалов 1",
             f"{r.get('texels_per_stud', 0):.0f} текс./стад, карты 1024²",
             "Ш × Г × В {:.2f} × {:.2f} × {:.2f}".format(*r.get("size_blender_xyz", (0, 0, 0)))]
    for j, line in enumerate(lines):
        d.text((x + 4, y + 38 + j * 28), line, font=F_S, fill=WHITE)
y += 38 + 4 * 28 + M
page = page.crop((0, 0, W, y))
page.save(os.path.join(lineup_dir, "batch_sheet.jpg"), quality=90)
print("ГОТОВО", page.size)
