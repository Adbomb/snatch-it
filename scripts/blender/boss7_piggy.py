"""Босс 7 «Копилка-громила» (Банк) — игровая модель: части на Motor6D, позы, проверки (шаг 2 D64, D73).

Формы — утверждённая копилка v2 (scripts/blender/boss7/piggy.py, листы assets/concepts/bosses_5_10/boss7/). Отличия
игровой модели от концепта:
- модель собрана в покое (поза «stand») и разрезана на части с точками вращения (D18): Body (корень) → Head → Jaw →
  Tongue, EarL/R, LidL/R (веки), DizzyL/R (глаза-крестики); ноги LegFL/FR/BL/BR; Tail; SlotCoin (монета в щели);
  Coin1…6 (монеты «Тарана» и «Монетного града»); Cracks (трещины и пролом); Heap (горка монет поражения);
- выражения и эффекты — только сдвигом и поворотом частей: в покое веки, крестики и язык спрятаны внутри головы,
  трещины — внутри тела, горка монет — под землёй, монеты — в теле под щелью; в позах они выезжают наружу;
- глаза на 20–30 % крупнее концепта, с белком (правка владельца 2026-11-26): издалека читаются глаза, а не только
  пятачок и брови.
Позы — параметры скелета (подъём, наклон, крен тела, голова, каждая нога, челюсть, язык, уши, веки, крестики, хвост,
монеты, трещины, горка). frames(P) → система каждой части; pose_world(P) → матрица «покой → поза»; transforms(P) →
Transform суставов относительно покоя (как у Йети, Boss5_Yeti.anim.json).
Игровая копия ≤ 8 000 треугольников. Карты (Head / Body / Limbs) — после «ок» листа аудита (D64 п. 7).

Пишет кадры поз и report.json в папку кадров; FBX и rig.json — режим export (после «ок»).
Запуск: blender --background --factory-startup --python scripts/blender/boss7_piggy.py -- <репо> <кадры> [check|export]
Подключается и как модуль (boss7_piggy_anim.py): тогда ничего не собирает.
Зависит от boss7/piggy.py (формы v2), art_style.py, anatomy_kit.py, dragon10/v4_kit.py, joint_check.py.
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "boss7"), os.path.join(HERE, "dragon10")):
    if p not in sys.path:
        sys.path.insert(0, p)
import anatomy_kit as A  # noqa: E402
import art_style as S  # noqa: E402
import piggy as PG  # noqa: E402

V = Vector
S2 = (1, -1)
T, R, about = PG.T, PG.R, PG.about
SCALE = 1.967  # стадов на единицу модели: высота в стойке 16 стадов (концепт v2, stats.json)
AX = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))  # оси Roblox: (x, y, z) Blender → (x, z, −y)
EYE_R = 0.43  # концепт 0.34 → +26 %
HC = PG.HEAD_C
JAW_PIV = V((0, -5.2, HC.z + 0.32))
TONGUE_PIV = V((0.3, -6.15, HC.z + 0.42))
EAR_BASE = {s: V((s * 1.4, HC.y + 0.6, HC.z + 3.15)) for s in S2}
TAIL_BASE = V((0.2, PG.BODY_Y[1] - 0.4, PG.BODY_Z + 0.6))
HIDE = 0.5  # насколько прячутся внутрь веки, крестики, язык и трещины
COINS = 6

RIG_TREE = {"Body": (None, "Body"), "Head": ("Body", "Head"), "Jaw": ("Head", "Head"), "Tongue": ("Jaw", "Head"),
            "EarL": ("Head", "Head"), "EarR": ("Head", "Head"), "LidL": ("Head", "Head"), "LidR": ("Head", "Head"),
            "DizzyL": ("Head", "Head"), "DizzyR": ("Head", "Head"),
            "LegFL": ("Body", "Limbs"), "LegFR": ("Body", "Limbs"), "LegBL": ("Body", "Limbs"),
            "LegBR": ("Body", "Limbs"), "Tail": ("Body", "Limbs"), "SlotCoin": ("Body", "Body"),
            **{f"Coin{i}": ("Body", "Body") for i in range(1, COINS + 1)},
            "Cracks": ("Body", "Body"), "Heap": ("Body", "Body")}
MAPS = {m: tuple(p for p, (_, mm) in RIG_TREE.items() if mm == m) for m in ("Head", "Body", "Limbs")}


def side(s):
    return "L" if s > 0 else "R"


# ── Позы ──────────────────────────────────────────────────────────────────────────────────────────────────────
# legs: {"FL": (мах вперёд −/назад +, развод), …}; ears: {s: повис 0…1}; lid, dizzy, tongue, crack, heap — 0…1;
# burst — монеты «Тарана» 0…1 (вылет из щели дугой), fountain — «Монетного града» 0…1; slot — подскок монеты в щели.
BASE = dict(lift=0.0, pitch=0.0, roll=0.0, head=(4.0, 0.0, 0.0), jaw=0.0, tongue=0.0,
            legs={"FL": (0.0, 6.0), "FR": (0.0, 6.0), "BL": (0.0, 5.0), "BR": (0.0, 5.0)},
            ears={1: 0.0, -1: 0.0}, lid=0.0, dizzy=0.0, tail=0.0, burst=0.0, fountain=0.0, slot=0.0, crack=0.0,
            heap=0.0)


def pose(base=None, **kw):
    P = {k: (dict(v) if isinstance(v, dict) else v) for k, v in (base or BASE).items()}
    for k, v in kw.items():
        if isinstance(v, dict) and isinstance(P.get(k), dict):
            P[k] = {**P[k], **v}
        else:
            P[k] = v
    return P


def legs_all(fs, fo, bs, bo):
    return {"FL": (fs, fo), "FR": (fs, fo), "BL": (bs, bo), "BR": (bs, bo)}


POSES = {
    "stand": pose(),
    "combat": pose(lift=-0.15, pitch=6.0, head=(10.0, 0.0, 0.0), legs=legs_all(-6, 12, 8, 7), jaw=6.0),
    "sleep": pose(lift=-1.75, pitch=3.0, head=(14.0, 8.0, 4.0), legs=legs_all(-82, 8, 84, 8), lid=1.0,
                  ears={1: 0.6, -1: 0.6}),
    "ram": pose(lift=-0.2, pitch=8.0, head=(8.0, 0.0, 0.0), legs=legs_all(-14, 16, 14, 6), jaw=26.0, burst=0.5),
    "hail": pose(lift=0.0, pitch=-38.0, head=(-14.0, 0.0, 0.0), legs=legs_all(-48, 12, 0, 8), jaw=26.0,
                 fountain=0.6),
    "defeat": pose(lift=-1.6, pitch=5.0, roll=7.0, head=(22.0, -14.0, -10.0), legs=legs_all(-30, 58, 30, 58),
                   jaw=14.0, tongue=1.0, ears={1: 1.0, -1: 1.0}, dizzy=1.0, crack=1.0, heap=1.0),
}


def skeleton(P):
    M = {"body": T((0, 0, P["lift"])) @ about(PG.HIP, R("X", P["pitch"]) @ R("Y", P["roll"]))}
    hp, hy, hr = P["head"]
    M["head"] = M["body"] @ about(PG.NECK, R("Z", hy) @ R("X", hp) @ R("Y", hr))
    for s in S2:
        fs, fo = P["legs"]["F" + side(s)]
        bs, bo = P["legs"]["B" + side(s)]
        M[("F", s)] = M["body"] @ about((s * PG.LEG_XF, PG.SHOULDER_Y, PG.LEG_TOP), R("X", fs) @ R("Y", -s * fo))
        M[("B", s)] = M["body"] @ about((s * PG.LEG_XB, PG.HIP_Y, PG.LEG_TOP),
                                        R("Y", -P["roll"]) @ R("X", -P["pitch"]) @ R("X", bs) @ R("Y", -s * bo))
    return M


def slot_world(M):
    yc = (PG.BANDS[0] + PG.BANDS[1]) / 2
    wx, wz, _ = PG.slice_at(yc)
    top = PG.BODY_Z + (wz + 0.16) * math.sin(math.radians(86))
    return V((0, yc, top + 0.08)), M["body"]


COIN_REST = [V((0.3 * (i % 3 - 1), 0.5, 4.6 - 0.25 * (i // 3))) for i in range(COINS)]  # в теле под щелью
BURST = [(0.5, -0.4, 1.6), (-0.7, 0.3, 2.4), (0.3, 0.8, 3.2), (-0.2, -0.2, 4.0), (0.9, 0.2, 2.0), (-0.9, -0.5, 2.8)]


def frames(P):
    """Система каждой части в позе P (геометрия части строится в системе покоя)."""
    M = skeleton(P)
    F = {"Body": M["body"], "Head": M["head"]}
    F["Jaw"] = M["head"] @ about(JAW_PIV, R("X", P["jaw"]))
    F["Tongue"] = F["Jaw"] @ T((0, HIDE * (1 - P["tongue"]), 0))
    for s in S2:
        d = P["ears"][s]
        F["Ear" + side(s)] = M["head"] @ about(EAR_BASE[s], R("Y", s * 35 * d) @ R("X", 40 * d))
        F["Lid" + side(s)] = M["head"] @ T((0, HIDE * (1 - P["lid"]), 0))
        F["Dizzy" + side(s)] = M["head"] @ T((0, HIDE * (1 - P["dizzy"]), 0))
        F["LegF" + side(s)] = M[("F", s)]
        F["LegB" + side(s)] = M[("B", s)]
    F["Tail"] = M["body"] @ about(TAIL_BASE, R("Z", P["tail"]))
    sc, mb = slot_world(M)
    F["SlotCoin"] = mb @ T((0, 0, 0.35 * P["slot"]))
    sw = mb @ sc
    for i in range(COINS):
        b, f = P["burst"], P["fountain"]
        if b > 1e-4:  # «Таран»: дугой вверх-назад из щели
            dx, dy, dz = BURST[i]
            tgt = sw + V((dx * b, dy * b, dz * math.sin(math.pi * min(b, 1.0) * 0.9)))
        elif f > 1e-4:  # «Монетный град»: фонтан вверх в мировых осях
            ang = math.radians(i * 60 + 15)
            tgt = sw + V((1.9 * math.sin(ang) * f, 1.2 * f + 0.8 * math.cos(ang) * f, 1.2 * f + 4.2 * f - 1.3 * f * f))
        else:
            F[f"Coin{i + 1}"] = mb
            continue
        F[f"Coin{i + 1}"] = T(tgt) @ R("Z", 40 * i * (b + f)) @ R("X", 70 * (b + f)) @ T(-COIN_REST[i])
    F["Cracks"] = M["body"] @ T((-0.55 * (1 - P["crack"]), 0, -0.55 * (1 - P["crack"])))  # в покое — внутрь тела
    F["Heap"] = T((0, 0, -3.0 * (1 - P["heap"])))
    return F


REST_F = None
PIVOTS = {}


def rest_frames():
    global REST_F
    if REST_F is None:
        REST_F = frames(POSES["stand"])
        pivots()
    return REST_F


def pivots():
    F = REST_F
    PIVOTS["Body"] = PG.HIP.copy()
    PIVOTS["Head"] = PG.NECK.copy()
    PIVOTS["Jaw"] = JAW_PIV.copy()
    PIVOTS["Tongue"] = TONGUE_PIV.copy()
    for s in S2:
        PIVOTS["Ear" + side(s)] = EAR_BASE[s].copy()
        PIVOTS["Lid" + side(s)] = V((s * 0.95, -6.4, HC.z + 2.6))
        PIVOTS["Dizzy" + side(s)] = V((s * 0.95, -6.4, HC.z + 2.6))
        PIVOTS["LegF" + side(s)] = V((s * PG.LEG_XF, PG.SHOULDER_Y, PG.LEG_TOP))
        PIVOTS["LegB" + side(s)] = V((s * PG.LEG_XB, PG.HIP_Y, PG.LEG_TOP))
    PIVOTS["Tail"] = TAIL_BASE.copy()
    sc, _ = slot_world(skeleton(POSES["stand"]))
    PIVOTS["SlotCoin"] = sc.copy()
    for i in range(COINS):
        PIVOTS[f"Coin{i + 1}"] = COIN_REST[i].copy()
    PIVOTS["Cracks"] = V((3.0, 0.6, PG.BODY_Z))
    PIVOTS["Heap"] = V((5.2, 0.2, -3.0))
    return PIVOTS


def pose_world(P):
    rf = rest_frames()
    F = frames(P)
    return {n: F[n] @ rf[n].inverted() for n in RIG_TREE}


def transforms(P):
    """Transform каждого сустава относительно покоя (Motor6D: деталь = родитель · C0 · Transform · C1⁻¹)."""
    W = pose_world(P)
    out = {}
    for n, (par, _) in RIG_TREE.items():
        pv = PIVOTS[n]
        Wn = W[n] @ T(pv)
        if par is None:
            L, Lr = Wn, T(pv)
        else:
            L = (W[par] @ T(PIVOTS[par])).inverted() @ Wn
            Lr = T(pv - PIVOTS[par])
        X = Lr.inverted() @ L
        out[n] = (X.to_3x3(), X.translation.copy())
    return out


# ── Геометрия покоя ───────────────────────────────────────────────────────────────────────────────────────────
def build():
    """Модель в покое: части по группам (art.face_groups), формы — копилка v2 и крупные глаза с белком."""
    F = rest_frames()
    P = POSES["stand"]
    M = {"body": F["Body"], "head": F["Head"]}
    for s in S2:
        M[("F", s)] = F["LegF" + side(s)]
        M[("B", s)] = F["LegB" + side(s)]
    a = PG.new_art("Boss7Piggy")
    a.paint("lidP", PG.PALETTE["pig"][0], rings=False)
    top = PG.body(a, M, dict(P, mouth="grin"))  # тело, обручи, седло, щель, наплечники, хвост (группа Tail)
    head(a, F)
    for s in S2:
        PG.leg(a, M, s, True)
        PG.leg(a, M, s, False)
    a.transform, a.group = F["SlotCoin"], "SlotCoin"
    sc, _ = slot_world(skeleton(P))
    PG.coin(a, sc, (0, -1, 0), r=0.72, th=0.16)
    for i in range(COINS):
        a.transform, a.group = F[f"Coin{i + 1}"], f"Coin{i + 1}"
        PG.coin(a, COIN_REST[i], (0, -1, 0.3), r=0.42, th=0.12, spin=30 * i)
    cracks(a, F)
    heap(a, F)
    a.transform, a.group = None, None
    return a, top


def head(a, F):
    a.transform, a.group = F["Head"], "Head"
    tiers = PG.round_z(a, "pig", tuple(HC), PG.HEAD_R[0], PG.HEAD_R[1], PG.HEAD_R[2], PG.head_prof, 8)
    sz = HC.z + 1.3
    fy = PG.front_y(tiers, 0, sz)
    sm = T((0, 0, sz))
    a.prism("pigD", PG.ring(0, 0, 1.55, 1.18), fy - 0.15, fy + 0.4, axis="y", bevel=0, matrix=sm)
    a.prism("snout", PG.ring(0, 0, 1.45, 1.1), fy - 1.0, fy + 0.3, axis="y", bevel=0, matrix=sm)
    a.frame("snout", PG.ring(0, 0, 1.47, 1.12), 0.2, fy - 1.12, fy - 0.95, axis="y", bevel=0, matrix=sm)
    for s in S2:
        a.prism("nostril", PG.ring(s * 0.52, 0.0, 0.25, 0.4, 12), fy - 1.02, fy - 0.9, axis="y", bevel=0, matrix=sm)
        a.frame("snoutD", PG.ring(s * 0.52, 0.0, 0.36, 0.52, 12), 0.11, fy - 1.1, fy - 0.96, axis="y", bevel=0,
                matrix=sm)
    ez = HC.z + 2.62
    for s in S2:  # глаза крупнее (+26 %), белок виден: веко злое, но открывает белок
        x = s * 1.0
        n = V((s * 0.3, -1, 0.05))
        p = V((x, PG.front_y(tiers, x, ez) + 0.03, ez))
        A.eye(a, p, EYE_R, normal=n, mood="angry", side=s, skin_key="pig", brow_key="brow", look=(0.0, -0.15),
              lid=0.2, brow_tilt=28, brow_lift=0.04, h=1.08, pupil=0.42)
        # веко (прикрывает глаз во сне): в покое спрятано в голове, выезжает вперёд
        a.transform, a.group = F["Lid" + side(s)], "Lid" + side(s)
        m = T(p) @ A.facing(n)
        a.box("lidP", -EYE_R * 1.15, EYE_R * 1.15, -0.1, 0.08, -EYE_R * 1.2, EYE_R * 1.2, bevel=0, matrix=m)
        a.box("dark", -EYE_R * 1.0, EYE_R * 1.0, -0.13, -0.09, -0.05, 0.04, bevel=0, matrix=m)  # ресницы
        # глаза-крестики (поражение): тоже спрятаны в голове
        a.transform, a.group = F["Dizzy" + side(s)], "Dizzy" + side(s)
        a.box("white", -EYE_R, EYE_R, -0.08, 0.06, -EYE_R, EYE_R, bevel=0, matrix=m)
        for ang in (45, -45):
            a.box("dark", -EYE_R * 1.15, EYE_R * 1.15, -0.13, -0.07, -0.09, 0.09, bevel=0, matrix=m @ R("Y", ang))
        a.transform, a.group = F["Head"], "Head"
    fz = HC.z + 3.15
    fyy = PG.front_y(tiers, 0, fz)
    mf = T((0, fyy + 0.12, fz)) @ R("X", 34)
    a.box("steel", -1.2, 1.2, -0.2, 0.25, -0.42, 0.42, bevel=0.03, matrix=mf)
    a.box("steelL", -1.25, 1.25, -0.24, 0.0, -0.48, -0.3, bevel=0, matrix=mf)
    for x in (-0.8, 0.0, 0.8):
        PG.stud(a, "gold", (mf @ V((x, -0.2, 0.08))), mf.to_3x3() @ V((0, -1, 0)), s=0.11, h=0.08)
    jz = HC.z + 0.02
    jy = PG.front_y(tiers, 0, jz + 0.3)
    for sx in S2:  # уголки рта — ухмылка
        x0, x1 = sx * 1.4, sx * 1.75
        PG.taper(a, "mouth", (x0, PG.front_y(tiers, x0, jz + 0.42) - 0.02, jz + 0.4),
                 (x1, PG.front_y(tiers, x1, jz + 0.66) - 0.02, jz + 0.66), 0.1, 0.09, 0.1, 0.09, up=(0, -1, 0))
    a.box("mouth", -1.25, 1.25, jy - 0.05, jy + 0.9, jz + 0.25, jz + 0.85, bevel=0)  # глотка (видна, когда пасть открыта)
    a.transform, a.group = F["Jaw"], "Jaw"
    a.prism("pig", PG.ring(0, 0, 1.6, 0.42), jy - 0.4, jy + 1.4, axis="y", bevel=0, matrix=T((0, 0, jz)))
    a.box("mouth", -1.35, 1.35, jy - 0.3, jy + 0.9, jz + 0.3, jz + 0.4, bevel=0)
    a.box("tongue", -0.65, 0.65, jy - 0.1, jy + 0.8, jz + 0.34, jz + 0.46, bevel=0)
    for sx in S2:
        PG.K.KEY = "tusk"
        b = V((sx * 1.52, jy - 0.15, jz + 0.2))
        PG.K.taper(a, b, b + V((sx * 0.1, -0.1, 0.8)), 0.28, 0.14, 0.26, 0.13, up=(0, -1, 0), cut=0.2)
    a.transform, a.group = F["Tongue"], "Tongue"  # язык набок (поражение): спрятан в пасти
    PG.taper(a, "tongue", (0.45, jy + 0.1, jz + 0.42), (0.95, jy - 0.6, jz - 0.35), 0.5, 0.42, 0.13, 0.11)
    for s in S2:
        a.transform, a.group = F["Ear" + side(s)], "Ear" + side(s)
        base = EAR_BASE[s]
        p1 = base + V((s * 0.6, -0.1, 0.9))
        p2 = p1 + V((s * 0.45, -0.6, 0.3))
        tip = p2 + V((s * 0.15, -0.55, -0.4))
        PG.chain(a, "pig", [base, p1, p2, tip], [1.9, 1.6, 1.05, 0.26], [0.36, 0.32, 0.27, 0.15], up=(0, -1, 0.5),
                 overlap=0.4)
        n = V((0, -0.16, 0.06))
        PG.chain(a, "pigD", [base + n, p1 + n, p2 + n, tip + n * 0.6], [1.25, 1.05, 0.68, 0.12], [0.08] * 4,
                 up=(0, -1, 0.5), overlap=0.3)
    a.transform, a.group = F["Head"], "Head"


def cracks(a, F):
    """Трещины и пролом на правом (+x) боку и по спине; в покое утоплены в тело на HIDE."""
    a.transform, a.group = F["Cracks"], "Cracks"
    wx, wz, c = PG.slice_at(0.4)
    for sgn, pts in ((1, [(-1.2, 4.6, 1.5), (-0.6, 3.6, 1.0), (0.1, 4.0, 0.5), (0.8, 3.2, 0.0), (1.6, 3.7, -0.5)]),
                     (1, [(-0.9, 2.0, 0.4), (-0.3, 2.5, -0.1), (0.3, 1.9, -0.5)]),
                     (1, [(1.4, 4.2, 1.2), (1.9, 3.5, 0.8), (2.4, 4.0, 0.4)])):
        q = []
        for y, h, dz in pts:
            d = V((sgn * 1.0, 0, h / 4.6 * 0.9)).normalized()
            p = PG.hull_point(wx, wz, c, d) + V((0, y, PG.BODY_Z + dz))
            q.append(p + d * 0.03)
        PG.chain(a, "crack", q, [0.16] * len(q), [0.12] * len(q), up=(sgn, 0, 0), overlap=0.3)
    hole = PG.hull_point(wx, wz, c, V((1, 0, -0.15)).normalized()) + V((0, 0.6, PG.BODY_Z - 0.4))
    a.prism("slot", S.octagon(-0.7, 0.7, -0.55, 0.5, 0.25), -0.04, 0.3, axis="y", bevel=0,
            matrix=T(hole) @ A.facing((1, 0, -0.15)))


def heap(a, F):
    """Горка монет поражения у пролома (в покое — под землёй)."""
    a.transform, a.group = F["Heap"], "Heap"
    base = V((5.2, 0.2, 0.0))  # на земле; в покое система горки опущена на 3 под землю
    a.prism("coin", S.octagon(base.x - 1.5, base.x + 1.5, base.y - 1.3, base.y + 1.3, 0.6), base.z + 0.012,
            base.z + 0.3, bevel=0)
    a.prism("coinL", S.octagon(base.x - 0.95, base.x + 0.95, base.y - 0.8, base.y + 0.8, 0.4), base.z + 0.28,
            base.z + 0.55, bevel=0)
    for i, (dx, dy, dz) in enumerate(((0.7, 0.4, 0.4), (-0.6, 0.5, 0.42), (0.2, -0.7, 0.38), (0.45, 0.15, 0.62),
                                      (-0.1, 0.3, 0.7))):
        PG.coin(a, base + V((dx, dy, dz)), (0.25 * math.sin(i * 1.7), 0.25 * math.cos(i * 2.3), 1), r=0.42, th=0.12,
                spin=i * 31)


# ── Разрез на части, проверки, кадры ──────────────────────────────────────────────────────────────────────────
def split(obj, art, col):
    import creature_kit as CK  # noqa: E402

    art.rig = {n: (par, tuple(PIVOTS[n])) for n, (par, _) in RIG_TREE.items()}
    return CK.split_keep(obj, art, col)


def place(parts, P, turn=None):
    W = pose_world(P)
    for n, o in parts.items():
        o.matrix_world = (turn or Matrix()) @ W[n] @ T(PIVOTS[n])
    bpy.context.view_layer.update()


SAMPLE = {}  # точки покоя каждой части (мир) — для проверки земли и посадки поз


def sample_parts(parts):
    for n, o in parts.items():
        SAMPLE[n] = [o.matrix_world @ v.co for v in o.data.vertices][::2]


def check_pose(P):
    """Нижняя точка позы — без горки монет, летящих монет, спрятанных век, крестиков и языка (они внутри тела)."""
    W = pose_world(P)
    low = {}
    for n, pts in SAMPLE.items():
        if n in ("Heap", "Cracks") or n.startswith(("Coin", "Lid", "Dizzy")):
            continue
        if n == "Tongue" and P["tongue"] < 0.5:
            continue
        low[n] = min((W[n] @ p).z for p in pts)
    n = min(low, key=low.get)
    return n, round(low[n], 3)


def ground(P):
    """Посадить позу на землю: самая низкая точка тела, ног и головы — ровно на z = 0 (подъём lift)."""
    for _ in range(2):
        n, z = check_pose(P)
        P["lift"] -= z
    return P


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    repo, out = os.path.abspath(argv[0]), os.path.abspath(argv[1])
    mode = argv[2] if len(argv) > 2 else ""
    os.makedirs(out, exist_ok=True)
    sys.path.insert(0, os.path.join(HERE, "concepts510"))
    import ck  # noqa: E402
    from joint_check import check_joints  # noqa: E402

    col = ck.reset_scene()
    rest_frames()
    art, _ = build()
    obj = art.build(col)
    PG_mat = obj.data.materials
    for mat in PG_mat:
        k = mat.name.rsplit("_", 1)[-1]
        b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b is not None and k.startswith(("gold", "coin")):
            b.inputs["Metallic"].default_value, b.inputs["Roughness"].default_value = 0.5, 0.3
        elif b is not None and k.startswith("steel"):
            b.inputs["Metallic"].default_value, b.inputs["Roughness"].default_value = 0.35, 0.38
    stats = dict(art.stats)
    stats["coplanar"] = len(stats["coplanar"])
    parts = split(obj, art, col)
    bpy.context.view_layer.update()
    sample_parts(parts)
    for P in POSES.values():
        ground(P)
    tris = {n: sum(len(p.vertices) - 2 for p in o.data.polygons) for n, o in parts.items()}
    rig = {n: (par, tuple(PIVOTS[n])) for n, (par, _) in RIG_TREE.items()}
    joints = check_joints({n: o for n, o in parts.items() if not n.startswith(("Coin", "Heap", "Cracks", "Lid",
                                                                                "Dizzy", "Tongue"))},
                          {n: rig[n] for n in rig if not n.startswith(("Coin", "Heap", "Cracks", "Lid", "Dizzy",
                                                                      "Tongue"))}, gap=0.05)
    report = {"tris_total": sum(tris.values()), "tris_by_part": tris, "parts": len(parts), "scale": SCALE,
              "eye_radius": EYE_R, "build": stats, "joint_issues_rest": joints, "poses": {}}
    cam = ck.studio(col, size=1.5, bg=(0.7, 0.76, 0.86))
    bpy.context.scene.view_settings.exposure = -0.3
    for name, P in POSES.items():
        place(parts, P)
        report["poses"][name] = {"lowest": check_pose(P), "lift": round(P["lift"], 3)}
        if mode == "check":
            continue
        for label, ang in (("34", -35), ("front", 0)) if name != "hail" else (("34", -62), ("front", 0)):
            place(parts, P, R("Z", ang))
            ck.shot(cam, os.path.join(out, f"game_{name}_{label}.png"), (0, -26.0, 9.5), (0, 0, 3.2), 55, (900, 900))
        if name == "stand":
            place(parts, P)
            hcw = pose_world(P)["Head"] @ V((0, -4.6, HC.z + 2.0))
            ck.shot(cam, os.path.join(out, "game_face.png"), hcw + V((0, -10.0, 1.4)), hcw, 55, (900, 900))
            ck.shot(cam, os.path.join(out, "game_far.png"), (0, -60.0, 14.0), (0, 0, 3.5), 55, (900, 900))
    with open(os.path.join(out, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("REPORT", json.dumps({k: report[k] for k in ("tris_total", "parts", "joint_issues_rest", "poses")},
                               ensure_ascii=False), flush=True)
    if mode == "export":
        import creature_kit as CK  # noqa: E402,F811

        mdir = os.path.join(repo, "assets", "models", "art", "boss7")
        os.makedirs(mdir, exist_ok=True)
        place(parts, POSES["stand"])
        S.export_fbx([parts[n] for n in RIG_TREE], os.path.join(mdir, "Boss7_Piggy.fbx"))
        CK.rig_json("Boss7_Piggy", art, parts, os.path.join(mdir, "Boss7_Piggy.rig.json"))


if __name__ == "__main__":
    main()
