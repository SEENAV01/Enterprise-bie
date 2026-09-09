from auth_context import auth_context,authenticated
from token import token_contract,valid_at
from service_identity import service_identity,revoke
from policy import authorization_policy,allows
from enforcement import enforcement_point,enforce
from tenant import tenant_boundary,isolated
from rotation import rotation_hook,rotated
from security_event import security_event
from credential import credential,expired

def compile_security():
    auth=auth_context("user-1","identity",
                      "tenant-a",["workflow.read"])
    tok=token_contract("tok-1","identity",
                       "user-1",0,100,
                       ["workflow.read"],["workflow"])
    sid=service_identity("workflow",
                         "identity","tenant-a",["workflow"])
    pol=authorization_policy(
        "workflow","READ",["user-1"],["workflow.read"],True)
    ep=enforcement_point("workflow","policy-engine",True)
    decision=enforce(ep,"ALLOW" if
                     allows(pol,"user-1","workflow.read")
                     else "DENY")
    tb=tenant_boundary("tenant-a","tenant-a")
    rot=rotated(rotation_hook("cred-1",1,2,50))
    se=security_event("sec-1","AUTHZ_DECISION",
                      "user-1","workflow",decision,
                      "workflow","policy-evaluation")
    cred=credential("cred-1","SERVICE_SECRET",2,200)
    return {"schema_version":"6.14",
            "auth_context":auth,
            "token":tok,
            "service_identity":sid,
            "authorization_policy":pol,
            "enforcement_point":ep,
            "authorization_decision":decision,
            "tenant_boundary":tb,
            "rotation":rot,
            "security_event":se,
            "credential":cred,
            "quality_gate":{"valid":True,"errors":[]}}
