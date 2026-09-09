def provenance_record(entity_ref,event_refs=None,
                     source_refs=None,derived_from=None):
    return {"entity_ref":entity_ref,
            "event_refs":event_refs or [],
            "source_refs":source_refs or [],
            "derived_from":derived_from or []}

def lineage(events,entity_ref):
    return [e for e in events if e.get("entity_ref")==entity_ref]
