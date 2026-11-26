"""Босс 6 «Королева-мухоловка»: 10 клипов (шаг 2 D64) на игровой модели scripts/blender/boss6_flytrap.py.

Клипы — ключевые позы в параметрах модели (наклон стебля, голова, створки, язык, веки, брови, лозы, пальцы-листья,
венчик, корона, мантия, розетка, бутоны); между ключами — кубический сплайн Эрмита по каждому параметру (как у Йети).
Мухоловка не ходит (D64 п. 5): вместо ходьбы — «поворот на месте» (листья розетки переступают, стебель качается;
сам поворот модели делает игра). Длительности и события — как у Йети (Config/Battle.Timeline, AttackAt):
  sleep_idle 6.4 (цикл) — бутон склонён, створки сомкнуты, дышит венчиком и мантией;
  wake 2.4 — открыла глаза (1.0, конец Wake), выпрямилась, раскрыла бутоны (1.9, конец StandUp), боевая стойка;
  combat_idle 3.6 (цикл); turn 0.8 (цикл, «шаг» на месте);
  snap 1.3 — основной выпад «Захлоп»: голова откидывается и бросается вперёд, створки смыкаются (AttackAt 0.45,
         контакт 0.7);
  grab 1.4 — «Хватает» (особая атака, только анимация D64 п. 3): лозы выброшены вперёд, листья-пальцы раскрыты
         веером (0.5), сжимаются в кулак из листьев (0.75);
  hit 0.47; victory 2.2 (торжествует → stand); defeat 2.4 (увяла, корона упала → медленно поднимается → stand);
  fall_asleep 1.6 (stand → sleep);
  eat 3.8 — катсцена D74 «съесть» (stand → stand): правая лоза рывком вперёд на всю длину, ладонь раскрыта (0.35) →
         листья-пальцы сжались — игра в этот миг крепит Ловибум к LovibumHold (0.6) → подносит к пасти, голова
         склонилась к ладони, створки широко (1.05) → пальцы разжались, Ловибум в пасти (1.3) → захлоп — Ловибум
         скрыть (1.5) → жуёт: створки и голова ходят, мантия и венчик колышутся (1.75–2.5) → набрала воздух (2.8) →
         выплюнула капсулу этажа вперёд из CapsuleSpawn (3.05) → довольная, прищур (3.5) → стойка.
  D74: боя нет — боевые клипы (combat_idle, turn, snap, grab, hit, victory, defeat) не удаляются, но не дорабатываются.
Выход: <папка>/Boss6_Flytrap.anim.json (до «ок» владельца на лист — не в assets; формат как у Boss5_Yeti.anim.json:
кадры — Transform суставов в осях Roblox, [x, y, z, qx, qy, qz, qw]), anim_report.json (провал под землю ниже стойки),
раскадровка <папка>/frames/<клип>_<k>.png (8 кадров, 3/4).
Режимы: (пусто) — расчёт, экспорт и кадры; check — только проверка. FLY_CLIPS="eat,wake" — клипы для кадров.
Запуск: blender --background --factory-startup --python scripts/blender/boss6_flytrap_anim.py -- <репо> <папка> [check]
Зависит от boss6_flytrap.py, concepts510/ck.py (студия и кадр).
"""

import json
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boss6_flytrap as Q  # noqa: E402

V = Vector
S2 = (1, -1)
FPS = 30
TOL = 0.1  # ниже нижней точки стойки больше чем на 0.1 ед. (0.2 стада) — провал под землю
SIDE_KEYS = {"lid": 3, "brow": 2, "arm": 5, "fing": 2, "bud": 2}
VEC_KEYS = {"head": 3, "jaw": 2, "tongue": 2, "mantle": 2}
SCALARS = ("lean", "side", "petals", "crown", "rosette")


# ── Параметры позы ↔ плоский словарь ────────────────────────────────────────────────────────────────────────
def flat(P):
    f = {k: float(P[k]) for k in SCALARS}
    for k, n in VEC_KEYS.items():
        for i in range(n):
            f[f"{k}{i}"] = float(P[k][i])
    for k, n in SIDE_KEYS.items():
        for s in S2:
            for i in range(n):
                f[f"{k}{s}_{i}"] = float(P[k][s][i])
    return f


def unflat(f):
    P = Q.base_pose()
    for k in SCALARS:
        P[k] = f[k]
    P["crown"] = max(0.0, min(1.0, P["crown"]))
    for k, n in VEC_KEYS.items():
        P[k] = tuple(f[f"{k}{i}"] for i in range(n))
    P["tongue"] = tuple(max(0.0, min(1.0, v)) for v in P["tongue"])
    for k, n in SIDE_KEYS.items():
        P[k] = {s: tuple(f[f"{k}{s}_{i}"] for i in range(n)) for s in S2}
    P["lid"] = {s: (max(0.0, min(1.0, a)), max(0.0, min(1.0, b)), c) for s, (a, b, c) in P["lid"].items()}
    return P


def pose(base, **kw):
    """Поза из библиотеки модели (имя или словарь) с правками."""
    P = Q.POSES[base] if isinstance(base, str) else base
    R_ = {k: (dict(v) if isinstance(v, dict) else v) for k, v in P.items()}
    for k, v in kw.items():
        if isinstance(v, dict) and isinstance(R_.get(k), dict):
            R_[k] = {**R_[k], **v}
        else:
            R_[k] = v
    return R_


# ── Клип: ключи → кадры (сплайн, как у Йети) ────────────────────────────────────────────────────────────────
class Clip:
    def __init__(self, name, title, dur, keys, loop=False, events=None, start=None, end=None):
        self.name, self.title, self.dur, self.loop = name, title, dur, loop
        self.keys = sorted(keys, key=lambda k: k[0])
        self.events = events or {}
        self.start, self.end = start, end

    def frames(self):
        n = round(self.dur * FPS)
        ts = [k[0] for k in self.keys]
        fl = [flat(k[1]) for k in self.keys]
        out = []
        for i in range(n + (0 if self.loop else 1)):
            t = min(i / FPS, self.dur)
            out.append(unflat({c: self._channel(ts, [x[c] for x in fl], t) for c in fl[0]}))
        return out

    def _seg(self, ts, t):
        if self.loop:
            t = t % self.dur
        for j in range(len(ts) - 1):
            if ts[j] <= t <= ts[j + 1]:
                return j, (t - ts[j]) / max(ts[j + 1] - ts[j], 1e-6)
        return len(ts) - 2, 1.0

    def _channel(self, ts, vs, t):
        """Кубический сплайн Эрмита с касательными Катмулла — Рома (на концах неповторяющегося клипа — 0)."""
        j, u = self._seg(ts, t)
        n = len(ts)

        def tang(i):
            if self.loop:
                a, ta = (i - 1, ts[i - 1]) if i > 0 else (n - 2, ts[n - 2] - self.dur)
                b, tb = (i + 1, ts[i + 1]) if i < n - 1 else (1, ts[1] + self.dur)
                return (vs[b] - vs[a]) / max(tb - ta, 1e-6)
            if i == 0 or i == n - 1:
                return 0.0
            return (vs[i + 1] - vs[i - 1]) / max(ts[i + 1] - ts[i - 1], 1e-6)

        h = ts[j + 1] - ts[j]
        p0, p1, m0, m1 = vs[j], vs[j + 1], tang(j) * h, tang(j + 1) * h
        u2, u3 = u * u, u * u * u
        return (2 * u3 - 3 * u2 + 1) * p0 + (u3 - 2 * u2 + u) * m0 + (-2 * u3 + 3 * u2) * p1 + (u3 - u2) * m1


# ── Ключевые позы клипов ────────────────────────────────────────────────────────────────────────────────────
SLEEP, COMBAT, STAND = Q.POSES["sleep"], Q.POSES["combat"], Q.POSES["stand"]


def clips():
    C = []
    # сон: бутон склонён, дышит — стебель чуть выпрямляется, венчик и мантия приподнимаются
    inhale = pose("sleep", lean=9.0, head=(20.0, 6.0, 8.0), petals=16.0, mantle=(-4.0, 3.0))
    C.append(Clip("sleep_idle", "Сон", 6.4, [(0.0, SLEEP), (3.2, inhale), (6.4, SLEEP)], loop=True))
    # пробуждение: моргнула, открыла глаза, выпрямилась, развела лозы и раскрыла бутоны
    blink = pose("sleep", lid={1: (0.55, 0.5, 0.0), -1: (0.6, 0.55, 0.0)}, head=(14.0, 4.0, 6.0))
    awake = pose("stand", lean=6.0, head=(6.0, 0.0, 0.0), jaw=(6, 10), lid=Q.both((0.15, 0.05, 0.0)),
                 brow={1: (-6.0, 0.05), -1: (6.0, 0.05)})
    stretch = pose("victory", jaw=(30, 50), lid=Q.SQUINT, brow=Q.ANGRY, bud=Q.both((60.0, -6.0)))
    C.append(Clip("wake", "Пробуждение", 2.4, [(0.0, SLEEP), (0.5, blink), (1.0, awake), (1.5, stretch),
                                               (1.9, pose("combat", jaw=(20, 36))), (2.4, COMBAT)],
                  events={"проснулась (конец Wake)": 1.0, "бутоны раскрыты (конец StandUp)": 1.9}, start="sleep",
                  end="combat"))
    # боевая стойка: стебель покачивается, створки щёлкают, лозы и пальцы шевелятся
    sway = pose("combat", lean=16.0, side=4.0, head=(0.0, 6.0, 3.0), jaw=(22, 38),
                arm={1: (146.0, 20.0, 62.0, -15.0, 55.0), -1: (100.0, 24.0, 40.0, -15.0, 36.0)},
                fing=Q.both((0.35, 14.0)))
    sway2 = pose("combat", lean=10.0, side=-4.0, head=(4.0, -6.0, -3.0), jaw=(30, 50),
                 arm={1: (138.0, 12.0, 54.0, -15.0, 46.0), -1: (108.0, 30.0, 32.0, -15.0, 44.0)},
                 fing=Q.both((0.2, 4.0)))
    C.append(Clip("combat_idle", "Боевая стойка", 3.6, [(0.0, COMBAT), (0.9, sway), (1.8, COMBAT), (2.7, sway2),
                                                       (3.6, COMBAT)], loop=True))
    # поворот на месте (не ходит): листья розетки приподнимаются по очереди, стебель качается вбок
    stepA = pose("combat", side=6.0, rosette=10.0, head=(2.0, -8.0, 0.0))
    stepB = pose("combat", side=-6.0, rosette=-4.0, head=(2.0, 8.0, 0.0))
    C.append(Clip("turn", "Поворот на месте", 0.8, [(0.0, COMBAT), (0.2, stepA), (0.4, COMBAT), (0.6, stepB),
                                                    (0.8, COMBAT)], loop=True,
                  events={"розетка: правый «шаг»": 0.2, "розетка: левый «шаг»": 0.6}))
    # «Захлоп» (основной выпад): голова откидывается назад, створки широко раскрыты → бросок вперёд, створки смыкаются
    windup = pose("combat", lean=2.0, head=(-22.0, 0.0, 0.0), jaw=(40, 58), petals=-6.0)
    after = pose("snap", lean=24.0, head=(12.0, 0.0, 0.0), jaw=(8, 12))
    C.append(Clip("snap", "Захлоп", 1.3, [(0.0, COMBAT), (0.45, windup), (0.7, Q.POSES["snap"]), (0.95, after),
                                          (1.3, COMBAT)],
                  events={"начало выпада в игре (AttackAt)": 0.45, "контакт: створки сомкнулись": 0.7},
                  start="combat", end="combat"))
    # «Хватает» (особая атака): лозы назад и в стороны → выброшены вперёд, пальцы раскрыты веером → сжались в кулак
    reach_back = pose("combat", lean=6.0, head=(-8.0, 0.0, 0.0), arm=Q.both((120.0, -30.0, 40.0, -20.0, 30.0)),
                      fing=Q.both((0.6, 0.0)))
    hold = pose("grab2", lean=22.0)
    C.append(Clip("grab", "Хватает", 1.4, [(0.0, COMBAT), (0.25, reach_back), (0.5, Q.POSES["grab"]),
                                           (0.75, Q.POSES["grab2"]), (1.0, hold), (1.4, COMBAT)],
                  events={"начало выпада в игре (AttackAt)": 0.5, "контакт: листья-пальцы сжались": 0.75},
                  start="combat", end="combat"))
    # получение урона
    C.append(Clip("hit", "Получение урона", 0.4667, [(0.0, COMBAT), (0.07, Q.POSES["hit"]), (0.4667, COMBAT)],
                  events={"пик реакции": 0.07}, start="combat", end="combat"))
    # победа: торжествует, раскачивается, створки «хохочут» → стойка
    laugh = pose("victory", jaw=(10, 20), lean=-2.0)
    C.append(Clip("victory", "Победа", 2.2, [(0.0, COMBAT), (0.4, Q.POSES["victory"]), (0.7, laugh),
                                             (0.95, Q.POSES["victory"]), (1.2, laugh), (1.9, STAND), (2.2, STAND)],
                  events={"торжествует": 0.4, "стоит (поза stand)": 1.9}, start="combat", end="stand"))
    # поражение: увядает, корона падает, лежит; медленно выпрямляется и надевает корону (корона возвращается)
    droop = pose("defeat", crown=0.0)
    lying = Q.POSES["defeat"]
    rise = pose("stand", lean=14.0, head=(12.0, 0.0, 0.0), lid=Q.both((0.4, 0.2, 0.0)), crown=0.3,
                arm=Q.both((40.0, 10.0, 30.0, 0.0, 0.0)))
    C.append(Clip("defeat", "Поражение", 2.4, [(0.0, COMBAT), (0.35, droop), (0.7, lying), (1.62, lying),
                                               (2.0, rise), (2.4, STAND)],
                  events={"увяла": 0.35, "корона на земле": 0.7, "начинает подниматься": 1.62}, start="combat",
                  end="stand"))
    # засыпание: зевает, бутоны закрываются, клонится, глаза закрываются
    yawn = pose("stand", jaw=(34, 54), lid=Q.both((0.5, 0.3, 0.0)), head=(-8.0, 0.0, 0.0))
    nod = pose("sleep", lid=Q.both((0.7, 0.6, 0.0)), head=(14.0, 4.0, 4.0))
    C.append(Clip("fall_asleep", "Засыпание", 1.6, [(0.0, STAND), (0.5, yawn), (1.0, nod), (1.6, SLEEP)],
                  events={"зевок": 0.5}, start="stand", end="sleep"))
    # «съесть» (D74): отобрала Ловибум → в пасть → захлоп → жуёт → выплюнула капсулу этажа → довольная
    happy = dict(lid={1: (0.0, 0.0, 0.0), -1: (0.0, 0.0, 0.0)}, brow={1: (-12.0, 0.12), -1: (12.0, 0.12)})
    reach = pose("stand", lean=24.0, head=(8.0, 0.0, 0.0), jaw=(20, 34), **happy, rosette=4.0,
                 arm={-1: (120.0, 80.0, 0.0, -40.0, 20.0)}, fing={-1: (0.55, 12.0)})
    snatch = pose(reach, lean=22.0, arm={-1: (112.0, 76.0, 14.0, -40.0, 30.0)}, fing={-1: (-0.4, 95.0)})
    lift = pose("stand", lean=20.0, head=(12.0, 0.0, 0.0), jaw=(40, 58), **happy, petals=-6.0,
                arm={-1: (20.0, 90.0, 30.0, -20.0, -40.0)}, fing={-1: (-0.3, 80.0)})
    drop = pose(lift, fing={-1: (0.45, 8.0)})
    gulp = pose("stand", lean=22.0, head=(16.0, 0.0, 0.0), jaw=(0, 0), lid=SQUINT_, brow=Q.SMUG, petals=-10.0,
                arm={-1: (44.0, 40.0, 40.0, 0.0, 10.0)}, fing={-1: (0.2, 20.0)})
    chew_a = pose(gulp, lean=16.0, head=(8.0, 7.0, 5.0), jaw=(9, 13), mantle=(6.0, 5.0), petals=4.0,
                  arm={-1: (52.0, 30.0, 40.0, 0.0, 10.0)})
    chew_b = pose(gulp, lean=15.0, head=(8.0, -7.0, -5.0), jaw=(0, 0), mantle=(-3.0, 0.0), petals=-8.0,
                  arm={-1: (56.0, 26.0, 40.0, 0.0, 10.0)})
    breath = pose("stand", lean=0.0, head=(-18.0, 0.0, 0.0), jaw=(0, 0), lid=SQUINT_, brow=Q.SMUG, petals=-14.0,
                  mantle=(12.0, 8.0), arm={-1: (40.0, -10.0, 30.0, -10.0, 20.0)})
    spit = pose("stand", lean=14.0, head=(-4.0, 0.0, 0.0), jaw=(34, 50), tongue=(1.0, 0.0), **happy, petals=8.0,
                mantle=(-6.0, 2.0), arm={-1: (40.0, -10.0, 30.0, -10.0, 20.0)})  # пасть смотрит вперёд, лоза в сторону
    proud = pose("stand", head=(-6.0, 0.0, 4.0), petals=-6.0, mantle=(6.0, 6.0))
    C.append(Clip("eat", "Съесть", 3.8, [(0.0, STAND), (0.35, reach), (0.6, snatch), (1.05, lift), (1.3, drop),
                                         (1.5, gulp), (1.75, chew_a), (2.0, chew_b), (2.25, chew_a), (2.5, gulp),
                                         (2.8, breath), (3.05, spit), (3.5, proud), (3.8, STAND)],
                  events={"отобрала: крепить Ловибум к LovibumHold": 0.6, "Ловибум в пасти: открепить": 1.3,
                          "захлоп: Ловибум скрыть": 1.5, "капсула этажа вылетает из CapsuleSpawn": 3.05,
                          "довольная": 3.5},
                  start="stand", end="stand"))
    return C


SQUINT_ = {1: (0.55, 0.15, -6.0), -1: (0.55, 0.15, 6.0)}  # довольный прищур (жуёт)


# ── Экспорт и проверки ──────────────────────────────────────────────────────────────────────────────────────
def export(path, baked):
    out = {"fps": FPS, "order": list(Q.RIG_TREE), "scale": Q.SCALE,
           "format": "frames[кадр][часть по order] = [x, y, z, qx, qy, qz, qw]", "clips": {}}
    for clip, frames in baked:
        rows = []
        for P in frames:
            tr = Q.transforms(P)
            row = []
            for n in Q.RIG_TREE:
                m3, off = tr[n]
                t = Q.AX @ (off * Q.SCALE)
                q = (Q.AX @ m3 @ Q.AX.transposed()).to_quaternion()
                row.append([round(v, 4) for v in (t.x, t.y, t.z, q.x, q.y, q.z, q.w)])
            rows.append(row)
        out["clips"][clip.name] = {"title": clip.title, "duration": round(clip.dur, 4), "loop": clip.loop,
                                   "start_pose": clip.start, "end_pose": clip.end,
                                   "events": {k: round(v, 4) for k, v in clip.events.items()}, "frames": rows}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("EXPORT_OK", path, round(os.path.getsize(path) / 1e6, 2), "МБ", flush=True)


def low_point(P, sample, skip_crown=False):
    W = Q.pose_world(P)
    per = {n: min((W[n] @ (Q.PIVOTS[n] + c)).z for c in pts) for n, pts in sample.items()
           if not (skip_crown and n == "Crown")}
    n_low = min(per, key=per.get)
    return n_low, per[n_low]


def check(baked, sample):
    """Провал под землю: нижняя точка кадра ниже нижней точки стойки (корни и розетка у земли) больше чем на TOL."""
    _, ref = low_point(Q.base_pose(), sample)
    rep = {"reference_low": round(ref, 3)}
    for clip, frames in baked:
        lows, who = [], {}
        for P in frames:
            n, z = low_point(P, sample, skip_crown=P["crown"] > 0)  # упавшая корона лежит на земле — так задумано
            lows.append(z)
            if z < ref - TOL:
                who[n] = round(min(who.get(n, 0.0), z), 3)
        rep[clip.name] = {"frames": len(frames), "lowest": round(min(lows), 3),
                          "below_ground_frames": sum(1 for z in lows if z < ref - TOL), "below_parts": who}
    return rep


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    out = os.path.abspath(argv[1])
    mode = argv[2] if len(argv) > 2 else ""
    os.makedirs(out, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    col = bpy.data.collections.new("Flytrap")
    bpy.context.scene.collection.children.link(col)
    Q.rest_frames()
    only = [c for c in os.environ.get("FLY_CLIPS", "").split(",") if c]
    baked = [(c, c.frames()) for c in clips()]  # проверка и экспорт — все клипы; FLY_CLIPS выбирает только кадры
    parts = {}
    for m in ("Head", "Body", "Limbs"):
        a = Q.build(m)
        obj = a.build(col)
        parts.update(Q._split_keep(obj, a, col))
    sample = {n: [v.co.copy() for v in o.data.vertices][::3] for n, o in parts.items()}
    rep = check(baked, sample)
    with open(os.path.join(out, "anim_report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    print("CHECK", json.dumps(rep, ensure_ascii=False), flush=True)
    if mode == "check":
        return
    export(os.path.join(out, "Boss6_Flytrap.anim.json"), baked)
    strips(parts, [b for b in baked if not only or b[0].name in only], out)


def strips(parts, baked, out):
    """Раскадровка каждого клипа: 8 кадров, вид 3/4 — <папка>/frames/<клип>_<k>.png (ряды собирает лист королевы)."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "concepts510"))
    import ck  # noqa: E402

    fdir = os.path.join(out, "frames")
    os.makedirs(fdir, exist_ok=True)
    cam = ck.studio(bpy.data.collections["Flytrap"], size=1.5, bg=(0.7, 0.76, 0.86))
    bpy.context.scene.view_settings.exposure = -0.3
    turn = Q.R("Z", -30)
    for clip, frames in baked:
        if clip.name == "eat":
            eat_strip(parts, frames, cam, fdir, turn, ck)
            continue
        idx = [round(i * (len(frames) - 1) / 7) for i in range(8)]
        for k, i in enumerate(idx):
            W = Q.pose_world(frames[i])
            for n, o in parts.items():
                o.matrix_world = turn @ W[n] @ Q.T(Q.PIVOTS[n])
            bpy.context.view_layer.update()
            ck.shot(cam, os.path.join(fdir, f"{clip.name}_{k}.png"), (0.0, -30.0, 7.5), (0.0, 0.0, 5.6), 50,
                    (420, 520))
        print("STRIP", clip.name, flush=True)


# раскадровка «съесть»: (время, подпись) — кадры eat_<k>.png 600×600; подписи берёт лист королевы
EAT_SHOTS = [(0.0, "стойка"), (0.35, "рывок лозой к Ловибуму"), (0.6, "отобрала: пальцы сжались"),
             (1.05, "несёт к пасти"), (1.3, "пальцы разжались — Ловибум в пасти"), (1.5, "захлоп"),
             (1.75, "жуёт"), (2.0, "жуёт"), (2.8, "набрала воздух"), (3.05, "выплюнула капсулу этажа"),
             (3.3, "капсула летит вперёд"), (3.5, "довольная")]
PLAYER_AT = V((-1.4, -7.4, 1.4))  # макет: Ловибум у игрока перед королевой (в игре его подтягивает сама игра)
MOUTH_AT = V((0, -1.9, 0.45))  # макет: Ловибум внутри пасти (система головы)


def _mat(name, rgb, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = 0.35
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


def _prop(parts_spec, name):
    """Макет из примитивов (только для раскадровки): [(тип, размеры, сдвиг, поворот, материал)] → пустышка-родитель."""
    root = bpy.data.objects.new(name, None)
    bpy.data.collections["Flytrap"].objects.link(root)
    for kind, dims, off, rot, mat in parts_spec:
        if kind == "cyl":
            bpy.ops.mesh.primitive_cylinder_add(vertices=dims[2], radius=dims[0], depth=dims[1], location=off,
                                                rotation=rot)
        elif kind == "cone":
            bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=dims[0], radius2=0, depth=dims[1], location=off,
                                            rotation=rot)
        else:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=dims[0], location=off)
        o = bpy.context.active_object
        o.data.materials.append(mat)
        o.parent = root
    return root


def eat_strip(parts, frames, cam, fdir, turn, ck):
    import math

    steel, neon = _mat("propSteel", (0.42, 0.45, 0.52)), _mat("propNeon", (0.2, 0.9, 1.0), emit=3.0)
    gold, pink = _mat("propGold", (0.96, 0.66, 0.08)), _mat("propPink", (1.0, 0.35, 0.6))
    lovi = _prop([("cyl", (0.6, 0.42, 8), (0, 0, 0), (0, 0, 0), steel),
                  ("cone", (0.48, 1.0), (0, 0, 0.7), (0, 0, math.radians(45)), neon),
                  ("cone", (0.48, 0.42), (0, 0, 0.0), (math.pi, 0, math.radians(45)), neon)], "PropLovibum")
    caps = _prop([("cyl", (0.62, 1.1, 16), (0, 0, 0), (math.pi / 2, 0, 0), gold),
                  ("ball", (0.62,), (0, 0.55, 0), None, pink), ("ball", (0.62,), (0, -0.55, 0), None, pink)],
                 "PropCapsule")
    for k, (t, _) in enumerate(EAT_SHOTS):
        P = frames[min(round(t * FPS), len(frames) - 1)]
        W = Q.pose_world(P)
        F = Q.frames(P)
        for n, o in parts.items():
            o.matrix_world = turn @ W[n] @ Q.T(Q.PIVOTS[n])
        hold = F["PalmR"] @ Q.ATTACH["LovibumHold"][1]
        if t < 0.35:
            p = PLAYER_AT
        elif t < 0.6:
            p = PLAYER_AT.lerp(hold, (t - 0.35) / 0.25)
        elif t < 1.3:
            p = hold
        else:
            p = F["Head"] @ MOUTH_AT
        lovi.hide_render = t >= 1.5
        for c in lovi.children:
            c.hide_render = lovi.hide_render
        lovi.matrix_world = turn @ Q.T(p)
        show = t >= 3.05
        if show:
            spawn = F["Head"] @ Q.ATTACH["CapsuleSpawn"][1] if t < 3.1 else None
            if spawn is None:  # полёт макета: от точки появления в кадре 3.05 вперёд и вниз по дуге
                P0 = frames[round(3.05 * FPS)]
                F0 = Q.frames(P0)
                s0 = F0["Head"] @ Q.ATTACH["CapsuleSpawn"][1]
                d0 = (F0["Head"].to_3x3() @ V((0, -1, 0))).normalized()
                dt = t - 3.05
                spawn = s0 + d0 * 10.0 * dt + V((0, 0, 4.0 * dt - 16.0 * dt * dt))
                spawn.z = max(spawn.z, 0.5)
            caps.matrix_world = turn @ Q.T(spawn)
        for c in [caps, *caps.children]:
            c.hide_render = not show
        bpy.context.view_layer.update()
        ck.shot(cam, os.path.join(fdir, f"eat_{k}.png"), (6.0, -36.0, 8.0), (-1.8, -3.0, 5.2), 72, (600, 600))
    print("STRIP eat", flush=True)


if __name__ == "__main__":
    main()
