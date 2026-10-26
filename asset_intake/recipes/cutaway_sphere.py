"""Recipe: cutaway sphere — concentric layers with one wedge cut out, so the inside shows (Earth's interior, a cell,
a fruit, an atom model, a planet, a ball bearing). The outer surface can be a procedural planet (oceans and land) or
a plain colour; the innermost layer can glow. Anchors sit on each layer's cut face for code labels.

Layers JSON (outside first): [{"name":"Crust","radius":1.0,"color":[0.55,0.42,0.3]}, ...,
{"name":"Inner core","radius":0.2,"color":[1,0.85,0.5],"glow":6}]

Run:  python cutaway_sphere.py -- --preview out.png [--layers layers.json] [--surface planet|plain] [--glb out.glb]
      [--wedge 90] [--spin 0] [--frames 120]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402

import recipe_common as rc  # noqa: E402

EARTH = [
    {"name": "Crust", "radius": 1.0, "color": [0.32, 0.22, 0.15]},
    {"name": "Mantle", "radius": 0.94, "color": [0.75, 0.22, 0.05], "glow": 0.15},
    {"name": "Outer core", "radius": 0.55, "color": [1.0, 0.5, 0.08], "glow": 0.8},
    {"name": "Inner core", "radius": 0.22, "color": [1.0, 0.85, 0.45], "glow": 3.0},
]


def planet_material():
    m = bpy.data.materials.new("planet_surface")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.2
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.6
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position = 0.48; e[0].color = (0.01, 0.06, 0.22, 1)      # ocean
    e[1].position = 0.53; e[1].color = (0.05, 0.18, 0.05, 1)      # land
    e3 = e.new(0.66); e3.color = (0.28, 0.22, 0.12, 1)            # dry land
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    rough = nt.nodes.new("ShaderNodeMath"); rough.operation = "GREATER_THAN"; rough.inputs[1].default_value = 0.5
    nt.links.new(noise.outputs["Fac"], rough.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.15; mr.inputs["To Max"].default_value = 0.8
    nt.links.new(rough.outputs[0], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    return m


def layer_material(spec):
    col = tuple(spec["color"]) + (1.0,)
    glow = float(spec.get("glow", 0))
    return rc.mat_principled("m_" + spec["name"], col, roughness=0.6,
                             emission=col if glow else None, strength=glow)


def cutter(wedge_deg):
    """A box that removes the x>0, y<0, z>0 region (a 90 degree wedge from the top); wider wedges rotate it."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(1.5, -1.5, 1.5))
    c = bpy.context.active_object
    c.name = "cutter"
    c.scale = (3, 3, 3)
    c.hide_render = True
    c.display_type = "WIRE"
    return c


def build(layers, surface, wedge_deg, spin, frames):
    rc.world_color((0.004, 0.005, 0.009, 1), 1.0)
    rc.area_light("key", (4, -3, 4), (45, 0, 50), 500, size=3)
    rc.area_light("rim", (-4, 3, 2), (-60, 0, -130), 300, size=3, color=(0.6, 0.75, 1.0))
    cut = cutter(wedge_deg)
    root = rc.empty("globe_root", (0, 0, 0))
    for i, spec in enumerate(layers):
        r = float(spec["radius"])
        bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=r, location=(0, 0, 0))
        s = bpy.context.active_object
        s.name = "layer_%d" % i
        bpy.ops.object.shade_smooth()
        if i + 1 < len(layers):
            # make this layer a hollow shell, so its cut face is a ring and never covers the layers inside it
            bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=float(layers[i + 1]["radius"]),
                                                 location=(0, 0, 0))
            hole = bpy.context.active_object
            bpy.context.view_layer.objects.active = s
            shell = s.modifiers.new("shell", "BOOLEAN")
            shell.operation = "DIFFERENCE"
            shell.object = hole
            shell.solver = "EXACT"
            bpy.ops.object.modifier_apply(modifier="shell")
            bpy.data.objects.remove(hole, do_unlink=True)
        mod = s.modifiers.new("cut", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cut
        mod.solver = "EXACT"
        bpy.ops.object.modifier_apply(modifier="cut")
        mats = [layer_material(spec)]
        if i == 0 and surface == "planet":
            mats = [planet_material(), layer_material(spec)]
        for m in mats:
            s.data.materials.append(m)
        if len(mats) == 2:
            # faces on the cut planes (axis-aligned normals) get the layer colour; the rest is the planet surface
            for poly in s.data.polygons:
                n = poly.normal
                on_cut = (abs(n.x) > 0.999 or abs(n.y) > 0.999 or abs(n.z) > 0.999) and \
                    (poly.center.x >= -1e-4 and poly.center.y <= 1e-4 and poly.center.z >= -1e-4)
                poly.material_index = 1 if on_cut else 0
        s.parent = root
        # anchor on the horizontal cut face, between this radius and the next one in
        inner = float(layers[i + 1]["radius"]) if i + 1 < len(layers) else 0.0
        mid = (r + inner) / 2
        a = rc.empty("anchor_" + spec["name"], (mid * 0.72, -mid * 0.72, 0.003))
        a.parent = root
    root.rotation_euler = (0, 0, math.radians(spin))
    if frames:
        root.rotation_euler.z = math.radians(spin)
        root.keyframe_insert("rotation_euler", frame=1)
        root.rotation_euler.z = math.radians(spin + 40)
        root.keyframe_insert("rotation_euler", frame=frames)
        root.rotation_euler.z = math.radians(spin)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--preview", required=True)
    p.add_argument("--layers", default="")
    p.add_argument("--surface", default="planet", choices=["planet", "plain"])
    p.add_argument("--wedge", type=float, default=90)
    p.add_argument("--spin", type=float, default=0)
    p.add_argument("--glb", default="")
    p.add_argument("--frames", type=int, default=0)
    p.add_argument("--samples", type=int, default=48)
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    a = p.parse_args(rc.args_after_dashes())
    layers = json.load(open(a.layers)) if a.layers else EARTH
    rc.reset()
    build(layers, a.surface, a.wedge, a.spin, a.frames)
    rc.camera((3.3, -3.9, 2.6), target=(0, 0, 0.0), lens=50, dof_target=(0.3, -0.3, 0.2), fstop=8)
    rc.render_settings(a.width, a.height, a.samples)
    rc.render(a.preview)
    if a.glb:
        rc.export_glb(a.glb)
    rc.done({"recipe": "cutaway_sphere", "preview": a.preview, "glb": a.glb or None,
             "layers": [s["name"] for s in layers],
             "anchors": rc.anchors(["anchor_" + s["name"] for s in layers]),
             "params": {k: v for k, v in vars(a).items() if k != "layers"}})


if __name__ == "__main__":
    main()
