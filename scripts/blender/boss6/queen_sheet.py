"""Лист игровой модели королевы-мухоловки (босс 6, шаг 2 D64) — владельцу до запекания карт (читается с телефона).

  python scripts/blender/boss6/queen_sheet.py → assets/concepts/bosses_5_10/boss6_prod/9_queen.png (вне git)
Кадры: быстрая сборка scripts/blender/boss6_flytrap.py (виды, силуэты, позы, ладони) и раскадровка клипов
scripts/blender/boss6_flytrap_anim.py (frames/<клип>_<k>.png) в boss6_prod/queen/; числа — report.json и
anim_report.json там же. Оформление — sheet.py (шапка, ряды кадров, панели).
"""

import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sheet as SH  # noqa: E402

V = SH.V
QDIR = os.path.join(SH.REPO, "assets", "concepts", "bosses_5_10", "boss6_prod", "queen")
OUT = os.path.join(SH.REPO, "assets", "concepts", "bosses_5_10", "boss6_prod", "9_queen.png")
CLIPS = [("sleep_idle", "Сон (цикл 6.4 с)"), ("wake", "Пробуждение 2.4 с"), ("combat_idle", "Боевая стойка (цикл 3.6 с)"),
         ("turn", "Поворот на месте (цикл 0.8 с; не ходит)"), ("snap", "«Захлоп» — основной выпад 1.3 с"),
         ("grab", "«Хватает» — особая атака 1.4 с"), ("hit", "Получение урона 0.47 с"), ("victory", "Победа 2.2 с"),
         ("defeat", "Поражение 2.4 с (корона падает)"), ("fall_asleep", "Засыпание 1.6 с")]


def q(name):
    return os.path.join(QDIR, name + ".png")


def main():
    rep = json.load(open(os.path.join(QDIR, "report.json"), encoding="utf-8"))
    anim = json.load(open(os.path.join(QDIR, "anim_report.json"), encoding="utf-8"))
    W, M = SH.W, SH.M
    sheet = Image.new("RGB", (W, 9000), SH.BG)
    d = ImageDraw.Draw(sheet)
    SH.header(d, "Королева-мухоловка — игровая модель и 10 клипов (до запекания карт)",
              f"Быстрая сборка без карт · {rep['tris_total']} треугольников (≤ 8000) · {rep['parts']} подвижных частей · "
              "рост в стойке 24 стада · не ходит, поворачивается на месте (D64 п. 5)")
    y = 128
    y = SH.section(d, y, "Стойка", "спереди · 3/4 · сбоку · сзади")
    size = (W - 2 * M - 3 * 12) // 4
    y = SH.tiles(sheet, d, y, [(q("stand_front"), "спереди"), (q("stand_34"), "3/4"), (q("stand_side"), "сбоку"),
                               (q("stand_back"), "сзади")], size)
    # модерация: силуэты + список проверок
    y = SH.section(d, y, "Модерация: силуэт", "чёрный силуэт спереди и сбоку")
    sw = (W - 2 * M - 12) // 3
    y0 = y
    SH.tiles(sheet, d, y, [(q("stand_sil"), "силуэт спереди"), (q("stand_sil_side"), "силуэт сбоку")], sw)
    x = M + 2 * (sw + 12)
    lines = [
        "• Не фигура человека: голова — бутон с ловушкой и венчиком, тело — стебель без талии и плеч.",
        "• Лозы растут из стебля на разной высоте (0.2 и 1.3 ед.), в стойке одна поднята и закручена, другая свисает к "
        "розетке — нет симметричных «рук».",
        "• Внизу — клубень и розетка листьев на земле, а не юбка или платье; мантия — три коротких отдельных листа.",
        "• Ладонь — три листа-пальца (не кисть человека, не «бантик»).",
        "• Пасть — ловушка мухоловки с тупыми ресничками, крови нет; ничего пугающего.",
        "• Нет текста, логотипов, оружия, чужих персонажей.",
    ]
    ty = y0 + 4
    d.rectangle((x, y0, W - M, y0 + sw), fill=SH.PANEL)
    d.text((x + 18, ty + 8), "Что проверено", font=V.font(28, True), fill=SH.ACC)
    ty += 56
    for ln in lines:
        ty = V.para(d, x + 18, ty, ln, W - M - x - 36, size=20, fill=SH.INK) + 6
    y = y0 + sw + 16
    # позы
    y = SH.section(d, y, "Позы", "3/4; «хватает» — замах и хват")
    size = (W - 2 * M - 3 * 12) // 4
    y = SH.tiles(sheet, d, y, [(q("sleep_34"), "сон"), (q("combat_34"), "бой"), (q("grab_34"), "хватает: замах"),
                               (q("grab2_34"), "хватает: хват")], size)
    y = SH.tiles(sheet, d, y, [(q("snap_34"), "захлоп"), (q("hit_34"), "урон"), (q("victory_34"), "победа"),
                               (q("defeat_34"), "поражение")], size)
    y = SH.section(d, y, "Ладонь из трёх листьев-пальцев", "крупно: стойка · бой · раскрыта · сжата")
    y = SH.tiles(sheet, d, y, [(q("hand_stand"), "стойка"), (q("hand_combat"), "бой"), (q("hand_grab"), "раскрыта"),
                               (q("hand_grab2"), "сжата в кулак")], size)
    y = SH.section(d, y, "Клипы", "по 8 кадров на клип, вид 3/4")
    fw = (W - 2 * M - 7 * 8) // 8
    fh = int(fw * 520 / 420)
    for name, title in CLIPS:
        r = anim.get(name, {})
        bad = r.get("below_ground_frames", 0)
        d.text((M, y), f"{title} — кадров {r.get('frames', '?')}, ниже земли: {bad}", font=V.font(24, True),
               fill=SH.INK if not bad else (235, 120, 120))
        y += 36
        for k in range(8):
            p = os.path.join(QDIR, "frames", f"{name}_{k}.png")
            if os.path.exists(p):
                sheet.paste(V.fit(Image.open(p).convert("RGB"), fw, fh), (M + k * (fw + 8), y))
        y += fh + 18
    sheet = sheet.crop((0, 0, W, y + M))
    sheet.save(OUT)
    return OUT, sheet.size


if __name__ == "__main__":
    print(main())
