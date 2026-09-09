def invalidation_event(record_id,reason,affected_artifacts=None):
    return {"record_id":record_id,"reason":reason,
            "affected_artifacts":affected_artifacts or []}

def affected_records(events):
    return [e["record_id"] for e in events]
