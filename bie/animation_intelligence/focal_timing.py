from .attention_contracts import *

def plan_focal_timing(*, decision_id, target:AttentionTarget, cue_start_ms, cue_end_ms,
                      narration_revision, lead_ms=120, tail_ms=80, min_focus_ms=250):
    if cue_start_ms<0 or cue_end_ms<=cue_start_ms:
        raise AttentionTimingError("invalid cue interval")
    if min_focus_ms<1 or lead_ms<0 or tail_ms<0:
        raise AttentionTimingError("invalid focal timing parameters")
    start=max(0,cue_start_ms-lead_ms)
    end=cue_end_ms+tail_ms
    if end-start<min_focus_ms:
        end=start+min_focus_ms
    window=AttentionWindow(decision_id+":window",(target.target_id,),start,end,target.importance,
                           "focus window bound to narration cue",narration_revision,True,
                           {"cue_start_ms":cue_start_ms,"cue_end_ms":cue_end_ms,
                            "lead_ms":lead_ms,"tail_ms":tail_ms})
    return make_decision(decision_id,status="PASS",primary_target=target.target_id,
                         windows=(window,),evidence_refs=target.evidence_refs,reasoning_refs=target.reasoning_refs)
