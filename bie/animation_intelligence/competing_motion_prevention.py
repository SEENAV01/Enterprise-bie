from .attention_contracts import *

def prevent_competing_motion(*, decision_id, windows, motion_targets, max_simultaneous_motion=1):
    windows=tuple(windows); motion_targets=dict(motion_targets)
    if max_simultaneous_motion<1:
        raise AttentionError("max_simultaneous_motion must be >=1")
    conflicts=[]; warnings=[]
    ordered=sorted(windows,key=lambda w:(w.start_ms,w.end_ms,w.window_id))
    for i,a in enumerate(ordered):
        active_a=set(motion_targets.get(a.window_id,()))
        for b in ordered[i+1:]:
            if max(a.start_ms,b.start_ms)>=min(a.end_ms,b.end_ms):
                continue
            active=active_a | set(motion_targets.get(b.window_id,()))
            if len(active)>max_simultaneous_motion and (a.exclusive or b.exclusive):
                conflicts.append((a.window_id,b.window_id,tuple(sorted(active))))
    if conflicts:
        blockers=tuple(f"competing_motion:{a}:{b}" for a,b,_ in conflicts)
        return make_decision(decision_id,status="BLOCKED",primary_target=None,blockers=blockers,
                             warnings=("serialize_or_suppress_nonessential_motion",),
                             evidence_refs=tuple(sorted({e for w in windows for e in w.payload.get("evidence_refs",())})),
                             reasoning_refs=tuple(sorted({r for w in windows for r in w.payload.get("reasoning_refs",())})))
    if len(ordered)>4:
        warnings.append("dense_attention_schedule")
    return make_decision(decision_id,status="REVIEW" if warnings else "PASS",primary_target=None,
                         warnings=tuple(warnings))
