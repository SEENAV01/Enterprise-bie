def isolation_policy(no_host_access=True,no_privilege_escalation=True,
                     readonly_inputs=True,restricted_outputs=True):
    return {"no_host_access":no_host_access,
            "no_privilege_escalation":no_privilege_escalation,
            "readonly_inputs":readonly_inputs,
            "restricted_outputs":restricted_outputs}

def validate_isolation(policy):
    required=["no_host_access","no_privilege_escalation",
              "readonly_inputs","restricted_outputs"]
    return {"valid":all(policy.get(k) is True for k in required),
            "missing_or_disabled":[k for k in required
                                   if policy.get(k) is not True]}
