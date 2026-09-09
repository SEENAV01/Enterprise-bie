def evaluate_outcome(outcome,thresholds=None):
    thresholds=thresholds or {"mastery_gain":0.05}
    gain=float(outcome.get("delta",{}).get("mastery_gain",0.0))
    return {"outcome_id":outcome["outcome_id"],
            "effective":gain>=thresholds["mastery_gain"],
            "mastery_gain":gain,
            "reason":"MASTERY_GAIN_THRESHOLD" if gain>=thresholds["mastery_gain"]
                     else "INSUFFICIENT_OBSERVED_GAIN"}

def aggregate_outcomes(outcomes):
    if not outcomes: return {"count":0,"effectiveness":None}
    effective=sum(bool(x.get("effective")) for x in outcomes)
    return {"count":len(outcomes),"effective_count":effective,
            "effectiveness":effective/len(outcomes)}
