def envelope(key_id, data_key_ref,
             wrapping_key_ref, algorithm):
    return {"key_id":key_id,
            "data_key_ref":data_key_ref,
            "wrapping_key_ref":wrapping_key_ref,
            "algorithm":algorithm}

def valid(record):
    return bool(record["data_key_ref"] and record["wrapping_key_ref"])
