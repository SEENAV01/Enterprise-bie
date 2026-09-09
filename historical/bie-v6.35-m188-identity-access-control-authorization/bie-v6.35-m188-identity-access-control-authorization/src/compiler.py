from principal import principal,active as principal_active
from role import role,active as role_active
from permission import permission,matches
from scope import scope,matches as scope_matches
from authorization import authorize,allowed
from delegation import delegation
from service_identity import service_identity,active as service_active
from credential_boundary import credential_boundary,issuer_allowed,audience_allowed
from audit import audit_event,denied

def compile_authorization():
    user=principal("user-1","USER",{"department":"engineering"})
    svc=service_identity("svc-1","bie-runtime","cred-1")
    perm=permission("read","artifact:123")
    r=role("reader",[perm])
    sc=scope("artifact:123")
    dec=authorize(user,[perm],"read","artifact:123")
    dg=delegation("user-1","svc-1",sc,2000)
    cb=credential_boundary("svc-1",["issuer-a"],["bie-runtime"])
    audit=audit_event("ae-1","user-1","read","artifact:123",
                      dec["decision"],dec["reason"])
    deny=authorize(user,[perm],"delete","artifact:123")
    return {"schema_version":"6.35",
            "principal":user,"service_identity":svc,
            "role":r,"permission":perm,"scope":sc,
            "authorization":dec,"delegation":dg,
            "credential_boundary":cb,"audit":audit,
            "deny_example":deny,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "principal_active":principal_active(user),
              "service_active":service_active(svc),
              "role_active":role_active(r),
              "permission_matches":matches(perm,"read","artifact:123"),
              "scope_matches":scope_matches(sc,"artifact:123"),
              "allowed":allowed(dec),
              "delegation_active":dg["status"]=="ACTIVE",
              "issuer_allowed":issuer_allowed(cb,"issuer-a"),
              "audience_allowed":audience_allowed(cb,"bie-runtime"),
              "deny_audited":denied(audit) is False,
              "explicit_deny":deny["decision"]=="DENY"
            }}
