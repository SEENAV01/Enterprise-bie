def adaptation_signal(outcome,context=None):
    gain=outcome.get("delta",{}).get("mastery_gain",0.0)
    uncertainty=outcome.get("post_state",{}).get("uncertainty",1.0)
    if gain>=0.05 and uncertainty<=0.25:
        return {"signal":"POSITIVE","recommended_change":"CONTINUE_OR_ADVANCE"}
    if gain<0.0:
        return {"signal":"NEGATIVE","recommended_change":"RECONSIDER_ACTION"}
    return {"signal":"AMBIGUOUS","recommended_change":"COLLECT_MORE_EVIDENCE"}
