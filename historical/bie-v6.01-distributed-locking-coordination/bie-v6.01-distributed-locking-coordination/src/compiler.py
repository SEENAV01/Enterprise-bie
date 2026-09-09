from lock import lock_record
from lease import lease
from fencing import next_fencing_token
from ownership import ownership
from singleton import singleton_execution

def compile_coordination(resource,owner,
                         previous_token=0,
                         now=0,ttl=30,
                         lock_id="lock-1",
                         lease_id="lease-1"):
    token=next_fencing_token(previous_token)
    lock=lock_record(lock_id,resource,owner,
                     token,now+ttl)
    l=lease(lease_id,owner,now,now+ttl)
    own=ownership(resource,owner,token,lease_id)
    return {"schema_version":"6.01",
            "lock":lock,"lease":l,
            "ownership":own,
            "singleton":singleton_execution(
                resource,owner,token,lease_id),
            "quality_gate":{"valid":True,"errors":[]}}
