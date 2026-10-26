"""Recipe: studio stage — a grid-tiled glossy floor and a curved gradient back wall (the 'virtual studio' of
3D explainer videos such as Branch Education). Other recipes call build_stage() to place their objects on it.

Run:  python studio_stage.py -- --preview stage.png [--wall-top 0.05,0.35,0.38] [--wall-bottom 0.02,0.06,0.12]
      [--floor 0.62,0.64,0.68] [--lines 0.08,0.09,0.11] [--tile 0.5] [--hero] [--samples 48]
"""
from __future__ import annotations

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402

import recipe_common as rc  # noqa: E402


def rgb(s):
    v = [float(x) for x in s.split(",")]
    return (v[0], v[1], v[2], 1.0)


def grid_floor_material(floor, lines, tile, line_width=0.035):
    m = bpy.data.materials.new("grid_floor")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    b.inputs["Roughness"].default_value = 0.28
    b.inputs["Coat Weight"].default_value = 0.4
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    edges = []
    for axis in ("X", "Y"):
        div = nt.nodes.new("ShaderNodeMath"); div.operation = "DIVIDE"; div.inputs[1].default_value = tile
        nt.links.new(sep.outputs[axis], div.inputs[0])
        fr = nt.nodes.new("ShaderNodeMath"); fr.operation = "FRACT"
        nt.links.new(div.outputs[0], fr.inputs[0])
        # distance to the nearest tile edge: min(f, 1-f)
        inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
        nt.links.new(fr.outputs[0], inv.inputs[1])
        mn = nt.nodes.new("ShaderNodeMath"); mn.operation = "MINIMUM"
        nt.links.new(fr.outputs[0], mn.inputs[0]); nt.links.new(inv.outputs[0], mn.inputs[1])
        lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = line_width
        nt.links.new(mn.outputs[0], lt.inputs[0])
        edges.append(lt)
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
    nt.links.new(edges[0].outputs[0], mx.inputs[0]); nt.links.new(edges[1].outputs[0], mx.inputs[1])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.inputs[6].default_value = floor
    mix.inputs[7].default_value = lines
    nt.links.new(mx.outputs[0], mix.inputs[0])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    return m


def gradient_wall_material(top, bottom):
    m = bpy.data.materials.new("gradient_wall")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    b.inputs["Roughness"].default_value = 0.9
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = bottom
    ramp.color_ramp.elements[1].color = top
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    # a little self-light so the wall reads as a coloured backdrop, not a shadowed box
    nt.links.new(ramp.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 1.2
    return m


def build_stage(wall_top=(0.05, 0.35, 0.38, 1), wall_bottom=(0.02, 0.06, 0.12, 1), floor=(0.62, 0.64, 0.68, 1),
                lines=(0.08, 0.09, 0.11, 1), tile=0.5, size=30.0):
    """Floor + curved cyclorama wall + lights + dark world. Returns nothing; objects are named stage_*."""
    rc.world_color((0.005, 0.006, 0.01, 1.0), 1.0)
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    fl = bpy.context.active_object; fl.name = "stage_floor"
    rc.assign(fl, grid_floor_material(floor, lines, tile))
    # cyclorama: a quarter-cylinder sweep behind the floor
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=size / 3.0, depth=size, location=(0, 0, 0))
    wall = bpy.context.active_object; wall.name = "stage_wall"
    wall.scale = (1.0, 1.0, 0.6)
    wall.location = (0, 0, size * 0.3 - 0.01)
    bpy.ops.object.shade_smooth()
    # flip normals so the inside faces the camera
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode="OBJECT")
    rc.assign(wall, gradient_wall_material(wall_top, wall_bottom))
    rc.area_light("key", (3, -3.5, 5), (40, 0, 40), 700, size=3)
    rc.area_light("rim", (-5, 4, 4), (-55, 0, -140), 500, size=4, color=(0.7, 0.85, 1.0))
    rc.area_light("fill", (0, -8, 2), (85, 0, 0), 60, size=8)


def hero_object():
    """A simple rounded-slab 'device' so the stage preview shows scale and reflections."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.1))
    o = bpy.context.active_object; o.name = "hero_device"
    o.scale = (1.3, 2.6, 0.12)
    o.rotation_euler = (math.radians(12), 0, math.radians(28))
    bev = o.modifiers.new("bevel", "BEVEL"); bev.width = 0.08; bev.segments = 6
    bpy.ops.object.shade_smooth()
    rc.assign(o, rc.mat_principled("device", (0.02, 0.02, 0.025, 1), roughness=0.12, metallic=0.2, coat=1.0))
    rc.empty("anchor_device", (0, 0, 1.05))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--preview", required=True)
    p.add_argument("--wall-top", default="0.05,0.35,0.38")
    p.add_argument("--wall-bottom", default="0.02,0.06,0.12")
    p.add_argument("--floor", default="0.42,0.44,0.48")
    p.add_argument("--lines", default="0.08,0.09,0.11")
    p.add_argument("--tile", type=float, default=0.8)
    p.add_argument("--hero", action="store_true")
    p.add_argument("--samples", type=int, default=48)
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    a = p.parse_args(rc.args_after_dashes())
    rc.reset()
    build_stage(rgb(a.wall_top), rgb(a.wall_bottom), rgb(a.floor), rgb(a.lines), a.tile)
    if a.hero:
        hero_object()
    rc.camera((4.6, -5.4, 2.6), target=(0, 0, 1.0), lens=38, dof_target=(0, 0, 1.1), fstop=2.8)
    rc.render_settings(a.width, a.height, a.samples)
    rc.render(a.preview)
    rc.done({"recipe": "studio_stage", "preview": a.preview, "anchors": rc.anchors(["anchor_device"]),
             "params": vars(a)})


if __name__ == "__main__":
    main()
