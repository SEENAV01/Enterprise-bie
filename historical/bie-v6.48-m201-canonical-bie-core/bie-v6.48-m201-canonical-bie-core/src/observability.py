def pipeline_event(event_id, run_id, stage,
                  status, duration_ms=0):
    return {"event_id":event_id,"run_id":run_id,
            "stage":stage,"status":status,
            "duration_ms":duration_ms}

def healthy(event):
    return event["duration_ms"]>=0
