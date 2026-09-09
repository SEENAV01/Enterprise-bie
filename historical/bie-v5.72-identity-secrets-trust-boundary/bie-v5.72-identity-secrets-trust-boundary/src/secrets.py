def secret_ref(secret_id,version=None):
    return {"secret_id":secret_id,"version":version}

def secret_access(secret_ref_record,identity_ref_value,
                  allowed_identities):
    return {"allowed":identity_ref_value in set(allowed_identities),
            "secret_ref":secret_ref_record}
