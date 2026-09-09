def build_manifest(build_ref,artifact_refs,source_pins,
                  model_pins,tool_pins,policy_pins,
                  experiment_pins=None,environment=None,
                  provenance_nodes=None,provenance_edges=None):
    return {
      "build_ref":build_ref,
      "artifact_refs":artifact_refs,
      "source_pins":source_pins,
      "model_pins":model_pins,
      "tool_pins":tool_pins,
      "policy_pins":policy_pins,
      "experiment_pins":experiment_pins or [],
      "environment":environment or {},
      "provenance_nodes":provenance_nodes or [],
      "provenance_edges":provenance_edges or []
    }
