"""Лист «было → стало» босса 7 по правкам владельца к аудиту анатомии (2026-11-26): только исправленные существа.

На каждое: «было» (кадры до правок, boss7_prod/before/) и «стало» (быстрая сборка art_bank.py quick) — 3/4, спереди,
сбоку; что сделано; числа отчёта сборки (треугольники без подставки, суставы).
Выход (вне git): assets/concepts/bosses_5_10/boss7_prod/7_redo.png (и 7_redo_2.png, если не помещается).
Запуск из корня: python scripts/boss7_redo_sheet.py
Зависит от Pillow, scripts/boss7_anatomy_audit.py (отчёты, каталог) и scripts/blender/boss7/sheet.py (оформление).
"""

import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import boss7_anatomy_audit as AU  # noqa: E402

SH, V = AU.SH, AU.V
BEFORE = os.path.join(AU.PROD, "before")
V1_TAG, V2_TAG = (120, 120, 132), (61, 200, 110)

DONE = {  # что сделано (замечания владельца и аудита)
    "StarNoseMole": "Переделан: тело — одна круглая «картофелина», голова сидит в теле, самородок прижат к ладоням.",
    "GoldenPheasant": "Переделан: хохол растёт с макушки назад по спине, лицо светлое и открытое, клюв на виду.",
    "MirrorMorpho": "Переделан: классическая бабочка — 4 широких скруглённых крыла раскрыты в стороны, тело толще, "
                    "ноги короткие.",
    "VeilGoldfish": "Переделан: цельная круглая рыбка на широком бугре воды (не палочка); вуали — длинные плавные "
                    "ленты (в игре полупрозрачные), хвост веером назад и в стороны, к игроку.",
    "SapphireTiger": "Переделан: мощная грудь и плечи, крупные лапы, шаг — правая передняя поднята, хвост дугой; "
                     "синие полосы светятся (Neon).",
    "JugglerStarfish": "Цвет оранжево-жёлтый с синими пятнами, лицо меньше, улыбка маленькая (не мультяшная).",
    "WhiskerShrimp": "Усы — длинные дуги назад с маленьким завитком на кончиках.",
    "HandstandSkunk": "Хвост — пушистый чёрный веер с золотой полосой.",
    "RingLemur": "Хвост — S за спиной, не крючок над головой.",
    "StashSquirrel": "Хвост — пушистый S, жёлуди крупные, торчат наружу.",
    "PearlPlatypus": "Голова поднята, клюв вверх; сам крупнее на плите.",
    "BeadGila": "Голова поднята на шее; сам крупнее на плите.",
    "HoardHamster": "Суставы: шар-сустав в плечах (сгиб не раскрывается).",
    "RaccoonMagpie": "Суставы крыльев и хвоста; крылья прижаты к бокам.",
    "GreedyWolverine": "Суставы рук; светлые лоб и морда, глаза крупнее — эмоция читается.",
    "JumpJerboa": "Сустав хвоста.",
    "PouchKangaroo": "Лапки утоплены в тело (была щель 0.18).",
    "PearlOtter": "Сустав лапки.",
    "SniffCoati": "Сустав хвоста.",
    "GoldHornKid": "Шея внахлёст с грудью.",
    "TreasureGriffin": "Сустав хвоста.",
}
ORDER = ["StarNoseMole", "GoldenPheasant", "MirrorMorpho", "VeilGoldfish", "SapphireTiger", "JugglerStarfish",
         "WhiskerShrimp", "HandstandSkunk", "RingLemur", "StashSquirrel", "PearlPlatypus", "BeadGila", "HoardHamster",
         "RaccoonMagpie", "GreedyWolverine", "JumpJerboa", "PouchKangaroo", "PearlOtter", "SniffCoati", "GoldHornKid",
         "TreasureGriffin"]


def shot(folder, item, view):
    p = os.path.join(folder, f"{item}_{view}.png")
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert("RGB")
    if view == "hero":
        w, h = im.size
        im = im.crop((int(w * 0.15), int(h * 0.12), int(w * 0.85), int(h * 0.82)))
    return im


def tag(d, x, y, text, col):
    f = V.font(24, True)
    tw = d.textlength(text, font=f)
    d.rectangle((x, y, x + tw + 20, y + 36), fill=col)
    d.text((x + 10, y + 3), text, font=f, fill=(255, 255, 255))


def block(sheet, d, y, it):
    pic, gap = 250, 8
    x = SH.M
    for folder, t in ((BEFORE, "было"), (AU.SHOTS, "стало")):
        for view in ("hero", "front", "side"):
            im = shot(folder, it["id"], view)
            if im is not None:
                sheet.paste(V.fit(im, pic, pic), (x, y))
            if view == "hero":
                tag(d, x + 6, y + 6, t, V1_TAG if t == "было" else V2_TAG)
            x += pic + gap
        x += 14
    tx = x + 6
    tw = SH.W - SH.M - tx
    col = SH.RARITY[it["rarity"]]
    d.rectangle((tx - 12, y, tx - 5, y + pic), fill=col)
    ty = V.para(d, tx, y + 2, f"№{it['n']} {it['name']}", tw, size=26, fill=SH.INK, bold=True)
    ty = V.para(d, tx, ty + 2, DONE[it["id"]], tw, size=18, fill=SH.INK) + 4
    rep = AU.report(it["id"])
    lines, bad = AU.numbers(rep)
    V.para(d, tx, ty, " · ".join(lines), tw, size=16, fill=(235, 120, 120) if bad else SH.DIM)
    return pic + 12


def main():
    its = {it["id"]: it for it in AU.items()}
    todo = [its[i] for i in ORDER]
    outs = []
    per = 11
    for page in range((len(todo) + per - 1) // per):
        group = todo[page * per:(page + 1) * per]
        sheet = Image.new("RGB", (SH.W, 130 + len(group) * 262 + SH.M), SH.BG)
        d = ImageDraw.Draw(sheet)
        SH.header(d, f"Босс 7 — «было → стало» по аудиту анатомии ({page + 1}/2)",
                  "Переделки и мелкие правки владельца 2026-11-26 и 13 суставных замечаний аудита. Слева — было, "
                  "справа — стало (3/4, спереди, сбоку).")
        y = 130
        for it in group:
            y += block(sheet, d, y, it)
        out = os.path.join(AU.PROD, f"7_redo{'' if page == 0 else '_2'}.png")
        sheet.crop((0, 0, SH.W, y + SH.M)).save(out)
        outs.append(out)
    return outs


if __name__ == "__main__":
    for o in main():
        print(o)
