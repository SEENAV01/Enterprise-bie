from .qa_contracts import *
MAP={"introduce":{"enter","reveal"},"remove":{"exit"},"focus":{"emphasize","camera"},
     "show_change":{"transform","morph","simulation_state"},"show_direction":{"trace","path_follow"},
     "show_sequence":{"reveal","transform","simulation_state"},"show_relation":{"emphasize","trace","transform"}}
def evaluate(events,allow_unmapped=False):
    events=tuple(events)
    if not events:return result("qa:purpose","UNSUPPORTED",blockers=("no_events",))
    blockers=[];warnings=[]
    for e in events:
      allowed=MAP.get(e.purpose)
      if allowed is None:
        (warnings if allow_unmapped else blockers).append(f"unmapped:{e.event_id}");continue
      if e.action not in allowed:blockers.append(f"misaligned:{e.event_id}")
      elif not e.essential:warnings.append(f"nonessential:{e.event_id}")
    return result("qa:purpose","BLOCKED" if blockers else ("REVIEW" if warnings else "PASS"),
                  max(0,1-.25*len(blockers)-.08*len(warnings)),blockers,warnings)
