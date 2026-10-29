"""Симулятор долгой прогрессии (D29–D31; перерождений нет, сила = гантель × (1 + сила музея)).

Читает числа баланса из src/shared/Config/Progression.luau (тот же файл берёт игра), прогоняет типичного игрока
и печатает таблицы «день → сила, перерождения, зона, монеты, музей, гантель» и дни событий.

  python scripts/sim/progression.py                 — таблицы по текущим числам
  python scripts/sim/progression.py --tune          — подобрать боссов, цены музея и гантели и записать в файл
  python scripts/sim/progression.py --tune --ratio 4 --dry — то же с множителем гантели ×4, без записи

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
TRAIN_SHARE = 0.6  # доля времени на тренировке, остальное — походы в зоны и музей
DAYS = 90
STEP = 5  # шаг тренировки, с
ZONE_NEAR = 120  # стадов от музея до входа в зону 1
ZONE_LEN = 60  # длина зоны вдоль коридора
ZONE_INSIDE = 30  # от входа зоны до предмета
FIGHT = 5  # автобой, с
HANDLE = 6  # подбор и выставление, с
LOAD = 0.9  # средний множитель скорости с грузом (Light 1 / Medium 0.9 / Heavy 0.8)
STORAGE = 10  # вместимость хранилища

RARITIES = ["Common", "Uncommon", "Rare", "Legendary", "Secret"]
VARIANTS = ["Normal", "Golden", "Giant", "Rainbow"]

# Цели в днях игры (1 день = SESSION секунд).
ZONE_TARGETS = {2: 4 / 90, 3: 30 / 90, 4: 1.0, 5: 3.5, 6: 7, 7: 10.5, 8: 24.5, 9: 45, 10: 75}
MUSEUM_TARGETS = {2: 0.15, 3: 1.0, 4: 2.5, 5: 5, 6: 9.5, 7: 15, 8: 24, 9: 37, 10: 58}  # между уровнями гантели
DUMBBELL_TARGETS = {2: 0.5, 3: 1.5, 4: 3.5, 5: 7, 6: 12, 7: 19, 8: 30, 9: 45, 10: 70}
SECRET_TARGET = (30, 40)  # первый Secret у среднего игрока, не раньше 25-го дня


# --- Чтение и запись Luau-таблицы ---
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


def save_numbers(cfg, path=CONFIG):
	"""Записывает подобранные числа в Progression.luau: строки вида «Имя = { … }» внутри своих разделов."""
	text = path.read_text(encoding="utf-8")
	fmt = lambda xs: "{ " + ", ".join(f"{x:g}" if x < 1e6 else str(int(x)) for x in xs) + " }"

	def put(section, key, values):
		nonlocal text
		start = text.index(section) if section else 0
		m = re.compile(key + r" = \{[^}]*\}").search(text, start)
		text = text[: m.start()] + f"{key} = " + fmt(values) + text[m.end() :]

	put(None, "Bosses", cfg["Bosses"])
	put("Museum = {", "Prices", cfg["Museum"]["Prices"])
	put("Dumbbell = {", "Power", cfg["Dumbbell"]["Power"])
	put("Dumbbell = {", "Prices", cfg["Dumbbell"]["Prices"])
	path.write_text(text, encoding="utf-8", newline="\n")


def nice(x):
	"""Округление вниз до двух значащих цифр (вниз — чтобы не перескочить равную цену другой покупки)."""
	if x <= 0:
		return 0
	e = 10 ** (math.floor(math.log10(x)) - 1)
	return math.floor(x / e) * e


def short(x):
	"""Как в игре: 1.2K / 3.4M / 5.6B / 7.8T / 9.1Qa."""
	for div, suf in ((1e15, "Qa"), (1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
		if x >= div:
			return f"{x / div:.1f}{suf}"
	return f"{x:.0f}"


def day_str(d):
	if d == math.inf:
		return "—"
	return f"{d * SESSION / 60:.0f} мин" if d < 1 else f"{d:.1f}"


# --- Игрок ---
class Player:
	def __init__(self, cfg, rng):
		self.cfg, self.rng = cfg, rng
		self.t = 0.0
		self.S = 0.0
		self.coins = 0.0
		self.earned = 0.0
		self.level = 1  # уровень музея
		self.bell = 1  # уровень гантели
		self.items = []  # (доход, бонус силы) каждого предмета в музее и хранилище, по убыванию дохода
		self.found = {}  # (редкость, вид) → номера найденных предметов
		self.catalog_bonus = 0.0
		self.max_zone = 1
		self.events = {}  # ("zone"|"museum"|"dumbbell"|"secret", n) → время
		self.raids = 0

	# Сила, скорость, зоны
	def museum_power(self):
		"""Бонус силы от экспонатов на витринах (D31), с потолком."""
		mp = self.cfg["MuseumPower"]
		return min(mp["cap"], sum(b for _, b in self.items[: self.slots()]))

	def rate(self):
		"""Сила в секунду — сила гантели × (1 + сила музея)."""
		return self.cfg["Dumbbell"]["Power"][self.bell - 1] * (1 + self.museum_power())

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
		shown = sum(v for v, _ in self.items[: self.slots()])
		return shown * (1 + self.catalog_bonus)

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
		bonus = cfg["MuseumPower"]["Rarity"][rarity] * cfg["MuseumPower"]["Variant"][variant]

		got = self.found.setdefault((rarity, variant), set())
		if item not in got:
			got.add(item)
			if len(got) == cfg["ItemCounts"][rarity]:
				self.catalog_bonus += cfg["Catalog"]["Rarity"][rarity] * cfg["Catalog"]["Variant"][variant]
		if rarity == "Secret":
			self.events.setdefault(("secret", 1), self.t)

		self.items.append((value, bonus))
		self.items.sort(reverse=True)
		del self.items[self.slots() + STORAGE :]
		self.raids += 1

	# Тренировка
	def train(self, dt):
		while dt > 0:
			step = min(STEP, dt)
			self.S += self.rate() * step
			self.earn(step)
			self.t += step
			dt -= step
			z = self.zone()
			if z > self.max_zone:
				for k in range(self.max_zone + 1, z + 1):
					self.events[("zone", k)] = self.t
				self.max_zone = z

	# Решения: покупки (дешёвая из доступных — первой)
	def next_buys(self):
		"""Доступные покупки: (цена, вид)."""
		buys = []
		if self.level < 10:
			buys.append((self.cfg["Museum"]["Prices"][self.level - 1], "museum"))
		if self.bell < 10:
			buys.append((self.cfg["Dumbbell"]["Prices"][self.bell - 1], "dumbbell"))
		return buys

	def decide(self):
		while True:
			buys = [b for b in self.next_buys() if b[0] <= self.coins]
			if not buys:
				break
			price, kind = min(buys)
			self.coins -= price
			if kind == "museum":
				self.level += 1
				self.events[("museum", self.level)] = self.t
			else:
				self.bell += 1
				self.events[("dumbbell", self.bell)] = self.t

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
	"""Прогон игрока. until(p) → True останавливает раньше. snapshots: дни для таблицы."""
	p = Player(cfg, random.Random(seed))
	rows, want = [], sorted(snapshots or [])
	end = days * SESSION
	while p.t < end:
		p.cycle()
		while want and p.t >= want[0] * SESSION:
			rows.append(
				(want.pop(0), p.S, p.zone(), p.coins, p.level, p.bell, p.income(), p.catalog_bonus, p.museum_power())
			)
		if until and until(p):
			break
	return p, rows


# --- Подбор чисел ---
def event_day(cfg, key, seed, limit):
	p, _ = run(cfg, seed, days=limit, until=lambda p: key in p.events)
	return p.events.get(key, math.inf) / SESSION


def tune_value(cfg, values, i, key, target, seeds):
	"""Двоичный поиск по логарифму: values[i], при котором событие key случается в день target (медиана сидов).
	Нижняя граница — предыдущее число списка: цены и силы только растут."""
	lo, hi = max(values[i - 1] * 1.05, 1) if i > 0 else 1, 9e15
	limit = target * 2 + 1
	for _ in range(16):
		values[i] = math.sqrt(lo * hi)
		day = statistics.median(event_day(cfg, key, s, limit) for s in seeds)
		if day < target:
			lo = values[i]
		else:
			hi = values[i]
	values[i] = nice(math.sqrt(lo * hi))


def tune(cfg, ratio, passes=2, seeds=3):
	"""Подбирает боссов, цены музея и гантели. Музей и гантель тратят одни монеты, а сила зависит от гантели,
	поэтому все события подбираются вместе в порядке целевых дней: раннее число не зависит от позднего."""
	cfg["Dumbbell"]["Power"] = [nice(ratio**i) if ratio**i >= 100 else round(ratio**i, 1) for i in range(10)]
	jobs = []
	for k in range(2, 11):
		jobs.append((ZONE_TARGETS[k], cfg["Bosses"], k - 1, ("zone", k)))
		jobs.append((MUSEUM_TARGETS[k], cfg["Museum"]["Prices"], k - 2, ("museum", k)))
		jobs.append((DUMBBELL_TARGETS[k], cfg["Dumbbell"]["Prices"], k - 2, ("dumbbell", k)))
	jobs.sort(key=lambda j: j[0])
	for n in range(passes):
		for target, values, i, key in jobs:
			tune_value(cfg, values, i, key, target, range(1, seeds + 1))
		print(f"проход {n + 1}: боссы {[short(b) for b in cfg['Bosses']]}", flush=True)


# --- Отчёт ---
def report(cfg, seeds=200):
	snaps = [1, 2, 3, 4, 5, 7, 10, 14, 21, 28, 35, 45, 60, 75, 90]
	_, rows = run(cfg, seed=1, snapshots=snaps)
	dn = cfg["Dumbbell"]
	print("\nГантель:")
	print("| ур. | гантель | сила/с | цена |")
	print("|---|---|---|---|")
	for i in range(10):
		price = "—" if i == 0 else short(dn["Prices"][i - 1])
		power = dn["Power"][i]
		print(f"| {i + 1} | {dn['Names'][i]} | {short(power) if power >= 1000 else f'{power:g}'} | {price} |")

	print("\nТипичный игрок (сид 1), конец дня:")
	print("| день | сила | зона | монеты | музей | гантель | доход/с | каталог | сила музея |")
	print("|---|---|---|---|---|---|---|---|---|")
	for d, S, z, coins, lvl, bell, inc, cat, mp in rows:
		print(
			f"| {d} | {short(S)} | {z} | {short(coins)} | {lvl} | {bell} | {short(inc)} | +{cat * 100:.0f}% "
			f"| +{mp * 100:.0f}% |"
		)

	runs = [run(cfg, seed=s)[0] for s in range(seeds)]

	def stat(key):
		days = sorted(p.events.get(key, math.inf) / SESSION for p in runs)
		q = lambda f: days[int(f * (len(days) - 1))]
		return day_str(q(0.5)), day_str(q(0.1)), day_str(q(0.9))

	print(f"\nСобытия, день игры (медиана и 10–90 % по {seeds} игрокам):")
	print("| событие | медиана | 10 % | 90 % | цель |")
	print("|---|---|---|---|---|")
	for kind, name, targets in (
		("dumbbell", "гантель", DUMBBELL_TARGETS),
		("zone", "зона", ZONE_TARGETS),
		("museum", "музей", MUSEUM_TARGETS),
	):
		for k in range(2, 11):
			m, a, b = stat((kind, k))
			print(f"| {name} {k} | {m} | {a} | {b} | {day_str(targets[k])} |")
	m, a, b = stat(("secret", 1))
	got = sum(("secret", 1) in p.events for p in runs)
	lo, hi = SECRET_TARGET
	print(f"| первый Secret | {m} | {a} | {b} | {lo}–{hi} | ({got}/{seeds} получили за {DAYS} дней)")
	print(f"\nПредметов в день (медиана): {statistics.median(p.raids for p in runs) / DAYS:.0f}")
	peak = max(max(p.earned, p.S) for p in runs)
	print(f"Максимум чисел: {short(peak)} (предел 9e15)")


def main():
	sys.stdout.reconfigure(encoding="utf-8")
	ap = argparse.ArgumentParser()
	ap.add_argument("--tune", action="store_true")
	ap.add_argument("--ratio", type=float, default=4)
	ap.add_argument("--dry", action="store_true", help="не записывать подобранные числа")
	ap.add_argument("--seeds", type=int, default=200)
	ap.add_argument("--passes", type=int, default=2, help="проходов подбора")
	ap.add_argument("--tune-seeds", type=int, default=3, help="игроков на каждую пробу подбора (медиана)")
	args = ap.parse_args()
	cfg = load_config()
	if args.tune:
		tune(cfg, args.ratio, args.passes, args.tune_seeds)
		if not args.dry:
			save_numbers(cfg)
	report(cfg, args.seeds)


if __name__ == "__main__":
	main()
