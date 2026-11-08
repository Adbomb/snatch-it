"""Листы концептов Ловибумов (D55, этап 0) с русскими подписями из рендеров scripts/blender/lovibum_concepts.py.

Пишет в <папка>: trio.jpg (три рядом спереди и сзади), boom.jpg / turbo.jpg / mega.jpg (закрыт, открыт, повороты),
scale.jpg (манекены Roblox с Ловибумом на ладони и крупные планы), before_after.jpg (первая версия и итог, если
передана папка первой версии).
Запуск: python scripts/d55_lovibum_sheets.py <рендеры> <папка> [<рендеры первой версии>]
Зависит от Pillow.
"""

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

RAW, OUT = sys.argv[1], sys.argv[2]
BEFORE = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(OUT, exist_ok=True)
BG = (32, 35, 44)
FONT = "C:/Windows/Fonts/segoeuib.ttf"
NAMES = {"Boom": ("Бум", "бонус ×1", (255, 194, 26)), "Turbo": ("Турбо", "бонус ×1.5", (63, 160, 255)),
         "Mega": ("Мега", "бонус ×2", (176, 112, 255))}


def font(size):
    return ImageFont.truetype(FONT, size)


def load(name, folder=RAW):
    return Image.open(os.path.join(folder, name)).convert("RGB")


def fit(im, width):
    return im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)


def text(draw, xy, s, size, fill=(255, 255, 255), anchor="la"):
    draw.text(xy, s, font=font(size), fill=fill, anchor=anchor, stroke_width=max(2, size // 14),
              stroke_fill=(20, 22, 28))


def stack(rows, gap=0, header=None, width=None):
    width = width or max(r.width for r in rows)
    top = 90 if header else 0
    sheet = Image.new("RGB", (width, top + sum(r.height for r in rows) + gap * (len(rows) - 1)), BG)
    y = top
    for r in rows:
        sheet.paste(r, ((width - r.width) // 2, y))
        y += r.height + gap
    if header:
        text(ImageDraw.Draw(sheet), (30, 22), header, 46)
    return sheet


def label_trio(im, centers, title):
    d = ImageDraw.Draw(im)
    for name, x in centers.items():
        ru, bonus, color = NAMES[name]
        text(d, (x, 40), ru, 64, fill=color, anchor="ma")
        text(d, (x, 112), bonus, 40, anchor="ma")
    text(d, (30, im.height - 70), title, 38, fill=(220, 224, 235))
    return im


report = json.load(open(os.path.join(RAW, "report.json"), encoding="utf-8"))

# 1. Три рядом: спереди и сзади.
centers = {"Boom": 330, "Turbo": 1010, "Mega": 1615}
front = label_trio(load("trio_front.png"), centers, "Спереди: «пасть» для захвата, глаза, свой силуэт у каждого")
back = label_trio(load("trio_back.png"), centers,
                  "Сзади — так Ловибум видит игрок в мини-игре: номер уровня, «взрыв», пламя, звезда")
stack([front, back], gap=8, header="Ловибумы — концепты D55 (стиль D39), на утверждение").save(
    os.path.join(OUT, "trio.jpg"), quality=90)

# 2. Каждый отдельно: закрыт и открыт сверху, повороты снизу.
for name in ("Boom", "Turbo", "Mega"):
    ru, bonus, color = NAMES[name]
    hero, opened = load(f"Lovibum_{name}_hero.png"), load(f"Lovibum_{name}_open_hero.png")
    top = Image.new("RGB", (hero.width * 2 + 8, hero.height), BG)
    top.paste(hero, (0, 0))
    top.paste(opened, (hero.width + 8, 0))
    d = ImageDraw.Draw(top)
    text(d, (30, 30), "Закрыт", 48)
    text(d, (hero.width + 38, 30), "Открыт — захват «кусь»", 48)
    turns = fit(load(f"Lovibum_{name}_turns.png"), top.width)
    d = ImageDraw.Draw(turns)
    for i, s in enumerate(("Спереди", "3/4", "Сбоку", "Сзади")):
        text(d, (i * turns.width // 4 + 24, 20), s, 40)
    size = report[name]["size"]
    head = f"{ru} — {bonus} · {size[0]} × {size[1]} × {size[2]} стада · {report[name]['tris']} треуг."
    stack([top, turns], gap=8, header=head).save(os.path.join(OUT, f"{name.lower()}.jpg"), quality=90)

# 3. Масштаб: манекены Roblox (5.2 стада) с Ловибумом на ладони и крупные планы.
scale = load("hand_scale.png")
d = ImageDraw.Draw(scale)
for name, x in {"Boom": 330, "Turbo": 1000, "Mega": 1700}.items():
    ru, bonus, color = NAMES[name]
    text(d, (x, 120), ru, 60, fill=color, anchor="ma")
closeups = [fit(load(f"hand_{n}.png"), (scale.width - 16) // 3) for n in ("Boom", "Turbo", "Mega")]
row = Image.new("RGB", (scale.width, closeups[0].height), BG)
for i, im in enumerate(closeups):
    row.paste(im, (i * (im.width + 8), 0))
stack([scale, row], gap=8, header="Масштаб: манекен Roblox 5.2 стада, Ловибум на ладони вытянутой руки").save(
    os.path.join(OUT, "scale.jpg"), quality=90)

# 4. Было → стало (первая версия и итог, те же камеры).
if BEFORE:
    a, b = fit(load("trio_front.png", BEFORE), 1400), fit(load("trio_front.png"), 1400)
    d = ImageDraw.Draw(a)
    text(d, (24, 20), "v1 — было", 52)
    d = ImageDraw.Draw(b)
    text(d, (24, 20), "итог — стало", 52)
    stack([a, b], gap=8, header="Две правки после критики: нос Турбо, спина Бума, «торт» Меги, рука").save(
        os.path.join(OUT, "before_after.jpg"), quality=90)
print("SHEETS_OK")
