"""Исследование удара хвостом на настоящей геометрии v2: насколько близко кисть может подойти к игроку.
Для каждого положения корпуса (угол поворота, ось, сдвиг) подбирает углы четырёх звеньев хвоста так, чтобы середина
кисти была как можно ближе к игроку, без пересечений хвоста с телом и землёй и без изломов звеньев больше, чем в
утверждённом клипе. blender --background --factory-startup --python tail_study.py -- <файл результата.json>"""
import json
import math
import os
import random
import sys

import numpy as np
from mathutils import Euler, Vector

sys.path.insert(0, "C:/Users/uzhgb/snatch-it/scripts/blender")
import boss4_sphinx as M  # noqa: E402

M.init_checks()
S = M.SCALE
OUT = sys.argv[sys.argv.index("--") + 1]
TAILS = ("Tail1", "Tail2", "Tail3", "Tassel")
MID = (Vector(M.bp(0.0, 3.92, 4.4)) - Vector(M.RIG["Tassel"][1])) * S  # середина кисти от её сустава, стады
RADIUS = 1.74  # половина толщины кисти, стады
PLAYER_R = 1.0  # половина ширины персонажа
LIMIT_ROOT, LIMIT_LINK = 60.0, 70.0  # наибольший излом у корня и между звеньями, градусы (в утверждённом клипе до 66)
WHIP_TAIL = ((-6, 0, -34), (-46, 0, -84), (-90, 0, -120), (-104, 0, -146))
random.seed(7)


def q_of(deg):
    return Euler([math.radians(d) for d in deg], "XYZ").to_quaternion()


def bend(a, b):
    return math.degrees(q_of(a).rotation_difference(q_of(b)).angle)


def pose_for(yaw, about, shift, angles, pitch=3.0, drop=0.3):
    """Поза удара: корпус повёрнут на yaw вокруг вертикали y = about и сдвинут на shift (x, y), лапы под корпусом."""
    torso = M.pivot_turn(yaw, pitch, about=about, off=(shift[0], shift[1], -drop))
    feet = {k: (0, 0, 0, 0, yaw) for k in M.LEGS}
    return M._merge("combat", M.plant(torso, follow={k: 1.0 for k in M.LEGS}, **feet), M.tail(*angles), Torso=torso,
                    Head=((0, -6, -yaw * 0.8), (0, 0, 0.14)), Jaw=(M.X(6), M.Z3))


def tail_clash(mats, world):
    """Наибольшее новое пересечение, в котором участвует хвост (сверх стойки), и пара."""
    worst, who = 0.0, ""
    for b, sols in M.SOLIDS.items():
        mb = np.array(mats[b].inverted())
        pivot = np.array(M.RIG[b][1])
        for a, w in world.items():
            if a == b or not (a in TAILS or b in TAILS):
                continue
            q = (w @ mb[:3, :3].T + mb[:3, 3]) / S + pivot
            best = 0.0
            for inv, n, d, scale, lo, hi in sols:
                mask = np.all((q >= lo) & (q <= hi), axis=1)
                if mask.any():
                    ql = q[mask] @ inv[:3, :3].T + inv[:3, 3]
                    best = max(best, float((d[None, :] - ql @ n.T).min(axis=1).max()) * scale)
            depth = best * S - M.BASE.get("+".join(sorted((a, b))), 0.0)
            if {a, b} == {"Tail1", "Torso"}:
                depth -= 0.4  # стык основания хвоста с корпусом: в утверждённом клипе уже есть 0.35 сверх стойки
            if depth > worst:
                worst, who = depth, "+".join(sorted((a, b)))
    return worst, who


def measure(yaw, about, shift, angles, player):
    """Расстояние от середины кисти до оси игрока, штрафы и подробности."""
    mats = M.pose_matrices(pose_for(yaw, about, shift, angles))
    world = M.world_points(mats)
    tip = mats["Tassel"] @ MID
    # игрок — вертикальный отрезок высотой от 1 до 4.5 стада перед боссом (вперёд — это −y модели)
    z = min(max(tip.z, 1.0), 4.5)
    dist = (tip - Vector((0.0, -player, z))).length
    low = min(float(world[p][:, 2].min()) for p in TAILS)
    depth, pair = tail_clash(mats, world)
    kinks = [bend((0, 0, 0), angles[0])] + [bend(angles[i], angles[i + 1]) for i in range(3)]
    over = max(0.0, kinks[0] - LIMIT_ROOT) + sum(max(0.0, k - LIMIT_LINK) for k in kinks[1:])
    # насколько близко к игроку подходят остальные части босса (ниже роста игрока)
    near = 1e9
    for name, pts in world.items():
        if name in TAILS:
            continue
        lowp = pts[pts[:, 2] < 5.2]
        if len(lowp):
            near = min(near, float(np.hypot(lowp[:, 0], lowp[:, 1] + player).min()) - PLAYER_R)
    penalty = (60.0 * max(0.0, depth - 0.28) + 60.0 * max(0.0, -0.02 - low) + 0.5 * over + 30.0 * max(0.0, 0.3 - near)
               + 200.0 * max(0.0, -shift[1]))
    head = mats["Head"].translation
    root = mats["Tail1"].translation
    return dist + penalty, {"dist": round(dist, 2), "tip": [round(c, 2) for c in tip], "clash": round(depth, 2), "pair": pair,
                            "low": round(low, 2), "kinks": [round(k) for k in kinks], "penalty": round(penalty, 3),
                            "head": [round(c, 2) for c in head], "root": [round(c, 2) for c in root], "body_gap": round(near, 2)}


def optimise(yaw, about, max_shift, player, starts=3, steps=380):
    """Подбор углов хвоста (и сдвига корпуса не дальше max_shift единиц модели) случайными шагами с остыванием."""
    best_all = None
    for s in range(starts):
        if s == 0:
            angles = [list(a) for a in WHIP_TAIL]
        else:
            angles = [[random.uniform(-110, 10), 0.0, random.uniform(-170, 0)] for _ in range(4)]
            angles.sort(key=lambda a: -a[2])
        shift = [0.0, 0.0]
        score, info = measure(yaw, about, shift, angles, player)
        best = (score, info, [list(a) for a in angles], list(shift))
        for i in range(steps):
            heat = 1.0 - i / steps
            cand = [list(a) for a in angles]
            k = random.randrange(4)
            cand[k][0] += random.gauss(0, 14 * heat + 2)
            cand[k][2] += random.gauss(0, 18 * heat + 2)
            if random.random() < 0.3:  # соседнее звено идёт следом — хвост гнётся плавно
                j = min(3, k + 1)
                cand[j][0] += random.gauss(0, 8 * heat + 1)
                cand[j][2] += random.gauss(0, 10 * heat + 1)
            cs = list(shift)
            if max_shift > 0 and random.random() < 0.35:
                cs[0] += random.gauss(0, 0.25 * heat + 0.03)
                cs[1] = max(0.0, cs[1] + random.gauss(0, 0.25 * heat + 0.03))
                n = math.hypot(*cs)
                if n > max_shift:
                    cs = [c * max_shift / n for c in cs]
            sc, inf = measure(yaw, about, cs, cand, player)
            if sc < score or random.random() < 0.04 * heat:
                angles, shift, score, info = cand, cs, sc, inf
                if sc < best[0]:
                    best = (sc, inf, [list(a) for a in cand], list(cs))
        if best_all is None or best[0] < best_all[0]:
            best_all = best
    score, info, angles, shift = best_all
    info.update(angles=[[round(v, 1) for v in a] for a in angles], shift_studs=[round(c * S, 2) for c in shift], score=round(score, 2))
    return info


PLAYER = 8.5
results = {}
import time  # noqa: E402

t0 = time.time()
for _ in range(20):
    measure(-58, -1.0, (0, 0), WHIP_TAIL, PLAYER)
print("STUDY время одного замера, мс:", round((time.time() - t0) / 20 * 1000, 1))
# как сейчас в утверждённом клипе
_, now = measure(-58, -1.0, (0, 0), WHIP_TAIL, PLAYER)
results["сейчас: 58°, ось между передними лапами, хвост клипа"] = now
print("STUDY сейчас", json.dumps(now, ensure_ascii=False))
plans = [
    ("58°, ось между передними лапами", -58, -1.0, 0.0),
    ("58°, ось в центре корпуса", -58, 0.3, 0.0),
    ("58°, ось в центре, шаг до 3 ст.", -58, 0.3, 1.0),
    ("65°, ось в центре, шаг до 3 ст.", -65, 0.3, 1.0),
    ("75°, ось в центре, шаг до 3 ст.", -75, 0.3, 1.0),
    ("85°, ось в центре, шаг до 3 ст.", -85, 0.3, 1.0),
    ("95°, ось в центре", -95, 0.3, 0.0),
    ("105°, ось в центре", -105, 0.3, 0.0),
]
extra = [float(a) for a in os.environ.get("TAIL_EXTRA", "").split(",") if a]
if extra:
    plans = [(f"{a:g}°, ось в центре, шаг до 3 ст.", -a, 0.3, 1.0) for a in extra]
only = [p for p in os.environ.get("TAIL_PLANS", "").split(";") if p]
for label, yaw, about, max_shift in plans:
    if only and not any(o in label for o in only):
        continue
    info = optimise(yaw, about, max_shift, PLAYER)
    info["gap"] = round(info["dist"] - RADIUS - PLAYER_R, 2)
    # голова: куда ей нужно смотреть, чтобы видеть игрока, и сколько это от оси корпуса
    hx, hy = info["head"][0], info["head"][1]
    want = math.degrees(math.atan2(-(0 - hx), -(-PLAYER - hy)))  # 0 — прямо вперёд (−y), плюс — влево (+x)
    info["head_turn_needed"] = round(want - (-yaw) * -1, 1)
    results[label] = info
    print("STUDY", label, json.dumps(info, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
print("STUDY_OK")
