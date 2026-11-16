"""Анимации Короля-дракона v7 на риге v7_rig.py: клипы, проверки, кадры превью, .blend с действиями.

Как устроено движение (как у Сфинкса, scripts/blender/boss4_sphinx_anim.py):
- Каждый клип — ключевые позы каналов (тело, шея, голова, челюсть, хвост, крылья, лапы, скипетр, глаза). Между ключами
  монотонный кубический сплайн: без остановок в проходных ключах и без перелётов.
- Шея, хвост и пальцы крыльев идут с запаздыванием по звеньям: волна, а не механический поворот.
- Лапы задаются в мире: место запястья или лодыжки и поворот стопы. Суставы считает обратная кинематика на каждом
  кадре, поэтому опорная лапа стоит и не скользит.
- Наплечник следует за плечом на 40 %; полосы мантии — маятник от движения тела.
- Длительности состояний и время удара — как в Config/Battle: Wake + StandUp + ToCombat = 2.4 с, Victory 2.2,
  Defeat 2.4, FallAsleep 1.6, выпад — HitDelay 0.25 с после начала в игре (замах раньше, по плану атаки, ≤ 0.75 с).
  Шаг — под Speed 10 стадов/с.

Режимы (аргумент после папки вывода):
- poses — кадры опорных поз;
- check — проверки всех клипов (anim_report.json);
- render — кадры превью в <папка>/frames/<клип>;
- blend — boss10_v7_rig.blend с действиями;
- all — всё подряд.
Запуск:
  blender --background --factory-startup --python scripts/blender/dragon10/v7_anim.py -- <репо> <папка> <режим> [клипы]
"""

import json
import math
import os
import sys
import time

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "concepts510"))
import ck  # noqa: E402
import v7_rig as R  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
REPO, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
MODE = argv[2] if len(argv) > 2 else "check"
ONLY = [c for c in (argv[3].split(",") if len(argv) > 3 else []) if c]
os.makedirs(OUT, exist_ok=True)

FPS = 30
V = Vector
S2 = R.S2
SIDE = R.SIDE
STUDS = R.SCALE
ARENA_R = 31.0 / STUDS  # радиус арены 62 стада в единицах модели
SAFE_R = (31.0 - 1.0) / STUDS  # запас 1 стад до края
WALK_SPEED = 10.0 / STUDS  # Config/Battle.Bosses Speed = 10 стадов/с
HIT_DELAY = 0.25


# ── повороты ─────────────────────────────────────────────────────────────────────────────────────────────────
def rx(d):
    return Matrix.Rotation(math.radians(d), 4, "X")


def ry(d):
    return Matrix.Rotation(math.radians(d), 4, "Y")


def rz(d):
    return Matrix.Rotation(math.radians(d), 4, "Z")


def raxis(axis, d):
    return Matrix.Rotation(math.radians(d), 4, V(axis).normalized())


def about(p, m):
    """Поворот m вокруг точки p."""
    return Matrix.Translation(p) @ m @ Matrix.Translation(-V(p))


def tr(v):
    return Matrix.Translation(V(v))


# ── кривые ───────────────────────────────────────────────────────────────────────────────────────────────────
class Curve:
    """Монотонный кубический сплайн по ключам [(t, v)]: проходит через ключи, не перелетает, в экстремумах плавно
    тормозит. period — цикл (касательные замкнуты)."""

    def __init__(self, keys, period=None):
        keys = sorted(keys)
        if period:
            keys = [(t - period, v) for t, v in keys[-2:]] + keys + [(t + period, v) for t, v in keys[:2]]
        self.t = [k[0] for k in keys]
        self.v = [k[1] for k in keys]
        self.period = period
        n = len(keys)
        d = [(self.v[i + 1] - self.v[i]) / max(self.t[i + 1] - self.t[i], 1e-6) for i in range(n - 1)]
        m = [0.0] * n
        for i in range(1, n - 1):
            if d[i - 1] * d[i] > 0:
                w1 = 2 * (self.t[i + 1] - self.t[i]) + (self.t[i] - self.t[i - 1])
                w2 = (self.t[i + 1] - self.t[i]) + 2 * (self.t[i] - self.t[i - 1])
                m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
        self.m = m

    def __call__(self, t):
        if self.period:
            t0 = self.t[2]
            t = t0 + (t - t0) % self.period
        if t <= self.t[0]:
            return self.v[0]
        if t >= self.t[-1]:
            return self.v[-1]
        i = max(k for k in range(len(self.t) - 1) if self.t[k] <= t)
        h = self.t[i + 1] - self.t[i]
        s = (t - self.t[i]) / h
        h00, h10, h01, h11 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s, -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
        return h00 * self.v[i] + h10 * h * self.m[i] + h01 * self.v[i + 1] + h11 * h * self.m[i + 1]


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * x * (x * (6 * x - 15) + 10)


def bump(t, t0, t1):
    """0 → 1 → 0 на отрезке [t0, t1] (синус)."""
    if t <= t0 or t >= t1:
        return 0.0
    return math.sin(math.pi * (t - t0) / (t1 - t0))


# ── каналы поз ───────────────────────────────────────────────────────────────────────────────────────────────
WING_CH = ("raise", "sweep", "twist", "elbow", "fan", "fold", "cup")
LEG_CH = ("x", "y", "z", "yaw", "pitch", "heel", "bend")  # bend — локоть/колено наружу (градусы вокруг оси лапы)
FEET = {}
for _s in S2:
    _sh, _el, _wr, _ = R.fore(_s)
    FEET["F" + SIDE[_s]] = _wr
    _hip, _kn, _hk, _an, _ = R.hind(_s)
    FEET["H" + SIDE[_s]] = _an


def stand_pose():
    p = {k: 0.0 for k in ("root_x", "root_y", "root_yaw", "body_x", "body_y", "body_z", "body_p", "body_r", "body_yaw",
                          "neck_p", "neck_y", "neck_curl", "head_p", "head_y", "head_r", "jaw", "tail_p", "tail_y",
                          "tail_curl", "tail_lift", "tail_wave", "mantle_out", "sc_x", "sc_y", "sc_z", "sc_spin",
                          "sc_tilt", "sc_tilt_dir", "shards")}
    p.update(eyes=1.0, glow=1.0, tail_freq=0.0, tail_ground=0.0)
    for s in S2:
        for c in WING_CH:
            p[f"w{SIDE[s]}_{c}"] = 0.0
    for leg, pos in FEET.items():
        p.update({f"{leg}_x": pos.x, f"{leg}_y": pos.y, f"{leg}_z": pos.z, f"{leg}_yaw": 0.0, f"{leg}_pitch": 0.0,
                  f"{leg}_heel": 0.0, f"{leg}_bend": 0.0})
    return p


STAND = stand_pose()


def P(base, **kw):
    """Новая поза: base + изменения. w_… — оба крыла сразу, feet_dy/feet_dz — сдвиг всех лап."""
    p = dict(base)
    for k, v in kw.items():
        if k.startswith("w_"):
            for x in "LR":
                p[f"w{x}_{k[2:]}"] = v
        elif k in ("F_dy", "H_dy", "F_dz", "H_dz", "F_dx", "H_dx"):
            for x in "LR":
                p[f"{k[0]}{x}_{k[-1]}"] = base[f"{k[0]}{x}_{k[-1]}"] + v
        else:
            assert k in p, k
            p[k] = v
    return p


def D(base, **kw):
    """Как P, но значения — прибавки к base."""
    p = dict(base)
    for k, v in kw.items():
        if k.startswith("w_"):
            for x in "LR":
                p[f"w{x}_{k[2:]}"] += v
        else:
            p[k] += v
    return p


# Боевая стойка: присела, грудь ниже, голова вперёд-вниз, крылья приоткрыты, хвост выше.
COMBAT = P(STAND, body_z=-0.32, body_p=2.5, neck_p=6.0, neck_curl=4.0, head_p=-4.0, jaw=4.0, tail_p=7.0, tail_lift=1.5,
           tail_y=-8.0,
           w_raise=12.0, w_sweep=-6.0, w_fan=6.0, w_elbow=6.0, F_dx=0.0)
for _x, _s in (("L", 1), ("R", -1)):
    COMBAT[f"F{_x}_x"] += _s * 0.15
    COMBAT[f"H{_x}_x"] += _s * 0.1
# Сон: лежит на животе, передние лапы вытянуты вперёд, голова на лапах, крылья сложены, хвост обвивает бок.
SLEEP = P(STAND, body_z=-1.9, body_p=-1.5, body_y=0.7, neck_p=100.0, neck_curl=55.0, head_p=-90.0, head_y=8.0, jaw=-14.0,
          tail_p=-6.0, tail_curl=0.0, tail_y=-40.0, tail_ground=1.0, w_fold=1.0, mantle_out=48.0, eyes=0.0)
for _x, _s in (("L", 1), ("R", -1)):
    SLEEP.update({f"F{_x}_x": _s * 2.35, f"F{_x}_y": -3.9 if _s > 0 else -3.6, f"F{_x}_z": 0.9,
                  f"F{_x}_pitch": -52.0, f"H{_x}_x": _s * 2.5, f"H{_x}_y": 3.6, f"H{_x}_z": 0.35, f"H{_x}_heel": 30.0,
                  f"H{_x}_yaw": -_s * 10.0, f"H{_x}_bend": 30.0})


# ── позы → суставы ───────────────────────────────────────────────────────────────────────────────────────────
NECK_W = (0.3, 0.3, 0.24, 0.16)  # доля наклона и поворота шеи по звеньям
NECK_CURL = (1.0, 0.3, -0.6, -0.7)  # изгиб: низ шеи вперёд-вниз, верх назад-вверх
TAIL_W = (0.24, 0.2, 0.16, 0.13, 0.11, 0.09, 0.07)
TAIL_R = (1.02, 0.87, 0.72, 0.6, 0.48, 0.38, 0.3, 0.23)  # полутолщина хвоста в точках (v7: ws / 2)
FOLD = {"raise": 0.0, "sweep": 60.0, "twist": -50.0, "elbow": -45.0}  # сложенное крыло: вдоль спины, без пересечений
FINGER_FAN = (1.0, 0.45, -0.15, -0.6)  # раскрытие пальцев от w_fan
FINGER_FOLD = (-62.0, -38.0, -14.0, 6.0)  # сложенное крыло: пальцы сходятся к предплечью
PAULDRON_FOLLOW = 0.4
COLLAR_FOLLOW = 0.8  # воротник на 80 % идёт с нижней шеей (Neck2): кольцо остаётся вокруг шеи


def blend_tr(a, b, k, c):
    """Промежуточное жёсткое преобразование между a и b (доля k): точка покоя c идёт между a(c) и b(c), поворот —
    между поворотами a и b."""
    qa, qb = a.to_quaternion(), b.to_quaternion()
    return tr((a @ c).lerp(b @ c, k)) @ qa.slerp(qb, k).to_matrix().to_4x4() @ tr(-c)


class Rig:
    def __init__(self, arm):
        self.arm = arm
        self.L = {b.name: b.matrix_local.copy() for b in arm.data.bones}
        self.Li = {k: m.inverted() for k, m in self.L.items()}
        self.parent = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}
        self.head = {b.name: b.head_local.copy() for b in arm.data.bones}
        self.wing = {s: R.wing_frame(s) for s in S2}
        self.fore = {s: R.fore(s) for s in S2}
        self.hind = {s: R.hind(s) for s in S2}
        self.clamps = 0
        self.tail_lift = 0

    # ── ноги ──
    def two_bone(self, S, T, l1, l2, pole):
        """Колено/локоть для цепи S → ? → T с длинами l1, l2, сгиб в сторону pole. Недотяг — выпрямить."""
        d = T - S
        dist = d.length
        u = d / max(dist, 1e-6)
        if dist > l1 + l2 - 1e-3:
            self.clamps += 1
            dist = l1 + l2 - 1e-3
        a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
        h = math.sqrt(max(l1 * l1 - a * a, 0.0))
        pp = pole - u * pole.dot(u)
        pp = pp.normalized() if pp.length > 1e-6 else V((0, 0, 1))
        return S + u * a + pp * h, S + u * dist

    @staticmethod
    def frame(d, n):
        d = d.normalized()
        n = (n - d * n.dot(d)).normalized()
        return Matrix((d, n, d.cross(n))).transposed()

    def aim(self, a0, b0, n0, a1, b1, n1):
        """Перенос кости a0→b0 в a1→b1, плоскость сгиба n0 → n1."""
        R3 = self.frame(b1 - a1, n1) @ self.frame(b0 - a0, n0).inverted()
        return tr(a1) @ R3.to_4x4() @ tr(-a0)

    def leg_front(self, X, s, p):
        sh, el, wr, _ = self.fore[s]
        x = SIDE[s]
        Xb = X["Body"]
        S = Xb @ sh
        T = V((p[f"F{x}_x"], p[f"F{x}_y"], p[f"F{x}_z"]))
        n0 = (el - sh).cross(wr - el)
        pole = Xb.to_3x3() @ (el - (sh + wr) / 2)
        if p[f"F{x}_bend"]:
            pole = raxis(T - S, s * p[f"F{x}_bend"]).to_3x3() @ pole
        E, T = self.two_bone(S, T, (el - sh).length, (wr - el).length, pole)
        n1 = (E - S).cross(T - E)
        if n1.length < 1e-6:
            n1 = Xb.to_3x3() @ n0
        X[f"UpperArm.{x}"] = self.aim(sh, el, n0, S, E, n1)
        X[f"Forearm.{x}"] = self.aim(el, wr, n0, E, T, n1)
        foot = rz(p[f"F{x}_yaw"]) @ rx(p[f"F{x}_pitch"])
        X[f"Paw.{x}"] = tr(T) @ foot @ tr(-wr)

    def leg_hind(self, X, s, p):
        hip, knee, hock, ankle, _ = self.hind[s]
        x = SIDE[s]
        Xb = X["Body"]
        A = V((p[f"H{x}_x"], p[f"H{x}_y"], p[f"H{x}_z"]))
        foot = rz(p[f"H{x}_yaw"]) @ rx(p[f"H{x}_pitch"])
        meta = foot @ rx(-p[f"H{x}_heel"])  # пятка вверх и назад: плюсна ложится
        Hk = A + meta.to_3x3() @ (hock - ankle)
        S = Xb @ hip
        n0 = (knee - hip).cross(hock - knee)
        pole = Xb.to_3x3() @ (knee - (hip + hock) / 2)
        if p[f"H{x}_bend"]:
            pole = raxis(Hk - S, -s * p[f"H{x}_bend"]).to_3x3() @ pole
        Kn, Hk2 = self.two_bone(S, Hk, (knee - hip).length, (hock - knee).length, pole)
        n1 = (Kn - S).cross(Hk2 - Kn)
        X[f"Thigh.{x}"] = self.aim(hip, knee, n0, S, Kn, n1)
        X[f"Shin.{x}"] = self.aim(knee, hock, n0, Kn, Hk2, n1)
        X[f"Meta.{x}"] = tr(Hk2) @ meta @ tr(-hock)
        X[f"HindPaw.{x}"] = tr(A + (Hk2 - Hk)) @ foot @ tr(-ankle)

    # ── крылья ──
    def plane(self, s, d):
        """Поворот в плоскости крыла на d градусов (против часовой в осях u — наружу, v — вверх)."""
        M3 = self.wing[s][0].to_3x3()
        return (M3 @ ry(-d).to_3x3() @ M3.inverted()).to_4x4()

    def wings(self, X, p, lag):
        for s in S2:
            x = SIDE[s]
            M, pts = self.wing[s]
            g = {c: p[f"w{x}_{c}"] for c in WING_CH}
            fold = g["fold"]
            arm_dir = pts["E"] - pts["root"]
            D_arm = (rz(s * (g["sweep"] + fold * FOLD["sweep"])) @ ry(-s * (g["raise"] + fold * FOLD["raise"]))
                     @ raxis(arm_dir, s * (g["twist"] + fold * FOLD["twist"])))
            X[f"WingArm.{x}"] = X["Body"] @ about(pts["root"], D_arm)
            X[f"WingFore.{x}"] = X[f"WingArm.{x}"] @ about(pts["E"], self.plane(s, g["elbow"] + fold * FOLD["elbow"]))
            for i in range(4):
                lg = lag[f"w{x}_fan"][i]
                fan = lg * FINGER_FAN[i] + fold * FINGER_FOLD[i]
                cup = raxis(pts[f"F{i + 1}"] - pts["W"], s * g["cup"] * (0.4 + 0.2 * i))
                X[f"Finger{i + 1}.{x}"] = X[f"WingFore.{x}"] @ about(pts["W"], self.plane(s, fan) @ cup)

    # ── вся поза ──
    def solve(self, p, lag=None):
        """Поза (каналы) → преобразования костей X (мир покоя → мир) в осях арматуры."""
        lag = lag or {}
        X = {}
        X["Root"] = tr((p["root_x"], p["root_y"], 0)) @ rz(p["root_yaw"])
        Rb = rz(p["body_yaw"]) @ rx(p["body_p"]) @ ry(-p["body_r"])
        X["Body"] = X["Root"] @ tr((p["body_x"], p["body_y"], p["body_z"])) @ about(R.BODY_C, Rb)
        nk = lag.get("neck") or [(p["neck_p"], p["neck_y"], p["neck_curl"])] * 4
        prev = "Body"
        for i in range(4):
            npit, nyaw, ncurl = nk[i]
            m = rz(nyaw * NECK_W[i]) @ rx(npit * NECK_W[i] + ncurl * NECK_CURL[i])
            X[f"Neck{i + 1}"] = X[prev] @ about(R.NECK[i], m)
            prev = f"Neck{i + 1}"
        X["Head"] = X["Neck4"] @ about(R.NECK[4], rz(p["head_y"]) @ rx(p["head_p"]) @ ry(p["head_r"]))
        X["Jaw"] = X["Head"] @ about(R.JAW_HINGE, raxis(R.JAW_AXIS, p["jaw"]))
        X["Collar"] = blend_tr(X["Body"], X["Neck2"], COLLAR_FOLLOW, self.head["Collar"])
        tl = lag.get("tail") or [(p["tail_p"], p["tail_y"], p["tail_curl"], p["tail_lift"], 0.0)] * 7
        prev = "Body"
        for i in range(7):
            tp, ty, tc, tlift, wave = tl[i]
            m = rz(ty * TAIL_W[i] + tc + wave) @ rx(tp * TAIL_W[i] + tlift)
            Xi = X[prev] @ about(R.TAIL[i], m)
            # хвост не уходит под землю: звено, конец которого ниже земли, приподнимается у своего начала
            Hd, En = Xi @ R.TAIL[i], Xi @ R.TAIL[i + 1]
            need = TAIL_R[i + 1] + 0.08 - En.z
            if need < 0:  # лёжа (tail_ground) лежащая часть хвоста (звенья 3–7) опускается на землю
                need = need * p["tail_ground"] if i >= 2 else 0.0
            v = En - Hd
            if abs(need) > 1e-4 and v.length > 1e-6:
                ln = v.length
                want = max(-1.0, min(1.0, (En.z + need - Hd.z) / ln))
                delta = math.asin(want) - math.asin(max(-1.0, min(1.0, v.z / ln)))
                axis = v.cross(V((0, 0, 1)))
                if axis.length > 1e-6:
                    Xi = about(Hd, Matrix.Rotation(delta, 4, axis.normalized())) @ Xi
                    self.tail_lift += 1
            X[f"Tail{i + 1}"] = Xi
            prev = f"Tail{i + 1}"
        for s in S2:
            self.leg_front(X, s, p)
            self.leg_hind(X, s, p)
        if "wL_fan" not in lag:
            lag.update({f"w{x}_fan": [p[f"w{x}_fan"]] * 4 for x in "LR"})
        self.wings(X, p, lag)
        for s in S2:
            x = SIDE[s]
            sh = self.fore[s][0]
            rel = (X["Body"].inverted() @ X[f"UpperArm.{x}"]).to_quaternion()
            part = Quaternion().slerp(rel, PAULDRON_FOLLOW).to_matrix().to_4x4()
            X[f"Pauldron.{x}"] = X["Body"] @ about(sh, part)
            for k in range(3):
                name = f"Mantle.{x}{k + 1}"
                out, swing = (lag.get("mantle") or {}).get(name, (0.0, 0.0))
                m = ry(-s * (p["mantle_out"] + out)) @ rx(swing)
                X[name] = X["Body"] @ about(self.head[name], m)
        sc = tr((p["sc_x"], p["sc_y"], p["sc_z"]))
        tilt = rz(p["sc_tilt_dir"]) @ rx(-p["sc_tilt"]) @ rz(-p["sc_tilt_dir"])
        X["ScepterCircle"] = X["Root"]
        X["Scepter"] = X["Root"] @ sc @ about(self.head["Scepter"], tilt @ rz(p["sc_spin"]))
        X["ScepterShards"] = X["Scepter"] @ about(self.head["ScepterShards"], rz(p["shards"]))
        return X

    def apply(self, X):
        for pb in self.arm.pose.bones:
            n = pb.name
            par = self.parent[n]
            Xp = X[par] if par else Matrix.Identity(4)
            pb.matrix_basis = self.Li[n] @ Xp.inverted() @ X[n] @ self.L[n]


# ── клипы ────────────────────────────────────────────────────────────────────────────────────────────────────
class Clip:
    def __init__(self, name, title, duration, keys, loop=False, events=None, start=None, end=None, layers=None,
                 note=""):
        self.name, self.title, self.duration, self.loop = name, title, duration, loop
        self.events = events or {}
        self.start, self.end = start, end
        self.layers = layers or []
        self.note = note
        chans = keys[0][1].keys()
        per = duration if loop else None
        self.curves = {c: Curve([(t, k[c]) for t, k in keys], per) for c in chans}

    def base(self, t):
        return {c: f(t) for c, f in self.curves.items()}

    def frames(self):
        n = int(round(self.duration * FPS))
        return n if self.loop else n + 1


def lagged(clip, t, chans, lags):
    """Значения каналов в моменты t − lag (для звеньев)."""
    out = []
    for lg in lags:
        tt = t - lg
        if not clip.loop:
            tt = max(tt, 0.0)
        out.append(tuple(clip.curves[c](tt) for c in chans))
    return out


NECK_LAG = (0.0, 0.035, 0.07, 0.1)
TAIL_LAG = tuple(0.045 * i for i in range(7))
FAN_LAG = (0.03, 0.06, 0.09, 0.12)


def pose_at(clip, t):
    """Поза клипа в момент t: ключи + слои (дыхание, волна хвоста…) + запаздывание звеньев. Прибавка слоёв к шее,
    хвосту и пальцам идёт без запаздывания (слои и так плавные)."""
    base = clip.base(t)
    p = dict(base)
    for layer in clip.layers:
        layer(p, t, clip)

    def plus(c):
        return p[c] - base[c]

    lag = {"neck": [(a + plus("neck_p"), b + plus("neck_y"), c + plus("neck_curl"))
                    for a, b, c in lagged(clip, t, ("neck_p", "neck_y", "neck_curl"), NECK_LAG)]}
    tail = []
    for i, (tp, ty, tc, tlift) in enumerate(lagged(clip, t, ("tail_p", "tail_y", "tail_curl", "tail_lift"), TAIL_LAG)):
        ph = 2 * math.pi * p["tail_freq"] * (t - TAIL_LAG[i]) - 0.6 * i
        wave = p["tail_wave"] * (0.45 + 0.12 * i) * math.sin(ph)
        tail.append((tp + plus("tail_p"), ty + plus("tail_y"), tc + plus("tail_curl"), tlift + plus("tail_lift"), wave))
    lag["tail"] = tail
    for x in "LR":
        lag[f"w{x}_fan"] = [v[0] + plus(f"w{x}_fan") for v in lagged(clip, t, (f"w{x}_fan",), FAN_LAG)]
    return p, lag


# ── сцена ────────────────────────────────────────────────────────────────────────────────────────────────────
def setup():
    col = ck.reset_scene()
    rig = R.build(col)
    scene = bpy.context.scene
    scene.render.fps = FPS
    return col, rig


def eval_points(obj):
    deps = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(deps)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    return co.reshape(-1, 3)


def stage(col):
    """Сцена превью: широкий пол, тёмный фон, круг арены 62 стада (радиус 31) и центр, свет как у листов v7."""
    scene = bpy.context.scene
    ck.engine(scene, samples=int(os.environ.get("SAMPLES", "24")))
    world = bpy.data.worlds.new("Stage")
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.03, 0.033, 0.045, 1)
    bg.inputs["Strength"].default_value = 1.0
    scene.world = world
    me = bpy.data.meshes.new("Floor")
    me.from_pydata([(-900, -900, 0), (900, -900, 0), (900, 900, 0), (-900, 900, 0)], [], [(0, 1, 2, 3)])
    fm = bpy.data.materials.new("FloorM")
    fm.use_nodes = True
    fb = next(n for n in fm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    fb.inputs["Base Color"].default_value = (0.11, 0.115, 0.14, 1)
    fb.inputs["Roughness"].default_value = 0.8
    me.materials.append(fm)
    col.objects.link(bpy.data.objects.new("Floor", me))
    am = bpy.data.materials.new("ArenaM")
    am.use_nodes = True
    ab = next(n for n in am.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    ab.inputs["Base Color"].default_value = (0.9, 0.75, 0.3, 1)
    ab.inputs["Emission Color"].default_value = (1.0, 0.78, 0.3, 1)
    ab.inputs["Emission Strength"].default_value = 1.2
    for name, r0, r1 in (("ArenaRing", ARENA_R - 0.06, ARENA_R + 0.06), ("SafeRing", SAFE_R - 0.025, SAFE_R + 0.025)):
        n = 128
        verts = [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), 0.012) for r in (r0, r1)
                 for i in range(n)]
        faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        rm = bpy.data.meshes.new(name)
        rm.from_pydata(verts, [], faces)
        rm.materials.append(am)
        col.objects.link(bpy.data.objects.new(name, rm))
    for name, kind, loc, energy, size in (("Key", "AREA", (-14, -20, 22), 9000, 14), ("Fill", "AREA", (18, -12, 9), 3500, 14),
                                          ("Rim", "AREA", (6, 22, 16), 6000, 12)):
        data = bpy.data.lights.new(name, kind)
        data.energy, data.size = energy, size
        light = bpy.data.objects.new(name, data)
        light.location = loc
        light.rotation_euler = (V(loc) - V((0, 0, 4))).to_track_quat("Z", "Y").to_euler()
        scene.collection.objects.link(light)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = -0.2
    return cam


VIEWS = {  # камера: (глаз, цель, объектив)
    "34": ((-22.0, -31.0, 13.0), (0.0, -0.5, 4.6), 42),
    "34r": ((24.0, -30.0, 12.0), (0.0, -0.5, 4.6), 42),
    "side": ((-38.0, -1.0, 9.0), (0.0, 0.0, 4.6), 45),
    "front": ((0.0, -38.0, 10.0), (0.0, 0.0, 5.0), 42),
    "back": ((16.0, 30.0, 14.0), (0.0, 0.0, 4.6), 42),
    "top": ((0.0, -6.0, 46.0), (0.0, 0.0, 0.0), 35),
    "sideL": ((40.0, -2.0, 10.0), (0.0, -0.3, 5.2), 36),
    "wide": ((-25.0, -36.0, 15.0), (0.0, -0.5, 6.2), 36),
    "wide_r": ((26.0, -35.0, 14.0), (0.0, -0.5, 6.0), 38),
}


def show(rg, rig, pose, lag=None):
    rg.apply(rg.solve(dict(pose), lag))
    rig["arm"]["eyes"] = pose["eyes"]
    rig["arm"]["glow"] = pose["glow"]
    bpy.context.view_layer.update()


def jaw_point(local):
    L, H = R.HL, R.HH
    h = V((0, -0.12 * L, 0))
    J = tr(h) @ rx(17) @ tr(-h)
    return R.HEAD_M @ J @ V(local)


JAW_LOW = jaw_point((0, -0.42 * R.HL, -0.58 * R.HH))
NOSE_DIR = (R.HEAD_M.to_3x3() @ V((0, -1, 0))).normalized()


SNOUT = R.HEAD_M @ V((0, -1.08 * R.HL, 0.28 * R.HH))


def head_fit(rg, base, jaw_z=0.35, level=4.0, y_range=(-8.2, -5.2), reach=10.0, neck1=48.0):
    """Шея и голова так, чтобы челюсть легла на землю (jaw_z), голова почти ровно (level — нос вверх, градусы)."""
    best = None
    for npit in range(20, 181, 5):
        for curl in range(-30, 61, 5):
            for hp in range(-110, 41, 5):
                p = dict(base, neck_p=float(npit), neck_curl=float(curl), head_p=float(hp))
                X = rg.solve(p)
                low = X["Jaw"] @ JAW_LOW
                nose = X["Head"].to_3x3() @ NOSE_DIR
                pitch = math.degrees(math.asin(max(-1.0, min(1.0, nose.z))))  # плюс — нос вверх
                org = X["Head"] @ R.HEAD_ORIGIN
                necks = [X[f"Neck{i + 1}"] @ R.NECK[i + 1] for i in range(4)]
                pen = sum(max(0.0, 1.6 - q.z) for q in necks)
                yb = max(0.0, y_range[0] - org.y) + max(0.0, org.y - y_range[1])
                tip = X["Head"] @ SNOUT
                far = max(0.0, math.hypot(tip.x, tip.y) - reach)
                n1 = max(0.0, npit * NECK_W[0] + curl * NECK_CURL[0] - neck1)
                cost = (abs(low.z - jaw_z) * 3 + abs(pitch - level) / 15 + pen * 4 + yb * 3 + abs(curl) / 200
                        + far * 6 + n1 / 10)
                if best is None or cost < best[0]:
                    best = (cost, npit, curl, hp, round(low.z, 2), round(pitch, 1), tuple(round(c, 2) for c in org))
    return best


def main_poses(col, rig, rg, poses, views=("34", "side")):
    """Кадры опорных поз (самопроверка рига)."""
    cam = stage(col)
    for name, pose in poses:
        show(rg, rig, pose)
        for view in views:
            eye, target, lens = VIEWS[view]
            ck.shot(cam, os.path.join(OUT, f"pose_{name}_{view}.png"), eye, target, lens, (960, 640))
    print("POSES", rg.clamps, flush=True)


# ── слои движения ───────────────────────────────────────────────────────────────────────────────────────────
def scepter_idle(p, t, clip):
    """Скипетр парит: покачивание и медленный поворот. В игре это делает скрипт постоянно, здесь — для превью."""
    d = clip.duration
    if clip.loop:
        spin = 90 * max(0, round(d * 22 / 90)) * t / d
        shards = 120 * max(1, round(d * 30 / 120)) * t / d
        bob = math.sin(2 * math.pi * max(1, round(d / 2.4)) * t / d)
    else:
        spin, shards, bob = 22 * t, 30 * t, math.sin(2 * math.pi * t / 2.4)
    p["sc_z"] += 0.14 * bob
    p["sc_spin"] += spin
    p["shards"] += shards


def breath(period, z=0.05, pitch=0.7, wing=2.5, fan=1.5, jaw=1.2, neck=-0.8, head=0.6, until=None):
    """Дыхание: грудь и спина поднимаются, крылья и пальцы чуть раскрываются, пасть приоткрывается на вдохе."""
    def layer(p, t, clip):
        if until is not None and t > until:
            return
        w = math.sin(2 * math.pi * t / period)
        p["body_z"] += z * w
        p["body_p"] -= pitch * w
        p["neck_p"] += neck * w
        p["head_p"] += head * w
        p["jaw"] += jaw * max(w, 0.0)
        for x in "LR":
            p[f"w{x}_raise"] += wing * w
            p[f"w{x}_fan"] += fan * w
    return layer


def idle_look(p, t, clip):
    """Боевая стойка: оглядывается, переносит вес, раз моргает."""
    a = 2 * math.pi * t / clip.duration
    p["head_y"] += 9 * math.sin(a)
    p["neck_y"] += 5 * math.sin(a - 0.6)
    p["head_p"] += 2.5 * math.sin(2 * a + 1.0)
    p["head_r"] += 2.0 * math.sin(a + 0.3)
    p["body_r"] += 1.3 * math.sin(a + 0.4)
    p["body_x"] += 0.07 * math.sin(a + 0.4)
    blink = max(0.0, 1 - abs(t - 2.65) / 0.09)
    p["eyes"] = min(p["eyes"], 1 - 0.92 * blink)


WALK_T = 1.2  # цикл шага, с: при скорости 10 стадов/с шаг 12 стадов
WALK_DUTY = 0.62  # доля опоры
WALK_PHASE = {"HL": 0.0, "FL": 0.25, "HR": 0.5, "FR": 0.75}  # латеральная последовательность: тяжёлый шаг
LEG_RU = {"FL": "левая передняя", "FR": "правая передняя", "HL": "левая задняя", "HR": "правая задняя"}
WALK_HOME = {"FL": (2.45, -3.05), "FR": (-2.45, -3.05), "HL": (2.15, 3.1), "HR": (-2.15, 3.1)}


def walk_layer(p, t, clip):
    """Шаг на месте под скорость 10 стадов/с: опорная лапа уходит назад со скоростью босса и не скользит по земле
    (босс в игре движется вперёд), переносимая — по дуге. Тело покачивается к опорной стороне, голова держит взгляд."""
    S = WALK_SPEED * WALK_DUTY * WALK_T
    for leg, ph0 in WALK_PHASE.items():
        ph = (t / WALK_T - ph0) % 1.0
        x0, y0 = WALK_HOME[leg]
        z0 = FEET[leg].z
        front = leg[0] == "F"
        if ph < WALK_DUTY:
            u = ph / WALK_DUTY
            y, z = y0 - S / 2 + S * u, z0
            pitch = 0.0
            heel = -16 * smooth((u - 0.55) / 0.45)
        else:
            u = (ph - WALK_DUTY) / (1 - WALK_DUTY)
            y = y0 + S / 2 - S * smooth(u)
            z = z0 + (0.8 if front else 0.62) * math.sin(math.pi * u)
            pitch = 22 * math.sin(math.pi * u) * (1 - u) - 6 * math.sin(math.pi * u) * u
            heel = -16 * (1 - smooth(u * 2.5)) + 8 * math.sin(math.pi * u)
        p[f"{leg}_x"], p[f"{leg}_y"], p[f"{leg}_z"], p[f"{leg}_pitch"] = x0, y, z, pitch
        if not front:
            p[f"{leg}_heel"] = heel
    a = 2 * math.pi * t / WALK_T
    p["body_z"] += -0.08 * (0.5 - 0.5 * math.cos(2 * a))
    p["body_r"] += 1.8 * math.sin(a)
    p["body_p"] += 0.8 * math.sin(2 * a + 0.5)
    p["body_yaw"] += 1.6 * math.sin(a + math.pi / 2)
    p["body_x"] += 0.06 * math.sin(a)
    p["head_p"] -= 0.8 * math.sin(2 * a + 0.5)
    p["head_y"] -= 1.6 * math.sin(a + math.pi / 2)
    p["neck_p"] += 1.5 * math.sin(2 * a - 0.4)
    for x in "LR":
        p[f"w{x}_raise"] += 2.5 * math.sin(2 * a - 0.9)


def rot2(x, y, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return x * c - y * s, x * s + y * c


TURN_STEPS = {"FL": ((0.2, 0.55), (0.8, 1.15)), "HR": ((0.26, 0.6), (0.86, 1.2)),
              "FR": ((0.45, 0.8), (1.05, 1.4)), "HL": ((0.5, 0.85), (1.1, 1.45))}


def turn_layer(p, t, clip):
    """Разворот на месте на 90° влево: тело поворачивается плавно, лапы переступают дважды (45° и 90°) и между
    шагами стоят на земле."""
    for leg, steps in TURN_STEPS.items():
        x0, y0, z0 = COMBAT[f"{leg}_x"], COMBAT[f"{leg}_y"], COMBAT[f"{leg}_z"]
        ang, lift, pitch = 0.0, 0.0, 0.0
        for k, (t0, t1) in enumerate(steps):
            u = min(max((t - t0) / (t1 - t0), 0.0), 1.0)
            ang += 45.0 * smooth(u)
            lift += (0.75 if leg[0] == "F" else 0.6) * math.sin(math.pi * u)
            pitch += 18 * math.sin(math.pi * u)
        x, y = rot2(x0, y0, ang)
        p[f"{leg}_x"], p[f"{leg}_y"], p[f"{leg}_z"] = x, y, z0 + lift
        p[f"{leg}_yaw"], p[f"{leg}_pitch"] = ang, pitch


# ── клипы ────────────────────────────────────────────────────────────────────────────────────────────────────
def K(base, **kw):
    return P(base, **kw)


def clip_sleep():
    return Clip("sleep_idle", "Сон", 6.4, [(0.0, SLEEP), (6.4, SLEEP)], loop=True,
                layers=[breath(3.2, z=0.06, pitch=0.5, wing=1.5, fan=1.0, jaw=0.6, neck=0.0, head=0.0), scepter_idle],
                note="цикл: два вдоха по 3.2 с, хвост и крылья дышат вместе с грудью")


def clip_wake():
    lie_up = P(SLEEP, neck_p=38.0, neck_curl=22.0, head_p=-36.0, head_y=-6.0, jaw=-6.0, eyes=1.0, tail_curl=-10.0,
               w_fold=0.9)
    look = P(lie_up, neck_p=22.0, neck_curl=8.0, head_p=-16.0, head_y=-12.0, w_fold=0.75)
    rise = P(STAND, body_z=-1.0, body_p=3.0, neck_p=8.0, head_p=-10.0, head_y=-4.0, w_fold=0.4, w_raise=6.0,
             mantle_out=20.0, tail_y=-40.0, tail_p=12.0)
    for x, s in (("L", 1), ("R", -1)):
        rise.update({f"F{x}_x": s * 2.4, f"F{x}_y": -3.6, f"F{x}_z": 0.9, f"F{x}_pitch": -18.0,
                     f"H{x}_heel": 18.0, f"H{x}_x": s * 2.3, f"H{x}_y": 3.2, f"H{x}_z": 0.36})
    stood = P(STAND, body_z=-0.12, w_fold=0.08, w_raise=16.0, neck_p=3.0, head_p=-8.0)
    roar = P(COMBAT, w_raise=32.0, w_fan=16.0, w_elbow=10.0, w_sweep=10.0, jaw=12.0, head_p=-10.0, neck_p=-4.0,
             body_p=-2.0)
    keys = [(0.0, SLEEP), (0.18, P(SLEEP, eyes=0.0)), (0.42, P(SLEEP, eyes=1.0, neck_p=82.0, neck_curl=46.0, head_p=-76.0)),
            (0.72, lie_up), (1.0, look), (1.45, rise), (1.9, stood), (2.15, roar), (2.4, COMBAT)]
    return Clip("wake", "Пробуждение", 2.4, keys, events={"открыл глаза": 0.3, "лёжа (конец Wake)": 1.0,
                                                           "стойка (конец StandUp)": 1.9, "рык (ToCombat)": 2.15},
                start="sleep", end="combat", layers=[scepter_idle],
                note="Wake 1.0 + StandUp 0.9 + ToCombat 0.5 с, как Config/Battle.Timeline")


def clip_combat():
    return Clip("combat_idle", "Боевая стойка", 3.6, [(0.0, COMBAT), (3.6, COMBAT)], loop=True,
                layers=[breath(1.8), idle_look, scepter_idle],
                note="цикл: два вдоха, взгляд по сторонам, перенос веса, моргание")


def clip_walk():
    base = P(COMBAT, body_z=-0.24, w_raise=6.0, w_fold=0.12, head_p=-2.0, jaw=2.0, tail_wave=4.0,
             tail_freq=1 / WALK_T)
    return Clip("walk", "Ходьба", WALK_T, [(0.0, base), (WALK_T, base)], loop=True,
                layers=[walk_layer, breath(WALK_T / 2, z=0.0, pitch=0.0, wing=0.0, fan=1.0, jaw=1.0, neck=0.0,
                                           head=0.0), scepter_idle],
                events={f"{LEG_RU[leg]} на земле": round(ph * WALK_T, 3) for leg, ph in WALK_PHASE.items()},
                note=f"шаг на месте под 10 стадов/с (босс идёт вперёд в игре): цикл {WALK_T} с, шаг 12 стадов")


def clip_turn():
    keys = [(0.0, COMBAT), (0.1, P(COMBAT, head_y=8.0)),
            (0.42, P(COMBAT, root_yaw=12.0, head_y=24.0, neck_y=14.0, body_yaw=7.0, tail_y=6.0)),
            (0.9, P(COMBAT, root_yaw=50.0, head_y=14.0, neck_y=10.0, body_yaw=6.0, tail_y=20.0, body_z=-0.42)),
            (1.35, P(COMBAT, root_yaw=84.0, head_y=2.0, neck_y=2.0, body_yaw=1.0, tail_y=14.0)),
            (1.8, P(COMBAT, root_yaw=90.0))]
    return Clip("turn_left", "Разворот на месте", 1.8, keys, layers=[turn_layer, scepter_idle],
                events={"конец поворота корня": 1.5}, start="combat", end="combat",
                note="поворот корня на 90° влево (в игре — поворот модели), лапы переступают дважды")


def clip_claw():
    wind = P(COMBAT, body_y=0.35, body_x=-0.2, body_r=4.0, body_p=-5.0, body_z=-0.24, neck_p=-8.0, neck_y=6.0,
             head_p=-10.0, head_y=10.0, jaw=10.0, w_raise=30.0, w_fan=10.0, w_sweep=10.0, tail_p=12.0,
             tail_y=-10.0, FL_x=3.05, FL_y=-2.55, FL_z=3.7, FL_pitch=40.0, FL_bend=50.0)
    peak = P(wind, body_y=0.45, body_p=-8.0, head_p=-14.0, jaw=12.0, w_raise=36.0, FL_x=3.3, FL_y=-2.25, FL_z=4.5,
             FL_pitch=60.0, FL_bend=62.0)
    hit = P(COMBAT, body_y=-0.55, body_p=10.0, body_z=-0.62, body_r=-3.0, body_yaw=-6.0, neck_p=18.0, head_p=6.0,
            head_y=4.0, jaw=12.0, w_raise=14.0, w_sweep=-14.0, tail_y=10.0, tail_p=2.0,
            FL_x=1.3, FL_y=-5.1, FL_z=1.3, FL_pitch=-6.0, FL_bend=12.0)
    press = P(hit, body_z=-0.7, body_p=11.0, neck_p=20.0, jaw=12.0, FL_pitch=0.0)
    back = P(COMBAT, body_y=-0.1, body_z=-0.38, FL_x=2.0, FL_y=-4.1, FL_z=1.9, FL_pitch=10.0, jaw=6.0, w_raise=16.0)
    keys = [(0.0, COMBAT), (0.3, wind), (0.55, peak), (0.8, hit), (0.92, press), (1.15, back), (1.4, COMBAT)]
    return Clip("claw_swipe", "Удар лапой", 1.4, keys, layers=[scepter_idle], start="combat", end="combat",
                events={"начало выпада в игре (AttackAt)": 0.55, "контакт: удар лапы": 0.8},
                note="замах 0.55 с (по плану атаки), удар через HitDelay 0.25 с")


def clip_bite():
    coil = P(COMBAT, neck_p=-16.0, neck_curl=-10.0, head_p=-12.0, jaw=8.0, body_y=0.3, body_p=-4.0, w_raise=26.0,
             w_fan=8.0, w_sweep=10.0, tail_p=10.0)
    peak = P(coil, neck_p=-22.0, neck_curl=-14.0, head_p=-18.0, jaw=12.0, body_y=0.4, body_p=-6.0, body_z=-0.36)
    snap = P(COMBAT, neck_p=26.0, neck_curl=12.0, head_p=12.0, jaw=-9.0, body_y=-0.5, body_p=8.0, body_z=-0.55,
             w_raise=12.0, w_sweep=-10.0, tail_p=2.0)
    shake = [P(snap, neck_p=28.0, head_y=10.0, head_r=8.0), P(snap, neck_p=27.0, head_y=-9.0, head_r=-7.0),
             P(snap, neck_p=26.0, head_y=5.0, head_r=4.0)]
    release = P(COMBAT, neck_p=14.0, head_p=4.0, jaw=6.0, body_y=-0.25, body_z=-0.42)
    keys = [(0.0, COMBAT), (0.3, coil), (0.5, peak), (0.75, snap), (0.86, shake[0]), (0.96, shake[1]),
            (1.05, shake[2]), (1.18, release), (1.4, COMBAT)]
    return Clip("bite", "Укус", 1.4, keys, layers=[scepter_idle], start="combat", end="combat",
                events={"начало выпада в игре (AttackAt)": 0.5, "контакт: пасть смыкается": 0.75})


def clip_tail():
    wind = P(COMBAT, body_yaw=7.0, body_x=-0.15, tail_y=30.0, tail_curl=-2.0, tail_p=14.0, head_y=14.0, neck_y=8.0, jaw=6.0,
             w_raise=20.0, w_sweep=8.0)
    peak = P(wind, body_yaw=9.0, tail_y=40.0, tail_curl=-2.0, tail_p=18.0)
    hit = P(COMBAT, body_yaw=-12.0, body_x=0.25, body_z=-0.45, tail_y=-80.0, tail_curl=2.0, tail_p=10.0,
            head_y=20.0, neck_y=12.0, jaw=12.0, wR_raise=30.0, wL_raise=10.0, w_sweep=8.0, body_r=3.0)
    follow = P(hit, body_yaw=-14.0, tail_y=-90.0, tail_curl=3.0, tail_p=8.0)
    keys = [(0.0, COMBAT), (0.32, wind), (0.5, peak), (0.75, hit), (0.9, follow), (1.15, P(COMBAT, tail_y=-30.0)),
            (1.4, COMBAT)]
    return Clip("tail_strike", "Удар хвостом", 1.4, keys, layers=[scepter_idle], start="combat", end="combat",
                events={"начало выпада в игре (AttackAt)": 0.5, "контакт: хвост по левому боку": 0.75})


def clip_wings():
    up = P(COMBAT, w_raise=48.0, w_sweep=10.0, w_elbow=12.0, w_fan=12.0, w_twist=-10.0, body_p=-6.0, body_z=-0.22,
           neck_p=-3.0, head_p=-8.0, jaw=8.0, tail_p=12.0)
    peak = P(up, w_raise=57.0, w_fan=16.0, w_sweep=13.0, body_p=-8.0, head_p=-10.0, jaw=12.0)
    down = P(COMBAT, w_raise=-12.0, w_sweep=-22.0, w_twist=18.0, w_cup=25.0, w_fan=4.0, body_p=6.0, body_z=-0.5,
             body_y=-0.3, neck_p=16.0, head_p=-2.0, jaw=10.0, tail_p=-4.0)
    low = P(down, w_raise=-17.0, w_cup=30.0, w_sweep=-18.0)
    keys = [(0.0, COMBAT), (0.35, up), (0.55, peak), (0.8, down), (0.95, low),
            (1.15, P(COMBAT, w_raise=24.0, w_fan=10.0, jaw=6.0)), (1.4, COMBAT)]
    return Clip("wing_buffet", "Взмах крыльями", 1.4, keys, layers=[scepter_idle], start="combat", end="combat",
                events={"начало выпада в игре (AttackAt)": 0.55, "контакт: порыв ветра": 0.8})


SC_FRONT = (1.4, -3.4, 2.2)  # скипетр справа-спереди на высоте груди: (−3.0, −7.4), центр на высоте 5.4  # скипетр справа-спереди: от места покоя (−5, −4.6) к (−2.0, −8.0), центр на высоте 4.2


def clip_magic():
    fx, fy, fz = SC_FRONT
    keys = [
        (0.0, COMBAT),
        (0.3, P(COMBAT, neck_p=-6.0, head_p=-12.0, jaw=10.0, w_raise=30.0, w_fan=10.0, w_sweep=10.0, sc_z=1.3,
                glow=1.5,
                sc_spin=40.0, shards=60.0)),
        (0.8, P(COMBAT, neck_p=-2.0, head_p=-6.0, head_y=-12.0, jaw=6.0, w_raise=36.0, w_fan=12.0, w_sweep=10.0,
                sc_x=0.4, sc_y=-1.8, sc_z=3.0, glow=2.0, sc_spin=160.0, shards=240.0)),
        (1.2, P(COMBAT, neck_p=2.0, head_p=2.0, head_y=-20.0, neck_y=-6.0, jaw=4.0, w_raise=42.0, w_fan=16.0,
                w_elbow=10.0,
                w_sweep=10.0,
                sc_x=fx, sc_y=fy, sc_z=fz, glow=2.4, sc_spin=270.0, shards=420.0)),
        (1.6, P(COMBAT, neck_p=-2.0, head_p=0.0, head_y=-18.0, neck_y=-6.0, jaw=8.0, body_p=-5.0, body_y=0.3,
                w_raise=48.0,
                w_fan=18.0, w_elbow=12.0, w_sweep=12.0, sc_x=fx, sc_y=fy, sc_z=fz + 0.3, glow=3.0, sc_spin=360.0, shards=720.0)),
        (1.95, P(COMBAT, neck_p=12.0, head_p=4.0, head_y=-8.0, jaw=12.0, body_p=6.0, body_y=-0.4, body_z=-0.5, w_raise=26.0,
                 w_sweep=-12.0, sc_x=fx, sc_y=fy - 0.25, sc_z=fz + 0.2, sc_tilt=20.0, sc_tilt_dir=180.0, glow=3.0,
                 sc_spin=405.0, shards=900.0)),
        (2.3, P(COMBAT, neck_p=6.0, jaw=6.0, w_raise=20.0, sc_x=fx * 0.8, sc_y=fy * 0.8, sc_z=2.6, sc_tilt=10.0,
                sc_tilt_dir=180.0, glow=1.6, sc_spin=470.0, shards=1020.0)),
        (2.9, P(COMBAT, sc_spin=540.0, shards=1080.0, glow=1.0)),
        (3.0, P(COMBAT, sc_spin=540.0, shards=1080.0, glow=1.0)),
    ]
    return Clip("magic_scepter", "Магия скипетра", 3.0, keys, start="combat", end="combat",
                events={"призыв скипетра": 0.3, "скипетр перед драконом": 1.2, "заклинание": 1.95,
                        "скипетр на месте": 2.9},
                note="нового выпада в игре нет: клип готов, как он встанет в бой — решает владелец")


def clip_hit():
    peak = P(COMBAT, neck_p=-14.0, neck_y=8.0, head_p=-16.0, head_y=16.0, head_r=-10.0, jaw=10.0, body_y=0.3,
             body_p=-4.0, body_r=3.0, w_raise=26.0, w_fan=12.0, w_sweep=10.0, tail_y=12.0, eyes=0.55)
    keys = [(0.0, COMBAT), (0.1, peak), (0.26, P(COMBAT, neck_p=3.0, head_y=-3.0, jaw=6.0, eyes=1.0)),
            (0.6, COMBAT)]
    return Clip("hit", "Получение урона", 0.6, keys, layers=[scepter_idle], start="combat", end="combat",
                events={"пик реакции": 0.1})


def clip_victory():
    rear = P(COMBAT, body_p=-16.0, body_z=0.42, body_y=0.25, w_raise=32.0, w_fan=16.0, w_elbow=10.0, w_sweep=22.0,
             neck_p=-4.0, head_p=-16.0, jaw=12.0, tail_p=16.0, tail_wave=6.0, tail_freq=1.6)
    for x, s in (("L", 1), ("R", -1)):
        rear.update({f"F{x}_x": s * 2.5, f"F{x}_y": -3.0, f"F{x}_z": 2.2, f"F{x}_pitch": 38.0})
    top = P(rear, body_p=-20.0, head_p=-19.0)
    for x in "LR":
        top[f"F{x}_z"] = 2.7
        top[f"F{x}_y"] = -2.85
        top[f"F{x}_pitch"] = 50.0
    slam = P(COMBAT, body_p=5.0, body_z=-0.56, w_raise=30.0, w_sweep=-10.0, neck_p=12.0, head_p=6.0, jaw=12.0,
             tail_wave=3.0, tail_freq=1.6)
    proud = P(STAND, neck_p=-8.0, head_p=-12.0, w_raise=18.0, w_fan=6.0, body_z=-0.1)
    keys = [(0.0, COMBAT), (0.6, rear), (0.95, top), (1.3, slam), (1.45, P(slam, body_z=-0.62)), (1.9, proud),
            (2.2, STAND)]
    return Clip("victory", "Победа", 2.2, keys, layers=[scepter_idle], start="combat", end="stand",
                events={"встал на дыбы": 0.6, "удар лапами о землю": 1.3},
                note="Victory 2.2 с; дальше в игре — возвращение домой шагом")


def lying(base, **kw):
    p = P(base, body_z=-1.85, body_r=-8.0, body_p=2.0, body_y=0.75, neck_p=94.0, neck_curl=50.0, head_p=-88.0,
          head_y=14.0,
          w_raise=-12.0, w_fold=0.55, w_fan=-10.0, jaw=-6.0, eyes=0.25, tail_p=-10.0, tail_curl=0.0, tail_y=-30.0, tail_ground=1.0,
          mantle_out=40.0)
    for x, s in (("L", 1), ("R", -1)):
        p.update({f"F{x}_x": s * 2.55, f"F{x}_y": -3.9, f"F{x}_z": 0.9, f"F{x}_pitch": -48.0,
                  f"H{x}_x": s * 2.5, f"H{x}_y": 3.6, f"H{x}_z": 0.35, f"H{x}_heel": 30.0, f"H{x}_yaw": -s * 10.0,
                  f"H{x}_bend": 30.0})
    p.update(kw)
    return p


def clip_defeat():
    stagger = P(COMBAT, neck_p=-10.0, head_p=-10.0, head_y=14.0, jaw=12.0, body_y=0.35, body_r=5.0, w_raise=26.0,
                w_sweep=12.0, eyes=0.6)
    buckle = P(COMBAT, body_z=-1.2, body_r=-6.0, body_p=4.0, body_y=0.8, neck_p=20.0, neck_curl=14.0, head_p=-16.0,
               w_raise=-10.0, w_fold=0.3, w_fan=-10.0, eyes=0.3, jaw=8.0, mantle_out=20.0)
    for x in "LR":
        buckle[f"F{x}_y"] = -4.0
    down = lying(COMBAT)
    dazed = lying(COMBAT, neck_p=84.0, head_p=-72.0, eyes=0.35)
    lift = lying(COMBAT, neck_p=50.0, neck_curl=26.0, head_p=-40.0, head_y=4.0, eyes=0.8, body_r=-4.0)
    rising = P(STAND, body_z=-0.75, body_r=-2.0, neck_p=14.0, head_p=-12.0, w_fold=0.25, mantle_out=10.0)
    for x, s in (("L", 1), ("R", -1)):
        rising.update({f"F{x}_x": s * 2.45, f"F{x}_y": -3.5, f"F{x}_z": 0.9 + 0.3 * (s > 0), f"F{x}_pitch": -12.0,
                       f"H{x}_heel": 16.0})
    keys = [(0.0, COMBAT), (0.2, stagger), (0.55, buckle), (0.95, down), (1.3, dazed), (1.62, lift), (2.0, rising),
            (2.4, STAND)]
    return Clip("defeat", "Поражение", 2.4, keys, layers=[breath(0.7, z=0.04, pitch=0.6, wing=1.5, until=1.62),
                                                         scepter_idle],
                start="combat", end="stand", events={"лежит": 0.95, "начинает вставать": 1.62},
                note="Defeat 2.4 с: повалился и встаёт; дальше в игре — домой шагом и «Засыпание»")


def clip_fall_asleep():
    sit = P(STAND, body_z=-0.6, body_p=-4.0, neck_p=5.0, w_fold=0.5, tail_curl=-4.0)
    lie = P(SLEEP, neck_p=40.0, neck_curl=20.0, head_p=-40.0, head_y=4.0, eyes=0.7, jaw=-4.0)
    lower = P(SLEEP, neck_p=86.0, neck_curl=45.0, head_p=-80.0, eyes=0.2, jaw=-10.0)
    keys = [(0.0, STAND), (0.3, sit), (0.88, lie), (1.25, lower), (1.6, SLEEP)]
    return Clip("fall_asleep", "Засыпание", 1.6, keys, layers=[scepter_idle], start="stand", end="sleep",
                events={"лёг (поза «лёжа»)": 0.88, "закрыл глаза": 1.4},
                note="FallAsleep 1.6 с: лёг, голова на землю, глаза закрылись")


CLIPS = [clip_sleep, clip_wake, clip_combat, clip_walk, clip_turn, clip_claw, clip_bite, clip_tail, clip_wings,
         clip_magic, clip_hit, clip_victory, clip_defeat, clip_fall_asleep]


# ── мантия: маятник ──────────────────────────────────────────────────────────────────────────────────────────
SWING_LIMIT = ((-1.0, 20.0), (-10.0, 10.0), (-20.0, 1.0))  # полоса 1 не вперёд (локоть), 3 не назад (бедро)
G = 9.81 / 0.28 / STUDS  # ускорение свободного падения в единицах модели (1 стад ≈ 0.28 м)
MANTLE_W, MANTLE_Z = 6.5, 0.38  # собственная частота (рад/с) и затухание тяжёлой ткани


LEG_BONES = ("UpperArm", "Forearm", "Paw", "Thigh", "Shin", "Meta", "HindPaw")
STRIP_REST = 13.0  # полосы и так отходят от бока к подолу на ~13°


def leg_samples(rig):
    """Точки поверхности лап (покой) для расчёта мантии: не больше 160 на кость."""
    obj = rig["dragon"]
    out = {}
    for s in S2:
        for b in LEG_BONES:
            name = f"{b}.{SIDE[s]}"
            g = obj.vertex_groups[name].index
            pts = [v.co[:] for v in obj.data.vertices if any(x.group == g and x.weight > 0.5 for x in v.groups)]
            step = max(1, len(pts) // 160)
            out[name] = np.array(pts[::step])
    return out


PUSH_OUT = 26.0  # наружу лапа отводит полосу не больше чем на столько; остальное — качание вперёд-назад


def mantle_push(rg, X):
    """Для каждой полосы: (угол наружу, качание), при которых лапы остаются между боком и тканью. Передняя лапа
    отводит полосу назад, задняя — вперёд: ткань не взлетает горизонтально."""
    Bi = np.array(X["Body"].inverted())
    res = {}
    for x, s in (("L", 1), ("R", -1)):
        sets = {}
        for kind, bones in (("F", ("UpperArm", "Forearm", "Paw")), ("H", ("Thigh", "Shin", "Meta", "HindPaw"))):
            pts = []
            for b in bones:
                M = Bi @ np.array(X[f"{b}.{x}"])
                pts.append(rg.samples[f"{b}.{x}"] @ M[:3, :3].T + M[:3, 3])
            sets[kind] = np.vstack(pts)
        for k, (y0, y1, zh, dxs) in enumerate(R.D.STRIPS):
            name = f"Mantle.{x}{k + 1}"
            piv = rg.head[name]
            ln = piv.z - zh
            need = {}
            for kind, pts in sets.items():
                sel = pts[(pts[:, 1] > y0 - 0.15) & (pts[:, 1] < y1 + 0.15) & (pts[:, 2] < piv.z + 0.05)]
                dx = (sel[:, 0] - s * (1.98 + dxs)) * s
                dz = piv.z - sel[:, 2]
                near = np.hypot(dx, dz) < ln + 0.35
                need[kind] = 0.0 if not near.any() else float(
                    max(np.degrees(np.arctan2(dx[near] + 0.14, np.maximum(dz[near], 0.05))).max() - STRIP_REST + 3.0, 0.0))
            out = min(max(need.values()), PUSH_OUT)
            swing = 0.9 * max(need["F"] - PUSH_OUT, 0.0) - 0.9 * max(need["H"] - PUSH_OUT, 0.0)
            res[name] = (out, max(min(swing, 35.0), -35.0))
    return res


def mantle_track(rg, clip, poses):
    """Полосы мантии висят: компенсируют наклон тела (на 85 %) и раскачиваются от ускорений; внутрь к боку не
    заходят. Цикл — три прогона, берётся последний."""
    n = len(poses)
    dt = 1.0 / FPS
    names = [(f"Mantle.{x}{k + 1}", s) for x, s in (("L", 1), ("R", -1)) for k in range(3)]
    info = []
    pushes = []
    for p, lag in poses:
        X = rg.solve(p, dict(lag))
        Rb = X["Body"].to_3x3()
        info.append((Rb, {nm: X["Body"] @ rg.head[nm] for nm, _ in names}, p))
        pushes.append(mantle_push(rg, X))
    out = [{} for _ in range(n)]
    for nm, s in names:
        th = [0.0, 0.0]  # наружу, вперёд-назад
        om = [0.0, 0.0]
        runs = 3 if clip.loop else 1
        for run in range(runs):
            for f in range(n):
                Rb, piv, p = info[f]
                fp, fn = info[(f - 1) % n] if clip.loop else info[max(f - 1, 0)], \
                    info[(f + 1) % n] if clip.loop else info[min(f + 1, n - 1)]
                acc = (fn[1][nm] - 2 * piv[nm] + fp[1][nm]) / (dt * dt)
                local = Rb.transposed() @ acc
                tgt = [-s * p["body_r"] * 0.85 - s * math.degrees(local.x / G),
                       -p["body_p"] * 0.85 - math.degrees(local.y / G)]
                if run == 0 and f == 0 and not clip.loop:
                    th = [tgt[0], tgt[1]]
                for k in range(2):
                    for _ in range(4):
                        h = dt / 4
                        a = MANTLE_W ** 2 * (tgt[k] - th[k]) - 2 * MANTLE_Z * MANTLE_W * om[k]
                        om[k] += a * h
                        th[k] += om[k] * h
                th[0] = max(th[0], -2.0 - p["mantle_out"])
                pout, pswing = pushes[f][nm]
                push = pout - p["mantle_out"]
                if th[0] < push:  # лапа толкает ткань наружу; дальше она опускается сама
                    th[0] = push
                    om[0] = max(om[0], 0.0)
                lo, hi = SWING_LIMIT[int(nm[-1]) - 1]
                th[1] = max(min(th[1], hi), lo)
                if pswing > 0 and th[1] < pswing:  # передняя лапа отводит полосу назад
                    th[1], om[1] = pswing, max(om[1], 0.0)
                elif pswing < 0 and th[1] > pswing:  # задняя — вперёд
                    th[1], om[1] = pswing, min(om[1], 0.0)
                if run == runs - 1:
                    out[f][nm] = (th[0], th[1])
    return out


def clip_frames(rg, clip):
    """Позы клипа по кадрам: (p, lag) с мантией."""
    times = [i / FPS for i in range(clip.frames())]
    poses = [pose_at(clip, t) for t in times]
    for (p, lag), m in zip(poses, mantle_track(rg, clip, poses)):
        lag["mantle"] = m
    return times, poses


# ── проверки ─────────────────────────────────────────────────────────────────────────────────────────────────
PAIRS = [("crown", "horns"), ("crown", "spines"), ("horns", "spines"), ("horns", "wingL"), ("horns", "wingR"),
         ("crown", "wingL"), ("crown", "wingR"),
         ("pauldronL", "foreleg" + "L"), ("pauldronR", "foreleg" + "R"), ("bracerL", "body"), ("bracerR", "body"),
         ("chest", "foreleg" + "L"), ("chest", "foreleg" + "R"), ("chest", "neck"), ("collar", "jaw"),
         ("collar", "skull"), ("collar", "drapeL"), ("collar", "drapeR"), ("greaveL", "tail"), ("greaveR", "tail"),
         ("tailarmor", "hindlegL"), ("tailarmor", "hindlegR"), ("spineplates", "wingL"), ("spineplates", "wingR"),
         ("drapeL", "wingL"), ("drapeR", "wingR"), ("pauldronL", "wingL"), ("pauldronR", "wingR"),
         ("mantleL", "foreleg" + "L"), ("mantleL", "hindlegL"), ("mantleL", "wingL"),
         ("mantleR", "foreleg" + "R"), ("mantleR", "hindlegR"), ("mantleR", "wingR"),
         ("yokeL", "wingL"), ("yokeR", "wingR"),
         ("jaw", "neck"), ("jaw", "chest"), ("jaw", "foreleg" + "L"), ("jaw", "foreleg" + "R"),
         ("skull", "foreleg" + "L"), ("skull", "foreleg" + "R"),
         ("tail", "hindlegL"), ("tail", "hindlegR"), ("tail", "wingL"), ("tail", "wingR"),
         ("wingL", "body"), ("wingR", "body"), ("wingL", "skull"), ("wingR", "skull"), ("wingL", "wingR"),
         ("foreleg" + "L", "foreleg" + "R"), ("hindlegL", "hindlegR"), ("wingL", "hindlegL"), ("wingR", "hindlegR")]


class Checker:
    def __init__(self, rig):
        self.obj, self.sobj = rig["dragon"], rig["scepter"]
        me = self.obj.data
        polys = [list(pl.vertices) for pl in me.polygons]
        self.sets = {t: [polys[i] for i in idx] for t, idx in rig["tags"].items()}
        self.all = polys
        self.spolys = [list(pl.vertices) for pl in self.sobj.data.polygons]
        self.base = None
        self.vtag = {}
        for t in ("tail", "wingL", "wingR", "skull", "jaw", "horns", "crown", "mantleL", "mantleR", "body", "neck",
                  "foreleg" + "L", "foreleg" + "R", "hindlegL", "hindlegR"):
            for pl in self.sets[t]:
                for v in pl:
                    self.vtag[v] = t
        self.low_sets = {t: np.unique(np.array([v for pl in self.sets[t] for v in pl]))
                         for t in ("tail", "wingL", "wingR", "skull", "jaw", "mantleL", "mantleR", "body", "neck",
                                   "chest", "collar", "foreleg" + "L", "foreleg" + "R", "hindlegL", "hindlegR")}

    def measure(self):
        co = eval_points(self.obj)
        sco = eval_points(self.sobj)
        cl = co.tolist()
        trees = {}

        def tree(name):
            if name not in trees:
                trees[name] = BVHTree.FromPolygons(cl, self.sets[name])
            return trees[name]

        res = {f"{a}|{b}": len(tree(a).overlap(tree(b))) for a, b in PAIRS}
        sc_tree = BVHTree.FromPolygons(sco.tolist(), self.spolys)
        res["scepter|dragon"] = len(sc_tree.overlap(BVHTree.FromPolygons(cl, self.all)))
        both = np.vstack([co, sco])
        rad = np.sqrt(both[:, 0] ** 2 + both[:, 1] ** 2)
        res["_radius"] = float(rad.max())
        far = int(rad.argmax())
        res["_far"] = "scepter" if far >= len(co) else self.vtag.get(far, "?")
        res["_top"] = float(both[:, 2].max())
        res["_low"] = float(co[:, 2].min())
        res["_low_scepter"] = float(sco[:, 2].min())
        for t, idx in self.low_sets.items():
            res["_low_" + t] = float(co[idx, 2].min())
        return res


def flagged(base, val):
    return val > base + max(4, 0.5 * base)


def run_check(rig, rg, clips, every=2):
    ch = Checker(rig)
    show(rg, rig, STAND)
    base = ch.measure()
    show(rg, rig, COMBAT)
    base_c = ch.measure()
    base = {k: max(base[k], base_c[k]) for k in base}
    report = {"baseline": {k: v for k, v in base.items() if not k.startswith("_")}, "clips": {}}
    for make in clips:
        clip = make()
        rg.clamps = 0
        times, poses = clip_frames(rg, clip)
        worst = {}
        ext = {"radius": 0.0, "top": 0.0, "low": 9.0, "low_scepter": 9.0}
        lows = {}
        frames_bad = {}
        for f in range(0, len(times), every):
            show(rg, rig, *poses[f])
            m = ch.measure()
            if m["_radius"] > ext["radius"]:
                ext["far"] = (m["_far"], round(times[f], 2))
            ext["radius"] = max(ext["radius"], m["_radius"])
            ext["top"] = max(ext["top"], m["_top"])
            ext["low"] = min(ext["low"], m["_low"])
            ext["low_scepter"] = min(ext["low_scepter"], m["_low_scepter"])
            for k, v in m.items():
                if k.startswith("_low_") and k != "_low_scepter" and v < -0.08:
                    if v < lows.get(k[5:], (0.0, 0.0))[0]:
                        lows[k[5:]] = (round(v * STUDS, 2), round(times[f], 2))
            for k, v in m.items():
                if k.startswith("_"):
                    continue
                if v > worst.get(k, (-1, 0))[0]:
                    worst[k] = (v, round(times[f], 2))
                if flagged(base[k], v):
                    frames_bad.setdefault(k, []).append(round(times[f], 2))
        report["clips"][clip.name] = {
            "title": clip.title, "duration": clip.duration, "loop": clip.loop, "events": clip.events,
            "ik_clamps": rg.clamps, "below_ground": lows,
            "radius_studs": round(ext["radius"] * STUDS, 1), "arena_ok": ext["radius"] <= SAFE_R,
            "farthest": ext.get("far"),
            "top_studs": round(ext["top"] * STUDS, 1), "low_studs": round(ext["low"] * STUDS, 2),
            "flags": {k: {"base": base[k], "max": worst[k][0], "at": worst[k][1], "frames": len(v),
                          "from": v[0], "to": v[-1]} for k, v in frames_bad.items()},
        }
        print("CHECK", clip.name, json.dumps(report["clips"][clip.name], ensure_ascii=False), flush=True)
    with open(os.path.join(OUT, "anim_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    return report


# ── кадры превью ─────────────────────────────────────────────────────────────────────────────────────────────
CLIP_VIEW = {"sleep_idle": "34", "wake": "wide", "combat_idle": "34", "walk": "sideL", "turn_left": "wide",
             "claw_swipe": "wide_r", "bite": "34r", "tail_strike": "wide_r", "wing_buffet": "front",
             "magic_scepter": "wide", "hit": "34r", "victory": "wide", "defeat": "34", "fall_asleep": "34"}
RES = (1280, 720)


def ground_marks(col):
    """Метки на земле для ходьбы на месте: бегут назад со скоростью босса — видно, что опорная лапа не скользит."""
    mat = bpy.data.materials.new("MarkM")
    mat.use_nodes = True
    b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.35, 0.37, 0.45, 1)
    marks = []
    for x in (-4.6, 4.6):
        for i in range(14):
            me = bpy.data.meshes.new("Mark")
            me.from_pydata([(-0.5, -0.15, 0.01), (0.5, -0.15, 0.01), (0.5, 0.15, 0.01), (-0.5, 0.15, 0.01)], [],
                           [(0, 1, 2, 3)])
            me.materials.append(mat)
            o = bpy.data.objects.new("Mark", me)
            col.objects.link(o)
            o.location = (x, -21 + i * 3.0, 0)
            o.hide_render = True
            marks.append(o)
    return marks


def render_clips(col, rig, rg, clips):
    cam = stage(col)
    marks = ground_marks(col)
    meta = {}
    for make in clips:
        clip = make()
        times, poses = clip_frames(rg, clip)
        view = CLIP_VIEW.get(clip.name, "34")
        eye, target, lens = VIEWS[view]
        folder = os.path.join(OUT, "frames", clip.name)
        os.makedirs(folder, exist_ok=True)
        for f, (p, lag) in enumerate(poses):
            show(rg, rig, p, lag)
            for i, m in enumerate(marks):
                m.hide_render = clip.name != "walk"
                if clip.name == "walk":
                    m.location.y = (-21 + (i % 14) * 3.0 + WALK_SPEED * times[f] + 21) % 42 - 21
            ck.shot(cam, os.path.join(folder, f"{f:04d}.png"), eye, target, lens, RES)
        meta[clip.name] = {"title": clip.title, "duration": clip.duration, "loop": clip.loop, "events": clip.events,
                           "frames": len(poses), "view": view, "note": clip.note}
        print("RENDERED", clip.name, len(poses), flush=True)
        with open(os.path.join(OUT, "frames", "meta.json"), "w", encoding="utf-8") as fh:
            json.dump(meta, fh, ensure_ascii=False, indent=1)


# ── .blend с действиями ──────────────────────────────────────────────────────────────────────────────────────
def bake_blend(col, rig, rg, clips, path):
    """Каждый клип — действие Dragon_<клип> (ключ на каждом кадре, 30 в секунду) и все клипы подряд в действии
    Dragon_AllClips с маркерами начала клипов."""
    arm = rig["arm"]
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    arm.animation_data_create()
    scene = bpy.context.scene
    allact = bpy.data.actions.new("Dragon_AllClips")
    allact.use_fake_user = True
    start = 0
    per_clip = []
    for make in clips:
        clip = make()
        times, poses = clip_frames(rg, clip)
        per_clip.append((clip, poses))
    for clip, poses in per_clip:
        act = bpy.data.actions.new("Dragon_" + clip.name)
        act.use_fake_user = True
        for a, offset in ((act, 0), (allact, start)):
            arm.animation_data.action = a
            for f, (p, lag) in enumerate(poses):
                rg.apply(rg.solve(dict(p), lag))
                arm["eyes"], arm["glow"] = p["eyes"], p["glow"]
                for pb in arm.pose.bones:
                    pb.keyframe_insert("location", frame=f + offset, group=pb.name)
                    pb.keyframe_insert("rotation_quaternion", frame=f + offset, group=pb.name)
                arm.keyframe_insert('["eyes"]', frame=f + offset)
                arm.keyframe_insert('["glow"]', frame=f + offset)
        scene.timeline_markers.new(clip.title, frame=start)
        start += len(poses) + 10
        print("BAKED", clip.name, len(poses), flush=True)
    arm.animation_data.action = allact
    scene.frame_start, scene.frame_end = 0, start
    scene.render.fps = FPS
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)


def strips(col, rig, rg, clips, n=8, res=(480, 270)):
    """Раскадровки для самопроверки: n кадров каждого клипа (с событиями) с его камеры."""
    cam = stage(col)
    for make in clips:
        clip = make()
        times, poses = clip_frames(rg, clip)
        idx = sorted(set([round(i * (len(times) - 1) / (n - 1)) for i in range(n)] +
                         [min(len(times) - 1, round(t * FPS)) for t in clip.events.values()]))
        eye, target, lens = VIEWS[os.environ.get("VIEW") or CLIP_VIEW.get(clip.name, "34")]
        folder = os.path.join(OUT, "strips", clip.name)
        os.makedirs(folder, exist_ok=True)
        for f in idx:
            show(rg, rig, *poses[f])
            ck.shot(cam, os.path.join(folder, f"{f:04d}.png"), eye, target, lens, res)
        print("STRIP", clip.name, len(idx), flush=True)


# ── демонстрация рига ───────────────────────────────────────────────────────────────────────────────────────
CHAIN_COLOR = {"Body": (0.95, 0.85, 0.3), "Neck": (0.4, 0.85, 1.0), "Head": (1.0, 0.55, 0.25), "Jaw": (1.0, 0.35, 0.2),
               "Collar": (1.0, 1.0, 1.0), "Pauldron": (1.0, 0.8, 0.1), "UpperArm": (0.35, 1.0, 0.5),
               "Forearm": (0.2, 0.8, 0.35), "Paw": (0.15, 0.6, 0.25), "Thigh": (0.5, 0.6, 1.0),
               "Shin": (0.35, 0.45, 0.95), "Meta": (0.25, 0.3, 0.8), "HindPaw": (0.2, 0.2, 0.65),
               "WingArm": (1.0, 0.4, 0.85), "WingFore": (0.9, 0.3, 0.75), "Finger": (0.75, 0.25, 0.65),
               "Membrane": (0.55, 0.2, 0.5), "Tail": (0.95, 0.55, 0.15), "Mantle": (0.9, 0.15, 0.2),
               "Scepter": (0.2, 1.0, 0.95), "Root": (0.6, 0.6, 0.6)}


def chain_of(name):
    for k in sorted(CHAIN_COLOR, key=len, reverse=True):
        if name.startswith(k):
            return k
    return "Root"


def flat(name, col, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = 0.7
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


def segmentation(rig):
    """Копия дракона и скипетра (с той же арматурой): грани окрашены по костям — видно, какая часть к какой кости."""
    out = []
    for obj, art in ((rig["dragon"], rig["art"]), (rig["scepter"], rig["sart"])):
        cp = obj.copy()
        cp.data = obj.data.copy()
        bpy.context.scene.collection.objects.link(cp)
        cp.data.materials.clear()
        names = sorted({g or "Root" for g in art.face_groups})
        for n in names:
            base = CHAIN_COLOR[chain_of(n)]
            side = 0.82 if n.endswith(".R") or n[-2:-1] == "R" else 1.0
            k = 0.85 + 0.15 * ((hash(n) % 7) / 6)
            cp.data.materials.append(flat("seg_" + n, tuple(min(1.0, c * side * k) for c in base)))
        idx = [names.index(g or "Root") for g in art.face_groups]
        cp.data.polygons.foreach_set("material_index", idx)
        cp.hide_render = True
        out.append(cp)
    return out


def skeleton(rg, X):
    """Скелет в позе X: суставы — октаэдры, кости — тонкие бруски от сустава к суставу-ребёнку (или к хвосту кости)."""
    import bmesh as _bm
    bm = _bm.new()
    mats = {}
    me = bpy.data.meshes.new("Skeleton")
    faces_mat = []
    bones = rg.arm.data.bones
    for b in bones:
        if b.name == "Root":
            continue
        col = chain_of(b.name)
        if col not in mats:
            mats[col] = len(mats)
            me.materials.append(flat("sk_" + col, CHAIN_COLOR[col], emit=0.9))
        h = X[b.name] @ b.head_local
        kids = [c for c in b.children if c.name != "Root"]
        ends = [X[c.name] @ c.head_local for c in kids if (c.head_local - b.head_local).length > 0.2] or                [X[b.name] @ b.tail_local]
        r = 0.2 if col in ("Finger", "Mantle", "Collar", "Scepter") else 0.3
        for e in ends:
            d = e - h
            if d.length < 1e-3:
                continue
            m = Matrix.Translation(h) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
            w = r * 0.45
            vs = [bm.verts.new(m @ V(c)) for c in ((-w, -w, 0), (w, -w, 0), (w, w, 0), (-w, w, 0),
                                                   (-w * 0.5, -w * 0.5, d.length), (w * 0.5, -w * 0.5, d.length),
                                                   (w * 0.5, w * 0.5, d.length), (-w * 0.5, w * 0.5, d.length))]
            for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
                bm.faces.new([vs[i] for i in f])
                faces_mat.append(mats[col])
        vs = [bm.verts.new(h + V(c) * r) for c in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
        for f in ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)):
            bm.faces.new([vs[i] for i in f])
            faces_mat.append(mats[col])
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("material_index", faces_mat)
    o = bpy.data.objects.new("Skeleton", me)
    bpy.context.scene.collection.objects.link(o)
    return o


def rig_demo(col, rig, rg):
    """Кадры демонстрации рига: раскраска по костям, скелет поверх модели (два прохода), контрольные позы."""
    cam = stage(col)
    folder = os.path.join(OUT, "rigdemo")
    os.makedirs(folder, exist_ok=True)
    scene = bpy.context.scene
    segs = segmentation(rig)
    clips = {c().name: c for c in CLIPS}

    def at(name, t):
        clip = clips[name]()
        times, poses = clip_frames(rg, clip)
        return poses[min(len(times) - 1, round(t * FPS))]

    shots = [("stand", (dict(STAND), None), ("wide", "sideL")),
             ("claw", at("claw_swipe", 0.55), ("wide_r",)),
             ("wings", at("wing_buffet", 0.55), ("front",)),
             ("sleep", (dict(SLEEP), None), ("wide",))]
    for name, (pose, lag), views in shots:
        show(rg, rig, pose, lag)
        X = rg.solve(dict(pose), lag)
        for o in (rig["dragon"], rig["scepter"]):
            o.hide_render = False
        for o in segs:
            o.hide_render = True
        for view in views:
            eye, target, lens = VIEWS[view]
            ck.shot(cam, os.path.join(folder, f"{name}_{view}_model.png"), eye, target, lens, (960, 640))
        for o in (rig["dragon"], rig["scepter"]):
            o.hide_render = True
        for o in segs:
            o.hide_render = False
        for view in views:
            eye, target, lens = VIEWS[view]
            ck.shot(cam, os.path.join(folder, f"{name}_{view}_seg.png"), eye, target, lens, (960, 640))
        for o in segs:
            o.hide_render = True
        sk = skeleton(rg, X)
        floor = [o for o in scene.objects if o.name.startswith(("Floor", "ArenaRing", "SafeRing"))]
        for o in floor:
            o.hide_render = True
        scene.render.film_transparent = True
        for view in views:
            eye, target, lens = VIEWS[view]
            ck.shot(cam, os.path.join(folder, f"{name}_{view}_skel.png"), eye, target, lens, (960, 640))
        scene.render.film_transparent = False
        for o in floor:
            o.hide_render = False
        bpy.data.objects.remove(sk)
        for o in (rig["dragon"], rig["scepter"]):
            o.hide_render = False
    info = {"bones": [], "parts": rig["info"]["parts_per_bone"], "membrane": rig["info"]["membrane"]}
    for b in rig["arm"].data.bones:
        info["bones"].append({"name": b.name, "parent": b.parent.name if b.parent else None,
                              "deform": b.use_deform, "chain": chain_of(b.name)})
    with open(os.path.join(folder, "rig_info.json"), "w", encoding="utf-8") as fh:
        json.dump(info, fh, ensure_ascii=False, indent=1)
    print("RIGDEMO", len(info["bones"]), flush=True)


if __name__ == "__main__":
    t0 = time.time()
    col, rig = setup()
    rg = Rig(rig["arm"])
    rg.samples = leg_samples(rig)
    print("RIG", json.dumps(rig["info"], ensure_ascii=False), flush=True)
    chosen = [c for c in CLIPS if not ONLY or c.__name__[5:] in ONLY or c().name in ONLY]
    if MODE == "foldtest":
        cam = stage(col)
        variants = {"A": (0, 30, -35, -45), "B": (0, 60, -50, -45), "C": (0, 50, -50, -45), "D": (10, 60, -50, -45)}
        for name, (ra, sw, tw, el) in variants.items():
            FOLD.update({"raise": ra, "sweep": sw, "twist": tw, "elbow": el})
            show(rg, rig, SLEEP)
            for view in ("back", "side", "34"):
                eye, target, lens = VIEWS[view]
                ck.shot(cam, os.path.join(OUT, f"fold_{name}_{view}.png"), eye, target, lens, (720, 480))
    if MODE == "fit":
        for jz, reach, n1 in ((0.9, 10.3, 60.0), (0.6, 10.3, 60.0), (0.9, 10.5, 70.0)):
            print("FIT sleep", jz, reach, n1, head_fit(rg, SLEEP, jaw_z=jz, reach=reach, neck1=n1), flush=True)
            print("FIT lying", jz, reach, n1, head_fit(rg, lying(COMBAT), jaw_z=jz, level=2.0, reach=reach, neck1=n1),
                  flush=True)
    if MODE == "legscan":
        ch = Checker(rig)
        best = {}
        bz = float(os.environ.get("BZ", "-2.02"))
        for fy in (0.0, 0.3, 0.6):
            for fz in (0.46, 0.65, 0.85, 1.05):
                for fp in (-52.0, -40.0, -28.0):
                    pose = dict(SLEEP, body_z=bz)
                    for x in "LR":
                        pose[f"F{x}_y"] += fy
                        pose[f"F{x}_z"], pose[f"F{x}_pitch"] = fz, fp
                    show(rg, rig, pose)
                    m = ch.measure()
                    low = min(m["_low_foreleg" + "L"], m["_low_foreleg" + "R"])
                    cost = max(0.0, -0.06 - low) * 10 + fz + abs(fp) / 200
                    if "F" not in best or cost < best["F"][0]:
                        best["F"] = (cost, fy, fz, fp, round(low, 2))
        for hy in (0.0, 0.4, 0.8, 1.2):
            for hz in (0.3, 0.6, 0.9):
                for heel in (10.0, 25.0, 40.0):
                    for bend in (0.0, 25.0, 50.0):
                        pose = dict(SLEEP, body_z=bz)
                        for x in "LR":
                            pose[f"H{x}_y"] += hy
                            pose[f"H{x}_z"], pose[f"H{x}_heel"], pose[f"H{x}_bend"] = hz, heel, bend
                        show(rg, rig, pose)
                        m = ch.measure()
                        low = min(m["_low_hindlegL"], m["_low_hindlegR"])
                        cost = max(0.0, -0.06 - low) * 10 + hz + hy / 4
                        if "H" not in best or cost < best["H"][0]:
                            best["H"] = (cost, hy, hz, heel, bend, round(low, 2))
        print("LEGS", best, flush=True)
    if MODE == "tailpos":
        clips = {c().name: c for c in CLIPS}
        for nm, pose in (("STAND", STAND), ("COMBAT", COMBAT)):
            X = rg.solve(dict(pose))
            print("TP", nm, [tuple(round(c, 1) for c in X[f"Tail{i + 1}"] @ R.TAIL[i + 1]) for i in range(7)],
                  "lifts", rg.tail_lift, flush=True)
        clip = clips["tail_strike"]()
        times, poses = clip_frames(rg, clip)
        for f in (0, 15, 22, 27):
            X = rg.solve(dict(poses[f][0]), poses[f][1])
            print("TS", f, [tuple(round(c, 1) for c in X[f"Tail{i + 1}"] @ R.TAIL[i + 1]) for i in range(0, 7, 2)],
                  flush=True)
    if MODE == "tailscan":
        ch = Checker(rig)
        clips = {c().name: c for c in CLIPS}
        base = dict(clips["tail_strike"]().curves and pose_at(clips["tail_strike"](), 0.75)[0])
        rows = []
        for ty in (-30.0, -50.0, -70.0, -90.0, -110.0):
            for tc in (-8.0, -4.0, 0.0, 4.0):
                for tp in (6.0, 14.0, 22.0):
                    pz = dict(base, tail_y=ty, tail_curl=tc, tail_p=tp, body_yaw=-12.0, body_x=0.25)
                    show(rg, rig, pz)
                    m = ch.measure()
                    X = rg.solve(pz)
                    tip = X["Tail7"] @ R.TAIL[7]
                    hits = m["tail|hindlegR"] + m["tail|hindlegL"] + m["tailarmor|hindlegL"] + m["tail|wingL"]
                    aim = (tip - V((5.6, -1.5, 1.5))).length
                    cost = hits / 10 + aim + 3 * max(0.0, m["_radius"] - 10.4)
                    rows.append((round(cost, 2), hits, round(aim, 2), round(m["_radius"] * STUDS, 1), ty, tc, tp,
                                 tuple(round(c, 1) for c in tip)))
        rows.sort()
        for r in rows[:8]:
            print("TSCAN", r, flush=True)
    if MODE == "taildebug":
        ch = Checker(rig)
        rows = []
        for ty in (-40.0, -20.0, 0.0, 20.0, 40.0, 60.0, 90.0):
            for tc in (-6.0, -3.0, 0.0, 4.0, 8.0, 12.0):
                show(rg, rig, dict(SLEEP, tail_y=ty, tail_curl=tc))
                m = ch.measure()
                X = rg.solve(dict(SLEEP, tail_y=ty, tail_curl=tc))
                end = X["Tail7"] @ R.TAIL[7]
                hits = m["tail|hindlegL"] + m["tail|hindlegR"] + m["tail|wingL"] + m["tail|wingR"]
                if (ty, tc) in ((40.0, 4.0),):
                    for fb in (0.0, 40.0):
                        Xf = rg.solve(dict(COMBAT, FL_bend=fb, FR_bend=fb, FL_z=3.0, FR_z=3.0))
                        print("FBEND", fb, tuple(round(c, 2) for c in Xf["UpperArm.L"] @ rg.fore[1][1]),
                              tuple(round(c, 2) for c in Xf["UpperArm.R"] @ rg.fore[-1][1]), flush=True)
                    for hb in (-30.0, 0.0, 30.0):
                        pz = dict(SLEEP, tail_y=ty, tail_curl=tc, HL_bend=hb, HR_bend=hb)
                        show(rg, rig, pz)
                        mm = ch.measure()
                        Xh = rg.solve(pz)
                        print("BEND", hb, mm["tail|hindlegL"], mm["tail|hindlegR"],
                              tuple(round(c, 2) for c in Xh["Shin.L"] @ rg.hind[1][1]),
                              tuple(round(c, 2) for c in Xh["Shin.R"] @ rg.hind[-1][1]), flush=True)
                    show(rg, rig, dict(SLEEP, tail_y=ty, tail_curl=tc))
                if (ty, tc) in ((40.0, 4.0), (120.0, 20.0), (80.0, 12.0)):
                    print("TAILPAIRS", ty, tc, {k: m[k] for k in ("tail|hindlegL", "tail|hindlegR", "tail|wingL",
                                                                  "tail|wingR")}, flush=True)
                rows.append((hits + 20 * max(0.0, m["_radius"] - 10.3), hits, round(m["_radius"] * STUDS, 1), ty, tc,
                             tuple(round(c, 1) for c in end)))
        rows.sort()
        for r in rows[:6]:
            print("TAIL", r, flush=True)
    if MODE == "frames":
        cam = stage(col)
        spec = [("walk", 0.07, (14.0, -8.0, 6.0), (2.4, -1.5, 3.6), 40), ("walk", 0.47, (-14.0, -8.0, 6.0), (-2.4, -1.5, 3.6), 40),
                ("turn_left", 0.8, (-14.0, -10.0, 6.0), (-2.0, -1.0, 3.6), 40),
                ("claw_swipe", 0.5, (16.0, -16.0, 14.0), (1.5, -1.5, 8.5), 40),
                ("victory", 0.8, (16.0, -16.0, 14.0), (1.0, -1.0, 9.0), 35),
                ("magic_scepter", 1.93, (-16.0, -20.0, 10.0), (-2.0, -6.0, 6.0), 40),
                ("tail_strike", 0.8, (-20.0, 12.0, 14.0), (-1.0, 3.0, 3.0), 35),
                ("sleep_idle", 0.0, (22.0, -8.0, 10.0), (0.0, 0.5, 2.0), 35)]
        clips = {c().name: c for c in CLIPS}
        for name, t, eye, target, lens in spec:
            clip = clips[name]()
            times, poses = clip_frames(rg, clip)
            f = min(len(times) - 1, round(t * FPS))
            show(rg, rig, *poses[f])
            ck.shot(cam, os.path.join(OUT, f"close_{name}_{t:.2f}.png"), eye, target, lens, (800, 600))
    if MODE == "foldscan":
        ch = Checker(rig)
        rows = []
        pairs = ("wingL|body", "wingR|body", "spineplates|wingL", "spineplates|wingR", "wingL|wingR",
                 "wingL|hindlegL", "wingR|hindlegR", "mantleL|wingL", "mantleR|wingR", "tail|wingL", "tail|wingR")
        for ra in (0, 10, 20, 30):
            for sw in (30, 40, 50, 60):
                for tw in (-50, -35, -20, -5):
                    for el in (-15, -30, -45):
                        FOLD.update({"raise": ra, "sweep": sw, "twist": tw, "elbow": el})
                        show(rg, rig, SLEEP)
                        m = ch.measure()
                        hits = sum(m[k] for k in pairs)
                        rows.append((hits + 8 * max(0.0, m["_top"] - 8.6), hits, round(m["_top"], 2), ra, sw, tw, el))
        rows.sort()
        for r in rows[:12]:
            print("FOLD", r, flush=True)
        FOLD.update({"raise": rows[0][3], "sweep": rows[0][4], "twist": rows[0][5], "elbow": rows[0][6]})
        show(rg, rig, SLEEP)
        m = ch.measure()
        print("FOLDBEST", {k: m[k] for k in pairs}, flush=True)
    if MODE == "poses":
        main_poses(col, rig, rg, [("stand", STAND), ("combat", COMBAT), ("sleep", SLEEP)],
                   ("34", "side", "back", "top"))
    if MODE in ("check", "all"):
        run_check(rig, rg, chosen)
    if MODE == "rigdemo":
        rig_demo(col, rig, rg)
    if MODE == "strips":
        strips(col, rig, rg, chosen)
    if MODE in ("render", "all"):
        render_clips(col, rig, rg, chosen)
    if MODE in ("blend", "all"):
        bake_blend(col, rig, rg, CLIPS, os.path.join(OUT, "boss10_v7_rig.blend"))
    print("DONE", round(time.time() - t0, 1), flush=True)
