def provenance_chain(claim_id,source_refs=None,
                     derived_artifacts=None):
    return {"claim_id":claim_id,"source_refs":source_refs or [],
            "derived_artifacts":derived_artifacts or []}
