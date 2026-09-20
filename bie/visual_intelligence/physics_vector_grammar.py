from __future__ import annotations

from typing import Any, Mapping, Sequence
from .grammar_contracts import VisualGrammar, GrammarValidationError, finite_number, make_plan

PHYSICS_VECTOR_GRAMMAR = VisualGrammar(
    grammar_id="bie.vis.grammar.physics_vector",
    version="1.0.0",
    domains=("physics", "engineering"),
    representations=("vector_diagram", "free_body_diagram"),
    allowed_primitives=("axis", "arrow", "point", "label", "angle_arc", "component_guide"),
    required_roles=("reference_frame", "vector"),
    semantic_constraints=(
        "vectors require an explicit reference frame",
        "arrow direction encodes signed direction; magnitude is never inferred from arrow length unless scale is explicit",
        "component guides must preserve the declared basis",
    ),
    aliases=("physics-vector",),
    tags=("vector", "magnitude", "direction"),
    description="Evidence-bound grammar for physical vector and free-body representations.",
)


def plan_physics_vectors(
    vectors: Sequence[Mapping[str, Any]], *, frame_id: str, evidence_refs: Sequence[str], reasoning_refs: Sequence[str], scale: float | None = None
):
    if not isinstance(frame_id, str) or not frame_id.strip():
        raise GrammarValidationError("frame_id must be non-blank")
    if scale is not None and finite_number(scale, field_name="scale") <= 0:
        raise GrammarValidationError("scale must be > 0")
    elements = [{
        "id": f"frame:{frame_id.strip()}", "role": "reference_frame", "primitive": "axis",
        "label": frame_id.strip(), "source_ids": list(evidence_refs),
        "payload": {"frame_id": frame_id.strip(), "scale": scale, "scale_is_semantic": scale is not None},
    }]
    relations = []
    seen = set()
    for raw in vectors:
        if not isinstance(raw, Mapping):
            raise GrammarValidationError("each vector must be a mapping")
        vector_id = str(raw.get("id", "")).strip()
        if not vector_id or vector_id in seen:
            raise GrammarValidationError("vector ids must be non-blank and unique")
        seen.add(vector_id)
        components = raw.get("components")
        direction = raw.get("direction")
        if components is None and direction is None:
            raise GrammarValidationError(f"vector {vector_id} needs components or direction")
        payload: dict[str, Any] = {"frame_id": frame_id.strip(), "quantity": str(raw.get("quantity", "vector")).strip() or "vector"}
        if components is not None:
            if not isinstance(components, Sequence) or isinstance(components, (str, bytes)) or len(components) not in (2, 3):
                raise GrammarValidationError(f"vector {vector_id} components must contain 2 or 3 numbers")
            payload["components"] = [finite_number(v, field_name=f"{vector_id}.components") for v in components]
        if direction is not None:
            if not isinstance(direction, Sequence) or isinstance(direction, (str, bytes)) or len(direction) not in (2, 3):
                raise GrammarValidationError(f"vector {vector_id} direction must contain 2 or 3 numbers")
            direction_values = [finite_number(v, field_name=f"{vector_id}.direction") for v in direction]
            if all(v == 0 for v in direction_values):
                raise GrammarValidationError(f"vector {vector_id} direction cannot be zero")
            payload["direction"] = direction_values
        magnitude = raw.get("magnitude")
        if magnitude is not None:
            magnitude = finite_number(magnitude, field_name=f"{vector_id}.magnitude")
            if magnitude < 0:
                raise GrammarValidationError("magnitude must be non-negative")
            payload["magnitude"] = magnitude
        unit = raw.get("unit")
        if unit is not None:
            if not isinstance(unit, str) or not unit.strip():
                raise GrammarValidationError("unit must be non-blank when supplied")
            payload["unit"] = unit.strip()
        source_ids = raw.get("source_ids", evidence_refs)
        element_id = f"vector:{vector_id}"
        elements.append({
            "id": element_id, "role": "vector", "primitive": "arrow", "label": str(raw.get("label", vector_id)),
            "source_ids": list(source_ids), "payload": payload,
        })
        relations.append({
            "id": f"bind:{vector_id}", "source": element_id, "target": f"frame:{frame_id.strip()}",
            "kind": "expressed_in", "source_ids": list(source_ids), "payload": {},
        })
    if not vectors:
        raise GrammarValidationError("at least one vector is required")
    warnings = [] if scale is not None else ["arrow length must not be interpreted as magnitude without an explicit scale"]
    return make_plan(
        PHYSICS_VECTOR_GRAMMAR, evidence_refs=evidence_refs, reasoning_refs=reasoning_refs,
        elements=elements, relations=relations, constraints=PHYSICS_VECTOR_GRAMMAR.semantic_constraints, warnings=warnings,
    )
