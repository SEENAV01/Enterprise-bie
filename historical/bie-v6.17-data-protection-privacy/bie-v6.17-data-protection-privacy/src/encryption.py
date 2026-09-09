def encryption_policy(data_id,
                    algorithm,
                    key_ref,
                    scope="AT_REST"):
    return {"data_id":data_id,
            "algorithm":algorithm,
            "key_ref":key_ref,
            "scope":scope,
            "status":"REQUIRED"}

def protected(record):
    return bool(record["algorithm"] and
                record["key_ref"])
