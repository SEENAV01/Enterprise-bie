def reliability_policy(service,
                       slo_targets=None,
                       alert_severity="WARNING"):
    return {"service":service,
            "slo_targets":slo_targets or {},
            "alert_severity":alert_severity}

def action_for_budget(consumed_ratio,
                      threshold=1.0):
    return "REVIEW" if consumed_ratio>=threshold else "NORMAL"
