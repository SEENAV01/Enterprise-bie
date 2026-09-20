from .attention_contracts import *

def sync_narration_attention(*, decision_id, narration_revision, cue_windows, attention_windows,
                             require_exact_revision=True, allow_overlap_same_target=True):
    cues=tuple(cue_windows); attn=tuple(attention_windows)
    if not cues or not attn:
        raise AttentionError("narration and attention windows required")
    blockers=[]; warnings=[]
    for w in attn:
        if require_exact_revision and w.narration_revision!=narration_revision:
            blockers.append("stale_attention_revision:"+w.window_id)
        overlaps=[c for c in cues if max(c.start_ms,w.start_ms)<min(c.end_ms,w.end_ms)]
        if not overlaps:
            blockers.append("attention_window_not_bound_to_narration:"+w.window_id)
        if len(overlaps)>1 and w.exclusive:
            warnings.append("exclusive_attention_spans_multiple_narration_cues:"+w.window_id)
    if not allow_overlap_same_target:
        for i,a in enumerate(attn):
            for b in attn[i+1:]:
                if set(a.target_ids)&set(b.target_ids) and max(a.start_ms,b.start_ms)<min(a.end_ms,b.end_ms):
                    blockers.append("same_target_attention_overlap:"+a.window_id+":"+b.window_id)
    status="BLOCKED" if blockers else ("REVIEW" if warnings else "PASS")
    primary=attn[0].target_ids[0] if attn else None
    ev=tuple(sorted({e for w in attn for e in w.payload.get("evidence_refs",())}))
    rr=tuple(sorted({r for w in attn for r in w.payload.get("reasoning_refs",())}))
    return make_decision(decision_id,status=status,primary_target=primary,windows=attn,
                         blockers=tuple(blockers),warnings=tuple(warnings),evidence_refs=ev,reasoning_refs=rr)
