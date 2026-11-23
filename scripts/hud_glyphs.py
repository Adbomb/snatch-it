# Свои плоские 2D-значки HUD (ТЗ владельца 2026-11-17: вид — по его референсу, без Blender): музей, солнце, луна с
# облаком. Рисуются векторно (Pillow, сглаживание — уменьшением в 4 раза), без обводки: чёрную обводку добавляет
# интерфейс (Shared/StudUI — UI.Glyph), как у белых силуэтов CheckUIIcons.
# Запуск: python scripts/hud_glyphs.py  →  assets/ui/hud/glyph_<имя>_256.png и лист glyphs_sheet.png.
import math
import os

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "ui", "hud")
SIZE = 256
K = 4  # сглаживание
WHITE = (255, 255, 255, 255)
YELLOW = (255, 214, 40, 255)
YELLOW_LIGHT = (255, 240, 130, 255)
CLOUD = (92, 98, 112, 255)
BLACK = (0, 0, 0, 255)


def canvas():
    return Image.new("RGBA", (SIZE * K, SIZE * K), (0, 0, 0, 0))


def s(v):
    return int(round(v * K))


def box(x0, y0, x1, y1):
    return [s(x0), s(y0), s(x1), s(y1)]


def finish(img, name):
    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    path = os.path.join(OUT, "glyph_%s_256.png" % name)
    img.save(path)
    return img


def museum():
    # крупные формы: значок рисуется высотой около 20 px — три колонны и одно основание читаются, мелкое сливается
    img = canvas()
    d = ImageDraw.Draw(img)
    d.polygon([(s(128), s(12)), (s(248), s(88)), (s(8), s(88))], fill=WHITE)  # фронтон
    d.rounded_rectangle(box(20, 96, 236, 122), radius=s(5), fill=WHITE)  # балка
    for cx in (62, 128, 194):  # колонны
        d.rounded_rectangle(box(cx - 20, 132, cx + 20, 200), radius=s(6), fill=WHITE)
    d.rounded_rectangle(box(8, 210, 248, 246), radius=s(7), fill=WHITE)  # основание
    return finish(img, "museum")


def sun():
    img = canvas()
    d = ImageDraw.Draw(img)
    c = 128
    for i in range(8):  # лучи — скруглённые клинья
        a = math.radians(i * 45 - 90)
        ax, ay = math.cos(a), math.sin(a)
        px, py = -ay, ax
        r0, r1, w = 76, 122, 17
        pts = [
            (c + ax * r0 + px * w, c + ay * r0 + py * w),
            (c + ax * r1, c + ay * r1),
            (c + ax * r0 - px * w, c + ay * r0 - py * w),
        ]
        d.polygon([(s(x), s(y)) for x, y in pts], fill=YELLOW)
    d.ellipse(box(c - 64, c - 64, c + 64, c + 64), fill=YELLOW)
    d.ellipse(box(c - 46, c - 50, c + 30, c + 26), fill=YELLOW_LIGHT)  # светлое пятно, как блик на референсе
    return finish(img, "sun")


def moon():
    img = canvas()
    # серп: большой круг минус сдвинутый круг
    disc = Image.new("L", img.size, 0)
    ImageDraw.Draw(disc).ellipse(box(22, 10, 190, 178), fill=255)
    cut = Image.new("L", img.size, 0)
    ImageDraw.Draw(cut).ellipse(box(84, -6, 232, 142), fill=255)
    crescent = Image.composite(Image.new("L", img.size, 0), disc, cut)
    img.paste(Image.new("RGBA", img.size, WHITE), (0, 0), crescent)
    # облака: силуэт из кругов; чёрная кайма отделяет их от серпа
    cloud = Image.new("L", img.size, 0)
    cd = ImageDraw.Draw(cloud)
    for x, y, r in ((118, 196, 38), (164, 176, 46), (208, 200, 34)):
        cd.ellipse(box(x - r, y - r, x + r, y + r), fill=255)
    cd.rounded_rectangle(box(92, 196, 236, 236), radius=s(18), fill=255)
    for x, y, r in ((196, 96, 22), (226, 104, 18)):  # малое облако справа
        cd.ellipse(box(x - r, y - r, x + r, y + r), fill=255)
    cd.rounded_rectangle(box(178, 100, 244, 124), radius=s(11), fill=255)
    rim = cloud.filter(ImageFilter.MaxFilter(s(9) | 1))
    alpha = img.getchannel("A")
    img.paste(Image.new("RGBA", img.size, BLACK), (0, 0), Image.composite(rim, Image.new("L", img.size, 0), alpha))
    img.paste(Image.new("RGBA", img.size, CLOUD), (0, 0), cloud)
    return finish(img, "moon")


def sheet(icons):
    # проверочный лист: значки на цветах кнопок референса, с обводкой, как её рисует интерфейс
    pad, cell = 24, 200
    bg = [(132, 255, 0), (2, 238, 255), (255, 179, 81), (253, 80, 84)]
    out = Image.new("RGB", (pad + len(icons) * (cell + pad), pad * 2 + cell), (40, 44, 52))
    for i, icon in enumerate(icons):
        x = pad + i * (cell + pad)
        tile = Image.new("RGBA", (cell, cell), bg[i % len(bg)] + (255,))
        small = icon.resize((150, 150), Image.LANCZOS)
        black = Image.new("RGBA", small.size, BLACK)
        for k in range(16):
            a = k / 16 * math.pi * 2
            tile.paste(black, (25 + int(round(math.cos(a) * 9)), 25 + int(round(math.sin(a) * 9))), small.getchannel("A"))
        tile.paste(small, (25, 25), small)
        out.paste(tile.convert("RGB"), (x, pad))
    out.save(os.path.join(OUT, "glyphs_sheet.png"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sheet([museum(), sun(), moon()])
    print("ok")
