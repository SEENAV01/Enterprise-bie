def delivery_contract(workflow_id,
                     event_type,queue_name,
                     idempotency_required=True):
    return {"workflow_id":workflow_id,
            "event_type":event_type,
            "queue_name":queue_name,
            "idempotency_required":idempotency_required}
