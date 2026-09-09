def error_budget(slo_target):
    allowed=1-slo_target
    return {"slo_target":slo_target,
            "allowed_error_ratio":allowed}

def consumed(total_events,bad_events,
             budget):
    allowed=budget["allowed_error_ratio"]*total_events
    return 0 if allowed<=0 else bad_events/allowed
