"""Листы концепта босса 7 «Банк» (шаг 1 D64): босс, арена, 10 эскизов коллекции — на утверждение владельцем.

  python scripts/blender/boss7/sheet.py
  → assets/concepts/bosses_5_10/boss7/{1_boss,2_arena,3_collection}.png (вне git)
Кадры и числа — из boss7/raw/ (render.py, arena.py, creatures.py). Оформление — как листы боссов 5 и 6.
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
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss7")
RAW = os.path.join(OUT, "raw")
CR = os.path.join(RAW, "creatures")
V.RAW = RAW
BG, PANEL, INK, DIM, ACC = V.BG, V.PANEL, V.INK, V.DIM, V.ACC
W, M = 2400, 24
RARITY = {k: SC.rgb(SC.RARITY[k][1]) for k in ("Common", "Rare", "Epic", "Legendary")}
RARITY_RU = {"Common": "Обычное", "Rare": "Редкое", "Epic": "Эпическое", "Legendary": "Легендарное"}


def header(d, title, sub):
    d.rectangle((0, 0, W, 110), fill=PANEL)
    d.text((30, 12), title, font=V.font(44, True), fill=INK)
    d.text((32, 70), sub, font=V.font(23), fill=DIM)


def load(name):
    return Image.open(name if os.path.isabs(name) else os.path.join(RAW, name)).convert("RGB")


def tiles(sheet, d, y, items, size, gap=12, h=None):
    h = h or size
    for i, (name, text) in enumerate(items):
        x = M + i * (size + gap)
        sheet.paste(V.fit(load(name), size, h), (x, y))
        V.label(d, x + 12, y + h - 44, text)
    return y + h + 16


def panel(d, x, y, w, title, lines, size=21):
    y0 = y
    d.text((x + 18, y + 12), title, font=V.font(28, True), fill=ACC)
    y += 58
    for ln in lines:
        y = V.para(d, x + 18, y, ln, w - 36, size=size, fill=INK if ln.startswith("•") else DIM) + 4
    return y0, y + 12


def text_blocks(sheet, d, y, blocks):
    colw = (W - 2 * M - 24) // 3
    scratch = ImageDraw.Draw(Image.new("RGB", (W, 3000)))
    bottom = max(panel(scratch, 0, y, colw, t, ls)[1] for t, ls in blocks)
    for i, (title, lines) in enumerate(blocks):
        x = M + i * (colw + 12)
        d.rectangle((x, y, x + colw, bottom), fill=PANEL)
        panel(d, x, y, colw, title, lines)
    return bottom


def boss():
    st = json.load(open(os.path.join(RAW, "stats.json"), encoding="utf-8"))
    sheet = Image.new("RGB", (W, 7000), BG)
    d = ImageDraw.Draw(sheet)
    header(d, "Босс 7 · Банк — Копилка-громила · концепт",
           "Огромная бронированная свинья-копилка: прорезь для монет на спине, обручи и щитки с заклёпками. "
           "Сразу игровая копия ≤ 8 000 треугольников.")
    y = 128
    y = tiles(sheet, d, y, (("stand_front.png", "1. Спереди"), ("stand_side.png", "2. Сбоку — бочка, обручи"),
                            ("stand_back.png", "3. Сзади — хвост-завиток"), ("stand_34.png", "4. 3/4")), 579)
    y = tiles(sheet, d, y, (("sleep_34.png", "5. Сон"), ("combat_34.png", "6. Бой — «Таран пятачком»"),
                            ("special_34.png", "7. Особая — «Монетный град»"),
                            ("defeat_34.png", "8. Поражение — треснула")), 579)
    y = tiles(sheet, d, y, (("head_front.png", "9. Лицо"), ("head_34.png", "9. Голова — 3/4"),
                            ("slot.png", "10. Прорезь и седло"), ("combat_front.png", "11. Таран — спереди"),
                            ("defeat_front.png", "12. Глаза-крестики")), 460)
    sil_w = 560
    for i, (name, text) in enumerate((("stand_front_sil.png", "Силуэт спереди"),
                                      ("stand_side_sil.png", "Силуэт сбоку"))):
        x = M + i * (sil_w + 12)
        sheet.paste(V.contain(V.silhouette(name), sil_w, 600), (x, y))
        V.label(d, x + 12, y + 556, text)
    px = M + 2 * (sil_w + 12)
    d.rectangle((px, y, W - M, y + 600), fill=PANEL)
    d.text((px + 18, y + 12), "Палитра", font=V.font(28, True), fill=ACC)
    pal = (("pig", "Тело — ярко-розовое (главное пятно)"), ("snout", "Пятачок — светлее"),
           ("pigD", "Уши внутри, складки"), ("hoof", "Копыта"), ("steel", "Броня — тёмная сталь"),
           ("steelL", "Кромки брони"), ("gold", "Рамка прорези, заклёпки"), ("coin", "Монеты"),
           ("slot", "Прорезь, пролом"), ("brow", "Брови"), ("tusk", "Клычки — тупые"), ("crack", "Трещины"))
    palette = st["palette"]
    for i, (k, text) in enumerate(pal):
        yy = y + 58 + i * 42
        code = palette[k]
        d.rectangle((px + 18, yy, px + 56, yy + 32), fill=tuple(int(code[j:j + 2], 16) for j in (0, 2, 4)),
                    outline=(10, 10, 14))
        d.text((px + 68, yy + 2), f"{text}  #{code}", font=V.font(20), fill=INK)
    nx = px + 600
    d.text((nx, y + 12), "Числа", font=V.font(28, True), fill=ACC)
    poses = ("stand", "sleep", "combat", "special", "defeat")
    tris = [st[p]["tris"] for p in poses]
    grp = st["stand"].get("tris_by_group", {})
    sz = st["stand"]["size_studs"]
    lines = [f"Высота в стойке {sz[2]} стада, длина {sz[1]}, ширина {sz[0]} (с наплечниками); масштаб модели "
             f"×{st['export_scale']}. Ниже Йети (24), но вдвое длиннее — самый широкий и тяжёлый силуэт.",
             "Игровая копия уже сейчас: стойка {0}, сон {1}, бой {2}, особая {3}, поражение {4} треугольников — "
             "все ≤ 8 000.".format(*tris),
             "Части рига: " + ", ".join(f"{k} {v}" for k, v in grp.items()) + " треуг.",
             f"Перевёрнутых граней 0, совпадающих граней в стойке, сне и бою — 0."]
    yy = y + 62
    for ln in lines:
        yy = V.para(d, nx, yy, ln, W - M - nx - 18, size=21, fill=INK) + 10
    y += 616
    blocks = [
        ("Образ", ["• Копилка-«громила» на четырёх коротких толстых ногах: тело — розовая бочка ярусами D39, "
                   "голова с большим светлым пятачком, уши-треугольники вперёд, хвост-завиток.",
                   "• Броня: два стальных обруча и стальное седло с прорезью в золотой рамке, наплечники-щиты, "
                   "щиток на лбу, наголенники; заклёпки — золотые. Из прорези торчит монета.",
                   "• Розовое — около 2/3 видимой поверхности; сталь тёмная, золото — акцентами: на тёмном "
                   "мраморе и стали хранилища свинья — главное пятно кадра.",
                   "• Лицо: маленькие злые глаза, тяжёлые брови, ухмылка, челюсть «громилы» с двумя тупыми клычками."]),
        ("Бой и позы", ["• Бой — база боссов 1–5: HP 140, урон 8, интервал 1.4; сила по D56 — "
                        "Progression.Bosses[7] = 300M; ходит за игроком, как Йети (D65).",
                        "• Корпус широкий и длинный — удар считается от контура тела (BodyRange, как у Йети и "
                        "дракона), а не от центра.",
                        "• Основная атака — «Таран пятачком»: голову вниз, бросок вперёд, из прорези выскакивают монеты.",
                        "• Особая (каждый 3-й удар, только анимация, D64) — предлагаю «Монетный град»: встаёт на дыбы "
                        "и с грохотом опускается, из прорези бьёт фонтан монет.",
                        "• Сон — лежит на брюхе, ноги вытянуты, глаза закрыты, ничего не светится, «Z». Поражение — "
                        "трещины, пролом на боку, горка монет, розовые осколки, глаза-крестики, язык набок.",
                        "• Монеты — только оформление и анимация: бой, добыча и кражи не меняются."]),
        ("Модерация и дальше", ["• Без людей и охранников, картин, текста, логотипов банков, купюр и оружия; "
                                "клычки тупые, пасть мультяшная. Злой, но смешной.",
                                "• До общего выпуска — только Studio и тестовый сервер владельца (D64 п. 7).",
                                "• После «ок»: 10 клипов, 30 существ, арена, подключение — тем же конвейером, что "
                                "Йети и Королева-мухоловка."]),
    ]
    bottom = text_blocks(sheet, d, y, blocks)
    sheet = sheet.crop((0, 0, W, bottom + M))
    sheet.save(os.path.join(OUT, "1_boss.png"))
    return sheet.size


def arena():
    st = json.load(open(os.path.join(RAW, "arena7_stats.json"), encoding="utf-8"))
    sheet = Image.new("RGB", (W, 5000), BG)
    d = ImageDraw.Draw(sheet)
    header(d, "Арена 7 · Банк — хранилище Копилки-громилы",
           "Зона 184 × 95 стадов (каркас MapLayout). Копилка — поза сна, на плитах — по одному существу каждой "
           "редкости. Черновая сцена в Blender.")
    y = 128
    big = 1500
    bh = round(big * 9 / 16)
    sheet.paste(V.fit(load("arena7_player.png"), big, bh), (M, y))
    V.label(d, M + 14, y + bh - 46, "Главный кадр — ракурс игрока у входа в зону")
    sw = W - 2 * M - big - 12
    shh = round(sw * 9 / 16)
    sheet.paste(V.fit(load("arena7_approach.png"), sw, shh), (M + big + 12, y))
    V.label(d, M + big + 26, y + shh - 46, "Подход сбоку")
    ty = y + shh + 12
    sheet.paste(V.fit(load("arena7_lane.png"), sw, shh), (M + big + 12, ty))
    V.label(d, M + big + 26, ty + shh - 46, "Полоса бега насквозь")
    y += bh + 16
    sheet.paste(V.fit(load("arena7_top.png"), big, bh), (M, y))
    V.label(d, M + 14, y + bh - 46, "Зона сверху: вход внизу, выход вверху (дверь и ворота скрыты)")
    d.rectangle((M + big + 12, y, W - M, y + bh), fill=PANEL)
    yy = y + 14
    d.text((M + big + 30, yy), "Свободный бег (D66)", font=V.font(28, True), fill=ACC)
    yy += 52
    legend = (((61, 255, 122), "зелёные рамки — свободные пути: две полосы |x| 48–66 (18 стадов) насквозь от входа до "
                               "выхода и дальше, центральный путь к площадке, перемычки к полосам"),
              ((255, 255, 255), "пунктир — круг боя r 34"),
              ((255, 48, 72), "красные кольца — 4 плиты существ"),
              ((255, 212, 0), "жёлтый пунктир — |x| 76: дальше к стене твёрдое не выше 24"))
    for col, text in legend:
        d.rectangle((M + big + 30, yy + 8, M + big + 74, yy + 20), fill=col)
        yy = V.para(d, M + big + 88, yy, text, sw - 100, size=20, fill=INK) + 8
    ok = all(st.get(k) == "ok" for k in ("free_lanes", "exit_lanes"))
    notes = [("Проверка скриптом: в полосах, на путях и за выходом нет ничего на высоте 1.1–7 — да." if ok else
              f"Проверка скриптом: помехи на путях — {st.get('free_lanes')} / {st.get('exit_lanes')}."),
             "Круг боя r 34 — ничего выше 2 — " + ("да." if st.get("fight_circle_r34") == "ok" else
                                                  f"{st.get('fight_circle_r34')}."),
             "Твёрдое у стен (|x| > 76) не выше 24 — " + ("да." if st.get("walls_solid_le_24") == "ok" else
                                                         f"{st.get('walls_solid_le_24')}."),
             f"Игра: ≈ {st['game_parts_total']} частей (бюджет 800): дверь, стена, колонны, штабеля и горы монет — "
             f"мешами, пол — текстурой мрамора."]
    for ln in notes:
        yy = V.para(d, M + big + 30, yy, ln, sw - 36, size=20, fill=DIM) + 8
    y += bh + 16
    blocks = [
        ("Главное в кадре", ["• Задник — круглая дверь сейфа ø 32 из тёмной стали: золотой обод, 12 засовов, штурвал; "
                             "за ней — тёмная клёпаная стена хранилища. Розовая копилка — на тёмной стали.",
                             "• Пол — тёмно-зелёный мрамор крупной шахматкой; площадка — тёмный сине-зелёный мрамор "
                             "с золотыми кольцами, как монета.",
                             "• Мало крупных вещей вместо россыпи мелочи: дверь, колонны, два штабеля слитков у "
                             "двери, горы монет с огромными монетами на ребре."]),
        ("Колонны, золото, плиты", ["• Мраморные колонны (тёмно-зелёные, золотые база и капитель): пара у двери, "
                                    "пара в рамке входа, по две в середине и колоннада за полосами у стен.",
                                    "• Штабеля слитков пирамидой и горы монет — у двери и вдоль стен.",
                                    "• Плиты существ (D71): тёмный круг, золотой обод, кольцо и свет снизу цветом "
                                    "редкости — добыча видна от входа."]),
        ("Проход и правила", ["• Полосы |x| 48–66 — тёмная мраморная дорожка с золотой каймой (ниже 1.1), прямо "
                              "от входа до выхода; на выходе — массивные ворота: опоры вне полосы, балка выше 10.",
                              "• Без людей, статуй, картин, текста, логотипов банков, купюр, лазеров-«оружия» и "
                              "охранников; ничего похожего на петлю: в воротах ничего не свисает.",
                              "• Свет — тёплый от двери и холодный у входа; свет зоны — по D67 при постройке."]),
    ]
    bottom = text_blocks(sheet, d, y, blocks)
    sheet = sheet.crop((0, 0, W, bottom + M))
    sheet.save(os.path.join(OUT, "2_arena.png"))
    return sheet.size


SIGNS = {  # образ (шутка в теле) · признаки вида D64 · эмоция
    "HoardHamster": ("набил щёки монетами так, что щёки шире его самого; из губ торчат две монетки",
                     "защёчные мешки, круглые ушки, резцы, короткие лапки, хвостик-пенёк", "жадно-довольная ухмылка"),
    "StarNoseMole": ("нашёл самородок и прижал его огромными лапами-лопатами; нос-звезда распушился",
                     "розовая «звезда» из лучей, широкие лапы с когтями, бархатная шерсть, крошечные глаза",
                     "счастливо зажмурился"),
    "GoldAxolotl": ("золотой, а жабры разрослись в розовую корону — считает себя главным сокровищем",
                    "широкая голова с улыбкой, 3 пары ветвистых жабр, 4 лапки с пальцами, хвост-плавник",
                    "гордая улыбка"),
    "RaccoonMagpie": ("два воришки в одном: тело сороки, голова и полосатый хвост енота; уносит монету в клюве",
                      "чёрно-белое оперение и синее крыло, клюв, тонкие лапы; маска енота, круглые уши, хвост в кольцах",
                      "хитрый прищур"),
    "PouchKangaroo": ("сумка так набита монетами, что перевешивает — сидит на хвосте, как на стуле",
                      "длинные ступни, хвост-опора, лапки, длинные уши, морда, сумка", "озабоченно-гордая"),
    "GemArmadillo": ("вся броня — ряды огранённых самоцветов в золотой оправе: носит богатство на себе",
                     "панцирь из 5 поясов, щиток на голове, длинная морда, большие уши, хвост в кольцах",
                     "нос кверху, важный"),
    "PearlOtter": ("лежит на спине на волне и держит жемчужину больше своей головы — любуется",
                   "светлая голова калана, тёмное тело, перепончатые лапы вверх, плоский хвост, усы",
                   "любуется жемчужиной"),
    "GoldenPheasant": ("золотой хохол такой длинный, что струится по спине до хвоста, как грива",
                       "золотой хохол, оранжевая накидка в полоску, алая грудь, зелёная спина, синее крыло, "
                       "длинный хвост", "задрал клюв, гордец"),
    "FleeceAlpaca": ("руно золотое и такое пышное, что альпака — облако кудрей на тонких ножках",
                     "длинная шея, уши-«бананы», большие глаза с ресницами, раздвоенная губа, копытца",
                     "мечтательно-довольная"),
    "TreasureGriffin": ("перед — орёл, зад — лев; сидит на горке монет, раскрыл крылья «моё!», на лбу светится "
                        "самоцвет", "крючковатый клюв и хохол, птичьи когти, львиное тело, хвост с кисточкой, "
                                    "крылья", "надменно-гордый страж"),
}


def reports(folder):
    out = {}
    for name in sorted(os.listdir(folder)):
        if name.startswith("report") and name.endswith(".json"):
            out.update(json.load(open(os.path.join(folder, name), encoding="utf-8")))
    return out


def collection():
    sheet = Image.new("RGB", (W, 4600), BG)
    d = ImageDraw.Draw(sheet)
    header(d, "Коллекция «Банк» босса 7 — 10 эскизов из 30 · сокровища и жадность",
           "Странные и смешные звери: смешное в самом теле, сокровища — акцентом. Доля редкостей — как в коллекции "
           "12 / 9 / 6 / 3 (D64), Secret нет.")
    y = 128
    card = (W - 2 * M - 4 * 12) // 5
    rep = reports(CR)
    info_h = 330
    for i, item in enumerate(SIGNS):
        r = rep.get(item, {})
        x = M + (i % 5) * (card + 12)
        yy = y + (i // 5) * (card + info_h + 12)
        hero = os.path.join(CR, f"{item}_hero.png")
        if os.path.exists(hero):
            im = Image.open(hero).convert("RGB")
            w, h = im.size
            im = im.crop((int(w * 0.2), int(h * 0.16), int(w * 0.8), int(h * 0.76)))  # существо крупнее в карточке
            sheet.paste(V.fit(im, card, card), (x, yy))
        col = RARITY[r.get("rarity", "Common")]
        d.rectangle((x, yy + card, x + card, yy + card + info_h), fill=PANEL)
        d.rectangle((x, yy + card, x + card, yy + card + 8), fill=col)
        d.text((x + 14, yy + card + 16), r.get("title", item), font=V.font(25, True), fill=INK)
        d.text((x + 14, yy + card + 50), RARITY_RU[r.get("rarity", "Common")], font=V.font(22, True), fill=col)
        img, signs, mood = SIGNS[item]
        ty = V.para(d, x + 14, yy + card + 82, f"{img[0].upper()}{img[1:]}.", card - 28, size=18, fill=INK)
        ty = V.para(d, x + 14, ty + 4, f"Признаки: {signs}.", card - 28, size=17, fill=DIM)
        V.para(d, x + 14, ty + 4, f"Эмоция: {mood}. {r.get('tris_without_stand', '?')} треуг.", card - 28, size=17,
               fill=DIM)
    y += 2 * (card + info_h + 12) + 4
    blocks = [
        ("Тема и правила", ["• Тема — сокровища и жадность: набитые щёки и сумка, самородок, жемчужина, броня из "
                            "самоцветов, золотые руно и жабры, воришка с монетой, страж на горке монет.",
                            "• Гибриды — только зверь + зверь (сорока + енот, орёл + лев); бытовых вещей нет.",
                            "• Каждое ≤ 3 000 треугольников без подставки; подставка — цвет редкости (D71).",
                            "• Это эскизы: щели в суставах (у 6 из 10) и мелкие совпадающие грани доводятся на шаге 2 "
                            "до листа аудита анатомии D64."]),
        ("Не повторяет 1–6", ["• Звери новые: в коллекциях 1–6 не было хомяка, крота, аксолотля, сороки, енота, "
                              "кенгуру, броненосца, выдры, фазана, альпаки, грифона.",
                              "• Шутки новые: нет многоголовых, стопок, длинной шеи, огромных зубов и глаз, тела-шара, "
                              "хвоста-колеса, «держит лист над головой»."]),
        ("Легендарное «вау» 1", ["• Грифон-казначей — самый крупный и яркий: золото, бирюзовые кончики крыльев, "
                                 "светящийся самоцвет на лбу, горка монет в композиции — за ним хочется охотиться.",
                                 "• Модерация: без людей, текста, логотипов, купюр, оружия, мемных и чужих персонажей; "
                                 "мифический грифон — общий образ, не чей-то персонаж."]),
    ]
    bottom = text_blocks(sheet, d, y, blocks)
    sheet = sheet.crop((0, 0, W, bottom + M))
    sheet.save(os.path.join(OUT, "3_collection.png"))
    return sheet.size


if __name__ == "__main__":
    which = sys.argv[1:] or ["boss", "arena", "collection"]
    print({w: globals()[w]() for w in which})
