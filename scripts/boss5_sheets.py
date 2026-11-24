"""Листы босса 5 на просмотр владельцу перед загрузкой в Roblox (шаг 2 D64): коллекция, Йети и клипы, все карты.

  python scripts/boss5_sheets.py
  → assets/concepts/boss5/sheets/1_collection.png — 30 существ: имя, редкость, «вау», доход, треугольники, вес D58;
    2_yeti.png — игровая модель (позы) и раскадровки 10 клипов;
    maps_yeti.png и maps_creatures_<n>.png — каждая карта отдельно (цвет и нормали рядом), подписи — имя файла.
  Пишет и assets/concepts/boss5/sheets/weights.json — габарит без подставки и класс веса D58 по rig.json.
Кадры — assets/concepts/boss5/{creatures,yeti_game,anim}/ (art_glacier.py, boss5_yeti.py, boss5_yeti_anim.py).
"""

import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = os.path.join(ROOT, "assets", "concepts", "boss5")
OUT = os.path.join(C, "sheets")
MODELS = os.path.join(ROOT, "assets", "models", "art", "boss5")
TEX = os.path.join(ROOT, "assets", "textures", "art")
BG, PANEL, INK, DIM, ACC = (22, 24, 33), (35, 38, 51), (240, 242, 248), (165, 170, 188), (255, 196, 64)
RARITY = {"Common": (173, 166, 180), "Rare": (61, 142, 224), "Epic": (154, 62, 240), "Legendary": (245, 162, 21)}
RU = {"Common": "Обычное", "Rare": "Редкое", "Epic": "Эпическое", "Legendary": "Легендарное"}
W, M = 2400, 24


def font(size, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf", size)


def fit(im, w, h):
    k = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def header(d, title, sub):
    d.rectangle((0, 0, W, 110), fill=PANEL)
    d.text((30, 12), title, font=font(44, True), fill=INK)
    d.text((32, 70), sub, font=font(23), fill=DIM)


def catalog():
    """Строки каталога: id → (№, редкость, «вау», имя, доход)."""
    rows = {}
    for line in open(os.path.join(ROOT, "docs", "BOSS5_CATALOG.md"), encoding="utf-8"):
        m = re.match(r"^\| (\d+) \| (Common|Rare|Epic|Legendary) \| (\d+) \| ([^|]+)\| (\w+) \|.*\| ([\d\u00a0 ]+) \|", line)
        if m:
            rows[m.group(5)] = (int(m.group(1)), m.group(2), int(m.group(3)), m.group(4).strip(),
                                m.group(6).replace("\u00a0", " ").strip())
    return rows


def weight(item_id):
    """Наибольший габарит без подставки (стады) по rig.json и класс D58."""
    path = os.path.join(MODELS, f"{item_id}.rig.json")
    if not os.path.exists(path):
        return None, "—"
    rig = json.load(open(path, encoding="utf-8"))
    lo, hi = [1e9] * 3, [-1e9] * 3
    for name, p in rig["parts"].items():
        if name == "Stand":
            continue
        for i in range(3):
            c = p["pivot"][i] + p["center"][i]
            lo[i] = min(lo[i], c - p["size"][i] / 2)
            hi[i] = max(hi[i], c + p["size"][i] / 2)
    size = max(hi[i] - lo[i] for i in range(3))
    return round(size, 2), "Heavy" if size > 3.2 else "Medium" if size > 2.2 else "Light"


def collection(cat):
    shots = os.path.join(C, "creatures_final")
    reports = {}
    for f in os.listdir(shots):
        if f.startswith("report") and f.endswith(".json"):
            reports.update(json.load(open(os.path.join(shots, f), encoding="utf-8")))
    ids = sorted(cat, key=lambda k: cat[k][0])
    card, cols = (W - 2 * M - 5 * 12) // 6, 6
    rows = (len(ids) + cols - 1) // cols
    sheet = Image.new("RGB", (W, 128 + rows * (card + 150) + 60), BG)
    d = ImageDraw.Draw(sheet)
    header(d, "Ледяная коллекция босса 5 — 30 существ (модели шага 2)",
           "Стиль D39 v2, подвижные части, подставка в игре скрыта. Карты: Common 512², остальные 1024². "
           "В Roblox не загружалось.")
    weights = {}
    for k, item_id in enumerate(ids):
        num, rarity, wow, name, income = cat[item_id]
        x, y = M + (k % cols) * (card + 12), 128 + (k // cols) * (card + 150)
        hero = os.path.join(shots, f"{item_id}_hero.png")
        if os.path.exists(hero):
            sheet.paste(fit(Image.open(hero).convert("RGB"), card, card), (x, y))
        col = RARITY[rarity]
        d.rectangle((x, y + card, x + card, y + card + 140), fill=PANEL)
        d.rectangle((x, y + card, x + card, y + card + 6), fill=col)
        d.text((x + 10, y + card + 10), f"{num}. {name}", font=font(21, True), fill=INK)
        d.text((x + 10, y + card + 40), f"{RU[rarity]} · «вау» {wow} · {income}/сек", font=font(18, True), fill=col)
        rep = reports.get(item_id, {})
        size, cls = weight(item_id)
        weights[item_id] = {"size": size, "class": cls}
        tri = rep.get("tris", "—")
        d.text((x + 10, y + card + 70), f"треуг. {tri} · частей {rep.get('rig_parts', '—')}", font=font(18), fill=DIM)
        d.text((x + 10, y + card + 96), f"вес D58: {cls}" + (f" ({size} ст.)" if size else ""), font=font(18),
               fill=DIM)
    os.makedirs(OUT, exist_ok=True)
    sheet.save(os.path.join(OUT, "1_collection.png"))
    with open(os.path.join(OUT, "weights.json"), "w", encoding="utf-8") as f:
        json.dump(weights, f, ensure_ascii=False, indent=1)
    return weights


def yeti():
    g = os.path.join(C, "yeti_game")
    a = os.path.join(C, "anim", "frames")
    clips = [("sleep_idle", "Сон"), ("wake", "Пробуждение: глыба на спину"), ("combat_idle", "Боевая стойка"),
             ("walk", "Шаг"), ("smash", "Удар кулаком сверху"), ("ice_clap", "«Ледяной хлопок»"),
             ("hit", "Получение урона"), ("victory", "Победа"), ("defeat", "Поражение: верхушка откинулась"),
             ("fall_asleep", "Засыпание: снял глыбу")]
    tw, th = 270, 334
    sheet = Image.new("RGB", (W, 128 + 600 + 20 + len(clips) * (th + 50) + 40), BG)
    d = ImageDraw.Draw(sheet)
    header(d, "Йети-коллекционер — игровая модель и 10 клипов",
           "30 частей на Motor6D, 3 карты 1024², ≈ 6 100 треугольников; клипы — Config/Battle (тайминги Сфинкса). "
           "Лёд глыбы — прозрачный.")
    poses = ["pose_stand_front.png", "pose_stand_34.png", "pose_sleep_34.png", "pose_combat_34.png",
             "pose_dizzy_34.png"]
    pw = (W - 2 * M - 4 * 12) // 5
    for i, p in enumerate(poses):
        path = os.path.join(g, p)
        if os.path.exists(path):
            sheet.paste(fit(Image.open(path).convert("RGB"), pw, 600), (M + i * (pw + 12), 128))
    y = 128 + 620
    for name, title in clips:
        d.text((M, y), title, font=font(26, True), fill=ACC)
        y += 40
        for k in range(8):
            path = os.path.join(a, f"{name}_{k}.png")
            if os.path.exists(path):
                sheet.paste(fit(Image.open(path).convert("RGB"), tw, th), (M + k * (tw + 12), y))
        y += th + 10
    sheet.save(os.path.join(OUT, "2_yeti.png"))


def maps_page(items, title, path, thumb=520):
    """items = [(подпись, файл цвета, файл нормалей)] — по строке на карту: цвет и нормали рядом."""
    rows = len(items)
    sheet = Image.new("RGB", (W, 128 + rows * (thumb + 56) + 20), BG)
    d = ImageDraw.Draw(sheet)
    header(d, title, "Каждая карта — до загрузки (решение владельца). Слева цвет, справа нормали; подпись — имя файла.")
    y = 128
    for label, color, normal in items:
        d.text((M, y + 4), label, font=font(24, True), fill=INK)
        for i, f in enumerate((color, normal)):
            if os.path.exists(f):
                im = Image.open(f).convert("RGB").resize((thumb, thumb), Image.LANCZOS)
                sheet.paste(im, (M + i * (thumb + 16), y + 40))
                d.text((M + i * (thumb + 16) + 8, y + 40 + thumb - 30), os.path.basename(f) + f"  {Image.open(f).size[0]}²",
                       font=font(18), fill=(30, 30, 40))
        y += thumb + 56
    sheet.save(path)


def maps(cat):
    yeti_items = [(f"Йети · {m}", os.path.join(TEX, f"Boss5Yeti{m}_color.png"), os.path.join(TEX, f"Boss5Yeti{m}_normal.png"))
                  for m in ("Head", "Body", "Limbs")]
    maps_page(yeti_items, "Карты Йети-коллекционера (3 × 2)", os.path.join(OUT, "maps_yeti.png"))
    ids = sorted(cat, key=lambda k: cat[k][0])
    tex = os.path.join(TEX, "boss5")
    for page in range(0, len(ids), 6):
        chunk = ids[page:page + 6]
        items = [(f"{cat[i][0]}. {cat[i][3]} ({RU[cat[i][1]]})", os.path.join(tex, f"{i}_color.png"),
                  os.path.join(tex, f"{i}_normal.png")) for i in chunk]
        maps_page(items, f"Карты существ {page + 1}–{page + len(chunk)}",
                  os.path.join(OUT, f"maps_creatures_{page // 6 + 1}.png"), thumb=440)


def fixes(cat):
    """Только исправленное по замечаниям владельца 2026-11-24: Йети (сон, засыпание, пробуждение, глыба крупно),
    4 существа и их карты (листы 3_fix_yeti.png, 4_fix_creatures.png, maps_fix.png)."""
    g = os.path.join(C, "yeti_game")
    a = os.path.join(C, "anim", "frames")
    tw, th = 270, 334
    shots = [("pose_sleep_34.png", "Сон — глыба рядом"), ("pose_sleep_front.png", "Сон — спереди"),
             ("pose_stand_side.png", "Глыба сбоку"), ("pose_stand_back34.png", "Глыба сзади, 3/4")]
    clips = [("sleep_idle", "Сон (цикл)"), ("fall_asleep", "Засыпание: снял глыбу, поставил рядом, сел"),
             ("wake", "Пробуждение: встал, поднял глыбу к плечу, закинул на спину")]
    sheet = Image.new("RGB", (W, 128 + 600 + 20 + len(clips) * (th + 50) + 40), BG)
    d = ImageDraw.Draw(sheet)
    header(d, "Йети — исправления 2026-11-24",
           "Глыба во сне стоит рядом; пробуждение без подъёма над головой; экспонаты крупнее, у краёв глыбы.")
    pw = (W - 2 * M - 3 * 12) // 4
    for i, (f, title) in enumerate(shots):
        path = os.path.join(g, f)
        if os.path.exists(path):
            sheet.paste(fit(Image.open(path).convert("RGB"), pw, 600), (M + i * (pw + 12), 128))
            d.rectangle((M + i * (pw + 12), 128 + 560, M + i * (pw + 12) + pw, 128 + 600), fill=PANEL)
            d.text((M + i * (pw + 12) + 10, 128 + 566), title, font=font(22, True), fill=INK)
    y = 128 + 620
    for name, title in clips:
        d.text((M, y), title, font=font(26, True), fill=ACC)
        y += 40
        for k in range(8):
            path = os.path.join(a, f"{name}_{k}.png")
            if os.path.exists(path):
                sheet.paste(fit(Image.open(path).convert("RGB"), tw, th), (M + k * (tw + 12), y))
        y += th + 10
    sheet.save(os.path.join(OUT, "3_fix_yeti.png"))
    ids = ["SnowSlime", "SkiEarHare", "PenguinStack", "SwivelOwl"]
    shots_dir = os.path.join(C, "creatures_final")
    views = ("hero", "front", "side", "face")
    cw = (W - 2 * M - 3 * 12) // 4
    sheet = Image.new("RGB", (W, 128 + len(ids) * (cw + 60) + 20), BG)
    d = ImageDraw.Draw(sheet)
    header(d, "Существа — исправления 2026-11-24",
           "№2 слизень (рыбка внутри, желе прозрачное), №9 заяц (кончики ушей-лыж), №17 пирамида 3-2-1, №18 филин.")
    y = 128
    for item_id in ids:
        num, rarity, wow, name, income = cat[item_id]
        d.text((M, y + 6), f"{num}. {name} ({RU[rarity]})", font=font(26, True), fill=RARITY[rarity])
        for i, v in enumerate(views):
            path = os.path.join(shots_dir, f"{item_id}_{v}.png")
            if os.path.exists(path):
                sheet.paste(fit(Image.open(path).convert("RGB"), cw, cw), (M + i * (cw + 12), y + 48))
        y += cw + 60
    sheet.save(os.path.join(OUT, "4_fix_creatures.png"))
    tex = os.path.join(TEX, "boss5")
    items = [(f"Йети · {m}", os.path.join(TEX, f"Boss5Yeti{m}_color.png"), os.path.join(TEX, f"Boss5Yeti{m}_normal.png"))
             for m in ("Head", "Body", "Limbs")]
    items += [(f"{cat[i][0]}. {cat[i][3]} ({RU[cat[i][1]]})", os.path.join(tex, f"{i}_color.png"),
               os.path.join(tex, f"{i}_normal.png")) for i in ids]
    maps_page(items, "Карты исправленного: Йети (3) и 4 существа", os.path.join(OUT, "maps_fix.png"), thumb=440)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cat = catalog()
    assert len(cat) == 30, len(cat)
    if "fixes" in sys.argv[1:]:
        fixes(cat)
        print("FIX_SHEETS_OK")
        return
    w = collection(cat)
    yeti()
    maps(cat)
    print("SHEETS_OK", json.dumps({k: v["class"] for k, v in w.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
