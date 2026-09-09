def confidence_score(expansion, evidence_count, source_quality_avg=0):
    base=0.25
    base += min(0.25,evidence_count*0.08)
    base += 0.30*max(0,min(1,source_quality_avg))
    base += 0.20*max(0,min(1,expansion.get("confidence",0)))
    return round(min(1.0,base),3)
