"""D48 v2 — лист иконок, сравнение трёх иконок силы, макеты нового HUD (ПК и телефон) поверх кадра игры из Studio
и схема зон экрана.

Только картинки для утверждения: в игру ничего не попадает, в Roblox ничего не загружается.
Иконки — рендеры Blender (scripts/blender/d48_icons.py): здесь им добавляется одинаковый тёмный контур и мягкая тень.
Фон — assets/concepts/d48/ref/hud_clean.jpg (Studio, интерфейс скрыт). Шрифт — Montserrat Black/Bold из Roblox Studio
(как у Stud-UI). Системные элементы Roblox (меню, чат, список игроков, джойстик, прыжок) нарисованы полупрозрачными
заглушками, чтобы проверить, что HUD их не перекрывает.

Запуск: python scripts/d48_hud_mockup.py   (нужен Pillow)
"""

import glob
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D48 = os.path.join(ROOT, "assets", "concepts", "d48")
ICONS = os.path.join(D48, "v2", "icons")
HUD = os.path.join(D48, "v2", "hud")
os.makedirs(HUD, exist_ok=True)
NAMES = ["briefcase", "shield", "coin", "income", "fist", "dumbbell", "bicep"]
MAIN = ["briefcase", "shield", "fist", "coin", "income"]  # пять иконок HUD (сила — кулак, D48 v2)
POWER = "fist"
OUTLINE = (24, 20, 46, 255)


def font(weight, size):
    for p in sorted(glob.glob(os.path.expandvars(rf"%LOCALAPPDATA%\Roblox\Versions\*\content\fonts\Montserrat-{weight}.ttf"))):
        path = p
    return ImageFont.truetype(path, size)


# ── Иконки: контур одной толщины и тень ─────────────────────────────────────────────────────────────────────────
def outlined(name, size=1024, ring=26):
    raw = Image.open(os.path.join(ICONS, f"raw_{name}.png")).convert("RGBA")
    raw = raw.resize((size, size), Image.LANCZOS)
    a = raw.split()[3]
    grow = a
    steps = max(1, ring // 3)
    for _ in range(steps):
        grow = grow.filter(ImageFilter.MaxFilter(7))
    grow = grow.filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: 255 if v > 90 else 0)
    shadow = Image.new("RGBA", raw.size, (0, 0, 0, 0))
    shadow.putalpha(grow.point(lambda v: int(v * 0.35)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    base = Image.new("RGBA", raw.size, (0, 0, 0, 0))
    base.alpha_composite(shadow, (0, int(size * 0.02)))
    ol = Image.new("RGBA", raw.size, OUTLINE)
    ol.putalpha(grow)
    base.alpha_composite(ol)
    base.alpha_composite(raw)
    return base


ICON = {}
for n in NAMES:
    im = outlined(n)
    im.save(os.path.join(ICONS, f"icon_{n}.png"))
    ICON[n] = im


def icon(name, px):
    return ICON[name].resize((px, px), Image.LANCZOS)


# ── Текст с контуром и тенью (как у Stud-UI: тёмная обводка + выдавленная тень) ──────────────────────────────────
def text(img, xy, body, size, fill=(255, 255, 255), stroke=(24, 20, 46), sw=None, anchor="la", weight="Black",
         shadow=True):
    f = font(weight, size)
    sw = sw if sw is not None else max(2, size // 9)
    if shadow:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.text((xy[0], xy[1] + max(2, size // 12)), body, font=f, fill=(10, 8, 24, 200), stroke_width=sw,
               stroke_fill=(10, 8, 24, 200), anchor=anchor)
        layer = layer.filter(ImageFilter.GaussianBlur(max(1, size // 20)))
        img.alpha_composite(layer)
    d = ImageDraw.Draw(img)
    d.text(xy, body, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke, anchor=anchor)
    return d.textbbox(xy, body, font=f, stroke_width=sw, anchor=anchor)


def rounded(img, box, r, fill, outline=None, width=0):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, r, fill=fill, outline=outline, width=width)
    img.alpha_composite(layer)


def soft_blob(img, box, alpha=70, blur=40):
    """Мягкая тёмная подложка без рамки — читаемость на светлой траве."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, 40, fill=(10, 14, 30, alpha))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))


def paste(img, im, x, y):
    img.alpha_composite(im, (int(x), int(y)))


# ── Лист иконок ─────────────────────────────────────────────────────────────────────────────────────────────────
LABELS = {"briefcase": "Инвентарь", "shield": "Защита", "fist": "Сила", "coin": "Монеты", "income": "Доход/сек",
          "dumbbell": "Рука с гантелью", "bicep": "Бицепс"}


def icon_sheet():
    W, H = 1800, 1000
    img = Image.new("RGBA", (W, H))
    top, bot = (43, 58, 103), (22, 28, 54)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)) + (255,))
    text(img, (W // 2, 70), "D48 — иконки HUD (вариант 2)", 54, anchor="mm")
    text(img, (W // 2, 128), "Blender, стиль D39: блоки, ступенчатый силуэт, одна камера и один свет; контур одной "
                             "толщины", 24, fill=(200, 214, 255), weight="Bold", anchor="mm", sw=2)
    for i, n in enumerate(MAIN):
        cx = 200 + i * 350
        paste(img, icon(n, 290), cx - 145, 190)
        text(img, (cx, 505), LABELS[n], 34, anchor="mm")
    # читаемость в малом размере: на светлом и тёмном фоне
    rounded(img, (110, 590, W - 110, 760), 28, (238, 244, 255, 255))
    rounded(img, (110, 790, W - 110, 960), 28, (40, 48, 82, 255))
    for row, y in ((0, 600), (1, 800)):
        x = 150
        for px in (100, 64, 44):
            for n in MAIN:
                paste(img, icon(n, px), x, y + (150 - px) // 2)
                x += px + 14
            x += 40
    text(img, (W - 130, 605), "100 · 64 · 44 px", 22, fill=(60, 70, 110), stroke=(238, 244, 255), anchor="ra",
         weight="Bold", shadow=False, sw=0)
    img.convert("RGB").save(os.path.join(ICONS, "icons_sheet.png"))


def power_compare():
    W, H = 1800, 1180
    img = Image.new("RGBA", (W, H))
    top, bot = (43, 58, 103), (22, 28, 54)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)) + (255,))
    text(img, (W // 2, 66), "Иконка силы — три варианта", 54, anchor="mm")
    text(img, (W // 2, 122), "одна камера, один свет, один контур; проверка в 100 · 64 · 44 px на светлом и тёмном",
         24, fill=(200, 214, 255), weight="Bold", anchor="mm", sw=2)
    cards = (("fist", "1. Кулак", "читается сразу: удар, сила", True),
             ("dumbbell", "2. Рука с гантелью", "прокачка; в 44 px гантель сливается", False),
             ("bicep", "3. Бицепс", "мощь; в 44 px похож на «Г»", False))
    for i, (n, title, note, best) in enumerate(cards):
        cx = 300 + i * 600
        x0 = cx - 270
        rounded(img, (x0, 170, x0 + 540, 1120), 34, (255, 214, 90, 255) if best else (70, 84, 130, 255))
        rounded(img, (x0 + 6, 176, x0 + 534, 1114), 30, (30, 38, 72, 255))
        paste(img, icon(n, 330), cx - 165, 200)
        text(img, (cx, 570), title, 38, anchor="mm", fill=(255, 214, 90) if best else (255, 255, 255))
        text(img, (cx, 616), note, 22, anchor="mm", weight="Bold", fill=(205, 216, 245), sw=2)
        for row, (y, bg) in enumerate(((660, (238, 244, 255, 255)), (880, (16, 20, 40, 255)))):
            rounded(img, (x0 + 30, y, x0 + 510, y + 200), 22, bg)
            x = x0 + 60
            for px in (100, 64, 44):
                paste(img, icon(n, px), x, y + (200 - px) // 2)
                x += px + 50
        if best:
            rounded(img, (cx - 120, 1080, cx + 120, 1126), 23, (255, 214, 90, 255))
            text(img, (cx, 1103), "ВЫБОР", 26, anchor="mm", fill=(40, 28, 6), stroke=(255, 214, 90), shadow=False,
                 sw=0)
    img.convert("RGB").save(os.path.join(ICONS, "power_compare.png"))


# ── Фон кадра ───────────────────────────────────────────────────────────────────────────────────────────────────
SRC = Image.open(os.path.join(D48, "ref", "hud_clean.jpg")).convert("RGB")


def background(w, h, night=False):
    sw, sh = SRC.size
    tw = int(sh * w / h)
    x0 = (sw - tw) // 2
    bg = SRC.crop((x0, 0, x0 + tw, sh)).resize((w, h), Image.LANCZOS).convert("RGBA")
    if night:  # Судная ночь: тёмно-фиолетовое небо, красная виньетка
        tint = Image.new("RGBA", bg.size, (70, 40, 120, 255))
        bg = ImageChops.multiply(bg, Image.new("RGBA", bg.size, (150, 130, 200, 255)))
        bg = Image.blend(bg, tint, 0.18)
        vig = Image.new("L", bg.size, 0)
        ImageDraw.Draw(vig).ellipse((-w * 0.25, -h * 0.35, w * 1.25, h * 1.35), fill=255)
        vig = vig.filter(ImageFilter.GaussianBlur(160))
        red = Image.new("RGBA", bg.size, (190, 20, 40, 255))
        bg = Image.composite(bg, Image.blend(bg, red, 0.45), vig)
    return bg


# ── Системные элементы Roblox (заглушки для проверки зон) ──────────────────────────────────────────────────────
def roblox_pc(img):
    w, _ = img.size
    for k, glyph in enumerate(("≡", "💬")):
        x = 16 + k * 52
        rounded(img, (x, 12, x + 44, 56), 12, (18, 22, 30, 150))
    text(img, (38, 34), "R", 24, anchor="mm", weight="Black", sw=0, shadow=False)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((80, 24, 100, 40), 5, outline=(255, 255, 255, 230), width=3)
    rounded(img, (w - 258, 12, w - 16, 56), 12, (18, 22, 30, 150))  # список игроков (свёрнут)
    text(img, (w - 238, 34), "Игроки · 3", 20, anchor="lm", weight="Bold", sw=0, shadow=False)


def roblox_phone(img, notch=110):
    w, h = img.size
    rounded(img, (notch + 10, 14, notch + 64, 68), 14, (18, 22, 30, 150))
    rounded(img, (notch + 74, 14, notch + 128, 68), 14, (18, 22, 30, 150))
    text(img, (notch + 37, 41), "R", 28, anchor="mm", sw=0, shadow=False)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((notch + 88, 30, notch + 114, 52), 6, outline=(255, 255, 255, 230), width=3)
    # джойстик и прыжок
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.ellipse((notch + 70, h - 380, notch + 370, h - 80), outline=(255, 255, 255, 120), width=6,
               fill=(255, 255, 255, 28))
    ld.ellipse((notch + 165, h - 285, notch + 275, h - 175), fill=(255, 255, 255, 110))
    ld.ellipse((w - notch - 250, h - 290, w - notch - 60, h - 100), outline=(255, 255, 255, 130), width=6,
               fill=(255, 255, 255, 30))
    ld.polygon([(w - notch - 155, h - 235), (w - notch - 195, h - 175), (w - notch - 115, h - 175)],
               fill=(255, 255, 255, 170))
    img.alpha_composite(layer)
    # корпус телефона: вырез и скруглённые углы
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), 90, fill=255)
    frame = Image.new("RGBA", img.size, (12, 12, 16, 255))
    out = Image.composite(img, frame, mask)
    ImageDraw.Draw(out).rounded_rectangle((18, h // 2 - 110, 52, h // 2 + 110), 17, fill=(8, 8, 10, 255))
    return out


# ── Элементы нового HUD ─────────────────────────────────────────────────────────────────────────────────────────
PHASES = {
    "day": ("ДЕНЬ 2", "2:45", (255, 196, 44), "до Судной ночи: 8 дн."),
    "night": ("НОЧЬ", "0:24", (120, 170, 255), "скоро рассвет"),
    "prep": ("ПОДГОТОВКА", "1:12", (255, 140, 40), "ставьте защиту"),
    "doom": ("СУДНАЯ НОЧЬ", "0:54", (255, 70, 80), "кражи разрешены"),
}


def phase_glyph(img, cx, cy, r, kind, color):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse((cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10), fill=color + (60,))
    if kind == "day":
        for k in range(8):
            a = k * math.pi / 4
            x, y = cx + math.cos(a) * (r + 2), cy + math.sin(a) * (r + 2)
            d.rectangle((x - 4, y - 4, x + 4, y + 4), fill=color + (255,))
        d.ellipse((cx - r * 0.62, cy - r * 0.62, cx + r * 0.62, cy + r * 0.62), fill=color + (255,),
                  outline=OUTLINE, width=3)
    elif kind in ("night", "doom"):
        d.ellipse((cx - r * 0.8, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8), fill=color + (255,), outline=OUTLINE,
                  width=3)
        d.ellipse((cx - r * 0.35, cy - r * 0.95, cx + r * 1.0, cy + r * 0.45), fill=(20, 24, 48, 255))
    else:
        d.polygon([(cx, cy - r * 0.9), (cx + r * 0.9, cy + r * 0.75), (cx - r * 0.9, cy + r * 0.75)],
                  fill=color + (255,), outline=OUTLINE)
        d.rectangle((cx - 3, cy - r * 0.35, cx + 3, cy + r * 0.2), fill=OUTLINE)
        d.rectangle((cx - 3, cy + r * 0.35, cx + 3, cy + r * 0.52), fill=OUTLINE)
    img.alpha_composite(layer)


def timer(img, cx, top, kind, scale=1.0, progress=0.45):
    title, clock, color, sub = PHASES[kind]
    s = scale
    probe = ImageDraw.Draw(img)
    tw = probe.textlength(title, font=font("Black", int(24 * s)))
    cw = probe.textlength(clock, font=font("Black", int(38 * s)))
    w, h = int(70 * s + tw + 34 * s + cw + 26 * s), int(70 * s)
    x0, y0 = cx - w // 2, top
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle((x0 - 6, y0 - 6, x0 + w + 6, y0 + h + 6), h // 2 + 6,
                                           fill=color + (90 if kind == "doom" else 0,))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14 * s)))
    rounded(img, (x0, y0, x0 + w, y0 + h), h // 2, (14, 18, 38, 175), outline=color + (230,), width=max(2, int(3 * s)))
    phase_glyph(img, x0 + int(38 * s), y0 + h // 2, int(17 * s), kind, color)
    text(img, (x0 + int(70 * s), y0 + h // 2), title, int(24 * s), fill=color, anchor="lm")
    text(img, (x0 + w - int(22 * s), y0 + h // 2 + int(1 * s)), clock, int(38 * s), anchor="rm")
    # тонкая полоса прогресса фазы и подпись
    bx0, bx1, by = x0 + int(30 * s), x0 + w - int(30 * s), y0 + h + int(10 * s)
    rounded(img, (bx0, by, bx1, by + int(6 * s)), 3, (14, 18, 38, 150))
    rounded(img, (bx0, by, bx0 + int((bx1 - bx0) * progress), by + int(6 * s)), 3, color + (255,))
    text(img, (cx, by + int(26 * s)), sub, int(18 * s), fill=(235, 240, 255), anchor="mm", weight="Bold",
         sw=max(2, int(3 * s)))


def stats(img, x, y, scale=1.0):
    s = scale
    soft_blob(img, (x - 30, y - 30, x + int(300 * s), y + int(220 * s)), 70, 36)
    rows = (("coin", "$12.5M", int(42 * s), (255, 255, 255), int(64 * s)),
            ("income", "+1.2K/сек", int(30 * s), (124, 255, 107), int(52 * s)),
            (POWER, "1 250", int(32 * s), (255, 255, 255), int(52 * s)))
    yy = y
    for name, val, size, color, px in rows:
        paste(img, icon(name, px), x, yy)
        box = text(img, (x + px + int(10 * s), yy + px // 2), val, size, fill=color, anchor="lm")
        if name == POWER:  # у силы — короткая подпись, чтобы число не путали с деньгами
            text(img, (box[2] + int(8 * s), yy + px // 2 + int(3 * s)), "сила", int(18 * s), fill=(214, 222, 245),
                 anchor="lm", weight="Bold", sw=2)
        yy += px + int(12 * s)


def menu_column(img, right, cy, scale=1.0, pc=True, active=None, hover=None):
    s = scale
    items = (("briefcase", "Инвентарь", "B"), ("shield", "Защита", None))
    px, gap = int(100 * s), int(24 * s)
    total = len(items) * (px + int(26 * s)) + (len(items) - 1) * gap
    y = cy - total // 2
    for name, label, key in items:
        x = right - px
        big = int(px * 1.08) if hover == name else px
        if active == name:
            glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(glow).ellipse((x - 18, y - 12, x + px + 18, y + px + 18), fill=(255, 205, 60, 190))
            img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(18)))
            rounded(img, (x + px // 2 - int(16 * s), y + px + int(36 * s), x + px // 2 + int(16 * s),
                          y + px + int(42 * s)), 3, (255, 214, 90, 255))
        paste(img, icon(name, big), x - (big - px) // 2, y - (big - px) // 2)
        text(img, (x + px // 2, y + px + int(10 * s)), label, int(19 * s), anchor="mt", weight="Black")
        if pc and key:  # клавиша на ПК
            kx, ky = x + px - int(28 * s), y + px - int(30 * s)
            rounded(img, (kx, ky, kx + int(32 * s), ky + int(32 * s)), int(8 * s), (255, 255, 255, 240),
                    outline=OUTLINE, width=3)
            text(img, (kx + int(16 * s), ky + int(16 * s)), key, int(19 * s), fill=(24, 20, 46), anchor="mm",
                 shadow=False, sw=0)
        if hover == name and pc:  # подсказка при наведении
            tw = int(190 * s)
            rounded(img, (x - tw - int(16 * s), y + px // 2 - int(22 * s), x - int(16 * s), y + px // 2 + int(22 * s)),
                    int(14 * s), (14, 18, 38, 215))
            text(img, (x - tw // 2 - int(16 * s), y + px // 2), "Защита музея", int(20 * s), anchor="mm",
                 weight="Bold", sw=2)
        y += px + int(26 * s) + gap


def carry_chip(img, cx, y, scale=1.0, pc=True):
    s = scale
    w, h = int(520 * s), int(58 * s)
    x0 = cx - w // 2
    rounded(img, (x0, y, x0 + w, y + h), h // 2, (14, 18, 38, 185))
    rounded(img, (x0 + int(8 * s), y + int(8 * s), x0 + int(150 * s), y + h - int(8 * s)), (h - int(16 * s)) // 2,
            (90, 160, 255, 255))
    text(img, (x0 + int(79 * s), y + h // 2), "РЕДКИЙ", int(18 * s), anchor="mm", sw=2)
    text(img, (x0 + int(166 * s), y + h // 2), "Несёте: Ваза в ящике", int(22 * s), anchor="lm", weight="Bold", sw=2)
    bw = int(150 * s)
    rounded(img, (x0 + w + int(12 * s), y, x0 + w + int(12 * s) + bw, y + h), int(18 * s), (240, 71, 60, 255),
            outline=(120, 20, 24, 255), width=3)
    text(img, (x0 + w + int(12 * s) + bw // 2, y + h // 2), "Бросить" + ("  G" if pc else ""), int(21 * s),
         anchor="mm", stroke=(110, 16, 22))


def attack_button(img, cx, cy, r):
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((cx - r - 16, cy - r - 16, cx + r + 16, cy + r + 16), fill=(255, 60, 70, 110))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(18)))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse((cx - r, cy - r + 8, cx + r, cy + r + 8), fill=(120, 18, 26, 255))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(240, 71, 60, 255), outline=(120, 18, 26, 255), width=5)
    d.ellipse((cx - r + 22, cy - r + 12, cx + r - 22, cy - r * 0.35), fill=(255, 140, 128, 70))
    img.alpha_composite(layer)
    paste(img, icon(POWER, int(r * 1.05)), cx - int(r * 0.525), cy - int(r * 0.68))
    text(img, (cx, cy + int(r * 0.6)), "УДАР", int(r * 0.3), anchor="mm", stroke=(110, 16, 22))


def hint_chip(img, cx, y, body, scale=1.0):
    s = scale
    f = font("Bold", int(22 * s))
    tw = ImageDraw.Draw(img).textlength(body, font=f)
    w, h = int(tw + 48 * s), int(46 * s)
    rounded(img, (cx - w // 2, y, cx + w // 2, y + h), h // 2, (14, 18, 38, 170))
    text(img, (cx, y + h // 2), body, int(22 * s), anchor="mm", weight="Bold", sw=2)


def label(img, xy, body):
    text(img, xy, body, 20, fill=(255, 236, 140), anchor="la", weight="Bold", sw=3)


# ── Сборка макетов ──────────────────────────────────────────────────────────────────────────────────────────────
def pc(kind="day", context=False, name="hud_pc_day"):
    W, H = 1920, 1080
    img = background(W, H, night=kind == "doom")
    roblox_pc(img)
    timer(img, W // 2, 70, kind)
    stats(img, 34, 400)
    menu_column(img, W - 34, H // 2 + 10, hover="shield" if not context else None,
                active="briefcase" if context else None)
    if context:
        carry_chip(img, W // 2 - 80, H - 120)
        hint_chip(img, W // 2, H - 182, "ЛКМ — удар  ·  держите E у постамента — украсть")
    img.convert("RGB").save(os.path.join(HUD, name + ".png"))
    return img


def phone(kind="doom", name="hud_phone_doom"):
    W, H = 2340, 1080
    notch = 110
    img = background(W, H, night=kind == "doom")
    timer(img, W // 2, 64, kind, 1.1)
    stats(img, notch + 40, 170, 1.15)
    menu_column(img, W - notch - 40, 410, 1.15, pc=False)
    if kind == "doom":  # PvP только в Судную ночь (D37)
        attack_button(img, W - notch - 390, H - 250, 105)
    carry_chip(img, W // 2 - 40, H - 140, 1.1, pc=False)
    out = roblox_phone(img, notch)
    out.convert("RGB").save(os.path.join(HUD, name + ".png"))
    return out


ZONES = {  # имя, цвет
    "roblox": ("Roblox (не занимать)", (150, 150, 160)),
    "stats": ("Статистика", (255, 196, 44)),
    "menu": ("Меню", (90, 170, 255)),
    "timer": ("Таймер", (255, 120, 90)),
    "context": ("Действия", (110, 230, 120)),
}


def zone(img, box, kind):
    name, col = ZONES[kind]
    rounded(img, box, 16, col + (70,), outline=col + (255,), width=4)
    text(img, (box[0] + 14, box[1] + 10), name, 22, anchor="la", weight="Black", sw=3)


def zones_pc():
    W, H = 1920, 1080
    img = pc("day", True, "_tmp")
    os.remove(os.path.join(HUD, "_tmp.png"))
    for box in ((8, 6, 112, 62), (W - 266, 6, W - 8, 62)):
        zone(img, box, "roblox")
    zone(img, (14, 360, 420, 640), "stats")
    zone(img, (W - 220, 300, W - 14, 760), "menu")
    zone(img, (W // 2 - 260, 56, W // 2 + 260, 230), "timer")
    zone(img, (W // 2 - 520, H - 200, W // 2 + 520, H - 40), "context")
    img.convert("RGB").save(os.path.join(HUD, "hud_zones_pc.png"))


def zones_phone():
    W, H, notch = 2340, 1080, 110
    img = background(W, H)
    timer(img, W // 2, 64, "doom", 1.1)
    stats(img, notch + 40, 170, 1.15)
    menu_column(img, W - notch - 40, 410, 1.15, pc=False)
    attack_button(img, W - notch - 390, H - 250, 105)
    carry_chip(img, W // 2 - 40, H - 140, 1.1, pc=False)
    img = roblox_phone(img, notch)
    for box in ((notch + 4, 8, notch + 134, 74), (notch + 60, H - 390, notch + 380, H - 70),
                (W - notch - 260, H - 300, W - notch - 50, H - 90)):
        zone(img, box, "roblox")
    zone(img, (notch + 20, 150, notch + 520, 500), "stats")
    zone(img, (W - notch - 190, 260, W - notch - 14, 640), "menu")
    zone(img, (W // 2 - 300, 50, W // 2 + 300, 250), "timer")
    zone(img, (W // 2 - 520, H - 160, W // 2 + 440, H - 60), "context")
    zone(img, (W - notch - 510, H - 370, W - notch - 270, H - 120), "context")
    img.convert("RGB").save(os.path.join(HUD, "hud_zones_phone.png"))


def timer_states():
    W, H = 1000, 380
    img = Image.new("RGBA", (W, H), (34, 44, 80, 255))
    for i, k in enumerate(("day", "night", "prep", "doom")):
        timer(img, (250, 750)[i % 2], (40, 210)[i // 2], k, 1.0, (0.7, 0.4, 0.55, 0.3)[i])
    img.convert("RGB").save(os.path.join(HUD, "timer_states.png"))


def before_after(after):
    before = Image.open(os.path.join(D48, "ref", "hud_before.jpg")).convert("RGB")
    sw, sh = before.size
    tw = int(sh * 1920 / 1080)
    x0 = (sw - tw) // 2
    before = before.crop((x0, 0, x0 + tw, sh)).resize((1920, 1080), Image.LANCZOS)
    W = 1920
    img = Image.new("RGB", (W * 2 + 40, 1080 + 120), (24, 28, 48))
    img.paste(before, (0, 120))
    img.paste(after.convert("RGB"), (W + 40, 120))
    canvas = img.convert("RGBA")
    text(canvas, (W // 2, 60), "СЕЙЧАС", 54, anchor="mm")
    text(canvas, (W + 40 + W // 2, 60), "D48 — НОВЫЙ HUD", 54, fill=(255, 214, 90), anchor="mm")
    canvas = canvas.resize((canvas.width // 2, canvas.height // 2), Image.LANCZOS)
    canvas.convert("RGB").save(os.path.join(HUD, "hud_before_after.png"))


icon_sheet()
power_compare()
timer_states()
day = pc("day", False, "hud_pc_day")
pc("doom", True, "hud_pc_doom")
phone("doom", "hud_phone_doom")
phone("day", "hud_phone_day")
before_after(day)
zones_pc()
zones_phone()
print("ok")
