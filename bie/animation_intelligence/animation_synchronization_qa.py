from .qa_contracts import *
def evaluate(events,narration_revision,cues,max_start_drift_ms=200,max_end_drift_ms=250):
    events=tuple(events);cues=tuple(cues)
    if not events or not cues:return result("qa:sync","NOT_RUN",blockers=("events_and_cues_required",))
    blockers=[];warnings=[];pairs=[]
    for e in events:
      if e.narration_revision!=narration_revision:blockers.append(f"stale_revision:{e.event_id}")
      ovs=[c for c in cues if max(e.start_ms,c["start_ms"])<min(e.end_ms,c["end_ms"])]
      if not ovs:blockers.append(f"unbound:{e.event_id}");continue
      c=max(ovs,key=lambda x:min(e.end_ms,x["end_ms"])-max(e.start_ms,x["start_ms"]))
      if not (c["start_ms"]<=e.start_ms and e.end_ms<=c["end_ms"]):blockers.append(f"escapes_cue:{e.event_id}")
      sd=abs(e.start_ms-c["start_ms"]);ed=abs(e.end_ms-c["end_ms"])
      if sd>max_start_drift_ms:warnings.append(f"start_drift:{e.event_id}")
      if ed>max_end_drift_ms:warnings.append(f"end_drift:{e.event_id}")
      pairs.append({"event_id":e.event_id,"cue_id":c["cue_id"],"start_drift":sd,"end_drift":ed})
    return result("qa:sync","BLOCKED" if blockers else ("REVIEW" if warnings else "PASS"),
                  max(0,1-.22*len(blockers)-.06*len(warnings)),blockers,warnings,{"pairs":pairs})
