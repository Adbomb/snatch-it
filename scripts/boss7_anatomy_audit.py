"""Лист «аудит анатомии» босса 7 «Копилка-громила» по правилам D64 — владельцу до запекания карт (шаг 2, D73).

Существа (30): кадры спереди, сбоку, 3/4 и лицо (быстрая сборка scripts/blender/art_bank.py quick), признаки вида из
каталога (scripts/blender/boss7/catalog.py) с отметкой «есть / слабо / нет», эмоция, числа отчёта сборки
(треугольники без подставки, габарит, суставы joint_check), замечания и оценка «ок» / «мелкие правки» / «переделать».
Находки — assets/concepts/bosses_5_10/boss7_prod/audit.json (по кадрам):
  {"<Id>": {"signs": ["+" | "±" | "-", …] (по порядку признаков каталога), "emotion": "что видно",
            "problems": ["…"], "fixes": ["…"], "rating": "…"}, …}
Копилка: игровые позы (scripts/blender/boss7_piggy.py), раскадровка 10 клипов (boss7_piggy_anim.py), числа отчётов.

Выход (вне git): assets/concepts/bosses_5_10/boss7_prod/5_audit_{overview,common,rare,epic,legendary}.png и
6_boss_game.png; в git — docs/BOSS7_ANATOMY_AUDIT.md.
Запуск из корня: python scripts/boss7_anatomy_audit.py
Зависит от Pillow, scripts/blender/boss7/sheet.py (оформление, цвета редкостей из UITokens — D71) и catalog.py.
"""

import json
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "blender", "boss7"))
import catalog as CAT  # noqa: E402
import sheet as SH  # noqa: E402

V = SH.V
PROD = os.path.join(ROOT, "assets", "concepts", "bosses_5_10", "boss7_prod")
SHOTS = os.path.join(PROD, "creatures")
AUDIT = os.path.join(PROD, "audit.json")
DOC = os.path.join(ROOT, "docs", "BOSS7_ANATOMY_AUDIT.md")
RATING = {"ок": (46, 160, 67), "мелкие правки": (230, 150, 20), "переделать": (210, 50, 50)}
MARK = {"+": ("есть", (70, 190, 90)), "±": ("слабо", (235, 160, 30)), "-": ("нет", (230, 70, 70))}
LIMIT = 3000


def items():
    out = []
    for n, (star, rar, wow, name, iid, fam, hold, img, signs, mood, cols) in enumerate(CAT.ROWS, 1):
        out.append({"n": n, "rarity": rar, "wow": wow, "name": name, "id": iid, "family": fam, "img": img,
                    "signs": [x.strip() for x in signs.split(",")], "emotion": mood})
    return out


def report(item_id):
    best, when = {}, -1.0
    for name in os.listdir(SHOTS):
        if not (name.startswith("report") and name.endswith(".json")):
            continue
        p = os.path.join(SHOTS, name)
        rep = json.load(open(p, encoding="utf-8")).get(item_id)
        if rep and os.path.getmtime(p) > when:
            best, when = rep, os.path.getmtime(p)
    return best


def frame(item_id, view):
    p = os.path.join(SHOTS, f"{item_id}_{view}.png")
    return Image.open(p).convert("RGB") if os.path.exists(p) else None


def numbers(rep):
    tris = rep.get("tris_without_stand")
    size = rep.get("size_blender_xyz")
    joints = rep.get("joint_issues") or []
    bad, lines = [], []
    if tris is not None:
        lines.append(f"треугольников без подставки: {tris} (≤ {LIMIT})")
        if tris > LIMIT:
            bad.append("треугольники")
    if size:
        lines.append("габарит с подставкой: " + " × ".join(f"{v:.2f}" for v in size))
    lines.append("суставы: " + ("без щелей" if not joints else
                                f"{len(joints)} замечаний ({', '.join(sorted({j['kind'] for j in joints}))})"))
    if joints:
        bad.append("суставы")
    return lines, bad


def row(sheet, d, y, it, a, col):
    pic, gap = 300, 10
    x = SH.M
    for view, cap in (("front", "спереди"), ("side", "сбоку"), ("hero", "3/4"), ("face", "лицо")):
        im = frame(it["id"], view)
        if im is not None:
            sheet.paste(V.fit(im, pic, pic), (x, y))
        else:
            d.rectangle((x, y, x + pic, y + pic), fill=(60, 30, 30))
        V.label(d, x + 8, y + pic - 40, cap)
        x += pic + gap
    tx = x + 14
    tw = SH.W - SH.M - tx
    rating = a.get("rating", "—")
    rc = RATING.get(rating, (120, 120, 132))
    d.rectangle((tx - 14, y, tx - 6, y + pic), fill=col)
    ty = V.para(d, tx, y + 4, f"№{it['n']} {it['name']}", tw - 260, size=30, fill=SH.INK, bold=True)
    f = V.font(24, True)
    rw = d.textlength(rating, font=f)
    d.rectangle((SH.W - SH.M - rw - 30, y + 4, SH.W - SH.M, y + 46), fill=rc)
    d.text((SH.W - SH.M - rw - 15, y + 9), rating, font=f, fill=(255, 255, 255))
    ty = V.para(d, tx, ty + 2, f"{it['id']} · {SH.RARITY_RU[it['rarity']]} · «вау» {it['wow']} · семья {it['family']}",
                tw, size=18, fill=col) + 4
    ty = V.para(d, tx, ty, it["img"][0].upper() + it["img"][1:] + ".", tw, size=18, fill=SH.INK) + 4
    marks = a.get("signs") or []
    for i, text in enumerate(it["signs"]):
        word, mc = MARK.get(marks[i] if i < len(marks) else "", ("?", (150, 150, 150)))
        d.rectangle((tx, ty + 4, tx + 70, ty + 28), fill=mc)
        d.text((tx + 6, ty + 3), word, font=V.font(17, True), fill=(255, 255, 255))
        ty = max(V.para(d, tx + 80, ty + 2, text, tw - 90, size=18, fill=SH.INK), ty + 28) + 2
    seen = a.get("emotion")
    ty = V.para(d, tx, ty + 4, "Эмоция (каталог): " + it["emotion"] + (". На лице: " + seen if seen else ""), tw,
                size=18, fill=SH.DIM) + 4
    lines, bad = numbers(report(it["id"]))
    ty = V.para(d, tx, ty, " · ".join(lines), tw, size=17, fill=(235, 120, 120) if bad else SH.DIM) + 4
    for p in a.get("problems") or []:
        ty = V.para(d, tx, ty, "— " + p, tw, size=18, fill=(250, 200, 120)) + 2
    for p in a.get("fixes") or []:
        ty = V.para(d, tx, ty, "→ " + p, tw, size=18, fill=(150, 220, 160)) + 2
    return max(pic, ty - y) + 14


def page(its, audit, rar):
    group = [it for it in its if it["rarity"] == rar]
    col = SH.RARITY[rar]
    sheet = Image.new("RGB", (SH.W, 560 * len(group) + 400), SH.BG)
    d = ImageDraw.Draw(sheet)
    ok = sum(1 for it in group if audit.get(it["id"], {}).get("rating") == "ок")
    SH.header(d, f"Аудит анатомии D64 — {SH.RARITY_RU[rar]} ({len(group)}) · босс 7 «Банк»",
              f"Быстрая сборка без карт. «ок» — {ok} из {len(group)}. Признаки вида — из каталога docs/BOSS7_CATALOG.md;"
              " числа — из отчёта сборки.")
    y = 130
    for it in group:
        y += row(sheet, d, y, it, audit.get(it["id"], {}), col)
    sheet = sheet.crop((0, 0, SH.W, y + SH.M))
    out = os.path.join(PROD, f"5_audit_{rar.lower()}.png")
    sheet.save(out)
    return out


def overview(its, audit):
    cols, cell = 6, 380
    rows = (len(its) + cols - 1) // cols
    sheet = Image.new("RGB", (SH.W, 130 + rows * (cell + 70) + 160), SH.BG)
    d = ImageDraw.Draw(sheet)
    counts = {k: sum(1 for it in its if audit.get(it["id"], {}).get("rating") == k) for k in RATING}
    SH.header(d, "Аудит анатомии 30 существ «Банка» — до запекания карт",
              "Оценки: " + ", ".join(f"{k} — {v}" for k, v in counts.items()) + ". Подробно — листы по редкостям.")
    gap = (SH.W - 2 * SH.M - cols * cell) // (cols - 1)
    for i, it in enumerate(its):
        x = SH.M + (i % cols) * (cell + gap)
        y = 130 + (i // cols) * (cell + 70)
        im = frame(it["id"], "hero")
        if im is not None:
            w, h = im.size
            sheet.paste(V.fit(im.crop((int(w * 0.15), int(h * 0.12), int(w * 0.85), int(h * 0.82))), cell, cell), (x, y))
        rating = audit.get(it["id"], {}).get("rating", "—")
        d.rectangle((x, y + cell, x + cell, y + cell + 8), fill=RATING.get(rating, (120, 120, 132)))
        d.rectangle((x, y, x + 10, y + cell), fill=SH.RARITY[it["rarity"]])
        V.para(d, x + 4, y + cell + 12, f"№{it['n']} {it['name']} — {rating}", cell, size=21, fill=SH.INK, bold=True)
    y = 130 + rows * (cell + 70) + 10
    lx = SH.M
    for k, c in RATING.items():
        d.rectangle((lx, y + 8, lx + 40, y + 28), fill=c)
        d.text((lx + 50, y), k, font=V.font(24), fill=SH.INK)
        lx += 300
    for rar in ("Common", "Rare", "Epic", "Legendary"):
        d.rectangle((lx, y + 4, lx + 12, y + 32), fill=SH.RARITY[rar])
        d.text((lx + 20, y), SH.RARITY_RU[rar], font=V.font(24), fill=SH.INK)
        lx += 230
    out = os.path.join(PROD, "5_audit_overview.png")
    sheet.save(out)
    return out


def boss_page():
    """Копилка: игровые позы, раскадровка 10 клипов, числа."""
    bdir, adir = os.path.join(PROD, "boss"), os.path.join(PROD, "anim")
    rep = json.load(open(os.path.join(bdir, "report.json"), encoding="utf-8"))
    arep = json.load(open(os.path.join(adir, "anim_report.json"), encoding="utf-8"))
    sheet = Image.new("RGB", (SH.W, 7000), SH.BG)
    d = ImageDraw.Draw(sheet)
    SH.header(d, "Копилка-громила — игровая модель и 10 клипов (до карт)",
              f"Части на Motor6D: {rep['parts']}, треугольников {rep['tris_total']} (≤ 8 000). Глаза крупнее концепта "
              f"на 26 % (радиус {rep['eye_radius']}), с белком — правка владельца.")
    y = 128
    size = (SH.W - 2 * SH.M - 3 * 12) // 4
    shots = [("game_stand_front.png", "Стойка — спереди"), ("game_stand_34.png", "Стойка — 3/4"),
             ("game_face.png", "Лицо: глаза с белком"), ("game_far.png", "Издалека (60 стадов)"),
             ("game_sleep_34.png", "Сон"), ("game_ram_34.png", "«Таран пятачком»"),
             ("game_hail_34.png", "«Монетный град»"), ("game_defeat_34.png", "Поражение")]
    for i, (name, cap) in enumerate(shots):
        x = SH.M + (i % 4) * (size + 12)
        yy = y + (i // 4) * (size + 12)
        sheet.paste(V.fit(Image.open(os.path.join(bdir, name)).convert("RGB"), size, size), (x, yy))
        V.label(d, x + 12, yy + size - 44, cap)
    y += 2 * (size + 12) + 8
    y = SH.section(d, y, "10 клипов", "8 кадров на клип, вид 3/4; каждый кадр стоит на земле")
    titles = {"sleep_idle": "Сон", "wake": "Пробуждение", "combat_idle": "Боевая стойка", "walk": "Ходьба",
              "ram": "Таран пятачком", "coin_hail": "Монетный град", "hit": "Получение урона", "victory": "Победа",
              "defeat": "Поражение", "fall_asleep": "Засыпание"}
    fw = (SH.W - 2 * SH.M - 260 - 7 * 6) // 8
    fh = round(fw * 460 / 420)
    for clip, title in titles.items():
        d.text((SH.M, y + fh // 2 - 30), title, font=V.font(24, True), fill=SH.ACC)
        d.text((SH.M, y + fh // 2 + 4), f"{arep[clip]['frames']} кадров", font=V.font(18), fill=SH.DIM)
        for k in range(8):
            im = Image.open(os.path.join(adir, "frames", f"{clip}_{k}.png")).convert("RGB")
            sheet.paste(V.fit(im, fw, fh), (SH.M + 260 + k * (fw + 6), y))
        y += fh + 8
    y += 8
    tb = rep["tris_by_part"]
    lines = ["• Треугольники по частям: " + ", ".join(f"{k} {v}" for k, v in sorted(tb.items(), key=lambda kv: -kv[1])
                                                     if v) + ".",
             "• Суставы в покое: " + ("без щелей и с точками вращения у суставов (joint_check)." if not
                                      rep["joint_issues_rest"] else f"{len(rep['joint_issues_rest'])} замечаний."),
             "• Позы сажаются на землю автоматически: " + ", ".join(
                 f"{k} — ниже всех {v['lowest'][0]}" for k, v in rep["poses"].items()) + ".",
             "• Выражения и эффекты — сдвигом частей: веки, крестики и язык в покое спрятаны в голове, трещины — в "
             "теле, горка монет — под землёй, монеты — в теле под щелью. Без частиц и смены мешей.",
             "• Анимация — Boss7_Piggy.anim.json (формат Йети). В assets и в игру — после «ок» листа и карт."]
    d.rectangle((SH.M, y, SH.W - SH.M, y + 330), fill=SH.PANEL)
    yy = y + 14
    for ln in lines:
        yy = V.para(d, SH.M + 18, yy, ln, SH.W - 2 * SH.M - 36, size=21, fill=SH.INK) + 8
    y = max(yy, y + 330) + SH.M
    sheet = sheet.crop((0, 0, SH.W, y))
    out = os.path.join(PROD, "6_boss_game.png")
    sheet.save(out)
    return out


def doc(its, audit):
    lines = ["# Босс 7: аудит анатомии 30 существ «Банка» и игровой копилки (D64, D73)", "",
             "Создан скриптом `scripts/boss7_anatomy_audit.py` по кадрам быстрой сборки (`art_bank.py quick`) — "
             "до запекания карт. Листы (вне git): `assets/concepts/bosses_5_10/boss7_prod/5_audit_*.png`, "
             "`6_boss_game.png`.", "",
             "| № | Существо | Редкость | Оценка | Признаки (есть / слабо / нет) | Треуг. | Суставы | Замечания |",
             "|---|---|---|---|---|---|---|---|"]
    for it in its:
        a = audit.get(it["id"], {})
        marks = a.get("signs") or []
        cnt = "/".join(str(sum(1 for m in marks if m == k)) for k in ("+", "±", "-"))
        rep = report(it["id"])
        probs = "; ".join(a.get("problems") or []) or "—"
        lines.append(f"| {it['n']} | {it['name']} | {it['rarity']} | {a.get('rating', '—')} | {cnt} | "
                     f"{rep.get('tris_without_stand', '—')} | {len(rep.get('joint_issues') or [])} | {probs} |")
    open(DOC, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    return DOC


def main():
    its = items()
    audit = json.load(open(AUDIT, encoding="utf-8")) if os.path.exists(AUDIT) else {}
    outs = [overview(its, audit)] + [page(its, audit, r) for r in ("Common", "Rare", "Epic", "Legendary")]
    outs += [boss_page(), doc(its, audit)]
    return outs


if __name__ == "__main__":
    for o in main():
        print(o)
