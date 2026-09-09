def prerequisite_check(concept_id, required_concepts, learner_state):
    missing=[c for c in required_concepts
             if learner_state.get(c,{}).get("mastery",0)<0.7]
    return {
      "concept_id":concept_id,
      "ready":not missing,
      "missing_prerequisites":missing
    }
