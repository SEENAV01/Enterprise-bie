from __future__ import annotations

from typing import Any, Mapping, Sequence
from .grammar_contracts import VisualGrammar, GrammarValidationError, finite_number, make_plan

GEOGRAPHY_MAP_GRAMMAR = VisualGrammar(
    grammar_id="bie.vis.grammar.geography_map", version="1.0.0",
    domains=("geography", "earth_science", "civics"), representations=("map", "route_map", "thematic_map"),
    allowed_primitives=("map_frame", "point_marker", "route", "region", "label", "scale_bar", "north_arrow"),
    required_roles=("map_frame", "geo_feature"),
    semantic_constraints=("coordinate reference system is explicit", "features from incompatible coordinate frames are rejected", "route order and region membership preserve source semantics"),
    aliases=("geography-map",), tags=("map", "route", "region", "coordinates"),
)


def plan_map(features: Sequence[Mapping[str, Any]], *, crs: str, evidence_refs: Sequence[str], reasoning_refs: Sequence[str], map_extent: Sequence[float] | None = None):
    if not isinstance(crs, str) or not crs.strip():
        raise GrammarValidationError("crs must be non-blank")
    crs = crs.strip()
    elements = [{"id": f"map:{crs}", "role": "map_frame", "primitive": "map_frame", "label": crs, "source_ids": list(evidence_refs), "payload": {"crs": crs, "extent": None}}]
    if map_extent is not None:
        if not isinstance(map_extent, Sequence) or isinstance(map_extent, (str, bytes)) or len(map_extent) != 4:
            raise GrammarValidationError("map_extent must contain [xmin, ymin, xmax, ymax]")
        extent = [finite_number(v, field_name="map_extent") for v in map_extent]
        if extent[0] >= extent[2] or extent[1] >= extent[3]:
            raise GrammarValidationError("map_extent bounds are invalid")
        elements[0]["payload"]["extent"] = extent
    ids = set()
    for feature in features:
        fid = str(feature.get("id", "")).strip()
        if not fid or fid in ids: raise GrammarValidationError("feature ids must be non-blank and unique")
        ids.add(fid)
        feature_crs = str(feature.get("crs", crs)).strip()
        if feature_crs != crs: raise GrammarValidationError(f"feature {fid} uses incompatible CRS {feature_crs!r}")
        kind = str(feature.get("kind", "point")).strip().lower()
        primitive = {"point": "point_marker", "route": "route", "region": "region"}.get(kind)
        if primitive is None: raise GrammarValidationError(f"unsupported map feature kind: {kind}")
        coords = feature.get("coordinates")
        if not isinstance(coords, Sequence) or isinstance(coords, (str, bytes)) or not coords:
            raise GrammarValidationError(f"feature {fid} must include coordinates")
        if kind == "point":
            if len(coords) != 2: raise GrammarValidationError("point coordinates must have length 2")
            normalized = [finite_number(v, field_name=f"{fid}.coordinates") for v in coords]
        else:
            normalized = []
            for pair in coords:
                if not isinstance(pair, Sequence) or isinstance(pair, (str, bytes)) or len(pair) != 2:
                    raise GrammarValidationError(f"feature {fid} coordinate pairs must have length 2")
                normalized.append([finite_number(v, field_name=f"{fid}.coordinates") for v in pair])
            if kind == "region" and len(normalized) < 3: raise GrammarValidationError("region requires at least three vertices")
            if kind == "route" and len(normalized) < 2: raise GrammarValidationError("route requires at least two points")
        elements.append({"id": f"geo:{fid}", "role": "geo_feature", "primitive": primitive, "label": str(feature.get("label", fid)), "source_ids": list(feature.get("source_ids", evidence_refs)), "payload": {"kind": kind, "crs": crs, "coordinates": normalized}})
    if not features: raise GrammarValidationError("at least one map feature is required")
    return make_plan(GEOGRAPHY_MAP_GRAMMAR, evidence_refs=evidence_refs, reasoning_refs=reasoning_refs, elements=elements, constraints=GEOGRAPHY_MAP_GRAMMAR.semantic_constraints)
