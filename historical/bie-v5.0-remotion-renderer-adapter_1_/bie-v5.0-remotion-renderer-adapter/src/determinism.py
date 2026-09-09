def render_policy():
    return {
      "deterministic":True,
      "stable_ids_required":True,
      "seeded_randomness_required":True,
      "no_runtime_content_generation":True,
      "source_spec_is_immutable":True
    }
