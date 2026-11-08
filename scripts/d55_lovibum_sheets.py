"""Листы концептов Ловибумов v3 (D55, этап 0: энергетические капсулы) с русскими подписями.

Берёт рендеры scripts/blender/lovibum_concepts.py: у главных кадров есть проход свечения <кадр>_glow.png — его
размытие добавляется к кадру (ореол ядер, сети и искр). Пишет в <папка>: lineup.jpg (линейка), boom.jpg / turbo.jpg /
mega.jpg (крупно и повороты), flight.jpg (в полёте), capture.jpg (захват энергетической сетью по шагам), scale.jpg
(манекены Roblox с капсулой на ладони и крупные планы), phone.jpg (кадры размера экрана телефона 844 × 390 в масштабе
1 : 1: в руке и бросок, с увеличением места, где капсула), before_after.jpg (v2 и v3 — если передан кадр v2).
Запуск: python scripts/d55_lovibum_sheets.py <рендеры> <папка> [<lineup.png v2>]
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
text(d, (30, lineup.height - 118), "Одна форма: капсула, торцы, четыре стойки, ядро в окнах; символ — светящийся ромб", 36,
     fill=(220, 224, 235))
text(d, (30, lineup.height - 66), "Рост: простой корпус → стабилизаторы и свет → золото, кристалл и дуги", 36,
     fill=(220, 224, 235))
stack([lineup], header="Ловибумы v3 — энергетические капсулы (стиль D39), финальные правки").save(
    os.path.join(OUT, "lineup.jpg"), quality=90)

# 2. Каждая капсула: крупно и повороты.
notes = {"Boom": "оранжево-жёлтая, бирюзовое ядро — самая простая; v3: круглее (мельче ступени, шире срез)",
         "Turbo": "сине-голубая, решётка, световые полосы, огоньки, 4 стабилизатора",
         "Mega": "фиолетово-золотая, кристаллическое ядро, золотые дуги; v3: дуги меньше на ~22 %"}
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
    for line in (notes[name], "символ системы — светящийся ромб на верхнем поясе",
                 f"{size[0]} × {size[1]} × {size[2]} стада", f"{report[name]['tris']} треугольников"):
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

# 6. Телефон: кадры 844 × 390 в масштабе 1 : 1 и увеличение места, где капсула (по проходу свечения).
def zoom_box(name, pad=60, k=3):
    glow = Image.open(os.path.join(RAW, name.replace(".png", "_glow.png"))).convert("L")
    box = glow.point(lambda v: 255 if v > 90 else 0).getbbox() or (0, 0, glow.width, glow.height)
    cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
    half = max(box[2] - box[0], box[3] - box[1]) // 2 + pad
    crop = (max(0, cx - half), max(0, cy - half), min(glow.width, cx + half), min(glow.height, cy + half))
    return crop, k


def phone_frame(im):
    w, h = im.size
    out = Image.new("RGB", (w + 40, h + 40), (12, 13, 18))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((2, 2, w + 37, h + 37), radius=26, outline=(70, 74, 88), width=3)
    out.paste(im, (20, 20))
    return out


rows_ = []
for name in ("Boom", "Turbo", "Mega"):
    ru, bonus, color = NAMES[name]
    cells = []
    for kind, title in (("hand", "в руке — камера Roblox"), ("throw", "бросок в мини-игре")):
        fname = f"phone_{kind}_{name}.png"
        im = load(fname)
        crop, k = zoom_box(fname)
        z = im.crop(crop)
        z = z.resize((z.width * k, z.height * k), Image.NEAREST)
        z = z.resize((im.height, im.height), Image.LANCZOS) if z.height != im.height else z
        framed = phone_frame(im)
        d = ImageDraw.Draw(framed)
        text(d, (34, 28), f"{ru} — {title}", 26, fill=color)
        d.rectangle((20 + crop[0], 20 + crop[1], 20 + crop[2], 20 + crop[3]), outline=(255, 214, 64), width=2)
        zoomed = Image.new("RGB", (im.height + 40, im.height + 40), BG)
        zoomed.paste(z, (20, 20))
        text(ImageDraw.Draw(zoomed), (30, 26), "увеличено", 24, fill=(255, 214, 64))
        cells += [framed, zoomed]
    rows_.append(row(cells, gap=12))
phone = stack(rows_, gap=12, header="Телефон: кадры 844 × 390 точек в масштабе 1 : 1 (жёлтая рамка — что увеличено)")
phone.save(os.path.join(OUT, "phone.jpg"), quality=90)

# 7. Было → стало.
if BEFORE:
    a = fit(Image.open(BEFORE).convert("RGB"), 1400)
    b = fit(load("lineup.png"), 1400)
    text(ImageDraw.Draw(a), (24, 20), "v2 — предварительно утверждено", 50)
    text(ImageDraw.Draw(b), (24, 20), "v3 — Бум круглее, дуги Меги меньше, символ-ромб", 50)
    stack([a, b], header="Ловибумы: v2 и v3").save(os.path.join(OUT, "before_after.jpg"), quality=90)
print("SHEETS_OK")
