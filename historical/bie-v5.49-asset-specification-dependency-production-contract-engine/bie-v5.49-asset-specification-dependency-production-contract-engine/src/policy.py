def production_contract_policy():
    return {
      "asset_ids_are_stable":True,
      "dependencies_are_explicit":True,
      "production_contract_is_renderer_independent":True,
      "inputs_and_outputs_are_explicit":True,
      "timing_requirements_are_explicit":True,
      "interaction_contract_is_explicit":True,
      "accessibility_requirements_are_explicit":True,
      "validation_is_part_of_the_contract":True,
      "production_is_graph_based":True,
      "domain_agnostic":True
    }
