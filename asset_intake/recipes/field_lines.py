"""Recipe: field lines — glowing electric (or magnetic-dipole) field lines traced from point charges by code, with
charge spheres and direction arrows. Covers single-charge radial fields, dipoles, like charges repelling, and the
arcs between capacitor pads (use --plane for lines in one plane).

Charges JSON: [{"q": 1, "pos": [-1, 0, 0]}, {"q": -1, "pos": [1, 0, 0]}]
Run:  python field_lines.py -- --preview out.png [--preset dipole|radial|like] [--charges c.json] [--lines 24]
      [--plane] [--color 1,0.2,0.75] [--glb out.glb]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import recipe_common as rc  # noqa: E402

PRESETS = {
    "dipole": [{"q": 1, "pos": [-1.0, 0, 0]}, {"q": -1, "pos": [1.0, 0, 0]}],
    "radial": [{"q": 1, "pos": [0, 0, 0]}],
    "like": [{"q": 1, "pos": [-1.0, 0, 0]}, {"q": 1, "pos": [1.0, 0, 0]}],
}


def field(p, charges):
    e = Vector((0, 0, 0))
    for c in charges:
        d = p - c["v"]
        r = max(d.length, 1e-3)
        e += c["q"] * d / (r ** 3)
    return e


def seeds(n, plane):
    if plane:
        return [Vector((math.cos(2 * math.pi * k / n), math.sin(2 * math.pi * k / n), 0)) for k in range(n)]
    pts = []
    golden = math.pi * (3 - math.sqrt(5))
    for k in range(n):
        y = 1 - 2 * (k + 0.5) / n
        r = math.sqrt(1 - y * y)
        th = golden * k
        pts.append(Vector((math.cos(th) * r, y, math.sin(th) * r)))
    return pts


def trace(start, charges, step=0.02, max_steps=900, bound=4.0):
    pts = [start.copy()]
    p = start.copy()
    for _ in range(max_steps):
        e = field(p, charges)
        if e.length < 1e-6:
            break
        k1 = e.normalized()
        mid = p + k1 * step / 2
        k2 = field(mid, charges).normalized()
        p = p + k2 * step
        pts.append(p.copy())
        if p.length > bound:
            break
        if any(c["q"] < 0 and (p - c["v"]).length < 0.12 for c in charges):
            break
    return pts


def curve_from(points, name, radius, mat):
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = radius
    cd.bevel_resolution = 3
    sp = cd.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for i, v in enumerate(points):
        sp.points[i].co = (v.x, v.y, v.z, 1)
    o = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


def arrow(at, direction, name, mat, size=0.05):
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=size, radius2=0, depth=size * 2.2, location=at)
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(mat)
    return o


def build(charges, n_lines, plane, color):
    rc.world_color((0.006, 0.007, 0.014, 1), 1.0)
    rc.area_light("key", (3, -4, 5), (40, 0, 35), 600, size=3)
    rc.area_light("rim", (-4, 4, 2), (-60, 0, -130), 300, size=3, color=(0.7, 0.8, 1.0))
    for c in charges:
        c["v"] = Vector(c["pos"])
    line_mat = rc.mat_emission("field_line", color + (1,), 2.2)
    halo_mat = rc.mat_principled("field_halo", color + (1,), roughness=0.5, emission=color + (1,), strength=0.6,
                                 alpha=0.06)
    arrow_mat = rc.mat_emission("field_arrow", tuple(min(1, x * 1.2 + 0.2) for x in color) + (1,), 3.0)
    pos_mat = rc.mat_principled("charge_pos", (0.85, 0.05, 0.05, 1), roughness=0.15, coat=1.0,
                                emission=(1, 0.1, 0.1, 1), strength=0.4)
    neg_mat = rc.mat_principled("charge_neg", (0.05, 0.15, 0.9, 1), roughness=0.15, coat=1.0,
                                emission=(0.1, 0.2, 1, 1), strength=0.4)
    sources = [c for c in charges if c["q"] > 0] or charges
    count = 0
    for si, c in enumerate(sources):
        for k, d in enumerate(seeds(n_lines, plane)):
            pts = trace(c["v"] + d * 0.14, charges if c["q"] > 0 else [{"q": -x["q"], "v": x["v"]} for x in charges])
            if len(pts) < 8:
                continue
            curve_from(pts, "line_%d_%d" % (si, k), 0.007, line_mat)
            curve_from(pts, "halo_%d_%d" % (si, k), 0.025, halo_mat)
            mid = len(pts) // 2
            arrow(pts[mid], (pts[mid + 1] - pts[mid]), "arrow_%d_%d" % (si, k), arrow_mat)
            count += 1
    for i, c in enumerate(charges):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.2, location=c["v"])
        s = bpy.context.active_object
        s.name = "charge_%d" % i
        bpy.ops.object.shade_smooth()
        s.data.materials.append(pos_mat if c["q"] > 0 else neg_mat)
        rc.empty("anchor_charge_%d" % i, c["v"] + Vector((0, 0, 0.2)))
    return count


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--preview", required=True)
    p.add_argument("--preset", default="dipole", choices=sorted(PRESETS))
    p.add_argument("--charges", default="")
    p.add_argument("--lines", type=int, default=28)
    p.add_argument("--plane", action="store_true")
    p.add_argument("--color", default="1,0.2,0.75")
    p.add_argument("--glb", default="")
    p.add_argument("--samples", type=int, default=48)
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    a = p.parse_args(rc.args_after_dashes())
    charges = json.load(open(a.charges)) if a.charges else [dict(c) for c in PRESETS[a.preset]]
    color = tuple(float(x) for x in a.color.split(","))
    rc.reset()
    n = build(charges, a.lines, a.plane, color)
    rc.camera((0.0, -7.4, 2.8), target=(0, 0, -0.1), lens=40, dof_target=(0, 0, 0), fstop=11)
    rc.render_settings(a.width, a.height, a.samples)
    rc.render(a.preview)
    if a.glb:
        rc.export_glb(a.glb)
    rc.done({"recipe": "field_lines", "preview": a.preview, "glb": a.glb or None, "lines": n,
             "anchors": rc.anchors(["anchor_charge_%d" % i for i in range(len(charges))]),
             "params": {k: v for k, v in vars(a).items() if k != "charges"}})


if __name__ == "__main__":
    main()
