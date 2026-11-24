"""Босс 5: руки Йети не заходят в глыбу во сне (замечание владельца 2026-11-24 «рука йети входит в стекло»).

Собирает игровую модель (как boss5_yeti.py quick), ставит позы sleep и alert с глыбой на земле и считает
пересечения треугольников рук (UpperArm, ForeArm, Hand, Fingers) с глыбой (Block, BlockFrame) по BVH.
Для подбора места — кандидаты положения глыбы (середина основания, поворот): печатает число пересечений у каждого.
Запуск: blender --background --factory-startup --python scripts/blender/boss5_block_clearance.py -- <репо> [x,y,yaw …]
Ничего не пишет.
"""

import os
import sys

import bpy
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import boss5_yeti as Y  # noqa: E402

ARMS = [f"{p}{s}" for p in ("UpperArm", "ForeArm", "Hand", "Fingers") for s in ("L", "R")]
BLOCK = ["Block", "BlockFrame", "BlockTop", "BlockTopFrame"]


def bvh(o):
    """Дерево в мировых координатах (FromObject берёт меш в локальных)."""
    mw = o.matrix_world
    return BVHTree.FromPolygons([mw @ v.co for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons])


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    cands = [tuple(float(v) for v in c.split(",")) for c in argv[1:]] or [None]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    col = bpy.data.collections.new("Yeti")
    bpy.context.scene.collection.children.link(col)
    Y.rest_frames()
    parts = {}
    for m in ("Head", "Body", "Limbs"):
        a = Y.build(m)
        obj = a.build(col)
        parts.update(Y._split_keep(obj, a, col))
    for c in cands:
        out = []
        for name in ("sleep", "alert", "inhale"):  # inhale — вдох клипа сна (boss5_yeti_anim: торс −15)
            P = dict(Y.POSES["sleep" if name == "inhale" else name])
            if name == "inhale":
                P["torso"], P["pelvis"] = -15.0, Y.V((0, 0.35, 1.02))
            if c is not None:
                P["block"] = Y.block_world((c[0], c[1], 0.06), yaw=c[2])
            Y.apply(parts, P)
            trees = {n: bvh(parts[n]) for n in ARMS + BLOCK if n in parts}
            hits = {}
            for a_ in ARMS:
                n = sum(len(trees[a_].overlap(trees[b])) for b in BLOCK if b in trees)
                if n:
                    hits[a_] = n
            out.append(f"{name}: {hits or 'чисто'}")
        print("CAND", c, " | ".join(out), flush=True)


main()
