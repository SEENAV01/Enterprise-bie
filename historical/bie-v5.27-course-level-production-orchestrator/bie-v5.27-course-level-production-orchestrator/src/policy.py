def course_production_policy():
    return {
      "course_is_a_dependency_graph":True,
      "lessons_are_independently_addressable":True,
      "incremental_regeneration_is_supported":True,
      "unchanged_artifacts_can_be_cached":True,
      "parallel_rendering_is_supported":True,
      "global_visual_continuity_is_explicit":True,
      "lesson_manifests_are_persistent":True,
      "failures_are_recoverable":True,
      "course_generation_is_not_monolithic":True
    }
