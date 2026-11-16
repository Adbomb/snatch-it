"""Король-дракон v7, вторая итерация анимаций: подписи кадров, общий ролик, ролики залпа и уклонения с мини-картой
по данным volley_sim, таблицы, лист рига, сравнение сторон удара хвостом (PIL).

  python scripts/blender/dragon10/v7_anim2_post.py <папка кадров> <папка результата>
Читает <кадры>/frames/<клип>/*.png, frames/meta.json, anim_report.json, volley_*.json, frames/volley_*/,
tail_compare.json, tailcmp_*.png, rigdemo/*.png и rig_info.json. Пишет:
- <кадры>/labeled/<клип>/ — кадры с подписями; labeled/reel/ — все клипы подряд с титрами;
- <кадры>/labeled/volley_cinematic/, volley_<сценарий>/, volley_dodge_reel/ — залп и уклонение с мини-картой;
- <результат>/anim_table.png, rig_demo.png, tail_side_compare.png, volley_timing.png, volley_scenarios.json.
MP4 из labeled — scripts/blender/boss4_sphinx_anim_video.py.
"""

import json
import os
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont

SRC, DEST = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
FPS = 30
INK, DIM, ACC, BG, PANEL = (240, 242, 248), (170, 175, 192), (255, 196, 64), (22, 24, 33), (35, 38, 51)
ORDER = ["sleep_idle", "wake", "combat_idle", "walk", "turn_left", "claw_swipe", "bite", "tail_strike", "wing_buffet",
         "magic_volley", "hit", "victory", "defeat", "fall_asleep"]
REPEAT = {"walk": 4}
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import volley_sim as VS  # noqa: E402
GAME = {"sleep_idle": "Sleep (цикл)", "wake": "Wake 1.0 + StandUp 0.9 + ToCombat 0.5", "combat_idle": "Combat (цикл)",
        "walk": "Combat/Return: бег 10 ст/с", "turn_left": "поворот модели (нет в бою)",
        "claw_swipe": "выпад: AttackAt + HitDelay 0.25", "bite": "выпад: AttackAt + HitDelay 0.25",
        "tail_strike": "выпад: AttackAt + HitDelay 0.25", "wing_buffet": "выпад: AttackAt + HitDelay 0.25",
        "magic_volley": "новый выпад: на согласование", "hit": "реакция на удар", "victory": "Victory 2.2",
        "defeat": "Defeat 2.4", "fall_asleep": "FallAsleep 1.6"}


def font(size, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf", size)


def label_frame(im, meta, name, f, n):
    d = ImageDraw.Draw(im, "RGBA")
    W, H = im.size
    m = meta[name]
    d.rectangle((0, 0, W, 64), fill=(14, 16, 24, 205))
    d.text((18, 6), f"Король-дракон v7 — {m['title']}", font=font(30, True), fill=INK)
    loop = " · цикл" if m["loop"] else ""
    d.text((20, 40), f"{m['duration']:.2f} с · {m['frames']} кадров · 30 к/с{loop}", font=font(17), fill=DIM)
    t = f / FPS
    tw = d.textlength(f"{t:5.2f} с", font=font(26, True))
    d.text((W - tw - 20, 14), f"{t:5.2f} с", font=font(26, True), fill=ACC)
    # шкала времени с событиями
    y0 = H - 54
    d.rectangle((0, y0 - 30, W, H), fill=(14, 16, 24, 205))
    x0, x1 = 24, W - 24
    d.rectangle((x0, y0, x1, y0 + 6), fill=(70, 74, 92))
    px = x0 + (x1 - x0) * (f / max(n - 1, 1))
    d.rectangle((x0, y0, px, y0 + 6), fill=ACC)
    for ev, et in sorted(m["events"].items(), key=lambda kv: kv[1]):
        ex = x0 + (x1 - x0) * min(et / m["duration"], 1.0)
        on = abs(t - et) < 0.12
        d.rectangle((ex - 2, y0 - 6, ex + 2, y0 + 12), fill=(255, 120, 90) if on else (200, 205, 220))
        if on:
            ew = d.textlength(ev, font=font(18, True))
            d.text((min(max(ex - ew / 2, 8), W - ew - 8), y0 - 30), ev, font=font(18, True), fill=(255, 150, 110))
    d.text((24, H - 24), "жёлтый круг — край арены 62 стада · тонкий — запас 1 стад", font=font(15), fill=DIM)
    return im


def title_card(size, m, k):
    im = Image.new("RGB", size, BG)
    d = ImageDraw.Draw(im)
    W, H = size
    t1 = f"{k}. {m['title']}"
    d.text(((W - d.textlength(t1, font=font(56, True))) / 2, H / 2 - 70), t1, font=font(56, True), fill=INK)
    t2 = f"{m['duration']:.2f} с" + (" · цикл" if m["loop"] else "")
    d.text(((W - d.textlength(t2, font=font(30))) / 2, H / 2 + 6), t2, font=font(30), fill=ACC)
    t3 = m.get("note") or ""
    if t3:
        d.text(((W - d.textlength(t3, font=font(22))) / 2, H / 2 + 54), t3, font=font(22), fill=DIM)
    return im


def main():
    meta = json.load(open(os.path.join(SRC, "frames", "meta.json"), encoding="utf-8"))
    lab = os.path.join(SRC, "labeled")
    if os.path.isdir(lab):
        shutil.rmtree(lab)
    reel = os.path.join(lab, "reel")
    os.makedirs(reel)
    rn = 0
    for k, name in enumerate([c for c in ORDER if c in meta], 1):
        folder = os.path.join(SRC, "frames", name)
        if not os.path.isdir(folder):
            continue
        files = sorted(x for x in os.listdir(folder) if x.endswith(".png"))
        out = os.path.join(lab, name)
        os.makedirs(out)
        frames = []
        for f, fn in enumerate(files):
            im = label_frame(Image.open(os.path.join(folder, fn)).convert("RGB"), meta, name, f, len(files))
            path = os.path.join(out, f"{f:04d}.png")
            im.save(path)
            frames.append(path)
        card = title_card(Image.open(frames[0]).size, meta[name], k)
        for _ in range(int(0.9 * FPS)):
            card.save(os.path.join(reel, f"{rn:05d}.png"))
            rn += 1
        for _ in range(REPEAT.get(name, 1)):
            for path in frames:
                shutil.copyfile(path, os.path.join(reel, f"{rn:05d}.png"))
                rn += 1
        print("LABELED", name, len(files), flush=True)
    table(meta)
    rig_sheet()
    volley_videos()
    tail_sheet()
    timing_sheet()
    print("REEL", rn, flush=True)


def table(meta):
    rep = json.load(open(os.path.join(SRC, "anim_report.json"), encoding="utf-8"))["clips"]
    W = 2200
    rows = [c for c in ORDER if c in meta]
    H = 150 + 92 * len(rows) + 60
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((30, 20), "Король-дракон v7 — анимации: длительность, кадры, события, проверки", font=font(38, True), fill=INK)
    cols = [(30, "№"), (80, "Клип"), (390, "Длительность"), (560, "Кадров"), (680, "Состояние в игре"),
            (1110, "События (с)"), (1720, "Радиус, ст."), (1880, "Высота, ст.")]
    y = 92
    for x, t in cols:
        d.text((x, y), t, font=font(22, True), fill=ACC)
    y += 40
    for k, name in enumerate(rows, 1):
        m, r = meta[name], rep.get(name, {})
        d.rectangle((20, y - 6, W - 20, y + 80), fill=PANEL if k % 2 else BG)
        d.text((30, y), str(k), font=font(24, True), fill=INK)
        tsize = 24
        while d.textlength(m["title"], font=font(tsize, True)) > 295:
            tsize -= 1
        d.text((80, y), m["title"], font=font(tsize, True), fill=INK)
        d.text((80, y + 34), name, font=font(18), fill=DIM)
        d.text((390, y), f"{m['duration']:.2f} с" + (" цикл" if m["loop"] else ""), font=font(24), fill=INK)
        d.text((560, y), str(m["frames"]), font=font(24), fill=INK)
        d.text((680, y), GAME.get(name, ""), font=font(20), fill=INK)
        ev = "; ".join(f"{e} {t:.2f}" for e, t in sorted(m["events"].items(), key=lambda kv: kv[1]))
        line, yy = "", y
        for word in ev.split(" "):
            if d.textlength(line + " " + word, font=font(17)) > 580:
                d.text((1110, yy), line, font=font(17), fill=DIM)
                yy += 22
                line = word
            else:
                line = (line + " " + word).strip()
        d.text((1110, yy), line, font=font(17), fill=DIM)
        ok = r.get("arena_ok", True)
        d.text((1720, y), f"{r.get('radius_studs', 0):.1f}", font=font(24, True), fill=(140, 230, 140) if ok else (255, 120, 90))
        d.text((1880, y), f"{r.get('top_studs', 0):.1f}", font=font(24), fill=INK)
        y += 92
    d.text((30, y + 8), "Радиус — самая дальняя точка дракона и скипетра от центра босса; радиус арены 31 стад (диаметр 62), запас 1 стад → не больше 30. "
                        "Масштаб 2.795 (как v6/v7).", font=font(19), fill=DIM)
    im.save(os.path.join(DEST, "anim_table.png"))


def rig_sheet():
    folder = os.path.join(SRC, "rigdemo")
    if not os.path.isdir(folder):
        return
    info = json.load(open(os.path.join(folder, "rig_info.json"), encoding="utf-8"))

    def comp(name, view):
        model = Image.open(os.path.join(folder, f"{name}_{view}_model.png")).convert("RGB")
        skel = Image.open(os.path.join(folder, f"{name}_{view}_skel.png")).convert("RGBA")
        ghost = Image.blend(model, Image.new("RGB", model.size, (18, 20, 28)), 0.55)
        ghost.paste(skel, (0, 0), skel)
        return ghost

    T = (720, 480)
    W = 24 * 2 + 3 * T[0] + 2 * 12
    rows = [("stand", "wide", "Стойка"), ("stand", "sideL", "Стойка сбоку"), ("claw", "wide_r", "Замах лапой"),
            ("wings", "front", "Крылья вверх"), ("sleep", "wide", "Сон")]
    im = Image.new("RGB", (W, 140 + len(rows) * (T[1] + 16) + 700), BG)
    d = ImageDraw.Draw(im)
    d.text((30, 18), "Король-дракон v7 — риг: кости, привязка частей, контрольные позы", font=font(40, True), fill=INK)
    d.text((32, 72), f"{len(info['bones'])} кости. Каждая жёсткая деталь — на одной кости (в игре — Motor6D). Перепонки "
                     "крыльев — веса по углам (рука, пальцы, бок): в игре skinned mesh.", font=font(21), fill=DIM)
    y = 120
    for k, (name, view, title) in enumerate(rows):
        yy = y + k * (T[1] + 16)
        tiles = [Image.open(os.path.join(folder, f"{name}_{view}_seg.png")).convert("RGB").resize(T),
                 comp(name, view).resize(T),
                 Image.open(os.path.join(folder, f"{name}_{view}_model.png")).convert("RGB").resize(T)]
        for i, (tile, t) in enumerate(zip(tiles, ("части по костям", "скелет", "модель"))):
            x = 24 + i * (T[0] + 12)
            im.paste(tile, (x, yy))
            text = f"{title}: {t}"
            d.rectangle((x + 8, yy + 8, x + 24 + d.textlength(text, font=font(20, True)), yy + 40), fill=(14, 16, 24))
            d.text((x + 16, yy + 10), text, font=font(20, True), fill=INK)
    yy = y + len(rows) * (T[1] + 16) + 10
    d.text((30, yy), "Кости по цепям (родитель → дети)", font=font(28, True), fill=ACC)
    yy += 46
    chains = {}
    for b in info["bones"]:
        chains.setdefault(b["chain"], []).append(b["name"])
    order = ["Root", "Body", "Neck", "Head", "Jaw", "Collar", "Pauldron", "UpperArm", "Forearm", "Paw", "Thigh", "Shin",
             "Meta", "HindPaw", "WingArm", "WingFore", "Finger", "Tail", "Mantle", "Scepter"]
    col_w = (W - 60) // 2
    lines = []
    for c in order:
        if c in chains:
            parts = info["parts"]
            n = sum(parts.get(b, 0) for b in chains[c])
            lines.append(f"{c}: {', '.join(chains[c])}" + (f" — деталей {n}" if n else ""))
    lines.append(f"Перепонки: Membrane.L/R — {info['membrane']['L']['verts']} вершин на крыло, веса на WingArm, "
                 "WingFore, Finger1–4 и Body (бок).")
    half = (len(lines) + 1) // 2
    for i, line in enumerate(lines):
        x = 30 + (i // half) * col_w
        ly = yy + (i % half) * 30
        d.text((x, ly), line[:96] + ("…" if len(line) > 96 else ""), font=font(19), fill=INK)
    end = yy + half * 30 + 30
    im.crop((0, 0, W, end)).save(os.path.join(DEST, "rig_demo.png"))


# ── залп: подписи и мини-карта ─────────────────────────────────────────────────────────────────────────────
# стороны — для игрока, стоящего лицом к дракону: снаряд −1 летит в +x (правая рука игрока), +1 — в −x
SIDE_RU = {-1: "правый", 0: "центральный", 1: "левый"}
PLAYER_SPEED = 14  # Progression.Speed min, ст/с — скорость тестовой цели


def phase(t, prm, canceled):
    if canceled:
        return "БОЙ ОКОНЧЕН — атака отменена", (255, 120, 90)
    if t < 0.3:
        return "величественная поза, голова вверх", INK
    if t < prm["track_from"]:
        return "скипетр поднимается, кристалл разгорается", INK
    if t < prm["lock"]:
        return "подготовка: полосы следят за игроком", (255, 205, 90)
    if t < prm["fire"]:
        return "НАПРАВЛЕНИЕ ЗАФИКСИРОВАНО — уходите в сторону", (90, 235, 225)
    if t < 2.9:
        return "выстрел: три снаряда летят по прямым", (90, 235, 225)
    return "скипетр на месте", INK


def minimap(d, box, data, k):
    """Вид сверху в стадах: дракон сверху, игрок снизу (смотрит вверх, его левая рука — слева).
    Полосы, капсула игрока и его след, снаряды, колонна — всё из расчёта volley_sim, не из картинки."""
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(14, 16, 24, 230), outline=(90, 94, 110))
    L = data["launch"]
    prm = data["params"]
    fr = data["track"][min(k, len(data["track"]) - 1)]
    span_x, span_y = 30.0, 26.0
    sc = min((x1 - x0 - 16) / span_x, (y1 - y0 - 40) / span_y)
    cx = (x0 + x1) / 2

    def P(px, py):
        return cx + (px - L[0]) * sc, y0 + 34 + (L[1] - py) * sc

    d.text((x0 + 8, y0 + 4), "вид сверху · расчёт сервера", font=font(15, True), fill=DIM)
    for gy in range(0, 26, 5):
        yy = P(L[0], L[1] - gy)[1]
        d.line((x0 + 4, yy, x0 + 12, yy), fill=(90, 94, 110))
        d.text((x0 + 14, yy - 9), f"{gy}", font=font(12), fill=(120, 124, 140))
    if fr["t"] >= prm["track_from"] and not fr["canceled"]:
        col = (90, 235, 225, 110) if fr["locked"] else (255, 200, 80, 70)
        for side, ((ax, ay), (bx, by), w) in VS.lanes(L, fr["aim"], prm).items():
            vx, vy = bx - ax, by - ay
            n = (vx * vx + vy * vy) ** 0.5 or 1
            nx, ny = -vy / n * w / 2, vx / n * w / 2
            d.polygon([P(ax + nx, ay + ny), P(bx + nx, by + ny), P(bx - nx, by - ny), P(ax - nx, ay - ny)], fill=col)
    for (ox, oy, r) in data["obstacles"]:
        a, b = P(ox - r, oy + r), P(ox + r, oy - r)
        d.ellipse((a[0], a[1], b[0], b[1]), fill=(150, 146, 160), outline=(40, 40, 50))
    path = [P(f["feet"][0], f["feet"][1]) for f in data["track"][: k + 1]]
    if len(path) > 1:
        d.line(path, fill=(235, 238, 245, 160), width=2)
    feet = fr["feet"]
    pr = prm["player_radius"] * sc
    fx, fy = P(feet[0], feet[1])
    hit = any(h[0] <= fr["t"] + 1e-6 for h in data["hits"])
    d.ellipse((fx - pr, fy - pr, fx + pr, fy + pr), fill=(255, 90, 80) if hit else (235, 238, 245), outline=(20, 20, 30))
    rr = prm["radius"] * sc
    for side, pos, alive, end_t, why in fr["proj"]:
        px, py = P(pos[0], pos[1])
        if alive:
            d.ellipse((px - rr, py - rr, px + rr, py + rr), fill=(60, 240, 225), outline=(255, 210, 80), width=2)
        elif why in ("земля", "препятствие", "попал в игрока"):
            c = (255, 90, 80) if why == "попал в игрока" else (60, 240, 225)
            d.line((px - rr, py - rr, px + rr, py + rr), fill=c, width=3)
            d.line((px - rr, py + rr, px + rr, py - rr), fill=c, width=3)
    lx, ly = P(L[0], L[1])
    d.ellipse((lx - 6, ly - 6, lx + 6, ly + 6), fill=(255, 210, 80))
    d.text((lx + 10, ly - 10), "круг", font=font(13), fill=(255, 210, 80))
    d.text((x0 + 8, y1 - 34), "белый — игрок r 1.25 ст.", font=font(13), fill=DIM)
    d.text((x0 + 8, y1 - 18), "полоса = ширина снаряда", font=font(13), fill=DIM)


def verdict(data):
    if data["canceled"]:
        return f"АТАКА ОТМЕНЕНА ({data['canceled']}): урона нет, снаряды и круг удалены", (255, 150, 110)
    if data["hits"]:
        hs = ", ".join(f"{SIDE_RU[h[1]]} в {h[0]:.2f} с" for h in data["hits"])
        return f"ПОПАДАНИЕ: {hs} — урон засчитан 1 раз", (255, 120, 90)
    return "ПРОМАХ: урона нет", (140, 230, 140)


def label_volley(im, name, data, k):
    d = ImageDraw.Draw(im, "RGBA")
    W, H = im.size
    prm = data["params"]
    fr = data["track"][min(k, len(data["track"]) - 1)]
    t = fr["t"]
    d.rectangle((0, 0, W, 70), fill=(14, 16, 24, 210))
    title = "Королевский магический залп" if name == "cinematic" else f"Сценарий {name[0]}: {data['text']}"
    d.text((18, 6), title, font=font(26, True), fill=INK)
    ph, pc = phase(t, prm, fr["canceled"])
    d.text((20, 40), ph, font=font(20, True), fill=pc)
    tw = d.textlength(f"{t:4.2f} с", font=font(26, True))
    d.text((W - tw - 20, 14), f"{t:4.2f} с", font=font(26, True), fill=ACC)
    minimap(d, (W - 290, 80, W - 12, 420), data, k)
    y = H - 86
    d.rectangle((0, y, W, H), fill=(14, 16, 24, 215))
    d.text((20, y + 6), f"цель в {data['distance']:.0f} ст. от круга, бежит {PLAYER_SPEED} ст/с · снаряд {prm['speed']:.0f} ст/с, "
                       f"радиус {prm['radius']} ст., разлёт ±{prm['spread']:.0f}° · капсула игрока r {prm['player_radius']} ст.",
           font=font(18), fill=DIM)
    done = t >= (data["end_at"] if data["canceled"] else min([h[0] for h in data["hits"]] + [prm["fire"] + 1.1]))
    if done:
        v, c = verdict(data)
        d.text((20, y + 30), v, font=font(21, True), fill=c)
        if data["closest"]:
            gaps = " · ".join(f"{SIDE_RU[int(a)]} {b:+.2f}" for a, b in sorted(data["closest"].items(), key=lambda kv: int(kv[0])))
            d.text((20, y + 58), f"наименьший зазор снаряд–капсула, ст. (≤ 0 — касание): {gaps}", font=font(17), fill=INK)
    return im


def volley_videos():
    """Подписанные кадры залпа: кинематографичный ролик и семь сценариев уклонения (+ общий ролик уклонения)."""
    lab = os.path.join(SRC, "labeled")
    data = {}
    for fn in sorted(os.listdir(SRC)):
        if fn.startswith("volley_") and fn.endswith(".json"):
            data.update(json.load(open(os.path.join(SRC, fn), encoding="utf-8")))
    if not data:
        return
    reel = os.path.join(lab, "volley_dodge_reel")
    shutil.rmtree(reel, ignore_errors=True)
    os.makedirs(reel)
    rn = 0
    for name in sorted(data):
        src = os.path.join(SRC, "frames", "volley_" + name)
        if not os.path.isdir(src):
            continue
        out = os.path.join(lab, "volley_" + name)
        shutil.rmtree(out, ignore_errors=True)
        os.makedirs(out)
        files = sorted(x for x in os.listdir(src) if x.endswith(".png"))
        frames = []
        for f, fn in enumerate(files):
            im = label_volley(Image.open(os.path.join(src, fn)).convert("RGB"), name, data[name], f)
            path = os.path.join(out, f"{f:04d}.png")
            im.save(path)
            frames.append(path)
        if name != "cinematic" and frames:
            card = Image.new("RGB", Image.open(frames[0]).size, BG)
            cd = ImageDraw.Draw(card)
            W, H = card.size
            t1 = f"Сценарий {name[0]}"
            cd.text(((W - cd.textlength(t1, font=font(52, True))) / 2, H / 2 - 70), t1, font=font(52, True), fill=INK)
            t2 = data[name]["text"]
            cd.text(((W - cd.textlength(t2, font=font(28))) / 2, H / 2 + 4), t2, font=font(28), fill=ACC)
            v, c = verdict(data[name])
            cd.text(((W - cd.textlength("ожидаем: " + v, font=font(22))) / 2, H / 2 + 52), "итог: " + v, font=font(22), fill=c)
            for _ in range(int(1.4 * FPS)):
                card.save(os.path.join(reel, f"{rn:05d}.png"))
                rn += 1
            for path in frames:
                shutil.copyfile(path, os.path.join(reel, f"{rn:05d}.png"))
                rn += 1
            for _ in range(int(0.8 * FPS)):
                shutil.copyfile(frames[-1], os.path.join(reel, f"{rn:05d}.png"))
                rn += 1
        print("VOLLEY_LABELED", name, len(files), flush=True)
    slim = {k: {kk: v for kk, v in d.items() if kk != "track"} for k, d in data.items()}
    slim["_reaction_table"] = VS.reaction_table()
    json.dump(slim, open(os.path.join(DEST, "volley_scenarios.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def wrap(d, text, x, y, width, fnt, fill, step):
    line = ""
    for word in text.split():
        if d.textlength((line + " " + word).strip(), font=fnt) > width:
            d.text((x, y), line, font=fnt, fill=fill)
            y += step
            line = word
        else:
            line = (line + " " + word).strip()
    d.text((x, y), line, font=fnt, fill=fill)
    return y + step


def tail_sheet():
    fn = os.path.join(SRC, "tail_compare.json")
    if not os.path.exists(fn):
        return
    res = json.load(open(fn, encoding="utf-8"))
    T = (720, 480)
    W = 24 * 2 + 2 * T[0] + 12
    im = Image.new("RGB", (W, 1500), BG)
    d = ImageDraw.Draw(im, "RGBA")
    d.text((24, 16), "Удар хвостом: почему выбран левый бок — кадр контакта 0.80 с, одна и та же камера",
           font=font(30, True), fill=INK)
    rows = (("tail_strike", "Влево (в клипе tail_strike)"), ("tail_strike_right", "Вправо (прежний вариант, для сравнения)"))
    y = 70
    for name, title in rows:
        r = res.get(name)
        if not r:
            continue
        pics = sorted(x for x in os.listdir(SRC) if x.startswith(f"tailcmp_{name}_") and x.endswith(".png")
                      and (name == "tail_strike_right" or not x.startswith("tailcmp_tail_strike_right")))[:2]
        for j, pfn in enumerate(pics):
            im.paste(Image.open(os.path.join(SRC, pfn)).convert("RGB").resize(T), (24 + j * (T[0] + 12), y))
        d.rectangle((24, y + T[1] - 46, W - 24, y + T[1]), fill=(14, 16, 24, 220))
        ok = r.get("arena_ok", r.get("radius", 99) <= 30)
        tip = r.get("tip") or r.get("tip_0.8") or []
        tip_s = "(" + ", ".join(f"{v:.1f}" for v in tip[:3]) + ")" if tip else ""
        d.text((36, y + T[1] - 40), f"{title}: кончик хвоста {tip_s} ст., радиус клипа {r.get('radius', 0):.1f} ст. — "
                                   f"{'внутри арены' if ok else 'ЗА КРАЕМ АРЕНЫ (31)'}", font=font(20, True),
               fill=(140, 230, 140) if ok else (255, 120, 90))
        y += T[1] + 20
    txt = ("Хвост v6/v7 в покое загнут влево. Удар влево продолжает этот изгиб: хвост хлещет вдоль левого бока, "
           "кончик остаётся в пределах арены. Удар вправо сначала разгибает хвост, и в момент контакта он уходит прямо "
           "назад — за край арены и через обе задние лапы, до бока не доходит. Поэтому в клипе — левый вариант. "
           "Сторону не меняю без вашего решения: если нужен правый удар, придётся перестроить изгиб хвоста в позах "
           "(внешность хвоста при этом не меняется).")
    end = wrap(d, txt, 24, y + 4, W - 48, font(21), DIM, 30)
    im.crop((0, 0, W, end + 20)).save(os.path.join(DEST, "tail_side_compare.png"))


def timing_sheet():
    """Шкала времени залпа и время на реакцию (из volley_sim)."""
    prm = VS.PARAMS
    W = 1800
    im = Image.new("RGB", (W, 900), BG)
    d = ImageDraw.Draw(im)
    d.text((30, 18), "Королевский магический залп — тайминг и время на реакцию (предложение, баланс не изменён)",
           font=font(32, True), fill=INK)
    x0, x1, y = 60, W - 60, 130
    sx = (x1 - x0) / 3.0
    spans = [(0.0, 0.3, "поза", (120, 110, 160)), (0.3, prm["track_from"], "призыв скипетра", (150, 120, 190)),
             (prm["track_from"], prm["lock"], "слежение за игроком", (210, 160, 50)),
             (prm["lock"], prm["fire"], "зафиксировано", (50, 190, 180)),
             (prm["fire"], 2.9, "полёт · скипетр возвращается", (70, 140, 210)), (2.9, 3.0, "", (110, 110, 130))]
    for i, (a, b, text, c) in enumerate(spans):
        d.rectangle((x0 + a * sx, y, x0 + b * sx - 2, y + 56), fill=c)
        if text:
            d.text((x0 + a * sx + 8, y + 62 + (i % 2) * 24), text, font=font(18), fill=INK)
    for i in range(7):
        t = i * 0.5
        d.line((x0 + t * sx, y - 8, x0 + t * sx, y), fill=DIM)
        d.text((x0 + t * sx - 12, y - 32), f"{t:.1f}", font=font(16), fill=DIM)
    for t, name in ((prm["track_from"], "полосы появились 0.60"), (prm["lock"], "фиксация 1.45"), (prm["fire"], "выстрел 1.95")):
        d.line((x0 + t * sx, y - 6, x0 + t * sx, y + 130), fill=(255, 90, 80), width=3)
        d.text((x0 + t * sx + 6, y + 112), name, font=font(18, True), fill=(255, 130, 100))
    yy = 300
    d.text((60, yy), "Время у игрока после фиксации (центральный снаряд; расчёт volley_sim, шаг сервера 1/60 с)",
           font=font(24, True), fill=ACC)
    yy += 44
    heads = ["до цели, ст.", "игрок, ст/с", "фиксация → прилёт, с", "щель между полосами, ст.", "нужно сместиться, ст.",
             "успеть начать до, с"]
    xs = [60, 250, 420, 700, 1010, 1300]
    for x, h in zip(xs, heads):
        d.text((x, yy), h, font=font(19, True), fill=INK)
    yy += 34
    for r in VS.reaction_table(distances=(12.0, 16.0, 20.0, 30.0)):
        vals = [f"{r['distance']:.0f}", f"{r['speed']:.0f}", f"{r['time_after_lock']:.2f}", f"{r['pocket_width']:.2f}",
                f"{r['move_needed']:.2f}", f"{r['latest_reaction']:.2f}"]
        bad = r["latest_reaction"] < 0.45
        for x, v in zip(xs, vals):
            d.text((x, yy), v, font=font(19), fill=(255, 150, 110) if bad else INK)
        yy += 30
    yy = wrap(d, "«Успеть начать до» — сколько секунд после фиксации можно ждать и всё ещё уйти. Красным — меньше 0.45 с "
                 "(реакция человека ~0.25 с + задержка сети ~0.1–0.2 с): на таком расстоянии залп не применять. Щель < 0.8 ст. "
                 "— между полосами не встать, уходить только за боковую полосу.", 60, yy + 12, W - 120, font(18), DIM, 26)
    im.crop((0, 0, W, yy + 20)).save(os.path.join(DEST, "volley_timing.png"))


if __name__ == "__main__":
    main()
