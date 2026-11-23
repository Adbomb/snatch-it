"""Иконки HUD v3 для игры (ТЗ владельца 2026-11-17): из рендеров Blender scripts/blender/d48_icons.py
(assets/concepts/d48/v2/icons/raw_<имя>.png) — тёмный контур одной толщины и мягкая тень (как на листе D48 v2,
scripts/d48_hud_mockup.py), обрезка по рисунку, квадрат 256 px с прозрачным фоном.

Пишет assets/ui/hud/icon_<ключ>_256.png и лист для просмотра assets/ui/hud/hud_icons_sheet.png. В Roblox ничего не
загружает; ID загруженных картинок — assets/ui/hud/IDS.md и UITokens.HudIcons.

Запуск: python scripts/hud_icons.py   (нужен Pillow)
"""

import os

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "assets", "concepts", "d48", "v2", "icons")
OUT = os.path.join(ROOT, "assets", "ui", "hud")
os.makedirs(OUT, exist_ok=True)
OUTLINE = (24, 20, 46, 255)
SIZE = 256

# ключ иконки в игре (UITokens.HudIcons) → имя рендера
ICONS = {
    "Shop": "shop",
    "Inventory": "briefcase",
    "Museum": "museum",
    "Defense": "shield",
    "Coins": "coin",
    "Strength": "fist",
    "Day": "sun",
    "Preparation": "hourglass",
    "Night": "moon",
    "DoomNight": "skull",
}


def outlined(name, size=1024, ring=26):
    raw = Image.open(os.path.join(RAW, f"raw_{name}.png")).convert("RGBA").resize((size, size), Image.LANCZOS)
    grow = raw.split()[3]
    for _ in range(max(1, ring // 3)):
        grow = grow.filter(ImageFilter.MaxFilter(7))
    grow = grow.filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: 255 if v > 90 else 0)
    shadow = Image.new("RGBA", raw.size, (0, 0, 0, 0))
    shadow.putalpha(grow.point(lambda v: int(v * 0.35)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    base = Image.new("RGBA", raw.size, (0, 0, 0, 0))
    base.alpha_composite(shadow, (0, int(size * 0.02)))
    line = Image.new("RGBA", raw.size, OUTLINE)
    line.putalpha(grow)
    base.alpha_composite(line)
    base.alpha_composite(raw)
    return base


def fitted(im, size=SIZE, pad=6):
    """Обрезка по рисунку и вписывание в квадрат size с полем pad."""
    im = im.crop(im.getbbox())
    k = (size - 2 * pad) / max(im.size)
    im = im.resize((max(1, round(im.size[0] * k)), max(1, round(im.size[1] * k))), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.alpha_composite(im, ((size - im.size[0]) // 2, (size - im.size[1]) // 2))
    return out


done = {}
for key, name in ICONS.items():
    im = fitted(outlined(name))
    im.save(os.path.join(OUT, f"icon_{key}_256.png"))
    done[key] = im

# лист для просмотра: крупно, и в размерах HUD (40 и 28 px) на светлом и тёмном фоне
keys = list(ICONS)
W, H = 40 + len(keys) * 150, 420
sheet = Image.new("RGBA", (W, H), (38, 44, 78, 255))
d = ImageDraw.Draw(sheet)
d.rectangle((0, 250, W, 335), fill=(236, 242, 255, 255))
d.rectangle((0, 335, W, H), fill=(90, 190, 90, 255))
for i, key in enumerate(keys):
    x = 30 + i * 150
    sheet.alpha_composite(done[key].resize((130, 130), Image.LANCZOS), (x, 20))
    d.text((x + 20, 160), key, fill=(255, 255, 255, 255))
    for y in (262, 345):
        sheet.alpha_composite(done[key].resize((56, 56), Image.LANCZOS), (x, y))
        sheet.alpha_composite(done[key].resize((36, 36), Image.LANCZOS), (x + 64, y + 10))
        sheet.alpha_composite(done[key].resize((24, 24), Image.LANCZOS), (x + 106, y + 16))
sheet.convert("RGB").save(os.path.join(OUT, "hud_icons_sheet.png"))
print("иконок:", len(done), "→", OUT)
