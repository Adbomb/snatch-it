"""Листы «до / после» полировки существа босса 4 из кадров oasis_compare.py: каждая пара — одна камера, свет, фон и
настройки рендера, кадры не обрабатываются (только уменьшение под ячейку и увеличение кадра телефона без сглаживания).
Запуск: python scripts/boss4_polish_sheet.py <папка кадров> <id> "<название>"
Ждёт <папка>/v1_*.png, v2_*.png, v2nomarks_*.png и metrics.json; пишет <папка>/<id>_polish_sheet.jpg (общий вид и игра)
и <папка>/<id>_polish_details.jpg (морда A/B, лицо, контуры D39, кубик, медальон).
"""

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
folder, item, title = sys.argv[1], sys.argv[2], sys.argv[3]
BOLD = "C:/Windows/Fonts/arialbd.ttf"
F_T, F_L, F_S = ImageFont.truetype(BOLD, 44), ImageFont.truetype(BOLD, 28), ImageFont.truetype(BOLD, 22)
BG, GOLD, WHITE, GREY, RED, GREEN = (16, 18, 24), (255, 210, 63), (240, 242, 248), (170, 176, 190), (255, 120, 110), (
    120, 230, 140)
W, M = 2400, 16
metrics = json.load(open(os.path.join(folder, "metrics.json"), encoding="utf-8"))


def img(tag, name):
    return Image.open(os.path.join(folder, f"{tag}_{name}.png")).convert("RGB")


def fit(im, w, h, resample=Image.LANCZOS):
    k = min(w / im.width, h / im.height)
    small = im.resize((round(im.width * k), round(im.height * k)), resample)
    cell = Image.new("RGB", (w, h), BG)
    cell.paste(small, ((w - small.width) // 2, (h - small.height) // 2))
    return cell


def label(d, xy, text, font=F_L, fill=WHITE):
    x, y = xy
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        d.text((x + dx, y + dy), text, font=font, fill=BG)
    d.text(xy, text, font=font, fill=fill)


def row(page, d, y, cells, h, caption=None):
    """cells: [(картинка, подпись, цвет подписи)] в одну строку равной ширины."""
    n = len(cells)
    cw = (W - (n + 1) * M) // n
    for k, (im, text, color) in enumerate(cells):
        x = M + k * (cw + M)
        page.paste(im if im.size == (cw, h) else fit(im, cw, h), (x, y))
        label(d, (x + 12, y + 8), text, F_L, color)
    if caption:
        label(d, (M + 12, y + h - 36), caption, F_S, GREY)
    return y + h + M


def metric_text(tag):
    v, h = metrics[tag]["vertical_edge"], metrics[tag]["horizontal_edge"]
    return (f"глубина {round(100 * (v['depth'] + h['depth']) / 2)} %, ширина {round((v['fwhm_texels'] + h['fwhm_texels']) / 2, 1)} "
            f"тексела, скат {round((v['ramp_10_90_texels'] + h['ramp_10_90_texels']) / 2, 1)} тексела, "
            f"{round(v['texels_per_stud'])} текс./стад")


BEFORE, AFTER = ("ДО · v1", RED), ("ПОСЛЕ · v2", GREEN)

# ── Лист 1: общий вид и кадр как в игре ─────────────────────────────────────────────────────────────────────────
page = Image.new("RGB", (W, 4000), BG)
d = ImageDraw.Draw(page)
d.text((M, 14), f"{title} — полировка: до и после", font=F_T, fill=GOLD)
d.text((M, 72), "Одинаковые камера, свет, фон и настройки рендера; поза покоя; кадры без обработки. Форма, части и "
       "точки вращения не менялись (вершины совпадают с v1).", font=F_S, fill=GREY)
y = 116
y = row(page, d, y, [(img("v1", "hero"), "ДО · v1 · три четверти", RED),
                     (img("v2", "hero"), "ПОСЛЕ · v2 · три четверти", GREEN)], 1150)
y = row(page, d, y, [(img("v1", "front"), "ДО · спереди", RED), (img("v2", "front"), "ПОСЛЕ · спереди", GREEN),
                     (img("v1", "back"), "ДО · сзади", RED), (img("v2", "back"), "ПОСЛЕ · сзади", GREEN)], 700)
# кадр телефона 844 × 390 — 1 : 1, и тот же кадр увеличен ×3 без сглаживания (видно настоящие пиксели)
gw = (W - 3 * M) // 2
for k, tag in enumerate(("v1", "v2")):
    text, color = (BEFORE, AFTER)[k]
    g = img(tag, "game")
    x = M + k * (gw + M)
    page.paste(fit(g, gw, round(gw * g.height / g.width)), (x, y))
    label(d, (x + 12, y + 8), f"{text} · как в игре: кадр телефона 844 × 390 (растянут под ячейку)", F_S, color)
y += round(gw * 390 / 844) + M
for k, tag in enumerate(("v1", "v2")):
    text, color = (BEFORE, AFTER)[k]
    crop = img(tag, "game").crop((370, 95, 550, 275))  # существо в кадре телефона, 180 × 180 → ×5
    x = M + k * (gw + M)
    page.paste(fit(crop, gw, 900, Image.NEAREST), (x, y))
    label(d, (x + 12, y + 8), f"{text} · тот же кадр, существо ×5 без сглаживания (пиксели экрана)", F_S, color)
y += 900 + M
page = page.crop((0, 0, W, y))
page.save(os.path.join(folder, f"{item}_polish_sheet.jpg"), quality=90)
print("ГОТОВО лист", page.size)

# ── Лист 2: детали ──────────────────────────────────────────────────────────────────────────────────────────────
page = Image.new("RGB", (W, 6000), BG)
d = ImageDraw.Draw(page)
d.text((M, 14), f"{title} — детали до и после", font=F_T, fill=GOLD)
d.text((M, 72), "Морда: A — без отметин, B — с отметинами (всё остальное в A и B одинаково). Контуры D39: замер по карте "
       "цвета поперёк линии квадрата на затылке.", font=F_S, fill=GREY)
y = 116
y = row(page, d, y, [(img("v1", "muzzle"), "исходная морда · v1", RED),
                     (img("v2nomarks", "muzzle"), "A · v2 без отметин", WHITE),
                     (img("v2", "muzzle"), "B · v2 с отметинами", GREEN)], 640)
y = row(page, d, y, [(img("v1", "face"), "ДО · лицо крупно", RED), (img("v2", "face"), "ПОСЛЕ · лицо крупно", GREEN)],
        900)
y0 = y
y = row(page, d, y, [(img("v1", "texture"), "ДО · контуры D39 крупно", RED),
                     (img("v2", "texture"), "ПОСЛЕ · контуры D39 крупно", GREEN)], 900)
cw = (W - 3 * M) // 2
label(d, (M + 12, y0 + 900 - 40), "v1: " + metric_text("v1"), F_S, WHITE)
label(d, (2 * M + cw + 12, y0 + 900 - 40), "v2: " + metric_text("v2"), F_S, WHITE)
y = row(page, d, y, [(img("v1", "cube"), "ДО · кубик", RED), (img("v2", "cube"), "ПОСЛЕ · кубик", GREEN),
                     (img("v1", "medal"), "ДО · медальон", RED), (img("v2", "medal"), "ПОСЛЕ · медальон", GREEN)], 560)
page = page.crop((0, 0, W, y))
page.save(os.path.join(folder, f"{item}_polish_details.jpg"), quality=90)
print("ГОТОВО детали", page.size)
