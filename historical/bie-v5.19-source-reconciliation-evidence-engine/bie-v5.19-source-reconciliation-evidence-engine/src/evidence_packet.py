def evidence_packet(concept_id,claims,evidence,contradictions=None,
                    unresolved=False):
    return {"concept_id":concept_id,"claims":claims,"evidence":evidence,
            "contradictions":contradictions or [],"unresolved":unresolved,
            "status":"REVIEW_REQUIRED" if unresolved else "READY"}
