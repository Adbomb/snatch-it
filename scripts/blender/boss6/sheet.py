"""Листы концепта босса 6 «Джунгли» (шаг 3 D64): босс, арена, коллекция джунглей — для утверждения владельцем.

  python scripts/blender/boss6/sheet.py
  → assets/concepts/bosses_5_10/boss6_v2/{1_boss,2_arena,3_collection}.png (вне git)
Кадры и числа — из boss6_v2/raw/ (render.py, arena.py, creatures.py). Оформление — как листы босса 5.
"""

import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "dragon10"))
sys.path.insert(0, HERE)
import v7_sheet as V  # noqa: E402  (font, fit, para, label, silhouette — общие помощники листов)

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss6_v2")
RAW = os.path.join(OUT, "raw")
CR = os.path.join(RAW, "creatures")
V.RAW = RAW
BG, PANEL, INK, DIM, ACC = V.BG, V.PANEL, V.INK, V.DIM, V.ACC
W, M = 2400, 24
RARITY = {"Common": (173, 166, 180), "Rare": (61, 142, 224), "Epic": (154, 62, 240), "Legendary": (245, 162, 21)}
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
    y0 = y
    d.text((x + 18, y + 12), title, font=V.font(28, True), fill=ACC)
    y += 58
    for ln in lines:
        y = V.para(d, x + 18, y, ln, w - 36, size=size, fill=INK if ln.startswith("•") else DIM) + 4
    return y0, y + 12


def text_blocks(sheet, d, y, blocks):
    colw = (W - 2 * M - 24) // 3
    scratch = ImageDraw.Draw(Image.new("RGB", (W, 2000)))
    bottom = max(panel(scratch, 0, y, colw, t, ls)[1] for t, ls in blocks)
    for i, (title, lines) in enumerate(blocks):
        x = M + i * (colw + 12)
        d.rectangle((x, y, x + colw, bottom), fill=PANEL)
        panel(d, x, y, colw, title, lines)
    return bottom


def boss():
    st = json.load(open(os.path.join(RAW, "stats.json"), encoding="utf-8"))
    sheet = Image.new("RGB", (W, 6000), BG)
    d = ImageDraw.Draw(sheet)
    header(d, "Босс 6 · Джунгли — Королева-мухоловка",
           "Концепт шага 3 (D64): Blender, стиль D39, одна модель в четырёх позах. В Roblox не загружалось; "
           "правила боя, добычи и краж не меняются.")
    y = 128
    y = tiles(sheet, d, y, (("stand_front.png", "1. Спереди"), ("stand_side.png", "2. Сбоку"),
                            ("stand_back.png", "3. Сзади — мантия из листьев"), ("stand_34.png", "4. 3/4")), 579)
    y = tiles(sheet, d, y, (("sleep_34.png", "5. Сон — пасть сомкнута, голова склонилась"),
                            ("combat_34.png", "6. Бой — «Захлоп»"), ("defeat_34.png", "7. Поражение — увяла")), 776)
    y = tiles(sheet, d, y, (("head_front.png", "8. Лицо: веки, ресницы, корона"), ("head_34.png", "8. Голова — 3/4"),
                            ("collar.png", "9. Воротник, медальон, корсаж"), ("buds.png", "10. Бутоны-фрейлины")),
              579)
    sil_w = 560
    for i, (name, text) in enumerate((("stand_front_sil.png", "Силуэт спереди"),
                                      ("stand_side_sil.png", "Силуэт сбоку"))):
        x = M + i * (sil_w + 12)
        sheet.paste(V.contain(V.silhouette(name), sil_w, 560), (x, y))
        V.label(d, x + 12, y + 516, text)
    px = M + 2 * (sil_w + 12)
    d.rectangle((px, y, W - M, y + 560), fill=PANEL)
    d.text((px + 18, y + 12), "Палитра", font=V.font(28, True), fill=ACC)
    pal = (("leaf", "Листья, створки, бутон — зелень, кольца D39"), ("leafL", "Маска лица, юбка — салатовый"),
           ("maw", "Нутро пасти, кайма створок — малиновый"), ("teeth", "Реснички-зубы"),
           ("petal", "Венчик лепестков, румянец"), ("gold", "Корона, медальон, застёжка — золото"),
           ("neonGem", "Самоцветы — розовый неон"), ("root", "Клубень и корни"), ("stemD", "Узлы стебля, веки"))
    palette = st["palette"]
    for i, (k, text) in enumerate(pal):
        yy = y + 62 + i * 52
        code = palette[k]
        d.rectangle((px + 18, yy, px + 62, yy + 40), fill=tuple(int(code[j:j + 2], 16) for j in (0, 2, 4)),
                    outline=(10, 10, 14))
        d.text((px + 76, yy + 4), f"{text}  #{code}", font=V.font(22), fill=INK)
    nx = px + 640
    d.text((nx, y + 12), "Числа", font=V.font(28, True), fill=ACC)
    lines = [f"Рост в стойке {st['stand']['size_studs'][2]} стада (как Йети), ширина {st['stand']['size_studs'][0]} "
             f"(с корнями), масштаб модели ×{st['export_scale']}.",
             "Треугольники концепта: стойка {0}, сон {1}, бой {2}, поражение {3}; игровая копия на шаге 2 — "
             "≤ 8 тыс. (как дракон v7).".format(*(st[p]["tris"] for p in ("stand", "sleep", "combat", "defeat"))),
             "Части рига (предложение для шага 2): Base (клубень, корни, юбка — неподвижны), Stem ×4 узла, Collar, Head, Jaw (нижняя "
             "створка), VineL/R + HandL/R, Mantle, Buds ×2 (свои створки).",
             f"Перевёрнутых граней {st['stand']['flipped']}. Совпадающие грани слоёв створок уберу на шаге 2."]
    yy = y + 62
    for ln in lines:
        yy = V.para(d, nx, yy, ln, W - M - nx - 18, size=21, fill=INK) + 8
    y += 576
    blocks = [
        ("Образ", ["• Хищное растение-королева, вросшее в землю: внизу пышная юбка из двух ярусов огромных листьев "
                   "и корни, тонкая «талия» — стебель с узлами, корсаж из листьев крест-накрест.",
                   "• Голова — бутон с лицом: тяжёлые веки, ресницы, брови-бруски, румянец; над ней корона с "
                   "самоцветами и венчик розовых лепестков.",
                   "• Пасть — ловушка мухоловки: две створки, снаружи зелёные с малиновой каймой, внутри малиновые, "
                   "по краю — частокол ресничек; сомкнута — реснички переплетены.",
                   "• Сзади — мантия из трёх листьев с золотой застёжкой, на груди медальон. У ног — два бутона-"
                   "фрейлины (маленькие мухоловки с лицами)."]),
        ("Бой и позы", ["• Не ходит (D64 п. 5): вросла в террасу, поворачивается на месте, как дракон; удар — "
                        "от контура тела (BodyRange), как у Йети и дракона.",
                        "• Основная атака — «Захлоп»: голова бросается вперёд, створки захлопываются.",
                        "• Особая — только анимация (D64): предлагаю «Лиановый вихрь» — лианы-руки раскручиваются "
                        "и хлещут по кругу, бутоны-фрейлины щёлкают пастями.",
                        "• Сон: пасть сомкнута, голова склонилась, глаза закрыты, капля росы, «Z». Поражение: стебель "
                        "клонится, глаза-крестики, язык набок, корона на земле, опавшие листья."]),
        ("Модерация и игра", ["• Нет людей, картин, текста, логотипов, оружия и чужих персонажей; узоры — листья и "
                              "цветы. Отличие от чужих «растений с пастью»: лицо на бутоне, корона и венчик, юбка из "
                              "листьев, корни.",
                              "• Сила, HP, урон — как у боссов 1–5 по D56 (Progression.Bosses[6]); Closed до общего "
                              "выпуска (D64 п. 7).",
                              "• Шаг 2 после «ок»: игровая модель, 10 клипов, 30 существ, арена, подключение — тем же "
                              "конвейером, что Йети."]),
    ]
    bottom = text_blocks(sheet, d, y, blocks)
    sheet = sheet.crop((0, 0, W, bottom + M))
    sheet.save(os.path.join(OUT, "1_boss.png"))
    return sheet.size


def arena():
    st = json.load(open(os.path.join(RAW, "arena6_stats.json"), encoding="utf-8"))
    sheet = Image.new("RGB", (W, 3600), BG)
    d = ImageDraw.Draw(sheet)
    header(d, "Арена 6 · Джунгли — сад Королевы-мухоловки",
           "Зона 184 × 95 стадов (каркас MapLayout). Королева — поза сна, на местах — по одному существу каждой "
           "редкости. Черновая сцена в Blender.")
    y = 128
    big = 1500
    sheet.paste(V.fit(V.load("arena6_player.png"), big, round(big * 9 / 16)), (M, y))
    V.label(d, M + 14, y + round(big * 9 / 16) - 46, "Ракурс игрока у входа в зону")
    sw = W - 2 * M - big - 12
    sheet.paste(V.fit(V.load("arena6_approach.png"), sw, round(sw * 9 / 16)), (M + big + 12, y))
    V.label(d, M + big + 26, y + round(sw * 9 / 16) - 46, "Подход слева")
    ty = y + round(sw * 9 / 16) + 12
    sheet.paste(V.fit(V.load("arena6_lane.png"), sw, round(sw * 9 / 16)), (M + big + 12, ty))
    V.label(d, M + big + 26, ty + round(sw * 9 / 16) - 46, "Боковая дорожка насквозь")
    y += round(big * 9 / 16) + 16
    top_w = big
    sheet.paste(V.fit(V.load("arena6_top.png"), top_w, round(top_w * 9 / 16)), (M, y))
    V.label(d, M + 14, y + round(top_w * 9 / 16) - 46, "Зона сверху: вход внизу, выход вверху")
    d.rectangle((M + big + 12, y, W - M, y + round(top_w * 9 / 16)), fill=PANEL)
    yy = y + 14
    d.text((M + big + 30, yy), "Свободный бег и схема", font=V.font(28, True), fill=ACC)
    yy += 52
    legend = (((61, 255, 122), "зелёные рамки — свободные пути: две дорожки 14 стадов насквозь (x ±42), центральный "
                               "путь к площадке, перемычки к дорожкам"),
              ((255, 255, 255), "пунктир — круг боя r 34: выше 2 ничего нет"),
              ((255, 48, 72), "красные кольца — 4 места существ"))
    for col, text in legend:
        d.rectangle((M + big + 30, yy + 8, M + big + 74, yy + 20), fill=col)
        yy = V.para(d, M + big + 88, yy, text, sw - 100, size=20, fill=INK) + 8
    free = "проверка скриптом: на путях ничего выше 0.6 — да" if st.get("free_lanes") == "ok" else \
        f"проверка скриптом: помехи на путях — {st.get('free_lanes')}"
    notes = ["По замечанию к «Леднику»: пройти зону насквозь можно, никуда не сворачивая; декор — только в боковых "
             "полосах |x| 54…90 и за храмом, бордюр площадки — мох ниже 0.6 (перешагивается).",
             free + ".",
             f"Примитивов в черновой сцене: {st['total']} (без босса и существ); в игре крупное (храм, скалы, деревья) — "
             "мешами, оценка ≈ 600–750 частей, в пределах ~800 на зону (D64)."]
    for ln in notes:
        yy = V.para(d, M + big + 30, yy, ln, sw - 36, size=20, fill=DIM) + 8
    y += round(top_w * 9 / 16) + 16
    blocks = [
        ("Задник", ["• Ступенчатый храм-сад из зелёного камня: 4 уступа с мхом и цветами, лианы с листиками.",
                    "• Узоры — листья-ромбы (вымышленные, без религиозных символов и лиц).",
                    "• За королевой — арка из корней, ниша задёрнута лианами, над ней нефритовый самоцвет; "
                    "наверху — чаша с огромным цветком, по бокам — вазы с цветами."]),
        ("Площадка и бока", ["• Терраса — серо-зелёный камень с мхом и цветочной мозаикой, бордюр из мха.",
                             "• Водопады со скал в пруды с кувшинками (по одному с каждой стороны), деревья с "
                             "кронами и лианами, пальмы, гигантские цветы, грибы-зонтики, монстеры, клумбы у входа.",
                             "• Деревянный настил дорожек — светлые и тёмные доски, низкий бортик."]),
        ("Что изменилось после «Ледника»", ["• Нет препятствий на пути к следующему уровню: прямые дорожки "
                                            "от входа до выхода, без табличек и декора на них.",
                                            "• Без неба-«радуги» и неоновых полос: небо — обычное голубое.",
                                            "• Частиц нет; свечение — только нефрит и самоцветы короны."]),
    ]
    bottom = text_blocks(sheet, d, y, blocks)
    sheet = sheet.crop((0, 0, W, bottom + M))
    sheet.save(os.path.join(OUT, "2_arena.png"))
    return sheet.size


SIGNS = {  # D64 п. 1 — признаки вида и шутка в теле
    "FrogBubble": "горловой мешок больше самой лягушки, глаза навыкате. Признаки: глаза-бугры на макушке, рот-щель, "
                  "сложенные задние лапы, пальцы-подушечки",
    "BigBeakToucan": "клюв вдвое длиннее тела — откинулся на хвост. Признаки: трёхцветный клюв, чёрное тело и белое "
                     "горло, голубое кольцо у глаза, лапы 2+2",
    "PeriscopeChameleon": "глаза на стебельках смотрят в разные стороны. Признаки: шлем-гребень, сплюснутое тело с "
                          "полосами, лапы-клещи, хвост спиралью",
    "KnotSloth": "завязал лапы узлом над головой и уснул. Признаки: светлая маска и тёмные полосы от глаз, длинные "
                 "когти, мох в шерсти",
    "ManyEyeCaterpillar": "на каждом сегменте глаза со своим настроением. Признаки: сегменты-кольца, ложноножки, "
                          "усики, дыхальца",
    "WheelMonkey": "хвост свернулся обручем — сидит в нём, как в колесе. Признаки: маска, круглые уши, длинные руки, "
                   "цепкий хвост, хохолок",
    "ThreeHeadParrot": "три головы разных цветов говорят разом. Признаки: крючковатые клювы, хохолки, лапы 2+2, "
                       "хвост из длинных перьев",
    "TowerBeetle": "на роге жука — жук поменьше, на его роге — малыш. Признаки: рог, надкрылья со швом, 6 лап, усики",
    "FlowerJaguar": "вместо пятен-розеток — цветы, кончик хвоста — бутон. Признаки: мощное кошачье тело, круглые "
                    "уши, длинный хвост, усы",
    "SproutFlytrap": "малыш-мухоловка на ножках-корнях под листом-зонтиком, корона набекрень (не копия королевы). "
                     "Признаки: створки с ресничками, стебель, листья, корни",
}


def collection():
    sys.path.insert(0, HERE)
    sheet = Image.new("RGB", (W, 3200), BG)
    d = ImageDraw.Draw(sheet)
    header(d, "Коллекция джунглей босса 6 — 10 эскизов из 30",
           "Странные и смешные звери джунглей: смешное в самом теле, без бытовых вещей (как утверждённая ледяная "
           "коллекция v2). Доля редкостей — как в коллекции 12 / 9 / 6 / 3 (D64).")
    y = 128
    card = (W - 2 * M - 4 * 12) // 5
    ids = list(SIGNS)
    reports = {}
    for name in os.listdir(CR):
        if name.startswith("report") and name.endswith(".json"):
            reports.update(json.load(open(os.path.join(CR, name), encoding="utf-8")))
    info_h = 250
    for i, item in enumerate(ids):
        rep = reports.get(item, {})
        x = M + (i % 5) * (card + 12)
        yy = y + (i // 5) * (card + info_h + 12)
        hero = os.path.join(CR, f"{item}_hero.png")
        if os.path.exists(hero):
            sheet.paste(V.fit(Image.open(hero).convert("RGB"), card, card), (x, yy))
        col = RARITY[rep.get("rarity", "Common")]
        d.rectangle((x, yy + card, x + card, yy + card + info_h), fill=PANEL)
        d.rectangle((x, yy + card, x + card, yy + card + 8), fill=col)
        d.text((x + 14, yy + card + 16), rep.get("title", item), font=V.font(25, True), fill=INK)
        d.text((x + 14, yy + card + 50), RARITY_RU[rep.get("rarity", "Common")], font=V.font(22, True), fill=col)
        V.para(d, x + 14, yy + card + 82, f"{SIGNS[item][0].upper()}{SIGNS[item][1:]}. "
               f"{rep.get('tris_without_stand', '?')} треуг.", card - 28, size=18, fill=DIM)
    y += 2 * (card + info_h + 12) + 4
    d.rectangle((M, y, W - M, y + 130), fill=PANEL)
    V.para(d, M + 18, y + 14, "Эскизы собраны конвейером существ (части с точками вращения, проверка суставов D64, "
                             "лица с эмоцией); на шаге 2 — каталог всех 30 на «ок», затем чистовые модели и карты "
                             "(Common 512², Rare и выше 1024²). Не больше 3 существ одной семьи силуэтов; без людей, "
                             "текста, логотипов, оружия, бытовых вещей и чужих персонажей.",
           W - 2 * M - 36, size=21, fill=INK)
    sheet = sheet.crop((0, 0, W, y + 130 + M))
    sheet.save(os.path.join(OUT, "3_collection.png"))
    return sheet.size


if __name__ == "__main__":
    print(boss(), arena(), collection())
