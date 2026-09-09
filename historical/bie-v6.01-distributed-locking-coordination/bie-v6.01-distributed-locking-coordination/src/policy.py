def coordination_policy():
    return {
      "distributed_locks_are_supported":True,
      "leases_are_supported":True,
      "fencing_tokens_are_supported":True,
      "leader_election_is_supported":True,
      "coordination_versions_are_supported":True,
      "ownership_verification_is_supported":True,
      "singleton_execution_is_supported":True,
      "quorum_state_is_supported":True,
      "stale_owner_rejection_is_supported":True
    }
