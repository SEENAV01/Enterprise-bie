def credential_boundary(principal_id,
                        allowed_issuers=None,
                        allowed_audiences=None):
    return {"principal_id":principal_id,
            "allowed_issuers":allowed_issuers or [],
            "allowed_audiences":allowed_audiences or []}

def issuer_allowed(boundary, issuer):
    return not boundary["allowed_issuers"] or issuer in boundary["allowed_issuers"]

def audience_allowed(boundary, audience):
    return not boundary["allowed_audiences"] or audience in boundary["allowed_audiences"]
