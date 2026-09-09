def capabilities():
    return {"domain_events":True,"pub_sub":True,"durable_delivery_contract":True,
            "deduplication":True,"aggregate_ordering":True,"dead_letter_queue":True,
            "workflow_triggers":True}
