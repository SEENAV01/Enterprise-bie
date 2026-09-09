def secret_ref(secret_id,version=None,
              provider=None,scope=None):
    return {"secret_id":secret_id,
            "version":version,
            "provider":provider,
            "scope":scope,
            "material":"REFERENCE_ONLY"}

def scoped(record,scope):
    return record["scope"] is None or record["scope"]==scope
