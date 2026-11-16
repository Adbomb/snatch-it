"""Лист Короля-дракона v7 — королевское оформление: ракурсы, голова с короной, броня и мантия, скипетр,
силуэты, v6 → v7 одними камерами, палитра, атрибуты, числа, самопроверка, риски для анимаций.

  python scripts/blender/dragon10/v7_sheet.py   → assets/concepts/bosses_5_10/boss10_v7/v7_royal.png
Кадры и числа — из boss10_v7/raw/ (их делает v7_render.py).
"""

import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss10_v7")
RAW = os.path.join(OUT, "raw")
BG, PANEL, INK, DIM, ACC = (22, 24, 33), (35, 38, 51), (240, 242, 248), (165, 170, 188), (255, 196, 64)
W = 2400
M = 24  # поля


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


def para(d, x, y, text, width, size=21, fill=DIM, gap=5, bold=False):
    f = font(size, bold)
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
    f = font(26, True)
    if not dark:
        tw = d.textlength(text, font=f)
        d.rectangle((x - 8, y - 2, x + tw + 8, y + 34), fill=(22, 24, 33))
    d.text((x, y), text, font=f, fill=(30, 30, 40) if dark else INK)


def tiles(sheet, d, y, items, size, n, gap=12):
    """Ряд из n квадратных кадров; items = [(файл, подпись)]."""
    for i, (name, text) in enumerate(items):
        x = M + i * (size + gap)
        sheet.paste(fit(load(name), size, size), (x, y))
        label(d, x + 12, y + size - 44, text)
    return y + size + 16


PALETTE = (("scale", "Чешуя — королевский фиолетовый"), ("scaleD", "Брови, шипы, кости крыльев"),
           ("belly", "Живот, горло, губы — тёмная слива"), ("wing", "Перепонки — пурпур"),
           ("gold", "Броня и корона — золото"), ("goldD", "Золото: ступени и кант"), ("goldL", "Королевский знак"),
           ("neonCrystal", "Кристаллы — бирюза (свечение)"), ("neonEye", "Глаза — янтарь (свечение)"),
           ("ivory", "Рога, когти, клыки — слоновая кость"), ("mantle", "Мантия — алый (моё предложение)"),
           ("ermine", "Горностай"))


def main():
    st = json.load(open(os.path.join(RAW, "stats.json"), encoding="utf-8"))
    sheet = Image.new("RGB", (W, 7000), BG)
    d = ImageDraw.Draw(sheet)
    d.rectangle((0, 0, W, 110), fill=PANEL)
    d.text((30, 12), "Король-дракон v7 — королевское оформление утверждённой формы v6", font=font(44, True), fill=INK)
    d.text((32, 70), "Анатомия v6 без изменений (сверено по вершинам). Blender, стиль D39. В Roblox не загружалось, "
                     "DESIGN.md не менялся, коммита нет.", font=font(23), fill=DIM)
    y = 128
    y = tiles(sheet, d, y, (("v7_front.png", "1. Спереди"), ("v7_side.png", "2. Сбоку"), ("v7_back.png", "3. Сзади"),
                            ("v7_34.png", "4. 3/4")), 579, 4)
    y = tiles(sheet, d, y, (("v7_head_front.png", "5. Голова с короной — спереди"), ("v7_head_34.png", "5. Голова — 3/4"),
                            ("v7_head_side.png", "5. Голова — сбоку")), 776, 3)
    # броня, мантия, скипетр
    T3 = 776
    for i, (name, text) in enumerate((("v7_chest.png", "6. Нагрудник и броня"), ("v7_flank.png", "6. Мантия и броня сбоку"))):
        x = M + i * (T3 + 12)
        sheet.paste(fit(load(name), T3, T3), (x, y))
        label(d, x + 12, y + T3 - 44, text)
    sc = load("v7_scepter.png")
    x = M + 2 * (T3 + 12)
    sheet.paste(contain(sc, T3, T3, sc.getpixel((4, 4))), (x, y))
    label(d, x + 12, y + T3 - 44, "7. Скипетр отдельно")
    y += T3 + 16
    # силуэты
    S = 470
    for i, (name, text) in enumerate((("v7_front_sil.png", "8. Силуэт спереди"), ("v7_side_sil.png", "8. Силуэт сбоку"),
                                      ("v7_34_sil.png", "8. Силуэт 3/4"))):
        x = M + i * (T3 + 12)
        d.rectangle((x, y, x + T3, y + S), fill=(250, 250, 250))
        sheet.paste(contain(silhouette(name), T3 - 40, S - 70), (x + 20, y + 50))
        label(d, x + 14, y + 10, text, dark=True)
    y += S + 24
    # v6 → v7
    d.text((30, y), "9. v6 → v7: те же камеры и масштаб (v6 — утверждённая форма в глине)", font=font(32, True), fill=INK)
    y += 52
    C = 576
    pairs = (("v6_front.png", "v7_front.png", "спереди"), ("v6_side.png", "v7_side.png", "сбоку"),
             ("v6_34.png", "v7_34.png", "3/4"), ("v6_head_front.png", "v7_head_front.png", "голова"))
    for r in range(2):
        for c in range(2):
            v6, v7, t = pairs[r * 2 + c]
            for j, (name, tag) in enumerate(((v6, "v6"), (v7, "v7"))):
                x = M + (c * 2 + j) * (C + 12)
                sheet.paste(fit(load(name), C, C), (x, y))
                label(d, x + 10, y + C - 44, f"{tag} — {t}")
        y += C + 12
    y += 8
    # палитра, атрибуты, числа
    top = y
    col = (W - 2 * M - 24) // 3
    end = info(ImageDraw.Draw(Image.new("RGB", (W, 3000))), 0, st, col)
    d.rectangle((M, top, W - M, top + end + 20), fill=PANEL)
    info(d, top, st, col)
    y = top + end + 36
    top = y
    end = notes(ImageDraw.Draw(Image.new("RGB", (W, 4000))), 0)
    d.rectangle((M, top, W - M, top + end + 20), fill=PANEL)
    end = notes(d, top) + 30
    sheet.crop((0, 0, W, end)).save(os.path.join(OUT, "v7_royal.png"))
    print("DONE", end)


def info(d, top, st, col):
    """Палитра, атрибуты и числа в три колонки; возвращает низ самой длинной колонки (от top)."""
    px = M + 18
    d.text((px, top + 16), "Палитра (из ТЗ)", font=font(28, True), fill=ACC)
    yy = top + 64
    for k, text in PALETTE:
        code = st["palette"][k]
        d.rectangle((px, yy, px + 52, yy + 40), fill=tuple(int(code[i:i + 2], 16) for i in (0, 2, 4)),
                    outline=(90, 94, 110))
        d.text((px + 66, yy - 2), text, font=font(21), fill=INK)
        d.text((px + 66, yy + 22), "#" + code, font=font(16), fill=DIM)
        yy += 58
    yp = para(d, px, yy + 6, "Палитра работает: цвета насыщенные, золото и бирюза читаются на фиолетовом. "
                             "Альтернативу не готовил. Цвет мантии в ТЗ не задан — алый с горностаем; можно "
                             "показать другой.", col - 30, size=19)
    px = M + col + 30
    d.text((px, top + 16), "Королевские атрибуты", font=font(28, True), fill=ACC)
    yy = top + 64
    for line in ("Корона под голову дракона: обод из двух половин по верху бровей повторяет их «V»; ступенчатые "
                 "зубцы (средний выше), большой бирюзовый кристалл в оправе, малые камни. Перед основаниями рогов, "
                 "выше глаз; часть «Head».",
                 "Нагрудник-щит по наклону груди: три ступени, знак-корона, кристалл.",
                 "Наплечники над плечевым суставом, прижимают плечевую часть мантии.",
                 "Наручи на предплечьях, кольца на плюснах и ромбы на бёдрах задних лап, 4 сегмента вдоль хребта "
                 "между шипами, 2 кольца и камень у основания хвоста.",
                 "Мантия, короткая церемониальная: горностаевый воротник; плечевая часть с горностаевым краем; "
                 "шнур к золотой планке; по бокам по три полосы (MantleL1–3, MantleR1–3) со ступенчатым подолом, "
                 "золотой каймой и знаком. Висят ниже перепонки, между лапами.",
                 "Скипетр — отдельный объект, парит справа-спереди над магическим кругом с осколками; золотое "
                 "древко, когти держат кристалл, венец. Дракон его не держит."):
        yy = para(d, px, yy, "• " + line, col - 30, size=20, fill=INK) + 6
    ya = yy
    px = M + 2 * col + 42
    d.text((px, top + 16), "Числа", font=font(28, True), fill=ACC)
    sd, sv = st["size_dragon_studs"], st["size_v6_studs"]
    gt = st["group_tris"]
    mantle = sum(v for k, v in gt.items() if k.startswith("Mantle"))
    yy = top + 64
    for line in (f"Треугольники: дракон {st['tris']} + скипетр {st['tris_scepter']} = {st['tris_total']} из 8 000 "
                 f"(у формы v6 — {st['tris_v6']}).",
                 f"По частям рига: туловище {gt['Torso']}, голова с короной {gt['Head']}, челюсть {gt['Jaw']}, "
                 f"шея {gt['Neck']}, передние лапы по {gt['ForeLegL']}, задние по {gt['HindLegL']}, крылья по "
                 f"{gt['WingL']}, хвост {gt['Tail']}, полосы мантии {mantle}.",
                 f"Масштаб экспорта v6 ({st['export_scale']}) не менялся: {sd[0]} × {sd[1]} × {sd[2]} стада. "
                 f"Без короны высота {sv[2]}, как у v6; корона добавляет "
                 f"{round(sd[2] - sv[2], 1)} стада.",
                 f"Размах крыльев {st['wingspan_studs']} стада при арене диаметром {st['arena_diameter']:.0f}. "
                 f"Скипетр с кругом ({st['scepter_studs']} стада в высоту) не выходит за габарит крыльев.",
                 "Совпадающих граней 0, вывернутых 0, вырожденных 0.",
                 "В .blend — дракон (группы вершин по 17 частям рига) и скипетр отдельным объектом.",
                 "Хитбоксы, механика, баланс, анимации и конфиг не менялись."):
        yy = para(d, px, yy, "• " + line, col - 40, size=20, fill=INK) + 6
    return max(yy, ya, yp) - top


def notes(d, top):
    """Самопроверка и риски; возвращает низ текста."""
    yy = top + 16
    d.text((M + 20, yy), "Самопроверка: три круга рендеров", font=font(30, True), fill=ACC)
    yy += 50
    for line in ("Круг 1. Корона мелкая и пряталась за бровями → пересобрана: обод по бровям, высокие зубцы, крупный "
                 "кристалл. Нагрудник читался сумкой → щит по наклону груди. Мантию почти не было видно → полосы "
                 "с зазорами, отход подола и ступенчатый подол. Скипетр высоко над кругом → опущен.",
                 "Круг 2. Планка мантии задевала угол перепонки → опущена под него. Верх нагрудника уходил в горло → "
                 "опущен. Плечевая часть мантии добавлена под наплечник, наплечник вынесен наружу.",
                 "Круг 3. Два случая совпадающих граней (знак на полосе, горностаевый край) → исправлены, стало 0. "
                 "Кадры головы раздвинуты — корона целиком в кадре.",
                 "Пересечения (BVH, точные треугольники) — нет:",
                 "   – корона: с рогами, глазами, шипами бровей;",
                 "   – мантия: с крыльями, корнями крыльев, всеми лапами;",
                 "   – броня хребта: с шипами и крыльями;",
                 "   – скипетр: со всем драконом.",
                 "Задуманные касания:",
                 "   – обод короны лежит на бровях;",
                 "   – наплечник накрывает верх плеча лапы;",
                 "   – щит лежит на нижнем звене шеи, которое в v6 утоплено в грудь.",
                 "Минимальные зазоры (1 единица = 2,8 стада):",
                 "   – корона: до рогов 0,25, до глаз 0,36, до шипов бровей 0,2;",
                 "   – полосы мантии: до бедра 0,18, до перепонки 0,48;",
                 "   – планка мантии: до перепонки 0,23;",
                 "   – шнур мантии: до плеча лапы 0,12.",
                 "Статус читается без текста: корона с кристаллом, горностай, золотой щит со знаком, парящий "
                 "скипетр. Силуэт не потерян: анатомия v6 та же, на силуэтах добавились только корона и скипетр "
                 "рядом. Не перегружено: золото на груди, плечах и предплечьях, мелкие акценты сзади; крылья, шея "
                 "и морда чистые. Голова выразительна: корона выше бровей, «V» бровей продолжается в ободе, "
                 "глаза и клыки открыты.",
                 "Мантия не приклеена: полосы висят на планке и отходят от бока к подолу на 0,5. Слабое место: "
                 "спереди мантия читается только горностаевыми краями на плечах; полосы видны сбоку и в 3/4."):
        yy = para(d, M + 20, yy, ("" if line.startswith("   ") else "• ") + line, W - 2 * M - 60, size=21,
                  fill=INK) + 4
    d.text((M + 20, yy + 10), "Риски для анимаций (решать на этапе рига)", font=font(30, True), fill=ACC)
    yy += 60
    for line in ("Наплечники на туловище, верх плеча лапы под ними. Обычный шаг скрыт. Высокий замах лапой "
                 "прорежет низ наплечника → ограничить угол плеча или перенести наплечник в часть ForeLeg игровой копии.",
                 "Полосы мантии — отдельные части. При шаге задней лапы вперёд бедро подходит к задней полосе: "
                 "зазор 0,18. Нужен вторичный мах полос назад или меньший шаг.",
                 "Корона — часть головы, относительно рогов не двигается. При сильном подъёме головы зубцы "
                 "уходят назад: проверить с шипами шеи. Высота с короной 37 стадов вместо 35.",
                 "Складывание крыла: угол перепонки у бока в 0,23 над планкой мантии. Внутренняя панель должна "
                 "складываться с плечевой костью (как в v6), иначе заденет планку.",
                 "Шея проходит через воротник с заходом 0,05. Сильный поворот шеи вбок может проткнуть горностай → "
                 "поворот низа шеи умеренный (как в v6) или воротник в часть Neck.",
                 "Скипетр — отдельный объект, дочерний к дракону: покачивание и вращение в воздухе без касаний. "
                 "Анимацию призыва — по отдельному решению."):
        yy = para(d, M + 20, yy, "• " + line, W - 2 * M - 60, size=21, fill=DIM) + 4
    return yy


if __name__ == "__main__":
    main()
