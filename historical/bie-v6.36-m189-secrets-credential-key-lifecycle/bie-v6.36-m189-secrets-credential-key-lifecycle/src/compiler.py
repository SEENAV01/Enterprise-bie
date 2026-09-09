from secret_ref import secret_ref,active as secret_active
from key import key_record,usable
from version import key_version,next_version
from rotation import rotation_plan,activate
from revocation import revocation,revoked
from lease import credential_lease,active as lease_active
from envelope import envelope,valid
from retrieval import retrieval_request,fulfill
from audit import lifecycle_event,successful
from observability import key_event,metric

def compile_key_lifecycle():
    sr=secret_ref("secret-1",3,"service:runtime")
    kr=key_record("key-1","AES-256-GCM",3,"ENCRYPTION")
    kv=key_version("key-1",3,1000,2000)
    rp=rotation_plan("key-1",3,4,1500)
    rp=activate(rp)
    rv=revocation("key-1",2,"ROTATED",1400)
    lease=credential_lease("cred-1","svc-1",1000,2000)
    env=envelope("key-1","data-key-1","wrap-key-1","AES-KW")
    rr=fulfill(retrieval_request(sr,"svc-1","runtime"),3)
    aud=lifecycle_event("le-1","svc-1","key-1","ROTATE","SUCCESS")
    obs=key_event("ke-1","key-1",3,"RETRIEVE","SUCCESS")
    return {"schema_version":"6.36",
            "secret_ref":sr,"key":kr,"key_version":kv,
            "rotation":rp,"revocation":rv,"lease":lease,
            "envelope":env,"retrieval":rr,
            "audit":aud,"observability":obs,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "secret_active":secret_active(sr),
              "key_usable":usable(kr),
              "version_next":next_version(3)==4,
              "rotation_active":rp["status"]=="ACTIVE",
              "revoked":revoked(rv),
              "lease_active":lease_active(lease),
              "envelope_valid":valid(env),
              "retrieval_fulfilled":rr["status"]=="FULFILLED",
              "audit_success":successful(aud),
              "metric":metric(obs)
            }}
