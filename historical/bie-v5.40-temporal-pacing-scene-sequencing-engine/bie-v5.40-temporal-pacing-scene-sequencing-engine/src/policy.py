def temporal_policy():
    return {
      "sequence_is_dependency_driven":True,
      "timing_constraints_are_explicit":True,
      "arbitrary_fixed_durations_are_not_required":True,
      "duration_can_be_derived_later":True,
      "sync_events_are_explicit":True,
      "pacing_is_first_class":True,
      "interaction_events_can_affect_timeline":True,
      "temporal_plan_is_separate_from_render_code":True,
      "domain_agnostic":True
    }
