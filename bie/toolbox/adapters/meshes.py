"""3D meshes with trimesh: OBJ and STL files (BodyParts3D, NIH 3D) to glTF for three.js, and their measures (Task 046a)."""
from __future__ import annotations

import io

from .base import clean, need


def to_glb(data: bytes, file_type: str, *, colour=(230, 150, 140, 255), max_faces: int = 120000) -> tuple:
    """(glb bytes, info) for a mesh file. Large meshes are simplified only by dropping to ``max_faces`` when possible."""
    trimesh = need("trimesh")
    loaded = trimesh.load(io.BytesIO(data), file_type=file_type, force="mesh")
    mesh = loaded
    mesh.visual = trimesh.visual.ColorVisuals(mesh, face_colors=colour)
    mesh.apply_translation(-mesh.bounding_box.centroid)
    if len(mesh.faces) > max_faces:
        try:
            mesh = mesh.simplify_quadric_decimation(face_count=max_faces)
        except Exception:                              # simplification needs an optional backend; keep the full mesh
            pass
    glb = trimesh.exchange.gltf.export_glb(trimesh.Scene(mesh))
    return glb, clean({"vertices": len(mesh.vertices), "faces": len(mesh.faces), "extent": mesh.extents, "watertight": bool(mesh.is_watertight),
                       "computed_by": f"trimesh {trimesh.__version__}"}, 3)


def glb_info(data: bytes) -> dict:
    trimesh = need("trimesh")
    scene = trimesh.load(io.BytesIO(data), file_type="glb")
    geometries = list(scene.geometry.values()) if hasattr(scene, "geometry") else [scene]
    return clean({"meshes": len(geometries), "vertices": sum(len(g.vertices) for g in geometries),
                  "faces": sum(len(g.faces) for g in geometries if hasattr(g, "faces")), "extent": scene.extents}, 3)
