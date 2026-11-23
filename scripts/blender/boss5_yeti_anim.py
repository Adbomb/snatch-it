"""Босс 5 «Йети-коллекционер»: 10 клипов (шаг 2 D64) на игровой модели scripts/blender/boss5_yeti.py.

Клипы — ключевые позы в параметрах скелета (таз, наклоны, голова, руки, пальцы, лицо, глыба, экспонаты); между
ключами — кубический сплайн по каждому параметру (без остановок в проходных ключах). Ноги — цели стоп на земле
(обратная кинематика каждый кадр: опорная стопа стоит, перенос — по дуге). Глыба — на спине или в мире (снята на
землю во сне, поднята над головой при пробуждении); переход «мир ↔ спина» — смесь матриц от текущего положения спины.
Длительности и события — как у Сфинкса (Config/Battle.Timeline, HitDelay; начало выпада в игре — AttackAt):
  sleep_idle 6.4 (цикл) — сидит, привалившись к глыбе, дышит, похрапывает;
  wake 2.4 — открыл глаза (1.0, конец Wake), встал, поднял глыбу над головой и закинул на спину (1.9, конец StandUp),
             боевая стойка;
  combat_idle 3.6 (цикл); walk 0.8 (цикл, шаг на месте, скорость стоп ≈ Battle.Speed);
  smash 1.3 — основной выпад: кулак сверху (AttackAt 0.45, удар 0.7);
  ice_clap 1.4 — «Ледяной хлопок» двумя ладонями (D64, только анимация; AttackAt 0.5, хлопок 0.75);
  hit 0.47; victory 2.2 (рёв, бьёт себя в грудь → stand); defeat 2.4 (сел, верхушка глыбы откинулась, экспонаты
  подпрыгнули, монокль слетел; захлопнул верхушку, встаёт → stand); fall_asleep 1.6 (снял глыбу, сел, закрыл глаза → sleep).
Выход: assets/models/Boss5_Yeti.anim.json (кадры: Transform суставов в осях Roblox, [x, y, z, qx, qy, qz, qw]),
кадры клипов в <папка>/strip_<клип>.png и anim_report.json (провал под землю, недотяг ног).
Режимы: (пусто) — расчёт, экспорт и кадры; export — без кадров.
Запуск: blender --background --factory-startup --python scripts/blender/boss5_yeti_anim.py -- <репо> <папка> [export]
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boss5_yeti as Y  # noqa: E402

V = Vector
S2 = (1, -1)
FPS = 30
TOL = 0.1  # кончики прядей меха до 0.1 ед. (0.2 стада) в снегу не видны — не провал
T, R = Y.T, Y.R


# ── Параметры позы ↔ плоский словарь ────────────────────────────────────────────────────────────────────────
def feet_of(P):
    """Цели стоп позы: заданные или из углов ног (прямая кинематика)."""
    if P.get("feet"):
        return {s: tuple(P["feet"][s]) for s in S2}
    M = Y.skeleton(P)
    out = {}
    for s in S2:
        a = M[("an", s)].translation
        out[s] = (a.y, a.z - Y.ANKLE_H, P["leg"][s][2])
    return out


def flat(P):
    f = {}
    for i, c in enumerate(P["pelvis"]):
        f[f"pel{i}"] = c
    f["pitch"], f["torso"], f["jaw"], f["mono"] = P["pitch"], P["torso"], P["jaw"], P["mono"]
    for i, c in enumerate(P["head"]):
        f[f"head{i}"] = c
    for s in S2:
        for i, c in enumerate((tuple(P["arm"][s]) + (0.0,))[:5]):
            f[f"arm{s}{i}"] = c
        f[f"curl{s}"] = P["curl"][s]
        f[f"lid{s}"] = P["lid"][s]
        for i, c in enumerate(P["brow"][s]):
            f[f"brow{s}{i}"] = c
    for s, ft in feet_of(P).items():
        for i, c in enumerate(ft):
            f[f"feet{s}{i}"] = c
    for i, c in enumerate(P["top"]):
        f[f"top{i}"] = c
    for n in Y.EXHIBITS:
        for i, c in enumerate(P["ex"].get(n, (0, 0, 0, 0))):
            f[f"ex{n}{i}"] = c
    return f


def unflat(f):
    P = Y.base_pose()
    P["pelvis"] = V((f["pel0"], f["pel1"], f["pel2"]))
    P["pitch"], P["torso"], P["jaw"], P["mono"] = f["pitch"], f["torso"], f["jaw"], f["mono"]
    P["head"] = (f["head0"], f["head1"], f["head2"])
    P["arm"] = {s: tuple(f[f"arm{s}{i}"] for i in range(5)) for s in S2}
    P["curl"] = {s: f[f"curl{s}"] for s in S2}
    P["lid"] = {s: max(0.0, min(1.0, f[f"lid{s}"])) for s in S2}
    P["brow"] = {s: (f[f"brow{s}0"], f[f"brow{s}1"]) for s in S2}
    P["feet"] = {s: tuple(f[f"feet{s}{i}"] for i in range(3)) for s in S2}
    P["top"] = (f["top0"], f["top1"])
    P["ex"] = {n: tuple(f[f"ex{n}{i}"] for i in range(4)) for n in Y.EXHIBITS}
    return P


def pose(base, **kw):
    """Поза из библиотеки модели (имя или словарь) с правками."""
    P = Y.POSES[base] if isinstance(base, str) else base
    Q = {k: (dict(v) if isinstance(v, dict) else v) for k, v in P.items()}
    for k, v in kw.items():
        if isinstance(v, dict) and isinstance(Q.get(k), dict):
            Q[k] = {**Q[k], **v}
        else:
            Q[k] = v
    return Q


# ── Клип: ключи → кадры ─────────────────────────────────────────────────────────────────────────────────────
class Clip:
    def __init__(self, name, title, dur, keys, loop=False, events=None, start=None, end=None):
        self.name, self.title, self.dur, self.loop = name, title, dur, loop
        self.keys = sorted(keys, key=lambda k: k[0])
        self.events = events or {}
        self.start, self.end = start, end

    def frames(self):
        n = round(self.dur * FPS)
        ts = [k[0] for k in self.keys]
        fl = [flat(Y.solve(k[1])) for k in self.keys]
        blocks = [(None if k[1].get("block") is None else k[1]["block"]) for k in self.keys]
        out = []
        for i in range(n + (0 if self.loop else 1)):
            t = min(i / FPS, self.dur)
            f = {c: self._channel(ts, [x[c] for x in fl], t) for c in fl[0]}
            P = unflat(f)
            P["block"] = self._block(ts, blocks, t, P)
            out.append(P)
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
            if self.loop:  # ключи 0 и dur совпадают: соседи берутся через шов цикла
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

    def _block(self, ts, blocks, t, P):
        j, u = self._seg(ts, t)
        a, b = blocks[j], blocks[j + 1]
        if a is None and b is None:
            return None
        att = Y.block_attached(Y.skeleton(Y.solve(P)))
        ma = att if a is None else a
        mb = att if b is None else b
        k = u * u * (3 - 2 * u)
        return Y.blend(ma, mb, k)


# ── Ключевые позы клипов ────────────────────────────────────────────────────────────────────────────────────
SLEEP = Y.POSES["sleep"]
COMBAT = Y.POSES["combat"]
STAND = Y.POSES["stand"]
OVERHEAD = T((0.0, -1.0, 6.2))  # глыба над головой (система глыбы → мир): основание на высоте ≈ 7.8
LIFTED_BACK = None  # на спине


def clips():
    C = []
    # сон: дышит (торс и голова), похрапывает (челюсть), чуть шевелит пальцами
    inhale = pose("sleep", torso=-15.0, head=(19.0, 0.0, 12.0), jaw=4.0, pelvis=V((0, 0.35, 1.02)))
    C.append(Clip("sleep_idle", "Сон", 6.4, [(0.0, SLEEP), (3.2, inhale), (6.4, SLEEP)], loop=True))
    # пробуждение
    blink = pose("sleep", lid={1: 0.55, -1: 0.65}, head=(10.0, 0.0, 8.0), brow={1: (4, 0.06), -1: (4, 0.06)})
    reach = pose("alert", pelvis=V((0, 0.0, 1.5)), torso=34.0, head=(-20.0, 0, 0),
                 arm={1: (-35.0, 40.0, 45.0, 0), -1: (-35.0, 40.0, 45.0, 0)}, curl={1: 0.7, -1: 0.7},
                 feet={1: (-0.4, 0.0, 0.0), -1: (-0.2, 0.0, 0.0)})
    lift = pose("stand", pelvis=V((0, 0.1, 2.2)), torso=4.0, head=(-22.0, 0, 0), jaw=10.0,
                arm={1: (168.0, 14.0, 24.0, 0), -1: (168.0, 14.0, 24.0, 0)}, curl={1: 0.8, -1: 0.8},
                feet={1: (0.2, 0.0, 0.0), -1: (0.4, 0.0, 0.0)}, block=OVERHEAD)
    stood = pose("stand", arm={1: (60.0, 30.0, 80.0, 0), -1: (60.0, 30.0, 80.0, 0)}, curl={1: 0.5, -1: 0.5})
    C.append(Clip("wake", "Пробуждение", 2.4, [(0.0, SLEEP), (0.5, blink), (1.0, Y.POSES["alert"]), (1.35, reach),
                                               (1.65, lift), (1.9, stood), (2.4, COMBAT)],
                  events={"проснулся (конец Wake)": 1.0, "глыба на спине (конец StandUp)": 1.9}, start="sleep",
                  end="combat"))
    # боевая стойка
    dip = pose("combat", pelvis=V((0, 0.1, 1.92)))
    dip2 = pose("combat2", pelvis=V((0, 0.15, 1.88)))
    C.append(Clip("combat_idle", "Боевая стойка", 3.6, [(0.0, COMBAT), (0.9, dip), (1.8, Y.POSES["combat2"]),
                                                       (2.7, dip2), (3.6, COMBAT)], loop=True))
    # шаг на месте: опорная стопа едет назад со скоростью боя, переносная — по дуге вперёд
    A, B = Y.POSES["walkA"], Y.POSES["walkB"]
    passA = pose("walkA", pelvis=V((0, 0.1, 2.25)), feet={1: (0.05, 0.0, 0.0), -1: (0.05, 0.45, -12.0)},
                 arm={1: (35.0, 14.0, 35.0, 5), -1: (35.0, 14.0, 35.0, 5)})
    passB = pose("walkB", pelvis=V((0, 0.1, 2.25)), feet={1: (0.05, 0.45, -12.0), -1: (0.05, 0.0, 0.0)},
                 arm={1: (35.0, 14.0, 35.0, 5), -1: (35.0, 14.0, 35.0, 5)})
    C.append(Clip("walk", "Ходьба", 0.8, [(0.0, A), (0.2, passA), (0.4, B), (0.6, passB), (0.8, A)], loop=True,
                  events={"правая стопа касается земли": 0.0, "левая стопа касается земли": 0.4}))
    # основной выпад: кулак сверху
    wind = pose("combat", pelvis=V((0, 0.25, 2.1)), torso=6.0, head=(-30.0, 0, 0), jaw=22.0,
                arm={1: (165.0, 18.0, 70.0, 0), -1: (40.0, 30.0, 60.0, 10)}, feet={1: (-0.6, 0.0, 0.0), -1: (0.8, 0, 0)})
    hold = pose("bite", pelvis=V((0, -0.15, 1.8)), torso=36.0)
    C.append(Clip("smash", "Удар кулаком сверху", 1.3, [(0.0, COMBAT), (0.45, wind), (0.7, Y.POSES["bite"]),
                                                        (0.95, hold), (1.3, COMBAT)],
                  events={"начало выпада в игре (AttackAt)": 0.45, "контакт: удар кулаком": 0.7}, start="combat",
                  end="combat"))
    # «Ледяной хлопок»: руки широко → хлопок ладонями перед собой
    wide = pose("combat", pelvis=V((0, 0.2, 2.15)), torso=8.0, head=(-34.0, 0, 0), jaw=28.0,
                arm={1: (70.0, 80.0, 25.0, 0), -1: (70.0, 80.0, 25.0, 0)}, curl={1: 0.0, -1: 0.0},
                feet={1: (-0.4, 0.0, 0.0), -1: (0.6, 0, 0)})
    after = pose("swipe", pelvis=V((0, -0.05, 1.95)), torso=26.0, jaw=18.0)
    C.append(Clip("ice_clap", "Ледяной хлопок", 1.4, [(0.0, COMBAT), (0.5, wide), (0.75, Y.POSES["swipe"]),
                                                      (1.0, after), (1.4, COMBAT)],
                  events={"начало выпада в игре (AttackAt)": 0.5, "контакт: хлопок ладонями": 0.75}, start="combat",
                  end="combat"))
    # получение урона
    C.append(Clip("hit", "Получение урона", 0.4667, [(0.0, COMBAT), (0.07, Y.POSES["hit"]), (0.4667, COMBAT)],
                  events={"пик реакции": 0.07}, start="combat", end="combat"))
    # победа: рёв с поднятыми кулаками, бьёт себя в грудь, самодовольная стойка
    smug = pose("stand", head=(-20.0, 0, 6.0))
    C.append(Clip("victory", "Победа", 2.2, [(0.0, COMBAT), (0.4, Y.POSES["bark"]), (0.7, Y.POSES["bark2"]),
                                             (0.95, Y.POSES["bark"]), (1.2, Y.POSES["bark2"]), (1.94, smug),
                                             (2.2, STAND)],
                  events={"кулаки подняты": 0.4, "стоит (поза stand)": 1.94}, start="combat", end="stand"))
    # поражение: сел, верхушка откинулась, экспонаты подпрыгнули; захлопнул и встаёт
    sat = pose("dizzy", top=(0.0, 0.0), ex={}, mono=0.0, lid={1: 0.3, -1: 0.3})
    pop = pose("dizzy", ex={"ExCup": (-0.4, -0.6, 1.9, 50), "ExGem": (0.5, -0.4, 1.5, -70),
                            "ExLovibum": (0.2, -0.2, 0.6, 20), "ExCritter": (-0.2, -0.3, 0.9, -25)})
    daze = pose("dizzy", head=(-2.0, -14.0, -16.0))
    shut = pose("dizzy", top=(0.0, 0.0), ex={}, head=(-10.0, 0, 0), mono=0.6)
    rise = pose("stand", pelvis=V((0, 0.0, 1.8)), torso=34.0, head=(-12.0, 0, 0), mono=0.3, lid={1: 0.3, -1: 0.3},
                arm={1: (40.0, 30.0, 60.0, 0), -1: (40.0, 30.0, 60.0, 0)}, feet={1: (-0.2, 0, 0), -1: (0.2, 0, 0)})
    C.append(Clip("defeat", "Поражение", 2.4, [(0.0, COMBAT), (0.35, sat), (0.6, pop), (0.95, daze), (1.3, shut),
                                               (1.62, shut), (2.0, rise), (2.4, STAND)],
                  events={"сел, глыба треснула": 0.35, "верхушка откинута, экспонаты в воздухе": 0.6,
                          "лежит (оглушён)": 0.95, "начинает вставать": 1.62}, start="combat", end="stand"))
    # засыпание: снимает глыбу, садится, закрывает глаза
    unload = pose("stand", pelvis=V((0, 0.1, 2.1)), torso=24.0, arm={1: (-40.0, 40.0, 40.0, 0), -1: (-40.0, 40.0, 40.0, 0)},
                  curl={1: 0.7, -1: 0.7}, block=T((0.0, 0.6, -0.9)))
    sit = pose("alert", lid={1: 0.4, -1: 0.4})
    C.append(Clip("fall_asleep", "Засыпание", 1.6, [(0.0, STAND), (0.45, unload), (0.88, sit), (1.2, pose(
        "sleep", lid={1: 0.7, -1: 0.7})), (1.6, SLEEP)], events={"сел (поза alert)": 0.88}, start="stand", end="sleep"))
    return C


# ── Экспорт и проверки ──────────────────────────────────────────────────────────────────────────────────────
def export(path, baked):
    out = {"fps": FPS, "order": list(Y.RIG_TREE), "scale": Y.SCALE,
           "format": "frames[кадр][часть по order] = [x, y, z, qx, qy, qz, qw]", "clips": {}}
    for clip, frames in baked:
        rows = []
        for P in frames:
            tr = Y.transforms(P)
            row = []
            for n in Y.RIG_TREE:
                m3, off = tr[n]
                t = Y.AX @ (off * Y.SCALE)
                q = (Y.AX @ m3 @ Y.AX.transposed()).to_quaternion()
                row.append([round(v, 4) for v in (t.x, t.y, t.z, q.x, q.y, q.z, q.w)])
            rows.append(row)
        out["clips"][clip.name] = {"title": clip.title, "duration": round(clip.dur, 4), "loop": clip.loop,
                                   "start_pose": clip.start, "end_pose": clip.end,
                                   "events": {k: round(v, 4) for k, v in clip.events.items()}, "frames": rows}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("EXPORT_OK", path, round(os.path.getsize(path) / 1e6, 2), "МБ", flush=True)


def check(baked, sample):
    """Провал под землю (нижняя точка ниже −0.05 ед.) и недотяг ног по кадрам клипа."""
    rep = {}
    for clip, frames in baked:
        lows, short, who = [], 0.0, {}
        for P in frames:
            W = Y.pose_world(P)
            # сосульки под снятой глыбой воткнуты в снег (глыба стоит на земле) — не провал
            per = {n: min((W[n] @ (Y.PIVOTS[n] + c)).z for c in pts) for n, pts in sample.items()
                   if not (n == "Block" and P["block"] is not None)}
            n_low = min(per, key=per.get)
            lows.append(per[n_low])
            if per[n_low] < -TOL:
                who[n_low] = round(min(who.get(n_low, 0.0), per[n_low]), 3)
            for s in S2:
                y, lift, an = P["feet"][s]
                _, sh = Y.leg_ik(P, s, (s * Y.HIP.x, y, Y.ANKLE_H + lift), an)
                short = max(short, sh)
        rep[clip.name] = {"frames": len(frames), "lowest": round(min(lows), 3), "highest_low": round(max(lows), 3),
                          "below_ground_frames": sum(1 for z in lows if z < -TOL), "below_parts": who,
                          "leg_short_max": round(short, 3)}
    return rep


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    repo, out = os.path.abspath(argv[0]), os.path.abspath(argv[1])
    mode = argv[2] if len(argv) > 2 else ""
    os.makedirs(out, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    col = bpy.data.collections.new("Yeti")
    bpy.context.scene.collection.children.link(col)
    Y.rest_frames()
    only = [c for c in os.environ.get("YETI_CLIPS", "").split(",") if c]
    baked = [(c, c.frames()) for c in clips() if not only or c.name in only]
    # части (материалы сборки) — для проверок и кадров
    parts = {}
    for m in ("Head", "Body", "Limbs"):
        a = Y.build(m)
        obj = a.build(col)
        parts.update(Y._split_keep(obj, a, col))
    sample = {n: [v.co.copy() for v in o.data.vertices][::3] for n, o in parts.items()}
    rep = check(baked, sample)
    with open(os.path.join(out, "anim_report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    print("CHECK", json.dumps(rep, ensure_ascii=False), flush=True)
    if not only:
        export(os.path.join(repo, "assets", "models", "Boss5_Yeti.anim.json"), baked)
    if mode == "export":
        return
    strips(parts, baked, out)


def strips(parts, baked, out):
    """Раскадровка каждого клипа: 8 кадров, вид 3/4 (лёд полупрозрачный) — файлы <папка>/frames/<клип>_<k>.png;
    ряды собирает scripts/boss5_sheets.py (в Blender нет PIL)."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "concepts510"))
    import ck  # noqa: E402

    fdir = os.path.join(out, "frames")
    os.makedirs(fdir, exist_ok=True)
    cam = ck.studio(bpy.data.collections["Yeti"], size=1.5, bg=(0.7, 0.76, 0.86))
    bpy.context.scene.view_settings.exposure = -0.3
    for n in Y.ICE_PARTS:
        me = parts[n].data
        for i, m in enumerate(me.materials):
            mm = m.copy()
            b = next((x for x in mm.node_tree.nodes if x.type == "BSDF_PRINCIPLED"), None)
            if b is not None:
                b.inputs["Alpha"].default_value = 0.38
            mm.surface_render_method = "BLENDED"
            me.materials[i] = mm
    turn = Y.R("Z", -35)
    for clip, frames in baked:
        idx = [round(i * (len(frames) - 1) / 7) for i in range(8)]
        for k, i in enumerate(idx):
            W = Y.pose_world(frames[i])
            for n, o in parts.items():
                o.matrix_world = turn @ W[n] @ Y.T(Y.PIVOTS[n])
            bpy.context.view_layer.update()
            ck.shot(cam, os.path.join(fdir, f"{clip.name}_{k}.png"), (0, -24.0, 6.5), (0, 0, 4.6), 55, (420, 520))
        print("STRIP", clip.name, flush=True)


if __name__ == "__main__":
    main()
