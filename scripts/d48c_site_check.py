"""D48-C — проверка галерей на всех пяти участках мира по реальным габаритам объектов (снимок из Studio Play:
assets/concepts/d48/c2/world_scan.json) и раскладке scripts/blender/d48c_layout.py. Считает зазоры от галерей
(с карнизом и клумбой) до соседних музеев, обрыва, деревьев, поля качалки, гигантской гантели и таблички; рисует план
мира. Код возврата 1 — если зазор меньше допустимого или есть пересечение.

Гантель есть только у занятого участка — в снимке она у участка 1; для проверки она ставится на каждый участок
в тех же осях участка (худший случай).
Запуск: python scripts/d48c_site_check.py  → assets/concepts/d48/c2/site_check.png
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
SCAN = json.load(open(os.path.join(C2, "world_scan.json"), encoding="utf-8"))
XS, PZ = (150, 75, 0, -75, -150), 100
MIN_GAP = 3.0  # до объекта, у которого игрок может стоять (поле, гантель, дерево)
MIN_WALK = 8.0  # проход между музеями
CLOSED = 0.5  # щель уже не щель: в неё не пролезть


def world(i, x0, x1, z0, z1):
    xp = XS[i]
    a, b = xp + x0, xp + x1
    return (min(a, b), max(a, b), PZ + z0, PZ + z1)


def envelopes(i):
    """Галерея (с карнизом) и клумба для участка i, обе стороны."""
    out = []
    for sx in (-1, 1):
        out.append(("gallery", sx, world(i, sx * L.GAL_IN, sx * L.GAL_EAVE, L.GAL_Z0 - 0.6, L.GAL_Z1 + 0.6)))
        out.append(("planter", sx, world(i, sx * L.PLANTER[0], sx * L.PLANTER[1], L.GAL_Z0, L.GAL_Z1)))
    return out


def gap(a, b):
    """Зазор между прямоугольниками (x0, x1, z0, z1): < 0 — пересечение."""
    dx = max(b[0] - a[1], a[0] - b[1])
    dz = max(b[2] - a[3], a[2] - b[3])
    if dx < 0 and dz < 0:
        return max(dx, dz)
    return max(dx, 0) if dz < 0 else (max(dz, 0) if dx < 0 else (dx * dx + dz * dz) ** 0.5)


def local_box(i, box):
    xp = XS[i]
    return (box[0] - xp, box[1] - xp, box[2] - PZ, box[3] - PZ)


dumbbell_local = local_box(0, SCAN["plots"][0]["GiantDumbbell"])
results, failed = [], 0


def check(ok, text):
    global failed
    results.append(("ок  " if ok else "ОШИБКА ") + text)
    if not ok:
        failed += 1


for i in range(5):
    plot = SCAN["plots"][i]
    objs = {"поле качалки": plot["GymField"], "табличка": plot["SignPost"],
            "гантель": world(i, *dumbbell_local)}
    for kind, sx, env in envelopes(i):
        if kind != "gallery":
            continue
        side = "+x" if sx > 0 else "−x"
        for name, box in objs.items():
            g = gap(env, box)
            check(g >= MIN_GAP, f"участок {i + 1} {side}: до «{name}» {g:.1f} ст.")
        tg = min(gap(env, t) for t in SCAN["trees"])
        check(tg >= MIN_GAP, f"участок {i + 1} {side}: до ближайшего дерева {tg:.1f} ст.")
        for j in range(5):
            if j == i:
                continue
            for k2, s2, env2 in envelopes(j):
                g = gap(env, env2)
                check(g >= MIN_WALK, f"участок {i + 1} {side} ↔ {k2} участка {j + 1}: {g:.1f} ст.") if g < 40 else None
            g = gap(env, (SCAN["plots"][j]["Floor"]))
            if g < 40:
                check(g >= MIN_WALK, f"участок {i + 1} {side} ↔ плита участка {j + 1}: {g:.1f} ст.")
    # клумбы у обрыва: либо вплотную (щели нет), либо проход
    for kind, sx, env in envelopes(i):
        if kind != "planter":
            continue
        cg = min(gap(env, c) for c in SCAN["cliffs"])
        side = "+x" if sx > 0 else "−x"
        if cg < 10:
            check(cg <= CLOSED or cg >= MIN_WALK, f"участок {i + 1} {side}: клумба — обрыв {cg:.1f} ст. "
                                                 f"({'щель закрыта' if cg <= CLOSED else 'проход'})")
        gall = [e for k, s, e in envelopes(i) if k == "gallery" and s == sx][0]
        gc = min(gap(gall, c) for c in SCAN["cliffs"])
        check(gc >= 0, f"участок {i + 1} {side}: галерея не входит в обрыв ({gc:.1f} ст.)")
    back = min(gap(e, c) for k, s, e in envelopes(i) if k == "gallery" for c in SCAN["cliffs"] if c[2] > 125)
    check(back >= MIN_GAP, f"участок {i + 1}: от галерей до задней кромки {back:.1f} ст.")

for line in results:
    print(line)
print("ИТОГ:", "ошибок нет" if not failed else f"ошибок {failed}")


# ── рисунок ────────────────────────────────────────────────────────────────────────────────────────────────────
def font(weight, size):
    path = None
    for p in sorted(glob.glob(os.path.expandvars(rf"%LOCALAPPDATA%\Roblox\Versions\*\content\fonts\Montserrat-{weight}.ttf"))):
        path = p
    return ImageFont.truetype(path, size)


S, X0, Z0, W, H = 5.0, -205, 40, 2050, 640
img = Image.new("RGB", (W, H + 170), (126, 199, 90))
d = ImageDraw.Draw(img, "RGBA")


def r(box, fill=None, outline=None, width=2):
    x0, x1, z0, z1 = box
    # +x мира — справа на рисунке, вход музеев (−z) — внизу
    d.rectangle(((x0 - X0) * S, 170 + H - (z1 - Z0) * S, (x1 - X0) * S, 170 + H - (z0 - Z0) * S), fill=fill,
                outline=outline, width=width)


def say(xy, body, size=20, fill=(255, 255, 255), anchor="mm", weight="Black"):
    d.text(xy, body, font=font(weight, size), fill=fill, stroke_width=max(2, size // 8), stroke_fill=(24, 20, 46),
           anchor=anchor)


def pt(x, z):
    return ((x - X0) * S, 170 + H - (z - Z0) * S)


for c in SCAN["cliffs"]:
    r(c, (120, 96, 70, 255))
for t in SCAN["trees"]:
    r(t, (46, 120, 60, 255))
for name, box in SCAN["other"].items():
    r(box, (200, 200, 220, 255))
for i in range(5):
    plot = SCAN["plots"][i]
    r(plot["Floor"], None, (255, 255, 255, 255), 2)
    r(plot["Building"], (236, 230, 214, 255))
    r(plot["GymField"], (90, 170, 255, 160))
    r(world(i, *dumbbell_local), (150, 100, 60, 230))
    for kind, sx, env in envelopes(i):
        r(env, (255, 214, 90, 230) if kind == "gallery" else (60, 150, 70, 255), (24, 20, 46, 255), 1)
    say(pt(XS[i], 104), f"участок {i + 1}", 18)
d.rectangle((0, 0, W, 170), fill=(24, 28, 48))
say((W // 2, 44), "Галереи D48-C на всех пяти участках (по снимку мира из Studio)", 36)
say((W // 2, 92), "жёлтое — галереи, зелёное — клумбы, белая рамка — участок 44 × 44, синее — поле качалки, "
                  "коричневое — гантель и обрыв, тёмно-зелёное — деревья", 19, (205, 216, 245), weight="Bold")
say((W // 2, 132), ("ошибок нет" if not failed else f"ошибок: {failed}") + " · между музеями проход 12,2 ст. · "
    "до гантели 3,5 · до поля 6,4 · у обрыва щель закрыта клумбой", 21, (140, 255, 160) if not failed else
    (255, 150, 150), weight="Bold")
img.save(os.path.join(C2, "site_check.png"))
sys.exit(1 if failed else 0)
