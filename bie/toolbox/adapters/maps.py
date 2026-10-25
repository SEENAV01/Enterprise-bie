"""Maps for geography, history and polity, cut from Natural Earth by Shapely for BIE's d3-geo map block (Task 046a, batch 3).

- ``india``: India as India shows it (Natural Earth's India point-of-view boundary, ``ne_10m_admin_0_countries_ind``),
  its states and union territories (admin-1), and the neighbouring countries, simplified for drawing, with the named
  states picked out. Inside India's boundary, land that no admin-1 state covers (the parts of Jammu and Kashmir and
  Ladakh that India shows and Natural Earth's admin-1 does not) is drawn as India, never as another country.
- ``places``: towns and cities by name from Natural Earth's populated places.
- ``route``: a route through named places, with the great-circle length of every leg.
Map data is public domain; before a map of India is published, its boundary is Navin's to check against the Survey of
India's (the registry says so).
"""
from __future__ import annotations

import json
import math
from functools import lru_cache

from .base import clean, need

NEIGHBOURS = ("PAK", "CHN", "NPL", "BTN", "BGD", "MMR", "LKA", "AFG")
RENAMED = {"prayagraj": "allahabad", "gurugram": "gurgaon", "mysuru": "mysore", "kalaburagi": "gulbarga"}   # Natural Earth keeps the older names
EARTH_KM = 6371.0088


@lru_cache(maxsize=4)
def _features(name: str) -> tuple:
    from .. import sources
    return tuple(json.loads(sources.natural_earth(name).read_text(encoding="utf-8"))["features"])


def _area_km2(geometry) -> float:
    """Area on the sinusoidal projection, which keeps areas: within about 1 % of the surveyed area for a state."""
    shapely = need("shapely")
    np = need("numpy")

    def project(xy):
        lon, lat = np.radians(xy[:, 0]), np.radians(xy[:, 1])
        return np.column_stack([lon * np.cos(lat) * EARTH_KM, lat * EARTH_KM])
    return float(shapely.transform(geometry, project).area)


def india(highlight=(), *, tolerance: float = 0.02, neighbours: bool = True) -> dict:
    shapely = need("shapely")
    from shapely.geometry import mapping, shape
    from shapely.ops import unary_union
    country = next(f for f in _features("ne_10m_admin_0_countries_ind") if f["properties"]["ADM0_A3"] == "IND")
    outline = shape(country["geometry"])
    rows = [f for f in _features("ne_10m_admin_1_states_provinces") if f["properties"].get("adm0_a3") == "IND"]
    names = sorted(f["properties"]["name"] for f in rows)
    unknown = [h for h in highlight if h not in names]
    if unknown:
        raise ValueError(f"not a state or union territory in Natural Earth: {', '.join(unknown)} (known: {', '.join(names)})")
    states = []
    for f in sorted(rows, key=lambda f: f["properties"]["name"]):
        geom = shape(f["geometry"])
        point = geom.representative_point()
        states.append({"name": f["properties"]["name"], "kind": f["properties"].get("type_en") or "",
                       "iso": f["properties"].get("iso_3166_2") or "", "highlight": f["properties"]["name"] in highlight,
                       "label": [point.x, point.y], "area_km2": round(_area_km2(geom)),
                       "geometry": mapping(geom.simplify(tolerance, preserve_topology=True))})
    covered = unary_union([shape(f["geometry"]) for f in rows])
    rest = outline.difference(covered.buffer(0.01))            # India's boundary beyond the admin-1 states
    out = {"outline": mapping(outline.simplify(tolerance, preserve_topology=True)), "states": states,
           "beyond_states": mapping(rest.simplify(tolerance, preserve_topology=True)),
           "beyond_states_km2": round(_area_km2(rest)), "bounds": list(outline.bounds), "neighbours": [],
           "data": "Natural Earth 5.1.2 (public domain): India's point-of-view boundary and admin-1 states",
           "drawn_by": f"Shapely {shapely.__version__}"}
    if neighbours:
        for f in _features("ne_10m_admin_0_countries_ind"):
            if f["properties"]["ADM0_A3"] in NEIGHBOURS:
                geom = shape(f["geometry"]).difference(outline)          # never draw a neighbour over India's own boundary
                out["neighbours"].append({"name": f["properties"]["NAME"], "iso3": f["properties"]["ADM0_A3"],
                                          "geometry": mapping(geom.simplify(tolerance * 2, preserve_topology=True))})
    return clean(out, 3)


def places(names, *, countries=()) -> list:
    """Each name's place (the most populous match, within ``countries`` ISO3 codes when given) from Natural Earth."""
    rows = [f["properties"] for f in _features("ne_10m_populated_places_simple")]
    out = []
    for name in names:
        want = RENAMED.get(name.lower(), name.lower())
        found = [r for r in rows if want in (str(r.get("name", "")).lower(), str(r.get("nameascii", "")).lower())
                 and (not countries or r.get("adm0_a3") in countries)]
        if not found:
            raise ValueError(f"Natural Earth has no populated place {name!r}")
        best = max(found, key=lambda r: r.get("pop_max") or 0)
        out.append({"name": name, "lon": best["longitude"], "lat": best["latitude"], "country": best.get("adm0name"),
                    "population": best.get("pop_max")})
    return clean(out, 4)


def great_circle_km(a, b) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_KM * math.asin(math.sqrt(h))


def route(names, *, countries=()) -> dict:
    stops = places(names, countries=countries)
    total, legs = 0.0, []
    for a, b in zip(stops, stops[1:]):
        km = great_circle_km((a["lon"], a["lat"]), (b["lon"], b["lat"]))
        total += km
        legs.append({"from": a["name"], "to": b["name"], "km": round(km), "total_km": round(total)})
    return {"stops": stops, "legs": legs, "total_km": round(total), "data": "Natural Earth populated places (public domain)"}
