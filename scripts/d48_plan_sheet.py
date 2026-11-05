"""D48, этап A — план двух этажей с размерами (по рендерам сверху из scripts/blender/d48_museum_concept.py).

Рендеры 11_plan_upper / 12_plan_vault: 1100², орто 58 стадов, центр — точка участка (x 0, z 4), вход (−z) внизу,
+x участка — слева (как видит игрок, стоящий лицом к музею). Подписи — Montserrat из Roblox Studio.
Запуск: python scripts/d48_plan_sheet.py → assets/concepts/d48/renders/plan_dimensions.png
"""

import glob
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "assets", "concepts", "d48", "renders")
SIZE, ORTHO, CZ = 1100, 58.0, 4.0
K = SIZE / ORTHO
INK = (24, 20, 46)


def font(weight, size):
    for p in sorted(glob.glob(os.path.expandvars(rf"%LOCALAPPDATA%\Roblox\Versions\*\content\fonts\Montserrat-{weight}.ttf"))):
        path = p
    return ImageFont.truetype(path, size)


def px(x, z):
    return SIZE / 2 - x * K, SIZE / 2 - (z - CZ) * K


def say(d, xy, body, size=26, fill=(255, 255, 255), anchor="mm", weight="Black"):
    d.text(xy, body, font=font(weight, size), fill=fill, stroke_width=max(2, size // 8), stroke_fill=INK, anchor=anchor)


def dim(d, a, b, body, offset=(0, 0), size=22):
    (x0, y0), (x1, y1) = a, b
    d.line([a, b], fill=(255, 236, 140), width=4)
    for (x, y) in (a, b):
        if abs(x1 - x0) > abs(y1 - y0):
            d.line([(x, y - 12), (x, y + 12)], fill=(255, 236, 140), width=4)
        else:
            d.line([(x - 12, y), (x + 12, y)], fill=(255, 236, 140), width=4)
    say(d, ((x0 + x1) / 2 + offset[0], (y0 + y1) / 2 + offset[1]), body, size, (255, 236, 140))


upper = Image.open(os.path.join(R, "11_plan_upper.png")).convert("RGB")
vault = Image.open(os.path.join(R, "12_plan_vault.png")).convert("RGB")
du, dv = ImageDraw.Draw(upper), ImageDraw.Draw(vault)

# верхний этаж
say(du, (SIZE / 2, 40), "ВЕРХНИЙ ЭТАЖ — ВЫСТАВОЧНЫЙ ЗАЛ", 34)
dim(du, px(18, 25.5), px(-18, 25.5), "36 ст.", (0, -26))
dim(du, px(19.6, -12.7), px(19.6, 20.7), "33,4 ст.", (-62, 0))
say(du, px(0, -19.5), "ВХОД · портик", 24)
say(du, px(0, 13.6), "ЛЕСТНИЦА ВНИЗ", 22)
say(du, px(0, 11.4), "11 × 11,3", 20, (255, 236, 140), weight="Bold")
say(du, px(-12, -6.2), "сундук", 20, weight="Bold")
say(du, px(11.0, 8.2), "постамент 5×5", 20, weight="Bold")
say(du, px(0, -2.6), "проход 6,4", 20, weight="Bold")
say(du, px(-6.8, -9.8), "место защиты", 18, (140, 230, 255), weight="Bold")
say(du, px(0, 6.9), "лазер", 18, (255, 120, 120), weight="Bold")
say(du, px(-20.5, 21.2), "участок 44 × 44", 20, (255, 255, 255), "rb", "Bold")

# подземный этаж
say(dv, (SIZE / 2, 40), "ПОДЗЕМНЫЙ ЭТАЖ — ХРАНИЛИЩЕ", 34)
dim(dv, px(16.6, 25.5), px(-16.6, 25.5), "33,2 ст. (внутри)", (0, -26))
dim(dv, px(19.4, -11.3), px(19.4, 19.3), "30,6 ст.", (-62, 0))
say(dv, px(0, -6.2), "СЕЙФ", 26)
say(dv, px(-4.5, 4.0), "терминал инвентаря", 20, weight="Bold")
say(dv, px(11.5, -7.6), "центр безопасности", 20, weight="Bold")
say(dv, px(-14.0, 14.5), "стеллажи", 20, weight="Bold")
say(dv, px(0, 15.0), "лестница: 2 марша", 20, weight="Bold")
say(dv, px(0, 12.8), "13 ступ. × 1 ст.", 18, (255, 236, 140), weight="Bold")
say(dv, px(-20.5, 21.2), "высота 11,6 ст.", 20, (255, 255, 255), "rb", "Bold")

sheet = Image.new("RGB", (SIZE * 2 + 30, SIZE + 150), (24, 28, 48))
sheet.paste(upper, (0, 150))
sheet.paste(vault, (SIZE + 30, 150))
d = ImageDraw.Draw(sheet)
say(d, (sheet.width // 2, 52), "D48 — план музея на участке (1 стад = 1 клетка Roblox)", 40)
say(d, (sheet.width // 2, 108), "Внешний контур как у нынешнего здания (36 × 33,4 + портик); хранилище — под залом, "
                                "лестница внутри; соседние участки не задеты (шаг 75 ст.)", 24, (200, 214, 255),
    weight="Bold")
sheet = sheet.resize((sheet.width * 3 // 4, sheet.height * 3 // 4), Image.LANCZOS)
sheet.save(os.path.join(R, "plan_dimensions.png"))
print("ok", sheet.size)
