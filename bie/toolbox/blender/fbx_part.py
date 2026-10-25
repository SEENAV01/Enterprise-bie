"""Blender (bpy) script: import an anatomy FBX (Z-Anatomy), keep the objects whose names match, export glTF (Task 046a).

    python fbx_part.py --fbx CardioVascular41.fbx --match "heart" --out heart.glb [--max-objects 400]

Matching is case-insensitive on object names; meshes only. The kept objects are centred and scaled to about 2 units so
the web block can frame them; the names and the count are printed as BIE_BLENDER_RESULT for the asset record.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

import bpy
from mathutils import Vector


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--fbx", required=True)
    parser.add_argument("--match", required=True, help="regular expression on object names")
    parser.add_argument("--exclude", default="", help="regular expression on object names to drop")
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-objects", type=int, default=400)
    args = parser.parse_args(argv)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=args.fbx)
    keep = re.compile(args.match, re.I)
    drop = re.compile(args.exclude, re.I) if args.exclude else None
    kept, names = [], []
    for obj in list(bpy.data.objects):
        ok = obj.type == "MESH" and keep.search(obj.name) and not (drop and drop.search(obj.name))
        if ok and len(kept) < args.max_objects:
            kept.append(obj)
            names.append(obj.name)
        else:
            bpy.data.objects.remove(obj, do_unlink=True)
    if not kept:
        print("BIE_BLENDER_RESULT " + json.dumps({"error": f"no mesh matches {args.match!r}"}))
        sys.exit(2)
    for obj in kept:                                   # unparent but keep where the part really sits in the body
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
    bpy.context.view_layer.update()
    lo = Vector((min(min((o.matrix_world @ Vector(c))[i] for c in o.bound_box) for o in kept) for i in range(3)))
    hi = Vector((max(max((o.matrix_world @ Vector(c))[i] for c in o.bound_box) for o in kept) for i in range(3)))
    centre, size = (lo + hi) / 2, max(hi - lo) or 1.0
    for obj in kept:
        obj.location = (obj.location - centre) * (2.0 / size)
        obj.scale = obj.scale * (2.0 / size)
    bpy.ops.export_scene.gltf(filepath=args.out, export_format="GLB", export_apply=True, export_yup=True)
    print("BIE_BLENDER_RESULT " + json.dumps({"objects": len(kept), "names": names[:40], "size_before": round(size, 4),
                                              "blender": bpy.app.version_string, "out": args.out}))


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
