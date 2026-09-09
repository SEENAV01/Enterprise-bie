def visual_semantic(visual_id, concept_id, mathematical_state,
                    narration_cues=None):
    return {
      "visual_id":visual_id,
      "concept_id":concept_id,
      "mathematical_state":mathematical_state,
      "narration_cues":narration_cues or []
    }

def state_transition(transition_id, source_state, target_state,
                     meaning, duration_policy="CONTENT_DRIVEN"):
    return {
      "transition_id":transition_id,
      "source_state":source_state,
      "target_state":target_state,
      "meaning":meaning,
      "duration_policy":duration_policy
    }
