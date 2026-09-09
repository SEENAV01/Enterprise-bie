def provenance_policy():
    return {
      "artifact_hashes_are_supported":True,
      "immutable_manifests_are_supported":True,
      "input_hashes_are_supported":True,
      "model_prompt_config_versions_are_recorded":True,
      "code_version_is_recorded":True,
      "dependency_snapshots_are_supported":True,
      "environment_metadata_is_recorded":True,
      "lineage_graphs_are_supported":True,
      "replay_plans_are_supported":True,
      "artifact_verification_is_supported":True
    }
