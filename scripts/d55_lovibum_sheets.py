"""Листы концептов Ловибумов v5 (D55, этап 0: устройства «кристалл в когтях») с русскими подписями.

Берёт рендеры scripts/blender/lovibum_concepts.py: у кадров есть проход свечения <кадр>_glow.png — его размытие
добавляется к кадру (ореол ядер, кристаллов, сети и искр; умеренно, чтобы не закрывать существо). Пишет в <папка>:
lineup.jpg (линейка), boom.jpg / turbo.jpg / mega.jpg (закрыт, когти раскрыты, повороты), flight.jpg (в полёте),
capture.jpg (поимка сетью по шагам), scale.jpg (манекены Roblox с Ловибумом на ладони и крупные планы), phone.jpg
(кадры размера экрана телефона 844 × 390 в масштабе 1 : 1 без увеличения: в руке, бросок, сеть над существом),
before_after.jpg (v4 и v5 — если передан кадр линейки v4).
Запуск: python scripts/d55_lovibum_sheets.py <рендеры> <папка> [<lineup.png v4>]
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
NOTES = {"Boom": "простой и цельный: большое ядро-шар, короткие толстые когти с заклёпками, крупные защёлки",
         "Turbo": "быстрый и чистый: одна широкая полоса света на когте, стреловидные стабилизаторы, сопло-кольцо",
         "Mega": "самый ценный: ядро — огромный гранёный кристалл в золотой короне, золотые когти и камни"}


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
    for radius, gain in ((10 * k, 150), (30 * k, 100)):
        blur = glow.filter(ImageFilter.GaussianBlur(radius))
        base = ImageChops.screen(base, ImageChops.multiply(blur, Image.new("RGB", base.size, (gain,) * 3)))
    return base


def fit(im, width):
    return im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)


def text(draw, xy, s, size, fill=(255, 255, 255), anchor="la"):
    draw.text(xy, s, font=font(size), fill=fill, anchor=anchor, stroke_width=max(2, size // 14),
              stroke_fill=(20, 22, 28))


def stack(rows, gap=8, header=None, sub=None):
    width = max(r.width for r in rows)
    top = (90 if header else 0) + (50 if sub else 0)
    sheet = Image.new("RGB", (width, top + sum(r.height for r in rows) + gap * (len(rows) - 1)), BG)
    y = top
    for r in rows:
        sheet.paste(r, ((width - r.width) // 2, y))
        y += r.height + gap
    d = ImageDraw.Draw(sheet)
    if header:
        text(d, (30, 22), header, 46)
    if sub:
        text(d, (30, 92), sub, 32, fill=(220, 224, 235))
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
lineup = names(load("lineup.png"), {"Boom": 330, "Turbo": 990, "Mega": 1620})
d = ImageDraw.Draw(lineup)
text(d, (30, lineup.height - 118), "Фирменный элемент: кристалл-ромб в четырёх когтях — при поимке когти раскрываются",
     34, fill=(220, 224, 235))
text(d, (30, lineup.height - 66), "Кристалл растёт с уровнем: маленький у Бума → вытянутый у Турбо → огромный у Меги",
     34, fill=(220, 224, 235))
stack([lineup], header="Ловибумы v5 — «кристалл в когтях»: жирнее и чище силуэты, на утверждение").save(
    os.path.join(OUT, "lineup.jpg"), quality=90)

# 2. Каждый: закрыт, когти раскрыты, повороты.
for name in ("Boom", "Turbo", "Mega"):
    ru, bonus, color = NAMES[name]
    hero, opened = load(f"Lovibum_{name}_hero.png"), load(f"Lovibum_{name}_open_hero.png")
    top = row([hero, opened])
    d = ImageDraw.Draw(top)
    text(d, (30, 26), "Закрыт", 48)
    text(d, (hero.width + 38, 26), "Когти раскрыты — поимка", 48)
    turns = fit(load(f"Lovibum_{name}_turns.png"), top.width)
    d = ImageDraw.Draw(turns)
    for i, s in enumerate(("Спереди", "3/4", "Сбоку", "Сзади")):
        text(d, (i * turns.width // 4 + 24, 20), s, 40)
    size = report[name]["size"]
    stack([top, turns], header=f"{ru} — {bonus} · {size[0]} × {size[1]} × {size[2]} стада · {report[name]['tris']} треуг.",
          sub=NOTES[name]).save(os.path.join(OUT, f"{name.lower()}.jpg"), quality=90)

# 3. В полёте.
flight = names(load("flight.png"), {"Boom": 420, "Turbo": 1000, "Mega": 1650}, y=60, big=52, small=32)
d = ImageDraw.Draw(flight)
text(d, (30, flight.height - 70), "В полёте: кристаллом вперёд, крутится вокруг оси, короткий след из квадратных искр цвета ядра",
     32, fill=(220, 224, 235))
stack([flight], header="Ловибумы в полёте").save(os.path.join(OUT, "flight.jpg"), quality=90)

# 4. Поимка энергетической сетью — шаги.
steps = (("capture_1_throw.png", "1. Бросок", "летит кристаллом вперёд"),
         ("capture_2_net.png", "2. Сеть", "когти раскрылись, кристалл плетёт сеть"),
         ("capture_3_squeeze.png", "3. Сжатие", "сеть — в куб света, луч в кристалл"),
         ("capture_4_caught.png", "4. Поймано", "когти сомкнулись, ядро вспыхивает"),
         ("capture_5_escape.png", "5. Вырвалось", "сеть рассыпается на квадраты"))
tiles = []
for fname, title, subtitle in steps:
    im = fit(load(fname), 900)
    d = ImageDraw.Draw(im)
    text(d, (24, 18), title, 54)
    text(d, (24, 84), subtitle, 32, fill=(220, 224, 235))
    tiles.append(im)
info = Image.new("RGB", (900, 900), BG)
d = ImageDraw.Draw(info)
lines = ["Поимка — механизм когтей", "", "Ловибум зависает над существом,", "четыре когтя раскрываются,",
         "кристалл плетёт сеть из", "квадратных ячеек.", "", "Сеть стягивается в куб света и",
         "уходит лучом в кристалл; когти", "смыкаются — поймано.", "", "Неудача — сеть рассыпается.",
         "Цвет сети = цвет ядра.", "Существо видно сквозь сеть."]
y = 60
for i, line in enumerate(lines):
    text(d, (40, y), line, 50 if i == 0 else 40, fill=(255, 255, 255) if i == 0 else (220, 224, 235))
    y += 70 if i == 0 else 52
stack([row(tiles[:3]), row(tiles[3:] + [info])], header="Поимка: когти раскрываются, кристалл плетёт сеть").save(
    os.path.join(OUT, "capture.jpg"), quality=90)

# 5. Масштаб.
scale = load("hand_scale.png")
names(scale, {"Boom": 380, "Turbo": 1110, "Mega": 1840}, y=150, big=58, small=34)
closeups = [fit(load(f"hand_{n}.png"), (scale.width - 16) // 3) for n in ("Boom", "Turbo", "Mega")]
stack([scale, row(closeups)], header="Масштаб: манекен Roblox 5.2 стада, Ловибум на ладони вытянутой руки").save(
    os.path.join(OUT, "scale.jpg"), quality=90)


# 6. Телефон: кадры 844 × 390 в масштабе 1 : 1, без увеличения.
def phone_frame(im, label, color):
    w, h = im.size
    out = Image.new("RGB", (w + 40, h + 40), (12, 13, 18))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((2, 2, w + 37, h + 37), radius=26, outline=(70, 74, 88), width=3)
    out.paste(im, (20, 20))
    text(d, (34, 28), label, 24, fill=color)
    return out


rows_ = []
for name in ("Boom", "Turbo", "Mega"):
    ru, bonus, color = NAMES[name]
    cells = [phone_frame(load(f"phone_{kind}_{name}.png"), f"{ru} — {title}", color)
             for kind, title in (("hand", "в руке, камера Roblox"), ("throw", "бросок"), ("net", "сеть над существом"))]
    rows_.append(row(cells, gap=12))
stack(rows_, gap=12, header="Телефон: кадры 844 × 390 точек в масштабе 1 : 1, без увеличения",
      sub="Свечение умеренное: существо видно сквозь сеть, след при броске короткий").save(
    os.path.join(OUT, "phone.jpg"), quality=90)

# 7. Было → стало.
if BEFORE:
    a = fit(Image.open(BEFORE).convert("RGB"), 1400)
    b = fit(load("lineup.png"), 1400)
    text(ImageDraw.Draw(a), (24, 20), "v4 — Бум «ободок», Мега «яйцо в клетке»", 50)
    text(ImageDraw.Draw(b), (24, 20), "v5 — цельный Бум, чистый Турбо, Мега-корона", 50)
    stack([a, b], header="Ловибумы: v4 и v5").save(os.path.join(OUT, "before_after.jpg"), quality=90)
print("SHEETS_OK")
