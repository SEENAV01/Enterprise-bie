def dead_letter(topic_id, reason=None,
                original_event_id=None):
    return {"topic_id":topic_id,"reason":reason,
            "original_event_id":original_event_id}

def traceable(record):
    return record["original_event_id"] is not None
