"""D48-C, фаза 1 — листы для утверждения планировки на 20 мест: план с размерами и номерами мест, этапы открытия по
уровням, зоны защиты, сравнение вариантов A / B / C, бюджет деталей и сводный лист кадров. Собирает рендеры
scripts/blender/d48c_museum.py и раскладку scripts/blender/d48c_layout.py; в игру ничего не попадает.

План L*_plan.png: 1300², орто 66 стадов, центр (x 0, z −0.6), вход (−z) внизу, +x участка — слева.
Запуск: python scripts/d48c_sheets.py  → assets/concepts/d48/c1/sheets/*.png
"""

import glob
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "blender"))
import d48c_layout as L  # noqa: E402

C1 = os.path.join(ROOT, "assets", "concepts", "d48", "c1")
REN, OUT = os.path.join(C1, "renders"), os.path.join(C1, "sheets")
os.makedirs(OUT, exist_ok=True)
INK, GOLD, SOFT, WHITE = (24, 20, 46), (255, 214, 90), (205, 216, 245), (255, 255, 255)
SIZE, ORTHO, CZ = 1300, 66.0, -0.6
K = SIZE / ORTHO
STAGE = {1: (120, 220, 255), 4: (255, 214, 90), 5: (130, 235, 140), 6: (130, 235, 140), 7: (255, 160, 90),
         8: (255, 160, 90), 9: (235, 120, 220), 10: (235, 120, 220)}


def font(weight, size):
    path = None
    for p in sorted(glob.glob(os.path.expandvars(rf"%LOCALAPPDATA%\Roblox\Versions\*\content\fonts\Montserrat-{weight}.ttf"))):
        path = p
    return ImageFont.truetype(path, size)


def say(d, xy, body, size=26, fill=WHITE, anchor="mm", weight="Black", stroke=INK, sw=None):
    d.text(xy, body, font=font(weight, size), fill=fill, stroke_width=max(2, size // 8) if sw is None else sw,
           stroke_fill=stroke, anchor=anchor)


def px(x, z):
    return SIZE / 2 - x * K, SIZE / 2 - (z - CZ) * K


def rect(x0, x1, z0, z1):
    (ax, ay), (bx, by) = px(x0, z0), px(x1, z1)
    return (min(ax, bx), min(ay, by), max(ax, bx), max(ay, by))


def dim(d, a, b, body, offset=(0, 0), size=22, col=(255, 236, 140)):
    (x0, y0), (x1, y1) = a, b
    d.line([a, b], fill=col, width=4)
    for (x, y) in (a, b):
        if abs(x1 - x0) > abs(y1 - y0):
            d.line([(x, y - 12), (x, y + 12)], fill=col, width=4)
        else:
            d.line([(x - 12, y), (x + 12, y)], fill=col, width=4)
    say(d, ((x0 + x1) / 2 + offset[0], (y0 + y1) / 2 + offset[1]), body, size, col)


def gradient(w, h, top=(43, 58, 103), bot=(22, 28, 54)):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)))
    return img


def stage_color(level):
    return STAGE.get(level, STAGE[1] if level <= 3 else WHITE)


def rounded_paste(sheet, im, xy, r=18):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    sheet.paste(im, xy, mask)


# ── 1. План L10 с размерами, номерами мест и уровнями открытия ─────────────────────────────────────────────────
def plan_sheet():
    im = Image.open(os.path.join(REN, "L10_plan.png")).convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle(rect(-22, 22, -22, 22), outline=(255, 255, 255, 255), width=3)  # участок
    say(d, px(-21.5, 21.3), "участок 44 × 44", 18, anchor="rb", weight="Bold")
    d.rectangle(rect(-18, 18, -12.7, 20.7), outline=(90, 200, 255, 230), width=3)  # хранилище под залом
    say(d, px(0, 18.0), "хранилище внизу (36 × 33,4)", 17, (140, 220, 255), weight="Bold")
    for p in L.places():
        x, _, z = p["center"]
        cx, cy = px(x, z)
        col = stage_color(p["unlock_compat"])
        d.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=col + (235,), outline=INK, width=4)
        say(d, (cx, cy - 4), str(p["slot"]), 30, INK, stroke=col, sw=0)
        say(d, (cx, cy + 20), f"ур.{p['unlock_compat']}", 13, INK, stroke=col, sw=0, weight="Bold")
    say(d, px(0, 7.0), "ПАВИЛЬОН", 20)
    say(d, px(0, 5.2), "лестница вниз", 16, weight="Bold")
    say(d, px(-9.0, -7.0), "сундук", 17, weight="Bold")
    say(d, px(9.0, -7.0), "стенд", 17, weight="Bold")
    for sx in (-1, 1):
        say(d, px(sx * 17.3, -8.4), "арка", 16, (255, 236, 140), weight="Bold")
        say(d, px(sx * 23.5, -21.0), "ГАЛЕРЕЯ", 18, GOLD)
    dim(d, px(29, -24.6), px(-29, -24.6), "58 ст. по галереям (было 58 у крыльев D36)", (0, 24), 19)
    dim(d, px(18, 23.6), px(-18, 23.6), "36 ст. — главный зал (прежний контур)", (0, -22), 19)
    dim(d, px(31.0, -22.0), px(31.0, 20.7), "42,7", (24, 0), 19)
    dim(d, px(18.0, 13.0), px(22.0, 13.0), "4,0", (0, -18), 16, (140, 255, 160))
    dim(d, px(4.4, 13.0), px(10.7, 13.0), "6,3", (0, -18), 16, (140, 255, 160))
    dim(d, px(-3.2, -3.0), px(3.2, -3.0), "6,4", (0, -18), 16, (140, 255, 160))
    say(d, px(-10.5, -2.5), "проход", 15, (140, 255, 160), weight="Bold")
    sheet = Image.new("RGB", (SIZE, SIZE + 230), (24, 28, 48))
    sheet.paste(im, (0, 230))
    d = ImageDraw.Draw(sheet)
    say(d, (SIZE // 2, 46), "D48-C — музей на 20 мест (уровень 10)", 40)
    say(d, (SIZE // 2, 98), "Главный зал — 8 ниш (места 1–8). Галереи в объёме крыльев D36 — места 9–20, вход только "
                            "аркой из зала.", 21, SOFT, weight="Bold")
    say(d, (SIZE // 2, 132), "Галереи выходят за участок 44 × 44 (как нынешние крылья D36, до x ±29); до соседнего "
                             "музея — 17 ст.", 21, (255, 190, 120), weight="Bold")
    x = 120
    for label, lv in (("старт ур.1", 1), ("ниши 7–8 ур.4", 4), ("галереи ур.5–6", 5), ("ур.7–8", 7),
                      ("ур.9–10", 9)):
        d.ellipse((x, 168, x + 30, 198), fill=stage_color(lv), outline=INK, width=3)
        say(d, (x + 40, 183), label, 20, anchor="lm", weight="Bold")
        x += 245
    sheet = sheet.resize((sheet.width * 4 // 5, sheet.height * 4 // 5), Image.LANCZOS)
    sheet.save(os.path.join(OUT, "plan_20.png"))


# ── 2. Этапы открытия по уровням ───────────────────────────────────────────────────────────────────────────────
def stages_sheet():
    W, H = 1700, 900
    sheet = gradient(W, H)
    d = ImageDraw.Draw(sheet)
    say(d, (W // 2, 56), "Открытие мест по уровням музея", 44)
    say(d, (W // 2, 104), "D37: мест = 2 × уровень. Сейчас в коде 6 мест на любом уровне — предлагаю совместимо: "
                          "max(6, 2 × уровень)", 22, SOFT, weight="Bold")
    cols = ["Уровень", "D37", "Код сейчас", "Совместимо", "Что открывается / строится"]
    xs = [80, 260, 420, 640, 860]
    y = 160
    for x, c in zip(xs, cols):
        say(d, (x, y), c, 24, GOLD, anchor="lm")
    what = {1: "ниши 1–6; 4-я пара ниш — урны; углы входа — растения",
            2: "(по D37 — места 3–4)", 3: "(по D37 — места 5–6)",
            4: "ниши 7–8 вместо урн — зал полный: 8 ниш",
            5: "галереи и арки; места 9–10, остальные — «закрыто»",
            6: "места 11–12", 7: "места 13–14 (у портика)", 8: "места 15–16", 9: "места 17–18",
            10: "места 19–20 — все 20 открыты"}
    for lv in range(1, 11):
        y = 160 + lv * 62
        d.rounded_rectangle((60, y - 26, W - 60, y + 26), 18, fill=(30, 38, 72) if lv % 2 else (36, 46, 86))
        d.ellipse((90, y - 16, 122, y + 16), fill=stage_color(lv), outline=INK, width=3)
        say(d, (106, y), str(lv), 18, INK, stroke=stage_color(lv), sw=0)
        say(d, (xs[1] + 30, y), str(L.slots_d37(lv)), 24)
        say(d, (xs[2] + 60, y), "6", 24, (255, 150, 150))
        say(d, (xs[3] + 60, y), str(L.slots_compat(lv)), 24, (140, 255, 160))
        say(d, (xs[4], y), what[lv], 20, anchor="lm", weight="Bold")
    sheet.save(os.path.join(OUT, "stages_20.png"))


# ── 3. Зоны защиты ─────────────────────────────────────────────────────────────────────────────────────────────
def defense_sheet():
    tiles = []
    for level in (1, 10):
        name = os.path.join(REN, f"L{level}_plan.png")
        im = Image.open(name).convert("RGB")
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        z = L.defense_zones(level)
        for r in z["allowed"]:
            d.rectangle(rect(*r), fill=(80, 230, 120, 95), outline=(80, 230, 120, 255), width=3)
        for r in z["forbidden"]:
            d.rectangle(rect(*r), fill=(240, 70, 70, 70))
        for nm, las in L.LASERS.items():
            half = las["length"] / 2
            d.line([px(half, las["z"]), px(-half, las["z"])], fill=(255, 60, 60, 255), width=7)
            say(d, px(-half - 0.6, las["z"]), f"лазер: {'вход' if nm == 'Entrance' else 'галерея'}", 17,
                (255, 140, 140), anchor="rm", weight="Bold")
        d.rectangle(rect(-6, 6, -12.9, -12.1), fill=(80, 170, 255, 255))
        say(d, px(0, -14.4), "бронедверь", 18, (140, 200, 255), weight="Bold")
        im = Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB").resize((800, 800), Image.LANCZOS)
        tiles.append(im)
    W, H = 1700, 1080
    sheet = gradient(W, H)
    d = ImageDraw.Draw(sheet)
    say(d, (W // 2, 50), "Зоны защиты: уровень 1 и уровень 10", 42)
    say(d, (W // 2, 98), "Зелёное — свободная установка (ловушка, капкан, робот); красное — нельзя; лимит устройств "
                         "D37 не меняется", 21, SOFT, weight="Bold")
    for k, im in enumerate(tiles):
        rounded_paste(sheet, im, (40 + k * 840, 140))
        say(d, (440 + k * 840, 970), ("Уровень 1 — 6 мест, галерей нет", "Уровень 10 — 20 мест, галереи")[k], 26)
    say(d, (W // 2, 1030), "Галереи без устройств: проход 4 ст. — устройство перекрыло бы путь. Вход в галереи — "
                           "только через зал, мимо двери и лазеров.", 20, (255, 214, 90), weight="Bold")
    sheet.save(os.path.join(OUT, "defense_20.png"))


# ── 4. Варианты A / B / C ──────────────────────────────────────────────────────────────────────────────────────
def options_sheet():
    W, H = 1800, 980
    sheet = gradient(W, H)
    d = ImageDraw.Draw(sheet)
    say(d, (W // 2, 56), "Как разместить 20 мест — три варианта", 44)
    S = 7.2  # пикселей на стад в схемах

    def scheme(ox, oy, kind):
        def r(x0, x1, z0, z1, fill, outline=None):
            d.rectangle((ox - x1 * S, oy - z1 * S, ox - x0 * S, oy - z0 * S), fill=fill, outline=outline, width=2)
        r(-22, 22, -22, 22, None, (255, 255, 255))  # участок
        r(-18, 18, -12.7, 20.7, (232, 226, 210), (120, 110, 90))  # зал
        r(-16, 16, -23, -12.7, (215, 210, 196))  # портик
        r(-4.4, 4.4, 2.4, 11.6, (58, 90, 140))  # павильон
        r(-3.2, 3.2, -11.3, 2.4, (184, 40, 58))  # дорожка
        pts = []
        if kind == "A":
            for sx in (-1, 1):
                r(*sorted((sx * 18, sx * 29)), -6, 18, (210, 222, 240), (120, 130, 160))  # крылья D36: z −6…18
                pts += [(sx * 13.4, z) for z in (-1.6, 6.2, 14.0)] + [(sx * 24.7, z) for z in (-3, 3, 9, 15)]
        elif kind == "B":
            pts += [(sx * 13.4, z) for sx in (-1, 1) for z in L.NICHE_Z]
            pts += [(sx * 13.4, -8.4) for sx in (-1, 1)]
        else:
            for sx in (-1, 1):
                r(*sorted((sx * 18, sx * 29)), -22, 20.7, (210, 240, 214), (110, 160, 120))
                pts += [(sx * 13.4, z) for z in L.NICHE_Z] + [(sx * 24.7, z) for z in L.GAL_Z]
        for (x, z) in pts:
            cx, cy = ox - x * S, oy - z * S
            d.rectangle((cx - 2.7 * S, cy - 2.7 * S, cx + 2.7 * S, cy + 2.7 * S), fill=(255, 214, 90), outline=INK)
        return len(pts)

    cards = (("A", "A. Боковые крылья D36", "крылья как сейчас (z −6…18)",
              ["3 ниши у стен + 4 места в крыле", "14 мест — не хватает 6", "крылья уже утверждены (D36)"]),
             ("B", "B. Только внутри контура", "ниши по 4 у стен + углы входа",
              ["10 мест: больше не влезает", "углы входа: конфликт с сундуком", "центр зала — свободный"]),
             ("C", "C. Комбинированный ★", "8 ниш зала + 2 галереи по 6 (рекомендую)",
              ["20 мест, проходы ≥ 4 ст.", "галереи — вдоль портика до z −22", "вход только аркой из зала"]))
    for k, (kind, title, sub, notes) in enumerate(cards):
        x0 = 40 + k * 590
        d.rounded_rectangle((x0, 110, x0 + 560, 950), 30, fill=(30, 38, 72),
                            outline=GOLD if kind == "C" else (70, 84, 130), width=5 if kind == "C" else 2)
        n = scheme(x0 + 280, 470, kind)
        say(d, (x0 + 280, 150), title, 28, GOLD if kind == "C" else WHITE)
        say(d, (x0 + 280, 188), sub, 19, SOFT, weight="Bold")
        say(d, (x0 + 280, 760), f"{n} мест", 40, (140, 255, 160) if n >= 20 else (255, 150, 150))
        for i, line in enumerate(notes):
            say(d, (x0 + 280, 820 + i * 36), line, 20, weight="Bold")
    sheet.save(os.path.join(OUT, "options_20.png"))


# ── 5. Бюджет деталей ──────────────────────────────────────────────────────────────────────────────────────────
def budget_sheet():
    data = {lv: json.load(open(os.path.join(C1, "bricks", f"museum_L{lv}.json"), encoding="utf-8"))
            for lv in (1, 10) if os.path.exists(os.path.join(C1, "bricks", f"museum_L{lv}.json"))}
    l1, l10 = data[1]["total"], data[10]["total"]
    lights1, lights10 = len(data[1]["lights"]), len(data[10]["lights"])
    rows = [
        ("", "6 мест (ур. 1)", "20 мест (ур. 10)", "5 музеев × 20 мест"),
        ("Part-версия, как в концепте", f"{l1}", f"{l10}  > 400", f"{5 * l10}"),
        ("Part-версия, упрощённая (временная)", "≈ 250", "≈ 370", "≈ 1 850"),
        ("Mesh-версия (Blender-модули)", "≈ 70", "≈ 115", "≈ 575"),
        ("Экспонаты (1–3 MeshPart каждый)", "6–18", "20–60", "100–300"),
        ("Защита в Судную ночь (≤ 5 × 16–35)", "≤ 150", "≤ 150", "≤ 750"),
        ("Свет: как в концепте → по правилу", f"{lights1} → 11", f"{lights10} → 15", "135 → 75, видно ≈ 25"),
    ]
    W, H = 1700, 760
    sheet = gradient(W, H)
    d = ImageDraw.Draw(sheet)
    say(d, (W // 2, 54), "Бюджет: детали и свет на музей и на сервер", 42)
    say(d, (W // 2, 100), "Part-версия — точный счёт по выгрузке; упрощённая и Mesh — оценка до моделей фазы 2; "
                          "карта сейчас ≈ 4 700 деталей, лимит 12 000", 20, SOFT, weight="Bold")
    xs = [70, 760, 1050, 1340]
    for r, row in enumerate(rows):
        y = 160 + r * 76
        if r:
            d.rounded_rectangle((50, y - 30, W - 50, y + 30), 16, fill=(30, 38, 72) if r % 2 else (36, 46, 86))
        for c, cell in enumerate(row):
            col = GOLD if r == 0 else ((255, 150, 150) if "> 400" in cell else WHITE)
            say(d, (xs[c], y), cell, 22 if c == 0 else 24, col, anchor="lm", weight="Bold" if c == 0 and r else
                "Black")
    say(d, (W // 2, 690), "Упрощение Part-версии: постамент 5 деталей, ниша 3, декор хранилища −65; Mesh: модуль = "
                          "1 MeshPart + табличка + свет", 20, (255, 214, 90), weight="Bold")
    say(d, (W // 2, 725), "Правило света: прожектор — только у занятых ниш зала; в галерее — 1 PointLight; свет "
                          "хранилища — только когда свой игрок внизу", 20, (255, 214, 90), weight="Bold")
    sheet.save(os.path.join(OUT, "budget_20.png"))


# ── 6. Сводный лист кадров ─────────────────────────────────────────────────────────────────────────────────────
SHOTS = [("L1_hall_from_entrance", "Ур. 1: зал от входа — 6 мест"), ("L1_overview", "Ур. 1: зал сверху"),
         ("L1_exterior", "Ур. 1: снаружи — как сейчас"), ("L10_hall_inside", "Ур. 10: 8 ниш зала"),
         ("L10_overview", "Ур. 10: зал и галереи сверху"), ("L10_exterior", "Ур. 10: галереи вдоль портика"),
         ("L10_gallery", "Ур. 10: галерея, 6 мест"), ("L10_gallery_arch", "Арка из входного зала"),
         ("L5_gallery", "Ур. 5: галерея — 1 место открыто, 5 закрыто"),
         ("L10_hall_toward_entrance", "Ур. 10: к выходу, арки"), ("L10_hall_from_entrance", "Ур. 10: от входа"),
         ("L5_overview", "Ур. 5: галереи построены")]


def contact():
    cw, ch, cols = 560, 315, 3
    shots = [s for s in SHOTS if os.path.exists(os.path.join(REN, s[0] + ".png"))]
    rows = (len(shots) + cols - 1) // cols
    W, H = cols * cw + (cols + 1) * 24, 150 + rows * (ch + 70)
    sheet = gradient(W, H)
    d = ImageDraw.Draw(sheet)
    say(d, (W // 2, 58), "D48-C — музей до 20 мест: уровни 1, 5, 10", 44)
    say(d, (W // 2, 106), "временная геометрия из деталей Roblox для проверки планировки (не финальная графика)", 22,
        SOFT, weight="Bold")
    for k, (name, caption) in enumerate(shots):
        r, c = divmod(k, cols)
        x, y = 24 + c * (cw + 24), 150 + r * (ch + 70)
        im = Image.open(os.path.join(REN, name + ".png")).convert("RGB").resize((cw, ch), Image.LANCZOS)
        rounded_paste(sheet, im, (x, y))
        say(d, (x + cw // 2, y + ch + 30), caption, 22)
    sheet.save(os.path.join(OUT, "contact_20.png"))


if __name__ == "__main__":
    plan_sheet()
    stages_sheet()
    defense_sheet()
    options_sheet()
    budget_sheet()
    contact()
    print("ok")
