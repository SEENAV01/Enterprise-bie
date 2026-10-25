"""Blender (bpy) script: build a sheet of epithelial cells and export it as glTF (Task 046a, route C).

Run by ``bie.toolbox.adapters.blender.cell_sheet`` in its own process:
    python cell_sheet.py --out sheet.glb --kind columnar --rows 5 --cols 7 --seed 7
(or ``blender -b --python cell_sheet.py -- --out ...``). Objects are named so the web block can find them:
``cell_<r>_<c>``, ``nucleus_<r>_<c>``, ``basement_membrane``. Kinds follow the textbook shapes: squamous (flat
plates), cuboidal (as tall as wide), columnar (tall pillars, nucleus near the base), and stratified (squamous
cells on top of rounder layers).
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys

import bpy

SHAPES = {                    # radius, height, nucleus (sx, sy, sz) as fractions, nucleus height as fraction
    "squamous": (0.62, 0.22, (0.42, 0.42, 0.45), 0.55),
    "cuboidal": (0.5, 0.95, (0.42, 0.42, 0.34), 0.5),
    "columnar": (0.42, 2.3, (0.5, 0.5, 0.16), 0.3),
}
COLOURS = {"cytoplasm": (0.93, 0.55, 0.58, 1.0), "nucleus": (0.36, 0.2, 0.62, 1.0), "membrane": (0.55, 0.72, 0.86, 1.0)}


def material(name, rgba, roughness=0.55):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def hex_cell(name, x, y, z, radius, height, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=radius, depth=height, location=(x, y, z + height / 2))
    obj = bpy.context.active_object
    obj.name = name
    bevel = obj.modifiers.new("soft", "BEVEL")
    bevel.width = min(0.06, height / 4)
    bevel.segments = 2
    obj.data.materials.append(mat)
    return obj


def nucleus(name, x, y, z, radius, height, frac, at, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=1.0, location=(x, y, z + height * at))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (radius * frac[0] * 1.6, radius * frac[1] * 1.6, max(0.06, height * frac[2]))
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return obj


def build(kind: str, rows: int, cols: int, seed: int) -> dict:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rng = random.Random(seed)
    mats = {k: material(k, v) for k, v in COLOURS.items()}
    layers = [("squamous", 0.0)] if kind == "squamous" else [(kind, 0.0)]
    if kind == "stratified":
        layers = [("cuboidal", 0.0), ("cuboidal", 0.95), ("squamous", 1.9)]
    cells = 0
    width = depth = 0.0
    for li, (shape, z0) in enumerate(layers):
        radius, height, frac, at = SHAPES[shape]
        dx, dy = math.sqrt(3) * radius, 1.5 * radius
        for r in range(rows):
            for c in range(cols):
                x = (c - (cols - 1) / 2) * dx + (dx / 2 if r % 2 else 0.0)
                y = (r - (rows - 1) / 2) * dy
                h = height * (1 + rng.uniform(-0.06, 0.06))
                tag = f"{li}_{r}_{c}" if len(layers) > 1 else f"{r}_{c}"
                hex_cell(f"cell_{tag}", x, y, z0, radius * 0.98, h, mats["cytoplasm"])
                nucleus(f"nucleus_{tag}", x, y, z0, radius, h, frac, at, mats["nucleus"])
                cells += 1
        width, depth = max(width, cols * dx), max(depth, rows * dy)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.04))
    membrane = bpy.context.active_object
    membrane.name = "basement_membrane"
    membrane.scale = (width + 0.6, depth + 0.6, 0.08)
    membrane.data.materials.append(mats["membrane"])
    return {"kind": kind, "cells": cells, "layers": len(layers), "width": round(width, 3), "depth": round(depth, 3)}


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--kind", default="columnar", choices=("squamous", "cuboidal", "columnar", "stratified"))
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--cols", type=int, default=7)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)
    info = build(args.kind, args.rows, args.cols, args.seed)
    # Blender's own export: the glTF 2.0 binary; modifiers (the bevel) applied, Y up for three.js.
    bpy.ops.export_scene.gltf(filepath=args.out, export_format="GLB", export_apply=True, export_yup=True)
    info.update(blender=bpy.app.version_string, out=args.out)
    print("BIE_BLENDER_RESULT " + json.dumps(info))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(argv)
