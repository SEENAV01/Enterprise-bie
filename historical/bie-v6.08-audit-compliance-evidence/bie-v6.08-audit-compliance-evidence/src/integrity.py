def integrity_metadata(event_id,
                       previous_hash=None,
                       event_hash=None,
                       algorithm="SHA-256"):
    return {"event_id":event_id,
            "previous_hash":previous_hash,
            "event_hash":event_hash,
            "algorithm":algorithm}

def chained(previous_hash,event_hash):
    return {"previous_hash":previous_hash,
            "event_hash":event_hash}
