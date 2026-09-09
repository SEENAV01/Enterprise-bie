def contract_test(event,schema,consumer_versions):
    from validate import validate_event
    valid=validate_event(event,schema)["valid"]
    accepted=event.get("_schema_version") in consumer_versions
    return {"valid":valid and accepted,
            "schema_valid":valid,
            "version_accepted":accepted}
