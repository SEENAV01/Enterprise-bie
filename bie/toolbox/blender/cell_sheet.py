"""Blender (bpy) script: build a sheet of epithelial cells and export it as glTF (Task 046a, route C; Task 046 Part B:
every member of the family).

Run by ``bie.toolbox.adapters.blender.cell_sheet`` in its own process:
    python cell_sheet.py --out sheet.glb --kind columnar --rows 5 --cols 7 --seed 7
(or ``blender -b --python cell_sheet.py -- --out ...``). Objects are named so the web block (``blocks/toolbox/benchmark.tsx``,
``cell_sheet``) finds them: ``cell_<layer>_<r>_<c>``, ``nucleus_<layer>_<r>_<c>``, ``cilium_<r>_<c>_<k>``,
``microvillus_<r>_<c>_<k>``, ``basement_membrane``, ``underlying_tissue``, ``gland_duct``. Kinds: the textbook shapes
squamous, cuboidal, columnar, and the family members simple_squamous, simple_cuboidal (with microvilli), simple_columnar,
ciliated (cilia on top), pseudostratified (every cell touches the base, nuclei at different heights, cilia), stratified
(= stratified_squamous), stratified_cuboidal, stratified_columnar, transitional (dome cells), keratinised (dead flat
layers on top), glandular (the sheet folds into a duct). The same block renders a Blender sheet (``src``) and a
procedural one (route A); the geometry is the same recipe, so route C is measured against route A on equal terms.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys

import bpy

SHAPES = {                    # radius, height, nucleus (sx, sy, sz) as fractions, nucleus height as fraction
    "squamous": (0.62, 0.2, (0.42, 0.42, 0.3), 0.5),
    "cuboidal": (0.5, 0.95, (0.42, 0.42, 0.34), 0.5),
    "columnar": (0.42, 2.3, (0.5, 0.5, 0.16), 0.28),
    "dome": (0.56, 0.9, (0.42, 0.42, 0.34), 0.5),
    "keratin": (0.62, 0.14, None, 0.5),
}
MEMBERS = {                   # layers from the base up; the top layer's shape names the member
    "squamous": ["squamous"], "cuboidal": ["cuboidal"], "columnar": ["columnar"],
    "simple_squamous": ["squamous"], "simple_cuboidal": ["cuboidal"], "simple_columnar": ["columnar"], "ciliated": ["columnar"],
    "pseudostratified": ["columnar"], "stratified": ["cuboidal", "dome", "dome", "squamous", "squamous"],
    "stratified_squamous": ["cuboidal", "dome", "dome", "squamous", "squamous"], "stratified_cuboidal": ["cuboidal", "cuboidal"],
    "stratified_columnar": ["cuboidal", "columnar"], "transitional": ["cuboidal", "dome", "dome"],
    "keratinised": ["cuboidal", "dome", "squamous", "keratin", "keratin"], "glandular": ["cuboidal"], "generic": ["cuboidal"],
}
COLOURS = {"cytoplasm": (0.93, 0.55, 0.58, 1.0), "dead": (0.73, 0.65, 0.55, 1.0), "nucleus": (0.36, 0.2, 0.62, 1.0),
           "membrane": (0.31, 0.55, 0.7, 1.0), "tissue": (0.16, 0.25, 0.33, 1.0), "cilia": (0.96, 0.84, 0.63, 1.0)}


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


def hair(name, x, y, z, length, radius, mat, tilt=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=radius, depth=length, location=(x, y, z + length / 2))
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_euler = (tilt, 0, 0)
    obj.data.materials.append(mat)
    return obj


def build(kind: str, rows: int, cols: int, seed: int) -> dict:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rng = random.Random(seed)
    mats = {k: material(k, v) for k, v in COLOURS.items()}
    layers = MEMBERS[kind]
    cells = hairs = 0
    width = depth = 0.0
    z0 = 0.0
    for li, shape_name in enumerate(layers):
        radius, height, frac, at = SHAPES[shape_name]
        dx, dy = math.sqrt(3) * radius, 1.5 * radius
        top_layer = li == len(layers) - 1
        for r in range(rows):
            for c in range(cols):
                x = (c - (cols - 1) / 2) * dx + (dx / 2 if r % 2 else 0.0)
                y = (r - (rows - 1) / 2) * dy
                h = height * (1 + rng.uniform(-0.06, 0.06))
                if kind == "pseudostratified":
                    h = height * (0.55 + 0.45 * rng.random())
                tag = f"{li}_{r}_{c}"
                dead = shape_name == "keratin"
                hex_cell(f"cell_{tag}", x, y, z0, radius * 0.98, h, mats["dead" if dead else "cytoplasm"])
                if not dead:
                    at_here = 0.25 + 0.5 * rng.random() if kind == "pseudostratified" else at
                    nucleus(f"nucleus_{tag}", x, y, z0, radius, h, frac, at_here, mats["nucleus"])
                cells += 1
                if top_layer and kind in ("ciliated", "pseudostratified"):
                    for k in range(7):
                        a, rad = (k / 7) * math.tau, radius * 0.45 * rng.random()
                        hair(f"cilium_{r}_{c}_{k}", x + math.cos(a) * rad, y + math.sin(a) * rad, z0 + h, 0.55, 0.022, mats["cilia"],
                             tilt=rng.uniform(-0.25, 0.25))
                        hairs += 1
                if top_layer and kind == "simple_cuboidal":
                    for k in range(5):
                        a, rad = (k / 5) * math.tau + rng.random(), radius * 0.5 * math.sqrt(rng.random())
                        hair(f"microvillus_{r}_{c}_{k}", x + math.cos(a) * rad, y + math.sin(a) * rad, z0 + h, 0.08, 0.022, mats["cytoplasm"])
                        hairs += 1
        z0 += height * (0.9 if shape_name == "keratin" else 0.86)
        width, depth = max(width, cols * dx), max(depth, rows * dy)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.05))
    membrane = bpy.context.active_object
    membrane.name = "basement_membrane"
    membrane.scale = (width + 0.7, depth + 0.7, 0.09)
    membrane.data.materials.append(mats["membrane"])
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.56))
    tissue = bpy.context.active_object
    tissue.name = "underlying_tissue"
    tissue.scale = (width + 0.7, depth + 0.7, 0.9)
    tissue.data.materials.append(mats["tissue"])
    if kind == "glandular":
        bpy.ops.mesh.primitive_torus_add(major_radius=0.9, minor_radius=0.28, major_segments=24, minor_segments=10, location=(0, 0, -0.35))
        duct = bpy.context.active_object
        duct.name = "gland_duct"
        duct.rotation_euler = (math.pi / 2, 0, 0)
        duct.data.materials.append(mats["cytoplasm"])
    return {"kind": kind, "cells": cells, "hairs": hairs, "layers": len(layers), "width": round(width, 3), "depth": round(depth, 3),
            "top": round(z0, 3)}


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--kind", default="columnar", choices=sorted(MEMBERS))
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
