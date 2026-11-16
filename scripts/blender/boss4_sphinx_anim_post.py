"""Босс 4 «Сфинкс-лежебока»: подписи на кадрах анимаций, GIF, раскадровки и схема удара хвостом.

Берёт кадры съёмок и их описание (meta_*.json) из scripts/blender/boss4_sphinx_anim.py (режим render или all).
Кадры с подписями (название клипа, время, отметка «КОНТАКТ») пишет в <frames>/labeled/<съёмка> — из них
scripts/blender/boss4_sphinx_anim_video.py собирает MP4; GIF (15 кадров в секунду, ширина 480) — в <назначение>/gif,
раскадровки и схему удара — в <назначение>/sheets. Нужен Pillow; шрифт — Arial из Windows.
Запуск: python scripts/blender/boss4_sphinx_anim_post.py <папка frames> <папка назначения> [съёмка,съёмка|tail_scheme]
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
root, dest = Path(sys.argv[1]), Path(sys.argv[2])
only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
FPS = 30
BOLD = "C:/Windows/Fonts/arialbd.ttf"
F_TITLE, F_TIME, F_MARK = ImageFont.truetype(BOLD, 26), ImageFont.truetype(BOLD, 20), ImageFont.truetype(BOLD, 34)
GOLD, WHITE, RED, DARK = (255, 210, 63), (240, 242, 248), (255, 92, 80), (14, 16, 22)

meta = {}
for f in root.glob("meta_*.json"):
    meta.update(json.load(open(f, encoding="utf-8")))
tail = meta.pop("tail_path", None)


def outlined(draw, xy, text, font, fill):
    x, y = xy
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        draw.text((x + dx, y + dy), text, font=font, fill=DARK)
    draw.text(xy, text, font=font, fill=fill)


for shot, info in sorted(meta.items()):
    if only and shot not in only:
        continue
    src = root / shot
    files = sorted(src.glob("*.png"))
    if len(files) != len(info["frames"]):
        print("ПРОПУСК", shot, len(files), "кадров вместо", len(info["frames"]))
        continue
    out = root / "labeled" / shot
    out.mkdir(parents=True, exist_ok=True)
    frames, mark, mark_left = [], "", 0
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGB")
        d = ImageDraw.Draw(im)
        row = info["frames"][i]
        outlined(d, (16, 12), row["title"], F_TITLE, GOLD)
        outlined(d, (16, 44), f"{row['t']:.2f} с", F_TIME, WHITE)
        for e in row["events"]:
            mark, mark_left = e, 6 if "контакт" in e else 4
        if mark_left > 0:
            hit = "контакт" in mark
            text = "КОНТАКТ" if hit else mark
            w = d.textlength(text, font=F_MARK if hit else F_TIME)
            outlined(d, (im.width - w - 18, 12), text, F_MARK if hit else F_TIME, RED if hit else WHITE)
            if hit:
                d.rectangle((0, im.height - 8, im.width, im.height), fill=RED)
            mark_left -= 1
        im.save(out / f.name)
        frames.append(im)
    gif_dir = dest / "gif"
    gif_dir.mkdir(parents=True, exist_ok=True)
    small = [im.resize((480, round(480 * im.height / im.width)), Image.LANCZOS) for im in frames[::2]]
    small[0].save(gif_dir / f"{shot}.gif", save_all=True, append_images=small[1:], duration=round(2000 / FPS), loop=0,
                  optimize=True)
    # раскадровка для просмотра: каждый 3-й кадр (у длинных — реже)
    step = max(3, len(frames) // 40)
    pick = frames[::step]
    cols = 8
    tw = 427
    th = round(tw * frames[0].height / frames[0].width)
    rows = (len(pick) + cols - 1) // cols
    page = Image.new("RGB", (cols * tw, rows * th), DARK)
    for k, im in enumerate(pick):
        page.paste(im.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
    sheet_dir = dest / "sheets"
    sheet_dir.mkdir(parents=True, exist_ok=True)
    page.save(sheet_dir / f"{shot}.jpg", quality=86)
    print("ГОТОВО", shot, len(frames), "кадров; gif", round((gif_dir / f"{shot}.gif").stat().st_size / 1e6, 2), "МБ")

if tail and meta.get("tail_strike_top") and (not only or "tail_scheme" in only):
    # схема удара хвостом: вид сверху в момент контакта, путь кисти, зона удара
    info = meta.get("tail_strike_top")
    src = root / "tail_strike_top"
    files = sorted(src.glob("*.png"))
    clip_idx = [i for i, r in enumerate(info["frames"]) if r["clip"] == "tail_strike"]
    hit_t = next(v for k, v in tail["events"].items() if "контакт" in k)
    start_t = next(v for k, v in tail["events"].items() if "начало" in k)
    hit_frame = min(range(len(tail["frames"])), key=lambda k: abs(k / FPS - hit_t))
    im = Image.open(files[clip_idx[hit_frame]]).convert("RGB")
    scale = 2
    im = im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    eye, target, lens = tail["camera"]
    width, height = im.size

    def px(p):
        k = (width / 2) / ((eye[2] - p[2]) * 18.0 / lens)
        return (width / 2 - k * (p[0] - eye[0]), height / 2 + k * (p[1] - eye[1]))

    pts = [px(p) for p in tail["frames"]]
    a, b = round(start_t * FPS) - 14, hit_frame
    for k in range(max(a, 0), b):
        d.line((pts[k], pts[k + 1]), fill=GOLD if k / FPS >= start_t else WHITE, width=6)
    for k in range(b, min(b + 4, len(pts) - 1)):
        d.line((pts[k], pts[k + 1]), fill=(255, 150, 120), width=4)
    x, y = pts[b]
    r = (width / 2) / (eye[2] * 18.0 / lens) * 3.0
    d.ellipse((x - r, y - r, x + r, y + r), outline=RED, width=6)
    big, mid = ImageFont.truetype(BOLD, 34), ImageFont.truetype(BOLD, 26)
    outlined(d, (x - r, y + r + 8), f"КОНТАКТ, {hit_t:.2f} с", big, RED)
    hx, hy, _ = tail["frames"][b]
    outlined(d, (x - r, y + r + 50), f"{abs(hx):.1f} стада влево от оси, {abs(hy):.1f} вперёд от центра", mid, WHITE)
    sx, sy = pts[max(a, 0)]
    outlined(d, (sx + 14, sy - 14), "замах", mid, WHITE)
    gx, gy = px((0.0, -9.5, 0.0))
    d.line((gx - 16, gy, gx + 16, gy), fill=WHITE, width=4)
    d.line((gx, gy - 16, gx, gy + 16), fill=WHITE, width=4)
    outlined(d, (gx + 22, gy - 16), "дальность атаки игры: 9.5 стада от центра", mid, WHITE)
    outlined(d, (20, 16), "«Хвост-кистень»: путь кисти сверху (жёлтый — удар, белый — замах)", big, GOLD)
    (dest / "sheets").mkdir(parents=True, exist_ok=True)
    im.save(dest / "sheets" / "tail_strike_scheme.jpg", quality=90)
    print("ГОТОВО схема удара хвостом: контакт", [round(c, 2) for c in tail["frames"][b]])
