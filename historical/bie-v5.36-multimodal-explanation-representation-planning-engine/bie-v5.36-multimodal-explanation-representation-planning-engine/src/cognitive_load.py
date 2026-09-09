def cognitive_load_budget(segment_id,intrinsic=0.0,
                         extraneous=0.0,germane=0.0,max_total=1.0):
    total=intrinsic+extraneous+germane
    return {"segment_id":segment_id,"intrinsic":intrinsic,
            "extraneous":extraneous,"germane":germane,
            "total":total,"within_budget":total<=max_total}

def multimodal_overlap_guard(representations):
    types=[r.get("rep_type") for r in representations]
    redundant={"TEXT","NARRATION"}.issubset(types)
    return {"redundant_overlap":redundant,
            "review_required":redundant and len(types)>3}
