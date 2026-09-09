def promotion_record(artifact_id,from_state,to_state,
                     validation_ref=None,build_id=None):
    return {"artifact_id":artifact_id,"from_state":from_state,
            "to_state":to_state,"validation_ref":validation_ref,
            "build_id":build_id}

def promotion_allowed(record):
    return (record.get("from_state")=="VALIDATED" and
            record.get("to_state")=="PROMOTED" and
            bool(record.get("validation_ref")))
