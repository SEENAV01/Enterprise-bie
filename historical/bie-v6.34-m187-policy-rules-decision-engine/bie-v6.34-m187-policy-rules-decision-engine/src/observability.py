def policy_event(event_id,policy_id,version,
                 operation,status,matched_count=0):
    return {"event_id":event_id,"policy_id":policy_id,
            "version":version,"operation":operation,
            "status":status,"matched_count":matched_count}

def metric(record):
    return {"policy_id":record["policy_id"],
            "version":record["version"],
            "operation":record["operation"],
            "status":record["status"],
            "matched_count":record["matched_count"]}
