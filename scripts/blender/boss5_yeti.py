"""Босс 5 «Йети-коллекционер» (Ледник) — игровая модель: части на Motor6D, три карты, игровые позы (шаг 2 D64).

Формы — утверждённый концепт scripts/blender/boss5/yeti.py (листы assets/concepts/bosses_5_10/boss5_v2/). Отличия
игровой модели от концепта:
- модель собрана в покое (поза «stand») и разрезана на 30 частей с точками вращения (D18): Torso (корень) → Head →
  Jaw, EyelidL/R, BrowL/R, Monocle; руки UpperArm → ForeArm → Hand → Fingers (кулак — сгиб пальцев), ноги Thigh →
  Shin → Foot; глыба Block (лёд) с BlockFrame (рама-носилка, обвязки, лямки, нижние уголки — непрозрачные), верхушка
  BlockTop (лёд) с BlockTopFrame (верхняя обвязка и уголки) — в поражении откидывается; 4 простых экспоната внутри
  (D64: не больше 4, лёгкие) — ExCup, ExGem, ExLovibum, ExCritter, свои части (в поражении подпрыгивают из глыбы);
- выражения — сдвигом и поворотом частей: веки опускаются на глаза (сон), брови поворачиваются, челюсть открывается,
  монокль слетает и висит на цепочке; «Z» сна и пузырь из носа — только на концепт-листе;
- лёд Block и BlockTop в игре — MeshPart с прозрачностью (Glass в игре непрозрачен, BUGS.md), экспонаты видны.
Карты 1024² (D39 v2, как у существ: запекание ×4, выравнивание островов): Head (голова, челюсть, веки, брови,
монокль), Body (туловище, глыба, экспонаты), Limbs (руки и ноги).

Позы задаются параметрами скелета концепта (таз, наклоны, голова, руки, ноги или цели стоп, пальцы, лицо, глыба).
pose_world(P) → матрица каждой части в мире (геометрия покоя → поза); transforms(P) → Transform суставов относительно
покоя в стиле rig.json Сфинкса. Ноги — обратная кинематика по целям стоп (стопа ровно на земле).

Пишет assets/models/Boss5_Yeti.{fbx,blend,rig.json,colors.json}, карты assets/textures/art/Boss5_Yeti{Head,Body,
Limbs}_{color,normal}.png, кадры и report.json — в папку кадров.
Режимы: (пусто) — запекание, экспорт, кадры; quick — материалы сборки, без экспорта; check — только сборка и числа.
Запуск: blender --background --factory-startup --python scripts/blender/boss5_yeti.py -- <репо> <кадры> [quick|check]
Подключается и как модуль (boss5_yeti_anim.py): тогда ничего не собирает.
Зависит от art_style.py, dragon10/v4_kit.py, boss5/yeti.py (контуры и помощники).
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "dragon10"), os.path.join(HERE, "boss5")):
    if p not in sys.path:
        sys.path.insert(0, p)
import art_style as S  # noqa: E402
import v4_kit as K  # noqa: E402
import yeti as C5  # noqa: E402  (концепт: контуры, помощники, палитра)

V = Vector
S2 = (1, -1)
SCALE = 2.03  # стадов на единицу модели: рост в стойке 24 стада (концепт-лист)
HEAD_SCALE = C5.HEAD_SCALE
SPLIT = 4.6  # высота шва глыбы: выше — откидывающаяся верхушка
AX = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))  # оси Roblox: (x, y, z) Blender → (x, z, −y)
R, T, key, slab, half, tufts = C5.R, C5.T, C5.key, C5.slab, C5.half, C5.tufts
SHOULDER, NECK, HIP = C5.SHOULDER, C5.NECK, C5.HIP
UPPER, FORE, THIGH, SHIN = C5.UPPER, C5.FORE, C5.THIGH, C5.SHIN
ANKLE_H = 0.42  # от сустава стопы до подошвы
KNUCKLE = V((0, -0.05, -0.7))  # сгиб пальцев в системе кисти
JAW_HINGE = V((0, -0.6, 0.45))  # в системе головы (до HEAD_SCALE)
LID_DROP = 0.42  # веко опускается на столько (до HEAD_SCALE)
MONO_C = V((-0.52, -1.46, 1.43))
BLOCK_PIV = V((0, 1.05, 1.6))  # в системе торса
BLOCK_TILT = -8.0  # глыба на спине стоит ровнее торса (концепт: половина наклона стойки 16°)
TOP_HINGE = V((0.0, 3.05, SPLIT))  # задний край шва — петля верхушки (в системе глыбы)
EXHIBITS = {"ExCup": V((-1.12, 2.0, 5.75)), "ExGem": V((1.2, 2.0, 6.2)), "ExLovibum": V((1.1, 2.0, 3.7)),
            "ExCritter": V((-1.05, 2.0, 2.45))}  # крупные, у краёв глыбы: спереди видны по бокам головы, сбоку — все  # центры (точки вращения) в системе глыбы

PALETTE = dict(C5.PALETTE)
for k in ("iceBlock", "iceD", "iceE"):
    PALETTE[k] = PALETTE[k]

# ── Скелет игры: часть → (родитель, карта) — точки вращения считаются из позы покоя ────────────────────────────
RIG_TREE = {"Torso": (None, "Body"), "Head": ("Torso", "Head"), "Jaw": ("Head", "Head"),
            "EyelidL": ("Head", "Head"), "EyelidR": ("Head", "Head"), "BrowL": ("Head", "Head"),
            "BrowR": ("Head", "Head"), "Monocle": ("Head", "Head")}
for _s in "LR":
    RIG_TREE.update({f"UpperArm{_s}": ("Torso", "Limbs"), f"ForeArm{_s}": (f"UpperArm{_s}", "Limbs"),
                     f"Hand{_s}": (f"ForeArm{_s}", "Limbs"), f"Fingers{_s}": (f"Hand{_s}", "Limbs"),
                     f"Thigh{_s}": ("Torso", "Limbs"), f"Shin{_s}": (f"Thigh{_s}", "Limbs"),
                     f"Foot{_s}": (f"Shin{_s}", "Limbs")})
RIG_TREE.update({"Block": ("Torso", "Body"), "BlockFrame": ("Block", "Body"), "BlockTop": ("Block", "Body"),
                 "BlockTopFrame": ("BlockTop", "Body"), "ExCup": ("Block", "Body"), "ExGem": ("Block", "Body"),
                 "ExLovibum": ("Block", "Body"), "ExCritter": ("Block", "Body")})
MAPS = {m: tuple(p for p, (_, mm) in RIG_TREE.items() if mm == m) for m in ("Head", "Body", "Limbs")}
HEAD_PARTS = ["Head", "Jaw", "EyelidL", "EyelidR", "BrowL", "BrowR", "Monocle"]
ICE_PARTS = ["Block", "BlockTop"]


def side(s):
    return "L" if s > 0 else "R"


# ── Позы: параметры ──────────────────────────────────────────────────────────────────────────────────────────
def base_pose():
    """Поза покоя — «stand» концепта с ровными бровями и открытыми глазами (в ней собирается модель)."""
    return {"pelvis": V((0.0, 0.0, 2.3)), "pitch": 0.0, "torso": 16.0, "head": (-14.0, 0.0, 0.0),
            "arm": {1: (34.0, 12.0, 26.0, 10.0), -1: (28.0, 14.0, 22.0, 8.0)},
            "leg": {1: (12.0, 26.0, 0.0), -1: (12.0, 26.0, 0.0)}, "curl": {1: 0.0, -1: 0.0},
            "jaw": 0.0, "lid": {1: 0.0, -1: 0.0}, "brow": {1: (0.0, 0.0), -1: (0.0, 0.0)}, "mono": 0.0,
            "block": None, "top": (0.0, 0.0), "ex": {}, "roll": 0.0}


def _ground_offset():
    """Сдвиг таза по высоте, чтобы подошвы стойки стояли на z = 0."""
    P = base_pose()
    M = skeleton(P, ground=False)
    return -min((M[("an", s)].translation.z - ANKLE_H) for s in S2)


def skeleton(P, ground=True):
    """Матрицы суставов концепта (как C5.skeleton), z земли = 0."""
    M = {}
    pel = V(P["pelvis"]) + (V((0, 0, GROUND)) if ground else V())
    M["pelvis"] = T(pel) @ R("X", P["pitch"])
    M["torso"] = M["pelvis"] @ R("X", P["torso"]) @ R("Y", P.get("roll", 0.0))  # roll > 0 — наклон к +x
    hp, hy, hr = P["head"]
    M["head"] = M["torso"] @ T(NECK) @ R("Z", hy) @ R("X", hp) @ R("Y", hr)
    for s in S2:
        sw, ab, el, wr, yaw = (tuple(P["arm"][s]) + (0.0,))[:5]  # yaw — поворот руки внутрь (к середине груди)
        M[("sh", s)] = (M["torso"] @ T(V((s * SHOULDER.x, SHOULDER.y, SHOULDER.z))) @ R("Z", -s * yaw)
                        @ R("Y", -s * ab) @ R("X", -sw))
        M[("el", s)] = M[("sh", s)] @ T((0, 0, -UPPER)) @ R("X", -el)
        M[("wr", s)] = M[("el", s)] @ T((0, 0, -FORE)) @ R("X", -wr)
        hf, kn, an = P["leg"][s]
        M[("hip", s)] = M["pelvis"] @ T(V((s * HIP.x, HIP.y, HIP.z))) @ R("X", -hf)
        M[("kn", s)] = M[("hip", s)] @ T((0, 0, -THIGH)) @ R("X", kn)
        M[("an", s)] = M[("kn", s)] @ T((0, 0, -SHIN)) @ R("X", hf - kn - P["pitch"] + an)
    return M


GROUND = 0.0
GROUND = _ground_offset()


def leg_ik(P, s, ankle_world, an=0.0):
    """Углы ноги s, чтобы сустав стопы встал в ankle_world (x не важен: нога сгибается в плоскости yz таза);
    an — наклон стопы (0 — ровно). Возвращает (hf, kn, an) и недотяг (0 — достал)."""
    pel = V(P["pelvis"]) + V((0, 0, GROUND))
    Mp = T(pel) @ R("X", P["pitch"])
    a = Mp.inverted() @ V(ankle_world)
    hip = V((s * HIP.x, HIP.y, HIP.z))
    dy, dz = a.y - hip.y, a.z - hip.z
    D = math.hypot(dy, dz)
    reach = THIGH + SHIN - 1e-4
    short = max(0.0, D - reach)
    D = min(D, reach)
    D = max(D, abs(THIGH - SHIN) + 1e-4)
    phi = math.atan2(-dy, -dz)  # угол от «вниз» к «вперёд» (−y)
    al = math.acos(max(-1, min(1, (THIGH ** 2 + D ** 2 - SHIN ** 2) / (2 * THIGH * D))))
    be = math.acos(max(-1, min(1, (SHIN ** 2 + D ** 2 - THIGH ** 2) / (2 * SHIN * D))))
    hf = math.degrees(phi + al)
    kn = math.degrees(al + be)
    return (hf, kn, an), short


def solve(P):
    """Поза с целями стоп (P["feet"] = {s: (y, подъём над землёй, наклон стопы)}) → углы ног; x стопы — под бедром."""
    P = dict(P)
    feet = P.get("feet")
    if feet:
        legs = dict(P["leg"])
        for s, (y, lift, an) in feet.items():
            legs[s], _ = leg_ik(P, s, (s * HIP.x, y, ANKLE_H + lift), an)
        P["leg"] = legs
    return P


def block_attached(M):
    """Глыба на спине: матрица системы глыбы (в концепте — система торса с поворотом у основания)."""
    return M["torso"] @ T(BLOCK_PIV) @ R("X", BLOCK_TILT) @ T(-BLOCK_PIV)


def frames(P):
    """Система каждой части в позе P: геометрия части строится в этой системе (в покое — base_pose)."""
    P = solve(P)
    M = skeleton(P)
    F = {"Torso": M["torso"]}
    hs = M["head"] @ Matrix.Scale(HEAD_SCALE, 4)
    F["Head"] = hs
    F["Jaw"] = hs @ T(JAW_HINGE) @ R("X", P["jaw"]) @ T(-JAW_HINGE)
    for s in S2:
        F[f"Eyelid{side(s)}"] = hs @ T((0, 0, -LID_DROP * P["lid"][s]))
        ang, lift = P["brow"][s]
        c = V((s * 0.55, -1.3, 1.78))
        F[f"Brow{side(s)}"] = hs @ T((0, 0, lift)) @ T(c) @ R("Y", s * ang) @ T(-c)
        F[f"UpperArm{side(s)}"] = M[("sh", s)]
        F[f"ForeArm{side(s)}"] = M[("el", s)]
        F[f"Hand{side(s)}"] = M[("wr", s)]
        F[f"Fingers{side(s)}"] = M[("wr", s)] @ T(KNUCKLE) @ R("X", -110.0 * P["curl"][s]) @ T(-KNUCKLE)
        F[f"Thigh{side(s)}"] = M[("hip", s)]
        F[f"Shin{side(s)}"] = M[("kn", s)]
        F[f"Foot{side(s)}"] = M[("an", s)]
    on = T(MONO_C)
    off = T((-0.95, -1.5, 0.15)) @ R("X", -20) @ R("Z", 30)  # слетел: висит на цепочке у щеки
    F["Monocle"] = hs @ blend(on, off, P["mono"]) @ T(-MONO_C)
    Fb = block_attached(M) if P["block"] is None else P["block"]
    F["Block"] = F["BlockFrame"] = Fb
    ang, lift = P["top"]
    F["BlockTop"] = F["BlockTopFrame"] = Fb @ T((0, 0, lift)) @ T(TOP_HINGE) @ R("X", ang) @ T(-TOP_HINGE)
    for n, c in EXHIBITS.items():
        dx, dy, dz, rx = P["ex"].get(n, (0, 0, 0, 0))
        F[n] = Fb @ T(c + V((dx, dy, dz))) @ R("X", rx) @ T(-c)
    return F


def blend(a, b, k):
    """Смесь двух жёстких матриц: сдвиг — линейно, поворот — по дуге."""
    if k <= 0:
        return a.copy()
    if k >= 1:
        return b.copy()
    ta, qa, _ = a.decompose()
    tb, qb, _ = b.decompose()
    return T(ta.lerp(tb, k)) @ qa.slerp(qb, k).to_matrix().to_4x4()


REST_F = None
PIVOTS = {}


def rest_frames():
    global REST_F
    if REST_F is None:
        REST_F = frames(base_pose())
        pivots()
    return REST_F


def pivots():
    """Точки вращения частей в мире покоя (начала их систем; у экспонатов — центр, у век — над глазом)."""
    F = REST_F
    for n in RIG_TREE:
        PIVOTS[n] = F[n].translation.copy()
    # части с общей системой головы — свои точки (иначе вращение «вокруг шеи»)
    hs = F["Head"]
    PIVOTS["Jaw"] = hs @ JAW_HINGE
    for s in S2:
        PIVOTS[f"Eyelid{side(s)}"] = hs @ V((s * 0.52, -1.42, 1.84))
        PIVOTS[f"Brow{side(s)}"] = hs @ V((s * 0.55, -1.3, 1.78))
        PIVOTS[f"Fingers{side(s)}"] = F[f"Hand{side(s)}"] @ KNUCKLE
    PIVOTS["Monocle"] = hs @ MONO_C
    PIVOTS["BlockTop"] = PIVOTS["BlockTopFrame"] = F["Block"] @ TOP_HINGE
    PIVOTS["Block"] = PIVOTS["BlockFrame"] = F["Block"] @ V((0.0, 1.95, 1.6))  # середина основания глыбы
    for n, c in EXHIBITS.items():
        PIVOTS[n] = F["Block"] @ c
    return PIVOTS


def pose_world(P):
    """Матрица каждой части: геометрия покоя (в мире) → поза P."""
    rf = rest_frames()
    F = frames(P)
    return {n: F[n] @ rf[n].inverted() for n in RIG_TREE}


def transforms(P):
    """Transform каждого сустава относительно покоя (поворот 3×3 и сдвиг, в осях Blender, единицы модели) —
    как Motor6D: деталь = родитель · C0 · Transform · C1⁻¹, системы суставов в покое — без поворота."""
    W = pose_world(P)
    out = {}
    for n, (par, _) in RIG_TREE.items():
        pv = PIVOTS[n]
        Wn = W[n] @ T(pv)  # система сустава в позе
        if par is None:
            L = Wn
            Lr = T(pv)
        else:
            L = (W[par] @ T(PIVOTS[par])).inverted() @ Wn
            Lr = T(pv - PIVOTS[par])
        X = Lr.inverted() @ L
        out[n] = (X.to_3x3(), X.translation.copy())
    return out


# ── Игровые позы (имена как у боссов 1–4: их ждут BossAnim и рост полоски HP) ─────────────────────────────────
def pose(**kw):
    P = base_pose()
    for k, v in kw.items():
        if isinstance(v, dict) and isinstance(P.get(k), dict):
            P[k] = {**P[k], **v}
        else:
            P[k] = v
    return P


def stand_feet(y=0.25, spread=0.0, lift=0.0):
    return {1: (y, lift, 0.0), -1: (y - spread, lift, 0.0)}


BLOCK_BASE = V((0.0, 1.95, 1.6))  # середина основания глыбы в её системе


def block_world(pos, yaw=0.0, tilt_y=0.0):
    """Глыба в мире: середина основания в pos, поворот вокруг вертикали yaw и наклон вбок tilt_y."""
    return T(pos) @ R("Z", yaw) @ R("Y", tilt_y) @ T(-BLOCK_BASE)


def sleep_block():
    """Глыба снята и стоит на земле рядом (слева от Йети, к зрителю в 3/4 — видна): он спит, привалившись к ней."""
    return block_world((3.75, 0.9, 0.06), yaw=135.0)  # рама-носилка — от Йети и зрителя; уголки (−0.06) на земле


POSES = {
    "stand": pose(head=(-14, 0, 0), brow={1: (-16, 0), -1: (10, 0.12)}, feet=stand_feet(0.4)),
    "sleep": pose(pelvis=V((0, 0.35, 1.0)), torso=-8, roll=20, head=(18, 0, 22), lid={1: 1.0, -1: 1.0},
                  brow={1: (-4, -0.05), -1: (-4, -0.05)}, arm={1: (8, 48, 62, 20), -1: (16, 24, 46, 35)},
                  feet={1: (-1.5, 0.08, -18), -1: (-1.4, 0.08, -16)}, curl={1: 0.35, -1: 0.35}, block=sleep_block()),
    "alert": pose(pelvis=V((0, 0.35, 1.0)), torso=-4, roll=10, head=(-6, 0, -6),
                  arm={1: (8, 44, 58, 20), -1: (16, 24, 46, 35)},
                  feet={1: (-1.5, 0.08, -18), -1: (-1.4, 0.08, -16)}, curl={1: 0.35, -1: 0.35}, block=sleep_block(),
                  brow={1: (6, 0.08), -1: (6, 0.08)}),
    "combat": pose(pelvis=V((0, 0.1, 2.0)), torso=22, head=(-22, 0, 0), jaw=14, brow={1: (-24, 0), -1: (-24, 0)},
                   arm={1: (52, 26, 70, 10), -1: (52, 26, 70, 10)}, curl={1: 1.0, -1: 1.0},
                   feet={1: (-0.35, 0, 0), -1: (0.75, 0, 0)}),
    "combat2": pose(pelvis=V((0, 0.15, 1.95)), torso=24, head=(-18, 6, 0), jaw=10, brow={1: (-22, 0), -1: (-24, 0)},
                    arm={1: (58, 24, 76, 10), -1: (46, 28, 66, 10)}, curl={1: 1.0, -1: 1.0},
                    feet={1: (-0.3, 0, 0), -1: (0.8, 0, 0)}),
    "walkA": pose(pelvis=V((0, 0.1, 2.1)), torso=20, head=(-16, 0, 0), brow={1: (-12, 0), -1: (-12, 0)},
                  arm={1: (10, 14, 30, 5), -1: (60, 14, 40, 5)}, curl={1: 0.6, -1: 0.6},
                  feet={1: (-0.75, 0, 0), -1: (0.85, 0.0, 0)}),
    "walkB": pose(pelvis=V((0, 0.1, 2.1)), torso=20, head=(-16, 0, 0), brow={1: (-12, 0), -1: (-12, 0)},
                  arm={1: (60, 14, 40, 5), -1: (10, 14, 30, 5)}, curl={1: 0.6, -1: 0.6},
                  feet={1: (0.85, 0.0, 0), -1: (-0.75, 0, 0)}),
    "hit": pose(pelvis=V((0, 0.35, 2.05)), torso=6, head=(-30, -8, -8), jaw=18, lid={1: 0.45, -1: 0.45},
                brow={1: (14, 0.1), -1: (14, 0.1)}, arm={1: (20, 40, 50, 0), -1: (20, 40, 50, 0)},
                curl={1: 0.3, -1: 0.3}, feet={1: (0.1, 0, 0), -1: (0.6, 0, 0)}),
    "dizzy": pose(pelvis=V((0, 0.2, 1.0)), torso=-14, head=(-4, 14, 18), jaw=12, lid={1: 0.55, -1: 0.4},
                  brow={1: (16, 0.06), -1: (12, 0.06)}, mono=1.0, arm={1: (-8, 52, 14, -10), -1: (-14, 56, 20, -6)},
                  feet={1: (-1.5, 0.12, -25), -1: (-1.4, 0.12, -22)}, top=(-75, 0.4),
                  ex={"ExCup": (-0.4, -0.6, 1.6, 40), "ExGem": (0.5, -0.4, 1.2, -60)}),
    "bite": pose(pelvis=V((0, -0.2, 1.75)), torso=40, head=(-30, 0, 0), jaw=24, brow={1: (-26, 0), -1: (-26, 0)},
                 arm={1: (95, 10, 10, 0), -1: (30, 30, 60, 10)}, curl={1: 1.0, -1: 1.0},
                 feet={1: (-1.1, 0, 0), -1: (0.9, 0, 0)}),
    "swipe": pose(pelvis=V((0, -0.1, 1.9)), torso=30, head=(-26, 0, 0), jaw=26, brow={1: (-26, 0), -1: (-26, 0)},
                  arm={1: (80, 0, 22, 0, 46), -1: (80, 0, 22, 0, 46)}, curl={1: 0.0, -1: 0.0},  # ладони сведены
                  feet={1: (-0.5, 0, 0), -1: (0.6, 0, 0)}),
    "bark": pose(pelvis=V((0, 0.1, 2.3)), torso=4, head=(-34, 0, 0), jaw=28, brow={1: (-20, 0.05), -1: (-20, 0.05)},
                 arm={1: (20, 150, 30, 0), -1: (20, 150, 30, 0)}, curl={1: 1.0, -1: 1.0}, feet=stand_feet(0.3)),
    "bark2": pose(pelvis=V((0, 0.1, 2.25)), torso=6, head=(-24, 0, 0), jaw=22, brow={1: (-16, 0), -1: (-16, 0)},
                  arm={1: (60, 10, 100, 0), -1: (60, 10, 100, 0)}, curl={1: 1.0, -1: 1.0}, feet=stand_feet(0.3)),
}


# ── Геометрия (в покое) ──────────────────────────────────────────────────────────────────────────────────────
class GameArt(S.Art):
    """Art, который принимает только детали частей своей карты (одна сборка — одна карта)."""

    def __init__(self, name, allowed):
        super().__init__(name, ring_z0=3.0)
        self.allowed = set(allowed)
        self.ring = dict(S.RING, core=0.55)
        for k, (code, rings) in PALETTE.items():
            self.paint(k, code, rings=rings)
        self.bake_opts = {"ss": 4, "pack_margin": 0.003, "align": True, "project_angle": 66}

    def _add(self, bm, key_, planes, matrix):
        if self.group not in self.allowed:
            bm.free()
            return
        super()._add(bm, key_, planes, matrix)


def at(a, frame, group):
    a.transform, a.group = frame, group


def build_torso(a, F):
    at(a, F["Torso"], "Torso")
    C5.torso(a, F["Torso"])
    C5.harness(a, F["Torso"])
    a.group = "Torso"


def build_head(a, F):
    hs = F["Head"]
    at(a, hs, "Head")
    dome = [(1.05, 0.2), (1.15, 1.4), (0.8, 2.25), (0.0, 2.55), (-0.8, 2.4), (-1.1, 1.95), (-1.12, 0.3),
            (-0.6, -0.15), (0.6, -0.15)]
    key("fur")
    K.layered(a, dome, [(1.05, 1.0, 1.0), (1.32, 0.88, 0.9)], (0.0, 1.1))
    for p in ((0, 0.25, 2.45), (0.5, 0.5, 2.3), (-0.5, 0.5, 2.3), (0.0, 0.85, 2.15)):
        p = V(p)
        K.spike(a, p, p + V((p.x * 0.6, 0.5, 1.0 - abs(p.x) * 0.3)), 0.66)
    for i, t in enumerate(range(-140, 141, 28)):
        r = math.radians(t)
        p = V((1.22 * math.sin(r), -0.9, 1.05 + 1.02 * math.cos(r)))
        d = V((math.sin(r), -0.35, math.cos(r))).normalized()
        sz = 0.78 if i % 2 == 0 else 0.6
        K.spike(a, p, p + d * sz, sz * 0.75)
    key("skin")
    for s in S2:
        half(a, [(-0.9, 1.95), (-1.25, 1.86), (-1.33, 0.85), (-1.22, 0.45), (-0.9, 0.45)], 1.0, s, -12, 1.0)
    for s in S2:  # глаза открыты (в позах их закрывают веки)
        ex = s * 0.52
        key("neonEye")
        slab(a, [(-1.26, 1.66), (-1.36, 1.6), (-1.36, 1.24), (-1.26, 1.2)], ex - 0.31, ex + 0.31)
        key("pupil")
        slab(a, [(-1.36, 1.56), (-1.39, 1.54), (-1.39, 1.3), (-1.36, 1.28)], ex - s * 0.06 - 0.09, ex - s * 0.06 + 0.09)
        key("white")
        slab(a, [(-1.36, 1.6), (-1.385, 1.6), (-1.385, 1.54), (-1.36, 1.54)], ex + 0.12, ex + 0.22)
    key("skin")
    for s in S2:
        half(a, [(-1.2, 1.22), (-1.62, 1.12), (-1.7, 0.66), (-1.42, 0.52), (-1.15, 0.6)], 0.74, s, -10, 0.8)
    key("nose")
    slab(a, [(-1.6, 1.3), (-1.8, 1.2), (-1.84, 1.0), (-1.7, 0.9), (-1.6, 0.9)], -0.32, 0.32)
    for s in S2:
        a.box("dark", s * 0.16 - 0.08, s * 0.16 + 0.08, -1.88, -1.83, 0.96, 1.06, bevel=0)
    key("skinD")
    slab(a, [(-1.6, 0.66), (-1.72, 0.66), (-1.72, 0.58), (-1.6, 0.58)], -0.5, 0.5)
    key("mouth")  # полость рта — видна, когда челюсть открыта
    slab(a, [(-0.85, 0.62), (-1.58, 0.6), (-1.6, 0.05), (-0.85, 0.05)], -0.62, 0.62)
    slab(a, [(-1.6, 0.6), (-1.74, 0.6), (-1.74, 0.53), (-1.6, 0.53)], -0.58, 0.58)
    key("ivory")
    for s in S2:  # верхние клыки (за нижней челюстью, пока рот закрыт)
        K.spike(a, (s * 0.38, -1.58, 0.62), (s * 0.38, -1.62, 0.32), 0.17)
    # челюсть с языком, нижними зубами и бивнями
    at(a, F["Jaw"], "Jaw")
    key("tongue")
    slab(a, [(-0.9, 0.34), (-1.6, 0.36), (-1.62, 0.22), (-0.9, 0.2)], -0.36, 0.36)
    key("skin")
    for s in S2:
        half(a, [(-0.75, 0.6), (-1.86, 0.66), (-1.9, 0.2), (-1.5, -0.18), (-0.75, -0.12)], 0.68, s, -8, 0.25)
    for dx in (-0.42, -0.14, 0.14, 0.42):
        a.box("ivory", dx - 0.1, dx + 0.1, -1.86, -1.74, 0.62, 0.8, bevel=0.01)
    key("ivory")
    for s in S2:
        p0, p1, p2 = V((s * 0.62, -1.72, 0.5)), V((s * 0.74, -1.84, 0.98)), V((s * 0.92, -1.86, 1.38))
        K.chain(a, [p0, p1], [0.3, 0.24], up=(0, -1, 0), cut=0.3, overlap=0.2)
        K.spike(a, p1, p2, 0.24)
    # веки (в покое подняты под надбровье) и брови
    for s in S2:
        ex = s * 0.52
        at(a, F[f"Eyelid{side(s)}"], f"Eyelid{side(s)}")
        key("skinD")
        slab(a, [(-1.39, 2.06), (-1.47, 2.02), (-1.47, 1.63), (-1.39, 1.62)], ex - 0.34, ex + 0.34)
        key("dark")
        slab(a, [(-1.47, 1.68), (-1.5, 1.68), (-1.5, 1.62), (-1.47, 1.62)], ex - 0.3, ex + 0.3)  # ресничная линия
        at(a, F[f"Brow{side(s)}"], f"Brow{side(s)}")
        key("skinD")
        slab(a, [(-0.98, 2.04), (-1.58, 1.94), (-1.52, 1.7), (-1.05, 1.72)], s * 0.04, s * 1.06)
    # монокль с цепочкой
    at(a, F["Monocle"], "Monocle")
    mm = T(MONO_C) @ R("X", 90)
    a.frame("gold", S.octagon(-0.42, 0.42, -0.42, 0.42, 0.13), 0.1, -0.05, 0.05, axis="z", matrix=mm)
    a.prism("lens", S.octagon(-0.33, 0.33, -0.33, 0.33, 0.1), -0.015, 0.015, axis="z", matrix=mm)
    for i in range(4):
        p = MONO_C + V((-0.36 - i * 0.06, 0.06 + i * 0.03, -0.42 - i * 0.26))
        a.box("goldS", p.x - 0.05, p.x + 0.05, p.y - 0.05, p.y + 0.05, p.z - 0.1, p.z + 0.1, bevel=0.01)


def build_limbs(a, F):
    for s in S2:
        L = side(s)
        M = {("sh", s): F[f"UpperArm{L}"], ("el", s): F[f"ForeArm{L}"], ("wr", s): F[f"Hand{L}"],
             ("hip", s): F[f"Thigh{L}"], ("kn", s): F[f"Shin{L}"], ("an", s): F[f"Foot{L}"]}
        # плечо и предплечье — как в концепте
        at(a, M[("sh", s)], f"UpperArm{L}")
        key("furS")
        K.taper(a, (0, 0, 0.55), (0, 0, -0.65), 1.75, 1.45, 1.6, 1.35, up=(0, -1, 0), cut=0.32)
        key("fur")
        K.chain(a, [(0, 0, 0.1), (0, 0.05, -1.05), (0, 0, -UPPER)], [1.25, 1.18, 1.0], up=(0, -1, 0), cut=0.3)
        tufts(a, [(s * 0.55, -0.1, 0.75), (s * 0.85, 0.15, 0.4), (s * 0.4, 0.45, 0.65)], 0.75,
              lambda p, s=s: (s * 0.6, 0.1, 1.0), down=-0.3)
        at(a, M[("el", s)], f"ForeArm{L}")
        key("fur")
        K.chain(a, [(0, 0, 0.15), (0, -0.1, -1.25), (0, 0, -FORE)], [1.1, 1.95, 1.15], [1.1, 1.75, 1.05],
                up=(0, -1, 0), cut=0.3)
        tufts(a, [(0, 0.45, 0.05), (s * 0.3, 0.4, -0.25)], 0.6, (0, 1, -0.2), down=0.2)
        cuff = [(0.62 * math.cos(t), 0.55 * math.sin(t), -FORE + 0.35) for t in [i * math.pi / 3 for i in range(6)]]
        tufts(a, cuff, 0.55, lambda p: (p.x, p.y, -0.3), down=0.75)
        # кисть: ладонь и большой палец; пальцы — своя часть (кулак — сгибом)
        at(a, M[("wr", s)], f"Hand{L}")
        key("skin")
        K.taper(a, (0, 0, 0.1), (0, -0.05, -0.75), 1.15, 1.3, 0.8, 0.82, up=(0, -1, 0), cut=0.28)
        th = -s * 0.62
        K.chain(a, [(th, -0.2, -0.25), (th * 1.05, -0.55, -0.45), (th * 0.8, -0.78, -0.55)], [0.34, 0.3, 0.26],
                up=(0, -1, 0), cut=0.3)
        at(a, F[f"Fingers{L}"], f"Fingers{L}")
        for dx in (-0.38, 0.0, 0.38):
            pts = [(dx, -0.05, -0.62), (dx, -0.3, -1.15), (dx, -0.62, -1.3)]
            key("skin")
            K.chain(a, pts, [0.36, 0.33, 0.28], up=(0, -1, 0), cut=0.3)
            key("ivory")
            tip = V(pts[-1])
            K.spike(a, tip + V((0, -0.08, 0)), tip + V((0, -0.32, -0.12)), 0.18)
        # нога — как в концепте
        at(a, M[("hip", s)], f"Thigh{L}")
        key("fur")
        K.chain(a, [(0, 0, 0.35), (0, -0.05, -0.6), (0, 0, -THIGH)], [1.6, 1.7, 1.35], up=(0, -1, 0), cut=0.32)
        at(a, M[("kn", s)], f"Shin{L}")
        K.chain(a, [(0, 0, 0.2), (0, 0.05, -0.5), (0, 0, -SHIN)], [1.25, 1.3, 1.08], up=(0, -1, 0), cut=0.32)
        cuff = [(0.62 * math.cos(t), 0.6 * math.sin(t), -SHIN + 0.42) for t in [i * math.pi / 3.5 for i in range(7)]]
        tufts(a, cuff, 0.4, lambda p: (p.x, p.y, -0.2), down=0.7)  # короче концепта: в позах не задевают землю
        at(a, M[("an", s)], f"Foot{L}")
        key("skin")
        slab(a, [(0.5, 0.0), (0.42, -0.42), (-1.2, -0.42), (-1.38, -0.18), (-1.05, 0.12), (-0.2, 0.3), (0.35, 0.25)],
             -0.62, 0.62)
        key("skinD")
        slab(a, [(0.45, -0.42), (-1.2, -0.42), (-1.2, -0.36), (0.45, -0.36)], -0.64, 0.64)
        key("ivory")
        for dx in (-0.36, 0.0, 0.36):
            K.spike(a, (dx, -1.25, -0.3), (dx, -1.6, -0.4), 0.2)


def build_block(a, F):
    """Глыба: лёд (Block — низ, BlockTop — верхушка выше шва), рама и обвязки отдельно (непрозрачные), экспонаты."""
    Fb = F["Block"]
    x0, x1, y0, y1 = -1.95, 1.95, 0.85, 3.05
    z0, z1 = 1.6, 7.2
    oct_ = S.octagon(x0, x1, y0, y1, 0.55)
    at(a, Fb, "Block")
    a.extrude("iceBlock", oct_, z0, SPLIT, axis="z")  # невыпуклая деталь: грани экспонатов внутри не прячутся
    for x in (x0 + 0.02, x1 - 0.02):
        a.box("iceE", x - 0.04, x + 0.04, y0 + 0.35, y0 + 0.85, z0 + 0.3, SPLIT - 0.2, bevel=0)
    for i, x in enumerate((-1.55, -0.9, -0.2, 0.55, 1.2, 1.7)):
        key("iceD" if i % 2 else "iceE")
        K.spike(a, (x, y1 - 0.25, z0 + 0.02), (x, y1 - 0.2, z0 - 0.45 - 0.25 * (i % 3)), 0.32)
    at(a, F["BlockTop"], "BlockTop")
    a.extrude("iceBlock", oct_, SPLIT, z1, axis="z")
    a.frustum("iceBlock", (x0 + 0.2, x1 - 0.2, y0 + 0.15, y1 - 0.15), (-1.3, 0.9, 1.55, 2.85), z1, z1 + 0.85, bevel=0)
    a.frustum("iceE", (-1.3, 0.9, 1.55, 2.85), (-0.7, -0.1, 2.0, 2.4), z1 + 0.85, z1 + 1.45, bevel=0)
    for x, y, h, lean, w in ((1.3, 1.8, 1.6, 0.5, 0.6), (-1.45, 2.55, 1.2, -0.45, 0.5), (0.35, 2.9, 0.9, 0.2, 0.42)):
        key("iceD")
        K.spike(a, (x, y, z1 + 0.25), (x + lean, y + 0.1, z1 + 0.25 + h), w)
    for x in (x0 + 0.02, x1 - 0.02):
        a.box("iceE", x - 0.04, x + 0.04, y0 + 0.35, y0 + 0.85, SPLIT + 0.2, z1 - 0.3, bevel=0)
    # рама, обвязки, лямки, нижние уголки, табличка, шов-трещина — непрозрачная часть
    at(a, Fb, "BlockFrame")
    a.box("leatherD", -1.45, 1.45, y0 - 0.85, y0 + 0.05, 2.3, 6.3, bevel=0.03)
    for x in (-1.1, 1.1):
        for z in (2.7, 4.3, 5.9):
            a.box("goldS", x - 0.12, x + 0.12, y0 - 0.92, y0 - 0.8, z - 0.12, z + 0.12, bevel=0.02)
    a.frame("leather", S.octagon(x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, 0.6), 0.16, 2.3, 2.68, axis="z", bevel=0.008)
    for x in (x0 - 0.14, x1 + 0.14):
        a.box("gold", x - 0.06, x + 0.06, 1.95, 2.45, 2.24, 2.74, bevel=0.015)
    for s in S2:
        key("leather")
        K.chain(a, [(s * 1.25, y0 - 0.4, 5.6), (s * 1.55, 0.3, 4.75), (s * 1.55, -0.2, 4.2)], [0.42] * 3, [0.13] * 3,
                up=(1, 0, 0), cut=0.15, overlap=0.15)
    for x in (x0, x1):
        sx = 1 if x > 0 else -1
        for y in (y0 + 0.3, y1 - 0.3):
            a.box("gold", x - sx * 0.05, x + sx * 0.12, y - 0.35, y + 0.35, z0 - 0.06, z0 + 0.55, bevel=0.015)
    a.box("gold", -0.75, 0.75, y1 + 0.02, y1 + 0.1, z0 + 0.95, z0 + 1.45, bevel=0.02)
    a.box("goldD", -0.55, 0.55, y1 + 0.1, y1 + 0.13, z0 + 1.08, z0 + 1.32, bevel=0)
    crack_ring(a, x0, x1, y0, y1, SPLIT - 0.06)
    at(a, F["BlockTopFrame"], "BlockTopFrame")
    a.frame("leather", S.octagon(x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, 0.6), 0.16, 6.3, 6.68, axis="z", bevel=0.008)
    for x in (x0 - 0.14, x1 + 0.14):
        a.box("gold", x - 0.06, x + 0.06, 1.95, 2.45, 6.24, 6.74, bevel=0.015)
    for x in (x0, x1):
        sx = 1 if x > 0 else -1
        for y in (y0 + 0.3, y1 - 0.3):
            a.box("gold", x - sx * 0.05, x + sx * 0.12, y - 0.35, y + 0.35, z1 + 0.06, z1 - 0.55, bevel=0.015)
    # экспонаты: простые и лёгкие (D64)
    at(a, Fb, "ExCup")
    c = EXHIBITS["ExCup"]
    sc = 1.38
    a.prism("gold", S.octagon(c.x - 0.42 * sc, c.x + 0.42 * sc, c.y - 0.42 * sc, c.y + 0.42 * sc, 0.12 * sc),
            c.z - 0.62 * sc, c.z - 0.47 * sc)
    a.prism("goldD", S.octagon(c.x - 0.12 * sc, c.x + 0.12 * sc, c.y - 0.12 * sc, c.y + 0.12 * sc, 0.04 * sc),
            c.z - 0.47 * sc, c.z - 0.09 * sc)
    a.frustum("gold", (c.x - 0.25 * sc, c.x + 0.25 * sc, c.y - 0.25 * sc, c.y + 0.25 * sc),
              (c.x - 0.55 * sc, c.x + 0.55 * sc, c.y - 0.55 * sc, c.y + 0.55 * sc), c.z - 0.09 * sc, c.z + 0.6 * sc)
    at(a, Fb @ T(EXHIBITS["ExGem"]) @ R("X", 35) @ R("Y", 45), "ExGem")
    a.box("neonGem", -0.45, 0.45, -0.45, 0.45, -0.45, 0.45, bevel=0)
    at(a, Fb, "ExLovibum")
    c = EXHIBITS["ExLovibum"] - V((0, 0, 0.7))
    sc = 1.55
    a.prism("steel", S.octagon(c.x - 0.32 * sc, c.x + 0.32 * sc, c.y - 0.32 * sc, c.y + 0.32 * sc, 0.1 * sc), c.z,
            c.z + 0.22 * sc)
    a.frustum("neonCrystal", (c.x - 0.26 * sc, c.x + 0.26 * sc, c.y - 0.26 * sc, c.y + 0.26 * sc), (c.x, c.x, c.y, c.y),
              c.z + 0.45 * sc, c.z + 0.95 * sc, bevel=0)
    a.frustum("crystalD", (c.x - 0.26 * sc, c.x + 0.26 * sc, c.y - 0.26 * sc, c.y + 0.26 * sc), (c.x, c.x, c.y, c.y),
              c.z + 0.45 * sc, c.z + 0.2 * sc, bevel=0)
    at(a, Fb, "ExCritter")
    c = EXHIBITS["ExCritter"] - V((0, 0, 0.7))
    sc = 1.55
    key("critter")
    K.layered(a, [(-0.4 * sc, c.z), (-0.45 * sc, c.z + 0.5 * sc), (-0.2 * sc, c.z + 0.85 * sc),
                  (0.3 * sc, c.z + 0.8 * sc), (0.42 * sc, c.z + 0.35 * sc), (0.3 * sc, c.z)],
              [(0.38 * sc, 1, 1)], (0, c.z + 0.4 * sc), xc=c.x, matrix=T((0, c.y, 0)))
    for s in S2:
        K.spike(a, (c.x + s * 0.22 * sc, c.y, c.z + 0.78 * sc), (c.x + s * 0.32 * sc, c.y + 0.05, c.z + 1.12 * sc),
                0.16 * sc)
        a.box("dark", c.x + s * 0.15 * sc - 0.06 * sc, c.x + s * 0.15 * sc + 0.06 * sc, c.y - 0.47 * sc,
              c.y - 0.42 * sc, c.z + 0.48 * sc, c.z + 0.62 * sc, bevel=0)


def crack_ring(a, x0, x1, y0, y1, z):
    """Шов-трещина по кругу глыбы: тёмная ломаная полоса — видно, что верхушка откидывается."""
    pts = [(x0, y0 + 0.55), (x0 + 0.55, y0), (x1 - 0.55, y0), (x1, y0 + 0.55), (x1, y1 - 0.55), (x1 - 0.55, y1),
           (x0 + 0.55, y1), (x0, y1 - 0.55)]
    for i in range(len(pts)):
        p0, p1 = V((*pts[i], z)), V((*pts[(i + 1) % len(pts)], z))
        n = max(1, int((p1 - p0).length / 0.6))
        for k in range(n):
            q0, q1 = p0.lerp(p1, k / n), p0.lerp(p1, (k + 1) / n)
            out = V((q0.x + q1.x, q0.y + q1.y, 0)) / 2 - V(((x0 + x1) / 2, (y0 + y1) / 2, 0))
            out = out.normalized() * 0.04
            dz = 0.07 if k % 2 else -0.07
            mid = (q0 + q1) / 2 + out + V((0, 0, dz))
            d = q1 - q0
            m = T(mid) @ R("Z", math.degrees(math.atan2(d.y, d.x)))
            a.box("iceD", -d.length / 2 - 0.02, d.length / 2 + 0.02, -0.03, 0.03, -0.045, 0.045, bevel=0, matrix=m)


def build(map_name):
    F = rest_frames()
    a = GameArt(f"Boss5Yeti{map_name}", MAPS[map_name])
    if map_name == "Head":
        build_head(a, F)
    elif map_name == "Body":
        build_torso(a, F)
        build_block(a, F)
    else:
        build_limbs(a, F)
    a.transform, a.group = None, None
    return a


# ── Сборка, запекание, экспорт, кадры ─────────────────────────────────────────────────────────────────────────
def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    repo, shots = os.path.abspath(argv[0]), os.path.abspath(argv[1])
    mode = argv[2] if len(argv) > 2 else ""
    texdir = os.path.join(repo, "assets", "textures", "art")
    models = os.path.join(repo, "assets", "models")
    os.makedirs(shots, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    col = bpy.data.collections.new("Yeti")
    bpy.context.scene.collection.children.link(col)
    rest_frames()
    report = {"maps": {}, "tris": {}, "ground_offset": round(GROUND, 3)}
    parts = {}
    arts = {}
    for m in ("Head", "Body", "Limbs"):
        a = build(m)
        arts[m] = a
        obj = a.build(col)
        if mode == "check":
            report["maps"][m] = a.stats
            continue
        if mode == "":
            _explode(obj, a, 1)
            uv = S.bake(obj, a, texdir, a.name, **a.bake_opts)
            _explode(obj, a, -1)
            report["maps"][m] = {**a.stats, **{k: round(v, 3) for k, v in uv.items()}}
            split = S.split_groups(obj, a, {g: PIVOTS[g] for g in dict.fromkeys(a.face_groups)}, col)
        else:
            report["maps"][m] = a.stats
            split = _split_keep(obj, a, col)
        parts.update(split)
    if mode == "check":
        print("CHECK", json.dumps(report, ensure_ascii=False))
        return
    missing = [n for n in RIG_TREE if n not in parts]
    if missing:
        raise ValueError(f"нет частей {missing}")
    report["dropped_enclosed_faces"] = _drop_enclosed(parts)
    for n, o in parts.items():
        o.data.calc_loop_triangles()
        report["tris"][n] = len(o.data.loop_triangles)
    report["tris_total"] = sum(report["tris"].values())
    _ice_look(arts)
    if mode == "":
        game = {}
        for n, o in parts.items():  # игровой масштаб в меше, начало — точка вращения
            o.data.transform(Matrix.Scale(SCALE, 4))
            o.location = PIVOTS[n] * SCALE
            game[n] = o
        S.export_fbx([game[n] for n in RIG_TREE], os.path.join(models, "Boss5_Yeti.fbx"))
        write_rig(os.path.join(models, "Boss5_Yeti.rig.json"), game, report)
        write_colors(os.path.join(models, "Boss5_Yeti.colors.json"), arts, parts)
        for n, o in parts.items():
            o.data.transform(Matrix.Scale(1 / SCALE, 4))
            o.location = PIVOTS[n]
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(models, "Boss5_Yeti.blend"), compress=True)
    shoot(parts, shots, report)
    with open(os.path.join(shots, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("YETI_OK", json.dumps({"tris_total": report["tris_total"], "maps": {m: r.get("tris") for m, r in
                                                                             report["maps"].items()}}))


def _explode(obj, art, sign):
    order = {g: i for i, g in enumerate(dict.fromkeys(art.face_groups))}
    me = obj.data
    done = set()
    for poly in me.polygons:
        dx = order[art.face_groups[poly.index]] * 14 * S.RING["step"] * sign
        for v in poly.vertices:
            if v not in done:
                me.vertices[v].co.x += dx
                done.add(v)


def _split_keep(obj, art, col):
    out = {}
    me = obj.data
    for group in dict.fromkeys(art.face_groups):
        pv = PIVOTS[group]
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if art.face_groups[f.index] != group], context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        bmesh.ops.translate(bm, vec=-pv, verts=bm.verts)
        mesh = bpy.data.meshes.new(f"{obj.name}_{group}")
        bm.to_mesh(mesh)
        bm.free()
        for m in me.materials:
            mesh.materials.append(m)
        o = bpy.data.objects.new(f"{obj.name}_{group}", mesh)
        o.location = pv
        col.objects.link(o)
        out[group] = o
    bpy.data.objects.remove(obj)
    return out


def _drop_enclosed(parts):
    """Грани, которых не видно ни в одной позе (все лучи упираются в ту же часть), — долой (как у существ)."""
    dirs = []
    n = 300
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(1 - z * z, 0.0))
        ang = math.pi * (3 - math.sqrt(5)) * i
        dirs.append(V((r * math.cos(ang), r * math.sin(ang), z)))
    removed = 0
    for name, o in parts.items():
        if name in ICE_PARTS or name.startswith("Ex"):
            continue  # лёд прозрачный — его внутренние грани видны
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.normal_update()
        tree = BVHTree.FromBMesh(bm, epsilon=0.0)
        dead = [f for f in bm.faces
                if all(all(tree.ray_cast(p + f.normal * 0.004, d)[0] is not None for d in dirs)
                       for p in (f.calc_center_median(), *[v.co.lerp(f.calc_center_median(), 0.1) for v in f.verts]))]
        if dead:
            removed += len(dead)
            bmesh.ops.delete(bm, geom=dead, context="FACES")
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
            bm.to_mesh(o.data)
            o.data.update()
        bm.free()
    return removed


def _ice_look(arts):
    """Лёд глыбы в кадрах полупрозрачный (в игре — прозрачность MeshPart), золото чуть металлическое."""
    for a in arts.values():
        for mat in a.materials:
            k = mat.name.rsplit("_", 1)[-1]
            b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if b is None:
                continue
            if k.startswith("neon"):
                b.inputs["Emission Strength"].default_value = 3.0
            if k.startswith("gold"):
                b.inputs["Metallic"].default_value = 0.4
                b.inputs["Roughness"].default_value = 0.35


def write_rig(path, game, report):
    out = {"scale": SCALE, "order": list(RIG_TREE), "parts": {}, "poses": {}, "heights": {}, "head_parts": HEAD_PARTS,
           "ice_parts": ICE_PARTS, "attack_clips": {"bite": "smash", "swipe": "ice_clap"}}
    for n, (parent, m) in RIG_TREE.items():
        co = [AX @ v.co for v in game[n].data.vertices]
        lo = V([min(c[i] for c in co) for i in range(3)])
        hi = V([max(c[i] for c in co) for i in range(3)])
        out["parts"][n] = {"parent": parent, "pivot": [round(c, 4) for c in AX @ (PIVOTS[n] * SCALE)],
                           "center": [round(c, 4) for c in (lo + hi) / 2], "size": [round(c, 4) for c in hi - lo],
                           "map": m}
    rest = {n: [v.co.copy() / SCALE for v in game[n].data.vertices] for n in RIG_TREE}
    for name, P in POSES.items():
        W = pose_world(P)
        zs = [(W[n] @ (PIVOTS[n] + c)).z for n in RIG_TREE for c in rest[n]]
        low, high = min(zs), max(zs)
        out["heights"][name] = round((high - low) * SCALE, 2)
        tr = transforms(P)
        out["poses"][name] = {}
        for n in RIG_TREE:
            m3, off = tr[n]
            r = AX @ m3 @ AX.transposed()
            t = AX @ (off * SCALE)
            if n == "Torso":
                t.y -= low * SCALE
            out["poses"][name][n] = [round(x, 4) for x in [t.x, t.y, t.z] + [r[i][j] for i in range(3) for j in range(3)]]
        report.setdefault("pose_low", {})[name] = round(low, 3)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("RIG_OK", path, json.dumps(out["heights"]))


def write_colors(path, arts, parts):
    """Средний цвет каждой части по площади граней (заготовка блоками до импорта мешей)."""
    out = {}
    for m, a in arts.items():
        keys = list(a.colors)
        for n in MAPS[m]:
            o = parts[n]
            acc, area = V((0, 0, 0)), 0.0
            for p in o.data.polygons:
                mi = p.material_index
                code = a.colors[keys[mi]][0] if mi < len(keys) else "FFFFFF"
                c = V(S.rgb(code))
                acc += c * p.area
                area += p.area
            c = acc / max(area, 1e-6)
            out[n] = "".join(f"{max(0, min(255, round(x * 255))):02X}" for x in c)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


def apply(parts, P):
    W = pose_world(P)
    for n, o in parts.items():
        o.matrix_world = W[n] @ T(PIVOTS[n])
    bpy.context.view_layer.update()


def shoot(parts, shots, report):
    sys.path.insert(0, os.path.join(HERE, "concepts510"))
    import ck  # noqa: E402

    cam = ck.studio(bpy.data.collections["Yeti"], size=1.5, bg=(0.7, 0.76, 0.86))
    bpy.context.scene.view_settings.exposure = -0.3
    for n in ICE_PARTS:  # лёд глыбы в кадрах полупрозрачный — своя копия материала (в игре — прозрачность MeshPart)
        me = parts[n].data
        for i, m in enumerate(me.materials):
            mm = m.copy()
            b = next((x for x in mm.node_tree.nodes if x.type == "BSDF_PRINCIPLED"), None)
            if b is not None:
                b.inputs["Alpha"].default_value = 0.3
            mm.surface_render_method = "BLENDED"
            mm.use_backface_culling = True
            me.materials[i] = mm
    root = bpy.data.objects.new("Turn", None)
    bpy.data.collections["Yeti"].objects.link(root)
    for o in parts.values():
        o.parent = root
    want = os.environ.get("YETI_SHOTS", "all")
    names = list(POSES) if want == "all" else want.split(",")
    for name in names:
        apply(parts, POSES[name])
        co = [o.matrix_world @ v.co for o in parts.values() for v in o.data.vertices]
        lo = V([min(c[i] for c in co) for i in range(3)])
        hi = V([max(c[i] for c in co) for i in range(3)])
        cz = (lo.z + hi.z) / 2
        span = max(hi.x - lo.x, hi.z - lo.z, 9.0)
        dist = 1.15 * span / (2 * 18 / 55)
        views = (("34", -35), ("front", 0)) if name in ("sleep", "combat") else (("34", -35),)
        if name == "stand":  # глыба с экспонатами: сбоку и сзади в 3/4
            views = (("34", -35), ("front", 0), ("side", -90), ("back34", 145))
        for label, ang in views:
            root.rotation_euler = (0, 0, math.radians(ang))
            bpy.context.view_layer.update()
            xs = [(o.matrix_world @ v.co).x for o in parts.values() for v in o.data.vertices]
            cx = (min(xs) + max(xs)) / 2  # кадр по всей сцене (глыба рядом во сне не обрезается)
            span2 = max(max(xs) - min(xs), hi.z - lo.z, 9.0)
            d2 = 1.15 * span2 / (2 * 18 / 55)
            ck.shot(cam, os.path.join(shots, f"pose_{name}_{label}.png"), (cx, -d2, cz + 1.5), (cx, 0, cz), 55,
                    (700, 700))
        root.rotation_euler = (0, 0, 0)
        report.setdefault("pose_size", {})[name] = [round(hi[i] - lo[i], 2) for i in range(3)]


if __name__ == "__main__":
    main()
