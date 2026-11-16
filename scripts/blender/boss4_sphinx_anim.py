"""Босс 4 «Сфинкс-лежебока»: анимации в Blender на утверждённой модели v2 (этап анимаций; в игру не подключено).

Модель не пересобирается: скелет, 13 игровых поз, кинематика и проверки берутся из scripts/blender/boss4_sphinx.py
(подключается как модуль), а для кадров открывается готовый assets/models/Boss4_Sphinx.blend.

Как устроено движение. Игровой движок (Shared/BossAnim) смешивает две позы по суставам — отсюда провалы лап и
механичность. Здесь каждый клип — набор дорожек по ключам:
  • туловище, голова, мимика, платок, хвост — ключевые позы суставов, между ними кубический сплайн (без остановок в
    проходных ключах), у «мягких» частей (хвост, уши, концы платка) запаздывание;
  • лапы — в мире: место запястья, поворот лапы, подсказка локтя; суставы считаются обратной кинематикой на каждом
    кадре, поэтому опорная лапа стоит на месте, а перенос идёт по дуге над землёй;
  • слои поверх: дыхание, покачивание хвоста, уши, моргание; концы платка — маятник от движения головы.
Клипы начинаются и кончаются в игровых позах (sleep, alert, stand, combat, …), длительности состояний и момент
попадания — как в Config/Battle (ничего в бою менять не нужно). Результат запекается по кадрам (30 в секунду).

Режимы (третий аргумент): check — самопроверка кинематики и отчёт по клипам (<папка>/anim_report.json: провалы под
землю, скольжение опорных лап, недотяг, пересечения, стыки с игровыми позами, что будет при хранении 15 кадров в
секунду); sheets — то же и кадры раскадровок; render — кадры съёмок в <папка>/frames/<съёмка> и их описание
(meta_*.json); all — то же, а также экспорт assets/models/Boss4_Sphinx.anim.json (кадры клипов: Transform суставов в
осях Roblox) и assets/models/Boss4_Sphinx_anim.blend (все клипы подряд на шкале времени, маркеры — начала клипов).
SPHINX_CLIPS=имя,имя — только эти клипы; SPHINX_SHOTS=имя,имя — только эти съёмки.
Подписи, GIF и схема удара — scripts/blender/boss4_sphinx_anim_post.py, MP4 — scripts/blender/boss4_sphinx_anim_video.py.
Запуск: blender --background assets/models/Boss4_Sphinx.blend --python scripts/blender/boss4_sphinx_anim.py --
        <репо> <папка кадров> [check|sheets|render|all]
"""

import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boss4_sphinx as M  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
REPO, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
MODE = argv[2] if len(argv) > 2 else "check"
ONLY = [c for c in os.environ.get("SPHINX_CLIPS", "").split(",") if c]
os.makedirs(OUT, exist_ok=True)

FPS = 30
SCALE = M.SCALE
RIG = M.RIG
Z3 = Vector((0.0, 0.0, 0.0))
M.init_checks()

# Лапа → (лопатка или бедро, предплечье или голень, лапа, куда по умолчанию смотрит сгиб: локоть назад, колено вперёд).
LEG = {"FL": ("FUpperL", "FLowerL", "FPawL", 1.0), "FR": ("FUpperR", "FLowerR", "FPawR", 1.0),
       "BL": ("BUpperL", "BLowerL", "BPawL", -1.0), "BR": ("BUpperR", "BLowerR", "BPawR", -1.0)}
LEG_PARTS = {p for leg in LEG.values() for p in leg[:3]}
FK_PARTS = [p for p in RIG if p not in LEG_PARTS]


# ── Повороты ─────────────────────────────────────────────────────────────────────────────────────────────────


def qeuler(deg):
    return Euler([math.radians(d) for d in deg], "XYZ").to_quaternion()


def expmap(q, ref=None):
    """Кватернион → вектор «ось × угол»; ref — соседний ключ: знак выбирается так, чтобы путь был непрерывным."""
    if ref is not None and q.dot(ref) < 0:
        q = -q
    v = Vector((q.x, q.y, q.z))
    n = v.length
    if n < 1e-9:
        return np.zeros(3), q
    return np.array(v / n * (2 * math.atan2(n, q.w))), q


def from_exp(v):
    v = Vector(v)
    angle = v.length
    return Quaternion() if angle < 1e-9 else Quaternion(v / angle, angle)


def twist_angle(q, axis):
    """Угол поворота q вокруг оси axis (q — чистая скрутка вокруг неё)."""
    return 2 * math.atan2(Vector((q.x, q.y, q.z)).dot(axis), q.w)


def near_angle(a, ref):
    """Тот же угол a, ближайший к ref (без скачка на ±360°)."""
    while a - ref > math.pi:
        a -= 2 * math.pi
    while a - ref < -math.pi:
        a += 2 * math.pi
    return a


# ── Опорные позы: 13 игровых поз, поставленные на землю ──────────────────────────────────────────────────────


def lowest(tr):
    """(высота нижней точки модели в стадах, часть) для позы."""
    world = M.world_points(M.tr_matrices(tr))
    low = {g: float(w[:, 2].min()) for g, w in world.items()}
    part = min(low, key=low.get)
    return low[part], part


def ground(tr):
    """Та же поза, но туловище поднято так, чтобы нижняя точка модели лежала на земле (z = 0)."""
    out = dict(tr)
    q, off = tr["Torso"]
    out["Torso"] = (q, off - Vector((0, 0, lowest(tr)[0] / SCALE)))
    return out


A = {name: ground(M.pose_tr(M.POSES[source])) for name, source in M.EXPORT.items()}
A["pawUp"] = ground(M.pose_tr(M.POSES["pawUp"]))


def edit(tr, **parts):
    """Копия позы с правками суставов (не лап). Часть=(поворот XYZ°, сдвиг) — задать заново; часть={"r": …} —
    довернуть поверх (в осях сустава), {"o": …} — досдвинуть, {"R": …} — задать только поворот, {"O": …} — сдвиг."""
    out = {k: (q.copy(), o.copy()) for k, (q, o) in tr.items()}
    for name, value in parts.items():
        q, o = out[name]
        if isinstance(value, dict):
            if "R" in value:
                q = qeuler(value["R"])
            if "O" in value:
                o = Vector(value["O"])
            if "r" in value:
                q = q @ qeuler(value["r"])
            if "o" in value:
                o = o + Vector(value["o"])
        else:
            q, o = qeuler(value[0]), Vector(value[1])
        out[name] = (q, o)
    return out


# ── Лапы: состояние в мире и обратная кинематика двух костей ─────────────────────────────────────────────────


def leg_state(tr, key):
    """Состояние лапы в позе tr (мир, единицы модели): w — запястье, q — поворот лапы, d — куда смотрит сгиб
    (локоть или колено; единичный вектор поперёк линии плечо — запястье), tu и tl — скрутка лопатки и предплечья
    вокруг своей кости, off — сдвиг плеча."""
    up, lo, paw, sign = LEG[key]
    mats = M.tr_matrices(tr)
    qt = mats["Torso"].to_quaternion()
    s, e, w = (mats[p].translation / SCALE for p in (up, lo, paw))
    q_up, q_lo, q_paw = (mats[p].to_quaternion() for p in (up, lo, paw))
    u0 = Vector(RIG[lo][1]) - Vector(RIG[up][1])
    l0 = Vector(RIG[paw][1]) - Vector(RIG[lo][1])
    swing_up = (qt @ u0).rotation_difference(e - s) @ qt
    swing_lo = (q_up @ l0).rotation_difference(w - e) @ q_up
    u = (w - s).normalized()
    d = (e - s) - (e - s).dot(u) * u
    if d.length < 0.02:  # лапа почти прямая: сгиб по умолчанию (локоть назад, колено вперёд)
        d = qt @ Vector((0.0, sign, 0.0))
        d = d - d.dot(u) * u
    return {"w": w, "q": q_paw, "d": d.normalized(), "tu": twist_angle(q_up @ swing_up.inverted(), (e - s).normalized()),
            "tl": twist_angle(q_lo @ swing_lo.inverted(), (w - e).normalized()), "off": tr[up][1].copy()}


def solve_leg(tr, key, st):
    """Суставы лапы key по её состоянию st при туловище из tr. Возвращает недотяг до цели (единицы модели)."""
    up, lo, paw, sign = LEG[key]
    qt, toff = tr["Torso"]
    p0 = Vector(RIG["Torso"][1])
    s0, e0, w0 = Vector(RIG[up][1]), Vector(RIG[lo][1]), Vector(RIG[paw][1])
    s = p0 + toff + qt @ (s0 - p0 + st["off"])
    u0, l0 = e0 - s0, w0 - e0
    l1, l2 = u0.length, l0.length
    d = st["w"] - s
    dist = min(max(d.length, abs(l1 - l2) + 1e-3), l1 + l2 - 1e-4)
    u = d.normalized()
    along = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    pole = st["d"] - st["d"].dot(u) * u
    if pole.length < 0.05:
        pole = qt @ Vector((0.0, sign, 0.0))
        pole = pole - pole.dot(u) * u
    e = s + along * u + math.sqrt(max(l1 * l1 - along * along, 0.0)) * pole.normalized()
    w = s + dist * u
    q_up = Quaternion((e - s).normalized(), st["tu"]) @ (qt @ u0).rotation_difference(e - s) @ qt
    q_lo = Quaternion((w - e).normalized(), st["tl"]) @ (q_up @ l0).rotation_difference(w - e) @ q_up
    tr[up] = (qt.inverted() @ q_up, st["off"].copy())
    tr[lo] = (q_up.inverted() @ q_lo, Z3.copy())
    tr[paw] = (q_lo.inverted() @ st["q"], Z3.copy())
    return (st["w"] - w).length


def mix_state(a, b, k):
    """Промежуточное состояние лапы."""
    d = a["d"].lerp(b["d"], k)
    return {"w": a["w"].lerp(b["w"], k), "q": a["q"].slerp(b["q"], k), "d": d.normalized() if d.length > 0.1 else a["d"].copy(),
            "tu": a["tu"] + (near_angle(b["tu"], a["tu"]) - a["tu"]) * k,
            "tl": a["tl"] + (near_angle(b["tl"], a["tl"]) - a["tl"]) * k, "off": a["off"].lerp(b["off"], k)}


def moved(st, dw=(0, 0, 0), pitch=0.0, yaw=0.0, roll=0.0, bend=None, **over):
    """Копия состояния лапы: сдвиг запястья, наклон лапы пальцами вниз (pitch), разворот и крен, bend — куда
    смотрит сгиб (вектор)."""
    out = {k: (v.copy() if hasattr(v, "copy") else v) for k, v in st.items()}
    out["w"] = st["w"] + Vector(dw)
    if pitch or yaw or roll:
        out["q"] = qeuler((0, 0, yaw)) @ st["q"] @ qeuler((pitch, roll, 0))
    if bend is not None:
        out["d"] = Vector(bend).normalized()
    out.update(over)
    return out


def selftest():
    """Кинематика возвращает опорные позы: состояние лапы → суставы → те же мировые матрицы."""
    worst = 0.0
    for name, tr in A.items():
        ref = M.tr_matrices(tr)
        for key, leg in LEG.items():
            again = {k: (q.copy(), o.copy()) for k, (q, o) in tr.items()}
            solve_leg(again, key, leg_state(tr, key))
            got = M.tr_matrices(again)
            for p in leg[:3]:
                worst = max(worst, (ref[p].translation - got[p].translation).length,
                            math.degrees(ref[p].to_quaternion().rotation_difference(got[p].to_quaternion()).angle))
    print(f"SELFTEST кинематика лап на {len(A)} позах: наибольшее расхождение {worst:.4f} (стады или градусы)")
    return worst


# ── Сплайн по ключам ─────────────────────────────────────────────────────────────────────────────────────────


class Curve:
    """Кубический сплайн Эрмита по ключам (время, значение, остановка). В ключе с остановкой и на концах скорость
    нулевая; в проходных ключах касательная — по соседям (движение не замирает). loop — концы стыкуются."""

    def __init__(self, keys, loop=False):
        keys = sorted(keys, key=lambda k: k[0])
        self.t = [float(k[0]) for k in keys]
        self.v = [np.atleast_1d(np.asarray(k[1], float)) for k in keys]
        hold = [bool(k[2]) if len(k) > 2 else False for k in keys]
        n = len(keys)
        self.m = []
        for i in range(n):
            if hold[i] or n == 1:
                self.m.append(np.zeros_like(self.v[i]))
            elif 0 < i < n - 1:
                self.m.append((self.v[i + 1] - self.v[i - 1]) / (self.t[i + 1] - self.t[i - 1]))
            elif loop and n > 2:  # концы цикла — один и тот же ключ
                j, k = (1, n - 2)
                self.m.append((self.v[j] - self.v[k]) / ((self.t[j] - self.t[0]) + (self.t[-1] - self.t[k])))
            else:
                self.m.append(np.zeros_like(self.v[i]))

    def __call__(self, t):
        ts = self.t
        if t <= ts[0]:
            return self.v[0]
        if t >= ts[-1]:
            return self.v[-1]
        i = max(k for k in range(len(ts) - 1) if ts[k] <= t)
        h = ts[i + 1] - ts[i]
        s = (t - ts[i]) / h
        s2, s3 = s * s, s * s * s
        return ((2 * s3 - 3 * s2 + 1) * self.v[i] + (s3 - 2 * s2 + s) * h * self.m[i]
                + (-2 * s3 + 3 * s2) * self.v[i + 1] + (s3 - s2) * h * self.m[i + 1])


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def bump(t, t0, t1, peak=None):
    """Плавный бугор 0 → 1 → 0 на отрезке [t0, t1] (вершина в peak или посередине)."""
    if t <= t0 or t >= t1:
        return 0.0
    peak = (t0 + t1) / 2 if peak is None else peak
    return smooth((t - t0) / (peak - t0)) if t < peak else smooth((t1 - t) / (t1 - peak))


if MODE == "selftest":
    selftest()
    for name in ("sleep", "alert", "stand", "combat", "bite", "swipe", "dizzy", "bark", "hit"):
        print("ANCHOR", name, "torso", [round(c, 3) for c in A[name]["Torso"][1]],
              [round(math.degrees(a), 1) for a in A[name]["Torso"][0].to_euler("XYZ")])
        for key in LEG:
            st = leg_state(A[name], key)
            print("   ", key, "w", [round(c, 2) for c in st["w"]], "d", [round(c, 2) for c in st["d"]],
                  "paw", [round(math.degrees(a)) for a in st["q"].to_euler("XYZ")],
                  "tw", round(math.degrees(st["tu"])), round(math.degrees(st["tl"])), "off", [round(c, 2) for c in st["off"]])
    sys.exit(0)


# ── Клип: дорожки по ключам → поза на любой момент ───────────────────────────────────────────────────────────

SOFT_LAG = {"Tail1": 0.02, "Tail2": 0.045, "Tail3": 0.07, "Tassel": 0.1, "EarL": 0.03, "EarR": 0.03}


class Clip:
    """Один клип. Суставы туловища, головы, мимики, платка и хвоста — ключевые позы (pose); лапы — состояния в мире
    (foot, step, plant); layers — правки поверх (дыхание, покачивание); events — отметки времени (контакт удара)."""

    def __init__(self, name, title, duration, loop=False, lag=None):
        self.name, self.title, self.dur, self.loop = name, title, float(duration), loop
        self.body = {p: [] for p in FK_PARTS}
        self.legs = {k: [] for k in LEG}
        self.layers, self.leg_layers = [], []
        self.lag = dict(SOFT_LAG if lag is None else lag)
        self.events, self.notes = {}, []
        self.built = False
        self.short_by = {}  # лапа → (наибольший недотяг до цели, когда)

    # — ключи —
    def pose(self, t, tr, hold=False, only=None, skip=()):
        """Ключ суставов (не лап) из позы tr в момент t."""
        for p in FK_PARTS if only is None else only:
            if p not in skip:
                self.body[p].append((t, tr[p][0].copy(), tr[p][1].copy(), hold))
        return self

    def part(self, name, t, rot=None, off=None, hold=False, base=None):
        """Ключ одного сустава: поворот XYZ° и сдвиг (чего нет — из позы base или из прошлого ключа)."""
        prev = base[name] if base is not None else (self.body[name][-1][1], self.body[name][-1][2])
        self.body[name].append((t, prev[0].copy() if rot is None else qeuler(rot),
                                prev[1].copy() if off is None else Vector(off), hold))
        return self

    def foot(self, key, t, st, hold=False):
        self.legs[key].append((t, st, hold))
        return self

    def feet(self, t, tr, hold=True, only=None):
        """Ключи лап из позы tr (опорные лапы — с остановкой)."""
        for key in LEG if only is None else only:
            self.foot(key, t, leg_state(tr, key), hold)
        return self

    def last(self, key):
        return max(self.legs[key], key=lambda k: k[0])[1]

    def plant(self, key, t):
        """Лапа стоит, где стояла, до момента t."""
        return self.foot(key, t, self.last(key), True)

    def step(self, key, t0, t1, st, lift=0.2, toe=0.0, out=0.0, knee=(0.0, 0.0)):
        """Перенос лапы с t0 по t1 из прежнего места в состояние st: сначала отрыв вверх, потом перенос по дуге
        высотой lift, в конце — вниз на место (лапа не волочится). toe — наклон пальцами вниз в вершине (градусы),
        out — вынос дуги вбок наружу, knee — на сколько сгиб в вершине смотрит назад и вверх (добавка к вектору)."""
        a = self.last(key)
        self.foot(key, t0, a, True)
        side = 1.0 if key[1] == "L" else -1.0
        span = t1 - t0
        for share, way, high in ((0.2, 0.07, 0.55), (0.5, 0.5, 1.0), (0.8, 0.93, 0.55)):
            k = mix_state(a, st, way)
            bow = math.sin(math.pi * way)
            k["w"] = k["w"] + Vector((side * out * bow, 0.0, lift * high))
            k["d"] = (k["d"] + Vector((0.0, knee[0] * bow, knee[1] * bow))).normalized()
            if toe:
                k["q"] = k["q"] @ qeuler((toe * bow, 0, 0))
            self.foot(key, t0 + span * share, k, False)
        self.foot(key, t1, st, True)
        return self

    def torso_at(self, t):
        """Туловище (кватернион, сдвиг) в момент t по уже поставленным ключам (без слоёв)."""
        keys = self._keys(self.body["Torso"])
        rot, ref = [], None
        for tt, q, _, hold in keys:
            v, ref = expmap(q, ref)
            rot.append((tt, v, hold))
        return from_exp(Curve(rot)(t)), Vector(Curve([(tt, tuple(o), h) for tt, _, o, h in keys])(t))

    def hop(self, key, t0, t1, st, lift=0.3):
        """Перенос лапы, когда туловище в это время разворачивается: в воздухе лапа идёт под своим плечом или
        бедром (а не по прямой между местами), поэтому нога не вытягивается в струну."""
        a = self.last(key)
        self.foot(key, t0, a, True)
        rest, p0 = Vector(RIG[LEG[key][2]][1]), Vector(RIG["Torso"][1])
        sign = LEG[key][3]
        span = t1 - t0
        for share, high, own in ((0.25, 0.75, 0.55), (0.5, 1.0, 0.85), (0.75, 0.75, 0.55)):
            t = t0 + span * share
            q, off = self.torso_at(t)
            home = p0 + off + q @ (rest - p0)
            k = mix_state(a, st, share)
            flat = k["w"].lerp(Vector((home.x, home.y, k["w"].z)), own)
            k["w"] = Vector((flat.x, flat.y, k["w"].z + lift * high))
            k["d"] = (q @ Vector((0.0, sign, 0.25))).normalized()
            self.foot(key, t, k, False)
        self.foot(key, t1, st, True)
        return self

    def event(self, name, t):
        self.events[name] = t
        return self

    # — сборка сплайнов —
    @staticmethod
    def _keys(keys):
        """Ключи по времени; из двух ключей в один момент остаётся поставленный позже."""
        out = []
        for k in sorted(keys, key=lambda k: k[0]):
            if out and abs(k[0] - out[-1][0]) < 1e-6:
                out[-1] = k
            else:
                out.append(k)
        return out

    def build(self):
        self.curves = {}
        for p, keys in self.body.items():
            assert keys, f"{self.name}: нет ключей сустава {p}"
            keys = self._keys(keys)
            rot, ref = [], None
            for t, q, _, hold in keys:
                v, ref = expmap(q, ref)
                rot.append((t, v, hold))
            self.curves[p] = (Curve(rot, self.loop), Curve([(t, tuple(o), h) for t, _, o, h in keys], self.loop))
        self.leg_curves = {}
        for key, keys in self.legs.items():
            assert keys, f"{self.name}: нет ключей лапы {key}"
            keys = self._keys(keys)
            rot, ref, tu, tl = [], None, [], []
            for t, st, hold in keys:
                v, ref = expmap(st["q"], ref)
                rot.append((t, v, hold))
                tu.append((t, near_angle(st["tu"], tu[-1][1]) if tu else st["tu"], hold))
                tl.append((t, near_angle(st["tl"], tl[-1][1]) if tl else st["tl"], hold))
            self.leg_curves[key] = {
                "w": Curve([(t, tuple(st["w"]), h) for t, st, h in keys], self.loop),
                "d": Curve([(t, tuple(st["d"]), h) for t, st, h in keys], self.loop),
                "off": Curve([(t, tuple(st["off"]), h) for t, st, h in keys], self.loop),
                "q": Curve(rot, self.loop), "tu": Curve(tu, self.loop), "tl": Curve(tl, self.loop)}
        self.built = True
        return self

    def _time(self, t, p):
        lag = self.lag.get(p, 0.0)
        if not lag:
            return t
        if self.loop:
            return (t - lag) % self.dur
        return max(t - lag * min(1.0, max(0.0, (self.dur - t) / (4 * lag))), 0.0)

    def leg_at(self, key, t):
        c = self.leg_curves[key]
        return {"w": Vector(c["w"](t)), "d": Vector(c["d"](t)), "off": Vector(c["off"](t)),
                "q": from_exp(c["q"](t)), "tu": float(c["tu"](t)[0]), "tl": float(c["tl"](t)[0])}

    def sample(self, t):
        """Поза (сустав → (кватернион, сдвиг)) в момент t и недотяг лап."""
        if not self.built:
            self.build()
        tr = {}
        for p in FK_PARTS:
            rot, off = self.curves[p]
            tt = self._time(t, p)
            tr[p] = (from_exp(rot(tt)), Vector(off(tt)))
        for layer in self.layers:
            layer(t, tr)
        short = 0.0
        for key in LEG:
            st = self.leg_at(key, t)
            for layer in self.leg_layers:
                st = layer(t, key, st, tr) or st
            miss = solve_leg(tr, key, st)
            if miss > self.short_by.get(key, (0.0, 0.0))[0]:
                self.short_by[key] = (miss, t)
            short = max(short, miss)
        return tr, short

    def frames(self):
        """Кадры клипа: у цикла — ровно период (последний кадр стыкуется с первым), иначе — с конечным кадром."""
        n = round(self.dur * FPS)
        times = [i / FPS for i in range(n if self.loop else n + 1)]
        out, short = [], 0.0
        for t in times:
            tr, s = self.sample(t)
            out.append(tr)
            short = max(short, s)
        self.short = short
        return clear_lappets(swing_lappets(out, self.loop), self.loop)


# Концы платка — маятники: отстают от движения головы и докачиваются. Назад (к плечам) и внутрь (к щекам) почти не
# идут — там тело; вперёд и наружу — свободно.
LAPPET = {"freq": 1.7, "damp": 0.38, "gain": 0.5, "limit": 11.0, "stop": 0.6}


def swing_lappets(frames, loop):
    dt = 1.0 / FPS
    w0 = 2 * math.pi * LAPPET["freq"]
    mats = [M.tr_matrices(tr) for tr in frames]
    rot = [m["Head"].to_quaternion() for m in mats]
    n = len(frames)
    for name, side in (("NemesL", 1.0), ("NemesR", -1.0)):
        pos = [m[name].translation / SCALE for m in mats]
        state = np.zeros(4)  # наклон вперёд-назад, крен, их скорости
        out = [None] * n
        for _ in range(3 if loop else 1):
            for i in range(n):
                if loop:
                    a, b, c = pos[(i - 1) % n], pos[i], pos[(i + 1) % n]
                else:
                    a, b, c = pos[max(i - 1, 0)], pos[i], pos[min(i + 1, n - 1)]
                pitch = min(max(math.degrees(state[0]), -LAPPET["limit"]), LAPPET["stop"])
                roll = math.degrees(state[1])
                roll = (min(max(roll, -LAPPET["limit"]), LAPPET["stop"]) if side > 0
                        else min(max(roll, -LAPPET["stop"]), LAPPET["limit"]))
                out[i] = (pitch, roll)
                acc = rot[i].inverted() @ ((a - 2 * b + c) / (dt * dt))
                drive = np.array([-acc.y, acc.x]) * LAPPET["gain"] / 0.75
                for k in range(2):
                    state[2 + k] += (-w0 * w0 * state[k] - 2 * LAPPET["damp"] * w0 * state[2 + k] + drive[k]) * dt
                    state[k] += state[2 + k] * dt
        if not loop:  # клип кончается в опорной позе: размах гаснет к концу
            for i in range(n):
                k = smooth((n - 1 - i) / max(0.25 * FPS, 1))
                out[i] = (out[i][0] * k, out[i][1] * k)
        for tr, (pitch, roll) in zip(frames, out):
            q, off = tr[name]
            tr[name] = (q @ qeuler((pitch, roll, 0)), off)
    return frames


# Концы платка уступают телу: если конец заходит в плечо, лапу или туловище, он подтягивается вверх под крыло платка
# и чуть наклоняется вперёд — ровно настолько, чтобы разойтись; поправка сглажена по времени (без рывков).
LAPPET_CLEAR = {"lift": 0.4, "pitch": -7.0, "gap": 0.26, "others": ("FUpper", "FLower", "FPaw")}


def depth_between(mats, a, b):
    """Глубина в стадах, на которую точки части a заходят в тела части b и наоборот."""
    best = 0.0
    for x, y in ((a, b), (b, a)):
        if y not in M.SOLIDS:
            continue
        m = np.array(mats[x])
        w = ((M.POINTS[x] - np.array(RIG[x][1])) * SCALE) @ m[:3, :3].T + m[:3, 3]
        mb = np.array(mats[y].inverted())
        q = (w @ mb[:3, :3].T + mb[:3, 3]) / SCALE + np.array(RIG[y][1])
        for inv, n, d, scale, lo, hi in M.SOLIDS[y]:
            mask = np.all((q >= lo) & (q <= hi), axis=1)
            if mask.any():
                ql = q[mask] @ inv[:3, :3].T + inv[:3, 3]
                best = max(best, float((d[None, :] - ql @ n.T).min(axis=1).max()) * scale)
    return best * SCALE


def clear_lappets(frames, loop):
    n = len(frames)
    for name in ("NemesL", "NemesR"):
        side = name[-1]
        others = [p + side for p in LAPPET_CLEAR["others"]] + ["Torso", "FPaw" + ("R" if side == "L" else "L")]
        base = {o: M.BASE.get("+".join(sorted((name, o))), 0.0) for o in others}

        def pushed(tr, c):
            q, off = tr[name]
            out = dict(tr)
            out[name] = (q @ qeuler((LAPPET_CLEAR["pitch"] * c, 0, 0)), off + Vector((0, 0, LAPPET_CLEAR["lift"] * c)))
            return out

        def clear(tr, c):
            mats = M.tr_matrices(pushed(tr, c))
            return all(depth_between(mats, name, o) - base[o] < LAPPET_CLEAR["gap"] for o in others)

        need = []
        for tr in frames:
            if clear(tr, 0.0):
                need.append(0.0)
                continue
            lo, hi = 0.0, 1.0
            for _ in range(6):
                mid = (lo + hi) / 2
                if clear(tr, mid):
                    hi = mid
                else:
                    lo = mid
            need.append(hi)
        if not any(need):
            continue

        def at(i):
            return need[i % n] if loop else need[min(max(i, 0), n - 1)]

        wide = [max(at(j) for j in range(i - 4, i + 5)) for i in range(n)]

        def at2(i):
            return wide[i % n] if loop else wide[min(max(i, 0), n - 1)]

        soft = [sum(at2(j) for j in range(i - 3, i + 4)) / 7 for i in range(n)]
        if not loop:  # клип начинается и кончается в опорной позе
            soft[0] = need[0]
            soft[-1] = need[-1]
        for i, tr in enumerate(frames):
            c = max(soft[i], need[i])
            if c > 0:
                frames[i] = pushed(tr, c)
    return frames


# ── Клипы ────────────────────────────────────────────────────────────────────────────────────────────────────
# Время — секунды от начала клипа. Длительности состояний и момент попадания — из Config/Battle (не меняются):
# Wake 1.0 + StandUp 0.9 + ToCombat 0.5, Victory 2.2, Defeat 2.4, FallAsleep 1.6, попадание через 0.25 с после начала
# выпада (HitDelay), выпады босса раз в 1.4 с, скорость 10 стадов в секунду.

HS = M.HEAD_SCALE
LID = {"closed": 0.0, "squint": 0.2 * HS, "half": 0.33 * HS, "open": 0.5 * HS}
EYES = ["EyelidL", "EyelidR", "BrowL", "BrowR"]
EARS = ["EarL", "EarR"]
NEMES = ["NemesL", "NemesR"]
TAIL = ["Tail1", "Tail2", "Tail3", "Tassel"]
CORE = ["Torso", "Head", "Jaw"]
SL, AL, ST, CB = A["sleep"], A["alert"], A["stand"], A["combat"]
LS = {name: {key: leg_state(tr, key) for key in LEG} for name, tr in A.items()}  # состояния лап опорных поз
EDGE_OUT = qeuler((0, -90, 0))  # правая лапа на ребре: тыльной стороной наружу
HIT_DELAY = 0.25  # Config/Battle.HitDelay: от начала выпада до попадания


def face(tr, lid=None, lid_r=None, brow=None, brow_r=None, jaw=None, ears=None):
    """Копия позы с мимикой: веки (сдвиг вверх), брови (поворот°, подъём), челюсть (°), уши (назад°, в стороны°)."""
    out = {k: (q.copy(), o.copy()) for k, (q, o) in tr.items()}
    if lid is not None:
        out["EyelidL"] = (Quaternion(), Vector((0, 0, lid)))
        out["EyelidR"] = (Quaternion(), Vector((0, 0, lid if lid_r is None else lid_r)))
    if brow is not None:
        br = brow if brow_r is None else brow_r
        out["BrowL"] = (qeuler((0, brow[0], 0)), Vector((0, 0, brow[1])))
        out["BrowR"] = (qeuler((0, -br[0], 0)), Vector((0, 0, br[1])))
    if jaw is not None:
        out["Jaw"] = (qeuler((jaw, 0, 0)), out["Jaw"][1])
    if ears is not None:
        out["EarL"] = (qeuler((ears[0], ears[1], 0)), out["EarL"][1])
        out["EarR"] = (qeuler((ears[0], -ears[1], 0)), out["EarR"][1])
    return out


def blend(a, b, k):
    """Промежуточная поза суставов."""
    return {p: (a[p][0].slerp(b[p][0], k), a[p][1].lerp(b[p][1], k)) for p in RIG}


def with_tail(tr, t1, t2, t3, tassel):
    """Копия позы с хвостом: повороты звеньев и кисти относительно туловища (XYZ°), как в позах модели."""
    out = dict(tr)
    for name, (rot, _) in M.tail(t1, t2, t3, tassel).items():
        out[name] = (qeuler(rot), tr[name][1].copy())
    return out


def turned(yaw, pitch, drop):
    """Туловище, повёрнутое вокруг вертикали между передними лапами (таз уходит вбок), опущенное на drop."""
    rot, off = M.pivot_turn(yaw, pitch)
    return (rot, (off[0], off[1], -drop))


def add(tr, name, rot=(0, 0, 0), off=(0, 0, 0)):
    q, o = tr[name]
    tr[name] = (q @ qeuler(rot), o + Vector(off))


def follow_head(key, base):
    """Лапа key держится за голову (кулак под щекой): её запястье и поворот идут за головой от позы base."""
    head0 = M.tr_matrices(base)["Head"]
    st0 = leg_state(base, key)
    local = head0.inverted() @ (st0["w"] * SCALE)
    q_local = head0.to_quaternion().inverted() @ st0["q"]
    rest = {p: (Quaternion(), Z3) for p in RIG}

    def layer(t, k, st, tr):
        if k != key:
            return None
        head = M.tr_matrices(rest | {p: tr[p] for p in ("Torso", "Head")})["Head"]
        out = dict(st)
        out["w"] = (head @ local) / SCALE
        out["q"] = head.to_quaternion() @ q_local
        return out

    return layer


def steady_shoulders(base):
    """Плечи и бёдра остаются там, где они в позе base: дыхание поднимает туловище, а лапы лежат неподвижно
    (сустав плеча чуть скользит по корпусу — на долю стада)."""
    mats = M.tr_matrices(base)
    home = {key: mats[LEG[key][0]].translation / SCALE for key in LEG}
    p0 = Vector(RIG["Torso"][1])

    def layer(t, key, st, tr):
        qt, toff = tr["Torso"]
        now = p0 + toff + qt @ (Vector(RIG[LEG[key][0]][1]) - p0)
        out = dict(st)
        out["off"] = qt.inverted() @ (home[key] - now)
        return out

    return layer


def keep_head(tr, base_head):
    """Голова остаётся на месте в мире (лежит на кулаке), как бы ни двигалось туловище: шея подстраивается."""
    qt, toff = tr["Torso"]
    p0, h0 = Vector(RIG["Torso"][1]), Vector(RIG["Head"][1])
    tr["Head"] = (qt.inverted() @ base_head.to_quaternion(),
                  qt.inverted() @ (base_head.translation / SCALE - p0 - toff) - (h0 - p0))


def clip_sleep():
    """A. Сон: дыхание, уши, хвост, брови. Цикл 6.4 с (два вдоха)."""
    c = Clip("sleep_idle", "Сон", 6.4, loop=True)
    c.pose(0.0, SL, hold=True).pose(c.dur, SL, hold=True)
    c.feet(0.0, SL).feet(c.dur, SL)
    head_home = M.tr_matrices(SL)["Head"]

    def breathe(t, tr):
        b = 0.5 - 0.5 * math.cos(2 * math.pi * t / 3.2)  # вдох 0 → 1 → 0
        slow = math.sin(2 * math.pi * t / c.dur)
        # грудь и спина поднимаются, а голова лежит на кулаке и лапы — на земле: они не двигаются
        add(tr, "Torso", (-1.5 * b, 0, 0), (0, 0, 0.085 * b))
        keep_head(tr, head_home)
        add(tr, "Head", (0.25 * b, 0, 0.5 * slow))
        add(tr, "Jaw", (1.2 * b, 0, 0))
        add(tr, "EarL", (0, 22 * (bump(t, 1.9, 2.25, 2.0) - 0.5 * bump(t, 2.2, 2.5)), 0))
        add(tr, "EarR", (0, -15 * bump(t, 4.55, 4.9, 4.65), 0))
        add(tr, "BrowL", (0, 1.6 * slow, 0), (0, 0, 0.012 * b))
        add(tr, "BrowR", (0, 1.2 * slow, 0), (0, 0, 0.02 * bump(t, 4.4, 5.6)))
        flick = bump(t, 3.85, 4.5, 4.0) - 0.45 * bump(t, 4.4, 4.95)
        sway = math.sin(2 * math.pi * t / c.dur)
        for name, yaw, lift in (("Tail2", 2.0, 0.0), ("Tail3", 4.0, 8.0), ("Tassel", 7.0, 18.0)):
            add(tr, name, (-lift * flick, 0, yaw * sway))

    c.layers.append(breathe)
    c.leg_layers.append(steady_shoulders(SL))
    c.leg_layers.append(follow_head("FR", SL))
    c.notes.append("два вдоха по 3.2 с; ухо — на 2.0 и 4.7 с, кисть хвоста — на 4.0 с")
    return c


def clip_wake():
    """B. Пробуждение: глаза → голова с кулака → вес на левую лапу → разворот опорной лапы в воздухе → лапы под
    плечи → грудь вверх → боевая стойка. Границы состояний игры: 1.0 с (лёжа) и 1.9 с (стойка)."""
    c = Clip("wake", "Пробуждение", 2.4)
    t1, t2 = 1.0, 1.9
    c.event("лёжа (конец Wake)", t1).event("стойка (конец StandUp)", t2)
    # — туловище, голова, платок, хвост —
    c.pose(0.0, SL, hold=True)
    c.pose(0.22, SL, hold=True, only=CORE)
    # глаза приоткрываются по очереди, бровь ползёт вверх, ухо дёргается
    c.pose(0.08, SL, hold=True, only=EYES + EARS)
    c.pose(0.30, face(SL, lid=LID["squint"], lid_r=0.08, brow=(2, 0.0), brow_r=(6, 0.05), ears=(0, 22)), only=EYES + EARS)
    # голова снимается с кулака — чуть выше, чем нужно, и оседает
    up = edit(face(AL, lid=LID["half"], brow=(-4, 0.0), brow_r=(6, 0.07)), Head=((-13, -3, 5), (0.0, 0.0, -0.04)),
              Torso={"r": (-1.5, 1.2, 0), "o": (0.02, 0, 0.05)})
    c.pose(0.62, up, only=CORE + EYES + EARS)
    # вес на левое предплечье, пока правая лапа разворачивается
    lean = edit(AL, Torso={"r": (-1, 1.5, 0), "o": (0.03, 0, 0.05)}, Head=((-9, -2, 3), (0, 0, -0.08)))
    c.pose(0.82, lean, only=["Torso", "Head"])
    c.pose(t1, AL, skip=("NemesR",))
    # конец платка справа отведён в сторону, пока под ним лапа; возвращается, когда она легла
    c.pose(0.9, SL, hold=True, only=["NemesR"])
    c.part("NemesR", 1.3, rot=(-10, -4, 0), off=(0, 0, 0))
    # подъём: лапы уже под плечами, грудь идёт первой, голова прижимается, потом таз
    c.pose(1.15, edit(AL, Torso=((-2.5, -3.0, 0), (-0.04, 0.01, -0.58)), Head=((-4, 2, 0), (0, 0, -0.08))), only=["Torso", "Head"])
    c.pose(1.34, edit(AL, Torso=((-5.0, 2.0, 0), (0.03, 0.02, -0.5)), Head=((-1, -1, 0), (0, 0, -0.05))), only=["Torso", "Head"])
    rise = edit(face(ST, lid=LID["half"], brow=(-6, 0.0)), Torso=((-9.5, 0, 0), (0, 0.04, -0.3)), Head=((6, 0, 0), Z3))
    c.pose(1.54, rise, only=CORE + EYES + EARS)
    top = edit(ST, Torso=((-3.0, 0, 0), (0, 0.0, -0.085)), Head=((-4, 0, 0), Z3))
    c.pose(1.74, top, only=["Torso", "Head"])
    c.pose(t2, ST)
    # в боевую стойку: приседает чуть ниже и возвращается, брови сходятся
    dip = edit(face(CB, lid=LID["squint"], brow=(-15, -0.03), jaw=10, ears=(-18, 0)),
               Torso=((6.6, 0, 0), (0, 0, -0.175)), Head=((7.5, 0, 0), Z3), NemesL=((-7, 0, 0), Z3), NemesR=((-7, 0, 0), Z3))
    c.pose(2.2, dip, only=CORE + EYES + EARS + NEMES)
    c.pose(2.4, CB, hold=True)
    # — лапы —
    c.feet(0.0, SL)
    # левая: лежит, где лежала во сне, потом шагает под плечо
    c.plant("FL", 1.02)
    c.step("FL", 1.02, 1.3, LS["stand"]["FL"], lift=0.22, knee=(0.3, 1.0))
    # правая (опорная): ждёт, пока голова поднимется, отрывается, переворачивается в воздухе и ложится
    c.plant("FR", 0.44)
    a, b = LS["sleep"]["FR"], LS["alert"]["FR"]
    edge = mix_state(a, b, 0.5)
    edge.update(w=Vector((-1.22, -2.06, 0.95)), q=EDGE_OUT)
    c.foot("FR", 0.62, edge)
    over = mix_state(a, b, 0.92)
    over.update(w=Vector((-1.0, -1.92, 0.76)), q=qeuler((-7, 0, 0)))
    c.foot("FR", 0.8, over)
    c.foot("FR", 0.98, b, True)
    c.plant("FR", 1.27)
    c.step("FR", 1.27, 1.56, LS["stand"]["FR"], lift=0.22, knee=(0.3, 1.0))
    for key in ("FL", "FR"):
        c.foot(key, t2, LS["stand"][key], True)
    for key in ("BL", "BR"):
        c.foot(key, t1, LS["alert"][key], True)
        c.foot(key, t2, LS["stand"][key], True)
    c.feet(2.4, CB)
    return c


def clip_combat():
    """C. Боевая стойка: дыхание, перенос веса, голова ведёт за противником, хвост покачивается, моргание."""
    c = Clip("combat_idle", "Боевая стойка", 3.6, loop=True)
    c.pose(0.0, CB, hold=True).pose(c.dur, CB, hold=True)
    c.feet(0.0, CB).feet(c.dur, CB)

    def live(t, tr):
        ph = 2 * math.pi * t / c.dur
        b = 0.5 - 0.5 * math.cos(2 * ph)  # два вдоха за цикл
        sway = math.sin(ph)
        add(tr, "Torso", (1.4 * b, 1.6 * sway, 1.0 * (math.sin(ph - 0.6) + math.sin(0.6))), (0.04 * sway, 0, -0.05 * b))
        add(tr, "Head", (1.3 * b, -1.3 * sway, 3.6 * (math.sin(ph - 1.0) + math.sin(1.0))))
        add(tr, "Jaw", (2.0 * b, 0, 0))
        for name, yaw, lag, lift in (("Tail1", 9.0, 0.4, 2.0), ("Tail2", 9.0, 0.85, 3.0), ("Tail3", 8.0, 1.3, 3.0),
                                     ("Tassel", 13.0, 1.8, 4.0)):
            add(tr, name, (lift * (math.cos(2 * (ph - lag)) - math.cos(2 * lag)), 0, yaw * (math.sin(ph - lag) + math.sin(lag))))
        for name in EARS:
            add(tr, name, (-2.5 * b, 0, 0))
        blink = bump(t, 2.48, 2.72)
        for name in ("EyelidL", "EyelidR"):
            q, o = tr[name]
            tr[name] = (q, o * (1 - blink))
        add(tr, "BrowL", (0, -1.5 * b, 0))
        add(tr, "BrowR", (0, 1.5 * b, 0))

    c.layers.append(live)
    c.notes.append("два вдоха за цикл 3.6 с; моргание на 2.6 с")
    return c


# Цикл — целое число кадров (22 при 30 к/с). Ноги короткие (от плеча до запястья 3.84 стада при длине тела 23.5),
# поэтому шаг длиннее 7–7.5 стада им не достать: «вес» даёт не редкий шаг, а корпус — он оседает на каждую пару лап
# (bob), переваливается (sway, крен) и ведёт плечом за лапой.
WALK = {"period": 22 / 30, "duty": 0.5, "drop": 0.2, "bob": 0.055, "sway": 0.09, "lift": {"F": 0.36, "B": 0.3},
        "touch": {"FL": 0.0, "BR": 0.94, "FR": 0.5, "BL": 0.44}, "ahead": {"F": 0.0, "B": 0.04},
        "toe": {"F": 1.32, "B": 1.26}, "roll": 0.12, "peel": 20.0}  # от запястья до носка; подъём пятки


def clip_walk():
    """D. Шаг на месте (движение — скоростью босса в игре, 10 стадов в секунду): тяжёлый шаг диагональными парами,
    задняя лапа ставится чуть раньше передней; корпус оседает на каждую пару и переваливается. Опорная лапа уходит
    назад ровно со скоростью земли — не скользит."""
    period = WALK["period"]
    c = Clip("walk", "Ходьба", period, loop=True, lag={})
    c.pose(0.0, ST, hold=True).pose(period, ST, hold=True)
    c.feet(0.0, ST).feet(period, ST)
    stride = 10.0 / SCALE * period  # путь за цикл, единицы модели
    duty = WALK["duty"]

    def body(t, tr):
        ph = 2 * math.pi * t / period
        # корпус: оседает сразу после постановки каждой пары лап (ниже всего — через 0.6 рад) и поднимается над
        # опорой; клюёт носом на оседании, переваливается на опорную переднюю лапу, плечо идёт за лапой
        low = 0.6
        add(tr, "Torso", (1.5 * math.cos(2 * (ph - low)), 3.2 * math.sin(ph - 0.1), -3.0 * math.cos(ph)),
            (WALK["sway"] * math.sin(ph - 0.1), 0, -WALK["drop"] - WALK["bob"] * math.cos(2 * (ph - low))))
        # голова гасит качку корпуса с запозданием и кивает после оседания
        add(tr, "Head", (1.9 * math.cos(2 * (ph - low - 0.5)) - 0.7 * math.cos(2 * (ph - low)),
                         -2.0 * math.sin(ph - 0.35), 1.9 * math.cos(ph - 0.25)))
        for name in EARS:
            add(tr, name, (5.0 * math.cos(2 * (ph - low - 0.9)), 0, 0))
        for name, yaw, lag, bob in (("Tail1", 8.0, 0.9, 2.5), ("Tail2", 12.0, 1.7, 4.0), ("Tail3", 12.0, 2.5, 4.0),
                                    ("Tassel", 16.0, 3.3, 6.0)):
            add(tr, name, (bob * math.cos(2 * (ph - lag)), 0, yaw * math.sin(ph - lag)))

    def foot(t, key, st, tr):
        fb = key[0]
        rest = LS["stand"][key]
        toe_len, height = WALK["toe"][fb], rest["w"].z  # от запястья до носка; высота запястья над землёй
        s = (t / period - WALK["touch"][key]) % 1.0
        toe_td = rest["w"].y - stride * duty / 2 - WALK["ahead"][fb] - toe_len  # где носок касается земли
        roll = WALK["roll"]  # последняя доля цикла в опоре, когда пятка уже поднимается
        lift = 0.0
        if s < duty:  # опора: носок уходит назад со скоростью земли
            toe = toe_td + stride * s
            pitch = WALK["peel"] * smooth((s - (duty - roll)) / roll)
        else:  # перенос: вперёд по дуге, в начале и в конце — со скоростью земли (без рывка и проскальзывания)
            u = (s - duty) / (1 - duty)
            y0, m = toe_td + stride * duty, stride * (1 - duty)
            u2, u3 = u * u, u * u * u
            toe = (2 * u3 - 3 * u2 + 1) * y0 + (u3 - 2 * u2 + u) * m + (-2 * u3 + 3 * u2) * toe_td + (u3 - u2) * m
            lift = WALK["lift"][fb] * math.sin(math.pi * u ** 0.9) ** 2
            pitch = WALK["peel"] * (1 - smooth(u / 0.62)) + 5 * bump(u, 0.0, 0.5, 0.2)
        p = math.radians(pitch)
        out = dict(st)
        out["w"] = Vector((rest["w"].x, toe + toe_len * math.cos(p) - height * math.sin(p),
                           lift + toe_len * math.sin(p) + height * math.cos(p)))
        out["q"] = qeuler((pitch, 0, 0))
        out["d"] = Vector((0, 1.0 if fb == "F" else -1.0, 0.2)).normalized()
        out["tu"] = out["tl"] = 0.0
        return out

    c.layers.append(body)
    c.leg_layers.append(foot)
    c.notes.append(f"шаг на месте; цикл {period} с, длина шага {stride * SCALE:.1f} стада при 10 стадах в секунду; "
                   f"опора {duty:.0%} цикла")
    for key, ph in WALK["touch"].items():
        c.event(f"{key} касается земли", round(ph * period % period, 3))
    return c


def clip_heavy_paw():
    """E. «Тяжёлая лапа»: перенос веса → замах правой лапой → удар сверху вперёд → фиксация → возврат.
    Игра начинает выпад на 0.45 с клипа (до этого — замах), попадание — через HitDelay."""
    lead = 0.45
    hit = lead + HIT_DELAY
    c = Clip("heavy_paw", "Тяжёлая лапа", 1.3)
    c.event("начало выпада в игре (AttackAt)", lead).event("контакт: удар лапы", hit)
    bite = A["bite"]
    c.pose(0.0, CB, hold=True, skip=("NemesR",))
    prep = edit(face(CB, lid=LID["half"], brow=(-15, -0.03), jaw=6), Torso={"r": (-1, 3, -2), "o": (0.08, 0.07, -0.03)},
                Head={"r": (-2, -2, 3)})
    c.pose(0.2, prep, only=CORE + EYES)
    up = edit(face(CB, lid=LID["open"], brow=(-17, -0.03), jaw=18, ears=(-6, 4)),
              Torso=((-5.5, 4.0, -6), (0.11, 0.2, -0.07)), Head=((-5, 5, 8), Z3))
    up = with_tail(up, (-34, 0, 0), (-54, 0, 0), (-76, 0, 0), (-88, 0, 0))
    c.pose(lead, up, hold=True, skip=("NemesR",))
    c.pose(hit - 0.08, blend(up, bite, 0.62), only=CORE)
    c.pose(hit, bite, hold=True, skip=("NemesR",))
    squash = edit(face(bite, lid=LID["squint"], brow=(-16, -0.04), jaw=5, ears=(-22, 0)),
                  Head={"r": (6.0, 0, 0)})
    c.pose(hit + 0.08, squash, only=CORE + EYES + EARS)
    c.pose(hit + 0.2, bite, only=CORE)
    back = edit(CB, Torso={"r": (-1.6, 0, 0), "o": (0, 0.04, 0.015)}, Head={"r": (-2.5, 0, 0)})
    c.pose(1.12, back, only=["Torso", "Head"])
    c.pose(1.3, CB, hold=True, skip=("NemesR",))
    # конец платка справа поднят и отведён, пока под ним проходит лапа
    c.pose(0.0, CB, hold=True, only=["NemesR"])
    wing = blend(bite, SL, 0.75)  # конец платка отлетает в сторону, как во сне на кулаке, — лапа проходит под ним
    c.pose(0.2, bite, only=["NemesR"])
    c.pose(0.38, wing, hold=True, only=["NemesR"])
    c.pose(0.56, wing, hold=True, only=["NemesR"])
    c.pose(0.72, bite, only=["NemesR"])
    c.pose(0.95, bite, hold=True, only=["NemesR"])
    c.pose(1.24, CB, hold=True, only=["NemesR"])
    c.pose(1.3, CB, hold=True, only=["NemesR"])
    # — лапы —
    c.feet(0.0, CB)
    c.plant("FR", 0.13)
    cb_fr, hit_fr = LS["combat"]["FR"], LS["bite"]["FR"]
    raise_ = moved(cb_fr, pitch=-30)
    raise_.update(w=Vector((-1.5, -1.2, 1.25)), d=Vector((-0.8, 0.55, 0.1)).normalized())
    c.foot("FR", 0.29, raise_)
    apex = moved(cb_fr, pitch=-55, yaw=-10)
    apex.update(w=Vector((-1.78, -1.3, 2.1)), d=Vector((-0.85, 0.5, -0.1)).normalized())
    c.foot("FR", lead, apex, True)
    drive = moved(hit_fr, pitch=-10)
    drive.update(w=Vector((-1.2, -2.12, 1.1)), d=Vector((-0.7, 0.6, 0.35)).normalized())
    c.foot("FR", hit - 0.07, drive)
    c.foot("FR", hit, hit_fr, True)
    c.plant("FR", 0.9)
    c.step("FR", 0.9, 1.2, cb_fr, lift=0.22, toe=0)
    for key in ("FL", "BL", "BR"):
        c.foot(key, 1.3, LS["combat"][key], True)
    c.foot("FR", 1.3, cb_fr, True)
    c.notes.append("замах идёт 0.45 с до начала выпада в игре; контакт на 0.70 с — ровно через HitDelay после него")
    return c


def clip_tail_strike():
    """F. «Хвост-кистень» (каждый третий удар): короткий замах в другую сторону → таз заносит на 58°, передние лапы
    переступают, голова на цели → хвост по дуге снаружи тела, кисть бьёт сбоку → возврат."""
    lead = 0.5
    hit = lead + HIT_DELAY
    c = Clip("tail_strike", "Хвост-кистень", 1.4, lag={"EarL": 0.03, "EarR": 0.03})  # отставание хвоста — в ключах
    c.event("начало выпада в игре (AttackAt)", lead).event("контакт: удар кисти", hit)
    sw = A["swipe"]
    c.pose(0.0, CB, hold=True)
    # замах: таз чуть в другую сторону, хвост заносится вправо-вверх, взгляд на цели
    ant = edit(face(CB, lid=LID["squint"], brow=(-16, -0.03), jaw=10), Torso=turned(8, 5.0, 0.2), Head=((6, 2, -6), Z3))
    ant = with_tail(ant, (-12, 0, 26), (-36, 0, 58), (-58, 0, 84), (-66, 0, 100))
    c.pose(0.42, ant, hold=True)
    # занос: туловище проходит полпути, хвост ещё отстаёт позади
    mid = edit(blend(ant, sw, 0.5), Torso=turned(-26, 4.0, 0.27), Head=((2, -3, 21), (0, 0, 0.06)))
    mid = with_tail(mid, (-10, 0, 14), (-34, 0, 22), (-62, 0, 22), (-72, 0, 16))
    c.pose(0.6, mid)
    c.pose(hit, sw, hold=True)
    # кисть проскакивает дальше и возвращается
    over = with_tail(edit(sw, Torso={"r": (0, 0, -2.5), "o": (0, 0, -0.02)}), (-6, 0, -38), (-46, 0, -93), (-92, 0, -136),
                     (-108, 0, -168))
    c.pose(hit + 0.07, over, only=["Torso"] + TAIL)
    c.pose(hit + 0.17, sw, only=["Torso"] + TAIL)
    # возврат: туловище назад, хвост тянется следом по той же дуге
    ret = edit(blend(sw, CB, 0.5), Torso=turned(-25, 4.0, 0.23), Head=((4, -2, 20), (0, 0, 0.05)))
    ret = with_tail(ret, (-12, 0, -30), (-38, 0, -56), (-66, 0, -70), (-78, 0, -78))
    c.pose(1.12, ret)
    past = with_tail(edit(CB, Torso=turned(3, 5.0, 0.16)), (-24, 0, 8), (-44, 0, 14), (-66, 0, 16), (-80, 0, 16))
    c.pose(1.29, past, only=["Torso"] + TAIL)
    c.pose(1.4, CB, hold=True)
    # — лапы: правая передняя переступает во время замаха, левая — в начале заноса; задние переносятся прыжком —
    c.feet(0.0, CB)
    c.step("FR", 0.14, 0.38, LS["swipe"]["FR"], lift=0.14, toe=0)
    c.plant("FL", 0.45)
    c.step("FL", 0.45, 0.63, LS["swipe"]["FL"], lift=0.12, toe=0)
    c.plant("BR", 0.44)
    c.hop("BR", 0.44, 0.7, LS["swipe"]["BR"], lift=0.3)
    c.plant("BL", 0.47)
    c.hop("BL", 0.47, 0.73, LS["swipe"]["BL"], lift=0.36)
    for key in LEG:
        c.foot(key, hit, LS["swipe"][key], True)
    c.plant("BR", 0.96)
    c.hop("BR", 0.96, 1.26, LS["combat"]["BR"], lift=0.3)
    c.plant("BL", 0.99)
    c.hop("BL", 0.99, 1.29, LS["combat"]["BL"], lift=0.34)
    c.plant("FL", 1.0)
    c.step("FL", 1.0, 1.18, LS["combat"]["FL"], lift=0.12, toe=0)
    c.plant("FR", 1.16)
    c.step("FR", 1.16, 1.34, LS["combat"]["FR"], lift=0.12, toe=0)
    c.feet(1.4, CB)
    c.notes.append("замах идёт 0.5 с до начала выпада в игре; контакт на 0.75 с; кисть бьёт слева от босса, сбоку")
    return c


def clip_hit():
    """G. Получение урона: голова и плечи отдёргиваются, вес назад, глаза зажмурены — и быстро обратно в стойку."""
    c = Clip("hit", "Получение урона", 14 / 30)
    c.pose(0.0, CB, hold=True)
    rec = edit(face(CB, lid=LID["closed"], brow=(9, 0.05), jaw=13, ears=(-30, 8)),
               Torso={"r": (-4.5, 0, 1.5), "o": (0, 0.12, -0.02)}, Head={"r": (-9, 3, 6)})
    rec = with_tail(rec, (-34, 0, 0), (-58, 0, 0), (-82, 0, 0), (-98, 0, 0))
    c.pose(0.07, rec)
    reb = edit(face(CB, lid=0.1, brow=(-8, -0.01), jaw=9, ears=(-18, 2)), Torso={"r": (1.3, 0, -0.5), "o": (0, -0.025, -0.02)},
               Head={"r": (3.5, 0, -2)})
    c.pose(0.21, reb)
    c.pose(c.dur, CB, hold=True)
    c.feet(0.0, CB).feet(c.dur, CB)
    c.event("пик реакции", 0.07)
    return c


def clip_victory():
    """H. Победа: грудь вперёд, морда вверх, прищур, левая лапа приподнята, хвост довольно машет; в конце — стойка."""
    c = Clip("victory", "Победа", 2.2)
    bark, bark2 = A["bark"], A["bark2"]
    c.pose(0.0, CB, hold=True)
    big = edit(bark, Torso={"r": (-2.5, 0, 0), "o": (0, 0.02, -0.04)}, Head={"r": (-5, 0, 0)})
    c.pose(0.36, big, only=CORE)
    c.pose(0.52, face(bark, lid=0.16, brow=(7, 0.06)))
    c.pose(0.92, face(edit(bark2, Head={"r": (2, -3, 0)}), lid=0.12, brow=(8, 0.07)))
    c.pose(1.32, face(edit(bark, Head={"r": (1, 3, 0)}), lid=0.16, brow=(7, 0.06)))
    c.pose(1.68, face(edit(bark2, Head={"r": (3, -2, 0)}), lid=0.14, brow=(6, 0.05)))
    c.pose(2.2, ST, hold=True)
    c.feet(0.0, CB)
    for key in ("FR", "BL", "BR"):
        c.foot(key, 0.52, LS["bark"][key], True)
        c.foot(key, 1.68, LS["bark"][key], True)
    # левая передняя лапа лениво приподнята, пальцы свисают
    c.plant("FL", 0.4)
    up = moved(LS["bark"]["FL"], pitch=24, bend=(0, 1, 0.15))
    up.update(w=Vector((1.02, -1.3, 1.27)))
    off = moved(LS["bark"]["FL"], dw=(0, -0.08, 0.42), pitch=6, bend=(0, 1, 0.1))
    c.foot("FL", 0.52, off)
    c.foot("FL", 0.7, up, True)
    up2 = moved(up, dw=(0, 0.02, 0.05), pitch=-6)
    c.foot("FL", 1.15, up2)
    c.foot("FL", 1.62, up, True)
    above = moved(LS["stand"]["FL"], dw=(0, -0.05, 0.3), pitch=3, bend=(0, 1, 0.1))
    c.foot("FL", 1.8, above)
    c.foot("FL", 1.94, LS["stand"]["FL"], True)
    c.feet(2.2, ST)
    c.event("лапа поднята", 0.7).event("лапа опущена", 1.94)
    return c


def clip_defeat():
    """I. Поражение: удар отбрасывает, шатается, лапы разъезжаются, падает на грудь, голова кружится — и поднимается
    на четыре лапы (дальше игра ведёт босса домой шагом и укладывает спать)."""
    c = Clip("defeat", "Поражение", 2.4)
    dz = A["dizzy"]
    down, up0 = 0.95, 1.62
    c.event("лежит", down).event("начинает вставать", up0)
    c.pose(0.0, CB, hold=True)
    rec = edit(face(CB, lid=LID["closed"], brow=(10, 0.04), jaw=12, ears=(-32, 6)),
               Torso=((-7, 0, 0), (0, 0.15, -0.2)), Head=((-13, 0, 7), Z3))
    rec = with_tail(rec, (8, 0, 0), (16, 0, 0), (16, 0, 0), (26, 0, 0))
    c.pose(0.13, rec)
    sway1 = edit(face(CB, lid=0.1, lid_r=0.0, brow=(12, 0.03), jaw=14, ears=(-10, 16)),
                 Torso=((2, 5, 4), (0.12, 0.08, -0.25)), Head=((9, -5, -6), Z3))
    c.pose(0.36, sway1)
    sway2 = edit(face(dz, jaw=18), Torso=((4, -1.2, -3), (-0.06, 0.0, -0.39)), Head=((13, 4, 11), Z3))
    c.pose(0.6, sway2, only=CORE + EYES + EARS)
    c.pose(0.8, edit(dz, Torso=((1.5, 0.8, 0), (0.01, 0, -0.565)), Head=((10, 5, 14), (0, -0.06, 0))), only=["Torso", "Head"])
    c.pose(down, dz, hold=True)
    c.pose(up0, dz, hold=True)
    # встаёт: вес с лапы, которая шагает под плечо; грудь вверх; встряхивает головой
    c.pose(1.78, edit(dz, Torso=((-2, -3, 0), (-0.04, 0, -0.585)), Head=((6, 4, 8), (0, -0.04, 0))), only=["Torso", "Head"])
    rise = edit(face(ST, lid=0.12, lid_r=0.3, brow=(8, 0.02), jaw=8), Torso=((-6, 2, 0), (0.03, 0.02, -0.47)), Head=((6, 2, 3), Z3))
    c.pose(1.98, rise, only=CORE + EYES + EARS)
    c.pose(2.14, edit(ST, Torso=((-8, 0, 0), (0, 0.03, -0.26)), Head=((3, 2, 8), Z3)), only=["Torso", "Head"])
    c.pose(2.27, edit(ST, Torso=((-2.5, 0, 0), (0, 0, -0.07)), Head=((-2, -1, -6), Z3)), only=["Torso", "Head"])
    c.pose(2.4, ST, hold=True)

    def wobble(t, tr):
        k = bump(t, down - 0.1, up0 + 0.15, down + 0.25)
        add(tr, "Head", (2 * k * math.sin((t - down) * 9), 3 * k * math.cos((t - down) * 7), 8 * k * math.sin((t - down) * 7)))
        add(tr, "EarL", (0, 6 * k * math.sin((t - down) * 11), 0))
        add(tr, "Tassel", (0, 0, 10 * k * math.sin((t - down) * 8)))

    c.layers.append(wobble)
    # — лапы: левая оступается, потом обе передние разъезжаются локтями наружу; встаёт, переставляя их под плечи —
    c.feet(0.0, CB)
    c.plant("FL", 0.15)
    spot = moved(LS["combat"]["FL"], dw=(0.26, -0.24, 0))
    c.step("FL", 0.15, 0.33, spot, lift=0.14)
    c.plant("FL", 0.4)
    slip = mix_state(spot, LS["dizzy"]["FL"], 0.6)
    slip["w"].z = 0.55
    c.foot("FL", 0.6, slip)
    c.foot("FL", 0.82, LS["dizzy"]["FL"], True)
    c.plant("FR", 0.3)
    slip = mix_state(LS["combat"]["FR"], LS["dizzy"]["FR"], 0.62)
    slip["w"].z = 0.55
    c.foot("FR", 0.5, slip)
    c.foot("FR", 0.74, LS["dizzy"]["FR"], True)
    for key in ("BL", "BR"):
        c.foot(key, down, LS["dizzy"][key], True)
        c.foot(key, up0, LS["dizzy"][key], True)
    c.plant("FL", up0 + 0.04)
    c.step("FL", up0 + 0.04, 1.92, LS["stand"]["FL"], lift=0.22, knee=(0.3, 1.0))
    c.plant("FR", 1.88)
    c.step("FR", 1.88, 2.14, LS["stand"]["FR"], lift=0.22, knee=(0.3, 1.0))
    c.feet(2.4, ST)
    c.notes.append("передние лапы при падении разъезжаются по земле намеренно (0.3–0.8 с)")
    return c


def clip_fall_asleep():
    """J. Возвращение ко сну (дома, состояние FallAsleep): лапы вперёд, ложится на грудь, правая лапа поднимается,
    переворачивается и встаёт кулаком, голова опускается на неё, глаза закрываются."""
    c = Clip("fall_asleep", "Засыпание", 1.6)
    t1 = 0.88
    c.event("лёг (поза «лёжа»)", t1)
    c.pose(0.0, ST, hold=True)
    c.pose(0.2, edit(ST, Torso=((3, -2.5, 0), (-0.03, 0, -0.1)), Head=((-3, 1, 0), Z3)), only=["Torso", "Head"])
    low = edit(face(ST, lid=LID["half"], brow=(0, 0.0)), Torso=((7.0, 2.5, 0), (0.03, 0.0, -0.3)), Head=((-7, -1, 0), Z3))
    c.pose(0.5, low, only=CORE + EYES)
    c.pose(t1, AL, skip=("NemesR",))
    c.pose(0.84, AL, only=["NemesR"])
    c.pose(1.12, SL, hold=True, only=["NemesR"])
    # голова приподнята и повёрнута, пока лапа встаёт; потом опускается на кулак
    wait = edit(face(AL, lid=0.3, brow=(-2, 0.0), brow_r=(4, 0.04)), Head=((-9, -5, 9), (-0.02, 0, 0.0)),
                Torso={"r": (-0.5, 0.5, 0), "o": (0.0, 0, 0.045)})
    c.pose(1.14, wait, only=CORE + EYES)
    near = edit(face(SL, lid=0.14, lid_r=0.1, brow=(2, 0.0), brow_r=(5, 0.02)), Head={"r": (-4, 1.5, 0), "o": (0, 0, 0.05)})
    c.pose(1.44, near, only=CORE + EYES)
    c.pose(1.6, SL, hold=True)
    # — лапы —
    c.feet(0.0, ST)
    c.plant("FL", 0.06)
    c.step("FL", 0.06, 0.38, LS["sleep"]["FL"], lift=0.22)
    c.plant("FR", 0.36)
    c.step("FR", 0.36, 0.68, LS["alert"]["FR"], lift=0.22, toe=0)
    for key in ("BL", "BR"):
        c.foot(key, t1, LS["alert"][key], True)
    c.plant("FR", 0.92)
    a, b = LS["alert"]["FR"], LS["sleep"]["FR"]
    off = mix_state(a, b, 0.1)
    off.update(w=Vector((-1.0, -1.92, 0.78)), q=qeuler((-7, 0, 0)))
    c.foot("FR", 1.03, off)
    edge = mix_state(a, b, 0.5)
    edge.update(w=Vector((-1.22, -2.06, 0.98)), q=EDGE_OUT)
    c.foot("FR", 1.16, edge)
    c.foot("FR", 1.36, b, True)
    c.feet(1.6, SL)
    return c


CLIPS = {"sleep_idle": clip_sleep, "wake": clip_wake, "combat_idle": clip_combat, "walk": clip_walk,
         "heavy_paw": clip_heavy_paw, "tail_strike": clip_tail_strike, "hit": clip_hit, "victory": clip_victory,
         "defeat": clip_defeat, "fall_asleep": clip_fall_asleep}
# С какой опорной позы клип начинается и какой кончается (проверка стыков).
START = {"wake": "sleep", "heavy_paw": "combat", "tail_strike": "combat", "hit": "combat", "victory": "combat",
         "defeat": "combat", "fall_asleep": "stand"}
END = {"wake": "combat", "heavy_paw": "combat", "tail_strike": "combat", "hit": "combat", "victory": "stand",
       "defeat": "stand", "fall_asleep": "sleep"}


# ── «Хвост-кистень», вариант C: взмах хвостом и удар левой передней лапой ─────────────────────────────────────
# Утверждён владельцем 2026-11-12 вместо прежнего клипа (58°, бьёт кисть; он остаётся как clip_tail_strike_v1 и
# в экспорт не входит). Игрок в расчётах — фигура перед мордой босса: по ней ставится контакт лапы.

PLAYER_AHEAD = 8.5  # стадов от центра босса до игрока: босс подходит на 8–9 (Config/Battle: AttackRange 9.5)
PLAYER_RADIUS, PLAYER_HEIGHT = 1.0, 5.2
PLAYER_HALF = (1.95, 0.5)  # полуширина фигуры игрока с руками и её полутолщина (игрок стоит лицом к боссу)


def turned_about(yaw, pitch, drop, about=-1.0, shift=(0.0, 0.0)):
    """Туловище, повёрнутое вокруг вертикали y = about, сдвинутое на shift и опущенное на drop."""
    rot, off = M.pivot_turn(yaw, pitch, about=about)
    return (rot, (off[0] + shift[0], off[1] + shift[1], -drop))


STRIKE_LEG = ("FUpperL", "FLowerL", "FPawL")


def figure_gap_points(pts, ahead=PLAYER_AHEAD):
    """Расстояние от набора точек (стады) до фигуры игрока — прямоугольника с руками. Минус — точки зашли внутрь
    (на столько стадов)."""
    dx = np.abs(pts[:, 0]) - PLAYER_HALF[0]
    dy = np.abs(pts[:, 1] + ahead) - PLAYER_HALF[1]
    dz = pts[:, 2] - PLAYER_HEIGHT
    out = np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dy, 0) ** 2 + np.maximum(dz, 0) ** 2)
    inside = (dx < 0) & (dy < 0) & (dz < 0)
    if inside.any():
        return -float(np.minimum(np.minimum(-dx, -dy), -dz)[inside].max())
    return float(out.min())


def part_gaps(mats, ahead=PLAYER_AHEAD):
    """Часть → расстояние до фигуры игрока в этой позе."""
    return {name: figure_gap_points(pts, ahead) for name, pts in M.world_points(mats).items()}


def combo_stance(yaw, about=-1.0, shift=(0.0, 0.0), follow_front=0.45, head_yaw=None, drop=0.3, pitch=3.0):
    """Поза разворота для двухфазной атаки: как утверждённая tailWhip (ось между передними лапами, передние лапы
    переступают на долю follow_front), но с любым углом. Левая передняя лапа здесь стоит — бьёт она в клипе."""
    torso = turned_about(yaw, pitch, drop, about, shift)
    follow = {"FL": follow_front, "FR": follow_front, "BL": 1.0, "BR": 1.0}
    feet = {"FL": (0.12, 0, 0, 0, yaw * 0.3), "FR": (-0.12, 0, 0, 0, yaw * 0.3), "BL": (0.1, -0.15, 0, 0, yaw),
            "BR": (-0.1, 0.15, 0, 0, yaw)}
    pose = M._merge("combat", M.plant(torso, follow=follow, **feet),
                    M.tail((-6, 0, -34), (-46, 0, -84), (-90, 0, -120), (-104, 0, -146)), Torso=torso,
                    Head=((0, -6, -yaw * 0.8 if head_yaw is None else head_yaw), (0, 0, 0.14)), Jaw=(M.X(6), M.Z3),
                    **M.lids(M.SQUINT), NemesL=((-30, -6, 0), (0, 0, 0.25)), NemesR=((0, 10, 0), M.Z3))
    return ground(M.pose_tr(pose))


def studs(x, y, z):
    """Точка в стадах от центра босса (x — влево от босса, −y — к игроку) → единицы модели."""
    return Vector((x, y, z)) / SCALE


PAW_LOCAL = (M.POINTS["FPawL"] - np.array(RIG["FPawL"][1])) * SCALE
PAW_OF = {leg[2]: key for key, leg in LEG.items()}


def paw_points(st):
    """Точки левой передней лапы в мире (стады) по её состоянию (если запястье дотягивается до цели)."""
    m = np.array(st["q"].to_matrix())
    return PAW_LOCAL @ m.T + np.array(st["w"] * SCALE)


def side_depth(pts, ahead=PLAYER_AHEAD):
    """На сколько стадов точки зашли в фигуру игрока с его правого бока (со стороны +x): 0 — касание боковой
    грани, плюс — глубже, минус — не дошли. Считаются точки на уровне фигуры по y и по высоте."""
    slab = (np.abs(pts[:, 1] + ahead) < PLAYER_HALF[1]) & (pts[:, 2] < PLAYER_HEIGHT) & (pts[:, 2] > 0)
    if not slab.any():
        return -99.0
    return float(PLAYER_HALF[0] - pts[slab, 0].min())


def settle(st, along, want, span=4.0):
    """Сдвинуть лапу вдоль направления along так, чтобы она заходила в бок фигуры игрока ровно на want стадов.
    Возвращает новое состояние и сдвиг в стадах."""
    along = Vector(along).normalized()

    def depth(s):
        out = dict(st)
        out["w"] = st["w"] + along * (s / SCALE)
        return side_depth(paw_points(out)), out

    lo, hi = -span, span  # при lo лапа далеко, при hi — глубоко
    if depth(lo)[0] > want or depth(hi)[0] < want:
        print("SETTLE: цель вне диапазона", round(depth(lo)[0], 2), round(depth(hi)[0], 2))
    for _ in range(30):
        mid = (lo + hi) / 2
        if depth(mid)[0] < want:
            lo = mid
        else:
            hi = mid
    return depth(hi)[1], hi


# Времена ключей двухфазной пробы, секунды от начала клипа.
COMBO_T = {"prep": 0.18, "turn1": 0.34, "turn2": 0.48, "whip": 0.57, "cock": 0.635, "hit": 0.75, "press": 0.785,
           "release": 0.81, "fl_down": 1.0, "ret": 1.14, "past": 1.3}
PRESS_DEPTH = 0.4
BLADE_Y = float(os.environ.get("BLADE_Y", "0.19"))  # на сколько лопатка отходит назад по корпусу в ударе
BLADE_DOWN = float(os.environ.get("BLADE_DOWN", "1.15"))  # доля сдвига лопатки, когда лапа встала на место
BLADE_RET = float(os.environ.get("BLADE_RET", "0.4"))  # и в середине возврата корпуса  # на сколько стадов подошва заходит в бок фигуры игрока в момент контакта


def build_combo(yaw, name, title):
    """F. «Хвост-кистень», вариант C (утверждён владельцем 2026-11-12): взмах хвостом и удар левой передней лапой.
    yaw — наибольший разворот корпуса вокруг передних лап (минус — таз уходит влево). 0–0.18 с: перенос веса, правая передняя лапа отступает, хвост заносится вправо-вверх.
    0.18–0.48: корпус разворачивается вокруг передних лап (как в утверждённом клипе), зад переносится одним
    заносом — обе передние лапы в это время стоят. 0.40–0.60: хвост широкой дугой обходит левый бок (кисть до
    игрока не достаёт — это замах всем телом). 0.47–0.63: левая передняя лапа поднимается и отводится в сторону.
    0.63–0.75: корпус доворачивает, лапа подошвой бьёт игрока сбоку. 0.75: контакт (единственный момент урона).
    Дальше: лапа возвращается на место, зад заносится обратно, правая передняя подтягивается."""
    lead = 0.5
    hit = lead + HIT_DELAY
    T = COMBO_T
    c = Clip(name, title, 1.4, lag={"EarL": 0.03, "EarR": 0.03})
    c.event("начало выпада в игре (AttackAt)", lead).event("взмах хвоста: кисть на дуге", T["whip"])
    c.event("контакт: удар лапы", hit)
    sw = combo_stance(yaw)
    land = combo_stance(yaw * 0.9)  # задние лапы встают чуть раньше конца разворота: корпус доворачивает над ними
    c.pose(0.0, CB, hold=True)
    # — перенос веса и замах: корпус чуть в другую сторону и на левый бок, хвост заносится вправо-вверх —
    ant = edit(face(CB, lid=LID["squint"], brow=(-16, -0.03), jaw=9), Torso=turned(7, 4.0, 0.2), Head=((3, 2, -5), Z3))
    ant = edit(ant, Torso={"r": (0, 2.0, 0), "o": (0.03, 0.03, 0)})
    ant = with_tail(ant, (-12, 0, 26), (-36, 0, 58), (-58, 0, 84), (-66, 0, 100))
    c.pose(T["prep"], ant, hold=True, skip=TAIL)
    c.pose(T["prep"] + 0.06, ant, hold=True, only=TAIL)  # хвост доходит до замаха чуть позже корпуса
    # — разворот: туловище проходит без остановки, хвост сначала отстаёт позади, потом хлещет —
    m1 = edit(blend(ant, sw, 0.45), Torso=turned(yaw * 0.38, 4.0, 0.27), Head=((2, -3, -yaw * 0.31), (0, 0, 0.06)))
    m1 = with_tail(m1, (-10, 0, 14), (-34, 0, 22), (-62, 0, 22), (-72, 0, 16))
    c.pose(T["turn1"], m1, skip=TAIL)
    c.pose(T["turn1"] + 0.06, m1, only=TAIL)
    m2 = edit(blend(ant, sw, 0.85), Torso=turned(yaw * 0.83, 3.5, 0.3), Head=((1, -5, -yaw * 0.65), (0, 0, 0.12)))
    c.pose(T["turn2"], m2, skip=TAIL)
    # кисть проходит широкую дугу, чуть проскакивает дальше позы и оседает
    whip = with_tail(sw, (-6, 0, -34), (-46, 0, -84), (-90, 0, -120), (-104, 0, -146))
    over = with_tail(sw, (-6, 0, -37), (-46, 0, -90), (-91, 0, -130), (-106, 0, -160))
    c.pose(T["whip"], whip, only=TAIL)
    c.pose(T["whip"] + 0.07, over, only=TAIL)
    c.pose(T["whip"] + 0.18, whip, only=TAIL, hold=True)
    # — довод корпуса в удар лапой: вес на правую переднюю и зад, левое плечо идёт вперёд, морда на игроке —
    cock = edit(sw, Torso=turned(yaw * 0.93, 2.0, 0.24), Head=((1, -6, -yaw * 0.74), (0, 0, 0.14)))
    cock = face(edit(cock, Torso={"r": (0, -3.5, 0), "o": (0.05, 0.1, 0)}), lid=LID["half"], brow=(-17, -0.03), jaw=13)
    c.pose(T["cock"], cock, skip=TAIL)
    strike = edit(sw, Torso=turned(yaw * 0.975, 3.5, 0.33), Head=((2, -8, -yaw * 0.8), (0, 0, 0.14)))
    strike = face(edit(strike, Torso={"r": (0, 3.5, 0), "o": (0.09, 0.16, 0)}), lid=LID["open"], brow=(-18, -0.04), jaw=17,
                  ears=(-10, 4))
    c.pose(hit, strike, skip=TAIL)
    press = edit(sw, Torso=turned(yaw, 3.8, 0.37), Head=((3, -8, -yaw * 0.8), (0, 0, 0.14)))
    press = face(edit(press, Torso={"r": (0, 4.5, 0), "o": (0.09, 0.16, 0)}), lid=LID["squint"], brow=(-17, -0.04), jaw=7,
                 ears=(-20, 0))
    c.pose(T["press"] + 0.025, press, hold=True, skip=TAIL)
    c.pose(T["fl_down"], edit(sw, Torso=turned(yaw * 0.95, 3.5, 0.3)), skip=TAIL)
    # — возврат: туловище назад, хвост тянется следом по той же дуге —
    ret = edit(blend(sw, CB, 0.5), Torso=turned(yaw * 0.43, 4.0, 0.23), Head=((4, -2, -yaw * 0.34), (0, 0, 0.05)))
    ret = with_tail(ret, (-12, 0, -30), (-38, 0, -56), (-66, 0, -70), (-78, 0, -78))
    c.pose(T["ret"], ret)
    past = with_tail(edit(CB, Torso=turned(3, 5.0, 0.16)), (-24, 0, 8), (-44, 0, 14), (-66, 0, 16), (-80, 0, 16))
    c.pose(T["past"], past, only=["Torso"] + TAIL)
    c.pose(1.4, CB, hold=True)

    # — лапы —
    cb, ls, ll = LS["combat"], {key_: leg_state(sw, key_) for key_ in LEG}, {key_: leg_state(land, key_) for key_ in LEG}
    c.feet(0.0, CB)
    # правая передняя отступает под будущее место плеча, пока вес уходит на левый бок
    c.plant("FR", 0.02)
    c.step("FR", 0.02, 0.18, ls["FR"], lift=0.1, toe=0)
    # зад заносится влево одним подскоком; обе передние лапы стоят
    c.plant("BR", 0.19)
    c.hop("BR", 0.19, 0.45, ll["BR"], lift=0.28)
    c.plant("BL", 0.21)
    c.hop("BL", 0.21, 0.47, ll["BL"], lift=0.32)
    # левая передняя: подъём назад-вверх и отвод в сторону (мимо игрока) → удар подошвой по игроку сбоку → возврат
    blade = Vector((0.03, BLADE_Y, 0.0))  # лопатка скользит назад по корпусу — плечо не упирается в игрока
    c.foot("FL", 0.47, moved(cb["FL"], off=blade * 0.8), True)
    home = cb["FL"]["w"]
    contact = moved(cb["FL"], yaw=12, roll=80)
    contact.update(w=studs(3.3, -7.0, 3.05), d=Vector((0.45, 0.7, 0.55)).normalized(), off=blade)
    contact, _ = settle(contact, (-1.0, 0.0, 0.0), PRESS_DEPTH)
    cockst = moved(cb["FL"], yaw=30, roll=42, pitch=-8)
    cockst.update(w=contact["w"] + studs(2.35, 1.15, 1.1), d=Vector((0.3, 0.85, 0.42)).normalized(), off=blade)
    peel = moved(cb["FL"], yaw=6, roll=8, pitch=-10)
    peel.update(w=home + studs(0.3, 0.35, 0.55), d=Vector((0.1, 0.97, 0.2)).normalized())
    c.foot("FL", 0.52, peel)
    rise = moved(cb["FL"], yaw=17, roll=22, pitch=-13)
    rise.update(w=home.lerp(cockst["w"], 0.6) + studs(0.1, 0.5, 0.35), d=Vector((0.22, 0.92, 0.32)).normalized(),
                off=blade * 0.6)
    c.foot("FL", 0.58, rise)
    c.foot("FL", T["cock"], cockst, True)
    c.foot("FL", hit, contact)
    pressst = moved(contact, dw=tuple(studs(-0.25, 0, 0)))
    c.foot("FL", T["press"], pressst, True)
    c.foot("FL", T["release"], pressst, True)
    # возврат: лапа отходит от игрока в сторону и назад, разворачивается подошвой вниз и встаёт на своё место
    span = T["fl_down"] - T["release"]
    off1 = moved(cb["FL"], yaw=14, roll=52, pitch=-6)
    off1.update(w=pressst["w"].lerp(home, 0.3) + studs(0.7, 0.0, 0.45), d=Vector((0.35, 0.8, 0.5)).normalized(),
                off=blade)
    c.foot("FL", T["release"] + span * 0.36, off1)
    off2 = moved(cb["FL"], yaw=6, roll=16, pitch=-8)
    off2.update(w=pressst["w"].lerp(home, 0.78) + studs(0.3, 0.0, 0.55), d=Vector((0.15, 0.95, 0.3)).normalized(),
                off=blade)
    c.foot("FL", T["release"] + span * 0.72, off2)
    c.foot("FL", T["fl_down"], moved(cb["FL"], off=blade * BLADE_DOWN), True)
    c.foot("FL", T["ret"], moved(cb["FL"], off=blade * BLADE_RET), False)
    # зад обратно; обе передние стоят
    c.plant("BR", 0.97)
    c.hop("BR", 0.97, 1.21, cb["BR"], lift=0.28)
    c.plant("BL", 1.0)
    c.hop("BL", 1.0, 1.24, cb["BL"], lift=0.3)
    # правая передняя подтягивается на место
    c.plant("FR", 1.24)
    c.step("FR", 1.24, 1.39, cb["FR"], lift=0.09, toe=0)
    c.feet(1.4, CB)
    c.notes.append("экспериментальный вариант: не заменяет tail_strike")
    c.contact_state = contact
    return c



def clip_tail_combo():
    """F. «Хвост-кистень» в рабочем наборе — вариант C, разворот 58° (поза swipe и места задних лап прежние)."""
    c = build_combo(-58.0, "tail_strike", "Хвост-кистень")
    c.notes[:] = ["вариант C: взмах хвостом 0.40–0.60 с, контакт левой лапой на 0.75 с — ровно через HitDelay после"
                  " начала выпада; замах идёт 0.5 с до начала выпада в игре"]
    return c


clip_tail_strike_v1 = clip_tail_strike
CLIPS["tail_strike"] = clip_tail_combo


# ── Проверки по кадрам ───────────────────────────────────────────────────────────────────────────────────────

CONTACT = 0.05  # стады: лапа считается опорной, если её носок не выше
# Носок каждой лапы в координатах модели (середина переднего края подошвы).
TOE = {"FL": Vector((M.FX, -2.3, 0.0)), "FR": Vector((-M.FX, -2.3, 0.0)), "BL": Vector((M.BX, 0.54, 0.0)),
       "BR": Vector((-M.BX, 0.54, 0.0))}


def pair_kind(pair):
    """fold — складка лапы или лапа под корпусом; joint — стык головы, шеи, платка, основания хвоста; real — прочее."""
    a, b = pair.split("+")

    def leg(n):
        return n[0] in "FB" and n[1:].rstrip("LR") in ("Upper", "Lower", "Paw")

    def head(n):
        return n in ("Head", "Jaw") or n[:-1] in ("Nemes", "Ear", "Eyelid", "Brow")

    if (leg(a) and leg(b) and a[0] == b[0] and a[-1] == b[-1]) or (leg(a) and b == "Torso") or (leg(b) and a == "Torso"):
        return "fold"
    if (head(a) and head(b)) or {a, b} in ({"Tail1", "Torso"}, {"Head", "Torso"}, {"Jaw", "Torso"}):
        return "joint"
    return "real"


def diagnose(clip, frames, speed=0.0, clash_every=2):
    """Отчёт по кадрам клипа: провал под землю, скольжение опорных лап (speed — скорость земли назад, стадов в
    секунду, для шага на месте), пересечения частей, наибольший шаг сустава за кадр, стык цикла."""
    n = len(frames)
    dt = 1.0 / FPS
    rep = {"frames": n, "duration": round(clip.dur, 3), "short": round(clip.short * SCALE, 3)}
    sink, sink_at = 0.0, ""
    slide = {k: 0.0 for k in LEG}
    run = {k: 0.0 for k in LEG}
    contact_frames = {k: 0 for k in LEG}
    prev = None
    clashes = {}
    step_max, step_at = 0.0, ""
    lows_by_part, highs_by_part, sink_parts = {}, {}, {}
    seq = list(range(n)) + ([0] if clip.loop else [])
    for idx, i in enumerate(seq):
        tr = frames[i]
        mats = M.tr_matrices(tr)
        world = M.world_points(mats)
        lows = {g: float(w[:, 2].min()) for g, w in world.items()}
        for g, z in lows.items():
            lows_by_part[g] = min(lows_by_part.get(g, 9.0), z)
            highs_by_part[g] = max(highs_by_part.get(g, -9.0), z)
            if z < -0.03 and z < sink_parts.get(g, (0.0, 0.0))[0]:
                sink_parts[g] = (z, i * dt)
        who = min(lows, key=lows.get)
        if lows[who] < sink:
            sink, sink_at = lows[who], f"{who} на {i * dt:.2f} с"
        state = {}
        for key, leg in LEG.items():  # опора — по носку лапы: он на земле и при поднятой пятке
            toe = mats[leg[2]] @ ((TOE[key] - Vector(RIG[leg[2]][1])) * SCALE)
            state[key] = (toe.z < CONTACT, Vector((toe.x, toe.y)))
        if prev is not None:
            for key in LEG:
                if state[key][0] and prev[key][0]:
                    d = state[key][1] - prev[key][1] - Vector((0.0, speed * dt))
                    run[key] += d.length
                    contact_frames[key] += 1
                else:
                    slide[key] = max(slide[key], run[key])
                    run[key] = 0.0
            for p in RIG:
                ang = math.degrees(frames[seq[idx - 1]][p][0].rotation_difference(tr[p][0]).angle)
                if ang > step_max:
                    step_max, step_at = ang, f"{p} на {i * dt:.2f} с"
        prev = state
        if idx % clash_every == 0 and idx < n:
            for pair, (v, base) in M.new_clashes(mats).items():
                if v > clashes.get(pair, (0.0,))[0]:
                    clashes[pair] = (v, base, round(i * dt, 2))
    for key in LEG:
        slide[key] = max(slide[key], run[key])
    rep["sink"] = round(-sink, 3)
    rep["sink_at"] = sink_at if sink < -0.005 else ""
    rep["slide"] = {k: round(v, 3) for k, v in slide.items()}
    rep["contact_share"] = {k: round(v / max(n - 1, 1), 2) for k, v in contact_frames.items()}
    rep["step_max_deg"] = round(step_max, 1)
    rep["step_at"] = step_at
    rep["clash_real"] = {k: v for k, v in clashes.items() if pair_kind(k) == "real"}
    rep["clash_joint"] = {k: v for k, v in clashes.items() if pair_kind(k) == "joint"}
    rep["clash_fold_max"] = round(max([v[0] for k, v in clashes.items() if pair_kind(k) == "fold"] or [0.0]), 2)
    rep["sink_parts"] = {g: (round(-z, 3), round(t, 2)) for g, (z, t) in sink_parts.items()}
    rep["short_by"] = {k: (round(v * SCALE, 3), round(t, 2)) for k, (v, t) in clip.short_by.items() if v * SCALE > 0.02}
    rep["low_range"] = {g: (round(lows_by_part[g], 3), round(highs_by_part[g], 3)) for g in lows_by_part}
    rep["events"] = {k: round(v, 3) for k, v in clip.events.items()}
    return rep


def pose_gap(a, b):
    """Наибольшее расхождение двух поз: (градусы, стады)."""
    ang = max(math.degrees(a[p][0].rotation_difference(b[p][0]).angle) for p in RIG)
    pos = max((a[p][1] - b[p][1]).length for p in RIG) * SCALE
    return round(ang, 3), round(pos, 4)


# ── Кадры: готовая модель v2 из открытого .blend ─────────────────────────────────────────────────────────────

SCENE = bpy.context.scene
PARTS = {o.name.rsplit("_", 1)[1]: o for o in SCENE.objects if o.name.startswith("Boss4_Sphinx")}
HAVE_MODEL = len(PARTS) == len(RIG)

# Камеры: (точка, куда смотрит, фокусное). Модель стоит мордой к −y, левый бок — +x.
CAMS = {
    "34": ((28.3, -36.2, 12.5), (0.0, 0.5, 7.4), 42),  # как на утверждённых листах: слева-спереди
    "34r": ((-28.3, -36.2, 12.5), (0.0, 0.5, 7.4), 42),  # справа-спереди: видна правая лапа
    "front": ((0.0, -46.0, 10.5), (0.0, 0.0, 7.6), 42),  # как видит игрок
    "side": ((54.0, 0.5, 10.0), (0.0, 0.5, 7.6), 46),  # левый бок
    "top": ((0.0, 1.0, 76.0), (0.0, 1.0, 0.0), 40),
    "close": ((16.0, -26.0, 9.5), (-0.5, -4.5, 8.0), 50),  # крупно (квадратный кадр): голова и передние лапы
    "wide34": ((34.0, -43.5, 14.5), (1.5, 0.0, 6.5), 42),  # шире: атака хвостом
}


def setup_scene():
    for o in SCENE.objects:
        if o.name.startswith("Mannequin"):
            o.hide_render = True
    SCENE.render.fps = FPS
    props = SCENE.render.image_settings.bl_rna.properties
    if "media_type" in props:
        SCENE.render.image_settings.media_type = "IMAGE"
    SCENE.render.image_settings.file_format = "PNG"
    floor = SCENE.objects.get("Floor")
    if floor:
        floor.scale = (2.2, 3.6, 3.6)


def show(tr, shift=(0.0, 0.0, 0.0)):
    mats = M.tr_matrices(tr)
    move = Matrix.Translation(shift)
    for name, obj in PARTS.items():
        obj.matrix_world = move @ mats[name]


def shoot(path, view, res):
    eye, target, lens = CAMS[view]
    floor = SCENE.objects.get("Floor")
    if floor:  # задник студии — позади модели относительно камеры (для вида сбоку разворачивается)
        floor.rotation_euler = (0.0, 0.0, math.pi / 2 if view == "side" else 0.0)
        floor.location = (-14.0, 0.0, 0.0) if view == "side" else (0.0, 14.0, 0.0)
    cam = SCENE.camera
    cam.data.lens = lens
    cam.location = eye
    cam.rotation_euler = (Vector(eye) - Vector(target)).to_track_quat("Z", "Y").to_euler()
    SCENE.render.resolution_x, SCENE.render.resolution_y = res
    SCENE.render.filepath = path
    bpy.ops.render.render(write_still=True)


MARKS = []


def ground_marks(on):
    """Полосы на земле для шага на месте: по ним видно, что опорная лапа не скользит."""
    if on and not MARKS:
        mat = bpy.data.materials.new("GroundMark")
        mat.use_nodes = True
        bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = (0.32, 0.36, 0.46, 1)
        for i in range(-6, 7):
            mesh = bpy.data.meshes.new("GroundMark")
            mesh.from_pydata([(-13, -0.22, 0.02), (13, -0.22, 0.02), (13, 0.22, 0.02), (-13, 0.22, 0.02)], [],
                             [(0, 1, 2, 3)])
            mesh.materials.append(mat)
            obj = bpy.data.objects.new("GroundMark", mesh)
            SCENE.collection.objects.link(obj)
            MARKS.append((obj, i * 6.0))
    for obj, _ in MARKS:
        obj.hide_render = not on


def move_marks(distance):
    for obj, base in MARKS:
        obj.location = (0.0, (base + distance + 39.0) % 78.0 - 39.0, 0.0)


def render_clip(name, frames, view, res, every=1, speed=0.0, prefix=""):
    """Кадры клипа одной камерой: <папка>/<имя>_<камера>/<номер>.png. speed — земля бежит назад (шаг на месте)."""
    folder = os.path.join(OUT, f"{prefix}{name}_{view}")
    os.makedirs(folder, exist_ok=True)
    ground_marks(speed != 0.0)
    for i in range(0, len(frames), every):
        if speed:
            move_marks(speed * i / FPS)
        show(frames[i])
        shoot(os.path.join(folder, f"{i:04d}.png"), view, res)
    return folder


# ── Запуск ───────────────────────────────────────────────────────────────────────────────────────────────────

SPEED = {"walk": 10.0}  # стадов в секунду: скорость босса в бою и по дороге домой (Config/Battle)
SHEET_VIEWS = {"sleep_idle": ("close",), "wake": ("close",), "combat_idle": ("34",), "walk": ("side",),
               "heavy_paw": ("34r",), "tail_strike": ("top",), "hit": ("34",), "victory": ("34",),
               "defeat": ("34",), "fall_asleep": ("close",)}
AX = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))  # оси Roblox: (x, y, z) Blender → (x, z, −y) Roblox



def half_rate_error(frames, loop):
    """Если хранить клип вдвое реже (15 кадров в секунду) и восстанавливать пропущенные кадры так, как это делает
    игра (CFrame:Lerp суставов): наибольший уход носка лапы от настоящего кадра и наибольший провал, стады."""
    n = len(frames)
    worst, sink = 0.0, 0.0
    for i in range(1, n - (0 if loop else 1), 2):
        mid = blend(frames[i - 1], frames[(i + 1) % n], 0.5)
        got, ref = M.tr_matrices(mid), M.tr_matrices(frames[i])
        for key, leg in LEG.items():
            local = (TOE[key] - Vector(RIG[leg[2]][1])) * SCALE
            worst = max(worst, ((got[leg[2]] @ local) - (ref[leg[2]] @ local)).length)
        sink = min(sink, min(float(w[:, 2].min()) for w in M.world_points(got).values()))
    return {"toe_error": round(worst, 3), "sink": round(-sink, 3)}


selftest()
report = {"fps": FPS, "clips": {}}
baked = {}
for name, make in CLIPS.items():
    if ONLY and name not in ONLY:
        continue
    clip = make()
    frames = clip.frames()
    baked[name] = (clip, frames)
    rep = diagnose(clip, frames, SPEED.get(name, 0.0))
    if not clip.loop:
        rep["ends"] = {"start": pose_gap(frames[0], A[START[name]]) if name in START else None,
                       "end": pose_gap(frames[-1], A[END[name]]) if name in END else None}
    rep["half_rate"] = half_rate_error(frames, clip.loop)
    times = set()
    for keys in list(clip.body.values()) + list(clip.legs.values()):
        times.update(round(k[0], 3) for k in keys)
    rep["key_times"] = len(times)
    rep["title"], rep["loop"], rep["notes"] = clip.title, clip.loop, clip.notes
    rep["start"], rep["end"] = START.get(name), END.get(name)
    report["clips"][name] = rep
    print("DIAG", name, json.dumps(rep, ensure_ascii=False))

for spec in [d for d in os.environ.get("SPHINX_DEBUG", "").split(";") if d]:  # клип:время:лапа — где суставы
    name, when, key = spec.split(":")
    clip = baked[name][0]
    tr, _ = clip.sample(float(when))
    mats = M.tr_matrices(tr)
    world = M.world_points(mats)
    up, lo, paw, _ = LEG[key]
    print("DEBUG", spec, "torso", [round(c, 2) for c in tr["Torso"][1]],
          [round(math.degrees(a), 1) for a in tr["Torso"][0].to_euler("XYZ")],
          "плечо", [round(c / SCALE, 2) for c in mats[up].translation], "локоть", [round(c / SCALE, 2) for c in mats[lo].translation],
          "запястье", [round(c / SCALE, 2) for c in mats[paw].translation],
          "сгиб", [round(c, 2) for c in clip.leg_at(key, float(when))["d"]],
          "низ", {p: round(float(world[p][:, 2].min()) / SCALE, 2) for p in (up, lo, paw, "Torso")})

with open(os.path.join(OUT, "anim_report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)


def fade(a, b, n=4):
    """Стык кусков: первые n кадров b подтягиваются от последнего кадра a (как короткое смешение в игре)."""
    out = list(b)
    for i in range(min(n, len(out))):
        out[i] = blend(a[-1], out[i], smooth((i + 1) / (n + 1)))
    return out


def tagged(name, frames, t0=0.0):
    """Кадры с подписью: (поза, клип, время в клипе)."""
    return [(tr, name, round(t0 + i / FPS, 3)) for i, tr in enumerate(frames)]


def sequence(*pieces):
    """Склейка кусков (имя, кадры) с короткими стыками там, где позы не совпадают."""
    out = []
    for name, frames in pieces:
        if out and max(pose_gap(out[-1][0], frames[0])) > 0.05:
            frames = fade([out[-1][0]], frames)
        out += tagged(name, frames)
    return out


def tassel_path(frames):
    """Путь кисти хвоста (середина кисти, стады) по кадрам — для схемы удара."""
    mid = (Vector(M.bp(0.0, 3.92, 4.4)) - Vector(RIG["Tassel"][1])) * SCALE
    return [[round(c, 3) for c in M.tr_matrices(tr)["Tassel"] @ mid] for tr in frames]


def export_json(path):
    """Клипы для будущего переноса: по кадрам, Transform каждого сустава относительно покоя в осях Roblox
    (стады; у Torso — вместе с высотой над землёй): [x, y, z, qx, qy, qz, qw]. Порядок частей — как в rig.json."""
    out = {"fps": FPS, "order": list(RIG), "scale": SCALE,
           "format": "frames[кадр][часть по order] = [x, y, z, qx, qy, qz, qw]", "clips": {}}
    for name, (clip, frames) in baked.items():
        rows = []
        for tr in frames:
            row = []
            for p in RIG:
                q, off = tr[p]
                t = AX @ (off * SCALE)
                r = (AX @ q.to_matrix() @ AX.transposed()).to_quaternion()
                row.append([round(v, 4) for v in (t.x, t.y, t.z, r.x, r.y, r.z, r.w)])
            rows.append(row)
        out["clips"][name] = {"title": clip.title, "duration": round(clip.dur, 4), "loop": clip.loop,
                              "start_pose": START.get(name), "end_pose": END.get(name),
                              "events": {k: round(v, 4) for k, v in clip.events.items()}, "frames": rows}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("EXPORT_OK", path, round(os.path.getsize(path) / 1e6, 2), "МБ")


def bake_blend(path):
    """Все клипы подряд на шкале времени (маркеры — начала клипов): ключи положения и поворота каждой части."""
    SCENE.frame_start = 1
    frame = 1
    for marker in list(SCENE.timeline_markers):
        SCENE.timeline_markers.remove(marker)
    for obj in PARTS.values():
        obj.rotation_mode = "QUATERNION"
        obj.animation_data_clear()
    last = {}
    for name, (clip, frames) in baked.items():
        SCENE.timeline_markers.new(name, frame=frame)
        for tr in frames:
            mats = M.tr_matrices(tr)
            for part, obj in PARTS.items():
                loc, rot, _ = mats[part].decompose()
                if part in last and rot.dot(last[part]) < 0:
                    rot = -rot
                last[part] = rot
                obj.location, obj.rotation_quaternion = loc, rot
                obj.keyframe_insert("location", frame=frame)
                obj.keyframe_insert("rotation_quaternion", frame=frame)
            frame += 1
    SCENE.frame_end = frame - 1
    SCENE.frame_set(1)
    ground_marks(False)
    eye, target, lens = CAMS["34"]
    SCENE.camera.location, SCENE.camera.data.lens = eye, lens
    SCENE.camera.rotation_euler = (Vector(eye) - Vector(target)).to_track_quat("Z", "Y").to_euler()
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    print("BLEND_OK", path, "кадров", frame - 1)


def shots():
    """Что снимать: имя → (кадры с подписями, камера, размер)."""
    idle = baked["combat_idle"][1]
    plan = {}

    def of(name):
        return baked[name][1]

    def padded(name):  # атака со стойкой до и после
        return sequence(("combat_idle", idle[-10:]), (name, of(name)), ("combat_idle", idle[:10]))

    res = (854, 480)
    sleep, walk = of("sleep_idle"), of("walk")
    waking = sequence(("sleep_idle", sleep[81:96]), ("wake", of("wake")), ("combat_idle", idle[:15]))
    square = (720, 720)
    plan["sleep_idle_close"] = (tagged("sleep_idle", sleep), "close", square)
    plan["wake_close"] = (waking, "close", square)
    plan["wake_34"] = (waking, "34", res)
    plan["combat_idle_34"] = (tagged("combat_idle", idle), "34", res)
    plan["walk_side"] = (tagged("walk", walk * 4), "side", res)
    plan["walk_34"] = (tagged("walk", walk * 4), "34", res)
    plan["heavy_paw_34r"] = (padded("heavy_paw"), "34r", res)
    plan["heavy_paw_front"] = (padded("heavy_paw"), "front", res)
    plan["tail_strike_top"] = (padded("tail_strike"), "top", res)
    plan["tail_strike_wide34"] = (padded("tail_strike"), "wide34", res)
    plan["tail_strike_front"] = (padded("tail_strike"), "front", res)
    plan["hit_34"] = (sequence(("combat_idle", idle[:15]), ("hit", of("hit")), ("combat_idle", idle[:12]),
                               ("hit", of("hit")), ("combat_idle", idle[:15])), "34", res)
    plan["victory_34"] = (sequence(("combat_idle", idle[-10:]), ("victory", of("victory")),
                                   ("stand", [A["stand"]] * 10)), "34", res)
    plan["defeat_34"] = (sequence(("combat_idle", idle[-10:]), ("defeat", of("defeat")),
                                  ("stand", [A["stand"]] * 8)), "34", res)
    plan["fall_asleep_close"] = (sequence(("stand", [A["stand"]] * 8), ("fall_asleep", of("fall_asleep")),
                                          ("sleep_idle", sleep[:30])), "close", square)
    # общая цепочка: сон → пробуждение → стойка → две «Тяжёлые лапы» → «Хвост-кистень» → два попадания → поражение
    # → шаг домой → засыпание → сон
    plan["reel"] = (sequence(("sleep_idle", sleep[:96]), ("wake", of("wake")), ("combat_idle", idle),
                             ("heavy_paw", of("heavy_paw")), ("combat_idle", idle[:3]),
                             ("heavy_paw", of("heavy_paw")), ("combat_idle", idle[:2]),
                             ("tail_strike", of("tail_strike")), ("combat_idle", idle[:12]),
                             ("hit", of("hit")), ("combat_idle", idle[:12]), ("hit", of("hit")),
                             ("combat_idle", idle[:9]), ("defeat", of("defeat")), ("walk", walk * 4),
                             ("fall_asleep", of("fall_asleep")), ("sleep_idle", sleep[:96])), "reel", res)
    return plan


CAMS["reel"] = ((15.7, -43.2, 12.5), (0.0, 0.3, 7.4), 42)  # между «спереди» и 3/4: видны и правая лапа, и хвост

if MODE in ("sheets", "render", "all") and HAVE_MODEL:
    setup_scene()
    if MODE == "sheets":
        steps = {"sleep_idle": 8, "combat_idle": 6, "walk": 1, "hit": 1, "heavy_paw": 2, "tail_strike": 2}
        for name, (clip, frames) in baked.items():
            for view in SHEET_VIEWS.get(name, ("34",)):
                render_clip(name, frames, view, (560, 400), every=steps.get(name, 3), speed=SPEED.get(name, 0.0),
                            prefix="sheet_")
    else:
        want = [s for s in os.environ.get("SPHINX_SHOTS", "").split(",") if s]
        span = [int(v) for v in os.environ.get("SPHINX_RANGE", "0:999999").split(":")]  # кадры съёмки с … по …
        meta = {}
        for name, (frames, view, res) in shots().items():
            if want and name not in want:
                continue
            folder = os.path.join(OUT, "frames", name)
            os.makedirs(folder, exist_ok=True)
            walking = [clip == "walk" for _, clip, _ in frames]
            ground_marks(any(walking))
            travel = 0.0
            for i, (tr, clip, t) in enumerate(frames):
                if walking[i]:
                    travel += 10.0 / FPS
                move_marks(travel)
                for obj, _ in MARKS:
                    obj.hide_render = not walking[i]
                if span[0] <= i < span[1]:
                    show(tr)
                    shoot(os.path.join(folder, f"{i:04d}.png"), view, res)
            meta[name] = {"view": view, "size": res, "frames": [
                {"clip": clip, "t": t, "title": baked[clip][0].title if clip in baked else "Стойка",
                 "events": [e for e, at in (baked[clip][0].events.items() if clip in baked else [])
                            if t - 1e-6 <= at < t + 1.0 / FPS - 1e-6]} for _, clip, t in frames]}
            print("SHOT_OK", name, len(frames))
        meta["tail_path"] = {"frames": tassel_path(baked["tail_strike"][1]), "events": baked["tail_strike"][0].events,
                             "camera": CAMS["top"], "size": [854, 480]}
        with open(os.path.join(OUT, "frames", f"meta_{'_'.join(want) or 'all'}.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
    if MODE == "all" and not ONLY:
        export_json(os.path.join(REPO, "assets", "models", "Boss4_Sphinx.anim.json"))
        bake_blend(os.path.join(REPO, "assets", "models", "Boss4_Sphinx_anim.blend"))
if MODE == "export" and HAVE_MODEL and not ONLY:  # только данные: клипы для переноса и сцена Blender, без рендера
    setup_scene()
    export_json(os.path.join(REPO, "assets", "models", "Boss4_Sphinx.anim.json"))
    bake_blend(os.path.join(REPO, "assets", "models", "Boss4_Sphinx_anim.blend"))
print("ANIM_OK", MODE, list(baked))


# ── Пробные варианты «Хвоста-кистеня» (режим tailtest) ───────────────────────────────────────────────────────
# Исследование: насколько близко кисть может подойти к игроку, который стоит перед мордой. Пробные клипы живут
# только здесь: в CLIPS их нет, поэтому в экспорт (anim.json, anim.blend) и в общий ролик они не попадают, а
# утверждённый клип tail_strike не меняется. Кадры — в <папка>/frames/tailtest_*.

PLAYER_AHEAD = 8.5  # стадов от центра босса до игрока: босс подходит на 8–9 (Config/Battle: AttackRange 9.5)
PLAYER_RADIUS, PLAYER_HEIGHT = 1.0, 5.2
TASSEL_RADIUS = 1.74  # половина толщины кисти, стады
TASSEL_MID = (Vector(M.bp(0.0, 3.92, 4.4)) - Vector(RIG["Tassel"][1])) * SCALE
CAMS["player"] = ((0.0, -27.0, 10.5), (0.0, -5.0, 6.0), 17)  # из-за спины игрока, как камера Roblox
CAMS["top_wide"] = ((0.0, -2.0, 50.0), (0.0, -2.0, 0.0), 40)

# yaw — поворот корпуса (минус — таз уходит влево), about — вертикальная ось поворота (y в единицах модели: −1.0 —
# между передними лапами, 0.3 — центр корпуса), shift — шаг корпуса (x, y), tail — углы звеньев в момент удара
# (подобраны tail_study.py: без пересечений, изломы не больше, чем в утверждённом клипе).
TAIL_TEST = {
    "step65": {
        "title": "Хвост-кистень — проба: 65° и шаг вбок",
        "yaw": -65.0, "about": 0.3, "shift": (-1.0, 0.0), "head_yaw": 50.0, "follow": {"FL": 0.9, "FR": 0.9},
        "tail": ((-12.0, 0, -58.9), (-73.5, 0, -89.5), (-78.6, 0, -140.0), (-84.1, 0, -151.9)),
    },
    "step82": {
        "title": "Хвост-кистень — проба: 82° и шаг вбок",
        "yaw": -82.0, "about": 0.3, "shift": (-1.0, 0.0), "head_yaw": 50.0, "follow": {"FL": 0.9, "FR": 0.9},
        "tail": ((-21.1, 0, -55.9), (-60.6, 0, -97.0), (-91.6, 0, -132.0), (-85.6, 0, -141.3)),
    },
}
PLAYER_HALF = (1.95, 0.5)  # полуширина фигуры игрока с руками и её полутолщина (игрок стоит лицом к боссу)


def turned_about(yaw, pitch, drop, about=-1.0, shift=(0.0, 0.0)):
    """Туловище, повёрнутое вокруг вертикали y = about, сдвинутое на shift и опущенное на drop."""
    rot, off = M.pivot_turn(yaw, pitch, about=about)
    return (rot, (off[0] + shift[0], off[1] + shift[1], -drop))


def strike_tr(v):
    """Поза удара пробного варианта: лапы под корпусом (правая передняя — в упоре, отстаёт), поставлена на землю."""
    yaw = v["yaw"]
    torso = turned_about(yaw, 3.0, 0.3, v["about"], v["shift"])
    follow = {"FL": v["follow"]["FL"], "FR": v["follow"]["FR"], "BL": 1.0, "BR": 1.0}
    feet = {"FL": (0.1, 0, 0, 0, yaw * 0.7), "FR": (-0.1, 0, 0, 0, yaw * 0.7), "BL": (0.1, -0.15, 0, 0, yaw),
            "BR": (-0.1, 0.15, 0, 0, yaw)}
    pose = M._merge("combat", M.plant(torso, follow=follow, **feet), M.tail(*v["tail"]), Torso=torso,
                    Head=((0, -6, v["head_yaw"]), (0, 0, 0.14)), Jaw=(M.X(6), M.Z3), **M.lids(M.SQUINT),
                    NemesL=((-30, -6, 0), (0, 0, 0.25)), NemesR=((0, 10, 0), M.Z3))
    return ground(M.pose_tr(pose))


def clip_tail_test(key):
    """Пробный «Хвост-кистень»: замах (хвост высоко и вправо, корпус чуть в другую сторону) → корпус разворачивается
    вокруг своего центра и шагает к цели, лапы переступают парами → хвост хлещет вокруг левого бока на высоте игрока
    → возврат. Времена те же, что у утверждённого клипа: выпад на 0.5 с, контакт через HitDelay."""
    v = TAIL_TEST[key]
    lead = 0.5
    hit = lead + HIT_DELAY
    yaw, about, shift = v["yaw"], v["about"], v["shift"]
    c = Clip("tailtest_" + key, v["title"], 1.4, lag={"EarL": 0.03, "EarR": 0.03})
    c.event("начало выпада в игре (AttackAt)", lead).event("контакт: удар кисти", hit)
    sw = strike_tr(v)
    part = lambda k: (shift[0] * k, shift[1] * k)  # noqa: E731
    c.pose(0.0, CB, hold=True)
    ant = edit(face(CB, lid=LID["squint"], brow=(-16, -0.03), jaw=10), Torso=turned_about(12, 5.0, 0.24, about),
               Head=((6, 2, -9), Z3))
    ant = with_tail(ant, (-8, 0, 30), (-26, 0, 64), (-44, 0, 92), (-50, 0, 110))
    c.pose(0.42, ant, hold=True)
    mid = edit(blend(ant, sw, 0.5), Torso=turned_about(yaw * 0.45, 4.0, 0.12, about, part(0.45)),
               Head=((2, -3, v["head_yaw"] * 0.45), (0, 0, 0.06)))
    mid = with_tail(mid, (-10, 0, 14), (-34, 0, 22), (-62, 0, 20), (-72, 0, 12))
    c.pose(0.6, mid)
    c.pose(hit, sw, hold=True)
    t = v["tail"]
    # довод: таз проворачивается ещё на 3° и уносит хвост дальше по дуге (сам хвост к бедру не подгибается),
    # кисть чуть провисает
    over = with_tail(edit(sw, Torso={"r": (0, 0, -3.0), "o": (0, 0, -0.03)}), t[0], t[1], t[2], t[3])
    c.pose(hit + 0.07, over, only=["Torso"] + TAIL)
    c.pose(hit + 0.17, sw, only=["Torso"] + TAIL)
    ret = edit(blend(sw, CB, 0.5), Torso=turned_about(yaw * 0.45, 4.0, 0.14, about, part(0.45)),
               Head=((4, -2, v["head_yaw"] * 0.42), (0, 0, 0.05)))
    ret = with_tail(ret, (-12, 0, -30), (-38, 0, -56), (-66, 0, -70), (-78, 0, -78))
    c.pose(1.12, ret)
    past = with_tail(edit(CB, Torso=turned_about(3, 5.0, 0.16, about)), (-24, 0, 8), (-44, 0, 14), (-66, 0, 16), (-80, 0, 16))
    c.pose(1.29, past, only=["Torso"] + TAIL)
    c.pose(1.4, CB, hold=True)
    # — лапы: корпус разворачивается вокруг своего центра, поэтому переставляются все четыре лапы — грузный
    #   подскок. Каждая лапа идёт под своим плечом или бедром; первой отрывается отстающая пара (левая передняя и
    #   правая задняя), последней приземляется ведущая — за мгновение до удара кисти. Обратно — наоборот —
    ls = {k: leg_state(sw, k) for k in LEG}
    cb = LS["combat"]
    c.feet(0.0, CB)
    for k, t0, t1, lift in (("FL", 0.42, 0.68, 0.22), ("BR", 0.42, 0.69, 0.3), ("FR", 0.46, 0.72, 0.22), ("BL", 0.46, 0.73, 0.32)):
        c.plant(k, t0)
        c.hop(k, t0, t1, ls[k], lift=lift)
    for k in LEG:
        c.foot(k, hit, ls[k], True)
    for k, t0, t1, lift in (("FR", 0.93, 1.2, 0.2), ("BL", 0.93, 1.21, 0.28), ("FL", 0.97, 1.24, 0.2), ("BR", 0.97, 1.25, 0.28)):
        c.plant(k, t0)
        c.hop(k, t0, t1, cb[k], lift=lift)
    c.feet(1.4, CB)
    c.notes.append("пробный вариант: не заменяет tail_strike")
    return c


def player_metrics(clip, frames):
    """Кисть и игрок по кадрам: расстояние от середины кисти до оси игрока и зазор до его тела; где кисть в момент
    контакта (оси Roblox: x — влево от босса, y — вверх, z — вперёд); насколько близко к игроку подходят остальные
    части босса; поворот корпуса в момент контакта."""
    axis = Vector((0.0, -PLAYER_AHEAD, 0.0))
    hit = next(t for name, t in clip.events.items() if "контакт" in name)
    rows, near_body, body_part = [], 1e9, ""
    for i, tr in enumerate(frames):
        mats = M.tr_matrices(tr)
        tip = mats["Tassel"] @ TASSEL_MID
        z = min(max(tip.z, 1.0), PLAYER_HEIGHT - 0.7)
        rows.append((i / FPS, (tip - Vector((axis.x, axis.y, z))).length, tip.copy(), mats))
        for name, pts in M.world_points(mats).items():
            if name in TAIL:
                continue
            low = pts[pts[:, 2] < PLAYER_HEIGHT]
            if len(low):
                d = float(np.hypot(low[:, 0] - axis.x, low[:, 1] - axis.y).min()) - PLAYER_RADIUS
                if d < near_body:
                    near_body, body_part = d, f"{name} на {i / FPS:.2f} с"
    best = min(rows, key=lambda r: r[1])
    mats = M.tr_matrices(clip.sample(hit)[0])  # ровно момент контакта (между кадрами 0.733 и 0.767 с)
    tip = mats["Tassel"] @ TASSEL_MID
    at = (hit, (tip - Vector((axis.x, axis.y, min(max(tip.z, 1.0), PLAYER_HEIGHT - 0.7)))).length)
    fwd = mats["Torso"].to_quaternion() @ Vector((0.0, -1.0, 0.0))
    head = mats["Head"].to_quaternion() @ Vector((0.0, -1.0, 0.0))
    def figure_gap(point):  # от поверхности кисти до фигуры игрока (прямоугольник с руками), стады; минус — задела
        dx = max(abs(point.x) - PLAYER_HALF[0], 0.0)
        dy = max(abs(point.y + PLAYER_AHEAD) - PLAYER_HALF[1], 0.0)
        dz = max(point.z - PLAYER_HEIGHT, 0.0)
        return math.sqrt(dx * dx + dy * dy + dz * dz) - TASSEL_RADIUS

    return {
        "player_ahead": PLAYER_AHEAD,
        "gap_to_figure_at_contact": round(figure_gap(tip), 2),
        "gap_to_figure_min": round(min(figure_gap(r[2]) for r in rows), 2),
        "contact_time": hit,
        "tassel_to_player_at_contact": round(at[1], 2),
        "gap_at_contact": round(at[1] - TASSEL_RADIUS - PLAYER_RADIUS, 2),
        "tassel_at_contact_roblox": [round(tip.x, 2), round(tip.z, 2), round(-tip.y, 2)],
        "closest": [round(best[1], 2), round(best[0], 2)],
        "torso_yaw_at_contact": round(math.degrees(math.atan2(fwd.x, -fwd.y)), 1),
        "head_yaw_at_contact": round(math.degrees(math.atan2(head.x, -head.y)), 1),
        "body_to_player_min": [round(near_body, 2), body_part],
    }


def place_player(on):
    """Манекен игрока (он есть в сцене модели, рост 5.2 стада) — на место игрока перед боссом."""
    parts = [o for o in SCENE.objects if o.name.startswith("Mannequin")]
    if not parts:
        return
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in parts:
        o.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    for o in parts:
        for corner in o.bound_box:
            p = o.matrix_world @ Vector(corner)
            lo = Vector((min(lo.x, p.x), min(lo.y, p.y), min(lo.z, p.z)))
            hi = Vector((max(hi.x, p.x), max(hi.y, p.y), max(hi.z, p.z)))
    move = Vector((-(lo.x + hi.x) / 2, -PLAYER_AHEAD - (lo.y + hi.y) / 2, -lo.z))
    mat = bpy.data.materials.new("PlayerMark")  # только для кадров: сцена модели не сохраняется
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.05, 0.3, 0.95, 1)
    for o in parts:
        o.location = move
        o.hide_render = not on
        o.data.materials.clear()
        o.data.materials.append(mat)
    print("PLAYER рост", round(hi.z - lo.z, 2), "ширина", round(hi.x - lo.x, 2), "место", [round(c, 2) for c in move])


if MODE == "tailtest":
    test_report = {"approved": {}, "tests": {}}
    if "tail_strike" in baked:
        clip, frames = baked["tail_strike"]
        test_report["approved"] = player_metrics(clip, frames)
        print("TAILTEST утверждённый", json.dumps(test_report["approved"], ensure_ascii=False))
    tests = {}
    for key in TAIL_TEST:
        clip = clip_tail_test(key)
        frames = clip.frames()
        rep = diagnose(clip, frames)
        rep["ends"] = {"start": pose_gap(frames[0], A["combat"]), "end": pose_gap(frames[-1], A["combat"])}
        rep["player"] = player_metrics(clip, frames)
        rep["title"] = clip.title
        tests[key] = (clip, frames)
        test_report["tests"][key] = rep
        print("DIAG", clip.name, json.dumps(rep, ensure_ascii=False))
        print("TAILTEST", key, json.dumps(rep["player"], ensure_ascii=False))
    with open(os.path.join(OUT, "tailtest_report.json"), "w", encoding="utf-8") as f:
        json.dump(test_report, f, ensure_ascii=False, indent=1)
    kept = dict(baked)  # кадры пробных клипов рядом с отчётом; основной экспорт не трогается
    baked.clear()
    baked.update({clip.name: (clip, frames) for clip, frames in tests.values()})
    if "tail_strike" in kept:
        baked["tail_strike"] = kept["tail_strike"]
    export_json(os.path.join(OUT, "tailtest_clips.json"))
    baked.clear()
    baked.update(kept)
    if HAVE_MODEL and os.environ.get("SPHINX_SHOTS", "") != "none":
        setup_scene()
        place_player(True)
        ground_marks(False)
        idle = baked["combat_idle"][1]
        want = [s for s in os.environ.get("SPHINX_SHOTS", "").split(",") if s]
        plan = {}
        for key, (clip, frames) in tests.items():
            seq = sequence(("combat_idle", idle[-10:]), (clip.name, frames), ("combat_idle", idle[:10]))
            for view, res in (("player", (854, 480)), ("front", (854, 480)), ("top_wide", (720, 720)), ("side", (854, 480))):
                plan[f"tailtest_{key}_{view}"] = (seq, view, res, clip)
        if "tail_strike" in baked:
            clip, frames = baked["tail_strike"]
            seq = sequence(("combat_idle", idle[-10:]), ("tail_strike", frames), ("combat_idle", idle[:10]))
            for view, res in (("player", (854, 480)), ("top_wide", (720, 720))):
                plan[f"tailnow_{view}"] = (seq, view, res, clip)
        meta = {}
        for name, (seq, view, res, clip) in plan.items():
            if want and name not in want:
                continue
            folder = os.path.join(OUT, "frames", name)
            os.makedirs(folder, exist_ok=True)
            for i, (tr, _, _) in enumerate(seq):
                if i % int(os.environ.get("TAIL_EVERY", "1")) == 0:
                    show(tr)
                    shoot(os.path.join(folder, f"{i:04d}.png"), view, res)
            meta[name] = {"view": view, "size": res, "frames": [
                {"clip": cname, "t": t, "title": clip.title if cname == clip.name else "Стойка",
                 "events": [e for e, at in (clip.events.items() if cname == clip.name else []) if t - 1e-6 <= at < t + 1.0 / FPS - 1e-6]}
                for _, cname, t in seq]}
            print("SHOT_OK", name, len(seq))
        with open(os.path.join(OUT, "frames", f"meta_tailtest_{'_'.join(want)[:60] or 'all'}.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
    print("TAILTEST_OK")


# ── Двухфазная проба «Хвоста-кистеня»: взмах хвостом + удар левой передней лапой (режимы probe и combo) ─────────
# Проверка идеи владельца: хвост делает широкий взмах (он не достаёт до игрока), а урон на 0.75 с совпадает с
# касанием передней лапы. Клип живёт только здесь: в CLIPS его нет, в экспорт (anim.json, anim.blend) он не
# попадает, утверждённый tail_strike не меняется.

if MODE == "probe":
    np.set_printoptions(precision=2, suppress=True)
    for name in ("FPawL", "FLowerL", "FUpperL", "Head", "NemesL", "Jaw"):
        local = (M.POINTS[name] - np.array(RIG[name][1])) * SCALE
        print("PROBE часть", name, "точек", len(local), "от", local.min(axis=0), "до", local.max(axis=0))
    cb = M.tr_matrices(CB)
    print("PROBE стойка: плечо FL", np.array(cb["FUpperL"].translation), "запястье FL", np.array(cb["FPawL"].translation),
          "голова", np.array(cb["Head"].translation), "torso", np.array(cb["Torso"].translation))
    gaps = part_gaps(cb)
    print("PROBE стойка: ближе всего к игроку", sorted(((round(v, 2), k) for k, v in gaps.items()))[:5])
    for about in (-1.0, -0.6, 0.3):
        for yaw in (-45.0, -50.0, -55.0, -58.0, -60.0, -65.0):
            tr = combo_stance(yaw, about)
            mats = M.tr_matrices(tr)
            gaps = part_gaps(mats)
            near = sorted(((round(v, 2), k) for k, v in gaps.items() if k not in STRIKE_LEG))[:4]
            sh = mats["FUpperL"].translation
            head = mats["Head"].translation
            fwd = mats["Head"].to_quaternion() @ Vector((0.0, -1.0, 0.0))
            to_player = Vector((0.0 - head.x, -PLAYER_AHEAD - head.y, 0.0))
            off = math.degrees(Vector((fwd.x, fwd.y, 0)).angle(to_player))
            d_axis = math.hypot(sh.x, sh.y + PLAYER_AHEAD)
            print(f"PROBE ось {about:+.1f} поворот {yaw:.0f}: плечо FL ({sh.x:.2f}, {sh.y:.2f}, {sh.z:.2f}), до оси игрока "
                  f"{d_axis:.2f}; голова ({head.x:.2f}, {head.y:.2f}, {head.z:.2f}) сдвиг "
                  f"{(head - cb['Head'].translation).length:.2f}, морда мимо игрока на {off:.0f}°; ближние части {near}; "
                  f"запястье FL {np.array(mats['FPawL'].translation)}; FR {np.array(mats['FPawR'].translation)}; "
                  f"таз {np.array(mats['Tail1'].translation)}")
    print("PROBE_OK")
    sys.exit(0)


COMBO = {
    "c58": {"title": "Проба: взмах хвостом и удар лапой, 58°", "yaw": -58.0},
    "c52": {"title": "Проба: взмах хвостом и удар лапой, 52°", "yaw": -52.0},
    "c64": {"title": "Проба: взмах хвостом и удар лапой, 64°", "yaw": -64.0},
}


def clip_combo(key):
    """Пробный клип с другим углом — тем же построителем, что рабочий клип (build_combo, часть a3c)."""
    c = build_combo(COMBO[key]["yaw"], "combotest_" + key, COMBO[key]["title"])
    c.notes.append("пробный угол: в рабочий набор входит только 58°")
    return c


def combo_metrics(clip, frames, strike_leg=STRIKE_LEG, striker="FPawL"):
    """Проверки атаки по кадрам (стады, секунды): контакт бьющей части с фигурой игрока, остальные части и игрок,
    путь кисти, поворот и смещение корпуса и головы, опора лап."""
    dt = 1.0 / FPS
    hit = next(t for name, t in clip.events.items() if "контакт" in name)
    cb = M.tr_matrices(A["combat"])
    rows = []
    for i, tr in enumerate(frames):
        mats = M.tr_matrices(tr)
        toes = {}
        for key_, leg in LEG.items():
            toes[key_] = mats[leg[2]] @ ((TOE[key_] - Vector(RIG[leg[2]][1])) * SCALE)
        fwd = mats["Torso"].to_quaternion() @ Vector((0.0, -1.0, 0.0))
        rows.append({"t": i * dt, "gaps": part_gaps(mats), "toes": toes,
                     "side": side_depth(M.world_points(mats)[striker]),
                     "yaw": math.degrees(math.atan2(fwd.x, -fwd.y)),
                     "tassel": mats["Tassel"] @ TASSEL_MID, "head": mats["Head"].translation.copy(),
                     "torso": mats["Torso"].translation.copy()})

    def speed(get):
        best = (0.0, 0.0)
        for a, b in zip(rows, rows[1:]):
            s = (get(b) - get(a)).length / dt
            if s > best[0]:
                best = (s, b["t"])
        return [round(best[0], 1), round(best[1], 2)]

    on = [[k_ for k_ in LEG if r["toes"][k_].z < CONTACT] for r in rows]  # лапы на земле по кадрам
    spans = {}
    for k_ in LEG:
        air, runs, start = [k_ not in o for o in on], [], None
        for i, a in enumerate(air + [False]):
            if a and start is None:
                start = i
            if not a and start is not None:
                runs.append([round(start * dt, 2), round(i * dt, 2)])
                start = None
        spans[k_] = runs
    at = M.tr_matrices(clip.sample(hit)[0])  # ровно момент контакта (между кадрами 0.733 и 0.767 с)
    g_hit = part_gaps(at)
    strike_min = min(rows, key=lambda r: r["gaps"][striker])

    def others(r):
        return min((v, k_) for k_, v in r["gaps"].items() if k_ not in strike_leg and k_ not in TAIL)

    body_min = min(((others(r), r["t"]) for r in rows), key=lambda x: x[0][0])
    tassel_min = min(((figure_gap_points(np.array([r["tassel"]])) - TASSEL_RADIUS, r["t"]) for r in rows),
                     key=lambda x: x[0])
    fwd_t = at["Torso"].to_quaternion() @ Vector((0.0, -1.0, 0.0))
    fwd_h = at["Head"].to_quaternion() @ Vector((0.0, -1.0, 0.0))
    look = Vector((0.0, -PLAYER_AHEAD, 2.6)) - at["Head"].translation
    toe_key = PAW_OF.get(striker)
    by_distance = {}
    for ahead in (8.0, 8.5, 9.0):  # босс подходит к игроку на 8–9 стадов
        pts = M.world_points(at)
        low, arm = 9.0, {p_: (9.0, 0.0) for p_ in strike_leg if p_ != striker}
        for i, tr in enumerate(frames):
            g = part_gaps(M.tr_matrices(tr), ahead)
            low = min(low, min(v for k_, v in g.items() if k_ not in strike_leg and k_ not in TAIL))
            for p_ in arm:
                if g[p_] < arm[p_][0]:
                    arm[p_] = (g[p_], i * dt)
        stance = part_gaps(cb, ahead)
        by_distance[str(ahead)] = {"striker_gap": round(figure_gap_points(pts[striker], ahead), 2),
                                   "striker_side_depth": round(side_depth(pts[striker], ahead), 2),
                                   "other_parts_min_gap": round(low, 2),
                                   "strike_arm_min_gap": {p_: [round(v_[0], 2), round(v_[1], 2)] for p_, v_ in arm.items()},
                                   "other_parts_gap_in_stance": round(min(stance.values()), 2)}
    return {
        "by_distance": by_distance,
        "contact_time": hit,
        "striker_gap_at_contact": round(g_hit[striker], 2),
        "striker_side_depth_at_contact": round(side_depth(M.world_points(at)[striker]), 2),
        "striker_side_depth_frames": {f"{r['t']:.3f}": round(r["side"], 2) for r in rows if abs(r["t"] - hit) < 0.11},
        "striker_side_depth_max": round(max(r["side"] for r in rows), 2),
        "striker_gap_frames": {f"{r['t']:.3f}": round(r["gaps"][striker], 2) for r in rows if abs(r["t"] - hit) < 0.11},
        "striker_gap_min": [round(strike_min["gaps"][striker], 2), round(strike_min["t"], 2)],
        "strike_leg_gaps_at_contact": {p: round(g_hit[p], 2) for p in strike_leg},
        "other_parts_min_gap": [round(body_min[0][0], 2), body_min[0][1], round(body_min[1], 2)],
        "other_parts_gap_at_contact": sorted((round(v, 2), k_) for k_, v in g_hit.items() if k_ not in strike_leg)[:4],
        "tassel_min_gap": [round(tassel_min[0], 2), round(tassel_min[1], 2)],
        "tassel_path_roblox": {f"{r['t']:.2f}": [round(r["tassel"].x, 1), round(r["tassel"].z, 1), round(-r["tassel"].y, 1)]
                               for r in rows if 0.19 < r["t"] < 0.81 and round(r["t"] * FPS) % 2 == 0},
        "tassel_speed_max": speed(lambda r: r["tassel"]),
        "torso_yaw_at_contact": round(math.degrees(math.atan2(fwd_t.x, -fwd_t.y)), 1),
        "torso_yaw_range": [round(min(r["yaw"] for r in rows), 1), round(max(r["yaw"] for r in rows), 1)],
        "torso_yaw_speed_max": round(max(abs(b["yaw"] - a["yaw"]) / dt for a, b in zip(rows, rows[1:])), 0),
        "torso_centre_shift_max": round(max((r["torso"] - cb["Torso"].translation).length for r in rows), 2),
        "torso_centre_shift_at_contact": [round(c_, 2) for c_ in (at["Torso"].translation - cb["Torso"].translation)],
        "torso_speed_max": speed(lambda r: r["torso"]),
        "head_shift_max": round(max((r["head"] - cb["Head"].translation).length for r in rows), 2),
        "head_shift_at_contact": [round(c_, 2) for c_ in (at["Head"].translation - cb["Head"].translation)],
        "head_speed_max": speed(lambda r: r["head"]),
        "head_off_player_deg": round(math.degrees(fwd_h.angle(look)), 0),
        "paws_on_ground_min": min(len(o) for o in on),
        "time_no_paws": round(sum(1 for o in on if not o) * dt, 3),
        "time_one_paw": round(sum(1 for o in on if len(o) == 1) * dt, 3),
        "air_spans": spans,
        "wrists_at_contact": {k_: [round(c_, 2) for c_ in at[LEG[k_][2]].translation] for k_ in LEG},
        "striker_toe_speed_max": speed(lambda r: r["toes"][toe_key]) if toe_key else None,
    }


if MODE == "combo":
    want_keys = [k_ for k_ in os.environ.get("COMBO_KEYS", "c58").split(",") if k_]
    combo_report = {"tests": {}, "compare": {}}
    tests = {}
    for key in want_keys:
        clip = clip_combo(key)
        frames = clip.frames()
        rep = diagnose(clip, frames, clash_every=1)
        rep["ends"] = {"start": pose_gap(frames[0], A["combat"]), "end": pose_gap(frames[-1], A["combat"])}
        rep["combo"] = combo_metrics(clip, frames)
        rep["title"] = clip.title
        rep["half_rate"] = half_rate_error(frames, False)
        tests[key] = (clip, frames)
        combo_report["tests"][key] = rep
        print("DIAG", clip.name, json.dumps({k_: v_ for k_, v_ in rep.items() if k_ != "combo"}, ensure_ascii=False))
        print("COMBO", key, json.dumps(rep["combo"], ensure_ascii=False))
        if os.environ.get("COMBO_TRACE"):
            prev = None
            for i, tr in enumerate(frames):
                t = i / FPS
                mats = M.tr_matrices(tr)
                fwd = mats["Torso"].to_quaternion() @ Vector((0.0, -1.0, 0.0))
                toe = {k_: mats[LEG[k_][2]] @ ((TOE[k_] - Vector(RIG[LEG[k_][2]][1])) * SCALE) for k_ in LEG}
                clip.short_by = {}
                clip.sample(t)
                short = {k_: round(v_[0] * SCALE, 2) for k_, v_ in clip.short_by.items() if v_[0] * SCALE > 0.01}
                gaps = part_gaps(mats)
                near = min((v_, k_) for k_, v_ in gaps.items() if k_ not in STRIKE_LEG and k_ not in TAIL)
                line = f"TRACE {t:.3f} yaw {math.degrees(math.atan2(fwd.x, -fwd.y)):6.1f}"
                if prev is not None:
                    steps = sorted(((math.degrees(prev[1][p_][0].rotation_difference(tr[p_][0]).angle), p_) for p_ in RIG), reverse=True)[:2]
                    line += " | носки ст./с " + " ".join(f"{k_} {(toe[k_] - prev[0][k_]).length * FPS:5.1f}" for k_ in LEG)
                    line += " | шаг " + ", ".join(f"{p_} {a_:.0f}" for a_, p_ in steps)
                line += f" | на земле {''.join(k_ + ' ' for k_ in LEG if toe[k_].z < CONTACT)}| лапа-игрок {gaps['FPawL']:.2f} вглубь {side_depth(M.world_points(mats)['FPawL']):.2f} плечо {gaps['FUpperL']:.2f} предпл. {gaps['FLowerL']:.2f} прочее {near[0]:.2f} {near[1]} | недотяг {short}"
                print(line)
                prev = (toe, tr)
    # те же проверки для утверждённого клипа (A), пробы 82° (B) и «Тяжёлой лапы» — для сравнения
    others = {}
    tail_parts = ("Tail1", "Tail2", "Tail3", "Tassel")
    if os.environ.get("COMBO_COMPARE", "1") == "1":
        a_old = clip_tail_strike_v1()
        others["A_tail_strike_v1"] = (a_old, a_old.frames(), tail_parts, "Tassel")
        if "tail_strike" in baked:
            others["tail_strike_final"] = (baked["tail_strike"][0], baked["tail_strike"][1], STRIKE_LEG, "FPawL")
        b = clip_tail_test("step82")
        others["B_step82"] = (b, b.frames(), tail_parts, "Tassel")
        if "heavy_paw" in baked:
            others["heavy_paw"] = (baked["heavy_paw"][0], baked["heavy_paw"][1], ("FUpperR", "FLowerR", "FPawR"), "FPawR")
    for name, (clip, frames, leg, striker) in others.items():
        rep = diagnose(clip, frames, clash_every=1)
        rep["combo"] = combo_metrics(clip, frames, leg, striker)
        combo_report["compare"][name] = rep
        tests_b = (clip, frames)
        if name == "B_step82":
            others_b = tests_b
        print("DIAG", name, json.dumps({k_: v_ for k_, v_ in rep.items() if k_ != "combo"}, ensure_ascii=False))
        print("COMPARE", name, json.dumps(rep["combo"], ensure_ascii=False))
    with open(os.path.join(OUT, "combo_report.json"), "w", encoding="utf-8") as f:
        json.dump(combo_report, f, ensure_ascii=False, indent=1)
    kept = dict(baked)  # кадры пробных клипов рядом с отчётом; основной экспорт не трогается
    baked.clear()
    baked.update({clip.name: (clip, frames) for clip, frames in tests.values()})
    export_json(os.path.join(OUT, "combo_clips.json"))
    baked.clear()
    baked.update(kept)
    CAMS["hit_back"] = ((4.5, -21.0, 8.5), (2.2, -7.4, 3.1), 62)  # крупно из-за плеча игрока: лапа и его бок
    CAMS["hit_top"] = ((1.8, -7.6, 27.0), (1.8, -7.6, 0.0), 40)  # крупно сверху: подошва и фигура игрока
    if HAVE_MODEL and os.environ.get("SPHINX_SHOTS", "") != "none":
        setup_scene()
        place_player(True)
        ground_marks(False)
        idle = baked["combat_idle"][1]
        want = [s_ for s_ in os.environ.get("SPHINX_SHOTS", "").split(",") if s_]
        every = int(os.environ.get("TAIL_EVERY", "1"))
        span = [int(v_) for v_ in os.environ.get("COMBO_RANGE", "0:999999").split(":")]
        HEAD_PARTS = ("Head", "Jaw", "EyelidL", "EyelidR", "BrowL", "BrowR", "EarL", "EarR", "NemesL", "NemesR")

        def head_shown(on):  # вид сверху без головы: головной убор нависает над игроком и закрывает контакт
            for part in HEAD_PARTS:
                PARTS[part].hide_render = not on

        CAMS["top_nohead"] = CAMS["top_wide"]
        CAMS["hit_top_nohead"] = CAMS["hit_top"]
        plan = {}
        for key, (clip, frames) in tests.items():
            seq = sequence(("combat_idle", idle[-10:]), (clip.name, frames), ("combat_idle", idle[:10]))
            for view, res in (("player", (854, 480)), ("front", (854, 480)), ("top_wide", (720, 720)), ("side", (854, 480)),
                              ("hit_back", (854, 480)), ("hit_top_nohead", (720, 720)), ("34", (854, 480)),
                              ("top_nohead", (720, 720))):
                plan[f"combo_{key}_{view}"] = (seq, view, res, clip)
        if "heavy_paw" in baked:  # «Тяжёлая лапа» теми же камерами и с манекеном — для сравнения двух ударов лапой
            clip, frames = baked["heavy_paw"]
            seq = sequence(("combat_idle", idle[-10:]), ("heavy_paw", frames), ("combat_idle", idle[:13]))
            for view, res in (("player", (854, 480)), ("top_wide", (720, 720)), ("top_nohead", (720, 720))):
                plan[f"heavynow_{view}"] = (seq, view, res, clip)
        meta = {}
        for name, (seq, view, res, clip) in plan.items():
            if want and name not in want:
                continue
            folder = os.path.join(OUT, "frames", name)
            os.makedirs(folder, exist_ok=True)
            head_shown("nohead" not in view)
            for i, (tr, _, _) in enumerate(seq):
                if i % every == 0 and span[0] <= i < span[1]:
                    show(tr)
                    shoot(os.path.join(folder, f"{i:04d}.png"), view, res)
            head_shown(True)
            meta[name] = {"view": view, "size": res, "frames": [
                {"clip": cname, "t": t, "title": clip.title if cname == clip.name else "Стойка",
                 "events": [e for e, at in (clip.events.items() if cname == clip.name else []) if t - 1e-6 <= at < t + 1.0 / FPS - 1e-6]}
                for _, cname, t in seq]}
            print("SHOT_OK", name, len(seq))
        # ровно момент контакта (0.75 с лежит между кадрами 0.733 и 0.767): так его покажет игра, смешав два кадра
        for key, (clip, frames) in tests.items():
            hit_t = next(t for n_, t in clip.events.items() if "контакт" in n_)
            i0 = int(hit_t * FPS)
            still = blend(frames[i0], frames[min(i0 + 1, len(frames) - 1)], hit_t * FPS - i0)
            for view, res in (("hit_back", (1280, 720)), ("hit_top_nohead", (900, 900)), ("player", (1280, 720)),
                              ("top_nohead", (900, 900)), ("34", (1280, 720))):
                name = f"still_{key}_{view}"
                if want and name not in want:
                    continue
                head_shown("nohead" not in view)
                show(still)
                shoot(os.path.join(OUT, "frames", name + ".png"), view, res)
                head_shown(True)
                print("STILL_OK", name)
        with open(os.path.join(OUT, "frames", f"meta_combo_{'_'.join(want)[:60] or 'all'}.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
    print("COMBO_OK")
