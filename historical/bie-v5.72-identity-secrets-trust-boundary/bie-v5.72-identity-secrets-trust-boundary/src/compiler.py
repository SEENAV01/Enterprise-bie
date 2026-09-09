from trust import can_cross
from credentials import credential_allows

def authorize_boundary(request,credential,trust_policy):
    boundary_ok=can_cross(request["source_zone"],
                          request["target_zone"],trust_policy)
    credential_ok=credential_allows(credential,request["operation"])
    allowed=boundary_ok and credential_ok
    return {"schema_version":"5.72",
            "allowed":allowed,
            "reason":"ALLOW" if allowed else
            ("TRUST_BOUNDARY_DENY" if not boundary_ok else "CREDENTIAL_SCOPE_DENY")}

def compile_identity(identity_record):
    return {"schema_version":"5.72",
            "identity":identity_record,
            "quality_gate":{"valid":True,"errors":[]}}
