def field_protection(resource,
                    fields,
                    mode="ENCRYPT"):
    if mode not in {"ENCRYPT","TOKENIZE","HASH"}:
        raise ValueError("INVALID_FIELD_PROTECTION_MODE")
    return {"resource":resource,
            "fields":fields,
            "mode":mode}

def protects(record,field):
    return field in record["fields"]
