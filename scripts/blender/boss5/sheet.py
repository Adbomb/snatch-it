"""Листы концепта босса 5 «Ледник» (шаг 1 D64): босс, арена, ледяная коллекция — для утверждения владельцем.

  python scripts/blender/boss5/sheet.py
  → assets/concepts/bosses_5_10/boss5_v2/{1_boss,2_arena,3_collection}.png (вне git)
Кадры и числа — из boss5_v2/raw/ (render.py, arena.py, creature_render.py). Оформление — как лист дракона v7.
"""

import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))  # scripts/blender
import stand_colors as SC  # noqa: E402  (D71: цвета редкостей из UITokens)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "dragon10"))
import v7_sheet as V  # noqa: E402  (font, fit, para, label, silhouette — общие помощники листов)

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss5_v2")
RAW = os.path.join(OUT, "raw")
V.RAW = RAW
BG, PANEL, INK, DIM, ACC = V.BG, V.PANEL, V.INK, V.DIM, V.ACC
W, M = 2400, 24
RARITY = {k: SC.rgb(SC.RARITY[k][1]) for k in ("Common", "Rare", "Epic", "Legendary")}  # D71: из UITokens
RARITY_RU = {"Common": "Обычное", "Rare": "Редкое", "Epic": "Эпическое", "Legendary": "Легендарное"}


def header(d, title, sub):
    d.rectangle((0, 0, W, 110), fill=PANEL)
    d.text((30, 12), title, font=V.font(44, True), fill=INK)
    d.text((32, 70), sub, font=V.font(23), fill=DIM)


def tiles(sheet, d, y, items, size, gap=12):
    for i, (name, text) in enumerate(items):
        x = M + i * (size + gap)
        sheet.paste(V.fit(V.load(name), size, size), (x, y))
        V.label(d, x + 12, y + size - 44, text)
    return y + size + 16


def panel(d, x, y, w, title, lines, size=21):
    """Текстовая панель: заголовок и пункты; возвращает нижний край."""
    y0 = y
    d.text((x + 18, y + 12), title, font=V.font(28, True), fill=ACC)
    y += 58
    for ln in lines:
        y = V.para(d, x + 18, y, ln, w - 36, size=size, fill=INK if ln.startswith("•") else DIM) + 4
    return y0, y + 12


def boss():
    st = json.load(open(os.path.join(RAW, "stats.json"), encoding="utf-8"))
    sheet = Image.new("RGB", (W, 6000), BG)
    d = ImageDraw.Draw(sheet)
    header(d, "Босс 5 · Ледник — Йети-коллекционер",
           "Концепт шага 1 (D64): Blender, стиль D39, одна модель в четырёх позах. В Roblox не загружалось; "
           "правила боя, добычи и краж не меняются.")
    y = 128
    y = tiles(sheet, d, y, (("stand_front.png", "1. Спереди"), ("stand_side.png", "2. Сбоку"),
                            ("stand_back.png", "3. Сзади — глыба-витрина"), ("stand_34.png", "4. 3/4")), 579)
    y = tiles(sheet, d, y, (("sleep_34.png", "5. Сон — привалился к глыбе"), ("combat_34.png", "6. Бой — рёв, кулак"),
                            ("defeat_34.png", "7. Поражение — глыба треснула")), 776)
    y = tiles(sheet, d, y, (("head_front.png", "8. Морда: монокль, прикус"), ("head_34.png", "8. Морда — 3/4"),
                            ("belt.png", "9. Портупея, бирки, ключи, лупа"), ("block.png", "10. Экспонаты во льду")),
              579)
    # силуэты + палитра + числа
    sil_w = 560
    for i, (name, text) in enumerate((("stand_front_sil.png", "Силуэт спереди"), ("stand_side_sil.png",
                                                                                "Силуэт сбоку"))):
        x = M + i * (sil_w + 12)
        sheet.paste(V.contain(V.silhouette(name), sil_w, 560), (x, y))
        V.label(d, x + 12, y + 516, text)
    px = M + 2 * (sil_w + 12)
    d.rectangle((px, y, W - M, y + 560), fill=PANEL)
    d.text((px + 18, y + 12), "Палитра", font=V.font(28, True), fill=ACC)
    pal = (("fur", "Мех — снежно-белый, кольца D39"), ("furS", "Мех: живот и плечи"), ("skin", "Маска, кисти, стопы — индиго"),
           ("neonEye", "Глаза — ледяной неон"), ("iceBlock", "Глыба — голубой лёд (прозрачность)"),
           ("gold", "Монокль, уголки, знак — золото"), ("leather", "Портупея и обвязки — кожа"),
           ("ivory", "Бивни, когти, зубы"), ("tag", "Музейные бирки (без текста)"))
    palette = st["palette"]
    for i, (k, text) in enumerate(pal):
        yy = y + 62 + i * 52
        code = palette[k]
        d.rectangle((px + 18, yy, px + 62, yy + 40), fill=tuple(int(code[j:j + 2], 16) for j in (0, 2, 4)),
                    outline=(10, 10, 14))
        d.text((px + 76, yy + 4), f"{text}  #{code}", font=V.font(22), fill=INK)
    nx = px + 620
    d.text((nx, y + 12), "Числа", font=V.font(28, True), fill=ACC)
    lines = [f"Рост в стойке {st['stand']['size_studs'][2]} стада (как Сфинкс), ширина {st['stand']['size_studs'][0]}, "
             f"масштаб модели ×{st['export_scale']}.",
             "Треугольники: стойка {0}, сон {1}, бой {2}, поражение {3} (дракон v7 — 9 тыс.).".format(
                 *(st[p]["tris"] for p in ("stand", "sleep", "combat", "defeat"))),
             "Части рига: Torso, Head, руки (UpperArm, ForeArm, Hand), ноги (Thigh, Shin, Foot) L/R, Block — "
             "глыба на своём суставе, BlockTop — отлетающая верхушка.",
             "Перевёрнутых граней 0. Совпадающие грани (лёд + уголки) уберу на шаге 2, как на этажах."]
    yy = y + 62
    for ln in lines:
        yy = V.para(d, nx, yy, ln, W - M - nx - 18, size=21, fill=INK) + 8
    y += 576
    # текст: образ, глыба, позы, модерация
    colw = (W - 2 * M - 24) // 3
    blocks = [
        ("Образ", ["• Огромный сутулый йети: короткие кривые ноги, могучие предплечья, голова утоплена в горб плеч.",
                   "• Знаток-коллекционер: золотой монокль на цепочке, кожаная портупея со знаком-снежинкой, пояс с "
                   "музейными бирками, связкой ключей и лупой.",
                   "• Морда: тёмная индиговая маска, тяжёлые брови, неправильный прикус — нижние зубы поверх губы и "
                   "два бивня вверх. Мех — ступенчатые пряди D39, грива обрамляет лицо.",
                   "Отличие от отклонённого медведя: своя анатомия (горилла-йети, а не стопка кубов), силуэт "
                   "читается и спереди (глыба над головой), и сбоку."]),
        ("Глыба-витрина", ["• На спине — ледяной кристалл выше головы в золотых уголках и кожаных обвязках: внутри "
                           "вморожены кубок, самоцвет, Ловибум и маленький зверёк.",
                           "• Сон: снял глыбу и спит, привалившись к ней, морозный пузырь из носа, ледяные «Z».",
                           "• Бой: рёв, кулак вверх. Поражение: глыба трескается — верхушка с трещинами отлетает, "
                           "осколки и экспонаты падают, монокль слетел, глаза-крестики.",
                           "Всё это — оформление и анимации (D64): добыча и бой как у Сфинкса."]),
        ("Модерация и игра", ["• Нет людей, картин, текста, логотипов, оружия и чужих персонажей; бирки и табличка — "
                              "без надписей (точки).",
                              "• Лёд глыбы в игре — MeshPart с прозрачностью ~0.3 (F_Glass в игре непрозрачен, BUGS.md), "
                              "экспонаты — отдельные меши внутри.",
                              "• Особая атака — только анимация (D64); предлагаю «Ледяной хлопок» двумя кулаками.",
                              "• Шаг 2 после «ок»: меши, 10 клипов, карты 1024², 30 существ, зона."]),
    ]
    yb = y
    scratch = ImageDraw.Draw(Image.new("RGB", (W, 2000)))  # сначала меряем высоту панелей, потом рисуем фон и текст
    bottom = max(panel(scratch, 0, yb, colw, t, ls)[1] for t, ls in blocks)
    for i, (title, lines) in enumerate(blocks):
        x = M + i * (colw + 12)
        d.rectangle((x, yb, x + colw, bottom), fill=PANEL)
        panel(d, x, yb, colw, title, lines)
    sheet = sheet.crop((0, 0, W, bottom + M))
    sheet.save(os.path.join(OUT, "1_boss.png"))
    return sheet.size


def arena():
    st = json.load(open(os.path.join(RAW, "arena5_stats.json"), encoding="utf-8"))
    sheet = Image.new("RGB", (W, 3000), BG)
    d = ImageDraw.Draw(sheet)
    header(d, "Арена 5 · Ледник — замёрзшая галерея коллекционера",
           "Зона 184 × 95 стадов (каркас MapLayout, как зона 4). Босс — поза сна, на местах — по одному существу "
           "каждой редкости. Черновая сцена в Blender.")
    y = 128
    big = 1500
    sheet.paste(V.fit(V.load("arena5_player.png"), big, round(big * 9 / 16)), (M, y))
    V.label(d, M + 14, y + round(big * 9 / 16) - 46, "Ракурс игрока у входа в зону")
    sw = W - 2 * M - big - 12
    sheet.paste(V.fit(V.load("arena5_approach.png"), sw, round(sw * 9 / 16)), (M + big + 12, y))
    V.label(d, M + big + 26, y + round(sw * 9 / 16) - 46, "Подход слева")
    ty = y + round(sw * 9 / 16) + 12
    th = round(big * 9 / 16) - round(sw * 9 / 16) - 12
    d.rectangle((M + big + 12, ty, W - M, ty + th), fill=PANEL)
    lines = ["• Задник — ледник одной стеной с острыми пиками (не дворец и не башни): в центре круглая дверь "
             "хранилища — золотое кольцо, снежинка-штурвал, голубое свечение.",
             "• На ледяном уступе — витрины с экспонатами: кубок, самоцвет, будильник, корона (объёмные, не рамки "
             "на стене).",
             "• Площадка — замёрзшее озеро со снежинкой-мозаикой; по краю — музейные столбики с красным канатом "
             "(ниже 2 стадов, проходы на пути).",
             "• По бокам — витрины на пьедесталах, гряды ледника, трещины с голубым светом, ели, сугробы с "
             "кристаллами. Небо — вечер, северное сияние лентой."]
    yy = ty + 14
    d.text((M + big + 30, yy), "Окружение", font=V.font(28, True), fill=ACC)
    yy += 50
    for ln in lines:
        yy = V.para(d, M + big + 30, yy, ln, sw - 36, size=20, fill=INK) + 6
    y += round(big * 9 / 16) + 16
    top_w = big
    sheet.paste(V.fit(V.load("arena5_top.png"), top_w, round(top_w * 9 / 16)), (M, y))
    V.label(d, M + 14, y + round(top_w * 9 / 16) - 46, "Зона сверху: вход внизу, выход вверху")
    d.rectangle((M + big + 12, y, W - M, y + round(top_w * 9 / 16)), fill=PANEL)
    yy = y + 14
    d.text((M + big + 30, yy), "Схема и бюджет", font=V.font(28, True), fill=ACC)
    yy += 52
    legend = (((255, 255, 255), "пунктир — круг боя r 34: декора выше 2 нет"),
              ((255, 48, 72), "красные кольца — 4 места существ (как зона 4, D59)"),
              ((61, 255, 122), "зелёные линии — пути: вход → площадка, к выходу по бокам задника (x ±40)"))
    for col, text in legend:
        d.rectangle((M + big + 30, yy + 8, M + big + 74, yy + 20), fill=col)
        yy = V.para(d, M + big + 88, yy, text, sw - 100, size=20, fill=INK) + 8
    total = st["total"]
    notes = [f"Примитивов в черновой сцене: {total} (без босса и существ). В игре крупный декор (ледник, гряды, ели) "
             "станет мешами — оценка ≈ 500–650 частей, в пределах ~800 на зону (D64).",
             "Частицы не нужны: сияние и свечение трещин — неоновые детали.",
             "Сияние на шаге 2 — неоновые полосы с прозрачностью в небе за ледником, вне игровой зоны.",
             "Без картин и рамок на стенах, без людей и текста: экспонаты — предметы."]
    for ln in notes:
        yy = V.para(d, M + big + 30, yy, ln, sw - 36, size=20, fill=DIM) + 8
    bottom = y + round(top_w * 9 / 16) + M
    sheet = sheet.crop((0, 0, W, bottom))
    sheet.save(os.path.join(OUT, "2_arena.png"))
    return sheet.size


def collection():
    sheet = Image.new("RGB", (W, 3000), BG)
    d = ImageDraw.Draw(sheet)
    header(d, "Ледяная коллекция босса 5 — 10 эскизов из 30",
           "Существа-экспонаты в стиле D39: у каждого своя анатомия и своя деталь-«изюминка». Доля редкостей — как в "
           "коллекции 12 / 9 / 6 / 3 (D64).")
    y = 128
    card = (W - 2 * M - 4 * 12) // 5
    notes = ["свернулся в снежок, щёки набиты", "боком на доске, очки на лбу, шарф по ветру",
             "шлем, свитер с полосой, клюшка и шайба", "ушанка со снежинкой, хвост-муфта",
             "у лунки с удочкой, шапка с помпоном, ведро рыбы", "наушники-муфты, жёлтые глаза, пенёк",
             "колючки — сосульки", "вязаный свитер со снежинками, хобот завитком",
             "рога-сияние светятся, бубенец (нос чёрный)", "на спине айсберг с деревушкой и маяком, фонтан"]
    for i in range(10):
        info = json.load(open(os.path.join(RAW, f"creature{i}.json"), encoding="utf-8"))
        x = M + (i % 5) * (card + 12)
        yy = y + (i // 5) * (card + 190)
        sheet.paste(V.fit(V.load(f"creature{i}_34.png"), card, card), (x, yy))
        col = RARITY[info["rarity"]]
        d.rectangle((x, yy + card, x + card, yy + card + 178), fill=PANEL)
        d.rectangle((x, yy + card, x + card, yy + card + 8), fill=col)
        d.text((x + 14, yy + card + 16), info["name"], font=V.font(25, True), fill=INK)
        d.text((x + 14, yy + card + 52), RARITY_RU[info["rarity"]], font=V.font(22, True), fill=col)
        V.para(d, x + 14, yy + card + 84, f"{notes[i]}. {info['tris']} треуг.", card - 28, size=19, fill=DIM)
    y += 2 * (card + 190) + 4
    d.rectangle((M, y, W - M, y + 150), fill=PANEL)
    V.para(d, M + 18, y + 14, "Эскизы — форма, цвет и «изюминка»; на шаге 2 каждое получает чистовую модель "
                             "(≤ 3 000 треугольников, проверки CHECK_OK и непохожести, карты: Common 512², Rare и выше "
                             "1024²). Остальные 20 существ коллекции — в каталоге шага 2 по тем же правилам: не больше "
                             "3 существ одной семьи силуэтов, без людей, текста, логотипов и чужих персонажей.",
           W - 2 * M - 36, size=21, fill=INK)
    sheet = sheet.crop((0, 0, W, y + 150 + M))
    sheet.save(os.path.join(OUT, "3_collection.png"))
    return sheet.size


if __name__ == "__main__":
    print(boss(), arena(), collection())
