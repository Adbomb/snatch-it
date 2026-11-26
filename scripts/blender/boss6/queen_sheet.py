"""Лист игровой модели королевы-мухоловки (босс 6, шаг 2 D64) — владельцу до запекания карт (читается с телефона).

  python scripts/blender/boss6/queen_sheet.py → assets/concepts/bosses_5_10/boss6_prod/9_queen.png (вне git)
  python scripts/blender/boss6/queen_sheet.py eat → boss6_prod/10_queen_eat.png: правки владельца 2026-11-26 —
  контраст с ареной (кадры арены с игровой королевой), зубы вдвое короче, раскадровка клипа «съесть» (D74), сон /
  пробуждение / засыпание в новой палитре.
  … chew → 11_queen_chew.png: раскадровка жевания клипа «съесть» (кадры chew_<k>.png);
  … emo → 13_queen_emo.png: эмоции клипа «съесть» веками и бровями крупно (кадры emo_<k>.png; FLY_EAT=emo);
  … face → 14_queen_face.png: правки головы 2026-11-26 — кант створок тёмно-зелёный, дуги «^^» на нижнем веке,
  «— —» сна на верхнем (кадры с картами boss6_prod/queen_maps/face_*.png) и эмоции «съесть» (emo_<k>.png);
  … maps → 12_queen_maps.png: карты королевы (assets/textures/art/Boss6Flytrap<Карта>_{color,normal}.png) и кадры
  полной сборки с картами (boss6_prod/queen_maps/) — владельцу до загрузки (D70). Кадры — boss6_prod/queen_v2/ (boss6_flytrap.py quick, boss6_flytrap_anim.py
  с FLY_CLIPS=eat,sleep_idle,wake,fall_asleep, arena.py player,approach queen=game out=…/queen_v2/arena).
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


Q2 = os.path.join(SH.REPO, "assets", "concepts", "bosses_5_10", "boss6_prod", "queen_v2")
OUT_EAT = os.path.join(SH.REPO, "assets", "concepts", "bosses_5_10", "boss6_prod", "10_queen_eat.png")
EAT = [(0.0, "стойка"), (0.35, "рывок лозой"), (0.6, "отобрала"), (1.05, "несёт к пасти"), (1.3, "в пасти"),
       (1.5, "захлоп"), (1.75, "жуёт"), (2.0, "жуёт"), (2.8, "вдох"), (3.05, "плевок"), (3.3, "капсула летит"),
       (3.5, "довольная")]  # = EAT_SHOTS в anim


def q2(name):
    return os.path.join(Q2, name + ".png")


def eat_sheet():
    W, M = SH.W, SH.M
    anim = json.load(open(os.path.join(Q2, "anim_report.json"), encoding="utf-8"))
    rep = json.load(open(os.path.join(Q2, "report.json"), encoding="utf-8"))
    rig = json.load(open(os.path.join(Q2, "Boss6_Flytrap.rig.json"), encoding="utf-8"))
    # голова крупно «было → стало»: одна и та же рамка кадров спереди
    for src, dst in ((q("stand_front"), q2("head_before")), (q2("stand_front"), q2("head_after"))):
        Image.open(src).convert("RGB").crop((190, 40, 710, 460)).save(dst)
    sheet = Image.new("RGB", (W, 9000), SH.BG)
    d = ImageDraw.Draw(sheet)
    SH.header(d, "Королева-мухоловка: контраст с ареной, короткие зубы, клип «съесть» (D74)",
              f"Быстрая сборка без карт · {rep['tris_total']} треугольников (≤ 8000) · суставы без щелей · "
              "карты — после «ок»")
    y = 128
    y = SH.section(d, y, "Стойка на арене «Джунгли»", "кадр игрока у входа")
    sheet.paste(V.fit(Image.open(os.path.join(Q2, "arena", "arena6_player.png")).convert("RGB"), W - 2 * M,
                      (W - 2 * M) * 9 // 16), (M, y))
    y += (W - 2 * M) * 9 // 16 + 16
    half = (W - 2 * M - 12) // 2
    sheet.paste(V.fit(Image.open(os.path.join(Q2, "arena", "arena6_approach.png")).convert("RGB"), half,
                      half * 9 // 16), (M, y))
    V.label(d, M + 12, y + half * 9 // 16 - 44, "с подхода, ближе")
    x = M + half + 12
    d.rectangle((x, y, W - M, y + half * 9 // 16), fill=SH.PANEL)
    lines = [
        "• Голова-ловушка снаружи — тёмная бутылочная зелень; мантия за головой — тёмная.",
        "• Стебель, лозы, узлы на лозах и побеги бутонов — тёмные оливково-коричневые.",
        "• Светлые сочные — только листья розетки на земле и ладони с листьями-пальцами.",
        "• Главные пятна — малиновая пасть, розовые лепестки венчика, золотая корона.",
        "• Маска лица — средняя зелень (чуть темнее прежней), глаза и брови читаются.",
        "• На светлом храме и тёмном проёме силуэт королевы не сливается с кронами.",
    ]
    ty = y + 12
    d.text((x + 18, ty), "Что изменено в цвете", font=V.font(28, True), fill=SH.ACC)
    ty += 50
    for ln in lines:
        ty = V.para(d, x + 18, ty, ln, W - M - x - 36, size=22, fill=SH.INK) + 8
    y += half * 9 // 16 + 16
    y = SH.section(d, y, "Было → стало", "палитра и зубы-реснички (вдвое короче: злая, но не страшная)")
    size = (W - 2 * M - 4 * 12) // 5
    y = SH.tiles(sheet, d, y, [(q("stand_34"), "было 3/4"), (q2("stand_34"), "стало 3/4"),
                               (q2("stand_front"), "стало спереди"), (q2("head_before"), "было: зубы"),
                               (q2("head_after"), "стало: зубы вдвое короче")], size)
    r = anim.get("eat", {})
    y = SH.section(d, y, "Клип «съесть» — 3.8 с (D74)",
                   f"стойка → стойка · кадров {r.get('frames', '?')} · ниже земли: {r.get('below_ground_frames', '?')}"
                   " · Ловибум и капсула — макеты только для раскадровки")
    fw = (W - 2 * M - 5 * 12) // 6
    for i, (t, cap) in enumerate(EAT):
        x = M + (i % 6) * (fw + 12)
        yy = y + (i // 6) * (fw + 12)
        p = os.path.join(Q2, "frames", f"eat_{i}.png")
        if os.path.exists(p):
            sheet.paste(V.fit(Image.open(p).convert("RGB"), fw, fw), (x, yy))
        V.label(d, x + 10, yy + fw - 44, f"{t:.2f} с — {cap}")
    y += 2 * (fw + 12) + 6
    att = rig.get("attachments", {})
    ev = ["• 0.60 с — «отобрала»: игра крепит Ловибум к точке LovibumHold (правая ладонь, перед листьями-пальцами). "
          "Лоза тянется на всю длину, но до игрока не достаёт — Ловибум подлетает к ладони сам.",
          "• 1.30 с — пальцы разжались: Ловибум открепить, он в пасти; 1.50 с — захлоп: Ловибум скрыть.",
          "• 1.75–2.5 с — жуёт: створки ходят, голова качается, мантия и венчик колышутся, довольный прищур.",
          "• 3.05 с — капсула этажа появляется в точке CapsuleSpawn (перед кончиками створок) и летит вперёд по её "
          "направлению; дальше — прокрутка редкости (D74).",
          f"• Точки в риге Boss6_Flytrap.rig.json → attachments: " + ", ".join(
              f"{k} (деталь {v['part']})" for k, v in att.items()) + "; клип eat — в Boss6_Flytrap.anim.json.",
          "• Боевые клипы (стойка, поворот, захлоп, хватает, урон, победа, поражение) по D74 не удалены и не "
          "дорабатываются."]
    ty = y
    for ln in ev:
        ty = V.para(d, M + 12, ty, ln, W - 2 * M - 24, size=22, fill=SH.INK) + 6
    y = ty + 14
    y = SH.section(d, y, "Сон, пробуждение, засыпание", "в новой палитре, по 8 кадров, вид 3/4")
    fw = (W - 2 * M - 7 * 8) // 8
    fh = int(fw * 520 / 420)
    for name, title in (("sleep_idle", "Сон (цикл 6.4 с)"), ("wake", "Пробуждение 2.4 с"),
                        ("fall_asleep", "Засыпание 1.6 с")):
        r = anim.get(name, {})
        d.text((M, y), f"{title} — кадров {r.get('frames', '?')}, ниже земли: {r.get('below_ground_frames', '?')}",
               font=V.font(24, True), fill=SH.INK)
        y += 36
        for k in range(8):
            p = os.path.join(Q2, "frames", f"{name}_{k}.png")
            if os.path.exists(p):
                sheet.paste(V.fit(Image.open(p).convert("RGB"), fw, fh), (M + k * (fw + 8), y))
        y += fh + 18
    sheet = sheet.crop((0, 0, W, y + M))
    sheet.save(OUT_EAT)
    return OUT_EAT, sheet.size


CHEW = [(1.5, "захлоп"), (1.62, "чавк 1"), (1.85, "кивок"), (1.97, "чавк 2"), (2.2, "кивок"), (2.32, "чавк 3"),
        (2.55, "кивок"), (2.67, "чавк 4"), (2.9, "проглотила"), (3.05, "ик!"), (3.2, "после икоты"),
        (3.45, "набрала воздух")]  # = CHEW_SHOTS в anim


def chew_sheet():
    W, M = SH.W, SH.M
    anim = json.load(open(os.path.join(Q2, "anim_report.json"), encoding="utf-8"))
    r = anim.get("eat", {})
    sheet = Image.new("RGB", (W, 3000), SH.BG)
    d = ImageDraw.Draw(sheet)
    SH.header(d, "Клип «съесть»: жевание 1.4 с — 4 «чавка» и икота",
              f"Весь клип 4.45 с · кадров {r.get('frames', '?')} · ниже земли: {r.get('below_ground_frames', '?')} · "
              "плевок капсулой — 3.75 с")
    y = 128
    fw = (W - 2 * M - 3 * 12) // 4
    for i, (t, cap) in enumerate(CHEW):
        x = M + (i % 4) * (fw + 12)
        yy = y + (i // 4) * (fw + 12)
        p = os.path.join(Q2, "frames", f"chew_{i}.png")
        if os.path.exists(p):
            sheet.paste(V.fit(Image.open(p).convert("RGB"), fw, fw), (x, yy))
        V.label(d, x + 10, yy + fw - 44, f"{t:.2f} с — {cap}")
    y += 3 * (fw + 12) + 6
    for ln in ("• «Чавк» каждые 0.35 с: створки-щёки расходятся («раздуваются»), мантия и венчик пышнеют, голова "
               "вскидывается и поворачивается — по очереди вправо и влево; «кивок» — створки сомкнуты, голова "
               "кивает вниз в такт.",
               "• Масштаба в скелете нет (как у всех боссов): раздувание — движением створок и листьев.",
               "• Икота 3.05 с: вздрогнула, голова вверх, глаза круглые, листья торчком; затем вдох и плевок 3.75 с."):
        y = V.para(d, M + 12, y, ln, W - 2 * M - 24, size=24, fill=SH.INK) + 8
    sheet = sheet.crop((0, 0, W, y + M))
    out = os.path.join(SH.REPO, "assets", "concepts", "bosses_5_10", "boss6_prod", "11_queen_chew.png")
    sheet.save(out)
    return out, sheet.size


EMO = [(1.62, "чавк — блаженство: дуги «^^», брови вверх"), (3.05, "икота — испуг: глаза настежь, брови высоко"),
       (3.45, "вдох — хитрый прищур, бровь вздёрнута"), (4.15, "финал — довольная: глаза-улыбки")]  # = EMO_SHOTS


def emo_sheet():
    W, M = SH.W, SH.M
    sheet = Image.new("RGB", (W, 3000), SH.BG)
    d = ImageDraw.Draw(sheet)
    SH.header(d, "Клип «съесть»: эмоции веками и бровями", "Карты не менялись · чавки 1.62–2.67 с · икота 3.05 с · "
              "вдох 3.45 и плевок 3.75 с · финал 4.15 с")
    y = 128
    fw = (W - 2 * M - 12) // 2
    for i, (t, cap) in enumerate(EMO):
        x = M + (i % 2) * (fw + 12)
        yy = y + (i // 2) * (fw + 12)
        p = os.path.join(Q2, "frames", f"emo_{i}.png")
        if os.path.exists(p):
            sheet.paste(V.fit(Image.open(p).convert("RGB"), fw, fw), (x, yy))
        V.label(d, x + 10, yy + fw - 44, f"{t:.2f} с — {cap}")
    y += 2 * (fw + 12) + 6
    for ln in ("• Веко — плоская пластина, поэтому «зажмурилась» — прямой шов «— —», а не дуга «^^». Дуга — это "
               "маленькая тёмная деталь на нижнем веке, то есть новая карта головы.",
               "• Глаза-гнёзда квадратные: «круглые от испуга» — это веки, убранные целиком, и брови домиком.",):
        y = V.para(d, M + 12, y, ln, W - 2 * M - 24, size=24, fill=SH.INK) + 8
    sheet = sheet.crop((0, 0, W, y + M))
    out = os.path.join(SH.REPO, "assets", "concepts", "bosses_5_10", "boss6_prod", "13_queen_emo.png")
    sheet.save(out)
    return out, sheet.size


def face_sheet():
    W, M = SH.W, SH.M
    qm = os.path.join(SH.REPO, "assets", "concepts", "bosses_5_10", "boss6_prod", "queen_maps")
    sheet = Image.new("RGB", (W, 5200), SH.BG)
    d = ImageDraw.Draw(sheet)
    SH.header(d, "Королева: голова — кант створок и дуги «^^»", "С картами (карты не менялись) · перезалив только меша "
              "головы — после «ок»")
    y = 128
    pic = (W - 2 * M - 12) // 2
    y = SH.section(d, y, "Лицо крупно, с картами", "пасть сомкнута · стойка · блаженство · сон")
    y = SH.tiles(sheet, d, y, [(os.path.join(qm, "face_closed.png"), "пасть сомкнута: кант тёмно-зелёный"),
                               (os.path.join(qm, "face_stand.png"), "стойка: малиновое — только внутри")], pic)
    y = SH.tiles(sheet, d, y, [(os.path.join(qm, "face_bliss.png"), "блаженство: дуги «^^» на нижнем веке"),
                               (os.path.join(qm, "face_sleep.png"), "сон: «— —» по краю верхнего века")], pic)
    y = SH.section(d, y, "Клип «съесть»: эмоции", "чавк · икота · вдох · финал")
    y = SH.tiles(sheet, d, y, [(os.path.join(Q2, "frames", f"emo_{i}.png"), f"{t:.2f} с — {c}")
                               for i, (t, c) in enumerate(EMO)][:2], pic)
    y = SH.tiles(sheet, d, y, [(os.path.join(Q2, "frames", f"emo_{i}.png"), f"{t:.2f} с — {c}")
                               for i, (t, c) in enumerate(EMO)][2:], pic)
    for ln in ("• Кант створок берёт цвет век с той же карты (перенос развёртки), малиновое нутро и реснички-зубчики "
               "на месте; ресницы и румянец не тронуты.",
               "• Дуга и полоса сна — новые маленькие детали с цветом бровей с той же карты. В блаженстве верхнее веко "
               "уходит вверх, нижнее с дугой поднимается до верха глаза; во сне — наоборот."):
        y = V.para(d, M + 12, y, ln, W - 2 * M - 24, size=24, fill=SH.INK) + 8
    sheet = sheet.crop((0, 0, W, y + M))
    out = os.path.join(SH.REPO, "assets", "concepts", "bosses_5_10", "boss6_prod", "14_queen_face.png")
    sheet.save(out)
    return out, sheet.size


def maps_sheet():
    W, M = SH.W, SH.M
    tex = os.path.join(SH.REPO, "assets", "textures", "art")
    qm = os.path.join(SH.REPO, "assets", "concepts", "bosses_5_10", "boss6_prod", "queen_maps")
    rep = json.load(open(os.path.join(qm, "report.json"), encoding="utf-8"))
    sheet = Image.new("RGB", (W, 4000), SH.BG)
    d = ImageDraw.Draw(sheet)
    SH.header(d, "Королева-мухоловка: карты — на просмотр до загрузки",
              f"Три карты (голова, тело, лозы) · {rep['tris_total']} треугольников · ничего не загружено; загрузка — "
              "после «ок»")
    y = 128
    y = SH.section(d, y, "Модель с картами", "спереди · 3/4 · сбоку · сзади")
    size = (W - 2 * M - 3 * 12) // 4
    y = SH.tiles(sheet, d, y, [(os.path.join(qm, f"stand_{v}.png"), c) for v, c in
                               (("front", "спереди"), ("34", "3/4"), ("side", "сбоку"), ("back", "сзади"))], size)
    pic = (W - 2 * M - 2 * 12) // 3
    for m, title in (("Head", "Голова: ловушка, маска, веки, брови, корона, венчик"),
                     ("Body", "Тело: клубень, розетка, стебель, мантия, бутоны"),
                     ("Limbs", "Лозы, ладони и листья-пальцы")):
        y = SH.section(d, y, title, f"Boss6Flytrap{m}")
        items = []
        for kind, cap in (("color", "цвет"), ("normal", "нормали")):
            p = os.path.join(tex, f"Boss6Flytrap{m}_{kind}.png")
            if os.path.exists(p):
                items.append((p, f"{cap} {Image.open(p).size[0]}×{Image.open(p).size[1]}"))
        y = SH.tiles(sheet, d, y, items, pic)
    sheet = sheet.crop((0, 0, W, y + M))
    out = os.path.join(SH.REPO, "assets", "concepts", "bosses_5_10", "boss6_prod", "12_queen_maps.png")
    sheet.save(out)
    return out, sheet.size


if __name__ == "__main__":
    mode = sys.argv[1:2]
    print(eat_sheet() if mode == ["eat"] else chew_sheet() if mode == ["chew"] else maps_sheet() if mode == ["maps"]
          else emo_sheet() if mode == ["emo"] else face_sheet() if mode == ["face"]
          else main())
