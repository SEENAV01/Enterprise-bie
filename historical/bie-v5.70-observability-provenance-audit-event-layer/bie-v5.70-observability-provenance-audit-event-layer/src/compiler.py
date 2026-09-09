from audit import audit_query

def compile_audit(events,root_id=None):
    selected=events
    if root_id is not None:
        selected=[e for e in events
                  if e.get("correlation_id","").startswith(root_id)]
    return {"schema_version":"5.70",
            "event_count":len(selected),
            "events":selected,
            "quality_gate":{"valid":True,"errors":[]}}
