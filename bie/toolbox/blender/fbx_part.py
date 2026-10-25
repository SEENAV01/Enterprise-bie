"""Blender (bpy) script: import an anatomy FBX (Z-Anatomy), keep the objects whose names match, export glTF (Task 046a).

    python fbx_part.py --fbx CardioVascular41.fbx --match "heart" --out heart.glb [--max-objects 400]
                       [--group "^(Frontal|Parietal) lobe\\.g$" --min-vertices 20]

Matching is case-insensitive on object names; meshes only. The kept objects are centred and scaled to about 2 units so
the web block can frame them; the names and the count are printed as BIE_BLENDER_RESULT for the asset record.
With ``--group``, a mesh is kept only when one of its parents' names matches, and the kept meshes are joined into one
object per such parent, named after it without Z-Anatomy's ".g" suffix (a brain becomes one object per lobe).
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
    parser.add_argument("--group", default="", help="regular expression on parent names: keep and join meshes per parent")
    parser.add_argument("--min-vertices", type=int, default=0)
    args = parser.parse_args(argv)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=args.fbx)
    keep = re.compile(args.match, re.I)
    drop = re.compile(args.exclude, re.I) if args.exclude else None
    group = re.compile(args.group, re.I) if args.group else None

    def owner(obj):
        parent = obj.parent
        while parent is not None:
            if group.search(parent.name):
                return parent.name
            parent = parent.parent
        return None
    owners = {obj.name: owner(obj) for obj in bpy.data.objects} if group else {}
    kept, names = [], []
    for obj in list(bpy.data.objects):
        ok = (obj.type == "MESH" and keep.search(obj.name) and not (drop and drop.search(obj.name))
              and len(obj.data.vertices) >= args.min_vertices and (not group or owners.get(obj.name)))
        if ok and len(kept) < args.max_objects:
            kept.append(obj)
            names.append(obj.name)
        elif obj.type == "MESH" or not group:
            bpy.data.objects.remove(obj, do_unlink=True)
    if not kept:
        print("BIE_BLENDER_RESULT " + json.dumps({"error": f"no mesh matches {args.match!r}"}))
        sys.exit(2)
    for obj in kept:                                   # unparent but keep where the part really sits in the body
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
    for obj in list(bpy.data.objects):                 # the group empties are not needed any more
        if obj.type != "MESH":
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.context.view_layer.update()
    if group:
        joined, by_owner = [], {}
        for o in kept:                                 # grouped before joining: a join deletes the other members
            by_owner.setdefault(owners[o.name], []).append(o)
        for name, members in sorted(by_owner.items()):
            with bpy.context.temp_override(active_object=members[0], selected_objects=members, selected_editable_objects=members):
                bpy.ops.object.join()
            members[0].name = re.sub(r"\.g$", "", name)
            members[0].data.name = members[0].name
            joined.append(members[0])
        kept, parts = joined, len(names)
        names = [o.name for o in kept]
    else:
        parts = len(kept)
    lo = Vector((min(min((o.matrix_world @ Vector(c))[i] for c in o.bound_box) for o in kept) for i in range(3)))
    hi = Vector((max(max((o.matrix_world @ Vector(c))[i] for c in o.bound_box) for o in kept) for i in range(3)))
    centre, size = (lo + hi) / 2, max(hi - lo) or 1.0
    for obj in kept:
        obj.location = (obj.location - centre) * (2.0 / size)
        obj.scale = obj.scale * (2.0 / size)
    bpy.ops.export_scene.gltf(filepath=args.out, export_format="GLB", export_apply=True, export_yup=True)
    print("BIE_BLENDER_RESULT " + json.dumps({"objects": len(kept), "parts": parts, "names": names[:40], "size_before": round(size, 4),
                                              "blender": bpy.app.version_string, "out": args.out}))


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
