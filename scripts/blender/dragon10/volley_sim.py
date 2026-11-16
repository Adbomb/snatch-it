"""«Королевский магический залп» Короля-дракона — модель способности для проверки честности (без Roblox и Blender).

Та же логика, что предлагается для сервера (BattleService), только в чистом Python: по ней считаются цифры
предложения и сценарии уклонения, а Blender (v7_anim2.py) берёт из неё положения снарядов и цели для видео.

Правила:
- подготовка: от начала клипа до фиксации прицел следит за целью (направление на её грудь);
- фиксация (LOCK) за LOCK_TO_FIRE до выстрела: направление больше не меняется, полосы-предупреждения замирают;
- выстрел (FIRE): три снаряда из центра магического круга по прямым — центральный в зафиксированную точку, боковые
  повёрнуты на ±SPREAD в плане с тем же наклоном;
- снаряд летит с постоянной скоростью, не наводится; исчезает, ударившись в препятствие или в землю, или пройдя
  RANGE;
- попадание: отрезок пути снаряда за шаг сервера ближе r_снаряда + r_игрока к капсуле игрока (ось от ступней + r до
  макушки − r); каждый снаряд бьёт игрока не больше одного раза, за залп — не больше одного урона (предложение);
- отмена: конец боя до выстрела — снарядов нет, предупреждение гаснет; во время полёта — снаряды удаляются сразу.

Единицы — стады и секунды, оси как в Blender: z вверх, босс смотрит в −y.
"""

import math
from dataclasses import dataclass, field

# ── предлагаемые числа (на утверждение владельца; в Config/Battle не внесены) ─────────────────────────────────
PARAMS = {
    "track_from": 0.6,  # с от начала клипа: появляются полосы, прицел следит за целью
    "lock": 1.45,  # фиксация направления
    "fire": 1.95,  # выстрел (как «заклинание» прежнего клипа)
    "speed": 38.0,  # стадов/с, по прямой
    "spread": 25.0,  # градусов: боковые снаряды в плане
    "radius": 1.5,  # стада: радиус снаряда для попадания (видимое ядро — тот же радиус)
    "player_radius": 1.25,  # стада: капсула игрока (R15 ≈ 2.5 стада в ширину)
    "player_height": 5.0,
    "range": 60.0,  # стадов: дальше снаряд гаснет сам
    "server_hz": 60.0,  # шаг проверки попаданий на сервере (Heartbeat)
    "aim_height": 2.6,  # стада над ступнями: точка прицела — грудь
}
LAUNCH = (-4.5, -28.5, 14.5)  # центр магического круга при выстреле вперёд (стады; 28.9 от центра босса)


def v_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def v_mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def v_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def v_len(a):
    return math.sqrt(v_dot(a, a))


def v_unit(a):
    n = v_len(a)
    return (a[0] / n, a[1] / n, a[2] / n)


def seg_seg(p1, q1, p2, q2):
    """Наименьшее расстояние между отрезками p1q1 и p2q2 (стандартный способ, Ericson)."""
    d1, d2, r = v_sub(q1, p1), v_sub(q2, p2), v_sub(p1, p2)
    a, e, f = v_dot(d1, d1), v_dot(d2, d2), v_dot(d2, r)
    eps = 1e-9
    if a <= eps and e <= eps:
        return v_len(r)
    if a <= eps:
        s, t = 0.0, min(max(f / e, 0.0), 1.0)
    else:
        c = v_dot(d1, r)
        if e <= eps:
            t, s = 0.0, min(max(-c / a, 0.0), 1.0)
        else:
            b = v_dot(d1, d2)
            den = a * e - b * b
            s = min(max((b * f - c * e) / den, 0.0), 1.0) if den > eps else 0.0
            t = (b * s + f) / e
            if t < 0:
                t, s = 0.0, min(max(-c / a, 0.0), 1.0)
            elif t > 1:
                t, s = 1.0, min(max((b - c) / a, 0.0), 1.0)
    c1, c2 = v_add(p1, v_mul(d1, s)), v_add(p2, v_mul(d2, t))
    return v_len(v_sub(c1, c2))


@dataclass
class Obstacle:
    """Препятствие — вертикальный цилиндр (колонна, стена арены): центр в плане, радиус, высота."""
    x: float
    y: float
    r: float
    h: float


@dataclass
class Projectile:
    side: int  # −1 левый (по ходу залпа), 0 центральный, +1 правый
    start: tuple
    dir: tuple
    alive: bool = True
    end_t: float = None  # время исчезновения (от выстрела)
    end_why: str = ""
    hit_t: float = None
    pos: tuple = None


@dataclass
class Result:
    projectiles: list = field(default_factory=list)
    hits: list = field(default_factory=list)  # (время от начала клипа, снаряд, расстояние)
    damage_events: int = 0
    canceled: str = ""
    aim_lock: tuple = None
    closest: dict = field(default_factory=dict)  # снаряд → наименьший зазор до капсулы игрока (стады; − — внутри)
    frames: list = field(default_factory=list)


def rot_z(v, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2])


def aim_dirs(launch, target_feet, prm):
    """Три направления: центральное — в грудь цели, боковые — повёрнуты в плане на ±spread, наклон тот же."""
    aim = v_add(target_feet, (0, 0, prm["aim_height"]))
    d = v_unit(v_sub(aim, launch))
    # «левый» по ходу залпа: поворот против часовой (вид сверху), если смотреть вдоль направления
    return {0: d, -1: v_unit(rot_z(d, prm["spread"])), 1: v_unit(rot_z(d, -prm["spread"]))}, aim


def ground_hit(start, d):
    """Через сколько стадов снаряд коснётся земли (z = 0), если летит вниз."""
    if d[2] >= -1e-6:
        return math.inf
    return start[2] / -d[2]


def obstacle_hit(start, d, obstacles, radius):
    """Расстояние по лучу до первого препятствия (цилиндра) с учётом радиуса снаряда."""
    best = math.inf
    for o in obstacles:
        # в плане: луч (x, y) против окружности радиуса o.r + radius
        ox, oy = start[0] - o.x, start[1] - o.y
        dx, dy = d[0], d[1]
        a = dx * dx + dy * dy
        if a < 1e-9:
            continue
        b = 2 * (ox * dx + oy * dy)
        c = ox * ox + oy * oy - (o.r + radius) ** 2
        disc = b * b - 4 * a * c
        if disc < 0:
            continue
        t = (-b - math.sqrt(disc)) / (2 * a)
        if t < 0:
            continue
        z = start[2] + d[2] * t
        if z - radius <= o.h:
            best = min(best, t)
    return best


def simulate(target_path, prm=None, launch=LAUNCH, obstacles=(), end_at=None, dt_frame=1 / 30, t_end=4.2):
    """Залп против цели, движущейся по target_path(t) → (x, y, z ступней). end_at — бой кончился в этот момент
    (с от начала клипа). Возвращает Result с покадровым состоянием (для видео) и событиями попаданий."""
    prm = dict(PARAMS, **(prm or {}))
    res = Result()
    dirs = None
    projs = []
    hit_players = set()
    step = 1.0 / prm["server_hz"]
    t = 0.0
    reach = prm["radius"] + prm["player_radius"]
    seg_r = prm["player_radius"]

    def capsule(feet):
        return (v_add(feet, (0, 0, seg_r)), v_add(feet, (0, 0, prm["player_height"] - seg_r)))

    frame_t = 0.0
    prev_feet = target_path(0.0)
    while t <= t_end + 1e-9:
        feet = target_path(t)
        ended = end_at is not None and t >= end_at
        if ended and not res.canceled:
            res.canceled = "до выстрела" if t < prm["fire"] else "во время полёта"
            for pr in projs:
                if pr.alive:
                    pr.alive, pr.end_t, pr.end_why = False, t - prm["fire"], "бой окончен"
        if not res.canceled:
            if t >= prm["lock"] and res.aim_lock is None:
                dirs, aim = aim_dirs(launch, feet, prm)
                res.aim_lock = aim
            if t >= prm["fire"] and not projs:
                for side, d in dirs.items():
                    projs.append(Projectile(side, launch, d, pos=launch))
            for pr in projs:
                if not pr.alive:
                    continue
                age0 = max(t - step - prm["fire"], 0.0)
                age1 = t - prm["fire"]
                lim = min(ground_hit(pr.start, pr.dir), obstacle_hit(pr.start, pr.dir, obstacles, prm["radius"]),
                          prm["range"])
                d0, d1 = age0 * prm["speed"], min(age1 * prm["speed"], lim)
                a, b = v_add(pr.start, v_mul(pr.dir, d0)), v_add(pr.start, v_mul(pr.dir, d1))
                pr.pos = b
                c0, c1 = capsule(prev_feet)
                cap_a, cap_b = capsule(feet)
                # капсула за шаг: ось в начале и в конце шага — берём ближайшую из двух осей и середины
                dist = min(seg_seg(a, b, c0, c1), seg_seg(a, b, cap_a, cap_b))
                gap = dist - reach
                res.closest[pr.side] = min(res.closest.get(pr.side, math.inf), gap)
                if gap <= 0 and pr.side not in hit_players:
                    hit_players.add(pr.side)
                    pr.hit_t = t
                    res.hits.append((round(t, 3), pr.side, round(dist, 2)))
                    pr.alive, pr.end_t, pr.end_why = False, age1, "попал в игрока"
                    if res.damage_events == 0:
                        res.damage_events = 1  # за залп — один урон
                    continue
                if d1 >= lim - 1e-6:
                    why = "земля" if lim == ground_hit(pr.start, pr.dir) else (
                        "препятствие" if lim < prm["range"] else "дальность")
                    pr.alive, pr.end_t, pr.end_why = False, age1, why
        if t + 1e-9 >= frame_t:
            res.frames.append({
                "t": round(frame_t, 4), "feet": feet,
                "aim": res.aim_lock if res.aim_lock else v_add(feet, (0, 0, prm["aim_height"])),
                "locked": res.aim_lock is not None, "canceled": res.canceled,
                "proj": [(p.side, p.pos, p.alive, p.end_t, p.end_why) for p in projs],
            })
            frame_t += dt_frame
        prev_feet = feet
        t += step
    res.projectiles = projs
    return res


def lanes(launch, aim, prm=None):
    """Полосы предупреждения: для каждого снаряда — отрезок на земле от проекции круга до точки касания земли (или
    до дальности), ширина 2·radius. Совпадает с тем, где пройдёт снаряд."""
    prm = dict(PARAMS, **(prm or {}))
    dirs, _ = aim_dirs(launch, (aim[0], aim[1], aim[2] - prm["aim_height"]), prm)
    out = {}
    for side, d in dirs.items():
        lim = min(ground_hit(launch, d), prm["range"])
        end = v_add(launch, v_mul(d, lim))
        out[side] = ((launch[0], launch[1]), (end[0], end[1]), prm["radius"] * 2)
    return out


# ── сценарии проверки ────────────────────────────────────────────────────────────────────────────────────────
def standing(p):
    return lambda t: p


def dodge(p0, side_dir, start, speed, distance):
    """Цель стоит в p0, в момент start бежит вбок (side_dir — единичный вектор в плане) со скоростью speed на distance."""
    def f(t):
        if t <= start:
            return p0
        d = min((t - start) * speed, distance)
        return (p0[0] + side_dir[0] * d, p0[1] + side_dir[1] * d, p0[2])
    return f


def scenario_set(distance=20.0, speed=14.0, prm=None):
    """Шесть сценариев ТЗ для цели на distance стадов от круга (по горизонтали), скорость игрока speed."""
    prm = dict(PARAMS, **(prm or {}))
    fwd = v_unit((0.0, -1.0, 0.0))
    p0 = (LAUNCH[0], LAUNCH[1] - distance, 0.0)
    # игрок стоит лицом к дракону (смотрит в +y; дракон смотрит в −y): его правая рука — +x, левая — −x
    left = (-1.0, 0.0, 0.0)
    right = (1.0, 0.0, 0.0)
    pocket = distance * math.tan(math.radians(prm["spread"])) / 2  # середина между центральной и боковой полосой
    react = 0.35  # с после фиксации: реакция игрока (с запасом на задержку сети)
    t_arrive = prm["fire"] + math.dist(LAUNCH, (p0[0], p0[1], prm["aim_height"])) / prm["speed"]
    return {
        "1_stand": (standing(p0), None, "стоит на месте"),
        "2_left": (dodge(p0, left, prm["lock"] + react, speed, pocket), None,
                   f"уходит влево через {react} с после фиксации, на {pocket:.1f} ст. — между полосами"),
        "3_right": (dodge(p0, right, prm["lock"] + react, speed, pocket), None,
                    f"уходит вправо через {react} с после фиксации, на {pocket:.1f} ст."),
        "4_late": (dodge(p0, left, t_arrive - 0.12, speed, pocket), None,
                   "начинает уходить за 0.12 с до прилёта снаряда"),
        "5_end_prep": (standing(p0), 1.2, "бой кончается во время подготовки (1.2 с)"),
        "6_end_flight": (standing(p0), prm["fire"] + 0.2, "бой кончается через 0.2 с после выстрела"),
        "7_cover": (standing(p0), None, "стоит за колонной: центральный снаряд разбивается о неё"),
    }, p0, t_arrive


COVER = lambda: [Obstacle(LAUNCH[0], LAUNCH[1] - 12.0, 1.6, 14.0)]  # noqa: E731  колонна на центральной полосе


def reaction_table(prm=None, speeds=(14.0, 20.0), distances=(12.0, 20.0, 30.0)):
    """Сколько времени у игрока: от фиксации до прилёта; самая поздняя реакция, при которой он ещё успевает уйти
    в ближайшую безопасную сторону (между полосами, если «карман» есть, иначе — за боковую полосу)."""
    prm = dict(PARAMS, **(prm or {}))
    reach = prm["radius"] + prm["player_radius"]
    rows = []
    for D in distances:
        aim = (LAUNCH[0], LAUNCH[1] - D, prm["aim_height"])
        L = math.dist(LAUNCH, aim)
        t_avail = prm["fire"] - prm["lock"] + L / prm["speed"]
        side = D * math.tan(math.radians(prm["spread"]))
        pocket = side - 2 * reach
        need = reach + 0.3 if pocket >= 0.8 else side + reach + 0.3
        for v in speeds:
            rows.append({"distance": D, "speed": v, "time_after_lock": round(t_avail, 2),
                         "pocket_width": round(pocket, 2), "move_needed": round(need, 2),
                         "latest_reaction": round(t_avail - need / v, 2)})
    return rows


if __name__ == "__main__":
    import json
    import sys
    out = {"params": PARAMS, "launch": LAUNCH, "reaction": reaction_table(), "scenarios": {}}
    for D in (12.0, 20.0, 30.0):
        sc, p0, t_arr = scenario_set(D)
        for name, (path, end_at, text) in sc.items():
            r = simulate(path, end_at=end_at, obstacles=COVER() if name == "7_cover" else ())
            out["scenarios"][f"{name}@{int(D)}"] = {
                "text": text, "arrive": round(t_arr, 2), "hits": r.hits, "damage": r.damage_events,
                "canceled": r.canceled, "closest": {str(k): round(v, 2) for k, v in r.closest.items()},
                "ends": [(p.side, round(p.end_t, 2) if p.end_t is not None else None, p.end_why) for p in r.projectiles]}
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
