"""Validate topology before emitting any vertex indexing expression."""
from .hardening_contracts import known_properties, finite_number, reject, sequence

def model2d_geometry(props: dict) -> dict:
    known_properties(props, {'vertices', 'coordinate_space', 'edges'})
    vertices = sequence(props.get("vertices"), "vertices", minimum=2)
    output = []
    if props.get("coordinate_space", "normalized") != "normalized":
        reject("MODEL2D_COORDINATE_SPACE_UNSUPPORTED", "supply normalized x-right/y-down coordinates explicitly")
    for point in vertices:
        xy = [finite_number(x, "coordinate") for x in sequence(point, "vertex", minimum=2, maximum=2)]
        if any(not 0 <= x <= 1 for x in xy):
            reject("MODEL2D_COORDINATE_OUT_OF_RANGE", "normalized coordinates must be within [0,1]")
        output.append(xy)
    if len({tuple(p) for p in output}) != len(output):
        reject("MODEL2D_DUPLICATE_VERTEX", "coincident vertices need an explicit topology adapter")
    edges = sequence(props.get("edges", []), "edges", minimum=0, maximum=4000)
    seen, checked = set(), []
    for edge in edges:
        if not isinstance(edge, (list, tuple)) or len(edge) != 2 or any(type(i) is not int or not 0 <= i < len(output) for i in edge):
            reject("MODEL2D_EDGE_INDEX_INVALID", "edge must contain two in-range integer vertex indices")
        a, b = edge
        if a == b:
            reject("MODEL2D_SELF_LOOP_UNSUPPORTED", "self loops are not line segments")
        key = tuple(sorted((a,b)))
        if key in seen:
            reject("MODEL2D_DUPLICATE_EDGE", "duplicate undirected edge")
        seen.add(key);checked.append([a,b])
    return {"vertices": output, "edges": checked, "coordinate_space": "normalized", "axis_convention": "x-right-y-down"}
