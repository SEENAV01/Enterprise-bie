from identity import identity
from auth import authentication_context
from permission import permission
from rbac import role
from policy import security_policy
from authorize import authorization_request,decide
from tenant import tenant_boundary
from audit import authorization_audit

def compile_security(subject_id,tenant_id,
                     action,resource):
    ident=identity(subject_id,tenant_id,
                   roles=["operator"])
    auth=authentication_context(ident,0)
    p=permission(action,resource)
    r=role("operator",[p])
    pol=security_policy("default",1)
    req=authorization_request(subject_id,
                              tenant_id,action,resource,
                              {"authenticated":auth["authenticated"]})
    decision=decide(req,[r],True)
    boundary=tenant_boundary(tenant_id,tenant_id)
    audit=authorization_audit(
        "decision-1",subject_id,tenant_id,
        action,resource,decision["decision"],
        pol["version"],0,decision["reason"])
    return {"schema_version":"6.05",
            "identity":ident,
            "authentication":auth,
            "permission":p,
            "role":r,
            "policy":pol,
            "request":req,
            "decision":decision,
            "tenant_boundary":boundary,
            "audit":audit,
            "quality_gate":{"valid":True,"errors":[]}}
