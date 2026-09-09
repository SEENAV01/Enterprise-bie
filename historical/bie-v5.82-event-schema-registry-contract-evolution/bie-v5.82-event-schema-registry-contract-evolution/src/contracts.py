def producer_contract(event_type,version,schema):
    return {"type":"PRODUCER","event_type":event_type,
            "version":version,"schema":schema}

def consumer_contract(event_type,version,accepted_versions):
    return {"type":"CONSUMER","event_type":event_type,
            "version":version,
            "accepted_versions":accepted_versions}

def contract_match(producer,consumer):
    return producer["event_type"]==consumer["event_type"] and            producer["version"] in consumer["accepted_versions"]
