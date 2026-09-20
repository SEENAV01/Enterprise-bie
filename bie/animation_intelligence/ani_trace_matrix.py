from dataclasses import dataclass

class AniTraceError(ValueError): pass

@dataclass(frozen=True)
class TrackTrace:
    track_id:str
    source_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    visual_ids:tuple[str,...]
    owner_stage:str
    qa_ids:tuple[str,...]
    downstream_node_ids:tuple[str,...]=()
    required:bool=True

@dataclass(frozen=True)
class TraceAudit:
    rows:tuple[TrackTrace,...]
    blockers:tuple[str,...]
    passed:bool
    review_required:bool=True
    accepted:bool=False

def audit_trace(rows):
    rows=tuple(rows)
    if len({r.track_id for r in rows})!=len(rows):
        raise AniTraceError("duplicate track_id")
    blockers=[]
    for r in rows:
        if not r.track_id: blockers.append("missing_track_id")
        if not r.source_refs: blockers.append("missing_source:"+r.track_id)
        if not r.reasoning_refs: blockers.append("missing_reasoning:"+r.track_id)
        if not r.visual_ids: blockers.append("missing_visual:"+r.track_id)
        if r.required and not r.qa_ids: blockers.append("missing_qa:"+r.track_id)
        if r.required and not r.downstream_node_ids: blockers.append("missing_downstream:"+r.track_id)
    return TraceAudit(rows,tuple(sorted(set(blockers))),not blockers,True,False)

def require_trace_pass(audit):
    if not audit.passed:
        raise AniTraceError("trace audit blocked")
    return True
