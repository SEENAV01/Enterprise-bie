def state_event(event_id, job_id, from_state, to_state,
               reason, artifact_refs=None, evidence_refs=None):
    return {"event_id":event_id,"job_id":job_id,
            "from_state":from_state,"to_state":to_state,
            "reason":reason,"artifact_refs":artifact_refs or [],
            "evidence_refs":evidence_refs or []}

def valid(e):
    return bool(e["event_id"] and e["job_id"] and e["from_state"]
                and e["to_state"] and e["reason"])
