def experience_provenance(interaction_id,objective_refs=None,
                            concept_refs=None,source_refs=None):
    return {"interaction_id":interaction_id,
            "objective_refs":objective_refs or [],
            "concept_refs":concept_refs or [],
            "source_refs":source_refs or []}
