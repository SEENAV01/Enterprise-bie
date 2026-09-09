def storyboard_qa(segments,shots,overlays,alignment_records):
    errors=[]
    if len(segments)!=len(shots): errors.append("SEGMENT_SHOT_MISMATCH")
    if len(overlays)!=len(segments): errors.append("SEGMENT_TEXT_MISMATCH")
    if any(r["alignment"]<1 for r in alignment_records):
        errors.append("VISUAL_CONCEPT_MISMATCH")
    return {"passed":not errors,"errors":errors}

def pedagogical_gate(narration,alignment,overlay,storyboard):
    checks=[narration["passed"],alignment["passed"],overlay["passed"],storyboard["passed"]]
    return {"valid":all(checks),"checks":checks,"errors":[] if all(checks) else ["QA_FAILURE"]}
