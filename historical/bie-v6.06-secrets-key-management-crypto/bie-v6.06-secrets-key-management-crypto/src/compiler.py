from secret import secret_reference
from key import key_reference
from lifecycle import lifecycle
from rotation import rotation_plan
from access import access_policy

def compile_crypto(secret_id,key_id,version,
                   service,created_at=0):
    secret=secret_reference(secret_id,version,
                            scope=service)
    key=key_reference(key_id,version,
                      "ENCRYPTION","AES")
    state=lifecycle(secret_id,"ACTIVE",version,
                    created_at)
    rotation=rotation_plan(secret_id,version,
                           version+1,created_at)
    policy=access_policy(secret_id,[service],["READ"],
                         "ALLOW")
    return {"schema_version":"6.06",
            "secret":secret,"key":key,
            "lifecycle":state,
            "rotation":rotation,
            "access_policy":policy,
            "quality_gate":{"valid":True,"errors":[]}}
