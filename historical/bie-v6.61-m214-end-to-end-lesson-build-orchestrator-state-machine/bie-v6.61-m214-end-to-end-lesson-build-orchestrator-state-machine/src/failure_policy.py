def failure_policy(max_remediation_cycles=3,
                  fail_on_critical=True):
    return {"max_remediation_cycles":max_remediation_cycles,
            "fail_on_critical":fail_on_critical}

def should_fail(severity, cycle, policy):
    return ((policy["fail_on_critical"] and severity=="CRITICAL")
            or cycle >= policy["max_remediation_cycles"])
