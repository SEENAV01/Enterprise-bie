def secret_reference(secret_id,version=None,
                     scope=None,expires_at=None):
    return {"secret_id":secret_id,"version":version,
            "scope":scope,"expires_at":expires_at,
            "kind":"SECRET"}

def secret_access(reference,subject,action="READ"):
    return {"secret_id":reference["secret_id"],
            "version":reference.get("version"),
            "subject":subject,"action":action}
