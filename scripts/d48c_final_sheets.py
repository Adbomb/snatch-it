"""D48-C, фаза 2 — листы для утверждения финальных Blender-моделей: сводный лист рендеров музея, план с размерами
(исправленная планировка: фасад галерей z −19, клумбы), лист устройств защиты по состояниям, лист оптимизации.
Собирает рендеры scripts/blender/d48_final.py и d48_final_devices.py, раскладку d48c_layout.py, учёт треугольников
из assets/models/Pack3_d48.layout.json, Pack4_d48_defense.layout.json и c2/mesh_placement.json.
Запуск: python scripts/d48c_final_sheets.py  → assets/concepts/d48/c2/sheets/*.png
"""

import glob
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "blender"))
import d48c_layout as L  # noqa: E402

C2 = os.path.join(ROOT, "assets", "concepts", "d48", "c2")
REN, DEV, OUT = os.path.join(C2, "renders"), os.path.join(C2, "devices"), os.path.join(C2, "sheets")
os.makedirs(OUT, exist_ok=True)
INK, GOLD, SOFT, WHITE, GREEN, RED = (24, 20, 46), (255, 214, 90), (205, 216, 245), (255, 255, 255), (124, 255, 107), \
    (255, 150, 150)
SIZE, ORTHO, CZ = 1300, 66.0, -0.6
K = SIZE / ORTHO


def font(weight, size):
    path = None
    for p in sorted(glob.glob(os.path.expandvars(rf"%LOCALAPPDATA%\Roblox\Versions\*\content\fonts\Montserrat-{weight}.ttf"))):
        path = p
    return ImageFont.truetype(path, size)


def say(d, xy, body, size=26, fill=WHITE, anchor="mm", weight="Black", sw=None):
    d.text(xy, body, font=font(weight, size), fill=fill, stroke_width=max(2, size // 8) if sw is None else sw,
           stroke_fill=INK, anchor=anchor)


def gradient(w, h, top=(43, 58, 103), bot=(22, 28, 54)):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)))
    return img


def paste_round(sheet, im, xy, r=18):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    sheet.paste(im, xy, mask)


def px(x, z):
    return SIZE / 2 - x * K, SIZE / 2 - (z - CZ) * K


def dim(d, a, b, body, offset=(0, 0), size=20, col=(255, 236, 140)):
    (x0, y0), (x1, y1) = a, b
    d.line([a, b], fill=col, width=4)
    for (x, y) in (a, b):
        if abs(x1 - x0) > abs(y1 - y0):
            d.line([(x, y - 12), (x, y + 12)], fill=col, width=4)
        else:
            d.line([(x - 12, y), (x + 12, y)], fill=col, width=4)
    say(d, ((x0 + x1) / 2 + offset[0], (y0 + y1) / 2 + offset[1]), body, size, col)


PLACEMENT = json.load(open(os.path.join(C2, "mesh_placement.json"), encoding="utf-8"))["levels"]
PACK3 = json.load(open(os.path.join(ROOT, "assets", "models", "Pack3_d48.layout.json"), encoding="utf-8"))["d48"]
PACK4 = json.load(open(os.path.join(ROOT, "assets", "models", "Pack4_d48_defense.layout.json"), encoding="utf-8"))[
    "d48_defense"]
RIGS = json.load(open(os.path.join(C2, "defense_rigs.json"), encoding="utf-8"))
PART1 = json.load(open(os.path.join(ROOT, "assets", "concepts", "d48", "c1", "bricks", "museum_L1.json"),
                       encoding="utf-8"))["total"]
PART10 = json.load(open(os.path.join(ROOT, "assets", "concepts", "d48", "c1", "bricks", "museum_L10.json"),
                        encoding="utf-8"))["total"]
VAULT = ("D48_VaultShell", "D48_Safe", "D48_Terminal", "D48_Archive", "D48_Security", "D48_Lockers")


def split(level):
    items = PLACEMENT[str(level)]["items"]
    vault = sum(PACK3[i["model"]]["triangles"] for i in items if i["model"] in VAULT)
    total = PLACEMENT[str(level)]["triangles"]
    return total - vault, vault, PLACEMENT[str(level)]["meshparts"]


# ── 1. Сводный лист рендеров музея ─────────────────────────────────────────────────────────────────────────────
SHOTS = [("L1_exterior", "Ур. 1 — снаружи: как сейчас"), ("L1_hall_from_entrance", "Ур. 1 — зал: 6 мест"),
         ("L10_exterior", "Ур. 10 — галереи вдоль портика"), ("L10_hall_inside", "Ур. 10 — 8 ниш зала"),
         ("L10_overview", "Ур. 10 — зал и галереи сверху"), ("L10_gallery", "Галерея: 6 мест"),
         ("L10_gallery_arch", "Арка из входного зала"), ("L10_vault_gate", "Решётка хранилища: чужим закрыто"),
         ("L10_stair_down", "Лестница (вид владельца)"), ("L10_vault_safe", "Сейф коллекции"),
         ("L10_vault_main", "Хранилище"), ("L10_vault_overview", "Хранилище сверху")]


def contact():
    cw, ch, cols = 560, 315, 3
    rows = (len(SHOTS) + cols - 1) // cols
    W, H = cols * cw + (cols + 1) * 24, 160 + rows * (ch + 70)
    sheet = gradient(W, H)
    d = ImageDraw.Draw(sheet)
    say(d, (W // 2, 58), "D48-C — финальные Blender-модели музея", 46)
    say(d, (W // 2, 108), "меши-модули (FBX Pack3_d48), материал игры LegoSquaresSoft по UV, без новых текстур; "
                          "уровни 1 и 10", 22, SOFT, weight="Bold")
    for k, (name, cap) in enumerate(SHOTS):
        r, c = divmod(k, cols)
        x, y = 24 + c * (cw + 24), 160 + r * (ch + 70)
        path = os.path.join(REN, name + ".png")
        if not os.path.exists(path):
            continue
        paste_round(sheet, Image.open(path).convert("RGB").resize((cw, ch), Image.LANCZOS), (x, y))
        say(d, (x + cw // 2, y + ch + 30), cap, 22)
    sheet.save(os.path.join(OUT, "museum_final.png"))


# ── 2. План с размерами (финальные модели, уровень 10) ─────────────────────────────────────────────────────────
def plan():
    im = Image.open(os.path.join(REN, "L10_plan.png")).convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle((*px(22, 22), *px(-22, -22)), outline=(255, 255, 255, 255), width=3)
    say(d, px(-21.6, 21.4), "участок 44 × 44", 17, anchor="rb", weight="Bold")
    for p in L.places():
        x, _, z = p["center"]
        cx, cy = px(x, z)
        d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=(255, 214, 90, 230), outline=INK, width=3)
        say(d, (cx, cy - 3), str(p["slot"]), 22, INK, sw=0)
        say(d, (cx, cy + 14), f"ур.{p['unlock_compat']}", 10, INK, sw=0, weight="Bold")
    dim(d, px(29, -25.5), px(-29, -25.5), "58 ст. (галереи, как крылья D36)", (0, 22), 18)
    dim(d, px(-31.6, -19), px(-31.6, 20.7), "39,7", (-30, 0), 17)
    dim(d, px(-29, -21.0), px(-31.4, -21.0), "клумба 2,4", (-10, -18), 13, (140, 255, 160))
    dim(d, px(-22, 13), px(-18, 13), "4,0", (0, -16), 15, (140, 255, 160))
    dim(d, px(4.4, 13), px(10.7, 13), "6,3", (0, -16), 15, (140, 255, 160))
    say(d, px(23.5, -21.5), "фасад галереи z −19: до гантели 3,5 ст.", 15, (255, 236, 140), weight="Bold")
    say(d, px(0, 6.8), "ПАВИЛЬОН · решётка", 16)
    sheet = Image.new("RGB", (SIZE, SIZE + 180), (24, 28, 48))
    sheet.paste(im, (0, 180))
    d = ImageDraw.Draw(sheet)
    say(d, (SIZE // 2, 48), "D48-C — план финального музея (уровень 10, 20 мест)", 38)
    say(d, (SIZE // 2, 98), "по проверке мира: галереи короче спереди (z −19), вдоль наружных стен — клумбы", 20,
        SOFT, weight="Bold")
    say(d, (SIZE // 2, 138), "мест открыто: max(6, 2 × уровень) — 6, 6, 6, 8, 10 … 20; галереи строятся с уровня 5",
        20, GOLD, weight="Bold")
    sheet = sheet.resize((sheet.width * 4 // 5, sheet.height * 4 // 5), Image.LANCZOS)
    sheet.save(os.path.join(OUT, "plan_final.png"))


# ── 3. Защита: состояния и части ───────────────────────────────────────────────────────────────────────────────
DEVTEXT = [
    ("trap", "Ловушка", "Trap", "обычно → сработала: шипы выезжают (0,12 с), вспышка",
     "основание · блок шипов (подъём 1,35) · вспышка"),
    ("snare", "Капкан", "Snare", "раскрыт → сомкнулся (0,08 с), держит 10 с (GameConfig)",
     "основание с кнопкой · 2 челюсти (одна модель, шарнир) · кольцо"),
    ("laser", "Лазер", "Laser", "дежурит → тревога: луч 0,1 → 0,2, маяки красные",
     "стойка ×2 (одна модель) · луч — Neon-деталь по длине метки"),
    ("door", "Бронедверь", "Door", "закрыта → взлом (штурвал крутится 5 с) → открыта",
     "створка L · створка R · штурвал (едет со створкой L) · лампа · взломщик"),
    ("robot", "Робот-охранник", "Robot", "ожидание · обнаружение · атака · попадание · разрушение",
     "основание · корпус на турели · голова · 2 руки (дубинка) · разряд · тревога · искры"),
]


def devices():
    W, CARD = 1800, 430
    sheet = gradient(W, 200 + CARD * len(DEVTEXT))
    d = ImageDraw.Draw(sheet)
    say(d, (W // 2, 58), "D48-C — финальные модели защиты (Blender, подвижные части)", 44)
    say(d, (W // 2, 108), "FBX Pack4_d48_defense; огонёк состояния — роль State (цвет ставит игра); урон, время, "
                          "цены — GameConfig, не меняются", 21, SOFT, weight="Bold")
    say(d, (W // 2, 146), "бирюзовый — дежурит · жёлтый — обнаружил · красный — сработал · оранжевый — взлом · "
                          "зелёный — открыто", 20, GOLD, weight="Bold")
    for k, (key, title, rig, states, parts) in enumerate(DEVTEXT):
        y = 190 + k * CARD
        d.rounded_rectangle((30, y, W - 30, y + CARD - 24), 26, fill=(30, 38, 72))
        im = Image.open(os.path.join(DEV, f"{key}.png")).convert("RGB")
        th = CARD - 60
        tw = min(int(im.width * th / im.height), 1180)
        th = int(im.height * tw / im.width)
        paste_round(sheet, im.resize((tw, th), Image.LANCZOS), (50, y + 18 + (CARD - 60 - th) // 2))
        tx = 50 + tw + 30
        say(d, (tx, y + 46), title, 34, GOLD, anchor="lm")
        f = font("Bold", 21)
        yy = y + 92
        for body in (f"Состояния: {states}", f"Части: {parts}"):
            words, line = body.split(), ""
            for w in words:
                if d.textlength(line + " " + w, font=f) > W - 70 - tx:
                    d.text((tx, yy), line.strip(), font=f, fill=(235, 240, 255))
                    yy += 30
                    line = ""
                line += " " + w
            d.text((tx, yy), line.strip(), font=f, fill=(235, 240, 255))
            yy += 44
        say(d, (tx, y + CARD - 64), f"{RIGS['triangles'][rig]} треугольников", 24, GREEN, anchor="lm", weight="Bold")
    sheet = sheet.resize((sheet.width * 3 // 4, sheet.height * 3 // 4), Image.LANCZOS)
    sheet.save(os.path.join(OUT, "devices_final.png"))


# ── 4. Оптимизация ─────────────────────────────────────────────────────────────────────────────────────────────
def optimization():
    a1, v1, m1 = split(1)
    a10, v10, m10 = split(10)
    rows = [
        ("", "уровень 1 (6 мест)", "уровень 10 (20 мест)", "5 музеев, ур. 10"),
        ("Part-прототип: деталей", f"{PART1}", f"{PART10}", f"{5 * PART10}"),
        ("Mesh: экземпляров (MeshPart)", f"{m1}", f"{m10}", f"{5 * m10}"),
        ("Mesh: треугольников наверху", f"{a1:,}".replace(",", " "), f"{a10:,}".replace(",", " "),
         f"{5 * a10:,}".replace(",", " ")),
        ("Mesh: хранилище (только владельцу)", f"{v1:,}".replace(",", " "), f"{v10:,}".replace(",", " "),
         f"≤ {v10:,} (свой)".replace(",", " ")),
        ("Защита (≤ 5 устройств)", "≤ 6 100", "≤ 6 100", "≤ 30 000 (только ночь)"),
        ("Новые текстуры к загрузке", "0", "0", "0 (LegoSquaresSoft)"),
    ]
    heavy = sorted(((n, v["triangles"]) for n, v in PACK3.items()), key=lambda t: -t[1])[:6]
    W, H = 1800, 980
    sheet = gradient(W, H)
    d = ImageDraw.Draw(sheet)
    say(d, (W // 2, 56), "D48-C — оптимизация: Part-прототип → Blender-модули", 42)
    say(d, (W // 2, 102), "бюджет D33: музей ≤ 20 000 треугольников — наверху 17 600 на уровне 10; одинаковые модули "
                          "(постамент ×20) — один меш", 20, SOFT, weight="Bold")
    xs = [70, 760, 1080, 1400]
    for r, row in enumerate(rows):
        y = 170 + r * 70
        if r:
            d.rounded_rectangle((50, y - 28, W - 50, y + 28), 16, fill=(30, 38, 72) if r % 2 else (36, 46, 86))
        for c, cell in enumerate(row):
            say(d, (xs[c], y), cell, 22 if c == 0 else 24, GOLD if r == 0 else WHITE, anchor="lm",
                weight="Bold" if c == 0 and r else "Black")
    say(d, (70, 690), "Самые тяжёлые модули:", 24, GOLD, anchor="lm")
    for k, (n, t) in enumerate(heavy):
        say(d, (70 + (k % 3) * 560, 740 + (k // 3) * 46), f"{n.replace('D48_', '')} — {t}", 21, anchor="lm",
            weight="Bold")
    for k, line in enumerate((
            "Сделано: фаска только на крупных деталях · круги 6–24 граней · кусты и лампы — блоки D39 · крыша, "
            "галереи, решётка — отдельные модули",
            "В игре: свет хранилища и его модули — только у владельца внизу; RenderFidelity Automatic (LOD); "
            "прожектор — у занятых ниш")):
        say(d, (W // 2, 870 + k * 44), line, 19, (255, 236, 140), weight="Bold")
    sheet.save(os.path.join(OUT, "optimization.png"))


if __name__ == "__main__":
    contact()
    plan()
    devices()
    optimization()
    print("ok", split(1), split(10))
