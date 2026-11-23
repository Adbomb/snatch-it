# Вырезать вид игры из снимка окна Studio (scripts/studio/window.ps1 -Action shot): ищет синюю рамку вокруг вида
# в Play. Использование: python scripts/studio/crop_view.py in.png out.png [zoom] [x0 y0 x1 y1 — область внутри вида]
# Печатает прямоугольник вида в снимке и размер результата. Зависит от Pillow.
import sys

from PIL import Image


def viewport(im):
    px = im.convert("RGB").load()
    w, h = im.size

    def blue(x, y):
        r, g, b = px[x, y]
        return b > 200 and r < 110 and 70 < g < 170

    # левая граница рамки: столбец, где много синих пикселей подряд
    best = None
    for x in range(0, min(40, w)):
        run, top, cur = 0, None, None
        for y in range(h):
            if blue(x, y):
                if cur is None:
                    cur = y
                if y - cur + 1 > run:
                    run, top = y - cur + 1, cur
            else:
                cur = None
        if run > 150:
            best = (x, top, top + run - 1)
            break
    if not best:
        return None
    x0, y0, y1 = best
    # правая граница: по верхней линии рамки
    x1 = x0
    for x in range(x0, w):
        if blue(x, y0 + 1) or blue(x, y0):
            x1 = x
        elif x - x1 > 4:
            break
    return (x0 + 2, y0 + 2, x1 - 1, y1 - 1)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    zoom = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    im = Image.open(src)
    box = viewport(im)
    if not box:
        print("рамка вида не найдена")
        sys.exit(1)
    view = im.crop(box)
    if len(sys.argv) > 7:
        view = view.crop(tuple(int(v) for v in sys.argv[4:8]))
    if zoom != 1.0:
        view = view.resize((int(view.width * zoom), int(view.height * zoom)), Image.LANCZOS)
    view.save(dst)
    print(box, view.size)


main()
