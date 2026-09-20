from dataclasses import dataclass
from .qa_contracts import *
@dataclass(frozen=True)
class Case:
    case_id:str;purpose:float|None;temporal:float|None;motion:float|None;sync:float|None;grounding:float|None;empirical_render:bool|None=None
def run(cases,metric_floor=.80,aggregate_floor=.86,require_empirical=False):
    cases=tuple(cases)
    if not cases:return result("qa:benchmark","NOT_RUN",blockers=("cases_required",))
    if len({c.case_id for c in cases})!=len(cases):raise AnimationQAError("duplicate cases")
    blockers=[];scores=[]
    for c in cases:
      vals=(c.purpose,c.temporal,c.motion,c.sync,c.grounding)
      if any(v is None for v in vals):blockers.append(f"metrics_not_run:{c.case_id}")
      scored=[v for v in vals if v is not None]
      if any(v is not None and v<metric_floor for v in vals):blockers.append(f"metric_below_floor:{c.case_id}")
      if scored:scores.append(sum(scored)/len(scored))
      if require_empirical and c.empirical_render is None:blockers.append(f"empirical_not_run:{c.case_id}")
      if c.empirical_render is False:blockers.append(f"empirical_failed:{c.case_id}")
    agg=sum(scores)/len(scores) if scores else None
    if agg is None:blockers.append("aggregate_not_computable")
    elif agg<aggregate_floor:blockers.append("aggregate_below_floor")
    return result("qa:benchmark","BLOCKED" if blockers else "PASS",None if agg is None else round(agg,6),sorted(set(blockers)))
