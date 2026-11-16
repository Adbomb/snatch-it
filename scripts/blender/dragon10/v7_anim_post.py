"""Подписи кадров превью Короля-дракона v7, общий ролик, таблица длительностей и лист демонстрации рига (PIL).

  python scripts/blender/dragon10/v7_anim_post.py <папка кадров> <папка результата>
Читает <кадры>/frames/<клип>/*.png, frames/meta.json, anim_report.json, rigdemo/*.png и rig_info.json.
Пишет:
- <кадры>/labeled/<клип>/ — кадры с подписями;
- <кадры>/labeled/reel/ — все клипы подряд с титрами;
- <результат>/anim_table.png и <результат>/rig_demo.png.
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
         "magic_scepter", "hit", "victory", "defeat", "fall_asleep"]
REPEAT = {"walk": 3}
GAME = {"sleep_idle": "Sleep (цикл)", "wake": "Wake 1.0 + StandUp 0.9 + ToCombat 0.5", "combat_idle": "Combat (цикл)",
        "walk": "Combat/Return: бег 10 ст/с", "turn_left": "поворот модели (нет в бою)",
        "claw_swipe": "выпад: AttackAt + HitDelay 0.25", "bite": "выпад: AttackAt + HitDelay 0.25",
        "tail_strike": "выпад: AttackAt + HitDelay 0.25", "wing_buffet": "выпад: AttackAt + HitDelay 0.25",
        "magic_scepter": "нового выпада в игре нет", "hit": "реакция на удар", "victory": "Victory 2.2",
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
        d.text((80, y), m["title"], font=font(24, True), fill=INK)
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


if __name__ == "__main__":
    main()
