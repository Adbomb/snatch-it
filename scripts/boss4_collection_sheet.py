"""Общий лист коллекции босса 4 (30 существ): пять рядов по шесть одной камерой и в одном масштабе (oasis_lineup.py,
папки row1…row5), под каждым рядом — подписи; ниже — сетка главных рендеров каждого существа и сетка кадров телефона.
Только кадры настоящих моделей из Blender.
Запуск: python scripts/boss4_collection_sheet.py <папка существ> <папка коллекции>
Пишет <папка коллекции>/collection_sheet.jpg, collection_heroes.jpg и печатает порядок рядов для oasis_lineup.py.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
CREATURES = [  # (№, id, название, редкость, папка кадров, файл главного рендера)
    (1, "CactusBoxer", "Кактус-боксёр", "Common"), (2, "FloppyFennec", "Фенек-лопоух", "Common"),
    (3, "TumbleweedRunner", "Перекати-поле-бегун", "Common"), (4, "CanteenCamel", "Верблюжонок-фляга", "Common"),
    (5, "DuneTurtle", "Черепаха-бархан", "Common"), (6, "UmbrellaLizard", "Ящерка-зонтик", "Common"),
    (7, "MelonArmadillo", "Арбуз-броненосец", "Common"), (8, "StrawSnake", "Змейка-соломинка", "Common"),
    (9, "DropBeetle", "Жук-капелька", "Common"), (10, "MeerkatLookout", "Сурикат-часовой", "Common"),
    (11, "CanScorpion", "Скорпион-лейка", "Common"), (12, "SandChick", "Страусёнок-песочник", "Common"),
    (13, "AquariumCamel", "Верблюд-аквариум", "Rare"), (14, "CactusAcrobats", "Кактусы-акробаты", "Rare"),
    (15, "DrillWorm", "Песчаный червь-бурильщик", "Rare"), (16, "FanVulture", "Гриф-вентилятор", "Rare"),
    (17, "CobraFountain", "Кобра-фонтан", "Rare"), (18, "DustDevil", "Смерч-озорник", "Rare"),
    (19, "KaleidoChameleon", "Хамелеон-калейдоскоп", "Rare"), (20, "FennecRiddler_v2", "Фенек-загадочник", "Rare"),
    (21, "MirageFish", "Рыба-мираж", "Rare"), (22, "DuneWhale", "Кит-бархан", "Epic"),
    (23, "IslandTurtle", "Черепаха-остров", "Epic"), (24, "BlazeOstrich", "Жар-страус", "Epic"),
    (25, "CloudCamel", "Верблюд-туча", "Epic"), (26, "CrystalScorpion", "Кристальный скорпион", "Epic"),
    (27, "GiantCactus", "Кактус-великан", "Epic"), (28, "SpringAntelope", "Антилопа-родник", "Legendary"),
    (29, "PuzzlePhoenix", "Феникс-головоломка", "Legendary"), (30, "TornadoKing", "Царь-смерч", "Legendary")]
RARITY = {"Common": (92, 194, 204), "Rare": (170, 120, 240), "Epic": (226, 176, 255), "Legendary": (255, 210, 63)}
BOLD = "C:/Windows/Fonts/arialbd.ttf"
F_T, F_L, F_S = ImageFont.truetype(BOLD, 46), ImageFont.truetype(BOLD, 24), ImageFont.truetype(BOLD, 20)
BG, GOLD, WHITE, GREY = (16, 18, 24), (255, 210, 63), (240, 242, 248), (170, 176, 190)
W, M = 2400, 16


def folder_of(item):
    return "FennecRiddler" if item.startswith("FennecRiddler") else item


def fit(im, w, h):
    k = min(w / im.width, h / im.height)
    small = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    cell = Image.new("RGB", (w, h), BG)
    cell.paste(small, ((w - small.width) // 2, (h - small.height) // 2))
    return cell


def label(d, xy, text, font, fill):
    x, y = xy
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        d.text((x + dx, y + dy), text, font=font, fill=BG)
    d.text(xy, text, font=font, fill=fill)


if __name__ == "__main__":
    creatures_dir, out = sys.argv[1], sys.argv[2]
    rows = [CREATURES[i:i + 6] for i in range(0, 30, 6)]
    if len(sys.argv) > 3 and sys.argv[3] == "rows":
        for r in rows:
            print(" ".join(c[1] for c in r))
        sys.exit(0)
    page = Image.new("RGB", (W, 9000), BG)
    d = ImageDraw.Draw(page)
    d.text((M, 14), "Босс 4 «Сфинкс-лежебока» — коллекция из 30 существ (D39, эталон №20 v2)", font=F_T, fill=GOLD)
    d.text((M, 74), "Ряды по шесть — одна камера, один свет и один масштаб (площадка 3.7 × 3.7 стада); 12 Common · 9 Rare · "
           "6 Epic · 3 Legendary.", font=F_S, fill=GREY)
    y = 116
    for k, r in enumerate(rows):
        im = Image.open(os.path.join(out, f"row{k + 1}", "lineup_color.png")).convert("RGB")
        cell = fit(im, W - 2 * M, round((W - 2 * M) * im.height / im.width))
        page.paste(cell, (M, y))
        cw = (W - 2 * M) / 6
        for j, (num, item, name, rarity) in enumerate(r):
            label(d, (M + round(j * cw) + 10, y + 8), f"№{num} {name}", F_S, WHITE)
            label(d, (M + round(j * cw) + 10, y + 34), rarity, F_S, RARITY[rarity])
        y += cell.height + M
    page = page.crop((0, 0, W, y))
    page.save(os.path.join(out, "collection_sheet.jpg"), quality=90)
    print("ГОТОВО ряды", page.size)
    # сетка главных рендеров: 6 × 5
    cw = (W - 7 * M) // 6
    ch = cw + 40
    grid = Image.new("RGB", (W, 116 + 5 * (ch + M)), BG)
    d = ImageDraw.Draw(grid)
    d.text((M, 14), "Главные рендеры всех 30 существ (у каждого свой кадр по его габаритам)", font=F_T, fill=GOLD)
    for i, (num, item, name, rarity) in enumerate(CREATURES):
        x = M + (i % 6) * (cw + M)
        yy = 96 + (i // 6) * (ch + M)
        im = Image.open(os.path.join(creatures_dir, folder_of(item), f"{item}_hero.png")).convert("RGB")
        grid.paste(fit(im, cw, cw), (x, yy))
        label(d, (x + 8, yy + 6), f"№{num}", F_L, RARITY[rarity])
        d.text((x + 4, yy + cw + 6), name, font=F_S, fill=WHITE)
    grid.save(os.path.join(out, "collection_heroes.jpg"), quality=90)
    print("ГОТОВО сетка", grid.size)
