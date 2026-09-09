def identity(identity_id,kind,roles=None,attributes=None,
             issuer=None):
    return {"identity_id":identity_id,"kind":kind,
            "roles":roles or [],"attributes":attributes or {},
            "issuer":issuer}

def identity_ref(i):
    return f"{i['kind']}:{i['identity_id']}"
