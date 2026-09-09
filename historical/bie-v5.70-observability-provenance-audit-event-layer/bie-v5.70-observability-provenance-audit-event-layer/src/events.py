def audit_event(event_id,event_type,timestamp,actor,
               entity_ref,correlation_id=None,previous_state=None,
               new_state=None,evidence_refs=None,build_id=None,
               policy_version=None,metadata=None):
    return {"event_id":event_id,"event_type":event_type,
            "timestamp":timestamp,"actor":actor,
            "entity_ref":entity_ref,"correlation_id":correlation_id,
            "previous_state":previous_state,
            "new_state":new_state,
            "evidence_refs":evidence_refs or [],
            "build_id":build_id,
            "policy_version":policy_version,
            "metadata":metadata or {}}
