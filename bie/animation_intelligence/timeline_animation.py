from .temporal_contracts import *
def animate_timeline(ctx,timeline_id,events,scale_mode="ordinal",preserve_uncertainty=True):
    events=tuple(events)
    if len(events)<2:raise TimeOrderError("need >=2 events")
    if len({e.event_id for e in events})!=len(events):raise TimeOrderError("duplicate events")
    for e in events:
        if e.source_ref not in ctx.evidence_refs:raise TimeGroundingError("ungrounded event")
    blockers=[];warnings=[]
    if scale_mode not in {"ordinal","proportional","calendar"}:raise TimeError("bad scale")
    if scale_mode=="ordinal" and any(e.order_index is None for e in events):blockers.append("order_index_required")
    if scale_mode in {"proportional","calendar"} and any(e.time_value is None for e in events):blockers.append("numeric_time_required")
    if any(e.uncertain for e in events):
        if not preserve_uncertainty:blockers.append("uncertain_time_cannot_be_exact")
        else:warnings.append("show_uncertainty")
    if ctx.uncertainty>=.4:warnings.append("source_uncertainty")
    return plan(ctx,":timeline","timeline_animation","BLOCKED" if blockers else ("REVIEW" if warnings else "PASS"),
                ops=({"op":"timeline","timeline_id":timeline_id,"scale_mode":scale_mode,"events":[e.__dict__ for e in events],"preserve_uncertainty":preserve_uncertainty},),warnings=warnings,blockers=blockers)
