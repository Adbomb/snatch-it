"""Король-дракон №10, этап C.1: текстуры версии 2 — тот же рисунок и палитра D39, больше объёма.

Основа — цвет версии 1 (assets/textures/art/boss10/Boss10_<группа>_color.png: палитра, кольца D39, своя окклюзия),
поверх — карты из scripts/blender/dragon10/v7_tex_v2.py (та же развёртка, что у загруженных мешей):
- тени между частями: окклюзия всех частей вместе (ao_near — щели между пластинами, под золотыми накладками, у
  суставов; ao_far — под брюхом, между лапами, под крыльями);
- свет сверху: верхние грани светлее, нижние темнее; мягкий свет сверху-спереди-слева (по нормали грани: грани к
  свету светлее, от света — темнее, так читается объём и вертикальных граней); у пола (лапы, низ брюха) темнее;
- оттенки фиолетового по крупным формам: сверху чуть холоднее и светлее, снизу глубже и теплее, к кончику хвоста
  чуть темнее (основной фиолетовый тот же);
- золото объёмнее: сильнее свет сверху, светлые блики на верхних гранях, янтарная глубина снизу;
- кристаллы не темнеют (светятся).
Контуры D39 не размываются: все множители плавные, кольца остаются из версии 1.

Кроме цвета (для проверки в Studio, подключаются только после просмотра):
- _metal — металл золота (MetalnessMap SurfaceAppearance), _rough — шероховатость по материалам;
- _glow — маска свечения кристаллов (EmissiveMaskContent).
Пишет assets/textures/art/boss10_v2/Boss10v2_<группа>_{color,metal,rough,glow}.png и <папка>/atlas_<группа>.png
(версия 1 | версия 2). Карты версии 1 не меняются.

  python scripts/boss10_tex_v2.py <папка карт v7_tex_v2> <папка превью>
"""

import os
import sys

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "assets", "textures", "art", "boss10")
DST = os.path.join(REPO, "assets", "textures", "art", "boss10_v2")
REGIONS = ["BodyA", "BodyB", "Head", "Front", "Hind", "Tail"]

# ── числа внешнего вида (подобраны по превью; менять здесь) ─────────────────────────────────────────────────
NEAR = {"scale": 0.50, "gold": 0.45, "cream": 0.66, "cloth": 0.55, "crystal": 0.92}  # окклюзия 1.4 ст.: наименьший множитель
FAR = {"scale": 0.74, "gold": 0.78, "cream": 0.84, "cloth": 0.76, "crystal": 0.95}  # окклюзия 6 ст.
UP = {"scale": 0.14, "gold": 0.22, "cream": 0.08, "cloth": 0.12, "crystal": 0.05}  # свет сверху: ±доля
KEY = {"scale": 0.12, "gold": 0.22, "cream": 0.07, "cloth": 0.10, "crystal": 0.04}  # свет сверху-спереди: ±доля
KEY_DIR = (0.35, -0.55, 0.76)  # оси Blender: лицо дракона −Y, левый бок +X
GROUND = 0.86  # у пола; к 6 стадам высоты — 1
HUE_UP = -9.0  # градусов: верх — холоднее (к синему), низ — теплее (к пурпуру)
SAT_UP = -0.06  # верх чуть светлее по насыщенности
TAIL_DARK = 0.08  # к кончику хвоста темнее на столько
GOLD_HI = (1.0, 0.90, 0.58)  # блик золота сверху (sRGB)
GOLD_LO = (1.0, 0.80, 0.58)  # глубина золота снизу (множитель sRGB)
ROUGH = {"scale": 0.55, "gold": 0.30, "cream": 0.45, "cloth": 0.85, "crystal": 0.12}
METAL_GOLD = 1.0


def srgb_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def rgb_hsv(c):
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    mx, mn = c.max(-1), c.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-6
    rr = m & (mx == r)
    gg = m & (mx == g) & ~rr
    bb = m & ~rr & ~gg
    h[rr] = ((g - b)[rr] / d[rr]) % 6
    h[gg] = (b - r)[gg] / d[gg] + 2
    h[bb] = (r - g)[bb] / d[bb] + 4
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0)
    return h * 60.0, s, mx


def hsv_rgb(h, s, v):
    h = (h % 360.0) / 60.0
    i = np.floor(h).astype(int) % 6
    f = h - np.floor(h)
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    out = np.zeros(h.shape + (3,))
    for k, (a, b, c) in enumerate(((v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q))):
        sel = i == k
        out[sel] = np.stack([a[sel], b[sel], c[sel]], -1)
    return out


def smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def classes(c):
    """Материал по цвету версии 1 (палитра D39 — несколько чистых цветов): золото, кость/мех, кристалл, ткань, чешуя."""
    h, s, v = rgb_hsv(c)
    gold = (h >= 24) & (h <= 56) & (s > 0.55) & (v > 0.28)
    cream = (s < 0.32) & (v > 0.62)
    crystal = (h >= 160) & (h <= 205) & (s > 0.4) & (v > 0.4)
    cloth = ((h < 16) | (h > 340)) & (s > 0.55) & (v > 0.25)
    scale = ~(gold | cream | crystal | cloth)
    return {"gold": gold, "cream": cream, "crystal": crystal, "cloth": cloth, "scale": scale}, (h, s, v)


def per_class(cls, table):
    out = np.zeros(cls["scale"].shape, np.float32)
    for k, m in cls.items():
        out[m] = table[k]
    return out


def compose(region, bake):
    c1 = np.asarray(Image.open(os.path.join(SRC, f"Boss10_{region}_color.png")).convert("RGB"), np.float32) / 255.0
    geo = np.load(os.path.join(bake, f"{region}_geo.npy"))
    nrm = np.load(os.path.join(bake, f"{region}_nrm.npy")) * 2 - 1
    kd = np.array(KEY_DIR, np.float32)
    n_l = np.clip((nrm * (kd / np.linalg.norm(kd))).sum(-1), -1, 1)
    ao_n = np.clip(np.load(os.path.join(bake, f"{region}_ao_near.npy"))[..., 0], 0, 1)
    ao_f = np.clip(np.load(os.path.join(bake, f"{region}_ao_far.npy"))[..., 0], 0, 1)
    up = geo[..., 0] * 2 - 1
    height, along = geo[..., 1], geo[..., 2]
    cls, (h, s, v) = classes(c1)

    # оттенок фиолетового по крупным формам (только чешуя и перепонки): верх холоднее и светлее, низ теплее
    sc = cls["scale"]
    h2 = np.where(sc, h + HUE_UP * up, h)
    s2 = np.where(sc, np.clip(s + SAT_UP * np.maximum(up, 0) - 0.5 * SAT_UP * np.maximum(-up, 0), 0, 1), s)
    base = hsv_rgb(h2, s2, v).astype(np.float32)

    lin = srgb_lin(base)
    near = per_class(cls, NEAR)
    far = per_class(cls, FAR)
    k_up = per_class(cls, UP)
    occl = (near + (1 - near) * ao_n) * (far + (1 - far) * ao_f)
    light = (1 + k_up * up) * (1 + per_class(cls, KEY) * n_l)
    ground = GROUND + (1 - GROUND) * smooth(height, 0.0, 0.16)
    tail = 1 - TAIL_DARK * smooth(along, 0.6, 1.0)
    shade = occl * light * ground * tail
    shade = np.where(cls["crystal"], np.maximum(shade, 0.95), shade)
    out = lin * shade[..., None]

    # золото: светлый блик сверху, янтарная глубина снизу
    g = cls["gold"]
    hi = srgb_lin(np.array(GOLD_HI, np.float32))
    k_hi = (0.45 * smooth(np.maximum(up, n_l), 0.3, 0.95) * ao_n)[..., None]
    lo = srgb_lin(np.array(GOLD_LO, np.float32))
    k_lo = (0.7 * smooth(-np.minimum(up, n_l), 0.0, 0.8))[..., None]
    gold = out * (1 - k_lo + k_lo * lo)
    gold = gold * (1 - k_hi) + hi * np.maximum(shade, 0.8)[..., None] * k_hi
    out = np.where(g[..., None], gold, out)

    color = lin_srgb(out)
    os.makedirs(DST, exist_ok=True)
    Image.fromarray((color * 255 + 0.5).astype(np.uint8)).save(os.path.join(DST, f"Boss10v2_{region}_color.png"))
    metal = np.where(g, METAL_GOLD, 0.0)
    rough = per_class(cls, ROUGH)
    glow = cls["crystal"].astype(np.float32)
    for name, arr in (("metal", metal), ("rough", rough), ("glow", glow)):
        Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8), "L").save(
            os.path.join(DST, f"Boss10v2_{region}_{name}.png"))
    share = {k: round(float(m.mean()), 3) for k, m in cls.items()}
    return c1, color, share


def main():
    bake, preview = sys.argv[1], sys.argv[2]
    os.makedirs(preview, exist_ok=True)
    for r in REGIONS:
        c1, c2, share = compose(r, bake)
        both = np.concatenate([c1, c2], 1)
        Image.fromarray((both * 255 + 0.5).astype(np.uint8)).resize((1024, 512)).save(
            os.path.join(preview, f"atlas_{r}.png"))
        print("TEX2", r, share, flush=True)


if __name__ == "__main__":
    main()
