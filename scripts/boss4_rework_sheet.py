"""Лист «до / после» доработки существа босса 4 из кадров oasis_compare.py (общие ракурсы): каждая пара — одна камера,
свет, фон и настройки рендера; кадры не обрабатываются (только уменьшение под ячейку и увеличение кадра телефона без
сглаживания).
Запуск: python scripts/boss4_rework_sheet.py <папка кадров> <id> "<название>" "<что исправлено>"
Ждёт <папка>/v1_*.png и v2_*.png; пишет <папка>/<id>_rework_sheet.jpg.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
folder, item, title, note = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
BOLD = "C:/Windows/Fonts/arialbd.ttf"
F_T, F_S = ImageFont.truetype(BOLD, 42), ImageFont.truetype(BOLD, 21)
BG, GOLD, GREY, RED, GREEN = (16, 18, 24), (255, 210, 63), (170, 176, 190), (255, 120, 110), (120, 230, 140)
W, M = 2400, 16
NAMES = {"hero": "три четверти", "front": "спереди", "front34": "спереди-слева 45°", "front34r": "спереди-справа 45°",
         "face": "лицо спереди", "face34": "лицо слева 45°", "face34r": "лицо справа 45°", "side": "сбоку",
         "back": "сзади", "top": "сверху", "sil_front": "силуэт спереди", "sil_34": "силуэт под 45°"}


def img(tag, name):
    return Image.open(os.path.join(folder, f"{tag}_{name}.png")).convert("RGB")


def fit(im, w, h, resample=Image.LANCZOS):
    k = min(w / im.width, h / im.height)
    small = im.resize((round(im.width * k), round(im.height * k)), resample)
    cell = Image.new("RGB", (w, h), BG)
    cell.paste(small, ((w - small.width) // 2, (h - small.height) // 2))
    return cell


def label(d, xy, text, fill):
    x, y = xy
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        d.text((x + dx, y + dy), text, font=F_S, fill=BG)
    d.text(xy, text, font=F_S, fill=fill)


page = Image.new("RGB", (W, 6000), BG)
d = ImageDraw.Draw(page)
d.text((M, 14), f"{title} — до и после доработки", font=F_T, fill=GOLD)
d.text((M, 70), note, font=F_S, fill=GREY)
y = 110
cw = (W - 5 * M) // 4
for a_name, b_name in (("hero", "front"), ("front34", "front34r"), ("face", "face34"), ("face34r", "side"),
                       ("back", "top"), ("sil_front", "sil_34")):
    for k, (name, tag) in enumerate(((a_name, "v1"), (a_name, "v2"), (b_name, "v1"), (b_name, "v2"))):
        x = M + k * (cw + M)
        page.paste(fit(img(tag, name), cw, 600), (x, y))
        label(d, (x + 10, y + 8), ("ДО · " if tag == "v1" else "ПОСЛЕ · ") + NAMES[name], RED if tag == "v1" else GREEN)
    y += 600 + M
gw = (W - 3 * M) // 2
for k, tag in enumerate(("v1", "v2")):
    g = img(tag, "game")
    x = M + k * (gw + M)
    gh = round(gw * g.height / g.width)
    page.paste(fit(g, gw, gh), (x, y))
    label(d, (x + 10, y + 8), ("ДО" if tag == "v1" else "ПОСЛЕ") + " · как в игре: кадр телефона 844 × 390 (растянут под ячейку)",
          RED if tag == "v1" else GREEN)
    crop = g.crop((380, 110, 560, 290))
    page.paste(fit(crop, gw, 760, Image.NEAREST), (x, y + gh + M))
    label(d, (x + 10, y + gh + M + 8), ("ДО" if tag == "v1" else "ПОСЛЕ") + " · тот же кадр, существо ×4 без сглаживания",
          RED if tag == "v1" else GREEN)
y += round(gw * 390 / 844) + M + 760 + M
page = page.crop((0, 0, W, y))
page.save(os.path.join(folder, f"{item}_rework_sheet.jpg"), quality=90)
print("ГОТОВО", page.size)
