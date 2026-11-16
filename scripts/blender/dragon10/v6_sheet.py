"""Лист формы Короля-дракона v6: ракурсы, голова крупно, силуэты, сравнение с v5 одними камерами, проверка, числа.

  python scripts/blender/dragon10/v6_sheet.py   → assets/concepts/bosses_5_10/boss10_v6/v6_form.png
"""

import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss10_v6")
RAW = os.path.join(OUT, "raw")
BG, PANEL, INK, DIM, ACC = (22, 24, 33), (35, 38, 51), (240, 242, 248), (165, 170, 188), (255, 196, 64)


def font(size, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf", size)


def load(name):
    return Image.open(os.path.join(RAW, name)).convert("RGB")


def fit(im, w, h):
    k = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def contain(im, w, h, bg=(250, 250, 250)):
    k = min(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    out = Image.new("RGB", (w, h), bg)
    out.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    return out


def silhouette(name):
    im = Image.open(os.path.join(RAW, name)).convert("RGBA")
    a = im.split()[3].point(lambda v: 255 if v > 40 else 0)
    out = Image.new("RGB", im.size, (250, 250, 250))
    out.paste((10, 10, 14), mask=a)
    return out.crop(a.getbbox())


def para(d, x, y, text, width, size=21, fill=DIM, gap=5):
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


def label(d, x, y, text, dark=False):
    d.text((x, y), text, font=font(26, True), fill=(30, 30, 40) if dark else INK)


def main():
    st = json.load(open(os.path.join(RAW, "stats.json"), encoding="utf-8"))
    W = 2400
    sheet = Image.new("RGB", (W, 3600), BG)
    d = ImageDraw.Draw(sheet)
    d.rectangle((0, 0, W, 110), fill=PANEL)
    d.text((30, 12), "Король-дракон v6 — доработка формы: голова, шея и грудь, задние лапы", font=font(44, True),
           fill=INK)
    d.text((32, 70), "Один нейтральный материал; без короны, брони, мантии, скипетра и текстур. Blender, стиль D39. "
                     "Не загружалось в Roblox.", font=font(23), fill=DIM)
    y = 128
    T4 = 579
    for i, (v, t) in enumerate((("front", "Спереди"), ("side", "Сбоку"), ("back", "Сзади"), ("34", "3/4"))):
        x = 24 + i * (T4 + 12)
        sheet.paste(fit(load(f"v6_{v}.png"), T4, T4), (x, y))
        label(d, x + 12, y + T4 - 40, t)
    y += T4 + 16
    T3 = 776
    for i, (v, t) in enumerate((("v6_head_front.png", "Голова спереди"), ("v6_head_34.png", "Голова 3/4"))):
        x = 24 + i * (T3 + 12)
        sheet.paste(fit(load(v), T3, T3), (x, y))
        label(d, x + 12, y + T3 - 40, t)
    px = 24 + 2 * (T3 + 12)
    d.rectangle((px, y, W - 24, y + T3), fill=PANEL)
    yy = y + 16
    d.text((px + 18, yy), "Размеры и бюджет", font=font(28, True), fill=ACC)
    sm, ss = st["size_model"], st["size_studs"]
    for line in (f"Модель: {sm[0]} × {sm[1]} × {sm[2]} (ш × г × в, единицы).",
                 f"Масштаб экспорта {st['export_scale']} вместо 3 → {ss[0]} × {ss[1]} × {ss[2]} стада: высота с рогами "
                 f"ровно 35, пропорции не меняются.",
                 f"Размах крыльев {st['wingspan_studs']} стада при арене диаметром {st['arena_diameter']:.0f}: запас около "
                 f"{(st['arena_diameter'] - st['wingspan_studs']) / 2:.0f} стадов с каждой стороны; длина "
                 f"{ss[1]} стада тоже помещается.",
                 f"Треугольники: v6 — {st['tris']} (v5 — {st['tris_v5']}); бюджет игровой модели 8 000 — запас на "
                 f"королевские атрибуты и детали D39.",
                 "Хитбоксы, механика, арена и конфиг босса не менялись."):
        yy = para(d, px + 18, yy + 44 if line.startswith("Модель") else yy + 8, "• " + line, T3 - 40, size=21,
                  fill=INK)
    y += T3 + 16
    S = 470
    for i, (v, t) in enumerate((("v6_front_sil.png", "Силуэт спереди"), ("v6_side_sil.png", "Силуэт сбоку"),
                                ("v6_34_sil.png", "Силуэт 3/4"))):
        x = 24 + i * (T3 + 12)
        d.rectangle((x, y, x + T3, y + S), fill=(250, 250, 250))
        sheet.paste(contain(silhouette(v), T3 - 40, S - 70), (x + 20, y + 50))
        label(d, x + 14, y + 10, t, dark=True)
    y += S + 24
    d.text((30, y), "v5 → v6: те же камеры и масштаб", font=font(32, True), fill=INK)
    y += 50
    C = 386
    for i, (v5, v6, t) in enumerate((("v5_front.png", "v6_front.png", "спереди"), ("v5_side.png", "v6_side.png", "сбоку"),
                                     ("v5_head_front.png", "v6_head_front.png", "голова спереди"))):
        for j, (name, tag) in enumerate(((v5, "v5"), (v6, "v6"))):
            x = 24 + (i * 2 + j) * (C + 10)
            sheet.paste(fit(load(name), C, C), (x, y))
            label(d, x + 10, y + C - 38, f"{tag} — {t}")
    y += C + 24
    d.rectangle((24, y, W - 24, y + 760), fill=PANEL)
    yy = y + 16
    d.text((44, yy), "Самопроверка трёх областей", font=font(30, True), fill=ACC)
    yy += 48
    for line in ("Голова (главный приоритет). В v5 спереди — прямоугольник с прямоугольной пастью. В v6 каждый слой "
                 "головы — две скошенные половины: купол, череп и морда сужаются кверху, скулы раскрыты книзу, нижняя "
                 "челюсть сходится клином к подбородку, уголки пасти подняты в оскал, брови — «V», глаза утоплены в "
                 "глазницы между бровью и скулой и развёрнуты вперёд. Пасть: верхняя губа свисает над утопленным нёбом, "
                 "дно рта ниже бортиков нижней губы, челюсть раскрыта глубже; клыки — четыре пары (2 + 2 сверху и "
                 "снизу), а не россыпь шипов. Рога и агрессивное выражение сохранены.",
                 "Шея и грудь. Основание шеи — мышечный «мост» из ступенчатых профилей, он расходится в плечевой пояс "
                 "и грудь; сзади — мышца от шеи к холке. Механического стыка «труба в коробку» больше нет; шея не тоньше, "
                 "голова на той же высоте.",
                 "Задние лапы. Бедро крупнее и выше на крупе, коленная масса, икра за голенью, длинный скакательный "
                 "сустав со шпорой, плюсна вперёд, лапа шире с крупными когтями. Анатомия отличается от передних "
                 "(обратный сустав), все четыре лапы держат массу."):
        yy = para(d, 44, yy, "• " + line, W - 120, size=22, fill=INK) + 8
    d.text((44, yy + 6), "Риски для будущих анимаций", font=font(30, True), fill=ACC)
    yy += 54
    for line in ("Длинные рога идут назад над шеей: при сильном подъёме головы концы могут задеть спинные шипы шеи — "
                 "ограничить угол или укоротить верхние шипы.",
                 "Перепонка у бока: при складывании крыла внутренняя панель (крыло → бок) станет отдельной частью и "
                 "складывается с плечевой костью; возможны небольшие пересечения с боком в крайней позе.",
                 "Челюсть: широкие жевательные мышцы вращаются с челюстью — раскрытие до ~30° без пересечения со "
                 "скулами.",
                 "Шея — три части (низ, середина, верх) с точками вращения на стыках звеньев; мышечный «мост» остаётся "
                 "на корпусе, поэтому нижняя часть шеи поворачивается умеренно.",
                 "Передние лапы рядом с грудными мышцами: большой мах назад в шаге может задеть грудь — шаг короче или "
                 "грудь чуть уже в игровой копии. Асимметричная стойка — поза ожидания, риг строится в нейтральной позе."):
        yy = para(d, 44, yy, "• " + line, W - 120, size=21, fill=DIM) + 4
    end = max(yy, y) + 30
    sheet.crop((0, 0, W, end)).save(os.path.join(OUT, "v6_form.png"))
    print("DONE", end)


if __name__ == "__main__":
    main()
