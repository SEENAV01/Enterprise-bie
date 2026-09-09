def should_abstain(confidence,evidence_count,critical_conflict=False,min_conf=.4):
 if not 0<=confidence<=1 or not 0<=min_conf<=1 or evidence_count<0:raise ValueError("invalid inputs")
 reasons=[]
 if evidence_count==0:reasons.append("no_evidence")
 if confidence<min_conf:reasons.append("low_confidence")
 if critical_conflict:reasons.append("critical_conflict")
 return bool(reasons),tuple(reasons)
