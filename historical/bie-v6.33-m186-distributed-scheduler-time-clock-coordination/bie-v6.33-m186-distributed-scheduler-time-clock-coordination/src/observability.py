def scheduler_event(event_id,schedule_id,
                     operation,status,
                     clock_skew_ms=0,
                     misfire=False):
    return {"event_id":event_id,
            "schedule_id":schedule_id,
            "operation":operation,
            "status":status,
            "clock_skew_ms":clock_skew_ms,
            "misfire":misfire}

def metric(record):
    return {"schedule_id":record["schedule_id"],
            "operation":record["operation"],
            "status":record["status"],
            "clock_skew_ms":record["clock_skew_ms"],
            "misfire":record["misfire"]}
