def generation_spec(spec_id,objective_ref,item_type,
                    difficulty=None,concept_refs=None,
                    misconception_refs=None,constraints=None):
    return {"spec_id":spec_id,"objective_ref":objective_ref,
            "item_type":item_type,"difficulty":difficulty,
            "concept_refs":concept_refs or [],
            "misconception_refs":misconception_refs or [],
            "constraints":constraints or {}}

def generation_requirements(spec):
    return {
      "objective_required":bool(spec.get("objective_ref")),
      "type_required":bool(spec.get("item_type")),
      "misconception_aware":bool(spec.get("misconception_refs")),
      "difficulty_controlled":spec.get("difficulty") is not None
    }
