def regeneration_guard(failure_ids, remediation_ids,
                     preserve_refs=None, max_attempts=3):
    return {"failure_ids":failure_ids,"remediation_ids":remediation_ids,
            "preserve_refs":preserve_refs or [],
            "max_attempts":max_attempts}

def safe(g):
    return bool(g["failure_ids"] and g["remediation_ids"]
                and g["max_attempts"] > 0)
