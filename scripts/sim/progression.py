"""Симулятор долгой прогрессии (D29).

Читает числа баланса из src/shared/Config/Progression.luau (тот же файл берёт игра), прогоняет типичного игрока
и печатает таблицу «день → сила, перерождения, зона, монеты, уровень музея».

  python scripts/sim/progression.py           — таблица по текущим числам
  python scripts/sim/progression.py --tune    — подобрать силы боссов и цены музея под цели и записать в файл

Здесь только модель поведения игрока (сколько играет, сколько идёт до зоны). Числа игры — в Progression.luau.
"""

import argparse
import math
import random
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "src" / "shared" / "Config" / "Progression.luau"

# --- Модель игрока (не баланс игры) ---
SESSION = 5400  # секунд в игре за день (1,5 ч)
TRAIN_SHARE = 0.6  # доля времени на лучшем круге, остальное — походы в зоны и музей
DAYS = 90
STEP = 5  # шаг тренировки, с
ZONE_NEAR = 120  # стадов от музея до входа в зону 1
ZONE_LEN = 60  # длина зоны вдоль коридора
ZONE_INSIDE = 30  # от входа зоны до предмета
FIGHT = 5  # автобой, с
HANDLE = 6  # подбор и выставление, с
LOAD = 0.9  # средний множитель скорости с грузом (Light 1 / Medium 0.9 / Heavy 0.8)
STORAGE = 10  # вместимость хранилища
MUSEUM_WAIT = 0.5  # не перерождаться, если до следующего уровня музея копить меньше стольких дней
PUSH_DAYS = 0.5  # не перерождаться, если до следующего босса тренироваться меньше стольких дней
FINAL_REBIRTH_DAYS = 1.0  # после зоны 10: перерождаться, если вернуть силу босса 10 можно за столько дней

RARITIES = ["Common", "Uncommon", "Rare", "Legendary", "Secret"]
VARIANTS = ["Normal", "Golden", "Giant", "Rainbow"]

# Цели D29 в днях игры (1 день = SESSION секунд).
ZONE_TARGETS = {2: 4 / 90, 3: 30 / 90, 4: 1.0, 5: 3.5, 6: 7, 7: 10.5, 8: 24.5, 9: 45, 10: 75}
MUSEUM_TARGETS = {2: 0.1, 3: 0.5, 4: 1.5, 5: 3, 6: 6, 7: 11, 8: 20, 9: 35, 10: 60}


# --- Чтение Luau-таблицы ---
def load_config(path=CONFIG):
	src = re.sub(r"--[^\n]*", "", path.read_text(encoding="utf-8"))
	tokens = re.findall(r"[A-Za-z_]\w*|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|\"[^\"]*\"|[{}=,\[\]]", src)
	pos = tokens.index("return") + 1

	def value():
		nonlocal pos
		tok = tokens[pos]
		pos += 1
		if tok == "{":
			items, keys = [], []
			while tokens[pos] != "}":
				if tokens[pos + 1] == "=":
					keys.append(tokens[pos])
					pos += 2
				items.append(value())
				if tokens[pos] == ",":
					pos += 1
			pos += 1
			return dict(zip(keys, items)) if keys else items
		if tok.startswith('"'):
			return tok[1:-1]
		return float(tok) if re.match(r"\d", tok) else tok

	return value()


def save_numbers(bosses, prices, path=CONFIG):
	text = path.read_text(encoding="utf-8")
	fmt = lambda xs: ", ".join(str(int(x)) for x in xs)
	text = re.sub(r"Bosses = \{[^}]*\}", "Bosses = { " + fmt(bosses) + " }", text)
	text = re.sub(r"Prices = \{[^}]*\}", "Prices = { " + fmt(prices) + " }", text)
	path.write_text(text, encoding="utf-8", newline="\n")


def nice(x):
	"""Округление до двух значащих цифр."""
	if x <= 0:
		return 0
	e = 10 ** (math.floor(math.log10(x)) - 1)
	return round(x / e) * e


def short(x):
	"""Как в игре: 1.2K / 3.4M / 5.6B / 7.8T / 9.1Qa."""
	for div, suf in ((1e15, "Qa"), (1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
		if x >= div:
			return f"{x / div:.1f}{suf}"
	return f"{x:.0f}"


# --- Игрок ---
class Player:
	def __init__(self, cfg, rng):
		self.cfg, self.rng = cfg, rng
		self.t = 0.0
		self.S = 0.0
		self.R = 0
		self.coins = 0.0
		self.earned = 0.0
		self.level = 1
		self.items = []  # доход каждого предмета в музее и хранилище, по убыванию
		self.found = {}  # (редкость, вид) → номера найденных предметов
		self.catalog_bonus = 0.0
		self.max_zone = 1
		self.events = {}  # ("zone", k) / ("museum", k) / ("rebirth", n) / ("secret", 1) → время
		self.raids = 0

	# Сила, скорость, зоны
	def circle_rate(self, S=None, R=None):
		S = self.S if S is None else S
		R = self.R if R is None else R
		rate = 0
		for c in self.cfg["Circles"]:
			if S >= c["strength"] and R >= c["rebirths"]:
				rate = max(rate, c["rate"])
		return rate

	def gain(self, R=None):
		R = self.R if R is None else R
		return 1 + self.cfg["Rebirth"]["strengthBonus"] * R

	def time_to(self, S, target, R):
		"""Секунды тренировки, чтобы дойти от силы S до target при R перерождениях."""
		t = 0.0
		while S < target:
			rate = self.circle_rate(S, R) * self.gain(R)
			nxt = [c["strength"] for c in self.cfg["Circles"] if S < c["strength"] < target and R >= c["rebirths"]]
			stop = min(nxt) if nxt else target
			t += (stop - S) / rate
			S = stop
		return t

	def speed(self):
		sp = self.cfg["Speed"]
		k = min(1.0, math.log10(1 + self.S) / math.log10(1 + sp["cap"]))
		return sp["min"] + (sp["max"] - sp["min"]) * k

	def zone(self):
		z = 1
		for k, b in enumerate(self.cfg["Bosses"], start=1):
			if self.S >= b:
				z = k
		return z

	# Доход
	def slots(self):
		return int(self.cfg["Museum"]["Slots"][self.level - 1])

	def income(self):
		shown = sum(self.items[: self.slots()])
		return shown * (1 + self.cfg["Rebirth"]["incomeBonus"] * self.R) * (1 + self.catalog_bonus)

	def earn(self, dt):
		got = self.income() * dt
		self.coins += got
		self.earned += got

	# Добыча
	def drop(self, z):
		cfg = self.cfg
		f = (z - 1) / 9
		weights = []
		for r in RARITIES:
			w = cfg["RarityFirst"][r] + (cfg["RarityLast"][r] - cfg["RarityFirst"][r]) * f
			if r == "Secret" and z < cfg["SecretFromZone"]:
				w = 0
			weights.append(w)
		rarity = self.rng.choices(RARITIES, weights)[0]
		roll, variant, acc = self.rng.random(), "Normal", 0.0
		for v in ("Rainbow", "Giant", "Golden"):
			acc += cfg["Modifiers"][v]["chance"]
			if roll < acc:
				variant = v
				break
		item = self.rng.randrange(int(cfg["ItemCounts"][rarity]))
		mult = cfg["Modifiers"][variant]["income"] if variant != "Normal" else 1
		value = cfg["Income"][rarity] * mult

		key = (rarity, variant)
		got = self.found.setdefault(key, set())
		if item not in got:
			got.add(item)
			if len(got) == cfg["ItemCounts"][rarity]:
				self.catalog_bonus += cfg["Catalog"]["Rarity"][rarity] * cfg["Catalog"]["Variant"][variant]
		if rarity == "Secret":
			self.events.setdefault(("secret", 1), self.t)

		self.items.append(value)
		self.items.sort(reverse=True)
		del self.items[self.slots() + STORAGE :]
		self.raids += 1

	# Тренировка
	def train(self, dt):
		while dt > 0:
			step = min(STEP, dt)
			self.S += self.circle_rate() * self.gain() * step
			self.earn(step)
			self.t += step
			dt -= step
			z = self.zone()
			if z > self.max_zone:
				for k in range(self.max_zone + 1, z + 1):
					self.events[("zone", k)] = self.t
				self.max_zone = z

	# Решения: музей и перерождение
	def decide(self):
		cfg = self.cfg
		prices = cfg["Museum"]["Prices"]
		while self.level < 10 and self.coins >= prices[self.level - 1]:
			self.coins -= prices[self.level - 1]
			self.level += 1
			self.events[("museum", self.level)] = self.t

		rb = cfg["Rebirth"]
		need_s = rb["strength"] * rb["strengthGrowth"] ** self.R
		need_c = rb["coins"] * rb["coinGrowth"] ** self.R
		if self.S < need_s or self.coins < need_c:
			return
		if self.level < 10:
			left = prices[self.level - 1] - self.coins
			if left > 0 and left <= self.income() * SESSION * MUSEUM_WAIT:
				return
		bosses = cfg["Bosses"]
		day = SESSION * TRAIN_SHARE
		if self.max_zone < 10:
			if self.time_to(self.S, bosses[self.max_zone], self.R) <= day * PUSH_DAYS:
				return
		elif self.time_to(0, bosses[9], self.R + 1) > day * FINAL_REBIRTH_DAYS:
			return
		self.R += 1
		self.S = 0.0
		self.coins = 0.0
		self.events[("rebirth", self.R)] = self.t

	def cycle(self):
		z = self.zone()
		dist = ZONE_NEAR + ZONE_LEN * (z - 1) + ZONE_INSIDE
		sp = self.speed()
		raid = dist / sp + dist / (sp * LOAD) + FIGHT + HANDLE
		self.earn(raid)
		self.t += raid
		self.drop(z)
		self.train(raid * TRAIN_SHARE / (1 - TRAIN_SHARE))
		self.decide()


def run(cfg, seed=1, days=DAYS, until=None, snapshots=None):
	"""Прогон игрока. until(p) → True останавливает раньше. snapshots: список дней для таблицы."""
	p = Player(cfg, random.Random(seed))
	rows, want = [], sorted(snapshots or [])
	end = days * SESSION
	while p.t < end:
		p.cycle()
		while want and p.t >= want[0] * SESSION:
			rows.append((want.pop(0), p.S, p.R, p.zone(), p.max_zone, p.coins, p.level, p.income(), p.catalog_bonus))
		if until and until(p):
			break
	return p, rows


# --- Подбор чисел ---
def event_day(cfg, key, seed, limit):
	p, _ = run(cfg, seed, days=limit, until=lambda p: key in p.events)
	return p.events.get(key, math.inf) / SESSION


def tune_value(cfg, setter, key, target, lo, hi, seeds=(1,)):
	"""Двоичный поиск по логарифму: значение, при котором событие key случается в день target (медиана сидов)."""
	limit = target * 2 + 1
	for _ in range(22):
		mid = math.sqrt(lo * hi)
		setter(mid)
		day = statistics.median(event_day(cfg, key, s, limit) for s in seeds)
		if day < target:
			lo = mid
		else:
			hi = mid
	setter(nice(math.sqrt(lo * hi)))


def tune(cfg, passes=2):
	bosses, prices = cfg["Bosses"], cfg["Museum"]["Prices"]
	for n in range(passes):
		for k in range(2, 11):

			def set_boss(v, k=k):
				bosses[k - 1] = v

			lo = max(bosses[k - 2] * 1.05, 1)
			tune_value(cfg, set_boss, ("zone", k), ZONE_TARGETS[k], lo, max(lo * 10, 9e15))
		for k in range(2, 11):

			def set_price(v, k=k):
				prices[k - 2] = v

			lo = prices[k - 3] * 1.05 if k > 2 else 10
			tune_value(cfg, set_price, ("museum", k), MUSEUM_TARGETS[k], lo, 9e15)
		print(f"проход {n + 1}: боссы {[short(b) for b in bosses]}")
		print(f"          музей {[short(x) for x in prices]}")


# --- Отчёт ---
def report(cfg, seeds=200):
	snaps = [1, 2, 3, 4, 5, 7, 10, 14, 21, 28, 35, 45, 60, 75, 90]
	_, rows = run(cfg, seed=1, snapshots=snaps)
	print("\nТипичный игрок (сид 1), конец дня:")
	print("| день | сила | перерожд. | зона (макс.) | монеты | музей | доход/с | каталог |")
	print("|---|---|---|---|---|---|---|---|")
	for d, S, R, z, mz, coins, lvl, inc, cat in rows:
		print(f"| {d} | {short(S)} | {R} | {z} ({mz}) | {short(coins)} | {lvl} | {short(inc)} | +{cat * 100:.0f}% |")

	runs = [run(cfg, seed=s)[0] for s in range(seeds)]

	def stat(key):
		days = sorted(p.events.get(key, math.inf) / SESSION for p in runs)
		q = lambda f: days[int(f * (len(days) - 1))]
		fmt = lambda d: "—" if d == math.inf else (f"{d * 90:.0f} мин" if d < 1 else f"{d:.1f}")
		return fmt(q(0.5)), fmt(q(0.1)), fmt(q(0.9))

	print(f"\nСобытия, день игры (медиана и 10–90 % по {seeds} игрокам):")
	print("| событие | медиана | 10 % | 90 % | цель |")
	print("|---|---|---|---|---|")
	for k in range(2, 11):
		m, a, b = stat(("zone", k))
		print(f"| зона {k} | {m} | {a} | {b} | {ZONE_TARGETS[k]:.1f} |")
	for k in range(2, 11):
		m, a, b = stat(("museum", k))
		print(f"| музей {k} | {m} | {a} | {b} | {MUSEUM_TARGETS[k]:.1f} |")
	for k in (1, 3, 6, 9, 12):
		m, a, b = stat(("rebirth", k))
		print(f"| перерождение {k} | {m} | {a} | {b} | |")
	m, a, b = stat(("secret", 1))
	got = sum(("secret", 1) in p.events for p in runs)
	print(f"| первый Secret | {m} | {a} | {b} | ~30 | ({got}/{seeds} получили за {DAYS} дней)")
	print(f"\nПредметов в день (медиана): {statistics.median(p.raids for p in runs) / DAYS:.0f}")
	peak = max(max(p.earned, p.S) for p in runs)
	print(f"Максимум чисел: {short(peak)} (предел 9e15)")


def main():
	sys.stdout.reconfigure(encoding="utf-8")
	ap = argparse.ArgumentParser()
	ap.add_argument("--tune", action="store_true")
	ap.add_argument("--seeds", type=int, default=200)
	args = ap.parse_args()
	cfg = load_config()
	if args.tune:
		tune(cfg)
		save_numbers(cfg["Bosses"], cfg["Museum"]["Prices"])
	report(cfg, args.seeds)


if __name__ == "__main__":
	main()
