"""Explicit projection contract. A 3D vector never silently becomes 2D."""
from __future__ import annotations
import math
from .hardening_contracts import known_properties, finite_number, label, reject, sequence, text_value

def vector_geometry(props: dict) -> dict:
    known_properties(props, {'label', 'projection', 'components', 'units'})
    components = sequence(props.get("components"), "components", minimum=2, maximum=3)
    components = [finite_number(x, "vector component") for x in components]
    units = label(props, "units")
    projection_label = "2D Cartesian (x right, y up)"
    projection = props.get("projection")
    if len(components) == 3:
        if not isinstance(projection, dict) or projection.get("kind") != "orthographic_matrix":
            reject("VECTOR_PROJECTION_REQUIRED", "3D vectors require an explicit orthographic_matrix projection")
        known_properties(projection, {"kind", "matrix", "label"})
        projection_label = text_value(projection.get("label"), "projection label", maximum=256)
        rows = sequence(projection.get("matrix"), "projection matrix", minimum=2, maximum=2)
        matrix = [[finite_number(x, "projection coefficient") for x in sequence(r, "projection row", minimum=3, maximum=3)] for r in rows]
        # Orthonormal rows avoid hidden shear/scale and establish a genuine orthographic view.
        norms = [math.hypot(*r) for r in matrix]
        dot = sum(a*b for a,b in zip(*matrix))
        if any(not math.isclose(n, 1.0, rel_tol=1e-9, abs_tol=1e-9) for n in norms) or abs(dot) > 1e-9:
            reject("VECTOR_PROJECTION_INVALID", "projection rows must be orthonormal")
        projected = [math.fsum(a*b for a,b in zip(row, components)) for row in matrix]
        norm = math.hypot(*components)
        if norm and math.hypot(*projected) / norm < 1e-10:
            reject("VECTOR_VIEW_DEGENERATE", "vector is hidden in this view; choose an explicit nondegenerate projection")
    else:
        if projection is not None:
            reject("VECTOR_UNUSED_PROJECTION", "2D vector does not consume a 3D projection")
        projected = list(components)
        matrix = None
    largest = max(abs(x) for x in projected)
    # A per-vector view scale is explicit and must not be read as shared magnitude scale.
    scale = 100.0 / largest if largest else 1.0
    if not math.isfinite(scale):
        reject("VECTOR_SCALE_UNSUPPORTED", "vector magnitude is below finite view-scale support")
    end = [200 + projected[0] * scale, 145 - projected[1] * scale]
    return {"components": components, "dimensions": len(components), "units": units,
            "projection_label": projection_label, "projection_matrix": matrix,
            "projected": projected, "scale_px_per_unit": scale, "origin": [200, 145],
            "endpoint": end, "is_zero": not any(components), "label": label(props, "label")}
