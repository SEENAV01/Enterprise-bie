"""Shared helpers for asset-intake Blender recipes (run with bpy 5.x, Python 3.11, or `blender -b --python`).

Every recipe: builds a scene from parameters, can export the model (.glb), renders a preview (.png) with Cycles,
and prints ONE JSON line: outputs, parameters, and 2D anchor points (pixel positions of named parts in the preview)
so BIE's code can draw leader-line labels on top in any language. Labels are never baked into the render.
"""
from __future__ import annotations

import json
import math
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


def args_after_dashes(argv=None):
    argv = list(sys.argv if argv is None else argv)
    return argv[argv.index("--") + 1:] if "--" in argv else argv[1:]


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat_principled(name, rgba, roughness=0.5, metallic=0.0, transmission=0.0, ior=1.45, emission=None, strength=0.0,
                   alpha=1.0, sss=0.0, sss_radius=(1.0, 0.4, 0.3), coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = rgba
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Transmission Weight"].default_value = transmission
    b.inputs["IOR"].default_value = ior
    b.inputs["Alpha"].default_value = alpha
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = sss_radius
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if emission is not None:
        b.inputs["Emission Color"].default_value = emission
        b.inputs["Emission Strength"].default_value = strength
    return m


def mat_emission(name, rgba, strength=4.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = rgba
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def world_color(rgba=(0.01, 0.012, 0.02, 1.0), strength=1.0):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = rgba
    bg.inputs["Strength"].default_value = strength


def area_light(name, loc, rot_deg, energy, size=4.0, color=(1, 1, 1)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = [math.radians(a) for a in rot_deg]
    return obj


def camera(loc, target=(0, 0, 0), lens=50, dof_target=None, fstop=2.8):
    data = bpy.data.cameras.new("Camera")
    data.lens = lens
    cam = bpy.data.objects.new("Camera", data)
    bpy.context.collection.objects.link(cam)
    cam.location = loc
    direction = Vector(target) - Vector(loc)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    if dof_target is not None:
        data.dof.use_dof = True
        data.dof.focus_distance = (Vector(dof_target) - Vector(loc)).length
        data.dof.aperture_fstop = fstop
    return cam


def render_settings(width=1280, height=720, samples=48, engine="CYCLES"):
    sc = bpy.context.scene
    sc.render.engine = engine
    sc.render.resolution_x, sc.render.resolution_y = width, height
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    if engine == "CYCLES":
        sc.cycles.device = "CPU"
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 8
        sc.cycles.transmission_bounces = 8


def anchors(names):
    """Pixel positions (x, y from top-left) of named objects' origins or empties in the current camera view."""
    sc = bpy.context.scene
    cam = sc.camera
    w, h = sc.render.resolution_x, sc.render.resolution_y
    out = {}
    for n in names:
        obj = bpy.data.objects.get(n)
        if not obj:
            continue
        co = world_to_camera_view(sc, cam, obj.matrix_world.translation)
        out[n] = [round(co.x * w, 1), round((1 - co.y) * h, 1)]
    return out


def empty(name, loc):
    e = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(e)
    e.location = loc
    return e


def render(path):
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def export_glb(path, names=None):
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.objects:
        if o.type == "MESH" or o.type == "CURVE":
            if names is None or o.name in names:
                o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path), use_selection=True, export_format="GLB")


def done(record):
    """Print the result line and write it next to the preview as <preview>.json."""
    print("RECIPE_RESULT " + json.dumps(record))
    if record.get("preview"):
        with open(str(record["preview"]) + ".json", "w") as f:
            json.dump(record, f, indent=1)
