from __future__ import annotations

from typing import Any, Mapping, Sequence
from .grammar_contracts import VisualGrammar, GrammarValidationError, finite_number, make_plan

DATA_CHART_GRAMMAR = VisualGrammar(
    grammar_id="bie.vis.grammar.data_chart", version="1.0.0",
    domains=("data_science", "statistics", "economics", "science", "*"), representations=("chart", "data_chart"),
    allowed_primitives=("axis", "bar", "line_series", "point_series", "area", "pie_slice", "error_bar", "legend", "label"),
    required_roles=("chart_frame", "data_series"),
    semantic_constraints=("encoding channels are explicit", "uncertainty/error values remain visible when supplied", "truncated baselines and aggregation choices are disclosed"),
    aliases=("data-chart",), tags=("chart", "data", "encoding"),
)


def plan_chart(series: Sequence[Mapping[str, Any]], *, chart_type: str, x_label: str, y_label: str, evidence_refs: Sequence[str], reasoning_refs: Sequence[str], y_baseline: float | None = 0.0):
    chart_type = str(chart_type).strip().lower()
    if chart_type not in {"bar", "line", "scatter", "area", "pie"}: raise GrammarValidationError("unsupported chart_type")
    if not str(x_label).strip() or not str(y_label).strip(): raise GrammarValidationError("axis labels must be non-blank")
    baseline = None if y_baseline is None else finite_number(y_baseline, field_name="y_baseline")
    elements = [{"id": "chart:frame", "role": "chart_frame", "primitive": "axis", "label": f"{x_label} / {y_label}", "source_ids": list(evidence_refs), "payload": {"chart_type": chart_type, "x_label": x_label, "y_label": y_label, "y_baseline": baseline}}]
    seen = set(); warnings = []
    for item in series:
        sid = str(item.get("id", "")).strip()
        if not sid or sid in seen: raise GrammarValidationError("series ids must be non-blank and unique")
        seen.add(sid)
        values = item.get("values")
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or not values: raise GrammarValidationError("series values must be a non-empty sequence")
        normalized = []
        for row in values:
            if not isinstance(row, Mapping): raise GrammarValidationError("each chart datum must be a mapping")
            x = row.get("x"); y = finite_number(row.get("y"), field_name=f"{sid}.y")
            if chart_type == "pie" and y < 0: raise GrammarValidationError("pie values cannot be negative")
            datum = {"x": x, "y": y}
            if row.get("error") is not None:
                err = finite_number(row.get("error"), field_name=f"{sid}.error")
                if err < 0: raise GrammarValidationError("error magnitude must be non-negative")
                datum["error"] = err
            normalized.append(datum)
        primitive = {"bar": "bar", "line": "line_series", "scatter": "point_series", "area": "area", "pie": "pie_slice"}[chart_type]
        elements.append({"id": f"series:{sid}", "role": "data_series", "primitive": primitive, "label": str(item.get("label", sid)), "source_ids": list(item.get("source_ids", evidence_refs)), "payload": {"values": normalized, "aggregation": item.get("aggregation"), "encoding": item.get("encoding", {"x": "position", "y": "position"})}})
    if not series: raise GrammarValidationError("at least one data series is required")
    if chart_type in {"bar", "area"} and baseline not in {0.0, None}: warnings.append("non-zero baseline must be visibly disclosed")
    if chart_type == "pie": warnings.append("pie chart encodes part-to-whole only; downstream QA must verify total semantics")
    return make_plan(DATA_CHART_GRAMMAR, evidence_refs=evidence_refs, reasoning_refs=reasoning_refs, elements=elements, constraints=DATA_CHART_GRAMMAR.semantic_constraints, warnings=warnings)
