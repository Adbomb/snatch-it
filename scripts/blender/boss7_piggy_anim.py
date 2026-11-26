"""Босс 7 «Копилка-громила»: 10 клипов (шаг 2 D64, D73) на игровой модели scripts/blender/boss7_piggy.py.

Клипы — ключевые позы в параметрах скелета (подъём, наклон и крен тела, голова, ноги, челюсть, язык, уши, веки,
крестики, хвост, монеты, трещины, горка); между ключами — кубический сплайн по каждому параметру. Каждый кадр
садится на землю (самая низкая точка тела, ног и головы — z = 0). Длительности и события — как у Йети и Сфинкса
(Config/Battle.Timeline, HitDelay; начало выпада в игре — AttackAt):
  sleep_idle 6.4 (цикл) — лежит на брюхе, дышит, похрапывает (челюсть), уши подрагивают;
  wake 2.4 — открыл глаза (1.0, конец Wake), поднялся на ноги (1.9, конец StandUp), боевая стойка;
  combat_idle 3.6 (цикл) — переминается, фыркает, хвост виляет; walk 0.8 (цикл, рысь: диагональные пары ног);
  ram 1.3 — «Таран пятачком»: замах назад, бросок вперёд головой вниз, монеты выскакивают из щели
        (AttackAt 0.45, контакт 0.7);
  coin_hail 1.4 — «Монетный град» (только анимация, D64 п. 3): на дыбы, удар передними, фонтан монет
        (AttackAt 0.5, удар 0.75);
  hit 0.47; victory 2.2 (довольно хрюкает, привстаёт, виляет хвостом → stand);
  defeat 2.4 (заваливается набок, трещины, горка монет, глаза-крестики, язык набок; затем встаёт → stand;
        трещины и горка уходят в конце); fall_asleep 1.6 (ложится, закрывает глаза → sleep).
Выход: <папка>/Boss7_Piggy.anim.json (кадры: Transform суставов в осях Roblox, [x, y, z, qx, qy, qz, qw]),
<папка>/frames/<клип>_<k>.png (8 кадров на клип) и anim_report.json. В assets — после «ок» листа аудита.
Запуск: blender --background --factory-startup --python scripts/blender/boss7_piggy_anim.py -- <репо> <папка> [check]
"""

import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boss7_piggy as B  # noqa: E402

FPS = 30
S2 = (1, -1)
LEGS = ("FL", "FR", "BL", "BR")
SCAL = ("lift", "pitch", "roll", "jaw", "tongue", "lid", "dizzy", "tail", "burst", "fountain", "slot", "crack", "heap")


def flat(P):
    f = {k: float(P[k]) for k in SCAL}
    for i, c in enumerate(P["head"]):
        f[f"head{i}"] = c
    for k in LEGS:
        f[f"{k}0"], f[f"{k}1"] = P["legs"][k]
    for s in S2:
        f[f"ear{s}"] = P["ears"][s]
    return f


def unflat(f):
    P = {k: f[k] for k in SCAL}
    P["head"] = (f["head0"], f["head1"], f["head2"])
    P["legs"] = {k: (f[f"{k}0"], f[f"{k}1"]) for k in LEGS}
    P["ears"] = {s: f[f"ear{s}"] for s in S2}
    return P


def pose(base, **kw):
    return B.pose(B.POSES[base] if isinstance(base, str) else base, **kw)


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
            P = unflat({c: self._channel(ts, [x[c] for x in fl], t) for c in fl[0]})
            for k in ("tongue", "lid", "dizzy", "burst", "fountain", "slot", "crack", "heap"):
                P[k] = min(max(P[k], 0.0), 1.0)
            out.append(B.ground(P))
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


def clips():
    P = B.POSES
    SLEEP, STAND, COMBAT = P["sleep"], P["stand"], P["combat"]
    C = []
    inhale = pose("sleep", pitch=1.0, head=(12.0, 8.0, 4.0), jaw=5.0, ears={1: 0.5, -1: 0.65})
    C.append(Clip("sleep_idle", "Сон", 6.4, [(0.0, SLEEP), (3.2, inhale), (6.4, SLEEP)], loop=True))
    blink = pose("sleep", lid=0.4, head=(6.0, 4.0, 2.0), ears={1: 0.2, -1: 0.2})
    crouch = pose("sleep", lid=0.0, head=(0.0, 0.0, 0.0), legs=B.legs_all(-40, 10, 40, 8), ears={1: 0.0, -1: 0.0})
    C.append(Clip("wake", "Пробуждение", 2.4, [(0.0, SLEEP), (0.5, blink), (1.0, pose("sleep", lid=0.0, ears={
        1: 0.0, -1: 0.0}, head=(0.0, 0.0, 0.0))), (1.45, crouch), (1.9, STAND), (2.4, COMBAT)],
        events={"проснулся (конец Wake)": 1.0, "встал (конец StandUp)": 1.9}, start="sleep", end="combat"))
    sway = pose("combat", roll=3.0, head=(6.0, 6.0, 2.0), tail=25.0, jaw=12.0)
    sway2 = pose("combat", roll=-3.0, head=(6.0, -6.0, -2.0), tail=-25.0)
    C.append(Clip("combat_idle", "Боевая стойка", 3.6, [(0.0, COMBAT), (0.9, sway), (1.8, COMBAT), (2.7, sway2),
                                                       (3.6, COMBAT)], loop=True))
    trA = pose("combat", legs={"FL": (-22, 10), "BR": (-18, 6), "FR": (18, 10), "BL": (20, 6)}, pitch=5.0)
    trB = pose("combat", legs={"FL": (18, 10), "BR": (20, 6), "FR": (-22, 10), "BL": (-18, 6)}, pitch=5.0)
    C.append(Clip("walk", "Ходьба", 0.8, [(0.0, trA), (0.4, trB), (0.8, trA)], loop=True,
                  events={"левая передняя касается земли": 0.0, "правая передняя касается земли": 0.4}))
    wind = pose("combat", pitch=-6.0, head=(-12.0, 0.0, 0.0), legs=B.legs_all(10, 14, 18, 8), jaw=8.0)
    hitp = pose("ram", burst=0.55)
    follow = pose("ram", head=(4.0, 0.0, 0.0), burst=1.0, jaw=14.0)
    C.append(Clip("ram", "Таран пятачком", 1.3, [(0.0, COMBAT), (0.45, wind), (0.7, hitp), (0.95, follow),
                                                 (1.3, COMBAT)],
                  events={"начало выпада в игре (AttackAt)": 0.45, "контакт: таран": 0.7}, start="combat",
                  end="combat"))
    rear = pose("hail", fountain=0.0, slot=1.0)
    slam = pose("combat", pitch=12.0, legs=B.legs_all(-20, 18, 12, 8), jaw=26.0, head=(10.0, 0, 0), fountain=0.55)
    rain = pose("combat", fountain=1.0, jaw=10.0)
    C.append(Clip("coin_hail", "Монетный град", 1.4, [(0.0, COMBAT), (0.5, rear), (0.75, slam), (1.05, rain),
                                                      (1.4, COMBAT)],
                  events={"начало выпада в игре (AttackAt)": 0.5, "удар передними, фонтан монет": 0.75},
                  start="combat", end="combat"))
    ouch = pose("combat", pitch=-8.0, head=(-18.0, -8.0, -6.0), lid=0.5, ears={1: 0.5, -1: 0.5}, jaw=16.0)
    C.append(Clip("hit", "Получение урона", 0.4667, [(0.0, COMBAT), (0.07, ouch), (0.4667, COMBAT)],
                  events={"пик реакции": 0.07}, start="combat", end="combat"))
    proud = pose("stand", pitch=-14.0, head=(-20.0, 0.0, 0.0), jaw=18.0, tail=30.0, slot=1.0)
    proud2 = pose("stand", pitch=-10.0, head=(-16.0, 6.0, 4.0), jaw=6.0, tail=-30.0)
    C.append(Clip("victory", "Победа", 2.2, [(0.0, COMBAT), (0.45, proud), (0.8, proud2), (1.15, proud),
                                             (1.6, proud2), (2.2, STAND)],
                  events={"привстал, хрюкает": 0.45, "стоит (поза stand)": 2.2}, start="combat", end="stand"))
    crash = pose("defeat", crack=0.6, heap=0.3, dizzy=0.0, tongue=0.0)
    down = P["defeat"]
    daze = pose("defeat", head=(18.0, -20.0, -14.0))
    up = pose("combat", crack=1.0, heap=1.0, dizzy=0.0, lid=0.4, ears={1: 0.5, -1: 0.5})
    clean = pose("stand", crack=0.0, heap=0.0)
    C.append(Clip("defeat", "Поражение", 2.4, [(0.0, COMBAT), (0.35, crash), (0.6, down), (0.95, daze), (1.62, daze),
                                               (2.0, up), (2.4, clean)],
                  events={"завалился, треснул": 0.35, "монеты высыпались": 0.6, "лежит (оглушён)": 0.95,
                          "начинает вставать": 1.62}, start="combat", end="stand"))
    kneel = pose("stand", legs=B.legs_all(-40, 10, 40, 8), lid=0.3, ears={1: 0.3, -1: 0.3})
    C.append(Clip("fall_asleep", "Засыпание", 1.6, [(0.0, STAND), (0.6, kneel), (1.1, pose("sleep", lid=0.6)),
                                                    (1.6, SLEEP)],
                  events={"лёг": 1.1}, start="stand", end="sleep"))
    return C


def export(path, baked):
    out = {"fps": FPS, "order": list(B.RIG_TREE), "scale": B.SCALE,
           "format": "frames[кадр][часть по order] = [x, y, z, qx, qy, qz, qw] — Transform Motor6D в осях Roblox, "
                     "стады", "clips": {}}
    for clip, frames in baked:
        rows = []
        for P in frames:
            tr = B.transforms(P)
            row = []
            for n in B.RIG_TREE:
                m3, off = tr[n]
                t = B.AX @ (off * B.SCALE)
                q = (B.AX @ m3 @ B.AX.transposed()).to_quaternion()
                row.append([round(v, 4) for v in (t.x, t.y, t.z, q.x, q.y, q.z, q.w)])
            rows.append(row)
        out["clips"][clip.name] = {"title": clip.title, "duration": round(clip.dur, 4), "loop": clip.loop,
                                   "start_pose": clip.start, "end_pose": clip.end,
                                   "events": {k: round(v, 4) for k, v in clip.events.items()}, "frames": rows}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("EXPORT_OK", path, round(os.path.getsize(path) / 1e6, 2), "МБ", flush=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    repo, out = os.path.abspath(argv[0]), os.path.abspath(argv[1])
    mode = argv[2] if len(argv) > 2 else ""
    os.makedirs(out, exist_ok=True)
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "concepts510"))
    import ck  # noqa: E402

    col = ck.reset_scene()
    B.rest_frames()
    art, _ = B.build()
    obj = art.build(col)
    for mat in obj.data.materials:
        k = mat.name.rsplit("_", 1)[-1]
        b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b is not None and k.startswith(("gold", "coin")):
            b.inputs["Metallic"].default_value, b.inputs["Roughness"].default_value = 0.5, 0.3
    parts = B.split(obj, art, col)
    bpy.context.view_layer.update()
    B.sample_parts(parts)
    for Pz in B.POSES.values():
        B.ground(Pz)
    baked = [(c, c.frames()) for c in clips()]
    rep = {c.name: {"frames": len(fr), "lift_min": round(min(P["lift"] for P in fr), 3),
                    "lift_max": round(max(P["lift"] for P in fr), 3)} for c, fr in baked}
    with open(os.path.join(out, "anim_report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    print("CHECK", json.dumps(rep, ensure_ascii=False), flush=True)
    if mode == "check":
        return
    export(os.path.join(out, "Boss7_Piggy.anim.json"), baked)
    fdir = os.path.join(out, "frames")
    os.makedirs(fdir, exist_ok=True)
    cam = ck.studio(col, size=1.5, bg=(0.7, 0.76, 0.86))
    bpy.context.scene.view_settings.exposure = -0.3
    turn = B.R("Z", -35)
    for clip, frames in baked:
        for k, i in enumerate([round(i * (len(frames) - 1) / 7) for i in range(8)]):
            B.place(parts, frames[i], turn)
            ck.shot(cam, os.path.join(fdir, f"{clip.name}_{k}.png"), (0, -30.0, 9.5), (0, 0, 4.0), 55, (420, 460))
        print("STRIP", clip.name, flush=True)


if __name__ == "__main__":
    main()
