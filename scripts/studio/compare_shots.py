# Лист сравнения (референс владельца и наши снимки): картинки одна под другой, одной ширины, с подписью над каждой.
# python scripts/studio/compare_shots.py out.jpg "Референс" ref.jpg "Сейчас (эмуляция телефона)" shot.png [...]
# Зависит от Pillow.
import sys

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1688


def font(size):
    for name in ("C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def main():
    out = sys.argv[1]
    pairs = [(sys.argv[i], sys.argv[i + 1]) for i in range(2, len(sys.argv), 2)]
    f = font(30)
    tiles = []
    for label, path in pairs:
        im = Image.open(path).convert("RGB")
        h = int(round(im.height * WIDTH / im.width))
        im = im.resize((WIDTH, h), Image.LANCZOS)
        tiles.append((label, im))
    bar = 48
    total = sum(bar + im.height for _, im in tiles) + 8 * (len(tiles) - 1)
    sheet = Image.new("RGB", (WIDTH, total), (24, 26, 32))
    d = ImageDraw.Draw(sheet)
    y = 0
    for label, im in tiles:
        d.text((14, y + 6), label, fill=(255, 255, 255), font=f)
        sheet.paste(im, (0, y + bar))
        y += bar + im.height + 8
    sheet.save(out, quality=92)
    print(sheet.size)


main()
