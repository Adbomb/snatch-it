"""D48-C, фаза 1 — раскладка музея до 20 мест: единый источник правды для Blender-кадров, листов и (на фазе 3)
игрового конфига. Без bpy: можно импортировать где угодно, `python d48c_layout.py <файл.json>` пишет JSON.

Координаты — оси участка (центр участка на уровне пола зала, вход −Z, x+ — левая рука входящего). Здание: главный
зал — прежний контур D36 (36 × 33.4 + портик), хранилище и павильон — D48 v2 без изменений. Новое:
  • 8 ниш главного зала (по 4 на боковую стену, шаг 6.1) — места 1–8;
  • две боковые галереи в объёме крыльев D36 (x 18…29), продлённые вперёд вдоль портика до z = −19 (перед ними —
    поле качалки и гигантская гантель), по 6 мест у наружной стены — места 9–20; вход — только аркой из входного
    зала (не с улицы); вдоль наружной стены — клумба (у крайних участков закрывает щель до обрыва).
Открытие мест: D37 — уровень × 2 (место n открывается на уровне ⌈n/2⌉). Код сейчас даёт 6 мест на любом уровне —
предложение совместимой миграции: max(6, 2 × уровень). Галереи строятся с уровня, на котором открываются места 9–10.
"""

import json
import math
import sys

# ── Главный зал и хранилище (как D48 v2) ────────────────────────────────────────────────────────────────────────
HW, FZ, BZ, T = 18.0, -12.7, 20.7, 1.4
IX, IZ0, IZ1 = HW - T, FZ + T, BZ - T  # −16.6…16.6, −11.3…19.3
CEIL, DOOR, DOORH = 16.0, 6.0, 10.0
PV_X, PV_Z0, PV_Z1 = 4.4, 2.4, 11.6  # павильон над лестницей
ST0, STW = 3.0, 2.6

# ── Места ───────────────────────────────────────────────────────────────────────────────────────────────────────
TOP = 5.0  # верх постамента 5 × 5 на высоте 3 (GameConfig.Museum.ShowcaseSize не меняется)
BASE = 5.4  # основание постамента
NICHE_Z = (-2.0, 4.1, 10.2, 16.3)  # шаг 6.1: основания −4.7…0.7, 1.4…6.8, 7.5…12.9, 13.6…19.0
NICHE_D = 3.2  # центр постамента ниши — в 3.2 от стены: x ±13.4, основание 10.7…16.1
PIL_Z = (-5.05, 1.05, 7.15, 13.25)  # пилястры перед каждой нишей (последняя ниша упирается в заднюю стену)

GAL_IN, GAL_OUT, GAL_Z0, GAL_Z1, GAL_H = 18.0, 29.0, -19.0, 20.7, 10.4  # галерея: от стены зала до наружной стены
# фасад галереи — z −19 (не −22): гигантская гантель участка стоит до z −23.1, поле качалки — до −26 (проверка мира)
GAL_IX = GAL_OUT - T  # 27.6 — внутренняя грань наружной стены
GAL_IZ0, GAL_IZ1 = GAL_Z0 + T, GAL_Z1 - T  # −17.6…19.3
GAL_D = 2.9  # центр постамента галереи — в 2.9 от наружной стены: x ±24.7, основание 22.0…27.4
GAL_Z = (-8.45, -2.35, -14.55, 3.75, 9.85, 15.95)  # шаг 6.1, как у ниш; порядок открытия: от арки — к краям
GAL_EAVE = 29.4  # карниз галереи снаружи не дальше x 29.4
PLANTER = (29.0, 31.4, 1.6)  # клумба вдоль наружной стены галереи: x 29…31.4, высота; у крайних участков закрывает
# щель до обрыва (кромка обрыва — x 31.6 от центра участка 1 и 5), между участками остаётся проход ≈ 12 ст.
ARCH_Z0, ARCH_Z1, ARCH_H = -10.8, -6.0, 8.0  # арка в боковой стене входного зала

CHEST = {"center": (-9.0, -9.7), "size": (4.0, 3.0, 3.0), "face": (0, 0, 1)}  # было x −12: освобождает арку
STAND = {"center": (9.0, -9.6)}
LASERS = {"Entrance": {"z": -8.6, "length": 12.0, "y": 2.4}, "Gallery": {"z": -6.4, "length": 9.2, "y": 2.4}}


def places():
    """20 мест: номер, центр верха постамента (y = 3), куда смотрит табличка, зона, уровень открытия (D37)."""
    out = []
    n = 0
    for z in NICHE_Z:
        for sx in (1, -1):
            n += 1
            out.append({"slot": n, "zone": "hall", "center": [sx * (IX - NICHE_D), 3.0, z], "face": [-sx, 0, 0]})
    for z in GAL_Z:
        for sx in (1, -1):
            n += 1
            out.append({"slot": n, "zone": "gallery", "side": sx, "center": [sx * (GAL_IX - GAL_D), 3.0, z],
                        "face": [-sx, 0, 0]})
    for p in out:
        p["unlock_d37"] = math.ceil(p["slot"] / 2)
        p["unlock_compat"] = 1 if p["slot"] <= 6 else math.ceil(p["slot"] / 2)
    return out


def slots_d37(level):
    return 2 * level


def slots_compat(level):
    return max(6, 2 * level)


GALLERY_LEVEL = 5  # места 9–10 → галереи и арки строятся с уровня 5 (в обеих схемах)


# ── Зоны защиты (D46: ловушка, робот, капкан — свободно на допустимом полу; дверь — вход; лазер — 2 метки) ───────
def defense_zones(level):
    """Прямоугольники пола (x0, x1, z0, z1): allowed — все три свободных устройства; forbidden — нельзя ничего.
    Итоговая проверка в игре — DefenseRules (ShowcaseClear 4.6 от центра постамента, DeviceGap 4)."""
    allowed = [
        (-10.2, -5.0, -4.5, 18.8), (5.0, 10.2, -4.5, 18.8),  # боковые проходы вдоль павильона
        (-4.6, 4.6, 12.2, 18.8),  # задний проход за павильоном
    ]
    forbidden = [
        (-3.6, 3.6, IZ0, PV_Z0), (-4.8, 4.8, PV_Z0 - 0.4, PV_Z1 + 0.4),  # дорожка и павильон
        (4.4, 5.6, -5.0, 2.6),  # открытая сейфовая дверь
        (-7.5, 7.5, IZ0, -5.0),  # входная группа: дверь, лазеры, путь к аркам
    ]
    for p in places():
        if p["zone"] == "hall":
            x, _, z = p["center"]
            forbidden.append((x - 4.6, x + 4.6, z - 4.6, z + 4.6))
    if level >= GALLERY_LEVEL:
        for sx in (-1, 1):
            forbidden.append(tuple(sorted((sx * 10.6, sx * IX))) + (IZ0, -5.0))  # подход к арке
            forbidden.append(tuple(sorted((sx * GAL_IN, sx * GAL_IX))) + (GAL_IZ0, GAL_IZ1))  # галерея: проход 4 ст.
    return {"allowed": allowed, "forbidden": forbidden}


def layout():
    return {
        "units": "studs, plot axes (y up, entrance −Z)",
        "hall": {"half_width": HW, "front": FZ, "back": BZ, "ceiling": CEIL, "door": [2 * DOOR, DOORH]},
        "pavilion": {"half_x": PV_X, "z0": PV_Z0, "z1": PV_Z1}, "stair": {"top_z": ST0, "half_width": STW},
        "gallery": {"x_in": GAL_IN, "x_out": GAL_OUT, "z0": GAL_Z0, "z1": GAL_Z1, "height": GAL_H,
                    "eave": GAL_EAVE, "planter": list(PLANTER), "arch": [ARCH_Z0, ARCH_Z1, ARCH_H],
                    "level": GALLERY_LEVEL},
        "showcase": {"top": TOP, "base": BASE, "height": 3.0},
        "places": places(), "chest": CHEST, "stand": STAND, "lasers": LASERS,
        "slots": {"d37": [slots_d37(level) for level in range(1, 11)],
                  "compat": [slots_compat(level) for level in range(1, 11)]},
        "defense": {str(level): defense_zones(level) for level in (1, 10)},
    }


if __name__ == "__main__":
    data = layout()
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
    for p in data["places"]:
        print(p["slot"], p["zone"], p["center"], "D37 ур.", p["unlock_d37"], "совм. ур.", p["unlock_compat"])
