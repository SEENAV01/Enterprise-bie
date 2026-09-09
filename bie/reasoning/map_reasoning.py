"""RE-SPATIAL-003: scaled planar maps and grounded directed shortest routes.

Coordinates are explicit map units, never latitude/longitude inferred from numbers.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import heapq
from math import atan2, degrees

from bie.reasoning.coordinate_reasoning import analyze
from bie.reasoning.grounded_result import evidence, finite, identifier, inference, require_refs

TASK_ID = "BIE-RE-SPATIAL-003"


@dataclass(frozen=True)
class MapFrame:
    frame_id: str
    metres_per_unit: float
    evidence_ids: tuple[str, ...]
    y_axis: str = "north"
    coordinate_system: str = "local_planar"


@dataclass(frozen=True)
class MapLocation:
    location_id: str
    x: float
    y: float
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class MapEdge:
    edge_id: str
    source: str
    target: str
    distance_m: float
    evidence_ids: tuple[str, ...]
    bidirectional: bool = False


def _validate(frame, locations, refs):
    refs = evidence(refs)
    identifier(frame.frame_id, "map frame")
    if finite(frame.metres_per_unit, "scale") <= 0:
        raise ValueError("Map scale must be positive")
    if frame.coordinate_system != "local_planar" or frame.y_axis not in {"north", "south"}:
        raise ValueError("Explicit local planar frame and north/south y-axis required")
    require_refs(frame.evidence_ids, refs)
    by_id = {}
    for loc in locations:
        identifier(loc.location_id, "location id")
        finite(loc.x, "map x"); finite(loc.y, "map y")
        require_refs(loc.evidence_ids, refs)
        if loc.location_id in by_id:
            raise ValueError("Duplicate location id")
        by_id[loc.location_id] = loc
    if not by_id:
        raise ValueError("Locations required")
    return by_id, refs


def relative_position(frame: MapFrame, origin: MapLocation, destination: MapLocation, refs):
    locations, refs = _validate(frame, (origin, destination), refs)
    result = analyze((origin.x, origin.y), (destination.x, destination.y))
    east = finite(result["dx"] * frame.metres_per_unit, "east displacement")
    north = finite(result["dy"] * frame.metres_per_unit * (1 if frame.y_axis == "north" else -1), "north displacement")
    distance = finite(result["distance"] * frame.metres_per_unit, "distance")
    bearing = (degrees(atan2(east, north)) + 360) % 360 if distance else None
    labels = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
    direction = "coincident" if bearing is None else labels[int((bearing + 22.5) // 45) % 8]
    return inference(TASK_ID, "map.relative_position", {"frame": asdict(frame), "locations": [asdict(origin), asdict(destination)]}, {"distance_m": distance, "east_m": east, "north_m": north, "bearing_degrees_clockwise_from_north": bearing, "direction": direction}, refs, assumptions=("Local planar distance; supplied scale and orientation are source-grounded",))


def shortest_route(frame: MapFrame, locations, edges, start: str, goal: str, refs):
    locations, refs = _validate(frame, tuple(locations), refs)
    if start not in locations or goal not in locations:
        raise ValueError("Unknown route endpoint")
    edges = tuple(edges)
    adjacency = {k: [] for k in locations}
    ids = set()
    for edge in edges:
        identifier(edge.edge_id, "edge id")
        if edge.edge_id in ids or edge.source not in locations or edge.target not in locations or edge.source == edge.target:
            raise ValueError("Duplicate edge, unknown endpoint, or self edge")
        ids.add(edge.edge_id)
        if finite(edge.distance_m, "edge distance") <= 0 or type(edge.bidirectional) is not bool:
            raise ValueError("Strictly positive edge distance and boolean direction flag required")
        require_refs(edge.evidence_ids, refs)
        adjacency[edge.source].append((edge.target, edge.distance_m, edge.edge_id))
        if edge.bidirectional:
            adjacency[edge.target].append((edge.source, edge.distance_m, edge.edge_id))
    # Exact equal-cost ties resolve by lexicographic node path then edge path.
    queue = [(0.0, (start,), (), start)]
    best = {start: (0.0, (start,), ())}
    while queue:
        cost, nodes, used_edges, current = heapq.heappop(queue)
        if best[current] != (cost, nodes, used_edges):
            continue
        if current == goal:
            break
        for neighbour, distance, edge_id in sorted(adjacency[current]):
            candidate = (finite(cost + distance, "route distance"), nodes + (neighbour,), used_edges + (edge_id,))
            if neighbour not in best or candidate < best[neighbour]:
                best[neighbour] = candidate
                heapq.heappush(queue, (*candidate, neighbour))
    inputs = {"frame": asdict(frame), "locations": [asdict(locations[k]) for k in sorted(locations)], "edges": [asdict(e) for e in sorted(edges, key=lambda e: e.edge_id)], "start": start, "goal": goal}
    if goal not in best:
        return inference(TASK_ID, "map.shortest_route", inputs, {"node_ids": [], "edge_ids": [], "distance_m": None}, refs, status="UNREACHABLE", uncertainty=("No route exists in the supplied map graph; missing roads are not inferred",))
    cost, nodes, used_edges = best[goal]
    return inference(TASK_ID, "map.shortest_route", inputs, {"node_ids": nodes, "edge_ids": used_edges, "distance_m": cost}, refs, assumptions=("Only supplied directed edges are traversable", "Edge costs are metres; equal-cost routes use lexicographic tie-breaking"))
