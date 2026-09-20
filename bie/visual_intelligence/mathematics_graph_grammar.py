from __future__ import annotations

from typing import Any, Mapping, Sequence
from .grammar_contracts import VisualGrammar, GrammarValidationError, finite_number, make_plan

MATHEMATICS_GRAPH_GRAMMAR = VisualGrammar(
    grammar_id="bie.vis.grammar.mathematics_graph", version="1.0.0",
    domains=("mathematics", "physics", "economics", "data_science"), representations=("function_graph", "coordinate_graph"),
    allowed_primitives=("axis", "curve", "sample_point", "asymptote", "interval_highlight", "label", "tangent"),
    required_roles=("coordinate_frame", "graph_object"),
    semantic_constraints=("axis scales and units are explicit", "sampled data are not presented as an exact analytic curve", "discontinuities and domain restrictions remain visible"),
    aliases=("mathematics-graph",), tags=("graph", "function", "axis"),
)


def plan_math_graph(series: Sequence[Mapping[str, Any]], *, x_label: str, y_label: str, evidence_refs: Sequence[str], reasoning_refs: Sequence[str], x_scale: str = "linear", y_scale: str = "linear"):
    if x_scale not in {"linear", "log"} or y_scale not in {"linear", "log"}: raise GrammarValidationError("axis scale must be linear or log")
    if not str(x_label).strip() or not str(y_label).strip(): raise GrammarValidationError("axis labels must be non-blank")
    elements = [{"id": "graph:frame", "role": "coordinate_frame", "primitive": "axis", "label": f"{x_label} vs {y_label}", "source_ids": list(evidence_refs), "payload": {"x_label": x_label, "y_label": y_label, "x_scale": x_scale, "y_scale": y_scale}}]
    seen = set(); warnings = []
    for item in series:
        sid = str(item.get("id", "")).strip()
        if not sid or sid in seen: raise GrammarValidationError("series ids must be non-blank and unique")
        seen.add(sid)
        kind = str(item.get("kind", "samples")).strip().lower()
        if kind not in {"samples", "analytic"}: raise GrammarValidationError("series kind must be samples or analytic")
        payload: dict[str, Any] = {"kind": kind, "domain": item.get("domain"), "discontinuities": item.get("discontinuities", [])}
        primitive = "curve"
        if kind == "samples":
            points = item.get("points")
            if not isinstance(points, Sequence) or isinstance(points, (str, bytes)) or len(points) < 2: raise GrammarValidationError("sample series needs at least two points")
            normalized = []
            for p in points:
                if not isinstance(p, Sequence) or isinstance(p, (str, bytes)) or len(p) != 2: raise GrammarValidationError("graph point must contain x,y")
                x, y = finite_number(p[0], field_name=f"{sid}.x"), finite_number(p[1], field_name=f"{sid}.y")
                if x_scale == "log" and x <= 0: raise GrammarValidationError("log x-scale requires positive x")
                if y_scale == "log" and y <= 0: raise GrammarValidationError("log y-scale requires positive y")
                normalized.append([x, y])
            payload["points"] = normalized
            payload["interpolation_claim"] = False
            warnings.append(f"{sid}: sampled points must not be narrated as an exact analytic curve")
        else:
            expression = str(item.get("expression", "")).strip()
            if not expression: raise GrammarValidationError("analytic series requires an expression")
            payload["expression"] = expression
            payload["interpolation_claim"] = None
        elements.append({"id": f"series:{sid}", "role": "graph_object", "primitive": primitive, "label": str(item.get("label", sid)), "source_ids": list(item.get("source_ids", evidence_refs)), "payload": payload})
    if not series: raise GrammarValidationError("at least one graph series is required")
    return make_plan(MATHEMATICS_GRAPH_GRAMMAR, evidence_refs=evidence_refs, reasoning_refs=reasoning_refs, elements=elements, constraints=MATHEMATICS_GRAPH_GRAMMAR.semantic_constraints, warnings=warnings)
