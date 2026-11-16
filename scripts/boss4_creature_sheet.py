"""Лист утверждения существа босса 4 (art_oasis.py): все ракурсы, крупные планы, масштаб, кадр как в игре и
сравнение с эталоном D39 (ваза v13) — на одном листе, с подписями. Только кадры настоящей модели из Blender.
Запуск: python scripts/boss4_creature_sheet.py <папка кадров> <id> "<название · редкость>" "<строка с числами>"
Пишет <папка>/<id>_sheet.jpg и <папка>/<id>_vs_v13.jpg.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
folder, item, title, facts = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
BOLD = "C:/Windows/Fonts/arialbd.ttf"
F_T, F_L, F_S = ImageFont.truetype(BOLD, 44), ImageFont.truetype(BOLD, 26), ImageFont.truetype(BOLD, 22)
BG, GOLD, WHITE, GREY = (16, 18, 24), (255, 210, 63), (240, 242, 248), (170, 176, 190)


def img(name):
    return Image.open(os.path.join(folder, f"{item}_{name}.png")).convert("RGB")


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


W, M = 2400, 16
page = Image.new("RGB", (W, 3000), BG)
d = ImageDraw.Draw(page)
d.text((M, 14), title, font=F_T, fill=GOLD)
d.text((M, 72), facts, font=F_S, fill=GREY)
y0 = 116
# главный рендер слева, справа — спереди, сбоку, сзади, сверху
hero_w = 1100
page.paste(fit(img("hero"), hero_w, 1100), (M, y0))
label(d, (M + 14, y0 + 10), "главный рендер · три четверти")
cw, ch = (W - hero_w - 3 * M) // 2, (1100 - M) // 2
for k, (name, text) in enumerate((("front", "спереди"), ("side", "сбоку (слева)"), ("back", "сзади"),
                                  ("top", "сверху"))):
    x = M * 2 + hero_w + (k % 2) * (cw + M)
    y = y0 + (k // 2) * (ch + M)
    page.paste(fit(img(name), cw, ch), (x, y))
    label(d, (x + 12, y + 8), text)
y1 = y0 + 1100 + M
# крупные планы и поза
cw3 = (W - 4 * M) // 3
for k, (name, text) in enumerate((("face", "лицо крупно"), ("texture", "текстура D39 крупно: контуры запечены в карту"),
                                  ("pose", "пробная поза на суставах (части двигаются без дыр)"))):
    x = M + k * (cw3 + M)
    page.paste(fit(img(name), cw3, 620), (x, y1))
    label(d, (x + 12, y1 + 8), text, F_S)
y2 = y1 + 620 + M
# масштаб и кадр как в игре
sw = 1500
page.paste(fit(img("scale"), sw, 750), (M, y2))
label(d, (M + 12, y2 + 8), "масштаб: ваза v13 · существо на площадке 3.7 × 3.7 · манекен Roblox 5.2 стада", F_S)
pw = W - sw - 3 * M
phone = img("ingame_phone")
page.paste(fit(phone, pw, round(pw * phone.height / phone.width)), (M * 2 + sw, y2))
label(d, (M * 2 + sw + 12, y2 + 8), "как в игре: кадр телефона 844 × 390, 1 : 1", F_S)
ph = round(pw * phone.height / phone.width)
page.paste(fit(phone.crop((380, 80, 620, 300)), pw, 750 - ph - M), (M * 2 + sw, y2 + ph + M))
label(d, (M * 2 + sw + 12, y2 + ph + M + 8), "тот же кадр, увеличено в 2 раза", F_S)
y3 = y2 + 750 + M
page = page.crop((0, 0, W, y3))
page.save(os.path.join(folder, f"{item}_sheet.jpg"), quality=90)
print("ГОТОВО лист", page.size)

# сравнение с эталоном D39: вазой v13 — общий кадр и крупно на одинаковом расстоянии
cmp = Image.new("RGB", (W, 1500), BG)
d = ImageDraw.Draw(cmp)
d.text((M, 14), "Сравнение с эталоном D39 — ваза v13 (её дизайн не менялся)", font=F_T, fill=GOLD)
d.text((M, 72), "Те же правила: острые блоки, фаска 0.012, квадраты-контуры шаг 0.6 / квадрат 0.42 / контур 0.03, "
       "цвет, окклюзия и нормали запечены в карты 1024²", font=F_S, fill=GREY)
cmp.paste(fit(img("scale"), W - 2 * M, 700), (M, 116))
half = (W - 3 * M) // 2
cmp.paste(fit(img("vase_close"), half, 640), (M, 116 + 700 + M))
label(d, (M + 12, 116 + 700 + M + 8), "ваза v13 крупно")
cmp.paste(fit(img("texture"), half, 640), (2 * M + half, 116 + 700 + M))
label(d, (2 * M + half + 12, 116 + 700 + M + 8), "фенек крупно, тот же объектив")
cmp = cmp.crop((0, 0, W, 116 + 700 + M + 640 + M))
cmp.save(os.path.join(folder, f"{item}_vs_v13.jpg"), quality=90)
print("ГОТОВО сравнение", cmp.size)
