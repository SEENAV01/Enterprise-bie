from saga import create_saga,next_step
from transaction import begin,record_effect,commit,rollback
from effects import effect_key,apply_once,exactly_once_effect_contract
from failure import failure_policy
from compensation import compensate_saga

def build_m271_runtime():
    steps=[
      {"id":"RENDER","compensation":"REMOVE_RENDER"},
      {"id":"UPLOAD","compensation":"DELETE_UPLOAD"},
      {"id":"INDEX","compensation":"REMOVE_INDEX"}
    ]
    saga=create_saga("saga-001",steps,{"course_id":"course-001"})
    tx=begin("tx-001"); store={}
    completed=[]
    for step in steps[:2]:
        key=effect_key(saga["saga_id"],step["id"])
        result=apply_once(store,key,{"step":step["id"],"status":"APPLIED"})
        exactly_once_effect_contract(result)
        record_effect(tx,result)
        saga["completed"].append(step["id"]); completed.append(step["id"])
    failed_code="PARTIAL_COMMIT"
    policy=failure_policy(failed_code,1)
    comp=compensate_saga(saga,failed_code)
    rolled=rollback(tx)
    duplicate=apply_once(store,effect_key("saga-001","UPLOAD"),{"step":"UPLOAD","status":"APPLIED"})
    return {"schema_version":"7.18","saga":saga,"transaction":rolled,
            "completed_before_failure":completed,"failure":{"code":failed_code,"policy":policy},
            "compensation":comp,"duplicate_effect":duplicate,
            "transaction_gate":{"valid":rolled["status"]=="ROLLED_BACK" and
                                saga["status"]=="COMPENSATED" and duplicate["duplicate"],
                                "errors":[]}}
