from .qa_contracts import *
HIGH={"camera","path_follow","morph","simulation_state","trace"}
def evaluate(events,reduced_motion_requested=False,max_budget=2.6,max_high=3):
    events=tuple(events)
    if not events:return result("qa:motion","UNSUPPORTED",blockers=("no_events",))
    blockers=[];warnings=[]
    budget=sum(e.motion*(1.25 if e.action in HIGH else 1) for e in events)
    high=sum(1 for e in events if e.action in HIGH and e.motion>=.65)
    if budget>max_budget:blockers.append("motion_budget_exceeded")
    if high>max_high:blockers.append("high_motion_limit_exceeded")
    if reduced_motion_requested and any(e.action in HIGH and e.motion>.25 for e in events):blockers.append("reduced_motion_not_applied")
    if any((not e.essential) and e.motion>.65 for e in events):warnings.append("decorative_high_motion")
    return result("qa:motion","BLOCKED" if blockers else ("REVIEW" if warnings else "PASS"),
                  max(0,1-.18*len(blockers)-.08*len(warnings)),blockers,warnings,
                  {"budget":round(budget,6),"high_motion":high})
