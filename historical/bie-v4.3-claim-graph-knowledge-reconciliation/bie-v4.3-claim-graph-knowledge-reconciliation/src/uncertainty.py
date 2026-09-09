def uncertainty_state(support_count, contradiction_count, source_count):
    if contradiction_count>0:return "CONFLICTED"
    if support_count>=2 and source_count>=2:return "HIGH_CONFIDENCE"
    if support_count>=1:return "SUPPORTED"
    return "UNSUPPORTED"

def annotate_claim(claim, support_count, contradiction_count, source_count):
    claim["uncertainty"]=uncertainty_state(
      support_count,contradiction_count,source_count)
    return claim
