from __future__ import annotations

from typing import Any, Mapping, Sequence
from .grammar_contracts import VisualGrammar, GrammarValidationError, finite_number, make_plan

FIELD_GRAMMAR = VisualGrammar(
    grammar_id="bie.vis.grammar.field",
    version="1.0.0",
    domains=("physics", "engineering", "mathematics"),
    representations=("field", "field_map"),
    allowed_primitives=("axis", "source_marker", "field_arrow", "field_line", "contour", "label", "sample_point"),
    required_roles=("reference_frame", "field_sample"),
    semantic_constraints=(
        "field samples must retain coordinates and declared field type",
        "field lines/contours are derived only when explicitly requested and supported by supplied samples/model evidence",
        "no direction or source sign may be invented",
    ),
    aliases=("field-grammar",), tags=("field", "vector_field", "scalar_field"),
)


def plan_field(samples: Sequence[Mapping[str, Any]], *, field_type: str, frame_id: str, evidence_refs: Sequence[str], reasoning_refs: Sequence[str], derived_lines: bool = False):
    field_type = str(field_type).strip().lower()
    if field_type not in {"scalar", "vector"}:
        raise GrammarValidationError("field_type must be scalar or vector")
    if not isinstance(frame_id, str) or not frame_id.strip():
        raise GrammarValidationError("frame_id must be non-blank")
    elements = [{"id": f"frame:{frame_id}", "role": "reference_frame", "primitive": "axis", "label": frame_id, "source_ids": list(evidence_refs), "payload": {"frame_id": frame_id}}]
    seen = set()
    for sample in samples:
        sid = str(sample.get("id", "")).strip()
        if not sid or sid in seen:
            raise GrammarValidationError("sample ids must be non-blank and unique")
        seen.add(sid)
        coordinates = sample.get("coordinates")
        if not isinstance(coordinates, Sequence) or isinstance(coordinates, (str, bytes)) or len(coordinates) not in (2, 3):
            raise GrammarValidationError(f"sample {sid} coordinates must have 2 or 3 values")
        coords = [finite_number(v, field_name=f"{sid}.coordinates") for v in coordinates]
        if field_type == "scalar":
            value = finite_number(sample.get("value"), field_name=f"{sid}.value")
            payload = {"coordinates": coords, "value": value, "field_type": field_type}
            primitive = "sample_point"
        else:
            vector = sample.get("vector")
            if not isinstance(vector, Sequence) or isinstance(vector, (str, bytes)) or len(vector) != len(coords):
                raise GrammarValidationError(f"sample {sid} vector dimensionality must match coordinates")
            payload = {"coordinates": coords, "vector": [finite_number(v, field_name=f"{sid}.vector") for v in vector], "field_type": field_type}
            primitive = "field_arrow"
        elements.append({"id": f"sample:{sid}", "role": "field_sample", "primitive": primitive, "label": str(sample.get("label", sid)), "source_ids": list(sample.get("source_ids", evidence_refs)), "payload": payload})
    if not samples:
        raise GrammarValidationError("at least one field sample is required")
    warnings = []
    if derived_lines:
        warnings.append("field lines/contours are derivation requests; downstream computation must prove them from the bound model or samples")
    return make_plan(FIELD_GRAMMAR, evidence_refs=evidence_refs, reasoning_refs=reasoning_refs, elements=elements, constraints=FIELD_GRAMMAR.semantic_constraints, warnings=warnings)
