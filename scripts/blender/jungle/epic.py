"""Коллекция джунглей босса 6 — Epic (каталог docs/BOSS6_CATALOG.md, утверждён 2026-11-25).
Каждое существо — функция, возвращающая Art с подвижными частями (part), позой и кадрами; список ITEMS — в порядке
каталога. Признаки вида, эмоция и цвета — из каталога; правила анатомии D64 — в jungle/kit.py и anatomy_kit.
"""

import math
import os
import sys

from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jungle_kit import *  # noqa: E402,F401,F403


_OWN = []  # Муравей и Ягуар — в своих модулях (ant_strongman.py, flower_jaguar.py)

# порядок каталога; новые существа — по модулю на существо (jungle/<snake_case>.py с ITEM), см. jungle_kit.collect
ORDER = "FlowerJaguar AntStrongman RhinoBeetle FrillLizard DinoCassowary GreedyPitcher".split()
ITEMS = collect(ORDER, _OWN)
