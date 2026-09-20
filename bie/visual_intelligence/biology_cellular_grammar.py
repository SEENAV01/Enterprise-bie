from __future__ import annotations

from typing import Any, Mapping, Sequence
from .grammar_contracts import VisualGrammar, GrammarValidationError, make_plan

BIOLOGY_CELLULAR_GRAMMAR = VisualGrammar(
    grammar_id="bie.vis.grammar.biology_cellular", version="1.0.0",
    domains=("biology",), representations=("cell_diagram", "cellular_process"),
    allowed_primitives=("cell_boundary", "organelle", "molecule", "transport_arrow", "label", "membrane", "region"),
    required_roles=("cell_or_region",),
    semantic_constraints=("compartment containment is explicit", "transport arrows encode declared transport only", "diagrammatic size is not physical scale unless scale metadata is supplied"),
    aliases=("biology-cellular",), tags=("cell", "organelle", "transport"),
)


def plan_cellular_diagram(components: Sequence[Mapping[str, Any]], transports: Sequence[Mapping[str, Any]], *, evidence_refs: Sequence[str], reasoning_refs: Sequence[str], scale_bar: str | None = None):
    elements = []
    ids = set()
    for comp in components:
        cid = str(comp.get("id", "")).strip()
        if not cid or cid in ids:
            raise GrammarValidationError("component ids must be non-blank and unique")
        ids.add(cid)
        kind = str(comp.get("kind", "region")).strip().lower()
        primitive = {"cell": "cell_boundary", "organelle": "organelle", "molecule": "molecule", "membrane": "membrane", "region": "region"}.get(kind)
        if primitive is None:
            raise GrammarValidationError(f"unsupported cellular kind: {kind}")
        role = "cell_or_region" if kind in {"cell", "region"} else kind
        elements.append({"id": f"bio:{cid}", "role": role, "primitive": primitive, "label": str(comp.get("label", cid)), "source_ids": list(comp.get("source_ids", evidence_refs)), "payload": {"kind": kind, "parent_id": comp.get("parent_id"), "scale_bar": scale_bar}})
    if not elements:
        raise GrammarValidationError("at least one cellular component is required")
    relations = []
    for i, tr in enumerate(transports):
        src, dst = str(tr.get("source", "")).strip(), str(tr.get("target", "")).strip()
        if src not in ids or dst not in ids:
            raise GrammarValidationError("transport references unknown component")
        substance = str(tr.get("substance", "")).strip()
        if not substance:
            raise GrammarValidationError("transport substance must be explicit")
        relations.append({"id": f"transport:{i}", "source": f"bio:{src}", "target": f"bio:{dst}", "kind": "transport", "source_ids": list(tr.get("source_ids", evidence_refs)), "payload": {"substance": substance, "mechanism": tr.get("mechanism")}})
    warnings = [] if scale_bar else ["diagram is schematic; visual size must not be interpreted as physical scale"]
    return make_plan(BIOLOGY_CELLULAR_GRAMMAR, evidence_refs=evidence_refs, reasoning_refs=reasoning_refs, elements=elements, relations=relations, constraints=BIOLOGY_CELLULAR_GRAMMAR.semantic_constraints, warnings=warnings)
