from secret import secret_reference
from scope import credential_scope
from grant import access_grant
from injection import injection_request,injection_boundary

def compile_credential_access(secret_id,service,
                              actions,subject,
                              issued_at,expires_at,
                              grant_id="grant-1"):
    s=secret_reference(secret_id,service=service)
    scope=credential_scope("scope-1",service,actions)
    grant=access_grant(grant_id,s,scope,issued_at,
                       expires_at,subject)
    injection=injection_request("task-1",grant_id,
                                "WORKER")
    return {"schema_version":"5.96",
            "secret":s,"scope":scope,"grant":grant,
            "injection":injection_boundary(injection),
            "quality_gate":{"valid":True,"errors":[]}}
