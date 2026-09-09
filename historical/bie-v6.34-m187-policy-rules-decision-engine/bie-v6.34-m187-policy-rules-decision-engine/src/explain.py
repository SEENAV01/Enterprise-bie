def decision_trace(policy_id, version,
                   evaluations, decision):
    return {"policy_id":policy_id,"version":version,
            "evaluations":evaluations,"decision":decision}

def explain(trace):
    return {"policy_id":trace["policy_id"],
            "version":trace["version"],
            "matched_rules":[x["rule_id"] for x in trace["evaluations"] if x["matched"]],
            "decision":trace["decision"]}
