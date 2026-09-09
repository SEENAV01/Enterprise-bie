def codegen_policy():
    return {
      "scene_graph_is_deterministic":True,
      "all_scene_assets_are_explicitly_bound":True,
      "animations_reference_timeline":True,
      "composition_duration_comes_from_temporal_plan":True,
      "remotion_is_a_downstream_render_target":True,
      "generated_code_is_validated_before_render":True,
      "components_are_reusable":True,
      "source_and_asset_provenance_is_preserved":True,
      "domain_logic_is_not_hidden_inside_render_code":True
    }
