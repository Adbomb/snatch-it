"""D48 v2 — листы для утверждения: план двух этажей с размерами, лист устройств защиты с описаниями, сводный лист
кадров музея. Собирает готовые рендеры (scripts/blender/d48_museum.py, d48_devices.py); в игру ничего не попадает.

Планы 15/16: 1100², орто 58 стадов, центр — точка участка (x 0, z 4), вход (−z) внизу, +x участка — слева.
Запуск: python scripts/d48_v2_sheets.py  → assets/concepts/d48/v2/sheets/*.png
"""

import glob
import json
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V2 = os.path.join(ROOT, "assets", "concepts", "d48", "v2")
REN, DEV, OUT = os.path.join(V2, "renders"), os.path.join(V2, "devices"), os.path.join(V2, "sheets")
os.makedirs(OUT, exist_ok=True)
INK = (24, 20, 46)
GOLD = (255, 214, 90)
SOFT = (205, 216, 245)
SIZE, ORTHO, CZ = 1100, 58.0, 4.0
K = SIZE / ORTHO


def font(weight, size):
    path = None
    for p in sorted(glob.glob(os.path.expandvars(rf"%LOCALAPPDATA%\Roblox\Versions\*\content\fonts\Montserrat-{weight}.ttf"))):
        path = p
    return ImageFont.truetype(path, size)


def say(d, xy, body, size=26, fill=(255, 255, 255), anchor="mm", weight="Black", stroke=INK):
    d.text(xy, body, font=font(weight, size), fill=fill, stroke_width=max(2, size // 8), stroke_fill=stroke,
           anchor=anchor)


def px(x, z):
    return SIZE / 2 - x * K, SIZE / 2 - (z - CZ) * K


def dim(d, a, b, body, offset=(0, 0), size=22):
    (x0, y0), (x1, y1) = a, b
    col = (255, 236, 140)
    d.line([a, b], fill=col, width=4)
    for (x, y) in (a, b):
        if abs(x1 - x0) > abs(y1 - y0):
            d.line([(x, y - 12), (x, y + 12)], fill=col, width=4)
        else:
            d.line([(x - 12, y), (x + 12, y)], fill=col, width=4)
    say(d, ((x0 + x1) / 2 + offset[0], (y0 + y1) / 2 + offset[1]), body, size, col)


def gradient(w, h, top=(43, 58, 103), bot=(22, 28, 54)):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)))
    return img


def wrap(d, body, f, width):
    words, lines, cur = body.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=f) <= width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ── 1. План двух этажей ────────────────────────────────────────────────────────────────────────────────────────
def plans():
    data = json.load(open(os.path.join(V2, "bricks", "museum.json"), encoding="utf-8"))
    up = Image.open(os.path.join(REN, "15_plan_upper.png")).convert("RGB")
    vt = Image.open(os.path.join(REN, "16_plan_vault.png")).convert("RGB")
    du, dv = ImageDraw.Draw(up), ImageDraw.Draw(vt)
    say(du, (SIZE / 2, 40), "ВЕРХНИЙ ЭТАЖ — ГАЛЕРЕЯ", 34)
    dim(du, px(18, 25.5), px(-18, 25.5), "36 ст.", (0, -26))
    dim(du, px(19.6, -12.7), px(19.6, 20.7), "33,4 ст.", (-62, 0))
    say(du, px(0, -19.5), "ВХОД · портик", 24)
    for place in data["places"]:
        x, _, z = place["center"]
        say(du, px(x, z), str(place["slot"]), 44, GOLD)
    say(du, px(0, 7.0), "ПАВИЛЬОН", 22)
    say(du, px(0, 5.2), "лестница вниз", 18, weight="Bold")
    say(du, px(-12.0, -6.6), "сундук", 20, weight="Bold")
    say(du, px(12.0, -6.6), "стенд", 20, weight="Bold")
    say(du, px(0, -1.4), "медальон", 18, SOFT, weight="Bold")
    for name, z in (("лазер: вход", -8.6), ("лазер: галерея", -6.4)):
        say(du, px(-8.6, z + (0.9 if "гал" in name else -0.9)), name, 16, (255, 130, 130), weight="Bold")
    say(du, px(-20.5, 21.2), "участок 44 × 44", 20, anchor="rb", weight="Bold")
    say(dv, (SIZE / 2, 40), "ПОДЗЕМНЫЙ ЭТАЖ — ХРАНИЛИЩЕ", 34)
    dim(dv, px(16.6, 25.5), px(-16.6, 25.5), "33,2 ст. (внутри)", (0, -26))
    dim(dv, px(19.4, -11.3), px(19.4, 19.3), "30,6 ст.", (-62, 0))
    say(dv, px(0, 17.4), "СЕЙФ КОЛЛЕКЦИИ", 24, GOLD)
    say(dv, px(0, 9.0), "лестница", 20, weight="Bold")
    say(dv, px(0, 7.4), "12 ступ. × 1 ст.", 17, (255, 236, 140), weight="Bold")
    say(dv, px(0, 0.2), "терминал инвентаря", 20, weight="Bold")
    say(dv, px(12.5, -3.0), "центр безопасности", 20, weight="Bold")
    say(dv, px(-12.6, 1.5), "архив", 20, weight="Bold")
    say(dv, px(0, -9.6), "банковские ячейки", 18, weight="Bold")
    say(dv, px(-20.5, 21.2), "высота 11,6 ст.", 20, anchor="rb", weight="Bold")
    sheet = Image.new("RGB", (SIZE * 2 + 30, SIZE + 170), (24, 28, 48))
    sheet.paste(up, (0, 170))
    sheet.paste(vt, (SIZE + 30, 170))
    d = ImageDraw.Draw(sheet)
    say(d, (sheet.width // 2, 52), "D48 v2 — план музея на участке (1 стад = 1 клетка Roblox)", 40)
    say(d, (sheet.width // 2, 106), f"Контур как у нынешнего здания (36 × 33,4 + портик). Деталей: верх {data['upper']}, "
                                    f"низ {data['lower']}, всего {data['total']} из 400 (бюджет музея).", 24, SOFT,
        weight="Bold")
    say(d, (sheet.width // 2, 142), "Цифры 1–6 — официальные места экспонатов (номер витрины в игре).", 22, GOLD,
        weight="Bold")
    sheet = sheet.resize((sheet.width * 3 // 4, sheet.height * 3 // 4), Image.LANCZOS)
    sheet.save(os.path.join(OUT, "plan_v2.png"))


# ── 2. Лист устройств защиты ───────────────────────────────────────────────────────────────────────────────────
DEVICES = [
    ("trap.png", "Ловушка «Пружинная плита»",
     "Где: свободно на полу зала по образцу, не на постаменте и не в проходе (радиус 2).",
     "Обычно: плита с жёлто-чёрной рамкой, пять закрытых люков, бирюзовый огонёк.",
     "Срабатывание: шипы ступенями выходят из люков, красная вспышка по контуру.",
     "16 / 27 деталей"),
    ("snare.png", "Капкан «Захват»",
     "Где: свободно на полу зала, обычно у ниш — там, куда вор подходит красть.",
     "Обычно: круглое основание, челюсти раскрыты плашмя, бирюзовый огонёк.",
     "Срабатывание: челюсти смыкаются (10 с), красное кольцо и кнопка.",
     "17 / 18 деталей"),
    ("laser.png", "Лазерные стойки",
     "Где: только размеченные места поперёк прохода — «вход» и «галерея» (гнёзда в полу).",
     "Обычно: тёмно-синие колонны с золотыми кольцами, тонкий луч, бирюзовые маяки.",
     "Срабатывание: луч толще с ореолом, маяки красные, тревога владельцу.",
     "19 / 20 деталей"),
    ("door_strip.png", "Бронедверь",
     "Где: только в проёме входа 12 × 10, внутри золотой рамы портала.",
     "Обычно: две створки, сталь и золото, разметка внизу, замок-штурвал, бирюзовая лампа.",
     "Взлом: устройство на замке, оранжевый свет (5 с); после — створки уходят в стену, зелёная лампа.",
     "26–35 деталей"),
    ("robot.png", "Робот-охранник",
     "Где: свободно на полу зала; лучше у павильона хранилища или в середине галереи.",
     "Обычно: стоит на турели, бирюзовый визор, дубинка вперёд.",
     "Срабатывание: визор и антенна красные, дубинка поднята, разряд, красный круг на полу.",
     "24 / 28 деталей"),
]


def devices():
    strip = [Image.open(os.path.join(DEV, f"door_{s}.png")).convert("RGB") for s in ("idle", "hack", "open")]
    w = sum(i.width for i in strip)
    door = Image.new("RGB", (w, strip[0].height))
    x = 0
    for im in strip:
        door.paste(im, (x, 0))
        x += im.width
    W, CARD = 1800, 470
    sheet = gradient(W, 190 + CARD * len(DEVICES) + 40)
    d = ImageDraw.Draw(sheet)
    say(d, (W // 2, 62), "D48 v2 — защита музея (Blender, детали Roblox)", 50)
    say(d, (W // 2, 112), "Единый язык: тёмно-синий корпус, белые панели, золото; бирюзовый — дежурит, красный — сработал",
        22, SOFT, weight="Bold")
    say(d, (W // 2, 142), "жёлто-чёрная разметка — только у напольных устройств и двери", 22, SOFT, weight="Bold")
    for k, (img_name, title, where, idle, active, parts) in enumerate(DEVICES):
        y = 170 + k * CARD
        d.rounded_rectangle((40, y, W - 40, y + CARD - 30), 30, fill=(30, 38, 72))
        im = door if img_name == "door_strip.png" else Image.open(os.path.join(DEV, img_name)).convert("RGB")
        th = CARD - 60
        tw = int(im.width * th / im.height)
        if tw > 960:
            tw = 960
            th = int(im.height * tw / im.width)
        im = im.resize((tw, th), Image.LANCZOS)
        mask = Image.new("L", im.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, tw - 1, th - 1), 22, fill=255)
        sheet.paste(im, (60, y + 15 + (CARD - 60 - th) // 2), mask)
        tx = 60 + tw + 40
        say(d, (tx, y + 50), title, 34, GOLD, anchor="lm")
        f = font("Bold", 22)
        yy = y + 100
        for label, body in (("", where), ("", idle), ("", active)):
            for line in wrap(d, body, f, W - 80 - tx):
                d.text((tx, yy), line, font=f, fill=(235, 240, 255))
                yy += 32
            yy += 14
        say(d, (tx, max(yy + 6, y + CARD - 75)), parts, 22, (124, 255, 107), anchor="lm", weight="Bold")
        if k == 0:
            say(d, (60 + tw // 4, y + 40), "обычно", 22, anchor="mm", weight="Bold")
            say(d, (60 + tw * 3 // 4, y + 40), "сработала", 22, (255, 140, 140), anchor="mm", weight="Bold")
    sheet = sheet.resize((sheet.width * 3 // 4, sheet.height * 3 // 4), Image.LANCZOS)
    sheet.save(os.path.join(OUT, "devices_v2.png"))


# ── 3. Сводный лист кадров музея ───────────────────────────────────────────────────────────────────────────────
SHOTS = [
    ("01_exterior", "Снаружи — контур прежний"), ("02_hall_from_entrance", "Галерея от входа"),
    ("03_hall_toward_entrance", "Галерея к выходу"), ("04_hall_overview", "Зал сверху"),
    ("07_vault_entrance", "Павильон и сейфовая дверь"), ("08_stair_down", "Лестница вниз"),
    ("09_vault_safe", "Сейф коллекции"), ("10_vault_main", "Хранилище"),
    ("11_vault_security", "Центр безопасности"), ("12_vault_overview", "Хранилище сверху"),
    ("13_section", "Разрез: два этажа"), ("14_defense_in_museum", "Защита в зале"),
]


def contact():
    cw, ch = 560, 315
    cols = 3
    rows = (len(SHOTS) + cols - 1) // cols
    W, H = cols * cw + (cols + 1) * 24, 150 + rows * (ch + 70)
    sheet = gradient(W, H)
    d = ImageDraw.Draw(sheet)
    say(d, (W // 2, 60), "D48 v2 — музей игрока: галерея и хранилище", 46)
    say(d, (W // 2, 108), "Blender, EEVEE; всё собрано из деталей Roblox (Block, Cylinder, Ball, Wedge)", 22, SOFT,
        weight="Bold")
    for k, (name, caption) in enumerate(SHOTS):
        r, c = divmod(k, cols)
        x, y = 24 + c * (cw + 24), 150 + r * (ch + 70)
        im = Image.open(os.path.join(REN, name + ".png")).convert("RGB").resize((cw, ch), Image.LANCZOS)
        mask = Image.new("L", im.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw - 1, ch - 1), 18, fill=255)
        sheet.paste(im, (x, y), mask)
        say(d, (x + cw // 2, y + ch + 30), caption, 24, anchor="mm", weight="Black")
    sheet.save(os.path.join(OUT, "museum_v2_contact.png"))


if __name__ == "__main__":
    plans()
    devices()
    contact()
    print("ok")
