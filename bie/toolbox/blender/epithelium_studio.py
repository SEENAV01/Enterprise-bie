"""Blender (bpy) recipe: an epithelium shot the way a science-animation studio makes it (Task 046 one-shot test, after
Navin rejected Part B on 26 October 2026: "dur dur tak benchmark se mel nahi khata").

Run by ``bie.toolbox.adapters.blender.epithelium_studio`` in its own process:
    python epithelium_studio.py --params params.json --out <folder>
(or ``blender -b --python epithelium_studio.py -- --params ... --out ...``). Cycles on the CPU, no GPU.

What makes it different from the Part B sheet (``cell_sheet.py``, hexagonal prisms): every cell is an organic shape. The
outlines are a relaxed Voronoi tiling whose shared edges are bent by one smooth noise field, so neighbours interlock like
the benchmark's wavy boundaries; each cell is a soft slab with rounded membrane edges, a slightly domed top and a raised
bulge over its nucleus. Materials scatter light under the surface (subsurface scattering) and let some of it through, so
cells glow from within and the darker, denser nuclei show through the cytoplasm; fine noise breaks up the surface. A
basement membrane with collagen fibres lies below, a capillary with red blood cells lies behind, out of focus. A key and
a rim light, haze from the mist pass, depth of field, a slow camera push-in, small glowing particles crossing the layer for
exchange, and the compositor's glare on the lit cell. The image carries no text: labels and captions are drawn by BIE's
code on top (VG-02), from the anchor points this script writes for every frame (``anchors.json``).

The parameters (a JSON file; every key optional) make the same recipe build other members later: ``layers`` (a list,
base first: each with ``thickness``, ``dome``, ``bulge``, ``cell_size``), colours, ``context`` (``capillary`` or
``none``), camera, frames, resolution, samples. Output: ``frames/f0001.png``…, ``anchors.json``, ``record.json`` and one
``BIE_BLENDER_RESULT {json}`` line (cells, seconds per frame, samples, Blender version).
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

import bpy
import mathutils
from mathutils import Vector
from mathutils import noise as mnoise

# Presets (members, colours, camera, render settings) live in epithelium_studio.json, which Route 2's prompt writer reads
# too (bie/brain/video/still_prompt.py), so both routes share one layout.
PRESETS = json.loads((Path(__file__).resolve().parent / "epithelium_studio.json").read_text(encoding="utf-8"))
MEMBERS = PRESETS["members"]
DEFAULTS = PRESETS["defaults"]


# ---------------------------------------------------------------- geometry: relaxed, bent Voronoi outlines

def clip(poly, a, b):
    """The part of polygon ``poly`` on the side of the bisector of sites a and b that is nearer to a."""
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    nx, ny = b[0] - a[0], b[1] - a[1]
    inside = lambda p: (p[0] - mx) * nx + (p[1] - my) * ny <= 0
    out = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        pi, qi = inside(p), inside(q)
        if pi:
            out.append(p)
        if pi != qi:
            dp = (p[0] - mx) * nx + (p[1] - my) * ny
            dq = (q[0] - mx) * nx + (q[1] - my) * ny
            t = dp / (dp - dq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def voronoi(sites, box):
    x0, y0, x1, y1 = box
    cells = []
    for i, a in enumerate(sites):
        poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        near = sorted((s for j, s in enumerate(sites) if j != i), key=lambda s: (s[0] - a[0]) ** 2 + (s[1] - a[1]) ** 2)[:24]
        for b in near:
            poly = clip(poly, a, b)
            if len(poly) < 3:
                break
        cells.append(poly)
    return cells


def centroid(poly):
    area = cx = cy = 0.0
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        c = p[0] * q[1] - q[0] * p[1]
        area += c
        cx += (p[0] + q[0]) * c
        cy += (p[1] + q[1]) * c
    area *= 0.5
    if abs(area) < 1e-9:
        return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))
    return (cx / (6 * area), cy / (6 * area))


def tiling(width, depth, cell_size, rng, relax=3):
    n = max(6, int(width * depth / (cell_size ** 2 * 0.866)))
    sites = [(rng.uniform(-width / 2, width / 2), rng.uniform(-depth / 2, depth / 2)) for _ in range(n)]
    box = (-width / 2, -depth / 2, width / 2, depth / 2)
    for _ in range(relax):                                   # Lloyd relaxation: even sizes, still irregular
        sites = [centroid(c) if len(c) >= 3 else s for s, c in zip(sites, voronoi(sites, box))]
    return sites, voronoi(sites, box)


def bend(poly, amp, freq, seed):
    """Split every edge into short steps and move every point by one smooth noise field: shared edges move together,
    so neighbours interlock."""
    pts = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        steps = max(2, int(math.dist(p, q) / 0.035))
        for k in range(steps):
            t = k / steps
            pts.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    out = []
    for x, y in pts:                                         # two octaves: broad lobes and small jigsaw bumps
        v = mnoise.noise_vector(Vector((x * freq + seed, y * freq - seed, 0.37)))
        w = mnoise.noise_vector(Vector((x * freq * 2.7 - seed, y * freq * 2.7 + seed, 1.91)))
        out.append((x + (v.x + 0.35 * w.x) * amp, y + (v.y + 0.35 * w.y) * amp))
    return out


def shrink(poly, gap):
    c = centroid(poly)
    out = []
    for x, y in poly:
        d = math.hypot(x - c[0], y - c[1]) or 1.0
        s = max(0.5, 1 - gap / d)
        out.append((c[0] + (x - c[0]) * s, c[1] + (y - c[1]) * s))
    return out


# ---------------------------------------------------------------- materials

def socket(sockets, name, kind):
    return next(s for s in sockets if s.name == name and s.type == kind)


def principled(name, colour, *, sss=0.0, sss_colour=None, radius=(1.0, 0.45, 0.3), scale=0.08, rough=0.4, coat=0.0,
               transmission=0.0, emission=None, strength=0.0, alpha=1.0, bump=0.0, bump_scale=40.0, speckle=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    try:
        bsdf.subsurface_method = "BURLEY"                    # much faster than random walk, same soft glow at this size
    except (AttributeError, TypeError):
        pass
    def put(key, value):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = value
    put("Base Color", (*colour, 1.0))
    put("Roughness", rough)
    put("Subsurface Weight", sss)
    put("Subsurface Radius", radius)
    put("Subsurface Scale", scale)
    if sss_colour and "Subsurface Color" in bsdf.inputs:
        put("Subsurface Color", (*sss_colour, 1.0))
    put("Coat Weight", coat)
    put("Coat Roughness", 0.12)
    put("Transmission Weight", transmission)
    put("Alpha", alpha)
    if emission:
        put("Emission Color", (*emission, 1.0))
        put("Emission Strength", strength)
    if speckle:                                              # darker granules under the membrane (organelles)
        vor = nt.nodes.new("ShaderNodeTexVoronoi")
        vor.inputs["Scale"].default_value = speckle["scale"]
        warp = nt.nodes.new("ShaderNodeTexNoise")
        warp.inputs["Scale"].default_value = speckle["scale"] * 0.8
        coord = nt.nodes.new("ShaderNodeTexCoord")
        add = nt.nodes.new("ShaderNodeVectorMath")
        add.operation = "MULTIPLY_ADD"
        add.inputs[1].default_value = (0.06, 0.06, 0.06)
        nt.links.new(warp.outputs["Color"], add.inputs[0])
        nt.links.new(coord.outputs["Object"], add.inputs[2])
        nt.links.new(add.outputs["Vector"], vor.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeMapRange")
        ramp.inputs["From Min"].default_value = 0.12
        ramp.inputs["From Max"].default_value = 0.34
        ramp.inputs["To Min"].default_value = speckle["amount"]
        ramp.inputs["To Max"].default_value = 0.0
        nt.links.new(vor.outputs["Distance"], ramp.inputs["Value"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        socket(mix.inputs, "A", "RGBA").default_value = (*colour, 1.0)
        socket(mix.inputs, "B", "RGBA").default_value = (*speckle["colour"], 1.0)
        nt.links.new(ramp.outputs["Result"], socket(mix.inputs, "Factor", "VALUE"))
        nt.links.new(socket(mix.outputs, "Result", "RGBA"), bsdf.inputs["Base Color"])
    if bump > 0:                                             # fine surface noise: nothing reads as plastic
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = bump_scale
        tex.inputs["Detail"].default_value = 8.0
        b = nt.nodes.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = bump
        b.inputs["Distance"].default_value = 0.02
        nt.links.new(tex.outputs["Fac"], b.inputs["Height"])
        nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    if alpha < 1.0:
        try:
            mat.surface_render_method = "BLENDED"
        except AttributeError:
            pass
    return mat


# ---------------------------------------------------------------- objects

# (scale toward the centre, height as a fraction of the thickness): a rounded membrane edge, then the top surface
RINGS = [(1.0, 0.0), (1.0, 0.35), (0.996, 0.6), (0.986, 0.78), (0.968, 0.9), (0.944, 0.97), (0.915, 1.0), (0.86, 1.0),
         (0.78, 1.0), (0.69, 1.0), (0.6, 1.0), (0.5, 1.0), (0.4, 1.0), (0.3, 1.0), (0.2, 1.0), (0.11, 1.0), (0.04, 1.0)]


def smooth_ring(points, iterations):
    """Laplacian smoothing of a closed polyline: the inner rings of a cell grow rounder, so the outline's corners do not
    run as ridges across the top."""
    pts = list(points)
    n = len(pts)
    for _ in range(iterations):
        pts = [((pts[i - 1][0] + pts[(i + 1) % n][0]) * 0.25 + pts[i][0] * 0.5,
                (pts[i - 1][1] + pts[(i + 1) % n][1]) * 0.25 + pts[i][1] * 0.5) for i in range(n)]
    return pts


def cell_mesh(name, outline, z0, layer, rng, mats):
    """A soft slab over ``outline``: rounded membrane edge, domed top, a bulge over the nucleus. The mesh is dense enough
    to shade smooth without a subdivision modifier (Cycles spent minutes per frame subdividing the high-valence centres)."""
    h, dome, bulge = layer["thickness"], layer["dome"], layer["bulge"]
    c = centroid(outline)
    nuc = (c[0] + rng.uniform(-0.06, 0.06), c[1] + rng.uniform(-0.06, 0.06))
    rad = max(0.08, layer["nucleus"] * layer["cell_size"])
    rings = RINGS
    verts, faces = [], []
    n = len(outline)
    for s, frac in rings:
        ring = [(c[0] + (x - c[0]) * s, c[1] + (y - c[1]) * s) for x, y in outline]
        if s < 0.9:
            ring = smooth_ring(ring, int(6 + 60 * (0.9 - s)))
        for px, py in ring:
            if frac >= 1.0:
                z = h + dome * (1 - s * s)
                d = math.hypot(px - nuc[0], py - nuc[1])
                z += 0.35 * bulge * math.exp(-(d / (rad * 1.6)) ** 2)     # the membrane rises toward the nucleus
            else:
                z = h * frac
            verts.append((px, py, z0 + z))
    top_centre = z0 + h + dome + 0.35 * bulge * math.exp(-(math.hypot(c[0] - nuc[0], c[1] - nuc[1]) / (rad * 1.6)) ** 2)
    verts.append((c[0], c[1], top_centre))
    centre = len(verts) - 1
    for r in range(len(rings) - 1):
        for i in range(n):
            a, b = r * n + i, r * n + (i + 1) % n
            faces.append((a, b, b + n, a + n))
    last = (len(rings) - 1) * n
    for i in range(n):
        faces.append((last + i, last + (i + 1) % n, centre))
    faces.append(tuple(reversed(range(n))))                  # the base: one flat face on the basement membrane
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mats["cytoplasm"])
    for poly in mesh.polygons:
        poly.use_smooth = True
    # the nucleus: in a flat cell it pushes the top up into a round dome (its cap shows above the membrane); in a tall
    # cell it sits inside and shows through the translucent cytoplasm
    if bulge > 0.02:
        zc, zs = h * 0.6, h + dome + bulge - h * 0.6
    else:
        zc, zs = h * 0.5, max(0.035, h * 0.3)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0, location=(nuc[0], nuc[1], z0 + zc))
    n_obj = bpy.context.active_object
    n_obj.name = name.replace("cell", "nucleus")
    n_obj.scale = (rad, rad * rng.uniform(0.85, 1.0), zs)
    n_obj.rotation_euler = (0, 0, rng.uniform(0, math.pi))
    n_obj.data.materials.append(mats["nucleus"])
    bpy.ops.object.shade_smooth()
    return obj, n_obj, c, max(top_centre, z0 + zc + zs)


def fibres(rng, width, depth, z, mat, count=110):
    curves = bpy.data.curves.new("fibres", "CURVE")
    curves.dimensions = "3D"
    curves.bevel_depth = 0.0075
    curves.bevel_resolution = 2
    for _ in range(count):
        spline = curves.splines.new("BEZIER")
        k = 6
        spline.bezier_points.add(k - 1)
        x, y = rng.uniform(-width / 2, width / 2), rng.uniform(-depth / 2, depth / 2)
        ang = rng.uniform(0, math.pi)
        for i, bp in enumerate(spline.bezier_points):
            t = (i - k / 2) * 0.55
            px = x + math.cos(ang) * t + math.sin(i * 1.3 + x) * 0.06
            py = y + math.sin(ang) * t + math.cos(i * 1.1 + y) * 0.06
            px = max(-width / 2 + 0.1, min(width / 2 - 0.1, px))          # under the sheet only, never poking out
            py = max(-depth / 2 + 0.1, min(depth / 2 - 0.1, py))
            bp.co = (px, py, z + rng.uniform(-0.025, 0.012))
            bp.handle_left_type = bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new("collagen_fibres", curves)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def capillary(rng, mats, y=7.5, z=-1.75, radius=0.5):
    """A gently winding capillary behind the sheet: a translucent wall with red blood cells inside, far out of focus."""
    curve = bpy.data.curves.new("capillary", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 6
    curve.use_fill_caps = True
    spline = curve.splines.new("BEZIER")
    xs = [-13 + i * 2.6 for i in range(11)]
    spline.bezier_points.add(len(xs) - 1)
    path = []
    for bp, x in zip(spline.bezier_points, xs):
        point = (x, y + 0.9 * math.sin(x * 0.33 + 0.6), z + 0.25 * math.sin(x * 0.21))
        bp.co = point
        bp.handle_left_type = bp.handle_right_type = "AUTO"
        path.append(point)
    tube = bpy.data.objects.new("capillary_wall", curve)
    bpy.context.collection.objects.link(tube)
    tube.data.materials.append(mats["vessel"])
    for i in range(22):                                       # red blood cells: flattened, dimpled discs, inside the wall
        k = rng.uniform(0, len(path) - 1.001)
        a, b = path[int(k)], path[int(k) + 1]
        t = k - int(k)
        centre = [a[j] + (b[j] - a[j]) * t for j in range(3)]
        bpy.ops.mesh.primitive_torus_add(major_radius=0.17, minor_radius=0.075,
                                         location=(centre[0], centre[1] + rng.uniform(-0.2, 0.2), centre[2] + rng.uniform(-0.2, 0.2)))
        rbc = bpy.context.active_object
        rbc.name = f"red_blood_cell_{i}"
        rbc.rotation_euler = (rng.uniform(0, math.pi), rng.uniform(0, math.pi), 0)
        rbc.data.materials.append(mats["blood"])
        bpy.ops.object.shade_smooth()
    return tube


def particles(rng, count, centre, mat, frames, top):
    out = []
    for i in range(count):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=rng.uniform(0.045, 0.085))
        p = bpy.context.active_object
        p.name = f"gas_{i}"
        p.data.materials.append(mat)
        bpy.ops.object.shade_smooth()
        x, y = centre[0] + rng.uniform(-2.6, 2.6), centre[1] + rng.uniform(-1.8, 1.8)
        start = rng.uniform(-0.45, 0.55) * frames
        length = rng.uniform(0.75, 1.05) * frames
        for f in (1, frames):
            t = (f - start) / length
            p.location = (x + 0.15 * math.sin(i + t * 3), y + 0.1 * math.cos(i * 2 + t * 2), top + 1.9 - 2.4 * t)
            p.keyframe_insert("location", frame=f)
        for fc in getattr(p.animation_data.action, "fcurves", []) or []:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
        out.append(p)
    return out


def light(name, kind, location, rotation, energy, colour, size=None):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    data.color = colour
    if size is not None and hasattr(data, "size"):
        data.size = size
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    obj.rotation_euler = rotation
    bpy.context.collection.objects.link(obj)
    return obj


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def compositor(scene, glare: bool, haze: float = 0.0, haze_colour=(0.1, 0.13, 0.19)):
    """Haze from the mist pass, then glare on the bright parts (the lit cell, the particles); Blender 5's node-group
    compositor or the older tree."""
    if not glare and haze <= 0:
        return False
    try:
        tree = bpy.data.node_groups.new("BIE compositor", "CompositorNodeTree")
        scene.compositing_node_group = tree
        rl = tree.nodes.new("CompositorNodeRLayers")
        out = tree.nodes.new("NodeGroupOutput")
        tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    except (AttributeError, TypeError, RuntimeError):
        scene.use_nodes = True
        tree = scene.node_tree
        tree.nodes.clear()
        rl = tree.nodes.new("CompositorNodeRLayers")
        out = tree.nodes.new("CompositorNodeComposite")
    g = tree.nodes.new("CompositorNodeGlare")
    for key, value in (("glare_type", "BLOOM"), ("quality", "HIGH"), ("threshold", 0.9), ("size", 7), ("mix", -0.55)):
        try:
            setattr(g, key, value)
        except (AttributeError, TypeError):
            pass
    for name, value in (("Type", "Bloom"), ("Threshold", 0.9), ("Strength", 0.45), ("Size", 0.6), ("Quality", "High")):
        if name in g.inputs:
            try:
                g.inputs[name].default_value = value
            except (TypeError, ValueError):
                pass
    image = rl.outputs["Image"]
    if haze > 0 and "Mist" in rl.outputs:
        fac = tree.nodes.new("ShaderNodeMath")
        fac.operation = "MULTIPLY"
        fac.inputs[1].default_value = haze
        tree.links.new(rl.outputs["Mist"], fac.inputs[0])
        mix = tree.nodes.new("ShaderNodeMix")
        mix.data_type, mix.blend_type = "RGBA", "SCREEN"
        tree.links.new(fac.outputs[0], socket(mix.inputs, "Factor", "VALUE"))
        tree.links.new(image, socket(mix.inputs, "A", "RGBA"))
        socket(mix.inputs, "B", "RGBA").default_value = (*haze_colour, 1.0)
        image = socket(mix.outputs, "Result", "RGBA")
    if glare:
        tree.links.new(image, g.inputs["Image"])
        image = g.outputs["Image"]
    tree.links.new(image, out.inputs[0])
    return True


# ---------------------------------------------------------------- the shot

def build(params: dict) -> dict:
    p = json.loads(json.dumps(DEFAULTS))
    for key, value in params.items():
        if isinstance(value, dict) and isinstance(p.get(key), dict):
            p[key].update(value)
        else:
            p[key] = value
    layers = p.get("layers") or MEMBERS[p["member"]]
    rng = random.Random(p["seed"])
    mnoise.seed_set(int(p["seed"]))          # Blender seeds its noise anew in every process: without this, chunks rendered
                                             # on different runners would build different cells
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    col = p["colours"]
    mats = {
        "cytoplasm": principled("cytoplasm", col["cytoplasm"], sss=0.6, sss_colour=col["cytoplasm_sss"], radius=(1.0, 0.42, 0.28),
                                scale=0.1, rough=0.38, coat=0.4, bump=0.16, bump_scale=34.0,
                                speckle={"colour": col["speckle"], "amount": 0.6, "scale": 4.5}),
        "nucleus": principled("nucleus", col["nucleus_top"], sss=0.35, radius=(0.6, 0.3, 0.7), scale=0.05, rough=0.45, coat=0.3,
                              bump=0.6, bump_scale=50.0),
        "membrane": principled("basement_membrane", col["membrane"], sss=0.5, scale=0.1, rough=0.45, transmission=0.2),
        "fibre": principled("collagen", col["fibre"], sss=0.5, scale=0.04, rough=0.5),
        "vessel": principled("vessel", col["vessel"], rough=0.5, transmission=0.85),
        "blood": principled("blood", col["blood"], sss=0.6, scale=0.15, rough=0.3, coat=0.4),
        "particle": principled("gas", col["particle"], sss=0.3, rough=0.2, coat=0.8, emission=col["particle"], strength=0.6),
    }
    focus_mat = mats["cytoplasm"].copy()
    focus_mat.name = "cytoplasm_focus"
    bsdf = focus_mat.node_tree.nodes.get("Principled BSDF")
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.62, 0.48, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 0.0
        bsdf.inputs["Emission Strength"].keyframe_insert("default_value", frame=1)
        bsdf.inputs["Emission Strength"].default_value = float(p["focus_cell_glow"])
        bsdf.inputs["Emission Strength"].keyframe_insert("default_value", frame=int(p["frames"] * 0.45))

    cells = nuclei = 0
    z0 = 0.0
    anchors_world = {}
    top_cells = []
    for li, layer in enumerate(layers):
        layer = dict({"thickness": 0.1, "dome": 0.04, "bulge": 0.06, "cell_size": 1.0, "nucleus": 0.17}, **layer)
        sites, polys = tiling(p["width"], p["depth"], layer["cell_size"], rng)
        for k, poly in enumerate(polys):
            if len(poly) < 3:
                continue
            outline = shrink(bend(poly, p["wobble"] * layer["cell_size"], p["wobble_freq"] / layer["cell_size"], p["seed"] + li), p["gap"])
            obj, nobj, c, top = cell_mesh(f"cell_{li}_{k}", outline, z0, layer, rng, mats)
            cells += 1
            nuclei += 1
            if li == len(layers) - 1:
                top_cells.append((obj, c, top))
        z0 += layer["thickness"] * 0.92
    target = Vector(p["camera"]["target"])
    focus = min(top_cells, key=lambda t: (t[1][0] - target.x) ** 2 + (t[1][1] - target.y) ** 2)
    focus[0].data.materials[0] = focus_mat
    anchors_world["simple squamous"] = Vector((focus[1][0], focus[1][1], focus[2]))
    # "boundary": the far edge of the sheet, where the camera sees how thin the layer is against the dark
    anchors_world["boundary"] = Vector((target.x + 1.2, p["depth"] / 2 - 0.05, z0 * 0.5))
    # basement membrane and fibres below
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.035))
    bm = bpy.context.active_object
    bm.name = "basement_membrane"
    bm.scale = (p["width"] + 0.05, p["depth"] + 0.05, 0.05)
    bm.data.materials.append(mats["membrane"])
    fibres(rng, p["width"], p["depth"], -0.075, mats["fibre"])
    if p["context"] == "capillary":
        capillary(rng, mats, y=p["depth"] / 2 + 3.5)
    gas = particles(rng, int(p["particles"]), (target.x, target.y), mats["particle"], int(p["frames"]), z0)
    # lights: a warm key from front-left above, a cool rim from behind that outlines every dome, a soft fill
    light("key", "AREA", (-4.5, -4.0, 6.0), (math.radians(40), 0, math.radians(-45)), 900, col["key"], size=4.0)
    light("rim", "AREA", (2.5, 7.0, 3.2), (math.radians(-68), 0, math.radians(165)), 1400, col["rim"], size=3.0)
    light("fill", "AREA", (5.0, -5.0, 2.0), (math.radians(70), 0, math.radians(45)), 160, (0.8, 0.85, 1.0), size=6.0)
    world = bpy.data.worlds.new("dark")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (*col["world"], 1.0)
    scene.world = world
    # haze: the mist pass (distance from the camera) mixed over the image in the compositor; far things fade into a
    # cool dark haze. A volume box gave the same look at many times the render time.
    world.mist_settings.start, world.mist_settings.depth, world.mist_settings.falloff = 5.5, 12.0, "QUADRATIC"
    scene.view_layers[0].use_pass_mist = p["haze"] > 0
    # camera: a slow push-in toward the lit cell, focus on it, shallow depth of field
    cam_data = bpy.data.cameras.new("camera")
    cam_data.lens = p["lens"]
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = p["fstop"]
    cam = bpy.data.objects.new("camera", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    focus_empty = bpy.data.objects.new("focus", None)
    focus_empty.location = anchors_world["simple squamous"]
    bpy.context.collection.objects.link(focus_empty)
    cam_data.dof.focus_object = focus_empty
    frames = int(p["frames"])
    for f, key in ((1, "from"), (frames, "to")):
        cam.location = Vector(p["camera"][key])
        look_at(cam, target)
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
    # render settings: Cycles on the CPU, denoiser, filmic look
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = int(p["samples"])
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = bool(p["denoise"])
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    scene.cycles.adaptive_threshold = float(p["noise_threshold"])
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = scene.cycles.glossy_bounces = scene.cycles.transmission_bounces = 2
    scene.cycles.volume_bounces = 0
    scene.render.resolution_x, scene.render.resolution_y = p["resolution"]
    scene.render.resolution_percentage = 100
    scene.render.fps = int(p["fps"])
    scene.frame_start, scene.frame_end = 1, frames
    scene.render.image_settings.file_format = "PNG"
    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Medium High Contrast"
        scene.view_settings.exposure = float(p["exposure"])
    except TypeError:
        pass
    glare = compositor(scene, bool(p["glare"]), float(p["haze"]), col["haze"])
    return {"scene": scene, "cam": cam, "anchors_world": anchors_world, "cells": cells, "nuclei": nuclei, "glare": glare,
            "params": p, "particles": len(gas)}


def anchors(scene, cam, points: dict) -> dict:
    from bpy_extras.object_utils import world_to_camera_view
    out = {name: [] for name in points}
    for f in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(f)
        for name, point in points.items():
            v = world_to_camera_view(scene, cam, point)
            out[name].append([round(v.x, 5), round(1 - v.y, 5), round(v.z, 3)])     # x, y from the top-left, depth
    return out


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", default="")
    parser.add_argument("--out", required=True)
    parser.add_argument("--stills", default="", help="only these frames (comma separated), for tests and sample sweeps")
    args = parser.parse_args(argv)
    params = json.loads(Path(args.params).read_text(encoding="utf-8")) if args.params else {}
    out = Path(args.out)
    (out / "frames").mkdir(parents=True, exist_ok=True)
    built = build(params)
    scene, p = built["scene"], built["params"]
    (out / "anchors.json").write_text(json.dumps({"resolution": p["resolution"], "fps": p["fps"], "frames": p["frames"],
                                                  "points": anchors(scene, built["cam"], built["anchors_world"])}), encoding="utf-8")
    wanted = [int(x) for x in args.stills.split(",") if x] if args.stills else \
        list(range(int(p["frame_from"]), int(p["frame_to"] or p["frames"]) + 1, int(p["frame_step"])))
    started = time.time()
    times = []
    for f in wanted:
        scene.frame_set(f)
        scene.render.filepath = str(out / "frames" / f"f{f:04d}.png")
        t = time.time()
        bpy.ops.render.render(write_still=True)
        times.append(round(time.time() - t, 2))
    record = {"recipe": "epithelium_studio", "member": p["member"], "cells": built["cells"], "nuclei": built["nuclei"],
              "particles": built["particles"], "glare": built["glare"], "samples": p["samples"], "denoise": p["denoise"],
              "resolution": p["resolution"], "frames_rendered": len(wanted), "seconds_per_frame": times,
              "mean_seconds_per_frame": round(sum(times) / max(1, len(times)), 2), "total_seconds": round(time.time() - started, 1),
              "blender": bpy.app.version_string, "threads": scene.render.threads}
    (out / "record.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    print("BIE_BLENDER_RESULT " + json.dumps(record))


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
