def required_fields(schema):
    return set(schema.get("required",[]))

def validate_event(event,schema):
    missing=sorted(required_fields(schema)-set(event))
    return {"valid":not missing,"missing":missing}

def validate_payload(payload,schema):
    required=required_fields(schema)
    missing=sorted(required-set(payload))
    return {"valid":not missing,"missing":missing}
