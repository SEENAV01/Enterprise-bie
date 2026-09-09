def representation_spec(spec_id,concept_refs,modality,
                        objective_refs=None,learner_constraints=None,
                        fidelity="STANDARD",parameters=None):
    return {"spec_id":spec_id,"concept_refs":concept_refs,
            "modality":modality,"objective_refs":objective_refs or [],
            "learner_constraints":learner_constraints or {},
            "fidelity":fidelity,"parameters":parameters or {}}
