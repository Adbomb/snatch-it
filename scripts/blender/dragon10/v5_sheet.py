"""Лист формы Короля-дракона v5 (гибрид A+B): спереди, сбоку, 3/4, чёрные силуэты, сзади, голова, разбор.

  python scripts/blender/dragon10/v5_sheet.py   → assets/concepts/bosses_5_10/boss10_v5/v5_form.png
"""

import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "assets", "concepts", "bosses_5_10", "boss10_v5")
RAW = os.path.join(OUT, "raw")
BG, PANEL, INK, DIM, ACC = (22, 24, 33), (35, 38, 51), (240, 242, 248), (165, 170, 188), (255, 196, 64)


def font(size, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf", size)


def fit(im, w, h):
    k = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def contain(im, w, h, bg=(250, 250, 250)):
    k = min(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    out = Image.new("RGB", (w, h), bg)
    out.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    return out


def silhouette(path):
    im = Image.open(path).convert("RGBA")
    a = im.split()[3].point(lambda v: 255 if v > 40 else 0)
    out = Image.new("RGB", im.size, (250, 250, 250))
    out.paste((10, 10, 14), mask=a)
    return out


def para(d, x, y, text, width, size=22, fill=DIM, gap=5):
    f = font(size)
    line = ""
    for word in text.split():
        t = (line + " " + word).strip()
        if d.textlength(t, font=f) <= width:
            line = t
        else:
            d.text((x, y), line, font=f, fill=fill)
            y += size + gap
            line = word
    if line:
        d.text((x, y), line, font=f, fill=fill)
        y += size + gap
    return y


def main():
    st = json.load(open(os.path.join(RAW, "stats.json"), encoding="utf-8"))
    sx, sy, sz = st["size"]
    W, H = 2400, 2480
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.rectangle((0, 0, W, 110), fill=PANEL)
    d.text((30, 12), "Король-дракон v5 — гибрид A «Титан» + B «Владыка»: форма", font=font(46, True), fill=INK)
    d.text((32, 72), "Один нейтральный материал; без короны, брони, мантии и текстур. Blender, стиль D39 (ступени, острые "
                     "рёбра). Не загружалось в Roblox.", font=font(23), fill=DIM)
    T = 776
    y = 130
    for i, (v, label) in enumerate((("front", "Спереди"), ("side", "Сбоку"), ("34", "3/4"))):
        x = 24 + i * (T + 12)
        sheet.paste(fit(Image.open(os.path.join(RAW, f"{v}.png")).convert("RGB"), T, T), (x, y))
        d.text((x + 14, y + T - 44), label, font=font(30, True), fill=INK)
    y += T + 16
    S = 560
    for i, (v, label) in enumerate((("front", "Силуэт спереди"), ("side", "Силуэт сбоку"), ("34", "Силуэт 3/4"))):
        x = 24 + i * (T + 12)
        sil = silhouette(os.path.join(RAW, f"{v}_sil.png"))
        box = sil.convert("L").point(lambda c: 255 if c < 128 else 0).getbbox()
        sheet.paste(contain(sil.crop(box), T - 40, S - 70), (x + 20, y + 50))
        d.rectangle((x, y, x + T, y + 48), fill=(250, 250, 250))
        d.rectangle((x, y + 48, x + 20, y + S), fill=(250, 250, 250))
        d.rectangle((x + T - 20, y + 48, x + T, y + S), fill=(250, 250, 250))
        d.rectangle((x, y + S - 20, x + T, y + S), fill=(250, 250, 250))
        d.text((x + 14, y + 10), label, font=font(26, True), fill=(30, 30, 40))
    y += S + 16
    sheet.paste(fit(Image.open(os.path.join(RAW, "back.png")).convert("RGB"), T, T - 120), (24, y))
    d.text((38, y + T - 164), "Сзади (проверка)", font=font(26, True), fill=INK)
    sheet.paste(fit(Image.open(os.path.join(RAW, "head.png")).convert("RGB"), T, T - 120), (24 + T + 12, y))
    d.text((38 + T + 12, y + T - 164), "Голова (проверка)", font=font(26, True), fill=INK)
    px = 24 + 2 * (T + 12)
    d.rectangle((px, y, W - 24, y + T - 120), fill=PANEL)
    yy = y + 14
    d.text((px + 18, yy), "От A «Титан»", font=font(26, True), fill=ACC)
    yy = para(d, px + 18, yy + 38, "массивный четвероногий корпус, широкая грудь с грудными мышцами, мощные лапы с "
                                   "локтями, крупная голова, толстый хвост.", T - 40, size=21)
    d.text((px + 18, yy + 6), "От B «Владыка»", font=font(26, True), fill=ACC)
    yy = para(d, px + 18, yy + 44, "грудь поднята, голова высоко на S-образной шее, длинные рога дугой с загнутыми "
                                   "концами, большие раскрытые крылья.", T - 40, size=21)
    d.text((px + 18, yy + 6), "Новое", font=font(26, True), fill=ACC)
    yy = para(d, px + 18, yy + 44, "морда ступенями (три сужения, гребень переносицы), скулы с шипами, тяжёлые надбровья, "
                                   "приоткрытая сильная челюсть с клыками; раздельные пальцы с крупными когтями; крыло "
                                   "растёт из мышцы на лопатке, перепонка крепится к боку; живая поза: голова чуть "
                                   "повёрнута, левая лапа шагает, крылья раскрыты по-разному, хвост S-изгибом.",
              T - 40, size=21)
    para(d, px + 18, yy + 10, f"Модель {sx} × {sy} × {sz}; в игре ×3 ≈ {sx * 3:.0f} × {sy * 3:.0f} × {sz * 3:.0f} стадов "
                              f"(с рогами выше ориентира 35 — масштаб правится при экспорте без изменения пропорций). "
                              f"Блок-аут: {st['tris']} треугольников.", T - 40, size=20, fill=INK)
    sheet.crop((0, 0, W, y + T - 120 + 24)).save(os.path.join(OUT, "v5_form.png"))
    print("DONE")


if __name__ == "__main__":
    main()
