"""Листы концептов Ловибумов, вторая версия (D55, этап 0: энергетические капсулы) с русскими подписями.

Берёт рендеры scripts/blender/lovibum_concepts.py: у главных кадров есть проход свечения <кадр>_glow.png — его
размытие добавляется к кадру (ореол ядер, сети и искр). Пишет в <папка>: lineup.jpg (линейка), boom.jpg / turbo.jpg /
mega.jpg (крупно и повороты), flight.jpg (в полёте), capture.jpg (захват энергетической сетью по шагам), scale.jpg
(манекены Roblox с капсулой на ладони и крупные планы), before_after.jpg (отклонённая первая версия и новая — если
передан кадр первой версии).
Запуск: python scripts/d55_lovibum_sheets.py <рендеры> <папка> [<trio_front.png первой версии>]
Зависит от Pillow.
"""

import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

RAW, OUT = sys.argv[1], sys.argv[2]
BEFORE = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(OUT, exist_ok=True)
BG = (32, 35, 44)
FONT = "C:/Windows/Fonts/segoeuib.ttf"
NAMES = {"Boom": ("Бум", "бонус ×1", (255, 194, 26)), "Turbo": ("Турбо", "бонус ×1.5", (90, 200, 255)),
         "Mega": ("Мега", "бонус ×2", (196, 130, 255))}


def font(size):
    return ImageFont.truetype(FONT, size)


def load(name):
    """Кадр со свечением: размытый проход свечения добавляется экраном (если он есть)."""
    base = Image.open(os.path.join(RAW, name)).convert("RGB")
    glow_path = os.path.join(RAW, name.replace(".png", "_glow.png"))
    if not os.path.exists(glow_path):
        return base
    glow = Image.open(glow_path).convert("RGB")
    k = max(base.size) / 1100
    for radius, gain in ((10 * k, 200), (30 * k, 170)):
        blur = glow.filter(ImageFilter.GaussianBlur(radius))
        base = ImageChops.screen(base, ImageChops.multiply(blur, Image.new("RGB", base.size, (gain,) * 3)))
    return base


def wrap(line, width):
    """Перенос по словам."""
    out, cur = [], ""
    for word in line.split():
        if cur and len(cur) + 1 + len(word) > width:
            out.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return out + ([cur] if cur else [])


def fit(im, width):
    return im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)


def text(draw, xy, s, size, fill=(255, 255, 255), anchor="la"):
    draw.text(xy, s, font=font(size), fill=fill, anchor=anchor, stroke_width=max(2, size // 14),
              stroke_fill=(20, 22, 28))


def stack(rows, gap=8, header=None):
    width = max(r.width for r in rows)
    top = 90 if header else 0
    sheet = Image.new("RGB", (width, top + sum(r.height for r in rows) + gap * (len(rows) - 1)), BG)
    y = top
    for r in rows:
        sheet.paste(r, ((width - r.width) // 2, y))
        y += r.height + gap
    if header:
        text(ImageDraw.Draw(sheet), (30, 22), header, 46)
    return sheet


def row(images, gap=8):
    h = max(im.height for im in images)
    out = Image.new("RGB", (sum(im.width for im in images) + gap * (len(images) - 1), h), BG)
    x = 0
    for im in images:
        out.paste(im, (x, 0))
        x += im.width + gap
    return out


def names(im, centers, y=36, big=62, small=38):
    d = ImageDraw.Draw(im)
    for name, x in centers.items():
        ru, bonus, color = NAMES[name]
        text(d, (x, y), ru, big, fill=color, anchor="ma")
        text(d, (x, y + big + 8), bonus, small, anchor="ma")
    return im


report = json.load(open(os.path.join(RAW, "report.json"), encoding="utf-8"))

# 1. Линейка.
lineup = names(load("lineup.png"), {"Boom": 350, "Turbo": 975, "Mega": 1600})
d = ImageDraw.Draw(lineup)
text(d, (30, lineup.height - 118), "Одна форма: капсула, ступенчатые торцы, четыре стойки, энергетическое ядро в окнах", 36,
     fill=(220, 224, 235))
text(d, (30, lineup.height - 66), "Рост: простой корпус → стабилизаторы и свет → золото, кристалл и дуги", 36,
     fill=(220, 224, 235))
stack([lineup], header="Ловибумы v2 — энергетические капсулы (стиль D39), на утверждение").save(
    os.path.join(OUT, "lineup.jpg"), quality=90)

# 2. Каждая капсула: крупно и повороты.
notes = {"Boom": "оранжево-жёлтый корпус, бирюзовое ядро — самая простая",
         "Turbo": "сине-голубая, решётка, световые полосы, огоньки, 4 стабилизатора",
         "Mega": "фиолетово-золотая, кристаллическое ядро, золотые дуги с кристаллами"}
for name in ("Boom", "Turbo", "Mega"):
    ru, bonus, color = NAMES[name]
    hero = load(f"Lovibum_{name}_hero.png")
    turns = fit(load(f"Lovibum_{name}_turns.png"), hero.width * 2)
    d = ImageDraw.Draw(turns)
    for i, s in enumerate(("Спереди", "3/4", "Сбоку", "Сзади")):
        text(d, (i * turns.width // 4 + 24, 20), s, 40)
    side = Image.new("RGB", (hero.width, hero.height), BG)
    d = ImageDraw.Draw(side)
    size = report[name]["size"]
    text(d, (40, 60), ru, 110, fill=color)
    text(d, (40, 200), bonus, 54)
    y = 300
    for line in (notes[name], f"{size[0]} × {size[1]} × {size[2]} стада", f"{report[name]['tris']} треугольников"):
        for chunk in wrap(line, 34):
            text(d, (40, y), chunk, 44, fill=(220, 224, 235))
            y += 60
        y += 20
    stack([row([hero, side]), turns], header=f"{ru} — {bonus}").save(os.path.join(OUT, f"{name.lower()}.jpg"),
                                                                     quality=90)

# 3. В полёте.
flight = names(load("flight.png"), {"Boom": 420, "Turbo": 1000, "Mega": 1650}, y=60, big=52, small=32)
d = ImageDraw.Draw(flight)
text(d, (30, flight.height - 70), "В полёте: верхом вперёд, крутится вокруг оси, за ней — след из квадратных искр цвета ядра",
     34, fill=(220, 224, 235))
stack([flight], header="Ловибумы в полёте").save(os.path.join(OUT, "flight.jpg"), quality=90)

# 4. Захват энергетической сетью — шаги.
steps = (("capture_1_throw.png", "1. Бросок", "капсула летит, след искр"),
         ("capture_2_net.png", "2. Сеть", "зависла и раскинула сеть"),
         ("capture_3_squeeze.png", "3. Сжатие", "сеть — в куб света, луч в ядро"),
         ("capture_4_caught.png", "4. Поймано", "ядро вспыхивает, искры"),
         ("capture_5_escape.png", "5. Вырвалось", "сеть рассыпается на квадраты"))
tiles = []
for fname, title, sub in steps:
    im = fit(load(fname), 900)
    d = ImageDraw.Draw(im)
    text(d, (24, 18), title, 54)
    text(d, (24, 84), sub, 34, fill=(220, 224, 235))
    tiles.append(im)
info = Image.new("RGB", (900, 900), BG)
d = ImageDraw.Draw(info)
lines = ["Захват энергетической сетью", "", "Капсула не раскрывается и не", "засасывает существо лучом:",
         "она зависает над ним и плетёт", "сеть из квадратных ячеек.", "", "Сеть стягивается в куб света",
         "и уходит лучом в ядро.", "", "Неудача — сеть рассыпается", "квадратными осколками.", "",
         "Цвет сети = цвет ядра:", "бирюзовый · голубой · фиолетовый"]
y = 60
for i, line in enumerate(lines):
    text(d, (40, y), line, 50 if i == 0 else 40, fill=(255, 255, 255) if i == 0 else (220, 224, 235))
    y += 70 if i == 0 else 52
stack([row(tiles[:3]), row(tiles[3:] + [info])], header="Захват: сеть вместо «раскрыться и втянуть»").save(
    os.path.join(OUT, "capture.jpg"), quality=90)

# 5. Масштаб.
scale = load("hand_scale.png")
names(scale, {"Boom": 380, "Turbo": 1110, "Mega": 1840}, y=150, big=58, small=34)
closeups = [fit(load(f"hand_{n}.png"), (scale.width - 16) // 3) for n in ("Boom", "Turbo", "Mega")]
stack([scale, row(closeups)], header="Масштаб: манекен Roblox 5.2 стада, капсула на ладони вытянутой руки").save(
    os.path.join(OUT, "scale.jpg"), quality=90)

# 6. Было → стало.
if BEFORE:
    a = fit(Image.open(BEFORE).convert("RGB"), 1400)
    b = fit(load("lineup.png"), 1400)
    text(ImageDraw.Draw(a), (24, 20), "v1 — отклонено: персонажи с лицами", 50)
    text(ImageDraw.Draw(b), (24, 20), "v2 — устройства одной линейки, без лиц", 50)
    stack([a, b], header="Ловибумы: первая версия и новая").save(os.path.join(OUT, "before_after.jpg"), quality=90)
print("SHEETS_OK")
