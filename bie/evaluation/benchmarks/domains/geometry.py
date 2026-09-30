"""MATH-003: planar/simple-polygon and rigid-motion reference profiles."""
from __future__ import annotations
from fractions import Fraction
import math
from ..models import BenchmarkError, exact_fields, number
from .common import scalar, vector


def _cross(a: tuple, b: tuple, c: tuple) -> Fraction:
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def _on(a: tuple, b: tuple, p: tuple) -> bool:
    return _cross(a,b,p) == 0 and min(a[0],b[0]) <= p[0] <= max(a[0],b[0]) and min(a[1],b[1]) <= p[1] <= max(a[1],b[1])


def _intersects(a: tuple, b: tuple, c: tuple, d: tuple) -> bool:
    x, y, z, w = _cross(a,b,c), _cross(a,b,d), _cross(c,d,a), _cross(c,d,b)
    return (x*y < 0 and z*w < 0) or _on(a,b,c) or _on(a,b,d) or _on(c,d,a) or _on(c,d,b)


def solve(data: dict) -> dict:
    if type(data) is not dict:
        raise BenchmarkError("INVALID_FIELDS")
    op = data.get("op")
    if op == "triangle_sides":
        exact_fields(data, {"op", "sides"})
        if type(data["sides"]) is not list or len(data["sides"]) != 3:
            raise BenchmarkError("INVALID_TRIANGLE")
        a,b,c = sorted((scalar(q, "length", positive=True) for q in data["sides"]), reverse=True)
        if c <= a-b:
            raise BenchmarkError("DEGENERATE_OR_IMPOSSIBLE_TRIANGLE")
        # Kahan's rearrangement of Heron's formula for improved numerical stability.
        area = .25*math.sqrt((a+(b+c))*(c-(a-b))*(c+(a-b))*(a+(b-c)))
        return {"area_m2": number(area), "perimeter_m": number(a+b+c)}
    if op == "simple_polygon_area":
        exact_fields(data, {"op", "vertices", "unit"})
        raw = data["vertices"]
        if type(raw) is not list or not 3 <= len(raw) <= 128:
            raise BenchmarkError("INVALID_POLYGON_VERTEX_COUNT")
        vertices = [tuple(Fraction(str(n)) for n in vector({"values": p, "unit": data["unit"]}, "length", 2)) for p in raw]
        if len(set(vertices)) != len(vertices):
            raise BenchmarkError("REPEATED_POLYGON_VERTEX")
        n = len(vertices)
        # Collinear consecutive points are allowed unless they backtrack.
        for i in range(n):
            a,b,c = vertices[i-1], vertices[i], vertices[(i+1)%n]
            if _cross(a,b,c) == 0 and not _on(a,c,b):
                raise BenchmarkError("POLYGON_EDGE_BACKTRACK")
        for i in range(n):
            for j in range(i+1,n):
                if j == i+1 or i == 0 and j == n-1:
                    continue
                if _intersects(vertices[i], vertices[(i+1)%n], vertices[j], vertices[(j+1)%n]):
                    raise BenchmarkError("NON_SIMPLE_POLYGON")
        twice = sum(vertices[i][0]*vertices[(i+1)%n][1]-vertices[(i+1)%n][0]*vertices[i][1] for i in range(n))
        if twice == 0:
            raise BenchmarkError("DEGENERATE_POLYGON")
        return {"area_m2": number(float(abs(twice)/2)), "orientation": "CCW" if twice > 0 else "CW"}
    if op == "rigid_transform_2d":
        exact_fields(data, {"op", "points", "unit", "angle", "translation"})
        if type(data["points"]) is not list or not 1 <= len(data["points"]) <= 128:
            raise BenchmarkError("INVALID_POINT_COUNT")
        angle = scalar(data["angle"], "angle")
        if abs(angle) > 1e8:
            raise BenchmarkError("ANGLE_RESOLUTION_LIMIT")
        t = vector(data["translation"], "length", 2)
        co, si = math.cos(angle), math.sin(angle)
        points = [vector({"values": p, "unit": data["unit"]}, "length", 2) for p in data["points"]]
        return {"points_m": [[number(co*x-si*y+t[0]), number(si*x+co*y+t[1])] for x,y in points]}
    if op == "similar_figure_area":
        exact_fields(data, {"op", "base_area", "length_scale"})
        a = scalar(data["base_area"], "area", positive=True)
        scale = number(data["length_scale"], maximum=1e15)
        if scale <= 0:
            raise BenchmarkError("NONPOSITIVE_SCALE")
        return {"area_m2": number(a*scale*scale)}
    raise BenchmarkError("UNSUPPORTED_OPERATION")
