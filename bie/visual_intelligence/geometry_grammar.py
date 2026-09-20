from __future__ import annotations

from typing import Any, Mapping, Sequence
from .grammar_contracts import VisualGrammar, GrammarValidationError, finite_number, make_plan

GEOMETRY_GRAMMAR = VisualGrammar(
    grammar_id="bie.vis.grammar.geometry", version="1.0.0",
    domains=("mathematics", "physics", "engineering"), representations=("geometry_diagram", "construction"),
    allowed_primitives=("point", "segment", "ray", "line", "angle_arc", "polygon", "circle", "dimension", "label"),
    required_roles=("geometry_object",),
    semantic_constraints=("declared incidences and measurements are preserved", "diagram appearance is not proof of equality/parallelism/perpendicularity", "measurements require units when dimensioned"),
    aliases=("geometry",), tags=("geometry", "construction", "measurement"),
)


def plan_geometry(objects: Sequence[Mapping[str, Any]], *, evidence_refs: Sequence[str], reasoning_refs: Sequence[str], frame_id: str = "geometry"):
    elements = []; ids = set()
    for obj in objects:
        oid = str(obj.get("id", "")).strip()
        if not oid or oid in ids: raise GrammarValidationError("geometry object ids must be non-blank and unique")
        ids.add(oid)
        kind = str(obj.get("kind", "point")).strip().lower()
        primitive = {"point": "point", "segment": "segment", "ray": "ray", "line": "line", "angle": "angle_arc", "polygon": "polygon", "circle": "circle", "dimension": "dimension"}.get(kind)
        if primitive is None: raise GrammarValidationError(f"unsupported geometry kind: {kind}")
        payload = {"kind": kind, "frame_id": frame_id}
        if "coordinates" in obj:
            coords = obj["coordinates"]
            if not isinstance(coords, Sequence) or isinstance(coords, (str, bytes)) or len(coords) not in (2, 3): raise GrammarValidationError("coordinates must contain 2 or 3 numbers")
            payload["coordinates"] = [finite_number(v, field_name=f"{oid}.coordinates") for v in coords]
        if kind == "dimension":
            value = finite_number(obj.get("value"), field_name=f"{oid}.value")
            unit = str(obj.get("unit", "")).strip()
            if not unit: raise GrammarValidationError("dimension requires unit")
            payload.update({"value": value, "unit": unit})
        refs = obj.get("refs", [])
        if refs:
            if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes)): raise GrammarValidationError("refs must be a sequence")
            payload["refs"] = [str(r).strip() for r in refs]
        elements.append({"id": f"geom:{oid}", "role": "geometry_object", "primitive": primitive, "label": str(obj.get("label", oid)), "source_ids": list(obj.get("source_ids", evidence_refs)), "payload": payload})
    if not elements: raise GrammarValidationError("at least one geometry object is required")
    for element in elements:
        for ref in element["payload"].get("refs", []):
            if ref not in ids: raise GrammarValidationError(f"geometry object references unknown id: {ref}")
    warnings = ["visual appearance alone must not be used as geometric proof"]
    return make_plan(GEOMETRY_GRAMMAR, evidence_refs=evidence_refs, reasoning_refs=reasoning_refs, elements=elements, constraints=GEOMETRY_GRAMMAR.semantic_constraints, warnings=warnings)
