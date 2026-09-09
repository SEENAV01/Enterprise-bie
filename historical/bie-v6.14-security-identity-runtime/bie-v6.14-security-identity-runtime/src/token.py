def token_contract(token_id,issuer,
                   subject_id,issued_at,
                   expires_at,scopes=None,
                   audience=None):
    return {"token_id":token_id,
            "issuer":issuer,
            "subject_id":subject_id,
            "issued_at":issued_at,
            "expires_at":expires_at,
            "scopes":scopes or [],
            "audience":audience}

def valid_at(record,now):
    return record["issued_at"] <= now < record["expires_at"]
