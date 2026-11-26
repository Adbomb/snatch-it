"""Лист карт существ «Банка» босса 7 — владельцу до загрузки в Roblox (D70: каждую картинку владелец видит до загрузки).

На существо: цветовая карта (<Id>_color.png) и кадр модели с запечёнными картами (<Id>_hero.png полной сборки), строка:
размер карты, редкость, треугольники. Нормали со босса 7 не загружаем (решение владельца после босса 6, BUGS.md) —
на листе их нет. Карты — assets/textures/art/boss7/, кадры — assets/concepts/bosses_5_10/boss7_prod/creatures/
(полная сборка art_bank.py без quick).
Запуск из корня: python scripts/boss7_maps_sheet.py [id…] → assets/concepts/bosses_5_10/boss7_prod/8_maps_<n>.png
(вне git), по 10 существ на лист. Без аргументов — все существа, у которых карта есть.
Зависит от Pillow, scripts/boss7_anatomy_audit.py (каталог, отчёты, оформление).
"""

import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import boss7_anatomy_audit as AU  # noqa: E402

SH, V = AU.SH, AU.V
TEX = os.path.join(ROOT, "assets", "textures", "art", "boss7")
PER = 10


def has_maps(item_id):
    return os.path.exists(os.path.join(TEX, f"{item_id}_color.png"))


def main(only=()):
    items = [it for it in AU.items() if (not only or it["id"] in only) and has_maps(it["id"])]
    outs = []
    pic, gap = 400, 12
    cols = 1 if only else 2  # выборка: по существу в ряд, с видами сверху и спереди
    cw_ = (SH.W - 2 * SH.M - (cols - 1) * 24) // cols
    for g in range(0, len(items), PER):
        grp = items[g:g + PER]
        rows = (len(grp) + cols - 1) // cols
        row_h = pic + 20
        sheet = Image.new("RGB", (SH.W, 130 + rows * row_h + 20), SH.BG)
        d = ImageDraw.Draw(sheet)
        SH.header(d, f"Карты существ «Банка» — на просмотр до загрузки ({g + 1}–{g + len(grp)} из {len(items)})",
                  "Цветовая карта и модель с картами. Нормали не загружаем. Ничего не загружено; загрузка — после «ок».")
        for i, it in enumerate(grp):
            x = SH.M + (i % cols) * (cw_ + 24)
            y = 130 + (i // cols) * row_h
            col = SH.RARITY[it["rarity"]]
            views = [(os.path.join(TEX, f"{it['id']}_color.png"), "цвет"),
                     (os.path.join(AU.SHOTS, f"{it['id']}_hero.png"), "модель с картами")]
            if only:
                views += [(os.path.join(AU.SHOTS, f"{it['id']}_top.png"), "сверху"),
                          (os.path.join(AU.SHOTS, f"{it['id']}_front.png"), "спереди")]
            for path, cap in views:
                if os.path.exists(path):
                    sheet.paste(V.fit(Image.open(path).convert("RGB"), pic, pic), (x, y))
                V.label(d, x + 8, y + pic - 40, cap)
                x += pic + gap
            d.rectangle((x, y, x + 8, y + pic), fill=col)
            tx = x + 20
            tw = SH.M + (i % cols) * (cw_ + 24) + cw_ - tx
            size = Image.open(os.path.join(TEX, f"{it['id']}_color.png")).size
            rep = AU.report(it["id"])
            ty = V.para(d, tx, y + 6, f"№{it['n']} {it['name']}", tw, size=26, fill=SH.INK, bold=True)
            ty = V.para(d, tx, ty + 4, f"{it['id']} · {SH.RARITY_RU[it['rarity']]}", tw, size=20, fill=col)
            ty = V.para(d, tx, ty + 4, f"карта {size[0]}×{size[1]}", tw, size=20, fill=SH.DIM)
            V.para(d, tx, ty + 4, f"треугольников без подставки: {rep.get('tris_without_stand')}", tw, size=18,
                   fill=SH.DIM)
        tag = f"{g // PER + 1}" if not only else "_".join(only)[:60]  # выборка — свой файл, общий лист не затирается
        out = os.path.join(AU.PROD, f"8_maps_{tag}.png")
        sheet = sheet.crop((0, 0, SH.W, 130 + rows * row_h + 10))
        sheet.save(out)
        outs.append(out)
    return outs


if __name__ == "__main__":
    for o in main(sys.argv[1:]):
        print(o)
