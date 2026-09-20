from __future__ import annotations

from typing import Any, Mapping, Sequence
from .grammar_contracts import VisualGrammar, GrammarValidationError, finite_number, make_plan

HISTORY_TIMELINE_GRAMMAR = VisualGrammar(
    grammar_id="bie.vis.grammar.history_timeline", version="1.0.0",
    domains=("history", "civics"), representations=("timeline", "chronology"),
    allowed_primitives=("timeline_axis", "event_marker", "interval", "uncertainty_band", "label", "era_band"),
    required_roles=("timeline_axis", "historical_event"),
    semantic_constraints=("uncertain dates remain uncertain", "simultaneity and intervals are preserved", "visual order must follow declared chronology rather than lexical label order"),
    aliases=("history-timeline",), tags=("history", "timeline", "chronology", "uncertainty"),
)


def plan_timeline(events: Sequence[Mapping[str, Any]], *, evidence_refs: Sequence[str], reasoning_refs: Sequence[str], axis_label: str = "time"):
    if not isinstance(axis_label, str) or not axis_label.strip(): raise GrammarValidationError("axis_label must be non-blank")
    elements = [{"id": "timeline:axis", "role": "timeline_axis", "primitive": "timeline_axis", "label": axis_label.strip(), "source_ids": list(evidence_refs), "payload": {"axis_label": axis_label.strip()}}]
    normalized = []
    seen = set()
    for event in events:
        eid = str(event.get("id", "")).strip()
        if not eid or eid in seen: raise GrammarValidationError("event ids must be non-blank and unique")
        seen.add(eid)
        label = str(event.get("label", eid)).strip()
        time_label = str(event.get("time_label", "")).strip()
        if not time_label: raise GrammarValidationError(f"event {eid} needs a time_label")
        order_key = event.get("order_key")
        lower, upper = event.get("lower_bound"), event.get("upper_bound")
        if order_key is None and lower is None and upper is None:
            raise GrammarValidationError(f"event {eid} needs order_key or temporal bounds")
        if order_key is not None: order_key = finite_number(order_key, field_name=f"{eid}.order_key")
        if lower is not None: lower = finite_number(lower, field_name=f"{eid}.lower_bound")
        if upper is not None: upper = finite_number(upper, field_name=f"{eid}.upper_bound")
        if lower is not None and upper is not None and lower > upper:
            raise GrammarValidationError(f"event {eid} lower_bound exceeds upper_bound")
        uncertain = bool(event.get("uncertain", False)) or (lower is not None and upper is not None and lower != upper)
        normalized.append((order_key if order_key is not None else (lower if lower is not None else upper), eid, label, time_label, lower, upper, uncertain, event))
    if not normalized: raise GrammarValidationError("at least one historical event is required")
    normalized.sort(key=lambda row: (row[0], row[1]))
    for position, (_, eid, label, time_label, lower, upper, uncertain, raw) in enumerate(normalized):
        primitive = "uncertainty_band" if uncertain else ("interval" if lower is not None and upper is not None and lower != upper else "event_marker")
        elements.append({"id": f"event:{eid}", "role": "historical_event", "primitive": primitive, "label": label, "source_ids": list(raw.get("source_ids", evidence_refs)), "payload": {"time_label": time_label, "lower_bound": lower, "upper_bound": upper, "uncertain": uncertain, "ordinal_position": position}})
    warnings = ["timeline positions encode declared chronology; geometric spacing is not a duration claim unless bounds support it"]
    return make_plan(HISTORY_TIMELINE_GRAMMAR, evidence_refs=evidence_refs, reasoning_refs=reasoning_refs, elements=elements, constraints=HISTORY_TIMELINE_GRAMMAR.semantic_constraints, warnings=warnings)
