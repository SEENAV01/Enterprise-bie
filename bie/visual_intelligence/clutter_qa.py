from .visual_qa_contracts import ClutterQAError, make_result

def evaluate_clutter_qa(element_count,text_chars,annotation_count,edge_count,motion_count,focus_competitors,evidence_refs,reasoning_refs,
                        limits=(12,500,5,18,3,2)):
    vals=(element_count,text_chars,annotation_count,edge_count,motion_count,focus_competitors)
    if any(isinstance(v,bool) or not isinstance(v,int) or v<0 for v in vals): raise ClutterQAError("counts must be nonnegative integers")
    if len(limits)!=6 or any(isinstance(v,bool) or not isinstance(v,int) or v<1 for v in limits): raise ClutterQAError("limits invalid")
    ratios=[a/b for a,b in zip(vals,limits)]
    labels=("element_overload","text_overload","annotation_overload","edge_overload","motion_overload","focus_competition")
    blockers=[label for label,r in zip(labels,ratios) if r>1]
    warnings=[label+"_near_limit" for label,r in zip(labels,ratios) if .75<r<=1]
    value=max(0.0,1-sum(max(0,r-.5) for r in ratios)/len(ratios))
    return make_result("vis-clutter","clutter_qa",value,blockers,warnings,evidence_refs,reasoning_refs,{"ratios":[round(r,6) for r in ratios]})
