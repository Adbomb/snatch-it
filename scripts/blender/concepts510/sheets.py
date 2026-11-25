"""Листы концептов боссов 5–10 из кадров run.py (обычный Python + Pillow, без Blender).

  python scripts/blender/concepts510/sheets.py

Читает assets/concepts/bosses_5_10/raw/*, палитры — из bossN.py (PALETTE, разбор исходника без запуска), пишет:
  bossN/1_character.png — виды спереди/сбоку/сзади, 3/4, лицо, атаки, сон, палитра и материалы;
  bossN/2_arena.png     — арена с ракурса игрока, подход, зона сверху со схемой;
  bossN/3_creatures.png — 10 примеров существ с редкостями;
  00_lineup.png, 00_arenas.png — все шесть рядом.
"""

import ast
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))  # scripts/blender
import stand_colors as SC  # noqa: E402  (D71: цвета редкостей из UITokens)
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10")
RAW = os.path.join(OUT, "raw")
FONT = "C:/Windows/Fonts/segoeui.ttf"
FONTB = "C:/Windows/Fonts/segoeuib.ttf"
BG, PANEL, INK, DIM = (24, 26, 36), (36, 39, 52), (240, 242, 248), (160, 166, 184)
RARITY = {k: v[1] for k, v in SC.RARITY.items()}  # D71: из UITokens
RARITY_RU = {"Common": "Обычное", "Rare": "Редкое", "Epic": "Эпическое", "Legendary": "Легендарное", "Secret": "Секретное"}
NOTE = "Черновой концепт: блок-аут в Blender, кольца D39 процедурные. Не финальная модель, не загружалось в Roblox."

BOSSES = {
    5: dict(zone="Ледник", name="Полярный медведь", collection="Морозный двор",
            look="Огромный сонный белый медведь: вязаный клюквенный шарф, ледяная корона набекрень, ледяные браслеты, "
                 "ворчливая морда. Сильнее Сфинкса: выше (≈24 стада против 16.8), шире, длинные лапы.",
            a1=("Ледяная оплеуха", "Лапа над головой, кольцо ледяных осколков; удар сверху вниз."),
            a2=("Снежный ком", "Обеими лапами поднимает ком над головой и бросает (каждый третий удар)."),
            mat="Plastic + LegoSquares; лёд короны и браслетов — Plastic светлый (Glass не нужен); осколки атаки — Neon."),
    6: dict(zone="Джунгли", name="Горилла", collection="Джунгли-патруль",
            look="Мощная горилла с серебристой спиной, короной из листьев с розовым цветком, ожерельем-орехами, "
                 "браслетами-лианами и огромным барабаном-колодой за спиной.",
            a1=("Кулак-молот", "Сцепленные кулаки над головой — удар в землю, разлёт камней."),
            a2=("Барабанная дробь", "Ставит барабан перед собой и бьёт — зелёные кольца-волны по земле."),
            mat="Plastic + LegoSquares; кольца волн — Neon (только на время атаки)."),
    7: dict(zone="Банк", name="Бронированный охранник", collection="Сокровищница",
            look="Массивный броненосец-инкассатор: панцирь поясами с золотыми заклёпками, кираса с жетоном, фуражка "
                 "с мигалкой, ключ-дубинка и огромная дверь сейфа как щит. Внушительнее 5 и 6: самый широкий.",
            a1=("Удар дверцей сейфа", "Щит-дверь вперёд, золотые кольца ударной волны."),
            a2=("Тревога!", "Сворачивается в бронированный шар, мигалка горит, катится вперёд."),
            mat="Plastic + LegoSquares; мигалка в «Тревоге» — Neon; дверь — Plastic (без Metal-текстур)."),
    8: dict(zone="Вулкан", name="Лавовый голем", collection="Огненная кухня",
            look="Огромный устрашающий обсидиановый голем: раскалённые трещины, огненное ядро в оправе, базальтовые "
                 "столбы на плечах и спине, рога-осколки, огромные кулаки. Без колпака, сковородки и кухни.",
            a1=("Обсидиановый молот", "Оба кулака над головой — удар, лавовое кольцо и камни по кругу."),
            a2=("Извержение", "Ядро раскрывается, над головой взлетают раскалённые камни с огненными хвостами."),
            mat="Тело — Plastic тёмный; трещины, ядро, глаза — Neon (на сне — тусклые красные Plastic)."),
    9: dict(zone="Космопорт", name="Пришелец-генерал", collection="Звёздный зоопарк",
            look="Трёхглазый генерал в фиолетово-белой космической броне и фуражке с золотой кокардой, медали; "
                 "парящий командный трон с плавником-спинкой, пультами, антигравитационным кольцом и двигателями.",
            a1=("Орбитальный удар", "Рука вверх — на земле красный прицел, сверху падает луч."),
            a2=("Тройной луч", "Лучи из трёх глаз сходятся в точку перед ним."),
            mat="Plastic + LegoSquares; неон трона и пультов — Neon (без источников света); лучи — Neon."),
    10: dict(zone="Замок", name="Король-дракон", collection="Королевский зверинец",
             look="Финальный противник: красно-золотой дракон, огромные крылья, золотые наплечники и ворот с рубином, "
                  "пурпурная мантия с горностаем, корона с тремя камнями, скипетр, рога. Самый крупный силуэт ряда.",
             a1=("Королевское пламя", "Огненное дыхание вперёд конусом."),
             a2=("Взмах крыльев", "Крылья вверх — золотые кольца вихря и летящие монеты."),
             mat="Plastic + LegoSquares; камни короны — Plastic яркий; пламя и вихрь — Neon только в атаке."),
}
ARENA_NOTES = {
    5: ["Площадка — замёрзшее озеро: ледяная мозаика с трещинами", "Задник — ледяной дворец-иглу с тремя башнями",
        "Северное сияние — неоновые ленты над дворцом", "Бока — ели в снегу, сугробы, ледяные кристаллы",
        "Пути — утоптанный снег с голубыми плитками"],
    6: ["Площадка — каменная терраса с мхом", "Задник — ступенчатый храм с лианами и нефритом (узоры вымышленные)",
        "Водопады со скал по бокам в пруды с кувшинками", "Гигантские цветы, грибы, пальмы",
        "Пути — деревянный настил"],
    7: ["Площадка — мрамор с золотой розой ветров", "Задник — гигантская круглая дверь хранилища в стене",
        "Лазерная сетка — низкие красные лучи в боковых полосах", "Пирамиды слитков, мраморные колонны",
        "Пути — красные ковры с золотыми столбиками"],
    8: ["Площадка — обсидиан со светящимися трещинами", "Задник — вулкан с неоновым жерлом и потоками лавы, дым",
        "Лавовые озёра с корками и базальтовые столбы по бокам", "Пути — тёмный камень с оранжевыми швами",
        "Небо — дымно-оранжевое"],
    9: ["Площадка — посадочный круг с неоновой разметкой", "Задник — ангар с открытыми воротами и световой рамкой",
        "Ракеты и антенны по бокам, ящики груза", "Звёздное ночное небо", "Пути — панели со световыми стрелками"],
    10: ["Площадка — гербовая мозаика красно-золотая", "Задник — главная башня с воротами, знамёна, две башни",
         "Стены вместо обрывов, ров вдоль стен, мост сбоку (не поперёк коридора)",
         "Горы сокровищ, круглые башни по бокам", "Пути — красные ковры с золотыми столбиками"],
}


def font(size, bold=False):
    return ImageFont.truetype(FONTB if bold else FONT, size)


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def fit(path, w, h):
    im = Image.open(path).convert("RGB")
    k = min(w / im.width, h / im.height)
    return im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)


def wrap(draw, text, fnt, width):
    lines, cur = [], ""
    for word in text.split():
        test = (cur + " " + word).strip()
        if draw.textlength(test, font=fnt) <= width:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def text_block(draw, xy, text, fnt, width, fill=INK, gap=6):
    x, y = xy
    for line in wrap(draw, text, fnt, width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + gap
    return y


def header(draw, W, title, sub):
    draw.rectangle((0, 0, W, 104), fill=PANEL)
    draw.text((32, 14), title, font=font(46, True), fill=INK)
    draw.text((34, 70), sub, font=font(22), fill=DIM)


def palette(n):
    src = open(os.path.join(HERE, f"boss{n}.py"), encoding="utf-8").read()
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "PALETTE":
            return ast.literal_eval(node.value)
    return {}


def character_sheet(n, d):
    raw = os.path.join(RAW, f"boss_{n}")
    W, H = 2400, 1380
    sheet = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(sheet)
    header(dr, W, f"Босс {n} · {d['zone']} — {d['name']}", NOTE)
    x, y = 24, 124
    for label, fname, w, h in (("Спереди", "front", 430, 540), ("Сбоку", "side", 430, 540), ("Сзади", "back", 430, 540),
                               ("3/4", "hero", 540, 540), ("Лицо", "face", 470, 540)):
        im = fit(os.path.join(raw, f"boss{n}_{fname}.png"), w, h)
        sheet.paste(im, (x, y))
        dr.text((x + 10, y + h - 36), label, font=font(24, True), fill=INK)
        x += w + 10
    y2 = y + 560
    x = 24
    for label, fname, (title, desc) in (("Основная атака", "attack1", d["a1"]), ("Особая атака", "attack2", d["a2"]),
                                         ("Сон на арене", "sleep", ("Поза сна", "Так игрок видит босса на подходе."))):
        im = fit(os.path.join(raw, f"boss{n}_{fname}.png"), 520, 520)
        sheet.paste(im, (x, y2))
        dr.text((x, y2 + 530), f"{label}: «{title}»" if fname != "sleep" else label, font=font(24, True), fill=INK)
        text_block(dr, (x, y2 + 564), desc, font(20), 510, fill=DIM)
        x += 540
    px = x + 10
    dr.rectangle((px, y2, W - 24, H - 24), fill=PANEL)
    dr.text((px + 20, y2 + 14), "Палитра", font=font(28, True), fill=INK)
    yy = y2 + 60
    for key, (code, desc) in palette(n).items():
        dr.rectangle((px + 20, yy, px + 76, yy + 34), fill=hexrgb(code), outline=(0, 0, 0))
        dr.text((px + 90, yy + 2), f"#{code}  {desc}", font=font(20), fill=INK)
        yy += 42
    yy += 10
    dr.text((px + 20, yy), "Материалы", font=font(28, True), fill=INK)
    yy = text_block(dr, (px + 20, yy + 42), d["mat"], font(20), W - px - 70, fill=DIM)
    dr.text((px + 20, yy + 12), "Образ", font=font(28, True), fill=INK)
    text_block(dr, (px + 20, yy + 54), d["look"], font(20), W - px - 70, fill=DIM)
    return sheet


def arena_sheet(n, d):
    raw = os.path.join(RAW, f"arena_{n}")
    W, H = 2400, 1880
    sheet = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(sheet)
    header(dr, W, f"Арена {n} · {d['zone']} — зона 184 × 95 стадов",
           "Босс — поза сна ×3, на местах — 4 существа его коллекции. " + NOTE)
    sheet.paste(fit(os.path.join(raw, f"arena{n}_player.png"), 1440, 810), (24, 124))
    dr.text((40, 124 + 770), "С ракурса игрока у входа в зону", font=font(26, True), fill=INK)
    sheet.paste(fit(os.path.join(raw, f"arena{n}_approach.png"), 900, 506), (1476, 124))
    dr.text((1490, 124 + 470), "Подход слева", font=font(24, True), fill=INK)
    dr.rectangle((1476, 650, W - 24, 934), fill=PANEL)
    dr.text((1496, 662), "Окружение", font=font(28, True), fill=INK)
    yy = 706
    for line in ARENA_NOTES[n]:
        yy = text_block(dr, (1496, yy), "• " + line, font(21), 860, fill=DIM, gap=4)
    sheet.paste(fit(os.path.join(raw, f"arena{n}_top.png"), 1440, 810), (24, 954))
    dr.text((40, 954 + 770), "Зона сверху: вход внизу, выход вверху", font=font(26, True), fill=INK)
    dr.rectangle((1476, 954, W - 24, H - 24), fill=PANEL)
    dr.text((1496, 966), "Схема (только на виде сверху)", font=font(28, True), fill=INK)
    yy = 1012
    for color, line in (((255, 255, 255), "пунктир — круг боя r 34: декора выше 2 нет"),
                        ((255, 48, 72), "красные кольца — 4 места существ (как у зоны 4, D59)"),
                        ((61, 255, 122), "зелёные линии — пути: вход → площадка, от площадки к выходу по бокам "
                                         "задника (x ±40); во входе зоны — те же две дорожки")):
        dr.rectangle((1496, yy + 8, 1530, yy + 18), fill=color)
        yy = text_block(dr, (1546, yy), line, font(21), 810, fill=DIM, gap=4) + 8
    try:
        st = json.load(open(os.path.join(raw, f"arena{n}_stats.json"), encoding="utf-8"))
        yy = text_block(dr, (1496, yy + 10), f"Примитивов в черновой сцене: {st['total']} (не детали игры; оценка "
                                             "игры — OVERVIEW.md, ≈ 800 на зону).", font(21), 860, fill=DIM)
    except OSError:
        pass
    text_block(dr, (1496, yy + 10), "Площадка r 31, место босса (0, −5), ширина коридора ±92, длина 95 — "
                                     "как у зоны 4 (MapLayout). Задник — в полосе y 31…47, |x| < 30.",
               font(21), 860, fill=DIM)
    return sheet


def creature_sheet(n, d):
    tree = ast.parse(open(os.path.join(HERE, f"creatures{n}.py"), encoding="utf-8").read())
    entries = []  # (id, имя, редкость) из CREATURES без запуска Blender
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CREATURES":
            for elt in node.value.elts:
                entries.append(tuple(ast.literal_eval(e) for e in elt.elts[:3]))
    raw = os.path.join(RAW, f"creatures_{n}")
    W, H = 2400, 1300
    sheet = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(sheet)
    header(dr, W, f"Коллекция босса {n} «{d['collection']}» — 10 примеров из 30",
           "Каждое — своя форма и механизм, не перекраска. " + NOTE)
    files = sorted(f for f in os.listdir(raw) if f.endswith(".png"))
    cw, ch = 460, 460
    for i, ((cid, name, rarity), fname) in enumerate(zip(entries, files)):
        x = 24 + (i % 5) * (cw + 10)
        y = 124 + (i // 5) * (ch + 120)
        sheet.paste(fit(os.path.join(raw, fname), cw, ch), (x, y))
        col = hexrgb(RARITY[rarity])
        dr.rectangle((x, y + ch, x + cw, y + ch + 100), fill=PANEL)
        dr.rectangle((x, y + ch, x + 8, y + ch + 100), fill=col)
        text_block(dr, (x + 20, y + ch + 8), name, font(24, True), cw - 30, gap=2)
        dr.text((x + 20, y + ch + 66), RARITY_RU[rarity], font=font(21, True), fill=col)
    return sheet


def lineup():
    raw = os.path.join(RAW, "lineup")
    im = Image.open(os.path.join(raw, "lineup.png")).convert("RGB")
    marks = json.load(open(os.path.join(raw, "lineup.json")))
    W, H = im.width, im.height + 230
    sheet = Image.new("RGB", (W, H), BG)
    sheet.paste(im, (0, 120))
    dr = ImageDraw.Draw(sheet)
    header(dr, W, "Боссы 5–10 рядом: идёт рост угрозы к финалу",
           "Слева — габарит Сфинкса (босс 4) и игрок для масштаба; высоты в игре ×3. " + NOTE)
    for m in marks:
        if m["id"] == "ref":
            label, sub = "Сфинкс · игрок", "16.8 · ≈5 ст."
        else:
            n = int(m["id"])
            label, sub = f"{n}. {BOSSES[n]['name']}", f"≈{m['top'] * 3:.0f} стадов"
        w = dr.textlength(label, font=font(28, True))
        dr.text((m["u"] - w / 2, 120 + im.height + 20), label, font=font(28, True), fill=INK)
        w2 = dr.textlength(sub, font=font(22))
        dr.text((m["u"] - w2 / 2, 120 + im.height + 62), sub, font=font(22), fill=DIM)
    return sheet


def arenas_grid():
    W, H = 2400, 1520
    sheet = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(sheet)
    header(dr, W, "Арены 5–10 с ракурса игрока", NOTE)
    for i, n in enumerate((5, 6, 7, 8, 9, 10)):
        x, y = 24 + (i % 3) * 790, 124 + (i // 3) * 690
        sheet.paste(fit(os.path.join(RAW, f"arena_{n}", f"arena{n}_player.png"), 780, 439), (x, y))
        dr.text((x, y + 448), f"{n}. {BOSSES[n]['zone']} — {BOSSES[n]['name']}", font=font(28, True), fill=INK)
        text_block(dr, (x, y + 490), ARENA_NOTES[n][1], font(21), 770, fill=DIM)
    return sheet


def main():
    for n, d in BOSSES.items():
        folder = os.path.join(OUT, f"boss{n}")
        os.makedirs(folder, exist_ok=True)
        character_sheet(n, d).save(os.path.join(folder, "1_character.png"))
        arena_sheet(n, d).save(os.path.join(folder, "2_arena.png"))
        creature_sheet(n, d).save(os.path.join(folder, "3_creatures.png"))
        print("boss", n)
    lineup().save(os.path.join(OUT, "00_lineup.png"))
    arenas_grid().save(os.path.join(OUT, "00_arenas.png"))
    print("DONE")


if __name__ == "__main__":
    main()
