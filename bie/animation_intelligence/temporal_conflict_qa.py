from .qa_contracts import *
def evaluate(events,allow_same_target_overlap=False,max_parallel_essential=2):
    events=tuple(events)
    if not events:return result("qa:temporal","UNSUPPORTED",blockers=("no_events",))
    blockers=[];warnings=[]
    for i,a in enumerate(events):
      for b in events[i+1:]:
        if max(a.start_ms,b.start_ms)>=min(a.end_ms,b.end_ms): continue
        if set(a.targets)&set(b.targets) and not allow_same_target_overlap:blockers.append(f"same_target:{a.event_id}:{b.event_id}")
        if a.action in {"trace","path_follow","simulation_state"} and b.action in {"trace","path_follow","simulation_state"}:warnings.append(f"rate_sensitive_overlap:{a.event_id}:{b.event_id}")
    points=sorted({x for e in events for x in (e.start_ms,e.end_ms)})
    for t in points:
      if sum(1 for e in events if e.essential and e.start_ms<=t<e.end_ms)>max_parallel_essential:
        blockers.append(f"essential_concurrency@{t}");break
    score=max(0,1-.2*len(set(blockers))-.08*len(set(warnings)))
    return result("qa:temporal","BLOCKED" if blockers else ("REVIEW" if warnings else "PASS"),score,sorted(set(blockers)),sorted(set(warnings)))
