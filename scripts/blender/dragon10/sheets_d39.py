"""Листы Короля-дракона v3 (стиль D39) из кадров render_d39.py (обычный Python + Pillow).

  python scripts/blender/dragon10/sheets_d39.py

Пишет в assets/concepts/bosses_5_10/boss10_v3/: 1_clay.png, 2_color.png, 3_details.png, 4_style_and_old.png,
5_game_copy.png.
"""

import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss10_v3")
RAW = os.path.join(OUT, "raw")
OLD = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "raw", "boss_10")
SPHINX = os.path.join(REPO, "assets", "concepts", "boss4", "sphinx_v2")
BG, PANEL, INK, DIM = (22, 24, 33), (35, 38, 51), (240, 242, 248), (165, 170, 188)
NOTE = "Стиль D39, как Сфинкс. Блок-аут Blender, кольца D39 процедурные (для игры запекаются). Не загружалось в Roblox."


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


def para(d, x, y, text, width, size=22, fill=DIM, gap=5):
    f = font(size)
    line = ""
    for word in text.split():
        t = (line + " " + word).strip()
        if d.textlength(t, font=f) <= width:
            line = t
        else:
            d.text((x, y), line, font=f, fill=fill)
            y += size + gap
            line = word
    if line:
        d.text((x, y), line, font=f, fill=fill)
        y += size + gap
    return y


def main():
    hero = json.load(open(os.path.join(RAW, "stats.json"), encoding="utf-8"))
    game = json.load(open(os.path.join(RAW, "stats_game.json"), encoding="utf-8"))
    views = [("front", "Спереди"), ("side", "Сбоку"), ("back", "Сзади"), ("34", "3/4")]

    im, d = sheet(2400, 780, "Король-дракон v3 — без текстур", "Однотонно: силуэт ступенями, пропорции, крупные блоки. " + NOTE)
    tiles(im, d, [(os.path.join(RAW, f"clay_{k}.png"), t) for k, t in views], 24, 120, 579, 579)
    im.save(os.path.join(OUT, "1_clay.png"))

    im, d = sheet(2400, 780, "Король-дракон v3 — цвет и квадраты D39", NOTE)
    tiles(im, d, [(os.path.join(RAW, f"color_{k}.png"), t) for k, t in views], 24, 120, 579, 579)
    im.save(os.path.join(OUT, "2_color.png"))

    im, d = sheet(2400, 1800, "Король-дракон v3 — крупные планы", NOTE)
    det = [("close_head", "Морда: брови-бруски, глаза с зрачком и бликом, площадка носа, клыки"),
           ("close_crown", "Корона: обод с кантами, зубцы с камнями, шапка, дуги, держава"),
           ("close_armor", "Броня: нагрудник ступенью с килем, медальоны, пояс, щитки"),
           ("close_wing", "Крыло и мантия: кости, панели перепонки, складки, герб"),
           ("close_tail", "Хвост: звенья с кантами, золотые шипы, лезвие с рубинами")]
    for i, (k, t) in enumerate(det):
        x, y = 24 + (i % 3) * 788, 120 + (i // 3) * 838
        im.paste(fit(os.path.join(RAW, f"{k}.png"), 776, 776), (x, y))
        para(d, x + 4, y + 784, t, 770, size=24, fill=INK)
    im.save(os.path.join(OUT, "3_details.png"))

    im, d = sheet(2400, 1180, "Стиль: Сфинкс (эталон D39) — дракон v3; было → стало",
                  f"Треугольников: концепт {hero['tris']}, игровая копия {game['tris']}; совпадающих граней "
                  f"{len(hero['coplanar'])}, вывернутых {hero['flipped']}.")
    tiles(im, d, [(os.path.join(SPHINX, "sphinx_hero_stand.jpg"), "Сфинкс — эталон D39"),
                  (os.path.join(RAW, "color_34.png"), "Дракон v3 — 3/4"),
                  (os.path.join(OLD, "boss10_hero.png"), "Было: дракон v1 — 3/4"),
                  (os.path.join(RAW, "color_front.png"), "Дракон v3 — спереди")], 24, 120, 579, 579)
    y = 770
    for line in ("Как у Сфинкса: блоки квадратного сечения с острыми рёбрами (фаска 0.012), силуэт ступенями, чистые "
                 "яркие цвета; квадраты-контуры D39 одного масштаба на крупных цветах, мелкие накладки гладкие; без "
                 "гладких скруглённых форм.",
                 "Приёмы Сфинкса: слои наплечников и щитков полосами, тёмные канты под краями, медальоны «золото — кант "
                 "— камень — блик», лицо из плоских накладок (белок, радужка, вертикальный зрачок, блик, ресница), "
                 "тяжёлые брови-бруски.",
                 "Против v1: голова крупнее (×1.15) с мордой, носом и клыками; корона — обод с кантами, зубцы с "
                 "камнями, шапка, дуги, держава; грудь шире живота, нагрудник ступенью с килем; пальцеходящие ноги "
                 "с желобками; хвост звеньями; крылья из панелей; мантия складками с гербом; гребень на затылке."):
        y = para(d, 34, y, "• " + line, 2330, size=23, fill=INK) + 8
    im.save(os.path.join(OUT, "4_style_and_old.png"))

    im, d = sheet(2400, 1120, "Игровая копия: те же блоки, ≤ 8 000 треугольников",
                  "Фаска остаётся на крупных блоках; у мелких деталей (< 0.7) её нет — с игровой дистанции не видно; "
                  "мантия 7 → 5 складок.")
    tiles(im, d, [(os.path.join(RAW, "color_34.png"), f"Концепт: {hero['tris']} тр."),
                  (os.path.join(RAW, "game_34.png"), f"Игровая копия: {game['tris']} тр."),
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
