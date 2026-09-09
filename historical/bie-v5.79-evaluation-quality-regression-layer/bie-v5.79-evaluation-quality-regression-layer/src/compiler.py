from evaluate import evaluate_suite
from gates import promotion_gate

def compile_evaluation(results,threshold,
                       regression_result=None):
    ev=evaluate_suite(results,threshold)
    gate=promotion_gate(ev,regression_result)
    return {"schema_version":"5.79",
            "evaluation":ev,"promotion_gate":gate,
            "quality_gate":{"valid":gate["allowed"],
                            "errors":[] if gate["allowed"] else [gate["reason"]]}}
