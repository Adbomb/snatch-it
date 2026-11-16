"""Двухфазная проба «Хвоста-кистеня»: подписи на кадрах, сводные кадры, раскадровка, контакт крупно, сравнения.
python boss4_sphinx_combo_post.py <папка frames пробы> <папка frames прежнего исследования хвоста> <папка назначения>
Кадры для видео — <frames пробы>/labeled/<съёмка>/NNNN.png (MP4 собирает boss4_sphinx_anim_video.py)."""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
root, tail_root, dest = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
KEY = sys.argv[4] if len(sys.argv) > 4 else "c58"
FPS = 30
PAD = 10  # кадров стойки перед клипом в каждой съёмке
BOLD = "C:/Windows/Fonts/arialbd.ttf"


def font(size):
    return ImageFont.truetype(BOLD, size)


GOLD, WHITE, RED, DARK, BLUE = (255, 210, 63), (240, 242, 248), (255, 92, 80), (14, 16, 22), (120, 190, 255)
TITLE = {"combotest_" + KEY: "Проба C: хвост + лапа", "heavy_paw": "Тяжёлая лапа", "tail_strike": "Хвост-кистень (сейчас)"}
PHASES = [(0.0, 0.18, "1. Перенос веса, хвост заносится"), (0.18, 0.47, "2. Разворот корпуса, занос зада"),
          (0.47, 0.635, "3. Взмах хвостом, лапа поднимается"), (0.635, 0.734, "4. Удар левой лапой"),
          (0.734, 0.82, "5. Контакт — момент урона"), (0.82, 1.401, "6. Возврат в стойку")]
VIEW_NAME = {"player": "как видит игрок", "front": "спереди", "side": "сбоку (левый бок)", "top_wide": "сверху",
             "top_nohead": "сверху, голова скрыта", "34": "три четверти", "hit_back": "крупно: из-за плеча игрока",
             "hit_top_nohead": "крупно сверху, голова скрыта"}

meta = {}
for f in root.glob("meta_combo_*.json"):
    meta.update(json.load(open(f, encoding="utf-8")))


def outlined(draw, xy, text, fnt, fill, anchor="la"):
    x, y = xy
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        draw.text((x + dx, y + dy), text, font=fnt, fill=DARK, anchor=anchor)
    draw.text(xy, text, font=fnt, fill=fill, anchor=anchor)


def phase_of(clip, t):
    if not clip.startswith("combotest"):
        return ""
    return next((name for a, b, name in PHASES if a - 1e-6 <= t < b - 1e-6), "")


def frames_of(folder):
    return sorted(Path(folder).glob("*.png"))


def fit(im, size):
    """Картинка в ячейке size: по высоте, по центру (квадратный вид сверху — с полями)."""
    w, h = size
    k = min(w / im.width, h / im.height)
    small = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    cell = Image.new("RGB", size, DARK)
    cell.paste(small, ((w - small.width) // 2, (h - small.height) // 2))
    return cell


# ── 1. Подписи на кадрах съёмок ──────────────────────────────────────────────────────────────────────────────
labeled = {}
for shot, info in sorted(meta.items()):
    files = frames_of(root / shot)
    if len(files) != len(info["frames"]):
        print("ПРОПУСК", shot, len(files), "кадров вместо", len(info["frames"]))
        continue
    out = root / "labeled" / shot
    out.mkdir(parents=True, exist_ok=True)
    mark_left = 0
    view = VIEW_NAME.get(info["view"], info["view"])
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGB")
        d = ImageDraw.Draw(im)
        row = info["frames"][i]
        outlined(d, (16, 12), TITLE.get(row["clip"], "Стойка"), font(26), GOLD)
        outlined(d, (16, 44), f"{row['t']:.2f} с", font(20), WHITE)
        ph = phase_of(row["clip"], row["t"])
        if ph:
            outlined(d, (16, im.height - 38), ph, font(22), WHITE)
        outlined(d, (im.width - 14, im.height - 34), view, font(18), BLUE, anchor="ra")
        if any("контакт" in e for e in row["events"]):
            mark_left = 4
        if mark_left > 0:
            outlined(d, (im.width - 16, 12), "КОНТАКТ", font(34), RED, anchor="ra")
            d.rectangle((0, im.height - 6, im.width, im.height), fill=RED)
            mark_left -= 1
        im.save(out / f.name)
    labeled[shot] = out
    print("ПОДПИСИ", shot, len(files))


# ── 2. Четыре вида в одном кадре ─────────────────────────────────────────────────────────────────────────────
def grid(name, shots, cell=(854, 480)):
    lists = [frames_of(root / "labeled" / s) for s in shots]
    n = min(len(x) for x in lists)
    out = root / "labeled" / name
    out.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        page = Image.new("RGB", (cell[0] * 2, cell[1] * 2), DARK)
        for k, files in enumerate(lists):
            page.paste(fit(Image.open(files[i]).convert("RGB"), cell), ((k % 2) * cell[0], (k // 2) * cell[1]))
        page.save(out / f"{i:04d}.png")
    print("СЕТКА", name, n)


grid(f"combo_{KEY}_grid", [f"combo_{KEY}_{v}" for v in ("player", "front", "top_nohead", "side")])


# ── 3. Раскадровка ключевых фаз ──────────────────────────────────────────────────────────────────────────────
STORY = [(0.0, "стойка"), (0.167, "перенос веса,\nхвост заносится"), (0.333, "разворот,\nзад заносит"), (0.467, "хвост на\nширокой дуге"),
         (0.567, "кисть прошла\nдугу"), (0.633, "лапа занесена"), (0.7, "удар лапой"), (0.767, "КОНТАКТ\n(урон на 0.75 с)"),
         (0.833, "прижим"), (1.0, "лапа на месте"), (1.2, "зад обратно"), (1.4, "стойка")]


def storyboard(path, views, cell=(480, 270)):
    cols = len(STORY)
    half = cols // 2
    rows_per_view = 2
    cap = 64
    page = Image.new("RGB", (half * cell[0], len(views) * rows_per_view * (cell[1] + cap) + 54), DARK)
    d = ImageDraw.Draw(page)
    d.text((16, 10), "Проба C «хвост + лапа»: ключевые фазы (время от начала клипа, секунды)", font=font(30), fill=GOLD)
    y = 54
    for view in views:
        files = frames_of(root / f"combo_{KEY}_{view}")
        for r in range(rows_per_view):
            for c in range(half):
                t, text = STORY[r * half + c]
                im = fit(Image.open(files[PAD + round(t * FPS)]).convert("RGB"), cell)
                page.paste(im, (c * cell[0], y))
                hit = "КОНТАКТ" in text
                d.text((c * cell[0] + 10, y + cell[1] + 4), f"{t:.2f} с — " + text.replace("\n", " "), font=font(19),
                       fill=RED if hit else WHITE)
                if hit:
                    d.rectangle((c * cell[0], y, (c + 1) * cell[0] - 1, y + cell[1] - 1), outline=RED, width=4)
            d.text((half * cell[0] - 12, y + 6), VIEW_NAME[view], font=font(18), fill=BLUE, anchor="ra")
            y += cell[1] + cap
    path.parent.mkdir(parents=True, exist_ok=True)
    page.save(path, quality=90)
    print("РАСКАДРОВКА", path.name, page.size)


storyboard(dest / "storyboard_34_player.jpg", ["34", "player"])
storyboard(dest / "storyboard_top_side.jpg", ["top_nohead", "side"])


# ── 4. Контакт крупно: ровно 0.75 с ──────────────────────────────────────────────────────────────────────────
def contact_page(path):
    a = Image.open(root / f"still_{KEY}_hit_back.png").convert("RGB")
    b = fit(Image.open(root / f"still_{KEY}_hit_top_nohead.png").convert("RGB"), (720, 720))
    c = fit(Image.open(root / f"still_{KEY}_34.png").convert("RGB"), (1280, 720))
    e = fit(Image.open(root / f"still_{KEY}_top_nohead.png").convert("RGB"), (720, 720))
    page = Image.new("RGB", (2000, 1440 + 70), DARK)
    d = ImageDraw.Draw(page)
    d.text((16, 14), "Проба C: момент контакта, 0.75 с (единственный момент урона)", font=font(34), fill=GOLD)
    for im, xy, text in ((a, (0, 70), "из-за плеча игрока: подошва левой лапы лежит на его правом боку"),
                         (b, (1280, 70), "сверху, голова скрыта"),
                         (c, (0, 790), "три четверти: корпус развёрнут на 57°, хвост уже обошёл левый бок"),
                         (e, (1280, 790), "сверху, голова скрыта: весь босс")):
        page.paste(im, xy)
        outlined(d, (xy[0] + 14, xy[1] + im.height - 40), text, font(22), WHITE)
    page.save(path, quality=90)
    print("КОНТАКТ", path.name, page.size)


contact_page(dest / "contact_075.jpg")


# ── 5. Сравнение трёх вариантов: одинаковые камеры и масштаб ─────────────────────────────────────────────────
ABC = [("A. Сейчас: 58°, бьёт хвост", "до игрока 8.9 стада", tail_root / "tailnow_player", tail_root / "tailnow_top_wide"),
       ("B. Проба: 82° и шаг вбок", "кисть касается игрока", tail_root / "tailtest_step82_player", tail_root / "tailtest_step82_top_wide"),
       ("C. Проба: хвост + лапа, 58°", "лапа касается игрока", root / f"combo_{KEY}_player", root / f"combo_{KEY}_top_wide")]


def abc_frame(i, cell=(640, 360), big=False):
    head = 76
    page = Image.new("RGB", (cell[0] * 3, cell[1] * 2 + head), DARK)
    d = ImageDraw.Draw(page)
    t = (i - PAD) / FPS
    for c, (title, note, pl, top) in enumerate(ABC):
        d.text((c * cell[0] + 14, 6), title, font=font(26), fill=GOLD)
        d.text((c * cell[0] + 14, 40), ("в момент контакта: " + note) if big else note, font=font(20), fill=WHITE)
        page.paste(fit(Image.open(frames_of(pl)[i]).convert("RGB"), cell), (c * cell[0], head))
        page.paste(fit(Image.open(frames_of(top)[i]).convert("RGB"), cell), (c * cell[0], head + cell[1]))
    label = f"{t:.2f} с" if 0 <= t <= 1.401 else "стойка"
    outlined(d, (page.width - 16, head + 8), label, font(24), WHITE, anchor="ra")
    if 0.733 - 1e-6 <= t < 0.87:
        outlined(d, (page.width - 16, head + 40), "КОНТАКТ", font(30), RED, anchor="ra")
        d.rectangle((0, page.height - 6, page.width, page.height), fill=RED)
    outlined(d, (12, head + cell[1] - 30), "как видит игрок", font(18), BLUE)
    outlined(d, (12, head + 2 * cell[1] - 32), "сверху", font(18), BLUE)
    return page


out = root / "labeled" / "compare_abc"
out.mkdir(parents=True, exist_ok=True)
n = min(len(frames_of(x[2])) for x in ABC)
for i in range(n):
    abc_frame(i).save(out / f"{i:04d}.png")
abc_frame(PAD + 23, cell=(854, 480), big=True).save(dest / "compare_abc_contact.jpg", quality=90)
print("СРАВНЕНИЕ ABC", n)


# ── 6. Два удара лапой рядом: «Тяжёлая лапа» и проба C ───────────────────────────────────────────────────────
def paws_frame(i, cell=(854, 480)):
    head = 50
    page = Image.new("RGB", (cell[0] * 2, cell[1] * 2 + head), DARK)
    d = ImageDraw.Draw(page)
    for c, (title, pl, top) in enumerate((("«Тяжёлая лапа» (основная атака): правая лапа, сверху вниз", root / "heavynow_player", root / "heavynow_top_nohead"),
                                          ("Проба C: взмах хвостом, затем левая лапа сбоку", root / f"combo_{KEY}_player", root / f"combo_{KEY}_top_nohead"))):
        d.text((c * cell[0] + 14, 10), title, font=font(24), fill=GOLD)
        page.paste(fit(Image.open(frames_of(pl)[i]).convert("RGB"), cell), (c * cell[0], head))
        page.paste(fit(Image.open(frames_of(top)[i]).convert("RGB"), cell), (c * cell[0], head + cell[1]))
        t = (i - PAD) / FPS
        hit = 0.7 if c == 0 else 0.75
        outlined(d, (c * cell[0] + 14, head + 8), f"{t:.2f} с" if t >= 0 else "стойка", font(22), WHITE)
        if hit - 0.02 <= t < hit + 0.12:
            outlined(d, ((c + 1) * cell[0] - 14, head + 8), "КОНТАКТ", font(30), RED, anchor="ra")
    return page


out = root / "labeled" / "compare_paws"
out.mkdir(parents=True, exist_ok=True)
n = min(len(frames_of(root / "heavynow_player")), len(frames_of(root / f"combo_{KEY}_player")))
for i in range(n):
    paws_frame(i).save(out / f"{i:04d}.png")
# лист: замах и контакт каждого удара
picks = [(PAD + 13, PAD + 19), (PAD + 21, PAD + 23)]  # (кадр «Тяжёлой лапы», кадр пробы): замах; контакт
cell = (854, 480)
page = Image.new("RGB", (cell[0] * 2, cell[1] * 2 + 60), DARK)
d = ImageDraw.Draw(page)
d.text((14, 12), "Два удара лапой с камеры игрока: замах (верх) и контакт (низ)", font=font(30), fill=GOLD)
for r, (ih, ic) in enumerate(picks):
    for c, (folder, i, text) in enumerate(((root / "heavynow_player", ih, "«Тяжёлая лапа»: правая лапа над головой → удар сверху вниз"),
                                           (root / f"combo_{KEY}_player", ic, "Проба C: корпус боком, хвост прошёл дугу → левая лапа сбоку"))):
        page.paste(fit(Image.open(frames_of(folder)[i]).convert("RGB"), cell), (c * cell[0], 60 + r * cell[1]))
        outlined(d, (c * cell[0] + 14, 60 + r * cell[1] + 10), text, font(20), WHITE)
        outlined(d, (c * cell[0] + 14, 60 + (r + 1) * cell[1] - 36), f"{(i - PAD) / FPS:.2f} с", font(22), GOLD)
page.save(dest / "compare_heavy_paw.jpg", quality=90)
print("СРАВНЕНИЕ ЛАП", n)
