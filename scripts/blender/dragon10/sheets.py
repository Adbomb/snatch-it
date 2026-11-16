"""Листы эталона Короля-дракона v2 из кадров render.py (обычный Python + Pillow).

  python scripts/blender/dragon10/sheets.py

Пишет в assets/concepts/bosses_5_10/boss10_v2/: 1_clay.png, 2_color.png, 3_details.png, 4_old_vs_new.png,
5_game_copy.png.
"""

import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss10_v2")
RAW = os.path.join(OUT, "raw")
OLD = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "raw", "boss_10")
BG, PANEL, INK, DIM, ACC = (22, 24, 33), (35, 38, 51), (240, 242, 248), (165, 170, 188), (255, 196, 64)


def font(size, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf", size)


def fit(path, w, h):
    im = Image.open(path).convert("RGB")
    k = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def sheet(W, H, title, sub):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 100), fill=PANEL)
    d.text((30, 12), title, font=font(44, True), fill=INK)
    d.text((32, 66), sub, font=font(22), fill=DIM)
    return im, d


def tiles(im, d, items, x0, y0, w, h, gap=12, cols=None):
    cols = cols or len(items)
    for i, (path, label) in enumerate(items):
        x, y = x0 + (i % cols) * (w + gap), y0 + (i // cols) * (h + 56)
        im.paste(fit(path, w, h), (x, y))
        d.text((x + 4, y + h + 10), label, font=font(24, True), fill=INK)


def wrap(d, text, f, width):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= width:
            cur = t
        else:
            out.append(cur)
            cur = w
    return out + ([cur] if cur else [])


def para(d, x, y, text, width, size=22, fill=DIM, gap=5):
    f = font(size)
    for line in wrap(d, text, f, width):
        d.text((x, y), line, font=f, fill=fill)
        y += size + gap
    return y


def main():
    hero = json.load(open(os.path.join(RAW, "stats.json")))
    game = json.load(open(os.path.join(RAW, "stats_game.json")))
    views = [("front", "Спереди"), ("side", "Сбоку"), ("back", "Сзади"), ("34", "3/4")]

    im, d = sheet(2400, 780, "Король-дракон v2 — без текстур",
                  "Однотонный материал: силуэт, пропорции, анатомия и крупные формы. Блок-аут Blender, не загружалось в Roblox.")
    tiles(im, d, [(os.path.join(RAW, f"clay_{k}.png"), t) for k, t in views], 24, 120, 579, 579)
    im.save(os.path.join(OUT, "1_clay.png"))

    im, d = sheet(2400, 780, "Король-дракон v2 — цвет и материалы",
                  "Чешуя с рельефом (процедурно, для игры запекается в карты), золото с тёмной кромкой D39, бархатная мантия.")
    tiles(im, d, [(os.path.join(RAW, f"color_{k}.png"), t) for k, t in views], 24, 120, 579, 579)
    im.save(os.path.join(OUT, "2_color.png"))

    im, d = sheet(2400, 1800, "Король-дракон v2 — крупные планы",
                  "Морда и корона, броня, крыло, хвост.")
    det = [("close_head", "Морда: надбровья, глаз с зрачком, ноздри, клыки"), ("close_crown", "Корона: обод, зубцы, камни, дуги"),
           ("close_armor", "Броня: нагрудник, наплечники, пояс"), ("close_wing", "Крыло: кости и перепонки"),
           ("close_tail", "Хвост: сегменты, шипы, лезвие")]
    for i, (k, t) in enumerate(det):
        x, y = 24 + (i % 3) * 788, 120 + (i // 3) * 838
        im.paste(fit(os.path.join(RAW, f"{k}.png"), 776, 776), (x, y))
        para(d, x + 4, y + 784, t, 770, size=24, fill=INK)
    im.save(os.path.join(OUT, "3_details.png"))

    im, d = sheet(2400, 1150, "Было → стало: Король-дракон v1 (блок-аут) и v2 (новая геометрия)",
                  f"v1 — стопки восьмигранников и одна сетка плиток; v2 — свои сетки: лофт сечений, оболочки брони, "
                  f"ступенчатые купола. Треугольников: концепт {hero['triangles']}, игровая копия {game['triangles']}.")
    pairs = [(os.path.join(OLD, "boss10_front.png"), "v1 спереди"), (os.path.join(RAW, "color_front.png"), "v2 спереди"),
             (os.path.join(OLD, "boss10_hero.png"), "v1 3/4"), (os.path.join(RAW, "color_34.png"), "v2 3/4")]
    tiles(im, d, pairs, 24, 120, 579, 579)
    y = 770
    for line in ("Голова: крупнее (×1.14), лофт черепа и отдельная челюсть; тяжёлые надбровья, миндалевидный светящийся "
                 "глаз с вертикальным зрачком и веком, ноздри, клыки, гребни; рога сужаются и изгибаются, с золотыми кольцами.",
                 "Корона: ступенчатый обод, зубцы-лилии с огранёнными камнями в оправах, бархатная шапка, дуги, держава.",
                 "Тело: V-силуэт (грудь 2.08, талия 1.08), нагрудник из двух грудных пластин с килем, колонна брюшных щитков, "
                 "пояс с пряжкой и набедренники; ступенчатые наплечники и наколенники; пальцеходящие ноги, живая стойка.",
                 "Крылья: кости-трубы с суставами, четыре пальца, перепонки с прогибом и вырезами; не закрывают фигуру.",
                 "Хвост: ступенчатые сегменты с сужением, золотые шипы-лезвия, наконечник с килем и рубинами.",
                 "Мантия: складки, золотая кайма, горностаевый воротник, цепь с застёжками, герб на спине."):
        y = para(d, 34, y, "• " + line, 2330, size=23, fill=INK) + 6
    im.save(os.path.join(OUT, "4_old_vs_new.png"))

    im, d = sheet(2400, 1120, "Игровая копия: те же формы, ≤ 8 000 треугольников",
                  "Из того же кода с меньшим числом граней (сечения, обод короны, ряды пластин, мантия, камни).")
    tiles(im, d, [(os.path.join(RAW, "color_34.png"), f"Концепт: {hero['triangles']} тр."),
                  (os.path.join(RAW, "game_34.png"), f"Игровая копия: {game['triangles']} тр."),
                  (os.path.join(RAW, "close_head.png"), "Концепт: морда"),
                  (os.path.join(RAW, "game_head.png"), "Игровая копия: морда")], 24, 120, 579, 579)
    d.rectangle((24, 760, 2376, 1096), fill=PANEL)
    d.text((44, 772), f"Части (будущие MeshPart на Motor6D): {game['parts']} — треугольники концепт / игра",
           font=font(26, True), fill=INK)
    names = sorted(game["per_part"], key=lambda n: -hero["per_part"][n])
    for i, n in enumerate(names):
        x, y = 44 + (i // 7) * 580, 818 + (i % 7) * 38
        d.text((x, y), f"{n:<10}  {hero['per_part'][n]:>5} / {game['per_part'][n]:>5}", font=font(22), fill=DIM)
    im.save(os.path.join(OUT, "5_game_copy.png"))
    print("DONE")


if __name__ == "__main__":
    main()
