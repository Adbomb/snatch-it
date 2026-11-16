"""Король-дракон №10, этап C.2: текстуры версии 3 — та же палитра и рисунок D39, объём заметнее, чем у v2.

Основа — цвет версии 1 (как у v2: палитра, кольца D39). Поверх — те же карты, что у v2 (scripts/blender/dragon10/
v7_tex_v2.py: окклюзия 1.4 и 6 ст., нормаль, высота), плюс новые запекания того же скрипта:
- ao_tight — окклюзия на 0.5 ст.: щели между пластинами чешуи и края накладок (тонкие тёмные линии в стыках);
- part — номер части (меша сустава) в каждом пикселе: оттенок фиолетового по крупным частям тела.
Что сильнее, чем в v2 (scripts/boss10_tex_v2.py):
- тени под бронёй и в стыках (окклюзия 1.4 ст. до ×0.42, 6 ст. до ×0.56, щели 0.5 ст. до ×0.7);
- свет сверху и сверху-спереди (±26 % и ±24 %), мягкие светлые акценты на верхних гранях (к сиреневому);
- низ тела у пола темнее (×0.74 у пола, к ~10 ст. высоты — без изменения);
- оттенки по частям: шея холоднее и светлее, плечи теплее, передние лапы глубже, задние темнее и теплее, хвост к кончику
  в индиго, морда сверху светлее, челюсть снизу темнее, кости крыльев темнее (перепонки — без изменений);
- грудь: верх пластин светлее, низ темнее (свет сверху + щели) — форма читается.
Основной фиолетовый тот же (сдвиги оттенка ≤ 8°, яркость частей ×0.86…1.10; средняя яркость чешуи и ткани
в каждом атласе выровнена по v1 — дракон не темнеет, растёт только разница света и тени), кольца D39 и контуры — из v1.
Металл, шероховатость и маска свечения у v3 — те же, что у v2 (Boss10v2_maps.json), новые — только цвета.

Пишет assets/textures/art/boss10_v3/Boss10v3_<группа>_color.png и <папка превью>/atlas_<группа>.png (v2 | v3).
Карты v1 и v2 не меняются.

  python scripts/boss10_tex_v3.py <папка карт v7_tex_v2> <папка превью>
"""

import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boss10_tex_v2 as V2  # noqa: E402

REPO = V2.REPO
DST = os.path.join(REPO, "assets", "textures", "art", "boss10_v3")
REGIONS = V2.REGIONS

# ── числа внешнего вида v3 ─────────────────────────────────────────────────────────────────────────────────────
NEAR = {"scale": 0.42, "gold": 0.40, "cream": 0.60, "cloth": 0.48, "crystal": 0.92}
FAR = {"scale": 0.56, "gold": 0.66, "cream": 0.78, "cloth": 0.64, "crystal": 0.95}
TIGHT = {"scale": 0.70, "gold": 0.72, "cream": 0.80, "cloth": 0.75, "crystal": 1.0}  # щели 0.5 ст.
UP = {"scale": 0.26, "gold": 0.30, "cream": 0.12, "cloth": 0.18, "crystal": 0.05}
KEY = {"scale": 0.24, "gold": 0.28, "cream": 0.10, "cloth": 0.16, "crystal": 0.04}
TOP_ACCENT = ("C9B6FF", 0.20)  # светлый акцент верхних граней чешуи (цвет sRGB, наибольшая доля)
HUE_UP, SAT_UP = -9.0, -0.06
GROUND, GROUND_TOP, TAIL_DARK = 0.74, 0.28, 0.12  # у пола ×0.74, к 0.28 высоты (≈10 ст.) — 1
BRIGHT = 0.92  # средняя видимая яркость атласа от v1 (v2 — около 0.8)

# оттенок (градусы) и яркость по крупным частям (только чешуя)
FAMILY = {
    "neck": (-7.0, 1.10),
    "body": (0.0, 1.0),
    "shoulder": (7.0, 1.05),
    "foreleg": (-4.0, 0.88),
    "hindleg": (5.0, 0.87),
    "tail": (-8.0, 0.95),
    "head": (0.0, 1.07),
    "jaw": (3.0, 0.88),
    "wingbone": (-4.0, 0.86),
    "other": (0.0, 1.0),
}


def family(name):
    if name.startswith(("Neck", "Collar")):
        return "neck"
    if name.startswith("Body"):
        return "body"
    if name.startswith(("UpperArm", "Pauldron", "Mantle")):
        return "shoulder"
    if name.startswith(("Forearm", "Paw")):
        return "foreleg"
    if name.startswith(("Thigh", "Shin", "Meta", "HindPaw")):
        return "hindleg"
    if name.startswith("Tail"):
        return "tail"
    if name == "Head":
        return "head"
    if name == "Jaw":
        return "jaw"
    if name.startswith(("WingArm", "WingFore", "Finger")):
        return "wingbone"
    return "other"


def median3(a):
    """Медиана 3×3 (убирает смешанные номера частей на краях островов)."""
    p = np.pad(a, 1, mode="edge")
    stack = np.stack([p[i:i + a.shape[0], j:j + a.shape[1]] for i in range(3) for j in range(3)], 0)
    return np.median(stack, 0)


def family_maps(region, bake, names, island):
    pid = np.round(np.load(os.path.join(bake, f"{region}_part.npy"))[..., 0] * 100).astype(int)
    pid = np.clip(pid, 0, len(names) - 1)
    hue = np.zeros(pid.shape, np.float32)
    val = np.ones(pid.shape, np.float32)
    tail_k = np.zeros(pid.shape, np.float32)
    for i, name in enumerate(names):
        sel = pid == i
        if not sel.any():
            continue
        h, v = FAMILY[family(name)]
        hue[sel], val[sel] = h, v
        if name.startswith("Tail"):
            tail_k[sel] = (int(name[4:]) - 1) / 6.0  # 0 — у корня, 1 — кончик
    hue, val, tail_k = median3(hue), median3(val), median3(tail_k)
    hue[~island], val[~island] = 0, 1
    return hue, val, tail_k


def compose(region, bake, names):
    c1 = np.asarray(Image.open(os.path.join(V2.SRC, f"Boss10_{region}_color.png")).convert("RGB"), np.float32) / 255
    island = c1.sum(-1) > 0.03
    geo = np.load(os.path.join(bake, f"{region}_geo.npy"))
    nrm = np.load(os.path.join(bake, f"{region}_nrm.npy")) * 2 - 1
    kd = np.array(V2.KEY_DIR, np.float32)
    n_l = np.clip((nrm * (kd / np.linalg.norm(kd))).sum(-1), -1, 1)
    ao_n = np.clip(np.load(os.path.join(bake, f"{region}_ao_near.npy"))[..., 0], 0, 1)
    ao_f = np.clip(np.load(os.path.join(bake, f"{region}_ao_far.npy"))[..., 0], 0, 1)
    ao_t = np.clip(np.load(os.path.join(bake, f"{region}_ao_tight.npy"))[..., 0], 0, 1)
    up = geo[..., 0] * 2 - 1
    height, along = geo[..., 1], geo[..., 2]
    cls, (h, s, v) = V2.classes(c1)
    fam_hue, fam_val, tail_k = family_maps(region, bake, names, island)

    sc = cls["scale"]
    h2 = np.where(sc, h + HUE_UP * up + fam_hue, h)
    s2 = np.where(sc, np.clip(s + SAT_UP * np.maximum(up, 0) - 0.5 * SAT_UP * np.maximum(-up, 0), 0, 1), s)
    v2 = np.where(sc, np.clip(v * fam_val * (1 - 0.08 * tail_k), 0, 1), v)
    base = V2.hsv_rgb(h2, s2, v2).astype(np.float32)
    lin = V2.srgb_lin(base)

    pc = V2.per_class
    near, far, tight = pc(cls, NEAR), pc(cls, FAR), pc(cls, TIGHT)
    occl = (near + (1 - near) * ao_n) * (far + (1 - far) * ao_f) * (tight + (1 - tight) * ao_t)
    light = (1 + pc(cls, UP) * up) * (1 + pc(cls, KEY) * n_l)
    ground = GROUND + (1 - GROUND) * V2.smooth(height, 0.0, GROUND_TOP)
    tail = 1 - TAIL_DARK * V2.smooth(along, 0.6, 1.0)
    shade = occl * light * ground * tail
    shade = np.where(cls["crystal"], np.maximum(shade, 0.95), shade)
    out = lin * shade[..., None]

    # мягкий светлый акцент на верхних гранях чешуи (к сиреневому), только где не затенено
    acc = V2.srgb_lin(np.array([int(TOP_ACCENT[0][i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32))
    k_acc = (TOP_ACCENT[1] * V2.smooth(np.maximum(up, n_l), 0.45, 0.95) * ao_n * ao_t * sc)[..., None]
    out = out * (1 - k_acc) + acc * shade[..., None] * k_acc

    # золото — как в v2, контраст сильнее
    g = cls["gold"]
    hi = V2.srgb_lin(np.array(V2.GOLD_HI, np.float32))
    k_hi = (0.4 * V2.smooth(np.maximum(up, n_l), 0.35, 0.95) * ao_n)[..., None]
    lo = V2.srgb_lin(np.array(V2.GOLD_LO, np.float32))
    k_lo = (0.75 * V2.smooth(-np.minimum(up, n_l), 0.0, 0.8))[..., None]
    gold = out * (1 - k_lo + k_lo * lo)
    gold = gold * (1 - k_hi) + hi * np.maximum(shade, 0.8)[..., None] * k_hi
    out = np.where(g[..., None], gold, out)

    # яркость не падает: средняя видимая (sRGB) яркость чешуи и ткани в атласе — BRIGHT от v1 (тени
    # глубже, верх светлее, общий тон тот же); подбор множителя — несколько шагов
    lum_w = np.array([0.2126, 0.7152, 0.0722], np.float32)
    for key in ("scale", "cloth"):  # золото не выравнивается: иначе выцветает в лимонный
        m = cls[key] & island
        if m.sum() < 500:
            continue
        target = BRIGHT * float((c1[m] @ lum_w).mean())
        k = 1.0
        for _ in range(4):
            seen = float((V2.lin_srgb(out[m] * k) @ lum_w).mean())
            k *= (target / max(seen, 1e-6)) ** 2.2
        out[m] = out[m] * min(max(k, 1.0), 1.8)
    color = V2.lin_srgb(out)
    color = np.where(island[..., None], color, c1)
    os.makedirs(DST, exist_ok=True)
    Image.fromarray((color * 255 + 0.5).astype(np.uint8)).save(os.path.join(DST, f"Boss10v3_{region}_color.png"))
    return color


def main():
    bake, preview = sys.argv[1], sys.argv[2]
    os.makedirs(preview, exist_ok=True)
    names = json.load(open(os.path.join(bake, "parts.json"), encoding="utf-8"))
    for r in REGIONS:
        c3 = compose(r, bake, names)
        c2 = np.asarray(Image.open(os.path.join(V2.DST, f"Boss10v2_{r}_color.png")).convert("RGB"), np.float32) / 255
        both = np.concatenate([c2, c3], 1)
        Image.fromarray((both * 255 + 0.5).astype(np.uint8)).resize((1024, 512)).save(
            os.path.join(preview, f"atlas_v2_v3_{r}.png"))
        print("TEX3", r, flush=True)


if __name__ == "__main__":
    main()
