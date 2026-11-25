"""Листы концепта босса 6 «Джунгли» v2 (шаг 3 D64): босс, арена, коллекция джунглей — для утверждения владельцем.

  python scripts/blender/boss6/sheet.py
  → assets/concepts/bosses_5_10/boss6_v2/{1_boss,2_arena,3_collection}.png (вне git)
Кадры и числа v2 — из boss6_v2/raw/ (render.py, arena.py, creatures.py); для сравнения v1 — из boss6_v2/v1/raw/
(копия кадров v1, отправленных владельцу 2026-11-24). Оформление — как листы босса 5.
"""

import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))  # scripts/blender
import stand_colors as SC  # noqa: E402  (D71: цвета редкостей из UITokens)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "dragon10"))
sys.path.insert(0, HERE)
import v7_sheet as V  # noqa: E402  (font, fit, para, label, silhouette — общие помощники листов)

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss6_v2")
RAW = os.path.join(OUT, "raw")
RAW1 = os.path.join(OUT, "v1", "raw")
CR = os.path.join(RAW, "creatures")
CR1 = os.path.join(RAW1, "creatures")
V.RAW = RAW
BG, PANEL, INK, DIM, ACC = V.BG, V.PANEL, V.INK, V.DIM, V.ACC
W, M = 2400, 24
RARITY = {k: SC.rgb(SC.RARITY[k][1]) for k in ("Common", "Rare", "Epic", "Legendary")}  # D71: из UITokens
RARITY_RU = {"Common": "Обычное", "Rare": "Редкое", "Epic": "Эпическое", "Legendary": "Легендарное"}
V1_TAG, V2_TAG = (120, 120, 132), (61, 200, 110)


def header(d, title, sub):
    d.rectangle((0, 0, W, 110), fill=PANEL)
    d.text((30, 12), title, font=V.font(44, True), fill=INK)
    d.text((32, 70), sub, font=V.font(23), fill=DIM)


def load(name):
    """Кадр v2 по имени или любой кадр по полному пути."""
    return Image.open(name if os.path.isabs(name) else os.path.join(RAW, name)).convert("RGB")


def tag(d, x, y, text, col):
    """Плашка «v1» / «v2» в углу кадра."""
    f = V.font(30, True)
    tw = d.textlength(text, font=f)
    d.rectangle((x, y, x + tw + 24, y + 44), fill=col)
    d.text((x + 12, y + 3), text, font=f, fill=(255, 255, 255))


def tiles(sheet, d, y, items, size, gap=12, h=None):
    """Ряд кадров; items = [(файл, подпись[, «v1»/«v2»])]."""
    h = h or size
    for i, it in enumerate(items):
        name, text = it[0], it[1]
        x = M + i * (size + gap)
        sheet.paste(V.fit(load(name), size, h), (x, y))
        V.label(d, x + 12, y + h - 44, text)
        if len(it) > 2:
            tag(d, x + 10, y + 10, it[2], V1_TAG if it[2] == "v1" else V2_TAG)
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


def section(d, y, title, sub=""):
    """Заголовок раздела во всю ширину."""
    d.rectangle((M, y, W - M, y + 56), fill=PANEL)
    d.text((M + 18, y + 8), title, font=V.font(30, True), fill=ACC)
    if sub:
        tw = d.textlength(title, font=V.font(30, True))
        d.text((M + 40 + tw, y + 14), sub, font=V.font(22), fill=DIM)
    return y + 68


def boss():
    st = json.load(open(os.path.join(RAW, "stats.json"), encoding="utf-8"))
    sheet = Image.new("RGB", (W, 7000), BG)
    d = ImageDraw.Draw(sheet)
    header(d, "Босс 6 · Джунгли — Королева-мухоловка · v2",
           "Переделано по замечаниям к v1: не «платье», а настоящая мухоловка — тёмный стебель, клубень и розетка "
           "листьев; пасть-ловушка; сразу игровая копия ≤ 8 000 треугольников.")
    y = 128
    y = tiles(sheet, d, y, (("stand_front.png", "1. Спереди"), ("stand_side.png", "2. Сбоку — створки полукругом"),
                            ("stand_back.png", "3. Сзади — мантия из трёх листов"), ("stand_34.png", "4. 3/4")), 579)
    y = tiles(sheet, d, y, (("sleep_34.png", "5. Сон — ловушка сомкнута"),
                            ("combat_34.png", "6. Бой — «Захлоп», бутоны раскрылись"),
                            ("defeat_34.png", "7. Поражение — увяла")), 776)
    y = tiles(sheet, d, y, (("head_front.png", "8. Лицо и пасть"), ("head_34.png", "8. Голова — 3/4"),
                            ("collar.png", "9. Амулет на стебле"), ("buds.png", "10. Фрейлина — бутон"),
                            ("buds_combat.png", "11. Фрейлина в бою")), 460)
    sil_w = 560
    for i, (name, text) in enumerate((("stand_front_sil.png", "Силуэт спереди"),
                                      ("stand_side_sil.png", "Силуэт сбоку"))):
        x = M + i * (sil_w + 12)
        sheet.paste(V.contain(V.silhouette(name), sil_w, 600), (x, y))
        V.label(d, x + 12, y + 556, text)
    px = M + 2 * (sil_w + 12)
    d.rectangle((px, y, W - M, y + 600), fill=PANEL)
    d.text((px + 18, y + 12), "Палитра", font=V.font(28, True), fill=ACC)
    pal = (("trap", "Створки снаружи — тёмно-зелёный"), ("maw", "Нутро пасти — малиновый"),
           ("rim", "Кант створок"), ("teeth", "Реснички — короткие, тупые"), ("face", "Лицо — светлое"),
           ("pod", "Бутон головы"), ("stem", "Стебель-ствол — тёмный"), ("vine", "Руки-лозы — светлые"),
           ("leafD", "Мантия — три листа"), ("leafL", "Розетка листьев на земле"), ("root", "Клубень"),
           ("petal", "Венчик, бутоны-фрейлины"), ("gold", "Корона, амулет — золото"), ("neonGem", "Самоцветы"))
    palette = st["palette"]
    for i, (k, text) in enumerate(pal):
        yy = y + 58 + i * 38
        code = palette[k]
        d.rectangle((px + 18, yy, px + 56, yy + 30), fill=tuple(int(code[j:j + 2], 16) for j in (0, 2, 4)),
                    outline=(10, 10, 14))
        d.text((px + 68, yy + 1), f"{text}  #{code}", font=V.font(20), fill=INK)
    nx = px + 600
    d.text((nx, y + 12), "Числа", font=V.font(28, True), fill=ACC)
    tris = [st[p]["tris"] for p in ("stand", "sleep", "combat", "defeat")]
    grp = st["stand"].get("tris_by_group", {})
    lines = [f"Рост в стойке {st['stand']['size_studs'][2]} стада (как Йети), ширина с розеткой "
             f"{st['stand']['size_studs'][0]}, масштаб модели ×{st['export_scale']}.",
             "Это уже игровая копия: стойка {0}, сон {1}, бой {2}, поражение {3} треугольников — "
             "все ≤ 8 000 (v1 — ≈ 14 800).".format(*tris),
             "Части рига: " + ", ".join(f"{k} {v}" for k, v in grp.items()) + " треуг.",
             f"Перевёрнутых граней {st['stand']['flipped']}, совпадающих граней {len(st['stand']['coplanar'])}."]
    yy = y + 62
    for ln in lines:
        yy = V.para(d, nx, yy, ln, W - M - nx - 18, size=21, fill=INK) + 10
    y += 616
    y = section(d, y, "v1 → v2", "те же камеры: слева то, что было, справа — по замечаниям")
    p1 = lambda n: os.path.join(RAW1, n)  # noqa: E731
    y = tiles(sheet, d, y, ((p1("stand_front.png"), "Спереди", "v1"), ("stand_front.png", "Спереди", "v2"),
                            (p1("stand_side.png"), "Сбоку", "v1"), ("stand_side.png", "Сбоку", "v2")), 579)
    y = tiles(sheet, d, y, ((p1("head_front.png"), "Пасть", "v1"), ("head_front.png", "Пасть", "v2"),
                            (p1("buds.png"), "Фрейлины", "v1"), ("buds.png", "Фрейлины", "v2")), 579)
    blocks = [
        ("Что исправлено", ["• Нет «платья»: юбки, корсажа и тонкой талии нет. Толстый тёмный стебель-ствол, внизу "
                            "бурый клубень и розетка из огромных светлых листьев на земле, как у настоящей мухоловки.",
                            "• Пасть — ловушка: две короткие округлые створки на петле, сбоку вместе — круг. "
                            "Ресничек вдвое меньше (по 8 на створку, у петли их нет), они короче и тупые. Внутри малиновый, язык.",
                            "• Цвет по светлоте: створки тёмные с малиновым кантом, лицо и бутон головы светлые, "
                            "стебель и мантия тёмные, руки-лозы светлые на тёмном. Акценты — золото и розовый.",
                            "• Мантия — три изогнутых листа-плаща с жилками и золотой застёжкой.",
                            "• Фрейлины — закрытые розовые бутоны в чашелистиках, без лиц; раскрываются только в бою.",
                            "• Сразу игровая копия ≤ 8 000 треугольников."]),
        ("Бой и позы", ["• Не ходит (D64 п. 5): вросла в террасу, поворачивается на месте, как дракон; удар — "
                        "от контура тела (BodyRange), как у Йети и дракона.",
                        "• Основная атака — «Захлоп»: голова бросается вперёд, створки захлопываются, язык наружу.",
                        "• Особая — только анимация (D64): «Лиановый вихрь» — руки-лозы хлещут по кругу, бутоны "
                        "раскрываются и щёлкают.",
                        "• Сон: ловушка сомкнута «застёжкой» ресничек, глаза закрыты, капля росы, «Z». Поражение: "
                        "стебель клонится, глаза-крестики, язык набок, корона на земле."]),
        ("Модерация и игра", ["• Нет людей, картин, текста, логотипов, оружия и чужих персонажей; узоры — листья "
                              "и цветы. Злая, но смешная: брови, крестики, язык.",
                              "• Сила, HP, урон — как у боссов 1–5 по D56 (Progression.Bosses[6]); Closed до общего "
                              "выпуска (D64 п. 7).",
                              "• После «ок»: 10 клипов, 30 существ, арена, подключение — тем же конвейером, что Йети."]),
    ]
    bottom = text_blocks(sheet, d, y, blocks)
    sheet = sheet.crop((0, 0, W, bottom + M))
    sheet.save(os.path.join(OUT, "1_boss.png"))
    return sheet.size


def arena():
    st = json.load(open(os.path.join(RAW, "arena6_stats.json"), encoding="utf-8"))
    sheet = Image.new("RGB", (W, 5000), BG)
    d = ImageDraw.Draw(sheet)
    header(d, "Арена 6 · Джунгли — храм Королевы-мухоловки · v2",
           "Зона 184 × 95 стадов (каркас MapLayout). Королева — поза сна, на местах — по одному существу каждой "
           "редкости. Черновая сцена в Blender.")
    y = 128
    big = 1500
    bh = round(big * 9 / 16)
    sheet.paste(V.fit(load("arena6_player.png"), big, bh), (M, y))
    V.label(d, M + 14, y + bh - 46, "Главный кадр — ракурс игрока у входа в зону")
    tag(d, M + 10, y + 10, "v2", V2_TAG)
    sw = W - 2 * M - big - 12
    shh = round(sw * 9 / 16)
    sheet.paste(V.fit(load("arena6_approach.png"), sw, shh), (M + big + 12, y))
    V.label(d, M + big + 26, y + shh - 46, "Подход сбоку")
    ty = y + shh + 12
    sheet.paste(V.fit(load("arena6_lane.png"), sw, shh), (M + big + 12, ty))
    V.label(d, M + big + 26, ty + shh - 46, "Мостки — сквозная полоса")
    y += bh + 16
    sheet.paste(V.fit(load("arena6_top.png"), big, bh), (M, y))
    V.label(d, M + 14, y + bh - 46, "Зона сверху: вход внизу, выход вверху")
    d.rectangle((M + big + 12, y, W - M, y + bh), fill=PANEL)
    yy = y + 14
    d.text((M + big + 30, yy), "Свободный бег (D66)", font=V.font(28, True), fill=ACC)
    yy += 52
    legend = (((61, 255, 122), "зелёные рамки — свободные пути: две полосы-мостки |x| 48–66 (18 стадов) насквозь от "
                               "входа до выхода, центральная дамба к площадке, перемычки к полосам"),
              ((255, 255, 255), "пунктир — круг боя r 34"),
              ((255, 48, 72), "красные кольца — 4 места существ"))
    for col, text in legend:
        d.rectangle((M + big + 30, yy + 8, M + big + 74, yy + 20), fill=col)
        yy = V.para(d, M + big + 88, yy, text, sw - 100, size=20, fill=INK) + 8
    ok = st.get("free_lanes") == "ok"
    walls = st.get("walls_solid_le_24")
    if st.get("exit_lanes") not in (None, "ok"):
        ok = False
    notes = [("Проверка скриптом: в полосах и на путях нет твёрдого на высоте 1.1–7 — да." if ok else
              f"Проверка скриптом: помехи на путях — {st.get('free_lanes')}."),
             "Над полосами — кроны и арки выше 7, лианы не ниже 7: бежать можно, не сворачивая."]
    if walls is not None:
        notes.append("Твёрдое у стен (|x| > 76) не выше 24 — " + ("да." if walls in ("ok", True) else f"{walls}."))
    gp, gm = st.get("game_parts_total"), st.get("game_tris_no_bevel_total")
    if gp:
        notes.append(f"Игра: ≈ {gp} частей (бюджет {st.get('game_parts_budget', 800)}) — крупная листва, храм, корни, "
                     f"мостки — мешами; ≈ {round(gm / 1000)} тыс. треугольников без фасок" +
                     ("." if st.get("zone_tris_ok") else
                      f" (цель {round(st.get('zone_tris_target', 200000) / 1000)} тыс. — в игровой копии лианы проще)."))
    for ln in notes:
        yy = V.para(d, M + big + 30, yy, ln, sw - 36, size=20, fill=DIM) + 8
    y += bh + 16
    y = section(d, y, "v1 → v2", "ракурс игрока: было «зелёное на зелёном» и парк — стали храм, болото и джунгли")
    half = (W - 2 * M - 12) // 2
    hh = round(half * 9 / 16)
    for i, (path, t, text) in enumerate(((os.path.join(RAW1, "arena6_player.png"), "v1", "Было"),
                                         ("arena6_player.png", "v2", "Стало"))):
        x = M + i * (half + 12)
        sheet.paste(V.fit(load(path), half, hh), (x, y))
        tag(d, x + 10, y + 10, t, V1_TAG if t == "v1" else V2_TAG)
        V.label(d, x + 14, y + hh - 46, text)
    y += hh + 16
    blocks = [
        ("Задник — храм", ["• Босс — главное пятно: ступенчатый храм из тёплого песчаника и терракоты со мхом, "
                           "за королевой — тёмный проём, над ней светлая перемычка, а не зелень.",
                           "• Корень ползёт по уступам храма, рельефы — листья-ромбы и спирали (без лиц и "
                           "религиозных символов).",
                           "• За храмом — сплошная стена тёмных джунглей и туманный лес, неба-«парка» нет."]),
        ("Джунгли и болото", ["• Над полосами нависают кроны-груды, с них свисают лианы (не ниже 7); у входа — "
                              "рамка из высокой травы, папоротников и банановых листьев.",
                              "• Площадка — остров в мелком болоте с ряской и кувшинками; полосы и перемычки — "
                              "деревянные мостки над водой, к площадке — дамба из песчаника.",
                              "• Зеленоватая дымка — за храмом и по краям, тёплый свет; передний план чистый."]),
        ("Проход и бюджет", ["• Полосы |x| 48–66 — прямо от входа до выхода (как в «Пустыне» и «Леднике»); "
                             "выход — туннель из корней и лиан с низом выше 7.",
                             "• Весь декор — у стен (|x| > 66) или в середине вне круга боя; у стен твёрдое не выше "
                             "24, выше — листва без столкновений.",
                             "• Крупная листва, храм, корни и мостки — мешами, ≤ 800 частей на зону."]),
    ]
    bottom = text_blocks(sheet, d, y, blocks)
    sheet = sheet.crop((0, 0, W, bottom + M))
    sheet.save(os.path.join(OUT, "2_arena.png"))
    return sheet.size


SIGNS = {  # D64 п. 1 — признаки вида и шутка в теле
    "FrogBubble": "древолаз: ядовито-красный с синими лапами и чёрными пятнами, раздул круглый прозрачный мешок из-под "
                  "подбородка. Признаки: глаза-бугры, самодовольная ухмылка, пальцы-подушечки",
    "BigBeakToucan": "клюв больше тела — откинулся на хвост. Признаки: трёхцветный клюв, чёрное тело и белое горло, "
                     "голубое кольцо у глаза, лапы 2+2",
    "RainbowChameleon": "весь в радужных полосах, один глаз-башенка смотрит на игрока, другой в небо. Признаки: "
                        "шлем-гребень, плотное тело, лапы-клещи на ветках, хвост спиралью",
    "KnotSloth": "завязал лапы узлом над головой и уснул. Признаки: светлая маска и тёмные полосы от глаз, длинные "
                 "когти, мох в шерсти",
    "ManyEyeCaterpillar": "жёлто-чёрная, одна хитрая голова в чёрной маске, а на каждом сегменте — ложный глазок, как у "
                          "настоящих гусениц. Признаки: сегменты с поясами, ложноножки, щетинки, рожки",
    "WheelMonkey": "хвост свернулся обручем — сидит в нём, как в колесе. Признаки: маска, круглые уши, длинные руки, "
                   "цепкий хвост, хохолок",
    "ThreeHeadParrot": "три головы разных цветов и настроений — единственный «многоголовый». Признаки: крючковатые "
                       "клювы, хохолки, лапы 2+2, хвост из длинных перьев",
    "AntStrongman": "выжал над головой лист в 10 раз больше себя, стиснул зубы и вспотел. Признаки: три отдела тела, "
                    "тонкая талия, 6 лап, коленчатые усики, жвалы",
    "FlowerJaguar": "вместо пятен — крупные яркие цветы, цветок за ухом, хвост зацвёл. Признаки: мощное кошачье тело, "
                    "круглые уши, длинный хвост, усы",
    "SproutFlytrap": "мини-копия мамы и самый высокий: розовый венчик, золотая корона со светящимся самоцветом, "
                     "ловушка с короткими ресничками, тёмный стебель, клубень и розетка листьев-ловушек",
}
REPLACED = {"PeriscopeChameleon": "RainbowChameleon", "TowerBeetle": "AntStrongman"}


def reports(folder):
    out = {}
    for name in sorted(os.listdir(folder)):
        if name.startswith("report") and name.endswith(".json"):
            out.update(json.load(open(os.path.join(folder, name), encoding="utf-8")))
    return out


def collection():
    sheet = Image.new("RGB", (W, 4200), BG)
    d = ImageDraw.Draw(sheet)
    header(d, "Коллекция джунглей босса 6 — 10 эскизов из 30 · v2",
           "Странные и смешные звери джунглей: смешное в самом теле. Яркие, не «зелёное на зелёном»; доля "
           "редкостей — как в коллекции 12 / 9 / 6 / 3 (D64).")
    y = 128
    card = (W - 2 * M - 4 * 12) // 5
    rep2 = reports(CR)
    info_h = 270
    for i, item in enumerate(SIGNS):
        rep = rep2.get(item, {})
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
    y = section(d, y, "v1 → v2", "сверху то, что было; замены: «Башня жуков» → Муравей-силач, хамелеон — радужный")
    rep1 = reports(CR1)
    small = (W - 2 * M - 9 * 8) // 10
    ids1 = list(rep1) or list(SIGNS)
    for row, (folder, reps, ids, t) in enumerate(((CR1, rep1, ids1, "v1"), (CR, rep2, list(SIGNS), "v2"))):
        for i, item in enumerate(ids[:10]):
            x = M + i * (small + 8)
            yy = y + row * (small + 50)
            hero = os.path.join(folder, f"{item}_hero.png")
            if os.path.exists(hero):
                sheet.paste(V.fit(Image.open(hero).convert("RGB"), small, small), (x, yy))
            V.para(d, x + 4, yy + small + 4, reps.get(item, {}).get("title", item), small - 8, size=16, fill=INK)
        tag(d, M + 6, y + row * (small + 50) + 6, t, V1_TAG if t == "v1" else V2_TAG)
    y += 2 * (small + 50) + 8
    d.rectangle((M, y, W - M, y + 180), fill=PANEL)
    V.para(d, M + 18, y + 14, "Что изменилось: «много голов» — только у попугая; вместо «башни жуков» — муравей-силач с "
                             "листом; лягушка — красно-синий древолаз с круглым прозрачным мешком, хамелеон — "
                             "радужный, с глазами-башенками и хвостом-спиралью, гусеница — жёлто-чёрная; ягуар в "
                             "цветах уложен в 3 000 треугольников; Росток — мини-копия мамы с короной и светящимся "
                             "самоцветом, самый высокий. Тукан, ленивец, обезьяна-колесо, попугай — как были. Каждое "
                             "существо ≤ 3 000 треугольников, суставы проверены (D64); без людей, текста, логотипов, "
                             "оружия и чужих персонажей.",
           W - 2 * M - 36, size=21, fill=INK)
    sheet = sheet.crop((0, 0, W, y + 180 + M))
    sheet.save(os.path.join(OUT, "3_collection.png"))
    return sheet.size


if __name__ == "__main__":
    print(boss(), arena(), collection())
