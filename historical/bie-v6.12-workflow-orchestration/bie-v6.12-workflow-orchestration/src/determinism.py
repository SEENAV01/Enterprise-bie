def deterministic_input(workflow_id,
                      sequence,event_type,
                      payload_ref):
    return {"workflow_id":workflow_id,
            "sequence":sequence,
            "event_type":event_type,
            "payload_ref":payload_ref}

def replay_order(records):
    return sorted(records,
                  key=lambda x:x["sequence"])
