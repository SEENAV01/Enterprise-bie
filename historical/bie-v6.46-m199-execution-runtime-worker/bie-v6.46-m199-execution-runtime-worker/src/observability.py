def execution_metric(event_id, job_id,
                     operation, status, queue_ms=0,
                     execution_ms=0, attempt_number=1):
    return {"event_id":event_id,"job_id":job_id,
            "operation":operation,"status":status,
            "queue_ms":queue_ms,"execution_ms":execution_ms,
            "attempt_number":attempt_number}

def healthy(record):
    return (record["status"]=="SUCCESS" and
            record["queue_ms"]>=0 and record["execution_ms"]>=0)
