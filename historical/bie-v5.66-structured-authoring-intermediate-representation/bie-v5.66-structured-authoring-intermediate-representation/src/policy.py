def authoring_policy():
    return {
      "canonical_ir_is_renderer_independent":True,
      "components_are_reusable":True,
      "timeline_is_explicit":True,
      "layout_constraints_are_explicit":True,
      "semantic_bindings_are_explicit":True,
      "transform_passes_are_versioned":True,
      "multiple_renderers_can_target_same_ir":True,
      "domain_agnostic":True
    }
