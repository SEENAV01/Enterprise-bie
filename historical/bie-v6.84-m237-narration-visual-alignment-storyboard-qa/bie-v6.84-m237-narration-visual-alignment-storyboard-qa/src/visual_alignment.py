def alignment(segment,shot):
    concepts=set(segment.get("concept_ids",[]))
    visuals=set(shot.get("concept_ids",[]))
    matched=concepts & visuals
    score=len(matched)/len(concepts) if concepts else 1.0
    return {"segment_id":segment.get("segment_id"),
            "shot_id":shot.get("shot_id"),"matched_concepts":sorted(matched),
            "alignment":score}

def validate_alignment(records,threshold=1.0):
    missing=[r for r in records if r["alignment"]<threshold]
    return {"passed":not missing,"missing":missing,"threshold":threshold}
