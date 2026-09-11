"""RE-TEMP-013: integrated temporal timeline synthesis over events, constraints and periods."""
from __future__ import annotations
from dataclasses import asdict
from bie.reasoning.chronology_reasoning import validate_events
from bie.reasoning.event_order_reasoning import event_order
from bie.reasoning.periodization_reasoning import periodization
from bie.reasoning.grounded_result import inference
TASK_ID="BIE-RE-TEMP-013"


def synthesize_timeline(events,constraints,periods,refs):
    constraints, periods = tuple(constraints), tuple(periods)
    events,refs=validate_events(events,refs)
    ordered=event_order(events,constraints,refs)
    assigned=periodization(events,periods,refs)
    conflict=ordered.status=="CONFLICT"
    ambiguous=ordered.status=="AMBIGUOUS" or assigned.status=="AMBIGUOUS"
    if conflict:
        status="CONFLICT"; sequence=[]
    else:
        status="AMBIGUOUS" if ambiguous else "RESOLVED"
        sequence=ordered.value["linear_extension"]
    assignment_by={x["event_id"]:x for x in assigned.value["assignments"]}
    event_by={e.event_id:e for e in events}
    rows=[]
    for event_id in (sequence if sequence else sorted(event_by)):
        event=event_by[event_id]; a=assignment_by[event_id]
        rows.append({"event_id":event_id,"label":event.label,"time":asdict(event.time),"definite_period_ids":a["definite_period_ids"],"possible_period_ids":a["possible_period_ids"],"event_evidence_ids":sorted(event.evidence_ids),"period_assignment_status":a["status"]})
    value={"axis":events[0].time.axis,"timeline_rows":rows,"proven_sequence":sequence,"order_status":ordered.status,"periodization_status":assigned.status,"order_cycle_witness":ordered.value["cycle_witness"],"order_violations":ordered.value["violations"],"overlapping_periods":assigned.value["overlapping_siblings"]}
    uncertainty=[]
    if conflict: uncertainty.append("Conflicting temporal order prevents a valid synthesized sequence")
    if ordered.status=="AMBIGUOUS": uncertainty.append("Multiple temporal orders remain possible")
    if assigned.status=="AMBIGUOUS": uncertainty.append("One or more period assignments remain ambiguous")
    inputs={"events":[asdict(e) for e in events],"constraints":[asdict(c) for c in constraints],"periods":[asdict(p) for p in periods]}
    return inference(TASK_ID,"temporal.timeline_synthesis",inputs,value,refs,status=status,assumptions=("Synthesis preserves upstream temporal ambiguity/conflict rather than inventing a narrative order",),uncertainty=tuple(uncertainty))
