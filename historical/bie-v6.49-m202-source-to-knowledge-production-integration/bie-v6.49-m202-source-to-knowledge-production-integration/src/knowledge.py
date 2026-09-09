def concept(concept_id, label, definition=None, evidence_ids=None, attributes=None):
    return {"concept_id":concept_id,"label":label,"definition":definition,
            "evidence_ids":evidence_ids or [],"attributes":attributes or {}}

def grounded(record):
    return bool(record["evidence_ids"])

def relationship(rel_id, source_concept, target_concept, relation, evidence_ids=None):
    return {"rel_id":rel_id,"source":source_concept,"target":target_concept,
            "relation":relation,"evidence_ids":evidence_ids or []}
