"""Лист Part-версии существ босса 3 (D55, этап D): у каждого из 30 — меш D54 с картой и блоки, из которых существо
собрано в игре до импорта (кадры scripts/blender/creature_parts.py). Пишет <папка>/creatures_parts.jpg.
Запуск: python scripts/d55_creature_sheets.py <рендеры> <папка>
Зависит от Pillow.
"""

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

RAW, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = json.load(open(os.path.join(REPO, "assets", "models", "art", "Boss3Creatures.index.json"), encoding="utf-8"))
REPORT = json.load(open(os.path.join(RAW, "report.json"), encoding="utf-8"))
FONT = "C:/Windows/Fonts/segoeuib.ttf"
BG = (32, 35, 44)
COLS, TW, TH = 5, 600, 347

items = [i for i in INDEX["items"] if os.path.exists(os.path.join(RAW, f"{i['id']}.png"))]
rows = (len(items) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * TW, 90 + rows * TH), BG)
d = ImageDraw.Draw(sheet)
d.text((24, 22), "Существа босса 3 — Part-версия в игре (слева меш D54, справа блоки ≤ 40; подставка скрыта, D54)",
       font=ImageFont.truetype(FONT, 40), fill=(255, 255, 255))
small = ImageFont.truetype(FONT, 22)
for k, item in enumerate(items):
    im = Image.open(os.path.join(RAW, f"{item['id']}.png")).convert("RGB").resize((TW, TH))
    x, y = (k % COLS) * TW, 90 + (k // COLS) * TH
    sheet.paste(im, (x, y))
    rep = REPORT.get(item["id"], {})
    d.text((x + 10, y + 8), f"{item['n']}. {item['name']} · {rep.get('blocks', '?')} бл.", font=small, fill=(255, 255, 255),
           stroke_width=2, stroke_fill=(20, 22, 28))
sheet.save(os.path.join(OUT, "creatures_parts.jpg"), quality=88)
print("SHEET_OK", len(items))
