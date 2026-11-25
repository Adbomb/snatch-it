"""Лист каталога 30 существ джунглей босса 6 — для утверждения владельцем (читается с телефона).

  python scripts/blender/boss6/catalog_sheet.py
  → assets/concepts/bosses_5_10/boss6_v2/4_catalog.png (вне git)
Источник — таблица docs/BOSS6_CATALOG.md; у 10 утверждённых эскизов (★) — кадр hero из boss6_v2/raw/creatures/,
у новых — карточка без картинки (модели делаются после «ок» на каталог). Оформление — sheet.py.
"""

import os
import re
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sheet as SH  # noqa: E402  (W, M, V, header, RARITY, RARITY_RU, BG, PANEL, INK, DIM, ACC)

V = SH.V
CATALOG = os.path.join(SH.REPO, "docs", "BOSS6_CATALOG.md")


def rows():
    out = []
    for line in open(CATALOG, encoding="utf-8"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 11 and cells[0].isdigit():
            n, rar, wow, name, cid, fam, image, signs, emo, cols, inc = cells
            star = name.startswith("★")
            out.append(dict(n=int(n), rarity=rar, wow=wow, name=name.lstrip("★ ").strip(), id=cid, family=fam,
                            image=image, signs=signs, emotion=emo, colors=cols, income=inc, star=star))
    return out


def main():
    items = rows()
    assert len(items) == 30, len(items)
    W, M = SH.W, SH.M
    sheet = Image.new("RGB", (W, 9000), SH.BG)
    d = ImageDraw.Draw(sheet)
    SH.header(d, "Каталог джунглей босса 6 — 30 существ · на утверждение",
              "12 обычных / 9 редких / 6 эпических / 3 легендарных. С кадром и меткой «утверждён» — 10 эскизов концепта, "
              "остальные 20 — новые: модели после «ок». Подробно — docs/BOSS6_CATALOG.md.")
    y = 128
    cols = 3
    cw = (W - 2 * M - (cols - 1) * 12) // cols
    pic = 300
    for rar in ("Common", "Rare", "Epic", "Legendary"):
        group = [it for it in items if it["rarity"] == rar]
        col = SH.RARITY[rar]
        d.rectangle((M, y, W - M, y + 56), fill=SH.PANEL)
        d.rectangle((M, y, M + 12, y + 56), fill=col)
        d.text((M + 28, y + 8), f"{SH.RARITY_RU[rar]} — {len(group)}", font=V.font(32, True), fill=col)
        y += 68
        for row0 in range(0, len(group), cols):
            heights = []
            scratch = ImageDraw.Draw(Image.new("RGB", (cw, 2000)))
            for it in group[row0:row0 + cols]:
                heights.append(card(scratch, None, 0, 0, cw, pic, it, col))
            h = max(heights)
            for i, it in enumerate(group[row0:row0 + cols]):
                x = M + i * (cw + 12)
                d.rectangle((x, y, x + cw, y + h), fill=SH.PANEL)
                card(d, sheet, x, y, cw, pic, it, col)
            y += h + 12
        y += 8
    sheet = sheet.crop((0, 0, W, y + M))
    out = os.path.join(SH.OUT, "4_catalog.png")
    sheet.save(out)
    return sheet.size


def card(d, sheet, x, y, cw, pic, it, col):
    """Карточка существа; sheet=None — только измерить высоту."""
    hero = os.path.join(SH.CR, f"{it['id']}_hero.png")
    if sheet is not None:
        if it["star"] and os.path.exists(hero):
            sheet.paste(V.fit(Image.open(hero).convert("RGB"), pic, pic), (x, y))
            SH.tag(d, x + 8, y + 8, "утверждён", SH.V2_TAG)
        else:
            d.rectangle((x, y, x + pic, y + pic), fill=(44, 46, 58))
            d.rectangle((x, y, x + pic, y + 8), fill=col)
            V.para(d, x + 18, y + 24, it["family"], pic - 36, size=26, fill=SH.DIM, bold=True)
            V.para(d, x + 18, y + 64, "новое — модель после «ок»", pic - 36, size=19, fill=SH.DIM)
            V.para(d, x + 18, y + 120, "Цвета: " + it["colors"], pic - 36, size=18, fill=SH.INK)
    tx, tw = x + pic + 16, cw - pic - 30
    ty = y + 10
    title = it["name"]
    ty = V.para(d, tx, ty, title, tw, size=27, fill=SH.INK, bold=True) + 2
    ty = V.para(d, tx, ty, f"№{it['n']} · «вау» {it['wow']} · {it['family']} · {it['income']}/с", tw, size=18,
                fill=col) + 6
    ty = V.para(d, tx, ty, it["image"][0].upper() + it["image"][1:] + ".", tw, size=19, fill=SH.INK) + 6
    ty = V.para(d, tx, ty, "Эмоция: " + it["emotion"] + ".", tw, size=18, fill=SH.DIM) + 4
    ty = V.para(d, tx, ty, "Признаки: " + it["signs"] + ".", tw, size=17, fill=SH.DIM) + 10
    return max(ty - y, pic)


if __name__ == "__main__":
    print(main())
