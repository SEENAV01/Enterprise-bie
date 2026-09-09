def scene_planning_policy():
    return {
      "shots_are_semantic_units":True,
      "narration_is_primary_timing_reference":True,
      "composition_supports_focus_hierarchy":True,
      "camera_motion_requires_semantic_reason":True,
      "transitions_require_semantic_reason":True,
      "no_arbitrary_fixed_shot_duration":True,
      "visual_density_is_pedagogically_controlled":True,
      "shot_plan_is_renderer_independent":True
    }
