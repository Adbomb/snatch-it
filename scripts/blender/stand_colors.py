"""Цвета подставок существ и листов концептов из одного источника — UITokens.Rarity (D71).

Читает src/shared/Config/UITokens.luau (таблица `UITokens.Rarity = { Common = gradient("верх", "низ"), … }`) и отдаёт
словарь RARITY = {"Common": ("D9D7E3", "ADA6B4"), …} — (светлый верх, насыщенный низ), как в интерфейсе.
Подставка: тело — насыщенный низ, кайма — светлый верх; тёмный цоколь — низ, затемнённый shade().
Вписанных вручную копий цветов редкости в скриптах больше нет: creature_kit и листы берут их отсюда.
Зависимостей нет (обычный Python, работает и в Blender, и в PIL-скриптах листов).
"""

import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOKENS = os.path.join(REPO, "src", "shared", "Config", "UITokens.luau")


def _read():
    text = open(TOKENS, encoding="utf-8").read()
    block = re.search(r"UITokens\.Rarity\s*=\s*\{(.*?)\n\}", text, re.S)
    if not block:
        raise RuntimeError("UITokens.Rarity не найдена в " + TOKENS)
    out = {}
    for name, top, bottom in re.findall(r"(\w+)\s*=\s*gradient\(\"([0-9A-Fa-f]{6})\",\s*\"([0-9A-Fa-f]{6})\"\)",
                                        block.group(1)):
        out[name] = (top.upper(), bottom.upper())
    for need in ("Common", "Rare", "Epic", "Legendary"):
        if need not in out:
            raise RuntimeError("в UITokens.Rarity нет " + need)
    return out


RARITY = _read()


def shade(code, k):
    """Цвет code, умноженный на k (k < 1 — темнее, k > 1 — светлее, до белого)."""
    r, g, b = (int(code[i:i + 2], 16) for i in (0, 2, 4))
    return "".join(f"{max(0, min(255, round(c * k))):02X}" for c in (r, g, b))


def rgb(code):
    return tuple(int(code[i:i + 2], 16) for i in (0, 2, 4))


def stand(rarity):
    """Цвета подставки редкости: body (насыщенный), rim (светлый), base (тёмный цоколь)."""
    top, bottom = RARITY[rarity]
    return {"body": bottom, "rim": top, "base": shade(bottom, 0.72)}


if __name__ == "__main__":
    for k, v in RARITY.items():
        print(k, v, stand(k) if k in ("Common", "Rare", "Epic", "Legendary", "Secret") else "")
