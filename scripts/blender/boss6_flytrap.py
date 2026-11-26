"""Босс 6 «Джунгли» — Королева-мухоловка, игровая модель: части на Motor6D, игровые позы (шаг 2 D64).

Формы — утверждённый концепт v2b scripts/blender/boss6/flytrap.py (лист assets/concepts/bosses_5_10/boss6_v2/).
Мухоловка не ходит (D64 п. 5): корень Root стоит на месте, поворот — всей моделью. Отличия игровой модели от концепта:
- модель собрана в покое (стойка с закрытой пастью, ровными бровями и открытыми глазами) и разрезана на 45 частей
  с точками вращения (D18): Root (клубень, корни, побеги к бутонам; корень рига) → Rosette1…6 (листья розетки на
  земле) → Stem1…4 (звенья стебля; на Stem2 — амулет) → Head (бутон, маска лица, глаза) → EyelidL/R и EyelidLowL/R
  (верхнее и нижнее веко: прячутся в маске над и под глазом, сон — смыкаются), BrowL/R, TrapUpper/TrapLower
  (створки пасти) → Tongue, Crown (в поражении падает на землю), Petals (венчик); MantleL/C/R (три коротких листа за
  стеблем); лозы VineUpperL/R → VineLowerL/R → PalmL/R (ладонь-лист) → FingerL1…3 / FingerR1…3 (листья-пальцы,
  каждый на своём суставе: раскрыть, сжать — «хватает»); BudStemL/R (побег с бутоном-фрейлиной и задней створкой)
  → BudLidL/R (передняя створка: в бою раскрывается маленькой ловушкой, без лица);
- руки — ладонь из трёх листьев-пальцев (замечание владельца 2026-11-25: не «бантик»), лозы растут из узлов стебля
  на разной высоте (растение, а не плечи человека); глаза — в гнёздах маски, веки выдвигаются (прищур, сон);
- «Z» сна, капля росы, опавшие листья — только на концепт-листе.
Позы — параметрами (числа, чтобы клипы можно было сплайнить): наклон стебля, голова, створки, язык (наружу, набок),
веки, брови, лозы (отвод, мах, сгиб, поворот и сгиб кисти), пальцы (развод, сгиб), венчик, корона (падение 0…1),
мантия, розетка, бутоны (раскрытие, наклон). frames(P) → система каждой части; pose_world(P) → матрица покой → поза;
transforms(P) → Transform суставов относительно покоя, как у Йети (rig.json).
Карты 1024² (D39 v2, как у Йети): Head (голова, веки, брови, створки, язык, корона, венчик), Body (клубень, розетка,
стебель, мантия, бутоны), Limbs (лозы, ладони, пальцы).
Пишет (полный режим): assets/models/Boss6_Flytrap.{fbx,blend,rig.json,colors.json}, карты assets/textures/art/
Boss6Flytrap{Head,Body,Limbs}_{color,normal}.png; кадры, report.json и предпросмотр rig.json — в папку кадров.
Режимы: (пусто) — запекание, экспорт, кадры; quick — материалы сборки, без экспорта (rig.json — в папку кадров);
check — только сборка и числа. Кадры по выбору: FLY_SHOTS="stand,grab" (none — без кадров).
Запуск: blender --background --factory-startup --python scripts/blender/boss6_flytrap.py -- <репо> <кадры> [quick|check]
Подключается и как модуль (клипы): тогда ничего не собирает.
Зависит от art_style.py, dragon10/v4_kit.py, boss6/flytrap.py (концепт: листья, створки, венчик, корона, палитра),
joint_check.py, concepts510/ck.py (студия, кадр).
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "dragon10"), os.path.join(HERE, "boss6")):
    if p not in sys.path:
        sys.path.insert(0, p)
import art_style as S  # noqa: E402
import flytrap as C6  # noqa: E402  (концепт: лист, створка, венчик, корона, палитра)
import v4_kit as K  # noqa: E402

V = Vector
S2 = (1, -1)
SCALE = 1.968  # стадов на единицу модели: рост в стойке 24 стада (концепт-лист)
AX = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))  # оси Roblox: (x, y, z) Blender → (x, z, −y)
R, T, key, leaf, frame = C6.R, C6.T, C6.key, C6.leaf, C6.frame
STEM_BASE, STEM_LEN, STEM_W = C6.STEM_BASE, C6.STEM_LEN, C6.STEM_W
FACE_Y, EYE_Z, HINGE, POD_H = C6.FACE_Y, C6.EYE_Z, C6.HINGE, C6.POD_H
EX = 0.68  # глаз: центр по x
SOCK_W, SOCK_H = 0.42, 0.48  # гнездо глаза в маске: полуширина, полувысота
SOCK_D = 0.16  # глубина передней пластины маски (гнездо)
LID = 0.5  # высота века; веко прячется в маске над гнездом (нижнее — под ним), сон — сдвиг на LID
MASK = (-1.42, 1.42, 1.05, 3.22, 0.25)  # маска лица: x0, x1, z0, z1, срез углов (выше концепта: веко помещается)
HALO_C = V((0, 0.55, 1.75))  # центр венчика в системе головы
CROWN_AT = V((0.1, -0.15, POD_H - 0.12))
CROWN_FALLEN = T((3.6, -5.8, 0.95)) @ R("Z", 30) @ R("Y", 74)  # корона на земле (поражение, как в концепте)
TONGUE_ROOT = V((0, 0, 0.05))  # корень языка в системе нижней створки
SHOULDER_Z = {1: 0.2, -1: 1.3}  # лозы растут из узла на заметно разной высоте — растение, а не плечи (модерация)
UPPER, FORE = 1.55, 1.4  # звенья лозы
KNUCKLES = ((-0.5, 30.0, 1.9), (0.0, 0.0, 2.2), (0.5, -30.0, 1.9))  # пальцы: x на ладони, развод, длина
FINGER_W = 0.92  # ширина листа-пальца (крупные: ладонь читается с камеры игрока)
KNUCKLE_Z = -0.9  # линия пальцев на ладони (система кисти: лоза по −z, ладонь смотрит в −y)
BUD_AT = {1: (3.75, -4.4), -1: (-3.75, -4.4)}  # бутоны-фрейлины (как в концепте)
BUD_HINGE = V((0, 0.05, 1.7))  # петля передней створки бутона в системе побега
# точки крепления для катсцены D74 «съесть» (подключает игра): Ловибум в правой ладони — перед лицом ладони у основания
# пальцев (система ладони); капсула этажа — перед кончиками сомкнутых створок (система головы), летит вперёд (−y)
ATTACH = {"LovibumHold": ("PalmR", V((0, -0.6, -0.9)), V((0, -1, 0))),
          "CapsuleSpawn": ("Head", V((0, -3.35, 0.32)), V((0, -1, 0)))}
BUD_LOBE = dict(L=1.55, H=0.55, W=1.2, n_cil=4, cil=0.12, cil_w=0.1, out_key="petal", rim=0.16)

PALETTE = dict(C6.PALETTE)
# контраст с зелёной ареной (правка владельца 2026-11-26: «снова зелёное на зелёном»): голова-ловушка и мантия —
# тёмные бутылочные, стебель и лозы — тёмные оливково-коричневые; светлые сочные — только листья розетки и ладони;
# главные пятна — малиновая пасть, розовые лепестки, золотая корона
PALETTE.update({
    "pod": ("1E5C34", True), "podD": ("174D2B", True), "trap": ("123F24", True), "leafD": ("1A4F2D", True),
    "stem": ("4E4522", True), "stemD": ("362F16", False), "vine": ("5E4F26", True),
    "face": ("528F40", False), "lid": ("2C6A34", False), "brow": ("10281A", False),
    "palm": ("BDEB6E", True),  # ладони и листья-пальцы — светлые сочные
})

# ── Скелет игры: часть → (родитель, карта) ───────────────────────────────────────────────────────────────────
RIG_TREE = {"Root": (None, "Body")}
for _i in range(1, 7):
    RIG_TREE[f"Rosette{_i}"] = ("Root", "Body")
RIG_TREE.update({"Stem1": ("Root", "Body"), "Stem2": ("Stem1", "Body"), "Stem3": ("Stem2", "Body"),
                 "Stem4": ("Stem3", "Body"), "Head": ("Stem4", "Head")})
for _s in "LR":
    RIG_TREE.update({f"Eyelid{_s}": ("Head", "Head"), f"EyelidLow{_s}": ("Head", "Head"), f"Brow{_s}": ("Head", "Head")})
RIG_TREE.update({"TrapUpper": ("Head", "Head"), "TrapLower": ("Head", "Head"), "Tongue": ("TrapLower", "Head"),
                 "Crown": ("Head", "Head"), "Petals": ("Head", "Head"),
                 "MantleL": ("Stem4", "Body"), "MantleC": ("Stem4", "Body"), "MantleR": ("Stem4", "Body")})
for _s in "LR":
    RIG_TREE.update({f"VineUpper{_s}": ("Stem3", "Limbs"), f"VineLower{_s}": (f"VineUpper{_s}", "Limbs"),
                     f"Palm{_s}": (f"VineLower{_s}", "Limbs")})
    for _j in range(1, 4):
        RIG_TREE[f"Finger{_s}{_j}"] = (f"Palm{_s}", "Limbs")
for _s in "LR":
    RIG_TREE.update({f"BudStem{_s}": ("Root", "Body"), f"BudLid{_s}": (f"BudStem{_s}", "Body")})
MAPS = {m: tuple(p for p, (_, mm) in RIG_TREE.items() if mm == m) for m in ("Head", "Body", "Limbs")}
HEAD_PARTS = ["Head", "EyelidL", "EyelidR", "EyelidLowL", "EyelidLowR", "BrowL", "BrowR", "TrapUpper", "TrapLower",
              "Tongue", "Crown", "Petals"]
BODY_PARTS = ("Root", "Stem1", "Stem2", "Stem3", "Stem4", "Head", "TrapUpper", "TrapLower")  # контур тела (BodyRange)
NOT_JOINTS = ("EyelidL", "EyelidR", "EyelidLowL", "EyelidLowR", "BrowL", "BrowR", "Crown", "Tongue", "TrapUpper",
              "TrapLower", "BudLidL", "BudLidR", "MantleL", "MantleC", "MantleR")  # не сгибы: выдвигаются,
# раскрываются или это плоский лист, утопленный корнем в стебель (сфера проверки шире листа) — сгиб не проверяется


def side(s):
    return "L" if s > 0 else "R"


# ── Позы: параметры ──────────────────────────────────────────────────────────────────────────────────────────
def base_pose():
    """Поза покоя — стойка концепта: пасть закрыта, брови ровные, глаза открыты (в ней собирается модель).
    Наклон головы −4.5° гасит изгиб стебля (4.5°): в покое голова стоит по осям — проверка совпадающих граней точная."""
    return {"lean": 4.0, "side": 0.0, "head": (-4.5, 0.0, 0.0), "jaw": (0.0, 0.0), "tongue": (0.0, 0.0),
            "lid": {1: (0.0, 0.0, 0.0), -1: (0.0, 0.0, 0.0)}, "brow": {1: (0.0, 0.0), -1: (0.0, 0.0)},
            "arm": {1: (80.0, 24.0, 34.0, 0.0, 0.0), -1: (84.0, 22.0, 38.0, 15.0, 0.0)},
            "fing": {1: (0.0, 0.0), -1: (0.0, 0.0)}, "petals": 0.0, "crown": 0.0, "mantle": (0.0, 0.0),
            "rosette": 0.0, "bud": {1: (0.0, 0.0), -1: (0.0, 0.0)}}


def pose(**kw):
    P = base_pose()
    for k, v in kw.items():
        if isinstance(v, dict) and isinstance(P.get(k), dict):
            P[k] = {**P[k], **v}
        else:
            P[k] = v
    return P


def both(v):
    return {1: v, -1: v}


SMUG = {1: (-20.0, 0.1), -1: (22.0, -0.05)}  # брови: вредная, одна выше (концепт «smug»)
ANGRY = {1: (-24.0, -0.08), -1: (24.0, -0.08)}  # злые: к переносице ниже
SQUINT = {1: (0.6, 0.12, -10.0), -1: (0.6, 0.12, 10.0)}  # прищур: верхнее веко на треть, к переносице ниже
GLARE = {1: (0.35, 0.08, -12.0), -1: (0.35, 0.08, 12.0)}
SHUT = both((1.0, 1.0, 0.0))

POSES = {
    # лозы несимметричны (модерация: не силуэт фигуры с руками): одна высоко и закручена усиком, другая ниже,
    # свисает к розетке
    "stand": pose(jaw=(15, 28), lid=SQUINT, brow=SMUG, arm={1: (138, 12, 70, -15, 46), -1: (58, 22, 38, -10, 30)},
                  fing={1: (0.1, 18), -1: (0.05, 30)}),
    "sleep": pose(lean=12, side=4, head=(24, 6, 8), lid=SHUT, brow={1: (8, -0.05), -1: (-8, -0.05)},
                  arm={1: (12, 12, 22, 0, 0), -1: (14, 10, 26, 0, 0)}, fing=both((-0.1, 45)), petals=22,
                  mantle=(-8, 0), bud=both((0, 34))),
    "combat": pose(lean=12, head=(2, 0, 0), jaw=(28, 46), tongue=(1, 0), lid=GLARE, brow=ANGRY,
                   arm={1: (142, 16, 58, -15, 50), -1: (104, 28, 36, -15, 40)}, fing=both((0.25, 8)), rosette=4,
                   bud=both((78, -8))),
    # «Хватает» (особая атака, только анимация). Замах: лозы выброшены вперёд к игроку (вперёд-в стороны, чуть вверх),
    # кисть отогнута вверх — ладонь смотрит на игрока (камера сверху-спереди), три пальца-листа вверх веером,
    # чуть согнуты когтем…
    "grab": pose(lean=20, head=(-4, 0, 0), jaw=(24, 40), lid=GLARE, brow=ANGRY,
                 arm=both((136, 50, 8, -36, 85)), fing=both((0.55, 18)), rosette=4,
                 bud=both((78, -8))),
    # …хват: стебель и лозы подаются ещё вперёд, кисть чуть опускается, три пальца сходятся и сгибаются к ладони
    # (к игроку) — ладонь сжимается в кулак из листьев на месте раскрытой (та же ветвь углов, что у замаха —
    # клип сплайнится без переворота кисти)
    "grab2": pose(lean=26, head=(0, 0, 0), jaw=(10, 22), lid=GLARE, brow=ANGRY,
                  arm=both((140, 56, 4, -34, 50)), fing=both((-0.4, 95)), rosette=4,
                  bud=both((78, -8))),
    # «Захлоп» (основной выпад): голова бросается вперёд, створки сомкнуты
    "snap": pose(lean=28, head=(16, 0, 0), jaw=(0, 0), lid=GLARE, brow=ANGRY,
                 arm={1: (64, -28, 30, 0, 0), -1: (64, -28, 30, 0, 0)}, fing=both((0.1, 30)), petals=-10,
                 bud=both((40, -4))),
    "hit": pose(lean=-10, side=6, head=(-24, -10, -8), jaw=(10, 30), lid=SHUT, brow={1: (16, 0.08), -1: (-16, 0.08)},
                arm={1: (62, -16, 50, 0, 0), -1: (62, -16, 50, 0, 0)}, fing=both((0.4, -10)), petals=-12,
                bud=both((0, -10))),
    "defeat": pose(lean=16, side=-18, head=(26, -12, -28), jaw=(8, 38), tongue=(0, 1), lid=SHUT,
                   brow={1: (-16, 0.1), -1: (16, 0.1)}, arm={1: (26, -6, 10, 0, 0), -1: (30, -4, 12, 0, 0)},
                   fing=both((-0.1, 40)), petals=14, crown=1.0, mantle=(-24, 10), bud=both((0, 46))),
    "victory": pose(lean=-6, head=(-12, 0, 0), jaw=(22, 42), lid=SQUINT, brow=SMUG,
                    arm={1: (158, 14, 64, 0, 20), -1: (92, 30, 28, 0, 10)}, fing=both((0.3, 0)), petals=-8,
                    mantle=(12, 10), bud=both((60, -6))),
}


# ── Системы частей ───────────────────────────────────────────────────────────────────────────────────────────
def blend(a, b, k):
    """Смесь двух жёстких матриц: сдвиг — линейно, поворот — по дуге."""
    if k <= 0:
        return a.copy()
    if k >= 1:
        return b.copy()
    ta, qa, _ = a.decompose()
    tb, qb, _ = b.decompose()
    return T(ta.lerp(tb, k)) @ qa.slerp(qb, k).to_matrix().to_4x4()


def tongue_motion(out, side_):
    """Язык: 0 — лежит в нижней створке; out — высунут вперёд и вверх; side_ — свесился набок и вниз."""
    m_out = T((0, -0.75, 0.05)) @ R("X", -14)
    m_side = T((0.15, -0.45, 0.0)) @ R("Z", 40) @ R("X", 35)
    m = blend(Matrix(), m_out, out)
    return blend(m, m_side, side_)


def frames(P):
    """Система каждой части в позе P (начало — точка вращения); геометрия строится в позе покоя."""
    F = {"Root": Matrix()}
    for i in range(6):
        t = 30 + 60 * i
        d = V((math.cos(math.radians(t)), math.sin(math.radians(t)), 0))
        F[f"Rosette{i + 1}"] = T(d * 2.4 + V((0, 0, 0.7))) @ R("Z", t) @ R("Y", -P["rosette"])
    k = len(STEM_LEN)
    m = T(STEM_BASE)
    nodes = [m]
    for i, ln in enumerate(STEM_LEN):
        f = (i + 1) / k  # изгиб растёт к верху — стебель гнётся дугой (как в концепте)
        m = m @ R("X", P["lean"] / k * (0.5 + f)) @ R("Y", P["side"] / k * (0.5 + f))
        F[f"Stem{i + 1}"] = m
        m = m @ T((0, 0, ln))
        nodes.append(m)
    F["_nodes"] = nodes
    hp, hy, hr = P["head"]
    H = nodes[-1] @ T((0, 0, 0.7)) @ R("Z", hy) @ R("X", hp) @ R("Y", hr)
    F["Head"] = H
    for s in S2:
        L = side(s)
        up_, low, tilt = P["lid"][s]
        c = V((s * EX, FACE_Y, EYE_Z))
        F[f"Eyelid{L}"] = H @ T(c) @ T((0, 0, -LID * up_)) @ R("Y", tilt)
        F[f"EyelidLow{L}"] = H @ T(c) @ T((0, 0, LID * low)) @ R("Y", tilt * 0.5)
        ang, lift = P["brow"][s]
        F[f"Brow{L}"] = H @ T((s * EX, FACE_Y - 0.11, EYE_Z + 0.78 + lift)) @ R("Y", ang)
    up_, down = P["jaw"]
    F["TrapUpper"] = H @ T(HINGE) @ R("X", -up_)
    F["TrapLower"] = H @ T(HINGE) @ R("X", down)
    F["Tongue"] = F["TrapLower"] @ T(TONGUE_ROOT) @ tongue_motion(*P["tongue"])
    F["Petals"] = H @ T(HALO_C) @ R("X", P["petals"])
    F["Crown"] = blend(H @ T(CROWN_AT) @ R("Y", -8) @ R("X", -6), CROWN_FALLEN, P["crown"])
    lift, flare = P["mantle"]
    for dx, n in ((-1, "MantleR"), (0, "MantleC"), (1, "MantleL")):
        F[n] = nodes[-1] @ T((dx * 0.75, 0.6, -0.3)) @ R("Z", dx * flare) @ R("X", lift)
    for s in S2:
        L = side(s)
        out, fwd, el, tw, bend = P["arm"][s]
        sh = F["Stem3"] @ T((s * 0.95, -0.1, SHOULDER_Z[s])) @ R("Y", -s * out) @ R("X", -fwd)
        elb = sh @ T((0, 0, -UPPER)) @ R("X", -el)
        wr = elb @ T((0, 0, -FORE)) @ R("Z", s * tw) @ R("X", bend)
        F[f"VineUpper{L}"], F[f"VineLower{L}"], F[f"Palm{L}"] = sh, elb, wr
        spread, curl = P["fing"][s]
        for j, (kx, ka, _) in enumerate(KNUCKLES):
            F[f"Finger{L}{j + 1}"] = wr @ T((kx, 0, KNUCKLE_Z)) @ R("Y", ka * (1 + spread)) @ R("X", -curl)
        opn, tilt = P["bud"][s]
        x, y = BUD_AT[s]
        Fs = T((x, y, 0)) @ R("Z", -s * 22) @ R("X", tilt)
        F[f"BudStem{L}"] = Fs
        F[f"BudLid{L}"] = Fs @ T(BUD_HINGE) @ R("X", opn)
    return F


REST_F = None
PIVOTS = {}


def rest_frames():
    global REST_F
    if REST_F is None:
        REST_F = frames(base_pose())
        for n in RIG_TREE:
            PIVOTS[n] = REST_F[n].translation.copy()
    return REST_F


def pose_world(P):
    """Матрица каждой части: геометрия покоя (в мире) → поза P."""
    rf = rest_frames()
    F = frames(P)
    return {n: F[n] @ rf[n].inverted() for n in RIG_TREE}


def transforms(P):
    """Transform каждого сустава относительно покоя (как Motor6D: деталь = родитель · C0 · Transform · C1⁻¹)."""
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


# ── Геометрия (в покое) ──────────────────────────────────────────────────────────────────────────────────────
class GameArt(S.Art):
    """Art, который принимает только детали частей своей карты (одна сборка — одна карта)."""

    def __init__(self, name, allowed):
        super().__init__(name, ring_z0=0.5)
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


def at(a, m, group):
    a.transform, a.group = m, group


def build_root(a, F):
    """Клубень (ярусы, бугры, корни), побеги к бутонам и листья розетки — как в концепте, листья — свои части."""
    at(a, Matrix(), "Root")
    for i, (r0, r1, z0, z1, ox, oy) in enumerate(((2.75, 3.1, 0.0, 0.45, 0.0, 0.0), (3.05, 2.85, 0.4, 0.9, 0.08, -0.05),
                                                  (2.75, 2.35, 0.85, 1.3, 0.12, 0.04), (2.2, 1.75, 1.25, 1.6, 0.05, 0.1),
                                                  (1.65, 1.35, 1.55, 1.85, 0.0, 0.05))):
        key("root" if i % 2 == 0 else "rootD")
        t = math.radians(22.5 * (i % 2))
        K.taper(a, (ox, oy, z0), (ox, oy, z1), 2 * r0, 2 * r1, up=(math.sin(t), -math.cos(t), 0), cut=0.3)
    for ang, h, rr in ((0, 0.95, 0.62), (128, 0.75, 0.55), (236, 0.8, 0.6)):
        d = V((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
        key("rootD" if ang else "root")
        K.taper(a, d * 2.45 + V((0, 0, h)), d * 3.15 + V((0, 0, h + 0.12)), 2 * rr, 1.2 * rr, up=(0, 0, 1), cut=0.3)
    for ang in (62, 180):
        d = V((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
        key("root")
        K.chain(a, [d * 2.7 + V((0, 0, 0.35)), d * 3.6 + V((0, 0, 0.12)), d * 4.2 + V((0, 0, -0.12))],
                [0.5, 0.34, 0.16], up=(0, 0, 1), cut=0.3, overlap=0.3)
    for s in S2:  # побеги-корни от клубня к бутонам-фрейлинам: бутоны — отростки королевы, а не отдельные цветы
        x, y = BUD_AT[s]
        d = V((x, y, 0)).normalized()
        key("root")
        K.chain(a, [d * 2.6 + V((0, 0, 0.32)), d * 4.2 + V((0, 0, 0.2)), V((x, y, 0.12)) + d * 0.1],
                [0.52, 0.42, 0.4], [0.42, 0.34, 0.3], up=(0, 0, 1), cut=0.3, overlap=0.3)
    for i in range(6):  # розетка: 6 огромных светлых листьев веером на земле
        t = math.radians(30 + 60 * i)
        d = V((math.cos(t), math.sin(t), 0))
        root = d * 2.4 + V((0, 0, 0.7))
        at(a, Matrix(), f"Rosette{i + 1}")
        ln = 5.3 if i != 4 else 4.7
        leaf(a, "leafL", frame(root, d + V((0, 0, -0.42)), V((0, 0, 1))), ln, 2.7, 0.2, bends=(0, 22, 16),
             ts=(0.3, 0.74), rib="rib", root_w=0.3)


def build_stem(a, F):
    """Звенья стебля (каждое — своя часть, нахлёст на узлах), пояски узлов, листочки, амулет на Stem2."""
    nodes = F["_nodes"]
    pts = [n.translation.copy() for n in nodes]
    for i in range(len(STEM_LEN)):
        at(a, Matrix(), f"Stem{i + 1}")
        key("stem")
        ov = 0.45 * 0.5
        K.taper(a, pts[i], pts[i + 1], STEM_W[i], STEM_W[i + 1], up=(0, -1, 0), cut=0.3,
                ext0=STEM_W[i] * ov if i else 0.0, ext1=STEM_W[i + 1] * ov)
    for i in (2, 3):  # пояски узлов закрывают сгиб
        at(a, nodes[i], f"Stem{i + 1}")
        w = STEM_W[i] / 2 + 0.14
        a.prism("stemD", S.octagon(-w, w, -w, w, w * 0.6), -0.14, 0.14)
    for i, s in ((2, -1), (3, 1)):  # листочки из узлов — живой стебель
        at(a, nodes[i], f"Stem{i + 1}")
        w = STEM_W[i] / 2
        leaf(a, "leafL", frame((s * w * 0.8, 0.1, 0.05), (s, -0.25, 0.75), (-s * 0.5, -0.3, 1)), 1.7, 0.85, 0.12,
             bends=(0, 18), ts=(0.5,), rib="rib", root_w=0.3)
    at(a, nodes[1] @ T((0, 0, C6.AMULET_Z)), "Stem2")  # амулет: золотой обруч и медальон
    w = (STEM_W[1] + STEM_W[2]) / 4 + 0.1
    a.prism("gold", S.octagon(-w, w, -w, w, w * 0.6), -0.2, 0.2)
    a.prism("goldD", S.octagon(-w - 0.04, w + 0.04, -w - 0.04, w + 0.04, (w + 0.04) * 0.6), -0.06, 0.06, bevel=0)
    a.box("gold", -0.14, 0.14, -w - 0.2, -w + 0.1, -0.55, -0.05, bevel=0)
    at(a, nodes[1] @ T((0, -w - 0.12, C6.AMULET_Z - 0.75)) @ R("X", 90 + 6), "Stem2")
    a.prism("gold", S.octagon(-0.62, 0.62, -0.62, 0.62, 0.22), -0.04, 0.16)
    a.prism("goldD", S.octagon(-0.48, 0.48, -0.48, 0.48, 0.17), 0.16, 0.2, bevel=0)
    a.prism("neonGem", S.octagon(-0.36, 0.36, -0.36, 0.36, 0.13), 0.2, 0.36, bevel=0)
    a.box("white", 0.06, 0.18, 0.1, 0.22, 0.36, 0.38, bevel=0)


def build_mantle(a, F):
    """Три коротких изогнутых листа-плаща за стеблем, разведены в стороны; застёжка — на центральном."""
    top = F["_nodes"][-1]
    for dx, n in ((-1, "MantleR"), (0, "MantleC"), (1, "MantleL")):
        at(a, Matrix(), n)
        ln, w = (4.6, 2.6) if dx == 0 else (4.2, 2.45)
        root = top @ V((dx * 0.75, 0.6, -0.3))
        Mf = frame(root, V((dx * 1.8, 0.8 if dx else 1.0, -0.45)), V((dx * 0.9, 1.0, 0.45)))
        leaf(a, "leafD", Mf, ln, w, 0.17, bends=(0, -10, 50), ts=(0.3, 0.66), fold=26, rib="rib", veins=True,
             root_w=0.3, rib_w=0.1)
    at(a, top @ T((0, 0.8, -0.2)) @ R("X", -80), "MantleC")
    a.prism("gold", S.octagon(-0.45, 0.45, -0.45, 0.45, 0.15), -0.06, 0.12)
    a.prism("neonGem", S.octagon(-0.22, 0.22, -0.22, 0.22, 0.07), 0.12, 0.24, bevel=0)


def build_mask(a):
    """Маска лица с гнёздами глаз: задняя пластина целиком, передняя — рамка вокруг гнёзд (полосы, переносица, бока)
    со ступенями D39. Веки прячутся в передней пластине над и под гнездом."""
    x0, x1, z0, z1, c = MASK
    y0 = FACE_Y
    zb, zt = EYE_Z - SOCK_H, EYE_Z + SOCK_H
    a.prism("face", S.octagon(x0 + 0.1, x1 - 0.1, z0 + 0.1, z1 - 0.1, c), y0 + SOCK_D, y0 + 0.5, axis="y")  # задняя
    # пластина на 0.1 у́же рамки: ступень D39, без общих граней
    back = y0 + SOCK_D + 0.03  # передние куски заходят в заднюю пластину
    a.prism("face", [(x0, z0 + c), (x0 + c, z0), (x1 - c, z0), (x1, z0 + c), (x1, zb), (x0, zb)], y0, back, axis="y",
            bevel=0)
    a.prism("face", [(x0, zt), (x1, zt), (x1, z1 - c), (x1 - c, z1), (x0 + c, z1), (x0, z1 - c)], y0, back, axis="y",
            bevel=0)
    ix, ox = EX - SOCK_W, EX + SOCK_W
    a.prism("face", [(-ix, zb - 0.02), (ix, zb - 0.02), (ix, zt + 0.02), (-ix, zt + 0.02)], y0 - 0.04, back, axis="y",
            bevel=0)  # переносица выступает ступенью
    for s in S2:
        xa, xb = sorted((s * ox, s * (x1 - 0.03)))  # бок рамки на 0.03 внутри: без общей грани с полосами
        a.prism("face", [(xa, zb - 0.02), (xb, zb - 0.02), (xb, zt + 0.02), (xa, zt + 0.02)], y0 - 0.02,
                back + 0.015, axis="y", bevel=0)  # задняя грань глубже полос — не в одной плоскости с ними


def lobe(a, m, upper, seam=False, **kw):
    """Створка концепта (C6.lobe) для игры: слои малинового нутра сдвинуты ступенью (у сомкнутых створок торцы
    нутра не совпадают), плоские донца пяти слоёв створки — тоже (у концепта они в одной плоскости: широкий слой
    теперь ниже узких на 0.005 за слой и прячет их донца), seam — малиновая пластина у шва под ресничками
    (реснички не висят в воздухе; у нижней створки сдвинута к петле на 0.02 — торцы швов не совпадают)."""
    n0 = len(a.parts)
    C6.lobe(a, m, upper, **kw)
    W = (a.transform if a.transform is not None else Matrix()) @ m
    Wi = W.inverted()
    sgn = 1 if upper else -1
    L = kw.get("L", C6.TRAP_L)
    yc = (0.25 - L) / 2
    k = 0
    out_key = kw.get("out_key", "trap")
    for j, (bm, key_, _, _) in enumerate(a.parts[n0:n0 + 5]):  # пять слоёв створки (K.layered)
        assert key_ == out_key
        for v in bm.verts:
            q = Wi @ v.co
            if abs(q.z) < 1e-4:
                q.z = -sgn * 0.005 * j  # шаг 0.005: не совпадает со швом (±0.012, ±0.035) и нутром
                v.co = W @ q
    for bm, key_, _, _ in a.parts[n0:]:
        if key_ != "maw":
            continue
        for v in bm.verts:
            q = Wi @ v.co
            q.z += sgn * 0.007 * (k + 1)
            if not upper:
                q.y = yc + (q.y - yc) * 0.985
            v.co = W @ q
        k += 1
    if seam:
        hw = kw.get("W", C6.TRAP_W) / 2 * (1.0 if upper else 0.975)
        half = (0.25 + L) / 2
        dy = 0.0 if upper else 0.02
        pts = [(0.92 * hw * math.sin(math.radians(u)), yc + dy - 0.93 * half * math.cos(math.radians(u)))
               for u in range(-90, 91, 18)]
        a.prism("rim", pts, -sgn * 0.035, sgn * 0.012, bevel=0, matrix=m)


def build_head(a, F):
    H = F["Head"]
    at(a, H, "Head")
    a.prism("stem", S.octagon(-0.85, 0.85, -0.85, 0.75, 0.45), -1.55, 0.4, bevel=0)  # шея: в бутон и глубоко
    # в стебель — при наклоне головы назад сустав не раскрывается
    n = 6
    for i in range(n):  # бутон — ступенчатое «яйцо» (как pod концепта, без маски)
        t0, t1 = i / n, (i + 1) / n
        tm = (t0 + t1) / 2
        f = max(math.sqrt(max(1 - ((tm - 0.45) / (0.55 if tm > 0.45 else 0.45)) ** 2, 0.0)), 0.42)
        wx, wy = C6.POD_RX * f - 0.01 * i, C6.POD_RY * f - 0.01 * i
        a.prism("pod" if i % 2 == 0 else "podD",
                S.octagon(C6.POD_C.x - wx, C6.POD_C.x + wx, C6.POD_C.y - wy, C6.POD_C.y + wy, min(wx, wy) * 0.36),
                POD_H * t0 - (0.01 if i else 0), POD_H * t1 + 0.01)
    build_mask(a)
    y = FACE_Y
    for s in S2:  # глаза в гнёздах: белок, зрачок, блик (за веками); ресницы вверх-наружу — на маске
        ex, ez = s * EX, EYE_Z
        a.box("eyeW", ex - SOCK_W - 0.01, ex + SOCK_W + 0.01, y + 0.14, y + 0.22, ez - SOCK_H - 0.01,
              ez + SOCK_H + 0.01, bevel=0)  # за рамкой на 0.01 (рамка заходит в гнездо на 0.02) — торцы не совпадают
        px, pz = -s * 0.08, -0.08
        a.box("pupil", ex + px - 0.2, ex + px + 0.2, y + 0.115, y + 0.15, ez + pz - 0.24, ez + pz + 0.24, bevel=0)
        a.box("white", ex + px + 0.03, ex + px + 0.14, y + 0.105, y + 0.12, ez + pz + 0.06, ez + pz + 0.18, bevel=0)
        for j, dx in enumerate((-0.3, 0.0, 0.3)):
            key("dark")
            tip = (ex + dx + s * 0.22 + dx * 0.4, y - 0.18, ez + 0.76 + (0.06 if j == 1 else 0.0))
            K.spike(a, (ex + dx, y + 0.02, ez + SOCK_H + 0.06), tip, 0.1)
        a.box("petal", s * 1.08 - 0.2, s * 1.08 + 0.2, y - 0.06, y + 0.02, 1.38, 1.54, bevel=0)  # румянец
    for s in S2:  # веки: верхнее над гнездом, нижнее под ним (спрятаны в маске); нижнее чуть глубже — без общих граней
        L = side(s)
        at(a, F[f"Eyelid{L}"], f"Eyelid{L}")
        a.box("lid", -SOCK_W - 0.06, SOCK_W + 0.06, 0.015, 0.085, SOCK_H + 0.02, SOCK_H + 0.02 + LID, bevel=0)
        at(a, F[f"EyelidLow{L}"], f"EyelidLow{L}")
        a.box("lid", -SOCK_W - 0.05, SOCK_W + 0.05, 0.025, 0.095, -SOCK_H - 0.02 - LID, -SOCK_H - 0.02, bevel=0)
        a.box("dark", -SOCK_W - 0.02, SOCK_W + 0.02, 0.018, 0.04, -SOCK_H - 0.1, -SOCK_H - 0.05, bevel=0)  # шов сна
        at(a, F[f"Brow{L}"], f"Brow{L}")
        a.box("brow", -0.52, 0.52, -0.1, 0.17, -0.11, 0.11, bevel=0.03)
    at(a, H, "TrapUpper")
    lobe(a, T(HINGE), True, seam=True, cil=0.19, cil_w=0.13)  # реснички вдвое короче концепта: злая, не страшная
    at(a, H, "TrapLower")
    lobe(a, T(HINGE), False, seam=True, cil=0.19, cil_w=0.13)
    at(a, F["Tongue"], "Tongue")
    key("tongue")
    K.chain(a, [(0, 0.0, 0.0), (0, -0.8, 0.09), (0, -1.45, 0.11)], [0.95, 0.9, 0.72], [0.22] * 3, up=(0, 0, 1),
            cut=0.35, overlap=0.3)
    at(a, H, "Petals")
    C6.halo(a, "smug", 0.0)
    at(a, H, "Crown")
    C6.crown(a, T(CROWN_AT) @ R("Y", -8) @ R("X", -6))


def build_limbs(a, F):
    for s in S2:
        L = side(s)
        sh, el, wr = F[f"VineUpper{L}"], F[f"VineLower{L}"], F[f"Palm{L}"]
        # лоза: изогнутые звенья (растение), узел-утолщение на сгибе закрывает сустав
        at(a, sh, f"VineUpper{L}")
        key("vine")
        K.chain(a, [(0, 0, 0.1), (s * 0.08, -0.14, -0.8), (0, 0, -UPPER)], [0.8, 0.72, 0.66], up=(0, -1, 0), cut=0.3,
                overlap=0.3)
        a.prism("stemD", S.octagon(-0.44, 0.44, -0.44, 0.44, 0.15), -UPPER - 0.26, -UPPER + 0.2)  # узел лозы
        leaf(a, "leafD", frame((s * 0.18, -0.1, -0.55), (s * 0.9, -0.3, 0.6), (0, -1, 0.3)), 1.0, 0.55, 0.1,
             bends=(0, 14), ts=(0.5,), rib="rib", root_w=0.35)  # листочек-прилистник на лозе
        at(a, el, f"VineLower{L}")
        key("vine")
        K.chain(a, [(0, 0, 0.15), (-s * 0.06, -0.12, -0.72), (0, 0, -FORE)], [0.64, 0.58, 0.52], up=(0, -1, 0),
                cut=0.3, overlap=0.3)
        for j in range(2):  # усики, закрученные завитком
            q = [V((s * (0.28 + 0.28 * math.cos(t)), 0.28 * math.sin(t), -0.35 - 0.5 * j - 0.1 * t))
                 for t in (0.0, 1.6, 3.2)]
            K.chain(a, [V((0, 0, -0.35 - 0.5 * j))] + q, [0.2, 0.17, 0.14, 0.1], up=(0, -1, 0), cut=0.3, overlap=0.3)
        a.prism("stemD", S.octagon(-0.38, 0.38, -0.38, 0.38, 0.13), -FORE - 0.22, -FORE + 0.14)  # узел у ладони
        # ладонь — широкий лист-основание (смотрит в −y), светлые жилки веером к каждому пальцу
        at(a, wr, f"Palm{L}")
        a.prism("palm", [(-0.48, 0.12), (0.48, 0.12), (0.86, -0.42), (0.76, -1.06), (-0.76, -1.06), (-0.86, -0.42)],
                -0.15, 0.15, axis="y")
        for kx, _, _ in KNUCKLES:
            p0, p1 = V((0, 0, -0.08)), V((kx, 0, KNUCKLE_Z))
            mid, ln = (p0 + p1) / 2, (p1 - p0).length
            ang = math.degrees(math.atan2(-(p1.x - p0.x), -(p1.z - p0.z)))  # ось бруска вдоль p0 → p1
            a.box("leaf", -0.055, 0.055, -0.21, -0.14, -ln / 2, ln / 2, bevel=0, matrix=T(mid) @ R("Y", ang))
        for j, (kx, ka, ln) in enumerate(KNUCKLES):  # пальцы-листья: длинные, заострённые, с жилкой; в сгибе — к ладони
            at(a, F[f"Finger{L}{j + 1}"], f"Finger{L}{j + 1}")
            leaf(a, "palm", frame((0, 0, 0.2), (0, 0, -1), (0, -1, 0)), ln, FINGER_W, 0.18, bends=(0, 14), ts=(0.45,),
                 rib="leaf", root_w=0.45, rib_w=0.06)


def build_buds(a, F):
    """Бутоны-фрейлины без лиц: побег с листочками, чашелистики, задняя створка (на побеге) и передняя (своя
    часть). Закрыт — розовое «яйцо» с застёжкой ресничек; в бою передняя створка откидывается — маленькая ловушка."""
    for s in S2:
        L = side(s)
        Fs = F[f"BudStem{L}"]
        at(a, Fs, f"BudStem{L}")
        key("stem")  # побег тёмный, как стебель королевы (контраст с ареной)
        K.chain(a, [(0, 0, 0.02), (0.08, -0.05, 0.8), (0, 0.05, BUD_HINGE.z - 0.1)], [0.42, 0.36, 0.32], up=(0, -1, 0),
                cut=0.3, overlap=0.3)
        for ss, ln in ((1, 1.3), (-1, 1.1)):
            leaf(a, "leafD", frame((ss * 0.15, 0, 0.3), (ss * 1, -0.25, 0.25), (0, 0, 1)), ln, 0.7, 0.1, bends=(0,),
                 ts=(), root_w=0.3)
        hb = T(BUD_HINGE)
        a.prism("trap", S.octagon(-0.42, 0.42, -0.42, 0.42, 0.15), -0.4, 0.05, bevel=0, matrix=hb)  # донце чаши
        for i in range(4):  # чашелистики — низкая чаша под бутоном
            t = math.radians(45 + 90 * i)
            d = V((math.cos(t), math.sin(t), 0))
            leaf(a, "trap" if i % 2 else "leafD", frame(BUD_HINGE + d * 0.3 + V((0, 0, -0.3)), d * 0.5 + V((0, 0, 1)), d),
                 0.8, 0.72, 0.13, bends=(0,), ts=(), root_w=0.8)
        lobe(a, hb @ R("X", -90), True, **BUD_LOBE)  # задняя створка (вверх: длина створки по +z)
        at(a, F[f"BudLid{L}"], f"BudLid{L}")
        lobe(a, R("X", -90), False, **{**BUD_LOBE, "L": BUD_LOBE["L"] - 0.04})  # передняя створка — откидывается
        # вперёд; на 0.04 короче задней: канты сомкнутых створок не в одной плоскости


def build(map_name):
    F = rest_frames()
    a = GameArt(f"Boss6Flytrap{map_name}", MAPS[map_name])
    if map_name == "Head":
        build_head(a, F)
    elif map_name == "Body":
        build_root(a, F)
        build_stem(a, F)
        build_mantle(a, F)
        build_buds(a, F)
    else:
        build_limbs(a, F)
    a.transform, a.group = None, None
    return a


# ── Сборка, проверки, кадры ──────────────────────────────────────────────────────────────────────────────────
def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    repo, shots = os.path.abspath(argv[0]), os.path.abspath(argv[1])
    mode = argv[2] if len(argv) > 2 else ""
    texdir = os.path.join(repo, "assets", "textures", "art")
    models = os.path.join(repo, "assets", "models")
    os.makedirs(shots, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    col = bpy.data.collections.new("Flytrap")
    bpy.context.scene.collection.children.link(col)
    rest_frames()
    report = {"maps": {}, "tris": {}, "parts": len(RIG_TREE)}
    parts, arts = {}, {}
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
        report["tris_total"] = sum(r["tris"] for r in report["maps"].values())
        with open(os.path.join(shots, "report_check.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
        print("STATS CHECK", json.dumps({m: {k: r[k] for k in ("tris", "flipped", "degenerate")} | {
            "coplanar": len(r["coplanar"])} for m, r in report["maps"].items()}, ensure_ascii=False),
              report["tris_total"])
        return
    missing = [n for n in RIG_TREE if n not in parts]
    if missing:
        raise ValueError(f"нет частей {missing}")
    report["dropped_enclosed_faces"] = _drop_enclosed(parts)
    bpy.context.view_layer.update()
    from joint_check import check_bends, check_joints  # правила анатомии D64: щели в суставах > 0.05 стада — ошибка

    rig = {n: (par, tuple(PIVOTS[n])) for n, (par, _) in RIG_TREE.items()}
    report["joint_issues"] = confirm_floating(parts, check_joints(parts, rig, gap=0.05 / SCALE, pivot_far=0.5 / SCALE))
    print("STATS JOINTS", json.dumps(report["joint_issues"], ensure_ascii=False), flush=True)
    report["joint_issues_by_pose"] = {}
    for name, P in POSES.items():
        apply(parts, P)
        W = pose_world(P)
        rig_p = {n: (par, tuple(W[n] @ PIVOTS[n])) for n, (par, _) in RIG_TREE.items()}
        gaps = [i for i in check_joints(parts, rig_p, gap=0.05 / SCALE, pivot_far=99) if i["kind"] == "щель в суставе"]
        if P["crown"] > 0:
            gaps = [i for i in gaps if i["part"] != "Crown"]  # корона упала на землю — так задумано
        gaps += [i for i in check_bends(parts, rig_p) if i["part"] not in NOT_JOINTS]
        report["joint_issues_by_pose"][name] = gaps
    apply(parts, base_pose())
    print("STATS JOINTS_POSES", json.dumps(report["joint_issues_by_pose"], ensure_ascii=False), flush=True)
    for n, o in parts.items():
        o.data.calc_loop_triangles()
        report["tris"][n] = len(o.data.loop_triangles)
    report["tris_total"] = sum(report["tris"].values())
    report["tris_by_map"] = {m: sum(report["tris"][n] for n in MAPS[m]) for m in MAPS}
    _look(arts)
    rig_path = os.path.join(models if mode == "" else shots, "Boss6_Flytrap.rig.json")
    write_rig(rig_path, parts, report)
    if mode == "":
        game = {}
        for n, o in parts.items():  # игровой масштаб в меше, начало — точка вращения
            o.data.transform(Matrix.Scale(SCALE, 4))
            o.location = PIVOTS[n] * SCALE
            game[n] = o
        S.export_fbx([game[n] for n in RIG_TREE], os.path.join(models, "Boss6_Flytrap.fbx"))
        write_colors(os.path.join(models, "Boss6_Flytrap.colors.json"), arts, parts)
        for n, o in parts.items():
            o.data.transform(Matrix.Scale(1 / SCALE, 4))
            o.location = PIVOTS[n]
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(models, "Boss6_Flytrap.blend"), compress=True)
    shoot(parts, shots, report)
    with open(os.path.join(shots, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("DONE FLYTRAP_OK", json.dumps({"tris_total": report["tris_total"], "by_map": report["tris_by_map"],
                                    "coplanar": {m: len(r.get("coplanar", [])) for m, r in report["maps"].items()},
                                    "flipped": {m: r.get("flipped") for m, r in report["maps"].items()}}))


def confirm_floating(parts, issues):
    """«Летающая деталь» joint_check ищется по точкам (вершины и центры граней): вложенные слои створки концепта
    (слой шире соседнего, но тоньше по профилю) пересекаются, а точки друг в друга не попадают. Остров, чья
    поверхность пересекает другие острова части или другие части (BVH overlap), не летает — такие находки снимаются."""
    import joint_check as J

    out = []
    for it in issues:
        if it["kind"] != "летающая деталь":
            out.append(it)
            continue
        bm = J._world_bm(parts[it["part"]])
        isl = J._islands(bm)
        at_ = V(it["at"])

        def centre(faces):
            pts = [v.co for f in faces for v in f.verts] + [f.calc_center_median() for f in faces]
            return sum(pts, V()) / len(pts)

        def near(faces):  # ближайшая к находке точка острова (вершина или центр грани)
            return min(min((v.co - at_).length for f in faces for v in f.verts),
                       min((f.calc_center_median() - at_).length for f in faces))

        k = min(range(len(isl)), key=lambda i: (near(isl[i]), (centre(isl[i]) - at_).length))
        lo = [round(min(v.co[i] for f in isl[k] for v in f.verts), 2) for i in range(3)]
        hi = [round(max(v.co[i] for f in isl[k] for v in f.verts), 2) for i in range(3)]
        info = {"faces": len(isl[k]), "lo": lo, "hi": hi}  # остров-находка: в отчёт (что именно «летает»)
        verts = [v.co.copy() for v in bm.verts]
        mine = BVHTree.FromPolygons(verts, [[v.index for v in f.verts] for f in isl[k]])
        rest = [[v.index for v in f.verts] for j, fs in enumerate(isl) if j != k for f in fs]
        trees = [BVHTree.FromPolygons(verts, rest)] if rest else []
        for n, o in parts.items():
            if n != it["part"] and len(o.data.polygons):
                b2 = J._world_bm(o)
                trees.append(BVHTree.FromBMesh(b2))
                b2.free()
        bm.free()
        if not any(mine.overlap(t) for t in trees):
            out.append({**it, "island": info})
    return out


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


LONE_MAX = 0.6  # одинокая грань крупнее (ед.²) — видимая деталь (белок глаза 0.84), не остаток (торцы створок ≤ 0.43)


def _drop_enclosed(parts):
    """Грани, которых не видно ни в одной позе (все лучи упираются в ту же часть), — долой (как у Йети)."""
    dirs = []
    n = 300
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(1 - z * z, 0.0))
        ang = math.pi * (3 - math.sqrt(5)) * i
        dirs.append(V((r * math.cos(ang), r * math.sin(ang), z)))
    removed = 0
    orphans = 0
    for o in parts.values():
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
            # одинокая грань — остаток детали, чьи соседние грани спрятаны (торец канта створки): долой; крупная
            # (белок глаза: бока в рамке, перед виден) — остаётся
            lone = [f for f in bm.faces if not any(len(e.link_faces) > 1 for e in f.edges) and f.calc_area() < LONE_MAX]
            orphans += len(lone)
            bmesh.ops.delete(bm, geom=lone, context="FACES")
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
            bm.to_mesh(o.data)
            o.data.update()
        bm.free()
    print("STATS ORPHAN_FACES", orphans, flush=True)
    return removed


def _look(arts):
    """Золото чуть металлическое, самоцветы светятся (как в концепте)."""
    for a in arts.values():
        for mat in a.materials:
            k = mat.name.rsplit("_", 1)[-1]
            b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if b is None:
                continue
            if k.startswith("neon"):
                b.inputs["Emission Strength"].default_value = 3.0
            if k.startswith("gold"):
                b.inputs["Metallic"].default_value = 0.45
                b.inputs["Roughness"].default_value = 0.32


def hull(points):
    """Выпуклая оболочка точек (x, z) — против часовой стрелки (монотонная цепь Эндрю)."""
    pts = sorted(set(points))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def simplify(poly, min_turn=12.0):
    """Убрать вершины контура с поворотом меньше min_turn градусов (контур для боя — до ~16 точек)."""
    out = list(poly)
    changed = True
    while changed and len(out) > 6:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            u, v = (b[0] - a[0], b[1] - a[1]), (c[0] - b[0], c[1] - b[1])
            ang = abs(math.degrees(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1])))
            if ang < min_turn:
                out.pop(i)
                changed = True
                break
    return out


def write_rig(path, parts, report):
    """rig.json как у Йети: части (родитель, точка вращения, габарит, карта), позы (12 чисел), высоты, контур тела
    Body (вид сверху, X и Z Roblox, стады) — дальность ближнего боя от контура (BodyRange)."""
    out = {"scale": SCALE, "order": list(RIG_TREE), "parts": {}, "poses": {}, "heights": {}, "head_parts": HEAD_PARTS,
           "attack_clips": {"bite": "snap", "swipe": "grab"}, "rooted": True}
    rest = {n: [v.co.copy() for v in parts[n].data.vertices] for n in RIG_TREE}  # от точки вращения, ед. модели
    for n, (parent, m) in RIG_TREE.items():
        co = [AX @ (c * SCALE) for c in rest[n]]
        lo = V([min(c[i] for c in co) for i in range(3)])
        hi = V([max(c[i] for c in co) for i in range(3)])
        out["parts"][n] = {"parent": parent, "pivot": [round(c, 4) for c in AX @ (PIVOTS[n] * SCALE)],
                           "center": [round(c, 4) for c in (lo + hi) / 2], "size": [round(c, 4) for c in hi - lo],
                           "map": m}
    pts = []
    for n in BODY_PARTS:
        for c in rest[n]:
            w = AX @ ((PIVOTS[n] + c) * SCALE)
            pts.append((round(w.x, 2), round(w.z, 2)))
    out["body"] = [[x, z] for x, z in simplify(hull(pts))]
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
            out["poses"][name][n] = [round(x, 4) for x in [t.x, t.y, t.z] + [r[i][j] for i in range(3) for j in range(3)]]
        report.setdefault("pose_low", {})[name] = round(low, 3)
    rf = rest_frames()
    out["attachments"] = {}
    for name, (part, p, d) in ATTACH.items():  # в осях детали от её точки вращения (как Attachment.Position), стады
        w = rf[part] @ p
        out["attachments"][name] = {"part": part, "position": [round(c, 4) for c in AX @ ((w - PIVOTS[part]) * SCALE)],
                                    "direction": [round(c, 4) for c in AX @ (rf[part].to_3x3() @ d).normalized()]}
    out["eat_clip"] = "eat"
    report["body_points"] = len(out["body"])
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("STATS RIG_OK", path, json.dumps(out["heights"]))


def write_colors(path, arts, parts):
    """Средний цвет каждой части по площади граней (заготовка блоками до импорта мешей)."""
    out = {}
    for m, a in arts.items():
        keys = list(a.colors)
        for n in MAPS[m]:
            acc, area = V((0, 0, 0)), 0.0
            for p in parts[n].data.polygons:
                mi = p.material_index
                code = a.colors[keys[mi]][0] if mi < len(keys) else "FFFFFF"
                acc += V(S.rgb(code)) * p.area
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


def _points(parts, names):
    return [o.matrix_world @ v.co for n, o in parts.items() if n in names for v in o.data.vertices]


def shoot(parts, shots, report):
    sys.path.insert(0, os.path.join(HERE, "concepts510"))
    import ck  # noqa: E402

    col = bpy.data.collections["Flytrap"]
    cam = ck.studio(col, size=1.5, bg=(0.7, 0.76, 0.86))
    scene = bpy.context.scene
    scene.view_settings.exposure = -0.3
    root = bpy.data.objects.new("Turn", None)
    col.objects.link(root)
    for o in parts.values():
        o.parent = root
    want = os.environ.get("FLY_SHOTS", "all")
    names = [] if want == "none" else list(POSES) if want == "all" else want.split(",")
    sil = bpy.data.materials.new("Sil")  # силуэт: всё чёрное на белом
    sil.use_nodes = True
    nt = sil.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0, 0, 0, 1)
    outn = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], outn.inputs[0])
    res = (900, 900)
    for name in names:
        apply(parts, POSES[name])
        co = _points(parts, RIG_TREE)
        lo = V([min(c[i] for c in co) for i in range(3)])
        hi = V([max(c[i] for c in co) for i in range(3)])
        report.setdefault("pose_size", {})[name] = [round(hi[i] - lo[i], 2) for i in range(3)]
        cz = max(hi.z, 12.0) / 2
        views = {"stand": (("front", 0), ("side", -90), ("back", 180), ("34", -35))}.get(name, (("34", -35), ("front", 0)))
        for label, ang in views:
            root.rotation_euler = (0, 0, math.radians(ang))
            bpy.context.view_layer.update()
            xs = [(o.matrix_world @ v.co).x for o in parts.values() for v in o.data.vertices]
            span = max(max(xs) - min(xs), hi.z - lo.z, 13.0)
            dist = 1.18 * span / (2 * 18 / 55)
            ck.shot(cam, os.path.join(shots, f"{name}_{label}.png"), (0, -dist, cz + 1.2), (0, 0, cz - 0.4), 55, res)
            if name == "stand" and label in ("front", "side"):  # силуэт: «не женщина в платье» — проверка заливкой
                world = scene.world
                bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
                old = (tuple(bg.inputs["Color"].default_value), bg.inputs["Strength"].default_value,
                       scene.view_settings.exposure)
                bg.inputs["Color"].default_value = (1, 1, 1, 1)
                bg.inputs["Strength"].default_value = 1.0
                scene.view_settings.exposure = 0.0
                bpy.data.objects["Floor"].hide_render = True
                bpy.context.view_layer.material_override = sil
                ck.shot(cam, os.path.join(shots, "stand_sil.png" if label == "front" else "stand_sil_side.png"),
                        (0, -dist, cz + 1.2), (0, 0, cz - 0.4), 55, res)
                bpy.context.view_layer.material_override = None
                bpy.data.objects["Floor"].hide_render = False
                bg.inputs["Color"].default_value = old[0]
                bg.inputs["Strength"].default_value = old[1]
                scene.view_settings.exposure = old[2]
        root.rotation_euler = (0, 0, 0)
        bpy.context.view_layer.update()
        if name in ("stand", "grab", "grab2", "combat"):  # ладонь крупно: три пальца-листа читаются
            hand = ["PalmL", "FingerL1", "FingerL2", "FingerL3"]
            pts = _points(parts, hand)
            c = sum(pts, V()) / len(pts)
            ck.shot(cam, os.path.join(shots, f"hand_{name}.png"), c + V((2.6, -7.2, 2.2)), c, 55, (700, 700))
        if name == "stand":  # лицо и пасть крупно: длина ресничек-зубов (злая, но не страшная)
            pts = _points(parts, ["Head", "TrapUpper", "TrapLower"])
            c = sum(pts, V()) / len(pts)
            ck.shot(cam, os.path.join(shots, "face_stand.png"), c + V((2.4, -9.5, 1.2)), c, 55, (700, 700))
    if "grab" in names or "grab2" in names:  # «хватает»: от игрока чуть сверху (камера телефона)
        for name in ("grab", "grab2"):
            if name not in names:
                continue
            apply(parts, POSES[name])
            ck.shot(cam, os.path.join(shots, f"{name}_player.png"), (3.0, -17.0, 9.0), (0, -3.0, 6.0), 45, res)
        apply(parts, base_pose())


if __name__ == "__main__":
    main()
