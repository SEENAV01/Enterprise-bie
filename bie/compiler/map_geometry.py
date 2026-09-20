"""H2-004 explicit inline geographic geometry and projection.

EPSG:4326 INPUT IS EXPLICITLY lon_lat HERE (not inferred native EPSG axis order).
No tiles, online providers, implicit clipping, reprojection label-only behavior,
geodesic claims, or invented boundary data. Bounded simple regional geometry.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math
from .hardening_contracts import finite_number, known_properties, sequence, text_value, reject

RADIUS = 6378137.0
MERCATOR_MAX_LAT = 85.0511287798066


def project_lonlat(lon: float, lat: float, projection: str):
    lon, lat = finite_number(lon, "longitude"), finite_number(lat, "latitude")
    if not -180 <= lon <= 180 or not -90 <= lat <= 90:
        reject("MAP_COORDINATE_OUT_OF_RANGE", "longitude/latitude outside geographic domain")
    if projection == "web_mercator":
        if abs(lat) > MERCATOR_MAX_LAT:
            reject("MAP_MERCATOR_LATITUDE_LIMIT", "polar coordinates are not silently clamped")
        return RADIUS*math.radians(lon), RADIUS*math.asinh(math.tan(math.radians(lat)))
    if projection == "equirectangular":
        return RADIUS*math.radians(lon), RADIUS*math.radians(lat)
    reject("MAP_PROJECTION_UNSUPPORTED", "only declared web_mercator / equirectangular supported")


def _segments_intersect(a, b, c, d):
    def orient(p, q, r): return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    def on(p, q, r): return min(p[0], q[0]) <= r[0] <= max(p[0], q[0]) and min(p[1], q[1]) <= r[1] <= max(p[1], q[1])
    s, t, u, v = orient(a,b,c), orient(a,b,d), orient(c,d,a), orient(c,d,b)
    return (s*t < 0 and u*v < 0) or any(x == 0 and on(p,q,r) for x,p,q,r in ((s,a,b,c),(t,a,b,d),(u,c,d,a),(v,c,d,b)))


def validate_polygon(points):
    if len(points) < 4 or points[0] != points[-1] or len(set(map(tuple, points[:-1]))) != len(points)-1:
        reject("MAP_POLYGON_INVALID", "polygon needs an explicitly closed unique-vertex ring")
    if len(points) > 129:
        reject("MAP_COMPLEXITY_LIMIT", "simple polygon supports at most 128 vertices")
    area = sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points, points[1:]))/2
    if abs(area) < 1e-14:
        reject("MAP_POLYGON_INVALID", "polygon has zero/unresolved area")
    edges = list(zip(points, points[1:]))
    for i, (a,b) in enumerate(edges):
        for j, (c,d) in enumerate(edges):
            if j <= i+1 or (i == 0 and j == len(edges)-1): continue
            if _segments_intersect(a,b,c,d):
                reject("MAP_POLYGON_SELF_INTERSECTION", "self-crossing polygon unsupported")


@dataclass(frozen=True)
class MapGeometry:
    source_crs: str
    projection: str
    axis_order: str
    extent: tuple[float, float, float, float]
    projected_extent: tuple[float, float, float, float]
    layers: tuple[dict, ...]
    attribution: str
    title: str
    interpolation: str = "straight-segments-in-projected-space"
    accepted: bool = False

    def to_dict(self): return asdict(self)


def map_geometry(props):
    known_properties(props, {"crs", "projection", "layers", "attribution", "title"})
    crs = props.get("crs")
    if not isinstance(crs, str):
        reject("MAP_SOURCE_CRS_UNSUPPORTED", "CRS must be a string")
    normalized = crs in {"normalized", "BIE:NORMALIZED"}
    if not normalized and crs != "EPSG:4326":
        reject("MAP_SOURCE_CRS_UNSUPPORTED", "explicit normalized or EPSG:4326 input required")
    if normalized:
        if "projection" in props:
            reject("MAP_PROJECTION_UNCONSUMED", "normalized geometry does not take a geographic projection")
        kind, order, extent = "normalized-cartesian-y-up", "xy", (0., 0., 1., 1.)
        project = lambda x,y: (x,y)
    else:
        spec = props.get("projection")
        if not isinstance(spec, dict) or set(spec) != {"kind", "axis_order", "extent"}:
            reject("MAP_PROJECTION_REQUIRED", "explicit kind, axis_order and extent are required")
        kind, order = spec["kind"], spec["axis_order"]
        if not isinstance(kind,str) or kind not in {"web_mercator", "equirectangular"} or order != "lon_lat":
            reject("MAP_PROJECTION_UNSUPPORTED", "projection and lon_lat order must be explicitly supported")
        vals = sequence(spec["extent"], "map extent", minimum=4, maximum=4)
        extent = tuple(finite_number(v, "extent") for v in vals)
        if not (-180 <= extent[0] < extent[2] <= 180 and -90 <= extent[1] < extent[3] <= 90):
            reject("MAP_EXTENT_INVALID", "extent must be west,south,east,north without antimeridian wrapping")
        project = lambda x,y: project_lonlat(x,y,kind)
    if extent[2]-extent[0] < 1e-7 or extent[3]-extent[1] < 1e-7:
        reject("MAP_EXTENT_UNRESOLVED", "extent is below supported geometric resolution")
    a, b = project(extent[0], extent[1]), project(extent[2], extent[3])
    projected_extent = (a[0], a[1], b[0], b[1])
    scale = min(900/(b[0]-a[0]), 420/(b[1]-a[1]))
    offset_x = 50+(900-(b[0]-a[0])*scale)/2
    offset_y = 65+(420-(b[1]-a[1])*scale)/2
    def pixel(pt):
        x,y = project(*pt)
        return [offset_x+(x-a[0])*scale, offset_y+(b[1]-y)*scale]
    layers = sequence(props.get("layers"), "map layers", maximum=6)
    output, ids, total = [], set(), 0
    for i, layer in enumerate(layers):
        if not isinstance(layer, dict):
            reject("MAP_LAYER_INVALID", "layer must be an object")
        known_properties(layer, {"kind", "points", "label", "layer_id", "source_ref"})
        layer_kind = layer.get("kind")
        if not isinstance(layer_kind,str) or layer_kind not in {"route", "point", "polygon"}:
            reject("MAP_LAYER_UNSUPPORTED", "supported inline layers: route, point, simple polygon")
        pts = sequence(layer.get("points"), "layer points", minimum=1 if layer_kind == "point" else 2, maximum=1 if layer_kind == "point" else 4096)
        total += len(pts)
        if total > 10000: reject("MAP_COMPLEXITY_LIMIT", "total vertex budget exceeded")
        coords = []
        for pt in pts:
            pair = sequence(pt, "map point", minimum=2, maximum=2)
            q = [finite_number(v, "coordinate") for v in pair]
            if not extent[0] <= q[0] <= extent[2] or not extent[1] <= q[1] <= extent[3]:
                reject("MAP_GEOMETRY_OUTSIDE_EXTENT", "clipping/dropping source coordinates is forbidden")
            project(*q)  # Checks actual geographic projection domain, not just a label.
            if coords and coords[-1] == q:
                reject("MAP_ZERO_LENGTH_SEGMENT", "adjacent duplicate points unsupported")
            if coords and not normalized and abs(q[0]-coords[-1][0]) > 180:
                reject("MAP_ANTIMERIDIAN_UNSUPPORTED", "split/unwrap this route upstream with governed provenance; do not draw across the world")
            coords.append(q)
        if layer_kind == "polygon": validate_polygon(coords)
        lid = text_value(layer.get("layer_id", "layer-"+str(i)), "layer_id", maximum=100)
        if lid in ids: reject("MAP_LAYER_ID_DUPLICATE", "layer identities must be unique")
        ids.add(lid)
        label = text_value(layer.get("label", lid), "map label", maximum=80)
        source = layer.get("source_ref")
        if source is not None: text_value(source, "map layer source_ref", maximum=1000)
        output.append({"layer_id": lid, "kind": layer_kind, "label": label, "source_ref": source,
                       "source_points": coords, "projected_points": [list(project(*p)) for p in coords], "pixels": [pixel(p) for p in coords]})
    attribution = text_value(props.get("attribution", "" if not normalized else "Inline normalized geometry; no external basemap."), "map attribution", maximum=160)
    return MapGeometry(crs, kind, order, extent, projected_extent, tuple(output), attribution,
                       text_value(props.get("title", "Declared inline map geometry"), "map title", maximum=120))
