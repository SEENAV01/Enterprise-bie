def concept(concept_id,label,kind="CONCEPT",
           definitions=None,evidence_refs=None,metadata=None):
    return {"concept_id":concept_id,"label":label,"kind":kind,
            "definitions":definitions or [],
            "evidence_refs":evidence_refs or [],
            "metadata":metadata or {}}

def relation(source,target,relation_type,confidence=None,
             evidence_refs=None):
    return {"source":source,"target":target,
            "relation_type":relation_type,
            "confidence":confidence,
            "evidence_refs":evidence_refs or []}
