"""Лист «аудит анатомии» 30 существ джунглей босса 6 по правилам D64 — владельцу до запекания карт (шаг 2).

На каждое существо: кадры спереди, сбоку, 3/4 и лицо (быстрая сборка scripts/blender/art_jungle.py quick), признаки
вида из каталога с отметкой «есть / слабо / нет», эмоция лица, числа из отчёта сборки (треугольники без подставки,
габарит, суставы joint_check, скрытые грани), замечания и оценка «ок» / «мелкие правки» / «переделать».
Находки — assets/concepts/bosses_5_10/boss6_prod/audit.json (пишут проверяющие по кадрам):
  {"<Id>": {"signs": [["признак", "+" | "±" | "-"], …], "emotion": "что видно", "problems": ["…"],
            "fixes": ["…"], "rating": "ок" | "мелкие правки" | "переделать"}, …}
Числа — из отчётов report_<Id>.json конвейера. Каталог — docs/BOSS6_CATALOG.md (через blender/boss6/catalog_sheet.rows).

Выход (вне git): assets/concepts/bosses_5_10/boss6_prod/5_audit_{overview,common,rare,epic,legendary}.png;
в git — docs/BOSS6_ANATOMY_AUDIT.md (таблица оценок и замечаний).
Запуск из корня: python scripts/boss6_anatomy_audit.py
Зависит от Pillow, scripts/blender/boss6/sheet.py (оформление, цвета редкостей из UITokens — D71).
"""

import json
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "blender", "boss6"))
import sheet as SH  # noqa: E402
import catalog_sheet as CS  # noqa: E402

V = SH.V
PROD = os.path.join(ROOT, "assets", "concepts", "bosses_5_10", "boss6_prod")
SHOTS = os.path.join(PROD, "creatures")
AUDIT = os.path.join(PROD, "audit.json")
DOC = os.path.join(ROOT, "docs", "BOSS6_ANATOMY_AUDIT.md")
RATING = {"ок": (46, 160, 67), "мелкие правки": (230, 150, 20), "переделать": (210, 50, 50)}
MARK = {"+": ("есть", (70, 190, 90)), "±": ("слабо", (235, 160, 30)), "-": ("нет", (230, 70, 70))}
LIMITS = {"tris": 3000, "size": (3.7, 3.7, 4.55)}  # D64 и каталог: без подставки


def report(item_id):
    """Отчёт сборки существа: самый свежий из общего report.json (сборка всех) и report_<Id>.json (точечная)."""
    best, when = {}, -1.0
    for name in ("report.json", f"report_{item_id}.json"):
        p = os.path.join(SHOTS, name)
        if os.path.exists(p) and os.path.getmtime(p) > when:
            rep = json.load(open(p, encoding="utf-8")).get(item_id)
            if rep:
                best, when = rep, os.path.getmtime(p)
    return best


def frame(item_id, view):
    p = os.path.join(SHOTS, f"{item_id}_{view}.png")
    return Image.open(p).convert("RGB") if os.path.exists(p) else None


def numbers(rep):
    """Строки чисел отчёта и признак нарушения правил."""
    tris = rep.get("tris_without_stand")
    size = rep.get("size_no_stand") or rep.get("size_blender_xyz")
    joints = rep.get("joint_issues") or []
    bad = []
    lines = []
    if tris is not None:
        lines.append(f"треугольников без подставки: {tris} (≤ {LIMITS['tris']})")
        if tris > LIMITS["tris"]:
            bad.append("треугольники")
    if size:
        lines.append("габарит: " + " × ".join(f"{v:.2f}" for v in size))
    lines.append("суставы: " + ("без щелей" if not joints else f"{len(joints)} замечаний"))
    if joints:
        bad.append("суставы")
    enc = rep.get("enclosed_faces")
    if enc is not None:
        lines.append(f"невидимых граней: {enc}")
    return lines, bad


def row(sheet, d, y, it, a, col):
    """Ряд существа: 4 кадра слева, текст справа. Возвращает высоту ряда."""
    pic, gap = 300, 10
    x = SH.M
    for view, cap in (("front", "спереди"), ("side", "сбоку"), ("hero", "3/4"), ("face", "лицо")):
        im = frame(it["id"], view)
        if im is not None:
            sheet.paste(V.fit(im, pic, pic), (x, y))
        else:
            d.rectangle((x, y, x + pic, y + pic), fill=(60, 30, 30))
            d.text((x + 12, y + 12), "нет кадра", font=V.font(22, True), fill=(255, 200, 200))
        V.label(d, x + 8, y + pic - 40, cap)
        x += pic + gap
    tx = x + 14
    tw = SH.W - SH.M - tx
    rating = a.get("rating", "—")
    rc = RATING.get(rating, (120, 120, 132))
    ty = y + 4
    d.rectangle((tx - 14, y, tx - 6, y + pic), fill=col)
    ty = V.para(d, tx, ty, f"№{it['n']} {it['name']}", tw - 260, size=30, fill=SH.INK, bold=True)
    f = V.font(24, True)
    rw = d.textlength(rating, font=f)
    d.rectangle((SH.W - SH.M - rw - 30, y + 4, SH.W - SH.M, y + 46), fill=rc)
    d.text((SH.W - SH.M - rw - 15, y + 9), rating, font=f, fill=(255, 255, 255))
    ty = V.para(d, tx, ty + 2, f"{it['id']} · {SH.RARITY_RU[it['rarity']]} · «вау» {it['wow']} · семья {it['family']}", tw,
                size=18, fill=col) + 6
    # признаки вида: цветная метка + текст, в две колонки
    signs = a.get("signs") or []
    half = (len(signs) + 1) // 2
    cw = tw // 2
    sy = ty
    for i, (text, mark) in enumerate(signs):
        cx = tx + (i // half) * cw if half else tx
        cy = sy + (i % half) * 30 if half else sy
        word, mc = MARK.get(mark, ("?", (150, 150, 150)))
        d.rectangle((cx, cy + 4, cx + 70, cy + 28), fill=mc)
        d.text((cx + 6, cy + 3), word, font=V.font(17, True), fill=(255, 255, 255))
        V.para(d, cx + 80, cy + 2, text, cw - 90, size=18, fill=SH.INK)
    ty = sy + max(half, 1) * 30 + 6
    ty = V.para(d, tx, ty, "Эмоция: " + it["emotion"] + (" — " + a["emotion"] if a.get("emotion") else ""), tw, size=18,
                fill=SH.DIM) + 4
    lines, bad = numbers(report(it["id"]))
    ty = V.para(d, tx, ty, " · ".join(lines), tw, size=17, fill=(235, 120, 120) if bad else SH.DIM) + 4
    for p in a.get("problems") or []:
        ty = V.para(d, tx, ty, "— " + p, tw, size=18, fill=(250, 200, 120)) + 2
    for p in a.get("fixes") or []:
        ty = V.para(d, tx, ty, "→ " + p, tw, size=18, fill=(150, 220, 160)) + 2
    return max(pic, ty - y) + 14


def page(items, audit, rar):
    group = [it for it in items if it["rarity"] == rar]
    col = SH.RARITY[rar]
    sheet = Image.new("RGB", (SH.W, 400 * len(group) + 400), SH.BG)
    d = ImageDraw.Draw(sheet)
    ok = sum(1 for it in group if audit.get(it["id"], {}).get("rating") == "ок")
    SH.header(d, f"Аудит анатомии D64 — {SH.RARITY_RU[rar]} ({len(group)})",
              f"Быстрая сборка без карт. «ок» — {ok} из {len(group)}. Признаки вида — из каталога docs/BOSS6_CATALOG.md; "
              "числа — из отчёта сборки.")
    y = 130
    for it in group:
        y += row(sheet, d, y, it, audit.get(it["id"], {}), col)
    sheet = sheet.crop((0, 0, SH.W, y + SH.M))
    out = os.path.join(PROD, f"5_audit_{rar.lower()}.png")
    sheet.save(out)
    return out


def overview(items, audit):
    """Все 30 на одном листе (герой-кадр, оценка цветной полосой) — открыть первым."""
    cols, cell = 6, 380
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGB", (SH.W, 130 + rows * (cell + 70) + 160), SH.BG)
    d = ImageDraw.Draw(sheet)
    counts = {k: sum(1 for it in items if audit.get(it["id"], {}).get("rating") == k) for k in RATING}
    SH.header(d, "Аудит анатомии 30 существ джунглей — до запекания карт",
              "Оценки: " + ", ".join(f"{k} — {v}" for k, v in counts.items()) + ". Подробно — листы по редкостям.")
    gap = (SH.W - 2 * SH.M - cols * cell) // (cols - 1)
    for i, it in enumerate(items):
        x = SH.M + (i % cols) * (cell + gap)
        y = 130 + (i // cols) * (cell + 70)
        im = frame(it["id"], "hero")
        if im is not None:
            sheet.paste(V.fit(im, cell, cell), (x, y))
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


def doc(items, audit):
    lines = ["# Босс 6: аудит анатомии 30 существ джунглей (D64)", "",
             "Создан скриптом `scripts/boss6_anatomy_audit.py` по кадрам быстрой сборки (`art_jungle.py quick`) — "
             "до запекания карт. Листы (вне git): `assets/concepts/bosses_5_10/boss6_prod/5_audit_*.png`.", "",
             "| № | Существо | Редкость | Оценка | Признаки (есть / слабо / нет) | Треуг. | Замечания |",
             "|---|---|---|---|---|---|---|"]
    for it in items:
        a = audit.get(it["id"], {})
        signs = a.get("signs") or []
        cnt = "/".join(str(sum(1 for _, m in signs if m == k)) for k in ("+", "±", "-"))
        rep = report(it["id"])
        probs = "; ".join(a.get("problems") or []) or "—"
        lines.append(f"| {it['n']} | {it['name']} | {it['rarity']} | {a.get('rating', '—')} | {cnt} | "
                     f"{rep.get('tris_without_stand', '—')} | {probs} |")
    open(DOC, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    return DOC


def main():
    items = CS.rows()
    audit = json.load(open(AUDIT, encoding="utf-8")) if os.path.exists(AUDIT) else {}
    outs = [overview(items, audit)] + [page(items, audit, r) for r in ("Common", "Rare", "Epic", "Legendary")]
    outs.append(doc(items, audit))
    return outs


if __name__ == "__main__":
    for o in main():
        print(o)
