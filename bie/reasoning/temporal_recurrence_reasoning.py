"""RE-TEMP-010: bounded evidence-grounded recurrence expansion."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from bie.reasoning.grounded_result import evidence, identifier, inference, require_refs
TASK_ID="BIE-RE-TEMP-010"

@dataclass(frozen=True)
class RecurrenceRule:
    rule_id: str
    subject_id: str
    first_tick: int
    cadence_ticks: int
    evidence_ids: tuple[str, ...]
    last_tick: int | None = None
    max_occurrences: int | None = None


def expand_recurrence(rule, window_start, window_end, axis, refs):
    refs=evidence(refs)
    if not isinstance(rule,RecurrenceRule): raise ValueError("Expected RecurrenceRule")
    identifier(rule.rule_id,"rule id"); identifier(rule.subject_id,"subject id"); identifier(axis,"axis")
    require_refs(rule.evidence_ids,refs)
    if axis not in {"historical_year","gregorian_day"}: raise ValueError("Unsupported temporal axis")
    for name,value in (("first_tick",rule.first_tick),("cadence_ticks",rule.cadence_ticks),("window_start",window_start),("window_end",window_end)):
        if isinstance(value,bool) or not isinstance(value,int): raise ValueError(f"{name} must be an integer tick")
    if rule.cadence_ticks<=0 or window_start>window_end: raise ValueError("Positive cadence and ordered window required")
    if rule.last_tick is not None and (isinstance(rule.last_tick,bool) or not isinstance(rule.last_tick,int) or rule.last_tick<rule.first_tick): raise ValueError("Invalid recurrence last tick")
    if rule.max_occurrences is not None and (isinstance(rule.max_occurrences,bool) or not isinstance(rule.max_occurrences,int) or rule.max_occurrences<=0): raise ValueError("max_occurrences must be positive")
    occurrences=[]; tick=rule.first_tick; idx=1
    while tick<=window_end:
        if rule.last_tick is not None and tick>rule.last_tick: break
        if rule.max_occurrences is not None and idx>rule.max_occurrences: break
        if tick>=window_start: occurrences.append({"index":idx,"tick":tick})
        tick += rule.cadence_ticks; idx += 1
        if idx>1000000: raise ValueError("Recurrence expansion safety bound exceeded")
    value={"subject_id":rule.subject_id,"axis":axis,"window":{"start":window_start,"end":window_end},"occurrences":occurrences,"bounded_by":"last_tick" if rule.last_tick is not None else "max_occurrences" if rule.max_occurrences is not None else "query_window","evidence_ids":sorted(rule.evidence_ids)}
    return inference(TASK_ID,"temporal.recurrence",{"rule":asdict(rule),"window_start":window_start,"window_end":window_end,"axis":axis},value,refs,status="RESOLVED",assumptions=("Cadence is constant in integer ticks of the declared axis",))
