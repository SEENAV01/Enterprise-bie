from .element_common import *
def build(element_id,events,source_refs,reasoning_refs,scale_mode="ordinal",preserve_uncertainty=True,accessibility=None):
    if scale_mode not in {"ordinal","proportional","calendar"}: raise ElementSpecError("unsupported scale mode")
    events=tuple(dict(x) for x in events)
    if len(events)<2: raise ElementSpecError("timeline needs >=2 events")
    ids=[tok(x.get("event_id"),"event_id") for x in events]
    if len(set(ids))!=len(ids): raise ElementSpecError("duplicate event")
    if any(x.get("uncertain") for x in events) and not preserve_uncertainty: raise ElementSpecError("uncertainty cannot be dropped")
    return make(element_id,"timeline",source_refs,reasoning_refs,{"events":events,"scale_mode":scale_mode,"preserve_uncertainty":bool(preserve_uncertainty)},accessibility)
