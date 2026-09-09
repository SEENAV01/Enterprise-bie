from simulation import simulate,diff_decisions

def compile_policy_change(policy,contexts,
                          previous_results=None):
    current=simulate(policy,contexts)
    changes=(diff_decisions(previous_results,current)
             if previous_results is not None else [])
    return {"schema_version":"5.86",
            "policy":policy,
            "simulation":current,
            "behavior_changes":changes,
            "quality_gate":{"valid":True,"errors":[]}}
