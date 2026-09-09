def failure_detector(node_id,
                   heartbeat_at,
                   timeout):
    if timeout <= 0:
        raise ValueError("INVALID_TIMEOUT")
    return {"node_id":node_id,
            "heartbeat_at":heartbeat_at,
            "timeout":timeout}

def suspected(record,now):
    return now >= record["heartbeat_at"] + record["timeout"]
