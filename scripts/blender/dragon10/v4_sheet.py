"""Сравнительный лист силуэтов Короля-дракона v4 (этап A): три варианта, один масштаб, силуэты, разбор.

  python scripts/blender/dragon10/v4_sheet.py   → assets/concepts/bosses_5_10/boss10_v4/v4_silhouettes.png
"""

import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss10_v4")
RAW = os.path.join(OUT, "raw")
BG, PANEL, INK, DIM, ACC = (22, 24, 33), (35, 38, 51), (240, 242, 248), (165, 170, 188), (255, 196, 64)

INFO = {
    "A": ("Титан", "Четвероногий тяжеловес. Огромная голова на короткой толстой шее, высокая холка с лопатками, "
                   "низкая широкая стойка, лапы с локтями врозь, тяжёлый хвост с булавой, крылья полуподняты над "
                   "холкой. Силуэт горизонтальный, главный акцент — голова с бычьими рогами."),
    "B": ("Владыка", "Сидит по-королевски на задних лапах. Прямые передние лапы, грудь колесом, длинная толстая "
                     "S-образная шея, голова смотрит сверху вниз, длинные рога дугой назад, широко раскрытые крылья, "
                     "хвост обвивает передние лапы. Силуэт вертикальный и самый изящный."),
    "C": ("Император", "Стоит на задних пальцеходящих лапах в хищной стойке. V-силуэт: огромные плечи и грудь, узкий "
                       "таз; мощные лапы с когтями выставлены вперёд; широкая голова с костяным венцом из рогов — "
                       "корона заложена в анатомию; крылья сложены вдоль спины как плащ; хвост — противовес."),
}
REVIEW = {
    "A": ["Дракон? Да: четыре лапы, крылья, рога, хвост — с первого взгляда.",
          "Финальный босс? Да: самая большая масса и самая крупная голова.",
          "Не Roblox-персонаж? Да: звериная четвероногая стойка.",
          "Без текстур: цельный тяжёлый силуэт; спереди морда пока «коробом».",
          "Гармония: голова, лапы и булава согласованы; крылья можно крупнее.",
          "Перекрытия: голову не закрывает ничего; в 3/4 крыло частично за головой."],
    "B": ["Дракон? Да: классический силуэт — шея, рога, раскрытые крылья.",
          "Финальный босс? Величие за счёт роста и размаха крыльев, массы меньше.",
          "Не Roblox-персонаж? Да: сидящая звериная посадка.",
          "Без текстур: самый изящный силуэт; спереди шея читается столбом.",
          "Гармония: голова маловата для таких крыльев — увеличить при доработке.",
          "Перекрытия: крылья не закрывают голову; хвост вокруг лап читается."],
    "C": ["Дракон? Да: венец рогов, крылья-плащ, хвост, звериные лапы.",
          "Финальный босс? Да: самые властные плечи и «корона» из рогов.",
          "Не Roblox-персонаж? Сбоку и в 3/4 — хищная стойка; спереди двуногая "
          "фигура ближе всех к человеческой — главный риск варианта.",
          "Без текстур: сильный V-силуэт; задние лапы коротковаты для корпуса.",
          "Гармония: тяжёлый верх уравновешен хвостом; лапы стоит удлинить.",
          "Перекрытия: сложенные крылья не закрывают голову и грудь."],
}


def font(size, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf", size)


def fit(im, w, h):
    k = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def silhouette(path):
    im = Image.open(path).convert("RGBA")
    a = im.split()[3].point(lambda v: 255 if v > 40 else 0)
    out = Image.new("RGB", im.size, (250, 250, 250))
    out.paste((10, 10, 14), mask=a)
    return out


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
    st = json.load(open(os.path.join(RAW, "stats.json"), encoding="utf-8"))
    W, H = 2400, 4300
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.rectangle((0, 0, W, 110), fill=PANEL)
    d.text((30, 12), "Король-дракон v4 — три силуэта на выбор (этап A)", font=font(46, True), fill=INK)
    d.text((32, 72), "Один нейтральный материал, без брони и украшений; одинаковые свет, масштаб и ракурсы. "
                     "Блок-ауты Blender, не загружались в Roblox.", font=font(23), fill=DIM)
    y = 130
    T = 640
    for k in "ABC":
        name, text = INFO[k]
        size = st[k]["size"]
        d.rectangle((24, y, 24 + 404, y + T), fill=PANEL)
        d.text((44, y + 14), k, font=font(90, True), fill=ACC)
        d.text((120, y + 40), name, font=font(44, True), fill=INK)
        yy = para(d, 44, y + 130, text, 368, size=22, fill=DIM)
        yy = para(d, 44, yy + 12, f"Габарит модели {size[0]} × {size[1]} × {size[2]}; в игре ×3 ≈ "
                                  f"{size[0] * 3:.0f} × {size[1] * 3:.0f} × {size[2] * 3:.0f} стадов. "
                                  f"Блок-аут: {st[k]['tris']} треугольников.", 368, size=20, fill=INK)
        for i, (v, label) in enumerate((("front", "спереди"), ("side", "сбоку"), ("34", "3/4"))):
            x = 440 + i * (T + 12)
            sheet.paste(fit(Image.open(os.path.join(RAW, f"{k}_{v}.png")).convert("RGB"), T, T), (x, y))
            d.text((x + 12, y + T - 40), f"{k} — {label}", font=font(26, True), fill=INK)
        y += T + 20
    # все три рядом
    d.text((30, y + 4), "Все три рядом, один масштаб", font=font(32, True), fill=INK)
    y += 52
    for i, v in enumerate(("34", "front")):
        im = Image.open(os.path.join(RAW, f"lineup_{v}.png")).convert("RGB")
        sheet.paste(fit(im, 1170, 488), (24 + i * 1182, y))
    y += 500
    # силуэты
    d.text((30, y + 4), "Силуэты без внутренней детализации", font=font(32, True), fill=INK)
    y += 52
    cell = 254
    for j, k in enumerate("ABC"):
        for i, v in enumerate(("front", "side", "34")):
            x = 24 + (j * 3 + i) * (cell + 9)
            sheet.paste(fit(silhouette(os.path.join(RAW, f"{k}_{v}_sil.png")), cell, cell), (x, y))
            d.text((x + 8, y + 6), f"{k} {('спереди', 'сбоку', '3/4')[i]}", font=font(20, True), fill=(30, 30, 40))
    y += cell + 24
    # различия и самопроверка
    d.rectangle((24, y, W - 24, H - 24), fill=PANEL)
    d.text((44, y + 14), "Принципиальные различия", font=font(32, True), fill=INK)
    yy = y + 64
    for line in ("A — горизонтальный четвероногий тяжеловес: вся сила в голове, груди и лапах; крылья — второй план.",
                 "B — вертикальная сидящая фигура: величие через рост, длинную шею, рога и самый широкий размах крыльев.",
                 "C — двуногая хищная стойка: власть через плечи и «корону» из рогов, крылья сложены плащом; "
                 "ближе всех к будущей мантии и броне, но спереди ближе всех к человеческой фигуре.",
                 "Риг: A и B — четвероногие (как Сфинкс), C — двуногий, ближе к ригу v3. Хитбоксы и характеристики "
                 "не меняются. Блок-ауты ~2 000 треугольников: до бюджета 8 000 большой запас на детали D39."):
        yy = para(d, 44, yy, "• " + line, W - 120, size=23, fill=INK) + 4
    yy += 14
    d.text((44, yy), "Самопроверка (6 вопросов ТЗ)", font=font(32, True), fill=INK)
    yy += 52
    colw = (W - 88) // 3
    top = yy
    bottom = top
    for j, k in enumerate("ABC"):
        x = 44 + j * colw
        d.text((x, top), f"{k} — {INFO[k][0]}", font=font(26, True), fill=ACC)
        ty = top + 40
        for n, line in enumerate(REVIEW[k], 1):
            ty = para(d, x, ty, f"{n}. {line}", colw - 30, size=20, fill=DIM, gap=4) + 6
        bottom = max(bottom, ty)
    end = bottom + 30
    d.rectangle((0, end, W, H), fill=BG)
    sheet.crop((0, 0, W, end + 24)).save(os.path.join(OUT, "v4_silhouettes.png"))
    print("DONE")


if __name__ == "__main__":
    main()
