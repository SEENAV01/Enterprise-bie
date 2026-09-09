from decision import route
from audit import routing_decision

def compile_route(task_id,models,requirements,
                  policy_version="1",weights=None,budget=None):
    r=route(models,requirements,weights,budget)
    if r["status"]!="ROUTED":
        return {"schema_version":"5.78",
                "status":r["status"],
                "quality_gate":{"valid":False,
                                "errors":["NO_COMPATIBLE_MODEL"]}}
    rec=routing_decision(task_id,requirements,r["primary"],
                         r["fallback_chain"],policy_version,
                         "CAPABILITY_QUALITY_COST_LATENCY")
    rec["quality_gate"]={"valid":True,"errors":[]}
    return rec
