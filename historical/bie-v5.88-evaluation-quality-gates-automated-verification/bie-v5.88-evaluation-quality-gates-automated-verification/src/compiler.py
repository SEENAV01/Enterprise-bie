from evaluate import evaluation,regression
from gates import evaluate_gate
from release import release_eligibility

def compile_quality(artifact_id,criteria,checks,
                    gate,baseline=None,min_confidence=0.0):
    ev=evaluation(artifact_id,criteria)
    gate_result=evaluate_gate(gate,ev,checks)
    reg=regression(ev,baseline) if baseline else {"regressed":False}
    release=release_eligibility([gate_result],
                                not reg["regressed"],
                                ev["confidence"],min_confidence)
    return {"schema_version":"5.88",
            "evaluation":ev,
            "gate":gate_result,
            "regression":reg,
            "release":release,
            "quality_gate":{"valid":True,"errors":[]}}
