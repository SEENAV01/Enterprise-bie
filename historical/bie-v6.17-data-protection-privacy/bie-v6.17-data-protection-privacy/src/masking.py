def masking_policy(resource,
                  fields,visible_suffix=4):
    return {"resource":resource,
            "fields":fields,
            "visible_suffix":visible_suffix}

def mask(value,suffix=4):
    if not isinstance(value,str):
        return value
    if len(value)<=suffix:
        return "*"*len(value)
    return "*"*(len(value)-suffix)+value[-suffix:]

def apply(record,data):
    out=dict(data)
    for field in record["fields"]:
        if field in out:
            out[field]=mask(out[field],
                            record["visible_suffix"])
    return out
