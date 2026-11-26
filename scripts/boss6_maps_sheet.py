"""Лист карт существ джунглей босса 6 — владельцу до загрузки в Roblox (D70: каждую картинку владелец видит до загрузки).

На существо: цветовая карта (<Id>_color.png), карта нормалей (<Id>_normal.png), кадр модели с запечёнными картами
(<Id>_hero.png полной сборки) и строка: размер карты, редкость, треугольники. Карты — assets/textures/art/boss6/,
кадры — assets/concepts/bosses_5_10/boss6_prod/creatures/ (полная сборка art_jungle.py без quick).
Запуск из корня: python scripts/boss6_maps_sheet.py [id…] → assets/concepts/bosses_5_10/boss6_prod/7_maps_<n>.png
(вне git), по 8 существ на лист. Без аргументов — все существа, у которых карта есть.
Зависит от Pillow, scripts/blender/boss6/sheet.py и catalog_sheet.py, scripts/boss6_anatomy_audit.py (отчёты).
"""

import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "blender", "boss6"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import sheet as SH  # noqa: E402
import catalog_sheet as CS  # noqa: E402
import boss6_anatomy_audit as AU  # noqa: E402

V = SH.V
TEX = os.path.join(ROOT, "assets", "textures", "art", "boss6")
PROD = os.path.join(ROOT, "assets", "concepts", "bosses_5_10", "boss6_prod")
SHOTS = os.path.join(PROD, "creatures")
PER = 8


def has_maps(item_id):
    return os.path.exists(os.path.join(TEX, f"{item_id}_color.png"))


def main(only=()):
    items = [it for it in CS.rows() if (not only or it["id"] in only) and has_maps(it["id"])]
    outs = []
    pic, gap = 360, 12
    for g in range(0, len(items), PER):
        grp = items[g:g + PER]
        row_h = pic + 70
        sheet = Image.new("RGB", (SH.W, 130 + len(grp) * row_h + 20), SH.BG)
        d = ImageDraw.Draw(sheet)
        SH.header(d, f"Карты существ джунглей — на просмотр до загрузки ({g + 1}–{g + len(grp)} из {len(items)})",
                  "Цветовая карта, карта нормалей и модель с картами. Ничего не загружено; загрузка — после «ок».")
        y = 130
        for it in grp:
            x = SH.M
            col = SH.RARITY[it["rarity"]]
            for path, cap in ((os.path.join(TEX, f"{it['id']}_color.png"), "цвет"),
                              (os.path.join(TEX, f"{it['id']}_normal.png"), "нормали"),
                              (os.path.join(SHOTS, f"{it['id']}_hero.png"), "модель с картами")):
                if os.path.exists(path):
                    im = Image.open(path).convert("RGB")
                    sheet.paste(V.fit(im, pic, pic), (x, y))
                V.label(d, x + 8, y + pic - 40, cap)
                x += pic + gap
            d.rectangle((x, y, x + 10, y + pic), fill=col)
            tx = x + 26
            cw = Image.open(os.path.join(TEX, f"{it['id']}_color.png")).size
            rep = AU.report(it["id"])
            ty = V.para(d, tx, y + 6, f"№{it['n']} {it['name']}", SH.W - tx - SH.M, size=30, fill=SH.INK, bold=True)
            ty = V.para(d, tx, ty + 4, f"{it['id']} · {SH.RARITY_RU[it['rarity']]} · карта {cw[0]}×{cw[1]}",
                        SH.W - tx - SH.M, size=22, fill=col)
            V.para(d, tx, ty + 6, f"треугольников без подставки: {rep.get('tris_without_stand')}",
                   SH.W - tx - SH.M, size=20, fill=SH.DIM)
            y += row_h
        out = os.path.join(PROD, f"7_maps_{g // PER + 1}.png")
        sheet = sheet.crop((0, 0, SH.W, y + 10))
        sheet.save(out)
        outs.append(out)
    return outs


if __name__ == "__main__":
    for o in main(sys.argv[1:]):
        print(o)
