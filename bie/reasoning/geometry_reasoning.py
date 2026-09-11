"""RE-SPATIAL-004: grounded Euclidean geometry, exact decimal predicates.

This operates on extracted coordinates, not raster diagrams or theorem conjectures.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from fractions import Fraction
from math import fsum

from bie.reasoning.coordinate_reasoning import analyze
from bie.reasoning.grounded_result import evidence, finite, identifier, inference, require_refs

TASK_ID = "BIE-RE-SPATIAL-004"


@dataclass(frozen=True)
class Point:
    point_id: str
    x: float
    y: float
    evidence_ids: tuple[str, ...]


def _points(points, refs):
    refs = evidence(refs)
    identities, coords = {}, []
    for p in points:
        identifier(p.point_id, "point id")
        finite(p.x, "x"); finite(p.y, "y")
        require_refs(p.evidence_ids, refs)
        coordinate = (Fraction(str(p.x)), Fraction(str(p.y)))
        # Independent observations may cite different evidence for one point.
        # Identity constrains coordinates, not which source observed them.
        if p.point_id in identities and identities[p.point_id] != coordinate:
            raise ValueError("Conflicting coordinates for point id")
        identities[p.point_id] = coordinate
        coords.append(coordinate)
    return tuple(coords), refs


def _cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on(p, a, b):
    return _cross(a, b, p) == 0 and min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])


def _relation(a, b, c, d):
    if a == b or c == d:
        raise ValueError("Segments must have distinct endpoints")
    ab_c, ab_d, cd_a, cd_b = _cross(a, b, c), _cross(a, b, d), _cross(c, d, a), _cross(c, d, b)
    if ab_c == ab_d == cd_a == cd_b == 0:
        axis = 0 if a[0] != b[0] else 1
        low = max(min(a[axis], b[axis]), min(c[axis], d[axis]))
        high = min(max(a[axis], b[axis]), max(c[axis], d[axis]))
        return "overlapping" if low < high else "touching" if low == high else "disjoint"
    if ab_c * ab_d < 0 and cd_a * cd_b < 0:
        return "proper_crossing"
    if any((_on(c, a, b), _on(d, a, b), _on(a, c, d), _on(b, c, d))):
        return "touching"
    return "disjoint"


def _polygon(vertices, refs):
    vertices = tuple(vertices)
    coords, refs = _points(vertices, refs)
    if len(coords) < 3 or len(set(coords)) != len(coords):
        raise ValueError("An open polygon ring requires at least three distinct vertices")
    n = len(coords)
    for i in range(n):
        for j in range(i + 1, n):
            relation = _relation(coords[i], coords[(i + 1) % n], coords[j], coords[(j + 1) % n])
            adjacent = j == i + 1 or (i == 0 and j == n - 1)
            if (adjacent and relation != "touching") or (not adjacent and relation != "disjoint"):
                raise ValueError("Self-intersecting or retraced polygon")
    twice_area = sum(coords[i][0] * coords[(i + 1) % n][1] - coords[(i + 1) % n][0] * coords[i][1] for i in range(n))
    if not twice_area:
        raise ValueError("Degenerate zero-area polygon")
    return vertices, coords, refs, twice_area


def _context(frame_id, unit):
    identifier(frame_id, "coordinate frame")
    if unit not in {"m", "cm", "mm", "km", "map_unit"}:
        raise ValueError("Explicit supported uniform linear unit required")
    return {"frame_id": frame_id, "unit": unit}


def segment_relation(a: Point, b: Point, c: Point, d: Point, refs, *, frame_id: str, unit="m"):
    context = _context(frame_id, unit)
    points, refs = _points((a, b, c, d), refs)
    return inference(TASK_ID, "geometry.segment_relation", {**context, "points": [asdict(x) for x in (a, b, c, d)]}, {"relation": _relation(*points)}, refs, assumptions=("Exact predicates on supplied decimal coordinates in a common Euclidean frame",))


def polygon_measure(vertices, refs, *, frame_id: str, unit="m"):
    context = _context(frame_id, unit)
    vertices, coords, refs, twice_area = _polygon(vertices, refs)
    n = len(coords)
    perimeter = finite(fsum(analyze((vertices[i].x, vertices[i].y), (vertices[(i + 1) % n].x, vertices[(i + 1) % n].y))["distance"] for i in range(n)), "perimeter")
    cross = [coords[i][0] * coords[(i + 1) % n][1] - coords[(i + 1) % n][0] * coords[i][1] for i in range(n)]
    centroid = [finite(float(sum((coords[i][axis] + coords[(i + 1) % n][axis]) * cross[i] for i in range(n)) / (3 * twice_area)), "centroid") for axis in (0, 1)]
    turns = [_cross(coords[i], coords[(i + 1) % n], coords[(i + 2) % n]) for i in range(n)]
    value = {"area": finite(float(abs(twice_area) / 2), "area"), "area_unit": unit + "^2", "perimeter": perimeter, "length_unit": unit, "centroid": centroid, "orientation": "counterclockwise" if twice_area > 0 else "clockwise", "convex": all(x >= 0 for x in turns) or all(x <= 0 for x in turns), "vertex_count": n}
    return inference(TASK_ID, "geometry.polygon_measure", {**context, "vertices": [asdict(x) for x in vertices]}, value, refs, assumptions=("Simple polygon without holes; coordinates represent exact supplied values",))


def point_in_polygon(point: Point, vertices, refs, *, frame_id: str, unit="m"):
    context = _context(frame_id, unit)
    vertices, coords, refs, _ = _polygon(vertices, refs)
    # Validate the query and ring together: a query cannot redefine a vertex.
    all_coords, refs = _points((point, *vertices), refs)
    p = all_coords[0]
    winding, boundary = 0, False
    for i, a in enumerate(coords):
        b = coords[(i + 1) % len(coords)]
        if _on(p, a, b):
            boundary = True
            break
        if a[1] <= p[1] < b[1] and _cross(a, b, p) > 0:
            winding += 1
        elif b[1] <= p[1] < a[1] and _cross(a, b, p) < 0:
            winding -= 1
    value = "boundary" if boundary else "inside" if winding else "outside"
    return inference(TASK_ID, "geometry.point_in_polygon", {**context, "point": asdict(point), "vertices": [asdict(x) for x in vertices]}, {"relation": value}, refs)


def triangle_properties(vertices, refs, *, frame_id: str, unit="m"):
    vertices = tuple(vertices)
    if len(vertices) != 3:
        raise ValueError("Exactly three triangle vertices required")
    refs = evidence(refs)
    measure = polygon_measure(vertices, refs, frame_id=frame_id, unit=unit)
    coords, refs = _points(vertices, refs)
    squared = sorted(sum((coords[i][k] - coords[(i + 1) % 3][k]) ** 2 for k in (0, 1)) for i in range(3))
    residual = squared[0] + squared[1] - squared[2]
    value = {**measure.value, "side_class": "equilateral" if len(set(squared)) == 1 else "isosceles" if len(set(squared)) == 2 else "scalene", "angle_class": "right" if residual == 0 else "acute" if residual > 0 else "obtuse"}
    return inference(TASK_ID, "geometry.triangle_properties", json_inputs(measure), value, refs, assumptions=measure.assumptions)


def json_inputs(result):
    import json
    return json.loads(result.inputs_json)
