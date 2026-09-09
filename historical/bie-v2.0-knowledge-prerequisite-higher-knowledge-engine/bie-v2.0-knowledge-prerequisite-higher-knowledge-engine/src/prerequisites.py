def build_prerequisite_candidates(units):
    # Candidate generation only. The relation becomes trusted after evidence/review.
    out=[]
    for i in range(1,len(units)):
        prev=units[i-1]
        cur=units[i]
        out.append({
            "source":prev["unit_id"],
            "target":cur["unit_id"],
            "relation":"prerequisite_of",
            "status":"CANDIDATE",
            "confidence":0.5
        })
    return out

def gate_dependency(edge, threshold=.80):
    if edge["status"]=="SOURCE_DERIVED" and edge["confidence"]>=threshold:
        return "TRUSTED"
    if edge["confidence"]>=threshold:
        return "REVIEW"
    return "WEAK"
