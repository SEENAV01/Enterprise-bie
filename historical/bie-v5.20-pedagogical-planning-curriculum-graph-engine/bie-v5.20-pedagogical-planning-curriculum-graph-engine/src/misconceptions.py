def misconception(misconception_id,concept_id,belief,
                   correction=None,evidence_refs=None):
    return {"misconception_id":misconception_id,"concept_id":concept_id,
            "belief":belief,"correction":correction,
            "evidence_refs":evidence_refs or []}
