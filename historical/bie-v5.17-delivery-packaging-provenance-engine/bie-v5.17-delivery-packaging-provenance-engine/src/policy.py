def delivery_policy():
    return {
      "final_delivery_has_machine_readable_manifest":True,
      "source_to_artifact_lineage_is_preserved":True,
      "build_fingerprint_is_recorded":True,
      "asset_license_metadata_is_required":True,
      "captions_are_explicit_deliverables":True,
      "accessibility_metadata_is_explicit":True,
      "reproducibility_information_is_recorded":True,
      "provenance_does_not_claim_unavailable_information":True
    }
