def remediation_signal(signal_id, report_id, severity,
                      target_refs, reason, recommended_action):
    if severity not in {"LOW","MEDIUM","HIGH","CRITICAL"}:
        raise ValueError("INVALID_SIGNAL_SEVERITY")
    return {"signal_id":signal_id,"report_id":report_id,
            "severity":severity,"target_refs":target_refs,
            "reason":reason,"recommended_action":recommended_action}

def valid(s):
    return bool(s["signal_id"] and s["report_id"] and s["target_refs"])
