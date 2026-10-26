"""Recipe: exploded layer stack — thin layers that lift apart (and close again) to show what a device or material is
made of (phone screen, SSD/NAND stack, chip, skin layers, soil strata). Works on the studio stage or a dark void.

Layers come from a JSON list (top first): [{"name":"glass","kind":"glass|grid|checker|rgb|solid|emissive",
"color":[r,g,b],"thickness":0.05}, ...]. t = 0 is assembled, t = 1 fully exploded. With --frames N the recipe
also writes keyframes (assembled at frame 1, exploded at frame N) so a video block can play it.

Run:  python exploded_layers.py -- --preview out.png [--layers layers.json] [--t 1.0] [--gap 0.55] [--stage studio|void]
      [--glb out.glb] [--frames 90]
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
import studio_stage  # noqa: E402

DEFAULT_LAYERS = [
    {"name": "Toughened glass", "kind": "glass", "color": [0.85, 0.92, 1.0], "thickness": 0.05},
    {"name": "Touch sensor grid", "kind": "checker", "color": [0.95, 0.78, 0.05], "color2": [0.08, 0.15, 0.75], "thickness": 0.03},
    {"name": "Insulator", "kind": "solid", "color": [0.95, 0.45, 0.65], "thickness": 0.03},
    {"name": "OLED pixels", "kind": "rgb", "color": [1, 1, 1], "thickness": 0.04},
    {"name": "Circuit board", "kind": "solid", "color": [0.05, 0.25, 0.12], "thickness": 0.06},
]


def layer_material(spec):
    kind = spec.get("kind", "solid")
    col = tuple(spec.get("color", [0.8, 0.8, 0.8])) + (1.0,)
    if kind == "glass":
        return rc.mat_principled("m_" + spec["name"], col, roughness=0.02, transmission=1.0, ior=1.5, coat=1.0)
    if kind == "emissive":
        return rc.mat_emission("m_" + spec["name"], col, 3.0)
    m = rc.mat_principled("m_" + spec["name"], col, roughness=0.35)
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    if kind in ("checker", "grid"):
        # diamond pattern: rotate texture coordinates 45 degrees, then a checker
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (0, 0, math.radians(45))
        mp.inputs["Scale"].default_value = (36, 36, 36)
        ch = nt.nodes.new("ShaderNodeTexChecker")
        ch.inputs["Color1"].default_value = col
        ch.inputs["Color2"].default_value = tuple(spec.get("color2", [0.1, 0.1, 0.6])) + (1.0,)
        ch.inputs["Scale"].default_value = 1.0
        nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], ch.inputs["Vector"])
        nt.links.new(ch.outputs["Color"], b.inputs["Base Color"])
    elif kind == "rgb":
        # repeating red/green/blue stripes that glow
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["UV"], sep.inputs["Vector"])
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 90.0
        nt.links.new(sep.outputs["X"], mul.inputs[0])
        fr = nt.nodes.new("ShaderNodeMath"); fr.operation = "FRACT"
        nt.links.new(mul.outputs[0], fr.inputs[0])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.interpolation = "CONSTANT"
        e = ramp.color_ramp.elements
        e[0].position = 0.0; e[0].color = (1, 0.05, 0.05, 1)
        e[1].position = 0.34; e[1].color = (0.05, 1, 0.1, 1)
        e3 = e.new(0.67); e3.color = (0.1, 0.25, 1, 1)
        nt.links.new(fr.outputs[0], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = 1.5
    return m


def build(layers, t, gap, width=2.2, depth=4.2, base_z=0.6, frames=0):
    total = len(layers)
    objs = []
    z = base_z
    # build bottom-up so thickness stacks; layers list is top-first
    for i, spec in enumerate(reversed(layers)):
        th = float(spec.get("thickness", 0.04))
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
        o = bpy.context.active_object
        o.name = "layer_%02d" % (total - 1 - i)
        o.scale = (width, depth, th)
        bev = o.modifiers.new("bevel", "BEVEL"); bev.width = min(0.03, th / 3); bev.segments = 3
        bpy.ops.object.transform_apply(scale=True)
        bpy.ops.object.shade_smooth()
        rc.assign(o, layer_material(spec))
        assembled = z + th / 2
        exploded = assembled + i * gap
        o.location = (0, 0, assembled + (exploded - assembled) * t)
        if frames:
            o.location.z = assembled
            o.keyframe_insert("location", frame=1)
            o.location.z = exploded
            o.keyframe_insert("location", frame=frames)
            o.location.z = assembled + (exploded - assembled) * t
        a = rc.empty("anchor_" + o.name, (width / 2, 0, 0))
        a.parent = o
        objs.append((o, spec))
        z += th
    return objs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--preview", required=True)
    p.add_argument("--layers", default="")
    p.add_argument("--t", type=float, default=1.0)
    p.add_argument("--gap", type=float, default=0.55)
    p.add_argument("--stage", default="studio", choices=["studio", "void"])
    p.add_argument("--glb", default="")
    p.add_argument("--frames", type=int, default=0)
    p.add_argument("--samples", type=int, default=48)
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    a = p.parse_args(rc.args_after_dashes())
    layers = json.load(open(a.layers)) if a.layers else DEFAULT_LAYERS
    rc.reset()
    if a.stage == "studio":
        studio_stage.build_stage(wall_top=(0.32, 0.12, 0.45, 1), wall_bottom=(0.04, 0.03, 0.10, 1))
    else:
        rc.world_color((0.008, 0.01, 0.02, 1), 1.0)
        rc.area_light("key", (3, -3.5, 5), (40, 0, 40), 700, size=3)
        rc.area_light("rim", (-4, 4, 4), (-55, 0, -140), 400, size=4)
    objs = build(layers, a.t, a.gap, frames=a.frames)
    top_z = max(o.location.z for o, _ in objs)
    rc.camera((5.0, -5.8, top_z + 1.5), target=(0, 0, (0.6 + top_z) / 2), lens=40,
              dof_target=(0, 0, (0.6 + top_z) / 2), fstop=5.6)
    rc.render_settings(a.width, a.height, a.samples)
    rc.render(a.preview)
    if a.glb:
        rc.export_glb(a.glb, names=[o.name for o, _ in objs])
    names = ["anchor_" + o.name for o, _ in objs]
    rc.done({"recipe": "exploded_layers", "preview": a.preview, "glb": a.glb or None,
             "layers": [s["name"] for _, s in objs][::-1],
             "anchors": {s["name"]: rc.anchors(["anchor_" + o.name]).get("anchor_" + o.name) for o, s in objs},
             "params": {k: v for k, v in vars(a).items() if k != "layers"}})


if __name__ == "__main__":
    main()
