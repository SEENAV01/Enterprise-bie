def audit_query(events,entity_ref=None,event_type=None,
               actor=None):
    result=events
    if entity_ref is not None:
        result=[e for e in result if e.get("entity_ref")==entity_ref]
    if event_type is not None:
        result=[e for e in result if e.get("event_type")==event_type]
    if actor is not None:
        result=[e for e in result if e.get("actor")==actor]
    return result
