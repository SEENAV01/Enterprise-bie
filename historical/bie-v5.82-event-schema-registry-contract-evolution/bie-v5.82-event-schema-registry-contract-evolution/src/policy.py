def schema_policy():
    return {
      "event_schemas_are_registered":True,
      "versions_are_explicit":True,
      "producer_contracts_are_explicit":True,
      "consumer_contracts_are_explicit":True,
      "schema_validation_is_supported":True,
      "compatibility_is_checked":True,
      "breaking_changes_are_detectable":True,
      "migration_is_supported":True,
      "dual_publish_is_supported_as_a_strategy":True,
      "deprecated_versions_can_be_marked":True,
      "contract_testing_is_supported":True
    }
