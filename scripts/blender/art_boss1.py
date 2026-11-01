"""Коллекция босса 1 «Сторожевой пёс» — народные промыслы (D38), стиль D39: четыре объёмных произведения.

Глиняная свистулька (дымковский петушок), расписной поднос (жостовский букет на подставке), матрёшка-великан и
лошадка-качалка. Геометрия каждого предмета своя; общие инструменты (блоки, кольца D39, запекание, рендеры) —
art_style.py. Картина «Подсолнухи» — отдельным шагом.

Пишет assets/models/Art_Boss1.fbx (4 меша: Art_<id>), assets/textures/art/<id>_{color,normal}.png (+ общая
art_roughness.png), а в папку превью — повороты, крупные кадры, общий кадр с манекеном и <id>.json для Studio.
Запуск: blender --background --factory-startup --python scripts/blender/art_boss1.py -- <репо> <превью>
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, PREVIEWS = os.path.abspath(argv[0]), os.path.abspath(argv[1])
TEXDIR = os.path.join(REPO, "assets", "textures", "art")
os.makedirs(PREVIEWS, exist_ok=True)
os.makedirs(TEXDIR, exist_ok=True)


def eye(art, x0, x1, z0, z1, at, glint, sides=(-1, 1), plane="xz"):
    """Чёрный квадратный глаз с белым бликом (как у животных из TikTok) на гранях side·at."""
    gx0, gx1, gz0, gz1 = glint
    for s in sides:
        if plane == "xz":
            art.box("black", x0, x1, s * (at - 0.02), s * (at + 0.03), z0, z1, bevel=0)
            art.box("glint", gx0, gx1, s * (at + 0.02), s * (at + 0.05), gz0, gz1, bevel=0)
        else:
            art.box("black", s * (at - 0.02), s * (at + 0.03), x0, x1, z0, z1, bevel=0)
            art.box("glint", s * (at + 0.02), s * (at + 0.05), gx0, gx1, gz0, gz1, bevel=0)


# ── 1. Глиняная свистулька: дымковский петушок на подставке, голова слева (-x), свисток у хвоста ────────────


def folk_whistle():
    a = S.Art("Art_FolkWhistle", ring_z0=0.86)
    a.paint("clay", "F6F0E4", rings=True)  # белая обожжённая глина
    a.paint("terracotta", "D2693C", rings=True)
    for key, code in (("red", "E23B32"), ("blue", "2F6BD8"), ("yellow", "FFC531"), ("green", "2FAE5A"),
                      ("beak", "F59E1B"), ("black", "1F1F26"), ("glint", "FFFFFF")):
        a.paint(key, code)
    # подставка и ножка
    a.box("terracotta", -0.5, 0.5, -0.38, 0.38, 0.0, 0.16)
    a.box("terracotta", -0.4, 0.4, -0.3, 0.3, 0.14, 0.24)
    a.box("clay", -0.22, 0.22, -0.2, 0.2, 0.22, 0.44)
    # тело ступенями: брюшко, корпус, спинка
    a.box("clay", -0.5, 0.42, -0.36, 0.36, 0.42, 0.62)
    a.box("clay", -0.66, 0.6, -0.44, 0.44, 0.6, 1.12)
    a.box("clay", -0.52, 0.5, -0.38, 0.38, 1.1, 1.26)
    # шея, голова, макушка
    a.box("clay", -0.64, -0.2, -0.32, 0.32, 1.1, 1.5)
    a.box("clay", -0.74, -0.12, -0.34, 0.34, 1.46, 1.98)
    a.box("clay", -0.64, -0.22, -0.28, 0.28, 1.96, 2.04)
    a.box("red", -0.69, -0.17, -0.35, 0.35, 1.13, 1.21)  # ожерелье
    # клюв, гребень, бородка
    a.box("beak", -0.96, -0.72, -0.12, 0.12, 1.68, 1.8)
    a.box("beak", -0.88, -0.72, -0.1, 0.1, 1.6, 1.69)
    for x0, x1, z1 in ((-0.66, -0.52, 2.22), (-0.5, -0.36, 2.3), (-0.34, -0.22, 2.18)):
        a.box("red", x0, x1, -0.09, 0.09, 2.02, z1)
    a.box("red", -0.8, -0.66, -0.09, 0.09, 1.42, 1.6)
    eye(a, -0.56, -0.4, 1.68, 1.84, 0.34, (-0.48, -0.42, 1.77, 1.82))
    # хвост-веер ступенями вверх и назад
    feathers = (("blue", 0.5, 0.82, 0.8, 1.42, 0.18), ("yellow", 0.72, 1.02, 1.05, 1.78, 0.15),
                ("red", 0.92, 1.18, 1.32, 2.08, 0.18))  # соседние перья разной толщины — без общих граней
    for key, x0, x1, z0, z1, t in feathers:
        a.box(key, x0, x1, -t, t, z0, z1)
    # белые точки на перьях хвоста (дымковская роспись)
    for (x0, z0), (*_, t) in zip(((0.6, 1.22), (0.82, 1.56), (1.0, 1.86)), feathers):
        for s in (-1, 1):
            a.box("glint", x0, x0 + 0.08, s * (t - 0.02), s * (t + 0.03), z0, z0 + 0.08, bevel=0)
    # свисток: мундштук у хвоста, дырочка на торце и на спинке
    a.box("terracotta", 0.5, 0.98, -0.13, 0.13, 0.5, 0.72)
    a.box("black", 0.96, 1.01, -0.06, 0.06, 0.57, 0.66, bevel=0)
    a.box("black", -0.05, 0.13, -0.08, 0.08, 1.24, 1.29, bevel=0)
    # крыло с жёлтыми «яблоками» и полоса росписи на брюшке — с обеих сторон
    wing = ["BBBBB....",
            "BYBYBBB..",
            "BBBBBBBBB",
            ".BYBYBBB.",
            "..BBBBB.."]
    a.pixels(wing, {"B": ("blue", 0.03), "Y": ("yellow", 0.05)}, 0.08, -0.26, 1.02, "xz", 0.44, sides=(-1, 1))
    # грудка: красный цветок с жёлтой серединкой; ножка в цветных поясках
    a.pixels([".R.", "RYR", ".R."], {"R": ("red", 0.03), "Y": ("yellow", 0.045)}, 0.08, 0.12, 0.98, "yz", 0.66,
             sides=(-1,), flip=True)
    a.box("red", -0.235, 0.235, -0.215, 0.215, 0.27, 0.32, bevel=0)
    a.box("blue", -0.235, 0.235, -0.215, 0.215, 0.36, 0.41, bevel=0)
    return a


# ── 2. Расписной поднос: жостовский букет на чёрном лаке, золотая кайма, подставка ─────────────────────────


BOUQUET = [
    "..........GG...........",
    ".....YY...GHG...YY.....",
    "....YDDY..GH...YDDY....",
    "..G..YYG.RRRRR..GYY..G.",
    ".GHG..G.RRDDDRR.G..GHG.",
    "..GHG..RRDRRRDRR..GG...",
    "...GPPP.RDRDDRDR.WWW...",
    "..PPQPPPRDRDRRDRRWBBBW.",
    ".PPQQQPPRRDRRDRRRWBYBW.",
    ".PPQPQPPRRRDDRRRRWBBBW.",
    "..PPPPP.RRRRRRRR..WWW..",
    "...PPP.GGRRRRRRGG..G...",
    "..GG..GHHGRRRRGHHG.GG..",
    ".GHG.GH...GGGG...HG.GHG",
    "..G..BB...GHHG...BB..G.",
    ".....BWB...GG...BWB....",
    "......B...........B....",
]


def painted_tray():
    a = S.Art("Art_PaintedTray", ring_z0=1.1)
    a.paint("lacquer", "1E1F26", rings=True)
    a.paint("wood", "9A5B2E", rings=True)
    for key, code in (("gold", "E9B53A"), ("red", "D92F3A"), ("darkred", "9E1B2A"), ("pink", "F28AA0"),
                      ("rose", "D5607A"), ("white", "F4F1EA"), ("yellow", "FFC531"), ("blue", "4A86E8"),
                      ("green", "3FA34D"), ("darkgreen", "23703A")):
        a.paint(key, code)
    outline = S.octagon(-1.3, 1.3, 0.15, 2.05, 0.42)
    a.prism("lacquer", outline, -0.3, -0.12, axis="y")
    a.frame("gold", outline, 0.14, -0.36, -0.28, axis="y")  # кайма спереди
    a.frame("gold", outline, 0.14, -0.14, -0.08, axis="y")  # и сзади
    # подставка: доска, упор спереди, стойка и крючок сзади
    a.box("wood", -1.0, 1.0, -0.56, 0.4, 0.0, 0.16)
    a.box("wood", -0.9, 0.9, -0.56, -0.37, 0.14, 0.42)
    a.box("wood", -0.14, 0.14, -0.125, 0.2, 0.14, 1.5)
    a.box("wood", -0.1, 0.1, -0.13, 0.26, 1.38, 1.53)
    # букет: листья ниже цветов, сердцевины выше
    cell = 0.075
    palette = {"G": ("green", 0.03), "H": ("darkgreen", 0.03), "R": ("red", 0.05), "P": ("pink", 0.05),
               "W": ("white", 0.05), "B": ("blue", 0.05), "Y": ("yellow", 0.05), "D": ("darkred", 0.065),
               "Q": ("rose", 0.065)}
    a.pixels(BOUQUET, palette, cell, -len(BOUQUET[0]) * cell / 2, 1.1 + len(BOUQUET) * cell / 2, "xz", 0.3)
    return a


# ── 3. Матрёшка-великан: восьмигранные ярусы, платок, лицо, фартук с розой ─────────────────────────────────


def nesting_doll():
    a = S.Art("Art_NestingDoll", ring_z0=0.74)
    a.paint("red", "D93A3A", rings=True)
    for key, code in (("gold", "F2B51E"), ("apron", "FFCE3D"), ("skin", "FAD7B5"), ("hair", "6B3A22"),
                      ("eye", "2A4C9E"), ("glint", "FFFFFF"), ("cheek", "F28C8C"), ("mouth", "C8283A"),
                      ("rose", "E0303A"), ("rosedark", "A51E2B"), ("leaf", "3FA34D")):
        a.paint(key, code)
    # восьмигранные ярусы: круглый низ, широкое тело, плечи, перехват, голова, макушка двумя ступенями
    tiers = [("gold", 0.0, 0.12, 0.76), ("red", 0.1, 0.35, 0.92), ("red", 0.33, 1.15, 1.0), ("red", 1.13, 1.55, 0.92),
             ("red", 1.53, 1.78, 0.8), ("red", 1.76, 1.88, 0.7), ("red", 1.86, 2.8, 0.76), ("red", 2.78, 2.96, 0.62),
             ("red", 2.94, 3.06, 0.42)]
    for key, z0, z1, w in tiers:
        a.prism(key, S.octagon(-w, w, -w, w, 0.3 * w), z0, z1)
    # фартук: по куску на ярус, ступенями вместе с телом; роза с листьями
    for x, z0, z1, w in ((0.42, 0.16, 0.35, 0.92), (0.6, 0.34, 1.14, 1.0), (0.42, 1.13, 1.45, 0.92)):
        a.box("apron", -x, x, -(w - 0.02), -(w + 0.03), z0, z1, bevel=0)
    rose = ["...RRR...",
            ".RRDDDRR.",
            ".RDRRRDR.",
            "RRDRDRDRR",
            ".RDRRRDR.",
            ".RRDDDRR.",
            "GG.RRR.GG",
            ".GGG.GGG."]
    cell = 0.08
    a.pixels(rose, {"R": ("rose", 0.04), "D": ("rosedark", 0.055), "G": ("leaf", 0.03)}, cell,
             -len(rose[0]) * cell / 2, 0.74 + len(rose) * cell / 2, "xz", 1.03)
    # платок: жёлтая кайма вокруг лица, узелок под подбородком, жёлтый горошек по бокам и сзади
    a.box("apron", -0.45, 0.45, -0.74, -0.79, 1.94, 2.72, bevel=0)
    a.box("apron", -0.12, 0.12, -0.66, -0.84, 1.76, 1.95)
    flowers = [".Y.....",
               "YWY....",
               ".Y.....",
               ".......",
               "....Y..",
               "...YWY.",
               "....Y.."]
    for plane, sides in (("yz", (-1, 1)), ("xz", (1,))):
        a.pixels(flowers, {"Y": ("apron", 0.03), "W": ("glint", 0.04)}, 0.08, -0.28, 2.61, plane, 0.76, sides=sides)
    # лицо пикселями: волосы с пробором, глаза с бликом, румянец, рот
    face = ["HHHHHHHHHH",
            "HHHHSSHHHH",
            "HHSSSSSSHH",
            "HSSSSSSSSH",
            "SSEWSSEWSS",
            "SSEESSEESS",
            "SCCSSSSCCS",
            "SSSSMMSSSS",
            "SSSSSSSSSS"]
    cell = 0.075
    a.pixels(face, {"S": ("skin", 0.03), "H": ("hair", 0.045), "E": ("eye", 0.045), "W": ("glint", 0.06),
                    "C": ("cheek", 0.035), "M": ("mouth", 0.04)}, cell, -len(face[0]) * cell / 2,
             2.66, "xz", 0.79)
    return a


# ── 4. Лошадка-качалка: профиль влево (-x), полозья ступенчатой дугой, грива, седло, ручка ────────────────


def rocking_horse():
    a = S.Art("Art_RockingHorse", ring_z0=1.225)
    a.paint("horse", "F5EFE6", rings=True)
    for key, code in (("mane", "F2A93B"), ("red", "D23A2E"), ("saddle", "2E6FD8"), ("yellow", "FFC531"),
                      ("wood", "6B4423"), ("black", "1F1F26"), ("glint", "FFFFFF"), ("green", "3FA34D")):
        a.paint(key, code)
    radius, seg, n = 2.6, 0.36, 9

    def arc(x):
        return radius - math.sqrt(radius * radius - x * x)

    # полозья: цельная ступенчатая дуга (без швов между ступенями) с завитками на концах
    xs = [(k - n / 2) * seg for k in range(n + 1)]
    zb = [arc((xs[k] + xs[k + 1]) / 2) for k in range(n)]
    h, curl_w, curl_h = 0.22, 0.16, 0.22
    pts = []
    for k in range(n):
        pts += [(xs[k], zb[k]), (xs[k + 1], zb[k])]
    pts += [(xs[n], zb[-1] + h + curl_h), (xs[n] - curl_w, zb[-1] + h + curl_h)]
    for k in reversed(range(n)):
        xa = xs[0] + curl_w if k == 0 else xs[k]
        xb = xs[n] - curl_w if k == n - 1 else xs[k + 1]
        pts += [(xb, zb[k] + h), (xa, zb[k] + h)]
    pts += [(xs[0] + curl_w, zb[0] + h + curl_h), (xs[0], zb[0] + h + curl_h)]
    clean = [p for i, p in enumerate(pts) if p != pts[i - 1]]
    for s in (-1, 1):
        a.extrude("red", clean, s * 0.33, s * 0.5, axis="y")
    for x in (-0.72, 0.72):  # перекладины
        a.box("wood", x - 0.1, x + 0.1, -0.48, 0.48, 0.26, 0.4)
    for x in (-0.72, 0.72):  # ноги с копытами и красными поясками
        for s in (-1, 1):
            y0, y1 = sorted((s * 0.12, s * 0.3))
            a.box("horse", x - 0.09, x + 0.09, y0, y1, 0.39, 1.0)
            a.box("wood", x - 0.12, x + 0.12, y0 - 0.02, y1 + 0.02, 0.36, 0.5)
            a.box("red", x - 0.105, x + 0.105, y0 - 0.015, y1 + 0.015, 0.66, 0.72, bevel=0)
    # тело, брюхо, круп, грудь
    a.box("horse", -0.82, 0.82, -0.36, 0.36, 0.95, 1.5)
    a.box("horse", -0.68, 0.68, -0.32, 0.32, 0.88, 0.97)
    a.box("horse", 0.3, 0.84, -0.34, 0.34, 1.48, 1.6)
    a.box("horse", -0.98, -0.8, -0.3, 0.3, 1.0, 1.42)
    # шея ступенями, голова, морда, лоб, уши
    a.box("horse", -1.0, -0.52, -0.26, 0.26, 1.45, 1.82)
    a.box("horse", -1.12, -0.66, -0.24, 0.24, 1.78, 2.1)
    a.box("horse", -1.55, -0.86, -0.27, 0.27, 2.02, 2.4)
    a.box("horse", -1.72, -1.4, -0.22, 0.22, 1.98, 2.24)
    a.box("horse", -1.3, -0.9, -0.22, 0.22, 2.38, 2.46)
    for s in (-1, 1):
        y0, y1 = sorted((s * 0.08, s * 0.2))
        a.box("horse", -1.0, -0.88, y0, y1, 2.44, 2.64)
    eye(a, -1.29, -1.14, 2.2, 2.33, 0.27, (-1.23, -1.17, 2.27, 2.32))
    for s in (-1, 1):  # ноздри
        a.box("black", -1.68, -1.6, s * 0.2, s * 0.25, 2.08, 2.15, bevel=0)
    a.box("red", -1.5, -1.42, -0.29, 0.29, 1.96, 2.43)  # уздечка
    a.box("wood", -1.06, -0.96, -0.52, 0.52, 2.08, 2.18)  # ручка
    # грива и чёлка, хвост
    # соседние пряди разной толщины — без общих граней
    for x0, x1, z0, z1, t in ((-0.62, -0.42, 1.5, 1.95, 0.1), (-0.76, -0.56, 1.8, 2.28, 0.12),
                              (-0.94, -0.72, 2.1, 2.52, 0.1), (-1.2, -1.0, 2.42, 2.52, 0.12)):
        a.box("mane", x0, x1, -t, t, z0, z1)
    for x0, x1, z0, z1, t in ((0.8, 1.02, 1.22, 1.52, 0.1), (0.96, 1.16, 0.92, 1.3, 0.12), (1.08, 1.26, 0.66, 1.0, 0.1)):
        a.box("mane", x0, x1, -t, t, z0, z1)
    # седло: сиденье, передняя и задняя луки, чепрак с жёлтой каймой и цветком
    a.box("saddle", -0.3, 0.34, -0.38, 0.38, 1.47, 1.62)
    a.box("saddle", 0.24, 0.4, -0.3, 0.3, 1.58, 1.74)
    a.box("saddle", -0.34, -0.22, -0.24, 0.24, 1.58, 1.72)
    for s in (-1, 1):
        a.box("saddle", -0.36, 0.42, s * 0.34, s * 0.39, 1.12, 1.49, bevel=0)
        a.box("yellow", -0.38, 0.44, s * 0.34, s * 0.41, 1.06, 1.14, bevel=0)
    flower = [".Y.Y.",
              "YRRRY",
              ".RYR.",
              "YRRRY",
              ".YGY."]
    a.pixels(flower, {"Y": ("yellow", 0.03), "R": ("red", 0.04), "G": ("green", 0.03)}, 0.07, -0.145, 1.48,
             "xz", 0.39, sides=(-1, 1))
    return a


# ── Сборка, запекание, экспорт, проверочные рендеры ─────────────────────────────────────────────────────────

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
collection = bpy.data.collections.new("ArtBoss1")
bpy.context.scene.collection.children.link(collection)

ITEMS = [("FolkWhistle", folk_whistle), ("PaintedTray", painted_tray), ("NestingDoll", nesting_doll),
         ("RockingHorse", rocking_horse)]
report, objs = {}, []
if len(argv) > 2 and argv[2] == "check":
    for item_id, make in ITEMS:
        art = make()
        art.build(collection)
        print("CHECK", item_id, json.dumps(art.stats, ensure_ascii=False))
    sys.exit(0)
for item_id, make in ITEMS:
    art = make()
    obj = art.build(collection)
    uv = S.bake(obj, art, TEXDIR, item_id)
    lo, hi = S.bounds(obj)
    report[item_id] = {**art.stats, **{k: round(v, 3) for k, v in uv.items()},
                       "size": [round(hi[i] - lo[i], 2) for i in range(3)]}
    S.studio_json(obj, os.path.join(PREVIEWS, f"{item_id}.json"))
    objs.append(obj)

S.export_fbx(objs, os.path.join(REPO, "assets", "models", "Art_Boss1.fbx"))

prev = S.Preview(collection)
heroes = [S.render_item(prev, obj, PREVIEWS) for obj in objs]
S.strip(heroes, os.path.join(PREVIEWS, "sheet.png"), gap=12)

# Общий кадр: четыре предмета в ряд и манекен.
x = -6.6
for obj in objs:
    lo, hi = S.bounds(obj)
    obj.location.x = x - lo.x
    x += (hi.x - lo.x) + 0.7
S.mannequin(collection, x + 0.9)
center = Vector(((-6.6 + x + 2.4) / 2, 0, 2.2))
prev.aim_lights(center)
prev.shot(os.path.join(PREVIEWS, "group.png"), (center.x, -22.0, 4.6), (center.x, 0, 2.0), 50, (1600, 800))
for obj in objs:
    obj.location = (0, 0, 0)

with open(os.path.join(PREVIEWS, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("BOSS1_OK " + json.dumps(report, ensure_ascii=False))
