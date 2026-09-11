from __future__ import annotations
from bie.reasoning.chronology_reasoning import chronology
from bie.reasoning.event_order_reasoning import event_order
from bie.reasoning.periodization_reasoning import periodization
from bie.reasoning.temporal_synthesis_reasoning import synthesize_timeline
from bie.reasoning.grounded_result import inference
TASK_ID="BIE-RE-TEMP-018"
def temporal_reasoning_engine(events,constraints,periods,refs):
    events, constraints, periods, refs = tuple(events), tuple(constraints), tuple(periods), tuple(refs)
    c=chronology(events,refs); o=event_order(events,constraints,refs); p=periodization(events,periods,refs); s=synthesize_timeline(events,constraints,periods,refs)
    results=(c,o,p,s); conflict=any(r.status=="CONFLICT" for r in results); review=any(r.requires_review for r in results)
    status="CONFLICT" if conflict else ("AMBIGUOUS" if review else "RESOLVED")
    value={"chronology_result_id":c.result_id,"order_result_id":o.result_id,"periodization_result_id":p.result_id,"synthesis_result_id":s.result_id,"timeline":s.value,"requires_review":review,"component_statuses":{r.operation:r.status for r in results}}
    return inference(TASK_ID,"temporal.engine",{"event_count":len(tuple(events)),"constraint_count":len(tuple(constraints)),"period_count":len(tuple(periods))},value,refs,status=status,assumptions=("The engine preserves component conflicts and ambiguity",),uncertainty=("One or more temporal components require review",) if review else ())
