"""Лист «было → стало» по существам джунглей, которые владелец вернул на переделку после аудита анатомии (2026-11-26).

На существо — ряд: «было» (3/4 и спереди, кадры до правки из boss6_prod/before_redo/) и «стало» (3/4, спереди, лицо —
свежая быстрая сборка из boss6_prod/creatures/), подпись — что сделано, и числа отчёта сборки.
Запуск из корня: python scripts/boss6_redo_sheet.py → assets/concepts/bosses_5_10/boss6_prod/6_redo.png (вне git).
Зависит от Pillow, scripts/blender/boss6/sheet.py, scripts/boss6_anatomy_audit.py (отчёты сборки).
"""

import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "blender", "boss6"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import sheet as SH  # noqa: E402
import boss6_anatomy_audit as AU  # noqa: E402

V = SH.V
PROD = os.path.join(ROOT, "assets", "concepts", "bosses_5_10", "boss6_prod")
BEFORE = os.path.join(PROD, "before_redo")
AFTER = os.path.join(PROD, "creatures")

# (id, №, имя, что сделано) — в порядке списка владельца
REDO = [
    ("CocoonFruitBat", 10, "Крылан-кокон",
     "П-образной рамы нет: живая кривая ветка из коряги с кроной листьев и плодом-манго (не «виселица»)."),
    ("SnailTurtle", 4, "Черепаха-улитка",
     "Кожа оливковая с тёмными щитками и чешуёй, круглая голова с клювом, короткая шея; рожки мягкие и изогнуты "
     "вперёд (не «жираф»); розовая раковина прежняя."),
    ("ParadiseDancer", 29, "Птица-танцор",
     "На чёрном бархатном плаще с синим отливом по краю — светящийся бирюзовый «смайлик»: улыбка-полумесяц и два "
     "«глаза»; птица крупнее в 1.3 раза."),
    ("LightningEel", 30, "Угорь-молния",
     "Зигзаг светится голубой неоновой каймой по обоим краям, искры почти вдвое крупнее, разряд на каждом звене; "
     "голова — широкий округлый шар со светлым подбородком."),
    ("ArchBoto", 14, "Дельфин-арка",
     "Голова смотрит на игрока, не запрокинута; круглый лоб-«дыня» над клювом, круглые глаза со зрачками, "
     "широкая улыбка вдоль клюва."),
    ("BigEyeTarsier", 6, "Долгопят-глазастик",
     "Стебель зелёный с узлом и парой листьев; пальцы цвета кожи (не розовые) — не читается как червяк."),
    ("CrocLanternfly", 15, "Фонарница-крокодил",
     "«Крокодилья морда» зелёно-бурая: бурые пятна, крупные ноздри-бугорки, ряд нарисованных сомкнутых "
     "зубов-полосок вдоль пасти."),
    ("BeeHummingbird", 5, "Колибри-шмель", "Клюв 0.1–0.14 стада (был 0.07), лапки толще и вынесены из-под брюшка."),
]


def img(folder, item_id, view):
    p = os.path.join(folder, f"{item_id}_{view}.png")
    return Image.open(p).convert("RGB") if os.path.exists(p) else Image.new("RGB", (10, 10), (60, 30, 30))


def main():
    pic, gap = 330, 10
    W = SH.W
    row_h = pic + 120
    sheet = Image.new("RGB", (W, 130 + len(REDO) * (row_h + 14) + 20), SH.BG)
    d = ImageDraw.Draw(sheet)
    SH.header(d, "Джунгли: 8 существ после правок владельца — было → стало",
              "Быстрая сборка без карт (2026-11-26). Слева «было» (3/4, спереди), справа «стало» (3/4, спереди, лицо).")
    y = 130
    for item_id, n, name, what in REDO:
        x = SH.M
        for view, cap in (("hero", "было 3/4"), ("front", "было спереди")):
            sheet.paste(V.fit(img(BEFORE, item_id, view), pic, pic), (x, y))
            V.label(d, x + 8, y + pic - 40, cap)
            x += pic + gap
        d.rectangle((x + 4, y + pic // 2 - 6, x + 36, y + pic // 2 + 6), fill=SH.ACC)
        d.polygon([(x + 36, y + pic // 2 - 18), (x + 56, y + pic // 2), (x + 36, y + pic // 2 + 18)], fill=SH.ACC)
        x += 66
        for view, cap in (("hero", "стало 3/4"), ("front", "стало спереди"), ("face", "стало лицо")):
            sheet.paste(V.fit(img(AFTER, item_id, view), pic, pic), (x, y))
            V.label(d, x + 8, y + pic - 40, cap)
            x += pic + gap
        rep = AU.report(item_id)
        size = rep.get("size_no_stand") or rep.get("size_without_stand_xyz")
        nums = f"треугольников без подставки {rep.get('tris_without_stand')} (≤ 3000) · суставы: " + (
            "без щелей" if not rep.get("joint_issues") else f"{len(rep['joint_issues'])} замечаний")
        if size:
            nums += " · габарит " + " × ".join(f"{v:.2f}" for v in size)
        ty = V.para(d, SH.M, y + pic + 8, f"№{n} {name} — " + what, W - 2 * SH.M, size=22, fill=SH.INK, bold=True)
        V.para(d, SH.M, ty + 2, nums, W - 2 * SH.M, size=18, fill=SH.DIM)
        y += row_h + 14
    sheet = sheet.crop((0, 0, W, y + 10))
    out = os.path.join(PROD, "6_redo.png")
    sheet.save(out)
    return out


if __name__ == "__main__":
    print(main())
