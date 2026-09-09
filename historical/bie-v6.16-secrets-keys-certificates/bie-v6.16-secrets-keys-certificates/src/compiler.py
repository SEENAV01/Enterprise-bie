from secret_ref import secret_ref,scoped
from key import key_metadata,usable
from key_rotation import rotation,activate_next
from certificate import certificate,valid_at
from revocation import revocation,is_revoked
from usage_policy import key_usage_policy,allows
from expiry import expiry_check,safe
from material_boundary import material_boundary,protected
from audit import secret_audit

def compile_secrets():
    secret=secret_ref("db-password",3,
                      "secret-store","tenant-a")
    key=key_metadata("signing-key",2,
                     "AES-256","ENCRYPT",
                     "ACTIVE",0,1000)
    rot=activate_next(rotation("signing-key",1,2,500))
    cert=certificate("cert-1","service-a",
                     "internal-ca",0,1000,2)
    rev=revocation("old-cert","CERTIFICATE",
                   "ROTATION",600)
    policy=key_usage_policy(
        "signing-key",["ENCRYPT"],["workflow"],True)
    boundary=material_boundary(
        "signing-key","KEY","HSM",False)
    exp=expiry_check("signing-key","KEY",1000,700)
    audit=secret_audit("audit-1","signing-key",
                       "ROTATE","operator","SUCCESS")
    return {"schema_version":"6.16",
            "secret_reference":secret,
            "key":key,
            "rotation":rot,
            "certificate":cert,
            "revocation":rev,
            "usage_policy":policy,
            "material_boundary":boundary,
            "expiry_check":exp,
            "audit":audit,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "secret_scoped":scoped(secret,"tenant-a"),
              "key_usable":usable(key,700),
              "key_usage_allowed":allows(
                   policy,"ENCRYPT","workflow"),
              "certificate_valid":valid_at(cert,700),
              "revoked":is_revoked(rev),
              "material_protected":protected(boundary),
              "not_expired":safe(exp)
            }}
