from recommendations import bounded_recommendation
from guardrails import optimization_guard,approval_gate

def compile_optimization(evaluation_suites,benchmarks,
                         recommendations=None,policy_changes=None,
                         approved_changes=None):
    recommendations=recommendations or []
    policy_changes=policy_changes or []
    approved_changes=approved_changes or []
    recs=[bounded_recommendation(r) for r in recommendations]
    changes=[]
    for c in policy_changes:
        guard=optimization_guard(c)
        approval=approval_gate(
            c,approved=c.get("change_id") in approved_changes)
        changes.append({"change":c,"guard":guard,"approval":approval})
    return {"schema_version":"5.55",
            "evaluation_suites":evaluation_suites,
            "benchmarks":benchmarks,
            "recommendations":recs,
            "policy_changes":changes,
            "quality_gate":{"valid":all(
              x["guard"]["allowed"] and
              x["approval"]["status"]=="APPROVED"
              for x in changes)}}
