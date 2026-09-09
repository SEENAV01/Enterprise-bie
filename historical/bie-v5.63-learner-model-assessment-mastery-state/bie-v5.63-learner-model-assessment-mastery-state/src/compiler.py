from mastery import classify_mastery
from remediation import recommend_remediation

def compile_mastery(state,rule=None):
    rule=rule or {"threshold":0.8,"uncertainty":0.25,
                  "strategies":["EXPLAIN","PRACTICE"]}
    status=classify_mastery(state.get("estimate",0),
                            state.get("uncertainty",1),
                            rule["threshold"],0.5)
    rec=recommend_remediation(state,rule)
    return {"schema_version":"5.63","mastery_state":state,
            "status":status,"recommended_remediation":rec,
            "quality_gate":{"valid":True,"errors":[]}}
