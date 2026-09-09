def participant(participant_id, endpoint=None, metadata=None):
    if not participant_id:
        raise ValueError("INVALID_PARTICIPANT")
    return {"participant_id":participant_id,"endpoint":endpoint,
            "metadata":metadata or {},"status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
